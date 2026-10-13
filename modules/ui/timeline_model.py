"""
Builds the value drawn by the Timeline component.

All timing comes from the same functions the worker uses, so the timeline
shows where things will really land: sections from the worker's section
count, keyframes from keyframes.snap_keyframe_times, prompt segments from
prompt_handler.parse_timestamped_prompt. The component only draws this.
"""

import os

from modules.pipelines import keyframes
from modules.prompt_handler import parse_timestamped_prompt
from modules.ui import capabilities as caps


def section_count(total_second_length, latent_window_size):
    """Same formula as the worker."""
    sections = (total_second_length * 30) / (latent_window_size * 4)
    return int(max(round(sections), 1))


def _prompt_segments(prompt, duration, latent_window_size):
    text = (prompt or "").strip()
    if not text:
        return []
    # "F1" keeps the user's own time order; the worker reverses it internally
    # for Original, which is a generation detail, not where things appear.
    parsed = parse_timestamped_prompt(text, duration, latent_window_size, "F1")
    segments = []
    for section in parsed:
        start = min(max(section.start_time, 0.0), duration)
        end = duration if section.end_time is None else section.end_time
        end = min(max(end, start), duration)
        if end - start < 0.05:
            continue  # starts after the video ends, so it's never used
        segments.append(
            {"start": round(start, 2), "end": round(end, 2), "text": section.prompt}
        )
    if segments:
        # Snapping can pull the last end short of the video; it runs to the end.
        segments[-1]["end"] = duration
    return segments


def build_timeline(
    *,
    total_second_length,
    latent_window_size,
    model,
    source,
    prompt="",
    blend_sections=0,
    has_start=False,
    has_end=False,
    keyframe_slots=(),
    camera="None",
    camera_amount=0.0,
    arrow_count=0,
    reference_path=None,
    reroll_from_section=None,
    selectable=False,
):
    """
    keyframe_slots: sequence of (time_seconds, has_image) per keyframe slot.
    reroll_from_section: 1-based section in generation order, or None.
    """
    window = int(latent_window_size or 9)
    total = section_count(float(total_second_length or 1), window)
    step = keyframes.section_seconds(window)
    duration = round(total * step, 2)

    if source == "Video":
        direction = None  # the generation order for video sources isn't defined here
    elif model == "Original":
        direction = "backward"
    else:
        direction = "forward"

    sections = []
    for i in range(total):
        order = None
        if direction == "backward":
            order = total - i
        elif direction == "forward":
            order = i + 1
        state = "normal"
        if reroll_from_section and order is not None:
            state = "regen" if order >= reroll_from_section else "kept"
        sections.append(
            {
                "start": round(i * step, 2),
                "end": round((i + 1) * step, 2),
                "order": order,
                "state": state,
            }
        )

    keyframes_ok = caps.supports("keyframes", model, source)
    frames = [
        {
            "kind": "start",
            "t": 0.0,
            "label": "Source" if source == "Video" else "Start",
            "set": bool(has_start),
        }
    ]
    times = [float(t or 0.0) for t, _ in keyframe_slots]
    snapped = dict(keyframes.snap_keyframe_times(times, total, window))
    snapped_by_slot = {slot: boundary * step for boundary, slot in snapped.items()}
    for index, (t, has_image) in enumerate(keyframe_slots):
        if not has_image:
            continue
        snap = snapped_by_slot.get(index)
        frames.append(
            {
                "kind": "key",
                "t": round(float(t or 0.0), 2),
                "snapped": None if snap is None else round(snap, 2),
                "label": f"K{index + 1}"
                if snap is not None
                else f"K{index + 1} (ignored)",
                "index": index,
                "set": True,
            }
        )
    if caps.supports("end_frame", model, source):
        frames.append(
            {"kind": "end", "t": duration, "label": "End", "set": bool(has_end)}
        )

    lanes = []
    motion_bits = []
    if camera and camera != "None" and camera_amount:
        motion_bits.append(f"{camera} · {round(camera_amount * 100)}%")
    if arrow_count:
        motion_bits.append(f"{arrow_count} arrow{'s' if arrow_count != 1 else ''}")
    if motion_bits:
        lanes.append(
            {
                "id": "camera",
                "label": "Motion",
                "text": " · ".join(motion_bits),
                "start": 0.0,
                "end": duration,
                "enabled": caps.supports("motion_sketch", model, source),
                "reason": caps.unsupported_reason("motion_sketch", model, source),
            }
        )
    if reference_path:
        lanes.append(
            {
                "id": "reference",
                "label": "Reference",
                "text": os.path.basename(str(reference_path)),
                "start": 0.0,
                "end": duration,
                "enabled": caps.supports("motion_reference", model, source),
                "reason": caps.unsupported_reason("motion_reference", model, source),
            }
        )

    return {
        "duration": duration,
        "direction": direction,
        "sections": sections,
        "prompts": _prompt_segments(prompt, duration, window),
        "blend": round(float(blend_sections or 0) * step, 2),
        "frames": frames,
        "lanes": lanes,
        "keyframes_enabled": keyframes_ok,
        "keyframes_reason": caps.unsupported_reason("keyframes", model, source),
        "selected_section": None,
        "selectable": bool(selectable),
    }


def keyframe_times_from_timeline(value, current_times):
    """Read keyframe times back from an edited timeline value."""
    times = list(current_times)
    for frame in (value or {}).get("frames", []):
        if frame.get("kind") == "key" and frame.get("index") is not None:
            index = int(frame["index"])
            if 0 <= index < len(times):
                times[index] = round(float(frame.get("t", times[index])), 1)
    return times
