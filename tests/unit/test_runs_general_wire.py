"""General bundles retain factor data and transcript decisions across disk."""

from collections.abc import Callable
from dataclasses import replace
from functools import partial
from pathlib import Path

import numpy as np
import pytest
from tests.support.general_toys import (
    decoy_like_general,
    qubit_bb84_general,
    two_factor_general,
)

from certiqs_key.domain._base import BundleValidationError
from certiqs_key.domain.bundle import parse_manifest, read_bundle, write_bundle
from certiqs_key.domain.validation import validate_manifest
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.declaration.general_validation import (
    validate_general_declaration,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.runs.general_wire import build_general_bundle
from certiqs_key.runs.pipeline import Preparation


@pytest.mark.parametrize(
    "factory",
    [
        decoy_like_general,
        partial(two_factor_general, party_local=True),
        partial(qubit_bb84_general, messages=3),
    ],
)
def test_factor_arrays_and_transcript_round_trip(
    factory: Callable[[], GeneralDeclaration],
    tmp_path: Path,
) -> None:
    declaration = replace(factory(), sector_block_kind="proof_sector")
    bundle, ids = build_general_bundle(
        declaration,
        alice_announcements=(),
        bob_announcements=(),
        reduction_chain=None,
        created_by="general-wire-test",
    )
    write_bundle(tmp_path / "bundle", bundle)
    reread = declaration_from_bundle(read_bundle(tmp_path / "bundle"))
    assert isinstance(reread, GeneralDeclaration)
    assert reread.rounds == declaration.rounds
    assert reread.alice_form == declaration.alice_form
    assert len(reread.factors) == len(declaration.factors)
    assert reread.sector_index_set == tuple(ids.sector.values())
    for before, after in zip(declaration.factors, reread.factors, strict=True):
        assert before.party == after.party
        for bv, av in zip(before.alphabet, after.alphabet, strict=True):
            for bs, ass in zip(
                before.sectors.labels, after.sectors.labels, strict=True
            ):
                np.testing.assert_array_equal(
                    before.blocks[bv][bs], after.blocks[av][ass]
                )
    for (x, v), key in declaration.key_map.items():
        assert reread.key_map[ids.alice_outcome[x], ids.bob_outcome[v]] == key
        assert (
            reread.acceptance_value(ids.alice_outcome[x], ids.bob_outcome[v])
            == (ids.acceptance_value[declaration.acceptance_value(x, v)])
        )


@pytest.mark.parametrize(
    "defect", ["missing_phi", "bad_phi", "missing_message", "bad_message"]
)
def test_unreachable_transcript_cells_are_validated_before_writing(defect: str) -> None:
    declaration = qubit_bb84_general(messages=3)
    unreachable = ("Z", "Z", "drop")
    assert all(
        declaration.announcement(x, v) != unreachable
        for x in declaration.alice_alphabet
        for v in declaration.bob_outcomes
    )
    if defect.endswith("phi"):
        phi = dict(declaration.accept_statistic)
        if defect == "missing_phi":
            del phi[unreachable]
        else:
            phi[unreachable] = "outside"
        declaration = replace(declaration, accept_statistic=phi)
    else:
        messages = list(declaration.transcript.messages)
        table = dict(messages[2].table)
        # This readout/prefix combination is unreachable for Alice z0.
        cell = ("z0", ("X", "Z"))
        if defect == "missing_message":
            del table[cell]
        else:
            table[cell] = "outside"
        messages[2] = replace(messages[2], table=table)
        declaration = replace(
            declaration,
            transcript=replace(declaration.transcript, messages=tuple(messages)),
        )
    with pytest.raises(DeclarationError, match=r"phi|message"):
        validate_general_declaration(declaration)
    with pytest.raises(DeclarationError, match=r"phi|message"):
        build_general_bundle(
            declaration,
            alice_announcements=(),
            bob_announcements=(),
            reduction_chain=None,
            created_by="invalid-transcript",
        )


def test_message_mapping_insertion_order_is_not_wire_semantics(tmp_path: Path) -> None:
    declaration = qubit_bb84_general(messages=3)
    messages = tuple(
        replace(m, table=dict(reversed(tuple(m.table.items()))))
        for m in declaration.transcript.messages
    )
    shuffled = replace(
        declaration, transcript=replace(declaration.transcript, messages=messages)
    )
    test_factor_arrays_and_transcript_round_trip(lambda: shuffled, tmp_path)


def test_scoped_constraint_uses_its_factor_basis_namespace() -> None:
    """Equal local shapes on different factors do not identify their bases."""
    declaration = replace(
        two_factor_general(party_local=True), sector_block_kind="proof_sector"
    )
    bundle, _ = build_general_bundle(
        declaration,
        alice_announcements=(),
        bob_announcements=(),
        reduction_chain=None,
        created_by="scoped-constraint-basis-test",
    )
    validate_manifest(bundle.manifest)

    malformed = bundle.manifest.model_dump(mode="json")
    constraint = malformed["payload"]["declaration"]["constraint_list"][0]
    constraint["operator"]["blocks"]["qB"]["basis"] = "computational.Q.0.qB"
    with pytest.raises(BundleValidationError, match="basis"):
        validate_manifest(parse_manifest(malformed))


def test_ensemble_slot_survives_without_constructing_a_povm(tmp_path: Path) -> None:
    declaration = replace(
        decoy_like_general(ensemble=True), sector_block_kind="proof_sector"
    )
    bundle, _ = build_general_bundle(
        declaration,
        alice_announcements=(),
        bob_announcements=(),
        reduction_chain=None,
        created_by="ensemble-wire-test",
    )
    assert not bundle.manifest.payload.declaration.alice_povm
    assert bundle.manifest.payload.declaration.alice_ensemble
    write_bundle(tmp_path / "bundle", bundle)
    reread = declaration_from_bundle(read_bundle(tmp_path / "bundle"))
    assert isinstance(reread, GeneralDeclaration)
    assert reread.alice_form == declaration.alice_form
    for x in declaration.alice_alphabet:
        for t in declaration.alice_sectors:
            np.testing.assert_array_equal(
                reread.alice_operators[x][t], declaration.alice_operators[x][t]
            )


def test_bbm92_preparation_round_trips_both_local_chains(tmp_path: Path) -> None:
    """The production two-station compiler artifact reaches disk and back."""
    from instances.bbm92.surface import default_config, preparation

    prepared = preparation(default_config())
    assert isinstance(prepared, Preparation), prepared
    candidate = prepared.declaration
    raw = prepared.raw_joint_distribution
    assert raw is not None
    frequencies = dict.fromkeys(candidate.acceptance_alphabet, 0.0)
    for (x, v), probability in raw.items():
        value = candidate.acceptance_value(candidate.announcement(x, v))
        frequencies[value] += float(probability)
    docked = dock_general_candidate(
        candidate,
        acceptance_set=AcceptanceSet(
            geometry="singleton",
            frequencies=tuple(
                frequencies[value] for value in candidate.acceptance_alphabet
            ),
        ),
        rounds=default_config().rounds,
        parameters=default_config().parameters,
        reduction_chain_record=prepared.compilation.reduction_chain_record,
    )
    bundle, _ = build_general_bundle(
        docked,
        alice_announcements=candidate.alice_announcement_alphabet,
        bob_announcements=candidate.bob_announcement_alphabet,
        reduction_chain=prepared.compilation.reduction_chain_record,
        created_by="bbm92-general-wire-test",
    )
    chain = bundle.manifest.payload.reduction_chain
    assert chain is not None
    assert hasattr(chain, "receiver_factor_segments")
    assert len(chain.receiver_factor_segments) == 2
    malformed = bundle.manifest.model_dump(mode="json")
    malformed["payload"]["reduction_chain"]["receiver_factor_segments"][0][
        "outcome_correspondence"
    ][0][1] = "outside_local_factor_alphabet"
    with pytest.raises(BundleValidationError, match="emitted outcome"):
        validate_manifest(parse_manifest(malformed))
    write_bundle(tmp_path / "bbm92-bundle", bundle)
    reread = declaration_from_bundle(read_bundle(tmp_path / "bbm92-bundle"))
    assert isinstance(reread, GeneralDeclaration)
    assert len(reread.factors) == 2
