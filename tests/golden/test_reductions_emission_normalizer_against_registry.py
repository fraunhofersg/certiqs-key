"""Group PR-Q against the code: ``def:emitnorm``, ``eq:latdown``, the entries.

**THE FREEZE NEEDS A READER.** Group PR-Q of
``tests/oracles/registry_reductions.py`` is the two-instance evidence for
the whole 0.3.0-to-1.0.1 delta -- every value derived by hand from the
accepted text before ``src/certiqs_key/reductions/`` was touched -- and
``tests/oracles`` cannot assert the code against it: its own
independence test pins that the registry imports no part of the package, so a
reader has to live here.

FIVE FROZEN COLLECTIONS ARE READ, AND THEY ARE THE WHOLE OF GROUP PR-Q:

* ``EMISSION_NORMALIZER_CASES`` (EN1--EN4) -- ``def:emitnorm`` on one
  preserved block, read THROUGH :data:`AMENDED_EN` because the
  fidelity-first normalizer replaces the procedure they pin;
* ``WEIGHT_ROUNDING_CASES`` (WR1) -- ``eq:weightroute`` followed by
  ``eq:latdown``, the one emitted number a downstream inequality consumes;
* ``SCALAR_ENTRY_CASES`` (SE1--SE2) -- ``cor:entries``, every constant a real
  scalar and no constant shifted at 1.0.0;
* ``LATTICE_EXPONENT_CASES`` (LK1--LK6) -- the row that runs first;
* ``EMITNORM_IRRATIONAL_DISPLACEMENT`` -- ``eq:displacement`` held as an exact
  square, with the one binary64 value this module emits.

NO FROZEN VALUE IS EDITED HERE AND NONE IS RECOMPUTED FROM THE CODE. Where a
case's expectation and the code disagree, the test fails and the disagreement is
a finding.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest
from reductions_support import emission_normalizer as _emission_normalizer
from registry_reductions import (
    EMISSION_NORMALIZER_CASES,
    EMITNORM_IRRATIONAL_DISPLACEMENT,
    LATTICE_EXPONENT_CASES,
    SCALAR_ENTRY_CASES,
    WEIGHT_ROUNDING_CASES,
    EmissionNormalizerCase,
    LatticeExponentCase,
    ScalarEntryCase,
    WeightRoundingCase,
)

from certiqs_key.foundations.exact import Cx, Matrix, equal, matrix
from certiqs_key.reductions.channels import split_blocks
from certiqs_key.reductions.constraints import (
    DeclaredForm,
    SourceMode,
    probe_expectation_entry,
    restricted_entry,
)
from certiqs_key.reductions.inputs import (
    ProbeDeclaration,
)
from certiqs_key.reductions.normalizer import BlockSnap as _BlockSnap
from certiqs_key.reductions.normalizer import (
    entrywise_max_modulus_squared as _entrywise_max_modulus_squared,
)
from certiqs_key.reductions.reasons import RefusalReason, Relation
from certiqs_key.reductions.validation import (
    rule_emitted_family,
    rule_lattice_exponent,
)
from certiqs_key.reductions.wpfss.construction import (
    flat_sectors,
    wpfss_target,
)
from certiqs_key.reductions.wpfss.weights import (
    BoundedLetter,
    weight_route,
)

F = Fraction

#: The single setting every PR-Q emission case is declared at.
SETTING = "t0"


def _m(frozen: object) -> Matrix:
    """Return a frozen registry matrix in the module's representation."""
    rows = frozen  # type: ignore[assignment]
    return matrix([[Cx(entry[0], entry[1]) for entry in row] for row in rows])  # type: ignore[index,union-attr]


# ---------------------------------------------------------------------------
#  EN1--EN4: def:emitnorm, steps (1) to (4)
# ---------------------------------------------------------------------------


