r"""The machine vocabulary of this module: refusal reasons, rows, ledger keys.

EVERY REFUSAL-REASON STRING HERE IS THE INTERFACE'S, VERBATIM
================================================================================
The contract fixes every refusal-reason string itself: five
tabulars naming THIRTY-ONE strings across TWENTY-NINE rows. Three rows name two
reasons each (the chain row, the constraint-certificate row, the licence-presence
row), AND ONE REASON is named by TWO DIFFERENT ROWS --
``constraint_without_certificate``, by the constraint-certificate row and by the
licensed-route Hermiticity row -- so the two counts do not determine each other.

``requested_assurance_unknown`` IS A REQUEST NAMING A VALUE THAT IS NOT ONE OF
THE TIERS. The ladder is the three tiers of foundations/def:tiers, ``certified``
among them (PRINCIPLES.md section 10), so there is no shelved rung for a request to
name; the row is stated positively ("The requested assurance is one of the three tiers
of foundations/def:tiers"), and anything else is refused with this reason.

THE ``certified_outer`` LINK STATUS IS NOT THAT TIER AND IS KEPT EVERYWHERE.
It is the tag saying a squashing relation holds only up to an error term; this
module refuses to emit it because no theorem of its own converts an error term
into a security penalty, which is a different statement from the platform's
``certified`` assurance tier. It lives in
:class:`certiqs_key.domain.chain.LinkStatus`.

THE CORE KEEPS A REGISTRY; A SUBMODULE ADDS ITS OWN ROW
================================================================================
Spelling the reasons, the fail-closed rows and the assumption
ids as three ``StrEnum``s WOULD NOT BE EXTENSIBLE. This module is a core
with submodules, and a submodule owns rows of its own: ``wpfss``
owns the six rows about the weight route and the dark-count matrix, and a
branching submodule owns the one about its model. Deleting a removable
submodule must leave the package importable and every remaining test green,
so the core may not name its rows.

THE MECHANISM, AND THERE IS EXACTLY ONE. A fail-closed row is a
:class:`FailClosedRow` record -- its name, its ORDER in the interface's own
table, and the reasons it can produce -- and :func:`register_row` puts it in one
registry. The core registers its twenty-one at import; each submodule registers
its own at import of its package. The ORDER FIELD is what lets a submodule's row
sit between two core rows without the core naming it: the table runs 1 lattice,
2 assurance, 3 receiver, then a submodule's cutoff at 4, then 5 blocks, 6
admissibility and 7 the emitted family, then five weight-route rows at 8-12 and
a branching model's at 13 and a sixth weight-route row at 14, then the core's
15-23, a weight-route row at 24 and the core's 25-28; :func:`registered_rows`
returns whatever is registered sorted by that field. Registration is IDEMPOTENT
and refuses a conflicting re-registration, so the registry cannot silently
acquire two readings of one row.

WHAT THE REGISTRY IS NOT USED FOR. It does NOT decide which rows a given
reduction reports: that is the core's rows plus the ones THE BUILDER DECLARES,
assembled per call in :mod:`certiqs_key.reductions.emit`, so a report never
depends on which submodules happen to have been imported. The registry answers
one question -- "which reasons can row ``r`` produce?" -- for the machine record
of a rule outcome, and a submodule's row is registered whenever its builder can
be reached.

A REFUSAL IS A RECORD AND NEVER AN EXCEPTION
============================================
"Every failed validation produces a refusal with a machine-readable reason and
NO ARTIFACT." :class:`Refusal` is that record. The exceptions of
:mod:`certiqs_key.reductions.errors` are for arguments no rule can be read
against, which is a different statement and must stay distinguishable: a caller
must not be able to turn a refusal into an exception or an exception into a
reason code.

THE VOCABULARIES BELOW ARE THE CONTRACT'S TOO
=============================================
The nine link kinds, the two stages, the three statuses, the two routes and the
three certificate cases are all enumerated by the claims.
:data:`LINK_KINDS_DEFERRED` and :data:`LINK_STATUS_EMITTED` record what this
version refuses and what it emits.

THE NULL SOURCE MODE IS DECIDED HERE
====================================
The interface types ``source_mode`` as "``tau_A`` or ``nomarg``" with type
"state or null" and "FIXES NO MACHINE STRING: a ``null`` YAML value, the literal
string ``none``, and a ``nomarg`` enum member all satisfy the row."
:class:`SourceMode` spells the two MODES ``def:licensed`` does fix as
``trusted`` and ``untrusted``, which is what the frozen oracle registry also
carries, and the untrusted mode is represented by the enum member
:attr:`SourceMode.UNTRUSTED` rather than by ``None``. THE REASON IS THAT A
MISSING MARGINAL AND AN UNTRUSTED SOURCE ARE THE SAME DECLARATION HERE and a
``None`` would make "the caller did not say" and "the caller said untrusted"
indistinguishable -- and the fail-closed convention says no default is
substituted for a missing datum. The trusted mode carries the declared
``tau_A`` beside it; the untrusted mode carries nothing, because
``def:licensed`` types its right-hand sides as real numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from certiqs_key.domain.chain import LinkStage, LinkStatus
from certiqs_key.domain.claim_closure import never_verified
from certiqs_key.foundations.errors import MalformedInputError

__all__ = [
    "ASSUMED_FROM_FOUNDATIONS",
    "ASSUMED_FROM_THE_TRANSMITTER",
    "ASSUMPTION_MACHINE_KEYS",
    "CERTIFICATE_KINDS",
    "CORE_ASSUMPTIONS",
    "CORE_FAIL_CLOSED_ROWS",
    "CORE_REFUSAL_REASONS",
    "INHERITED_KEY_WITH_A_DECLARED_RECORD",
    "LINK_KINDS_DEFERRED",
    "LINK_KINDS_IMPLEMENTED",
    "LINK_STATUS_EMITTED",
    "NEVER_VERIFIED",
    "OMITTED_ON_RECEIVER_PROVENANCE",
    "PRESENT_ONLY_WHERE_A_BLOCK_RESTS_ON_A_SNAP",
    "PRESENT_ONLY_WITH_A_NON_EMPTY_CONSTRAINT_LIST",
    "PRESENT_ONLY_WITH_A_NON_EMPTY_SOURCE_SEGMENT",
    "PRESENT_ONLY_WITH_A_PRIVATE_SETTING",
    "PRESENT_ONLY_WITH_A_SETTING_OR_A_CHOICE",
    "SNAPPED_MEASUREMENT_ROW",
    "AssumptionId",
    "AssumptionRow",
    "CertificateKind",
    "FailClosedRow",
    "FailClosedRule",
    "LinkKind",
    "LinkStage",
    "LinkStatus",
    "Refusal",
    "RefusalReason",
    "Relation",
    "Route",
    "SourceMode",
    "fail_closed_rules",
    "ledger_row",
    "reasons_of",
    "register_row",
    "registered_rows",
]


class RefusalReason(StrEnum):
    """The THIRTY core refusal-reason strings, in the interface's row order.

    A submodule's own refusal string is spelled in the submodule's package,
    and a test asserts that the union is exactly the interface's.

    ``requested_assurance_unknown`` names a request for a value that is not a
    tier. See the module docstring.
    """

    # --- the lattice and the requested rung, decided before anything ------
    #: FIRST IN THE SECTION. spec/architecture.md 2.9, condition (D-LAT): "the
    #: producer declares kappa, THERE IS NO DEFAULT AND NO FALLBACK, and a
    #: defaulted lattice would decide a security-relevant predicate on nobody's
    #: authority." The second inequality of the row --
    #: kappa + ceil(log2 max{|V|, |Y|, |T|}) <= 53, Eq. eq:latsumcond -- is
    #: "REFUSED UNDER THE SAME REASON".
    LATTICE_EXPONENT_NOT_DECLARED = "lattice_exponent_not_declared"
    #: No rung is
    #: shelved (the three tiers of foundations/def:tiers are all live), so what
    #: the row refuses is a request naming a value that is not one of them.
    #: "REFUSED RATHER THAN DEMOTED, a silent demotion being a caller receiving
    #: a weaker claim than it asked for without being told."
    REQUESTED_ASSURANCE_UNKNOWN = "requested_assurance_unknown"

    # --- the receiver artifact, the cutoff and the declared blocks --------
    RECEIVER_SPEC_NOT_ACCEPTED = "receiver_spec_not_accepted"
    CUTOFF_MISMATCH = "cutoff_mismatch"
    NO_BLOCK_STRUCTURE = "no_block_structure"
    #: ``def:exactadm`` (c): the declared receiver blocks -- and they alone --
    #: are exactly Hermitian, exactly positive semidefinite, exactly complete
    #: over Y at each (t, m), with that declared-order sum rounding nowhere and
    #: every entry on the lattice Eq. eq:latinv. "DECIDED AND NOT MEASURED...
    #: THE REFUSAL NAMES WHICH ONE FAILED, and NO WINDOW APPEARS ANYWHERE."
    DECLARATION_NOT_EXACTLY_ADMISSIBLE = "declaration_not_exactly_admissible"
    #: THE ONLY REASON OF THIS ENUM WHOSE SUBJECT IS THIS MODULE'S OWN NUMBERS.
    #: Theorem ``thm:emit`` (ii): the family about to be emitted satisfies all
    #: six (D-EMIT) conditions of spec/architecture.md 2.9, decided after the
    #: emission normalizer of ``def:emitnorm`` acted -- a DEFENSIVE exact
    #: check that no path of the normalizer reaches on admitted data -- and,
    #: under the strict option, every moved class is refused under it too
    #: where no reference companion is formed (``req:emission-refusal``).
    #: "THE REFUSAL NAMES THE PREDICATE THAT FAILED".
    EMITTED_FAMILY_NOT_ADMISSIBLE = "emitted_family_not_admissible"

    # --- the fibre condition and the dark-count matrix R (wpfss's rows) ---
    BOUND_SET_NOT_A_FIBRE = "bound_set_not_a_fibre"
    DARK_COUNTS_NOT_COLUMN_STOCHASTIC = "dark_counts_not_column_stochastic"
    DARK_COUNTS_DO_NOT_DESCEND = "dark_counts_do_not_descend"
    BOUNDED_LETTER_NOT_ABSORBING = "bounded_letter_not_absorbing"
    TOTAL_WEIGHT_NOT_BELOW_ONE = "total_weight_not_below_one"

    # --- the routed weights, the probe and the relations ------------------
    HIGH_PHOTON_SLOT_ILL_FORMED = "high_photon_slot_ill_formed"
    PROBE_WEIGHTS_ILL_FORMED = "probe_weights_ill_formed"
    DECLARED_RELATION_IMPOSSIBLE = "declared_relation_impossible"
    CHAIN_ILL_FORMED = "chain_ill_formed"
    SOURCE_LINK_AFTER_RECEIVER_LINK = "source_link_after_receiver_link"
    LINK_KIND_DEFERRED = "link_kind_deferred"
    APPROXIMATE_SQUASHING_UNSUPPORTED = "approximate_squashing_unsupported"
    DEVICE_FAMILY_UNSUPPORTED = "device_family_unsupported"
    CONSTRAINT_WITHOUT_CERTIFICATE = "constraint_without_certificate"
    DATA_DEPENDENT_CONSTANT = "data_dependent_constant"
    LICENCE_MISSING = "licence_missing"
    LICENCE_WITHOUT_CONSTRAINTS = "licence_without_constraints"
    ROUTE_NOT_SINGLE_VALUED = "route_not_single_valued"
    CONSTRAINT_CHANNEL_MISMATCH = "constraint_channel_mismatch"
    ALPHABET_OR_ORDER_MISMATCH = "alphabet_or_order_mismatch"
    POST_PROCESSING_ORDER_VIOLATED = "post_processing_order_violated"
    UNSOUND_CONSTRAINT_REQUESTED = "unsound_constraint_requested"

    # --- the normalized receiver as a branch (wpfss's row, after the freeze)
    #: ``wpfss/req:normalized-branch-refusal``: an artefact that embeds the
    #: flat instance as a branch of a branching instance reads only a receiver
    #: artefact compiled at the factored loss t = 1, and refuses one at t < 1.
    #: ``wpfss/cor:normalized-flat`` absorbs the loss for the flat instance on
    #: the channel system; beside other branches no claim moves it in front.
    NORMALIZED_RECEIVER_IN_BRANCH = "normalized_receiver_in_branch"


#: The THIRTY, in the order the interface's tables introduce them. A
#: submodule's reasons are its own; the union is asserted by a golden test.
CORE_REFUSAL_REASONS: Final[tuple[str, ...]] = tuple(
    str(reason) for reason in RefusalReason
)


@dataclass(frozen=True, slots=True)
class Refusal:
    """The record a failed validation rule produces, INSTEAD OF an artifact.

    ``reason`` is the machine-readable field and the load-bearing one; ``rule``
    names the fail-closed row that decided it, and ``detail`` names the
    offending declared datum in prose for a human reading a refusal. A refusal
    is emitted instead of an artifact, never beside one.

    BOTH FIELDS ARE TYPED ``str`` AND NOT AN ENUM MEMBER, because a submodule's
    reason and a submodule's row are its own strings: the core may not name
    them and a core-typed enum could not hold them.
    """

    reason: str
    rule: str
    detail: str

    def as_machine_record(self) -> dict[str, str]:
        """Return the refusal as a machine record."""
        return {"reason": str(self.reason), "rule": self.rule, "detail": self.detail}


class LinkKind(StrEnum):
    """The NINE link kinds, in the interface's own order."""

    IDENTITY = "identity"
    FSS = "fss"
    WPFSS = "wpfss"
    REGISTER_MIXTURE = "register-mixture"
    FLAGS_ENOUGH = "flags-enough"
    PINCHING = "pinching"
    SOURCE_MAP = "source-map"
    FAMILY_DOMINATING = "family-dominating"
    LABEL_SPACE = "label-space"


