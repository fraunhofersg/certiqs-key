"""A-COIN at every measured factor, A-LAB per party.

WHY THIS EXISTS. An emission predicate reading the first measured factor only
would miss a public choice declared only at a second station, a missing premise
in the unsafe direction (guard G6). A-COIN is stated over every factor and either
party (``protocol-compiler/ass:coin``; the interface's ``emission_rule``),
allows one ``choice_weighting`` per measured factor and records one
``choice_weighting_record`` entry per weighted factor, naming the factor
(``req:choice-weighting-record``), and merges the two laboratory premises
into ``meat-core/ass:lab``, emitted once per party. These tests would fail
were any of those false:

* G6: a two-station specification whose only public choice is a weighting on
  the SECOND measured factor emits A-COIN, in the compiler's ledger and in the
  run's route-exact assumption set;
* weightings on two factors compile, with two record entries naming the
  factors;
* A-LAB in a run's manifest: at both parties with a key length, at the party
  of A on a trusted run reporting only a bound, nowhere on an untrusted one.

The specifications are BBM92's own (``instances/bbm92``, untrusted pair
source, two passive stations, Alice's test coin), re-ordered or re-weighted
with their public part relabelled to the new product letters: real compiled
declarations, no solve.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from types import SimpleNamespace
from typing import Any

import pytest
from instances.bbm92.surface import default_config, preparation
from tests.support.route_fixtures import route_result

from certiqs_key.foundations.blocks import PRODUCT_LABEL_SEPARATOR
from certiqs_key.protocol_compiler import Party, ProtocolSpecification
from certiqs_key.protocol_compiler.compile import (
    compile_specification,
    public_choice_declared,
)
from certiqs_key.protocol_compiler.reasons import (
    ASSUMPTION_MACHINE_KEYS as COMPILER_KEYS,
)
from certiqs_key.protocol_compiler.reasons import AssumptionId as CompilerId
from certiqs_key.protocol_compiler.weights import ChoiceWeighting, setting_joint_label
from certiqs_key.runs.assumptions import (
    emitted_rows,
    route_exact_assumptions,
    run_claim_roots,
)
from certiqs_key.runs.pipeline import Preparation

pytestmark = pytest.mark.contract

A_COIN = COMPILER_KEYS[CompilerId.A_COIN]
CHOICE_ENCODING = "protocol-compiler/thm:choice-encoding"


def _bbm92() -> Preparation:
    prepared = preparation(default_config())
    assert isinstance(prepared, Preparation), prepared
    return prepared


def _relabelled(
    spec: ProtocolSpecification, relabel: dict[str, list[str]], **partition: Any
) -> ProtocolSpecification:
    """Return ``spec`` with its readout tables keyed by the new product letters.

    ``relabel`` maps each old product letter ``v`` to the new letters that
    replace it; each new letter keeps the readouts of ``v`` (a readout is a
    function of the outcome, so each party observes what it observed). The
    transcript and the acceptance statistic read readouts only and are
    unchanged.
    """
    public = spec.public
    old = public.partition
    assert old is not None
    new = replace(
        old,
        alice_readout={
            (x, w): value
            for (x, v), value in old.alice_readout.items()
            for w in relabel[v]
        },
        bob_readout={
            (x, w): value
            for (x, v), value in old.bob_readout.items()
            for w in relabel[v]
        },
        **partition,
    )
    return replace(spec, public=replace(public, partition=new))


def _coin_on_the_second_factor() -> ProtocolSpecification:
    """BBM92 with its two stations in the other order, parties unchanged.

    Bob's station is the first measured factor and Alice's, which carries the
    test coin, the second: the specification's ONLY public choice is a
    ``choice_weighting`` on the second factor (the source is untrusted at
    ``d_A = 1`` and presents no choice).
    """
    prepared = _bbm92()
    spec = prepared.specification
    declaration = prepared.declaration
    assert declaration.bob_factors is not None
    left, right = declaration.bob_factors.factors
    first, second = spec.receiver_parts
    assert first.choice_weighting is not None and second.choice_weighting is None
    relabel = {
        PRODUCT_LABEL_SEPARATOR.join((a, b)): [PRODUCT_LABEL_SEPARATOR.join((b, a))]
        for a in left.alphabet
        for b in right.alphabet
    }
    reordered = replace(
        spec,
        receiver=second,
        further_receiver_factors=(first,),
        chain=second.chain,
    )
    return _relabelled(
        reordered,
        relabel,
        sector_factor_parties=((Party.BOB,), (Party.ALICE,)),
    )


def _two_weighted_factors() -> ProtocolSpecification:
    """BBM92 with a second coin, ``p`` or ``q`` at one half each, at Bob's station."""
    prepared = _bbm92()
    spec = prepared.specification
    declaration = prepared.declaration
    assert declaration.bob_factors is not None
    left, right = declaration.bob_factors.factors
    _, second = spec.receiver_parts
    coin = ChoiceWeighting(
        choice_alphabet=("p", "q"),
        setting_alphabet=("off",),
        setting_of=dict.fromkeys(right.alphabet, "off"),
        matrix={("off", "p"): Fraction(1, 2), ("off", "q"): Fraction(1, 2)},
    )
    relabel = {
        PRODUCT_LABEL_SEPARATOR.join((a, b)): [
            PRODUCT_LABEL_SEPARATOR.join((a, str(setting_joint_label(b, f))))
            for f in coin.choice_alphabet
        ]
        for a in left.alphabet
        for b in right.alphabet
    }
    weighted = replace(
        spec, further_receiver_factors=(replace(second, choice_weighting=coin),)
    )
    return _relabelled(weighted, relabel)


