"""Fixed worker runs used to compare a checkout against a recorded baseline."""

import sys

import torch

import fpharness

CASES = {
    "F1": dict(model_type="F1"),
    "Original": dict(model_type="Original"),
    "Endframe": dict(
        model_type="Original with Endframe",
        end_frame_image=fpharness.default_image(seed=7),
        end_frame_strength=0.8,
    ),
    "F1_noimage": dict(model_type="F1", has_input_image=False, latent_type="Black"),
}


def run_case(name):
    kw = dict(CASES[name])
    if not kw.get("has_input_image", True):
        kw["input_image"] = fpharness.default_image(
            seed=3
        )  # process() fills a blank image
    return fpharness.run(kw.pop("model_type"), **kw)


if __name__ == "__main__":
    out = {name: [c["out"] for c in run_case(name)["calls"]] for name in CASES}
    torch.save(out, sys.argv[1])
    print(f"Saved baseline for {len(out)} cases to {sys.argv[1]}")
