"""The route-exact assumption set: the reconciliation rules and the adapter.

WHY THIS EXISTS. "The report lists the route-exact set from one reconciled list
... A test fails when ledger rows and closure disagree."
``certiqs_key.runs.assumptions.route_exact_assumptions`` is that list. The
first half of this file holds its rules on a hand-written table and
hand-written rows, so each rule is seen in isolation. The second half holds the
adapter ``emitted_rows`` to what the real emitters emit on the route fixtures:
who is named as an emitter, which rows are engaged, and which emitters one
deduplicated entry lists.

The agreement of real ledgers with the real closures is
``tests/unit/test_ledger_closure_agree.py``; the roots per route are
``tests/unit/test_run_claim_roots.py``.
"""

from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction
from typing import Any

import pytest
from tests.support.route_fixtures import ROUTES, route_result

from certiqs_key.domain.claim_closure import ClaimClosureError
from certiqs_key.protocol_compiler.reasons import (
    ASSUMPTION_MACHINE_KEYS as COMPILER_KEYS,
)
from certiqs_key.runs.assumptions import (
    DiscrepancyKind,
    EmittedRow,
    Section,
    emitted_rows,
    route_exact_assumptions,
    run_claim_roots,
)

pytestmark = pytest.mark.contract


# ===========================================================================
#  A hand-written table: the rules, one at a time
# ===========================================================================


def _assumption(
    key: str,
    owner: str,
    *,
    verification: str = "never",
    category: str | None = "protocol-structure",
    emission: dict[str, str] | None = None,
    refines: str | None = None,
) -> dict[str, Any]:
    return {
        "machine_key": key,
        "owner": owner,
        "verification": verification,
        "verification_sentence": f"sentence for {verification}",
        "title": f"title of {owner}",
        "summary": f"summary of {owner}",
        "user_statement": f"statement of {owner}",
        "category": category,
        "affects": ["secrecy"],
        "refines": refines,
        "status": "accepted",
        "effective_status": "accepted",
        "contract": {"pdf": "spec/modules/x/contract.pdf", "anchor": f"claim-{owner}"},
        "emission": emission or {},
    }


def _root(*short_ids: str) -> dict[str, Any]:
    owners = {sid: f"owner/{sid}" for sid in short_ids}
    return {"claims": ["root"], "assumptions": owners}


TABLE: dict[str, Any] = {
    "assumptions": {
        "A-SEQ": _assumption("sequential_round_model", "transmitter/ass:seq"),
        "A-AUTH": _assumption(
            "classical_channel_authenticated",
            "meat-core/ass:auth",
            category="channel-and-adversary",
            emission={"meat-core": "on every run that reports a key length"},
        ),
        "A-LMO": _assumption(
            "exact_linear_oracle",
            "meat-core/frank-wolfe/ass:lmo",
            category="numerical-trust",
        ),
        "A-EIG": _assumption(
            "exact_window_eigenvalue_slack",
            "receiver/ass:eig",
            category="numerical-trust",
        ),
        # A refinement that restates its whole parent (A-WCP and A-ENS), and
        # one that narrows its parent to a part (A-ALICE-MEAS and A-SPEC).
        "A-ENS": _assumption("source_ensemble", "transmitter/ass:ens"),
        "A-WCP": _assumption(
            "wcp_source_model", "transmitter/decoy/ass:wcp", refines="A-ENS"
        ),
        "A-SPEC": _assumption(
            "specification_describes_apparatus", "protocol-compiler/ass:spec"
        ),
        "A-ALICE-MEAS": _assumption(
            "alice_measurement_as_declared",
            "protocol-compiler/ass:alice-meas",
            refines="A-SPEC",
        ),
        "A-TSM": _assumption("test_statistics_model", "reductions/ass:tsm"),
        "A-LINK": _assumption(
            "reduction_chain_sound",
            "protocol-compiler/ass:link",
            category="supplied-artefact",
            emission={"protocol-compiler": "always"},
        ),
        "A-ORPHAN": _assumption("orphan_key", "elsewhere/ass:orphan"),
    },
    "roots": {
        "meat-core/thm:main": _root("A-SEQ", "A-AUTH", "A-LMO"),
        "transmitter/thm:source": _root("A-ENS", "A-SPEC"),
        "receiver/thm:emitted": _root("A-EIG"),
        "protocol-compiler/thm:band": _root("A-LINK"),
        "elsewhere/thm:orphan": _root("A-ORPHAN"),
    },
}

VOCABULARIES = {
    "meat-core": frozenset({"A-SEQ", "A-AUTH", "A-LMO", "A-TSM"}),
    "transmitter": frozenset({"A-SEQ", "A-ENS", "A-WCP", "A-SPEC", "A-ALICE-MEAS"}),
    "reductions": frozenset({"A-SEQ", "A-TSM"}),
    "receiver": frozenset({"A-EIG"}),
    "protocol-compiler": frozenset({"A-LINK"}),
}
MAIN = {"meat-core": ["meat-core/thm:main"]}
WITH_RECEIVER = {**MAIN, "receiver": ["receiver/thm:emitted"]}


