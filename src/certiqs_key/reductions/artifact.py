"""The emitted ``ProofReductionArtifact``: the outputs table, key by key.

EVERY KEY OF THE OUTPUTS TABLE, ALL PRESENT, IN THE INTERFACE'S OWN ORDER
=========================================================================
The outputs tables list the payload key by key -- the core's keys plus the
two ``wpfss`` adds, ``wpfss_data`` and ``route`` -- and
:class:`ProofReductionArtifact` has a field per key one artefact carries,
named exactly as the machine keys; :data:`OUTPUT_KEYS` states the order once so
that the list is checkable from the code rather than from a comment.

``route`` IS EMITTED AND NOT ONLY CARRIED. It is an output row of
``wpfss/interface.yaml`` -- "always, for an artifact emitted from the flat
instance; the single value the request carried" -- and the two routes run on
DIFFERENT CHANNELS (``wpfss/rem:tworoutes``), so a record that did not say
which one produced it would leave a consumer to infer it from the shape of the
flag block.

``douglas_data`` IS NOT AMONG THEM. A key emitted with the value ``null``
"so that adding a dominator later is not a schema change" would be, in
PRINCIPLES.md section 7's terms, a hand-maintained mirror of a deferral, and
the deferral already has a docking point in the planned `family-reduction`
submodule, which is where the data of a family will be declared (the
`family-dominating` link kind is the `domination` submodule's link, which no
requirement emits and which asks for no dominator).

Two presence rules are the interface's and are enforced rather than described:

* ``status`` is ``exact``. "``certified_outer`` and ``exploratory_numeric`` are
  NEVER EMITTED by this module."
* ``attack_set_license`` is non-null EXACTLY WHEN ``constraint_list`` is
  non-empty (the slot itself is always emitted,
  ``req:constraint-and-licence-slots``), and
  :meth:`ProofReductionArtifact.__post_init__` refuses a record that violates
  the iff -- so the two directions of the licence row cannot come
  apart in an emitted object even by a programming error.

WHAT IS DELIBERATELY NOT EMITTED
================================
The outputs table, transcribed because each item is something an implementation could
add without noticing: "NO ENTROPY, NO OBJECTIVE VALUE, NO KEY LENGTH, NO
ACCEPTANCE SET, NO HONEST-CHANNEL STATISTICS, AND NO OBSERVED NUMBER OF ANY
KIND. NO PENALTY TERM AND NO ERROR PARAMETER: the transfer of Theorem
``thm:transfer`` is an EQUALITY, so there is nothing to report. NO RECEIVER
QUANTITY IS RECOMPUTED: the ``t``-uniform weights ``p_i`` and the blocks
``blk M^{=m}`` are referenced, transported, and never re-derived or
re-quantified." :data:`NOT_EMITTED` is that list as a checkable tuple, and no
field of this module carries any of them.

OPEN IMPLEMENTATION CHOICE 5 OF 12 IS DECIDED HERE: ``wpfss_data`` IS ALWAYS PRESENT
====================================================================================
``interface.yaml``: "WHAT THE CONTRACT DOES NOT SAY is whether the
``wpfss_data`` KEY is populated, empty or absent in an artifact emitted on the
``licensed`` route, where the target is ``F^FSS`` rather than ``F^WP``."

THE DECISION: it is ALWAYS PRESENT and always carries the declared weights, the
flag basis in the declared order of ``V``, the cutoff and the total, on BOTH
routes; a boolean ``encoded_in_target`` records which route put them where.
Four reasons.

1. The contract gives ``attack_set_license`` a presence rule and gives this key
   none. The contrast is the strongest signal the text offers, and a key with no
   presence rule is present.
2. The data exist on both routes. The total-weight row applies the ``p < 1``
   test "on both routes deliberately", so the weights are declared and
   validated either way; ``wpfss/rem:tworoutes`` says that on the licensed
   route they travel as the constraint entry instead of inside the target,
   which is a statement about WHERE THEY TRAVEL and not that they cease to be
   declared.
3. The parameters table requires the record: "This module takes them from
   ``eq:weightroute``; ANY SMALLER NON-NEGATIVE CHOICE IS ALSO VALID (Remark
   ``rem:weightfree``) AND THE ARTIFACT RECORDS WHICH WAS USED."
4. THE LICENSED ROUTE IS THE ONE THAT NEEDS THE RECORD. On the encoded route
   the weights can be read back off ``F^WP`` -- they ARE its flag diagonal. On
   the licensed route the target is ``F^FSS``, whose flag block is a bare
   projector, so the weights are readable only from this key or by inverting the
   constraint operator. Dropping the key exactly there would remove the record
   at the one place it carries information.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Final, Protocol

from certiqs_key.domain.bindings import as_json
from certiqs_key.foundations.exact import Matrix, equal, serialize_matrix
from certiqs_key.reductions.channels import ChannelWitness, TransportedOperator
from certiqs_key.reductions.constraints import AttackSetLicence, ConstraintEntry
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import (
    ChannelGrading,
    InheritedAssumption,
    JointOutcome,
    Label,
    outcome_label,
    probe_settings_of,
)
from certiqs_key.reductions.links import Chain, SystemFamily
from certiqs_key.reductions.normalizer import ClassSnap
from certiqs_key.reductions.reasons import (
    CORE_ASSUMPTIONS,
    INHERITED_KEY_WITH_A_DECLARED_RECORD,
    AssumptionRow,
    LinkStatus,
    Refusal,
    Route,
)
from certiqs_key.reductions.sectors import SectorSet
from certiqs_key.reductions.validation import RULE_ORDER, RuleOutcome

__all__ = [
    "ADR_0008_DISCLOSURES",
    "NOT_EMITTED",
    "NO_KEY_LENGTH_BOUND",
    "ONE_ARTEFACT_ONLY_KEYS",
    "OUTPUT_KEYS",
    "ROUNDING_DIRECTIONS",
    "SNAPPED_MEASUREMENT_ASSUMPTION",
    "AssumptionLedgerEntry",
    "BlockEmissionRecord",
    "BranchRegister",
    "CompanionRecord",
    "EmissionRecord",
    "ExactIdentity",
    "ProofReductionArtifact",
    "ReductionOutcome",
    "SourceDescriptor",
    "TargetDescriptor",
    "VerificationReport",
    "WpfssData",
    "assumption_ledger",
]

#: The outputs table of interface.yaml in its own order: the core's keys and
#: the two ``wpfss`` adds, ``wpfss_data`` and ``route``. ``emission_record``
#: sits immediately before
#: ``mathematical_spec_version``; ``douglas_data`` is NOT a key,
#: and ``route`` is adjacent to ``wpfss_data``, so that the submodule's two keys
#: are adjacent.
#:
#: ``emission_record`` IS ALWAYS PRESENT AND SO IS ITS VALUE. The row is present on
#: every emitted artifact because it carries ``kappa`` and the six condition
#: outcomes, which exist whenever an artifact does -- "SINCE OTHERWISE THERE
#: WOULD BE NO ARTIFACT".
#:
#: ``factor_emission`` IS THE ONE KEY OF THIS LIST THAT IS NOT A FIELD OF ONE
#: ARTEFACT. It is "PRESENT
#: EXACTLY WHEN THE CALL DECLARES MORE THAN ONE INSTANCE -- one per measuring
#: party. ABSENT FOR A ONE-FACTOR EMISSION, which is every emission of version
#: 1, and nothing else in this file changes there" (the ``factor_emission``
#: output row). What it carries is the ORDERED LIST OF THE FACTORS' ARTEFACTS
#: plus the combination rule, so it belongs to the emission of several
#: instances and not to any one of them:
#: :class:`certiqs_key.reductions.factors.FactorEmission` is the record, and
#: :meth:`ProofReductionArtifact.record_keys` is what one artefact's machine
#: record carries -- this list without that key.
OUTPUT_KEYS: Final[tuple[str, ...]] = (
    "source_descriptor",
    "target_descriptor",
    "target_povm",
    "factor_emission",
    "outcome_correspondence",
    "squashing_channel",
    "exact_identity",
    "transported_operators",
    "reachable_set_statement",
    "constraint_list",
    "attack_set_license",
    "wpfss_data",
    "route",
    "reduction_chain",
    "status",
    "verification_report",
    "assumption_ledger",
    "receiver_row_omitted_on_provenance",
    "emission_record",
    "reference_companion",
    "mathematical_spec_version",
)

#: THE KEYS ONE ARTEFACT'S MACHINE RECORD CARRIES: :data:`OUTPUT_KEYS` without
#: ``factor_emission``, which is the emission of several instances and not a
#: field of any one of them. A ONE-FACTOR EMISSION IS ONE ARTEFACT AND CARRIES
#: EXACTLY THESE, in this order, which is the record it carried before the key
#: existed -- "SO THIS ROW ADDS NOTHING TO A ONE-FACTOR ARTEFACT AND IS ABSENT
#: FROM IT" (the ``factor_emission`` row's ``one_factor_is_todays_artefact``).
ONE_ARTEFACT_ONLY_KEYS: Final[tuple[str, ...]] = tuple(
    key for key in OUTPUT_KEYS if key != "factor_emission"
)

#: the outputs table, "What is deliberately not emitted", as a checkable list. No
#: field of :class:`ProofReductionArtifact` carries any of these.
NOT_EMITTED: Final[tuple[str, ...]] = (
    "entropy",
    "objective_value",
    "key_length",
    "acceptance_set",
    "honest_channel_statistics",
    "any_observed_number",
    "penalty_term",
    "error_parameter",
    "any_recomputed_receiver_quantity",
)


class CompanionRecord(Protocol):
    """The reference companion, or the record of its absence: one record method.

    Typed structurally so that this file names nothing of
    :mod:`certiqs_key.reductions.companion`, which imports the instance and
    through it this file.
    """

    def as_record(self) -> dict[str, object]:
        """Return the record as a JSON-ready mapping."""
        ...


@dataclass(frozen=True)
class BranchRegister:
    """The register a branching instance conditions on: its labels and POVM.

    ``cor:register-instance``'s datum: ``B = B_0 D`` with ``{N_j}`` a POVM on
    ``D`` and ``M_v = sum_j M_{v|j} (x) N_j``. THE RECORD IS GENERIC AND NAMES
    NO BRANCHING MODEL. Carrying one model's modes and register directly,
    under machine keys named after that model, beside ``register_dimension``
    and ``register_povm``, would name one model; the register that arrives
    with the light may be a detector-response mode, a device label or a decoy
    tag, so the key
    is ``branch_register`` and the record is what an instance supplies.

    ``None`` on an instance with no register at all -- the flat one, whose
    physical system is the channel space itself.
    """

    labels: tuple[Label, ...]
    povm: Mapping[Label, Matrix]
    dimension: int


@dataclass(frozen=True)
class SourceDescriptor:
    """``B``: the physical system the instance names, ``def:reduction-instance`` (I1).

    The channel Fock space WITH ITS DECLARED PHOTON-NUMBER GRADING and, where
    the instance conditions on a branch register, that register with its POVM
    ``{N_j}`` (``cor:register-instance``). WHICH REGISTER IT IS, AND WHETHER
    THERE IS ONE, IS THE INSTANCE'S: this record names no branching model.

    NO SINGLE DIMENSION IS CARRIED FOR THE CHANNEL. ``H(B)`` is separable and
    may be infinite-dimensional, which Definition ``def:system-setting`` permits
    exactly here -- only ``H(Q)`` and the side registers are finite-dimensional. The
    grading is what is carried
    (:class:`~certiqs_key.reductions.inputs.ChannelGrading`, open implementation
    choice 3), and ``register_dimension`` is finite because ``{N_j}`` is a POVM
    declared as matrices.
    """

    channel_grading: ChannelGrading
    #: The branching register, where the instance conditions on one. ``None``
    #: on an instance whose physical system is the channel space itself.
    branch_register: BranchRegister | None = None
    description: str = "B: the channel Fock space with its declared grading"


@dataclass(frozen=True)
class TargetDescriptor:
    """``(Q, S)`` with the party partition: ``def:reduction-instance`` (I2).

    THE SECTOR MAP IS THE TYPE: the sector identifiers IN THE DECLARED ORDER,
    their dimensions, and ``dim H(Q) = sum_s d_s``. No full-space array is
    carried here or anywhere in the artifact, and the two formulas are THE
    INSTANCE'S own words for what it built. An alternative space an instance's
    claims prove but no declared input selects is not a field of the artifact;
    where one exists, the comparison of the two formulas is a property of that
    construction and the submodule's tests make it.

    ``party_partition`` is the DEFAULT PARTY PARTITION of (I2): Bob holds every
    factor of every ``H(Q_s)``, for every instance, "which is the assignment
    the physical model already makes -- the target describes what reaches Bob's
    receiver, the instance's system ``B`` being his". It is a DECLARED LABEL and
    not a computation, and it is what makes the emitted tuple satisfy the
    well-formedness conditions the consuming declaration places on Bob's side
    (``thm:emit`` (ii), Eq. ``eq:emitwellformed``), which the five conditions of
    ``def:exactadm`` say nothing about.
    """

    sectors: SectorSet
    dimension: int
    party_partition: str
    #: THE INSTANCE'S, not this record's. ``def:reduction-instance``
    #: (I2) states the generic ones, and an instance that builds a different
    #: target says so in its own words.
    dimension_formula: str = "dim H(Q) = sum_s d_s (def:reduction-instance (I2))"
    space_formula: str = "H(Q) = (+)_s H(Q_s) (def:reduction-instance (I2))"


@dataclass(frozen=True)
class ExactIdentity:
    """``Lambda^dagger(F_v) = M^dec_v``, holding EXACTLY (``thm:emit`` (iii)).

    WHAT THIS FIELD ASSERTS, read out of the text rather than assumed. It
    asserts THE THEOREM, which holds by construction: Eq. ``eq:emitidentity``
    holds "exactly, with no error term" for the instance's own channel
    (``def:reduction-instance`` (I3)) at the declared datum, and Definition
    ``def:link``'s ``status = exact`` means the identity "holds WITH NO ERROR
    TERM".

    IT IS NOT A NUMERICAL RESIDUAL CHECK ON MATERIALISED MATRICES, and could not
    be: the ``squashing_channel`` output row records that the supplier emits no
    above-cutoff block, so an instance's channel cannot in general be
    materialised from the artifact. What IS decidable, and what the artifact
    therefore carries beside this field, is the hypothesis set the theorem runs
    on -- every fail-closed row, in :class:`VerificationReport`.

    ``NO certified bound and NO approximation is ever emitted in this field``,
    which is why there is no error-term slot to leave empty.
    """

    statement: str = "Lambda^dagger(F_v) = M_v for every v in V"
    holds_by: str = (
        "the instance's existence theorem, def:reduction-instance (I3): "
        "exactly, with no error term"
    )
    status: LinkStatus = LinkStatus.EXACT
    is_numerical_residual_check: bool = False
    #: THE IDENTITY IS ASSERTED OF THE NUMBERS EMITTED, for the DECLARED model,
    #: and not of a family some assumption provides:
    #: Theorem ``thm:emit`` (iii) proves ``Lambda-dagger(F_v) = M'^ph_v``
    #: exactly, and Remark ``rem:emitclaim`` adds that ``status = exact`` "is
    #: truthful PRECISELY BECAUSE THE IDENTITY IS RE-ESTABLISHED FOR M'^ph,
    #: whose nb branch is M', RATHER THAN ASSERTED OF A CONSTRUCTION THE
    #: ARTIFACT DOES NOT CARRY". Empty where every ``Delta_s = 0``: there
    #: ``M' = M`` and "there is nothing to say".
    emission_snap_disposition: str = ""


@dataclass(frozen=True)
class BlockEmissionRecord:
    """What the emission normalizer did to ONE data sector, class by class.

    ``req:emission-record``, per data sector: the emission displacement
    ``Delta_s``; per class whether it was KEPT or MOVED, and for a moved
    class the step (2) or (3) that snapped it, the weight ``w`` taken or the
    fall-back of (3), the hosts of the components of its residue, and the flag
    ``support_not_preserved`` of a class snapped by (3).
    """

    block_index: int
    #: ``def:emitnorm``, FIRST PROPERTY: every class kept, so the normalizer
    #: is the identity on the sector.
    already_on_lattice: bool
    #: ``Delta_s`` in binary64 -- **THE ONE EMITTED NUMBER OF THIS ARTIFACT
    #: THAT IS NOT FORMED IN THE EXACT SUBSTRATE** (``thm:emit`` (i)). No
    #: predicate, bound, constant, claim or refusal reads it.
    displacement: float
    #: ``Delta_s^2``, EXACT, emitted beside the binary64 root.
    displacement_squared: Fraction
    #: Per class, the normalizer's record, in the declared order of the
    #: classes.
    classes: Mapping[str, ClassSnap]

    @property
    def moved(self) -> tuple[ClassSnap, ...]:
        """The moved classes of the sector."""
        return tuple(snap for snap in self.classes.values() if snap.moved)

    def as_machine_record(self) -> dict[str, object]:
        """Return the block's record, with every exact number as a string.

        ``displacement`` is the ONE float: it is binary64 by Theorem
        ``thm:emit`` (i). Everything else is an exact rational rendered as a
        string.
        """
        return {
            "block_index": self.block_index,
            "already_on_lattice": self.already_on_lattice,
            "displacement": self.displacement,
            "displacement_squared": str(self.displacement_squared),
            "classes": [snap.as_record() for snap in self.classes.values()],
        }


#: the outputs table, ``emission_record``, third disclosure: "THE DIRECTION IN WHICH
#: EVERY EMITTED BOUND WAS ROUNDED, BOUND BY BOUND, WITH ONE SENTENCE PER BOUND
#: SAYING WHY THAT SIDE IS SAFE." Three bounds, and the contract's own
#: sentences. spec/architecture.md 2.9, condition **(D-DIR)**.
ROUNDING_DIRECTIONS: Final[tuple[tuple[str, str, str], ...]] = (
    (
        "p_v = lat(p^_v), each per-outcome certified weight",
        "down",
        "because LOWERING a certified weight PRESERVES eq:certweights and "
        "RAISING one DESTROYS it (Prop. prop:route, Rem. rem:weightfree)",
    ),
    (
        "1 - p, the complement",
        "recomputed_not_rounded",
        "because the flag sector's completeness is the identity "
        "sum_v p_v + (1 - p) = 1 and ROUNDING BOTH SIDES INDEPENDENTLY WOULD "
        "BREAK IT (Thm. thm:emit (ii))",
    ),
    (
        "a caller-requested entry whose declared constant is not a lattice number",
        "enlarges_the_feasible_set_for_the_declared_relation",
        "because A SMALLER ADMISSIBLE SET IS THE DIRECTION IN WHICH "
        "Theorem thm:licence's INCLUSION CAN FAIL (Cor. cor:entries); down for "
        ">=, up for <=, and an EQUALITY entry off the lattice is REFUSED "
        "rather than split into a pair, an equality having no loosening "
        "direction",
    ),
)

#: The three disclosures spec/architecture.md 2.9 requires of a producer that
#: declares a nearby family rather than emitting the one it constructed.
#: Present exactly when some ``Delta_s > 0`` -- see
#: :attr:`EmissionRecord.three_adr_0008_disclosures`.
ADR_0008_DISCLOSURES: Final[tuple[str, ...]] = (
    "the emitted numbers are A DECLARATION and not the constructed ones",
    "the measured per-block displacement Delta_s",
    "the rounding direction of every weight",
)

#: Remark ``rem:emitclaim``, and it is the one thing the record must not be
#: read as asserting. Transcribed verbatim.
NO_KEY_LENGTH_BOUND: Final[str] = (
    "NO BOUND RELATING A KEY LENGTH COMPUTED FROM THE EMITTED DECLARATION ALONE "
    "TO ONE COMPUTED FROM THE HANDED MODEL IS ASSERTED, AND NOTHING ELSE "
    "RELATES THE TWO ON A MOVED CLASS; A RUN EVALUATES OFF THE SNAP ON THE "
    "REFERENCE COMPANION, OR RESTS ON THE SNAPPED-MEASUREMENT PREMISE THERE "
    "(Thm. thm:emit (v), (vi))"
)


#: ``foundations/ass:snapped-measurement``: the id, machine key and claim of
#: the assumption an artefact may rest on wherever some data sector holds a
#: moved class (``req:emission-record``;
#: ``spec/modules/foundations/interface.yaml``).
SNAPPED_MEASUREMENT_ASSUMPTION: Final[tuple[str, str, str]] = (
    "A-SNAP",
    "snapped_measurement",
    "foundations/ass:snapped-measurement",
)


@dataclass(frozen=True)
class EmissionRecord:
    """The outputs table's ``emission_record``: **ALWAYS PRESENT**.

    Implements ``reductions/req:emission-record``. It records what this
    module DID TO ITS OWN CONSTRUCTION before declaring it: the declared
    ``kappa``; whether the run declared the strict option and whether it uses
    enclosed references; the reference kind of every snap the normalizer
    makes, ``exact`` (the handed datum is its own reference, so the enclosure
    setting does not bear on it); per data sector the displacement and the
    per-class record; the six condition outcomes; every rounding direction;
    and the data sectors with a moved class, which rest on
    ``foundations/ass:snapped-measurement`` (A-SNAP) unless the run evaluates
    them off their snap, carried as that assumption exactly where there is
    one. Which of them rest is the run's decision: the naming here is
    provisional (``thm:emit`` (vi)).
    """

    #: The declared exponent, ECHOED. This module "NEITHER CHOOSES kappa NOR
    #: DERIVES IT FROM THE RECEIVER ARTIFACT".
    lattice_exponent: int
    #: The outcome of each of the six (D-EMIT) conditions, by name. Present
    #: "SINCE OTHERWISE THERE WOULD BE NO ARTIFACT".
    six_condition_outcomes: Mapping[str, bool]
    #: One record per data sector, in the declared sector order.
    blocks: tuple[BlockEmissionRecord, ...]
    #: PER ENTRY: the label, the constant EMITTED, and the direction a
    #: caller-declared constant off the lattice was rounded in
    #: (``cor:entries`` (iii); ``thm:emit`` (iv)). EMPTY where none was.
    constant_rounding_directions: tuple[tuple[str, str, str], ...] = ()
    #: Eq. ``eq:latinv``, as the statement the row requires.
    lattice_invariant_statement: str = (
        "every emitted operator entry is an integer multiple of 2^-kappa of "
        "modulus at most 1 (Eq. eq:latinv)"
    )
    #: Whether the run declared the strict option
    #: (``foundations/req:snap-reference`` (iv)).
    strict_snaps: bool = False
    #: Whether the run uses enclosed references (the enclosure setting of
    #: ``foundations/req:snap-reference`` (i)), echoed; it does not bear on the
    #: normalizer's snaps, whose reference is exact.
    enclosed_references_used: bool = True
    #: The reference kind of every snap the normalizer makes.
    reference_kind: str = "exact"

    @property
    def displaced(self) -> bool:
        """Whether the normalizer moved any number -- some ``Delta_s > 0``."""
        return any(block.displacement_squared > 0 for block in self.blocks)

    @property
    def three_adr_0008_disclosures(self) -> tuple[str, ...]:
        """The three disclosures, PRESENT EXACTLY WHEN some ``Delta_s > 0``."""
        return ADR_0008_DISCLOSURES if self.displaced else ()

    @property
    def moved_sectors(self) -> tuple[tuple[int, str], ...]:
        """The data sectors with a moved class, each with what moved it.

        ``req:emission-record``: "A data sector rests on
        foundations/ass:snapped-measurement where some class of it is moved,
        save where it is evaluated off its snap"; the run decides the latter,
        so these are named provisionally.
        """
        out: list[tuple[int, str]] = []
        for block in self.blocks:
            if block.moved:
                detail = ", ".join(
                    f"class {snap.label!r} moved by {snap.step}"
                    + (", support_not_preserved" if snap.support_not_preserved else "")
                    for snap in block.moved
                )
                out.append((block.block_index, detail))
        return tuple(out)

    @property
    def last_resort_sectors(self) -> frozenset[int]:
        """The data sectors with a class snapped by the last resort (3)."""
        return frozenset(
            block.block_index
            for block in self.blocks
            if any(snap.support_not_preserved for snap in block.moved)
        )

    @property
    def snapped_measurement_assumption(self) -> dict[str, object] | None:
        """A-SNAP naming the sectors with a moved class, or ``None`` where none."""
        moved = self.moved_sectors
        if not moved:
            return None
        identifier, machine_key, claim = SNAPPED_MEASUREMENT_ASSUMPTION
        return {
            "id": identifier,
            "machine_key": machine_key,
            "claim": claim,
            "clause": "(ii): a producer's snap of its own emission",
            "provisional": True,
            "data_sectors": [
                {"data_sector": index, "moved": detail} for index, detail in moved
            ],
        }

    def as_machine_record(self) -> dict[str, object]:
        """Return the record as a machine record."""
        return {
            "lattice_exponent": self.lattice_exponent,
            "lattice_invariant_statement": self.lattice_invariant_statement,
            "run_settings": {
                "strict_snaps": self.strict_snaps,
                "enclosed_references_used": self.enclosed_references_used,
            },
            "reference_kind": self.reference_kind,
            "six_condition_outcomes": dict(self.six_condition_outcomes),
            "blocks": [block.as_machine_record() for block in self.blocks],
            "displaced": self.displaced,
            "three_adr_0008_disclosures": list(self.three_adr_0008_disclosures),
            "rounding_directions": [
                {"bound": bound, "direction": direction, "why": why}
                for bound, direction, why in ROUNDING_DIRECTIONS
            ],
            "constant_rounding_directions": [
                {"entry": label, "constant": constant, "direction": direction}
                for label, constant, direction in self.constant_rounding_directions
            ],
            "snapped_measurement_assumption": self.snapped_measurement_assumption,
            "no_key_length_bound": NO_KEY_LENGTH_BOUND,
        }


@dataclass(frozen=True)
class WpfssData:
    """``{p_v}``, the flag basis, ``N`` and ``p`` -- on BOTH routes.

    Open implementation choice 5 is decided in the module docstring.
    ``encoded_in_target`` is ``True`` on the ``encoded`` route, where the
    weights ARE the flag diagonal of ``F^WP``, and ``False`` on the ``licensed``
    route, where they travel as the constraint entry of Corollary
    ``wpfss/cor:fssinstance`` instead (``wpfss/rem:tworoutes``).

    ``weight_provenance`` is the record the parameters table asks for: "This module
    takes them from ``eq:weightroute``; ANY SMALLER NON-NEGATIVE CHOICE IS ALSO VALID
    (Remark ``rem:weightfree``) AND THE ARTIFACT RECORDS WHICH WAS USED. ... The
    module therefore uses the LARGEST weight the artifact certifies, RECORDS it,
    is FREE TO BE GIVEN A SMALLER ONE, and NEVER SILENTLY SUBSTITUTES A LARGER
    ONE."
    """

    flag_basis: tuple[JointOutcome, ...]
    weights: tuple[Fraction, ...]
    cutoff: int
    total: Fraction
    encoded_in_target: bool
    weight_provenance: str = "eq:weightroute (Proposition prop:route)"

    def __post_init__(self) -> None:
        """Refuse a record whose weights do not index the declared flag basis."""
        if len(self.flag_basis) != len(self.weights):
            raise MalformedInputError(
                "wpfss_data carries one weight per flag basis vector, in the "
                "declared order of V (the outputs table)"
            )


@dataclass(frozen=True)
class AssumptionLedgerEntry:
    """One row of the emitted ledger: a machine key and what it constrains.

    The outputs table: "the machine keys of the assumption-ledger table, INCLUDING THE
    INHERITED RECEIVER ASSUMPTIONS, with the declared value of every parameter each one
    constrains".

    THE INHERITED SET IS THE SUPPLIER'S LEDGER, ENTIRE, AS MACHINE KEYS, not
    prose phrases. The emitted ledger
    carries, for the inherited receiver assumptions, THE SUPPLIER'S OWN MACHINE
    KEYS READ FROM THE RECEIVER ARTIFACT'S LEDGER, as they stand and in the
    supplier's order, together with that artifact's
    ``mathematical_spec_version`` (Assumption ``ass:recv``). A PROSE LIST IS
    NOT A KEY AND DOES NOT COMPOSE: an inherited assumption named only by an
    English phrase cannot be matched against the supplier's ledger by a
    consumer. THIS MODULE HOLDS NO LIST OF THE SUPPLIER'S KEYS (the ledger is passed
    through), so a key the supplier adds reaches
    this entry without an edit here; and a key the RECEIVER'S OWN presence
    rules make present that the artifact does not carry is a refusal
    (``receiver_spec_not_accepted``;
    :func:`certiqs_key.reductions.validation.required_receiver_keys`) rather
    than a silently shortened list.

    AN INHERITED KEY IS NOT NAMESPACED AGAINST A LOCAL ONE, because the keys do
    not collide. Short ids and machine keys are REPOSITORY-WIDE, so one string
    standing for two different assumptions across a docking boundary would be
    a defect rather than an open choice: this module's assumption is
    ``A-ROUND-SQ`` with machine key ``round_homogeneity_squashing``, and the
    supplier's ``round_homogeneity`` is carried unchanged, because it is the
    supplier's. THE TWO DO NOT COLLIDE AND NOTHING IS NAMESPACED: each key
    is one assumption's own, this module's entries carry their machine keys
    UNPREFIXED, and the inherited keys are carried on the SINGLE A-RECV
    entry in a field of their own, so the two lists cannot merge and no entry
    is lost. Namespacing one as ``receiver-povm@x.y.z:key`` would have put a
    string in an emitted artifact that no accepted contract fixes and would
    LOOK like the supplier's key while being this module's. What the contract
    does fix is that A-RECV "NAMES THE RECEIVER ARTIFACT BY VERSION", and
    ``inherited_from`` is that.

    ``inherited_declared`` IS THE ONE PIECE OF SUPPLIER CONTENT A-RECV NAMES.
    Of the inherited keys, A-RECV says of ``exact_window_eigenvalue_slack`` alone that
    "its declared slack ``eps_eig`` ... IS RECORDED IN THE EMITTED LEDGER
    BESIDE THE SETTINGS AT WHICH THE SUPPLIER SAYS IT WAS INVOKED". The field
    carries the supplier's own record for that key, read and never checked --
    "this module can NEITHER VERIFY NOR IMPROVE IT" -- and it is empty for
    every other key, because for those the contract asks for the key and
    nothing else.
    """

    assumption_id: str
    machine_key: str
    never_verifiable: bool
    #: The declared values the row's assumption is about, as immutable
    #: ``(name, value)`` pairs: strings where the row records a parameter by
    #: its printed value, structured values (tuples, nested pairs) where a
    #: submodule binds declared data (a branching model). Written to
    #: the record by :func:`certiqs_key.domain.bindings.as_json`.
    constrains: tuple[tuple[str, object], ...] = ()
    #: The supplier's machine keys, on the A-RECV entry and nowhere else,
    #: exactly as the supplied ledger carries them and in its order.
    inherited: tuple[str, ...] = ()
    inherited_from: str | None = None
    #: The supplier's declared record for `exact_window_eigenvalue_slack`:
    #: `eps_eig` and the settings at which the supplier says A-EIG was invoked.
    inherited_declared: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = ()


def assumption_ledger(
    constrained: Mapping[str, tuple[tuple[str, object], ...]],
    receiver_spec_version: str,
    inherited: Sequence[InheritedAssumption] = (),
    rows: Sequence[AssumptionRow] = CORE_ASSUMPTIONS,
) -> tuple[AssumptionLedgerEntry, ...]:
    """Return the assumption-ledger rows with their declared parameter values.

    THE ROWS ARE THE CALLER'S AND THE ORDER IS THE LEDGER'S
    (:attr:`AssumptionRow.order`). This function names no row and drops none:
    which rows an emission carries is decided by the emission, in
    :mod:`certiqs_key.reductions.emit`, because the one conditional core-ledger
    row -- A-SRC, present exactly when the emitted chain's source segment is
    non-empty -- is conditional on a datum that lives there and not here.

    ``never_verifiable`` is the row's own (:func:`~certiqs_key.reductions.
    reasons.ledger_row`): ``True`` exactly for a row whose assumption carries
    ``verification: never`` (spec/claim-format.md section 3.2), whichever
    module states it -- a core row, a submodule's, or one taken from the
    transmitter or the engine, which carries its owner's mark
    (``req:never-verified-assumptions``). No code path of this module decides
    what such an assumption says beyond its clauses on the declared data, and
    the ledger says so rather than reporting it as checked.

    ``inherited`` IS THE SUPPLIER'S OWN LEDGER, PASSED THROUGH AND NOT
    FILTERED. The A-RECV entry
    carries every key of the supplied ledger, as it stands and in the
    supplier's order; this function holds no list of the supplier's keys, so
    it drops none and adds none, and a key the receiver gains is carried
    without an edit here. A ledger short of a key the RECEIVER'S OWN presence
    rules make present never reaches this function, because the fail-closed
    table's receiver-spec row refuses the artifact first
    (``receiver_spec_not_accepted``;
    :func:`certiqs_key.reductions.validation.required_receiver_keys`): "A
    SILENTLY SHORTENED LIST" is the thing the contract forbids. The default is
    empty rather than a full list so that no caller can obtain an inherited
    list without supplying one. The supplier's record for
    ``exact_window_eigenvalue_slack`` travels beside its key, as A-RECV
    names it.
    """
    declared = {row.machine_key: row.constrains for row in inherited}
    supplied = tuple(row.machine_key for row in inherited)
    eig = declared.get(INHERITED_KEY_WITH_A_DECLARED_RECORD)
    ordered = sorted(rows, key=lambda row: row.order)
    return tuple(
        AssumptionLedgerEntry(
            assumption_id=row.identifier,
            machine_key=row.machine_key,
            never_verifiable=row.never_verifiable,
            constrains=constrained.get(row.identifier, ()),
            inherited=(supplied if row.identifier == "A-RECV" else ()),
            inherited_from=(
                receiver_spec_version if row.identifier == "A-RECV" else None
            ),
            inherited_declared=(
                ((INHERITED_KEY_WITH_A_DECLARED_RECORD, eig),)
                if row.identifier == "A-RECV" and eig is not None
                else ()
            ),
        )
        for row in ordered
    )


@dataclass(frozen=True)
class VerificationReport:
    """Every fail-closed row with its outcome, and the dependency identity.

    OPEN IMPLEMENTATION CHOICE 8 OF 12 IS DECIDED HERE. ``interface.yaml``: the
    contract "fixes the CONTENT ... and fixes that every such rule is decidable
    from declared data before anything is emitted. It fixes NO ENCODING: whether
    a rule's outcome is a boolean, a tri-state including 'not applicable', or a
    record carrying the datum it was decided on, IS NOT DECIDED HERE."

    THE DECISION: a TRI-STATE record per rule --
    :class:`~certiqs_key.reductions.validation.RuleOutcome`, carrying ``decided``,
    ``passed``, the refusal if any, and a prose ``detail`` naming the datum --
    in the contract's own row order, plus the receiver dependency identity. A
    boolean would be wrong for one reason: the fail-closed table's preamble says every
    rule "IS DECIDED FROM DECLARED DATA", and a rule that could not be decided
    on a given declaration must say so rather than report a vacuous pass. That
    distinction is load-bearing here, because two rows genuinely cannot be
    decided on an artifact path -- see :attr:`undecided`.

    IT ALSO RECORDS WHAT WAS ASKED FOR, AND EVERY TIER REACHES THIS FIELD.
    The ladder is the three tiers of ``foundations/def:tiers``
    (:class:`certiqs_key.foundations.assurance.Assurance`): ``estimate``, the
    diagnostic, ``first-order``, the headline, and ``certified``, a first-order
    number whose arithmetic is rigorously enclosed (PRINCIPLES.md sections 2.1
    and 10). The ``requested_assurance`` input row admits all three and
    REFUSES anything else under ``requested_assurance_unknown``, so this field
    carries whichever the request declared; a request naming ``certified``
    neither guarantees nor refuses that tier, which only the run's certified
    evaluation reaches. THE REFUSAL IS NOT A DEMOTION. Recording the request
    beside the inherited evaluation is the whole of what this record does with
    it: the propagation is unchanged and no tier is assigned anywhere.

    THE REPORT RE-DERIVES NOTHING. The outputs table's closing paragraph forbids it:
    "no receiver quantity is recomputed ... referenced, transported, and NEVER
    re-derived or re-quantified". The dependency identity is the artifact's
    declared ``mathematical_spec_version`` and ``bound_evaluation``, carried
    unchanged -- and ``bound_evaluation`` in particular is PROPAGATED AND NEVER
    UPGRADED (design.md).
    """

    outcomes: tuple[RuleOutcome, ...]
    receiver_spec_version: str
    receiver_bound_evaluation: str
    #: What the request ASKED FOR, beside what backed it: ``estimate``,
    #: ``first-order`` or ``certified``, whichever the request declared. A
    #: value outside the ladder is REFUSED by the requested-assurance row and
    #: never reaches an artifact. The two sit together here so that an artifact
    #: says both, and NEITHER IS A LABEL: the emitted ``status``
    #: is ``exact`` whatever was requested, and this module never upgrades
    #: ``bound_evaluation``. THE VALUE IS ONE OF
    #: :class:`certiqs_key.foundations.assurance.Assurance`'s, carried as its ``.value``
    #: string: this record is data a run logs, and holding the platform enum
    #: here would put ``certiqs_key.meat`` on the import graph of a module that
    #: may not have it (PRINCIPLES.md section 4). The one site that
    #: reaches the vocabulary is
    #: :func:`certiqs_key.reductions.emit._requested_assurance`, which says why.
    requested_assurance: str

    def __post_init__(self) -> None:
        """Refuse a report that repeats a row or omits one of the core's.

        THE CHECK IS NOT "EVERY ROW OF ONE FIXED LIST". The rows a reduction
        reports are the CORE'S plus the ones the instance builder declares, so
        one builder's reduction reports twenty-seven rows and another's
        twenty-eight, and a list frozen in this file could only be one of
        them. What stays
        checkable is what a report must satisfy whatever built it: every core
        row is present, and no row is reported twice. The ORDER is guaranteed
        by construction -- :func:`certiqs_key.reductions.emit.reduce` assembles
        the report by sorting the merged rows on their declared place in the
        interface's table -- and is not re-decided here.
        """
        rules = tuple(str(outcome.rule) for outcome in self.outcomes)
        if len(set(rules)) != len(rules):
            raise MalformedInputError(
                "the verification report carries each fail-closed row ONCE; a "
                "repeated row would report two outcomes for one decision"
            )
        missing = tuple(rule for rule in RULE_ORDER if str(rule) not in set(rules))
        if missing:
            raise MalformedInputError(
                "the verification report carries EVERY core fail-closed row "
                f"with its outcome; {missing!r} are absent"
            )

    @property
    def refusal(self) -> Refusal | None:
        """Return the FIRST refusal in the contract's row order, or ``None``."""
        return next(
            (outcome.refusal for outcome in self.outcomes if outcome.refusal), None
        )

    @property
    def undecided(self) -> tuple[RuleOutcome, ...]:
        """Return the rows that could not be decided on this declaration."""
        return tuple(outcome for outcome in self.outcomes if not outcome.decided)


@dataclass(frozen=True)
class ProofReductionArtifact:
    """The emitted artifact: every key of the outputs table, all present.

    The field names ARE the machine keys, in the contract's order, so that
    :data:`OUTPUT_KEYS` and the dataclass cannot drift apart -- a unit test
    asserts they agree.

    ``__post_init__`` enforces the presence rules the interface states, so
    that an artifact violating one cannot be constructed at all. That is
    stronger than validating on emission: the licence row has two
    reasons because the iff can break in two directions, and an object that
    cannot hold a broken iff cannot emit one.
    """

    source_descriptor: SourceDescriptor
    target_descriptor: TargetDescriptor
    #: PER OUTCOME, ONE SQUARE ARRAY PER SECTOR BLOCK, IN THE ORDER OF THE
    #: SECTOR MAP. The outputs table's `target_povm` row: "F_v IS the list
    #: (F_v^(s))_s, and F_v = (+)_s F_v^(s) is what that list MEANS, not an
    #: object the artifact carries"; the `target_descriptor` row: "NO FULL
    #: dim H(Q) x dim H(Q) ARRAY IS EMITTED, HERE OR ANYWHERE IN THIS
    #: ARTIFACT" (spec/architecture.md 2.8-2.9).
    target_povm: Mapping[JointOutcome, tuple[Matrix, ...]]
    outcome_correspondence: Mapping[JointOutcome, JointOutcome]
    squashing_channel: ChannelWitness
    exact_identity: ExactIdentity
    transported_operators: tuple[TransportedOperator, ...]
    reachable_set_statement: str
    constraint_list: tuple[ConstraintEntry, ...]
    attack_set_license: AttackSetLicence | None
    wpfss_data: WpfssData
    reduction_chain: Chain
    verification_report: VerificationReport
    assumption_ledger: tuple[AssumptionLedgerEntry, ...]
    route: Route
    status: LinkStatus = LinkStatus.EXACT
    #: the outputs table, ``emission_record``: **ALWAYS PRESENT**, and there is no
    #: presence rule to enforce and no ``None`` state to reason about. What this record
    #: carries -- ``kappa``, the six condition outcomes, and what the normalizer did per
    #: block -- exists whenever an artifact does. Typed without a default so that no
    #: artifact can be constructed without it: an emitted artifact whose emission record
    #: were absent would be asserting six passes it never recorded. KEYWORD-ONLY, so
    #: that requiring it moves no positional argument -- the same shape
    #: ``lattice_exponent`` has on the request, and for the same reason.
    emission_record: EmissionRecord = field(kw_only=True)
    #: The reference companion emitted beside this artefact, or the record of
    #: why none was (``req:reference-companion``; the output row
    #: ``reference_companion``). EVALUATION-ONLY: it is not part of what this
    #: artefact asserts and a consumer admits it under its own rule
    #: (``meat-core/req:companion-admission``). ``None`` only for an artefact
    #: built outside :func:`~certiqs_key.reductions.emit.reduce`.
    reference_companion: CompanionRecord | None = field(default=None, kw_only=True)
    #: The output row ``receiver_row_omitted_on_provenance``
    #: (``req:recv-row-provenance``): EMPTY where the A-RECV row is emitted;
    #: where it is omitted, the declared version of the receiver artefact the
    #: instance read, so that a consumer of this artefact sees why the row is
    #: absent. ALWAYS PRESENT in the machine record. The default is the empty
    #: tuple, which is what an artefact built outside
    #: :func:`~certiqs_key.reductions.emit.reduce` says: its ledger is what it
    #: carries.
    receiver_row_omitted_on_provenance: tuple[str, ...] = field(
        default=(), kw_only=True
    )
    #: ``artifact_bindings.mathematical_spec_version``: the module id at the
    #: version of the ACCEPTED contract, the same string as
    #: :data:`certiqs_key.reductions.MATHEMATICAL_SPEC_VERSION`, which is
    #: derived from the one literal
    #: :data:`certiqs_key.reductions.CONTRACT_VERSION`; a golden test asserts
    #: the equality. An artifact may not claim a draft version, and a
    #: ``-draft`` suffix is refused below.
    #:
    #: THE CLAIM GRAPH IS PINNED BY THIS VERSION AND IS CARRIED IN THE RUN
    #: MANIFEST, NOT HERE. PRINCIPLES.md section 2.1 asks a RESULT's manifest
    #: for "the assumption IDs, module versions and claim graph it rests on";
    #: a module artifact pins the module version, the assumption ledger carries
    #: the ids, and the claim ids behind them are resolved from the accepted
    #: version by whoever assembles the run record.
    mathematical_spec_version: str = "reductions@0.21.0"

    def __post_init__(self) -> None:
        """Enforce the two presence rules the interface and the rules state."""
        if (self.attack_set_license is not None) != bool(self.constraint_list):
            raise MalformedInputError(
                "attack_set_license is present EXACTLY WHEN the constraint list "
                "is non-empty (the outputs table, Definition def:link); the two "
                "directions are licence_missing and licence_without_constraints"
            )
        if self.status is not LinkStatus.EXACT:
            raise MalformedInputError(
                "certified_outer and exploratory_numeric are NEVER emitted by "
                "this module (the outputs table; design.md, 'Deferred "
                "extensions and where each attaches')"
            )
        if self.mathematical_spec_version.endswith("-draft"):
            raise MalformedInputError(
                "an artifact may not claim a draft version (the outputs table)"
            )
        if self.constraint_list and self.route is not Route.LICENSED:
            raise MalformedInputError(
                "a non-empty constraint list selects the licensed route: "
                "'Requesting any entry SELECTS the licensed route, because a "
                "non-empty list requires the licence' (the outputs table)"
            )
        if self.route is Route.ENCODED and self.constraint_list:
            raise MalformedInputError(
                "the encoded route emits an EMPTY constraint list (the inputs table)"
            )
        if self.receiver_row_omitted_on_provenance and any(
            entry.assumption_id == "A-RECV" for entry in self.assumption_ledger
        ):
            raise MalformedInputError(
                "receiver_row_omitted_on_provenance names the receiver artefact "
                "whose A-RECV row req:recv-row-provenance omitted, and the "
                "ledger carries that row all the same"
            )

    def as_machine_record(self) -> dict[str, object]:
        """Return the artifact as a machine record: every key, once each.

        NOTHING IS SERIALIZED TWICE. The emitted ``{F_v}`` matrices appear under
        ``target_povm`` and nowhere else: a chain link whose family IS the
        emitted target references it by the key name rather than repeating the
        matrices, and a link's constraint entries reference ``constraint_list``
        by entry label. A key-rate run logging this record therefore pays for
        each operator once.

        Exact values are written as :class:`~fractions.Fraction` strings and
        matrices as pairs of such strings
        (:func:`~certiqs_key.foundations.exact.serialize_matrix`), which read back
        without loss -- there is no numeric conversion anywhere in the record.

        EVERY ``Q``-OPERATOR IS SERIALIZED PER SECTOR BLOCK: ``target_povm``
        and each ``transported_operators`` entry become a LIST of square
        arrays whose dimensions are the sector map's, and the record carries
        no ``dim H(Q) x dim H(Q)`` array anywhere. A reader wanting the dense rendering
        forms the direct sum from the blocks and the sector map, which the record also
        carries.
        """
        emitted = tuple(self.target_povm[v] for v in self.wpfss_data.flag_basis)
        flags = self.wpfss_data.flag_basis
        settings = probe_settings_of(flags)
        record: dict[str, object] = {
            "source_descriptor": {
                "description": self.source_descriptor.description,
                "channel_block_dimensions": list(
                    self.source_descriptor.channel_grading.block_dimensions
                ),
                "channel_above_cutoff_finite": (
                    self.source_descriptor.channel_grading.above_cutoff_finite
                ),
                # GENERIC: no top-level keys of one model. The register that
                # arrives with the light is one instance's datum, so it is ONE
                # sub-record and it is ``None`` where the instance has no
                # register.
                "branch_register": (
                    None
                    if self.source_descriptor.branch_register is None
                    else {
                        "branches": list(self.source_descriptor.branch_register.labels),
                        "register_dimension": (
                            self.source_descriptor.branch_register.dimension
                        ),
                        "register_povm": {
                            label: serialize_matrix(
                                self.source_descriptor.branch_register.povm[label]
                            )
                            for label in self.source_descriptor.branch_register.labels
                        },
                    }
                ),
            },
            "target_descriptor": {
                "space_formula": self.target_descriptor.space_formula,
                "dimension_formula": self.target_descriptor.dimension_formula,
                "dimension": self.target_descriptor.dimension,
                "sectors": [
                    [mode, label]
                    for mode, label in self.target_descriptor.sectors.labels
                ],
                "sector_dimensions": list(self.target_descriptor.sectors.dimensions),
                "party_partition": self.target_descriptor.party_partition,
            },
            "target_povm": {
                outcome_label(v, settings): [
                    serialize_matrix(block) for block in self.target_povm[v]
                ]
                for v in flags
            },
            "outcome_correspondence": {
                "map": "identity on V = Y x T",
                "reason": (
                    "squashing does not relabel outcomes, and every relabelling "
                    "has already happened in the classical post-processing an "
                    "instance applies BEFORE the first squashing link"
                ),
                "alphabet": [outcome_label(v, settings) for v in flags],
            },
            "squashing_channel": self.squashing_channel.as_machine_record(),
            "exact_identity": {
                "statement": self.exact_identity.statement,
                "holds_by": self.exact_identity.holds_by,
                "status": str(self.exact_identity.status),
                "is_numerical_residual_check": (
                    self.exact_identity.is_numerical_residual_check
                ),
                "emission_snap_disposition": (
                    self.exact_identity.emission_snap_disposition
                ),
            },
            "transported_operators": [
                {
                    "label": entry.label,
                    "target_operator": [
                        serialize_matrix(block) for block in entry.target_operator
                    ],
                    "pullback": (
                        None
                        if entry.pullback is None
                        else serialize_matrix(entry.pullback)
                    ),
                    "pullback_expression": entry.pullback_expression,
                    "certificate_kind": str(entry.certificate_kind),
                    "relation": str(entry.relation),
                    "constant": str(entry.constant),
                    "certified_against": entry.certified_against,
                }
                for entry in self.transported_operators
            ],
            "reachable_set_statement": self.reachable_set_statement,
            "constraint_list": [
                {
                    "label": entry.label,
                    # PER SECTOR BLOCK, in the sector map's order, as
                    # `target_povm` and every transported operator are: an
                    # entry's hat O_k is an operator on Q and the
                    # `target_descriptor` row's "NO FULL dim H(Q) x dim H(Q)
                    # ARRAY IS EMITTED, HERE OR ANYWHERE IN THIS ARTIFACT" is a
                    # statement about the whole record (spec/architecture.md
                    # 2.8-2.9).
                    "operator": [
                        serialize_matrix(block) for block in entry.operator
                    ],
                    "relation": str(entry.relation),
                    "constant": str(entry.constant),
                    "theta_typing": entry.theta_typing,
                    "certificate_kind": str(entry.certificate_kind),
                    "certified_against": entry.certified_against,
                    "constant_is_declared": entry.constant_is_declared,
                    # sec:outputs, `constraint_list`: "THE FORM IS EMITTED WITH
                    # THE ENTRY, as the tag value `homogeneous` in
                    # trusted-source mode ... the docking is by key and NOTHING
                    # ABOUT THE FORM IS INFERRED AT EITHER END." `None` in
                    # untrusted-source mode, for which the contract names the
                    # scalar form and fixes no tag string (DeclaredForm).
                    "form": None if entry.form is None else str(entry.form),
                    # THE READING, AND THE KEYS APPEAR ONLY WHERE THERE IS ONE.
                    # `cor:entries`: an entry is emitted UNTAGGED and read in
                    # the form of its source mode, or -- where the measured
                    # system is a DECLARED product of party-scoped factors --
                    # with the tag `party_local` and the factor scope. "EVERY
                    # ENTRY OF A ONE-FACTOR EMISSION IS UNTAGGED AND IS WHAT IT
                    # WAS, clause for clause and constant for constant", and
                    # the record of such an entry is what it was too: a key
                    # spelling `None` would be a field the accepted row does
                    # not put on an untagged entry.
                    **(
                        {}
                        if entry.tag is None
                        else {"tag": str(entry.tag), "scope": entry.scope}
                    ),
                }
                for entry in self.constraint_list
            ],
            "attack_set_license": (
                None
                if self.attack_set_license is None
                else self.attack_set_license.as_machine_record()
            ),
            "wpfss_data": {
                "flag_basis": [outcome_label(v, settings) for v in flags],
                "weights": [str(weight) for weight in self.wpfss_data.weights],
                "cutoff": self.wpfss_data.cutoff,
                "total": str(self.wpfss_data.total),
                "encoded_in_target": self.wpfss_data.encoded_in_target,
                "weight_provenance": self.wpfss_data.weight_provenance,
            },
            # `wpfss`'s second output row: "the single value the request
            # carried". IT IS PROOF-RELEVANT AND NOT BOOKKEEPING -- the two
            # routes RUN ON DIFFERENT CHANNELS (wpfss/rem:tworoutes), so a
            # consumer reading this record must be able to tell which one
            # produced it without reading the request back.
            "route": str(self.route),
            # THE COMPOSITE IS THE PAIR (def:chain, eq:chaincomposite), AND
            # BOTH MEMBERS ARE EMITTED ALWAYS. `composite_witness` is the
            # RECEIVER composite, which thm:chain (i)-(iv) read alone;
            # `source_composite_witness` is the source composite, the IDENTITY
            # wherever the segment is empty. THE SEGMENT IS EMITTED EMPTY
            # RATHER THAN OMITTED, which the `link_record.source_segment` row
            # states in terms -- "presence: always emitted; EMPTY in every
            # artefact emitted today", "emitted EMPTY rather than omitted, SO
            # THAT A CONSUMER READS A SEGMENT AND NOT A SILENCE" -- so an
            # absent key is not available to say what an empty one says:
            # a consumer cannot tell a producer that emits no segment from one
            # whose segment is empty, and the pair form exists to be read as a
            # pair, and the row forbids conditional keys.
            "reduction_chain": {
                "order": list(self.reduction_chain.composite_order()),
                "composite_witness": (
                    self.reduction_chain.composite_witness().as_machine_record()
                ),
                "links": [
                    _link_record(link, emitted) for link in self.reduction_chain.links
                ],
                "source_segment": list(self.reduction_chain.source_segment),
                "source_composite_witness": (
                    self.reduction_chain.source_composite_witness(
                    ).as_machine_record()
                ),
            },
            "status": str(self.status),
            "verification_report": {
                "receiver_spec_version": (
                    self.verification_report.receiver_spec_version
                ),
                "receiver_bound_evaluation": (
                    self.verification_report.receiver_bound_evaluation
                ),
                "requested_assurance": (self.verification_report.requested_assurance),
                "rules": [
                    outcome.as_machine_record()
                    for outcome in self.verification_report.outcomes
                ],
            },
            "assumption_ledger": [
                {
                    "assumption_id": entry.assumption_id,
                    "machine_key": entry.machine_key,
                    "never_verifiable": entry.never_verifiable,
                    "constrains": {
                        name: as_json(value) for name, value in entry.constrains
                    },
                    "inherited": list(entry.inherited),
                    "inherited_from": entry.inherited_from,
                    # A-RECV: the supplier's `eps_eig` "IS RECORDED IN THE
                    # EMITTED LEDGER BESIDE THE SETTINGS AT WHICH THE SUPPLIER
                    # SAYS IT WAS INVOKED". Empty on every other entry.
                    "inherited_declared": {
                        key: dict(values) for key, values in entry.inherited_declared
                    },
                }
                for entry in self.assumption_ledger
            ],
            # req:recv-row-provenance: why the A-RECV row is absent, where it
            # is (the receiver artefact's version); empty where it is emitted.
            "receiver_row_omitted_on_provenance": list(
                self.receiver_row_omitted_on_provenance
            ),
            "emission_record": (self.emission_record.as_machine_record()),
            # THE REFERENCE COMPANION'S RECORD (req:reference-companion (v),
            # (vi)): whether one was emitted beside this artefact, why not
            # where none was, and its per-block record with a digest of its
            # exact data. ``None`` only for an artefact built outside
            # ``reduce`` (a hand-built record).
            "reference_companion": (
                None
                if self.reference_companion is None
                else self.reference_companion.as_record()
            ),
            "mathematical_spec_version": self.mathematical_spec_version,
        }
        if tuple(record) != self.record_keys():  # pragma: no cover - by tests
            raise MalformedInputError(
                "the emitted record is not the keys of one artefact "
                "(OUTPUT_KEYS without `factor_emission`, which belongs to an "
                "emission of several instances and to no single artefact)"
            )
        return record

    def record_keys(self) -> tuple[str, ...]:
        """Return the keys THIS artefact's machine record carries, in order.

        :data:`ONE_ARTEFACT_ONLY_KEYS`, and the presence rule it states:
        ``factor_emission`` is "PRESENT EXACTLY WHEN THE CALL DECLARES MORE
        THAN ONE INSTANCE" and carries "THE ORDERED LIST OF THE FACTORS'
        ARTEFACTS ... AND THE COMBINATION RULE", so it is a record ABOUT a list
        of artefacts and is emitted beside them by
        :mod:`certiqs_key.reductions.factors`, never inside one of them. An
        artefact that carried it would be one factor claiming to carry the
        others.
        """
        return ONE_ARTEFACT_ONLY_KEYS


def _family_record(
    family: SystemFamily, emitted: Sequence[tuple[Matrix, ...]]
) -> dict[str, object]:
    """Return a link family, referencing the emitted POVM rather than copying it.

    A family's POVM is a list of SECTOR-BLOCK LISTS wherever it has one, so the
    comparison with the emitted family and the inline serialization are both
    per block.
    """
    is_emitted = (
        family.povm is not None
        and len(family.povm) == len(emitted)
        and all(
            len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b, strict=True))
            for a, b in zip(family.povm, emitted, strict=True)
        )
    )
    return {
        "description": family.description,
        "dimension": family.dimension,
        "povm": (
            "target_povm" if is_emitted else (None if family.povm is None else "inline")
        ),
        "povm_inline": (
            None
            if family.povm is None or is_emitted
            else [
                [serialize_matrix(block) for block in element]
                for element in family.povm
            ]
        ),
    }


def _link_record(
    link: object, emitted: Sequence[tuple[Matrix, ...]]
) -> dict[str, object]:
    """Return one link's TEN slots, with ``link_id`` beside them and not among them."""
    return {
        "link_id": link.link_id,  # type: ignore[attr-defined]
        "slots": {
            "stage": str(link.stage),  # type: ignore[attr-defined]
            "kind": str(link.kind),  # type: ignore[attr-defined]
            "source_family": _family_record(link.source_family, emitted),  # type: ignore[attr-defined]
            "target": _family_record(link.target, emitted),  # type: ignore[attr-defined]
            "channel_witness": link.channel_witness.as_machine_record(),  # type: ignore[attr-defined]
            "carried_operator_pair": [
                list(link.carried_operator_pair[0]),  # type: ignore[attr-defined]
                list(link.carried_operator_pair[1]),  # type: ignore[attr-defined]
            ],
            "reachable_set_statement": link.reachable_set_statement,  # type: ignore[attr-defined]
            "constraint_entries": [
                entry.label
                for entry in link.constraint_entries  # type: ignore[attr-defined]
            ],
            "licence": (
                None
                if link.licence is None  # type: ignore[attr-defined]
                else "attack_set_license"
            ),
            "status": str(link.status),  # type: ignore[attr-defined]
        },
    }


@dataclass(frozen=True)
class ReductionOutcome:
    """What a reduction request returns: an artifact OR a refusal, never both.

    The conventions block, ``fail_closed``: "every failed validation produces a refusal
    with a machine-readable reason and NO ARTIFACT". The invariant is enforced
    in ``__post_init__``, so a caller cannot be handed both and cannot be handed
    neither.

    THE REPORT IS PRESENT EITHER WAY, and is the SAME OBJECT the artifact
    carries when one is emitted -- referenced, not copied. A refusal without a
    report would lose which rules had been decided before the failing one, and
    The outputs table asks for "every validation rule of the fail-closed table WITH ITS
    OUTCOME".
    """

    artifact: ProofReductionArtifact | None
    refusal: Refusal | None
    verification_report: VerificationReport

    def __post_init__(self) -> None:
        """Refuse an outcome that is neither a refusal nor an artifact, or both."""
        if (self.artifact is None) == (self.refusal is None):
            raise MalformedInputError(
                "a reduction returns an artifact OR a refusal and never both: a "
                "failure produces a refusal with a machine-readable reason and "
                "NO ARTIFACT (the conventions block, fail_closed)"
            )
        if self.artifact is not None and (
            self.artifact.verification_report is not self.verification_report
        ):
            raise MalformedInputError(
                "the emitted artifact carries THE report, not a copy of it"
            )

    @property
    def emitted(self) -> bool:
        """Whether an artifact was emitted."""
        return self.artifact is not None
