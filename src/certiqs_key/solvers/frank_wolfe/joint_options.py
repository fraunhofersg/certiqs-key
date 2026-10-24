"""How the Frank-Wolfe loop runs: its linear oracle, step rule and start.

``frank-wolfe/thm:firstorder`` ``eq:hlb`` is a maximum over iterates of
per-iterate brackets, and each bracket needs only (H-POS), (H-SUPP) and
(H-NOPERT) at its own iterate and the two lower bounds on the linear minima
(``thm:firstorder`` (iv); ``req:verified-feasible-side``).
``rem:fo-reachability``: "This module prescribes no optimizer and does not
require one". So the three choices below change the PATH the solver takes and
the iterates it reaches, and not what a bracket at any of them means; no claim
reads them. Each is a recorded run setting, and the defaults are the plain
loop. There is one driver, so every declaration, the accepted-format ones
included, may choose them.

``oracle``
    ``"qics"`` (default): every subproblem goes to the conic oracle the caller
    supplied. ``"spectral"``: every subproblem whose feasible set is a
    SPECTRAPLEX goes to the closed-form backend of
    :mod:`certiqs_key.solvers.oracles.spectral`, and every other one to the
    conic oracle. :func:`oracle_assignment` decides which is which ONCE, before
    the loop, from the declaration's structure alone, and the assignment is on
    the record; nothing is ever re-routed because a backend failed
    (spec/architecture.md 7.3).
``step_rule``
    ``"vanilla"`` (default): today's Frank-Wolfe step toward the oracle return.
    ``"pairwise"``: pairwise Frank-Wolfe over an explicit active set of
    atoms (:mod:`certiqs_key.solvers.frank_wolfe.joint_pairwise`) -- product
    atoms ``(q_i, J_i)``, or ``J``-only atoms where the acceptance geometry
    gets the exact ``q`` rule (:mod:`certiqs_key.solvers.frank_wolfe.q_rule`);
    each iteration searches the pairwise step and the plain step toward the
    same new atom and takes the better, counting the plain ones.
``warm_start``
    ``None`` (default): the cold start -- the interior start of
    ``joint_initial_point``, or the oracle's zero-cost vertex for a
    declaration with constraint rows. A :class:`WarmStart`: a prior point's
    final iterate, mixed with that cold start by :data:`WARM_START_MIX` and
    REFUSED (:class:`WarmStartRefused`) unless the feasible set is the same --
    for a declaration with rows, unless the seed carries the same rows
    (:func:`constraint_rows_digest`).

THE SOLVER'S OWN NUMBERS ARE HERE AND NOT IN A CALLER'S REACH:
:data:`PAIRWISE_SHRINK`, :data:`PAIRWISE_FOLD_BELOW` and
:data:`WARM_START_MIX` are constants of this module, recorded on every run that
uses them, and :class:`~certiqs_key.runs.config.SolverSettings` offers the
three names above and none of these numbers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

import numpy as np

from certiqs_key.meat_core.declaration.general import SEPARATOR, GeneralDeclaration
from certiqs_key.meat_core.errors import MeatError
from certiqs_key.meat_core.objective.joint import JointChoiParametrization, JointSector
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions

#: The admitted values of the two named choices. The first of each is the
#: default and is today's loop.
ORACLE_CHOICES: tuple[str, ...] = ("qics", "spectral")
STEP_RULES: tuple[str, ...] = ("vanilla", "pairwise")

#: THE SHRINK OF EVERY PAIRWISE ORACLE ATOM toward the interior start:
#: ``atom = (1 - delta) S + delta J_0`` (and the same on the acceptance side
#: toward ``q_0``). It keeps a positive weight on ``J_0`` at every iterate, and
#: ``J_0`` positive definite is what makes (H-SUPP) and (H-POS) reachable
#: (``rem:fo-reachability``, "what makes (H-SUPP) reachable"). Without it a
#: pairwise run moves the weight off ``J_0`` until it is negligible -- a
#: pairwise run without it loses a rank on decoy's key-active pair ``(n0, C_1)``
#: (iteration 13). THE COMPONENT IS POSITIVE DEFINITE ONLY WHEN THE ANCHOR IS:
#: the interior start is. A declaration with constraint rows starts (and
#: anchors) at the oracle's zero-cost return, which nothing guarantees to be
#: positive definite by construction, so the driver MEASURES the anchor's
#: smallest block eigenvalue before the loop, records it
#: (``solver_report["pairwise"]["anchor_min_eigenvalue"]``) and stops a run
#: whose anchor is not positive definite (fail closed;
#: ``joint_driver.run_joint_frank_wolfe``). So pairwise IS AVAILABLE WITH ROWS:
#: QICS's zero-cost return is an interior point in practice, and the licensed
#: routes run pairwise at 10 and 20 dB with no (H-SUPP) withdrawal.
#: 1e-8 is small enough that the shrunk atom's
#: linear value differs from the exact return's by 1e-8 of the gap, and the
#: CERTIFICATE NEVER READS THE SHRUNK ATOM: the bracket consumes the exact
#: oracle return (``joint_driver.run_joint_frank_wolfe``).
PAIRWISE_SHRINK = 1e-8

#: Active-set atoms whose weight falls below this are FOLDED, never deleted:
#: the tiny atoms and the heaviest atom are replaced by their weighted mean,
#: carrying their summed weight, so the iterate the atoms represent is
#: unchanged in exact arithmetic (and is rebuilt from the atoms before it is
#: evaluated, so what is evaluated is what the atoms say). An atom of weight
#: below 1e-12 can move the objective by no more than 1e-12 times the width of
#: the linear form, beneath what the line search resolves, and left in place it
#: is repeatedly chosen as the away atom for a futile step. The fold is in
#: practice how atoms leave the set: the golden-section search never returns
#: the endpoint ``w_away`` itself, so a pairwise step does not zero an atom.
PAIRWISE_FOLD_BELOW = 1e-12

#: The warm start is ``(1 - eps) J_prev + eps J_0``, with ``J_0`` the cold start
#: of the new point: the interior start, or, where the declaration has
#: constraint rows, the oracle's zero-cost vertex -- which satisfies the rows,
#: as the interior start need not. ``eps > 0`` keeps the positive-definite
#: component a start needs for (H-SUPP) at the first iterate; 1e-6 moves the
#: start's value by about 1e-6 of the objective's range.
WARM_START_MIX = 1e-6


class WarmStartRefused(MeatError):
    """A warm start whose seed does not live in the new point's feasible set.

    A NAMED REFUSAL AND NOT A CLAMP: projecting a mismatched seed onto the new
    set would be a start nobody chose. ``reason`` is one of
    ``warm_start_source_mode_mismatch``, ``warm_start_layout_mismatch``,
    ``warm_start_block_dims_mismatch``, ``warm_start_constraint_rows_mismatch``
    (the seed's constraint rows are not this point's, or cannot be shown to be)
    and ``warm_start_not_feasible`` (a non-finite or non-Hermitian block, or a
    seed outside the PSD, coupling or row windows of the new point).
    """

    def __init__(self, message: str, *, reason: str) -> None:
        """Keep the machine-readable reason beside the message."""
        super().__init__(message)
        self.reason = reason


def blocks_digest(blocks: Mapping[JointSector, Matrix]) -> str:
    """Return the sha256 of a list of blocks' CANONICAL BYTES.

    Joint sectors in sorted order; for each, its joint label, its shape and
    its entries as little-endian complex128. A function of the numbers alone,
    so it identifies an iterate whatever file or format carried it.
    """
    digest = sha256()
    for pair in sorted(blocks):
        block = np.ascontiguousarray(as_matrix(blocks[pair]), dtype="<c16")
        digest.update(SEPARATOR.join(pair).encode("utf-8"))
        digest.update(repr(block.shape).encode("ascii"))
        digest.update(block.tobytes())
    return digest.hexdigest()


def constraint_rows_digest(declaration: GeneralDeclaration) -> str | None:
    """Return the sha256 of the data that DEFINE a declaration's constraint rows.

    ``None`` for a declaration without rows. Otherwise, over canonical bytes:
    each entry in order -- its scope, relation, tag, operator blocks (sorted by
    sector; shape and little-endian complex128 entries) and its bound (the
    scalar ``c_k``, or the block list ``Theta_k^{(t)}``) -- and, in
    trusted-source mode, the declared marginal of every Alice sector, which
    builds a ``homogeneous`` right-hand side ``c_k tau_A`` and the frame the
    rows are conjugated by. Two declarations with the same digest, the same
    source mode and the same layout have the same ``Feas^J``, which is what a
    warm start across points with rows needs (the licensed routes' rows come
    from the receiver and do not move with the channel).
    """
    if not declaration.constraint_list:
        return None
    digest = sha256()

    def matrix(block: Matrix) -> None:
        array = np.ascontiguousarray(as_matrix(block), dtype="<c16")
        digest.update(repr(array.shape).encode("ascii"))
        digest.update(array.tobytes())

    for entry in declaration.constraint_list:
        digest.update(
            repr((entry.scope, str(entry.relation), str(entry.rhs_tag))).encode()
        )
        for sector in sorted(entry.operator_blocks):
            digest.update(sector.encode("utf-8"))
            matrix(entry.operator_blocks[sector])
        if isinstance(entry.bound, Mapping):
            for alice_sector in sorted(entry.bound):
                digest.update(alice_sector.encode("utf-8"))
                matrix(entry.bound[alice_sector])
        else:
            digest.update(float(entry.bound).hex().encode("ascii"))
    if declaration.is_trusted_source:
        for alice_sector in declaration.alice_sectors:
            digest.update(alice_sector.encode("utf-8"))
            matrix(declaration.marginal_block(alice_sector))
    return digest.hexdigest()


def iterate_layout(parametrization: JointChoiParametrization) -> dict[str, Any]:
    """Return how each joint block splits: Alice factor by sector factor.

    Equal block dimensions do not fix the split -- ``2 x 6`` and ``3 x 4`` are
    both 12 -- so a seed records the split and a warm start compares it. The
    Alice factor is the frame's input dimension in trusted-source mode and the
    Alice sector's own dimension in untrusted-source mode.
    """
    declaration = parametrization.declaration
    return {
        "alice_factor_dims": {
            alice_sector: int(
                parametrization.input_dim(alice_sector)
                if declaration.is_trusted_source
                else declaration.alice_dim_of(alice_sector)
            )
            for alice_sector in declaration.alice_sectors
        },
        "sector_dims": {
            sector: int(declaration.sector_dim(sector))
            for sector in declaration.sector_index_set
        },
    }


@dataclass(frozen=True, eq=False)
class WarmStart:
    """A prior point's final iterate, with what identifies it.

    ``blocks`` is keyed by joint sector; ``source_mode`` is the prior
    declaration's (``"trusted"`` or ``"untrusted"``); ``constraint_count`` is the
    number of constraint rows it declared and ``rows_sha256`` their
    :func:`constraint_rows_digest` (``None`` without rows, or for a seed file
    that predates it); ``layout`` is its
    :func:`iterate_layout` (``None`` for a seed from a file that predates it,
    which then relies on the block shapes alone); ``file_sha256`` and
    ``source`` say which file it was read from.

    ITS IDENTITY IS :attr:`blocks_sha256`, DERIVED HERE from the blocks'
    canonical bytes (:func:`blocks_digest`) and never asserted by a caller.
    Equality and hashing go by it, so two options differing only in their seed
    differ.
    """

    blocks: Mapping[JointSector, Matrix]
    source_mode: str
    constraint_count: int
    file_sha256: str = ""
    source: str = ""
    layout: Mapping[str, Any] | None = None
    rows_sha256: str | None = None
    blocks_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        """Derive the identity from the numbers."""
        object.__setattr__(self, "blocks_sha256", blocks_digest(self.blocks))

    def __eq__(self, other: object) -> bool:
        """Compare by the derived identity."""
        if not isinstance(other, WarmStart):
            return NotImplemented
        return self.blocks_sha256 == other.blocks_sha256

    def __hash__(self) -> int:
        """Hash by the derived identity."""
        return hash(self.blocks_sha256)

    def as_payload(self) -> dict[str, Any]:
        """Return the seed's identity for a record, never its matrices."""
        return {
            "blocks_sha256": self.blocks_sha256,
            "file_sha256": self.file_sha256,
            "source": self.source,
            "source_mode": self.source_mode,
            "joint_sectors": len(self.blocks),
            "constraint_count": self.constraint_count,
            "rows_sha256": self.rows_sha256,
            "mix": WARM_START_MIX,
        }


