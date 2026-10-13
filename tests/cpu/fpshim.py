"""Import shims so FramePack Studio modules load on a CUDA-less Mac."""

import importlib.abc
import importlib.machinery
import os
import sys
import types

import torch

torch.cuda.current_device = lambda: 0

# Packages that are only needed by the toolbox / have no arm64 Mac wheels.
STUB_PREFIXES = (
    "decord",
    "basicsr",
    "realesrgan",
    "gfpgan",
    "facexlib",
    "open_clip",
    "nitrous_ema",
    "hydra",
    "torchdiffeq",
)
# eva-decord has arm64 Mac wheels; FP_REAL_DECORD=1 uses it so video jobs run.
if os.environ.get("FP_REAL_DECORD"):
    STUB_PREFIXES = tuple(p for p in STUB_PREFIXES if p != "decord")


class _StubMeta(type):
    def __getattr__(cls, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _StubMeta(name, (), {})


class _StubAttr(metaclass=_StubMeta):
    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return _StubMeta(name, (), {})


class _StubModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _StubMeta(name, (_StubAttr,), {})


class _StubFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path, target=None):
        if fullname.split(".")[0] in STUB_PREFIXES:
            return importlib.machinery.ModuleSpec(fullname, self, is_package=True)
        return None

    def create_module(self, spec):
        mod = _StubModule(spec.name)
        mod.__path__ = []
        return mod

    def exec_module(self, module):
        pass


sys.meta_path.insert(0, _StubFinder())