def _run_with(spec: ProtocolSpecification) -> tuple[Any, SimpleNamespace]:
    """Return the compilation and a finished-run stand-in carrying it.

    The untrusted two-station route's stand-in (``tests/support/route_fixtures``)
    with this specification and its compilation in place of BBM92's: the run
    tier's reading of the compiler's rows and roots is what is tested.
    """
    compiled = compile_specification(spec)
    assert compiled.refusal is None, compiled.refusal
    base = route_result("untrusted-two-station")
    result = SimpleNamespace(**{**vars(base), "compilation": compiled,
                                "specification": spec})
    return compiled, result


# ===========================================================================
#  G6: a public choice declared only at the second station
# ===========================================================================


def test_a_coin_at_the_second_factor_alone_emits_a_coin() -> None:
    """``ass:coin``'s emission rule: "a `choice_weighting` of any measured factor"."""
    spec = _coin_on_the_second_factor()
    assert spec.receiver.choice_weighting is None
    assert public_choice_declared(spec)
    compiled, result = _run_with(spec)
    # The compiler's ledger.
    assert A_COIN in compiled.assumption_ledger
    # The run's manifest: A-COIN engaged, emitted by the compiler, and the
    # theorem it is the premise of among the compiler's roots.
    roots = run_claim_roots(result)
    assert CHOICE_ENCODING in roots["protocol-compiler"]
    found = route_exact_assumptions(roots, emitted_rows(result))
    (coin,) = [entry for entry in found.entries if entry.short_id == "A-COIN"]
    assert {module for module, *_ in coin.emitted_by} == {"protocol-compiler"}
    # Its binding names the weighting of the factor that declares one.
    (bound,) = [value for name, value, _ in coin.bindings if name == "choice_weighting"]
    assert len(bound) == 1  # type: ignore[arg-type]
    # The record names the weighted factor, the second.
    (entry,) = compiled.as_machine_record()["choice_weighting_record"]
    assert entry["factor"] == "alice_station"
    assert spec.receiver_parts[1].factor_label == "alice_station"


def test_without_any_public_choice_no_a_coin_is_emitted() -> None:
    """The converse, on the same specification with the coin removed."""
    spec = _coin_on_the_second_factor()
    bare = replace(
        spec,
        further_receiver_factors=(
            replace(spec.further_receiver_factors[0], choice_weighting=None),
        ),
    )
    assert not public_choice_declared(bare)


# ===========================================================================
#  Two weighted factors: accepted, one record entry each
# ===========================================================================


