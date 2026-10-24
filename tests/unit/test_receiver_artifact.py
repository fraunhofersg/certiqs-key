"""The emitted artifact is documented, serializable, and carries nothing twice.

Structural tests of the wire form decided in
:mod:`certiqs_key.receiver.artifact`. A key-rate run has to be able to LOG the
artifact, so the payload must survive a JSON round trip with nothing lost and
nothing invented; and the outputs table's fifteen keys must be fifteen, with the
one conditional key conditional and no sixteenth.

WHAT "NOTHING TWICE" MEANS HERE. The port map lives only inside
``receiver_construction``; the Grams only under ``port_grams``; the per-setting
WEIGHT only under ``high_photon_bounds`` and the per-setting BRANCH record only
under ``bound_quantifier_domain``; the dark-count matrix stores only the
non-zero entries (D2) leaves. The tests below walk the payload and check each of
those, because a duplicated datum is the way two copies of one fact drift apart.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import replace

import pytest
from probe_presence import requires_probe, with_probe
from receiver_povm_support import (
    bb84_channel_only_request,
    probe_free_matrix_request,
    probe_receiver_request,
)

from certiqs_key.receiver import (
    OUTPUT_KEYS,
    GramFamily,
    ProbeDeclaration,
    ProbeSetting,
    ReceiverRequest,
    construct_receiver,
)
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.receiver.reasons import AssumptionId, RefusalReason

_JSON_TYPES = (str, int, float, bool, type(None))

#: The route-(ii) receivers: the probe-free one in every tree, the probe
#: receiver where the removable probe-conditioning submodule is present.
MATRIX_REQUESTS = (probe_free_matrix_request, *with_probe(probe_receiver_request))


def _artifact(request: ReceiverRequest) -> ReceiverMeasurementArtifact:
    """Return the emitted artifact, asserting the emission did not refuse."""
    emission = construct_receiver(request)
    assert emission.refusal is None, emission.refusal
    assert emission.artifact is not None
    return emission.artifact


def _route_one_request(
    build: Callable[[], ReceiverRequest] = probe_free_matrix_request,
) -> ReceiverRequest:
    """Return a route-(ii) fixture's receiver as a route-(i) declaration.

    The Grams the instrument matrix realizes, supplied directly: the same
    receiver on the route that declares neither a graph nor a Gamma. The
    construction is the golden artifact test's and is repeated here rather than
    imported, so that this file's cases stand on their own.
    """
    supplied = _artifact(build())
    family = GramFamily(
        tuple(label for label, _ in supplied.port_grams),
        tuple(matrix for _, matrix in supplied.port_grams),
    )
    return replace(build(), instrument_matrix=None, port_grams=family)


def _walk(value: object, path: str = "") -> Iterator[tuple[str, object]]:
    """Yield every ``(path, value)`` pair of a payload, depth first."""
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


@pytest.mark.contract
def test_the_payload_round_trips_through_json_unchanged() -> None:
    """A key-rate run must be able to log the artifact and read it back."""
    for build in (bb84_channel_only_request, *MATRIX_REQUESTS):
        payload = _artifact(build()).as_payload()
        text = json.dumps(payload, sort_keys=True)
        assert json.loads(text) == payload
        # Every leaf is a JSON-native scalar -- no NumPy scalar, no complex, no
        # Fraction, no enum object survives into the payload.
        for path, value in _walk(payload):
            if isinstance(value, dict | list):
                continue
            assert isinstance(value, _JSON_TYPES), (path, type(value))


@pytest.mark.contract
def test_the_payload_keys_are_the_fifteen_with_one_conditional() -> None:
    """The outputs table and ``artifact_bindings.produces_note``: no sixteenth key."""
    compiled = _artifact(bb84_channel_only_request())
    assert tuple(compiled.as_payload()) == OUTPUT_KEYS
    for build in MATRIX_REQUESTS:
        supplied = _artifact(build())
        assert tuple(supplied.as_payload()) == tuple(
            key for key in OUTPUT_KEYS if key != "receiver_construction"
        )
        assert set(compiled.as_payload()) - set(supplied.as_payload()) == {
            "receiver_construction"
        }
        # No sixteenth key on any route.
        for artifact in (compiled, supplied):
            assert set(artifact.as_payload()) <= set(OUTPUT_KEYS)


@pytest.mark.contract
def test_nothing_in_the_payload_appears_twice() -> None:
    """The wire-form rule that keeps two copies of one fact from drifting apart."""
    payload = _artifact(bb84_channel_only_request()).as_payload()
    paths = [path for path, _ in _walk(payload)]
    # The port map is carried ONLY inside receiver_construction.
    port_map_paths = [p for p in paths if p.endswith("port_map")]
    assert port_map_paths == ["receiver_construction.port_map"]
    # The Grams only under port_grams.
    gram_paths = {p.split("[")[0] for p in paths if p.endswith("gram")}
    assert gram_paths == {"port_grams"}
    # The per-setting weight only under high_photon_bounds, the per-setting
    # branch record only under bound_quantifier_domain. The
    # per-setting weights are INSIDE the slot entry, whose guaranteed content
    # they are (def:slot), with no entry-level list beside it, so the weights
    # are carried once, inside the entry with its uniform weight.
    weight_paths = {p.split("[")[0] for p in paths if p.endswith(".weight")}
    assert weight_paths == {"high_photon_bounds.entries"}
    assert not any(p.startswith("high_photon_bounds.per_setting") for p in paths)
    entry_weight_paths = {
        p for p in paths if p.startswith("high_photon_bounds.entries[0]")
    }
    assert "high_photon_bounds.entries[0].weight" in entry_weight_paths
    assert any(".per_setting[" in p for p in entry_weight_paths)
    branch_paths = {p.split("[")[0] for p in paths if p.endswith(".branch")}
    assert branch_paths == {"bound_quantifier_domain.per_setting"}
    # The probe alphabet is echoed once, as the outputs table asks of
    # `bound_quantifier_domain`; the second moments live in the ledger row of
    # the assumption that constrains them and in the reproducible construction.
    assert payload["bound_quantifier_domain"]["probe_alphabet"] == ["off"]  # type: ignore[index]


@pytest.mark.contract
def test_every_index_in_the_payload_is_a_declared_label() -> None:
    """Wire-form rule 1: labels, never positions, so a payload reads on its own."""
    payload = _artifact(bb84_channel_only_request()).as_payload()
    grams = payload["port_grams"]
    assert isinstance(grams, list)
    assert [row["port"] for row in grams] == ["H", "V", "+", "-"]
    alphabet = payload["outcome_alphabet"]
    assert isinstance(alphabet, dict)
    fibres = alphabet["coarse_graining"]
    assert isinstance(fibres, list)
    # Click patterns are sorted tuples of PORT LABELS, not port indices.
    multiclick = next(row for row in fibres if row["letter"] == "mc")
    assert all(
        all(isinstance(port, str) for port in pattern)
        for pattern in multiclick["fibre"]
    )
    assert ["H", "V"] in multiclick["fibre"]
    construction = payload["receiver_construction"]
    assert isinstance(construction, dict)
    supports = [element["support"] for element in construction["elements"]]
    assert all(isinstance(mode, str) for support in supports for mode in support)
    assert ["Led_H", "Led_V"] in supports


@pytest.mark.contract
def test_a_complex_entry_survives_as_a_pair_and_the_phase_is_not_dropped() -> None:
    """Wire-form rule 2, and the `waveplate_convention` end to end."""
    for build in MATRIX_REQUESTS:
        payload = _artifact(build()).as_payload()
        grams = payload["port_grams"]
        assert isinstance(grams, list)
        for row in grams:
            for line in row["gram"]:
                for entry in line:
                    assert isinstance(entry, list) and len(entry) == 2
                    assert all(isinstance(part, float) for part in entry)
    # The route-(iii) receiver carries the retarder's physical phase e^{-i pi/2}
    # in its declared parameters. The half-wave preset declares its retardance
    # as pi EXACTLY, in presentation (b) of `parameters.units` (an angle as a
    # rational coefficient of pi), and the payload carries the coefficient,
    # which is the declared datum (`presentation_rule`).
    construction = _artifact(bb84_channel_only_request()).as_payload()[
        "receiver_construction"
    ]
    assert isinstance(construction, dict)
    hwp = next(e for e in construction["elements"] if e["name"] == "hwp")
    assert hwp["entry_id"] == "C3"
    assert hwp["parameters"]["retardance"] == {"pi_coefficient": "1"}


@pytest.mark.contract
def test_the_dark_count_record_stores_only_its_non_zero_entries() -> None:
    """Wire-form rule 3 with Definition def:darkadm (D2)."""
    for build in MATRIX_REQUESTS:
        artifact = _artifact(build())
        payload = artifact.as_payload()["dark_count_channel"]
        assert isinstance(payload, dict)
        assert payload["route"] == "per_port_product_form"
        assert payload["conditions_derived"] == ["D1", "D2"]
        assert payload["conditions_checked"] == []
        for column in payload["columns"]:
            for entry in column["entries"]:
                assert entry["probability"] > 0.0
                # (D2): a non-zero entry has the column as a SUBSET of the row.
                assert set(column["column"]) <= set(entry["row"])
        assert payload["r_min"] == pytest.approx(0.02)


@pytest.mark.contract
def test_the_assumption_ledger_is_one_row_per_file_with_their_declared_values() -> (
    None
):
    """``interface.yaml`` ``outputs.assumption_ledger``, and the never-verified set.

    One row per assumption file, every row on every artifact. The
    never-verified rows are the members of ``never_verified_set``: the
    assumptions whose ``verification`` header field is ``never``
    (spec/claim-format.md section 3.2; Remark ``rem:unchecked-assumptions``),
    A-EIG among them -- a statement about the ARITHMETIC, INVOKED ONLY WHERE A
    CALLER DECLARES AN EXACT-WINDOW DEPTH (Assumption ``ass:eig``).

    THIS DECLARATION CARRIES NO DEPTH, so the A-EIG row records that it was
    invoked NOWHERE and that no ``eps_eig`` was declared -- ``None``, not zero.
    The row still exists, because the outputs table asks for the machine keys
    of the assumption files, one row per file and every row on every artifact
    (``a_eig_row_note``).
    """
    payload = _artifact(bb84_channel_only_request()).as_payload()
    ledger = payload["assumption_ledger"]
    assert isinstance(ledger, list)
    assert [row["id"] for row in ledger] == [str(member) for member in AssumptionId]
    never = [row["id"] for row in ledger if row["never_verified"]]
    # TEN, in the ledger's order: A-TRUST, A-MODES, A-EIG, A-NOSEL, A-ROUND,
    # A-PASSIVE, A-VAC, A-THRESH, A-PORT and A-EXACT carry
    # `verification: never` (rem:unchecked-assumptions,
    # req:decidable-assumptions).
    assert never == [
        "A-TRUST",
        "A-PASSIVE",
        "A-VAC",
        "A-MODES",
        "A-THRESH",
        "A-PORT",
        "A-EXACT",
        "A-NOSEL",
        "A-ROUND",
        "A-EIG",
    ]
    rows = {row["id"]: row for row in ledger}
    # A-EIG on a declaration that requests NO exact window: not invoked, and
    # its declared parameter ABSENT rather than zero.
    assert rows["A-EIG"]["machine_key"] == "exact_window_eigenvalue_slack"
    assert rows["A-EIG"]["constrains"]["invoked_at"] == []
    assert rows["A-EIG"]["constrains"]["eps_eig"] is None
    assert rows["A-THRESH"]["constrains"]["tau"] == 0
    assert rows["A-VAC"]["constrains"]["undeclared_input_modes"] == [
        "Led_H",
        "Led_V",
        "X_H",
        "X_V",
        "Z_H",
        "Z_V",
    ]
    assert rows["A-EXACT"]["constrains"]["declared_tolerance_fields"] == []
    assert set(rows["A-PASSIVE"]["constrains"]["catalogue_entries"]) == {
        "C1",
        "C3",
        "C9",
    }


@pytest.mark.contract
def test_every_ledger_row_is_present_on_every_route_and_probe_alphabet() -> None:
    """``interface.yaml`` ``outputs.assumption_ledger``: no row is conditional.

    "One row per file and every row on every artifact": a probe-free
    element-graph receiver, an instrument-matrix receiver (probe-free, and
    probe-bearing where the probe-conditioning submodule is present) and the
    same receiver declared through its port Grams carry the same rows in the
    same order, each with the same four fields. The conditions the receiver
    decides on the declared data -- (E2) of ``def:graph`` and the
    occupation-diagonal probe states of ``def:probe`` -- have no row
    (``decided_conditions_note``), and neither has the evaluation model of
    ``def:evaluation-model``.
    """
    requests = {"element_graph": bb84_channel_only_request()}
    for build in MATRIX_REQUESTS:
        requests[f"instrument_matrix {build.__name__}"] = build()
        requests[f"port_grams {build.__name__}"] = _route_one_request(build)
    for route, request in requests.items():
        artifact = _artifact(request)
        payload = artifact.as_payload()
        ledger = payload["assumption_ledger"]
        assert isinstance(ledger, list)
        assert [row["id"] for row in ledger] == [str(i) for i in AssumptionId], route
        for row in ledger:
            assert set(row) == {"id", "machine_key", "never_verified", "constrains"}
        text = json.dumps(payload)
        for retired in (
            "acyclic_element_graph",
            "probe_fock_diagonal",
            "floating_point_evaluation",
            "declared_route",
        ):
            assert retired not in text, (route, retired)
    for build in (bb84_channel_only_request, probe_free_matrix_request):
        free = _artifact(build()).bound_quantifier_domain
        assert free.probe_alphabet == ("off",)


@pytest.mark.contract
@requires_probe
def test_a_probe_bearing_receiver_echoes_its_alphabet() -> None:
    """``bound_quantifier_domain.probe_alphabet``: every declared setting, in order."""
    probed = _artifact(probe_receiver_request()).bound_quantifier_domain
    assert probed.probe_alphabet == ("off", "on")


@pytest.mark.contract
def test_a_probe_alphabet_naming_one_label_twice_is_refused() -> None:
    """Def. def:probe: T is an alphabet, a SET of settings.

    A declaration with a source mode and two ``off`` settings, if accepted,
    would have a probe row emitted on it while the reductions side, reading the
    set, classified the artefact probe-free. It is refused before any artifact
    exists.
    """
    base = probe_receiver_request()
    for settings in (
        (ProbeSetting("off", (0,)), ProbeSetting("off", (0,))),
        (
            ProbeSetting("off", (0,)),
            ProbeSetting("on", (1,)),
            ProbeSetting("on", (2,)),
        ),
    ):
        emission = construct_receiver(
            replace(base, probe_declaration=ProbeDeclaration(settings))
        )
        assert emission.artifact is None
        assert emission.refusal is not None
        assert emission.refusal.reason is RefusalReason.PROBE_ALPHABET_LABEL_REPEATED


@pytest.mark.contract
def test_a_ledger_survives_the_json_round_trip_and_adds_no_key() -> None:
    """The ledger rows are wire-form data like every other field.

    They must survive ``json.dumps``/``loads`` unchanged (a run logs the
    artifact), and they may not widen the artifact's own key set: the outputs
    table's fifteen keys are fifteen, ``receiver_construction`` absent off
    route (iii).
    """
    requests = [
        request
        for build in MATRIX_REQUESTS
        for request in (build(), _route_one_request(build))
    ]
    for request in requests:
        payload = _artifact(request).as_payload()
        assert json.loads(json.dumps(payload, sort_keys=True)) == payload
        assert tuple(payload) == tuple(
            key for key in OUTPUT_KEYS if key != "receiver_construction"
        )


@pytest.mark.contract
def test_the_calibration_coverage_is_the_literal_statement() -> None:
    """`outputs.calibration_coverage` with Assumption ass:trust: never a verdict."""
    artifact = _artifact(bb84_channel_only_request())
    statement = artifact.calibration_coverage
    assert "trusted and exactly characterized" in statement
    assert "ass:trust" in statement
    assert "No characterization data, uncertainty set or device family" in statement
    # The same statement on every artifact, whatever the request said.
    for build in MATRIX_REQUESTS:
        other = _artifact(build())
        assert other.calibration_coverage == statement


@pytest.mark.contract
def test_the_emitted_efficiency_record_names_every_declared_transmittance() -> None:
    """Requirement req:efficiency-record, end to end on a compiled receiver."""
    request = replace(
        bb84_channel_only_request(),
    )
    artifact = _artifact(request)
    rows = artifact.efficiency_record.rows
    sites = [row.site for row in rows]
    assert sites.count("terminal factor D_eta") == 4
    assert any(site.startswith("chain position") for site in sites)
    # Two elements carrying equal numerical values are still two rows.
    equal = [row for row in rows if row.value == pytest.approx(1.0)]
    assert len(equal) == 4
    assert len({row.element for row in equal}) == 4
