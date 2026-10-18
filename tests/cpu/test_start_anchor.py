"""Start anchor dials (start_attention, start_gap, start_shift) on Original, with fake models."""

import os
import sys

import pytest
import torch
from PIL import Image

import fpharness

sys.path.insert(0, os.path.join(fpharness.REPO_ROOT, "tools"))

import run_job as rj  # noqa: E402

TINY = dict(
    model_type="Original",
    total_second_length=2,
    resolutionW=64,
    resolutionH=64,
    steps=3,
    latent_window_size=3,
    seed=11,
    save_section_latents=True,
    use_magcache=False,
)


@pytest.fixture(autouse=True)
def restore_studio_state():
    from modules.studio_manager import StudioManager

    sm = StudioManager()
    saved = dict(sm.settings.settings)
    yield
    sm.settings.settings.clear()
    sm.settings.settings.update(saved)
    sm.unset_current_generator()


@pytest.fixture(scope="module")
def image(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("assets") / "start.png")
    Image.fromarray(fpharness.default_image(96, 128)).save(path)
    return path


def render(image, out, **options):
    from modules.pipelines import section_checkpoint

    result = rj.run_job(
        output_dir=str(out), fake=True, verbose=False, input_image=image, **TINY, **options
    )
    return section_checkpoint.load_section_checkpoint(
        section_checkpoint.checkpoint_path(str(out), result["job_id"])
    )


@pytest.fixture
def section_calls(monkeypatch):
    """Per sampling call: the start frame's time index and the start attention weight."""
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh
    from diffusers_helper.models import hunyuan_video_packed as hvp

    calls = []
    real = kdh.sample_hunyuan

    def sample(**kwargs):
        calls.append(
            (kwargs["clean_latent_indices"][0, 0].item(), hvp._START_ATTENTION["weight"])
        )
        return real(**kwargs)

    monkeypatch.setattr(kdh, "sample_hunyuan", sample)
    return calls


def test_shift_start_frame_moves_only_the_start_index():
    from modules.pipelines import start_anchor

    indices = torch.tensor([[0, 13]])
    assert start_anchor.shift_start_frame(indices, 0) is indices
    shifted = start_anchor.shift_start_frame(indices, 2.5)
    assert shifted.tolist() == [[-2.5, 13.0]]
    assert indices.tolist() == [[0, 13]]


@pytest.mark.parametrize(
    "options, starts, weights",
    [
        ({}, [0, 0, 0, 0, 0], [None] * 5),
        (dict(start_gap=3.0), [0, 0, 0, 0, -3.0], [None] * 5),
        (dict(start_shift=2.0), [-2.0] * 5, [None] * 5),
        (dict(start_shift=1.0, start_gap=2.0), [-1.0] * 4 + [-3.0], [None] * 5),
        (dict(start_attention=0.4), [0] * 5, [None] * 4 + [0.4]),
        (dict(start_attention=0.4, start_attention_all_sections=True), [0] * 5, [0.4] * 5),
    ],
)
def test_each_section_gets_its_start_index_and_weight(
    image, tmp_path, section_calls, options, starts, weights
):
    from diffusers_helper.models import hunyuan_video_packed as hvp

    render(image, tmp_path, **options)
    # 2 s with a 3-latent window is 5 sections; the last call is time 0
    assert [c[0] for c in section_calls] == starts
    assert [c[1] for c in section_calls] == weights
    assert hvp._START_ATTENTION["weight"] is None  # reset when the job ends


def test_attention_bias_reweights_the_start_keys():
    from diffusers_helper.models import hunyuan_video_packed as hvp

    torch.manual_seed(0)
    q, k, v = (torch.randn(1, 6, 2, 8) for _ in range(3))  # (batch, tokens, heads, dim)
    plain = torch.nn.functional.scaled_dot_product_attention(
        q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2)
    ).transpose(1, 2)
    scale = torch.tensor([1.0, 1.0, 0.5, 0.5, 1.0, 1.0])  # keys 2-3 at half weight
    try:
        hvp._START_ATTENTION["bias"] = torch.zeros(1, 1, 1, 6)
        assert torch.allclose(hvp.attn_varlen_func(q, k, v, None, None, None, None), plain, atol=1e-6)
        hvp._START_ATTENTION["bias"] = scale.log().view(1, 1, 1, 6)
        out = hvp.attn_varlen_func(q, k, v, None, None, None, None)
    finally:
        hvp._START_ATTENTION["bias"] = None
    # By hand: softmax with keys 2-3 scaled by 0.5
    logits = torch.einsum("bqhd,bkhd->bhqk", q, k) / 8 ** 0.5
    weights = logits.softmax(-1) * scale
    weights = weights / weights.sum(-1, keepdim=True)
    assert torch.allclose(out, torch.einsum("bhqk,bkhd->bqhd", weights, v), atol=1e-5)


def test_bias_covers_the_start_frame_and_image_tokens(image, tmp_path, monkeypatch):
    from diffusers_helper.models import hunyuan_video_packed as hvp

    biases = []
    real = hvp.HunyuanVideoTransformer3DModelPacked._start_attention_bias

    def spy(self, hidden_states, encoder_hidden_states, image_tokens):
        bias = real(self, hidden_states, encoder_hidden_states, image_tokens)
        if bias is not None:
            start, count = self._start_frame_span
            biases.append((bias, start, count, hidden_states.shape[1], image_tokens))
        return bias

    monkeypatch.setattr(hvp.HunyuanVideoTransformer3DModelPacked, "_start_attention_bias", spy)
    render(image, tmp_path, start_attention=0.5)
    assert len(biases) == TINY["steps"]  # time-0 section only
    for bias, start, count, video_len, image_tokens in biases:
        flat = bias.flatten()
        hit = torch.nonzero(flat).flatten().tolist()
        expected = list(range(start, start + count)) + list(
            range(video_len, video_len + image_tokens)
        )
        assert count > 0 and image_tokens > 0
        assert hit == expected
        assert flat[hit[0]].item() == pytest.approx(torch.log(torch.tensor(0.5)).item())
    assert hvp._START_ATTENTION["weight"] is None  # reset when the job ends
