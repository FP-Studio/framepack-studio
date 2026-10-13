<h1 align="center">FramePack Studio</h1>

[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/MtuM7gFJ3V)[![Patreon](https://img.shields.io/badge/Patreon-F96854?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/ColinU)

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/colinurbs/FramePack-Studio)

FramePack Studio is an AI video generation application based on FramePack that strives to provide everything you need to create high quality video projects.

![screencapture-127-0-0-1-7860-2025-06-12-19_50_37](https://github.com/user-attachments/assets/b86a8422-f4ce-452b-80eb-2ba91945f2ea)
![screencapture-127-0-0-1-7860-2025-06-12-19_52_33](https://github.com/user-attachments/assets/ebfb31ca-85b7-4354-87c6-aaab6d1c77b1)

## Current Features

- **F1, Original and Video Extension Generations**: Run all in a single queue
- **End Frame Control for 'Original' Model**: Provides greater control over generations
- **Upscaling and Post-processing**
- **Timestamped Prompts**: Define different prompts for specific time segments in your video
- **Prompt Blending**: Define the blending time between timestamped prompts
- **LoRA Support**: Works with most (all?) Hunyuan Video LoRAs
- **Queue System**: Process multiple generation jobs without blocking the interface. Import and export queues.
- **Metadata Saving/Import**: Prompt and seed are encoded into the output PNG, all other generation metadata is saved in a JSON file that can be imported later for similar generations.
- **Custom Presets**: Allow quick switching between named groups of parameters. A custom Startup Preset can also be set.
- **I2V and T2V**: Works with or without an input image to allow for more flexibility when working with standard Hunyuan Video LoRAs
- **Latent Image Options**: When using T2V you can generate based on a black, white, green screen, or pure noise image

## Prerequisites

- CUDA-compatible GPU with at least 8GB VRAM (16GB+ recommended)
- 16GB System Memory (32GB+ strongly recommended)
- 80GB+ of storage (including ~25GB for each model family: Original and F1)

## Documentation

For information on installation, configuration, and usage, please visit our [documentation site](https://docs.framepackstudio.com/).

## Installation

Please see [this guide](https://docs.framepackstudio.com/docs/get_started/) on our documentation site to get FP-Studio installed.

### Install and configuration guide for agents (and headless servers)

This section is a step-by-step reference for AI coding agents and anyone installing FP-Studio on a headless Linux box. Everything here comes from the scripts and code in this repo. Where the repo doesn't decide something, it says so.

#### Prerequisites

- An NVIDIA GPU with working drivers (`nvidia-smi` must succeed). There is no CPU, Mac/MPS or AMD path.
  - **VRAM:** see [Prerequisites](#prerequisites) above. At startup the app checks free VRAM and only enables "High-VRAM Mode" above 60 GB. Below that, models are swapped between CPU and GPU.
- Python 3.10, 3.11 or 3.12. CI tests these three, and `install.bat` warns on anything else.
- System `ffmpeg`. The Docker image installs it with apt, and torchcodec, the fallback video writer used with newer torchvision, loads FFmpeg's shared libraries. The post-processing toolbox also downloads its own static ffmpeg into `modules/toolbox/bin/` on first start.
- **Disk:** around 25 GB for each model family (Original, F1), plus the shared HunyuanVideo text encoders/VAE and the optional LLM, audio and upscaler weights. Plan for 80 GB or more.

#### Linux install (venv)

```bash
git clone https://github.com/FP-Studio/framepack-studio.git
cd framepack-studio
git checkout main            # or: develop, for unreleased changes

python3 -m venv venv         # Ubuntu may need: sudo apt install python3-venv
source venv/bin/activate
pip install --upgrade pip

# CUDA torch first, then requirements (nothing in requirements.txt pins torch, so it is kept).
pip install torch torchvision torchaudio torchcodec --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

This order was verified on Ubuntu 24.04 with Python 3.10, an RTX 3090 and driver 580: it gave torch 2.11.0+cu128 and torchcodec 0.11.1+cu128. The Dockerfile installs in the opposite order; either should work, but this is the one tested.

**No sudo (no `python3-venv`, no apt `ffmpeg`)?** Use conda for Python and FFmpeg, then make a normal venv from that Python:

```bash
conda create -y -p ./.conda-py -c conda-forge python=3.10 "ffmpeg=7"
./.conda-py/bin/python -m venv venv
ln -sf "$PWD/.conda-py/bin/ffmpeg" venv/bin/ffmpeg
ln -sf "$PWD/.conda-py/bin/ffprobe" venv/bin/ffprobe
```

- **Pin `ffmpeg=7`.** torchcodec 0.11 fails to load against conda-forge's FFmpeg 9 with `Could not load this library: .../libtorchcodec_core4.so`.
- **Don't export `LD_LIBRARY_PATH=.conda-py/lib` globally.** It isn't needed, and it breaks system tools such as `tmux` (`libtinfo.so.6: version ... not found`).

- **CUDA version:** pick the torch index for your setup (`cu128` works on any card with a recent driver). The Docker images are built for `cu124`, `cu126` and `cu128`. **RTX 50xx (Blackwell) cards need `cu128`**; `install.bat` uses torch 2.7.0 + cu128 for them and torch 2.6.0 + cu126 for older cards.
- **`setuptools<81`:** `requirements.txt` pins this on purpose (issue #383). Newer setuptools drops `pkg_resources`, which some dependencies still import. Don't upgrade it.
- **Verify the install:**
  ```bash
  python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
  ```
  This must print `True`.

#### Windows install

Run `install.bat`, then `run.bat`. `install.bat` creates `venv`, picks the torch build from your GPU name (RTX 5000 series gets cu128), and offers to install Sage Attention and/or Flash Attention wheels. `update.bat` runs `git pull` and updates dependencies.

#### Docker

```bash
docker compose up -d          # uses docker-compose.yml; needs the NVIDIA Container Toolkit
```

- **Images:** prebuilt images are published to Docker Hub as `colinurbs/fp-studio` on every push to `main` or `develop`:
  - `cuda12.4-latest`, `cuda12.6-latest` and `cuda12.8-latest` track `main`.
  - Each of those also has a `-latest-develop` variant that tracks `develop`.
  - `cuda12.X-<8-char commit sha>` pins a specific build.
- **Default tag:** `docker-compose.yml` defaults to `cuda12.4-latest-develop`. Edit the `image:` line to change it, and use `cuda12.8-*` for RTX 50xx.
- **Volumes:** compose mounts `./loras`, `./outputs`, `./.framepack`, the toolbox model folders, and `$HOME/.cache/huggingface` (mounted as the container's `hf_download`). The app is served on port 7860.

#### Optional attention libraries

The model picks the first attention library it can import: **SageAttention > FlashAttention > xFormers > PyTorch SDPA**. The `--- Attention Configuration ---` block in the startup output tells you which one is active. `install.bat` installs prebuilt Windows wheels. The repo doesn't pin Linux builds, so install a version that matches your torch/CUDA if you want one. None are required.

#### Running

```bash
source venv/bin/activate
python studio.py --port 7860            # or: bash run.sh --port 7860
```

| Flag | Effect |
| --- | --- |
| `--server <addr>` | Address to bind. **Defaults to `0.0.0.0`**, so it is reachable from the LAN by default. Use `--server 127.0.0.1` for local-only. |
| `--port <n>` | Port. If unset, Gradio's default (7860) is used. |
| `--share` | Create a public Gradio share link. |
| `--inbrowser` | Open a browser on launch. |
| `--offline` | Sets `HF_HUB_OFFLINE=1`. Only works once all models are downloaded. |
| `--lora <paths>` | Parsed but currently unused. Put LoRAs in `lora_dir` instead. |

- **Working directory:** run from the repo root. `studio.log`, `queue.json` and the MMAudio `weights/`/`ext_weights/` folders are written to the current working directory.
- **`run.sh` and `python`:** `run.sh` checks for a `python` binary on `PATH` *before* activating the venv. On systems without one (no `python-is-python3`), it exits with "Did not find a Python binary", so call `venv/bin/python studio.py` directly.

To run it in the background:

```bash
nohup venv/bin/python -u studio.py --port 7860 > studio.out 2>&1 &

# or in tmux, so you can attach to the console later with `tmux attach -t fps`:
tmux new-session -d -s fps "venv/bin/python -u studio.py --port 7860 2>&1 | tee -a studio.out"
```

Use `python -u` whenever output goes to a file or pipe. Without it, stdout is buffered, so lines such as Gradio's `Running on local URL` may never show up in `studio.out` even though the server is up. Check the port instead (see [Verifying it's up](#verifying-its-up)).

To run it as a systemd service, use a unit like this (fill in the user and paths):

```ini
[Unit]
Description=FramePack Studio
After=network-online.target

[Service]
User=YOUR_USER
WorkingDirectory=/path/to/framepack-studio
ExecStart=/path/to/framepack-studio/venv/bin/python studio.py --port 7860
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### Model downloads and `HF_HOME`

- **Where models go:** if `./hf_download` exists *or* `HF_HOME` is unset, `studio.py` sets `HF_HOME` to `./hf_download`. Otherwise it keeps your existing `HF_HOME`. So to reuse a shared Hugging Face cache, export `HF_HOME` and make sure `./hf_download` does not exist.
- **First start:** downloads `hunyuanvideo-community/HunyuanVideo` (text encoders, tokenizers, VAE) and `lllyasviel/flux_redux_bfl` (image encoder) *before the UI comes up*, which can take a long time. The toolbox's ffmpeg is downloaded at this point too.
- **Transformers:** these load (and download on first use) when a job of that type runs, or at startup if a startup model is set:
  - `lllyasviel/FramePackI2V_HY` for Original and Video Extension.
  - `lllyasviel/FramePack_F1_I2V_HY_20250503` for F1 and F1 Video Extension.
- **On first use of their feature:** `microsoft/Florence-2-large` (captioning), `ibm-granite/granite-3.3-2b-instruct` (prompt enhancement), the MMAudio weights (audio generation), and the ESRGAN/RIFE models (toolbox).

#### Configuration

Settings live in `.framepack/settings.json` and are written by the Settings tab, which auto-saves by default. The app keeps settings in memory and rewrites the file whenever one changes, so **stop the app before editing the file by hand**. Missing keys fall back to defaults. Useful keys:

| Key | Default | Notes |
| --- | --- | --- |
| `output_dir`, `metadata_dir` | `./outputs` | Also the only paths Gradio is allowed to serve files from. |
| `lora_dir` | `./loras` | Put `.safetensors` LoRAs here. |
| `gradio_temp_dir` | `./temp` | Exported as `GRADIO_TEMP_DIR`. |
| `input_files_dir` | `./input_files` | |
| `gpu_memory_preservation` | `6` | GB of VRAM to keep free. |
| `lora_loader` | `lora_ready` | `lora_ready` (kohya-ss loader) or `diffusers`. |
| `quantization_format` | `brain_floating_point_16bit` | Also accepts `integer_8bit` or `normal_float_4bit`. Quantization requires `bitsandbytes`; without it the app logs an error and runs unquantized. |
| `reuse_model_instance` | `false` | Keep the transformer loaded between jobs. |
| `startup_model_type` | `"None"` | Preload a model at startup. |
| `auto_cleanup_on_startup` | `false` | Clear temp files on start. |
| `mp4_crf` | `16` | Output video quality. |

#### Verifying it's up

1. In the startup output, check for:
   - `Free VRAM … GB`
   - the `--- Attention Configuration ---` block
   - Gradio's `Running on local URL: http://0.0.0.0:7860`
2. Run `curl -sf -o /dev/null -w '%{http_code}\n' http://HOST:7860/`. It should print `200`.
3. Check `studio.log` in the repo root. It is written at DEBUG level, so it has more detail than the console.
4. Run a short generation of each type you care about. Transformer downloads and loading only happen at this point.

#### Common failures

- **`No module named 'pkg_resources'`:** setuptools 81+ got installed. Run `pip install "setuptools<81"`.
- **Video saving fails after a torch/torchvision upgrade:** newer torchvision removed `torchvision.io.write_video`, so the app falls back to torchcodec. That fallback needs torchcodec installed from the same torch index and system FFmpeg libraries (`sudo apt install ffmpeg`).
- **CUDA errors such as "no kernel image" on RTX 50xx:** reinstall torch from the `cu128` index.
- **`run.sh` says "Did not find a Python binary":** see [Running](#running).
- **Startup seems hung:** it is usually still downloading models (see [Model downloads](#model-downloads-and-hf_home)). Check network activity or `hf_download/` size.

## Contributing 

We would love your help building FramePack Studio! To make collaboration effective, please adhere to the following:
- Keep Pull Requests Focused: Each Pull Request should address a single issue or add one specific feature. Please do not mix bug fixes, new features, and code refactoring in the same PR.
- Target the develop Branch: All Pull Requests must be opened against the develop branch. PRs opened against the main branch will be closed.
- Discuss Big Changes First: If you plan to work on a large feature or a significant refactor, please announce it first in the #contributors channel on our [Discord server](https://discord.com/invite/MtuM7gFJ3V). This helps us coordinate efforts and prevent duplicate work.


## Credits

Many thanks to [Lvmin Zhang](https://github.com/lllyasviel) for the absolutely amazing work on the original [FramePack](https://github.com/lllyasviel/FramePack) code!

Thanks to [Rickard Edén](https://github.com/neph1) for the LoRA code and their general contributions to this growing FramePack scene!

Thanks to [Zehong Ma](https://github.com/Zehong-Ma) for [MagCache](https://github.com/Zehong-Ma/MagCache): Fast Video Generation with Magnitude-Aware Cache!

Thanks to everyone who has joined the Discord, reported a bug, sumbitted a PR, or helped with testing!

    @article{zhang2025framepack,
        title={Packing Input Frame Contexts in Next-Frame Prediction Models for Video Generation},
        author={Lvmin Zhang and Maneesh Agrawala},
        journal={Arxiv},
        year={2025}
    }

    @misc{zhang2025packinginputframecontext,
        title={Packing Input Frame Context in Next-Frame Prediction Models for Video Generation},
        author={Lvmin Zhang and Maneesh Agrawala},
        year={2025},
        eprint={2504.12626},
        archivePrefix={arXiv},
        primaryClass={cs.CV},
        url={https://arxiv.org/abs/2504.12626}
    }