def reconcile(
    roots: dict[str, list[str]],
    rows: list[EmittedRow],
    **options: Any,
) -> Any:
    return route_exact_assumptions(
        roots, rows, vocabularies=VOCABULARIES, table=TABLE, **options
    )


def row(key: str, module: str = "meat-core", **fields: Any) -> EmittedRow:
    return EmittedRow(machine_key=key, emitted_by=module, **fields)


def test_a_premise_outside_every_closure_is_listed_and_flagged() -> None:
    """``emitted_not_in_closure``: still a premise, because overstating is safe."""
    rows = [row("sequential_round_model"), row("test_statistics_model")]
    found = reconcile(MAIN, rows)
    assert "A-TSM" in found.section(Section.ASSUMPTIONS)
    assert found.kinds(DiscrepancyKind.EMITTED_NOT_IN_CLOSURE) == ("A-TSM",)
    (item,) = found.discrepancies
    # An emitter is (module, station, party) since record 0.30.0.
    assert item.emitted_by == (("meat-core", None, None),)


@pytest.mark.parametrize("verification", ["decided", "discharged"])
def test_a_table_carrying_a_retired_verification_is_refused(verification: str) -> None:
    """``decided`` and ``discharged`` are not in the vocabulary.

    No ``checks`` section is held for such rows; both values are refused on
    every assumption, so a table carrying one is stale and is refused, as the
    package's own accessors refuse it.
    """
    table = json.loads(json.dumps(TABLE))
    table["assumptions"]["A-TSM"]["verification"] = verification
    with pytest.raises(ClaimClosureError, match=verification):
        route_exact_assumptions(MAIN, [], vocabularies=VOCABULARIES, table=table)
    assert {str(section) for section in Section} == {"assumptions", "numerics"}


def test_a_closure_member_a_ran_module_did_not_emit_is_not_engaged() -> None:
    """With the module's emission rule from the table, quoted as the rule.

    The rule says when the row IS emitted, so it is introduced as the rule and
    followed by the fact that the route does not meet it; quoted bare, it
    would read as the condition of the row's absence.
    """
    found = reconcile(MAIN, [row("sequential_round_model")])
    reasons = {(item.short_id, item.module): item.reason for item in found.not_engaged}
    assert reasons[("A-AUTH", "meat-core")] == (
        "emission rule: on every run that reports a key length; "
        "not met on this route"
    )
    # A ran module whose interface states no rule: the generic reason.
    assert reasons[("A-LMO", "meat-core")] == "not emitted on this route"
    assert "A-AUTH" not in {entry.short_id for entry in found.entries}
    assert found.discrepancies == ()


def test_a_module_with_roots_and_no_rows_counts_as_ran() -> None:
    found = reconcile(WITH_RECEIVER, [])
    assert {item.module for item in found.not_engaged} == {"meat-core", "receiver"}
    assert found.discrepancies == ()


def test_a_closure_member_no_ran_module_can_emit_is_a_discrepancy() -> None:
    """``in_closure_no_emitter``: a premise the run rests on that nothing emitted."""
    roots = {**MAIN, "elsewhere": ["elsewhere/thm:orphan"]}
    found = reconcile(roots, [row("sequential_round_model")])
    assert "A-ORPHAN" in found.kinds(DiscrepancyKind.IN_CLOSURE_NO_EMITTER)
    (item,) = [d for d in found.discrepancies if d.short_id == "A-ORPHAN"]
    assert "elsewhere/thm:orphan" in item.detail
    assert item.emitted_by == ()
    assert "A-ORPHAN" not in {entry.short_id for entry in found.not_engaged}


def test_an_unknown_machine_key_is_fatal() -> None:
    with pytest.raises(ClaimClosureError, match="no_such_key"):
        reconcile(MAIN, [row("no_such_key")])


def test_a_short_id_the_table_gives_another_key_is_fatal() -> None:
    with pytest.raises(ClaimClosureError, match="A-TSM"):
        reconcile(MAIN, [row("sequential_round_model", "reductions", short_id="A-TSM")])


def test_a_root_the_table_lacks_is_fatal() -> None:
    with pytest.raises(ClaimClosureError, match="thm:absent"):
        reconcile({"meat-core": ["meat-core/thm:absent"]}, [])


def test_a_table_whose_key_names_two_assumptions_is_refused() -> None:
    table = json.loads(json.dumps(TABLE))
    table["assumptions"]["A-TSM"]["machine_key"] = "sequential_round_model"
    with pytest.raises(ClaimClosureError, match="two assumptions"):
        route_exact_assumptions(MAIN, [], vocabularies=VOCABULARIES, table=table)


