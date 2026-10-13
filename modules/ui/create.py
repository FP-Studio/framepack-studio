"""
The Create tab: everything needed to set up a job and add it to the queue.

Layout: the left column is the job (model and source, inputs, prompt, shot,
timeline, motion, LoRAs, quality); the right column is a sticky rail with the
live preview, checks, the queue button and what's up next.

Which controls are usable comes from modules.ui.capabilities, so a feature
the chosen model can't use is disabled with a reason instead of being
silently dropped by the worker.
"""

import json
import logging
import random

import gradio as gr
import numpy as np
from PIL import Image

from diffusers_helper.bucket_tools import find_nearest_bucket
from modules.llm_captioner import caption_image, stop_captioning
from modules.llm_enhancer import enhance_prompt, stop_enhancing
from modules.pipelines.flow_noise import CAMERA_MOVES
from modules.ui import capabilities as caps
from modules.ui import presets
from modules.ui.components.motion_canvas import MotionCanvas
from modules.ui.components.timeline import Timeline
from modules.ui.timeline_model import build_timeline, keyframe_times_from_timeline

logger = logging.getLogger(__name__)

NUM_KEYFRAME_SLOTS = 3
MAX_SEED = 2**31 - 1

# Component keys saved in presets. Unchanged from the old Generate tab so
# existing presets still load.
PRESET_KEYS = [
    "prompt",
    "n_prompt",
    "blend_sections",
    "steps",
    "total_second_length",
    "resolutionW",
    "resolutionH",
    "seed",
    "randomize_seed",
    "gs",
    "cfg",
    "rs",
    "latent_window_size",
    "cache_type",
    "teacache_num_steps",
    "teacache_rel_l1_thresh",
    "magcache_threshold",
    "magcache_max_consecutive_skips",
    "magcache_retention_ratio",
    "latent_type",
    "end_frame_strength_original",
    "combine_with_source",
    "num_cleaned_frames",
    "lora_selector",
]

CACHE_CHOICES = [
    ("MagCache (faster)", "MagCache"),
    ("TeaCache", "TeaCache"),
    ("Off (slowest, full quality)", "None"),
]


def _quality_label(steps, cache_type):
    cache = {"MagCache": "MagCache", "TeaCache": "TeaCache"}.get(cache_type, "no cache")
    return f"Quality & speed · {int(steps)} steps · {cache}"


def _bucket_text(img, width, height):
    h, w = (height, width) if img is None else img.shape[:2]
    res = (width + height) / 2 if img is None else width
    bucket_h, bucket_w = find_nearest_bucket(h, w, resolution=res)
    return f"Output size **{bucket_w} × {bucket_h}**"


