"""The ``statistics-acceptance`` oracle registry -- hand-derived golden values.

The implementation band runs under the freeze rule, in two instances. **This
file is run A's output.** Every value below was derived BY HAND from the
accepted ``contract.tex`` 0.1.2 before any implementation existed. Run B, a
different implementer instance, writes the code against these numbers and may
read but not modify them. An expected value that turns out to be wrong is a
FINDING, reported and corrected deliberately with its derivation, never edited
in passing to make a test green.

WHY A SIBLING FILE AND NOT A NEW GROUP IN ``registry.py``
========================================================
``registry.py`` is, in its own first line, "the ``meat-core`` oracle registry",
and its policy binds every entry in its ``ORACLES`` tuple to that module:
``test_registry_integrity.py::test_every_oracle_claim_id_exists_in_the_interface``
asserts that each entry's ``claims`` resolve in
``docs/mathematical-contracts/meat-core/interface.yaml``, whose claim IDs are
C1-C20. The claims pinned here are SA1-SA9 of a DIFFERENT module at a DIFFERENT
contract version, and they resolve in
``docs/mathematical-contracts/statistics-acceptance/interface.yaml`` instead.
Adding them to that tuple would either break that assertion or force it to be
weakened -- and weakening a traceability check to admit new data is exactly the
move the freeze rule exists to prevent.

So this is a PURE INSERTION: a new module beside ``registry.py``. Not one
existing entry, value, derivation or tuple in ``registry.py`` is edited, and its
Group 8 -- which pins ``meat-core``'s side of the same geometry -- is untouched.
The conventions are that file's, deliberately: the same entry shape (an
``oracle_id``, the claim IDs it pins, a ``kind`` from the same vocabulary, a
subject, and a derivation long enough to redo on paper), the same admissibility
rule, and the same rule that a witness which merely AGREES with a value is a
cross-check and never its source. ``KINDS`` and ``INADMISSIBLE_SOURCES`` are
IMPORTED from it rather than restated, so the two registries cannot drift on
what an admissible oracle is.

ONE DELIBERATE DEPARTURE: EXACT RATIONALS, NOT FLOATS
=====================================================
``registry.py`` freezes ``float`` values, because the quantities it pins are
transcendental (trace powers, logarithms) and the contract it serves rounds them
under an interval-arithmetic assumption. THIS contract has no such quantity.
Assumption A-EXACT requires that ``p^hon``, ``ecomp`` and the allocation be
exact rationals and that every number the module emits be one; Theorem
``thm:box-construction`` (i) proves the emitted box bounds are integer multiples of ``1/n``;
and Remark ``rem:epsstar`` makes ``epsilon_star`` exactly computable at rational
``p^hon``. Freezing these as binary floats would introduce the only rounding in
the whole module and would silently destroy the two values below whose
denominator is ``10**30``. Every number here is therefore a
``fractions.Fraction``, and equality is EXACT equality -- no tolerance appears
anywhere in this file or in the tests that read it.

ADMISSIBILITY (ADR-0003)
========================
No MATLAB, OpenQKDSecurity, CVX, MOSEK or Julia value is admissible and none is
used; the guard is asserted against ``INADMISSIBLE_SOURCES``. Every number below
is an exact closed form, an elementary evaluation of one, or a hand-computed
integer. This registry cites nothing: contract.tex 0.1.2 carries five citations
and ALL FIVE live in its Section 6 remark ``rem:literature``, which that remark
declares non-normative ("No claim of this contract rests on any external
source"). There is therefore no published comparison point to record, and
inventing one would be worse than none.

WHAT THIS REGISTRY DOES NOT DO
==============================
It does not certify anything. ``statistics-acceptance`` 0.1.2 declares NO
per-result assurance label at all -- no ``estimate`` / ``certified`` output row,
no requested-assurance parameter, no runtime certificate chain -- so
``ASSURANCE`` below is the ORACLE's own evidential status and is ``estimate``
for every entry, exactly as in ``registry.py``. The tier ceiling recorded in
STATUS.yaml (``certified``) is an ELIGIBILITY statement about the mathematics
and is not a property any number here has.

It also does not implement the module. No function in this file constructs an
acceptance set, computes a binomial quantile, or searches for ``kappa``. Every
frozen field is a LITERAL, and the only computation is the exact rational
arithmetic that assembles a literal from integers a reader can check --
``Fraction(1789, 65536)``, ``Fraction(999, 1000) ** 10``. That is the same
discipline ``registry.py`` states for C11 and C12: an oracle that is the
implementation checks the solver against itself.

WHAT IS PINNED, BY CLAIM
========================
SA1  geometry validation predicates, with the RATIONAL interpolation witness
SA2  exact binomial tails at small n, with the pmf written out
SA3  the extremal endpoints, admissible relaxation, and the exact guard cost in
     both regimes ``rem:guard`` separates
SA4  twelve complete ``Acc`` constructions, with raw box bounds AND the denoted
     set's tight bounds recorded apart
SA5  ``epsilon_star`` on every construction, and where the union bound is loose
SA6  honest containment, and the nine input-domain violation codes
SA7  budget monotonicity, the ``ecomp = 0`` limit, the ``n``-non-monotonicity
     counterexample, the Chebyshev half-width, the one-letter alphabet
SA8  the acceptance support (including a STRICT superset), the closed-form box
     minimum and its tight dual witness
SA9  singleton completeness, including both degenerate no-admissible-budget
     cases and the zero-budget point mass

CLAIM IDS AND LABELS
====================
No case, no derivation, no claim id and no number of this file is regenerated:
the two imports it makes (``registry.INADMISSIBLE_SOURCES`` and
``registry.KINDS``) resolve to this repository's ``registry.py``.
PRINCIPLES.md section 2.3: an oracle registry "moves with its module and is
never regenerated from the code it tests".

The text above this paragraph is the freeze's own text, which is why it still
names ``contract.tex`` 0.1.2 and the two-run freeze: those are the document and
the process the freeze bound. The claim ids ``SA1``-``SA9`` are that contract's
section names; in this repository they are claim labels under
``spec/modules/statistics/``, and
``tests/oracles/test_statistics_acceptance_registry_interface.py`` is where the
two are bound together -- including ``SA3``, which is now
``binomial-box/prop:rule-exact`` for what is the exact rule's and
``binomial-box/lem:guard`` for what is every rule's.

THE STRING ``statistics-acceptance@0.1.2`` STAYS, and so does the assumption id
``A-EXACT`` wherever a derivation names it (the id is ``A-RATIONAL`` in this
repository, with the machine key ``exact_rational_inputs`` unchanged). Both are
the record of WHAT THE FREEZE BOUND; the emitted pin and the live assumption id
are the code's and the claim files', and neither is edited here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from registry import INADMISSIBLE_SOURCES, KINDS

__all__ = [
    "ASSURANCE",
    "BINOMIAL_TAIL_CASES",
    "BOX_MINIMUM_CASES",
    "CONSTRUCTION_CASES",
    "GEOMETRY_VALIDATION_CASES",
    "GUARD_CASES",
    "INADMISSIBLE_SOURCES",
    "INPUT_DOMAIN_VIOLATION_CASES",
    "KINDS",
    "REASON_CODES",
    "SA_ORACLES",
    "SINGLETON_CASES",
    "BinomialTailCase",
    "BoxMinimumCase",
    "ConstructionCase",
    "GeometryValidationCase",
    "GuardCase",
    "InputDomainViolationCase",
    "SAOracleEntry",
    "SingletonCase",
    "sa_oracle",
]

#: The ORACLE's own evidential tier. ``estimate`` for every entry: see the
#: module docstring, "WHAT THIS REGISTRY DOES NOT DO". The module's contract
#: declares no per-result assurance label of any kind.
ASSURANCE = "estimate"

#: The nine machine-readable input-domain violation codes, VERBATIM from
#: contract.tex 0.1.2 Theorem ``thm:honest-containment`` (iii) and in its order. This tuple is
#: the whole vocabulary: the contract enumerates exactly these and states that
#: one further clause of the input domain -- the cross-artifact A-ALPHABET
#: clause -- carries NO code and is routed to bundle validation as a hard error.
REASON_CODES: tuple[str, ...] = (
    "alphabet_empty",
    "alphabet_not_finite",
    "rounds_out_of_range",
    "honest_not_a_distribution",
    "budget_out_of_range",
    "allocation_negative",
    "allocation_exceeds_budget",
    "selector_not_a_subset",
    "inputs_not_rational",
)


@dataclass(frozen=True)
class SAOracleEntry:
    """One frozen expected value with the derivation that produced it.

    The field set mirrors ``registry.OracleEntry``; ``value`` is widened to
    ``Fraction`` and the alpha-dependent fields are dropped, no claim of this
    contract depending on the Renyi order (contract.tex Section 2.3).
    """

    oracle_id: str
    claims: tuple[str, ...]
    kind: str
    subject: str
    derivation: str
    #: Single golden value where there is one; the case tuples carry the rest.
    value: Fraction | int | str | None = None
    #: Hypotheses a consuming theorem carries that must hold for this entry.
    hypotheses: tuple[str, ...] = field(default_factory=tuple)
    assurance: str = ASSURANCE


def sa_oracle(oracle_id: str) -> SAOracleEntry:
    """Return the registry entry with the given ``oracle_id``."""
    for entry in SA_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no oracle entry {oracle_id!r}")


# ===========================================================================
#  Group SA-A -- exact binomial tails (SA2)
# ===========================================================================
#
#  Every case writes the pmf out over a COMMON DENOMINATOR, so that the whole
#  table is integer arithmetic a reader can add up. Theorem thm:binomial-tails proves the
#  two tails equal the regularized incomplete beta function; Lemma
#  lem:exact-strict-tails fixes the two forms the rest of the contract uses,
#      Pr[N < k] = Pr[N <= k-1]   and   Pr[N > k] = Pr[N >= k+1] ,
#  with Pr[N < 0] = 0 and Pr[N > n] = 0. Those are the two arrays frozen here,
#  indexed so that entry k IS the value at k.


@dataclass(frozen=True)
class BinomialTailCase:
    """The exact law of one binomial count, and both tails at every k."""

    case_id: str
    n: int
    p: Fraction
    #: Common denominator of every numerator tuple below.
    denominator: int
    #: Pr[N = k] * denominator, for k = 0 .. n.
    pmf_numerators: tuple[int, ...]
    #: Pr[N <= k] * denominator, for k = 0 .. n.
    cdf_numerators: tuple[int, ...]
    #: Pr[N < k] * denominator, for k = 0 .. n+1. Entry 0 is 0 by convention.
    lower_tail_numerators: tuple[int, ...]
    #: Pr[N > k] * denominator, for k = 0 .. n. Entry n is 0 by convention.
    upper_tail_numerators: tuple[int, ...]
    beta_cross_check: str
    arithmetic: str


BINOMIAL_TAIL_CASES: tuple[BinomialTailCase, ...] = (
    BinomialTailCase(
        case_id="BTAIL-n2-p-half",
        n=2,
        p=Fraction(1, 2),
        denominator=4,
        pmf_numerators=(1, 2, 1),
        cdf_numerators=(1, 3, 4),
        lower_tail_numerators=(0, 1, 3, 4),
        upper_tail_numerators=(3, 1, 0),
        beta_cross_check="""\
Theorem thm:binomial-tails, Eq. eq:uppertail, at k = 1:
  Pr[N >= 1] = I_{1/2}(1, 2)
             = int_0^{1/2} (1-t) dt / int_0^1 (1-t) dt
             = [t - t^2/2]_0^{1/2} / (1/2) = (1/2 - 1/8)/(1/2) = 3/4 ,
and the table's upper_tail_numerators[0] / 4 = 3/4. At k = 2:
  Pr[N >= 2] = I_{1/2}(2, 1) = int_0^{1/2} t dt / int_0^1 t dt
             = (1/8)/(1/2) = 1/4 = upper_tail_numerators[1] / 4 .
The integral route and the summation route agree, which is the content of
Eq. eq:uppertail; the lead-in of Lemma lem:exact-strict-tails says taking either is an implementation
choice constrained only by A-EXACT.""",
        arithmetic="""\
THE SMALLEST NON-TRIVIAL CASE, and the one every later table is checked
against. n = 2, p = 1/2, so binom(2,k) 2^{-2} gives
  Pr[N = 0] = 1/4 , Pr[N = 1] = 2/4 , Pr[N = 2] = 1/4 ,
summing to 4/4 = 1. Partial sums give the cdf (1, 3, 4)/4.
LOWER TAILS Pr[N < k] = Pr[N <= k-1], read off the cdf shifted by one, with
Pr[N < 0] = 0 by convention (Theorem thm:binomial-tails, boundary values):
  k = 0 : 0 ,  k = 1 : 1/4 ,  k = 2 : 3/4 ,  k = 3 : 4/4 = 1 .
UPPER TAILS Pr[N > k] = 1 - Pr[N <= k]:
  k = 0 : 3/4 ,  k = 1 : 1/4 ,  k = 2 : 0 .
MONOTONICITY, the last sentence of Theorem thm:binomial-tails, is visible in both arrays:
Pr[N < k] is non-decreasing in k and Pr[N > k] non-increasing. The proof of
Theorem thm:sa3 (iii) uses exactly that and nothing else.""",
    ),
    BinomialTailCase(
        case_id="BTAIL-n3-p-half",
        n=3,
        p=Fraction(1, 2),
        denominator=8,
        pmf_numerators=(1, 3, 3, 1),
        cdf_numerators=(1, 4, 7, 8),
        lower_tail_numerators=(0, 1, 4, 7, 8),
        upper_tail_numerators=(7, 4, 1, 0),
        beta_cross_check="""\
Eq. eq:uppertail at k = 2:
  Pr[N >= 2] = I_{1/2}(2, 2) = int_0^{1/2} t(1-t) dt / int_0^1 t(1-t) dt
             = [t^2/2 - t^3/3]_0^{1/2} / (1/6)
             = (1/8 - 1/24) / (1/6) = (1/12) * 6 = 1/2 ,
and upper_tail_numerators[1] / 8 = 4/8 = 1/2. The normalizing integral
int_0^1 t(1-t) dt = 1/2 - 1/3 = 1/6 is the value the proof of Theorem thm:binomial-tails
obtains from G(1) = 1 rather than from a table, which is why that proof appeals
to no tabulated identity.""",
        arithmetic="""\
n = 3, p = 1/2: binom(3,k) 2^{-3} = (1, 3, 3, 1)/8, summing to 1. Cdf
(1, 4, 7, 8)/8.
LOWER TAILS Pr[N < k]: 0, 1/8, 4/8, 7/8, 8/8 for k = 0, 1, 2, 3, 4.
UPPER TAILS Pr[N > k]: 7/8, 4/8, 1/8, 0 for k = 0, 1, 2, 3.
THIS TABLE IS WHAT THE n-NON-MONOTONICITY COUNTEREXAMPLE OF THEOREM
thm:monotonicity-limits (v) IS BUILT FROM, at the budget 2/5: Pr[N < 1] = 1/8 <= 2/5 while
Pr[N < 2] = 4/8 > 2/5 (compare 4*5 = 20 against 8), so kappa^- = 1; and
Pr[N > 1] = 4/8 > 2/5 while Pr[N > 2] = 1/8 <= 2/5, so kappa^+ = 2. The
companion n = 2 numbers come from BTAIL-n2-p-half at the same budget.""",
    ),
    BinomialTailCase(
        case_id="BTAIL-n4-p-half",
        n=4,
        p=Fraction(1, 2),
        denominator=16,
        pmf_numerators=(1, 4, 6, 4, 1),
        cdf_numerators=(1, 5, 11, 15, 16),
        lower_tail_numerators=(0, 1, 5, 11, 15, 16),
        upper_tail_numerators=(15, 11, 5, 1, 0),
        beta_cross_check="""\
Eq. eq:uppertail at k = 4:
  Pr[N >= 4] = I_{1/2}(4, 1) = int_0^{1/2} t^3 dt / int_0^1 t^3 dt
             = (1/64)/(1/4) = 1/16 = upper_tail_numerators[3] / 16 .
At k = 1, Eq. eq:uppertail reads I_{1/2}(1, 4)
= int_0^{1/2}(1-t)^3 dt / int_0^1 (1-t)^3 dt = (1/4 - 1/64)/(1/4) = 15/16,
matching upper_tail_numerators[0] / 16.""",
        arithmetic="""\
n = 4, p = 1/2: binom(4,k) 2^{-4} = (1, 4, 6, 4, 1)/16, sum 16/16. Cdf
(1, 5, 11, 15, 16)/16.
LOWER TAILS Pr[N < k]: 0, 1/16, 5/16, 11/16, 15/16, 1 for k = 0 .. 5.
UPPER TAILS Pr[N > k]: 15/16, 11/16, 5/16, 1/16, 0 for k = 0 .. 4.
USED BY ACC-raw-vs-tight-3letter at the single-outcome budget 1/4 = 4/16:
Pr[N < 1] = 1/16 <= 4/16 while Pr[N < 2] = 5/16 > 4/16, so kappa^- = 1;
Pr[N > 2] = 5/16 > 4/16 while Pr[N > 3] = 1/16 <= 4/16, so kappa^+ = 3. Both
comparisons are integer comparisons of numerators over 16, which is the sense
in which Theorem thm:sa3 (iv) calls the endpoints computable.""",
    ),
    BinomialTailCase(
        case_id="BTAIL-n10-p-half",
        n=10,
        p=Fraction(1, 2),
        denominator=1024,
        pmf_numerators=(1, 10, 45, 120, 210, 252, 210, 120, 45, 10, 1),
        cdf_numerators=(1, 11, 56, 176, 386, 638, 848, 968, 1013, 1023, 1024),
        lower_tail_numerators=(
            0,
            1,
            11,
            56,
            176,
            386,
            638,
            848,
            968,
            1013,
            1023,
            1024,
        ),
        upper_tail_numerators=(1023, 1013, 968, 848, 638, 386, 176, 56, 11, 1, 0),
        beta_cross_check="""\
Eq. eq:uppertail at k = 10 is the cheapest instance to check by integration:
  Pr[N >= 10] = I_{1/2}(10, 1) = int_0^{1/2} t^9 dt / int_0^1 t^9 dt
              = (2^{-10}/10) / (1/10) = 2^{-10} = 1/1024 ,
which is upper_tail_numerators[9] / 1024. The symmetric instance k = 1 gives
I_{1/2}(1, 10) = 1 - 2^{-10} = 1023/1024 = upper_tail_numerators[0] / 1024.""",
        arithmetic="""\
n = 10, p = 1/2, so every value has denominator 2^10 = 1024 and the numerators
are the binomial coefficients binom(10, k):
  1, 10, 45, 120, 210, 252, 210, 120, 45, 10, 1 ,
which sum to 1024 (check the partial sums below, whose last entry is 1024).
CUMULATIVE NUMERATORS, added left to right:
  1, 11, 56, 176, 386, 638, 848, 968, 1013, 1023, 1024 .
LOWER TAILS Pr[N < k] are that array shifted right with a leading 0; UPPER
TAILS Pr[N > k] are 1024 minus it.
THE THREE VALUES REMARK rem:guard NAMES, recovered here:
  Pr[N < 7] = Pr[N <= 6] = 848/1024 = 53/64 , and 53/64 <= 9/10 since
    530 <= 576 ;
  Pr[N < 8] = Pr[N <= 7] = 968/1024 = 121/128 , and 121/128 > 9/10 since
    1210 > 1152 ;
  Pr[N <= 5] = 638/1024 = 319/512 , the value eq:guard-lo0 compares 9/10
    against, and 9/10 > 319/512 since 4608 > 3190 -- so the guard is active,
  while eq:guard-lo1 compares 9/10 against Pr[N <= 6] = 53/64 and 9/10 exceeds
    it too, so the cost is MORE THAN ONE COUNT.
That is the whole of the rem:guard counterexample's arithmetic, and it is
reproduced independently in GUARD-lower-two-counts.""",
    ),
    BinomialTailCase(
        case_id="BTAIL-n8-p-three-quarters",
        n=8,
        p=Fraction(3, 4),
        denominator=65536,
        pmf_numerators=(1, 24, 252, 1512, 5670, 13608, 20412, 17496, 6561),
        cdf_numerators=(1, 25, 277, 1789, 7459, 21067, 41479, 58975, 65536),
        lower_tail_numerators=(0, 1, 25, 277, 1789, 7459, 21067, 41479, 58975, 65536),
        upper_tail_numerators=(
            65535,
            65511,
            65259,
            63747,
            58077,
            44469,
            24057,
            6561,
            0,
        ),
        beta_cross_check="""\
Eq. eq:uppertail at k = 8:
  Pr[N >= 8] = I_{3/4}(8, 1) = int_0^{3/4} t^7 dt / int_0^1 t^7 dt
             = ((3/4)^8 / 8) / (1/8) = (3/4)^8 = 6561/65536 ,
which is upper_tail_numerators[7] / 65536 and also pmf_numerators[8] / 65536,
as it must be.""",
        arithmetic="""\
n = 8, p = 3/4. Write every value over 4^8 = 65536:
  Pr[N = k] = binom(8,k) 3^k / 65536 ,
because 3^k * 1^{8-k} / 4^8 is exactly p^k (1-p)^{8-k}. With
binom(8,k) = 1, 8, 28, 56, 70, 56, 28, 8, 1 and 3^k = 1, 3, 9, 27, 81, 243,
729, 2187, 6561 the numerators are
  1, 24, 252, 1512, 5670, 13608, 20412, 17496, 6561 ,
and they sum to 65536: 1 + 24 = 25, +252 = 277, +1512 = 1789, +5670 = 7459,
+13608 = 21067, +20412 = 41479, +17496 = 58975, +6561 = 65536. Those running
totals ARE the cdf numerators.
THE TWO ENDPOINT DETERMINATIONS THIS TABLE FEEDS, both by integer comparison
against 65536/20 = 3276.8 (equivalently, numerator * 20 against 65536):
  at the budget 1/20, Pr[N <= 3] = 1789/65536 has 1789 * 20 = 35780 < 65536, so
    k = 4 is admissible in eq:kappaminus, while Pr[N <= 4] = 7459/65536 has
    7459 * 20 = 149180 > 65536, so k = 5 is not: kappa^- = 4 ;
  Pr[N >= 8] = 6561/65536 has 6561 * 20 = 131220 > 65536, so k = 7 is not
    admissible in eq:kappaplus, while Pr[N > 8] = 0: kappa^+ = 8 .
At the budget 1/5 the same comparisons (numerator * 5 against 65536) give
kappa^- = 5 and kappa^+ = 7. Both budgets are used in ACC-normal-2letter and
ACC-budget-large respectively.""",
    ),
    BinomialTailCase(
        case_id="BTAIL-n8-p-one-quarter",
        n=8,
        p=Fraction(1, 4),
        denominator=65536,
        pmf_numerators=(6561, 17496, 20412, 13608, 5670, 1512, 252, 24, 1),
        cdf_numerators=(6561, 24057, 44469, 58077, 63747, 65259, 65511, 65535, 65536),
        lower_tail_numerators=(
            0,
            6561,
            24057,
            44469,
            58077,
            63747,
            65259,
            65511,
            65535,
            65536,
        ),
        upper_tail_numerators=(58975, 41479, 21067, 7459, 1789, 277, 25, 1, 0),
        beta_cross_check="""\
The mirror identity inside the proof of Theorem thm:binomial-tails: n - N is binomial with
parameters (n, 1-p). Here that says Pr[N_{1/4} = k] = Pr[N_{3/4} = 8-k], and
indeed this pmf is BTAIL-n8-p-three-quarters' reversed. Eq. eq:lowertail is the
same statement, Pr[N <= k] = I_{1-p}(n-k, k+1); at k = 0 it gives
  Pr[N <= 0] = I_{3/4}(8, 1) = (3/4)^8 = 6561/65536 = cdf_numerators[0]/65536 .""",
        arithmetic="""\
n = 8, p = 1/4, over 4^8 = 65536: Pr[N = k] = binom(8,k) 3^{8-k} / 65536, so
the numerators are the previous case's reversed,
  6561, 17496, 20412, 13608, 5670, 1512, 252, 24, 1 ,
again summing to 65536. Running totals give the cdf.
WHY BOTH HALVES OF A TWO-LETTER ALPHABET ARE FROZEN. On Chat = {c0, c1} the
counts satisfy N_{c1} = n - N_{c0} identically (Lemma lem:freq-in-simplex), so
the two outcomes' tails are the SAME numbers read from opposite ends. That is
not a redundancy: it is what makes the union bound of Theorem thm:completeness-bound
double-count on a binary alphabet, and ACC-normal-2letter freezes the resulting
factor of exactly 2 between epsilon_star and the true failure probability.
THE ENDPOINTS THIS TABLE FEEDS. At the budget 1/20: Pr[N <= 0] = 6561/65536 has
6561 * 20 = 131220 > 65536, so k = 1 is inadmissible and kappa^- = 0; and
Pr[N >= 4] = 7459/65536 exceeds 1/20 while Pr[N >= 5] = 1789/65536 does not, so
kappa^+ = 4. At the budget 1/5: 6561 * 5 = 32805 < 65536 makes k = 1 admissible
and 24057 * 5 = 120285 > 65536 stops it there, so kappa^- = 1; and
Pr[N >= 3] = 21067/65536 exceeds 1/5 while Pr[N >= 4] = 7459/65536 does not, so
kappa^+ = 3.""",
    ),
)


O_SA_BINOMIAL_TAILS = SAOracleEntry(
    oracle_id="O-SA-BINOMIAL-TAILS",
    claims=("SA2",),
    kind="toy-instance",
    subject=(
        "The exact law and both exact tails of a binomial count at six small "
        "(n, p) pairs, with the pmf written out over a common denominator and "
        "the incomplete-beta form of Theorem thm:binomial-tails checked by integration."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:binomial-tails and Remark rem:tail-forms.

WHAT IS PINNED. For each case: the pmf Pr[N = k] = binom(n,k) p^k (1-p)^{n-k}
over a common denominator, the cdf Pr[N <= k], and BOTH tail arrays in the two
forms Eq. eq:tails-used fixes,
  Pr[N < k] = Pr[N <= k-1] , with Pr[N < 0] = 0 ,
  Pr[N > k] = Pr[N >= k+1] , with Pr[N > n] = 0 ,
indexed so that entry k is the value AT k. Those two arrays, and nothing else,
are what Definition def:interval compares a budget against, so they are the
smallest object an implementation of SA3 can be wrong about.

HOW EVERY NUMBER WAS OBTAINED. By hand: binomial coefficients from Pascal's
rule, powers of p and 1-p cleared to a common denominator (2^n, 4^n), and the
cdf by running partial sums whose last entry must equal the denominator -- the
check is written into each case's arithmetic and it is the only check needed,
a pmf summing to 1 with correct coefficients being determined.

THE BETA CROSS-CHECK IS A CHECK, NOT THE SOURCE. Theorem thm:binomial-tails proves
  Pr[N >= k] = I_p(k, n-k+1) ,
the regularized incomplete beta function of Eq. eq:ireg, and each case
evaluates that integral in closed form at one k and compares. The integrals are
polynomial and the normalizing constant is obtained inside the contract's own
proof from G(1) = 1 rather than from a table, so no external identity is
appealed to here either. Agreement is evidence that the summation route and the
integral route are the same function; the frozen numbers come from the sum.

WHY BOTH HALVES OF A TWO-LETTER ALPHABET APPEAR. n = 8 is frozen at p = 3/4 and
at p = 1/4, which on Chat = {c0, c1} are the SAME experiment read from the two
ends: N_{c1} = n - N_{c0} identically, because each round contributes exactly
one outcome (Lemma lem:freq-in-simplex). Theorem thm:completeness-bound nevertheless sums both
outcomes' tails, and on a binary alphabet with Chat_con = Chat that DOUBLE
COUNTS a single event. The consequence is frozen numerically in
ACC-normal-2letter and ACC-budget-large, where epsilon_star is exactly twice
the true failure probability. An implementation is not wrong to report the
larger figure -- the contract's epsilon_star is defined as that sum -- but a
reader who takes epsilon_star for the failure probability is.

BOUNDARY VALUES. Theorem thm:binomial-tails fixes Pr[N >= k] = 1 for k <= 0,
Pr[N >= k] = 0 for k > n, Pr[N <= k] = 0 for k < 0 and Pr[N <= k] = 1 for
k >= n. The frozen arrays carry the two that matter -- the leading 0 of every
lower-tail array and the trailing 0 of every upper-tail array -- because they
are exactly what makes the two sets of Eqs. eq:kappaminus and eq:kappaplus
non-empty, which is the whole of Theorem thm:sa3 (i).

MONOTONICITY IN k, the property the proof of Theorem thm:sa3 (iii) runs on: the
lower-tail array is non-decreasing and the upper-tail array non-increasing in
every case, visibly, because the cdf numerators increase. Monotonicity in p, the
last sentence of Theorem thm:binomial-tails, is not frozen as a table; it is used nowhere
below.

The six cases are in BINOMIAL_TAIL_CASES.
""",
    hypotheses=(
        "n >= 1 and p in [0, 1] (Theorem thm:binomial-tails hypotheses).",
        "p rational, so every value is an exact rational (Assumption A-EXACT).",
    ),
)


# ===========================================================================
#  Group SA-B -- the geometry taxonomy and its validation predicates (SA1)
# ===========================================================================
#
#  Definition def:taxonomy admits exactly TWO tags and no third; a consumer
#  presented with any other refuses rather than guessing. Theorem thm:geometry-validation proves
#  that every denoted set WHOSE VALIDATION PREDICATE HOLDS is non-empty, closed,
#  convex and compact in the simplex, which is how meat-core Assumption A-ACC is
#  discharged.
#
#  THE ORDER OF THE TWO CHECKS ON A CANONICAL BOX IS LOAD-BEARING. The
#  closed-form predicate Eq. eq:boxfeas, sum q^- <= 1 <= sum q^+, is proved
#  UNDER the hypothesis 0 <= q^- <= q^+ componentwise. Data violating that
#  hypothesis is not a canonical box at all, and running the sum test on it
#  first can return a pass on an empty set -- ILLFORMED-inverted below is that
#  case.


@dataclass(frozen=True)
class GeometryValidationCase:
    """One declared geometry, and the verdict its validation predicate gives."""

    case_id: str
    tag: str
    outcomes: tuple[str, ...]
    #: ``singleton`` data, else None.
    q_star: tuple[Fraction, ...] | None
    #: ``(q^-, q^+)`` when the data claims canonical box form, else None.
    box_bounds: tuple[tuple[Fraction, ...], tuple[Fraction, ...]] | None
    #: False when the data is not well formed for the form it CLAIMS, so the
    #: closed-form predicate is not applicable to it.
    well_formed: bool
    #: The verdict of the validation predicate of Definition def:taxonomy.
    predicate_holds: bool
    #: ``(sum q^-, sum q^+)`` for a box, else None.
    box_sums: tuple[Fraction, Fraction] | None
    #: The RATIONAL interpolation parameter of the (<=) direction of Theorem
    #: thm:geometry-validation (iii), and the point it produces. None when the predicate fails.
    theta_star: Fraction | None
    witness_point: tuple[Fraction, ...] | None
    arithmetic: str


