import torch
import math

from diffusers_helper.k_diffusion.uni_pc_fm import sample_unipc
from diffusers_helper.k_diffusion.wrapper import fm_wrapper
from diffusers_helper.utils import repeat_to_batch_size


def flux_time_shift(t, mu=1.15, sigma=1.0):
    return math.exp(mu) / (math.exp(mu) + (1 / t - 1) ** sigma)


def calculate_flux_mu(context_length, x1=256, y1=0.5, x2=4096, y2=1.15, exp_max=7.0):
    k = (y2 - y1) / (x2 - x1)
    b = y1 - k * x1
    mu = k * context_length + b
    mu = min(mu, math.log(exp_max))
    return mu


def get_flux_sigmas_from_mu(n, mu):
    sigmas = torch.linspace(1, 0, steps=n + 1)
    sigmas = flux_time_shift(sigmas, mu=mu)
    return sigmas


@torch.inference_mode()
def sample_hunyuan(
    transformer,
    sampler="unipc",
    initial_latent=None,
    concat_latent=None,
    strength=1.0,
    width=512,
    height=512,
    frames=16,
    real_guidance_scale=1.0,
    distilled_guidance_scale=6.0,
    guidance_rescale=0.0,
    shift=None,
    num_inference_steps=25,
    batch_size=None,
    generator=None,
    prompt_embeds=None,
    prompt_embeds_mask=None,
    prompt_poolers=None,
    negative_prompt_embeds=None,
    negative_prompt_embeds_mask=None,
    negative_prompt_poolers=None,
    dtype=torch.bfloat16,
    device=None,
    negative_kwargs=None,
    callback=None,
    noise=None,
    **kwargs,
):
    device = device or transformer.device

    if batch_size is None:
        batch_size = int(prompt_embeds.shape[0])

    shape = (batch_size, 16, (frames + 3) // 4, height // 8, width // 8)
    if noise is None:
        latents = torch.randn(shape, generator=generator, device=generator.device)
    else:
        # Caller-supplied starting noise, e.g. warped along a motion field
        assert tuple(noise.shape) == shape, f"noise shape {noise.shape} != {shape}"
        latents = noise
    latents = latents.to(device=device, dtype=torch.float32)

    B, C, T, H, W = latents.shape
    seq_length = T * H * W // 4

    if shift is None:
        mu = calculate_flux_mu(seq_length, exp_max=7.0)
    else:
        mu = math.log(shift)

    sigmas = get_flux_sigmas_from_mu(num_inference_steps, mu).to(device)

    k_model = fm_wrapper(transformer)

    first_step = 0
    if initial_latent is not None:
        # img2img: skip the first (1 - strength) of the steps, like diffusers
        keep = max(1, min(num_inference_steps, round(num_inference_steps * strength)))
        first_step = num_inference_steps - keep
        sigmas = sigmas[first_step:]
        first_sigma = sigmas[0].to(device=device, dtype=torch.float32)
        initial_latent = initial_latent.to(device=device, dtype=torch.float32)
        latents = (
            initial_latent.float() * (1.0 - first_sigma) + latents.float() * first_sigma
        )

    if concat_latent is not None:
        concat_latent = concat_latent.to(latents)

    distilled_guidance = torch.tensor(
        [distilled_guidance_scale * 1000.0] * batch_size
    ).to(device=device, dtype=dtype)

    prompt_embeds = repeat_to_batch_size(prompt_embeds, batch_size)
    prompt_embeds_mask = repeat_to_batch_size(prompt_embeds_mask, batch_size)
    prompt_poolers = repeat_to_batch_size(prompt_poolers, batch_size)
    negative_prompt_embeds = repeat_to_batch_size(negative_prompt_embeds, batch_size)
    negative_prompt_embeds_mask = repeat_to_batch_size(
        negative_prompt_embeds_mask, batch_size
    )
    negative_prompt_poolers = repeat_to_batch_size(negative_prompt_poolers, batch_size)
    concat_latent = repeat_to_batch_size(concat_latent, batch_size)

    sampler_kwargs = dict(
        dtype=dtype,
        cfg_scale=real_guidance_scale,
        cfg_rescale=guidance_rescale,
        concat_latent=concat_latent,
        positive=dict(
            pooled_projections=prompt_poolers,
            encoder_hidden_states=prompt_embeds,
            encoder_attention_mask=prompt_embeds_mask,
            guidance=distilled_guidance,
            **kwargs,
        ),
        negative=dict(
            pooled_projections=negative_prompt_poolers,
            encoder_hidden_states=negative_prompt_embeds,
            encoder_attention_mask=negative_prompt_embeds_mask,
            guidance=distilled_guidance,
            **(kwargs if negative_kwargs is None else {**kwargs, **negative_kwargs}),
        ),
    )

    if hasattr(transformer, "begin_sampling"):
        # Step caches must know where in the schedule this section starts
        transformer.begin_sampling(first_step, len(sigmas) - 1)

    if sampler == "unipc":
        results = sample_unipc(
            k_model,
            latents,
            sigmas,
            extra_args=sampler_kwargs,
            disable=False,
            callback=callback,
        )
    else:
        raise NotImplementedError(f"Sampler {sampler} is not supported.")

    return results
