import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fpshim  # noqa: E402,F401  (stub CUDA/toolbox imports before anything else)