def create_create_ui(lora_names, default_prompt, dummy_lora_name, settings):
    initial_model, initial_source = "Original", "Image"

    with gr.Row(elem_id="create-root", equal_height=False):
        # ------------------------------------------------------------------ job
        with gr.Column(scale=7, elem_id="create-main"):
            with gr.Row(elem_classes="setup-bar", equal_height=True):
                model = gr.Radio(
                    list(caps.MODELS),
                    value=initial_model,
                    label="Model",
                    elem_classes="segmented",
                    scale=0,
                    min_width=150,
                )
                source = gr.Radio(
                    list(caps.SOURCES),
                    value=initial_source,
                    label="Start from",
                    elem_classes="segmented",
                    scale=0,
                    min_width=150,
                )
                with gr.Column(scale=2, min_width=240, elem_classes="preset-col"):
                    preset_dropdown = gr.Dropdown(
                        label="Preset",
                        choices=presets.list_presets(initial_model, initial_source),
                        value=None,
                    )
                    with gr.Row(elem_classes="preset-actions"):
                        preset_save_btn = gr.Button("Save as preset…", size="sm")
                        preset_delete_btn = gr.Button(
                            "Delete preset", size="sm", interactive=False
                        )
            with gr.Row(visible=False, elem_classes="inline-form") as preset_save_row:
                preset_name = gr.Textbox(
                    label="Preset name",
                    placeholder="e.g. Portrait, slow push-in",
                    scale=3,
                )
                preset_save_confirm = gr.Button("Save", variant="primary", scale=0)
                preset_save_cancel = gr.Button("Cancel", scale=0)
            with gr.Row(visible=False, elem_classes="inline-form") as preset_delete_row:
                preset_delete_text = gr.Markdown("")
                preset_delete_yes = gr.Button("Delete", variant="stop", scale=0)
                preset_delete_no = gr.Button("Keep it", scale=0)

            # Inputs
            with gr.Row(equal_height=False, elem_classes="frames-row"):
                with gr.Column(scale=1, min_width=220) as image_col:
                    input_image = gr.Image(
                        sources="upload",
                        type="numpy",
                        label="Start frame · optional",
                        image_mode="RGB",
                        height=280,
                        show_download_button=False,
                        elem_classes="frame-input",
                    )
                    latent_type = gr.Dropdown(
                        ["Noise", "White", "Black", "Green Screen"],
                        value="Noise",
                        label="Without a start frame, begin from",
                        visible=True,
                    )
                with gr.Column(scale=1, min_width=220, visible=False) as video_col:
                    input_video = gr.Video(
                        sources="upload",
                        label="Video to extend",
                        height=280,
                        elem_id="video-input",
                    )
                    combine_with_source = gr.Checkbox(
                        label="Join the result onto the source video",
                        value=True,
                    )
                    num_cleaned_frames = gr.Slider(
                        label="Context frames from the source",
                        minimum=2,
                        maximum=10,
                        value=5,
                        step=1,
                        info="More keeps the look of the source but uses more memory "
                        "and can restrict motion.",
                    )
                with gr.Column(scale=1, min_width=220) as end_col:
                    end_frame_image = gr.Image(
                        sources="upload",
                        type="numpy",
                        label="End frame · optional",
                        image_mode="RGB",
                        height=280,
                        show_download_button=False,
                        elem_classes="frame-input",
                    )
                    end_frame_strength = gr.Slider(
                        label="End frame influence",
                        minimum=0.05,
                        maximum=1.0,
                        value=1.0,
                        step=0.05,
                    )
                    end_frame_note = gr.Markdown("", elem_classes="field-note")

            # Prompt
            prompt = gr.Textbox(
                label="Prompt",
                value=default_prompt,
                lines=3,
                info="Change the prompt over time with [2s: …] — the timeline "
                "below shows where each part lands.",
            )
            with gr.Row(elem_classes="prompt-tools"):
                enhance_btn = gr.Button("Enhance prompt", size="sm", scale=0)
                stop_enhance_btn = gr.Button(
                    "Stop enhancing", size="sm", variant="stop", scale=0, visible=False
                )
                caption_btn = gr.Button("Describe start frame", size="sm", scale=0)
                stop_caption_btn = gr.Button(
                    "Stop describing", size="sm", variant="stop", scale=0, visible=False
                )
            with gr.Accordion("More prompt options", open=False):
                n_prompt = gr.Textbox(label="Negative prompt", value="")
                blend_sections = gr.Slider(
                    minimum=0,
                    maximum=10,
                    value=4,
                    step=1,
                    label="Blend between prompt changes (sections)",
                    info="How many sections each prompt change fades over.",
                )

            # Shot
            with gr.Group(elem_classes="shot-group"):
                with gr.Row():
                    total_second_length = gr.Slider(
                        label="Length (seconds)",
                        minimum=1,
                        maximum=120,
                        value=6,
                        step=0.1,
                        scale=3,
                    )
                    seed = gr.Number(label="Seed", value=2500, precision=0, scale=1)
                    randomize_seed = gr.Checkbox(
                        label="New seed after each job",
                        value=True,
                        scale=1,
                    )
                with gr.Row():
                    resolutionW = gr.Slider(
                        label="Width", minimum=128, maximum=768, value=640, step=32
                    )
                    resolutionH = gr.Slider(
                        label="Height", minimum=128, maximum=768, value=640, step=32
                    )
                resolution_text = gr.Markdown(
                    _bucket_text(None, 640, 640), elem_classes="field-note right"
                )

            timeline = Timeline(
                label="Timeline", elem_id="create-timeline", interactive=True
            )

            # Motion
            with gr.Column(elem_classes="motion-group"):
                gr.Markdown("### Motion", elem_classes="section-title")
                with gr.Tabs(elem_id="motion-tabs", selected="keyframes"):
                    # Hidden: warped noise breaks the real model even at low
                    # strength (tested on HunyuanVideo FramePack). Needs a
                    # fine-tuned model.
                    with gr.Tab("Camera & arrows", id="motion_sketch", visible=False):
                        sketch_note = gr.Markdown("", elem_classes="field-note warn")
                        motion_canvas = MotionCanvas(
                            label="Draw where things should move",
                            show_label=False,
                            interactive=True,
                        )
                        with gr.Row():
                            camera = gr.Dropdown(
                                label="Camera move",
                                choices=list(CAMERA_MOVES),
                                value="None",
                            )
                            camera_amount = gr.Slider(
                                label="Camera amount",
                                minimum=0.0,
                                maximum=1.0,
                                value=0.3,
                                step=0.05,
                                info="How far the camera travels, as a share of the frame.",
                            )
                        flow_strength = gr.Slider(
                            label="Motion strength",
                            minimum=0.0,
                            maximum=1.0,
                            value=0.7,
                            step=0.05,
                            info="Arrows and camera moves nudge the model rather than "
                            "force it. High values can freeze texture in place.",
                        )
                    with gr.Tab("Keyframes", id="keyframes"):
                        keyframes_note = gr.Markdown("", elem_classes="field-note warn")
                        gr.Markdown(
                            "Images the video should pass through. Each one snaps to "
                            "the nearest section boundary — drag its marker on the "
                            "timeline to move it.",
                            elem_classes="field-note",
                        )
                        keyframe_images, keyframe_times = [], []
                        with gr.Row():
                            for i in range(NUM_KEYFRAME_SLOTS):
                                with gr.Column(min_width=140):
                                    keyframe_images.append(
                                        gr.Image(
                                            sources="upload",
                                            type="numpy",
                                            label=f"Keyframe {i + 1}",
                                            image_mode="RGB",
                                            height=150,
                                            show_download_button=False,
                                            elem_classes="frame-input",
                                        )
                                    )
                                    keyframe_times.append(
                                        gr.Number(
                                            label="At (seconds)",
                                            value=round(2.0 * (i + 1), 1),
                                            minimum=0,
                                            step=0.1,
                                        )
                                    )
                    with gr.Tab("Reference video", id="motion_reference"):
                        reference_note = gr.Markdown("", elem_classes="field-note warn")
                        gr.Markdown(
                            "Follow the motion and layout of another clip. Where things "
                            "are and how they move carry over; the prompt and start "
                            "frame decide what they look like.",
                            elem_classes="field-note",
                        )
                        motion_reference_video = gr.Video(
                            sources="upload", label="Reference clip", height=220
                        )
                        with gr.Row():
                            motion_reference_strength = gr.Slider(
                                label="Follow the reference",
                                minimum=0.0,
                                maximum=1.0,
                                value=0.5,
                                step=0.05,
                                info="Higher values also copy more of its shapes and "
                                "framing.",
                            )
                            motion_reference_start = gr.Number(
                                label="Start at (seconds)",
                                value=0,
                                minimum=0,
                                step=0.1,
                                info="A single shot works best; cuts in the reference "
                                "become cuts in the video.",
                            )

            # LoRAs
            with gr.Accordion("LoRAs", open=False) as lora_accordion:
                with gr.Row(equal_height=True):
                    lora_selector = gr.Dropdown(
                        choices=lora_names,
                        label="LoRAs",
                        multiselect=True,
                        value=[],
                        scale=10,
                        show_label=False,
                        info="Pick one or more; a weight slider appears for each.",
                    )
                    refresh_loras_button = gr.Button(
                        "Rescan folder", scale=0, size="sm"
                    )
                lora_names_states = gr.State(lora_names)
                lora_sliders = {
                    lora: gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=1.0,
                        step=0.01,
                        label=lora,
                        visible=False,
                        interactive=True,
                    )
                    for lora in lora_names
                }

            # Quality & speed
            with gr.Accordion(_quality_label(25, "MagCache"), open=False) as quality:
                steps = gr.Slider(
                    label="Steps", minimum=1, maximum=100, value=25, step=1
                )
                cache_type = gr.Radio(
                    CACHE_CHOICES,
                    value="MagCache",
                    label="Speed-up cache",
                    info="A cache skips some steps. Faster, but can soften detail or "
                    "change motion.",
                )
                with gr.Row(visible=True) as magcache_row:
                    magcache_threshold = gr.Slider(
                        label="MagCache threshold",
                        minimum=0.01,
                        maximum=1.0,
                        step=0.01,
                        value=0.1,
                        info="Higher is faster.",
                    )
                    magcache_max_consecutive_skips = gr.Slider(
                        label="Max skips in a row",
                        minimum=1,
                        maximum=5,
                        step=1,
                        value=2,
                        info="Higher is faster.",
                    )
                    magcache_retention_ratio = gr.Slider(
                        label="Protected early steps",
                        minimum=0.0,
                        maximum=1.0,
                        step=0.01,
                        value=0.25,
                        info="Lower is faster.",
                    )
                with gr.Row(visible=False) as teacache_row:
                    teacache_num_steps = gr.Slider(
                        label="TeaCache steps",
                        minimum=1,
                        maximum=50,
                        step=1,
                        value=25,
                    )
                    teacache_rel_l1_thresh = gr.Slider(
                        label="TeaCache threshold",
                        minimum=0.01,
                        maximum=1.0,
                        step=0.01,
                        value=0.15,
                        info="Higher is faster.",
                    )
                with gr.Row():
                    gs = gr.Slider(
                        label="Distilled guidance",
                        minimum=1.0,
                        maximum=32.0,
                        value=10.0,
                        step=0.5,
                    )
                    cfg = gr.Slider(
                        label="Real guidance (CFG)",
                        minimum=1.0,
                        maximum=3.0,
                        value=1.0,
                        step=0.1,
                        info="Above 1 follows the prompt more closely but takes "
                        "about twice as long.",
                    )
                    rs = gr.Slider(
                        label="Guidance rescale",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.0,
                        step=0.05,
                    )
                latent_window_size = gr.Slider(
                    label="Section size (latent window)",
                    minimum=1,
                    maximum=60,
                    value=9,
                    step=1,
                    info="Sets how long each section is (9 ≈ 1.2 s). Experimental — "
                    "the model was trained at 9.",
                )

        # ----------------------------------------------------------------- rail
        with gr.Column(scale=5, elem_id="create-rail"):
            progress_desc = gr.Markdown("", elem_classes="progress-desc")
            progress_bar = gr.HTML("", elem_classes="progress-html")
            with gr.Group(elem_classes="rail-card"):
                preview_image = gr.Image(
                    label="Live preview",
                    type="numpy",
                    interactive=False,
                    image_mode="RGB",
                    height=150,
                    elem_classes="live-preview",
                    show_download_button=False,
                )
                result_video = gr.Video(
                    label="Latest result",
                    autoplay=True,
                    loop=True,
                    height=300,
                    show_share_button=False,
                    interactive=False,
                )
            reroll_state = gr.State(None)
            with gr.Column(visible=False, elem_classes="reroll-banner") as reroll_row:
                reroll_text = gr.Markdown("")
                reroll_clear_btn = gr.Button("Stop re-rolling", size="sm", scale=0)
            checks = gr.Markdown("", elem_classes="checks")
            start_button = gr.Button(
                "Add to queue", variant="primary", size="lg", elem_id="add-to-queue"
            )
            end_button = gr.Button(
                "Cancel current job", variant="stop", visible=False, size="sm"
            )
            with gr.Accordion(
                "Batch: one job per image", open=False, visible=True
            ) as batch_accordion:
                gr.Markdown(
                    "Every image gets the settings on the left as its start frame.",
                    elem_classes="field-note",
                )
                batch_input_images = gr.File(
                    label="Images",
                    file_count="multiple",
                    file_types=["image"],
                    type="filepath",
                )
                add_batch_to_queue_btn = gr.Button("Add batch to queue")
            up_next = gr.HTML("", elem_classes="up-next")
            current_job_id = gr.Textbox(value="", visible=False)

    ui = locals()
    ui.pop("i", None)
    ui["lora_slider_list"] = list(lora_sliders.values())
    ui["preset_components"] = {
        "prompt": prompt,
        "n_prompt": n_prompt,
        "blend_sections": blend_sections,
        "steps": steps,
        "total_second_length": total_second_length,
        "resolutionW": resolutionW,
        "resolutionH": resolutionH,
        "seed": seed,
        "randomize_seed": randomize_seed,
        "gs": gs,
        "cfg": cfg,
        "rs": rs,
        "latent_window_size": latent_window_size,
        "cache_type": cache_type,
        "teacache_num_steps": teacache_num_steps,
        "teacache_rel_l1_thresh": teacache_rel_l1_thresh,
        "magcache_threshold": magcache_threshold,
        "magcache_max_consecutive_skips": magcache_max_consecutive_skips,
        "magcache_retention_ratio": magcache_retention_ratio,
        "latent_type": latent_type,
        "end_frame_strength_original": end_frame_strength,
        "combine_with_source": combine_with_source,
        "num_cleaned_frames": num_cleaned_frames,
        "lora_selector": lora_selector,
        **lora_sliders,
    }
    return ui


