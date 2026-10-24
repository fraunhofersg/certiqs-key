"""Contract tests of the measurement-family snap: kept, or moved and disclosed.

``foundations/def:snap`` (kept and moved blocks), ``req:snap-reference``
(i)-(iv), ``req:support-safe-snap`` (i)-(iv), ``req:who-snaps`` and
``def:evaluated-off-snap`` (i), as
:func:`certiqs_key.foundations.snap.snap_measurement_family` implements them
with the procedure of spec/architecture.md 2.9. Expected values are derived
by hand beside each test.
"""

from __future__ import annotations

import json
from fractions import Fraction as F
from typing import Any

import numpy as np
import pytest

from certiqs_key.foundations.exact import (
    Matrix,
    diagonal,
    identity,
    is_complete_at,
    is_positive_semidefinite,
    matrix,
    subtract,
)
from certiqs_key.foundations.reference import (
    Enclosure,
    Reference,
    ReferenceBlock,
    ReferenceIdentity,
    ReferenceKind,
    scaled_enclosure,
)
from certiqs_key.foundations.resting import (
    FIX_NOISE_MODEL,
    RestingCause,
    RestingGroup,
)
from certiqs_key.foundations.snap import (
    ASSUMPTION_ID,
    ASSUMPTION_MACHINE_KEY,
    REFUSAL_REASONS,
    BlockStatus,
    SnapRefusedError,
    SnapSettings,
    SnapStep,
    snap_measurement_family,
)

pytestmark = pytest.mark.contract

K = 40


def diag(*values: int | F) -> Matrix:
    """Return the exact diagonal matrix with the given entries."""
    return diagonal([F(v) for v in values])


def floats(m: Matrix) -> np.ndarray:
    """Return the nearest complex128 array of an exact matrix (the 'evaluation')."""
    return np.array(
        [[complex(float(e.re), float(e.im)) for e in row] for row in m],
        dtype=np.complex128,
    )


def exact_reference(
    blocks: dict[str, list[Matrix]], alphabet: tuple[str, ...] = ("a", "b")
) -> Reference:
    """Return an exact reference of the given blocks."""
    return Reference(
        alphabet,
        tuple(
            ReferenceBlock(label, tuple(Enclosure.exact(m) for m in family))
            for label, family in blocks.items()
        ),
        F(1),
        ReferenceIdentity("hand-derived test model", {"source": "this test"}),
    )


def enclosed_reference(blocks: dict[str, list[Matrix]], radius: F) -> Reference:
    """Return a reference of the given blocks enclosed with one radius everywhere."""
    return Reference(
        ("a", "b"),
        tuple(
            ReferenceBlock(
                label,
                tuple(
                    Enclosure(m, tuple(tuple(radius for _ in row) for row in m))
                    for m in family
                ),
                input_radius=radius,
            )
            for label, family in blocks.items()
        ),
        F(1),
        ReferenceIdentity("enclosed toy", {}, ("toy:claim",)),
    )


def snap(
    blocks: dict[str, list[Matrix]],
    alphabet: tuple[str, ...] = ("a", "b"),
    *,
    lattice_exponent: int = K,
    **kwargs: Any,
):  # type: ignore[no-untyped-def]
    """Snap the float evaluation of ``blocks``."""
    data = {label: [floats(m) for m in family] for label, family in blocks.items()}
    return snap_measurement_family(
        data,
        alphabet=alphabet,
        tolerance=1e-9,
        lattice_exponent=lattice_exponent,
        site="bob_povm",
        **kwargs,
    )


# On the lattice: [[1/2, 1/4], [1/4, 1/2]] and its complement, both positive
# definite (eigenvalues 3/4 and 1/4).
ON_A = matrix([[F(1, 2), F(1, 4)], [F(1, 4), F(1, 2)]])
ON_B = subtract(identity(2), ON_A)
# Off the lattice: [[1/3, 1/7], [1/7, 1/5]] (determinant 1/15 - 1/49 > 0) and
# its complement; 1/3 is no multiple of 2^-40.
OFF_A = matrix([[F(1, 3), F(1, 7)], [F(1, 7), F(1, 5)]])
OFF_B = subtract(identity(2), OFF_A)


