import gradio as gr
import time
import logging
import json
from modules.video_queue import JobStatus
from modules.ui.template_loader import (
    render_thumbnail_html,
    render_queue_row,
    render_queue,
)

logger = logging.getLogger(__name__)


def format_queue_status(jobs):
    """Format queue status with custom HTML templates."""

    rows = []
    for job in jobs:
        elapsed_time = ""
        if job.started_at:
            end_time = job.completed_at or time.time()
            elapsed_seconds = end_time - job.started_at
            elapsed_time = f"{elapsed_seconds:.2f}s"

        # Get job data
        generation_type = getattr(job, "generation_type", "Original")
        thumbnail = getattr(job, "thumbnail", None)
        thumbnail_html = render_thumbnail_html(thumbnail)

        # Get job settings from job.params (where JSON data is actually stored)
        width = job.params.get("resolutionW", 512) if hasattr(job, "params") else 512
        height = job.params.get("resolutionH", 512) if hasattr(job, "params") else 512
        size = f"{width}×{height}"

        # Get video length from total_second_length (already in seconds)
        total_seconds = (
            job.params.get("total_second_length", 6) if hasattr(job, "params") else 6
        )
        length = f"{total_seconds}s" if total_seconds else "N/A"

        # Get seed from params
        seed = job.params.get("seed", "Random") if hasattr(job, "params") else "Random"

        # Get prompt from params
        prompt = job.params.get("prompt_text", "") if hasattr(job, "params") else ""

        # Get all job data for changed settings detection from job.params
        params = job.params if hasattr(job, "params") else {}
        job_data = {
            "prompt": prompt,
            "negative_prompt": params.get("n_prompt", ""),
            "seed": seed,
            "steps": params.get("steps", 25),
            "cfg": params.get("cfg", 1.0),
            "gs": params.get("gs", 10),
            "rs": params.get("rs", 0),
            "latent_type": params.get("latent_type", "Noise"),
            "latent_window_size": params.get("latent_window_size", 9),
            "resolutionW": params.get("resolutionW", 512),
            "resolutionH": params.get("resolutionH", 512),
            "model_type": params.get("model_type", generation_type),
            "generation_type": params.get("model_type", generation_type),
            "total_second_length": params.get("total_second_length", 6),
            "blend_sections": params.get("blend_sections", 4),
            "num_cleaned_frames": params.get("num_cleaned_frames", 0),
            "end_frame_strength": params.get("end_frame_strength", 1.0),
            "end_frame_image_path": params.get("end_frame_image_path", None),
            "end_frame_used": params.get("end_frame_used", "False"),
            "input_video": params.get("input_video", None),
            "video_path": params.get("video_path", None),
            "x_param": params.get("x_param", None),
            "y_param": params.get("y_param", None),
            "x_values": params.get("x_values", None),
            "y_values": params.get("y_values", None),
            "combine_with_source": params.get("combine_with_source", True),
            "use_teacache": params.get("use_teacache", False),
            "teacache_num_steps": params.get("teacache_num_steps", 25),
            "teacache_rel_l1_thresh": params.get("teacache_rel_l1_thresh", 0.15),
            "use_magcache": params.get("use_magcache", True),
            "magcache_threshold": params.get("magcache_threshold", 0.1),
            "magcache_max_consecutive_skips": params.get(
                "magcache_max_consecutive_skips", 2
            ),
            "magcache_retention_ratio": params.get("magcache_retention_ratio", 0.25),
            "loras": params.get("loras", {}),
        }

        # Render each row using the template
        row_html = render_queue_row(
            job_id=job.id[:6] + "...",
            job_id_full=job.id,
            generation_type=generation_type,
            status=job.status.value,
            prompt_text=prompt,
            size=size,
            length=length,
            seed=str(seed),
            started=time.strftime("%H:%M:%S", time.localtime(job.started_at))
            if job.started_at
            else "--",
            completed=time.strftime("%H:%M:%S", time.localtime(job.completed_at))
            if job.completed_at
            else "--",
            elapsed=elapsed_time or "--",
            thumbnail=thumbnail_html,
            job_data=job_data,
            error=job.error if job.status == JobStatus.FAILED else "",
        )
        rows.append(row_html)

    # Render the complete queue
    return render_queue(rows)


def update_queue_status_with_thumbnails():
    try:
        from __main__ import job_queue

        jobs = job_queue.get_all_jobs()
        for job in jobs:
            if job.status == JobStatus.PENDING:
                job.queue_position = job_queue.get_queue_position(job.id)
        current = job_queue.current_job
        if current is not None and current.status == JobStatus.PENDING:
            # Only a job that's just been picked up is promoted. The queue
            # thread marks it finished before it clears current_job, so a
            # finished job must not be flipped back to running here.
            current.status = JobStatus.RUNNING

        # Sort jobs according to the requested priority:
        # 1. Running and Cancelling items first (same job transitioning states)
        # 2. Queued (pending) items in ascending order by created_at
        # 3. Editing items (future feature)
        # 4. Completed, Failed, and Cancelled items in descending order by completed_at
        def sort_key(job):
            if job.status in [JobStatus.RUNNING, JobStatus.CANCELLING]:
                return (
                    0,
                    job.created_at,
                )  # Running/Cancelling items first (same priority - never coexist)
            elif job.status == JobStatus.PENDING:
                # Sort by order number if available, otherwise fall back to created_at
                return (
                    1,
                    job.order_number
                    if job.order_number is not None
                    else job.created_at,
                )
            elif job.status == JobStatus.EDITING:
                return (
                    2,
                    job.created_at,
                )  # Editing items third, ordered by creation time
            else:  # COMPLETED, FAILED, CANCELLED
                # Use completed_at if available, otherwise use created_at, with descending order
                timestamp = job.completed_at if job.completed_at else job.created_at
                return (
                    3,
                    -timestamp,
                )  # Completed/Failed/Cancelled items last, descending order

        jobs.sort(key=sort_key)

        return format_queue_status(jobs)
    except ImportError:
        logging.error(
            "Error: Could not import job_queue. Queue status update might fail."
        )
        return []
    except Exception as e:
        logging.error(f"Error updating queue status: {e}")
        return []


