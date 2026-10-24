"""Source links: the two witness kinds, the obligation triple, the registry.

``transmitter/def:source-link`` (the tuple and its slots) and
``transmitter/def:source-segment`` (which kinds are admitted, and (A1) to (A3)).

C4 admits tagging through its declaring submodule and preserves the raw
core refusals for missing admission, deferred source maps and unknown kinds.
These tests also exercise the individual A1--A3 conditions directly; public
cross-module admission is covered by test_transmitter_c4_admission.py.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import matrix
from certiqs_key.transmitter.artifact import SourceSpecification, emit_artifact
from certiqs_key.transmitter.links import (
    DECLARED_KINDS_WITHOUT_A_SOUNDNESS_CLAIM,
    SOUNDNESS_REGISTRY,
    AliceSideDescriptor,
    ObligationRecord,
    SourceLink,
    SourceLinkKind,
    SourceLinkStatus,
    WitnessKind,
    check_source_link,
    source_link_kinds,
)
from certiqs_key.transmitter.reasons import Refusal, RefusalReason

pytestmark = pytest.mark.contract

ALPHABET = ("x0", "x1")
WEIGHTS = {"x0": F(1, 2), "x1": F(1, 2)}
#: A ledger OF SHORT IDS, which is what Eq. ``eq:registry`` and (A2) compare
#: against and what :func:`check_source_link` reads. The ledger an artefact
#: emits carries MACHINE KEYS instead; the compiler explicitly resolves them
#: to short IDs at the source-link check boundary.
LEDGER = ("A-ENS", "A-SEQ", "A-WCP")

DESCRIPTOR = AliceSideDescriptor(
    name="A^v",
    alphabet=ALPHABET,
    weights=WEIGHTS,
    system_dim=2,
    weighted_members={
        "x0": matrix(((F(1, 2), 0), (0, 0))),
        "x1": matrix(((0, 0), (0, F(1, 2)))),
    },
)
TARGET = replace(DESCRIPTOR, name="A'")

TAGGING = ObligationRecord(
    kind=SourceLinkKind.TAGGING,
    soundness_claim="transmitter/decoy/prop:tagging",
    assumptions=("A-WCP",),
    family_member="the emitted tagged source declaration",
)


def _data_link(**overrides: object) -> SourceLink:
    fields: dict[str, object] = {
        "kind": SourceLinkKind.TAGGING,
        "source_descriptor": DESCRIPTOR,
        "target_descriptor": TARGET,
        "channel_witness": {"x0": matrix(((1, 0), (0, 1)))},
        "declared_descriptor_family": (DESCRIPTOR.name,),
    }
    fields.update(overrides)
    return SourceLink(**fields)  # type: ignore[arg-type]


def _constructor_link(**overrides: object) -> SourceLink:
    fields: dict[str, object] = {
        "kind": SourceLinkKind.TAGGING,
        "source_descriptor": DESCRIPTOR,
        "target_descriptor": TARGET,
        "channel_witness": None,
        "declared_descriptor_family": ("every tagged source declaration",),
        "obligation": TAGGING,
        "status": SourceLinkStatus.EXACT,
    }
    fields.update(overrides)
    return SourceLink(**fields)  # type: ignore[arg-type]


def _specification(segment: tuple[object, ...]) -> SourceSpecification:
    return SourceSpecification(
        signal_alphabet=ALPHABET,
        transmitted_dim=2,
        signal_weights=dict(WEIGHTS),
        signal_states={
            "x0": matrix(((1, 0), (0, 0))),
            "x1": matrix(((0, 0), (0, 1))),
        },
        alice_dim=2,
        alice_povm={
            "x0": matrix(((1, 0), (0, 0))),
            "x1": matrix(((0, 0), (0, 1))),
        },
        source_segment=segment,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
#  C4: the raw core admission boundary
# ---------------------------------------------------------------------------


def test_the_core_declared_kind_still_trips_link_kind_deferred() -> None:
    """``source-map`` is declared, reserved and refused, with the frozen string."""
    result = emit_artifact(_specification(("source-map",)))
    assert result.artifact is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.LINK_KIND_DEFERRED


def test_admitted_kind_still_requires_admitting_module_provenance() -> None:
    """A3 refuses a core specification even when its link kind is admitted."""
    result = emit_artifact(_specification((_constructor_link(),)))
    assert result.artifact is None
    assert result.refusal is not None
    assert (
        result.refusal.reason is RefusalReason.SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE
    )


def test_a_segment_carries_kinds_as_strings_or_as_typed_links() -> None:
    """The kind is read off either spelling, so the refusal names what arrived."""
    assert source_link_kinds(("source-map",)) == ("source-map",)
    assert source_link_kinds((_constructor_link(),)) == ("tagging",)


# ---------------------------------------------------------------------------
#  def:source-link: the tuple's own typing
# ---------------------------------------------------------------------------


def test_a_witness_is_supplied_in_exactly_one_of_the_two_ways() -> None:
    """(c): as data OR as a theorem constructor, never both and never neither."""
    with pytest.raises(MalformedInputError, match="EITHER as data"):
        _data_link(obligation=TAGGING)
    with pytest.raises(MalformedInputError, match="EITHER as data"):
        _constructor_link(obligation=None)


def test_the_obligations_first_component_is_the_links_own_kind() -> None:
    """Eq. ``eq:obligation``: the triple's first slot IS the kind."""
    with pytest.raises(MalformedInputError, match="first component IS the link"):
        _constructor_link(kind=SourceLinkKind.SOURCE_MAP)