def test_one_entry_per_id_with_every_emitter_listed() -> None:
    """The A-SEQ case: transmitter, reductions and meat-core emit one key."""
    rows = [
        row("sequential_round_model", "transmitter"),
        row("sequential_round_model", "reductions", station=0, short_id="A-SEQ"),
        row("sequential_round_model", "meat-core"),
    ]
    found = reconcile(MAIN, rows)
    (entry,) = [entry for entry in found.entries if entry.short_id == "A-SEQ"]
    assert [emitter[:2] for emitter in entry.emitted_by] == [
        ("transmitter", None),
        ("reductions", 0),
        ("meat-core", None),
    ]
    assert [entry.short_id for entry in found.entries].count("A-SEQ") == 1


def test_each_id_sits_in_exactly_one_section() -> None:
    """Numerical trust to numerics, the rest premises (two sections since 0.20.0)."""
    rows = [
        row("sequential_round_model"),
        row("classical_channel_authenticated"),
        row("exact_linear_oracle"),
        row(
            "exact_window_eigenvalue_slack",
            "receiver",
            bindings=(("invoked_at", ["t"]),),
        ),
    ]
    found = reconcile(WITH_RECEIVER, rows)
    assert found.section(Section.ASSUMPTIONS) == ("A-AUTH", "A-SEQ")
    assert found.section(Section.NUMERICS) == ("A-EIG", "A-LMO")
    listed = [entry.short_id for entry in found.entries]
    assert len(listed) == len(set(listed))


def test_a_row_emitted_not_engaged_is_not_engaged_and_never_listed() -> None:
    """A-EIG with an empty ``invoked_at``: the emitter's condition is the reason."""
    rows = [
        row("sequential_round_model"),
        row(
            "exact_window_eigenvalue_slack",
            "receiver",
            engaged=False,
            condition="invoked exactly where a depth is declared",
        ),
    ]
    found = reconcile(WITH_RECEIVER, rows)
    assert "A-EIG" not in {entry.short_id for entry in found.entries}
    (item,) = [item for item in found.not_engaged if item.short_id == "A-EIG"]
    assert (item.module, item.reason) == (
        "receiver",
        "invoked exactly where a depth is declared",
    )
    assert found.discrepancies == ()


def test_one_engaged_station_engages_the_id() -> None:
    rows = [
        row("exact_window_eigenvalue_slack", "receiver", station=0, engaged=False),
        row("exact_window_eigenvalue_slack", "receiver", station=1),
    ]
    found = reconcile(WITH_RECEIVER, rows)
    (entry,) = [entry for entry in found.entries if entry.short_id == "A-EIG"]
    assert [emitter[:2] for emitter in entry.emitted_by] == [("receiver", 1)]
    assert "A-EIG" not in {item.short_id for item in found.not_engaged}


BAND = {"protocol-compiler": ["protocol-compiler/thm:band"]}
DISCHARGES = {"protocol-compiler/thm:band": ("A-LINK",)}


def test_a_row_emitted_where_a_root_discharges_it_is_a_discrepancy() -> None:
    """A row emitted where a root discharges it is a discrepancy."""
    found = reconcile(
        BAND, [row("reduction_chain_sound", "protocol-compiler")], discharges=DISCHARGES
    )
    assert found.kinds(DiscrepancyKind.EMITTED_WHERE_DISCHARGED) == ("A-LINK",)
    assert "A-LINK" in found.section(Section.ASSUMPTIONS)


def test_a_discharged_row_not_emitted_is_not_engaged_with_its_theorem() -> None:
    """What the report moves to ``discharged_on_route``."""
    found = reconcile(BAND, [], discharges=DISCHARGES)
    (item,) = found.not_engaged
    assert item.discharged_by == "protocol-compiler/thm:band"
    assert item.reason == "discharged on this route by protocol-compiler/thm:band"
    assert item.as_payload()["discharged_by"] == "protocol-compiler/thm:band"
    assert found.discrepancies == ()


def test_a_discharge_applies_only_where_its_root_is_a_root_of_the_run() -> None:
    roots = {"protocol-compiler": ["meat-core/thm:main"]}
    found = reconcile(roots, [row("reduction_chain_sound", "protocol-compiler")],
                      discharges=DISCHARGES)
    assert found.kinds(DiscrepancyKind.EMITTED_WHERE_DISCHARGED) == ()


SOURCE = {"transmitter": ["transmitter/thm:source"]}


def test_an_engaged_covering_refinement_covers_its_parent() -> None:
    """A-WCP emitted, A-ENS in the closure and emitted by none.

    A-WCP restates A-ENS's clauses for the source model's states, so the
    run's A-ENS is A-WCP's: the parent is neither listed as not engaged nor a
    discrepancy, and A-WCP is listed as the premise.
    """
    rows = [
        row("wcp_source_model", "transmitter"),
        row("specification_describes_apparatus", "transmitter"),
    ]
    found = reconcile(SOURCE, rows)
    assert "A-WCP" in found.section(Section.ASSUMPTIONS)
    assert "A-ENS" not in {item.short_id for item in found.not_engaged}
    assert "A-ENS" not in {entry.short_id for entry in found.entries}
    # A-WCP itself is outside this hand-written closure, the safe direction.
    assert found.kinds(DiscrepancyKind.EMITTED_NOT_IN_CLOSURE) == ("A-WCP",)
    assert found.kinds(DiscrepancyKind.IN_CLOSURE_NO_EMITTER) == ()


