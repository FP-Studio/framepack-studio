"""
Generation presets.

Stored in .framepack/generation_presets.json keyed by legacy model_type
(e.g. "Original", "Original with Endframe"), exactly as before. The UI asks
by model and source, so "Original" and "Original with Endframe" presets
show up together.
"""

import json
import os

from modules.ui import capabilities as caps

PRESET_FILE = os.path.join(".framepack", "generation_presets.json")


def _read():
    if not os.path.isfile(PRESET_FILE):
        return {}
    try:
        with open(PRESET_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _write(data):
    os.makedirs(os.path.dirname(PRESET_FILE), exist_ok=True)
    with open(PRESET_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _keys(model, source):
    base = caps.to_legacy(model, source)
    return [base, caps.to_legacy(model, source, has_end_frame=True)]


def load_presets(model_type):
    """Preset names for a legacy model_type (used by Settings > Startup)."""
    model, source = caps.from_legacy(model_type)
    return list_presets(model, source)


def list_presets(model, source):
    data = _read()
    names = []
    for key in dict.fromkeys(_keys(model, source)):
        names.extend(n for n in data.get(key, {}) if n not in names)
    return names


def get_preset(model, source, name):
    data = _read()
    for key in _keys(model, source):
        if name in data.get(key, {}):
            return data[key][name]
    return None


def save_preset(model, source, name, values):
    data = _read()
    key = caps.to_legacy(model, source)
    data.setdefault(key, {})[name] = values
    _write(data)


def delete_preset(model, source, name):
    data = _read()
    for key in _keys(model, source):
        data.get(key, {}).pop(name, None)
    _write(data)
