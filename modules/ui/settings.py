"""
The Settings tab. Every change saves immediately.

Each control is listed against the settings key it writes, so a control can
never save under the wrong name (the old tab saved the startup model, preset
and theme under their component names, so those settings never applied).
"""

import gradio as gr

from modules.ui import presets
from shared import LoraLoader, QuantizationFormat

BUILT_IN_THEMES = [
    "default",
    "base",
    "soft",
    "glass",
    "monochrome",
    "origin",
    "citrus",
    "ocean",
]

STARTUP_CHOICES = [
    ("Nothing — use the defaults", "None"),
    ("Original", "Original"),
    ("F1", "F1"),
    ("Original, from a video", "Video"),
    ("F1, from a video", "Video F1"),
]


def create_settings_ui(settings):
    theme = settings.get("gradio_theme", "default")
    themes = BUILT_IN_THEMES + ([theme] if theme not in BUILT_IN_THEMES else [])
    startup_model = settings.get("startup_model_type", "None")
    startup_presets = (
        presets.load_presets(startup_model) if startup_model != "None" else []
    )

    with gr.Column(elem_id="settings-root"):
        status = gr.Markdown("Changes save automatically.", elem_classes="field-note")
        with gr.Row(equal_height=False):
            with gr.Column():
                with gr.Group(elem_classes="settings-card"):
                    gr.Markdown("### Files", elem_classes="section-title")
                    output_dir = gr.Textbox(
                        label="Output folder",
                        value=settings.get("output_dir"),
                        max_lines=1,
                    )
                    metadata_dir = gr.Textbox(
                        label="Settings & thumbnails folder",
                        value=settings.get("metadata_dir"),
                        max_lines=1,
                    )
                    lora_dir = gr.Textbox(
                        label="LoRA folder", value=settings.get("lora_dir"), max_lines=1
                    )
                    gradio_temp_dir = gr.Textbox(
                        label="Temporary folder",
                        value=settings.get("gradio_temp_dir"),
                        max_lines=1,
                    )
                    save_metadata = gr.Checkbox(
                        label="Save each job's settings next to the video",
                        value=settings.get("save_metadata", True),
                        info="Needed for “Use these settings” in the Library.",
                    )
                    save_section_latents = gr.Checkbox(
                        label="Save section data for re-roll",
                        value=settings.get("save_section_latents", True),
                        info="A few MB per job. Needed to re-roll a job from a section later.",
                    )
                    clean_up_videos = gr.Checkbox(
                        label="Keep only the final video",
                        value=settings.get("clean_up_videos", True),
                        info="Deletes the in-progress versions once a job finishes.",
                    )
                    auto_cleanup_on_startup = gr.Checkbox(
                        label="Empty the temporary folder on startup",
                        value=settings.get("auto_cleanup_on_startup", False),
                    )
                    with gr.Row():
                        cleanup_btn = gr.Button(
                            "Empty temporary folder now", size="sm", scale=0
                        )
                        cleanup_output = gr.Markdown("", elem_classes="field-note")
                with gr.Group(elem_classes="settings-card"):
                    gr.Markdown("### Video files", elem_classes="section-title")
                    mp4_crf = gr.Slider(
                        label="MP4 compression (CRF)",
                        minimum=0,
                        maximum=100,
                        step=1,
                        value=settings.get("mp4_crf", 16),
                        info="Lower is higher quality and larger files. If videos come "
                        "out black, try 16.",
                    )
            with gr.Column():
                with gr.Group(elem_classes="settings-card"):
                    gr.Markdown("### When the app starts", elem_classes="section-title")
                    startup_model_type = gr.Dropdown(
                        label="Open Create with",
                        choices=STARTUP_CHOICES,
                        value=startup_model,
                    )
                    startup_preset_name = gr.Dropdown(
                        label="and this preset",
                        choices=startup_presets,
                        value=settings.get("startup_preset_name")
                        if settings.get("startup_preset_name") in startup_presets
                        else None,
                    )
                    gradio_theme = gr.Dropdown(
                        label="Theme",
                        choices=themes,
                        value=theme,
                        info="Takes effect after a restart.",
                    )
                with gr.Group(elem_classes="settings-card"):
                    gr.Markdown("### Memory & speed", elem_classes="section-title")
                    gpu_memory_preservation = gr.Slider(
                        label="VRAM to keep free (GB)",
                        minimum=1,
                        maximum=128,
                        step=0.1,
                        value=settings.get("gpu_memory_preservation", 6),
                        info="Raise it (1 GB at a time) if the computer freezes or steps "
                        "crawl. Lower is faster. 5.5–8.5 is common.",
                    )
                    reuse_model_instance = gr.Checkbox(
                        label="Keep the model loaded between jobs",
                        value=settings.get("reuse_model_instance", False),
                        info="Skips reloading when the model and LoRAs don't change.",
                    )
                    quantization_format = gr.Dropdown(
                        label="Weight format",
                        choices=[q.value for q in QuantizationFormat],
                        value=settings.quantization_format.value,
                        info="bf16 is the default and doesn't quantize. NF4 uses less "
                        "memory. int8 doesn't work with FramePack's memory management.",
                    )
                    vram_mode_setting = gr.Dropdown(
                        label="VRAM mode (restart to apply)",
                        choices=["auto", "high", "medium", "low"],
                        value=settings.get("vram_mode", "auto"),
                        info="Medium keeps the model on the GPU in fp8 (needs about "
                        "20 GB free) and is much faster than low. Auto picks from "
                        "the free VRAM.",
                    )
                    offload_engine = gr.Dropdown(
                        label="Low VRAM offload (applies when the model next loads)",
                        choices=["legacy", "streamed"],
                        value=settings.get("offload_engine", "legacy"),
                        info="How low mode moves the model in from system RAM. "
                        "Streamed copies whole blocks ahead of time from pinned "
                        "memory; it needs bf16 or float8_storage.",
                    )
                    lora_loader = gr.Dropdown(
                        label="LoRA loader",
                        choices=[loader.value for loader in LoraLoader],
                        value=settings.lora_loader.value,
                        info="diffusers for Diffusers-format LoRAs, lora_ready for Kohya-ss.",
                    )
                with gr.Accordion("Text encoder system prompt", open=False):
                    override_system_prompt = gr.Checkbox(
                        label="Use my own system prompt",
                        value=settings.get("override_system_prompt", False),
                    )
                    system_prompt_template = gr.Textbox(
                        label="System prompt template",
                        value=settings.get("system_prompt_template"),
                        lines=8,
                        info="A JSON or Python dict with 'template' and 'crop_start' keys.",
                    )
                    reset_system_prompt_btn = gr.Button("Reset to default", size="sm")

    controls = {
        "output_dir": output_dir,
        "metadata_dir": metadata_dir,
        "lora_dir": lora_dir,
        "gradio_temp_dir": gradio_temp_dir,
        "save_metadata": save_metadata,
        "save_section_latents": save_section_latents,
        "clean_up_videos": clean_up_videos,
        "auto_cleanup_on_startup": auto_cleanup_on_startup,
        "mp4_crf": mp4_crf,
        "startup_model_type": startup_model_type,
        "startup_preset_name": startup_preset_name,
        "gradio_theme": gradio_theme,
        "gpu_memory_preservation": gpu_memory_preservation,
        "reuse_model_instance": reuse_model_instance,
        "quantization_format": quantization_format,
        "vram_mode": vram_mode_setting,
        "offload_engine": offload_engine,
        "lora_loader": lora_loader,
        "override_system_prompt": override_system_prompt,
        "system_prompt_template": system_prompt_template,
    }
    return {
        "controls": controls,
        "status": status,
        "cleanup_btn": cleanup_btn,
        "cleanup_output": cleanup_output,
        "reset_system_prompt_btn": reset_system_prompt_btn,
    }


