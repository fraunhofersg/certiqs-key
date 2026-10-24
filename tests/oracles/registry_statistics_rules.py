"""The ``statistics`` endpoint-rule oracle registry -- hand-derived, frozen.

WHAT THIS FILE IS AND WHY IT IS NOT IN THE OTHER ONE.
``registry_statistics_acceptance.py`` is the original freeze: its cases
were derived by hand from ``statistics-acceptance`` 0.1.2 before its
implementation existed. It pins the exact binomial
quantile rule evaluated by the sweep, which is the default route and the only
route that contract had. TWO ROUTES ARE ADDED -- the Bernstein rule of
``binomial-box/prop:rule-bernstein`` and the local enclosure evaluation of
``binomial-box/prop:bracketed-endpoints`` -- and what pins them is: "new
small-n oracles pin the enclosure's bracket verdict and its equality with the
sweep where the bracket is decided". This file is those oracles. IT IS A PURE
INSERTION: not one entry, value or
derivation of the other registry is touched, and the conventions are that
file's, deliberately -- the same entry shape, the same admissibility rule, and
``KINDS`` and ``INADMISSIBLE_SOURCES`` imported from ``registry.py`` rather
than restated, so the three registries cannot drift on what an admissible
oracle is.

EVERY VALUE HERE WAS DERIVED ON PAPER AND NONE CAME FROM THE CODE.
PRINCIPLES.md section 2.3: an oracle is never regenerated from the code it
tests. Each entry's docstring carries the derivation in full, and the two
groups derive differently because the two rules are different objects:

GROUP R-A, THE BERNSTEIN RULE. The rule's endpoints depend on ``L``, an UPPER
rational bound on ``ln(1/eps)`` whose exact value depends on the evaluation
parameters ``j`` and ``s``. A frozen integer that depended on those parameters
would pin an implementation and not a rule, so EVERY CASE HERE IS DERIVED OVER
A BRACKET: a rational interval ``[L_lo, L_hi]`` containing ``ln(1/eps)``, and
the demonstration that ``floor(np - t(L))`` and ``ceil(np + t(L))`` take the
SAME values for every ``L`` in it. The frozen integers are therefore facts
about the rule of ``prop:rule-bernstein``, at every ``L`` in the stated
bracket.

    THAT IS NOT THE SAME AS "AT ANY ADMISSIBLE (j, s)", which is what this
    docstring once said.
    ``lem:log-enclosure`` bounds ``ln(1/eps)`` from above at every ``j`` and
    ``s``, but HOW FAR above is a statement about them: at a small ``j`` the
    evaluation's ``L`` lands outside the bracket and the endpoints move. The
    hypothesis is on the entry, as the sibling ``O-ENCL-EQUALS-SWEEP`` already
    carried it; the golden test pins three settings and all three reproduce.

    The logarithms are bracketed from the ARTANH SERIES, which a reader can
    redo: ln x = 2 artanh((x-1)/(x+1)) = 2 (u + u^3/3 + u^5/5 + ...) with
    u = (x-1)/(x+1).
        ln 2 = 2 artanh(1/3) = 2 (1/3 + 1/81 + 1/1215 + 1/15309 + 1/177147...)
             = 2 (0.3333333 + 0.0123457 + 0.0008230 + 0.0000653 + 0.0000056)
             = 2 (0.3465730...) = 0.6931472... , and the omitted tail is under
             2e-7, so ln 2 is in (0.693146, 0.693148).
        ln 1.024 = 2 artanh(0.012/1.012) = 2 artanh(0.01185771)
                 = 2 (0.01185771 + 0.00000056) = 0.0237165... , the tail under
                 1e-9, so ln 1.024 is in (0.023716, 0.023717).
        10^3 = 1024 / 1.024, so 3 ln 10 = 10 ln 2 - ln 1.024, giving
             3 ln 10 in (6.93146 - 0.023717, 6.93148 - 0.023716)
                      = (6.907743, 6.907764), so
             ln 10 in (2.302581, 2.302589), ln 100 in (4.605162, 4.605178) and
             ln 1000 in (6.907743, 6.907764).

GROUP R-B, THE ENCLOSURE EVALUATION. Here the binomial law is written out over
its common denominator, the exact quantiles are read off the integer table, and
the bracket verdict is argued from the MARGIN: the enclosure's own width is
bounded by the parameters and is orders of magnitude below the log-distance
between the tail and the budget at the indices that decide the bracket, so the
verdict is a fact about the rule and not about the precision. One case is
deliberately the OTHER kind: its budget is set exactly equal to a tail value,
where no enclosure of positive width can decide the comparison, and the emitted
endpoint is provably ONE COUNT above the exact quantile.

WHAT THIS REGISTRY DOES NOT DO. It does not implement the module: no function
here searches for an endpoint, evaluates an enclosure or sums a window. Every
frozen field is a literal or an exact rational assembled from integers a reader
can check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from registry import INADMISSIBLE_SOURCES, KINDS

__all__ = [
    "ASSURANCE",
    "BERNSTEIN_CASES",
    "ENCLOSURE_CASES",
    "INADMISSIBLE_SOURCES",
    "KINDS",
    "RULE_ORACLES",
    "BernsteinCase",
    "EnclosureCase",
    "RuleOracleEntry",
    "rule_oracle",
]

#: The ORACLE's own evidential tier, as in the sibling registries: this module
#: declares no per-result assurance label of any kind.
ASSURANCE = "estimate"


@dataclass(frozen=True)
class RuleOracleEntry:
    """One frozen expected value with the derivation that produced it."""

    oracle_id: str
    claims: tuple[str, ...]
    kind: str
    subject: str
    derivation: str
    value: Fraction | int | str | None = None
    hypotheses: tuple[str, ...] = field(default_factory=tuple)
    assurance: str = ASSURANCE


def rule_oracle(oracle_id: str) -> RuleOracleEntry:
    """Return the registry entry with the given ``oracle_id``."""
    for entry in RULE_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no oracle entry {oracle_id!r}")


# ===========================================================================
#  Group R-A -- the Bernstein rule (prop:rule-bernstein)
# ===========================================================================


@dataclass(frozen=True)
class BernsteinCase:
    """One ``(n, p, eps)`` with the endpoints Eq. ``eq:bernstein-endpoints`` gives.

    ``budget_low`` and ``budget_high`` bracket ``ln(1 / eps)``; the derivation
    shows that every ``L`` in that interval gives the frozen endpoints, so the
    case pins the RULE and not an evaluation of it. ``deviation_low`` and
    ``deviation_high`` are ``t(L)`` at the two ends, to three or four decimal
    places, and are carried so that a reader can check the floor and the
    ceiling without redoing the square root.
    """

    case_id: str
    rounds: int
    honest: Fraction
    eps_lower: Fraction
    eps_upper: Fraction
    variance: Fraction
    budget_low: Fraction
    budget_high: Fraction
    deviation_low: Fraction
    deviation_high: Fraction
    endpoint_lower: int
    endpoint_upper: int
    derivation: str


BERNSTEIN_CASES: tuple[BernsteinCase, ...] = (
    BernsteinCase(
        case_id="BERN-n100-p-half",
        rounds=100,
        honest=Fraction(1, 2),
        eps_lower=Fraction(1, 100),
        eps_upper=Fraction(1, 100),
        variance=Fraction(25),
        budget_low=Fraction(46, 10),
        budget_high=Fraction(461, 100),
        deviation_low=Fraction(167764, 10000),
        deviation_high=Fraction(167965, 10000),
        endpoint_lower=33,
        endpoint_upper=67,
        derivation="""n = 100, p = 1/2, eps^- = eps^+ = 1/100.
        v = n p (1-p) = 100 * 1/2 * 1/2 = 25, and n p = 50.
        L = ln(100), which the artanh bracket of the module docstring puts in
        (4.605162, 4.605178); take the wider [4.60, 4.61], which contains it.
        t(L) = L/3 + sqrt((L/3)^2 + 2 v L) = L/3 + sqrt(L^2/9 + 50 L).
          At L = 4.60: L/3 = 1.533333, L^2/9 = 2.351111, 50L = 230, so the
            radicand is 232.351111; 15.24^2 = 232.2576 and 15.25^2 = 232.5625,
            so the root is 15.2431 to four places and t = 16.7764.
          At L = 4.61: L/3 = 1.536667, L^2/9 = 2.361344, 50L = 230.5, so the
            radicand is 232.861344; 15.25^2 = 232.5625 and 15.26^2 = 232.8676,
            so the root is 15.2598 and t = 16.7965.
        np + t lies in [66.7764, 66.7965], whose ceiling is 67 throughout;
        np - t lies in [33.2035, 33.2236], whose floor is 33 throughout.
        Neither clip is active (0 < 33 and 67 < 100). So R^- = 33, R^+ = 67 for
        every L in [4.60, 4.61] and hence for every admissible (j, s).""",
    ),
    BernsteinCase(
        case_id="BERN-n10-clip-at-zero",
        rounds=10,
        honest=Fraction(1, 5),
        eps_lower=Fraction(1, 10),
        eps_upper=Fraction(1, 10),
        variance=Fraction(8, 5),
        budget_low=Fraction(230, 100),
        budget_high=Fraction(2305, 1000),
        deviation_low=Fraction(35858, 10000),
        deviation_high=Fraction(35908, 10000),
        endpoint_lower=0,
        endpoint_upper=6,
        derivation="""n = 10, p = 1/5, eps^- = eps^+ = 1/10.
        v = 10 * 1/5 * 4/5 = 8/5 = 1.6, and n p = 2.
        L = ln(10), in (2.302581, 2.302589) by the artanh bracket; take the
        wider [2.300, 2.305].
        t(L) = L/3 + sqrt(L^2/9 + 3.2 L).
          At L = 2.300: L/3 = 0.766667, L^2/9 = 0.587778, 3.2L = 7.36, so the
            radicand is 7.947778; 2.819^2 = 7.946761 and 2.820^2 = 7.952400,
            so the root is 2.81918 and t = 3.585847.
          At L = 2.305: L/3 = 0.768333, L^2/9 = 0.590336, 3.2L = 7.376, so the
            radicand is 7.966336; 2.822^2 = 7.963684 and 2.823^2 = 7.969329,
            so the root is 2.82247 and t = 3.590803.
        np + t lies in [5.5858, 5.5908], whose ceiling is 6 throughout.
        np - t lies in [-1.5908, -1.5858], whose floor is -2 throughout, and
        THE CLIP AT ZERO IS ACTIVE: R^- = max{0, -2} = 0. That is the branch of
        Eq. eq:bernstein-endpoints this case exists for, and the admissibility
        it needs is trivial: Pr[N < 0] = 0 <= eps^-.
        So R^- = 0, R^+ = 6 for every L in [2.300, 2.305].""",
    ),
    BernsteinCase(
        case_id="BERN-n1000-p-tenth",
        rounds=1000,
        honest=Fraction(1, 10),
        eps_lower=Fraction(1, 1000),
        eps_upper=Fraction(1, 1000),
        variance=Fraction(90),
        budget_low=Fraction(6907, 1000),
        budget_high=Fraction(6908, 1000),
        deviation_low=Fraction(376373, 10000),
        deviation_high=Fraction(376402, 10000),
        endpoint_lower=62,
        endpoint_upper=138,
        derivation="""n = 1000, p = 1/10, eps^- = eps^+ = 1/1000.
        v = 1000 * 1/10 * 9/10 = 90, and n p = 100.
        L = ln(1000) = 3 ln 10, in (6.907743, 6.907764) by the artanh bracket;
        take the wider [6.907, 6.908].
        t(L) = L/3 + sqrt(L^2/9 + 180 L).
          At L = 6.907: L/3 = 2.302333, L^2/9 = 5.300740, 180L = 1243.26, so
            the radicand is 1248.560740; 35.33^2 = 1248.2089 and
            35.34^2 = 1248.9156, so the root is 35.3350 and t = 37.6373.
          At L = 6.908: L/3 = 2.302667, L^2/9 = 5.302275, 180L = 1243.44, so
            the radicand is 1248.742275; the same two squares bracket it and
            the root is 35.3375, so t = 37.6402.
        np + t lies in [137.6373, 137.6402], whose ceiling is 138 throughout;
        np - t lies in [62.3598, 62.3627], whose floor is 62 throughout.
        Neither clip is active. So R^- = 62, R^+ = 138 for every L in
        [6.907, 6.908].""",
    ),
    BernsteinCase(
        case_id="BERN-degenerate-mass-zero",
        rounds=64,
        honest=Fraction(0),
        eps_lower=Fraction(1, 8),
        eps_upper=Fraction(1, 8),
        variance=Fraction(0),
        budget_low=Fraction(2079, 1000),
        budget_high=Fraction(2080, 1000),
        deviation_low=Fraction(0),
        deviation_high=Fraction(0),
        endpoint_lower=0,
        endpoint_upper=0,
        derivation="""n = 64, p = 0, any admissible allocation.
        Definition def:endpoint-rule (c), the degenerate-mass convention:
        R^- = R^+ = 0 at p = 0, FOR EVERY eps. No evaluation is performed and
        no logarithm is taken -- the count is 0 with probability one, so both
        tails are exactly 0 and both budgets are entirely unspent
        (prop:rule-exact (v) proves the same for the exact rule, and
        def:endpoint-rule (c) makes it a REQUIREMENT on every rule, which is
        what this case pins). The budget bracket is carried only for
        uniformity: ln 8 = 3 ln 2 is in (2.079438, 2.079444).""",
    ),
    BernsteinCase(
        case_id="BERN-zero-budget",
        rounds=64,
        honest=Fraction(1, 4),
        eps_lower=Fraction(0),
        eps_upper=Fraction(0),
        variance=Fraction(12),
        budget_low=Fraction(0),
        budget_high=Fraction(0),
        deviation_low=Fraction(0),
        deviation_high=Fraction(0),
        endpoint_lower=0,
        endpoint_upper=64,
        derivation="""n = 64, p = 1/4, eps^- = eps^+ = 0.
        Definition def:endpoint-rule (b), the zero-budget convention: at
        0 < p < 1 the rule returns R^- = 0 and R^+ = n at a zero budget. No
        logarithm is taken -- ln(1/0) has no value -- and the convention is
        what makes thm:monotonicity-limits (iii) hold for every rule: a zero completeness
        budget buys no constraint at all, the emitted interval being the whole
        range [0, 64]. v = 64 * 1/4 * 3/4 = 12 is carried for the reader; it
        enters nothing here.""",
    ),
)


# ===========================================================================
#  Group R-B -- the enclosure evaluation (prop:bracketed-endpoints)
# ===========================================================================


@dataclass(frozen=True)
class EnclosureCase:
    """One ``(n, p, eps)`` small enough for the exact tails to be written out.

    ``mass`` is the binomial law over the common denominator ``denominator``,
    indexed so that entry ``k`` IS the mass at ``k``; ``kappa_lower`` and
    ``kappa_upper`` are the EXACT quantiles of Eqs. ``eq:kappaminus`` and
    ``eq:kappaplus`` read off it. ``bracketed_lower`` and ``bracketed_upper``
    are what the enclosure evaluation returns, and ``lower_decided`` /
    ``upper_decided`` are the bracket verdict of
    ``prop:bracketed-endpoints`` (ii).
    """

    case_id: str
    rounds: int
    honest: Fraction
    eps_lower: Fraction
    eps_upper: Fraction
    denominator: int
    mass: tuple[int, ...]
    kappa_lower: int
    kappa_upper: int
    guarded_lower: int
    guarded_upper: int
    bracketed_lower: int
    bracketed_upper: int
    lower_decided: bool
    upper_decided: bool
    derivation: str


ENCLOSURE_CASES: tuple[EnclosureCase, ...] = (
    EnclosureCase(
        case_id="ENCL-n10-p-half-decided",
        rounds=10,
        honest=Fraction(1, 2),
        eps_lower=Fraction(1, 10),
        eps_upper=Fraction(1, 10),
        denominator=1024,
        mass=(1, 10, 45, 120, 210, 252, 210, 120, 45, 10, 1),
        kappa_lower=3,
        kappa_upper=7,
        guarded_lower=3,
        guarded_upper=7,
        bracketed_lower=3,
        bracketed_upper=7,
        lower_decided=True,
        upper_decided=True,
        derivation="""n = 10, p = 1/2, eps^- = eps^+ = 1/10.
        The law is C(10,k)/1024, the row (1, 10, 45, 120, 210, 252, 210, 120,
        45, 10, 1), which sums to 1024.
        UPPER TAILS Pr[N > k] = (sum_{j>k} mass_j) / 1024:
          k = 7: (45 + 10 + 1)/1024 = 56/1024 = 0.0546875 <= 1/10, admissible;
          k = 6: (120 + 56)/1024 = 176/1024 = 0.171875 > 1/10, not admissible.
        The set of Eq. eq:kappaplus is an up-set, so kappa^+ = 7.
        LOWER TAILS Pr[N < k] = (sum_{j<k} mass_j) / 1024:
          k = 3: (1 + 10 + 45)/1024 = 56/1024 <= 1/10, admissible;
          k = 4: (56 + 120)/1024 = 176/1024 > 1/10, not admissible.
        kappa^- = 3, the maximum of a down-set.
        THE GUARD IS INACTIVE: floor(np) = ceil(np) = 5, and 3 <= 5 <= 7, so
        k^- = min{3, 5} = 3 and k^+ = max{7, 5} = 7.
        THE BRACKET IS DECIDED ON BOTH SIDES, and the margins are what decides
        it: at k = 7 the tail is 0.0547 against a budget of 0.1, a log distance
        of ln(0.1/0.0546875) = 0.60 nats, and at k = 6 the tail is 0.1719
        against the same budget, a log distance of 0.54 nats. The enclosure's
        own width at this n is bounded by the Wallis constant's contribution,
        under 2e-4 nats, so both comparisons are decided by three orders of
        magnitude and the emitted endpoints EQUAL the exact quantiles
        (prop:bracketed-endpoints (ii)). The lower side is the same statement
        for the mirror N' = 10 - N, which is binomial (10, 1/2) again.""",
    ),
    EnclosureCase(
        case_id="ENCL-n8-p-quarter-decided",
        rounds=8,
        honest=Fraction(1, 4),
        eps_lower=Fraction(1, 16),
        eps_upper=Fraction(1, 16),
        denominator=65536,
        mass=(6561, 17496, 20412, 13608, 5670, 1512, 252, 24, 1),
        kappa_lower=0,
        kappa_upper=4,
        guarded_lower=0,
        guarded_upper=4,
        bracketed_lower=0,
        bracketed_upper=4,
        lower_decided=True,
        upper_decided=True,
        derivation="""n = 8, p = 1/4, eps^- = eps^+ = 1/16.
        The law is C(8,k) 3^(8-k) / 4^8 with 4^8 = 65536:
          k=0: 1*6561 = 6561        k=5: 56*27 = 1512
          k=1: 8*2187 = 17496       k=6: 28*9 = 252
          k=2: 28*729 = 20412       k=7: 8*3 = 24
          k=3: 56*243 = 13608       k=8: 1*1 = 1
          k=4: 70*81 = 5670
        The nine add to 65536, which a reader can check:
        6561+17496 = 24057, +20412 = 44469, +13608 = 58077, +5670 = 63747,
        +1512 = 65259, +252 = 65511, +24 = 65535, +1 = 65536.
        The budget is 1/16 = 4096/65536, so every comparison is between
        integers.
        UPPER TAILS: Pr[N > 4] = 1512 + 252 + 24 + 1 = 1789 <= 4096, and
        Pr[N > 3] = 5670 + 1789 = 7459 > 4096. So kappa^+ = 4.
        LOWER TAILS: Pr[N < 1] = 6561 > 4096, and Pr[N < 0] = 0 <= 4096. So
        kappa^- = 0.
        THE GUARD IS INACTIVE: np = 2, so floor = ceil = 2 and
        k^- = min{0, 2} = 0, k^+ = max{4, 2} = 4.
        THE BRACKET IS DECIDED ON BOTH SIDES. Upper: 1789/4096 and 7459/4096
        are a factor 2.29 below and 1.82 above the budget, log distances of
        0.83 and 0.60 nats. Lower, through the mirror N' = 8 - N, which is
        binomial (8, 3/4): Pr[N' > 8] = 0 certifies the endpoint (the exact
        boundary value of thm:binomial-tails, never enclosed), and Pr[N' > 7] = 6561 >
        4096 certifies the index below it inadmissible at a log distance of
        0.47 nats. Both are orders of magnitude above the enclosure's width,
        so the emitted endpoints equal the exact quantiles.""",
    ),
    EnclosureCase(
        case_id="ENCL-n10-budget-on-a-tail-undecided",
        rounds=10,
        honest=Fraction(1, 2),
        eps_lower=Fraction(7, 128),
        eps_upper=Fraction(7, 128),
        denominator=1024,
        mass=(1, 10, 45, 120, 210, 252, 210, 120, 45, 10, 1),
        kappa_lower=3,
        kappa_upper=7,
        guarded_lower=2,
        guarded_upper=8,
        bracketed_lower=2,
        bracketed_upper=8,
        lower_decided=False,
        upper_decided=False,
        derivation="""n = 10, p = 1/2, eps^- = eps^+ = 7/128 = 56/1024, WHICH IS
        EXACTLY THE TAIL Pr[N > 7] = Pr[N < 3] = 56/1024. The law is the row of
        ENCL-n10-p-half-decided.
        THE EXACT RULE: k = 7 satisfies Pr[N > 7] <= eps^+ WITH EQUALITY, so
        kappa^+ = 7, and symmetrically kappa^- = 3.
        THE ENCLOSURE EVALUATION CANNOT REACH THEM, and that is what this case
        pins. At k = 7 the certified-admissible test is U(7) <= lambda^- for
        rationals U(7) >= ln Pr[N > 7] and lambda^- <= ln eps^+; the two
        quantities are EQUAL, and any enclosure of positive width has
        U(7) > ln eps^+ >= lambda^-, so k = 7 is NOT certified. It is not
        certified inadmissible either: Lambda(7) <= ln Pr[N > 7] = ln eps^+ <=
        lambda^+. It is UNDECIDED, and the search counts an undecided index as
        not certified (search_procedure).
        The next index up IS certified: Pr[N > 8] = (10 + 1)/1024 = 11/1024, a
        factor 5.09 below the budget, a log distance of 1.63 nats. So the
        bisection returns 8, and the bracket is NOT decided, because 7 is
        undecided rather than certified inadmissible.
        The emitted endpoint is therefore ONE COUNT ABOVE the exact quantile:
        8 = kappa^+ + 1, which is admissible (Pr[N > 8] <= eps^+) and is
        exactly what prop:bracketed-endpoints (i) promises and its (iii)
        bounds. The lower side is the mirror: the search returns 2 = kappa^- -
        1, undecided at 3.
        THE GUARD DOES NOT MOVE EITHER ENDPOINT: floor(np) = ceil(np) = 5, and
        2 <= 5 <= 8, so k^- = 2 and k^+ = 8.""",
    ),
)


