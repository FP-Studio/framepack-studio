from typing import List, Any
from pathlib import Path
import gradio as gr
import os
import json
import logging

from modules.MMAudio.app import (
    DEFAULT_AUDIO_CFG,
    DEFAULT_AUDIO_NEGATIVE_PROMPT,
    DEFAULT_AUDIO_STEPS,
    add_audio_to_video,
    all_model_cfg,
    get_mmaudio_model,
    load_video,
    reencode_without_audio,
)

logger = logging.getLogger(__name__)


def create_outputs_ui(settings):
    outputDirectory_video = settings.get(
        "output_dir", settings.default_settings["output_dir"]
    )
    outputDirectory_metadata = settings.get(
        "metadata_dir", settings.default_settings["metadata_dir"]
    )

    os.makedirs(outputDirectory_video, exist_ok=True)
    os.makedirs(outputDirectory_metadata, exist_ok=True)

    gallery_items_state = gr.State([])
    selected_original_video_path_state = gr.State(None)

    with gr.Row():
        with gr.Column(scale=2):
            thumbs = gr.Gallery(
                columns=[4], allow_preview=False, object_fit="cover", height="auto"
            )
            refresh_gallery_button = gr.Button("🔄 Update Gallery")
            delete_btn = gr.Button("🗑️ Delete Selected", visible=False)

            gen_audio_acc = gr.Accordion(label="Audio", open=False, visible=False)
            with gen_audio_acc:
                with gr.Accordion(label="Generate"):
                    audio_model_dropdown = gr.Dropdown(
                        label="Select mmaudio model",
                        choices=all_model_cfg.keys(),
                        multiselect=False,
                        value="large_44k_v2",
                        info="Select one mmaudio model to use, to generate audio",
                        # scale=1,
                    )
                    overwrite_audio_chkbox = gr.Checkbox(
                        label="Overwrite audio", visible=False
                    )

                    with gr.Blocks():
                        audio_prompt_chkbox = gr.Checkbox(label="Append")
                        audio_prompt_txt = gr.Textbox(label="Positive prompt")

                    audio_prompt_neg_txt = gr.Textbox(
                        label="Negative prompt", value=DEFAULT_AUDIO_NEGATIVE_PROMPT
                    )
                    audio_steps_slider = gr.Slider(
                        label="Steps",
                        minimum=1,
                        maximum=100,
                        step=1,
                        value=DEFAULT_AUDIO_STEPS,
                    )
                    audio_cfg_slider = gr.Slider(
                        label="CFG strength",
                        minimum=1.0,
                        maximum=10.0,
                        step=0.1,
                        value=DEFAULT_AUDIO_CFG,
                        info="How closely the audio follows the prompt",
                    )

                    gen_audio_btn = gr.Button("Generate audio")
                audio_delete_btn = gr.Button("🗑️ Delete")
        with gr.Column(scale=5):
            video_out = gr.Video(sources=[], autoplay=True, loop=True, visible=False)
        with gr.Column(scale=1):
            info_out = gr.Textbox(label="Generation info", visible=False)
            send_to_toolbox_btn = gr.Button("➡️ Send to Post-processing", visible=False)

    return {
        "gallery_items_state": gallery_items_state,
        "selected_original_video_path_state": selected_original_video_path_state,
        "thumbs": thumbs,
        "refresh_gallery_button": refresh_gallery_button,
        "video_out": video_out,
        "info_out": info_out,
        "send_to_toolbox_btn": send_to_toolbox_btn,
        "outputDirectory_video": outputDirectory_video,
        "outputDirectory_metadata": outputDirectory_metadata,
        "delete_btn": delete_btn,
        "selected_prefix_state": gr.State(None),
        "gen_audio_btn": gen_audio_btn,
        "overwrite_audio_chkbox": overwrite_audio_chkbox,
        "gen_audio_acc": gen_audio_acc,
        "audio_prompt_txt": audio_prompt_txt,
        "audio_prompt_neg_txt": audio_prompt_neg_txt,
        "audio_delete_btn": audio_delete_btn,
        "audio_model_dropdown": audio_model_dropdown,
        "audio_prompt_chkbox": audio_prompt_chkbox,
        "audio_steps_slider": audio_steps_slider,
        "audio_cfg_slider": audio_cfg_slider,
    }