LABELS = {
    "output_dir": "Output folder",
    "metadata_dir": "Settings & thumbnails folder",
    "lora_dir": "LoRA folder",
    "gradio_temp_dir": "Temporary folder",
    "gradio_theme": "Theme (restart to apply)",
}


def connect_settings_events(s, settings, tb_processor):
    def save(key, value):
        settings.save_settings(**{key: value})
        label = LABELS.get(key, key.replace("_", " ").capitalize())
        return f"Saved: {label}."

    for key, component in s["controls"].items():
        event = (
            component.blur if isinstance(component, gr.Textbox) else component.change
        )
        event(
            fn=lambda value, key=key: save(key, value),
            inputs=[component],
            outputs=[s["status"]],
            show_progress="hidden",
        )

    s["controls"]["startup_model_type"].change(
        fn=lambda model_type: gr.update(
            choices=presets.load_presets(model_type) if model_type != "None" else [],
            value=None,
        ),
        inputs=[s["controls"]["startup_model_type"]],
        outputs=[s["controls"]["startup_preset_name"]],
    )

    def reset_system_prompt():
        default = settings.default_settings["system_prompt_template"]
        settings.save_settings(
            system_prompt_template=default, override_system_prompt=False
        )
        return default, False, "Saved: system prompt reset to default."

    s["reset_system_prompt_btn"].click(
        fn=reset_system_prompt,
        outputs=[
            s["controls"]["system_prompt_template"],
            s["controls"]["override_system_prompt"],
            s["status"],
        ],
    )
    s["cleanup_btn"].click(
        fn=tb_processor.tb_clear_temporary_files, outputs=[s["cleanup_output"]]
    )