def test_without_the_refinement_the_parent_is_not_engaged() -> None:
    """The cover needs the engaged refinement; the parent alone is listed."""
    found = reconcile(SOURCE, [row("specification_describes_apparatus", "transmitter")])
    assert ("A-ENS", "transmitter") in {
        (item.short_id, item.module) for item in found.not_engaged
    }


def test_a_refinement_outside_the_covering_set_covers_nothing() -> None:
    """``refines`` alone is narrowing: A-ALICE-MEAS does not stand for A-SPEC."""
    rows = [
        row("alice_measurement_as_declared", "transmitter"),
        row("source_ensemble", "transmitter"),
    ]
    found = reconcile(SOURCE, rows)
    assert ("A-SPEC", "transmitter") in {
        (item.short_id, item.module) for item in found.not_engaged
    }
    # And the covering set is a parameter: emptied, A-WCP covers nothing.
    rows = [
        row("wcp_source_model", "transmitter"),
        row("specification_describes_apparatus", "transmitter"),
    ]
    found = reconcile(SOURCE, rows, covering=frozenset())
    assert "A-ENS" in {item.short_id for item in found.not_engaged}


def test_on_the_decoy_route_a_wcp_covers_a_ens() -> None:
    """The real decoy route: the transmitter emits A-WCP and not A-ENS."""
    from certiqs_key.runs.assumptions import COVERING_REFINEMENTS

    assert frozenset({"A-WCP"}) == COVERING_REFINEMENTS
    result = route_result("decoy")
    rows = emitted_rows(result)
    assert any(r.machine_key == "wcp_source_model" for r in rows)
    assert not any(r.machine_key == "source_ensemble" for r in rows)
    found = route_exact_assumptions(run_claim_roots(result), rows)
    assert "A-WCP" in {entry.short_id for entry in found.entries}
    assert "A-ENS" not in {item.short_id for item in found.not_engaged}
    assert "A-ENS" not in {item.short_id for item in found.discrepancies}


def test_identical_bindings_collapse_and_different_ones_stay_apart() -> None:
    rows = [
        row("sequential_round_model", "transmitter", bindings=(("rounds", 10),)),
        row("sequential_round_model", "reductions", station=0,
            bindings=(("rounds", 10), ("order", "msg-last"))),
        row("sequential_round_model", "meat-core", bindings=(("rounds", 11),)),
    ]
    found = reconcile(MAIN, rows)
    (entry,) = [entry for entry in found.entries if entry.short_id == "A-SEQ"]
    assert [(name, value, emitters) for name, value, emitters in entry.bindings] == [
        ("rounds", 10, (("transmitter", None, None), ("reductions", 0, None))),
        ("order", "msg-last", (("reductions", 0, None),)),
        ("rounds", 11, (("meat-core", None, None),)),
    ]


def test_the_payload_is_json_with_the_snapshot_and_no_emission_rules() -> None:
    """Design section 2.4: the entry carries the table's text; values are JSON."""
    law = (("ok", Fraction(1, 3)), ("err", Fraction(2, 3)))
    rows = [
        row("sequential_round_model", "transmitter",
            bindings=(("honest_distribution", law), ("alphabet", ("ok", "err")))),
    ]
    payload = reconcile(MAIN, rows).as_payload()
    text = json.dumps(payload)
    assert json.loads(text) == payload
    (entry,) = payload["assumptions"]
    assert entry["short_id"] == "A-SEQ"
    assert entry["section"] == "assumptions"
    assert entry["owner"] == "transmitter/ass:seq"
    assert entry["user_statement"] == "statement of transmitter/ass:seq"
    assert "emission" not in entry
    bindings = {binding["name"]: binding["value"] for binding in entry["bindings"]}
    assert bindings == {
        "honest_distribution": {"ok": "1/3", "err": "2/3"},
        "alphabet": ["ok", "err"],
    }
    assert entry["emitted_by"] == [
        {"module": "transmitter", "station": None, "party": None,
         "machine_key": "sequential_round_model", "inherited_from": None}
    ]
    assert set(payload) == {
        "roots", "claim_closure", "assumptions", "not_engaged", "discrepancies"
    }
    assert payload["roots"] == {"meat-core": ["meat-core/thm:main"]}
    assert set(payload["claim_closure"]) == {"meat-core/thm:main"}


def test_the_snapshot_is_a_copy_of_the_table() -> None:
    found = reconcile(MAIN, [row("sequential_round_model")])
    payload = found.as_payload()
    payload["assumptions"][0]["title"] = "changed"
    payload["claim_closure"]["meat-core/thm:main"]["assumptions"].clear()
    assert TABLE["assumptions"]["A-SEQ"]["title"] == "title of transmitter/ass:seq"
    assert TABLE["roots"]["meat-core/thm:main"]["assumptions"]


