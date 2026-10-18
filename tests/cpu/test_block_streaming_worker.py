"""A low VRAM job with offload_engine "streamed" matches a high VRAM one."""

import copy
import sys
import weakref

import pytest
import torch

import fpharness
import diffusers_helper.memory as memory
from modules.generators.base_generator import BaseModelGenerator
from modules.studio_manager import StudioManager


@pytest.fixture
def low_vram_streamed(monkeypatch):
    """Call the returned function to switch later runs to low VRAM mode with
    block streaming; it returns weak references to the streamers the
    generators create (the tests mustn't keep them alive)."""
    real_install = fpharness._install_globals
    real_patch = fpharness._patch_cpu
    streamers = []

    def install(stream, vae):
        real_install(stream, vae)
        main = sys.modules["__main__"]
        main.high_vram = False
        # Low mode moves the encoders around, so they can't be None
        for name in ("text_encoder", "text_encoder_2", "image_encoder"):
            setattr(main, name, torch.nn.Linear(1, 1))

    def load_model(self):
        # A copy, so the hooks don't stay on the shared tiny transformer
        self.transformer = copy.deepcopy(fpharness.tiny_transformer())
        self.place_transformer()
        streamers.append(weakref.ref(self.block_streamer))
        return self.transformer

    def patch():
        worker_mod = real_patch()
        for cls in fpharness._all_subclasses(BaseModelGenerator):
            monkeypatch.setattr(cls, "load_model", load_model)
        return worker_mod

    def enable():
        monkeypatch.setattr(fpharness, "_install_globals", install)
        monkeypatch.setattr(fpharness, "_patch_cpu", patch)
        # No free VRAM: every block is streamed
        monkeypatch.setattr(memory, "get_cuda_free_memory_gb", lambda device=None: 0.0)
        monkeypatch.setitem(
            StudioManager().settings.settings, "offload_engine", "streamed"
        )
        return streamers

    yield enable
    for ref in streamers:
        if ref() is not None:
            ref().close()


@pytest.mark.parametrize("model_type", ["F1", "Original"])
def test_streamed_job_matches_high_vram(model_type, low_vram_streamed):
    expected = fpharness.run(model_type)
    assert not expected["errors"]
    streamers = low_vram_streamed()
    got = fpharness.run(model_type)
    assert not got["errors"], got["errors"]

    streamer = streamers[-1]()
    assert streamer is not None
    assert streamer.n_resident == 0
    assert streamer.copy_log, "blocks should have been streamed"
    assert not streamer.prepared, "released before the last VAE decode"

    assert len(got["calls"]) == len(expected["calls"])
    assert len(got["videos"]) == len(expected["videos"]) > 0
    for a, b in zip(got["videos"], expected["videos"]):
        assert torch.equal(a[1], b[1])


def test_old_transformer_freed_before_the_next_load(low_vram_streamed, monkeypatch):
    # A LoRA change (or reuse_model_instance off) makes the worker build a new
    # generator. The old one's host buffers are pinned and can't be swapped,
    # so they must be gone before the next model loads and merges its LoRA.
    expected = fpharness.run("Original")
    streamers = low_vram_streamed()
    alive_at_load = []
    real_place = BaseModelGenerator.place_transformer

    def place(self):
        alive_at_load.append([r() is not None for r in refs])
        real_place(self)

    refs = []
    monkeypatch.setattr(BaseModelGenerator, "place_transformer", place)
    first = fpharness.run("Original")
    refs.append(weakref.ref(streamers[-1]().transformer))
    sm = StudioManager()
    monkeypatch.setitem(sm.settings.settings, "reuse_model_instance", False)
    # Keep the first job's generator, as the app does between jobs
    monkeypatch.setattr(sm, "unset_current_generator", lambda: None)
    second = fpharness.run("Original")

    assert not first["errors"] and not second["errors"], second["errors"]
    assert len(streamers) == 2
    assert alive_at_load[-1] == [False]
    for a, b in zip(second["videos"], expected["videos"]):
        assert torch.equal(a[1], b[1])
