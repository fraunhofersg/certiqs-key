"""The key-rate report off the paths the shipped examples take.

A robustness pass with toy protocols found reports that
state false or misleading things on paths no shipped example takes: a run
refused at compilation, a run whose key length is 0, a basis weight that is
not dyadic and was moved onto the 2^-40 lattice, complex operator entries,
and a few mechanical defects its lint found. Each test states one fact a
reader relies on, by the write-up's id; the expected texts are written by hand
from the hand-written record, never read back from the renderer.
"""

from __future__ import annotations

from typing import Any

from tests.support.report_records import (
    completed_record,
    refused_record,
    synthetic_table,
)

from certiqs_key.runs.report import (
    build_report,
    build_sweep_report,
    default_contract_link,
    render_markdown,
    render_sweep_markdown,
)
from certiqs_key.runs.report._page import _snap_cell
from certiqs_key.runs.report._render import format_entry
from certiqs_key.runs.report.explain import roles_box
from certiqs_key.runs.report.model import KeyRateReport, SweepPoint
from certiqs_key.runs.report.setup import _conjugates
from certiqs_key.runs.roles import PublicChoice, Roles


def built(record: dict[str, Any]) -> KeyRateReport:
    return build_report(record, table=synthetic_table())


def md(report: KeyRateReport) -> str:
    return render_markdown(report, contract_link=default_contract_link())


def checks(report: KeyRateReport) -> dict[str, dict[str, Any]]:
    found = report["sections"]["checks"]["checks"]
    return {check["id"]: dict(check) for check in found}


def steps(report: KeyRateReport) -> dict[str, str]:
    return {step["title"]: step["text"]
            for step in report["sections"]["setup"]["protocol"]}


def compilation_refusal(**payload: Any) -> dict[str, Any]:
    """Return a Band-A document run refused at compilation: no receiver stage."""
    record = refused_record(stage="compilation",
                            reason="band_a_outside_ideal_receiver")
    record["payload"].update(payload)
    return record


DOCUMENT = {
    "id": "toy", "format_version": "1", "packaged": False, "digest": "0" * 64,
    "user_declared": [{
        "kind": "receiver_povm", "path": "/stations/0", "label": "bob",
        "text": "The measurement of station 'bob', declared as a POVM.",
        "assumptions": ["A-SPEC"],
    }],
}


# --------------------------------------------------------------------------
# B1: no receiver route on a run refused at compilation
# --------------------------------------------------------------------------


def test_a_route_never_reached_is_not_reached_rather_than_passed() -> None:
    found = checks(built(compilation_refusal()))
    assert found["receiver-route"]["outcome"] == "not-reached"
    assert found["receiver-route"]["value"] is None


def test_a_route_taken_before_the_refusal_still_reads_passed() -> None:
    # The receiver stage is on the path (an optical station built before the
    # compiler refused): a route was taken, though the record does not name it.
    record = compilation_refusal(composition_flow={"stages": [
        {"stage": "receiver_construction", "status": "executed"},
        {"stage": "compilation", "status": "refused"},
    ], "mermaid": ""})
    assert checks(built(record))["receiver-route"]["outcome"] == "passed"
    # And past compilation the route was taken on every path.
    assert checks(built(refused_record()))["receiver-route"]["outcome"] == "passed"


# --------------------------------------------------------------------------
# B2, m2: the protocol steps a refused run never reached
# --------------------------------------------------------------------------


def test_a_step_the_refusal_preceded_says_it_was_not_reached() -> None:
    found = steps(built(compilation_refusal()))
    unreached = ("Not reached: the run was refused at its compilation stage, "
                 "before this step.")
    for title in ("Source", "Measurement", "Public choice", "Announcements",
                  "Sifting and key map", "Acceptance test"):
        assert found[title] == unreached, title
    # No key length deducts the leakage on a refused run.
    assert found["Error correction"] == (
        "One-way error correction; its transcript leaks λ_EC = 0 bits."
    )


def test_a_step_a_later_refusal_left_out_says_the_record_lacks_it() -> None:
    found = steps(built(refused_record()))
    assert found["Public choice"] == "The record does not hold this step."
    assert found["Acceptance test"] == "The record does not hold this step."


