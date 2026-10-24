"""The run tier's plausibility check: no entropy bound above what a key can carry.

WHY THIS EXISTS
===============
A key-rate regression hunt found an OVERSTATED key: decoy BB84 at photon cutoff 2 and
half-wave angle 1/7 reported ``h_low = 3.06`` bits per round on a one-bit key, where the
ideal on-grid device gives 0.096. Round-down-and-place had rounded the
measurement to a degenerate family, so the declared model contradicted the
honest statistics, and nothing caught it: the tests asserted statuses and
record shapes, and ``meat-core`` has no reason to refuse a large value, which
its objective admits (``meat-core/prop:value-range`` (iii): no finite a-priori
ceiling on ``h_low``). This module is the check; the canaries are
``tests/integration/test_key_rate_canaries.py``.

A second case: an honest table measured on a
real device against idealised stations contradicted the declared model by a
moderate amount. The check refused most alphas of an outer search, but its
absolute slack let one through, the search chose it, and the run ended with a
key six times too large. So a proved contradiction refuses a searched run as
a whole (:mod:`certiqs_key.runs.alpha_search`), the
comparison is exact where the number is certified and relative to the ceiling
otherwise, and the record stores the objective's split. Its canaries are
``tests/integration/test_contradictory_statistics_canaries.py``.

THE CEILING, AND WHERE EACH STEP OF IT IS STATED
================================================
``h_low`` is a rate PER ROUND, over all ``n`` rounds, sifted-out rounds
included: the key length is ``n h_low`` less the deductions
(``meat-core/thm:keylength``, Eq. ``eq:keylength``;
:mod:`certiqs_key.meat_core.finitekey.keylength`, ``rounds * h_low``), and the
objective is a sum over the whole acceptance alphabet ``Chat`` of a per-round
frequency vector ``q`` (``meat-core/def:feasible``, Eq. ``eq:objective``),
whose entropy terms sit on the key-live values ``Chat_key`` alone
(``meat-core/def:declaration``, Eq. ``eq:chkey``). The proof of
``prop:value-range`` (i) rewrites it as

    O_alpha(q, w) = alpha/(alpha-1) D(q || Phi[w]) + sum_{c in Chat_key} q(c) e_c(w),

and ``prop:value-range`` (ii) bounds each entropy term:
``e_c(w) <= log2 |Z_perp| = log2(d_Z + 1)``, the key alphabet ``Z`` of
``d_Z = key_value_count`` values together with the sifting symbol. With

    C := log2(d_Z + 1) max_{q in Gamma} q(Chat_key),

``max_{q in Gamma} q(Chat_key)`` is the largest probability, over the
acceptance set ``Gamma``, that a round is a key-live round: the sum of the
frequencies on ``Chat_key`` for a singleton set, an exact linear program over
the declared polytope otherwise (:func:`~certiqs_key.meat_core.acceptance.
geometry.acceptance_minimum`), rounded UP to a machine number.

``log2(d_Z + 1)`` and not ``log2 d_Z``: a key-live value may also be reached by
a class that fails sifting (Eq. ``eq:chkey`` asks for SOME passing class), so
the claims bound the entropy term by the size of ``Z_perp``. For a one-bit key
the ceiling is ``log2 3 = 1.585`` bits per key-live round, which the hunt's
3.06 bits per round exceeds at every key-round probability.

A BOUND ABOVE THE CEILING PROVES A CONTRADICTION, AND IT DOES NOT DEPEND ON ALPHA
================================================================================
Write ``D_min := inf { D(q || Phi[w]) : q in Gamma, w in Feas }``, the least
divergence between an accepted statistic and the statistics of a feasible
state (``foundations/def:kl``; ``meat-core/def:feasible``). Take any pair
``(q, w)`` in ``Gamma x Feas`` with ``D(q || Phi[w])`` finite. Then ``q`` is
absolutely continuous with respect to ``Phi[w]``, so every ``c`` with
``q(c) > 0`` has ``P_c(w) > 0`` and ``prop:value-range`` (ii) gives
``e_c(w) <= log2(d_Z + 1)``; a ``c`` with ``q(c) = 0`` adds nothing. With
the decomposition of (i),

    O_alpha(q, w) <= alpha/(alpha-1) D(q || Phi[w]) + log2(d_Z + 1) q(Chat_key)
                  <= alpha/(alpha-1) D(q || Phi[w]) + C.

``h_low`` is the infimum of ``O_alpha`` over ``Gamma x Feas``
(``eq:hlow-def``), so taking the infimum of the right-hand side over the pairs
with finite divergence,

    h_low <= alpha/(alpha-1) D_min + C.

(Where no pair has a finite divergence, ``D_min = +inf`` and the inequality
holds trivially; ``h_low = +inf`` there, ``prop:value-range`` (iv), is
``meat-core``'s own gate and is not compared here.) Every bound this check
compares is at most ``h_low`` in exact arithmetic: ``h_lb``
(``meat-core/frank-wolfe/thm:firstorder``), ``h_lb_dropped <= h_low^D <=
h_low`` (``cor:fo-dropped``, ``meat-core/prop:drop-bound``), and the certified
number ``h_cert`` (``frank-wolfe/cor:certified-keylength`` (i), (iii)). So a
bound ``b > C`` gives ``alpha/(alpha-1) D_min >= h_low - C >= b - C > 0``,
and since ``alpha/(alpha-1) > 0`` for ``alpha > 1``,

    D_min > 0:

NO feasible state reproduces ANY accepted statistic (``D(q || Phi[w]) = 0``
exactly when ``q = Phi[w]``, ``foundations/def:kl``). The bound is still
correct for the declared model, but the protocol accepted statistics that
model cannot produce, so the model is refuted by the data and the key has no
warrant for the device; it is bought by the divergence penalty, which
``prop:value-range`` (iii) leaves unbounded and which grows like
``alpha/(alpha-1)`` as ``alpha -> 1``.

``D_min`` reads ``Gamma``, ``Feas`` and ``Phi`` only, and none of them depends
on alpha: the acceptance set is built from the honest law, ``n``, the
completeness budget and the endpoint rule, and ``Feas`` and ``Phi`` are the
compiled declaration's. So one alpha's proof is a fact about the declaration
and the data that holds at every alpha, and an outer search refuses the run as
a whole at the first one (:mod:`certiqs_key.runs.alpha_search`, "A PROVED
CONTRADICTION REFUSES THE RUN"). The declaration in question is the one the
compared number is formed on: the searched declaration, or the reference
companion where its bracket counts, which reads the run's acceptance set too
(``frank-wolfe/cor:fo-reference``).

WHICH NUMBER IS COMPARED, AND HOW
=================================
The number the key length is formed from, never the estimate. ``h_low``
bounds the true value from ABOVE (``meat-core/lem:estimate``): on an honest
run stopped before it converged, its divergence term can still put it above
``C``, and refusing on it would refuse an honest run at a small budget. It is
recorded beside the bound.

EXACT, where the run is reported at the certified tier (its reason code
``certified_reported``): its key length is formed from ``h_cert``, computed
exactly (``frank-wolfe/req:certified-evaluation`` (vi)), and the record's
``certified_bound`` is ``h_cert`` rounded toward
``-inf``, a certified lower end. It is compared against an UPPER bound on
``C``: ``log2(d_Z + 1)`` and its product with the key-live mass (already
rounded up) enclosed in python-flint balls, the upper end taken
(:func:`certiqs_key.foundations.balls.upper`) and rounded up to a machine
number (:func:`ceiling_upper`). No slack: ``lower end > upper bound`` proves
``h_cert > C`` and so ``D_min > 0``. The library is loaded only here, where
the certified evaluation has already loaded it, so a run with the evaluation
off never loads it.

RELATIVE, otherwise (first-order: the evaluation off, unavailable or not
covering the run, or a length withheld): the binary64 ``h_lb`` (or
``h_lb_dropped``) against ``C`` rounded up in binary64 (two ulps above the
binary64 product, which covers ``log2``'s and the product's rounding) plus
:data:`RELATIVE_SLACK` times that. ``h_lb <= h_low`` is an exact-arithmetic
consequence, not a binary64 invariant (``frank-wolfe/rem:fo-arithmetic``), so
a slack is needed, and its job is that an HONEST run is never refused.

THE SLACK, 2^-10 OF THE CEILING
-------------------------------
What it must cover is the binary64 bound's excess over the exact one at the
same points. That excess is not relative to ``C``. Over every evaluation of
the five reproduction cases, the binary64 ``h_lb``
exceeds the certified number at the same points by at most 4.3e-5 ``C``: the
consistent control ``g1`` (key-live mass 4.6e-7, ``C = 7.3e-7``) by 3.1e-11 at
``alpha - 1 = 1e-5``, 3.9e-12 at 7.6e-5 and 4.8e-13 at 5.7e-4, roughly
``alpha/(alpha-1)`` times a few 1e-16, as the penalty's rounding scaled by its
factor would be. Two things stand between such an error and a refusal of an
honest run:

* THE HONEST MARGIN. Where every class that reaches a key-live value passes
  sifting, the sifting symbol is not in the support of that branch's key, the
  proof of ``prop:value-range`` (ii) bounds its entropy term by ``log2 d_Z``,
  and an honest run has ``h_low <= log2(d_Z) q(Chat_key)``: below ``C`` by
  ``1 - log2 d_Z / log2(d_Z + 1)`` of it, 37 % for a one-bit key (``log2 2``
  against ``log2 3``), 14 % at ``d_Z = 4`` and still 0.07 % at
  ``d_Z = 256``. (The consistent cases' entropy terms carry at most 0.575
  ``C``.) Where a failing class reaches a key-live value, there is no such
  margin.
* THE SLACK, ``2^-10 C``, about 0.1 % of the ceiling: over twenty times the
  largest excess measured, at the search's lowest alpha on the smallest
  key-live mass measured, with no honest margin counted. What it costs is
  detection of a contradiction whose penalty adds less than 0.1 % of ``C``,
  which the ceiling cannot see anyway: its own looseness (the margin above)
  hides far more, and a tighter ceiling is left to a separate piece of work.

It is a judgement in binary64, not a proof, and the record says so
(``comparison: relative``, with the slack). An honest run whose bound came
within ``2^-10 C`` of the ceiling with an error beyond that would need a
key-live probability per round far below the measured 4.6e-7 at an alpha
near ``1 + 1e-5`` AND entropy terms near ``log2(d_Z + 1)``; the certified
tier compares exactly and does not depend on the slack at all.

Where the acceptance set gives the key-live values no mass, ``C = 0`` and the
slack is zero too: there every positive bound is refused, and the declaration
produces no key in either case.

THE OBJECTIVE'S SPLIT, A DIAGNOSTIC
===================================
The record also stores the two parts of (i) at the returned point, the one
``h_low`` is the objective at (:func:`objective_split`): the divergence
penalty ``alpha/(alpha-1) D(q_t || Phi[w_t])`` and the entropy terms
``sum_{c in Chat_key} q_t(c) e_c(w_t)``, both binary64, and the penalty's
share of their sum. They are read off the result's own fields (``optimized_q``
is ``q_t``, ``predicted_statistics`` is ``Phi[w_t]`` and
``block_contributions`` the deficits ``K_c - P_c``), with no new solve. The
split decides nothing, refuses nothing and changes no number. A contradiction
shows a penalty share near 1 at every alpha (the reproduction's refused
cases); an honest run a small one where it converged, but also a large one
where its estimate did not (the consistent control ``g1``: 0.96 at
``alpha - 1 = 1e-5``, 0.03 at 5.7e-4), which is one reason it decides
nothing.

THE RUN TIER'S, NOT ``meat-core``'s
===================================
This is a check of a result against its own declaration, not a claim: it adds
no bound, moves no number and narrows nothing a theorem says. It reads
``prop:value-range`` and refuses where a run contradicts it, which is the run
tier's business (spec/architecture.md 3.3, the order and the record); the
refusal is carried as data under the run tier's own code
(:class:`~certiqs_key.runs.errors.RunRefusalReason`), with both numbers in the
record.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Final

from certiqs_key.meat_core.acceptance.geometry import (
    POLYTOPE,
    acceptance_minimum,
    float_above,
)
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.objective.branch import key_live_values
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    CERTIFIED_REASON,
    GeneralKeyRateResult,
)

__all__ = [
    "EXACT",
    "RELATIVE",
    "RELATIVE_SLACK",
    "PlausibilityCheck",
    "ceiling_upper",
    "general_key_live_values",
    "key_live_mass",
    "objective_split",
    "plausibility_check",
]

#: The slack of the binary64 comparison, as a multiple of the ceiling rounded
#: up: ``2^-10``. See the module docstring, "THE SLACK".
RELATIVE_SLACK: Final[float] = 2.0**-10

#: ``comparison`` where a certified number's lower end is compared exactly.
EXACT: Final[str] = "exact"
#: ``comparison`` where the binary64 bound is compared with the relative slack.
RELATIVE: Final[str] = "relative"

#: The working precision of the ceiling's enclosure, in bits: the certified
#: evaluation's own (``frank-wolfe/req:certified-evaluation`` (v)).
_PRECISION: Final[int] = 128

#: The rule as the record states it.
RULE: Final[str] = (
    "bound <= log2(key_value_count + 1) * max_{q in acceptance set} "
    "q(key-live values) (meat-core/prop:value-range (i)-(ii)); compared exactly "
    "where the key length is formed from the certified number (its lower end "
    "against the ceiling rounded up, no slack), otherwise the binary64 bound "
    "against the ceiling rounded up plus relative_slack times it"
)


@dataclass(frozen=True)
class PlausibilityCheck:
    """One run's bound held against the ceiling of ``meat-core/prop:value-range``."""

    #: ``h_cert`` where the key length is formed from the certified number,
    #: else ``h_lb``, or ``h_lb_dropped`` where the run reported a dropped set:
    #: the name of the number the key length is formed from.
    bound_name: str
    #: Its value, bits per round (``h_cert``'s lower end); ``None`` where no
    #: bound was reported.
    bound: float | None
    #: The estimate, bits per round, recorded beside the bound and not compared.
    h_low: float
    #: ``d_Z``, the number of raw key values.
    key_value_count: int
    #: ``Chat_key``, in the declared order.
    key_live_values: tuple[str, ...]
    #: ``max_{q in Gamma} q(Chat_key)``, rounded up.
    key_live_mass: float
    #: ``log2(d_Z + 1) * key_live_mass`` in binary64, bits per round.
    ceiling: float
    #: The ceiling rounded up (:func:`ceiling_upper`): what the bound is
    #: compared against, the slack added on the relative comparison.
    ceiling_upper: float
    #: :data:`EXACT` or :data:`RELATIVE` (module docstring).
    comparison: str = RELATIVE
    #: The first-order number, ``h_lb`` or ``h_lb_dropped``, beside a certified
    #: bound; equal to ``bound`` on the relative comparison.
    first_order_bound: float | None = None
    #: :func:`objective_split` at the returned point, or ``None``. Decides
    #: nothing.
    objective_split: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        """Reject a comparison this module does not make."""
        if self.comparison not in (EXACT, RELATIVE):
            raise ValueError(f"comparison is {EXACT!r} or {RELATIVE!r}")

    @property
    def relative_slack(self) -> float:
        """``0`` on the exact comparison, :data:`RELATIVE_SLACK` on the other."""
        return 0.0 if self.comparison == EXACT else RELATIVE_SLACK

    @property
    def slack(self) -> float:
        """The slack in bits per round: ``relative_slack * ceiling_upper``."""
        return self.relative_slack * self.ceiling_upper

    @property
    def threshold(self) -> float:
        """What the bound must exceed to be refused: ``ceiling_upper + slack``."""
        return self.ceiling_upper + self.slack

    @property
    def compared(self) -> bool:
        """Whether a finite bound was compared (an infinite estimate is not)."""
        return (
            self.bound is not None
            and math.isfinite(self.bound)
            and not math.isinf(self.h_low)
        )

    @property
    def exceeded(self) -> bool:
        """Whether the bound lies above the threshold."""
        return (
            self.compared and self.bound is not None and self.bound > self.threshold
        )

    def as_record(self) -> dict[str, Any]:
        """JSON-ready: the numbers, the ceiling's factors, how compared, the verdict."""
        return {
            "bound_name": self.bound_name,
            "bound": self.bound,
            "first_order_bound": self.first_order_bound,
            "h_low": None if math.isinf(self.h_low) else self.h_low,
            "h_low_is_infinite": math.isinf(self.h_low),
            "ceiling": self.ceiling,
            "ceiling_upper": self.ceiling_upper,
            "key_value_count": self.key_value_count,
            "key_alphabet_with_sifting_symbol": self.key_value_count + 1,
            "key_live_values": list(self.key_live_values),
            "key_live_mass": self.key_live_mass,
            "comparison": self.comparison,
            "relative_slack": self.relative_slack,
            "slack": self.slack,
            "threshold": self.threshold,
            "compared": self.compared,
            "exceeded": self.exceeded,
            "objective_split": (
                None if self.objective_split is None else dict(self.objective_split)
            ),
            "rule": RULE,
        }

    def detail(self) -> str:
        """Return the refusal's detail: the contradiction in words, then numbers."""
        how = (
            "compared exactly: the certified number's lower end against the "
            "ceiling rounded up, with no slack"
            if self.comparison == EXACT
            else "compared in binary64, with a slack of "
            f"{self.relative_slack:g} times the ceiling for the bound's rounding"
        )
        return (
            "the accepted statistics contradict the declared model: no feasible "
            "state of it reproduces any accepted statistic, so a key has no "
            "warrant for this device. The entropy bound "
            f"{self.bound_name} = {self.bound!r} bits per round exceeds the "
            f"ceiling {self.ceiling_upper!r} = log2({self.key_value_count} + 1) x "
            f"{self.key_live_mass!r} (rounded up), the most the entropy terms can "
            "carry when a round is key-live with probability at most "
            f"{self.key_live_mass!r} over the acceptance set "
            "(meat-core/prop:value-range (ii)); the bound is at most h_low, and "
            "h_low at most alpha/(alpha-1) D_min plus that ceiling "
            "(prop:value-range (i)-(ii)), so D_min, the least divergence between "
            "an accepted statistic and the statistics of a feasible state, is "
            f"positive, and it does not depend on alpha ({how}; "
            f"h_low = {self.h_low!r})"
        )


