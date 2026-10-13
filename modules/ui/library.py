"""
The Library tab: every video in the output folder, newest first.

Videos are grouped by job id straight from their file names, so a video
shows up whether or not its metadata was saved. From a selected video you
can reuse its settings, re-roll it from a section, add audio, open it in
Tools or delete it.
"""

import json
import logging
import os
import re
import time
from html import escape

import gradio as gr

from modules.pipelines import section_checkpoint
from modules.ui import capabilities as caps
from modules.ui import library_audio
from modules.ui.components.timeline import Timeline

logger = logging.getLogger(__name__)

# {job}_{frames}.mp4, {job}_combined.mp4, {job}_combined_v1.mp4
VIDEO_NAME = re.compile(r"^(?P<job>.+?)_(?P<tag>\d+|combined(?:_v\d+)?)\.mp4$")


def scan_outputs(output_dir):
    """{job_id: [video paths, best first]} for every video in output_dir."""
    jobs = {}
    if not os.path.isdir(output_dir):
        return jobs
    for name in os.listdir(output_dir):
        match = VIDEO_NAME.match(name)
        if not match:
            if name.endswith(".mp4"):
                jobs.setdefault(name[:-4], []).append(name)
            continue
        jobs.setdefault(match["job"], []).append(name)

    def rank(name):
        match = VIDEO_NAME.match(name)
        tag = match["tag"] if match else ""
        # combined (source + result) first, then the most frames
        return (0, tag) if tag.startswith("combined") else (1, -int(tag or 0))

    return {
        job: [os.path.join(output_dir, n) for n in sorted(names, key=rank)]
        for job, names in jobs.items()
    }


def _thumbnail(job_id, video_path, metadata_dir, cache_dir):
    png = os.path.join(metadata_dir, f"{job_id}.png")
    if os.path.exists(png):
        return png
    os.makedirs(cache_dir, exist_ok=True)
    thumb = os.path.join(cache_dir, f"{job_id}.jpg")
    if os.path.exists(thumb) and os.path.getmtime(thumb) >= os.path.getmtime(
        video_path
    ):
        return thumb
    try:
        import cv2

        capture = cv2.VideoCapture(video_path)
        ok, frame = capture.read()
        capture.release()
        if ok:
            cv2.imwrite(thumb, frame)
            return thumb
    except Exception as e:
        logger.debug(f"No thumbnail for {video_path}: {e}")
    return None


def list_library(settings, skip_jobs=()):
    """[(thumbnail, job_id)] newest first, plus {job_id: [videos]}.

    skip_jobs: ids still queued or running, whose partial videos aren't results yet.
    """
    output_dir = settings.get("output_dir")
    metadata_dir = settings.get("metadata_dir")
    cache_dir = os.path.join(settings.get("gradio_temp_dir"), "library_thumbs")
    jobs = {
        k: v for k, v in scan_outputs(output_dir).items() if k not in set(skip_jobs)
    }
    items = []
    for job_id, videos in jobs.items():
        newest = max(os.path.getmtime(v) for v in videos)
        thumb = _thumbnail(job_id, videos[0], metadata_dir, cache_dir)
        items.append((newest, thumb, job_id))
    items.sort(reverse=True)
    return [(thumb, job_id) for _, thumb, job_id in items if thumb], jobs


def load_metadata(settings, job_id):
    path = os.path.join(settings.get("metadata_dir"), f"{job_id}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Could not read {path}: {e}")
        return {}


def summary_html(job_id, video_path, meta):
    if not meta:
        return (
            "<div class='lib-summary'><p class='muted'>No saved settings for this "
            "video (metadata saving was off).</p></div>"
        )
    model, source = caps.from_legacy(
        meta.get("model_type") or meta.get("generation_type")
    )
    loras = meta.get("loras") or {}
    rows = [
        ("Model", model + (" · from video" if source == "Video" else "")),
        ("Size", f"{meta.get('resolutionW', '?')} × {meta.get('resolutionH', '?')}"),
        ("Length", f"{meta.get('total_second_length', '?')} s"),
        ("Seed", meta.get("seed", "?")),
        ("Steps", meta.get("steps", "?")),
        (
            "Cache",
            "MagCache"
            if meta.get("use_magcache")
            else "TeaCache"
            if meta.get("use_teacache")
            else "Off",
        ),
    ]
    if meta.get("end_frame_used") not in (None, False, "False"):
        rows.append(("End frame", f"influence {meta.get('end_frame_strength', 1.0)}"))
    if loras:
        rows.append(("LoRAs", ", ".join(f"{k} ({v})" for k, v in loras.items())))
    when = meta.get("timestamp")
    if when:
        rows.append(("Made", time.strftime("%Y-%m-%d %H:%M", time.localtime(when))))
    cells = "".join(
        f"<dt>{escape(str(k))}</dt><dd>{escape(str(v))}</dd>" for k, v in rows
    )
    prompt = escape(meta.get("prompt", ""))
    negative = escape(meta.get("negative_prompt", ""))
    neg_html = f"<p class='muted'>Not: {negative}</p>" if negative else ""
    return (
        f"<div class='lib-summary'><p class='lib-prompt'>{prompt}</p>{neg_html}"
        f"<dl>{cells}</dl></div>"
    )


