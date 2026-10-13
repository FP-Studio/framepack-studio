import pytest

from modules.ui import capabilities as caps

LEGACY = [
    "Original",
    "Original with Endframe",
    "F1",
    "Video",
    "Video with Endframe",
    "Video F1",
]


@pytest.mark.parametrize("legacy", LEGACY)
def test_legacy_round_trip(legacy):
    model, source = caps.from_legacy(legacy)
    assert caps.to_legacy(model, source, "Endframe" in legacy) == legacy


def test_end_frame_only_adds_suffix_where_supported():
    assert caps.to_legacy("F1", "Image", has_end_frame=True) == "F1"
    assert caps.to_legacy("F1", "Video", has_end_frame=True) == "Video F1"
    assert caps.to_legacy("Original", "Image", has_end_frame=False) == "Original"


def test_unknown_legacy_falls_back():
    assert caps.from_legacy("XY Plot") == ("Original", "Image")
    assert caps.from_legacy(None) == ("Original", "Image")


def test_backend_model_type():
    assert caps.backend_model_type("Video with Endframe") == "Video"
    assert caps.backend_model_type("Original with Endframe") == "Original with Endframe"


def test_matrix_matches_pipelines():
    expected = {
        # feature: {(model, source): supported}
        "end_frame": {"OI": 1, "FI": 0, "OV": 1, "FV": 0},
        "keyframes": {"OI": 1, "FI": 0, "OV": 0, "FV": 0},
        "motion_sketch": {"OI": 1, "FI": 1, "OV": 0, "FV": 0},
        "motion_reference": {"OI": 1, "FI": 1, "OV": 0, "FV": 0},
        "reroll": {"OI": 1, "FI": 1, "OV": 0, "FV": 0},
        "batch": {"OI": 1, "FI": 1, "OV": 0, "FV": 0},
    }
    names = {"O": "Original", "F": "F1", "I": "Image", "V": "Video"}
    for feature, cells in expected.items():
        for key, want in cells.items():
            model, source = names[key[0]], names[key[1]]
            assert caps.supports(feature, model, source) == bool(want), (
                feature,
                key,
            )


def test_reasons():
    assert caps.unsupported_reason("keyframes", "Original", "Image") == ""
    assert (
        caps.unsupported_reason("keyframes", "F1", "Image")
        == "Keyframes only works with Original."
    )
    assert (
        caps.unsupported_reason("end_frame", "F1", "Image")
        == "End frame only works with Original or Original with a video."
    )
