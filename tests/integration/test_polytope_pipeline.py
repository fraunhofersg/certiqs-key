"""The whole pipeline on a NON-SINGLETON acceptance set.

The exit condition of the polytope acceptance-oracle band (spec/architecture.md 6):
a bundle on disk in, a ``certified`` ``KeyRateResult`` out, with the polytope
minimum in place. The ``q`` block of the Frank-Wolfe direction moves on this run,
so the JOINT ``(q, omega)`` optimization Eq. ``eq:hlow-def`` asks for is
exercised in ``q`` as well as in ``omega``.

TOY-8-T-POLY IS BUILT SO THAT ONLY ``q`` CAN MOVE. Its feasible set is the
single point ``omega = tau_A`` (Eq. ``eq:feas`` on a one-dimensional ``Q``), so
``Phi[omega] = (7/8, 1/8)`` is fixed and every bit of the optimization is on the
acceptance side. The run therefore lands on the right answer through the
acceptance oracle or not at all, and the closed-form ``h_low`` it must reach is
derived by hand in ``tests/support/polytope_toys.py`` from the declaration --
never read off a run.

WHY THE START MATTERS. The oracle starts at ``(1/2, 1/2)``, the average of the
two coordinate maximizers, and the infimum is at ``(3/4, 1/4)``. A driver that
ignored the acceptance direction would sit at the start and report an ``h_low``
larger by a visible margin, so ``test_the_run_actually_moves_q`` pins the
distance rather than only the destination.
"""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import pytest
from mode_bundles import build_bundle
from polytope_toys import (
    POLYTOPE_ARGMIN,
    POLYTOPE_H_LOW_AT_ALPHA_1_5,
    POLYTOPE_START,
    general_polytope_toy,
    polytope_toy,
)
from tests.support.provenance import COMPILED
from tests.support.tiers import BRACKET_TIER
from toy_declarations import ToyDeclaration

from certiqs_key.domain.bundle import read_bundle, write_bundle
from certiqs_key.meat_core.acceptance.geometry import POLYTOPE
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet, PolytopeData
from certiqs_key.meat_core.errors import (
    DeclarationError,
    UnsupportedDeclarationError,
)
from certiqs_key.meat_core.objective.support import acceptance_support
from certiqs_key.meat_core.reasons import AssuranceReason
from certiqs_key.solvers.frank_wolfe import FrankWolfeOptions, solve, solve_bundle

#: The Frank-Wolfe step cap is ``1 - 1e-10``, so a run that converges to a
#: vertex of the acceptance set stops that far short of it. The bar here is the
#: residual that cap leaves, not a solver tolerance.
STEP_CAP_RESIDUAL = 1e-8

pytestmark = pytest.mark.requires_qics


def oracle_instance():
    """Return a fresh QICS-backed linear oracle."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return QicsSectorChoiOracle()


def round_trip(toy: ToyDeclaration, directory: Path):
    """Write a toy's bundle to disk and read it back."""
    write_bundle(directory, build_bundle(toy))
    assert (directory / "manifest.json").is_file()
    return read_bundle(directory)


