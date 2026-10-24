"""Linear minimization oracles.

``protocol`` is the physics-blind interface; ``acceptance`` is the separate
frequency-vector oracle of spec/architecture.md 7.2; ``qics`` is the initial
backend and is imported only by a caller that wants it, so that an environment
without the optional extra still imports this package.
"""

from __future__ import annotations

from certiqs_key.solvers.oracles.acceptance import (
    AcceptanceOracle,
    ExactAcceptanceOracle,
    PolytopeAcceptanceOracle,
    SingletonAcceptanceOracle,
    acceptance_oracle,
)
from certiqs_key.solvers.oracles.protocol import (
    AffineRow,
    LinearOracle,
    OracleFailure,
    OracleSolution,
    SectorChoiProblem,
)

__all__ = [
    "AcceptanceOracle",
    "AffineRow",
    "ExactAcceptanceOracle",
    "LinearOracle",
    "OracleFailure",
    "OracleSolution",
    "PolytopeAcceptanceOracle",
    "SectorChoiProblem",
    "SingletonAcceptanceOracle",
    "acceptance_oracle",
]
