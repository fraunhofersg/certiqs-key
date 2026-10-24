"""A Band-A protocol document lowers to what the modules are given.

THE PERMANENT EQUIVALENCE. ``instances/bb84/specification.py`` is the
protocol compiler's worked declaration (PC12, ``ex:conj``). The bb84 document's lowered
specification is held EQUAL to ``bb84_specification(...)`` at the registry weightings,
and its preparation record equal to the REFERENCE PREPARATION (wall times and the
``protocol_document`` key aside) at the defaults, every preset and a few edits: the
preparation rebuilt here from ``bb84_specification``, the library's
``depolarized_bell_pair`` model and the ``qubit_identity`` channel builder, through the
run tier's ``prepare`` -- so that the comparison keeps a reference that is not the
document itself. The one intended difference is named: at the registry's 0.9/0.1 case
the document routes the source through the transmitter, which refuses it
(``source_refused``) where the hand-built artefact reaches the compiler's
``choice_weights_not_normalized``.

THE COVERAGE DOCUMENTS. Each custom document exercises one
lowering the qubit instance does not. The test asserts only that the ENGINE
decides each one -- a preparation, a module's refusal as data, a transmitter
refusal surfaced as ``source_refused``, or a module's own
``MalformedInputError`` for an input it does not type -- and never that the
lowering fails with an exception of its own.

Also here: the document-layer refusals the lowering adds (Q9's licence rule,
a topology Band A has no route for, the wrapped arithmetic of an honest model) and
the expansion and user-declared record.
"""

from __future__ import annotations

import copy
import traceback
from dataclasses import replace
from fractions import Fraction as F
from typing import Any

import pytest
from instances.bb84.specification import bb84_specification
from instances.declared import DocumentError, DocumentReason
from instances.declared.lowering import lower
from tests.support.declared_documents import (
    COVERAGE,
    bb84_surface,
    coverage_surface,
    custom,
    declaring_everything,
)

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.errors import RunInputError
from certiqs_key.runs.pipeline import Preparation, PreparationOutcome, SliceRefusal
from certiqs_key.runs.record import preparation_record
from certiqs_key.transmitter.artifact import SourceSpecification, emit_artifact
from certiqs_key.transmitter.reasons import SourceMode

HALF = F(1, 2)


def _strip(value: Any) -> Any:
    """Drop every ``wall_time_s``, at any depth: the wall clock is not compared."""
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k != "wall_time_s"}
    if isinstance(value, list):
        return [_strip(item) for item in value]
    return value


def _weights(config: Any) -> tuple[F, F, F, F]:
    device = config.device
    return (device["alice_z"], device["alice_x"], device["bob_z"], device["bob_x"])


#: bb84's four basis weights, its numeric device fields.
_WEIGHTS = ("alice_z", "alice_x", "bob_z", "bob_x")


def _reference_config(**overrides: Any) -> RunConfig:
    """Return the bb84 reference ``default_config``, written out.

    The run fields, the table defaults and ``declared_tolerance = 0.0`` (no
    float-evaluated device data on the Band-A route); every override replaces
    its field.
    """
    base: dict[str, Any] = {
        "rounds": 10_000,
        "completeness_budget": F(1, 1_000_000),
        "parameters": KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        "declared_tolerance": 0.0,
        "model": {"qber": F(0)},
        "device": dict.fromkeys(_WEIGHTS, HALF),
    }
    return RunConfig.from_inputs(
        numeric_device_fields=_WEIGHTS, **{**base, **overrides}
    )


def _reference_context() -> Any:
    """Return the structure the library model is told: bb84's, fixed by code."""
    from instances.common.honest import HonestContext, SourceFacts, StationFacts
    from instances.common.sources import SIGNAL_ALPHABET

    return HonestContext(
        instance="bb84",
        stations=(
            StationFacts(id="bob", party="B", kind="declared_povm", dimension=2),
        ),
        source=SourceFacts(kind="trusted", alice_dim=2, alphabet=SIGNAL_ALPHABET),
    )