# ===========================================================================
#  The adapter, on the real emitters
# ===========================================================================


def _entries(route: str, outcome: str = "key-length") -> dict[str, Any]:
    result = route_result(route, outcome)
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    return {entry.short_id: entry for entry in found.entries}


def test_the_transmitter_rows_are_the_transmitter_s_and_not_the_compiler_s() -> None:
    """The compiler copies the transmitter artefact's ledger; the row is its.

    Design section 3.2: the transmitter's rows are "carried through the
    compiler's copy of the transmitter keys".
    """
    result = route_result("wpfss-encoded")
    rows = emitted_rows(result)
    transmitter = [r.machine_key for r in rows if r.emitted_by == "transmitter"]
    compiler = [r.machine_key for r in rows if r.emitted_by == "protocol-compiler"]
    assert tuple(transmitter) == tuple(
        result.specification.source.artifact.assumption_ledger
    )
    assert not set(transmitter) & set(compiler)
    assert set(transmitter) | set(compiler) == set(result.compilation.assumption_ledger)


def test_a_eig_without_an_exact_window_is_emitted_and_not_engaged() -> None:
    result = route_result("wpfss-no-window")
    (eig,) = [r for r in emitted_rows(result) if r.short_id == "A-EIG"]
    assert eig.engaged is False
    assert eig.condition is not None and "exact_window" in eig.condition
    assert "A-EIG" not in _entries("wpfss-no-window")
    # With the window declared, every setting's weight is the enclosed one
    # (receiver/req:rigorous-weight), which does not invoke A-EIG
    # (receiver/req:eig-ledger-row): emitted, not engaged, on this route too.
    (rigorous,) = [r for r in emitted_rows(route_result("wpfss-encoded"))
                   if r.short_id == "A-EIG"]
    assert rigorous.engaged is False
    assert "A-EIG" not in _entries("wpfss-encoded")


@pytest.mark.parametrize("route", ROUTES)
def test_a_eve_dim_is_on_no_route(route: str) -> None:
    """meat-core/ass:eve-dim is superseded: no emitter emits it, no closure holds it.

    The round model keeps the adversary's registers finite-dimensional by
    definition, and cor:composed-security, through lem:memory-lift, carries
    the security statement to registers of any dimension (the meat-core
    interface's ``a_eve_dim_note``).
    """
    result = route_result(route)
    rows = emitted_rows(result)
    assert all(row.machine_key != "adversary_registers_finite" for row in rows)
    found = route_exact_assumptions(run_claim_roots(result), rows)
    assert "A-EVE-DIM" not in {entry.short_id for entry in found.entries}
    assert "A-EVE-DIM" not in {item.short_id for item in found.not_engaged}
    for entry in found.claim_closure.values():
        assert "A-EVE-DIM" not in entry["assumptions"]


#: The compiler's premises thm:keylength assumes (the meat-core interface's
#: ``a_link_note`` and ``a_spec_note``), reached by the key-length roots.
KEY_LENGTH_COMPILER_PREMISES = ("A-LINK", "A-SPEC", "A-ALICE-MEAS")


@pytest.mark.parametrize("route", ROUTES)
def test_the_compiler_s_key_length_premises_are_listed_as_its_ledger_has_them(
    route: str,
) -> None:
    """A-LINK, A-SPEC and A-ALICE-MEAS: engaged where the compiler emits them.

    thm:keylength assumes them, so meat-core's key-length roots reach them;
    the compiler's ledger carries A-SPEC on every run, A-ALICE-MEAS under its
    presence rule, and A-LINK except where thm:band-a (v) or
    req:link-row-provenance proves its clauses, where the run lists it as not
    engaged and discharged by that root. Each is listed once, engaged or not.
    """
    result = route_result(route, "key-length")
    roots = run_claim_roots(result)
    found = route_exact_assumptions(roots, emitted_rows(result))
    keylength = found.claim_closure["meat-core/cor:keylength-bound"]
    assert set(KEY_LENGTH_COMPILER_PREMISES) <= set(keylength["assumptions"])
    engaged = {entry.short_id: entry for entry in found.entries}
    unengaged = {item.short_id: item for item in found.not_engaged}
    compiled = set(result.compilation.assumption_ledger)
    keys = {str(member): key for member, key in COMPILER_KEYS.items()}
    for short_id in KEY_LENGTH_COMPILER_PREMISES:
        assert (short_id in engaged) != (short_id in unengaged), short_id
        assert (short_id in engaged) == (keys[short_id] in compiled), short_id
        if short_id in engaged:
            assert [emitter[0] for emitter in engaged[short_id].emitted_by] == [
                "protocol-compiler"
            ]
    # A-SPEC is on every run.
    assert "A-SPEC" in engaged
    # A-LINK, per route, as the compiler's emission rule decides it.
    expected = EXPECTED_A_LINK[route]
    if expected == "engaged":
        assert "A-LINK" in engaged
    else:
        assert unengaged["A-LINK"].discharged_by == expected
    # A-ALICE-MEAS: no fixture route has an untrusted source or d_A = 1 with
    # at least two letters (bbm92 is untrusted at one letter, every other
    # route trusted at d_A >= 2), so it is not engaged on any, and nothing
    # discharges it: its presence rule is not met.
    assert unengaged["A-ALICE-MEAS"].discharged_by is None


