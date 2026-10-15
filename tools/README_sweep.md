# Headless jobs and the motion reference sweep

`tools/run_job.py` runs FramePack Studio generations without the Gradio UI.
It loads the models the way `studio.py` does and calls the real worker
(`modules/pipelines/worker.py`), so a job gives the same video as the same
settings in the app. Models stay loaded between jobs.

`tools/sweep_motion_reference.py` uses it to run a grid of motion reference
settings over a set of test cases, one process for the whole sweep.

## On the GPU server

Run from the repo root with the app's venv, so the app's model cache
(`hf_download/`) and settings (`.framepack/settings.json`) are used:

```bash
cd /path/to/framepack-studio
source venv/bin/activate        # the venv run.sh uses

# one job
python tools/run_job.py --image start.png --prompt "a man dancing" \
    --model-type F1 --seconds 4 --seed 2500 \
    --guide dance.mp4 --strength 0.5 --start 1.5 --output-dir outputs/try1

# see how big a sweep is before starting it
python tools/sweep_motion_reference.py --spec sweep.yaml --dry-run --seconds-per-job 150

# run it (resumable: just run the same command again after an interruption)
nohup python tools/sweep_motion_reference.py --spec sweep.yaml > sweep.log 2>&1 &
```

Add `--offline` to either script to load models only from the local cache
(same as `studio.py --offline`). Don't run a sweep while the app is generating
on the same GPU.

The app's settings file is read but never written: `quantization_format`,
`mp4_crf` and `gpu_memory_preservation` apply as in the app. The runner
overrides these in memory only: `reuse_model_instance` (on, so the
transformer stays loaded), `output_dir` / `metadata_dir` (per job),
`clean_up_videos` (on, keeps only the final mp4) and `save_metadata` (on).

## run_job.py

```python
import sys; sys.path.insert(0, "tools")
from run_job import run_job

r = run_job(input_image="start.png", prompt="a man dancing", model_type="F1",
            total_second_length=4, seed=1, output_dir="outputs/try1",
            motion_reference_video="dance.mp4", motion_reference_strength=0.75,
            motion_reference_start=1.5)
r["video_path"], r["metadata_path"], r["elapsed"]
```

Parameters are the worker's keyword arguments. Short names also work:
`prompt`, `start_image`/`image`, `seconds`, `width`, `height`, `guide_video`,
`strength` (`motion_reference_strength`), `start` (`motion_reference_start`,
seconds into the guide video). Unknown names raise `TypeError`. A worker
error raises `RuntimeError` with the worker's traceback.

`python tools/run_job.py --params jobs.json` runs one job (a JSON object) or
several (a list) in one process; command line flags override every job, and a
job may set its own `output_dir`. Run `python tools/run_job.py -h` for flags.

### Defaults

The UI defaults from `modules/ui/generate.py`: 25 steps, distilled CFG
(`gs`) 10, CFG 1, `rs` 0, latent window 9, 640x640, 6 s, seed 2500,
blend sections 4, latent type Noise, and MagCache on (threshold 0.1, max
consecutive skips 2, retention 0.25) with TeaCache off, because the UI's
"Caching strategy" defaults to MagCache. Motion reference strength 0.5 and
start 0 s.

Use `--cache None` (or `use_magcache=False`) to sample every step. Worth
checking on a few cases: the MagCache ratios are calibrated on the full
noise schedule, and motion reference shortens it (each section starts from
the reference's latents and the sampler skips the first `0.5 * strength` of
the steps), so MagCache may skip different steps on guided runs than on
baselines.

Two differences from the app, both so runs repeat exactly:

- the global torch RNG is seeded with the job seed before each job (the
  worker seeds its own sampler noise, but the start frame's VAE latent is
  sampled from the global RNG, which the app never seeds);
- `save_section_latents` defaults to off (no re-roll checkpoint per job).

The motion reference video is read from where it is; the app first copies it
into `input_files_dir`.

### Testing without a GPU

`--fake` (or `run_job(fake=True)`) uses the tiny random models from
`tests/cpu/fpharness.py`. Outputs are noise but go through the real worker.
Set up the CPU venv as in `tests/cpu/README.md`, then:

```bash
.venv-cpu/bin/python tools/run_job.py --fake --image start.png --prompt test \
    --model-type F1 --seconds 2 --width 64 --height 64 --steps 3 \
    --latent-window-size 3 --guide guide.mp4
.venv-cpu/bin/python -m pytest tests/cpu/test_run_job.py
```

## sweep_motion_reference.py

### Spec

```yaml
output_root: outputs/sweep_motion_reference   # default; --out overrides
cases:                    # relative paths are relative to this file
  - name: dance01
    start_image: cases/dance01/start.png
    prompt: "a man in a red shirt dancing in a park"
    guide_video: cases/dance01/guide.mp4
grid:                     # these are the defaults
  model_type: [Original, F1]
  strength: [0.25, 0.5, 0.75, 1.0]
  start: [0.0]            # seconds into the guide video
seeds: [2500, 2501, 2502]
baseline: true            # one unguided run per (case, model, seed)
job:                      # anything run_job accepts, shared by every run
  total_second_length: 4
  resolutionW: 640
  resolutionH: 640
```

JSON with the same keys works too. Without a spec, a single case can be given
with `--start-image`, `--guide-video`, `--prompt` and `--name`. Grid and job flags (`--models`, `--strengths`, `--starts`,
`--seeds`, `--no-baseline`, `--seconds`,
`--width`, `--height`, `--steps`, `--latent-window-size`, `--cache`)
override the spec.

The full default grid is 2 models x 3 seeds x (4 strengths x 1 start
guided + 1 baseline) = 30 runs per case. The worker skips the first `0.5 * strength` of
the sampling steps, so strength 1.0 (half the steps) is the strongest setting
and the default strengths cover the whole useful range. `--dry-run` prints the count and an estimate
from `--seconds-per-job` (time one 4 s job first).

### Picking runs

- `--only key=value` keeps runs whose field matches (`model_type`, `case`,
  `seed`, `strength`, `start`, `guided`); `--only text` keeps
  runs whose name contains it (globs work). Repeat to combine; all must match.
- `--limit N` runs at most N of the pending runs.

Run names look like `dance01__F1__s0.5_t0__seed2500` (strength 0.5, start 0 s) and
`dance01__F1__baseline__seed2500`.

### Output

```
<output_root>/
  sweep_config.json         resolved cases, grid, seeds and job settings
  results.jsonl             one line per finished run (append-only log)
  results.csv               rebuilt at the end from every result.json
  runs/<run name>/
    <job_id>_<frames>.mp4   the video
    <job_id>.json / .png    the app's job metadata and start image
    result.json             run fields, all job params, video path, elapsed
```

A run is done when its `result.json` says `ok` and its mp4 exists. Failed runs
are recorded with the error and retried on the next invocation.

