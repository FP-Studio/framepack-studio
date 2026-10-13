# The vendored mmaudio package uses absolute `from mmaudio...` imports, so its
# parent directory must be on sys.path. Import it only as `mmaudio`, never as
# `modules.MMAudio.mmaudio`, or Python loads a second copy of the package.
import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)