#: A-LINK on each fixture route, from the protocol-compiler interface's
#: emission rule for it (req:link-row-provenance): omitted, and discharged by
#: thm:band-a (v), on Band A; omitted, and discharged by
#: req:link-row-provenance (ii), where the source segment is empty and every
#: measured factor's receiver segment is the single exact in-run instance link
#: of the FLAT instance (the one rem:obligations-discharged names the
#: compression claim for); emitted, hence engaged, everywhere else. DECOY: its
#: source segment carries the tagging link, so (ii) fails at its first
#: condition. A BRANCHING ROUTE: a single exact receiver link with no channel
#: as data, but of a branching artefact, for which rem:obligations-discharged
#: names no compression claim, so the run passes no chain_provenance and the
#: row stays.
EXPECTED_A_LINK: dict[str, str] = {
    "band-a": "protocol-compiler/thm:band-a",
    "wpfss-encoded": "protocol-compiler/req:link-row-provenance",
    "wpfss-licensed": "protocol-compiler/req:link-row-provenance",
    "wpfss-no-window": "protocol-compiler/req:link-row-provenance",
    "untrusted-two-station": "protocol-compiler/req:link-row-provenance",
    "decoy": "engaged",
}


def test_the_a_link_pins_cover_every_route_and_follow_the_chain() -> None:
    """EXPECTED_A_LINK names every route, and its reasons hold of the chains."""
    assert set(ROUTES) <= set(EXPECTED_A_LINK)
    decoy = route_result("decoy").specification.chain
    assert decoy.source_segment
    for route in ROUTES:
        if route in ("band-a", "decoy"):
            continue
        result = route_result(route)
        assert not result.specification.chain.source_segment, route
        # The run tier attested the in-run flat link exactly where the pin
        # says req:link-row-provenance discharges the row.
        assert result.compilation.link_row_omitted_on_provenance is (
            EXPECTED_A_LINK[route] == "protocol-compiler/req:link-row-provenance"
        ), route


def test_an_emitted_a_alice_meas_row_is_engaged_and_the_compiler_s() -> None:
    """The engaged path of A-ALICE-MEAS, a premise thm:keylength assumes.

    No fixture route meets its presence rule (untrusted source or d_A = 1,
    with at least two letters), and a route that does would need new
    instance data; so the untrusted two-station route's rows are taken with
    the row the compiler emits where the rule is met inserted where the
    compiler puts it, right after A-SPEC, binding ``alice_povm`` and
    ``source_mode`` (its ``binds``). The rule's own branch in the compiler is
    held by tests/unit/test_protocol_emission.py; this holds the route-exact
    set: the row is engaged, emitted by the compiler alone, reached by the
    key-length roots, and no longer listed as not engaged.
    """
    result = route_result("untrusted-two-station", "key-length")
    rows = list(emitted_rows(result))
    keys = {str(member): key for member, key in COMPILER_KEYS.items()}
    (spec_at,) = [
        index for index, item in enumerate(rows)
        if item.emitted_by == "protocol-compiler"
        and item.machine_key == keys["A-SPEC"]
    ]
    rows.insert(spec_at + 1, row(
        keys["A-ALICE-MEAS"],
        "protocol-compiler",
        bindings=(
            ("alice_povm", (("letters", ("x0", "x1")),)),
            ("source_mode", "untrusted"),
        ),
    ))
    found = route_exact_assumptions(run_claim_roots(result), rows)
    engaged = {entry.short_id: entry for entry in found.entries}
    assert "A-ALICE-MEAS" in engaged
    assert [emitter[0] for emitter in engaged["A-ALICE-MEAS"].emitted_by] == [
        "protocol-compiler"
    ]
    assert "A-ALICE-MEAS" not in {item.short_id for item in found.not_engaged}
    assert "A-ALICE-MEAS" in found.claim_closure["meat-core/thm:keylength"][
        "assumptions"
    ]
    assert found.discrepancies == ()


def test_a_recv_is_one_entry_naming_the_supplier_version() -> None:
    """Where a reductions artefact emits A-RECV, it names the supplier version.

    The route fixtures build their receiver artefacts in the run, exact and
    rigorous, so each omits its row (req:recv-row-provenance); this reads the
    same run with that omission undone, as an artefact handed in from outside
    the run would carry it. The compiler emits no A-RECV row on any route, so
    reductions is the one emitter.
    """
    result = route_result("wpfss-encoded")
    rows = list(emitted_rows(result))
    assert "A-RECV" not in {row.short_id for row in rows}
    version = result.reduction_artifact.receiver_row_omitted_on_provenance[0]
    rows.append(row(
        "receiver_artifact_accepted", "reductions", inherited_from=version
    ))
    roots = run_claim_roots(result)
    roots["reductions"] = tuple(
        root for root in roots["reductions"]
        if root != "reductions/req:recv-row-provenance"
    )
    found = route_exact_assumptions(roots, rows)
    entry = {entry.short_id: entry for entry in found.entries}["A-RECV"]
    modules = {emitter[0]: emitter for emitter in entry.emitted_by}
    assert set(modules) == {"reductions"}
    assert str(modules["reductions"][4]).startswith("receiver@")
    assert [d for d in found.discrepancies if d.short_id == "A-RECV"] == []


