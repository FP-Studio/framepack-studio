"""
Sweep the motion reference settings over a set of test cases.

Every run goes through tools/run_job.py in this one process, so the models are
loaded once. Runs are ordered by model type so the transformer is swapped only
when the model type changes.

    python tools/sweep_motion_reference.py --spec sweep.yaml --dry-run --seconds-per-job 150
    python tools/sweep_motion_reference.py --spec sweep.yaml
    python tools/sweep_motion_reference.py --spec sweep.yaml --only model_type=F1 --limit 10

Each run writes into <out>/runs/<run name>/: the mp4, the job metadata json,
and result.json. A run whose result.json points at an existing mp4 is skipped,
so an interrupted sweep picks up where it stopped. <out>/results.jsonl gets one
line per finished run and <out>/results.csv is rebuilt from all result.json
files at the end.

See tools/README_sweep.md for the spec format.
"""

import argparse
import csv
import fnmatch
import itertools
import json
import os
import sys
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)

DEFAULT_GRID = {
    "model_type": ["Original", "F1"],
    # The worker skips 0.5 * strength of the steps, so 1.0 (half the steps,
    # starting near sigma 0.85) is the strongest setting and still leaves the
    # look to the prompt; below ~0.25 the reference barely registers.
    "strength": [0.25, 0.5, 0.75, 1.0],
    # Seconds into the guide video to start from.
    "start": [0.0],
}
DEFAULT_SEEDS = [2500, 2501, 2502]

# Job settings shared by every run; anything run_job accepts can go here.
DEFAULT_JOB = {
    "total_second_length": 4,
    "resolutionW": 640,
    "resolutionH": 640,
}

CSV_FIELDS = [
    "name",
    "case",
    "model_type",
    "guided",
    "strength",
    "start",
    "seed",
    "status",
    "video_path",
    "metadata_path",
    "elapsed",
    "start_image",
    "guide_video",
    "prompt",
    "error",
]


def load_spec(path):
    if path is None:
        return {}
    with open(path) as f:
        if path.endswith((".yaml", ".yml")):
            import yaml

            spec = yaml.safe_load(f)
        else:
            spec = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    for case in spec.get("cases", []):
        for key in ("start_image", "guide_video"):
            if case.get(key) and not os.path.isabs(case[key]):
                case[key] = os.path.normpath(os.path.join(base, case[key]))
    return spec


def slug(text):
    return "".join(c if c.isalnum() or c in "-." else "-" for c in str(text))


def run_name(case, model_type, seed, strength=None, start=None):
    head = f"{slug(case)}__{slug(model_type)}"
    if strength is None:
        return f"{head}__baseline__seed{seed}"
    return f"{head}__s{strength:g}_t{start:g}__seed{seed}"


def plan_runs(cases, grid, seeds, baseline=True):
    """All runs, ordered by model type so the transformer reloads only on a switch."""
    runs = []
    for model_type in grid["model_type"]:
        for case in cases:
            for seed in seeds:
                common = {
                    "case": case["name"],
                    "model_type": model_type,
                    "seed": seed,
                    "start_image": case["start_image"],
                    "prompt": case.get("prompt", ""),
                }
                if baseline:
                    runs.append(
                        dict(
                            common,
                            name=run_name(case["name"], model_type, seed),
                            guided=False,
                            guide_video=None,
                            strength=None,
                            start=None,
                        )
                    )
                for strength, start in itertools.product(
                    grid["strength"], grid["start"]
                ):
                    runs.append(
                        dict(
                            common,
                            name=run_name(
                                case["name"],
                                model_type,
                                seed,
                                strength,
                                start,
                            ),
                            guided=True,
                            guide_video=case["guide_video"],
                            strength=strength,
                            start=start,
                        )
                    )
    return runs


def matches(run, filters):
    """Every filter must match: key=value compares a field, anything else globs the name."""
    for f in filters:
        if "=" in f:
            key, value = f.split("=", 1)
            if str(run.get(key)).lower() != value.lower():
                try:
                    if float(run.get(key)) == float(value):
                        continue
                except (TypeError, ValueError):
                    pass
                return False
        elif not fnmatch.fnmatch(run["name"], f if "*" in f else f"*{f}*"):
            return False
    return True


def run_dir(out_root, run):
    return os.path.join(out_root, "runs", run["name"])


