"""Flow-noise tests (run from the flow-noise checkout)."""

import math

import pytest
import torch

import fpharness
from modules.pipelines import flow_noise as fn


def gen(seed=0):
    return torch.Generator("cpu").manual_seed(seed)


@pytest.mark.parametrize("move", fn.CAMERA_MOVES)
@pytest.mark.parametrize("strength", [0.0, 0.5, 1.0])
def test_noise_stays_standard_normal(move, strength):
    v = fn.camera_velocity(move, 0.5, 40, 48, 16) + fn.arrow_velocity(
        [(0.2, 0.5, 0.8, 0.5)], 40, 48, 16
    )
    noise = fn.warped_noise(v, 16, 16, gen(), strength)
    assert noise.shape == (1, 16, 16, 40, 48)
    for t in range(16):
        frame = noise[0, :, t]
        assert abs(frame.mean().item()) < 0.05
        assert abs(frame.std().item() - 1) < 0.05


def test_pan_moves_pattern_exactly():
    v = torch.zeros(2, 20, 30)
    v[0] = 1.0  # one latent pixel right per frame
    noise = fn.warped_noise(v, 5, 4, gen(), strength=1.0)[0]
    for t in range(5):
        assert torch.equal(noise[:, t, :, t:], noise[:, 0, :, : 30 - t])
    # Partial strength keeps correlation sqrt(a) with the moved pattern
    noise = fn.warped_noise(v, 5, 16, gen(), strength=0.64)[0]
    a, b = noise[:, 4, :, 4:].flatten(), noise[:, 0, :, :26].flatten()
    corr = torch.corrcoef(torch.stack([a, b]))[0, 1].item()
    # frame 0 itself has 0.8 * base, so corr = 0.8 * 0.8
    assert corr == pytest.approx(0.64, abs=0.05)


def test_no_motion_is_frozen_pattern():
    noise = fn.warped_noise(torch.zeros(2, 8, 8), 4, 2, gen(), strength=1.0)[0]
    assert all(torch.equal(noise[:, t], noise[:, 0]) for t in range(4))


def test_camera_velocity_directions():
    pan = fn.camera_velocity("Pan left", 0.5, 20, 40, 11)
    assert torch.allclose(pan[0], torch.full((20, 40), 0.5 * 40 / 10))
    assert torch.equal(pan[1], torch.zeros(20, 40))
    zoom = fn.camera_velocity("Zoom in", 0.5, 21, 21, 11)
    assert zoom[0, 10, 10] == 0 and zoom[0, 10, 20] > 0 and zoom[0, 10, 0] < 0
    assert zoom[1, 20, 10] > 0
    assert torch.equal(fn.camera_velocity("None", 0.5, 4, 4, 11), torch.zeros(2, 4, 4))


def test_arrow_velocity_is_local():
    v = fn.arrow_velocity([(0.25, 0.5, 0.75, 0.5)], 41, 81, 11, radius=0.1)
    # At the arrow start content moves the full arrow length over the video
    assert v[0, 20, 20].item() * 10 == pytest.approx(0.5 * 80, rel=1e-3)
    assert abs(v[1, 20, 20].item()) < 1e-6
    assert abs(v[0, 20, 79].item()) < 1e-3  # far away stays still
    # Two identical arrows average instead of doubling
    v2 = fn.arrow_velocity([(0.25, 0.5, 0.75, 0.5)] * 2, 41, 81, 11, radius=0.1)
    assert torch.allclose(v2[:, 20, 20], v[:, 20, 20])


def test_section_slice_order():
    noise = torch.arange(16).float().view(1, 1, 16, 1, 1)
    take = lambda *a, **k: fn.section_slice(noise, *a, **k).flatten().tolist()  # noqa: E731
    assert take(0, 5, 3, True, reverse_order=False) == [1, 2, 3]
    assert take(0, 5, 3, True, reverse_order=True) == [13, 14, 15]
    assert take(4, 5, 3, False, reverse_order=True) == [0, 1, 2]


@pytest.mark.parametrize("model_type", ["F1", "Original"])
def test_end_to_end(model_type):
    res = fpharness.run(
        model_type,
        flow_noise_camera="Pan left",
        flow_noise_camera_amount=0.5,
        flow_noise_arrows=[(0.3, 0.5, 0.7, 0.4)],
        flow_noise_strength=0.8,
    )
    assert not res["errors"], res["errors"]
    calls = res["calls"]
    noises = [c["kwargs"]["noise"] for c in calls]
    assert all(n is not None and n.shape == calls[0]["out"].shape for n in noises)

    # Re-assemble the time-ordered noise and check it matches a direct build
    ordered = noises if model_type == "F1" else noises[::-1]
    timeline = torch.cat(ordered, dim=2)
    h, w = timeline.shape[-2:]
    total = 1 + timeline.shape[2]
    v = fn.camera_velocity("Pan left", 0.5, h, w, total) + fn.arrow_velocity(
        [(0.3, 0.5, 0.7, 0.4)], h, w, total
    )
    expected = fn.warped_noise(v, total, 16, gen(1234), 0.8)[:, :, 1:]
    assert torch.equal(timeline, expected)


def test_no_motion_matches_plain_run():
    base = fpharness.run("F1")
    res = fpharness.run("F1", flow_noise_camera="None", flow_noise_strength=0.8)
    for a, b in zip(base["calls"], res["calls"]):
        assert torch.equal(a["out"], b["out"])
        assert b["kwargs"]["noise"] is None


def test_sampler_noise_argument():
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    t = fpharness.tiny_transformer()
    common = dict(
        transformer=t,
        width=64,
        height=64,
        frames=9,
        num_inference_steps=2,
        prompt_embeds=torch.zeros(1, 4, fpharness.TEXT_DIM, dtype=torch.bfloat16),
        prompt_embeds_mask=torch.ones(1, 4, dtype=torch.bool),
        prompt_poolers=torch.zeros(1, fpharness.POOL_DIM, dtype=torch.bfloat16),
        negative_prompt_embeds=torch.zeros(
            1, 4, fpharness.TEXT_DIM, dtype=torch.bfloat16
        ),
        negative_prompt_embeds_mask=torch.ones(1, 4, dtype=torch.bool),
        negative_prompt_poolers=torch.zeros(
            1, fpharness.POOL_DIM, dtype=torch.bfloat16
        ),
        image_embeddings=torch.zeros(1, 2, fpharness.CLIP_DIM, dtype=torch.bfloat16),
        device=torch.device("cpu"),
    )
    noise = torch.randn((1, 16, 3, 8, 8), generator=gen(5))
    a = kdh.sample_hunyuan(generator=gen(5), **common)
    b = kdh.sample_hunyuan(generator=gen(99), noise=noise, **common)
    assert torch.equal(a, b)
    with pytest.raises(AssertionError):
        kdh.sample_hunyuan(generator=gen(5), noise=noise[:, :, :2], **common)
    assert math.isfinite(a.abs().max().item())
