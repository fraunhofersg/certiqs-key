"""statistics emits the assumption ledger its interface describes.

``spec/modules/statistics/interface.yaml`` describes an assumption ledger, its
own rows "emitted as the `assumption_ledger` output key: the machine key of
each row below, as `emission_rule` says". The expectations here are read off
that interface file, row by row, so the two cannot drift: the short ids, the
machine keys and the claims from its ``own_rows``, the never-verified flags
from its ``never_verified`` block, which rows each route carries from its
``emission_rule``.

THE ROWS FOLLOW THE ROUTE: a run lists what its results rest on. So the rows a route
carries are held to the assumption closure of the results it reports, read from the
shipped claim-closure table: for the constructed box its completeness bound,
its honest containment and the box oracle behind the emitted acceptance
support; for a declared singleton its completeness. A test that held the rows
to the interface alone would pass while both drifted from the claims
together.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
import yaml

from certiqs_key.domain.claim_closure import (
    ACCEPTANCE_ROOTS,
    COMPLETENESS_ROOTS,
    claim_closure,
)
from certiqs_key.statistics import (
    EMISSION_BY_ROUTE,
    ENVELOPE_MODEL_TAG,
    HONEST_MODEL_TAG,
    AcceptanceConstruction,
    AcceptanceRequest,
    AcceptanceRoute,
    GeometryTag,
    HonestEnvelope,
    HypothesisError,
    InfeasibleInput,
    MalformedInputError,
    assumption_ledger,
    construct,
)
from certiqs_key.statistics.ledger import LEDGER_CLAIMS, LEDGER_IDS, MACHINE_KEYS

ROOT = Path(__file__).resolve().parents[2]

#: The results each route reports: for the constructed box, its completeness
#: bound, its honest containment and the box oracle whose (i) is the emitted
#: acceptance support; for a declared singleton, its completeness figure.
ROOTS_OF = {
    AcceptanceRoute.CONSTRUCTED_BOX: (
        "statistics/binomial-box/thm:completeness-bound",
        "statistics/binomial-box/thm:honest-containment",
        "statistics/thm:box-oracle",
    ),
    AcceptanceRoute.DECLARED_SINGLETON: (
        "statistics/singleton/thm:singleton-completeness",
    ),
}

HALF = Fraction(1, 2)
LAW = (("a", "1/2"), ("b", "1/2"))
BOUNDS = (("lower", (("a", "2/5"), ("b", "2/5"))),
          ("upper", (("a", "3/5"), ("b", "3/5"))))


def _interface() -> dict[str, Any]:
    path = ROOT / "spec" / "modules" / "statistics" / "interface.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _rows(route: AcceptanceRoute, **overrides: Any) -> tuple[Any, ...]:
    arguments: dict[str, Any] = {
        "alphabet": ("a", "b"),
        "rounds": 100,
        "honest": (HALF, HALF),
    }
    arguments.update(overrides)
    return assumption_ledger(route, **arguments)


def _envelope(route: AcceptanceRoute) -> tuple[Any, ...]:
    return _rows(route, honest=(Fraction(2, 5), Fraction(2, 5)),
                 honest_upper=(Fraction(3, 5), Fraction(3, 5)))


def _request(honest: Any) -> AcceptanceRequest:
    return AcceptanceRequest(
        alphabet=("a", "b"),
        honest=honest,
        rounds=100,
        budget=Fraction(1, 100),
        constrained=("a", "b"),
    )


def test_the_constants_are_the_interface_s_own_rows_in_its_order() -> None:
    block = _interface()["assumption_ledger"]
    declared = [(row["id"], row["machine_key"], f"statistics/{row['claim']}")
                for row in block["own_rows"]]
    assert [(i, MACHINE_KEYS[i], LEDGER_CLAIMS[i]) for i in LEDGER_IDS] == declared
    # No row is inherited (Q4 (a)): A-TSM is declared by two remarks and by no
    # result whose figure this module reports.
    assert "inherited_rows" not in block
    assert set(block["emission_rule"]) == set(LEDGER_IDS)


def test_every_machine_key_is_an_identifier() -> None:
    """There are no ``key = value`` prose keys."""
    for key in MACHINE_KEYS.values():
        assert key.isidentifier(), key


@pytest.mark.contract
@pytest.mark.parametrize("route", list(AcceptanceRoute))
def test_each_route_emits_the_closure_of_the_results_it_reports(
    route: AcceptanceRoute,
) -> None:
    assert set(ROOTS_OF[route]) <= {*COMPLETENESS_ROOTS, *ACCEPTANCE_ROOTS}
    closure: set[str] = set()
    for root in ROOTS_OF[route]:
        closure |= set(claim_closure(root)["assumptions"])
    emitted = [row.assumption_id for row in _rows(route)]
    assert set(emitted) == closure
    # In the interface's own_rows order, and as the emission rule declares.
    assert emitted == [i for i in LEDGER_IDS if i in closure]
    assert tuple(emitted) == EMISSION_BY_ROUTE[route]


def test_the_box_never_carries_a_hon_nor_the_singleton_a_reach() -> None:
    box = {row.assumption_id for row in _rows(AcceptanceRoute.CONSTRUCTED_BOX)}
    single = {row.assumption_id
              for row in _rows(AcceptanceRoute.DECLARED_SINGLETON)}
    assert box == {"A-HON-ENV", "A-ALPHABET", "A-REACH"}
    assert single == {"A-HON", "A-ALPHABET"}
    assert "A-TSM" not in box | single


def test_the_never_verified_flags_are_the_interface_s() -> None:
    never = _interface()["never_verified"]
    assert set(never) == {"own", "note"}
    marked = set(never["own"])
    assert marked == {"A-HON", "A-HON-ENV", "A-ALPHABET", "A-REACH"}
    for route in AcceptanceRoute:
        for row in _rows(route):
            assert row.never_verified is (row.assumption_id in marked), row
            assert row.owner == "statistics"
            assert row.claim == LEDGER_CLAIMS[row.assumption_id]


@pytest.mark.contract
def test_the_rows_bind_the_declared_values_their_clauses_are_about() -> None:
    """A law: the distribution; an envelope: both vectors; exact rationals as p/q."""
    law = {row.assumption_id: dict(row.constrains)
           for row in _rows(AcceptanceRoute.CONSTRUCTED_BOX)}
    assert law["A-HON-ENV"] == {
        "honest_model": HONEST_MODEL_TAG,
        "honest_distribution": LAW,
        "rounds": 100,
    }
    assert law["A-ALPHABET"] == {"acceptance_alphabet": ("a", "b"), "rounds": 100}
    assert law["A-REACH"] == {"honest_distribution": LAW}
    single = {row.assumption_id: dict(row.constrains)
              for row in _rows(AcceptanceRoute.DECLARED_SINGLETON)}
    assert single["A-HON"] == law["A-HON-ENV"]
    envelope = {row.assumption_id: dict(row.constrains)
                for row in _envelope(AcceptanceRoute.CONSTRUCTED_BOX)}
    assert envelope["A-HON-ENV"] == {
        "honest_model": ENVELOPE_MODEL_TAG,
        "honest_envelope": BOUNDS,
        "rounds": 100,
    }
    assert envelope["A-REACH"] == {"honest_envelope": BOUNDS}


def test_the_tag_is_derived_from_the_envelope_so_it_cannot_disagree() -> None:
    """No caller passes the tag."""
    for rows, tag in ((_rows(AcceptanceRoute.CONSTRUCTED_BOX), HONEST_MODEL_TAG),
                      (_envelope(AcceptanceRoute.CONSTRUCTED_BOX), ENVELOPE_MODEL_TAG)):
        bound = {dict(row.constrains).get("honest_model") for row in rows} - {None}
        assert bound == {tag}
    with pytest.raises(TypeError):
        _rows(AcceptanceRoute.CONSTRUCTED_BOX, honest_model=ENVELOPE_MODEL_TAG)


def test_a_declared_singleton_with_an_envelope_is_refused() -> None:
    """Its honest input is a single law (singleton/req:singleton-point-form)."""
    with pytest.raises(HypothesisError, match="singleton-point-form"):
        _envelope(AcceptanceRoute.DECLARED_SINGLETON)


def test_a_ledger_for_no_route_or_mismatched_vectors_is_refused() -> None:
    with pytest.raises(MalformedInputError, match="route"):
        _rows("ellipsoid")  # type: ignore[arg-type]
    # The bare geometry tag is no route: a declared polytope rests on none of
    # the box's results.
    with pytest.raises(MalformedInputError, match="route"):
        _rows(GeometryTag.POLYTOPE)  # type: ignore[arg-type]
    with pytest.raises(MalformedInputError, match="differ in length"):
        _rows(AcceptanceRoute.CONSTRUCTED_BOX, honest=(HALF,))


def test_the_ledger_and_the_construction_are_immutable_and_hashable() -> None:
    """Tuples of pairs, no dict or list.

    A frozen construction that carried a dict could be neither hashed nor
    trusted not to change after it was emitted.
    """
    def immutable(value: object) -> bool:
        if isinstance(value, tuple):
            return all(immutable(item) for item in value)
        return isinstance(value, str | int)

    for route in AcceptanceRoute:
        for row in _rows(route):
            assert immutable(row.constrains), row
            hash(row)
    for row in _envelope(AcceptanceRoute.CONSTRUCTED_BOX):
        assert immutable(row.constrains), row
    for honest in ({"a": HALF, "b": HALF},
                   HonestEnvelope(lower={"a": Fraction(2, 5), "b": Fraction(2, 5)},
                                  upper={"a": Fraction(3, 5), "b": Fraction(3, 5)})):
        result = construct(_request(honest))
        assert isinstance(result, AcceptanceConstruction)
        hash(result.assumption_ledger)
        hash(result)


def test_the_output_row_exists_and_every_result_carries_the_box_ledger() -> None:
    outputs = {row["name"]: row for row in _interface()["outputs"]}
    assert "assumption_ledger" in outputs
    result = construct(_request({"a": HALF, "b": HALF}))
    assert isinstance(result, AcceptanceConstruction)
    assert result.acceptance_set.tag is GeometryTag.POLYTOPE
    assert result.acceptance_set.is_canonical_box
    assert result.assumption_ledger == _rows(AcceptanceRoute.CONSTRUCTED_BOX)
    refused = construct(
        AcceptanceRequest(
            alphabet=("a", "b"),
            honest={"a": HALF, "b": HALF},
            rounds=0,
            budget=Fraction(1, 100),
            constrained=("a", "b"),
        )
    )
    # NO ACCEPTANCE SET, NO LEDGER: the refusal branch has nothing to read.
    assert isinstance(refused, InfeasibleInput)
    assert not hasattr(refused, "assumption_ledger")


def test_an_envelope_run_binds_the_envelope_and_a_degenerate_one_its_law() -> None:
    def ledger(lower: dict[str, Fraction], upper: dict[str, Fraction]) -> Any:
        result = construct(_request(HonestEnvelope(lower=lower, upper=upper)))
        assert isinstance(result, AcceptanceConstruction)
        rows = {row.assumption_id: dict(row.constrains)
                for row in result.assumption_ledger}
        # The record's tag and the ledger's are the one decision.
        assert rows["A-HON-ENV"]["honest_model"] == result.honest_model.tag
        return rows

    drifting = ledger({"a": Fraction(2, 5), "b": Fraction(2, 5)},
                      {"a": Fraction(3, 5), "b": Fraction(3, 5)})
    assert drifting["A-HON-ENV"]["honest_model"] == ENVELOPE_MODEL_TAG
    assert drifting["A-HON-ENV"]["honest_envelope"] == BOUNDS
    degenerate = ledger({"a": HALF, "b": HALF}, {"a": HALF, "b": HALF})
    assert degenerate["A-HON-ENV"]["honest_model"] == HONEST_MODEL_TAG
    assert degenerate["A-HON-ENV"]["honest_distribution"] == LAW