def load_result(out_root, run):
    path = os.path.join(run_dir(out_root, run), "result.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def is_done(out_root, run):
    result = load_result(out_root, run)
    return bool(
        result
        and result.get("status") == "ok"
        and result.get("video_path")
        and os.path.exists(result["video_path"])
    )


def job_params(run, job_defaults):
    params = dict(job_defaults)
    params.update(
        model_type=run["model_type"],
        input_image=run["start_image"],
        prompt_text=run["prompt"],
        seed=run["seed"],
    )
    if run["guided"]:
        params.update(
            motion_reference_video=run["guide_video"],
            motion_reference_strength=run["strength"],
            motion_reference_start=run["start"],
        )
    else:
        params["motion_reference_video"] = None
    return params


def write_result(out_root, run, result):
    folder = run_dir(out_root, run)
    os.makedirs(folder, exist_ok=True)
    tmp = os.path.join(folder, "result.json.tmp")
    with open(tmp, "w") as f:
        json.dump(result, f, indent=2)
    os.replace(tmp, os.path.join(folder, "result.json"))
    with open(os.path.join(out_root, "results.jsonl"), "a") as f:
        f.write(json.dumps(result) + "\n")


def write_csv(out_root, runs):
    path = os.path.join(out_root, "results.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for run in runs:
            result = load_result(out_root, run)
            if result:
                writer.writerow(result)
    return path


def run_one(out_root, run, job_defaults, fake, offline):
    from run_job import normalize_params, run_job

    record = {k: run.get(k) for k in CSV_FIELDS if k in run}
    # Every setting the job ran with, UI defaults included.
    record["params"] = {
        k: v
        for k, v in normalize_params(job_params(run, job_defaults)).items()
        if k not in ("input_image", "end_frame_image", "keyframe_images")
    }
    try:
        result = run_job(
            output_dir=run_dir(out_root, run),
            fake=fake,
            offline=offline,
            **job_params(run, job_defaults),
        )
    except Exception as e:  # keep sweeping; the failure is recorded
        record.update(status="error", error=str(e)[-2000:])
        return record
    record.update(
        status="ok",
        video_path=result["video_path"],
        metadata_path=result["metadata_path"],
        elapsed=round(result["elapsed"], 2),
        job_id=result["job_id"],
    )
    return record


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--spec", help="YAML or JSON sweep spec (see README_sweep.md)")
    p.add_argument(
        "--out",
        help="output root (default: spec 'output_root' or outputs/sweep_motion_reference)",
    )
    case = p.add_argument_group("single case without a spec")
    case.add_argument("--name", default="case")
    case.add_argument("--start-image")
    case.add_argument("--guide-video")
    case.add_argument("--prompt", default="")
    grid = p.add_argument_group("grid (overrides the spec)")
    grid.add_argument("--models", help="comma list, default Original,F1")
    grid.add_argument("--strengths", help="comma list, default 0.25,0.5,0.75,1.0")
    grid.add_argument(
        "--starts", help="comma list of seconds into the guide, default 0"
    )
    grid.add_argument("--seeds", help="comma list, default 2500,2501,2502")
    grid.add_argument("--no-baseline", action="store_true")
    job = p.add_argument_group("job settings (override the spec)")
    job.add_argument("--seconds", type=float, help="video length, default 4")
    job.add_argument("--width", type=int)
    job.add_argument("--height", type=int)
    job.add_argument("--steps", type=int)
    job.add_argument("--latent-window-size", type=int)
    job.add_argument("--cache", choices=["MagCache", "TeaCache", "None"])
    sel = p.add_argument_group("selection")
    sel.add_argument(
        "--only",
        action="append",
        default=[],
        help="key=value or name glob; repeatable, all must match",
    )
    sel.add_argument("--limit", type=int, help="run at most N pending runs")
    sel.add_argument(
        "--dry-run", action="store_true", help="print the plan and time estimate"
    )
    sel.add_argument(
        "--seconds-per-job",
        type=float,
        default=150.0,
        help="for the --dry-run estimate",
    )
    p.add_argument("--fake", action="store_true", help="tiny CPU test models")
    p.add_argument("--offline", action="store_true")
    return p


def _csv(value, cast):
    return [cast(v.strip()) for v in value.split(",") if v.strip()]


def resolve_config(args):
    spec = load_spec(args.spec)
    cases = spec.get("cases") or []
    if args.start_image:
        cases = [
            {
                "name": args.name,
                "start_image": os.path.abspath(args.start_image),
                "guide_video": os.path.abspath(args.guide_video)
                if args.guide_video
                else None,
                "prompt": args.prompt,
            }
        ]
    if not cases:
        raise SystemExit("No cases: pass --spec or --start-image/--guide-video")
    for case in cases:
        missing = [k for k in ("name", "start_image", "guide_video") if not case.get(k)]
        if missing:
            raise SystemExit(f"Case {case.get('name')!r} is missing {missing}")

    grid = dict(DEFAULT_GRID)
    grid.update({k: v for k, v in (spec.get("grid") or {}).items() if k in grid})
    if args.models:
        grid["model_type"] = _csv(args.models, str)
    if args.strengths:
        grid["strength"] = _csv(args.strengths, float)
    if args.starts:
        grid["start"] = _csv(args.starts, float)
    seeds = spec.get("seeds") or DEFAULT_SEEDS
    if args.seeds:
        seeds = _csv(args.seeds, int)
    baseline = spec.get("baseline", True) and not args.no_baseline

    job = dict(DEFAULT_JOB)
    job.update(spec.get("job") or {})
    for key, value in (
        ("total_second_length", args.seconds),
        ("resolutionW", args.width),
        ("resolutionH", args.height),
        ("steps", args.steps),
        ("latent_window_size", args.latent_window_size),
    ):
        if value is not None:
            job[key] = value
    if args.cache:
        job["use_magcache"] = args.cache == "MagCache"
        job["use_teacache"] = args.cache == "TeaCache"

    out_root = os.path.abspath(
        args.out
        or spec.get("output_root")
        or os.path.join(REPO_ROOT, "outputs", "sweep_motion_reference")
    )
    return cases, grid, seeds, baseline, job, out_root


def main(argv=None):
    args = build_parser().parse_args(argv)
    cases, grid, seeds, baseline, job, out_root = resolve_config(args)

    runs = plan_runs(cases, grid, seeds, baseline)
    selected = [r for r in runs if matches(r, args.only)]
    done = [r for r in selected if is_done(out_root, r)]
    pending = [r for r in selected if not is_done(out_root, r)]
    if args.limit is not None:
        pending = pending[: args.limit]

    per_case = len(runs) // len(cases)
    print(
        f"Grid: {len(cases)} case(s) x {per_case} runs = {len(runs)} runs "
        f"({len(grid['model_type'])} models x {len(seeds)} seeds x "
        f"({len(grid['strength'])} strengths x {len(grid['start'])} starts guided"
        f"{' + 1 baseline' if baseline else ''}))"
    )
    print(
        f"Selected {len(selected)}, already done {len(done)}, to run now {len(pending)}"
    )
    hours = len(pending) * args.seconds_per_job / 3600
    print(
        f"Estimate at {args.seconds_per_job:g} s/job: {hours:.1f} h "
        f"({len(pending) * args.seconds_per_job / 60:.0f} min)"
    )
    print(f"Output: {out_root}")
    print(f"Job settings: {json.dumps(job)}")
    if args.dry_run:
        for run in pending[:10]:
            print(f"  {run['name']}")
        if len(pending) > 10:
            print(f"  ... {len(pending) - 10} more")
        return 0

    os.makedirs(out_root, exist_ok=True)
    with open(os.path.join(out_root, "sweep_config.json"), "w") as f:
        json.dump(
            {
                "cases": cases,
                "grid": grid,
                "seeds": seeds,
                "baseline": baseline,
                "job": job,
            },
            f,
            indent=2,
        )

    if not pending:
        print(f"Nothing to run. Wrote {write_csv(out_root, runs)}")
        return 0

    sys.path.insert(0, TOOLS_DIR)
    import run_job

    run_job.configure_logging()
    run_job.load_models(fake=args.fake, offline=args.offline)

    failures = 0
    started = time.time()
    for i, run in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] {run['name']}", flush=True)
        record = run_one(out_root, run, job, args.fake, args.offline)
        if record["status"] == "ok":
            print(f"  done in {record['elapsed']:.1f}s -> {record['video_path']}")
        else:
            failures += 1
            print(f"  FAILED: {record['error'].strip().splitlines()[-1]}")
        write_result(out_root, run, record)
    print(
        f"Finished {len(pending)} run(s) in {(time.time() - started) / 60:.1f} min, "
        f"{failures} failed"
    )
    print(f"Wrote {write_csv(out_root, runs)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