def reroll_timeline(ckpt_path):
    """Selectable timeline for a job's section checkpoint, or None."""
    try:
        ckpt = section_checkpoint.load_summary(ckpt_path)
    except Exception as e:
        logger.debug(f"No usable checkpoint {ckpt_path}: {e}")
        return None
    ranges = section_checkpoint.section_time_ranges(ckpt)
    if not ranges:
        return None
    sections = [
        {"start": round(s, 2), "end": round(e, 2), "order": i + 1, "state": "normal"}
        for i, (s, e) in enumerate(ranges)
    ]
    sections.sort(key=lambda s: s["start"])
    backward = section_checkpoint.is_prepending_model(ckpt["model_type"])
    duration = max(s["end"] for s in sections)
    return {
        "duration": duration,
        "direction": "backward" if backward else "forward",
        "sections": sections,
        "prompts": [],
        "blend": 0,
        "frames": [],
        "lanes": [],
        "keyframes_enabled": False,
        "keyframes_reason": "",
        "selected_section": None,
        "selectable": True,
    }


def create_library_ui():
    selected_job = gr.State(None)
    job_order = gr.State([])
    job_videos = gr.State({})
    with gr.Row(equal_height=False, elem_id="library-root"):
        with gr.Column(scale=5, min_width=320):
            with gr.Row(elem_classes="toolbar-row"):
                library_count = gr.Markdown("", elem_classes="field-note")
                refresh_button = gr.Button("Refresh", size="sm", scale=0)
            gallery = gr.Gallery(
                columns=[4],
                allow_preview=False,
                object_fit="cover",
                height="auto",
                show_label=False,
                elem_id="library-gallery",
            )
            empty_note = gr.Markdown(
                "Nothing here yet. Finished videos appear here automatically.",
                visible=False,
                elem_classes="empty-state",
            )
        with gr.Column(scale=6, min_width=360, elem_id="library-detail"):
            nothing_selected = gr.Markdown(
                "Select a video to see its settings and what you can do with it.",
                elem_classes="empty-state",
            )
            with gr.Column(visible=False) as detail:
                video = gr.Video(
                    autoplay=True, loop=True, interactive=False, show_label=False
                )
                version = gr.Dropdown(label="Version", choices=[], visible=False)
                summary = gr.HTML("")
                with gr.Row(elem_classes="action-row"):
                    use_settings_btn = gr.Button(
                        "Use these settings", variant="primary"
                    )
                    send_to_tools_btn = gr.Button("Open in Tools")
                    delete_btn = gr.Button("Delete…", variant="stop")
                with gr.Row(visible=False, elem_classes="inline-form") as delete_row:
                    gr.Markdown(
                        "Delete this video, its other versions and its saved settings? "
                        "This can't be undone."
                    )
                    delete_yes = gr.Button("Delete", variant="stop", scale=0)
                    delete_no = gr.Button("Keep it", scale=0)
                with gr.Accordion(
                    "Re-roll from a section", open=False, visible=False
                ) as reroll_acc:
                    gr.Markdown(
                        "Click the section to regenerate from. Sections generated "
                        "before it are kept.",
                        elem_classes="field-note",
                    )
                    reroll_timeline_view = Timeline(show_label=False, interactive=True)
                    reroll_btn = gr.Button(
                        "Re-roll from the selected section", interactive=False
                    )
                    reroll_section = gr.State(None)
                    reroll_path = gr.State(None)
                with gr.Accordion("Audio", open=False) as audio_acc:
                    audio_model = gr.Dropdown(
                        label="Audio model",
                        choices=library_audio.AUDIO_MODELS,
                        value=library_audio.DEFAULT_AUDIO_MODEL,
                    )
                    audio_overwrite = gr.Checkbox(
                        label="Replace existing audio", visible=False
                    )
                    with gr.Row():
                        audio_prompt = gr.Textbox(label="Sound prompt", scale=4)
                        audio_prompt_append = gr.Checkbox(
                            label="Add to the video prompt", scale=1
                        )
                    audio_negative = gr.Textbox(
                        label="Avoid", value=library_audio.DEFAULT_AUDIO_NEGATIVE_PROMPT
                    )
                    with gr.Row():
                        audio_steps = gr.Slider(
                            label="Steps",
                            minimum=1,
                            maximum=100,
                            step=1,
                            value=library_audio.DEFAULT_AUDIO_STEPS,
                        )
                        audio_cfg = gr.Slider(
                            label="CFG strength",
                            minimum=1.0,
                            maximum=10.0,
                            step=0.1,
                            value=library_audio.DEFAULT_AUDIO_CFG,
                            info="How closely the audio follows the prompt",
                        )
                    with gr.Row():
                        audio_generate_btn = gr.Button(
                            "Generate audio", variant="primary"
                        )
                        audio_delete_btn = gr.Button("Remove audio…")
                    with gr.Row(
                        visible=False, elem_classes="inline-form"
                    ) as audio_delete_row:
                        gr.Markdown("Remove the audio track from this video file?")
                        audio_delete_yes = gr.Button("Remove", variant="stop", scale=0)
                        audio_delete_no = gr.Button("Keep it", scale=0)
                    audio_status = gr.Markdown("", elem_classes="field-note")
                with gr.Accordion("All saved settings", open=False):
                    raw_metadata = gr.JSON(show_label=False)
    return locals()


