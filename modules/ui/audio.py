import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

import gradio as gr

logger = logging.getLogger(__name__)


def _ensure_mmaudio_on_path():
    """
    Ensure that the 'mmaudio' package (from modules/MMAudio) is importable as a top-level package.
    MMAudio uses absolute imports like 'from mmaudio.*', so we need modules/MMAudio on sys.path.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    mmaudio_root = os.path.abspath(os.path.join(here, "..", "MMAudio"))
    if mmaudio_root not in sys.path:
        sys.path.insert(0, mmaudio_root)


def create_audio_ui(settings):
    """
    Build the Audio tab UI.

    Inputs:
      - Video file
      - Prompt (and optional negative prompt)
      - Model variant
      - Duration, CFG strength, steps
      - Options: mask_away_clip, skip video composite, full precision
      - Seed

    Outputs:
      - Generated audio (FLAC)
      - Optional composited video with the generated audio
      - Status log/markdown
      - Previous generations list and preview
    """
    with gr.Row():
        with gr.Column(scale=2):
            input_video = gr.Video(
                sources="upload",
                label="Input Video",
                height=420,
                show_label=True,
            )
            with gr.Row():
                prompt = gr.Textbox(
                    label="Prompt",
                    value="",
                    placeholder="Describe the soundtrack you want...",
                    scale=3,
                )
            negative_prompt = gr.Textbox(
                label="Negative Prompt",
                value="",
                placeholder="Optional: what to avoid in the audio",
            )

            with gr.Row():
                variant = gr.Dropdown(
                    label="Model Variant",
                    choices=[
                        "small_16k",
                        "small_44k",
                        "medium_44k",
                        "large_44k",
                        "large_44k_v2",
                    ],
                    value="large_44k_v2",
                    info="Choose the pre-trained MMAudio model variant",
                )
                duration = gr.Slider(
                    label="Max Duration (sec)",
                    minimum=1.0,
                    maximum=60.0,
                    step=0.5,
                    value=8.0,
                    info="Will be truncated if the video is shorter after preprocessing",
                )

            with gr.Row():
                cfg_strength = gr.Slider(
                    label="CFG Strength",
                    minimum=0.0,
                    maximum=10.0,
                    step=0.1,
                    value=4.5,
                )
                num_steps = gr.Slider(
                    label="Inference Steps",
                    minimum=5,
                    maximum=100,
                    step=1,
                    value=25,
                )

            with gr.Row():
                seed = gr.Number(label="Seed", value=42, precision=0)
                mask_away_clip = gr.Checkbox(
                    label="Mask Away CLIP (ignore CLIP frames)",
                    value=False,
                    info="Disable CLIP conditioning from the video",
                )

            with gr.Row():
                skip_video_composite = gr.Checkbox(
                    label="Skip Video Composite",
                    value=False,
                    info="If checked, only audio will be saved/returned",
                )
                full_precision = gr.Checkbox(
                    label="Full Precision (float32)",
                    value=False,
                    info="Uses more VRAM/CPU RAM; otherwise uses bfloat16",
                )

            generate_btn = gr.Button("🎵 Generate Audio", variant="primary")

        with gr.Column(scale=1):
            audio_output = gr.Audio(
                label="Generated Audio (FLAC)",
                interactive=False,
                type="filepath",
            )
            video_output = gr.Video(
                label="Latest Result (with generated audio)",
                visible=True,
                autoplay=False,
                show_share_button=False,
                height=300,
            )
            status = gr.Markdown("", elem_classes="no-generating-animation")

            with gr.Accordion("Previous Generations", open=True):
                prev_versions_dropdown = gr.Dropdown(
                    label="Select a previous version (for this input video)",
                    choices=[],
                    value=None,
                    interactive=True,
                )
                with gr.Row():
                    refresh_prev_btn = gr.Button("🔄 Refresh List", variant="secondary")
                preview_selected_video = gr.Video(
                    label="Preview Selected Version",
                    autoplay=False,
                    show_share_button=False,
                    height=300,
                )

    return {
        "input_video": input_video,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "variant": variant,
        "duration": duration,
        "cfg_strength": cfg_strength,
        "num_steps": num_steps,
        "seed": seed,
        "mask_away_clip": mask_away_clip,
        "skip_video_composite": skip_video_composite,
        "full_precision": full_precision,
        "generate_btn": generate_btn,
        "audio_output": audio_output,
        "video_output": video_output,
        "status": status,
        "prev_versions_dropdown": prev_versions_dropdown,
        "refresh_prev_btn": refresh_prev_btn,
        "preview_selected_video": preview_selected_video,
    }


def connect_audio_events(a, settings):
    """
    Wire up events for the Audio tab using MMAudio's demo flow.
    """

    def _validate_inputs(video_path: Optional[str], prompt_text: str):
        if not video_path or not os.path.exists(video_path):
            return False, "Please provide a valid input video."
        if prompt_text is None:
            prompt_text = ""
        return True, ""

    def _audio_output_dir() -> Path:
        base_output_dir = settings.get("output_dir", "./outputs")
        p = Path(base_output_dir) / "audio"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _scan_previous_versions_for_video(
        video_path: Optional[str],
    ) -> Tuple[dict, dict]:
        """
        Returns:
          - update for prev_versions_dropdown (choices and selected value)
          - update for preview_selected_video (value)
        """
        if not video_path:
            return gr.update(choices=[], value=None), gr.update(value=None)

        stem = Path(video_path).stem
        out_dir = _audio_output_dir()
        # Find mp4 files matching stem_*.mp4
        mp4s: List[Path] = sorted(
            out_dir.glob(f"{stem}_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not mp4s:
            # no previous mp4s
            return gr.update(choices=[], value=None), gr.update(value=None)
        # Use full paths as values; display will show them
        choices = [str(p) for p in mp4s]
        selected = choices[0]
        return gr.update(choices=choices, value=selected), gr.update(value=selected)

    def _refresh_prev_versions(video_path: Optional[str]):
        dd_upd, prev_upd = _scan_previous_versions_for_video(video_path)
        return dd_upd, prev_upd

    def run_mmaudio(
        video_path: Optional[str],
        prompt_text: str,
        negative_text: str,
        variant_name: str,
        duration_sec: float,
        cfg_strength_val: float,
        steps_val: int,
        seed_val: int,
        mask_away_clip_val: bool,
        skip_video_composite_val: bool,
        full_precision_val: bool,
    ):
        ok, msg = _validate_inputs(video_path, prompt_text)
        if not ok:
            # 5 outputs: audio_output, video_output, status, prev_dropdown, prev_preview
            return (
                gr.update(),
                gr.update(),
                gr.update(value=f"❌ {msg}"),
                gr.update(),
                gr.update(),
            )

        # Status: starting
        yield (
            gr.update(),
            gr.update(),
            gr.update(value="⏳ Loading MMAudio..."),
            gr.update(),
            gr.update(),
        )

        net = None
        feature_utils = None
        video_info = None
        try:
            _ensure_mmaudio_on_path()

            import torch
            import torchaudio

            from mmaudio.eval_utils import (
                ModelConfig,
                all_model_cfg,
                generate,
                load_video,
                make_video,
                setup_eval_logging,
            )
            from mmaudio.model.flow_matching import FlowMatching
            from mmaudio.model.networks import get_my_mmaudio
            from mmaudio.model.utils.features_utils import FeaturesUtils

            audio_output_dir = _audio_output_dir()

            # Logging for eval
            setup_eval_logging()

            if variant_name not in all_model_cfg:
                yield (
                    gr.update(),
                    gr.update(),
                    gr.update(value=f"❌ Unknown model variant: {variant_name}"),
                    gr.update(),
                    gr.update(),
                )
                return

            model: ModelConfig = all_model_cfg[variant_name]
            # Download weights if needed (will use relative paths at repo root)
            model.download_if_needed()

            # Device / dtype
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
            dtype = torch.float32 if full_precision_val else torch.bfloat16

            # Load network and weights
            net = get_my_mmaudio(model.model_name).to(device, dtype).eval()
            # weights_only=True is used in the demo; keep parity
            net.load_weights(
                torch.load(model.model_path, map_location=device, weights_only=True)
            )

            # Seed / sampler
            rng = torch.Generator(device=device)
            rng.manual_seed(int(seed_val))
            fm = FlowMatching(
                min_sigma=0, inference_mode="euler", num_steps=int(steps_val)
            )

            # Feature utils
            feature_utils = FeaturesUtils(
                tod_vae_ckpt=model.vae_path,
                synchformer_ckpt=model.synchformer_ckpt,
                enable_conditions=True,
                mode=model.mode,
                bigvgan_vocoder_ckpt=model.bigvgan_16k_path,
                need_vae_encoder=False,
            )
            feature_utils = feature_utils.to(device, dtype).eval()

            # Status: loading video
            yield (
                gr.update(),
                gr.update(),
                gr.update(value="📼 Loading and preprocessing video..."),
                gr.update(),
                gr.update(),
            )

            video_path_obj = Path(video_path)
            video_info = load_video(video_path_obj, float(duration_sec))
            clip_frames = video_info.clip_frames
            sync_frames = video_info.sync_frames
            # Adjust duration if loader truncated
            duration_sec = video_info.duration_sec

            if mask_away_clip_val:
                clip_frames = None
            else:
                clip_frames = clip_frames.unsqueeze(0)
            sync_frames = sync_frames.unsqueeze(0)

            # Update model seq lengths
            seq_cfg = model.seq_cfg
            seq_cfg.duration = float(duration_sec)
            net.update_seq_lengths(
                seq_cfg.latent_seq_len, seq_cfg.clip_seq_len, seq_cfg.sync_seq_len
            )

            # Status: generating
            yield (
                gr.update(),
                gr.update(),
                gr.update(value="🎧 Generating audio... This may take a while..."),
                gr.update(),
                gr.update(),
            )

            # Run generation
            audios = generate(
                clip_frames,
                sync_frames,
                [prompt_text],
                negative_text=[negative_text] if negative_text is not None else None,
                feature_utils=feature_utils,
                net=net,
                fm=fm,
                rng=rng,
                cfg_strength=float(cfg_strength_val),
            )
            audio = audios.float().cpu()[0]  # (channels, samples)
            sr = seq_cfg.sampling_rate

            # Save with unique name: include seed and timestamp
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = video_path_obj.stem
            audio_save_path = audio_output_dir / f"{stem}_{int(seed_val)}_{ts}.flac"
            torchaudio.save(audio_save_path, audio, sr)

            # Optionally composite video with audio
            video_save_path = None
            if not skip_video_composite_val:
                # Status: compositing
                yield (
                    gr.update(value=str(audio_save_path)),
                    gr.update(),
                    gr.update(value="🎬 Compositing video with generated audio..."),
                    gr.update(),
                    gr.update(),
                )
                video_save_path = audio_output_dir / f"{stem}_{int(seed_val)}_{ts}.mp4"
                make_video(video_info, video_save_path, audio, sampling_rate=sr)

            # Build previous versions list/preview updates
            dd_upd, prev_upd = _scan_previous_versions_for_video(str(video_path_obj))

            # Final status
            status_msg = f"✅ Done. Audio saved to {audio_save_path}"
            if video_save_path is not None:
                status_msg += f" | Video saved to {video_save_path}"

            yield (
                gr.update(value=str(audio_save_path)),
                gr.update(value=str(video_save_path))
                if video_save_path
                else gr.update(),
                gr.update(value=status_msg),
                dd_upd,
                prev_upd,
            )

        except Exception as e:
            logger.exception("Error during MMAudio generation")
            # Also attempt to refresh list even on error
            dd_upd, prev_upd = _scan_previous_versions_for_video(video_path)
            yield (
                gr.update(),
                gr.update(),
                gr.update(value=f"❌ Error: {e}"),
                dd_upd,
                prev_upd,
            )
        finally:
            # Proactively unload models to free VRAM/CPU RAM
            try:
                import gc
                import torch  # type: ignore

                # Remove refs
                del net
                del feature_utils
                del video_info
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as _e:
                logger.debug(
                    f"Cleanup after MMAudio generation encountered a non-fatal issue: {_e}"
                )

    # Click binding with streaming status updates (now returns 5 outputs)
    a["generate_btn"].click(
        fn=run_mmaudio,
        inputs=[
            a["input_video"],
            a["prompt"],
            a["negative_prompt"],
            a["variant"],
            a["duration"],
            a["cfg_strength"],
            a["num_steps"],
            a["seed"],
            a["mask_away_clip"],
            a["skip_video_composite"],
            a["full_precision"],
        ],
        outputs=[
            a["audio_output"],
            a["video_output"],
            a["status"],
            a["prev_versions_dropdown"],
            a["preview_selected_video"],
        ],
        show_progress="minimal",
    )

    # Populate previous versions when input video changes
    a["input_video"].change(
        fn=_refresh_prev_versions,
        inputs=[a["input_video"]],
        outputs=[a["prev_versions_dropdown"], a["preview_selected_video"]],
        show_progress="hidden",
    )

    # Manual refresh button
    a["refresh_prev_btn"].click(
        fn=_refresh_prev_versions,
        inputs=[a["input_video"]],
        outputs=[a["prev_versions_dropdown"], a["preview_selected_video"]],
    )

    # When selecting a previous version, update the preview player
    def _on_prev_select(selected_path: Optional[str]):
        return gr.update(value=selected_path if selected_path else None)

    a["prev_versions_dropdown"].change(
        fn=_on_prev_select,
        inputs=[a["prev_versions_dropdown"]],
        outputs=[a["preview_selected_video"]],
        show_progress="hidden",
    )
