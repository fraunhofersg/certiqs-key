"""The declared-data parts of premises, decided on the declared numbers.

Three requirements of this module turn a part of a premise that is a property
of the DECLARED DATA into a decision, so that no specification is analysed
under a premise its own numbers already contradict:

* ``req:band-a-ideal-receiver``: the Band-A route rests on A-IDEAL, an ideal
  projective measurement on a qubit (``thm:band-a`` (iv)). The number of
  measured factors, the two dimensions and the projectivity of the declared
  family are data, so a specification on the route that fails one of them is
  refused with ``band_a_outside_ideal_receiver``
  (:func:`decide_band_a_ideal_receiver`). The route itself is recognised by
  :func:`band_a_route`, which in the basic format is :func:`is_band_a`,
  ``def:banda`` read on the record: the SHAPE condition (b) gives the chain.
* ``req:band-a-identity-link``: the clauses of ``def:banda`` (b) the
  recognition leaves open -- the one link supplies its channel as data, its
  outcome correspondence is the identity on ``V = V^ph``, and its target POVM
  is the declared family -- are decided on a specification the route admits.
  The first two here, refusing with ``band_a_link_not_identity``
  (:func:`decide_band_a_identity_link`); the third by condition (C4) of the
  chain stage, which those two make decidable and which then reads
  ``F_v = F^ph_v`` entry for entry (a failure is
  ``chain_interface_condition_failed`` naming (C4), as every (C4) failure is).
* ``req:da1-source-identity``: in trusted-source mode at ``d_A = 1`` no
  source-replacement certificate is demanded, so condition (SR2) of
  ``transmitter/def:srcert`` read at ``d_A = 1``, ``sigma_x = m_x sum_y
  sigma_y``, is decided by nothing else; it is decided here, exactly, and a
  failure is ``da1_source_identity_failed``
  (:func:`decide_da1_source_identity`).

WHY A MODULE OF ITS OWN. All are refusals the compilation map takes BEFORE A
DECLARATION IS EMITTED, on data the map has already read, and none forms
anything the declaration carries; :mod:`certiqs_key.protocol_compiler.compile`
calls them at the stage each one's data are in hand. Keeping them apart keeps
the premises' decisions readable beside each other and out of the
pipeline's own file, which is long enough.

EVERY DECISION IS EXACT. Matrices are the exact Gaussian-rational
:data:`~certiqs_key.foundations.exact.Matrix` of the declared binary64
numbers, products and sums are formed in exact arithmetic, and no tolerance
appears (the interface's ``exact_decisions`` and ``no_snapping``).
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from certiqs_key.domain.families import AliceForm
from certiqs_key.foundations.blocks import Label, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Matrix,
    add,
    dimension,
    direct_sum,
    equal,
    is_diagonal,
    is_square,
    matmul,
    scale,
)
from certiqs_key.protocol_compiler.chain import (
    ChainLink,
    LinkStatus,
    ReductionChain,
)
from certiqs_key.protocol_compiler.reasons import Refusal, RefusalReason
from certiqs_key.protocol_compiler.spec import (
    DirectPovm,
    ProtocolSpecification,
    PublicChoices,
)
from certiqs_key.transmitter.reasons import SourceMode

__all__ = [
    "band_a_link",
    "band_a_route",
    "channel_is_exactly_identity",
    "decide_band_a_ideal_receiver",
    "decide_band_a_identity_link",
    "decide_da1_source_identity",
    "is_band_a",
]


# ---------------------------------------------------------------------------
#  req:band-a-ideal-receiver: the route, and the ideal receiver on it
# ---------------------------------------------------------------------------


def channel_is_exactly_identity(link: ChainLink) -> bool:
    """Whether the link's channel, where it supplies one as data, is the identity.

    ``req:band-a-ideal-receiver``'s link test: "a channel that, where the link
    supplies one as data, is exactly the identity map on its system". A link
    that supplies no channel passes (the requirement asks nothing of it).

    THE DECISION IS EXACT AND IT IS THIS ONE. A Kraus set ``{K_k}`` realises
    the identity map on a ``d``-dimensional system if and only if every
    ``K_k`` is ``c_k 1_d`` and ``sum_k |c_k|^2 = 1``. If: ``sum_k K_k rho
    K_k^dag = (sum_k |c_k|^2) rho = rho``. Only if: the Choi operator of the
    identity map is the rank-one ``|Omega><Omega|``, and every Kraus operator's
    vectorisation lies in its range, which is spanned by ``vec(1_d)``. So each
    operator is decided diagonal with equal diagonal entries, on the system's
    dimension (the link's source descriptor's), and the squared moduli are
    summed over the rationals.
    """
    if link.channel is None:
        return True
    if not link.channel:
        return False
    dim = link.source_descriptor.dim
    total = Fraction(0)
    for operator in link.channel:
        if not operator or not is_square(operator) or len(operator) != dim:
            return False
        if not is_diagonal(operator):
            return False
        scalar = operator[0][0]
        if any(operator[i][i] != scalar for i in range(len(operator))):
            return False
        total += scalar.squared_modulus
    return total == 1


def band_a_link(chain: ReductionChain) -> bool:
    """Whether a receiver segment is the one identity link of ``def:banda`` (b).

    ``req:band-a-ideal-receiver``'s link condition, read on one measured
    factor's chain record: "the receiver segment is one link with status
    exact, equal source and target descriptors, a channel that, where the link
    supplies one as data, is exactly the identity map on its system
    (:func:`channel_is_exactly_identity`), an empty constraint slot and an
    empty licence slot". The source segment and the sector set are the
    specification's and are read by :func:`band_a_route`.
    """
    if len(chain.receiver_segment) != 1:
        return False
    link = chain.receiver_segment[0]
    return (
        link.status is LinkStatus.EXACT
        and link.source_descriptor == link.target_descriptor
        and link.transported_constraints == ()
        and link.license_slot_empty
        and channel_is_exactly_identity(link)
    )


def is_band_a(chain: ReductionChain, sectors: SectorStructure) -> bool:
    """Whether the presented specification is ``def:banda``'s, on the record.

    ``def:banda`` IS A CONJUNCTION and this function decides both conjuncts it
    is given data for. (b): "an empty source segment, ``L_s = 0`` ... and a
    receiver segment of one link, ``L = 1``, ``Lambda_1 = id_Q``, with status
    ``exact``, empty constraint slot and empty licence slot" -- every conjunct
    a slot of :class:`~certiqs_key.domain.chain.ChainLink`, the one link
    mapping ``Q`` to ``Q`` by the descriptor identity and, where the link
    supplies its channel as data, that channel decided exactly the identity
    map (``req:band-a-ideal-receiver``'s link test, :func:`band_a_link`).
    This is the SHAPE of (b), the route's recognition. The clauses of (b) it
    leaves open -- the channel supplied as data, the outcome correspondence
    the identity, the target POVM the declared family -- are decided on a
    specification the route admits, before a declaration is emitted, by
    :func:`decide_band_a_identity_link` and by (C4) of the chain stage
    (``req:band-a-identity-link``), so every EMITTED Band-A declaration
    satisfies (b) in full on its record.
    (a), the half that is a property of the EMITTED
    SECTOR SET: ``S = {s_0}``, a singleton, which
    :attr:`~certiqs_key.protocol_compiler.spec.ProtocolSpecification.sectors`
    carries and which the caller therefore holds.

    THE FUNCTION TAKES THE SECTOR SET AS WELL AS THE CHAIN. Deciding (b) on
    the chain alone would call a specification satisfying (b) over TWO sectors
    Band A, which would name ``A-IDEAL`` and OMIT A-LINK, the soundness of a
    chain a consumer matches keys against. Omitting an assumption understates
    what a declaration rests on, which is the direction PRINCIPLES.md section
    2.1 exists for.

    THE ONE HALF OF (a) THAT STAYS UNDECIDED HERE, AND WHY. (a) also asks that
    the receiver part declare ``{F^ph_w}`` DIRECTLY, "with no characterization
    step and no photon-number structure". That is a fact about the PROVENANCE
    of the family -- whether a receiver-characterization module produced it --
    and ``def:spec`` (c) hands this module a chain record and a POVM
    presentation, neither of which carries its own history: a directly declared
    family and a characterized one that happens to have been flattened into one
    exact identity link over a singleton sector set are the same record here.

    WHERE THAT RESIDUE BITES -- a receiver that WAS characterized upstream,
    presented through a chain that satisfies (b) over a singleton -- this
    function answers Band A and ``A-IDEAL`` is named (an OVERstatement, and
    safe). The family so declared rests on A-SPEC, the specification describing
    the apparatus, which this module emits on every route. This module emits
    no row of ``reductions/ass:recv`` (A-RECV) on any route: the supplier
    premise is the reductions artefact's own row, emitted or omitted there
    (``reductions/req:recv-row-provenance``), and the run tier reads that
    module's own ledger off each reductions artefact it consumed
    (spec/architecture.md 4.4).

    WHERE IT IS READ. On a specification the reading is
    :func:`band_a_route`, which in the basic format IS this function on the
    specification's chain and its sector set, and in the general format reads
    the joint sector set and every measured factor's chain
    (``req:band-a-ideal-receiver``). Every consumer reads the route: the
    ledger rows whose presence rules are complementary. ``A-IDEAL``'s is
    "BAND A ONLY" by its own title, and A-LINK's is "everywhere but Band A"
    (the interface's ``assumption_ledger.emission_rule``) but for the in-run
    instance link of ``req:link-row-provenance`` (ii): in Band A no emitted
    slot depends on an artefact of the receiver or reductions module, and the
    residual physical content is A-IDEAL (``thm:band-a`` (iv)).
    """
    if len(sectors.labels) != 1:
        return False
    if chain.source_segment:
        return False
    return band_a_link(chain)


def band_a_route(specification: ProtocolSpecification) -> bool:
    """Whether the specification is on the Band-A route, as the record shows it.

    ``req:band-a-ideal-receiver``: "The engine takes the Band A route, reading
    conditions (b) and the sector clause of (a) of Definition def:banda on the
    record, for a specification whose source segment is empty, whose emitted
    sector set (in the general format, the joint one) is a singleton, and in
    which, FOR SOME MEASURED FACTOR, the receiver segment is [the identity
    link]; it decides the link condition on the chain record of EVERY
    measured factor."

    THE SECTOR SET IS THE EMITTED ONE (in the general format the joint one,
    :func:`_emitted_sectors_singleton`). THE LINK TEST RUNS PER FACTOR: the
    first factor's segment is the specification's chain, a further factor's
    its own ``ReceiverPart.chain`` (``def:spec`` (c')), as the compilation
    reads them. A specification whose route this answers but which declares
    more than one measured factor is refused by
    :func:`decide_band_a_ideal_receiver` (i), so on every EMITTED declaration
    this answer and :func:`is_band_a` on the first chain and the emitted
    sector set agree.

    IN THE BASIC FORMAT THE ROUTE IS :func:`is_band_a` itself, on the
    specification's chain and its emitted sector set
    (:attr:`~certiqs_key.protocol_compiler.spec.ProtocolSpecification.sectors`):
    there is one measured factor and its chain is the specification's, so
    ``def:banda``'s reading on the record is what every consumer of the
    route reads.
    """
    chain = specification.chain
    if not isinstance(chain, ReductionChain):
        return False
    if not specification.is_general_format:
        return is_band_a(chain, specification.sectors)
    if chain.source_segment:
        return False
    if not _emitted_sectors_singleton(specification, chain):
        return False
    return any(
        isinstance(factor_chain, ReductionChain) and band_a_link(factor_chain)
        for factor_chain in _factor_chains(specification, chain)
    )


def _factor_chains(
    specification: ProtocolSpecification, chain: ReductionChain
) -> tuple[object, ...]:
    """Return each measured factor's chain record, in the factors' order."""
    return tuple(
        chain if position == 0 else part.chain
        for position, part in enumerate(specification.receiver_parts)
    )


def _emitted_sectors_singleton(
    specification: ProtocolSpecification, chain: ReductionChain
) -> bool:
    """Whether the joint emitted sector set of a general-format specification is one.

    Called in the general format only: in the accepted format the emitted set
    is :attr:`ProtocolSpecification.sectors`, "supplied by the last link's
    target descriptor", and :func:`band_a_route` reads it through
    :func:`is_band_a`. In the general format that slot holds the first
    factor's map and is not read (``def:compile`` derives the product map
    from the factor list), so the JOINT set ``T x S`` is read off what it is
    derived from: a singleton exactly when Alice's sector set ``T`` and every
    measured factor's sector map, read off its last link's target descriptor as the
    compilation reads it, are each a singleton. A factor whose chain carries
    no sector map is not a singleton here; the compilation refuses it as
    malformed later.
    """
    if specification.source.alice_sectors.count != 1:
        return False
    for factor_chain in _factor_chains(specification, chain):
        if not isinstance(factor_chain, ReductionChain):
            return False
        if not factor_chain.receiver_segment:
            return False
        sectors = factor_chain.receiver_segment[-1].target_descriptor.sector_map()
        if sectors is None or sectors.count != 1:
            return False
    return True


def _first_non_projector(elements: tuple[Matrix, ...]) -> int | None:
    """Return the 1-based index of the first element with ``F F != F``, or None."""
    for index, element in enumerate(elements, start=1):
        if not equal(matmul(element, element), element):
            return index
    return None


def decide_band_a_ideal_receiver(
    specification: ProtocolSpecification,
) -> Refusal | None:
    """Refuse a Band-A specification outside the ideal qubit receiver, or None.

    ``req:band-a-ideal-receiver``. On the route (:func:`band_a_route`) the
    specification is refused with ``band_a_outside_ideal_receiver``, before a
    declaration is emitted, naming the first clause that fails, unless

    (i) it declares exactly one measured factor;
    (ii) that factor's physical receiver system has dimension two and, in
        trusted-source mode, the transmitted system of the transmitter
        artefact has dimension two; and
    (iii) that factor's physical receiver family as presented is projective,
        decided exactly: presented directly, every element satisfies
        ``F F = F``; presented choice-weighted, every element of every
        declared conditional family satisfies ``N N = N`` (``def:weighted``).
        The refusal names the choice value where there is one and the outcome
        index of the first element that is not a projector.

    THE TRANSMITTED SYSTEM IS READ AS THE ARTEFACT'S ``A^v``. The route has an
    empty source segment on the chain record, and the compilation decides
    before this call that the artefact's typed segment is the chain's
    (``source_segment_not_from_admitting_module`` otherwise, also where the
    chain's is empty), so on every specification this decision is taken for
    the artefact's segment is empty too. There the virtual transmitted system
    IS the specified one (``transmitter/def:srcert``, "One reading at every
    L_s"; the transmitter decides that identity where it holds both pairs),
    so :attr:`~certiqs_key.protocol_compiler.spec.SourcePart.transmitted_dim`
    is the transmitted system's dimension here. Called directly, outside the
    compilation, on a specification whose artefact carries a segment the
    chain does not, it reads ``A^v`` as it stands.

    Exact admissibility of the same family is decided first, on every route
    (``req:physical-family-decision``); the caller takes this decision after
    that one and before any condition of the chain.
    """
    if not band_a_route(specification):
        return None
    parts = specification.receiver_parts

    def refusing(clause: str, detail: str) -> Refusal:
        return Refusal(
            reason=RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER,
            detail=(
                f"the specification is on the Band-A route (def:banda read on "
                f"the record) and clause {clause} of req:band-a-ideal-receiver "
                f"fails: {detail}. The route rests on A-IDEAL, an ideal "
                "projective qubit measurement; declare such a receiver through "
                "the receiver module and a squashing reduction"
            ),
        )

    if len(parts) != 1:
        return refusing(
            "(i)",
            f"it declares {len(parts)} measured factors, and the route admits "
            "exactly one",
        )
    part = parts[0]
    if part.physical_dim != 2:
        return refusing(
            "(ii)",
            f"the physical receiver system has dimension {part.physical_dim}, not two",
        )
    source = specification.source
    if source.source_mode is SourceMode.TRUSTED and source.transmitted_dim != 2:
        return refusing(
            "(ii)",
            "in trusted-source mode the transmitted system of the transmitter "
            f"artefact has dimension {source.transmitted_dim}, not two",
        )
    presentation = part.physical_povm
    if isinstance(presentation, DirectPovm):
        failed_at = _first_non_projector(presentation.ordered())
        if failed_at is not None:
            return refusing(
                "(iii)",
                f"element {failed_at} of the physical receiver family's declared "
                f"order, F^ph_{presentation.alphabet[failed_at - 1]}, is not a "
                "projector (F F != F, decided exactly)",
            )
        return None
    assert isinstance(presentation, PublicChoices)
    for choice in presentation.choices:
        outcomes = presentation.conditional_alphabets[choice]
        family = presentation.conditional_elements[choice]
        failed_at = _first_non_projector(tuple(family[u] for u in outcomes))
        if failed_at is not None:
            return refusing(
                "(iii)",
                f"at choice value {choice!r}, element {failed_at} of the "
                f"conditional family's declared order, "
                f"N_{{{outcomes[failed_at - 1]}|{choice}}}, is not a projector "
                "(N N != N, decided exactly)",
            )
    return None


# ---------------------------------------------------------------------------
#  req:band-a-identity-link: the route's one link, decided the identity
# ---------------------------------------------------------------------------


def decide_band_a_identity_link(
    specification: ProtocolSpecification,
    physical_alphabet: tuple[Label, ...],
) -> Refusal | None:
    """Refuse a Band-A specification whose one link is not decided the identity.

    ``req:band-a-identity-link``. For a specification on the route
    (:func:`band_a_route`) that :func:`decide_band_a_ideal_receiver` does not
    refuse, decided on the chain record of its one measured factor, before a
    declaration is emitted:

    (i) the one link of that factor's receiver segment supplies its channel
        as data -- which the recognition (:func:`band_a_link`, through
        :func:`channel_is_exactly_identity`) has then decided to be exactly
        the identity map on its system; and
    (ii) the segment's outcome correspondence is the identity: the physical
        receiver alphabet ``V^ph`` and the alphabet ``V`` of the link's
        target POVM are one set, and ``gamma(w) = w`` for every ``w`` in
        ``V^ph``.

    A failure is refused with ``band_a_link_not_identity``, naming the first
    clause that fails.

    THE TARGET-POVM CLAUSE OF ``def:banda`` (b) IS NOT COMPARED HERE. With
    both clauses passed, condition (C4) of ``def:chaincond`` is decidable
    (the link supplies its channel) and, at the identity channel and the
    identity correspondence, reads ``F_v = F^ph_v`` for every ``v``, entry
    for entry, ``{F^ph_w}`` being the physical family as the chain stage
    reads it (the family of products ``def:weighted`` forms, where it is
    presented choice-weighted). :func:`~certiqs_key.protocol_compiler.chain.check_chain`
    decides (C4) on every chain whose links supply their channel, Band A
    included, and refuses its failure with ``chain_interface_condition_failed``
    naming (C4); a second comparison here would give one failure two names.

    ``physical_alphabet`` IS ``V^ph`` AS THE CHAIN STAGE READS IT: the
    alphabet of the physical family the caller resolved and hands to (C2)
    and (C4) (the joint alphabet ``sqcup_t U_t x {t}`` of a choice-weighted
    presentation). Taking it from the caller keeps the two decisions on one
    alphabet. THE CALLER TAKES THIS DECISION after
    :func:`decide_band_a_ideal_receiver`, whose clause (i) has refused every
    count of measured factors but one, and before the chain stage; called on
    a specification with more than one measured factor it decides nothing.
    """
    if not band_a_route(specification):
        return None
    if len(specification.receiver_parts) != 1:
        return None
    chain = specification.chain
    assert isinstance(chain, ReductionChain)  # band_a_route read it as one
    (link,) = chain.receiver_segment

    def refusing(clause: str, detail: str) -> Refusal:
        return Refusal(
            reason=RefusalReason.BAND_A_LINK_NOT_IDENTITY,
            detail=(
                f"the specification is on the Band-A route (def:banda read on "
                f"the record) and clause {clause} of req:band-a-identity-link "
                f"fails: {detail}. On the route the link-soundness premise "
                "A-LINK is proved (thm:band-a (v)), which needs the one link "
                "given as the identity map, keeping the outcomes as they are "
                "and delivering the declared measurement; give the link its "
                "channel as data with the identity outcome correspondence, or "
                "declare the reduction through the reductions module"
            ),
        )

    if not link.channel_supplied:
        return refusing(
            "(i)",
            f"link {link.link_id!r} of the receiver segment names its channel "
            "but supplies none as data, so condition (C4) cannot be decided "
            "and nothing ties the measurement it delivers to the declared one",
        )
    target_alphabet = link.target_alphabet or ()
    if set(physical_alphabet) != set(target_alphabet):
        only_physical = [w for w in physical_alphabet if w not in target_alphabet]
        only_target = [v for v in target_alphabet if v not in physical_alphabet]
        return refusing(
            "(ii)",
            "the physical receiver alphabet V^ph and the alphabet V of the "
            "link's target POVM are not one set (in V^ph only: "
            f"{only_physical}; in V only: {only_target})",
        )
    gamma = chain.outcome_correspondence
    for outcome in physical_alphabet:
        if outcome not in gamma:
            return refusing(
                "(ii)",
                f"the outcome correspondence gamma assigns nothing to the "
                f"physical outcome {outcome!r}",
            )
        if gamma[outcome] != outcome:
            return refusing(
                "(ii)",
                f"the outcome correspondence maps the physical outcome "
                f"{outcome!r} to {gamma[outcome]!r}, not to itself",
            )
    return None


# ---------------------------------------------------------------------------
#  req:da1-source-identity: (SR2) read at d_A = 1
# ---------------------------------------------------------------------------


def _weighted_members(specification: ProtocolSpecification) -> dict[Label, Matrix]:
    """Return ``sigma_x`` of the virtual ensemble the artefact emits, per letter.

    ``req:da1-source-identity``: "``sigma_x = p_x rho^v_x`` is the weighted
    member for ``x`` of the virtual ensemble the transmitter artefact emits
    ... where the artefact emits the ensemble by its weighted members,
    ``sigma_x`` is the declared member". So the declared blocks are read
    where the artefact carries them (their direct sum, the one matrix the
    blocks are of), and otherwise the product ``p_x rho^v_x`` is formed in
    exact arithmetic.
    """
    artifact = specification.source.artifact
    blocks = artifact.virtual_ensemble_blocks
    members: dict[Label, Matrix] = {}
    for label in specification.source.alphabet:
        if blocks is not None:
            members[label] = direct_sum(list(blocks[label]))
            continue
        states = artifact.virtual_ensemble_states
        if label not in states or label not in artifact.virtual_ensemble_weights:
            raise MalformedInputError(
                f"the transmitter artefact emits no virtual ensemble member for "
                f"letter {label!r}: neither its weighted members nor a weight "
                "and a state (the interface's virtual_ensemble row)"
            )
        members[label] = scale(artifact.virtual_ensemble_weights[label], states[label])
    return members


def _measurement_weights(
    specification: ProtocolSpecification, alice_elements: Mapping[Label, Matrix]
) -> dict[Label, Matrix]:
    """Return Alice's element per letter, as the declaration carries it.

    ``req:da1-source-identity``: ``m_x`` is "the one entry of Alice's
    measurement element ``M_x``, read as the declaration carries it (for a
    choice-weighted family the weighted element the engine forms; in the
    ensemble form, ``N_x``, which equals ``M_x`` at ``d_A = 1``)". The POVM
    form's elements are the caller's resolved family (the weighted one where a
    choice is presented); the ensemble form's are the slot's block lists,
    read as the one matrix they are.
    """
    source = specification.source
    if source.alice_form is AliceForm.ENSEMBLE:
        slot = source.alice_slot
        assert slot is not None  # the ensemble form always has its slot
        return {
            label: direct_sum(list(member.blocks))
            for label, member in zip(slot.alphabet, slot.members, strict=True)
        }
    missing = [label for label in source.alphabet if label not in alice_elements]
    if missing:
        raise MalformedInputError(
            f"Alice's resolved family has no element for letter(s) {missing} of "
            "the signal alphabet X, which arrives ordered with the source part "
            "(def:spec (a)); no identity can be read against it"
        )
    return {label: alice_elements[label] for label in source.alphabet}


def decide_da1_source_identity(
    specification: ProtocolSpecification, alice_elements: Mapping[Label, Matrix]
) -> Refusal | None:
    """Refuse a trusted ``d_A = 1`` specification whose emission depends on the letter.

    ``req:da1-source-identity``. In trusted-source mode at ``d_A = 1``, for
    every ``x`` in the declared order and exactly on the declared numbers,
    the identity ``sigma_x = m_x sum_y sigma_y`` is decided entry by entry;
    a failure refuses with ``da1_source_identity_failed``, naming the first
    such letter and the first entry at which the two sides differ.

    It is (SR2) of ``transmitter/def:srcert`` read at ``d_A = 1``, where no
    certificate is demanded and so nothing else decides it. Its trace is
    ``m_x = p_x``; on a letter with ``p_x > 0`` it says the emitted state is
    one common state. In untrusted-source mode no source premise is emitted
    and there is nothing to compare, so nothing is decided; at ``d_A >= 2``
    the certificate carries the condition (gate (G2)). A one-letter
    specification satisfies it whenever its data are normalised, and is
    decided anyway: the rule has no exception.

    ``alice_elements`` is the POVM-form family the compilation map resolved
    (unused in ensemble form, where the slot is read).
    """
    source = specification.source
    if source.source_mode is not SourceMode.TRUSTED or source.alice_dim != 1:
        return None
    members = _weighted_members(specification)
    weights = _measurement_weights(specification, alice_elements)
    total: Matrix | None = None
    for label in source.alphabet:
        member = members[label]
        total = member if total is None else add(total, member)
    assert total is not None  # an alphabet is non-empty
    for label in source.alphabet:
        element = weights[label]
        if dimension(element) != 1:
            raise MalformedInputError(
                f"Alice's element for letter {label!r} acts on dimension "
                f"{dimension(element)} where d_A = 1"
            )
        expected = scale(element[0][0], total)
        member = members[label]
        if equal(member, expected):
            continue
        row, column = next(
            (i, j)
            for i in range(len(member))
            for j in range(len(member[0]))
            if member[i][j] != expected[i][j]
        )
        return Refusal(
            reason=RefusalReason.DA1_SOURCE_IDENTITY_FAILED,
            detail=(
                "in trusted-source mode at d_A = 1 the identity sigma_x = m_x "
                f"sum_y sigma_y fails at letter {label!r}, first at entry "
                f"({row + 1}, {column + 1}): sigma_x there is "
                f"{member[row][column]} and m_x sum_y sigma_y is "
                f"{expected[row][column]}, with m_x = {element[0][0]} "
                "(req:da1-source-identity; (SR2) of transmitter/def:srcert "
                "read at d_A = 1). Alice's letter weights must equal the "
                "source's and every letter of positive weight must be sent as "
                "the same state; a source whose emitted state depends on the "
                "letter is declared with d_A >= 2 and a source-replacement "
                "certificate"
            ),
        )
    return None