#: The six kinds this version implements, in the interface's order.
#: ``family-dominating`` is the ``domination`` submodule's kind
#: (``domination/def:domination-link``; its interface's ``link_kinds``), which
#: no requirement emits: it is in the vocabulary and is built nowhere, and the
#: chain row refuses a request that declares it.
LINK_KINDS_IMPLEMENTED: Final[tuple[LinkKind, ...]] = (
    LinkKind.IDENTITY,
    LinkKind.FSS,
    LinkKind.WPFSS,
    LinkKind.REGISTER_MIXTURE,
    LinkKind.FLAGS_ENOUGH,
    LinkKind.PINCHING,
)

#: The kinds that are declared, reserved and REFUSED in this version, under
#: ``link_kind_deferred`` (``req:reserved-link-kinds``): the core's reserved
#: receiver-stage kind ``label-space``, and ``source-map``, the transmitter's
#: source-stage kind, which this module does not declare.
LINK_KINDS_DEFERRED: Final[tuple[LinkKind, ...]] = (
    LinkKind.SOURCE_MAP,
    LinkKind.LABEL_SPACE,
)

#: ``certified_outer`` and ``exploratory_numeric`` are NEVER emitted by this
#: version. A request for either is refused with
#: ``approximate_squashing_unsupported``, because Theorem ``thm:transfer`` has
#: no penalty slot. THE STATUS IS NOT THE DROPPED ASSURANCE TIER; see
#: :mod:`certiqs_key.domain.chain`.
LINK_STATUS_EMITTED: Final[tuple[LinkStatus, ...]] = (LinkStatus.EXACT,)