GEOMETRY_VALIDATION_CASES: tuple[GeometryValidationCase, ...] = (
    GeometryValidationCase(
        case_id="VALID-box-interior",
        tag="polytope",
        outcomes=("c0", "c1", "c2"),
        q_star=None,
        box_bounds=(
            (Fraction(1, 4), Fraction(1, 4), Fraction(1, 4)),
            (Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)),
        ),
        well_formed=True,
        predicate_holds=True,
        box_sums=(Fraction(3, 4), Fraction(3, 2)),
        theta_star=Fraction(1, 3),
        witness_point=(Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)),
        arithmetic="""\
A WELL-FORMED CANONICAL BOX, and the case that supplies the RATIONAL witness.
  q^- = (1/4, 1/4, 1/4) , q^+ = (1/2, 1/2, 1/2) ,
componentwise 0 <= q^- <= q^+, so the closed form of Theorem thm:geometry-validation (iii)
applies. Sums: 3/4 <= 1 <= 3/2, so Eq. eq:boxfeas holds and the predicate
passes.
THE WITNESS, which is the point of this case. The (<=) direction of Theorem
thm:geometry-validation (iii) argues by the intermediate value theorem on
  theta |-> sum_chat q(theta)(chat) ,  q(theta) = q^- + theta (q^+ - q^-) ,
and the G3 signature records as judgement call (c) that the IVT
witness is REAL-VALUED where the predicate it certifies is rational. The map is
AFFINE, so the witness is available in closed form and is rational whenever the
data is:
  theta^* = (1 - sum q^-) / (sum q^+ - sum q^-)   when sum q^+ > sum q^- ,
  theta^* = 0                                     when sum q^+ = sum q^- ,
the second branch being legitimate because the two sums then both equal 1 and
q^- itself already sums to 1. Here
  theta^* = (1 - 3/4) / (3/2 - 3/4) = (1/4)/(3/4) = 1/3 ,
  q(theta^*) = 1/4 + (1/3)(1/4) = 1/4 + 1/12 = 1/3  in every coordinate,
so q(theta^*) = (1/3, 1/3, 1/3), which sums to 1, lies in the box and is
therefore an element of the denotation. NO IRRATIONAL NUMBER OCCURS.
Verification is by substitution: 1/4 <= 1/3 <= 1/2 in each coordinate and
3 * (1/3) = 1.""",
    ),
    GeometryValidationCase(
        case_id="VALID-box-both-sums-equal-one",
        tag="polytope",
        outcomes=("c0", "c1"),
        q_star=None,
        box_bounds=((Fraction(1), Fraction(0)), (Fraction(1), Fraction(0))),
        well_formed=True,
        predicate_holds=True,
        box_sums=(Fraction(1), Fraction(1)),
        theta_star=Fraction(0),
        witness_point=(Fraction(1), Fraction(0)),
        arithmetic="""\
THE DEGENERATE BRANCH OF THE WITNESS FORMULA, and the box ACC-degenerate-honest
-mass actually emits.
  q^- = q^+ = (1, 0) , so sum q^- = 1 = sum q^+ .
Eq. eq:boxfeas holds AT BOTH ENDS WITH EQUALITY, 1 <= 1 <= 1, and the
denotation is the single point {(1, 0)}. The general witness formula has
denominator sum q^+ - sum q^- = 0 and is therefore UNDEFINED here; the second
branch applies and theta^* = 0, giving q(0) = q^- = (1, 0), which sums to 1.
WHY THIS DESERVES A CASE. An implementation that computes theta^* by the
division alone divides by zero on data the contract calls admissible -- and
this is not an exotic input: it is exactly what Acc emits from a degenerate
honest distribution (Theorem thm:sa3 (v)), and Theorem thm:monotonicity-limits (vi) shows a
one-letter alphabet always lands here. The branch is not a special case bolted
on; it is where the affine map is CONSTANT and every theta is a witness.""",
    ),
    GeometryValidationCase(
        case_id="INVALID-box-caps-below-one",
        tag="polytope",
        outcomes=("c0", "c1", "c2"),
        q_star=None,
        box_bounds=(
            (Fraction(0), Fraction(0), Fraction(0)),
            (Fraction(1, 5), Fraction(1, 5), Fraction(1, 5)),
        ),
        well_formed=True,
        predicate_holds=False,
        box_sums=(Fraction(0), Fraction(3, 5)),
        theta_star=None,
        witness_point=None,
        arithmetic="""\
WELL-FORMED DATA DENOTING AN EMPTY SET, failing the RIGHT half of Eq. eq:boxfeas.
  q^- = (0, 0, 0) , q^+ = (1/5, 1/5, 1/5) ,
so 0 <= q^- <= q^+ holds and the closed form applies: sum q^- = 0 <= 1, but
sum q^+ = 3/5 < 1, so 1 <= sum q^+ FAILS.
DIRECT CERTIFICATE, checkable by substitution and independent of the closed
form: adding the three cap rows of Eq. eq:boxrows with multiplier 1 each gives
sum_chat q(chat) <= 3/5, while every point of the simplex has
sum_chat q(chat) = 1. Nonnegative multipliers, so this is a legitimate
consequence of the system.
WHAT ACC CANNOT DO. Theorem thm:honest-containment (iii) proves that on the input domain of
Section 2.1 the predicate is satisfied by the output of Acc UNCONDITIONALLY, so
this box is not reachable from any admissible input -- it is a DECLARED
geometry, which the taxonomy must still be able to reject. Theorem thm:box-construction (iii)
is why: p^hon always lies in the emitted set, so sum q^+ >= sum_chat p^hon = 1.""",
    ),
    GeometryValidationCase(
        case_id="INVALID-box-floors-above-one",
        tag="polytope",
        outcomes=("c0", "c1", "c2"),
        q_star=None,
        box_bounds=(
            (Fraction(2, 5), Fraction(2, 5), Fraction(2, 5)),
            (Fraction(4, 5), Fraction(4, 5), Fraction(4, 5)),
        ),
        well_formed=True,
        predicate_holds=False,
        box_sums=(Fraction(6, 5), Fraction(12, 5)),
        theta_star=None,
        witness_point=None,
        arithmetic="""\
THE MIRROR IMAGE, failing the LEFT half of Eq. eq:boxfeas -- frozen because the
predicate is a two-sided sandwich and an implementation that checks one side
accepts one of these two boxes.
  q^- = (2/5, 2/5, 2/5) , q^+ = (4/5, 4/5, 4/5) ,
well formed; sum q^- = 6/5 > 1 while 1 <= sum q^+ = 12/5 passes.
DIRECT CERTIFICATE: adding the three floor rows with multiplier 1 each gives
-sum_chat q(chat) <= -6/5, i.e. sum_chat q(chat) >= 6/5, incompatible with
sum_chat q(chat) = 1.
THE FAILURE MODE THIS FORBIDS. The SA8 residual r = 1 - sum q^- = -1/5 is
NEGATIVE here, and the fill rule "the least j whose prefix width reaches r" is
satisfied at the FIRST index by 0 >= -1/5, so a minimization that skips the
feasibility test returns q^- itself and reports a number for a set with no
points in it. Theorem thm:box-oracle (ii) is stated for a NON-EMPTY box and takes
r >= 0 from Theorem thm:geometry-validation (iii); outside that hypothesis it proves nothing.""",
    ),
    GeometryValidationCase(
        case_id="ILLFORMED-box-inverted",
        tag="polytope",
        outcomes=("c0", "c1", "c2"),
        q_star=None,
        box_bounds=(
            (Fraction(4, 5), Fraction(0), Fraction(0)),
            (Fraction(1, 5), Fraction(1), Fraction(1)),
        ),
        well_formed=False,
        predicate_holds=False,
        box_sums=(Fraction(4, 5), Fraction(11, 5)),
        theta_star=None,
        witness_point=None,
        arithmetic="""\
ILL-FORMED DATA, AND THE ONLY CASE HERE ON WHICH THE CLOSED-FORM TEST RETURNS A
PASS.
  q^- = (4/5, 0, 0) , q^+ = (1/5, 1, 1) .
Definition def:taxonomy requires 0 <= q^- <= q^+ COMPONENTWISE of a canonical
box, and at c0 the data has 4/5 > 1/5. So this is NOT a canonical box, and
Eq. eq:boxfeas -- proved under that hypothesis -- does not apply to it. Applied
anyway it reports
  sum q^- = 4/5 <= 1 <= 11/5 = sum q^+
and PASSES, declaring a non-empty set.
THE SET IS EMPTY: the c0 rows of Eq. eq:boxrows read q(c0) <= 1/5 and
q(c0) >= 4/5; adding them with multipliers (1, 1) annihilates the variable and
leaves 0 <= 1/5 - 4/5 = -3/5, which is false.
THE ORDER OF THE CHECKS IS THE CONTENT OF THIS CASE, and it is a WELL-FORMEDNESS
refusal rather than an emptiness one. The two must not be collapsed: a path that
runs the sum test without the componentwise test admits this box and then
computes a fill from the width q^+(c0) - q^-(c0) = -3/5, which is NEGATIVE. A
negative width breaks the fill's own hypotheses -- Theorem thm:box-oracle (ii) takes
D_i >= 0 from 0 <= q^- <= q^+ -- so the prefix sums are no longer monotone and
"the least index whose prefix reaches r" is not the index the exchange argument
justifies.
UNREACHABLE FROM Acc, for the same reason as the two INVALID cases: Theorem
thm:box-construction (ii) proves 0 <= q^- <= q^+ <= 1 for every admissible input.""",
    ),
    GeometryValidationCase(
        case_id="VALID-singleton",
        tag="singleton",
        outcomes=("c0", "c1"),
        q_star=(Fraction(1, 2), Fraction(1, 2)),
        box_bounds=None,
        well_formed=True,
        predicate_holds=True,
        box_sums=None,
        theta_star=None,
        witness_point=(Fraction(1, 2), Fraction(1, 2)),
        arithmetic="""\
THE OTHER TAG. Definition def:taxonomy: data is a vector q^* in Q^Chat, the
denotation is {q^*}, and the validation predicate is q^*(chat) >= 0 for every
chat together with sum_chat q^*(chat) = 1 -- that is, q^* in the simplex,
verbatim. Here (1/2, 1/2) is nonnegative and sums to 1, so the predicate holds.
Theorem thm:geometry-validation (ii) proves the predicate NECESSARY AND SUFFICIENT for the
denotation to be a non-empty subset of the simplex, which is stronger than what
(i) gives for a general polytope: for a singleton there is nothing to search.
NO INTERPOLATION WITNESS IS NEEDED and none is recorded; the witness point is
q^* itself.
THE SAME POINT IS ALSO EXPRESSIBLE AS A BOX -- take q^- = q^+ = (1/2, 1/2),
whose sums bracket 1 at both ends -- and the two routes must not disagree about
what the denotation is. Remark rem:two-tags settles the relation: the canonical
box form is a SUB-FORM of `polytope`, not a third tag. Remark
rem:singleton-honest settles who emits which: Acc NEVER emits `singleton`, and
the tag is in the taxonomy because a consumer's currently implemented acceptance
oracle reads exactly that geometry and because the consuming contract certifies
its acceptance-side minimum.""",
    ),
    GeometryValidationCase(
        case_id="INVALID-singleton-not-normalized",
        tag="singleton",
        outcomes=("c0", "c1"),
        q_star=(Fraction(1, 2), Fraction(1, 4)),
        box_bounds=None,
        well_formed=True,
        predicate_holds=False,
        box_sums=None,
        theta_star=None,
        witness_point=None,
        arithmetic="""\
q^* = (1/2, 1/4) is nonnegative but sums to 3/4, not 1, so the second half of
the singleton predicate fails and the denotation {q^*} is NOT a subset of the
simplex. By Theorem thm:geometry-validation (ii) that is decisive -- the predicate is necessary
as well as sufficient, so there is no reading on which this datum denotes an
admissible geometry.
WHY IT IS FROZEN. A singleton is the one geometry whose validation is a
MEMBERSHIP TEST rather than a feasibility question, which makes it the one an
implementation is most likely to skip. Skipping it here hands the consumer a
"distribution" of total mass 3/4, on which meat-core's acceptance-side
minimization is an evaluation at a point that is not a probability vector.""",
    ),
    GeometryValidationCase(
        case_id="INVALID-singleton-negative-coordinate",
        tag="singleton",
        outcomes=("c0", "c1"),
        q_star=(Fraction(3, 2), Fraction(-1, 2)),
        box_bounds=None,
        well_formed=True,
        predicate_holds=False,
        box_sums=None,
        theta_star=None,
        witness_point=None,
        arithmetic="""\
q^* = (3/2, -1/2) SUMS TO 1 and still fails: the first half of the predicate
asks q^*(chat) >= 0 for EVERY chat, and the second coordinate is negative.
Frozen because the normalization is the memorable half of the predicate and the
nonnegativity is the half a checksum-style test omits. The two conditions are
independent -- INVALID-singleton-not-normalized fails the other one alone --
and Definition def:taxonomy states both.""",
    ),
)


O_SA_GEOMETRY_VALIDATION = SAOracleEntry(
    oracle_id="O-SA-GEOMETRY-VALIDATION",
    claims=("SA1",),
    kind="structural-identity",
    subject=(
        "The validation predicates of the two admissible tags: the closed-form "
        "box predicate sum q^- <= 1 <= sum q^+ with a RATIONAL interpolation "
        "witness, the singleton membership test, and the well-formedness check "
        "that must run first."
    ),
    derivation="""\
contract.tex 0.1.2 Definition def:taxonomy and Theorem thm:geometry-validation.

WHAT IS PINNED. For each declared geometry: whether the DATA is well formed for
the form it claims, whether the validation predicate holds, the two box sums
when there is a box, and -- when the predicate holds -- an explicit point of the
denotation, which certifies non-emptiness by substitution rather than by an
existence argument.

THE RATIONAL WITNESS, and why it is worth an entry. Theorem thm:geometry-validation (iii)'s
(<=) direction proves non-emptiness of a canonical box by the intermediate value
theorem applied to theta |-> sum_chat q(theta)(chat) with
q(theta) = q^- + theta (q^+ - q^-). The G3 signature records as
judgement call (c) that this witness is real-valued where the predicate it
certifies is rational. It is re-derived here rather than copied: the map is AFFINE, so
  theta^* = (1 - sum q^-) / (sum q^+ - sum q^-)  if sum q^+ > sum q^- ,
  theta^* = 0                                    otherwise ,
and the second branch is correct because sum q^- <= 1 <= sum q^+ with the two
sums equal forces both to be 1. Both branches are frozen -- VALID-box-interior
and VALID-box-both-sums-equal-one -- because the degenerate one divides by zero
in the general formula and is exactly what Acc emits from a degenerate honest
distribution.

THE ORDER OF THE CHECKS. Eq. eq:boxfeas is proved UNDER the hypothesis
0 <= q^- <= q^+ componentwise, so well-formedness is decided FIRST and emptiness
second. ILLFORMED-box-inverted is data that passes the sum test and denotes an
empty set; it is the one case here whose refusal is a well-formedness refusal,
and an implementation may report it the same way as the others but may not reach
that conclusion by the sum test.

WHAT Acc CAN AND CANNOT PRODUCE. Three of these eight cases are UNREACHABLE from
any admissible input: Theorem thm:box-construction (ii) gives 0 <= q^- <= q^+ <= 1 and
(iii) gives p^hon in AcceptSet, whence sum q^- <= 1 <= sum q^+ automatically.
That is Theorem thm:honest-containment (iii)'s first sentence -- the predicate holds
UNCONDITIONALLY on the output of Acc -- so every infeasibility report this
module emits originates in an input-domain violation and never in the
construction. The invalid cases are DECLARED geometries, which the taxonomy must
still reject, and they exist here so that the rejection path is exercised on
data the construction path cannot supply.

RELATION TO THE meat-core REGISTRY. Group 8 of registry.py pins overlapping
verdicts from the CONSUMER's side, under meat-core claim C19. Nothing here is
taken from it: the numbers differ deliberately (fifths rather than quarters), the
claims pinned are different, and the derivations above stand alone. Two
registries reaching compatible verdicts from two contracts is evidence; it is
not this file's source.

The eight cases are in GEOMETRY_VALIDATION_CASES.
""",
    hypotheses=(
        "Definition def:taxonomy admits exactly two tags; any other tag is "
        "refused rather than guessed.",
        "The closed form Eq. eq:boxfeas is proved only for a canonical box, "
        "i.e. under 0 <= q^- <= q^+ componentwise.",
    ),
)


# ===========================================================================
#  Group SA-C -- the per-outcome interval and the honest-containment guard
#                (SA3)
# ===========================================================================
#
#  Definition def:interval fixes the extremal endpoints
#      kappa^-(chat) = max { k in {0..n} : Pr[N < k] <= eps^-(chat) }
#      kappa^+(chat) = min { k in {0..n} : Pr[N > k] <= eps^+(chat) }
#  and then the EMITTED endpoints after the guard, Eq. eq:guard,
#      k^-(chat) = min { kappa^-(chat), floor(n p) }
#      k^+(chat) = max { kappa^+(chat), ceil(n p) } .
#
#  Theorem thm:sa3 (vi) gives the exact cost of that guard and FOUR iff
#  conditions, and Remark rem:guard insists the two PAIRS be read apart:
#      eq:guard-lo0 / eq:guard-up0  --  the guard is INERT (cost 0)
#      eq:guard-lo1 / eq:guard-up1  --  the guard costs AT MOST ONE COUNT
#  The pairs fail in different regimes. The lo1/up1 pair fails only when a
#  single tail carries a near-unit budget; the lo0/up0 pair fails AT ORDINARY
#  BUDGETS UNDER THE DEFAULT UNIFORM RULE, for any outcome whose expected count
#  over the whole run is positive and at or below its allocated tail budget.
#  Both regimes are frozen below, on the contract's own instances.


@dataclass(frozen=True)
class GuardCase:
    """One outcome's interval, before and after the honest-containment guard."""

    case_id: str
    n: int
    p: Fraction
    eps_lower: Fraction
    eps_upper: Fraction
    #: The extremal endpoints of Eqs. eq:kappaminus and eq:kappaplus.
    kappa_lower: int
    kappa_upper: int
    #: The emitted endpoints of Eq. eq:guard.
    k_lower: int
    k_upper: int
    floor_np: int
    ceil_np: int
    #: Eq. eq:guard-cost: kappa^- - k^- and k^+ - kappa^+, in counts.
    lower_enlargement: int
    upper_enlargement: int
    #: The four iff conditions of Theorem thm:sa3 (vi), as verdicts.
    guard_lo0_holds: bool
    guard_lo1_holds: bool
    guard_up0_holds: bool
    guard_up1_holds: bool
    #: Eq. eq:guard-from-p: p - k^-/n and k^+/n - p, both in [0, 1].
    distance_below_p: Fraction
    distance_above_p: Fraction
    #: False when the tail values are too large to write out; then the
    #: determination rests on the rigorous inequality in `tail_certificate`.
    tails_frozen: bool
    tail_certificate: str
    arithmetic: str


GUARD_CASES: tuple[GuardCase, ...] = (
    GuardCase(
        case_id="GUARD-inert",
        n=8,
        p=Fraction(3, 4),
        eps_lower=Fraction(1, 20),
        eps_upper=Fraction(1, 20),
        kappa_lower=4,
        kappa_upper=8,
        k_lower=4,
        k_upper=8,
        floor_np=6,
        ceil_np=6,
        lower_enlargement=0,
        upper_enlargement=0,
        guard_lo0_holds=True,
        guard_lo1_holds=True,
        guard_up0_holds=True,
        guard_up1_holds=True,
        distance_below_p=Fraction(1, 4),
        distance_above_p=Fraction(1, 4),
        tails_frozen=True,
        tail_certificate="BTAIL-n8-p-three-quarters, read at the budget 1/20.",
        arithmetic="""\
THE BASELINE: THE GUARD DOES NOTHING. n = 8, p = 3/4, both tail budgets 1/20.
From BTAIL-n8-p-three-quarters, comparing numerators over 65536 against
65536/20 (equivalently numerator * 20 against 65536):
  Pr[N < 4] = Pr[N <= 3] = 1789/65536 , 1789 * 20 = 35780 < 65536 , admissible ;
  Pr[N < 5] = Pr[N <= 4] = 7459/65536 , 7459 * 20 = 149180 > 65536 , not ;
so kappa^- = 4. And
  Pr[N > 7] = 6561/65536 , 6561 * 20 = 131220 > 65536 , k = 7 not admissible ;
  Pr[N > 8] = 0 , admissible ;
so kappa^+ = 8.
GUARD: n p = 6 exactly, so floor(n p) = ceil(n p) = 6, and Eq. eq:guard gives
  k^- = min{4, 6} = 4 ,  k^+ = max{8, 6} = 8 ,
i.e. both enlargements are 0 and the emitted interval IS the raw quantile
interval.
THE FOUR CONDITIONS, all holding, checked directly rather than inferred from the
zero cost:
  eq:guard-lo0 : eps^- < Pr[N <= floor(n p)] = Pr[N <= 6] = 41479/65536 , and
    1/20 < 41479/65536 since 65536 < 829580 ;
  eq:guard-lo1 : eps^- < Pr[N <= 7] = 58975/65536 , a fortiori ;
  eq:guard-up0 : eps^+ < Pr[N >= ceil(n p)] = Pr[N >= 6] = 44469/65536 , and
    1/20 < 44469/65536 since 65536 < 889380 ;
  eq:guard-up1 : eps^+ < Pr[N >= 5] = 58077/65536 , a fortiori .
DISTANCES FROM THE HONEST VALUE, Eq. eq:guard-from-p:
  p - k^-/n = 3/4 - 4/8 = 1/4 ,  k^+/n - p = 8/8 - 3/4 = 1/4 ,
both non-negative, which is the ordering chain Eq. eq:ordering. The 1/n clause
of eq:guard-from-p bounds the emitted endpoint's distance only ON THE SIDE THE
GUARD ACTS, and here it acts on neither, so 1/4 > 1/8 is no violation --
reading that bound as unconditional is the misreading Remark rem:guard warns
against.""",
    ),
    GuardCase(
        case_id="GUARD-lower-two-counts",
        n=10,
        p=Fraction(1, 2),
        eps_lower=Fraction(9, 10),
        eps_upper=Fraction(1, 20),
        kappa_lower=7,
        kappa_upper=8,
        k_lower=5,
        k_upper=8,
        floor_np=5,
        ceil_np=5,
        lower_enlargement=2,
        upper_enlargement=0,
        guard_lo0_holds=False,
        guard_lo1_holds=False,
        guard_up0_holds=True,
        guard_up1_holds=True,
        distance_below_p=Fraction(0),
        distance_above_p=Fraction(3, 10),
        tails_frozen=True,
        tail_certificate="BTAIL-n10-p-half, read at the budgets 9/10 and 1/20.",
        arithmetic="""\
THE lo1 PAIR FAILING: A COST OF MORE THAN ONE COUNT. This is Remark rem:guard's
own counterexample, re-derived from BTAIL-n10-p-half rather than copied.
  n = 10 , p = 1/2 , eps^- = 9/10 , eps^+ = 1/20 ,
the allocation summing to 9/10 + 1/20 = 19/20, hence admissible for any
ecomp in [19/20, 1).
LOWER ENDPOINT. Numerators over 1024, compared against 9/10 by cross
multiplication (numerator * 10 against 1024 * 9 = 9216):
  Pr[N < 7] = Pr[N <= 6] = 848/1024 , 8480 <= 9216 , admissible ;
  Pr[N < 8] = Pr[N <= 7] = 968/1024 , 9680 > 9216 , not admissible ;
so kappa^- = 7. In lowest terms those are 53/64 <= 9/10 and 121/128 > 9/10,
which is the pair of comparisons Remark rem:guard states.
UPPER ENDPOINT, against 1/20 (numerator * 20 against 1024):
  Pr[N > 7] = 56/1024 , 1120 > 1024 , not admissible ;
  Pr[N > 8] = 11/1024 , 220 < 1024 , admissible ;
so kappa^+ = 8.
GUARD: n p = 5, floor = ceil = 5, so k^- = min{7, 5} = 5 and
k^+ = max{8, 5} = 8. Eq. eq:guard-cost gives
  lower enlargement = kappa^- - k^- = max{0, 7 - 5} = 2 COUNTS ,
  upper enlargement = k^+ - kappa^+ = max{0, 5 - 8} = 0 .
TWO COUNTS IS MORE THAN ONE, and the iff conditions say exactly why:
  eq:guard-lo0 asks eps^- < Pr[N <= floor(n p)] = Pr[N <= 5] = 638/1024, i.e.
    9/10 < 319/512; cross multiplying, 4608 > 3190, so it FAILS -- the guard is
    active at all ;
  eq:guard-lo1 asks eps^- < Pr[N <= 6] = 848/1024 = 53/64, i.e. 9/10 < 53/64;
    4608 > 3392 in the cross multiplication 9 * 512 against 53 * 80... written
    plainly, 9/10 = 0.9 and 53/64 = 0.828125, so it FAILS TOO -- the cost
    exceeds one count.
  eq:guard-up0 asks eps^+ < Pr[N >= ceil(n p)] = Pr[N >= 5] = 638/1024, and
    1/20 < 319/512 holds, so the upper side is inert, as computed.
  eq:guard-up1 then holds a fortiori.
THE REGIME. Remark rem:guard's closing paragraphs name it: a cost above one
count requires a SINGLE OUTCOME'S SINGLE TAIL to carry a budget exceeding the
mass the count law places up to one step beyond n p, and here eps^- = 9/10
against Pr[N <= 6] = 53/64 is exactly that -- a near-unit budget. The sharp
threshold the G3 signature records as judgement call (a) is that a single-tail
budget of at least 1/2 is what is needed, via median bracketing; 9/10 is well
past it.
UNBOUNDEDNESS, the second half of Theorem thm:sa3 (vi). Push the same tail
further: any eps^- >= 1 - p^n = 1 - 2^{-10} = 1023/1024 makes k = n = 10
admissible in eq:kappaminus, so kappa^- = 10 and the lower enlargement becomes
10 - 5 = 5 counts. The contract proves this happens for every n and every
p in (0, 1), the enlargement approaching 1 - p in FREQUENCY uniformly in n, so
no bound of the form "at most one count" survives against the raw quantile
interval.
DISTANCES FROM THE HONEST VALUE:
  p - k^-/n = 1/2 - 5/10 = 0 ,  k^+/n - p = 8/10 - 1/2 = 3/10 .
The guard acts on the LOWER side, and there the distance is 0 <= 1/n = 1/10, in
agreement with Eq. eq:guard-from-p. THAT IS THE POINT OF THE SECOND MEASURE: the
enlargement against the raw interval is 2 counts and unbounded in general, while
the distance from p on the guarded side is at most 1/n always. Both statements
are true and Theorem thm:sa3 (vi) records both, because reporting only the
second overstates the guarantee.""",
    ),
    GuardCase(
        case_id="GUARD-upper-active-uniform",
        n=10,
        p=Fraction(1, 1000),
        eps_lower=Fraction(1, 40),
        eps_upper=Fraction(1, 40),
        kappa_lower=0,
        kappa_upper=0,
        k_lower=0,
        k_upper=1,
        floor_np=0,
        ceil_np=1,
        lower_enlargement=0,
        upper_enlargement=1,
        guard_lo0_holds=True,
        guard_lo1_holds=True,
        guard_up0_holds=False,
        guard_up1_holds=True,
        distance_below_p=Fraction(1, 1000),
        distance_above_p=Fraction(99, 1000),
        tails_frozen=True,
        tail_certificate="""\
Pr[N > 0] = 1 - (999/1000)^10 = 1 - 999^10/10^30, with
999^10 = 990044880209748209880044990001, so
Pr[N > 0] = 9955119790251790119955009999/10^30, which is below 1/40 = 0.025
since it is below 10^-2. The determination needs only the Bernoulli bound
1 - (1-p)^n <= n p = 1/100 <= 1/40, and that bound is what the contract uses.""",
        arithmetic="""\
THE up0 PAIR FAILING AT AN ORDINARY BUDGET, UNDER THE DEFAULT UNIFORM RULE. This
is the outcome c1 of Remark rem:guard's own n = 10 instance:
  Chat = {c0, c1} , p^hon = (999/1000, 1/1000) , n = 10 , Chat_con = Chat ,
  ecomp = 1/10 , uniform allocation eps^{+-} = ecomp/(2 |Chat_con|) = 1/40 .
Here p = p^hon(c1) = 1/1000 and n p = 1/100, so floor(n p) = 0 and
ceil(n p) = 1.
UPPER ENDPOINT. Is k = 0 admissible in eq:kappaplus, i.e. is
Pr[N > 0] <= 1/40? Bernoulli's inequality (1 - p)^n >= 1 - n p, valid for
p in [0, 1], gives
  Pr[N > 0] = 1 - (1 - p)^n <= n p = 1/100 <= 1/40 ,
so YES and kappa^+ = 0, the smallest index there is. The exact value is in
tail_certificate and confirms it, but the INEQUALITY is the derivation: it is
what makes the conclusion independent of evaluating a 30-digit rational.
GUARD: k^+ = max{kappa^+, ceil(n p)} = max{0, 1} = 1. THE GUARD RAISES THE
EMITTED ENDPOINT BY EXACTLY ONE COUNT, and without it q^+(c1) would be 0 -- a
box forbidding the honest outcome to occur at all, on an outcome the honest
channel produces with positive probability.
LOWER ENDPOINT. Is k = 1 admissible in eq:kappaminus, i.e. is
Pr[N < 1] = (1 - p)^n <= 1/40? Bernoulli again, the other way:
  (1 - p)^n >= 1 - n p = 1 - 1/100 = 99/100 > 1/40 ,
so NO, and kappa^- = 0. Guard: k^- = min{0, floor(n p)} = min{0, 0} = 0, inert.
THE FOUR CONDITIONS:
  eq:guard-up0 asks eps^+ < Pr[N >= ceil(n p)] = Pr[N >= 1] = Pr[N > 0], and
    that is 1/40 < (something at most 1/100), which is FALSE -- the guard is
    active ;
  eq:guard-up1 asks eps^+ < Pr[N >= ceil(n p) - 1] = Pr[N >= 0] = 1, and
    1/40 < 1 is TRUE -- so the cost is at most one count, and being nonzero it
    is exactly one. This is one of the two END-OF-RANGE cases Remark rem:guard
    names as unable to fail: n p < 1 forces ceil(n p) - 1 <= 0 and the tail
    is 1 > eps^+ because eps^+ <= ecomp < 1 ;
  eq:guard-lo0 asks eps^- < Pr[N <= floor(n p)] = Pr[N <= 0] = (1-p)^n, and
    1/40 < 99/100 holds, so the lower side is inert ;
  eq:guard-lo1 then holds a fortiori.
THE REGIME, and why no profile may assume it away. The sufficient condition
Remark rem:guard proves is 0 < n p <= eps^+, and it holds here at
n p = 1/100 <= 1/40 -- AT A BUDGET NOWHERE NEAR 1, AND WITH THE BUDGET SPREAD
UNIFORMLY RATHER THAN CONCENTRATED. Under Assumption A-TSM the acceptance
alphabet is the JOINT outcome, carrying every per-round public choice, so
outcomes of expected count at or below one are a routine feature of a
fine-grained Chat rather than an exotic one.
DISTANCES: p - k^-/n = 1/1000 - 0 = 1/1000 and
k^+/n - p = 1/10 - 1/1000 = 99/1000. On the side the guard acts (the upper),
99/1000 <= 1/n = 1/10 = 100/1000, in agreement with Eq. eq:guard-from-p and with
nothing to spare -- the bound is nearly attained.""",
    ),
    GuardCase(
        case_id="GUARD-lower-active-uniform",
        n=10,
        p=Fraction(999, 1000),
        eps_lower=Fraction(1, 40),
        eps_upper=Fraction(1, 40),
        kappa_lower=10,
        kappa_upper=10,
        k_lower=9,
        k_upper=10,
        floor_np=9,
        ceil_np=10,
        lower_enlargement=1,
        upper_enlargement=0,
        guard_lo0_holds=False,
        guard_lo1_holds=True,
        guard_up0_holds=True,
        guard_up1_holds=True,
        distance_below_p=Fraction(99, 1000),
        distance_above_p=Fraction(1, 1000),
        tails_frozen=True,
        tail_certificate="""\
Pr[N < 10] = Pr[N <= 9] = 1 - p^10 = 1 - (999/1000)^10
= 9955119790251790119955009999/10^30, below 1/40 for the same reason as
GUARD-upper-active-uniform: the Bernoulli bound 1 - (1-x)^n <= n x applied at
x = 1 - p = 1/1000 gives 1 - p^10 <= 10/1000 = 1/100 <= 1/40.""",
        arithmetic="""\
THE MIRROR OF GUARD-upper-active-uniform, on the OTHER outcome of the same
instance: p = p^hon(c0) = 999/1000, n = 10, uniform eps^{+-} = 1/40.
  n p = 999/100 = 9.99 , floor(n p) = 9 , ceil(n p) = 10 .
LOWER ENDPOINT. Is k = 10 = n admissible in eq:kappaminus, i.e.
Pr[N < 10] <= 1/40? With x = 1 - p = 1/1000, Bernoulli gives
p^n = (1 - x)^n >= 1 - n x = 99/100, so
  Pr[N < 10] = 1 - p^n <= n x = 1/100 <= 1/40 ,
YES, and since 10 is the largest index available, kappa^- = 10.
GUARD: k^- = min{10, 9} = 9. THE GUARD LOWERS THE EMITTED ENDPOINT BY EXACTLY
ONE COUNT. Without it q^-(c0) would be 1, forcing every accepted frequency
vector to put ALL its mass on c0 -- which the honest run achieves only when c1
never occurs.
UPPER ENDPOINT. Is k = 9 admissible in eq:kappaplus, i.e. Pr[N > 9] <= 1/40?
Pr[N > 9] = Pr[N = 10] = p^n >= 99/100 > 1/40, so NO; k = 10 gives
Pr[N > 10] = 0, so kappa^+ = 10. Guard: k^+ = max{10, 10} = 10, inert.
THE FOUR CONDITIONS:
  eq:guard-lo0 asks eps^- < Pr[N <= floor(n p)] = Pr[N <= 9] = 1 - p^n, and
    1/40 < (something at most 1/100) is FALSE -- the guard is active ;
  eq:guard-lo1 asks eps^- < Pr[N <= floor(n p) + 1] = Pr[N <= 10] = 1, TRUE,
    so the cost is at most one count and hence exactly one. This is the OTHER
    end-of-range case Remark rem:guard names: floor(n p) >= n - 1 forces the
    tail to be 1, and 1 > eps^- because eps^- <= ecomp < 1 ;
  eq:guard-up0 asks eps^+ < Pr[N >= ceil(n p)] = Pr[N >= 10] = p^n, and
    1/40 < 99/100 holds, so the upper side is inert ;
  eq:guard-up1 a fortiori.
THE SUFFICIENT CONDITION, in the contract's mirrored form: 0 < n(1 - p) <=
eps^-, here 10/1000 = 1/100 <= 1/40. Both halves of that instance therefore
activate the guard on the same run, on opposite sides of opposite outcomes, and
together they are what ACC-guard-active-uniform assembles.
DISTANCES: p - k^-/n = 999/1000 - 9/10 = 99/1000 <= 1/10 = 1/n on the side the
guard acts; k^+/n - p = 1 - 999/1000 = 1/1000 on the inert side.""",
    ),
    GuardCase(
        case_id="GUARD-fine-alphabet-million-rounds",
        n=1000000,
        p=Fraction(1, 1000000000),
        eps_lower=Fraction(1, 100),
        eps_upper=Fraction(1, 100),
        kappa_lower=0,
        kappa_upper=0,
        k_lower=0,
        k_upper=1,
        floor_np=0,
        ceil_np=1,
        lower_enlargement=0,
        upper_enlargement=1,
        guard_lo0_holds=True,
        guard_lo1_holds=True,
        guard_up0_holds=False,
        guard_up1_holds=True,
        distance_below_p=Fraction(1, 1000000000),
        distance_above_p=Fraction(999, 1000000000),
        tails_frozen=False,
        tail_certificate="""\
THE TAIL VALUES ARE NOT FROZEN, DELIBERATELY. Pr[N > 0] = 1 - (1 - 10^-9)^{10^6}
is an exact rational with roughly 10^7 digits, and writing it down would put a
number in this registry that no reader can check. The determination does not
need it. Bernoulli's inequality (1 - x)^m >= 1 - m x, valid for x in [0, 1],
gives the two rigorous bounds the endpoints turn on:
  Pr[N > 0] = 1 - (1 - p)^n <= n p = 10^6 * 10^-9 = 10^-3 <= 10^-2 = eps^+ ,
    so k = 0 IS admissible in eq:kappaplus and kappa^+ = 0 ;
  Pr[N < 1] = (1 - p)^n >= 1 - n p = 1 - 10^-3 = 999/1000 > 10^-2 = eps^- ,
    so k = 1 is NOT admissible in eq:kappaminus and kappa^- = 0 .
Both are inequalities in the CONSERVATIVE direction for the conclusion they
support, so no rounding question arises. What is frozen is the pair of integers
(kappa, k) and the resulting rational q^+ = 1/n = 10^-6.""",
        arithmetic="""\
THE SAME REGIME AT REALISTIC SCALE, and the instance Remark rem:guard gives to
rule out reading the lo0/up0 failure as a small-n artefact.
  n = 10^6 , ecomp = 1/10 , |Chat_con| = 5 , so the DEFAULT uniform rule
  allocates eps^{+-}(chat) = ecomp / (2 |Chat_con|) = (1/10)/10 = 10^-2 ,
and a constrained outcome of honest probability p = 10^-9 has n p = 10^-3.
Since 0 < n p <= eps^+, the sufficient condition of Remark rem:guard applies and
eq:guard-up0 fails.
THE NUMBERS. floor(n p) = 0 and ceil(n p) = 1 because 0 < n p = 10^-3 < 1.
kappa^+ = 0 and kappa^- = 0 by the two Bernoulli bounds in tail_certificate.
Eq. eq:guard then gives
  k^- = min{0, 0} = 0 ,  k^+ = max{0, 1} = 1 ,
so the emitted box bounds for this outcome are
  q^-(chat) = 0 ,  q^+(chat) = 1/n = 10^-6 ,
WHERE THE RAW QUANTILE INTERVAL WOULD HAVE GIVEN q^+(chat) = 0. That is the
whole content of the instance: at a hundredth of a per-cent tail budget on a
million rounds, the guard is what keeps a rare-but-real outcome from being
forbidden outright.
COST, BOUNDED BY BOTH MEASURES. Exactly one count, since eq:guard-up1 holds
(ceil(n p) - 1 = 0 and Pr[N >= 0] = 1 > eps^+); and at most 1/n from the honest
value, since k^+/n - p = 10^-6 - 10^-9 = 999 * 10^-9 <= 10^-6 = 1/n.
WHY THIS MATTERS FOR THE PROFILE. Under Assumption A-TSM every per-round public
choice of known bias is a component of the declared joint outcome, so Chat is
the joint alphabet and fine-grained by construction. An implementation tuned on
a two-outcome toy will never see this branch; a real declaration hits it on the
first rare joint outcome.""",
    ),
    GuardCase(
        case_id="GUARD-degenerate-p-zero",
        n=4,
        p=Fraction(0),
        eps_lower=Fraction(1, 8),
        eps_upper=Fraction(1, 8),
        kappa_lower=0,
        kappa_upper=0,
        k_lower=0,
        k_upper=0,
        floor_np=0,
        ceil_np=0,
        lower_enlargement=0,
        upper_enlargement=0,
        guard_lo0_holds=True,
        guard_lo1_holds=True,
        guard_up0_holds=True,
        guard_up1_holds=True,
        distance_below_p=Fraction(0),
        distance_above_p=Fraction(0),
        tails_frozen=True,
        tail_certificate=(
            "N = 0 with probability one, so Pr[N > k] = 0 for every k >= 0 and "
            "Pr[N < k] = 0 for k = 0, = 1 for k >= 1. Both emitted tails are "
            "EXACTLY ZERO."
        ),
        arithmetic="""\
DEGENERATE HONEST MASS, Theorem thm:sa3 (v), first half. p = 0 makes N = 0 with
probability one.
  eq:kappaplus : Pr[N > k] = 0 <= 1/8 for every k >= 0, so the minimum is
    kappa^+ = 0 ;
  eq:kappaminus : Pr[N < 0] = 0 <= 1/8 admits k = 0, while Pr[N < 1] =
    Pr[N = 0] = 1 > 1/8 rejects k = 1, so kappa^- = 0 .
GUARD: n p = 0, floor = ceil = 0, so k^- = min{0, 0} = 0 and
k^+ = max{0, 0} = 0. The emitted interval is [0, 0], exactly as Theorem
thm:sa3 (v) states, and the box bounds are q^- = q^+ = 0.
BOTH BUDGETS ARE UNSPENT: Pr[N < k^-] = Pr[N < 0] = 0 and Pr[N > k^+] =
Pr[N > 0] = 0, both EXACTLY zero, so this outcome contributes nothing at all to
epsilon_star (Theorem thm:completeness-bound, Eq. eq:completeness). Remark rem:epsstar names
this as one of the reasons epsilon_star is generally strictly below ecomp.
THE CONSEQUENCE FOR THE ACCEPTANCE SUPPORT. q^+(chat) = 0 puts chat OUTSIDE
Chat_acc = {chat : q^+(chat) > 0} of Theorem thm:box-oracle (i) -- the only way the
construction map produces a support smaller than Chat on a constrained
outcome. ACC-degenerate-honest-mass freezes that.""",
    ),
    GuardCase(
        case_id="GUARD-degenerate-p-one",
        n=4,
        p=Fraction(1),
        eps_lower=Fraction(1, 8),
        eps_upper=Fraction(1, 8),
        kappa_lower=4,
        kappa_upper=4,
        k_lower=4,
        k_upper=4,
        floor_np=4,
        ceil_np=4,
        lower_enlargement=0,
        upper_enlargement=0,
        guard_lo0_holds=True,
        guard_lo1_holds=True,
        guard_up0_holds=True,
        guard_up1_holds=True,
        distance_below_p=Fraction(0),
        distance_above_p=Fraction(0),
        tails_frozen=True,
        tail_certificate=(
            "N = n = 4 with probability one, so Pr[N < k] = 0 for every k <= 4 "
            "and Pr[N > k] = 1 for k < 4, = 0 for k = 4. Both emitted tails are "
            "EXACTLY ZERO."
        ),
        arithmetic="""\
DEGENERATE HONEST MASS, Theorem thm:sa3 (v), second half. p = 1 makes N = n = 4
with probability one.
  eq:kappaminus : Pr[N < k] = 0 <= 1/8 for every k <= 4, so the MAXIMUM is
    kappa^- = 4 ;
  eq:kappaplus : Pr[N > 3] = 1 > 1/8 rejects k = 3, while Pr[N > 4] = 0 admits
    k = 4, so kappa^+ = 4 .
GUARD: n p = 4, floor = ceil = 4, so k^- = min{4, 4} = 4 and
k^+ = max{4, 4} = 4. The emitted interval is [n, n] = [4, 4], exactly as
Theorem thm:sa3 (v) states, and the box bounds are q^- = q^+ = 1.
BOTH BUDGETS UNSPENT, both emitted tails exactly zero.
THIS IS THE ONE-LETTER ALPHABET'S ONLY CASE. Theorem thm:monotonicity-limits (vi): on
Chat = {c0} the input domain forces p^hon = delta_{c0}, i.e. p = 1, so the
construction is CONSTANT in n, ecomp and the allocation and returns the single
point. ACC-one-letter-constrained freezes that, and the asymmetry with p = 0 --
kappa^- runs to n here and to 0 there -- is why both halves of Theorem
thm:sa3 (v) are frozen separately.""",
    ),
)


