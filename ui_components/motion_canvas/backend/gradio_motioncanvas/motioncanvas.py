"""Start-frame canvas for drawing motion arrows (FramePack Studio)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

import numpy as np
from gradio import processing_utils
from gradio.components.base import Component
from gradio.data_classes import FileData, GradioModel
from gradio.events import Events
from PIL import Image


class MotionCanvasData(GradioModel):
    background: Optional[FileData] = None
    arrows: list[list[float]] = []
    camera: str = "None"
    camera_amount: float = 0.0
    enabled: bool = True
    reason: str = ""


class MotionCanvas(Component):
    """Shows a start frame and lets the user drag motion arrows onto it.

    Value (postprocess) is a dict: ``background`` (numpy HxWx3, PIL image, path
    or None), ``arrows`` ([[x0, y0, x1, y1], ...] normalised 0..1), ``camera``,
    ``camera_amount`` (0..1), ``enabled`` and ``reason``. The function input
    (preprocess) is ``{"arrows", "camera", "camera_amount"}``.
    """

    EVENTS = [Events.change, Events.input]
    data_model = MotionCanvasData

    def __init__(
        self,
        value: dict | Callable | None = None,
        *,
        label: str | None = None,
        show_label: bool | None = None,
        container: bool = True,
        scale: int | None = None,
        min_width: int = 160,
        interactive: bool | None = None,
        visible: bool = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        key: int | str | None = None,
    ):
        super().__init__(
            value=value,
            label=label,
            show_label=show_label,
            container=container,
            scale=scale,
            min_width=min_width,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            render=render,
            key=key,
        )

    def preprocess(self, payload: MotionCanvasData | None) -> dict:
        if payload is None:
            return {"arrows": [], "camera": "None", "camera_amount": 0.0}
        return {
            "arrows": [list(a) for a in payload.arrows],
            "camera": payload.camera,
            "camera_amount": payload.camera_amount,
        }

    def postprocess(self, value: dict | None) -> MotionCanvasData | None:
        if value is None:
            return None
        value = dict(value)
        value["background"] = self._background(value.get("background"))
        return MotionCanvasData(**value)

    def _background(self, bg: Any) -> FileData | None:
        if bg is None or isinstance(bg, FileData):
            return bg
        if isinstance(bg, dict):
            return FileData(**bg)
        if isinstance(bg, np.ndarray):
            path = processing_utils.save_img_array_to_cache(
                bg, cache_dir=self.GRADIO_CACHE, format="png"
            )
        elif isinstance(bg, Image.Image):
            path = processing_utils.save_pil_to_cache(
                bg, cache_dir=self.GRADIO_CACHE, format="png"
            )
        else:
            path = str(Path(bg))
        return FileData(path=path)

    def example_payload(self) -> Any:
        return {
            "arrows": [[0.3, 0.5, 0.6, 0.5]],
            "camera": "None",
            "camera_amount": 0.0,
        }

    def example_value(self) -> Any:
        return {"background": None, "arrows": [[0.3, 0.5, 0.6, 0.5]]}