def test_a_compiled_run_without_a_choice_still_says_so() -> None:
    found = steps(built(completed_record()))
    assert found["Public choice"] == (
        "The record holds no public choice (no test coin and no basis choice "
        "announced separately)."
    )
    assert found["Error correction"] == (
        "One-way error correction; its transcript leaks λ_EC = 0 bits, which "
        "the key length deducts."
    )


def test_how_computed_explains_no_key_rate_on_a_refused_run() -> None:
    text = md(built(compilation_refusal()))
    part = text[text.index('id="how-computed"'):text.index('id="security-claims"')]
    assert ("The run was refused at its compilation stage, before the solve, so "
            "no key length was reported and no bound was formed. The table holds "
            "what the record states.") in part
    assert "headline key rate" not in part
    assert "This sets the key length." not in part


def test_a_solve_refusal_names_the_bound_its_record_holds() -> None:
    # The run tier's plausibility refusal records the bound and the estimate.
    record = refused_record(reason="entropy_bound_above_key_ceiling")
    record["payload"]["stages"]["solve"]["plausibility"] = {
        "bound_name": "h_cert", "bound": 1.25, "h_low": 1.5,
    }
    text = md(built(record))
    assert ("The run was refused at its solve stage, so no key length was "
            "reported. The record holds the bound the solve formed, h_cert = "
            "1.25 bits per round, beside the solver's estimate h_low = 1.5. The "
            "table holds what the record states.") in text
    # A solve refusal with no number recorded says so.
    assert ("The run was refused at its solve stage, so no key length was "
            "reported. The record holds no bound.") in md(built(refused_record()))


# --------------------------------------------------------------------------
# B3: a snapped input is shown with the value the run analysed
# --------------------------------------------------------------------------


def _snapped_inputs() -> dict[str, Any]:
    """Return a document run whose snap.groups moved Bob's weights 2/3, 1/3."""

    def edit(record: dict[str, Any]) -> None:
        payload = record["payload"]
        payload["config"]["device"] = {"bob_x": "2/3", "bob_z": "1/3"}
        payload["snaps"]["instance"] = {"input_preparation": [{
            "site": "device.bob_x+bob_z",
            "rule": "shared_family_snap",
            "input_values": ["2/3", "1/3"],
            "prepared_values": ["733007751851/1099511627776",
                                "366503875925/1099511627776"],
            "total_displacement": ["1/3298534883328", "-1/3298534883328"],
            "normalization_defect": "0",
            "admission": "declared_tolerance",
            "declared_tolerance": 0.0,
        }]}

    return completed_record(edit=edit)


def test_a_snapped_weight_shows_the_analysed_value_and_the_move() -> None:
    report = built(_snapped_inputs())
    rows = {row["name"]: row for row in report["sections"]["protocol"]["inputs"]}
    assert rows["device.bob_x"]["prepared"] == "733007751851/1099511627776"
    assert rows["device.bob_z"]["prepared"] == "366503875925/1099511627776"
    # 2/3 - 733007751851/2^40 = 1/(3 * 2^40) = 3.03e-13.
    assert ("0.666667 (733007751851/1099511627776), prepared from the requested "
            "0.666667 (2/3) and analysed (moved by 3.03e-13)") in md(report)


def test_the_snap_check_and_the_preparation_state_the_move() -> None:
    report = built(_snapped_inputs())
    snap = checks(report)["snaps-within-tolerance"]
    assert snap["outcome"] == "passed"
    # The record's snap_max_defect stays as it states it (null: no measurement
    # block snapped); the input move stands beside it under its own name.
    assert snap["value"] == {
        "snap_max_defect": None, "declared_tolerance": 0.0,
        "inputs_moved": {"device.bob_x+bob_z": 1 / 3298534883328},
        "input_normalization_defect": 0.0,
    }
    preparation = report["sections"]["protocol"]["preparation"]
    assert preparation["input_preparation_pointer"] == (
        "/payload/snaps/instance/input_preparation")
    assert preparation["snap_max_defect"] is None
    assert preparation["snap_max_displacement"] is None
    assert preparation.get("input_max_displacement") == 1 / 3298534883328
    assert preparation.get("input_normalization_defect") == 0.0


