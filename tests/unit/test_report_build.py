"""The key-rate report of one run record, against hand-written expectations.

Correctness of the report is held by hand-written expectations on
hand-written records, not by the rendered snapshots. Every record here is
synthetic in the shape of the record (``tests/support/report_records.py`` says
which parts are assumed), and each expected value below is stated by hand.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest
from tests.support.report_records import (
    AUTH_STATEMENT,
    completed_record,
    estimate_record,
    refused_record,
    synthetic_table,
)

from certiqs_key.runs.report import (
    ReportInputError,
    build_report,
    select,
)
from certiqs_key.runs.report.build import (
    PER_EXECUTION_CLAIMS,
    SUPPORTED_RECORD_SCHEMA_VERSION,
)
from certiqs_key.runs.report.model import AssumptionEntry, KeyRateReport


def report(record: dict[str, Any]) -> KeyRateReport:
    return build_report(record, table=synthetic_table())


def r3_ids(built: KeyRateReport) -> list[str]:
    return [
        entry["short_id"]
        for group in built["sections"]["assumptions"]["groups"]
        for family in group["families"]
        for entry in (family["head"], *family["members"])
    ]


def r3_entry(built: KeyRateReport, short_id: str) -> AssumptionEntry:
    found = select(built, f"assumptions/{short_id}")
    assert isinstance(found, dict)
    return found  # type: ignore[return-value]


def test_a_auth_is_a_premise_with_eps_auth_and_k_auth_bound() -> None:
    built = report(completed_record())
    groups = {
        group["category"]: [family["head"]["short_id"] for family in group["families"]]
        for group in built["sections"]["assumptions"]["groups"]
    }
    assert "A-AUTH" in groups["channel-and-adversary"]
    auth = r3_entry(built, "A-AUTH")
    bindings = {binding["name"]: binding for binding in auth["bindings"]}
    assert bindings["eps_auth"]["value"] == 0.0
    assert bindings["eps_auth"]["pointer"] == "/payload/config/parameters/eps_auth"
    assert bindings["k_auth"]["value"] == 0
    assert bindings["k_auth"]["pointer"] == "/payload/config/parameters/k_auth"
    # A-AUTH's delta is described by its user_statement, carried verbatim.
    assert auth["user_statement"] == AUTH_STATEMENT
    assert "δ" in AUTH_STATEMENT


def test_a_lmo_and_a_eig_appear_only_under_trusted_engine_numerics() -> None:
    built = report(completed_record())
    numerics = [entry["short_id"] for entry in built["sections"]["numerics"]["entries"]]
    assert numerics == ["A-EIG", "A-LMO"]
    assert "A-LMO" not in r3_ids(built)
    assert "A-EIG" not in r3_ids(built)
    decided = [e["short_id"] for e in built["sections"]["checks"]["decided_rows"]]
    assert "A-LMO" not in decided and "A-EIG" not in decided


def test_a_numerical_trust_entry_is_moved_to_r4_even_without_its_id() -> None:
    def edit(record: dict[str, Any]) -> None:
        for entry in record["payload"]["assumption_manifest"]["assumptions"]:
            if entry["short_id"] == "A-TRUST":
                entry["category"] = "numerical-trust"
                entry["section"] = "assumptions"  # what a record says is overridden

    built = report(completed_record(edit=edit))
    numerics = built["sections"]["numerics"]["entries"]
    assert "A-TRUST" in [entry["short_id"] for entry in numerics]
    assert "A-TRUST" not in r3_ids(built)


def test_no_assumption_appears_in_two_sections() -> None:
    built = report(completed_record())
    sections = built["sections"]
    lists = [
        r3_ids(built),
        [entry["short_id"] for entry in sections["numerics"]["entries"]],
        [entry["short_id"] for entry in sections["checks"]["decided_rows"]],
    ]
    flat = [short_id for ids in lists for short_id in ids]
    assert len(flat) == len(set(flat))
    assert set(flat) == {
        "A-AUTH", "A-KEYREG", "A-CONFORM", "A-LMO", "A-EIG", "A-TRUST", "A-THRESH",
        "A-PORT", "A-SPEC", "A-ALICE-MEAS", "A-SEQ", "A-DECIDED",
    }


def test_a_decided_row_is_a_check_and_never_a_premise() -> None:
    built = report(completed_record())
    decided = [e["short_id"] for e in built["sections"]["checks"]["decided_rows"]]
    assert decided == ["A-DECIDED"]
    assert "A-DECIDED" not in r3_ids(built)


def test_the_three_zero_default_flags_are_raised_first_in_order() -> None:
    built = report(completed_record())
    flags = built["sections"]["result"]["not_counted"]
    assert [flag["id"] for flag in flags] == [
        "lambda_ec_zero", "eps_auth_zero", "k_auth_zero",
    ]
    assert [flag["parameter"] for flag in flags] == [
        "parameters.lambda_ec", "parameters.eps_auth", "parameters.k_auth",
    ]
    assert flags[0]["assumptions"] == ["A-KEYREG", "A-CONFORM"]
    assert flags[1]["assumptions"] == ["A-AUTH"]
    assert flags[2]["assumptions"] == ["A-AUTH"]
    assert list(built["sections"]["result"])[:2] == ["outcome", "refusal"]


def test_no_flag_for_a_declared_nonzero_value() -> None:
    built = report(completed_record(lambda_ec=1_000, eps_auth=1e-12, k_auth=256))
    assert built["sections"]["result"]["not_counted"] == []


def test_only_the_zero_parameter_is_flagged() -> None:
    built = report(completed_record(lambda_ec=1_000))
    flags = built["sections"]["result"]["not_counted"]
    assert [flag["id"] for flag in flags] == ["eps_auth_zero", "k_auth_zero"]


def test_numbers_are_read_from_the_record_never_recomputed() -> None:
    # Deliberately inconsistent numbers: the report must show the record's.
    record = completed_record(key_length=1_000, net_key_length=993,
                              security_parameter=0.125)
    result = report(record)["sections"]["result"]
    assert result["outcome"] == "key-length"
    assert result["key_length"] == 1_000
    assert result["net_key_length"] == 993
    assert result["security_parameter"]["value"] == 0.125
    assert result["security_parameter"]["terms"] == {
        "eps_pa": 2.0**-30, "eps_ev": 2.0**-30, "eps_auth": 0.0,
    }
    assert result["security_parameter"]["auth_factor"] == 2
    assert result["rounds"] == 1_000_000_000
    assert result["reported_tier"] == "first-order"
    assert result["completeness"] is not None
    assert result["completeness"]["eps_star"] == "1/1000000"


def test_statement_claims_on_a_key_length() -> None:
    result = report(completed_record())["sections"]["result"]
    assert [claim["id"] for claim in result["statement_claims"]] == [
        "meat-core/cor:keylength-bound",
        "meat-core/frank-wolfe/thm:firstorder",
        "meat-core/cor:composed-security",
        "meat-core/thm:keylength",
        "meat-core/lem:ev-correctness",
    ]


def test_per_execution_cites_both_claims_and_limitations_are_listed() -> None:
    result = report(completed_record())["sections"]["result"]
    assert [claim["id"] for claim in result["per_execution"]] == [
        "meat-core/rem:repeated-executions",
        "meat-core/cor:separate-executions",
    ]
    assert tuple(claim["id"] for claim in result["per_execution"]) == (
        PER_EXECUTION_CLAIMS
    )
    assert [claim["id"] for claim in result["limitations"]] == [
        "meat-core/rem:completeness-scope",
        "meat-core/rem:repeated-executions",
    ]
    anchor = result["per_execution"][1]["contract"]
    assert anchor == {
        "pdf": "spec/modules/meat-core/contract.pdf",
        "anchor": "claim-meat-core/cor:separate-executions",
    }


def test_a_refused_record_s_result_section() -> None:
    record = refused_record(eps_pa=0.5, eps_ev=0.5)
    result = report(record)["sections"]["result"]
    assert result["outcome"] == "refused"
    assert result["refusal"] == {
        "stage": "solve",
        "reason": "security_statement_vacuous",
        "detail": "a detail the module wrote",
        "rule": None,
    }
    assert result["key_length"] is None
    assert result["net_key_length"] is None
    assert result["security_parameter"]["value"] is None
    assert result["statement_claims"] == []
    assert result["completeness"] is None
    built = report(record)
    assert r3_ids(built) == []
    assert built["sections"]["numerics"]["entries"] == []


def test_an_estimate_tier_record_has_no_key_length_and_no_key_length_premises() -> None:
    built = report(estimate_record())
    result = built["sections"]["result"]
    assert result["outcome"] == "no-key-length"
    assert result["key_length"] is None
    assert result["net_key_length"] is None
    assert result["security_parameter"]["value"] is None
    assert result["reported_tier"] == "estimate"
    assert [claim["id"] for claim in result["statement_claims"]] == [
        "meat-core/lem:estimate",
    ]
    everywhere = {
        *r3_ids(built),
        *(entry["short_id"] for entry in built["sections"]["numerics"]["entries"]),
        *(entry["short_id"] for entry in built["sections"]["checks"]["decided_rows"]),
    }
    assert not everywhere & {"A-AUTH", "A-KEYREG", "A-CONFORM", "A-LMO"}


def test_a_record_without_a_key_length_raises_no_flag() -> None:
    """The flags qualify a key length, so none without one.

    The estimate-tier record's parameters are all zero (the defaults), which
    raises all three flags on a record with a length; here R3 lists none of
    A-KEYREG, A-CONFORM or A-AUTH, so a flag would cite premises the report
    does not carry and qualify numbers that do not exist.
    """
    record = estimate_record()
    parameters = record["payload"]["config"]["parameters"]
    assert (parameters["lambda_ec"], parameters["eps_auth"], parameters["k_auth"]) == (
        0, 0.0, 0,
    )
    result = report(record)["sections"]["result"]
    assert result["outcome"] == "no-key-length"
    assert result["not_counted"] == []


def test_families_by_refines_in_the_table_s_category_order() -> None:
    groups = report(completed_record())["sections"]["assumptions"]["groups"]
    assert [group["category"] for group in groups] == [
        "receiver", "channel-and-adversary", "protocol-structure", "post-processing",
    ]
    receiver = groups[0]["families"]
    assert [family["head"]["short_id"] for family in receiver] == ["A-TRUST"]
    assert [entry["short_id"] for entry in receiver[0]["members"]] == [
        "A-PORT", "A-THRESH",
    ]
    structure = groups[2]["families"]
    assert [family["head"]["short_id"] for family in structure] == ["A-SEQ", "A-SPEC"]
    # A member sits in its head's category, whatever its own category is.
    assert [entry["short_id"] for entry in structure[1]["members"]] == ["A-ALICE-MEAS"]
    assert structure[1]["members"][0]["category"] == "receiver"


def test_a_member_whose_head_is_absent_stands_alone() -> None:
    def edit(record: dict[str, Any]) -> None:
        manifest = record["payload"]["assumption_manifest"]
        manifest["assumptions"] = [
            entry for entry in manifest["assumptions"] if entry["short_id"] != "A-TRUST"
        ]

    groups = report(completed_record(edit=edit))["sections"]["assumptions"]["groups"]
    receiver = groups[0]["families"]
    assert [family["head"]["short_id"] for family in receiver] == ["A-THRESH"]
    assert [entry["short_id"] for entry in receiver[0]["members"]] == ["A-PORT"]


def test_one_entry_lists_every_emitter() -> None:
    seq = r3_entry(report(completed_record()), "A-SEQ")
    assert [emission["module"] for emission in seq["emitted_by"]] == [
        "transmitter", "reductions", "meat-core",
    ]


def test_inputs_carry_values_meanings_and_back_links() -> None:
    built = report(completed_record())
    eps_auth = select(built, "inputs/parameters.eps_auth")
    assert eps_auth["value"] == 0.0
    assert eps_auth["section"] == "key-length"
    assert eps_auth["pointer"] == "/payload/config/parameters/eps_auth"
    assert eps_auth["bound_by"] == ["A-AUTH"]
    assert select(built, "inputs/parameters.lambda_ec")["bound_by"] == [
        "A-CONFORM", "A-KEYREG",
    ]
    qber = select(built, "inputs/model.qber")
    assert qber["meaning"] == "The quantum bit error rate of the honest channel."
    assert qber["is_default"] is True
    assert qber["applies"] is True
    # A table parameter the configuration did not declare: its default, read
    # from the instance table the record carries.
    bias = select(built, "inputs/device.basis_bias")
    assert bias["value"] == "1/2"
    assert bias["pointer"] == "/payload/instance/parameters/1/default"
    assert bias["snapped"] is True


def test_a_binding_gets_a_pointer_only_where_one_resolves() -> None:
    keyreg = r3_entry(report(completed_record()), "A-KEYREG")
    bindings = {binding["name"]: binding for binding in keyreg["bindings"]}
    assert bindings["lambda_ec"]["pointer"] == "/payload/config/parameters/lambda_ec"
    assert "pointer" not in bindings["key_holder"]


def test_not_engaged_and_discharged_rows() -> None:
    sections = report(completed_record())["sections"]
    assert sections["assumptions"]["not_engaged"] == [
        {"short_id": "A-SRC", "module": "meat-core",
         "reason": "trusted-source mode at d_A >= 2"},
    ]
    assert sections["checks"]["discharged_on_route"] == [
        {"short_id": "A-LINK", "module": "protocol-compiler",
         "reason": "the identity link of Band A",
         "discharged_by": "protocol-compiler/thm:band-a"},
    ]
    assert sections["assumptions"]["discrepancies"] == []


def test_the_receiver_route_is_a_check() -> None:
    check = select(report(completed_record()), "checks/receiver-route")
    assert check["value"] == "declared-finite-povm"
    assert check["outcome"] == "passed"
    assert check["pointer"] == "/payload/stages/receiver_construction/receiver_route"


def test_provenance() -> None:
    provenance = report(completed_record())["sections"]["provenance"]
    assert provenance["engine"] == {
        "distribution_version": "0.0.1.dev0", "git_commit": "a" * 40,
        "git_dirty": False,
    }
    assert provenance["reproduce"] == {"config_pointer": "/payload/config"}
    assert provenance["record_schema_version"] == SUPPORTED_RECORD_SCHEMA_VERSION
    assert provenance["module_versions"]["contracts"]["meat-core"] == "3.0.0"
    assert provenance["artefacts"] == [
        {"stage": "solve", "station": None, "kind": "key_rate_result",
         "id": "kr-1", "digest": "b" * 64},
    ]
    assert provenance["claim_status"][0]["id"] == (
        "meat-core/cor:keylength-bound"
    )


def test_the_index_resolves_every_linked_target() -> None:
    index = report(completed_record())["index"]
    # Linked from rem:repeated-executions' summary.
    assert "meat-core/cor:separate-executions" in index["claims"]
    assert index["assumptions"]["A-SEPARATE"] == "meat-core/ass:separate-executions"
    assert "meat-core/ass:separate-executions" in index["claims"]
    assert index["assumptions"]["A-KEYREG"] == "meat-core/ass:keyreg"


def test_the_report_id_is_the_sha256_of_the_canonical_record() -> None:
    record = completed_record()
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    first = report(record)
    assert first["id"] == expected
    assert report(completed_record()) == first


def test_a_record_of_another_schema_is_refused_with_its_reason() -> None:
    record = completed_record()
    record["schema_version"] = "0.19.0"
    with pytest.raises(ReportInputError) as caught:
        report(record)
    assert caught.value.reason == "record_schema_version"


def test_what_is_not_a_run_record_is_refused() -> None:
    record = completed_record()
    record["kind"] = "preparation"
    with pytest.raises(ReportInputError) as caught:
        report(record)
    assert caught.value.reason == "not_a_run_record"


def test_the_builder_reads_the_engine_s_current_record_schema() -> None:
    from certiqs_key.runs.record import RECORD_SCHEMA_VERSION

    assert SUPPORTED_RECORD_SCHEMA_VERSION == RECORD_SCHEMA_VERSION


def test_alpha_and_parameters_alpha_are_two_inputs() -> None:
    """``alpha`` is the configuration's own; ``parameters.alpha`` the key length's."""

    def edit(record: dict[str, Any]) -> None:
        record["payload"]["config"]["alpha"] = 1.4
        record["payload"]["config"]["parameters"]["alpha"] = 1.5
        for entry in record["payload"]["assumption_manifest"]["assumptions"]:
            if entry["short_id"] == "A-SEQ":
                entry["bindings"] = [
                    {"name": "alpha", "value": 1.4, "emitted_by": []},
                    {"name": "parameters.alpha", "value": 1.5, "emitted_by": []},
                ]

    built = report(completed_record(edit=edit))
    bindings = {b["name"]: b for b in r3_entry(built, "A-SEQ")["bindings"]}
    assert bindings["alpha"]["pointer"] == "/payload/config/alpha"
    assert bindings["parameters.alpha"]["pointer"] == (
        "/payload/config/parameters/alpha"
    )
    assert select(built, "inputs/alpha")["value"] == 1.4
    assert select(built, "inputs/alpha")["bound_by"] == ["A-SEQ"]
    assert select(built, "inputs/parameters.alpha")["value"] == 1.5
    assert select(built, "inputs/parameters.alpha")["bound_by"] == ["A-SEQ"]


def test_a_bare_key_length_name_still_finds_its_parameter() -> None:
    from certiqs_key.runs.report.inputs import INPUT_POINTERS, parameter_alias

    assert parameter_alias("eps_auth") == "parameters.eps_auth"
    assert parameter_alias("parameters.eps_auth") == "eps_auth"
    assert parameter_alias("alpha") is None
    assert parameter_alias("parameters.alpha") is None
    assert INPUT_POINTERS["alpha"] == "/payload/config/alpha"
    assert INPUT_POINTERS["parameters.alpha"] == "/payload/config/parameters/alpha"
    assert INPUT_POINTERS["eps_auth"] == "/payload/config/parameters/eps_auth"


def test_a_contract_link_is_derived_from_the_claim_id_never_copied() -> None:
    def edit(record: dict[str, Any]) -> None:
        for entry in record["payload"]["assumption_manifest"]["assumptions"]:
            entry["contract"] = {"pdf": "javascript:alert(1)", "anchor": "x"}

    auth = r3_entry(report(completed_record(edit=edit)), "A-AUTH")
    assert auth["owner"]["contract"] == {
        "pdf": "spec/modules/meat-core/contract.pdf",
        "anchor": "claim-meat-core/ass:auth",
    }


def test_an_owner_that_is_not_a_claim_id_is_refused() -> None:
    def edit(record: dict[str, Any]) -> None:
        entry = record["payload"]["assumption_manifest"]["assumptions"][0]
        entry["owner"] = "javascript:alert(1)//x"

    with pytest.raises(ReportInputError) as caught:
        report(completed_record(edit=edit))
    assert caught.value.reason == "not_a_run_record"


@pytest.mark.parametrize(
    "breakage",
    ["no-config", "no-parameters", "manifest-not-object", "assumptions-not-list",
     "entry-without-owner", "binding-without-name", "stages-not-object"],
)
def test_a_truncated_or_malformed_record_is_not_a_run_record(breakage: str) -> None:
    record = completed_record()
    payload = record["payload"]
    manifest = payload["assumption_manifest"]
    if breakage == "no-config":
        del payload["config"]
    elif breakage == "no-parameters":
        del payload["config"]["parameters"]
    elif breakage == "manifest-not-object":
        payload["assumption_manifest"] = ["A-AUTH"]
    elif breakage == "assumptions-not-list":
        manifest["assumptions"] = {"A-AUTH": {}}
    elif breakage == "entry-without-owner":
        del manifest["assumptions"][0]["owner"]
    elif breakage == "binding-without-name":
        manifest["assumptions"][0]["bindings"] = [{"value": 1}]
    else:
        payload["stages"] = ["solve"]
    with pytest.raises(ReportInputError) as caught:
        report(record)
    assert caught.value.reason == "not_a_run_record"


def test_an_absent_parameter_is_flagged_as_not_recorded() -> None:
    def edit(record: dict[str, Any]) -> None:
        del record["payload"]["config"]["parameters"]["k_auth"]

    flags = report(completed_record(edit=edit))["sections"]["result"]["not_counted"]
    k_auth = next(flag for flag in flags if flag["id"] == "k_auth_zero")
    assert k_auth["value"] is None
    assert k_auth["text"] == "k_auth not recorded."
    eps_auth = next(flag for flag in flags if flag["id"] == "eps_auth_zero")
    assert eps_auth["value"] == 0.0
    assert eps_auth["text"].startswith("No authentication error counted")
