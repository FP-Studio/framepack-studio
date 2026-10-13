"""
MMAudio generation for a Library video.

Moved from the old Outputs tab; the inputs are plain values (a video path and
its metadata) instead of a gallery prefix.
"""

import logging

from modules.MMAudio.app import (
    DEFAULT_AUDIO_CFG,
    DEFAULT_AUDIO_NEGATIVE_PROMPT,  # noqa: F401  (used by the Library UI)
    DEFAULT_AUDIO_STEPS,
    add_audio_to_video,
    all_model_cfg,
    get_mmaudio_model,
    load_video,
    reencode_without_audio,
)

logger = logging.getLogger(__name__)

AUDIO_MODELS = list(all_model_cfg.keys())
DEFAULT_AUDIO_MODEL = "large_44k_v2"


def _clip_audio(video_path):
    from moviepy import VideoFileClip

    clip = VideoFileClip(str(video_path))
    return clip.audio, clip.duration


def has_audio(video_path):
    try:
        audio, _ = _clip_audio(video_path)
        return audio is not None
    except Exception as e:
        logger.error(f"Error checking audio: {e}")
        return False


def generate_audio(
    video_path,
    metadata,
    model_name,
    overwrite,
    prompt_text,
    negative_text,
    append_prompt,
    steps=DEFAULT_AUDIO_STEPS,
    cfg_strength=DEFAULT_AUDIO_CFG,
):
    """Add generated audio to the video in place. Returns a status message."""
    audio, duration = _clip_audio(video_path)
    if audio is not None and not overwrite:
        return "This video already has audio. Tick “Replace existing audio” to regenerate it."

    # The video prompt describes what the scene looks like, which is still
    # a reasonable description of what it should sound like.
    prompt = metadata.get("prompt", "")
    if prompt_text:
        prompt = f"{prompt}, {prompt_text}" if append_prompt and prompt else prompt_text

    # Don't reuse the video's negative prompt: it lists visual defects
    # ("blurry", "low quality"), not sounds.
    negative_prompt = negative_text or ""

    # Steps and CFG are the audio model's own; the video's "cfg" is usually 1,
    # which turns MMAudio's guidance off.
    steps = int(steps)
    cfg_strength = float(cfg_strength)
    model_config = all_model_cfg.get(model_name) if model_name else None

    logger.info(
        f"GENAudio: prompt:{prompt}\n negative prompt:{negative_prompt}\n"
        f" steps:{steps}\n cfg:{cfg_strength}"
    )

    net, feature_utils, seq_cfg = get_mmaudio_model(model_config)
    result = add_audio_to_video(
        video_path=video_path,
        prompt=prompt,
        audio_negative_prompt=negative_prompt,
        audio_steps=steps,
        audio_cfg_strength=cfg_strength,
        duration=duration,
        audio_net=net,
        audio_feature_utils=feature_utils,
        audio_seq_cfg=seq_cfg,
        overwrite_orig_file=True,
    )
    if result is None:
        return "Audio generation failed — see the console for details."
    return "Audio added."


def delete_audio(video_path):
    audio, duration = _clip_audio(video_path)
    if audio is None:
        return "This video has no audio."
    reencode_without_audio(load_video(video_path, duration), video_path)
    logger.info(f"Deleted audio for video {video_path}")
    return "Audio removed."
