"""The six fail-closed rows of the weight route, and the reasons they carry.

WHY THEY ARE HERE AND NOT IN THE CORE. Each is a statement about ONE squasher's
device model -- a threshold detector whose dark counts are a column-stochastic
matrix on raw click patterns, a supplier's strengthening slot, the routed total
weight of Proposition ``prop:route``. A protocol with an already-finite POVM
has none of them, and the core's ``thm:emit`` quantifies over an instance that
need not have a weight route at all.

THE ROWS SIT BETWEEN CORE ROWS IN THE INTERFACE'S TABLE, and that is what
:attr:`~certiqs_key.reductions.reasons.FailClosedRow.order` carries: the fibre,
column-stochasticity, descent, absorbing and total-weight rows are positions 8
to 12, after the emitted-family row, and the strengthening-slot row is
position 14 (13 is a branching submodule's row, where one is in the tree).
The core never names them; the builder declares them per call and
:func:`certiqs_key.reductions.emit.reduce` merges and sorts.

WHAT THESE RULES MAY NOT DO. "NO DEFAULT IS SUBSTITUTED FOR A MISSING DATUM, NO
WEIGHT IS CLIPPED INTO RANGE, NO FIBRE CONDITION IS WAIVED, AND NO LICENCE IS
EMITTED WITHOUT ITS CERTIFICATE." Nothing below repairs, normalizes, rounds or
defaults; every rule reads declared data and returns a verdict.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Final

from certiqs_key.reductions.inputs import (
    CoarseGraining,
    DarkCountChannel,
    HighPhotonBound,
    Label,
)
from certiqs_key.reductions.reasons import (
    FailClosedRow,
    Refusal,
    RefusalReason,
    register_row,
)
from certiqs_key.reductions.validation import refuse
from certiqs_key.reductions.wpfss.weights import (
    BoundedLetter,
    declared_column_sums,
    descend,
    is_monotone,
    smallest_declared_entry,
)

__all__ = [
    "NORMALIZED_BRANCH",
    "NORMALIZED_BRANCH_ROWS",
    "WPFSS_ROWS",
    "FailClosedRule",
    "receiver_version_states_the_per_setting_weights",
    "rule_absorbing",
    "rule_column_stochastic",
    "rule_descent",
    "rule_fibre",
    "rule_high_photon_slot",
    "rule_normalized_branch",
    "rule_total_weight",
]


class FailClosedRule:
    """The six row identifiers ``wpfss`` owns, spelled once.

    A SUBMODULE'S ROWS ARE ITS OWN. The core's
    :class:`certiqs_key.reductions.reasons.FailClosedRule` enum cannot be
    extended, and these six rows are about ONE squasher's device model, so the
    core does not name them; what it holds is the registry they register into
    and the REASONS they carry, which are its own strings -- only a
    removable submodule owns a reason string, because it has to be removable.
    """

    FIBRE: Final[str] = "fibre"
    COLUMN_STOCHASTIC: Final[str] = "column_stochastic"
    DESCENT: Final[str] = "descent"
    ABSORBING: Final[str] = "absorbing"
    TOTAL_WEIGHT: Final[str] = "total_weight"
    HIGH_PHOTON_SLOT: Final[str] = "high_photon_slot"


#: The six rows with the place each holds in the interface's table of
#: twenty-eight. Registered at import so that a machine record can name the
#: reasons a row of this submodule can produce; WHICH rows a reduction reports
#: is assembled per call from the builder's declaration.
WPFSS_ROWS: Final[tuple[FailClosedRow, ...]] = (
    FailClosedRow(FailClosedRule.FIBRE, 8, (RefusalReason.BOUND_SET_NOT_A_FIBRE,)),
    FailClosedRow(
        FailClosedRule.COLUMN_STOCHASTIC,
        9,
        (RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC,),
    ),
    FailClosedRow(
        FailClosedRule.DESCENT, 10, (RefusalReason.DARK_COUNTS_DO_NOT_DESCEND,)
    ),
    FailClosedRow(
        FailClosedRule.ABSORBING, 11, (RefusalReason.BOUNDED_LETTER_NOT_ABSORBING,)
    ),
    FailClosedRow(
        FailClosedRule.TOTAL_WEIGHT, 12, (RefusalReason.TOTAL_WEIGHT_NOT_BELOW_ONE,)
    ),
    FailClosedRow(
        FailClosedRule.HIGH_PHOTON_SLOT,
        14,
        (RefusalReason.HIGH_PHOTON_SLOT_ILL_FORMED,),
    ),
)

for _row in WPFSS_ROWS:
    register_row(_row)

#: THE ROW OF ``req:normalized-branch-refusal``, added after the freeze at the
#: next free place of the table, 29. It is NOT one of the flat path's rows: the
#: flat instance absorbs a factored loss (``cor:normalized-flat``) and has
#: nothing to refuse. A builder that embeds the flat instance as a BRANCH of a
#: branching instance declares and decides it.
NORMALIZED_BRANCH: Final[str] = "normalized_branch"
NORMALIZED_BRANCH_ROWS: Final[tuple[FailClosedRow, ...]] = (
    FailClosedRow(
        NORMALIZED_BRANCH, 29, (RefusalReason.NORMALIZED_RECEIVER_IN_BRANCH,)
    ),
)

for _row in NORMALIZED_BRANCH_ROWS:
    register_row(_row)


# ---------------------------------------------------------------------------
#  Row 29: a normalized receiver is not read as a branch
# ---------------------------------------------------------------------------


def rule_normalized_branch(factored_loss: Fraction) -> Refusal | None:
    """Row 29: ``normalized_receiver_in_branch`` -- ``req:normalized-branch-refusal``.

    An artefact that embeds the flat instance as a branch of a branching
    instance (``reductions/thm:instrument-instance``), the register instance
    included, reads only a receiver artefact whose ``efficiency_record``
    carries the factored loss ``t = 1``. ``cor:normalized-flat`` absorbs the
    loss for the flat instance on the channel system; a branching instance
    places it beside branches that need not be the pull-back of anything
    through a loss on the channel modes, so no claim moves the loss in front,
    and a normalized receiver is refused rather than read as the device. A
    run whose receiver is to be such a branch declares
    ``efficiency_normalization = 1`` to the receiver.
    """
    if factored_loss == 1:
        return None
    return refuse(
        NORMALIZED_BRANCH,
        RefusalReason.NORMALIZED_RECEIVER_IN_BRANCH,
        f"the receiver artefact was compiled at its normalized station, factored "
        f"loss t = {factored_loss} < 1, and this artefact embeds the flat "
        "instance as a branch of a branching instance; only t = 1 is read there "
        "(wpfss/req:normalized-branch-refusal). Declare efficiency_normalization "
        "= 1 to the receiver",
    )


# ---------------------------------------------------------------------------
#  Row 8: each bounded set is EXACTLY a fibre, for distinct letters
# ---------------------------------------------------------------------------


def rule_fibre(
    bounds: Sequence[HighPhotonBound], coarse_graining: CoarseGraining
) -> Refusal | None:
    """Row 8: ``bound_set_not_a_fibre`` (Remark ``rem:fibre``).

    ``O_i = cg^{-1}(y_i)`` for pairwise DISTINCT letters. Two failures, in
    opposite directions, and both carry this reason.

    A SPLIT fibre: "if ``cg`` SPLITS ``O`` across two emitted letters, NEITHER
    LETTER INHERITS A BOUND, and the natural repair -- bound each piece -- is
    UNAVAILABLE because the supplier certified ONLY THE SUM", and "a bound on a
    sum of positive operators says nothing about the individual summands".

    A MERGED fibre: the bound "STILL HOLDS for the merged letter (adding positive
    operators only helps), but ... the emitted weight is attached to a letter
    WHOSE FIBRE IS LARGER THAN THE CERTIFIED SET -- sound, and recorded as such,
    BUT ONLY IF THE CONTAINMENT IS VALIDATED RATHER THAN ASSUMED. This module
    therefore requires EQUALITY."
    """
    seen: set[Label] = set()
    for index, bound in enumerate(bounds):
        matches = [
            letter
            for letter in coarse_graining.letters
            if coarse_graining.fibre(letter) == bound.outcome_set
        ]
        if not matches:
            return refuse(
                FailClosedRule.FIBRE,
                RefusalReason.BOUND_SET_NOT_A_FIBRE,
                f"bounded set {index} is not exactly cg^{{-1}}(y) for any "
                "declared letter",
            )
        letter = matches[0]
        if letter in seen:
            return refuse(
                FailClosedRule.FIBRE,
                RefusalReason.BOUND_SET_NOT_A_FIBRE,
                f"two bounded sets are the fibre of the same letter {letter!r}; "
                "the inputs table requires pairwise distinct letters",
            )
        seen.add(letter)
    return None


# ---------------------------------------------------------------------------
#  Row 9: the column-stochasticity of the DECLARED R, exactly
# ---------------------------------------------------------------------------


def rule_column_stochastic(channel: DarkCountChannel) -> Refusal | None:
    """Row 9: ``dark_counts_not_column_stochastic`` (Remark ``rem:colstoch``).

    Section ``sec:failclosed``: "the
    declared dark-count matrix ``R`` is EXACTLY column-stochastic:
    ``R_{S|S'} >= 0`` for every entry, and ``sum_{S subset [K]} R_{S|S'} = 1``
    for every column ``S'``". The row is a CONJUNCTION and one half failing is
    enough; both halves are checked here so that the refusal names which.

    THE SUBJECT IS THE DECLARED ``R``, AND ONE ROW SUFFICES. "DECIDED ON ``R``,
    WHICH SUFFICES: Lemma ``lem:descent`` carries BOTH HALVES to ``R^cg``, so NO
    SECOND ROW IS STATED ON THE DESCENDED MATRIX." Remark ``rem:colstoch``
    proves it: the fibres of ``cg`` partition ``2^[K]``, so
    ``R^cg_{y|y'} = sum_{S in cg^{-1}(y)} R_{S|S'} >= 0`` as a sum of
    non-negative entries and ``sum_y R^cg_{y|y'} = sum_S R_{S|S'} = 1``. There
    is deliberately NO second rule on ``R^cg``:
    :meth:`~certiqs_key.reductions.wpfss.weights.DescendedChannel.is_column_stochastic`
    exists to make that implication checkable and is not consulted here.

    EXACTLY, AND THERE IS NOTHING IT COULD BE DECIDED WITHIN. The fail-closed table:
    every rule is decided exactly, "AN IDENTITY BY COMPARISON OF ENTRIES", and
    Lemma ``lem:exactpsd`` is NOT INVOKED here. Nothing in this function reads a
    tolerance -- this module carries none at 1.0.0 -- and ``kappa`` is not one
    either: the ``lattice_exponent`` row says "IT IS NOT A TOLERANCE, NOTHING IS
    ADMITTED OR REFUSED WITHIN ``kappa``". The row compares declared rationals
    against ``0`` and ``1``. The contract's own example is a matrix "whose
    columns sum to 1 only to within a rounding error", and it is refused
    (Rem. ``rem:exactboundary``).

    IT IS NOT THE DESCENT ROW AND NEITHER COVERS THE OTHER (Remark
    ``rem:darkcompose``): a NEGATIVE entry in a monotonicity-forbidden position
    satisfies that row's implication VACUOUSLY and is refused HERE, while a
    STRICTLY POSITIVE entry in the same position leaves column-stochasticity
    untouched and is refused THERE. Folding the two into one test would emit the
    wrong reason string in both directions.

    WHAT HAVING THE ROW CHANGES, IN THE CONTRACT'S OWN WORDS: "what is closed
    here is COVERAGE AND ATTRIBUTION, NOT SOUNDNESS". Every result of the
    contract was proved for an exactly column-stochastic ``R`` and asserts
    nothing about a declaration that is not one; the class this row catches is
    the residue that would meet no other row, and it is REFUSED. The one place the row
    is load-bearing beyond diagnosis is that with it "EVERY ADMITTED ``R`` IS EXACTLY
    ADMISSIBLE IN THE SUPPLIER'S SENSE" -- (D1) of ``receiver-povm`` 0.2.0's Def.
    ``def:darkadm`` by this row and (D2) by the descent row.
    """
    smallest = smallest_declared_entry(channel)
    if smallest < 0:
        return refuse(
            FailClosedRule.COLUMN_STOCHASTIC,
            RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC,
            f"the declared dark-count matrix has a negative entry ({smallest}); "
            "sec:failclosed requires R_{S|S'} >= 0 for EVERY entry, exactly, "
            "and this row is decided by a sign comparison on the declared "
            "entries (rem:exactboundary)",
        )
    for column, total in declared_column_sums(channel).items():
        if total != 1:
            return refuse(
                FailClosedRule.COLUMN_STOCHASTIC,
                RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC,
                "the declared dark-count matrix has a column that does not sum "
                f"to one: column {sorted(column)} sums to {total}; "
                "sec:failclosed requires sum_S R_{S|S'} = 1 for EVERY column, "
                "EXACTLY -- a column summing to one only to within a rounding "
                "error is refused here (rem:exactboundary, rem:colstoch)",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 10: R is monotone and DESCENDS through cg, tested directly
# ---------------------------------------------------------------------------


def rule_descent(
    channel: DarkCountChannel, coarse_graining: CoarseGraining
) -> Refusal | None:
    """Row 10: ``dark_counts_do_not_descend`` (Lemma ``lem:descent``).

    "TESTED DIRECTLY, NOT VIA THE SHORTCUT Eq. ``eq:canonicalcg``". Remark
    ``rem:descentneedsconstant`` exhibits a monotone ``R`` and a ``cg`` meeting
    two of that equation's three clauses for which ``R^cg`` is NOT well defined,
    so "an implementation testing the shortcut instead of the property would
    ACCEPT a declaration it must refuse". Nothing here looks at the shape of
    ``cg``.

    Monotonicity is checked in the same row because the inputs table declares the two
    together and the row's own text reads "``R`` is monotone AND descends".
    """
    if not is_monotone(channel):
        return refuse(
            FailClosedRule.DESCENT,
            RefusalReason.DARK_COUNTS_DO_NOT_DESCEND,
            "the declared dark-count channel is not monotone: some R_{S|S'} > 0 "
            "with S' not a subset of S",
        )
    if descend(channel, coarse_graining) is None:
        return refuse(
            FailClosedRule.DESCENT,
            RefusalReason.DARK_COUNTS_DO_NOT_DESCEND,
            "two columns with the same cg-image carry different values of "
            "P(y | S'), so R^cg is not well defined (lem:descent, "
            "rem:descentneedsconstant)",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 11: every bounded letter is absorbing, and r_min reads every other column
# ---------------------------------------------------------------------------


def rule_absorbing(letters: Sequence[BoundedLetter]) -> Refusal | None:
    """Row 11: ``bounded_letter_not_absorbing`` (Eq. ``eq:absorbing``).

    "``R^cg_{y_i|y_i} = 1``, and each ``r_min,i`` is computed over EVERY column
    ``y' != y_i``." Without it Eq. ``eq:routebound`` is "NOT MERELY UNPROVED BUT
    FALSE, IN THE DIRECTION THAT CERTIFIES A WEIGHT THE DEVICE DOES NOT HAVE"
    (Remark ``rem:absorbneeded``) -- the failure Assumption A-RECV's ledger row
    calls a security break.

    THE REFUSAL COVERS THE WHOLE ARTIFACT and that is deliberate: Proposition
    ``prop:route``'s proof "uses ``eq:absorbing`` ONLY AT ``y_i``, so ONE
    non-absorbing letter could in principle have been handled by dropping that
    entry's weight to zero and keeping the rest. This module REFUSES THE WHOLE
    ARTIFACT instead -- fail-closed, and A RATE LOSS RATHER THAN A SOUNDNESS
    QUESTION -- because a partially honoured slot would emit a target whose
    weights no longer correspond ENTRY-FOR-ENTRY to the declared slot, and NO
    DECLARED FIELD RECORDS WHICH ENTRY WAS SILENTLY ZEROED."
    """
    for letter in letters:
        if not letter.absorbing:
            return refuse(
                FailClosedRule.ABSORBING,
                RefusalReason.BOUNDED_LETTER_NOT_ABSORBING,
                f"the bounded letter {letter.letter!r} has R^cg_{{y|y}} != 1, so "
                "eq:routebound is false in the unsafe direction "
                "(rem:absorbneeded); the whole artifact is refused",
            )
    return None


# ---------------------------------------------------------------------------
#  Row 12: p_v >= 0 and p = sum_v p_v < 1
# ---------------------------------------------------------------------------


def rule_total_weight(weights: Sequence[Fraction]) -> Refusal | None:
    """Row 12: ``total_weight_not_below_one``.

    "The construction Eq. ``eq:Lwp`` divides by ``1 - p`` on the ``encoded``
    route. On the ``licensed`` route the witness is ``Lambda^FSS``, which
    performs no such division, SO THERE THE TEST IS STRICTER THAN THE MATHEMATICS
    REQUIRES; this module applies it ON BOTH ROUTES DELIBERATELY -- one validity
    rule rather than two, fail-closed and conservative, and by Remark
    ``rem:peqone`` the excluded boundary is recoverable by lowering one weight
    infinitesimally."

    IT ALSO RUNS UNCONDITIONALLY: "``p_v < 0`` is impossible, and so is ``p > 1``
    WHEN ``H(B_{>N}) != {0}`` (Lemma ``lem:ple1``); where that block is trivial
    the certified-weight condition is vacuous and this test is THE ONLY THING
    CONSTRAINING ``p``, WHICH IS WHY IT RUNS UNCONDITIONALLY."

    A DECLARATION WITH ``p >= 1`` IS REFUSED, NOT CLIPPED (the parameters table).
    """
    for index, weight in enumerate(weights):
        if weight < 0:
            return refuse(
                FailClosedRule.TOTAL_WEIGHT,
                RefusalReason.TOTAL_WEIGHT_NOT_BELOW_ONE,
                f"the weight at index {index} is {weight} < 0; Lemma lem:ple1 "
                "makes that impossible for a certified family, so the "
                "declaration is not one",
            )
    total = sum(weights, start=Fraction(0))
    if total >= 1:
        return refuse(
            FailClosedRule.TOTAL_WEIGHT,
            RefusalReason.TOTAL_WEIGHT_NOT_BELOW_ONE,
            f"p = sum_v p_v = {total} >= 1; eq:Lwp divides by 1 - p and the "
            "declaration is refused, not clipped (rem:peqone: the refusal is "
            "conservative and the boundary is recoverable by lowering one "
            "weight infinitesimally)",
        )
    return None


# ---------------------------------------------------------------------------
#  Row 14: the supplier's strengthening slot, per setting
# ---------------------------------------------------------------------------


def receiver_version_states_the_per_setting_weights(version: str) -> bool:
    """Whether the receiver version ``version`` STATES the per-setting weights.

    ``req:supplier-version`` and the interface key
    ``requires_a_receiver_version_stating_them``: the per-setting read needs "a
    version which states them: one whose Thm. ``thm:emitted-bound`` carries
    Eq. ``eq:pmcsetting`` and whose Def. ``def:slot`` carries a weight per entry
    and setting. At an earlier version the per-setting values an artifact
    reported beside the minimum were the content of no claim ... so they are not
    read from an artifact of such a version."

    WHICH VERSION THAT IS IS THE SUPPLIER'S FACT AND IS READ FROM IT, not kept
    here: ``FIRST_VERSION_STATING_THE_PER_SETTING_WEIGHTS`` of
    :mod:`certiqs_key.receiver.artifact`, the first ``receiver`` version whose
    contract states them. The import is
    FUNCTION-LOCAL and points downward (``reductions`` depends on
    ``receiver``), for the reason
    :func:`certiqs_key.reductions.validation.required_receiver_keys` gives:
    this package loads no array library at import.

    FAIL-CLOSED ON THE STRING: anything but ``receiver@<major>.<minor>.<patch>``
    with integer parts -- a draft suffix, another module's id -- does not state
    them. (The receiver-spec row refuses such a version anyway; this row does
    not rely on that.)
    """
    from certiqs_key.receiver.artifact import (
        FIRST_VERSION_STATING_THE_PER_SETTING_WEIGHTS,
    )

    module, separator, number = version.partition("@")
    if module != "receiver" or not separator:
        return False
    parts = number.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return False
    major, minor, patch = (int(part) for part in parts)
    return (major, minor, patch) >= FIRST_VERSION_STATING_THE_PER_SETTING_WEIGHTS


def rule_high_photon_slot(
    bounds: Sequence[HighPhotonBound],
    settings: Sequence[Label],
    receiver_version: str,
) -> Refusal | None:
    """Row 14: ``high_photon_slot_ill_formed`` -- the slot, well formed PER SETTING.

    The row: "its per-setting weights are indexed by exactly the settings T of the
    supplied blocks, ``p_i^(t) >= 0`` for every ``i`` and ``t``, and
    ``sum_i p_i^(t) <= 1`` at every ``t``" (the ``wpfss`` interface's
    ``high_photon_slot`` row). ``settings`` is that ``T``, read by the caller off
    the supplied blocks. FOUR CLAUSES, 0 to 3, one reason string, decided in this
    order:

    0. THE SLOT IS READ ONLY FROM A RECEIVER VERSION THAT STATES IT PER
       SETTING. ``rem:receiver-imports``: the supplier's claims are read at
       the version the artifact names, "where each resolves and reads as
       Proposition prop:route (iv) cites it; for the per-setting weights that
       version must state them" (``req:supplier-version``, whose rule is that
       such values are not read from an artifact of an earlier version); the
       interface key
       ``requires_a_receiver_version_stating_them`` asks the code "to refuse a
       per-setting read from an earlier receiver version". THE WEIGHT ROUTE
       READS EVERY SLOT PER SETTING, so an artifact of an earlier version is
       REFUSED -- not read at its uniform weight at every setting, which would
       be this module choosing a reading its import does not state . A probe-free
       artifact of an earlier version is refused too: its one weight is the one the
       per-setting route would read, but the claim it would be read under is not the
       claim quoted here. (:func:`receiver_version_states_the_per_setting_weights`.)
    1. THE SETTINGS MATCH. Every entry carries a weight at EXACTLY the settings
       of ``T``, each once: Eq. ``eq:weightroute`` reads at ``(y_i, t)`` the
       weight of that setting, "so a slot missing a setting of T leaves a joint
       outcome without its weight and a slot with a setting outside T carries a
       weight no joint outcome reads; the supplier emits blocks and slot from
       one setting family, so either is a malformed artifact, and it is refused
       under this row's reason rather than repaired by a default".
    2. ``p_i^(t) >= 0``. NOT COVERED BY THE TOTAL-WEIGHT ROW, which tests the
       ROUTED total: "where ``r_min,i > 0`` A NEGATIVE ``p_i^(t)`` IS INVISIBLE
       IN THE ROUTED TOTAL". Such a declaration is "NOT A SECURITY BREAK -- the
       routed bound at ``p_i^(t) < 0`` is WEAKER than at ``p_i^(t) = 0`` -- but
       it CONTRADICTS THE SUPPLIER'S OWN SLOT GUARANTEE (A-RECV) and is refused
       rather than consumed".
    3. ``sum_i p_i^(t) <= 1`` AT EVERY ``t`` (receiver ``prop:slotvalid``).
    An entry with ONE weight at every setting -- the ``t``-uniform form, which
    every one-setting slot has -- is read to exactly the numbers the
    ``t``-uniform route gave (``rem:minweight``, last paragraph); it needs no
    clause of its own.

    The conventions block's ``fail_closed`` convention classifies the row with
    the total-weight row: EXACT SIGN AND EQUALITY COMPARISONS ON DECLARED
    SCALARS AND LABELS, decided in the substrate of Definition ``def:substrate`` and
    NOT an instance of Lemma ``lem:exactpsd``.
    """
    if not receiver_version_states_the_per_setting_weights(receiver_version):
        return refuse(
            FailClosedRule.HIGH_PHOTON_SLOT,
            RefusalReason.HIGH_PHOTON_SLOT_ILL_FORMED,
            f"the receiver artifact's version {receiver_version!r} does not state "
            "the per-setting multi-click weights (its thm:emitted-bound carries no "
            "eq:pmcsetting and its def:slot no weight per entry and setting); "
            "the weight route reads every slot per setting, and per-setting "
            "values of such a version are the content of no claim, so the "
            "slot is refused rather than read at its uniform weight "
            "(req:supplier-version; requires_a_receiver_version_stating_them)",
        )
    declared = tuple(settings)
    for index, bound in enumerate(bounds):
        carried = bound.settings
        if len(set(carried)) != len(carried) or set(carried) != set(declared):
            return refuse(
                FailClosedRule.HIGH_PHOTON_SLOT,
                RefusalReason.HIGH_PHOTON_SLOT_ILL_FORMED,
                f"the declared slot entry {index} carries weights at the settings "
                f"{list(carried)!r}, which are not exactly T = {list(declared)!r} "
                "of the supplied blocks, each once; eq:weightroute reads at "
                "(y_i, t) the weight of that setting, and a missing or extra "
                "setting is a malformed artifact, refused rather than repaired",
            )
        for setting, weight in bound.per_setting:
            if weight < 0:
                return refuse(
                    FailClosedRule.HIGH_PHOTON_SLOT,
                    RefusalReason.HIGH_PHOTON_SLOT_ILL_FORMED,
                    f"the declared slot entry {index} has p_i^({setting}) = "
                    f"{weight} < 0; the inputs table types the slot with "
                    "p_i^(t) >= 0, and a negative one is invisible in the ROUTED "
                    "total wherever r_min,i > 0 (cor:oneabsorbing), so no test on "
                    "the routed weights recovers it",
                )
    for setting in declared:
        total = sum(
            (bound.weight_at(setting) for bound in bounds), start=Fraction(0)
        )
        if total > 1:
            return refuse(
                FailClosedRule.HIGH_PHOTON_SLOT,
                RefusalReason.HIGH_PHOTON_SLOT_ILL_FORMED,
                f"the declared slot has sum_i p_i^({setting}) = {total} > 1, which "
                "contradicts the supplier's own slot guarantee (Assumption "
                "A-RECV, importing receiver's prop:slotvalid, per setting) and "
                "is refused rather than consumed",
            )
    return None
