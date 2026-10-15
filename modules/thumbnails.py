"""
Thumbnails for finished videos.

The first frame of a generated video is just the start image, so finished
jobs are shown by a frame a third of the way in instead.
"""

import base64
import io
import logging

logger = logging.getLogger(__name__)

THUMBNAIL_POSITION = 1 / 3


def frame_at(video_path, position=THUMBNAIL_POSITION):
    """RGB uint8 frame at `position` (0..1) of the video, or None."""
    import cv2

    capture = cv2.VideoCapture(str(video_path))
    try:
        count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if count > 1:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int((count - 1) * position))
        ok, frame = capture.read()
        if not ok and count > 1:
            # Some containers can't seek; fall back to the first frame
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = capture.read()
    finally:
        capture.release()
    if not ok:
        return None
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def save_thumbnail(video_path, out_path, position=THUMBNAIL_POSITION):
    """Write the frame at `position` to out_path. Returns out_path or None."""
    from PIL import Image

    try:
        frame = frame_at(video_path, position)
        if frame is None:
            return None
        Image.fromarray(frame).save(out_path)
        return out_path
    except Exception as e:
        logger.debug(f"No thumbnail for {video_path}: {e}")
        return None


def thumbnail_data_url(video_path, size=150, position=THUMBNAIL_POSITION):
    """PNG data URL of the frame at `position`, at most size x size, or None."""
    from PIL import Image

    try:
        frame = frame_at(video_path, position)
        if frame is None:
            return None
        image = Image.fromarray(frame)
        image.thumbnail((size, size))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        logger.debug(f"No thumbnail for {video_path}: {e}")
        return None
