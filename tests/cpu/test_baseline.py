"""
With new features unused, the worker must match a reference checkout bitwise.

Record the baseline from an untouched checkout (e.g. origin/develop) first:
    python tests/cpu/baseline_cases.py /path/to/baseline.pt
then run with FP_BASELINE=/path/to/baseline.pt. Skipped when unset.
"""

import os

import pytest
import torch

import baseline_cases

BASELINE = os.environ.get("FP_BASELINE")
pytestmark = pytest.mark.skipif(
    not BASELINE or not os.path.exists(BASELINE), reason="FP_BASELINE not set"
)


@pytest.mark.parametrize("name", list(baseline_cases.CASES))
def test_matches_develop(name):
    expected = torch.load(BASELINE)[name]
    res = baseline_cases.run_case(name)
    assert not res["errors"], res["errors"]
    got = [c["out"] for c in res["calls"]]
    assert len(got) == len(expected)
    for a, b in zip(got, expected):
        assert torch.equal(a, b)