def create_queue_ui():
    with gr.Column(elem_id="queue-root"):
        with gr.Row(elem_classes="toolbar-row") as queue_controls_row:
            queue_summary = gr.Markdown("", elem_classes="field-note")
            load_queue_button = gr.Button("Resume saved queue", size="sm", scale=0)
            clear_complete_button = gr.Button("Clear finished", size="sm", scale=0)
            clear_queue_button = gr.Button(
                "Cancel all waiting…", size="sm", variant="stop", scale=0
            )
        with gr.Row(visible=False, elem_classes="inline-form") as confirm_cancel_row:
            gr.Markdown("Cancel every job that's waiting? The running job keeps going.")
            confirm_cancel_yes_btn = gr.Button("Cancel them", variant="stop", scale=0)
            confirm_cancel_no_btn = gr.Button("Keep them", scale=0)
        queue_status = gr.HTML(render_queue([]), elem_id="queue-list")
        # Bridge for the per-row buttons (see queue_actions.js). Hidden with CSS,
        # not visible=False, so the elements stay in the page.
        queue_action_input = gr.Textbox(
            elem_id="queue-action-input", elem_classes="bridge", show_label=False
        )
        queue_action_trigger = gr.Button(
            "Queue action", elem_id="queue-action-trigger", elem_classes="bridge"
        )
        with gr.Accordion("Import or export a queue", open=False):
            gr.Markdown(
                "Export saves every job and its input images to a zip in the "
                "output folder. Import adds the jobs from a saved .json or .zip.",
                elem_classes="field-note",
            )
            with gr.Row():
                queue_export_button = gr.Button("Export queue", scale=0)
                import_queue_file = gr.File(
                    label="Import queue",
                    file_types=[".json", ".zip"],
                    type="filepath",
                    height=90,
                )
    return {
        "queue_status": queue_status,
        "queue_summary": queue_summary,
        "load_queue_button": load_queue_button,
        "queue_export_button": queue_export_button,
        "clear_complete_button": clear_complete_button,
        "clear_queue_button": clear_queue_button,
        "import_queue_file": import_queue_file,
        "queue_controls_row": queue_controls_row,
        "confirm_cancel_row": confirm_cancel_row,
        "confirm_cancel_yes_btn": confirm_cancel_yes_btn,
        "confirm_cancel_no_btn": confirm_cancel_no_btn,
        "queue_action_input": queue_action_input,
        "queue_action_trigger": queue_action_trigger,
    }


def connect_queue_events(q, f, job_queue):
    stats_outputs = f["stats_outputs"]

    def run(action):
        def handler(*args):
            action(*args)
            return f["update_stats"]()

        return handler

    def handle_queue_action(action_json):
        """Per-row cancel/remove from the queue HTML: {"action", "job_id"}."""
        try:
            data = json.loads(action_json) if action_json else {}
            action, job_id = data.get("action"), data.get("job_id")
            if action == "cancel" and job_id:
                job_queue.cancel_job(job_id)
            elif action == "remove" and job_id:
                job_queue.remove_job(job_id)
        except Exception as e:
            logging.error(f"Queue action error: {e}")
        return f["update_stats"]()

    q["queue_action_trigger"].click(
        fn=handle_queue_action, inputs=[q["queue_action_input"]], outputs=stats_outputs
    )
    q["clear_queue_button"].click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        outputs=[q["queue_controls_row"], q["confirm_cancel_row"]],
    )
    q["confirm_cancel_no_btn"].click(
        fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
        outputs=[q["queue_controls_row"], q["confirm_cancel_row"]],
    )
    q["confirm_cancel_yes_btn"].click(
        fn=run(lambda: job_queue.clear_queue()), outputs=stats_outputs
    ).then(
        fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
        outputs=[q["queue_controls_row"], q["confirm_cancel_row"]],
    )
    q["clear_complete_button"].click(
        fn=run(lambda: job_queue.clear_completed_jobs()), outputs=stats_outputs
    )

    def export_queue():
        path = job_queue.export_queue_to_zip()
        if path:
            gr.Info(f"Queue exported to {path}")
        return f["update_stats"]()

    q["queue_export_button"].click(fn=export_queue, outputs=stats_outputs)
    q["load_queue_button"].click(
        fn=run(lambda: job_queue.load_queue_from_json()), outputs=stats_outputs
    ).then(fn=f["follow_current_job"], outputs=f["follow_outputs"])

    def import_queue(path):
        if path:
            job_queue.load_queue_from_json(path)
        return f["update_stats"]()

    q["import_queue_file"].upload(
        fn=import_queue, inputs=[q["import_queue_file"]], outputs=stats_outputs
    ).then(fn=f["follow_current_job"], outputs=f["follow_outputs"])
