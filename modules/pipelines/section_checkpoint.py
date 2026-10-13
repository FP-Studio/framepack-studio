"""
Section checkpoints: save a job's latent state so later jobs can re-roll
from any section onward while keeping the sections before it untouched.

A checkpoint holds the *full* history_latents (including the context
padding and any end-frame latent) plus the number of latent frames each
section produced, in generation order. That is enough to rebuild the exact
sampler state before any section by slicing.

Generation order differs per model family:
  - F1 appends sections, so generation order == time order.
  - Original prepends sections (it generates from the end of the video
    backwards), so re-rolling from section k regenerates the *start* of the
    video while keeping the tail.
"""

import glob
import json
import logging
import os

import torch

logger = logging.getLogger(__name__)

CHECKPOINT_VERSION = 1
CHECKPOINT_SUFFIX = "_sections.pt"
SUMMARY_SUFFIX = "_sections.json"  # small sidecar so the UI never loads latents
SUMMARY_KEYS = (
    "model_type",
    "height",
    "width",
    "latent_window_size",
    "has_input_image",
    "section_frames",
)
REROLL_MODEL_TYPES = ("Original", "Original with Endframe", "F1")
LATENT_FPS = 30 / 4  # one latent frame covers four pixel frames at 30fps


def is_prepending_model(model_type):
    return model_type in ("Original", "Original with Endframe")


def checkpoint_path(output_dir, job_id):
    return os.path.join(output_dir, f"{job_id}{CHECKPOINT_SUFFIX}")


def summary_path(path):
    return path[: -len(CHECKPOINT_SUFFIX)] + SUMMARY_SUFFIX


def save_section_checkpoint(path, **state):
    """Atomically write a checkpoint so a crash never leaves a torn file."""
    state["version"] = CHECKPOINT_VERSION
    state = {
        k: (v.detach().cpu() if torch.is_tensor(v) else v) for k, v in state.items()
    }
    tmp_path = path + ".tmp"
    torch.save(state, tmp_path)
    os.replace(tmp_path, path)
    summary = {k: state[k] for k in SUMMARY_KEYS}
    with open(summary_path(path) + ".tmp", "w") as f:
        json.dump(summary, f)
    os.replace(summary_path(path) + ".tmp", summary_path(path))


def load_summary(path):
    """The checkpoint's metadata without loading its latents."""
    try:
        with open(summary_path(path)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {
            k: v for k, v in load_section_checkpoint(path).items() if k in SUMMARY_KEYS
        }


def load_section_checkpoint(path):
    if not path or not os.path.exists(path):
        raise ValueError(f"Section checkpoint not found: {path}")
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    if ckpt.get("version") != CHECKPOINT_VERSION:
        raise ValueError(
            f"Unsupported section checkpoint version {ckpt.get('version')} in {path}"
        )
    return ckpt


def validate_checkpoint(
    ckpt,
    model_type,
    height,
    width,
    latent_window_size,
    latent_paddings,
    has_input_image,
    reroll_from_section,
):
    """Raise ValueError if a checkpoint can't seed a re-roll of this job."""
    if model_type not in REROLL_MODEL_TYPES:
        raise ValueError(f"Section re-roll is not supported for {model_type} jobs.")
    expected = {
        "model_type": model_type,
        "height": height,
        "width": width,
        "latent_window_size": latent_window_size,
        "latent_paddings": list(latent_paddings),
        "has_input_image": has_input_image,
    }
    for key, value in expected.items():
        if ckpt.get(key) != value:
            raise ValueError(
                f"Section re-roll mismatch for '{key}': checkpoint has "
                f"{ckpt.get(key)!r}, this job has {value!r}. Use the same model, "
                "resolution, video length and latent window size as the original job"
                + (
                    " (and add a start image only if the original had one)."
                    if key == "has_input_image"
                    else "."
                )
            )
    saved = len(ckpt["section_frames"])
    if not 1 <= reroll_from_section <= saved:
        raise ValueError(
            f"Can only re-roll from section 1..{saved} of this checkpoint "
            f"(got {reroll_from_section})."
        )


def history_before_section(ckpt, section, init_len):
    """
    Rebuild history_latents as it was right before `section` (0-based,
    generation order) was sampled.

    init_len is the length of the freshly initialised history (context
    padding plus, for F1, the start latent).
    """
    kept = list(ckpt["section_frames"][:section])
    history = ckpt["history_latents"]
    keep_len = init_len + sum(kept)
    if is_prepending_model(ckpt["model_type"]):
        restored = history[:, :, history.shape[2] - keep_len :]
    else:
        restored = history[:, :, :keep_len]
    return restored.clone(), kept


def section_time_ranges(ckpt):
    """
    Approximate (start_s, end_s) of each section in generation order.
    """
    frames = list(ckpt["section_frames"])
    lead = (
        1
        if ckpt["has_input_image"] and not is_prepending_model(ckpt["model_type"])
        else 0
    )
    ranges = []
    if is_prepending_model(ckpt["model_type"]):
        total = sum(frames)
        end = total
        for count in frames:
            ranges.append(((end - count) / LATENT_FPS, end / LATENT_FPS))
            end -= count
    else:
        start = lead
        for count in frames:
            ranges.append((start / LATENT_FPS, (start + count) / LATENT_FPS))
            start += count
    return ranges


def section_choices(ckpt):
    """Dropdown (label, value) pairs; value is the 1-based section number."""
    choices = []
    for i, (start, end) in enumerate(section_time_ranges(ckpt), start=1):
        choices.append((f"Section {i} (~{start:.1f}s-{end:.1f}s)", i))
    return choices


def list_checkpoints(output_dir):
    """Checkpoint paths in output_dir, newest first."""
    if not output_dir or not os.path.isdir(output_dir):
        return []
    paths = glob.glob(os.path.join(output_dir, f"*{CHECKPOINT_SUFFIX}"))
    return sorted(paths, key=os.path.getmtime, reverse=True)


def checkpoint_label(path):
    job_id = os.path.basename(path)[: -len(CHECKPOINT_SUFFIX)]
    try:
        ckpt = load_summary(path)
    except Exception as e:
        logger.debug(f"Skipping unreadable section checkpoint {path}: {e}")
        return None
    return (
        f"{job_id} - {ckpt['model_type']}, {len(ckpt['section_frames'])} sections, "
        f"{ckpt['width']}x{ckpt['height']}"
    )
