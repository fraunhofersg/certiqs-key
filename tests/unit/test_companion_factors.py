"""The factor enclosures carried from the receiver to the compiled companion.

``reductions/cor:companion-factor-enclosure`` and ``req:reference-companion``
(vii), ``reductions/wpfss/cor:flat-companion``, ``protocol-compiler/
lem:weighted-factor`` and ``req:reference-companion-compiled`` (ii), and
``meat-core/cor:reference-companion-factors``'s chain. CONTRACT TESTS:

* a non-negative combination concatenates the combining blocks' boxes
  unaltered and multiplies their cores by the coefficients exactly; a
  coefficient of zero drops its block, no combining block gives no column, a
  combining block without a factor enclosure gives none, and a negative
  coefficient (no non-negative combination) gives none;
* the flat instance's coefficients are ``q_t R^cg`` (bare) and ``q_t``
  (dark-composed);
* a block handed for only some of its letters carries no factor enclosure;
  a builder that names no non-negative-combination claim (a branching one)
  carries none;
* the compiler's weighting keeps the box and takes the weight into the core;
* on the ideal device the factor enclosures reach the compiled companion.
"""

from __future__ import annotations

from fractions import Fraction as F
from types import SimpleNamespace
from typing import Any

import pytest

from certiqs_key.foundations.exact import Cx
from certiqs_key.foundations.recentring import EntrywiseEnclosure
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.reductions.companion import (
    _datum_factors,
    _handed_rows,
    combined_factor,
)
from certiqs_key.reductions.inputs import HandedReference
from certiqs_key.reductions.wpfss.weights import post_processed_preserved_factors

pytestmark = pytest.mark.contract

ZERO = F(0)


def _cx(x: F | int) -> Cx:
    return Cx(F(x), ZERO)


def _column(a: int, b: int, *, core: F, radius: F = F(1, 2**100)) -> FactorEnclosure:
    return FactorEnclosure(((_cx(a),), (_cx(b),)), ((radius,), (radius,)), (core,))


ONE_ZERO = _column(1, 0, core=F(1, 2))
ZERO_ONE = _column(0, 1, core=F(1, 3))


# cor:companion-factor-enclosure (i)


def test_a_combination_concatenates_the_boxes_and_scales_the_cores() -> None:
    combined = combined_factor([(F(2), ONE_ZERO), (ZERO, None), (F(3), ZERO_ONE)], 2)
    assert combined is not None
    assert combined.centre == ((_cx(1), _cx(0)), (_cx(0), _cx(1)))
    assert combined.radii == (
        (ONE_ZERO.radii[0][0], ZERO_ONE.radii[0][0]),
        (ONE_ZERO.radii[1][0], ZERO_ONE.radii[1][0]),
    )
    assert combined.core == (F(1), F(1))


def test_no_combining_block_gives_no_column() -> None:
    combined = combined_factor([(ZERO, ONE_ZERO), (ZERO, None)], 2)
    assert combined is not None and combined.columns == 0


@pytest.mark.parametrize(
    "terms",
    [
        [(F(1), ONE_ZERO), (F(1, 2), None)],
        [(F(-1), ONE_ZERO)],
        [(F(1), FactorEnclosure.no_column(3))],
    ],
    ids=["a-combining-block-without", "negative", "another-dimension"],
)
def test_none_where_the_corollary_does_not_apply(terms: Any) -> None:
    assert combined_factor(terms, 2) is None


# wpfss/cor:flat-companion: the flat instance's coefficients


def _artifact(form: str) -> Any:
    return SimpleNamespace(
        photon_blocks_form=form,
        channel_grading=SimpleNamespace(block_dimensions=(2,)),
    )


DESCENDED = SimpleNamespace(
    letters=("a", "b"),
    value=lambda row, column: {("a", "a"): F(3, 4), ("a", "b"): F(1, 4),
                               ("b", "a"): F(1, 5), ("b", "b"): F(4, 5)}[(row, column)],
)
PROBE = SimpleNamespace(weights={"t": F(1, 2)})
HANDED = {("a", "t"): (ONE_ZERO,), ("b", "t"): (ZERO_ONE,)}


def test_the_bare_form_combines_with_q_times_r_cg() -> None:
    found = post_processed_preserved_factors(
        _artifact("bare"), PROBE, DESCENDED, [("a", "t")], HANDED  # type: ignore[arg-type]
    )
    (factor,) = found[("a", "t")]
    assert factor is not None
    assert factor.core == (F(1, 2) * F(3, 4) * F(1, 2), F(1, 2) * F(1, 4) * F(1, 3))


def test_the_dark_composed_form_scales_by_q_alone() -> None:
    found = post_processed_preserved_factors(
        _artifact("dark_composed"), PROBE, DESCENDED, [("b", "t")], HANDED  # type: ignore[arg-type]
    )
    (factor,) = found[("b", "t")]
    assert factor is not None and factor.core == (F(1, 2) * F(1, 3),)
    assert factor.centre == ZERO_ONE.centre


# req:reference-companion (vii): where none is carried