class Route(StrEnum):
    """Which route a request takes. EXACTLY ONE VALUE PER REQUEST.

    ``encoded`` is the DEFAULT: the weights go into ``{F_v}`` and the
    constraint list is empty. ``licensed``: the weights travel as the
    constraint entry of Corollary ``cor:fssinstance`` under the licence of
    Theorem ``thm:licence``. ``both`` is REFUSED and is deliberately NOT a
    member here -- a caller naming it names a value outside this enum, and the
    refusal ``route_not_single_valued`` is what it gets. The reason is Remark
    ``rem:tworoutes``: the two routes run on DIFFERENT CHANNELS, so one
    artifact carrying both would admit the cross-channel pairing of
    Eq. ``eq:crosspairing``, which is unsound.
    """

    ENCODED = "encoded"
    LICENSED = "licensed"


class SourceMode(StrEnum):
    """Definition ``def:licensed``: which class the emitted entries are typed in.

    The module docstring says how the null spelling is decided and why. In
    ``trusted`` mode ``Theta_k = c_k tau_A``; in ``untrusted`` mode
    ``Theta_k = c_k`` is a real number.
    """

    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class Relation(StrEnum):
    """``bowtie_k`` of Definition ``def:attset``, in the OPERATOR spelling.

    The split in the consuming contract runs between two LEVELS and not between
    the two source modes, and "this contract states operator conditions
    throughout and so uses the operator spelling, and EVERYTHING IT EMITS
    (>= with c = 0; = with c = q_t) IS ADMITTED UNDER EITHER". The wire
    spelling is :class:`certiqs_key.domain.constraints.Relation`, which spells
    the same three relations as words.
    """

    LE = "<="
    EQ = "="
    GE = ">="