# ---------------------------------------------------------------------------
#  req:snap-reference (ii): kept, or moved
# ---------------------------------------------------------------------------


def test_an_exact_block_on_the_lattice_is_kept_and_rests_on_nothing() -> None:
    """(ii): F = G with the steps Keep and Decide last; handed; no assumption.

    The H/V analyser's one-photon block has rank-deficient elements on the
    lattice: kept all the same, so rank deficiency is no obstruction where
    nothing moves.
    """
    hv = {"m=0": [diag(0), diag(1)], "m=1": [diag(1, 0), diag(0, 1)]}
    result = snap(hv, ("H", "V"), reference=exact_reference(hv, ("H", "V")))
    assert [b.status for b in result.record.blocks] == [BlockStatus.KEPT] * 2
    for block in result.record.blocks:
        assert block.steps == (SnapStep.KEEP, SnapStep.DECIDE_LAST)
        assert block.reference_kind is ReferenceKind.EXACT
        assert block.handed is not None and block.handed.kind is ReferenceKind.EXACT
        assert not block.rests_on_assumption and block.cause is None
        assert block.group is None
    assert result.record.moved_blocks == ()
    assert result.record.handed_blocks == ("m=0", "m=1")
    assert result.record.assumption is None
    assert result.blocks["m=1"] == tuple(hv["m=1"])
    assert set(result.handed) == {"m=0", "m=1"}


def test_an_exact_block_off_the_lattice_is_moved_on_its_centres() -> None:
    """(ii): the centres are rounded onto 2^-40, so the block is moved.

    The reference is handed, so the block rests on A-SNAP only where the run
    does not evaluate it off its snap: the snap records no cause, and nothing
    rests whatever the run does.
    """
    ref = exact_reference({"m=1": [OFF_A, OFF_B]})
    result = snap({"m=1": [OFF_A, OFF_B]}, reference=ref)
    (block,) = result.record.blocks
    assert block.status is BlockStatus.MOVED
    assert block.reference_kind is ReferenceKind.EXACT
    assert block.defects_ground == "reference"
    assert block.handed is not None
    assert block.cause is None and not block.rests_on_assumption
    assert result.record.moved_blocks == ("m=1",)
    assert result.record.resting_blocks == ()
    assert result.record.assumption is None
    assert SnapStep.LATTICE in block.steps
    assert 0 < block.displacement < 2**-40


def test_data_from_a_model_are_moved_even_where_unchanged() -> None:
    """def:snap: data computed from a model are compared with the model.

    The data are already on the lattice and admissible, so the rows leave
    them unchanged; with no exact reference no exact decision equates them
    with the model, and the block is moved, with no reference handed: it
    rests on A-SNAP with the cause no_reference. Data stated with no model
    behind them, decided unchanged, are kept and rest on nothing.
    """
    from_model = snap({"m=1": [ON_A, ON_B]})
    (block,) = from_model.record.blocks
    assert block.status is BlockStatus.MOVED
    assert block.displacement_squared == 0
    assert block.cause is RestingCause.NO_REFERENCE
    assert block.group is RestingGroup.NO_USABLE_REFERENCE
    assert block.rests_on_assumption
    assert from_model.record.cause is RestingCause.NO_REFERENCE
    stated = snap({"m=1": [ON_A, ON_B]}, data_from_model=False)
    (block,) = stated.record.blocks
    assert block.status is BlockStatus.KEPT and block.cause is None
    assert stated.record.assumption is None


def test_a_partial_reference_is_kept_on_its_exact_blocks() -> None:
    """A declarer holding only its exact blocks: kept there, moved elsewhere.

    The block it holds no reference of rests on A-SNAP with the cause
    no_reference; the one it holds is handed.
    """
    ref = exact_reference({"m=0": [ON_A, ON_B]})
    result = snap({"m=0": [ON_A, ON_B], "m=1": [OFF_A, OFF_B]}, reference=ref)
    blocks = {block.block: block for block in result.record.blocks}
    assert blocks["m=0"].status is BlockStatus.KEPT
    assert blocks["m=1"].status is BlockStatus.MOVED
    assert blocks["m=1"].cause is RestingCause.NO_REFERENCE
    assert result.record.resting_blocks == ("m=1",)
    assert result.record.handed_blocks == ("m=0",)