# ===========================================================================
#  The entries
# ===========================================================================


RULE_ORACLES: tuple[RuleOracleEntry, ...] = (
    RuleOracleEntry(
        oracle_id="O-BERN-ENDPOINTS",
        claims=("binomial-box/prop:rule-bernstein",),
        kind="toy-instance",
        subject=(
            "the Bernstein rule's endpoints at three (n, p, eps), each over a "
            "bracket of L"
        ),
        derivation="""Eq. eq:bernstein-endpoints evaluated over an interval of
        L rather than at one value, so that the frozen integers are facts about
        the rule and not about the evaluation parameters. The three cases of
        BERNSTEIN_CASES carry the arithmetic; the logarithms are bracketed from
        the artanh series in the module docstring, which needs no table and no
        library. A reader redoes each case with a square root to four decimal
        places.""",
        hypotheses=(
            "0 < p < 1 and eps > 0 for the three evaluated cases; the other two "
            "are the conventions def:endpoint-rule (b) and (c), where no "
            "evaluation happens at all",
            "the evaluation parameters are such that L = the upper root bound "
            "of lem:log-enclosure on 1/eps lands inside the case's own bracket "
            "[budget_low, budget_high]. Every (j, s) bounds ln(1/eps) from "
            "ABOVE, so every one of them is admissible; how far above is a "
            "statement about (j, s), and at a small j the endpoints move. The "
            "bracket is wide enough for the settled parameters and for the two "
            "coarser settings the golden test also pins",
        ),
    ),
    RuleOracleEntry(
        oracle_id="O-BERN-CONVENTIONS",
        claims=("binomial-box/prop:rule-bernstein", "binomial-box/def:endpoint-rule"),
        kind="structural-identity",
        subject="the zero-budget and degenerate-mass conventions on the Bernstein rule",
        derivation="""Definition def:endpoint-rule (b) and (c) are REQUIREMENTS
        on every admissible endpoint rule, not consequences of an evaluation:
        at p = 0 the rule returns (0, 0) and at p = 1 it returns (n, n) for
        every budget, and at a zero budget with 0 < p < 1 it returns 0 on the
        lower side and n on the upper. Both are what make thm:monotonicity-limits (iii) and
        (vi) and rem:epsstar hold for every rule, and neither takes a
        logarithm -- ln(1/0) has no value, so a rule that reached its
        evaluation at a zero budget would not be total.""",
    ),
    RuleOracleEntry(
        oracle_id="O-ENCL-EQUALS-SWEEP",
        claims=(
            "binomial-box/prop:bracketed-endpoints",
            "binomial-box/def:interval",
        ),
        kind="toy-instance",
        subject=(
            "the enclosure evaluation returns the exact quantile where the "
            "bracket is decided"
        ),
        derivation="""prop:bracketed-endpoints (ii): if the index below the
        emitted one is certified inadmissible, the emitted index IS the exact
        binomial quantile. The two decided cases of ENCLOSURE_CASES write the
        binomial law out over its common denominator, read the exact quantiles
        off the integer table, and argue the verdict from the log distance
        between the tail and the budget at the two deciding indices -- 0.47 to
        0.83 nats, against an enclosure width bounded by about 2e-4 nats at
        these n. The verdict is therefore a fact about the rule at any
        admissible parameters.""",
        hypotheses=(
            "the evaluation parameters are such that the enclosure width at "
            "these n is below the stated margins, which every admissible "
            "setting of them satisfies by orders of magnitude",
        ),
    ),
    RuleOracleEntry(
        oracle_id="O-ENCL-UNDECIDED-IS-CONSERVATIVE",
        claims=(
            "binomial-box/prop:bracketed-endpoints",
            "binomial-box/lem:guard",
        ),
        kind="analytic-limit",
        subject=(
            "a budget equal to a tail leaves the bracket undecided and costs "
            "one count"
        ),
        derivation="""The one case where NO enclosure of positive width can
        decide the comparison: eps^+ is set exactly equal to Pr[N > 7] at
        n = 10, p = 1/2, so the upper bound of any enclosure strictly exceeds
        ln eps^+ and the lower bound is at most it. The index is undecided, the
        search counts it as not certified, and the emitted endpoint is the next
        one up. That endpoint is still ADMISSIBLE -- which is
        prop:bracketed-endpoints (i), and is why the route costs rate and never
        soundness -- and the emitted interval CONTAINS the sweep's. The cost is
        exactly one count on each side, which the case freezes.""",
    ),
)
