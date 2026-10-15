"""
The app shell: header, the five tabs, and the status that ties them together.

Create makes jobs, Queue runs them, Library holds the results, Tools edits
them and Settings configures the app. One update_stats() feeds every status
view (header pill, queue list, the "up next" rail on Create).
"""

import logging
from html import escape

import gradio as gr

from diffusers_helper.gradio.progress_bar import make_progress_bar_css
from modules import DUMMY_LORA_NAME
from modules.toolbox_app import (
    tb_create_video_toolbox_ui,
    tb_get_formatted_toolbar_stats,
    tb_processor,
)
from modules.ui.create import (
    apply_startup,
    connect_create_events,
    create_create_ui,
    render_up_next,
)
from modules.ui.library import connect_library_events, create_library_ui
from modules.ui.queue import (
    connect_queue_events,
    create_queue_ui,
    update_queue_status_with_thumbnails,
)
from modules.ui.settings import connect_settings_events, create_settings_ui
from modules.ui.timeline_model import apply_progress, job_direction
from modules.version import APP_VERSION_DISPLAY
from modules.video_queue import JobStatus

logger = logging.getLogger(__name__)

STATS_HTML = """
<div id="toolbar-stats-container" class="sys-stats">
  <div class="stat-card ram"><span class="stat-label">RAM</span><span class="stat-value"></span><div class="stat-bar"><span class="fill"></span></div></div>
  <div class="stat-card vram"><span class="stat-label">VRAM</span><span class="stat-value"></span><div class="stat-bar"><span class="fill"></span></div></div>
  <div class="stat-card gpu"><span class="stat-label">GPU</span><span class="stat-value"></span><div class="stat-bar"><span class="fill"></span></div></div>
</div>
"""


# Discord's logo mark (Simple Icons), drawn in the current text colour
DISCORD_ICON = (
    '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" '
    'aria-hidden="true"><path d="'
    "M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00"
    "-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68"
    "-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 "
    "00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-."
    "0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00"
    ".0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 "
    "0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 "
    "00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0"
    " 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 0"
    "1.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01"
    ".0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276"
    " 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604"
    ".698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.606"
    "7 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.1"
    "77-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 1"
    "5.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189"
    " 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555"
    " 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2"
    ".419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2"
    ".1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z"
    '"/></svg>'
)


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _status_pill(running, pending, finished):
    if running:
        text = "Running" + (f" · {pending} waiting" if pending else "")
        state = "running"
    elif pending:
        text, state = f"{pending} waiting", "waiting"
    else:
        text = "Idle" + (f" · {finished} done" if finished else "")
        state = "idle"
    return f"<div class='status-pill {state}'><span class='dot'></span>{escape(text)}</div>"


