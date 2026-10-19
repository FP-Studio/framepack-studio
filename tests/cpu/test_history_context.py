"""history_context: pack less history into each section."""

import os
import sys

import pytest
import torch
from PIL import Image

import fpharness

sys.path.insert(0, os.path.join(fpharness.REPO_ROOT, "tools"))

import run_job as rj  # noqa: E402


@pytest.fixture(autouse=True)
def restore_studio_state():
    from modules.studio_manager import StudioManager

    sm = StudioManager()
    saved = dict(sm.settings.settings)
    yield
    sm.settings.settings.clear()
    sm.settings.settings.update(saved)
    sm.unset_current_generator()


@pytest.mark.parametrize("model_type", ["F1", "Original"])
@pytest.mark.parametrize(
    "context, has_2x, has_4x",
    [
        ("full", True, True),
        ("no4x", True, False),
        ("no2x", False, True),
        ("1x", False, False),
    ],
)
def test_history_context_drops_the_compressed_history(
    tmp_path, monkeypatch, model_type, context, has_2x, has_4x
):
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    image = str(tmp_path / "start.png")
    Image.fromarray(fpharness.default_image(96, 128)).save(image)
    calls = []
    real = kdh.sample_hunyuan

    def sample(**kwargs):
        calls.append(
            (
                kwargs["clean_latents_2x"] is not None,
                kwargs["clean_latents_4x"] is not None,
                kwargs["clean_latents"] is not None,
            )
        )
        return real(**kwargs)

    monkeypatch.setattr(kdh, "sample_hunyuan", sample)
    result = rj.run_job(
        output_dir=str(tmp_path / "out"),
        fake=True,
        verbose=False,
        input_image=image,
        model_type=model_type,
        total_second_length=2,
        resolutionW=64,
        resolutionH=64,
        steps=2,
        latent_window_size=3,
        seed=3,
        use_magcache=False,
        history_context=context,
    )
    assert os.path.exists(result["video_path"])
    assert calls and all(c == (has_2x, has_4x, True) for c in calls)


@pytest.mark.parametrize(
    "sigma, ramp", [(0.0, False), (0.1, False), (0.2, True), (0.2, "far")]
)
def test_history_noise_noises_the_history_not_the_start_frame(
    tmp_path, monkeypatch, sigma, ramp
):
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh
    from modules.generators.f1_generator import F1ModelGenerator

    image = str(tmp_path / "start.png")
    Image.fromarray(fpharness.default_image(96, 128)).save(image)
    before, after = [], []
    real_prepare = F1ModelGenerator.prepare_clean_latents
    real_sample = kdh.sample_hunyuan

    def prepare(self, *args):
        out = real_prepare(self, *args)
        before.append([t.clone() for t in out])
        return out

    def sample(**kwargs):
        after.append(
            [
                kwargs[k].clone()
                for k in ("clean_latents", "clean_latents_2x", "clean_latents_4x")
            ]
        )
        return real_sample(**kwargs)

    monkeypatch.setattr(F1ModelGenerator, "prepare_clean_latents", prepare)
    monkeypatch.setattr(kdh, "sample_hunyuan", sample)
    rj.run_job(
        output_dir=str(tmp_path / "out"),
        fake=True,
        verbose=False,
        input_image=image,
        model_type="F1",
        total_second_length=2,
        resolutionW=64,
        resolutionH=64,
        steps=2,
        latent_window_size=3,
        seed=3,
        use_magcache=False,
        history_noise=sigma,
        history_noise_ramp=ramp,
    )
    assert len(before) == len(after) == 5
    for (c0, c2, c4), (n0, n2, n4) in zip(before, after):
        assert torch.equal(n0[:, :, :1], c0[:, :, :1])  # the start frame stays clean
        sigmas = {True: (sigma, sigma / 2, 0.0), "far": (0.0, sigma / 2, sigma)}.get(
            ramp, (sigma,) * 3
        )
        for (clean, noised), s in zip(
            ((c0[:, :, 1:], n0[:, :, 1:]), (c2, n2), (c4, n4)), sigmas
        ):
            # noised = (1 - s) * clean + s * eps, eps ~ N(0, 1)
            eps_part = noised.float() - (1 - s) * clean.float()
            assert eps_part.std().item() == pytest.approx(s, rel=0.2, abs=1e-3)


def _frames(path):
    import av

    with av.open(path) as c:
        return sum(1 for _ in c.decode(video=0))


@pytest.mark.parametrize("model_type", ["F1", "Original"])
def test_section_overlap_regenerates_and_keeps_the_length(
    tmp_path, monkeypatch, model_type
):
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    image = str(tmp_path / "start.png")
    Image.fromarray(fpharness.default_image(96, 128)).save(image)
    real = kdh.sample_hunyuan
    calls = {}

    def run(overlap):
        seen = calls.setdefault(overlap, [])

        def sample(**kwargs):
            seen.append((kwargs["frames"], kwargs["latent_indices"].shape[1]))
            return real(**kwargs)

        monkeypatch.setattr(kdh, "sample_hunyuan", sample)
        return rj.run_job(
            output_dir=str(tmp_path / f"out{overlap}"),
            fake=True,
            verbose=False,
            input_image=image,
            model_type=model_type,
            total_second_length=2,
            resolutionW=64,
            resolutionH=64,
            steps=2,
            latent_window_size=3,
            seed=3,
            use_magcache=False,
            section_overlap=overlap,
        )

    plain, overlapped = run(0), run(2)
    window = 3
    assert calls[0] == [(window * 4 - 3, window)] * 5
    if model_type == "F1":
        # first section has nothing to overlap; the rest generate 2 extra latent frames
        assert (
            calls[2]
            == [(window * 4 - 3, window)] + [((window + 2) * 4 - 3, window + 2)] * 4
        )
    else:
        assert calls[2] == calls[0]
    assert _frames(overlapped["video_path"]) == _frames(plain["video_path"])


