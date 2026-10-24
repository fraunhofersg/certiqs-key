"""The QICS-backed sector-Choi linear oracle (spec/architecture.md 7.4).

Importing this module does not import QICS: the optional extra is imported
inside the oracle's methods, so that an environment without it fails closed at
probe time with installation instructions rather than at import time.
"""

from __future__ import annotations

from certiqs_key.solvers.oracles.qics.adapter import QicsSectorChoiOracle

__all__ = ["QicsSectorChoiOracle"]