def connect_library_events(
    lib, create, create_api, tools_video, main_tabs, settings, lora_names, active_jobs
):
    from modules.ui.create import restore_targets, settings_from_metadata

    def refresh():
        items, jobs = list_library(settings, active_jobs())
        count = len(items)
        label = f"{count} video{'s' if count != 1 else ''}" if count else ""
        return (
            gr.update(value=[thumb for thumb, _ in items]),
            [job for _, job in items],
            jobs,
            label,
            gr.update(visible=not items),
        )

    refresh_outputs = [
        lib["gallery"],
        lib["job_order"],
        lib["job_videos"],
        lib["library_count"],
        lib["empty_note"],
    ]

    def select(order, jobs, evt: gr.SelectData):
        if evt.index is None or evt.index >= len(order):
            return [gr.update()] * 12
        job_id = order[evt.index]
        videos = jobs.get(job_id) or []
        if not videos:
            return [gr.update()] * 12
        meta = load_metadata(settings, job_id)
        ckpt = section_checkpoint.checkpoint_path(settings.get("output_dir"), job_id)
        timeline = reroll_timeline(ckpt) if os.path.exists(ckpt) else None
        return [
            job_id,
            gr.update(visible=False),  # nothing_selected
            gr.update(visible=True),  # detail
            videos[0],
            gr.update(
                choices=[(os.path.basename(v), v) for v in videos],
                value=videos[0],
                visible=len(videos) > 1,
            ),
            summary_html(job_id, videos[0], meta),
            meta or None,
            gr.update(interactive=bool(meta)),  # use settings
            gr.update(visible=timeline is not None, open=False),
            timeline,
            ckpt if timeline else None,
            gr.update(visible=library_audio.has_audio(videos[0]), value=False),
        ]

    lib["gallery"].select(
        fn=select,
        inputs=[lib["job_order"], lib["job_videos"]],
        outputs=[
            lib["selected_job"],
            lib["nothing_selected"],
            lib["detail"],
            lib["video"],
            lib["version"],
            lib["summary"],
            lib["raw_metadata"],
            lib["use_settings_btn"],
            lib["reroll_acc"],
            lib["reroll_timeline_view"],
            lib["reroll_path"],
            lib["audio_overwrite"],
        ],
    )
    lib["version"].input(
        fn=lambda v: v, inputs=[lib["version"]], outputs=[lib["video"]]
    )
    lib["refresh_button"].click(fn=refresh, outputs=refresh_outputs)

    # Use these settings -> Create
    targets = restore_targets(create)

    def use_settings(meta):
        if not meta:
            return [gr.update()] * len(targets) + [gr.update()]
        gr.Info("Settings loaded into Create.")
        return settings_from_metadata(meta, lora_names) + [
            gr.update(selected="create_tab")
        ]

    lib["use_settings_btn"].click(
        fn=use_settings,
        inputs=[lib["raw_metadata"]],
        outputs=targets + [main_tabs],
    ).then(
        fn=create_api["on_setup_change"],
        inputs=[create["model"], create["source"], create["preset_dropdown"]],
        outputs=create_api["setup_outputs"],
    )

    # Re-roll
    def pick_section(evt: gr.SelectData):
        value = evt.value or {}
        order = value.get("order")
        if order is None:
            return None, gr.update(interactive=False)
        return order, gr.update(value=f"Re-roll from section {order}", interactive=True)

    lib["reroll_timeline_view"].select(
        fn=pick_section, outputs=[lib["reroll_section"], lib["reroll_btn"]]
    )

    def start_reroll(job_id, path, section, meta):
        if not (path and section):
            return [gr.update()] * (len(targets) + 2)
        updates = (
            settings_from_metadata(meta, lora_names)
            if meta
            else [gr.update()] * len(targets)
        )
        state = {"path": path, "section": int(section), "label": f"job {job_id[:8]}"}
        gr.Info(
            "Re-roll set up in Create. Change the prompt or seed, then add it to the queue."
        )
        return updates + [state, gr.update(selected="create_tab")]

    lib["reroll_btn"].click(
        fn=start_reroll,
        inputs=[
            lib["selected_job"],
            lib["reroll_path"],
            lib["reroll_section"],
            lib["raw_metadata"],
        ],
        outputs=targets + [create["reroll_state"], main_tabs],
    ).then(
        fn=create_api["on_setup_change"],
        inputs=[create["model"], create["source"], create["preset_dropdown"]],
        outputs=create_api["setup_outputs"],
    )

    # Tools
    lib["send_to_tools_btn"].click(
        fn=lambda path: (gr.update(value=path), gr.update(selected="tools_tab")),
        inputs=[lib["video"]],
        outputs=[tools_video, main_tabs],
    )

    # Delete
    lib["delete_btn"].click(
        fn=lambda: gr.update(visible=True), outputs=[lib["delete_row"]]
    )
    lib["delete_no"].click(
        fn=lambda: gr.update(visible=False), outputs=[lib["delete_row"]]
    )

    def delete(job_id, jobs):
        if not job_id:
            return [gr.update()] * (len(refresh_outputs) + 3)
        removed = 0
        for path in jobs.get(job_id, []):
            try:
                os.remove(path)
                removed += 1
            except OSError as e:
                logger.error(f"Could not delete {path}: {e}")
        for ext in (".json", ".png"):
            path = os.path.join(settings.get("metadata_dir"), f"{job_id}{ext}")
            if os.path.exists(path):
                os.remove(path)
        gr.Info(f"Deleted {removed} video file{'s' if removed != 1 else ''}.")
        return [
            *refresh(),
            gr.update(visible=False),  # delete_row
            gr.update(visible=False),  # detail
            gr.update(visible=True),  # nothing_selected
        ]

    lib["delete_yes"].click(
        fn=delete,
        inputs=[lib["selected_job"], lib["job_videos"]],
        outputs=refresh_outputs
        + [lib["delete_row"], lib["detail"], lib["nothing_selected"]],
    )

    # Audio
    def generate_audio(
        video_path, meta, model_name, overwrite, prompt, negative, append_p, steps, cfg
    ):
        if not video_path:
            return gr.update(), "Select a video first."
        try:
            status = library_audio.generate_audio(
                video_path,
                meta or {},
                model_name,
                overwrite,
                prompt,
                negative,
                append_p,
                steps,
                cfg,
            )
        except Exception as e:
            logger.exception("Audio generation failed")
            return gr.update(), f"Audio generation failed: {e}"
        # Same path, new contents: clear first so the player reloads it
        return gr.update(value=video_path), status

    lib["audio_generate_btn"].click(
        fn=lambda: "Generating audio… this can take a minute.",
        outputs=[lib["audio_status"]],
    ).then(
        fn=generate_audio,
        inputs=[
            lib["video"],
            lib["raw_metadata"],
            lib["audio_model"],
            lib["audio_overwrite"],
            lib["audio_prompt"],
            lib["audio_negative"],
            lib["audio_prompt_append"],
            lib["audio_steps"],
            lib["audio_cfg"],
        ],
        outputs=[lib["video"], lib["audio_status"]],
    ).then(
        fn=lambda path: gr.update(
            visible=bool(path) and library_audio.has_audio(path), value=False
        ),
        inputs=[lib["video"]],
        outputs=[lib["audio_overwrite"]],
    )

    def remove_audio(video_path):
        if not video_path:
            return gr.update(), "Select a video first."
        return gr.update(value=video_path), library_audio.delete_audio(video_path)

    lib["audio_delete_btn"].click(
        fn=lambda: gr.update(visible=True), outputs=[lib["audio_delete_row"]]
    )
    lib["audio_delete_no"].click(
        fn=lambda: gr.update(visible=False), outputs=[lib["audio_delete_row"]]
    )
    lib["audio_delete_yes"].click(
        fn=remove_audio,
        inputs=[lib["video"]],
        outputs=[lib["video"], lib["audio_status"]],
    ).then(fn=lambda: gr.update(visible=False), outputs=[lib["audio_delete_row"]])

    return refresh, refresh_outputs
