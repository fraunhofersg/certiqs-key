"""Schema 0.2.0: the reduction chain on the wire, and the round trip that reads it.

The wire carries exactly one extension -- the identity link an
ideal-qubit protocol reduces by, "recorded in the bundle as an ``exact``
reduction" -- and this module is where that lands and comes back.

Two halves, deliberately separate.

* THE SLICE'S WRITER (:mod:`certiqs_key.runs.wire`): does the manifest it
  produces carry what the compiler emitted, re-keyed and otherwise untouched, and
  does ``meat-core`` read the same declaration back off the disk?
* THE FORMAT'S OWN VALIDATION (:mod:`certiqs_key.domain.validation`): is every
  shape condition spec/architecture.md 3.6 asks for a HARD ERROR, on a manifest
  built by hand to violate exactly one of them? A producer that happens not to
  emit a defect is no defence against a producer that does, which is the same
  argument the frozen entry ``O-POLYTOPE-EMPTY-FAIL-CLOSED`` makes.

The compatibility rule is tested in BOTH directions, because half of a
compatibility rule is a claim about the version you are not writing.
"""

from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from instances.bb84.specification import bb84_specification
from instances.common.honest.depolarized_bell_pair import (
    honest_distribution,
)

from certiqs_key.domain.bundle import (
    RETIRED_SCHEMA_VERSIONS,
    SUPPORTED_SCHEMA_VERSIONS,
    BundleValidationError,
    OperatorBundle,
    RetiredSchemaVersionError,
    parse_manifest,
    read_bundle,
    validate_bundle,
    write_bundle,
)
from certiqs_key.domain.manifest import SCHEMA_VERSION
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import (
    KeyLengthParameters,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.validation import validate_declaration
from certiqs_key.meat_core.docking import dock_declaration
from certiqs_key.meat_core.docking_statistics import acceptance_set_record
from certiqs_key.protocol_compiler import (
    CandidateDeclaration,
    CompilationResult,
    compile_specification,
)
from certiqs_key.runs.wire import build_bundle, bundle_documents
from certiqs_key.statistics import AcceptanceRequest, construct

# THE SNAP IS THE PRODUCER'S: ``meat-core``'s ``acceptance_data_exact`` row
# decides the declared acceptance data at EXACTLY 0, and a vector converted
# from exact rationals coordinate by coordinate sums to a hair away from one.
# The remedy is the PRODUCER'S -- "a producer emits exact rationals, or SNAPS
# AT THE INSTANCE before this module sees the data" -- and
# :func:`instances.bb84.declare.declare_acceptance_frequencies` is that snap.

#: The snap's two declared numbers, neither of which has a default anywhere on
#: this platform. ``kappa = 40`` is spec/architecture.md 2.9's measured value,
#: at which the per-coordinate displacement is at most ``2^-41 = 4.5e-13``;
#: ``tau = 0`` is what this slice declares everywhere else and the snap needs
#: no more of it, the lattice step not being decided by ``tau``.
SNAP_LATTICE_EXPONENT = 40
SNAP_TOLERANCE = 0.0

pytestmark = pytest.mark.contract

PARAMETERS = KeyLengthParameters(
    alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
)
ROUNDS = 400


def _compiled() -> CompilationResult:
    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.declaration is not None
    return result


def _docked(
    rounds: int = ROUNDS,
) -> tuple[CompilationResult, CandidateDeclaration, ProtocolDeclaration]:
    """Return ``(compilation, declaration, docked)`` on a REAL constructed polytope."""
    result = _compiled()
    declaration = result.declaration
    assert declaration is not None
    honest = honest_distribution(declaration, F(1, 20))
    construction = construct(
        AcceptanceRequest(
            alphabet=declaration.acceptance_alphabet,
            honest=honest,
            rounds=rounds,
            budget=F(1, 1000),
        )
    )
    assert construction.acceptance_set is not None
    docked = dock_declaration(
        declaration,
        acceptance_set=acceptance_set_record(construction.acceptance_set),
        rounds=rounds,
        parameters=PARAMETERS,
    )
    return result, declaration, docked


def _documents(**overrides: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    result, declaration, docked = _docked()
    manifest, arrays, _ = bundle_documents(
        docked,
        alice_announcements=declaration.alice_announcement_alphabet,
        bob_announcements=declaration.bob_announcement_alphabet,
        reduction_chain=result.reduction_chain_record,
        created_by="tests.unit.test_bb84_wire_bundle",
        **overrides,
    )
    return manifest, arrays


# ---------------------------------------------------------------------------
#  The slice's writer.
# ---------------------------------------------------------------------------


def test_the_bundle_is_stamped_at_the_version_its_own_payload_needs() -> None:
    """The slice's bundle is a 0.3.0 document, and 0.4.0's arrival did not move it.

    The stamp is the LOWEST version that can express the document
    (``domain/manifest.py``), so this declaration -- one ``Q`` factor, one
    undecomposed ``A``, no ``sector_factorisation`` -- is stamped 0.3.0 and
    writes the bytes it wrote before 0.4.0 existed. The reader accepts both live
    versions; the WRITER's stamp is decided by the payload.
    """
    manifest, _ = _documents()
    assert manifest["schema_version"] == SCHEMA_VERSION == "0.3.0"
    assert SUPPORTED_SCHEMA_VERSIONS == ("0.3.0", "0.4.0")
    assert "sector_factorisation" not in manifest["payload"]


def test_the_identity_link_travels_as_an_exact_reduction() -> None:
    """The identity link, read off the manifest.

    One receiver link, status ``exact``, an empty source segment PRESENT rather
    than absent, and both slots -- transported constraints and the licence --
    emitted although both are empty. That last part is Requirement
    ``req:chain-record-slots``: a record that omits an empty slot cannot later
    distinguish "no entries" from "entries not carried".
    """
    manifest, _ = _documents()
    chain = manifest["payload"]["reduction_chain"]
    assert chain["source_segment"] == []
    assert len(chain["receiver_segment"]) == 1
    (link,) = chain["receiver_segment"]
    assert link["status"] == "exact"
    assert link["segment"] == "receiver"
    assert link["link_id"] == "Lambda_1"
    assert link["channel_supplied"] is True
    assert link["transported_constraints"] == 0
    assert link["license_slot_present"] is True
    assert link["license_slot_empty"] is True
    assert link["source_descriptor"] == link["target_descriptor"]
    assert link["target_descriptor"]["dim"] == 2
    assert link["target_descriptor"]["sectors"] == [["s0", 2]]


def test_the_outcome_correspondence_is_the_identity_on_the_emitted_alphabet() -> None:
    """(C2) at its special case, re-keyed by the same bijection as every table."""
    manifest, _ = _documents()
    payload = manifest["payload"]
    pairs = payload["reduction_chain"]["outcome_correspondence"]
    assert [physical for physical, _ in pairs] == list(
        payload["declaration"]["bob_povm"]
    )
    assert all(physical == emitted for physical, emitted in pairs)


def test_the_chain_record_is_the_compilers_own_keys() -> None:
    """This module adds no field the compiler did not emit, and drops none.

    Compared key for key against ``CompilationResult.reduction_chain_record``,
    so that a slot the compiler starts emitting shows up here as a failure rather
    than as a slot that quietly never reached the wire.
    """
    result, _, _ = _docked()
    emitted = result.reduction_chain_record
    manifest, _ = _documents()
    wire = manifest["payload"]["reduction_chain"]
    assert set(wire) == set(emitted)
    assert set(wire["receiver_segment"][0]) == set(
        emitted["receiver_segment"][0]  # type: ignore[index]
    )


@pytest.mark.smoke
def test_the_bundle_round_trips_and_meat_core_reads_the_same_declaration(
    tmp_path: Path,
) -> None:
    """Write, read, validate, and compare the numbers on both sides.

    The comparison goes through the label bijection rather than by key, because
    the wire carries stable IDs and the compiler carries its own presentation
    labels -- which is the whole point of
    :mod:`certiqs_key.runs.identifiers`.
    """
    result, declaration, docked = _docked()
    bundle, labels = build_bundle(
        docked,
        alice_announcements=declaration.alice_announcement_alphabet,
        bob_announcements=declaration.bob_announcement_alphabet,
        reduction_chain=result.reduction_chain_record,
        created_by="tests.unit.test_bb84_wire_bundle",
    )
    write_bundle(tmp_path / "bundle", bundle)
    reread = read_bundle(tmp_path / "bundle")
    parsed = declaration_from_bundle(reread)
    # RAISES on the first violation; a clean return is the assertion.
    validate_declaration(parsed)

    assert parsed.alice_dim == docked.alice_dim
    assert parsed.rounds == docked.rounds
    assert parsed.parameters == docked.parameters
    assert parsed.acceptance_set.geometry == "polytope"
    assert parsed.acceptance_set.polytope is not None
    for label, identifier in labels.alice_outcome.items():
        np.testing.assert_array_equal(
            parsed.alice_povm[identifier], docked.alice_povm[label]
        )
    for label, identifier in labels.bob_outcome.items():
        np.testing.assert_array_equal(
            parsed.bob_povm[identifier]["s0"], docked.bob_povm[label]["s0"]
        )
    assert docked.alice_marginal is not None
    np.testing.assert_array_equal(parsed.alice_marginal, docked.alice_marginal)
    for (x, v), value in docked.key_map.items():
        assert parsed.key_map[(labels.alice_outcome[x], labels.bob_outcome[v])] == value


def test_the_reread_declaration_carries_the_chain_it_was_written_with(
    tmp_path: Path,
) -> None:
    result, declaration, docked = _docked()
    bundle, _ = build_bundle(
        docked,
        alice_announcements=declaration.alice_announcement_alphabet,
        bob_announcements=declaration.bob_announcement_alphabet,
        reduction_chain=result.reduction_chain_record,
        created_by="tests.unit.test_bb84_wire_bundle",
    )
    write_bundle(tmp_path / "bundle", bundle)
    chain = read_bundle(tmp_path / "bundle").manifest.payload.reduction_chain
    assert chain is not None
    assert chain.source_segment == ()
    assert len(chain.receiver_segment) == 1
    assert str(chain.receiver_segment[0].status) == "exact"


def test_a_bundle_without_a_chain_is_a_conforming_bundle() -> None:
    """The field is OPTIONAL, and absent means no chain was recorded."""
    manifest, arrays = _documents()
    manifest["payload"]["reduction_chain"] = None
    parsed = parse_manifest(manifest)
    assert parsed.payload.reduction_chain is None
    validate_bundle(parsed, arrays)


def _with_constraints(*entries: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the documents for the Band-A declaration plus the given entries."""
    from dataclasses import replace

    result, declaration, docked = _docked()
    manifest, arrays, _ = bundle_documents(
        replace(docked, constraint_list=tuple(entries)),
        alice_announcements=declaration.alice_announcement_alphabet,
        bob_announcements=declaration.bob_announcement_alphabet,
        reduction_chain=result.reduction_chain_record,
        created_by="test",
    )
    return manifest, arrays


def test_an_operator_bound_constraint_entry_reaches_the_wire() -> None:
    """Trusted-source mode: ``Theta_k`` is an operator on ``A`` and stays one.

    Band A's own list is empty; the trusted-source list is not, and the format
    carries ``constraint_list``. What is asserted here is
    that ``O_k`` crosses in the SAME block-diagonal form as a Bob POVM element
    -- def:admissible-declaration (iii) requires it to be sector-block-diagonal -- and
    that the bound crosses as an ARRAY rather than as a number.
    """
    from certiqs_key.domain.manifest import ConstraintRelation
    from certiqs_key.meat_core.declaration.declaration import ConstraintEntry, RhsTag

    manifest, arrays = _with_constraints(
        ConstraintEntry(
            operator_blocks={"s0": np.eye(2, dtype=np.complex128)},
            relation=ConstraintRelation.EQ,
            bound=np.eye(2, dtype=np.complex128) * 0.5,
            # THE DECLARED FORM, and it is DECLARED and not read off `bound`.
            # `general`: the bound is a Hermitian Theta_k on A. The wire carries
            # the tag from here, which is the property asserted below.
            rhs_tag=RhsTag.GENERAL,
        )
    )
    (entry,) = manifest["payload"]["declaration"]["constraint_list"]
    assert entry["relation"] == "eq"
    assert entry["constraint_rhs_tag"] == "general"
    assert entry["operator"]["form"] == "block_diagonal"
    assert entry["operator"]["block_kind"] == "proof_sector"
    operator = entry["operator"]["blocks"]["s0"]
    assert operator["semantic_role"] == "constraint_operator"
    assert operator["dataset"] in arrays
    assert entry["bound"]["semantic_role"] == "constraint_bound"
    assert entry["bound"]["dataset"] in arrays
    validate_bundle(parse_manifest(manifest), arrays)


def test_a_scalar_bound_crosses_as_a_number_and_is_not_promoted() -> None:
    """Untrusted-source mode: ``Theta_k = c_k`` is a real number and stays one.

    Not cosmetic. ``meat-core`` Remark ``rem:homog`` (a) exhibits a licensed
    attack set for which reading a scalar entry as the operator form
    ``Theta_k = c_k 1_A`` EMPTIES the feasible set, so a serializer that
    normalized the two spellings into one would change which states are
    feasible.
    """
    from certiqs_key.domain.manifest import ConstraintRelation
    from certiqs_key.meat_core.declaration.declaration import ConstraintEntry, RhsTag

    manifest, arrays = _with_constraints(
        ConstraintEntry(
            operator_blocks={"s0": np.eye(2, dtype=np.complex128)},
            relation=ConstraintRelation.PRECEQ,
            bound=0.25,
            # `homogeneous`: the bound is the real scalar c_k, the licensed
            # form. The tag is what tells the two spellings apart on the wire,
            # which is exactly what this test is about.
            rhs_tag=RhsTag.HOMOGENEOUS,
        )
    )
    (entry,) = manifest["payload"]["declaration"]["constraint_list"]
    assert entry["relation"] == "preceq"
    assert entry["bound"] == 0.25
    assert entry["constraint_rhs_tag"] == "homogeneous"
    validate_bundle(parse_manifest(manifest), arrays)


def test_every_entry_gets_its_own_datasets() -> None:
    """Two entries do not share a path, so neither can overwrite the other."""
    from certiqs_key.domain.manifest import ConstraintRelation
    from certiqs_key.meat_core.declaration.declaration import ConstraintEntry, RhsTag

    def entry(scale: float) -> Any:
        return ConstraintEntry(
            operator_blocks={"s0": np.eye(2, dtype=np.complex128) * scale},
            relation=ConstraintRelation.SUCCEQ,
            bound=scale,
            rhs_tag=RhsTag.HOMOGENEOUS,
        )

    manifest, arrays = _with_constraints(entry(1.0), entry(2.0))
    first, second = manifest["payload"]["declaration"]["constraint_list"]
    paths = {
        first["operator"]["blocks"]["s0"]["dataset"],
        second["operator"]["blocks"]["s0"]["dataset"],
    }
    assert len(paths) == 2
    assert paths <= set(arrays)
    validate_bundle(parse_manifest(manifest), arrays)


def test_the_band_a_declaration_still_carries_an_empty_list() -> None:
    """Slice 1 emits an empty list: Definition ``def:bandA``."""
    manifest, _ = _documents()
    assert manifest["payload"]["declaration"]["constraint_list"] == []


# ---------------------------------------------------------------------------
#  The compatibility rule: there is one version.
#
#  The reader accepts one schema version (spec/architecture.md 2.9 §6), so what
#  a writer owes is that it stamps a version the reader accepts, and what the
#  reader owes is that it says which retired version it found.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("version", RETIRED_SCHEMA_VERSIONS)
def test_a_retired_version_is_refused_by_name(version: str) -> None:
    manifest, _ = _documents()
    manifest["schema_version"] = version
    with pytest.raises(RetiredSchemaVersionError) as caught:
        parse_manifest(manifest)
    assert caught.value.declared_version == version
    assert caught.value.reason == "schema_version_retired"


def test_what_the_slice_writes_reads_back_at_the_stamped_version() -> None:
    """The writer's stamp and the reader's accepted set are the same string."""
    manifest, arrays = _documents()
    parsed = parse_manifest(manifest)
    assert parsed.schema_version == SCHEMA_VERSION
    assert parsed.payload.reduction_chain is not None
    validate_bundle(parsed, arrays)


def test_the_chain_may_be_omitted_and_the_declaration_is_unchanged() -> None:
    """``reduction_chain`` is optional.

    Absent means "no chain was recorded" and says nothing about which version
    stamped the bundle, so omitting it must leave the
    declaration -- which is the meat-core §2.1 input table -- identical.
    """
    manifest, _ = _documents()
    without = json.loads(json.dumps(manifest))
    without["payload"].pop("reduction_chain")
    assert parse_manifest(without).payload.reduction_chain is None
    assert (
        parse_manifest(without).payload.declaration
        == parse_manifest(manifest).payload.declaration
    )


# ---------------------------------------------------------------------------
#  The format's own structural validation: one defect at a time.
# ---------------------------------------------------------------------------


def _with_chain(mutate: Any) -> tuple[Any, dict[str, Any]]:
    """Return ``(manifest_document, arrays)`` with the chain mutated in place."""
    manifest, arrays = _documents()
    mutate(manifest["payload"]["reduction_chain"])
    return manifest, arrays


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda c: c["receiver_segment"][0].__setitem__("status", "probably_fine"),
            "status",
        ),
        (lambda c: c.__setitem__("receiver_segment", []), "receiver_segment"),
        (
            lambda c: c["receiver_segment"][0]["target_descriptor"].__setitem__(
                "dim", 0
            ),
            "dim",
        ),
        (
            lambda c: c.__setitem__("outcome_correspondence", []),
            "outcome_correspondence",
        ),
    ],
    ids=[
        "unknown-status",
        "no-receiver-link",
        "zero-dimension",
        "empty-correspondence",
    ],
)
def test_a_malformed_chain_is_refused_at_parse_time(mutate: Any, message: str) -> None:
    """The model's own half of §5.6: vocabulary, non-emptiness, positive dimensions."""
    manifest, _ = _with_chain(mutate)
    with pytest.raises(BundleValidationError, match=message):
        parse_manifest(manifest)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda c: c["receiver_segment"][0].__setitem__("segment", "source"),
            "filed under",
        ),
        (
            lambda c: c["receiver_segment"][0]["target_descriptor"].__setitem__(
                "sectors", [["s0", 1]]
            ),
            "does not decompose its own system",
        ),
        (
            lambda c: c["receiver_segment"][0]["target_descriptor"].update(
                {"dim": 3, "sectors": [["s0", 3]]}
            ),
            "declared receiver dimension",
        ),
        (
            lambda c: c["outcome_correspondence"].append(["_Y_0_", "not_an_outcome"]),
            "not in the declared Bob alphabet",
        ),
        (
            lambda c: c["outcome_correspondence"].append(["_Z_0_", "_Z_1_"]),
            "already has an image",
        ),
    ],
    ids=[
        "segment-mismatch",
        "sectors-do-not-sum",
        "dimension-disagrees",
        "outcome-outside-alphabet",
        "correspondence-not-a-function",
    ],
)
def test_a_chain_inconsistent_with_its_declaration_is_a_hard_error(
    mutate: Any, message: str
) -> None:
    """spec/architecture.md 3.6: "a hard error, never a warning and never a repair"."""
    manifest, arrays = _with_chain(mutate)
    parsed = parse_manifest(manifest)
    with pytest.raises(BundleValidationError, match=message):
        validate_bundle(parsed, arrays)


