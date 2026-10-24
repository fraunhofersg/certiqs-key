"""Make the FROZEN oracle registry importable from the golden tests.

``tests/oracles/`` is committed and frozen: it may be read
and may not be modified, moved, reformatted or extended. This file adds its
directory to ``sys.path`` so that the golden tests can import ``registry``,
``toy_declarations``, ``dummy_bundles`` and ``reference`` -- reading only.

Doing it in a ``conftest.py`` rather than inside each test module is what makes
it deterministic: conftest files are imported before the test modules beside
them, so the path is present no matter which subset of the suite is collected.
"""

from __future__ import annotations

import sys
from pathlib import Path

ORACLE_TREE = Path(__file__).resolve().parents[1] / "oracles"

if str(ORACLE_TREE) not in sys.path:
    sys.path.insert(0, str(ORACLE_TREE))
