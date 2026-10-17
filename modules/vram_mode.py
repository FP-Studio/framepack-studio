"""
How much of the GPU Studio's models may keep, chosen once at startup.

- high: every model stays on the GPU (60 GB+ free).
- medium: the transformer is stored in fp8 (about 13 GB) and stays on the
  GPU for the whole job; the text encoders, image encoder and VAE are swapped
  in and out as in low mode. Fits 24 GB cards and up.
- low: the transformer is streamed from system RAM as needed.

The "vram_mode" setting picks one ("auto" by default, which chooses from the
free VRAM). Changing it needs a restart.
"""

import logging

logger = logging.getLogger(__name__)

HIGH, MEDIUM, LOW, AUTO = "high", "medium", "low", "auto"
CHOICES = (AUTO, HIGH, MEDIUM, LOW)
HIGH_MIN_FREE_GB = 60
# fp8 transformer (~13 GB) plus room for activations and the VAE decode
MEDIUM_MIN_FREE_GB = 20

_mode = LOW


def choose(free_gb, requested=AUTO):
    """The mode for this much free VRAM; an explicit request wins over auto."""
    if requested in (HIGH, MEDIUM, LOW):
        return requested
    if free_gb > HIGH_MIN_FREE_GB:
        return HIGH
    if free_gb >= MEDIUM_MIN_FREE_GB:
        return MEDIUM
    return LOW


def set_mode(mode):
    global _mode
    _mode = mode
    logger.info(f"VRAM mode: {mode}")


def get():
    return _mode


def transformer_stays_on_gpu():
    """Medium mode: the transformer is loaded to the GPU once and kept there."""
    return _mode == MEDIUM
