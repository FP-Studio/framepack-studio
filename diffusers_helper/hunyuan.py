import torch

from diffusers.pipelines.hunyuan_video.pipeline_hunyuan_video import DEFAULT_PROMPT_TEMPLATE
from diffusers_helper.utils import crop_or_pad_yield_mask


@torch.no_grad()
def encode_prompt_conds(prompt, text_encoder, text_encoder_2, tokenizer, tokenizer_2, max_length=256):
    assert isinstance(prompt, str)

    prompt = [prompt]

    # LLAMA
    
    # Check if there's a custom system prompt template in settings
    custom_template = None
    try:
        from modules.settings import Settings
        settings = Settings()
        override_system_prompt = settings.get("override_system_prompt", False)
        custom_template_str = settings.get("system_prompt_template")
        
        if override_system_prompt and custom_template_str:
            try:
                # Convert the string representation to a dictionary
                # Extract template and crop_start directly from the string using regex
                import re
                
                # Try to extract the template value
                template_match = re.search(r"['\"]template['\"]\s*:\s*['\"](.+?)['\"](?=\s*,|\s*})", custom_template_str, re.DOTALL)
                crop_start_match = re.search(r"['\"]crop_start['\"]\s*:\s*(\d+)", custom_template_str)
                
                if template_match and crop_start_match:
                    template_value = template_match.group(1)
                    crop_start_value = int(crop_start_match.group(1))
                    
                    # Unescape any escaped characters in the template
                    template_value = template_value.replace("\\n", "\n").replace("\\\"", "\"").replace("\\'", "'")
                    
                    custom_template = {
                        "template": template_value,
                        "crop_start": crop_start_value
                    }
                    print(f"Using custom system prompt template from settings: {custom_template}")
                else:
                    print(f"Could not extract template or crop_start from system prompt template string")
                    print(f"Falling back to default template")
                    custom_template = None
            except Exception as e:
                print(f"Error parsing custom system prompt template: {e}")
                print(f"Falling back to default template")
                custom_template = None
        else:
            if not override_system_prompt:
                print(f"Override system prompt is disabled, using default template")
            elif not custom_template_str:
                print(f"No custom system prompt template found in settings")
            custom_template = None
    except Exception as e:
        print(f"Error loading settings: {e}")
        print(f"Falling back to default template")
        custom_template = None
    
    # Use custom template if available, otherwise use default
    template = custom_template if custom_template else DEFAULT_PROMPT_TEMPLATE
    
    prompt_llama = [template["template"].format(p) for p in prompt]
    crop_start = template["crop_start"]

    llama_inputs = tokenizer(
        prompt_llama,
        padding="max_length",
        max_length=max_length + crop_start,
        truncation=True,
        return_tensors="pt",
        return_length=False,
        return_overflowing_tokens=False,
        return_attention_mask=True,
    )

    llama_input_ids = llama_inputs.input_ids.to(text_encoder.device)
    llama_attention_mask = llama_inputs.attention_mask.to(text_encoder.device)
    llama_attention_length = int(llama_attention_mask.sum())

    llama_outputs = text_encoder(
        input_ids=llama_input_ids,
        attention_mask=llama_attention_mask,
        output_hidden_states=True,
    )

    llama_vec = llama_outputs.hidden_states[-3][:, crop_start:llama_attention_length]
    # llama_vec_remaining = llama_outputs.hidden_states[-3][:, llama_attention_length:]
    llama_attention_mask = llama_attention_mask[:, crop_start:llama_attention_length]

    assert torch.all(llama_attention_mask.bool())

    # CLIP

    clip_l_input_ids = tokenizer_2(
        prompt,
        padding="max_length",
        max_length=77,
        truncation=True,
        return_overflowing_tokens=False,
        return_length=False,
        return_tensors="pt",
    ).input_ids
    clip_l_pooler = text_encoder_2(clip_l_input_ids.to(text_encoder_2.device), output_hidden_states=False).pooler_output

    return llama_vec, clip_l_pooler


