"""
Streams the transformer's blocks from system RAM in low VRAM mode
(offload_engine "streamed").

As many leading blocks as fit stay on the GPU. Each of the rest is copied in
on a side CUDA stream, into one of two reusable GPU buffers, while the block
before it runs. This follows ComfyUI's async weight offloading
(comfy/ops.py cast_bias_weight / uncast_bias_weight,
comfy/model_management.py get_offload_stream / get_cast_buffer /
pin_memory), but per block: FramePack runs its 60 blocks in a fixed order,
so prefetching the next one is enough.

Every block's weights live in one contiguous host buffer, pinned in place
with cudaHostRegister while the pin budget lasts, so a block is a single
asynchronous copy. DynamicSwapInstaller, which this replaces for the
transformer, copied each weight synchronously from pageable memory on every
access.

Only plain tensors can be streamed (bf16, or fp8 storage through
enable_layerwise_casting). bitsandbytes weights keep extra state outside
.data, so int8/NF4 models stay on DynamicSwapInstaller.
"""

import logging
import os
import time
import weakref
from contextlib import nullcontext

import torch

logger = logging.getLogger(__name__)

GB = 1024**3
ALIGN = 256
# VRAM kept back for the CUDA context and allocator slack
# (ComfyUI's EXTRA_RESERVED_VRAM)
EXTRA_RESERVED_BYTES = 400 * 1024**2
# FRAMEPACK_STREAM_TIMING=1 logs, per prepare/release, how long the GPU
# waited on copies
TIMING = os.environ.get("FRAMEPACK_STREAM_TIMING") == "1"


def _aligned(n):
    return (n + ALIGN - 1) // ALIGN * ALIGN


def default_pin_budget():
    """
    Bytes of system RAM that may be pinned. ComfyUI's Linux formula
    (MAX_PINNED_MEMORY) without swap: at least 40 % of RAM, otherwise all
    but 16 GB.
    """
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        return 0
    return int(max(ram * 0.4, min(ram * 0.9, ram - 16 * GB)))


def plan_resident(block_bytes, budget):
    """
    How many leading blocks stay on the GPU: as many as fit in `budget`
    next to two copy buffers sized for the largest block left to stream.
    """
    for n in range(len(block_bytes), -1, -1):
        rest = block_bytes[n:]
        if sum(block_bytes[:n]) + 2 * max(rest, default=0) <= budget:
            return n
    return 0


def _host_register(t):
    ptr = t.data_ptr()
    if torch.cuda.cudart().cudaHostRegister(ptr, t.numel(), 0) == 0:
        return ptr
    logger.warning(
        f"Block streaming: couldn't pin {t.numel() / GB:.2f} GB; that block "
        "is copied from pageable memory (slower)."
    )
    # A failed register can leave an error queued on the device; clear it
    # (ComfyUI's discard_cuda_async_error)
    try:
        torch.cuda.synchronize()
    except RuntimeError:
        pass
    return None


def _host_unregister(pinned):
    for ptr in list(pinned):
        torch.cuda.cudart().cudaHostUnregister(ptr)