class CertificateKind(StrEnum):
    """The three cases of Corollary ``cor:pullback`` that discharge an entry.

    Corollary ``cor:transported`` closes with: "EVERY CONSTRAINT THIS MODULE
    EMITS IS OF CASE (i)" -- certified, holding "on EVERY reachable state
    whatever the adversary is allowed to send" -- as against case (ii),
    assumed, which "is sound only for the ``S^ph`` it was assumed on". The
    three kinds below are the three certificate cases WITHIN case (i).
    """

    IDENTITY = "identity"
    POSITIVITY = "positivity"
    SPECTRAL = "spectral"


#: The three, in Corollary ``cor:pullback``'s order (i)-(iii).
CERTIFICATE_KINDS: Final[tuple[CertificateKind, ...]] = (
    CertificateKind.IDENTITY,
    CertificateKind.POSITIVITY,
    CertificateKind.SPECTRAL,
)


class AssumptionId(StrEnum):
    """The core assumptions of the ledger, by their ids, and the assumed ones.

    A submodule's assumption is spelled in the submodule's package, which
    registers it at the position the ledger gives it. The member order is the
    ledger's.

    TWO OF THE MEMBERS BELOW ARE THE TRANSMITTER'S AND ARE *ASSUMED FROM
    ANOTHER MODULE*, which is where ``interface.yaml`` declares them
    (``assumption_ledger.assumed_from_another_module``): A-SEQ, which
    ``def:protocol`` declares -- an assumption being a leaf whose ``assumes``
    is empty, so no ``ass`` claim of this module can carry it -- and A-SRC,
    which ``lem:source-transfer`` brings with
    ``transmitter/thm:certificate-sufficiency`` (iii) and which is present only where
    the emitted chain's source segment is non-empty. Short ids and machine keys are
    repository-wide, so each is the transmitter's own key carried unprefixed, exactly as
    the supplier's keys are on the A-RECV row.

    THERE IS NO A-NOSRC. No claim of this
    module rests on the source segment being empty -- ``def:chain``
    defines the chain at every length and its composite as the pair,
    ``thm:chain`` (i)-(iv) read the receiver composite alone, and
    ``rem:ordering``'s inclusion is ``lem:precomposition`` -- so the key is in
    the closure of no claim producing the artefact, and a declared row for it
    would name an assumption nothing emitted rests on
    (``interface.yaml``'s ``assumption_ledger.no_row_for_an_empty_source_segment``).
    WHETHER THE SEGMENT IS EMPTY IS DATA A CONSUMER READS, in the emitted
    ``reduction_chain``.

    THERE IS NO ROW FOR THE ADVERSARY'S REGISTERS. The adjoint bookkeeping of
    ``lem:sep`` (ii) reads them as finite-dimensional, and that is the round
    model's (``foundations/def:round-model``), not an assumption: the
    consuming engine carries its security statement to an adversary whose
    memory has any dimension (``meat-core/cor:composed-security``, through
    ``meat-core/lem:memory-lift``). The engine's A-EVE-DIM
    (``meat-core/ass:eve-dim``) is superseded and no row of this ledger; the
    other half of the former A-DIM, the separable ``H(B)`` and the finite,
    declared target and side registers, is ``def:system-setting``, a
    definition and no ledger row. Order 1 is unassigned.

    THERE IS NO A-SOUND (``constraints_sound``). No claim declares it; that every entry
    this module emits is sound for the chain is a conclusion of ``thm:chain``,
    ``cor:entries`` and ``thm:licence`` (``rem:sound-and-atk``), not a row of
    the ledger. Its order, 10, stays vacant: a row keeps the place it was
    given.
    """

    #: NOT ``A-ROUND`` with machine key
    #: ``round_homogeneity``. Short ids and machine keys are REPOSITORY-WIDE
    #: and the receiver module already owns both: its own ``A-ROUND`` is one of
    #: the supplier keys this module INHERITS and emits unchanged on its
    #: A-RECV entry, so two different assumptions would
    #: otherwise share one key across a docking boundary. They differ, and
    #: nothing is namespaced: each key is one assumption's own.
    A_MEAS = "A-MEAS"
    A_ROUND_SQ = "A-ROUND-SQ"
    A_RECV = "A-RECV"
    A_PROBE = "A-PROBE"
    A_TSM = "A-TSM"
    #: THE TRANSMITTER'S, assumed here and never restated. Present only where
    #: the emitted chain's source segment is NON-EMPTY, which is admitted only
    #: in trusted-source mode and which no artefact emitted today carries
    #: (:data:`PRESENT_ONLY_WITH_A_NON_EMPTY_SOURCE_SEGMENT`).
    A_SRC = "A-SRC"
    A_CONST = "A-CONST"
    #: THE TRANSMITTER'S, declared by ``def:protocol`` and emitted
    #: UNCONDITIONALLY: the number of measuring parties is not a datum that
    #: definition reads, and with one measuring party the key is the
    #: assumption it always was (``transmitter/ass:seq``). It is a row a
    #: one-party emission carries too, and no emitted number, entry,
    #: target or constant depends on it.
    A_SEQ = "A-SEQ"


