from typing import Optional
from pathlib import Path

import torch

from modules.MMAudio.mmaudio.eval_utils import (
    ModelConfig,
    all_model_cfg,
    generate as mmaudio_generate,
    load_video,
    make_video,
)
from mmaudio.model.flow_matching import FlowMatching
from mmaudio.model.networks import MMAudio, get_my_mmaudio
from mmaudio.model.sequence_config import SequenceConfig
from mmaudio.model.utils.features_utils import FeaturesUtils

DEFAULT_AUDIO_NEGATIVE_PROMPT: list[str] = [
    'music',
    'noise',
]

# MMAudio Settings
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
device = 'cuda'
dtype = torch.bfloat16

# Initialize MMAudio Model
def get_mmaudio_model(audio_model_config: Optional[ModelConfig] = None) -> tuple[MMAudio, FeaturesUtils, SequenceConfig]:
    if audio_model_config is None:
        audio_model_config = all_model_cfg['large_44k_v2']

    audio_model_config.download_if_needed()

    seq_cfg = audio_model_config.seq_cfg

    net: MMAudio = get_my_mmaudio(audio_model_config.model_name).to(device, dtype).eval()
    net.load_weights(torch.load(audio_model_config.model_path, map_location=device, weights_only=True))

    feature_utils = FeaturesUtils(tod_vae_ckpt=audio_model_config.vae_path,
                                  synchformer_ckpt=audio_model_config.synchformer_ckpt,
                                  enable_conditions=True,
                                  mode=audio_model_config.mode,
                                  bigvgan_vocoder_ckpt=audio_model_config.bigvgan_16k_path,
                                  need_vae_encoder=False)
    feature_utils = feature_utils.to(device, dtype).eval()

    return net, feature_utils, seq_cfg


# Audio generation function
@torch.inference_mode()
def add_audio_to_video(
        video_path: Path,
        prompt: str,
        audio_negative_prompt: str,
        audio_steps: int,
        audio_cfg_strength: int,
        duration: int,
        audio_net: MMAudio,
        audio_feature_utils: FeaturesUtils,
        audio_seq_cfg: SequenceConfig,
        overwrite_orig_file: bool
) -> Path:
    """Generate and add audio to video using MMAudio"""

    try:
        rng = torch.Generator(device=device)
        rng.seed()  # Random seed for audio
        fm = FlowMatching(min_sigma=0, inference_mode='euler', num_steps=audio_steps)

        video_info = load_video(video_path, duration)
        clip_frames = video_info.clip_frames
        sync_frames = video_info.sync_frames
        duration = video_info.duration_sec
        clip_frames = clip_frames.unsqueeze(0)
        sync_frames = sync_frames.unsqueeze(0)
        audio_seq_cfg.duration = duration
        audio_net.update_seq_lengths(audio_seq_cfg.latent_seq_len, audio_seq_cfg.clip_seq_len,
                                     audio_seq_cfg.sync_seq_len)

        audios = mmaudio_generate(clip_frames, sync_frames,
                                  text=[prompt],
                                  negative_text=[audio_negative_prompt],
                                  feature_utils=audio_feature_utils,
                                  net=audio_net,
                                  fm=fm,
                                  rng=rng,
                                  cfg_strength=audio_cfg_strength)
        audio = audios.float().cpu()[0]

        video_filename = video_path.name

        if overwrite_orig_file:
            # Create video with audio, in the same location as the original file
            video_with_audio_filename = video_filename
        else:
            # Create video with audio, in the same folder with the original video
            video_with_audio_filename = video_filename + "_audio.mp4"

        video_dir = video_path.parent
        video_with_audio_path = Path(video_dir) / video_with_audio_filename

        # video_with_audio_str = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
        # video_with_audio_path = Path(video_with_audio_str)

        # add a 'h264' video encoded stream and a 'aac' encoded audio stream, to the file 'video_with_audio_path'
        make_video(video_info, video_with_audio_path, audio, sampling_rate=audio_seq_cfg.sampling_rate)

        return video_with_audio_path
    except Exception as e:
        print(f"Error in audio generation: {e}")
        return video_path