class _Block:
    """One transformer block's weights, laid out in one host buffer."""

    def __init__(self, module):
        self.module = module
        self.entries = []  # (owner, name, is_param, offset, nbytes, dtype, shape)
        self.host = None  # uint8 CPU tensor holding every weight
        self.nbytes = 0
        self.signature = None

    def tensors(self):
        for owner_name, owner in self.module.named_modules():
            for name, p in owner._parameters.items():
                if p is not None:
                    yield owner_name, owner, name, True, p
            for name, b in owner._buffers.items():
                if b is not None:
                    yield owner_name, owner, name, False, b

    def current_signature(self):
        return tuple(
            (owner_name, name, id(t), t.data_ptr(), t.dtype, tuple(t.shape))
            for owner_name, _, name, _, t in self.tensors()
        )

    def layout_bytes(self):
        return sum(_aligned(t.numel() * t.element_size()) for *_, t in self.tensors())

    def build(self, pin):
        """Copy the weights into one host buffer and point them at it.
        Returns the registered pointer if the buffer got pinned."""
        found = list(self.tensors())
        self.nbytes = 0
        layout = []
        for _, owner, name, is_param, t in found:
            nbytes = t.numel() * t.element_size()
            layout.append(
                (owner, name, is_param, self.nbytes, nbytes, t.dtype, t.shape)
            )
            self.nbytes += _aligned(nbytes)
        host = torch.empty(self.nbytes, dtype=torch.uint8)
        self.entries = layout
        for (_, _, _, _, t), entry in zip(found, layout):
            view = self._view(host, entry)
            view.copy_(t.detach())
            t.data = view
        self.host = host
        self.signature = self.current_signature()
        return _host_register(host) if pin else None

    @staticmethod
    def _view(buf, entry):
        _, _, _, offset, nbytes, dtype, shape = entry
        return buf[offset : offset + nbytes].view(dtype).view(shape)

    def _get(self, entry):
        owner, name, is_param = entry[:3]
        return owner._parameters[name] if is_param else owner._buffers[name]

    def point_at(self, buf):
        for entry in self.entries:
            self._get(entry).data = self._view(buf, entry)

    def to_device(self, device):
        """Resident copy. One tensor per weight rather than views of one
        buffer: layerwise casting swaps in new tensors after every layer,
        and a shared buffer would then stay allocated next to them."""
        for entry in self.entries:
            self._get(entry).data = self._view(self.host, entry).to(
                device, non_blocking=True
            )


class _Slot:
    """A reusable GPU buffer that streamed blocks are copied into."""

    def __init__(self, nbytes, device, cuda):
        self.buf = torch.empty(nbytes, dtype=torch.uint8, device=device)
        self.holds = None  # index of the block whose weights are in buf
        self.ready = torch.cuda.Event() if cuda else None
        self.free = None  # recorded when the block last using buf has run


