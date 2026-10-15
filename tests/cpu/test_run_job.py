"""Headless runner (tools/run_job.py) and motion reference sweep, with fake models."""

import json
import os
import sys

import av
import numpy as np
import pytest
from PIL import Image

import fpharness
from test_motion_reference import make_video

sys.path.insert(0, os.path.join(fpharness.REPO_ROOT, "tools"))

import run_job as rj  # noqa: E402
import sweep_motion_reference as sweep  # noqa: E402

TINY = dict(
    total_second_length=2,
    resolutionW=64,
    resolutionH=64,
    steps=3,
    latent_window_size=3,
)


@pytest.fixture(autouse=True)
def restore_studio_state():
    from modules.studio_manager import StudioManager

    sm = StudioManager()
    saved = dict(sm.settings.settings)
    yield
    sm.settings.settings.clear()
    sm.settings.settings.update(saved)
    sm.unset_current_generator()


@pytest.fixture(scope="module")
def assets(tmp_path_factory):
    folder = tmp_path_factory.mktemp("assets")
    image = str(folder / "start.png")
    Image.fromarray(fpharness.default_image(96, 128)).save(image)
    guide = make_video(str(folder / "guide.mp4"), seconds=2.5)
    return {"image": image, "guide": guide}


@pytest.fixture
def sampler_calls(monkeypatch):
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    calls = []
    real = kdh.sample_hunyuan

    def sample(**kwargs):
        calls.append(
            {
                "strength": kwargs.get("strength"),
                "initial_latent": kwargs.get("initial_latent") is not None,
                "noise": kwargs.get("noise") is not None,
            }
        )
        return real(**kwargs)

    monkeypatch.setattr(kdh, "sample_hunyuan", sample)
    return calls


@pytest.fixture
def reference_reads(monkeypatch):
    from modules.pipelines import motion_reference

    reads = []
    real = motion_reference.read_video_frames

    def read(*args, **kwargs):
        reads.append(kwargs.get("start_seconds"))
        return real(*args, **kwargs)

    monkeypatch.setattr(motion_reference, "read_video_frames", read)
    return reads


def read_frames(path):
    with av.open(path) as container:
        return np.stack(
            [f.to_ndarray(format="rgb24") for f in container.decode(video=0)]
        )


@pytest.mark.parametrize("model_type", ["Original", "F1"])
@pytest.mark.parametrize("guided", [False, True])
def test_run_job_writes_video(
    model_type, guided, assets, sampler_calls, reference_reads, tmp_path
):
    params = dict(TINY, model_type=model_type, input_image=assets["image"], seed=7)
    if guided:
        params.update(guide_video=assets["guide"], strength=0.6, start=0.5)
    result = rj.run_job(output_dir=str(tmp_path), fake=True, verbose=False, **params)

    assert os.path.exists(result["video_path"])
    assert result["video_path"].startswith(str(tmp_path))
    assert read_frames(result["video_path"]).shape[0] > 30
    assert result["metadata_path"] and os.path.exists(result["metadata_path"])
    assert result["elapsed"] > 0
    assert sampler_calls
    # The reference steers through the starting latent only, never the noise.
    assert not any(c["noise"] for c in sampler_calls)
    if guided:
        # Each section starts from the reference and skips 0.5 * strength of
        # the steps.
        assert all(c["initial_latent"] for c in sampler_calls)
        assert all(c["strength"] == pytest.approx(1 - 0.5 * 0.6) for c in sampler_calls)
        assert reference_reads == [0.5]
    else:
        assert not any(c["initial_latent"] for c in sampler_calls)
        assert reference_reads == []


def test_same_seed_repeats_and_transformer_is_reused(assets, tmp_path, monkeypatch):
    from modules.generators.base_generator import BaseModelGenerator

    loads = []
    for cls in fpharness._all_subclasses(BaseModelGenerator):
        real = cls.load_model

        def counted(self, real=real):
            loads.append(self.model_name)
            return real(self)

        monkeypatch.setattr(cls, "load_model", counted)

    params = dict(TINY, model_type="F1", input_image=assets["image"], seed=3)
    a = rj.run_job(output_dir=str(tmp_path / "a"), fake=True, verbose=False, **params)
    b = rj.run_job(output_dir=str(tmp_path / "b"), fake=True, verbose=False, **params)
    assert np.array_equal(read_frames(a["video_path"]), read_frames(b["video_path"]))
    assert loads == ["F1"]  # second job reused the loaded transformer


def test_worker_error_raises(assets, tmp_path):
    with pytest.raises(RuntimeError):
        rj.run_job(
            output_dir=str(tmp_path),
            fake=True,
            verbose=False,
            **dict(TINY, model_type="F1", input_image=assets["image"], steps=0),
        )


@pytest.mark.parametrize(
    "key", ["stength", "detail", "grayscale", "motion_reference_detail"]
)
def test_unknown_param_rejected(key):
    with pytest.raises(TypeError):
        rj.normalize_params({key: 0.5})


def test_motion_reference_defaults_and_aliases():
    params = rj.normalize_params({"strength": 0.75, "start": 1.5})
    assert params["motion_reference_strength"] == 0.75
    assert params["motion_reference_start"] == 1.5
    defaults = rj.normalize_params({})
    assert defaults["motion_reference_strength"] == 0.5
    assert defaults["motion_reference_start"] == 0.0
    args = rj.build_parser().parse_args(["--strength", "0.3", "--start", "2"])
    assert args.motion_reference_strength == 0.3
    assert args.motion_reference_start == 2.0


def test_sweep_plan_counts():
    cases = [{"name": "a", "start_image": "s.png", "guide_video": "g.mp4"}]
    runs = sweep.plan_runs(cases, sweep.DEFAULT_GRID, sweep.DEFAULT_SEEDS)
    assert len(runs) == 2 * 3 * (4 * 1 + 1)
    assert len({r["name"] for r in runs}) == len(runs)
    models = [r["model_type"] for r in runs]
    assert models == sorted(models, key=["Original", "F1"].index)  # one switch
    f1_start0 = [r for r in runs if sweep.matches(r, ["model_type=F1", "start=0"])]
    assert len(f1_start0) == 3 * 4  # guided runs only; baselines have no start
    assert "a__F1__s0.5_t0__seed2500" in {r["name"] for r in runs}


def test_sweep_runs_and_resumes(assets, tmp_path, capsys):
    out = tmp_path / "sweep"
    argv = [
        "--start-image", assets["image"],
        "--guide-video", assets["guide"],
        "--name", "sq",
        "--out", str(out),
        "--fake",
        "--seconds", "2", "--width", "64", "--height", "64",
        "--steps", "2", "--latent-window-size", "3",
        "--models", "F1", "--strengths", "0.5", "--starts", "0.5",
        "--seeds", "1,2",
    ]  # fmt: skip
    assert sweep.main(argv + ["--limit", "3"]) == 0
    rows = [json.loads(line) for line in open(out / "results.jsonl")]
    assert len(rows) == 3 and all(r["status"] == "ok" for r in rows)

    capsys.readouterr()
    assert sweep.main(argv + ["--dry-run"]) == 0
    assert "already done 3, to run now 1" in capsys.readouterr().out
    assert sweep.main(argv) == 0
    assert len(open(out / "results.jsonl").readlines()) == 4
    assert len(open(out / "results.csv").readlines()) == 5  # header + 4 runs