@torch.no_grad()
def vae_decode_fake(latents):
    latent_rgb_factors = [
        [-0.0395, -0.0331, 0.0445],
        [0.0696, 0.0795, 0.0518],
        [0.0135, -0.0945, -0.0282],
        [0.0108, -0.0250, -0.0765],
        [-0.0209, 0.0032, 0.0224],
        [-0.0804, -0.0254, -0.0639],
        [-0.0991, 0.0271, -0.0669],
        [-0.0646, -0.0422, -0.0400],
        [-0.0696, -0.0595, -0.0894],
        [-0.0799, -0.0208, -0.0375],
        [0.1166, 0.1627, 0.0962],
        [0.1165, 0.0432, 0.0407],
        [-0.2315, -0.1920, -0.1355],
        [-0.0270, 0.0401, -0.0821],
        [-0.0616, -0.0997, -0.0727],
        [0.0249, -0.0469, -0.1703]
    ]  # From comfyui

    latent_rgb_factors_bias = [0.0259, -0.0192, -0.0761]

    weight = torch.tensor(latent_rgb_factors, device=latents.device, dtype=latents.dtype).transpose(0, 1)[:, :, None, None, None]
    bias = torch.tensor(latent_rgb_factors_bias, device=latents.device, dtype=latents.dtype)

    images = torch.nn.functional.conv3d(latents, weight, bias=bias, stride=1, padding=0, dilation=1, groups=1)
    images = images.clamp(0.0, 1.0)

    return images


@torch.no_grad()
def vae_decode(latents, vae, image_mode=False):
    latents = latents / vae.config.scaling_factor

    if not image_mode:
        image = vae.decode(latents.to(device=vae.device, dtype=vae.dtype)).sample
    else:
        latents = latents.to(device=vae.device, dtype=vae.dtype).unbind(2)
        image = [vae.decode(l.unsqueeze(2)).sample for l in latents]
        image = torch.cat(image, dim=2)

    return image

@torch.no_grad()
def vae_decode_with_tiling(latents, vae, low_vram_tiling_enabled=False):
    """
    Decode latents using VAE's built-in tiling support for low VRAM.
    Important: HunyuanVideo has temporal_compression_ratio=4, so:
    - Pixel space stride gets divided by 4 to get latent space stride
    - Minimum temporal stride in pixel space must be >= 4 to avoid 0 in latent space
    """
    if low_vram_tiling_enabled:
        # Tiling configuration for 8GB VRAM
        tile_height = 128
        tile_width = 128
        tile_frames = 5  # Minimum practical size (2 latents -> 5 frames)

        # CRITICAL: stride_frames must be >= temporal_compression_ratio (4)
        # Otherwise: latent_stride = pixel_stride / 4 = 0 (causes "range() arg 3 must not be zero")
        stride_height = 64     # 50% overlap for spatial dimensions
        stride_width = 64      # 50% overlap for spatial dimensions
        stride_frames = 4      # Minimum to avoid 0 in latent space (4/4 = 1 latent frame)

        vae.enable_tiling(
            tile_sample_min_height=tile_height,
            tile_sample_min_width=tile_width,
            tile_sample_min_num_frames=tile_frames,
            tile_sample_stride_height=stride_height,
            tile_sample_stride_width=stride_width,
            tile_sample_stride_num_frames=stride_frames  # Must be >= 4!
        )
        print(f"[VAE] Tiling enabled: tiles={tile_height}x{tile_width}x{tile_frames}f, strides={stride_height}x{stride_width}x{stride_frames}f")
        print(f"[VAE] Latent space stride: {stride_frames//4} latent frames")

    latents = latents / vae.config.scaling_factor
    latents = latents.to(device=vae.device, dtype=vae.dtype)

    try:
        with torch.amp.autocast('cuda', enabled=True, dtype=torch.bfloat16):
            decoded = vae.decode(latents).sample

        print(f"[VAE Decode] Output shape: {decoded.shape}")
        return decoded

    except Exception as e:
        print(f"[VAE Decode Error] {e}")
        raise
    finally:
        if low_vram_tiling_enabled:
            vae.disable_tiling()

@torch.no_grad()
def vae_encode(image, vae):
    latents = vae.encode(image.to(device=vae.device, dtype=vae.dtype)).latent_dist.sample()
    latents = latents * vae.config.scaling_factor
    return latents
