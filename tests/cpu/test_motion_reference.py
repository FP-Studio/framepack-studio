"""Motion reference tests (run from the motion-reference checkout)."""

import os
import tempfile

import av
import numpy as np
import pytest
import torch

import fpharness
from modules.pipelines import motion_reference as mr


def make_video(path, fps=30, seconds=2.0, size=(96, 128), color=(255, 64, 0)):
    """A square moving left to right on a black background."""
    h, w = size
    n = int(round(fps * seconds))
    with av.open(path, "w") as container:
        stream = container.add_stream("libx264", rate=fps)
        stream.width, stream.height, stream.pix_fmt = w, h, "yuv420p"
        for i in range(n):
            img = np.zeros((h, w, 3), np.uint8)
            x = int(i / max(n - 1, 1) * (w - 24))
            img[h // 2 - 12 : h // 2 + 12, x : x + 24] = color
            for packet in stream.encode(
                av.VideoFrame.from_ndarray(img, format="rgb24")
            ):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return path


@pytest.fixture(scope="module")
def video30():
    return make_video(os.path.join(tempfile.mkdtemp(), "ref30.mp4"))


def square_x(frame):
    cols = np.where(frame.max(axis=(0, 2)) > 128)[0]
    return cols.mean()


def test_read_resamples_and_resizes(video30, tmp_path):
    frames = mr.read_video_frames(video30, 64, 64, max_frames=1000)
    assert frames.shape == (60, 64, 64, 3) and frames.dtype == np.uint8
    xs = [square_x(f) for f in frames]
    assert all(b >= a for a, b in zip(xs, xs[1:]))  # motion preserved in order

    v15 = make_video(str(tmp_path / "ref15.mp4"), fps=15)
    f15 = mr.read_video_frames(v15, 64, 64, max_frames=1000)
    assert f15.shape[0] == 60  # 2s at 15fps -> 60 output frames at 30fps
    assert np.array_equal(f15[0], f15[1])  # each source frame held twice

    capped = mr.read_video_frames(video30, 64, 64, max_frames=17)
    assert capped.shape[0] == 17

    later = mr.read_video_frames(video30, 64, 64, max_frames=5, start_seconds=1.0)
    assert np.array_equal(later[0], frames[30])


def test_section_slice_alignment():
    ref = torch.arange(20).float().view(1, 1, 20, 1, 1)
    take = lambda *a, **k: mr.section_slice(ref, *a, **k).flatten().tolist()  # noqa: E731
    # F1 with start image: section k covers latents 1 + k*w ...
    assert take(0, 3, 4, True, reverse_order=False) == [1, 2, 3, 4]
    assert take(2, 3, 4, True, reverse_order=False) == [9, 10, 11, 12]
    # Original: first generated section is the last in time
    assert take(0, 3, 4, True, reverse_order=True) == [9, 10, 11, 12]
    assert take(2, 3, 4, False, reverse_order=True) == [0, 1, 2, 3]
    # Short reference holds its last frame
    assert take(4, 5, 4, True, reverse_order=False) == [17, 18, 19, 19]
    assert mr.frames_needed(3, 4, True) == 1 + 12 * 4


@pytest.mark.parametrize("model_type", ["F1", "Original"])
def test_end_to_end(model_type, video30):
    res = fpharness.run(
        model_type,
        motion_reference_video=video30,
        motion_reference_strength=0.6,
        motion_reference_start=0.5,
    )
    assert not res["errors"], res["errors"]
    calls = res["calls"]
    assert len(calls) == 5
    for c in calls:
        assert c["kwargs"]["noise"] is None
        assert c["kwargs"]["strength"] == pytest.approx(0.7)

    # Initial latents are the reference along the output timeline
    h, w = (d * 8 for d in calls[0]["out"].shape[-2:])
    frames = mr.read_video_frames(
        video30, w, h, mr.frames_needed(5, 3, True), start_seconds=0.5
    )
    ref = mr.encode_frames(frames, fpharness.tiny_vae())
    inits = [c["kwargs"]["initial_latent"] for c in calls]
    order = range(5) if model_type == "F1" else reversed(range(5))
    for init, t in zip(inits, order):
        expected = mr.section_slice(ref, t, 5, 3, True, reverse_order=False)
        assert torch.allclose(init, expected, atol=1e-5)


def test_zero_strength_matches_plain_run(video30):
    base = fpharness.run("F1")
    res = fpharness.run(
        "F1",
        motion_reference_video=video30,
        motion_reference_strength=0,
    )
    for a, b in zip(base["calls"], res["calls"]):
        assert torch.equal(a["out"], b["out"])
        assert b["kwargs"]["initial_latent"] is None
        assert b["kwargs"]["noise"] is None


def test_img2img_skips_steps():
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    t = fpharness.tiny_transformer()
    common = dict(
        transformer=t,
        width=64,
        height=64,
        frames=9,
        num_inference_steps=8,
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
        generator=torch.Generator("cpu").manual_seed(0),
    )
    steps = []
    kdh.sample_hunyuan(
        initial_latent=torch.zeros(1, 16, 3, 8, 8),
        strength=0.5,
        callback=lambda d: steps.append(d["i"]),
        **common,
    )
    assert len(steps) == 4


@pytest.mark.parametrize(
    "n,expected", [(1, 1), (5, 2), (17, 5), (60, 16), (61, 16), (62, 17)]
)
def test_encode_keeps_every_frame(n, expected):
    frames = np.random.default_rng(0).integers(0, 255, (n, 32, 32, 3), dtype=np.uint8)
    vae = fpharness.tiny_vae()
    assert mr.encode_frames(frames, vae, batch_size=16).shape[2] == expected
    # Chunk seams don't shift content: the first chunk matches a one-shot encode
    if n >= 17:
        whole = mr.encode_frames(frames[:17], vae, batch_size=64)
        chunked = mr.encode_frames(frames, vae, batch_size=16)
        assert torch.allclose(whole, chunked[:, :, :5], atol=1e-5)
