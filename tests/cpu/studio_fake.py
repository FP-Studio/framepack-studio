"""
Launch the real studio.py UI on a CUDA-less Mac with tiny fake models.

    python tests/cpu/studio_fake.py --port 7861 --server 127.0.0.1

Every model load is replaced: text encoders and CLIP vision return
deterministic fake embeddings, the VAE and transformer are tiny random
networks. Generation runs end-to-end through the real queue and worker.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, REPO_ROOT]
os.chdir(REPO_ROOT)  # studio.py uses paths relative to the repo

import fpshim  # noqa: E402,F401

import runpy  # noqa: E402

import torch  # noqa: E402

import diffusers_helper.memory as memory  # noqa: E402

memory.gpu = torch.device("cpu")
memory.get_cuda_free_memory_gb = lambda device=None: 80.0

import fpharness  # noqa: E402
import diffusers  # noqa: E402
import transformers  # noqa: E402
import diffusers_helper.hunyuan as hunyuan  # noqa: E402


class Dummy:
    def __getattr__(self, name):
        return lambda *a, **k: self


def _dummy_loader(*args, **kwargs):
    return Dummy()


for name in (
    "LlamaModel",
    "CLIPTextModel",
    "LlamaTokenizerFast",
    "CLIPTokenizer",
    "SiglipImageProcessor",
    "SiglipVisionModel",
):
    getattr(transformers, name).from_pretrained = staticmethod(_dummy_loader)


def _tiny_vae_loader(*args, **kwargs):
    vae = fpharness.tiny_vae()
    real_to = vae.to

    def to(*a, **k):  # keep float32 on CPU; studio.py casts the VAE to fp16
        k.pop("dtype", None)
        a = tuple(x for x in a if not isinstance(x, torch.dtype))
        return real_to(*a, **k) if a or k else vae

    vae.to = to
    return vae


diffusers.AutoencoderKLHunyuanVideo.from_pretrained = staticmethod(_tiny_vae_loader)


def fake_encode_prompt_conds(prompt, *args, **kwargs):
    vec, _, pool = fpharness.FakePromptCache()[prompt]
    return vec[:, :8], pool


hunyuan.encode_prompt_conds = fake_encode_prompt_conds


def save_mp4_with_av(x, output_filename, fps=10, crf=0):
    """torchcodec needs Homebrew's ffmpeg dylibs; PyAV bundles its own."""
    import av
    import einops

    os.makedirs(os.path.dirname(os.path.abspath(output_filename)), exist_ok=True)
    x = (torch.clamp(x.float(), -1.0, 1.0) * 127.5 + 127.5).to(torch.uint8)
    frames = einops.rearrange(x[:1], "b c t h w -> t h (b w) c").numpy()
    with av.open(output_filename, "w") as container:
        stream = container.add_stream("libx264", rate=int(fps))
        stream.width, stream.height = frames.shape[2], frames.shape[1]
        stream.pix_fmt = "yuv420p"
        for frame in frames:
            for packet in stream.encode(
                av.VideoFrame.from_ndarray(frame, format="rgb24")
            ):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return output_filename


import diffusers_helper.utils as dh_utils  # noqa: E402

dh_utils.save_bcthw_as_mp4 = save_mp4_with_av
worker_mod = fpharness._patch_cpu()
worker_mod.save_bcthw_as_mp4 = save_mp4_with_av

import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh  # noqa: E402

_real_sampler = kdh.sample_hunyuan


def _logged_sampler(**kwargs):
    def desc(name):
        v = kwargs.get(name)
        return tuple(v.shape) if torch.is_tensor(v) else v

    print(
        f"[fake-studio] sample_hunyuan noise={desc('noise')} "
        f"initial_latent={desc('initial_latent')} strength={kwargs.get('strength')}",
        flush=True,
    )
    return _real_sampler(**kwargs)


kdh.sample_hunyuan = _logged_sampler

sys.argv = [os.path.join(os.getcwd(), "studio.py")] + sys.argv[1:]
runpy.run_path("studio.py", run_name="__main__")