def test_per_station_rows_carry_their_station() -> None:
    entry = _entries("untrusted-two-station")["A-SEQ"]
    assert [emitter[:2] for emitter in entry.emitted_by] == [
        ("transmitter", None),
        ("reductions", 0),
        ("reductions", 1),
        ("meat-core", None),
    ]
    stations = {
        r.station for r in emitted_rows(route_result("untrusted-two-station"))
        if r.emitted_by == "receiver"
    }
    assert stations == {0, 1}


def test_the_statistics_bindings_reach_the_payload_as_objects() -> None:
    result = route_result("band-a")
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    payload = found.as_payload()
    json.dumps(payload)
    (entry,) = [e for e in payload["assumptions"] if e["short_id"] == "A-HON-ENV"]
    bindings = {binding["name"]: binding["value"] for binding in entry["bindings"]}
    assert set(bindings) == {"honest_model", "honest_distribution", "rounds"}
    assert isinstance(bindings["honest_distribution"], dict)
    law = bindings["honest_distribution"]
    assert all(isinstance(value, str) for value in law.values())


def test_a_eig_is_a_trusted_numeric_and_never_a_premise() -> None:
    """Where invoked (a floating-point window), A-EIG is listed among the numerics."""
    rows = [*emitted_rows(route_result("wpfss-encoded"))]
    engaged = [replace(r, engaged=True, condition=None) if r.short_id == "A-EIG"
               else r for r in rows]
    found = route_exact_assumptions(run_claim_roots(route_result("wpfss-encoded")),
                                    engaged)
    sections = {entry.short_id: entry.section for entry in found.entries}
    assert sections["A-EIG"] is Section.NUMERICS


# ===========================================================================
#  The declared vocabularies and discharges, against the shipped table
# ===========================================================================


def test_every_vocabulary_names_assumptions_the_table_carries() -> None:
    from certiqs_key.domain.claim_closure import closure_table
    from certiqs_key.runs.assumptions import LEDGER_VOCABULARIES, MODULE_ORDER

    carried = set(closure_table()["assumptions"])
    assert set(LEDGER_VOCABULARIES) == set(MODULE_ORDER)
    for module, vocabulary in LEDGER_VOCABULARIES.items():
        assert vocabulary <= carried, (module, sorted(vocabulary - carried))


def test_every_discharge_names_a_carried_root_and_an_id_some_ledger_emits() -> None:
    from certiqs_key.domain.claim_closure import closure_table
    from certiqs_key.runs.assumptions import DISCHARGED_ON_ROUTE, LEDGER_VOCABULARIES

    roots = closure_table()["roots"]
    emitted = set().union(*LEDGER_VOCABULARIES.values())
    for root, short_ids in DISCHARGED_ON_ROUTE.items():
        assert root in roots
        assert set(short_ids) <= emitted


def test_band_a_discharges_a_link() -> None:
    """Band A rests on no A-LINK: thm:band-a (v) discharges it.

    Part (v) of that theorem proves every clause of A-LINK of the identity
    link, so the compiler omits the row on Band A and
    ``DISCHARGED_ON_ROUTE`` names the theorem. A-LINK still reaches the
    closure through thm:choice-encoding where a public choice is declared, as
    on this route, and is listed as not engaged with ``discharged_by``.
    """
    from certiqs_key.runs.assumptions import DISCHARGED_ON_ROUTE

    assert "A-LINK" in DISCHARGED_ON_ROUTE["protocol-compiler/thm:band-a"]
    result = route_result("band-a")
    rows = emitted_rows(result)
    assert not any(r.machine_key == "reduction_chain_sound" for r in rows)
    found = route_exact_assumptions(run_claim_roots(result), rows)
    assert "A-LINK" not in {entry.short_id for entry in found.entries}
    assert found.kinds(DiscrepancyKind.EMITTED_WHERE_DISCHARGED) == ()
    (item,) = [item for item in found.not_engaged if item.short_id == "A-LINK"]
    assert item.discharged_by == "protocol-compiler/thm:band-a"


