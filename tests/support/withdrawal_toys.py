"""One iterate per WITHDRAWAL ROW of ``meat-core`` ``req:first-order-withdrawal``.

The four rows are the four ways ``h_lb`` can be withdrawn, and each is a
different hypothesis of Theorem ``thm:firstorder`` failing at a contributing
iterate. Without this module no test outside the frozen registry would name
``gradient_hypothesis_positivity``, ``gradient_hypothesis_support``,
``gradient_perturbation_applied``, ``iterate_not_feasible`` or the fifth row,
``oracle_not_optimal`` (not emitted as a withdrawal), so the strings and the
gate that emits them would be unexercised.

WHY STUB ORACLES AND NOT A DECLARATION PER ROW. Three of the five are
properties of the ORACLE or of the SOLVER OPTIONS rather than of a declaration
-- an oracle status that does not assert optimality, an acceptance factor not
formed on the exact island, an explicit gradient perturbation -- and
:func:`~certiqs_key.solvers.frank_wolfe.joint_driver.run_joint_frank_wolfe`
takes both oracles as arguments precisely so that they can be supplied. The
stubs below are the smallest objects satisfying the two protocols; they
compute nothing the driver then trusts, because what is under test is the GATE
and not the arithmetic.

NOTHING HERE WEAKENS A CHECK. Every stub returns a point that is genuinely what
it claims to be -- a singular block really is singular, a negative eigenvalue
really is negative -- so the gate decides on the same measurement it would make
of a backend's return.

ONE DRIVER. The toy is the accepted-format declaration it always
was, run as the degenerate general declaration it IS
(:func:`~certiqs_key.meat_core.declaration.general.general_from_accepted`), so a
point is keyed by the joint sector ``(t0, s)`` and the stub oracle is asked the
per-Alice-sector program, whose cost is keyed by ``s``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np
from toy_declarations import toy

from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.declaration.general import general_from_accepted
from certiqs_key.meat_core.objective.joint import JointMaps, JointSector
from certiqs_key.solvers.capabilities.probe import Capability, OracleCapabilities
from certiqs_key.solvers.frank_wolfe.general_keyrate import _prepare_general
from certiqs_key.solvers.oracles.protocol import OracleSolution, SectorChoiProblem

__all__ = [
    "SINGULAR_START",
    "StubAcceptanceOracle",
    "StubLinearOracle",
    "interior_start",
    "singular_start",
    "toy_setup",
    "with_negative_block",
]

#: The toy every row below runs on: TOY-1, one Alice dimension, two
#: one-dimensional sectors, a singleton acceptance set on ``{chat0}``. It is
#: the declaration Group 10's ``O-FO-BRACKET-UNCONSTRAINED`` is derived on, so
#: the numbers a run produces here are numbers the frozen registry already
#: describes.
TOY_ID = "TOY-1"

#: A start whose key-active block is EXACTLY SINGULAR, which is what makes
#: (H-SUPP) fail: ``rank X_{chat,s} < dim W_{chat,s}`` at ``w0 = 0``, the case
#: ``O-FO-BRACKET-UNCONSTRAINED`` derives ("At ``w0 = 0`` the key-active branch
#: operator is ``X_chat0,s0 = 0``, whose rank is 0, while
#: ``dim W_chat0,s0 = 1``").
SINGULAR_START: Mapping[str, float] = {"s0": 0.0, "s1": 1.0}


#: The one Alice sector of a degenerate general declaration
#: (:func:`~certiqs_key.meat_core.declaration.general.general_from_accepted`).
ALICE = "t0"


def toy_setup(toy_id: str = TOY_ID) -> tuple[ProtocolDeclaration, JointMaps]:
    """Return the declaration and the joint maps the one driver runs on."""
    from dummy_bundles import build_bundle

    declaration = declaration_from_bundle(build_bundle(toy(toy_id)))
    maps, _ = _prepare_general(
        general_from_accepted(declaration), StubLinearOracle(blocks={})
    )
    return declaration, maps


def interior_start(
    declaration: ProtocolDeclaration,
) -> dict[JointSector, np.ndarray]:
    """Return a strictly positive feasible point: equal weight on each sector."""
    weight = 1.0 / len(declaration.sector_index_set)
    return {
        (ALICE, sector): np.array([[weight]], dtype=np.complex128)
        for sector in declaration.sector_index_set
    }


def singular_start(
    declaration: ProtocolDeclaration,
) -> dict[JointSector, np.ndarray]:
    """Return a feasible point whose key-active block is exactly ``0``."""
    return {
        (ALICE, sector): np.array([[SINGULAR_START[sector]]], dtype=np.complex128)
        for sector in declaration.sector_index_set
    }


def with_negative_block(
    point: Mapping[JointSector, np.ndarray], sector: str, depth: float
) -> dict[JointSector, np.ndarray]:
    """Return ``point`` with one block pushed ``depth`` below zero.

    ``depth`` is a POSITIVE number and the block comes back at ``-depth``, so
    the caller reads the sign it asked for. Kept shallower than
    ``iterate_repair_window`` by the caller, so that the point reaches the gate
    rather than being rejected by the layout check first: Remark
    ``rem:fo-iterate-checks`` decides ``iterate_positivity`` "at exactly 0 and at
    no window", and this is a drift that would otherwise pass silently.
    """
    blocks = {name: np.array(block, copy=True) for name, block in point.items()}
    blocks[(ALICE, sector)] = np.array([[-depth]], dtype=np.complex128)
    return blocks


@dataclass
class StubLinearOracle:
    """A ``LinearOracle`` that returns a point it was given.

    It does not minimize anything, and nothing in the tests below reads its
    objective: what it exists to control is the ``sol_status`` the gate
    records (a diagnostic) and the point the search steps toward. It
    returns no dual, so the bracket's feasible side is formed with zero
    multipliers (``req:verified-feasible-side`` (ii)). ``blocks`` is keyed by
    the joint sector; the return is the one Alice sector's program, keyed by
    the sector.
    """

    blocks: Mapping[JointSector, np.ndarray]
    status: str = "optimal"
    calls: int = 0

    def capabilities(self) -> OracleCapabilities:
        """Declare enough for the driver; nothing is probed in these tests."""
        return OracleCapabilities(
            name="stub",
            version="0",
            capabilities=frozenset(
                {
                    Capability.COMPLEX_HERMITIAN_PSD,
                    Capability.DIRECT_SUM_SECTORS,
                    Capability.CHOI_FORM,
                    Capability.EQUALITY_ROWS,
                    Capability.INEQUALITY_ROWS,
                }
            ),
        )

    def minimize(self, problem: SectorChoiProblem) -> OracleSolution:
        """Return the declared point with the declared status."""
        del problem
        self.calls += 1
        return OracleSolution(
            blocks={
                pair[1]: np.array(b, copy=True) for pair, b in self.blocks.items()
            },
            objective=0.0,
            diagnostics={"sol_status": self.status},
        )


@dataclass
class StubAcceptanceOracle:
    """An acceptance oracle with a declared start and a declared island flag.

    ``exact_island`` is a RECORDED PROPERTY and never a measurement (Section
    2.2), so a stub that declares ``False`` is exactly what a geometry forming
    ``q_t`` in binary64 would look like to the gate -- the case Remark
    ``rem:acc-side`` says withdraws under ``iterate_not_feasible``, "in either
    case".
    """

    frequencies: Mapping[str, float]
    exact_island: bool = True
    minimizer: Mapping[str, float] | None = field(default=None)

    def start(self) -> dict[str, float]:
        """Return the declared starting frequency vector."""
        return dict(self.frequencies)

    def minimize(self, gradient: Mapping[str, float]) -> dict[str, float]:
        """Return the declared vertex, or the start where none was declared."""
        del gradient
        return dict(self.minimizer if self.minimizer is not None else self.frequencies)
