"""Synthetic run records and a synthetic closure table for the key-rate report tests.

WHY SYNTHETIC. The report is built from the run record's assumption manifest
and instance blocks, whose shape is assumed here. Every record here is
hand-written in that shape, so each
expectation in the tests is a hand-written fact about a hand-written input and
not a value read back from the code under test. The closure table is small
and hand-written for the same reason, and so that the tests do not move when
the shipped table is regenerated from the claim headers.

THE SHAPE ASSUMED of the record:

- ``payload.assumption_manifest.assumptions``: one entry per short id, with
  the closure table's snapshot fields (title, summary, user_statement,
  category, affects, refines, verification, verification_sentence, status,
  effective_status, contract), ``machine_key``, ``owner``, ``emitted_by`` as a
  list of ``{module, station, machine_key, inherited_from}`` and ``bindings``
  as a list of ``{name, value | input, emitted_by: [{module, station}]}``;
- ``not_engaged`` (``{short_id, module, reason}``, plus ``discharged_by`` for a
  row a route discharges) and ``discrepancies``;
- ``payload.instance`` (descriptor plus ``parameters``, the instance's
  ``ParameterSpec.as_payload()`` list) and ``payload.provenance.engine``;
- ``config.parameters.eps_auth`` and ``k_auth``;
  ``stages.key_rate.security_parameter`` and ``net_key_length``;
  ``stages.receiver_construction.receiver_route``.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from certiqs_key.runs.report.build import SUPPORTED_RECORD_SCHEMA_VERSION
from certiqs_key.runs.report.checks import CHECK_CLAIMS

__all__ = [
    "A_SNAP_ENTRY",
    "LAST_RESORT_FIX",
    "SNAP_BLOCKS",
    "assumption",
    "completed_record",
    "estimate_record",
    "refused_record",
    "snap_block",
    "snapped_record",
    "synthetic_table",
    "with_snaps",
]

NEVER = (
    "The engine does not verify this assumption; a run that rests on it records "
    "it as unverified."
)
DECIDED = "The engine decides this condition on every run that rests on it."


def _contract(claim_id: str) -> dict[str, str]:
    core = claim_id.split("/", 1)[0]
    return {"pdf": f"spec/modules/{core}/contract.pdf", "anchor": f"claim-{claim_id}"}


def _claim(
    claim_id: str, kind: str, word: str, title: str, summary: str
) -> dict[str, Any]:
    return {
        "kind": kind,
        "kind_word": word,
        "title": title,
        "summary": summary,
        "status": "accepted",
        "effective_status": "accepted",
        "contract": _contract(claim_id),
    }


def synthetic_table() -> dict[str, Any]:
    """Return a hand-written closure table carrying every claim a report cites."""
    claims: dict[str, Any] = {
        "meat-core/cor:keylength-bound": _claim(
            "meat-core/cor:keylength-bound", "cor", "Corollary",
            "Key length from an entropy lower bound",
            "The key length computed from any lower bound h on h_low."),
        "meat-core/frank-wolfe/thm:firstorder": _claim(
            "meat-core/frank-wolfe/thm:firstorder", "thm", "Theorem",
            "The estimate and the first-order lower bound",
            "The best linearisation over the iterates bounds h_low from below."),
        "meat-core/lem:estimate": _claim(
            "meat-core/lem:estimate", "lem", "Lemma", "The estimate",
            "h_low at the returned point bounds the true value from above."),
        "meat-core/cor:composed-security": _claim(
            "meat-core/cor:composed-security", "cor", "Corollary",
            "Composed security with authentication",
            "The protocol is (ε_PA + ε_EV + 2ε_auth)-secure ([[A-AUTH]])."),
        "meat-core/thm:keylength": _claim(
            "meat-core/thm:keylength", "thm", "Theorem", "Secrecy of the key",
            "The key is ε_PA-secret."),
        "meat-core/lem:ev-correctness": _claim(
            "meat-core/lem:ev-correctness", "lem", "Lemma", "Correctness",
            "The keys agree except with probability ε_EV."),
        "meat-core/rem:repeated-executions": _claim(
            "meat-core/rem:repeated-executions", "rem", "Remark",
            "One execution's security parameter and a reused key",
            "One execution's parameter covers one run, and separate executions "
            "add their parameters ([[meat-core/cor:separate-executions]]) under "
            "[[A-SEPARATE]]."),
        "meat-core/cor:separate-executions": _claim(
            "meat-core/cor:separate-executions", "cor", "Corollary",
            "Security parameters of separate executions add",
            "N executions that share no key are together (ε_1 + ... + ε_N)-secure."),
        "meat-core/rem:completeness-scope": _claim(
            "meat-core/rem:completeness-scope", "rem", "Remark",
            "What the completeness figure covers",
            "The completeness figure is the honest abort probability."),
        "meat-core/ass:separate-executions": _claim(
            "meat-core/ass:separate-executions", "ass", "Assumption",
            "Executions that share no key and no device state",
            "Several executions touch none of each other's registers."),
        "statistics/binomial-box/req:completeness-report": _claim(
            "statistics/binomial-box/req:completeness-report", "req", "Requirement",
            "The reported completeness figure", "The engine reports ε* itself."),
    }
    for claim_id in CHECK_CLAIMS:
        claims.setdefault(
            claim_id,
            _claim(claim_id, claim_id.split(":", 1)[0].rsplit("/", 1)[-1],
                   "Requirement", f"Title of {claim_id}", f"Summary of {claim_id}."),
        )
    return {
        "assumptions": {
            "A-AUTH": {"owner": "meat-core/ass:auth"},
            "A-SEPARATE": {"owner": "meat-core/ass:separate-executions"},
        },
        "category_order": [
            "source", "receiver", "channel-and-adversary", "protocol-structure",
            "local-randomness", "post-processing", "honest-model",
            "supplied-artefact", "numerical-trust",
        ],
        "claims": claims,
        "limitations": [
            "meat-core/rem:completeness-scope",
            "meat-core/rem:repeated-executions",
        ],
    }


def assumption(
    short_id: str,
    owner: str,
    machine_key: str,
    *,
    category: str | None,
    title: str,
    summary: str = "",
    user_statement: str | None = None,
    affects: list[str] | None = None,
    refines: str | None = None,
    verification: str = "never",
    emitted_by: tuple[str, ...] = ("meat-core",),
    bindings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return one record entry in the shape the manifest carries."""
    return {
        "short_id": short_id,
        "machine_key": machine_key,
        "owner": owner,
        "title": title,
        "summary": summary or f"Summary of {short_id}.",
        "user_statement": user_statement,
        "category": category,
        "affects": affects,
        "refines": refines,
        "verification": verification,
        "verification_sentence": NEVER if verification == "never" else DECIDED,
        "status": "accepted",
        "effective_status": "accepted",
        "contract": _contract(owner),
        "emitted_by": [
            {"module": module, "station": None, "machine_key": machine_key,
             "inherited_from": None}
            for module in emitted_by
        ],
        "bindings": bindings or [],
    }