# --------------------------------------------------------------------- events


def render_up_next(jobs, current_job):
    """Small list for the rail: what's running and what's next."""
    from html import escape

    pending = [j for j in jobs if j.status.value.lower() == "pending"]
    if not current_job and not pending:
        return "<div class='up-next-empty'>The queue is empty.</div>"
    rows = []
    if current_job:
        prompt = escape((current_job.params.get("prompt_text") or "")[:70])
        rows.append(f"<li class='running'><span>Running</span>{prompt}</li>")
    for job in pending[:4]:
        prompt = escape((job.params.get("prompt_text") or "")[:70])
        length = job.params.get("total_second_length", "")
        rows.append(f"<li><span>{length}s</span>{prompt}</li>")
    more = len(pending) - 4
    tail = (
        f"<div class='up-next-more'>and {more} more in the Queue tab</div>"
        if more > 0
        else ""
    )
    return f"<div class='up-next-title'>Up next</div><ul>{''.join(rows)}</ul>{tail}"


def connect_create_events(g, f, settings, dummy_lora_name):
    """g: create components, f: shared functions from interface.py."""
    stats_outputs = f["stats_outputs"]

    # ---- model / source -----------------------------------------------------
    feature_inputs = [
        g["model"],
        g["source"],
        g["input_video"],
        g["end_frame_image"],
        *g["keyframe_images"],
        g["motion_canvas"],
        g["camera"],
        g["camera_amount"],
        g["motion_reference_video"],
        g["reroll_state"],
    ]

    def _features_in_use(
        end_image, kf_images, canvas, camera, amount, ref_video, reroll
    ):
        arrows = (canvas or {}).get("arrows") or []
        return {
            "end_frame": end_image is not None,
            "keyframes": any(img is not None for img in kf_images),
            "motion_sketch": bool(arrows) or (camera not in (None, "None") and amount),
            "motion_reference": bool(ref_video),
            "reroll": bool(reroll),
        }

    def assess(model, source, input_video, end_image, *rest):
        kf_images = rest[:NUM_KEYFRAME_SLOTS]
        canvas, camera, amount, ref_video, reroll = rest[NUM_KEYFRAME_SLOTS:]
        problems, notes = [], []
        if source == "Video" and not input_video:
            problems.append("Add a video to extend.")
        used = _features_in_use(
            end_image, kf_images, canvas, camera, amount, ref_video, reroll
        )
        for feature, in_use in used.items():
            if in_use and not caps.supports(feature, model, source):
                notes.append(
                    f"{caps.FEATURE_LABELS[feature]} will be skipped — "
                    f"it only works with {caps.supported_setups(feature)}."
                )
        lines = [f"<div class='fps-check stop'>{p}</div>" for p in problems]
        lines += [f"<div class='fps-check warn'>{n}</div>" for n in notes]
        return (
            "".join(lines),
            gr.update(interactive=not problems),
        )

    def on_setup_change(model, source, preset=None):
        is_video = source == "Video"
        notes = {
            feature: caps.unsupported_reason(feature, model, source)
            for feature in (
                "keyframes",
                "motion_sketch",
                "motion_reference",
                "end_frame",
            )
        }
        keyframes_ok = not notes["keyframes"]
        end_ok = not notes["end_frame"]
        return [
            gr.update(visible=not is_video),  # image_col
            gr.update(visible=is_video),  # video_col
            gr.update(interactive=end_ok),  # end_frame_image
            gr.update(interactive=end_ok),  # end_frame_strength
            notes["end_frame"],  # end_frame_note
            notes["keyframes"],
            notes["motion_sketch"],
            notes["motion_reference"],
            *[gr.update(interactive=keyframes_ok)] * (2 * NUM_KEYFRAME_SLOTS),
            gr.update(interactive=not notes["motion_sketch"]),  # camera
            gr.update(interactive=not notes["motion_sketch"]),  # camera_amount
            gr.update(interactive=not notes["motion_sketch"]),  # flow_strength
            gr.update(interactive=not notes["motion_reference"]),  # ref video
            gr.update(interactive=not notes["motion_reference"]),  # ref strength
            gr.update(interactive=not notes["motion_reference"]),  # ref start
            gr.update(visible=caps.supports("batch", model, source)),
            gr.update(visible=not is_video),  # caption button
            gr.update(
                choices=(names := presets.list_presets(model, source)),
                value=preset if preset in names else None,
            ),
        ]

    setup_outputs = [
        g["image_col"],
        g["video_col"],
        g["end_frame_image"],
        g["end_frame_strength"],
        g["end_frame_note"],
        g["keyframes_note"],
        g["sketch_note"],
        g["reference_note"],
        *g["keyframe_images"],
        *g["keyframe_times"],
        g["camera"],
        g["camera_amount"],
        g["flow_strength"],
        g["motion_reference_video"],
        g["motion_reference_strength"],
        g["motion_reference_start"],
        g["batch_accordion"],
        g["caption_btn"],
        g["preset_dropdown"],
    ]

    # ---- timeline -----------------------------------------------------------
    timeline_inputs = [
        g["total_second_length"],
        g["latent_window_size"],
        g["model"],
        g["source"],
        g["prompt"],
        g["blend_sections"],
        g["input_image"],
        g["input_video"],
        g["end_frame_image"],
        *g["keyframe_images"],
        *g["keyframe_times"],
        g["camera"],
        g["camera_amount"],
        g["motion_canvas"],
        g["motion_reference_video"],
        g["reroll_state"],
    ]

    def refresh_timeline(
        length, window, model, source, prompt, blend, img, video, end, *rest
    ):
        kf_images = rest[:NUM_KEYFRAME_SLOTS]
        kf_times = rest[NUM_KEYFRAME_SLOTS : 2 * NUM_KEYFRAME_SLOTS]
        camera, amount, canvas, ref_video, reroll = rest[2 * NUM_KEYFRAME_SLOTS :]
        return build_timeline(
            total_second_length=length,
            latent_window_size=window,
            model=model,
            source=source,
            prompt=prompt,
            blend_sections=blend,
            has_start=(video if source == "Video" else img) is not None,
            has_end=end is not None,
            keyframe_slots=[(t, im is not None) for t, im in zip(kf_times, kf_images)],
            camera=camera,
            camera_amount=amount,
            arrow_count=len((canvas or {}).get("arrows") or []),
            reference_path=ref_video,
            reroll_from_section=(reroll or {}).get("section"),
        )

    def on_timeline_input(value, *times):
        return keyframe_times_from_timeline(value, list(times))

    g["timeline"].input(
        fn=on_timeline_input,
        inputs=[g["timeline"], *g["keyframe_times"]],
        outputs=g["keyframe_times"],
        show_progress="hidden",
    )

    def wire(component, event="change"):
        getattr(component, event)(
            fn=refresh_timeline,
            inputs=timeline_inputs,
            outputs=[g["timeline"]],
            show_progress="hidden",
            trigger_mode="always_last",
        )
        getattr(component, event)(
            fn=assess,
            inputs=feature_inputs,
            outputs=[g["checks"], g["start_button"]],
            show_progress="hidden",
            trigger_mode="always_last",
        )

    for component in [
        g["total_second_length"],
        g["latent_window_size"],
        g["prompt"],
        g["blend_sections"],
        g["input_image"],
        g["input_video"],
        g["end_frame_image"],
        *g["keyframe_images"],
        *g["keyframe_times"],
        g["camera"],
        g["camera_amount"],
        g["motion_reference_video"],
    ]:
        wire(component)
    wire(g["motion_canvas"], "input")
    wire(g["reroll_state"])

    for component in (g["model"], g["source"]):
        component.change(
            fn=on_setup_change,
            inputs=[g["model"], g["source"], g["preset_dropdown"]],
            outputs=setup_outputs,
            show_progress="hidden",
        )
        wire(component)

    # ---- motion canvas follows the start frame and camera ------------------
    def canvas_value(image, canvas, camera, amount, model, source):
        canvas = canvas or {}
        reason = caps.unsupported_reason("motion_sketch", model, source)
        return {
            "background": image,
            "arrows": canvas.get("arrows") or [],
            "camera": camera or "None",
            "camera_amount": amount or 0.0,
            "enabled": not reason,
            "reason": reason,
        }

    canvas_inputs = [
        g["input_image"],
        g["motion_canvas"],
        g["camera"],
        g["camera_amount"],
        g["model"],
        g["source"],
    ]
    for component in (
        g["input_image"],
        g["camera"],
        g["camera_amount"],
        g["model"],
        g["source"],
    ):
        component.change(
            fn=canvas_value,
            inputs=canvas_inputs,
            outputs=[g["motion_canvas"]],
            show_progress="hidden",
        )

    # ---- small field behaviours --------------------------------------------
    def on_resolution_change(img, width, height):
        return _bucket_text(img, width, height)

    for component in (g["resolutionW"], g["resolutionH"], g["input_image"]):
        component.change(
            fn=on_resolution_change,
            inputs=[g["input_image"], g["resolutionW"], g["resolutionH"]],
            outputs=[g["resolution_text"]],
            show_progress="hidden",
        )

    g["input_image"].change(
        fn=lambda img: gr.update(visible=img is None),
        inputs=[g["input_image"]],
        outputs=[g["latent_type"]],
        show_progress="hidden",
    )

    def on_cache_change(cache_type, steps):
        return (
            gr.update(visible=cache_type == "MagCache"),
            gr.update(visible=cache_type == "TeaCache"),
            gr.update(label=_quality_label(steps, cache_type)),
        )

    for component in (g["cache_type"], g["steps"]):
        component.change(
            fn=on_cache_change,
            inputs=[g["cache_type"], g["steps"]],
            outputs=[g["magcache_row"], g["teacache_row"], g["quality"]],
            show_progress="hidden",
        )

    def update_lora_sliders(selected, all_loras):
        selected = [name for name in selected or [] if name != dummy_lora_name]
        return [gr.update(value=selected)] + [
            gr.update(visible=name in selected) for name in all_loras
        ]

    g["lora_selector"].change(
        fn=update_lora_sliders,
        inputs=[g["lora_selector"], g["lora_names_states"]],
        outputs=[g["lora_selector"]] + g["lora_slider_list"],
        show_progress="hidden",
    )

    # ---- presets ------------------------------------------------------------
    preset_keys = list(g["preset_components"].keys())
    preset_values = list(g["preset_components"].values())

    def apply_preset(name, model, source):
        preset = presets.get_preset(model, source, name) if name else None
        if not preset:
            return [gr.update()] * len(preset_keys) + [gr.update(interactive=False)]
        values = dict(preset)
        values.update(preset.get("lora_values", {}))
        return [
            gr.update(value=values[key]) if key in values else gr.update()
            for key in preset_keys
        ] + [gr.update(interactive=True)]

    g["preset_dropdown"].change(
        fn=apply_preset,
        inputs=[g["preset_dropdown"], g["model"], g["source"]],
        outputs=preset_values + [g["preset_delete_btn"]],
    )

    g["preset_save_btn"].click(
        fn=lambda name: (gr.update(visible=True), gr.update(value=name or "")),
        inputs=[g["preset_dropdown"]],
        outputs=[g["preset_save_row"], g["preset_name"]],
    )
    g["preset_save_cancel"].click(
        fn=lambda: gr.update(visible=False), outputs=[g["preset_save_row"]]
    )

    def save_preset(name, model, source, *values):
        name = (name or "").strip()
        if not name:
            gr.Warning("Give the preset a name first.")
            return gr.update(), gr.update(visible=True)
        data = dict(zip(preset_keys, values))
        weights = {k: data.pop(k) for k in list(data) if k in g["lora_sliders"]}
        selected = data.get("lora_selector") or []
        data["lora_values"] = {k: v for k, v in weights.items() if k in selected}
        presets.save_preset(model, source, name, data)
        gr.Info(f"Saved preset “{name}”.")
        return (
            gr.update(choices=presets.list_presets(model, source), value=name),
            gr.update(visible=False),
        )

    g["preset_save_confirm"].click(
        fn=save_preset,
        inputs=[g["preset_name"], g["model"], g["source"]] + preset_values,
        outputs=[g["preset_dropdown"], g["preset_save_row"]],
    )

    g["preset_delete_btn"].click(
        fn=lambda name: (gr.update(visible=True), f"Delete the preset **{name}**?"),
        inputs=[g["preset_dropdown"]],
        outputs=[g["preset_delete_row"], g["preset_delete_text"]],
    )
    g["preset_delete_no"].click(
        fn=lambda: gr.update(visible=False), outputs=[g["preset_delete_row"]]
    )

    def delete_preset(name, model, source):
        if name:
            presets.delete_preset(model, source, name)
        return (
            gr.update(choices=presets.list_presets(model, source), value=None),
            gr.update(visible=False),
            gr.update(interactive=False),
        )

    g["preset_delete_yes"].click(
        fn=delete_preset,
        inputs=[g["preset_dropdown"], g["model"], g["source"]],
        outputs=[g["preset_dropdown"], g["preset_delete_row"], g["preset_delete_btn"]],
    )

    # ---- prompt helpers -----------------------------------------------------
    def enhance_wrapper(text):
        yield (
            gr.update(interactive=False),
            gr.update(visible=True),
            gr.update(interactive=False),
            gr.update(),
        )
        enhanced = enhance_prompt(text)
        yield (
            gr.update(interactive=True),
            gr.update(visible=False),
            gr.update(interactive=True),
            gr.update(value=enhanced) if enhanced else gr.update(),
        )

    g["enhance_btn"].click(
        fn=enhance_wrapper,
        inputs=[g["prompt"]],
        outputs=[
            g["enhance_btn"],
            g["stop_enhance_btn"],
            g["caption_btn"],
            g["prompt"],
        ],
    )
    g["stop_enhance_btn"].click(
        fn=stop_enhancing,
        outputs=[g["enhance_btn"], g["stop_enhance_btn"], g["caption_btn"]],
    )

    def caption_wrapper(img, text):
        if img is None:
            gr.Warning("Add a start frame to describe.")
            yield gr.update(), gr.update(), gr.update(), text
            return
        yield (
            gr.update(interactive=False),
            gr.update(interactive=False),
            gr.update(visible=True),
            gr.update(),
        )
        captioned = caption_image(img)
        yield (
            gr.update(interactive=True),
            gr.update(interactive=True),
            gr.update(visible=False),
            gr.update(value=captioned) if captioned else gr.update(),
        )

    g["caption_btn"].click(
        fn=caption_wrapper,
        inputs=[g["input_image"], g["prompt"]],
        outputs=[
            g["enhance_btn"],
            g["caption_btn"],
            g["stop_caption_btn"],
            g["prompt"],
        ],
    )
    g["stop_caption_btn"].click(
        fn=stop_captioning,
        outputs=[g["enhance_btn"], g["stop_caption_btn"], g["caption_btn"]],
    )

    # ---- re-roll banner -----------------------------------------------------
    def on_reroll_change(reroll):
        if not reroll:
            return gr.update(visible=False), ""
        return (
            gr.update(visible=True),
            f"**Re-rolling {reroll['label']}** from section {reroll['section']}. "
            "Earlier sections are kept; keep the model, size, length and section "
            "size the same as the original job.",
        )

    g["reroll_state"].change(
        fn=on_reroll_change,
        inputs=[g["reroll_state"]],
        outputs=[g["reroll_row"], g["reroll_text"]],
    )
    g["reroll_clear_btn"].click(fn=lambda: None, outputs=[g["reroll_state"]])

    # ---- add to queue -------------------------------------------------------
    job_inputs = {
        "model": g["model"],
        "source": g["source"],
        "input_image": g["input_image"],
        "input_video": g["input_video"],
        "end_frame_image": g["end_frame_image"],
        "end_frame_strength": g["end_frame_strength"],
        "prompt": g["prompt"],
        "n_prompt": g["n_prompt"],
        "seed": g["seed"],
        "randomize_seed": g["randomize_seed"],
        "total_second_length": g["total_second_length"],
        "latent_window_size": g["latent_window_size"],
        "steps": g["steps"],
        "cfg": g["cfg"],
        "gs": g["gs"],
        "rs": g["rs"],
        "cache_type": g["cache_type"],
        "teacache_num_steps": g["teacache_num_steps"],
        "teacache_rel_l1_thresh": g["teacache_rel_l1_thresh"],
        "magcache_threshold": g["magcache_threshold"],
        "magcache_max_consecutive_skips": g["magcache_max_consecutive_skips"],
        "magcache_retention_ratio": g["magcache_retention_ratio"],
        "blend_sections": g["blend_sections"],
        "latent_type": g["latent_type"],
        "lora_selector": g["lora_selector"],
        "resolutionW": g["resolutionW"],
        "resolutionH": g["resolutionH"],
        "combine_with_source": g["combine_with_source"],
        "num_cleaned_frames": g["num_cleaned_frames"],
        "motion_canvas": g["motion_canvas"],
        "camera": g["camera"],
        "camera_amount": g["camera_amount"],
        "flow_strength": g["flow_strength"],
        "motion_reference_video": g["motion_reference_video"],
        "motion_reference_strength": g["motion_reference_strength"],
        "motion_reference_start": g["motion_reference_start"],
        "reroll_state": g["reroll_state"],
        **{f"keyframe_image_{i}": c for i, c in enumerate(g["keyframe_images"])},
        **{f"keyframe_time_{i}": c for i, c in enumerate(g["keyframe_times"])},
    }
    job_input_names = list(job_inputs)
    job_input_components = list(job_inputs.values()) + g["lora_slider_list"]

    def submit_job(v, lora_values, image_override=None, seed_override=None):
        """Queue one job from the form values. Unsupported features are dropped here."""
        model, source = v["model"], v["source"]
        use = {
            feature: caps.supports(feature, model, source)
            for feature in caps.FEATURE_LABELS
        }
        end_image = v["end_frame_image"] if use["end_frame"] else None
        model_type = caps.to_legacy(model, source, end_image is not None)
        is_video = source == "Video"
        input_image = image_override if image_override is not None else v["input_image"]
        input_data = v["input_video"] if is_video else input_image

        keyframe_pairs = []
        if use["keyframes"]:
            for i in range(NUM_KEYFRAME_SLOTS):
                image, t = v[f"keyframe_image_{i}"], v[f"keyframe_time_{i}"]
                if image is not None and t is not None:
                    keyframe_pairs.append((image, float(t)))
        canvas = v["motion_canvas"] or {}
        arrows = (
            [tuple(a) for a in canvas.get("arrows") or []]
            if use["motion_sketch"]
            else []
        )
        camera = v["camera"] if use["motion_sketch"] else "None"
        reroll = v["reroll_state"] if use["reroll"] else None

        # LoRA weights in the stable slider order (see #388)
        lora_names = list(g["lora_sliders"].keys())
        seed = v["seed"] if seed_override is None else seed_override

        return f["process_fn"](
            caps.backend_model_type(model_type),
            input_data,
            end_image,
            v["end_frame_strength"] if end_image is not None else 1.0,
            v["prompt"],
            v["n_prompt"],
            seed,
            v["total_second_length"],
            v["latent_window_size"],
            v["steps"],
            v["cfg"],
            v["gs"],
            v["rs"],
            v["cache_type"] == "TeaCache",
            v["teacache_num_steps"],
            v["teacache_rel_l1_thresh"],
            v["cache_type"] == "MagCache",
            v["magcache_threshold"],
            v["magcache_max_consecutive_skips"],
            v["magcache_retention_ratio"],
            v["blend_sections"],
            v["latent_type"],
            settings.get("clean_up_videos", True),
            v["lora_selector"],
            v["resolutionW"],
            v["resolutionH"],
            v["input_video"] if is_video else None,
            v["combine_with_source"],
            v["num_cleaned_frames"],
            lora_names,
            *lora_values,
            save_section_latents=settings.get("save_section_latents", True),
            reroll_latents_path=(reroll or {}).get("path"),
            reroll_from_section=(reroll or {}).get("section"),
            keyframe_images=[image for image, _ in keyframe_pairs] or None,
            keyframe_times=[t for _, t in keyframe_pairs] or None,
            motion_reference_video=v["motion_reference_video"]
            if use["motion_reference"]
            else None,
            motion_reference_strength=v["motion_reference_strength"],
            motion_reference_start=v["motion_reference_start"] or 0.0,
            flow_noise_arrows=arrows or None,
            flow_noise_camera=camera,
            flow_noise_camera_amount=v["camera_amount"],
            flow_noise_strength=v["flow_strength"],
        )

    def split_values(values):
        named = dict(zip(job_input_names, values[: len(job_input_names)]))
        return named, list(values[len(job_input_names) :])

    def on_add(*values):
        v, lora_values = split_values(values)
        result = submit_job(v, lora_values)
        job_id = result[1] if result else None
        new_seed = random.randint(0, MAX_SEED) if v["randomize_seed"] else gr.update()
        if job_id:
            gr.Info("Added to the queue.")
        return (job_id or gr.update(), new_seed, *f["update_stats"]())

    g["start_button"].click(
        fn=on_add,
        inputs=job_input_components,
        outputs=[g["current_job_id"], g["seed"], *stats_outputs],
    )

    def on_add_batch(files, *values):
        v, lora_values = split_values(values)
        if not files:
            gr.Warning("Choose some images first.")
            return (gr.update(), *f["update_stats"]())
        seed = v["seed"]
        last_job = None
        for path in files:
            try:
                image = np.array(Image.open(path).convert("RGB"))
            except Exception as e:
                logger.error(f"Skipping batch image {path}: {e}")
                continue
            result = submit_job(
                v, lora_values, image_override=image, seed_override=seed
            )
            last_job = (result[1] if result else None) or last_job
            if v["randomize_seed"]:
                seed = random.randint(0, MAX_SEED)
        gr.Info(f"Added {len(files)} jobs to the queue.")
        return (last_job or gr.update(), *f["update_stats"]())

    g["add_batch_to_queue_btn"].click(
        fn=on_add_batch,
        inputs=[g["batch_input_images"]] + job_input_components,
        outputs=[g["current_job_id"], *stats_outputs],
    )

    # ---- running job --------------------------------------------------------
    monitor_outputs = [
        g["result_video"],
        g["preview_image"],
        g["progress_desc"],
        g["progress_bar"],
        g["end_button"],
    ]
    g["current_job_id"].change(
        fn=f["monitor_fn"],
        inputs=[g["current_job_id"]],
        outputs=monitor_outputs,
    ).then(fn=f["update_stats"], outputs=stats_outputs)

    def cancel_current():
        f["end_process_fn"]()
        return (gr.update(value="Cancelling…", interactive=False), *f["update_stats"]())

    g["end_button"].click(fn=cancel_current, outputs=[g["end_button"], *stats_outputs])

    return {
        "job_input_components": job_input_components,
        "refresh_timeline": refresh_timeline,
        "timeline_inputs": timeline_inputs,
        "assess": assess,
        "feature_inputs": feature_inputs,
        "on_setup_change": on_setup_change,
        "setup_outputs": setup_outputs,
        "canvas_value": canvas_value,
        "canvas_inputs": canvas_inputs,
    }


