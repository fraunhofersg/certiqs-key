"""Definition ``def:weight-route``: the dark-count descent and the routed weights.

"THE ORDER IS PART OF THE INTERFACE, NOT AN IMPLEMENTATION DETAIL: steps 1-2 are
classical post-processing of the physical outcome and must happen BEFORE step 3
(Remark ``rem:intertwining``)." The three steps are three functions below, in
that order, and :func:`consume_receiver_artifact` runs them once.

WHERE THIS FILE SITS, AND WHY IT IS NOT THE CORE'S
==================================================
This file holds steps 1 and 3 of the receiver consumption; step 2 is the core's.
Steps 1 and 3 -- the
dark-count post-processing and the weight route -- are statements about ONE
squasher's device model: a threshold detector with a dark-count matrix on raw
click patterns and a supplier's strengthening slot. Step 2, the joint family
``M_{(y,t)} = q_t M~_{y|t}``, is what ANY protocol with a private setting has,
so it is ``def:joint-family`` and lives in
:mod:`certiqs_key.reductions.joint`.

ONE GRANULARITY FACT DECIDES THE WHOLE OF THIS FILE
===================================================
The receiver-consumption block states it first because everything else follows from it.
The supplier emits the COARSE-GRAINED blocks, one per emitted letter, together with a
dark-count channel ``R`` that acts on RAW click patterns ``2^[K]`` and weights ``p_i``
certified for RAW outcome sets. "A consumer holding only the coarse blocks cannot in
general apply ``R`` to them, because ``S -> cg(S)`` is many-to-one and ``R`` need not
respect it." This module therefore REQUIRES ``R`` to descend through ``cg``, validates
that requirement, and REFUSES a declaration failing it rather than approximating.
The weights are
``p_i^(t)``, ONE PER SETTING, and the route forms the weight of a joint letter
``(y_i, t)`` from the weight of its own setting (Definition
``def:weight-route``; Remark ``rem:minweight``).

THE DESCENT TEST IS DIRECT, AND THAT IS A RULE
==============================================
The fail-closed table's row reads: "``R`` is monotone and DESCENDS through ``cg`` --
TESTED DIRECTLY, NOT VIA THE SHORTCUT Eq. ``eq:canonicalcg``".
:func:`descend` computes ``P(y | S') = sum_{S in cg^{-1}(y)} R_{S|S'}`` for every
column and checks that it depends on ``S'`` only through ``cg(S')`` -- which is
Lemma ``lem:descent``'s definition, verbatim. Remark ``rem:descentneedsconstant``
exhibits a monotone ``R`` and a ``cg`` meeting TWO of Eq. ``eq:canonicalcg``'s
three clauses for which ``R^cg`` is not well defined, and records that the
sufficient condition is "ONLY A SHORTCUT THAT MUST ITSELF BE CHECKED IN FULL".
An implementation testing the shortcut instead would accept a declaration it
must refuse, so no code path here looks at the shape of ``cg`` at all.

THE ONE ARITHMETIC EVALUATION OF THE WHOLE MODULE
=================================================
Eq. ``eq:weightroute`` is it, and design.md says so: this module "states NO
CLAIM WHOSE PROOF DEPENDS ON A FLOATING-POINT COMPUTATION", and the single place
a number is formed from other numbers is

    ``p_(y_i,t) = q_t ( (1 - r_min,i) p_i^(t) + r_min,i )``,

``p_i^(t)`` the slot's weight AT THE LETTER'S OWN SETTING ``t`` (the
per-setting route; at a slot with one weight at every setting it
is the ``t``-uniform route, number for number, ``rem:minweight``).

Over the exact rationals of :mod:`certiqs_key.foundations.exact` this is exact and
the conditional rounding rule -- round TOWARD ZERO if the upstream evaluation
ever becomes exact or interval-valued -- is never engaged. The
direction is recorded there as
:data:`~certiqs_key.foundations.exact.WEIGHT_ROUNDING_DIRECTION`.

THREE THINGS ARE LOAD-BEARING IN Eq. ``eq:weightroute`` AND NONE IS DROPPED
==========================================================================
The receiver-consumption block enumerates them and :func:`weight_route` honours each.

(a) ``r_min`` IS INDEXED BY THE BOUNDED LETTER: "it is a property of row ``y_i``
    of ``R^cg`` read across the columns ``y' != y_i``, and one entry's value is
    not another's". :func:`minimum_off_letter_rate` takes the letter and reads
    that row.
(b) THE ABSORBING CONDITION IS A HYPOTHESIS, NOT A CONSEQUENCE. Remark
    ``rem:absorbneeded`` shows that without it Eq. ``eq:routebound`` is false in
    the UNSAFE direction -- it would assert a weight the device does not have,
    "the failure Assumption A-RECV's ledger row calls a security break". So
    :func:`weight_route` refuses rather than computing when a bounded letter is
    not absorbing, and the refusal covers THE WHOLE ARTIFACT: Remark
    ``rem:absorbneeded`` records that one non-absorbing letter could in
    principle be handled by zeroing that entry, and that this module refuses
    instead, "because a partially honoured slot would emit a target whose
    weights no longer correspond ENTRY-FOR-ENTRY to the declared slot, and NO
    DECLARED FIELD RECORDS WHICH ENTRY WAS SILENTLY ZEROED".
(c) A POSITIVE ``r_min,i`` CAN OCCUR ONLY AT ``r = 1`` (Corollary
    ``cor:oneabsorbing``), so for ``r >= 2`` every entry contributes the
    un-improved weight ``q_t p_i^(t)`` -- "which is sound, merely not
    sharpened by the dark counts". Nothing here special-cases that; it falls out of the
    minimum, and :func:`weight_route` never needs to know ``r``.

THE EMPTY-MINIMUM CONVENTION IS THE CONSERVATIVE VALUE, NOT A TIE-BREAK
=======================================================================
The inputs table and Proposition ``prop:route`` both state it: ``r_min,i := 0`` when
the minimum is over the EMPTY SET, that is when ``Y = {y_i}``. Eq.
``eq:weightroute`` is increasing in ``r`` for ``p_i^(t) <= 1``, so ``r = 0`` gives
the SMALLEST admissible weight, hence the cleanest target, hence the most
generous adversary (Corollary ``cor:monotone``). Any other convention -- an
infimum over the reals would give ``1`` -- would assert a weight the device has
not been shown to have.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.foundations.exact import (
    Matrix,
    add,
    direct_sum,
    lattice_floor,
    scale,
    zeros,
)
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.reductions.companion import combined_factor
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import (
    ClickPattern,
    CoarseGraining,
    DarkCountChannel,
    HighPhotonBound,
    JointOutcome,
    Label,
    ProbeDeclaration,
    ReceiverArtifactRows,
    patterns,
)

__all__ = [
    "BoundedLetter",
    "DescendedChannel",
    "bounded_letters",
    "declared_column_sums",
    "descend",
    "is_column_stochastic",
    "is_monotone",
    "minimum_off_letter_rate",
    "post_processed_preserved_blocks",
    "post_processed_preserved_factors",
    "preserved_blocks",
    "smallest_declared_entry",
    "weight_route",
]


def declared_column_sums(
    channel: DarkCountChannel,
) -> dict[ClickPattern, Fraction]:
    """Return ``sum_{S subset [K]} R_{S|S'}`` for every column ``S'``, exactly.

    THE SUM RUNS OVER THE WHOLE INDEX SET ``2^[K]``, not over the keys the
    declaration happens to carry. ``R`` is typed on ``2^[K]`` and
    :meth:`~certiqs_key.reductions.inputs.DarkCountChannel.value` reads an absent
    pair as zero, which is the declaration's own convention and not a default
    substituted for a missing datum. Summing the present keys instead would make
    a column that declares nothing at all sum vacuously, and a column of zeros
    must REFUSE: its sum is ``0``, not ``1``.
    """
    index_set = patterns(channel.ports)
    return {
        column: sum(
            (channel.value(row, column) for row in index_set), start=Fraction(0)
        )
        for column in index_set
    }


def smallest_declared_entry(channel: DarkCountChannel) -> Fraction:
    """Return ``min_{S,S'} R_{S|S'}`` over the whole index set ``2^[K]``.

    Zero when every declared entry is positive, because an absent pair is a
    declared zero. The value is what the row's non-negativity half compares
    against, and it is exact.
    """
    index_set = patterns(channel.ports)
    return min(
        (channel.value(row, column) for row in index_set for column in index_set),
        default=Fraction(0),
    )


def is_column_stochastic(channel: DarkCountChannel) -> bool:
    """Whether the DECLARED ``R`` is EXACTLY column-stochastic, over ``2^[K]``.

    Section ``sec:failclosed``'s column-stochasticity row, both halves: "the
    declared dark-count matrix ``R`` is EXACTLY column-stochastic:
    ``R_{S|S'} >= 0`` for every entry, and ``sum_{S subset [K]} R_{S|S'} = 1``
    for every column ``S'``". A conjunction -- one half failing is enough.

    THE SUBJECT IS THE DECLARED MATRIX AND NOT THE DESCENDED ONE, and the
    contract proves that this suffices: the fibres of ``cg`` PARTITION ``2^[K]``,
    ``cg`` being a total surjection, so ``R^cg_{y|y'}`` is a sum of non-negative
    entries and ``sum_y R^cg_{y|y'} = sum_S R_{S|S'} = 1``. "Deciding it on the
    declared matrix therefore DISCHARGES IT FOR THE DESCENDED ONE, AND NO SECOND
    ROW IS STATED" (Remark ``rem:colstoch``). See
    :meth:`DescendedChannel.is_column_stochastic`, which is that implication
    made checkable and is NOT a rule.

    NOTHING IS DECIDED WITHIN ANYTHING. At 1.0.0 this module carries no
    tolerance at all and ``kappa`` is not one -- the ``lattice_exponent`` row
    says "IT IS NOT A TOLERANCE, NOTHING IS ADMITTED OR REFUSED WITHIN
    ``kappa``" -- so the declared scalars here, "the dark-count matrix ``R``
    with its COLUMN-STOCHASTICITY, descent, monotonicity and absorbing
    conditions", are compared against ``0`` and ``1`` exactly
    (Rem. ``rem:exactboundary``). Lemma
    ``lem:exactpsd`` is not invoked: Section
    ``sec:conventions``'s ``exact_arithmetic`` bullet names this row as one of
    the THREE neighbouring rows that are exact "WITHOUT BEING INSTANCES OF THAT
    PREDICATE", being "a SIGN-AND-EQUALITY COMPARISON ON THE DECLARED ENTRIES OF
    R". Over :class:`~fractions.Fraction` both comparisons are exact.
    """
    if smallest_declared_entry(channel) < 0:
        return False
    return all(total == 1 for total in declared_column_sums(channel).values())


def is_monotone(channel: DarkCountChannel) -> bool:
    """Whether ``R_{S|S'} > 0 => S' subset S``, decided exactly.

    Section ``sec:inputs``'s monotonicity condition on the declared dark-count
    channel. Physically: a dark count adds a click and never removes one.

    IT IS THAT EXACT IMPLICATION AND NOTHING MORE, which is what makes it
    INDEPENDENT of :func:`is_column_stochastic` rather than implied by it. A
    NEGATIVE entry in a forbidden position satisfies the implication VACUOUSLY
    -- it is not ``> 0`` -- and is refused by the column-stochasticity row
    instead; a STRICTLY POSITIVE entry in a forbidden position fails here while
    leaving column-stochasticity untouched. "THE TWO ROWS ARE NEEDED TOGETHER
    AND NEITHER COVERS THE OTHER" (Remark ``rem:darkcompose``), and folding them
    into one test would emit the wrong reason string in both directions.

    THE GUARD IS ``> 0`` AND NOT ``!= 0``: testing every entry not equal to zero
    would refuse a NEGATIVE entry in a forbidden position
    under ``dark_counts_do_not_descend``. The contract states the implication
    with a strict inequality in three places -- Section ``sec:inputs``'s type
    row, the descent row's own "THAT EXACT IMPLICATION AND NOTHING MORE", and
    Remark ``rem:darkcompose``'s (D2) -- so the vacuous case belongs to the
    column-stochasticity row. THE GUARD LOOSENS NOTHING: every declaration
    that is admitted HERE rather than refused has a negative entry, so it fails
    the non-negativity half of :func:`is_column_stochastic` and is refused under
    ``dark_counts_not_column_stochastic`` instead. Which row
    names the cause is exactly what Remark ``rem:colstoch`` says the
    column-stochasticity row is for.
    """
    return all(
        column <= row for (row, column), value in channel.entries.items() if value > 0
    )


@dataclass(frozen=True)
class DescendedChannel:
    """``R^cg``, the descended matrix of Lemma ``lem:descent``.

    ``letters`` is the declared order of ``Y``; ``entries[(y, y')]`` is
    ``R^cg_{y|y'}``, and an absent pair is zero.
    """

    letters: tuple[Label, ...]
    entries: Mapping[tuple[Label, Label], Fraction]

    def value(self, row: Label, column: Label) -> Fraction:
        """Return ``R^cg_{row|column}``, zero where the matrix is silent."""
        return self.entries.get((row, column), Fraction(0))

    def is_absorbing_at(self, letter: Label) -> bool:
        """Whether Eq. ``eq:absorbing`` holds at ``letter``: ``R^cg_{y|y} = 1``."""
        return self.value(letter, letter) == 1

    def is_column_stochastic(self) -> bool:
        """Whether every column of ``R^cg`` is non-negative and sums to one.

        THIS IS NOT A FAIL-CLOSED ROW AND MUST NOT BECOME ONE. Section
        ``sec:failclosed`` decides column-stochasticity on the DECLARED ``R``
        -- :func:`is_column_stochastic` -- and says why that suffices:
        "Lemma ``lem:descent`` carries BOTH HALVES to ``R^cg``, so NO SECOND ROW
        IS STATED ON THE DESCENDED MATRIX." Remark ``rem:colstoch`` proves the
        implication from the fibres of ``cg`` partitioning ``2^[K]``. An
        implementation that added a row here "has added a rule the contract does
        not state" and would need a twenty-eighth reason string, which does not
        exist.

        WHAT IT IS FOR: making that implication CHECKABLE rather than asserted.
        The frozen oracle carries the descended matrix beside the declared one
        for every case precisely so that a test can confirm the property
        travels -- including the non-trivial direction, where a fibre has two
        elements and the descended entry is a genuine sum, and the direction
        where a declared defect reappears downstream.
        """
        for column in self.letters:
            entries = [self.value(row, column) for row in self.letters]
            if any(value < 0 for value in entries):
                return False
            if sum(entries, start=Fraction(0)) != 1:
                return False
        return True


def descend(
    channel: DarkCountChannel, coarse_graining: CoarseGraining
) -> DescendedChannel | None:
    """Return ``R^cg`` if ``R`` descends through ``cg``, else ``None``.

    THE TEST IS THE PROPERTY ITSELF, NOT THE SHORTCUT. Lemma ``lem:descent``
    defines descent as: ``P(y | S') := sum_{S in cg^{-1}(y)} R_{S|S'}`` depends
    on ``S'`` only through ``cg(S')``. This function computes ``P(y | S')`` for
    every letter and every column and compares the columns fibre by fibre. Two
    columns with the same ``cg``-image and different values make ``R^cg``
    ill defined, and the return is ``None`` -- which the caller turns into
    ``dark_counts_do_not_descend``.

    Eq. ``eq:canonicalcg`` is a SUFFICIENT condition and is deliberately not
    consulted: Remark ``rem:descentneedsconstant`` exhibits an ``R`` and a
    ``cg`` meeting two of its three clauses for which descent fails.
    """
    all_patterns = list(coarse_graining.assignment)
    fibres = {
        letter: coarse_graining.fibre(letter) for letter in coarse_graining.letters
    }
    column_values: dict[ClickPattern, dict[Label, Fraction]] = {}
    for source in all_patterns:
        values: dict[Label, Fraction] = {}
        for letter in coarse_graining.letters:
            values[letter] = sum(
                (channel.value(target, source) for target in fibres[letter]),
                start=Fraction(0),
            )
        column_values[source] = values
    entries: dict[tuple[Label, Label], Fraction] = {}
    for image in coarse_graining.letters:
        fibre = fibres[image]
        if not fibre:
            # `cg` is surjective onto the declared alphabet, so an empty fibre
            # is a malformed declaration rather than a failure of descent.
            raise MalformedInputError(
                f"the coarse-graining is not surjective: no pattern maps to {image}"
            )
        representatives = sorted(
            fibre, key=lambda pattern: (len(pattern), sorted(pattern))
        )
        reference = column_values[representatives[0]]
        for other in representatives[1:]:
            if column_values[other] != reference:
                return None
        for letter in coarse_graining.letters:
            value = reference[letter]
            if value != 0:
                entries[(letter, image)] = value
    return DescendedChannel(letters=coarse_graining.letters, entries=entries)


def minimum_off_letter_rate(descended: DescendedChannel, letter: Label) -> Fraction:
    """Return ``r_min,i = min_{y' != y_i} R^cg_{y_i|y'}``, with the empty convention.

    "It is a property of ROW ``y_i`` of ``R^cg`` read across the COLUMNS
    ``y' != y_i``, and one entry's value is not another's" (the receiver-consumption
    block, fact (a)). When ``Y = {y_i}`` the minimum is over the empty set and the value
    is ``0`` by the convention the inputs table and Proposition ``prop:route`` both
    state -- the conservative value, which reduces Eq. ``eq:weightroute`` to the
    un-improved bound.
    """
    others = [
        descended.value(letter, column)
        for column in descended.letters
        if column != letter
    ]
    if not others:
        return Fraction(0)
    return min(others)


@dataclass(frozen=True)
class BoundedLetter:
    """One bounded letter of the slot, with everything Eq. ``eq:weightroute`` needs.

    ``weights`` is the slot entry's ``((t, p_i^(t)), ...)``, ONE WEIGHT PER
    SETTING as the supplier states them (receiver ``def:slot``;
    ``def:weight-route``), carried unchanged from the entry; Eq.
    ``eq:weightroute`` reads the one of the joint letter's own setting
    (:meth:`weight_at`).
    """

    letter: Label
    weights: tuple[tuple[Label, Fraction], ...]
    absorbing: bool
    r_min: Fraction

    def weight_at(self, setting: Label) -> Fraction:
        """Return ``p_i^(t)`` at ``setting``, the weight Eq. ``eq:weightroute`` reads.

        Raises:
            MalformedInputError: if the entry carries no weight at ``setting``;
                the ``high_photon_slot`` row refuses such a slot before the
                route runs, so reaching this is a caller's defect.
        """
        for candidate, weight in self.weights:
            if candidate == setting:
                return weight
        raise MalformedInputError(
            f"the bounded letter {self.letter!r} carries no weight at the setting "
            f"{setting!r}; the high_photon_slot row refuses a slot whose settings "
            "are not exactly T before any weight is routed"
        )


def bounded_letters(
    bounds: Sequence[HighPhotonBound],
    coarse_graining: CoarseGraining,
    descended: DescendedChannel,
) -> tuple[BoundedLetter, ...] | None:
    """Return one :class:`BoundedLetter` per slot entry, or ``None`` if a fibre fails.

    The inputs table: "each bounded set ``O_i`` MUST BE EXACTLY A FIBRE,
    ``O_i = cg^{-1}(y_i)`` for distinct letters ``y_i``, else refused". Remark
    ``rem:fibre`` is why the condition cannot be dropped, in both directions: a
    SPLIT fibre leaves no letter with a bound, because "the supplier certified
    ONLY THE SUM" and "a bound on a sum of positive operators says nothing about
    the individual summands"; a MERGED one leaves the weight attached to a
    letter whose fibre is larger than the certified set -- sound, "BUT ONLY IF
    THE CONTAINMENT IS VALIDATED RATHER THAN ASSUMED. This module therefore
    requires EQUALITY".

    ``None`` means the fibre condition failed, which the caller turns into
    ``bound_set_not_a_fibre``. A non-absorbing letter is REPORTED rather than
    dropped: the record carries ``absorbing=False`` so that the refusal rule can
    name it, and :func:`weight_route` refuses on it.
    """
    seen: set[Label] = set()
    out: list[BoundedLetter] = []
    for bound in bounds:
        letter: Label | None = None
        for candidate in coarse_graining.letters:
            if coarse_graining.fibre(candidate) == bound.outcome_set:
                letter = candidate
                break
        if letter is None or letter in seen:
            return None
        seen.add(letter)
        out.append(
            BoundedLetter(
                letter=letter,
                weights=bound.per_setting,
                absorbing=descended.is_absorbing_at(letter),
                r_min=minimum_off_letter_rate(descended, letter),
            )
        )
    return tuple(out)


def weight_route(
    letters: Sequence[BoundedLetter],
    probe: ProbeDeclaration,
    joint_alphabet: Sequence[JointOutcome],
    *,
    lattice_exponent: int,
) -> dict[JointOutcome, Fraction] | None:
    r"""Eq. ``eq:weightroute``, one bounded letter at a time, ROUNDED DOWN.

    ``p^_(y_i,t) = q_t ( (1 - r_min,i) p_i^(t) + r_min,i )`` at every bounded
    letter and every setting -- ``p_i^(t)`` THE WEIGHT OF THE JOINT LETTER'S
    OWN SETTING, as the supplier states it (receiver ``thm:emitted-bound``
    Eq. ``eq:pmcsetting``; ``prop:route``; ``rem:minweight``) -- and
    ``p_(y,t) = 0`` FOR EVERY OTHER ``(y, t)``; and then::

        p_(y_i,t) = lat( p^_(y_i,t) ) = 2^-kappa floor( 2^kappa p^_(y_i,t) )

    Eq. ``eq:latdown``. "**THE EMITTED WEIGHT IS** ``p_(y_i,t)`` **AND NOT**
    ``p^_(y_i,t)``, and THE DIRECTION OF THAT ROUNDING IS THE WHOLE OF WHAT
    MAKES IT SAFE: it is THE ONE EMITTED NUMBER OF THIS CONTRACT THAT A
    DOWNSTREAM INEQUALITY CONSUMES AS A BOUND, Eq. eq:certweights IS PRESERVED
    WHEN A CERTIFIED WEIGHT IS LOWERED AND DESTROYED WHEN ONE IS RAISED, and
    ``lat(.)`` ONLY LOWERS" (Prop. ``prop:route``, Rem. ``rem:weightfree``;
    spec/architecture.md 2.9, condition **(D-DIR)**).

    THE FLOOR IS A DIFFERENT MECHANISM FROM ``def:emitnorm`` (2), WHICH ROUNDS
    TO NEAREST, and the two are deliberately two functions of
    :mod:`certiqs_key.foundations.exact`. Their safety arguments do not transfer:
    to-nearest is correct there because it is odd-symmetric and carries a
    Hermitian block to a Hermitian one, and a floor is correct here because it
    only lowers a certified weight. AN IMPLEMENTATION THAT USES ONE FUNCTION
    FOR BOTH HAS MERGED TWO RULES WITH DIFFERENT SAFETY ARGUMENTS. A floor
    also has NO TIE TO BREAK, which is why 1.0.1's rounding-tie amendment does
    not reach this line.

    ``p >= 0`` NEEDS NO CLAMP, and the contract says why: ``p^`` "is a product
    of non-negative declared numbers, and THE LARGEST LATTICE NUMBER AT MOST A
    NON-NEGATIVE RATIONAL IS ITSELF NON-NEGATIVE" (the receiver-consumption block (d)).

    ``1 - p`` IS NOT COMPUTED HERE AND IS NEVER ROUNDED SEPARATELY. It is
    RECOMPUTED from the emitted weights where the flag sector is built,
    "because the flag sector's completeness is the identity
    ``sum_v p_v + (1 - p) = 1`` and ROUNDING BOTH SIDES INDEPENDENTLY WOULD
    BREAK IT" (the outputs table, ``emission_record``; Thm. ``thm:emit`` (ii)).

    Returns ``None`` when some bounded letter is not absorbing, which the caller
    turns into ``bounded_letter_not_absorbing``. Nothing is computed in that
    case: Remark ``rem:absorbneeded`` shows the formula is then FALSE IN THE
    UNSAFE DIRECTION, and the refusal covers the whole artifact rather than the
    offending entry -- see fact (b) in the module docstring.

    Args:
        letters: the bounded letters, with their ``r_min`` and declared weight.
        probe: the declared probe alphabet and its ``q_t``.
        joint_alphabet: the declared order of ``V``.
        lattice_exponent: the declared ``kappa``, already validated by Section
            4.14's first row.
    """
    if any(not letter.absorbing for letter in letters):
        return None
    weights = {letter.letter: letter for letter in letters}
    out: dict[JointOutcome, Fraction] = {}
    for outcome in joint_alphabet:
        letter_name, setting = outcome
        bounded = weights.get(letter_name)
        if bounded is None:
            # Zero is on every lattice, so lat(0) = 0 and the floor is the
            # identity here; it is applied anyway, so that no emitted weight
            # reaches the artifact by a path the rounding rule did not take.
            out[outcome] = Fraction(0)
            continue
        q_t = probe.weights[setting]
        # THE WEIGHT OF THIS JOINT LETTER'S OWN SETTING (eq:weightroute). With one
        # weight at every setting -- every one-setting slot -- this is the t-uniform
        # route's number, and the same exact arithmetic and the same floor follow
        # (rem:minweight).
        p_t = bounded.weight_at(setting)
        hat = q_t * ((1 - bounded.r_min) * p_t + bounded.r_min)
        out[outcome] = lattice_floor(hat, lattice_exponent)
    return out


def preserved_blocks(
    artifact: ReceiverArtifactRows,
    family: Mapping[JointOutcome, tuple[Matrix, ...]],
    joint_alphabet: Sequence[JointOutcome],
) -> dict[JointOutcome, Matrix]:
    """Return ``blk M^{<=N}_v`` as the direct sum of the emitted blocks.

    The conventions block, ``subsystem_order``: "the preserved photon-number blocks IN
    INCREASING ``m``". The conventions block, ``block_restriction``: ``blk M^{=n}``
    denotes an operator BLOCK, NOT A COMPRESSION -- ``blk M^{<=N}`` acts on
    ``H(C_{<=N})`` and is NOT ``Pi^{<=N} M Pi^{<=N}``. The distinction has
    content precisely because ``M`` may have entries off the block structure;
    what the direct sum below assembles are the blocks the supplier emitted, and
    nothing is projected.
    """
    del artifact
    return {outcome: direct_sum(list(family[outcome])) for outcome in joint_alphabet}


def post_processed_preserved_blocks(
    artifact: ReceiverArtifactRows,
    probe: ProbeDeclaration,
    descended: DescendedChannel,
    joint_alphabet: Sequence[JointOutcome],
) -> dict[JointOutcome, tuple[Matrix, ...]]:
    """Return steps 1 and 2 together, kept PER PRESERVED BLOCK.

    The numbers the flat instance's DATA SECTORS are, held one block at a time
    because ``def:emitnorm`` acts per data sector and, for its steps (3) and
    (4), per class: "on each block ``m <= N`` and at each ``t in T``". A direct
    sum would hide the sector boundary the normalizer needs, and
    ``Delta_s`` is defined PER SECTOR (Eq. ``eq:displacement``) rather than over
    the sum.

    Step 1 is post-processing by ``R^cg`` (Lemma ``lem:linear`` (i)), step 2 the
    joint alphabet ``M_{(y,t)} = q_t M~_{y|t}`` (Lemma ``lem:linear`` (ii),
    ``def:joint-family``). In the DARK-COMPOSED input form
    (``ReceiverArtifactRows.photon_blocks_form``) the supplied blocks are the
    composed family itself and step 1 is not applied to them: the datum is
    step 2 alone, which ``wpfss/prop:precomposed-blocks`` (ii) shows is the
    same instance as composing here wherever no snap moved a block. Both are
    linear and (i) says the result is "a POVM
    with THE SAME PHOTON-NUMBER BLOCK STRUCTURE", so no block is opened and none
    is mixed with another. THE ABOVE-CUTOFF BLOCK IS ABSENT THROUGHOUT and no
    step invents one.
    """
    per_outcome: dict[JointOutcome, tuple[Matrix, ...]] = {}
    dark_composed = artifact.photon_blocks_form == "dark_composed"
    for outcome in joint_alphabet:
        letter, setting = outcome
        per_block: list[Matrix] = []
        for index in range(len(artifact.channel_grading.block_dimensions)):
            if dark_composed:
                # THE DARK-COMPOSED FORM: the supplied blocks are already the
                # family the model takes below the cutoff after the dark
                # counts, so step 1 is NOT applied again and the datum is step
                # 2 alone, A^(m)_(y,t) = q_t M~^(m)_{y|t}
                # (wpfss/def:weight-route, the two input forms;
                # wpfss/prop:precomposed-blocks (ii)). R^cg is still formed and
                # decided, and the routed weights still read it.
                per_block.append(
                    scale(
                        probe.weights[setting],
                        artifact.photon_blocks[(letter, setting)][index],
                    )
                )
                continue
            accumulated = zeros(artifact.channel_grading.block_dimensions[index])
            for column in descended.letters:
                coefficient = descended.value(letter, column)
                if coefficient == 0:
                    continue
                accumulated = add(
                    accumulated,
                    scale(
                        coefficient,
                        artifact.photon_blocks[(column, setting)][index],
                    ),
                )
            per_block.append(scale(probe.weights[setting], accumulated))
        per_outcome[outcome] = tuple(per_block)
    return per_outcome


def post_processed_preserved_factors(
    artifact: ReceiverArtifactRows,
    probe: ProbeDeclaration,
    descended: DescendedChannel,
    joint_alphabet: Sequence[JointOutcome],
    factors: Mapping[JointOutcome, tuple[FactorEnclosure | None, ...]],
) -> dict[JointOutcome, tuple[FactorEnclosure | None, ...]]:
    """Return the factor enclosure of every element of the flat datum, or ``None``.

    The factor mirror of :func:`post_processed_preserved_blocks`, by
    ``reductions/wpfss/cor:flat-companion``: the flat instance's rule of (I1)
    is a non-negative combination with the coefficients ``q_t R^cg_{y|y'}``
    (bare form) and ``q_t`` (dark-composed form), so each element's factor
    enclosure is :func:`combined_factor` of the handed blocks' own
    (``factors``, keyed as ``photon_blocks`` is, ``None`` on a block that
    carries none).
    """
    out: dict[JointOutcome, tuple[FactorEnclosure | None, ...]] = {}
    dark_composed = artifact.photon_blocks_form == "dark_composed"
    dimensions = artifact.channel_grading.block_dimensions
    for outcome in joint_alphabet:
        letter, setting = outcome
        weight = probe.weights[setting]
        per_block: list[FactorEnclosure | None] = []
        for index, dimension in enumerate(dimensions):
            if dark_composed:
                terms = [(weight, _factor_at(factors, (letter, setting), index))]
            else:
                terms = [
                    (
                        weight * descended.value(letter, column),
                        _factor_at(factors, (column, setting), index),
                    )
                    for column in descended.letters
                ]
            per_block.append(combined_factor(terms, dimension))
        out[outcome] = tuple(per_block)
    return out


def _factor_at(
    factors: Mapping[JointOutcome, tuple[FactorEnclosure | None, ...]],
    key: JointOutcome,
    index: int,
) -> FactorEnclosure | None:
    found = factors.get(key, ())
    return found[index] if index < len(found) else None
