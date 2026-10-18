"""
Loosen the start image's pull on FramePack Original's opening seconds.

Original renders backwards: the time-0 section comes last, squeezed between
the start frame and a finished future, which is where the slow start comes
from. Three inference-time dials, all off by default:

- start_attention: a weight (0..1) on how much every token attends to the
  start image (its latent frame and its SigLIP tokens), applied while the
  time-0 section renders (or every section). Lower means a weaker anchor.
- start_gap: move the start frame N latent frames further back in time while
  the time-0 section renders, so the model treats it as further away.
- start_shift: the same move, in every section.

One latent frame is 4 video frames. Gap and shift only change the start
frame's RoPE time index; no tokens are added.
"""

import torch

from diffusers_helper.models import hunyuan_video_packed

MODEL_TYPES = ("Original", "Original with Endframe")


def shift_start_frame(clean_latent_indices, amount):
    """Move the start frame (the first clean index) `amount` latent frames back."""
    if not amount:
        return clean_latent_indices
    shifted = clean_latent_indices.to(torch.float32).clone()
    shifted[:, 0] -= float(amount)
    return shifted


def set_section_attention(weight):
    """Weight on attention to the start image for the next sampling call, or None."""
    hunyuan_video_packed.set_start_attention(weight)