def _binding(name: str, value: Any, module: str = "meat-core") -> dict[str, Any]:
    return {"name": name, "value": value,
            "emitted_by": [{"module": module, "station": None}]}


AUTH_STATEMENT = (
    "Every classical message of your protocol is protected by one authentication "
    "scheme. ε_auth is its composable error plus the distance δ of a reused key "
    "from an ideal one; declare that sum as ε_auth and the key bits used as "
    "k_auth. The reconciliation is [[A-KEYREG]]'s."
)


def _key_entries(eps_auth: Any = 0.0, k_auth: Any = 0, lambda_ec: Any = 0) -> list[
    dict[str, Any]
]:
    """Return the entries a run that reports a key length carries in addition."""
    return [
        assumption(
            "A-AUTH", "meat-core/ass:auth", "classical_channel_authenticated",
            category="channel-and-adversary",
            title="Authentication of the classical channel by a keyed scheme",
            summary="Every classical message travels through an authentication "
                    "scheme within ε_auth.",
            user_statement=AUTH_STATEMENT, affects=["secrecy", "correctness"],
            bindings=[_binding("eps_auth", eps_auth), _binding("k_auth", k_auth)],
        ),
        assumption(
            "A-KEYREG", "meat-core/ass:keyreg", "key_register",
            category="post-processing",
            title="Dedicated key register and one-way reconciliation",
            user_statement="Error correction is one-way; the transcript has "
                           "exactly λ_EC bits.",
            affects=["secrecy"],
            bindings=[_binding("lambda_ec", lambda_ec), _binding("key_holder", "A")],
        ),
        assumption(
            "A-CONFORM", "meat-core/ass:conform", "post_processing_as_analysed",
            category="post-processing", title="The post-processing as analysed",
            user_statement="Your implementation runs the analysed post-processing.",
            affects=["secrecy", "correctness"],
            bindings=[
                _binding("rounds", 1_000_000_000),
                _binding("lambda_ec", lambda_ec),
            ],
        ),
    ]


