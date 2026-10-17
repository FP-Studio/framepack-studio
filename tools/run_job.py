"""
Run FramePack Studio generations headlessly, without the Gradio UI.

Models are loaded the way studio.py loads them and handed to the real
`modules.pipelines.worker.worker`, which reads them from `__main__` exactly as
it does inside the app. They stay loaded across calls, so one process can run
many jobs.

From Python:

    from tools.run_job import run_job
    result = run_job(input_image="start.png", prompt="a bunny dancing",
                     model_type="F1", total_second_length=4, seed=1,
                     motion_reference_video="guide.mp4",
                     motion_reference_strength=0.5)
    result["video_path"], result["metadata_path"], result["elapsed"]

From the command line (run from the repo root with the app's venv):

    python tools/run_job.py --image start.png --prompt "a bunny dancing" \
        --model-type F1 --seconds 4 --guide guide.mp4 --strength 0.5 --start 1.5
    python tools/run_job.py --params job.json   # one job or a list of jobs
    python tools/run_job.py --image start.png --prompt "..." \
        --lora dolly_smoke_r32:1.0 --lora-dir runs/dolly_smoke_r32

LoRAs are named by file stem, NAME or NAME:WEIGHT, and load with the
lora_ready (kohya) loader unless --lora-loader says otherwise: it reads
musubi-tuner's format, which the diffusers loader can't.

`--fake` swaps in the tiny CPU test models from tests/cpu/fpharness.py so the
plumbing can be checked without a GPU (outputs are noise).
"""

# ruff: noqa: E402 - HF_HOME must be set before diffusers / transformers are imported
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Same rule as the top of studio.py, with the repo root in place of studio.py's
# directory: use ./hf_download if it exists or if HF_HOME is not set at all.
STUDIO_HF_HOME = os.path.abspath(
    os.path.realpath(os.path.join(REPO_ROOT, "./hf_download"))
)
if os.path.exists(STUDIO_HF_HOME) or os.environ.get("HF_HOME") is None:
    os.environ["HF_HOME"] = STUDIO_HF_HOME
os.environ["TOKENIZERS_PARALLELISM"] = "false"

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import argparse
import gc
import json
import logging
import threading
import time
import traceback
import types

logger = logging.getLogger("run_job")

# UI defaults (modules/ui/generate.py) unless noted.
DEFAULTS = {
    "model_type": "Original",
    "input_image": None,  # path or HxWx3 uint8 array; None -> blank latent_type image
    "end_frame_image": None,
    "end_frame_strength": 1.0,
    "prompt_text": "",
    "n_prompt": "",
    "seed": 2500,
    "total_second_length": 6,
    "latent_window_size": 9,
    "steps": 25,
    "cfg": 1.0,
    "gs": 10.0,
    "rs": 0.0,
    # The UI's "Caching strategy" radio defaults to MagCache.
    "use_teacache": False,
    "teacache_num_steps": 25,
    "teacache_rel_l1_thresh": 0.15,
    "use_magcache": True,
    "magcache_threshold": 0.1,
    "magcache_max_consecutive_skips": 2,
    "magcache_retention_ratio": 0.25,
    "blend_sections": 4,
    "latent_type": "Noise",
    "resolutionW": 640,
    "resolutionH": 640,
    "combine_with_source": True,
    "num_cleaned_frames": 5,
    "save_metadata_checked": True,
    # The UI saves a re-roll checkpoint per job; a sweep doesn't need them.
    "save_section_latents": False,
    # Re-roll: a section checkpoint and the 1-based section (generation order)
    # to regenerate from; earlier sections are kept as they were.
    "reroll_latents_path": None,
    "reroll_from_section": None,
    "keyframe_images": None,
    "keyframe_times": None,
    "motion_reference_video": None,
    "motion_reference_strength": 0.5,
    "motion_reference_start": 0.0,
    "flow_noise_arrows": None,
    "flow_noise_camera": "None",
    "flow_noise_camera_amount": 0.3,
    "flow_noise_strength": 0.7,
    # {file stem: weight}; files are looked up in lora_dir (default: the app's)
    "loras": None,
    "lora_dir": None,
    "lora_loader": "lora_ready",
}

