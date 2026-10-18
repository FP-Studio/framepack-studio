"""
diffusers_helper.streaming on CPU: the "GPU" is the CPU, so copies are
synchronous, but block placement, prefetch order, buffer reuse and the
outputs are the same as on CUDA.
"""

import copy

import pytest
import torch

from diffusers_helper.models.hunyuan_video_packed import (
    HunyuanVideoTransformer3DModelPacked,
)
from diffusers_helper.streaming import BlockStreamer, plan_resident

CPU = torch.device("cpu")


def _model(layers=3, single_layers=4):
    torch.manual_seed(0)
    t = HunyuanVideoTransformer3DModelPacked(
        num_attention_heads=2,
        attention_head_dim=16,
        num_layers=layers,
        num_single_layers=single_layers,
        num_refiner_layers=1,
        text_embed_dim=32,
        pooled_projection_dim=16,
        rope_axes_dim=(4, 6, 6),
        has_image_proj=True,
        image_proj_dim=24,
        has_clean_x_embedder=True,
    )
    return t.to(torch.bfloat16).eval().requires_grad_(False)


def _inputs():
    g = torch.Generator().manual_seed(1)

    def r(*shape):
        return torch.randn(*shape, generator=g).to(torch.bfloat16)

    return dict(
        hidden_states=r(1, 16, 2, 4, 4),
        timestep=torch.tensor([500.0]),
        encoder_hidden_states=r(1, 8, 32),
        encoder_attention_mask=torch.ones(1, 8, dtype=torch.bool),
        pooled_projections=r(1, 16),
        guidance=torch.tensor([10000.0]),
        image_embeddings=r(1, 4, 24),
        return_dict=False,
    )


def _run(model):
    with torch.no_grad():
        return model(**_inputs())[0]


def _budget_for(streamer, n):
    """The smallest budget that keeps the first n blocks resident. With dual
    blocks bigger than single ones, some n can't come out of the planner
    (keeping one more dual block beats streaming it)."""
    sizes = [b.nbytes for b in streamer.blocks]
    return sum(sizes[:n]) + 2 * max(sizes[n:], default=0)


def test_plan_resident():
    assert plan_resident([10, 10, 10], 30) == 3
    # two buffers for the largest streamed block come out of the budget
    assert plan_resident([10, 10, 10], 29) == 0
    assert plan_resident([10, 10, 10, 10], 35) == 1
    assert plan_resident([30, 10, 10], 39) == 0
    assert plan_resident([30, 10, 10, 10], 55) == 1
    assert plan_resident([10, 10], 0) == 0


@pytest.mark.parametrize("n_resident", [0, 3, 4, 7])
def test_outputs_match_plain_model(n_resident):
    model = _model()
    expected = _run(copy.deepcopy(model))
    streamer = BlockStreamer(model, CPU, pin_budget=0)
    streamer._ensure_layout()
    streamer.prepare(budget_bytes=_budget_for(streamer, n_resident))
    assert streamer.n_resident == n_resident
    for _ in range(2):  # a second step reuses the wrapped-around prefetch
        assert torch.equal(_run(model), expected)


def test_prefetch_order_and_buffer_reuse():
    model = _model()
    streamer = BlockStreamer(model, CPU, pin_budget=0)
    streamer._ensure_layout()
    streamer.prepare(budget_bytes=_budget_for(streamer, 3))
    assert streamer.n_resident == 3
    buffers = [s.buf.data_ptr() for s in streamer.slots]
    order = []
    for i, b in enumerate(streamer.blocks):
        b.module.register_forward_pre_hook(
            lambda _m, _a, i=i: order.append(("run", i, len(streamer.copy_log)))
        )
    _run(model)
    _run(model)
    n = len(streamer.blocks)
    streamed = list(range(3, n))
    # step 1: first streamed block on demand, then each one prefetched while
    # the one before runs, and the last prefetches the next step's first
    assert [c[0] for c in streamer.copy_log] == streamed + [3] + streamed[1:] + [3]
    # consecutive copies alternate between the two buffers
    slots = [c[1] for c in streamer.copy_log]
    assert all(a != b for a, b in zip(slots, slots[1:]))
    # every streamed block was in place before it ran: its copy is in the
    # log before the hook that runs it (our hook fires first, so copies
    # made for block i+1 already show up)
    for _, i, copies in order:
        if i >= 3:
            assert i in [c[0] for c in streamer.copy_log[: copies + 1]]
    assert [s.buf.data_ptr() for s in streamer.slots] == buffers


def test_release_points_weights_back_at_host():
    model = _model()
    streamer = BlockStreamer(model, CPU, pin_budget=0)
    streamer._ensure_layout()
    streamer.prepare(budget_bytes=_budget_for(streamer, 3))
    _run(model)
    streamer.release()
    for block in streamer.blocks:
        assert block.signature == block.current_signature()
    assert streamer.slots == []


def test_replaced_weights_are_laid_out_again():
    model = _model()
    streamer = BlockStreamer(model, CPU, pin_budget=0)
    streamer.prepare(budget_bytes=_budget_for(streamer, 0) * 4)
    streamer.release()
    # like load_state_dict(assign=True) after merging a LoRA
    block = model.single_transformer_blocks[1]
    block.proj_out.weight = torch.nn.Parameter(
        block.proj_out.weight.detach() * 2, requires_grad=False
    )
    expected = _run(copy.deepcopy(model))
    streamer.prepare(budget_bytes=_budget_for(streamer, 2))
    assert torch.equal(_run(model), expected)
    streamer.release()
    # an in-place copy (fp8 storage's load_state_dict(assign=False)) lands in
    # the host buffer directly
    with torch.no_grad():
        block.proj_out.weight.mul_(0.5)
    expected = _run(copy.deepcopy(model))
    streamer.prepare(budget_bytes=_budget_for(streamer, 2))
    assert torch.equal(_run(model), expected)


def _fp8_model():
    model = _model()
    model.enable_layerwise_casting(
        storage_dtype=torch.float8_e4m3fn, compute_dtype=torch.bfloat16
    )
    return model


def test_fp8_storage():
    # deepcopy breaks diffusers hooks, so the reference is a second model
    expected = _run(_fp8_model())
    model = _fp8_model()
    streamer = BlockStreamer(model, CPU, pin_budget=0)
    streamer._ensure_layout()
    fp8 = [
        t.dtype
        for *_, t in streamer.blocks[-1].tensors()
        if t.dtype == torch.float8_e4m3fn
    ]
    assert fp8, "streamed blocks should hold fp8 weights"
    streamer.prepare(budget_bytes=_budget_for(streamer, 3))
    for _ in range(2):
        assert torch.equal(_run(model), expected)
    streamer.release()
    for block in streamer.blocks:
        assert block.signature == block.current_signature()


def test_close_removes_hooks():
    model = _model()
    expected = _run(copy.deepcopy(model))
    streamer = BlockStreamer(model, CPU, pin_budget=0)
    streamer.prepare(budget_bytes=_budget_for(streamer, 1))
    streamer.close()
    assert torch.equal(_run(model), expected)
    assert streamer.copy_log == []
