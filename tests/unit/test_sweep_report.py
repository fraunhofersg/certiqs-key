"""The sweep report: the common part once, what varies, one row per point.

Common part plus what varies: varying inputs inferred, a point on another route flagged
with its delta, refused points listed with no route, mixed instances refused, and no
field that adds ε over points.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import pytest
from tests.support.report_records import (
    completed_record,
    refused_record,
    synthetic_table,
)

from certiqs_key.runs.report import ReportInputError, build_sweep_report, select
from certiqs_key.runs.report.build import record_id
from certiqs_key.runs.report.model import SweepReport


def sweep(records: list[dict[str, Any]], **kwargs: Any) -> SweepReport:
    return build_sweep_report(records, table=synthetic_table(), **kwargs)


def without(short_id: str) -> Any:
    def edit(record: dict[str, Any]) -> None:
        manifest = record["payload"]["assumption_manifest"]
        manifest["assumptions"] = [
            entry for entry in manifest["assumptions"] if entry["short_id"] != short_id
        ]

    return edit


def keys(document: Any) -> set[str]:
    if isinstance(document, dict):
        return set(document) | {k for value in document.values() for k in keys(value)}
    if isinstance(document, list):
        return {k for value in document for k in keys(value)}
    return set()


def test_the_varying_inputs_are_inferred() -> None:
    built = sweep([completed_record(qber=q) for q in ("1/50", "1/25", "3/50")])
    assert built["varying"] == ["model.qber"]
    assert [point["values"] for point in built["points"]] == [
        {"model.qber": "1/50"}, {"model.qber": "1/25"}, {"model.qber": "3/50"},
    ]
    common = [row["name"] for row in built["common"]["inputs"]]
    assert "model.qber" not in common
    assert "parameters.eps_auth" in common


def test_points_carry_their_own_numbers() -> None:
    records = [
        completed_record(key_length=100, net_key_length=100, security_parameter=1e-9),
        completed_record(qber="1/25", key_length=50, net_key_length=50,
                         security_parameter=2e-9),
    ]
    built = sweep(records)
    assert [point["key_length"] for point in built["points"]] == [100, 50]
    assert [point["security_parameter"] for point in built["points"]] == [1e-9, 2e-9]
    assert [point["record_id"] for point in built["points"]] == [
        record_id(record) for record in records
    ]


def test_no_field_adds_epsilon_over_points() -> None:
    built = sweep([completed_record(qber=q) for q in ("1/50", "1/25")])
    top = set(built) | keys(built["common"])
    assert "security_parameter" not in top
    assert not {
        key for key in top
        if re.search(r"(^|_)(total|sum|aggregate|combined)(_|$)", key)
    }
    assert set(built) == {
        "kind", "report_schema_version", "record_schema_version", "id", "common",
        "varying", "points", "index",
    }


def test_a_point_on_another_route_is_flagged_with_its_delta() -> None:
    records = [
        completed_record(),
        completed_record(qber="1/25", edit=without("A-EIG")),
        completed_record(qber="3/50"),
    ]
    points = sweep(records)["points"]
    assert [point["route_differs"] for point in points] == [False, True, False]
    assert points[1]["route_delta"] == {"added": [], "removed": ["A-EIG"]}
    assert points[0]["route_delta"] == {"added": [], "removed": []}
    assert points[0]["route_signature"] == points[2]["route_signature"]


def test_a_tie_between_routes_goes_to_the_lowest_index() -> None:
    records = [completed_record(edit=without("A-EIG")), completed_record(qber="1/25")]
    points = sweep(records)["points"]
    assert [point["route_differs"] for point in points] == [False, True]
    assert points[1]["route_delta"] == {"added": ["A-EIG"], "removed": []}


def test_a_premise_some_points_engage_is_listed_with_its_points() -> None:
    """The three-point A-EIG case: the union, never the intersection."""
    records = [
        completed_record(),
        completed_record(qber="1/25", edit=without("A-EIG")),
        completed_record(qber="3/50"),
    ]
    common = sweep(records)["common"]
    numerics = {entry["short_id"]: entry for entry in common["numerics"]["entries"]}
    assert set(numerics) == {"A-EIG", "A-LMO"}
    assert numerics["A-EIG"]["points"] == [0, 2]
    assert numerics["A-LMO"]["points"] == "all"
    # Its text travels with it, as in a run report.
    assert numerics["A-EIG"]["user_statement"] == (
        "The eigensolver may overestimate by at most ε_eig."
    )
    assert common["numerics"]["diagnostics"] == {}


def test_an_r3_premise_of_one_point_is_listed_with_that_point() -> None:
    records = [completed_record(edit=without("A-AUTH")), completed_record(qber="1/25")]
    built = sweep(records)
    auth = select(built, "assumptions/A-AUTH")
    assert auth["points"] == [1]
    assert select(built, "assumptions/A-KEYREG")["points"] == "all"


def test_all_points_means_every_completed_point() -> None:
    records = [completed_record(), refused_record(), completed_record(qber="1/25")]
    built = sweep(records)
    assert select(built, "assumptions/A-AUTH")["points"] == "all"
    assert built["common"]["decided_rows"][0]["short_id"] == "A-DECIDED"
    assert built["common"]["decided_rows"][0]["points"] == "all"


def test_rows_discharged_on_the_route_have_a_home() -> None:
    def no_link(record: dict[str, Any]) -> None:
        manifest = record["payload"]["assumption_manifest"]
        manifest["not_engaged"] = [
            row for row in manifest["not_engaged"] if row["short_id"] != "A-LINK"
        ]

    built = sweep([completed_record(), completed_record(qber="1/25", edit=no_link)])
    discharged = built["common"]["discharged_on_route"]
    assert discharged == [
        {"short_id": "A-LINK", "module": "protocol-compiler",
         "reason": "the identity link of Band A",
         "discharged_by": "protocol-compiler/thm:band-a", "points": [0]},
    ]
    assert built["common"]["assumptions"]["not_engaged"][0]["points"] == "all"


def test_bindings_are_the_union_over_the_points() -> None:
    def other_bindings(record: dict[str, Any]) -> None:
        for entry in record["payload"]["assumption_manifest"]["assumptions"]:
            if entry["short_id"] == "A-KEYREG":
                entry["bindings"] = [
                    {"name": "lambda_ec", "value": 0,
                     "emitted_by": [{"module": "meat-core", "station": None}]},
                    {"name": "holder_station", "value": "Bob",
                     "emitted_by": [{"module": "meat-core", "station": None}]},
                ]

    built = sweep([completed_record(), completed_record(qber="1/25",
                                                        edit=other_bindings)])
    keyreg = select(built, "assumptions/A-KEYREG")
    bindings = {binding["name"]: binding for binding in keyreg["bindings"]}
    assert list(bindings) == ["lambda_ec", "key_holder", "holder_station"]
    assert bindings["lambda_ec"]["value"] == 0
    assert bindings["key_holder"].get("varies") is True
    assert bindings["holder_station"].get("varies") is True


def test_a_check_that_differs_reads_varies_with_each_point_s_outcome() -> None:
    def closed(record: dict[str, Any]) -> None:
        record["payload"]["stages"]["key_rate"]["security_gates"][
            "key_length_permitted"
        ] = False

    records = [completed_record(), completed_record(qber="1/25", edit=closed),
               refused_record()]
    checks = {check["id"]: check for check in sweep(records)["common"]["checks"]}
    gate = checks["key-length-gate"]
    assert gate["outcome"] == "varies"
    assert gate["point_outcomes"] == ["passed", "failed", "not-reached"]
    assert len(checks) == 14  # no check is dropped


def test_a_binding_whose_value_varies_is_marked() -> None:
    records = [completed_record(lambda_ec=0), completed_record(lambda_ec=4_000)]
    built = sweep(records)
    keyreg = select(built, "assumptions/A-KEYREG")
    bindings = {binding["name"]: binding for binding in keyreg["bindings"]}
    assert bindings["lambda_ec"].get("varies") is True
    assert "value" not in bindings["lambda_ec"]
    assert bindings["key_holder"]["value"] == "A"
    assert built["varying"] == ["parameters.lambda_ec"]


def test_flags_common_to_every_point_and_those_of_some() -> None:
    """The union over the completed points, each flag with its points."""
    records = [completed_record(), completed_record(eps_auth=1e-12)]
    built = sweep(records)
    assert [
        (flag["id"], flag["points"]) for flag in built["common"]["not_counted"]
    ] == [("lambda_ec_zero", "all"), ("eps_auth_zero", [0]), ("k_auth_zero", "all")]
    assert [point["flags"] for point in built["points"]] == [["eps_auth_zero"], []]


def test_a_refused_point_neither_raises_nor_removes_a_flag() -> None:
    """A refused point neither raises nor removes a flag.

    Intersecting the common block over every point, the refused one included,
    would drop a flag every completed point raised when a refused point
    carried none (or keep it when only the refused point's parameters raised
    it). The common block is the union over the completed points, ``"all"``
    meaning every completed one.
    """
    records = [completed_record(lambda_ec=1_000), refused_record(),
               completed_record(lambda_ec=1_000, qber="1/25")]
    built = sweep(records)
    assert [
        (flag["id"], flag["points"]) for flag in built["common"]["not_counted"]
    ] == [("eps_auth_zero", "all"), ("k_auth_zero", "all")]
    assert [point["flags"] for point in built["points"]] == [[], [], []]


def test_refused_points_are_listed_with_their_refusal_and_no_route() -> None:
    records = [completed_record(), refused_record(eps_pa=0.5, eps_ev=0.5)]
    built = sweep(records)
    refused = built["points"][1]
    assert refused["outcome"] == "refused"
    assert refused["refusal"] is not None
    assert refused["refusal"]["reason"] == "security_statement_vacuous"
    assert refused["route_signature"] is None
    assert refused["route_differs"] is False
    assert refused["key_length"] is None
    # The common assumptions are the completed points'.
    assert "A-AUTH" in [
        family["head"]["short_id"]
        for group in built["common"]["assumptions"]["groups"]
        for family in group["families"]
    ]


def test_checks_with_one_outcome_everywhere_are_common() -> None:
    records = [completed_record(), completed_record(qber="1/25", key_length=7,
                                                    net_key_length=7)]
    common = {check["id"]: check for check in sweep(records)["common"]["checks"]}
    assert common["reported-key-length"].get("value_varies") is True
    assert common["reported-key-length"]["value"] is None
    assert common["receiver-route"]["value"] == "declared-finite-povm"


def test_mixed_instances_are_refused() -> None:
    with pytest.raises(ReportInputError) as caught:
        sweep([completed_record(), completed_record(instance_id="decoy_bb84")])
    assert caught.value.reason == "mixed_instances"


def test_mixed_record_schemas_are_refused() -> None:
    old = completed_record()
    old["schema_version"] = "0.19.0"
    with pytest.raises(ReportInputError) as caught:
        sweep([completed_record(), old])
    assert caught.value.reason == "record_schema_version"


def test_labels_name_the_points_and_must_match_in_number() -> None:
    records = [completed_record(), completed_record(qber="1/25")]
    built = sweep(records, labels=["run-a", "run-b"])
    assert [point["label"] for point in built["points"]] == ["run-a", "run-b"]
    with pytest.raises(ReportInputError) as caught:
        sweep(records, labels=["only-one"])
    assert caught.value.reason == "labels_mismatch"


def test_the_sweep_id_is_the_sha256_over_the_record_ids_in_order() -> None:
    records = [completed_record(), completed_record(qber="1/25")]
    expected = hashlib.sha256(
        "\n".join(record_id(record) for record in records).encode("utf-8")
    ).hexdigest()
    assert sweep(records)["id"] == expected
    assert sweep(list(reversed(records)))["id"] != expected


def test_an_empty_sweep_is_refused() -> None:
    with pytest.raises(ReportInputError) as caught:
        sweep([])
    assert caught.value.reason == "no_records"