def _reference_preparation(config: RunConfig) -> PreparationOutcome:
    """Return the bb84 reference preparation, rebuilt from the library.

    Its weights snapped onto ``2^-40`` as two probability families, its
    specification ``bb84_specification(...)``, its raw table the library's
    ``depolarized_bell_pair`` at ``qber`` and its channel interface
    ``qubit_identity``, through the run tier's ``prepare``.
    """
    from instances.common.channel import qubit_identity
    from instances.common.honest.depolarized_bell_pair import MODEL

    from certiqs_key.runs.inputs import (
        attach_input_preparation,
        prepare_config_probabilities,
    )
    from certiqs_key.runs.pipeline import prepare

    config = prepare_config_probabilities(
        config,
        (("alice_z", "alice_x"), ("bob_z", "bob_x")),
        lattice_exponent=40,
        numeric_device_fields=_WEIGHTS,
    )
    context = _reference_context()
    MODEL.preconditions(context)
    _honest, raw = MODEL.providers({"qber": config.model["qber"]}, context)
    outcome = prepare(
        config,
        specification=bb84_specification(*_weights(config)),
        raw_joint_provider=raw,
        channel_interface_provider=qubit_identity,
    )
    return attach_input_preparation(outcome, config)


# ===========================================================================
#  1. The permanent bb84 equivalence
# ===========================================================================

#: The grid: the defaults, every preset, and edits (non-dyadic weights that
#: snap, a channel parameter, a decimal written as text).
_EDITS: tuple[dict[str, Any], ...] = (
    {"model": {"qber": F(1, 50)}},
    {
        "model": {"qber": F(0)},
        "device": {
            "alice_z": F(9, 10),
            "alice_x": F(1, 10),
            "bob_z": F(4, 5),
            "bob_x": F(1, 5),
        },
    },
    {
        "model": {"qber": "0.03"},
        "device": {
            "alice_z": "0.7",
            "alice_x": "0.3",
            "bob_z": F(1, 3),
            "bob_x": F(2, 3),
        },
    },
)


def _grid() -> list[tuple[str, dict[str, Any]]]:
    defaults = bb84_surface().default_config()
    grid: list[tuple[str, dict[str, Any]]] = [("defaults", {})]
    grid += [
        (
            preset.name,
            {"model": dict(defaults.model), "device": dict(preset.device)},
        )
        for preset in bb84_surface().PRESETS
    ]
    grid += [(f"edit-{index}", edit) for index, edit in enumerate(_EDITS)]
    return grid


@pytest.mark.parametrize(("name", "overrides"), _grid(), ids=[n for n, _ in _grid()])
def test_the_lowered_specification_is_bb84_specification(
    name: str, overrides: dict[str, Any]
) -> None:
    """At every registry weighting and edit, the same object as the constructor."""
    document = bb84_surface()
    config = document.default_config(**copy.deepcopy(overrides))
    prepared, lowered = document._read(config)
    assert lowered.specification == bb84_specification(*_weights(prepared))


@pytest.mark.parametrize(("name", "overrides"), _grid(), ids=[n for n, _ in _grid()])
def test_the_preparation_record_is_the_reference_preparation_s(
    name: str, overrides: dict[str, Any]
) -> None:
    """Equal except ``protocol_document`` and wall times."""
    document = bb84_surface()
    ours = document.preparation(document.default_config(**copy.deepcopy(overrides)))
    theirs = _reference_preparation(_reference_config(**copy.deepcopy(overrides)))
    assert isinstance(ours, Preparation) and isinstance(theirs, Preparation)
    left, right = preparation_record(ours), preparation_record(theirs)
    assert left.pop("protocol_document") is not None
    assert right.pop("protocol_document") is None
    assert _strip(left) == _strip(right)


