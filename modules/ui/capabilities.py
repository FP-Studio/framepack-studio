"""
What each model can do, in one place.

The UI picks a model ("Original" or "F1") and a source ("Image" or "Video").
Everything stored on disk (presets, metadata, queue files, section
checkpoints) and the worker itself still use the six legacy model_type
strings, so this module converts between the two at the UI boundary.

Feature support comes from the pipelines' own *_MODEL_TYPES constants, so
the UI can't drift from what the worker actually accepts.
"""

from modules.pipelines import flow_noise, keyframes, motion_reference
from modules.pipelines import section_checkpoint

MODELS = ("Original", "F1")
SOURCES = ("Image", "Video")

# (model, source) -> legacy model_type without an end frame
_BASE_TYPES = {
    ("Original", "Image"): "Original",
    ("F1", "Image"): "F1",
    ("Original", "Video"): "Video",
    ("F1", "Video"): "Video F1",
}
# Legacy types that carry an end frame
_END_FRAME_TYPES = {
    "Original": "Original with Endframe",
    "Video": "Video with Endframe",
}

FEATURE_LABELS = {
    "end_frame": "End frame",
    "keyframes": "Keyframes",
    "motion_sketch": "Camera moves and arrows",
    "motion_reference": "Motion reference",
    "reroll": "Section re-roll",
    "batch": "Batch from images",
}

# Legacy model types each feature works with
_FEATURE_TYPES = {
    "end_frame": tuple(_END_FRAME_TYPES.values()),
    "keyframes": keyframes.KEYFRAME_MODEL_TYPES,
    "motion_sketch": flow_noise.FLOW_NOISE_MODEL_TYPES,
    "motion_reference": motion_reference.MOTION_REFERENCE_MODEL_TYPES,
    "reroll": section_checkpoint.REROLL_MODEL_TYPES,
    "batch": ("Original", "Original with Endframe", "F1"),
}


def to_legacy(model, source, has_end_frame=False):
    """Legacy model_type string for a model/source pair."""
    base = _BASE_TYPES[(model, source)]
    if has_end_frame and base in _END_FRAME_TYPES:
        return _END_FRAME_TYPES[base]
    return base


def from_legacy(model_type):
    """(model, source) for a legacy model_type string. Unknown -> Original/Image."""
    model_type = (model_type or "").replace(" with Endframe", "")
    for pair, legacy in _BASE_TYPES.items():
        if legacy == model_type:
            return pair
    return ("Original", "Image")


def backend_model_type(model_type):
    """The worker treats "Video with Endframe" as plain "Video"."""
    return "Video" if model_type == "Video with Endframe" else model_type


def supports(feature, model, source):
    types = _FEATURE_TYPES[feature]
    base = _BASE_TYPES[(model, source)]
    return base in types or _END_FRAME_TYPES.get(base) in types


def supported_setups(feature):
    """Human list of the model/source pairs a feature works with."""
    setups = [
        f"{model} with a video" if source == "Video" else model
        for (model, source) in _BASE_TYPES
        if supports(feature, model, source)
    ]
    if len(setups) <= 1:
        return "".join(setups)
    return ", ".join(setups[:-1]) + " or " + setups[-1]


def unsupported_reason(feature, model, source):
    """One-line reason a feature is unavailable, or "" if it is supported."""
    if supports(feature, model, source):
        return ""
    return f"{FEATURE_LABELS[feature]} only works with {supported_setups(feature)}."
