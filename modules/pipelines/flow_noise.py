"""
Flow-warped starting noise: steer motion by moving the noise.

Diffusion models tend to keep structure that is already present in their
starting noise. If every frame starts from the *same* noise pattern, shifted
along a motion field, the model is nudged to move content the same way.

Motion comes from drag arrows on the start frame and/or a camera preset.
Noise is warped with nearest-neighbour sampling, which keeps every value an
exact N(0, 1) sample (bilinear blending would shrink the variance), and then
mixed with fresh noise:

    n_t = sqrt(a) * warp(n_0, t * v) + sqrt(1 - a) * eps_t

`a` is the flow strength; a = 1 moves a frozen noise pattern, a = 0 is plain
noise. This is training-free, so it biases motion rather than dictating it.
"""

import math

import torch

FLOW_NOISE_MODEL_TYPES = ("Original", "Original with Endframe", "F1")
CAMERA_MOVES = (
    "None",
    "Pan left",
    "Pan right",
    "Pan up",
    "Pan down",
    "Zoom in",
    "Zoom out",
)


def camera_velocity(move, amount, height, width, total_frames):
    """
    (2, H, W) displacement per latent frame, in latent pixels (dx, dy).

    amount is the fraction of the frame the camera travels over the video.
    Panning the camera left makes the scene move right, and so on.
    """
    v = torch.zeros(2, height, width)
    if move == "None" or amount <= 0 or total_frames <= 1:
        return v
    steps = total_frames - 1
    if move.startswith("Pan"):
        dx, dy = {
            "Pan left": (1, 0),
            "Pan right": (-1, 0),
            "Pan up": (0, 1),
            "Pan down": (0, -1),
        }[move]
        v[0] = dx * amount * width / steps
        v[1] = dy * amount * height / steps
    elif move.startswith("Zoom"):
        ys, xs = torch.meshgrid(
            torch.arange(height) - (height - 1) / 2,
            torch.arange(width) - (width - 1) / 2,
            indexing="ij",
        )
        sign = 1 if move == "Zoom in" else -1
        v[0] = sign * xs * amount / steps
        v[1] = sign * ys * amount / steps
    else:
        raise ValueError(f"Unknown camera move: {move}")
    return v


def arrow_velocity(arrows, height, width, total_frames, radius=0.15):
    """
    (2, H, W) displacement per latent frame from drag arrows.

    Each arrow is (x0, y0, x1, y1) in [0, 1] image coordinates and means
    "content at (x0, y0) travels to (x1, y1) over the video". Its effect
    fades out with a Gaussian of `radius` (fraction of the shorter side).
    """
    v = torch.zeros(2, height, width)
    if not arrows or total_frames <= 1:
        return v
    steps = total_frames - 1
    ys, xs = torch.meshgrid(
        torch.arange(height, dtype=torch.float32),
        torch.arange(width, dtype=torch.float32),
        indexing="ij",
    )
    sigma = max(radius * min(height, width), 1.0)
    weighted = torch.zeros(2, height, width)
    total_weight = torch.zeros(height, width)
    for x0, y0, x1, y1 in arrows:
        cx, cy = x0 * (width - 1), y0 * (height - 1)
        weight = torch.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / (2 * sigma**2))
        weighted[0] += weight * (x1 - x0) * (width - 1) / steps
        weighted[1] += weight * (y1 - y0) * (height - 1) / steps
        total_weight += weight
    # Full arrow motion near its start, fading to still far away; overlapping
    # arrows average instead of adding up.
    return weighted / total_weight.clamp(min=1.0)


def warped_noise(velocity, total_frames, channels, generator, strength):
    """
    (1, C, T, H, W) noise where frame t is frame 0 moved by t * velocity,
    mixed with fresh noise by `strength`.
    """
    # Backward warp: the value now at x came from x - t * v(x).
    displacements = (-t * velocity for t in range(total_frames))
    return displaced_noise(
        displacements, velocity.shape[1:], channels, generator, strength
    )


def displaced_noise(displacements, size, channels, generator, strength):
    """
    (1, C, T, H, W) noise where frame t takes frame 0's value from
    x + displacements[t](x), mixed with fresh noise by `strength`.
    Sources outside the frame get fresh noise.
    """
    height, width = size
    shape = (channels, height, width)
    base = torch.randn(shape, generator=generator, device=generator.device)
    ys, xs = torch.meshgrid(
        torch.arange(height, dtype=torch.float32),
        torch.arange(width, dtype=torch.float32),
        indexing="ij",
    )
    keep, fresh = math.sqrt(strength), math.sqrt(1.0 - strength)
    frames = []
    for disp in displacements:
        src_x = torch.round(xs + disp[0]).long()
        src_y = torch.round(ys + disp[1]).long()
        inside = (src_x >= 0) & (src_x < width) & (src_y >= 0) & (src_y < height)
        moved = base[:, src_y.clamp(0, height - 1), src_x.clamp(0, width - 1)]
        eps = torch.randn(shape, generator=generator, device=generator.device)
        # Content moving in from outside the frame gets fresh noise.
        frames.append(torch.where(inside, keep * moved + fresh * eps, eps))
    return torch.stack(frames, dim=1)[None]


def section_slice(
    noise,
    generation_index,
    total_sections,
    latent_window_size,
    has_input_image,
    reverse_order,
):
    """
    The noise for one section, aligned with the output timeline. Original
    models generate sections from the end backwards (reverse_order=True).
    """
    time_index = (
        total_sections - 1 - generation_index if reverse_order else generation_index
    )
    start = int(has_input_image) + time_index * latent_window_size
    return noise[:, :, start : start + latent_window_size]