def test_the_configuration_and_the_honest_note_are_the_reference_s() -> None:
    """The Python instance's configuration, note and channel builder, written out."""
    from instances.common.channel import qubit_identity
    from instances.common.honest.depolarized_bell_pair import MODEL

    document = bb84_surface()
    assert document.default_config().to_payload() == _reference_config().to_payload()
    assert MODEL.note({}, _reference_context()) == document.DEFAULT_HONEST_MODEL_NOTE
    assert document.channel_interface is qubit_identity


def test_a_configuration_refusal_is_the_run_tier_s_own() -> None:
    """The run tier's own refusal, with its own code, as the instance gave it.

    The Python instance refused a QBER outside its table's domain with the run
    tier's ``check_keys``; the document refuses it with the same check on the
    same table, so the reference is that check, called directly.
    """
    from certiqs_key.runs.surface import Section, check_keys

    bad = {"model": {"qber": F(1, 2)}}
    with pytest.raises(RunInputError) as ours:
        bb84_surface().preparation(bb84_surface().default_config(**bad))
    with pytest.raises(RunInputError) as theirs:
        check_keys(
            Section.MODEL,
            bad["model"],
            bb84_surface().PARAMETERS,
            "bb84",
            complete_for=_reference_config(**bad),
        )
    assert type(ours.value) is type(theirs.value)
    assert ours.value.reason == theirs.value.reason


def test_the_registry_s_rounding_case_is_refused_by_the_transmitter() -> None:
    """The 0.9/0.1 case: the intended difference, named.

    Through the transmitter, Alice's completeness sum is decided first and
    rounds; the hand-built artefact skips that decision and reaches the
    compiler's weight-list refusal. Both refuse; the document's refusal carries
    the transmitter's own reason, which ``emit_artifact`` returns on the Python
    side's source specification too.
    """
    document = bb84_surface()
    base = document.default_config()
    z, x = F(0.9), F(0.1)
    config = replace(base, device={**base.device, "alice_z": z, "alice_x": x})
    with pytest.raises(DocumentError) as refused:
        lower(
            document._whole(),
            document._environment(config),
            record_label="bb84",
            document_id="bb84",
            declared_tolerance=0.0,
        )
    assert refused.value.reason is DocumentReason.SOURCE_REFUSED
    artifact = bb84_specification(z, x, HALF, HALF).source.artifact
    licence = artifact.source_replacement_license
    assert licence is not None and licence.certificate is not None
    python_side = emit_artifact(
        SourceSpecification(
            signal_alphabet=artifact.signal_alphabet,
            transmitted_dim=2,
            signal_weights=dict(artifact.virtual_ensemble_weights),
            signal_states=dict(artifact.virtual_ensemble_states),
            alice_dim=artifact.alice_dim,
            alice_povm=dict(artifact.alice_povm),
            source_mode_request=SourceMode.TRUSTED,
            alice_marginal=artifact.alice_marginal,
            certificate=licence.certificate,
        )
    )
    assert python_side.refusal is not None
    assert refused.value.module_reason == str(python_side.refusal.reason)


def test_the_expansion_is_recorded_row_for_row() -> None:
    """What was handed to PublicPart, with the rule that fired."""
    document = bb84_surface()
    outcome = document.preparation(document.default_config())
    record = outcome.protocol_document
    assert record is not None
    assert record["id"] == "bb84" and record["packaged"] is True
    assert record["digest"] == document.digest
    expansion = record["expansion"]
    assert len(expansion["announce_alice"]["rows"]) == 4
    assert len(expansion["sifting"]["rows"]) == 9
    assert len(expansion["key"]["rows"]) == 36
    assert ["(X,1)", "(X,1)", "ok", 1] in expansion["acceptance"]["rows"]
    assert all(rows == [] for rows in record["unmatched"].values())
    public = outcome.specification.public
    assert {tuple(row[:2]): row[2] for row in expansion["sifting"]["rows"]} == {
        key: str(value) for key, value in public.sifting.items()
    }


