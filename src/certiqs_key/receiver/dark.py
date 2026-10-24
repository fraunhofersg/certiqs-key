"""Dark counts as a classical outcome channel on ``2^[K]``.

Definition ``def:darkadm`` and Theorem ``thm:dark-counts``. With the efficiencies
inside the Grams, the remaining detector imperfection is a click produced with
no incident light. Dark counts change the recorded OUTCOME, not the optical
modes, so they are a classical channel on the label -- and a channel satisfying
(D1) and (D2) exactly can only HELP the multiclick bound. The care is in HOW
MUCH it helps.

    (D1) column-stochastic:  R_{S|S'} >= 0 and sum_S R_{S|S'} = 1
    (D2) monotone:           R_{S|S'} > 0 implies S' subset of S
                             -- a dark count ADDS a click and never removes one

THE ``r_min`` TRAP, WHICH THIS MODULE IS BUILT AROUND
=====================================================
Eq. ``eq:rmin`` minimizes ``R_{MC|S'}`` over EVERY non-multiclick column, THE
NO-CLICK COLUMN ``S' = empty`` INCLUDED. Remark ``rem:rmintrap``: minimising
only over the single-click columns gives an INVALID bound whenever
``R_{MC|empty} < R_{MC|{k}}``, and that is THE GENERIC CASE rather than a
corner one -- at ``K = 4`` with ``p = 10^-5`` the two differ by more than four
orders of magnitude. The reason the column cannot be excluded is that the
no-click element does not vanish in the high-photon sectors of a lossy
receiver: ``lmin(blk M_empty^{(=n)}) = (1 - lmax(A_Sigma))^n > 0`` whenever
``lmax(A_Sigma) < 1``, so in exactly the regime where the high-photon bound
matters, the column that the shortcut discards carries weight.

:func:`minimum_multiclick_mass` implements Eq. ``eq:rmin`` as written. The
single-click-only shortcut is NOT implemented here, in either direction: the
contract calls it invalid, so this module does not compute it.

THE COMPOSITION IS THE CONSUMER'S, AND THE INEQUALITY IS NAMED
==============================================================
``interface.yaml`` ``outputs``: ``photon_blocks`` and ``high_photon_bounds``
are the BARE, PRE-DARK-COUNT objects -- ``R`` is emitted separately and THE
CONSUMER COMPOSES -- so nothing in this package folds ``r_min`` into an
emitted ``p_mc``. What is named is WHICH inequality a consumer composes with
(Requirement ``req:dark-channel-record``):

    Eq. eq:darkpmcslack   blk Mtilde^{(>N)}_{MC} >=
                              ((1 - rbar) p_mc + rbar - delta_dc) id^{(>N)}

**not** Eq. ``eq:darkpmc``, which holds only for an EXACTLY admissible ``R``.
:func:`composed_slack` is the first and :func:`improved_bound` the second, and
:func:`overstatement` is Eq. ``eq:darkoverstate``, the difference -- first
order in the receiver tolerances and in the UNSAFE direction (Remark
``rem:d2slack`` (e)). Both are offered and neither is applied to an emitted
``p_mc``.

THREE SCALARS UNDER DISTINCT NAMES, AND NOTHING IS REPAIRED
===========================================================
``interface.yaml`` ``outputs.dark_count_channel`` emits ``R`` with

    r_min      Eq. eq:rmin, EXACTLY AS IT COMPUTES IT -- unmodified, and it
               "is the only one from which a reader can see that a declared
               channel produced r_min > 1 at all" (the lead-in of
               req:dark-channel-record);
    rbar       Eq. eq:rbar, min{r_min, 1}: a COEFFICIENT in a stated
               inequality, not a repair of r_min and not a clamp of R;
    delta_dc   Eq. eq:darkdelta, 0 on the generated route and
               eps_4 + (K + 1) eps_2 on the declared one.

``rbar`` exists because the widened (D1) of Definition ``def:tolmap`` (iii)
admits column sums up to ``1 + eps_4``, so Eq. ``eq:rminupper`` gives
``R_{MC|S'} <= 1 + (K + 2) eps_4`` and ``r_min > 1`` IS REACHABLE. Without the
cap, the coefficient ``1 - r_min`` that Theorem ``thm:dark-counts`` (iv)'s
substitution step requires to be non-negative would not be, and the composed
bound would FAIL -- IN THE UNSAFE DIRECTION -- by ``(r_min - 1)(1 - p_mc)``
(Remark ``rem:d2slack`` (c)).

**``rbar`` IS NEVER FLOORED AT 0.** Proposition ``prop:dark-slack-bound``'s proof
ends: no step uses a bound on ``r_min`` from either side, AND NO STEP USES THE
SIGN OF ``r_min`` OR OF ``rbar``. A negative ``r_min`` -- reachable, because the
widened (D1) admits entries down to ``-eps_4`` -- gives a negative ``rbar``, and
the inequality still holds, because replacing each coefficient of a sum of
POSITIVE operators by a SMALLER real gives a Loewner-smaller operator, which is
sign-blind. Flooring would RAISE a coefficient and strengthen a stated
inequality without a warrant.

**``delta_dc`` IS A FUNCTION OF THE ROUTE AND THE DECLARED TOLERANCES, NEVER OF
THE CHANNEL.** Eq. ``eq:darkdelta`` is a two-case definition on the ROUTE. The
witness channel of Remark ``rem:d2slack`` occupies no (D2)-forbidden position at
all and is admitted at ``eps_2 = 0``, and its ``delta_dc`` still carries the
``(K + 1) eps_2`` term of the declaration it arrived under.

BOTH ROUTES AT ONCE IS A REFUSAL
================================
The ``detector_layer`` input carries ``p_dc|k`` UNCONDITIONALLY, so the
generator of the independent product form Eq. ``eq:darkR`` is always present;
the ``dark_count_channel`` input ADDITIONALLY admits a declared ``R``. The rule
for a request supplying both is stated three times over (``interface.yaml``
``inputs.dark_count_channel.route_exclusivity_rule``): the inputs table,
Requirement ``req:dark-route-exclusive`` and the refusal rules. THE TWO ROUTES
ARE EXCLUSIVE: a request that declares an explicit ``R`` while some
``p_dc|k`` is non-zero in ``detector_layer`` is REFUSED, with the verbatim
reason ``dark_count_channel_declared_twice``. It is a REFUSAL, not a
precedence rule and not a consistency check. The converse is fixed with it: a
declared ``R`` requires ``p_dc|k = 0`` for every ``k``, so a declared ``R``
beside all-zero per-port probabilities is ADMITTED and takes the declared
route.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from itertools import combinations

import numpy as np

from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import Matrix, NumericalTolerances, Scalar, to_float
from certiqs_key.receiver.reasons import DARK_CONDITION_REASONS, Refusal, RefusalReason

__all__ = [
    "DarkCountChannel",
    "DarkCountRoute",
    "capped_coefficient",
    "check_dark_channel",
    "check_dark_count_source",
    "compose_blocks",
    "composed_slack",
    "composition_correction",
    "improved_bound",
    "improves_on_weight",
    "minimum_multiclick_mass",
    "multiclick_mass",
    "overstatement",
    "product_form",
]


class DarkCountRoute(StrEnum):
    """Which of the two routes the emitted ``R`` came from.

    Remark ``rem:corrdark``: the artifact records which of the two routes the
    emitted ``R`` came from, and for a declared ``R`` what must then be CHECKED
    rather than derived is (D1) and (D2).
    """

    #: Eq. eq:darkR generated from the per-port {p_dc|k}. Theorem thm:dark-counts (i)
    #: DERIVES both (D1) and (D2) for it.
    PER_PORT_PRODUCT_FORM = "per_port_product_form"
    #: A declared column-stochastic multiclick-absorbing R on 2^[K].
    DECLARED_MATRIX = "declared_matrix"


@dataclass(frozen=True)
class DarkCountChannel:
    """A channel ``R = (R_{S|S'})`` on ``2^[K]``, stored column by column.

    Only the non-zero entries of a column are held: (D2) makes every other
    entry zero by definition, and storing the zeros would invite an
    implementation to sum over a dense matrix and lose the monotonicity that
    makes Theorem ``thm:dark-counts`` (iii) true.
    """

    port_count: int
    route: DarkCountRoute
    columns: Mapping[frozenset[int], Mapping[frozenset[int], Scalar]]

    def entry(self, row: frozenset[int], column: frozenset[int]) -> Scalar:
        """Return ``R_{S|S'}``, zero where the column carries no entry.

        THE ENTRY TYPE IS :data:`~certiqs_key.receiver.numerics.Scalar`, not
        ``float``, and the two routes fill it differently ON PURPOSE. On the
        GENERATED route :func:`product_form` evaluates Eq. ``eq:darkR``
        EXACTLY, so the entries are exact rationals and every column sums to
        exactly 1 -- which is what makes Definition ``def:darkadm``'s (D1) and
        (D2) holding BY CONSTRUCTION for Eq. ``eq:darkR`` (Theorem
        ``thm:dark-counts`` (i)) true of the emitted matrix and not only of the
        equation. On the DECLARED route the entries are the DECLARER'S
        NUMBERS, in whatever exact form the declaration presents them, and are
        checked at ``eps_4``/``eps_2`` by Definition ``def:tolmap`` (iii).

        The absent entry is the exact integer ``0`` and not ``0.0``: (D2) makes
        it zero BY DEFINITION, so nothing about it is an evaluation.
        """
        return self.columns.get(column, {}).get(row, 0)

    def patterns(self) -> tuple[frozenset[int], ...]:
        """Return ``2^[K]``, ordered by cardinality then lexicographically."""
        ports = range(self.port_count)
        return tuple(
            frozenset(chosen)
            for size in range(self.port_count + 1)
            for chosen in combinations(ports, size)
        )

    def multiclick_patterns(self) -> tuple[frozenset[int], ...]:
        """Return ``MC_K`` -- Eq. ``eq:mcsc``."""
        return tuple(pattern for pattern in self.patterns() if len(pattern) >= 2)


def product_form(
    probabilities: Sequence[Scalar], route: DarkCountRoute | None = None
) -> DarkCountChannel:
    r"""Return the independent product form of Eq. ``eq:darkR``.

        R_{S|S'} = 1[S' subset of S] prod_{k in S \ S'} p_k
                   prod_{k not in S} (1 - p_k)

    Theorem ``thm:dark-counts`` (i) proves it satisfies (D1) and (D2), so for this
    route both are DERIVED rather than checked (Remark ``rem:corrdark``).

    **THE EVALUATION IS EXACT, AND THAT IS WHAT MAKES THEOREM ``thm:dark-counts`` (i)
    TRUE OF THE EMITTED MATRIX.** Every entry is computed in exact rational
    arithmetic from the declared probabilities, so every column sums to
    EXACTLY 1 and every entry is exactly the product Eq. ``eq:darkR`` writes.
    A float evaluation is not enough here: the products and complements round,
    and a column then sums to ``1 +/- O(2^-54)`` -- on a declaration as ordinary
    as ``p_dc = (1/10, 1/5)`` three of the four columns miss 1 by a few units in
    the last place. Definition ``def:darkadm`` says (D1) and (D2) hold "by
    construction" for Eq. ``eq:darkR``, and Remark ``rem:d2slack`` (b) makes
    ``delta_dc = 0`` on this route BECAUSE (D1) and (D2) are THEOREMS there and
    NOT TESTS, so there is no slack to carry. A matrix
    whose columns sum to 1 only to within a rounding error carries slack the
    module then declares to be zero, and no threshold of this contract stands
    behind it -- the generated route has none, by design.

    THE DECLARED PROBABILITY IS TAKEN AS THE EXACT NUMBER IT IS. A declared
    :class:`~fractions.Fraction` is used as it stands; a declared ``float`` is a
    binary64 value, hence a dyadic rational, and ``Fraction(x)`` NAMES that
    rational exactly -- there is nothing to round and no direction to round in.
    So no declaration loses anything by crossing into this function, and the
    exactness is a property of the arithmetic rather than of the presentation.

    THIS ROUTE ONLY. A DECLARED ``R`` is the declarer's own numbers and is not
    rebuilt, re-derived or repaired here; Definition ``def:tolmap`` (iii)
    decides it at ``eps_4`` and ``eps_2``, which is the whole difference
    between a matrix this contract CONSTRUCTS and one it is HANDED.
    """
    values = [Fraction(value) for value in probabilities]
    if any(not 0 <= value <= 1 for value in values):
        raise HypothesisError("a dark-count probability lies in [0, 1]")
    port_count = len(values)
    ports = range(port_count)
    all_patterns = [
        frozenset(chosen)
        for size in range(port_count + 1)
        for chosen in combinations(ports, size)
    ]
    columns: dict[frozenset[int], dict[frozenset[int], Scalar]] = {}
    for column in all_patterns:
        entries: dict[frozenset[int], Scalar] = {}
        for row in all_patterns:
            if not column <= row:
                continue
            weight = Fraction(1)
            for port in ports:
                if port in row - column:
                    weight *= values[port]
                elif port not in row:
                    weight *= 1 - values[port]
            if weight != 0:
                entries[row] = weight
        columns[column] = entries
    return DarkCountChannel(
        port_count=port_count,
        route=route if route is not None else DarkCountRoute.PER_PORT_PRODUCT_FORM,
        columns=columns,
    )


def check_dark_channel(
    channel: DarkCountChannel, tolerances: NumericalTolerances
) -> Refusal | None:
    """Return a refusal naming (D1) or (D2) -- Definition ``def:tolmap`` (iii).

    **THE ASSIGNMENT IS THE CONTRACT'S.** Definition ``def:tolmap`` (iii),
    whose content is Definition ``def:darktol``, for a DECLARED ``R``:

    * **(D1) column-stochasticity is decided at** ``eps_4`` -- admitted when
      ``R_{S|S'} >= -eps_4`` FOR EVERY ENTRY and
      ``|sum_S R_{S|S'} - 1| <= eps_4`` FOR EVERY COLUMN. TWO HALVES, and both
      are tested: a channel whose columns sum to 1 exactly can still fail the
      entrywise half, which an implementation testing only the sums would
      admit;
    * **(D2) monotonicity is decided at** ``eps_2`` -- AN ENTRY COUNTS AS
      POSITIVE WHEN ``R_{S|S'} > eps_2``, so the channel is refused EXACTLY WHEN
      some entry with ``S'`` not a subset of ``S`` EXCEEDS ``eps_2``. The
      comparison is STRICT: an entry sitting exactly at ``eps_2`` in a forbidden
      position is ADMITTED.

    Definition ``def:darktol`` gives the reason for each number: ``eps_4``
    bounds the completeness residual Eq. ``eq:res4``, which is the same kind of
    quantity as a column sum's defect from one; ``eps_2`` is the threshold at
    which the contract already calls a spectral quantity zero. In particular
    the entrywise half of (D1) is tested against ``eps_4``, not ``eps_2``.

    WHAT THE WIDENED ADMISSION COSTS IS NOT ABSORBED HERE. Proposition
    ``prop:dark-slack-bound`` carries it to Eq. ``eq:darkpmcslack`` through
    :func:`composition_correction` and :func:`capped_coefficient`, and the
    artifact emits both. Nothing is clamped, repaired or renormalized in this
    function: it either passes on the declared datum or refuses.

    ON THE GENERATED ROUTE NEITHER CONDITION IS A TEST: (D1) and (D2) are
    THEOREMS there (Theorem ``thm:dark-counts`` (i)), so there is no slack to
    carry and the correction is exactly 0 (Remark ``rem:d2slack`` (b)). **THIS
    FUNCTION IS REACHED ON THE DECLARED ROUTE ONLY**:
    :func:`certiqs_key.receiver.request._check_dark_counts` returns before
    calling it where no ``R`` was declared, so a product form is never tested
    here -- and none needs to be, since Eq. ``eq:darkR`` is evaluated exactly
    (:func:`product_form`) and its columns sum to exactly 1. It decides nothing
    about ``delta_dc`` either, which :func:`composition_correction` reads off
    the ROUTE.
    """
    for column in channel.patterns():
        entries = channel.columns.get(column, {})
        for row, value in entries.items():
            if value < -tolerances.eps_4:
                return Refusal(
                    DARK_CONDITION_REASONS["D1"],
                    f"(D1) R_{{{sorted(row)}|{sorted(column)}}} = {value} is "
                    f"below -eps_4 = {-tolerances.eps_4}; Def. def:tolmap (iii) "
                    f"admits an entry only at or above -eps_4",
                )
            if value > tolerances.eps_2 and not column <= row:
                return Refusal(
                    DARK_CONDITION_REASONS["D2"],
                    f"(D2) R_{{{sorted(row)}|{sorted(column)}}} = {value} "
                    f"exceeds the declared eps_2 = {tolerances.eps_2} although "
                    f"{sorted(column)} is not a subset of {sorted(row)}: a dark "
                    f"count ADDS a click and never removes one",
                )
        total = sum(entries.values())
        # THE COLUMN-SUM HALF, WRITTEN AS ITS TWO SIDES. Def. def:darktol (the
        # content of def:tolmap (iii)) states it as |sum - 1| <= eps_4, and its
        # lead-in READS THE TWO SIDES SEPARATELY BY NAME -- "the lower side of
        # (D1)'s column sum" with the upper side of (D2)'s entry bound gives
        # eq:d2slack, "the upper side of (D1)'s column sum permits r_min > 1"
        # (eq:rminupper). The pair `1 - eps_4 <= sum <= 1 + eps_4`
        # is the same exact condition and is the form that decides a column
        # sitting EXACTLY on either boundary the way the exact condition does:
        # under Def. def:evaluation-model `abs(0.999 - 1.0)` evaluates one ulp ABOVE the
        # declared 0.001 while `0.999 >= 1.0 - 0.001` holds with equality, and
        # the contract admits that channel (Rem. rem:d2slack's own witness).
        if not 1.0 - tolerances.eps_4 <= total <= 1.0 + tolerances.eps_4:
            return Refusal(
                DARK_CONDITION_REASONS["D1"],
                f"(D1) column {sorted(column)} sums to {total}, outside "
                f"[1 - eps_4, 1 + eps_4] = "
                f"[{1.0 - tolerances.eps_4}, {1.0 + tolerances.eps_4}]",
            )
    return None


def check_dark_count_source(
    declared_channel: DarkCountChannel | None,
    per_port_probabilities: Sequence[Scalar],
) -> Refusal | None:
    """Refuse a request that supplies BOTH a declared ``R`` and dark counts.

    **THE CONTRACT'S OWN RULE, WITH ITS OWN REASON STRING.** Requirement
    ``req:dark-route-exclusive``: THE TWO ROUTES ARE EXCLUSIVE, and a request
    declaring ``R`` while some ``p_dc|k`` is non-zero is REFUSED with
    ``dark_count_channel_declared_twice``; its lead-in gives the reason -- the
    request would supply the channel twice with no rule that makes the two
    agree, and the record of which route the emitted ``R`` came from (Remark
    ``rem:corrdark``, Requirement ``req:dark-channel-record``) PRESUPPOSES THAT
    EXACTLY ONE WAS TAKEN. ``interface.yaml`` ``inputs.dark_count_channel``
    states the same rule, and the refusal rules give it the reason string.

    THE CONVERSE IS FIXED TOO (``inputs.dark_count_channel``): a declared ``R``
    requires ``p_dc|k = 0`` for every ``k``, so a declared ``R`` beside
    all-zero per-port probabilities is ADMITTED and takes the declared route;
    and a per-port form with no declared ``R`` takes the generated one.

    **THE CONDITION IS DECIDED ON THE DECLARED VALUE, AND NO THRESHOLD
    DECIDES IT.** Some ``p_dc|k`` being non-zero is an EXACT statement about
    declared data, and Definition ``def:tolmap`` -- which fixes every
    condition this contract decides under a threshold, each decided by a
    declared number "and by no other threshold" -- does not list this one: its
    closing enumeration classes the exclusivity of the two dark-count routes
    as kind (b), a combinatorial predicate on the declaration. So it is decided
    by no threshold at all, and the comparison is ``value != 0`` against the
    declared number itself.

    DECIDING IT THROUGH ``to_float`` SUPPLIED ONE ANYWAY, and it failed OPEN:
    an exactly non-zero declared probability below the binary64 underflow
    point converts to ``0.0``, so a request declaring an explicit ``R``
    beside ``p_dc = (1/10^400, 0)`` was ADMITTED where the contract refuses
    it with the verbatim ``dark_count_channel_declared_twice``. The window is
    physically empty and nothing unchecked was emitted -- the declared ``R``
    is still checked at ``eps_4``/``eps_2`` -- but a contract-verbatim refusal
    on an exact condition may not turn on a representation limit.

    THE DETAIL PRINTS THE DECLARED VALUE AS DECLARED, for the same reason:
    converting it for the message would print ``0.0`` as the offending datum
    in exactly the case a conversion would miss, so the refusal would
    contradict its own explanation. A ``Fraction`` renders as ``n/d`` and a
    ``float`` as itself -- each in the presentation the declaration used.
    """
    if declared_channel is None:
        return None
    nonzero = [
        (index, value)
        for index, value in enumerate(per_port_probabilities)
        if value != 0
    ]
    if not nonzero:
        return None
    return Refusal(
        RefusalReason.DARK_COUNT_CHANNEL_DECLARED_TWICE,
        f"the request declares an explicit dark_count_channel while the "
        f"detector_layer carries non-zero dark-count probabilities "
        f"{[f'p_dc|{index} = {value}' for index, value in nonzero]}; the inputs "
        f"table and Req. req:dark-route-exclusive make the two routes "
        f"exclusive, and a declared R requires p_dc|k = 0 for every k",
    )


def multiclick_mass(channel: DarkCountChannel, column: frozenset[int]) -> Scalar:
    """Return ``R_{MC|S'}``, the multiclick mass of one column.

    EVALUATED IN THE SUBSTRATE THE ENTRIES ARE IN, and nothing is converted
    here: on the generated route the entries are exact rationals, so this sum
    is exact and a multiclick column's mass is exactly 1 as
    Theorem ``thm:dark-counts`` (iii) states rather than 1 to within a rounding
    error. A caller that needs a machine number applies
    :func:`~certiqs_key.receiver.numerics.to_float` at ITS OWN site: the
    conversion belongs where the float is consumed and never where the value
    is produced, or the exactness this route is built for is lost one call
    before it is used.
    """
    total: Scalar = 0
    for row in channel.multiclick_patterns():
        total = total + channel.entry(row, column)
    return total


def minimum_multiclick_mass(channel: DarkCountChannel) -> Scalar:
    """Return ``r_min`` of Eq. ``eq:rmin`` -- Theorem ``thm:dark-counts`` (iv).

    The minimum runs over EVERY non-multiclick column, THE NO-CLICK COLUMN
    INCLUDED. Remark ``rem:rmintrap`` is why, and its Eq. ``eq:rmintrapnum``
    is the number an implementation that computed this over the single-click
    columns alone gets wrong.

    THE MINIMUM IS TAKEN IN THE ENTRIES' OWN SUBSTRATE, so on the generated
    route ``r_min`` is the exact rational Eq. ``eq:rmin`` defines and the
    comparison that selects it is exact -- which is what ``interface.yaml``
    ``outputs.dark_count_channel`` asks for when it emits ``r_min`` EXACTLY AS
    Eq. ``eq:rmin`` COMPUTES IT.
    """
    multiclick = set(channel.multiclick_patterns())
    columns = [column for column in channel.patterns() if column not in multiclick]
    return min(multiclick_mass(channel, column) for column in columns)


def capped_coefficient(minimum_mass: Scalar) -> Scalar:
    """Return ``rbar = min{r_min, 1}`` -- Eq. ``eq:rbar``.

    A COEFFICIENT, NEVER A CLAMP. Requirement ``req:dark-channel-record``:
    nothing is clamped -- ``R`` is emitted as declared and ``r_min`` as
    Eq. ``eq:rmin`` computes it. Remark ``rem:d2slack`` (d): ``rbar`` is a
    SEPARATE NAMED SCALAR appearing as a COEFFICIENT IN A STATED INEQUALITY;
    lowering that coefficient WEAKENS the bound, and needs nothing beyond
    ``id - M_MC >= 0``; no claim is made that ``rbar`` approximates ``r_min``
    or any exact quantity.

    THE CAP IS ONE-SIDED AND IS NOT FLOORED AT ZERO. A negative ``r_min`` gives
    a negative ``rbar``, and that is admissible: in the proof of Proposition
    ``prop:dark-slack-bound`` no step uses a bound on ``r_min`` from either
    side, and no step uses the sign of ``r_min`` or of ``rbar``. Its cost is
    bounded by Eq. ``eq:rbarcost``, ``0 <= r_min - rbar <= (K + 2) eps_4``.

    THE COMPARISON IS EXACT AND THE CAP IS THE EXACT INTEGER ``1``: where
    ``r_min`` is an exact rational so is the returned ``rbar``, and where
    ``r_min <= 1`` the value is returned UNCHANGED rather than re-presented
    in another substrate.
    """
    return min(minimum_mass, 1)


def composition_correction(
    route: DarkCountRoute, port_count: int, tolerances: NumericalTolerances
) -> float:
    """Return ``delta_dc`` of Eq. ``eq:darkdelta`` -- BY ROUTE, not by channel.

        delta_dc = 0                      generated route (Eq. eq:darkR)
        delta_dc = eps_4 + (K + 1) eps_2  declared route (def:tolmap (iii))

    The two cases are the two routes of Definition ``def:darkadm`` (Proposition
    ``prop:dark-slack-bound``), and the artifact carries the value of the route
    it took. On the generated route (D1) and (D2) are THEOREMS (Theorem
    ``thm:dark-counts`` (i)) and not tests, so there is no slack to carry and
    the correction is exactly 0 (Remark ``rem:d2slack`` (b)).

    THE DECLARED VALUE DOES NOT DEPEND ON HOW MUCH SLACK THE CHANNEL ACTUALLY
    USED. It is derived at Eq. ``eq:d2slack`` from the LOWER side of (D1)'s
    column sum and the UPPER side of (D2)'s entry bound, the ``K + 1`` counting
    the rows ``S`` with ``|S| <= 1``, none of which contains an ``S'`` in
    ``MC_K``. A channel occupying no (D2)-forbidden position at all still
    carries the ``(K + 1) eps_2`` term.
    """
    if route is DarkCountRoute.PER_PORT_PRODUCT_FORM:
        return 0.0
    return tolerances.eps_4 + (port_count + 1) * tolerances.eps_2


def improved_bound(minimum_mass: Scalar, weight: float) -> float:
    """Return ``(1 - r_min) p_mc + r_min`` -- Eq. ``eq:darkpmc``.

    Theorem ``thm:dark-counts`` (iv), the EXACTLY-ADMISSIBLE form, whose final
    comparison is ``(1 - r_min) p_mc + r_min - p_mc = r_min (1 - p_mc) >= 0``
    since ``p_mc <= 1``.

    **THIS IS NOT THE INEQUALITY A CONSUMER COMPOSES WITH.** Requirement
    ``req:dark-channel-record`` and Remark ``rem:d2slack`` name
    Eq. ``eq:darkpmcslack`` -- :func:`composed_slack` -- and the remark says
    what using this one instead costs: Eq. ``eq:darkoverstate``, first order in
    the receiver tolerances and in the UNSAFE direction. It is kept because on
    the generated route the two coincide -- ``delta_dc = 0`` and ``r_min <= 1``,
    so ``rbar = r_min`` and Eq. ``eq:darkpmcslack`` IS Eq. ``eq:darkpmc``
    (Remark ``rem:d2slack`` (e)) -- and because :func:`overstatement` is the
    difference of the two. Like it, this is offered and never applied to an
    emitted ``p_mc``.

    ``r_min`` may be exact and ``p_mc`` is a floating-point evaluation
    (Definition ``def:evaluation-model``), so their composition is one and
    :func:`~certiqs_key.receiver.numerics.to_float` is applied HERE, at the
    consumer of the value.
    """
    mass = to_float(minimum_mass)
    return (1.0 - mass) * weight + mass


def composed_slack(weight: float, capped: Scalar, correction: float) -> float:
    """Return ``(1 - rbar) p_mc + rbar - delta_dc`` -- Eq. ``eq:darkpmcslack``.

    THE INEQUALITY A CONSUMER COMPOSES WITH (``interface.yaml``
    ``outputs.dark_count_channel`` and ``outputs.high_photon_bounds``;
    Proposition ``prop:dark-slack-bound``): whenever
    ``blk M^{(>N)}_{MC} >= p_mc id^{(>N)}``,

        blk Mtilde^{(>N)}_{MC} >= ((1 - rbar) p_mc + rbar - delta_dc) id^{(>N)}

    for every ``R`` admitted under Definition ``def:tolmap`` (iii), "on either
    side of either test and whatever the sign of" ``r_min``. The step that
    needs ``rbar`` rather than ``r_min`` is the substitution, where
    ``1 - rbar >= 0`` BY CONSTRUCTION of Eq. ``eq:rbar``.

    THE RESULT IS NOT CLAMPED INTO ``[0, 1]`` AND IS NOT RAISED TO ``p_mc``. On
    an admitted declared channel whose slack costs more than its dark counts
    gain the composed value sits BELOW ``p_mc``, and the contract says the two
    emitted numbers say so (Remark ``rem:d2slack`` (e)); clamping it up would
    assert a bound the widened hypotheses do not support.

    ``rbar`` may be exact and ``p_mc`` is not, so the composed value is a
    floating-point one and :func:`~certiqs_key.receiver.numerics.to_float` is
    applied HERE rather than where ``rbar`` was produced.
    """
    coefficient = to_float(capped)
    return (1.0 - coefficient) * weight + coefficient - correction


def overstatement(
    minimum_mass: Scalar, capped: Scalar, correction: float, weight: float
) -> float:
    """Return ``(r_min - rbar)(1 - p_mc) + delta_dc`` -- Eq. ``eq:darkoverstate``.

    What a consumer that used Eq. ``eq:darkpmc`` in place of
    Eq. ``eq:darkpmcslack`` would overstate by (Remark ``rem:d2slack`` (e)):
    first order in the receiver tolerances and in the UNSAFE direction -- a (D2)
    violation is precisely weight moved out of ``MC_K``, and ``r_min > 1`` is
    multiclick mass the column arithmetic does not have. It is exactly
    :func:`improved_bound` minus :func:`composed_slack`.
    """
    gap = to_float(minimum_mass) - to_float(capped)
    return gap * (1.0 - weight) + correction


def improves_on_weight(capped: Scalar, correction: float, weight: float) -> bool:
    """Return whether Eq. ``eq:darkpmcslack`` improves on the bare ``p_mc``.

    Remark ``rem:d2slack`` (e): Eq. ``eq:darkpmcslack`` improves on ``p_mc`` --
    which is the point of Theorem ``thm:dark-counts`` (iv) -- ONLY WHERE
    ``rbar (1 - p_mc) >= delta_dc``; below that threshold the declared
    channel's admitted slack costs more than its dark counts gain, and the two
    emitted numbers say so. A consumer should not have to derive that.
    """
    return to_float(capped) * (1.0 - weight) >= correction


def compose_blocks(
    channel: DarkCountChannel, blocks: Mapping[frozenset[int], Matrix]
) -> dict[frozenset[int], Matrix]:
    """Return ``Mtilde_S = sum_{S'} R_{S|S'} M_{S'}`` -- Thm. ``thm:dark-counts`` (ii).

    ``R`` acts on the outcome label alone: it commutes with every operation on
    the optical modes, so the composition is a scalar recombination of blocks
    and the POVM and block structure survive it unchanged.
    """
    shapes = {matrix.shape for matrix in blocks.values()}
    if len(shapes) != 1:
        raise HypothesisError("the composed blocks must share one shape")
    shape = shapes.pop()
    composed: dict[frozenset[int], Matrix] = {}
    for row in channel.patterns():
        total = np.zeros(shape, dtype=np.complex128)
        for column, matrix in blocks.items():
            entry = channel.entry(row, column)
            if entry != 0:
                # to_float AT THE CONSUMER: the blocks are complex128 under
                # Definition def:evaluation-model, so the coefficient becomes a machine
                # number exactly here, where it meets one.
                total = total + to_float(entry) * matrix
        composed[row] = np.asarray(total, dtype=np.complex128)
    return composed
