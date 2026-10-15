"""Job metadata, "Use these settings" and the queue keep every job setting."""

import inspect
import json
import os
import shutil
import sys

import numpy as np
import pytest
from PIL import Image

import fpharness
from test_motion_reference import make_video

sys.path.insert(0, os.path.join(fpharness.REPO_ROOT, "tools"))

import run_job as rj  # noqa: E402
from modules import video_queue  # noqa: E402
from modules.pipelines.worker import worker  # noqa: E402
from modules.ui.create import (  # noqa: E402
    NUM_KEYFRAME_SLOTS,
    restore_targets,
    settings_from_metadata,
)
from modules.ui.library import summary_html  # noqa: E402

KEYFRAMES = [fpharness.default_image(seed=5), fpharness.default_image(seed=6)]
NEW_TARGETS = [
    "input_image",
    "end_frame_image",
    "input_video",
    *[f"keyframe_image_{i}" for i in range(NUM_KEYFRAME_SLOTS)],
    *[f"keyframe_time_{i}" for i in range(NUM_KEYFRAME_SLOTS)],
    "motion_reference_video",
    "motion_reference_strength",
    "motion_reference_start",
    "motion_canvas",
    "camera",
    "camera_amount",
    "flow_strength",
]
WORKER_PARAMS = set(inspect.signature(worker).parameters)


class _Names(dict):
    def __missing__(self, key):
        return key


def restored(meta, lora_names=()):
    """{component name: update} from settings_from_metadata."""
    g = _Names(
        keyframe_images=[f"keyframe_image_{i}" for i in range(NUM_KEYFRAME_SLOTS)],
        keyframe_times=[f"keyframe_time_{i}" for i in range(NUM_KEYFRAME_SLOTS)],
        lora_slider_list=[f"lora:{n}" for n in lora_names],
    )
    targets = restore_targets(g)
    updates = settings_from_metadata(meta, list(lora_names))
    assert len(targets) == len(updates)
    return dict(zip(targets, updates))


def is_noop(update):
    return update == {"__type__": "update"}


@pytest.fixture(autouse=True)
def restore_studio_state():
    from modules.studio_manager import StudioManager

    sm = StudioManager()
    saved = dict(sm.settings.settings)
    yield
    sm.settings.settings.clear()
    sm.settings.settings.update(saved)
    sm.unset_current_generator()


@pytest.fixture
def ref_video(tmp_path):
    """A motion reference clip from somewhere outside the app's folders."""
    folder = tmp_path / "refs"
    folder.mkdir(parents=True)
    return make_video(str(folder / "guide.mp4"), seconds=2.5)


# ------------------------------------------------------------- job metadata


