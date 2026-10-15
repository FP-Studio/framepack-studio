"""TeaCache / MagCache stay in step when sections run fewer steps (img2img)."""

import os
import tempfile

import numpy as np
import torch

import fpharness
from diffusers_helper.models.mag_cache import MagCache
from test_motion_reference import make_video


def make_magcache(num_steps=25):
    mc = MagCache(
        "Original",
        640,
        640,
        num_steps,
        threshold=1e9,
        max_consectutive_skips=10**6,
        retention_ratio=0.0,
    )
    # Every step looks skippable, so only the section logic can force a compute
    mc.mag_ratios = np.ones(num_steps)
    return mc


def run_section(mc, n, seen_index=None):
    """Drive MagCache like the transformer does; return the skip decisions."""
    skips = []
    for _ in range(n):
        if seen_index is not None:
            seen_index.append(mc.step_index)
        h = torch.randn(1, 4, 8)
        skip = mc.should_skip(h)
        if not skip:
            mc.update_hidden_states(h + 1)
        skips.append(skip)
    return skips


def test_magcache_never_skips_without_a_residual():
    mc = make_magcache()
    mc.step_index = 5
    assert mc.should_skip(torch.randn(1, 4, 8)) is False


def test_magcache_shortened_sections_line_up():
    mc = make_magcache(25)
    k = 10
    for _ in range(3):
        mc.start_section(k)
        assert mc.previous_residual is None  # nothing from the previous section
        seen = []
        skips = run_section(mc, 25 - k, seen)
        assert seen == list(range(k, 25))  # mag_ratios[step_index] = real step
        assert skips[0] is False
        assert any(skips[1:])  # the skip path is live
        assert mc.step_index == 0  # wraps after the schedule's last step


def test_magcache_without_start_section_keeps_wrapping():
    mc = make_magcache(8)
    for _ in range(2):
        seen = []
        skips = run_section(mc, 8, seen)
        assert seen == list(range(8))
        assert skips[0] is False


def test_magcache_calibration_with_shortened_section():
    mc = MagCache("Original", 640, 640, 8, is_calibrating=True)
    mc.start_section(4)
    assert run_section(mc, 4) == [False] * 4
    assert len(mc.norm_ratio) == 3


def test_teacache_computes_first_and_last_step_of_every_section(monkeypatch):
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    video = make_video(os.path.join(tempfile.mkdtemp(), "ref.mp4"))
    t = fpharness.tiny_transformer()
    sections = []

    real_forward = t.forward
    real_layers = t._run_denoising_layers
    real_sample = kdh.sample_hunyuan

    def forward(*args, **kwargs):
        sections[-1].append(False)
        return real_forward(*args, **kwargs)

    def layers(*args, **kwargs):
        sections[-1][-1] = True
        return real_layers(*args, **kwargs)

    def sample(**kwargs):
        sections.append([])
        return real_sample(**kwargs)

    monkeypatch.setattr(t, "forward", forward)
    monkeypatch.setattr(t, "_run_denoising_layers", layers)
    monkeypatch.setattr(kdh, "sample_hunyuan", sample)
    try:
        res = fpharness.run(
            "F1",
            steps=8,
            motion_reference_video=video,
            motion_reference_strength=1.0,  # each section runs the last 4 of 8 steps
            use_teacache=True,
            teacache_rel_l1_thresh=float("inf"),  # skip all but the forced steps
        )
    finally:
        t.initialize_teacache(enable_teacache=False)
        t.uninstall_magcache()

    assert not res["errors"], res["errors"]
    assert len(sections) == 5
    for computed in sections:
        assert computed == [True, False, False, True]