def _common_entries() -> list[dict[str, Any]]:
    """Return the entries every completed synthetic run carries."""
    return [
        assumption(
            "A-LMO", "meat-core/frank-wolfe/ass:lmo", "exact_linear_oracle",
            category="numerical-trust",
            title="Exact linear minimisation over the feasible set",
            bindings=[_binding("oracle", "qics")],
        ),
        assumption(
            "A-EIG", "receiver/ass:eig", "exact_window_eigenvalue_slack",
            category="numerical-trust",
            title="Declared slack on the computed block eigenvalues",
            user_statement="The eigensolver may overestimate by at most ε_eig.",
            affects=["secrecy"], emitted_by=("receiver",),
            bindings=[_binding("eps_eig", 1e-12, "receiver")],
        ),
        assumption(
            "A-TRUST", "receiver/ass:trust", "receiver_trusted_exact",
            category="receiver", title="Trusted exact receiver",
            user_statement="Your receiver is the declared one.",
            affects=["secrecy"], emitted_by=("receiver",),
        ),
        assumption(
            "A-THRESH", "receiver/ass:thresh", "threshold_memoryless_detectors",
            category="receiver", title="Threshold memoryless detectors",
            user_statement="Each detector clicks or not, with no memory.",
            affects=["secrecy"], refines="A-TRUST", emitted_by=("receiver",),
            bindings=[_binding("tau", "1", "receiver")],
        ),
        assumption(
            "A-PORT", "receiver/ass:port", "mode_insensitive_ports",
            category="receiver", title="Mode-insensitive ports",
            user_statement="Each port responds alike to every mode.",
            affects=["secrecy"], refines="A-THRESH", emitted_by=("receiver",),
        ),
        assumption(
            "A-SPEC", "protocol-compiler/ass:spec", "specification_describes_apparatus",
            category="protocol-structure",
            title="The specification describes the apparatus",
            user_statement="Your declared tables are the ones performed.",
            affects=["secrecy", "correctness"], emitted_by=("protocol-compiler",),
            bindings=[{"name": "specification", "input": "specification",
                       "emitted_by": [{"module": "protocol-compiler",
                                       "station": None}]}],
        ),
        assumption(
            "A-ALICE-MEAS", "protocol-compiler/ass:alice-meas",
            "alice_measurement_untrusted",
            category="receiver", title="Alice's measurement as declared",
            user_statement="Alice measures as declared.", affects=["secrecy"],
            refines="A-SPEC", emitted_by=("protocol-compiler",),
        ),
        assumption(
            "A-SEQ", "transmitter/ass:seq", "sequential_round_model",
            category="protocol-structure", title="Sequential rounds",
            user_statement="No message before the round's measurements.",
            affects=["secrecy"],
            emitted_by=("transmitter", "reductions", "meat-core"),
            bindings=[_binding("rounds", 1_000_000_000)],
        ),
        # The decided row of the fixture, a PURELY SYNTHETIC SHAPE. No
        # assumption of the tree reads decided. The report still renders the
        # shape (its checks section), so the fixture keeps one row of it under
        # an id no claim file carries.
        assumption(
            "A-DECIDED", "meat-core/ass:decided", "decided_condition",
            category=None, title="A synthetic decided condition",
            verification="decided",
        ),
    ]


def _instance() -> dict[str, Any]:
    return {
        "id": "bb84",
        "title": "BB84 with a qubit channel",
        "summary": "The textbook BB84 protocol on a depolarising qubit channel.",
        "readme": "instances/bb84/README.md",
        "parameters": [
            {
                "name": "qber", "section": "model", "kind": "fraction",
                "quantity": "probability", "unit": None, "default": "1/50",
                "domain": {"form": "interval", "lower": "0", "upper": "1/2",
                           "lower_open": False, "upper_open": True},
                "snapped": False,
                "meaning": "The quantum bit error rate of the honest channel.",
                "per_port_labels": [], "applies_when": None, "station": None,
            },
            {
                "name": "basis_bias", "section": "device", "kind": "fraction",
                "quantity": "probability", "unit": None, "default": "1/2",
                "domain": {"form": "interval", "lower": "0", "upper": "1",
                           "lower_open": True, "upper_open": True},
                "snapped": True, "meaning": "The probability of the Z basis.",
                "per_port_labels": [], "applies_when": None, "station": None,
            },
        ],
    }