# ===========================================================================
#  2. The coverage documents
# ===========================================================================


@pytest.mark.parametrize("name", sorted(COVERAGE))
def test_the_engine_decides_every_coverage_document(name: str) -> None:
    """Accepted, or refused by a module -- never an exception of the lowering."""
    surface = coverage_surface(name)
    try:
        outcome = surface.preparation(surface.default_config())
    except DocumentError as refusal:
        assert refusal.reason is DocumentReason.SOURCE_REFUSED, refusal
        assert refusal.module_reason
        return
    except MalformedInputError as failure:
        # A module's own hard error for an input it does not type, raised in
        # that module and not in the document layer.
        origin = traceback.extract_tb(failure.__traceback__)[-1].filename
        assert "certiqs_key" in origin and "instances" not in origin, origin
        return
    assert isinstance(outcome, Preparation | SliceRefusal)
    assert outcome.protocol_document is not None
    if isinstance(outcome, SliceRefusal):
        assert outcome.reason


def test_the_three_outcome_povm_document_is_refused_at_clause_iii() -> None:
    """A non-projective direct qubit POVM on the Band-A route.

    ``protocol-compiler/req:band-a-ideal-receiver`` (iii): the document's
    outcome is pinned to the clause, not to "some module refusal".
    """
    surface = coverage_surface("three_outcome_povm")
    outcome = surface.preparation(surface.default_config())
    assert isinstance(outcome, SliceRefusal)
    assert outcome.reason == "band_a_outside_ideal_receiver"
    assert "clause (iii)" in outcome.detail


def test_the_block_certificate_document_is_refused_at_row_3() -> None:
    """O-2 on the document route: a refusal record, not a hard error.

    The block form's licence record is present here, so (G2) refuses it by
    its declared form (protocol-compiler/def:eligible, "(G2) by form of the
    certificate"; thm:gates (ii'), Step 5), which the parametrised test above
    admits among other outcomes and this one pins.
    """
    surface = coverage_surface("block_certificate")
    outcome = surface.preparation(surface.default_config())
    assert isinstance(outcome, SliceRefusal)
    assert outcome.stage == "compilation"
    assert str(outcome.reason) == "gate_g2_failed"
    assert "BLOCK FORM" in str(outcome.detail)


def test_the_y_basis_document_compiles_with_its_complex_states() -> None:
    """The basis the qubit instance cannot show the conjugation convention on."""
    outcome = coverage_surface("y_basis").preparation(
        coverage_surface("y_basis").default_config()
    )
    assert isinstance(outcome, Preparation)
    assert outcome.specification.source.artifact.signal_alphabet == (
        "(Z,0)",
        "(Z,1)",
        "(Y,0)",
        "(Y,1)",
    )


def test_every_user_declared_kind_is_recorded_with_its_premise() -> None:
    surface = coverage_surface("explicit_entries_with_licence")
    outcome = surface.preparation(surface.default_config())
    assert outcome.protocol_document is not None
    items = outcome.protocol_document["user_declared"]
    assert {item["kind"]: item["assumptions"] for item in items} == {
        "retention_attestation": ["A-SRC"],
        "receiver_povm": ["A-SPEC", "A-IDEAL"],
        "constraint_entry": ["A-ATK"],
        "attack_set_license": ["A-ATK"],
        "feasibility_witness": [],
    }
    for item in items:
        assert item["text"].count("Declared in the run's protocol document") == 1
    (povm,) = [item for item in items if item["kind"] == "receiver_povm"]
    assert "A-IDEAL" in povm["text"]
    licence = outcome.specification.constraints.attack_set_license
    assert licence is not None
    assert licence.supplier == "user-declared:coverage_explicit_entries_with_licence"


# ===========================================================================
#  3. The document-layer refusals of the lowering
# ===========================================================================


