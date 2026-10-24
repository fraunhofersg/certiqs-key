"""``req:link-row-provenance``: A-LINK is omitted only on a proved chain.

WHAT THIS FILE IS THE TEST HALF OF. The discharge is per measured factor (at
several factors the joint transfer is reductions/thm:emitted-product (ii), (iii)
with A-MEAS (iv)). The compiler omits the A-LINK row (``reduction_chain_sound``)
under part (ii) only where the run passes ``chain_provenance`` naming every
measured factor AND every part of (ii) that is data holds of the presented
chain: for each factor one link, the id the provenance names, status exact, no
channel supplied as data, the identity outcome correspondence; and an empty
source segment. Each of those is broken here on its own, on the real
one-station flat-instance route, and the row must stay; on the real
two-station route (BBM92, two flat instances) the row is omitted where both
factors are attested and kept where one is not; and the run tier attests
only what it docked.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.support.route_fixtures import preparation

from certiqs_key.domain.chain import (
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
)
from certiqs_key.foundations.exact import identity, scale
from certiqs_key.protocol_compiler import (
    ChainProvenance,
    DirectPovm,
    FactorProvenance,
    ProtocolSpecification,
    compile_specification,
    link_row_discharged,
)
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.reasons import LinkKind
from certiqs_key.runs.chain_provenance import (
    attest_chain_provenance,
)

pytestmark = pytest.mark.contract

LINK_ROW = "reduction_chain_sound"


def _first(
    artifact: ProofReductionArtifact | None,
) -> dict[str, ProofReductionArtifact]:
    """Return the one-station route's artefact, keyed by its default factor label."""
    return {} if artifact is None else {"f0": artifact}


def _route() -> tuple[ProtocolSpecification, ReductionChain, ChainProvenance]:
    prepared, _ = preparation("wpfss-encoded")
    specification = prepared.specification
    assert specification.receiver.factor_label is None
    chain = specification.chain
    assert isinstance(chain, ReductionChain)
    token = attest_chain_provenance(
        specification, _first(prepared.reduction_artifact)
    )
    assert token is not None, "the run attests its own docked flat-instance link"
    return specification, chain, token


def test_the_run_s_token_omits_the_row_and_its_absence_keeps_it() -> None:
    specification, _, token = _route()
    without = compile_specification(specification)
    assert without.refusal is None
    assert LINK_ROW in without.assumption_ledger
    assert not without.link_row_omitted_on_provenance
    with_token = compile_specification(specification, chain_provenance=token)
    assert with_token.refusal is None
    assert LINK_ROW not in with_token.assumption_ledger
    assert with_token.link_row_omitted_on_provenance
    # Nothing else of the ledger moves with the provenance.
    assert [key for key in without.assumption_ledger if key != LINK_ROW] == list(
        with_token.assumption_ledger
    )


def test_the_route_s_chain_meets_every_data_part_of_ii() -> None:
    specification, chain, token = _route()
    assert link_row_discharged(specification, chain, token)
    assert not link_row_discharged(specification, chain, None)


def test_a_non_identity_outcome_correspondence_keeps_the_row() -> None:
    specification, chain, token = _route()
    letters = list(chain.outcome_correspondence)
    swapped = dict(chain.outcome_correspondence)
    swapped[letters[0]], swapped[letters[1]] = letters[1], letters[0]
    assert not link_row_discharged(
        specification, replace(chain, outcome_correspondence=swapped), token
    )


def test_a_two_link_segment_keeps_the_row() -> None:
    specification, chain, token = _route()
    (link,) = chain.receiver_segment
    second = replace(link, link_id="L-after", source_descriptor=link.target_descriptor)
    longer = replace(chain, receiver_segment=(link, second))
    assert not link_row_discharged(specification, longer, token)


