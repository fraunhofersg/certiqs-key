"""Lemma D executed: ``frank-wolfe/lem:feasible-side-dual`` and its requirement.

CONTRACT TESTS on small programs whose minimum over the EXACT feasible set is
known in closed form. Each would fail if the claim were false or the
evaluator broke it:

* the bound never exceeds the minimum, at the optimal dual, at a perturbed
  dual, at a dual of the wrong sign and at zero multipliers (Lemma D (i): no
  dual feasibility is asked);
* it reaches the minimum at the optimal dual, to the eigenvalue bound's
  precision (the bound is TIGHT where it should be, not merely sound);
* an inequality row's multiplier of the wrong sign is shifted into its cone
  (``req:verified-feasible-side`` (ii)); the same multipliers read as an
  equality row's, which needs no shift, put the bound ABOVE the minimum, so
  the shift is what keeps it sound;
* a frame with an error: the bound with the deduction of Lemma D (iv) stays
  below the exact minimum, and the same bound without it lies above; at
  ``d = 2`` the deduction needs its factor ``d_{A_0}`` to do so.

The groups are built here directly (``verified._Group``), in the evaluator's
own data form, so that each program is small enough to solve by hand; the
golden toys run the same evaluator end to end on real declarations
(``tests/golden/test_verified_bracket_against_registry.py``).
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.foundations.dyadic import DyadicMatrix
from certiqs_key.meat_core.objective.joint import AliceFrame, marginal_frame
from certiqs_key.solvers.frank_wolfe.verified import (
    MULTIPLIERS_BACKEND,
    MULTIPLIERS_ZERO,
    GroupSolve,
    _frame_error,
    _Group,
    _group_bound,
    _LiftedRow,
)
from certiqs_key.solvers.oracles.protocol import OracleDual

pytestmark = pytest.mark.contract

#: The refined eigenvalue bound's slack on these tiny matrices (below
#: ``1e-24 ||R||``); "tight" means within this of the minimum.
TIGHT = Fraction(1, 10**20)


def _scalar(value: float) -> DyadicMatrix:
    return DyadicMatrix.from_array(np.array([[value]]))


def _bound(
    group: _Group, gradient: dict, dual: OracleDual | None
) -> tuple[Fraction, str]:
    bound, _, _, source = _group_bound(group, gradient, GroupSolve(None, dual), "t")
    return bound, source


# ---------------------------------------------------------------------------
#  (a) a spectraplex: one-dimensional coupling, no rows (Lemma D (iii))
# ---------------------------------------------------------------------------


def test_a_spectraplex_group_is_bounded_by_its_least_eigenvalue_exactly() -> None:
    """``{J_b >= 0 : sum_b tr J_b = 1}``: the minimum is ``min_b lambda_min(G_b)``.

    The requirement takes ``Y = 0`` there whatever the backend returned, and
    Lemma D (iii) makes that bound the minimum itself.
    """
    group = _Group(
        unit=True,
        input_dim=1,
        pairs={"b1": ("t", "s1"), "b2": ("t", "s2")},
        pad={"b1": 2, "b2": 2},
        lifted=(),
        party_local=(),
        frame=None,
        frame_error=None,
        frame_norm=Fraction(0),
    )
    gradient = {
        ("t", "s1"): np.array([[1.25, 1.0], [1.0, 1.25]]),  # eigenvalues 1/4, 9/4
        ("t", "s2"): np.diag([0.5, 3.0]),
    }
    minimum = Fraction(1, 4)
    for dual in (None, OracleDual(coupling=0.375), OracleDual(coupling=-7.0)):
        bound, source = _bound(group, gradient, dual)
        assert source == MULTIPLIERS_ZERO
        assert minimum - TIGHT <= bound <= minimum


# ---------------------------------------------------------------------------
#  (b) an operator coupling at d = 2, no rows
# ---------------------------------------------------------------------------

#: ``J_1 + J_2 = 1_2``, ``J_s >= 0`` (two sectors of dimension one). With
#: ``G_1 - G_2`` of eigenvalues -2 and 2 the minimum is ``tr G_2 - 2 = 3``,
#: attained at the projectors onto ``(1, -1)`` and ``(1, 1)``; the optimal
#: ``Y`` is ``1 P_- + 2 P_+`` (each eigenvalue's smaller cost), ``tr Y = 3``.
COUPLED = _Group(
    unit=False,
    input_dim=2,
    pairs={"s1": ("t", "s1"), "s2": ("t", "s2")},
    pad={"s1": 1, "s2": 1},
    lifted=(),
    party_local=(),
    frame=_scalar(1.0),
    frame_error=None,
    frame_norm=Fraction(0),
)
COUPLED_GRADIENT = {
    ("t", "s1"): np.array([[2.5, 1.5], [1.5, 2.5]]),
    ("t", "s2"): np.array([[2.5, -0.5], [-0.5, 2.5]]),
}
COUPLED_Y = np.array([[1.5, 0.5], [0.5, 1.5]])


@pytest.mark.parametrize(
    ("label", "coupling"),
    [
        ("optimal", COUPLED_Y),
        ("perturbed", COUPLED_Y + np.array([[0.125, 0.0625], [0.0625, -0.25]])),
        ("wrong sign", -COUPLED_Y),
        ("zero", np.zeros((2, 2))),
    ],
)
def test_a_coupled_group_is_bounded_whatever_the_dual(
    label: str, coupling: np.ndarray
) -> None:
    """Lemma D (i) at ``d_in = 2``: any ``Y`` bounds, the optimal one is the minimum."""
    bound, source = _bound(COUPLED, COUPLED_GRADIENT, OracleDual(coupling=coupling))
    assert source == MULTIPLIERS_BACKEND
    assert bound <= 3, label
    if label == "optimal":
        assert bound >= 3 - TIGHT
    if label == "zero":
        # d_in * min_s lambda_min(G_s) = 2 * min(1, 2), the trace identity.
        assert 2 - TIGHT <= bound <= 2


# ---------------------------------------------------------------------------
#  (c) an inequality row and an equality row
# ---------------------------------------------------------------------------


def _rows_group(inequality: ConstraintRelation) -> _Group:
    """Three sectors of dimension one, ``J_1 + J_2 + J_3 = 1``, and two rows.

    ``J_1 <= 3/8`` (``inequality``, as declared ``preceq``) and ``J_3 = 1/4``,
    on a trusted sector with ``d_A = 1`` and the exact frame ``W = 1``.
    """

    def row(relation: ConstraintRelation, which: int, theta: float) -> _LiftedRow:
        return _LiftedRow(
            relation=relation,
            theta=_scalar(theta),
            operators={
                s: _scalar(1.0 if s == f"s{which}" else 0.0) for s in ("s1", "s2", "s3")
            },
            norm=Fraction(1),
        )

    return _Group(
        unit=False,
        input_dim=1,
        pairs={s: ("t", s) for s in ("s1", "s2", "s3")},
        pad=dict.fromkeys(("s1", "s2", "s3"), 1),
        lifted=(row(inequality, 1, 0.375), row(ConstraintRelation.EQ, 3, 0.25)),
        party_local=(),
        frame=_scalar(1.0),
        frame_error=Fraction(0),
        frame_norm=Fraction(1),
    )


#: Minimise ``2 J_1 + J_2 + 5 J_3``: ``J_3 = 1/4`` and the rest on ``J_2``, so
#: the minimum is ``3/4 + 5/4 = 2`` with the inequality slack. The optimal
#: multipliers (the Lagrangian sign of :class:`OracleDual`): ``Y = 1``,
#: ``Lambda_ineq = 0``, ``Lambda_eq = 4``.
ROWS_GRADIENT = {
    ("t", "s1"): np.array([[2.0]]),
    ("t", "s2"): np.array([[1.0]]),
    ("t", "s3"): np.array([[5.0]]),
}


def _rows_dual(y: float, inequality: float, equality: float) -> OracleDual:
    return OracleDual(
        coupling=np.array([[y]]),
        rows=(np.array([[inequality]]), np.array([[equality]])),
    )


@pytest.mark.parametrize(
    ("label", "dual"),
    [
        ("optimal", _rows_dual(1.0, 0.0, 4.0)),
        ("perturbed", _rows_dual(0.875, -0.25, 4.5)),
        ("wrong sign", _rows_dual(1.0, 1.0, 4.0)),
        ("zero", None),
    ],
)
def test_a_group_with_an_inequality_and_an_equality_row(
    label: str, dual: OracleDual | None
) -> None:
    """The bound is at most 2 for every dual, and 2 at the optimal one."""
    bound, _ = _bound(_rows_group(ConstraintRelation.PRECEQ), ROWS_GRADIENT, dual)
    assert bound <= 2, label
    if label in ("optimal", "wrong sign"):
        # The wrong-signed multiplier of the `preceq` row is shifted to 0
        # (req:verified-feasible-side (ii)), which is the optimal one here.
        assert bound == 2


def test_the_sign_repair_is_what_keeps_a_wrong_sign_sound() -> None:
    """The same multipliers on a row that needs no repair overshoot the minimum.

    Read as an EQUALITY row ``J_1 = 3/8``, ``Lambda = 1`` needs no shift, and
    the bound is the minimum over that smaller set, ``2 (3/8) + 3/8 + 5/4
    = 19/8 > 2``. As the declared ``preceq`` row it is shifted into the cone and
    the bound is 2. Without the shift the evaluator would report 19/8 for the
    ``preceq`` program, above its minimum.
    """
    wrong = _rows_dual(1.0, 1.0, 4.0)
    as_equality, _ = _bound(_rows_group(ConstraintRelation.EQ), ROWS_GRADIENT, wrong)
    assert as_equality == Fraction(19, 8)
    repaired, _ = _bound(_rows_group(ConstraintRelation.PRECEQ), ROWS_GRADIENT, wrong)
    assert repaired == 2


def test_an_untrusted_scalar_row_of_the_wrong_sign_is_repaired() -> None:
    """The scalar form of the same repair.

    ``omega_1 + omega_2 = 1``, ``omega_1 <= 3/8`` (a scalar row, untrusted-source
    mode), minimise ``omega_1``: the minimum is 0, with the row slack. The
    multiplier ``+1`` has the wrong sign for a ``preceq`` row; read as the
    EQUALITY ``omega_1 = 3/8``'s, which needs no repair, it gives ``3/8``.
    Clamped into its cone (``req:verified-feasible-side`` (ii)) it gives 0.
    """

    def scalar_group(relation: ConstraintRelation) -> _Group:
        return _Group(
            unit=True,
            input_dim=1,
            pairs={"b1": ("t", "s1"), "b2": ("t", "s2")},
            pad={"b1": 1, "b2": 1},
            lifted=(
                _LiftedRow(
                    relation=relation,
                    theta=Fraction(3, 8),
                    operators={"b1": _scalar(1.0), "b2": _scalar(0.0)},
                    norm=Fraction(1),
                ),
            ),
            party_local=(),
            frame=None,
            frame_error=None,
            frame_norm=Fraction(0),
        )

    gradient = {("t", "s1"): np.array([[1.0]]), ("t", "s2"): np.array([[0.0]])}
    wrong = OracleDual(coupling=0.0, rows=(1.0,))
    as_equality, _ = _bound(scalar_group(ConstraintRelation.EQ), gradient, wrong)
    assert as_equality == Fraction(3, 8)
    repaired, source = _bound(scalar_group(ConstraintRelation.PRECEQ), gradient, wrong)
    assert source == MULTIPLIERS_BACKEND
    assert repaired == 0


# ---------------------------------------------------------------------------
#  (d) a frame with an error: Lemma D (iv)
# ---------------------------------------------------------------------------


def _framed_group(error: Fraction) -> _Group:
    """``d_A = 1``, ``tau = 1``, so ``W = 1``; the rows are built with ``W~ = 9/8``.

    One equality row ``J_1 = 1/4`` and the objective ``J_2``: the exact minimum
    is ``3/4``. The rows ``W~`` cuts out read ``(81/64) J_1 = 1/4``, whose
    minimum is ``1 - 16/81 = 65/81`` -- ABOVE ``3/4``.
    """
    return _Group(
        unit=False,
        input_dim=1,
        pairs={"s1": ("t", "s1"), "s2": ("t", "s2")},
        pad={"s1": 1, "s2": 1},
        lifted=(
            _LiftedRow(
                relation=ConstraintRelation.EQ,
                theta=_scalar(0.25),
                operators={"s1": _scalar(1.0), "s2": _scalar(0.0)},
                norm=Fraction(1),
            ),
        ),
        party_local=(),
        frame=_scalar(1.125),
        frame_error=error,
        frame_norm=Fraction(9, 8),
    )


def test_the_frame_deduction_keeps_the_bound_below_the_exact_minimum() -> None:
    """With ``eps >= ||W~ - W|| = 1/8`` charged the bound is below 3/4, else above."""
    gradient = {("t", "s1"): np.array([[0.0]]), ("t", "s2"): np.array([[1.0]])}
    # The optimal multipliers of the program the computed frame cuts out.
    dual = OracleDual(coupling=np.array([[1.0]]), rows=(np.array([[-64.0 / 81.0]]),))
    uncharged, _, _, _ = _group_bound(
        _framed_group(Fraction(0)), gradient, GroupSolve(None, dual), "t"
    )
    assert uncharged > Fraction(3, 4)
    assert abs(uncharged - Fraction(65, 81)) < Fraction(1, 10**15)
    charged, deduction, norm, source = _group_bound(
        _framed_group(Fraction(1, 8)), gradient, GroupSolve(None, dual), "t"
    )
    assert source == MULTIPLIERS_BACKEND
    assert charged <= Fraction(3, 4)
    # kappa = d eps (2 ||W~|| + eps) ||Lambda|| max_s ||O_s||, with ||Lambda||
    # bounded by its Frobenius norm rounded up.
    multiplier = abs(Fraction(-64.0 / 81.0))
    assert norm >= multiplier
    assert deduction >= Fraction(1, 8) * (Fraction(9, 4) + Fraction(1, 8)) * multiplier
    assert charged == uncharged - deduction


def test_the_frame_deduction_scales_with_the_input_dimension() -> None:
    """``kappa_r`` carries its factor ``d_{A_0}``.

    ``d = 2``, ``tau = 1_2`` so ``W = 1_2``; the rows are built with
    ``W~ = (9/8) 1_2``. ``J_1 + J_2 = 1_2``, one equality row
    ``W J_1 W^dagger = 1_2``, objective ``tr J_2``: the exact set is the one
    point ``J_1 = 1_2``, ``J_2 = 0``, minimum 0. The rows ``W~`` cuts out give
    ``J_1 = (64/81) 1_2`` and the value ``34/81``, which the optimal multipliers
    of that program (``Y = 1_2``, ``Lambda = -(64/81) 1_2``) reproduce.
    ``kappa = d eps (2 ||W~|| + eps) ||Lambda||`` with ``||Lambda||`` at least
    ``(64/81) sqrt 2`` is about 0.66, so the bound lies below 0; without the
    factor ``d`` it would be about 0.33 and the bound about 0.09, above the
    minimum.
    """
    group = _Group(
        unit=False,
        input_dim=2,
        pairs={"s1": ("t", "s1"), "s2": ("t", "s2")},
        pad={"s1": 1, "s2": 1},
        lifted=(
            _LiftedRow(
                relation=ConstraintRelation.EQ,
                theta=DyadicMatrix.from_array(np.eye(2)),
                operators={"s1": _scalar(1.0), "s2": _scalar(0.0)},
                norm=Fraction(1),
            ),
        ),
        party_local=(),
        frame=DyadicMatrix.from_array(1.125 * np.eye(2)),
        frame_error=Fraction(1, 8),
        frame_norm=Fraction(9, 8),
    )
    gradient = {("t", "s1"): np.zeros((2, 2)), ("t", "s2"): np.eye(2)}
    dual = OracleDual(coupling=np.eye(2), rows=(-(64.0 / 81.0) * np.eye(2),))
    bound, deduction, _, _ = _group_bound(group, gradient, GroupSolve(None, dual), "t")
    assert abs(bound + deduction - Fraction(34, 81)) < Fraction(1, 10**15)
    assert bound + deduction > 0  # the uncharged bound overshoots the minimum 0
    assert bound <= 0


# ---------------------------------------------------------------------------
#  The frame error itself (req:verified-feasible-side (iv))
# ---------------------------------------------------------------------------


def _frame(tau: np.ndarray, *, full: bool) -> AliceFrame:
    built = marginal_frame(tau, full=full)
    w = np.asarray(built.root @ built.iota, dtype=np.complex128)
    return AliceFrame("t", w, built.iota, int(w.shape[1]), w.conj().T @ w, built.full)


@pytest.mark.parametrize("full", [False, True])
def test_the_frame_error_bounds_the_square_roots_rounding(full: bool) -> None:
    """``eps >= |fl(sqrt(t)) - sqrt(t)|`` at every entry, decided exactly."""
    mpmath = pytest.importorskip("mpmath")
    mpmath.mp.dps = 50
    tau = np.diag([0.5, 0.25, 0.0, 0.1]).astype(np.complex128)
    frame = _frame(tau, full=full)
    error = _frame_error(tau, frame, DyadicMatrix.from_array(frame.w))
    assert error is not None
    worst = max(
        abs(mpmath.mpf(float(np.sqrt(t))) - mpmath.sqrt(mpmath.mpf(t)))
        for t in (0.5, 0.25, 0.1)
    )
    assert mpmath.mpf(error.numerator) / error.denominator >= worst
    assert error < Fraction(1, 10**15)


def test_an_exact_frame_has_no_error_and_a_doubtful_one_none() -> None:
    """``0`` where ``W~ = W`` is decided; ``None`` off the diagonal case."""
    exact = np.diag([0.25, 0.5625]).astype(np.complex128)  # roots 1/2 and 3/4
    frame = _frame(exact, full=False)
    assert _frame_error(exact, frame, DyadicMatrix.from_array(frame.w)) == 0
    general = np.array([[0.5, 0.25], [0.25, 0.5]], dtype=np.complex128)
    frame = _frame(general, full=True)
    assert _frame_error(general, frame, DyadicMatrix.from_array(frame.w)) is None
    # A frame non-zero where W vanishes is not the diagonal case either.
    tampered = _frame(exact, full=False)
    w = np.array(tampered.w)
    w[0, 1] = 1e-300
    assert _frame_error(exact, tampered, DyadicMatrix.from_array(w)) is None