#: EN1--EN4 THROUGH THE FIDELITY-FIRST NORMALIZER, DERIVED BY HAND
#: The frozen cases pin a procedure --
#: round to nearest, absorb into the largest trace, LIFT positivity -- and
#: ``def:emitnorm`` keeps a class on the lattice and otherwise
#: snaps it for fidelity: off-diagonals scaled by ``1 - w``, rounded to
#: nearest, the residue's components hosted in the designation order; it
#: never lifts a handed class that is not positive. The frozen record is not
#: edited; the live side is compared against it THROUGH THIS MAP:
#:
#: * EN1 -- on the lattice and positive: KEPT, emitted unchanged,
#:   ``Delta_s = 0``. The frozen emission stands.
#: * EN2 -- ``(21, 17, 17, 9)/64`` at ``kappa = 4``: not kept, so MOVED by
#:   step (2) at ``w = 0`` (dimension 1, no off-diagonal): rounding to
#:   nearest gives ``5/16, 1/4, 1/4, 1/8`` (``5.25 -> 5``, ``4.25 -> 4``,
#:   ``2.25 -> 2`` sixteenths, no tie); the residue ``1/16`` on index 0 is
#:   hosted by ``y0``, first in the designation order (21 > 17 = 17 > 9, the
#:   tie broken by the declared order), whose support holds index 0: ``3/8``.
#:   Every element is a non-negative number. That is the frozen emitted
#:   family and ``Delta_s = 3/64``.
#: * EN3 -- on the lattice but NOT positive (``e_2(A_y0) = -1/64``): the
#:   handed class is outside ``D_adm``, which the definition's hypothesis
#:   excludes; the normalizer repairs nothing it was handed (fourth property),
#:   passes it through untouched, and step (5) REFUSES it naming positivity.
#:   The frozen lift ``w = 1/8`` is SUPERSEDED.
#: * EN4 -- the same, and the frozen refusal stands: positivity fails at
#:   ``y0`` and step (5) refuses with ``emitted_family_not_admissible``.
AMENDED_EN: dict[str, dict[str, object]] = {
    "EN1-already-on-the-lattice": {"status": "kept", "refused": False},
    "EN2-rounded-and-restored": {
        "status": "moved",
        "step": "snap_for_fidelity",
        "mixing": F(0),
        "hosts": ("y0",),
        "refused": False,
    },
    "EN3-positivity-lift": {"status": "not_admissible", "refused": True},
    "EN4-no-rung-repairs-it": {"status": "not_admissible", "refused": True},
}


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    "case", EMISSION_NORMALIZER_CASES, ids=lambda case: case.case_id
)
def test_the_emission_normalizer_reproduces_every_frozen_case(
    case: EmissionNormalizerCase,
) -> None:
    """The fidelity-first normalizer on the CONSTRUCTED family, against the freeze.

    :data:`AMENDED_EN` says
    case by case what moves and why. Where the frozen emission stands (EN1,
    EN2) every emitted number and ``Delta_s`` is asserted against it; where it
    is superseded (EN3) or the refusal stands (EN4), the refusal is asserted
    as the second gate decides it, naming positivity.
    """
    amended = AMENDED_EN[case.case_id]
    dimension = len(case.constructed[0][1])
    normalized = _emission_normalizer(
        {(letter, SETTING): (_m(block),) for letter, block in case.constructed},
        letters=case.letters,
        settings=(SETTING,),
        probe_weights={SETTING: case.q_t},
        block_dimensions=(dimension,),
        kappa=case.kappa,
    )
    record = normalized.blocks[0]
    snap = record.classes[SETTING]
    assert str(snap.status) == amended["status"]
    order = [(letter, SETTING) for letter in case.letters]
    refusal = rule_emitted_family(
        dict(normalized.family),
        order,
        (dimension,),
        lattice_exponent=case.kappa,
        sector_map_agrees=True,
    )
    if amended["refused"]:
        assert refusal is not None
        assert refusal.reason is RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE
        assert "positive semidefinite" in refusal.detail
        if case.refusal_reason is not None:
            assert case.refusal_reason == str(refusal.reason)
        return
    assert refusal is None
    assert case.emitted is not None
    for letter, expected in case.emitted:
        assert equal(normalized.family[(letter, SETTING)][0], _m(expected))
    assert case.delta_s is not None
    assert record.displacement_squared == case.delta_s * case.delta_s
    if amended["status"] == "kept":
        assert record.already_on_lattice
        assert not record.moved
        return
    assert str(snap.step) == amended["step"]
    assert snap.mixing_weight == amended["mixing"]
    assert snap.hosts == amended["hosts"]
    assert not snap.support_not_preserved