def general_key_live_values(declaration: GeneralDeclaration) -> tuple[str, ...]:
    """Return ``Chat_key`` of Eq. ``eq:chkey`` for a general declaration.

    The values to which some outcome pair whose class passes sifting maps
    (sifting is announcement-determined, ``def:admissible-declaration`` (v)),
    in the declared order: the reading
    :func:`~certiqs_key.meat_core.objective.joint.build_joint_maps` makes.
    """
    live = {
        declaration.acceptance_value(x, v)
        for x in declaration.alice_alphabet
        for v in declaration.bob_outcomes
        if declaration.raw_key(x, v) is not None
    }
    return tuple(c for c in declaration.acceptance_values if c in live)


def key_live_mass(
    acceptance: AcceptanceSet,
    acceptance_values: tuple[str, ...],
    live: tuple[str, ...],
) -> float:
    """Return ``max_{q in Gamma} q(Chat_key)``, exactly and then rounded up.

    A singleton set sums its frequencies on ``live``; a polytope solves the
    exact linear program of :func:`acceptance_minimum` with ``-1`` on ``live``.
    Where that program has no optimum (an empty set), ``1``: the trivial bound
    on a probability, which keeps the ceiling a ceiling. Never above ``1``.
    """
    chosen = set(live)
    exact: Fraction
    if acceptance.geometry == POLYTOPE and acceptance.polytope is not None:
        surrogate = [-1.0 if c in chosen else 0.0 for c in acceptance_values]
        optimum = acceptance_minimum(surrogate, acceptance.polytope)
        exact = Fraction(1) if optimum is None else -optimum.minimum
    else:
        exact = sum(
            (
                Fraction(frequency)
                for c, frequency in zip(
                    acceptance_values, acceptance.frequencies, strict=True
                )
                if c in chosen
            ),
            Fraction(0),
        )
    exact = min(max(exact, Fraction(0)), Fraction(1))
    rounded = float_above(exact)
    return 1.0 if rounded is None else min(rounded, 1.0)