@pytest.mark.contract
@pytest.mark.oracle
def test_a_polytope_declaration_survives_the_disk_and_reaches_its_infimum(
    tmp_path: Path,
) -> None:
    """The estimate path, end to end, against the hand-derived closed form."""
    bundle = round_trip(polytope_toy(), tmp_path / "bundle")
    declaration = declaration_from_bundle(bundle)
    assert declaration.acceptance_set.geometry == POLYTOPE
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    assert result.mathematical_spec_version == "meat-core@1.28.0"
    assert result.h_low == pytest.approx(
        POLYTOPE_H_LOW_AT_ALPHA_1_5, abs=STEP_CAP_RESIDUAL
    )
    # The infimum is ABOVE zero and the length is positive, so the run is not
    # passing by landing on a degenerate answer.
    assert result.h_low > 0.2
    assert result.key_length is not None and result.key_length > 0
    # The certified tier where the ball arithmetic is installed: the
    # polytope's exact acceptance minimum is decided exactly.
    assert result.assurance is BRACKET_TIER


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", [1.1, 1.9])
def test_the_polytope_infimum_tracks_the_closed_form_across_alpha(
    tmp_path: Path, alpha: float
) -> None:
    """The alpha dependence of the joint run, which one alpha cannot show.

    ``h_low = (alpha/(alpha-1)) [ (3/4) log2(6/7) + 1/4 ]`` at EVERY ``alpha``,
    because the objective on this declaration is a positive multiple of the KL
    term alone: TOY-8-T declares ``chat_key = ()``, so Eq. ``eq:Owork`` carries
    only its first sum, the prefactor moves with ``alpha`` and the acceptance
    minimizer does not. The suite runs the polytope end to end at
    ``alpha = 3/2`` only, so an implementation that let the acceptance
    minimization depend on ``alpha`` -- or that reached the box cap by luck at
    one order -- would not be caught. Two further orders inside the key-length
    domain ``(1, 2)`` catch both, and they are the R8 limiting directions: ``1.1``
    approaches ``alpha -> 1+`` where the prefactor blows up, ``1.9`` the other
    endpoint.
    """
    bundle = round_trip(polytope_toy(), tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED, alpha=alpha)
    expected = (alpha / (alpha - 1.0)) * (
        0.75 * math.log2(6.0 / 7.0) + 0.25 * math.log2(2.0)
    )
    assert result.h_low == pytest.approx(expected, rel=1e-6)
    # The minimizer is where it was: the acceptance side does not see alpha.
    for chat, value in POLYTOPE_ARGMIN.items():
        assert result.optimized_q[chat] == pytest.approx(value, abs=STEP_CAP_RESIDUAL)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_run_actually_moves_q(tmp_path: Path) -> None:
    """The acceptance block is optimized, not carried.

    Three things at once: the reported ``q`` is the box cap rather than the
    start, it is still a member of the declared set, and the objective at the
    start is strictly worse -- so a driver that skipped the acceptance direction
    would be caught by the value alone.
    """
    bundle = round_trip(polytope_toy(), tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    for chat, expected in POLYTOPE_ARGMIN.items():
        assert result.optimized_q[chat] == pytest.approx(
            expected, abs=STEP_CAP_RESIDUAL
        )
        assert result.optimized_q[chat] != POLYTOPE_START[chat]
    # Still in the declared set: inside the box and on the simplex.
    assert 0.25 <= result.optimized_q["chat0"] <= 0.75
    assert 0.125 <= result.optimized_q["chat1"] <= 0.75
    assert sum(result.optimized_q.values()) == pytest.approx(1.0, abs=1e-12)
    # What the start would have reported: (alpha/(alpha-1)) D((1/2,1/2)||(7/8,1/8)).
    at_start = 3.0 * (0.5 * math.log2(0.5 / 0.875) + 0.5 * math.log2(0.5 / 0.125))
    assert at_start > result.h_low + 0.3, "the run moved, and it moved downhill"


@pytest.mark.contract
@pytest.mark.oracle
def test_a_certified_run_on_a_polytope_acceptance_set(tmp_path: Path) -> None:
    """The band's exit condition: ``certified``, with the polytope minimum in it.

    Everything the 0.4.0 band asserted of a certified run, on a declaration
    whose acceptance side now goes through instantiation (b) of Remark
    ``rem:acc-side`` -- the dual bound and its componentwise check -- rather
    than through the singleton evaluation.
    """
    bundle = round_trip(polytope_toy(), tmp_path / "bundle")
    estimate = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    certified = solve_bundle(
        bundle, oracle_instance(), compiled=COMPILED
    )
    assert certified.h_low == pytest.approx(estimate.h_low, abs=1e-15)
    assert certified.assurance is BRACKET_TIER  # certified where installed
    assert certified.certificate["assurance_reason"] == "first_order_reported"
    assert certified.h_lb is not None
    # Theorem thm:firstorder, the whole content: h_lb <= h_low IN EXACT REAL
    # ARITHMETIC under Assumption ass:lmo. The comparison below is a
    # DIAGNOSTIC and never an assertion (Section 2.2), which is why it is
    # written with the solver residual and not as a bare inequality.
    assert certified.h_lb <= certified.h_low + STEP_CAP_RESIDUAL
    assert certified.h_lb == pytest.approx(
        POLYTOPE_H_LOW_AT_ALPHA_1_5, abs=STEP_CAP_RESIDUAL
    )
    assert certified.key_length is not None and estimate.key_length is not None
    assert 0 < certified.key_length <= estimate.key_length
    # The length's corollary: the certified one where the run certifies
    # (frank-wolfe/cor:certified-keylength).
    corollary = (
        "cor:certified-keylength"
        if certified.certified["status"] == "certified"
        else "cor:fo-keylength"
    )
    assert corollary in certified.key_length_reason

    payload = certified.as_payload()
    # THE PER-ITERATE BRACKET RECORD REPLACES THE WITNESS PAYLOAD (Section
    # 2.2). The acceptance side is not a witness a record carries: it is
    # DISCHARGED BY CONSTRUCTION on the exact island (Remark rem:acc-side), and
    # what the record carries of it is the boolean acceptance_iterate_exact --
    # "A RECORDED PROPERTY, NEVER A MEASUREMENT".
    per_iterate = payload["optimizer_certificate"]["per_iterate"]
    assert per_iterate
    for record in per_iterate:
        assert record["acceptance_iterate_exact"] is True
        # Every hypothesis held: the gate recorded no withdrawal (the one
        # record's per-iterate entry has no separate `hypotheses_hold` field;
        # it is exactly `withdrawal is None`).
        assert record["withdrawal"] is None
    import json

    json.dumps(payload)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_general_form_and_the_box_form_agree(tmp_path: Path) -> None:
    """``box_bounds`` is a sub-form: both forms reach the same infimum and key.

    ``statistics`` calls the canonical box a sub-form of ``polytope``
    rather than a third tag, and says "a consumer that ignores ``box_bounds``
    still reads a well-formed ``polytope``". So the same ``(B, b)`` declared
    with and without that record must reach the same answer.

    THE PATHS DIFFER. Exact partial minimisation in ``q`` is the loop's one
    ``q`` rule, keyed on the declared geometry: a declared canonical box gets
    the closed-form solve, and a polytope without the record keeps the step
    toward the LP vertex, whose exact partial minimum is not built. So the box
    form lands ON the hand-derived argmin and the general form within the step
    cap's residual of it, and the key length is the same.
    """
    with_box = solve_bundle(
        round_trip(polytope_toy(), tmp_path / "box"),
        oracle_instance(),
        compiled=COMPILED,
    )
    without = solve_bundle(
        round_trip(general_polytope_toy(), tmp_path / "general"),
        oracle_instance(),
        compiled=COMPILED,
    )
    assert with_box.optimized_q == POLYTOPE_ARGMIN
    assert math.isclose(
        with_box.h_low, POLYTOPE_H_LOW_AT_ALPHA_1_5, rel_tol=0.0, abs_tol=1e-15
    )
    assert math.isclose(
        without.h_low,
        POLYTOPE_H_LOW_AT_ALPHA_1_5,
        rel_tol=0.0,
        abs_tol=STEP_CAP_RESIDUAL,
    )
    assert with_box.key_length == without.key_length


@pytest.mark.contract
@pytest.mark.oracle
def test_the_narrowing_a_result_carries_is_the_current_one(tmp_path: Path) -> None:
    """What is narrowed is disclosed.

    The one record every run writes carries no ``scope_narrowings`` field, and
    the disclosure lives where a third tag is refused -- in
    the refusal's own message, which names the two representations this
    polytope run is one of.
    """
    from certiqs_key.meat_core.acceptance.geometry import acceptance_verdict

    result = solve_bundle(
        round_trip(polytope_toy(), tmp_path / "bundle"),
        oracle_instance(),
        compiled=COMPILED,
    )
    assert "scope_narrowings" not in result.certificate
    declaration = declaration_from_bundle(
        round_trip(polytope_toy(), tmp_path / "again")
    )
    unread = replace(
        declaration,
        acceptance_set=AcceptanceSet(geometry="ball", frequencies=(0.5, 0.5)),
    )
    detail = acceptance_verdict(unread).detail
    assert "polytope" in detail and "singleton" in detail
    assert "def:admissible-acceptance-set" in detail
    assert "identically zero" not in detail


# ===========================================================================
#  Fail-closed: an acceptance set the solver cannot use.
# ===========================================================================


@pytest.mark.contract
@pytest.mark.oracle
def test_a_set_forcing_a_zero_weight_runs_and_behaves_as_the_zero_frequency_does(
    tmp_path: Path,
) -> None:
    """C22b END TO END: a proper ``Chat_acc`` is a run, not a wall.

    A non-empty, well-formed polytope can force ``q(chat) = 0`` on an outcome --
    here the degenerate box ``q^- = q^+ = (1, 0)``, whose denotation is the
    single point ``(1, 0)``, so ``Chat_acc = {chat0}`` is a PROPER SUBSET of
    the declared ``Chat``. def:admissible-acceptance-set admits exactly that, and
    Theorem ``thm:firstorder`` states (H-POS) on ``Chat_acc`` rather than on ``Chat``
    for this case by name: on ``Chat`` the hypothesis "would be UNSATISFIABLE
    whenever ``Chat_acc`` is a proper subset ... so that the `first-order` rung
    would be unreachable for a whole class of declarations for no mathematical
    reason". Lemma ``lem:fo-khyp`` (iii) -- claim C22b -- is that weakening,
    and it restricts the two gradient sums to the same set.

    The corollary ``cor:full-gradient`` is consumed through ``lem:fo-khyp``
    (iii), the quantifier is ``Chat_acc``, and a declaration of this shape must
    REACH A RESULT. The parity between the two geometries -- the point the test
    exists to make -- is asserted on the numbers.
    """
    base = declaration_from_bundle(round_trip(polytope_toy(), tmp_path / "bundle"))
    forcing = PolytopeData(
        columns=2,
        rows=((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)),
        rhs=(1.0, 0.0, -1.0, 0.0),
        box_bounds=((1.0, 0.0), (1.0, 0.0)),
    )
    by_polytope = replace(
        base, acceptance_set=AcceptanceSet(geometry=POLYTOPE, polytope=forcing)
    )
    by_singleton = replace(
        base,
        acceptance_set=AcceptanceSet(geometry="singleton", frequencies=(1.0, 0.0)),
    )
    results = []
    for declaration in (by_polytope, by_singleton):
        # Eq. eq:chacc-def on each geometry: the same PROPER subset, which is
        # what makes the two comparable at all.
        assert acceptance_support(declaration) == ("chat0",)
        assert declaration.acceptance_values == ("chat0", "chat1")
        results.append(solve(declaration, oracle_instance(), compiled=COMPILED))

    polytope_result, singleton_result = results
    # THE PARITY, on the numbers. Bit for bit: the two declarations denote the
    # same one-point acceptance set, so the whole run is the same run.
    assert polytope_result.h_low == singleton_result.h_low
    assert polytope_result.h_lb == singleton_result.h_lb
    assert dict(polytope_result.optimized_q) == dict(singleton_result.optimized_q)

    # AND THE RUNG IS REACHED.
    for result in results:
        assert result.h_lb is not None
        assert result.reported_tier is BRACKET_TIER  # certified where installed
        assert result.certificate["assurance_reason"] == "first_order_reported"
        # The coordinate outside Chat_acc sits at exactly 0 and the run does
        # not withdraw on it: lem:fo-khyp (i) makes that the only value it can
        # take at any point of the declared set.
        assert result.optimized_q["chat1"] == 0.0
        # thm:firstorder (ii) in the direction it is stated, up to the
        # arithmetic Remark rem:fo-arithmetic declares unbudgeted -- and that
        # arithmetic is bounded HERE, because Feas^J is one point. d_Q = 1, so
        # the coupling forces J = 1_{A_0}: the iterate is that point exactly
        # and every oracle return S differs from it by its coupling residual,
        # which the driver checks at iterate_coupling (rem:feas-tol: the
        # return is established only in Feas^J(epsilon)). The acceptance
        # direction is zero (a one-point set), so h_lb - h_low = <G, S - 1>,
        # with G = -(alpha/(alpha-1)) (1/ln 2) (1/Phi_0) P_0, P_0 >= 0 of
        # trace Phi_0 = 7/8 on a 2x2 block, whose entrywise 1-norm is at most
        # twice its trace. Hence |h_lb - h_low| <= 2 (alpha/(alpha-1)) / ln 2
        # * iterate_coupling. The joint loop starts at the exact point and sees
        # the backend's error (measured: 4.3e-12 = (3/ln 2) x
        # the QICS return's residual 1.0e-12). A diagnostic, never a refusal.
        alpha = result.alpha
        allowance = (
            2.0 * (alpha / (alpha - 1.0)) / math.log(2.0)
            * FrankWolfeOptions().iterate_coupling
        )
        assert result.h_lb <= result.h_low + allowance


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    ("acceptance", "reason"),
    [
        (
            AcceptanceSet(
                geometry=POLYTOPE,
                polytope=PolytopeData(
                    columns=2,
                    rows=((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)),
                    rhs=(0.25, 0.25, 0.0, 0.0),
                    box_bounds=((0.0, 0.0), (0.25, 0.25)),
                ),
            ),
            AssuranceReason.ACCEPTANCE_SET_EMPTY,
        ),
        (
            AcceptanceSet(
                geometry=POLYTOPE,
                polytope=PolytopeData(
                    columns=2,
                    rows=((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)),
                    rhs=(0.25, 0.75, -0.75, -0.125),
                    box_bounds=((0.75, 0.125), (0.25, 0.75)),
                ),
            ),
            AssuranceReason.ACCEPTANCE_SET_ILL_FORMED,
        ),
        (
            AcceptanceSet(geometry="ball", frequencies=(0.5, 0.5)),
            None,
        ),
    ],
    ids=["empty", "ill-formed", "unsupported"],
)
def test_an_unusable_acceptance_set_is_refused_before_anything_is_computed(
    tmp_path: Path, acceptance: AcceptanceSet, reason: AssuranceReason | None
) -> None:
    """The three unusable sets are REFUSED at validation, on every entry point.

    ``meat-core`` decides every Group A row BEFORE the loop, on both entry
    points, so a declaration carrying one of these sets never reaches an
    iterate at all: it is a typed refusal with the module's own message.

    That is the fail-closed rule, and the frozen entry
    ``O-POLYTOPE-EMPTY-FAIL-CLOSED``'s reason is: "the producer
    and the consumer are separate modules with separate contracts, and a
    consumer that trusts its producer has no defence when the producer is
    wrong". What the test asserts is the refusal rather than the propagation,
    and that no oracle is ever built for such a set.

    ``reason`` is carried through the parametrisation because it names WHICH
    check the set fails, and the refusal's message is asserted to be about that
    check rather than about the symptom the three share. An unread geometry
    has none: frank-wolfe/req:acceptance-geometries refuses it at admission
    and no record names it.
    """
    bundle = round_trip(polytope_toy(), tmp_path / "bundle")
    declaration = replace(declaration_from_bundle(bundle), acceptance_set=acceptance)
    with pytest.raises((DeclarationError, UnsupportedDeclarationError)):
        solve(declaration, oracle_instance(), compiled=COMPILED)
    # And no oracle was ever built for it.
    with pytest.raises(UnsupportedDeclarationError):
        from certiqs_key.solvers.oracles.acceptance import acceptance_oracle

        acceptance_oracle(declaration)