def test_entries_without_a_licence_are_refused() -> None:
    """The record would credit the entries to nobody's licence."""

    def edit(tree: dict[str, Any]) -> None:
        declaring_everything(tree)
        del tree["constraints"]["attack_set_license"]

    surface = custom(edit, "entries_alone")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config())
    assert refused.value.reason is DocumentReason.USER_ENTRIES_WITHOUT_LICENCE
    assert refused.value.path == "/constraints/entries"


@pytest.mark.parametrize(
    ("edit", "path"),
    [
        (lambda tree: tree["public"].update(partition="factor_projection"), None),
        (
            lambda tree: tree["channel_interface"].update(variant="single_photon"),
            "/channel_interface/variant",
        ),
    ],
    ids=["factor-projection", "optical-channel-interface"],
)
def test_a_topology_band_a_has_no_route_for_is_refused(edit: Any, path: Any) -> None:
    """One Band-A station: no factor projection, no optical channel interface.

    Several stations are lowered, so a second Band-A station is not refused
    here: it is a coverage document
    (``tests/unit/test_declared_lowering_optical.py``).
    """
    try:
        surface = custom(edit, "later")
    except DocumentError as refused:  # the static topology check may come first
        assert refused.reason is DocumentReason.UNSUPPORTED_TOPOLOGY
        return
    with pytest.raises(DocumentError) as refused_late:
        surface.preparation(surface.default_config())
    assert refused_late.value.reason is DocumentReason.UNSUPPORTED_TOPOLOGY
    if path is not None:
        assert refused_late.value.path == path


def test_a_declared_povm_station_takes_the_identity_link_only() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["stations"][0]["reduction"] = {"links": [{"kind": "fss"}]}

    surface = custom(edit, "not_identity")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config())
    assert refused.value.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("route", "licensed"),
        ("squash_before_post_processing", True),
        ("declared_sector_order", ["s0"]),
        ("lattice_exponent", 30),
        ("carried_operators", [{"library": "two_sector_floor"}]),
    ],
)
def test_no_reduction_field_of_a_declared_povm_station_is_dropped(
    field: str, value: Any
) -> None:
    """A field with no effect on Band A is refused, with its path."""

    def edit(tree: dict[str, Any]) -> None:
        tree["stations"][0]["reduction"][field] = value

    surface = custom(edit, "reduction_field")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config())
    assert refused.value.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION
    assert refused.value.path == f"/stations/0/reduction/{field}"


def test_a_switch_resolving_to_no_carried_operators_is_the_default() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["stations"][0]["reduction"]["carried_operators"] = {
            "switch": "acceptance_map",
            "cases": {"resolved": [], "merged": []},
        }
        tree["parameters"]["table"].append(
            {
                "name": "acceptance_map",
                "section": "device",
                "kind": "choice",
                "quantity": "choice",
                "default": "resolved",
                "domain": {
                    "form": "choices",
                    "options": [
                        {"value": "resolved", "meaning": "one"},
                        {"value": "merged", "meaning": "two"},
                    ],
                },
                "snapped": False,
                "meaning": "a choice that switches nothing here",
            }
        )

    surface = custom(edit, "switched_operators")
    assert isinstance(surface.preparation(surface.default_config()), Preparation)


def test_party_local_view_is_refused_on_band_a() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["constraints"] = {"party_local_view": "operator"}

    surface = custom(edit, "party_local_view")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config())
    assert refused.value.path == "/constraints/party_local_view"


def test_the_document_s_note_is_nested_and_cannot_rewrite_the_model_s() -> None:
    """The report prints this note; a document may not forge it."""

    def edit(tree: dict[str, Any]) -> None:
        tree["honest"]["note"] = {"model": "forged", "overridden": True, "lab": "x"}

    surface = custom(edit, "forged_note")
    note = surface.DEFAULT_HONEST_MODEL_NOTE
    assert note["model"].startswith("depolarizing qubit channel")
    assert note["overridden"] is False
    assert note["document"] == {"model": "forged", "overridden": True, "lab": "x"}


