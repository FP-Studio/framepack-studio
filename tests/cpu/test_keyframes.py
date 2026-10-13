"""Keyframe planning + end-to-end tests (run from the section-reroll checkout)."""

import os

import pytest
import torch

import fpharness
from modules.generators.original_generator import OriginalModelGenerator
from modules.pipelines import keyframes as kf
from modules.pipelines import section_checkpoint as sc

PADDINGS = OriginalModelGenerator.get_latent_paddings


def _paddings(n):
    return PADDINGS(None, n)


def test_snap_times():
    # window 3 -> 0.4s sections; 5 sections
    assert kf.snap_keyframe_times([0.8], 5, 3) == [(2, 0)]
    assert kf.snap_keyframe_times([1.3, 0.35], 5, 3) == [(1, 1), (3, 0)]
    # start, end, and duplicate boundaries are dropped
    assert kf.snap_keyframe_times([0.0, 2.0, 0.8, 0.85], 5, 3) == [(2, 2)]


def test_plan_without_keyframes_matches_generator():
    for n in range(1, 9):
        plans = kf.plan_sections(_paddings, n, [])
        assert [p.padding for p in plans] == _paddings(n)
        assert not any(p.starts_at_keyframe for p in plans)
        assert all(p.anchor == 0 for p in plans)


def test_plan_with_keyframes():
    plans = kf.plan_sections(_paddings, 5, [2])
    assert [p.padding for p in plans] == [2, 1, 0, 1, 0]
    assert [p.anchor for p in plans] == [1, 1, 1, 0, 0]
    assert [p.starts_at_keyframe for p in plans] == [False, False, True, False, False]

    plans = kf.plan_sections(_paddings, 8, [1, 6])
    assert [p.padding for p in plans] == [1, 0, 3, 2, 2, 1, 0, 0]
    assert [p.anchor for p in plans] == [2, 2, 1, 1, 1, 1, 1, 0]


KEYFRAME = fpharness.default_image(seed=42)


def _ckpt(res):
    name = [f for f in res["job_files"] if f.endswith(sc.CHECKPOINT_SUFFIX)][0]
    return sc.load_section_checkpoint(os.path.join(res["out_dir"], name))


@pytest.mark.parametrize("model_type", ["Original", "Original with Endframe"])
def test_keyframe_conditions_neighbouring_sections(model_type):
    extra = {}
    if model_type == "Original with Endframe":
        extra = dict(end_frame_image=fpharness.default_image(seed=7))
    base = fpharness.run(model_type, **extra)
    res = fpharness.run(
        model_type, keyframe_images=[KEYFRAME], keyframe_times=[0.8], **extra
    )
    assert not res["errors"], res["errors"]
    calls = res["calls"]
    assert len(calls) == 5

    # Section starting at the keyframe: pre latent is the keyframe, padding 0
    at = calls[2]["kwargs"]
    key_latent = at["clean_latents"][:, :, :1]
    assert at["latent_indices"][0, 0].item() == 1
    assert at["clean_latent_indices"][0, 0].item() == 0
    assert not torch.equal(key_latent, calls[4]["kwargs"]["clean_latents"][:, :, :1])

    # It is conditioned on the keyframe's CLIP embedding, not the start image's
    from diffusers_helper.utils import resize_and_center_crop

    h, w = (d * 8 for d in at["clean_latents"].shape[-2:])
    resized = resize_and_center_crop(KEYFRAME, w, h)
    clip_key = fpharness.fake_clip_encode(resized, None, None).last_hidden_state
    assert torch.equal(at["image_embeddings"], clip_key.to(torch.bfloat16).float())
    assert not torch.equal(
        calls[4]["kwargs"]["image_embeddings"], at["image_embeddings"]
    )

    # Section just before the keyframe: post latent is the keyframe
    before = calls[3]["kwargs"]
    assert torch.equal(before["clean_latents"][:, :, 1:2], key_latent)
    assert torch.equal(
        before["clean_latents"][:, :, :1], calls[4]["kwargs"]["clean_latents"][:, :, :1]
    )

    # The keyframe latent sits in the final video at its time position
    ckpt = _ckpt(res)
    assert ckpt["section_frames"] == [3, 3, 4, 3, 4]
    hist = ckpt["history_latents"]
    # time order: [start, s0, s0, s0, s1 x3, key, s2 x3, ...]
    assert torch.equal(hist[:, :, 7:8], key_latent)

    assert not torch.equal(base["calls"][2]["out"], calls[2]["out"])
    assert res["videos"][-1][1].shape[2] == base["videos"][-1][1].shape[2] + 4


def test_keyframes_ignored_for_f1():
    base = fpharness.run("F1")
    res = fpharness.run("F1", keyframe_images=[KEYFRAME], keyframe_times=[0.8])
    assert not res["errors"]
    for a, b in zip(base["calls"], res["calls"]):
        assert torch.equal(a["out"], b["out"])


def test_reroll_with_keyframes():
    full = fpharness.run("Original", keyframe_images=[KEYFRAME], keyframe_times=[0.8])
    name = [f for f in full["job_files"] if f.endswith(sc.CHECKPOINT_SUFFIX)][0]
    rer = fpharness.run(
        "Original",
        keyframe_images=[KEYFRAME],
        keyframe_times=[0.8],
        reroll_latents_path=os.path.join(full["out_dir"], name),
        reroll_from_section=4,
    )
    assert not rer["errors"], rer["errors"]
    for a, b in zip(full["calls"][3:], rer["calls"]):
        assert torch.equal(a["out"], b["out"])
    # A different keyframe layout changes the padding schedule and is rejected
    bad = fpharness.run(
        "Original",
        reroll_latents_path=os.path.join(full["out_dir"], name),
        reroll_from_section=4,
    )
    assert bad["errors"] and "latent_paddings" in bad["errors"][0]
