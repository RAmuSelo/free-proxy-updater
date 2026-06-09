"""Optional helper to put the src-layout package on sys.path.

Not required by the test suite (each test module bootstraps sys.path inline so
``python3 -m unittest discover`` works from any working directory). Kept as a
convenience for ad-hoc imports, e.g. ``python3 -c "import tests._path; ..."``.
"""

import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