O_SA_GUARD_COST = SAOracleEntry(
    oracle_id="O-SA-GUARD-COST",
    claims=("SA3",),
    kind="toy-instance",
    subject=(
        "The extremal endpoints kappa^{+-}, the emitted endpoints after the "
        "honest-containment guard, the exact guard cost in counts and in "
        "distance from the honest value, and the verdicts of all four iff "
        "conditions of Theorem thm:sa3 (vi) -- in both regimes Remark "
        "rem:guard separates, plus both degenerate honest masses."
    ),
    derivation="""\
contract.tex 0.1.2 Definition def:interval, Theorem thm:sa3 and Remark
rem:guard.

WHAT IS PINNED, per outcome: kappa^-, kappa^+ from Eqs. eq:kappaminus and
eq:kappaplus; floor(n p) and ceil(n p); the emitted k^-, k^+ from Eq. eq:guard;
the two enlargements of Eq. eq:guard-cost; the four verdicts of
Eqs. eq:guard-lo0, eq:guard-lo1, eq:guard-up0, eq:guard-up1; and the two
distances of Eq. eq:guard-from-p.

HOW THE ENDPOINTS WERE OBTAINED. By reading the frozen tail arrays of Group SA-A
and comparing each against the budget BY CROSS MULTIPLICATION OF INTEGERS -- the
arithmetic is written out in every case. Two cases have tails too large to
tabulate, and there the determination rests on Bernoulli's inequality
(1 - x)^m >= 1 - m x in the direction that is conservative for the conclusion,
which is the same argument Remark rem:guard uses; those cases carry
tails_frozen = False and their inequality in tail_certificate.

WHY BOTH CONDITION PAIRS ARE FROZEN, AND SEPARATELY. Remark rem:guard's closing
paragraphs exist because the two pairs fail in DIFFERENT REGIMES and "must not
be read together":
  the lo1/up1 pair -- cost above one count -- requires a single outcome's single
    tail to carry a near-unit budget, and CANNOT fail at either end of the range
    (n p < 1 on the upper side, floor(n p) >= n - 1 on the lower), because
    eps^{+-} <= ecomp < 1. GUARD-lower-two-counts is that regime: eps^- = 9/10
    against Pr[N <= 6] = 53/64, giving a two-count enlargement, on the
    contract's own instance ;
  the lo0/up0 pair -- guard active at all -- FAILS AT ORDINARY BUDGETS UNDER THE
    DEFAULT UNIFORM RULE, whenever 0 < n p <= eps^+ (or 0 < n(1-p) <= eps^-).
    GUARD-upper-active-uniform and GUARD-lower-active-uniform are the two halves
    of the contract's n = 10 instance at ecomp = 1/10 with the budget spread
    uniformly, and GUARD-fine-alphabet-million-rounds is the same regime at
    n = 10^6 with |Chat_con| = 5.
That distinction is the substance of finding F-2-01 and
of the 0.1.2 revision that closed it. A registry that froze only the near-unit
case would pin exactly the half an implementation gets right by accident.

THE TWO COST MEASURES, both frozen, because reporting only the second overstates
the guarantee (Theorem thm:sa3 (vi) and Remark rem:guard say so in as many
words). AGAINST THE RAW QUANTILE INTERVAL the cost is Eq. eq:guard-cost and is
NOT bounded by one count: GUARD-lower-two-counts shows two, and the contract
proves the enlargement approaches 1 - p in frequency, uniformly in n, as a
single tail's allocation approaches 1. AGAINST THE HONEST VALUE the quantity
bounded is the emitted endpoint's DISTANCE from p, and that is at most 1/n
unconditionally, ON THE SIDE WHERE THE GUARD ACTS -- GUARD-inert is frozen
partly to show that reading the 1/n clause as unconditional is wrong, its
distances being 1/4 on a run with n = 8.

WHAT THE GUARD BUYS, and why it is never optional. Remark rem:guard: p^hon(chat)
lies in [k^-/n, k^+/n] for EVERY admissible budget and EVERY admissible
allocation, including allocations so lopsided that the raw quantile interval
excludes the honest value. Theorem thm:box-construction (iii) and Theorem thm:honest-containment rest on
exactly that, and without the guard both would carry a side condition on how
large ecomp may be. Theorem thm:sa3 (iii) is why the widening is always
allowed: enlarging the interval can only lower the failure probability.

THE DEGENERATE CASES. GUARD-degenerate-p-zero and GUARD-degenerate-p-one freeze
Theorem thm:sa3 (v): at p = 0 the interval is [0, 0], at p = 1 it is [n, n], and
in BOTH the two budgets are entirely unspent, both emitted tails being exactly
zero. They are asymmetric in which endpoint runs to the boundary, so both halves
are frozen. The p = 0 case is also the only route by which the construction map
produces an acceptance support smaller than Chat on a constrained outcome.

The seven cases are in GUARD_CASES.
""",
    hypotheses=(
        "The input domain of contract Section 2.1, whose consequence "
        "0 <= eps^{+-}(chat) <= ecomp < 1 Definition def:interval records and "
        "the proof of Theorem thm:sa3 (vi) uses twice.",
        "Exact or upward-rounded tail evaluation (Assumption A-EXACT): k^- may "
        "be replaced by any smaller admissible integer and k^+ by any larger "
        "one, never the reverse.",
    ),
)


