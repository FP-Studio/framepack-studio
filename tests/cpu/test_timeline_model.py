from modules.pipelines import section_checkpoint
from modules.ui.timeline_model import (
    apply_progress,
    job_direction,
    build_timeline,
    keyframe_times_from_timeline,
    section_count,
)


def _timeline(**kw):
    args = dict(
        total_second_length=6, latent_window_size=9, model="Original", source="Image"
    )
    args.update(kw)
    return build_timeline(**args)


def test_sections_match_worker_count():
    tl = _timeline()
    assert len(tl["sections"]) == section_count(6, 9) == 5
    assert tl["duration"] == 6.0
    # 7 s rounds to 6 sections of 1.2 s
    assert _timeline(total_second_length=7)["duration"] == 7.2


def test_original_generates_backwards():
    tl = _timeline()
    assert tl["direction"] == "backward"
    assert [s["order"] for s in tl["sections"]] == [5, 4, 3, 2, 1]
    tl = _timeline(model="F1")
    assert tl["direction"] == "forward"
    assert [s["order"] for s in tl["sections"]] == [1, 2, 3, 4, 5]


def test_video_source_has_no_direction():
    tl = _timeline(source="Video")
    assert tl["direction"] is None
    assert all(s["order"] is None for s in tl["sections"])


def test_section_order_matches_reroll_labels():
    """Section N in the timeline covers the same seconds as re-roll's Section N."""
    tl = _timeline()
    ckpt = {
        "model_type": "Original",
        "has_input_image": False,
        "section_frames": [9, 9, 9, 9, 9],  # latent frames
    }
    ranges = section_checkpoint.section_time_ranges(ckpt)
    by_order = {s["order"]: (s["start"], s["end"]) for s in tl["sections"]}
    for order, (start, end) in enumerate(ranges, start=1):
        assert by_order[order] == (round(start, 2), round(end, 2))


def test_keyframes_snap_like_the_worker():
    tl = _timeline(keyframe_slots=[(2.0, True), (3.0, True), (5.9, True)])
    keys = [f for f in tl["frames"] if f["kind"] == "key"]
    assert [k["snapped"] for k in keys] == [2.4, None, None]
    assert keys[1]["label"] == "K2 (ignored)"  # 3.0 s snaps onto K1's boundary
    assert keys[2]["label"] == "K3 (ignored)"  # 5.9 s snaps onto the very end


def test_empty_keyframe_slots_are_hidden():
    tl = _timeline(keyframe_slots=[(2.0, False), (4.0, True)])
    assert [f["index"] for f in tl["frames"] if f["kind"] == "key"] == [1]


def test_keyframes_disabled_on_f1():
    tl = _timeline(model="F1")
    assert not tl["keyframes_enabled"]
    assert tl["keyframes_reason"] == "Keyframes only works with Original."
    assert not any(f["kind"] == "end" for f in tl["frames"])


def test_reroll_marks_kept_and_regenerated():
    tl = _timeline(reroll_from_section=3)
    assert [s["state"] for s in tl["sections"]] == [
        "regen",
        "regen",
        "regen",
        "kept",
        "kept",
    ]


def test_prompt_segments_in_user_time_order():
    tl = _timeline(prompt="[0s: wave] [3s: jump]")
    assert [p["text"] for p in tl["prompts"]] == ["wave", "jump"]
    assert tl["prompts"][0]["start"] == 0.0
    assert tl["prompts"][-1]["end"] == 6.0


def test_lanes_flag_unsupported_motion():
    tl = _timeline(source="Video", camera="Pan right", camera_amount=0.3, arrow_count=2)
    lane = tl["lanes"][0]
    assert lane["text"] == "Pan right · 30% · 2 arrows"
    assert not lane["enabled"]
    assert "Camera moves and arrows only works with" in lane["reason"]


def test_keyframe_times_from_timeline():
    value = {"frames": [{"kind": "key", "index": 1, "t": 3.62}]}
    assert keyframe_times_from_timeline(value, [2.0, 4.0, 6.0]) == [2.0, 3.6, 6.0]


def test_prompts_after_the_end_are_dropped():
    tl = _timeline(total_second_length=1.2, prompt="[0s: wave] [5s: dance]")
    assert [p["text"] for p in tl["prompts"]] == ["wave"]


def _progress_timeline(model="Original", reroll=None):
    return _timeline(model=model, reroll_from_section=reroll)


def states(value):
    return [s["state"] for s in value["sections"]]


def test_progress_marks_generation_order():
    # Original generates backwards: order 1 is the last section in time
    value = apply_progress(_progress_timeline(), current_section=2, total_sections=5)
    assert states(value) == ["normal", "normal", "normal", "generating", "done"]
    value = apply_progress(
        _progress_timeline("F1"), current_section=2, total_sections=5
    )
    assert states(value) == ["done", "generating", "normal", "normal", "normal"]


def test_progress_clears_and_skips_mismatched_jobs():
    marked = apply_progress(_progress_timeline(), 3, 5)
    cleared = apply_progress(marked)
    assert set(states(cleared)) == {"normal"}
    # A job with a different section count isn't drawn on this timeline
    assert apply_progress(_progress_timeline(), 1, 7) is None
    # Nothing to change -> None, so the timer sends no update
    assert apply_progress(cleared) is None


def test_progress_leaves_reroll_states_alone():
    # Every section is "kept" or "regen" while re-rolling; progress doesn't
    # repaint them, so there's nothing to update
    timeline = _progress_timeline(reroll=3)
    assert set(states(timeline)) == {"kept", "regen"}
    assert apply_progress(timeline, current_section=4, total_sections=5) is None


def test_progress_follows_the_running_jobs_direction():
    # An F1 guide queued from an Original setup fills the timeline front to back
    value = apply_progress(
        _progress_timeline(), current_section=2, total_sections=5, direction="forward"
    )
    assert states(value) == ["done", "generating", "normal", "normal", "normal"]
    assert job_direction("F1") == "forward"
    assert job_direction("Original with Endframe") == "backward"
    assert job_direction("Video") is None