@dataclass(frozen=True)
class JointFrankWolfeOptions(FrankWolfeOptions):
    """:class:`FrankWolfeOptions` with the three choices of the driver.

    A SUBCLASS so that it travels the run tier's existing ``options`` path
    unchanged. Every declaration runs on the one driver, so every choice
    applies to every declaration (an accepted-format one included).
    """

    oracle: str = ORACLE_CHOICES[0]
    step_rule: str = STEP_RULES[0]
    #: Compared and hashed by the seed's derived identity (``WarmStart``).
    warm_start: WarmStart | None = None

    def __post_init__(self) -> None:
        """Refuse a name outside the admitted vocabulary."""
        if self.oracle not in ORACLE_CHOICES:
            raise ValueError(
                f"oracle is {self.oracle!r}; admitted: {list(ORACLE_CHOICES)}"
            )
        if self.step_rule not in STEP_RULES:
            raise ValueError(
                f"step_rule is {self.step_rule!r}; admitted: {list(STEP_RULES)}"
            )

    @property
    def is_default(self) -> bool:
        """Return whether every general-format choice is today's default."""
        return (
            self.oracle == ORACLE_CHOICES[0]
            and self.step_rule == STEP_RULES[0]
            and self.warm_start is None
        )


def joint_choices(
    options: FrankWolfeOptions | None,
) -> tuple[str, str, WarmStart | None]:
    """Return ``(oracle, step_rule, warm_start)`` of any options, defaults filled."""
    if isinstance(options, JointFrankWolfeOptions):
        return options.oracle, options.step_rule, options.warm_start
    return ORACLE_CHOICES[0], STEP_RULES[0], None