#: The ledger's machine keys, one per core assumption.
ASSUMPTION_MACHINE_KEYS: Final[MappingProxyType[AssumptionId, str]] = MappingProxyType(
    {
        AssumptionId.A_MEAS: "measurement_only_receiver",
        AssumptionId.A_ROUND_SQ: "round_homogeneity_squashing",
        AssumptionId.A_RECV: "receiver_artifact_accepted",
        AssumptionId.A_PROBE: "probe_setting_private",
        AssumptionId.A_TSM: "test_statistics_model",
        AssumptionId.A_SRC: "source_replacement_license",
        AssumptionId.A_CONST: "declared_constants",
        AssumptionId.A_SEQ: "sequential_round_model",
    }
)


@dataclass(frozen=True, slots=True)
class AssumptionRow:
    """One row of the emitted assumption ledger, with its place in it.

    ``order`` is the position the ledger's own table gives the row, so that a
    submodule's assumption sits where the table puts it without the core naming
    it, between two core rows if the table puts it there.
    ``never_verifiable`` marks a row whose assumption carries ``verification:
    never`` (spec/claim-format.md section 3.2): no code path decides what it
    says beyond its clauses on the declared data, and the ledger says so
    rather than reporting it as checked (``req:never-verified-assumptions``).
    Build a row with :func:`ledger_row`, which reads the mark from the header
    field by machine key, so that no row carries a hand-written one.
    """

    identifier: str
    machine_key: str
    never_verifiable: bool
    order: int


def ledger_row(identifier: str, machine_key: str, order: int) -> AssumptionRow:
    """Return the ledger row of one assumption, marked by its header field.

    ``never_verifiable`` is
    :func:`certiqs_key.domain.claim_closure.never_verified` of the machine key:
    the assumption's ``verification`` field, the one place that says whether a
    run rests on it unverified. A row this module takes from another
    module therefore carries its owner's mark, as
    ``req:never-verified-assumptions`` requires of A-SRC and A-SEQ, and a
    submodule's row is marked by the same rule.
    """
    return AssumptionRow(identifier, machine_key, never_verified(machine_key), order)


#: The rows this module emits, in the ledger's own order: the SIX core rows of
#: ``interface.yaml``'s ``assumption_ledger.core_rows`` and the TWO it
#: assumes from the transmitter (``assumed_from_another_module``): A-SRC at
#: order 8 and A-SEQ at order 11. A submodule's rows take the orders its
#: interface gives them.
#: THE ORDERS ARE THE INTERFACE TABLE'S AND A ROW KEEPS THE PLACE IT WAS
#: GIVEN, so an arriving row takes the next free one rather than renumbering
#: the rows that were there, and a departing row leaves its order unassigned
#: -- which is why A-SEQ is at 11, why A-SRC takes the order 8, and why 1
#: (the superseded A-EVE-DIM's) and 10 (the retired A-SOUND's) stay vacant.
CORE_ASSUMPTIONS: Final[tuple[AssumptionRow, ...]] = (
    ledger_row("A-MEAS", "measurement_only_receiver", 2),
    ledger_row("A-ROUND-SQ", "round_homogeneity_squashing", 3),
    ledger_row("A-RECV", "receiver_artifact_accepted", 4),
    ledger_row("A-PROBE", "probe_setting_private", 6),
    ledger_row("A-TSM", "test_statistics_model", 7),
    ledger_row("A-SRC", "source_replacement_license", 8),
    ledger_row("A-CONST", "declared_constants", 9),
    ledger_row("A-SEQ", "sequential_round_model", 11),
)

#: FOUNDATIONS' ROW, ``foundations/ass:snapped-measurement`` (A-SNAP, key
#: ``snapped_measurement``), assumed here and never restated, at
#: order 13. KEPT OUT OF :data:`CORE_ASSUMPTIONS` AND :class:`AssumptionId`
#: because it is foundations' and conditional: ``thm:emit`` assumes it only
#: in its part (vi), which asserts nothing of a run whose record names no
#: resting block, and ``req:emission-record`` attaches it to an artefact
#: exactly where a data sector holds a moved class or the declaring party's
#: snap a moved block (:data:`PRESENT_ONLY_WHERE_A_BLOCK_RESTS_ON_A_SNAP`), so
#: :func:`certiqs_key.reductions.emit.emitted_assumption_rows` appends it
#: there and nowhere else. It carries its owner's never-verified mark.
SNAPPED_MEASUREMENT_ROW: Final[AssumptionRow] = ledger_row(
    "A-SNAP", "snapped_measurement", 13
)

#: THE ROWS OF THE TUPLE ABOVE THAT ARE NOT THE CORE'S OWN. They are the
#: transmitter's, declared under ``assumed_from_another_module`` in
#: ``interface.yaml`` and emitted here as declared rows under their declared
#: presence rules (A-SEQ on every emission, A-SRC only where the emitted
#: chain's source segment is non-empty); this module states neither and
#: restates neither, and each carries the mark its owner gives it
#: (``req:never-verified-assumptions``).
ASSUMED_FROM_THE_TRANSMITTER: Final[frozenset[str]] = frozenset(
    {AssumptionId.A_SRC.value, AssumptionId.A_SEQ.value}
)