def connect_outputs_events(
    o, tb_target_video_input: gr.Tab, main_tabs_component: gr.Tabs
):
    def get_gallery_items() -> List[tuple[str, str]]:
        if not os.path.exists(o["outputDirectory_metadata"]):
            logging.error(
                f"Error: Metadata directory not found at {o['outputDirectory_metadata']}"
            )
            return []

        files_with_mtime = []

        all_video_files = os.listdir(o["outputDirectory_video"])

        for f in os.listdir(o["outputDirectory_metadata"]):
            if f.endswith(".png"):
                prefix = os.path.splitext(f)[0]

                matching_videos = []
                for video_file in all_video_files:
                    if video_file.startswith(prefix) and video_file.endswith(".mp4"):
                        matching_videos.append(
                            os.path.join(o["outputDirectory_video"], video_file)
                        )

                if matching_videos:
                    latest_video = max(matching_videos, key=os.path.getmtime)
                    files_with_mtime.append(
                        (
                            os.path.join(o["outputDirectory_metadata"], f),
                            prefix,
                            os.path.getmtime(latest_video),
                        )
                    )

        files_with_mtime.sort(key=lambda x: x[2], reverse=True)

        return [(thumb, prefix) for thumb, prefix, _ in files_with_mtime]

    def refresh_gallery() -> tuple[gr.State, gr.Gallery]:
        new_items = get_gallery_items()
        return (
            new_items,  # gallery_items_state
            gr.update(value=[item[0] for item in new_items]),  # thumbs
        )

    def get_latest_video_version(prefix) -> str:
        max_number = -1
        selected_file = None
        for f in os.listdir(o["outputDirectory_video"]):
            if f.startswith(prefix + "_") and f.endswith(".mp4"):
                if "combined" in f:
                    continue
                try:
                    num_str = f.replace(prefix + "_", "").replace(".mp4", "")
                    if num_str.isdigit():
                        num = int(num_str)
                        if num > max_number:
                            max_number = num
                            selected_file = f
                except (ValueError, TypeError):
                    continue
        return selected_file

    def load_video_and_info_from_prefix(
        prefix,
    ) -> tuple[None, str, gr.Button, None] | tuple[str, str, gr.Button, str]:
        video_file = get_latest_video_version(prefix)
        if not video_file:
            video_file = f"{prefix}.mp4"

        video_path = os.path.join(o["outputDirectory_video"], video_file)
        json_path = os.path.join(o["outputDirectory_metadata"], f"{prefix}.json")

        if not os.path.exists(video_path) or not os.path.exists(json_path):
            return None, "Video or JSON not found.", gr.update(visible=False), None

        with open(json_path, "r", encoding="utf-8") as f:
            info_content = json.load(f)

        return (
            video_path,
            json.dumps(info_content, indent=2, ensure_ascii=False),
            gr.update(visible=True),
            video_path,
        )

    def delete_selected_item(
        selected_prefix: str,
    ) -> tuple[gr.Video, gr.State, List, gr.Gallery, gr.Button, gr.Accordion]:
        if not selected_prefix:
            return (
                gr.update(visible=False),  # video out
                None,  # selected_original_video_path_state
                [],  # gallery_items_state
                gr.update(value=[]),  # thumbs
                gr.update(visible=False),  # delete button
                gr.update(visible=False, open=False),  # generate audio accordion
            )

        deleted_files = []

        # Delete all MP4 files with the pattern prefix_*.mp4
        for filename in os.listdir(o["outputDirectory_video"]):
            if filename.startswith(selected_prefix + "_") and filename.endswith(".mp4"):
                file_path = os.path.join(o["outputDirectory_video"], filename)
                try:
                    os.remove(file_path)
                    deleted_files.append(filename)
                except Exception as e:
                    logger.error(f"Error deleting {filename}: {e}")

        # Also delete the base prefix.mp4 if it exists
        base_file = f"{selected_prefix}.mp4"
        base_path = os.path.join(o["outputDirectory_video"], base_file)
        if os.path.exists(base_path):
            try:
                os.remove(base_path)
                deleted_files.append(base_file)
            except Exception as e:
                logger.error(f"Error deleting {base_file}: {e}")

        # Delete metadata files (json and png)
        for ext in [".json", ".png"]:
            meta_file = f"{selected_prefix}{ext}"
            meta_path = os.path.join(o["outputDirectory_metadata"], meta_file)
            if os.path.exists(meta_path):
                try:
                    os.remove(meta_path)
                    deleted_files.append(meta_file)
                except Exception as e:
                    logger.error(f"Error deleting {meta_file}: {e}")

        logger.debug(f"Deleted files: {deleted_files}")

        # Refresh the gallery
        new_items = get_gallery_items()
        return (
            gr.update(visible=False),  # video out
            None,  # selected_original_video_path_state
            new_items,  # gallery_items_state
            gr.update(value=[item[0] for item in new_items]),  # thumbs
            gr.update(visible=False),  # delete button
            gr.update(
                visible=False, open=False
            ),  # Make generate audio accordion invisible
        )

    def on_select(
        gallery_items, evt: gr.SelectData
    ) -> tuple[
        gr.Video,
        gr.Textbox,
        gr.Button,
        gr.State,
        gr.Button,
        gr.State,
        gr.Accordion,
        gr.Checkbox,
    ]:
        if evt.index is None or not gallery_items or evt.index >= len(gallery_items):
            return (
                gr.update(visible=False),  # video_out
                gr.update(visible=False),  # info_out
                gr.update(visible=False),  # send_to_toolbox_btn
                None,  # selected_original_video_path_state
                gr.update(visible=False),  # delete_btn
                None,  # selected_prefix_state
                gr.update(visible=False),  # gen_audio_acc
                gr.update(visible=False),  # overwrite_audio_chkbox
            )

        prefix = gallery_items[evt.index][1]
        original_video_path, info_string, button_visibility, new_selected_path = (
            load_video_and_info_from_prefix(prefix)
        )

        overwrite_audio_checkbox_visibility = check_audio(prefix)[0]

        return (
            gr.update(
                value=original_video_path, visible=bool(original_video_path)
            ),  # video_out
            gr.update(value=info_string, visible=bool(original_video_path)),  # info_out
            gr.update(visible=bool(original_video_path)),  # send_to_toolbox_btn
            new_selected_path,  # selected_original_video_path_state
            gr.update(visible=bool(original_video_path)),  # delete_btn
            prefix,  # selected_prefix_state
            gr.update(visible=bool(original_video_path)),  # gen_audio_acc
            overwrite_audio_checkbox_visibility,  # overwrite_audio_chkbox
        )

    def send_to_toolbox(selected_video_path) -> tuple[gr.Tab, gr.Tabs]:
        return gr.update(value=selected_video_path), gr.update(selected="toolbox_tab")

    def get_video_file_and_metadata(prefix) -> tuple[Path, str]:
        original_video_path, metadata, button_visibility, new_selected_path = (
            load_video_and_info_from_prefix(prefix)
        )
        if original_video_path is None:
            logging.error(f"Video file and metadata for prefix {prefix}, not found")
        return Path(original_video_path), metadata

    def get_audio(selected_prefix: str) -> tuple[Path, Any, int]:
        video_file_path = get_video_file_and_metadata(selected_prefix)[0]

        from moviepy import VideoFileClip

        video_clip = VideoFileClip(video_file_path)

        # get the audio from the video
        video_audio = video_clip.audio

        # get the duration of the video
        video_duration = video_clip.duration

        return (
            video_file_path,
            video_audio,
            video_duration,
        )

    def generate_audio(
        selected_prefix: str,
        audio_model_dropdown: gr.Dropdown,
        overwrite_audio_chkbox: gr.Checkbox,
        audio_prompt_txt: gr.Textbox,
        audio_prompt_neg_txt: gr.Textbox,
        audio_prompt_chkbox: gr.Checkbox,
        audio_steps: int,
        audio_cfg: float,
    ) -> tuple[gr.State]:
        if not selected_prefix:
            return (
                None,  # selected_original_video_path_state
            )

        video_file, metadata = get_video_file_and_metadata(selected_prefix)
        # load the metadata as a json
        metadata = json.loads(metadata)

        video_file_path, video_audio, duration = get_audio(selected_prefix)

        logger.info("GENAudio: Loading video")

        if video_audio is not None and overwrite_audio_chkbox is False:
            logging.info(
                "GENAudio: Audio exists but overwrite audio is unchecked -> skipping"
            )
            return (
                None,  # selected_original_video_path_state
            )

        # The video prompt describes what the scene looks like, which is still
        # a reasonable description of what it should sound like.
        prompt = metadata.get("prompt", "")
        if audio_prompt_txt:
            prompt = (
                f"{prompt}, {audio_prompt_txt}"
                if audio_prompt_chkbox and prompt
                else audio_prompt_txt
            )

        # Don't reuse the video's negative prompt: it lists visual defects
        # ("blurry", "low quality"), not sounds.
        negative_prompt = audio_prompt_neg_txt or ""

        # Steps and CFG are the audio model's own; the video's "cfg" is
        # usually 1, which turns MMAudio's guidance off.
        steps = int(audio_steps)
        cfg_strength = float(audio_cfg)

        model_config = None

        if audio_model_dropdown:
            model_config = all_model_cfg.get(audio_model_dropdown)

        logger.info(
            f"GENAudio: Generating audio with\n"
            f" prompt:{str(prompt)}\n"
            f" negative prompt:{str(negative_prompt)}\n"
            f" steps:{str(steps)}\n"
            f" cfg:{str(cfg_strength)}"
        )

        audio_net_model, features_utils, sequence_config = get_mmaudio_model(
            model_config
        )
        video_with_audio_path = add_audio_to_video(
            video_path=video_file,
            prompt=prompt,
            audio_negative_prompt=negative_prompt,
            audio_steps=steps,
            audio_cfg_strength=cfg_strength,
            duration=duration,
            audio_net=audio_net_model,
            audio_feature_utils=features_utils,
            audio_seq_cfg=sequence_config,
            overwrite_orig_file=True,
        )

        if video_with_audio_path is not None:
            logger.info(
                "Generating audio finished for video: " + video_with_audio_path.name
            )
        else:
            logger.info("Error generating audio for video: " + video_file.name)

        return (
            None,  # selected_original_video_path_state
        )

    def delete_audio(selected_prefix: str):
        if not selected_prefix:
            return

        video_file_path, video_audio, duration = get_audio(selected_prefix)

        if video_audio is not None:
            video_info = load_video(video_file_path, duration)
            reencode_without_audio(video_info, video_file_path)

            logger.info(f"Deleted audio for video {str(video_file_path)}")
        else:
            logger.info(f"No audio found for video {str(video_file_path)}")

    def check_audio(selected_prefix: str) -> tuple[gr.Checkbox]:
        if not selected_prefix:
            return (
                gr.update(visible=False),  # overwrite_audio_chkbox
            )

        try:
            video_file_path, video_audio, duration = get_audio(selected_prefix)
            if video_audio is not None:
                return (
                    gr.update(visible=True, value=False),  # overwrite_audio_chkbox
                )
            else:
                return (
                    gr.update(visible=False),  # overwrite_audio_chkbox
                )
        except Exception as e:
            logger.error(f"Error checking audio: {e}")
            return (gr.update(visible=False),)

    o["refresh_gallery_button"].click(
        fn=refresh_gallery, inputs=[], outputs=[o["gallery_items_state"], o["thumbs"]]
    )
    o["thumbs"].select(
        fn=on_select,
        inputs=[o["gallery_items_state"]],
        outputs=[
            o["video_out"],
            o["info_out"],
            o["send_to_toolbox_btn"],
            o["selected_original_video_path_state"],
            o["delete_btn"],
            o["selected_prefix_state"],
            o["gen_audio_acc"],
            o["overwrite_audio_chkbox"],
        ],
    )
    o["send_to_toolbox_btn"].click(
        fn=send_to_toolbox,
        inputs=[o["selected_original_video_path_state"]],
        outputs=[tb_target_video_input, main_tabs_component],
    )
    o["delete_btn"].click(
        fn=delete_selected_item,
        inputs=[o["selected_prefix_state"]],
        outputs=[
            o["video_out"],
            o["selected_original_video_path_state"],
            o["gallery_items_state"],
            o["thumbs"],
            o["delete_btn"],
            o["gen_audio_acc"],
        ],
    )
    o["gen_audio_btn"].click(
        fn=generate_audio,
        inputs=[
            o["selected_prefix_state"],
            o["audio_model_dropdown"],
            o["overwrite_audio_chkbox"],
            o["audio_prompt_txt"],
            o["audio_prompt_neg_txt"],
            o["audio_prompt_chkbox"],
            o["audio_steps_slider"],
            o["audio_cfg_slider"],
        ],
        outputs=[
            o["selected_original_video_path_state"],
        ],
    )
    o["audio_delete_btn"].click(
        fn=delete_audio,
        inputs=[
            o["selected_prefix_state"],
        ],
        outputs=[],
    )
    o["gen_audio_acc"].expand(
        fn=check_audio,
        inputs=[
            o["selected_prefix_state"],
        ],
        outputs=[
            o["overwrite_audio_chkbox"],
        ],
    )
    return get_gallery_items
