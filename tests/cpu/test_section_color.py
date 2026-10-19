"""Colour lock (modules/pipelines/section_color.py)."""

import os
import sys

import pytest
import torch
from PIL import Image

import fpharness

sys.path.insert(0, os.path.join(fpharness.REPO_ROOT, "tools"))

import run_job as rj  # noqa: E402

TINY = dict(
    model_type="F1",
    total_second_length=2,
    resolutionW=64,
    resolutionH=64,
    steps=3,
    latent_window_size=3,
    seed=5,
    use_magcache=False,
)


@pytest.fixture(autouse=True)
def restore_studio_state():
    from modules.studio_manager import StudioManager

    sm = StudioManager()
    saved = dict(sm.settings.settings)
    yield
    sm.settings.settings.clear()
    sm.settings.settings.update(saved)
    sm.unset_current_generator()


def stats(x):
    return x.mean((2, 3, 4)), x.std((2, 3, 4))


def test_match_start_moves_channel_stats_toward_the_start():
    from modules.pipelines import section_color

    torch.manual_seed(0)
    start = torch.randn(1, 4, 1, 8, 8) * 0.5 + 0.2
    section = torch.randn(1, 4, 6, 8, 8) * 2.0 - 1.0
    assert section_color.match_start(section, start, 0) is section
    full = section_color.match_start(section, start, 1.0)
    assert torch.allclose(stats(full)[0], stats(start)[0], atol=1e-5)
    assert torch.allclose(stats(full)[1], stats(start)[1], atol=1e-4)
    half = section_color.match_start(section, start, 0.5)
    assert torch.allclose(
        stats(half)[0], (stats(section)[0] + stats(start)[0]) / 2, atol=1e-5
    )
    assert half.dtype == section.dtype and half.shape == section.shape


@pytest.mark.parametrize("strength", [0.0, 0.7])
def test_f1_job_locks_every_section(tmp_path, monkeypatch, strength):
    from modules.pipelines import section_color

    image = str(tmp_path / "start.png")
    Image.fromarray(fpharness.default_image(96, 128)).save(image)
    calls = []
    real = section_color.match_start

    def spy(section, start_latent, s):
        calls.append(s)
        return real(section, start_latent, s)

    monkeypatch.setattr(section_color, "match_start", spy)
    rj.run_job(
        output_dir=str(tmp_path / "out"),
        fake=True,
        verbose=False,
        input_image=image,
        color_lock=strength,
        **TINY,
    )
    # 2 s with a 3-latent window is 5 sections
    assert calls == ([strength] * 5 if strength else [])
