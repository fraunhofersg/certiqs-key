"""The fail-closed validation set, one function per ROW of the table.

"EVERY RULE BELOW IS DECIDED FROM DECLARED DATA BEFORE ANYTHING IS EMITTED; a
failure produces a refusal with a machine-readable reason and NO ARTIFACT."
Twenty-one rows, twenty-four reason strings, and one function per row. Each
returns a :class:`~certiqs_key.reductions.reasons.Refusal` or ``None`` and NEVER
RAISES ON DATA THE CONTRACT TYPES: a rule failure is a record, and the only
exceptions that can escape are those of :mod:`certiqs_key.reductions.errors`, for
arguments no rule can be read against.

WHY ONE FUNCTION PER ROW AND NOT ONE PER REASON
===============================================
Three rows name two reasons each, and each pair is TWO DIFFERENT FAILURES rather
than a spelling variant. Splitting by reason would lose which check produced
which; splitting by row keeps the ``verification_report`` output row -- "EVERY
VALIDATION RULE OF ``fail_closed`` WITH ITS OUTCOME" -- a record of twenty-one
decisions, which is what the row asks for.

WHICH ROWS ARE HERE, AND WHICH BELONG TO A SUBMODULE
====================================================
TWENTY-ONE of the twenty-eight rows. The other seven are about one squasher's
device model or about one branching model, and they live with it:

* ``wpfss`` owns SIX -- the fibre condition, the dark-count matrix's
  column-stochasticity and its descent, the absorbing condition, the routed
  total weight and the supplier's strengthening slot. Every one of them is a
  statement about the weight route of Proposition ``prop:route``, which is one
  squasher's construction.
* a branching submodule owns ONE -- that its declared model is well formed.
  Deleting that directory must leave this file whole, so the core may not name
  its row.

A ROW'S PLACE IN THE TABLE IS CARRIED BY ITS ``order`` FIELD
(:class:`certiqs_key.reductions.reasons.FailClosedRow`), not by this file's
member order, because the submodules' rows sit BETWEEN core ones. Which rows a
given reduction reports is the core's rows plus the ones THE INSTANCE BUILDER
DECLARES, assembled per call in :mod:`certiqs_key.reductions.emit`.

WHAT THESE RULES MAY NOT DO, IN THE CONTRACT'S OWN WORDS
========================================================
The conventions block, ``fail_closed``: "NO DEFAULT IS SUBSTITUTED FOR A MISSING DATUM,
NO WEIGHT IS CLIPPED INTO RANGE, NO FIBRE CONDITION IS WAIVED, AND NO LICENCE IS EMITTED
WITHOUT ITS CERTIFICATE." Nothing below repairs, normalizes, rounds or defaults; every
rule reads declared data and returns a verdict.

WHAT SECTION 4.14 DOES NOT COVER, AND WHY NO RULE IS INVENTED FOR IT
=====================================================================
The closing paragraph accounts for five of spec/architecture.md 5.4's conditions that
have no row: "TWO of spec/architecture.md 5.4's conditions are discharged UPSTREAM and
are re-checked here ONLY AS CONSISTENCY: a noncontractive receiver instrument and a
doubly applied efficiency are refusals of ``receiver-povm``, and THIS MODULE REFUSES AN
ARTIFACT THAT DOES NOT CARRY THAT CONTRACT'S VALIDATION RESULTS. TWO ARE IMPOSSIBILITIES
RATHER THAN FAILURES, by Lemma ``lem:ple1``. ONE -- the Douglas dominator and
contraction witness -- belongs to a link kind
this module REFUSES OUTRIGHT."

Three consequences, each implemented rather than assumed:

* the consistency re-check IS a refusal and the contract states it WITHOUT
  NAMING A REASON STRING. :func:`rule_receiver_spec` decides it, inside the
  receiver-spec row, whose subject -- "the receiver artifact resolves to an
  ACCEPTED contract version", Assumption A-RECV -- is what a missing validation
  record falls under. NO TWENTY-FIFTH STRING IS INVENTED; the alternative would
  be to leave a stated refusal unimplemented.
* ``p_v < 0`` and ``p > 1`` ARE IMPOSSIBILITIES and get no rule of their own.
  What :func:`rule_total_weight` decides is the boundary the construction needs,
  ``p < 1``, which the fail-closed table says runs "UNCONDITIONALLY" and "ON BOTH ROUTES
  DELIBERATELY -- one validity rule rather than two, fail-closed and
  conservative".
* the Douglas witness has no rule: a continuum family of devices is the
  planned family reduction, and the ``family-dominating`` kind that does exist
  is the ``domination`` submodule's link, which no requirement emits and which
  asks for no dominator.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

from certiqs_key.foundations.exact import (
    LATTICE_EXPONENT_MAX,
    LATTICE_EXPONENT_MIN,
    Matrix,
    add,
    dimension,
    equal,
    identity,
    is_binary64,
    is_hermitian,
    is_positive_semidefinite,
    linear_relations,
    loewner_ge,
    on_lattice,
    on_lattice_scalar,
    scale,
    span_dimension,
    spectral_bounds,
    sum_rounds_nowhere,
    zeros,
)
from certiqs_key.reductions.constraints import ConstraintEntry, certificate_holds
from certiqs_key.reductions.inputs import (
    PHOTON_BLOCK_FORMS,
    CarriedOperatorRequest,
    ChannelGrading,
    ConstraintForm,
    JointOutcome,
    Label,
    LinkDeclaration,
    ProbeDeclaration,
    ReceiverArtifactRows,
)
from certiqs_key.reductions.links import Chain
from certiqs_key.reductions.reasons import (
    LINK_KINDS_DEFERRED,
    FailClosedRule,
    LinkStatus,
    Refusal,
    RefusalReason,
    Route,
    reasons_of,
)

__all__ = [
    "RULE_ORDER",
    "ExactAdmissibilityDecision",
    "RuleOutcome",
    "refuse",
    "required_receiver_keys",
    "resolve_route",
    "rule_alphabet_order",
    "rule_approximate",
    "rule_block_structure_from_blocks",
    "rule_chain",
    "rule_constraint_certificate",
    "rule_constraint_channel",
    "rule_cutoff",
    "rule_device_family",
    "rule_emitted_family",
    "rule_exact_admissibility",
    "rule_lattice_exponent",
    "rule_licence_presence",
    "rule_licensed_hermiticity",
    "rule_link_kind",
    "rule_obstructions",
    "rule_post_processing_order",
    "rule_probe_weights",
    "rule_receiver_spec",
    "rule_requested_assurance",
    "rule_route",
    "rule_unsound_transplant",
]

#: The TWENTY-ONE CORE rows, in the order the interface's tables print them.
#: A submodule's rows are its own and are merged per call; see the module
#: docstring.
RULE_ORDER: tuple[FailClosedRule, ...] = tuple(FailClosedRule)


@dataclass(frozen=True)
class RuleOutcome:
    """One fail-closed row with its outcome, for the verification report.

    ``decided`` is ``False`` where the rule quantifies over data the declaration
    does not materialise -- Lemma ``lem:obstructions`` on a physical family that
    lives on a Fock space, for instance. It is NOT a pass: every rule "is
    decided from declared data", and a rule that could not be decided says so
    rather than reporting a vacuous success.

    ``rule`` is typed ``str`` and not an enum member, because a submodule's row
    is its own string and a core-typed enum could not hold it. The reasons the
    row can produce are read from the registry
    (:func:`certiqs_key.reductions.reasons.reasons_of`).
    """

    rule: str
    decided: bool
    refusal: Refusal | None
    detail: str = ""

    @property
    def passed(self) -> bool:
        """Whether the rule was decided and did not refuse."""
        return self.decided and self.refusal is None

    def as_machine_record(self) -> dict[str, object]:
        """Return the outcome as a machine record."""
        return {
            "rule": str(self.rule),
            "reasons": [str(reason) for reason in reasons_of(self.rule)],
            "decided": self.decided,
            "passed": self.passed,
            "refusal": (
                None if self.refusal is None else self.refusal.as_machine_record()
            ),
            "detail": self.detail,
        }


def refuse(rule: str, reason: str, detail: str) -> Refusal:
    """Return the refusal of a row, checking that the row can produce the reason.

    The check is against the registry, so a submodule's row is checked the same
    way the core's are and a row that is not registered at all refuses nothing:
    a reason emitted under a row that cannot carry it would make the machine
    record say two different things at once.
    """
    if reason not in reasons_of(rule):  # pragma: no cover - guarded by tests
        raise AssertionError(f"{reason} is not a reason of row {rule}")
    # THE MEMBER IS PASSED THROUGH, NOT ITS ``str``. A core reason is a
    # ``StrEnum`` member and a submodule's is a plain string; both ARE strings,
    # and passing the member keeps ``refusal.reason is RefusalReason.X`` the
    # identity test every carried golden writes it as.
    return Refusal(reason=reason, rule=rule, detail=detail)


# ---------------------------------------------------------------------------
#  Row 3: the receiver artifact resolves to an accepted contract version
# ---------------------------------------------------------------------------


def required_receiver_keys() -> tuple[str, ...]:
    """Return the machine keys the RECEIVER'S OWN presence rules make present.

    Assumption A-RECV (``ass:recv``; ``wpfss/rem:receiver-imports``): the
    A-RECV entry carries the supplier's ledger, and an artifact lacking a key
    the supplier's presence rules make present is refused rather than passed on
    as a silently shortened list. THIS MODULE HOLDS NO COPY OF EITHER: the
    ledger is passed through. The keys are read here from the receiver's own
    vocabulary, the one :mod:`certiqs_key.receiver.construct` emits its ledger
    under: every key of ``ASSUMPTION_MACHINE_KEYS``, in the receiver's order.
    The receiver's presence rule is "one row per file and every row on every
    artifact" (its ``outputs.assumption_ledger``), so no key is conditional and
    the required set does not depend on the artifact.

    THE IMPORT IS FUNCTION-LOCAL, and it points DOWNWARD (``reductions``
    depends on ``receiver`` in ``spec/modules.yaml``). The receiver package
    loads NumPy at import, and importing this package must load no array
    library (``tests/unit/test_reductions_fail_closed_properties.py``), so the
    arrow exists only while an artifact's receiver-spec row is decided, as the
    tier vocabulary's does in :mod:`certiqs_key.reductions.emit`.
    """
    from certiqs_key.receiver.reasons import ASSUMPTION_MACHINE_KEYS

    return tuple(ASSUMPTION_MACHINE_KEYS.values())


def rule_receiver_spec(
    artifact: ReceiverArtifactRows, accepted_versions: Sequence[str]
) -> Refusal | None:
    """Row 3: ``receiver_spec_not_accepted`` (``req:supplier-version-accepted``).

    THE FIRST TWO REFUSALS ARE REQUIREMENT ``req:supplier-version-accepted``:
    a version outside the caller's declared ``accepted_versions``, and an
    artifact without the supplier's validation results. That the declared set
    names only accepted versions, and that the artifact is genuine and true of
    the device, stay Assumption A-RECV (``ass:recv`` (i), (ii)). The last two
    are ``req:supplier-ledger-refusals``.

    "A DRAFT VERSION IS REFUSED", and the check is a STRING-LEVEL resolution
    against the supplier's accepted set rather than a numeric comparison: a
    ``-draft`` suffix on the same version number is still a refusal, because the
    accepted artifact is the one a human signed and a draft of it is not.

    THIS RULE DECIDES NOTHING ABOUT THE DEVICE. A-RECV is an assumption this module
    never verifies (its ``verification`` field is ``never``; spec/claim-format.md
    section 3.2, req:never-verified-assumptions); the conforming behaviour is exactly
    this test plus naming the artifact by version in the licence record.

    The consistency re-check named by the fail-closed table's closing
    paragraph is decided here too -- see the module docstring for why it lives
    in this row and why no new reason string is invented for it. The
    ``no_second_reason_string`` note of the ``receiver_artifact`` input row is
    what fixes that: the row is THE DECLARED CARRIER OF THREE REFUSALS UNDER
    ONE STRING, and ``receiver_spec_not_accepted`` is that string.
    """
    version = artifact.mathematical_spec_version
    if version not in tuple(accepted_versions):
        return refuse(
            FailClosedRule.RECEIVER_SPEC,
            RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED,
            f"{version!r} does not resolve to an accepted receiver contract "
            f"(accepted: {tuple(accepted_versions)!r}); a draft version may not "
            "back an emitted artifact",
        )
    if not artifact.validation_results_present:
        return refuse(
            FailClosedRule.RECEIVER_SPEC,
            RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED,
            "the artifact does not carry the receiver module's validation results; "
            "the fail-closed table's closing paragraph refuses such an artifact, the "
            "noncontractive-instrument and doubly-applied-efficiency conditions "
            "being discharged upstream and re-checked here as consistency",
        )
    # THE REQUIRED KEYS ARE THE RECEIVER'S OWN PRESENCE RULES, read from the
    # receiver itself.
    # A REPEATED KEY IS REFUSED, as a well-formedness check of the supplied
    # ledger and under the row's existing reason string. The ledger is passed
    # through as supplied, so a repeated key would be emitted twice, and the
    # A-EIG record lookup would keep one of two differing records and drop the
    # other silently; fail closed instead.
    keys = [row.machine_key for row in artifact.inherited_assumption_ledger]
    repeated = tuple(dict.fromkeys(key for key in keys if keys.count(key) > 1))
    if repeated:
        return refuse(
            FailClosedRule.RECEIVER_SPEC,
            RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED,
            f"the artifact's assumption ledger repeats the machine key(s) "
            f"{repeated!r}; Assumption A-RECV carries the supplier's own ledger "
            "entire, as supplied; a repeated key or a missing required key is "
            "refused",
        )
    carried = set(keys)
    missing = tuple(key for key in required_receiver_keys() if key not in carried)
    if missing:
        return refuse(
            FailClosedRule.RECEIVER_SPEC,
            RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED,
            "the artifact's assumption ledger does not carry the receiver "
            f"key(s) {missing!r} that the receiver's own presence rules make "
            "present; Assumption A-RECV carries the supplier's own ledger "
            "entire, as supplied; a repeated key or a missing required key is "
            "refused rather than passed on as a silently shortened list",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 4: the declared cutoff equals the receiver's echoed one
# ---------------------------------------------------------------------------


def rule_cutoff(declared_cutoff: int, artifact: ReceiverArtifactRows) -> Refusal | None:
    """Row 4: ``cutoff_mismatch``.

    "The quantifier domain of every weight is ``m > N``". The hazard is precise:
    the supplier certified its bound for ``m > N_supplier``, and consuming it at
    a smaller ``N`` would attach that weight to blocks where NOTHING WAS
    CERTIFIED -- spec/architecture.md 5.4's "bounds not uniform above the
    cutoff", in the unsafe direction.

    The grading is checked with the echo: ``block_dimensions`` runs ``0..N``, so
    a grading of the wrong length is the same mismatch by another route.
    """
    echoed = artifact.bound_quantifier_domain.cutoff
    if declared_cutoff != echoed:
        return refuse(
            FailClosedRule.CUTOFF,
            RefusalReason.CUTOFF_MISMATCH,
            f"declared photon_cutoff N = {declared_cutoff} but the receiver "
            f"artifact echoes N = {echoed}",
        )
    if artifact.channel_grading.cutoff != declared_cutoff:
        return refuse(
            FailClosedRule.CUTOFF,
            RefusalReason.CUTOFF_MISMATCH,
            "the declared photon-number grading runs 0.."
            f"{artifact.channel_grading.cutoff} but the cutoff is "
            f"{declared_cutoff}",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 5: the declared datum is presented against the instance's sector map
# ---------------------------------------------------------------------------


def rule_block_structure_from_blocks(
    photon_blocks: Mapping[JointOutcome, tuple[Matrix, ...]],
    grading: ChannelGrading,
    detection_alphabet: Sequence[Label],
    settings: Sequence[Label],
    *,
    photon_blocks_form: str = "bare",
) -> Refusal | None:
    """Row 5: THE STRUCTURAL HALF ONLY, on the declared per-``m`` list.

    THE INPUT FORM IS PART OF THE STRUCTURE (``wpfss`` input
    ``photon_blocks_form``): the supplied blocks are ``bare`` or
    ``dark_composed`` (``wpfss/def:weight-route``, the two input forms), and a
    value outside the two is refused here with ``no_block_structure``, the
    reason the interface names for that input.

    THE SECTOR-MAP COMPARISON of spec/architecture.md 2.9, and it REPLACES
    EVERY ZERO CHECK. The fail-closed table: the declared datum "is presented
    against the instance's SECTOR MAP: a block for every sector at every
    outcome of the sector's support, of the declared dimension, over the
    declared alphabets and in the declared orders". The datum is a per-sector
    list (``def:reduction-instance`` (I2)), so sector-block diagonality holds
    BY CONSTRUCTION, THERE IS NO OFF-SECTOR ENTRY TO WRITE AND THEREFORE NONE
    TO TEST -- which is why this row is the structural half only. THE NUMERICAL
    HALF IS THE NEXT ROW.

    WHAT IS DECIDED ELSEWHERE. This row decides the declared dimension.
    Hermiticity-and-positivity of each block and blockwise completeness at each
    setting are the NUMERICAL HALF, and belong to the EXACT-ADMISSIBILITY ROW
    (:func:`rule_exact_admissibility`, ``declaration_not_exactly_admissible``),
    which decides Definition ``def:exactadm`` (a)-(e) EXACTLY and per block on
    entry -- no window, no measured defect, no eigenvalue routine.

    The conventions block's ``fail_closed`` convention classifies this row: it is "a
    TYPE check", exact in the substrate of Definition ``def:substrate`` but NOT an
    instance of Lemma ``lem:exactpsd``, which it neither invokes nor needs.

    THE OPERATOR FORM OF BLOCK DIAGONALITY IS IMPORTED, NOT DECIDED. Assumption
    A-RECV imports the supplier's setting family and its channel-photon-number
    BLOCK DIAGONALITY (``receiver/def:setting-family`` (a)), and the supplier
    emits BLOCKS rather than whole operators precisely because it holds.

    THE SUBJECT IS THE DECLARED DATUM AND NOTHING ELSE
    (``def:reduction-instance`` (I1)). A submodule whose instance carries a
    branch the declaration does not characterise NARROWS THE SUBJECT to the
    branches it does -- an uncharacterised branch has no declared block
    structure to compare, and none is demanded of it -- and that narrowing
    lives in THAT SUBMODULE'S interface, adds no reason string, and goes away
    with it. Without any such narrowing the row's subject is the whole declared
    family, which is what this function decides.
    """
    if photon_blocks_form not in PHOTON_BLOCK_FORMS:
        return refuse(
            FailClosedRule.BLOCK_STRUCTURE,
            RefusalReason.NO_BLOCK_STRUCTURE,
            f"photon_blocks_form {photon_blocks_form!r} is not one of "
            f"{list(PHOTON_BLOCK_FORMS)} (wpfss/def:weight-route, the two input "
            "forms)",
        )
    expected = grading.block_dimensions
    for setting in settings:
        for index, dim in enumerate(expected):
            for letter in detection_alphabet:
                blocks = photon_blocks.get((letter, setting))
                if blocks is None:
                    return refuse(
                        FailClosedRule.BLOCK_STRUCTURE,
                        RefusalReason.NO_BLOCK_STRUCTURE,
                        "no photon-number blocks are declared for the outcome "
                        f"({letter!r}, {setting!r})",
                    )
                if len(blocks) != len(expected):
                    return refuse(
                        FailClosedRule.BLOCK_STRUCTURE,
                        RefusalReason.NO_BLOCK_STRUCTURE,
                        f"({letter!r}, {setting!r}) declares {len(blocks)} blocks "
                        f"where the grading declares {len(expected)}",
                    )
                block = blocks[index]
                if dimension(block) != dim:
                    return refuse(
                        FailClosedRule.BLOCK_STRUCTURE,
                        RefusalReason.NO_BLOCK_STRUCTURE,
                        f"block m = {index} of ({letter!r}, {setting!r}) has "
                        f"dimension {dimension(block)}, not the declared "
                        f"dim H(C_{index}) = {dim}",
                    )
    return None


# ---------------------------------------------------------------------------
#  Row 1: the declared lattice exponent kappa
# ---------------------------------------------------------------------------


def rule_lattice_exponent(
    value: object, *, alphabet_sizes: Mapping[str, int]
) -> Refusal | None:
    r"""Row 1: ``lattice_exponent_not_declared``. IT RUNS FIRST.

    The fail-closed table's first row, verbatim: "the request carries the declared
    lattice exponent ``kappa``, an integer with ``1 <= kappa <= 53`` and
    ``kappa + ceil(log2 max{|V|, |Y|, |T|}) <= 53``".

    "spec/architecture.md 2.9, condition **(D-LAT)**: the producer declares
    ``kappa``, THERE IS NO DEFAULT AND NO FALLBACK, and a defaulted lattice
    would decide a security-relevant predicate ON NOBODY'S AUTHORITY. **THIS
    ROW RUNS FIRST AND REFUSES BEFORE ANYTHING IS CONSTRUCTED**; the second
    inequality is what makes every completeness sum this contract states exact
    (Lemma ``lem:latsum``) and IS REFUSED UNDER THE SAME REASON."

    "RUNS FIRST" IS A STATEMENT ABOUT ORDER AND NOT MERELY ABOUT PRESENCE. The
    member :attr:`~certiqs_key.reductions.reasons.FailClosedRule.LATTICE_EXPONENT`
    is first in the enum and therefore first in :data:`RULE_ORDER`, and
    :func:`certiqs_key.reductions.emit.reduce` decides it before it reads any
    other declared datum. An implementation that decided another row before
    this one would have decided a predicate at an undeclared lattice.

    THREE THINGS ARE REFUSED UNDER ONE REASON, and the contract puts them
    there: a MISSING exponent ("a request that does not carry it is refused
    under the same reason"), an exponent outside ``[1, 53]``, and an exponent
    whose accumulation bound Eq. ``eq:latsumcond`` fails. The detail names
    which.

    A NON-INTEGER IS A REFUSAL AND NOT MALFORMED INPUT. The field is typed
    ``object`` for exactly this: the fail-closed table gives the row a reason string,
    so a value that cannot be presented could not be refused.

    Args:
        value: the declared ``lattice_exponent``, unvalidated.
        alphabet_sizes: ``|V|``, ``|Y|`` and ``|T|``, by name, for the
            accumulation bound. The bound is "a condition ON DECLARED COUNTS
            and CARRIES NO ARITHMETIC".
    """
    if value is None:
        return refuse(
            FailClosedRule.LATTICE_EXPONENT,
            RefusalReason.LATTICE_EXPONENT_NOT_DECLARED,
            "the request carries no lattice exponent; spec/architecture.md 2.9's "
            "condition (D-LAT) gives it NO DEFAULT AND NO FALLBACK, and a "
            "defaulted lattice would decide a security-relevant predicate on "
            "nobody's authority",
        )
    if isinstance(value, bool) or not isinstance(value, int):
        return refuse(
            FailClosedRule.LATTICE_EXPONENT,
            RefusalReason.LATTICE_EXPONENT_NOT_DECLARED,
            f"the declared lattice exponent {value!r} is not an integer; "
            "Eq. eq:latinv declares kappa as one",
        )
    if value < LATTICE_EXPONENT_MIN or value > LATTICE_EXPONENT_MAX:
        return refuse(
            FailClosedRule.LATTICE_EXPONENT,
            RefusalReason.LATTICE_EXPONENT_NOT_DECLARED,
            f"the declared lattice exponent kappa = {value} is outside "
            f"Eq. eq:latinv's {LATTICE_EXPONENT_MIN} <= kappa <= "
            f"{LATTICE_EXPONENT_MAX}; the upper bound is the binary64 "
            "significand, which is what makes a lattice value exactly a "
            "binary64 number",
        )
    largest = max(alphabet_sizes.values(), default=1)
    headroom = max(largest - 1, 1).bit_length() if largest > 1 else 0
    if value + headroom > LATTICE_EXPONENT_MAX:
        widest = max(alphabet_sizes, key=lambda name: alphabet_sizes[name])
        return refuse(
            FailClosedRule.LATTICE_EXPONENT,
            RefusalReason.LATTICE_EXPONENT_NOT_DECLARED,
            f"kappa + ceil(log2 max{{|V|, |Y|, |T|}}) = {value} + {headroom} = "
            f"{value + headroom} exceeds 53 at |{widest}| = {largest} "
            "(Eq. eq:latsumcond): the completeness sums Definition "
            "def:exactadm (e) requires to round nowhere are not guaranteed "
            "exact at this exponent, and Lemma lem:latsum is what makes that "
            "condition satisfiable rather than one refusing every family",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 2: the requested assurance is one of the tiers of foundations/def:tiers
# ---------------------------------------------------------------------------


def rule_requested_assurance(
    value: str, *, live_rungs: Sequence[str]
) -> Refusal | None:
    """Row 2: ``requested_assurance_unknown``.

    The fail-closed table: "The requested assurance is one of the three tiers
    of foundations/def:tiers, ``estimate``, ``first-order`` or ``certified``",
    REFUSED RATHER THAN DEMOTED, "a silent demotion being a caller receiving a
    weaker claim than it asked for without being told".

    THE LADDER IS THE ONE OF ``foundations/def:tiers``, ALL OF IT. Its third
    rung, ``certified``, is an a-posteriori verification
    of the first-order bound (PRINCIPLES.md section 10); the row admits a request naming
    it, and such a request neither guarantees nor refuses that tier (the interface's
    ``requested_assurance`` row: it is reached only by the run's certified
    evaluation). The row's subject is A VALUE THAT IS NOT ONE OF THE TIERS, so
    the reason string is ``requested_assurance_unknown``, not a name for a
    shelved rung.

    THIS ROW FAILS OPEN IF IT IS NOT PRESENT, which is why it is the second
    thing decided: a tier vocabulary that grows widens an enum loop without
    editing this module, and a row that REFUSES anything outside the declared
    live set is the fix. A demotion would not be.

    THE ROW IS STATED POSITIVELY AND NO DROPPED LABEL IS NAMED. The test is a
    membership test in ``live_rungs``, so NOTHING IN THIS PACKAGE HOLDS,
    CONSTRUCTS OR EMITS A TIER STRING OF ITS OWN; a request naming anything
    outside the ladder fails the membership test like any other value, and the
    refusal ECHOES the caller's own string, which is an input this module
    quotes rather than a label it holds.

    THE VOCABULARY IS REACHED AT ONE FUNCTION-LOCAL SITE and this row does not
    reach it: the caller passes the tier strings in, so that
    :mod:`certiqs_key.reductions.validation` carries no tier literal as a module
    constant either. See :func:`certiqs_key.reductions.emit._live_rungs`.

    Args:
        value: the declared ``requested_assurance``.
        live_rungs: the tier labels of the ladder, in ladder order.
    """
    if value in live_rungs:
        return None
    return refuse(
        FailClosedRule.REQUESTED_ASSURANCE,
        RefusalReason.REQUESTED_ASSURANCE_UNKNOWN,
        f"the request asks for {value!r}, which is not one of the live rungs "
        + ", ".join(repr(rung) for rung in live_rungs) + " of "
        "spec/architecture.md 2.8, so the request is REFUSED RATHER THAN "
        "DEMOTED -- a silent demotion being a caller receiving a weaker claim "
        "than it asked for without being told. The ladder has no further rung "
        "to demote to or to promote from: PRINCIPLES.md section 10 leaves it "
        "at the rungs named here",
    )


# ---------------------------------------------------------------------------
#  Row 6: the declared datum is EXACTLY admissible
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExactAdmissibilityDecision:
    """The exact-admissibility row's verdict and the conjuncts it decided.

    ``conjuncts`` names each of the five conditions of Definition
    ``def:exactadm`` (c) together with whether it held, in the order the row
    decides them. The fail-closed table requires that "THE REFUSAL NAMES WHICH ONE
    FAILED", and the outputs table's ``verification_report`` carries the row's
    outcome, so the row RETURNS the conjuncts rather than discarding everything
    but a boolean. THERE ARE NO MEASURED DEFECTS: nothing here measures, and
    there is no ``defects`` field.
    """

    refusal: Refusal | None
    conjuncts: tuple[tuple[str, bool], ...]


def rule_exact_admissibility(
    photon_blocks: Mapping[JointOutcome, tuple[Matrix, ...]],
    grading: ChannelGrading,
    detection_alphabet: Sequence[Label],
    settings: Sequence[Label],
    *,
    lattice_exponent: int,
) -> ExactAdmissibilityDecision:
    r"""Row 6: ``declaration_not_exactly_admissible``, DECIDED AND NOT MEASURED.

    The fail-closed table, verbatim: "the DECLARED RECEIVER BLOCKS
    ``blk M^{=m}_{y|t}``, ``m <= N`` --- AND THEY ALONE --- are EXACTLY
    ADMISSIBLE: exactly Hermitian, exactly positive semidefinite, exactly
    complete over ``Y`` at each ``(t, m)``, with that declared-order sum
    ROUNDING NOWHERE and every entry satisfying Eq. eq:latinv
    (Def. def:exactadm (c))."

    FIVE CONJUNCTS, and the row decides all five in the substrate of Lemma
    ``lem:exactpsd``:

    * **(b) Hermiticity** -- ``A = A-dagger``, ENTRY FOR ENTRY. Not a norm, not
      a defect, not a window.
    * **(c) positivity** -- ``A >= 0``, decided by Eq. ``eq:psdtest``. Remark
      ``rem:psdalgorithm`` excludes a floating-point eigenvalue BY NAME, and
      the reason is that a singular positive operator is exactly the case one
      gets wrong: "a procedure that returns an approximate eigenvalue DECIDES
      NOTHING EXACTLY, WHATEVER ITS ERROR BOUND".
    * **(d) completeness** -- ``sum_{y in Y} blk M^{=m}_{y|t} = 1`` on each
      block, AS AN IDENTITY OF THE ENTRIES, at each ``(t, m)``.
    * **(e) the sum rounds nowhere** -- every entrywise binary64 addition of
      that accumulation, IN THE DECLARED SUMMATION ORDER, is exact. This is a
      condition and not a remark about one, and the counterexample that
      establishes it is ``meat-core`` 1.0.0's, not reproduced here: "what this
      contract carries is THE OBLIGATION RATHER THAN THE ARGUMENT FOR IT".
    * **Eq. eq:latinv** -- ``2^kappa x in Z`` and ``|x| <= 1`` for every real
      and every imaginary part of every entry.

    CONJUNCT (a), THE SECTOR MAP, IS NOT DECIDED HERE. It is "a comparison of
    declared labels, decided and never measured" and it is the block-structure
    row's, which runs before this one: "THE NUMERICAL HALF IS THE NEXT ROW".

    NOTHING IS MEASURED AND NOTHING IS REPAIRED. There is no tolerance, no
    window, no defect and no threshold anywhere in this function. "THE PERTURBATION THIS
    ROW DOES NOT SEE was absorbed AT THE INSTANCE, before this module was reached, and
    its record is the instance's."

    THE ROW REACHES NO OTHER OPERATOR FAMILY: the objects an instance's
    hypotheses (H) are about "PRESENT NO MATRIX TO DECIDE ANYTHING ON"
    (``rem:exactboundary``, ``def:reduction-instance`` (I1)), and a submodule
    that declares one keeps its own row for it.

    Args:
        photon_blocks: the declared blocks, by ``(y, t)`` and then by ``m``.
        grading: the declared channel grading, for the block dimensions.
        detection_alphabet: the declared order of ``Y``, which is the
            SUMMATION ORDER conjunct (e) is decided in.
        settings: the declared order of ``T``.
        lattice_exponent: the declared ``kappa``, already validated by row 1.
    """
    conjuncts: list[tuple[str, bool]] = []
    first: Refusal | None = None

    def fail(name: str, detail: str) -> None:
        nonlocal first
        conjuncts.append((name, False))
        if first is None:
            first = refuse(
                FailClosedRule.EXACT_ADMISSIBILITY,
                RefusalReason.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                detail,
            )

    hermitian = True
    positive = True
    complete = True
    rounds_nowhere = True
    on_the_lattice = True

    for setting in settings:
        for index, _ in enumerate(grading.block_dimensions):
            family: list[Matrix] = []
            for letter in detection_alphabet:
                blocks = photon_blocks.get((letter, setting))
                if blocks is None or len(blocks) <= index:  # pragma: no cover
                    return ExactAdmissibilityDecision(first, tuple(conjuncts))
                family.append(blocks[index])

            for letter, block in zip(detection_alphabet, family, strict=True):
                site = f"blk M^{{={index}}}_{{{letter!r}|{setting!r}}}"
                if not is_hermitian(block):
                    if hermitian:
                        fail(
                            "hermiticity",
                            f"{site} is NOT exactly Hermitian; def:exactadm "
                            "(b) requires A = A-dagger ENTRY FOR ENTRY, and "
                            "this module carries no window in which a "
                            "near-Hermitian block could be admitted",
                        )
                    hermitian = False
                elif not is_positive_semidefinite(block):
                    if positive:
                        fail(
                            "positivity",
                            f"{site} is NOT exactly positive semidefinite; "
                            "def:exactadm (c), decided by Eq. eq:psdtest and "
                            "NEVER by an eigenvalue routine "
                            "(Rem. rem:psdalgorithm)",
                        )
                    positive = False
                if not on_lattice(block, lattice_exponent):
                    if on_the_lattice:
                        fail(
                            "lattice_invariant",
                            f"{site} carries an entry off the declared "
                            f"2^-{lattice_exponent} lattice; Eq. eq:latinv "
                            "requires 2^kappa x in Z and |x| <= 1 of every "
                            "real and every imaginary part, and a declaration "
                            "off it is REFUSED RATHER THAN ROUNDED INTO IT "
                            "(Rem. def:substrate)",
                        )
                    on_the_lattice = False

            total = zeros(grading.block_dimensions[index])
            for block in family:
                total = add(total, block)
            if not equal(total, identity(grading.block_dimensions[index])):
                if complete:
                    fail(
                        "completeness",
                        f"sum_y blk M^{{={index}}}_{{y|{setting!r}}} is NOT "
                        "exactly the identity; def:exactadm (d) states it AS "
                        "AN IDENTITY OF THE ENTRIES at each (t, m)",
                    )
                complete = False

            verdict = sum_rounds_nowhere(family)
            if not verdict.ok:
                if rounds_nowhere:
                    fail(
                        "declared_order_sum",
                        "the declared-order completeness sum on block "
                        f"m = {index} at setting {setting!r} ROUNDS: the "
                        f"addition of element {verdict.first_inexact_index} "
                        f"at entry {verdict.first_inexact_entry} leaves the "
                        "binary64 lattice, so def:exactadm (e) fails and the "
                        "COMPUTED sum is not the sum of (d)",
                    )
                rounds_nowhere = False

    for name, held in (
        ("hermiticity", hermitian),
        ("positivity", positive),
        ("completeness", complete),
        ("declared_order_sum", rounds_nowhere),
        ("lattice_invariant", on_the_lattice),
    ):
        if held:
            conjuncts.append((name, True))
    return ExactAdmissibilityDecision(first, tuple(conjuncts))


# ---------------------------------------------------------------------------
#  Row 7: the EMITTED family satisfies all six (D-EMIT)
# ---------------------------------------------------------------------------


def rule_emitted_family(
    family: Mapping[JointOutcome, tuple[Matrix, ...]],
    order: Sequence[JointOutcome],
    block_dimensions: Sequence[int],
    *,
    lattice_exponent: int,
    sector_map_agrees: bool,
    strict_refusal: str | None = None,
) -> Refusal | None:
    r"""Row 7: ``emitted_family_not_admissible``. THE SECOND GATE.

    Implements ``reductions/req:emission-refusal``: the engine emits a family
    only if the six conditions hold of the numbers about to be emitted,
    decided exactly after the emission normalizer, and otherwise refuses
    naming the predicate that failed; and, where the run declares the strict
    option and no reference companion is formed beside the artefact, it
    refuses every moved class of ``def:emitnorm``, naming the data sector,
    the class, the cause and the fix (``strict_refusal``). Without that option
    no class is refused for being moved: on declared data that pass the
    refusal rules every
    path of the normalizer produces a family the six hold of, so the decision
    below is a DEFENSIVE EXACT CHECK (``thm:emit`` (ii), proof).

    The fail-closed table, verbatim: "the EMITTED family ``{F_v}`` satisfies all six
    conditions **(D-EMIT)** --- the sector map, exact Hermiticity, exact
    positive semidefiniteness, exact completeness per sector block, the
    declared-order sum rounding nowhere, and Eq. eq:latinv of every entry ---
    DECIDED ON THE NUMBERS ABOUT TO BE EMITTED, AFTER THE EMISSION NORMALIZER
    WHERE THAT ACTED."

    THE ONLY ROW OF SECTION 4.14 WHOSE SUBJECT IS THIS MODULE'S OWN NUMBERS.
    "This module DECIDES WHAT IT IS ABOUT TO EMIT AND REFUSES RATHER THAN
    EMITTING A FAMILY IT HAS NOT ESTABLISHED, which is what makes the emitted
    status A STATEMENT ABOUT THE ARTIFACT rather than about a construction the
    artifact does not carry, and what lets a consumer RE-DECIDE THE SAME SIX
    CONDITIONS AND REACH THE SAME ANSWER" (``thm:emit`` (ii)).

    ALL SIX, NOT THE THREE THAT CHANGED. ``def:emitnorm`` (4): "All six
    conditions are decided last, after (2) or (3), each of which changes
    partial sums from the touched element onward".

    COMPLETENESS IS DECIDED OVER ``V`` AND PER SECTOR BLOCK. ``def:emitnorm``
    restores it PER CLASS, and summing over ``t`` with ``sum_t q_t = 1`` gives
    completeness over ``V`` as well; this row decides the consequence, which
    is what ``def:exactadm`` (d) states for the emitted family.

    THE REFUSAL NAMES THE PREDICATE THAT FAILED -- the contract says so twice,
    at this row and at ``def:emitnorm`` (4).

    WHY THIS IS NOT ROUTED THROUGH A SHARED SNAPPING KERNEL.
    spec/architecture.md 2.9 declares a shared snapping kernel
    (``foundations/snap.py``) with a producer-side
    check whose docstring names the (D-EMIT) (ii)-(v) use -- so it would be
    the obvious call to make. It is not made, for two reasons, recorded
    here rather than left to be re-derived.

    * **A modulus test is not Eq. eq:latinv.** Refusing an entry whose SQUARED
      MODULUS exceeds one would refuse ``0.75 + 0.75i``, which this contract
      admits: ``def:exactadm`` (b) says "a complex entry satisfies eq:latinv
      WHEN ITS REAL AND IMAGINARY PARTS DO", a bound on each PART. The kernel
      decides part by part, so this reason does not apply; the next one
      stands.
    * **Its substrate is binary64 arrays and this module's is exact
      rationals** (Def. ``def:substrate``). Routing a decision through a
      lossy representation to decide whether the numbers are representable
      inverts the question.

    So the six conditions are decided here, from ``def:exactadm``, in this
    module's own substrate; when ``domain/snap.py`` (now ``foundations/snap.py``)
    arrives, this is the
    predicate it must agree with.

    Args:
        family: the numbers about to be emitted, by ``v`` and then by block.
        order: the declared order of ``V``, which is the summation order.
        block_dimensions: the declared dimension of each preserved block.
        lattice_exponent: the declared ``kappa``.
        sector_map_agrees: condition (a), decided by the caller as a
            comparison of declared labels, kinds, dimensions and orders.
        strict_refusal: where the run declares the strict option, the
            normalizer moved a class and no reference companion is formed,
            the account of the first such class (data sector, class, cause,
            fix); ``None`` otherwise.
    """
    if strict_refusal is not None:
        return refuse(
            FailClosedRule.EMITTED_FAMILY,
            RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE,
            strict_refusal,
        )
    if not sector_map_agrees:
        return refuse(
            FailClosedRule.EMITTED_FAMILY,
            RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE,
            "the sector map of the emitted family is not the one the consumer "
            "holds (def:exactadm (c), clause (a)): a comparison of declared "
            "labels, decided and never measured",
        )
    for index, dim in enumerate(block_dimensions):
        sector = [family[outcome][index] for outcome in order]
        for outcome, block in zip(order, sector, strict=True):
            site = f"F_{outcome!r} on block m = {index}"
            if not is_hermitian(block):
                return refuse(
                    FailClosedRule.EMITTED_FAMILY,
                    RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE,
                    f"{site} is not exactly Hermitian (def:exactadm (b))",
                )
            if not is_positive_semidefinite(block):
                return refuse(
                    FailClosedRule.EMITTED_FAMILY,
                    RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE,
                    f"{site} is not exactly positive semidefinite "
                    "(def:exactadm (c), decided by Eq. eq:psdtest)",
                )
            if not on_lattice(block, lattice_exponent):
                return refuse(
                    FailClosedRule.EMITTED_FAMILY,
                    RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE,
                    f"{site} carries an entry off the declared "
                    f"2^-{lattice_exponent} lattice (Eq. eq:latinv)",
                )
        total = zeros(dim)
        for block in sector:
            total = add(total, block)
        if not equal(total, identity(dim)):
            return refuse(
                FailClosedRule.EMITTED_FAMILY,
                RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE,
                f"sum_v F_v on block m = {index} is not exactly the identity "
                "(def:exactadm (d)); def:emitnorm (3) restores completeness "
                "per class and sum_t q_t = 1 carries it to V, so a failure "
                "here says one of those two did not hold",
            )
        verdict = sum_rounds_nowhere(sector)
        if not verdict.ok:
            return refuse(
                FailClosedRule.EMITTED_FAMILY,
                RefusalReason.EMITTED_FAMILY_NOT_ADMISSIBLE,
                f"the declared-order sum of the emitted family on block "
                f"m = {index} ROUNDS at element "
                f"{verdict.first_inexact_index}, entry "
                f"{verdict.first_inexact_entry} (def:exactadm (e))",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 15: {q_t} is a probability distribution declared by the protocol
# ---------------------------------------------------------------------------


def rule_probe_weights(
    probe: ProbeDeclaration, *, lattice_exponent: int | None = None
) -> Refusal | None:
    """Row 15: ``probe_weights_ill_formed`` (Assumption A-PROBE).

    "Finite non-empty, ``q_t > 0``, ``sum_t q_t = 1``." The two violations fail
    different things and both are refused. A sum ``!= 1`` breaks Lemma
    ``lem:linear`` (ii)'s completeness computation
    ``sum_{y,t} q_t M_{y|t} = sum_t q_t 1``, so the joint family IS NOT A POVM. A
    zero weight keeps completeness but breaks the STRICT positivity the row
    states, and with it the reading that every declared setting actually occurs
    -- a setting of weight zero would contribute a flag basis vector to ``V``
    with no statistics behind it.
    """
    if not probe.settings:
        return refuse(
            FailClosedRule.PROBE_WEIGHTS,
            RefusalReason.PROBE_WEIGHTS_ILL_FORMED,
            "T is empty; the inputs table requires it finite and NON-EMPTY",
        )
    if set(probe.weights) != set(probe.settings):
        return refuse(
            FailClosedRule.PROBE_WEIGHTS,
            RefusalReason.PROBE_WEIGHTS_ILL_FORMED,
            "the probe weights are not indexed by the declared T",
        )
    for setting in probe.settings:
        weight = probe.weights[setting]
        if weight <= 0 or weight > 1:
            return refuse(
                FailClosedRule.PROBE_WEIGHTS,
                RefusalReason.PROBE_WEIGHTS_ILL_FORMED,
                f"q_{setting} = {weight} is not in (0, 1]; a setting of weight "
                "zero would contribute a flag basis vector with no statistics "
                "behind it, and q_t <= 1 IS USED AS AN EXACT BOUND IN "
                "prop:route",
            )
        # Every declared REAL SCALAR satisfies Eq. eq:latinv.
        # def:exactadm (b) names them -- "the q_t, the p_i, the entries of R,
        # and any declared device constant" -- and a probe weight off the
        # lattice takes the whole post-processed family off it, step 2 of
        # The receiver-consumption block multiplying every block by q_t.
        if lattice_exponent is not None and not on_lattice_scalar(
            weight, lattice_exponent
        ):
            return refuse(
                FailClosedRule.PROBE_WEIGHTS,
                RefusalReason.PROBE_WEIGHTS_ILL_FORMED,
                f"q_{setting} = {weight} is off the declared "
                f"2^-{lattice_exponent} lattice; Eq. eq:latinv is a condition "
                "on EVERY declared real scalar (def:exactadm (b)) and not only "
                "on the operator entries",
            )
    total = sum(probe.weights.values(), start=Fraction(0))
    if total != 1:
        return refuse(
            FailClosedRule.PROBE_WEIGHTS,
            RefusalReason.PROBE_WEIGHTS_ILL_FORMED,
            f"sum_t q_t = {total} != 1, so lem:linear (ii)'s completeness "
            "computation fails and the joint family is not a POVM",
        )
    # The declared-order sum ROUNDS NOWHERE. "lem:latsum is why
    # THE THIRD IS SATISFIABLE rather than a condition that would refuse every
    # declaration", and sum_t q_t = 1 "IS WHAT CARRIES THE PER-SETTING
    # COMPLETENESS OF def:emitnorm (3) TO COMPLETENESS OVER V" -- so a sum that
    # rounds would break the emitted family's completeness, not merely a
    # bookkeeping identity.
    running = Fraction(0)
    for index, setting in enumerate(probe.settings):
        running += probe.weights[setting]
        if not is_binary64(running):
            return refuse(
                FailClosedRule.PROBE_WEIGHTS,
                RefusalReason.PROBE_WEIGHTS_ILL_FORMED,
                f"the declared-order sum of {{q_t}} ROUNDS at element {index} "
                f"(setting {setting!r}, partial sum {running}); def:exactadm "
                "(e)'s condition is on the ADDITIONS and not on the total",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 16: every declared relation passes Lemma lem:obstructions
# ---------------------------------------------------------------------------


def rule_obstructions(
    physical: Sequence[Matrix], target: Sequence[Matrix]
) -> Refusal | None:
    """Row 16: ``declared_relation_impossible``.

    "A cheap refusal before any construction is attempted." Lemma
    ``lem:obstructions``, both legs.

    (i) SPECTRAL INCLUSION. ``spec(M_v) subset [inf spec F_v, sup spec F_v]``,
    whose PROOF is the operator statement: "with ``a := inf spec X`` and
    ``b := sup spec X`` we have ``a 1_Q <= X <= b 1_Q``; applying the positive
    unital map ``Lambda^dagger`` preserves both inequalities, so
    ``a 1_B <= X' <= b 1_B``". The bounds are algebraic numbers and in general
    irrational, so this rule uses the exact RATIONAL enclosure of
    :func:`~certiqs_key.foundations.exact.spectral_bounds` -- which IS the spectrum's
    hull whenever ``F_v`` is diagonal, and every emitted target of this module is
    sector-block-diagonal with one-dimensional flag sectors. A violation of the
    enclosure is a RATIONAL PROOF that no channel realizes the relation; where
    the enclosure is loose the rule refuses less than (i) forbids, which is the
    safe direction for a necessary condition and is recorded on the outcome
    rather than hidden.

    (ii) SPAN MONOTONICITY. ``dim span{M_v} <= dim span{F_v} <= (dim H(Q))^2``,
    "and every linear relation ``sum_v a_v F_v = c 1_Q`` FORCES
    ``sum_v a_v M_v = c 1_B``". Both are exact rational linear algebra: the span
    dimensions are ranks, and the relations are the null space of
    ``(a, c) -> sum_v a_v F_v - c 1_Q``, each of whose basis vectors is tested on
    the physical side.
    """
    if len(physical) != len(target) or not physical:
        return refuse(
            FailClosedRule.OBSTRUCTIONS,
            RefusalReason.DECLARED_RELATION_IMPOSSIBLE,
            "the two families of a declared relation are over the same finite "
            "alphabet (def:squashing); the declared ones are not",
        )
    source_dim = dimension(physical[0])
    target_dim = dimension(target[0])
    for index, (physical_element, target_element) in enumerate(
        zip(physical, target, strict=True)
    ):
        if not is_hermitian(physical_element) or not is_hermitian(target_element):
            return refuse(
                FailClosedRule.OBSTRUCTIONS,
                RefusalReason.DECLARED_RELATION_IMPOSSIBLE,
                f"the declared POVM elements at index {index} are not Hermitian",
            )
        bounds = spectral_bounds(target_element)
        upper = scale(bounds.upper, identity(source_dim))
        lower = scale(bounds.lower, identity(source_dim))
        if not loewner_ge(upper, physical_element) or not loewner_ge(
            physical_element, lower
        ):
            return refuse(
                FailClosedRule.OBSTRUCTIONS,
                RefusalReason.DECLARED_RELATION_IMPOSSIBLE,
                f"lem:obstructions (i) fails at index {index}: M_v does not lie "
                f"in [{bounds.lower}, {bounds.upper}] 1_B, an exact rational "
                f"enclosure of spec(F_v) (tight: {bounds.tight})",
            )
    physical_span = span_dimension(list(physical))
    target_span = span_dimension(list(target))
    if physical_span > target_span:
        return refuse(
            FailClosedRule.OBSTRUCTIONS,
            RefusalReason.DECLARED_RELATION_IMPOSSIBLE,
            f"lem:obstructions (ii) fails: dim span{{M_v}} = {physical_span} > "
            f"{target_span} = dim span{{F_v}}",
        )
    if target_span > target_dim * target_dim:
        return refuse(
            FailClosedRule.OBSTRUCTIONS,
            RefusalReason.DECLARED_RELATION_IMPOSSIBLE,
            f"lem:obstructions (ii) fails: dim span{{F_v}} = {target_span} > "
            f"{target_dim * target_dim} = (dim H(Q))^2",
        )
    for relation in linear_relations(list(target), identity(target_dim)):
        coefficients, constant = relation[:-1], relation[-1]
        accumulated = zeros(source_dim)
        for coefficient, element in zip(coefficients, physical, strict=True):
            accumulated = add(accumulated, scale(coefficient, element))
        expected = scale(constant, identity(source_dim))
        if not equal(accumulated, expected):
            return refuse(
                FailClosedRule.OBSTRUCTIONS,
                RefusalReason.DECLARED_RELATION_IMPOSSIBLE,
                "lem:obstructions (ii) fails: the target satisfies the linear "
                f"relation with coefficients {tuple(coefficients)} and c = "
                f"{constant}, which unitality forces on the physical side and "
                "which does not hold there",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 17: the chain is composable, tuple-chained and stage-ordered
# ---------------------------------------------------------------------------


def rule_chain(chain: Chain) -> Refusal | None:
    """Row 17: ``chain_ill_formed`` / ``source_link_after_receiver_link``.

    TWO REASONS, TWO FAILURES. (C1) and (C2) are about SHAPE -- a target that is
    not the next source family, or a carried tuple that does not chain -- and
    carry ``chain_ill_formed``. (C3) is about ORDER and carries
    ``source_link_after_receiver_link``, for the reason Remark ``rem:ordering``
    gives: a source link after a receiver link needs the inclusion
    ``A^real_1 o Gamma subset A^virtual_1``, "and NOTHING IN THIS CONTRACT
    ESTABLISHES IT FOR ANY ``Gamma``".

    A chain failing more than one condition names the FIRST in Definition
    ``def:chain``'s own order, (C1) then (C2) then (C3), so that the reason a
    caller receives does not depend on which condition was tested last. The full
    verdict of all three is on the
    :class:`~certiqs_key.reductions.links.ChainConditionOutcome`.
    """
    outcome = chain.conditions()
    failing = outcome.first_failing_condition
    if failing is None:
        return None
    reason = (
        RefusalReason.SOURCE_LINK_AFTER_RECEIVER_LINK
        if failing == "C3"
        else RefusalReason.CHAIN_ILL_FORMED
    )
    return refuse(FailClosedRule.CHAIN, reason, outcome.detail)


# ---------------------------------------------------------------------------
#  Row 18: the requested link kind is implemented by this module
# ---------------------------------------------------------------------------


def rule_link_kind(declarations: Sequence[LinkDeclaration]) -> Refusal | None:
    """Row 18: ``link_kind_deferred`` (``req:reserved-link-kinds``).

    Implements ``reductions/req:reserved-link-kinds``: the engine emits no
    receiver-stage link of the reserved kind ``label-space`` and refuses a
    request that declares one; ``source-map`` is the transmitter's
    source-stage kind and is refused here under the same string. The kind
    ``family-dominating`` is not reserved: it is the ``domination``
    submodule's, which no requirement emits, and a request that declares it
    names a link this module does not build, which the chain row refuses.
    """
    for index, declaration in enumerate(declarations):
        if declaration.kind in LINK_KINDS_DEFERRED:
            return refuse(
                FailClosedRule.LINK_KIND,
                RefusalReason.LINK_KIND_DEFERRED,
                f"link {index} declares kind {declaration.kind.value!r}, which "
                "this module reserves and refuses; design.md names its docking "
                "point",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 19: no approximate relation is offered
# ---------------------------------------------------------------------------


def rule_approximate(declarations: Sequence[LinkDeclaration]) -> Refusal | None:
    """Row 19: ``approximate_squashing_unsupported``.

    "Theorem ``thm:transfer`` has NO PENALTY SLOT." design.md's deferrals: approximate
    squashing is "deliberately NOT a parameter of Theorem ``thm:transfer``: that
    theorem is AN EQUALITY OF OUTPUT STATES WITH NO PENALTY SLOT, so an
    approximate relation needs A NEW THEOREM converting the error into a security
    penalty, and UNTIL THERE IS ONE THE REQUEST IS REFUSED."

    The docking point is the STATUS value ``certified_outer``, which this module
    never emits; ``exploratory_numeric`` is refused with it. The exact substitute
    that IS available is operator domination with a declared weight (Corollary
    ``cor:instances`` (i)).
    """
    for index, declaration in enumerate(declarations):
        if declaration.requested_status != LinkStatus.EXACT.value:
            return refuse(
                FailClosedRule.APPROXIMATE,
                RefusalReason.APPROXIMATE_SQUASHING_UNSUPPORTED,
                f"link {index} requests status "
                f"{declaration.requested_status!r}; thm:transfer has no penalty "
                "slot, so this module emits `exact` only",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 20: no device FAMILY is declared
# ---------------------------------------------------------------------------


def rule_device_family(artifact: ReceiverArtifactRows) -> Refusal | None:
    """Row 20: ``device_family_unsupported``.

    spec/architecture.md 5.4: "a continuum family checked at sampled
    points". Assumption A-RECV: "a single device family, uncertainty set or
    characterization protocol appears NOWHERE: THIS MODULE REDUCES ONE DECLARED
    RECEIVER."

    This refusal is also one of the four reasons design.md gives for judging
    the family-wide-optical-bound escalation trigger NOT to fire.
    """
    if artifact.declared_device_family:
        return refuse(
            FailClosedRule.DEVICE_FAMILY,
            RefusalReason.DEVICE_FAMILY_UNSUPPORTED,
            "the receiver artifact declares a device family "
            f"{artifact.declared_device_family!r}; this module reduces ONE "
            "declared receiver",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 21: every entry has a certificate, and every c_k is declared
# ---------------------------------------------------------------------------


def rule_constraint_certificate(
    entries: Sequence[ConstraintEntry],
    pullbacks: Mapping[str, Matrix],
    *,
    theorem_discharged: Mapping[str, str] = MappingProxyType({}),
    decided_before_this_row: Mapping[str, str] = MappingProxyType({}),
) -> Refusal | None:
    """Row 21: ``constraint_without_certificate`` / ``data_dependent_constant``.

    TWO REASONS, TWO FAILURES. The first is Eq. ``eq:certificate`` not holding
    for the declared ``(bowtie_k, c_k)`` -- Theorem ``thm:licence``'s hypothesis,
    recomputed and not trusted. The second is Assumption A-CONST: "every constant
    ``c_k`` in an emitted entry is FIXED BEFORE THE PROTOCOL RUN by the device
    fact that certifies it, and IS NOT A FUNCTION OF ANY STATISTIC OBSERVED
    DURING THE RUN", and Remark ``rem:notlicensed`` (c) adds that such an entry
    "would be UNSOUND HERE REGARDLESS OF PROVENANCE, and the module REFUSES TO
    BUILD ONE".

    THE DATA-DEPENDENCE CHECK IS ON THE DECLARATION AND NOT AN INFERENCE. No
    function of the emitted data can tell whether a number came from a run, which
    is exactly why A-CONST is an assumption; what the module can do, and does, is
    refuse an entry that DECLARES itself data-dependent, and never build one
    itself.

    An entry whose pull-back is not supplied is refused with the first reason: the
    conventions block's ``fail_closed`` convention says no default is substituted for a
    missing datum, and a certificate cannot be discharged against a pull-back that was
    not computed.

    ``theorem_discharged`` IS THE ONE EXEMPTION, AND IT IS NOT A TRUST HOLE.
    Corollary ``cor:fssinstance``'s pull-back is
    ``blk M^{<=N}_o (+) (blk M^{>N}_o - p_o 1)``, and THE SUPPLIER EMITS NO
    ABOVE-CUTOFF BLOCK (the outputs table), so that pull-back cannot be materialised
    from any artifact -- ever, not merely here. What discharges it is the
    corollary itself, whose two halves are the positivity of the emitted
    preserved block (decided by the emission pass on the declared data) and
    Eq. ``eq:certweights`` (the supplier's claim, imported under Assumption
    A-RECV, which this module names and can never verify). The mapping is
    populated ONLY by the emission pass, and only for entries THAT PASS ITSELF
    BUILT by that corollary; a caller-supplied ``carried_operators`` entry is
    never in it. Such an entry is decided instead by the builder's call of
    :func:`~certiqs_key.reductions.constraints.certify_carried_operators`, on the
    emitted numbers and before this row runs, by the decided certificate a claim
    stated for the instance gives (``cor:entries`` (iii)) -- so no request can
    reach a discharge it did not earn.
    The locator each label maps to is recorded in the verification report's
    certificate row, so a reader can see which entries were discharged by
    theorem and on which imported hypothesis.

    decided_before_this_row IS THE SECOND AND LAST EXEMPTION, and it is a
    different statement. A caller's carried_operators entry is decided
    BEFORE this row, on the emitted numbers, by certify_carried_operators,
    which admits it only on a decided certificate a claim stated for the
    instance gives (cor:entries (i)-(iii); the row's certificate_rule): a
    default carried operator at >= 0; Remark rem:unsound's expectation
    identity, whose hypothesis is checked on every declared branch; and, on
    the flat instance, Eq. eq:two-sector-entry, whose condition
    (wpfss/cor:two-sector-decided) is decided on the emitted preserved blocks
    and the certified weight. An entry with no such certificate never reaches
    this row: the builder refuses it first (req:uncertified-operator-refused).
    So the labels here are the ones already decided, each mapped to what
    decided it, and A-CONST is still checked for them above -- the exemption is
    from the pull-back clause alone.

    BOTH MAPPINGS ARE POPULATED ONLY BY THE EMISSION PASS, and a caller can
    reach neither. Every label in either one is recorded with its locator in the
    verification report's certificate row.
    """
    for entry in entries:
        if not entry.constant_is_declared:
            return refuse(
                FailClosedRule.CONSTRAINT_CERTIFICATE,
                RefusalReason.DATA_DEPENDENT_CONSTANT,
                f"entry {entry.label!r} declares a constant that is a function "
                "of a statistic observed during the run (A-CONST, "
                "rem:notlicensed (c))",
            )
        pullback = pullbacks.get(entry.label)
        if pullback is None:
            if entry.label in decided_before_this_row:
                # Decided on declared data by an earlier pass, which named what
                # discharged it; A-CONST above still runs on every entry.
                continue
            if entry.label in theorem_discharged:
                # Discharged BY A COROLLARY OF THIS CONTRACT rather than
                # numerically; see the parameter's documentation above. Only the
                # emission pass populates the mapping, and only for entries it
                # built itself at the certified weight.
                continue
            return refuse(
                FailClosedRule.CONSTRAINT_CERTIFICATE,
                RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                f"entry {entry.label!r} has no computed pull-back, so "
                "eq:certificate cannot be discharged for it",
            )
        if not certificate_holds(pullback, entry.relation, entry.constant):
            return refuse(
                FailClosedRule.CONSTRAINT_CERTIFICATE,
                RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                f"eq:certificate fails for entry {entry.label!r}: "
                f"Lambda+(O^) {entry.relation.value} {entry.constant} 1_B does "
                "not hold",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 22: attack_set_license present iff the constraint list is non-empty
# ---------------------------------------------------------------------------


def rule_licence_presence(
    entries: Sequence[ConstraintEntry], licence_present: bool
) -> Refusal | None:
    """Row 22: ``licence_missing`` / ``licence_without_constraints``.

    THE RULE IS AN IFF and both directions are refusals with DIFFERENT reasons.

    A constraint list without a licence leaves unshown exactly what
    spec/architecture.md 5.4 names: "the squashed attack set is not shown
    to contain the physical image".

    A licence with nothing to license is not harmless either: it would attest an
    attack-set restriction the artifact does not carry, and a consumer gating on
    PRESENCE -- which Remark ``rem:gateweight`` says the consuming gate does,
    resting "ENTIRELY on part (ii)" -- would treat the declaration as licensed
    when its constraint list is empty. The ``encoded`` route emits an empty list
    AND NO LICENCE.
    """
    if entries and not licence_present:
        return refuse(
            FailClosedRule.LICENCE_PRESENCE,
            RefusalReason.LICENCE_MISSING,
            f"the constraint list carries {len(entries)} entries and no "
            "attack_set_license is present",
        )
    if not entries and licence_present:
        return refuse(
            FailClosedRule.LICENCE_PRESENCE,
            RefusalReason.LICENCE_WITHOUT_CONSTRAINTS,
            "an attack_set_license is present with an empty constraint list; it "
            "would attest a restriction the artifact does not carry",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 23: the licensed route's Hermiticity, then Row 24: one route value
# ---------------------------------------------------------------------------


def rule_licensed_hermiticity(
    entries: Sequence[ConstraintEntry],
    route: Route | None,
    *,
    lattice_exponent: int | None = None,
) -> Refusal | None:
    """Row 23: the licensed route's exact-Hermiticity and lattice condition.

    The fail-closed table: "ON THE ``licensed`` ROUTE: EVERY EMITTED CONSTRAINT OPERATOR
    IS EXACTLY HERMITIAN -- ``O^_ij = conj(O^_ji)`` ENTRY BY ENTRY -- AND EVERY
    ONE OF ITS ENTRIES SATISFIES Eq. ``eq:latinv``."

    A ROW CARRYING AN EXISTING REASON. It runs on the licensed route
    unconditionally, and the checked condition includes the LATTICE INVARIANT.

    THE REASON: "Definition ``def:licensed`` and Corollary
    ``cor:pullback`` COMPARE A REAL CONSTANT WITH ``tr[O^ sigma]``, WHICH IS
    NOT A REAL NUMBER UNLESS ``O^ = O^-dagger``, and ``fail_closed`` FORBIDS
    SYMMETRIZING ONE."

    IT IS SATISFIABLE AND IT IS NOT A FORMALITY, and the contract says which:
    "the emitted blocks are exactly Hermitian (``thm:emit`` (ii),
    ``def:emitnorm`` (1)), and each ``O^`` is formed from them BY ADDING A REAL
    MULTIPLE OF A SECTOR PROJECTOR OR BY ACCUMULATING OVER ``V``, both of which
    PRESERVE THE CONJUGATE PAIRING EXACTLY; **WHAT THE ROW CATCHES IS A
    CALLER-REQUESTED OPERATOR THAT DOES NOT**. IT IS THE EMITTED-FAMILY ROW'S
    OBLIGATION APPLIED TO THE SECOND FAMILY THIS MODULE EMITS, DECIDED THE SAME
    WAY AND REFUSED THE SAME WAY."

    THE ``encoded`` ROUTE IS UNAFFECTED: "its list is empty and its transported
    operators are the sector projectors of ``cor:entries`` (iii)".

    AN ENTRY TAGGED ``party_local`` IS DECIDED ON THAT FACTOR'S BLOCKS, and
    this row needs nothing added to do it: the entry IS its block list against
    that factor's sector map, "the operator being an operator on that factor's
    ``Q_f`` and nothing wider; there is no product operator to decide anything
    on" (the ``licensed_hermiticity`` row). Both
    halves -- exact Hermiticity and Eq. ``eq:latinv`` -- are per block either
    way, and the blocks of a tagged entry are a factor's own, which is also why
    the lattice half is decided at THAT FACTOR'S declared ``kappa``.

    Args:
        entries: the emitted constraint list, or the joint list of a factor
            emission.
        route: the resolved route; the row is scoped to ``licensed``.
        lattice_exponent: the declared ``kappa``. ``None`` where row 1 refused,
            in which case the lattice half is not decided -- there is no
            lattice to decide it against -- and the Hermiticity half still is.
    """
    if route is not Route.LICENSED:
        return None
    for entry in entries:
        # PER SECTOR BLOCK, because the entry IS its block list: a
        # block-diagonal operator is Hermitian exactly when every block is, and
        # every entry of it lies in one of them (spec/architecture.md 2.8-2.9).
        if not all(is_hermitian(block) for block in entry.operator):
            return refuse(
                FailClosedRule.LICENSED_HERMITICITY,
                RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                f"the emitted constraint operator {entry.label!r} is not "
                "EXACTLY Hermitian; def:licensed and cor:pullback compare a "
                "real constant with tr[O^ sigma], WHICH IS NOT A REAL NUMBER "
                "unless O^ = O^-dagger, and the conventions block's fail_closed "
                "convention forbids symmetrizing a supplied block. Every "
                "operator this module builds is exactly Hermitian by "
                "construction, so what this row catches is a caller-requested "
                "one that is not",
            )
        if lattice_exponent is not None and not all(
            on_lattice(block, lattice_exponent) for block in entry.operator
        ):
            return refuse(
                FailClosedRule.LICENSED_HERMITICITY,
                RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                f"the emitted constraint operator {entry.label!r} carries an "
                f"entry off the declared 2^-{lattice_exponent} lattice "
                "(Eq. eq:latinv); it is the emitted-family row's obligation "
                "applied to THE SECOND FAMILY THIS MODULE EMITS, decided the "
                "same way and refused the same way",
            )
    return None


def rule_route(value: str) -> Refusal | None:
    """Row 24: ``route_not_single_valued``.

    "The emitted payload is single-valued throughout, and the two routes run on
    DIFFERENT CHANNELS, so one artifact carrying both would admit a cross-channel
    pairing that is UNSOUND" (Remark ``rem:tworoutes``). Eq. ``eq:crosspairing``
    is the witness: pairing the licensed entry with the encoded route's channel
    gives ``Lambda^WP+(F^FSS_o - p_o Pi_flag)``, whose flag block "is NOT implied
    positive by Eq. ``eq:certweights`` -- at the tight end
    ``blk M^{>N}_o = p_o 1`` it equals ``-p_o 1``, strictly negative for
    ``p_o > 0``".

    "A caller wanting both issues TWO REQUESTS and receives two self-contained
    artifacts" -- with no schema in which the unsound pairing can be expressed.
    """
    if value not in {route.value for route in Route}:
        return refuse(
            FailClosedRule.ROUTE,
            RefusalReason.ROUTE_NOT_SINGLE_VALUED,
            f"route = {value!r} is not exactly one of "
            f"{tuple(route.value for route in Route)!r}; `both` is refused "
            "because the two routes run on different channels "
            "(rem:tworoutes, eq:crosspairing)",
        )
    return None


def resolve_route(value: str) -> Route | None:
    """Return the declared route, or ``None`` when :func:`rule_route` refuses it."""
    for route in Route:
        if route.value == value:
            return route
    return None


# ---------------------------------------------------------------------------
#  Row 25: every entry is certified against ITS OWN LINK's channel witness
# ---------------------------------------------------------------------------


def rule_constraint_channel(
    entries: Sequence[ConstraintEntry],
    witness_identity: str,
    *,
    factor_witnesses: Mapping[str, str] | None = None,
) -> Refusal | None:
    """Row 25: ``constraint_channel_mismatch``, widened to the factor scope.

    "Definition ``def:link`` binds the two per link; Remark
    ``rem:channel-choice`` (c)." That remark is the reason the binding is a
    refusal and not a convention: "constraints sound for ``Lambda`` and
    constraints sound for ``Lambda'`` may have an intersection excluding every
    state reachable under either, and imposing them together would void Theorem
    ``thm:transfer`` exactly as an unsound constraint does".

    Remark ``rem:tworoutes`` freezes what goes wrong with numbers: the
    ``cor:fssinstance`` entry pulls back to ``0`` under its own ``Lambda^FSS``
    and to a strictly negative operator under ``Lambda^WP``, excluding a state
    that IS reachable under the latter.

    NO NEW ROW AND NO NEW REASON STRING FOR TAGGED ENTRIES: "AN ENTRY
    TAGGED ``party_local`` NAMES A FACTOR OF THE DECLARED ORDERED FACTOR LIST,
    carries an operator on that factor's ``Q_f`` against that factor's sector
    map, and is certified against THAT FACTOR'S OWN CHANNEL WITNESS
    ``Lambda_f`` -- never against another factor's and never against a joint
    channel." THE DISTINCTION IS NOT A FORMALITY: the operator reading holds
    because the squashing channel is a PRODUCT with that factor's certificate
    on that factor's own channel, and ``lem:party-local`` (iv) exhibits a
    channel that satisfies the scalar bound of the same entry and VIOLATES the
    operator one, so a tag emitted on a certificate against anything else would
    assert an operator inequality nothing proves -- the security-break
    direction of ``rem:unsound``.

    A ONE-FACTOR EMISSION HAS NO FACTOR LIST AND NO TAG TO CHECK
    (``factor_witnesses`` is ``None`` there), "and a party-local entry
    requested there is the UNTAGGED entry rather than a refusal; this row
    reaches it as the untagged entry it is, against the one channel witness
    there is".

    Args:
        entries: the emitted constraint list, or the joint list of a factor
            emission.
        witness_identity: the channel witness of the link the untagged entries
            belong to.
        factor_witnesses: per factor label, that factor's own channel witness,
            where the call declares a factor list. ``None`` for a one-factor
            emission, where a tagged entry cannot arise.
    """
    for entry in entries:
        if entry.tag is None:
            if entry.certified_against != witness_identity:
                return refuse(
                    FailClosedRule.CONSTRAINT_CHANNEL,
                    RefusalReason.CONSTRAINT_CHANNEL_MISMATCH,
                    f"entry {entry.label!r} was certified against "
                    f"{entry.certified_against!r}, not against its own link's "
                    f"channel witness {witness_identity!r}",
                )
            continue
        declared = factor_witnesses or {}
        scope = entry.scope
        # The tag and the scope travel together or the ENTRY is malformed and
        # cannot be constructed at all (ConstraintEntry.__post_init__), so a
        # tagged entry whose scope is absent is not a case this row decides.
        if scope is None or scope not in declared:
            return refuse(
                FailClosedRule.CONSTRAINT_CHANNEL,
                RefusalReason.CONSTRAINT_CHANNEL_MISMATCH,
                f"entry {entry.label!r} is tagged {str(entry.tag)!r} and scoped "
                f"to {entry.scope!r}, which is not a factor of the declared "
                f"ordered factor list {sorted(declared)!r}; a tag names a "
                "reading on ONE declared factor's Q_f (cor:entries, the tag "
                "paragraphs) and this module emits it in one place, the "
                "emission of several measuring parties",
            )
        if entry.certified_against != declared[scope]:
            return refuse(
                FailClosedRule.CONSTRAINT_CHANNEL,
                RefusalReason.CONSTRAINT_CHANNEL_MISMATCH,
                f"entry {entry.label!r} is scoped to factor {entry.scope!r} and "
                f"was certified against {entry.certified_against!r}, not "
                f"against that factor's own channel witness "
                f"{declared[scope]!r}; thm:licence (v) licenses the "
                "party-local reading ON THAT FACTOR'S CHANNEL and on nothing "
                "else, and lem:party-local (iv) exhibits a channel satisfying "
                "the scalar bound while violating the operator one",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 26: alphabets, sector order and basis order agree across artifacts
# ---------------------------------------------------------------------------


def rule_alphabet_order(
    artifact: ReceiverArtifactRows,
    detection_alphabet: Sequence[Label],
    probe: ProbeDeclaration,
    joint_alphabet: Sequence[JointOutcome],
    declared_sector_order: Sequence[str] | None = None,
    constructed_sector_order: Sequence[str] | None = None,
    declared_occupation_basis_order: Sequence[tuple[str, ...]] | None = None,
) -> Refusal | None:
    """Row 26: ``alphabet_or_order_mismatch``.

    spec/architecture.md 5.4. The conventions block ``subsystem_order`` makes the
    flag basis "IN THE DECLARED ORDER OF ``V = Y x T``" and the outputs table's
    ``wpfss_data`` emits "the flag basis IN THE DECLARED ORDER OF ``V``", so a
    permuted ``Y`` permutes the flag basis and with it every emitted ``F_v`` and
    every sector label -- SILENTLY, "because the permuted objects are still POVMs
    summing to the identity. The refusal exists because NO LATER CHECK WOULD
    CATCH IT."

    THE ORDER IS y-FASTEST. The convention's "y VARIES FASTEST AND t
    SLOWEST... EQUIVALENTLY, V IS ENUMERATED AS T-BLOCKS OF Y-RUNS" fixes the
    grouping, so rule (3) below validates the ORDER as well as the declared
    product SET. NOTHING IS CONSTRUCTED: the order
    remains a declared datum, "VALIDATED against the product set ``Y x T`` and
    against this grouping, and NEVER CONSTRUCTED IN PLACE OF A MISSING
    DECLARATION".

    FIVE AGREEMENTS ARE CHECKED, and the last is the one the conventions block says is
    inherited rather than chosen: (1) the receiver artifact's declared ``Y`` and
    the declaration's, ORDER INCLUDED; (2) THE ECHOED ``T`` of
    ``bound_quantifier_domain`` against the declaration's probe alphabet, ORDER
    INCLUDED; (3) the declared ``V`` against the product ``Y x T``, as a set,
    without repetition, AND IN THE GROUPING SECTION 2.5 FIXES -- ``y``
    fastest, ``t`` slowest; (4) a declared
    sector order against the constructed one, where the request declares one;
    (5) the occupation-vector basis order, "INHERITED UNCHANGED" from the
    receiver artifact.

    WHY ``T`` BELONGS HERE. The inputs table's ``bound_quantifier_domain`` row types
    the datum as "the literal statement 'for all m > N and all t in T'" and
    names only ``N`` as the thing whose mismatch is refused -- that is the
    ``cutoff_mismatch`` row. But ``T`` is an ALPHABET, and this row is the one
    that makes alphabets agree across artifacts. The hazard it closes is narrow
    and real: a weight would be applied at a setting the supplier's quantifier
    does not name, wherever the blocks happen to exist for it. A conforming
    receiver artifact keeps the two equal, so the check costs nothing and
    refuses only a declaration that is already inconsistent with itself.
    """
    if tuple(artifact.detection_alphabet) != tuple(detection_alphabet):
        return refuse(
            FailClosedRule.ALPHABET_ORDER,
            RefusalReason.ALPHABET_OR_ORDER_MISMATCH,
            "the receiver artifact declares Y as "
            f"{tuple(artifact.detection_alphabet)!r} and the declaration as "
            f"{tuple(detection_alphabet)!r}; the ORDER is part of the agreement",
        )
    if tuple(artifact.bound_quantifier_domain.settings) != tuple(probe.settings):
        return refuse(
            FailClosedRule.ALPHABET_ORDER,
            RefusalReason.ALPHABET_OR_ORDER_MISMATCH,
            "the receiver artifact's quantifier domain echoes T as "
            f"{tuple(artifact.bound_quantifier_domain.settings)!r} and the "
            f"declaration declares {tuple(probe.settings)!r}; the weights are "
            "certified 'for all t in T' and the two T's must be the same one",
        )
    product = [
        (letter, setting) for setting in probe.settings for letter in detection_alphabet
    ]
    if sorted(joint_alphabet) != sorted(product):
        return refuse(
            FailClosedRule.ALPHABET_ORDER,
            RefusalReason.ALPHABET_OR_ORDER_MISMATCH,
            "the declared joint alphabet is not exactly the product Y x T",
        )
    if tuple(joint_alphabet) != tuple(product):
        # y-FASTEST. The conventions block `subsystem_order` fixes the GROUPING and
        # not only the membership: "THE FLAG BASIS IS IN THE DECLARED ORDER OF V = Y x
        # T, WHICH IS THE ORDER IN WHICH y VARIES FASTEST AND t SLOWEST ...
        # EQUIVALENTLY, V IS ENUMERATED AS T-BLOCKS OF Y-RUNS. The
        # order is a DECLARED datum and is never constructed in place of a missing
        # declaration -- a declaration in the OTHER grouping is refused, not used.
        return refuse(
            FailClosedRule.ALPHABET_ORDER,
            RefusalReason.ALPHABET_OR_ORDER_MISMATCH,
            "the declared joint alphabet IS the product Y x T but not in the "
            "order the subsystem_order convention fixes: y varies FASTEST "
            "and t SLOWEST, so V is enumerated as T-blocks of Y-runs. Declared "
            f"{tuple(joint_alphabet)!r}; the contract's grouping is "
            f"{tuple(product)!r}. No later check would catch the difference -- "
            "the two have the same multiset of weights and the same total p -- "
            "so an emitted weight would sit in the wrong slot of wpfss_data",
        )
    if len(set(joint_alphabet)) != len(joint_alphabet):
        return refuse(
            FailClosedRule.ALPHABET_ORDER,
            RefusalReason.ALPHABET_OR_ORDER_MISMATCH,
            "the declared joint alphabet repeats an outcome",
        )
    if (
        declared_sector_order is not None
        and constructed_sector_order is not None
        and tuple(declared_sector_order) != tuple(constructed_sector_order)
    ):
        return refuse(
            FailClosedRule.ALPHABET_ORDER,
            RefusalReason.ALPHABET_OR_ORDER_MISMATCH,
            "the declared sector order disagrees with the one the "
            "instance's sector set (def:reduction-instance (I2)) and the "
            "conventions block subsystem_order give",
        )
    if declared_occupation_basis_order is not None and tuple(
        declared_occupation_basis_order
    ) != tuple(artifact.occupation_basis_order):
        return refuse(
            FailClosedRule.ALPHABET_ORDER,
            RefusalReason.ALPHABET_OR_ORDER_MISMATCH,
            "the occupation-vector basis order is inherited UNCHANGED from "
            "the receiver artifact and the request declares a different one",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 27: squash requested AFTER classical post-processing, not before
# ---------------------------------------------------------------------------


def rule_post_processing_order(squash_first: bool) -> Refusal | None:
    """Row 27: ``post_processing_order_violated`` (Remark ``rem:intertwining``).

    Lemma ``lem:linear`` (i) applies a post-processing to BOTH SIDES AT ONCE, which is
    why the receiver-consumption block puts the classical steps first. It does NOT say a
    classical map applied before a FIXED squasher may be moved across it: that asks
    whether ``P' M = P M`` has a stochastic solution ``P'``, "A LINEAR FEASIBILITY
    PROBLEM IN ``P'`` THAT HAS NO SOLUTION IN GENERAL, and none whenever the map ``P' ->
    P' M`` fails to have ``P M`` in the image of the stochastic matrices". THIS
    MODULE NEVER ASKS IT.
    """
    if squash_first:
        return refuse(
            FailClosedRule.POST_PROCESSING_ORDER,
            RefusalReason.POST_PROCESSING_ORDER_VIOLATED,
            "the request asks to squash before the classical post-processing "
            "of the outcome; the order is fixed and the request is refused "
            "(rem:intertwining)",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 28: an operator-form transplant of a physical identity is requested
# ---------------------------------------------------------------------------


def rule_unsound_transplant(
    requests: Sequence[CarriedOperatorRequest],
) -> Refusal | None:
    """Row 28: ``unsound_constraint_requested`` (Remark ``rem:unsound``).

    "Equation ``eq:inclusion`` is the whole of soundness, and the standard way to
    violate it is to transplant an operator identity that holds in the PHYSICAL
    model." The physical POVM satisfies ``sum_y M_(y,t) = q_t 1_B``; the squashed
    operators generally satisfy only the PULL-BACK identity, "while
    ``sum_y F_(y,t) != q_t 1_Q`` ON THE FLAG SECTOR of a flag-shaped target".
    Imposing the operator form "would exclude reachable states and void Theorem
    ``thm:transfer``, which is A SECURITY BREAK RATHER THAN A RATE LOSS".

    The EXPECTATION form of the same fact is sound and remains available on
    request, on the licensed route and under the licence that route requires; it
    is :func:`~certiqs_key.reductions.constraints.probe_expectation_entry`.
    """
    for request in requests:
        if request.form is ConstraintForm.OPERATOR:
            return refuse(
                FailClosedRule.UNSOUND_TRANSPLANT,
                RefusalReason.UNSOUND_CONSTRAINT_REQUESTED,
                f"carried operator {request.label!r} is requested in the "
                "OPERATOR form; the sound form of a transplanted physical "
                "identity is the expectation form (rem:unsound)",
            )
    return None