def ceiling_upper(key_value_count: int, mass: float, *, rigorous: bool) -> float:
    """Return ``log2(key_value_count + 1) * mass`` rounded up to a machine number.

    ``rigorous``: enclosed in python-flint balls at 128 bits, the upper end
    taken and rounded up (module docstring, "EXACT"), so the result is at
    least the real ceiling. Otherwise binary64, two ulps above the binary64
    product: not a proof, and needed by the relative comparison only, whose
    slack is far wider ("RELATIVE").
    """
    if rigorous:
        from certiqs_key.foundations import balls

        with balls.precision(_PRECISION):
            enclosure = (
                balls.real(key_value_count + 1).log()
                / balls.real(2).log()
                * balls.real(mass)
            )
            above = float_above(balls.upper(enclosure))
        if above is None:  # pragma: no cover - log2(d + 1) * mass is small
            return math.inf
        return above
    value = math.log2(key_value_count + 1) * mass
    return math.nextafter(math.nextafter(value, math.inf), math.inf)


def objective_split(
    key_rate: GeneralKeyRateResult, live: tuple[str, ...]
) -> dict[str, Any] | None:
    """Return the objective's two parts at the returned point, or ``None``.

    ``prop:value-range`` (i): ``alpha/(alpha-1) D(q_t || Phi[w_t])`` and
    ``sum_{c in Chat_key} q_t(c) e_c(w_t)`` with ``e_c = log2(P_c / K_c) /
    (alpha - 1)``, read off ``optimized_q`` (``q_t``), ``predicted_statistics``
    (``P``) and ``block_contributions`` (``K_c - P_c``, the dropped program's
    under a dropped set), in binary64, with the penalty's share of their sum.
    A DIAGNOSTIC (module docstring, "THE OBJECTIVE'S SPLIT"): ``None`` where
    ``h_low`` is infinite or a part is not finite.
    """
    if math.isinf(key_rate.h_low) or not key_rate.optimized_q:
        return None
    alpha = key_rate.alpha
    chosen = set(live)
    divergence = 0.0
    entropy = 0.0
    for c, weight in key_rate.optimized_q.items():
        if weight <= 0.0:
            continue
        p = key_rate.predicted_statistics.get(c)
        if p is None or p <= 0.0:
            return None
        divergence += weight * math.log2(weight / p)
        if c in chosen:
            k = p + sum(key_rate.block_contributions.get(c, {}).values())
            if k <= 0.0:
                return None
            entropy += weight * math.log2(p / k) / (alpha - 1.0)
    penalty = alpha / (alpha - 1.0) * divergence
    if not (math.isfinite(penalty) and math.isfinite(entropy)):
        return None
    total = penalty + entropy
    return {
        "divergence_penalty": penalty,
        "entropy_terms": entropy,
        "penalty_share": penalty / total if total > 0.0 else None,
        "at": "the returned point, where h_low is the objective",
        "rule": (
            "O_alpha(q, w) = alpha/(alpha-1) D(q || Phi[w]) + sum_{c key-live} "
            "q(c) e_c(w), e_c = log2(P_c / K_c)/(alpha - 1) (meat-core/"
            "prop:value-range (i)); a diagnostic that decides nothing"
        ),
    }