def test_job_metadata_records_and_restores_new_settings(tmp_path, ref_video):
    from modules.studio_manager import StudioManager

    StudioManager().settings.settings["input_files_dir"] = str(tmp_path / "inputs")
    out = tmp_path / "out"
    result = rj.run_job(
        output_dir=str(out),
        fake=True,
        verbose=False,
        model_type="Original",
        input_image=fpharness.default_image(),
        total_second_length=2,
        latent_window_size=3,
        steps=3,
        resolutionW=64,
        resolutionH=64,
        keyframe_images=KEYFRAMES,
        keyframe_times=[0.8, 1.2],
        motion_reference_video=ref_video,
        motion_reference_strength=0.6,
        motion_reference_start=0.5,
        flow_noise_arrows=[(0.2, 0.5, 0.6, 0.5)],
        flow_noise_camera="Pan left",
        flow_noise_camera_amount=0.4,
        flow_noise_strength=0.0,  # recorded, but leaves the noise alone
    )
    with open(result["metadata_path"]) as f:
        meta = json.load(f)

    assert meta["keyframe_times"] == [0.8, 1.2]
    files = meta["keyframe_image_files"]
    assert len(files) == 2 and all(os.path.dirname(p) == str(out) for p in files)
    for path, image in zip(files, KEYFRAMES):
        assert np.array_equal(np.array(Image.open(path)), image)
    assert meta["motion_reference_video"] == ref_video
    assert meta["motion_reference_strength"] == 0.6
    assert meta["motion_reference_start"] == 0.5
    # The reference is kept with the metadata, out of the Library's sight
    copy = meta["motion_reference_file"]
    assert copy == str(out / "reference_clips" / f"{result['job_id']}.mp4")
    assert open(copy, "rb").read() == open(ref_video, "rb").read()
    assert meta["flow_noise_arrows"] == [[0.2, 0.5, 0.6, 0.5]]
    assert meta["flow_noise_camera"] == "Pan left"
    assert meta["flow_noise_camera_amount"] == 0.4
    assert meta["flow_noise_strength"] == 0.0
    assert meta["save_section_latents"] is False  # run_job's default
    assert meta["reroll_latents_path"] is None and meta["reroll_from_section"] is None
    assert meta["start_image_file"] == str(out / f"{result['job_id']}.png")
    assert meta["end_frame_image_file"] is None
    assert meta["input_video_file"] is None

    # "Use these settings" brings it all back
    u = restored(meta)
    # The start frame as the job used it (resized to its bucket)
    start = u["input_image"]["value"]
    assert np.array_equal(start, np.array(Image.open(meta["start_image_file"])))
    for i, image in enumerate(KEYFRAMES):
        assert np.array_equal(u[f"keyframe_image_{i}"]["value"], image)
    assert u["keyframe_time_0"]["value"] == 0.8
    assert u["keyframe_time_1"]["value"] == 1.2
    assert u["keyframe_image_2"]["value"] is None  # unused slot emptied
    assert u["end_frame_image"]["value"] is None
    assert u["input_video"]["value"] is None
    assert u["motion_reference_video"]["value"] == copy
    assert u["motion_reference_strength"]["value"] == 0.6
    assert u["motion_reference_start"]["value"] == 0.5
    assert u["camera"]["value"] == "Pan left"
    assert u["camera_amount"]["value"] == 0.4
    assert u["flow_strength"]["value"] == 0.0
    assert u["motion_canvas"]["value"]["arrows"] == [[0.2, 0.5, 0.6, 0.5]]

    html = summary_html(result["job_id"], result["video_path"], meta)
    assert "0.8 s, 1.2 s" in html and "guide.mp4" in html

    # Once the original reference is gone, the kept copy still restores
    os.remove(ref_video)
    assert restored(meta)["motion_reference_video"]["value"] == copy


def test_old_metadata_restores_as_before():
    old = {
        "app_version": "0.9",
        "prompt": "a cat",
        "negative_prompt": "",
        "seed": 31337,
        "steps": 25,
        "cfg": 1.0,
        "gs": 10.0,
        "rs": 0.0,
        "latent_type": "Black",
        "timestamp": 1700000000.0,
        "resolutionW": 640,
        "resolutionH": 640,
        "model_type": "Original",
        "generation_type": "Original",
        "has_input_image": True,
        "input_image_path": None,
        "total_second_length": 6,
        "blend_sections": 4,
        "latent_window_size": 9,
        "num_cleaned_frames": 5,
        "end_frame_strength": None,
        "end_frame_image_path": None,
        "end_frame_used": "False",
        "input_video": None,
        "video_path": None,
        "combine_with_source": False,
        "use_teacache": False,
        "teacache_num_steps": 0,
        "teacache_rel_l1_thresh": 0.0,
        "use_magcache": True,
        "magcache_threshold": 0.1,
        "magcache_max_consecutive_skips": 2,
        "magcache_retention_ratio": 0.25,
        "loras": {"style": 0.8},
    }
    u = restored(old, lora_names=["style", "other"])
    for name in NEW_TARGETS:
        assert is_noop(u[name]), name
    assert u["prompt"]["value"] == "a cat"
    assert u["seed"]["value"] == 31337
    assert u["cache_type"]["value"] == "MagCache"
    assert u["lora_selector"]["value"] == ["style"]
    assert u["lora:style"] == {"__type__": "update", "value": 0.8, "visible": True}
    assert u["lora:other"] == {"__type__": "update", "visible": False}
    assert "Keyframes" not in summary_html("job", "job.mp4", old)