def test_a_move_admitted_by_its_rounding_cells_is_said_to_be_untested() -> None:
    record = _snapped_inputs()
    entry = record["payload"]["snaps"]["instance"]["input_preparation"][0]
    entry["admission"] = "float_rounding_cells"
    entry["normalization_defect"] = "1/1000"
    snap = checks(built(record))["snaps-within-tolerance"]
    # 1/1000 is above tau = 0, but tau does not bound it: passed, and said so.
    assert snap["outcome"] == "passed"
    assert snap["value"]["not_tested_against_tau"] == {
        "device.bob_x+bob_z": "admitted by its float rounding cells",
    }
    assert snap["value"]["input_normalization_defect"] == 0.001


def test_a_run_that_moved_nothing_keeps_its_snap_fields() -> None:
    report = built(completed_record())
    snap = checks(report)["snaps-within-tolerance"]
    assert snap["value"] == {"snap_max_defect": None, "declared_tolerance": 0.0}
    preparation = report["sections"]["protocol"]["preparation"]
    assert preparation["input_preparation_pointer"] is None
    assert preparation["snap_max_displacement"] is None
    assert "input_max_displacement" not in preparation


# --------------------------------------------------------------------------
# M1: a key length of 0 is no key, with the cause the record states
# --------------------------------------------------------------------------


def _zero_key(
    h_lb: float, status: str = "iteration-limit", lambda_ec: float = 0.0,
    penalty: float = 0.0,
) -> dict[str, Any]:
    """Return a key length of 0 from n = 100,000 rounds; 359 bits deducted."""

    def edit(record: dict[str, Any]) -> None:
        payload = record["payload"]
        payload["config"]["rounds"] = 100_000
        payload["stages"]["key_rate"].update(
            rounds=100_000, key_length=0, net_key_length=0, rate_per_round=0.0,
            h_lb=h_lb, h_low=0.0028, frank_wolfe_gap=0.0039,
            solver_status=status, iterations=10,
            deductions={"error_correction_lambda_ec": lambda_ec,
                        "error_verification": 30.0,
                        "privacy_amplification": 330.0,
                        "two_universal_hash_penalty": penalty,
                        "accepted_state_flag_bonus": 1.0},
        )

    return completed_record(edit=edit)


def test_a_zero_key_leads_the_box_and_the_result_with_no_key() -> None:
    summary = built(_zero_key(-0.0004))["sections"]["summary"]
    first = summary["at_a_glance"][0]
    assert (first["lead"], first["text"]) == (
        "No key at these settings",
        ": the key length is \u2113 = 0 bits from n = 100,000 rounds",
    )
    leads = [item["lead"] for item in summary["at_a_glance"]]
    assert not any(lead.startswith(("Key length", "Key rate")) for lead in leads)
    assert summary["result"].startswith(
        "No key at these settings: from n = 100,000 rounds the key length is "
        "\u2113 = 0 bits. The bound the key length is computed from, h_lb = "
        "-0.0004 bits per round, is not positive, so the accumulated entropy is "
        "clamped at 0 ([[meat-core/cor:keylength-bound]]). The solver stopped "
        "at its step limit of 10 steps with a Frank-Wolfe gap of 0.0039 bits "
        "per round, larger than |h_lb| = 0.0004, while its estimate of h_low "
        "is 0.0028 bits per round, positive. The estimate is not a bound and "
        "gives no key ([[meat-core/frank-wolfe/thm:firstorder]])."
    )
    assert "outputs a key" not in summary["result"]
    assert summary["considerations"][0]["text"].startswith(
        "No key at these settings. The bound the key length is computed from")
    assert summary["considerations"][0]["anchor"] == "levers"