def plausibility_check(
    declaration: ProtocolDeclaration | GeneralDeclaration,
    key_rate: GeneralKeyRateResult,
) -> PlausibilityCheck:
    """Hold the run's bound against the ceiling of ``prop:value-range`` (ii).

    ``declaration`` is the one solved (read back off the bundle), so the
    acceptance set, the key alphabet and ``Chat_key`` are those the bound is
    about. The comparison is exact where the key length is formed from the
    certified number and relative otherwise. See the module docstring for the
    derivation.
    """
    if isinstance(declaration, GeneralDeclaration):
        live = general_key_live_values(declaration)
    else:
        live = key_live_values(declaration)
    mass = key_live_mass(
        declaration.acceptance_set, tuple(declaration.acceptance_values), live
    )
    count = declaration.key_value_count
    dropped = bool(key_rate.dropped_set)
    first_order = key_rate.h_lb_dropped if dropped else key_rate.h_lb
    recorded = (key_rate.certified or {}).get("certified_bound")
    certified_bound = None if recorded is None else float(recorded)
    # The key length is formed from the certified number exactly where the
    # result's reason code says so; the record holds that code and the
    # certified tier equal (GeneralKeyRateResult.__post_init__).
    exact = (
        key_rate.key_length_reason_code == CERTIFIED_REASON
        and certified_bound is not None
    )
    return PlausibilityCheck(
        bound_name="h_cert" if exact else "h_lb_dropped" if dropped else "h_lb",
        bound=certified_bound if exact else first_order,
        h_low=key_rate.h_low,
        key_value_count=count,
        key_live_values=live,
        key_live_mass=mass,
        ceiling=math.log2(count + 1) * mass,
        ceiling_upper=ceiling_upper(count, mass, rigorous=exact),
        comparison=EXACT if exact else RELATIVE,
        first_order_bound=first_order,
        objective_split=objective_split(key_rate, live),
    )
