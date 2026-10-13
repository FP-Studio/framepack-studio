"""
End-to-end CPU harness for FramePack Studio's worker.

Runs the real `modules.pipelines.worker.worker` with:
  - a tiny randomly-initialised HunyuanVideoTransformer3DModelPacked (real code path)
  - a tiny randomly-initialised AutoencoderKLHunyuanVideo
  - fake text / CLIP-vision encoders (deterministic embeddings)
and records every sample_hunyuan call so tests can compare section latents.

Usage:
    import fpharness
    res = fpharness.run("F1", input_image=img, total_second_length=2, ...)
"""

import fpshim  # noqa: F401  (must come first)

import hashlib
import os
import sys
import tempfile
import types

import numpy as np
import torch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from diffusers import AutoencoderKLHunyuanVideo  # noqa: E402

from diffusers_helper.models.hunyuan_video_packed import (  # noqa: E402
    HunyuanVideoTransformer3DModelPacked,
)
from diffusers_helper.thread_utils import AsyncStream  # noqa: E402
import diffusers_helper.clip_vision as clip_vision  # noqa: E402
import diffusers_helper.memory as memory  # noqa: E402
import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh  # noqa: E402

TEXT_DIM = 32
POOL_DIM = 16
CLIP_DIM = 24
CPU = torch.device("cpu")


def _seeded(key: str, shape, dtype=torch.float32):
    seed = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    g = torch.Generator("cpu").manual_seed(seed)
    return torch.randn(shape, generator=g, dtype=torch.float32).to(dtype)


class FakePromptCache(dict):
    """Behaves like a fully-populated prompt embedding cache."""

    def __contains__(self, key):
        return True

    def __getitem__(self, key):
        vec = _seeded("llama:" + key, (1, 512, TEXT_DIM))
        mask = torch.zeros((1, 512), dtype=torch.bool)
        mask[:, :8] = True
        pool = _seeded("clip:" + key, (1, POOL_DIM))
        return vec, mask, pool


def fake_clip_encode(image, feature_extractor, image_encoder):
    arr = np.asarray(image)
    key = hashlib.sha256(arr.tobytes()).hexdigest()
    return types.SimpleNamespace(last_hidden_state=_seeded(key, (1, 8, CLIP_DIM)))


_TRANSFORMER_CACHE = {}


def tiny_transformer():
    if "t" not in _TRANSFORMER_CACHE:
        torch.manual_seed(0)
        t = HunyuanVideoTransformer3DModelPacked(
            num_attention_heads=2,
            attention_head_dim=16,
            num_layers=1,
            num_single_layers=1,
            num_refiner_layers=1,
            text_embed_dim=TEXT_DIM,
            pooled_projection_dim=POOL_DIM,
            rope_axes_dim=(4, 6, 6),
            has_image_proj=True,
            image_proj_dim=CLIP_DIM,
            has_clean_x_embedder=True,
        )
        # Shrink the output head so repeated sampling stays numerically tame.
        with torch.no_grad():
            t.proj_out.weight.mul_(0.05)
        t = t.to(torch.bfloat16).eval().requires_grad_(False)
        _TRANSFORMER_CACHE["t"] = t
    return _TRANSFORMER_CACHE["t"]


def tiny_vae():
    torch.manual_seed(1)
    vae = AutoencoderKLHunyuanVideo(
        block_out_channels=(8, 8, 8, 8),
        layers_per_block=1,
        norm_num_groups=4,
        mid_block_add_attention=False,
    )
    return vae.float().eval().requires_grad_(False)


class Recorder:
    def __init__(self, stream=None, cancel_after=None):
        self.calls = []
        self.saved_videos = []
        self.stream = stream
        self.cancel_after = cancel_after

    def wrap_sampler(self, real):
        def sample(**kwargs):
            out = real(**kwargs)
            self.calls.append(
                {
                    "out": out.detach().float().cpu().clone(),
                    "kwargs": {
                        k: (
                            v.detach().float().cpu().clone()
                            if torch.is_tensor(v)
                            else v
                        )
                        for k, v in kwargs.items()
                        if k
                        in (
                            "latent_indices",
                            "clean_latents",
                            "clean_latent_indices",
                            "clean_latents_2x",
                            "clean_latent_2x_indices",
                            "clean_latents_4x",
                            "clean_latent_4x_indices",
                            "initial_latent",
                            "strength",
                            "noise",
                            "image_embeddings",
                            "prompt_embeds",
                        )
                    },
                }
            )
            if self.cancel_after is not None and len(self.calls) >= self.cancel_after:
                self.stream.input_queue.push(
                    "end"
                )  # same signal the Cancel button sends
            return out

        return sample