def _config(**parameters: Any) -> dict[str, Any]:
    base = {"alpha": 1.5, "eps_pa": 2.0**-30, "eps_ev": 2.0**-30, "lambda_ec": 0,
            "eps_auth": 0.0, "k_auth": 0}
    base.update(parameters)
    return {
        "rounds": 1_000_000_000,
        "completeness_budget": "1/1000000",
        "declared_tolerance": 0.0,
        "parameters": base,
        "model": {"qber": "1/50"},
        "device": {},
        "alpha": 1.5,
        "constrained": None,
        "solver": {"max_iterations": 20},
        "endpoint_rule": "exact",
        "tail_evaluation": "sweep",
        "config_digest": "0" * 64,
    }


def _flow() -> dict[str, Any]:
    return {
        "stages": [
            {"stage": "solve", "station": None, "module": "meat-core",
             "status": "executed",
             "emits": [{"id": "kr-1", "kind": "key_rate_result",
                        "digest": "b" * 64, "record_key": None}],
             "consumes": {"config": [], "artefacts": [], "artefact_kinds": []},
             "children": []},
        ],
        "mermaid": "flowchart LR",
    }


def completed_record(
    *,
    qber: str = "1/50",
    key_length: int | None = 12_345,
    net_key_length: int | None = 12_345,
    security_parameter: float | None = 2.0**-29,
    instance_id: str = "bb84",
    edit: Callable[[dict[str, Any]], None] | None = None,
    **parameters: Any,
) -> dict[str, Any]:
    """Return a completed first-order run record in the 0.21.0 shape."""
    config = _config(**parameters)
    config["model"] = {"qber": qber}
    values = config["parameters"]
    entries = [
        *_key_entries(values["eps_auth"], values["k_auth"], values["lambda_ec"]),
        *_common_entries(),
    ]
    instance = _instance()
    instance["id"] = instance_id
    record: dict[str, Any] = {
        "kind": "run-record",
        "schema_version": SUPPORTED_RECORD_SCHEMA_VERSION,
        "created_by": "tests.support.report_records",
        "payload": {
            "config": config,
            "refused": False,
            "contracts": {"meat-core": "3.0.0", "protocol-compiler": "2.0.0"},
            "instance": instance,
            "provenance": {"engine": {"distribution_version": "0.0.1.dev0",
                                      "git_commit": "a" * 40, "git_dirty": False}},
            # Record 0.21.0 writes it on every record, null off the document
            # route.
            "protocol_document": None,
            "honest_model_note": None,
            "assumption_manifest": {
                "roots": {"meat-core": ["meat-core/cor:keylength-bound"]},
                "claim_closure": {},
                "assumptions": entries,
                "not_engaged": [
                    {"short_id": "A-SRC", "module": "meat-core",
                     "reason": "trusted-source mode at d_A >= 2"},
                    {"short_id": "A-LINK", "module": "protocol-compiler",
                     "reason": "the identity link of Band A",
                     "discharged_by": "protocol-compiler/thm:band-a"},
                ],
                "discrepancies": [],
                "module_versions": {"statistics": "1.0.0"},
                "reported_tier": "first-order",
            },
            "stages": {
                "compilation": {"refused": False},
                "acceptance_construction": {
                    "refused": False,
                    "geometry": "PolytopeGeometry",
                    "completeness_certified": "1/1000000",
                    "outcomes": ["Z0", "Z1", "X0", "X1", "abort"],
                    "honest_distribution": {"Z0": "49/100", "Z1": "1/100"},
                },
                "key_rate": {
                    "alpha": 1.5,
                    "rounds": 1_000_000_000,
                    "key_length": key_length,
                    "net_key_length": net_key_length,
                    "security_parameter": security_parameter,
                    "reported_tier": "first-order",
                    "key_length_reason": "first_order_reported: computed from h_lb",
                    "rate_per_round": None if key_length is None
                    else key_length / 1_000_000_000,
                    "claim_roots": ["meat-core/cor:keylength-bound",
                                    "meat-core/frank-wolfe/thm:firstorder"],
                    "h_low": 0.75,
                    "h_lb": 0.7,
                    "first_order_minus_estimate": -0.05,
                    "frank_wolfe_gap": 1e-6,
                    "solver_status": "converged",
                    "iterations": 20,
                    "per_iterate": [{"withdrawal": None},
                                    {"withdrawal": "iterate_not_feasible"}],
                    "security_gates": {"key_length_permitted": True,
                                       "source_mode": "trusted",
                                       "accumulation_branch": "thm:c3"},
                    "tolerances": {"optimizer_gap": 1e-6},
                    "backend": {"python": "3.14", "oracle": "qics"},
                    "group_b_worst": {},
                    "solver_options": {"max_iterations": 20},
                },
                "receiver_construction": {
                    "route": "declared_finite_povm",
                    "receiver_route": "declared-finite-povm",
                    "modes": [],
                },
            },
            "compiled": {"public": {"choice_weightings": []}, "source": {}},
            "channel_interface": None,
            "snaps": {"declared_tolerance": 0.0, "instance": None, "producer": None,
                      "snap_max_defect": None, "snap_max_displacement": None},
            "composition_flow": _flow(),
        },
    }
    if edit is not None:
        edit(record)
    return copy.deepcopy(record)