def test_the_witness_kind_is_derived_and_has_no_second_carrier() -> None:
    """Which slot is filled IS the witness kind."""
    assert _data_link().witness_kind is WitnessKind.DATA
    assert _constructor_link().witness_kind is WitnessKind.THEOREM_CONSTRUCTOR
    fields = set(SourceLink.__dataclass_fields__)
    assert "witness_kind" not in fields


# ---------------------------------------------------------------------------
#  The admission rule and (A1)-(A3), decided directly
# ---------------------------------------------------------------------------


def _check(link: SourceLink, **overrides: object) -> Refusal | None:
    kwargs: dict[str, object] = {
        "assumption_ledger": LEDGER,
        "from_admitting_module": True,
    }
    kwargs.update(overrides)
    return check_source_link(link, **kwargs)  # type: ignore[arg-type]


def test_an_admitted_constructor_link_passes_every_decided_condition() -> None:
    """The one kind with a soundness claim, with the registry's own triple."""
    assert _check(_constructor_link()) is None


def test_a_non_empty_entry_list_is_refused_whatever_the_kind() -> None:
    """"NO CLAIM OF THIS REPOSITORY TRANSPORTS AN ALICE-SIDE ENTRY."""
    refusal = _check(_constructor_link(constraint_entries=("anything",)))
    assert refusal is not None
    assert refusal.reason is RefusalReason.SOURCE_LINK_ENTRY_PRESENT


def test_a_licence_without_an_entry_is_refused() -> None:
    """(f): the licence is present EXACTLY WHEN the entry list is non-empty."""
    refusal = _check(_constructor_link(licence="a record"))
    assert refusal is not None
    assert refusal.reason is RefusalReason.SOURCE_LINK_ENTRY_PRESENT


def test_a_kind_without_a_registry_entry_is_refused() -> None:
    """The core's ``source-map``: declared, and no claim proves it."""
    link = _data_link(
        kind=SourceLinkKind.SOURCE_MAP, declared_descriptor_family=(DESCRIPTOR.name,)
    )
    refusal = _check(link)
    assert refusal is not None
    assert refusal.reason is RefusalReason.LINK_KIND_DEFERRED
    assert SourceLinkKind.SOURCE_MAP in DECLARED_KINDS_WITHOUT_A_SOUNDNESS_CLAIM


def test_a_data_links_family_must_contain_its_own_descriptor() -> None:
    """A data link's family must contain its own source descriptor.

    (d): a link whose family excludes it "asserts nothing about the descriptor
    it carries, and is refused".
    """
    refusal = _check(_data_link(declared_descriptor_family=("something else",)))
    assert refusal is not None
    assert refusal.reason is (
        RefusalReason.SOURCE_LINK_FAMILY_EXCLUDES_ITS_DESCRIPTOR
    )