def test_a_factor_the_token_does_not_name_keeps_the_row() -> None:
    specification, chain, token = _route()
    # The second factor presents a real segment, so only the token's silence
    # about it (it names f0 alone) can keep the row.
    two = replace(
        specification,
        further_receiver_factors=(replace(specification.receiver, chain=chain),),
    )
    assert not link_row_discharged(two, chain, token)
    (attested,) = token.factors
    both = ChainProvenance(factors=(attested, replace(attested, factor="f1")))
    assert link_row_discharged(two, chain, both)


def test_a_non_empty_source_segment_keeps_the_row() -> None:
    specification, chain, token = _route()
    source_link = ChainLink(
        link_id="S1",
        segment=LinkStage.SOURCE,
        link_type="source-map",
        source_descriptor=SystemDescriptor(name="A'", dim=2, side=Side.ALICE),
        target_descriptor=SystemDescriptor(name="A", dim=2, side=Side.ALICE),
        status=LinkStatus.EXACT,
    )
    with_source = replace(chain, source_segment=(source_link,))
    assert not link_row_discharged(specification, with_source, token)


def test_a_supplied_channel_keeps_the_row() -> None:
    specification, chain, token = _route()
    (link,) = chain.receiver_segment
    dim = link.source_descriptor.dim
    assert dim is not None
    with_channel = replace(link, channel=(identity(dim),))
    supplied = replace(chain, receiver_segment=(with_channel,))
    assert not link_row_discharged(specification, supplied, token)


def test_a_status_other_than_exact_keeps_the_row() -> None:
    specification, chain, token = _route()
    (link,) = chain.receiver_segment
    outer = replace(
        chain, receiver_segment=(replace(link, status=LinkStatus.CERTIFIED_OUTER),)
    )
    assert not link_row_discharged(specification, outer, token)


def test_a_token_naming_another_link_keeps_the_row() -> None:
    specification, chain, token = _route()
    (attested,) = token.factors
    other = ChainProvenance(factors=(replace(attested, link_id="other"),))
    assert not link_row_discharged(specification, chain, other)


def test_band_a_keeps_its_own_omission_and_no_provenance_flag() -> None:
    prepared, _ = preparation("band-a")
    result = prepared.compilation
    assert LINK_ROW not in result.assumption_ledger
    assert not result.link_row_omitted_on_provenance


def test_the_run_attests_nothing_without_its_artefact() -> None:
    specification, _, _ = _route()
    assert attest_chain_provenance(specification, {}) is None


def test_the_run_attests_nothing_where_the_family_is_not_the_read_off() -> None:
    """A presented family that is not exactly the artefact's read-off: no token."""
    prepared, _ = preparation("wpfss-encoded")
    specification = prepared.specification
    family = specification.receiver.physical_povm
    assert isinstance(family, DirectPovm)
    first = family.alphabet[0]
    altered = DirectPovm(
        alphabet=family.alphabet,
        elements={**family.elements, first: scale(2, family.elements[first])},
    )
    changed = replace(
        specification, receiver=replace(specification.receiver, physical_povm=altered)
    )
    artifacts = _first(prepared.reduction_artifact)
    assert attest_chain_provenance(changed, artifacts) is None


def test_the_run_attests_nothing_where_a_factor_has_no_artefact() -> None:
    prepared, _ = preparation("wpfss-encoded")
    specification = prepared.specification
    two = replace(specification, further_receiver_factors=(specification.receiver,))
    assert attest_chain_provenance(two, _first(prepared.reduction_artifact)) is None


def test_the_run_attests_nothing_where_a_link_follows_the_instance_link() -> None:
    """reductions/domination/cor:emitted-dominated squashes another model.

    An artefact chain with a link after the instance link passes no
    provenance.
    """
    prepared, _ = preparation("wpfss-encoded")
    artifact = prepared.reduction_artifact
    assert artifact is not None
    (link,) = artifact.reduction_chain.links
    dominated = replace(link, kind=LinkKind.FAMILY_DOMINATING)
    longer = replace(
        artifact,
        reduction_chain=replace(artifact.reduction_chain, links=(link, dominated)),
    )
    assert attest_chain_provenance(prepared.specification, _first(longer)) is None