# ---------------------------------------------------------------------------
#  WR1: eq:weightroute, then eq:latdown
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", WEIGHT_ROUNDING_CASES, ids=lambda case: case.case_id)
def test_the_routed_weight_is_the_frozen_lowered_one(
    case: WeightRoundingCase,
) -> None:
    """``p = lat(p^)``, and the frozen case's ``lowered_by`` is the gap.

    "THE EMITTED WEIGHT IS ``p_(y_i,t)`` AND NOT ``p^_(y_i,t)``, and THE
    DIRECTION OF THAT ROUNDING IS THE WHOLE OF WHAT MAKES IT SAFE ... ``lat(.)``
    ONLY LOWERS" (Prop. ``prop:route``). The frozen case also pins that every
    OTHER outcome takes weight zero -- "``p_(y,t) := 0`` for every other
    ``(y, t)``" -- which is asserted here rather than left to the fixture.
    """
    letters = tuple(dict.fromkeys(letter for (letter, _), _ in case.weights))
    settings = tuple(dict.fromkeys(setting for (_, setting), _ in case.weights))
    bounded = letters[0]
    routed = weight_route(
        (
            BoundedLetter(
                letter=bounded,
                weights=((settings[0], case.p_i),),
                absorbing=True,
                r_min=case.r_min,
            ),
        ),
        ProbeDeclaration(settings=settings, weights={settings[0]: case.q_t}),
        [(letter, setting) for letter in letters for setting in settings],
        lattice_exponent=case.kappa,
    )
    assert routed is not None
    assert routed == dict(case.weights)
    assert routed[(bounded, settings[0])] == case.p_emitted
    assert case.p_hat - case.p_emitted == case.lowered_by
    assert case.lowered_by > 0
    assert not case.p_hat_on_lattice
    # The total is accumulated in the declared order and its complement is
    # RECOMPUTED, never rounded on its own (thm:emit (iv)).
    assert sum(routed.values(), start=F(0)) == case.total
    assert 1 - case.total == case.complement


# ---------------------------------------------------------------------------
#  SE1--SE2: cor:entries, the scalar constants
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", SCALAR_ENTRY_CASES, ids=lambda case: case.case_id)
def test_every_emitted_entry_carries_the_frozen_scalar_constant(
    case: ScalarEntryCase,
) -> None:
    """``cor:entries``: a real scalar ``c_k``, and NO CONSTANT IS SHIFTED AT 1.0.0.

    Each frozen case records the 0.3.0 constant it supersedes -- ``-eta_o`` for
    the flag-sector entry and the ``(q_t -/+ delta_t)`` PAIR for the probe
    expectation -- and the 1.0.0 constant is a plain declared number in both
    cases. The superseded forms are asserted ABSENT: a regression to either
    would emit a constant no accepted contract carries.
    """
    # CARRIED WITH THE FLAT CONSTRUCTION RATHER THAN A BRANCHING ONE. The
    # entry could be built on a branching target with the DEGENERATE
    # one-mode model, where the branching target IS the flat one; the
    # constant, the relation and the declared form are what the case freezes,
    # and none of them is a property of the branching model. Building it here
    # keeps the file free of the removable submodule.
    target = wpfss_target(
        (matrix([[F(1, 2)]]), matrix([[F(1, 2)]])), (F(1, 4), F(1, 4))
    )
    sectors = flat_sectors((1,), ("y0,t0", "y1,t0"))
    mode = SourceMode.TRUSTED if case.source_mode == "trusted" else SourceMode.UNTRUSTED

    if case.relation == ">=":
        # THE TARGET ELEMENT IS HANDED OVER AS ITS SECTOR-BLOCK LIST, which is
        # the form an instance carries it in; ``wpfss_target`` writes
        # eq:WPtarget's whole-space array, so
        # the test splits it once, here. THE ENTRY OPERATOR IS A BLOCK LIST
        # TOO.
        entry = restricted_entry(
            tuple(split_blocks(target[0], list(sectors.dimensions))),
            sectors,
            (0, sectors.total_dimension),
            (1, 2),
            case.c_k,
            label=case.ohat,
            certified_against="Lambda^FSS",
            mode=mode,
        )
        assert entry.relation is Relation.GE
    else:
        entry = probe_expectation_entry(
            [
                tuple(split_blocks(element, list(sectors.dimensions)))
                for element in target
            ],
            case.c_k,
            label=case.ohat,
            certified_against="Lambda^FSS",
            mode=mode,
        )
        assert entry.relation is Relation.EQ

    assert entry.constant == case.c_k
    assert isinstance(entry.constant, Fraction)
    assert entry.constant_is_declared is True
    # The declared FORM is the frozen tag, emitted with the entry.
    assert case.form_tag == str(DeclaredForm.HOMOGENEOUS)
    assert entry.form is DeclaredForm.HOMOGENEOUS
    # ONE entry per case: cor:entries emits no pair at 1.0.0.
    assert case.entry_count == 1
    assert "eta" not in str(entry.constant)


