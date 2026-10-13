"""Section timeline with draggable keyframe markers (FramePack Studio)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from gradio.components.base import Component
from gradio.events import Events

EXAMPLE = {
    "duration": 6.0,
    "direction": "backward",
    "sections": [
        {"start": 0.0, "end": 3.0, "order": 2, "state": "normal"},
        {"start": 3.0, "end": 6.0, "order": 1, "state": "normal"},
    ],
    "prompts": [{"start": 0.0, "end": 6.0, "text": "A person waves"}],
    "blend": 0.0,
    "frames": [
        {"kind": "start", "t": 0.0, "label": "Start", "set": True},
        {"kind": "end", "t": 6.0, "label": "End", "set": False},
    ],
    "lanes": [],
    "keyframes_enabled": True,
    "keyframes_reason": "",
    "selected_section": None,
    "selectable": False,
}


class Timeline(Component):
    """Draws a section-based video timeline; the app does all of the maths.

    The value is a plain dict (see EXAMPLE). Edits made in the browser (dragging
    keyframes, selecting a section) come back as the same dict.
    """

    EVENTS = [Events.change, Events.input, Events.select]

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

    def preprocess(self, payload: dict | None) -> dict | None:
        return payload

    def postprocess(self, value: dict | None) -> dict | None:
        return value

    def api_info(self) -> dict[str, Any]:
        return {"type": "object"}

    def example_payload(self) -> Any:
        return EXAMPLE

    def example_value(self) -> Any:
        return EXAMPLE