def test_a_failed_exact_block_does_not_take_a_valid_one_down_with_it() -> None:
    """(i), decided per block.

    A valid exact m=0 block on the lattice beside an exact m=1 "reference"
    that is not positive semidefinite: m=0 is still kept and handed; m=1 is
    neither used nor handed, and rests with the cause reference_failed.
    """
    bad_a = matrix([[F(3, 2), F(0)], [F(0), F(1, 2)]])
    bad_b = subtract(identity(2), bad_a)  # entry -1/2: not PSD
    ref = exact_reference({"m=0": [ON_A, ON_B], "m=1": [bad_a, bad_b]})
    result = snap({"m=0": [ON_A, ON_B], "m=1": [OFF_A, OFF_B]}, reference=ref)
    blocks = {block.block: block for block in result.record.blocks}
    assert blocks["m=0"].status is BlockStatus.KEPT
    assert blocks["m=0"].handed is not None
    assert blocks["m=1"].handed is None
    assert blocks["m=1"].cause is RestingCause.REFERENCE_FAILED
    assert result.record.cause is RestingCause.REFERENCE_FAILED
    assert "m=1/b: not_positive_semidefinite" in result.record.reference_failures
    assert result.record.resting_blocks == ("m=1",)


# ---------------------------------------------------------------------------
#  req:snap-reference (i): the reference handed, and the enclosure opt-out
# ---------------------------------------------------------------------------


def test_an_enclosed_reference_is_handed_and_the_snap_runs_on_the_data() -> None:
    """(i), (ii): an enclosed block is handed; the snap starts from the data.

    Only an exact reference is snapped from; an enclosed one is passed on
    unaltered with its largest radius and its input radius
    (def:evaluated-off-snap (i), req:who-snaps).
    """
    r = F(1, 1 << 60)
    ref = enclosed_reference({"m=1": [OFF_A, OFF_B]}, r)
    result = snap({"m=1": [OFF_A, OFF_B]}, reference=ref)
    (block,) = result.record.blocks
    assert block.status is BlockStatus.MOVED
    assert block.reference_kind is ReferenceKind.NONE
    assert block.defects_ground == "measured"
    assert block.handed is not None
    assert block.handed.kind is ReferenceKind.ENCLOSED
    assert block.handed.largest_radius == r
    assert block.as_record()["handed_reference"] == {
        "kind": "enclosed",
        "largest_radius": str(r),
        "input_radius": str(r),
    }
    assert block.cause is None and not block.rests_on_assumption
    assert result.handed["m=1"] is ref.block("m=1")


def test_the_enclosure_opt_out_hands_the_exact_blocks_alone() -> None:
    """(i), (iii)(a): an enclosed block is not handed, cause enclosure_not_used."""
    r = F(1, 1 << 60)
    enclosed = enclosed_reference({"m=1": [OFF_A, OFF_B]}, r)
    ref = Reference(
        ("a", "b"),
        (exact_reference({"m=0": [ON_A, ON_B]}).block("m=0"), enclosed.block("m=1")),
        F(1),
        enclosed.identity,
    )
    off = snap(
        {"m=0": [ON_A, ON_B], "m=1": [OFF_A, OFF_B]},
        reference=ref,
        settings=SnapSettings(reference_enclosure=False),
    )
    blocks = {block.block: block for block in off.record.blocks}
    assert blocks["m=0"].handed is not None
    assert blocks["m=1"].handed is None
    assert blocks["m=1"].cause is RestingCause.ENCLOSURE_NOT_USED
    assert blocks["m=1"].group is RestingGroup.NO_USABLE_REFERENCE
    assert off.record.settings.reference_enclosure is False
    assert off.record.reference is not None  # the reference held is still named