#: THE ROW THIS MODULE ASSUMES FROM FOUNDATIONS: A-SNAP
#: (:data:`SNAPPED_MEASUREMENT_ROW`), declared under
#: ``assumed_from_another_module`` in ``interface.yaml`` with owner
#: ``foundations``, at order 13 -- the next free order after the rows a
#: submodule had taken. ``req:emission-record`` carries it "among the
#: assumptions the artefact may rest on exactly where there is one" moved
#: sector, beside the declaring party's moved blocks; the row carries its
#: owner's never-verified mark.
ASSUMED_FROM_FOUNDATIONS: Final[frozenset[str]] = frozenset(
    {SNAPPED_MEASUREMENT_ROW.identifier}
)

#: THE ROW PRESENT ONLY WHERE SOME BLOCK OF THE ARTEFACT MAY REST ON A SNAP:
#: A-SNAP, "whenever the emission record names a moved class, or the
#: declaring party's snap record a moved block, as resting on it"
#: (``interface.yaml``, ``assumption_ledger.assumed_from_another_module``).
#: Read at the one place that holds both records, the emission in
#: :mod:`certiqs_key.reductions.emit`.
PRESENT_ONLY_WHERE_A_BLOCK_RESTS_ON_A_SNAP: Final[frozenset[str]] = frozenset(
    {SNAPPED_MEASUREMENT_ROW.identifier}
)

#: THE ROW WHOSE PRESENCE IS CONDITIONAL ON THE EMITTED CHAIN, and there is
#: ONE. A-SRC is the transmitter's source-replacement attestation, which
#: ``lem:source-transfer`` reads through ``transmitter/thm:certificate-sufficiency``
#: (iii), and it is present "whenever the emitted chain's source segment is NON-EMPTY"
#: (``interface.yaml``, ``assumption_ledger.assumed_from_another_module``) --
#: and then only in trusted-source mode, where the admission rule of
#: ``def:chain`` admits such a chain at all and where ``ass:src`` is asserted.
#:
#: IT IS ABSENT FROM EVERY ARTEFACT EMITTED TODAY, because every emitted chain
#: has an empty source segment: no claim on the emission path uses
#: ``lem:source-transfer`` or ``thm:two-sided``, and ``thm:chain`` reads the
#: receiver composite alone. The emitted ledger is the declared row list under
#: its presence rules (``req:assumption-ledger``), and this is one of them.
#: The condition is read at the one place that holds the chain, the emission
#: in :mod:`certiqs_key.reductions.emit`.
PRESENT_ONLY_WITH_A_NON_EMPTY_SOURCE_SEGMENT: Final[frozenset[str]] = frozenset(
    {AssumptionId.A_SRC.value}
)

#: THE ROW PRESENT ONLY WHERE THE EMITTED CONSTRAINT LIST IS NON-EMPTY: A-CONST
#: (``ass:constdecl``), "only where the emitted constraint list is non-empty, a
#: condition on the constants of emitted entries holding vacuously of an empty
#: list" (``interface.yaml``, ``assumption_ledger.emission_rule``;
#: ``req:assumption-ledger``).
#: The encoded route emits no entry, so it does not rest on it. Read at the one
#: place that holds the emitted list, the emission in
#: :mod:`certiqs_key.reductions.emit`.
PRESENT_ONLY_WITH_A_NON_EMPTY_CONSTRAINT_LIST: Final[frozenset[str]] = frozenset(
    {AssumptionId.A_CONST.value}
)

#: THE ROW PRESENT ONLY WHERE THE DECLARED SETTING SET HAS AT LEAST TWO VALUES:
#: A-PROBE (``ass:probe``), "at a station only where its declared setting set
#: T has at least two values" (``interface.yaml``, ``assumption_ledger``
#: emission_rule; ``req:assumption-ledger``). At
#: ``T = {*}`` its clauses hold of the one setting drawn with weight one. Read
#: at the emission in :mod:`certiqs_key.reductions.emit`.
PRESENT_ONLY_WITH_A_PRIVATE_SETTING: Final[frozenset[str]] = frozenset(
    {AssumptionId.A_PROBE.value}
)

#: THE ROW PRESENT ONLY WHERE A SETTING OR A PUBLIC CHOICE IS AT THE STATION:
#: A-TSM (``ass:tsm``), "at a station only where T has at least two values, or
#: where the consuming specification applies a public choice at the station's
#: measured factor ...; the emission is told whether such a choice is applied;
#: where it is not told, the row is emitted" (``interface.yaml``;
#: ``req:assumption-ledger``). Read at the
#: emission in :mod:`certiqs_key.reductions.emit`.
PRESENT_ONLY_WITH_A_SETTING_OR_A_CHOICE: Final[frozenset[str]] = frozenset(
    {AssumptionId.A_TSM.value}
)

#: THE ROW OMITTED WHERE THE RUN ATTESTS IT BUILT THE RECEIVER ARTIFACT: A-RECV
#: (``ass:recv``), "on every emission save where req:recv-row-provenance omits
#: it: every supplier artifact the instance read is a receiver artifact the run
#: attests it built (`receiver_provenance`), with a model admissible exactly and
#: the `rigorous` evaluation label" (``interface.yaml``, ``core_rows``). Read at
#: the emission in :mod:`certiqs_key.reductions.emit`
#: (:func:`~certiqs_key.reductions.emit.receiver_row_omitted_on_provenance`).
OMITTED_ON_RECEIVER_PROVENANCE: Final[frozenset[str]] = frozenset(
    {AssumptionId.A_RECV.value}
)