def test_a_zero_key_names_the_step_limit_and_the_rounds_as_levers() -> None:
    levers = [item["text"] for item in
              built(_zero_key(-0.0004))["sections"]["summary"]["levers"]]
    assert levers[0] == (
        "Solver step limit: the search stopped at its limit of 10 steps with a "
        "Frank-Wolfe gap of 0.0039 bits per round, larger than |h_lb| = 0.0004; "
        "more steps (solver.max_iterations) may close the gap and give a "
        "positive key length ([[meat-core/frank-wolfe/thm:firstorder]])."
    )
    # 100,000 x 0.0028 = 280 bits < 360; conditional on more steps, since
    # h_lb is not positive.
    assert levers[1] == (
        "Rounds n: if more steps make h_lb positive, the rounds matter too: at "
        "n = 100,000, n times the solver's estimate of h_low is ≈ 280 bits (the "
        "estimate is not a bound), short of the 360 bits a one-bit key needs: "
        "the 359 bits the key length deducts and one more. Of these deductions, "
        "359 bits do not grow with n: the verification hash (30 bits) and the "
        "finite-size term of privacy amplification (330 bits), less the "
        "constant bit. So more rounds may leave a key "
        "([[meat-core/thm:keylength]])."
    )


def test_a_converged_bound_below_zero_names_no_rounds_lever() -> None:
    # max{0, h} = 0 at every n: more rounds alone give no key.
    levers = [item["text"] for item in built(_zero_key(-1e-6, status="converged"))[
        "sections"]["summary"]["levers"]]
    assert not any(text.startswith(("Rounds n", "Solver step limit"))
                   for text in levers)


def test_a_lambda_ec_that_grows_with_n_is_weighed_per_round() -> None:
    # lambda_EC = 150 bits: 0.0015 per round, below h_lb = 0.002. The hash
    # penalty is one of the deductions that do not grow with n.
    levers = [item["text"] for item in built(_zero_key(
        0.002, status="converged", lambda_ec=150.0, penalty=1.0))[
        "sections"]["summary"]["levers"]]
    assert ("Rounds n: at n = 100,000, n·h_lb is ≈ 200 bits, short of the 511 "
            "bits a one-bit key needs: the 510 bits the key length deducts and "
            "one more. Of these deductions, 360 bits do not grow with n: the "
            "verification hash (30 bits), the finite-size term of privacy "
            "amplification (330 bits) and the hash penalty (1 bit), less the "
            "constant bit; λ_EC = 150 bits is taken to grow with n, as an "
            "estimate from the honest model does, and 0.002 bits per round "
            "exceeds λ_EC/n = 0.0015. So more rounds may leave a key "
            "([[meat-core/thm:keylength]]).") in levers
    # lambda_EC = 250 bits: 0.0025 per round, above h_lb; more rounds do not help.
    levers = [item["text"] for item in built(_zero_key(
        0.002, status="converged", lambda_ec=250.0))["sections"]["summary"]["levers"]]
    assert not any(text.startswith("Rounds n") for text in levers)


def test_a_sum_within_one_bit_of_the_deductions_rounds_down() -> None:
    # 100,000 x 0.003595 = 359.5 bits: above the 359 deducted, below 360.
    result = built(_zero_key(0.003595, status="converged"))[
        "sections"]["summary"]["result"]
    assert ("The accumulated entropy n·h_lb ≈ 359.5 bits, less the 359 bits the "
            "key length deducts for error correction, error verification and "
            "privacy amplification (the constant bit added back), leaves less "
            "than one bit, which rounds down to 0 "
            "([[meat-core/thm:keylength]]).") in result
    assert "is less than the 359 bits" not in result


def test_a_positive_bound_below_the_costs_is_said_as_such() -> None:
    summary = built(_zero_key(0.002, status="converged"))["sections"]["summary"]
    # 100,000 x 0.002 = 200 bits < 359; the solver converged, so no step limit.
    assert ("\u2113 = 0 bits. The accumulated entropy n·h_lb ≈ 200 bits is less than "
            "the 359 bits the key length deducts for error correction, error "
            "verification and privacy amplification, less the constant bit "
            "([[meat-core/thm:keylength]]).") in summary["result"]
    assert "step limit" not in summary["result"]
    levers = [item["text"] for item in summary["levers"]]
    assert not any(text.startswith("Solver step limit") for text in levers)
    assert any(text.startswith("Rounds n: at n = 100,000, n·h_lb is ≈ 200 bits, "
                               "short of the 360 bits") for text in levers)