#: How far from Hermitian a supplied start or seed block may be, relative to
#: its largest entry, before it is refused. The engine's own points are
#: Hermitian by construction (``hermitian_part``); a caller's may carry the
#: rounding of a product ``L B L^dagger``, which is ~1e-16 of the entries.
HERMITICITY_WINDOW = 1e-12


def hermiticity_defect(block: Matrix) -> str | None:
    """Return what is wrong with a supplied block, or ``None``.

    Non-finite entries, or a deviation ``max |B - B^dagger|`` above
    :data:`HERMITICITY_WINDOW` times ``max(1, max |B|)``.
    """
    matrix = np.asarray(block)
    if not np.all(np.isfinite(matrix)):
        return "not finite"
    scale = max(1.0, float(np.max(np.abs(matrix)))) if matrix.size else 1.0
    deviation = float(np.max(np.abs(matrix - matrix.conj().T))) if matrix.size else 0.0
    if deviation > HERMITICITY_WINDOW * scale:
        return f"not Hermitian (max |B - B^dagger| = {deviation:.3e})"
    return None


def oracle_assignment(
    parametrization: JointChoiParametrization, oracle: str
) -> dict[str, str]:
    """Return the backend of every subproblem group, decided before the loop.

    The groups are the independent programs of ``rem:fo-general-format`` (2):
    one per Alice sector in trusted-source mode, one (``"*"``) over every joint
    sector in untrusted-source mode. Under ``"spectral"`` a group goes to the
    closed-form backend exactly when its feasible set is a spectraplex -- no
    declared constraint row, and in trusted-source mode an Alice sector of
    input dimension one -- and to ``"qics"`` otherwise. STRUCTURAL: nothing
    numerical is read, so the assignment is the same at every iterate and a
    group is never re-routed on a failure.
    """
    declaration = parametrization.declaration
    no_rows = not declaration.constraint_list
    if not declaration.is_trusted_source:
        spectral = oracle == "spectral" and no_rows
        return {"*": "spectral" if spectral else "qics"}
    return {
        alice_sector: (
            "spectral"
            if oracle == "spectral"
            and no_rows
            and parametrization.input_dim(alice_sector) == 1
            else "qics"
        )
        for alice_sector in declaration.alice_sectors
    }