#: THE ASSUMPTIONS OF THIS LEDGER NO CODE PATH OF THIS CORE DECIDES BEYOND THEIR CLAUSES
#: ON THE DECLARED DATA (req:never-verified-assumptions), in the ledger's order: every
#: member whose ``verification`` header field is ``never`` (spec/claim-format.md section
#: 3.2), read from the shipped claim-closure table by machine key and not listed here by
#: hand. The rows taken from the transmitter and the engine are members by their owner's
#: field, and a submodule marks its own rows by the same rule. Validation still decides
#: the conditions on declared data the assumptions are read with -- the declared
#: dimensions of ``def:system-setting``, the declared class weights of
#: ``def:joint-family``, the refusal of an entry that declares itself data-dependent
#: under A-CONST -- and for A-RECV it refuses an artifact whose ``module_version`` is
#: outside the caller's declared accepted set (``req:supplier-version-accepted``) and
#: NAMES the artifact by version in the licence record. No number depends on membership:
#: it sets the ledger's ``never_verifiable`` flag and nothing else.
NEVER_VERIFIED: Final[tuple[AssumptionId, ...]] = tuple(
    identifier
    for identifier in AssumptionId
    if never_verified(ASSUMPTION_MACHINE_KEYS[identifier])
)


#: NO TRANSCRIPTION OF THE SUPPLIER'S MACHINE KEYS OR PRESENCE RULES LIVES
#: HERE (the ledger is passed through). The A-RECV entry carries the supplied receiver
#: ledger's keys as they stand, in the supplier's order
#: (:func:`certiqs_key.reductions.artifact.assumption_ledger`), and the
#: receiver-spec row requires the keys the RECEIVER'S OWN presence rules make
#: present, read from :mod:`certiqs_key.receiver.reasons` at the one
#: function-local site :func:`certiqs_key.reductions.validation.required_receiver_keys`.
#: A key the receiver gains therefore reaches the emitted ledger without an edit
#: here, and a key its rules make present that an artifact lacks is refused.

#: The one inherited key whose declared content A-RECV names: ``eps_eig`` "IS
#: RECORDED IN THE EMITTED LEDGER BESIDE THE SETTINGS AT WHICH THE SUPPLIER SAYS
#: IT WAS INVOKED".
INHERITED_KEY_WITH_A_DECLARED_RECORD: Final[str] = "exact_window_eigenvalue_slack"


class FailClosedRule(StrEnum):
    """One identifier per CORE fail-closed row, in the interface's order.

    TWENTY-ONE of the interface's rows; the others are the submodules' and are
    spelled in ``wpfss`` and the other submodules. The identifiers are this module's --
    the interface names rows by what they check, not by an ID -- and they exist
    for one purpose: the verification report carries "EVERY VALIDATION RULE WITH
    ITS OUTCOME", which needs a stable name per rule. NO IDENTIFIER HERE IS A
    REFUSAL REASON and none is ever emitted in place of one.

    THE MEMBER ORDER IS THE INTERFACE'S ROW ORDER RESTRICTED TO THE CORE; the
    interleaving with the submodules' rows is carried by
    :attr:`FailClosedRow.order` and not by this enum, because an enum cannot be
    extended and the submodules' rows sit between core ones.
    """

    # --- the lattice and the requested rung, decided before anything ------
    LATTICE_EXPONENT = "lattice_exponent"
    REQUESTED_ASSURANCE = "requested_assurance"

    # --- the receiver artifact, the cutoff and the declared blocks --------
    RECEIVER_SPEC = "receiver_spec"
    CUTOFF = "cutoff"
    BLOCK_STRUCTURE = "block_structure"
    EXACT_ADMISSIBILITY = "exact_admissibility"
    EMITTED_FAMILY = "emitted_family"

    # --- the probe, the relations and the chain ---------------------------
    PROBE_WEIGHTS = "probe_weights"
    OBSTRUCTIONS = "obstructions"
    CHAIN = "chain"
    LINK_KIND = "link_kind"
    APPROXIMATE = "approximate"
    DEVICE_FAMILY = "device_family"
    CONSTRAINT_CERTIFICATE = "constraint_certificate"

    # --- the licence, the route and the cross-artifact agreements ---------
    LICENCE_PRESENCE = "licence_presence"
    LICENSED_HERMITICITY = "licensed_hermiticity"
    ROUTE = "route"
    CONSTRAINT_CHANNEL = "constraint_channel"
    ALPHABET_ORDER = "alphabet_order"
    POST_PROCESSING_ORDER = "post_processing_order"
    UNSOUND_TRANSPLANT = "unsound_transplant"


@dataclass(frozen=True, slots=True)
class FailClosedRow:
    """One row of the fail-closed table: its name, its place, its reasons.

    ``order`` is the row's position in the interface's own table, counted from
    one over ALL the interface's rows and not only the core's. It is what lets
    the six ``wpfss`` rows sit between the emitted-family row and the
    probe-weight row, and another submodule's rows between two of those,
    without the core naming any of them.
    """

    rule: str
    order: int
    reasons: tuple[str, ...]