def test_a_block_the_declarer_withholds_names_the_enclosure_cause() -> None:
    """(iii)(a): a block the declarer withholds names the enclosure cause.

    The receiver carries no enclosure of a block not enclosed exactly where
    the run declares enclosed references not used, and names the block as
    withheld, so its cause is enclosure_not_used and not no_reference.
    """
    ref = exact_reference({"m=0": [ON_A, ON_B]})
    result = snap(
        {"m=0": [ON_A, ON_B], "m=1": [OFF_A, OFF_B]},
        reference=ref,
        withheld_blocks=("m=1",),
    )
    blocks = {block.block: block for block in result.record.blocks}
    assert blocks["m=1"].cause is RestingCause.ENCLOSURE_NOT_USED
    no_reference = snap({"m=1": [OFF_A, OFF_B]}, withheld_blocks=("m=1",))
    assert no_reference.record.cause is RestingCause.ENCLOSURE_NOT_USED


def test_a_failing_reference_is_not_used() -> None:
    """(i): an exact reference not complete is neither used nor handed."""
    bad = exact_reference({"m=1": [OFF_A, diag(F(1, 2), F(1, 2))]})
    result = snap({"m=1": [OFF_A, OFF_B]}, reference=bad)
    assert result.record.cause is RestingCause.REFERENCE_FAILED
    assert "m=1: not_complete" in result.record.reference_failures
    assert result.record.handed_blocks == ()


def test_a_mismatched_reference_is_a_malformed_call() -> None:
    """A reference of another family is refused before anything is snapped."""
    ref = exact_reference({"m=1": [OFF_A, OFF_B]}, ("x", "y"))
    with pytest.raises(ValueError):
        snap({"m=1": [OFF_A, OFF_B]}, reference=ref)


# ---------------------------------------------------------------------------
#  A rotated projective element: the fidelity-first rows
# ---------------------------------------------------------------------------


def test_an_ideal_irrational_ray_is_moved_with_fidelity() -> None:
    """rem:noise-floor's |DD> example, an enclosed reference, snapped on the data.

    No element of {|DD><DD|, 1 - |DD><DD|} is positive definite, and the
    reference is enclosed (irrational), so the snap starts from the binary64
    data, which are within 2^-53 of D = [[1/4, s, 1/4], [s, 1/2, s],
    [1/4, s, 1/4]], s = 1/(2 sqrt 2), and of 1 - D. By hand, at k = 40:
    rounding to nearest gives 1/4, 1/2, 3/4 exactly and s -> 388736063997 /
    2^40 (2^40 s = 388736063996.934...), so the rounded family sums to 1
    (residue zero; ties-to-even is odd-symmetric). The rounded s lies ABOVE
    s, and the rounded D has a negative eigenvalue: positivity fails. The
    coordinate family is T_D = diag(1/4, 1/2, 1/4), T_rest = diag(3/4, 1/2,
    3/4) -- equal to the diagonals -- so the mixture at w scales the
    off-diagonal entries by 1 - w and keeps the diagonal. At the first rung
    w = 2^-36: (1, 3) -> 1/4 - 2^-38, exactly on the lattice; (1, 2) ->
    2^-40 round(388736063997 (1 - 2^-36)) = 388736063991 / 2^40, below s, so
    both elements are positive semidefinite. Nothing is revived. The
    reference is handed, so the block rests on nothing the snap decides.
    """
    half = F(1, 2)
    n = (F(2), F(1), F(2))
    e_dd = scaled_enclosure(matrix([[half] * 3] * 3), n, bits=60)
    e_rest = scaled_enclosure(
        matrix(
            [
                [2 - half, -half, -half],
                [-half, 1 - half, -half],
                [-half, -half, 2 - half],
            ]
        ),
        n,
        bits=60,
    )
    ref = Reference(
        ("D", "rest"),
        (ReferenceBlock("m=2", (e_dd, e_rest), input_radius=F(1, 1 << 61)),),
        F(1),
        ReferenceIdentity(
            "ideal diagonal analyser", {}, ("foundations/lem:enclosure-psd",)
        ),
    )
    dd = np.array([0.5, 1 / np.sqrt(2), 0.5])
    data = {"m=2": [np.outer(dd, dd), np.eye(3) - np.outer(dd, dd)]}
    result = snap_measurement_family(
        data,
        alphabet=("D", "rest"),
        tolerance=1e-9,
        lattice_exponent=K,
        site="bob",
        reference=ref,
    )
    (block,) = result.record.blocks
    assert block.status is BlockStatus.MOVED
    assert block.reference_kind is ReferenceKind.NONE
    assert block.handed is not None and block.handed.kind is ReferenceKind.ENCLOSED
    assert block.steps == (SnapStep.LATTICE, SnapStep.COORDINATE_LIFT)
    assert block.lift_weight == F(1, 1 << 36)
    assert not block.support_not_preserved
    s_lift = F(388736063991, 1 << 40)
    quarter = F(1, 4) - F(1, 1 << 38)
    expected = matrix(
        [
            [F(1, 4), s_lift, quarter],
            [s_lift, F(1, 2), s_lift],
            [quarter, s_lift, F(1, 4)],
        ]
    )
    d_snapped, rest_snapped = result.blocks["m=2"]
    assert d_snapped == expected
    assert rest_snapped == subtract(identity(3), expected)
    assert block.displacement < 2**-37
    assert result.record.assumption is None