def _install_globals(main_stream, vae):
    main = sys.modules["__main__"]
    main.high_vram = True
    main.args = types.SimpleNamespace(offline=False)
    main.text_encoder = None
    main.text_encoder_2 = None
    main.tokenizer = None
    main.tokenizer_2 = None
    main.vae = vae
    main.image_encoder = None
    main.feature_extractor = None
    main.prompt_embedding_cache = FakePromptCache()
    main.stream = main_stream


def _patch_cpu():
    import modules.pipelines.worker as worker_mod

    memory.gpu = CPU
    worker_mod.gpu = CPU
    clip_vision.hf_clip_vision_encode = fake_clip_encode

    from modules.generators.base_generator import BaseModelGenerator

    def load_model(self):
        self.transformer = tiny_transformer()
        return self.transformer

    for cls in _all_subclasses(BaseModelGenerator):
        cls.load_model = load_model
    return worker_mod


def _all_subclasses(cls):
    out = set()
    for sub in cls.__subclasses__():
        out.add(sub)
        out |= _all_subclasses(sub)
    return out


def default_image(h=64, w=64, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (h, w, 3), dtype=np.uint8)


def run(model_type="F1", cancel_after=None, **overrides):
    """Run the worker synchronously and return a dict of recorded results."""
    worker_mod = _patch_cpu()
    from modules.studio_manager import StudioManager

    stream = AsyncStream()
    rec = Recorder(stream, cancel_after)
    real_sampler = kdh.sample_hunyuan
    kdh.sample_hunyuan = rec.wrap_sampler(real_sampler)

    real_save = worker_mod.save_bcthw_as_mp4

    def fake_save(x, output_filename, fps=10, crf=0):
        rec.saved_videos.append((output_filename, x.detach().float().cpu().clone()))
        return output_filename

    worker_mod.save_bcthw_as_mp4 = fake_save

    out_dir = tempfile.mkdtemp(prefix="fp_out_")
    vae = tiny_vae()
    _install_globals(stream, vae)

    sm = StudioManager()
    sm.settings.settings["save_metadata"] = False
    sm.settings.settings["clean_up_videos"] = False
    sm.settings.settings["output_dir"] = out_dir
    sm.unset_current_generator()

    image = overrides.pop("input_image", None)
    if image is None and overrides.get("has_input_image", True):
        image = default_image()
    params = dict(
        model_type=model_type,
        input_image=image,
        end_frame_image=None,
        end_frame_strength=1.0,
        prompt_text="a test prompt",
        n_prompt="",
        seed=1234,
        total_second_length=2,
        latent_window_size=3,
        steps=3,
        cfg=1.0,
        gs=10.0,
        rs=0.0,
        use_teacache=False,
        teacache_num_steps=25,
        teacache_rel_l1_thresh=0.15,
        use_magcache=False,
        magcache_threshold=0.1,
        magcache_max_consecutive_skips=2,
        magcache_retention_ratio=0.25,
        blend_sections=0,
        latent_type="Black",
        selected_loras=[],
        has_input_image=True,
        lora_values=[],
        job_stream=stream,
        output_dir=out_dir,
        metadata_dir=out_dir,
        input_files_dir=out_dir,
        resolutionW=64,
        resolutionH=64,
        lora_loaded_names=[],
    )
    params.update(overrides)
    tiny_transformer()  # build before seeding so first-run init doesn't shift the RNG
    # vae_encode samples latent_dist with the global RNG
    torch.manual_seed(0)
    try:
        worker_mod.worker(**params)
    finally:
        kdh.sample_hunyuan = real_sampler
        worker_mod.save_bcthw_as_mp4 = real_save

    errors = []
    events = []
    while True:
        item = stream.output_queue.pop()
        if item is None:
            break
        events.append(item[0])
        if item[0] == "error":
            errors.append(item[1])
    return {
        "calls": rec.calls,
        "videos": rec.saved_videos,
        "errors": errors,
        "events": events,
        "out_dir": out_dir,
        "job_files": sorted(os.listdir(out_dir)),
    }