class BlockStreamer:
    def __init__(self, transformer, device, pin_budget=None):
        self.transformer = transformer
        self.device = torch.device(device)
        self.cuda = self.device.type == "cuda"
        self.pin_budget = default_pin_budget() if pin_budget is None else pin_budget
        self.blocks = [
            _Block(m)
            for m in list(transformer.transformer_blocks)
            + list(transformer.single_transformer_blocks)
        ]
        block_modules = {
            id(transformer.transformer_blocks),
            id(transformer.single_transformer_blocks),
        }
        self.base_modules = [
            m for _, m in transformer.named_children() if id(m) not in block_modules
        ]
        self.stream = torch.cuda.Stream(device=self.device) if self.cuda else None
        self.slots = []
        self.n_resident = len(self.blocks)
        self.prepared = False
        self.active = None  # slot the running block reads from
        self.copy_log = []  # (block index, slot index) per copy; for tests
        self._pinned = {}  # registered pointer -> bytes
        self._finalizer = weakref.finalize(self, _host_unregister, self._pinned)
        self._waits = []
        self._hooks = []
        for i, block in enumerate(self.blocks):
            self._hooks.append(
                block.module.register_forward_pre_hook(
                    lambda _m, _a, i=i: self._before_block(i)
                )
            )
            self._hooks.append(
                block.module.register_forward_hook(
                    lambda _m, _a, _o, i=i: self._after_block(i)
                )
            )

    # --- layout ---------------------------------------------------------

    def _ensure_layout(self):
        """(Re)build the host buffers of blocks whose weights were replaced,
        e.g. by loading or unloading LoRAs."""
        stale = [b for b in self.blocks if b.signature != b.current_signature()]
        if not stale:
            return
        start = time.perf_counter()
        # Pin the last blocks first: they are the ones streamed every step
        for block in reversed(stale):
            old = block.host.data_ptr() if block.host is not None else None
            if old in self._pinned:
                _host_unregister([old])
                del self._pinned[old]
            pin = (
                self.cuda
                and sum(self._pinned.values()) + block.layout_bytes() <= self.pin_budget
            )
            ptr = block.build(pin)
            if ptr is not None:
                self._pinned[ptr] = block.nbytes
        logger.info(
            f"Block streaming: laid out {len(stale)} blocks in "
            f"{time.perf_counter() - start:.1f}s, "
            f"{sum(self._pinned.values()) / GB:.1f} GB pinned of "
            f"{sum(b.nbytes for b in self.blocks) / GB:.1f} GB"
        )

    # --- placement ------------------------------------------------------

    def prepare(self, reserve_gb=0.0, budget_bytes=None):
        """
        Put the small modules and as many blocks as fit on the GPU, leaving
        `reserve_gb` free for activations, and set up the copy buffers.
        """
        if self.prepared:
            return
        self._ensure_layout()
        for m in self.base_modules:
            m.to(self.device)
        if budget_bytes is None:
            from diffusers_helper.memory import get_cuda_free_memory_gb

            free = get_cuda_free_memory_gb(self.device) * GB
            budget_bytes = free - reserve_gb * GB - EXTRA_RESERVED_BYTES
        sizes = [b.nbytes for b in self.blocks]
        self.n_resident = plan_resident(sizes, budget_bytes)
        for block in self.blocks[: self.n_resident]:
            block.to_device(self.device)
        streamed = sizes[self.n_resident :]
        if streamed:
            self.slots = [
                _Slot(max(streamed), self.device, self.cuda) for _ in range(2)
            ]
        self.active = None
        self.copy_log = []
        self._waits = []
        self.prepared = True
        logger.info(
            f"Block streaming: {self.n_resident}/{len(self.blocks)} blocks on the GPU "
            f"({sum(sizes[: self.n_resident]) / GB:.1f} GB), {len(streamed)} streamed "
            f"({sum(streamed) / GB:.1f} GB per step)"
        )

    def release(self):
        """Point every weight back at system RAM and free the GPU copies."""
        if not self.prepared:
            return
        if self.cuda:
            # Pending prefetches write into the buffers about to be freed
            self.stream.synchronize()
            torch.cuda.current_stream(self.device).synchronize()
            self._log_waits()
        for block in self.blocks:
            block.point_at(block.host)
        for m in self.base_modules:
            m.to("cpu")
        self.slots = []
        self.active = None
        self.prepared = False
        if self.cuda:
            torch.cuda.empty_cache()

    def close(self):
        """Release, remove the hooks and unpin the host buffers."""
        self.release()
        for h in self._hooks:
            h.remove()
        self._hooks = []
        self._finalizer()

    # --- per block ------------------------------------------------------

    def _next_streamed(self, i):
        """The streamed block after i, wrapping to the first one so the next
        step's first copy overlaps the end of this step."""
        j = i + 1
        return j if j < len(self.blocks) else self.n_resident

    def _holding(self, i):
        for slot in self.slots:
            if slot.holds == i:
                return slot
        return None

    def _copy_in(self, i, avoid=None):
        slot = next(s for s in self.slots if s is not avoid)
        block = self.blocks[i]
        with torch.cuda.stream(self.stream) if self.cuda else nullcontext():
            if slot.free is not None:
                # Don't overwrite weights a kernel may still be reading
                self.stream.wait_event(slot.free)
            slot.buf[: block.nbytes].copy_(block.host, non_blocking=self.cuda)
            if self.cuda:
                slot.ready.record(self.stream)
        slot.holds = i
        self.copy_log.append((i, self.slots.index(slot)))
        return slot

    def _before_block(self, i):
        if not self.prepared or i < self.n_resident:
            return
        slot = self._holding(i) or self._copy_in(i)
        if self.cuda:
            compute = torch.cuda.current_stream(self.device)
            if TIMING:
                before, after = (
                    torch.cuda.Event(enable_timing=True),
                    torch.cuda.Event(enable_timing=True),
                )
                before.record(compute)
                compute.wait_event(slot.ready)
                after.record(compute)
                self._waits.append((before, after))
            else:
                compute.wait_event(slot.ready)
        self.blocks[i].point_at(slot.buf)
        self.active = slot
        nxt = self._next_streamed(i)
        if nxt != i and self._holding(nxt) is None:
            self._copy_in(nxt, avoid=slot)

    def _after_block(self, i):
        if not self.prepared or i < self.n_resident:
            return
        slot = self.active
        self.blocks[i].point_at(self.blocks[i].host)
        if self.cuda:
            if slot.free is None:
                slot.free = torch.cuda.Event()
            slot.free.record(torch.cuda.current_stream(self.device))
        self.active = None

    def _log_waits(self):
        if not self._waits:
            return
        waited = sum(a.elapsed_time(b) for a, b in self._waits) / 1000
        logger.info(
            f"Block streaming: GPU waited {waited:.2f}s on copies over "
            f"{len(self._waits)} streamed blocks"
        )
        self._waits = []
