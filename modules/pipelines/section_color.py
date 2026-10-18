"""
Colour lock: keep each new section's colour statistics close to the start
frame's, so colour drift, oversaturation and section-to-section flashing
can't build up (F1 especially, where every section is generated from the
ones before it).

Each latent channel's mean and standard deviation over the whole section are
moved toward the start latent's by `strength` (0 = off, 1 = matched exactly).
It runs on the new section before it joins the history, so later sections
are generated from corrected frames.
"""

import torch


def match_start(section, start_latent, strength):
    """Move section's per-channel mean/std (B, C, T, H, W) toward start_latent's."""
    if not strength or start_latent is None:
        return section
    dims = (2, 3, 4)
    x = section.float()
    ref = start_latent.to(x)
    x_mean, x_std = x.mean(dims, keepdim=True), x.std(dims, keepdim=True)
    ref_mean, ref_std = ref.mean(dims, keepdim=True), ref.std(dims, keepdim=True)
    matched = (x - x_mean) / x_std.clamp(min=1e-6) * ref_std + ref_mean
    return (x + float(strength) * (matched - x)).to(section.dtype)