# ------------------------------------------------------------ restore settings


def restore_targets(g):
    """Components updated by settings_from_metadata, in order."""
    return [
        g["model"],
        g["source"],
        g["prompt"],
        g["n_prompt"],
        g["seed"],
        g["randomize_seed"],
        g["steps"],
        g["total_second_length"],
        g["end_frame_strength"],
        g["latent_window_size"],
        g["resolutionW"],
        g["resolutionH"],
        g["blend_sections"],
        g["cache_type"],
        g["magcache_threshold"],
        g["magcache_max_consecutive_skips"],
        g["magcache_retention_ratio"],
        g["teacache_num_steps"],
        g["teacache_rel_l1_thresh"],
        g["latent_type"],
        g["combine_with_source"],
        g["num_cleaned_frames"],
        g["gs"],
        g["cfg"],
        g["rs"],
        g["lora_selector"],
    ] + g["lora_slider_list"]


def settings_from_metadata(meta, lora_names):
    """Updates for restore_targets() from a job's metadata dict."""
    if isinstance(meta, str):
        meta = json.loads(meta)
    model, source = caps.from_legacy(
        meta.get("model_type") or meta.get("generation_type")
    )
    cache_type = meta.get("cache_type") or (
        "MagCache"
        if meta.get("use_magcache")
        else "TeaCache"
        if meta.get("use_teacache")
        else "None"
    )
    loras = meta.get("loras") or {}

    def val(key):
        value = meta.get(key)
        return gr.update() if value is None else gr.update(value=value)

    updates = [
        gr.update(value=model),
        gr.update(value=source),
        val("prompt"),
        val("negative_prompt"),
        val("seed"),
        gr.update(value=False),  # keep the seed that made this video
        val("steps"),
        val("total_second_length"),
        val("end_frame_strength"),
        val("latent_window_size"),
        val("resolutionW"),
        val("resolutionH"),
        val("blend_sections"),
        gr.update(value=cache_type),
        val("magcache_threshold"),
        val("magcache_max_consecutive_skips"),
        val("magcache_retention_ratio"),
        val("teacache_num_steps"),
        val("teacache_rel_l1_thresh"),
        val("latent_type"),
        val("combine_with_source"),
        val("num_cleaned_frames"),
        val("gs"),
        val("cfg"),
        val("rs"),
        gr.update(value=[name for name in loras if name in lora_names]),
    ]
    updates += [
        gr.update(value=loras[name], visible=True)
        if name in loras
        else gr.update(visible=False)
        for name in lora_names
    ]
    return updates


def apply_startup(settings, g):
    """Startup model/preset from Settings, as updates for [model, source, preset]."""
    startup = settings.get("startup_model_type", "None")
    if not startup or startup == "None":
        return gr.update(), gr.update(), gr.update()
    model, source = caps.from_legacy(startup)
    names = presets.list_presets(model, source)
    preset = settings.get("startup_preset_name")
    return (
        gr.update(value=model),
        gr.update(value=source),
        gr.update(choices=names, value=preset if preset in names else None),
    )