# ---------------------------------------------------------------------------
#  LK1--LK6: the lattice-exponent row, which runs first
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", LATTICE_EXPONENT_CASES, ids=lambda case: case.case_id)
def test_the_lattice_exponent_row_decides_every_frozen_case(
    case: LatticeExponentCase,
) -> None:
    """``1 <= kappa <= 53`` and ``kappa + ceil(log2 max{|V|,|Y|,|T|}) <= 53``.

    THREE THINGS UNDER ONE REASON, and the frozen cases cover all three: a
    MISSING exponent (LK5), one outside ``[1, 53]`` (LK3, LK4), and one whose
    accumulation bound Eq. ``eq:latsumcond`` fails (LK2, against LK1 one step
    below it). The pair LK1/LK2 is the boundary and differs by one in ``kappa``.
    """
    refusal = rule_lattice_exponent(
        case.kappa, alphabet_sizes=dict(case.alphabet_sizes)
    )
    if case.admitted:
        assert case.refusal_reason is None
        assert refusal is None
        assert case.bounds_hold and case.accumulation_holds
        return
    assert refusal is not None
    assert str(refusal.reason) == case.refusal_reason
    assert refusal.reason is RefusalReason.LATTICE_EXPONENT_NOT_DECLARED
    assert not (case.bounds_hold and case.accumulation_holds)


# ---------------------------------------------------------------------------
#  eq:displacement: the exact square, and the one binary64 number
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_irrational_displacement_is_carried_as_an_exact_square() -> None:
    """``Delta_s`` is "the square root of an exact rational and IN GENERAL IRRATIONAL".

    The frozen record fixes an entry differing from the constructed one by
    ``(1/64) + i(1/64)``, whose modulus squared is the exact ``1/2048`` and
    whose modulus is ``sqrt(2)/64``. The code holds the SQUARE in the substrate
    and takes the root once, at the boundary, in binary64 -- and the frozen
    ``repr`` is what that produces.
    """
    frozen = dict(EMITNORM_IRRATIONAL_DISPLACEMENT)
    real = frozen["entry_displacement_real"]
    imaginary = frozen["entry_displacement_imag"]
    assert isinstance(real, Fraction) and isinstance(imaginary, Fraction)
    squared = real * real + imaginary * imaginary
    assert squared == frozen["modulus_squared_exact"]
    assert frozen["modulus_is_rational"] is False

    # THE CODE'S OWN PATH TO IT. eq:displacement is an entrywise maximum
    # modulus, and the module takes the maximum ON THE SQUARES -- "x -> x^2
    # being increasing on the non-negative reals, the argmax is the same" --
    # so the substrate never holds the root.
    left = matrix([[Cx(F(1, 2) + real, imaginary)]])
    right = matrix([[Cx(F(1, 2), F(0))]])
    assert _entrywise_max_modulus_squared(left, right) == squared

    # The root is taken ONCE, at the boundary, in binary64, and the frozen repr
    # is what that produces. Nothing reads it: sec:openitems says Delta_s
    # "DECIDES NO PREDICATE, no bound, constant, claim or refusal reads it".
    assert repr(math.sqrt(squared)) == frozen["modulus_binary64_repr"]
    snap = _BlockSnap(block_index=0, classes={}, displacement_squared=squared)
    assert repr(snap.displacement) == frozen["modulus_binary64_repr"]
    # And the closed form the record names, squared, is the same rational.
    assert squared == F(2, 64 * 64)
    assert frozen["modulus_closed_form"] == "sqrt(2) / 64"