def estimate_record() -> dict[str, Any]:
    """Return a completed run that reports no key length (estimate tier)."""

    def edit(record: dict[str, Any]) -> None:
        payload = record["payload"]
        key_rate = payload["stages"]["key_rate"]
        key_rate.update(
            key_length=None, net_key_length=None, security_parameter=None,
            reported_tier="estimate", rate_per_round=None,
            claim_roots=["meat-core/lem:estimate"],
            key_length_reason="iterate_not_feasible: no h_lb",
            per_iterate=[{"withdrawal": "iterate_not_feasible"}],
        )
        del key_rate["h_lb"]
        manifest = payload["assumption_manifest"]
        manifest["reported_tier"] = "estimate"
        manifest["assumptions"] = [
            entry for entry in manifest["assumptions"]
            if entry["short_id"] not in ("A-AUTH", "A-KEYREG", "A-CONFORM", "A-LMO")
        ]

    return completed_record(edit=edit)


def refused_record(
    stage: str = "solve",
    reason: str = "security_statement_vacuous",
    **parameters: Any,
) -> dict[str, Any]:
    """Return a refused run record: the refusing stage and its module's code."""
    return {
        "kind": "run-record",
        "schema_version": SUPPORTED_RECORD_SCHEMA_VERSION,
        "created_by": "tests.support.report_records",
        "payload": {
            "config": _config(**parameters),
            "refused": True,
            "contracts": {},
            "instance": _instance(),
            "provenance": {"engine": None},
            "protocol_document": None,
            "stages": {stage: {"refused": True, "reason": reason,
                               "detail": "a detail the module wrote"}},
            "composition_flow": {"stages": [], "mermaid": ""},
        },
    }


# --------------------------------------------------------------------------
# A measurement snap in the record 0.28.0 shape (instances/common/declare.py,
# runs/direct_route.py): blocks kept or moved, the run's decision on each.
# --------------------------------------------------------------------------

#: The fix the last-resort group names in these records (written by hand: the
#: report reads the record's words and never recomputes them).
LAST_RESORT_FIX = "a model that includes the noise your device has"


def _handed(
    kind: str, radius: str = "0", input_radius: str | None = None
) -> dict[str, Any]:
    return {"kind": kind, "largest_radius": radius, "input_radius": input_radius}


def snap_block(name: str, **fields: Any) -> dict[str, Any]:
    """Return a block record: by default kept, snapped from an exact reference."""
    block: dict[str, Any] = {
        "block": name, "status": "kept", "reference_kind": "exact",
        "handed_reference": _handed("exact"), "handed_reference_kind": "exact",
        "cause": None, "group": None, "fix": None, "group_fix": None,
        "receiver_fix": None, "steps": [], "lift_weight": None,
        "support_not_preserved": False, "rests_on_assumption": False,
        "evaluated_off_snap": False, "displacement": 0.0,
        "displacement_squared": "0", "defects_ground": "reference",
        "pre_snap": {}, "residue_placement": [],
    }
    block.update(fields)
    return block