# ---------------------------------------------------------------------------
#  req:support-safe-snap
# ---------------------------------------------------------------------------


def test_residue_goes_only_where_the_structural_support_holds_it() -> None:
    """req:support-safe-snap (i), (iii), without a reference, at k = 3.

    D_1..D_3 = diag(0.1, 0), diag(0.2, 0), diag(0.7, 0), D_4 = diag(0, 1).
    At k = 3, 0.1 -> 1/8, 0.2 -> 2/8, 0.7 -> 6/8 (nearest multiples), so the
    residue at (0, 0) is 1 - 9/8 = -1/8. The element of largest trace is D_4
    (trace 1), but index 0 is outside its structural support; among D_1..D_3
    the largest trace is D_3, which receives it: 6/8 - 1/8 = 5/8. D_4's row
    and column 0 stay zero, and so does every other zero.
    """
    data = {
        "m=1": [
            np.diag([0.1, 0.0]),
            np.diag([0.2, 0.0]),
            np.diag([0.7, 0.0]),
            np.diag([0.0, 1.0]),
        ]
    }
    result = snap_measurement_family(
        data,
        alphabet=("a", "b", "c", "d"),
        tolerance=1e-6,
        lattice_exponent=3,
        site="bob",
    )
    assert result.blocks["m=1"] == (
        diag(F(1, 8), 0),
        diag(F(2, 8), 0),
        diag(F(5, 8), 0),
        diag(0, 1),
    )
    (block,) = result.record.blocks
    assert block.residue_placement == ((0, 0, "c"),)
    assert not block.support_not_preserved
    assert block.cause is RestingCause.NO_REFERENCE
    assert block.reference_kind is ReferenceKind.NONE
    assert block.defects_ground == "measured"


def last_resort_data() -> dict[str, list[np.ndarray]]:
    """Return a family the support-safe rows cannot make positive.

    D_1 = [[1/2, b], [b, 0]] with b = 2^-30 is indefinite (least eigenvalue
    about -2 b^2 = -2^-59, within tau) and has a zero diagonal at index 1, so
    its coordinate-family lift (1-w) D_1 + w diag(1/2, 0) keeps the zero
    diagonal beside a non-zero off-diagonal and is never PSD. D_3 = 0 is
    structurally zero. The uniform lift with u = (1/2, 1/4, 1/4) at the
    smallest rung 2^-36 of the ladder restores it: det((1-w) D_1 + (w/2) 1)
    is about w/4 - b^2 = 2^-38 - 2^-60 > 0.
    """
    b = 2.0**-30
    d1 = np.array([[0.5, b], [b, 0.0]])
    d2 = np.array([[0.5, -b], [-b, 1.0]])
    return {"m=1": [d1, d2, np.zeros((2, 2))]}


