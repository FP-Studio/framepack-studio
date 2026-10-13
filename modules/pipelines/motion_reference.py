"""
Motion reference: follow the motion and layout of a reference video.

The reference is VAE-encoded at the output resolution and frame rate, and each
section starts denoising part-way from its time-aligned slice instead of from
pure noise. The first steps are skipped only up to a high noise level, where
the picture's fine detail and colour are already drowned out, so what carries
over is where things are and how they move; the prompt and start frame decide
what they look like.
"""

import logging

import av
import numpy as np
import torch

from diffusers_helper.utils import resize_and_center_crop

logger = logging.getLogger(__name__)

MOTION_REFERENCE_MODEL_TYPES = ("Original", "Original with Endframe", "F1")
OUTPUT_FPS = 30


def read_video_frames(
    path, width, height, max_frames, fps=OUTPUT_FPS, start_seconds=0.0
):
    """
    Decode up to max_frames frames resampled to `fps`, resized and center
    cropped to width x height, starting `start_seconds` into the clip.
    Returns uint8 (T, H, W, 3).
    """
    times, images = [], []
    end_time = max_frames / fps
    with av.open(path) as container:
        start_time = None
        for frame in container.decode(video=0):
            if frame.time is None:
                continue
            if start_time is None:
                if frame.time < start_seconds - 0.5 / fps:
                    continue
                start_time = frame.time
            if frame.time - start_time > end_time:
                break
            image = frame.to_ndarray(format="rgb24")
            times.append(frame.time - start_time)
            images.append(resize_and_center_crop(image, width, height))
    if not images:
        raise ValueError(f"Could not read any frames from motion reference {path}")

    # Show, at each output time, the latest source frame at or before it.
    times = np.asarray(times)
    duration = times[-1] + (times[-1] - times[-2] if len(times) > 1 else 1 / fps)
    count = min(max_frames, max(1, int(np.ceil(duration * fps - 1e-6))))
    picks = np.searchsorted(times, np.arange(count) / fps + 1e-6, side="right") - 1
    return np.stack([images[i] for i in np.clip(picks, 0, len(images) - 1)])


@torch.no_grad()
def encode_frames(frames, vae, batch_size=16):
    """
    VAE-encode (T, H, W, 3) uint8 frames in chunks, keeping latent j aligned
    with pixel frames 4j-3..4j like the output timeline.

    The VAE is causal with 4x temporal compression: a clip of 1 + 4k frames
    gives 1 + k latents, the first holding a single frame. Each chunk after
    the first re-encodes the previous chunk's last frame and drops that
    single-frame latent, so no frames are lost at chunk seams. Uses the
    latent mean so the reference is deterministic.
    """
    pixels = torch.from_numpy(frames).float() / 127.5 - 1
    pixels = pixels.permute(3, 0, 1, 2)[None]  # (1, C, T, H, W)
    pad = (-(pixels.shape[2] - 1)) % 4
    if pad:
        pixels = torch.cat([pixels, pixels[:, :, -1:].expand(-1, -1, pad, -1, -1)], 2)
    step = max(4, batch_size // 4 * 4)
    latents = []
    for start in range(0, pixels.shape[2] - 1 or 1, step):
        batch = pixels[:, :, start : start + step + 1]
        batch = batch.to(device=vae.device, dtype=vae.dtype)
        latent = vae.encode(batch).latent_dist.mode() * vae.config.scaling_factor
        latents.append(
            latent.float().cpu() if start == 0 else latent[:, :, 1:].float().cpu()
        )
    return torch.cat(latents, dim=2)


def frames_needed(total_sections, latent_window_size, has_input_image):
    latent_frames = int(has_input_image) + total_sections * latent_window_size
    return 1 + (latent_frames - 1) * 4


def section_slice(
    reference_latents,
    generation_index,
    total_sections,
    latent_window_size,
    has_input_image,
    reverse_order,
):
    """
    Reference latents for one section, aligned with the output timeline.

    Output latent 0 is the start image (when there is one), and each section
    adds latent_window_size frames. Original models generate sections from
    the end backwards (reverse_order=True). Short references hold their last
    frame.
    """
    time_index = (
        total_sections - 1 - generation_index if reverse_order else generation_index
    )
    start = int(has_input_image) + time_index * latent_window_size
    idx = torch.arange(start, start + latent_window_size).clamp(
        max=reference_latents.shape[2] - 1
    )
    return reference_latents[:, :, idx]