#: m=0 kept; m=1 moved from the floating-point blocks, its enclosure handed,
#: evaluated off its snap; m=2 moved by the last resort with no reference,
#: resting on A-SNAP in the group 'last resort'.
SNAP_BLOCKS: tuple[dict[str, Any], ...] = (
    snap_block("m=0"),
    snap_block(
        "m=1",
        status="moved",
        reference_kind="none",
        handed_reference=_handed(
            "enclosed",
            "1/1000000000000000000000000000000000000",
            "1/100000000000000000000000000000000000000",
        ),
        handed_reference_kind="enclosed",
        evaluated_off_snap=True,
        displacement=1e-13,
    ),
    snap_block(
        "m=2",
        status="moved",
        reference_kind="none",
        handed_reference=None,
        handed_reference_kind=None,
        cause="no_reference",
        group="last_resort",
        fix="declare a receiver model",
        group_fix=LAST_RESORT_FIX,
        receiver_fix="declare the loss and dark counts each port has",
        support_not_preserved=True,
        rests_on_assumption=True,
        displacement=2e-13,
    ),
)

#: The manifest entry of A-SNAP, as a run that rests on it lists it.
A_SNAP_ENTRY: dict[str, Any] = {
    "short_id": "A-SNAP", "section": "assumptions",
    "machine_key": "snapped_measurement",
    "owner": "foundations/ass:snapped-measurement",
    "verification": "never",
    "verification_sentence": "The engine does not verify this.",
    "title": "The device measures the snapped family",
    "summary": "On every moved block the run does not evaluate off its snap ...",
    "user_statement": None, "category": "receiver",
    "affects": None, "refines": None, "status": "draft",
    "effective_status": "draft",
    "contract": {"pdf": "spec/modules/foundations/contract.pdf",
                 "anchor": "claim-foundations/ass:snapped-measurement"},
    "emitted_by": [{"module": "reductions", "station": None,
                    "machine_key": "snapped_measurement",
                    "inherited_from": None}],
    "bindings": [],
}


def with_snaps(
    record: dict[str, Any],
    blocks: list[dict[str, Any]],
    *,
    enclosure: bool = True,
    strict: bool = False,
) -> None:
    """Write one receiver snap of ``blocks`` and the two run settings."""
    payload = record["payload"]
    payload["config"]["parameters"].update(
        reference_enclosure=enclosure, strict_snaps=strict
    )
    settings = {"reference_enclosure": enclosure, "strict_snaps": strict}
    payload["snaps"]["instance"] = {
        "snap_settings": settings,
        "photon_blocks_form": "dark_composed",
        "measurement_snaps": [
            {
                "site": "receiver_photon_blocks",
                "setting": "off",
                "run_settings": settings,
                "cause": None,
                "reference": {
                    "offered": [
                        {"block": "m=0", "kind": "exact"},
                        {"block": "m=1", "kind": "enclosed"},
                    ],
                },
                "blocks": blocks,
            }
        ],
    }


def snapped_record(
    *,
    blocks: tuple[dict[str, Any], ...] = SNAP_BLOCKS,
    manifest_lists_a_snap: bool = True,
    emission_rests: bool = False,
) -> dict[str, Any]:
    """Return a completed run whose receiver was snapped (record 0.28.0).

    ``emission_rests`` adds a reduction whose normaliser moved a class at
    data sector 0, which the run did not evaluate off its snap.
    """

    def edit(record: dict[str, Any]) -> None:
        with_snaps(record, [dict(block) for block in blocks])
        payload = record["payload"]
        if manifest_lists_a_snap:
            payload["assumption_manifest"]["assumptions"].append(dict(A_SNAP_ENTRY))
        if emission_rests:
            payload["stages"]["reduction"] = {"refused": False}
            payload["snaps"]["producer"] = {
                "blocks": [
                    {
                        "block_index": 0,
                        "classes": [
                            {"class": "t0", "status": "moved",
                             "step": "snap_for_fidelity",
                             "support_not_preserved": False},
                        ],
                    }
                ]
            }

    return completed_record(edit=edit)


def as_first_order(record: dict[str, Any]) -> dict[str, Any]:
    """Return ``record`` read as a first-order run: its certified stage taken out.

    Every committed key-length example is reported at the certified tier,
    so the first-order
    readings of the report are tested on this edit of one: the tier, its
    reason code and the claim roots as a run with the evaluation off records
    them, and no ``certified`` stage. The record is edited in place.
    """
    key_rate = record["payload"]["stages"]["key_rate"]
    key_rate["reported_tier"] = "first-order"
    key_rate["key_length_reason_code"] = "first_order_reported"
    key_rate.pop("certified", None)
    key_rate["claim_roots"] = [
        root for root in key_rate["claim_roots"] if "certified" not in root
    ]
    return record