def create_interface(
    process_fn,
    monitor_fn,
    end_process_fn,
    update_queue_status_fn,
    load_lora_file_fn,
    job_queue,
    settings,
    default_prompt: str = "[1s: The person waves hello] [3s: The person jumps up and down] [5s: The person does a dance]",
    lora_names: list = [],
    lora_values: list = [],
    enumerate_lora_dir_fn=None,
):
    css = make_progress_bar_css() + _read("modules/ui/styles.css")
    head = (
        f"<script>{_read('modules/ui/queue_actions.js')}</script>"
        f"<script>{_read('modules/ui/timeline_sync.js')}</script>"
    )

    def counts():
        jobs = job_queue.get_all_jobs()
        running = sum(
            j.status in (JobStatus.RUNNING, JobStatus.CANCELLING) for j in jobs
        )
        pending = sum(j.status == JobStatus.PENDING for j in jobs)
        finished = sum(
            j.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
            for j in jobs
        )
        return jobs, running, pending, finished

    def update_stats(*_):
        queue_html = update_queue_status_with_thumbnails()
        jobs, running, pending, finished = counts()
        summary = (
            f"{running} running · {pending} waiting · {finished} finished"
            if jobs
            else ""
        )
        return (
            queue_html,
            _status_pill(running, pending, finished),
            render_up_next(jobs, job_queue.current_job),
            summary,
        )

    last_signature = {"value": None}

    def poll_stats():
        """Timer tick: only re-render when something changed or a job is running."""
        jobs, running, _, _ = counts()
        signature = tuple((j.id, j.status, j.result) for j in jobs)
        if signature == last_signature["value"] and not running:
            return (gr.update(),) * 4
        last_signature["value"] = signature
        return update_stats()

    def follow_current_job():
        """If a job is running (e.g. after a page reload), attach the live preview."""
        with job_queue.lock:
            job = job_queue.current_job
            return job.id if job else gr.update()

    current_theme = settings.get("gradio_theme", "default")
    block = gr.Blocks(
        css=css, head=head, title="FramePack Studio", theme=current_theme
    ).queue()

    with block:
        with gr.Row(elem_id="app-header", equal_height=True):
            gr.HTML(
                f"<div class='brand'><span class='brand-name'>FramePack Studio</span>"
                f"<span class='brand-version'>{APP_VERSION_DISPLAY}</span></div>",
                elem_classes="header-brand",
            )
            header_status = gr.HTML(_status_pill(0, 0, 0), elem_classes="header-status")
            gr.HTML(STATS_HTML, elem_classes="header-stats")
            toolbar_stats_vars = gr.HTML("", elem_id="toolbar-stats-vars-wrapper")
            gr.HTML(
                "<div class='header-links'>"
                "<a href='https://discord.com/invite/MtuM7gFJ3V' target='_blank'"
                f" title='Discord' aria-label='Discord'>{DISCORD_ICON}</a>"
                "</div>",
                elem_classes="header-links-wrap",
            )

        with gr.Tabs(elem_id="main_tabs") as main_tabs:
            with gr.Tab("Create", id="create_tab"):
                g = create_create_ui(
                    lora_names, default_prompt, DUMMY_LORA_NAME, settings
                )
            with gr.Tab("Queue", id="queue_tab"):
                q = create_queue_ui()
            with gr.Tab("Library", id="library_tab"):
                lib = create_library_ui()
            with gr.Tab("Tools", id="tools_tab"):
                _, tools_video_input = tb_create_video_toolbox_ui()
            with gr.Tab("Settings", id="settings_tab"):
                s = create_settings_ui(settings)

        stats_outputs = [
            q["queue_status"],
            header_status,
            g["up_next"],
            q["queue_summary"],
        ]
        f = {
            "process_fn": process_fn,
            "monitor_fn": monitor_fn,
            "end_process_fn": end_process_fn,
            "update_stats": update_stats,
            "stats_outputs": stats_outputs,
            "follow_current_job": follow_current_job,
            "follow_outputs": [g["current_job_id"]],
        }

        create_api = connect_create_events(g, f, settings, DUMMY_LORA_NAME)
        connect_queue_events(q, f, job_queue)

        def active_jobs():
            return {
                j.id
                for j in job_queue.get_all_jobs()
                if j.status
                in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.CANCELLING)
            }

        library_refresh, library_outputs = connect_library_events(
            lib,
            g,
            create_api,
            tools_video_input,
            main_tabs,
            settings,
            lora_names,
            active_jobs,
        )
        connect_settings_events(s, settings, tb_processor)

        def refresh_loras(current):
            if not enumerate_lora_dir_fn:
                return gr.update()
            names = enumerate_lora_dir_fn()
            return gr.update(
                choices=names, value=[n for n in current or [] if n in names]
            )

        g["refresh_loras_button"].click(
            fn=refresh_loras, inputs=[g["lora_selector"]], outputs=[g["lora_selector"]]
        )

        # Library refreshes whenever it is opened and when a job finishes
        def on_tab_select(evt: gr.SelectData):
            if evt.value == "Library":
                return library_refresh()
            return [gr.update()] * len(library_outputs)

        main_tabs.select(
            fn=on_tab_select, outputs=library_outputs, show_progress="hidden"
        )

        # ...and when the set of finished jobs changes, not on every new section
        finished_seen = {"ids": None}

        def poll_library():
            finished = frozenset(
                j.id
                for j in job_queue.get_all_jobs()
                if j.status
                in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
            )
            if finished == finished_seen["ids"]:
                return [gr.update()] * len(library_outputs)
            finished_seen["ids"] = finished
            return library_refresh()

        timer = gr.Timer(2, active=True)
        timer.tick(fn=tb_get_formatted_toolbar_stats, outputs=[toolbar_stats_vars])
        timer.tick(fn=poll_stats, outputs=stats_outputs, show_progress="hidden")
        timer.tick(fn=poll_library, outputs=library_outputs, show_progress="hidden")

        def timeline_progress(value):
            # Show which section the running job is on in the Create timeline
            with job_queue.lock:
                job = job_queue.current_job
                running = job is not None and job.status == JobStatus.RUNNING
                progress = (job.progress_data or {}) if running else {}
                model_type = (job.params or {}).get("model_type") if running else None
            marked = apply_progress(
                value,
                progress.get("section"),
                progress.get("sections"),
                job_direction(model_type),
            )
            return gr.update() if marked is None else marked

        timer.tick(
            fn=timeline_progress,
            inputs=[g["timeline"]],
            outputs=[g["timeline"]],
            show_progress="hidden",
        )

        # Startup: attach to a running job, apply the startup model/preset,
        # then bring every derived view (motion gating, timeline, checks) in line.
        block.load(fn=follow_current_job, outputs=[g["current_job_id"]]).then(
            fn=update_stats, outputs=stats_outputs
        ).then(
            fn=library_refresh, outputs=library_outputs, show_progress="hidden"
        ).then(
            fn=lambda: apply_startup(settings, g),
            outputs=[g["model"], g["source"], g["preset_dropdown"]],
        ).then(
            fn=create_api["on_setup_change"],
            inputs=[g["model"], g["source"], g["preset_dropdown"]],
            outputs=create_api["setup_outputs"],
        ).then(
            fn=create_api["canvas_value"],
            inputs=create_api["canvas_inputs"],
            outputs=[g["motion_canvas"]],
        ).then(
            fn=create_api["refresh_timeline"],
            inputs=create_api["timeline_inputs"],
            outputs=[g["timeline"]],
        ).then(
            fn=create_api["assess"],
            inputs=create_api["feature_inputs"],
            outputs=[g["checks"], g["start_button"]],
        )

    return block