def test_a_positive_key_names_neither_lever() -> None:
    summary = built(completed_record())["sections"]["summary"]
    assert summary["at_a_glance"][0]["lead"] != "No key at these settings"
    levers = [item["text"] for item in summary["levers"]]
    assert not any(text.startswith(("Solver step limit", "Rounds n"))
                   for text in levers)


# --------------------------------------------------------------------------
# M2: what a protocol document can change, per refusal code
# --------------------------------------------------------------------------


def test_a_document_refusal_says_what_the_document_can_change() -> None:
    result = built(compilation_refusal(protocol_document=DOCUMENT))[
        "sections"]["summary"]["result"]
    assert result.endswith(
        "In a protocol document, declared_povm stations with the identity link "
        "put the run on the Band-A route ([[protocol-compiler/def:banda]]) "
        "wherever the source carries no source segment and the emitted sector "
        "set is a single sector, and that route admits exactly one measured "
        "station: one declared_povm station on a receiver system of dimension "
        "two (and, with a trusted source, a transmitted system of dimension "
        "two), its family projective as declared "
        "([[protocol-compiler/req:band-a-ideal-receiver]]). Declare any other "
        "receiver, and each station of a protocol in which both parties "
        "measure, as an optical station (kind: optical); see "
        "instances/declared/README.md."
    )


def test_a_refusal_off_the_document_route_adds_no_hint() -> None:
    result = built(compilation_refusal())["sections"]["summary"]["result"]
    assert result.endswith("Why: a detail the module wrote.")


# --------------------------------------------------------------------------
# m1: the statistics check that did not run
# --------------------------------------------------------------------------


def _statistics_row(report: KeyRateReport) -> str:
    text = md(report)
    line = next(line for line in text.splitlines()
                if 'id="input-parameters.statistics_check"' in line)
    return line.split(" | ")[1]


def test_a_check_asked_for_and_out_of_scope_reads_not_run() -> None:
    def edit(record: dict[str, Any]) -> None:
        payload = record["payload"]
        payload["config"]["parameters"]["statistics_check"] = "on"
        payload["statistics_consistency"] = {
            "checked": False, "unchecked_reason": "out_of_scope", "orders": [],
            "solve": None, "refused": False, "min_model_pass_probability": "1/2",
        }

    assert _statistics_row(built(completed_record(edit=edit))) == (
        "on (not run: the statistics are your honest model's predictions and "
        "you declared no constraint entry)"
    )


def test_a_check_on_a_run_refused_before_the_solve_reads_not_run() -> None:
    record = compilation_refusal(statistics_consistency={
        "checked": True, "unchecked_reason": None, "orders": [], "solve": None,
        "refused": False, "min_model_pass_probability": "1/2",
    })
    record["payload"]["config"]["parameters"]["statistics_check"] = "on"
    assert _statistics_row(built(record)) == (
        "on (not run: the run was refused at its compilation stage, before the "
        "solve)"
    )


# --------------------------------------------------------------------------
# m3, m4: a refused run's empty lists
# --------------------------------------------------------------------------


def test_the_premises_a_document_declared_are_said_to_follow() -> None:
    text = md(built(compilation_refusal(protocol_document=DOCUMENT)))
    assert ("No assumption of the run is listed because the run was refused at "
            "stage compilation (band_a_outside_ideal_receiver) before any result "
            "named a claim. The premises your protocol document declared are "
            "listed below.") in text
    plain = md(built(compilation_refusal()))
    assert "before any result named a claim.\n" in plain
    assert "The premises your protocol document declared" not in plain


def test_an_empty_claim_status_is_a_sentence_not_a_table() -> None:
    text = md(built(compilation_refusal()))
    part = text[text.index("Claim status"):]
    assert part.startswith(
        "Claim status\n\nNo claim status is listed: the run was refused before "
        "any result named a claim."
    )
    assert "| Claim | Review status" not in text


# --------------------------------------------------------------------------
# m6, m7: complex operator entries
# --------------------------------------------------------------------------