def test_last_resort_is_flagged_and_may_revive_a_zero_element() -> None:
    """req:support-safe-snap (iv): the uniform lift, flagged support_not_preserved.

    With no reference the block rests in the group last resort, whose fix
    adds the device's noise to the fix of its cause (req:snap-reference
    (iii)).
    """
    result = snap_measurement_family(
        last_resort_data(),
        alphabet=("a", "b", "c"),
        tolerance=1e-6,
        lattice_exponent=K,
        site="bob",
    )
    (block,) = result.record.blocks
    assert block.support_not_preserved
    assert block.steps[-1] is SnapStep.UNIFORM_LIFT_LAST_RESORT
    assert block.lift_weight == F(1, 1 << 36)
    assert block.rests_on_assumption
    assert block.group is RestingGroup.LAST_RESORT
    assert block.fix is not None and FIX_NOISE_MODEL in block.fix
    assert block.group_fix is not None and FIX_NOISE_MODEL in block.group_fix
    assert result.record.support_not_preserved_blocks == ("m=1",)
    # The structurally zero element is revived -- what the flag warns of.
    assert result.blocks["m=1"][2] != diag(0, 0)
    assert all(is_positive_semidefinite(m) for m in result.blocks["m=1"])
    assert is_complete_at(result.blocks["m=1"], F(1))


def test_coordinate_lift_restores_positivity_without_reviving() -> None:
    """req:support-safe-snap (ii): the per-coordinate lift, on the support only.

    D_1 = [[x, b], [b, d]] with x = 1 - 2^-20, b = 2^-17, d = 2^-34:
    det = 2^-34 (1 - 2^-20) - 2^-34 = -2^-54 < 0, within tau. D_2 = 1 - D_1
    is positive definite; D_3 = 0. The coordinate family is T = diag(D_v)
    (each diagonal already sums to one), so the mixture keeps the diagonal and
    shrinks the off-diagonal by (1 - w): det = 2^-34 ((1 - 2^-20) - (1 - w)^2)
    >= 0 iff w >= 1 - sqrt(1 - 2^-20), about 2^-21. The ladder's smallest
    such rung is 2^-20 (2^-24 gives (1 - 2^-24)^2 > 1 - 2^-20). Every entry of
    the mixture at w = 2^-20 is a lattice value at k = 40, and D_3 stays zero.
    """
    x, b, d = 1.0 - 2.0**-20, 2.0**-17, 2.0**-34
    d1 = np.array([[x, b], [b, d]])
    d2 = np.array([[1.0 - x, -b], [-b, 1.0 - d]])
    data = {"m=1": [d1, d2, np.zeros((2, 2))]}
    result = snap_measurement_family(
        data,
        alphabet=("a", "b", "c"),
        tolerance=1e-6,
        lattice_exponent=K,
        site="bob",
    )
    (block,) = result.record.blocks
    assert block.steps == (SnapStep.COORDINATE_LIFT,)
    assert block.lift_weight == F(1, 1 << 20)
    assert not block.support_not_preserved
    assert result.blocks["m=1"][2] == diag(0, 0)
    assert all(is_positive_semidefinite(m) for m in result.blocks["m=1"])


# ---------------------------------------------------------------------------
#  req:snap-reference (iv): the strict option
# ---------------------------------------------------------------------------


def test_strict_refuses_a_moved_block_with_no_reference_handed() -> None:
    """(iv): refused as soon as the resting is decided, naming cause and group."""
    strict = SnapSettings(strict=True)
    assert "strict_snaps" in REFUSAL_REASONS
    with pytest.raises(SnapRefusedError) as caught:
        snap({"m=1": [OFF_A, OFF_B]}, settings=strict)
    assert caught.value.reason == "strict_snaps"
    assert caught.value.block == "m=1"
    assert caught.value.detail["cause"] == "no_reference"
    assert caught.value.detail["group"] == "no_usable_reference"
    # The last resort.
    with pytest.raises(SnapRefusedError) as caught:
        snap_measurement_family(
            last_resort_data(),
            alphabet=("a", "b", "c"),
            tolerance=1e-6,
            lattice_exponent=K,
            site="bob",
            settings=strict,
        )
    assert caught.value.detail["support_not_preserved"] is True
    assert caught.value.detail["group"] == "last_resort"