def warm_start_point(
    parametrization: JointChoiParametrization,
    seed: WarmStart,
    cold: Mapping[JointSector, Matrix],
    options: FrankWolfeOptions | None = None,
) -> dict[JointSector, Matrix]:
    """Return ``(1 - eps) J_prev + eps J_0``, or refuse a mismatched seed.

    ``cold`` is ``J_0``, the new point's cold start: the interior start, or the
    oracle's zero-cost vertex where the declaration has constraint rows (which
    satisfies them; the interior start need not).

    The feasible set is the same when the source mode (and with it the
    coupling), the joint-sector layout and every block dimension agree and the
    constraint rows are the same rows: none on either side, or the same
    :func:`constraint_rows_digest` on both (a seed file written before the
    digest existed carries none and is refused where rows are present). Then
    the seed is a point of ``Feas^J`` whatever the channel. The seed's CONTENT
    is then checked: finite, Hermitian (to :data:`HERMITICITY_WINDOW`,
    relative), and inside the new point's PSD, coupling and row windows (the
    driver's own starting-point check, at ``options``' windows), each failure
    refused as ``warm_start_not_feasible``.
    """
    declaration = parametrization.declaration
    mode = "trusted" if declaration.is_trusted_source else "untrusted"
    if seed.source_mode != mode:
        raise WarmStartRefused(
            f"the warm-start seed is from a {seed.source_mode}-source "
            f"declaration and this point is {mode}-source; the couplings differ",
            reason="warm_start_source_mode_mismatch",
        )
    rows = constraint_rows_digest(declaration)
    # A seed that declared rows but carries no digest (a file written before
    # the digest existed) cannot show its rows are anybody's: refused either way.
    if (seed.constraint_count and seed.rows_sha256 is None) or (
        seed.rows_sha256 != rows
    ):
        raise WarmStartRefused(
            "the warm-start seed's constraint rows are not this point's: the "
            f"seed declares {seed.constraint_count} row(s) with digest "
            f"{seed.rows_sha256}, this point {len(declaration.constraint_list)} "
            f"with digest {rows}. A row's data defines the feasible set, so a "
            "seed is admitted across points with rows only when the rows are "
            "the same",
            reason="warm_start_constraint_rows_mismatch",
        )
    expected = set(parametrization.joint_sectors)
    if set(seed.blocks) != expected:
        raise WarmStartRefused(
            f"the seed covers {len(seed.blocks)} joint sectors and this point "
            f"has {len(expected)}; the layouts differ "
            f"(first difference: {sorted(set(seed.blocks) ^ expected)[:3]})",
            reason="warm_start_layout_mismatch",
        )
    if seed.layout is not None:
        layout = iterate_layout(parametrization)
        if {key: dict(value) for key, value in seed.layout.items()} != layout:
            raise WarmStartRefused(
                f"the seed's blocks split as {dict(seed.layout)} and this "
                f"point's as {layout}; equal block sizes, different factors",
                reason="warm_start_block_dims_mismatch",
            )
    for pair in parametrization.joint_sectors:
        block = as_matrix(seed.blocks[pair])
        dim = parametrization.block_dim(pair)
        if block.shape != (dim, dim):
            raise WarmStartRefused(
                f"the seed's block on {pair} has shape {block.shape}; this "
                f"point's is ({dim}, {dim})",
                reason="warm_start_block_dims_mismatch",
            )
        problem = hermiticity_defect(block)
        if problem is not None:
            raise WarmStartRefused(
                f"the seed's block on {pair} is {problem}",
                reason="warm_start_not_feasible",
            )
    # The seed itself must lie in the new point's Feas^J at the driver's own
    # windows; the check is the driver's (imported here: it imports this).
    from certiqs_key.meat_core.errors import SupportError
    from certiqs_key.solvers.frank_wolfe.joint_driver import _check_point

    try:
        _check_point(
            parametrization,
            {pair: as_matrix(block) for pair, block in seed.blocks.items()},
            options or FrankWolfeOptions(),
            "warm-start seed",
        )
    except SupportError as failure:
        raise WarmStartRefused(
            str(failure), reason="warm_start_not_feasible"
        ) from failure
    return {
        pair: np.asarray(
            (1.0 - WARM_START_MIX) * as_matrix(seed.blocks[pair])
            + WARM_START_MIX * as_matrix(cold[pair]),
            dtype=np.complex128,
        )
        for pair in parametrization.joint_sectors
    }


__all__ = [
    "HERMITICITY_WINDOW",
    "ORACLE_CHOICES",
    "PAIRWISE_FOLD_BELOW",
    "PAIRWISE_SHRINK",
    "STEP_RULES",
    "WARM_START_MIX",
    "JointFrankWolfeOptions",
    "WarmStart",
    "WarmStartRefused",
    "blocks_digest",
    "constraint_rows_digest",
    "hermiticity_defect",
    "iterate_layout",
    "joint_choices",
    "oracle_assignment",
    "warm_start_point",
]