# -------------------------------------------------------------------- queue


@pytest.fixture
def job_queue(tmp_path, monkeypatch):
    """A VideoJobQueue that doesn't run jobs, with every folder under tmp_path."""
    monkeypatch.chdir(tmp_path)
    settings = {
        "save_metadata": False,  # queue files still need the settings
        "output_dir": str(tmp_path / "outputs"),
        "metadata_dir": str(tmp_path / "outputs"),
        "input_files_dir": str(tmp_path / "input_files"),
        "lora_dir": str(tmp_path / "loras"),
    }

    class FakeSettings:
        def __init__(self):
            self.settings = settings

        def get(self, key, default=None):
            return self.settings.get(key, default)

    monkeypatch.setattr(video_queue, "Settings", FakeSettings)
    monkeypatch.setattr(video_queue.VideoJobQueue, "_worker_loop", lambda self: None)
    monkeypatch.setattr(video_queue.VideoJobQueue, "_instance", None)

    def fresh():
        video_queue.VideoJobQueue._instance = None
        return video_queue.VideoJobQueue()

    yield fresh
    video_queue.VideoJobQueue._instance = None


def queued_params(tmp_path, reference_video):
    return {
        "model_type": "Original",
        "input_image": fpharness.default_image(),
        "end_frame_image": None,
        "end_frame_strength": 1.0,
        "prompt_text": "a dancer",
        "n_prompt": "",
        "seed": 99,
        "total_second_length": 4,
        "latent_window_size": 9,
        "latent_type": "Noise",
        "steps": 20,
        "cfg": 1.0,
        "gs": 10.0,
        "rs": 0.0,
        "blend_sections": 4,
        "use_teacache": False,
        "teacache_num_steps": 25,
        "teacache_rel_l1_thresh": 0.15,
        "use_magcache": True,
        "magcache_threshold": 0.1,
        "magcache_max_consecutive_skips": 2,
        "magcache_retention_ratio": 0.25,
        "selected_loras": [],
        "has_input_image": True,
        "output_dir": str(tmp_path / "outputs"),
        "metadata_dir": str(tmp_path / "outputs"),
        "input_files_dir": str(tmp_path / "input_files"),
        "input_image_path": None,
        "end_frame_image_path": None,
        "resolutionW": 640,
        "resolutionH": 640,
        "lora_loaded_names": [],
        "combine_with_source": False,
        "num_cleaned_frames": 7,
        "save_metadata_checked": True,
        "save_section_latents": True,
        "reroll_latents_path": None,
        "reroll_from_section": None,
        "keyframe_images": KEYFRAMES,
        "keyframe_times": [1.2, 2.4],
        "motion_reference_video": reference_video,
        "motion_reference_strength": 0.65,
        "motion_reference_start": 0.75,
        "flow_noise_arrows": [(0.1, 0.2, 0.3, 0.4)],
        "flow_noise_camera": "Zoom in",
        "flow_noise_camera_amount": 0.2,
        "flow_noise_strength": 0.5,
    }


def check_loaded(params, reference_video):
    assert set(params) <= WORKER_PARAMS  # the queue calls worker(**params)
    assert len(params["keyframe_images"]) == 2
    for loaded, image in zip(params["keyframe_images"], KEYFRAMES):
        assert np.array_equal(loaded, image)
    assert params["keyframe_times"] == [1.2, 2.4]
    assert os.path.isfile(params["motion_reference_video"])
    with (
        open(params["motion_reference_video"], "rb") as a,
        open(reference_video, "rb") as b,
    ):
        assert a.read() == b.read()
    assert params["motion_reference_strength"] == 0.65
    assert params["motion_reference_start"] == 0.75
    assert params["flow_noise_arrows"] == [(0.1, 0.2, 0.3, 0.4)]
    assert params["flow_noise_camera"] == "Zoom in"
    assert params["flow_noise_camera_amount"] == 0.2
    assert params["flow_noise_strength"] == 0.5
    assert params["num_cleaned_frames"] == 7
    assert params["save_section_latents"] is True
    assert params["input_image"].shape == (64, 64, 3)


