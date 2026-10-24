"""The key-rate report's check table and how a refusal reads in it.

Every claim the report cites is in the shipped closure table; a refused record
marks the refusing check
``refused`` and every later one ``not-reached``; no refusal code is named that
no module defines.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from tests.support.report_records import (
    completed_record,
    estimate_record,
    refused_record,
    synthetic_table,
)

from certiqs_key.domain.claim_closure import (
    COMPOSITION_ROOTS,
    CORRECTNESS_ROOTS,
    SECRECY_ROOTS,
    claim_info,
    limitations,
)
from certiqs_key.meat_core.reasons import RefusalReason as MeatRefusal
from certiqs_key.protocol_compiler.reasons import RefusalReason as CompilerRefusal
from certiqs_key.receiver.reasons import RefusalReason as ReceiverRefusal
from certiqs_key.runs.report import build_report
from certiqs_key.runs.report.build import COMPLETENESS_CLAIM, PER_EXECUTION_CLAIMS
from certiqs_key.runs.report.checks import CHECK_CLAIMS, CHECKS, stage_index
from certiqs_key.runs.report.model import Check
from certiqs_key.statistics.reasons import InfeasibilityReason


def checks(record: dict[str, Any]) -> dict[str, Check]:
    built = build_report(record, table=synthetic_table())
    return {check["id"]: check for check in built["sections"]["checks"]["checks"]}


def outcomes(record: dict[str, Any]) -> list[tuple[str, str]]:
    return [(check_id, check["outcome"]) for check_id, check in checks(record).items()]


@pytest.mark.parametrize(
    "claim_id",
    sorted({
        *CHECK_CLAIMS, *PER_EXECUTION_CLAIMS, COMPLETENESS_CLAIM,
        *COMPOSITION_ROOTS, *SECRECY_ROOTS, *CORRECTNESS_ROOTS,
    }),
)
def test_every_claim_the_report_cites_is_in_the_shipped_table(claim_id: str) -> None:
    info = claim_info(claim_id)
    assert info["contract"]["anchor"] == f"claim-{claim_id}"


def test_the_shipped_table_names_limitations() -> None:
    assert "meat-core/rem:repeated-executions" in limitations()


def test_check_ids_are_stable_kebab_case_and_unique() -> None:
    ids = [spec.id for spec in CHECKS]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", check_id) for check_id in ids)


def test_the_table_is_in_stage_order() -> None:
    positions = [stage_index(spec.stage) for spec in CHECKS]
    assert positions == sorted(positions)


def test_every_refusal_code_is_one_a_module_defines() -> None:
    defined = {
        str(member)
        for enum in (MeatRefusal, CompilerRefusal, ReceiverRefusal,
                     InfeasibilityReason)
        for member in enum
    }
    for spec in CHECKS:
        assert spec.reasons <= defined, spec.id


def test_a_completed_record_s_checks() -> None:
    found = checks(completed_record())
    assert found["receiver-route"]["outcome"] == "passed"
    assert found["element-graph-acyclic"]["outcome"] == "not-applicable"
    assert found["probe-states-diagonal"]["outcome"] == "not-applicable"
    assert found["key-length-gate"]["outcome"] == "passed"
    assert found["key-length-gate"]["value"] is True
    assert found["first-order-hypotheses"]["value"] == {"contributing": 1,
                                                        "withdrawn": 1}
    assert found["reported-key-length"]["value"] == 12_345
    assert found["security-statement-not-vacuous"]["value"] == {
        "eps_pa": 2.0**-30, "eps_ev": 2.0**-30, "eps_auth": 0.0,
    }
    assert found["alpha-range"]["value"] == 1.5
    assert [claim["id"] for claim in found["alpha-range"]["claims"]] == [
        "meat-core/req:key-length-alpha-domain",
    ]
    assert found["snaps-within-tolerance"]["outcome"] == "passed"
    assert found["exact-statistics-inputs"]["value"] == "PolytopeGeometry"
    assert found["receiver-route"]["claims"][0]["id"] == "receiver/def:compile"


def test_an_element_graph_route_takes_the_graph_check() -> None:
    def edit(record: dict[str, Any]) -> None:
        receiver = record["payload"]["stages"]["receiver_construction"]
        receiver["receiver_route"] = "element-graph"
        receiver["modes"] = [{"label": "p", "role": "probe"}]

    found = checks(completed_record(edit=edit))
    assert found["element-graph-acyclic"]["outcome"] == "passed"
    assert found["probe-states-diagonal"]["outcome"] == "passed"


def test_a_closed_gate_and_no_contributing_iterate_read_failed() -> None:
    def edit(record: dict[str, Any]) -> None:
        record["payload"]["stages"]["key_rate"]["security_gates"][
            "key_length_permitted"
        ] = False

    assert checks(completed_record(edit=edit))["key-length-gate"]["outcome"] == "failed"
    found = checks(estimate_record())
    assert found["first-order-hypotheses"]["outcome"] == "failed"
    assert found["reported-key-length"]["outcome"] == "not-applicable"


def test_the_refusing_check_is_refused_and_every_later_one_not_reached() -> None:
    found = outcomes(refused_record(eps_pa=0.5, eps_ev=0.5))
    names = [check_id for check_id, _ in found]
    refusing = names.index("security-statement-not-vacuous")
    assert found[refusing][1] == "refused"
    assert all(outcome == "not-reached" for _, outcome in found[refusing + 1:])
    # Before the refusal: passed, or not-applicable where the check's own
    # evaluation on the record says so. A refused record carries no snaps
    # block, no element graph and no probe.
    assert dict(found[:refusing]) == {
        "snaps-within-tolerance": "not-applicable",
        "receiver-route": "passed",
        "element-graph-acyclic": "not-applicable",
        "probe-states-diagonal": "not-applicable",
        "specification-well-formed": "passed",
        "compiler-gates": "passed",
        "exact-statistics-inputs": "passed",
        "matched-alphabet": "passed",
        "declaration-admitted": "passed",
        "alpha-range": "passed",
    }
    refused = checks(refused_record())["security-statement-not-vacuous"]
    assert refused["value"] == {
        "stage": "solve", "reason": "security_statement_vacuous",
    }
    assert refused["pointer"] == "/payload/stages/solve"


def test_a_refusal_no_check_answers_for_is_placed_by_stage() -> None:
    found = dict(outcomes(refused_record(stage="compilation",
                                         reason="sector_map_mismatch")))
    # No receiver stage on the record and refused at compilation, which fixes
    # the Band-A route: no route was reached (B1 of the toy-protocol check).
    assert found["receiver-route"] == "not-reached"
    assert found["specification-well-formed"] == "not-reached"
    assert found["compiler-gates"] == "not-reached"
    assert found["reported-key-length"] == "not-reached"
    assert "refused" not in found.values()


def test_a_graph_refusal_is_the_graph_check_s() -> None:
    found = dict(outcomes(refused_record(stage="receiver_construction",
                                         reason="graph_condition_e2_failed")))
    assert found["receiver-route"] == "passed"
    assert found["element-graph-acyclic"] == "refused"
    assert found["probe-states-diagonal"] == "not-reached"


def test_a_band_a_refusal_keeps_the_probe_and_graph_checks_not_applicable() -> None:
    """A Band-A record (declared finite POVM, no probe) refused at compilation."""
    record = refused_record(stage="compilation", reason="gate_g1_failed")
    record["payload"]["stages"]["receiver_construction"] = {
        "route": "declared_finite_povm",
        "receiver_route": "declared-finite-povm",
        "modes": [],
    }
    found = dict(outcomes(record))
    assert found["receiver-route"] == "passed"
    assert found["element-graph-acyclic"] == "not-applicable"
    assert found["probe-states-diagonal"] == "not-applicable"
    assert found["specification-well-formed"] == "passed"
    assert found["compiler-gates"] == "refused"
    assert found["exact-statistics-inputs"] == "not-reached"


@pytest.mark.parametrize("stage", ["no_such_stage", ""])
def test_an_unknown_or_absent_refusing_stage_reaches_nothing(stage: str) -> None:
    record = refused_record(stage=stage or "solve", reason="not_a_known_code")
    if not stage:
        # The record says it refused but names no refusing stage.
        record["payload"]["stages"] = {}
    found = dict(outcomes(record))
    assert set(found.values()) == {"not-reached"}


def test_a_completed_record_without_snaps_reads_not_applicable() -> None:
    def edit(record: dict[str, Any]) -> None:
        del record["payload"]["snaps"]

    found = checks(completed_record(edit=edit))
    assert found["snaps-within-tolerance"]["outcome"] == "not-applicable"