def test_overlap_guide_holds_the_regenerated_frames_on_the_old_ones(
    tmp_path, monkeypatch
):
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    image = str(tmp_path / "start.png")
    Image.fromarray(fpharness.default_image(96, 128)).save(image)
    real = kdh.sample_hunyuan
    seen = []

    def sample(**kwargs):
        guide = kwargs["guide_latents"]
        held = []
        outer = kwargs["callback"]

        def callback(d):
            # x after step i sits at sigma i + 1; check the guided frames are on target
            if guide is not None and d["i"] < kwargs["guide_steps"]:
                held.append(d["x"][:, :, : guide.shape[2]].clone())
            return outer(d) if outer is not None else None

        out = real(**{**kwargs, "callback": callback})
        seen.append(
            (
                None if guide is None else guide.shape[2],
                kwargs["guide_steps"],
                len(held),
            )
        )
        return out

    monkeypatch.setattr(kdh, "sample_hunyuan", sample)
    rj.run_job(
        output_dir=str(tmp_path / "out"),
        fake=True,
        verbose=False,
        input_image=image,
        model_type="F1",
        total_second_length=2,
        resolutionW=64,
        resolutionH=64,
        steps=4,
        latent_window_size=3,
        seed=3,
        use_magcache=False,
        section_overlap=2,
        overlap_guide=0.5,
    )
    assert seen == [(None, 0, 0)] + [(2, 2, 2)] * 4


def test_guide_resets_the_frames_to_the_noised_target(monkeypatch):
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    sigmas = torch.tensor([1.0, 0.7, 0.3, 0.0])
    target = torch.full((1, 16, 2, 1, 1), 3.0)
    noise = torch.randn(1, 16, 5, 1, 1)
    seen = []

    def fake_unipc(model, x, sigmas, extra_args=None, callback=None, disable=False):
        for i in range(len(sigmas) - 1):
            x.mul_(0.5)
            callback({"x": x, "i": i, "denoised": x})
            seen.append(x.clone())
        return x

    class T:
        device = torch.device("cpu")

    monkeypatch.setattr(kdh, "sample_unipc", fake_unipc)
    monkeypatch.setattr(kdh, "get_flux_sigmas_from_mu", lambda n, mu: sigmas)
    monkeypatch.setattr(kdh, "fm_wrapper", lambda t: None)
    kdh.sample_hunyuan(
        T(),
        frames=17,
        width=8,
        height=8,
        num_inference_steps=3,
        batch_size=1,
        prompt_embeds=torch.zeros(1, 1, 1),
        noise=noise.clone(),
        shift=1.0,
        guide_latents=target,
        guide_steps=2,
    )
    for i in range(
        2
    ):  # held: target noised to the next sigma with the frames' own start noise
        expected = 3.0 * (1 - sigmas[i + 1]) + noise[:, :, :2] * sigmas[i + 1]
        assert torch.allclose(seen[i][:, :, :2], expected)
    assert torch.allclose(seen[2][:, :, :2], seen[1][:, :, :2] * 0.5)  # then free
    assert torch.allclose(
        seen[2][:, :, 2:], noise[:, :, 2:] * 0.125
    )  # other frames never touched


@pytest.mark.parametrize("guide", [0.5, 1.0])
def test_full_overlap_guide_keeps_the_old_frames(tmp_path, monkeypatch, guide):
    import diffusers_helper.pipelines.k_diffusion_hunyuan as kdh

    image = str(tmp_path / "start.png")
    Image.fromarray(fpharness.default_image(96, 128)).save(image)
    real = kdh.sample_hunyuan
    tails = []

    def sample(**kwargs):
        if kwargs["guide_latents"] is not None:
            tails.append(kwargs["guide_latents"].clone())
        return real(**kwargs)

    monkeypatch.setattr(kdh, "sample_hunyuan", sample)
    rj.run_job(
        output_dir=str(tmp_path / "out"),
        fake=True,
        verbose=False,
        input_image=image,
        model_type="F1",
        total_second_length=2,
        resolutionW=64,
        resolutionH=64,
        steps=2,
        latent_window_size=1,
        seed=3,
        use_magcache=False,
        section_overlap=2,
        overlap_guide=guide,
    )
    # a 1-frame window keeps one overlap frame in the next section's tail: unchanged
    # only when the re-generated frames don't blend into the history
    assert len(tails) > 2
    same = [torch.equal(a[:, :, 1:], b[:, :, :1]) for a, b in zip(tails, tails[1:])]
    assert all(same) if guide >= 1 else not any(same)
