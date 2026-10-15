"""Finished videos are shown by a frame a third of the way in, not the first."""

import fpshim  # noqa: F401  (must come first)

import os
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from modules import thumbnails  # noqa: E402

FRAMES = 30


@pytest.fixture
def ramp_video(tmp_path):
    """Grey levels 0, 8, 16, ... so a frame's index can be read off its pixels."""
    path = str(tmp_path / "ramp.mp4")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (64, 48))
    for i in range(FRAMES):
        writer.write(np.full((48, 64, 3), i * 8, dtype=np.uint8))
    writer.release()
    return path


def frame_index(frame):
    return round(float(frame.mean()) / 8)


def test_frame_at_one_third(ramp_video):
    frame = thumbnails.frame_at(ramp_video)
    assert frame.shape == (48, 64, 3)
    assert frame_index(frame) == pytest.approx((FRAMES - 1) // 3, abs=1)
    assert frame_index(thumbnails.frame_at(ramp_video, 0)) == 0


def test_data_url(ramp_video):
    url = thumbnails.thumbnail_data_url(ramp_video, size=32)
    assert url.startswith("data:image/png;base64,")


def test_missing_video_gives_none(tmp_path):
    missing = str(tmp_path / "missing.mp4")
    assert thumbnails.frame_at(missing) is None
    assert thumbnails.thumbnail_data_url(missing) is None
    assert thumbnails.save_thumbnail(missing, str(tmp_path / "t.jpg")) is None


def test_library_prefers_the_video_frame(ramp_video, tmp_path):
    from modules.ui import library

    metadata_dir = tmp_path / "meta"
    metadata_dir.mkdir()
    # The saved start image the Library used to show
    cv2.imwrite(str(metadata_dir / "job1.png"), np.zeros((8, 8, 3), np.uint8))
    thumb = library._thumbnail(
        "job1", ramp_video, str(metadata_dir), str(tmp_path / "cache")
    )
    assert thumb.endswith("job1_third.jpg")
    assert frame_index(cv2.imread(thumb)) == pytest.approx((FRAMES - 1) // 3, abs=1)