def test_strict_leaves_a_handed_or_kept_block_to_the_run() -> None:
    """(iv): a moved block with a reference handed is the run's to decide.

    A kept block rests on nothing; a moved block on which the reference is
    handed rests only where the run does not evaluate it off its snap, which
    the run decides after its search. Neither refuses at the snap.
    """
    strict = SnapSettings(strict=True)
    ref = exact_reference({"m=0": [ON_A, ON_B], "m=1": [OFF_A, OFF_B]})
    result = snap(
        {"m=0": [ON_A, ON_B], "m=1": [OFF_A, OFF_B]}, reference=ref, settings=strict
    )
    assert [b.status for b in result.record.blocks] == [
        BlockStatus.KEPT,
        BlockStatus.MOVED,
    ]
    stated = snap({"m=1": [ON_A, ON_B]}, settings=strict, data_from_model=False)
    assert stated.record.blocks[0].status is BlockStatus.KEPT


# ---------------------------------------------------------------------------
#  req:who-snaps: the record
# ---------------------------------------------------------------------------


def test_record_carries_the_run_settings_and_is_json_ready() -> None:
    """req:who-snaps: the two settings, per block facts, the handed blocks."""
    ref = exact_reference({"m=1": [OFF_A, OFF_B]})
    result = snap(
        {"m=1": [OFF_A, OFF_B]},
        reference=ref,
        settings=SnapSettings(reference_enclosure=False),
    )
    record = result.record.as_record()
    assert record["run_settings"] == {
        "reference_enclosure": False,
        "strict_snaps": False,
    }
    assert record["moved_blocks"] == ["m=1"]
    assert record["handed_blocks"] == ["m=1"]
    block = record["blocks"][0]  # type: ignore[index]
    for key in (
        "status",
        "reference_kind",
        "handed_reference",
        "handed_reference_kind",
        "cause",
        "group",
        "fix",
        "group_fix",
        "support_not_preserved",
        "rests_on_assumption",
        "displacement",
    ):
        assert key in block
    for retired in ("weight", "attainable_weight", "absorbing_outcome", "rho"):
        assert retired not in block
    assert block["status"] == "moved"
    assert block["defects_ground"] == "reference"
    json.dumps(record)
    arrays = result.arrays()["m=1"]
    assert all(a.dtype == np.complex128 for a in arrays)


def test_the_groups_and_their_fixes() -> None:
    """req:snap-reference (iii): four groups; each cause names its group."""
    assert {str(group) for group in RestingGroup} == {
        "no_usable_reference",
        "reference_bracket_withdrawn",
        "reference_bracket_not_evaluated",
        "last_resort",
    }
    for cause in (
        RestingCause.NO_REFERENCE,
        RestingCause.REFERENCE_FAILED,
        RestingCause.ENCLOSURE_NOT_USED,
        RestingCause.NO_REFERENCE_COMPANION,
    ):
        assert cause.group is RestingGroup.NO_USABLE_REFERENCE
    assert (
        RestingCause.REFERENCE_BRACKET_WITHDRAWN.group
        is RestingGroup.REFERENCE_BRACKET_WITHDRAWN
    )
    assert (
        RestingCause.REFERENCE_BRACKET_NOT_EVALUATED.group
        is RestingGroup.REFERENCE_BRACKET_NOT_EVALUATED
    )
    assert "reference_enclosure" in RestingCause.ENCLOSURE_NOT_USED.fix
    assert RestingGroup.LAST_RESORT.fix(RestingCause.NO_REFERENCE).startswith(
        FIX_NOISE_MODEL
    )


def test_the_assumption_keys_are_the_ledger_rows() -> None:
    """spec/modules/foundations/interface.yaml: the A-SNAP ledger row.

    The record names the assumption by the id and machine key the module's
    interface declares for ``ass:snapped-measurement``.
    """
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[2]
    interface = yaml.safe_load(
        (root / "spec/modules/foundations/interface.yaml").read_text(encoding="utf-8")
    )
    (row,) = interface["assumption_ledger"]["own_rows"]
    assert row["id"] == ASSUMPTION_ID
    assert row["machine_key"] == ASSUMPTION_MACHINE_KEY
    assert f"foundations/{row['claim']}" == "foundations/ass:snapped-measurement"
    result = snap({"m=1": [OFF_A, OFF_B]})
    assert result.record.assumption == {
        "id": ASSUMPTION_ID,
        "machine_key": ASSUMPTION_MACHINE_KEY,
        "claim": "foundations/ass:snapped-measurement",
        "site": "bob_povm",
        "setting": None,
        "blocks": ["m=1"],
    }