def test_a_physical_outcome_that_is_not_an_identifier_is_refused() -> None:
    """The reader is not looser than its own published schema.

    The schema types BOTH halves of ``outcome_correspondence`` as
    ``$defs/identifier``; the model types the physical half as a bare ``str``,
    and nothing else in the format ever looks at it -- the EMITTED half is
    checked by membership in the declared Bob alphabet, which ``check_alphabet``
    has already put through the identifier pattern, but ``V^ph`` is the
    reduction's own input alphabet and this format does not carry it. So without
    this check a bundle carrying ``(Z,0)`` there would be accepted by the reader
    and rejected by the schema, and an identifier is also an HDF5 link name.

    The writer sanitizes the physical half
    (:func:`certiqs_key.runs.wire._reduction_chain`), so no bundle this
    slice produces is affected; the case this exists for is a producer that does
    not, which is exactly the case a consumer cannot defend against by trusting.
    """
    manifest, arrays = _with_chain(
        lambda c: c["outcome_correspondence"].__setitem__(
            0, ["(Z,0) not an identifier!", "_Z_0_"]
        )
    )
    parsed = parse_manifest(manifest)
    with pytest.raises(BundleValidationError, match="not a stable identifier"):
        validate_bundle(parsed, arrays)


def test_a_duplicate_link_id_is_a_hard_error() -> None:
    manifest, arrays = _documents()
    chain = manifest["payload"]["reduction_chain"]
    twin = json.loads(json.dumps(chain["receiver_segment"][0]))
    chain["receiver_segment"].append(twin)
    parsed = parse_manifest(manifest)
    with pytest.raises(BundleValidationError, match="already used by"):
        validate_bundle(parsed, arrays)


def test_the_written_bundle_survives_the_disk_byte_for_byte(tmp_path: Path) -> None:
    """``dump_manifest`` is canonical, so a re-parse re-dumps identically."""
    from certiqs_key.domain.bundle import dump_manifest

    manifest, arrays = _documents()
    parsed = parse_manifest(manifest)
    write_bundle(tmp_path / "bundle", OperatorBundle(manifest=parsed, arrays=arrays))
    on_disk = (tmp_path / "bundle" / "manifest.json").read_text(encoding="utf-8")
    assert on_disk == dump_manifest(parsed)
    assert dump_manifest(parse_manifest(json.loads(on_disk))) == on_disk