# ===========================================================================
#  Two measured factors
# ===========================================================================


def _two_station() -> tuple[ProtocolSpecification, dict[str, ProofReductionArtifact]]:
    prepared, _ = preparation("untrusted-two-station")
    specification = prepared.specification
    assert len(specification.receiver_parts) == 2
    artifacts = {
        str(part.factor_label): emission.reduction
        for part, emission in zip(
            specification.receiver_parts, prepared.device_artifacts, strict=True
        )
    }
    return specification, artifacts


def test_a_two_station_run_whose_links_are_all_discharged_omits_the_row() -> None:
    """``req:link-row-provenance`` (ii) for every measured factor: the row goes."""
    specification, artifacts = _two_station()
    token = attest_chain_provenance(specification, artifacts)
    assert token is not None
    assert {item.factor for item in token.factors} == set(artifacts)
    compiled = compile_specification(specification, chain_provenance=token)
    assert compiled.refusal is None
    assert LINK_ROW not in compiled.assumption_ledger
    assert compiled.link_row_omitted_on_provenance
    # And the run itself passes that token (the pipeline's own compilation).
    prepared, _ = preparation("untrusted-two-station")
    assert LINK_ROW not in prepared.compilation.assumption_ledger


def test_a_two_station_run_with_one_factor_unattested_keeps_the_row() -> None:
    """One factor without the run's word: the row stays for the whole chain."""
    specification, artifacts = _two_station()
    token = attest_chain_provenance(specification, artifacts)
    assert token is not None
    one = ChainProvenance(factors=token.factors[:1])
    chain = specification.chain
    assert isinstance(chain, ReductionChain)
    assert not link_row_discharged(specification, chain, one)
    compiled = compile_specification(specification, chain_provenance=one)
    assert LINK_ROW in compiled.assumption_ledger
    first = next(iter(artifacts))
    assert attest_chain_provenance(specification, {first: artifacts[first]}) is None
    # And without any word the row stays.
    assert LINK_ROW in compile_specification(specification).assumption_ledger


@pytest.mark.parametrize("broken", ["status", "channel", "correspondence", "two links"])
def test_a_second_factor_failing_a_data_part_keeps_the_row(broken: str) -> None:
    """(ii) for every measured factor: a later factor's data are decided too."""
    specification, artifacts = _two_station()
    token = attest_chain_provenance(specification, artifacts)
    assert token is not None
    chain = specification.chain
    assert isinstance(chain, ReductionChain)
    second = specification.further_receiver_factors[0]
    segment = second.chain
    assert isinstance(segment, ReductionChain)
    link = segment.receiver_segment[0]
    gamma = dict(segment.outcome_correspondence)
    first, other = list(gamma)[:2]
    dim = link.source_descriptor.dim
    assert dim is not None
    changed = {
        "status": replace(
            segment,
            receiver_segment=(replace(link, status=LinkStatus.CERTIFIED_OUTER),),
        ),
        "channel": replace(
            segment, receiver_segment=(replace(link, channel=(identity(dim),)),)
        ),
        "correspondence": replace(
            segment,
            outcome_correspondence={
                **gamma, first: gamma[other], other: gamma[first]
            },
        ),
        "two links": replace(segment, receiver_segment=(link, link)),
    }[broken]
    presented = replace(
        specification, further_receiver_factors=(replace(second, chain=changed),)
    )
    assert link_row_discharged(specification, chain, token)
    assert not link_row_discharged(presented, chain, token)


def test_a_factor_provenance_names_its_factor() -> None:
    with pytest.raises(ValueError, match="empty field"):
        FactorProvenance(factor="", artifact_version="reductions@1", link_id="L")
    item = FactorProvenance(factor="f0", artifact_version="reductions@1", link_id="L")
    with pytest.raises(ValueError, match="twice"):
        ChainProvenance(factors=(item, item))
