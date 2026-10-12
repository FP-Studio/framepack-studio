import logging
import os
import subprocess

import av
import imageio_ffmpeg
import torch

from diffusers_helper.utils import save_bcthw_as_mp4

logger = logging.getLogger(__name__)


@torch.no_grad()
def combine_videos_sequentially_from_tensors(
    processed_input_frames_np,
    generated_frames_pt,
    output_path,
    target_fps,
    crf_value,
    source_video_path=None,
):
    """
    Combines processed input frames (NumPy) with generated frames (PyTorch Tensor) sequentially
    and saves the result as an MP4 video using save_bcthw_as_mp4.

    Args:
        processed_input_frames_np: NumPy array of processed input frames (T_in, H, W_in, C), uint8.
        generated_frames_pt: PyTorch tensor of generated frames (B_gen, C_gen, T_gen, H, W_gen), float32 [-1,1].
                             (This will be history_pixels from worker.py)
        output_path: Path to save the combined video.
        target_fps: FPS for the output combined video.
        crf_value: CRF value for video encoding.
        source_video_path: Optional source video whose audio track is copied into the output.

    Returns:
        Path to the combined video, or None if an error occurs.
    """
    try:
        # 1. Convert processed_input_frames_np to PyTorch tensor BCTHW, float32, [-1,1]
        # processed_input_frames_np shape: (T_in, H, W_in, C)
        input_frames_pt = (
            torch.from_numpy(processed_input_frames_np).float() / 127.5 - 1.0
        )  # (T,H,W,C)
        input_frames_pt = input_frames_pt.permute(3, 0, 1, 2)  # (C,T,H,W)
        input_frames_pt = input_frames_pt.unsqueeze(0)  # (1,C,T,H,W) -> BCTHW

        # Ensure generated_frames_pt is on the same device and dtype for concatenation
        input_frames_pt = input_frames_pt.to(
            device=generated_frames_pt.device, dtype=generated_frames_pt.dtype
        )

        # 2. Dimension Check (Heights and Widths should match)
        #    They should match, since the input frames should have been processed to match the generation resolution.
        #    But sanity check to ensure no mismatch occurs when the code is refactored.
        if input_frames_pt.shape[3:] != generated_frames_pt.shape[3:]:  # Compare (H,W)
            logger.warning(
                f"Dimension mismatch for sequential combination! Input: {input_frames_pt.shape[3:]}, Generated: {generated_frames_pt.shape[3:]}."
            )
            logger.warning(
                "Attempting to proceed, but this might lead to errors or unexpected video output."
            )
            # Potentially add resizing logic here if necessary, but for now, assume they match

        # 3. Concatenate Tensors along the time dimension (dim=2 for BCTHW)
        combined_video_pt = torch.cat([input_frames_pt, generated_frames_pt], dim=2)

        # 4. Save
        save_bcthw_as_mp4(combined_video_pt, output_path, fps=target_fps, crf=crf_value)
        if source_video_path:
            add_audio_from_source(output_path, source_video_path)
        logger.debug(
            f"Sequentially combined video (from tensors) saved to {output_path}"
        )
        return output_path
    except Exception as e:
        logger.exception(f"Error in combine_videos_sequentially_from_tensors: {str(e)}")
        return None


def add_audio_from_source(video_path, source_video_path):
    """
    Copies the audio track of source_video_path into video_path, in place.
    The audio starts at the beginning of the video, so it lines up with the source frames.
    Does nothing if the source has no audio.
    """
    try:
        with av.open(source_video_path) as container:
            if not container.streams.audio:
                return
        tmp_path = video_path + ".audio.mp4"
        cmd = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-i",
            video_path,
            "-i",
            source_video_path,
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            tmp_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        os.replace(tmp_path, video_path)
        logger.debug(f"Added audio from {source_video_path} to {video_path}")
    except Exception as e:
        logger.exception(f"Error adding audio from source video: {str(e)}")