def _enclosure(factor: FactorEnclosure | None) -> EntrywiseEnclosure:
    centre = ((_cx(1), _cx(0)), (_cx(0), _cx(0)))
    return EntrywiseEnclosure(centre, ((F(1, 8), ZERO), (ZERO, ZERO)), factor)


def test_a_block_handed_for_some_letters_only_carries_none() -> None:
    block = ((_cx(1), _cx(0)), (_cx(0), _cx(0)))
    call = SimpleNamespace(
        artifact_rows=SimpleNamespace(
            photon_blocks={("a", "t"): (block,), ("b", "t"): (block,)}
        )
    )
    whole = HandedReference(
        blocks={("a", "t"): (_enclosure(ONE_ZERO),), ("b", "t"): (_enclosure(None),)}
    )
    *_, factors = _handed_rows(call, whole)  # type: ignore[arg-type]
    assert factors == {("a", "t"): (ONE_ZERO,), ("b", "t"): (None,)}
    partial = HandedReference(blocks={("a", "t"): (_enclosure(ONE_ZERO),)})
    *_, factors = _handed_rows(call, partial)  # type: ignore[arg-type]
    assert factors == {("a", "t"): (None,), ("b", "t"): (None,)}


def test_a_builder_naming_no_combination_claim_carries_none() -> None:
    from certiqs_key.reductions.wpfss.api import FlatInstanceBuilder

    branching = SimpleNamespace(companion_claim="x")
    assert _datum_factors(branching, None, HANDED) == (None, {})  # type: ignore[arg-type]
    claim, found = _datum_factors(
        FlatInstanceBuilder(), None, {("a", "t"): (None,)}  # type: ignore[arg-type]
    )
    assert claim == "reductions/wpfss/cor:flat-companion" and found == {}


def test_the_record_names_each_elements_cause() -> None:
    from certiqs_key.reductions.companion import ReferenceCompanion

    def record(claim: str | None, factors: Any) -> Any:
        companion = SimpleNamespace(
            target_centre={("a", "t"): (), ("b", "t"): ()},
            target_factors=factors,
            data_sectors=(1,),
            factor_claim=claim,
        )
        return ReferenceCompanion.factor_record(companion)  # type: ignore[arg-type]

    carried = record(
        "reductions/wpfss/cor:flat-companion", {("a", "t"): (None, ONE_ZERO)}
    )
    assert carried["carried"] == 1 and carried["cause"] is None
    assert [item["cause"] for item in carried["elements"]] == [
        None,
        "combining_block_without_factor",
    ]
    assert carried["elements"][0]["columns"] == 1
    none = record(None, {})
    assert none["carried"] == 0
    assert none["cause"] == "no_non_negative_combination_claim"
    assert {item["cause"] for item in none["elements"]} == {
        "no_non_negative_combination_claim"
    }


# protocol-compiler/lem:weighted-factor


def test_the_weighting_keeps_the_box_and_scales_the_core() -> None:
    from certiqs_key.protocol_compiler.companion import _weighted, _weighted_factor

    weighted = _weighted_factor(ONE_ZERO, F(1, 3))
    assert weighted is not None
    assert (weighted.centre, weighted.radii) == (ONE_ZERO.centre, ONE_ZERO.radii)
    assert weighted.core == (F(1, 6),)
    weighting = SimpleNamespace(
        setting_of={"v": "s"},
        choice_alphabet=("f", "g"),
        weight=lambda setting, choice: F(1) if choice == "f" else F(0),
    )
    specification = SimpleNamespace(
        receiver_parts=[SimpleNamespace(choice_weighting=weighting)]
    )
    labels, _, _, factors = _weighted(
        ("v",), {"v": ((),)}, {"v": ((),)}, specification, 0,  # type: ignore[arg-type]
        {"v": (ONE_ZERO,)},
    )
    (label,) = labels
    assert factors == {label: (_weighted_factor(ONE_ZERO, F(1)),)}


# The chain on the ideal device: receiver -> reductions -> compiler


def test_the_ideal_devices_factors_reach_the_compiled_companion() -> None:
    from instances.optical_bb84.surface import default_config, preparation

    from certiqs_key.protocol_compiler.companion import CompiledReferenceCompanion
    from certiqs_key.runs.config import SolverSettings

    base = default_config(solver=SolverSettings(method="fw", max_iterations=3))
    prep = preparation(
        base.with_(
            device={
                **base.device,
                "photon_cutoff": F(2),
                "exact_window": F(3),
                "half_wave_angle": F(1, 7),
            }
        )
    )
    companion = prep.reduction_artifact.reference_companion
    record = companion.factor_record()
    assert record["claim"] == "reductions/wpfss/cor:flat-companion"
    assert record["carried"] > 0
    compiled = prep.reference_companion
    assert isinstance(compiled, CompiledReferenceCompanion)
    (factor,) = compiled.factors
    carried = [
        enclosure
        for row in factor.factor_enclosures.values()
        for enclosure in row
        if enclosure is not None
    ]
    assert carried and any(enclosure.columns == 1 for enclosure in carried)
    # The flat instance's scalar (flag) sectors carry none.
    for row in factor.factor_enclosures.values():
        for index, enclosure in enumerate(row):
            if index not in companion.data_sectors:
                assert enclosure is None