# Friendlier names accepted by run_job() / JSON job files.
ALIASES = {
    "prompt": "prompt_text",
    "negative_prompt": "n_prompt",
    "start_image": "input_image",
    "image": "input_image",
    "seconds": "total_second_length",
    "width": "resolutionW",
    "height": "resolutionH",
    "guide_video": "motion_reference_video",
    "motion_reference": "motion_reference_video",
    "strength": "motion_reference_strength",
    "start": "motion_reference_start",
}

_MODELS = None
_APP_DIRS = {}


def configure_logging(level=logging.INFO):
    """Console logging like studio.py (without its studio.log file handler)."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    for name in (
        "accelerate",
        "diffusers",
        "httpx",
        "huggingface_hub",
        "PIL",
        "safetensors",
        "sageattention",
        "torch",
        "torchvision",
    ):
        logging.getLogger(name).setLevel(logging.ERROR)


def load_models(fake=False, offline=False):
    """
    Load the shared (non-transformer) models once per process and return them.

    The transformer is loaded by the worker's model generator on the first
    job, like in the app.
    """
    global _MODELS
    if _MODELS is not None:
        if _MODELS.fake != fake:
            raise RuntimeError("Real and fake models can't be mixed in one process")
        return _MODELS
    _MODELS = _load_fake_models() if fake else _load_real_models(offline)
    return _MODELS


def _load_real_models(offline):
    # Mirrors studio.py: --offline handling, VRAM check, from_pretrained calls,
    # eval / fp16 / requires_grad, and the high_vram placement branch.
    if offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
    else:
        os.environ.pop("HF_HUB_OFFLINE", None)

    import torch
    from diffusers import AutoencoderKLHunyuanVideo
    from transformers import (
        CLIPTextModel,
        CLIPTokenizer,
        LlamaModel,
        LlamaTokenizerFast,
        SiglipImageProcessor,
        SiglipVisionModel,
    )

    from diffusers_helper.memory import (
        DynamicSwapInstaller,
        get_cuda_free_memory_gb,
        gpu,
    )

    from modules import vram_mode
    from modules.settings import Settings

    free_mem_gb = get_cuda_free_memory_gb(gpu)
    vram_mode.set_mode(
        vram_mode.choose(free_mem_gb, Settings().get("vram_mode", vram_mode.AUTO))
    )
    high_vram = vram_mode.get() == vram_mode.HIGH
    logger.info(f"Free VRAM {free_mem_gb} GB, VRAM mode: {vram_mode.get()}")

    text_encoder = LlamaModel.from_pretrained(
        "hunyuanvideo-community/HunyuanVideo",
        subfolder="text_encoder",
        torch_dtype=torch.float16,
    ).cpu()
    text_encoder_2 = CLIPTextModel.from_pretrained(
        "hunyuanvideo-community/HunyuanVideo",
        subfolder="text_encoder_2",
        torch_dtype=torch.float16,
    ).cpu()
    tokenizer = LlamaTokenizerFast.from_pretrained(
        "hunyuanvideo-community/HunyuanVideo", subfolder="tokenizer"
    )
    tokenizer_2 = CLIPTokenizer.from_pretrained(
        "hunyuanvideo-community/HunyuanVideo", subfolder="tokenizer_2"
    )
    vae = AutoencoderKLHunyuanVideo.from_pretrained(
        "hunyuanvideo-community/HunyuanVideo",
        subfolder="vae",
        torch_dtype=torch.float16,
    ).cpu()
    feature_extractor = SiglipImageProcessor.from_pretrained(
        "lllyasviel/flux_redux_bfl", subfolder="feature_extractor"
    )
    image_encoder = SiglipVisionModel.from_pretrained(
        "lllyasviel/flux_redux_bfl",
        subfolder="image_encoder",
        torch_dtype=torch.float16,
    ).cpu()

    vae.eval()
    text_encoder.eval()
    text_encoder_2.eval()
    image_encoder.eval()

    if not high_vram:
        vae.enable_slicing()
        vae.enable_tiling()

    vae.to(dtype=torch.float16)
    image_encoder.to(dtype=torch.float16)
    text_encoder.to(dtype=torch.float16)
    text_encoder_2.to(dtype=torch.float16)

    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)
    text_encoder_2.requires_grad_(False)
    image_encoder.requires_grad_(False)

    if not high_vram:
        # DynamicSwapInstaller is same as huggingface's enable_sequential_offload but 3x faster
        DynamicSwapInstaller.install_model(text_encoder, device=gpu)
    else:
        text_encoder.to(gpu)
        text_encoder_2.to(gpu)
        image_encoder.to(gpu)
        vae.to(gpu)

    return types.SimpleNamespace(
        fake=False,
        high_vram=high_vram,
        offline=offline,
        text_encoder=text_encoder,
        text_encoder_2=text_encoder_2,
        tokenizer=tokenizer,
        tokenizer_2=tokenizer_2,
        vae=vae,
        image_encoder=image_encoder,
        feature_extractor=feature_extractor,
        prompt_embedding_cache={},
    )


def _load_fake_models():
    # Same wiring as tests/cpu/fpharness.py (_patch_cpu / _install_globals),
    # but the worker writes real mp4 files.
    cpu_tests = os.path.join(REPO_ROOT, "tests", "cpu")
    if cpu_tests not in sys.path:
        sys.path.insert(0, cpu_tests)
    import fpshim  # noqa: F401  (stubs CUDA-only imports; must come first)
    import fpharness

    worker_mod = fpharness._patch_cpu()
    worker_mod.save_bcthw_as_mp4 = _save_mp4_with_av
    return types.SimpleNamespace(
        fake=True,
        high_vram=True,
        offline=False,
        text_encoder=None,
        text_encoder_2=None,
        tokenizer=None,
        tokenizer_2=None,
        vae=fpharness.tiny_vae(),
        image_encoder=None,
        feature_extractor=None,
        prompt_embedding_cache=fpharness.FakePromptCache(),
    )


def _save_mp4_with_av(x, output_filename, fps=10, crf=0):
    """Fake mode only: torchcodec needs system ffmpeg libraries, PyAV bundles its own."""
    import av
    import einops
    import torch

    os.makedirs(os.path.dirname(os.path.abspath(output_filename)), exist_ok=True)
    x = (torch.clamp(x.float(), -1.0, 1.0) * 127.5 + 127.5).to(torch.uint8)
    frames = einops.rearrange(x[:1], "b c t h w -> t h (b w) c").numpy()
    with av.open(output_filename, "w") as container:
        stream = container.add_stream("libx264", rate=int(fps))
        stream.width, stream.height = frames.shape[2], frames.shape[1]
        stream.pix_fmt = "yuv420p"
        for frame in frames:
            for packet in stream.encode(
                av.VideoFrame.from_ndarray(frame, format="rgb24")
            ):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return output_filename


def _install_globals(models, stream):
    """The worker does `from __main__ import high_vram, args, vae, ...`."""
    main = sys.modules["__main__"]
    main.high_vram = models.high_vram
    main.args = types.SimpleNamespace(offline=models.offline)
    main.text_encoder = models.text_encoder
    main.text_encoder_2 = models.text_encoder_2
    main.tokenizer = models.tokenizer
    main.tokenizer_2 = models.tokenizer_2
    main.vae = models.vae
    main.image_encoder = models.image_encoder
    main.feature_extractor = models.feature_extractor
    main.prompt_embedding_cache = models.prompt_embedding_cache
    # The worker also pushes every update to the app-wide stream; point it at
    # this job's stream so nothing piles up in an undrained queue.
    main.stream = stream


class _LogCatcher(logging.Handler):
    """Collects messages at or above `level` that mention `text`."""

    def __init__(self, level, text):
        super().__init__(level)
        self.text, self.messages = text, []

    def emit(self, record):
        message = record.getMessage()
        if self.text in message:
            self.messages.append(message)


_SETTINGS_OVERRIDES = {}


def _override_settings(settings, **values):
    """
    Set app settings for this process only. Studio calls Settings() in many
    places and every call reloads the file, so the overrides are reapplied on
    each reload rather than set once.
    """
    _SETTINGS_OVERRIDES.update(values)
    settings.settings.update(values)
    cls = type(settings)
    if not getattr(cls, "_run_job_patched", False):
        load = cls.load_settings

        def load_with_overrides(self):
            return {**load(self), **_SETTINGS_OVERRIDES}

        cls.load_settings = load_with_overrides
        cls._run_job_patched = True


def normalize_params(params):
    """Apply ALIASES and DEFAULTS; reject unknown keys."""
    out = dict(DEFAULTS)
    for key, value in params.items():
        key = ALIASES.get(key, key)
        if key not in DEFAULTS:
            raise TypeError(f"Unknown job parameter: {key}")
        out[key] = value
    return out


def _load_image(value):
    if value is None or not isinstance(value, (str, os.PathLike)):
        return value
    import numpy as np
    from PIL import Image

    # The UI's gr.Image(type="numpy", image_mode="RGB") hands the worker this.
    with Image.open(value) as img:
        return np.array(img.convert("RGB"))


def _blank_image(latent_type, height, width):
    """Same placeholder images as studio.py process() when no start frame is given."""
    import numpy as np

    if latent_type == "White":
        return np.ones((height, width, 3), dtype=np.uint8) * 255
    if latent_type == "Noise":
        return np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    if latent_type == "Green Screen":
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image[:, :, 1] = 177
        image[:, :, 2] = 64
        return image
    return np.zeros((height, width, 3), dtype=np.uint8)


def run_job(
    output_dir=None,
    metadata_dir=None,
    models=None,
    fake=False,
    offline=False,
    clean_up_videos=True,
    save_metadata=True,
    verbose=True,
    **params,
):
    """
    Run one generation through the real worker and wait for it to finish.

    `params` are worker() keyword arguments (or the ALIASES above); anything
    left out takes the UI default from DEFAULTS. `models` overrides the
    loaded models (e.g. a namespace built like _load_fake_models()).

    Returns {"video_path", "metadata_path", "elapsed", "job_id", "files"}.
    Raises RuntimeError if the worker reports an error or writes no video.
    """
    if models is None:
        models = load_models(fake=fake, offline=offline)

    import torch

    from diffusers_helper.thread_utils import AsyncStream
    from modules.pipelines import worker as worker_mod
    from modules.studio_manager import StudioManager

    job = normalize_params(params)
    sm = StudioManager()
    settings = sm.settings
    # Not settings.set(), which would rewrite .framepack/settings.json
    _override_settings(
        settings,
        reuse_model_instance=True,  # keep the transformer loaded
        clean_up_videos=clean_up_videos,
        save_metadata=save_metadata,
    )
    # Remember the app's own output folders before overriding them per job.
    app_dirs = _APP_DIRS.setdefault(
        "dirs",
        (settings.get("output_dir"), settings.get("metadata_dir"), settings.get("lora_dir")),
    )
    if output_dir is None:
        output_dir, metadata_dir = app_dirs[0], metadata_dir or app_dirs[1]
    output_dir = os.path.abspath(output_dir)
    metadata_dir = os.path.abspath(metadata_dir or output_dir)
    loras = job.pop("loras") or {}
    lora_dir = os.path.abspath(job.pop("lora_dir") or app_dirs[2])
    # The worker's start-image/metadata writer and LoRA loader read these
    _override_settings(
        settings,
        output_dir=output_dir,
        metadata_dir=metadata_dir,
        lora_dir=lora_dir,
        lora_loader=job.pop("lora_loader"),
    )
    input_files_dir = settings.get("input_files_dir")
    for name in loras:
        path = os.path.join(lora_dir, f"{name}.safetensors")
        if not os.path.exists(path):
            raise FileNotFoundError(path)
    os.environ.setdefault("GRADIO_TEMP_DIR", settings.get("gradio_temp_dir"))
    for path in (output_dir, metadata_dir, input_files_dir):
        os.makedirs(path, exist_ok=True)

    # Free the previous transformer before a different one is loaded, so two
    # never sit in memory at once.
    current = sm.current_generator
    if current is not None and current.model_name != job["model_type"]:
        sm.unset_current_generator()
        del current
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    has_input_image = job["input_image"] is not None
    job["input_image"] = _load_image(job["input_image"])
    if not has_input_image:
        job["input_image"] = _blank_image(
            job["latent_type"], job["resolutionH"], job["resolutionW"]
        )
    job["end_frame_image"] = _load_image(job["end_frame_image"])
    if job["motion_reference_video"]:
        job["motion_reference_video"] = os.path.abspath(job["motion_reference_video"])
        if not os.path.exists(job["motion_reference_video"]):
            raise FileNotFoundError(job["motion_reference_video"])

    stream = AsyncStream()
    _install_globals(models, stream)
    worker_kwargs = dict(
        job,
        selected_loras=list(loras),
        lora_values=[float(w) for w in loras.values()],
        lora_loaded_names=list(loras),
        has_input_image=has_input_image,
        job_stream=stream,
        output_dir=output_dir,
        metadata_dir=metadata_dir,
        input_files_dir=input_files_dir,
        input_image_path=None,  # the UI passes None for numpy start frames
        end_frame_image_path=None,
    )

    # The worker seeds its own sampler noise, but vae_encode samples the
    # start-frame latent from the global RNG; seed it so runs repeat exactly.
    torch.manual_seed(int(job["seed"]))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(job["seed"]))

    def target():
        try:
            worker_mod.worker(**worker_kwargs)
        except BaseException:
            stream.output_queue.push(("error", traceback.format_exc()))
            stream.output_queue.push(("end", None))

    # Studio logs a LoRA that fails to load and renders without it; catch that
    lora_errors = _LogCatcher(logging.ERROR, "LoRA")
    generators_log = logging.getLogger("modules.generators")
    generators_log.addHandler(lora_errors)

    started = time.time()
    thread = threading.Thread(target=target, name="run_job-worker", daemon=True)
    thread.start()

    files, errors = [], []
    job_id = None
    last_desc, last_print = None, 0.0
    try:
        while True:
            item = stream.output_queue.pop()
            if item is None:
                if not thread.is_alive():
                    item = stream.output_queue.pop()
                    if item is None:
                        break
                else:
                    time.sleep(0.05)
                    continue
            flag, data = item
            if flag == "file":
                files.append(data)
            elif flag == "job_id" and job_id is None:
                job_id = data
            elif flag == "error":
                errors.append(data)
            elif flag == "progress" and verbose:
                desc = data[1]
                now = time.time()
                if desc and desc != last_desc and now - last_print > 5:
                    logger.info(desc)
                    last_desc, last_print = desc, now
            elif flag == "end":
                break
    except KeyboardInterrupt:
        stream.input_queue.push("end")  # same signal as the Cancel button
        thread.join()
        raise
    thread.join()
    elapsed = time.time() - started
    generators_log.removeHandler(lora_errors)

    if errors:
        raise RuntimeError(errors[-1])
    if loras and lora_errors.messages:
        raise RuntimeError(f"LoRA didn't load: {lora_errors.messages[-1]}")
    if not files or not os.path.exists(files[-1]):
        raise RuntimeError(f"Worker finished without writing a video (job {job_id})")
    metadata_path = os.path.join(metadata_dir, f"{job_id}.json") if job_id else None
    if metadata_path and not os.path.exists(metadata_path):
        metadata_path = None
    files = [f for f in files if os.path.exists(f)]  # earlier sections get cleaned up
    return {
        "video_path": files[-1],
        "metadata_path": metadata_path,
        "elapsed": elapsed,
        "job_id": job_id,
        "files": files,
    }


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--params", help="JSON file with one job (object) or many (list)")
    p.add_argument("--image", dest="input_image", help="start frame image")
    p.add_argument("--prompt", dest="prompt_text")
    p.add_argument("--negative-prompt", dest="n_prompt")
    p.add_argument("--model-type", dest="model_type", help="Original, F1, ...")
    p.add_argument("--seed", type=int)
    p.add_argument("--seconds", dest="total_second_length", type=float)
    p.add_argument("--width", dest="resolutionW", type=int)
    p.add_argument("--height", dest="resolutionH", type=int)
    p.add_argument("--steps", type=int)
    p.add_argument("--gs", type=float)
    p.add_argument("--cfg", type=float)
    p.add_argument("--rs", type=float)
    p.add_argument("--latent-window-size", dest="latent_window_size", type=int)
    p.add_argument("--blend-sections", dest="blend_sections", type=int)
    p.add_argument(
        "--cache",
        choices=["MagCache", "TeaCache", "None"],
        help="caching strategy (UI default MagCache)",
    )
    p.add_argument(
        "--guide", dest="motion_reference_video", help="motion reference video"
    )
    p.add_argument(
        "--strength",
        dest="motion_reference_strength",
        type=float,
        help="0..1, how closely to follow the reference (UI default 0.5)",
    )
    p.add_argument(
        "--start",
        dest="motion_reference_start",
        type=float,
        help="seconds into the reference to start from (default 0)",
    )
    p.add_argument(
        "--lora",
        action="append",
        metavar="NAME[:WEIGHT]",
        help="LoRA file stem, repeatable (weight default 1.0)",
    )
    p.add_argument("--lora-dir", help="folder with the LoRA files")
    p.add_argument("--lora-loader", choices=["lora_ready", "diffusers"])
    p.add_argument("--output-dir", help="default: the app's output_dir setting")
    p.add_argument("--fake", action="store_true", help="tiny CPU test models")
    p.add_argument("--offline", action="store_true", help="HF_HUB_OFFLINE=1")
    p.add_argument("--keep-section-videos", action="store_true")
    p.add_argument(
        "--setting",
        action="append",
        metavar="KEY=VALUE",
        help="app setting for this run only, repeatable (e.g. quantization_format=float8_storage)",
    )
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    configure_logging()

    jobs = [{}]
    if args.params:
        with open(args.params) as f:
            loaded = json.load(f)
        jobs = loaded if isinstance(loaded, list) else [loaded]

    overrides = {
        k: v
        for k, v in vars(args).items()
        if v is not None
        and k
        not in (
            "params",
            "output_dir",
            "fake",
            "offline",
            "keep_section_videos",
            "cache",
            "setting",
        )
    }
    if args.lora:
        overrides["loras"] = {
            name: float(weight or 1.0)
            for name, _, weight in (spec.partition(":") for spec in args.lora)
        }
        del overrides["lora"]
    if args.cache:
        overrides["use_magcache"] = args.cache == "MagCache"
        overrides["use_teacache"] = args.cache == "TeaCache"

    if args.setting:
        from modules.settings import Settings

        values = {}
        for spec in args.setting:
            key, _, raw = spec.partition("=")
            try:
                values[key] = json.loads(raw)
            except ValueError:
                values[key] = raw
        _override_settings(Settings(), **values)

    load_models(fake=args.fake, offline=args.offline)
    results = []
    for job in jobs:
        job = dict(job)
        output_dir = job.pop("output_dir", None) or args.output_dir
        job.update(overrides)
        result = run_job(
            output_dir=output_dir,
            fake=args.fake,
            offline=args.offline,
            clean_up_videos=not args.keep_section_videos,
            **job,
        )
        print(json.dumps(result), flush=True)
        results.append(result)
    return results


if __name__ == "__main__":
    main()
