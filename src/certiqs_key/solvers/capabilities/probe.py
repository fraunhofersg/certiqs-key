"""Capability probing, declaration, and the gate that refuses.

spec/architecture.md 7.3: "The probe refuses: if the proof instance requires a
capability the active oracle does not declare, the run stops with a capability
error -- never a silent fallback to a solver that cannot represent the
problem."
spec/architecture.md 8
adds what a probe records -- Python version, NumPy/SciPy builds, the active
oracle identity, the QICS version when present, and the declared capabilities --
and that "the repository detects missing dependencies and reports instructions;
it does not install them".

Missing QICS is the case this module exists for. QICS is an OPTIONAL extra by
design (pyproject.toml, the ``oracle-qics`` extra): the fail-closed behaviour is
only testable in an
environment where the oracle is genuinely absent, so ``import qics`` is never a
module-level import anywhere in this package, and the absence of the extra
produces a :class:`CapabilityError` with installation instructions rather than
an ``ImportError`` from the middle of a solve.
"""

from __future__ import annotations

import importlib.util
import platform
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import numpy as np

from certiqs_key.meat_core.errors import MeatError

#: What to tell a user whose environment lacks the optional oracle.
QICS_INSTALL_HINT = (
    'pip install -e ".[oracle-qics]" (the pin is the oracle-qics extra of '
    "pyproject.toml; this repository declares dependencies and does not "
    "install them, spec/architecture.md 8)"
)


class CapabilityError(MeatError):
    """A required solver capability is not declared by the active oracle.

    Raised at probe time, before any numerical work. Never downgraded to a
    warning and never worked around by falling back to another solver.
    """


class Capability(StrEnum):
    """The capabilities a :class:`LinearOracle` may declare.

    The list is spec/architecture.md 7.3's: complex Hermitian PSD cones,
    direct-sum sector layout, Choi versus state form, and whether equality and
    inequality rows are native.
    """

    COMPLEX_HERMITIAN_PSD = "complex_hermitian_psd"
    DIRECT_SUM_SECTORS = "direct_sum_sectors"
    CHOI_FORM = "choi_form"
    EQUALITY_ROWS = "equality_rows"
    INEQUALITY_ROWS = "inequality_rows"


#: What the sector-Choi subproblem of the Frank-Wolfe driver needs from any
#: oracle: the minimum capability requirements of spec/architecture.md 7.4.
SECTOR_CHOI_REQUIREMENTS: frozenset[Capability] = frozenset(
    {
        Capability.COMPLEX_HERMITIAN_PSD,
        Capability.DIRECT_SUM_SECTORS,
        Capability.CHOI_FORM,
        Capability.EQUALITY_ROWS,
    }
)

#: What a SPECTRAPLEX subproblem needs: the cone, the sector layout and the Choi
#: form, and no row capability, because a spectraplex group has no declared row
#: (its one coupling equation is the trace normalisation the closed form of
#: :mod:`certiqs_key.solvers.oracles.spectral` is stated on). Probed on that
#: backend by the joint driver whenever a group is assigned to it.
SPECTRAPLEX_REQUIREMENTS: frozenset[Capability] = frozenset(
    {
        Capability.COMPLEX_HERMITIAN_PSD,
        Capability.DIRECT_SUM_SECTORS,
        Capability.CHOI_FORM,
    }
)


@dataclass(frozen=True)
class OracleCapabilities:
    """What one oracle declares about itself.

    ``max_sector_dim`` is the largest single PSD block the oracle accepts;
    ``None`` means it declares no bound.
    """

    name: str
    version: str
    capabilities: frozenset[Capability]
    max_sector_dim: int | None = None

    def as_payload(self) -> dict[str, Any]:
        """Return the declaration as serializable data."""
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": sorted(str(item) for item in self.capabilities),
            "max_sector_dim": self.max_sector_dim,
        }


def require_capabilities(
    declared: OracleCapabilities,
    required: Iterable[Capability],
    *,
    sector_dims: Iterable[int] = (),
) -> None:
    """Raise unless ``declared`` covers ``required`` and the block sizes.

    Raises:
        CapabilityError: naming every missing capability at once, so that a
            user is not sent round the loop one capability at a time.
    """
    missing = sorted(str(item) for item in set(required) - declared.capabilities)
    if missing:
        raise CapabilityError(
            f"the active linear oracle {declared.name!r} {declared.version} "
            f"does not declare {missing}. spec/architecture.md 7.3: a "
            "required capability the oracle does not declare stops the run; "
            "there is no fallback to an inapplicable solver"
        )
    if declared.max_sector_dim is not None:
        oversized = [dim for dim in sector_dims if dim > declared.max_sector_dim]
        if oversized:
            raise CapabilityError(
                f"the active linear oracle {declared.name!r} declares "
                f"max_sector_dim={declared.max_sector_dim} but the problem has "
                f"blocks of dimension {sorted(oversized)}"
            )


def qics_available() -> bool:
    """Return whether the optional QICS oracle can be imported."""
    return importlib.util.find_spec("qics") is not None


def qics_version() -> str | None:
    """Return the installed QICS version, or ``None`` when it is absent."""
    if not qics_available():
        return None
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("qics")
    except PackageNotFoundError:  # pragma: no cover - installed without metadata
        return "unknown"


def probe_environment(declared: OracleCapabilities | None = None) -> dict[str, Any]:
    """Return the capability record of spec/architecture.md 8.

    Data only: versions, an oracle identity and its declared capabilities. No
    solver handle and no backend object ever enters a payload (contract
    the `not_outputs` rows).
    """
    record: dict[str, Any] = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": _scipy_version(),
        "qics": qics_version(),
        "oracle": declared.as_payload() if declared is not None else None,
    }
    if not qics_available():
        record["qics_hint"] = QICS_INSTALL_HINT
    return record


def _scipy_version() -> str | None:
    """Return the installed SciPy version, or ``None`` when it is absent."""
    if importlib.util.find_spec("scipy") is None:  # pragma: no cover - declared dep
        return None
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("scipy")
    except PackageNotFoundError:  # pragma: no cover - installed without metadata
        return "unknown"


def describe(record: Mapping[str, Any]) -> str:
    """Return a one-line human summary of a probe record."""
    oracle = record.get("oracle")
    name = "none" if oracle is None else f"{oracle['name']} {oracle['version']}"
    return (
        f"python {record['python']}, numpy {record['numpy']}, "
        f"qics {record['qics']}, oracle {name}"
    )