def test_queue_save_and_load_round_trip(tmp_path, job_queue):
    (tmp_path / "input_files").mkdir()
    ref = make_video(str(tmp_path / "input_files" / "251013_ref.mp4"), seconds=1)
    q = job_queue()
    job_id = q.add_job(queued_params(tmp_path, ref))
    with open("queue.json") as f:
        saved = json.load(f)[job_id]
    assert saved["saved_keyframe_image_paths"] == [
        os.path.join("queue_images", f"{job_id}_keyframe_{i}.png") for i in (1, 2)
    ]
    assert saved["motion_reference_video"] == ref

    q = job_queue()
    assert q.load_queue_from_json("queue.json") == 1
    check_loaded(q.get_job(job_id).params, ref)
    assert q.get_job(job_id).keyframe_images_saved
    assert os.path.exists(ref)  # still referenced, so not cleaned up

    # Removing the job removes its keyframe images too
    q.get_job(job_id).status = video_queue.JobStatus.CANCELLED
    assert q.remove_job(job_id)
    assert not [n for n in os.listdir("queue_images") if "_keyframe_" in n]


def test_export_and_import_on_another_machine(tmp_path, job_queue, ref_video):
    q = job_queue()
    job_id = q.add_job(queued_params(tmp_path, ref_video))
    original = tmp_path / "original.mp4"
    shutil.copy(ref_video, original)
    zip_path = q.export_queue_to_zip(str(tmp_path / "export.zip"))
    assert zip_path

    # Another machine: none of this machine's files
    os.remove("queue.json")
    for folder in ("queue_images", "input_files", "refs"):
        shutil.rmtree(folder, ignore_errors=True)
    assert not os.path.exists(ref_video)

    q = job_queue()
    assert q.load_queue_from_json(zip_path) == 1
    params = q.get_job(job_id).params
    assert params["motion_reference_video"] == os.path.join("input_files", "guide.mp4")
    check_loaded(params, str(original))
    assert not os.path.exists("temp_queue_import")


def test_old_queue_file_still_loads(tmp_path, job_queue):
    os.makedirs("queue_images")
    Image.fromarray(fpharness.default_image()).save("queue_images/old_input.png")
    old = {
        "old": {
            "prompt": "a boat",
            "negative_prompt": "",
            "seed": 5,
            "steps": 25,
            "cfg": 1.0,
            "gs": 10.0,
            "rs": 0.0,
            "latent_type": "Noise",
            "resolutionW": 640,
            "resolutionH": 640,
            "model_type": "Original",
            "has_input_image": True,
            "total_second_length": 6,
            "blend_sections": 4,
            "latent_window_size": 9,
            "use_magcache": True,
            "magcache_threshold": 0.1,
            "magcache_max_consecutive_skips": 2,
            "magcache_retention_ratio": 0.25,
            "loras": {},
            "id": "old",
            "status": "pending",
            "created_at": 1700000000.0,
            "saved_input_image_path": "queue_images/old_input.png",
        }
    }
    with open("old_queue.json", "w") as f:
        json.dump(old, f)
    q = job_queue()
    assert q.load_queue_from_json("old_queue.json") == 1
    params = q.get_job("old").params
    assert set(params) <= WORKER_PARAMS
    defaults = inspect.signature(worker).parameters
    for key in (
        "keyframe_images",
        "keyframe_times",
        "motion_reference_video",
        "motion_reference_strength",
        "motion_reference_start",
        "flow_noise_arrows",
        "flow_noise_camera",
        "flow_noise_camera_amount",
        "flow_noise_strength",
        "save_section_latents",
        "reroll_latents_path",
        "reroll_from_section",
        "num_cleaned_frames",
    ):
        assert params[key] == defaults[key].default, key
    assert params["prompt_text"] == "a boat"
    assert params["input_image"].shape == (64, 64, 3)