def test_an_imaginary_fraction_carries_the_i_in_its_numerator() -> None:
    assert format_entry(["0", "1/8"]) == "i/8"
    assert format_entry(["0", "-1/2"]) == "-i/2"
    assert format_entry(["1/2", "3/8"]) == "1/2 + 3i/8"
    assert format_entry(["1/2", "-1/4"]) == "1/2 \u2212 i/4"
    assert format_entry([0.0, 0.5]) == "0.5i"


def _matrix(rows: list[list[tuple[str, str]]]) -> list[list[list[str | float]]]:
    return [[[real, imaginary] for real, imaginary in row] for row in rows]


def test_operators_that_are_weighted_conjugates_are_recognised() -> None:
    # |+i><+i| = [[1/2, -i/2], [i/2, 1/2]]; its conjugate weighted by 1/4.
    state = _matrix([[("1/2", "0"), ("0", "-1/2")], [("0", "1/2"), ("1/2", "0")]])
    operator = _matrix([[("1/8", "0"), ("0", "1/8")], [("0", "-1/8"), ("1/8", "0")]])
    states = [{"outcome": "(Y,0)", "matrix": state}]
    assert _conjugates([{"outcome": "(Y,0)", "matrix": operator}], states)
    # The state itself, not its conjugate, is not.
    assert not _conjugates([{"outcome": "(Y,0)", "matrix": state}], states)
    # A real operator has no complex entry to explain.
    real = _matrix([[("1/2", "0"), ("0", "0")], [("0", "0"), ("0", "0")]])
    assert not _conjugates([{"outcome": "(Z,0)", "matrix": real}],
                           [{"outcome": "(Z,0)", "matrix": real}])
    # An operator whose signal has no declared state: the sentence, which
    # speaks of all of them, is not said.
    assert not _conjugates([{"outcome": "(Y,0)", "matrix": operator},
                            {"outcome": "(Y,1)", "matrix": operator}], states)


def test_a_record_before_the_pbs_split_keeps_its_idealised_extinction() -> None:
    def edit(record: dict[str, Any]) -> None:
        record["payload"]["config"]["device"] = {"pbs_extinction": "0"}

    summary = built(completed_record(edit=edit))["sections"]["summary"]
    assert any("(polarising beam splitter extinction 0)" in item["text"]
               for item in summary["considerations"])


# --------------------------------------------------------------------------
# m12, n1, n3: the lint's mechanical findings
# --------------------------------------------------------------------------


def test_the_sweep_page_carries_the_status_legend_it_links() -> None:
    sweep = build_sweep_report([completed_record(), completed_record(qber="1/20")],
                               table=synthetic_table())
    text = render_sweep_markdown(sweep, contract_link=default_contract_link(),
                                 point_link=lambda point: f"points/{point['index']}.md")
    assert '<a id="status-legend"></a>What a claim\'s status means' in text


def test_an_empty_binding_reads_none() -> None:
    def edit(record: dict[str, Any]) -> None:
        entry = record["payload"]["assumption_manifest"]["assumptions"][0]
        entry["bindings"].append({
            "name": "declared_tolerance_fields", "value": [],
            "emitted_by": [{"module": "receiver", "station": None}],
        })

    text = md(built(completed_record(edit=edit)))
    assert "- declared_tolerance_fields: none\n" in text


def test_three_choices_read_as_a_list() -> None:
    roles = Roles(
        source_mode="trusted", source_trusted=True, alice_party="A",
        alice_dim=2, letters=("0", "1"), transmitted_dim=2, key_holder="A",
        stations=(), choosers=frozenset({"A"}), message_senders=(),
        public_choices=(PublicChoice("A", False, None, ("Z", "X", "Y"), False),),
    )
    line = next(line for line in roles_box(roles) if line.startswith("Public"))
    assert line.startswith("Public choices: Z, X or Y, drawn by Alice")


def test_block_counts_agree_in_number() -> None:
    point: SweepPoint = {"rests_on_a_snap": True, "resting_blocks": 1,  # type: ignore[typeddict-item]
                         "resting_sectors": 2}
    assert _snap_cell(point) == "rests on A-SNAP (1 block, 2 emission sectors)"
    point["resting_blocks"], point["resting_sectors"] = 4, 1
    assert _snap_cell(point) == "rests on A-SNAP (4 blocks, 1 emission sector)"