def test_family_membership_is_not_decided_for_a_constructor_link() -> None:
    """Family membership is not decided for a constructor link.

    (d): "FOR A CONSTRUCTOR LINK THAT MEMBERSHIP IS NOT A DECIDABLE CONDITION
    AND THIS DEFINITION DOES NOT PRETEND OTHERWISE."

    A constructor link whose declared family names nothing its descriptor
    matches is NOT refused for that: what is decided there is the triple.
    """
    assert _check(_constructor_link(declared_descriptor_family=("unrelated",))) is None


def test_a_triple_that_matches_no_registry_entry_is_refused() -> None:
    """(A2), compared entry by entry as declared strings."""
    refusal = _check(
        _constructor_link(
            obligation=replace(TAGGING, soundness_claim="transmitter/decoy/prop:other")
        )
    )
    assert refusal is not None
    assert refusal.reason is RefusalReason.SOURCE_LINK_NOT_IN_REGISTRY


def test_omitting_either_half_of_the_third_component_is_refused() -> None:
    """(A2): "BOTH COMPONENTS of A(kind) are compared".

    ``prop:tagging``'s assumption closure is EMPTY and the entry carries A-WCP
    for the other reason (A1) gives, so a link naming the empty closure alone is
    refused exactly as one naming neither -- which is the failure the registry's
    ``why_this_list`` field exists to prevent.
    """
    refusal = _check(_constructor_link(obligation=replace(TAGGING, assumptions=())))
    assert refusal is not None
    assert refusal.reason is RefusalReason.SOURCE_LINK_NOT_IN_REGISTRY


def test_an_assumption_the_ledger_does_not_carry_is_refused() -> None:
    """(A2): every assumption of the matched entry must TRAVEL in the ledger."""
    refusal = _check(_constructor_link(), assumption_ledger=("A-SEQ",))
    assert refusal is not None
    assert refusal.reason is RefusalReason.SOURCE_LINK_ASSUMPTION_NOT_IN_LEDGER


@pytest.mark.parametrize(
    "link", [_constructor_link(), _data_link()], ids=["constructor", "data"]
)
def test_a_segment_from_another_module_is_refused_whatever_its_triples(
    link: SourceLink,
) -> None:
    """(A3): a segment from another module is refused, for BOTH sorts of link.

    "The registry says which kinds this repository has proved, not that a
    particular link was built by the module that proved them."

    (A3) is decided before the CONSTRUCTOR branch: decided after the triple and
    the ledger, ``check_source_link`` would return ``None`` for every data link
    before reaching it -- and a data link carries no triple at all, so the links
    the condition is most about, the ones a consumer assembled itself, would be
    exactly the ones that passed. The condition is stated on the SEGMENT.
    """
    refusal = _check(link, from_admitting_module=False)
    assert refusal is not None
    assert refusal.reason is RefusalReason.SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE


def test_a_data_link_from_the_admitting_module_still_passes() -> None:
    """Moving (A3) up refuses no link that was admissible before it moved."""
    assert _check(_data_link()) is None


# ---------------------------------------------------------------------------
#  The registry itself
# ---------------------------------------------------------------------------


def test_the_registry_is_closed_and_is_the_interfaces_table() -> None:
    """One entry, and it is the ``soundness_registry`` output row's table.

    "The registry is closed: a kind not in it is refused, and ADDING ONE IS A
    CLAIM BATCH, NOT A CONFIGURATION." The third component is the union of the
    soundness claim's (empty) assumption closure and the physical-source
    assumption the submodule declares for its model.
    """
    assert len(SOUNDNESS_REGISTRY) == 1
    entry = SOUNDNESS_REGISTRY[0]
    assert entry.triple == (
        "tagging",
        "transmitter/decoy/prop:tagging",
        ("A-WCP",),
    )


def test_the_registry_the_artefact_emits_is_the_modules_own() -> None:
    """(A1): the emitted registry is the module version's own.

    "The registry of an artefact is the registry of the VERSION of this module
    that emitted it, not a datum a request supplies".
    """
    artifact = emit_artifact(_specification(())).require()
    assert artifact.soundness_registry == SOUNDNESS_REGISTRY
    assert "soundness_registry" not in set(SourceSpecification.__dataclass_fields__)