O_SA_INTERVAL_EXTREMALITY = SAOracleEntry(
    oracle_id="O-SA-INTERVAL-EXTREMALITY",
    claims=("SA3",),
    kind="structural-identity",
    subject=(
        "Theorem thm:sa3 (i)-(iv) on frozen data: the two endpoint sets are "
        "non-empty; the emitted endpoints meet their budgets; every enlargement "
        "of the interval is admissible and every shrink beyond "
        "[kappa^-, kappa^+] is NOT, with the unsound direction exhibited."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:sa3 (i)-(iv), on the data of GUARD-inert
(n = 8, p = 3/4, both budgets 1/20, kappa^- = 4, kappa^+ = 8) and
BTAIL-n8-p-three-quarters.

(i) NON-EMPTINESS, hence existence and uniqueness. k = 0 always belongs to the
set of eq:kappaminus, because Pr[N < 0] = 0 <= eps^-; k = n always belongs to
the set of eq:kappaplus, because Pr[N > n] = 0 <= eps^+. Both facts are frozen
as the leading and trailing zeros of the tail arrays in Group SA-A. A non-empty
finite set of integers has a unique maximum and a unique minimum, so kappa^{+-}
exist and are unique -- there is nothing to converge to and no tie to break.
THE ORDERING CHAIN Eq. eq:ordering,
  0 <= k^- <= floor(n p) <= ceil(n p) <= k^+ <= n ,
holds on GUARD-inert as 0 <= 4 <= 6 <= 6 <= 8 <= 8, and on every case of
GUARD_CASES; it is immediate from Eq. eq:guard, k^- being a minimum one of whose
arguments is floor(n p) and k^+ a maximum one of whose arguments is ceil(n p).

(ii) THE BUDGETS ARE MET BY THE EMITTED ENDPOINTS, Eq. eq:budget-met. On
GUARD-inert:
  Pr[N < k^-] = Pr[N < 4] = 1789/65536 <= 1/20 , since 1789 * 20 = 35780
    < 65536 ;
  Pr[N > k^+] = Pr[N > 8] = 0 <= 1/20 .
This is a consequence of (iii) and Eq. eq:guard, not an independent check: the
guard only ever moves k^- DOWN and k^+ UP.

(iii) EXTREMALITY, AND THE ADMISSIBLE RELAXATION -- the load-bearing part.
kappa^- = 4 is the LARGEST integer in {0..8} with Pr[N < k] <= 1/20 and
kappa^+ = 8 the SMALLEST with Pr[N > k] <= 1/20. Every pair
(k~^-, k~^+) with 0 <= k~^- <= 4 and 8 <= k~^+ <= 8 satisfies
Eq. eq:budget-met as well, by monotonicity of the two tail arrays in k. So
ENLARGING THE INTERVAL IS ALWAYS ADMISSIBLE.
THE UNSOUND DIRECTION, frozen as a number so that it is not merely asserted:
take k~^- = 5, one step INSIDE kappa^- = 4. Then
  Pr[N < 5] = Pr[N <= 4] = 7459/65536 ,
and 7459 * 20 = 149180 > 65536, so Pr[N < 5] > 1/20 = eps^-. The budget is
BROKEN, the shrink is inadmissible, and an implementation that reported
epsilon_star from the allocation rather than from the emitted endpoints would
not notice. Symmetrically k~^+ = 7 gives Pr[N > 7] = 6561/65536 > 1/20.
THE SAME DIRECTION IS ASSUMPTION A-EXACT'S. Its statement is exactly
"k^- may be replaced by any SMALLER admissible integer and k^+ by any LARGER
one, NEVER the reverse", and its "If violated" cell says an upward-rounded k^-
or a downward-rounded k^+ BREAKS SA5 -- a completeness figure is reported that
the set does not meet. The two frozen numbers 7459/65536 and 6561/65536 are what
that failure looks like.

(iv) COMPUTABILITY. Every comparison above is between an exact rational tail
(Lemma lem:exact-strict-tails, Eq. eq:tails-used) and an exact rational budget, hence
decidable by cross multiplication of integers. No search over a continuum, no
inverse CDF and no root-finding occurs anywhere: the endpoints are extrema of a
finite integer set. Which of the two evaluation routes -- summing the pmf or
evaluating the incomplete beta integral -- is taken is, in the contract's words,
an implementation choice constrained only by Assumption A-EXACT.
""",
    value=Fraction(7459, 65536),
    hypotheses=(
        "The tail arrays of BTAIL-n8-p-three-quarters, which this entry reads "
        "rather than recomputes.",
        "eps^{+-} <= ecomp < 1 (contract Section 2.1, recorded in Definition "
        "def:interval).",
    ),
)


# ===========================================================================
#  Group SA-D -- the construction map Acc, end to end (SA4, SA5, SA1, SA6, SA7)
# ===========================================================================
#
#  Definition def:construction: from an admissible input
#  (Chat, p^hon, n, ecomp, Chat_con, eps^-, eps^+), Acc emits the `polytope`
#  geometry in CANONICAL BOX FORM with
#      q^-(chat) = k^-(chat)/n on Chat_con , 0 off it ,
#      q^+(chat) = k^+(chat)/n on Chat_con , 1 off it ,
#  and AcceptSet = { q in Delta(Chat) : q^- <= q <= q^+ } (Eq. eq:accset).
#
#  ROW ORDER, fixed once here and never restated in a case. With m = |Chat| and
#  the DECLARATION's own enumeration chat^(1), ..., chat^(m), Eq. eq:boxrows
#  gives m_row = 2m rows:
#      row i      :  +e_i^T q <=  q^+(chat^(i))      (the caps)
#      row m + i  :  -e_i^T q <= -q^-(chat^(i))      (the floors)
#  Row indices are INTEGERS in {1, ..., 2m}, never alphabet elements
#  (contract Section 2.5, "Coordinate order"). The `rows` field below is B with
#  entries in {0, +-1} (Theorem thm:box-construction (i)) and `rhs` is b in the same order.
#
#  RAW BOUNDS VERSUS THE DENOTED SET'S TIGHT BOUNDS. `box_lower` / `box_upper`
#  are what Acc EMITS. `tight_lower` / `tight_upper` are the exact range of each
#  coordinate OVER THE DENOTED SET,
#      tight_upper(chat) = min{ q^+(chat) , 1 - sum_{chat' != chat} q^-(chat') }
#      tight_lower(chat) = max{ q^-(chat) , 1 - sum_{chat' != chat} q^+(chat') }
#  which is Theorem thm:box-oracle (ii)'s own fill run at g = -e_chat and g = +e_chat
#  respectively -- no new machinery, and valid exactly under the non-emptiness
#  Eq. eq:boxfeas. The two DIFFER whenever the simplex is what binds, and
#  Remark rem:selector requires the RAW bounds to be emitted anyway: the vacuous
#  [0, 1] bounds off Chat_con are kept so that m_row = 2|Chat| does not depend
#  on Chat_con and a consumer never has to infer a missing row. AN
#  IMPLEMENTATION THAT TIGHTENS THE EMITTED BOUNDS EMITS A DIFFERENT ARTIFACT.


@dataclass(frozen=True)
class ConstructionCase:
    """One complete run of the construction map, with everything it emits."""

    case_id: str
    outcomes: tuple[str, ...]
    honest: tuple[Fraction, ...]
    rounds: int
    constrained: tuple[str, ...]
    ecomp: Fraction
    #: The allocation on `constrained`, in that order.
    eps_lower: tuple[Fraction, ...]
    eps_upper: tuple[Fraction, ...]
    #: "uniform-default" when the allocation is ecomp / (2 |Chat_con|), else
    #: "explicit".
    allocation_rule: str
    #: The emitted box bounds q^-, q^+, in `outcomes` order. RAW.
    box_lower: tuple[Fraction, ...]
    box_upper: tuple[Fraction, ...]
    m_row: int
    #: B of Eq. eq:boxrows, rows in integer index order, entries in {0, +-1}.
    rows: tuple[tuple[int, ...], ...]
    #: b of Eq. eq:boxrows, in the same row order.
    rhs: tuple[Fraction, ...]
    #: (sum q^-, sum q^+): the two sides of Eq. eq:boxfeas.
    box_sums: tuple[Fraction, Fraction]
    #: The exact coordinate range over the DENOTED set. May be strictly inside
    #: the raw bounds; recorded apart and never emitted in their place.
    tight_lower: tuple[Fraction, ...]
    tight_upper: tuple[Fraction, ...]
    #: Chat_acc = {chat : q^+(chat) > 0}, the Outputs-table formula.
    acceptance_support: tuple[str, ...]
    #: The union of supp q over AcceptSet -- the MINIMAL acceptance support.
    #: May be strictly smaller than `acceptance_support`; that is conforming.
    minimal_support: tuple[str, ...]
    #: epsilon_star of Eq. eq:completeness.
    epsilon_star: Fraction
    #: The exact probability that the honest frequency vector leaves AcceptSet.
    #: Never above epsilon_star; strictly below it when the union bound
    #: double-counts.
    true_failure_probability: Fraction
    honest_contained: bool
    arithmetic: str


CONSTRUCTION_CASES: tuple[ConstructionCase, ...] = (
    ConstructionCase(
        case_id="ACC-normal-2letter",
        outcomes=("c0", "c1"),
        honest=(Fraction(3, 4), Fraction(1, 4)),
        rounds=8,
        constrained=("c0", "c1"),
        ecomp=Fraction(1, 5),
        eps_lower=(Fraction(1, 20), Fraction(1, 20)),
        eps_upper=(Fraction(1, 20), Fraction(1, 20)),
        allocation_rule="uniform-default",
        box_lower=(Fraction(1, 2), Fraction(0)),
        box_upper=(Fraction(1), Fraction(1, 2)),
        m_row=4,
        rows=((1, 0), (0, 1), (-1, 0), (0, -1)),
        rhs=(Fraction(1), Fraction(1, 2), Fraction(-1, 2), Fraction(0)),
        box_sums=(Fraction(1, 2), Fraction(3, 2)),
        tight_lower=(Fraction(1, 2), Fraction(0)),
        tight_upper=(Fraction(1), Fraction(1, 2)),
        acceptance_support=("c0", "c1"),
        minimal_support=("c0", "c1"),
        epsilon_star=Fraction(1789, 32768),
        true_failure_probability=Fraction(1789, 65536),
        honest_contained=True,
        arithmetic="""\
THE NORMAL PATH: nothing degenerate, the guard inert, the default allocation.
  Chat = (c0, c1) , p^hon = (3/4, 1/4) , n = 8 , Chat_con = Chat ,
  ecomp = 1/5 , uniform rule eps^{+-} = ecomp / (2 |Chat_con|)
                            = (1/5)/4 = 1/20 for every outcome.
ENDPOINTS, from BTAIL-n8-p-three-quarters and BTAIL-n8-p-one-quarter at the
budget 1/20 (numerator * 20 against 65536 in each comparison):
  c0 : kappa^- = 4 (1789 * 20 < 65536 <= 7459 * 20) ,
       kappa^+ = 8 (6561 * 20 > 65536, then Pr[N > 8] = 0) ,
       n p = 6 , floor = ceil = 6 , so k^- = min{4,6} = 4 , k^+ = max{8,6} = 8 ;
  c1 : kappa^- = 0 (6561 * 20 > 65536 already at k = 1) ,
       kappa^+ = 4 (7459 * 20 > 65536 at k = 3, 1789 * 20 < 65536 at k = 4) ,
       n p = 2 , floor = ceil = 2 , so k^- = min{0,2} = 0 , k^+ = max{4,2} = 4 .
The guard is inert on both outcomes and on both sides.
BOX BOUNDS, Eq. eq:boxbounds: q^- = (4/8, 0/8) = (1/2, 0) and
q^+ = (8/8, 4/8) = (1, 1/2). Every entry is an integer multiple of 1/8, which
is Theorem thm:box-construction (i).
NON-EMPTY, Eq. eq:boxfeas: sum q^- = 1/2 <= 1 <= 3/2 = sum q^+.
HONEST CONTAINMENT, Theorem thm:box-construction (iii): 1/2 <= 3/4 <= 1 and
0 <= 1/4 <= 1/2. Both hold, as they must -- the guard guarantees it
unconditionally.
TIGHT BOUNDS COINCIDE WITH THE RAW ONES HERE:
  tight_upper(c0) = min{1, 1 - q^-(c1)} = min{1, 1} = 1 ,
  tight_lower(c0) = max{1/2, 1 - q^+(c1)} = max{1/2, 1/2} = 1/2 ,
  tight_upper(c1) = min{1/2, 1 - 1/2} = 1/2 ,
  tight_lower(c1) = max{0, 1 - 1} = 0 .
So the emitted box is already the exact coordinate range; this is the baseline
against which the raw-versus-tight cases below are read.
epsilon_star, Eq. eq:completeness -- the sum over Chat_con of the two emitted
tails:
  c0 : Pr[N < 4] = Pr[N <= 3] = 1789/65536 , Pr[N > 8] = 0 ;
  c1 : Pr[N < 0] = 0 , Pr[N > 4] = Pr[N >= 5] = 1789/65536 ;
  epsilon_star = 1789/65536 + 1789/65536 = 3578/65536 = 1789/32768 ,
which is about 0.0546 and comfortably inside the budget 1/5.
THE UNION BOUND DOUBLE-COUNTS HERE, EXACTLY BY A FACTOR OF 2, and the case is
frozen partly to make that visible. On a two-letter alphabet N_{c1} = 8 - N_{c0}
identically, so
  {freq(c0) < 1/2} = {N_{c0} <= 3}  and  {freq(c1) > 1/2} = {N_{c1} >= 5}
                                                          = {N_{c0} <= 3}
are the SAME EVENT, while the other two failure events are impossible
(q^+(c0) = 1 and q^-(c1) = 0 cannot be violated). The true failure probability
is therefore 1789/65536, exactly half of epsilon_star. Theorem thm:completeness-bound claims
only an upper bound and is not weakened by this; but epsilon_star is what the
module REPORTS under completeness_certified, and a reader who takes it for the
failure probability is out by a factor of two on the most ordinary input there
is.""",
    ),
    ConstructionCase(
        case_id="ACC-budget-large",
        outcomes=("c0", "c1"),
        honest=(Fraction(3, 4), Fraction(1, 4)),
        rounds=8,
        constrained=("c0", "c1"),
        ecomp=Fraction(4, 5),
        eps_lower=(Fraction(1, 5), Fraction(1, 5)),
        eps_upper=(Fraction(1, 5), Fraction(1, 5)),
        allocation_rule="uniform-default",
        box_lower=(Fraction(5, 8), Fraction(1, 8)),
        box_upper=(Fraction(7, 8), Fraction(3, 8)),
        m_row=4,
        rows=((1, 0), (0, 1), (-1, 0), (0, -1)),
        rhs=(Fraction(7, 8), Fraction(3, 8), Fraction(-5, 8), Fraction(-1, 8)),
        box_sums=(Fraction(3, 4), Fraction(5, 4)),
        tight_lower=(Fraction(5, 8), Fraction(1, 8)),
        tight_upper=(Fraction(7, 8), Fraction(3, 8)),
        acceptance_support=("c0", "c1"),
        minimal_support=("c0", "c1"),
        epsilon_star=Fraction(3505, 8192),
        true_failure_probability=Fraction(3505, 16384),
        honest_contained=True,
        arithmetic="""\
THE SAME PROTOCOL AT A FOUR-TIMES-LARGER BUDGET -- the companion of
ACC-normal-2letter, and the pair O-SA-BUDGET-MONOTONE reads.
  Everything as in ACC-normal-2letter except ecomp = 4/5, so the uniform rule
  allocates eps^{+-} = (4/5)/4 = 1/5 to every tail.
ENDPOINTS, same two tail tables, now compared against 1/5 (numerator * 5 against
65536):
  c0 : Pr[N <= 4] = 7459/65536 , 7459 * 5 = 37295 < 65536 , so k = 5 is
         admissible ; Pr[N <= 5] = 21067/65536 , 21067 * 5 = 105335 > 65536 , so
         k = 6 is not : kappa^- = 5 .
       Pr[N >= 7] = 24057/65536 , 24057 * 5 = 120285 > 65536 , k = 6 not
         admissible ; Pr[N >= 8] = 6561/65536 , 6561 * 5 = 32805 < 65536 ,
         k = 7 admissible : kappa^+ = 7 .
       n p = 6 : k^- = min{5,6} = 5 , k^+ = max{7,6} = 7 . Guard inert.
  c1 : Pr[N <= 0] = 6561/65536 , 32805 < 65536 , k = 1 admissible ;
         Pr[N <= 1] = 24057/65536 , 120285 > 65536 : kappa^- = 1 .
       Pr[N >= 3] = 21067/65536 , 105335 > 65536 , k = 2 not admissible ;
         Pr[N >= 4] = 7459/65536 , 37295 < 65536 : kappa^+ = 3 .
       n p = 2 : k^- = min{1,2} = 1 , k^+ = max{3,2} = 3 . Guard inert.
BOX BOUNDS: q^- = (5/8, 1/8) , q^+ = (7/8, 3/8).
NON-EMPTY: 3/4 <= 1 <= 5/4. HONEST CONTAINMENT: 5/8 <= 6/8 <= 7/8 and
1/8 <= 2/8 <= 3/8.
NESTED INSIDE ACC-normal-2letter, STRICTLY, which is Theorem thm:monotonicity-limits (i):
  [5/8, 7/8] is inside [4/8, 8/8] and [1/8, 3/8] is inside [0, 4/8] ,
each inclusion strict at both ends. A LARGER BUDGET BUYS A SMALLER SET.
TIGHT BOUNDS COINCIDE WITH THE RAW ONES:
  tight_upper(c0) = min{7/8, 1 - 1/8} = 7/8 ,
  tight_lower(c0) = max{5/8, 1 - 3/8} = max{5/8, 5/8} = 5/8 ,
  and symmetrically for c1.
Both coordinates' bounds are simultaneously attainable because
sum q^- = 3/4 < 1 < 5/4 = sum q^+ leaves slack on both sides.
epsilon_star:
  c0 : Pr[N < 5] = Pr[N <= 4] = 7459/65536 , Pr[N > 7] = 6561/65536 ;
  c1 : Pr[N < 1] = Pr[N <= 0] = 6561/65536 , Pr[N > 3] = Pr[N >= 4]
         = 7459/65536 ;
  epsilon_star = (7459 + 6561 + 6561 + 7459)/65536 = 28040/65536 = 3505/8192 ,
about 0.4279, inside the budget 4/5.
AGAIN EXACTLY DOUBLE THE TRUTH. The four failure events collapse in pairs:
{N_{c0} <= 4} = {N_{c1} >= 4} and {N_{c0} >= 8} = {N_{c1} <= 0}. The union is
{N_{c0} <= 4} u {N_{c0} = 8}, disjoint, with probability
(7459 + 6561)/65536 = 3505/16384.
THE DIRECTION OF THE TRADE-OFF, frozen as two numbers rather than asserted:
epsilon_star rises from 1789/32768 to 3505/8192 as ecomp goes from 1/5 to 4/5,
while the set shrinks. Theorem thm:monotonicity-limits (ii) then makes any infimum over
AcceptSet -- the consumer's h_low among them -- NON-DECREASING in ecomp. That is
a trade-off, not an improvement: the same change makes the honest run abort more
often.""",
    ),
    ConstructionCase(
        case_id="ACC-guard-lower-two-counts",
        outcomes=("c0", "c1"),
        honest=(Fraction(1, 2), Fraction(1, 2)),
        rounds=10,
        constrained=("c0",),
        ecomp=Fraction(19, 20),
        eps_lower=(Fraction(9, 10),),
        eps_upper=(Fraction(1, 20),),
        allocation_rule="explicit",
        box_lower=(Fraction(1, 2), Fraction(0)),
        box_upper=(Fraction(4, 5), Fraction(1)),
        m_row=4,
        rows=((1, 0), (0, 1), (-1, 0), (0, -1)),
        rhs=(Fraction(4, 5), Fraction(1), Fraction(-1, 2), Fraction(0)),
        box_sums=(Fraction(1, 2), Fraction(9, 5)),
        tight_lower=(Fraction(1, 2), Fraction(1, 5)),
        tight_upper=(Fraction(4, 5), Fraction(1, 2)),
        acceptance_support=("c0", "c1"),
        minimal_support=("c0", "c1"),
        epsilon_star=Fraction(397, 1024),
        true_failure_probability=Fraction(397, 1024),
        honest_contained=True,
        arithmetic="""\
THE GUARD COSTING TWO COUNTS, ASSEMBLED INTO A COMPLETE CONSTRUCTION. The
per-outcome arithmetic is GUARD-lower-two-counts; this case is what Acc emits
around it.
  Chat = (c0, c1) , p^hon = (1/2, 1/2) , n = 10 , Chat_con = {c0} ,
  eps^-(c0) = 9/10 , eps^+(c0) = 1/20 , summing to 19/20 = ecomp .
The allocation is EXPLICIT, not the uniform rule: it is deliberately lopsided,
which is the regime in which a cost above one count is possible at all.
ENDPOINTS: kappa^- = 7, kappa^+ = 8, floor(n p) = ceil(n p) = 5, so
k^- = min{7,5} = 5 and k^+ = max{8,5} = 8 -- a two-count widening on the lower
side.
BOX BOUNDS. On Chat_con: q^-(c0) = 5/10 = 1/2, q^+(c0) = 8/10 = 4/5. OFF
Chat_con, Eq. eq:boxbounds gives the VACUOUS pair: q^-(c1) = 0, q^+(c1) = 1.
NON-EMPTY: 1/2 <= 1 <= 9/5. HONEST CONTAINMENT: 1/2 <= 1/2 <= 4/5 on c0 -- the
lower bound is attained EXACTLY, which is what the guard bought -- and
0 <= 1/2 <= 1 on c1.
WITHOUT THE GUARD the raw interval would have been [kappa^-, kappa^+] = [7, 8],
i.e. q(c0) in [7/10, 4/5], WHICH EXCLUDES THE HONEST VALUE 1/2. That is the
situation Remark rem:guard describes as an allocation "so lopsided that the raw
quantile interval excludes the honest value", and it is why Theorems
thm:box-construction (iii) and thm:honest-containment carry no side condition on how large ecomp may be.
RAW BOUNDS DIFFER FROM THE DENOTED SET'S TIGHT BOUNDS -- the first of four such
cases here, and the mildest:
  tight_upper(c1) = min{ q^+(c1) , 1 - q^-(c0) } = min{1, 1/2} = 1/2 ,
  tight_lower(c1) = max{ q^-(c1) , 1 - q^+(c0) } = max{0, 1/5} = 1/5 ,
so the DENOTED range of c1 is [1/5, 1/2] while the EMITTED bounds are [0, 1].
The c0 bounds are already tight: tight_upper(c0) = min{4/5, 1 - 0} = 4/5 and
tight_lower(c0) = max{1/2, 1 - 1} = 1/2.
BOTH ARE RECORDED, AND ONLY THE RAW PAIR IS EMITTED. Remark rem:selector is
explicit that the unconstrained coordinates receive the vacuous bounds rather
than being omitted, so that m_row = 2|Chat| = 4 does not depend on Chat_con. An
implementation that emitted [1/5, 1/2] for c1 would be emitting a different
artifact -- one with the same denotation, which is precisely why the substitution
is tempting and why the two columns are frozen apart.
epsilon_star. Only c0 is constrained:
  Pr[N < 5] = Pr[N <= 4] = 386/1024 = 193/512 , Pr[N > 8] = 11/1024 ,
  epsilon_star = 386/1024 + 11/1024 = 397/1024 , about 0.388 ,
inside the budget 19/20 with a great deal to spare -- the guard spent far less
than the 9/10 allocated to the lower tail, because it moved the endpoint DOWN
from 7 to 5 and a lower endpoint has a smaller tail.
HERE THE UNION BOUND IS TIGHT, unlike the two cases above: Chat_con has ONE
element and its two failure events {N < 5} and {N > 8} are DISJOINT, so
epsilon_star = 397/1024 IS the true failure probability. Frozen next to the
factor-of-2 cases so that neither is read as the general rule.""",
    ),
    ConstructionCase(
        case_id="ACC-guard-active-uniform",
        outcomes=("c0", "c1"),
        honest=(Fraction(999, 1000), Fraction(1, 1000)),
        rounds=10,
        constrained=("c0", "c1"),
        ecomp=Fraction(1, 10),
        eps_lower=(Fraction(1, 40), Fraction(1, 40)),
        eps_upper=(Fraction(1, 40), Fraction(1, 40)),
        allocation_rule="uniform-default",
        box_lower=(Fraction(9, 10), Fraction(0)),
        box_upper=(Fraction(1), Fraction(1, 10)),
        m_row=4,
        rows=((1, 0), (0, 1), (-1, 0), (0, -1)),
        rhs=(Fraction(1), Fraction(1, 10), Fraction(-9, 10), Fraction(0)),
        box_sums=(Fraction(9, 10), Fraction(11, 10)),
        tight_lower=(Fraction(9, 10), Fraction(0)),
        tight_upper=(Fraction(1), Fraction(1, 10)),
        acceptance_support=("c0", "c1"),
        minimal_support=("c0", "c1"),
        epsilon_star=Fraction(
            44760628993049280314920009, 500000000000000000000000000000
        ),
        true_failure_probability=Fraction(
            44760628993049280314920009, 1000000000000000000000000000000
        ),
        honest_contained=True,
        arithmetic="""\
THE GUARD ACTIVE ON BOTH OUTCOMES AT AN ORDINARY BUDGET UNDER THE DEFAULT
UNIFORM RULE -- the lo0/up0 regime, assembled from GUARD-upper-active-uniform
and GUARD-lower-active-uniform. This is Remark rem:guard's own n = 10 instance,
and the reason the 0.1.2 revision exists.
  Chat = (c0, c1) , p^hon = (999/1000, 1/1000) , n = 10 , Chat_con = Chat ,
  ecomp = 1/10 , uniform rule eps^{+-} = (1/10)/4 = 1/40 .
ENDPOINTS (derivations in the two GUARD cases; both rest on Bernoulli's
inequality rather than on evaluating a 30-digit tail):
  c1 : n p = 1/100 , floor = 0 , ceil = 1 ; kappa^- = 0 , kappa^+ = 0 ;
       k^- = min{0,0} = 0 , k^+ = max{0,1} = 1 -- THE GUARD RAISES IT ;
  c0 : n p = 999/100 , floor = 9 , ceil = 10 ; kappa^- = 10 , kappa^+ = 10 ;
       k^- = min{10,9} = 9 -- THE GUARD LOWERS IT -- , k^+ = max{10,10} = 10 .
BOX BOUNDS: q^- = (9/10, 0) , q^+ = (1, 1/10). Without the guard they would have
been q^- = (1, 0) and q^+ = (1, 0) -- a box denoting the single point
delta_{c0}, which forbids the honest run's own second outcome to occur at all
even though the honest channel produces it once per thousand rounds.
NON-EMPTY: 9/10 <= 1 <= 11/10. HONEST CONTAINMENT: 9/10 <= 999/1000 <= 1 and
0 <= 1/1000 <= 1/10.
TIGHT BOUNDS COINCIDE WITH THE RAW ONES: tight_upper(c0) = min{1, 1 - 0} = 1,
tight_lower(c0) = max{9/10, 1 - 1/10} = 9/10, tight_upper(c1) =
min{1/10, 1 - 9/10} = 1/10, tight_lower(c1) = max{0, 1 - 1} = 0.
epsilon_star. Both outcomes are constrained and each contributes one non-zero
tail:
  c0 : Pr[N < 9] = Pr[N <= 8] , Pr[N > 10] = 0 ;
  c1 : Pr[N < 0] = 0 , Pr[N > 1] = Pr[N >= 2] ;
and on a two-letter alphabet {N_{c0} <= 8} = {N_{c1} >= 2}, so BOTH non-zero
terms are the SAME NUMBER and epsilon_star is exactly twice it. With
N_{c1} binomial (10, 1/1000),
  Pr[N_{c1} >= 2] = 1 - (999/1000)^10 - 10 (1/1000)(999/1000)^9
                  = (10^30 - 999^10 - 10 * 999^9) / 10^30
                  = (10^30 - 999^9 (999 + 10)) / 10^30
                  = (10^30 - 1009 * 999^9) / 10^30
                  = 44760628993049280314920009 / 10^30 ,
using 999^9 = 991035916125874083964008999. Hence
  epsilon_star = 2 * that = 44760628993049280314920009 / (5 * 10^29) ,
about 8.95e-5, far inside the budget 1/10, and the true failure probability is
half of it, about 4.48e-5.
A SANITY BOUND that needs no 30-digit arithmetic: Pr[N_{c1} >= 2] <=
binom(10,2) (10^-3)^2 = 45 * 10^-6 = 4.5e-5, which brackets the exact value from
above. THAT IS A CHECK, NOT THE DERIVATION.
WHY THE EXACT VALUE IS FROZEN AND NOT A FLOAT. 44760628993049280314920009 /
(5 * 10^29) has no exact binary64 representation, and the two numbers here
differ from each other by a factor of exactly 2 -- a comparison that survives
rounding only if neither is rounded. This is the case that makes the whole
registry's use of Fraction rather than float load-bearing.""",
    ),
    ConstructionCase(
        case_id="ACC-degenerate-honest-mass",
        outcomes=("c0", "c1"),
        honest=(Fraction(1), Fraction(0)),
        rounds=4,
        constrained=("c0", "c1"),
        ecomp=Fraction(1, 2),
        eps_lower=(Fraction(1, 8), Fraction(1, 8)),
        eps_upper=(Fraction(1, 8), Fraction(1, 8)),
        allocation_rule="uniform-default",
        box_lower=(Fraction(1), Fraction(0)),
        box_upper=(Fraction(1), Fraction(0)),
        m_row=4,
        rows=((1, 0), (0, 1), (-1, 0), (0, -1)),
        rhs=(Fraction(1), Fraction(0), Fraction(-1), Fraction(0)),
        box_sums=(Fraction(1), Fraction(1)),
        tight_lower=(Fraction(1), Fraction(0)),
        tight_upper=(Fraction(1), Fraction(0)),
        acceptance_support=("c0",),
        minimal_support=("c0",),
        epsilon_star=Fraction(0),
        true_failure_probability=Fraction(0),
        honest_contained=True,
        arithmetic="""\
BOTH DEGENERATE HONEST MASSES ON ONE RUN, and the only way the construction map
emits an acceptance support SMALLER than Chat.
  Chat = (c0, c1) , p^hon = (1, 0) , n = 4 , Chat_con = Chat , ecomp = 1/2 ,
  uniform rule eps^{+-} = (1/2)/4 = 1/8 .
ENDPOINTS, from GUARD-degenerate-p-one and GUARD-degenerate-p-zero:
  c0 (p = 1) : [k^-, k^+] = [4, 4] = [n, n] ;
  c1 (p = 0) : [k^-, k^+] = [0, 0] .
BOX BOUNDS: q^- = q^+ = (1, 0). The denotation is the single point
{(1, 0)} = {delta_{c0}} -- A POLYTOPE WHOSE DENOTATION IS A SINGLETON, which the
taxonomy handles without a tag change (Remark rem:two-tags: the canonical box
form is a sub-form of `polytope`, not a third tag).
NON-EMPTY, AT BOTH ENDS WITH EQUALITY: sum q^- = 1 <= 1 <= 1 = sum q^+. This is
the branch of the SA1 witness formula whose denominator vanishes
(VALID-box-both-sums-equal-one), and it is reached from an ordinary admissible
input rather than from contrived data.
HONEST CONTAINMENT: 1 <= 1 <= 1 and 0 <= 0 <= 0.
TIGHT BOUNDS EQUAL THE RAW ONES, both being the single point.
THE ACCEPTANCE SUPPORT IS STRICTLY SMALLER THAN Chat. By the Outputs-table
formula, Chat_acc = {chat : q^+(chat) > 0} = {c0}, because q^+(c1) = 0. Here it
is also MINIMAL: the unique feasible point has support {c0}. Contrast
ACC-support-superset, where the same formula gives a STRICT superset of the
minimal support -- both are conforming, and the difference is the contract's.
epsilon_star = 0, EXACTLY. Theorem thm:sa3 (v): at p = 0 and at p = 1 both tails
in Eq. eq:budget-met are exactly zero, so all four summands of
Eq. eq:completeness vanish and THE ENTIRE BUDGET OF 1/2 IS UNSPENT. The true
failure probability is 0 as well: under A-HON every round yields c0, so the
frequency vector is delta_{c0} with probability one, which is the single point of
AcceptSet. Remark rem:epsstar names degenerate p^hon(chat) as the case that
leaves the budget entirely unspent, and this is it.""",
    ),
    ConstructionCase(
        case_id="ACC-support-superset",
        outcomes=("c0", "c1"),
        honest=(Fraction(1), Fraction(0)),
        rounds=4,
        constrained=("c0",),
        ecomp=Fraction(1, 2),
        eps_lower=(Fraction(1, 4),),
        eps_upper=(Fraction(1, 4),),
        allocation_rule="uniform-default",
        box_lower=(Fraction(1), Fraction(0)),
        box_upper=(Fraction(1), Fraction(1)),
        m_row=4,
        rows=((1, 0), (0, 1), (-1, 0), (0, -1)),
        rhs=(Fraction(1), Fraction(1), Fraction(-1), Fraction(0)),
        box_sums=(Fraction(1), Fraction(2)),
        tight_lower=(Fraction(1), Fraction(0)),
        tight_upper=(Fraction(1), Fraction(0)),
        acceptance_support=("c0", "c1"),
        minimal_support=("c0",),
        epsilon_star=Fraction(0),
        true_failure_probability=Fraction(0),
        honest_contained=True,
        arithmetic="""\
THE EMITTED ACCEPTANCE SUPPORT STRICTLY CONTAINS THE MINIMAL ONE, and the raw
box bounds strictly contain the denoted set's tight bounds. One admissible input
produces both.
  Chat = (c0, c1) , p^hon = (1, 0) , n = 4 , Chat_con = {c0} ONLY ,
  ecomp = 1/2 , uniform rule eps^{+-}(c0) = ecomp / (2 |Chat_con|)
                             = (1/2)/2 = 1/4 .
The only change from ACC-degenerate-honest-mass is that c1 is left
UNCONSTRAINED.
ENDPOINTS: c0 has p = 1, so [k^-, k^+] = [4, 4] exactly as before
(GUARD-degenerate-p-one, whose budgets 1/8 and 1/4 both give the same interval
-- the determination there uses only that the budget is below 1). c1 is off
Chat_con and receives the vacuous bounds of Eq. eq:boxbounds.
BOX BOUNDS: q^- = (1, 0) , q^+ = (1, 1).
NON-EMPTY: sum q^- = 1 <= 1 <= 2 = sum q^+.
THE DENOTATION IS STILL THE SINGLE POINT {(1, 0)}: the floor q^-(c0) = 1 already
exhausts the normalization, so every feasible q has q(c0) = 1 and hence
q(c1) = 0. THE SIMPLEX IS WHAT BINDS, not the box.
TIGHT BOUNDS: tight_upper(c1) = min{ q^+(c1) , 1 - q^-(c0) } = min{1, 0} = 0
against a RAW q^+(c1) = 1; tight_lower(c1) = max{0, 1 - 1} = 0; and c0's bounds
are already tight at 1. So the raw upper bound on c1 is loose by the whole
interval [0, 1].
THE ACCEPTANCE SUPPORT. The Outputs-table formula gives
  Chat_acc = { chat : q^+(chat) > 0 } = {c0, c1} ,
because q^+(c1) = 1 > 0. The UNION OF THE SUPPORTS over AcceptSet is {c0}, since
the only feasible point is (1, 0). SO Chat_acc STRICTLY CONTAINS THE MINIMAL
ACCEPTANCE SUPPORT, and that is CONFORMING, not a defect: Theorem thm:box-oracle (i)
asks only that supp q be inside Chat_acc for every q in AcceptSet, and claims
minimality ONLY for the `singleton` tag. The Section 3 notation row says the same
-- an acceptance support is "any set with supp q inside Chat_acc for every q in
AcceptSet".
WHY THIS MATTERS DOWNSTREAM. Chat_acc is consumed by meat-core Definition
def:perturbed, whose certificate domain condition and whose sums over Chat_acc
are all stated for a support that need not be minimal. An implementation that
rejects the larger support, or that computes a different acceptance-side minimum
from it, has read the definition as demanding minimality. It does not: the
minimum is unchanged, because q(c1) = 0 identically on the set --
PMIN-box-superset freezes that number.
epsilon_star = 0, EXACTLY: c1 contributes nothing because it is not in Chat_con
(Eq. eq:completeness sums over Chat_con only), and c0's two tails are zero by
Theorem thm:sa3 (v). The true failure probability is 0.""",
    ),
    ConstructionCase(
        case_id="ACC-ecomp-zero",
        outcomes=("c0", "c1", "c2"),
        honest=(Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)),
        rounds=8,
        constrained=("c0", "c1", "c2"),
        ecomp=Fraction(0),
        eps_lower=(Fraction(0), Fraction(0), Fraction(0)),
        eps_upper=(Fraction(0), Fraction(0), Fraction(0)),
        allocation_rule="uniform-default",
        box_lower=(Fraction(0), Fraction(0), Fraction(0)),
        box_upper=(Fraction(1), Fraction(1), Fraction(1)),
        m_row=6,
        rows=(
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (-1, 0, 0),
            (0, -1, 0),
            (0, 0, -1),
        ),
        rhs=(
            Fraction(1),
            Fraction(1),
            Fraction(1),
            Fraction(0),
            Fraction(0),
            Fraction(0),
        ),
        box_sums=(Fraction(0), Fraction(3)),
        tight_lower=(Fraction(0), Fraction(0), Fraction(0)),
        tight_upper=(Fraction(1), Fraction(1), Fraction(1)),
        acceptance_support=("c0", "c1", "c2"),
        minimal_support=("c0", "c1", "c2"),
        epsilon_star=Fraction(0),
        true_failure_probability=Fraction(0),
        honest_contained=True,
        arithmetic="""\
THE ecomp = 0 LIMIT, Theorem thm:monotonicity-limits (iii): A ZERO COMPLETENESS BUDGET BUYS THE
WHOLE SIMPLEX AND NO CONSTRAINT AT ALL.
  Chat = (c0, c1, c2) , p^hon = (1/2, 1/4, 1/4) , n = 8 , Chat_con = Chat ,
  ecomp = 0 , so the uniform rule -- and every admissible allocation -- gives
  eps^{+-}(chat) = 0 for every chat, these being non-negative with sum at
  most 0.
ENDPOINTS, at a zero budget and 0 < p < 1 on every outcome:
  eq:kappaminus : for k >= 1, Pr[N < k] >= Pr[N = 0] = (1-p)^n > 0, so no
    k >= 1 is admissible and kappa^- = 0. Concretely for c0,
    Pr[N = 0] = (1/2)^8 = 1/256 > 0; for c1 and c2,
    Pr[N = 0] = (3/4)^8 = 6561/65536 > 0 ;
  eq:kappaplus : for k <= n-1, Pr[N > k] >= Pr[N = n] = p^n > 0, so no such k
    is admissible and kappa^+ = n = 8. Concretely for c0, p^n = 1/256 > 0; for
    c1 and c2, p^n = (1/4)^8 = 1/65536 > 0 .
GUARD, inert in the sense that it cannot widen past the whole range:
k^- = min{0, floor(n p)} = 0 and k^+ = max{8, ceil(n p)} = 8 on every outcome.
BOX BOUNDS: q^- = (0, 0, 0) and q^+ = (1, 1, 1), so
AcceptSet = Delta(Chat) EXACTLY, which is the second sentence of Theorem
thm:monotonicity-limits (iii) -- 0 < p^hon(chat) < 1 holds for all three outcomes here.
NON-EMPTY: 0 <= 1 <= 3. TIGHT BOUNDS EQUAL THE RAW ONES: on three or more
outcomes the simplex does not bind a coordinate that already ranges over [0, 1],
since tight_upper(c0) = min{1, 1 - 0 - 0} = 1 and
tight_lower(c0) = max{0, 1 - 1 - 1} = max{0, -1} = 0.
epsilon_star = 0, EXACTLY: every summand of Eq. eq:completeness is
Pr[N < 0] = 0 or Pr[N > 8] = 0. The honest run can never fail an unconstrained
test, so the true failure probability is 0 too.
THE POINT OF THE LIMIT. The bound epsilon_star <= ecomp is met with equality at
0, and it is met by GIVING UP EVERYTHING: the emitted set constrains nothing, so
the consumer's infimum runs over the whole simplex and h_low is as small as it
can be. That is Theorem thm:monotonicity-limits (i)-(ii) at its left endpoint, and it is the
correct behaviour rather than a degenerate failure -- a protocol that will not
tolerate ANY chance of an honest abort cannot test anything.""",
    ),
    ConstructionCase(
        case_id="ACC-one-letter-constrained",
        outcomes=("c0",),
        honest=(Fraction(1),),
        rounds=7,
        constrained=("c0",),
        ecomp=Fraction(3, 10),
        eps_lower=(Fraction(3, 20),),
        eps_upper=(Fraction(3, 20),),
        allocation_rule="uniform-default",
        box_lower=(Fraction(1),),
        box_upper=(Fraction(1),),
        m_row=2,
        rows=((1,), (-1,)),
        rhs=(Fraction(1), Fraction(-1)),
        box_sums=(Fraction(1), Fraction(1)),
        tight_lower=(Fraction(1),),
        tight_upper=(Fraction(1),),
        acceptance_support=("c0",),
        minimal_support=("c0",),
        epsilon_star=Fraction(0),
        true_failure_probability=Fraction(0),
        honest_contained=True,
        arithmetic="""\
THE ONE-LETTER ALPHABET, Theorem thm:monotonicity-limits (vi), first branch.
  Chat = (c0) , n = 7 , ecomp = 3/10 , Chat_con = {c0} , uniform rule
  eps^{+-}(c0) = (3/10)/2 = 3/20 .
p^hon IS FORCED, not chosen: the only vector with non-negative coordinates
summing to 1 on a one-letter alphabet is delta_{c0}, so the input domain of
Section 2.1 admits p^hon = (1) and nothing else, and p = 1.
ENDPOINTS: Theorem thm:sa3 (v) at p = 1 gives [k^-, k^+] = [n, n] = [7, 7]
(GUARD-degenerate-p-one, whose derivation uses only eps^{+-} < 1). Box bounds
q^- = q^+ = 7/7 = 1.
THE EMITTED SET IS SIMULTANEOUSLY THE WHOLE SIMPLEX AND A SINGLE POINT:
AcceptSet = {q in Delta(Chat) : q(c0) = 1} = {delta_{c0}} = Delta(Chat). The
contract states exactly that, and it is not a contradiction -- on one letter the
simplex has one element.
NON-EMPTY, at both ends with equality: 1 <= 1 <= 1.
m_row = 2|Chat| = 2, and the row structure of Eq. eq:boxrows degenerates to one
cap row (1) with rhs 1 and one floor row (-1) with rhs -1.
epsilon_star = 0 and the true failure probability is 0: under A-HON every round
yields c0, so the frequency vector is delta_{c0} with probability one.
THE CONSTRUCTION IS CONSTANT IN ALL OF ITS PARAMETERS HERE -- n, ecomp and the
allocation appear nowhere in the answer. Theorem thm:monotonicity-limits (vi) says so, and adds
the reading: a one-letter acceptance alphabet imposes no constraint on the
consumer and carries no information; this is a degenerate case to be recognized,
not a regime to be used.""",
    ),
    ConstructionCase(
        case_id="ACC-one-letter-unconstrained",
        outcomes=("c0",),
        honest=(Fraction(1),),
        rounds=7,
        constrained=(),
        ecomp=Fraction(3, 10),
        eps_lower=(),
        eps_upper=(),
        allocation_rule="uniform-default",
        box_lower=(Fraction(0),),
        box_upper=(Fraction(1),),
        m_row=2,
        rows=((1,), (-1,)),
        rhs=(Fraction(1), Fraction(0)),
        box_sums=(Fraction(0), Fraction(1)),
        tight_lower=(Fraction(1),),
        tight_upper=(Fraction(1),),
        acceptance_support=("c0",),
        minimal_support=("c0",),
        epsilon_star=Fraction(0),
        true_failure_probability=Fraction(0),
        honest_contained=True,
        arithmetic="""\
THE ONE-LETTER ALPHABET WITH AN EMPTY SELECTOR, Theorem thm:monotonicity-limits (vi), second
branch -- and the ONLY case here with Chat_con = the empty set.
  Chat = (c0) , n = 7 , ecomp = 3/10 , Chat_con = () .
THE ALLOCATION IS THE EMPTY FUNCTION. The default uniform rule
ecomp / (2 |Chat_con|) has a ZERO DENOMINATOR here, and that is not a defect:
there is no outcome to evaluate it at, so the rule has NO INSTANCE, the
allocation is a pair of vectors on the empty set, and the domain constraint of
Section 2.1 reads sum over the empty set = 0 <= ecomp, which holds. The
contract admits this input -- Section 2.1 types Chat_con as any subset of Chat,
and Theorem thm:monotonicity-limits (vi) works this branch explicitly -- and fixes no
representation for the empty allocation; that is recorded as an open
implementation choice in interface.yaml
(inputs.budget_allocation.empty_selector_note) rather than decided here.
BOX BOUNDS: every outcome is off Chat_con, so Eq. eq:boxbounds gives the vacuous
pair throughout: q^- = (0) and q^+ = (1).
THE DENOTATION IS THE SAME AS IN ACC-one-letter-constrained:
AcceptSet = Delta(Chat) = {delta_{c0}}. THE TWO BRANCHES AGREE, which is the
closing sentence of the proof of Theorem thm:monotonicity-limits (vi) -- "the two cases exhaust
Chat_con subset-or-equal Chat and agree, and neither used n, ecomp or the
allocation".
RAW BOUNDS DIFFER FROM THE TIGHT ONES, in the LOWER direction this time:
tight_lower(c0) = max{ q^-(c0) , 1 - (empty sum) } = max{0, 1} = 1 against a raw
q^-(c0) = 0, and tight_upper(c0) = min{1, 1} = 1. The emitted floor is 0 and the
denoted floor is 1. Frozen because every other raw-versus-tight case here is
loose on an UPPER bound, and an implementation that "tightens" only caps would
pass those and fail this.
epsilon_star = 0 AS AN EMPTY SUM. Eq. eq:completeness sums over Chat_con, which
is empty, so there is no summand at all -- a different route to 0 than the
degenerate-tail route of ACC-one-letter-constrained, and worth distinguishing:
an implementation that initializes epsilon_star to ecomp and subtracts would get
this case wrong.""",
    ),
    ConstructionCase(
        case_id="ACC-raw-vs-tight-3letter",
        outcomes=("c0", "c1", "c2"),
        honest=(Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)),
        rounds=4,
        constrained=("c0",),
        ecomp=Fraction(1, 2),
        eps_lower=(Fraction(1, 4),),
        eps_upper=(Fraction(1, 4),),
        allocation_rule="uniform-default",
        box_lower=(Fraction(1, 4), Fraction(0), Fraction(0)),
        box_upper=(Fraction(3, 4), Fraction(1), Fraction(1)),
        m_row=6,
        rows=(
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (-1, 0, 0),
            (0, -1, 0),
            (0, 0, -1),
        ),
        rhs=(
            Fraction(3, 4),
            Fraction(1),
            Fraction(1),
            Fraction(-1, 4),
            Fraction(0),
            Fraction(0),
        ),
        box_sums=(Fraction(1, 4), Fraction(11, 4)),
        tight_lower=(Fraction(1, 4), Fraction(0), Fraction(0)),
        tight_upper=(Fraction(3, 4), Fraction(3, 4), Fraction(3, 4)),
        acceptance_support=("c0", "c1", "c2"),
        minimal_support=("c0", "c1", "c2"),
        epsilon_star=Fraction(1, 8),
        true_failure_probability=Fraction(1, 8),
        honest_contained=True,
        arithmetic="""\
RAW BOUNDS AGAINST TIGHT BOUNDS ON A THREE-LETTER ALPHABET, where the looseness
is caused by a FLOOR on another coordinate rather than by a two-letter
identity.
  Chat = (c0, c1, c2) , p^hon = (1/2, 1/4, 1/4) , n = 4 , Chat_con = {c0} ,
  ecomp = 1/2 , uniform rule eps^{+-}(c0) = (1/2)/2 = 1/4 .
ENDPOINTS for c0, from BTAIL-n4-p-half at the budget 1/4 = 4/16:
  Pr[N < 1] = Pr[N <= 0] = 1/16 <= 4/16 , admissible ;
  Pr[N < 2] = Pr[N <= 1] = 5/16 > 4/16 , not : kappa^- = 1 ;
  Pr[N > 2] = Pr[N >= 3] = 5/16 > 4/16 , k = 2 not admissible ;
  Pr[N > 3] = Pr[N >= 4] = 1/16 <= 4/16 , admissible : kappa^+ = 3 .
GUARD: n p = 2, floor = ceil = 2, so k^- = min{1,2} = 1 and k^+ = max{3,2} = 3.
Inert.
BOX BOUNDS: q^-(c0) = 1/4, q^+(c0) = 3/4; c1 and c2 are off Chat_con and take
the vacuous pair (0, 1).
NON-EMPTY: sum q^- = 1/4 <= 1 <= 11/4 = sum q^+. HONEST CONTAINMENT:
1/4 <= 1/2 <= 3/4, and 0 <= 1/4 <= 1 twice.
TIGHT BOUNDS:
  tight_upper(c1) = min{ q^+(c1) , 1 - q^-(c0) - q^-(c2) }
                  = min{1, 1 - 1/4 - 0} = 3/4 against a RAW 1 ;
  tight_lower(c1) = max{0, 1 - q^+(c0) - q^+(c2)} = max{0, 1 - 3/4 - 1}
                  = max{0, -3/4} = 0 , equal to the raw floor ;
  identically for c2 ; and c0's raw bounds are already tight,
  tight_upper(c0) = min{3/4, 1 - 0 - 0} = 3/4 and
  tight_lower(c0) = max{1/4, 1 - 1 - 1} = 1/4 ,
both attained, at (3/4, 1/4, 0) and (1/4, 3/4, 0) respectively.
SO TWO OF THE THREE CAPS ARE LOOSE, AND BY THE SAME AMOUNT, 1/4 -- exactly the
floor Acc placed on c0. The looseness is not an artefact of a binary alphabet;
it is the simplex propagating one constrained coordinate's floor onto every
other coordinate's cap.
THE MINIMAL SUPPORT IS ALL THREE OUTCOMES here, unlike ACC-support-superset:
(1/4, 3/4, 0) has support {c0, c1} and (1/4, 0, 3/4) has support {c0, c2}, so
the union is {c0, c1, c2} = Chat_acc. A loose cap does NOT by itself make the
emitted support non-minimal -- what does is a cap that no feasible point can
reach at all.
epsilon_star. Only c0 is constrained:
  Pr[N < 1] = 1/16 , Pr[N > 3] = 1/16 , epsilon_star = 2/16 = 1/8 ,
inside the budget 1/2. THE UNION BOUND IS TIGHT: one constrained outcome, two
disjoint events {N = 0} and {N = 4}, so 1/8 is also the true failure
probability.""",
    ),
    ConstructionCase(
        case_id="ACC-n2-singleton",
        outcomes=("c0", "c1"),
        honest=(Fraction(1, 2), Fraction(1, 2)),
        rounds=2,
        constrained=("c0",),
        ecomp=Fraction(4, 5),
        eps_lower=(Fraction(2, 5),),
        eps_upper=(Fraction(2, 5),),
        allocation_rule="uniform-default",
        box_lower=(Fraction(1, 2), Fraction(0)),
        box_upper=(Fraction(1, 2), Fraction(1)),
        m_row=4,
        rows=((1, 0), (0, 1), (-1, 0), (0, -1)),
        rhs=(Fraction(1, 2), Fraction(1), Fraction(-1, 2), Fraction(0)),
        box_sums=(Fraction(1, 2), Fraction(3, 2)),
        tight_lower=(Fraction(1, 2), Fraction(1, 2)),
        tight_upper=(Fraction(1, 2), Fraction(1, 2)),
        acceptance_support=("c0", "c1"),
        minimal_support=("c0", "c1"),
        epsilon_star=Fraction(1, 2),
        true_failure_probability=Fraction(1, 2),
        honest_contained=True,
        arithmetic="""\
THE CONSTRUCTION MAP EMITTING A SET WITH A SINGLE POINT, and the n = 2 half of
the n-non-monotonicity counterexample of Theorem thm:monotonicity-limits (v).
  Chat = (c0, c1) , p^hon = (1/2, 1/2) , n = 2 , Chat_con = {c0} ,
  ecomp = 4/5 , uniform rule eps^{+-}(c0) = (4/5)/2 = 2/5 .
ENDPOINTS from BTAIL-n2-p-half at the budget 2/5:
  Pr[N < 1] = 1/4 <= 2/5 (5 <= 8 after cross multiplying 1 * 5 against 4 * 2),
    admissible ; Pr[N < 2] = 3/4 > 2/5 , not : kappa^- = 1 ;
  Pr[N > 0] = 3/4 > 2/5 , k = 0 not admissible ; Pr[N > 1] = 1/4 <= 2/5 ,
    admissible : kappa^+ = 1 .
GUARD: n p = 1, floor = ceil = 1, so k^- = min{1,1} = 1 and k^+ = max{1,1} = 1.
Inert.
BOX BOUNDS: q^-(c0) = q^+(c0) = 1/2; c1 vacuous at (0, 1).
THE DENOTATION IS THE SINGLE POINT {(1/2, 1/2)}: q(c0) = 1/2 forces
q(c1) = 1/2 on a two-letter alphabet. RAW BOUNDS DIFFER FROM TIGHT:
tight_lower(c1) = max{0, 1 - 1/2} = 1/2 and tight_upper(c1) =
min{1, 1 - 1/2} = 1/2, so c1's denoted range is the point 1/2 against a raw
[0, 1].
epsilon_star: Pr[N < 1] + Pr[N > 1] = 1/4 + 1/4 = 1/2, inside the budget 4/5,
and TIGHT -- the two events are disjoint, so 1/2 is the true failure
probability.
THE CROSS-CHECK REMARK rem:singleton-honest ASKS FOR, and the reason this case
is frozen twice. This set is a single point, so Theorem thm:singleton-completeness also applies to
it, and it must give the same answer. SING-n2-agrees-with-sa5 computes the exact
accept probability of the point q^* = (1/2, 1/2) under p^hon = (1/2, 1/2) at
n = 2 by the multinomial formula Eq. eq:singleton-acc:
  2! / (1! 1!) * (1/2)^1 * (1/2)^1 = 2 * 1/4 = 1/2 ,
so SA9's least admissible budget is 1 - 1/2 = 1/2, and SA5's epsilon_star is
1/2. THE TWO STATEMENTS AGREE EXACTLY. Remark rem:singleton-honest says the two
must agree here, "because there the budget ecomp = 4/5 was large enough to pay
for it", and this is the arithmetic behind that sentence. Agreement is not
automatic: SA5's route is a union bound over count tails and SA9's is an exact
multinomial mass, and they coincide only because the two tail events are
disjoint and exhaust the complement of the accept event.""",
    ),
    ConstructionCase(
        case_id="ACC-n3-wider",
        outcomes=("c0", "c1"),
        honest=(Fraction(1, 2), Fraction(1, 2)),
        rounds=3,
        constrained=("c0",),
        ecomp=Fraction(4, 5),
        eps_lower=(Fraction(2, 5),),
        eps_upper=(Fraction(2, 5),),
        allocation_rule="uniform-default",
        box_lower=(Fraction(1, 3), Fraction(0)),
        box_upper=(Fraction(2, 3), Fraction(1)),
        m_row=4,
        rows=((1, 0), (0, 1), (-1, 0), (0, -1)),
        rhs=(Fraction(2, 3), Fraction(1), Fraction(-1, 3), Fraction(0)),
        box_sums=(Fraction(1, 3), Fraction(5, 3)),
        tight_lower=(Fraction(1, 3), Fraction(1, 3)),
        tight_upper=(Fraction(2, 3), Fraction(2, 3)),
        acceptance_support=("c0", "c1"),
        minimal_support=("c0", "c1"),
        epsilon_star=Fraction(1, 4),
        true_failure_probability=Fraction(1, 4),
        honest_contained=True,
        arithmetic="""\
THE n = 3 HALF OF THE n-NON-MONOTONICITY COUNTEREXAMPLE, Theorem thm:monotonicity-limits (v).
Every input is that of ACC-n2-singleton except n = 3.
ENDPOINTS from BTAIL-n3-p-half at the budget 2/5:
  Pr[N < 1] = 1/8 <= 2/5 , admissible ; Pr[N < 2] = 1/2 > 2/5 (5 > 4 after
    cross multiplying 1 * 5 against 2 * 2), not : kappa^- = 1 ;
  Pr[N > 1] = 1/2 > 2/5 , k = 1 not admissible ; Pr[N > 2] = 1/8 <= 2/5 ,
    admissible : kappa^+ = 2 .
GUARD: n p = 3/2, floor = 1, ceil = 2, so k^- = min{1,1} = 1 and
k^+ = max{2,2} = 2. Inert.
BOX BOUNDS: q^-(c0) = 1/3, q^+(c0) = 2/3; c1 vacuous at (0, 1). Tight bounds
[1/3, 2/3] on BOTH coordinates.
THE SET IS STRICTLY LARGER AT THE LARGER ROUND COUNT:
  AcceptSet(n = 2) = {(1/2, 1/2)}  is strictly inside
  AcceptSet(n = 3) = {q in Delta : 1/3 <= q(c0) <= 2/3} ,
with everything else -- p^hon, Chat_con, the allocation, ecomp -- held fixed. SO
AcceptSet IS NOT MONOTONE IN n.
WHY, AND WHY IT IS NOT REPAIRED. Remark rem:n-nonmono: kappa^{+-} are INTEGER
quantiles of a law whose support lattice refines with n, so the attainable tail
levels move in jumps and [k^-/n, k^+/n] can widen when n increases by one. The
asymptotic statement Eq. eq:width is unaffected -- the width still falls as
n^{-1/2} -- and no claim of the contract needs monotonicity in n. Recording the
failure is the point: a consumer that assumed "more rounds, tighter set" would
be assuming something false. THE MONOTONICITY THAT IS AVAILABLE is in ecomp,
Theorem thm:monotonicity-limits (i), and ACC-normal-2letter / ACC-budget-large freeze it.
epsilon_star: Pr[N < 1] + Pr[N > 2] = 1/8 + 1/8 = 1/4, tight (disjoint events),
inside the budget 4/5.
A SECOND NON-MONOTONICITY, frozen alongside: epsilon_star FALLS from 1/2 at
n = 2 to 1/4 at n = 3 while the set GROWS. The two quantities move in opposite
directions here, so neither can be used as a proxy for the other.""",
    ),
)


