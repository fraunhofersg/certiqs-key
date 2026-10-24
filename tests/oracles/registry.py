"""The ``meat-core`` oracle registry -- golden values derived from mathematics.

This file is the registry; ``toy_declarations.py`` holds the
hand-authored instances it refers to, ``reference.py`` the naive evaluator that
reproduces it, ``dummy_bundles.py`` the serialized operator bundles, and the
``test_*.py`` modules beside them the checks.

WHAT AN ENTRY IS
================
A frozen expected value together with the derivation that produced it. Every
entry names

* the ``meat-core`` claim IDs it pins (``claims``), which must appear in
  ``docs/mathematical-contracts/meat-core/interface.yaml`` -- C1-C17 from the
  0.3.0 freeze, C18-C20 plus the closed C13 from the 0.4.0 one, and C21 from
  the 0.5.0 one;
* the kind of derivation (``analytic-limit``, ``toy-instance``,
  ``structural-identity``, ``fail-closed``);
* the derivation itself, in enough detail to redo on paper.

ADMISSIBILITY (ADR-0003)
========================
No MATLAB, OpenQKDSecurity, CVX, MOSEK or Julia value is admissible as an
oracle, and none is used. Every number below is either an exact closed form, an
elementary evaluation of one, or a hand-computed integer. ``kamin2025renyi``,
``arqand2025meat``, ``tupkary2026decoy``, ``tomamichel2016finite``,
``winick2018reliable`` and ``navarro2025conic`` are the only citable sources
(references/index.json), and this registry cites a published comparison point
only where the contract itself does.

WHY THE VALUES COME BEFORE THE SOLVER
=====================================
This set is frozen before the solver code exists; the implementer is a
different instance which may read this registry and may not modify it. **An expected value that turns out to be wrong is a finding**,
reported and corrected deliberately with its derivation -- never edited in
passing to make a test go green.

The same discipline was applied again at the 0.3.0 G4: Group 6 below was
authored and committed by one implementer instance before any ``src/`` file
supporting the untrusted source mode, the party partition or the singular
trusted marginal existed, and the code was written by another against these
values.

And again at the 0.4.0 G4: **Group 7 -- the whole certificate chain -- was
authored and committed before any certificate source file existed.** Not one
number in Group 7 was produced by an implementation of the thing it pins.
Every enclosure constant, every dual bound and every ``h_cert`` below was
derived on paper from the displayed equations of ``contract.tex`` 0.4.0, and
each entry carries that derivation in full. Where a value happens to be an
evaluation of a closed form, the closed form is a HAND-DIAGONALIZED answer for
one named toy branch and not the general routine a solver runs.

C11 AND C12: WHAT IS AND IS NOT PINNED
=======================================
No entry here contains a Choi parametrization or a gradient evaluation. An
oracle for either would be the implementation written in the test tree, and
``test_registry_integrity.py`` asserts their absence. Exactly two entries name
those claims, and both pin scalar or structural witnesses only:

* ``O-CHOI-BASIS-INVARIANCE`` (C11) freezes a closed-form ``h_low`` and two
  HAND-AUTHORED Choi coordinate matrices whose relation is the content of
  Remark ``rem:basis-invariance``. It builds nothing from a declaration.
* ``O-GRADIENT-FACE-SPLIT`` (C6, C12) freezes two values of the trace-power
  functional ``T`` -- the same functional C6 bounds -- one correct and one
  produced by the compression rule Theorem ``thm:gradient`` (i) discards. It
  computes no gradient.

Both close implementation-found contract gaps (F-01-01, F-01-02) that the
0.3.0 contract resolves, which is exactly the kind of expected value that has
to exist before the code that must reproduce it.

WHAT THIS REGISTRY DOES NOT DO
==============================
**It does not certify anything, and that is unchanged by C13 closing.**

Through 0.3.0 the reason was that no certificate existed: C13 was ``open``. At
0.4.0 it is closed -- Theorem ``thm:cert`` proves ``h_cert <= h_low`` and the
label ``certified`` becomes REACHABLE for the first time in this module's
history. The reason every entry here still carries ``assurance = "estimate"``
is a different and more durable one:

    a result is labelled ``certified`` only when every RUNTIME check of
    contract Section 4.18 passes on the ACTUAL computation -- the exact
    membership ``x in D`` of Eq. ``eq:cert-domain``, the hypotheses (H1)-(H4)
    with their certified floors, the slack PSD verifications of Theorem
    ``thm:weak-duality``, and the enclosure assembly of Proposition
    ``prop:budget`` -- and any failure falls back to ``estimate`` with a
    machine-readable reason (ARCHITECTURE_SPEC.md Section 3.5; Remark
    ``rem:cert-interface``).

Agreement with an oracle in this file is not one of those checks and never was.
So ``ASSURANCE`` below is the tier of the ORACLE's own evidential status, and
it is ``estimate`` for every entry, including the Group 7 entries that pin the
certificate itself. Agreement here is evidence that an implementation computes
the contracted quantity; the label comes from the runtime checks or not at all.

Because the label is now reachable, the entries that say when it must NOT be
reachable are the load-bearing half of Group 7: ``O-CERT-DOMAIN-FAIL``,
``O-CERT-HYPOTHESES-FAIL``, ``O-DUAL-SLACK-NOT-PSD``,
``O-ACC-SIDE-UNSUPPORTED`` and ``O-ASSURANCE-CERTIFIED-GATE``. Two of them
freeze an explicitly UNSOUND number -- a dual bound that exceeds the true
minimum when the PSD check is skipped -- so that the check being load-bearing
is a fact the suite can fail on, not a claim in a comment.

GROUP 8 -- THE POLYTOPE ACCEPTANCE ORACLE
=========================================
Group 8 was authored under the SAME accepted contract 0.4.0: no new contract
version. Groups 1-7 are untouched by it: not one existing entry, value or
derivation was edited.

What it adds is the half of the acceptance side that Group 7 deliberately did
not pin. ``O-BETA-ACC`` pins the DUAL bound of Remark ``rem:acc-side`` (b) --
the number ``-<b, u> - v`` that an admissible ``(u, v)`` certifies. Group 8
pins the PRIMAL LP MINIMUM itself, ``min <g, q'>`` over a declared polytope on
2- and 3-outcome alphabets: the quantity on the right of Eq. ``eq:bacc-def``,
which is what a linear minimization oracle over the acceptance set must return
and what no ``beta_acc`` may exceed.

Same discipline, restated because a later band is exactly where it slips.
Every number was derived BY HAND, twice, by routes sharing no step -- the
exchange argument for the greedy optimum, and elimination of one coordinate
through ``sum q = 1`` followed by maximizing the resulting affine function
over the remaining box -- and each case records both. No value came from an
implementation, and none could have: no polytope acceptance oracle exists
under ``src/`` when this is written.

The geometry VOCABULARY these entries use -- the ``polytope`` tag, its
canonical box form with ``(q^-, q^+)`` recorded under ``box_bounds``, and the
integer-indexed row structure -- is fixed by the accepted
``statistics-acceptance`` contract 0.1.2 (Definition ``def:taxonomy``), which
``meat-core`` reads as DATA: contract.tex Section 2.1 types ``acceptance_set``
as a closed convex subset of the simplex and enumerates no geometries. Where
that module's Theorem ``thm:box-oracle`` gives a closed form for the box minimum, the
agreement is recorded below as a CROSS-CHECK and never as the derivation.

GROUP 9 -- THE DECLARED OPERATOR TOLERANCE (contract 0.5.0, C21)
================================================================
Group 9 was authored in the SCOPED IMPLEMENTATION BAND that the accepted
**amendment 0.5.0** opens (``bump_level`` minor), by the run-A implementer
instance under the two-instance freeze rule: run A freezes the evidence before any code changes,
and run B -- a different instance -- changes the code against it and may read
but never modify what is frozen here. **Not one number in Group 9 was produced
by an implementation of the thing it pins**, because no such implementation
existed when it was written.

What it adds is the whole of C21 as data: the three defects of
Eq. ``eq:defects`` on eleven hand-authored families with rational spectra
(``OPTOL_FAMILIES``); the admission rule case by case, with a boundary pair
for each of (H), (P), (C) and three cases showing (T) refused at every
tolerance (``OPTOL_ADMISSION_CASES``); the declared domain ``[0, 1)`` with the
family that derives its upper endpoint (``OPTOL_DOMAIN_CASES``); the three
branches of Theorem ``thm:optol`` with what each may and may not emit
(``OPTOL_BRANCH_OUTPUTS``); ``operator_tolerance_report`` field for field
(``OPTOL_REPORT_CASES``); Lemma ``lem:nearpovm`` both ways, with both halves
attained on ``WIT-HERM`` (``OPTOL_WITNESS_CASES``); Proposition
``prop:optol-nobound`` at two parameter values and in either direction
(``OPTOL_NOBOUND_CASES``); the six machine-readable reason strings the
contract spells (``OPTOL_REASON_VOCABULARY``); and what the tolerance does NOT
reach (``OPTOL_REACH_STATEMENTS``).

THE AMENDMENT MOVES NO EXISTING NUMBER, and the registry says why rather than
assuming it. Theorem ``thm:optol`` (i): on an exactly admissible declaration
"every claim C1-C20 of this contract applies to the declared numbers EXACTLY
AS AT VERSION 0.4.0. The declared eps_dec changes no statement, no bound and
no number." Every toy declaration here is exactly admissible, so every frozen
value of Groups 1-8 is a branch-(i) value. ``O-OPTOL-EXACT-UNCHANGED`` makes
that falsifiable: ``OPTOL-EXACT`` **is** TOY-1's POVM, element for element.

WHAT IS MARKED RATHER THAN EDITED. Three 0.4.0 objects are listed in
``SUPERSEDED_BY_0_5_0`` with the contract site and their replacements -- two
spec-version pins and one biconditional 0.5.0 falsifies -- and
``NOT_SUPERSEDED_BY_0_5_0`` records, in twelve rows, every object a reader
would expect to be marked and why it is not. Run A marks; run B retires or
rewrites. Nothing was deleted and nothing was silently edited: the single
in-place change to Groups 1-8 is one ``superseded_by`` field on
``O-ASSURANCE-CERTIFIED-GATE``.

CHANGE-REQUEST CANDIDATES CLEARED. ``CHANGE_REQUEST_CANDIDATES_0_5_0`` names
every reading this freeze had to take, with the contract site that settles it.
Five are closed by contract.tex 0.5.0 outright -- including the two the band
was asked about, whether a failure of (T) carries one of the new reason
strings (it does not) and whether the marginal and acceptance-sum checks are
inside the tolerance's reach (they are not, by Remark ``rem:optol-reach``
(c)) -- and five are places the contract DELIBERATELY leaves to an
implementation, recorded in ``interface.yaml`` as open choices OC-1 to OC-7
rather than decided here. **Nothing was worked around, and no reading was
improvised.**
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

# Alpha grid at which the alpha-dependent closed forms are frozen. Chosen inside
# the key-length domain (1, 2) of Assumption A-ALPHA, with 1.05 close to the
# alpha -> 1+ end and 1.9 close to the other.
ALPHA_GRID: tuple[float, ...] = (1.05, 1.25, 1.5, 1.75, 1.9)

#: One Renyi order OUTSIDE the key-length domain, admitted by Assumption
#: A-ALPHA for C3-C13 and C16-C20 (which hold on ``(1, inf)``) and used only
#: there. It exists because ``alpha = 2`` makes the exponent ``beta = alpha``
#: of Lemma ``lem:series`` a POSITIVE INTEGER, where the binomial series
#: terminates and both exact tails are zero -- the case the Round-10 verifier
#: recorded as uncovered by that lemma's ratio-test remark and the G3 signature
#: accepted as debt (judgement call (2)). No key-length case may use it:
#: Corollary ``cor:cert-keylength`` is confined to ``(1, 2)`` exactly as
#: Theorem ``thm:keylength`` is.
CERT_ALPHA_INTEGER_BETA: float = 2.0

#: The ORACLE's own evidential tier, and it is ``estimate`` for every entry --
#: including the Group 7 entries that pin the certificate chain. See the module
#: docstring, "WHAT THIS REGISTRY DOES NOT DO": agreement with an oracle is
#: never one of the runtime checks that produce a ``certified`` label.
ASSURANCE = "estimate"

#: The two values contract.tex 0.4.0 Section 2.2 admits for
#: ``optimizer_certificate.assurance``. Mirrored here so that the fail-closed
#: entries of Group 7 can name the value that must be emitted, without any
#: entry claiming that value for itself.
ASSURANCE_VALUES: tuple[str, ...] = ("estimate", "certified")

KINDS = frozenset(
    {"analytic-limit", "toy-instance", "structural-identity", "fail-closed"}
)

#: ADR-0003. A registry entry whose derivation mentions one of these is
#: inadmissible; the guard is asserted in test_registry_integrity.py.
INADMISSIBLE_SOURCES = ("MATLAB", "OpenQKDSecurity", "CVX", "MOSEK", "Julia")


@dataclass(frozen=True)
class OracleEntry:
    """One frozen expected value with the derivation that produced it."""

    oracle_id: str
    claims: tuple[str, ...]
    kind: str
    subject: str
    derivation: str
    toy_id: str | None = None
    #: Alpha-independent golden value, when there is a single one.
    value: float | int | str | None = None
    #: Closed form in alpha, when the value depends on the Renyi order.
    closed_form: Callable[[float], float] | None = None
    #: ``(alpha, value)`` pairs frozen from ``closed_form``. These guard a
    #: refactor or a typo in the closed form; the DERIVATION stays authoritative.
    frozen_values: tuple[tuple[float, float], ...] = ()
    #: Hypotheses a consuming theorem carries that must hold for this entry.
    hypotheses: tuple[str, ...] = field(default_factory=tuple)
    assurance: str = ASSURANCE
    #: ``"0.5.0"`` where the amendment MARKS this entry; see
    #: :data:`SUPERSEDED_BY_0_5_0`. An entry is never deleted and never
    #: silently edited: it is marked, and run B retires or rewrites it
    #: deliberately. ``None`` on every entry the amendment leaves standing.
    superseded_by: str | None = None
    #: Empty on every entry frozen once and never re-frozen. An entry the human
    #: operator authorises re-freezing carries here, dated, what changed, on
    #: whose decision, and the hand derivation from the claims that the new
    #: ``subject`` and ``derivation`` rest on -- the field
    #: ``registry_protocol_compiler.PCOracleEntry`` carries. One entry
    #: carries one: ``O-CGATE-DEGENERATE``.
    revalidation: str = ""


def _freeze(form: Callable[[float], float]) -> tuple[tuple[float, float], ...]:
    """Evaluate ``form`` on :data:`ALPHA_GRID`. Used only to author the table."""
    return tuple((a, form(a)) for a in ALPHA_GRID)


# ===========================================================================
#  Group 1 -- structural identities of the contracted objective (C2, C5, C6, C7)
# ===========================================================================

O_K_IDENTITY = OracleEntry(
    oracle_id="O-K-IDENTITY",
    claims=("C5",),
    kind="structural-identity",
    subject="K_chat = T_chat + P_chat - tr G_chat, exactly, at every feasible point.",
    derivation="""\
contract.tex Eq. eq:fK DEFINES K_chat(omega) = T_chat(omega) + P_chat(omega)
- tr G_chat(omega), so the identity is definitional; what an oracle can pin is
that an implementation's three ingredients are the contract's three, computed on
the same branch operator. The check therefore evaluates T, P and tr G
independently on hand-authored toys and compares K against the sector form
Eq. eq:c5-sector, K_chat = P_chat + sum_s f_{chat,s}, which is a THEOREM
(Theorem thm:branch-formula) and not a definition.

On TOY-1 at sector weights (w0, w1), w0 + w1 = 1:
  T_chat0 = w0 * 2^{1-alpha} + w1,  tr G_chat0 = w0 + w1 = 1,  P_chat0 = 1,
  K_chat0 = w0 * 2^{1-alpha} + w1 = 1 + w0 (2^{1-alpha} - 1),
  f_{chat0,s0} = w0 (2^{1-alpha} - 1),   f_{chat0,s1} = 0,
and P + sum_s f = 1 + w0 (2^{1-alpha} - 1) agrees.
""",
    toy_id="TOY-1",
)

O_K_RANGE = OracleEntry(
    oracle_id="O-K-RANGE",
    claims=("C5", "C6"),
    kind="structural-identity",
    subject=(
        "0 <= K_chat <= P_chat at every feasible point and every alpha in (1, inf)."
    ),
    derivation="""\
contract.tex Theorem thm:branch-formula. The LOWER bound is T_chat >= 0 together with
P_chat - tr G_chat = tr Theta_chat >= 0 (Lemma lem:branch-maps (i)). The UPPER bound is
T_chat <= tr G_chat, which is the pinching trace-power monotonicity of Lemma
foundations/lem:pinchmono (C6), so K_chat <= P_chat. Both bounds are needed downstream:
the branch entropy (1/(1-alpha)) log2(K/P) is non-negative exactly because of the
upper one, and that is what makes h_low >= 0 (Remark rem:hlow-range).

On TOY-1: K = 1 + w0 (2^{1-alpha} - 1) ranges over [2^{1-alpha}, 1] as w0 runs
over [0, 1], and P = 1, so the interval is strictly inside [0, P].
""",
    toy_id="TOY-1",
)

O_DEFICIT_SIGN = OracleEntry(
    oracle_id="O-DEFICIT-SIGN",
    claims=("C6", "C7"),
    kind="structural-identity",
    subject=(
        "f_{chat,s} <= 0 always, with equality exactly when G_{chat,s} is "
        "Z-block-diagonal -- in particular for every key-inert pair."
    ),
    derivation="""\
Corollary cor:f-nonpos, from Lemma foundations/lem:pinchmono's equality case: f_{chat,s}
= 0 iff G_{chat,s}(sigma) is a fixed point of the key pinching. Proposition prop:exact-cancellation
(C7) supplies the checkable sufficient condition on the DECLARATION: if r is
constant on the effective outcome set E^{(s)}_kappa of every pass class kappa,
then every Kraus term of G_{chat,s} carries a single R value, the sum is
R-block-diagonal, and f_{chat,s} vanishes for EVERY input -- not merely at the
optimum.

Golden signs:
  TOY-1  s0 (key-active):        f = w0 (2^{1-alpha} - 1) < 0 for w0 > 0
  TOY-1  s1 (key-inert):         f == 0 for every w1
  TOY-2  s0, s1 (both key-inert): f == 0 for every weight
  TOY-3  s0 (key-active):        f = m^{1-alpha} - 1 < 0
The sign is the direction that MATTERS: f > 0 would raise K above P and produce
a negative branch entropy.
""",
)

O_SECTOR_DECOMPOSITION = OracleEntry(
    oracle_id="O-SECTOR-DECOMPOSITION",
    claims=("C2", "C5"),
    kind="structural-identity",
    subject=(
        "Dense versus block agreement: G_chat(omega) = direct_sum_s "
        "G_{chat,s}(omega_s), hence T_chat = sum_s T_{chat,s} and "
        "K_chat = P_chat + sum_s f_{chat,s}."
    ),
    derivation="""\
Lemma lem:branch-maps (iii) and the sector form Eq. eq:c5-sector of Theorem thm:branch-formula. The
oracle is checked between two INDEPENDENTLY hand-written objects: the dense
Kraus operator on the whole of A x Q, and the per-sector Kraus operators. On
TOY-1 the dense operator has rows indexed by (v, q) with

  K[(v,q), q'] = delta_{q,q'} sqrt(F^{(q)}_v),

so G[(v,q), (v',q')] = delta_{q,q'} w_q sqrt(F^{(q)}_v F^{(q)}_{v'}) is block
diagonal in q -- the identity, verified rather than assumed.

Note the non-triviality: the key pinching Z groups rows by their R value
r(x0, v) = v, which CUTS ACROSS sectors (rows (v0,s0) and (v0,s1) share R = 0).
The two decompositions are different partitions of the same row set, and the
sector form survives only because G is already sector-block-diagonal.
""",
    toy_id="TOY-1",
)

O_TRACE_SPLIT = OracleEntry(
    oracle_id="O-TRACE-SPLIT",
    claims=("C1", "C2"),
    kind="structural-identity",
    subject=(
        "tr G_chat(omega) + tr Theta_chat(omega) = Phi[omega](chat), and "
        "sum_chat Phi[omega](chat) = 1."
    ),
    derivation="""\
Eq. eq:traces of Lemma lem:branch-maps (i), with Theorem thm:protocol-channel (iii) for normalization
of the statistics map. Golden values:
  TOY-1: single acceptance value chat0 with Phi = 1, all classes pass, so
         tr G_chat0 = 1 and tr Theta_chat0 = 0.
  TOY-4a/b: every class FAILS sifting, so G_chat == 0 (Lemma lem:branch-maps (iv), since
         Chat_key is empty) and the whole weight is in the fail branch:
         tr Theta_chat0 = 1/4, tr Theta_chat1 = 3/4, summing to 1.
  TOY-4c: Phi = (0, 1); the acceptance value chat0 is unreachable, which is what
         makes h_low infinite (see O-HLOW-INFINITE).
""",
)

O_BRANCH_ENTROPY = OracleEntry(
    oracle_id="O-BRANCH-ENTROPY",
    claims=("C4", "C5"),
    kind="analytic-limit",
    subject=(
        "H~down(Z | I Etilde)_{nu|chat} = (1/(1-alpha)) log2(K_chat / P_chat), "
        "checked against an independently known conditional entropy."
    ),
    derivation="""\
contract.tex Theorem thm:branch-formula, Eq. eq:c5, which rests on the imported pinching
identity Fact foundations/fact:pinch-id (kamin2025renyi, Thm. 8, Eq. (59)).

The independent value comes from TOY-3(m). There d_A = 1 and dim Q = 1, so the
purifying register is TRIVIAL and the branch state on Z is simply the uniform
distribution over the m raw-key values. Its sandwiched Renyi conditional entropy
with trivial conditioning is the Renyi entropy of a uniform distribution,

  H_alpha(Unif(m)) = (1/(1-alpha)) log2( sum_z (1/m)^alpha ) = log2(m),

for every alpha in (1, inf). The contract's formula gives K/P = m^{1-alpha} and
hence (1/(1-alpha)) log2(m^{1-alpha}) = log2(m). The two agree exactly, and the
second derivation never touches K, T or G.

Second point: TOY-1 at w0 = 1 gives K/P = 2^{1-alpha}, hence exactly 1 bit --
the pure state |eta> spread over two key values.
""",
    toy_id="TOY-3(m=2)",
)


# ===========================================================================
#  Group 2 -- analytic limits: closed-form h_low values (C8, C9b, C10)
# ===========================================================================

O_HLOW_DEPHASED = OracleEntry(
    oracle_id="O-HLOW-FULLY-DEPHASED",
    claims=("C5", "C8"),
    kind="analytic-limit",
    subject=(
        "Fully dephased branch: h_low = log2(m) exactly, at every alpha in (1, inf)."
    ),
    derivation="""\
TOY-3(m). The full derivation is in toy_declarations.fully_dephased: the single
feasible state gives K_chat0 = T_chat0 = m^{1-alpha}, P_chat0 = 1, the
divergence term vanishes because AcceptSet = {Phi[omega]}, and

  h_low = (1/(alpha-1)) log2(1 / m^{1-alpha}) = log2(m).

The value is INDEPENDENT of alpha, which makes it a good regression target: an
implementation whose alpha handling drifts will fail it at some alpha but not
others. It also sits inside the entropy-part ceiling of Remark rem:hlow-range,
log2|supp p| = log2(m) <= log2(d_Z + 1) = log2(m + 1).
""",
    toy_id="TOY-3(m=2)",
    value=1.0,
)

O_HLOW_DEPHASED_TABLE: tuple[tuple[int, float], ...] = (
    (2, 1.0),
    (3, math.log2(3)),
    (4, 2.0),
)

O_HLOW_DETERMINISTIC = OracleEntry(
    oracle_id="O-HLOW-DETERMINISTIC",
    claims=("C7", "C8"),
    kind="analytic-limit",
    subject=(
        "Deterministic / perfectly correlated raw key: every pair is key-inert, "
        "K = P, and h_low = 0 exactly at every alpha."
    ),
    derivation="""\
TOY-2. Each sector responds to exactly one Bob outcome, so every effective
outcome set is a singleton, every pair (chat0, s) is key-inert (Def. def:keyinert),
and Proposition prop:exact-cancellation gives f_{chat0,s} == 0 for every input. Hence
K_chat0 = P_chat0 = 1 and h_low = (1/(alpha-1)) log2(1) = 0.

Zero is the CORRECT answer and not a degenerate one: the raw key is a
deterministic function of the sector index, which the purifying register may
hold, so no secrecy is extractable. An implementation that returns a small
positive number here is overstating the key.
""",
    toy_id="TOY-2",
    value=0.0,
)

O_HLOW_ZERO_GENERATION = OracleEntry(
    oracle_id="O-HLOW-ZERO-GENERATION",
    claims=("C2", "C8"),
    kind="analytic-limit",
    subject=(
        "Zero generation (Chat_key empty) with a compatible acceptance set: "
        "h_low = 0 exactly at every alpha."
    ),
    derivation="""\
TOY-4a. Every announcement class fails sifting, so Chat_key = {} by Eq. eq:chkey
and G_chat == 0 for every chat by Lemma lem:branch-maps (iv). The objective Eq. eq:objective
reduces to the KL penalty alone, and AcceptSet = {Phi[omega]} = {(1/4, 3/4)}
makes that penalty zero. So h_low = 0.

This is a DIFFERENT mechanism from O-HLOW-DETERMINISTIC: there K-terms exist and
are trivial, here there are no K-terms at all. An implementation that indexes
the K-sum over the whole of Chat rather than over Chat_key will still return 0
here, so the two entries are checked together with O-TRACE-SPLIT, which
separates them.
""",
    toy_id="TOY-4a",
    value=0.0,
)

O_HLOW_RETENTION = OracleEntry(
    oracle_id="O-HLOW-RETENTION",
    claims=("C7", "C10"),
    kind="analytic-limit",
    subject=(
        "Dropping a constraint-active sector STRICTLY INCREASES h_low, from 0 "
        "to exactly 1 bit per round, at every alpha in (1, inf)."
    ),
    derivation="""\
contract.tex Proposition prop:retention (C10b), reproduced on TOY-1.
  With both sectors as variables:  inf over w0 in [0, 1] of
      (1/(alpha-1)) log2(1 / (1 + w0 (2^{1-alpha} - 1)))
  is attained at w0 = 0 with value 0.
  Forcing omega_{s1} = 0 (i.e. w0 = 1) gives K = 2^{1-alpha} and the value
      (1/(alpha-1)) log2(2^{alpha-1}) = 1.
The gap is exactly one bit, at EVERY alpha, and it is in the dangerous
direction: an implementation that prunes constraint-active sectors overstates
the key by one bit per round on this instance. The value 0 is the correct one --
an adversary that always populates the second sector makes the raw key
deterministic.
""",
    toy_id="TOY-1",
    value=0.0,
)

O_HLOW_RETENTION_DROPPED = 1.0

O_HLOW_NO_AVERAGING = OracleEntry(
    oracle_id="O-HLOW-NO-AVERAGING",
    claims=("C10",),
    kind="analytic-limit",
    subject=(
        "Averaging two sectors into one STRICTLY INCREASES h_low, from 0 to "
        "exactly 1 bit per round, at every alpha in (1, inf)."
    ),
    derivation="""\
contract.tex Proposition prop:no-averaging (C10c), reproduced on TOY-2 and its
averaged image TOY-2-AVG. Both declarations produce the same outcome statistics
-- TOY-2 at uniform sector weights and TOY-2-AVG on its single feasible state --
yet
  h_low(TOY-2)     = 0   (every pair key-inert, K = P = 1)
  h_low(TOY-2-AVG) = 1   (a single key-active sector with an unbiased response).
The obstruction is structural, not numerical: averaging erases the sector index
from the state space while the adversary retains it, so the averaged feasible
set no longer contains an image of every reachable attack. No simplification
step of an implementation may merge sectors; the only sanctioned
structure-changing simplification is Theorem thm:removal.
""",
    toy_id="TOY-2",
    value=0.0,
)

O_HLOW_NO_AVERAGING_AVERAGED = 1.0


def _hlow_constrained(alpha: float) -> float:
    """Return ``h_low`` on TOY-5/TOY-6 in closed form; see O-HLOW-CONSTRAINED."""
    return math.log2(2.0 / (1.0 + 2.0 ** (1.0 - alpha))) / (alpha - 1.0)


O_HLOW_CONSTRAINED = OracleEntry(
    oracle_id="O-HLOW-CONSTRAINED",
    claims=("C8", "C9b", "C17"),
    kind="analytic-limit",
    subject=(
        "One tau_A-homogeneous constraint pinning w0 >= 1/2 gives the "
        "alpha-dependent closed form h_low(L) = (1/(alpha-1)) log2(2 / "
        "(1 + 2^{1-alpha}))."
    ),
    derivation="""\
TOY-5. The feasible set of Eq. eq:feas gains the entry
  tr_Q[(1_A x Pi_s0) omega] = w0 >= 1/2 ,
so w0 in [1/2, 1]. The objective (1/(alpha-1)) log2(1 / K(w0)) with
K(w0) = 1 + w0 (2^{1-alpha} - 1) is increasing in w0 (the bracket is negative
for alpha > 1), so the infimum sits at the boundary w0 = 1/2:
  K = (1 + 2^{1-alpha}) / 2 ,  h_low(L) = (1/(alpha-1)) log2( 2 / (1 + 2^{1-alpha}) ).

This is the only entry in the registry whose value genuinely depends on alpha,
and the only positive-rate SECTOR instance, so it is the one that exercises the
objective's alpha handling end to end. It also pins two contract inequalities:
  h_low(L) >= h_low({}) = 0                (Definition def:hqkd-list; the
                                            constrained inner set is smaller)
  h_low(L) -> 1/2 as alpha -> 1+           (matching the C16 oracle below).
""",
    toy_id="TOY-5",
    closed_form=_hlow_constrained,
    frozen_values=(
        (1.05, 0.49566804691706573),
        (1.25, 0.47836619809201575),
        (1.5, 0.45689339367277615),
        (1.75, 0.4357362762413944),
        (1.9, 0.423253528932672),
    ),
)

O_HLOW_REMOVAL = OracleEntry(
    oracle_id="O-HLOW-REMOVAL",
    claims=("C10",),
    kind="analytic-limit",
    subject=(
        "Deleting a sector that satisfies (RM1)-(RM3) changes h_low by exactly "
        "zero, at a value that is not itself zero."
    ),
    derivation="""\
contract.tex Theorem thm:removal (C10a). TOY-6 is TOY-5 with a third sector s2
duplicating the key-inert sector s1; the (RM1)-(RM3) check is written out in
toy_declarations.TOY6_REMOVABLE. Since s1 and s2 are both key-inert their
deficits vanish identically (Proposition prop:exact-cancellation), K is unchanged, and the
infimum is again at w0 = 1/2:

  h_low(TOY-6) = h_low(TOY-5) = (1/(alpha-1)) log2( 2 / (1 + 2^{1-alpha}) ).

The entry is worth having only because the shared value is NON-ZERO: an
equality at zero would be satisfied by almost any bug. Its counterpart is
O-HLOW-RETENTION, where the criteria FAIL and deleting the sector moves the
value by a whole bit.
""",
    toy_id="TOY-6",
    closed_form=_hlow_constrained,
    frozen_values=O_HLOW_CONSTRAINED.frozen_values,
)


def _hlow_divergence_only(alpha: float) -> float:
    """Return ``h_low`` on TOY-4b in closed form; see O-HLOW-DIVERGENCE-ONLY."""
    return (alpha / (alpha - 1.0)) * (1.0 - 0.5 * math.log2(3.0))


O_HLOW_DIVERGENCE_ONLY = OracleEntry(
    oracle_id="O-HLOW-DIVERGENCE-ONLY",
    claims=("C3", "C8"),
    kind="analytic-limit",
    subject=(
        "Zero generation with an incompatible-but-absolutely-continuous "
        "acceptance set: h_low = (alpha/(alpha-1)) (1 - (1/2) log2 3), "
        "finite, positive, and divergent as alpha -> 1+."
    ),
    derivation="""\
TOY-4b. Chat_key is empty, so the objective Eq. eq:objective is the pure KL
penalty (alpha/(alpha-1)) D(q || Phi[omega]) with both arguments forced:
  q = (1/2, 1/2),  Phi[omega] = (1/4, 3/4),
  D = (1/2) log2( (1/2)/(1/4) ) + (1/2) log2( (1/2)/(3/4) )
    = 1/2 + (1/2)(1 - log2 3) = 1 - (1/2) log2 3 = 0.2075187496394...
  h_low(alpha) = (alpha/(alpha-1)) * 0.2075187496394... .

Two things this pins that no other entry does.
(1) The KL divergence really is the KL divergence sfD, not a Renyi divergence
    D_alpha. The penalty term of arqand2025meat, Cor. 4.2 / Eq. (137) -- read at its
    Eq. (118), "where the first term is the KL divergence" -- is D, and an
    earlier draft misquoted it. The number above is D and would differ under
    D_alpha, so an implementation that uses the wrong divergence fails here.
(2) h_low is UNBOUNDED as alpha -> 1+ on this instance, which is why Remark
    rem:hlow-range refuses any finite a-priori ceiling and requires the
    extended-real output domain [0, +inf].
""",
    toy_id="TOY-4b",
    closed_form=_hlow_divergence_only,
    frozen_values=(
        (1.05, 4.357893742427858),
        (1.25, 1.0375937481971098),
        (1.5, 0.6225562489182659),
        (1.75, 0.48421041582531793),
        (1.9, 0.4380951381276686),
    ),
)


# ===========================================================================
#  Group 3 -- the alpha -> 1+ consistency target (C16)
# ===========================================================================

#: The two hypotheses Theorem thm:oracle carries that Remark rem:oracle does NOT
#: repeat. Both are load-bearing and both must be recorded with any C16 check.
C16_EXTRA_HYPOTHESES: tuple[str, ...] = (
    "(H1) There is p_0 > 0 with q(chat) >= p_0 for EVERY q in AcceptSet and "
    "EVERY chat in Chat_key. A uniform positive floor on the key-live "
    "acceptance mass, not merely positivity at the optimum.",
    "(H2) The asymptotic feasible set Feas_1 = {omega in Feas : Phi[omega] in "
    "AcceptSet} is NONEMPTY -- i.e. the acceptance set is reachable by some "
    "feasible state.",
)

O_ALPHA_LIMIT = OracleEntry(
    oracle_id="O-ALPHA-LIMIT",
    claims=("C16",),
    kind="analytic-limit",
    subject=(
        "h_low(alpha) -> h_1, the blockwise relative-entropy program "
        "inf over Feas_1 of sum_chat sum_s D(G_{chat,s} || Z(G_{chat,s}))."
    ),
    derivation="""\
contract.tex Theorem thm:oracle, Eq. eq:oracle. The theorem is stated over the
declared feasible set, so it covers an arbitrary constraint list unchanged.

HYPOTHESES. The theorem carries two extra hypotheses that Remark rem:oracle does
not repeat, both recorded in C16_EXTRA_HYPOTHESES above and both checked per
entry below. They are not decorative: TOY-4b violates (H2) -- its acceptance set
is unreachable, Feas_1 is empty -- and there h_low(alpha) diverges as
alpha -> 1+ instead of converging to a finite limit (O-HLOW-DIVERGENCE-ONLY).

GOLDEN LIMITS, each computed twice: once as the alpha -> 1+ limit of the
hand-derived h_low(alpha), and once by evaluating the right-hand side of
Eq. eq:oracle directly.

  TOY-1: h_low(alpha) == 0 for all alpha, so the limit is 0. Directly:
     D(G_{chat0,s0}(w0) || Z(G_{chat0,s0}(w0))) = w0 exactly (computed below),
     D for the key-inert sector s1 is 0, and inf over Feas_1 = {w0 in [0,1]} of
     w0 is 0.                                                   0 = 0. OK
  TOY-3(m): h_low(alpha) == log2(m) for all alpha. Directly, the single feasible
     branch operator is |eta><eta| with |eta> uniform over m rows, so
     D(|eta><eta| || Z(|eta><eta|)) = -log2(1/m) = log2(m).     log2 m = log2 m. OK
  TOY-5: h_low(alpha) = (1/(alpha-1)) log2(2/(1 + 2^{1-alpha})). Writing
     eps = alpha - 1 and expanding 2^{-eps} = 1 - eps ln2 + O(eps^2):
        2 / (1 + 2^{-eps}) = 1 + (eps ln2)/2 + O(eps^2),
        log2 of that = eps/2 + O(eps^2),  divided by eps gives 1/2 + O(eps).
     Directly: inf over Feas_1 = {w0 in [1/2, 1]} of w0 = 1/2.   1/2 = 1/2. OK

THE PER-SECTOR RELATIVE ENTROPY, by hand. For the key-active sector of TOY-1 and
TOY-5, G = w0 |eta><eta| with |eta> = (1,1)/sqrt(2), and Z(G) = (w0/2) (|xi_0><xi_0|
+ |xi_1><xi_1|) for the two orthonormal rows. Then
  D(G || Z(G)) = tr[G log2 G] - tr[G log2 Z(G)]
               = w0 log2(w0) - w0 log2(w0 / 2) = w0 log2 2 = w0 .
So the C16 objective on TOY-1/TOY-5 is exactly the key-active sector weight.

WHAT THIS DOES NOT DO (Remark rem:oracle, restated): the oracle validates
consistency of the alpha -> 1+ limit. It does not certify (C13) and it does not
validate finite-alpha objective values. Disagreement is a defect in the
implementation, never a research question.
""",
    hypotheses=C16_EXTRA_HYPOTHESES,
)

#: ``(toy_id, h_1, alpha -> 1+ limit of h_low, p_0 witness, Feas_1 witness)``.
#: The two witnesses are what discharge (H1) and (H2) for that toy.
O_ALPHA_LIMIT_TABLE: tuple[tuple[str, float, float, float, str], ...] = (
    ("TOY-1", 0.0, 0.0, 1.0, "omega = diag(0, 1); Phi[omega] = delta_chat0"),
    ("TOY-3(m=2)", 1.0, 1.0, 1.0, "omega = [1]; Phi[omega] = delta_chat0"),
    (
        "TOY-3(m=3)",
        math.log2(3),
        math.log2(3),
        1.0,
        "omega = [1]; Phi[omega] = delta_chat0",
    ),
    ("TOY-5", 0.5, 0.5, 1.0, "omega = diag(1/2, 1/2); Phi[omega] = delta_chat0"),
)

O_ALPHA_LIMIT_HYPOTHESIS_FAILS = OracleEntry(
    oracle_id="O-ALPHA-LIMIT-HYPOTHESIS-FAILS",
    claims=("C16",),
    kind="analytic-limit",
    subject=(
        "When hypothesis (H2) fails -- Feas_1 empty -- h_low(alpha) diverges as "
        "alpha -> 1+ and Theorem thm:oracle does not apply."
    ),
    derivation="""\
TOY-4b. The only feasible state gives Phi[omega] = (1/4, 3/4), while
AcceptSet = {(1/2, 1/2)}, so Feas_1 = {omega in Feas : Phi[omega] in AcceptSet}
is EMPTY and hypothesis (H2) of Theorem thm:oracle fails. Correspondingly
  h_low(alpha) = (alpha/(alpha-1)) (1 - (1/2) log2 3)  ->  +inf as alpha -> 1+,
so no finite blockwise relative-entropy value is approached.

The entry exists so that an implementation cannot pass the C16 regression by
extrapolating a limit unconditionally: on this declaration the correct
behaviour is to REFUSE the alpha -> 1+ comparison (hypothesis unmet), not to
report a limit.
""",
    toy_id="TOY-4b",
)


# ===========================================================================
#  Group 4 -- fixed-length key assembly (C14, C15)
# ===========================================================================


@dataclass(frozen=True)
class KeyLengthCase:
    """One frozen key-length evaluation of contract Remark rem:plus2."""

    case_id: str
    rounds: int
    h_low: float
    lambda_ec: int
    eps_ev: float
    eps_pa: float
    alpha: float
    expected: int
    arithmetic: str
    ideal_hash: bool = True


KEY_LENGTH_CASES: tuple[KeyLengthCase, ...] = (
    KeyLengthCase(
        case_id="KL-1",
        rounds=1_000_000,
        h_low=1.0,
        lambda_ec=200_000,
        eps_ev=2.0**-30,
        eps_pa=2.0**-30,
        alpha=1.5,
        expected=799_881,
        arithmetic="""\
h_low = 1 bit/round is the TOY-3(m=2) oracle, so the entry is chained to a
value that is itself derived, not assumed. With alpha = 1.5,
alpha/(alpha-1) = 3 and log2(1/eps) = 30 for both budgets:
  n h_low                                  = 1 000 000
  - lambda_EC                              =  - 200 000  ->  800 000
  - ceil(log2(1/eps_EV)) = -30             ->  799 970
  - (alpha/(alpha-1)) log2(1/eps_PA) = -90 ->  799 880
  + 1                                      ->  799 881
The bracket is an exact integer, so the floor and the clamp are inactive here
and the case pins the ARITHMETIC of Eq. eq:keylength alone.""",
    ),
    KeyLengthCase(
        case_id="KL-2-floor",
        rounds=10,
        h_low=math.log2(3.0),
        lambda_ec=0,
        eps_ev=1.0,
        eps_pa=1.0,
        alpha=1.5,
        expected=16,
        arithmetic="""\
h_low = log2 3 is the TOY-3(m=3) oracle. At the maximal budgets eps = 1 both
deductions vanish (log2(1/1) = 0), so the bracket is
  10 log2 3 + 1 = 16.84962500721156 ,
and the reported value is floor(16.8496...) = 16. The case exists to pin the
DOWNWARD rounding of ARCHITECTURE_SPEC.md Section 14.4: 17 would be an
overstatement of the key by nearly one bit.""",
    ),
    KeyLengthCase(
        case_id="KL-3-clamp",
        rounds=1,
        h_low=1.0,
        lambda_ec=10,
        eps_ev=2.0**-30,
        eps_pa=2.0**-30,
        alpha=1.5,
        expected=0,
        arithmetic="""\
  1 - 10 - 30 - 90 + 1 = -128, so the clamp max{0, .} of Remark rem:plus2
fires and the reported length is 0. A negative key length is not a key length;
the contract's output domain is l >= 0.""",
    ),
    KeyLengthCase(
        case_id="KL-4-two-universal-hash",
        rounds=1_000_000,
        h_low=1.0,
        lambda_ec=200_000,
        eps_ev=2.0**-30,
        eps_pa=2.0**-30,
        alpha=1.5,
        expected=799_880,
        ideal_hash=False,
        arithmetic="""\
KL-1 under Assumption A-HASH's second reading. The privacy-amplification family
of Theorem thm:keylength is IDEAL two-universal (collision probability exactly
2^{-l}); for a merely two-universal family, tupkary2026decoy, Rem. 6.1 records a
one-bit penalty, and the contract requires Eq. eq:keylength to be tightened by
that bit: 799 881 - 1 = 799 880. The penalty is in the SAFE direction, and an
implementation that silently assumes the ideal family on a merely two-universal
one is off by one bit in the UNSAFE direction.""",
    ),
)

O_KEY_LENGTH = OracleEntry(
    oracle_id="O-KEY-LENGTH",
    claims=("C14",),
    kind="toy-instance",
    subject=(
        "l_max = max{0, floor(n h_low - lambda_EC - ceil(log2(1/eps_EV)) "
        "- (alpha/(alpha-1)) log2(1/eps_PA) + 1)}, on four frozen cases."
    ),
    derivation="""\
contract.tex Theorem thm:keylength Eq. eq:keylength, with the reported value
l_max of Remark rem:plus2. Each case's arithmetic is written out in
KEY_LENGTH_CASES; the h_low inputs are taken from the TOY-3 oracles rather than
invented, so the chain from the objective to the reported integer is closed.

THE +1 CONSTANT. It is this contract's, not the source's: the source region
proves secrecy for the ^Omega_AT state with constant +2, and this contract
spends one deterministic bit -- the announced error-verification acceptance flag
F_acc -- to reach the ACCEPTED state by an elementary contraction argument
(Remark rem:plus2). A profile preferring the source's convention adds the bit
back and must say so explicitly. An implementation must not silently use +2.

ALPHA DOMAIN. Every case has alpha in (1, 2). Assumption A-ALPHA confines every
KEY-LENGTH statement to that interval -- the Renyi leftover-hashing import
kamin2025renyi, Thm. 4, Eq. (13) is stated there -- even though claims C3-C12,
C16 and C17 individually hold on (1, inf).
""",
)

O_KEY_LENGTH_MONOTONE = OracleEntry(
    oracle_id="O-KEY-LENGTH-MONOTONE",
    claims=("C15",),
    kind="structural-identity",
    subject=(
        "l_max is non-increasing in lambda_EC, non-decreasing in eps_EV, and "
        "non-decreasing in eps_PA."
    ),
    derivation="""\
contract.tex Proposition prop:monotone (C15) and ARCHITECTURE_SPEC.md Section
14.4 ("increasing leakage or decreasing security errors cannot increase key
length"). h_low does not depend on any of the three, and in Eq. eq:keylength
  -lambda_EC                              is decreasing in lambda_EC,
  -ceil(log2(1/eps_EV))                   is non-decreasing in eps_EV,
  -(alpha/(alpha-1)) log2(1/eps_PA)       is increasing in eps_PA
                                          (alpha/(alpha-1) > 0 on (1, 2)),
and both the floor and the clamp are monotone. The direction is the whole point:
the failure mode this pins -- more leakage or a tighter budget buying MORE key --
is a security break, not a rounding artefact.
""",
)

O_KEY_LENGTH_EPS_TO_ZERO = OracleEntry(
    oracle_id="O-KEY-LENGTH-EPS-TO-ZERO",
    claims=("C14", "C15"),
    kind="analytic-limit",
    subject="l_max -> 0 as eps_PA -> 0+ and as eps_EV -> 0+, at fixed n and h_low.",
    derivation="""\
Rubric line R8 (behaviour as epsilon -> 0). In Eq. eq:keylength the deductions
(alpha/(alpha-1)) log2(1/eps_PA) and ceil(log2(1/eps_EV)) both diverge as their
budget goes to zero, so the bracket eventually goes negative and the clamp of
Remark rem:plus2 returns 0. Explicitly, l_max = 0 as soon as

  eps_PA <= 2^{-(alpha-1)/alpha * (n h_low - lambda_EC - ceil(log2(1/eps_EV)) + 1)} .

At n = 1000, h_low = 1, lambda_EC = 0, eps_EV = 1, alpha = 1.5 that threshold is
eps_PA <= 2^{-1001/3}, so eps_PA = 2^{-400} already gives l_max = 0. Demanding
perfect secrecy from a finite number of rounds yields no key, which is the
correct and conservative behaviour.
""",
)

O_KEY_LENGTH_LARGE_N = OracleEntry(
    oracle_id="O-KEY-LENGTH-LARGE-N",
    claims=("C14",),
    kind="analytic-limit",
    subject="l_max / n -> h_low as n -> inf, with an explicit finite-n envelope.",
    derivation="""\
Every deduction in Eq. eq:keylength except n h_low is independent of n, so with
  Delta := lambda_EC + ceil(log2(1/eps_EV)) + (alpha/(alpha-1)) log2(1/eps_PA)
the unclamped bracket is n h_low - Delta + 1 and, whenever it is non-negative,
  n h_low - Delta      <=  l_max  <=  n h_low - Delta + 1 ,
hence
  | l_max / n - h_low | <= (Delta + 1) / n .
At Delta = 200 120 (the KL-1 budgets) the envelope is 200 121 / n, so the rate
approaches h_low = 1 bit/round from below at order 1/n. The bound is stated with
an explicit constant rather than as a limit so that it is checkable at finite n.
""",
)

O_KEY_LENGTH_ACCEPTANCE_INDEPENDENT = OracleEntry(
    oracle_id="O-KEY-LENGTH-ACCEPTANCE-INDEPENDENT",
    claims=("C3", "C14"),
    kind="structural-identity",
    subject=(
        "l_max carries NO dependence on the acceptance probability Pr[Omega_AT]; "
        "in particular the Pr[Omega_AT] -> 1 limit is not a special case."
    ),
    derivation="""\
The accumulation bound Eq. eq:c3 carries the penalty
-(alpha/(alpha-1)) log2(1/Pr[Omega_AT]), and the secrecy step of Theorem
thm:keylength multiplies the leftover-hashing bound by Pr[Omega_AT] to pass to
the subnormalized ^Omega_AT state. With kappa = (alpha-1)/alpha > 0 the factor
2^{kappa log2(1/Pr[Omega_AT])} = 1/Pr[Omega_AT] CANCELS that prefactor exactly,
leaving Eq. eq:secrecy-at free of Pr[Omega_AT]. The reported l_max of Remark
rem:plus2 therefore has no Pr[Omega_AT] argument at all.

This is an interface fact, not a numeric one: an implementation that accepts an
acceptance probability as an input to the key-length computation, or that
special-cases Pr[Omega_AT] = 1, has added a parameter the contract does not
have. The only surviving hypothesis is Pr[Omega_AT] > 0 (Theorem thm:accumulated-entropy), and
its failure is exactly the h_low = +inf fail-closed branch (O-HLOW-INFINITE).
""",
    value="l_max is a function of (n, h_low, lambda_EC, eps_EV, eps_PA, alpha) only",
)


# ===========================================================================
#  Group 5 -- fail-closed behaviour (C13, C14, C17)
# ===========================================================================

O_HLOW_INFINITE = OracleEntry(
    oracle_id="O-HLOW-INFINITE",
    claims=("C8", "C14"),
    kind="fail-closed",
    subject=(
        "h_low = +inf must be propagated, never clamped, and NO key-length "
        "claim may be emitted when it is reached."
    ),
    derivation="""\
contract.tex Remark rem:hlow-range, fail-closed branch, on TOY-4c. There
Phi[omega] = (0, 1) for the only feasible state while AcceptSet = {(1/2, 1/2)},
so q(chat0) = 1/2 > 0 = Phi[omega](chat0), q is not absolutely continuous with
respect to Phi[omega], and the kernel convention u log2(u/0) = +inf of Lemma
foundations/lem:kernel gives O_alpha = +inf; the infimum over the singleton feasible set
is +inf. The output domain of h_low is the EXTENDED reals [0, +inf] precisely so
that this value can be reported.

WHY NO KEY LENGTH. h_low = +inf means no q in AcceptSet is absolutely continuous
with respect to any reachable Phi[omega], hence Pr[Omega_AT] = 0 for every
attack; the hypothesis Pr[Omega_AT] > 0 of Theorem thm:accumulated-entropy fails and the accepted
state is null. There is no run on which a key would be produced, so the
conforming behaviour is to emit no key-length claim and report the
declaration/acceptance mismatch. Returning a huge finite l_max -- which is what
substituting +inf into Eq. eq:keylength would suggest -- is the failure mode this
entry exists to forbid, and it is in the unsafe direction.

The contract states the interface consequence directly: "interface.yaml must
encode this branch explicitly rather than return a numeric l_max."
""",
    toy_id="TOY-4c",
    value=math.inf,
)

O_CONSTRAINT_GATE = OracleEntry(
    oracle_id="O-CONSTRAINT-GATE",
    claims=("C14", "C17"),
    kind="fail-closed",
    subject=(
        "A key-length output may be combined with a nonempty constraint list "
        "only if the list is tau_A-homogeneous AND attack_set_license is "
        "present. Hard-fail otherwise; numerical use stays unrestricted."
    ),
    derivation="""\
contract.tex Section 2.1 (the constraint_list row) and Section 4.19 ("Interface
consequence"). The gate has TWO parts and both must hold:
  (i)  tau_A-homogeneity, Theta_k = c_k tau_A (Definition def:homog) --
       mechanically checkable;
  (ii) the attack_set_license attestation of Assumption A-ATK -- NOT
       machine-checkable, and this module never verifies it; its absence simply
       disables the constrained branch.

Frozen verdicts:
  TOY-1  L empty                        -> key length ALLOWED (unconstrained branch)
  TOY-5  L homogeneous, no license      -> key length HARD-FAILS on part (ii)
  TOY-6  L homogeneous, no license      -> key length HARD-FAILS on part (ii)
  TOY-7  L non-homogeneous, no license  -> key length HARD-FAILS on part (i)
In every hard-fail case h_low itself remains a legitimate output: "numerical use
outside the security chain is unrestricted". The failure mode being forbidden is
a run that computes the tighter constrained h_low(L) >= h_low({}) and then feeds
it to Eq. eq:keylength without the license -- which overstates the key, since the
tightening is purchased entirely by A-ATK (contract Theorem thm:constrained-accumulation).

WHAT THE GATE DOES NOT ASSERT. This module never asserts attack-set inclusion
after squashing; A-ATK is a supplier obligation of proof-reductions. The
published instance that shows it is not vacuous is the flag-state squasher of
tupkary2026decoy, Lemma 9.4, Eqs. (151)-(152) (contract Example ex:fss).
""",
)

O_ASSURANCE_ESTIMATE = OracleEntry(
    oracle_id="O-ASSURANCE-ESTIMATE",
    claims=("C13",),
    kind="fail-closed",
    subject=(
        "Agreement with an oracle in this registry is never a certificate: "
        "every entry is assurance = estimate, and a result is labelled "
        "certified only by the runtime checks of contract Section 4.18."
    ),
    derivation="""\
REWRITTEN AT contract_version 0.4.0, because its old reason expired and its
conclusion did not.

THE OLD REASON, now spent. Through 0.3.0 C13 was tagged `open`, the contract
said "no code path may label any result certified" without qualification, and
STATUS.yaml recorded max_attainable_tier: estimate. Version 0.4.0 CLOSES C13
(Theorem thm:cert, Eq. eq:hcert: h_cert = beta_acc + beta_feas - eps_acc -
eps_feas <= h_low), zero claims are `open`, and under R14 as amended
(ADR-0005) max_attainable_tier is `certified`. The old sentence is therefore
no longer the contract's rule and must not be quoted as if it were.

THE REASON THAT REPLACES IT, and it is stronger. Tier eligibility is a CEILING,
not an assurance (contract Section 1.3). A RESULT is labelled `certified` only
when EVERY runtime check of Section 4.18 passes on the ACTUAL computation:
  (1) the exact membership x in D of Eq. eq:cert-domain, on the ROUNDED EXACT
      point -- every block omega_s PSD, tr omega <= 1, q >= 0 componentwise,
      supp q inside Chat_acc;
  (2) hypotheses (H1)-(H4) of Corollary cor:work-gradient with their CERTIFIED
      floors p_low, k_low, t_low;
  (3) the slack PSD verifications of Theorem thm:weak-duality;
  (4) the enclosure assembly of Proposition prop:budget.
Any failure falls back to `estimate` with a machine-readable reason naming the
failed or unrequested check, fail-closed (ARCHITECTURE_SPEC.md Section 3.5;
Remark rem:cert-interface). Reading an oracle table is none of (1)-(4).

WHAT STILL HOLDS, unchanged and pinned by this entry: evaluating O_alpha at a
feasible point bounds h_low from ABOVE, never from below, so no amount of
agreement between an implementation and this registry is a lower bound on
anything. Every entry here therefore carries assurance = estimate, this one
included, and the value frozen below is that word.

WHERE THE CERTIFIED LABEL IS PINNED INSTEAD: O-ASSURANCE-CERTIFIED-GATE names
the exact conditions under which `certified` MAY be emitted, and the four
fail-closed entries beside it name conditions under which it MUST NOT be.
""",
    value=ASSURANCE,
)

O_KERNEL_CONVENTIONS = OracleEntry(
    oracle_id="O-KERNEL-CONVENTIONS",
    claims=("C9b",),
    kind="structural-identity",
    subject=(
        "The lsc extension of d(u, v) = u log2(u/v): d(0, v) = 0 for every "
        "v >= 0 including v = 0, and d(u, 0) = +inf for u > 0."
    ),
    derivation="""\
Lemma foundations/lem:kernel and Definition foundations/def:kl. The extension is part of
claim C9b, not an afterthought: the kernel is the closed perspective of g(t) = t log2 t,
and it is exactly these values that make it jointly convex, lower semicontinuous, and
non-increasing in v -- the three properties Theorem thm:convexity uses to get
joint convexity of the objective through the CONCAVE K_chat.

Frozen values:
  d(0, 0)   = 0        (not NaN, and not +inf)
  d(0, 1/2) = 0
  d(1/2, 0) = +inf     (this is what produces h_low = +inf on TOY-4c)
  d(1/2, 1/2) = 0
  d(1/2, 1/4) = 1/2
  d(1/4, 1/2) = -1/4   (a single term may be NEGATIVE; only the full KL sum
                        over a pair of probability vectors is non-negative)
The last one matters: an implementation that clamps individual kernel terms at
zero computes a different, larger objective and overstates the key.
""",
)

O_CONVEXITY = OracleEntry(
    oracle_id="O-CONVEXITY",
    claims=("C9a", "C9b"),
    kind="structural-identity",
    subject=(
        "The objective is convex along the sector-weight family of TOY-1, and "
        "K_chat is concave there."
    ),
    derivation="""\
Theorem thm:convexity (C9b), resting on the concavity import Corollary
cor:concavity (C9a, from kamin2025renyi, App. F.1, Thm. 24).

Along TOY-1's one-parameter feasible family omega(w0) = diag(w0, 1 - w0):
  K(w0) = 1 + w0 c  with  c = 2^{1-alpha} - 1 in (-1, 0)
is AFFINE, hence in particular concave -- consistent with cor:concavity, which
gives concavity of K on the whole feasible set.
  O_alpha(w0) = -(1/(alpha-1)) log2(1 + w0 c)
has second derivative  c^2 / ((alpha-1) ln2 (1 + w0 c)^2)  > 0 on [0, 1], so it
is STRICTLY convex there. That is the direction the contract needs: convexity of
the objective is what makes Eq. eq:hlow-def a convex program whose infimum is
attained (Theorem thm:convexity), and it survives the composition
d(q, K(omega)) only because d is non-increasing in its second argument and K is
concave -- a concave K composed into a convex-decreasing kernel.
""",
    toy_id="TOY-1",
)


# ===========================================================================
#  Group 6 -- the 0.3.0 material: the two source modes, the party partition,
#             the singular trusted marginal, and the gradient face rule
# ===========================================================================
#
# Everything in this group was added at contract_version 0.3.0 or is one of
# the two implementation-found contract gaps that 0.3.0 closes (F-01-01, the
# declared basis of the Choi input register; F-01-02, the split face rule of
# thm:gradient (i)). None of it had an oracle before, because none of it was
# in the accepted contract before.


O_SOURCE_MODE_DERIVED = OracleEntry(
    oracle_id="O-SOURCE-MODE-DERIVED",
    claims=("C1",),
    kind="structural-identity",
    subject=(
        "The source mode is DERIVED from the marginal slot and is never "
        "separately declared: trusted exactly when alice_marginal is present, "
        "untrusted when it is absent."
    ),
    derivation="""\
contract.tex Section 2.5, the source_model convention, in its own words:
"trusted or untrusted, DERIVED, never separately declared -- it is trusted
exactly when alice_marginal is present (Remark rem:source-mode). A second key
carrying the mode would be a second source of truth and is forbidden."
Definition def:declaration types the slot as S_=(A) disjoint-union {none} and
says its two values ARE the two modes.

What an oracle can pin here is a PREDICATE, and its frozen verdicts:
  trusted   : TOY-1 .. TOY-7 (all twelve 0.2.4-era toys), TOY-8-T, TOY-9
  untrusted : TOY-1-UN, TOY-3(m=2)-UN, TOY-5-UN, TOY-8-UN, TOY-10
and the structural fact that no declaration in this registry carries a mode
field at all -- `source_mode()` reads it off `alice_marginal` and there is
nothing else it could read.

WHY IT IS WORTH FREEZING. Section 2.5 lists fourteen sites that branch on this
one bit -- def:declaration, def:homog, def:roundmodel, def:hqkd-list,
def:feasible, lem:range, thm:accumulated-entropy, thm:removal, thm:choi, thm:constrained-accumulation,
thm:keylength, cor:full-gradient, A-MARG and A-SRC. An implementation that
carried a second, independently settable mode key could put those fourteen
sites into a state the contract has no statement about; the contract forbids
the key rather than defining that state.
""",
    value="derived",
)

O_MARGINAL_INADMISSIBLE = OracleEntry(
    oracle_id="O-MARGINAL-INADMISSIBLE",
    claims=("C1", "C8"),
    kind="fail-closed",
    subject=(
        "tau_A = 0 is NOT how the absent marginal is expressed and must be "
        "rejected; tau_A = 1_A/d_A is not a neutral 'nothing is known' either. "
        "The absent marginal is the slot value `none`."
    ),
    derivation="""\
contract.tex Remark rem:source-mode (c) rejects tau_A = 0 on TWO INDEPENDENT
grounds, and an implementation that rejects it for only one of them will
accept the other spelling of the same mistake:
  (1) Assumption A-DECL (ii) requires the marginal slot to hold a NORMALIZED
      state, tr tau_A = 1, which tau_A = 0 fails outright.
  (2) Even with normalization dropped it expresses the OPPOSITE of the free
      set: for omega >= 0 on A x Q, omega_A = 0 gives tr omega = tr omega_A =
      0 and hence omega = 0, so Feas = {} in violation of A-DECL (vii) and
      Eq. eq:hlow-def would be an infimum over the empty set.

THE THIRD SPELLING, and the dangerous one. Assumption A-SRC records that
tau_A = 1_A/d_A is NOT a neutral way to say "nothing is known about the
source": it FIXES the marginal to maximally mixed and excludes every
adversarial source that sends anything else. It is a well-formed declaration
and must be accepted -- but it is a trusted-source declaration, it requires
source_replacement_license, and it is strictly stronger than the absent
marginal. TOY-7 is exactly this declaration at d_A = 2 (tau_A = I/2).

Frozen verdicts:
  tau_A = 0                 -> REJECT (A-DECL (ii); and Feas = {})
  tau_A = none              -> ACCEPT, untrusted-source mode
  tau_A = 1_A/d_A           -> ACCEPT, TRUSTED-source mode, licence required
  tau_A singular but /= 0   -> ACCEPT, trusted-source mode (TOY-9)
The Notation section adds that `none` is "deliberately not perp, which is the
sifting-failure key value, and not 0, which is inadmissible" -- three distinct
things that a JSON `null` would otherwise conflate.
""",
    value="reject",
)

O_MODE_EQUIVALENCE_DA1 = OracleEntry(
    oracle_id="O-MODE-EQUIVALENCE-DA1",
    claims=("C1", "C8"),
    kind="structural-identity",
    subject=(
        "At d_A = 1 the trusted and untrusted declarations are the SAME "
        "declaration, in all five respects of Remark rem:source-mode (b), and "
        "every computed quantity agrees to the last digit."
    ),
    derivation="""\
contract.tex Remark rem:source-mode (b). At d_A = 1, S_=(A) = {[1]}, so
trusted-source mode admits exactly one marginal; and for omega >= 0 on A x Q
the A-marginal IS the 1x1 matrix tr omega, so omega_A = tau_A and tr omega = 1
are the SAME CONDITION. Consequently:
  (b1) the two feasible sets of Eq. eq:feas coincide;
  (b2) A-MARG's n-round condition omega_{A_1^n} = tau_A^{tensor n} holds for
       every normalized state -- VACUOUSLY SATISFIED, which is not the same
       thing as violated;
  (b3) the licensed constraint classes coincide: every 1x1 Hermitian Theta_k
       equals c_k tau_A with c_k = Theta_k, so trusted-mode homogeneity IS the
       scalar typing of untrusted-source mode;
  (b4) the Choi parametrization degenerates: d_{A_0} = 1, iota = [1],
       W_tau = [1], chi = id, J_s = omega_s, and the coupling constraint of
       Eq. eq:choi-feas reads sum_s tr omega_s = 1 -- the untrusted-mode
       program of Remark def:untrusted-choi;
  (b5) A-SRC is VACUOUS: what it licenses is tr omega = 1, satisfied by every
       normalized state, so it deletes no attack, and an implementation must
       not demand the attestation.

FROZEN PAIRS. Each untrusted twin must reproduce its original exactly:
  TOY-1      / TOY-1-UN         h_low = 0                      (every alpha)
  TOY-3(m=2) / TOY-3(m=2)-UN    h_low = 1                      (every alpha)
  TOY-5      / TOY-5-UN         h_low = (1/(alpha-1)) log2(2/(1+2^{1-alpha}))
The TOY-5 pair also pins (b3) concretely: the trusted entry carries the
OPERATOR right-hand side Theta_1 = c_1 tau_A = [1/2] and the untrusted twin
the REAL SCALAR c_1 = 1/2, two different TYPES that cut out the same set
w0 >= 1/2. The TOY-3 pair is the one with a non-zero value, so a mode-handling
bug that returned 0 everywhere fails it.

This equivalence is also the pinned accumulation paper's own reading of its
channel conditional entropy: the sentence following
arqand2025meat, Eq. (1) recovers earlier definitions "by setting the C
register to be trivial and omitting the marginal constraint (equivalently,
setting A to be trivial)". The contract records that this is a statement about
that source's Eq. (1) and NOT about its Thm. 4.2a, and that (b1)-(b5) is its
own derivation and does not rest on it; the import-side check is
Fact fact:meat, locator note (vii).
""",
)


def _hlow_untrusted_gap(alpha: float) -> float:
    """Return TOY-8-T's ``h_low``; see O-UNTRUSTED-CONSERVATIVE."""
    return (alpha / (alpha - 1.0)) * (2.0 - 0.5 * math.log2(7.0))


O_UNTRUSTED_CONSERVATIVE = OracleEntry(
    oracle_id="O-UNTRUSTED-CONSERVATIVE",
    claims=("C8",),
    kind="analytic-limit",
    subject=(
        "Dropping the trusted marginal never increases h_low, and on TOY-8 it "
        "STRICTLY decreases it, from (alpha/(alpha-1)) (2 - (1/2) log2 7) to "
        "exactly 0."
    ),
    derivation="""\
contract.tex Remark rem:source-mode (a) proves the general direction: fix the
declaration data (O_k, bowtie_k, c_k) and compare Eq. eq:feas with tau_A
declared against the same with tau_A = none. Every omega feasible in
trusted-source mode is feasible in untrusted-source mode -- from
omega_A = tau_A we get tr omega = tr tau_A = 1, and taking the trace of the
operator entry tr_Q[(1_A x O_k) omega] bowtie_k c_k tau_A gives the scalar
entry tr[(1_A x O_k) omega] bowtie_k c_k, using tr tau_A = 1 and that X >= Y
implies tr X >= tr Y. So the untrusted feasible set is the LARGER and its
infimum the SMALLER:

    h_low(untrusted) <= h_low(trusted),  always.

TOY-8 makes it strict, and by a computable amount. The pair shares all its
declaration data; d_A = 2 with a one-dimensional sector, so a feasible omega
is a state on C^2, and Chat_key = {} makes the objective the pure KL penalty
(alpha/(alpha-1)) D(q || Phi[omega]) with Phi[omega] = (omega_00, omega_11).
  TRUSTED (tau_A = diag(7/8, 1/8)): omega_A = tau_A pins omega, so
    Phi = (7/8, 1/8) and
    D((1/2,1/2) || (7/8,1/8)) = (1/2) log2(4/7) + (1/2) log2 4
                              = 2 - (1/2) log2 7 = 0.596322538971198...,
    h_low = (alpha/(alpha-1)) (2 - (1/2) log2 7).
  UNTRUSTED (tau_A = none): Eq. eq:feas carries only tr omega = 1, so
    Phi ranges over the whole simplex, the accepted vector is reachable at
    omega = diag(1/2, 1/2), and h_low = 0.

WHICH DIRECTION IS DANGEROUS. Dropping the marginal LOSES rate and can never
turn an unsound declaration into a sound-looking one; declaring a tau_A
without the supplier attestation of A-SRC OVERSTATES the key -- here by
(alpha/(alpha-1)) (2 - (1/2) log2 7) bits per round, which is 1.788... at
alpha = 3/2 and diverges as alpha -> 1+. That is why Section 4.19 gates the
marginal fail-closed and why untrusted-source mode is the safe default.
""",
    toy_id="TOY-8-T",
    closed_form=_hlow_untrusted_gap,
    frozen_values=(
        (1.05, 12.522773318395146),
        (1.25, 2.98161269485599),
        (1.5, 1.7889676169135937),
        (1.75, 1.391419257599462),
        (1.9, 1.2589031378280846),
    ),
)

#: The untrusted-mode value of the same declaration data, at every alpha.
O_UNTRUSTED_CONSERVATIVE_UNTRUSTED_VALUE = 0.0

O_UNTRUSTED_SCALAR_CLASS = OracleEntry(
    oracle_id="O-UNTRUSTED-SCALAR-CLASS",
    claims=("C9b", "C17"),
    kind="fail-closed",
    subject=(
        "In untrusted-source mode the licensed constraint class is SCALAR. "
        "The operator form Theta_k = c_k 1_A is not merely unlicensed but "
        "wrong: it empties the feasible set at d_A >= 2."
    ),
    derivation="""\
contract.tex Definition def:homog (b) types the untrusted-mode right-hand side
as a real number and reads the entry as tr[(1_A x O_k) omega] bowtie_k c_k, a
comparison of REAL NUMBERS. Remark rem:homog (a) gives the structural reason:
in untrusted-source mode A is an OUTPUT of Eve's channel
(Definition def:roundmodel, Eq. eq:attackchannel), so the input side of the
adjoint identity carries no A factor and the operator-valued transport
Eq. eq:transport has no analogue -- only its trace survives, giving
Eq. eq:transport-un and the scalar class. The contract then states outright:
"the operator form Theta_k = c_k 1_A is NOT licensed", and exhibits a licensed
attack set for which imposing it would empty Feas.

THE WITNESS, re-derived here. Take the single entry
  O = 1_Q,   bowtie = succeq,   c = 1.
Its licensed attack set Eq. eq:attset-un is
  { A : A^dagger(1_A x 1_Q x 1_{E''}) >= 1 * 1_{E'} } = ALL CPTP maps,
because the adjoint of a CPTP map is unital, so the left-hand side is exactly
1_{E'}. Every attack sequence is admissible and the entry restricts nothing.
Read it the two ways:
  SCALAR (licensed, def:homog (b)):  tr[(1_A x 1_Q) omega] = tr omega = 1 >= 1
    -- satisfied by every feasible state, matching the fact that the attack set
    is everything. TOY-8-UN's h_low is unchanged at 0 by adding it.
  OPERATOR (unlicensed):  tr_Q[(1_A x 1_Q) omega] = omega_A >= 1_A. At d_A = 2
    this forces tr omega_A >= 2, contradicting tr omega = 1, so Feas = {} in
    violation of Assumption A-DECL (vii). The declaration would be rejected as
    infeasible although the attack set it came from admits every attack.

So the two readings are not two conventions for the same restriction: one is a
faithful state-level shadow of the licensed attack set and the other is a
condition no state satisfies. An implementation must type the right-hand side
by the DECLARED SOURCE MODE and must not obtain the untrusted program by
substituting W_tau = 1_A into Eq. eq:choi-feas -- which is the same mistake in
Choi coordinates and gives the same infeasible omega_A = 1_A
(Remark def:untrusted-choi (b)).
""",
    toy_id="TOY-8-UN",
)

O_CGATE_DEGENERATE = OracleEntry(
    oracle_id="O-CGATE-DEGENERATE",
    claims=("C14", "C17"),
    kind="fail-closed",
    subject=(
        "The mechanically checkable half of the two-part constraint gate is a "
        "type check at every d_A. It is VACUOUSLY TRUE in untrusted-source "
        "mode at any d_A, and at d_A = 1 it rejects only a `general` tag a "
        "producer can avoid. Where it degenerates, a passing part (i) is "
        "evidence of nothing and the gate rests entirely on the unverifiable "
        "attestation."
    ),
    derivation="""\
meat-core/rem:cgate, meat-core/def:homog and protocol-compiler/def:homog,
with meat-core/req:degenerate-gate-report and
meat-core/prop:trivial-alice-system (iii). RE-DERIVED AND RE-FROZEN; the record of what changed is the `revalidation` field below.

WHAT PART (i) CHECKS, case by case. Part (i) asks that the list be licensed
for the declared source mode, and protocol-compiler/def:homog, which
meat-core/def:homog cites, makes licensing "a type check on the tag, and it
compares no numbers": in trusted-source mode every entry must be declared
homogeneous, carrying a real c_k, and "a general entry is admissible input
... but it is not licensed, so a list containing one carries no key-length
claim". Neither definition makes an exception at any d_A.
  TRUSTED-source mode with d_A >= 2: a GENUINE restriction. The multiples of
    tau_A form a one-dimensional subspace of the d_A^2-dimensional real space
    of Hermitian operators on A, and a declaration can fail it by declaring
    the general form -- TOY-7 does, with Theta_1 = diag(1, 1/2) against
    tau_A = I/2.
  d_A = 1: still the type check, so an entry declared general FAILS it
    (rem:cgate: "An entry declared general fails it, as at every d_A"). It is
    DEGENERATE all the same: every 1x1 Hermitian Theta_k equals
    Theta_k * [1] = c_k tau_A (prop:trivial-alice-system (iii)), so the entry
    could always have been declared homogeneous with the same condition, and
    no declaration NEED fail part (i). A passing part (i) here is evidence of
    nothing (req:degenerate-gate-report). TOY-5 and TOY-6 are in this case.
  UNTRUSTED-source mode, ANY d_A: VACUOUSLY TRUE -- the entry TYPE is scalar
    by Definition def:declaration, so part (i) degenerates from a
    mathematical condition to a type check that a well-formed declaration
    passes by construction. TOY-5-UN is in this case.

TOY-5 AND TOY-6 IN THEIR TWO CARRIAGES. Each declares one entry
(O_1, succeq, .) at d_A = 1 with tau_A = [1], and its frozen record names the
scalar c_1 = 1/2 (homogeneous_scalar = 0.5): the declaration the record
describes is the homogeneous one. The frozen 0.1.0 operator-bundle builder
types every bound as an array, so on that wire the same entry arrives in the
general form Theta_1 = [1/2] (tests/support/licensed_form.py). The two
carriages denote the same condition w0 >= 1/2, and part (i) separates them by
the tag alone.

FROZEN VERDICTS, and the reason each fails:
  TOY-1     L empty                                       -> key length ALLOWED
  TOY-5     homogeneous c_1 = 1/2: part (i) PASSES, DEGENERATE (d_A = 1),
            no licence                                    -> HARD FAIL on part (ii)
  TOY-5     general Theta_1 = [1/2]: part (i) FAILS (the tag), no licence
                                                          -> HARD FAIL on (i) and (ii)
  TOY-6     the same two rows as TOY-5, for the same entry
  TOY-5-UN  part (i) VACUOUS (untrusted), no licence      -> HARD FAIL on part (ii)
  TOY-7     part (i) FAILS (trusted, d_A = 2)             -> HARD FAIL on part (i)
An implementation must not report a passing part (i) as evidence of anything
in the degenerate cases, and must still hard-fail on the missing attestation.
NO KEY LENGTH IS EMITTED ON ANY ROW BUT TOY-1's, and none was before: each
d_A = 1 row lacks the attack-set licence, so part (ii) refuses it whichever
carriage part (i) reads. Arguably the degeneration is correct: in the
no-marginal model the licensed class IS the scalar class (Remark rem:homog
(a)), so there is no wider class for part (i) to exclude, and the honest
statement is that the attestation is doing all of the work.
""",
    toy_id="TOY-5-UN",
    revalidation="""\
RE-DERIVED BY HAND AND RE-FROZEN on the owner's reading of the gate at
d_A = 1 (open item meat-core/constraint-gate-at-da1), the one frozen-oracle
change made for it.

WHAT CHANGED. The d_A = 1 case. The entry froze part (i) as "VACUOUSLY TRUE"
there -- "Every 1x1 Hermitian Theta_k equals Theta_k * [1] = c_k tau_A
(Remark rem:source-mode (b3)), so no declaration can fail it" -- and its
verdicts read "TOY-5 part (i) VACUOUS (d_A = 1), no licence -> HARD FAIL on
part (ii)", the same for TOY-6. The claims now read the gate the owner's way:
the licensed class of protocol-compiler/def:homog is a type check at every
d_A, so a general-tagged 1x1 entry is unlicensed, and rem:cgate's d_A = 1
paragraph says so. The subject, the d_A = 1 case and the TOY-5 and TOY-6 rows
are rewritten accordingly; the trusted d_A >= 2 case, the untrusted case and
the TOY-1, TOY-5-UN and TOY-7 rows are unchanged.

THE DERIVATION, FROM THE CLAIMS AND NOT FROM THE CODE.
(1) protocol-compiler/def:homog (a): in trusted-source mode "every entry is
    declared homogeneous, carrying c_k in R"; "Licensing is therefore a type
    check on the tag"; "a general entry ... is not licensed". No clause
    depends on d_A. meat-core/def:homog cites it ("the list is licensed when
    it is licensed for the declared source mode there").
(2) Hence at d_A = 1 in trusted-source mode an entry declared general fails
    part (i), and one declared homogeneous passes it. rem:cgate's d_A = 1
    paragraph states both halves.
(3) prop:trivial-alice-system (iii): at d_A = 1 the two classes coincide --
    a 1x1 Hermitian Theta_k is c_k [1] = c_k tau_A with c_k its one entry --
    so the general entry (O_1, succeq, [1/2]) and the homogeneous entry
    (O_1, succeq, 1/2) impose the same condition tr_Q[(1_A x O_1) omega]
    = w0 >= 1/2. A producer that declared the general one could have declared
    the homogeneous one; that is why part (i) is DEGENERATE there and why a
    pass is evidence of nothing (req:degenerate-gate-report, "at d_A = 1 and
    in untrusted-source mode").
(4) TOY-5 and TOY-6: alice_dim = 1, tau_A = [1], one entry with
    homogeneous_scalar = 0.5, attack_set_license = None. Homogeneous
    carriage: (i) passes by (2), degenerate by (3); (ii) fails, no licence;
    verdict HARD FAIL on (ii). General carriage, Theta_1 = [1/2]: (i) fails by
    (2); (ii) fails; verdict HARD FAIL on (i) and (ii).
(5) TOY-5-UN: untrusted-source mode, scalar entry c_1 = 1/2, no licence:
    rem:cgate's untrusted paragraph, part (i) vacuously true; (ii) fails;
    HARD FAIL on (ii). Unchanged.
(6) No number moves. Every d_A = 1 toy here carries no attack-set licence, so
    meat-core/req:constrained-key-gate withholds the key length on part (ii)
    under either reading; h_low is not a gate's to change, and TOY-1's
    unconstrained key length involves no constraint gate at all.""",
)

O_SOURCE_LICENSE_GATE = OracleEntry(
    oracle_id="O-SOURCE-LICENSE-GATE",
    claims=("C3", "C14"),
    kind="fail-closed",
    subject=(
        "A declared tau_A without source_replacement_license must hard-fail "
        "before any key-length output; at d_A = 1 the licence is vacuous and "
        "must NOT be demanded."
    ),
    derivation="""\
contract.tex Section 4.19, "Interface consequence", second half: "The same
fail-closed discipline governs the marginal: a declared tau_A without
source_replacement_license (Assumption A-SRC) must hard-fail before any
key-length output, and at d_A = 1 the licence is vacuous and must not be
demanded (Remark rem:source-mode (b5))." Section 2.1 types the input as
"optional; required whenever alice_marginal is present".

WHAT THE LICENCE BUYS, and why it is gated. A declared tau_A DELETES from
Eq. eq:feas every state whose A-marginal differs, hence every attack that
would have produced one. That is a different KIND of input from an entry of L
-- an entry of L restricts what Eve's channel may do to a register she holds,
whereas tau_A asserts that a register never reached her at all -- and a more
demanding one to justify. Absent the certificate the sound declaration is
untrusted-source mode, and O-UNTRUSTED-CONSERVATIVE measures the difference on
TOY-8: (alpha/(alpha-1)) (2 - (1/2) log2 7) bits per round, in the UNSAFE
direction.

FROZEN VERDICTS:
  d_A = 1, tau_A = [1], no licence   -> key length ALLOWED. The licence is
    VACUOUS: what it licenses is tr omega = 1, satisfied by every normalized
    state, so it deletes no attack. This covers every TRUSTED-source toy with
    d_A = 1 -- TOY-1 .. TOY-6 and the TOY-3 family -- none of which carries the
    record, and an implementation that demanded it there would be wrong.
    (TOY-10 is also d_A = 1 but is UNTRUSTED, so it falls under the last case
    below, not this one.)
  d_A >= 2, tau_A declared, no licence -> HARD FAIL before key length. TOY-7
    (tau_A = I/2) is in this case, and it fails A-SRC IN ADDITION to failing
    part (i) of the constraint gate; the two failures are independent and a
    conforming implementation reports the one it is asked about rather than
    letting either mask the other.
  d_A >= 2, tau_A declared, licence present -> ALLOWED. TOY-8-T and TOY-9.
  tau_A = none -> A-SRC is NOT ASSERTED and no licence exists to demand.
    TOY-8-UN, TOY-1-UN, TOY-3(m=2)-UN, TOY-5-UN, TOY-10.

A-MARG'S LEDGER ROW is read the same three ways and must not be collapsed:
NOT ASSERTED (untrusted-source mode), VACUOUSLY SATISFIED (d_A = 1), VIOLATED
(a tau_A is declared and the physical source does not produce it in every
round). Only the third is a violation, and only the third voids the key claim.
Like A-ATK, A-SRC is an attestation no program can verify: this module never
verifies it and never asserts it of any physical source.
""",
    toy_id="TOY-8-T",
)

O_PARTY_COMPUTABILITY = OracleEntry(
    oracle_id="O-PARTY-COMPUTABILITY",
    claims=("C1", "C14"),
    kind="structural-identity",
    subject=(
        "The raw-key map must factor through the declared key holder's OWN "
        "READOUT. On TOY-10, h = A is admissible and h = B is not -- while the "
        "superseded 0.2.x reading would have passed both."
    ),
    derivation="""\
contract.tex Assumption A-DECL (viii) and Eq. eq:partycomp: the declaration
names a party partition P, each party announces a function of its own readout,
and the declared key holder h computes the raw key from ITS OWN READOUT and
the announcements, r(x, v) = r_h(pi_h(x, v), a(x, v)) with r_h total.

TOY-10 is the declaration this widening was written for: the d_A = 1 embedding
of Remark rem:source-mode (b), where a protocol with no trusted source is
declared by folding the sender's outcome components into v. Its outcome
alphabet is V = {v00, v01, v10, v11} with pi_A(x0, v_ab) = a and
pi_B(x0, v_ab) = b, and its raw key is r(x0, v_ab) = a.

FROZEN VERDICTS:
  h = A  ADMISSIBLE. r = r_A(pi_A(x, v), a(x, v)) with r_A(a0, .) = 0,
         r_A(a1, .) = 1.
  h = B  INADMISSIBLE. pi_B(x0, v00) = pi_B(x0, v10) = b0 while
         r(x0, v00) = 0 and r(x0, v10) = 1, so no function of (pi_B, a) can
         produce r. Two outcomes with the SAME Bob readout carry DIFFERENT raw
         keys, which is the whole test.
  Under the superseded 0.2.x reading -- "r is a function of the holder's own
  outcome (x, v)" -- h = B would have PASSED, because r is a function of v.
  The contract says exactly this: that reading "would make it vacuous for any
  declaration that places both parties' data in v", which is this declaration
  shape, "while guaranteeing nothing about what the key holder can in fact
  compute".

WHY IT IS SECURITY-RELEVANT rather than cosmetic. A-DECL (viii) "is precisely
what makes the error-correction and verification steps of Theorem thm:keylength
physically executable": A-KEYREG has the holder compute Z_1^n from its own
outcome record and the public announcements, and reconciliation is one-way
FROM the holder. A declaration whose holder cannot compute Z_1^n has an
undefined C14 step, so the key-length statement is void rather than merely
optimistic.

The party partition's part (b) -- the party label of A and one per declared
tensor factor of each H(Q_s) -- carries a supplier obligation
(protocol-compiler) that this module never verifies, and no claim depends on
it. TOY-10's part (b) is nonetheless consistent: both sector factors are
one-dimensional and each party's outcome component is a private coin of
declared bias absorbed into the POVM elements, which Section 1.1 design
decision 1 names as this contract's way of carrying private randomness --
F^{(s0)}_{v_ab} = (1/2)(1/2) and F^{(s1)}_{v_ab} = [a = 0] * (1/2) both
factor across the two labelled factors.
""",
    toy_id="TOY-10",
)


def _hlow_toy9(alpha: float) -> float:
    """Return TOY-9's ``h_low``; see O-CHOI-BASIS-INVARIANCE."""
    return (alpha / (alpha - 1.0)) * 0.5 * math.log2(3.0)


O_CHOI_BASIS_INVARIANCE = OracleEntry(
    oracle_id="O-CHOI-BASIS-INVARIANCE",
    claims=("C11",),
    kind="structural-identity",
    subject=(
        "A singular tau_A is admissible; h_low is independent of the declared "
        "basis of the Choi input register A_0, while the reported J_s are "
        "relative to it and must be recorded."
    ),
    derivation="""\
contract.tex Remark rem:basis-invariance, Section 2.5's choi_ordering
convention, and Section 2.1's alice_marginal row. This is the closure of the
Round-1 implementation-verification finding F-01-01: the 0.2.4 text required
"the declared input basis of A_0" without naming one, and 0.2.5/0.3.0 resolve
it by proving the choice immaterial and REQUIRING the implementation to record
what it used, rather than by refusing a singular tau_A.

WHAT THE CONTRACT SETTLES, in its own words: "a SINGULAR tau_A is admissible
... ANY orthonormal basis of supp(tau_A) may be declared ... an implementation
must RECORD the iota it used, as the choi_input_basis field of
optimizer_certificate, whenever rank(tau_A) < d_A; and it MUST NOT refuse a
singular tau_A on the ground that the contract names no canonical basis,
because the contract deliberately names none."

THE PROOF, in four steps (rem:basis-invariance): (a) two admissible iota
differ by a unitary U on A_0, so W_tau -> W_tau U; (b) Ad_U carries
{J >= 0 : tr_Q J = 1_{A_0}} onto itself and chi' = chi . Ad_U; (c) the feasible
set and every objective ingredient are carried along, so h_low is unchanged --
independently, h_low is defined over the STATE variable by Eq. eq:hlow-def,
which never mentions A_0; (d) def:homog's homogeneous form is preserved and the
cor:full-gradient gradients are covariant.

FROZEN INSTANCE. TOY-9 has d_A = 3 and tau_A = diag(3/4, 1/4, 0), so
rank(tau_A) = 2 < 3 and A_0 is a proper subspace -- the only such declaration
in this registry. Its value is
  h_low(TOY-9) = (alpha/(alpha-1)) (1/2) log2 3
for every alpha in (1, inf), and it is constant over the whole feasible set,
because Gamma^{(s0)}_chat = M_x x 1_Q makes Phi depend on omega only through
omega_A, which trusted-source mode pins to tau_A. Two admissible isometries
are frozen with the toy:
  iota_1 = [e0, e1]                          -> J_1 = |f0><f0| x |0><0|
                                                   + |f1><f1| x |1><1|
  iota_2 = iota_1 H, H the 2x2 Hadamard      -> J_2 = (H^dagger x 1) J_1 (H x 1)
at the feasible point omega = (3/4)|e0><e0| x |0><0| + (1/4)|e1><e1| x |1><1|.
Both satisfy the coupling constraint sum_s tr_{Q_s} J_s = 1_{A_0}, both satisfy
chi(J) = omega, and J_1 /= J_2. That is the entry's whole content: the STATE
and h_low are basis-independent, the COORDINATES are not, and an implementation
that reports J without choi_input_basis has reported an unreadable matrix.

WHAT THIS ENTRY IS NOT. It pins no Choi PARAMETRIZATION and no program
assembly -- iota, omega, J_1 and J_2 are hand-authored literals, like the
branch Kraus operators, and building any of them from a declaration is
solver-side work that stays out of this tree.
""",
    toy_id="TOY-9",
    closed_form=_hlow_toy9,
    frozen_values=(
        (1.05, 16.642106257572124),
        (1.25, 3.96240625180289),
        (1.5, 2.377443751081734),
        (1.75, 1.8491229175080155),
        (1.9, 1.6730159729834426),
    ),
)


def _face_split_value(alpha: float) -> float:
    """Return the CORRECT ambient T of the rank-one witness; see below."""
    return 2.0 ** (1.0 - alpha)


def _face_compressed_value(alpha: float) -> float:
    """Return the value the WRONG compression returns for the same witness."""
    return 2.0 ** (-alpha)


O_GRADIENT_FACE_SPLIT = OracleEntry(
    oracle_id="O-GRADIENT-FACE-SPLIT",
    claims=("C6", "C12"),
    kind="structural-identity",
    subject=(
        "Compressing the trace-power functional to a non-Z-invariant subspace "
        "changes its value: on the rank-one witness the ambient value is "
        "2^{1-alpha} and the compressed one 2^{-alpha}."
    ),
    derivation="""\
contract.tex Theorem thm:gradient (i) and the witness inside its proof. This
is the closure of the Round-1 implementation-verification finding F-01-02: the
0.2.4 statement said "all operators compressed to supp X", its own proof
needed something else, and 0.2.5/0.3.0 restate the rule in the SPLIT form the
proof supports --
  (a) the divided-difference map D X^p[.] is compressed to S = supp X,
      i.e. the kernel sum runs over the STRICTLY POSITIVE spectrum only;
  (b) Y = Z(X^p), Y^{alpha-1} and Z(Y^{alpha-1}) are formed on the AMBIENT
      branch space and are NOT compressed to S.
Full compression to a subspace S' is licensed exactly when S is contained in
S' and S' is Z-invariant (Z_j S' contained in S' for every j); compressing to
S itself is that special case and is licensed only when S is Z-invariant. The
branch supports W_{chat,s} of Eq. eq:Wcs are in general NOT Z-invariant,
because A-DECL (viii) lets the raw-key value vary inside one announcement
class, so a single Kraus operator has range vectors spread over several
R-eigenvalues.

THE WITNESS, transcribed and re-derived. Let
  |eta> = a |j>_R |u> + b |j'>_R |u'>,  j /= j',  |a|^2 + |b|^2 = 1,
and X = |eta><eta|, so X^p = X for every p and
  Z(X^p) = |a|^2 |j,u><j,u| + |b|^2 |j',u'><j',u'|
has RANK TWO while X has rank one -- the pinching moved weight out of supp X.
  AMBIENT (correct):     T(X) = tr[(Z(X^p))^alpha] = |a|^{2 alpha} + |b|^{2 alpha}
  COMPRESSED TO S (wrong): (<eta| Z(X^p) |eta>)^alpha = (|a|^4 + |b|^4)^alpha
At |a|^2 = |b|^2 = 1/2 these are
  correct   T = 2 * 2^{-alpha} = 2^{1-alpha}
  wrong     T = (1/2)^alpha    = 2^{-alpha}
-- a factor of exactly 2, at every alpha. The frozen table below is the CORRECT
value; the companion `_face_compressed_value` is what the discarded rule
returns and exists so a test can assert the two differ rather than assert only
that one of them appears.

WHICH DIRECTION THE ERROR RUNS. The wrong value is SMALLER, and T enters the
objective through K_chat = P_chat + sum_s f_{chat,s} with f = T - tr G
(Eq. eq:fK). A smaller T gives a smaller K, and the kernel d(u, v) =
u log2(u/v) is NON-INCREASING in v (Lemma foundations/lem:kernel), so a smaller K gives
a LARGER objective, a LARGER h_low and a LARGER key length. The discarded rule
therefore errs in the UNSAFE direction, which is why the contract calls the
split rule "the rule an implementation must realize" rather than one of two
acceptable conventions.

WHERE IT BITES IN THIS REGISTRY. The witness is not exotic: TOY-1's sector s0
at w0 = 1 IS it, with |eta> = (1, 1)/sqrt2 spread over the two raw-key values,
and its frozen T = w0 * 2^{1-alpha} is the ambient value. TOY-10's s0 is the
same phenomenon over four outcomes. A solver that prefers a compressed ambient
space must use a Z-invariant S' containing W_{chat,s}, for instance
sum_j Z_j W_{chat,s}.

WHAT THIS ENTRY IS NOT. It pins no gradient. Every number here is a value of
the trace-power functional T of Eq. eq:fK, the same functional C6 bounds; what
C12 contributes is the licensing condition that decides WHICH of the two
numbers is T's value.
""",
    toy_id="TOY-1",
    closed_form=_face_split_value,
    frozen_values=(
        (1.05, 0.9659363289248455),
        (1.25, 0.8408964152537145),
        (1.5, 0.7071067811865476),
        (1.75, 0.5946035575013605),
        (1.9, 0.5358867312681466),
    ),
)

#: What the discarded "compress everything to supp X" rule returns on the same
#: witness, at :data:`ALPHA_GRID`. Frozen so that a test can assert the two
#: rules disagree, and by exactly a factor of two.
O_GRADIENT_FACE_COMPRESSED_VALUES: tuple[tuple[float, float], ...] = (
    (1.05, 0.48296816446242274),
    (1.25, 0.42044820762685725),
    (1.5, 0.3535533905932738),
    (1.75, 0.29730177875068026),
    (1.9, 0.2679433656340733),
)


# ===========================================================================
#  Group 7 -- the 0.4.0 certificate chain: C18 (perturbed objective),
#  C19 (weak duality), C20 (floating-point budget) and the closed C13.
# ===========================================================================
#
# READ THE HEADER OF THIS FILE FIRST, "WHAT THIS REGISTRY DOES NOT DO". C13 is
# closed and `certified` is reachable; nothing in this group certifies
# anything, and the entries that say when the label must NOT be reachable are
# the load-bearing half.
#
# THE AMBIENT BRANCH DIMENSION d_{chat,s}, used by every C18 entry below and
# counted here once. contract.tex Section 4.15 defines it as
#   d_{chat,s} = dim H(R x XY x C_A C_B x A x Q_s) ,
# the dimension of the space Eq. eq:Wcs lives in -- NOT the rank of the branch
# operator. For TOY-1's pair (chat0, s0):
#   R      : the raw-key register carries Z_perp = Z u {perp} with
#            Z = {0, 1}, so dim R = d_Z + 1 = 3 ;
#   XY     : |X| . |V| = 1 . 2 = 2 ;
#   C_A C_B: one announcement class, so 1 ;
#   A      : d_A = 1 ;
#   Q_s0   : 1 .
# Hence d_{chat0,s0} = 3 . 2 . 1 . 1 . 1 = 6, and the same count gives
# d_{chat0,s1} = 6. Getting this wrong changes every perturbed number below,
# which is why it is written out rather than inferred.


@dataclass(frozen=True)
class SeriesTailCase:
    """One frozen evaluation of the binomial tails of Lemma ``lem:series``."""

    case_id: str
    beta: float
    #: Lower end of the rescaled window ``[c, 1]`` of Lemma lem:series.
    c: float
    n: int
    a: float
    theta: float
    k0: int
    b_beta: float
    eta0: float
    eta1: float
    #: ``sup_{[c,1]} |y^beta - P_n(y)|``, computed in closed form by hand.
    exact_value_error: float
    #: ``sup_{[c,1]} |beta y^{beta-1} - P_n'(y)|``, likewise.
    exact_derivative_error: float
    arithmetic: str


SERIES_TAIL_CASES: tuple[SeriesTailCase, ...] = (
    SeriesTailCase(
        case_id="SER-1-integer-beta-n1",
        beta=2.0,
        c=1.0 / 3.0,
        n=1,
        a=2.0 / 3.0,
        theta=0.5,
        k0=1,
        b_beta=2.0,
        eta0=0.4444444444444444,
        eta1=4.0,
        exact_value_error=0.1111111111111111,
        exact_derivative_error=0.6666666666666666,
        arithmetic="""\
beta = 2, window [c, 1] = [1/3, 1]. The lemma's constants, in order:
  a     = (1 + c)/2 = (1 + 1/3)/2 = 2/3
  theta = (1 - c)/(1 + c) = (2/3)/(4/3) = 1/2
  k_0   = max(0, ceil((beta - 1)/2)) = ceil(1/2) = 1
  B_beta= max_{0<=k<=1} |binom(2, k)| = max(1, 2) = 2
Tails at n = 1:
  eta_0(1) = B a^beta theta^{n+1} / (1 - theta)
           = 2 . (2/3)^2 . (1/2)^2 / (1/2) = 2 . (4/9) . (1/4) . 2 = 4/9
  eta_1(1) = B a^{beta-1} ((n+1)(1-theta) + theta)/(1-theta)^2 . theta^n
           = 2 . (2/3) . ((2)(1/2) + 1/2)/(1/4) . (1/2)
           = (4/3) . (3/2) . 4 . (1/2) = 4
EXACT ERRORS, in closed form. For integer beta = 2 the expansion has three
terms, so P_1(y) = a^2 + 2a(y - a) = 2ay - a^2 and
  y^2 - P_1(y) = (y - a)^2 ,   2y - P_1'(y) = 2(y - a) .
On [1/3, 1] with a = 2/3, |y - a| <= 1/3 at BOTH endpoints, so
  sup |y^2 - P_1(y)|      = (1/3)^2 = 1/9 = 0.111111...
  sup |2y - P_1'(y)|      = 2/3     = 0.666666...
Both are <= their bounds (1/9 <= 4/9; 2/3 <= 4), which is the whole content of
Eq. eq:series-tails at this point.""",
    ),
    SeriesTailCase(
        case_id="SER-2-integer-beta-terminates",
        beta=2.0,
        c=1.0 / 3.0,
        n=3,
        a=2.0 / 3.0,
        theta=0.5,
        k0=1,
        b_beta=2.0,
        eta0=0.1111111111111111,
        eta1=1.6666666666666665,
        exact_value_error=0.0,
        exact_derivative_error=0.0,
        arithmetic="""\
THE CASE THE CONTRACT'S OWN RATIO-TEST REMARK DOES NOT COVER, and it is
reachable: beta = alpha = 2 is admitted by Assumption A-ALPHA for the C13 /
C18-C20 chain, which is stated on (1, inf). The contract accepted the gap as debt
in a JUSTIFICATION, not in a RESULT -- "the series terminates, the tails are
zero, and the stated bounds stay non-negative". This entry freezes exactly
that, so the reading is checkable rather than asserted.

Same constants as SER-1 (a = 2/3, theta = 1/2, k_0 = 1, B = 2). At n = 3:
  eta_0(3) = 2 . (2/3)^2 . (1/2)^4 / (1/2) = (16/9) . (1/16) = 1/9
  eta_1(3) = 2 . (2/3) . ((4)(1/2) + 1/2)/(1/4) . (1/8)
           = (4/3) . (5/2) . 4 . (1/8) = 5/3
EXACT ERRORS: ZERO, both of them. For n >= beta = 2 the binomial expansion
about a is the finite identity
  P_n(y) = a^2 + 2a(y - a) + (y - a)^2 = (a + (y - a))^2 = y^2 ,
so y^2 - P_n(y) == 0 and 2y - P_n'(y) == 0 identically on the window.
WHAT THIS PINS. The bounds 1/9 and 5/3 are LOOSE here by exactly the whole
error, and they are still SOUND and still NON-NEGATIVE -- the two properties
the certificate consumes. An implementation may not special-case integer beta
to return a smaller number than Eq. eq:series-tails gives, and it may not
return a negative one.""",
    ),
    SeriesTailCase(
        case_id="SER-3-fractional-beta",
        beta=0.5,
        c=1.0 / 3.0,
        n=4,
        a=2.0 / 3.0,
        theta=0.5,
        k0=0,
        b_beta=1.0,
        eta0=0.05103103630798288,
        eta1=0.9185586535436918,
        exact_value_error=-1.0,
        exact_derivative_error=-1.0,
        arithmetic="""\
beta = 1/2 -- the exponent p = 1/alpha at alpha = 2, which is the one
Proposition prop:budget (b) applies to X^{(delta)}. Window [1/3, 1], so
a = 2/3 and theta = 1/2 as before, but now
  k_0    = max(0, ceil((1/2 - 1)/2)) = max(0, ceil(-1/4)) = 0
  B_beta = |binom(1/2, 0)| = 1 .
Tails at n = 4:
  eta_0(4) = 1 . (2/3)^{1/2} . (1/2)^5 / (1/2) = sqrt(2/3) . 2^{-4}
           = 0.816496580927726 / 16 = 0.05103103630798288
  eta_1(4) = 1 . (2/3)^{-1/2} . ((5)(1/2) + 1/2)/(1/4) . (1/2)^4
           = sqrt(3/2) . 2 . 6 . 2^{-4} = 1.224744871391589 . 0.75
           = 0.9185586535436918
NO EXACT ERROR IS FROZEN (both fields carry the sentinel -1.0): for
non-integer beta the series does not terminate and the exact sup has no
elementary closed form, so writing one down would be inventing a number rather
than deriving it. What is checkable, and what the test checks, is the
INTERNAL structure: k_0 = 0 exactly when beta <= 1, B_beta = 1 there, and both
tails are positive and strictly decreasing in n.""",
    ),
    SeriesTailCase(
        case_id="SER-4-integer-beta-theta-third",
        beta=3.0,
        c=0.5,
        n=2,
        a=0.75,
        theta=1.0 / 3.0,
        k0=1,
        b_beta=3.0,
        eta0=0.07031249999999997,
        eta1=0.984375,
        exact_value_error=0.015625,
        exact_derivative_error=0.1875,
        arithmetic="""\
A THIRD ratio theta, so that no entry can pass by hard-coding theta = 1/2.
beta = 3, window [1/2, 1]:
  a      = (1 + 1/2)/2 = 3/4
  theta  = (1/2)/(3/2) = 1/3
  k_0    = ceil((3 - 1)/2) = 1
  B_beta = max(|binom(3,0)|, |binom(3,1)|) = max(1, 3) = 3 ,
and the lemma's coefficient claim holds for ALL k here: |binom(3,2)| = 3 and
|binom(3,3)| = 1 are both <= 3.
Tails at n = 2:
  eta_0(2) = 3 . (3/4)^3 . (1/3)^3 / (2/3) = (81/64) . (3/2) . (1/27)
           = 9/128 = 0.0703125
  eta_1(2) = 3 . (3/4)^2 . ((3)(2/3) + 1/3)/(4/9) . (1/3)^2
           = (81/64) . (2n + 3) . 3^{-n} at n = 2 = (81/64) . 7 / 9
           = 63/64 = 0.984375
EXACT ERRORS: P_2 drops only the k = 3 term (y - a)^3, so
  y^3 - P_2(y) = (y - a)^3 ,  3y^2 - P_2'(y) = 3(y - a)^2 ,
and |y - a| <= 1/4 on [1/2, 1] gives
  sup |y^3 - P_2(y)|   = (1/4)^3 = 1/64  = 0.015625
  sup |3y^2 - P_2'(y)| = 3/16            = 0.1875 ,
both comfortably inside 9/128 and 63/64.
The stored eta_0 reads 0.07031249999999997 rather than 0.0703125: that is the
binary-floating-point value of the displayed product evaluated left to right,
frozen as computed rather than rounded to the exact rational it approximates.""",
    ),
)

O_SERIES_TAILS = OracleEntry(
    oracle_id="O-SERIES-TAILS",
    claims=("C20",),
    kind="analytic-limit",
    subject=(
        "The explicit binomial tails eta_0(n), eta_1(n) of Lemma lem:series at "
        "four hand-chosen (beta, c, n), including two with beta a POSITIVE "
        "INTEGER, where the series terminates and the exact tails are zero."
    ),
    derivation="""\
contract.tex Lemma lem:series, Eq. eq:series-tails. The lemma rescales any
window [c, C] to [c/C, 1] by z -> y = z/C (values scale by C^beta, derivatives
by C^{beta-1}), so every case below is stated on [c, 1] directly.

  a = (1 + c)/2 ,  theta = (1 - c)/(1 + c) in [0, 1) ,
  k_0 = max(0, ceil((beta - 1)/2)) ,  B_beta = max_{0<=k<=k_0} |binom(beta,k)| ,
  eta_0(n) = B_beta a^beta theta^{n+1} / (1 - theta) ,
  eta_1(n) = B_beta a^{beta-1} ((n+1)(1 - theta) + theta)/(1 - theta)^2 theta^n .

THE COEFFICIENT BOUND, checked rather than assumed. The lemma claims
|binom(beta,k)| <= B_beta for ALL k >= 0, from |beta - k|/(k+1) <= 1 for
k >= (beta-1)/2. Both halves hold there: beta - k <= k + 1 exactly when
k >= (beta-1)/2, and k - beta <= k + 1 for every beta > 0. So |binom(beta,k)|
is non-increasing beyond k_0 and the maximum over 0..k_0 dominates everything.
SER-4 exhibits this at beta = 3, where the true maximum over all k is 3 and
B_beta = 3.

The four cases and their arithmetic are in SERIES_TAIL_CASES. Two of them,
SER-1 and SER-2, sit at beta = 2 -- the integer case that alpha = 2 makes
reachable through the exponent beta = alpha of Proposition prop:budget (b) --
and SER-4 at beta = 3 with a different theta. SER-3 is the fractional exponent
p = 1/alpha the same proposition applies to X^{(delta)}.

WHY BOTH BOUNDS MATTER SEPARATELY. eta_0 feeds Lemma lem:transfer (i), the
VALUE transfer used for the matrix powers and for the trace-level evaluation of
T(X^{(delta)}); eta_1 feeds Lemma lem:transfer (ii), the PAIRING bound on the
divided-difference map. They enter different terms of Eq. eq:budget and an
implementation that computed one and reused it for the other would be
unsound in the eta_1 direction, where the extra factor k in the tail makes
eta_1 the larger of the two on every case here.
""",
)


@dataclass(frozen=True)
class LogTailCase:
    """One frozen evaluation of the atanh tail of Lemma ``lem:logs``."""

    case_id: str
    z: float
    n: int
    w: float
    partial_sum: float
    exact: float
    error: float
    bound: float
    arithmetic: str


LOG_TAIL_CASES: tuple[LogTailCase, ...] = (
    LogTailCase(
        case_id="LOG-1-ln2",
        z=2.0,
        n=2,
        w=1.0 / 3.0,
        partial_sum=0.6930041152263374,
        exact=0.6931471805599453,
        error=0.00014306533360786133,
        bound=0.0001469723691945914,
        arithmetic="""\
z = 2 is the case the lemma singles out: "with ln 2 enclosed by the same series
at z = 2 (i.e. w = 1/3), log2 z = ln z / ln 2 is enclosed by an outward-rounded
quotient of enclosures". So this is the DENOMINATOR of every base-2 logarithm
on the certified path, and its enclosure width multiplies into all of them.
  w = (2 - 1)/(2 + 1) = 1/3 .
  2 sum_{j=0}^{2} w^{2j+1}/(2j+1) = 2 (1/3 + (1/27)/3 + (1/243)/5)
    = 2 (1/3 + 1/81 + 1/1215) = 2 . 0.34650205761316873
    = 0.6930041152263374 .
  ln 2 = 0.6931471805599453 , so the true error is 1.4306533360786e-4 .
  Bound, Eq. eq:log-tail: 2 |w|^{2n+3} / ((2n+3)(1 - w^2))
    = 2 (1/3)^7 / (7 . (8/9)) = (2/2187)(9/56) = 3/20412
    = 1.469723691945914e-4 .
The bound exceeds the error by 4 percent -- tight, which is what makes it a
useful oracle: a formula off by a factor would show immediately.""",
    ),
    LogTailCase(
        case_id="LOG-2-negative-w",
        z=0.5,
        n=2,
        w=-1.0 / 3.0,
        partial_sum=-0.6930041152263374,
        exact=-0.6931471805599453,
        error=0.00014306533360786133,
        bound=0.0001469723691945914,
        arithmetic="""\
z = 1/2 gives w = (1/2 - 1)/(1/2 + 1) = -1/3, the SIGN case. The series
2 sum w^{2j+1}/(2j+1) has odd powers only, so it is an odd function of w and
the partial sum is the exact negative of LOG-1's; ln(1/2) = -ln 2 likewise.
The tail bound of Eq. eq:log-tail depends on |w| and on w^2 only, so it is
IDENTICAL to LOG-1's, 3/20412.
WHAT THIS PINS: the tail bound is a bound on the ABSOLUTE error and does not
change sign, while the enclosure midpoint does. An implementation that took
w rather than |w| in the numerator would produce a NEGATIVE radius here, which
is not an enclosure at all -- and, fed into Definition def:enclosure, would
silently claim an interval that excludes the true value.""",
    ),
    LogTailCase(
        case_id="LOG-3-ln3",
        z=3.0,
        n=3,
        w=0.5,
        partial_sum=1.0980654761904762,
        exact=1.0986122886681098,
        error=0.0005468124776335515,
        bound=0.0005787037037037037,
        arithmetic="""\
z = 3, w = (3-1)/(3+1) = 1/2 -- a larger |w|, hence a slower tail, at a larger
truncation order.
  2 sum_{j=0}^{3} w^{2j+1}/(2j+1)
    = 2 (1/2 + (1/8)/3 + (1/32)/5 + (1/128)/7)
    = 2 . 0.5490327380952381 = 1.0980654761904762 .
  ln 3 = 1.0986122886681098 , error 5.468124776336e-4 .
  Bound: 2 (1/2)^9 / (9 . (1 - 1/4)) = (1/256)/6.75 = 5.787037037037e-4 .
COMPOSITION, which is the point of having a second case: Lemma lem:logs
reaches log2 by an outward-rounded QUOTIENT of two such enclosures, so
log2 3 = ln 3 / ln 2 is enclosed by combining LOG-3 with LOG-1. Both radii
enter, and the quotient's radius is larger than either -- an implementation
that enclosed only the numerator would understate it.""",
    ),
)

O_LOG_TAIL = OracleEntry(
    oracle_id="O-LOG-TAIL",
    claims=("C20",),
    kind="analytic-limit",
    subject=(
        "The scalar-logarithm tail of Lemma lem:logs at z = 2, z = 1/2 and "
        "z = 3, with the exact errors it must dominate; and log2 as an "
        "outward-rounded quotient of two such enclosures."
    ),
    derivation="""\
contract.tex Lemma lem:logs, Eq. eq:log-tail. With w = (z-1)/(z+1) in (-1, 1),
  ln z = 2 sum_{j>=0} w^{2j+1}/(2j+1) ,
  | ln z - 2 sum_{j=0}^{n} w^{2j+1}/(2j+1) | <= 2 |w|^{2n+3} / ((2n+3)(1-w^2)) .
The bound is the lemma's own geometric majorization:
  2 sum_{j>n} |w|^{2j+1}/(2j+1) <= (2|w|^{2n+3}/(2n+3)) sum_{i>=0} |w|^{2i} .

WHERE THIS IS CONSUMED. Proposition prop:budget (e): "the logarithms and
quotients of Eqs. eq:grad-q-work--eq:grad-w-work from the certified floors by
Lemma lem:logs". Every coefficient of the working gradient is a log2 of a
ratio of two quantities known only to lie in certified positive windows, so
this lemma is what turns the transcendental part of the gradient into an
enclosure. It is also the ONLY transcendental atom of the chain that is not a
matrix function.

The three cases are in LOG_TAIL_CASES: the ln 2 denominator every base change
divides by, the negative-w sign case, and a slower-converging value that has
to be composed with the first to reach log2 3.
""",
)


@dataclass(frozen=True)
class TransferCase:
    """One frozen evaluation of Lemma ``lem:transfer`` on a 2 x 2 matrix."""

    case_id: str
    #: Which part of the lemma this pins: "i", "ii", "iii" or "iv".
    part: str
    #: The attained left-hand side of the lemma's inequality.
    attained: float
    #: The lemma's bound on it.
    bound: float
    arithmetic: str


#: The single hand-chosen matrix every TRANSFER case is stated on, written out
#: here once. ``X = diag(1/4, 1)``, so ``spec X = {1/4, 1}`` is inside the
#: window ``[c, C] = [1/4, 1]`` and ``d = 2``.
TRANSFER_X_SPECTRUM: tuple[float, ...] = (0.25, 1.0)
TRANSFER_WINDOW: tuple[float, float] = (0.25, 1.0)
TRANSFER_DIMENSION: int = 2
#: ``f(x) = x^2``, ``P(x) = x`` on that window, so
#: ``eta_0 = sup |x^2 - x| = 1/4`` (at x = 1/2) and
#: ``eta_1 = sup |2x - 1| = 1`` (at x = 1), and ``L_f = sup |2x| = 2``.
TRANSFER_ETA0: float = 0.25
TRANSFER_ETA1: float = 1.0
TRANSFER_LIPSCHITZ: float = 2.0

TRANSFER_CASES: tuple[TransferCase, ...] = (
    TransferCase(
        case_id="TR-1-value-operator-norm",
        part="i",
        attained=0.1875,
        bound=0.25,
        arithmetic="""\
f(X) - P(X) = X^2 - X = diag(1/16 - 1/4, 1 - 1) = diag(-3/16, 0), whose
eigenvalues are exactly (f - P)(1/4) and (f - P)(1). Operator norm 3/16 =
0.1875, and the lemma's bound is eta_0 = 1/4: the spectral mapping makes part
(i) an inequality between a value ATTAINED at an eigenvalue and a supremum
over the whole window, so it is tight exactly when an eigenvalue attains the
sup -- here it does not, because sup |x^2 - x| sits at x = 1/2, between the
two eigenvalues.""",
    ),
    TransferCase(
        case_id="TR-2-value-frobenius",
        part="i",
        attained=0.1875,
        bound=0.3535533905932738,
        arithmetic="""\
The same error operator diag(-3/16, 0) measured in Frobenius norm: 3/16, since
it has one nonzero eigenvalue. The lemma's bound is sqrt(d) eta_0 =
sqrt(2)/4 = 0.3535533905932738.
WHY THE sqrt(d) FACTOR IS NOT DECORATION: Definition def:enclosure measures
MATRIX enclosures in Frobenius norm while the spectral argument of part (i)
gives an OPERATOR-norm radius, and prop:budget's proof records the conversion
||E||_F <= sqrt(d) ||E|| explicitly as the first of its three amplification
constants. An implementation that carried the operator-norm radius into a
Frobenius enclosure would understate it by up to sqrt(d).""",
    ),
    TransferCase(
        case_id="TR-3-pairing-offdiagonal",
        part="ii",
        attained=0.5,
        bound=2.0000000000000004,
        arithmetic="""\
The divided-difference kernels on spec X = {1/4, 1}: for f(x) = x^2,
f^[1](l, m) = l + m; for P(x) = x, P^[1] == 1. So the ERROR kernel is
  k_ij = (f - P)^[1](l_i, l_j) = l_i + l_j - 1 = [[-1/2, 1/4], [1/4, 1]] .
With X diagonal, (Df(X) - DP(X))[M] is the entrywise product k o M.
Take M = H = [[0, 1], [1, 0]] (Hermitian, ||M||_F = ||H||_F = sqrt 2):
  E = k o M = [[0, 1/4], [1/4, 0]] ,  tr[E H] = 1/4 + 1/4 = 1/2 .
The lemma's bound is eta_1 ||M||_F ||H||_F = 1 . sqrt2 . sqrt2 = 2. Stored as
2.0000000000000004, the binary value of sqrt(2) * sqrt(2).
NOTE WHAT IS NOT CLAIMED. |k_22| = 1 = eta_1, so the kernel maximum is
attained; the lemma still refuses to conclude any OPERATOR-norm bound on E
from it, and says so in place ("No operator-norm bound is claimed from the
kernel maximum, and none is needed"). That refusal is the Schur-multiplier
trap, and Eq. eq:budget is written as a bound on PAIRINGS against Frobenius-
unit directions precisely so that it is never needed.""",
    ),
    TransferCase(
        case_id="TR-4-frobenius-norm-form",
        part="ii",
        attained=0.5,
        bound=1.0,
        arithmetic="""\
The norm form of part (ii), added at 0.4.0 in answer to a Round-9 observation:
||(Df(X) - DP(X))[M]||_F <= eta_1 ||M||_F, the supremum of the pairing over
Hermitian H with ||H||_F <= 1, attained at H = E/||E||_F.
Take M = diag(1, 0), ||M||_F = 1. Then
  E = k o M = diag(-1/2, 0) ,  ||E||_F = 1/2 ,
against the bound eta_1 ||M||_F = 1. The attaining direction is
H = E/||E||_F = diag(-1, 0), and tr[E H] = 1/2 = ||E||_F, which is the
identity the lemma's proof uses.
E is Hermitian because k is real and symmetric (k_ij = k_ji), which is the
hypothesis the norm form needs and which part (ii) states.""",
    ),
    TransferCase(
        case_id="TR-5-lipschitz",
        part="iii",
        attained=1.7677669529663689,
        bound=2.8284271247461903,
        arithmetic="""\
Part (iii), the ARGUMENT-error route of prop:budget (d). With f(x) = x^2 the
full kernel is f^[1](l, m) = l + m, so on spec X = {1/4, 1}
  Df(X)[M] = [[l_1+l_1, l_1+l_2], [l_2+l_1, l_2+l_2]] o M .
Take M = [[0,1],[1,0]] and M' = 0:
  Df(X)[M] - Df(X)[M'] = [[0, 5/4], [5/4, 0]] , Frobenius norm
    (5/4) sqrt 2 = 1.7677669529663689 ;
  bound L_f ||M - M'||_F = 2 . sqrt 2 = 2.8284271247461903 ,
with L_f = sup_{[1/4,1]} |2x| = 2.
prop:budget (d) uses this at L_f = p c^{p-1}, the maximum of |(x^p)'| on the
certified window of Lemma lem:window -- which is why the window's LOWER end
being certified positive is what makes the Lipschitz constant finite at all.""",
    ),
    TransferCase(
        case_id="TR-6-rational-form",
        part="iv",
        attained=1.25,
        bound=1.25,
        arithmetic="""\
Part (iv) states DP(X)[M] = sum_m p_m sum_{a+b=m-1} X^a M X^b, a RATIONAL
matrix expression and hence interval-evaluable under Assumption A-IA. This
case checks it against the spectral form of Lemma lem:dk on the same data, so
that two independently written expressions must agree.
Take P(x) = x^2 (p_2 = 1), X = diag(1/4, 1), M = [[0,1],[1,0]]:
  rational form: sum_{a+b=1} X^a M X^b = M X + X M
    = [[0, 1], [1/4, 0]] + [[0, 1/4], [1, 0]] = [[0, 5/4], [5/4, 0]] ;
  spectral form: (l_i + l_j) o M = [[0, 1/4 + 1], [1 + 1/4, 0]]
    = [[0, 5/4], [5/4, 0]] .
Identical. The frozen scalar is the off-diagonal entry 5/4 = 1.25, and the
`attained == bound` pair records that this part is an IDENTITY, not an
inequality -- the one part of lem:transfer that is.""",
    ),
)

O_TRANSFER_BOUNDS = OracleEntry(
    oracle_id="O-TRANSFER-BOUNDS",
    claims=("C20",),
    kind="structural-identity",
    subject=(
        "All four parts of Lemma lem:transfer on X = diag(1/4, 1) with "
        "f(x) = x^2 and P(x) = x: value transfer in both norms, the pairing "
        "bound and its Frobenius form, the Lipschitz bound, and the rational "
        "DP(X)[M] identity."
    ),
    derivation="""\
contract.tex Lemma lem:transfer. One hand-chosen matrix serves all four parts
so that the constants are shared and a reader checks one spectrum:
  X = diag(1/4, 1) ,  spec X = {1/4, 1} subset [c, C] = [1/4, 1] ,  d = 2 ,
  f(x) = x^2 ,  P(x) = x ,
  eta_0 = sup_{[1/4,1]} |x^2 - x| = 1/4      (attained at x = 1/2)
  eta_1 = sup_{[1/4,1]} |2x - 1|   = 1       (attained at x = 1)
  L_f   = sup_{[1/4,1]} |2x|       = 2       (attained at x = 1) .
f and P are chosen POLYNOMIAL on purpose: every quantity below is then an
exact rational and the reader needs no series. The lemma itself is stated for
any f in C^1[c, C] and any polynomial P, and the certificate instantiates it
with f a matrix power and P the truncation of Lemma lem:series -- which is why
SER-1..SER-4 and this entry are the two halves of the same step.

The six cases are in TRANSFER_CASES, one per checkable statement:
  TR-1, TR-2  part (i), operator norm then Frobenius norm with the sqrt(d)
              conversion prop:budget's proof names explicitly;
  TR-3        part (ii), the PAIRING bound, with a note on what the lemma
              deliberately does NOT conclude from the kernel maximum;
  TR-4        part (ii) in norm form, added at 0.4.0, with its attaining H;
  TR-5        part (iii), the L_f Lipschitz bound in Frobenius norm;
  TR-6        part (iv), an IDENTITY, cross-checked against Lemma lem:dk.

WHY THE KERNEL IS COMPUTED BY HAND. The divided-difference kernel of
(f - P) on this spectrum is k_ij = l_i + l_j - 1, i.e.
[[-1/2, 1/4], [1/4, 1]], because f^[1](l, m) = (l^2 - m^2)/(l - m) = l + m and
P^[1] == 1; the diagonal entries are the derivative values 2l - 1. No
divided-difference routine is used or needed, which is what keeps this entry
an oracle rather than a second implementation.
""",
)

O_SQRT_RESIDUAL = OracleEntry(
    oracle_id="O-SQRT-RESIDUAL",
    claims=("C20",),
    kind="structural-identity",
    subject=(
        "Lemma lem:sqrt: ||sqrt A - sqrt B|| <= ||A - B||^{1/2}, tight at "
        "B = 0, and its exact-residual corollary ||S - sqrt A|| <= "
        "||S^2 - A||^{1/2} on a hand-chosen non-diagonal A."
    ),
    derivation="""\
contract.tex Lemma lem:sqrt. The certificate needs it because Eq. eq:kraus
carries sqrt(M_x) x sqrt(F_v): the branch Kraus operators contain POVM square
roots, which are transcendental in general, and prop:budget (a) encloses them
"once per declaration by Lemma lem:sqrt (ii)". Part (ii) is what makes that
possible WITHOUT a certified square-root routine -- any candidate S produced by
any means is admissible, and the exactly computable residual S^2 - A bounds how
far off it is.

PART (i), THREE FROZEN INSTANCES.
  (a) TIGHT, and equality: A = diag(1/4, 0), B = 0. Then sqrt A = diag(1/2, 0)
      and sqrt B = 0, so ||sqrt A - sqrt B|| = 1/2, while
      ||A - B||^{1/2} = (1/4)^{1/2} = 1/2. EQUALITY -- so the exponent 1/2
      cannot be improved, and an implementation using ||A - B|| in place of its
      square root would be UNSOUND here by a factor of 2 in the wrong
      direction (1/2 > 1/4).
  (b) STRICT: A = diag(1, 1/4), B = diag(1/4, 1/4). Then
      ||sqrt A - sqrt B|| = ||diag(1/2, 0)|| = 1/2 while
      ||A - B||^{1/2} = (3/4)^{1/2} = 0.8660254037844386.
  (c) The lemma's proof is an eigenvector argument, not a perturbation
      expansion: at a unit eigenvector psi of sqrt A - sqrt B with eigenvalue
      +t, <psi|(A - B)|psi> = t <psi|(sqrt A + sqrt B)|psi> >= t^2, using
      sqrt B >= 0. Instance (a) is exactly the equality case of that step.

PART (ii), ON A NON-DIAGONAL A. Take
  A = [[5/4, 3/4], [3/4, 5/4]] ,  eigenvalues 2 and 1/2 on (1,1)/sqrt2 and
  (1,-1)/sqrt2 , so sqrt A = [[3/(2 sqrt2), 1/(2 sqrt2)],
                              [1/(2 sqrt2), 3/(2 sqrt2)]] ,
and the candidate S = [[1, 1/2], [1/2, 1]] (a plausible but wrong root).
  S^2 = [[5/4, 1], [1, 5/4]] ,  S^2 - A = [[0, 1/4], [1/4, 0]] ,
  ||S^2 - A|| = 1/4 (exactly computable from exact data),
  bound = (1/4)^{1/2} = 1/2 .
The TRUE distance, from the closed form above:
  S - sqrt A = [[1 - 3 sqrt2/4, 1/2 - sqrt2/4],
                [1/2 - sqrt2/4, 1 - 3 sqrt2/4]] ,
whose eigenvalues are (1 - 3 sqrt2/4) +- (1/2 - sqrt2/4), i.e.
  3/2 - sqrt2 = 0.08578643762690485  and  (1 - sqrt2)/2 = -0.20710678118654752 ,
so ||S - sqrt A|| = (sqrt2 - 1)/2 = 0.20710678118654752 <= 1/2. Sound, with
room; the residual bound is loose here by about a factor 2.4, which is the
price of never needing a certified eigensolver.
""",
    value=0.20710678118654752,
)

#: The three PART (i) instances of O-SQRT-RESIDUAL, as
#: ``(||sqrt A - sqrt B||, ||A - B||^{1/2})`` pairs, in the order (a), (b) and
#: the part (ii) instance. The first pair is an EQUALITY.
SQRT_RESIDUAL_PAIRS: tuple[tuple[float, float], ...] = (
    (0.5, 0.5),
    (0.5, 0.8660254037844386),
    (0.20710678118654752, 0.5),
)


# ---------------------------------------------------------------------------
#  C18 -- the perturbed objective on TOY-1's key-active branch.
# ---------------------------------------------------------------------------
#
# THE BRANCH, written out once. TOY-1's pair (chat0, s0) has the single Kraus
# operator of Eq. eq:kraus mapping H(A x Q_s0) = C into the 6-dimensional
# ambient branch space counted at the head of this group:
#   K^{(s0)} = sqrt(1/2) |R=0, (x0,v0)> + sqrt(1/2) |R=1, (x0,v1)> ,
# so at omega_s0 = [w0] the branch operator is the RANK-ONE
#   X = X_{chat0,s0}(w0) = w0 |eta><eta| ,
#   |eta> = ( |R=0,(x0,v0)> + |R=1,(x0,v1)> ) / sqrt 2 ,
# with tr X = w0. The key pinching Z keeps entries whose two rows carry the
# same R value, so Z(|eta><eta|) = (1/2)(P_1 + P_2) with P_1, P_2 the rank-one
# projectors onto the two basis vectors -- ORTHOGONAL, and lying in different
# R blocks. That is the whole reason f_{chat0,s0} is nonzero: s0 is key-active.
#
# THE PERTURBED OPERATOR, Definition def:perturbed Eq. eq:mix, at d = 6:
#   X^{(delta)} = (1 - delta) w0 |eta><eta| + delta w0 (1/6) 1 ,
# so spec X^{(delta)} = { ((1-delta) + delta/6) w0  once ,
#                          (delta/6) w0             five times } .
# Writing A = (((1-delta) + delta/6) w0)^p and B = ((delta/6) w0)^p with
# p = 1/alpha,
#   (X^{(delta)})^p = B 1 + (A - B) |eta><eta| ,
#   Z((X^{(delta)})^p) = B 1 + (A - B) (1/2)(P_1 + P_2) ,
# whose spectrum is { (A+B)/2 twice, B four times }, and therefore
#   T(X^{(delta)}) = 2 ((A+B)/2)^alpha + 4 B^alpha .
# Since tr X^{(delta)} = tr X = w0 (the mixing map is trace-preserving),
#   f^{(delta)}_{chat0,s0}(w0) = 2 ((A+B)/2)^alpha + 4 B^alpha - w0 ,
# and at w0 = 1, using 4 B^alpha = 4 (delta/6)^{p alpha} = 2 delta/3,
#   f^{(delta)} = 2 ((a+b)/2)^alpha + 2 delta/3 - 1 ,
#   a = ((6 - 5 delta)/6)^p ,  b = (delta/6)^p .
# THIS IS A HAND DIAGONALIZATION OF ONE RANK-ONE BRANCH, not the general
# routine: a solver must build the 6 x 6 operator, perturb it, take a matrix
# power, pinch and trace.


def _f_delta_toy1_s0(alpha: float, delta: float = 0.5, dimension: int = 6) -> float:
    """Return ``f^(delta)_{chat0,s0}(w0 = 1)`` on TOY-1; see the block above."""
    p = 1.0 / alpha
    a = ((1.0 - delta) + delta / dimension) ** p
    b = (delta / dimension) ** p
    return 2.0 * ((a + b) / 2.0) ** alpha + (dimension - 2) * b**alpha - 1.0


def _f_plain_toy1_s0(alpha: float) -> float:
    """Return the UNPERTURBED ``f_{chat0,s0}(w0 = 1) = 2^{1-alpha} - 1``."""
    return 2.0 ** (1.0 - alpha) - 1.0


O_MIX_DOMINATION = OracleEntry(
    oracle_id="O-MIX-DOMINATION",
    claims=("C6", "C9a", "C18"),
    kind="analytic-limit",
    subject=(
        "The domination chain of Lemma lem:mix-dom on TOY-1's key-active "
        "branch at w0 = 1 and delta = 1/2: "
        "f <= (1 - delta) f <= f^(delta) <= 0, then 0 <= K <= K^(delta,Ret), "
        "then O^(delta,Ret) <= O_alpha, the last with O_alpha = 1.0 bit at "
        "every alpha."
    ),
    derivation="""\
contract.tex Lemma lem:mix-dom, all three parts, on the branch diagonalized in
the block above this entry. The point is omega = diag(1, 0) -- the whole weight
on the key-active sector s0, which is IN the certificate domain D of
Eq. eq:cert-domain (PSD blocks, tr omega = 1 <= 1) and also feasible for
TOY-1, so both sides of the chain are defined.

PART (i), the pointwise chain, at delta = 1/2 and w0 = 1:
  f = 2^{1-alpha} - 1                       (the frozen TOY-1 value)
  (1 - delta) f = f / 2
  f^{(delta)} = 2 ((a+b)/2)^alpha + delta/3 . 2 - 1 , a, b as above .
At alpha = 2 every term is a surd and the closed form collapses to
  f = -1/2 , (1-delta) f = -1/4 ,
  f^{(1/2)} = sqrt(7)/12 - 1/3 = -0.11285405741128415 ,
because a = sqrt(7/12), b = sqrt(1/12), ((a+b)/2)^2 = (2/3 + sqrt7/6)/4 and
4 b^2 = 1/3. The chain -1/2 <= -1/4 <= -0.1128... <= 0 holds strictly at every
inequality, which is what makes this a useful oracle: an implementation that
mixed with 1/d instead of tr[X]/d, or that used the wrong ambient dimension,
lands outside it.
Both LIMITS check: as delta -> 0+, a -> 1, b -> 0 and f^{(delta)} -> 2 . 2^{-alpha}
- 1 = 2^{1-alpha} - 1 = f, the unperturbed value; at delta = 1 (excluded, but
the limit is informative), a = b and f^{(1)} = 2/6 + 2/3 - 1 = 0, because
X^{(1)} = tr[X] . 1/d is Z-invariant and Lemma foundations/lem:pinchmono's equality case
applies.

PART (ii), the K chain. TOY-1 has P_chat0(omega) = tr omega = 1 for every
feasible omega and f_{chat0,s1} == 0 identically (s1 is key-inert, C7), so
  K_chat0 = 1 + f  and  K^{(delta,Ret)}_chat0 = 1 + f^{(delta)}
with Ret = {(chat0, s0)}. Both are in [0, 1] and K <= K^{(delta,Ret)} follows
termwise from part (i). Frozen in MIX_DOMINATION_K_TABLE.
THE RETAINED SET DOES NOT MOVE THE NUMBER HERE, and the reason is worth
recording: f^{(delta)}_{chat0,s1} = 0 as well. s1's branch operator
w1 |psi><psi| lies inside ONE R block, so it is already Z-invariant; the mixing
map preserves that (it adds a multiple of the identity), so the perturbed
deficit is zero too. Perturbing a key-inert sector cannot create a deficit.

PART (iii), the objective. TOY-1's acceptance set is the singleton
q = delta_chat0 = Phi[omega], so the divergence term vanishes and
  O_alpha = (1/(alpha-1)) log2(1/K) ,
  O^{(delta,Ret)}_alpha = (1/(alpha-1)) log2(1/K^{(delta,Ret)}) .
Since K <= K^{(delta,Ret)} and the kernel d is NON-INCREASING in its second
argument (Lemma foundations/lem:kernel), O^{(delta,Ret)} <= O_alpha pointwise. At
alpha = 1.5 that is 0.22193783525433586 <= 1.0.

THE UNPERTURBED OBJECTIVE IS 1.0 BIT AT EVERY ALPHA, and that is a closed-form
consequence rather than a computed coincidence: K = 1 + f = 2^{1-alpha}, so
log2(1/K) = alpha - 1 EXACTLY and the (1/(alpha-1)) prefactor cancels it. The
same 1.0 is pinned independently, on the same declaration at the same point, by
O_HLOW_RETENTION_DROPPED above -- two derivations that share no arithmetic.
The perturbed column has no such collapse and is computed from the frozen
K^{(delta,Ret)} column of MIX_DOMINATION_K_TABLE by the displayed formula; it
agrees BIT FOR BIT with the independent route through the closed form
_f_delta_toy1_s0, i.e. log2(1/(1 + f^{(delta)}))/(alpha - 1), at all five alpha.

REPAIRED (finding F-03-06). Until then the two numeric
columns of MIX_DOMINATION_OBJECTIVE carried log2(1/K) and log2(1/K^{(delta,Ret)})
-- the displayed formula with its (1/(alpha-1)) factor DROPPED -- under column
headings naming the objective. Nothing that consumed the entry was wrong,
because both tests asserted only the ORDERING and a common positive factor
cannot reorder; but the entry pinned no objective VALUE while reading as though
it did, so the coverage it appeared to give C18(iii) was weaker than it looked.
The freeze rule is what licenses this edit and also what
constrains it: "an expected value that turns out to be wrong is a finding,
reported and corrected deliberately with its derivation -- never edited in
passing to make a test go green". The repaired numbers are a transform of an
already-frozen column by a factor this derivation itself states; no value here
was read off the implementation.
THE DIRECTION IS THE WHOLE POINT: the perturbation LOWERS the certified value
and can never raise it, so delta prices TIGHTNESS ONLY and the soundness
penalty is zero (contract Section 1.1, design decision 6(a); Remark
rem:cert-tightness). An implementation whose perturbed objective came out
ABOVE the unperturbed one would be unsound in the unsafe direction, and this
entry is what catches it.
""",
    toy_id="TOY-1",
    closed_form=_f_delta_toy1_s0,
    frozen_values=(
        (1.05, -0.010131733419257438),
        (1.25, -0.04363388041771443),
        (1.5, -0.07403402806638071),
        (1.75, -0.09615337136376478),
        (1.9, -0.10669564858534841),
    ),
)

#: ``(alpha, f, (1 - delta) f, f^(delta))`` at delta = 1/2, w0 = 1, on TOY-1's
#: pair (chat0, s0). The three columns are the chain of lem:mix-dom (i), which
#: must be non-decreasing left to right and end at a non-positive number.
MIX_DOMINATION_CHAIN: tuple[tuple[float, float, float, float], ...] = (
    (1.05, -0.03406367107515451, -0.017031835537577256, -0.010131733419257438),
    (1.25, -0.1591035847462855, -0.07955179237314275, -0.04363388041771443),
    (1.5, -0.2928932188134524, -0.1464466094067262, -0.07403402806638071),
    (1.75, -0.4053964424986395, -0.20269822124931974, -0.09615337136376478),
    (1.9, -0.46411326873185343, -0.23205663436592672, -0.10669564858534841),
)

#: ``(alpha, K_chat0, K^(delta,Ret)_chat0)`` on the same point, lem:mix-dom (ii).
MIX_DOMINATION_K_TABLE: tuple[tuple[float, float, float], ...] = (
    (1.05, 0.9659363289248455, 0.9898682665807426),
    (1.25, 0.8408964152537145, 0.9563661195822856),
    (1.5, 0.7071067811865476, 0.9259659719336193),
    (1.75, 0.5946035575013605, 0.9038466286362352),
    (1.9, 0.5358867312681466, 0.8933043514146516),
)

#: ``(alpha, O_alpha, O^(delta,Ret)_alpha)`` on the same point,
#: lem:mix-dom (iii). The right column must not exceed the left.
#:
#: Both columns carry the ``1/(alpha - 1)`` prefactor of the objective, which
#: they lacked before the F-03-06 repair; see the entry's
#: derivation. ``O_alpha`` is the EXACT value ``1.0`` -- ``log2(1/K)`` is
#: ``alpha - 1`` in closed form, so the prefactor cancels -- and is written as
#: such rather than as whichever float a particular evaluation order lands on
#: (the three routes checked span 1.0 to 1.0000000000000013, i.e. 2 ulp).
MIX_DOMINATION_OBJECTIVE: tuple[tuple[float, float, float], ...] = (
    (1.05, 1.0, 0.2938310665546763),
    (1.25, 1.0, 0.25746029254413433),
    (1.5, 1.0, 0.22193783525433586),
    (1.75, 1.0, 0.19446681148857717),
    (1.9, 1.0, 0.18086256150413604),
)

#: The same chain at a SECOND perturbation weight, delta = 1/4, so that no
#: value can pass by hard-coding delta: ``(alpha, f^(delta))``. Smaller delta
#: means a tighter (more negative, closer to f) perturbed deficit.
MIX_DOMINATION_DELTA_QUARTER: tuple[tuple[float, float], ...] = (
    (1.05, -0.0199409886171541),
    (1.25, -0.08778846740177393),
    (1.5, -0.1515642930034673),
    (1.75, -0.19894504916871458),
    (1.9, -0.22171314110918583),
)

O_SPECTRAL_WINDOW = OracleEntry(
    oracle_id="O-SPECTRAL-WINDOW",
    claims=("C18",),
    kind="structural-identity",
    subject=(
        "Lemma lem:window (i) and (ii) on TOY-1's key-active branch at "
        "w0 = 1, delta = 1/2, d = 6: spec(X^(delta)) subset [delta c/d, 1] "
        "and spec(Y) subset [(delta c/d)^p, 1], with the LOWER endpoint "
        "attained in both."
    ),
    derivation="""\
contract.tex Lemma lem:window, on the branch diagonalized in the block above
O-MIX-DOMINATION. With c = tr X_{chat0,s0}(omega_s0) = w0 = 1, delta = 1/2 and
d_{chat0,s0} = 6:

PART (i). spec(X^{(delta)}) = { (1 - delta) + delta/6 , delta/6 (five times) }
  = { 7/12 = 0.5833333333333334 , 1/12 = 0.08333333333333333 (x5) } ,
and the lemma's window is [delta c / d, 1] = [1/12, 1]. The LOWER endpoint is
ATTAINED exactly -- the five directions orthogonal to |eta> carry precisely
delta tr[X]/d -- so the window is tight at the bottom and cannot be shrunk.
The upper end is loose here (7/12 < 1) because the lemma bounds
||X^{(delta)}|| <= (1-delta) c + delta c/d <= c <= 1 through the trace, which
is the only bound available without knowing the branch.
In particular X^{(delta)} > 0 STRICTLY on the ambient branch space, which is
the property the whole certificate rests on: Lemma lem:window (iii) then gives
two-sided differentiability with NO face rule of Theorem thm:gradient (i)-(ii)
invoked anywhere on the certified path.

PART (ii). Y = Z((X^{(delta)})^p) has spectrum { (A+B)/2 twice, B four times }
with A = (7/12)^p and B = (1/12)^p, and the lemma's window is
[(delta c/d)^p, 1] = [(1/12)^p, 1] = [B, 1]. The lower endpoint is again
ATTAINED, on the four directions the pinching leaves untouched. At
alpha = 1.5 (p = 2/3) that is B = 0.19078570709222198 with top
0.44446446722278005; at alpha = 2 (p = 1/2), B = 0.28867513459481287 with top
0.5262188752103931. Frozen in SPECTRAL_WINDOW_TABLE.
The proof of (ii) needs the pinching to be UNITAL and POSITIVE (so M >= m 1
implies Z(M) >= m 1) and a norm bound ||Z(M)|| <= ||M||; neither needs
Z-invariance of the branch, which TOY-1's s0 does not have.

WHY THE WINDOW IS THE LOAD-BEARING OUTPUT. Proposition prop:budget consumes
c_{chat,s} = delta t_low / d as the lower end of the certified window and then
uses it twice: as the argument window of the Lemma lem:series truncations for
the exponents p, alpha - 1 and alpha, and as the source of the Lipschitz
constant L_f = p c^{p-1} of lem:transfer (iii). A window whose lower end is
computed too large would understate BOTH, in the unsafe direction; this entry
freezes the exact endpoint so that cannot pass unnoticed.
""",
    toy_id="TOY-1",
)

#: ``(alpha, min spec Y, max spec Y, window lower end (delta c/d)^p)`` at
#: delta = 1/2, w0 = 1, d = 6 on TOY-1's pair (chat0, s0). The minimum and the
#: window's lower end are EQUAL: the endpoint is attained.
SPECTRAL_WINDOW_TABLE: tuple[tuple[float, float, float, float], ...] = (
    (1.05, 0.09380118763437251, 0.3461502207383477, 0.09380118763437251),
    (1.25, 0.13697931912643546, 0.39335504498905743, 0.13697931912643546),
    (1.5, 0.19078570709222198, 0.44446446722278005, 0.19078570709222198),
    (1.75, 0.24172691098649263, 0.4883218492599868, 0.24172691098649263),
    (1.9, 0.2704019819478004, 0.5117038833994112, 0.2704019819478004),
)

#: ``spec(X^(delta))`` at delta = 1/2, w0 = 1, d = 6, with multiplicities, and
#: the window [delta c/d, 1] of lem:window (i). Alpha-independent.
SPECTRAL_WINDOW_X_DELTA: tuple[tuple[float, int], ...] = (
    (0.5833333333333334, 1),
    (0.08333333333333333, 5),
)
SPECTRAL_WINDOW_X_BOUNDS: tuple[float, float] = (0.08333333333333333, 1.0)


# ---------------------------------------------------------------------------
#  C19 -- weak duality for the linear subproblem, both source modes.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WeakDualityCase:
    """One hand-authored dual witness for Theorem ``thm:weak-duality``."""

    case_id: str
    toy_id: str
    #: "trusted" or "untrusted" -- which part of the theorem applies.
    mode: str
    #: ``mu(G)`` of Eq. eq:linsub, the true minimum, derived by hand.
    mu: float
    #: The bound Eq. eq:betafeas-tr / eq:betafeas-un returns for this witness.
    bound: float
    #: Whether every slack block is PSD, i.e. whether the theorem APPLIES.
    slack_psd: bool
    #: Whether ``bound <= mu``. FALSE is the fail-closed content: it can only
    #: happen when ``slack_psd`` is False.
    sound: bool
    witness: str


WEAK_DUALITY_CASES: tuple[WeakDualityCase, ...] = (
    # -- TOY-8-T: trusted, d_A = 2, m = 0, Feas a single point. -------------
    WeakDualityCase(
        case_id="WD-T8T-tight",
        toy_id="TOY-8-T",
        mode="trusted",
        mu=1.625,
        bound=1.625,
        slack_psd=True,
        sound=True,
        witness="""\
TOY-8-T is trusted-source mode at d_A = 2 with one one-dimensional sector, so
omega is a 2 x 2 operator on A and the marginal condition omega_A = tau_A
= diag(7/8, 1/8) pins it: Feas = { diag(7/8, 1/8) }, a SINGLE POINT. Hence
  mu(G) = tr[G tau_A] exactly, for every G.
Surrogate G = diag(2, -1) (exact machine data), so
  mu(G) = 2 . 7/8 + (-1) . 1/8 = 14/8 - 1/8 = 13/8 = 1.625 .
WITNESS, Theorem thm:weak-duality (i) with m = 0 (no Lambda_k at all):
  y_0 = 0 ,  Upsilon = G = diag(2, -1) ,
  Slack = G - y_0 1 - Upsilon x 1_{Q_s} = 0 ,  PSD (trivially) ,
  bound = y_0 + tr[Upsilon tau_A] = 0 + 13/8 = 13/8 .
TIGHT: the bound equals mu(G). This is what the trusted branch's MARGINAL dual
Upsilon buys -- it is a full Hermitian operator on A, and here it absorbs G
exactly, which no scalar could do.""",
    ),
    WeakDualityCase(
        case_id="WD-T8T-suboptimal",
        toy_id="TOY-8-T",
        mode="trusted",
        mu=1.625,
        bound=0.75,
        slack_psd=True,
        sound=True,
        witness="""\
The same toy and the same G = diag(2, -1), with a DELIBERATELY POOR witness:
  y_0 = -1 ,  Upsilon = diag(2, 0) ,
  Slack = diag(2, -1) + 1 . diag(1, 1) - diag(2, 0) = diag(1, 0) ,  PSD ,
  bound = -1 + tr[diag(2,0) diag(7/8, 1/8)] = -1 + 7/4 = 3/4 = 0.75 .
Sound (0.75 <= 1.625) and loose. This freezes the theorem's own sentence
"ANY admissible dual choice certifies; no constraint qualification, attainment
or strong-duality statement is made or needed", and Remark rem:dual-exact's
"a corrupted or suboptimal dual witness can only LOWER the certified bound,
never invalidate it". An implementation that rejected this witness for being
suboptimal would be rejecting a valid certificate.""",
    ),
    WeakDualityCase(
        case_id="WD-T8T-slack-not-psd",
        toy_id="TOY-8-T",
        mode="trusted",
        mu=1.625,
        bound=1.75,
        slack_psd=False,
        sound=False,
        witness="""\
FAIL-CLOSED. The same toy and G, with a witness whose slack is NOT PSD:
  y_0 = 0 ,  Upsilon = diag(2, 0) ,
  Slack = diag(2, -1) - diag(2, 0) = diag(0, -1) ,
whose spectrum is {0, -1}: NOT PSD, so Theorem thm:weak-duality does not
apply. Evaluating Eq. eq:betafeas-tr anyway returns
  0 + tr[diag(2,0) diag(7/8,1/8)] = 7/4 = 1.75 ,
which EXCEEDS the true minimum 13/8 = 1.625 by exactly 1/8. Feeding that
number to Eq. eq:hcert as beta_feas would produce an h_cert that is NOT a
lower bound on h_low -- an unsound `certified` label, in the unsafe direction.
THE SLACK PSD CHECK IS WHAT PREVENTS IT, and Remark rem:dual-exact requires it
be decided EXACTLY: "the reference verification is an exact rational
LDL^T/Cholesky factorization (a finite exact algorithm)". A floating-point
eigenvalue that came out as -1e-17 and was rounded to zero would readmit this
witness.""",
    ),
    # -- TOY-8-UN: untrusted, d_A = 2, m = 0, Feas the whole state set. -----
    WeakDualityCase(
        case_id="WD-T8UN-tight",
        toy_id="TOY-8-UN",
        mode="untrusted",
        mu=-1.0,
        bound=-1.0,
        slack_psd=True,
        sound=True,
        witness="""\
TOY-8-UN is the same declaration with the marginal slot emptied, so Eq.
eq:feas-modes leaves only tr omega = 1 and Feas is the WHOLE set of density
matrices on C^2. Then, for the same G = diag(2, -1),
  mu(G) = min_{tr omega = 1, omega >= 0} tr[G omega] = lambda_min(G) = -1 ,
attained at the eigenprojector of the smaller eigenvalue.
WITNESS, Theorem thm:weak-duality (ii) with m = 0:
  y_0 = -1 ,  Slack = G - y_0 1 = diag(3, 0) ,  PSD ,
  bound = y_0 = -1 .
TIGHT, and the theorem's untrusted branch reduces here to the elementary fact
that y_0 <= lambda_min(G) is exactly the condition G - y_0 1 >= 0.
THE PAIR IS THE POINT. The trusted bound on this declaration is 13/8 and the
untrusted bound is -1: the untrusted feasible set is strictly larger, so its
minimum is smaller, and dropping the marginal is the CONSERVATIVE direction
(Remark rem:source-mode (a)). A certificate that used the trusted formula on
an untrusted declaration would overstate beta_feas by 21/8 here.""",
    ),
    WeakDualityCase(
        case_id="WD-T8UN-suboptimal",
        toy_id="TOY-8-UN",
        mode="untrusted",
        mu=-1.0,
        bound=-2.0,
        slack_psd=True,
        sound=True,
        witness="""\
y_0 = -2, Slack = diag(4, 1), PSD, bound -2 <= -1. Sound and loose, the
untrusted counterpart of WD-T8T-suboptimal.""",
    ),
    WeakDualityCase(
        case_id="WD-T8UN-slack-not-psd",
        toy_id="TOY-8-UN",
        mode="untrusted",
        mu=-1.0,
        bound=0.0,
        slack_psd=False,
        sound=False,
        witness="""\
FAIL-CLOSED, untrusted mode. y_0 = 0 gives Slack = diag(2, -1), NOT PSD, and
the formula would return the bound 0 -- which exceeds the true minimum -1 by a
whole unit. As in WD-T8T-slack-not-psd, only the PSD check stands between this
witness and an unsound certificate.""",
    ),
    # -- TOY-5 / TOY-5-UN: the succeq relation, in both modes. --------------
    WeakDualityCase(
        case_id="WD-T5-succeq-tight",
        toy_id="TOY-5",
        mode="trusted",
        mu=1.0,
        bound=1.0,
        slack_psd=True,
        sound=True,
        witness="""\
TOY-5 is trusted-source mode at d_A = 1 with two one-dimensional sectors and
ONE constraint of relation SUCCEQ: (Pi_s0, succeq, Theta_1 = (1/2) tau_A), so
  Feas = { diag(w0, 1 - w0) : w0 in [1/2, 1] } .
Surrogate G = (G_s0, G_s1) = (2, 0) (1 x 1 blocks), chosen so the constraint
is ACTIVE at the optimum:
  sum_s tr[G_s omega_s] = 2 w0 , minimized at w0 = 1/2 , so mu(G) = 1 .
WITNESS, Theorem thm:weak-duality (i) at d_A = 1, where Upsilon = [u] is a
scalar and only the sum t = y_0 + u appears:
  y_0 = 0 , u = 0 , Lambda_1 = [2] (>= 0, as SUCCEQ requires) ,
  Slack_s0 = 2 - 0 - 0 - 2 . 1 = 0 ,   Slack_s1 = 0 - 0 - 0 - 2 . 0 = 0 ,
both PSD, and
  bound = y_0 + tr[Upsilon tau_A] + tr[Lambda_1 Theta_1] = 0 + 0 + 2 . (1/2)
        = 1 .
TIGHT, with the SUCCEQ dual genuinely active (Lambda_1 = 2 > 0). Note the SIGN:
Eq. eq:slack-tr SUBTRACTS Lambda_k O_k for k in the succeq/eq groups and Eq.
eq:betafeas-tr ADDS tr[Lambda_k Theta_k] for the same groups. Swapping the two
groups' signs would return -1 here, a valid-looking but wrong number.""",
    ),
    WeakDualityCase(
        case_id="WD-T5-succeq-suboptimal",
        toy_id="TOY-5",
        mode="trusted",
        mu=1.0,
        bound=-0.5,
        slack_psd=True,
        sound=True,
        witness="""\
t = y_0 + u = -1 with Lambda_1 = [1]: Slack = (2 + 1 - 1, 0 + 1) = (2, 1),
both PSD, bound = -1 + 1 . (1/2) = -0.5 <= 1. Sound and loose.""",
    ),
    WeakDualityCase(
        case_id="WD-T5-succeq-slack-not-psd",
        toy_id="TOY-5",
        mode="trusted",
        mu=1.0,
        bound=1.5,
        slack_psd=False,
        sound=False,
        witness="""\
FAIL-CLOSED. t = y_0 + u = 1/2 with Lambda_1 = [2]:
  Slack_s0 = 2 - 1/2 - 2 = -1/2 ,  Slack_s1 = 0 - 1/2 = -1/2 ,
both NEGATIVE, and the formula would return 1/2 + 2 . (1/2) = 3/2 = 1.5 > 1.
Unsound by 1/2. Every sector block must be checked: here BOTH fail, but a
witness failing on one block only would be equally inadmissible, and an
implementation that checked the first block and stopped would admit it.""",
    ),
    WeakDualityCase(
        case_id="WD-T5UN-succeq-tight",
        toy_id="TOY-5-UN",
        mode="untrusted",
        mu=1.0,
        bound=1.0,
        slack_psd=True,
        sound=True,
        witness="""\
TOY-5-UN is TOY-5 with the marginal slot emptied and the right-hand side
retyped as the real scalar c_1 = 1/2. At d_A = 1 the feasible set is the same
segment w0 in [1/2, 1], so mu(G) = 1 for the same G = (2, 0).
WITNESS, Theorem thm:weak-duality (ii): y_0 = 0, lambda_1 = 2 (>= 0),
  Slack_s0 = 2 - 0 - 2 . 1 = 0 ,  Slack_s1 = 0 - 0 = 0 ,  both PSD ,
  bound = y_0 + lambda_1 c_1 = 0 + 2 . (1/2) = 1 .
IDENTICAL to WD-T5-succeq-tight through the OTHER formula. That is the
theorem's closing sentence made checkable: "At d_A = 1 in trusted-source mode,
Upsilon = [u] is a scalar merging with y_0 and (i) reduces to (ii) with
Theta_k = c_k tau_A = c_k". The two modes are different equations and the same
number.""",
    ),
    # -- TOY-7: the preceq relation with a genuinely MATRIX dual. -----------
    WeakDualityCase(
        case_id="WD-T7-preceq-tight",
        toy_id="TOY-7",
        mode="trusted",
        mu=0.5,
        bound=0.5,
        slack_psd=True,
        sound=True,
        witness="""\
TOY-7 is trusted-source mode at d_A = 2 with tau_A = 1/2 and one
one-dimensional sector, and ONE constraint of relation PRECEQ:
(O_1 = [1], preceq, Theta_1 = diag(1, 1/2)). The marginal condition alone pins
Feas = { 1/2 } (the constraint is satisfied there and adds nothing), so
  mu(G) = tr[G . 1/2] = (G_11 + G_22)/2 .
Surrogate G = [[1, 1/2], [1/2, 0]] (Hermitian, exact), so mu(G) = 1/2.
WITNESS with Lambda_1 = 0: y_0 = 0, Upsilon = G, Slack = 0, PSD,
  bound = 0 + tr[G . 1/2] - tr[0 . Theta_1] = 1/2 . TIGHT.""",
    ),
    WeakDualityCase(
        case_id="WD-T7-preceq-lambda-active",
        toy_id="TOY-7",
        mode="trusted",
        mu=0.5,
        bound=0.0,
        slack_psd=True,
        sound=True,
        witness="""\
The same toy with the PRECEQ dual switched on, so that its sign is pinned:
  y_0 = 0 , Lambda_1 = diag(1, 0) (>= 0, as PRECEQ requires) ,
  Upsilon = G + Lambda_1 = [[2, 1/2], [1/2, 0]] ,
  Slack = G - Upsilon + Lambda_1 x O_1 = G - (G + Lambda_1) + Lambda_1 = 0 ,
  PSD, and
  bound = tr[Upsilon tau_A] - tr[Lambda_1 Theta_1] = (2 + 0)/2 - 1 = 0 .
Sound (0 <= 1/2) and loose. Eq. eq:slack-tr ADDS Lambda_k O_k for k in the
PRECEQ group and Eq. eq:betafeas-tr SUBTRACTS tr[Lambda_k Theta_k] for it --
the opposite of the succeq group in both places. This case and
WD-T5-succeq-tight together pin that opposition; a single sign convention
applied to both groups gets one of them wrong.
Lambda_1 is a genuine 2 x 2 MATRIX dual here, which no d_A = 1 toy can
exercise, and its PSD-ness is a second, independent PSD check the theorem
imposes -- on the dual variable, not on the slack.""",
    ),
    # -- CERT-TOY-3REL: all three relation symbols at once, both modes. -----
    WeakDualityCase(
        case_id="WD-3REL-UN-tight",
        toy_id="CERT-TOY-3REL-UN",
        mode="untrusted",
        mu=0.125,
        bound=0.125,
        slack_psd=True,
        sound=True,
        witness="""\
CERT-TOY-3REL-UN carries ONE CONSTRAINT OF EACH RELATION SYMBOL:
  k = 1 (Pi_s0, succeq, c_1 = 1/4) , k = 2 (Pi_s1, preceq, c_2 = 1/2) ,
  k = 3 (Pi_s2, eq, c_3 = 1/8) ,
so Feas = { diag(7/8 - w1, w1, 1/8) : w1 in [0, 1/2] } and, with the surrogate
G = (1, -1, 2),
  sum_s tr[G_s omega_s] = 9/8 - 2 w1 ,  mu(G) = 1/8 at w1 = 1/2 .
WITNESS, Theorem thm:weak-duality (ii), lambda_1, lambda_2 >= 0 and lambda_3
UNRESTRICTED IN SIGN because k = 3 is an EQUALITY:
  y_0 = 1 , lambda = (0, 2, 1) ,
  Slack_s0 = 1 - 1 - 0        = 0 ,
  Slack_s1 = -1 - 1 + 2       = 0 ,
  Slack_s2 = 2 - 1 - 1        = 0 ,   all PSD ,
  bound = y_0 + lambda_1 c_1 - lambda_2 c_2 + lambda_3 c_3
        = 1 + 0 - 1 + 1/8 = 1/8 .
TIGHT, with all three groups present and each contributing its own sign. Note
lambda_1 = 0: the succeq entry w0 >= 1/4 is INACTIVE on this feasible set (it
is implied by w1 <= 1/2), and a witness is free to ignore an inactive
constraint entirely -- there is no complementary-slackness obligation, because
no strong duality is claimed.""",
    ),
    WeakDualityCase(
        case_id="WD-3REL-UN-equality-dual-negative",
        toy_id="CERT-TOY-3REL-UN",
        mode="untrusted",
        mu=0.125,
        bound=-0.125,
        slack_psd=True,
        sound=True,
        witness="""\
The SIGN-FREEDOM of the equality dual, pinned. Same toy and G, with
  y_0 = 1 , lambda = (0, 2, -1) :
  Slack_s0 = 0 , Slack_s1 = 0 , Slack_s2 = 2 - 1 + 1 = 2 ,  all PSD ,
  bound = 1 + 0 - 1 + (-1)(1/8) = -1/8 .
Sound (-1/8 <= 1/8) and looser than the lambda_3 = +1 witness. Theorem
thm:weak-duality admits lambda_k of EITHER sign for k in the equality group,
and its proof says why: for an equality constraint
tr[Lambda_k A_k(omega)] = tr[Lambda_k Theta_k] holds exactly, for either sign
of Lambda_k, so no inequality is used and no sign restriction is needed. An
implementation that clamped lambda_3 at zero would reject a valid witness; one
that clamped it at zero and reported the CLAMPED bound would still be sound,
but would lose tightness for no reason.""",
    ),
    WeakDualityCase(
        case_id="WD-3REL-UN-suboptimal",
        toy_id="CERT-TOY-3REL-UN",
        mode="untrusted",
        mu=0.125,
        bound=-0.875,
        slack_psd=True,
        sound=True,
        witness="""\
y_0 = 0, lambda = (0, 2, 1): slacks (1, 1, 1), all strictly PSD, bound
0 + 0 - 1 + 1/8 = -7/8 <= 1/8. Sound and loose.""",
    ),
    WeakDualityCase(
        case_id="WD-3REL-UN-slack-not-psd",
        toy_id="CERT-TOY-3REL-UN",
        mode="untrusted",
        mu=0.125,
        bound=1.125,
        slack_psd=False,
        sound=False,
        witness="""\
FAIL-CLOSED, with all three relation symbols in play. y_0 = 2, lambda =
(0, 2, 1): slacks (-1, -1, -1), all NEGATIVE, and the formula would return
2 + 0 - 1 + 1/8 = 9/8 = 1.125 > 1/8. Unsound by a whole unit.""",
    ),
    WeakDualityCase(
        case_id="WD-3REL-T-tight",
        toy_id="CERT-TOY-3REL-T",
        mode="trusted",
        mu=0.125,
        bound=0.125,
        slack_psd=True,
        sound=True,
        witness="""\
The TRUSTED twin, through Theorem thm:weak-duality (i). At d_A = 1 the duals
are Upsilon = [u] and Lambda_k = [lambda_k], the right-hand sides are the
operators Theta_k = c_k tau_A = [c_k], and only the sum t = y_0 + u appears:
  Slack_s0 = 1 - t - lambda_1 , Slack_s1 = -1 - t + lambda_2 ,
  Slack_s2 = 2 - t - lambda_3 ,
  bound = y_0 + tr[Upsilon tau_A] + lambda_1 c_1 - lambda_2 c_2 + lambda_3 c_3
        = t + lambda_1/4 - lambda_2/2 + lambda_3/8 .
WITNESS: y_0 = 0, u = 1 (so t = 1), lambda = (0, 2, 1). Slacks (0, 0, 0), all
PSD, bound = 1 + 0 - 1 + 1/8 = 1/8 = mu(G). TIGHT, and EQUAL to the untrusted
twin's bound WD-3REL-UN-tight through the other formula -- the same d_A = 1
mode reduction that WD-T5UN-succeq-tight pins on a one-relation toy, now with
all three relation symbols and with the marginal dual Upsilon carrying the
weight that y_0 carries in the untrusted twin.""",
    ),
)

O_WEAK_DUALITY = OracleEntry(
    oracle_id="O-WEAK-DUALITY",
    claims=("C19",),
    kind="toy-instance",
    subject=(
        "beta_feas from Theorem thm:weak-duality on five toy declarations in "
        "BOTH source modes, with hand-authored dual witnesses covering all "
        "three relation symbols, a matrix-valued Lambda_k, the sign-free "
        "equality dual, and three witnesses whose slack is NOT PSD and whose "
        "bound is consequently UNSOUND."
    ),
    derivation="""\
contract.tex Theorem thm:weak-duality (C19), Eqs. eq:slack-tr / eq:betafeas-tr
(trusted-source mode) and eq:slack-un / eq:betafeas-un (untrusted-source mode),
bounding the linear subproblem
  mu(G) = min_{omega in Feas} sum_s tr[G_s omega_s]           (Eq. eq:linsub)
that Theorem thm:cert hypothesis (c) consumes as beta_feas.

EVERY mu(G) BELOW IS DERIVED BY HAND FROM THE FEASIBLE SET, never from a
solver: three of the five feasible sets are single points (TOY-8-T, TOY-7),
one is the whole state set of C^2 where the minimum is lambda_min(G) by the
variational characterization, and two are one-dimensional segments where a
linear function is minimized at an endpoint. Each case's witness string
carries the argument.

COVERAGE, deliberately complete against the theorem's own case split:
  mode        trusted   : WD-T8T-*, WD-T5-*, WD-T7-*, WD-3REL-T-tight
  mode        untrusted : WD-T8UN-*, WD-T5UN-*, WD-3REL-UN-*
  relation    succeq    : WD-T5-*, WD-T5UN-*, WD-3REL-*
  relation    preceq    : WD-T7-*, WD-3REL-*
  relation    eq        : WD-3REL-* (the only ones; no 0.3.0 toy carries it)
  m = 0                 : WD-T8T-*, WD-T8UN-*
  Upsilon a MATRIX      : WD-T8T-*, WD-T7-*
  Lambda_k a MATRIX     : WD-T7-preceq-lambda-active
  Lambda_k SIGN-FREE    : WD-3REL-UN-equality-dual-negative
  d_A = 1 mode identity : WD-T5-succeq-tight = WD-T5UN-succeq-tight = 1 ,
                          WD-3REL-T-tight = WD-3REL-UN-tight = 1/8
  NOT PSD, UNSOUND      : WD-T8T-slack-not-psd, WD-T8UN-slack-not-psd,
                          WD-T5-succeq-slack-not-psd, WD-3REL-UN-slack-not-psd

THE THREE SIGN CONVENTIONS, which is where an implementation most easily goes
wrong. In Eq. eq:slack-tr the PRECEQ group enters the slack with a PLUS and
the SUCCEQ and EQ groups with a MINUS; in Eq. eq:betafeas-tr the PRECEQ group
enters the bound with a MINUS and the other two with a PLUS. The pair
WD-T5-succeq-tight / WD-T7-preceq-lambda-active pins the opposition, and
WD-3REL-* pins all three at once in one declaration.

WHAT IS DELIBERATELY NOT CLAIMED. No strong duality, no attainment, no
constraint qualification and no complementary slackness: the theorem states
only that ANY admissible witness certifies, and WD-3REL-UN-tight exhibits a
tight witness that ignores an inactive constraint entirely. Remark
rem:dual-exact adds that the whole chain is EXACT rational arithmetic on
declared machine data -- "the weak-duality chain itself carries NO
floating-point error term" -- so beta_feas contributes no width to
Eq. eq:hcert, and the only inexactness on the feasible side is the surrogate's
distance from the true gradient, which eps_feas covers.
""",
)


@dataclass(frozen=True)
class AcceptanceSideCase:
    """One frozen beta_acc from Remark ``rem:acc-side``."""

    case_id: str
    #: "singleton" (instantiation (a)) or "polytope" (instantiation (b)).
    instantiation: str
    #: The true minimum of ``<g, q'>`` over the acceptance set, by hand.
    minimum: float
    #: The value the remark's recipe returns for this witness.
    beta_acc: float
    #: Whether the witness satisfies the remark's admissibility condition.
    admissible: bool
    #: Whether ``beta_acc <= minimum``. FALSE only when ``admissible`` is False.
    sound: bool
    arithmetic: str


ACCEPTANCE_SIDE_CASES: tuple[AcceptanceSideCase, ...] = (
    AcceptanceSideCase(
        case_id="ACC-A-singleton",
        instantiation="singleton",
        minimum=0.5,
        beta_acc=0.5,
        admissible=True,
        sound=True,
        arithmetic="""\
Instantiation (a) of Remark rem:acc-side, "the currently implemented class":
AcceptSet = {q*} is a singleton, so the minimum over it is the single value and
beta_acc is "any downward-rounded evaluation of sum_chat g(chat) q*(chat)".
  Chat_acc = {chat0, chat1} , g = (2, -1) , q* = (1/2, 1/2) ,
  <g, q*> = (1/2)(2) + (1/2)(-1) = 1/2 .
Every number is a dyadic rational, so the downward rounding is a no-op and
beta_acc = 1/2 EXACTLY -- deliberately, so that the case pins the formula and
not a rounding mode. The rounding direction is pinned separately by
ACC-A-singleton-rounded below.""",
    ),
    AcceptanceSideCase(
        case_id="ACC-A-singleton-rounded",
        instantiation="singleton",
        minimum=6.09375,
        beta_acc=6.09375,
        admissible=True,
        sound=True,
        arithmetic="""\
The singleton beta_acc actually consumed by the end-to-end case CERT-T8T-a15:
  Chat_acc = {chat0, chat1} , q* = (1/2, 1/2) (TOY-8-T's acceptance set) ,
  surrogate g~ = (15/8, 165/16) (exact machine data) ,
  <g~, q*> = (1/2)(15/8) + (1/2)(165/16) = 15/16 + 165/32 = 195/32 = 6.09375 .
Again exactly representable, so beta_acc = 195/32. THE ROUNDING DIRECTION IS
STILL LOAD-BEARING and the contract fixes it in Section 2.5
(certificate_arithmetic): "every final combination in Eq. eq:hcert is rounded
DOWNWARD". beta_acc enters eq:hcert with a PLUS sign, so rounding it upward
would raise h_cert -- in the unsafe direction. eps_acc and eps_feas enter with
a MINUS, so THEY must be rounded upward for the same reason; the four
directions are not the same and cannot be implemented by one rounding mode.""",
    ),
    AcceptanceSideCase(
        case_id="ACC-B-polytope-tight",
        instantiation="polytope",
        minimum=0.5,
        beta_acc=0.5,
        admissible=True,
        sound=True,
        arithmetic="""\
Instantiation (b) of Remark rem:acc-side: AcceptSet = {q >= 0, sum q = 1,
B q <= b}. Hand-chosen:
  Chat_acc = {c0, c1, c2} , g = (0, 1, 4) ,
  B = [[1, 0, 0]] (one row) , b = (1/2) , i.e. the single cut q(c0) <= 1/2 .
TRUE MINIMUM, by hand: g is minimized by putting mass on the smallest
coefficient first. g(c0) = 0 is smallest but capped at 1/2; the next is
g(c1) = 1, which takes the remaining 1/2. So q = (1/2, 1/2, 0) and
  min <g, q> = 0 . (1/2) + 1 . (1/2) = 1/2 .
WITNESS, the remark's own recipe: any u >= 0 and v in R with
g(chat) + (B^T u)(chat) + v >= 0 for every chat gives
min <g, q'> >= -<b, u> - v. Take u = 1, v = -1:
  g + B^T u + v . 1 = (0 + 1 - 1, 1 + 0 - 1, 4 + 0 - 1) = (0, 0, 3) >= 0 ,
  beta_acc = -<b, u> - v = -(1/2)(1) - (-1) = 1/2 .
TIGHT. The remark's three-line proof is checkable on these numbers:
  <g, q'> = <g + B^T u + v 1, q'> - <u, B q'> - v
          >= 0 - <u, b> - v = 1/2 ,
using q' >= 0 componentwise for the first term, u >= 0 with B q' <= b for the
second, and sum_chat q'(chat) = 1 for the third.""",
    ),
    AcceptanceSideCase(
        case_id="ACC-B-polytope-suboptimal",
        instantiation="polytope",
        minimum=0.5,
        beta_acc=0.0,
        admissible=True,
        sound=True,
        arithmetic="""\
u = 2, v = -1 on the same polytope: g + B^T u + v = (1, 0, 3) >= 0, so the
witness is admissible, and beta_acc = -(1/2)(2) + 1 = 0 <= 1/2. Sound and
loose -- the acceptance side has the same "any admissible witness certifies"
character as the feasible side.""",
    ),
    AcceptanceSideCase(
        case_id="ACC-B-polytope-condition-violated",
        instantiation="polytope",
        minimum=0.5,
        beta_acc=1.0,
        admissible=False,
        sound=False,
        arithmetic="""\
FAIL-CLOSED. u = 0, v = -1 on the same polytope:
  g + B^T u + v . 1 = (-1, 0, 3) ,
whose FIRST component is negative, so the remark's admissibility condition
"g(chat) + (B^T u)(chat) + v >= 0 for every chat in Chat_acc" FAILS. Evaluating
-<b, u> - v anyway returns 0 + 1 = 1, which EXCEEDS the true minimum 1/2 and
would make beta_acc too large -- h_cert too large, in the unsafe direction.
The condition is a componentwise nonnegativity check on an exactly represented
vector; there is no reason for an implementation to skip it and no way for it
to be expensive.""",
    ),
)

O_BETA_ACC = OracleEntry(
    oracle_id="O-BETA-ACC",
    claims=("C19",),
    kind="toy-instance",
    subject=(
        "beta_acc from Remark rem:acc-side in BOTH instantiations -- (a) the "
        "singleton acceptance set and (b) the polytope with its (u, v) "
        "witness -- with the true minima derived by hand, plus one witness "
        "violating the admissibility condition and returning an UNSOUND "
        "beta_acc."
    ),
    derivation="""\
contract.tex Remark rem:acc-side, Eq. eq:bacc-def: the certificate consumes a
number beta_acc with
  beta_acc <= min_{q' in AcceptSet} sum_{chat in Chat_acc} g(chat) q'(chat)
for a given exact vector g. Two instantiations "are part of this contract", and
the remark is explicit about what happens outside them: "a declaration whose
AcceptSet fits neither must supply its own certified bound or forgo
certification (fail-closed)". That third branch is pinned by
O-ACC-SIDE-UNSUPPORTED; this entry pins the two that are supported.

WHY beta_acc IS AN INPUT OBLIGATION RATHER THAN AN ALGORITHM, in the
contract's own words: "By Assumption A-ACC the minimal Chat_acc exists for
every admissible AcceptSet; whether it is COMPUTABLE is a property of the
declared representation". A-ACC asks only for a closed convex subset of the
simplex, which is not enough to minimize a linear functional over
mechanically. So the interface takes beta_acc as data and checks the
inequality it must satisfy -- for (a) by evaluation, for (b) by the
componentwise sign check on g + B^T u + v.

THE COORDINATE RESTRICTION, easy to miss. Instantiation (b) says: "identify
AcceptSet with a subset of R^{Chat_acc} (every q in AcceptSet is supported in
Chat_acc by Definition def:perturbed, so coordinates outside Chat_acc carry no
mass and may be omitted from B)". So B has |Chat_acc| columns, not |Chat|, and
the sum in eq:bacc-def runs over Chat_acc only. That is the same support
condition the certificate domain D imposes on the certificate point's own q~,
and O-CERT-DOMAIN-FAIL pins its violation.

The five cases are in ACCEPTANCE_SIDE_CASES.
""",
)


# ---------------------------------------------------------------------------
#  C13 -- the Euler identity, the end-to-end bound, and the certified length.
# ---------------------------------------------------------------------------
#
# THE POINT AND THE DECLARATION, shared by O-EULER-IDENTITY, O-HCERT-END-TO-END
# and O-CERT-KEY-LENGTH, written out once.
#
# TOY-8-T is trusted-source mode at d_A = 2 with ONE one-dimensional sector, no
# constraint list, Chat_key EMPTY, and the singleton acceptance set
# q* = (1/2, 1/2) on Chat = {chat0, chat1}. Its statistics operators are
# Gamma^{(s0)}_chat0 = diag(1, 0) and Gamma^{(s0)}_chat1 = diag(0, 1), so
#   P_chat0(omega) = omega_11 ,  P_chat1(omega) = omega_22 .
# The marginal condition pins Feas = { tau_A } = { diag(7/8, 1/8) }, and the
# frozen 0.3.0 oracle O-HLOW-DIVERGENCE-ONLY's sibling for this toy gives
#   h_low = (alpha/(alpha-1)) . (2 - (1/2) log2 7)
#         = (alpha/(alpha-1)) . 0.5963225389711979 ,
# derived there from D((1/2,1/2) || (7/8,1/8)) alone.
#
# BECAUSE Chat_key IS EMPTY the certificate simplifies in a way that makes the
# whole chain checkable on paper: Ret is empty (there are no key branches to
# retain), K^{(delta,Ret)} never appears, hypotheses (H3) and (H4) are VACUOUS,
# and Eq. eq:Owork reduces to
#   O^{(delta,Ret)}_alpha(q, omega) = (alpha/(alpha-1)) sum_chat d(q(chat),
#                                     P_chat(omega)) = O_alpha(q, omega) ,
# an EQUALITY rather than the domination inequality -- lem:mix-dom (iii) is
# tight when there is no f-term to perturb. So delta is irrelevant here and the
# certificate is being tested on its OTHER three ingredients: the Euler
# cancellation, the two dual minima, and the two enclosure widths.
# O-MIX-DOMINATION and O-SPECTRAL-WINDOW carry the f-term half, on TOY-1.
#
# THE CERTIFICATE POINT is x = (q~, omega~) = ((1/2, 1/2), diag(7/8, 1/8)) --
# the optimizer, which Theorem thm:cert does NOT require but which makes the
# tightness statement of Remark rem:cert-tightness checkable. Its membership in
# D of Eq. eq:cert-domain: omega~ >= 0 (eigenvalues 7/8, 1/8), tr omega~ = 1
# <= 1, q~ >= 0 componentwise, sum q~ = 1 <= 1, supp q~ = {chat0, chat1} =
# Chat_acc. All four hold, all four exactly decidable on this data.


@dataclass(frozen=True)
class EulerCase:
    """The Euler identity of Lemma ``lem:euler`` at one alpha on TOY-8-T."""

    case_id: str
    alpha: float
    #: ``dO/dq(chat0)``, ``dO/dq(chat1)`` at x, from Eq. eq:grad-q-work.
    grad_q: tuple[float, float]
    #: The two diagonal entries of ``grad_omega O`` at x, Eq. eq:grad-w-work.
    grad_omega_diagonal: tuple[float, float]
    #: ``<grad O(x), x>``, the left-hand side of Eq. eq:euler.
    pairing: float
    #: ``O^(delta,Ret)_alpha(x)``, which here equals h_low independently.
    objective: float
    arithmetic: str


EULER_CASES: tuple[EulerCase, ...] = (
    EulerCase(
        case_id="EUL-T8T-a15",
        alpha=1.5,
        grad_q=(1.9060203564940776, 10.32808512266689),
        grad_omega_diagonal=(-2.473191498666794, -17.31234049066756),
        pairing=1.7889676169135935,
        objective=1.7889676169135937,
        arithmetic="""\
alpha = 1.5, so alpha/(alpha-1) = 3 and log2 e = 1/ln 2 = 1.4426950408889634.
Chat_acc = {chat0, chat1} is disjoint from Chat_key (which is empty), so only
the FIRST branch of Eq. eq:grad-q-work applies:
  dO/dq(chat) = (alpha/(alpha-1)) ( log2( q(chat)/P_chat ) + log2 e ) .
  chat0: 3 ( log2( (1/2)/(7/8) ) + log2 e ) = 3 ( log2(4/7) + log2 e )
       = 3 ( 2 - log2 7 + log2 e ) = 3 . 0.6353401188313594
       = 1.9060203564940776
  chat1: 3 ( log2( (1/2)/(1/8) ) + log2 e ) = 3 ( 2 + log2 e )
       = 3 . 3.4426950408889634 = 10.32808512266689
Eq. eq:grad-w-work, with Delta^{(delta)} absent (Ret empty) and
Gamma^{(s0)}_chat0 = diag(1,0), Gamma^{(s0)}_chat1 = diag(0,1):
  grad_omega O = - log2 e . 3 . [ (q0/P_chat0) diag(1,0)
                                + (q1/P_chat1) diag(0,1) ]
               = - 4.32808512266689 . diag(4/7, 4)
               = diag(-2.473191498666794, -17.31234049066756) .
EULER, Eq. eq:euler:
  <grad O(x), x> = (1/2)(1.9060203564940776) + (1/2)(10.32808512266689)
                 + (7/8)(-2.473191498666794) + (1/8)(-17.31234049066756)
                 = 0.9530101782470388 + 5.164042561333445
                   - 2.163792561333445 - 2.164042561333445
                 = 1.7889676169135935 ,
against O_alpha(x) = 3 . 0.5963225389711979 = 1.7889676169135937. Equal to
15 decimal places; the last-bit difference is floating-point summation order
and the test admits it at 1e-12.
WHAT MAKES THIS AN ORACLE AND NOT A TAUTOLOGY: the right-hand side is h_low,
which the 0.3.0 registry derived for TOY-8-T from the KL divergence alone,
with no gradient anywhere in it. So the identity cross-checks the gradient
formulas of Corollary cor:work-gradient against a number obtained without
them.""",
    ),
    EulerCase(
        case_id="EUL-T8T-a2",
        alpha=2.0,
        grad_q=(1.2706802376627184, 6.885390081777927),
        grad_omega_diagonal=(-1.6487943324445296, -11.541560327111707),
        pairing=1.1926450779423954,
        objective=1.1926450779423958,
        arithmetic="""\
The same identity at alpha = 2, where alpha/(alpha-1) = 2. This alpha is
OUTSIDE the key-length domain (1, 2) and inside the (1, inf) that Assumption
A-ALPHA gives C13 and C18-C20, so it is admissible here and must NOT appear in
any key-length case (see CERT_ALPHA_INTEGER_BETA).
  dO/dq(chat0) = 2 ( 2 - log2 7 + log2 e ) = 1.2706802376627184
  dO/dq(chat1) = 2 ( 2 + log2 e )          = 6.885390081777927
  grad_omega O = -2 log2 e . diag(4/7, 4)
               = diag(-1.6487943324445296, -11.541560327111707)
  <grad O(x), x> = 1.1926450779423954  vs  O_alpha(x) = 2 . 0.5963225389711979
                 = 1.1926450779423958 .
Euler holds at every alpha because Lemma lem:work-convex's homogeneity is
alpha-independent -- the objective is positively 1-homogeneous along rays of D
for every alpha in (1, inf) -- and Lemma lem:euler turns that into
<grad, x> = O(x) wherever the gradient exists. Two alphas are frozen so that a
formula accidentally right at one cannot pass.""",
    ),
)

O_EULER_IDENTITY = OracleEntry(
    oracle_id="O-EULER-IDENTITY",
    claims=("C13", "C18"),
    kind="structural-identity",
    subject=(
        "Lemma lem:euler on TOY-8-T at alpha = 1.5 and alpha = 2: "
        "<grad O^(delta,Ret)(x), x> = O^(delta,Ret)(x), cross-checked against "
        "the independently derived h_low of that toy."
    ),
    derivation="""\
contract.tex Lemma lem:euler, Eq. eq:euler, on the point and declaration
written out in the block above. The lemma's proof is three lines: the working
objective is C^1 on an ambient neighbourhood of x (Corollary
cor:work-gradient, under (H1)-(H4)) and positively 1-homogeneous along the ray
through x (Lemma lem:work-convex), so g(t) = O(tx) satisfies g(t) = t g(1) on
an interval ending at 1 and therefore g'(1) = g(1), which IS Eq. eq:euler.

WHY IT IS THE LOAD-BEARING STEP OF THE WHOLE CERTIFICATE. Step 2 of Theorem
thm:cert is the supporting-hyperplane inequality
  O(y) >= O(x) + <grad O(x), y - x> ,
and Eq. eq:euler cancels O(x) - <grad O(x), x> EXACTLY, leaving the pure
linear minimization <grad O(x), y>. The contract states the consequence in
place: "This cancellation is why no evaluation of the objective at x -- and
hence no objective-evaluation error term -- appears anywhere in
Eq. eq:hcert." So the certificate never needs an enclosure of O(x) itself,
only of its gradient. An implementation that instead evaluated O(x) and
carried its enclosure would be computing a different, weaker bound; one that
DROPPED the O(x) term without the homogeneity argument would be computing an
unsound one.

HYPOTHESES, checked at this point rather than assumed. (H1) q~(chat) = 1/2 > 0
for both chat in Chat_acc. (H2) P_chat0 = 7/8 > 0 and P_chat1 = 1/8 > 0.
(H3) and (H4) are VACUOUS because Chat_acc n Chat_key is empty and Ret is
empty. x lies in D. So Corollary cor:work-gradient applies and the gradient
exists two-sidedly on an ambient neighbourhood -- which is what lets
lem:euler differentiate at t = 1 from both sides.

The two cases are in EULER_CASES.
""",
    toy_id="TOY-8-T",
)


@dataclass(frozen=True)
class CertificateCase:
    """One end-to-end evaluation of Eq. ``eq:hcert``, with its h_low."""

    case_id: str
    toy_id: str
    mode: str
    alpha: float
    #: ``h_low``, known independently of the certificate.
    h_low: float
    beta_acc: float
    beta_feas: float
    eps_acc: float
    eps_feas: float
    #: ``beta_acc + beta_feas - eps_acc - eps_feas``.
    h_cert: float
    arithmetic: str


CERTIFICATE_CASES: tuple[CertificateCase, ...] = (
    CertificateCase(
        case_id="CERT-T8T-a15",
        toy_id="TOY-8-T",
        mode="trusted",
        alpha=1.5,
        h_low=1.7889676169135937,
        beta_acc=6.09375,
        beta_feas=-4.3515625,
        eps_acc=0.0625,
        eps_feas=0.0625,
        h_cert=1.6171875,
        arithmetic="""\
END TO END, TRUSTED-SOURCE MODE, WITH A STRICTLY POSITIVE h_low SO THAT THE
INEQUALITY IS NOT AN EQUALITY AT ZERO.

Point x = ((1/2, 1/2), diag(7/8, 1/8)), in D and satisfying (H1)-(H4) as
recorded above. alpha = 1.5. The true gradient at x is EUL-T8T-a15's:
  dO/dq = (1.9060203564940776, 10.32808512266689) ,
  grad_omega O = diag(-2.473191498666794, -17.31234049066756) .

SURROGATE (Theorem thm:cert requires only that it be "arbitrary exact machine
data"; these are dyadic rationals):
  g~ = (15/8, 165/16) = (1.875, 10.3125) ,
  G~ = diag(-5/2, -277/16) = diag(-2.5, -17.3125) .

HYPOTHESIS (a), the enclosure widths:
  |dO/dq(chat0) - g~(chat0)| = 0.03102035649407764
  |dO/dq(chat1) - g~(chat1)| = 0.015585122666889717   -> max 0.0310203565...
  eps_acc = 1/16 = 0.0625 covers it.
  grad_omega O - G~ = diag(0.026808501333206003, 0.0001595093324411323) ,
  whose Frobenius norm is 0.026808975865550026; since
  sup_{||H||_F <= 1} |tr[E H]| = ||E||_F for Hermitian E, that norm IS the
  quantity Eq. eq:budget bounds, and eps_feas = 1/16 = 0.0625 covers it.
  Both widths are chosen as dyadic rationals ABOVE the true errors, which is
  what a sound enclosure assembly must produce; prop:budget is the recipe for
  producing them, and this case pins the INEQUALITY it must satisfy rather
  than any particular assembly.

HYPOTHESIS (b), beta_acc, by Remark rem:acc-side (a) on the singleton
AcceptSet = {(1/2, 1/2)}:
  beta_acc = (1/2)(15/8) + (1/2)(165/16) = 195/32 = 6.09375 (exact).

HYPOTHESIS (c), beta_feas, by Theorem thm:weak-duality (i) with m = 0 on
Feas = {tau_A}:
  witness y_0 = 0, Upsilon = G~, so Slack = 0 >= 0 and
  beta_feas = tr[G~ tau_A] = (-5/2)(7/8) + (-277/16)(1/8)
            = -35/16 - 277/128 = -557/128 = -4.3515625 .
Tight, since Feas is a single point.

Eq. eq:hcert:
  h_cert = 195/32 - 557/128 - 1/16 - 1/16
         = 780/128 - 557/128 - 8/128 - 8/128 = 207/128 = 1.6171875 .

THE CLAIM, h_cert <= h_low:
  1.6171875 <= 1.7889676169135937 .  TRUE, with slack 0.1717801169135937.
That slack decomposes exactly as Remark rem:cert-tightness says it should:
  beta_acc + beta_feas = 780/128 - 557/128 = 223/128 = 1.7421875 is the value
  the SURROGATE gives where the true gradient would give h_low (Euler); the
  difference 1.7889676169135937 - 1.7421875 = 0.0467801169135937 is the
  surrogate's own slack, and the remaining eps_acc + eps_feas = 1/16 + 1/16 =
  1/8 = 0.125 is the enclosure. The two add to 0.1717801169135937 exactly.
  Nothing else contributes -- in particular no objective-evaluation term,
  because Euler cancelled it.
h_cert is POSITIVE here, so this case also carries a nonzero certified key
length; see CERT_KEY_LENGTH_CASES.""",
    ),
    CertificateCase(
        case_id="CERT-T8UN-a2",
        toy_id="TOY-8-UN",
        mode="untrusted",
        alpha=2.0,
        h_low=0.0,
        beta_acc=2.90625,
        beta_feas=-2.90625,
        eps_acc=0.03125,
        eps_feas=0.03125,
        h_cert=-0.0625,
        arithmetic="""\
END TO END, UNTRUSTED-SOURCE MODE, AT THE EXACT OPTIMUM -- the case where the
certificate's tightness statement is visible in the arithmetic.

TOY-8-UN is TOY-8-T with the marginal slot emptied, so Feas is the whole set
of density matrices on C^2 and h_low = 0, attained at omega = 1/2 (frozen at
0.3.0: the accepted statistics (1/2, 1/2) become reachable, so the divergence
vanishes). alpha = 2, admissible for C13 and C18-C20 on (1, inf).

Point x = ((1/2, 1/2), diag(1/2, 1/2)) -- the optimizer. In D: PSD, trace 1,
q~ >= 0 with sum 1, supported in Chat_acc. (H1): 1/2 > 0. (H2): P_chat0 =
P_chat1 = 1/2 > 0. (H3), (H4) vacuous (Chat_key empty).

TRUE GRADIENT at x, from Eq. eq:grad-q-work with alpha/(alpha-1) = 2 and
q(chat)/P_chat = 1 for both:
  dO/dq(chat) = 2 ( log2 1 + log2 e ) = 2 log2 e = 2.8853900817779268 , both ;
  grad_omega O = -2 log2 e ( 1 . diag(1,0) + 1 . diag(0,1) )
               = -2.8853900817779268 . 1_2 .
The gradient is a MULTIPLE OF THE IDENTITY here, which is why the two dual
bounds cancel so cleanly below.

SURROGATE: g~ = (93/32, 93/32) and G~ = -(93/32) 1_2, with 93/32 = 2.90625 the
dyadic rational just above 2 log2 e.
  |dO/dq - g~| = 0.020859918222073226 <= eps_acc = 1/32 = 0.03125 ;
  ||grad_omega O - G~||_F = 0.029500379259649614 <= eps_feas = 1/32 .

beta_acc, singleton: (1/2)(93/32) + (1/2)(93/32) = 93/32 = 2.90625.
beta_feas, Theorem thm:weak-duality (ii) with m = 0: y_0 = -93/32 gives
Slack = G~ - y_0 1 = 0 >= 0 and beta_feas = y_0 = -93/32 = -2.90625. Tight,
since min tr[G~ omega] over density matrices is lambda_min(G~) = -93/32.

Eq. eq:hcert:
  h_cert = 93/32 - 93/32 - 1/32 - 1/32 = -2/32 = -1/16 = -0.0625 <= 0 = h_low .

WHAT THIS PINS THAT THE TRUSTED CASE DOES NOT.
(1) beta_acc + beta_feas = 0 EXACTLY, which is Remark rem:cert-tightness's
    statement made arithmetic: "at an exact optimizer x* of the unperturbed
    program with exact data, first-order optimality makes
    min_y <grad O(x*), y> attained at x*, and the Euler identity gives
    h_cert = O_alpha(x*) = h_low". Here the surrogate is not the exact
    gradient, yet the two sides still cancel because the gradient is a
    multiple of the identity and the surrogate inherits that.
(2) h_cert is NEGATIVE while being perfectly SOUND. Contract Section 2.2:
    h_cert "may be negative or -inf-useless without being unsound; a poor
    h_cert is a tightness failure, reported as the gap diagnostic, never
    repaired". The whole deficit here is eps_acc + eps_feas = 1/16, the price
    of enclosing a transcendental gradient with dyadic rationals.
(3) By Corollary cor:cert-keylength, h_cert <= 0 means no positive length
    satisfies Eq. eq:keylength-cert and NO KEY IS CLAIMED -- the conservative
    outcome, and the correct one, since h_low = 0 offers no key either.""",
    ),
)

O_HCERT_END_TO_END = OracleEntry(
    oracle_id="O-HCERT-END-TO-END",
    claims=("C13", "C18", "C19", "C20"),
    kind="toy-instance",
    subject=(
        "Two complete evaluations of Eq. eq:hcert, one per source mode, on "
        "declarations whose h_low is known independently: h_cert <= h_low "
        "with 1.6171875 <= 1.7889676169135937 (trusted, positive rate) and "
        "-0.0625 <= 0 (untrusted, at the exact optimum)."
    ),
    derivation="""\
contract.tex Theorem thm:cert, Eq. eq:hcert:
  h_cert := beta_acc + beta_feas - eps_acc - eps_feas <= h_low ,
under (a) the two enclosure widths, (b) the acceptance-side minimum, (c) the
feasible-side minimum, at a point x in D satisfying (H1)-(H4). The two cases
below instantiate ALL FOUR ingredients on declarations whose h_low was derived
at 0.3.0 from the KL divergence alone, so the inequality is checked against a
number the certificate had no part in producing.

THE PROOF'S FOUR STEPS, each visible in the arithmetic of the cases:
  Step 1  domination, O_alpha(y) >= O^{(delta,Ret)}_alpha(y). EQUALITY here,
          because Chat_key is empty and there is no f-term to perturb;
          O-MIX-DOMINATION carries the strict case on TOY-1.
  Step 2  supporting hyperplane at x, collapsed by Euler to
          O^{(delta,Ret)}(y) >= <grad O(x), y>. O-EULER-IDENTITY pins the
          cancellation on the same point.
  Step 3  surrogate insertion, splitting <grad O(x), y> into the q-part
          (>= beta_acc - eps_acc, using sum_chat q'(chat) = 1) and the
          omega-part (>= beta_feas - eps_feas, using
          ||omega'_s||_F <= tr omega'_s and sum_s tr omega'_s = 1).
  Step 4  infimum over y in AcceptSet x Feas.
Every step lowers the value, so the whole chain is conservative and a
computed h_cert can only be too SMALL, never too large -- provided its four
inputs are what they claim to be, which is what the fail-closed entries guard.

WHY THE FROBENIUS BOUND IN STEP 3 IS NOT AN OPERATOR-NORM BOUND. The step uses
||omega'_s||_F <= ||omega'_s||_1 = tr omega'_s, valid because omega'_s is PSD,
and then sum_s tr omega'_s = 1. So eps_feas is defined against
Frobenius-unit directions and Lemma lem:transfer (ii) supplies exactly that
and nothing stronger -- the two are matched on purpose, and neither an
operator-norm width nor a trace-norm width would fit.

The two cases are in CERTIFICATE_CASES.
""",
)


@dataclass(frozen=True)
class CertifiedKeyLengthCase:
    """One frozen evaluation of Corollary ``cor:cert-keylength``."""

    case_id: str
    certificate_case_id: str
    rounds: int
    lambda_ec: int
    eps_ev: float
    eps_pa: float
    alpha: float
    h_cert: float
    h_low: float
    #: ``l_max`` from h_cert via Eq. eq:keylength-cert.
    certified_length: int
    #: ``l_max`` from h_low via Eq. eq:keylength. Must be >= the certified one.
    estimate_length: int
    arithmetic: str


CERTIFIED_KEY_LENGTH_CASES: tuple[CertifiedKeyLengthCase, ...] = (
    CertifiedKeyLengthCase(
        case_id="CKL-1-positive",
        certificate_case_id="CERT-T8T-a15",
        rounds=1000,
        lambda_ec=100,
        eps_ev=2.0**-32,
        eps_pa=2.0**-32,
        alpha=1.5,
        h_cert=1.6171875,
        h_low=1.7889676169135937,
        certified_length=1390,
        estimate_length=1561,
        arithmetic="""\
Corollary cor:cert-keylength Eq. eq:keylength-cert is Theorem thm:keylength
Eq. eq:keylength with h_cert in place of h_low and nothing else changed, so
the reported value is the same l_max of Remark rem:plus2:
  l_max = max{0, floor(n B - lambda_EC - ceil(log2(1/eps_EV))
                       - (alpha/(alpha-1)) log2(1/eps_PA) + 1)} .
With n = 1000, lambda_EC = 100, eps_EV = eps_PA = 2^{-32}, alpha = 1.5
(alpha/(alpha-1) = 3, log2(1/eps) = 32 for both budgets):
  FROM h_cert = 207/128 = 1.6171875 :
    n h_cert                                   = 1617.1875
    - lambda_EC                                = -100    -> 1517.1875
    - ceil(log2(1/eps_EV)) = -32               ->            1485.1875
    - (alpha/(alpha-1)) log2(1/eps_PA) = -96   ->            1389.1875
    + 1                                        ->            1390.1875
    floor                                      ->            1390
  FROM h_low = 1.7889676169135937 :
    1788.9676169135937 - 100 - 32 - 96 + 1 = 1561.9676169135937 -> 1561 .

THE ORDERING 1390 <= 1561 IS THE CONTENT. The corollary's proof is one line --
h_cert <= h_low and n >= 1, so eq:keylength-cert implies eq:keylength and
Theorem thm:keylength applies unchanged, "monotonicity in the bound is
manifest: the right-hand side of eq:keylength is non-decreasing in h_low". A
certified run therefore reports a length no LARGER than the estimate run would,
and the difference n (h_low - h_cert) = 171.78 bits is what the certificate
costs. An implementation reporting a certified length ABOVE the estimate
length has inverted the bound.

alpha = 1.5 IS IN (1, 2), as Assumption A-ALPHA requires of EVERY key-length
statement -- "Theorem thm:keylength and Corollary cor:cert-keylength alike".
The alpha = 2 of CERT-T8UN-a2 is admissible for h_cert itself and is NOT
usable here, which is why no key-length case carries it.

MONOTONICITY (C15) CARRIES VERBATIM. cor:cert-keylength's proof states that
all four conclusions of Proposition prop:monotone hold for the certified
length "because h_cert depends on none of (lambda_EC, eps_EV, eps_PA), so
prop:monotone's proof carries word for word". CKL-2 and CKL-3 freeze two
instances of that.""",
    ),
    CertifiedKeyLengthCase(
        case_id="CKL-2-leakage-monotone",
        certificate_case_id="CERT-T8T-a15",
        rounds=1000,
        lambda_ec=300,
        eps_ev=2.0**-32,
        eps_pa=2.0**-32,
        alpha=1.5,
        h_cert=1.6171875,
        h_low=1.7889676169135937,
        certified_length=1190,
        estimate_length=1361,
        arithmetic="""\
CKL-1 with lambda_EC raised from 100 to 300, everything else held: both lengths
drop by exactly 200, to 1190 and 1361. Proposition prop:monotone (i), which
cor:cert-keylength inherits: l_max is NON-INCREASING in leakage, on the
certified path as on the estimate path. The drop is exactly the leakage
increase because the bracket is linear in lambda_EC and no floor or clamp
fires here.""",
    ),
    CertifiedKeyLengthCase(
        case_id="CKL-3-clamp",
        certificate_case_id="CERT-T8UN-a2",
        rounds=1000,
        lambda_ec=0,
        eps_ev=1.0,
        eps_pa=1.0,
        alpha=1.5,
        h_cert=-0.0625,
        h_low=0.0,
        certified_length=0,
        estimate_length=1,
        arithmetic="""\
THE NEGATIVE-h_cert BRANCH, on CERT-T8UN-a2's value h_cert = -1/16. At the
maximal budgets eps = 1 both deductions vanish and lambda_EC = 0, so the
bracket is n h_cert + 1 = -62.5 + 1 = -61.5, the clamp max{0, .} of Remark
rem:plus2 fires, and the certified length is 0. From h_low = 0 the bracket is
0 + 1 = 1 and the estimate length is 1.
Corollary cor:cert-keylength states this outcome in its own last sentence: "If
h_cert <= 0 no positive l satisfies eq:keylength-cert and no key is claimed --
the conservative outcome." A negative h_cert is a TIGHTNESS failure, not an
unsoundness, and the conforming response is to claim no key rather than to
repair the certificate.
NOTE the alpha: the certificate value h_cert = -1/16 was computed at alpha = 2
(CERT-T8UN-a2), which is outside the key-length domain. This case therefore
uses alpha = 1.5 for the key-length arithmetic and consumes the NUMBER -1/16
as a bound. That is legitimate only because the bound is a bound: Theorem
thm:cert gives h_cert <= h_low at its own alpha, and h_low(TOY-8-UN) = 0 at
EVERY alpha in (1, inf), so -1/16 <= h_low holds at alpha = 1.5 too. The case
records the reasoning rather than silently mixing the two alphas.""",
    ),
)

O_CERT_KEY_LENGTH = OracleEntry(
    oracle_id="O-CERT-KEY-LENGTH",
    claims=("C13", "C14", "C15"),
    kind="toy-instance",
    subject=(
        "The certified key length of Corollary cor:cert-keylength on three "
        "frozen cases: 1390 <= 1561 against the estimate length, the "
        "leakage-monotone variant, and the clamp at 0 when h_cert < 0."
    ),
    derivation="""\
contract.tex Corollary cor:cert-keylength, Eq. eq:keylength-cert. The formula
is Theorem thm:keylength's with h_cert substituted for h_low; the reported
integer is l_max of Remark rem:plus2, with the same floor and the same clamp
at 0, "both in the safe direction".

WHAT THE THREE CASES PIN, beyond the arithmetic:
  CKL-1  the ORDERING certified <= estimate, on a case where both are large
         and positive, so an inverted bound cannot hide in a clamp;
  CKL-2  Proposition prop:monotone (i) on the certified path, which
         cor:cert-keylength's proof says holds verbatim because h_cert
         depends on none of (lambda_EC, eps_EV, eps_PA);
  CKL-3  the clamp when h_cert <= 0 -- no key claimed, which is the
         conservative outcome the corollary names.

THE +1 CONSTANT is this contract's, not the source's, exactly as for
Eq. eq:keylength: the source region proves secrecy for the ^Omega_AT state
with constant +2, and this contract spends one deterministic bit (the
announced error-verification acceptance flag) to reach the ACCEPTED state
(Remark rem:plus2). The certified formula inherits it unchanged.

ALPHA DOMAIN. Every case has alpha in (1, 2). Assumption A-ALPHA at 0.4.0
confines EVERY key-length statement to that interval and names
cor:cert-keylength alongside thm:keylength when it does so, even though C13
itself and the whole certificate chain C18-C20 hold on (1, inf).
""",
)


# ---------------------------------------------------------------------------
#  C13 fail-closed -- when `certified` must NOT be reachable.
# ---------------------------------------------------------------------------
#
# These are the load-bearing half of Group 7. Contract 0.4.0 makes the label
# `certified` reachable for the first time in this module's history, and every
# entry below names a condition under which it must not be emitted.


@dataclass(frozen=True)
class DomainFailureCase:
    """A candidate certificate point and its ``x in D`` verdict."""

    case_id: str
    #: Which condition of Eq. eq:cert-domain is at issue.
    condition: str
    in_domain: bool
    #: The conforming responses, in the contract's own order.
    responses: tuple[str, ...]
    arithmetic: str


DOMAIN_FAILURE_CASES: tuple[DomainFailureCase, ...] = (
    DomainFailureCase(
        case_id="DOM-1-negative-eigenvalue",
        condition="omega_s >= 0 (block PSD)",
        in_domain=False,
        responses=("repair to a point of D and re-check", "fail closed"),
        arithmetic="""\
Candidate x = ((1/2, 1/2), omega~) on TOY-8-T's declaration with
  omega~ = diag(1 + 1/128, -1/128) .
The trace is 1 and q~ is fine, but omega~ has the eigenvalue -1/128 < 0, so
the FIRST condition of Eq. eq:cert-domain fails and x is not in D.
This is the case Remark rem:cert-interface predicts by name: "rounding a
numerically-PSD matrix generically produces a stray negative eigenvalue or a
trace marginally above 1". The check runs on the ROUNDED EXACT point, never on
the pre-rounding floating-point iterate, so a solver iterate that was PSD to
machine precision can and does fail here.
THE CHECK IS EXACT: Theorem thm:cert says each condition of D is "exactly
decidable for exact machine data (the PSD checks by the same rational
LDL^T/Cholesky reference method as Remark rem:dual-exact; the rest by
inspection)". A tolerance of 1e-12 on the eigenvalue would admit this point.
THE TWO CONFORMING RESPONSES, and only these two: repair the point (any point
of D is admissible, so flooring negative eigenvalues and rescaling the trace
at the reference-arithmetic level is legitimate, at a tightness cost only) --
followed by a FRESH exact D-membership check on the repaired point -- or fail
closed to `estimate` with a machine-readable reason.
CERTIFYING FROM x ITSELF IS NOT AN OPTION, and the contract gives the reason
rather than a rule: Step 2 of thm:cert's proof needs convexity on the whole
segment from x to any feasible point, and Lemma lem:work-convex establishes
that on D only.""",
    ),
    DomainFailureCase(
        case_id="DOM-2-trace-above-one",
        condition="tr omega <= 1",
        in_domain=False,
        responses=("repair to a point of D and re-check", "fail closed"),
        arithmetic="""\
Candidate x = ((1/2, 1/2), omega~) with omega~ = diag(7/8, 1/4) on TOY-8-T's
declaration. omega~ is PSD and q~ is fine, but tr omega~ = 9/8 > 1, so the
SECOND condition of Eq. eq:cert-domain fails.
NOTE THE ASYMMETRY, which is easy to get wrong: D asks for tr omega <= 1, NOT
tr omega = 1. The certificate point need not be feasible and need not be
normalized; a point of trace 7/8 is perfectly admissible. Only exceeding 1 is
fatal, because C_<= is the cone slice on which lem:work-convex's homogeneity
argument runs (its rays are capped at t = 1).
REPAIR THAT SUCCEEDS, frozen so the branch is not merely described: rescaling
by 8/9 at the reference-arithmetic level gives
  omega~' = diag(7/9, 2/9) ,
which is PSD with trace exactly 1, hence IN D; and the hypotheses survive it,
since P_chat0 = 7/9 > 0 and P_chat1 = 2/9 > 0 give (H2), (H1) is untouched and
(H3), (H4) are vacuous on this declaration. So the run may proceed from
omega~' -- at a tightness cost, because omega~' is not the optimizer
diag(7/8, 1/8) and the resulting h_cert is smaller. Repair is a tightness
decision; it is never a soundness one.""",
    ),
    DomainFailureCase(
        case_id="DOM-3-mass-outside-acceptance-support",
        condition="supp q subset Chat_acc",
        in_domain=False,
        responses=("enlarge Chat_acc if admissible", "fail closed"),
        arithmetic="""\
Candidate x = (q~, diag(7/8, 1/8)) with Chat = {chat0, chat1, chat2},
acceptance support Chat_acc = {chat0, chat1}, and
  q~ = (0.4, 0.4, 0.2) .
q~ is nonnegative with sum 1 <= 1, and omega~ is PSD with trace 1, but
q~(chat2) = 0.2 > 0 while chat2 is not in Chat_acc, so the FOURTH condition of
Eq. eq:cert-domain fails and x is not in D.
WHY THIS ONE IS NOT COSMETIC. Step 3 of thm:cert bounds the q-part by
  <grad_q O(x), q'> >= sum_{chat in Chat_acc} g~(chat) q'(chat)
                       - eps_acc sum_{chat in Chat_acc} q'(chat)
                    >= beta_acc - eps_acc ,
and the last inequality uses sum_{chat in Chat_acc} q'(chat) = 1 -- true for
every q' in AcceptSet precisely because AcceptSet is supported in Chat_acc.
The surrogate g~ is a vector on Chat_acc and is not even DEFINED at chat2.
A point carrying mass outside Chat_acc is not a point of the space the
certificate is stated on.
THE SECOND CONFORMING RESPONSE IS AVAILABLE HERE and is not a repair of the
point: Definition def:perturbed admits ANY acceptance support, "the minimal
choice is the union of the supports and any admissible superset may be used".
So enlarging Chat_acc to {chat0, chat1, chat2} -- if that set is still an
acceptance support for the declared AcceptSet -- restores membership, at the
cost of a surrogate and an eps_acc over the larger index set. Enlarging it to
a set that is NOT an acceptance support is not a repair; it is a wrong
Chat_acc, and Step 3's sum-to-one step fails.""",
    ),
    DomainFailureCase(
        case_id="DOM-4-in-domain-but-not-feasible",
        condition="all four (this point IS in D)",
        in_domain=True,
        responses=("certify",),
        arithmetic="""\
THE CONTROL CASE, and the one that shows D is genuinely weaker than
feasibility. Candidate x = ((1/2, 1/2), omega~) with
  omega~ = diag(1/2, 1/4)
on TOY-8-T's declaration. It is IN D: PSD, tr = 3/4 <= 1, q~ >= 0 with sum 1,
supported in Chat_acc. It is NOT in Feas: TOY-8-T's marginal condition demands
omega = diag(7/8, 1/8) exactly, and neither the value nor even the trace
matches.
Theorem thm:cert applies anyway, and says so in its own hypothesis: "x is NOT
required to lie in AcceptSet x Feas: no marginal condition, no constraint of
CList and no acceptance membership is assumed of it." That is the sense in
which the closure is STRONGER than the criterion recorded at 0.2.3, which had
asked only for a theorem taking a FEASIBLE point -- and it is why no primal
repair machinery exists anywhere in the contract.
So an implementation must not add a feasibility check here. Doing so would be
sound but would reject valid certificates, and worse, it would suggest that
feasibility is what makes the bound work -- which would leave the actual
requirement, x in D, unenforced.""",
    ),
)

O_CERT_DOMAIN_FAIL = OracleEntry(
    oracle_id="O-CERT-DOMAIN-FAIL",
    claims=("C13", "C18"),
    kind="fail-closed",
    subject=(
        "The membership x in D of Eq. eq:cert-domain, on four candidate "
        "points: a negative eigenvalue, a trace above 1, mass outside the "
        "acceptance support -- each refused -- and one point that is in D "
        "while NOT being feasible, which must be accepted."
    ),
    derivation="""\
contract.tex Eq. eq:cert-domain, Theorem thm:cert's hypothesis, and Remark
rem:cert-interface. D is
  { q >= 0 componentwise, sum_chat q(chat) <= 1, q(chat) = 0 for chat outside
    Chat_acc } x { omega = (omega_s) : omega_s >= 0, tr omega <= 1 } ,
and thm:cert calls the membership LOAD-BEARING in its own words, with the
reason: "the supporting-hyperplane step below needs convexity on the whole
segment from x to any feasible point, which Lemma lem:work-convex establishes
on D only."

THIS ENTRY EXISTS BECAUSE THE OMISSION WAS A BLOCKING FINDING. F-9-01 was
raised against version 0.4.0's own draft text: the
interface remark's soundness sentence overstated the infeasible-point
allowance, and three enumerations of the certified-run checks omitted the
x-in-D check entirely, so "a literal G4 implementation could emit an unsound
certified label". The repair added the membership to all four sites. An oracle
that pins the check is the implementation-side counterpart of that repair.

THE FOUR CONDITIONS ARE INDEPENDENT and each is exactly decidable on exact
machine data. Three of the four cases below violate exactly one of them and
satisfy the others, so a check that conflated any two would pass a point it
must refuse. The fourth violates none while being infeasible, so a check that
tested feasibility instead of membership would refuse a point it must accept.

WHERE THE CHECK RUNS. On the ROUNDED EXACT point, in BOTH source modes: in
trusted-source mode the solver's Choi iterate is pushed forward by a plain
floating-point application of chi and then rounded; in untrusted-source mode
there is no push-forward and the state-form iterate is rounded directly. The
pre-rounding floating-point iterate is never the subject of the check.

The four cases are in DOMAIN_FAILURE_CASES.
""",
)


@dataclass(frozen=True)
class HypothesisFailureCase:
    """One violated hypothesis of Corollary ``cor:work-gradient``."""

    case_id: str
    #: "H1", "H2", "H3" or "H4".
    hypothesis: str
    #: The hypotheses that still HOLD at this point, so the failure is isolated.
    others_hold: tuple[str, ...]
    #: The conforming response, per Remark rem:cert-interface.
    response: str
    arithmetic: str


HYPOTHESIS_FAILURE_CASES: tuple[HypothesisFailureCase, ...] = (
    HypothesisFailureCase(
        case_id="HYP-1-q-vanishes",
        hypothesis="H1",
        others_hold=("H2", "H3", "H4"),
        response="fail closed to estimate, reason (H1)",
        arithmetic="""\
(H1) asks q(chat) > 0 for every chat in Chat_acc. Point
  x = ((1, 0), diag(7/8, 1/8)) on TOY-8-T's declaration, with
  Chat_acc = {chat0, chat1} .
x IS in D (q~ >= 0, sum 1, supported in Chat_acc; omega~ PSD, trace 1) and
(H2) holds (P_chat0 = 7/8 > 0, P_chat1 = 1/8 > 0); (H3) and (H4) are vacuous.
Only (H1) fails, at chat1.
WHY IT MATTERS. Eq. eq:grad-q-work's first branch is
  (alpha/(alpha-1)) ( log2( q(chat)/P_chat ) + log2 e ) ,
which at q(chat1) = 0 is log2 0 = -infinity: the objective is finite at x
(d(0, v) = 0 by Lemma foundations/lem:kernel) but NOT differentiable there, and
Corollary cor:work-gradient's C^1 extension does not exist. Theorem thm:cert's Step 2
needs a two-sided derivative at x and has none.
NO REPAIR IS OFFERED for (H1) in the contract, and none should be improvised:
moving q~ off the boundary changes the certificate point, which is legitimate
only by re-running the whole check chain at the new point. The conforming
response is to fail closed with a reason naming (H1).""",
    ),
    HypothesisFailureCase(
        case_id="HYP-2-branch-probability-vanishes",
        hypothesis="H2",
        others_hold=("H1", "H4"),
        response="fail closed to estimate, reason (H2)",
        arithmetic="""\
(H2) asks P_chat(omega) > 0 for every chat in Chat_acc. Point
  x = ((1/2, 1/2), diag(1, 0)) on TOY-8-T's declaration.
x IS in D (PSD, trace 1, q~ fine) and (H1) holds. But
  P_chat1(omega~) = tr[diag(0,1) diag(1,0)] = 0 ,
so (H2) fails at chat1.
WHY IT MATTERS. The kernel term d(q(chat1), 0) = +infinity for q(chat1) > 0
(Lemma foundations/lem:kernel), so O^{(delta,Ret)}_alpha(x) = +infinity: the objective
is not even FINITE at x, let alone differentiable, and neither Lemma lem:euler
nor Step 2 of thm:cert has anything to work with.
(H3) IS NOT LISTED AMONG THE SURVIVORS, and the reason is a structural fact
worth recording here rather than rediscovering: ON D, (H2) AND (H3) ARE
EQUIVALENT. From Eq. eq:fK and Eq. eq:traces, K_chat = T_chat + tr Theta_chat
with both terms non-negative, so K_chat = 0 forces T_chat = 0 (hence every
branch operator zero, hence tr G_chat = 0) and tr Theta_chat = 0, whence
P_chat = tr G_chat + tr Theta_chat = 0. Conversely each f^{(delta)} <= 0 gives
K^{(delta,Ret)}_chat <= P_chat, so P_chat = 0 forces
K^{(delta,Ret)}_chat = 0. Therefore an (H3) failure at a point of D is always
accompanied by an (H2) failure -- see HYP-3.""",
    ),
    HypothesisFailureCase(
        case_id="HYP-3-working-denominator-floor",
        hypothesis="H3",
        others_hold=("H1",),
        response="fail closed to estimate, reason (H3): no certified floor",
        arithmetic="""\
(H3) asks K^{(delta,Ret)}_chat(omega) > 0 for every chat in Chat_acc n
Chat_key, and Proposition prop:budget sharpens it to a CERTIFIED floor:
"interval evaluation under Assumption A-IA has certified positive floors ...
K^{(delta,Ret)}_chat(omega~) >= k_low > 0".
AN (H3)-ONLY VIOLATION DOES NOT EXIST ON D. By the equivalence derived in
HYP-2, K^{(delta,Ret)}_chat = 0 exactly when P_chat = 0, so the mathematical
hypothesis (H3) is implied by (H2) at every point of D. Stating it separately
is harmless and conservative -- a redundant hypothesis is not a wrong one --
but an implementer looking for a point that violates (H3) alone will not find
one, and should not manufacture one.
WHAT DOES FAIL INDEPENDENTLY IS THE FLOOR. Take TOY-1 at
  x = ((1), omega~) with omega~ = diag(2^{-40}, 0) ,
which is in D (PSD, trace 2^{-40} <= 1). Here P_chat0 = 2^{-40} > 0 and
K^{(delta,Ret)}_chat0 = 2^{-40} (1 + f^{(delta)}(1)) > 0, so both hypotheses
hold EXACTLY -- and yet an enclosure whose radius is 2^{-30} cannot certify
any positive floor, because the interval containing the true value also
contains 0. prop:budget requires k_low > 0 to be CERTIFIED, not merely true.
So the conforming response is to fail closed with a reason naming (H3), and
the reason must distinguish "violated" from "not certified": the second is a
numerical outcome that a finer enclosure could change, the first is not.""",
    ),
    HypothesisFailureCase(
        case_id="HYP-4-retained-branch-trace-vanishes",
        hypothesis="H4",
        others_hold=("H1", "H2", "H3"),
        response="drop the pair from Ret, or fail closed",
        arithmetic="""\
(H4) asks tr X_{chat,s}(omega_s) > 0 for every RETAINED pair (chat, s) in Ret.
This is the one hypothesis with a genuinely independent violation, and TOY-1
supplies it. Take
  x = ((1), omega~) with omega~ = diag(0, 1) ,  Ret = {(chat0,s0),(chat0,s1)} .
x is in D (PSD, trace 1). (H1): q~(chat0) = 1 > 0. (H2): P_chat0 = tr omega~
= 1 > 0. (H3): K^{(delta,Ret)}_chat0 = 1 + f^{(delta)}_{s0}(0)
+ f^{(delta)}_{s1}(1) = 1 + 0 + 0 = 1 > 0, using that s1 is key-inert so its
perturbed deficit vanishes as well (see O-MIX-DOMINATION, part (ii)).
But tr X_{chat0,s0}(0) = 0, so (H4) FAILS at the pair (chat0, s0).
WHY IT MATTERS. Lemma lem:window's spectral window is [delta c / d, 1] with
c = tr X_{chat,s}; at c = 0 the window collapses to {0}, X^{(delta)} = 0 is
not positive definite, and the whole reason the certified path never needs a
face rule disappears. Eq. eq:grad-fdelta has no gradient to return.
THE FIRST CONFORMING RESPONSE IS NOT FAILURE, and it is licensed by the
contract rather than invented: Ret is "any subset" of the key-live pairs
(Definition def:perturbed), Lemma lem:mix-dom holds "for every retained set
Ret", and Section 2.4 calls the retained set an implementation choice
"recorded in the witness payload, not a declared parameter: any admissible
choice yields a sound h_cert, and their quality affects tightness only". So
dropping (chat0, s0) from Ret leaves Ret' = {(chat0, s1)}, on which (H4)
holds (tr X_{chat0,s1}(1) = 1 > 0), and the certificate proceeds. The cost is
tightness: K^{(delta,Ret')} = 1 rather than a smaller number, so the certified
value is lower.
Failing closed is equally conforming. What is NOT conforming is evaluating
Eq. eq:Delta-work at the vanishing branch anyway.""",
    ),
)

O_CERT_HYPOTHESES_FAIL = OracleEntry(
    oracle_id="O-CERT-HYPOTHESES-FAIL",
    claims=("C13", "C18"),
    kind="fail-closed",
    subject=(
        "Each of (H1)-(H4) of Corollary cor:work-gradient violated "
        "separately, with the conforming response for each -- including the "
        "derived fact that (H2) and (H3) are EQUIVALENT on D, so an (H3) "
        "failure is always a failure to CERTIFY a floor, and the fact that an "
        "(H4) failure may be answered by shrinking the retained set."
    ),
    derivation="""\
contract.tex Corollary cor:work-gradient, hypotheses (H1)-(H4), and
Proposition prop:budget's certified floors p_low, k_low, t_low. Theorem
thm:cert requires the point x to satisfy all four, and Remark
rem:cert-interface lists them among the checks a certified run must pass:
"hypotheses (H1)-(H4) with their certified floors".

THE FOUR ARE NOT INDEPENDENT, and this entry derives the dependence rather
than assuming it. On the certificate domain D:
  (H2)  P_chat(omega) > 0        for chat in Chat_acc
  (H3)  K^{(delta,Ret)}_chat > 0 for chat in Chat_acc n Chat_key
are EQUIVALENT. Proof, from this contract's own Eqs. eq:fK and eq:traces:
  K_chat = T_chat + P_chat - tr G_chat = T_chat + tr Theta_chat ,
both terms non-negative, so K_chat = 0 iff T_chat = 0 and tr Theta_chat = 0;
T_chat = 0 forces every branch operator X_{chat,s} = 0, hence tr G_chat = 0,
hence P_chat = tr G_chat + tr Theta_chat = 0. Conversely
K^{(delta,Ret)}_chat = P_chat + sum_{Ret} f^{(delta)} <= P_chat because every
f^{(delta)} <= 0 (Lemma lem:mix-dom (i)), so P_chat = 0 forces
K^{(delta,Ret)}_chat = 0; and K^{(delta,Ret)}_chat >= K_chat >= 0 gives the
other direction.
CONSEQUENCE FOR AN IMPLEMENTATION: there is no point of D violating (H3) and
satisfying (H2), so an (H3) check that fails is reporting a failure to CERTIFY
a positive floor, not a violated inequality. HYP-3 freezes an instance where
the exact value is positive and no floor is certifiable, and requires the
machine-readable reason to say which of the two it is. This is a derived
observation about the contract, NOT a defect in it: a redundant hypothesis is
conservative, and stating (H3) separately is what lets prop:budget attach a
floor to it.

(H1), (H2) and (H4) DO fail independently, and the three cases exhibit points
where exactly one fails. (H4) is the only one with a repair the contract
licenses outright -- shrinking Ret -- because Ret is an implementation choice
and Lemma lem:mix-dom holds for every choice of it.

The four cases are in HYPOTHESIS_FAILURE_CASES.
""",
)

O_DUAL_SLACK_NOT_PSD = OracleEntry(
    oracle_id="O-DUAL-SLACK-NOT-PSD",
    claims=("C13", "C19"),
    kind="fail-closed",
    subject=(
        "Four dual witnesses whose slack is NOT PSD, each returning a "
        "beta_feas that EXCEEDS the true minimum mu(G) -- an unsound bound. "
        "The exact PSD check of Remark rem:dual-exact is the only thing that "
        "stops them."
    ),
    derivation="""\
contract.tex Theorem thm:weak-duality, whose conclusion is conditional on
"Slack_s >= 0 for every s", and Remark rem:dual-exact, which fixes how that
condition is decided: "The hypothesis Slack_s >= 0 is a statement about an
exactly represented Hermitian matrix; the reference verification is an exact
rational LDL^T/Cholesky factorization (a finite exact algorithm), and a sound
interval Cholesky under Assumption A-IA is an admissible substitute."

THE FOUR INSTANCES ARE ALREADY IN WEAK_DUALITY_CASES, flagged there by
slack_psd = False and sound = False; this entry names them as a group and
records what each one would cost:
  WD-T8T-slack-not-psd        bound 1.75  vs mu 1.625   overstated by 1/8
  WD-T8UN-slack-not-psd       bound 0.0   vs mu -1.0    overstated by 1
  WD-T5-succeq-slack-not-psd  bound 1.5   vs mu 1.0     overstated by 1/2
  WD-3REL-UN-slack-not-psd    bound 1.125 vs mu 0.125   overstated by 1
Every one of them is a number a certificate would happily consume as
beta_feas, and every one of them makes Eq. eq:hcert return an h_cert that is
NOT a lower bound on h_low. That is an unsound `certified` label, in the
unsafe direction, produced by arithmetic that is itself correct.

WHY EXACTNESS IS PART OF THE CHECK AND NOT A REFINEMENT OF IT. Three of the
four slacks above have a zero eigenvalue alongside the negative one, and
WD-T8T-slack-not-psd's slack is diag(0, -1). A floating-point symmetric
eigensolver on a slack assembled in floating point returns eigenvalues near
zero with sign noise; a tolerance generous enough to accept the legitimate
TIGHT witnesses -- whose slacks are exactly 0, and which the theorem must
accept -- is generous enough to accept these. The contract's answer is not a
better tolerance but exact rational arithmetic, where 0 and -1/2^k are
different numbers. This is the one exact-arithmetic obligation of the chain
that does NOT consume Assumption A-IA (rem:dual-exact says so; A-IA is
consumed only if an implementation substitutes a certified interval
factorization).

WHAT A FAILED SLACK CHECK MUST DO: the run falls back to `estimate` with a
machine-readable reason naming the failed check. It must NOT fall back to a
"best effort" bound computed from the same witness, and it must not search for
a nearby admissible witness silently -- a new witness is a new certificate and
re-enters the check chain.
""",
)

O_ACC_SIDE_UNSUPPORTED = OracleEntry(
    oracle_id="O-ACC-SIDE-UNSUPPORTED",
    claims=("C13", "C19"),
    kind="fail-closed",
    subject=(
        "An acceptance set fitting neither instantiation of Remark "
        "rem:acc-side supplies no beta_acc, so the run must forgo "
        "certification -- and the fall-back is `estimate`, not a guessed "
        "beta_acc."
    ),
    derivation="""\
contract.tex Remark rem:acc-side, third sentence: "Two instantiations are part
of this contract; a declaration whose AcceptSet fits neither must supply its
own certified bound or forgo certification (fail-closed)."

FROZEN VERDICTS, by declared acceptance-set geometry:
  singleton   -> instantiation (a) applies; beta_acc by evaluation (ACC-A-*)
  polytope    -> instantiation (b) applies; beta_acc by an admissible (u, v)
                 witness (ACC-B-*)
  anything else, e.g. a ball, an ellipsoid, a spectrahedron, or a set given
              only by a membership predicate
              -> NO beta_acc is derivable from this contract. The run emits
                 assurance = estimate with a machine-readable reason, unless
                 the declaration itself supplies a certified beta_acc as data.

WHY GUESSING IS NOT AVAILABLE. Assumption A-ACC asks only that AcceptSet be a
closed convex subset of the probability simplex. That is enough for the
convexity and attainment claims of C9b and for the MEAT hypothesis of C3, and
it is NOT enough to minimize a linear functional over it mechanically -- the
remark says as much: "whether it is computable is a property of the declared
representation, which is why Eq. eq:bacc-def is stated as an input obligation
rather than an algorithm." An implementation that fell back to, say, the
minimum of g over the whole simplex would be computing a bound on a LARGER
set, hence a SMALLER number, hence a sound but possibly vacuous beta_acc; that
would be conservative, but it would also be a bound this contract does not
state, and Eq. eq:bacc-def would no longer be the thing being checked. An
implementation that fell back to evaluating g at some interior point of
AcceptSet would be computing an UPPER bound on the minimum -- unsound.

RELATIONSHIP TO THE 0.3.0 FINDING F-04. The Round-1 implementation review
recorded that only singleton acceptance sets were implemented, and judged the
narrowing acceptable because it was DISCLOSED in every optimizer_certificate
under scope_narrowings rather than applied silently. The same discipline is
what this entry asks of the certificate path: the unsupported geometry is
reported, not worked around.

THE ESTIMATE PATH IS UNAFFECTED. h_low is computed from the declaration
exactly as before; only the certificate is withheld. A declaration whose
acceptance geometry is unsupported still produces a perfectly good
estimate-tier result, which is the whole reason the fall-back is a downgrade
and not an error.
""",
    value=ASSURANCE,
)

O_ASSURANCE_CERTIFIED_GATE = OracleEntry(
    oracle_id="O-ASSURANCE-CERTIFIED-GATE",
    claims=("C13",),
    kind="fail-closed",
    subject=(
        "assurance = certified EXACTLY when the requested assurance was "
        "certified AND all four check groups of Section 4.18 passed; "
        "estimate otherwise, with a machine-readable reason. Never silently "
        "upgraded; never downgraded without the reason."
    ),
    derivation="""\
contract.tex Section 2.2 (the optimizer_certificate row), Section 2.4 (the
requested_assurance parameter) and Remark rem:cert-interface. This is the
entry that says when `certified` MAY be emitted; the four entries beside it
say when it must not.

THE GATE, in the contract's own order:
  requested_assurance = estimate
    -> assurance = estimate, ALWAYS. The certificate post-processing is not
       run and the achieved assurance "is never silently upgraded". An
       implementation that noticed all checks would have passed and upgraded
       anyway has violated the parameter's contract, even though the label
       would have been true.
  requested_assurance = certified
    -> run the SAME solver (the certificate is a post-processing; Section 2.4
       says "same solver either way"), then check, in this order:
       (1) x in D on the ROUNDED EXACT point (Eq. eq:cert-domain);
       (2) (H1)-(H4) with their certified floors;
       (3) the slack PSD verifications of Theorem thm:weak-duality;
       (4) the enclosure assembly of Proposition prop:budget.
       ALL FOUR pass -> assurance = certified, and the record carries the full
       witness payload of rem:cert-interface (the certificate point x as exact
       machine data, Chat_acc, delta, Ret, the floors, the truncation orders,
       the surrogate, the dual witness, beta_acc, beta_feas, eps_acc,
       eps_feas, h_cert) -- "sufficient for independent re-verification
       without re-running the solver".
       ANY failure -> assurance = estimate with a machine-readable reason
       naming the failed or unrequested check (ARCHITECTURE_SPEC.md 3.5).

THE PARITY RULE, new at 0.4.0 and easy to miss. Remark rem:cert-interface
closes by binding the certified path to Remark rem:hlow-range: when
h_low = +infinity -- no feasible statistics compatible with AcceptSet -- an
implementation emits NO key-length claim, "and a finite h_cert does not
restore one (h_cert <= +infinity holds trivially while the accepted state that
Theorem thm:accumulated-entropy conditions on is null)". So a run on TOY-4c, whose frozen
h_low is +inf (O-HLOW-INFINITE), must emit no key length even if every
certificate check passes and h_cert comes back finite and positive. The
certificate bounds the RATE; it says nothing about whether the accepted event
has any probability.

WHAT THE LABEL IS NOT. h_low remains ESTIMATE-tier information on a certified
run -- the contract says so directly -- and key_length on such a run is
computed from h_cert via Corollary cor:cert-keylength, not from h_low. So a
result carrying assurance = certified reports a certified length derived from
h_cert and an estimate-tier h_low side by side; conflating them, or reporting
the h_low-derived length under a certified label, overstates the key by
exactly the gap this registry's CERT-* cases freeze (171 bits at n = 1000 in
CKL-1).
""",
    value="certified",
    # MARKED BY THE 0.5.0 AMENDMENT. Its subject states a BICONDITIONAL --
    # "certified EXACTLY when the requested assurance was certified AND all
    # four check groups of Section 4.18 passed" -- and contract.tex 0.5.0
    # falsifies it: Remark rem:optol-interface (4) forces `estimate` on the
    # tolerance branch "regardless of the requested assurance", whatever the
    # four groups would say. Nothing below the biconditional changed and no
    # number here moved. See SUPERSEDED_BY_0_5_0 and
    # O-OPTOL-ASSURANCE-FORCED-ESTIMATE.
    superseded_by="0.5.0",
)


# ===========================================================================
#  Group 8 -- the polytope acceptance oracle: the PRIMAL minimum (C19)
# ===========================================================================
#
#  A later implementation band under the SAME accepted
#  contract 0.4.0. See the module docstring, "GROUP 8", for the band's
#  authorization and for why the primal minimum is pinned separately from the
#  dual bound Group 7 already froze.
#
#  ROW ORDER, fixed once for every canonical box below and never restated in a
#  case. With m = |Chat_acc| and the declaration's own enumeration
#  c^(1), ..., c^(m), the canonical box form of `statistics-acceptance` 0.1.2
#  carries m_row = 2m rows:
#      row i      :  +e_i^T q <=  q^+(c^(i))     (the caps)
#      row m + i  :  -e_i^T q <= -q^-(c^(i))     (the floors)
#  Row indices are INTEGERS, never alphabet elements. The dual vector u below
#  is written in that same row order, so its first m entries multiply the caps
#  and its last m the floors -- which is why a floor multiplier enters
#  -<b, u> - v with the sign it does.


@dataclass(frozen=True)
class PolytopeMinimumCase:
    """One hand-derived primal minimum of ``<g, q>`` over a declared polytope."""

    case_id: str
    #: The declaration's enumeration of ``Chat_acc``, in order.
    outcomes: tuple[str, ...]
    #: The exact vector ``g`` of Eq. ``eq:bacc-def``, in ``outcomes`` order.
    g: tuple[float, ...]
    #: ``(q^-, q^+)`` when the geometry is in canonical box form, else None.
    #: A None here means the rows below are the whole of the data and no
    #: box-shaped closed form may be applied to it.
    box_bounds: tuple[tuple[float, ...], tuple[float, ...]] | None
    #: ``B`` of Remark ``rem:acc-side`` (b), rows in integer index order.
    rows: tuple[tuple[float, ...], ...]
    #: ``b`` of Remark ``rem:acc-side`` (b), in the same row order.
    rhs: tuple[float, ...]
    #: ``min <g, q'>`` over the polytope. Derived BY HAND; see ``arithmetic``.
    minimum: float
    #: Every minimizer this entry pins: one point when the argmin is unique,
    #: and the VERTICES of the argmin face when it is not.
    minimizers: tuple[tuple[float, ...], ...]
    #: ``u`` of Remark ``rem:acc-side`` (b), in row order.
    dual_u: tuple[float, ...]
    #: ``v`` of Remark ``rem:acc-side`` (b).
    dual_v: float
    #: ``-<b, u> - v``. Equals ``minimum`` in every case below: each witness is
    #: tight, and the agreement is a CHECK on the hand value, not its source.
    dual_value: float
    #: ``min_chat g(chat)``: the minimum over the WHOLE simplex, i.e. with the
    #: polytope rows dropped. Never above ``minimum``.
    simplex_relaxation: float
    #: A feasible NON-optimal point, when the set has one. Its value is ABOVE
    #: the minimum and is therefore an UNSOUND ``beta_acc``.
    feasible_point: tuple[float, ...] | None
    feasible_point_value: float | None
    arithmetic: str


POLYTOPE_MINIMUM_CASES: tuple[PolytopeMinimumCase, ...] = (
    PolytopeMinimumCase(
        case_id="PMIN-box-interior",
        outcomes=("c0", "c1", "c2"),
        g=(0.5, 1.5, 4.0),
        box_bounds=((0.125, 0.125, 0.125), (0.5, 0.75, 1.0)),
        rows=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, -1.0),
        ),
        rhs=(0.5, 0.75, 1.0, -0.125, -0.125, -0.125),
        minimum=1.3125,
        minimizers=((0.5, 0.375, 0.125),),
        dual_u=(1.0, 0.0, 0.0, 0.0, 0.0, 2.5),
        dual_v=-1.5,
        dual_value=1.3125,
        simplex_relaxation=0.5,
        feasible_point=(0.125, 0.125, 0.75),
        feasible_point_value=3.25,
        arithmetic="""\
A CANONICAL BOX ON THREE OUTCOMES, and the case where the fill stops STRICTLY
INSIDE one coordinate's range -- neither at its floor nor at its cap.
  Chat_acc = (c0, c1, c2) , g = (1/2, 3/2, 4) ,
  q^- = (1/8, 1/8, 1/8) , q^+ = (1/2, 3/4, 1) .
NON-EMPTY: sum q^- = 3/8 <= 1 <= 9/4 = sum q^+.
ROUTE 1, the exchange argument. Order the outcomes by g ascending (they
already are) and fill from the cheapest. The residual mass above the floors is
r = 1 - 3/8 = 5/8; the widths are D = (3/8, 5/8, 7/8); the cheapest outcome
absorbs only D_0 = 3/8 of r, and the next takes the remaining
5/8 - 3/8 = 1/4, strictly less than its own width 5/8. So
  q_opt = (1/2, 1/8 + 1/4, 1/8) = (1/2, 3/8, 1/8) , sum q_opt = 1 ,
  min <g, q> = (1/2)(1/2) + (3/2)(3/8) + 4(1/8)
             = 1/4 + 9/16 + 1/2 = 21/16 = 1.3125 .
Optimality in one line: for any feasible q, with lambda = 3/2 the cost at the
split and sum_i (q_i - q_opt,i) = 0,
  <g,q> - <g,q_opt> = sum_i (g_i - lambda)(q_i - q_opt,i) >= 0 ,
because below the split g_i - lambda <= 0 while q_i <= q^+_i = q_opt,i, above
it g_i - lambda >= 0 while q_i >= q^-_i = q_opt,i, and at the split the first
factor is zero.
ROUTE 2, elimination, run independently of Route 1. Put c = 1 - a - b. The
objective becomes 4 - (7/2)a - (5/2)b, so minimizing it is maximizing
(7/2)a + (5/2)b subject to a <= 1/2, b <= 3/4 and a + b <= 7/8 (the last from
c >= 1/8). The larger coefficient sits on a, so a = 1/2 and then
b <= 7/8 - 1/2 = 3/8:
  max = 7/4 + 15/16 = 43/16 ,   min = 4 - 43/16 = 21/16 .
The two routes agree, and the minimizer is unique because the coefficients are
distinct and both binding constraints are.
WITNESS, in the format Remark rem:acc-side (b) requires. lambda = 3/2,
v = -3/2, and u >= 0 with one entry per row:
  caps   u = (1, 0, 0) ,   floors u = (0, 0, 5/2) .
Then (B^T u)(chat) = u_cap(chat) - u_floor(chat) and
  g + B^T u + v.1 = (1/2 + 1 - 3/2, 3/2 + 0 - 3/2, 4 - 5/2 - 3/2)
                  = (0, 0, 0) >= 0 ,
which is the admissibility condition, and
  -<b, u> - v = -[(1/2)(1) + (-1/8)(5/2)] + 3/2 = -3/16 + 3/2 = 21/16 ,
the primal minimum again. THE WITNESS IS A CROSS-CHECK, NOT THE DERIVATION.
SANDWICH. Dropping the box rows leaves the whole simplex, whose minimum is
min_chat g(chat) = 1/2 -- a sound beta_acc, loose by 13/16. Evaluating g at
the feasible point (1/8, 1/8, 3/4) gives 13/4, ABOVE the minimum and
therefore an UNSOUND beta_acc.""",
    ),
    PolytopeMinimumCase(
        case_id="PMIN-box-spillover",
        outcomes=("c0", "c1", "c2"),
        g=(-1.0, 0.5, 2.0),
        box_bounds=((0.0, 0.0, 0.0), (0.75, 0.75, 0.75)),
        rows=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, -1.0),
        ),
        rhs=(0.75, 0.75, 0.75, 0.0, 0.0, 0.0),
        minimum=-0.625,
        minimizers=((0.75, 0.25, 0.0),),
        dual_u=(1.5, 0.0, 0.0, 0.0, 0.0, 1.5),
        dual_v=-0.5,
        dual_value=-0.625,
        simplex_relaxation=-1.0,
        feasible_point=(0.5, 0.5, 0.0),
        feasible_point_value=-0.25,
        arithmetic="""\
THE SIMPLEX NORMALIZATION IS WHAT BINDS. Three outcomes, floors at zero:
  g = (-1, 1/2, 2) , q^- = (0, 0, 0) , q^+ = (3/4, 3/4, 3/4) .
NON-EMPTY: 0 <= 1 <= 9/4.
ROUTE 1, the exchange argument. r = 1, and the cheapest outcome is capped at
3/4 < 1, so its cap alone cannot carry the normalization: exactly
1 - 3/4 = 1/4 SPILLS onto the second cheapest, and nothing reaches the third.
  q_opt = (3/4, 1/4, 0) ,  min = -3/4 + 1/8 + 0 = -5/8 = -0.625 .
ROUTE 2, elimination. c = 1 - a - b turns the objective into 2 - 3a - (3/2)b;
maximize 3a + (3/2)b with a, b <= 3/4, a + b >= 1/4 (from c <= 3/4) and
a + b <= 1 (from c >= 0). Take a = 3/4, then b <= 1/4:
  max = 9/4 + 3/8 = 21/8 ,   min = 2 - 21/8 = -5/8 .
The routes agree; the minimizer is unique.
WITNESS: lambda = 1/2, v = -1/2, caps u = (3/2, 0, 0), floors u = (0, 0, 3/2).
  g + B^T u + v.1 = (-1 + 3/2 - 1/2, 1/2 + 0 - 1/2, 2 - 3/2 - 1/2)
                  = (0, 0, 0) >= 0 ,
  -<b, u> - v = -(3/4)(3/2) + 1/2 = -9/8 + 1/2 = -5/8 ,
the floors contributing nothing because their right-hand sides are -q^- = 0.
WHY THIS CASE EXISTS. An implementation that minimizes over the BOX ALONE,
forgetting sum q = 1, returns (-1)(3/4) = -3/4: SMALLER than the true minimum,
hence still a sound beta_acc, and wrong -- it is the minimum of a set the
declaration never named. One that keeps the simplex and forgets the box
returns min_chat g(chat) = -1, sound and looser still. Both errors are
conservative, and neither is visible in the sign of h_cert; that is why the
VALUE is frozen and not merely its direction. The unsound direction is
available too: the feasible point (1/2, 1/2, 0) gives -1/4 > -5/8.""",
    ),
    PolytopeMinimumCase(
        case_id="PMIN-box-singleton",
        outcomes=("c0", "c1"),
        g=(2.0, -1.0),
        box_bounds=((0.5, 0.5), (0.5, 0.5)),
        rows=(
            (1.0, 0.0),
            (0.0, 1.0),
            (-1.0, 0.0),
            (0.0, -1.0),
        ),
        rhs=(0.5, 0.5, -0.5, -0.5),
        minimum=0.5,
        minimizers=((0.5, 0.5),),
        dual_u=(0.0, 0.0, 3.0, 0.0),
        dual_v=1.0,
        dual_value=0.5,
        simplex_relaxation=-1.0,
        feasible_point=None,
        feasible_point_value=None,
        arithmetic="""\
A SINGLETON WRITTEN AS A BOX, on exactly the data ACC-A-singleton freezes for
instantiation (a):
  Chat_acc = (c0, c1) , g = (2, -1) , q^- = q^+ = (1/2, 1/2) .
NON-EMPTY, and at both ends of the closed-form predicate at once:
sum q^- = 1 <= 1 <= 1 = sum q^+, each with EQUALITY. The denotation is the
single point {(1/2, 1/2)}, so the minimum is an evaluation:
  min <g, q> = 2(1/2) + (-1)(1/2) = 1 - 1/2 = 1/2 ,
THE SAME NUMBER ACC-A-singleton pins by route (a). That agreement is the
subject of O-POLYTOPE-SINGLETON-AGREEMENT.
THE DEGENERATE FILL, written out because it is where an implementation runs
off the end of its loop: r = 1 - 1 = 0, every width is D_i = 0, and the least
index whose prefix width reaches r is the FIRST one, since 0 >= 0. The fill
increment is w = 0 and q_opt = q^-. An implementation that looks for the least
index with a STRICT inequality finds none here.
WITNESS: the cost at the split is lambda = g(c1) = -1 (c1 is the cheaper
outcome and heads the g-ascending order), v = 1, caps u = (0, 0), floors
u = (3, 0):
  g + B^T u + v.1 = (2 - 3 + 1, -1 + 0 + 1) = (0, 0) >= 0 ,
  -<b, u> - v = -[(-1/2)(3)] - 1 = 3/2 - 1 = 1/2 .
SANDWICH: the simplex relaxation gives min_chat g(chat) = -1, sound and loose
by 3/2. There is NO feasible non-optimal point -- the set is one point -- so
no unsound evaluation exists inside it, which is exactly why a singleton needs
no minimization to be certified.""",
    ),
    PolytopeMinimumCase(
        case_id="PMIN-box-support-superset",
        outcomes=("c0", "c1", "c2"),
        g=(2.0, -1.0, 5.0),
        box_bounds=((0.5, 0.5, 0.0), (0.5, 0.5, 0.25)),
        rows=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, -1.0),
        ),
        rhs=(0.5, 0.5, 0.25, -0.5, -0.5, 0.0),
        minimum=0.5,
        minimizers=((0.5, 0.5, 0.0),),
        dual_u=(0.0, 0.0, 0.0, 3.0, 0.0, 6.0),
        dual_v=1.0,
        dual_value=0.5,
        simplex_relaxation=-1.0,
        feasible_point=None,
        feasible_point_value=None,
        arithmetic="""\
A NON-DEGENERATE BOX WHOSE DENOTATION IS STILL ONE POINT -- the case that
separates the two acceptance supports.
  g = (2, -1, 5) , q^- = (1/2, 1/2, 0) , q^+ = (1/2, 1/2, 1/4) .
NON-EMPTY: sum q^- = 1 <= 1 <= 5/4 = sum q^+. But the floors already exhaust
the normalization, so every feasible q equals q^-:
  q_opt = (1/2, 1/2, 0) ,  min <g, q> = 1 - 1/2 + 0 = 1/2 .
Both routes are immediate here and agree: the fill has r = 0 and returns q^-,
and elimination leaves a feasible set with one point.
THE POINT OF THE CASE. q^+(c2) = 1/4 > 0, so the acceptance support
{chat : q^+(chat) > 0} = {c0, c1, c2} STRICTLY CONTAINS the union of the
supports of the feasible points, {c0, c1}. The contract asks of an acceptance
support only that supp q be inside it for every q in AcceptSet, records the
union as the minimal choice, and says in as many words that "any admissible
superset may be used". So a Chat_acc carrying c2 is CONFORMING, not a defect,
and the two choices give the SAME minimum because q(c2) = 0 identically on the
set. An implementation that rejects the larger support, or that computes a
different minimum from it, has read the definition as demanding minimality.
The consequence reaches further than this entry: the certificate's domain
condition supp q~ inside Chat_acc, and the sums over Chat_acc in eq:bacc-def
and eq:Owork, are all stated for a support that need not be minimal.
WITNESS: lambda = -1, v = 1, caps u = (0, 0, 0), floors u = (3, 0, 6):
  g + B^T u + v.1 = (2 - 3 + 1, -1 - 0 + 1, 5 - 6 + 1) = (0, 0, 0) >= 0 ,
  -<b, u> - v = -[(-1/2)(3) + (-1/2)(0) + (0)(6)] - 1 = 3/2 - 1 = 1/2 .
The c2 floor multiplier is 6 and contributes NOTHING, its right-hand side
being -q^-(c2) = 0: a large multiplier on a costless row, which is legal and
is the shape an implementation that expects small u will get wrong.
SANDWICH: simplex relaxation -1; no feasible non-optimal point exists.""",
    ),
    PolytopeMinimumCase(
        case_id="PMIN-box-tie",
        outcomes=("c0", "c1", "c2"),
        g=(1.0, 1.0, 3.0),
        box_bounds=((0.0, 0.0, 0.0), (0.75, 0.75, 0.75)),
        rows=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, -1.0),
        ),
        rhs=(0.75, 0.75, 0.75, 0.0, 0.0, 0.0),
        minimum=1.0,
        minimizers=((0.75, 0.25, 0.0), (0.25, 0.75, 0.0)),
        dual_u=(0.0, 0.0, 0.0, 0.0, 0.0, 2.0),
        dual_v=-1.0,
        dual_value=1.0,
        simplex_relaxation=1.0,
        feasible_point=(0.25, 0.25, 0.5),
        feasible_point_value=2.0,
        arithmetic="""\
TIED COSTS: THE VALUE IS UNIQUE AND THE MINIMIZER IS NOT.
  g = (1, 1, 3) , q^- = (0, 0, 0) , q^+ = (3/4, 3/4, 3/4) .
ROUTE 1, and it needs no elimination: on the simplex
  <g, q> = (q0 + q1 + q2) + 2 q2 = 1 + 2 q2 ,
so minimizing <g, q> is minimizing q2. The value q2 = 0 is attainable --
q0 + q1 = 1 with both at most 3/4 needs only q0 in [1/4, 3/4] -- hence
  min <g, q> = 1 ,
and the ARGMIN IS THE WHOLE SEGMENT {(a, 1-a, 0) : 1/4 <= a <= 3/4}. Its two
endpoints (3/4, 1/4, 0) and (1/4, 3/4, 0) are the frozen minimizers; every
convex combination of them attains the same value.
ROUTE 2, the exchange-argument fill, run under BOTH tie-breaks: r = 1 and the
widths are 3/4 each, so with c0 first it returns (3/4, 1/4, 0) and with c1
first (1/4, 3/4, 0). Different points, the same value 1, and the same
lambda = 1, because the tie is a tie in g. A test that asserts the ARGMIN
rather than the VALUE therefore pins the sort's stability, which no contract
fixes; the value is what the certificate consumes.
WITNESS: lambda = 1, v = -1, caps u = (0, 0, 0), floors u = (0, 0, 2):
  g + B^T u + v.1 = (1 + 0 - 1, 1 + 0 - 1, 3 - 2 - 1) = (0, 0, 0) >= 0 ,
  -<b, u> - v = -0 + 1 = 1 ,
the floors again carrying right-hand side 0.
SANDWICH, and the second reason this case exists: min_chat g(chat) = 1 EQUALS
the minimum here, although the relaxed minimizer (1, 0, 0) is NOT feasible --
it exceeds q^+(c0) = 3/4. So a tight relaxation bound does not certify a
feasible minimizer, and agreement between the two numbers is NOT evidence that
the box rows were read at all. The feasible point (1/4, 1/4, 1/2) gives 2, an
unsound beta_acc.""",
    ),
    PolytopeMinimumCase(
        case_id="PMIN-general-row",
        outcomes=("c0", "c1", "c2"),
        g=(-2.0, 1.0, 3.0),
        box_bounds=None,
        rows=((1.0, 1.0, 0.0),),
        rhs=(0.5,),
        minimum=0.5,
        minimizers=((0.5, 0.0, 0.5),),
        dual_u=(5.0,),
        dual_v=-3.0,
        dual_value=0.5,
        simplex_relaxation=-2.0,
        feasible_point=(0.0, 0.0, 1.0),
        feasible_point_value=3.0,
        arithmetic="""\
A POLYTOPE THAT IS NOT A BOX. Remark rem:acc-side (b) asks only for an exact
B and b, and the geometry taxonomy admits any (m_row, B, b) with the canonical
box as a SUB-form. Three outcomes, ONE row:
  g = (-2, 1, 3) , m_row = 1 , B = [[1, 1, 0]] , b = (1/2) ,
i.e. the single cut q(c0) + q(c1) <= 1/2. It touches two coordinates, so it is
not of the row shape a canonical box has, and NO box-shaped closed form
applies: neither the feasibility test sum q^- <= 1 <= sum q^+ nor the greedy
fill. Both are statements about a box, and using either here would be reading
a theorem outside its own hypothesis.
NON-EMPTY: q = (0, 0, 1) satisfies the row (0 <= 1/2) and lies in the simplex.
THE MINIMUM, by elimination -- the only route available, the fill being
inapplicable. Put c = 1 - a - b; the objective -2a + b + 3c becomes
3 - 5a - 2b, so minimize it by maximizing 5a + 2b subject to a + b <= 1/2 and
a, b >= 0. The larger coefficient is on a, so the whole budget goes there:
  a = 1/2 , b = 0 , max = 5/2 ,  min <g, q> = 3 - 5/2 = 1/2 ,
attained at q_opt = (1/2, 0, 1/2), which is feasible (1/2 <= 1/2) and unique
because 5 > 2 > 0 leaves no tie.
THE DUAL, DERIVED RATHER THAN QUOTED, there being no closed form to lean on.
With one row the admissibility condition g + B^T u + v.1 >= 0 reads
  u + v >= 2 ,   u + v >= -1 ,   v >= -3 ,   u >= 0 ,
and the bound to maximize is -u/2 - v. For u <= 5 the binding condition is
v = 2 - u, giving u/2 - 2, increasing in u; for u >= 5 it is v = -3, giving
3 - u/2, decreasing. They meet at u = 5, v = -3, where
  g + B^T u + v.1 = (-2 + 5 - 3, 1 + 5 - 3, 3 + 0 - 3) = (0, 3, 0) >= 0 ,
  -<b, u> - v = -(1/2)(5) + 3 = 1/2 ,
equal to the primal minimum -- so the witness is tight here too, but by an
argument made for THIS polytope and not by any general theorem this registry
states. Note the middle slack is 3 and not 0: a tight witness need not
annihilate every coordinate, only those the optimum charges.
SANDWICH: the simplex relaxation is min_chat g(chat) = -2, sound and loose by
5/2; the feasible point (0, 0, 1) gives 3, unsound.""",
    ),
)

O_POLYTOPE_ACC_MINIMUM = OracleEntry(
    oracle_id="O-POLYTOPE-ACC-MINIMUM",
    claims=("C19",),
    kind="toy-instance",
    subject=(
        "The PRIMAL minimum min <g, q'> over a declared polytope acceptance "
        "set -- the right-hand side of Eq. eq:bacc-def, instantiation (b) -- "
        "hand-derived on 2- and 3-outcome alphabets by two independent "
        "routes, with the tight (u, v) witness as a third check."
    ),
    derivation="""\
contract.tex Remark rem:acc-side, Eq. eq:bacc-def: the certificate consumes a
number beta_acc with
  beta_acc <= min_{q' in AcceptSet} sum_{chat in Chat_acc} g(chat) q'(chat)
for a given exact vector g. THIS ENTRY PINS THE RIGHT-HAND SIDE -- the primal
minimum itself -- for instantiation (b), the polytope
  AcceptSet = { q : q >= 0 , sum_chat q(chat) = 1 , B q <= b } .

WHY IT IS SEPARATE FROM O-BETA-ACC. That entry pins the DUAL side: the number
-<b, u> - v that an admissible (u, v) certifies, together with what happens
when the admissibility condition is skipped. The two are different obligations
and an implementation can satisfy the second while getting the first wrong: a
loose witness is sound, so no dual check can reveal a minimum computed too
small, and a minimum computed too LARGE is exactly the unsound direction. The
minimum is therefore frozen here in its own right, on its own toys.

WHAT THIS ENTRY DOES AND DOES NOT AUTHORIZE. The contract states eq:bacc-def
as an INPUT OBLIGATION and says so in as many words: "whether it is computable
is a property of the declared representation, which is why Eq. eq:bacc-def is
stated as an input obligation rather than an algorithm". So nothing here
obliges an implementation to compute the minimum, and nothing here licenses
feeding a self-computed minimum to the certificate WITHOUT the admissibility
check of instantiation (b) -- the componentwise test on g + B^T u + v is what
makes a number certified, and ACC-B-polytope-condition-violated already
freezes what skipping it costs. What this entry fixes is the TRUE VALUE, so
that a disagreement is a finding rather than a matter of opinion.

THE COORDINATE RESTRICTION, unchanged from O-BETA-ACC and restated because one
case below turns on it: B has |Chat_acc| columns, the sum runs over Chat_acc
only, and Chat_acc is ANY set containing supp q for every q in AcceptSet --
the minimal choice being the union of those supports, with "any admissible
superset may be used". PMIN-box-support-superset is the case where the
declared support and the minimal one differ.

HOW EVERY NUMBER WAS OBTAINED. By hand, twice, by routes sharing no step.
(1) An exchange argument: order the outcomes by g ascending, fill the cheapest
first from the floors upward, and verify optimality from the identity
  <g,q> - <g,q_opt> = sum_i (g_i - lambda)(q_i - q_opt,i) ,
with lambda the cost at the split, every summand of which is non-negative.
(2) Elimination of one coordinate through sum q = 1, which turns the objective
into an affine function of the rest and the problem into maximizing it over an
explicit box. Each case records both, and then exhibits a (u, v) witness whose
value is compared with the result: that agreement is a THIRD check and never
the source of a number.

AGREEMENT WITH `statistics-acceptance`, recorded as a cross-check. That
module's accepted contract 0.1.2 proves a closed form for the minimum over a
canonical box (its Theorem thm:box-oracle), by the same exchange argument and with a
witness of the same shape, and it states there that the resulting bound is
TIGHT for a box. Five of the six cases below are canonical boxes and its
closed form agrees with the hand value in each. Two documents deriving the
same numbers independently is evidence; it is not this registry's derivation,
and no case takes its value from it. The sixth case is deliberately NOT a box,
so that nothing in this group depends on that closed form applying.

WHAT THE SANDWICH COLUMNS ARE FOR. Each case carries the minimum over the
WHOLE simplex (the rows dropped) and, where one exists, a feasible NON-optimal
point. They bracket the frozen value from both sides and name the two ways an
implementation goes wrong: relaxing the declared set gives a smaller number,
which stays sound as a beta_acc but is no longer the declared minimum;
evaluating at a feasible point that is not optimal gives a LARGER number,
which is unsound and raises h_cert.

EXACTNESS. Every g, q^-, q^+, b, minimum and witness entry below is a dyadic
rational of denominator at most 16, so each is a binary64 number exactly and
the downward rounding of Section 2.5 is a no-op on it. These cases pin the
FORMULA; the rounding direction is pinned separately by ACC-A-singleton-
rounded, and nothing here relaxes it.

The six cases are in POLYTOPE_MINIMUM_CASES.
""",
    hypotheses=(
        "A-ACC: AcceptSet is a closed convex subset of the simplex on Chat.",
        "rem:acc-side (b): B and b are EXACT machine data, with columns "
        "indexed by Chat_acc.",
        "The declared polytope is NON-EMPTY. The empty case carries no "
        "acceptance-side information at all and is O-POLYTOPE-EMPTY-FAIL-"
        "CLOSED.",
    ),
)

O_POLYTOPE_SINGLETON_AGREEMENT = OracleEntry(
    oracle_id="O-POLYTOPE-SINGLETON-AGREEMENT",
    claims=("C19",),
    kind="structural-identity",
    subject=(
        "A singleton acceptance set expressed as a polytope returns the SAME "
        "acceptance-side minimum as instantiation (a) -- 1/2 on the frozen "
        "ACC-A-singleton data -- so the two routes of Remark rem:acc-side may "
        "not disagree on a set that is both."
    ),
    derivation="""\
contract.tex Remark rem:acc-side offers two instantiations of ONE quantity,
Eq. eq:bacc-def. A set that qualifies as both must therefore receive one
answer, and this entry freezes that answer on data an earlier band already
froze:
  Chat_acc = {c0, c1} , g = (2, -1) , q* = (1/2, 1/2) ,
  route (a), ACC-A-singleton : <g, q*> = 1 + (-1/2) = 1/2 ;
  route (b), PMIN-box-singleton : the canonical box q^- = q^+ = q* denotes
             {q*}, and its minimum, derived independently there, is 1/2 .
Same number, and it must stay the same number: beta_acc enters Eq. eq:hcert
with a PLUS sign, so two routes returning two values would give one
declaration two certified bounds, and the larger of them would be the unsound
one.

WHY THIS DESERVES AN ENTRY rather than an assertion inside a case. The
degenerate box is where a closed-form fill is most likely to be wrong. The
residual mass is r = 0, every width is D_i = 0, and the rule "the least j with
sum_{i<=j} D_i >= r" is satisfied at the FIRST index by 0 >= 0. An off-by-one
-- looking for a STRICT inequality, or for the last such index -- finds no
index at all here, and an implementation that then returns a floor vector, or
raises, has broken a case both contracts call supported. The value 1/2 is
small, exact, and shared with an entry frozen in a previous band, so a
disagreement is visible immediately and cannot be argued away as tolerance.

THE SECOND CONSISTENCY PAIR is PMIN-box-support-superset, whose box is NOT
degenerate -- its third coordinate has width 1/4 -- and whose denotation is
nevertheless a single point. It returns the same 1/2. Together the two cases
say that the agreement is a property of the DENOTATION and not of the
representation happening to be degenerate: an implementation may not decide
which route to run by inspecting whether q^- equals q^+.

NOTHING HERE MAKES THE SINGLETON TAG REDUNDANT. Both instantiations remain
part of the contract, and the singleton route stays the cheaper one: it is an
evaluation rather than a minimization, and its validation predicate is a
membership test rather than a feasibility question.
""",
    value=0.5,
)

O_POLYTOPE_EMPTY_FAIL_CLOSED = OracleEntry(
    oracle_id="O-POLYTOPE-EMPTY-FAIL-CLOSED",
    claims=("C8", "C13", "C19"),
    kind="fail-closed",
    subject=(
        "A declared polytope whose denotation is EMPTY -- or whose canonical "
        "box data is ill-formed -- is refused: no beta_acc is derivable from "
        "it, no certificate may be emitted, and the conforming h_low is +inf "
        "with NO key-length claim."
    ),
    derivation="""\
THE HAZARD, stated first because it is not obvious. Assumption A-ACC asks that
AcceptSet be a closed convex subset of the probability simplex, and THE EMPTY
SET IS ONE: closed, convex, and a subset. So an empty acceptance set does not
violate A-ACC. Worse, Eq. eq:bacc-def is then VACUOUS -- a minimum over an
empty set is +inf under the usual convention, so EVERY real number satisfies
beta_acc <= min, including numbers that make h_cert as large as one likes. And
the check that protects the certificate on every non-empty polytope, the
componentwise test g + B^T u + v >= 0, passes here for suitable (u, v) exactly
as it would otherwise: it is a condition on g, B and v alone and says nothing
about whether any q satisfies B q <= b. An empty acceptance set is therefore
the one input on which the acceptance side of the certificate carries no
information at all.

THE CONFORMING BEHAVIOUR, which the contract already fixes. Eq. eq:hlow-def
defines h_low as an infimum over q in AcceptSet of an infimum over Feas; with
AcceptSet empty the outer infimum is over nothing, and Remark rem:hlow-range
states the case directly -- "h_low = +inf whenever no (q, omega) with
q << Phi[omega] is feasible" -- with the output domain declared as the
EXTENDED reals precisely so the value can be reported. Its fail-closed branch
governs the rest: "if h_low = +inf reaches Theorem thm:keylength, the
conforming behaviour is to emit NO key-length claim and report the
declaration/acceptance mismatch". Remark rem:cert-interface binds the
certified path to the same rule -- "a finite h_cert does not restore" a
key-length claim -- so the certificate cannot be used to walk around it. The
human record of the G3 signature on 0.4.0 settles the reading explicitly
(STATUS.yaml gates.g3, judgement call (4)): an empty acceptance set is treated
as the h_low = +inf branch of rem:hlow-range, fail-closed, and NEVER as a
certificate.

WHERE THE REFUSAL BELONGS, and why this entry exists anyway. Upstream, at
validation: the accepted `statistics-acceptance` contract 0.1.2 makes
non-emptiness the VALIDATION PREDICATE of the geometry -- for a polytope,
rational feasibility of {q >= 0, sum q = 1, B q <= b}; for a canonical box,
equivalently the closed form sum q^- <= 1 <= sum q^+ -- so an empty polytope is
not an admissible geometry and should never reach an oracle. This entry pins
what must happen if one does, which is the case that matters: the producer and
the consumer are separate modules with separate contracts, and a consumer that
trusts its producer has no defence when the producer is wrong.

FROZEN VERDICTS. In every case below the denotation is EMPTY, no beta_acc is
derivable, no certificate may be emitted, and the conforming h_low is +inf
with no key-length claim:
  INFEAS-box-caps-below-one          sum q^+ = 3/4 < 1
  INFEAS-box-floors-above-one        sum q^- = 3/2 > 1
  INFEAS-rows-contradict-simplex     one row sum_chat q(chat) <= 1/2
  INFEAS-rows-contradict-each-other  two rows summing to 0 <= -1/2
  ILLFORMED-box-inverted             q^-(c0) = 3/4 > 1/4 = q^+(c0)
Each carries its own certificate of emptiness in `emptiness_witness`, so every
verdict is checkable by substitution rather than by solving anything.

TWO DISTINCT REFUSALS, WHICH MUST NOT BE COLLAPSED. ILLFORMED-box-inverted
fails WELL-FORMEDNESS: a canonical box requires 0 <= q^- <= q^+, so this data
is not a canonical box and the closed-form emptiness test does not apply to
it. Applied anyway it reports sum q^- = 3/4 <= 1 <= 9/4 = sum q^+ and PASSES,
which is the trap the case exists to expose. The other four are well-formed
data denoting an empty set. A validation path that runs the closed-form test
without first checking 0 <= q^- <= q^+ admits the inverted box and then
computes a fill from widths that are NEGATIVE.

WHAT THIS ENTRY DOES NOT FIX. It does not name a machine-readable reason code.
contract.tex Section 2.2 requires "a machine-readable reason naming the failed
or unrequested check" and fixes no vocabulary of codes, so this registry
invents none -- the handling the 0.4.0 interface.yaml already gave the witness
payload's per-item keys. What is frozen is the VERDICT and the tier, not any
string.

INADMISSIBLE ALTERNATIVES, spelled out because each is locally reasonable.
Returning beta_acc = -inf as a "safe" bound writes a number the contract does
not define into the witness payload, and produces h_cert = -inf where the
contract asks for a refusal. Substituting the minimum over the whole simplex
replaces the declared set with a larger one; on a non-empty declaration that
would be sound but not the declared minimum, and here it merely hides an
infeasible declaration behind a plausible number. Repairing the box -- raising
a cap until the sums admit a point -- changes the declaration, which no part
of this contract licenses, and the repaired set is one nobody accepted. The
frozen verdict is refusal.
""",
    value=math.inf,
)


@dataclass(frozen=True)
class PolytopeInfeasibleCase:
    """One declared polytope that must be refused, with its emptiness witness."""

    case_id: str
    outcomes: tuple[str, ...]
    #: ``(q^-, q^+)`` when the data claims canonical box form, else None.
    box_bounds: tuple[tuple[float, ...], tuple[float, ...]] | None
    rows: tuple[tuple[float, ...], ...]
    rhs: tuple[float, ...]
    #: False when the DATA is not well formed for the form it claims, so the
    #: geometry is refused before emptiness is even considered.
    well_formed: bool
    #: The hand certificate of emptiness, checkable by substitution.
    emptiness_witness: str
    arithmetic: str


POLYTOPE_INFEASIBLE_CASES: tuple[PolytopeInfeasibleCase, ...] = (
    PolytopeInfeasibleCase(
        case_id="INFEAS-box-caps-below-one",
        outcomes=("c0", "c1", "c2"),
        box_bounds=((0.0, 0.0, 0.0), (0.25, 0.25, 0.25)),
        rows=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, -1.0),
        ),
        rhs=(0.25, 0.25, 0.25, 0.0, 0.0, 0.0),
        well_formed=True,
        emptiness_witness=(
            "Sum the three cap rows: sum_chat q(chat) <= 3/4 < 1, "
            "contradicting sum_chat q(chat) = 1."
        ),
        arithmetic="""\
A WELL-FORMED CANONICAL BOX -- 0 <= q^- <= q^+ holds coordinatewise -- whose
caps cannot carry the normalization:
  q^- = (0, 0, 0) , q^+ = (1/4, 1/4, 1/4) , sum q^+ = 3/4 < 1 .
The closed-form emptiness test of the geometry contract reads
sum q^- <= 1 <= sum q^+ and fails on the SECOND inequality. Directly: adding
the three cap rows gives sum_chat q(chat) <= 3/4, while every point of the
simplex has sum_chat q(chat) = 1, so no point is feasible. The witness is the
all-ones combination of the cap rows -- nonnegative multipliers, so it is a
legitimate consequence of the system.
THE FAILURE MODE THIS FORBIDS: computing a fill anyway. The residual is
r = 1 - 0 = 1 and the widths sum to 3/4 < r, so there IS no index whose prefix
width reaches r; an implementation that takes the last index instead returns
q = q^+ = (1/4, 1/4, 1/4), a vector that sums to 3/4 and is not a probability
distribution, and then reports its value as a minimum over a set with no
points in it.""",
    ),
    PolytopeInfeasibleCase(
        case_id="INFEAS-box-floors-above-one",
        outcomes=("c0", "c1", "c2"),
        box_bounds=((0.5, 0.5, 0.5), (0.75, 0.75, 0.75)),
        rows=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, -1.0),
        ),
        rhs=(0.75, 0.75, 0.75, -0.5, -0.5, -0.5),
        well_formed=True,
        emptiness_witness=(
            "Sum the three floor rows: -sum_chat q(chat) <= -3/2, i.e. "
            "sum_chat q(chat) >= 3/2 > 1."
        ),
        arithmetic="""\
The mirror image, and the half of the closed-form test that the other case
does not exercise:
  q^- = (1/2, 1/2, 1/2) , q^+ = (3/4, 3/4, 3/4) , sum q^- = 3/2 > 1 ,
so sum q^- <= 1 fails while 1 <= sum q^+ = 9/4 passes. Adding the three floor
rows with multiplier 1 each gives sum_chat q(chat) >= 3/2, incompatible with
sum_chat q(chat) = 1.
WHY BOTH HALVES ARE FROZEN. The test is a two-sided sandwich and an
implementation that checks only one side accepts one of these two boxes. The
floors side is the easier one to omit, because a box is usually thought of as
a set of upper bounds; here the residual r = 1 - 3/2 = -1/2 is NEGATIVE, and
the fill rule -- least index with a prefix width at least r -- is satisfied at
the first index by 0 >= -1/2, so a fill that skips the feasibility test
returns q^- itself and reports a number for an empty set.""",
    ),
    PolytopeInfeasibleCase(
        case_id="INFEAS-rows-contradict-simplex",
        outcomes=("c0", "c1", "c2"),
        box_bounds=None,
        rows=((1.0, 1.0, 1.0),),
        rhs=(0.5,),
        well_formed=True,
        emptiness_witness=(
            "The single row reads sum_chat q(chat) <= 1/2, contradicting the "
            "simplex condition sum_chat q(chat) = 1."
        ),
        arithmetic="""\
A GENERAL POLYTOPE, NOT A BOX, and the case that says the simplex condition is
part of the set and not decoration:
  m_row = 1 , B = [[1, 1, 1]] , b = (1/2) .
The row is satisfiable in the nonnegative orthant -- q = 0 satisfies it, and
so does every q with total mass at most 1/2 -- so a validation path that
checks only {q >= 0, B q <= b} finds a feasible point and ACCEPTS. Intersected
with the simplex the set is empty: sum_chat q(chat) = 1 > 1/2.
THE FAILURE MODE THIS FORBIDS is exactly that path. The taxonomy's validation
predicate for a polytope is feasibility of {q >= 0, sum q = 1, B q <= b}, all
three conditions together, and the middle one is what q = 0 fails. This is the
same omission as in PMIN-box-spillover, where dropping the normalization moved
a minimum; here it turns an empty set into an accepted one.""",
    ),
    PolytopeInfeasibleCase(
        case_id="INFEAS-rows-contradict-each-other",
        outcomes=("c0", "c1", "c2"),
        box_bounds=None,
        rows=((1.0, 1.0, 0.0), (-1.0, -1.0, 0.0)),
        rhs=(0.25, -0.75),
        well_formed=True,
        emptiness_witness=(
            "Add the two rows with multipliers (1, 1): 0 <= 1/4 - 3/4 = -1/2, "
            "false. Nonnegative multipliers, so the system itself is "
            "inconsistent."
        ),
        arithmetic="""\
TWO ROWS THAT CONTRADICT EACH OTHER, independently of the simplex:
  B = [[1, 1, 0], [-1, -1, 0]] , b = (1/4, -3/4) ,
i.e. q(c0) + q(c1) <= 1/4 and q(c0) + q(c1) >= 3/4. Adding the two rows with
the nonnegative multipliers (1, 1) annihilates every variable and leaves
0 <= -1/2, which is false: the linear system alone is inconsistent, before
q >= 0 or sum q = 1 is imposed. That inconsistency certificate is the whole
proof, checkable by substitution.
WHY IT IS NOT A BOX, and why that matters. Each row touches two coordinates,
so the rows are not of the one-hot shape a canonical box has and there are no
(q^-, q^+) to test with the closed form. This is the branch of the validation
predicate that has to be decided by rational feasibility of the system --
exactly the case the geometry contract states the predicate for, and the
reason the predicate is not simply "the box sums bracket 1".""",
    ),
    PolytopeInfeasibleCase(
        case_id="ILLFORMED-box-inverted",
        outcomes=("c0", "c1", "c2"),
        box_bounds=((0.75, 0.0, 0.0), (0.25, 1.0, 1.0)),
        rows=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, -1.0),
        ),
        rhs=(0.25, 1.0, 1.0, -0.75, 0.0, 0.0),
        well_formed=False,
        emptiness_witness=(
            "Add the cap and floor rows of c0 with multipliers (1, 1): "
            "0 <= 1/4 - 3/4 = -1/2, false. Equivalently q^-(c0) = 3/4 > 1/4 "
            "= q^+(c0), so the box is inverted at c0."
        ),
        arithmetic="""\
ILL-FORMED DATA, AND THE ONLY CASE HERE THAT THE CLOSED-FORM TEST PASSES.
  q^- = (3/4, 0, 0) , q^+ = (1/4, 1, 1) .
The canonical box form requires 0 <= q^- <= q^+ COMPONENTWISE, and at c0 the
data has 3/4 > 1/4. So this is not a canonical box, and the closed-form
emptiness test -- which is proved under that hypothesis -- does not apply.
Applied anyway it reports
  sum q^- = 3/4 <= 1 <= 9/4 = sum q^+
and PASSES, declaring a non-empty set. The set is empty: the c0 rows read
q(c0) <= 1/4 and q(c0) >= 3/4, and adding them with multipliers (1, 1) leaves
0 <= -1/2.
THE ORDER OF THE CHECKS IS THE CONTENT OF THIS CASE. Well-formedness of the
data comes first, emptiness second; a validation path that runs the sum test
without the componentwise test admits this box, and then computes a fill from
the width q^+(c0) - q^-(c0) = -1/2, which is NEGATIVE. A negative width breaks
the fill's own hypotheses -- the prefix sums are no longer monotone, so "the
least index whose prefix reaches r" is not the index the exchange argument
justifies -- and what comes out is a number with no theorem behind it.
TWO REFUSALS, NOT ONE. The other four cases in this group are well-formed data
denoting an empty set; this one is data that is not a geometry at all. An
implementation may report them the same way, but it may not reach the second
conclusion by the first test.""",
    ),
)


# ===========================================================================
#  Group 9 -- the DECLARED OPERATOR TOLERANCE (C21), new at contract 0.5.0
# ===========================================================================
#
#  Authored in the SCOPED IMPLEMENTATION BAND that the accepted amendment
#  0.5.0 opens (the freeze rule), by the run-A
#  implementer instance, BEFORE any source file supporting a declared operator
#  tolerance existed. Not one number below was produced by an implementation of
#  the thing it pins: every defect, every witness family and every gap is a
#  hand derivation from the displayed statements of contract.tex 0.5.0
#  (sha256 3783eb4f7c64adc5fe91cb8e06c6064ae635b794c9330a07ea692e687a3ddca3),
#  and each entry cites the labelled statement it comes from.
#
#  HOW THE FAMILIES WERE CHOSEN, because it is the whole reason the values are
#  checkable. Every declared family below lives on a TWO-DIMENSIONAL Q with
#  RATIONAL SPECTRUM: either two one-dimensional sectors, where every operator
#  is diagonal and the operator norm is the largest modulus of an entry, or one
#  two-dimensional sector carrying matrices of the form [[a, b], [b, a]] --
#  eigenvalues a +/- b -- or [[a, b], [c, a]], whose antisymmetric part has
#  norm |b - c|. So every frozen defect is a number derived on paper and not
#  one a solver produced, and reference.defects is a WITNESS to the derivation
#  rather than its source.
#
#  WHAT THIS GROUP DOES NOT DO. It decides no admission and runs no validation.
#  It freezes (a) what the three defects of Eq. eq:defects ARE on named
#  families, (b) what Definition def:optol ADMITS at a named tolerance,
#  (c) which branch of Theorem thm:optol a named (family, tolerance) pair falls
#  in and what that branch may and may not emit, and (d) the six reason strings
#  contract.tex spells. Ordering the refusals, choosing the arithmetic the
#  comparisons are decided in, and serializing the report are the
#  implementation's, and interface.yaml records them as open choices OC-1
#  through OC-7 rather than settling them here.
#
#  THE ONE FACT THIS GROUP EXISTS TO DISCRIMINATE. Versions 0.1.x-0.4.0 admit
#  EXACT data only, and the 0.4.0 implementation nonetheless decides the POVM
#  identities inside an UNDECLARED absolute window. At 0.5.0 an absent
#  operator_tolerance means eps_dec = 0, and "eps_dec = 0 means EXACT at every
#  site of this contract" (Section 2.5), so a defect of order 1e-11 with no
#  tolerance declared is a REFUSAL. OPTOL-SUBCONST-C and OPTOL-SUBCONST-P are
#  that discriminator, and they are the pair a validation path built around an
#  undeclared constant cannot pass.

#: The declared domain of eps_dec: the half-open interval [0, 1) of
#: contract.tex Section 2.1 and Remark rem:optol-interface (1). The upper
#: endpoint is DERIVED, not chosen: at eps_dec >= 1 condition (C) is satisfied
#: by F_v = 0 for every v, since then Delta_cpl = ||-1_Q|| = 1, "so the rule
#: would no longer constrain the family at all". OPTOL-ZERO below is that
#: family, frozen so the derivation is data rather than a sentence.
OPTOL_DOMAIN: tuple[float, float] = (0.0, 1.0)

#: The FIVE refusal reason strings contract.tex 0.5.0 spells, character for
#: character, at the sites named beside each. contract.tex Section 1.1 counts
#: the amendment's additions as "six machine-readable reason strings --- five
#: refusals and one assurance reason"; these are the five.
OPTOL_REFUSAL_REASONS: tuple[str, ...] = (
    # Section 2.1 (the operator_tolerance row); Remark rem:optol-interface (1).
    "operator_tolerance_out_of_domain",
    # Remark rem:optol-interface (2), Delta_herm > eps_dec.
    "bob_povm_hermiticity_defect",
    # Remark rem:optol-interface (2), Delta_pos > eps_dec.
    "bob_povm_negative_part",
    # Remark rem:optol-interface (2), Delta_cpl > eps_dec.
    "bob_povm_completeness_defect",
    # Remark rem:optol-interface (3): admitted, but Delta_herm > 0 or
    # Delta_pos > 0.
    "bob_povm_not_evaluable",
)

#: The SIXTH string, and it is NOT a refusal: it is the machine-readable
#: ASSURANCE reason accompanying the forced `estimate` of Remark
#: rem:optol-interface (4) and of the optimizer_certificate row of Section 2.2.
#: A run carrying it PRODUCED OUTPUT; a run carrying one of the five above
#: produced none.
OPTOL_ASSURANCE_REASON: str = "declared_operator_tolerance_open"

#: The whole vocabulary the amendment adds, as one tuple, so that a consumer
#: can assert against it without re-deriving the split. NO SEVENTH STRING IS
#: SPELLED BY THE CONTRACT, and in particular none for a failure of condition
#: (T): Remark rem:optol-interface (2) refuses that "as a MALFORMED
#: DECLARATION, at every eps_dec", which is the version-0.4.0 refusal path and
#: carries no reason of this amendment. OPTOL-BLOCK below freezes exactly that.
OPTOL_REASON_VOCABULARY: tuple[str, ...] = (
    *OPTOL_REFUSAL_REASONS,
    OPTOL_ASSURANCE_REASON,
)

#: ``meat-core@<contract_version>`` of the contract THIS GROUP is frozen
#: against (contract Section 2.5, artifact_bindings). Frozen here as the
#: EXPECTED value; nothing in this tree is retyped to it by run A. The 0.4.0
#: pins that must move to it are marked in :data:`SUPERSEDED_BY_0_5_0`.
MATHEMATICAL_SPEC_VERSION_0_5_0: str = "meat-core@0.5.0"

#: The sub-1e-10 perturbation size used by the two discriminator families,
#: chosen as an EXACT power of two so that the declared numbers are exact in
#: binary floating point and the frozen defect is the perturbation itself
#: rather than a rounding of it. 2^-37 = 7.275957614183426e-12, which is of
#: order 1e-11 and an order of magnitude BELOW the 1e-10 window the 0.4.0
#: implementation applies without declaring it.
OPTOL_SUBCONSTANT: float = 2.0**-37

#: A tolerance strictly above :data:`OPTOL_SUBCONSTANT` and still far below
#: any tolerance a real supplier would need, again an exact power of two:
#: 2^-33 = 1.1641532182693481e-10.
OPTOL_SUBCONSTANT_TOLERANCE: float = 2.0**-33

#: One row of a literal declared operator, exact as written.
OptolRow = tuple[complex, ...]
#: One declared operator, as rows.
OptolMatrix = tuple[OptolRow, ...]


@dataclass(frozen=True)
class ToleranceFamily:
    """One declared ``{F_v}`` with its three defects, derived by hand.

    The family is DATA: literal operators on a two-dimensional Q together with
    the declared sector dimensions. Nothing here is a declaration -- no
    announcements, no key map, no acceptance set -- because Definition
    ``def:optol`` reads only ``{F_v}`` and the sector decomposition, and
    freezing more would freeze what the definition does not use.
    """

    family_id: str
    #: ``(d_s)_{s in S}`` in order. ``(1, 1)`` is two one-dimensional sectors,
    #: where condition (T) is a real restriction; ``(2,)`` is one
    #: two-dimensional sector, where Pin_S is the identity and (T) is trivially
    #: satisfied.
    sector_dims: tuple[int, ...]
    #: ``{F_v}`` in outcome order ``v0, v1``.
    elements: tuple[OptolMatrix, ...]
    #: ``||F_v - F_v^dagger||`` per outcome; its maximum is `delta_herm`.
    per_outcome_hermiticity: tuple[float, ...]
    #: ``max{0, -lambda_min((F_v + F_v^dagger)/2)}`` per outcome; its maximum
    #: is `delta_pos`.
    per_outcome_negative: tuple[float, ...]
    delta_herm: float
    delta_pos: float
    delta_cpl: float
    #: Whether condition (T) holds. DECIDED EXACTLY and never within a
    #: tolerance (Definition def:optol; Remark rem:optol-reach (a)).
    block_diagonal: bool
    #: (T) AND all three defects zero -- Definition def:optol's "exactly
    #: admissible", which Lemma lem:optol-zero proves equivalent to the
    #: {F_v}-clauses of Assumption A-DECL (iii).
    exactly_admissible: bool
    derivation: str


OPTOL_FAMILIES: tuple[ToleranceFamily, ...] = (
    ToleranceFamily(
        family_id="OPTOL-EXACT",
        sector_dims=(1, 1),
        elements=(
            ((0.5 + 0j, 0j), (0j, 1 + 0j)),
            ((0.5 + 0j, 0j), (0j, 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=0.0,
        block_diagonal=True,
        exactly_admissible=True,
        derivation="""\
THE POVM OF TOY-1, written on the whole of Q rather than blockwise:
  F_v0 = diag(1/2, 1),  F_v1 = diag(1/2, 0).
Both are diagonal, hence block-diagonal for the declared sectors s0 = <e0> and
s1 = <e1>, so condition (T) of Definition def:optol holds EXACTLY.
  Delta_herm = max_v ||F_v - F_v^dagger|| = ||0|| = 0, every entry being real.
  Delta_pos: the Hermitian part of each is itself; spec F_v0 = {1/2, 1} and
             spec F_v1 = {1/2, 0}, both non-negative, so each
             max{0, -lambda_min} = 0 and Delta_pos = 0.
  Delta_cpl = ||F_v0 + F_v1 - 1_Q|| = ||diag(1, 1) - diag(1, 1)|| = 0.
By Lemma lem:optol-zero the family is EXACTLY ADMISSIBLE, and by Theorem
thm:optol (i) every claim C1-C20 applies to it "exactly as at version 0.4.0.
The declared eps_dec changes no statement, no bound and no number."

WHY THIS FAMILY AND NOT A FRESH ONE. TOY-1 carries frozen 0.2.4-era numbers
(O-HLOW-RETENTION, O-K-IDENTITY, O-DEFICIT-SIGN, O-SECTOR-DECOMPOSITION), so
"the 0.4.0 numbers are unchanged" becomes a statement this registry can
FALSIFY rather than assert: those entries and this one describe the same
operators, and if the amendment moved any of them the two would disagree.""",
    ),
    ToleranceFamily(
        family_id="OPTOL-HERM",
        sector_dims=(1, 1),
        elements=(
            ((0.5 + 0j, 0j), (0j, 1 + 0.125j)),
            ((0.5 + 0j, 0j), (0j, -0.125j)),
        ),
        per_outcome_hermiticity=(0.25, 0.25),
        per_outcome_negative=(0.0, 0.0),
        delta_herm=0.25,
        delta_pos=0.0,
        delta_cpl=0.0,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
A HERMITICITY DEFECT AND NOTHING ELSE. OPTOL-EXACT with +i/8 added to the s1
block of F_v0 and -i/8 to that of F_v1:
  F_v0 = diag(1/2, 1 + i/8),  F_v1 = diag(1/2, -i/8).
Both diagonal, so (T) holds exactly.
  Delta_herm: for a 1x1 block z, z - z_bar = 2i Im z, so
    ||F_v0 - F_v0^dagger|| = ||diag(0, i/4)|| = 1/4,
    ||F_v1 - F_v1^dagger|| = ||diag(0, -i/4)|| = 1/4,
  and Delta_herm = 1/4, ATTAINED BY BOTH OUTCOMES -- which is why the report's
  per-outcome vector is not recoverable from the maximum alone.
  Delta_pos: (F_v + F_v^dagger)/2 = diag(1/2, 1) and diag(1/2, 0) -- the
  imaginary parts cancel -- with spectra {1/2, 1} and {1/2, 0}, so
  Delta_pos = 0.
  Delta_cpl: the two imaginary parts cancel in the sum as well,
    F_v0 + F_v1 = diag(1, 1) = 1_Q, so Delta_cpl = 0.
The cancellation is deliberate: it ISOLATES (H) from (C), so a case that
refuses on the Hermiticity defect cannot be passing because of a completeness
defect it also has.

BRANCH. Delta_herm > 0, so by Theorem thm:optol (ii) and Lemma
lem:optol-defined (i) the positive semidefinite square root sqrt(F_v) of
Eqs. eq:Vmsm and eq:kraus DOES NOT EXIST, and with it none of V_msm, W_prot,
M_prot, K_kappa, G_chat, Theta_chat, T_chat, K_chat, f_{chat,s}, O_alpha or
h_low. "It is ADMISSION, NOT EVALUATION, that eps_dec governs here."
Even the affine Phi[omega] leaves its declared codomain here: at
Delta_herm > 0 the values tr[(M_x x F_v) omega] are in general COMPLEX, so
"the expression evaluates without being the object eq:Phimap types"
(lem:optol-defined (i)).""",
    ),
    ToleranceFamily(
        family_id="OPTOL-NEG",
        sector_dims=(1, 1),
        elements=(
            ((-0.125 + 0j, 0j), (0j, 1 + 0j)),
            ((1.125 + 0j, 0j), (0j, 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.125, 0.0),
        delta_herm=0.0,
        delta_pos=0.125,
        delta_cpl=0.0,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
A NEGATIVE PART AND NOTHING ELSE.
  F_v0 = diag(-1/8, 1),  F_v1 = diag(9/8, 0).
Both diagonal and real, so (T) holds exactly and Delta_herm = 0.
  Delta_pos: the Hermitian part of each is itself.
    lambda_min(F_v0) = -1/8, so max{0, 1/8} = 1/8;
    lambda_min(F_v1) = 0,    so max{0, 0}   = 0.
  Delta_pos = 1/8, ATTAINED BY v0 ALONE -- the per-outcome vector (1/8, 0)
  carries what the maximum does not.
  Delta_cpl = ||diag(-1/8 + 9/8, 1 + 0) - diag(1, 1)|| = ||0|| = 0: the family
  SUMS TO THE IDENTITY EXACTLY while one of its elements is not positive.
That combination is the point of this case. A validation path that checks
completeness and forgets positivity accepts it; a path that reads
Delta_cpl = 0 as "this is a POVM" accepts it too. It is neither, and by
Theorem thm:optol (ii) it is NOT EVALUABLE: sqrt(F_v0) does not exist on the
negative eigenvalue, and Lemma lem:optol-defined (i) records that "extending
t -> sqrt(t) below 0, or reading sqrt(F_v) as the square root of some nearby
positive semidefinite operator, is a CHOICE, and this contract makes none".""",
    ),
    ToleranceFamily(
        family_id="OPTOL-COMP",
        sector_dims=(1, 1),
        elements=(
            ((0.5 + 0j, 0j), (0j, 1 + 0j)),
            ((0.5 + 0j, 0j), (0j, 0.125 + 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=0.125,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
A COMPLETENESS DEFECT AND NOTHING ELSE -- the ONLY branch of Theorem
thm:optol on which a run may proceed at all.
  F_v0 = diag(1/2, 1),  F_v1 = diag(1/2, 1/8).
Both diagonal, real and positive semidefinite (spectra {1/2, 1} and
{1/2, 1/8}), so (T) holds exactly and Delta_herm = Delta_pos = 0.
  Delta_cpl = ||diag(1, 9/8) - diag(1, 1)|| = ||diag(0, 1/8)|| = 1/8.
BRANCH (iii) of Theorem thm:optol: Delta_herm = Delta_pos = 0 < Delta_cpl, so
the survivor list of Lemma lem:optol-defined (iv) holds VERBATIM for the
declared numbers and Eq. eq:hlow-def may be evaluated on them -- "but h_qkd is
not defined for the declared numbers, no claim of this contract bounds it,
h_low is a lower bound on NOTHING, and no key length is asserted."

WHAT FAILS, exactly, by Lemma lem:optol-defined (iii): V_msm is not an
isometry, W_prot is not one and M_prot is not trace-preserving
(thm:protocol-channel (i)); |sum_chat P_chat(omega) - 1| <= Delta_cpl = 1/8 on states, so
Phi[omega] is IN GENERAL NOT A PROBABILITY VECTOR (thm:protocol-channel (iii)); the
trace-non-increasing clause of lem:branch-maps (i) fails with it, since it needs
sum_v F_v <= 1_Q -- and here sum_v F_v = diag(1, 9/8) has a block ABOVE the
identity; and thm:branch-formula, thm:reduction, cor:reduction-constrained, thm:accumulated-entropy, thm:constrained-accumulation,
thm:keylength and cor:cert-keylength lose a hypothesis they use.
WHAT SURVIVES, by (iv): eq:traces; lem:branch-maps (ii), (iii), (iv); thm:protocol-channel (ii);
foundations/lem:pinchmono and cor:f-nonpos; the BOUNDS 0 <= K_chat <= P_chat of thm:branch-formula;
prop:exact-cancellation; thm:removal with the `removable` flag; and thm:convexity -- the last
with ONE substitution, its concavity step coming from lem:cone-concavity
instead of cor:concavity.
THE ARITHMETIC DISPLACEMENT, by Theorem thm:optol (iii) and
Eq. eq:penaltyshift, is bounded by log2(1/(1 - Delta_cpl)) = log2(8/7)
= 0.19264507794239583 bits in absolute value, of either sign. THE SMALLNESS IS
NOT A SECURITY STATEMENT: "Theorems thm:protocol-channel, thm:branch-formula and thm:reduction have no
conclusion for these numbers, so there is nothing for a small displacement to
be small relative to."
""",
    ),
    ToleranceFamily(
        family_id="OPTOL-BLOCK",
        sector_dims=(1, 1),
        elements=(
            ((0.75 + 0j, 0.25 + 0j), (0.25 + 0j, 0.75 + 0j)),
            ((0.25 + 0j, -0.25 + 0j), (-0.25 + 0j, 0.25 + 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=0.0,
        block_diagonal=False,
        exactly_admissible=False,
        derivation="""\
A PERFECT POVM THAT IS REFUSED AT EVERY TOLERANCE, and it is the sharpest
statement of Definition def:optol condition (T) available.
  F_v0 = [[3/4, 1/4], [1/4, 3/4]],  F_v1 = [[1/4, -1/4], [-1/4, 1/4]].
Both are real symmetric of the form [[a, b], [b, a]], so their spectra are
a +/- b:  spec F_v0 = {1, 1/2},  spec F_v1 = {1/2, 0}. Hence
  Delta_herm = 0 (both Hermitian),
  Delta_pos  = 0 (both spectra non-negative),
  Delta_cpl  = ||F_v0 + F_v1 - 1_Q|| = ||diag(1, 1) - diag(1, 1)|| = 0.
ALL THREE DEFECTS VANISH. The family is a genuine POVM on a two-dimensional
space -- and it is REFUSED, because the declared sectors are s0 = <e0> and
s1 = <e1>, and
  ||F_v0 - Pin_S(F_v0)|| = ||[[0, 1/4], [1/4, 0]]|| = 1/4 =/= 0,
so condition (T) FAILS. It fails identically for F_v1.

WHY THE NUMBER 1/4 IS NOT COMPARED TO ANYTHING. Definition def:optol decides
(T) "EXACTLY and never within a tolerance", and Remark rem:optol-reach (a)
gives the reason: the decomposition is used as an EXACT DIRECT SUM by
lem:branch-maps (iii), prop:exact-cancellation, thm:removal and thm:choi, and "the sector factorization
sqrt(F_v) = direct_sum_s sqrt(F_v^{(s)}) that carries eq:kraus into
eq:G-sector is an identity of the functional calculus that holds for a
block-diagonal operator and FOR NO OTHER". The off-block norm "can of course
be written down"; what cannot be written down without re-deriving them is what
those four statements would say about an operator that is only nearly
block-diagonal.
THE REFUSAL CARRIES NO 0.5.0 REASON STRING. Remark rem:optol-interface (2):
"Condition (T) is decided exactly and its failure is refused as a MALFORMED
DECLARATION, at every eps_dec." That is the version-0.4.0 refusal path -- the
{F_v}-clause of Assumption A-DECL (iii) -- and Section 1.1 counts the
amendment's additions as exactly five refusal reasons, none of them naming
block-diagonality.""",
    ),
    ToleranceFamily(
        family_id="OPTOL-2D-COMP",
        sector_dims=(2,),
        elements=(
            ((0.75 + 0j, 0.25 + 0j), (0.25 + 0j, 0.75 + 0j)),
            ((0.375 + 0j, -0.125 + 0j), (-0.125 + 0j, 0.375 + 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=0.25,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
A COMPLETENESS DEFECT ON ONE TWO-DIMENSIONAL SECTOR, so that Delta_cpl is a
genuine 2x2 spectral computation and not the largest of two diagonal entries.
  |S| = 1 with d_s0 = 2, so Pin_S = id and condition (T) is TRIVIALLY
  satisfied -- the case that shows (T) and (C) are independent.
  F_v0 = [[3/4, 1/4], [1/4, 3/4]],   spec = {1, 1/2}
  F_v1 = [[3/8, -1/8], [-1/8, 3/8]], spec = {1/4, 1/2}
Both real symmetric with non-negative spectrum, so Delta_herm = Delta_pos = 0.
  F_v0 + F_v1 - 1_Q = [[9/8, 1/8], [1/8, 9/8]] - [[1, 0], [0, 1]]
                    = [[1/8, 1/8], [1/8, 1/8]],
  a rank-one symmetric matrix of the form [[a, a], [a, a]] with a = 1/8, whose
  spectrum is {2a, 0} = {1/4, 0}. Hence Delta_cpl = 1/4.
BRANCH (iii), as OPTOL-COMP, with a displacement bound
log2(1/(1 - 1/4)) = log2(4/3) = 0.4150374992788438 bits.
The three matrices share the eigenbasis {(1, 1)/sqrt(2), (1, -1)/sqrt(2)}, in
which F_v0 = diag(1, 1/2), F_v1 = diag(1/4, 1/2) and the sum is diag(5/4, 1),
which is what makes the lem:nearpovm witness for this family exactly rational
(see OPTOL_WITNESS_CASES, WIT-2DCOMP).""",
    ),
    ToleranceFamily(
        family_id="OPTOL-2D-NEG",
        sector_dims=(2,),
        elements=(
            ((0.375 + 0j, 0.625 + 0j), (0.625 + 0j, 0.375 + 0j)),
            ((0.625 + 0j, -0.625 + 0j), (-0.625 + 0j, 0.625 + 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.25, 0.0),
        delta_herm=0.0,
        delta_pos=0.25,
        delta_cpl=0.0,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
A NEGATIVE EIGENVALUE THAT IS NOT A NEGATIVE ENTRY -- the case a
componentwise sign check accepts.
  |S| = 1 with d_s0 = 2, so (T) is trivial.
  F_v0 = [[3/8, 5/8], [5/8, 3/8]],   spec = 3/8 +/- 5/8 = {1, -1/4}
  F_v1 = 1_Q - F_v0 = [[5/8, -5/8], [-5/8, 5/8]], spec = 5/8 -/+ 5/8
                                                       = {0, 5/4}
Both real symmetric, so Delta_herm = 0, and by construction
  Delta_cpl = ||F_v0 + F_v1 - 1_Q|| = 0.
  Delta_pos: lambda_min(F_v0) = -1/4 gives max{0, 1/4} = 1/4;
             lambda_min(F_v1) = 0    gives 0.
  Delta_pos = 1/4, attained by v0.
EVERY DIAGONAL ENTRY OF F_v0 IS POSITIVE (3/8 and 3/8) and the operator is
still indefinite: the negative eigenvalue lives on (1, -1)/sqrt(2). Definition
def:optol takes lambda_min of the Hermitian part and not a minimum over
entries, and this family is the difference.
BRANCH (ii): NOT EVALUABLE, exactly as OPTOL-NEG.""",
    ),
    ToleranceFamily(
        family_id="OPTOL-2D-HERM",
        sector_dims=(2,),
        elements=(
            ((0.5 + 0j, 0.375 + 0j), (0.125 + 0j, 0.5 + 0j)),
            ((0.5 + 0j, -0.375 + 0j), (-0.125 + 0j, 0.5 + 0j)),
        ),
        per_outcome_hermiticity=(0.25, 0.25),
        per_outcome_negative=(0.0, 0.0),
        delta_herm=0.25,
        delta_pos=0.0,
        delta_cpl=0.0,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
A REAL, NON-SYMMETRIC FAMILY: the Hermiticity defect of a matrix with no
imaginary part at all.
  |S| = 1 with d_s0 = 2, so (T) is trivial.
  F_v0 = [[1/2, 3/8], [1/8, 1/2]],  F_v1 = [[1/2, -3/8], [-1/8, 1/2]].
  Delta_herm: for a real 2x2 F, F - F^T = [[0, b - c], [c - b, 0]], whose two
  singular values are both |b - c|. Here b - c = 3/8 - 1/8 = 1/4 for v0 and
  -1/4 for v1, so both norms are 1/4 and Delta_herm = 1/4, attained by both.
  Delta_pos: (F_v + F_v^T)/2 = [[1/2, 1/4], [1/4, 1/2]] and
  [[1/2, -1/4], [-1/4, 1/2]], of the form [[a, b], [b, a]] with spectra
  {3/4, 1/4} and {1/4, 3/4}; both non-negative, so Delta_pos = 0.
  Delta_cpl = ||F_v0 + F_v1 - 1_Q|| = ||[[1, 0], [0, 1]] - 1_Q|| = 0.
BRANCH (ii): NOT EVALUABLE. An implementation that tests Hermiticity by
comparing imaginary parts, or that silently symmetrizes a real matrix on the
way in, admits this family and computes on it -- which is the repair Remark
rem:optol-interface (3) forbids by name ("Hermitizing").""",
    ),
    ToleranceFamily(
        family_id="OPTOL-SUBCONST-C",
        sector_dims=(1, 1),
        elements=(
            ((0.5 + 0j, 0j), (0j, 1 + 0j)),
            ((0.5 + 0j, 0j), (0j, 2.0**-37 + 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=2.0**-37,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
THE DISCRIMINATOR, completeness side. OPTOL-EXACT with 2^-37 added to the s1
block of F_v1:
  F_v0 = diag(1/2, 1),  F_v1 = diag(1/2, 2^-37).
  Delta_herm = 0, Delta_pos = 0 (both diagonal, real, non-negative), and
  Delta_cpl = ||diag(1, 1 + 2^-37) - diag(1, 1)|| = 2^-37
            = 7.275957614183426e-12,
  an EXACT binary rational, so the frozen defect is the perturbation itself and
  not a rounding of it.
WHAT THIS CASE DECIDES. 2^-37 is of order 1e-11 and lies an order of magnitude
BELOW the undeclared 1e-10 window the 0.4.0 implementation applies to the same
identity. At 0.5.0:
  eps_dec ABSENT   -> eps_dec = 0 -> Delta_cpl = 2^-37 > 0 -> REFUSED, reason
                      bob_povm_completeness_defect (Remark
                      rem:optol-interface (2), and Section 2.5: "eps_dec = 0
                      means EXACT at every site of this contract");
  eps_dec = 0      -> the same verdict, character for character (Lemma
                      lem:optol-zero);
  eps_dec = 2^-37  -> ADMITTED at the boundary, branch (iii);
  eps_dec = 2^-33  -> ADMITTED, branch (iii).
A validation path that decides this identity inside an UNDECLARED absolute
window returns the fourth answer for all four inputs, and in particular admits
and COMPUTES where 0.5.0 refuses. The difference is not a matter of degree:
the contract fixes NO DEFAULT VALUE "here or in any artifact derived from
here", so a constant is not a small tolerance -- it is an undeclared one.""",
    ),
    ToleranceFamily(
        family_id="OPTOL-SUBCONST-P",
        sector_dims=(1, 1),
        elements=(
            ((-(2.0**-37) + 0j, 0j), (0j, 1 + 0j)),
            ((1 + 2.0**-37 + 0j, 0j), (0j, 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(2.0**-37, 0.0),
        delta_herm=0.0,
        delta_pos=2.0**-37,
        delta_cpl=0.0,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
THE DISCRIMINATOR, positivity side, and the harder half.
  F_v0 = diag(-2^-37, 1),  F_v1 = diag(1 + 2^-37, 0).
  Delta_herm = 0 (both diagonal and real).
  Delta_pos: lambda_min(F_v0) = -2^-37 gives max{0, 2^-37} = 2^-37;
             lambda_min(F_v1) = 0 gives 0. So Delta_pos = 2^-37, attained by
             v0.
  Delta_cpl = ||diag(-2^-37 + 1 + 2^-37, 1) - diag(1, 1)|| = 0: the two
  perturbations CANCEL in the sum, so completeness is exact and only
  positivity is defective.
AT 0.5.0:
  eps_dec ABSENT or 0 -> REFUSED, reason bob_povm_negative_part;
  eps_dec = 2^-33     -> ADMITTED by rule (2) -- and then REFUSED ANYWAY, with
                         reason bob_povm_not_evaluable, because Delta_pos > 0
                         (Theorem thm:optol (ii); Remark
                         rem:optol-interface (3)).
SO NO TOLERANCE MAKES THIS FAMILY COMPUTABLE, and that is the case's content.
A 1e-10 window admits it and computes sqrt(F_v0) on a matrix with a negative
eigenvalue -- which at that magnitude a floating-point square root returns as
NaN or silently clamps to zero, either of which is the repair the contract
forbids. Declaring a tolerance ABOVE the defect does not help: admission is
not evaluation, and the second refusal is "not a policy choice" but the
absence of any defined computation (lem:optol-defined (i)).""",
    ),
    ToleranceFamily(
        family_id="OPTOL-ZERO",
        sector_dims=(1, 1),
        elements=(
            ((0j, 0j), (0j, 0j)),
            ((0j, 0j), (0j, 0j)),
        ),
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=1.0,
        block_diagonal=True,
        exactly_admissible=False,
        derivation="""\
THE FAMILY THAT DERIVES THE UPPER ENDPOINT OF THE DECLARED DOMAIN.
  F_v0 = F_v1 = 0 on a two-dimensional Q.
  Both are trivially Hermitian, positive semidefinite and block-diagonal, so
  (T) holds and Delta_herm = Delta_pos = 0.
  Delta_cpl = ||0 - 1_Q|| = ||-1_Q|| = 1.
Remark rem:optol-interface (1) derives the endpoint from exactly this: "at
eps_dec >= 1 condition (C) is satisfied by F_v = 0 for every v (then
Delta_cpl = ||-1_Q|| = 1), SO THE RULE WOULD NO LONGER CONSTRAIN THE FAMILY AT
ALL." The endpoint "is DERIVED, not chosen", and this family is the
derivation.
IT IS NOT ADMISSIBLE AT ANY DECLARED TOLERANCE, because the domain stops
strictly below 1: at every eps_dec in [0, 1) one has Delta_cpl = 1 > eps_dec
and the request is refused with bob_povm_completeness_defect. The frozen
admission case AD-ZERO-NEAR-ONE pins that at eps_dec = 0.999.
A SECOND, DIFFERENT THRESHOLD, recorded here so the two are not conflated:
Lemma lem:nearpovm's hypothesis theta < 1 ceases to be GUARANTEED by the
admission rule at eps_dec >= (|V| + 1)^{-1}, which is 1/3 for the two-outcome
families of this group. That threshold bounds the WITNESS, not the domain, and
Remark rem:optol-interface (1) states them as two separate facts.""",
    ),
)


# ---------------------------------------------------------------------------
#  The declared domain [0, 1) -- Remark rem:optol-interface (1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToleranceDomainCase:
    """One declared ``eps_dec`` and whether Section 2.1 admits the DATUM.

    This is rule (1) of Remark ``rem:optol-interface`` and it fires BEFORE any
    operator is looked at: an out-of-domain tolerance is refused as a bad
    request, and no defect has been measured against a legal threshold when it
    is.
    """

    case_id: str
    #: ``None`` spells an ABSENT operator_tolerance, which "means eps_dec = 0".
    declared: float | None
    #: The value the rest of the rule reads. Equal to `declared` when present,
    #: and 0.0 when it is absent.
    effective: float | None
    in_domain: bool
    #: ``operator_tolerance_out_of_domain`` on a refusal, ``None`` otherwise.
    reason: str | None
    derivation: str


OPTOL_DOMAIN_CASES: tuple[ToleranceDomainCase, ...] = (
    ToleranceDomainCase(
        case_id="DOM-absent",
        declared=None,
        effective=0.0,
        in_domain=True,
        reason=None,
        derivation="""\
Section 2.1, the operator_tolerance row: "Optional; ABSENT MEANS eps_dec = 0,
which is the versions 0.1.x-0.4.0 reading verbatim." An absent declaration is
not a missing input and not an error: it is the exact reading, and Theorem
thm:optol (i) records that "an absent operator_tolerance is this case".
Paired with DOM-zero: THE TWO DECIDE IDENTICALLY on every family of this
group, which is the whole content of Lemma lem:optol-zero at the interface.""",
    ),
    ToleranceDomainCase(
        case_id="DOM-zero",
        declared=0.0,
        effective=0.0,
        in_domain=True,
        reason=None,
        derivation="""\
The LOWER ENDPOINT IS INCLUDED: the domain is [0, 1), closed at 0. A declared
zero is legal, and by Lemma lem:optol-zero the conditions (H), (P), (C) then
read Delta <= 0, "which for non-negative quantities is vanishing", so the
admission rule is "the bob_povm validity condition of versions 0.1.x-0.4.0
character for character".
DECLARING ZERO AND DECLARING NOTHING ARE THE SAME REQUEST as far as every
verdict of Definition def:optol and Theorem thm:optol goes. They may DIFFER in
what operator_tolerance_report presents -- the report carries "the declared
eps_dec verbatim" and how absence is spelled there is interface.yaml open
choice OC-3 -- but no admission, no branch and no number turns on it.""",
    ),
    ToleranceDomainCase(
        case_id="DOM-eighth",
        declared=0.125,
        effective=0.125,
        in_domain=True,
        reason=None,
        derivation="""\
An ordinary interior value, and the one the OPTOL-COMP and OPTOL-HERM boundary
pairs are stated at. 0 <= 1/8 < 1, so the datum is admitted and the rest of
Definition def:optol applies. Frozen so that the domain table contains a
POSITIVE admitted value and not only its two endpoints -- a check that
compares against the endpoints alone passes on a rule that admits nothing in
between.""",
    ),
    ToleranceDomainCase(
        case_id="DOM-near-one",
        declared=0.999,
        effective=0.999,
        in_domain=True,
        reason=None,
        derivation="""\
0.999 < 1, so the DATUM is in domain, however useless the threshold is. This
case exists to keep two facts apart. The domain rule admits it; the admission
rule then still refuses OPTOL-ZERO at it, because Delta_cpl = 1 > 0.999. What
Remark rem:optol-interface (1) rules out at eps_dec >= 1 is that condition (C)
"would no longer constrain the family AT ALL"; below 1 it constrains it, and
the fact that it constrains it weakly is not a domain question.
NOTE ALSO that 0.999 exceeds (|V| + 1)^{-1} = 1/3 for a two-outcome family, so
admission at this tolerance does NOT guarantee Lemma lem:nearpovm's hypothesis
theta < 1 -- the witness is then exhibited only for declarations whose MEASURED
defects still satisfy it.""",
    ),
    ToleranceDomainCase(
        case_id="DOM-one",
        declared=1.0,
        effective=None,
        in_domain=False,
        reason="operator_tolerance_out_of_domain",
        derivation="""\
THE UPPER ENDPOINT IS EXCLUDED: the domain is [0, 1), half-open at 1. A
declared 1.0 is REFUSED with reason operator_tolerance_out_of_domain, and the
refusal is derived rather than stipulated -- see OPTOL-ZERO, the family for
which (C) is satisfied at eps_dec = 1 and which is not a POVM by any reading.
NOTHING IS MEASURED ON THIS PATH. The request is refused as a bad DATUM, so no
defect has been compared against a legal threshold; what an implementation
reports in operator_tolerance_report here is interface.yaml open choice
OC-6.""",
    ),
    ToleranceDomainCase(
        case_id="DOM-three-halves",
        declared=1.5,
        effective=None,
        in_domain=False,
        reason="operator_tolerance_out_of_domain",
        derivation="""\
Above the endpoint, refused with the same reason. Frozen beside DOM-one so
that an implementation refusing only values STRICTLY above 1 -- a `> 1` where
the contract writes `>= 1` -- is caught by DOM-one rather than passing both.""",
    ),
    ToleranceDomainCase(
        case_id="DOM-negative-eighth",
        declared=-0.125,
        effective=None,
        in_domain=False,
        reason="operator_tolerance_out_of_domain",
        derivation="""\
Below the domain, refused with operator_tolerance_out_of_domain. A negative
tolerance is not "stricter than exact": Definition def:optol reads (H), (P),
(C) as Delta <= eps_dec with all three defects non-negative by construction,
so a negative eps_dec would refuse EVERY family including an exact POVM, on a
condition the contract never states. The contract closes the domain at 0
instead, and the refusal is a refusal of the datum.""",
    ),
    ToleranceDomainCase(
        case_id="DOM-negative-subconstant",
        declared=-(2.0**-37),
        effective=None,
        in_domain=False,
        reason="operator_tolerance_out_of_domain",
        derivation="""\
A negative value of the same magnitude as the discriminator perturbation,
refused for the same reason. Frozen beside DOM-negative-eighth because an
implementation that tests the lower endpoint with a tolerance of its own --
`eps_dec < -1e-10` rather than `eps_dec < 0` -- passes the first case and
fails this one. The domain of a DECLARED datum is decided exactly; there is no
tolerance on the tolerance.""",
    ),
)


# ---------------------------------------------------------------------------
#  The admission rule, case by case -- Definition def:optol, Remark
#  rem:optol-interface (2), (3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdmissionCase:
    """One (family, declared tolerance) pair and the verdict Section 2 fixes."""

    case_id: str
    family_id: str
    #: ``None`` spells an ABSENT operator_tolerance (eps_dec = 0).
    declared: float | None
    #: Whether Definition def:optol ADMITS the family at this tolerance --
    #: (T) and the three inequalities. ADMISSION IS NOT A LICENCE and it is
    #: not the same question as whether a run proceeds.
    admitted: bool
    #: The machine-readable refusal reason, or ``None`` where the request is
    #: not refused. A (T) failure carries ``None``: it is refused as a
    #: MALFORMED DECLARATION and the amendment spells no reason for it
    #: (Remark rem:optol-interface (2)).
    reason: str | None
    #: Which part of Theorem thm:optol the pair falls in: "i", "ii", "iii", or
    #: ``None`` where the request never reaches the theorem -- an
    #: out-of-domain datum, a (T) failure, or a defect above the tolerance.
    branch: str | None
    #: Whether the run produces output at all.
    proceeds: bool
    derivation: str


OPTOL_ADMISSION_CASES: tuple[AdmissionCase, ...] = (
    # -- (T): refused at EVERY tolerance, exactly, with no 0.5.0 reason -----
    AdmissionCase(
        case_id="AD-BLOCK-absent",
        family_id="OPTOL-BLOCK",
        declared=None,
        admitted=False,
        reason=None,
        branch=None,
        proceeds=False,
        derivation="""\
Condition (T) fails (off-block norm 1/4), so the declaration is refused as
MALFORMED, and the amendment spells no reason string for it. All three defects
are ZERO here, so a refusal that reports one of the three defect reasons is
reporting a defect the family does not have.""",
    ),
    AdmissionCase(
        case_id="AD-BLOCK-half",
        family_id="OPTOL-BLOCK",
        declared=0.5,
        admitted=False,
        reason=None,
        branch=None,
        proceeds=False,
        derivation="""\
The same verdict at eps_dec = 1/2, which exceeds the off-block norm 1/4 by a
factor of two. "Block-diagonality, decided EXACTLY and never within a
tolerance" (Definition def:optol (T)); "its failure is refused as a malformed
declaration, AT EVERY eps_dec" (Remark rem:optol-interface (2)). This case and
AD-BLOCK-absent differ in exactly one datum and agree in their verdict, which
is the opposite of a boundary pair and is the point.""",
    ),
    AdmissionCase(
        case_id="AD-BLOCK-near-one",
        family_id="OPTOL-BLOCK",
        declared=0.999,
        admitted=False,
        reason=None,
        branch=None,
        proceeds=False,
        derivation="""\
And again at the largest tolerance the domain admits. Three cases, three
tolerances spanning the whole domain, one verdict.""",
    ),
    # -- (i): exactly admissible; the 0.4.0 reading, verbatim ---------------
    AdmissionCase(
        case_id="AD-EXACT-absent",
        family_id="OPTOL-EXACT",
        declared=None,
        admitted=True,
        reason=None,
        branch="i",
        proceeds=True,
        derivation="""\
An absent tolerance on an exactly admissible family: eps_dec = 0, all three
defects vanish, (T) holds, so the family is 0-admissible and by Lemma
lem:optol-zero exactly admissible. Theorem thm:optol (i): the declaration
satisfies Assumption A-DECL in full and every claim C1-C20 applies to the
declared numbers exactly as at version 0.4.0. THIS IS THE DEFAULT REQUEST, and
"at eps_dec = 0 only case (i) can occur and the theorem is vacuous".""",
    ),
    AdmissionCase(
        case_id="AD-EXACT-zero",
        family_id="OPTOL-EXACT",
        declared=0.0,
        admitted=True,
        reason=None,
        branch="i",
        proceeds=True,
        derivation="""\
The same family with the tolerance DECLARED as zero. Identical verdict,
identical branch, identical numbers. Paired with AD-EXACT-absent to freeze
"absent means eps_dec = 0" as a decision and not only as a sentence.""",
    ),
    AdmissionCase(
        case_id="AD-EXACT-quarter",
        family_id="OPTOL-EXACT",
        declared=0.25,
        admitted=True,
        reason=None,
        branch="i",
        proceeds=True,
        derivation="""\
An exactly admissible family with a NONZERO tolerance declared. Still branch
(i), still every claim C1-C20, still the 0.4.0 numbers: "The declared eps_dec
changes no statement, no bound and no number. In particular DECLARING A
TOLERANCE NEVER WEAKENS A RUN WHOSE DATA DOES NOT USE IT" (Theorem
thm:optol (i)).
The report is NOT all-zero here: it carries the declared 1/4 verbatim
alongside three zero defects, and both booleans stay true (see
REPORT-EXACT-quarter). An implementation that infers key_length_claim from the
declared tolerance rather than from the measured defects fails exactly this
case, and it fails it in the direction that WITHHOLDS a legitimate key.""",
    ),
    # -- (H) boundary pair ---------------------------------------------------
    AdmissionCase(
        case_id="AD-HERM-boundary",
        family_id="OPTOL-HERM",
        declared=0.25,
        admitted=True,
        reason="bob_povm_not_evaluable",
        branch="ii",
        proceeds=False,
        derivation="""\
(H) AT THE BOUNDARY: Delta_herm = 1/4 <= 1/4 = eps_dec, so condition (H) holds
-- the inequality is NOT strict -- and with Delta_pos = Delta_cpl = 0 the
family is eps_dec-ADMITTED.
AND THE REQUEST IS STILL REFUSED, with reason bob_povm_not_evaluable, because
Delta_herm > 0 (Theorem thm:optol (ii); Remark rem:optol-interface (3)). This
is the case that separates ADMISSION from EVALUATION, and no other case in
this group does it as cleanly: the admission rule says yes and the contract
still specifies no computation, "so there is no computation for an
implementation to perform, and every way of proceeding ... is a repair of
declared data, which this contract forbids".""",
    ),
    AdmissionCase(
        case_id="AD-HERM-below",
        family_id="OPTOL-HERM",
        declared=0.125,
        admitted=False,
        reason="bob_povm_hermiticity_defect",
        branch=None,
        proceeds=False,
        derivation="""\
Delta_herm = 1/4 > 1/8 = eps_dec, so (H) FAILS and the request is refused by
rule (2) with the reason NAMING THE FAILED CHECK,
bob_povm_hermiticity_defect, "carrying the measured defect and the declared
eps_dec".
BOUNDARY PAIR with AD-HERM-boundary: same family, same operators, same three
defects; the two cases differ in EXACTLY ONE DATUM, the declared tolerance,
and in the reason they carry. The two reasons are different strings, and they
are different KINDS of refusal -- one says the declaration was not admitted,
the other says it was admitted and cannot be evaluated.""",
    ),
    AdmissionCase(
        case_id="AD-HERM-absent",
        family_id="OPTOL-HERM",
        declared=None,
        admitted=False,
        reason="bob_povm_hermiticity_defect",
        branch=None,
        proceeds=False,
        derivation="""\
No tolerance declared, so eps_dec = 0 and Delta_herm = 1/4 > 0: refused with
bob_povm_hermiticity_defect. Remark rem:optol-interface (2): "At eps_dec = 0
these are the version-0.4.0 refusals character for character."
Together with AD-HERM-below and AD-HERM-boundary this family is frozen at
three tolerances spanning the rule: below the defect, at it, and absent.""",
    ),
    AdmissionCase(
        case_id="AD-2DH-boundary",
        family_id="OPTOL-2D-HERM",
        declared=0.25,
        admitted=True,
        reason="bob_povm_not_evaluable",
        branch="ii",
        proceeds=False,
        derivation="""\
The same (H) boundary on the real, non-symmetric two-dimensional family:
Delta_herm = 1/4 <= 1/4, admitted, and refused as not evaluable. Frozen beside
AD-HERM-boundary because the two families reach the same verdict by different
arithmetic -- an imaginary part on a 1x1 block, and an asymmetry on a 2x2 real
block -- and an implementation that tests Hermiticity by inspecting imaginary
parts passes the first and admits the second silently.""",
    ),
    AdmissionCase(
        case_id="AD-2DH-below",
        family_id="OPTOL-2D-HERM",
        declared=0.125,
        admitted=False,
        reason="bob_povm_hermiticity_defect",
        branch=None,
        proceeds=False,
        derivation="""\
Delta_herm = 1/4 > 1/8: refused, reason bob_povm_hermiticity_defect. The
boundary partner of AD-2DH-boundary, differing in exactly one datum.""",
    ),
    # -- (P) boundary pair ---------------------------------------------------
    AdmissionCase(
        case_id="AD-NEG-boundary",
        family_id="OPTOL-NEG",
        declared=0.125,
        admitted=True,
        reason="bob_povm_not_evaluable",
        branch="ii",
        proceeds=False,
        derivation="""\
(P) AT THE BOUNDARY: Delta_pos = 1/8 <= 1/8 = eps_dec, so (P) holds; with
Delta_herm = Delta_cpl = 0 the family is admitted -- and refused anyway with
bob_povm_not_evaluable, Delta_pos > 0 (Theorem thm:optol (ii)).
Remark rem:optol-interface (3) names the four repairs that would let a run
proceed here -- "Hermitizing, FLOORING THE NEGATIVE PART, renormalizing by
S^{-1/2}, substituting the witness eq:starfam or any other nearby exact
family" -- and forbids all four. Flooring is the tempting one at a defect this
size, and it is a repair of DECLARED INPUT, where "by Proposition
prop:optol-nobound the choice decides the answer".""",
    ),
    AdmissionCase(
        case_id="AD-NEG-below",
        family_id="OPTOL-NEG",
        declared=0.0625,
        admitted=False,
        reason="bob_povm_negative_part",
        branch=None,
        proceeds=False,
        derivation="""\
Delta_pos = 1/8 > 1/16 = eps_dec: refused by rule (2) with
bob_povm_negative_part. The boundary partner of AD-NEG-boundary, differing in
exactly one datum.""",
    ),
    AdmissionCase(
        case_id="AD-2DN-boundary",
        family_id="OPTOL-2D-NEG",
        declared=0.25,
        admitted=True,
        reason="bob_povm_not_evaluable",
        branch="ii",
        proceeds=False,
        derivation="""\
Delta_pos = 1/4 <= 1/4: admitted at the boundary, refused as not evaluable.
The two-dimensional partner of AD-NEG-boundary, where the negative eigenvalue
is invisible to a componentwise sign test (every diagonal entry of F_v0 is
+3/8).""",
    ),
    AdmissionCase(
        case_id="AD-2DN-below",
        family_id="OPTOL-2D-NEG",
        declared=0.125,
        admitted=False,
        reason="bob_povm_negative_part",
        branch=None,
        proceeds=False,
        derivation="""\
Delta_pos = 1/4 > 1/8: refused by rule (2) with bob_povm_negative_part.
Boundary partner of AD-2DN-boundary, differing in exactly one datum. The
defect it names is a genuine EIGENVALUE, -1/4 on the direction
(1, -1)/sqrt(2), while every diagonal entry of F_v0 is +3/8: a refusal that
reported a componentwise minimum would report 3/8 and admit the family.""",
    ),
    # -- (C) boundary pair: THE ONLY BRANCH THAT PROCEEDS --------------------
    AdmissionCase(
        case_id="AD-COMP-boundary",
        family_id="OPTOL-COMP",
        declared=0.125,
        admitted=True,
        reason=OPTOL_ASSURANCE_REASON,
        branch="iii",
        proceeds=True,
        derivation="""\
(C) AT THE BOUNDARY: Delta_cpl = 1/8 <= 1/8 = eps_dec, admitted; and
Delta_herm = Delta_pos = 0, so this is BRANCH (iii) of Theorem thm:optol --
the only branch on which a run proceeds with a nonzero defect.
THE `reason` FIELD HERE IS NOT A REFUSAL. It is
declared_operator_tolerance_open, the ASSURANCE reason of Remark
rem:optol-interface (4): the run produces output, and
optimizer_certificate.assurance is `estimate` with that reason REGARDLESS OF
THE REQUESTED ASSURANCE. `proceeds` is True and no refusal string is carried;
what is withheld is key_length and the certified label, not the run.
See OPTOL_BRANCH_OUTPUTS for what may and may not be emitted.""",
    ),
    AdmissionCase(
        case_id="AD-COMP-below",
        family_id="OPTOL-COMP",
        declared=0.0625,
        admitted=False,
        reason="bob_povm_completeness_defect",
        branch=None,
        proceeds=False,
        derivation="""\
Delta_cpl = 1/8 > 1/16 = eps_dec: refused by rule (2) with
bob_povm_completeness_defect. Boundary partner of AD-COMP-boundary, differing
in exactly one datum -- and the pair spans the whole distance between "no
security output" and "no output at all".""",
    ),
    AdmissionCase(
        case_id="AD-COMP-absent",
        family_id="OPTOL-COMP",
        declared=None,
        admitted=False,
        reason="bob_povm_completeness_defect",
        branch=None,
        proceeds=False,
        derivation="""\
No tolerance declared: eps_dec = 0, Delta_cpl = 1/8 > 0, refused. The
version-0.4.0 refusal character for character (Lemma lem:optol-zero).""",
    ),
    AdmissionCase(
        case_id="AD-2DC-boundary",
        family_id="OPTOL-2D-COMP",
        declared=0.25,
        admitted=True,
        reason=OPTOL_ASSURANCE_REASON,
        branch="iii",
        proceeds=True,
        derivation="""\
Delta_cpl = 1/4 <= 1/4: admitted at the boundary, branch (iii), on one
two-dimensional sector where the defect is a genuine 2x2 spectral quantity and
not a diagonal entry. eps_dec = 1/4 < (|V| + 1)^{-1} = 1/3, so admission alone
GUARANTEES Lemma lem:nearpovm's hypothesis theta < 1 here (see
WIT-2DCOMP).""",
    ),
    AdmissionCase(
        case_id="AD-2DC-below",
        family_id="OPTOL-2D-COMP",
        declared=0.125,
        admitted=False,
        reason="bob_povm_completeness_defect",
        branch=None,
        proceeds=False,
        derivation="""\
Delta_cpl = 1/4 > 1/8: refused by rule (2) with
bob_povm_completeness_defect. Boundary partner of AD-2DC-boundary, differing
in exactly one datum. The defect it names is the SPECTRAL norm of
[[1/8, 1/8], [1/8, 1/8]], whose eigenvalues are {1/4, 0}; a refusal computing
a componentwise maximum would report 1/8 and ADMIT the family at this very
tolerance.""",
    ),
    # -- the undeclared-constant discriminator -------------------------------
    AdmissionCase(
        case_id="AD-SUBC-absent",
        family_id="OPTOL-SUBCONST-C",
        declared=None,
        admitted=False,
        reason="bob_povm_completeness_defect",
        branch=None,
        proceeds=False,
        derivation="""\
THE DISCRIMINATOR CASE. Delta_cpl = 2^-37 = 7.275957614183426e-12 and no
tolerance is declared, so eps_dec = 0 and 2^-37 > 0: REFUSED, reason
bob_povm_completeness_defect.
A validation path that decides POVM completeness inside an UNDECLARED absolute
window of 1e-10 ADMITS this family and computes on it, because
7.28e-12 < 1e-10. At 0.5.0 that is the wrong answer, and the contract leaves
no room to read it otherwise: Section 2.5 says "eps_dec = 0 MEANS EXACT AT
EVERY SITE OF THIS CONTRACT; no default is fixed here or in any artifact
derived from here". A constant is not a small tolerance; it is an undeclared
one, and Assumption A-DTOL exists to say that only a DECLARED one is even a
datum.""",
    ),
    AdmissionCase(
        case_id="AD-SUBC-zero",
        family_id="OPTOL-SUBCONST-C",
        declared=0.0,
        admitted=False,
        reason="bob_povm_completeness_defect",
        branch=None,
        proceeds=False,
        derivation="""\
The same family with zero DECLARED. Identical verdict and identical reason:
absent and declared-zero decide identically here as everywhere.""",
    ),
    AdmissionCase(
        case_id="AD-SUBC-boundary",
        family_id="OPTOL-SUBCONST-C",
        declared=2.0**-37,
        admitted=True,
        reason=OPTOL_ASSURANCE_REASON,
        branch="iii",
        proceeds=True,
        derivation="""\
The same family at eps_dec EQUAL to its defect: Delta_cpl = 2^-37 <= 2^-37,
admitted at the boundary, branch (iii). The run proceeds and emits no
key_length -- which is the SECOND half of the discriminator, and the half an
implementation is most likely to get wrong: declaring a tolerance large enough
to admit the numbers does not buy a key length, and a run that emits one here
has read admission as a licence, exactly the failure the A-DTOL ledger row
describes.""",
    ),
    AdmissionCase(
        case_id="AD-SUBC-above",
        family_id="OPTOL-SUBCONST-C",
        declared=2.0**-33,
        admitted=True,
        reason=OPTOL_ASSURANCE_REASON,
        branch="iii",
        proceeds=True,
        derivation="""\
And at a tolerance sixteen times the defect (2^-33 = 1.1641532182693481e-10,
just above the undeclared 1e-10 the 0.4.0 code applies): admitted, branch
(iii), same verdict as at the boundary. The three SUBCONST-C cases are the
whole discriminator: at absent and at zero the request is REFUSED, at 2^-37
and at 2^-33 it is ADMITTED WITHOUT A KEY LENGTH, and an undeclared window
gives one answer -- "admitted, with a key length" -- to all four.""",
    ),
    AdmissionCase(
        case_id="AD-SUBP-absent",
        family_id="OPTOL-SUBCONST-P",
        declared=None,
        admitted=False,
        reason="bob_povm_negative_part",
        branch=None,
        proceeds=False,
        derivation="""\
The positivity half of the discriminator. Delta_pos = 2^-37 > 0 = eps_dec:
REFUSED with bob_povm_negative_part. The 0.4.0 code compares the minimum
eigenvalue against -1e-10 and admits this family.""",
    ),
    AdmissionCase(
        case_id="AD-SUBP-above",
        family_id="OPTOL-SUBCONST-P",
        declared=2.0**-33,
        admitted=True,
        reason="bob_povm_not_evaluable",
        branch="ii",
        proceeds=False,
        derivation="""\
And with a tolerance above the defect: ADMITTED by rule (2), then REFUSED with
bob_povm_not_evaluable, because Delta_pos > 0 (Theorem thm:optol (ii)).
NO DECLARED TOLERANCE MAKES THIS FAMILY COMPUTABLE. That is what separates a
negative part from a completeness defect at 0.5.0 and it has no analogue at
0.4.0, where both were simply invalid.""",
    ),
    # -- the domain endpoint, on the family that derives it -------------------
    AdmissionCase(
        case_id="AD-ZERO-NEAR-ONE",
        family_id="OPTOL-ZERO",
        declared=0.999,
        admitted=False,
        reason="bob_povm_completeness_defect",
        branch=None,
        proceeds=False,
        derivation="""\
Delta_cpl = 1 > 0.999: refused, at the largest tolerance the declared domain
admits. The all-zero family is inadmissible EVERYWHERE in [0, 1), which is
precisely why the domain stops below 1 -- at eps_dec = 1 it would be admitted,
and "the rule would no longer constrain the family at all" (Remark
rem:optol-interface (1)). The datum eps_dec = 1 is itself refused by
DOM-one.""",
    ),
)


# ---------------------------------------------------------------------------
#  What each branch of Theorem thm:optol may and may not emit
#  -- Theorem thm:optol (i)-(v); Remark rem:optol-interface (3), (4);
#     Sections 2.2 (h_cert, key_length, optimizer_certificate rows)
# ---------------------------------------------------------------------------

#: The six output machine keys of contract Section 2.2, in that section's own
#: order. ``gradient_oracle`` is deliberately absent: Section 2.3 types it as
#: an internal/test API and "NOT serialized in the operator bundle nor in
#: KeyRateResult".
OPTOL_OUTPUT_KEYS: tuple[str, ...] = (
    "h_low",
    "h_cert",
    "key_length",
    "sector_report",
    "optimizer_certificate",
    "operator_tolerance_report",
)


@dataclass(frozen=True)
class BranchOutputs:
    """What one branch of Theorem ``thm:optol`` emits, and what it claims."""

    branch: str
    #: Output keys that MAY be present on this branch, in Section 2.2 order.
    present: tuple[str, ...]
    #: Output keys that are ABSENT on this branch, "not zero, not clamped".
    absent: tuple[str, ...]
    #: The value optimizer_certificate.assurance may take. A one-element tuple
    #: where the branch FORCES it.
    assurance: tuple[str, ...]
    #: The machine-readable reason accompanying `assurance`, or ``None``.
    assurance_reason: str | None
    #: Whether "h_cert <= h_low" is CLAIMED of the numbers reported here.
    hcert_bounds_hlow: bool
    #: Whether h_low is claimed to bound anything.
    hlow_bounds_hqkd: bool
    #: operator_tolerance_report.key_length_claim on this branch.
    key_length_claim: bool
    derivation: str


OPTOL_BRANCH_OUTPUTS: tuple[BranchOutputs, ...] = (
    BranchOutputs(
        branch="i",
        present=OPTOL_OUTPUT_KEYS,
        absent=(),
        assurance=("estimate", "certified"),
        assurance_reason=None,
        hcert_bounds_hlow=True,
        hlow_bounds_hqkd=True,
        key_length_claim=True,
        derivation="""\
THEOREM thm:optol (i): "If Delta_herm = Delta_pos = Delta_cpl = 0 then D
satisfies Assumption A-DECL in full and EVERY CLAIM C1-C20 OF THIS CONTRACT
APPLIES TO THE DECLARED NUMBERS EXACTLY AS AT VERSION 0.4.0."
So this branch is the 0.4.0 interface, unchanged, PLUS the new
operator_tolerance_report. Every output may be present; h_cert satisfies
h_cert <= h_low unconditionally (Theorem thm:cert); h_low bounds h_qkd
(Theorem thm:reduction); key_length is emitted when the rest of the interface
allows it; and assurance is whatever the four check groups of Section 4.18
achieve, `certified` included.
`absent` IS EMPTY HERE ONLY WITH RESPECT TO THE TOLERANCE. The 0.4.0 absence
rules stand untouched: key_length is still withheld when h_low = +infinity
(Remark rem:hlow-range), and h_cert is still present only on a run whose
requested assurance is `certified` and whose checks all passed. Those grounds
are independent of the tolerance and this table does not restate them.""",
    ),
    BranchOutputs(
        branch="ii",
        present=(),
        absent=OPTOL_OUTPUT_KEYS,
        assurance=(),
        assurance_reason=None,
        hcert_bounds_hlow=False,
        hlow_bounds_hqkd=False,
        key_length_claim=False,
        derivation="""\
THEOREM thm:optol (ii): "If Delta_herm > 0 or Delta_pos > 0 then the objects
of Lemma lem:optol-defined (i) -- among them G_chat, K_chat and, for every
declaration that generates key at all, O_alpha and h_low -- ARE NOT DEFINED on
the declared numbers, and THIS CONTRACT SPECIFIES NO COMPUTATION ON THEM."
There is therefore NO RESULT: the request is refused with
bob_povm_not_evaluable and no output row of Section 2.2 has a value. `present`
is empty, `assurance` is empty -- not `estimate`, because an assurance is a
property of a result and there is none -- and both claim flags are false
vacuously.
WHY NOT "COMPUTE ANYWAY AND LABEL IT ESTIMATE". Because there is nothing to
compute: sqrt(F_v) does not exist, and "every way of proceeding -- Hermitizing,
flooring the negative part, renormalizing by S^{-1/2}, substituting the
witness eq:starfam or any other nearby exact family -- IS A REPAIR OF DECLARED
DATA, WHICH THIS CONTRACT FORBIDS" (Remark rem:optol-interface (3)).
THE DEGENERATE CASE IS REFUSED TOO, on the second ground alone: a declaration
with Chat_key empty has no K-term in eq:objective, so lem:optol-defined (i)'s
argument does not reach its objective -- "that objective is not thereby
defined either (at Delta_pos > 0 some P_chat(omega) can be negative and at
Delta_herm > 0 non-real, while the kernel d(u, v) of Lemma foundations/lem:kernel is
defined only for v >= 0), and such a declaration produces no key at all, so
refusing it costs nothing and this rule stays one rule rather than two".
WHAT AN IMPLEMENTATION MAY STILL REPORT IS THE DEFECTS THEMSELVES: rule (2)
and rule (3) refusals carry "the measured defect and the declared eps_dec".
Whether that arrives as the operator_tolerance_report record or as refusal
metadata is interface.yaml open choice OC-6, and this table does not decide
it -- which is why operator_tolerance_report is listed under `absent` here as
an OUTPUT ROW OF A RESULT, not as a claim that the numbers are withheld.""",
    ),
    BranchOutputs(
        branch="iii",
        present=(
            "h_low",
            "h_cert",
            "sector_report",
            "optimizer_certificate",
            "operator_tolerance_report",
        ),
        absent=("key_length",),
        assurance=("estimate",),
        assurance_reason=OPTOL_ASSURANCE_REASON,
        hcert_bounds_hlow=False,
        hlow_bounds_hqkd=False,
        key_length_claim=False,
        derivation="""\
THEOREM thm:optol (iii) and Remark rem:optol-interface (4), the ONE branch on
which a run proceeds with a nonzero defect. Delta_herm = Delta_pos = 0 <
Delta_cpl <= eps_dec.
WHAT IS EMITTED: "h_low, h_cert, sector_report and optimizer_certificate may
be reported as EXPLORATION output, AND AS THAT ALONE."
WHAT IS NOT: "key_length is NOT emitted", and it is absent rather than zero or
clamped (Section 2.2, the key_length row: "Absent -- not zero, not clamped --
when the declared bob_povm is admitted with a nonzero defect").
WHAT IS NOT CLAIMED, and this is the substance:
  * h_low "is a lower bound on NOTHING": h_qkd is not defined for the declared
    numbers, M_prot not being a channel (lem:optol-defined (iii)), so no
    inequality of this contract bounds it. Even h_low >= 0 of Remark
    rem:hlow-range is unavailable, that bound resting on both arguments of the
    divergence being probability vectors.
  * h_cert "carries NO claim of h_cert <= h_low on this branch, Theorem
    thm:cert not being established for the declared numbers (its support
    reaches, through the spectral window of Lemma lem:window (i), the
    trace-non-increasing clause Lemma lem:optol-defined (iii) names as
    failing)". Section 2.2's h_cert row says the same in its own words.
  * sector_report "OMITS the state-blindness consequence sum_v c_{v,s} = 1"
    (Lemma lem:optol-defined (iii): "sector_report must not report it"). The
    DEFINING clause F^{(s)}_v = c_{v,s} 1_{Q_s} survives, and with it
    thm:removal and the `removable` flag, so the rest of the table stands.
ASSURANCE IS FORCED: "optimizer_certificate.assurance is ESTIMATE with the
machine-readable reason declared_operator_tolerance_open REGARDLESS OF THE
REQUESTED ASSURANCE -- a `certified` label is a statement about a key rate,
and Theorem thm:optol (iii) asserts none."
THIS IS THE CList DISCIPLINE OF SECTION 4.22 APPLIED TO A SECOND INPUT:
"valid arithmetic, no security output."
WHETHER THE POST-PROCESSING RUNS AT ALL is interface.yaml open choice OC-7:
"may be reported" is a permission, and an implementation that skips Section
4.18 here and reports h_cert and optimizer_certificate absent satisfies it
equally. Neither reading can produce a certified label.""",
    ),
)


# ---------------------------------------------------------------------------
#  operator_tolerance_report, field for field -- Section 2.2; Remark
#  rem:optol-interface (5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToleranceReport:
    """The six fields and two per-outcome vectors, on one named request.

    The contract fixes the CONTENT of this record and two of its machine keys
    (``exactly_admissible``, ``key_length_claim``); it fixes no key for the
    four numbers or the two vectors, and interface.yaml records that as open
    choice OC-2. This table is therefore stated in the contract's own
    mathematical names.
    """

    case_id: str
    family_id: str
    #: The declared eps_dec as the report carries it: "the declared eps_dec
    #: VERBATIM". ``None`` where the request declared none -- how that is
    #: PRESENTED is open choice OC-3; what it DECIDES is eps_dec = 0.
    declared: float | None
    delta_herm: float
    delta_pos: float
    delta_cpl: float
    per_outcome_hermiticity: tuple[float, ...]
    per_outcome_negative: tuple[float, ...]
    exactly_admissible: bool
    key_length_claim: bool
    derivation: str


OPTOL_REPORT_CASES: tuple[ToleranceReport, ...] = (
    ToleranceReport(
        case_id="REPORT-EXACT-absent",
        family_id="OPTOL-EXACT",
        declared=None,
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=0.0,
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        exactly_admissible=True,
        key_length_claim=True,
        derivation="""\
THE SENTENCE THIS CASE FREEZES, from Remark rem:optol-interface (5): "At
eps_dec = 0 the report is (0, 0, 0, 0, TRUE, TRUE) and ADDS NOTHING TO THE
VERSION-0.4.0 ARTIFACT."
Four zeros -- the declared eps_dec and the three defects -- then the two
booleans. The two per-outcome vectors are all-zero with them, each entry being
one of the quantities whose maximum is a zero above.
THAT IT ADDS NOTHING IS THE LOAD-BEARING HALF. Every existing 0.4.0 golden
value was produced on an exactly admissible declaration with no tolerance
declared, so this is the report EVERY ONE OF THEM CARRIES, and the amendment
changes not one of their numbers.""",
    ),
    ToleranceReport(
        case_id="REPORT-EXACT-quarter",
        family_id="OPTOL-EXACT",
        declared=0.25,
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=0.0,
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        exactly_admissible=True,
        key_length_claim=True,
        derivation="""\
THE SAME FAMILY WITH A TOLERANCE DECLARED. The report carries the declared 1/4
VERBATIM -- "the declared eps_dec verbatim", not the measured defects, not a
clamp, not a zero -- and the three defects are still 0, so both booleans are
still TRUE.
THE PAIR (REPORT-EXACT-absent, REPORT-EXACT-quarter) IS THE ONE THAT CATCHES
THE WRONG READING. An implementation that derives exactly_admissible or
key_length_claim from the DECLARED tolerance rather than from the MEASURED
defects reports false here and withholds a key length the contract awards:
Theorem thm:optol (i) says "declaring a tolerance NEVER WEAKENS a run whose
data does not use it". The two booleans are functions of the three defects
alone.""",
    ),
    ToleranceReport(
        case_id="REPORT-COMP-boundary",
        family_id="OPTOL-COMP",
        declared=0.125,
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=0.125,
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        exactly_admissible=False,
        key_length_claim=False,
        derivation="""\
BRANCH (iii), field for field: (1/8, 0, 0, 1/8, false, false). The declared
tolerance and the completeness defect happen to be EQUAL here, which is what
the boundary case means; they are two different fields and an implementation
that reports one for the other passes this case and fails
REPORT-2DCOMP-boundary, where they are also equal, but fails
REPORT-SUBC-above, where they are not.
exactly_admissible is false because Delta_cpl > 0 -- NOT because a tolerance
was declared -- and key_length_claim EQUALS it, so it is false too. Remark
rem:optol-interface (5): "A composition that consumes this module's output
must read key_length_claim: WHEN IT IS FALSE THE ARTIFACT CARRIES NO
KEY-LENGTH CLAIM OF THIS CONTRACT, AND NO DOWNSTREAM STEP MAY SUPPLY ONE."
The per-outcome vectors are all-zero: neither Delta_herm nor Delta_pos is the
defect here, and the report still carries both vectors.""",
    ),
    ToleranceReport(
        case_id="REPORT-2DCOMP-boundary",
        family_id="OPTOL-2D-COMP",
        declared=0.25,
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=0.25,
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        exactly_admissible=False,
        key_length_claim=False,
        derivation="""\
The same branch on one two-dimensional sector: (1/4, 0, 0, 1/4, false, false).
Frozen beside REPORT-COMP-boundary because Delta_cpl = 1/4 here is the
SPECTRUM of [[1/8, 1/8], [1/8, 1/8]] and not any entry of it; an
implementation reporting a componentwise maximum reports 1/8 and passes every
case in this table except this one.""",
    ),
    ToleranceReport(
        case_id="REPORT-SUBC-above",
        family_id="OPTOL-SUBCONST-C",
        declared=2.0**-33,
        delta_herm=0.0,
        delta_pos=0.0,
        delta_cpl=2.0**-37,
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.0, 0.0),
        exactly_admissible=False,
        key_length_claim=False,
        derivation="""\
THE CASE WHERE THE DECLARED TOLERANCE AND THE MEASURED DEFECT DIFFER, and both
are small: (2^-33, 0, 0, 2^-37, false, false), i.e.
(1.1641532182693481e-10, 0, 0, 7.275957614183426e-12, false, false).
TWO FIELDS, TWO VALUES, SIXTEEN-FOLD APART. Both are exact binary rationals,
so an implementation that confuses them, or that rounds either to zero for
display, is caught here and nowhere else in this table.
AND exactly_admissible IS FALSE AT A DEFECT OF 7.3e-12. There is no threshold
below which a defect stops counting: the boolean is "Delta_herm = Delta_pos =
Delta_cpl = 0" and 2^-37 is not 0. key_length_claim follows it and is false,
so this run -- admitted, arithmetically fine, defect twelve orders of
magnitude below one -- CARRIES NO KEY-LENGTH CLAIM.""",
    ),
    ToleranceReport(
        case_id="REPORT-HERM-boundary",
        family_id="OPTOL-HERM",
        declared=0.25,
        delta_herm=0.25,
        delta_pos=0.0,
        delta_cpl=0.0,
        per_outcome_hermiticity=(0.25, 0.25),
        per_outcome_negative=(0.0, 0.0),
        exactly_admissible=False,
        key_length_claim=False,
        derivation="""\
THE CONTENT OF THE RECORD ON A REFUSED REQUEST. The family is admitted at
eps_dec = 1/4 and then refused as not evaluable, and Remark
rem:optol-interface (2) requires the refusal to carry "the measured defect and
the declared eps_dec" -- which is these numbers: (1/4, 1/4, 0, 0, false,
false), with the per-outcome Hermiticity vector (1/4, 1/4).
BOTH ENTRIES OF THAT VECTOR ARE THE MAXIMUM, which is the case that shows the
vector is not "the argmax": Section 2.2 asks for "the per-outcome quantities
... THAT ATTAIN THE FIRST TWO", one number per outcome, and here both attain
it.
WHETHER THESE NUMBERS ARRIVE AS THE operator_tolerance_report RECORD or as
refusal metadata is interface.yaml open choice OC-6 and is NOT decided here.
What is frozen is their VALUES.""",
    ),
    ToleranceReport(
        case_id="REPORT-NEG-boundary",
        family_id="OPTOL-NEG",
        declared=0.125,
        delta_herm=0.0,
        delta_pos=0.125,
        delta_cpl=0.0,
        per_outcome_hermiticity=(0.0, 0.0),
        per_outcome_negative=(0.125, 0.0),
        exactly_admissible=False,
        key_length_claim=False,
        derivation="""\
(1/8, 0, 1/8, 0, false, false) with the per-outcome NEGATIVE vector (1/8, 0).
Here the maximum is attained by ONE outcome only, so this case and
REPORT-HERM-boundary between them pin both shapes the per-outcome vectors can
take. An implementation that reports the maximum twice, or that reports a
single index instead of a vector, fails one of the two.""",
    ),
)


# ---------------------------------------------------------------------------
#  Lemma lem:nearpovm -- the exactly admissible family the numbers declare
#  (Theorem thm:optol (iv)), and its converse
# ---------------------------------------------------------------------------

#: ``(|V| + 1)^{-1}`` for the two-outcome families of this group: the
#: threshold BELOW which admission alone guarantees Lemma lem:nearpovm's
#: hypothesis theta < 1 (Remark rem:optol-interface (1)). It is NOT the
#: declared domain's endpoint and the two must not be conflated.
OPTOL_WITNESS_GUARANTEE_THRESHOLD: float = 1.0 / 3.0


@dataclass(frozen=True)
class NearPovmWitness:
    """One evaluation of Lemma ``lem:nearpovm`` on a frozen family.

    THE WITNESS IS A WITNESS AND NOT A SUBSTITUTE (Remark
    ``rem:optol-witness``): "no run computes it, no output reports it, and
    substituting it -- or any other exactly admissible family within
    eps_dec_star -- for the declared numbers is FORBIDDEN". It is frozen here
    because Theorem ``thm:optol`` (iv) quantifies over such families and a test
    of that quantifier needs at least one of them exhibited.
    """

    case_id: str
    family_id: str
    #: ``theta = Delta_cpl + |V| Delta_pos`` of Lemma lem:nearpovm.
    theta: float
    #: ``eps_dec_star = Delta_herm/2 + Delta_pos + theta(1+theta)/(1-theta)``,
    #: Eq. eq:nearpovm.
    eps_dec_star: float
    #: ``{F*_v}`` of Eq. eq:starfam, exactly, in outcome order.
    star_elements: tuple[OptolMatrix, ...]
    #: ``||F_v - F*_v||`` per outcome; its maximum is what eq:nearpovm bounds.
    distances: tuple[float, ...]
    #: ``eta = max_v ||F_v - F*_v||``, the converse half's hypothesis.
    eta: float
    #: ``max{2, |V|} eta``, the tolerance Eq. eq:nearpovm-conv shows sufficient
    #: for admission of a family within eta of an exactly admissible one.
    sufficient_tolerance: float
    #: Whether admission at the frozen tolerance GUARANTEES theta < 1, i.e.
    #: whether that tolerance is below (|V| + 1)^{-1}.
    theta_guaranteed_by_admission: bool
    derivation: str


OPTOL_WITNESS_CASES: tuple[NearPovmWitness, ...] = (
    NearPovmWitness(
        case_id="WIT-COMP",
        family_id="OPTOL-COMP",
        theta=0.125,
        eps_dec_star=9.0 / 56.0,
        star_elements=(
            ((0.5 + 0j, 0j), (0j, 8.0 / 9.0 + 0j)),
            ((0.5 + 0j, 0j), (0j, 1.0 / 9.0 + 0j)),
        ),
        distances=(1.0 / 9.0, 1.0 / 72.0),
        eta=1.0 / 9.0,
        sufficient_tolerance=2.0 / 9.0,
        theta_guaranteed_by_admission=True,
        derivation="""\
LEMMA lem:nearpovm, forward half, carried out on OPTOL-COMP
(F_v0 = diag(1/2, 1), F_v1 = diag(1/2, 1/8)), step by step as the proof
states them.
  H_v := (F_v + F_v^dagger)/2 = F_v, both already Hermitian, so ||F_v - H_v||
         = Delta_herm/2 = 0.
  theta := Delta_cpl + |V| Delta_pos = 1/8 + 2 . 0 = 1/8 < 1, so the lemma
         applies.
  G_v := H_v + Delta_pos . 1_Q = H_v, since Delta_pos = 0.
  S  := sum_v G_v = diag(1, 9/8), Hermitian with
        ||S - 1_Q|| = 1/8 = theta < 1, so
        (1 - theta) 1_Q <= S <= (1 + theta) 1_Q and S is invertible.
  S^{-1/2} = diag(1, sqrt(8/9)) = diag(1, 2 sqrt(2)/3).
  F*_v := S^{-1/2} G_v S^{-1/2}:
        F*_v0 = diag(1/2 . 1, 1 . 8/9)   = diag(1/2, 8/9)
        F*_v1 = diag(1/2 . 1, 1/8 . 8/9) = diag(1/2, 1/9)
THE WITNESS IS EXACTLY RATIONAL even though S^{-1/2} is not: the irrational
entry 2 sqrt(2)/3 appears squared in every product.
CHECK THAT IT IS EXACTLY ADMISSIBLE: sum_v F*_v = diag(1, 8/9 + 1/9)
= diag(1, 1) = 1_Q; both are diagonal with non-negative entries. By Lemma
lem:optol-zero it is exactly admissible.
THE DISTANCE (Eq. eq:nearpovm):
  ||F_v0 - F*_v0|| = ||diag(0, 1 - 8/9)||   = 1/9  = 0.1111...
  ||F_v1 - F*_v1|| = ||diag(0, 1/8 - 1/9)|| = 1/72 = 0.01388...
  max = 1/9, and the lemma's bound is
  eps_dec_star = (1/2) . 0 + 0 + theta(1 + theta)/(1 - theta)
               = (1/8)(9/8)/(7/8) = (1/8)(9/7) = 9/56 = 0.16071428571428573.
  1/9 <= 9/56 holds with room: 0.1111 <= 0.1607.
THE CONVERSE HALF (Eq. eq:nearpovm-conv) with eta = 1/9:
  Delta_herm = 0   <= 2 eta   = 2/9
  Delta_pos  = 0   <= eta     = 1/9
  Delta_cpl  = 1/8 <= |V| eta = 2/9      (0.125 <= 0.2222)
  and "a family satisfying (T) that lies within eta of an exactly admissible
  one is eps_dec-admissible for every eps_dec >= max{2, |V|} eta" = 2/9.
  Delta_cpl = 1/8 <= 2/9 confirms it.
THE GUARANTEE. This family is admitted at eps_dec = 1/8, which is below
(|V| + 1)^{-1} = 1/3, so theta <= (|V| + 1) eps_dec = 3/8 < 1 is guaranteed BY
THE ADMISSION RULE and not only by the measured defects.
AND WHAT IT DOES NOT BUY. Theorem thm:optol (iv): every claim C1-C20 applies
to the SUBSTITUTED declaration D* verbatim, with h_qkd defined and -- for
alpha in (1, 2) -- Theorem thm:keylength available. "The numbers a run
computes are those of D, and NOTHING THIS CONTRACT CAN STATE RELATES THE TWO."
See OPTOL_NOBOUND_CASES.""",
    ),
    NearPovmWitness(
        case_id="WIT-2DCOMP",
        family_id="OPTOL-2D-COMP",
        theta=0.25,
        eps_dec_star=5.0 / 12.0,
        star_elements=(
            ((0.65 + 0j, 0.15 + 0j), (0.15 + 0j, 0.65 + 0j)),
            ((0.35 + 0j, -0.15 + 0j), (-0.15 + 0j, 0.35 + 0j)),
        ),
        distances=(0.2, 0.05),
        eta=0.2,
        sufficient_tolerance=0.4,
        theta_guaranteed_by_admission=True,
        derivation="""\
The same construction on one TWO-DIMENSIONAL sector, where S^{-1/2} is a
genuine matrix function.
  Delta_herm = Delta_pos = 0, so H_v = G_v = F_v and theta = Delta_cpl = 1/4.
  S = F_v0 + F_v1 = [[9/8, 1/8], [1/8, 9/8]].
All three of F_v0, F_v1 and S are of the form [[a, b], [b, a]], hence
SIMULTANEOUSLY DIAGONAL in the basis p+ = (1, 1)/sqrt(2), p- = (1, -1)/sqrt(2),
where
  F_v0 = diag(1, 1/2),  F_v1 = diag(1/4, 1/2),  S = diag(5/4, 1).
  S^{-1/2} = diag(2/sqrt(5), 1), so
  F*_v0 = diag(1 . 4/5, 1/2)   = diag(4/5, 1/2)
  F*_v1 = diag(1/4 . 4/5, 1/2) = diag(1/5, 1/2)
and sum_v F*_v = diag(1, 1) = 1_Q with both blocks non-negative: exactly
admissible.
BACK IN THE COMPUTATIONAL BASIS, with P+ = (1/2)[[1, 1], [1, 1]] and
P- = (1/2)[[1, -1], [-1, 1]]:
  F*_v0 = (4/5) P+ + (1/2) P- = [[13/20, 3/20], [3/20, 13/20]]
  F*_v1 = (1/5) P+ + (1/2) P- = [[7/20, -3/20], [-3/20, 7/20]]
  and F*_v0 + F*_v1 = [[1, 0], [0, 1]] exactly.
THE DISTANCE, read off in the eigenbasis:
  ||F_v0 - F*_v0|| = ||diag(1 - 4/5, 0)||   = 1/5  = 0.2
  ||F_v1 - F*_v1|| = ||diag(1/4 - 1/5, 0)|| = 1/20 = 0.05
  max = 1/5, and eps_dec_star = 0 + 0 + (1/4)(5/4)/(3/4) = (1/4)(5/3) = 5/12
  = 0.4166666666666667. 0.2 <= 0.4167 holds.
CONVERSE with eta = 1/5: Delta_herm = 0 <= 2/5, Delta_pos = 0 <= 1/5,
Delta_cpl = 1/4 <= |V| eta = 2/5, and max{2, |V|} eta = 2/5 suffices for
admission (1/4 <= 2/5).
GUARANTEE: admitted at eps_dec = 1/4 < 1/3 = (|V| + 1)^{-1}, so theta < 1 is
guaranteed by the admission rule.""",
    ),
    NearPovmWitness(
        case_id="WIT-HERM",
        family_id="OPTOL-HERM",
        theta=0.0,
        eps_dec_star=0.125,
        star_elements=(
            ((0.5 + 0j, 0j), (0j, 1 + 0j)),
            ((0.5 + 0j, 0j), (0j, 0j)),
        ),
        distances=(0.125, 0.125),
        eta=0.125,
        sufficient_tolerance=0.25,
        theta_guaranteed_by_admission=True,
        derivation="""\
THE CASE WHERE BOTH HALVES OF LEMMA lem:nearpovm ARE ATTAINED, which is what
makes it worth freezing: a bound that is never tight is a bound no test can
distinguish from a looser one.
  Delta_herm = 1/4, Delta_pos = Delta_cpl = 0, so theta = 0 and the
  construction reduces to its first step:
  H_v = (F_v + F_v^dagger)/2 = diag(1/2, 1) and diag(1/2, 0);
  G_v = H_v (Delta_pos = 0); S = sum_v H_v = 1_Q; S^{-1/2} = 1_Q; and
  F*_v = H_v.
SO THE WITNESS FOR OPTOL-HERM IS EXACTLY OPTOL-EXACT -- the same family the
0.2.4-era TOY-1 declares. That is a coincidence of this construction and not a
general fact, and it is a useful one: the exactly admissible neighbour here is
a family whose h_low the registry already froze.
FORWARD, ATTAINED: ||F_v - F*_v|| = ||diag(0, +/- i/8)|| = 1/8 for both
outcomes, and eps_dec_star = (1/2)(1/4) + 0 + 0 = 1/8. The bound is an
EQUALITY.
CONVERSE, ALSO ATTAINED: with eta = 1/8, Eq. eq:nearpovm-conv gives
Delta_herm <= 2 eta = 1/4 -- and Delta_herm IS 1/4. The factor 2 in the
converse is therefore not slack.
AND THE FAMILY IS STILL REFUSED. Theorem thm:optol (iv) applies to it -- an
exactly admissible neighbour exists, at distance exactly eps_dec_star, and
every claim C1-C20 holds of THAT family -- while the DECLARED family is
refused as not evaluable by (ii). "Substituting it ... for the declared
numbers is FORBIDDEN" (Remark rem:optol-witness). The existence of a perfect
neighbour one eighth away is precisely not a licence to use it.""",
    ),
    NearPovmWitness(
        case_id="WIT-NEG",
        family_id="OPTOL-NEG",
        theta=0.25,
        eps_dec_star=13.0 / 24.0,
        star_elements=(
            ((0j, 0j), (0j, 0.9 + 0j)),
            ((1 + 0j, 0j), (0j, 0.1 + 0j)),
        ),
        distances=(0.125, 0.125),
        eta=0.125,
        sufficient_tolerance=0.25,
        theta_guaranteed_by_admission=True,
        derivation="""\
The one case in which the lemma's MIDDLE step -- the shift by Delta_pos --
does work.
  Delta_herm = 0, Delta_pos = 1/8, Delta_cpl = 0, so
  theta = Delta_cpl + |V| Delta_pos = 0 + 2 . (1/8) = 1/4 < 1.
  H_v = F_v (both Hermitian).
  G_v = H_v + (1/8) 1_Q:
        G_v0 = diag(-1/8 + 1/8, 1 + 1/8)     = diag(0, 9/8)
        G_v1 = diag(9/8 + 1/8, 0 + 1/8)      = diag(5/4, 1/8)
  and both are positive semidefinite, which is the step's whole purpose:
  lambda_min(H_v) >= -Delta_pos, so G_v >= 0.
  S = sum_v G_v = diag(0 + 5/4, 9/8 + 1/8) = diag(5/4, 5/4) = (5/4) 1_Q,
  with ||S - 1_Q|| = 1/4 = theta.
  S^{-1/2} = sqrt(4/5) 1_Q, so F*_v = (4/5) G_v:
        F*_v0 = diag(0, 9/10),  F*_v1 = diag(1, 1/10)
  and sum_v F*_v = diag(1, 1) = 1_Q, both non-negative: exactly admissible.
THE DISTANCE:
  ||F_v0 - F*_v0|| = ||diag(-1/8 - 0, 1 - 9/10)|| = ||diag(-1/8, 1/10)||
                   = 1/8, the larger modulus (1/8 = 0.125 > 0.1);
  ||F_v1 - F*_v1|| = ||diag(9/8 - 1, 0 - 1/10)|| = ||diag(1/8, -1/10)|| = 1/8.
  max = 1/8, and eps_dec_star = 0 + 1/8 + (1/4)(5/4)/(3/4) = 1/8 + 5/12
  = 3/24 + 10/24 = 13/24 = 0.5416666666666666. 0.125 <= 0.5417 holds, loosely.
CONVERSE with eta = 1/8: Delta_pos = 1/8 <= eta = 1/8, ATTAINED; Delta_herm
= 0 <= 1/4; Delta_cpl = 0 <= 1/4; and max{2, |V|} eta = 1/4 suffices.
THE FAMILY IS STILL REFUSED AS NOT EVALUABLE at every tolerance (branch (ii)),
and F*_v0 = diag(0, 9/10) is what "renormalizing by S^{-1/2}" would produce --
the second of the four repairs Remark rem:optol-interface (3) forbids by
name.""",
    ),
)


# ---------------------------------------------------------------------------
#  Proposition prop:optol-nobound -- no uniform robustness, in either
#  direction, as DATA
# ---------------------------------------------------------------------------
#
#  The instance is the one Remark rem:hlow-range already constructs and this
#  proposition evaluates at two parameter values: d_A = d_Q = 1 (so both source
#  modes coincide and Feas = {[1]}), one sector, X = {x0} with M_x0 = [1],
#  V = {v0, v1}, a_A constant and a_B = id, phi(kappa) = c_B so Chat = V,
#  ALL-FAIL SIFTING (r == perp, holder B with r_B == perp, hence Chat_key
#  empty), CList empty, the default party partition, and the singleton
#  acceptance set AcceptSet = {(1, 0)}.
#  On it, Eq. eq:optol-instance gives, for F_v0 = [g0] and F_v1 = [g1] with
#  g0 > 0 and g1 >= 0 -- AND USING NO PROPERTY OF (g0, g1) BEYOND THOSE TWO
#  INEQUALITIES, in particular not g0 + g1 = 1 --
#      h_low[D_(g0, g1)] = (alpha/(alpha - 1)) log2(1/g0).
#  The convention 0 log2(0/v) = 0 of Definition foundations/def:kl is what kills the
#  second term, and Chat_key empty is what removes the entropy part, so the whole
#  value is the acceptance-test penalty. THAT IS WHERE BOTH GAPS LIVE (Remark
#  rem:optol-direction), and it is why neither depends on the entropy term.


def _nobound_hlow(g0: float) -> Callable[[float], float]:
    """Return ``alpha -> (alpha/(alpha-1)) log2(1/g0)`` (Eq. eq:optol-instance)."""

    def form(alpha: float) -> float:
        return (alpha / (alpha - 1.0)) * math.log2(1.0 / g0)

    return form


@dataclass(frozen=True)
class NoBoundCase:
    """One evaluation of Proposition ``prop:optol-nobound`` as frozen data."""

    case_id: str
    #: "i" or "ii" -- which part of the proposition this instantiates.
    part: str
    #: The declared ``(g0, g1)``.
    declared: tuple[float, float]
    #: ``(Delta_herm, Delta_pos, Delta_cpl)`` of the declared family.
    declared_defects: tuple[float, float, float]
    #: The two exactly admissible families, as ``(g0, g1)`` pairs.
    family_one: tuple[float, float]
    family_two: tuple[float, float]
    #: ``max_v ||F^(i)_v - F_v||`` for i = 1, 2.
    distance_one: float
    distance_two: float
    #: The distance the case must respect: ``epsilon`` in part (i),
    #: ``eps_dec_star`` in part (ii).
    distance_bound: float
    #: The prescribed bound B the gap must exceed.
    bound_b: float
    #: WHICH TWO VALUES `gap_form` MEASURES, as an ordered pair of the names
    #: "declared", "family_one" and "family_two": the gap is
    #: ``h_low[first] - h_low[second]`` and is POSITIVE. The pair is data
    #: because the DIRECTION is the proposition's content: part (ii) exhibits
    #: an admitted defective declaration ABOVE one exactly admissible
    #: neighbour, and a second declared family BELOW the other, at the same
    #: tolerance and with the same neighbours (Remark rem:optol-direction).
    gap_between: tuple[str, str]
    #: ``alpha -> `` the gap the proposition exhibits, in bits per round.
    gap_form: Callable[[float], float]
    frozen_gap: tuple[tuple[float, float], ...]
    derivation: str


OPTOL_NOBOUND_CASES: tuple[NoBoundCase, ...] = (
    NoBoundCase(
        case_id="NB-i-eps-half-B3",
        part="i",
        declared=(0.5, 0.5),
        declared_defects=(0.0, 0.0, 0.0),
        family_one=(0.0625, 0.9375),
        family_two=(0.5, 0.5),
        distance_one=0.4375,
        distance_two=0.0,
        distance_bound=0.5,
        bound_b=3.0,
        gap_between=("family_one", "family_two"),
        gap_form=lambda alpha: (alpha / (alpha - 1.0)) * 3.0,
        frozen_gap=_freeze(lambda alpha: (alpha / (alpha - 1.0)) * 3.0),
        derivation="""\
PROPOSITION prop:optol-nobound (i) at epsilon = 1/2 and B = 3, so
N = ceil(B) = 3.
  D  := D_(epsilon, 1 - epsilon) = D_(1/2, 1/2)
  {F^(2)_v} := {F_v} itself, at distance 0;
  {F^(1)_v} := the POVM of D_(epsilon 2^-N, 1 - epsilon 2^-N)
             = D_(1/16, 15/16), at distance
             epsilon (1 - 2^-N) = (1/2)(7/8) = 7/16 = 0.4375 <= 1/2 = epsilon
             in each of its two entries.
ALL THREE FAMILIES ARE EXACT POVMS: non-negative entries summing to 1
(1/2 + 1/2 = 1 and 1/16 + 15/16 = 1), so all three are EXACTLY ADMISSIBLE
by Lemma lem:optol-zero, and D satisfies Assumption A-DECL IN FULL.
THAT IS THE POINT OF PART (i). "They do not locate the fragility in the
defects: in part (i) BOTH FAMILIES ARE EXACT POVMs, so the phenomenon belongs
to the map {F_v} -> h_low and would be there for a supplier that emitted
perfect numbers for a slightly different device" (Remark
rem:optol-direction).
THE VALUES, by Eq. eq:optol-instance:
  h_low[D^(1)] = (alpha/(alpha-1)) log2(1/(1/16)) = (alpha/(alpha-1)) . 4
  h_low[D^(2)] = (alpha/(alpha-1)) log2(1/(1/2))  = (alpha/(alpha-1)) . 1
  gap = h_low[D^(1)] - h_low[D^(2)] = (alpha/(alpha-1)) . 3
      >= 3 = N >= B,  using alpha/(alpha-1) > 1 for alpha > 1.
At alpha = 3/2 the gap is 9 bits per round between two exact POVMs whose
entries differ by 7/16.
THE DIMENSIONS DO NOT MOVE WITH B: d_A = d_Q = 1, one sector, |X| = 1,
|V| = |Chat| = 2, d_Z = 1, whatever B is. So no function of the declared
dimensions, alphabet sizes, alpha and tolerance bounds the gap.""",
    ),
    NoBoundCase(
        case_id="NB-i-eps-quarter-B1",
        part="i",
        declared=(0.25, 0.75),
        declared_defects=(0.0, 0.0, 0.0),
        family_one=(0.125, 0.875),
        family_two=(0.25, 0.75),
        distance_one=0.125,
        distance_two=0.0,
        distance_bound=0.25,
        bound_b=1.0,
        gap_between=("family_one", "family_two"),
        gap_form=lambda alpha: (alpha / (alpha - 1.0)) * 1.0,
        frozen_gap=_freeze(lambda alpha: (alpha / (alpha - 1.0)) * 1.0),
        derivation="""\
The SECOND parameter value the provenance block refers to
("the instance ... evaluated at two parameter values"): epsilon = 1/4, B = 1,
N = 1.
  D = D_(1/4, 3/4); {F^(2)} = D's own POVM; {F^(1)} = D_(1/8, 7/8) at distance
  epsilon(1 - 2^-1) = 1/8 <= 1/4.
  gap = (alpha/(alpha-1)) log2((1/4)/(1/8)) = (alpha/(alpha-1)) . 1 >= 1 = B.
Frozen beside NB-i-eps-half-B3 so that the gap's DEPENDENCE ON N is data: the
two cases share every dimension and alphabet and differ only in epsilon and B,
and their gaps stand in the ratio 3 : 1 at every alpha. A bound that grew with
the dimensions would not distinguish them; nothing does, which is the
non-existence statement.""",
    ),
    NoBoundCase(
        case_id="NB-ii-c-half-B2",
        part="ii",
        declared=(0.125, 0.375),
        declared_defects=(0.0, 0.0, 0.5),
        family_one=(0.625, 0.375),
        family_two=(0.125, 0.875),
        distance_one=0.5,
        distance_two=0.5,
        distance_bound=1.5,
        bound_b=2.0,
        gap_between=("declared", "family_one"),
        gap_form=lambda alpha: (alpha / (alpha - 1.0)) * math.log2(5.0),
        frozen_gap=_freeze(lambda alpha: (alpha / (alpha - 1.0)) * math.log2(5.0)),
        derivation="""\
PROPOSITION prop:optol-nobound (ii), THE PART THEOREM thm:optol (iv) CONSUMES.
At c = 1/2 and B = 2, so N = 2 and t must satisfy
0 < t <= min{c 2^-N, (1/2)(1 - c)} = min{1/8, 1/4} = 1/8. Take t = 1/8.
  D  := D_(t, 1 - t - c) = D_(1/8, 3/8)
  {F^(1)} := (t + c, 1 - t - c) = (5/8, 3/8)
  {F^(2)} := (t, 1 - t)         = (1/8, 7/8)
ADMISSION OF D. t = 1/8 > 0 and 1 - t - c = 3/8 > 0, so by the instance's
display Delta_herm = Delta_pos = 0 and
  Delta_cpl = |t + (1 - t - c) - 1| = |1/2 - 1| = 1/2 = c.
Condition (T) is trivial (one sector), so D is eps_dec-ADMISSIBLE at the
declared eps_dec = c = 1/2, AND IT FALLS IN BRANCH (iii) of Theorem thm:optol:
a run on it proceeds, evaluates h_low, and emits no key length.
  theta = Delta_cpl + |V| Delta_pos = 1/2 < 1, so Lemma lem:nearpovm applies
  and eps_dec_star = 0 + 0 + c(1 + c)/(1 - c) = (1/2)(3/2)/(1/2) = 3/2.
NOTE THE PARENTHETICAL THE CONTRACT ADDS HERE: theta < 1 holds "although
admission alone guarantees it only for eps_dec < (|V| + 1)^{-1}" = 1/3, and
eps_dec = 1/2 exceeds that. The sufficient condition is not necessary, and
this is the frozen case in which it is not.
BOTH NEIGHBOURS ARE EXACTLY ADMISSIBLE AND INSIDE eps_dec_star:
  5/8 + 3/8 = 1 and 1/8 + 7/8 = 1, both with non-negative entries, so both are
  POVMs on the one-dimensional Q (Lemma lem:optol-zero); and
  ||F^(1) - F|| = max{|5/8 - 1/8|, 0}   = 1/2,
  ||F^(2) - F|| = max{0, |7/8 - 3/8|}   = 1/2,
  both <= 3/2 = eps_dec_star.
THE VALUES, by Eq. eq:optol-instance:
  h_low[D]      = (alpha/(alpha-1)) log2(1/t)       = (alpha/(alpha-1)) . 3
  h_low[D^(2)]  = (alpha/(alpha-1)) log2(1/t)       = (alpha/(alpha-1)) . 3
  h_low[D^(1)]  = (alpha/(alpha-1)) log2(1/(t + c)) = (alpha/(alpha-1)) log2(8/5)
so the first relation of Eq. eq:optol-gap2 holds with EQUALITY,
h_low[D] = h_low[D^(2)], and
  h_low[D] - h_low[D^(1)] = (alpha/(alpha-1)) log2((t + c)/t)
                          = (alpha/(alpha-1)) log2(1 + c/t)
                          = (alpha/(alpha-1)) log2(5)
                          >= log2(1 + 2^N) = log2(5) = 2.321928094887362
                          > 2 = N >= B,
using c/t = (1/2)/(1/8) = 4 = 2^N exactly.
THE DIRECTION IS THE UNSAFE ONE. The ADMITTED, DEFECTIVE declaration's h_low
lies ABOVE that of an exactly admissible family inside its own eps_dec_star,
by more than any prescribed B -- and for a key-length claim that is the
direction that overstates the key. THIS IS WHY key_length IS WITHHELD ON
BRANCH (iii), and it is why the withholding is not conservatism but the
absence of any statement to be conservative about.
KEY LENGTH. For alpha in (1, 2), inserting the gap into
l_max = max{0, floor(n h_low - lambda)} of Remark rem:plus2, whose subtrahend
does not depend on h_low: if the smaller of the two values is positive, the
two lengths differ by at least n B - 1 bits.""",
    ),
    NoBoundCase(
        case_id="NB-ii-reversed",
        part="ii",
        declared=(0.625, 0.875),
        declared_defects=(0.0, 0.0, 0.5),
        family_one=(0.625, 0.375),
        family_two=(0.125, 0.875),
        distance_one=0.5,
        distance_two=0.5,
        distance_bound=1.5,
        bound_b=2.0,
        gap_between=("family_two", "declared"),
        gap_form=lambda alpha: (alpha / (alpha - 1.0)) * math.log2(5.0),
        frozen_gap=_freeze(lambda alpha: (alpha / (alpha - 1.0)) * math.log2(5.0)),
        derivation="""\
THE SIGN REVERSED, at the same tolerance and with the same two neighbours --
the clause the Round-11 revision added as part (ii)'s second sentence, and
the reason the non-existence holds "in either direction".
  D' := D_(t + c, 1 - t) = D_(5/8, 7/8), the SECOND declared family.
  Delta_herm = Delta_pos = 0 (both entries positive) and
  Delta_cpl = |(t + c) + (1 - t) - 1| = |3/2 - 1| = 1/2 = c,
  THE SAME DEFECTS, hence the same eps_dec = 1/2, the same theta = 1/2 and the
  same eps_dec_star = 3/2 as NB-ii-c-half-B2.
  THE SAME TWO EXACTLY ADMISSIBLE NEIGHBOURS, at the same distance:
    ||F^(1) - F'|| = max{|5/8 - 5/8|, |3/8 - 7/8|} = 1/2
    ||F^(2) - F'|| = max{|1/8 - 5/8|, |7/8 - 7/8|} = 1/2
  both <= 3/2.
THE VALUE:
  h_low[D'] = (alpha/(alpha-1)) log2(1/(t + c)) = (alpha/(alpha-1)) log2(8/5)
            = h_low[D^(1)],
  which lies BELOW h_low[D^(2)] = (alpha/(alpha-1)) . 3 by exactly the same
  (alpha/(alpha-1)) log2(5).
SO NEITHER DIRECTION IS CONTROLLED. Two declared families, indistinguishable
in every datum the interface reports -- same dimensions, same alphabet, same
three defects, same declared tolerance, same eps_dec_star, same two exactly
admissible neighbours at the same distance -- and their h_low values straddle
those neighbours' in OPPOSITE directions, each by more than any prescribed B.
No function of the declared metadata can be both.""",
    ),
)


# ---------------------------------------------------------------------------
#  What the tolerance does NOT reach -- Remark rem:optol-reach (a)-(d)
# ---------------------------------------------------------------------------

#: Each entry is (what is decided, the contract's verdict at every declared
#: eps_dec, the site). "Exact" here is the contract's own word: "Every other
#: validity condition of Section 2.1 is DECIDED EXACTLY, AT EVERY DECLARED
#: VALUE OF eps_dec."
#:
#: THIS TABLE IS THE FREEZE'S ANSWER TO THE QUESTION "which declared identity
#: does eps_dec govern?", and the answer is: exactly three, all of them on
#: bob_povm. Every other identity a validation path decides -- the
#: normalization of tau_A, the completeness of alice_povm, the sum of a
#: declared frequency vector -- is decided EXACTLY at 0.5.0, so an undeclared
#: window around any of them is a divergence from the contract that the
#: declared tolerance does not license and never did.
OPTOL_REACH_STATEMENTS: tuple[tuple[str, str, str], ...] = (
    (
        "bob_povm Hermiticity defect Delta_herm",
        "governed by eps_dec, condition (H)",
        "Definition def:optol; Section 2.1 (bob_povm row)",
    ),
    (
        "bob_povm negative part Delta_pos",
        "governed by eps_dec, condition (P)",
        "Definition def:optol; Section 2.1 (bob_povm row)",
    ),
    (
        "bob_povm completeness defect Delta_cpl",
        "governed by eps_dec, condition (C)",
        "Definition def:optol; Section 2.1 (bob_povm row)",
    ),
    (
        "bob_povm block-diagonality F_v = Pin_S(F_v)",
        "EXACT at every eps_dec; a type condition, decided and not measured",
        "Definition def:optol (T); Remark rem:optol-reach (a)",
    ),
    (
        "constraint O_k Hermitian and sector-block-diagonal",
        "EXACT at every eps_dec",
        "Remark rem:optol-reach (a); Assumption A-DECL (iii)",
    ),
    (
        "constraint Theta_k typing (Hermitian on A / real scalar) and bowtie_k",
        "EXACT at every eps_dec",
        "Remark rem:optol-reach (a); Assumption A-DECL (vi)",
    ),
    (
        "constraint data O_k, Theta_k, c_k as numbers",
        "EXACT at every eps_dec; their soundness is A-SOUND / A-ATK, a "
        "supplier obligation this module never verifies",
        "Remark rem:optol-reach (b); Section 2.5 certificate_arithmetic",
    ),
    (
        "alice_marginal tau_A >= 0 and tr tau_A = 1",
        "EXACT at every eps_dec",
        "Remark rem:optol-reach (c); Assumption A-DECL (ii)",
    ),
    (
        "acceptance_set: closed convex subset of the simplex",
        "EXACT at every eps_dec",
        "Remark rem:optol-reach (c); Assumption A-ACC",
    ),
    (
        "alice_povm M_x >= 0 and sum_x M_x = 1_A",
        "EXACT at every eps_dec; a declared {M_x} that is not a POVM is "
        "refused as in version 0.4.0",
        "Remark rem:optol-reach (d); Section 2.1 (alice_povm row)",
    ),
    (
        "certificate arithmetic: certificate point, surrogate gradient, dual "
        "witness, declared constraint data",
        "EXACT machine numbers at every eps_dec; the tolerance reaches the "
        "declared bob_povm ALONE",
        "Section 2.5 certificate_arithmetic, closing sentence",
    ),
)


# ---------------------------------------------------------------------------
#  Group 9 oracle entries
# ---------------------------------------------------------------------------

O_OPTOL_DEFECTS = OracleEntry(
    oracle_id="O-OPTOL-DEFECTS",
    claims=("C21",),
    kind="structural-identity",
    subject=(
        "The three defects of Eq. eq:defects and the two per-outcome vectors "
        "that attain the first two, on eleven hand-authored families with "
        "rational spectra."
    ),
    derivation="""\
contract.tex Definition def:optol, Eq. eq:defects:
  Delta_herm := max_v ||F_v - F_v^dagger||
  Delta_pos  := max_v max{0, -lambda_min((F_v + F_v^dagger)/2)}
  Delta_cpl  := ||sum_v F_v - 1_Q||
with ||.|| the OPERATOR NORM (largest singular value, Section 3), and all
three non-negative by construction.

The families are OPTOL_FAMILIES, each with its own derivation. The three
one-defect families isolate the three conditions -- OPTOL-HERM has
(1/4, 0, 0), OPTOL-NEG has (0, 1/8, 0), OPTOL-COMP has (0, 0, 1/8) -- so no
frozen verdict can be reached by the wrong test; OPTOL-EXACT has (0, 0, 0) and
is exactly admissible; OPTOL-BLOCK has (0, 0, 0) and is refused, because
condition (T) fails and is decided EXACTLY.

WHY THE PER-OUTCOME VECTORS ARE FROZEN SEPARATELY. Section 2.2 requires the
report to carry "the per-outcome quantities ||F_v - F_v^dagger|| and
max{0, -lambda_min((F_v + F_v^dagger)/2)} THAT ATTAIN THE FIRST TWO", and the
maximum does not determine them: OPTOL-HERM's Hermiticity vector is
(1/4, 1/4) -- both entries attain -- while OPTOL-NEG's negative vector is
(1/8, 0), attained by one outcome only. An implementation reporting a single
attaining index instead of a vector fails one of the two.

EVERY VALUE IS EXACT. Each family is two-dimensional with rational spectrum:
diagonal, or of the form [[a, b], [b, a]] with eigenvalues a +/- b, or real
with antisymmetric part of norm |b - c|. No number here came from a solver;
reference.defects reproduces them and is a witness to the derivation.
""",
)

O_OPTOL_ADMISSION = OracleEntry(
    oracle_id="O-OPTOL-ADMISSION",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "Definition def:optol's rule (T)/(H)/(P)/(C) case by case: each of "
        "(H), (P), (C) admitted at the boundary Delta = eps_dec and refused "
        "above it with the reason naming the failed part; (T) refused at "
        "every eps_dec, exactly."
    ),
    derivation="""\
contract.tex Definition def:optol and Remark rem:optol-interface (2), (3),
frozen as OPTOL_ADMISSION_CASES. The rule, in the order the contract applies
it:
  (0) the DATUM: eps_dec outside [0, 1) -> operator_tolerance_out_of_domain,
      before any operator is read (OPTOL_DOMAIN_CASES);
  (1) (T): F_v = Pin_S(F_v) for every v, DECIDED EXACTLY -- a failure is
      "refused as a malformed declaration, AT EVERY eps_dec", and the
      amendment spells NO reason string for it;
  (2) (H)/(P)/(C): Delta <= eps_dec each; a defect ABOVE the tolerance is
      refused with the reason naming the failed check, "carrying the measured
      defect and the declared eps_dec";
  (3) admitted, but Delta_herm > 0 or Delta_pos > 0 -> bob_povm_not_evaluable.

THE BOUNDARY PAIRS ARE THE CONTENT. For each of (H), (P), (C) the registry
freezes two cases on the SAME family differing in EXACTLY ONE DATUM, the
declared tolerance:
  (H): AD-HERM-boundary (eps = 1/4 = Delta_herm)  admitted
       AD-HERM-below    (eps = 1/8 < Delta_herm)  bob_povm_hermiticity_defect
  (P): AD-NEG-boundary  (eps = 1/8 = Delta_pos)   admitted
       AD-NEG-below     (eps = 1/16 < Delta_pos)  bob_povm_negative_part
  (C): AD-COMP-boundary (eps = 1/8 = Delta_cpl)   admitted
       AD-COMP-below    (eps = 1/16 < Delta_cpl)  bob_povm_completeness_defect
and the same three on the two-dimensional families (AD-2DH-*, AD-2DN-*,
AD-2DC-*). The inequality is NOT STRICT: equality admits. An implementation
writing `Delta < eps_dec` passes every "below" case and fails every boundary
case.

AND ADMISSION IS NOT EVALUATION. Of the three boundary cases only (C)'s run
PROCEEDS. AD-HERM-boundary and AD-NEG-boundary are admitted by the rule and
then refused with bob_povm_not_evaluable, because Delta_herm > 0 respectively
Delta_pos > 0 (Theorem thm:optol (ii)). Two different refusal reasons on the
same family at two different tolerances, and neither is the other.

(T) IS REFUSED AT EVERY TOLERANCE. AD-BLOCK-absent, AD-BLOCK-half and
AD-BLOCK-near-one span the whole declared domain on a family whose three
defects are ALL ZERO and which is a perfect POVM -- refused three times, and
never with a defect reason, because it has no defect.

WHEN MORE THAN ONE DEFECT EXCEEDS THE TOLERANCE the contract fixes no
precedence, so no case in this group has two: every family here has at most
one nonzero defect, and interface.yaml records the ordering as open choice
OC-5 rather than settling it.
""",
)

O_OPTOL_DOMAIN = OracleEntry(
    oracle_id="O-OPTOL-DOMAIN",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "eps_dec has domain [0, 1): closed at 0, open at 1; outside it the "
        "request is refused with operator_tolerance_out_of_domain, and an "
        "absent tolerance decides identically to a declared zero."
    ),
    derivation="""\
contract.tex Section 2.1 (the operator_tolerance row) and Remark
rem:optol-interface (1), frozen as OPTOL_DOMAIN_CASES.

THE UPPER ENDPOINT IS DERIVED, NOT CHOSEN, and the derivation is frozen as
data: "at eps_dec >= 1 condition (C) is satisfied by F_v = 0 for every v (then
Delta_cpl = ||-1_Q|| = 1), so the rule would no longer constrain the family at
all". OPTOL-ZERO is that family, with defects (0, 0, 1), and AD-ZERO-NEAR-ONE
freezes that it is still refused at eps_dec = 0.999 -- inadmissible everywhere
in [0, 1), which is exactly why the domain stops below 1.

A SECOND THRESHOLD, DELIBERATELY NOT THE SAME ONE. Lemma lem:nearpovm's
hypothesis theta < 1 ceases to be GUARANTEED by the admission rule at
eps_dec >= (|V| + 1)^{-1} = 1/3 for a two-outcome family, "above which the
witness is exhibited only for the declarations whose measured defects still
satisfy it". NB-ii-c-half-B2 is admitted at eps_dec = 1/2 > 1/3 and has
theta = 1/2 < 1 anyway -- the contract's own parenthetical that "the
sufficient condition of Remark rem:optol-interface (1) is not necessary".
The two thresholds bound different things and only the first bounds the datum.

ABSENT AND DECLARED-ZERO DECIDE IDENTICALLY, on every family: DOM-absent and
DOM-zero, AD-EXACT-absent and AD-EXACT-zero, AD-SUBC-absent and AD-SUBC-zero.
Lemma lem:optol-zero is why: at eps_dec = 0 the admission rule "is the
bob_povm validity condition of versions 0.1.x-0.4.0 CHARACTER FOR CHARACTER".
What may differ is how the report PRESENTS the absence (interface.yaml open
choice OC-3); no admission, branch or number turns on it.

THE DOMAIN OF A DECLARED DATUM IS DECIDED EXACTLY. There is no tolerance on
the tolerance: DOM-negative-subconstant, at -2^-37, is refused as surely as
DOM-negative-eighth at -1/8, and an implementation testing the lower endpoint
inside a window of its own passes the second and fails the first.
""",
)

O_OPTOL_EXACT_UNCHANGED = OracleEntry(
    oracle_id="O-OPTOL-EXACT-UNCHANGED",
    claims=("C21",),
    kind="structural-identity",
    subject=(
        "Theorem thm:optol (i): on an exactly admissible declaration every "
        "claim C1-C20 applies exactly as at version 0.4.0, and the declared "
        "eps_dec changes no statement, no bound and no number."
    ),
    derivation="""\
contract.tex Theorem thm:optol (i): "If Delta_herm = Delta_pos = Delta_cpl = 0
then D satisfies Assumption A-DECL in full and EVERY CLAIM C1-C20 OF THIS
CONTRACT APPLIES TO THE DECLARED NUMBERS EXACTLY AS AT VERSION 0.4.0. The
declared eps_dec changes no statement, no bound and no number. In particular
DECLARING A TOLERANCE NEVER WEAKENS A RUN WHOSE DATA DOES NOT USE IT, and an
absent operator_tolerance is this case."

THIS ENTRY IS THE REASON GROUPS 1-8 ARE NOT TOUCHED BY THE AMENDMENT, and it
is made falsifiable rather than asserted: OPTOL-EXACT IS THE POVM OF TOY-1,
element for element (F^(s0)_v0 = F^(s0)_v1 = 1/2, F^(s1)_v0 = 1,
F^(s1)_v1 = 0), and TOY-1 carries frozen 0.2.4-era values -- O-HLOW-RETENTION,
O-K-IDENTITY, O-K-RANGE, O-DEFICIT-SIGN, O-SECTOR-DECOMPOSITION,
O-BRANCH-ENTROPY at w0 = 1. If the amendment had moved any of them, the two
descriptions of the same operators would disagree.

EVERY TOY DECLARATION IN THIS REGISTRY IS EXACTLY ADMISSIBLE, so every frozen
value in Groups 1-8 is a branch-(i) value and stands unchanged at 0.5.0. That
is a statement about the toys and not an assumption: each declares its POVM
blockwise as non-negative reals summing to one per sector.

THE THREE ADMISSION CASES. AD-EXACT-absent (eps_dec = 0 by absence),
AD-EXACT-zero (declared zero) and AD-EXACT-quarter (a NONZERO tolerance
declared on data that does not need it) all reach branch (i) with identical
numbers. The third is the one that matters: an implementation that lets a
declared tolerance influence exactly_admissible, key_length_claim or the
assurance on data with no defect WITHHOLDS A KEY THE CONTRACT AWARDS -- see
REPORT-EXACT-quarter, whose report is (1/4, 0, 0, 0, true, true).

AT eps_dec = 0 ONLY CASE (i) CAN OCCUR AND THE THEOREM IS VACUOUS. Every run
of this platform before 0.5.0 was such a run.
""",
    toy_id="TOY-1",
)

O_OPTOL_NOT_EVALUABLE = OracleEntry(
    oracle_id="O-OPTOL-NOT-EVALUABLE",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "Theorem thm:optol (ii): at Delta_herm > 0 or Delta_pos > 0 the "
        "quantities of Sections 4.6-4.18 are NOT DEFINED, the request is "
        "refused with bob_povm_not_evaluable, and every way of proceeding is "
        "a repair the contract forbids."
    ),
    derivation="""\
contract.tex Theorem thm:optol (ii), Lemma lem:optol-defined (i), Remark
rem:optol-interface (3).

WHAT FAILS AND WHY. Every object of Definitions def:maps and def:branch that
reads {F_v} otherwise than linearly -- V_msm, W_prot, M_prot, K_kappa,
G_chat, Theta_chat, and hence T_chat, K_chat, f_{chat,s} and every quantity of
Sections 4.11-4.18 built from them -- contains the operator square root
sqrt(F_v) of Eqs. eq:Vmsm and eq:kraus, "which this contract means as the
UNIQUE POSITIVE SEMIDEFINITE square root. That exists exactly on Pos(Q), i.e.
exactly when F_v = F_v^dagger and lambda_min(F_v) >= 0, which is
Delta_herm = Delta_pos = 0." So at either defect none of them is defined, and
with them neither is O_alpha nor h_low for any declaration that generates key
at all.
EVEN THE AFFINE QUANTITIES LEAVE THEIR CODOMAIN. Phi and each P_chat read
{F_v} LINEARLY, so the expression evaluates for any numbers whatever, but
"where it lands depends on Delta_herm": at Delta_herm > 0 the values are in
general COMPLEX and Phi leaves the codomain R^Chat that eq:Phimap declares.

THE REFUSAL IS NOT A POLICY CHOICE. "There is no computation for an
implementation to perform, and every way of proceeding -- HERMITIZING,
FLOORING THE NEGATIVE PART, RENORMALIZING BY S^{-1/2}, SUBSTITUTING THE
WITNESS eq:starfam or any other nearby exact family -- is a repair of declared
data, which this contract forbids." All four are named, and WIT-HERM and
WIT-NEG freeze what the third and fourth would produce: for OPTOL-HERM the
witness is OPTOL-EXACT itself, one eighth away, and it is still forbidden.

CONTRAST rem:cert-interface, where repairing the CERTIFICATE POINT is
legitimate: "there the point is an object the implementation is free to
choose, every point of D certifies, and the conclusion h_cert <= h_low is the
same whichever is chosen. Here the object is DECLARED INPUT, and by
Proposition prop:optol-nobound THE CHOICE DECIDES THE ANSWER."

FROZEN CASES: AD-HERM-boundary, AD-2DH-boundary, AD-NEG-boundary,
AD-2DN-boundary and AD-SUBP-above -- each ADMITTED by Definition def:optol and
then refused. AD-SUBP-above is the sharpest: no declared tolerance in [0, 1)
makes OPTOL-SUBCONST-P computable, at a negative eigenvalue of 2^-37.

THE DEGENERATE CASE IS REFUSED ON THE SECOND GROUND ALONE. A declaration with
Chat_key empty has no K-term, so the argument above does not reach its
objective -- and that objective is not defined either, "at Delta_pos > 0 some
P_chat(omega) can be negative and at Delta_herm > 0 non-real, while the kernel
d(u, v) of Lemma foundations/lem:kernel is defined only for v >= 0 -- and such a
declaration produces no key at all, so refusing it costs nothing and this rule
stays one rule rather than two".
""",
)

O_OPTOL_EXPLORATION = OracleEntry(
    oracle_id="O-OPTOL-EXPLORATION",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "Theorem thm:optol (iii): on the completeness-only branch the program "
        "may be evaluated and reported as EXPLORATION output, key_length is "
        "not emitted, and h_low is a lower bound on nothing."
    ),
    derivation="""\
contract.tex Theorem thm:optol (iii) and Remark rem:optol-interface (4),
frozen as the branch="iii" row of OPTOL_BRANCH_OUTPUTS.

THE HYPOTHESIS: Delta_herm = Delta_pos = 0 < Delta_cpl <= eps_dec. Then "the
statements of Lemma lem:optol-defined (iv) hold VERBATIM for the declared
numbers and the program of Eq. eq:hlow-def MAY BE EVALUATED on them; BUT
h_qkd is not defined for the declared numbers, no claim of this contract
bounds it, h_low is A LOWER BOUND ON NOTHING, and no key length is asserted."

PRESENT: h_low, h_cert, sector_report, optimizer_certificate,
operator_tolerance_report -- "as exploration output, AND AS THAT ALONE".
ABSENT: key_length, and absent rather than zero or clamped.
FORCED: optimizer_certificate.assurance = estimate with the machine-readable
reason declared_operator_tolerance_open, "REGARDLESS OF THE REQUESTED
ASSURANCE -- a certified label is a statement about a key rate, and Theorem
thm:optol (iii) asserts none".
OMITTED FROM sector_report: the state-blindness consequence sum_v c_{v,s} = 1,
which a completeness defect costs Definition def:classes (c) and which
"sector_report must not report" (Lemma lem:optol-defined (iii)). The DEFINING
clause F^{(s)}_v = c_{v,s} 1_{Q_s} survives, and with it Theorem thm:removal
and the `removable` flag.

THE ARITHMETIC DISPLACEMENT IS SMALL AND EXACTLY IDENTIFIED, and the contract
says in the same breath why that is not reassurance. By Eq. eq:penaltyshift,
writing varsigma = sum_chat P_chat(omega) - 1 with |varsigma| <= Delta_cpl,
  sum_chat q(chat) log2(q(chat)/P_chat(omega))
      = D(q || Pbar) - log2(1 + varsigma),
so the full-alphabet penalty sum differs from a genuine divergence by at most
log2(1/(1 - Delta_cpl)), of either sign: 0.19264507794239583 bits on
OPTOL-COMP (Delta_cpl = 1/8) and 0.4150374992788438 bits on OPTOL-2D-COMP
(Delta_cpl = 1/4). "IT IS NEVERTHELESS NO LONGER A DIVERGENCE", the bound
h_low >= 0 of Remark rem:hlow-range is unavailable -- it rests on both
arguments being probability vectors -- and "the smallness is not a security
statement IN ANY CASE: Theorems thm:protocol-channel, thm:branch-formula and thm:reduction have no
conclusion for these numbers, so there is nothing for a small displacement to
be small RELATIVE TO."

THIS IS THE CList DISCIPLINE OF SECTION 4.22 APPLIED TO A SECOND INPUT: valid
arithmetic, no security output. O-CONSTRAINT-GATE is its first instance and
this is its second, and the two hard-fail the same way for the same reason.

FROZEN CASES: AD-COMP-boundary, AD-2DC-boundary, AD-SUBC-boundary and
AD-SUBC-above all reach this branch; the last two at defects of order 1e-11.
""",
)

O_OPTOL_ASSURANCE_FORCED_ESTIMATE = OracleEntry(
    oracle_id="O-OPTOL-ASSURANCE-FORCED-ESTIMATE",
    claims=("C13", "C21"),
    kind="fail-closed",
    subject=(
        "A FIFTH route to assurance = estimate, prior to and independent of "
        "the four check groups of Section 4.18: the tolerance branch forces "
        "the label off with reason declared_operator_tolerance_open, whatever "
        "the checks would say and whatever was requested."
    ),
    derivation="""\
contract.tex Section 2.2 (the optimizer_certificate row) and Remark
rem:optol-interface (4). THIS ENTRY REPLACES the biconditional of
O-ASSURANCE-CERTIFIED-GATE, which contract.tex 0.5.0 falsifies and which is
marked in SUPERSEDED_BY_0_5_0.

WHAT 0.4.0 SAID, and it was complete then: `certified` EXACTLY WHEN the
requested assurance was `certified` AND all four check groups of Section 4.18
passed -- (1) x in D on the rounded exact point, (2) (H1)-(H4) with their
certified floors, (3) the slack PSD verifications, (4) the enclosure assembly.
WHAT 0.5.0 ADDS: "FORCED TO estimate, with the reason
declared_operator_tolerance_open and WHATEVER THE REQUESTED ASSURANCE WAS,
whenever the declared bob_povm is admitted with a nonzero defect: `certified`
is a statement about a key rate and Theorem thm:optol (iii) asserts none."

IT IS NOT A FAILED CHECK, and that is why it cannot be written as a fifth
entry in the check list. On branch (iii) the arithmetic of Section 4.18 MAY
RUN AND PASS -- nothing in it is undefined, Delta_herm = Delta_pos = 0 -- and
the label is withheld anyway, because what the label would ASSERT is
unestablished for the declared numbers rather than unverified. Theorem
thm:cert is not established there: "its support reaches, through the spectral
window of Lemma lem:window (i) whose upper endpoint is tr omega <= 1, the
trace-non-increasing clause that Lemma lem:optol-defined (iii) names as
failing".

THE ORDER MATTERS AND IS FROZEN: the forced downgrade fires BEFORE the four
groups and independently of them, so a run reaching branch (iii) with
requested_assurance = certified emits assurance = estimate with
declared_operator_tolerance_open -- not with a reason naming a check, and not
with `certified`.

THE FROZEN VALUE OF THIS ENTRY IS THE REASON STRING, not a tier: naming
`certified` is not claiming it, and this entry does not name it as a value at
all. Its own assurance is `estimate` like every other entry's
(O-ASSURANCE-ESTIMATE).

FAIL-CLOSED DIRECTION: the condition can only WITHHOLD a label, never grant
one, so it cannot make an unsound result certified. What it costs is a
certified label on a run whose declared POVM is not exactly admissible, which
is a run that carries no key-length claim in any case
(operator_tolerance_report.key_length_claim = false).
""",
    value=OPTOL_ASSURANCE_REASON,
)

O_OPTOL_HCERT_NO_CLAIM = OracleEntry(
    oracle_id="O-OPTOL-HCERT-NO-CLAIM",
    claims=("C13", "C21"),
    kind="fail-closed",
    subject=(
        "h_cert <= h_low is claimed UNCONDITIONALLY only on an exactly "
        "admissible declaration; on the tolerance branch h_cert is "
        "exploration output carrying no such claim, and h_low bounds nothing "
        "for it to be compared against."
    ),
    derivation="""\
contract.tex Section 2.2 (the h_cert row, as qualified at 0.5.0) and Remark
rem:optol-interface (4).

WHAT IS REPORTED ON BRANCH (iii): h_cert MAY be reported, and
optimizer_certificate with it, as exploration output.
WHAT IS NOT CARRIED: any claim that h_cert <= h_low. "There Theorem thm:cert
is NOT ESTABLISHED for the declared numbers -- its support reaches, through
the spectral window of Lemma lem:window (i) whose upper endpoint is
tr omega <= 1, the trace-non-increasing clause that Lemma
lem:optol-defined (iii) names as failing -- so h_cert and
optimizer_certificate are reported as exploration output carrying NO claim of
h_cert <= h_low, EXACTLY AS h_low IS THERE A LOWER BOUND ON NOTHING."

THE SYMMETRY IS THE POINT. Both numbers are computable, both are reported, and
neither bounds anything: h_low does not bound h_qkd because M_prot is not a
channel (Lemma lem:optol-defined (iii)), and h_cert does not bound h_low
because Theorem thm:cert's hypothesis chain is broken at the same clause.
Comparing them therefore proves nothing either way, and the implementation's
own conservative refusal `certified-bound-above-h-low` -- which compares
h_cert against h_low and withholds the label when h_cert > h_low -- IS NOT
AVAILABLE AS A SOUNDNESS TEST HERE. It is also not needed: the branch's own
forced downgrade fires first and unconditionally
(O-OPTOL-ASSURANCE-FORCED-ESTIMATE).

WHAT IS UNCHANGED ON BRANCH (i). On an exactly admissible declaration the
0.4.0 statement stands in full: h_cert <= h_low UNCONDITIONALLY (Theorem
thm:cert, Eq. eq:hcert), h_cert present only on a run whose requested
assurance is `certified` and whose checks all passed, possibly negative or
-inf-useless without being unsound, and a poor h_cert a TIGHTNESS failure
reported as the gap diagnostic and never repaired (Remark
rem:cert-tightness). Every Group 7 certificate value is a branch-(i) value.

LEMMA lem:optol-defined (iv) IS EXPLICIT THAT THE CERTIFICATE CHAIN IS THE ONE
UNCLASSIFIED CASE THE INTERFACE DEPENDS ON, and that it is "settled where it
is used rather than here". This entry is where the freeze records that
settlement: the survivor list does not contain the certificate chain, and its
absence from the list is not silence -- (iv) says "a statement absent from
both (iii) and (iv) is one this subsection HAS NOT CLASSIFIED, not one it has
silently placed on either side".

WHETHER THE POST-PROCESSING RUNS AT ALL on this branch is interface.yaml open
choice OC-7: "may be reported" is a permission, and reporting h_cert absent
satisfies it equally. Neither reading can produce a certified label.
""",
)

O_OPTOL_REPORT = OracleEntry(
    oracle_id="O-OPTOL-REPORT",
    claims=("C21",),
    kind="structural-identity",
    subject=(
        "operator_tolerance_report, field for field on each branch: the "
        "declared eps_dec verbatim, the three defects, the two per-outcome "
        "vectors, exactly_admissible, and key_length_claim which equals it."
    ),
    derivation="""\
contract.tex Section 2.2 (the operator_tolerance_report row) and Remark
rem:optol-interface (5), frozen as OPTOL_REPORT_CASES.

SIX FIELDS, in the contract's order:
  1. the DECLARED eps_dec, VERBATIM -- not the measured defect, not a clamp;
  2. Delta_herm;  3. Delta_pos;  4. Delta_cpl;
  5. exactly_admissible : bool, "(Delta_herm = Delta_pos = Delta_cpl = 0)";
  6. key_length_claim : bool, "WHICH EQUALS exactly_admissible".
plus the two PER-OUTCOME vectors "that attain the first two".

EMITTED ON EVERY RUN. "At eps_dec = 0 the report is (0, 0, 0, 0, TRUE, TRUE)
and it ADDS NOTHING TO THE VERSION-0.4.0 ARTIFACT" -- REPORT-EXACT-absent, and
the report every existing golden value carries.

THE TWO BOOLEANS ARE FUNCTIONS OF THE THREE MEASURED DEFECTS AND OF NOTHING
ELSE. REPORT-EXACT-quarter is the case that pins it: a tolerance of 1/4
declared on data with no defect gives (1/4, 0, 0, 0, true, true), so an
implementation deriving either boolean from the DECLARED tolerance withholds a
key the contract awards (Theorem thm:optol (i): "declaring a tolerance never
weakens a run whose data does not use it"). REPORT-SUBC-above is the converse
case: (2^-33, 0, 0, 2^-37, false, false), where the two small numbers are
different and sixteen-fold apart, and exactly_admissible is FALSE at a defect
of 7.3e-12 -- there is no threshold below which a defect stops counting.

THE COMPOSITION RULE, and it is the only clause of this contract addressed to
a CONSUMER of the artifact: "A composition that consumes this module's output
MUST READ key_length_claim: when it is FALSE the artifact carries no
key-length claim of this contract, AND NO DOWNSTREAM STEP MAY SUPPLY ONE."

THE TWO ABSENCE GROUNDS FOR key_length ARE INDEPENDENT, and this report
answers only one of them. A run on an exactly admissible declaration with
h_low = +infinity (TOY-4c, O-HLOW-INFINITE) emits no key_length while
key_length_claim is TRUE: the boolean says that this contract's key-length
claim attaches to the declared POVM, not that a length was emitted. The
converse case is branch (iii) with a finite h_low.

WHAT IS NOT FIXED HERE. The contract spells typewriter machine keys for the
two booleans only; the four numbers and the two vectors it spells
mathematically, and interface.yaml records the naming and the record's
serialization as open choices OC-1 and OC-2. Whether a REFUSED request
delivers these numbers as this record or as refusal metadata is OC-6 -- what
rule (2) requires either way is that the refusal carry "the measured defect
and the declared eps_dec", which is what REPORT-HERM-boundary and
REPORT-NEG-boundary freeze.
""",
)

O_OPTOL_WITNESS = OracleEntry(
    oracle_id="O-OPTOL-WITNESS",
    claims=("C21",),
    kind="toy-instance",
    subject=(
        "Lemma lem:nearpovm both ways: an exactly admissible {F*_v} within "
        "eps_dec_star of any (T)-satisfying family with theta < 1, and the "
        "converse bounds Delta_herm <= 2 eta, Delta_pos <= eta, "
        "Delta_cpl <= |V| eta -- with both halves ATTAINED on WIT-HERM."
    ),
    derivation="""\
contract.tex Lemma lem:nearpovm (Eqs. eq:nearpovm, eq:starfam,
eq:nearpovm-conv), Remark rem:optol-witness and Theorem thm:optol (iv),
frozen as OPTOL_WITNESS_CASES.

THE FORWARD CONSTRUCTION, in the proof's own steps: H_v the Hermitian part;
G_v = H_v + Delta_pos 1_Q, which is PSD because lambda_min(H_v) >= -Delta_pos;
S = sum_v G_v, with ||S - 1_Q|| <= theta = Delta_cpl + |V| Delta_pos < 1, so
(1 - theta) 1_Q <= S <= (1 + theta) 1_Q and S is invertible; and
F*_v = S^{-1/2} G_v S^{-1/2} (Eq. eq:starfam), a POVM inheriting (T) because
"the continuous functional calculus of a Pin_S-invariant operator is
Pin_S-invariant". The bound is
  eps_dec_star = Delta_herm/2 + Delta_pos + theta(1 + theta)/(1 - theta).

FOUR FROZEN EVALUATIONS, each exactly rational despite S^{-1/2} not being:
  WIT-HERM   theta = 0,   eps* = 1/8,   F* = OPTOL-EXACT,
             distances (1/8, 1/8) -- THE BOUND IS ATTAINED;
  WIT-NEG    theta = 1/4, eps* = 13/24, F* = (diag(0, 9/10), diag(1, 1/10)),
             distances (1/8, 1/8);
  WIT-COMP   theta = 1/8, eps* = 9/56,  F* = (diag(1/2, 8/9), diag(1/2, 1/9)),
             distances (1/9, 1/72);
  WIT-2DCOMP theta = 1/4, eps* = 5/12,
             F* = ([[13/20, 3/20], [3/20, 13/20]],
                   [[7/20, -3/20], [-3/20, 7/20]]),
             distances (1/5, 1/20).

WIT-HERM ATTAINS BOTH HALVES, which is what makes it worth freezing. Forward:
the distance 1/8 EQUALS eps_dec_star = Delta_herm/2. Converse: with eta = 1/8,
Eq. eq:nearpovm-conv gives Delta_herm <= 2 eta = 1/4 and Delta_herm IS 1/4, so
the factor 2 is not slack. WIT-NEG attains the second converse bound,
Delta_pos = eta = 1/8.

WHAT THE WITNESS IS FOR, AND WHAT IT IS NOT. It "brackets the admission rule
between two readings of 'the declared numbers are within O(eps_dec) of an
exactly admissible family', WHICH IS WHAT MAKES eps_dec AN OPERATOR TOLERANCE
RATHER THAN AN ARBITRARY THRESHOLD. IT LICENSES NOTHING FURTHER." The family
"is an existence witness inside that proof: NO RUN COMPUTES IT, NO OUTPUT
REPORTS IT, and substituting it -- or any other exactly admissible family
within eps_dec_star -- for the declared numbers is FORBIDDEN. It is one of
infinitely many such families, and by Proposition prop:optol-nobound TWO OF
THEM CAN CARRY VALUES OF h_low THAT DIFFER WITHOUT BOUND, so which one an
implementation picked would decide the answer it reported."
WIT-HERM makes that concrete: OPTOL-HERM's exactly admissible neighbour is
OPTOL-EXACT, whose h_low this registry has frozen since 0.2.4 -- and using it
is still forbidden, because the run was asked about OPTOL-HERM.

THE SUPPLIER CONSEQUENCE, from the closing paragraph of Remark
rem:optol-interface, is the converse read forwards: a supplier emitting {F_v}
as accurate to eta has Delta_herm <= 2 eta, Delta_pos <= eta and
Delta_cpl <= |V| eta, so declaring eps_dec >= max{2, |V|} eta SUFFICES FOR
ADMISSION -- and "IT DOES NOT MAKE THE RUN PRODUCE A KEY LENGTH: unless the
emitted numbers are exactly admissible, rule (3) or rule (4) applies, and the
way to a key-length output is FOR THE SUPPLIER TO EMIT THE EXACTLY ADMISSIBLE
FAMILY ITSELF." The `sufficient_tolerance` field of each case is that number.
""",
)

O_OPTOL_NO_ROBUSTNESS = OracleEntry(
    oracle_id="O-OPTOL-NO-ROBUSTNESS",
    claims=("C8", "C21"),
    kind="analytic-limit",
    subject=(
        "Proposition prop:optol-nobound: no function of the declared "
        "dimensions, alphabet sizes, alpha and tolerance bounds the h_low "
        "gap -- neither between two exactly admissible families at distance "
        "epsilon, nor between an admitted defective declaration and the "
        "exactly admissible families inside its own eps_dec_star, in either "
        "direction."
    ),
    derivation="""\
contract.tex Proposition prop:optol-nobound with Remark rem:optol-direction,
frozen as OPTOL_NOBOUND_CASES. The instance is the one Remark rem:hlow-range
already constructs, "evaluated at two parameter values" (the provenance block
of Section 4.23 says so).

THE INSTANCE: d_A = d_Q = 1 (both source modes coincide, Feas = {[1]}), one
sector, X = {x0} with M_x0 = [1], V = {v0, v1}, a_A constant, a_B = id,
phi(kappa) = c_B so Chat = V, ALL-FAIL SIFTING (r == perp, holder B with
r_B == perp, so Chat_key is empty), CList empty, default partition, and the
SINGLETON acceptance set AcceptSet = {(1, 0)}. Then Eq. eq:optol-instance:
    h_low[D_(g0, g1)] = (alpha/(alpha - 1)) log2(1/g0),   g0 > 0, g1 >= 0,
"a computation that uses NO PROPERTY of (g0, g1) beyond those two
inequalities -- IN PARTICULAR NOT g0 + g1 = 1", which is exactly why it
evaluates on a defective family too.
The dimensions and alphabets are FIXED INDEPENDENTLY of B, epsilon and c, so a
function of those data alone bounds neither quantity.

PART (i), TWO EXACTLY ADMISSIBLE FAMILIES AT DISTANCE epsilon.
  NB-i-eps-half-B3:    eps = 1/2, B = 3, N = 3, gap = (alpha/(alpha-1)) . 3
  NB-i-eps-quarter-B1: eps = 1/4, B = 1, N = 1, gap = (alpha/(alpha-1)) . 1
Both families in each case are EXACT POVMs, which is Remark
rem:optol-direction's second reading: "they do not locate the fragility in the
defects ... the phenomenon belongs to the map {F_v} -> h_low and would be
there for a supplier that emitted perfect numbers for a slightly different
device".

PART (ii), THE ONE THEOREM thm:optol (iv) CONSUMES.
  NB-ii-c-half-B2: c = 1/2, B = 2, N = 2, t = 1/8. The declared family
  (1/8, 3/8) has Delta_cpl = 1/2 = c, is admitted at eps_dec = c, FALLS IN
  BRANCH (iii), has theta = 1/2 and eps_dec_star = 3/2; the two exactly
  admissible neighbours (5/8, 3/8) and (1/8, 7/8) lie at distance 1/2 <= 3/2;
  h_low[D] = h_low[D^(2)] = (alpha/(alpha-1)) . 3 exactly, and
  h_low[D] - h_low[D^(1)] = (alpha/(alpha-1)) log2(5) >= log2(5) > 2 = N >= B.
  NB-ii-reversed: the second declared family (5/8, 7/8), with THE SAME three
  defects, THE SAME eps_dec, THE SAME eps_dec_star and THE SAME two
  neighbours at THE SAME distances -- and h_low BELOW h_low[D^(2)] by the same
  amount. Neither direction is controlled.

THE DIRECTION THAT MATTERS FOR SECURITY. In NB-ii-c-half-B2 the ADMITTED,
DEFECTIVE declaration's h_low lies ABOVE an exactly admissible neighbour's by
more than any prescribed B -- "for a key-length claim THE UNSAFE DIRECTION".
That is why key_length is withheld on branch (iii), and why the withholding is
not conservatism but the absence of any statement to be conservative about.

AND NO THRESHOLD ESCAPES BY BEING SMALL: "epsilon in part (i) and c in part
(ii) may be taken as small as any positive declared tolerance, THE GAP IN EACH
CASE BEING BOUGHT BY THE SECOND PARAMETER of the instance rather than by the
size of the perturbation". The two part-(i) cases exhibit that: they share
every dimension and alphabet and their gaps stand in the ratio 3 : 1.

BOTH GAPS LIVE ENTIRELY IN THE ACCEPTANCE-TEST PENALTY, Chat_key being empty,
"which every declaration carries" -- the same unboundedness Remark
rem:hlow-range records for h_low itself, there as a range statement and here
as a stability statement (O-HLOW-DIVERGENCE-ONLY and O-HLOW-INFINITE are the
range side of the same instance).

KEY LENGTH. For alpha in (1, 2), inserting the gap into
l_max = max{0, floor(n h_low - lambda)} of Remark rem:plus2, whose subtrahend
does not depend on h_low: the two maximal admissible key lengths differ by at
least n B - 1 bits whenever the smaller is positive. At alpha >= 2 the same
computation compares two values of the rem:plus2 EXPRESSION, "to which this
contract gives no key-length reading" (Assumption A-ALPHA).

THE CLOSED FORM BELOW is part (i)'s gap at epsilon = 1/2, B = 3:
(alpha/(alpha - 1)) . 3 bits per round, frozen on the standard alpha grid.
""",
    closed_form=lambda alpha: (alpha / (alpha - 1.0)) * 3.0,
    frozen_values=_freeze(lambda alpha: (alpha / (alpha - 1.0)) * 3.0),
)

O_OPTOL_UNDECLARED_CONSTANT = OracleEntry(
    oracle_id="O-OPTOL-UNDECLARED-CONSTANT",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "A defect of order 1e-11 with NO tolerance declared is a REFUSAL "
        "naming the failed part; the same family at a declared tolerance "
        "above the defect reaches the branch the contract assigns, and never "
        "a key length."
    ),
    derivation="""\
contract.tex Section 2.5 (the operator_tolerance convention), Lemma
lem:optol-zero, and Remark rem:optol-interface (2), (3), (4), frozen as the
two OPTOL-SUBCONST families and their five admission cases.

THE RULE THIS ENTRY DISCRIMINATES. "ABSENT MEANS eps_dec = 0, and eps_dec = 0
MEANS EXACT AT EVERY SITE OF THIS CONTRACT; NO DEFAULT IS FIXED HERE OR IN ANY
ARTIFACT DERIVED FROM HERE." A validation path that decides a declared
identity inside a constant absolute window has fixed a default -- an
UNDECLARED one -- and 0.5.0 forbids exactly that. Assumption A-DTOL exists so
that only a DECLARED tolerance is a datum at all.

THE COMPLETENESS SIDE, OPTOL-SUBCONST-C, Delta_cpl = 2^-37 =
7.275957614183426e-12:
  absent   -> REFUSED, bob_povm_completeness_defect   (AD-SUBC-absent)
  0.0      -> REFUSED, bob_povm_completeness_defect   (AD-SUBC-zero)
  2^-37    -> ADMITTED at the boundary, branch (iii)  (AD-SUBC-boundary)
  2^-33    -> ADMITTED, branch (iii)                  (AD-SUBC-above)
FOUR REQUESTS, THREE DISTINCT ANSWERS. An undeclared 1e-10 window returns one
answer -- "admitted, and compute" -- to all four, and in particular admits and
computes where the contract refuses.

THE POSITIVITY SIDE, OPTOL-SUBCONST-P, Delta_pos = 2^-37, Delta_cpl = 0 (the
two perturbations cancel in the sum):
  absent   -> REFUSED, bob_povm_negative_part         (AD-SUBP-absent)
  2^-33    -> ADMITTED, then REFUSED, bob_povm_not_evaluable  (AD-SUBP-above)
NO DECLARED TOLERANCE MAKES IT COMPUTABLE. At 2^-37 below zero, a
floating-point sqrt returns NaN or is silently clamped, and clamping is
"flooring the negative part" -- one of the four repairs Remark
rem:optol-interface (3) forbids by name.

BOTH PERTURBATIONS ARE EXACT POWERS OF TWO, so the declared numbers are exact
in binary floating point and the frozen defect is the perturbation itself
rather than a rounding of it. 2^-37 is an order of magnitude BELOW 1e-10 and
2^-33 = 1.1641532182693481e-10 is just above it, so the pair straddles the
constant.

AND THE SECOND HALF IS THE ONE MOST EASILY MISSED: declaring a tolerance large
enough to admit these numbers BUYS NO KEY LENGTH. AD-SUBC-boundary and
AD-SUBC-above are branch (iii) -- exploration, assurance forced to estimate
with declared_operator_tolerance_open, key_length absent,
key_length_claim = false (REPORT-SUBC-above). A run that emits a key length
there has read admission as a licence, which is the failure the A-DTOL ledger
row describes: "the emitted key length then rests on NO THEOREM of this
contract, and may exceed that of an exactly admissible family within the
declared tolerance BY ANY AMOUNT".

WHICH DECLARED IDENTITIES THE TOLERANCE REACHES AT ALL is
OPTOL_REACH_STATEMENTS, and the answer is three, all on bob_povm. Every other
identity -- the normalization of tau_A, the completeness of alice_povm, the
sum of a declared frequency vector -- is "DECIDED EXACTLY, AT EVERY DECLARED
VALUE OF eps_dec" (Remark rem:optol-reach (a)-(d)), so an undeclared window
around any of those is a divergence the declared tolerance does not license
and never did.
""",
)

O_OPTOL_REACH = OracleEntry(
    oracle_id="O-OPTOL-REACH",
    claims=("C21",),
    kind="structural-identity",
    subject=(
        "eps_dec governs (H), (P) and (C) on the declared bob_povm and "
        "NOTHING ELSE; every other validity condition of Section 2.1 is "
        "decided exactly, at every declared value."
    ),
    derivation="""\
contract.tex Remark rem:optol-reach, enumerated as OPTOL_REACH_STATEMENTS, and
the Section 2.5 conventions operator_tolerance and certificate_arithmetic.

"eps_dec governs (H), (P) and (C) on the declared {F_v} AND NOTHING ELSE.
EVERY OTHER VALIDITY CONDITION OF SECTION 2.1 IS DECIDED EXACTLY, AT EVERY
DECLARED VALUE OF eps_dec:"
  (a) BLOCK-DIAGONALITY (T) and the TYPING conditions of A-DECL (iii), (vi).
      "These are TYPE conditions: they say what shape a datum has, not how
      near one number is to another, and A TYPE IS DECIDED RATHER THAN
      MEASURED." The off-block defect "can of course be written down"; what
      cannot be written down without re-deriving them is what lem:branch-maps (iii),
      prop:exact-cancellation, thm:removal and thm:choi would say about an operator that is
      only nearly block-diagonal -- each uses the decomposition as an EXACT
      direct sum, and sqrt(F_v) = direct_sum_s sqrt(F_v^{(s)}) "is an identity
      of the functional calculus that holds for a block-diagonal operator AND
      FOR NO OTHER". OPTOL-BLOCK is the frozen instance.
  (b) THE DECLARED CONSTRAINT DATA. Their soundness at the declared numbers is
      A-SOUND (A-ATK inside the security chain), a supplier obligation this
      module never verifies. "A supplier that computes an entry inexactly
      discharges that obligation by declaring a constant that is SOUND AS
      DECLARED -- shifting the constant in the conservative direction is its
      own step, taken on its own side of the interface -- NOT BY ASKING THIS
      MODULE FOR SLACK ON THE RELATION."
  (c) THE MARGINAL tau_A (A-DECL (ii): tau_A >= 0, tr tau_A = 1) and THE
      ACCEPTANCE SET (A-ACC).
  (d) ALICE'S POVM {M_x}. It enters eq:Vmsm and eq:kraus through sqrt(M_x)
      "exactly as {F_v} does, so a tolerance on it would need this subsection
      RE-DERIVED for it; version 0.5.0 derives nothing of the kind and does
      not widen the amendment to it. A declared {M_x} that is not a POVM is
      refused as in version 0.4.0."
AND THE CERTIFICATE DATA, from Section 2.5: "the declared data named here stay
EXACT at every declared operator_tolerance: that tolerance reaches the
declared bob_povm ALONE".

THE ASYMMETRY IS DELIBERATE AND IS WHERE THE AMENDMENT STOPS: "{F_v} is the
one declared operator family that a supplier REDUCTION constructs and emits
with a stated accuracy, which is why it is the one the platform must be able
to talk about at a declared tolerance. EXTENDING THE TOLERANCE TO ANY OF
(a)-(d) IS A FURTHER AMENDMENT, NOT A READING OF THIS ONE."

WHY THIS ENTRY EXISTS AS A FROZEN OBJECT AND NOT AS A COMMENT. The amendment
makes ONE identity tolerable and, by saying so, makes every other identity's
exactness explicit. A reader who takes 0.5.0 as "the module now has a
tolerance" will apply the declared value in more places than three; a reader
who takes it as "one input gained an admission threshold" will not. This table
is the second reading, in eleven rows, and the three governed rows are the
first three.
""",
)


# ===========================================================================
#  Group 10 -- THE FIRST-ORDER RUNG (contract 1.0.0, C22)
# ===========================================================================
#
#  Authored in the implementation band the accepted MAJOR amendment 1.0.0
#  opens, by the run-A implementer instance under the two-instance freeze
#  rule: run A freezes the evidence before any code changes, and
#  run B -- a different instance -- changes the code against it and may read
#  but never modify what is frozen here. **Not one number in Group 10 was
#  produced by an implementation of the thing it pins**, because no
#  implementation of the first-order rung exists when it is written: the code
#  then implements 0.5.0, whose ladder has no such rung.
#
#  WHAT IT PINS is Theorem ``thm:firstorder`` as data: the bracket
#  Eq. ``eq:hlb`` on four declarations already in this registry, chosen so that
#  the linear minimization the bracket calls for is decidable BY HAND -- a
#  singleton feasible set, a gradient constant on the feasible set, a
#  one-parameter feasible interval with the vertex at each end -- together with
#  the key length Eq. ``eq:keylength-fo`` built from ``max{0, h_lb}``, the five
#  withdrawal reasons of Remark ``rem:fo-interface``, the typed
#  ``negative_objective`` refusal of Remark ``rem:fo-negative-values``, and the two-rung ladder itself.
#
#  NO ENTRY HERE COMPUTES A GRADIENT, and the exclusion
#  ``test_no_entry_is_a_choi_parametrization_or_a_gradient`` guards is
#  respected in the form that test states it: what is forbidden is "an oracle
#  that IS the implementation -- a Choi parametrization routine or a gradient
#  routine written in the test tree", and what is licensed is "a frozen scalar
#  witness that discriminates the contract's rule from a wrong one". The
#  closed forms below are functions of ``alpha`` alone (or of ``alpha`` and one
#  hand-named sector weight) for ONE named toy branch, derived on paper from
#  the displayed equations; none of them is a routine a solver could be checked
#  against by construction.
#
#  THE ONE-SECTOR REDUCTION, stated once because three entries use it.
#  TOY-1 and TOY-5 have ``d_A = 1`` and two one-dimensional sectors, a
#  singleton acceptance set ``{delta_chat0}`` with ``Chat = Chat_key =
#  {chat0}``, and ``P_chat0(omega) = w0 + w1``. Writing ``c := 1 - 2^{1-alpha}
#  in (0, 1)`` and ``K(w) = 1 - c w``, contract Eq. eq:objective reads
#
#      O(w0, w1) = -log2(w0 + w1) - (1/(alpha-1)) log2(w0 2^{1-alpha} + w1)
#
#  on the ambient cone, and ``= -(1/(alpha-1)) log2 K(w0)`` on the feasible
#  set, where ``w0 + w1 = 1``. Its gradient in the two block coordinates, AT A
#  FEASIBLE POINT, is
#
#      G_0 = -log2(e) (1 + 2^{1-alpha} / ((alpha-1) K)) ,
#      G_1 = -log2(e) (1 +        1     / ((alpha-1) K)) ,
#
#  so ``G_0 - G_1 = log2(e) c / ((alpha-1) K) > 0`` and the linear form
#  ``<G, J'> = G_0 w0' + G_1 w1'`` is minimized OVER THE FEASIBLE INTERVAL AT
#  ITS SMALLEST ADMISSIBLE ``w0'``. That is the whole of the linear
#  minimization on these two toys, and it is decided by a SIGN rather than by a
#  solver. The bracket at an iterate of weight ``w`` and an oracle vertex of
#  weight ``w*`` is therefore
#
#      B(w; w*) = O(w) + (G_0 - G_1)(w* - w)
#               = [ -log2 K(w) + log2(e) c (w* - w) / K(w) ] / (alpha - 1) ,
#
#  which is :func:`_fo_bracket_one_sector`. The acceptance term
#  ``<g_t, v_t - q_t>`` VANISHES on both: the acceptance set is a singleton, so
#  ``v_t = q_t = delta_chat0`` and the difference is the zero vector -- which is
#  also why conditions (alpha) and (beta) of Remark ``rem:acc-side`` are met
#  trivially there, every convex combination of one exact rational point being
#  that point.
#
#  CROSS-CHECK, SHARING NO STEP WITH THE DERIVATION and recorded as a
#  cross-check rather than as the derivation. Every bracket value below was
#  reproduced by evaluating the objective through ``reference.py`` -- branch
#  operators, eigendecompositions, the key pinching, T, K, P -- and taking the
#  directional derivative along the segment towards the oracle vertex by a
#  SECOND-ORDER ONE-SIDED FINITE DIFFERENCE at h = 1e-6. Nothing analytic
#  enters that route. It agrees with the analytic closed form to at worst
#  2.2e-8 on every (alpha, weight) pair frozen here, which is the accuracy that
#  difference has. The finite difference must be ONE-SIDED: at a vertex of the
#  feasible interval a central difference steps outside the cone, where the
#  objective is not defined -- the same fact Lemma ``lem:fo-face`` (b) is
#  about.

#: log2(e). Contract Section 2.5: "Natural logarithms appear only inside
#: derivative formulas and carry explicit conversion factors" -- this is that
#: factor, and it appears here for no other reason.
_LOG2E: float = 1.0 / math.log(2.0)

#: The two live rungs of ARCHITECTURE_SPEC.md Section 3.8, and the two values
#: contract.tex 1.0.0 Section 2.2 admits for ``optimizer_certificate.assurance``
#: and for ``reported_tier``. `certified` is a SHELVED NAME and is never
#: emitted; a request naming it is REFUSED with
#: ``assurance_tier_not_available`` and never silently demoted.
#: RE-DERIVED BY HAND from foundations/def:tiers as amended: "A tier of a reported
#: key-rate number is one of the following three labels" -- estimate,
#: first-order, certified -- "The tiers are ordered, estimate below
#: first-order below certified ... There is no other tier."
#: The third label is reported where req:certified-evaluation (vi) reports the
#: certified number (foundations/req:tiers); the order is the definition's.
ASSURANCE_VALUES_1_0_0: tuple[str, ...] = ("estimate", "first-order", "certified")

#: contract.tex 1.0.0 Section 2.5, artifact_bindings bullet.
MATHEMATICAL_SPEC_VERSION_1_0_0: str = "meat-core@1.0.0"

#: The shelved rung's name, kept so that a test can assert it is never emitted
#: and that a request naming it is refused. It is def:tiers
#: (iii)'s live label (see ASSURANCE_VALUES_1_0_0); the string is unchanged.
SHELVED_TIER_NAME: str = "certified"

#: The reason a request naming the shelved rung carries (Section 2.4).
SHELVED_TIER_REFUSAL: str = "assurance_tier_not_available"

#: The three hypotheses of Theorem ``thm:firstorder`` (ii), stated on the
#: ITERATE ALONE and naming no set -- which is what lets part (iiib) carry them
#: onto the relaxed family unchanged.
FO_ITERATE_HYPOTHESES: tuple[str, ...] = (
    "H-POS",
    "H-SUPP",
    "H-NOPERT",
)

#: The four machine-readable reasons that WITHDRAW ``h_lb`` and drop
#: ``reported_tier`` to `estimate` (Remark ``rem:fo-interface``). A
#: withdrawal is never a weakening of what ``h_lb`` means: "there is no reduced
#: form of the claim".
#:
#: RE-DERIVED BY HAND. The amended
#: ``frank-wolfe/req:first-order-withdrawal`` lists four items -- (i) "(H-POS)
#: fails", (ii) "(H-SUPP) fails", (iii) "a gradient perturbation was
#: applied", (iv) the point fails a check of ``req:iterate-checks`` or its
#: acceptance-side component was not formed on the exact island -- with the
#: interface spellings of each, and then says: "Neither the point the oracle
#: returned at that iterate nor its status removes the iterate from I". The
#: frank-wolfe interface's ``withdrawal_reasons.frozen_spellings`` carries the
#: same four. Old value: these four and ``oracle_not_optimal``, the former
#: item (v), which the amendment deleted and meat-core's interface lists
#: under ``refusal_reasons.retired``.
FO_WITHDRAWAL_REASONS: tuple[str, ...] = (
    "gradient_hypothesis_positivity",
    "gradient_hypothesis_support",
    "gradient_perturbation_applied",
    "iterate_not_feasible",
)

#: The three checks of Remark ``rem:fo-iterate-checks``, ALL THREE ON THE ``J``
#: FACTOR, together with the threshold row of Section 2.6 that decides each.
#: The acceptance factor is NOT in this list and adds no fourth check: it is
#: true by construction on the exact island (Remark ``rem:acc-side``).
FO_MEMBERSHIP_CHECKS: tuple[tuple[str, str, str], ...] = (
    (
        "per-block positive semidefiniteness",
        "iterate_positivity",
        "exactly 0, at no window: the relaxed family does not relax positivity, "
        "so a point admitted at a positive window lies in NO Feas^J(epsilon) "
        "and the objective is not defined at it",
    ),
    (
        "the coupling residual",
        "iterate_coupling",
        "declared: the residual is drift over the convex combinations that "
        "built the iterate and is measured orders above any declaration "
        "defect, so putting it under tau_num would refuse every run",
    ),
    (
        "each declared constraint row",
        "constraint_rows",
        "declared, required on every run: checking two of the three is not "
        "checking the condition",
    ),
)


def _fo_bracket_one_sector(alpha: float, weight: float, vertex: float) -> float:
    """Return the bracket Eq. ``eq:hlb`` on the one-sector reduction above.

    ``weight`` is the iterate's key-active sector weight ``w0``, ``vertex``
    the oracle return's. The acceptance term vanishes (singleton acceptance
    set), so this is the whole bracket at a single iterate; ``h_lb`` is its
    MAXIMUM over the run's iterate index set.
    """
    c = 1.0 - float(2.0 ** (1.0 - alpha))
    k = 1.0 - c * weight
    return (-math.log2(k) + _LOG2E * c * (vertex - weight) / k) / (alpha - 1.0)


def _fo_toy1_eighth(alpha: float) -> float:
    """Return the TOY-1 bracket at w0 = 1/8, the maximum over FO_TOY1_TABLE."""
    return _fo_bracket_one_sector(alpha, 0.125, 0.0)


#: TOY-1, ``(w0, ((alpha, bracket), ...))`` at the oracle vertex ``w0* = 0``.
#: The bracket is STRICTLY DECREASING in ``w0`` and STRICTLY NEGATIVE on
#: ``(0, 1]``, so the maximum over any finite iterate set is attained at its
#: SMALLEST weight -- here 1/8 -- and ``h_lb < 0 = h_low`` at every admissible
#: iterate set. See ``O-FO-BRACKET-UNCONSTRAINED``.
FO_TOY1_TABLE: tuple[tuple[float, tuple[tuple[float, float], ...]], ...] = (
    (
        1.0,
        (
            (1.05, -0.01753061486564607),
            (1.25, -0.09187266606133404),
            (1.5, -0.19516770460923105),
            (1.75, -0.31149218064895673),
            (1.9, -0.3882989987365879),
        ),
    ),
    (
        0.5,
        (
            (1.05, -0.004281911904585319),
            (1.25, -0.020386367884354217),
            (1.5, -0.03816127888668841),
            (1.75, -0.0532993292422721),
            (1.9, -0.061138319313527194),
        ),
    ),
    (
        0.25,
        (
            (1.05, -0.001058249400760213),
            (1.25, -0.004818456748520161),
            (1.5, -0.008557898120227503),
            (1.75, -0.011384841583614894),
            (1.9, -0.012708070938466284),
        ),
    ),
    (
        0.125,
        (
            (1.05, -0.00026305581199126036),
            (1.25, -0.0011722145799386297),
            (1.5, -0.0020322531662131105),
            (1.75, -0.0026467393339411247),
            (1.9, -0.002920730375030955),
        ),
    ),
)

#: TOY-5, the two STRICTLY SUBOPTIMAL iterates, at the oracle vertex
#: ``w0* = 1/2`` (the constraint boundary). At ``w0 = 1/2`` the bracket IS
#: ``h_low`` and is frozen by ``O-FO-BRACKET-CONSTRAINED`` through the
#: registry's existing closed form rather than duplicated here.
FO_TOY5_TABLE: tuple[tuple[float, tuple[tuple[float, float], ...]], ...] = (
    (
        0.75,
        (
            (1.05, 0.4945725901372236),
            (1.25, 0.4726516913220123),
            (1.5, 0.44493274948593037),
            (1.75, 0.41712581097839774),
            (1.9, 0.4005246646721292),
        ),
    ),
    (
        1.0,
        (
            (1.05, 0.49123469256717744),
            (1.25, 0.4540636669693331),
            (1.5, 0.40241614769538436),
            (1.75, 0.34425390967552166),
            (1.9, 0.3058505006317061),
        ),
    ),
)


O_FO_BRACKET_SINGLETON = OracleEntry(
    oracle_id="O-FO-BRACKET-SINGLETON",
    claims=("C22",),
    kind="analytic-limit",
    subject=(
        "Singleton feasible set: the bracket's linear term is IDENTICALLY ZERO "
        "and h_lb = h_low = log2(m) exactly, at every alpha in (1, inf)."
    ),
    derivation="""\
TOY-3(m). The declaration has ONE one-dimensional sector, so the feasible set
Eq. eq:feas is {omega : omega >= 0, tr omega = 1} on a one-dimensional space,
i.e. the SINGLE POINT omega = [1]; and the acceptance set is the singleton
{delta_chat0}. Both minimizations of Eq. eq:lmo are therefore over one-point
sets, so the pair (v_t, S_t) Assumption A-LMO speaks of is (q_t, J_t) itself,
BOTH DIFFERENCES IN Eq. eq:hlb VANISH, and the bracket at the only admissible
iterate is the objective there:

  h_lb = O^J_alpha(x_0) = h_low = log2(m)          (O-HLOW-FULLY-DEPHASED).

WHY THIS IS WORTH FREEZING RATHER THAN OBVIOUS. It is the one case in which
A-LMO is DISCHARGED RATHER THAN ASSUMED on BOTH sides: the feasible-side
minimum is attained at the only feasible point, so the inequality
<G_t, S_t> <= min_{J'} <G_t, J'> holds with equality by inspection and no
backend is trusted for it. The contract's own asymmetry -- "its acceptance half
is discharged, not assumed" (ass:lmo (c)) -- becomes total here, and the entry
is the reference point against which the OTHER three, where the feasible half
is genuinely assumed, are read.

HYPOTHESIS CHECK, all three of thm:firstorder (ii) at this point.
  (H-POS)    q(chat0) = 1 > 0; P_chat0 = 1 > 0; K_chat0 = m^{1-alpha} > 0.
  (H-SUPP)   X_chat0,s0 = |eta><eta| with |eta> = (1,...,1)/sqrt(m) has rank 1,
             and dim W_chat0,s0 = rank of the Kraus stack = 1 (the stack is the
             single column with every entry 1/sqrt(m)). Rank equality holds.
  (H-NOPERT) vacuous: there is nothing to perturb and no run needs to.
  MEMBERSHIP: the J factor by the three checks of rem:fo-iterate-checks at the
  single feasible point, and the acceptance factor by construction, the
  acceptance set having one exact rational element.

THE VALUE IS THE SAME NUMBER AS THE ESTIMATE, and that is not a defect: at a
point of the EXACT feasible set thm:firstorder (i) gives O >= h_low and (ii)
gives h_lb <= h_low, so at the unique feasible point both are equalities. An
implementation whose two reported numbers DIFFER on this declaration has a
defect in one of them, and this entry is what makes that falsifiable.
""",
    toy_id="TOY-3(m=2)",
    value=1.0,
)

O_FO_BRACKET_KEY_INERT = OracleEntry(
    oracle_id="O-FO-BRACKET-KEY-INERT",
    claims=("C7", "C22"),
    kind="analytic-limit",
    subject=(
        "Every pair key-inert: the gradient is CONSTANT on the feasible set, "
        "the bracket's linear term vanishes at every vertex, and "
        "h_lb = h_low = 0 exactly at every iterate and every alpha."
    ),
    derivation="""\
TOY-2. Every pair (chat0, s) is key-inert, so f_{chat0,s} == 0 for both sectors
(Proposition prop:exact-cancellation) and K_chat0(omega) = P_chat0(omega) = w0 + w1 on the whole
cone -- not merely on the feasible set. With q = delta_chat0 and
Chat_key = {chat0}, Eq. eq:objective is

  O(w0, w1) = -log2(w0 + w1) - (1/(alpha-1)) log2(w0 + w1) ,

a function of the SUM alone. Differentiating at a feasible point (where the sum
is 1) gives the two block components

  G_0 = G_1 = -log2(e) (1 + 1/(alpha-1)) = -log2(e) alpha/(alpha-1) ,

so the linear form <G, J'> = G_0 (w0' + w1') is CONSTANT on the feasible set,
which is the simplex w0' + w1' = 1. Every point of it attains the minimum; in
particular the oracle's S_t does, whatever it returns, and

  <G_t, S_t - J_t> = G_0 (1 - 1) = 0 .

Hence h_lb = O(x_t) = 0 = h_low AT EVERY FEASIBLE ITERATE, at every alpha.

WHAT THIS DISCRIMINATES, and it is the reason the entry exists beside
O-HLOW-DETERMINISTIC, which freezes the same 0 for the ESTIMATE. An
implementation that computes the bracket with a WRONG SIGN on the linear term,
or that forms it as O(x_t) + <G_t, S_t> - <G_t, J_t> with the two pairings taken
over different index sets, still returns 0 here only if the two pairings agree
-- which they do only when the gradient is read on the same coordinates as the
iterate. The zero is therefore not vacuous: it is the case in which the
linear term is EXACTLY zero for a stated structural reason, and a nonzero
answer localizes the defect to the pairing.

HYPOTHESIS CHECK. (H-POS): q = 1 > 0, P = K = 1 > 0. (H-SUPP): VACUOUS --
S_K(chat0) is EMPTY, both sectors being constraint-active rather than
key-active, so the hypothesis quantifies over nothing. That is itself worth
pinning: an implementation that reads (H-SUPP) as a condition on ALL sectors
rather than on the key-active ones withdraws h_lb here and reports `estimate`,
which is a defect this entry catches.
""",
    toy_id="TOY-2",
    value=0.0,
)

O_FO_BRACKET_UNCONSTRAINED = OracleEntry(
    oracle_id="O-FO-BRACKET-UNCONSTRAINED",
    claims=("C22",),
    kind="analytic-limit",
    subject=(
        "TOY-1: the bracket is STRICTLY NEGATIVE at every admissible iterate "
        "and its supremum 0 = h_low is NOT ATTAINED, because the only iterate "
        "reaching it fails (H-SUPP). max{0, h_lb} = 0 and the clamp fires."
    ),
    derivation="""\
TOY-1, on the one-sector reduction stated at the head of Group 10. The feasible
set is w0 in [0, 1] with w1 = 1 - w0; the oracle vertex is w0* = 0, because
G_0 - G_1 = log2(e) c / ((alpha-1) K) > 0 makes the linear form increasing in
w0'. So

  h_lb(w) = B(w; 0) = [ -log2 K(w) - log2(e) c w / K(w) ] / (alpha - 1) ,
            K(w) = 1 - c w ,  c = 1 - 2^{1-alpha} in (0, 1).

TWO PROPERTIES, BOTH PROVED AND NEITHER MEASURED.

(1) B(w; 0) <= 0 FOR EVERY w in [0, 1], with equality only at w = 0. Substitute
u := c w in [0, c] and write B = (log2(e)/(alpha-1)) psi(u) with
psi(u) := -ln(1-u) - u/(1-u). Then psi(0) = 0 and

  psi'(u) = 1/(1-u) - 1/(1-u)^2 = -u/(1-u)^2 <= 0 ,

strictly negative for u > 0. So psi <= 0 on [0, c] and B(w; 0) < 0 for w > 0.
THE INEQUALITY h_lb <= h_low = 0 OF thm:firstorder (ii) IS THEREFORE STRICT AT
EVERY POSITIVE WEIGHT, and it is strict for a structural reason -- the
linearization of a strictly convex function at a point away from the minimizer
under-estimates the minimum -- not by an accident of arithmetic.

(2) THE SUPREMUM IS NOT ATTAINED, BECAUSE w = 0 IS NOT AN ADMISSIBLE ITERATE.
At w0 = 0 the key-active branch operator is X_chat0,s0 = 0, whose rank is 0,
while dim W_chat0,s0 = 1 (the Kraus stack of s0 is the column
(sqrt(1/2), sqrt(1/2))^T). So (H-SUPP) FAILS, the iterate contributes no
bracket, and h_lb is the maximum over iterates with w > 0 -- strictly negative.
A run whose iterates approach the optimum therefore reports h_lb -> 0^- and
NEVER 0.

THE FROZEN TABLE. FO_TOY1_TABLE carries B(w; 0) at w = 1, 1/2, 1/4, 1/8 across
ALPHA_GRID. B is STRICTLY DECREASING in w (psi is, and the prefactor is
positive), so the maximum over any finite iterate set is at its SMALLEST
weight; over the four tabulated weights that is w = 1/8, which is this entry's
closed form.

WHAT REACHES THE KEY LENGTH. max{0, h_lb} = 0 on every such run, so
Eq. eq:keylength-fo yields no positive length and the boolean
`first_order_clamped` is TRUE beside an h_lb that carries the UNCLAMPED
negative value (Section 2.2, the h_lb row; rem:fo-negative-values). Reporting 0
in the h_lb field is a defect: "h_lb itself carries the unclamped value, so
that a reader sees what was computed and not only what was used."

AND WHAT THE CLAMP DOES NOT DO. Remark rem:fo-arithmetic (a): clamping at zero
"corrects only the LOW side; it cannot bring down a bracket that came out too
high". ARCHITECTURE_SPEC.md Section 3.8 measures exactly that failure on this
instance -- a run reporting h_lb = 4.8121e-11 where the true value is 0, the
whole of the excess being the oracle's returned vertex -- so this entry's
frozen negatives are what a CORRECT oracle produces and the measured positive
is what a trusted, unbudgeted one produced. The two are not in conflict: the
theorem's conclusion is in EXACT REAL ARITHMETIC.
""",
    toy_id="TOY-1",
    closed_form=_fo_toy1_eighth,
    frozen_values=(
        (1.05, -0.00026305581199126036),
        (1.25, -0.0011722145799386297),
        (1.5, -0.0020322531662131105),
        (1.75, -0.0026467393339411247),
        (1.9, -0.002920730375030955),
    ),
    hypotheses=(
        "(H-SUPP) fails at w0 = 0, so the supremum of the bracket is not "
        "attained and every admissible iterate gives h_lb < 0",
    ),
)

O_FO_BRACKET_CONSTRAINED = OracleEntry(
    oracle_id="O-FO-BRACKET-CONSTRAINED",
    claims=("C17", "C22"),
    kind="analytic-limit",
    subject=(
        "TOY-5: at the constrained optimum the bracket is TIGHT -- "
        "h_lb = h_low = (1/(alpha-1)) log2(2/(1+2^{1-alpha})) exactly -- and "
        "STRICTLY BELOW it at every other iterate."
    ),
    derivation="""\
TOY-5, on the one-sector reduction stated at the head of Group 10, with the
declared row w0 >= 1/2 narrowing the feasible interval to [1/2, 1]. The linear
form is still increasing in w0' (the same sign computation), so THE ORACLE
VERTEX IS THE CONSTRAINT BOUNDARY w0* = 1/2 rather than 0, and

  h_lb(w) = B(w; 1/2)
          = [ -log2 K(w) + log2(e) c (1/2 - w) / K(w) ] / (alpha - 1) .

AT THE OPTIMAL ITERATE w = 1/2 THE LINEAR TERM IS EXACTLY ZERO -- the factor
(w* - w) vanishes, in exact arithmetic and in binary64 alike, 0.5 - 0.5 being
exactly 0.0 -- so

  h_lb = O(1/2) = (1/(alpha-1)) log2( 2 / (1 + 2^{1-alpha}) ) = h_low ,

which is the closed form O-HLOW-CONSTRAINED already freezes, re-used here
rather than restated so that the two entries cannot drift apart.

AT EVERY OTHER ITERATE THE BRACKET IS STRICTLY BELOW h_low. With a := K(w) and
b := K(1/2), so that b - a = c (w - 1/2) >= 0,

  B(w; 1/2) - h_low = (log2(e)/(alpha-1)) [ ln(b/a) - (b-a)/a ] <= 0

by ln(x) <= x - 1 at x = b/a, with equality only at b = a, i.e. w = 1/2. The
frozen values at w = 3/4 and w = 1 are FO_TOY5_TABLE.

WHY THIS ENTRY IS THE LOAD-BEARING ONE OF GROUP 10. It is the only case in
which the first-order bound is TIGHT at a value that is not zero, so it
discriminates the contract's bracket from three wrong ones at once: a bracket
that omits the linear term returns O(w) and is too HIGH at every w > 1/2; a
bracket that takes the vertex at the WRONG END of the interval (w0* = 1, the
maximizer) returns a number ABOVE h_low, violating thm:firstorder in the unsafe
direction; and a bracket that minimizes over the RELAXED family
Feas^J(epsilon) rather than the exact Feas^J -- the substitution ass:lmo (d)
forbids by name -- takes its vertex outside [1/2, 1] and returns a number below
the frozen one, which is sound but is not what the contract states and is
detectable here.

HYPOTHESIS CHECK. (H-POS): q = 1, P = 1, K(w) = 1 - c w >= 1 - c = 2^{1-alpha}
> 0 on the whole interval. (H-SUPP): X_chat0,s0 = w0 |eta><eta| has rank 1 =
dim W_chat0,s0 for EVERY w0 >= 1/2, so unlike TOY-1 the hypothesis holds at
every feasible point INCLUDING THE OPTIMUM -- which is precisely why the
bracket can be tight here and cannot be there. (H-NOPERT): no perturbation is
applied or needed.

THE SECURITY GATE IS UNAFFECTED AND IS NOT WHAT THIS ENTRY PINS. TOY-5's
constraint list is nonempty and its attack_set_license is None, so part (ii) of
the two-part gate of Section 4.19 fails and NO key length may be emitted from
this declaration whatever h_lb is (O-CONSTRAINT-GATE). The bracket is
exploration output here, exactly as h_low is.

ONE ARITHMETIC OBSERVATION, RECORDED BECAUSE IT ILLUSTRATES rem:fo-arithmetic
RATHER THAN BECAUSE IT AFFECTS THE FROZEN VALUE. B(1/2; 1/2) and the closed
form of O-HLOW-CONSTRAINED are the SAME REAL NUMBER written two ways, and their
binary64 evaluations differ by up to 9 ulp on ALPHA_GRID (0 ulp at alpha = 1.5,
9 at 1.25). The frozen value is the mathematical one, taken through the
registry's existing closed form; a run comparing its computed h_lb against its
computed h_low on this declaration must not treat a last-ulp difference as a
violation, which is the contract's own instruction: "a comparison of h_lb
against the reported estimate is a DIAGNOSTIC, never an assertion".
""",
    toy_id="TOY-5",
    closed_form=_hlow_constrained,
    frozen_values=O_HLOW_CONSTRAINED.frozen_values,
)


@dataclass(frozen=True)
class FirstOrderKeyLengthCase:
    """One frozen evaluation of Eq. ``eq:keylength-fo`` from ``max{0, h_lb}``."""

    case_id: str
    rounds: int
    h_lb: float
    lambda_ec: int
    eps_ev: float
    eps_pa: float
    alpha: float
    expected: int
    clamped: bool
    arithmetic: str


FIRST_ORDER_KEY_LENGTH_CASES: tuple[FirstOrderKeyLengthCase, ...] = (
    FirstOrderKeyLengthCase(
        case_id="FOKL-1-tight",
        rounds=10_000,
        h_lb=0.45689339367277615,
        lambda_ec=1_000,
        eps_ev=2.0**-32,
        eps_pa=2.0**-32,
        alpha=1.5,
        expected=3_441,
        clamped=False,
        arithmetic="""\
h_lb is the TIGHT bracket of O-FO-BRACKET-CONSTRAINED at alpha = 1.5, so the
case is chained to a value that is itself derived. With alpha = 1.5,
alpha/(alpha-1) = 3 and log2(1/eps) = 32 for both budgets:
  n max{0, h_lb} = 10 000 * 0.45689339367277615 = 4568.9339367277615
  - lambda_EC = -1000                          -> 3568.9339367277615
  - ceil(log2(1/eps_EV)) = -32                 -> 3536.9339367277615
  - (alpha/(alpha-1)) log2(1/eps_PA) = -96     -> 3440.9339367277615
  + 1                                          -> 3441.9339367277615
  floor                                        -> 3441
No clamp: the bracket is positive. THE FORMULA IS Eq. eq:keylength WITH h_low
REPLACED BY max{0, h_lb} AND NOTHING ELSE CHANGED -- Corollary cor:fo-keylength
says so in terms: "no additional subtrahend, no floor beyond the one max{0, .}
already supplies, no arithmetic requirement of any kind".""",
    ),
    FirstOrderKeyLengthCase(
        case_id="FOKL-2-clamped",
        rounds=10_000,
        h_lb=-0.0020322531662131105,
        lambda_ec=0,
        eps_ev=1.0,
        eps_pa=1.0,
        alpha=1.5,
        expected=1,
        clamped=True,
        arithmetic="""\
h_lb is the NEGATIVE bracket of O-FO-BRACKET-UNCONSTRAINED at alpha = 1.5 and
w0 = 1/8. The clamp of Corollary cor:fo-keylength fires: max{0, h_lb} = 0, so
  n * 0 - 0 - 0 - 0 + 1 = 1 ,  floor -> 1 .
TWO THINGS THIS PINS. First, THE CLAMP IS APPLIED TO h_lb BEFORE THE FORMULA,
not to the formula's output: feeding the unclamped -0.00203... in would give
10 000 * (-0.00203...) + 1 = -19.32..., floor -20, and then the platform's own
max{0, .} would return 0 -- a DIFFERENT answer, and the wrong one. Second, the
boolean `first_order_clamped` is TRUE on this run and `h_lb` still carries
-0.0020322531662131105, the unclamped value.
The budgets are the degenerate eps = 1 so that the arithmetic isolates the
clamp; at any realistic budget the length is 0 by KL-3-clamp's mechanism as
well.""",
    ),
    FirstOrderKeyLengthCase(
        case_id="FOKL-3-monotone-anchor",
        rounds=10_000,
        h_lb=0.45689339367277615,
        lambda_ec=2_000,
        eps_ev=2.0**-32,
        eps_pa=2.0**-32,
        alpha=1.5,
        expected=2_441,
        clamped=False,
        arithmetic="""\
FOKL-1 with lambda_EC doubled from 1 000 to 2 000. The length falls by exactly
1 000 bits, 3441 -> 2441: Proposition prop:monotone (i) holds VERBATIM for the
first-order length, because h_lb "depends on the iterates, the oracle returns
and the declaration, and on none of (lambda_EC, eps_EV, eps_PA)" -- Corollary
cor:fo-keylength's proof carries prop:monotone's word for word with
max{0, h_lb} in place of h_low. The pair (FOKL-1, FOKL-3) is the falsifiable
form of that sentence.""",
    ),
)

O_FO_KEY_LENGTH = OracleEntry(
    oracle_id="O-FO-KEY-LENGTH",
    claims=("C14", "C15", "C22"),
    kind="toy-instance",
    subject=(
        "l_max from max{0, h_lb} through Eq. eq:keylength-fo, on three frozen "
        "cases: tight, clamped, and the leakage-monotonicity anchor."
    ),
    derivation="""\
contract.tex Corollary cor:fo-keylength (C22c), Eq. eq:keylength-fo. Each case's
arithmetic is written out in FIRST_ORDER_KEY_LENGTH_CASES, and each h_lb input
is taken from a Group 10 bracket oracle rather than invented, so the chain from
the objective through the linearization to the reported integer is closed.

THE FORMULA IS Eq. eq:keylength WITH h_low REPLACED BY max{0, h_lb}, AND
NOTHING ELSE CHANGED. That is the corollary's own sentence, and it is what this
entry exists to pin: an implementation that subtracts a further term on the
first-order path -- a relative-entropy penalty, a gap, a "safety margin" -- is
claiming a theorem this contract does not have. Remark rem:fo-interface's
closing paragraph forbids one such substitution BY NAME: "it imports no
relative-entropy penalty onto the objective from any source. An implementation
that subtracts a penalty term taken from a von-Neumann-entropy key-rate
formulation -- however standard there -- is claiming a theorem this objective
does not have."

WHICH RUNS MAY EMIT A LENGTH AT ALL. Section 2.2's key_length row: emitted ONLY
on a run whose reported_tier is `first-order`, and ABSENT -- not zero, not
clamped -- on three independent grounds (h_lb absent; the declared bob_povm
admitted with a nonzero defect; h_low = +inf). NONE OF THE THREE IS A ZERO
LENGTH: an implementation that reports l = 0 where the contract requires
absence has made a claim (that the computed length is zero) where the contract
makes none.

ALPHA DOMAIN. Every case has alpha in (1, 2). A-ALPHA confines every key-length
statement to that interval, cor:fo-keylength explicitly among them, even though
C22 itself is stated on (1, inf).
""",
)

O_FO_WITHDRAWAL = OracleEntry(
    oracle_id="O-FO-WITHDRAWAL",
    claims=("C22",),
    kind="fail-closed",
    subject=(
        "h_lb is WITHDRAWN, not weakened, on any of four named failures, and "
        "reported_tier falls to `estimate` with the matching reason."
    ),
    derivation="""\
contract.tex Remark rem:fo-interface, transcribed as data in
FO_WITHDRAWAL_REASONS. h_lb is withdrawn whenever any of the following holds AT
ANY ITERATE CONTRIBUTING TO THE MAXIMUM of Eq. eq:hlb:

  (H-POS) fails                          -> gradient_hypothesis_positivity
  (H-SUPP) fails                         -> gradient_hypothesis_support
  a gradient perturbation was applied    -> gradient_perturbation_applied
  the point fails one of the three checks of rem:fo-iterate-checks and is not
    repairable under rem:fo-iterate-repair, OR its acceptance-side component was not formed on
    the exact island under (alpha), (beta) of rem:acc-side
                                         -> iterate_not_feasible  (EITHER case)

If NO iterate survives, the index set is empty and h_lb is absent for that
reason with the same vocabulary.

RE-DERIVED BY HAND. The
amended req:first-order-withdrawal deletes its former item (v), "the oracle
status does not assert optimality -> oracle_not_optimal", and adds: "Neither
the point the oracle returned at that iterate nor its status removes the
iterate from I". Its reason: the feasible side of a bracket is no longer the
pairing with the oracle's return under A-LMO but the lower bound of
lem:feasible-side-dual, verified from the backend's dual
(req:verified-feasible-side), which "rests on no property of the backend".
The list above is the four that remain; the former paragraph (2) of this
derivation, "NEARLY OPTIMAL IS NOT OPTIMAL", pinned the deleted item and is
withdrawn with it.

THREE THINGS THIS PINS THAT A WEAKER READING WOULD LOSE.

(1) WITHDRAWAL IS NOT DEGRADATION. "Withdrawal is never a weakening of what
h_lb means; THERE IS NO REDUCED FORM OF THE CLAIM." An implementation that
reports a bracket with a caveat, a confidence flag, or a widened interval has
not implemented this rule.

(2) (WITHDRAWN with item (v); see above. A backend status of
`near_optimal` now withdraws nothing: no bracket reads it.)

(3) THE TWO ACCEPTANCE FAILURES CARRY THE SAME REASON. A J factor that fails
its checks and an acceptance factor not formed on the exact island BOTH
withdraw under iterate_not_feasible -- the contract writes "in either case" --
because the hypothesis they violate is the SAME membership in the product
AcceptSet x Feas^J(epsilon). An implementation that invents a sixth reason for
the acceptance case has left the contract's vocabulary; one that SILENTLY
ACCEPTS a binary64-formed q_t has left the contract.

WHAT IS NOT ON THIS LIST, and its absence is the point: the ORACLE. Formerly
that was because A-LMO was not checkable; now no bracket
rests on it (A-LMO is superseded), so no property of the oracle's return or
status can withdraw one.
""",
    value="four reasons; withdrawal, never a weakened claim",
)

O_FO_NEGATIVE_OBJECTIVE = OracleEntry(
    oracle_id="O-FO-NEGATIVE-OBJECTIVE",
    claims=("C22",),
    kind="fail-closed",
    subject=(
        "A negative h_lb is CLAMPED AND FLAGGED; a negative estimate is a "
        "TYPED REFUSAL and is NEVER clamped. The two are handled oppositely."
    ),
    derivation="""\
contract.tex Remark rem:fo-negative-values. Both cases arise in floating point and
neither may be passed over silently, and the asymmetry is the content.

ON THE FIRST-ORDER PATH: CLAMP, AND FLAG. A computed h_lb may be negative --
"the linearization is weak far from the optimum, or the arithmetic crosses
zero" -- and what reaches Corollary cor:fo-keylength is max{0, h_lb}, "which is
a valid lower bound on h_low" because 0 is one and the maximum of two lower
bounds is one. The clamp is RECORDED: the boolean `first_order_clamped` is
emitted beside `h_lb`, "and h_lb itself carries the UNCLAMPED value, so that a
reader sees what was computed and not only what was used". This is not a repair
of anybody's data; it is the substitution of one valid lower bound for another.
O-FO-BRACKET-UNCONSTRAINED is the instance: every admissible iterate of TOY-1
gives a strictly negative bracket.

ON THE ESTIMATE PATH: REFUSE, TYPED, AND NEVER CLAMP. A computed objective at a
point of the EXACT feasible set cannot be negative -- it is a non-negative
multiple of a KL divergence between two probability vectors plus a non-negative
combination of branch terms e_chat = (1/(1-alpha)) log2(K_chat/P_chat), each
non-negative because K_chat <= P_chat (thm:branch-formula's cone clause) and 1/(1-alpha) < 0
-- so a negative one signals a VIOLATED HYPOTHESIS rather than a small number.
The run is refused with the machine-readable reason `negative_objective`,
naming the value and the point, and THE ESTIMATE IS NEVER CLAMPED TO ZERO:
"unlike h_lb it is not a lower bound and zero cannot stand in for it; replacing
it by zero would report a plausible number in place of a detected
inconsistency". A BARE EXCEPTION IS NOT A CONFORMING IMPLEMENTATION OF THIS
RULE -- the reason must be readable by the caller.

AND THE REFUSAL CAN FIRE ON A POINT THAT IS OTHERWISE IN ORDER. At a point of
the RELAXED set the objective CAN be negative: there the second argument of the
divergence term is not a probability vector, and by Remark rem:feas-tol (c'')
the objective is bounded below by -(alpha/(alpha-1)) log2(1 + d_{A_0} epsilon)
and by nothing larger. "A run reads its feasible set at the Group B windows, so
it has a floor below zero and this refusal can fire against a point that is
otherwise in order. THAT IS INTENDED AND THE RULE DOES NOT CHANGE."
""",
    value="clamp-and-flag on h_lb; typed refusal on the estimate",
)

O_FO_LADDER = OracleEntry(
    oracle_id="O-FO-LADDER",
    claims=("C22",),
    kind="fail-closed",
    subject=(
        "Two live rungs, both reported on every run, with reported_tier naming "
        "the claim; `certified` is a shelved name, never emitted, and a "
        "request for it is REFUSED rather than demoted."
    ),
    derivation="""\
contract.tex Section 2.2 (the reported_tier row), Section 2.4 (the
requested_assurance row) and Section 2.5 (the assurance_ladder convention),
read against ARCHITECTURE_SPEC.md Section 3.8's ladder.

THE TWO VALUES ARE ASSURANCE_VALUES_1_0_0 = ("estimate", "first-order"), and
they are the values of BOTH reported_tier AND optimizer_certificate.assurance.
reported_tier is `first-order` EXACTLY WHEN h_lb is present and a key_length is
emitted from it, `estimate` otherwise.

WHAT REPLACES WHAT. At 0.4.0-0.5.0 the second value was `certified` and the
label was gated by four runtime check groups of the certificate band. None of
those checks exists at 1.0.0. `certified` is a SHELVED NAME (SHELVED_TIER_NAME)
and IS NEVER EMITTED; a requested_assurance naming it is REFUSED with
SHELVED_TIER_REFUSAL = "assurance_tier_not_available".

THE REFUSAL IS NOT A DEMOTION, AND THE CONTRACT SAYS WHY IN ONE SENTENCE: "it
is never silently demoted to `first-order`, because A CALLER WHO ASKED FOR A
CERTIFICATE AND RECEIVED A BOUND RESTING ON Assumption ass:lmo HAS BEEN GIVEN
SOMETHING WEAKER THAN IT ASKED FOR UNDER A NAME IT CHOSE." ARCHITECTURE_SPEC.md
Section 3.8 states the same rule platform-wide: "a request for the shelved rung
is refused, never silently demoted. Handing it a weaker claim than it asked
for, under a label it did not choose, is exactly the silent upgrade-in-reverse
the ladder exists to prevent."

THE DEFAULT MOVED TOO, and the reason is arithmetic rather than policy:
requested_assurance defaults to `first-order` at 1.0.0 and defaulted to
`estimate` at 0.5.0, because "the bracket of Theorem thm:firstorder is
accumulated DURING THE SAME SOLVER RUN and not by a separate pass", which was
not true of the certificate post-processing the old default avoided.

AND THE ESTIMATE IS STILL REPORTED ON A FIRST-ORDER RUN. "Every run emits BOTH
live numbers of the ladder ... together with the field reported_tier naming
which of the two carries the claim." An implementation that reports only the
number matching the tier has dropped a required output.

RE-DERIVED BY HAND from foundations/def:tiers as amended: "A tier of a reported
key-rate number is one of the following three labels" -- estimate,
first-order, certified -- "The tiers are ordered, estimate below
first-order below certified ... There is no other tier."
foundations/req:tiers: "reported_tier names the strongest tier reached" and
"the number at the strongest tier is the headline and the reported key length
is formed from it, a weaker tier's number recorded beside it". So the values
are ASSURANCE_VALUES_1_0_0 as re-derived, `certified` exactly where
frank-wolfe/req:certified-evaluation (vi) reports the certified number and a
key length is formed from it; the request row stays retired.
""",
    value=(
        "reported_tier in {estimate, first-order, certified}; certified where the "
        "certified evaluation reports it (re-derived from def:tiers)"
    ),
)


# ===========================================================================
#  Group 11 -- THE 1.0.0 ADMISSION SURFACE (C21 as amended)
# ===========================================================================
#
#  Same band, same run-A instance, same freeze rule as Group 10. What it adds
#  is the part of the admission rule version 1.0.0 CHANGED: the two conditions
#  (T) and (S) that def:optol gains, the datum's move from optional to
#  REQUIRED, and the two round-nowhere clauses Section 2.6 puts on Alice's
#  declared data. Group 9's eleven families, twenty-seven admission cases and
#  six reason strings are UNTOUCHED and still correct on their own subject --
#  the three defects and the (H)/(P)/(C) windows -- and the marks Group 11
#  places on 0.5.0 objects are in SUPERSEDED_BY_1_0_0, not here.
#
#  THE ARITHMETIC ROUTE. Every rounding verdict below was computed twice, by
#  routes sharing no step: (i) by hand from the binary64 exponent -- 2^-60 is
#  below half an ulp of 1, which is 2^-53, so an addition of it to 1 returns
#  its left operand; 1 + 2^-53 is the exact midpoint of the representable
#  neighbours 1 and 1 + 2^-52 and round-to-nearest-EVEN returns 1, the
#  significand of 1 being the even one; and (ii) by evaluating each sequential
#  addition in binary64 and comparing it against the same addition performed
#  over Fraction, an addition being exact exactly when the two agree. The
#  second route decides nothing the first does not; it is recorded because a
#  reader can rerun it in four lines.

#: The SEVENTEEN machine-readable strings contract.tex 1.0.0 spells, grouped by
#: what each one ends. Group 9's OPTOL_REASON_VOCABULARY is the 0.5.0 six and
#: is a SUBSET of this up to one rename; see SUPERSEDED_BY_1_0_0.
REASON_VOCABULARY_1_0_0: tuple[str, ...] = (
    # refused before anything is constructed (Section 2.1; rem:optol-interface (1))
    "declared_tolerance_absent",
    "declared_tolerance_out_of_domain",
    # refused at admission of bob_povm (rem:optol-interface (2))
    "sector_map_disagreement",
    "bob_povm_summation_rounds",
    "bob_povm_hermiticity_defect",
    "bob_povm_negative_part",
    "bob_povm_completeness_defect",
    # refused after admission (rem:optol-interface (3))
    "bob_povm_not_evaluable",
    # refused on a computed object (Section 2.6; rem:fo-negative-values)
    "choi_isometry_inexact",
    "negative_objective",
    # refused on the request's tier (Section 2.4)
    "assurance_tier_not_available",
    # h_lb withdrawn, tier falls to `estimate` (rem:fo-interface)
    "gradient_hypothesis_positivity",
    "gradient_hypothesis_support",
    "gradient_perturbation_applied",
    "iterate_not_feasible",
    "oracle_not_optimal",
    # assurance forced to `estimate`, not a refusal (rem:optol-interface (4))
    "declared_operator_tolerance_open",
)

#: The one string of the 0.5.0 six that 1.0.0 RENAMES, with its new spelling.
#: The other five survive character for character.
RENAMED_REASON_1_0_0: tuple[str, str] = (
    "operator_tolerance_out_of_domain",
    "declared_tolerance_out_of_domain",
)


@dataclass(frozen=True)
class SummationCase:
    """One frozen verdict of condition (S): whether a declared-order sum rounds.

    ``terms`` is the family in ITS DECLARED ORDER, on a one-dimensional block
    so that "entrywise" is a single scalar sequence and the arithmetic is
    checkable by eye. ``partial_sums`` is what binary64 returns after each
    addition; ``exact_total`` is the real sum as a Fraction pair
    ``(numerator, denominator)``.
    """

    case_id: str
    terms: tuple[float, ...]
    partial_sums: tuple[float, ...]
    first_inexact_index: int | None
    exact_total: tuple[int, int]
    computed_completeness_defect: float
    admitted: bool
    reason: str | None
    derivation: str


SUMMATION_CASES: tuple[SummationCase, ...] = (
    SummationCase(
        case_id="S-HAZARD-2^-60",
        terms=(1.0, 2.0**-60, 2.0**-60),
        partial_sums=(1.0, 1.0, 1.0),
        first_inexact_index=1,
        exact_total=(576460752303423489, 576460752303423488),
        computed_completeness_defect=0.0,
        admitted=False,
        reason="bob_povm_summation_rounds",
        derivation="""\
THE FAMILY contract.tex Definition def:optol EXHIBITS, transcribed: one sector
with d_s = 1 and V = {v1 < v2 < v3} carrying F^{(s)} = (1, 2^-60, 2^-60).
Every entry is exactly representable and non-negative, so Delta_herm = 0 and
Delta_pos = 0. 2^-60 is below half an ulp of 1 (which is 2^-53), so EACH OF
THE TWO ADDITIONS RETURNS ITS LEFT OPERAND: the partial sums are 1, 1, 1, the
computed Sigma^{(s)} is 1, and Delta_cpl = |1 - 1| = 0.
SO ALL THREE DEFECTS VANISH AND THE FAMILY WOULD BE **EXACTLY** ADMISSIBLE AT
EVERY tau_num, tau_num = 0 INCLUDED -- while the REAL sum is
1 + 2*2^-60 = 1 + 2^-59 = 576460752303423489/576460752303423488, so
sum_v F_v != 1_Q.
WHAT THAT COSTS IF ADMITTED, in the contract's own list: "V_msm is not an
isometry, M_prot is not trace-preserving, Phi[omega] is not a probability
vector, and by Lemma lem:optol-defined (iii) h_qkd is not defined for the
declared numbers". And "nothing recovers it from smallness":
prop:optol-nobound (ii) and rem:optol-direction say no function of the declared
metadata bounds what such a displacement costs below a scale of tens of bits
per round.
CONDITION (S) CLOSES THAT WINDOW. The first inexact addition is at index 1 (the
second term, 0-based), and the refusal carries the sector, THAT INDEX, and the
declared order. It fires AT EVERY tau_num.""",
    ),
    SummationCase(
        case_id="S-CONVERSE-2^-53",
        terms=(1.0, 2.0**-53),
        partial_sums=(1.0, 1.0),
        first_inexact_index=1,
        exact_total=(9007199254740993, 9007199254740992),
        computed_completeness_defect=0.0,
        admitted=False,
        reason="bob_povm_summation_rounds",
        derivation="""\
THE WITNESS OF Lemma lem:nearpovm's CONVERSE, transcribed. One sector, d_s = 1,
V = {v1 < v2}, F = (1, 2^-53). Both entries are representable and the family
satisfies (T). It lies within eta = 2^-53 IN THE OPERATOR NORM of the family
F* = (1 - 2^-53, 2^-53), which IS a POVM and whose single addition IS exact
(S-EXACT-NEIGHBOUR below).
BUT 1 + 2^-53 IS THE EXACT MIDPOINT of the representable neighbours 1 and
1 + 2^-52 and is not itself representable, and round-to-nearest-EVEN returns 1,
the significand of 1 being the even one. So THE ADDITION ROUNDS, (S) fails, and
F is REFUSED with bob_povm_summation_rounds AT EVERY tau_num -- including
tau_num >= max{2, |V|} eta = 2^-52, which the converse's closing clause would
otherwise say suffices for admission.
THIS IS WHY (S) IS A HYPOTHESIS OF THE CONVERSE AND NOT A REMARK ABOUT IT:
"proximity to an exactly admissible family does NOT imply that the
declared-order sum rounds nowhere". A supplier that reads the converse's first
two sentences alone, declares tau_num >= max{2, |V|} eta and expects admission
"will have its declaration refused".
The same witness shows what Delta_cpl measures WITHOUT (S): F's three defects
all read 0, the COMPUTED sum being the identity, while sum_v F_v = 1 + 2^-53.""",
    ),
    SummationCase(
        case_id="S-EXACT-NEIGHBOUR",
        terms=(1.0 - 2.0**-53, 2.0**-53),
        partial_sums=(1.0 - 2.0**-53, 1.0),
        first_inexact_index=None,
        exact_total=(1, 1),
        computed_completeness_defect=0.0,
        admitted=True,
        reason=None,
        derivation="""\
THE EXACTLY ADMISSIBLE NEIGHBOUR of S-CONVERSE-2^-53, and the reason that case
is a discriminator rather than a curiosity. F* = (1 - 2^-53, 2^-53) has both
entries representable; 1 - 2^-53 lies in the binade [1/2, 1) where the ulp is
2^-53, so BOTH TERMS ARE MULTIPLES OF 2^-53 AND THEIR SUM 1 IS TOO -- the
single addition is EXACT. (T), (S) hold and all three defects vanish, so the
family is EXACTLY ADMISSIBLE by Lemma lem:optol-zero and a run on it may emit a
key length.
THE PAIR IS THE POINT: two families at operator-norm distance 2^-53, both with
representable entries and all three defects reading 0, ONE ADMITTED AND ONE
REFUSED -- and the thing that separates them is not a defect at all but
WHETHER AN ADDITION ROUNDED. An implementation that measures defects and does
not verify the additions cannot tell them apart.""",
    ),
    SummationCase(
        case_id="S-DYADIC-HALVES",
        terms=(0.5, 0.5),
        partial_sums=(0.5, 1.0),
        first_inexact_index=None,
        exact_total=(1, 1),
        computed_completeness_defect=0.0,
        admitted=True,
        reason=None,
        derivation="""\
THE POSITIVE CONTROL, and it is TOY-1's own s0 block: F^{(s0)} = (1/2, 1/2).
Both entries are dyadic and their partial sums are dyadic of the same exponent,
so the single addition is exact, (S) holds, all three defects vanish, and the
block is exactly admissible.
IT IS HERE SO THAT THE (S) CASES ARE NOT ALL REFUSALS. Every toy declaration in
this registry declares its POVM blockwise as non-negative DYADIC reals summing
to one per sector, so every one of them satisfies (S) and every frozen value of
Groups 1-8 is a branch-(i) value under the 1.0.0 rule exactly as it was under
the 0.5.0 rule. THE AMENDMENT MOVES NO EXISTING NUMBER, and this case is the
falsifiable form of that sentence for the condition 1.0.0 added.
It is also the contract's own advice to a producer, instantiated: "emit numbers
whose defining sums close exactly in binary64, DYADIC ENTRIES SUFFICING".""",
    ),
)


@dataclass(frozen=True)
class AlicePovmExactCase:
    """One frozen verdict of the ``alice_povm_exact`` round-nowhere clause.

    The declared four-element BB84 Alice POVM at basis bias ``p_z``:
    ``M_Z0 = p_Z |0><0|``, ``M_Z1 = p_Z |1><1|``, ``M_X0 = p_X |+><+|``,
    ``M_X1 = p_X |-><-|`` with ``p_X = 1 - p_Z``, in the declared order
    ``(Z0, Z1, X0, X1)``. Every element is Hermitian and positive semidefinite
    and the COMPUTED completeness sum is the identity in every case; the only
    question is whether the three entrywise additions are exact.
    """

    case_id: str
    p_z: float
    diagonal_partial_sums: tuple[float, ...]
    first_inexact_index: int | None
    exact_diagonal_total: tuple[int, int]
    computed_sum_is_identity: bool
    admitted: bool
    orders_that_round_nowhere: int
    derivation: str


#: The number of orders of a four-element family, i.e. 4!.
ALICE_ORDER_COUNT: int = 24

ALICE_POVM_EXACT_CASES: tuple[AlicePovmExactCase, ...] = (
    AlicePovmExactCase(
        case_id="AE-PZ-0.9",
        p_z=0.9,
        diagonal_partial_sums=(0.9, 0.9, 0.95, 1.0),
        first_inexact_index=2,
        exact_diagonal_total=(1, 1),
        computed_sum_is_identity=True,
        admitted=False,
        orders_that_round_nowhere=4,
        derivation="""\
THE COST OF THE ROUND-NOWHERE CLAUSE, EXHIBITED ON A FAMILY THAT IS A GENUINE
POVM. At p_Z = 0.9 the declared elements are exactly representable binary64
data; fl(0.9) = 8106479329266893/9007199254740992 and
p_X = 1 - fl(0.9) = 0.09999999999999998 exactly, so p_X/2 = 0.04999999999999999
exactly. THE REAL SUM IS EXACTLY THE IDENTITY: on each diagonal entry it is
fl(0.9) + 2 * (1 - fl(0.9))/2 = 1, and off the diagonal the two X terms are
+p_X/2 and -p_X/2, which cancel exactly. So the family IS a POVM, all three
defects vanish, and it would be exactly admissible under the 0.5.0 rule.
BUT THE THIRD ADDITION ROUNDS. On the (0,0) entry the declared-order partial
sums are 0.9, 0.9, 0.95, 1.0. THE THIRD ADDITION ROUNDS. It takes
p_X/2 = 0.04999999999999999 onto fl(0.9), whose exact real sum is
17113678584007885 / 2^54 = 0.950000000000000011102230246251565404236316680908203125 ,
while the returned binary64 fl(0.95) is
17113678584007884 / 2^54 = 0.9499999999999999555910790149937383830547332763671875 .
They differ by exactly 2^-54, one half-ulp of 0.95 -- the exact sum is the
midpoint of two neighbours and round-to-nearest-even takes the lower. (The same
happens on the (1,1) entry.) So
the round-nowhere clause of `alice_povm_exact` FAILS and the declaration is
REFUSED.
THAT IS THE CONTRACT'S DISCLOSED COST AND NOT A DEFECT OF THE RULE: def:optol
says of the same clause on {F_v} that "what it can refuse is a genuine POVM
whose declared-order sum happens to round -- FAIL-CLOSED, and avoidable by the
producer with the same one sentence Remark rem:optol-reach (d) already
addresses to {M_x} and tau_A: emit numbers whose defining sums close exactly in
binary64, dyadic entries sufficing."
THE VERDICT DEPENDS ON THE ORDER, and that is why OC-5 of interface.yaml
records the order as an open implementation choice with a visible consequence:
of the 24 orders of this four-element family, 20 round somewhere and 4 round
nowhere -- the four that add the two X elements FIRST, smallest terms first.
Section 2.6 requires the order to be one "this module fixes and RECORDS", and
this case is why recording it is not ceremony.""",
    ),
    AlicePovmExactCase(
        case_id="AE-PZ-0.1",
        p_z=0.1,
        diagonal_partial_sums=(0.1, 0.1, 0.55, 1.0),
        first_inexact_index=2,
        exact_diagonal_total=(36028797018963969, 36028797018963968),
        computed_sum_is_identity=True,
        admitted=False,
        orders_that_round_nowhere=0,
        derivation="""\
THE HAZARD DIRECTION, AND IT IS THE ONE THE CLAUSE EXISTS FOR. At p_Z = 0.1 the
declared elements are again exactly representable, with fl(0.1) =
3602879701896397/36028797018963968 and p_X = 1 - fl(0.1) = 0.9 exactly (the
binary64 0.9), so p_X/2 = 0.45 exactly.
THE COMPUTED SUM IS EXACTLY THE IDENTITY -- diagonal partial sums 0.1, 0.1,
0.55, 1.0 -- so all three defects read ZERO. BUT THE REAL SUM IS NOT: it is
fl(0.1) + 2 * fl(0.45) = 1 + 2^-55 = 36028797018963969/36028797018963968.
So sum_x M_x != 1_A of the declared numbers, and the three sites that consume
that relation as an identity of REAL operators -- the proofs of thm:protocol-channel (i) and
(iii) and the identity Eq. eq:massdefect -- are reading something false. This is
the {M_x} instance of exactly the hazard def:optol exhibits for {F_v} at
(1, 2^-60, 2^-60), and Section 2.6's alice_povm_exact row cites the same
witness.
UNLIKE AE-PZ-0.9 THE VERDICT IS ORDER-INDEPENDENT: all 24 orders round
somewhere, so no choice of order admits this family. The pair (AE-PZ-0.9,
AE-PZ-0.1) therefore separates the clause's two faces -- a genuine POVM refused
at a cost, and a non-POVM refused at a benefit -- and shows that the order
question of OC-5 is a question about the FIRST kind only.""",
    ),
    AlicePovmExactCase(
        case_id="AE-PZ-HALF",
        p_z=0.5,
        diagonal_partial_sums=(0.5, 0.5, 0.75, 1.0),
        first_inexact_index=None,
        exact_diagonal_total=(1, 1),
        computed_sum_is_identity=True,
        admitted=True,
        orders_that_round_nowhere=24,
        derivation="""\
THE POSITIVE CONTROL. At the balanced basis choice p_Z = 1/2 every declared
number is dyadic -- p_Z = 1/2, p_X = 1/2, p_X/2 = 1/4 -- and every partial sum
is a multiple of 1/4, so EVERY ADDITION IS EXACT IN EVERY ONE OF THE 24 ORDERS.
The family is Hermitian, positive semidefinite and exactly complete, so
`alice_povm_exact` ADMITS it and a run on it may emit a key length.
IT IS HERE FOR TWO REASONS. First, so that the Alice cases are not all
refusals: the rule admits the instance the platform actually runs (the BB84
receiver of the sibling registries is stated at p_Z = p_X = 1/2). Second,
because it is the ORDER-INDEPENDENT admission against which AE-PZ-0.9's
order-dependence is read: dyadic declared data makes the OC-5 choice
immaterial, which is the producer-side sentence rem:optol-reach (d) addresses
to an instance -- "an instance meets all of this by declaring numbers that are
exactly representable and whose defining sums close exactly in binary64,
addition by addition -- DYADIC ENTRIES SUFFICE -- and by SNAPPING, at the
instance and before this module sees the data, anything that does not."
""",
    ),
)

O_DECLARED_TOLERANCE_REQUIRED = OracleEntry(
    oracle_id="O-DECLARED-TOLERANCE-REQUIRED",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "tau_num is REQUIRED at 1.0.0: an absent declaration is refused with "
        "declared_tolerance_absent BEFORE ANYTHING IS CONSTRUCTED, and there "
        "is no default and no fallback anywhere."
    ),
    derivation="""\
contract.tex Section 2.1 (the declared_tolerance row), Remark
rem:optol-interface (1), and Assumption ass:dtol. Three statements, and the
third is what makes the first two testable.

(1) NO DEFAULT VALUE IS FIXED BY THIS CONTRACT OR BY ANY ARTIFACT DERIVED FROM
IT, AND THERE IS NO FALLBACK. A request that does not declare tau_num is
refused with reason declared_tolerance_absent, "because a defaulted tolerance
decides a security-relevant predicate on NOBODY'S AUTHORITY"
(ARCHITECTURE_SPEC.md Section 3.8, which states the same rule for the platform:
"tau itself has no default and no fallback").

(2) THE DOMAIN IS [0, 1) AND A VALUE OUTSIDE IT IS REFUSED with reason
declared_tolerance_out_of_domain -- the 0.5.0 string
operator_tolerance_out_of_domain RENAMED WITH ITS DATUM (RENAMED_REASON_1_0_0),
and the only one of the 0.5.0 six that changes spelling.
THE UPPER LIMIT IS DERIVED, NOT CHOSEN: at tau_num >= 1 condition (C) is
satisfied by F_v = 0 for every v -- then Delta_cpl = ||-1_{Q_s}||_max = 1 on
every block, the identity's entries being 0 and 1 -- so the rule would no longer
constrain the family at all. (Group 9's OPTOL_DOMAIN_CASES freeze that
derivation and are UNAFFECTED by 1.0.0: the domain is the same interval.)

(3) WHAT CHANGED FROM 0.5.0, AND IT IS A DELETION OF A READING. The 0.5.0 row
was OPTIONAL and "absent means eps_dec = 0"; Group 9 froze that in its DOM-absent
/ DOM-zero and AD-EXACT-absent / AD-EXACT-zero pairs. AT 1.0.0 THE ABSENT CASE
IS NOT A ZERO, IT IS A REFUSAL. The reading AT tau_num = 0 survives untouched
as a LIMITING CASE -- it is the versions 0.1.x-0.4.0 reading verbatim together
with condition (S), by lem:optol-zero -- "and a run may declare it, but NO RUN
INHERITS IT BY OMISSION".
THE PAIRED GROUP 9 CASES ARE THEREFORE HALF-SUPERSEDED, and the mark is in
SUPERSEDED_BY_1_0_0 rather than here: the `zero` half of each pair stands
verbatim, and the `absent` half no longer denotes a run this contract admits.

WHAT THE RUN TIER IN FACT DECLARES IS NOT THIS CONTRACT'S TO SAY and is not
frozen here. ARCHITECTURE_SPEC.md Section 3.8 and
ADR-0008 Section 7.3 record that the modules receive 0, "the exact reading" of
lem:optol-zero. That is a platform decision about a CALLER; what this entry
pins is that the module refuses a request that declares nothing, whoever the
caller is.
""",
    value="declared_tolerance_absent; no default, no fallback, domain [0, 1)",
)

O_BOB_POVM_SUMMATION_ROUNDS = OracleEntry(
    oracle_id="O-BOB-POVM-SUMMATION-ROUNDS",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "Condition (S): a declared family whose declared-order completeness "
        "sum rounds ANYWHERE is refused at EVERY tau_num, tau_num = 0 "
        "included -- even with all three defects reading exactly zero."
    ),
    derivation="""\
contract.tex Definition def:optol condition (S), Lemma lem:optol-zero, Section
2.6's `bob_povm_summation_exact` row, and Remark rem:optol-interface (2). The
four frozen families are SUMMATION_CASES; each carries its partial sums, the
index of its first inexact addition, its exact total as a rational, and its
verdict.

WHY (S) IS A CONDITION OF THE RULE AND NOT A REMARK ABOUT IT. Delta_cpl is a
defect of Sigma^{(s)}, and Sigma^{(s)} is BY Eq. eq:declorder A FLOATING-POINT
SUM -- "that is the whole reason the declared order is part of the datum". So
Delta_cpl = 0 says the COMPUTED sum is the identity; it does NOT say that
sum_v F_v = 1_Q holds of the numbers, "and EVERY CONSUMER OF Delta_cpl IN THIS
CONTRACT READS IT AS SAYING THE LATTER". Section 2.6 enumerates those consumers:
Lemma lem:optol-zero; the ||Xi|| <= d_max Delta_cpl step of lem:optol-defined
(iii); Theorem thm:optol (i) and (iii); and BOTH HALVES of Lemma lem:nearpovm.
"Without (S) the two differ, IN THE UNSAFE DIRECTION AND BY AN AMOUNT NO
DECLARED NUMBER BOUNDS."

THE WINDOW IS EXACTLY 0 AND THERE IS NO OTHER. Section 2.6's row reads "exactly
0 (strict), and at every tau_num including 0", and ass:dtol says the same from
the other side: (T) and (S) "are on the same declared object and are NOT decided
against tau_num". So a run may declare any admissible tau_num and it changes
nothing here.

THE REFUSAL CARRIES THREE THINGS, and an implementation that emits the reason
without them has not implemented the rule: the sector, THE OUTCOME INDEX AT
WHICH THE FIRST INEXACT ADDITION OCCURRED, and the declared order.
SUMMATION_CASES freezes that index for each refused family.

THE DECLARED ORDER IS THE DECLARATION'S, NOT THE MODULE'S. def:optol fixes it
"as part of the declared outcome alphabet V", formed left to right, entrywise,
"WITH NO RE-ORDERING AND NO RE-ASSOCIATION". This is the one round-nowhere
clause of the three whose order the module does NOT choose -- contrast
`alice_povm_exact` and `alice_marginal_exact`, whose order is "one this module
fixes and records" (O-ALICE-EXACT-ORDER, and interface.yaml OC-5).

WHAT (S) COSTS, from the contract: "one pass over declared data at admission,
alongside the sum this module already forms in order to measure Delta_cpl; no
per-iterate arithmetic, no new mathematics, and nothing in any derivation."
""",
    value="bob_povm_summation_rounds, at every tau_num",
)

O_SECTOR_MAP_DISAGREEMENT = OracleEntry(
    oracle_id="O-SECTOR-MAP-DISAGREEMENT",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "Condition (T) is a TYPE rule, not a measurement: the only structural "
        "failure the representation admits is a sector-map disagreement, "
        "refused with sector_map_disagreement at every tau_num."
    ),
    derivation="""\
contract.tex Definition def:optol condition (T), Remark rem:optol-reach (a),
Section 2.5's `operator_form: sector_blocks` convention, and Remark
rem:optol-interface (2).

WHAT CHANGED AT 1.0.0, AND IT IS A CHANGE OF KIND RATHER THAN OF WINDOW. At
0.5.0 (T) read "F_v = Pin_S(F_v) for every v", block-diagonality DECIDED
EXACTLY on a full operator, and Group 9's OPTOL-BLOCK family carries a family
that fails it with an off-block entry. AT 1.0.0 A DECLARED OPERATOR ARRIVES AS
A LIST OF SECTOR BLOCKS PLUS THE SECTOR MAP, so an off-block entry is ABSENT
FROM THE DATUM RATHER THAN SMALL IN IT: "nothing can write one, NOTHING
VERIFIES THAT NONE WAS WRITTEN, and no d_Q x d_Q matrix is assembled in order to
be checked". Sector-block-diagonality HOLDS BY CONSTRUCTION.
SO THE PREDICATE THE 0.5.0 CODE MEASURED HAS NO OBJECT AT 1.0.0. What a
consumer compares is THE SECTOR MAP -- block kind, block identifiers, ordering
-- "and a disagreement is a refusal with a machine-readable reason, WHICH IS
THE ONLY FAILURE MODE THE REPRESENTATION ADMITS".

THE REASON IS NEW AT 1.0.0. At 0.5.0 a (T) failure carried NONE of the six
reason strings and travelled the version-0.4.0 malformed-declaration path --
Group 9's OPTOL-BLOCK admission cases carry reason=None for exactly that
reason, and CHANGE_REQUEST_CANDIDATES_0_5_0's first entry records the reading.
1.0.0 SPELLS THE STRING: sector_map_disagreement, "refused as a malformed
declaration ... AT EVERY tau_num". Group 9's reason=None rows are marked in
SUPERSEDED_BY_1_0_0.

WHY THE DECOMPOSITION MUST BE EXACT, unchanged from 0.5.0 and still the reason
this is a type condition rather than a tolerated defect: Lemma lem:branch-maps (iii),
Proposition prop:exact-cancellation, Theorem thm:removal and Theorem thm:choi all use the
decomposition as an EXACT DIRECT SUM, and the sector factorization
sqrt(F_v) = direct_sum_s sqrt(F_v^{(s)}) that carries Eq. eq:kraus into
Eq. eq:G-sector "is an identity of the functional calculus that holds for a
block-diagonal operator AND FOR NO OTHER". Under the block representation none
of those statements is ever applied to an operator that is only nearly
block-diagonal, "BECAUSE NO SUCH OPERATOR EXISTS AS A DATUM".

AND (T) IS DECIDED BEFORE THE OTHER FOUR. Section 2.2's tolerance_report row
says so and draws the consequence: (T) "is not among exactly_admissible's
conjuncts because IT IS DECIDED BEFORE ANY OF THEM and a disagreement refuses
the run outright", so that boolean is emitted only on runs where (T) holds and
states the remaining FOUR of the five conditions.
""",
    value="sector_map_disagreement, at every tau_num; (T) decided before the rest",
)

O_GENERAL_TAG_NOT_LICENSED = OracleEntry(
    oracle_id="O-GENERAL-TAG-NOT-LICENSED",
    claims=("C17", "C21"),
    kind="fail-closed",
    subject=(
        "A `general`-tagged constraint entry is ADMITTED AS INPUT and every "
        "structural and numerical claim is proved for it, but it is NEVER "
        "LICENSED, so no key length may be emitted -- decided by the TAG, "
        "comparing no numbers."
    ),
    derivation="""\
contract.tex Definition def:homog as amended at 1.0.0, Section 2.1's
constraint_list row, and Section 2.6's Group C row `homogeneity`.

TOY-7 IS THE INSTANCE AND IT NEEDS NO CHANGE. Its declaration carries d_A = 2,
tau_A = I/2, and one entry (O_1, preceq, Theta_1) with Theta_1 = diag(1, 1/2),
a Hermitian operator on A. Under 1.0.0 that entry declares the `general` tag:
the two declared forms are `homogeneous`, carrying a REAL SCALAR c_k from which
Theta_k := c_k tau_A is CONSTRUCTED, and `general`, carrying a Hermitian
Theta_k. TOY-7 carries an operator, so it is `general`.
THE VERDICT IS THE SAME AS AT 0.5.0 AND THE MECHANISM IS NOT. At 0.5.0 part (i)
of the two-part gate ASKED WHETHER Theta_1 = c tau_A -- a numerical test, which
TOY-7 fails because c = 2 from the first diagonal entry and c = 1 from the
second, so no such c exists (O-CONSTRAINT-GATE freezes that reasoning). AT 1.0.0
IT ASKS WHICH FORM THE ENTRY DECLARES AND COMPARES NO NUMBERS. Section 2.1:
"Part (i) is a TYPE check on the declared tag and compares no numbers; it is not
decided at tau_num or at any other window, AND VERSION 1.0.0 REPLACED THE
OPERATOR DECLARATION BY THE SCALAR ONE PRECISELY SO THAT IT COULD NOT BE."

WHY THE OLD MECHANISM WAS UNSAFE, in the contract's own words, because it is the
reason the change is not cosmetic: under the operator form "a declaration
carrying an operator Theta_k merely NEAR c_k tau_A had to be admitted or refused
by a numerical test, and admitting one was unsafe in a way no relaxation of this
contract covers: the transport of Lemma lem:range (i) and Eq. eq:transport
deliver exactly c_k tau_A on the right-hand side, while Eq. eq:feas-modes would
impose the declared Theta_k, and THE TWO FEASIBLE SETS ARE THEN NEITHER NESTED
NOR RELATED by rem:feas-tol's relaxation -- whose window is a spectral floor, or
an entrywise ball, on the RELATION, and not an entrywise-relative window on the
right-hand side."

WHAT A `general` ENTRY MAY STILL DO. It "remains admissible input -- every
structural and numerical claim below is proved for it -- but IT IS NEVER
LICENSED, so a list containing one carries no key-length claim, WHICH IS THE
FAIL-CLOSED DIRECTION". TOY-7's h_low = 0 is therefore still a legitimate value
to report; what may not happen is a key length. THE GATE'S SECOND PART IS
UNAFFECTED: attack_set_license is still required, and TOY-7 carries None, so the
gate fails on both parts independently.

GATE DEGENERATION IS UNCHANGED (Remark rem:cgate): in untrusted-source mode at
any d_A part (i) is VACUOUSLY TRUE, and at d_A = 1 it is a type check that
rejects only a `general` tag a producer can avoid; in both cases the gate rests
entirely on part (ii). O-CGATE-DEGENERATE freezes that: what changes at 1.0.0 is
HOW part (i) is decided, not when it degenerates.

[Aligned with the owner's reading of the gate at d_A = 1, under which
O-CGATE-DEGENERATE was re-derived and re-frozen; no verdict or
value of this entry moved. The paragraph previously read: "at d_A = 1, and in untrusted-source mode at any d_A, part (i)
is VACUOUSLY TRUE ... O-CGATE-DEGENERATE freezes that and is not superseded".]
""",
    toy_id="TOY-7",
    value="general-tagged: admitted, never licensed, no key length",
)

O_ALICE_EXACT_ORDER = OracleEntry(
    oracle_id="O-ALICE-EXACT-ORDER",
    claims=("C21",),
    kind="fail-closed",
    subject=(
        "The alice_povm_exact round-nowhere clause on the BB84 Alice POVM: "
        "refused at p_Z = 0.9 and at p_Z = 0.1, admitted at p_Z = 1/2 -- and "
        "at p_Z = 0.9 the verdict DEPENDS ON THE ORDER the module fixes."
    ),
    derivation="""\
contract.tex Section 2.6, the `alice_povm_exact` row, and Remark
rem:optol-reach (d). The three frozen cases are ALICE_POVM_EXACT_CASES, on the
declared four-element BB84 Alice POVM at basis bias p_Z in the declared order
(Z0, Z1, X0, X1).

THE CLAUSE. {M_x} must satisfy M_x = M_x^dagger and sum_x M_x = 1_A entrywise
and M_x >= 0 as a spectral floor, ALL THREE DEFECTS EXACTLY ZERO -- "not merely
below tau_num" -- AND THE COMPLETENESS SUM VERIFIED TO ROUND NOWHERE: "every one
of its |X| - 1 entrywise additions exact in binary64, IN AN ORDER THIS MODULE
FIXES AND RECORDS, so that the computed sum IS the real sum".

WHAT THE THREE CASES SEPARATE.
  p_Z = 1/2  ADMITTED, in every one of the 24 orders. Dyadic data.
  p_Z = 0.9  REFUSED, and the family IS A GENUINE POVM: its real sum is exactly
             the identity. This is THE DISCLOSED COST of the clause -- a
             fail-closed refusal of correct data -- and it is order-dependent:
             20 of the 24 orders round somewhere, 4 do not (those adding the two
             X elements first).
  p_Z = 0.1  REFUSED, and the family IS NOT A POVM: its real sum is 1 + 2^-55
             while its computed sum is exactly the identity, so all three
             defects read zero. This is THE HAZARD the clause exists for, and it
             is order-INDEPENDENT: all 24 orders round somewhere.

THE ORDER IS THE MODULE'S AND IT IS NOT FIXED BY THE CONTRACT. That is the one
respect in which this clause differs from condition (S) on {F_v}, whose order is
declared with the outcome alphabet and travels with the artifact. Section 2.6
requires the module's order to be FIXED AND RECORDED and names no order, so the
choice is an open implementation choice -- interface.yaml OC-5 -- AND THIS
ENTRY IS WHY IT IS NOT A FREE ONE: a declaration that one order admits, another
refuses. THE CHOICE MUST THEREFORE BE MADE DELIBERATELY, ONCE, AND RECORDED,
which is exactly what the contract asks and what a run-B implementation must
not decide by the accident of a dict iteration order.

WHAT A PRODUCER SHOULD DO INSTEAD OF ASKING FOR A WINDOW, and the contract
addresses it to an INSTANCE rather than to this module: "an instance meets all
of this by declaring numbers that are exactly representable and whose defining
sums close exactly in binary64, addition by addition -- dyadic entries suffice
-- and BY SNAPPING, AT THE INSTANCE AND BEFORE THIS MODULE SEES THE DATA,
anything that does not. It is refused otherwise, with the reason naming the
predicate; THIS MODULE NEVER REPAIRS IT."

NO REASON STRING IS SPELLED FOR THIS REFUSAL and this entry does not invent one.
rem:optol-interface (2) says the strictly-decided predicates "refuse under THEIR
OWN REASONS and are not folded into these three: a reader of a refusal must be
able to tell a tolerance failure from a strictness failure", and that "each such
reason NAMES THE PREDICATE THAT FAILED". The predicate's machine key is
`alice_povm_exact`; the spelling of the reason is not fixed, and is recorded as
an open implementation choice rather than decided here.

NO TOY DECLARATION CARRIES THIS FAMILY. Every meat-core toy has d_A = 1 except
TOY-7, TOY-8 and TOY-9, none of which declares a BB84 Alice POVM, so the cases
above are HAND-AUTHORED FAMILIES in the style of Group 9's OPTOL_FAMILIES rather
than declarations. They need nothing else: the clause is a predicate on {M_x}
alone.
""",
    value="p_Z = 1/2 admitted; p_Z = 0.9 and 0.1 refused; the order is the module's",
)
# ===========================================================================
#  SUPERSESSION -- what the 0.5.0 amendment MARKS in the 0.4.0 freeze
# ===========================================================================
#
#  THE HAND-OFF INVARIANT. Run A does not delete and does not silently edit.
#  Every 0.4.0 frozen object whose expected outcome the amendment changes is
#  MARKED here, with the contract site that invalidates or restates it and the
#  0.5.0 object that replaces it, and run B retires or rewrites it
#  deliberately. `test_registry_integrity.py` fails if a marked object is still
#  asserted, unmarked, by a file that has moved to the amendment.
#
#  `kind` says what sort of mark it is, because the three are not the same
#  obligation:
#    superseded -- the expected value or the statement is INVALIDATED. Run B
#                  must retire or rewrite it; asserting it as it stands would
#                  assert something contract.tex 0.5.0 does not say.
#    incomplete -- every value in it is still correct, but the object no longer
#                  covers what the contract now states. Run B extends it.
#    reframed   -- every value in it is still correct and the object still
#                  covers its subject, but its narrative names something the
#                  amendment changed. Run B rewrites the narrative.
#
#  THE LIST IS SHORT, AND THAT IS THE AMENDMENT'S OWN DOING. Theorem
#  thm:optol (i) says an exactly admissible declaration is "the version-0.4.0
#  reading, VERBATIM" -- every claim C1-C20, every bound, every number -- and
#  every toy declaration in this registry is exactly admissible. So no h_low,
#  no key length, no certificate value and no fail-closed verdict of Groups 1-8
#  moves. What moves is the SPEC VERSION every artifact declares, and one
#  BICONDITIONAL that 0.5.0 falsifies.


@dataclass(frozen=True)
class Supersession:
    """One 0.4.0 frozen object the 0.5.0 amendment marks."""

    #: The module-level name, or the case id inside the table named by `table`.
    name: str
    #: The module-level table it lives in; equal to `name` for a whole object.
    table: str
    #: The module the object lives in: "registry" or a companion's name.
    module: str
    kind: str
    superseded_by: str
    #: The element of contract.tex 0.5.0 that invalidates or restates it.
    contract_site: str
    reason: str
    #: The 0.5.0 names or case ids that replace it. Empty where the object is
    #: retired outright because the thing it tested no longer exists.
    replacement: tuple[str, ...]
    #: The literal text the hand-off scan looks for in a run-B file. It is not
    #: always `name`: for a value pin it is the VALUE, which disappears from
    #: the file when run B retypes it, so the scan shrinks by itself.
    scan_pattern: str


#: A file that names this string has MOVED TO THE AMENDMENT and may not assert
#: a marked object without acknowledging the mark.
AMENDMENT_SPEC_VERSION_MARKER: str = MATHEMATICAL_SPEC_VERSION_0_5_0

#: The spec-version string the 0.4.0 band pins, marked rather than changed.
SUPERSEDED_SPEC_VERSION: str = "meat-core@0.4.0"


SUPERSEDED_BY_0_5_0: tuple[Supersession, ...] = (
    Supersession(
        name="SPEC_VERSION_0_4_0",
        table="SPEC_VERSION",
        module="dummy_bundles, tests.support.mode_bundles",
        kind="superseded",
        superseded_by="0.5.0",
        contract_site=(
            "Section 2.5, artifact_bindings bullet; STATUS.yaml "
            "contract_version 0.5.0; gates.g3"
        ),
        reason=(
            "IT NAMES A CONTRACT THAT IS NO LONGER THE ACCEPTED ONE. "
            "contract.tex Section 2.5 fixes artifact_bindings."
            "mathematical_spec_version as the string "
            "meat-core@<contract_version> OF THE ACCEPTED CONTRACT, and 0.4.0 "
            "was superseded at the 0.5.0 G3, so every artifact declaring it is "
            "one a 0.5.0 consumer must refuse. THE MARK IS THE STRING AND NOT "
            "AN IDENTIFIER, because the tree holds TWO bundle builders that "
            "pin it independently -- tests/oracles/dummy_bundles.py and "
            "tests/support/mode_bundles.py, the second for the source-mode "
            "bundles the first cannot build -- and the implementation's own "
            "MATHEMATICAL_SPEC_VERSION beside them. Marking the VALUE catches "
            "all three and shrinks by itself as each is retyped. NO NUMBER IN "
            "ANY BUNDLE CHANGES: the declaration payload is unaffected, and by "
            "Theorem thm:optol (i) every toy in it is exactly admissible and "
            "carries the 0.4.0 reading verbatim. What is invalidated is the "
            "one string."
        ),
        replacement=("MATHEMATICAL_SPEC_VERSION_0_5_0",),
        scan_pattern="meat-core@0.4.0",
    ),
    Supersession(
        name="O-ASSURANCE-CERTIFIED-GATE",
        table="ORACLES",
        module="registry",
        kind="superseded",
        superseded_by="0.5.0",
        contract_site=(
            "Section 2.2 (the optimizer_certificate row, final clause); "
            "Remark rem:optol-interface (4); Theorem thm:optol (iii)"
        ),
        reason=(
            "ITS SUBJECT IS A BICONDITIONAL AND 0.5.0 FALSIFIES IT. The entry "
            "states 'assurance = certified EXACTLY WHEN the requested "
            "assurance was certified AND all four check groups of Section 4.18 "
            "passed; estimate otherwise'. At 0.5.0 a run on the tolerance "
            "branch of Theorem thm:optol (iii) is FORCED to estimate with the "
            "reason declared_operator_tolerance_open 'regardless of the "
            "requested assurance' -- and the four groups may all pass there, "
            "the arithmetic being perfectly well defined at "
            "Delta_herm = Delta_pos = 0. So the right-hand side of the "
            "biconditional can hold with the left-hand side false. THE FOUR "
            "CHECK GROUPS AND EVERY VERDICT ABOUT THEM ARE UNCHANGED, and on "
            "an exactly admissible declaration -- which is every toy in this "
            "registry -- the entry's content is still exactly right. What is "
            "invalidated is the word EXACTLY."
        ),
        replacement=(
            "O-OPTOL-ASSURANCE-FORCED-ESTIMATE",
            "OPTOL_BRANCH_OUTPUTS",
        ),
        scan_pattern="O-ASSURANCE-CERTIFIED-GATE",
    ),
)


#: The completeness half of the list: 0.4.0 objects a reader would EXPECT to
#: be marked, with the reason each is not. Recording the absences is part of
#: the list being complete -- an unmarked object is a decision, not an
#: oversight.
NOT_SUPERSEDED_BY_0_5_0: tuple[tuple[str, str], ...] = (
    (
        "Every h_low, key length, certificate and polytope value in Groups 1-8",
        "THEOREM thm:optol (i), and this is the amendment's largest single "
        "statement: on an exactly admissible declaration 'every claim C1-C20 "
        "of this contract applies to the declared numbers EXACTLY AS AT "
        "VERSION 0.4.0. The declared eps_dec changes no statement, no bound "
        "and no number.' Every toy declaration in this registry declares its "
        "POVM blockwise as non-negative reals summing to one per sector, so "
        "every one of them is exactly admissible and every frozen value is a "
        "branch-(i) value. O-OPTOL-EXACT-UNCHANGED makes this falsifiable "
        "rather than asserted: OPTOL-EXACT IS TOY-1's POVM.",
    ),
    (
        "ALL_TOYS, SOURCE_MODE_TOYS, CERTIFICATE_TOYS and every declaration in them",
        "Not one operator changes and not one becomes inadmissible. eps_dec is "
        "'a datum of the REQUEST, not a component of the declaration: "
        "Definition def:declaration is UNCHANGED' (Section 4.23, first "
        "bullet), so no toy gains, loses or re-types a field, and none needs "
        "a tolerance to be admitted.",
    ),
    (
        "O-ASSURANCE-ESTIMATE",
        "Its statement -- every entry of this registry carries "
        "assurance = estimate, and agreement with an oracle is never one of "
        "the runtime checks that produce a certified label -- is untouched, "
        "and the Group 9 entries carry assurance = estimate like every other. "
        "The 0.5.0 forced downgrade is a further reason the label is not "
        "reachable from a table, not a change to this one.",
    ),
    (
        "ASSURANCE_VALUES",
        "optimizer_certificate.assurance still takes EXACTLY the two values "
        "{estimate, certified} at 0.5.0; Section 2.2's row is unchanged in "
        "that respect. What 0.5.0 adds is a further ROUTE to `estimate`, not a "
        "third value, so the tuple is correct and complete. Its comment names "
        "0.4.0 as the section it was read from, which was true then and is "
        "true now.",
    ),
    (
        "O-HLOW-INFINITE",
        "Its subject is 'h_low = +inf must be propagated, never clamped, and "
        "NO key-length claim may be emitted WHEN IT IS REACHED' -- a "
        "sufficient condition, not a claim to enumerate every ground for an "
        "absent key_length. 0.5.0 adds a SECOND, INDEPENDENT ground (the "
        "tolerance branch) and Section 2.2's key_length row now names both. "
        "Neither implies the other and neither invalidates this entry; "
        "interface.yaml's key_length row carries the two_grounds_note that "
        "keeps them apart.",
    ),
    (
        "O-MARGINAL-INADMISSIBLE and every tau_A verdict",
        "Remark rem:optol-reach (c) places the marginal OUTSIDE the "
        "tolerance's reach: tau_A >= 0 and tr tau_A = 1 are 'DECIDED EXACTLY, "
        "AT EVERY DECLARED VALUE OF eps_dec'. So every frozen verdict stands "
        "unchanged, at every tolerance, and none of them turns on a window in "
        "any case: tau_A = 0 is refused, `none` and I/d_A and a singular "
        "nonzero tau_A are accepted.",
    ),
    (
        "O-CONSTRAINT-GATE and the two-part security gate",
        "Remark rem:optol-reach (a) and (b) keep the constraint data exact at "
        "every declared tolerance, and the gate's two parts are unchanged. "
        "0.5.0 applies the SAME DISCIPLINE to a second input -- 'the CList "
        "discipline of Section 4.22 applied to a second input: valid "
        "arithmetic, no security output' -- which makes this entry the "
        "precedent for O-OPTOL-EXPLORATION rather than something it "
        "supersedes.",
    ),
    (
        "The four fail-closed certificate entries: O-CERT-DOMAIN-FAIL, "
        "O-CERT-HYPOTHESES-FAIL, O-DUAL-SLACK-NOT-PSD, O-ACC-SIDE-UNSUPPORTED",
        "Each names a CHECK that must fail closed, and every one of them still "
        "must, on every branch. The 0.5.0 forced downgrade is not a check and "
        "does not replace any of them: it fires BEFORE them and independently. "
        "Only the entry stating the BICONDITIONAL over all four -- "
        "O-ASSURANCE-CERTIFIED-GATE -- is marked.",
    ),
    (
        "KEY_LENGTH_CASES and every frozen l_max",
        "Every case is stated on an exactly admissible declaration at "
        "alpha in (1, 2), hence on branch (i), where Theorem thm:keylength is "
        "available unchanged. The 0.5.0 withholding applies to branch (iii), "
        "which no frozen case reaches.",
    ),
    (
        "No registry object enumerates the KeyRateResult FIELD SET",
        "Checked, and recorded because the absence is load-bearing: "
        "operator_tolerance_report is emitted on EVERY run, so an object "
        "asserting a closed list of result fields would be invalidated by the "
        "amendment. There is none. The field set is asserted in run-B tests "
        "against the implementation's own record type, which is run B's to "
        "extend; OPTOL_OUTPUT_KEYS freezes the contract's six output keys for "
        "it to extend against.",
    ),
    (
        "reference.py's evaluators (psd_power, key_pinch, objective, key_length, ...)",
        "Every one of them computes a quantity of Sections 4.2-4.19 on numbers "
        "the caller supplies, and none of them validates a declaration. The "
        "0.5.0 additions -- operator_norm, hermiticity_defects, "
        "negative_parts, completeness_defect, defects, "
        "block_diagonality_defect -- are new functions beside them and change "
        "no existing one.",
    ),
    (
        "The alpha grid, CERT_ALPHA_INTEGER_BETA and Assumption A-ALPHA's domain",
        "A-ALPHA's per-claim enumeration grew to reach C21 and NO DOMAIN WAS "
        "WIDENED: 'alpha in (1, 2) for every key-length statement; "
        "alpha in (1, inf) for C3-C13, C16-C21'. Section 4.23's one key-length "
        "sentence -- the closing clause of prop:optol-nobound -- is confined "
        "to (1, 2) like every other, and every Group 9 alpha is on the "
        "existing grid inside it.",
    ),
)


#: The (file, marked object) pairs that EXIST at the freeze: places a run-B
#: file names a marked object today. The hand-off scan may only SHRINK from
#: this list, never grow, and every pair is work run B must dispose of.
#:
#: Scoped to the meat-core file set BY NAME. The sibling modules'
#: registries and tests are not scanned and not listed: they are other bands'
#: artifacts and marking one of their objects is not this list's business.
PENDING_RETIREMENT_AT_RUN_B: tuple[tuple[str, str], ...] = (
    ("tests/oracles/dummy_bundles.py", "SPEC_VERSION_0_4_0"),
    ("tests/oracles/test_fail_closed.py", "SPEC_VERSION_0_4_0"),
    ("tests/oracles/test_fail_closed.py", "O-ASSURANCE-CERTIFIED-GATE"),
    ("tests/oracles/test_certificate.py", "O-ASSURANCE-CERTIFIED-GATE"),
    ("tests/support/mode_bundles.py", "SPEC_VERSION_0_4_0"),
    (
        "tests/golden/test_certificate_against_registry.py",
        "O-ASSURANCE-CERTIFIED-GATE",
    ),
    (
        "tests/golden/test_fail_closed_against_registry.py",
        "SPEC_VERSION_0_4_0",
    ),
    (
        "tests/golden/test_fail_closed_against_registry.py",
        "O-ASSURANCE-CERTIFIED-GATE",
    ),
    ("tests/golden/test_source_modes_against_registry.py", "SPEC_VERSION_0_4_0"),
    ("tests/unit/test_meat_bundle_validation.py", "SPEC_VERSION_0_4_0"),
    ("tests/unit/test_meat_result_record.py", "SPEC_VERSION_0_4_0"),
    ("tests/integration/test_bb84_slice.py", "SPEC_VERSION_0_4_0"),
    ("tests/integration/test_key_rate_pipeline.py", "SPEC_VERSION_0_4_0"),
    ("tests/integration/test_polytope_pipeline.py", "SPEC_VERSION_0_4_0"),
)

#: The meat-core files the hand-off scan reads, by name. An explicit list and
#: not a glob: the tree also holds receiver-povm, proof-reductions,
#: protocol-compiler and statistics-acceptance tests, which belong to other
#: bands and are none of this invariant's business.
RUN_B_SCANNED_FILES: tuple[str, ...] = (
    # oracle-side (meat-core only; the sibling registries and their tests are
    # other bands' artifacts and are deliberately absent)
    "tests/oracles/dummy_bundles.py",
    "tests/oracles/test_alpha_limit.py",
    "tests/oracles/test_analytic_limits.py",
    "tests/oracles/test_certificate.py",
    "tests/oracles/test_dummy_bundles.py",
    "tests/oracles/test_fail_closed.py",
    "tests/oracles/test_key_length.py",
    "tests/oracles/test_sector_classification.py",
    "tests/oracles/test_source_modes.py",
    "tests/oracles/test_structural_identities.py",
    "tests/support/mode_bundles.py",
    # golden
    "tests/golden/test_alpha_limit_regression.py",
    "tests/golden/test_certificate_against_registry.py",
    "tests/golden/test_choi_and_gradient_oracles.py",
    "tests/golden/test_fail_closed_against_registry.py",
    "tests/golden/test_hlow_against_registry.py",
    "tests/golden/test_key_length_against_registry.py",
    "tests/golden/test_pointwise_against_registry.py",
    "tests/golden/test_polytope_acceptance_against_registry.py",
    "tests/golden/test_source_modes_against_registry.py",
    # unit
    "tests/unit/test_acceptance_geometry.py",
    "tests/unit/test_bb84_closed_forms.py",
    "tests/unit/test_bb84_honest_provider.py",
    "tests/unit/test_bb84_wire_bundle.py",
    "tests/unit/test_bundle_roundtrip.py",
    "tests/unit/test_certificate_acceptance_side.py",
    "tests/unit/test_certificate_budget.py",
    "tests/unit/test_certificate_exact_arithmetic.py",
    "tests/unit/test_certificate_substrate.py",
    "tests/unit/test_meat_bundle_validation.py",
    "tests/unit/test_meat_capabilities.py",
    "tests/unit/test_meat_declaration_maps.py",
    "tests/unit/test_meat_linalg_and_kernel.py",
    "tests/unit/test_meat_result_record.py",
    "tests/unit/test_meat_sector_operations.py",
    "tests/unit/test_source_mode_bundles.py",
    "tests/unit/test_source_mode_objective.py",
    # property and integration
    "tests/property/test_meat_objective_properties.py",
    "tests/integration/test_bb84_slice.py",
    "tests/integration/test_key_rate_pipeline.py",
    "tests/integration/test_polytope_pipeline.py",
)


def is_superseded(name: str) -> bool:
    """Whether ``name`` is marked by the 0.5.0 amendment."""
    return any(entry.name == name for entry in SUPERSEDED_BY_0_5_0)


def supersession(name: str) -> Supersession | None:
    """Return the mark on ``name``, or ``None`` where it is unmarked."""
    for entry in SUPERSEDED_BY_0_5_0:
        if entry.name == name:
            return entry
    return None


#: Every reading this freeze had to take that contract.tex 0.5.0 does not spell
#: in one place, with the verdict. The 0.4.0 freeze closed its own list the
#: same way, and the rule is the same: anything that could NOT be derived
#: exactly is a CHANGE REQUEST reported to the driver, never worked around.
#: NOTHING ON THIS LIST IS OPEN. Each entry names where the contract settles
#: it, and the four that the contract deliberately leaves to an implementation
#: are recorded in interface.yaml as open choices OC-1 to OC-7 instead of being
#: decided here.
CHANGE_REQUEST_CANDIDATES_0_5_0: tuple[tuple[str, str], ...] = (
    (
        "CLOSED BY 0.5.0 -- the reason string for a failure of condition (T)",
        "Definition def:optol decides (T) exactly and Remark "
        "rem:optol-interface (2) refuses its failure 'as a MALFORMED "
        "DECLARATION, at every eps_dec'. Section 1.1 counts the amendment's "
        "additions as 'six machine-readable reason strings --- FIVE REFUSALS "
        "and one assurance reason', and none of the five names "
        "block-diagonality. READING TAKEN: a (T) failure carries NONE of the "
        "six and travels the version-0.4.0 malformed-declaration path, which "
        "the {F_v}-clause of Assumption A-DECL (iii) already governs. Frozen "
        "as OPTOL-BLOCK with reason=None in its three admission cases.",
    ),
    (
        "CLOSED BY 0.5.0 -- whether the two trace checks and the acceptance "
        "frequency sum are inside the tolerance's reach",
        "THEY ARE NOT, and the contract settles it in one sentence rather "
        "than by inference. Remark rem:optol-reach: eps_dec 'governs (H), (P) "
        "and (C) on the declared {F_v} AND NOTHING ELSE. Every other validity "
        "condition of Section 2.1 is DECIDED EXACTLY, AT EVERY DECLARED VALUE "
        "OF eps_dec', and clause (c) names both by name -- 'the marginal "
        "tau_A (Assumption A-DECL (ii): tau_A >= 0, tr tau_A = 1) and the "
        "acceptance set (Assumption A-ACC)'. Clause (d) does the same for "
        "alice_povm. READING TAKEN: the declared tolerance reaches exactly "
        "THREE identities, all on bob_povm; an undeclared window around any "
        "other is a divergence 0.5.0 does not license and never did -- and it "
        "was already a divergence at 0.4.0, since A-DECL required those "
        "identities exactly then too. Frozen as OPTOL_REACH_STATEMENTS and "
        "O-OPTOL-REACH. NO CHANGE REQUEST: the contract answers the question "
        "as asked.",
    ),
    (
        "CLOSED BY 0.5.0 -- whether admission at the boundary Delta = eps_dec "
        "admits or refuses",
        "Definition def:optol writes (H), (P), (C) as 'Delta <= eps_dec', a "
        "NON-STRICT inequality, and Lemma lem:optol-zero reads it at "
        "eps_dec = 0 as 'Delta <= 0, which for non-negative quantities is "
        "vanishing'. READING TAKEN: equality ADMITS. Frozen as the three "
        "boundary pairs, whose 'boundary' halves are all admitted.",
    ),
    (
        "CLOSED BY 0.5.0 -- whether h_cert may be PRESENT on the tolerance "
        "branch, given that Section 2.2 types it 'present only on a run whose "
        "requested assurance is certified and whose certificate checks all "
        "passed' while the branch forces assurance to estimate",
        "The row QUALIFIES ITSELF in its next sentence: 'NOT SO ON THE "
        "TOLERANCE BRANCH ... so h_cert and optimizer_certificate are reported "
        "as EXPLORATION OUTPUT carrying no claim of h_cert <= h_low', and "
        "Remark rem:optol-interface (4) says the same from the other side: "
        "'h_low, h_cert, sector_report and optimizer_certificate MAY BE "
        "reported as exploration output, and as that alone'. READING TAKEN: "
        "h_cert MAY be present there, carrying no claim; the presence rule of "
        "the row's first sentence is the branch-(i) rule. Whether an "
        "implementation computes it at all is a permission, recorded as "
        "interface.yaml open choice OC-7. Frozen as O-OPTOL-HCERT-NO-CLAIM "
        "and the branch='iii' row of OPTOL_BRANCH_OUTPUTS.",
    ),
    (
        "CLOSED BY 0.5.0 -- whether key_length_claim can be true on a run that "
        "emits no key length",
        "YES, and the two facts are about different things. "
        "operator_tolerance_report.key_length_claim 'EQUALS "
        "exactly_admissible' (Section 2.2; Remark rem:optol-interface (5)), a "
        "function of the three measured defects alone; the ABSENCE of "
        "key_length has two independent grounds, the tolerance branch and "
        "h_low = +infinity (Section 2.2, key_length row). READING TAKEN: a run "
        "on an exactly admissible declaration with h_low = +infinity reports "
        "key_length_claim = true and emits no length. Recorded in "
        "interface.yaml as the key_length row's two_grounds_note and frozen in "
        "O-OPTOL-REPORT.",
    ),
    (
        "RECORDED, NOT DECIDED -- which reason is named when more than one "
        "defect exceeds eps_dec",
        "Remark rem:optol-interface (2) writes the three reasons as a list and "
        "fixes no precedence. NOT A CONTRACT GAP, because no frozen case needs "
        "it: every family in OPTOL_FAMILIES has AT MOST ONE nonzero defect, by "
        "construction, so no verdict here depends on the order. Recorded as "
        "interface.yaml open choice OC-5.",
    ),
    (
        "RECORDED, NOT DECIDED -- whether a REFUSED request carries the "
        "operator_tolerance_report record, and under which key",
        "Section 2.2 says the record is 'emitted on every run' and Remark "
        "rem:optol-interface (5) that 'every run carries' it; rule (2) says "
        "INDEPENDENTLY that the refusal carries 'the measured defect and the "
        "declared eps_dec'. What is not fixed is whether those numbers arrive "
        "AS that record or as refusal metadata, and what a rule-(1) domain "
        "refusal reports when no defect has been measured against a legal "
        "threshold. Section 2.3 places serialization outside the contract, so "
        "this is a serialization question and not a gap. The freeze pins the "
        "VALUES (REPORT-HERM-boundary, REPORT-NEG-boundary) and not the "
        "delivery. Recorded as interface.yaml open choice OC-6.",
    ),
    (
        "RECORDED, NOT DECIDED -- the machine keys of the four numbers and the "
        "two per-outcome vectors, and the record's serialization",
        "contract.tex spells typewriter keys for exactly_admissible and "
        "key_length_claim and states the four numbers and two vectors "
        "MATHEMATICALLY; Section 2.3 puts serialization outside the contract. "
        "Recorded as interface.yaml open choices OC-1 and OC-2, and this "
        "registry states them in the contract's mathematical names.",
    ),
    (
        "RECORDED, NOT DECIDED -- how an ABSENT tolerance is presented at the "
        "artifact boundary",
        "What it DECIDES is fixed: absent means eps_dec = 0 and decides "
        "identically to a declared zero (Lemma lem:optol-zero; DOM-absent and "
        "DOM-zero, AD-EXACT-absent and AD-EXACT-zero, AD-SUBC-absent and "
        "AD-SUBC-zero). What it LOOKS LIKE in the report -- a null, a missing "
        "key, or a literal 0 -- is not fixed, and the contract fixes NO "
        "DEFAULT VALUE anywhere. Recorded as interface.yaml open choice OC-3.",
    ),
    (
        "RECORDED, NOT DECIDED -- the numerical substrate for the three defects",
        "Section 3 fixes ||.|| as the operator norm (largest singular value) "
        "and Eq. eq:defects fixes the three formulas; neither fixes an "
        "algorithm, and Assumption A-IA reaches the CERTIFIED path only, so it "
        "does not cover the admission arithmetic. Every family in this group "
        "is chosen so the answer is a rational number reachable by hand, which "
        "is what lets the freeze be substrate-independent. Recorded as "
        "interface.yaml open choice OC-4.",
    ),
)


# ---------------------------------------------------------------------------
#  WHAT VERSION 1.0.0 MARKS
# ---------------------------------------------------------------------------
#
#  Version 1.0.0 is a MAJOR amendment: it removes four claims (C13, C18, C19,
#  C20) and one assumption (A-IA), so the marks it places are of a kind
#  0.5.0's were not. THREE kinds, kept apart because they license three
#  different dispositions, and the third was not on the brief's list -- it was
#  found by reading the registry against the 1.0.0 claim set and it is the
#  reason this section is not simply "Group 7".
#
#  (1) `superseded-by-scope`. The SUBJECT of the entry is removed
#  from the module's scope, so the entry's value is neither wrong nor
#  reproducible: there is nothing left to compute it against. Such an entry is
#  NOT DELETED AND NOT RE-DERIVED -- "the mode allows a group whose subject the
#  change removes to be marked superseded-by-scope with ONE DERIVATION
#  LINE, rather than re-derived or deleted".
#
#  (2) `superseded` -- the 0.5.0 sense: the entry's or constant's subject
#  SURVIVES and its statement is falsified or renamed by the new version.
#
#  (3) `repoint` -- NEW AT 1.0.0 AND NOT ANTICIPATED. The entry's SUBJECT
#  SURVIVES INTACT and only its CLAIM LIST is stale, because the surviving
#  statement moved from a deleted claim to a surviving one. Six entries are in
#  this position and all six for the same reason: the acceptance-side linear
#  minimization of Remark ``rem:acc-side`` lived inside C19 (weak duality) at
#  0.4.0, and at 1.0.0 it is the acceptance half of C22, where it DISCHARGES
#  Assumption A-LMO rather than feeding a certificate. A repointed entry is
#  neither superseded nor re-derived: its numbers stand, and run B changes the
#  `claims` tuple and nothing else. MARKING THE DIFFERENCE MATTERS BECAUSE THE
#  DISPOSITIONS DIFFER: a superseded-by-scope entry is retired, a repointed one
#  is kept.
#
#  WHY THE CERTIFICATE ENTRIES ARE MARKED RATHER THAN DELETED, said once. They
#  pin C13, C18, C19 and C20, which 1.0.0 REMOVES -- and removing a claim is not
#  retracting it: contract.tex Section 1.3 records that C13 "was proved and is
#  not retracted as mathematics, but it is no longer part of this module's
#  backbone and NO RUN COMPUTES IT". The entries remain correct about the
#  statements they pin; what changed is that this module no longer makes those
#  statements. Deleting them would destroy the record of a proof the human
#  signed at 0.4.0 and re-derive nothing; re-deriving them would spend a run-A
#  instance's arithmetic on a band the operator shelved. The charter chooses the
#  third thing and this is it.

#: The mark version 1.0.0 places on an entry whose SUBJECT it removes from
#: scope. Distinct from "superseded", which is for a subject that survives and
#: a statement the new version falsifies, and from "repoint", which is for a
#: subject that survives with a stale claim list.
SUPERSEDED_BY_SCOPE: str = "superseded-by-scope"

#: The mark on an entry whose subject survives and whose claim list is stale.
REPOINT: str = "repoint"

#: ONE DERIVATION LINE, as a superseded-by-scope group requires. It is the WHOLE of what is owed
#: for the certificate entries and it is recorded once rather than per entry.
CERTIFICATE_SUPERSESSION_LINE: str = (
    "Run A of the meat-core 1.0.0 implementation band: the "
    "certificate entries (Group 7 in full, less O-BETA-ACC which is repointed, "
    "plus O-OPTOL-HCERT-NO-CLAIM from Group 9) are marked SUPERSEDED-BY-SCOPE "
    "-- not re-derived and not deleted. GROUND: decision D3 of the "
    "number model shelved the `certified` rung "
    "(ARCHITECTURE_SPEC.md Section 3.8; FUTURE_SCOPE.md Section 3), and "
    "contract.tex 1.0.0 removes the four claims those entries pin -- C13, C18, "
    "C19, C20 -- together with Assumption A-IA. NO RUN OF THIS MODULE COMPUTES "
    "ANY QUANTITY THEY FREEZE. The values are not withdrawn as mathematics: "
    "each was derived on paper from contract.tex 0.4.0's displayed equations "
    "and each entry carries that derivation in full; what is withdrawn is the "
    "module's claim to compute them. LICENSE: a group whose subject the "
    "change removes is marked superseded-by-scope with one derivation line "
    "(frozen registry Group 7 in meat-core and group PR-O in "
    "proof-reductions)."
)

#: The entries marked SUPERSEDED-BY-SCOPE, with the ground for each stated in
#: one line beside CERTIFICATE_SUPERSESSION_LINE, which carries the shared
#: ground for all of them.
#:
#: THE MARK IS CARRIED HERE AND NOT ON THE ENTRIES. The 0.5.0 band set a
#: `superseded_by` field in place on one entry, and that is why
#: O-ASSURANCE-CERTIFIED-GATE already reads "0.5.0"; setting it to "1.0.0"
#: would ERASE the 0.5.0 mark, which is exactly the byte-immutability the
#: charter protects. A list composes where a field does not, and no entry of
#: Groups 1-9 is edited by this run.
SUPERSEDED_BY_SCOPE_1_0_0: tuple[tuple[str, str], ...] = (
    (
        "O-SERIES-TAILS",
        "C20. The binomial series truncation and its two exact tails. C20 is "
        "deleted with A-IA, no statement of 1.0.0 mentions a series "
        "truncation, and Section 2.6 retires the `certificate_series` "
        "threshold with the words 'deleted with the claims it guarded ... "
        "there is nothing left for it to guard'.",
    ),
    (
        "O-LOG-TAIL",
        "C20. The atanh series and the outward-rounded log2 quotient. Same "
        "ground: the enclosure lemmas exist only to bound a certificate's "
        "arithmetic, and 1.0.0 states no certificate and bounds no arithmetic "
        "-- 'no claim of this contract bounds the floating-point error of any "
        "computation, and none is intended to'.",
    ),
    (
        "O-TRANSFER-BOUNDS",
        "C20. Operator- and Frobenius-norm value transfer, the PAIRING bound "
        "and the Lipschitz window. Same ground.",
    ),
    (
        "O-SQRT-RESIDUAL",
        "C20. ||sqrt A - sqrt B|| <= ||A - B||^{1/2} and its exact-residual "
        "corollary. NOTE FOR A READER WHO MEETS THE SQUARE ROOT AGAIN AT "
        "1.0.0: Remark rem:optol-reach (d) argues from the SAME "
        "non-Lipschitz-at-0 fact, but it does so to explain why {M_x} and "
        "tau_A are decided EXACTLY rather than at a tolerance -- route (A) -- "
        "and it derives no modulus of continuity. The lemma this entry pins is "
        "route (B), which 1.0.0 does not take.",
    ),
    (
        "O-MIX-DOMINATION",
        "C18 (the entry also names C6 and C9a, which SURVIVE, as the internal "
        "imports the domination chain consumes). The perturbed objective and "
        "its zero-penalty domination. C18 is deleted, and Remark "
        "rem:fo-nopert states in terms that the perturbation route is CLOSED: "
        '\'with that band gone, the phrase "after an explicit perturbation" '
        "in Theorem thm:gradient (ii) HAS NO ACCOUNTED INSTANCE anywhere in "
        "this contract'. (H-NOPERT) forbids what this entry freezes.",
    ),
    (
        "O-SPECTRAL-WINDOW",
        "C18. The certified spectral windows on the perturbed operator. Same "
        "ground: there is no perturbed operator at 1.0.0.",
    ),
    (
        "O-WEAK-DUALITY",
        "C19. Weak duality for the linearized subproblem, both source modes. "
        "C19 is deleted, AND 1.0.0 FORBIDS THE SUBSTITUTION THIS ENTRY'S BOUND "
        "INVITES BY NAME: Requirement req:primal-pairing rules out reading a "
        "backend's DUAL objective as a lower bound on the feasible-side "
        "minimum and using it in Eq. eq:hlb, because an interior-point return "
        "is only approximately dual-feasible and the corrected bound carries a "
        "term of UNKNOWN SIGN. 'The bracket uses the PRIMAL pairing at the "
        "returned point and nothing else.' So this entry's subject is not "
        "merely out of scope; using it in the surviving rung would be a defect.",
    ),
    (
        "O-EULER-IDENTITY",
        "C13, C18. Euler's homogeneous-function identity on the perturbed "
        "objective, which the certificate used to relate the objective to its "
        "gradient pairing. Nothing at 1.0.0 consumes it: Theorem "
        "thm:firstorder's Step 2 is the three-chord inequality of convexity, "
        "not a homogeneity identity.",
    ),
    (
        "O-HCERT-END-TO-END",
        "C13, C18, C19, C20. The assembled h_cert. Its OUTPUT ROW is deleted "
        "from Section 2.2 and its formula from the contract.",
    ),
    (
        "O-CERT-KEY-LENGTH",
        "C13 (the entry also names C14 and C15, which SURVIVE). The CERTIFIED "
        "key length of Eq. eq:keylength-cert, deleted with C13. C14's formula "
        "is untouched and C15's monotonicity holds verbatim for the "
        "first-order length; O-FO-KEY-LENGTH is what pins them at 1.0.0, and "
        "its FOKL-3-monotone-anchor case is the direct replacement for this "
        "entry's monotonicity clause.",
    ),
    (
        "O-CERT-DOMAIN-FAIL",
        "C13, C18. The membership x in D fail-closed check. D is defined by "
        "Eq. eq:cert-domain, which is deleted. THE FAIL-CLOSED PRINCIPLE "
        "SURVIVES IN A DIFFERENT PLACE and is pinned by O-FO-WITHDRAWAL: a "
        "point that fails its checks contributes no bracket and h_lb is "
        "withdrawn with iterate_not_feasible.",
    ),
    (
        "O-CERT-HYPOTHESES-FAIL",
        "C13, C18. Hypotheses (H1)-(H4) and their certified floors, all "
        "deleted. Replaced in role, not in content, by O-FO-WITHDRAWAL's five "
        "reasons on (H-POS), (H-SUPP) and (H-NOPERT).",
    ),
    (
        "O-DUAL-SLACK-NOT-PSD",
        "C13, C19. The slack PSD verification that made the dual bound sound, "
        "and the explicitly UNSOUND number the entry freezes to show the check "
        "is load-bearing. Deleted with C19, and see O-WEAK-DUALITY: the dual "
        "route is not merely gone but forbidden.",
    ),
    (
        "O-ACC-SIDE-UNSUPPORTED",
        "C13, C19. The certificate's refusal on an acceptance geometry it "
        "could not certify. THE PRINCIPLE SURVIVES AND THE ENTRY DOES NOT: "
        "Remark rem:acc-side still requires that 'a declaration whose "
        "acceptance set fits neither must supply its own certified beta_acc or "
        "FORGO the first-order output (fail-closed)', and that is recorded as "
        "interface.yaml open choice OC-8. Run B may write a first-order "
        "counterpart; this entry is not it.",
    ),
    (
        "O-ASSURANCE-CERTIFIED-GATE",
        "C13. ALREADY MARKED `superseded` BY 0.5.0, which falsified the word "
        "EXACTLY in its biconditional; 1.0.0 removes its subject outright. The "
        "0.5.0 mark stands on the entry's own field and this list adds the "
        "second, which is why the mark is carried here rather than by "
        "overwriting that field. O-FO-LADDER is the 1.0.0 statement of what "
        "the assurance field may hold.",
    ),
    (
        "O-OPTOL-HCERT-NO-CLAIM",
        "C13, C21 (C21 SURVIVES). A Group 9 entry, not a Group 7 one, and it "
        "is here because its whole subject is h_cert: that on the tolerance "
        "branch h_cert carries no claim of h_cert <= h_low. There is no "
        "h_cert at 1.0.0. THE BRANCH'S RULE SURVIVES for the numbers that do "
        "exist -- on branch (iii) 'h_lb bounds a quantity that is not a bound' "
        "-- and O-OPTOL-EXPLORATION already states it for the outputs "
        "generally; run B extends that entry's output list rather than "
        "reviving this one.",
    ),
)

#: The entries whose SUBJECT SURVIVES and whose CLAIM LIST is stale. Run B
#: changes the `claims` tuple and NOTHING ELSE: no value, no derivation and no
#: verdict of any of these moves.
#:
#: ALL SIX FOR THE SAME REASON, which is worth stating once rather than six
#: times: the acceptance-side linear minimization of Remark ``rem:acc-side``
#: was inside C19 at 0.4.0 (weak duality supplied its dual witness) and is
#: inside C22 at 1.0.0, where Assumption ass:lmo (c) records that "its
#: acceptance half is DISCHARGED, not assumed" and Eq. eq:bacc-def is what
#: discharges it. The polytope minimum an oracle must return, the singleton
#: agreement, the empty-set refusal and the dual bound are all statements about
#: THAT minimization, and every one of them is still true and still needed.
REPOINT_AT_RUN_B_1_0_0: tuple[
    tuple[str, tuple[str, ...], tuple[str, ...], str], ...
] = (
    (
        "O-BETA-ACC",
        ("C19",),
        ("C22",),
        "It pins the DUAL bound of Eq. eq:bacc-def -- the number -<b,u> - v "
        "that an admissible (u, v) certifies. Eq. eq:bacc-def is IN "
        "rem:acc-side at 1.0.0 and is what the bracket consumes where the "
        "acceptance-side minimum is not attained (interface.yaml OC-8). The "
        "bound and its witness are unchanged; only the claim that owns them "
        "moved.",
    ),
    (
        "O-POLYTOPE-ACC-MINIMUM",
        ("C19",),
        ("C22",),
        "It pins the PRIMAL LP minimum min <g, q'> over a declared polytope -- "
        "'the quantity on the right of Eq. eq:bacc-def, which is what a linear "
        "minimization oracle over the acceptance set must return and what no "
        "beta_acc may exceed'. At 1.0.0 that is the FIRST inequality of "
        "Eq. eq:lmo, and rem:acc-side solves it EXACTLY over the rationals in "
        "geometry (b). The entry becomes MORE load-bearing, not less: it is "
        "what the discharged half of A-LMO is checked against.",
    ),
    (
        "O-POLYTOPE-SINGLETON-AGREEMENT",
        ("C19",),
        ("C22",),
        "The singleton geometry of rem:acc-side (a), unchanged at 1.0.0 and "
        "named there as the geometry in which 'the minimum is the single "
        "evaluation, attained at v_t = q^*'. It is also the geometry every toy "
        "in this registry declares, which is why the acceptance term of every "
        "Group 10 bracket vanishes.",
    ),
    (
        "O-POLYTOPE-EMPTY-FAIL-CLOSED",
        ("C8", "C13", "C19"),
        ("C8", "C22"),
        "An empty acceptance set. C8 stays; C13 goes; C19 becomes C22. The "
        "1.0.0 statement of the same case is Lemma lem:fo-khyp (i), which "
        "handles it explicitly: 'Chat_acc is empty, (H-POS) is unsatisfiable so "
        "the iterate index set is empty and no h_lb is reported, h_low = +inf "
        "as an infimum over an empty set, and Theorem thm:accumulated-entropy's hypothesis "
        "Pr[Omega_AT] > 0 fails, so no key length is claimed'. The verdict is "
        "the same and the contract now derives it.",
    ),
    (
        "O-ASSURANCE-ESTIMATE",
        ("C13",),
        ("C22",),
        "Its subject is the REGISTRY's own evidential tier -- every entry "
        "carries assurance = estimate, and agreement with an oracle is never "
        "one of the runtime checks that produce a stronger label. It named C13 "
        "because C13 was the claim that made a stronger label reachable; at "
        "1.0.0 that claim is C22. The statement is unchanged and is if "
        "anything easier to state, the runtime checks now being per-iterate "
        "hypotheses rather than four check groups.",
    ),
    (
        "O-OPTOL-ASSURANCE-FORCED-ESTIMATE",
        ("C13", "C21"),
        ("C21", "C22"),
        "The FORCED downgrade of Remark rem:optol-interface (4): on the "
        "tolerance branch the assurance is `estimate` with "
        "declared_operator_tolerance_open REGARDLESS of the requested "
        "assurance. The rule is UNCHANGED at 1.0.0 and its object is now the "
        "first-order label rather than the certified one -- the contract's "
        "wording moves from '`certified` is a statement about a key rate' to "
        "'an assurance label is a statement about a key rate', which is the "
        "same rule stated of whatever the stronger label is.",
    ),
)


SUPERSEDED_BY_1_0_0: tuple[Supersession, ...] = (
    Supersession(
        name="SPEC_VERSION_0_5_0",
        table="MATHEMATICAL_SPEC_VERSION_0_5_0",
        module="registry, dummy_bundles, tests.support.mode_bundles",
        kind="superseded",
        superseded_by="1.0.0",
        contract_site=(
            "Section 2.5, artifact_bindings bullet; STATUS.yaml "
            "contract_version 1.0.0; gates.g3"
        ),
        reason=(
            "IT NAMES A CONTRACT THAT IS NO LONGER THE ACCEPTED ONE. "
            "contract.tex Section 2.5 fixes artifact_bindings."
            "mathematical_spec_version as the string "
            "meat-core@<contract_version> OF THE ACCEPTED CONTRACT, and 0.5.0 "
            "was superseded at the 1.0.0 G3, so every artifact declaring it is "
            "one a 1.0.0 consumer must refuse. THE MARK IS THE STRING AND NOT "
            "AN IDENTIFIER, for the reason the 0.5.0 band gave when it marked "
            "the 0.4.0 string: the tree holds more than one place that pins it "
            "independently, and marking the VALUE catches all of them and "
            "shrinks by itself as each is retyped. NO NUMBER IN ANY BUNDLE "
            "CHANGES: by Theorem thm:optol (i) every toy in this registry is "
            "exactly admissible -- every declared POVM block is a non-negative "
            "DYADIC real and every declared-order sum is exact, so condition "
            "(S) holds of each (S-DYADIC-HALVES) -- and carries the 0.5.0 "
            "reading verbatim. What is invalidated is the one string."
        ),
        replacement=("MATHEMATICAL_SPEC_VERSION_1_0_0",),
        scan_pattern="meat-core@0.5.0",
    ),
    Supersession(
        name="ASSURANCE_VALUES",
        table="ASSURANCE_VALUES",
        module="registry",
        kind="superseded",
        superseded_by="1.0.0",
        contract_site=(
            "Section 2.2 (the optimizer_certificate and reported_tier rows); "
            "Section 2.4 (requested_assurance); Section 2.5 "
            "(assurance_ladder); ARCHITECTURE_SPEC.md Section 3.8"
        ),
        reason=(
            "ITS SECOND VALUE IS A SHELVED NAME. The tuple reads "
            "('estimate', 'certified') and states that "
            "optimizer_certificate.assurance takes EXACTLY those two values. "
            "At 1.0.0 the values are ('estimate', 'first-order'): `certified` "
            "was shelved with the numerical lower-bound "
            "certificate, IS NEVER EMITTED, and a requested_assurance naming "
            "it is REFUSED with assurance_tier_not_available rather than "
            "demoted. The 0.5.0 band's NOT_SUPERSEDED_BY_0_5_0 recorded this "
            "tuple as correct at that version -- '0.5.0 adds a further ROUTE "
            "to estimate, not a third value' -- and that reading was right "
            "then; 1.0.0 changes the value SET and not a route, so the tuple "
            "is now false. ASSURANCE_VALUES_1_0_0 replaces it."
        ),
        replacement=("ASSURANCE_VALUES_1_0_0", "O-FO-LADDER"),
        scan_pattern="ASSURANCE_VALUES",
    ),
    Supersession(
        name="OPTOL_DOMAIN_CASES absent-tolerance rows",
        table="OPTOL_DOMAIN_CASES",
        module="registry",
        kind="superseded",
        superseded_by="1.0.0",
        contract_site=(
            "Section 2.1 (the declared_tolerance row); Remark "
            "rem:optol-interface (1); Assumption ass:dtol"
        ),
        reason=(
            "THE ABSENT CASE IS NO LONGER A ZERO, IT IS A REFUSAL. Group 9 "
            "freezes the 0.5.0 reading in pairs -- DOM-absent beside DOM-zero, "
            "AD-EXACT-absent beside AD-EXACT-zero, AD-SUBC-absent beside "
            "AD-SUBC-zero -- each pair asserting that an ABSENT declaration "
            "decides identically to a declared 0. AT 1.0.0 tau_num IS REQUIRED: "
            "'there is no default and no fallback anywhere in this contract or "
            "in any artifact derived from it, and a request omitting it is "
            "refused' with declared_tolerance_absent, BEFORE ANYTHING IS "
            "CONSTRUCTED. THE `zero` HALF OF EACH PAIR STANDS VERBATIM -- "
            "lem:optol-zero is untouched and tau_num = 0 is still 'the exact "
            "reading' -- and only the `absent` half is superseded. The mark is "
            "therefore on the ROWS and not on the table: run B retires the "
            "absent rows and keeps the zero rows, and "
            "O-DECLARED-TOLERANCE-REQUIRED is what replaces them."
        ),
        replacement=("O-DECLARED-TOLERANCE-REQUIRED",),
        scan_pattern="DOM-absent",
    ),
    Supersession(
        name="OPTOL-BLOCK admission rows (reason=None)",
        table="OPTOL_ADMISSION_CASES",
        module="registry",
        kind="superseded",
        superseded_by="1.0.0",
        contract_site=(
            "Definition def:optol condition (T); Remark rem:optol-reach (a); "
            "Remark rem:optol-interface (2); Section 2.5 (operator_form)"
        ),
        reason=(
            "A (T) FAILURE NOW CARRIES A SPELLED REASON, AND ITS OBJECT NO "
            "LONGER EXISTS. The 0.5.0 freeze recorded, in "
            "CHANGE_REQUEST_CANDIDATES_0_5_0's first entry, the reading that a "
            "failure of (T) 'carries NONE of the six and travels the "
            "version-0.4.0 malformed-declaration path', and froze OPTOL-BLOCK "
            "with reason=None in its three admission cases. TWO THINGS CHANGE "
            "AT 1.0.0. The reason is SPELLED: sector_map_disagreement, refused "
            "at every tau_num. And the FAMILY ITSELF is no longer expressible: "
            "a declared operator arrives as a list of sector blocks plus the "
            "sector map, so 'an off-block entry is ABSENT FROM THE DATUM rather "
            "than small in it -- nothing can write one, nothing verifies that "
            "none was written'. OPTOL-BLOCK carries an off-block entry, which "
            "1.0.0's representation cannot hold. THE VERDICT IS UNCHANGED "
            "(refused, at every tau_num) AND THE MECHANISM IS NOT."
        ),
        replacement=("O-SECTOR-MAP-DISAGREEMENT",),
        scan_pattern="OPTOL-BLOCK",
    ),
    Supersession(
        name="OPTOL_REASON_VOCABULARY",
        table="OPTOL_REASON_VOCABULARY",
        module="registry",
        kind="superseded",
        superseded_by="1.0.0",
        contract_site=(
            "Sections 2.1, 2.2, 2.4, 2.6; Remark rem:optol-interface (1)-(4); "
            "Remarks rem:fo-interface, rem:fo-negative-values"
        ),
        reason=(
            "IT IS A CLOSED LIST AND 1.0.0 OPENS IT. The tuple is the SIX "
            "strings contract.tex 0.5.0 spells and asserts that they are the "
            "vocabulary. At 1.0.0 there are SEVENTEEN: eleven are new "
            "(sector_map_disagreement, bob_povm_summation_rounds, "
            "declared_tolerance_absent, choi_isometry_inexact, "
            "negative_objective, assurance_tier_not_available and the five "
            "withdrawal reasons of rem:fo-interface), and ONE OF THE SIX "
            "IS RENAMED WITH ITS DATUM -- operator_tolerance_out_of_domain "
            "becomes declared_tolerance_out_of_domain. THE OTHER FIVE SURVIVE "
            "CHARACTER FOR CHARACTER and their meanings are unchanged. "
            "REASON_VOCABULARY_1_0_0 replaces the tuple; RENAMED_REASON_1_0_0 "
            "carries the one rename so that the change is auditable as a "
            "rename rather than as a deletion plus an addition."
        ),
        replacement=("REASON_VOCABULARY_1_0_0", "RENAMED_REASON_1_0_0"),
        scan_pattern="OPTOL_REASON_VOCABULARY",
    ),
)


#: The completeness half of the 1.0.0 list: objects a reader would EXPECT to be
#: marked, with the reason each is not. Recording the absences is part of the
#: list being complete -- an unmarked object is a decision, not an oversight.
NOT_SUPERSEDED_BY_1_0_0: tuple[tuple[str, str], ...] = (
    (
        "Every h_low, key length, alpha-limit and polytope VALUE in Groups 1-6 and 8",
        "THEOREM thm:optol (i), unchanged in substance at 1.0.0 and now "
        "carrying condition (S) as well: on an exactly admissible declaration "
        "'every claim of this contract -- C1-C12, C14-C17, C22 -- applies to "
        "the declared numbers EXACTLY AS IT IS STATED. The declared tau_num "
        "changes no statement, no bound and no number.' Every toy declaration "
        "in this registry declares its POVM blockwise as non-negative DYADIC "
        "reals summing to one per sector, so each satisfies (S) as well as the "
        "three defect conditions and every frozen value is a branch-(i) value. "
        "S-DYADIC-HALVES makes the (S) half falsifiable rather than asserted, "
        "on TOY-1's own s0 block. (Three Group 8 entries are REPOINTED, which "
        "changes a claim tuple and no value.)",
    ),
    (
        "ALL_TOYS, SOURCE_MODE_TOYS and every declaration in them",
        "Not one operator changes and not one becomes inadmissible. tau_num is "
        "'a datum of the REQUEST, not a component of the declaration: "
        "Definition def:declaration is UNCHANGED', so no toy gains, loses or "
        "re-types a field. TWO 1.0.0 CHANGES COULD HAVE TOUCHED THEM AND DO "
        "NOT. The tagged constraint form of def:homog re-types a DECLARED "
        "FIELD, but every toy carrying a constraint already declares both an "
        "operator bound and a homogeneous_scalar, so the tag is READ OFF what "
        "is there: TOY-5 and TOY-6 carry homogeneous_scalar = 1/2 and are "
        "`homogeneous`; TOY-7 carries None and an operator bound and is "
        "`general` (O-GENERAL-TAG-NOT-LICENSED). And the block representation "
        "of Section 2.5 is what toy_declarations already uses -- bob_povm is "
        "`v -> sector -> block` and has been since the 0.3.0 freeze.",
    ),
    (
        "CERTIFICATE_TOYS",
        "They are DECLARATIONS, not certificate values: each is a well-formed "
        "protocol declaration that the certificate band happened to be the "
        "first to use, and h_low on any of them would still be correct. They "
        "become unreferenced once the marked entries are retired, which is a "
        "matter for run B's file hygiene and not a supersession.",
    ),
    (
        "O-HLOW-INFINITE",
        "Its subject is 'h_low = +inf must be propagated, never clamped, and "
        "NO key-length claim may be emitted WHEN IT IS REACHED' -- a "
        "sufficient condition, not a claim to enumerate every ground for an "
        "absent key_length. 1.0.0 makes the grounds THREE rather than two "
        "(h_lb absent; the tolerance branch; h_low = +inf) and Section 2.2's "
        "key_length row names all three. None implies another and none "
        "invalidates this entry; interface.yaml's key_length row carries the "
        "grounds_note that keeps them apart.",
    ),
    (
        "O-CONSTRAINT-GATE, O-CGATE-DEGENERATE and the two-part security gate",
        "The gate's TWO PARTS are unchanged and so is its verdict on every "
        "toy. What 1.0.0 changes is how part (i) is DECIDED -- a type check on "
        "the declared tag instead of a numerical test -- and "
        "O-GENERAL-TAG-NOT-LICENSED records that change against TOY-7 without "
        "disturbing either entry's reasoning. O-CGATE-DEGENERATE in "
        "particular stands: at d_A = 1 part (i) degenerates under either "
        "mechanism -- the numerical test could fail no 1x1 entry, and the type "
        "check rejects only a `general` tag a producer can avoid (rem:cgate). "
        "[Aligned with the owner's reading of the gate at "
        "d_A = 1; no "
        "verdict moved. This row previously read: 'at d_A = 1 part (i) is "
        "vacuously true under either mechanism'.]",
    ),
    (
        "O-MARGINAL-INADMISSIBLE and every tau_A verdict",
        "Remark rem:optol-reach (c) still places the marginal OUTSIDE the "
        "tolerance's reach, and 1.0.0 makes it STRICTER rather than looser: "
        "tau_A >= 0 and tr tau_A = 1 are decided exactly AND the trace must be "
        "summed without rounding. Every frozen verdict stands at every "
        "tolerance and none of them turns on a window: tau_A = 0 is refused, "
        "`none` and I/d_A and a singular nonzero tau_A are accepted. The new "
        "round-nowhere clause could only refuse MORE, and no frozen tau_A is a "
        "family whose trace sum rounds -- each is diagonal with dyadic entries.",
    ),
    (
        "O-CHOI-BASIS-INVARIANCE and TOY-9's two coordinate matrices",
        "Remark rem:basis-invariance is unchanged and is if anything more "
        "load-bearing at 1.0.0: with rank tau_A no longer computed, the frame "
        "is whichever construction the implementation used, and the invariance "
        "of h_low, key_length and sector_report under that choice is what "
        "makes the choice free. The entry freezes a closed-form h_low and two "
        "HAND-AUTHORED Choi coordinate matrices whose relation is the remark's "
        "content; neither is a rank decision.",
    ),
    (
        "O-GRADIENT-FACE-SPLIT",
        "Its subject is Theorem thm:gradient (i)'s SPLIT face rule, and 1.0.0 "
        "does not touch that theorem's statement -- it removes the OTHER "
        "consumer of the gradient, the certificate chain, which evaluated it "
        "only at strictly positive perturbed operators. So the face rules go "
        "from being one path's concern among two to being the only reading of "
        "C12 the contract has, WHICH MAKES THIS ENTRY MORE CENTRAL RATHER THAN "
        "SUPERSEDED: C22's (H-SUPP) is stated on exactly the condition it "
        "freezes, and Lemma lem:fo-face is what makes the +infinity case "
        "unreachable.",
    ),
    (
        "OPTOL_FAMILIES and the (H)/(P)/(C) admission cases of Group 9",
        "The three defects of Eq. eq:defects and the three windows they are "
        "compared against are unchanged in SUBSTANCE at 1.0.0. What changes is "
        "the NORM -- entrywise maximum modulus per block instead of the "
        "operator norm, with positivity still a spectral floor -- and EVERY "
        "GROUP 9 FAMILY IS BLOCK-DIAGONAL WITH 1x1 BLOCKS, WHERE THE TWO NORMS "
        "COINCIDE (for a 1x1 matrix ||X||_max = ||X|| = |x|). So no frozen "
        "defect value moves. The boundary pairs, the equality-admits reading "
        "and the three refusal reasons all stand.",
    ),
    (
        "OPTOL_WITNESS_CASES and the lem:nearpovm bracket",
        "Both halves of the lemma survive and both gain a hypothesis they "
        "already needed: (S), which the 0.5.0 freeze noted as quarantined for "
        "itself in the forward half and which 1.0.0 discharges for every "
        "admitted declaration through the admission rule. The forward constant "
        "gains a d_max factor from the norm change -- eps_star = "
        "(1/2) d_max Delta_herm + Delta_pos + theta(1+theta)/(1-theta) with "
        "theta = d_max Delta_cpl + |V| Delta_pos -- AND EVERY FROZEN WITNESS "
        "CASE HAS d_max = 1, so no frozen number moves. The converse gains no "
        "factor at all, every step going from the operator norm DOWN to the "
        "entrywise maximum modulus. S-CONVERSE-2^-53 and S-EXACT-NEIGHBOUR add "
        "the (S) hypothesis's witness beside them.",
    ),
    (
        "OPTOL_NOBOUND_CASES and prop:optol-nobound",
        "The proposition and its two parts are unchanged in direction and "
        "SHARPENED in scale: 1.0.0 states the bound it rules out as ruled out "
        "'at any scale a key-length claim could use', exhibiting instances "
        "forcing more than (alpha/(alpha-1)) N bits per round with N up to 52 "
        "under the number model, and adds one HYPOTHESIS to the reversal "
        "clause of part (ii) -- c a multiple of 2^-52. Both frozen cases have "
        "c dyadic, so the added hypothesis holds of them and no verdict moves.",
    ),
    (
        "reference.py's evaluators, including the 0.5.0 defect functions",
        "Every one computes a quantity of the surviving sections on numbers "
        "the caller supplies, and none validates a declaration or decides an "
        "admission. The defect functions measure in the OPERATOR NORM, which "
        "1.0.0 replaces with the entrywise maximum modulus for Delta_herm and "
        "Delta_cpl -- but they are NAMED operator_norm, hermiticity_defects, "
        "completeness_defect and they compute what they are named after, so "
        "they are not false; run B adds the entrywise measurements beside "
        "them, as the 0.5.0 band added these beside psd_trace_power. THE "
        "FROZEN VALUES DO NOT MOVE, every Group 9 block being 1x1.",
    ),
    (
        "The alpha grid and CERT_ALPHA_INTEGER_BETA",
        "The grid is unchanged and every Group 10 and 11 alpha is on it. "
        "CERT_ALPHA_INTEGER_BETA = 2.0 is a Renyi order OUTSIDE the key-length "
        "domain, admitted by A-ALPHA for the claims stated on (1, inf), and "
        "its only consumers are marked entries. It becomes UNREFERENCED when "
        "they are retired, which is file hygiene rather than supersession -- "
        "the constant says something true about A-ALPHA either way.",
    ),
)


def is_superseded_by_scope(oracle_id: str) -> bool:
    """Whether 1.0.0 removed this entry's SUBJECT from the module's scope."""
    return any(name == oracle_id for name, _ in SUPERSEDED_BY_SCOPE_1_0_0)


def repointing(oracle_id: str) -> tuple[str, ...] | None:
    """Return the 1.0.0 claim tuple for a repointed entry, or ``None``."""
    for name, _old, new, _reason in REPOINT_AT_RUN_B_1_0_0:
        if name == oracle_id:
            return new
    return None


def claims_at_1_0_0(entry: OracleEntry) -> tuple[str, ...]:
    """Return the claim IDs ``entry`` pins under contract 1.0.0.

    The entry's own tuple, unless 1.0.0 repointed it; a marked-by-scope entry
    keeps its tuple, which is why the integrity check exempts it by name rather
    than by rewriting it.
    """
    return repointing(entry.oracle_id) or entry.claims


ORACLES: tuple[OracleEntry, ...] = (
    O_K_IDENTITY,
    O_K_RANGE,
    O_DEFICIT_SIGN,
    O_SECTOR_DECOMPOSITION,
    O_TRACE_SPLIT,
    O_BRANCH_ENTROPY,
    O_HLOW_DEPHASED,
    O_HLOW_DETERMINISTIC,
    O_HLOW_ZERO_GENERATION,
    O_HLOW_RETENTION,
    O_HLOW_NO_AVERAGING,
    O_HLOW_CONSTRAINED,
    O_HLOW_REMOVAL,
    O_HLOW_DIVERGENCE_ONLY,
    O_ALPHA_LIMIT,
    O_ALPHA_LIMIT_HYPOTHESIS_FAILS,
    O_KEY_LENGTH,
    O_KEY_LENGTH_MONOTONE,
    O_KEY_LENGTH_EPS_TO_ZERO,
    O_KEY_LENGTH_LARGE_N,
    O_KEY_LENGTH_ACCEPTANCE_INDEPENDENT,
    O_HLOW_INFINITE,
    O_CONSTRAINT_GATE,
    O_ASSURANCE_ESTIMATE,
    O_KERNEL_CONVENTIONS,
    O_CONVEXITY,
    O_SOURCE_MODE_DERIVED,
    O_MARGINAL_INADMISSIBLE,
    O_MODE_EQUIVALENCE_DA1,
    O_UNTRUSTED_CONSERVATIVE,
    O_UNTRUSTED_SCALAR_CLASS,
    O_CGATE_DEGENERATE,
    O_SOURCE_LICENSE_GATE,
    O_PARTY_COMPUTABILITY,
    O_CHOI_BASIS_INVARIANCE,
    O_GRADIENT_FACE_SPLIT,
    # Group 7 -- the 0.4.0 certificate chain.
    O_SERIES_TAILS,
    O_LOG_TAIL,
    O_TRANSFER_BOUNDS,
    O_SQRT_RESIDUAL,
    O_MIX_DOMINATION,
    O_SPECTRAL_WINDOW,
    O_WEAK_DUALITY,
    O_BETA_ACC,
    O_EULER_IDENTITY,
    O_HCERT_END_TO_END,
    O_CERT_KEY_LENGTH,
    O_CERT_DOMAIN_FAIL,
    O_CERT_HYPOTHESES_FAIL,
    O_DUAL_SLACK_NOT_PSD,
    O_ACC_SIDE_UNSUPPORTED,
    O_ASSURANCE_CERTIFIED_GATE,
    # Group 8 -- the polytope acceptance oracle. A
    # later band under the SAME accepted contract 0.4.0; Groups 1-7 above are
    # unedited.
    O_POLYTOPE_ACC_MINIMUM,
    O_POLYTOPE_SINGLETON_AGREEMENT,
    O_POLYTOPE_EMPTY_FAIL_CLOSED,
    # Group 9 -- the 0.5.0 declared operator tolerance (C21). Authored in the
    # scoped implementation band the accepted amendment opens, by the run-A
    # instance, before any source file supporting a declared tolerance
    # existed. Groups 1-8 above are UNEDITED except for the single
    # `superseded_by` mark on O-ASSURANCE-CERTIFIED-GATE.
    O_OPTOL_DEFECTS,
    O_OPTOL_ADMISSION,
    O_OPTOL_DOMAIN,
    O_OPTOL_EXACT_UNCHANGED,
    O_OPTOL_NOT_EVALUABLE,
    O_OPTOL_EXPLORATION,
    O_OPTOL_ASSURANCE_FORCED_ESTIMATE,
    O_OPTOL_HCERT_NO_CLAIM,
    O_OPTOL_REPORT,
    O_OPTOL_WITNESS,
    O_OPTOL_NO_ROBUSTNESS,
    O_OPTOL_UNDECLARED_CONSTANT,
    O_OPTOL_REACH,
    # Group 10 -- the 1.0.0 first-order rung (C22). Authored in the
    # implementation band the accepted MAJOR amendment opens, by the run-A
    # instance, before any source file supporting a first-order rung existed.
    # Groups 1-9 above are UNEDITED by this band: the marks 1.0.0 places are
    # carried in SUPERSEDED_BY_SCOPE_1_0_0, REPOINT_AT_RUN_B_1_0_0 and
    # SUPERSEDED_BY_1_0_0, not in any entry's fields.
    O_FO_BRACKET_SINGLETON,
    O_FO_BRACKET_KEY_INERT,
    O_FO_BRACKET_UNCONSTRAINED,
    O_FO_BRACKET_CONSTRAINED,
    O_FO_KEY_LENGTH,
    O_FO_WITHDRAWAL,
    O_FO_NEGATIVE_OBJECTIVE,
    O_FO_LADDER,
    # Group 11 -- the 1.0.0 admission surface (C21 as amended).
    O_DECLARED_TOLERANCE_REQUIRED,
    O_BOB_POVM_SUMMATION_ROUNDS,
    O_SECTOR_MAP_DISAGREEMENT,
    O_GENERAL_TAG_NOT_LICENSED,
    O_ALICE_EXACT_ORDER,
)


def oracle(oracle_id: str) -> OracleEntry:
    """Return the registry entry with the given ``oracle_id``."""
    for entry in ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no oracle entry {oracle_id!r}")


# ===========================================================================
#  RUN B'S MARKS -- band B1 of the meat-core 1.0.0 band
# ===========================================================================
#
#  NOTHING ABOVE THIS LINE IS EDITED, MOVED OR DELETED. Everything run B has
#  to say about a frozen object is said HERE, in a list beside it, which is the
#  form the 0.5.0 band established and the two-instance freeze requires: "a
#  list composes where a field does not". That includes the two INVENTORY rows
#  of PENDING_RETIREMENT_AT_RUN_B whose files run B deleted -- run B removed
#  them at first, and restoring them is the correction: the freeze forbids a
#  deletion inside a frozen file EVEN OF AN INVENTORY ROW, because a row that
#  is gone cannot be read as having been disposed of deliberately.


#: THE TWO PENDING-RETIREMENT ROWS WHOSE FILES ARE GONE, marked rather than
#: removed. Each names a (file, marked-object) pair of
#: PENDING_RETIREMENT_AT_RUN_B whose FILE band B1 deleted with the certificate
#: chain; the row therefore names a file that no longer exists, which is a
#: disposal and not a defect.
#:
#: GROUND, stated once for both: band B1 of the meat-core
#: 1.0.0 implementation band. Decision D3 of the number model shelved the
#: `certified` rung (ARCHITECTURE_SPEC.md Section 3.8;
#: FUTURE_SCOPE.md Section 3), and contract.tex 1.0.0 deletes C13 and C18-C20
#: together with Assumption A-IA, so the certificate test files these rows
#: pointed at have no subject. THE PAIRS ARE NOT WITHDRAWN AS EVIDENCE: each
#: records that a run-B file DID name a superseded 0.4.0 object at the freeze,
#: which is what the hand-off invariant was for, and each is now discharged by
#: the file's deletion rather than by a rewrite.
PENDING_ROWS_SUPERSEDED_BY_SCOPE_1_0_0: tuple[tuple[str, str, str], ...] = (
    (
        "tests/oracles/test_certificate.py",
        "O-ASSURANCE-CERTIFIED-GATE",
        "the file is deleted with the certificate band (C13, C18-C20 and "
        "Assumption A-IA); the pair is discharged by the deletion, and the row "
        "stands as the record that it existed at the freeze",
    ),
    (
        "tests/golden/test_certificate_against_registry.py",
        "O-ASSURANCE-CERTIFIED-GATE",
        "the same, for the golden half of the certificate suite: the file is "
        "deleted with the certificate band, the pair is discharged by the "
        "deletion, and the row stands as the record that it existed at the "
        "freeze",
    ),
)


#: A CORRECTION BESIDE run A's NOT_SUPERSEDED_BY_1_0_0 row for Group 9,
#: and it corrects the row's GROUND and one of its consequences. RUN A'S TEXT
#: IS NOT REWRITTEN: it stands above, in full, and this entry stands beside it,
#: because a mark that erased the sentence it corrects would take with it the
#: record of what was believed.
#:
#: WHAT RUN A WROTE: "EVERY GROUP 9 FAMILY IS BLOCK-DIAGONAL WITH 1x1 BLOCKS,
#: WHERE THE TWO NORMS COINCIDE (for a 1x1 matrix ||X||_max = ||X|| = |x|). So
#: no frozen defect value moves."
#:
#: WHAT IS WRONG WITH IT. THE PREMISE IS FALSE FOR THREE FAMILIES:
#: OPTOL-2D-COMP, OPTOL-2D-NEG and OPTOL-2D-HERM each declare
#: `sector_dims = (2,)` -- ONE 2x2 BLOCK, not two 1x1 ones. The CONCLUSION then
#: fails for exactly one number.
#:
#: THE DERIVATION, so that the correction is checkable rather than asserted.
#: OPTOL-2D-COMP's completeness residual is (1/8) J_2, the all-ones 2x2 matrix
#: scaled by 1/8. Its ENTRYWISE MAXIMUM MODULUS is 1/8. Its OPERATOR NORM is
#: 2 * 1/8 = 1/4, J_2 having eigenvalues 0 and 2. So Eq. eq:normconv's
#: inequality ||X|| <= d ||X||_max is an EQUALITY here at d = 2, and the frozen
#: delta_cpl = 1/4 is the OPERATOR-NORM reading while 1.0.0's Definition
#: def:optol asks for the ENTRYWISE one, 1/8.
#:
#: THE REGISTRY ITSELF SAYS SO, WHICH IS WHY THIS IS A CORRECTION AND NOT A
#: DISCOVERY. REPORT-2DCOMP-boundary's own derivation reads: "an implementation
#: reporting a componentwise maximum reports 1/8 and passes every case in this
#: table except this one." The 0.5.0 freeze MADE THAT ROW THE DISCRIMINATOR
#: between the two norms, and 1.0.0 chose the componentwise side of it. The row
#: is superseded BY THE CONTRACT'S OWN NORM CHOICE.
#:
#: THE OTHER TWO 2x2 FAMILIES DO NOT MOVE, each for its own reason:
#: OPTOL-2D-NEG's delta_pos is a SPECTRAL FLOOR, which 1.0.0 leaves in the
#: spectrum ("positivity is the exception"); OPTOL-2D-HERM's anti-Hermitian
#: part is an off-diagonal pair whose entrywise maximum and operator norm are
#: both 1/4.
#:
#: NOTHING FROZEN IS EDITED BY THIS ENTRY. The three affected rows are listed
#: below as superseded-by-scope; their values stand where they are, and
#: tests/golden/test_operator_tolerance_against_registry.py asserts BOTH
#: readings with the factor exhibited, so neither is silently substituted for
#: the other.
NOT_SUPERSEDED_CORRECTION_1_0_0: str = (
    "Band B1 of the meat-core 1.0.0 implementation band. The "
    "NOT_SUPERSEDED_BY_1_0_0 row headed 'OPTOL_FAMILIES and the (H)/(P)/(C) "
    "admission cases of Group 9' rests on a FALSE PREMISE -- three Group 9 "
    "families declare one 2x2 block, not two 1x1 blocks -- and its conclusion "
    "that 'no frozen defect value moves' fails for exactly one number: "
    "OPTOL-2D-COMP's delta_cpl is 1/4 in the operator norm and 1/8 in the "
    "entrywise maximum modulus that Definition def:optol fixes at 1.0.0, the "
    "two related by Eq. eq:normconv's factor d = 2 as an EQUALITY. Run A's "
    "text is not rewritten; the three rows it affects are marked below."
)


#: THE THREE FROZEN ROWS THE 1.0.0 NORM CHANGE SUPERSEDES, which run A's
#: NOT_SUPERSEDED row missed. Marked, not re-derived and not deleted -- the
#: same disposition CERTIFICATE_SUPERSESSION_LINE licenses for the certificate
#: group, and for the same reason: the values are not withdrawn as mathematics,
#: each having been derived on paper in the operator norm and each carrying
#: that derivation; what is withdrawn is the claim that they are what a 1.0.0
#: run measures.
NORM_CHANGE_SUPERSEDED_1_0_0: tuple[tuple[str, str], ...] = (
    (
        "OPTOL_FAMILIES: OPTOL-2D-COMP.delta_cpl",
        "1/4 is the OPERATOR-NORM value of the residual (1/8) J_2; Definition "
        "def:optol at 1.0.0 measures the ENTRYWISE MAXIMUM MODULUS PER SECTOR "
        "BLOCK, which is 1/8. The family has ONE 2x2 block, so the two norms "
        "do not coincide, and eq:normconv's ||X|| <= d ||X||_max is an "
        "EQUALITY at d = 2",
    ),
    (
        "OPTOL_ADMISSION_CASES: AD-2DC-below",
        "THE ONE FROZEN VERDICT THE NORM CHANGE MOVES, and it moves in the "
        "ADMITTING direction because the entrywise defect is SMALLER: at "
        "tau_num = 1/8 the frozen row refuses OPTOL-2D-COMP with "
        "bob_povm_completeness_defect on delta_cpl = 1/4, and 1.0.0 ADMITS it "
        "on delta_cpl = 1/8, Definition def:optol writing (C) NON-STRICTLY so "
        "the boundary admits. Branch (iii): admitted, no key length",
    ),
    (
        "OPTOL_REPORT_CASES: REPORT-2DCOMP-boundary",
        "The row the 0.5.0 freeze MADE THE NORM DISCRIMINATOR -- its own "
        "derivation reads 'an implementation reporting a componentwise maximum "
        "reports 1/8 and passes every case in this table except this one' -- "
        "and 1.0.0 chose the componentwise side. Superseded by the contract's "
        "own norm choice and by nothing this run decided",
    ),
)


def pending_row_superseded(relative: str, name: str) -> bool:
    """Whether a PENDING_RETIREMENT_AT_RUN_B pair is discharged by a deletion."""
    return any(
        relative == row and name == marked
        for row, marked, _ in PENDING_ROWS_SUPERSEDED_BY_SCOPE_1_0_0
    )
