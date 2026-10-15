# CPU test harness

Runs the real generation worker, queue and Gradio UI without a GPU or model
downloads. The transformer and VAE are tiny randomly initialised versions of
the real architectures, and the text/CLIP encoders return deterministic fake
embeddings. Outputs are noise, but every tensor goes through the same code
paths as a real job, so the tests check plumbing exactly (same-seed runs match
bit for bit).

These tests do not show whether a feature *looks* right. Check that on a GPU
with the real models.

## Setup

```bash
uv venv -p 3.11 .venv-cpu
VIRTUAL_ENV=.venv-cpu uv pip install torch torchvision numpy==1.26.2 einops \
  diffusers==0.33.1 transformers==4.46.2 accelerate==1.6.0 safetensors \
  scipy==1.12.0 pillow opencv-python-headless pytest torchsde==0.2.6 \
  "huggingface_hub<0.35.1" gradio==5.25.2 "peft<0.18.0" av colorlog psutil \
  imageio imageio-ffmpeg==0.4.8 ffmpeg-python jinja2 requests sentencepiece \
  tqdm timm devicetorch torchcodec bitsandbytes omegaconf librosa
```

`fpshim.py` stubs packages that are only needed by the toolbox or that have
no wheels on some platforms (decord, basicsr, realesrgan, ...).

## Run the tests

```bash
.venv-cpu/bin/python -m pytest tests/cpu
```

To check that a branch doesn't change default behaviour, record a baseline
from an untouched checkout, then compare:

```bash
# in a checkout of the base branch
.venv-cpu/bin/python tests/cpu/baseline_cases.py /tmp/baseline.pt
# in this checkout
FP_BASELINE=/tmp/baseline.pt .venv-cpu/bin/python -m pytest tests/cpu/test_baseline.py
```

## Click through the UI

```bash
.venv-cpu/bin/python tests/cpu/studio_fake.py --port 7861 --server 127.0.0.1
```

Jobs run end to end in seconds at 128x128. Each sampler call is logged with
the noise / initial latent it received.

## Check the UI in a browser

`ui_check.py` drives the running app like a user: model gating, arrows and
keyframes on the timeline, a job through to the Library, a re-roll from a
section, a video extension and presets.

```bash
VIRTUAL_ENV=.venv-cpu uv pip install playwright static-ffmpeg eva-decord
.venv-cpu/bin/python -m playwright install chromium
# Gradio's video player needs ffprobe; static-ffmpeg ships one
export PATH="$(.venv-cpu/bin/python -c 'import static_ffmpeg.run as r, os; print(os.path.dirname(r.get_or_fetch_platform_executables_else_raise()[1]))'):$PATH"

FP_REAL_DECORD=1 .venv-cpu/bin/python tests/cpu/studio_fake.py --port 7861 --server 127.0.0.1 &
.venv-cpu/bin/python tests/cpu/ui_check.py --url http://127.0.0.1:7861/ --outputs outputs
```

Without `FP_REAL_DECORD=1`, decord is stubbed and video jobs fail; pass
`--no-video` to skip that part.

`tools_check.py` does the same for the Tools tab: steps, recipes, batch, Join
clips and Edit frames on small generated clips. The toolbox looks for ffmpeg
in `modules/toolbox/bin`, so link the static one there first:

```bash
FF="$(dirname "$(command -v ffmpeg)")"
ln -sf "$FF/ffmpeg" "$FF/ffprobe" modules/toolbox/bin/
.venv-cpu/bin/python tests/cpu/tools_check.py --url http://127.0.0.1:7861/
```