def test_a_negative_raw_table_entry_is_refused() -> None:
    """A raw table whose negatives cancel would aggregate to a law."""

    def edit(tree: dict[str, Any]) -> None:
        tree["honest"] = {
            "raw_table": {"(Z,0)|(Z,0)": "-1", "(Z,1)|(Z,1)": "2"},
            "source": "a table with a negative entry",
        }

    surface = custom(edit, "negative_raw")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config())
    assert refused.value.reason is DocumentReason.HONEST_TABLE_INVALID
    assert refused.value.path == "/honest/raw_table/(Z,0)|(Z,0)"


def test_the_surface_attributes_never_raise() -> None:
    """They are read on any document; a refusal is preparation's to report."""
    from instances.common.channel import single_photon

    def edit(tree: dict[str, Any]) -> None:
        tree["channel_interface"] = {"variant": "single_photon"}

    surface = custom(edit, "attributes")
    assert surface.channel_interface is single_photon
    note = surface.DEFAULT_HONEST_MODEL_NOTE
    assert note["not_built"] == "unsupported_topology"
    assert note["overridden"] is False


def test_a_choice_parameter_binds_its_value() -> None:
    """A ``{param}`` of a choice parameter binds the choice a model may take."""
    from instances.declared.lowering import _Lowering
    from instances.declared.model import ParamRef
    from instances.declared.values import Environment

    from certiqs_key.runs.surface import Kind

    surface = custom(lambda tree: None, "choice_bind")
    lowering = _Lowering(
        surface._whole(),
        Environment(
            {"source_model": Kind.CHOICE, "q": Kind.FRACTION},
            {"source_model": "spdc", "q": F(1, 3)},
        ),
        record_label="declared.choice_bind",
        document_id="choice_bind",
        declared_tolerance=0.0,
    )
    assert lowering._bound(ParamRef(param="source_model"), "/b") == "spdc"
    assert lowering._bound(ParamRef(param="q"), "/b") == F(1, 3)


def test_a_key_value_that_is_not_an_integer_is_refused() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["public"]["key"]["rule"] = [{"value": "{o.bit}"}]

    surface = custom(edit, "string_key")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config())
    assert refused.value.reason is DocumentReason.RULE_VALUE_INVALID


def test_an_honest_model_s_arithmetic_failure_is_a_coded_refusal() -> None:
    """The one wrapped call site of the library."""
    from instances.declared.lowering.honest import _guarded

    def failing(declaration: object) -> dict[str, F]:
        raise ZeroDivisionError("a model divided by zero")

    with pytest.raises(DocumentError) as refused:
        _guarded(failing)(None)
    assert refused.value.reason is DocumentReason.HONEST_MODEL_FAILED


def test_a_raw_table_is_split_at_its_declared_labels() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["honest"] = {
            "raw_table": {"(Z,0)|(Z,0)": "1/2", "(Z,1)|(Z,1)": "1/2"},
            "source": "a perfectly correlated Z table",
        }

    surface = custom(edit, "raw_table")
    outcome = surface.preparation(surface.default_config())
    assert isinstance(outcome, Preparation)
    assert outcome.raw_joint_distribution == {
        ("(Z,0)", "(Z,0)"): HALF,
        ("(Z,1)", "(Z,1)"): HALF,
    }

    def unsplittable(tree: dict[str, Any]) -> None:
        edit(tree)
        tree["honest"]["raw_table"] = {"(Z,0)(Z,0)": "1"}

    surface = custom(unsplittable, "raw_table_bad")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config())
    assert refused.value.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION


def test_a_static_fragment_has_nothing_to_prepare() -> None:
    from instances.declared import load_packaged
    from tests.support.declared_documents import BB84_DOCUMENT

    fragment = load_packaged(BB84_DOCUMENT, static=True)
    with pytest.raises(DocumentError):
        fragment.preparation(fragment.default_config())