def test_a_present_is_retired_and_band_a_discharges_only_a_link() -> None:
    """A-PRESENT is no premise on any route.

    The exact admissibility of the physical receiver family as presented is
    clause (iv) of def:well-formed-spec, which the compiler decides on every route
    (req:physical-family-decision), so no ledger emits its key, the closure
    table carries no such assumption, and ``DISCHARGED_ON_ROUTE`` names
    A-LINK alone.
    """
    from certiqs_key.domain.claim_closure import closure_table
    from certiqs_key.runs.assumptions import DISCHARGED_ON_ROUTE

    assert DISCHARGED_ON_ROUTE == {
        "protocol-compiler/thm:band-a": ("A-LINK",),
        "protocol-compiler/req:link-row-provenance": ("A-LINK",),
        "reductions/req:recv-row-provenance": ("A-RECV",),
    }
    assert "A-PRESENT" not in closure_table()["assumptions"]
    for route in ("band-a", "wpfss-encoded"):
        result = route_result(route)
        rows = emitted_rows(result)
        assert not any(r.machine_key == "presented_receiver_family" for r in rows)
        found = route_exact_assumptions(run_claim_roots(result), rows)
        assert "A-PRESENT" not in {entry.short_id for entry in found.entries}
        assert "A-PRESENT" not in {item.short_id for item in found.not_engaged}


# ===========================================================================
#  The engine's wire IDs, read back into the declared spelling
# ===========================================================================


def test_an_engine_letter_the_run_s_bijection_does_not_reach_is_refused() -> None:
    """Fail-closed: a binding the run cannot read back is not recorded.

    The join maps the engine's ``alice_povm`` and ``acceptance_set``
    alphabets through the inverse of the run's ``WireLabels``; a letter
    outside it would be recorded under a declared name in a spelling no
    declaration has.
    """
    from types import SimpleNamespace

    from certiqs_key.runs.errors import RunError

    result = route_result("band-a")
    key, bindings = next(
        (key, bindings)
        for key, bindings in result.key_rate.assumption_bindings
        if "alice_povm" in dict(bindings)
    )
    forged = tuple(
        (name, (("form", "povm"), ("alphabet", ("_nowhere_",)), ("dimension", 2)))
        if name == "alice_povm" else (name, value)
        for name, value in bindings
    )
    stand_in = SimpleNamespace(**vars(result))
    stand_in.key_rate = SimpleNamespace(
        **{
            **vars(result.key_rate),
            "assumption_bindings": tuple(
                (k, forged if k == key else b)
                for k, b in result.key_rate.assumption_bindings
            ),
        }
    )
    with pytest.raises(RunError, match="_nowhere_"):
        emitted_rows(stand_in)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("alice_povm", "povm over _Z_0_"),
        ("alice_povm", ("_Z_0_", "_Z_1_")),
        ("alice_povm", (("form", "povm"), ("alphabet", ["_Z_0_", "_Z_1_"]))),
        ("alice_povm", (("form", "povm"), ("dimension", 2))),
        ("alice_povm", (("alphabet", ("_Z_0_",)), ("alphabet", ("_Z_1_",)))),
        ("acceptance_set", ["gen", "err"]),
        ("acceptance_set", (("alphabet", "gen"),)),
    ],
    ids=[
        "a string", "a bare tuple of letters", "a list alphabet", "no alphabet",
        "two alphabets", "a list", "a string alphabet",
    ],
)
def test_a_label_bearing_binding_of_another_shape_is_refused(
    name: str, value: object
) -> None:
    """Fail-closed on the shape: a value the read-back cannot read.

    A value that is not a tuple, or an ``alphabet`` that is not a tuple, must
    not pass through unmapped, or the record could carry wire IDs under a
    declared name.
    """
    from types import SimpleNamespace

    from certiqs_key.runs.errors import RunError

    result = route_result("band-a")
    key, bindings = next(
        (key, bindings)
        for key, bindings in result.key_rate.assumption_bindings
        if name in dict(bindings)
    )
    forged = tuple(
        (bound, value if bound == name else held) for bound, held in bindings
    )
    stand_in = SimpleNamespace(**vars(result))
    stand_in.key_rate = SimpleNamespace(
        **{
            **vars(result.key_rate),
            "assumption_bindings": tuple(
                (k, forged if k == key else b)
                for k, b in result.key_rate.assumption_bindings
            ),
        }
    )
    with pytest.raises(RunError, match=name):
        emitted_rows(stand_in)  # type: ignore[arg-type]


def test_the_engine_binds_wire_ids_and_the_join_records_the_declared_ones() -> None:
    """The bb84 labels are renamed on the wire; the set holds the declared ones."""
    result = route_result("band-a")
    raw = {
        name: value
        for _, bindings in result.key_rate.assumption_bindings
        for name, value in bindings
    }
    assert dict(raw["alice_povm"])["alphabet"] == ("_Z_0_", "_Z_1_", "_X_0_", "_X_1_")
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    (src,) = [entry for entry in found.entries if entry.short_id == "A-SRC"]
    povm = [value for name, value, _ in src.bindings if name == "alice_povm"]
    assert len(povm) == 1
    assert dict(povm[0])["alphabet"] == ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")  # type: ignore[call-overload]
    emitters = {module for name, _, items in src.bindings if name == "alice_povm"
                for module, *_ in items}
    assert {"transmitter", "meat-core"} <= emitters
