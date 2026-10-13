"""
Mid-video keyframes for the Original models.

The Original model generates sections from the end of the video backwards.
Each section sees a "pre" clean latent (normally the start image, placed
`padding` windows before it) and a "post" clean latent (the first frame of
the section generated just before it, i.e. the next one in time).

A keyframe at a section boundary splits the video into segments. Inside a
segment everything works exactly like a normal Original job whose start
image is the keyframe:
  - the section that starts at the keyframe uses it as its pre latent with
    padding 0, and the keyframe latent is prepended to that section's output;
  - so the section just before the keyframe (generated next) gets the
    keyframe as its post latent, the same way the end frame is handled.
Both conditioning paths are ones the model was trained on.
"""

from dataclasses import dataclass

KEYFRAME_MODEL_TYPES = ("Original", "Original with Endframe")


@dataclass
class SectionPlan:
    padding: int  # latent padding in windows, as from get_latent_paddings
    anchor: int  # 0 = start image, k > 0 = keyframe k (1-based, time order)
    starts_at_keyframe: bool  # section begins at a mid-video keyframe


def section_seconds(latent_window_size, fps=30):
    return latent_window_size * 4 / fps


def snap_keyframe_times(times, total_sections, latent_window_size):
    """
    Snap keyframe times (seconds) to section boundaries.

    Returns sorted (boundary, input_index) pairs where boundary is the index
    (time order, 1..total_sections-1) of the section the keyframe starts.
    Keyframes that snap to the very start or end, or onto an earlier
    keyframe's boundary, are dropped.
    """
    step = section_seconds(latent_window_size)
    snapped = {}
    for idx, t in sorted(enumerate(times), key=lambda p: p[1]):
        boundary = int(round(float(t) / step))
        if 1 <= boundary <= total_sections - 1 and boundary not in snapped:
            snapped[boundary] = idx
    return sorted(snapped.items())


def plan_sections(get_latent_paddings, total_sections, boundaries):
    """
    Build the per-section plan in generation order (last segment first).

    get_latent_paddings is the generator's own padding schedule, applied to
    each segment independently so every segment looks like a normal job.
    """
    edges = [0] + list(boundaries) + [total_sections]
    plans = []
    for segment in reversed(range(len(edges) - 1)):
        length = edges[segment + 1] - edges[segment]
        for padding in get_latent_paddings(length):
            plans.append(
                SectionPlan(
                    padding=padding,
                    anchor=segment,
                    starts_at_keyframe=padding == 0 and segment > 0,
                )
            )
    return plans