O_SA_CONSTRUCTION = SAOracleEntry(
    oracle_id="O-SA-CONSTRUCTION",
    claims=("SA4", "SA1", "SA7"),
    kind="toy-instance",
    subject=(
        "Twelve complete runs of the construction map Acc: the emitted "
        "canonical box in full (bounds, m_row, B, b), its non-emptiness sums, "
        "honest containment, the acceptance support, and -- recorded APART -- "
        "the denoted set's tight coordinate bounds."
    ),
    derivation="""\
contract.tex 0.1.2 Definition def:construction and Theorem thm:box-construction, with the
non-emptiness predicate of Theorem thm:geometry-validation (iii) and the limiting cases of
Theorem thm:monotonicity-limits (iii), (v), (vi).

WHAT IS PINNED, per case: the full admissible input; the emitted box bounds
q^-, q^+ of Eq. eq:boxbounds; m_row, B and b of Eq. eq:boxrows; the two sides of
Eq. eq:boxfeas; whether p^hon lies in the emitted set; Chat_acc; the MINIMAL
acceptance support; epsilon_star; and the exact probability that an honest run
leaves the set.

HOW EVERY NUMBER WAS OBTAINED. The per-outcome endpoints come from the frozen
tail arrays of Group SA-A by integer cross multiplication against the budget,
written out in each case; the guard is then applied by Eq. eq:guard; and the box
bounds are k^{+-}/n on Chat_con and the vacuous (0, 1) off it. Nothing is
solved, searched or iterated. Two cases (ACC-guard-active-uniform, and the
million-round guard instance it points at) rest on Bernoulli's inequality where
the exact tail is too large to tabulate, and say so.

FOUR STRUCTURAL FACTS EVERY CASE CARRIES, so that a violation is visible on any
of the twelve rather than on a special one:
  Theorem thm:box-construction (i) : every q^{+-} is an exact rational -- an integer multiple
    of 1/n on Chat_con, else 0 or 1 -- and every entry of B is in {0, +-1} ;
  Theorem thm:box-construction (ii) : 0 <= q^- <= q^+ <= 1 componentwise, so the emitted data
    IS a canonical box and the closed-form predicate applies to it ;
  Theorem thm:box-construction (iii) : p^hon lies in AcceptSet, hence the set is non-empty
    and sum q^- <= 1 <= sum q^+ follows. Frozen as `honest_contained` and
    `box_sums`, and true in all twelve -- it is unconditional, for every
    admissible ecomp, every Chat_con and every admissible allocation ;
  Remark rem:selector : m_row = 2|Chat| in every case, INDEPENDENT of Chat_con.
    ACC-guard-lower-two-counts, ACC-support-superset and
    ACC-raw-vs-tight-3letter all have a proper subset as Chat_con and still emit
    the full row set, the unconstrained coordinates carrying the vacuous bounds.

THE RAW-VERSUS-TIGHT COLUMNS, AND WHY BOTH EXIST. The emitted bounds are what
Acc produces; the tight bounds are the exact coordinate range over the DENOTED
set. They differ in SIX of the twelve cases -- ACC-guard-lower-two-counts,
ACC-support-superset, ACC-one-letter-unconstrained, ACC-raw-vs-tight-3letter,
ACC-n2-singleton and ACC-n3-wider -- and the difference is always the simplex
binding where the box does not. Every case whose Chat_con is a PROPER SUBSET of
Chat is among them, which is not a coincidence: the unconstrained coordinates
carry the vacuous [0, 1] of Eq. eq:boxbounds while sum q = 1 pins them. The
tight bounds are computed by the closed form recorded in this group's header,
which is Theorem thm:box-oracle (ii)'s own fill at g = -e_chat and g = +e_chat, so no
machinery outside the contract is used. THE RAW PAIR IS WHAT MUST BE EMITTED:
Remark rem:selector requires the vacuous bounds to be kept, and a "tightened"
box is a different artifact with the same denotation. One case is loose on a
FLOOR rather than a cap (ACC-one-letter-unconstrained), which is what
distinguishes a genuine tightening bug from a cap-only one.

THE LIMITING CASES, all of them, so that no branch of Theorem thm:monotonicity-limits is
untested:
  ecomp = 0        ACC-ecomp-zero -- AcceptSet is the WHOLE simplex ;
  |Chat| = 1       ACC-one-letter-constrained and -unconstrained, the two
                   branches of (vi), agreeing as the proof requires ;
  degenerate mass  ACC-degenerate-honest-mass (p = 0 and p = 1 on one run) ;
  non-monotone n   ACC-n2-singleton and ACC-n3-wider, the (v) counterexample ;
  budget monotone  ACC-normal-2letter inside ACC-budget-large, strictly.

WHAT IS DELIBERATELY NOT HERE. No case exercises an inadmissible input: those
are Group SA-G, and the reason they are separate is Theorem thm:honest-containment (iii) --
every infeasibility report originates in an input-domain violation and NEVER in
the construction, so a construction case and a violation case are different
kinds of object.

The twelve cases are in CONSTRUCTION_CASES.
""",
    hypotheses=(
        "The input domain of contract Section 2.1, in full.",
        "Assumption A-EXACT: p^hon, ecomp and the allocation are exact rationals.",
        "Assumption A-ALPHABET: Chat, its enumeration and n are the consuming "
        "declaration's. Not checkable from this module's inputs, and carrying "
        "no report code (Theorem thm:honest-containment (iii)).",
    ),
)


