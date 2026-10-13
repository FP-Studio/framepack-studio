"""End-to-end section re-roll tests (run from a framepack-studio checkout)."""

import os

import pytest
import torch

import fpharness
from modules.pipelines import section_checkpoint as sc


def _ckpt(res):
    paths = [f for f in os.listdir(res["out_dir"]) if f.endswith(sc.CHECKPOINT_SUFFIX)]
    assert len(paths) == 1, paths
    return os.path.join(res["out_dir"], paths[0])


CASES = [
    ("F1", {}),
    ("Original", {}),
    (
        "Original with Endframe",
        {"end_frame_image": fpharness.default_image(seed=7), "end_frame_strength": 0.8},
    ),
]


@pytest.mark.parametrize("model_type,extra", CASES)
@pytest.mark.parametrize("from_section", [2, 4])
def test_reroll_same_seed_reproduces_full_run(model_type, extra, from_section):
    full = fpharness.run(model_type, **extra)
    assert not full["errors"]
    n = len(full["calls"])
    assert n == 5
    path = _ckpt(full)

    # A different start image proves the checkpoint's conditioning is what's used.
    rer = fpharness.run(
        model_type,
        input_image=fpharness.default_image(seed=99),
        reroll_latents_path=path,
        reroll_from_section=from_section,
        **extra,
    )
    assert not rer["errors"], rer["errors"]
    assert len(rer["calls"]) == n - (from_section - 1)
    for a, b in zip(full["calls"][from_section - 1 :], rer["calls"]):
        assert torch.equal(a["out"], b["out"])

    full_hist = sc.load_section_checkpoint(path)["history_latents"]
    rer_ckpt = sc.load_section_checkpoint(_ckpt(rer))
    assert torch.equal(full_hist, rer_ckpt["history_latents"])
    assert rer["videos"][-1][1].shape == full["videos"][-1][1].shape


@pytest.mark.parametrize("model_type", ["F1", "Original"])
def test_reroll_new_seed_keeps_earlier_sections(model_type):
    full = fpharness.run(model_type)
    path = _ckpt(full)
    rer = fpharness.run(
        model_type, seed=4321, reroll_latents_path=path, reroll_from_section=3
    )
    assert not rer["errors"]
    assert not torch.equal(full["calls"][2]["out"], rer["calls"][0]["out"])

    ckpt = sc.load_section_checkpoint(path)
    new = sc.load_section_checkpoint(_ckpt(rer))
    assert new["section_frames"] == ckpt["section_frames"]
    kept, _ = sc.history_before_section(ckpt, 2, init_len=19 + (model_type == "F1"))
    kept_new, _ = sc.history_before_section(new, 2, init_len=19 + (model_type == "F1"))
    assert torch.equal(kept, kept_new)
    assert not torch.equal(ckpt["history_latents"], new["history_latents"])


@pytest.mark.parametrize("model_type", ["F1", "Original"])
def test_reroll_continues_cancelled_job(model_type):
    full = fpharness.run(model_type)
    cancelled = fpharness.run(model_type, cancel_after=2)
    assert len(cancelled["calls"]) == 2
    ckpt = sc.load_section_checkpoint(_ckpt(cancelled))
    assert len(ckpt["section_frames"]) == 2
    # Cancelling keeps what was generated; re-rolling the last saved section
    # carries on exactly as the uncancelled job would have.
    rer = fpharness.run(
        model_type, reroll_latents_path=_ckpt(cancelled), reroll_from_section=2
    )
    assert not rer["errors"]
    assert len(rer["calls"]) == 4
    for a, b in zip(full["calls"][1:], rer["calls"]):
        assert torch.equal(a["out"], b["out"])


def test_summary_sidecar_matches_checkpoint():
    res = fpharness.run("Original")
    path = _ckpt(res)
    summary = sc.load_summary(path)
    ckpt = sc.load_section_checkpoint(path)
    for key in sc.SUMMARY_KEYS:
        assert summary[key] == ckpt[key]
    assert sc.section_choices(summary) == sc.section_choices(ckpt)
    label = sc.checkpoint_label(path)
    assert "Original, 5 sections" in label
    # Labels still work for checkpoints without a sidecar
    os.remove(sc.summary_path(path))
    assert sc.checkpoint_label(path) == label


def test_reroll_rejects_mismatched_job():
    full = fpharness.run("F1")
    rer = fpharness.run(
        "F1",
        total_second_length=3,
        reroll_latents_path=_ckpt(full),
        reroll_from_section=2,
    )
    assert rer["errors"] and "latent_paddings" in rer["errors"][0]
    assert not rer["calls"]


def test_section_choices_cover_video():
    for model_type in ("F1", "Original"):
        ckpt = sc.load_section_checkpoint(_ckpt(fpharness.run(model_type)))
        ranges = sc.section_time_ranges(ckpt)
        assert len(sc.section_choices(ckpt)) == 5
        ordered = sorted(ranges)
        for (_, end), (start, _) in zip(ordered, ordered[1:]):
            assert end == pytest.approx(start)
        if model_type == "Original":
            assert ranges[0][1] > ranges[-1][1]  # generated from the end backwards