#: The twenty-one core rows, with the place each holds in the table of
#: twenty-eight. Exactly three carry two reasons; the union over all
#: twenty-eight rows is the thirty strings, and a golden test asserts it.
CORE_FAIL_CLOSED_ROWS: Final[tuple[FailClosedRow, ...]] = (
    FailClosedRow(
        FailClosedRule.LATTICE_EXPONENT,
        1,
        (RefusalReason.LATTICE_EXPONENT_NOT_DECLARED,),
    ),
    FailClosedRow(
        FailClosedRule.REQUESTED_ASSURANCE,
        2,
        (RefusalReason.REQUESTED_ASSURANCE_UNKNOWN,),
    ),
    FailClosedRow(
        FailClosedRule.RECEIVER_SPEC, 3, (RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED,)
    ),
    FailClosedRow(FailClosedRule.CUTOFF, 4, (RefusalReason.CUTOFF_MISMATCH,)),
    FailClosedRow(
        FailClosedRule.BLOCK_STRUCTURE, 5, (RefusalReason.NO_BLOCK_STRUCTURE,)
    ),
    FailClosedRow(
        FailClosedRule.EXACT_ADMISSIBILITY,
        6,
        (RefusalReason.DECLARATION_NOT_EXACTLY_ADMISSIBLE,),
    ),
    FailClosedRow(
        FailClosedRule.EMITTED_FAMILY,
        7,
        (RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE,),
    ),
    FailClosedRow(
        FailClosedRule.PROBE_WEIGHTS, 15, (RefusalReason.PROBE_WEIGHTS_ILL_FORMED,)
    ),
    FailClosedRow(
        FailClosedRule.OBSTRUCTIONS, 16, (RefusalReason.DECLARED_RELATION_IMPOSSIBLE,)
    ),
    FailClosedRow(
        FailClosedRule.CHAIN,
        17,
        (
            RefusalReason.CHAIN_ILL_FORMED,
            RefusalReason.SOURCE_LINK_AFTER_RECEIVER_LINK,
        ),
    ),
    FailClosedRow(FailClosedRule.LINK_KIND, 18, (RefusalReason.LINK_KIND_DEFERRED,)),
    FailClosedRow(
        FailClosedRule.APPROXIMATE,
        19,
        (RefusalReason.APPROXIMATE_SQUASHING_UNSUPPORTED,),
    ),
    FailClosedRow(
        FailClosedRule.DEVICE_FAMILY, 20, (RefusalReason.DEVICE_FAMILY_UNSUPPORTED,)
    ),
    FailClosedRow(
        FailClosedRule.CONSTRAINT_CERTIFICATE,
        21,
        (
            RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
            RefusalReason.DATA_DEPENDENT_CONSTANT,
        ),
    ),
    FailClosedRow(
        FailClosedRule.LICENCE_PRESENCE,
        22,
        (RefusalReason.LICENCE_MISSING, RefusalReason.LICENCE_WITHOUT_CONSTRAINTS),
    ),
    FailClosedRow(
        FailClosedRule.LICENSED_HERMITICITY,
        23,
        (RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,),
    ),
    FailClosedRow(FailClosedRule.ROUTE, 24, (RefusalReason.ROUTE_NOT_SINGLE_VALUED,)),
    FailClosedRow(
        FailClosedRule.CONSTRAINT_CHANNEL,
        25,
        (RefusalReason.CONSTRAINT_CHANNEL_MISMATCH,),
    ),
    FailClosedRow(
        FailClosedRule.ALPHABET_ORDER, 26, (RefusalReason.ALPHABET_OR_ORDER_MISMATCH,)
    ),
    FailClosedRow(
        FailClosedRule.POST_PROCESSING_ORDER,
        27,
        (RefusalReason.POST_PROCESSING_ORDER_VIOLATED,),
    ),
    FailClosedRow(
        FailClosedRule.UNSOUND_TRANSPLANT,
        28,
        (RefusalReason.UNSOUND_CONSTRAINT_REQUESTED,),
    ),
)


_REGISTRY: dict[str, FailClosedRow] = {}


def register_row(row: FailClosedRow) -> FailClosedRow:
    """Put one fail-closed row in the registry, idempotently.

    Re-registering the SAME row is a no-op, so a submodule may register at
    import without caring how often it is imported. Registering a DIFFERENT row
    under a name already taken raises: two readings of one row would make the
    reasons a machine record names depend on import order, which is the one
    thing a vocabulary registry must not do.
    """
    existing = _REGISTRY.get(row.rule)
    if existing is not None and existing != row:
        raise MalformedInputError(
            f"the fail-closed row {row.rule!r} is already registered as "
            f"{existing!r} and cannot be re-registered as {row!r}: a row is one "
            "reading, and two would make a machine record depend on import order"
        )
    _REGISTRY[row.rule] = row
    return row


def registered_rows() -> tuple[FailClosedRow, ...]:
    """Return every registered row, in the interface's table order.

    NOT what decides a report's rows: those are the core's plus the ones the
    instance builder declares, assembled per call, so that a report never
    depends on which submodules happen to have been imported.
    """
    return tuple(sorted(_REGISTRY.values(), key=lambda row: row.order))


def fail_closed_rules() -> MappingProxyType[str, tuple[str, ...]]:
    """Return every registered row to the reasons it can produce.

    THE ``FAIL_CLOSED_RULES`` MAPPING IS BUILT FROM THE REGISTRY
    rather than written out, because a submodule's rows are its own and a
    constant in this file could not hold them. It is a FUNCTION and not a
    module constant for the same reason: what is registered depends on which
    submodules a caller imported, and a constant would freeze whichever answer
    happened to be true at import time.
    """
    return MappingProxyType(
        {str(row.rule): row.reasons for row in registered_rows()}
    )


def reasons_of(rule: str) -> tuple[str, ...]:
    """Return the reasons the named row can produce, or ``()`` if unregistered."""
    row = _REGISTRY.get(str(rule))
    return () if row is None else row.reasons


for _row in CORE_FAIL_CLOSED_ROWS:
    register_row(_row)