def test_weightings_at_two_factors_compile_with_one_entry_each() -> None:
    """``choice_weighting``: "at most one per factor"; the record, one per factor."""
    spec = _two_weighted_factors()
    compiled, result = _run_with(spec)
    assert compiled.declaration is not None
    record = compiled.as_machine_record()["choice_weighting_record"]
    assert [entry["factor"] for entry in record] == ["alice_station", "bob_station"]
    for entry in record:
        assert "party" not in entry
    assert record[0]["choice_alphabet"] == ["gen", "test"]
    assert record[1]["choice_alphabet"] == ["p", "q"]
    assert record[1]["matrix"] == {"off|p": "1/2", "off|q": "1/2"}
    assert [item.factor for item in compiled.choice_weightings] == [
        "alice_station", "bob_station",
    ]
    # Both weightings' decisions are in the transcript the gates read.
    assert A_COIN in compiled.assumption_ledger
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    (coin,) = [entry for entry in found.entries if entry.short_id == "A-COIN"]
    (bound,) = [value for name, value, _ in coin.bindings if name == "choice_weighting"]
    assert len(bound) == 2  # type: ignore[arg-type]


def test_two_weightings_are_keyed_by_their_factor_in_the_transcript() -> None:
    """Each factor's ``choice_weighting`` decisions carry that factor's label.

    The transcript's factor rule: with more than one measured factor, a
    decision on one factor's weighting is keyed ``<factor>:<element>``, so no
    two decisions of the compilation share a key.
    """
    compiled = compile_specification(_two_weighted_factors())
    assert compiled.gate_report is not None
    outcomes = compiled.gate_report.transcript.outcomes
    keys = [(o.source, o.predicate, o.element, o.block) for o in outcomes]
    assert len(keys) == len(set(keys))
    elements = {o.element for o in outcomes if str(o.source) == "compilation_map"}
    assert "bob_station:P( . | off)" in elements
    assert not any(
        element is not None and element.startswith("P(") for element in elements
    )


def test_the_run_record_lists_every_weighted_factor() -> None:
    """``compiled.public.choice_weightings`` (record 0.30.0): one entry per factor."""
    from certiqs_key.runs.record import _choice_weightings

    spec = _two_weighted_factors()
    compiled = compile_specification(spec)
    entries = _choice_weightings(compiled.as_machine_record())
    assert [entry["factor"] for entry in entries] == ["alice_station", "bob_station"]
    assert _choice_weightings({"choice_weighting_record": None}) == []


# ===========================================================================
#  A-LAB in a run's manifest, per party
# ===========================================================================


def _lab_parties(result: Any) -> list[str | None]:
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    labs = [entry for entry in found.entries if entry.short_id == "A-LAB"]
    if not labs:
        return []
    (lab,) = labs
    assert lab.snapshot["category"] == "laboratory"
    return [party for _, _, party, _, _ in lab.emitted_by]


@pytest.mark.parametrize("route", ["band-a", "untrusted-two-station"])
def test_a_key_length_run_emits_a_lab_at_both_parties(route: str) -> None:
    """``thm:keylength`` assumes A-LAB at each of the two parties."""
    assert _lab_parties(route_result(route, "key-length")) == ["A", "B"]


def test_a_trusted_run_with_a_bound_only_emits_a_lab_at_the_party_of_a() -> None:
    """``thm:accumulated-entropy``: A-LAB at the party of A, trusted mode."""
    assert _lab_parties(route_result("band-a", "bound-withheld")) == ["A"]


def test_an_untrusted_run_with_a_bound_only_emits_no_a_lab() -> None:
    """In untrusted-source mode without a length, A-LAB is not emitted."""
    result = route_result("untrusted-two-station", "bound-withheld")
    assert _lab_parties(result) == []
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    # Not engaged, with meat-core's own rule quoted, and no discrepancy.
    assert any(
        item.short_id == "A-LAB" and item.module == "meat-core"
        for item in found.not_engaged
    )
    assert "A-LAB" not in {item.short_id for item in found.discrepancies}