O_SA_COMPLETENESS = SAOracleEntry(
    oracle_id="O-SA-COMPLETENESS",
    claims=("SA5",),
    kind="toy-instance",
    subject=(
        "epsilon_star on all twelve frozen constructions, against the exact "
        "honest failure probability -- including the two cases where the union "
        "bound of Theorem thm:completeness-bound double-counts by exactly a factor of 2, and "
        "the four where it is tight."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:completeness-bound (Eq. eq:completeness) and Remark
rem:epsstar.

THE QUANTITY. Under Assumption A-HON,
  Pr[freq not in AcceptSet]
    <= epsilon_star
     = sum_{chat in Chat_con} ( Pr[N_chat < k^-(chat)]
                              + Pr[N_chat > k^+(chat)] )
    <= ecomp ,
each N_chat binomial with parameters (n, p^hon(chat)). Both inequalities are
frozen on every case: the left one against the exactly computed failure
probability, the right one against the declared budget.

HOW THE VALUES WERE OBTAINED. Each is a sum of at most 2|Chat_con| entries read
from the frozen tail arrays of Group SA-A at the EMITTED endpoints -- not at
kappa^{+-}, and not at the allocation. That distinction is the whole of Remark
rem:epsstar's first paragraph: the integrality of k^{+-} and the guard both
leave budget unspent, so epsilon_star is generally STRICTLY below ecomp, and
Theorem thm:sa3 (v) leaves it entirely unspent at degenerate p^hon(chat).
ACC-guard-lower-two-counts is the extreme instance: 9/10 allocated to one tail,
397/1024 spent in total.

THE THREE STEPS OF THE PROOF, each visible in the frozen data.
(1) MARGINAL LAWS. Under A-HON the indicator of {Chat_j = chat} is Bernoulli
with success probability p^hon(chat), independent across j, so N_chat is
binomial (n, p^hon(chat)). NO INDEPENDENCE ACROSS OUTCOMES IS CLAIMED OR USED --
the counts are in fact negatively related through sum_chat N_chat = n, which is
exactly why the two-letter cases below collapse.
(2) EVENT INCLUSION. Since freq is always in the simplex (Lemma
lem:freq-in-simplex), leaving AcceptSet means some coordinate leaves its box
bounds; off Chat_con the bounds are [0, 1] and CANNOT be violated. So the
failure event is the union of 2|Chat_con| count events.
(3) SUBADDITIVITY, with no independence hypothesis.

WHERE THE UNION BOUND IS LOOSE, AND BY EXACTLY HOW MUCH. On a two-letter
alphabet with Chat_con = Chat the identity N_{c1} = n - N_{c0} makes the c0
lower-tail event and the c1 upper-tail event THE SAME EVENT, and likewise the
other pair. Both such cases here are loose by a factor of EXACTLY 2:
  ACC-normal-2letter      epsilon_star 1789/32768 , truth 1789/65536 ;
  ACC-budget-large        epsilon_star 3505/8192  , truth 3505/16384 ;
  ACC-guard-active-uniform  the same collapse, with the 30-digit rational.
Where Chat_con is a SINGLETON the two events are disjoint and the bound is
TIGHT: ACC-guard-lower-two-counts (397/1024), ACC-raw-vs-tight-3letter (1/8),
ACC-n2-singleton (1/2), ACC-n3-wider (1/4). And where p^hon is degenerate or the
budget is zero, both are 0.
NEITHER BEHAVIOUR IS A DEFECT. epsilon_star is DEFINED as that sum, so the
larger figure is the contracted output; what the pairing forbids is reading
completeness_certified as the failure probability.

THE REPORTING RULE, transcribed because it is a requirement. An implementation
that cannot evaluate the tails exactly must round them UPWARD (Assumption
A-EXACT); a downward-rounded epsilon_star would claim a completeness the set
does not have. Upward rounding can push the figure above ecomp -- in the
degenerate case where every tail meets its allocation exactly and the allocation
sums to exactly ecomp -- so the rule is to report
  min{ ecomp , tilde-epsilon }   for any tilde-epsilon >= epsilon_star ,
which is again a valid bound and lies in the declared output domain [0, ecomp].
EXACT EVALUATION NEEDS NO CLAMP, because epsilon_star <= ecomp is part of
Eq. eq:completeness -- and every case here is exact, so no case exercises the
clamp. That is a gap in COVERAGE, not in the contract, and it is named here
rather than papered over: a test of the clamp needs an inexact evaluator, which
is an implementation object run B may or may not build.

SOUNDNESS DOES NOT DEPEND ON ANY OF THIS. Remark rem:sound-indep: A-HON is a
statement about the honest channel, used only in SA5, SA7 (iv) and SA9. If the
true honest channel differs from the declared p^hon, epsilon_star is VOID and
the protocol may abort more often than advertised; the key produced on the runs
that DO accept is unaffected, because AcceptSet enters the security statement
only as the fixed set h_low is an infimum over. A usability failure, never a
security one.

The values are the `epsilon_star` and `true_failure_probability` fields of
CONSTRUCTION_CASES.
""",
    hypotheses=(
        "Assumption A-HON: the honest acceptance statistics are i.i.d. with "
        "law p^hon. Asserted about the honest channel only, never against an "
        "adversary.",
        "Assumption A-TSM: p^hon is the law of Chat_j, i.e. the provider "
        "supplies joint per-outcome counts on Chat and not a sifted QBER.",
    ),
)


O_SA_BUDGET_MONOTONE = SAOracleEntry(
    oracle_id="O-SA-BUDGET-MONOTONE",
    claims=("SA7",),
    kind="structural-identity",
    subject=(
        "Theorem thm:monotonicity-limits (i)-(ii) on a frozen pair: the acceptance set SHRINKS "
        "as the completeness budget grows, strictly, and every infimum over it "
        "-- the consumer's h_low among them -- is therefore NON-DECREASING in "
        "ecomp."
    ),
    derivation="""\
contract.tex 0.1.2 Definition def:monotone-rule and Theorem thm:monotonicity-limits (i)-(ii),
on the pair ACC-normal-2letter (e_1 = 1/5) and ACC-budget-large (e_2 = 4/5).
Everything else is held fixed: Chat = (c0, c1), p^hon = (3/4, 1/4), n = 8,
Chat_con = Chat, and the DEFAULT UNIFORM RULE, which Definition
def:monotone-rule records as monotone -- e |-> e / (2 |Chat_con|) is
non-decreasing in e, coordinatewise.

THE FROZEN INCLUSION.
  AcceptSet(4/5) : q(c0) in [5/8, 7/8] , q(c1) in [1/8, 3/8] ;
  AcceptSet(1/5) : q(c0) in [4/8, 8/8] , q(c1) in [0/8, 4/8] ;
so AcceptSet(4/5) is inside AcceptSet(1/5), and STRICTLY at all four endpoints.
A LARGER BUDGET BUYS A SMALLER SET, which is the direction the claim table
states and the opposite of the one a reader expecting "budget buys room" would
guess.

WHY, IN ONE LINE PER STEP (proof of Theorem thm:monotonicity-limits (i)). Raising the budget
raises each eps^{+-}(chat) under a monotone rule; the admissible set of
eq:kappaminus GROWS when its threshold grows, so its MAXIMUM kappa^- does not
decrease; the admissible set of eq:kappaplus likewise grows, so its MINIMUM
kappa^+ does not increase; both guards in Eq. eq:guard are monotone in their
first argument; hence k^- does not decrease and k^+ does not increase, and the
count interval SHRINKS. Off Chat_con the bounds are [0, 1] at both budgets.
The frozen endpoints exhibit each step: kappa^- moves 4 -> 5 on c0 and 0 -> 1 on
c1, kappa^+ moves 8 -> 7 on c0 and 4 -> 3 on c1.

(ii) THE CONSEQUENCE FOR ANY CONSUMER INFIMUM. For every
Psi : Delta(Chat) -> [-inf, +inf] and e_1 <= e_2,
  inf over AcceptSet(e_1) of Psi  <=  inf over AcceptSet(e_2) of Psi ,
because an infimum over a SUBSET is at least the infimum over the superset. No
continuity, convexity or measurability of Psi is needed, and the extended reals
are admitted -- which matters, because the consumer's h_low takes the value
+infinity on an infeasible declaration (its Remark rem:hlow-range) and the
statement must survive that.
SPECIALIZED: h_low, defined by the consumer as an infimum over AcceptSet of an
infimum over its feasible set, is NON-DECREASING in ecomp. A WEAKER COMPLETENESS
GUARANTEE BUYS A LARGER ENTROPY BOUND. The contract adds the reading, and the
registry keeps it: THIS IS A TRADE-OFF, NOT AN IMPROVEMENT -- the same change
makes the honest run abort more often, and epsilon_star rises with it, from
1789/32768 to 3505/8192 on this very pair.

THE SAME MONOTONICITY IS WHAT MAKES A-EXACT'S ROUNDING DIRECTION SAFE. Its
ledger cell cites this step by name: a rounding-induced ENLARGEMENT of AcceptSet
lowers the consumer's h_low, by the same infimum-over-a-superset argument, and
costs rate rather than soundness. It is NOT a budget change -- the declared
ecomp is untouched -- which is why the two must not be conflated.

WHAT IS NOT MONOTONE. The round count: ACC-n2-singleton and ACC-n3-wider are
strictly ordered the WRONG way, and O-SA-N-NONMONOTONE freezes that.
""",
    hypotheses=(
        "A MONOTONE allocation rule (Definition def:monotone-rule). The claim "
        "is FALSE for an arbitrary pair of allocations, and the default "
        "uniform rule is the instance the contract certifies.",
        "Both budgets in [0, 1).",
    ),
)


O_SA_N_NONMONOTONE = SAOracleEntry(
    oracle_id="O-SA-N-NONMONOTONE",
    claims=("SA7",),
    kind="structural-identity",
    subject=(
        "Theorem thm:monotonicity-limits (v): AcceptSet is NOT monotone in n. At n = 2 the set "
        "is the single point (1/2, 1/2); at n = 3, with every other input "
        "unchanged, it is strictly larger."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:monotonicity-limits (v) and Remark rem:n-nonmono, re-derived from
BTAIL-n2-p-half and BTAIL-n3-p-half rather than copied from the contract's
display.

THE INPUT, identical but for n: Chat = (c0, c1), p^hon = (1/2, 1/2),
Chat_con = {c0}, eps^-(c0) = eps^+(c0) = 2/5, hence ecomp = 4/5.

n = 2. The law of N_{c0} is (1/4, 1/2, 1/4) on {0, 1, 2}.
  Pr[N < 0] = 0 <= 2/5 and Pr[N < 1] = 1/4 <= 2/5, but Pr[N < 2] = 3/4 > 2/5, so
    kappa^- = 1 ;
  Pr[N > 0] = 3/4 > 2/5 and Pr[N > 1] = 1/4 <= 2/5, so kappa^+ = 1 .
The guard is inert, floor(1) = ceil(1) = 1, so [k^-, k^+] = [1, 1] and
q(c0) = 1/2, which on a two-letter alphabet forces q = (1/2, 1/2):
  AcceptSet(n = 2) = {(1/2, 1/2)} .

n = 3. The law is (1/8, 3/8, 3/8, 1/8) on {0, 1, 2, 3}.
  Pr[N < 1] = 1/8 <= 2/5 but Pr[N < 2] = 1/2 > 2/5, so kappa^- = 1 ;
  Pr[N > 1] = 1/2 > 2/5 and Pr[N > 2] = 1/8 <= 2/5, so kappa^+ = 2 .
The guard is again inert, floor(3/2) = 1 and ceil(3/2) = 2, so
[k^-, k^+] = [1, 2] and
  AcceptSet(n = 3) = { q in Delta(Chat) : 1/3 <= q(c0) <= 2/3 } .

THE CONCLUSION: AcceptSet(n = 2) is STRICTLY inside AcceptSet(n = 3). More
rounds, LOOSER set.

WHY IT HAPPENS, AND WHY THE CONTRACT STATES IT RATHER THAN REPAIRING IT
(Remark rem:n-nonmono). kappa^{+-} are INTEGER quantiles of a distribution whose
support lattice refines with n, so the attainable tail levels move in jumps and
[k^-/n, k^+/n] can widen when n increases by one. The asymptotic statement
Eq. eq:width is unaffected -- the half-width still falls as n^{-1/2} -- and no
claim of the contract needs monotonicity in n. Recording the failure is the
point: a consumer that assumed "more rounds, tighter set" would be assuming
something false, and the R9 discipline is to say so rather than leave the
direction unexamined.
THE MONOTONICITY THAT IS AVAILABLE, and that a consumer MAY rely on, is in
ecomp: Theorem thm:monotonicity-limits (i), frozen in O-SA-BUDGET-MONOTONE, with the direction
stated there.

A SECOND REVERSAL ON THE SAME PAIR: epsilon_star FALLS from 1/2 to 1/4 while the
set GROWS. So epsilon_star is not a proxy for the set's size either, in either
direction.
""",
    hypotheses=(
        "Everything except n held fixed, the allocation included. The "
        "counterexample says nothing about varying n and the allocation "
        "together.",
    ),
)


O_SA_WIDTH_BOUND = SAOracleEntry(
    oracle_id="O-SA-WIDTH-BOUND",
    claims=("SA7",),
    kind="analytic-limit",
    subject=(
        "Theorem thm:monotonicity-limits (iv) and Lemma lem:cheb: the O(n^{-1/2}) half-width "
        "bound Eq. eq:width, checked in EXACT SQUARED FORM on frozen "
        "constructions, together with the Chebyshev inequality it rests on."
    ),
    derivation="""\
contract.tex 0.1.2 Lemma lem:cheb and Theorem thm:monotonicity-limits (iv).

LEMMA lem:cheb, PROVED FROM SCRATCH IN THE CONTRACT and checked here on data.
For N binomial (n, p) and t > 0, Pr[|N - n p| >= t] <= n p (1-p) / t^2. On
n = 8, p = 3/4 (BTAIL-n8-p-three-quarters), n p = 6 and the variance is
  Var(N) = n p (1-p) = 8 * (3/4) * (1/4) = 3/2 .
At t = 2 the bound is (3/2)/4 = 3/8, and the exact left-hand side is
  Pr[|N - 6| >= 2] = Pr[N <= 4] + Pr[N >= 8]
                   = 7459/65536 + 6561/65536 = 14020/65536 = 3505/16384 ,
about 0.2139 against a bound of 0.375. THE BOUND HOLDS AND IS LOOSE, as
Chebyshev is; the frozen pair is (3505/16384, 3/8).

THEOREM thm:monotonicity-limits (iv), Eq. eq:width. For chat in Chat_con with
0 < p < 1 and eps^{+-}(chat) > 0,
  0 <= q^+(chat) - p <= sqrt( p(1-p) / (n eps^+(chat)) ) + 1/n ,
  0 <= p - q^-(chat) <= sqrt( p(1-p) / (n eps^-(chat)) ) + 1/n .
THE SQUARE ROOT IS THE ONLY IRRATIONAL QUANTITY ANYWHERE IN THIS CONTRACT, and
it appears in a BOUND rather than in an emitted value. To keep this registry
exact the check is frozen in SQUARED FORM, which is equivalent because both
sides are non-negative once 1/n is moved across:
  ( q^+(chat) - p - 1/n )^2 <= p(1-p) / (n eps^+(chat))
      whenever q^+(chat) - p >= 1/n , and trivially otherwise ,
and symmetrically below. Every quantity in that inequality is rational.

THE FROZEN INSTANCES.
  ACC-normal-2letter, c0 : p = 3/4, n = 8, eps^{+-} = 1/20, q^+ = 1, q^- = 1/2.
    Upper : q^+ - p - 1/n = 1/4 - 1/8 = 1/8 , squared 1/64 ;
            p(1-p)/(n eps^+) = (3/16) / (8/20) = (3/16)(20/8) = 15/32 ;
            1/64 <= 15/32 , i.e. 1 <= 30 over 64ths. HOLDS.
    Lower : p - q^- - 1/n = 1/4 - 1/8 = 1/8 , same comparison. HOLDS.
  ACC-budget-large, c0 : p = 3/4, n = 8, eps^{+-} = 1/5, q^+ = 7/8, q^- = 5/8.
    Upper : q^+ - p - 1/n = 1/8 - 1/8 = 0 , squared 0 ;
            p(1-p)/(n eps^+) = (3/16) / (8/5) = 15/128 ; 0 <= 15/128. HOLDS,
            with the deviation exactly at the 1/n term -- the tightest of the
            four.
    Lower : p - q^- - 1/n = 1/8 - 1/8 = 0 . HOLDS.
  ACC-budget-large, c1 : p = 1/4, n = 8, eps^{+-} = 1/5, q^+ = 3/8, q^- = 1/8.
    Both sides give 0 <= 15/128 by the same arithmetic. HOLDS.

THE 1/n TERM IS NOT DECORATION. It absorbs two separate integer effects: the
ceiling in k = ceil(n p + t) in the upper proof, and the floor in
k' = max{0, floor(n p - t')} in the lower one -- including the CLIPPED branch,
where floor(n p - t') <= 0 forces k' = 0 and the argument runs through
n p - t' < 1 instead. The 0-deviation instances above are exactly where an
implementation that dropped it would still pass, which is why the 1/8-deviation
instance is frozen alongside.

THE HAUSDORFF CONSEQUENCE, not frozen as a number because it is asymptotic:
with Chat_con = Chat, 0 < p^hon(chat) < 1 for all chat, and the allocation held
fixed as n grows, sup over AcceptSet of ||q - p^hon||_infinity is O(n^{-1/2})
and AcceptSet converges to {p^hon} in Hausdorff distance -- the other half of
the distance being 0 because p^hon is always IN the set (Theorem thm:box-construction (iii)).
THE BOUND IS PROVED FOR THE GUARDED ENDPOINTS, with no side condition, so the
guard never breaks it: that is the sense in which Remark rem:guard calls the
guard cheap, and it is compatible with the guard's cost against the RAW interval
being unbounded, because the two measure different things.
""",
    value=Fraction(3505, 16384),
    hypotheses=(
        "Assumption A-HON (the count is binomial at all).",
        "0 < p^hon(chat) < 1 and eps^{+-}(chat) > 0: Eq. eq:width is vacuous or "
        "undefined otherwise, and the degenerate masses are Theorem "
        "thm:sa3 (v) instead.",
    ),
)


# ===========================================================================
#  Group SA-E -- the acceptance support and the exact box oracle (SA8)
# ===========================================================================
#
#  Theorem thm:box-oracle has three parts, and they bind the implementation surface
#  DIFFERENTLY. That split is recorded as a judgement call in interface.yaml
#  (claims.SA8.interface_binding_judgement) and is repeated here because it
#  decides what a disagreement with these numbers means:
#
#    (i)   IS an interface obligation of this module. The Outputs table carries
#          a row `acceptance_support` and names Claim SA8 (i) in its domain
#          cell, so Chat_acc MUST be emitted, with that row's formula.
#    (ii)  and (iii) are PROVEN FACTS ABOUT THE EMITTED GEOMETRY, not outputs.
#          Neither g, nor min <g, q>, nor (u, v), nor beta_acc appears in the
#          Inputs or Outputs table; Remark rem:box-oracle-consumer says Eq.
#          eq:bacc-shape is the CONSUMING contract's input obligation and that
#          the closed form is "an implementation consequence of this contract's
#          geometry". An implementation of THIS module may expose the oracle or
#          not; if it does, the values are FIXED by Eqs. eq:greedy,
#          eq:exactmin, eq:dualfeas and eq:dualvalue and are frozen below.
#          WHAT IT MAY NOT DO IS EMIT A NUMBER AS beta_acc: that quantity is
#          admitted by the consuming contract only through ITS OWN
#          admissibility check on g + B^T u + v.
#
#  TWO ENUMERATIONS, AND THEY ARE DIFFERENT (contract Section 3, Notation). The
#  rows of B are ALWAYS indexed by the DECLARATION's enumeration
#  chat^(1), ..., chat^(m). Theorem thm:box-oracle introduces a SECOND enumeration
#  c_1, ..., c_m induced by sorting g ASCENDING, and uses it only to define
#  j^*, lambda and q^opt. Every pairing with B or b is a sum over Chat and is
#  therefore independent of which enumeration is used. Below, `sorted_order` is
#  the second one and every vector field is in the FIRST.


@dataclass(frozen=True)
class BoxMinimumCase:
    """One hand-derived minimum of ``<g, q>`` over a canonical box Acc emits."""

    case_id: str
    #: The construction case whose emitted box this is.
    source_case: str
    #: The declaration's enumeration of Chat, in order.
    outcomes: tuple[str, ...]
    box_lower: tuple[Fraction, ...]
    box_upper: tuple[Fraction, ...]
    #: The exact objective vector g, in `outcomes` order.
    g: tuple[Fraction, ...]
    #: Chat_acc = {chat : q^+(chat) > 0}, the Outputs-table formula.
    acceptance_support: tuple[str, ...]
    #: The enumeration c_1, ..., c_m of Theorem thm:box-oracle (ii): g ascending.
    sorted_order: tuple[str, ...]
    #: r = 1 - sum q^-, the residual mass above the floors.
    residual_r: Fraction
    #: D_i = q^+(c_i) - q^-(c_i), in `sorted_order`.
    widths: tuple[Fraction, ...]
    #: The least index whose prefix width reaches r, named by outcome.
    j_star: str
    #: w = r - sum_{i < j^*} D_i, the fill increment at the split.
    fill_increment: Fraction
    #: q^opt of Eq. eq:greedy, in `outcomes` order.
    q_opt: tuple[Fraction, ...]
    #: Every minimizer this case pins: one point when the argmin is unique, and
    #: two vertices when the objective is constant on the set.
    minimizers: tuple[tuple[Fraction, ...], ...]
    minimum: Fraction
    #: lambda = g(c_{j^*}) and v = -lambda.
    lam: Fraction
    dual_v: Fraction
    #: u = (u^+, u^-) in ROW order: the m caps first, then the m floors, both
    #: in the DECLARATION's enumeration.
    dual_u: tuple[Fraction, ...]
    #: b of Eq. eq:boxrows, in the same row order.
    rhs: tuple[Fraction, ...]
    #: g + B^T u + v, per outcome. Zero in every coordinate: Eq. eq:dualfeas
    #: holds with EQUALITY, which is why the bound is tight.
    dual_feasibility: tuple[Fraction, ...]
    #: -<b, u> - v. Equals `minimum` in every case: the witness is tight.
    dual_value: Fraction
    elimination_route: str
    arithmetic: str


BOX_MINIMUM_CASES: tuple[BoxMinimumCase, ...] = (
    BoxMinimumCase(
        case_id="PMIN-normal-fill-at-cap",
        source_case="ACC-normal-2letter",
        outcomes=("c0", "c1"),
        box_lower=(Fraction(1, 2), Fraction(0)),
        box_upper=(Fraction(1), Fraction(1, 2)),
        g=(Fraction(3), Fraction(1)),
        acceptance_support=("c0", "c1"),
        sorted_order=("c1", "c0"),
        residual_r=Fraction(1, 2),
        widths=(Fraction(1, 2), Fraction(1, 2)),
        j_star="c1",
        fill_increment=Fraction(1, 2),
        q_opt=(Fraction(1, 2), Fraction(1, 2)),
        minimizers=((Fraction(1, 2), Fraction(1, 2)),),
        minimum=Fraction(2),
        lam=Fraction(1),
        dual_v=Fraction(-1),
        dual_u=(Fraction(0), Fraction(0), Fraction(2), Fraction(0)),
        rhs=(Fraction(1), Fraction(1, 2), Fraction(-1, 2), Fraction(0)),
        dual_feasibility=(Fraction(0), Fraction(0)),
        dual_value=Fraction(2),
        elimination_route="""\
Put a = q(c0), so q(c1) = 1 - a and the objective becomes
  <g, q> = 3a + 1(1 - a) = 1 + 2a ,
an increasing affine function of a. The box gives a in [1/2, 1] directly, and
q(c1) = 1 - a in [0, 1/2] gives the same interval, so the constraint set in a is
[1/2, 1] and the minimum is at a = 1/2:
  min = 1 + 2(1/2) = 2 .
No step of this route uses the fill, the sorted order or j^*.""",
        arithmetic="""\
THE BOX ACC-normal-2letter EMITS, minimized against g = (3, 1).
  q^- = (1/2, 0) , q^+ = (1, 1/2) , NON-EMPTY since 1/2 <= 1 <= 3/2 .
ROUTE 1, THE EXCHANGE ARGUMENT (Eq. eq:greedy). Order the outcomes by g
ASCENDING: c1 (g = 1) then c0 (g = 3), so c_1 = c1 and c_2 = c0.
  r = 1 - sum q^- = 1 - 1/2 = 1/2 ,
  D(c1) = 1/2 - 0 = 1/2 , D(c0) = 1 - 1/2 = 1/2 .
j^* is the LEAST index whose prefix width reaches r, and the prefix at c1 is
already 1/2 >= 1/2, so j^* = c1. The fill increment is
  w = r - (empty sum) = 1/2 ,
and w = D(c1) EXACTLY -- the fill stops precisely AT the cheapest outcome's cap,
which is the boundary between "stops strictly inside" (PMIN-fill-strictly-inside)
and "spills past this outcome onto the next". Eq. eq:greedy then gives
  q^opt(c1) = q^-(c1) + w = 0 + 1/2 = 1/2   (the split index) ,
  q^opt(c0) = q^-(c0) = 1/2                 (above the split) ,
summing to 1 and lying in the box, so q^opt is feasible. Its value is
  <g, q^opt> = 3(1/2) + 1(1/2) = 3/2 + 1/2 = 2 .
OPTIMALITY IN ONE LINE, the identity in the proof of Theorem thm:box-oracle (ii). With
lambda = g(c_{j^*}) = 1 and sum_i (q(c_i) - q^opt(c_i)) = 1 - 1 = 0,
  <g,q> - <g,q^opt> = sum_i (g(c_i) - lambda)(q(c_i) - q^opt(c_i)) ,
and every summand is >= 0: below the split g - lambda <= 0 while
q <= q^+ = q^opt, above it g - lambda >= 0 while q >= q^- = q^opt, and at the
split the first factor is 0. Here the only non-split index is c0, where
g - lambda = 2 >= 0 and q(c0) - 1/2 >= 0 because q^-(c0) = 1/2.
ROUTE 2 is in elimination_route and shares no step with this one. The two agree.
THE WITNESS, in the format Remark rem:acc-side (b) of the CONSUMING contract
expects (Theorem thm:box-oracle (iii)). lambda = 1, v = -lambda = -1, and
  u^+(chat) = max{lambda - g(chat), 0} = (0, 0) ,
  u^-(chat) = max{g(chat) - lambda, 0} = (2, 0) ,
so in ROW order -- caps first, then floors, both in the declaration's
enumeration -- u = (0, 0, 2, 0) >= 0.
DUAL FEASIBILITY, Eq. eq:dualfeas, using B^T u = u^+ - u^-:
  c0 : 3 + (0 - 2) + (-1) = 0 ,   c1 : 1 + (0 - 0) + (-1) = 0 ,
so g + B^T u + v = (0, 0). IT IS ZERO, NOT MERELY >= 0, AND THAT IS THE POINT:
the consuming remark only requires the componentwise inequality, and equality is
exactly why the resulting bound is TIGHT rather than conservative.
DUAL VALUE, Eq. eq:dualvalue, with b = (1, 1/2, -1/2, 0):
  <b, u> = (1)(0) + (1/2)(0) + (-1/2)(2) + (0)(0) = -1 ,
  -<b, u> - v = 1 - (-1) = 2 ,
THE PRIMAL MINIMUM AGAIN. THE WITNESS IS A THIRD CHECK, NOT THE DERIVATION.""",
    ),
    BoxMinimumCase(
        case_id="PMIN-fill-strictly-inside",
        source_case="ACC-raw-vs-tight-3letter",
        outcomes=("c0", "c1", "c2"),
        box_lower=(Fraction(1, 4), Fraction(0), Fraction(0)),
        box_upper=(Fraction(3, 4), Fraction(1), Fraction(1)),
        g=(Fraction(1), Fraction(2), Fraction(5)),
        acceptance_support=("c0", "c1", "c2"),
        sorted_order=("c0", "c1", "c2"),
        residual_r=Fraction(3, 4),
        widths=(Fraction(1, 2), Fraction(1), Fraction(1)),
        j_star="c1",
        fill_increment=Fraction(1, 4),
        q_opt=(Fraction(3, 4), Fraction(1, 4), Fraction(0)),
        minimizers=((Fraction(3, 4), Fraction(1, 4), Fraction(0)),),
        minimum=Fraction(5, 4),
        lam=Fraction(2),
        dual_v=Fraction(-2),
        dual_u=(
            Fraction(1),
            Fraction(0),
            Fraction(0),
            Fraction(0),
            Fraction(0),
            Fraction(3),
        ),
        rhs=(
            Fraction(3, 4),
            Fraction(1),
            Fraction(1),
            Fraction(-1, 4),
            Fraction(0),
            Fraction(0),
        ),
        dual_feasibility=(Fraction(0), Fraction(0), Fraction(0)),
        dual_value=Fraction(5, 4),
        elimination_route="""\
Put a = q(c0) and b = q(c1), so q(c2) = 1 - a - b and
  <g, q> = a + 2b + 5(1 - a - b) = 5 - 4a - 3b .
Minimizing that is MAXIMIZING 4a + 3b subject to a in [1/4, 3/4], b in [0, 1],
and q(c2) = 1 - a - b in [0, 1], i.e. a + b <= 1. The larger coefficient sits on
a, so push a to its cap 3/4; then b <= 1 - 3/4 = 1/4 binds before b's own cap of
1, giving b = 1/4:
  max (4a + 3b) = 3 + 3/4 = 15/4 ,   min = 5 - 15/4 = 5/4 .
The maximizer is unique because both coefficients are positive and both binding
constraints are, so the minimizer is unique too.""",
        arithmetic="""\
THE FILL STOPPING STRICTLY INSIDE A COORDINATE'S RANGE -- neither at its floor
nor at its cap -- on the box ACC-raw-vs-tight-3letter emits, against
g = (1, 2, 5).
  q^- = (1/4, 0, 0) , q^+ = (3/4, 1, 1) , NON-EMPTY since 1/4 <= 1 <= 11/4 .
ROUTE 1, THE EXCHANGE ARGUMENT. g is already ascending, so c_1 = c0, c_2 = c1,
c_3 = c2.
  r = 1 - sum q^- = 1 - 1/4 = 3/4 ,
  D = (D(c0), D(c1), D(c2)) = (1/2, 1, 1) .
PREFIX WIDTHS: 1/2 at c0, which is < 3/4; 1/2 + 1 = 3/2 at c1, which is >= 3/4.
So j^* = c1, and the fill increment is
  w = r - D(c0) = 3/4 - 1/2 = 1/4 ,
with 0 < w = 1/4 < 1 = D(c1) STRICTLY. Eq. eq:greedy gives
  q^opt(c0) = q^+(c0) = 3/4      (below the split: filled to the cap) ,
  q^opt(c1) = q^-(c1) + w = 1/4  (the split: partially filled) ,
  q^opt(c2) = q^-(c2) = 0        (above the split: left at the floor) ,
summing to 3/4 + 1/4 + 0 = 1. Value:
  <g, q^opt> = 1(3/4) + 2(1/4) + 5(0) = 3/4 + 1/2 = 5/4 .
WHY THIS CASE EXISTS. The two other fill regimes are degenerate in a way that
hides an off-by-one: PMIN-normal-fill-at-cap stops exactly at a cap (w = D), and
PMIN-degenerate-point has w = 0. Here w is strictly between the two, so an
implementation that mishandles the split index -- filling it to its cap, or
leaving it at its floor -- returns 1(3/4) + 2(1) + 5(-3/4)... more simply,
returns a vector that does not sum to 1 at all, and the error is visible in the
normalization before it is visible in the value.
ROUTE 2 is in elimination_route and shares no step. The two agree at 5/4.
THE WITNESS. lambda = g(c_{j^*}) = g(c1) = 2, v = -2, and
  u^+(chat) = max{2 - g(chat), 0} = (1, 0, 0) ,
  u^-(chat) = max{g(chat) - 2, 0} = (0, 0, 3) ,
so in row order u = (1, 0, 0, 0, 0, 3) >= 0.
DUAL FEASIBILITY, Eq. eq:dualfeas:
  c0 : 1 + (1 - 0) + (-2) = 0 ,
  c1 : 2 + (0 - 0) + (-2) = 0 ,
  c2 : 5 + (0 - 3) + (-2) = 0 ,
zero in every coordinate, hence >= 0 componentwise as the consuming remark
requires, and TIGHT.
DUAL VALUE, with b = (3/4, 1, 1, -1/4, 0, 0):
  <b, u> = (3/4)(1) + 0 + 0 + (-1/4)(0) + 0 + (0)(3) = 3/4 ,
  -<b, u> - v = -3/4 + 2 = 5/4 .
Note the c2 FLOOR multiplier is 3 and contributes NOTHING, its right-hand side
being -q^-(c2) = 0: a large multiplier on a costless row is legal, and it is the
shape an implementation that expects small u will get wrong.""",
    ),
    BoxMinimumCase(
        case_id="PMIN-floors-carry-the-mass",
        source_case="ACC-budget-large",
        outcomes=("c0", "c1"),
        box_lower=(Fraction(5, 8), Fraction(1, 8)),
        box_upper=(Fraction(7, 8), Fraction(3, 8)),
        g=(Fraction(1), Fraction(4)),
        acceptance_support=("c0", "c1"),
        sorted_order=("c0", "c1"),
        residual_r=Fraction(1, 4),
        widths=(Fraction(1, 4), Fraction(1, 4)),
        j_star="c0",
        fill_increment=Fraction(1, 4),
        q_opt=(Fraction(7, 8), Fraction(1, 8)),
        minimizers=((Fraction(7, 8), Fraction(1, 8)),),
        minimum=Fraction(11, 8),
        lam=Fraction(1),
        dual_v=Fraction(-1),
        dual_u=(Fraction(0), Fraction(0), Fraction(0), Fraction(3)),
        rhs=(Fraction(7, 8), Fraction(3, 8), Fraction(-5, 8), Fraction(-1, 8)),
        dual_feasibility=(Fraction(0), Fraction(0)),
        dual_value=Fraction(11, 8),
        elimination_route="""\
Put a = q(c0), so q(c1) = 1 - a and
  <g, q> = a + 4(1 - a) = 4 - 3a ,
decreasing in a, so minimizing means maximizing a. The box gives a <= 7/8, and
q(c1) = 1 - a >= 1/8 gives a <= 7/8 as well; the floors give a >= 5/8 and
a <= 7/8 from the other side. So a = 7/8 and
  min = 4 - 3(7/8) = 4 - 21/8 = 11/8 .""",
        arithmetic="""\
A BOX WITH NON-ZERO FLOORS ON EVERY COORDINATE -- the box ACC-budget-large emits
-- against g = (1, 4). This is the case where the residual mass is SMALL because
the floors already carry most of the normalization.
  q^- = (5/8, 1/8) , q^+ = (7/8, 3/8) , NON-EMPTY since 3/4 <= 1 <= 5/4 .
ROUTE 1, THE EXCHANGE ARGUMENT. g ascending: c_1 = c0 (g = 1), c_2 = c1 (g = 4).
  r = 1 - sum q^- = 1 - 3/4 = 1/4 ,
  D(c0) = 7/8 - 5/8 = 1/4 , D(c1) = 3/8 - 1/8 = 1/4 .
The prefix at c0 is 1/4 >= 1/4, so j^* = c0 -- THE VERY FIRST INDEX -- and
  w = r - (empty sum) = 1/4 = D(c0) .
Eq. eq:greedy gives
  q^opt(c0) = q^-(c0) + w = 5/8 + 1/4 = 7/8 ,
  q^opt(c1) = q^-(c1) = 1/8 ,
summing to 1. Value:
  <g, q^opt> = 1(7/8) + 4(1/8) = 7/8 + 4/8 = 11/8 .
WHAT AN IMPLEMENTATION THAT FORGETS sum q = 1 RETURNS. Minimizing over the BOX
ALONE puts every coordinate at its floor: (5/8, 1/8), value
5/8 + 4/8 = 9/8 < 11/8. SMALLER THAN THE TRUE MINIMUM -- so still a sound
beta_acc for the consumer, and WRONG: it is the minimum of a set the declaration
never named, and the vector does not even sum to 1. The error is conservative
and therefore invisible in the sign of any downstream bound, which is why the
VALUE is frozen and not merely its direction.
THE OTHER DIRECTION IS UNSOUND. Evaluating g at the feasible NON-optimal point
(5/8, 3/8) gives 5/8 + 12/8 = 17/8 > 11/8. A beta_acc above the true minimum is
exactly what the consuming contract's admissibility check exists to refuse.
ROUTE 2 is in elimination_route and agrees at 11/8.
THE WITNESS. lambda = g(c0) = 1, v = -1,
  u^+ = max{1 - g, 0} = (0, 0) ,  u^- = max{g - 1, 0} = (0, 3) ,
so u = (0, 0, 0, 3) in row order.
DUAL FEASIBILITY: c0 : 1 + 0 + (-1) = 0 ; c1 : 4 + (0 - 3) + (-1) = 0 .
DUAL VALUE, with b = (7/8, 3/8, -5/8, -1/8):
  <b, u> = (-1/8)(3) = -3/8 ,  -<b, u> - v = 3/8 + 1 = 11/8 .""",
    ),
    BoxMinimumCase(
        case_id="PMIN-degenerate-point",
        source_case="ACC-degenerate-honest-mass",
        outcomes=("c0", "c1"),
        box_lower=(Fraction(1), Fraction(0)),
        box_upper=(Fraction(1), Fraction(0)),
        g=(Fraction(2), Fraction(-1)),
        acceptance_support=("c0",),
        sorted_order=("c1", "c0"),
        residual_r=Fraction(0),
        widths=(Fraction(0), Fraction(0)),
        j_star="c1",
        fill_increment=Fraction(0),
        q_opt=(Fraction(1), Fraction(0)),
        minimizers=((Fraction(1), Fraction(0)),),
        minimum=Fraction(2),
        lam=Fraction(-1),
        dual_v=Fraction(1),
        dual_u=(Fraction(0), Fraction(0), Fraction(3), Fraction(0)),
        rhs=(Fraction(1), Fraction(0), Fraction(-1), Fraction(0)),
        dual_feasibility=(Fraction(0), Fraction(0)),
        dual_value=Fraction(2),
        elimination_route="""\
There is nothing to eliminate: q^- = q^+ forces q = (1, 0) coordinatewise, and
that vector sums to 1, so the feasible set is the single point and the minimum
is an EVALUATION,
  <g, q> = 2(1) + (-1)(0) = 2 .""",
        arithmetic="""\
THE DEGENERATE FILL, on the box ACC-degenerate-honest-mass emits -- a box whose
every width is zero -- against g = (2, -1). This is where an implementation runs
off the end of its own loop.
  q^- = q^+ = (1, 0) , NON-EMPTY WITH EQUALITY AT BOTH ENDS: 1 <= 1 <= 1 .
ROUTE 1. g ascending: c_1 = c1 (g = -1), c_2 = c0 (g = 2).
  r = 1 - sum q^- = 1 - 1 = 0 ,   D(c1) = 0 , D(c0) = 0 .
j^* IS THE LEAST INDEX WHOSE PREFIX WIDTH REACHES r, AND THAT IS THE FIRST ONE,
because 0 >= 0. AN IMPLEMENTATION THAT LOOKS FOR A STRICT INEQUALITY FINDS NO
INDEX AT ALL HERE, and one that then returns the floor vector by accident gets
the right answer for the wrong reason, while one that raises rejects a case both
contracts call supported. The fill increment is
  w = r - (empty sum) = 0 ,
so q^opt(c1) = q^-(c1) + 0 = 0 and q^opt(c0) = q^-(c0) = 1, i.e. q^opt = q^-,
which sums to 1. Value:
  <g, q^opt> = 2(1) + (-1)(0) = 2 .
NOTE THAT THE CHEAPEST OUTCOME IS c1, WITH g = -1, AND IT GETS NOTHING. That is
correct and is the whole content of the case: the floors have already spent the
entire normalization, so no mass is free to move to the cheap outcome. An
implementation that "obviously" puts mass where g is smallest returns
2(0) + (-1)(1) = -1, an UNSOUND under-estimate of a minimum over a set that does
not contain (0, 1).
ROUTE 2 is in elimination_route -- the feasible set is a point -- and agrees.
THE ACCEPTANCE SUPPORT IS STRICTLY SMALLER THAN Chat here: q^+(c1) = 0, so
Chat_acc = {c0}. The sum in Eq. eq:bacc-shape runs over Chat_acc only, and
dropping the c1 term changes nothing because q(c1) = 0 identically -- 2(1) = 2.
THE WITNESS. lambda = g(c_{j^*}) = g(c1) = -1, v = 1,
  u^+ = max{-1 - g, 0} = (0, 0) ,   u^- = max{g + 1, 0} = (3, 0) ,
so u = (0, 0, 3, 0) in row order.
DUAL FEASIBILITY: c0 : 2 + (0 - 3) + 1 = 0 ; c1 : -1 + (0 - 0) + 1 = 0 .
DUAL VALUE, with b = (1, 0, -1, 0):
  <b, u> = (-1)(3) = -3 ,   -<b, u> - v = 3 - 1 = 2 .""",
    ),
    BoxMinimumCase(
        case_id="PMIN-box-superset",
        source_case="ACC-support-superset",
        outcomes=("c0", "c1"),
        box_lower=(Fraction(1), Fraction(0)),
        box_upper=(Fraction(1), Fraction(1)),
        g=(Fraction(5), Fraction(-2)),
        acceptance_support=("c0", "c1"),
        sorted_order=("c1", "c0"),
        residual_r=Fraction(0),
        widths=(Fraction(1), Fraction(0)),
        j_star="c1",
        fill_increment=Fraction(0),
        q_opt=(Fraction(1), Fraction(0)),
        minimizers=((Fraction(1), Fraction(0)),),
        minimum=Fraction(5),
        lam=Fraction(-2),
        dual_v=Fraction(2),
        dual_u=(Fraction(0), Fraction(0), Fraction(7), Fraction(0)),
        rhs=(Fraction(1), Fraction(1), Fraction(-1), Fraction(0)),
        dual_feasibility=(Fraction(0), Fraction(0)),
        dual_value=Fraction(5),
        elimination_route="""\
q^-(c0) = q^+(c0) = 1 forces q(c0) = 1, and sum q = 1 then forces q(c1) = 0,
which is inside c1's own range [0, 1]. So the feasible set is the single point
(1, 0) -- NOT because the box is degenerate, but because the SIMPLEX closes it --
and the minimum is an evaluation, 5(1) + (-2)(0) = 5.""",
        arithmetic="""\
A NON-DEGENERATE BOX WHOSE DENOTATION IS STILL ONE POINT, and the case that
separates the two acceptance supports. This is the box ACC-support-superset
emits, against g = (5, -2).
  q^- = (1, 0) , q^+ = (1, 1) , NON-EMPTY since 1 <= 1 <= 2 .
c1'S WIDTH IS 1, NOT 0 -- so unlike PMIN-degenerate-point this box is not
degenerate as data -- and yet the floors already exhaust the normalization, so
every feasible q equals q^-.
ROUTE 1. g ascending: c_1 = c1 (g = -2), c_2 = c0 (g = 5).
  r = 1 - sum q^- = 0 ,   D(c1) = 1 , D(c0) = 0 .
The prefix at c1 is 1 >= 0, so j^* = c1 and w = 0. Eq. eq:greedy gives
  q^opt(c1) = q^-(c1) + 0 = 0 ,  q^opt(c0) = q^-(c0) = 1 ,
value 5(1) + (-2)(0) = 5.
THE POINT OF THE CASE. By the Outputs-table formula the acceptance support is
  Chat_acc = { chat : q^+(chat) > 0 } = {c0, c1} ,
which STRICTLY CONTAINS the union of the supports of the feasible points, {c0}.
Theorem thm:box-oracle (i) asks of an acceptance support ONLY that supp q be inside it
for every q in AcceptSet, and records minimality for the `singleton` tag alone.
SO A Chat_acc CARRYING c1 IS CONFORMING, NOT A DEFECT, and the two choices give
the SAME minimum because q(c1) = 0 identically on the set: summing over {c0}
gives 5(1) = 5 and summing over {c0, c1} gives 5(1) + (-2)(0) = 5.
AN IMPLEMENTATION THAT REJECTS THE LARGER SUPPORT, or that computes a different
minimum from it, has read the definition as demanding minimality. It does not.
The consequence reaches into the consuming contract, whose certificate domain
condition and whose sums over Chat_acc are all stated for a support that need
not be minimal.
THE CHEAP OUTCOME AGAIN GETS NOTHING, and here the temptation is stronger than
in PMIN-degenerate-point because c1's cap is 1: a minimization over the BOX
ALONE would return (1, 1) -- mass 2, not a distribution -- with value
5 - 2 = 3 < 5, an unsound-looking number for a set it does not describe.
ROUTE 2 is in elimination_route and agrees at 5.
THE WITNESS. lambda = g(c1) = -2, v = 2,
  u^+ = max{-2 - g, 0} = (0, 0) ,  u^- = max{g + 2, 0} = (7, 0) ,
so u = (0, 0, 7, 0).
DUAL FEASIBILITY: c0 : 5 + (0 - 7) + 2 = 0 ; c1 : -2 + (0 - 0) + 2 = 0 .
DUAL VALUE, with b = (1, 1, -1, 0):
  <b, u> = (-1)(7) = -7 ,  -<b, u> - v = 7 - 2 = 5 .
THE c1 CAP MULTIPLIER IS ZERO even though c1's cap is a real constraint of the
data; the row that binds is c0's FLOOR. A witness search that assumes the caps
are what bind returns nothing here.""",
    ),
    BoxMinimumCase(
        case_id="PMIN-tie-in-g",
        source_case="ACC-normal-2letter",
        outcomes=("c0", "c1"),
        box_lower=(Fraction(1, 2), Fraction(0)),
        box_upper=(Fraction(1), Fraction(1, 2)),
        g=(Fraction(2), Fraction(2)),
        acceptance_support=("c0", "c1"),
        sorted_order=("c0", "c1"),
        residual_r=Fraction(1, 2),
        widths=(Fraction(1, 2), Fraction(1, 2)),
        j_star="c0",
        fill_increment=Fraction(1, 2),
        q_opt=(Fraction(1), Fraction(0)),
        minimizers=(
            (Fraction(1), Fraction(0)),
            (Fraction(1, 2), Fraction(1, 2)),
        ),
        minimum=Fraction(2),
        lam=Fraction(2),
        dual_v=Fraction(-2),
        dual_u=(Fraction(0), Fraction(0), Fraction(0), Fraction(0)),
        rhs=(Fraction(1), Fraction(1, 2), Fraction(-1, 2), Fraction(0)),
        dual_feasibility=(Fraction(0), Fraction(0)),
        dual_value=Fraction(2),
        elimination_route="""\
Put a = q(c0), so q(c1) = 1 - a and
  <g, q> = 2a + 2(1 - a) = 2 ,
CONSTANT in a. Every feasible point is a minimizer and the value is 2, with no
optimization performed at all.""",
        arithmetic="""\
A TIE IN g, on the box ACC-normal-2letter emits. Theorem thm:box-oracle (ii) says
"enumerate Chat so that g(c_1) <= ... <= g(c_m)", which does NOT determine the
enumeration when two values are equal -- so the theorem's construction depends
on a choice the theorem does not make, and this case pins that THE VALUE DOES
NOT.
  q^- = (1/2, 0) , q^+ = (1, 1/2) , g = (2, 2) , r = 1/2 ,
  D(c0) = D(c1) = 1/2 .
ORDER (c0, c1): the prefix at c0 is 1/2 >= 1/2, so j^* = c0, w = 1/2, and
  q^opt = (q^-(c0) + 1/2 , q^-(c1)) = (1, 0) ,  value 2(1) + 2(0) = 2 .
ORDER (c1, c0): the prefix at c1 is 1/2 >= 1/2, so j^* = c1, w = 1/2, and
  q^opt = (q^-(c0) , q^-(c1) + 1/2) = (1/2, 1/2) ,  value 2(1/2) + 2(1/2) = 2 .
DIFFERENT MINIMIZERS, THE SAME MINIMUM. Both points are frozen in `minimizers`;
`q_opt` records the answer for the `sorted_order` this case declares.
WHY IT MUST BE SO. On the simplex a constant g is a constant objective:
sum_chat q(chat) = 1 forces <g, q> = 2 for EVERY feasible q, so the argmin is
the whole set and no tie-break can move the value. More generally the identity
in the proof of Theorem thm:box-oracle (ii) has (g(c_i) - lambda) = 0 at every tied
index, so the summands there vanish whichever tied index is called j^*.
WHAT THIS FORBIDS. An implementation may break ties however it likes -- by
alphabet order, by index, by anything stable -- but it may NOT report a
different minimum for two orderings of the same data, and it may not treat a tie
as an error. The frozen pair (2, 2) across the two orders is what a comparison
would have to violate.
THE WITNESS IS THE ZERO VECTOR. lambda = 2 either way, v = -2, and
  u^+ = max{2 - 2, 0} = (0, 0) ,  u^- = max{2 - 2, 0} = (0, 0) .
DUAL FEASIBILITY: 2 + 0 + (-2) = 0 in both coordinates. DUAL VALUE:
<b, u> = 0, so -<b, u> - v = 0 + 2 = 2. A TIGHT WITNESS WITH u = 0, which is
legal -- the dual constraint is satisfied by v alone -- and is the shape a
witness search that insists on a strictly positive multiplier will miss.""",
    ),
)


O_SA_BOX_MINIMUM = SAOracleEntry(
    oracle_id="O-SA-BOX-MINIMUM",
    claims=("SA8",),
    kind="toy-instance",
    subject=(
        "Theorem thm:box-oracle (ii)-(iii): the exact closed-form minimum of <g, q> "
        "over a canonical box Acc emits, by two independent routes, with the "
        "tight dual witness (u, v) as a third check -- on all three fill "
        "regimes, a tie in g, and a box whose denotation is one point."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:box-oracle (ii)-(iii) and Remark rem:box-oracle-consumer.

WHAT IS PINNED, AND WHAT IT IS NOT. This entry freezes the VALUE of
  min over q in AcceptSet of <g, q>
for boxes THIS module emits, together with the minimizer, the greedy data
(r, D, j^*, w) and the dual witness. IT DOES NOT MAKE THAT MINIMUM AN OUTPUT OF
THIS MODULE. Remark rem:box-oracle-consumer is explicit: Eq. eq:bacc-shape is the
CONSUMING contract's INPUT OBLIGATION, and what SA8 supplies is that for the
representation this module emits the minimum is computable in closed form,
exactly -- "no dual search and no linear-programming solve is needed" -- and
that the witness is available "for independent re-verification in exactly the
shape that remark's instantiation (b) expects". Section 1 says the same: SA8
"supplies exact input data to that remark's instantiation (b) and does not
restate or amend it". So an implementation of this module MAY expose the oracle
and MAY omit it; if it exposes it, these are the values, and nothing here
licenses feeding a self-computed minimum to a consumer's certificate without
that consumer's own admissibility check.

HOW EVERY NUMBER WAS OBTAINED. BY HAND, TWICE, BY ROUTES SHARING NO STEP.
(1) The exchange argument of Eq. eq:greedy: sort by g ascending, fill from the
    floors upward starting at the cheapest, and verify optimality from the
    identity
      <g,q> - <g,q^opt> = sum_i (g(c_i) - lambda)(q(c_i) - q^opt(c_i)) ,
    every summand of which is non-negative.
(2) Elimination of one coordinate through sum q = 1, which turns the objective
    into an affine function of the rest and the problem into maximizing it over
    an explicit box.
Each case records both, in `arithmetic` and `elimination_route`. The witness is
then exhibited and its value compared: THAT AGREEMENT IS A THIRD CHECK AND NEVER
THE SOURCE OF A NUMBER.

THE THREE FILL REGIMES, all frozen, because they are where an off-by-one lives:
  w = D(c_{j^*})     PMIN-normal-fill-at-cap, PMIN-floors-carry-the-mass and
                     PMIN-tie-in-g -- the fill stops exactly at a cap ;
  0 < w < D(c_{j^*}) PMIN-fill-strictly-inside -- the split coordinate is
                     partially filled ;
  w = 0              PMIN-degenerate-point and PMIN-box-superset -- r = 0, and
                     j^* is the FIRST index because 0 >= 0. An implementation
                     that searches for a STRICT prefix inequality finds no index
                     at all in these two.

THE DUAL WITNESS IS TIGHT, WITH EQUALITY. Theorem thm:box-oracle (iii) sets
lambda = g(c_{j^*}), v = -lambda, u^+(chat) = max{lambda - g(chat), 0} and
u^-(chat) = max{g(chat) - lambda, 0}, and proves
  g + B^T u + v = 0 componentwise (Eq. eq:dualfeas) ,
  -<b, u> - v = min over AcceptSet of <g, q> (Eq. eq:dualvalue) .
The consuming remark requires only the INEQUALITY g + B^T u + v >= 0; that it
holds here with EQUALITY is exactly why the resulting bound is tight for a
canonical box rather than conservative. `dual_feasibility` is frozen as the zero
vector in every case so that a sign error is a failure rather than a near-miss.
ROW ORDER: u is written caps-first then floors, both in the DECLARATION's
enumeration, matching Eq. eq:boxrows -- which is why a floor multiplier enters
-<b, u> - v with the sign it does. Two cases have a multiplier on a row whose
right-hand side is 0 (PMIN-fill-strictly-inside, PMIN-box-superset) and one has
u = 0 entirely (PMIN-tie-in-g); all three are legal and all three break a
witness search that assumes small or strictly positive multipliers.

THE TIE. Theorem thm:box-oracle (ii) fixes an enumeration with g ascending but does not
determine it when g has repeated values. PMIN-tie-in-g runs both orderings and
freezes the two DIFFERENT minimizers and the ONE minimum. The tie-break is free;
the value is not.

THE TWO WAYS TO GET IT WRONG, both frozen as numbers rather than as directions.
Dropping the simplex constraint and minimizing over the box alone returns
9/8 < 11/8 on PMIN-floors-carry-the-mass -- CONSERVATIVE, hence invisible,
and the minimum of a set nobody declared. Evaluating at a feasible non-optimal
point returns 17/8 > 11/8 on the same case -- the UNSOUND direction.

RELATION TO THE meat-core REGISTRY. Group 8 of registry.py pins the primal
minimum from the CONSUMER's side under claim C19, on its own toys, and records
agreement with this module's closed form as a cross-check. Nothing here is taken
from it: the boxes here are the ones Acc actually EMITS on the frozen
constructions, which is a different set of data, and every derivation above
stands alone.

The six cases are in BOX_MINIMUM_CASES.
""",
    hypotheses=(
        "The box is NON-EMPTY, i.e. Eq. eq:boxfeas holds. Theorem thm:box-oracle (ii) "
        "takes r >= 0 and the existence of j^* from Theorem thm:geometry-validation (iii); "
        "outside that hypothesis the fill proves nothing "
        "(INVALID-box-floors-above-one).",
        "0 <= q^- <= q^+ componentwise, so every width D_i is non-negative and "
        "the prefix sums are monotone (ILLFORMED-box-inverted).",
        "g is an exact rational vector. Every quantity above is then exact "
        "(Assumption A-EXACT).",
    ),
)


O_SA_ACCEPTANCE_SUPPORT = SAOracleEntry(
    oracle_id="O-SA-ACCEPTANCE-SUPPORT",
    claims=("SA8",),
    kind="structural-identity",
    subject=(
        "Theorem thm:box-oracle (i) and the Outputs-table formula: Chat_acc is the "
        "CAP-POSITIVITY set {chat : q^+(chat) > 0} for the box form and "
        "supp q^* for a singleton -- an admissible acceptance support that "
        "NEED NOT BE MINIMAL for a box, and MUST NOT be tightened."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:box-oracle (i), the Outputs table row
`acceptance_support` (Section 2.2), and the Chat_acc notation row of Section 3.

THE FORMULA, EXACTLY AS THE OUTPUTS TABLE FIXES IT:
  Chat_acc = { chat : q^+(chat) > 0 }   FOR THE BOX FORM ,
  Chat_acc = supp q^*                   FOR `singleton` ,
"admissible in the sense of meat-core Definition def:perturbed (Claim
SA8 (i))". THIS IS AN INTERFACE OBLIGATION OF THIS MODULE -- the Outputs table
carries the row -- and is the ONE part of SA8 that is. Parts (ii) and (iii) are
proven facts about the emitted geometry and are O-SA-BOX-MINIMUM; the split is
recorded as a judgement call in interface.yaml
(claims.SA8.interface_binding_judgement).

THE PROOF, in one line, and it is an INCLUSION and not an identity. If
q in AcceptSet and q^+(chat) = 0 then 0 <= q(chat) <= q^+(chat) = 0, so chat is
not in supp q; contrapositively supp q is inside Chat_acc for every
q in AcceptSet. That is exactly what an acceptance support is required to be --
the Section 3 notation row defines it as "any set with supp q inside Chat_acc
for every q in AcceptSet" -- AND NO MORE. Nothing in the proof says the
cap-positivity set is the union of the supports.

THE TWO BRANCHES ARE NOT THE SAME KIND OF STATEMENT, and the difference is the
contract's. For `singleton`, Theorem thm:box-oracle (i) DOES claim minimality: "For a
singleton geometry the MINIMAL acceptance support is Chat_acc = supp q^*",
proved by observing that the union over a one-point set is that point's support.
For a box it claims only the inclusion. An implementation that reads "the
support" as "the minimal support" gets the singleton branch right and the box
branch wrong.

THE FROZEN EVIDENCE, in the `acceptance_support` and `minimal_support` fields of
CONSTRUCTION_CASES. Three regimes occur among the twelve:
  EQUAL, AND EQUAL TO Chat -- eight cases, the ordinary situation ;
  EQUAL, AND STRICTLY SMALLER THAN Chat -- ACC-degenerate-honest-mass, where
    q^+(c1) = 0 because p^hon(c1) = 0 (Theorem thm:sa3 (v)). THIS IS THE ONLY
    ROUTE by which the construction map produces a support smaller than the
    alphabet on a constrained outcome ;
  CHAT_ACC STRICTLY LARGER THAN THE MINIMAL SUPPORT -- ACC-support-superset,
    where q^+(c1) = 1 > 0 puts c1 in Chat_acc while the floors already exhaust
    the normalization, so every feasible q has q(c1) = 0 and the union of
    supports is {c0}.
THE THIRD IS CONFORMING. PMIN-box-superset freezes the consequence that matters:
the minimum over the set is the SAME whether the sum runs over {c0} or over
{c0, c1}, because q(c1) = 0 identically. So the larger support costs nothing and
is what the formula returns; substituting the minimal one computes a different
object than the Outputs table names.

WHY THE LOOSER SUPPORT IS NOT MERELY TOLERATED BUT REQUIRED. Chat_acc is
consumed by meat-core Definition def:perturbed, whose certificate domain
condition (supp q inside Chat_acc) and whose sums over Chat_acc are all stated
for a support that need not be minimal. Computing the minimal support means
solving |Chat| linear programs over AcceptSet -- the tight-bound computation of
Group SA-D's header -- which is work the contract never asks for, on an output
whose specification is a one-line test on q^+.

A SEPARATE FACT, NOT TO BE CONFUSED WITH THIS ONE. The raw box bounds may also
be loose against the denoted set's tight bounds, and four construction cases
freeze that. The two loosenesses are independent: ACC-raw-vs-tight-3letter has
loose CAPS and a MINIMAL support, while ACC-support-superset has both. A cap
that no feasible point can reach makes the support non-minimal; a cap that is
merely not simultaneously attainable with the others does not.
""",
    hypotheses=(
        "The emitted geometry is a canonical box, or the declared geometry is "
        "a singleton. The taxonomy admits no third tag.",
    ),
)


# ===========================================================================
#  Group SA-F -- singleton completeness (SA9)
# ===========================================================================
#
#  Theorem thm:singleton-completeness is about a geometry THE CONSTRUCTION MAP NEVER EMITS
#  (Remark rem:singleton-honest). The tag is in the taxonomy because a
#  consumer's currently implemented acceptance oracle reads exactly that
#  geometry and because the consuming contract certifies its acceptance-side
#  minimum; what SA9 supplies is the completeness figure a profile that
#  DECLARES one must record.
#
#  Eq. eq:singleton-acc, with the convention 0^0 = 1:
#      Pr[freq = q^*] = n! / prod_chat (n q^*(chat))!
#                       * prod_chat p^hon(chat)^{n q^*(chat)}
#  when every n q^*(chat) is a non-negative integer, and 0 otherwise.
#
#  THE DEGENERATE CASE IS NOT AN EDGE CASE. Theorem thm:singleton-completeness (ii): when the
#  accept probability is 0 the admissible-budget interval
#  [1 - Pr, 1) = [1, 1) is EMPTY, so NO ecomp in [0, 1) is admissible and the
#  profile must RECORD THAT FACT rather than a budget of 1, which is outside
#  the declared domain of ecomp. Remark rem:singleton-honest adds that this is
#  reached "at most round counts" for a fixed q^*, since n q^* has a
#  non-integer coordinate for all but a sparse set of n.


@dataclass(frozen=True)
class SingletonCase:
    """One declared singleton geometry and its exact completeness figure."""

    case_id: str
    outcomes: tuple[str, ...]
    honest: tuple[Fraction, ...]
    rounds: int
    q_star: tuple[Fraction, ...]
    #: Whether every n q^*(chat) is a non-negative integer.
    counts_are_integral: bool
    #: (n q^*(chat))_chat when integral, else None.
    counts: tuple[int, ...] | None
    #: Whether q^* is absolutely continuous w.r.t. p^hon, i.e. q^*(chat) > 0
    #: implies p^hon(chat) > 0.
    absolutely_continuous: bool
    #: The multinomial coefficient n! / prod (n q^*)! when counts are integral.
    multinomial_coefficient: int | None
    accept_probability: Fraction
    #: The least admissible ecomp of Eq. eq:singleton-budget, or None when NO
    #: admissible budget exists.
    least_admissible_budget: Fraction | None
    admissible_budget_interval: str
    arithmetic: str


SINGLETON_CASES: tuple[SingletonCase, ...] = (
    SingletonCase(
        case_id="SING-fair-coin",
        outcomes=("c0", "c1"),
        honest=(Fraction(1, 2), Fraction(1, 2)),
        rounds=4,
        q_star=(Fraction(1, 2), Fraction(1, 2)),
        counts_are_integral=True,
        counts=(2, 2),
        absolutely_continuous=True,
        multinomial_coefficient=6,
        accept_probability=Fraction(3, 8),
        least_admissible_budget=Fraction(5, 8),
        admissible_budget_interval="[5/8, 1)",
        arithmetic="""\
THE ORDINARY CASE, and the one that shows why the construction map does not emit
this tag.
  Chat = (c0, c1) , p^hon = (1/2, 1/2) , n = 4 , q^* = (1/2, 1/2) .
COUNTS: n q^* = (2, 2), both non-negative integers, so the FIRST branch of
Eq. eq:singleton-acc applies.
MULTINOMIAL COEFFICIENT: 4! / (2! 2!) = 24/4 = 6 -- the number of length-4
strings over {c0, c1} with exactly two of each, which is what the proof counts.
PROBABILITY WEIGHT: each such string has probability
(1/2)^2 (1/2)^2 = 1/16 under A-HON, so
  Pr[freq = q^*] = 6 * 1/16 = 6/16 = 3/8 .
LEAST ADMISSIBLE BUDGET, Eq. eq:singleton-budget:
  ecomp = 1 - 3/8 = 5/8 , which lies in [0, 1) as it must ,
and the admissible budgets are exactly [5/8, 1).
WHAT THIS SAYS ABOUT THE TAG. An honest run of FOUR rounds on a FAIR COIN aborts
five times in eight against this acceptance set. Remark rem:singleton-honest:
the singleton's completeness figure is 1 - Pr[freq = q^*], "which is close to 1
for any realistic alphabet and round count", and that is why Acc emits a box
instead. Compare ACC-normal-2letter, where n = 8 on the same kind of alphabet
gives epsilon_star = 1789/32768, about 0.055.""",
    ),
    SingletonCase(
        case_id="SING-three-outcomes",
        outcomes=("c0", "c1", "c2"),
        honest=(Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)),
        rounds=4,
        q_star=(Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)),
        counts_are_integral=True,
        counts=(2, 1, 1),
        absolutely_continuous=True,
        multinomial_coefficient=12,
        accept_probability=Fraction(3, 16),
        least_admissible_budget=Fraction(13, 16),
        admissible_budget_interval="[13/16, 1)",
        arithmetic="""\
THE SAME STATEMENT ON THREE OUTCOMES, with q^* SET EQUAL TO THE HONEST
DISTRIBUTION -- the most favourable choice available, which is the point.
  Chat = (c0, c1, c2) , p^hon = q^* = (1/2, 1/4, 1/4) , n = 4 .
COUNTS: n q^* = (2, 1, 1), all non-negative integers.
MULTINOMIAL COEFFICIENT: 4! / (2! 1! 1!) = 24/2 = 12.
PROBABILITY WEIGHT: (1/2)^2 (1/4)^1 (1/4)^1 = (1/4)(1/4)(1/4) = 1/64, so
  Pr[freq = q^*] = 12/64 = 3/16 .
LEAST ADMISSIBLE BUDGET: 1 - 3/16 = 13/16, admissible interval [13/16, 1).
THE TREND IS THE CONTENT. Going from two outcomes to three, at the same n and
with q^* still exactly the honest law, the accept probability falls from 3/8 to
3/16. The multinomial mass at its own mode decays as the alphabet grows and as n
grows, so a singleton acceptance set is not merely inconvenient at scale -- it is
asymptotically useless, and the figure a profile must record approaches 1.
NOTHING HERE MAKES THE TAG INADMISSIBLE. The obligation Remark
rem:singleton-honest places is to RECORD ecomp from Eq. eq:singleton-budget and
"in either case to claim no completeness it does not have".""",
    ),
    SingletonCase(
        case_id="SING-n2-agrees-with-sa5",
        outcomes=("c0", "c1"),
        honest=(Fraction(1, 2), Fraction(1, 2)),
        rounds=2,
        q_star=(Fraction(1, 2), Fraction(1, 2)),
        counts_are_integral=True,
        counts=(1, 1),
        absolutely_continuous=True,
        multinomial_coefficient=2,
        accept_probability=Fraction(1, 2),
        least_admissible_budget=Fraction(1, 2),
        admissible_budget_interval="[1/2, 1)",
        arithmetic="""\
THE CROSS-CHECK REMARK rem:singleton-honest ASKS FOR: a set that is BOTH the
output of the construction map AND a single point, so that Theorem thm:completeness-bound and
Theorem thm:singleton-completeness both apply and must agree.
  Chat = (c0, c1) , p^hon = (1/2, 1/2) , n = 2 , q^* = (1/2, 1/2) .
This q^* is exactly the denotation of ACC-n2-singleton, whose emitted box
q^- = (1/2, 0), q^+ = (1/2, 1) denotes {(1/2, 1/2)}.
BY SA9: counts n q^* = (1, 1), multinomial coefficient 2!/(1! 1!) = 2, weight
(1/2)^1 (1/2)^1 = 1/4, so
  Pr[freq = q^*] = 2 * 1/4 = 1/2 ,
and the least admissible budget is 1 - 1/2 = 1/2.
BY SA5, on the same set: epsilon_star = Pr[N_{c0} < 1] + Pr[N_{c0} > 1]
= 1/4 + 1/4 = 1/2.
THE TWO ROUTES AGREE EXACTLY, at 1/2. Remark rem:singleton-honest says they must
here -- "the two statements agree, because there the budget ecomp = 4/5 was
large enough to pay for it" -- and this is the arithmetic behind that sentence.
AGREEMENT IS NOT AUTOMATIC, which is why it is frozen. SA5's route is a UNION
BOUND over count tails and SA9's is an EXACT multinomial mass; they coincide
only because the two tail events {N_{c0} < 1} and {N_{c0} > 1} are DISJOINT and
together exhaust the complement of the accept event. On a construction whose
Chat_con has two or more outcomes the union bound is generally strict, and
ACC-normal-2letter freezes a factor-of-2 gap. So this case pins a coincidence
with a reason, not a general identity.""",
    ),
    SingletonCase(
        case_id="SING-point-mass-zero-budget",
        outcomes=("c0", "c1"),
        honest=(Fraction(1), Fraction(0)),
        rounds=5,
        q_star=(Fraction(1), Fraction(0)),
        counts_are_integral=True,
        counts=(5, 0),
        absolutely_continuous=True,
        multinomial_coefficient=1,
        accept_probability=Fraction(1),
        least_admissible_budget=Fraction(0),
        admissible_budget_interval="[0, 1)",
        arithmetic="""\
THE ZERO-BUDGET POINT-MASS CASE, Theorem thm:singleton-completeness (iii) -- the ONLY way the least
admissible budget is 0.
  Chat = (c0, c1) , p^hon = (1, 0) = delta_{c0} , n = 5 , q^* = delta_{c0} .
COUNTS: n q^* = (5, 0), non-negative integers.
MULTINOMIAL COEFFICIENT: 5! / (5! 0!) = 1 -- there is exactly one string with
those counts, namely (c0, c0, c0, c0, c0).
PROBABILITY WEIGHT, and THIS IS WHERE THE CONVENTION 0^0 = 1 IS LOAD-BEARING:
  p^hon(c0)^5 * p^hon(c1)^0 = 1^5 * 0^0 = 1 * 1 = 1 ,
so Pr[freq = q^*] = 1 and the least admissible budget is 1 - 1 = 0.
WITHOUT THE CONVENTION the second factor would be undefined and the formula
would fail on a case whose answer is obvious -- the honest run produces c0 in
every round, so its frequency vector is delta_{c0} with probability one.
Eq. eq:singleton-acc states the convention explicitly for this reason, and the
proof of (ii) uses it again to argue that the product vanishes IF AND ONLY IF
some outcome has n_chat >= 1 with p^hon(chat) = 0.
THE CHARACTERIZATION, Theorem thm:singleton-completeness (iii): the budget is 0 if and only if
p^hon is a point mass delta_{c0} AND q^* equals it. Both halves are needed --
SING-not-absolutely-continuous has a point-mass p^hon with a different q^* and
gets accept probability 0, the opposite extreme.
WHY A POSITIVE-MASS ALPHABET CANNOT REACH 0. If p^hon gives positive mass to two
distinct outcomes chat != chat', then the strings (chat, chat, ..., chat) and
(chat', chat, ..., chat) BOTH have positive probability and their frequency
vectors differ by 1/n in coordinate chat, so freq is not almost surely constant
and the accept probability is strictly below 1.""",
    ),
    SingletonCase(
        case_id="SING-one-letter",
        outcomes=("c0",),
        honest=(Fraction(1),),
        rounds=6,
        q_star=(Fraction(1),),
        counts_are_integral=True,
        counts=(6,),
        absolutely_continuous=True,
        multinomial_coefficient=1,
        accept_probability=Fraction(1),
        least_admissible_budget=Fraction(0),
        admissible_budget_interval="[0, 1)",
        arithmetic="""\
THE ONE-LETTER ALPHABET, the "in particular" clause of Theorem thm:singleton-completeness (iii).
  Chat = (c0) , n = 6 . The input domain forces p^hon = (1), the only vector
  with non-negative coordinates summing to 1 on one letter, and q^* must equal
  it to satisfy the singleton validation predicate of Definition def:taxonomy.
COUNTS: n q^* = (6). MULTINOMIAL COEFFICIENT: 6!/6! = 1. WEIGHT: 1^6 = 1.
  Pr[freq = q^*] = 1 , least admissible budget 0 .
CONSISTENT WITH THE BOX ROUTE. ACC-one-letter-constrained and
ACC-one-letter-unconstrained both emit a set whose denotation is the same single
point delta_{c0}, with epsilon_star = 0 -- and 0 is exactly the least admissible
budget here. THE TWO TAGS AGREE ON A ONE-LETTER ALPHABET, as they must, the
denotation being the whole simplex either way (Theorem thm:monotonicity-limits (vi)).
A one-letter acceptance alphabet imposes no constraint on the consumer and
carries no information; this is a degenerate case to be recognized, not a regime
to be used.""",
    ),
    SingletonCase(
        case_id="SING-nonintegral-counts",
        outcomes=("c0", "c1"),
        honest=(Fraction(1, 2), Fraction(1, 2)),
        rounds=3,
        q_star=(Fraction(1, 2), Fraction(1, 2)),
        counts_are_integral=False,
        counts=None,
        absolutely_continuous=True,
        multinomial_coefficient=None,
        accept_probability=Fraction(0),
        least_admissible_budget=None,
        admissible_budget_interval="EMPTY -- no ecomp in [0, 1) is admissible",
        arithmetic="""\
THE FIRST DEGENERATE CASE OF THEOREM thm:singleton-completeness (ii): n q^* HAS A NON-INTEGER
COORDINATE.
  Chat = (c0, c1) , p^hon = (1/2, 1/2) , n = 3 , q^* = (1/2, 1/2) .
COUNTS: n q^* = (3/2, 3/2), NEITHER a non-negative integer, so the SECOND branch
of Eq. eq:singleton-acc applies and
  Pr[freq = q^*] = 0 .
The reason is definitional and needs no probability: freq = q^* holds exactly
when N_chat = n q^*(chat) for every chat (Definition def:freq), and N_chat is an
INTEGER, so the event is IMPOSSIBLE -- not improbable.
NO ADMISSIBLE BUDGET EXISTS. A budget is admissible for a geometry when it
satisfies BOTH the completeness requirement
Pr[freq not in AcceptSet] <= ecomp -- here 1 <= ecomp -- AND the domain
constraint ecomp in [0, 1) of Section 2.1. The admissible set is therefore
  [ 1 - Pr[freq = q^*] , 1 ) = [1, 1) = EMPTY .
THE CONFORMING BEHAVIOUR, and it is the whole point of freezing this case: a
profile declaring this geometry must RECORD THAT NO ADMISSIBLE COMPLETENESS
BUDGET EXISTS. It must NOT record ecomp = 1, which is OUTSIDE the declared
domain of ecomp and would be a claim of completeness the set does not have.
Remark rem:singleton-honest calls that "the honest reading of a geometry the
honest run can never satisfy".
NOT EXOTIC. Remark rem:singleton-honest: this is reached whenever n q^* has a
non-integer coordinate, "which for a fixed q^* happens at most round counts".
Here q^* = (1/2, 1/2) is admissible at every EVEN n and at no odd one --
SING-fair-coin at n = 4 and SING-n2-agrees-with-sa5 at n = 2 are the same q^*
with a positive accept probability, so the failure is a property of the PAIR
(q^*, n) and not of q^* alone.""",
    ),
    SingletonCase(
        case_id="SING-not-absolutely-continuous",
        outcomes=("c0", "c1"),
        honest=(Fraction(1), Fraction(0)),
        rounds=4,
        q_star=(Fraction(1, 2), Fraction(1, 2)),
        counts_are_integral=True,
        counts=(2, 2),
        absolutely_continuous=False,
        multinomial_coefficient=6,
        accept_probability=Fraction(0),
        least_admissible_budget=None,
        admissible_budget_interval="EMPTY -- no ecomp in [0, 1) is admissible",
        arithmetic="""\
THE SECOND DEGENERATE CASE OF THEOREM thm:singleton-completeness (ii): q^* IS NOT ABSOLUTELY
CONTINUOUS WITH RESPECT TO p^hon. The counts are perfectly integral here, so
this failure is INDEPENDENT of the first one.
  Chat = (c0, c1) , p^hon = (1, 0) , n = 4 , q^* = (1/2, 1/2) .
COUNTS: n q^* = (2, 2), both non-negative integers, so the FIRST branch of
Eq. eq:singleton-acc applies and the multinomial coefficient
4!/(2! 2!) = 6 is a POSITIVE INTEGER.
THE PRODUCT VANISHES ANYWAY:
  prod_chat p^hon(chat)^{n q^*(chat)} = 1^2 * 0^2 = 1 * 0 = 0 ,
so Pr[freq = q^*] = 6 * 0 = 0. Note that the convention 0^0 = 1 does NOT rescue
this: the exponent on the zero factor is 2, not 0.
THE CHARACTERIZATION, from the proof of Theorem thm:singleton-completeness (ii): under 0^0 = 1
every factor with n_chat = 0 equals 1, so the product vanishes IF AND ONLY IF
some chat has n_chat >= 1 and p^hon(chat) = 0; and n_chat >= 1 is equivalent to
q^*(chat) > 0. That is precisely q^* NOT absolutely continuous w.r.t. p^hon,
written q^* not << p^hon. Here q^*(c1) = 1/2 > 0 while p^hon(c1) = 0.
THE READING: the declared acceptance set asks the honest run to produce an
outcome the honest channel NEVER produces. The admissible-budget interval is
again [1, 1) = EMPTY, and the same obligation applies -- record that no
admissible budget exists, never ecomp = 1.
CONTRAST WITH THE BOX ROUTE ON THE SAME p^hon. ACC-degenerate-honest-mass has
the same honest distribution and n = 4 and emits a set with epsilon_star = 0 --
PERFECT completeness. The construction map cannot produce an unsatisfiable set,
because Theorem thm:box-construction (iii) puts p^hon inside whatever it emits; only a
DECLARED geometry can be unsatisfiable, which is exactly the division of labour
Theorem thm:honest-containment (iii) draws.""",
    ),
)


