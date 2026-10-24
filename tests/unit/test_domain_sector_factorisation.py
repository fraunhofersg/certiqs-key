"""Schema 0.4.0: the factorised sector map on the wire, and its degenerate case.

Motivation: 0.4.0 exists so that a manifest CAN carry a factor's system tag and
a joint operator's ``A``-side structure,
and the whole of its design rule is that **today's format is the one-``Q``-factor,
one-Alice-sector case of it, entry for entry**. Two things have to be executed
for that sentence to mean anything: that a payload of today's shape is stamped
and written exactly as it was before 0.4.0 existed, and that a factorisation
which disagrees with the keys it refines is refused rather than reconciled.

WHAT IS ASSERTED HERE. The stamp rule in both directions (the stamp is the
lowest version that can express the document, so a 0.3.0-shaped payload stamped
0.4.0 is refused as well); that the key is not written as ``null``; the
degenerate one-``Q``-factor product; the decoy shape (an ``A`` factor first, a
``Q`` factor after it); and each refusal the product and the manifest make --
including the one this wire cannot yet express, a ``Q`` side of two factors,
whose flattened identifier is not a stable identifier.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from bundle_format_fixtures import array_descriptor, minimal_manifest

from certiqs_key.domain._base import BundleValidationError
from certiqs_key.domain.bundle import dump_manifest, parse_manifest
from certiqs_key.domain.manifest import (
    SCHEMA_VERSION,
    SCHEMA_VERSION_FACTORISED,
    schema_version_for,
)
from certiqs_key.domain.validation import validate_manifest
from certiqs_key.foundations.blocks import PRODUCT_LABEL_SEPARATOR

#: The declared map of the minimal fixture, as a factor's own ``((s, d_s))_s``.
MEASURED_FACTOR: dict[str, Any] = {
    "system": "Q",
    "party": "B",
    "sectors": [["s0", 2], ["s1", 1]],
}

#: An ``A`` side that decomposes the fixture's ``d_A = 2`` into two sectors --
#: the decoy shape, at the smallest size that is not the degenerate one.
RETAINED_FACTOR: dict[str, Any] = {
    "system": "A",
    "party": "A",
    "sectors": [["t0", 1], ["t1", 1]],
}


def factorised(
    *factors: dict[str, Any], schema_version: str = SCHEMA_VERSION_FACTORISED
) -> dict[str, Any]:
    """Return the minimal manifest with a declared factorisation and a stamp."""
    document = minimal_manifest()
    document["schema_version"] = schema_version
    document["payload"]["declaration"]["sector_factorisation"] = [
        dict(factor) for factor in factors
    ]
    return document


def with_product_sectors() -> dict[str, Any]:
    """Return a manifest whose declared map IS the flattening of two Q factors.

    The fixture's two sectors, crossed with a two-sector first factor
    ``(qa0, qa1)`` of dimension one each: four declared sectors, named and
    ordered exactly as the product convention names and orders them, with one
    Bob POVM block per sector.
    """
    document = minimal_manifest()
    document["schema_version"] = SCHEMA_VERSION_FACTORISED
    declaration = document["payload"]["declaration"]
    join = PRODUCT_LABEL_SEPARATOR.join
    flattened = [
        (join((first, second)), second, dim)
        for first in ("qa0", "qa1")
        for second, dim in (("s0", 2), ("s1", 1))
    ]
    declaration["sector_index_set"] = [label for label, _, _ in flattened]
    declaration["sector_dims"] = {label: dim for label, _, dim in flattened}
    for outcome, operator in declaration["bob_povm"].items():
        operator["blocks"] = {
            label: array_descriptor(
                f"/declaration/bob_povm/{outcome}/{label}",
                dtype="float64",
                shape=(dim, dim),
                basis=f"computational.Q.{label}",
                subsystem_order=("Q",),
                storage="dense",
                semantic_role="bob_povm_element",
            )
            for label, _, dim in flattened
        }
        operator["block_permutation"] = list(range(len(flattened)))
    return document


# ---------------------------------------------------------------------------
#  The degenerate case: today's bytes, today's stamp
# ---------------------------------------------------------------------------


def test_a_payload_of_todays_shape_is_written_as_it_was_before_0_4_0() -> None:
    """No key, no null, no new stamp: the bytes of a 0.3.0 bundle do not move.

    The optional key is emitted only when it is used
    (``Declaration.serialize``), so the payload's key set is the pre-0.4.0 one and
    the stamp is the one :func:`schema_version_for` gives a payload that takes
    the single-factor default.
    """
    manifest = parse_manifest(minimal_manifest())
    assert manifest.payload.declaration.sector_factorisation is None
    assert schema_version_for(manifest.payload) == SCHEMA_VERSION == "0.3.0"
    document = json.loads(dump_manifest(manifest))
    assert set(document["payload"]) == {
        "alphabets",
        "declaration",
        "parameters",
        "reduction_chain",
    }
    assert "sector_factorisation" not in document["payload"]["declaration"]


def test_the_single_q_factor_product_is_todays_map_said_in_the_new_shape() -> None:
    """One ``Q`` factor whose map IS the declared one: accepted, and a refinement.

    Nothing about the declaration changes -- ``sector_index_set``,
    ``sector_dims`` and ``alice_dim`` are read exactly as before -- so this is
    the same bundle with its factorisation spelled out.
    """
    manifest = parse_manifest(factorised(MEASURED_FACTOR))
    validate_manifest(manifest)
    assert manifest.schema_version == SCHEMA_VERSION_FACTORISED
    factorisation = manifest.payload.declaration.sector_factorisation
    assert factorisation is not None
    (factor,) = factorisation
    assert factor.system.value == "Q"
    assert factor.party == "B"
    assert factor.sectors == (("s0", 2), ("s1", 1))
    document = json.loads(dump_manifest(manifest))
    assert document["payload"]["declaration"]["sector_factorisation"] == [
        MEASURED_FACTOR
    ]


def test_the_decoy_shape_declares_an_a_factor_first_and_a_q_factor_after_it() -> None:
    """``[(A, alice, Alice sectors), (Q, bob, receiver sectors)]``, validated."""
    manifest = parse_manifest(factorised(RETAINED_FACTOR, MEASURED_FACTOR))
    validate_manifest(manifest)
    factorisation = manifest.payload.declaration.sector_factorisation
    assert factorisation is not None
    assert [factor.system.value for factor in factorisation] == ["A", "Q"]
    assert factorisation[0].sectors == (("t0", 1), ("t1", 1))


# ---------------------------------------------------------------------------
#  The stamp is a fact about the document, in both directions
# ---------------------------------------------------------------------------


def test_a_factorised_payload_stamped_0_3_0_is_refused() -> None:
    """A document that lies about itself: a 0.3.0 reader could not read it."""
    document = factorised(MEASURED_FACTOR, schema_version=SCHEMA_VERSION)
    with pytest.raises(BundleValidationError, match="sector_factorisation"):
        parse_manifest(document)


def test_a_payload_of_todays_shape_stamped_0_4_0_is_refused() -> None:
    """The other direction, and it is refused for the bytes as well as the truth."""
    document = minimal_manifest()
    document["schema_version"] = SCHEMA_VERSION_FACTORISED
    with pytest.raises(BundleValidationError, match="schema_version"):
        parse_manifest(document)


# ---------------------------------------------------------------------------
#  The refusals
# ---------------------------------------------------------------------------


def test_two_a_factors_are_refused_rather_than_merged() -> None:
    """The retained system is one system; a second decomposition of it is not read."""
    second = {"system": "A", "party": "A", "sectors": [["u0", 2]]}
    manifest = parse_manifest(
        factorised(RETAINED_FACTOR, second, MEASURED_FACTOR)
    )
    with pytest.raises(BundleValidationError, match="AT MOST ONE"):
        validate_manifest(manifest)


def test_an_a_factor_that_is_not_first_is_refused_rather_than_permuted() -> None:
    """The joint block convention is ``A``-first, and a product is not reordered."""
    manifest = parse_manifest(factorised(MEASURED_FACTOR, RETAINED_FACTOR))
    with pytest.raises(BundleValidationError, match="FIRST factor"):
        validate_manifest(manifest)


def test_an_a_side_that_does_not_sum_to_alice_dim_is_refused() -> None:
    """A decomposition that does not decompose its own system."""
    wrong = {"system": "A", "party": "A", "sectors": [["t0", 1], ["t1", 2]]}
    manifest = parse_manifest(factorised(wrong, MEASURED_FACTOR))
    with pytest.raises(BundleValidationError, match="alice_dim"):
        validate_manifest(manifest)


@pytest.mark.parametrize(
    ("sectors", "because"),
    [
        ([["s1", 1], ["s0", 2]], "in that order"),
        ([["s0", 2]], "does not replace it"),
        ([["s0", 3], ["s1", 1]], "does not replace it"),
    ],
)
def test_a_q_side_that_is_not_the_declared_map_is_refused(
    sectors: list[list[Any]], because: str
) -> None:
    """The factorisation says how the DECLARED map factorises, in its order."""
    factor = {"system": "Q", "party": "B", "sectors": sectors}
    manifest = parse_manifest(factorised(factor))
    with pytest.raises(BundleValidationError, match=because):
        validate_manifest(manifest)


def test_a_declaration_with_no_q_factor_at_all_is_refused() -> None:
    """A map of the retained system alone declares no measured system."""
    manifest = parse_manifest(factorised(RETAINED_FACTOR))
    with pytest.raises(BundleValidationError, match="no Q factor"):
        validate_manifest(manifest)


def test_a_factorised_declaration_names_a_block_kind_of_the_shared_vocabulary() -> None:
    """The one-kind rule is stated over ``BlockKind``, so the string must be one.

    Elsewhere this format carries ``sector_block_kind`` as a string it does not
    interpret; a FACTORISED declaration is the one place it must name a member,
    because the rule that the factors of one map carry ONE kind is stated over
    that vocabulary.
    """
    document = factorised(MEASURED_FACTOR)
    document["payload"]["declaration"]["sector_block_kind"] = "proof"
    manifest = parse_manifest(document)
    with pytest.raises(BundleValidationError, match="sector_block_kind"):
        validate_manifest(manifest)


def test_a_two_factor_q_side_is_expressible_and_flattens_last_factor_fastest() -> None:
    """THE BBM92 SHAPE: two measured factors, and the wire carries the flattening.

    A sector identifier is an HDF5 link name
    (:mod:`certiqs_key.domain.identifiers`), so the flattened identifier of a
    product is one too. That is why the declared product separator is ``"__"``
    and not a character outside the identifier alphabet: with ``"*"`` this
    document could not have been written at all, and BBM92 declares two measured
    factors. What is checked here is the whole path -- the declared
    ``sector_index_set`` IS the flattening, in the product order with the last
    factor fastest, and the manifest agrees with it rather than being reconciled
    to it.
    """
    document = with_product_sectors()
    first = {"system": "Q", "party": "A", "sectors": [["qa0", 1], ["qa1", 1]]}
    second = {"system": "Q", "party": "B", "sectors": [["s0", 2], ["s1", 1]]}
    document["payload"]["declaration"]["sector_factorisation"] = [first, second]
    manifest = parse_manifest(document)
    validate_manifest(manifest)
    assert manifest.payload.declaration.sector_index_set == (
        "qa0__s0",
        "qa0__s1",
        "qa1__s0",
        "qa1__s1",
    )


def test_a_two_factor_q_side_that_is_not_the_declared_flattening_is_refused() -> None:
    """The order of the two factors is the product order, not a preference."""
    document = with_product_sectors()
    first = {"system": "Q", "party": "A", "sectors": [["qa1", 1], ["qa0", 1]]}
    second = {"system": "Q", "party": "B", "sectors": [["s0", 2], ["s1", 1]]}
    document["payload"]["declaration"]["sector_factorisation"] = [first, second]
    manifest = parse_manifest(document)
    with pytest.raises(BundleValidationError, match="in that order"):
        validate_manifest(manifest)


def test_a_factor_identifier_may_not_contain_the_product_separator() -> None:
    """Otherwise the flattened identifier no longer says which factor it is."""
    label = f"s0{PRODUCT_LABEL_SEPARATOR}x"
    factor = {"system": "Q", "party": "B", "sectors": [[label, 2], ["s1", 1]]}
    with pytest.raises(BundleValidationError, match="product separator"):
        parse_manifest(factorised(factor))


def test_a_factor_carries_a_system_of_the_closed_vocabulary() -> None:
    """``A`` or ``Q`` and no third: the round model has two systems."""
    factor = {"system": "E", "party": "B", "sectors": [["s0", 2], ["s1", 1]]}
    with pytest.raises(BundleValidationError, match="system"):
        parse_manifest(factorised(factor))


@pytest.mark.parametrize("version", [SCHEMA_VERSION, SCHEMA_VERSION_FACTORISED])
def test_a_present_but_empty_factorisation_is_refused_by_the_schema(
    version: str,
) -> None:
    """Absence already spells the default, so an empty list says nothing.

    Refused at either stamp, and by the SCHEMA -- a producer that meant to
    declare a factorisation and declared none is a malformed document, not a
    document that fell back on the single-factor reading.
    """
    document = minimal_manifest()
    document["schema_version"] = version
    document["payload"]["declaration"]["sector_factorisation"] = []
    with pytest.raises(BundleValidationError, match="sector_factorisation"):
        parse_manifest(document)


def test_a_flattened_wire_identifier_says_which_factor_supplied_which_part() -> None:
    """On the wire: the same refusal, reached by building the shared type.

    A record has no neighbours, so the adjacency half of the injectivity rule is
    decided over the LIST -- in ``validate_manifest``, which builds
    ``FactorisedSectorMap`` from the records and lets it refuse. One home for
    one rule.
    """
    document = with_product_sectors()
    document["payload"]["declaration"]["sector_factorisation"] = [
        {"system": "Q", "party": "A", "sectors": [["qa0", 1], ["qa1_", 1]]},
        {"system": "Q", "party": "B", "sectors": [["s0", 2], ["s1", 1]]},
    ]
    manifest = parse_manifest(document)
    with pytest.raises(BundleValidationError, match="product separator"):
        validate_manifest(manifest)


#: A declared party partition over the minimal fixture's alphabets, giving the
#: retained system to party ``A``. Present, so the ``A`` factor's party is
#: cross-checked against it.
PARTITION: dict[str, Any] = {
    "readout_alice": {"x0": {"v0": "x0", "v1": "x0"}, "x1": {"v0": "x1", "v1": "x1"}},
    "readout_bob": {"x0": {"v0": "v0", "v1": "v1"}, "x1": {"v0": "v0", "v1": "v1"}},
    "alphabet_alice": ["x0", "x1"],
    "alphabet_bob": ["v0", "v1"],
    "party_of_alice_system": "A",
    "party_of_sector_factors": {"s0": ["B"], "s1": ["B"]},
}


def test_the_a_factor_is_scoped_to_the_party_the_partition_gives_a_to() -> None:
    """Who holds ``A`` is one fact, and the format carries no second answer."""
    document = factorised(RETAINED_FACTOR, MEASURED_FACTOR)
    document["payload"]["declaration"]["party_partition"] = dict(PARTITION)
    validate_manifest(parse_manifest(document))

    disagreeing = factorised(
        {"system": "A", "party": "B", "sectors": [["t0", 1], ["t1", 1]]},
        MEASURED_FACTOR,
    )
    disagreeing["payload"]["declaration"]["party_partition"] = dict(PARTITION)
    manifest = parse_manifest(disagreeing)
    with pytest.raises(BundleValidationError, match="party_of_alice_system"):
        validate_manifest(manifest)

    # With the partition ABSENT nothing is compared: absence spells the default
    # partition, and this format does not settle the default's reading of a
    # factorised map on the producer's behalf.
    validate_manifest(parse_manifest(factorised(RETAINED_FACTOR, MEASURED_FACTOR)))