O_SA_SINGLETON_COMPLETENESS = SAOracleEntry(
    oracle_id="O-SA-SINGLETON-COMPLETENESS",
    claims=("SA9",),
    kind="toy-instance",
    subject=(
        "Theorem thm:singleton-completeness: the exact multinomial accept probability of a "
        "declared singleton, the least admissible completeness budget, BOTH "
        "degenerate cases in which no admissible budget exists, and the "
        "zero-budget point mass."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:singleton-completeness and Remark rem:singleton-honest.

WHAT IS PINNED, per case: whether n q^* is integral and the counts when it is;
whether q^* << p^hon; the multinomial coefficient; the exact accept probability
of Eq. eq:singleton-acc; and either the least admissible budget of
Eq. eq:singleton-budget or the fact that the admissible interval is EMPTY.

HOW EVERY NUMBER WAS OBTAINED. By the string count the contract's proof uses:
freq = q^* holds exactly when N_chat = n q^*(chat) for every chat, which is
impossible unless every n q^*(chat) is a non-negative integer; under A-HON each
string with those counts has probability prod_chat p^hon(chat)^{n_chat}, and the
number of such strings is the multinomial coefficient n! / prod_chat n_chat!.
Every coefficient below is a small factorial quotient computed by hand and every
weight is a product of small powers of dyadic rationals.

THE THREE OUTCOMES OF THEOREM thm:singleton-completeness (ii), all frozen:
  POSITIVE ACCEPT PROBABILITY -- SING-fair-coin (3/8), SING-three-outcomes
    (3/16), SING-n2-agrees-with-sa5 (1/2), and the two unit cases. The least
    admissible budget is 1 - Pr and lies in [0, 1) as the claim requires ;
  ZERO BY NON-INTEGER COUNTS -- SING-nonintegral-counts. The event is
    IMPOSSIBLE, not improbable ;
  ZERO BY FAILED ABSOLUTE CONTINUITY -- SING-not-absolutely-continuous, whose
    counts ARE integral and whose multinomial coefficient IS positive, so the
    two failure routes are independent and both are frozen.
IN BOTH ZERO CASES THE ADMISSIBLE-BUDGET INTERVAL IS [1, 1) = EMPTY, and the
frozen `least_admissible_budget` is None rather than 1. That is the substance of
finding F-1-04 and of the 0.1.1 restructuring that
closed it: ecomp = 1 is OUTSIDE the declared domain [0, 1) of Section 2.1, so
"budget 1" is not a way to describe a geometry the honest run can never satisfy.
The conforming behaviour is to RECORD THAT NO ADMISSIBLE BUDGET EXISTS.

THE ZERO-BUDGET CASE, Theorem thm:singleton-completeness (iii), with its convention. The budget is
0 if and only if p^hon is a point mass and q^* equals it; SING-point-mass-zero-
budget is that case at n = 5 and SING-one-letter is its |Chat| = 1 instance. The
convention 0^0 = 1 of Eq. eq:singleton-acc is LOAD-BEARING there -- without it
the weight 1^5 * 0^0 is undefined on a case whose answer is obviously 1 -- and
it is NOT load-bearing in SING-not-absolutely-continuous, where the exponent on
the zero factor is 2.

THE CROSS-CHECK AGAINST SA5. SING-n2-agrees-with-sa5 is the SAME SET as
ACC-n2-singleton, reached by the two different routes the contract provides, and
both give 1/2. Remark rem:singleton-honest requires that agreement. It is frozen
because it is not automatic: SA5 is a union bound over count tails and SA9 an
exact multinomial mass, and they coincide only because the two tail events are
disjoint and exhaust the complement of the accept event.

WHY THE TAG EXISTS AT ALL, given that Acc never emits it (Remark
rem:singleton-honest): a consumer's currently implemented acceptance oracle
reads exactly that geometry, and the consuming contract certifies its
acceptance-side minimum. What SA9 adds is the price -- a completeness figure
"close to 1 for any realistic alphabet and round count", visible here as
3/8 at n = 4 on two outcomes falling to 3/16 on three.

The seven cases are in SINGLETON_CASES.
""",
    hypotheses=(
        "Assumption A-HON: the honest acceptance statistics are i.i.d. with law p^hon.",
        "q^* is in the simplex, i.e. the singleton validation predicate of "
        "Definition def:taxonomy holds. Otherwise the geometry is inadmissible "
        "before completeness is considered (INVALID-singleton-* cases).",
        "The convention 0^0 = 1, stated in Eq. eq:singleton-acc.",
    ),
)


# ===========================================================================
#  Group SA-G -- honest containment and the infeasibility report (SA6)
# ===========================================================================
#
#  Theorem thm:honest-containment has three parts and they divide the work sharply:
#    (i)   p^hon is in AcceptSet, unconditionally on the input domain ;
#    (ii)  under A-REACH the infeasibility condition of the consuming Remark
#          rem:hlow-range is FALSE for the constructed set ;
#    (iii) SURFACING, NOT PASSING THROUGH -- the validation predicate holds
#          UNCONDITIONALLY on the output of Acc, so every infeasibility report
#          this module emits originates in an INPUT-DOMAIN VIOLATION and never
#          in the construction. The nine codes are the negation, clause by
#          clause, of the domain table of Section 2.1.


@dataclass(frozen=True)
class InputDomainViolationCase:
    """One inadmissible input, and the report code Theorem thm:honest-containment (iii) fixes."""

    case_id: str
    #: One of REASON_CODES, verbatim.
    reason_code: str
    #: The clause of the Section 2.1 domain table this input negates.
    violated_clause: str
    #: The offending input, described exactly. None where no finite datum can
    #: exhibit the violation.
    offending_input: str
    #: Always False: on any of the nine codes the module emits NO
    #: acceptance_set (Section 2.2, `infeasibility_report`).
    emits_acceptance_set: bool
    arithmetic: str


INPUT_DOMAIN_VIOLATION_CASES: tuple[InputDomainViolationCase, ...] = (
    InputDomainViolationCase(
        case_id="VIOL-alphabet-empty",
        reason_code="alphabet_empty",
        violated_clause="1 <= |Chat| < infinity (acceptance_alphabet)",
        offending_input="Chat = () , the empty alphabet",
        emits_acceptance_set=False,
        arithmetic="""\
|Chat| = 0 negates the LEFT half of the alphabet clause. The failure is not
merely bookkeeping: Delta(Chat) on an empty alphabet is the set of vectors with
no coordinates summing to 1, which is EMPTY, so no p^hon exists, no frequency
vector exists, and Eq. eq:accset denotes the empty set -- which is closed and
convex and would therefore pass the consuming Assumption A-ACC while carrying no
information at all. Refusing at the input is what keeps that set from being
constructed in the first place.""",
    ),
    InputDomainViolationCase(
        case_id="VIOL-alphabet-not-finite",
        reason_code="alphabet_not_finite",
        violated_clause="1 <= |Chat| < infinity (acceptance_alphabet)",
        offending_input=(
            "an alphabet presented without a finite enumeration -- no finite "
            "datum exhibits this, so no numeric case is frozen"
        ),
        emits_acceptance_set=False,
        arithmetic="""\
|Chat| not finite negates the RIGHT half of the same clause. NO CONCRETE INPUT
IS FROZEN FOR THIS CODE, deliberately: a violating alphabet cannot be written
down as finite data, so any "case" would be a mock rather than an instance. The
code is in the vocabulary because the contract enumerates it, and it is
reachable in practice through a lazily-presented or unbounded alphabet.
WHAT DEPENDS ON FINITENESS, so that the code is not read as pedantry: Theorem
thm:geometry-validation (i) uses Heine-Borel on R^Chat and needs the dimension finite for
compactness; Theorem thm:completeness-bound's aggregation is FINITE subadditivity over
2|Chat_con| events; Eq. eq:boxrows sets m_row = 2m with m = |Chat|; and the
assumption ledger's closing paragraph records that NO bound on |Chat| beyond
finiteness is assumed anywhere. Finiteness is the one cardinality hypothesis the
contract actually uses.""",
    ),
    InputDomainViolationCase(
        case_id="VIOL-rounds-zero",
        reason_code="rounds_out_of_range",
        violated_clause="n >= 1 (rounds)",
        offending_input="n = 0",
        emits_acceptance_set=False,
        arithmetic="""\
n = 0 negates the rounds clause. Every construction step divides by n:
Eq. eq:boxbounds sets q^{+-}(chat) = k^{+-}(chat)/n, and Definition def:freq
divides the counts by n. The proof of Theorem thm:completeness-bound's event-inclusion step
says "using n > 0" in as many words, because the equivalence
freq(chat) < q^-(chat) <=> N_chat < k^-(chat) is multiplication by n.
AN IMPLEMENTATION THAT DEFAULTS n TO 0 AND PROCEEDS produces a division by zero
or, worse, a silently-empty box; refusing at the input is the only conforming
behaviour. Note that n = 1 IS admissible and is not an edge to be excluded --
Theorem thm:binomial-tails is stated for n >= 1 and the tails are trivial there.""",
    ),
    InputDomainViolationCase(
        case_id="VIOL-honest-not-normalized",
        reason_code="honest_not_a_distribution",
        violated_clause=("p^hon in Delta(Chat) intersect Q^Chat (honest_distribution)"),
        offending_input="Chat = (c0, c1) , p^hon = (1/2, 1/4) , summing to 3/4",
        emits_acceptance_set=False,
        arithmetic="""\
p^hon = (1/2, 1/4) is non-negative but sums to 3/4, not 1, so it is not in
Delta(Chat).
WHY THIS IS NOT HARMLESS. Theorem thm:completeness-bound's marginal-law step needs
p^hon(chat) to be the SUCCESS PROBABILITY of a Bernoulli indicator, and its
event-inclusion step needs sum_chat N_chat = n, i.e. that each round contributes
exactly one outcome (Lemma lem:freq-in-simplex). A sub-normalized p^hon breaks
the second: the per-outcome counts would not partition the rounds, and the
completeness figure would concern a different experiment. The construction would
still RUN -- every per-outcome interval is well defined for any p in [0, 1] --
and would emit a box with a plausible epsilon_star. THAT IS WHY THE CHECK IS AT
THE INPUT and not inferred from the output.
THE CLAUSE ALSO COVERS a coordinate outside Chat, which the contract names
explicitly in the same code: a p^hon carrying mass on an outcome the alphabet
does not contain is not a distribution ON Chat.""",
    ),
    InputDomainViolationCase(
        case_id="VIOL-budget-equal-one",
        reason_code="budget_out_of_range",
        violated_clause="ecomp in [0, 1) (completeness_budget)",
        offending_input="ecomp = 1",
        emits_acceptance_set=False,
        arithmetic="""\
ecomp = 1 negates the RIGHT half of the budget clause, which is HALF-OPEN. The
exclusion is load-bearing twice over.
FIRST, Definition def:interval records as part of the input domain that
0 <= eps^{+-}(chat) <= ecomp < 1, and the proof of Theorem thm:sa3 (vi) USES
eps^{+-} < 1 TWICE -- at both end-of-range cases, where Pr[N <= K] = 1 or
Pr[N >= K] = 1 must STRICTLY exceed the budget for the guard's cost to be
bounded by one count. At ecomp = 1 those two arguments fail.
SECOND, Theorem thm:singleton-completeness (ii) turns on the same half-openness: when the accept
probability is 0 the admissible interval is [1, 1) = EMPTY, and the contract
insists a profile record that rather than "a budget of 1, which is outside the
declared domain of ecomp".
ecomp = 0 IS ADMISSIBLE and is not a violation -- it is the limit Theorem
thm:monotonicity-limits (iii) computes, frozen in ACC-ecomp-zero.""",
    ),
    InputDomainViolationCase(
        case_id="VIOL-allocation-negative",
        reason_code="allocation_negative",
        violated_clause=(
            "eps^{+-}(chat) >= 0 for every chat in Chat_con (budget_allocation)"
        ),
        offending_input=(
            "Chat_con = (c0, c1) , eps^-(c0) = -1/10 , the rest 1/10 , so the "
            "SUM is 3/10 <= ecomp = 1/2 and the sum test alone PASSES"
        ),
        emits_acceptance_set=False,
        arithmetic="""\
A NEGATIVE ALLOCATION ENTRY, chosen so that the SUM constraint is satisfied --
-1/10 + 1/10 + 1/10 + 1/10 = 2/10 = 1/5 <= 1/2 -- SO THAT AN IMPLEMENTATION
CHECKING ONLY THE SUM ACCEPTS IT. That is the whole point of the case: the
clause has two independent halves, componentwise non-negativity and the sum
bound, and VIOL-allocation-exceeds-budget exercises the other one.
WHAT A NEGATIVE BUDGET DOES DOWNSTREAM. eq:kappaminus asks for the largest k
with Pr[N < k] <= eps^-(chat); at eps^- = -1/10 no k qualifies at all, since
Pr[N < 0] = 0 > -1/10, AND THE SET IS EMPTY -- which destroys the non-emptiness
argument of Theorem thm:sa3 (i), whose entire content is that k = 0 always
belongs. The maximum of an empty set is undefined, so the construction has no
answer to give, and an implementation that returns 0 by convention has invented
a value the contract does not define.""",
    ),
    InputDomainViolationCase(
        case_id="VIOL-allocation-exceeds-budget",
        reason_code="allocation_exceeds_budget",
        violated_clause=(
            "sum over Chat_con of (eps^-(chat) + eps^+(chat)) <= ecomp "
            "(budget_allocation)"
        ),
        offending_input=(
            "ecomp = 1/10 , Chat_con = (c0,) , eps^-(c0) = eps^+(c0) = 1/10 , "
            "summing to 1/5 > 1/10 -- every entry non-negative"
        ),
        emits_acceptance_set=False,
        arithmetic="""\
THE MIRROR OF THE PREVIOUS CASE: every entry is non-negative and the SUM
1/10 + 1/10 = 1/5 exceeds ecomp = 1/10, so a componentwise check alone accepts
it.
WHAT BREAKS. Theorem thm:completeness-bound's final step -- the "Budget" paragraph -- reads:
each term of epsilon_star is at most the corresponding eps^{-+}(chat) by Theorem
thm:sa3 (ii), and THE ALLOCATION CONSTRAINT OF SECTION 2.1 SUMS THESE TO AT MOST
ecomp. Without that constraint the chain
  Pr[freq not in AcceptSet] <= epsilon_star <= ecomp
LOSES ITS SECOND INEQUALITY, and the module would report a
completeness_certified value outside its own declared output domain [0, ecomp].
THE FAILURE IS SILENT WITHOUT THE CHECK. The construction still runs, the
emitted box is still a valid canonical box containing p^hon, and epsilon_star is
still correctly computed -- it is only the CLAIM epsilon_star <= ecomp that is
false. Nothing downstream can detect it, because ecomp is this module's input
and the consumer never sees the allocation.""",
    ),
    InputDomainViolationCase(
        case_id="VIOL-selector-not-a-subset",
        reason_code="selector_not_a_subset",
        violated_clause="Chat_con subset-or-equal Chat (constrained_outcomes)",
        offending_input="Chat = (c0, c1) , Chat_con = (c0, c3)",
        emits_acceptance_set=False,
        arithmetic="""\
Chat_con contains c3, which is not in Chat.
WHAT BREAKS. Eq. eq:boxbounds is a case split on chat in Chat_con versus not,
over chat IN Chat; an element of Chat_con outside Chat has no box row to occupy
and no coordinate to bound. Eq. eq:completeness sums over Chat_con and would
need a count N_{c3} that Definition def:freq does not define. And Eq. eq:boxrows
sets m_row = 2|Chat|, INDEPENDENT of Chat_con -- Remark rem:selector is explicit
that the row count does not depend on the selector -- so there is no row for c3
even in principle.
Chat_con = () AND Chat_con = Chat ARE BOTH ADMISSIBLE and neither is a
violation: the empty selector is the second branch of Theorem thm:monotonicity-limits (vi),
frozen in ACC-one-letter-unconstrained, and Chat is the declared default.""",
    ),
    InputDomainViolationCase(
        case_id="VIOL-inputs-not-rational",
        reason_code="inputs_not_rational",
        violated_clause=(
            "p^hon in Q^Chat, ecomp rational, eps^{+-} rational (Assumption A-EXACT)"
        ),
        offending_input=(
            "p^hon(c0) = 1/sqrt(2) -- or any binary floating-point value "
            "presented as if exact"
        ),
        emits_acceptance_set=False,
        arithmetic="""\
THE CODE THAT GUARDS ASSUMPTION A-EXACT, whose statement is that p^hon, ecomp
and the allocation ARE exact rationals and that every tail comparison of
Definition def:interval is decided either exactly or against an UPWARD-rounded
bound.
WHY AN IRRATIONAL INPUT IS A DOMAIN VIOLATION AND NOT A PRECISION QUESTION. At
irrational p the tail Pr[N < k] is irrational, so the comparison against a
rational budget is not decidable by exact arithmetic and the endpoints
kappa^{+-} are not determined by the data the module was given. Lemma
lem:exact-strict-tails says the tails are rational numbers, decided exactly, AT
RATIONAL p, and that is the hypothesis being negated.
THE PRACTICAL FORM OF THIS VIOLATION IS A FLOAT. A binary64 value IS an exact
rational -- a dyadic one -- so it does not violate the letter of the clause; what
violates it is presenting a float as if it were the intended value, e.g. reading
"0.1" as 1/10. The safe direction, if a tail cannot be evaluated exactly, is not
to refuse but to ROUND THE TAIL UPWARD (Theorem thm:sa3 (iii) and A-EXACT),
which enlarges AcceptSet and costs rate rather than soundness. THE REPORT CODE
IS FOR THE INPUTS, THE ROUNDING RULE IS FOR THE EVALUATION, and conflating them
either refuses admissible work or admits inadmissible data.""",
    ),
)


O_SA_INFEASIBILITY_REPORT = SAOracleEntry(
    oracle_id="O-SA-INFEASIBILITY-REPORT",
    claims=("SA6",),
    kind="fail-closed",
    subject=(
        "Theorem thm:honest-containment (iii): the NINE machine-readable input-domain "
        "violation codes, one violating input per code, the verdict that NO "
        "acceptance_set is emitted on any of them, and the ONE clause of the "
        "input domain that carries no code at all."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:honest-containment (iii) and the Outputs table row
`infeasibility_report` (Section 2.2).

THE VOCABULARY IS FIXED BY THE CONTRACT AND IS NOT INVENTED HERE. REASON_CODES
above is the nine codes VERBATIM and in the theorem's order. This is unlike the
consuming contract, which requires "a machine-readable reason naming the failed
or unrequested check" and fixes no vocabulary -- registry.py's
O-POLYTOPE-EMPTY-FAIL-CLOSED says in as many words that it invents none. HERE
THE CODES ARE THE CONTRACT'S OWN, so freezing them is transcription and a
disagreement is an R12 finding rather than a matter of taste.

THE STRUCTURAL CLAIM, and it is the reason this group is separate from the
construction group. Theorem thm:honest-containment (iii), first sentence: the validation
predicate of Theorem thm:geometry-validation (iii) is decidable in closed form AND, on the input
domain of Section 2.1, is satisfied by the output of Acc UNCONDITIONALLY. Hence
  EVERY infeasibility_report this module emits originates in a violation of that
  input domain, and NEVER in the construction.
An implementation that can reach this output from a validated input has a
defect, not a geometry problem. The three INVALID/ILLFORMED cases of Group SA-B
are DECLARED geometries, unreachable from any admissible input -- Theorem
thm:box-construction (ii) gives 0 <= q^- <= q^+ <= 1 and (iii) gives p^hon in AcceptSet,
whence sum q^- <= 1 <= sum q^+ automatically.

THE VERDICT ON EVERY CODE: NO acceptance_set IS EMITTED. Section 2.2 states it
for the row -- "names one of the input-domain violations enumerated in Theorem
thm:honest-containment (iii) and NO acceptance_set is emitted" -- and Theorem thm:honest-containment (iii)
repeats it. `emits_acceptance_set` is False in all nine cases, and there is no
partial-output branch: a report and a set are mutually exclusive, so an
implementation may not emit a "best-effort" box beside a warning.

WHY EACH CASE IS THE ONE IT IS. Two pairs are chosen so that a HALF-CHECK
passes: VIOL-allocation-negative has a negative entry whose SUM is inside the
budget, and VIOL-allocation-exceeds-budget has all entries non-negative with a
SUM outside it -- the clause has two independent halves and each case defeats a
check of the other half only. VIOL-budget-equal-one exercises the half-open
right end, whose strictness the proof of Theorem thm:sa3 (vi) uses twice and
Theorem thm:singleton-completeness (ii) once. VIOL-alphabet-not-finite carries NO concrete input,
deliberately, because no finite datum exhibits it; the code is frozen without an
instance and the entry says so rather than inventing a mock.

THE ONE CLAUSE WITH NO CODE, transcribed because the nine must not be read as
covering it. Theorem thm:honest-containment (iii), closing sentences: exactly one clause of the
input domain is NOT decidable from this module's inputs -- the A-ALPHABET clause
that Chat, its enumeration and n are those of the SAME declaration the consumer
solves. That is A RELATION BETWEEN ARTIFACTS, not a property of an input, and it
is routed to bundle validation as a HARD ERROR
(ARCHITECTURE_SPEC.md Section 5.6). An implementation that adds a tenth code for
it has invented vocabulary; one that silently accepts a mismatched alphabet
emits a set on the wrong coordinate space.

WHAT IS NOT IN SCOPE HERE. Whether the consuming h_low is finite is a statement
about that contract's objective and belongs to it; Remark rem:hlow-consequence
quotes it and uses it in no proof. Theorem thm:honest-containment (ii) rules out the
infeasibility CONDITION of that remark under A-REACH -- which this contract
never verifies -- and O-SA-HONEST-CONTAINMENT freezes that side.

The nine cases are in INPUT_DOMAIN_VIOLATION_CASES, one per code.
""",
    value="no acceptance_set is emitted",
    hypotheses=(
        "The nine codes are decidable from this module's own inputs alone. The "
        "A-ALPHABET cross-artifact clause is not, and carries no code.",
    ),
)


O_SA_HONEST_CONTAINMENT = SAOracleEntry(
    oracle_id="O-SA-HONEST-CONTAINMENT",
    claims=("SA6", "SA4"),
    kind="structural-identity",
    subject=(
        "Theorem thm:honest-containment (i)-(ii): p^hon lies in every set Acc emits, "
        "unconditionally; and under A-REACH the pair (p^hon, omega^hon) "
        "witnesses that the consuming Remark rem:hlow-range's infeasibility "
        "condition is FALSE for the constructed set."
    ),
    derivation="""\
contract.tex 0.1.2 Theorem thm:honest-containment (i)-(ii), Theorem thm:box-construction (iii) and Remark
rem:hlow-consequence.

(i) HONEST CONTAINMENT, UNCONDITIONALLY. p^hon is in AcceptSet for EVERY
admissible ecomp in [0, 1), EVERY Chat_con and EVERY admissible allocation. The
proof is two lines and both are visible in the frozen data. On Chat_con,
Eq. eq:ordering gives
  q^-(chat) = k^-(chat)/n <= floor(n p)/n <= p   and
  q^+(chat) = k^+(chat)/n >= ceil(n p)/n  >= p ,
so the honest coordinate is inside its box bounds; off Chat_con the bounds are
[0, 1], which p^hon satisfies because it is in the simplex. THE GUARD IS WHAT
MAKES THIS UNCONDITIONAL -- without Eq. eq:guard the chain would run through
kappa^{+-} instead, and ACC-guard-lower-two-counts is a frozen input where the
RAW quantile interval [7/10, 4/5] EXCLUDES the honest value 1/2. Remark
rem:guard says exactly that: without the guard SA4 (iii) and SA6 "would carry a
side condition on how large ecomp may be".
FROZEN AS `honest_contained` ON ALL TWELVE CONSTRUCTION CASES, and true in every
one, including the two limits (ecomp = 0, where AcceptSet is the whole simplex)
and both degenerate masses (where AcceptSet is a single point that IS p^hon).

THE CONSEQUENCES THAT FOLLOW FROM (i) AND ARE FROZEN WITH IT. AcceptSet is
NON-EMPTY -- p^hon is in it -- so by Theorem thm:geometry-validation (iii) the closed-form
predicate holds, sum q^- <= 1 <= sum q^+, and `box_sums` brackets 1 in all
twelve. Note the direction of that argument in the contract's proof of
Theorem thm:box-construction (iii): non-emptiness is established FIRST, from containment, and
Eq. eq:boxfeas is then its NECESSARY consequence -- the right-to-left direction
of Theorem thm:geometry-validation (iii) is not needed and is not used.

(ii) THE INFEASIBILITY CONDITION IS FALSE, UNDER A-REACH. Assume A-REACH: there
is omega^hon in W, the feasible set of the consuming declaration, with
Phi[omega^hon] = p^hon. Then the pair (q, omega) = (p^hon, omega^hon) satisfies
all three of
  p^hon in AcceptSet          (by (i)) ,
  omega^hon in W              (by A-REACH) ,
  p^hon << Phi[omega^hon]     (trivially: the two vectors are EQUAL, so
                               p^hon(chat) > 0 implies Phi[omega^hon](chat) > 0
                               with nothing to check) ,
which is a WITNESS to the negation of the universally quantified condition
Eq. eq:infeasible -- "no q in AcceptSet is absolutely continuous with respect to
Phi[omega] for any omega in W". One witness refutes a universal statement, so
the condition is false and nothing more is claimed.

TWO LIMITS OF (ii), BOTH DELIBERATE AND BOTH RECORDED HERE SO THAT THE ENTRY IS
NOT OVER-READ (Remark rem:hlow-consequence).
FIRST, IT IS CONDITIONAL ON A-REACH, WHICH THIS CONTRACT NEVER VERIFIES. Whether
the declared honest distribution is producible by the declared protocol is a
joint property of the provider and the declaration; asserting it here would be
asserting something this module cannot see. The assumption ledger's "If
violated" cell is correspondingly narrow: ONLY SA6 (ii) lapses, the consumer may
return h_low = +infinity and must emit no key-length claim, and that is a rate
and usability failure, fail-closed by design, NEVER a security break. NO CASE IS
FROZEN FOR A VIOLATION OF A-REACH, because a violating input is not
distinguishable from an admissible one by anything this module can compute --
which is the assumption's whole content.
SECOND, IT EXCLUDES THE CONDITION AND SAYS NOTHING MORE. Whether h_low is then
FINITE is a statement about the consuming contract's objective and belongs to
that contract; the contract quotes it and uses it in no proof of its own. The
fail-closed behaviour on h_low = +infinity is unchanged and remains mandatory
there.

WHAT "SURFACING RATHER THAN PASSING THROUGH" MEANS, given (i)-(iii) together. A
specification error is caught HERE, at the point where the honest model and the
declaration are both available, instead of reappearing downstream as an
extended-real value with no diagnosis. The division of labour is exact: a set
built by Acc from a reachable honest distribution cannot trigger the condition
(ii); a set that could is either a DECLARED geometry (Group SA-B) or the product
of an inadmissible input (Group SA-G).
""",
    hypotheses=(
        "For (i): the input domain of Section 2.1, and nothing else. No bound "
        "on ecomp, no condition on the allocation beyond admissibility.",
        "For (ii): Assumption A-REACH, which this contract never verifies.",
    ),
)


# ===========================================================================
#  The registry
# ===========================================================================

SA_ORACLES: tuple[SAOracleEntry, ...] = (
    # Group SA-A -- exact binomial tails.
    O_SA_BINOMIAL_TAILS,
    # Group SA-B -- the geometry taxonomy and its validation predicates.
    O_SA_GEOMETRY_VALIDATION,
    # Group SA-C -- the per-outcome interval and the guard.
    O_SA_INTERVAL_EXTREMALITY,
    O_SA_GUARD_COST,
    # Group SA-D -- the construction map, end to end.
    O_SA_CONSTRUCTION,
    O_SA_COMPLETENESS,
    O_SA_BUDGET_MONOTONE,
    O_SA_N_NONMONOTONE,
    O_SA_WIDTH_BOUND,
    # Group SA-E -- the acceptance support and the box oracle.
    O_SA_ACCEPTANCE_SUPPORT,
    O_SA_BOX_MINIMUM,
    # Group SA-F -- singleton completeness.
    O_SA_SINGLETON_COMPLETENESS,
    # Group SA-G -- honest containment and the infeasibility report.
    O_SA_HONEST_CONTAINMENT,
    O_SA_INFEASIBILITY_REPORT,
)
