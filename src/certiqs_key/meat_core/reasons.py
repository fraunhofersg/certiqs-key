"""The machine vocabulary of this module: refusals, withdrawals, assumptions.

ONE REASONS MODULE, in the shape of
:mod:`certiqs_key.protocol_compiler.reasons`. The withdrawal and refusal
strings and the assumption ledger live together, because a reader auditing
what a run record says it rests on should find the enum, the machine keys and
the strings in one file.

THE REFUSAL STRINGS ARE THE INTERFACE'S
=======================================
spec/modules/meat-core/interface.yaml's ``refusal_reasons`` lists EIGHT
strings, four of them the core's and four the submodule's, and ONE spelling of
its own.

The core's: ``sector_map_disagreement``, ``bob_povm_summation_rounds``,
``choi_isometry_inexact``, ``negative_objective``. The submodule's: the four
withdrawal strings of :class:`AssuranceReason`. A fifth, ``oracle_not_optimal``,
is not emitted (it went with A-LMO): no bracket reads the oracle's return or
status, the feasible side being verified without them
(``frank-wolfe/req:verified-feasible-side``), so no status withdraws one.

The interface's own spelling: ``declaration_not_exactly_admissible``.
``def:declaration`` requires the refusal -- a declaration is exactly admissible
or it is refused -- and spells no string; a declared-tolerance apparatus would
have named a MEASURED DEFECT against a tolerance, but no tolerance exists, so
there is ONE name for one exact refusal. IT IS NOT A NEW COINAGE:
spec/modules/reductions/wpfss/interface.yaml already spells it for the same
decision on the same kind of datum.

ONE STRING IS IN NEITHER LIST ABOVE: ``security_statement_vacuous``, the named
reason of the corner gate. It refuses ``eps_PA + eps_EV + 2 eps_auth >= 1``
(the two-budget rule at the default ``eps_auth = 0``), where the security
statement a key length would be reported under is empty, and it names that
state rather than reporting a length there. Its interface row and this file
are the two sides of the same gate and are checked against each other by
``tests/oracles/test_meat_core_registry_interface.py``.

NINE SPELLINGS ARE NOT EMITTED and are named in :data:`RETIRED_REFUSAL_REASONS`
so that a record carrying one finds it disposed of rather than missing. Seven
belong to a declared-tolerance apparatus that does not exist, one to a
``requested_assurance`` row that does not exist and one to A-LMO. NONE IS
REUSED AND NONE IS RESPELLED.

A WITHDRAWAL IS NOT A REFUSAL
=============================
:class:`AssuranceReason` names why ``h_lb`` -- the first-order bracket of
``frank-wolfe/thm:firstorder`` -- was WITHDRAWN, on a result that EXISTS;
:class:`RefusalReason` names a refusal that produces NO OUTPUT AT ALL. The two
must stay distinguishable, and WITHDRAWAL IS NEVER A WEAKENING
(``frank-wolfe/rem:fo-interface``): there is no reduced form of the claim.
A run whose bracket is withdrawn reports the estimate and says which hypothesis
failed; it does not report a smaller ``h_lb`` or a hedged one.

THE LEDGER IS THE INTERFACE'S ``assumption_ledger``
===================================================
:class:`AssumptionId` carries THE ASSUMPTIONS THIS MODULE OWNS. Short ids are
repository-wide, so an assumption another module owns is read off that module
and is not a member of the enum:

* ``A-SRC`` is ``transmitter/ass:src``, ``A-TSM`` is ``reductions/ass:tsm``,
  ``A-ROUNDHOM`` is ``protocol-compiler/ass:rhom`` (A-RHOM), and the
  authenticated-and-licensed attacker assumption is
  ``protocol-compiler/ass:atk`` (A-ATK), under THIS module's id and machine
  key. These four are read off the supplier artefacts and are
  :data:`INHERITED_KEYS` here (and, by their owners' ``verification`` fields,
  :data:`INHERITED_NEVER_VERIFIED_KEYS`) rather than members of the enum,
  because this module does not own them.
* A-DIM belongs to ``reductions`` (a bound on a reduction instance's data
  sectors), and the setting is ``reductions/def:system-setting``.
* A-EVE-DIM (``ass:eve-dim``, machine key ``adversary_registers_finite``) is
  superseded and assumed by no claim: the round model keeps the adversary's
  registers finite-dimensional by definition, at every fixed dimension, and
  ``cor:composed-security``, through ``lem:memory-lift``, carries a run's
  security statement to registers of any dimension. It is no member of the
  enum and no run emits it; the interface keeps its key among the
  ``unemitted_rows`` for the claim-closure table.
* A-SOUND is reductions' soundness assumption, machine key ``constraints_sound`` and
  is not a ledger row: inside the security chain A-ATK implies it
  (``lem:range`` (i)), and that every entry reductions emits is sound for the
  chain is a conclusion of that module's theorems
  (``reductions/rem:sound-and-atk``). The engine emits no row for it.
* A-ALPHA (machine key ``alpha_domain``) is no row: every theorem states its
  own range of the Renyi order, ``rem:alpha-domain`` says why the key-length
  statements take ``(1, 2)``, and what the engine decides is two requirements,
  ``req:key-length-alpha-domain`` and ``req:objective-alpha-domain``. A
  condition the engine decides is not an assumption.

THE KEY-LENGTH PREMISES. ``thm:keylength`` splits into the post-processing
model, the secrecy theorem, the correctness lemma ``lem:ev-correctness`` and
the composition ``cor:composed-security``, which surface premises owned here:
A-SEED (the post-processing seeds), A-FIXED (the parameters fixed before the
run), A-CONFORM (the post-processing run as analysed), A-AUTH (the
authenticated classical channel, binding ``eps_auth`` and ``k_auth``) and
A-LAB (the sealed laboratory, one row per party). With them the transmitter's
A-SEQ is a premise of ``thm:keylength`` and is inherited here by machine key.
Each is emitted "on every run that reports a key length" (the interface's
``emission_rule``), and each is never verified. Two of them, A-SEED and the
laboratory premise, are emitted on every run that reports a first-order bound
as well (:data:`FIRST_ORDER_ROWS`): ``frank-wolfe/thm:firstorder`` rests on
them through ``lem:product-marginal``.

THE COMPILER'S PREMISES OF ``thm:keylength`` ARE NO ROW HERE. The theorem also
assumes A-LINK, whose clauses attest its hypothesis (H-CHAIN), and A-SPEC and
A-ALICE-MEAS, which attest that its run is that of ``lem:memory-lift`` (a)
(the interface's ``a_link_note`` and ``a_spec_note``). The compiler's own
ledger carries them under its presence rules, so a run's route-exact set
(:mod:`certiqs_key.runs.assumptions`) lists them as engaged where that ledger
emits them, and otherwise as not engaged: A-LINK discharged on Band A and
where ``req:link-row-provenance`` omits the row, A-ALICE-MEAS outside its
presence rule.

ONE LABORATORY PREMISE PER PARTY. A-LAB-ALICE and A-LAB-BOB would read "the
sender" and "the only receiver" and so agree with the declaration's two parties
on a prepare-and-measure run only; the premise is therefore ``ass:lab``
(A-LAB, machine key ``laboratory_sealed``), stated for a party P of the
declaration whatever P does in the protocol. Its row is emitted ONCE PER PARTY
and names the party (:data:`PER_PARTY_ROWS`, :func:`laboratory_parties`): at
both parties on a run that reports a key length (``thm:keylength`` assumes it
at each); on a run that reports a first-order bound and no length, only in
trusted-source mode and only at the party the party partition assigns ``A`` to
(the one instance ``thm:accumulated-entropy`` uses); in untrusted-source mode,
with no length, not at all.

EVERY ROW FOLLOWS THE CLOSURE OF THE ROOTS THE RESULT NAMES. A result names
``lem:estimate``, whose closure holds no assumption, when it reports neither a
bound nor a length; the first-order root (``frank-wolfe/thm:firstorder``, or
``cor:fo-dropped``) whenever it reports a bound; and ``cor:keylength-bound``
beside it with a length. So A-KEYREG and A-HASH, premises of ``thm:keylength``
and ``lem:ev-correctness`` only, are emitted with a key length and on no other
run, and the inherited A-ATK, A-SRC, A-RHOM and A-SEQ, which the first-order
bound rests on through ``lem:range`` and ``thm:accumulated-entropy``, with a
bound or a length and on no other run. A run that reports only the estimate
emits an empty ledger: ``lem:estimate`` says what the objective at a feasible
point is worth and rests on no assumption. The inherited A-TSM is no row: no
closure of this module holds it, and reductions emits it where its squashing
results rest on it.

THE DECLARED VALUES EACH ROW BINDS (values are bound per assumption) travel
beside the ledger as :func:`assumption_bindings`, one entry per row in the
ledger's order, in the shape of :mod:`certiqs_key.domain.bindings`;
:data:`ROW_BINDINGS` names them and says which clause each comes from.

``A-LMO`` IS THE SUBMODULE'S and is emitted on no run: both linear minima of a
bracket are bounded exactly, the feasible one from the oracle's dual
(``frank-wolfe/lem:feasible-side-dual``,
``frank-wolfe/req:verified-feasible-side``), so no first-order number rests on
a solver's optimality. Its key stays in the submodule's interface, which the
claim-closure table reads; this module emits no row for it. The core's docking
claims (``lem:estimate``, ``cor:keylength-bound``) assert nothing about how a
lower bound was obtained or in what arithmetic.

FIVE FORMER ASSUMPTIONS ARE NO ROW, each a condition the engine decides or a
theorem proves, which is no assumption; :data:`RETIRED_ASSUMPTION_IDS` says
where each went:

* ``A-DECL`` (``declaration_valid``) is ``def:admissible-declaration``,
  whose conditions the engine decides (``req:declaration-admission``), the
  non-empty feasible set included on every route that reports a key length,
  because a key length is reported only on a declaration the compiler emitted
  (``req:compiled-declaration-only``; :mod:`certiqs_key.meat_core.provenance`);
* ``A-ACC`` (``acceptance_convex``) is ``def:admissible-acceptance-set``,
  decided by ``req:acceptance-set-admission``;
* ``A-MARG`` (``trusted_marginal``) is ``lem:product-marginal``, derived
  from the source's premises. The DECLARATION FIELD ``trusted_marginal`` (the
  accessor of ``tau_A``) is a different thing and stays;
* ``A-PUR`` (``purifier_dim_ok``) is implied by the definitions
  (``def:hqkd-list``);
* ``A-BLOCK`` (the compiler's ``block_diagonal_feasible_set``) is the
  compiler's remark ``protocol-compiler/rem:block-restriction``, which
  ``thm:reduction``, step 1, proves. No ledger carries a row for it.

WHETHER A ROW IS NEVER VERIFIED IS ITS ASSUMPTION'S HEADER FIELD. The
constants below that state it -- :data:`NEVER_VERIFIED`,
:data:`INHERITED_NEVER_VERIFIED_KEYS` -- are read from the shipped
claim-closure table by machine key, never listed here by hand, and the run
record marks this module's bare keys the same way.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from certiqs_key.domain.bindings import LedgerBindings
from certiqs_key.domain.claim_closure import never_verified

__all__ = [
    "ASSUMPTION_MACHINE_KEYS",
    "DECLARATION_NOT_COMPILED",
    "FIRST_ORDER_ROWS",
    "INHERITED_KEYS",
    "INHERITED_NEVER_VERIFIED_KEYS",
    "KEY_LENGTH_ROWS",
    "NEVER_VERIFIED",
    "OPTIONAL_BINDINGS",
    "PER_PARTY_ROWS",
    "REASON_TEXT",
    "RETIRED_ASSUMPTION_IDS",
    "RETIRED_REFUSAL_REASONS",
    "ROW_BINDINGS",
    "WITHDRAWAL_REASONS",
    "AssumptionId",
    "AssuranceReason",
    "GroupAPredicate",
    "RefusalReason",
    "assumption_bindings",
    "assumption_ledger",
    "laboratory_parties",
]


class AssuranceReason(StrEnum):
    """Why a run reports ``estimate`` rather than ``first-order``.

    EIGHT STRINGS: the four WITHDRAWAL reasons of
    ``frank-wolfe/req:first-order-withdrawal``, two that name WHICH acceptance-set
    check sent the run to ``+inf``, one that names the ``+inf`` objective
    itself, and one that names a run which never reached a bracket at all. A
    fifth withdrawal, ``oracle_not_optimal``, is not emitted (it went with
    A-LMO; :data:`RETIRED_REFUSAL_REASONS`).

    TWO SPELLINGS DO NOT EXIST. ``declared_operator_tolerance_open`` would force
    the tier to the estimate when the declared receiver family was admitted with
    a nonzero defect; no family is admitted with a defect, so the state does
    not arise. ``first_order_not_requested`` would name a run whose
    ``requested_assurance`` was ``estimate``; THE TIER IS ACHIEVED AND NEVER
    REQUESTED (the interface's ``retired_parameter_rows``), so there is no
    request to record and :attr:`NO_BRACKET` names the only case -- a run that
    reached no bracket to withdraw.
    """

    # -- the four withdrawals of frank-wolfe/req:first-order-withdrawal -----
    #: (H-POS) failed at a contributing iterate.
    GRADIENT_HYPOTHESIS_POSITIVITY = "gradient_hypothesis_positivity"
    #: (H-SUPP) failed at one.
    GRADIENT_HYPOTHESIS_SUPPORT = "gradient_hypothesis_support"
    #: (H-NOPERT) failed over the run.
    GRADIENT_PERTURBATION_APPLIED = "gradient_perturbation_applied"
    #: The point failed one of the three checks of
    #: ``frank-wolfe/rem:fo-iterate-checks`` and was not repairable under
    #: ``frank-wolfe/req:iterate-repair``,
    #: OR its acceptance-side component was not formed on the exact island.
    #: EITHER CASE CARRIES THIS ONE REASON.
    ITERATE_NOT_FEASIBLE = "iterate_not_feasible"

    # -- the run never reached a bracket ------------------------------------
    #: The objective was ``+inf`` at the point the run returned, so there is no
    #: finite bracket to take a maximum of.
    OBJECTIVE_INFINITE = "objective_infinite"
    #: No bracket was reached at all, and nothing failed. There is no request
    #: row to have declined, and a record with no reason set still has to say
    #: what it means.
    NO_BRACKET = "first_order_no_bracket"

    # -- WHICH acceptance-set check failed on the +inf path ------------------
    #
    # THESE TWO ARE NOT AMONG THE INTERFACE'S STRINGS and this module does
    # not present them as such. A reason should name the failed check rather
    # than the symptom they share, and an unusable acceptance set reaches
    # ``h_low = +inf`` by a route of its own: an empty denotation, or data
    # that is not well formed for the form it claims. A geometry tag this
    # implementation does not read has no string: it is refused at admission,
    # before any solve (``frank-wolfe/req:acceptance-geometries``), and never
    # reaches a record. The contract names the OUTCOME (no
    # key-length claim, ``rem:hlow-range``) and leaves the diagnosis to the
    # implementation, so these are implementation reasons under an
    # implementation prefix rather than borrowed from the contract's
    # vocabulary.
    #
    # AN EMPTY ACCEPTANCE SET IS NOT AN ERROR: it SATISFIES
    # ``def:admissible-acceptance-set``, being a closed convex subset of the simplex, so
    # the refusal cannot come from the definition and has to be decided.
    ACCEPTANCE_SET_EMPTY = "acceptance_set_empty"
    ACCEPTANCE_SET_ILL_FORMED = "acceptance_set_ill_formed"


#: One sentence per reason, for a reader of a record who should not have to
#: open the contract to learn what the string means.
REASON_TEXT: Mapping[AssuranceReason, str] = {
    AssuranceReason.GRADIENT_HYPOTHESIS_POSITIVITY: (
        "hypothesis (H-POS) of frank-wolfe/thm:firstorder failed at a "
        "contributing iterate: q_t(chat) > 0 and P^J_chat(J_t) > 0 are "
        "required for every chat in Chat_acc, and K^J_chat(J_t) > 0 for every "
        "key-active one. STATED ON Chat_acc AND NOT ON Chat, because on Chat "
        "it would be unsatisfiable whenever Chat_acc is a proper subset -- a "
        "case def:admissible-acceptance-set admits"
    ),
    AssuranceReason.GRADIENT_HYPOTHESIS_SUPPORT: (
        "hypothesis (H-SUPP) failed: a key-active branch operator X_{chat,s} "
        "does not attain maximal support, rank X_{chat,s} = dim W_{chat,s}. "
        "This is NOT positivity of X_{chat,s} on its ambient space, which no "
        "X_{chat,s} has; J_{t,s} > 0 suffices for it. frank-wolfe/rem:fo-danger: "
        "the failure of (H-SUPP) is on the UNSAFE side, which is why it "
        "withdraws rather than adjusts"
    ),
    AssuranceReason.GRADIENT_PERTURBATION_APPLIED: (
        "hypothesis (H-NOPERT) failed: the gradient must be the split-form "
        "gradient taken AT x_t ITSELF, with no perturbation of x_t, of any "
        "J_{t,s}, or of any branch operator built from them. "
        "frank-wolfe/rem:fo-nopert: the perturbation route is CLOSED, and the "
        "consequence of applying one is a WITHDRAWAL and not a weakening"
    ),
    AssuranceReason.ITERATE_NOT_FEASIBLE: (
        "a contributing iterate was not established to lie in "
        "AcceptSet x Feas^J(epsilon): it failed one of the three checks of "
        "frank-wolfe/rem:fo-iterate-checks and was not repairable under "
        "frank-wolfe/req:iterate-repair, "
        "or its acceptance-side component was not formed on the exact island "
        "under (alpha) and (beta) of frank-wolfe/rem:acc-side. EITHER CASE "
        "CARRIES THIS ONE REASON"
    ),
    AssuranceReason.NO_BRACKET: (
        "the run reached no first-order bracket to report, and nothing "
        "failed. THE TIER IS ACHIEVED AND NEVER REQUESTED: there is no "
        "requested_assurance to have declined the bracket, so this names a "
        "record that simply carries none"
    ),
    AssuranceReason.ACCEPTANCE_SET_EMPTY: (
        "the declared acceptance set is well formed and its DENOTATION IS "
        "EMPTY. That satisfies def:admissible-acceptance-set -- an empty set is a "
        "closed convex "
        "subset of the simplex -- so eq:hlow-def is an infimum over nothing, "
        "h_low = +inf is propagated and never clamped, and no key-length claim "
        "is emitted (rem:hlow-range)"
    ),
    AssuranceReason.ACCEPTANCE_SET_ILL_FORMED: (
        "the declared acceptance data are not well formed for the geometry "
        "they claim. Refused before the denotation is looked at, because a set "
        "whose data contradict its own form denotes nothing to take an "
        "infimum over"
    ),
    AssuranceReason.OBJECTIVE_INFINITE: (
        "the objective is +inf at the returned point, so eq:hlb has no "
        "finite bracket to maximize. h_low = +inf is propagated and never "
        "clamped (rem:hlow-range), and no key length is emitted"
    ),
}

#: The four reasons that WITHDRAW a bracket the run could otherwise have
#: reported, as against the four that name a run which never had one.
WITHDRAWAL_REASONS: tuple[AssuranceReason, ...] = (
    AssuranceReason.GRADIENT_HYPOTHESIS_POSITIVITY,
    AssuranceReason.GRADIENT_HYPOTHESIS_SUPPORT,
    AssuranceReason.GRADIENT_PERTURBATION_APPLIED,
    AssuranceReason.ITERATE_NOT_FEASIBLE,
)


class RefusalReason(StrEnum):
    """Machine-readable refusals that end a run outright.

    Distinct from :class:`AssuranceReason` because a refusal produces NO
    OUTPUT, while an assurance reason travels on a result that exists.
    """

    #: The map a declared Q-operator family carries disagrees with the declared
    #: sector map in the BLOCK KIND, in the LIST OF BLOCK IDENTIFIERS or in
    #: their ORDER. The refusal names the first position at which the two lists
    #: differ.
    #:
    #: THE PREDICATE IS THE PLATFORM'S STRUCTURAL CHECK, which every consumer
    #: performs (spec/architecture.md 2.9); no tolerance definition is involved.
    SECTOR_MAP_DISAGREEMENT = "sector_map_disagreement"

    #: For some sector, the declared-order completeness sum of the receiver
    #: family does not round nowhere (``eq:declorder``). Carries THE SECTOR AND
    #: THE OUTCOME INDEX at which the first inexact addition occurred, and the
    #: declared order. ALSO SPELLED BY spec/modules/protocol-compiler, which
    #: decides the same predicate on the same family before emitting it: one
    #: string for one refusal, on both sides of the boundary.
    BOB_POVM_SUMMATION_ROUNDS = "bob_povm_summation_rounds"

    #: A declared family fails Hermiticity, positive semidefiniteness or
    #: completeness per block, or the declared marginal fails its predicates or
    #: its trace, or a declared constraint operator is not Hermitian per block.
    #: THE REFUSAL NAMES THE PREDICATE -- a member of :class:`GroupAPredicate`
    #: -- AND THE BLOCK, OUTCOME OR ENTRY INDEX at which it first failed. See
    #: the module docstring for why there is one spelling here and not three.
    DECLARATION_NOT_EXACTLY_ADMISSIBLE = "declaration_not_exactly_admissible"

    #: ``iota^dagger iota - 1_{A_0}`` or ``iota iota^dagger tau_A - tau_A`` is
    #: not EXACTLY 0 entrywise, on the isometry THIS MODULE CONSTRUCTED. Both
    #: constructions of ``lem:choi-marginal`` meet it by ``{0, 1}`` arithmetic.
    #: A GROUP B REFUSAL: the object is computed here and not declared, so it
    #: carries no declared number.
    CHOI_ISOMETRY_INEXACT = "choi_isometry_inexact"

    #: ``eps_PA + eps_EV + 2 eps_auth >= 1``, so the
    #: ``(eps_PA + eps_EV + 2 eps_auth)``-security statement of
    #: ``cor:composed-security`` (iii) a key length would be reported under --
    #: at the default ``eps_auth = 0`` the ``(eps_PA + eps_EV)``-statement --
    #: is EMPTY: satisfied by
    #: every protocol and by every length, including one that hands the
    #: adversary the key. THE RUN IS REFUSED AT PARAMETER VALIDATION, before
    #: any solve and before any length is computed.
    #:
    #: The corner is REAL and reachable: at
    #: ``eps_PA = eps_EV = 1``, ``lambda_EC = 0``, ``n = 1`` the right-hand
    #: side of ``eq:keylength-h`` is 1, and a length there at
    #: ``reported_tier`` first-order would contradict ``cor:keylength-bound``
    #: (b), which singles the corner out in its proof and disowns it -- "the
    #: corner carries no security claim, which is why the clause excludes it
    #: rather than claiming it".
    #:
    #: THE ARITHMETIC OF ``eq:keylength-h`` IS UNTOUCHED, which is the whole
    #: shape of the decision: the expression still computes what the claim says
    #: it computes, and what the gate removes is the ADVERTISEMENT of a
    #: first-order key-length claim at a parameter point the claim disowns. It
    #: is a DISCLOSED SCOPE NARROWING -- the claims admit the corner and this
    #: implementation refuses it -- and never a reading of a claim.
    #:
    #: THE PREDICATE IS THE SUM AND NOT EITHER BUDGET. Both budgets keep their
    #: declared domain ``(0, 1]`` and neither is narrowed on its own; what is
    #: refused is the pair whose sum reaches 1, because it is the SUM that the
    #: security statement is stated in.
    SECURITY_STATEMENT_VACUOUS = "security_statement_vacuous"

    #: A NEGATIVE computed estimate. NAMES THE VALUE AND THE POINT. The
    #: estimate is never clamped to zero -- unlike ``h_lb`` it is not a lower
    #: bound and zero cannot stand in for it: replacing it by zero would report
    #: a plausible number in place of a detected inconsistency. A BARE
    #: EXCEPTION IS NOT A CONFORMING IMPLEMENTATION OF THIS RULE.
    NEGATIVE_OBJECTIVE = "negative_objective"

    #: A run whose ``certified_evaluation`` option is ``strict`` and that is not
    #: reported at the certified tier (``frank-wolfe/req:certified-evaluation``
    #: (viii)); names the evaluation's reasons. No key length is reported.
    CERTIFICATION_REFUSED = "certification_refused"

    #: On a checked run with ``b > 0``, the cap ``2^(-x)`` on the probability
    #: that devices as declared pass the acceptance test is at most
    #: ``min_model_pass_probability`` (``req:unreachable-acceptance-set``
    #: (iv)), an undecided comparison included. The run is refused as a whole,
    #: before any order is evaluated, and reports no key length.
    ACCEPTANCE_SET_UNREACHABLE = "acceptance_set_unreachable"


#: THE NINE STRINGS THAT ARE NOT EMITTED, kept as strings so that a reader of a
#: record carrying one finds it disposed of rather than missing, and so that a
#: test can assert that none of them is a member of either enum above. Seven
#: belong to a declared-tolerance apparatus that does not exist, one to the
#: ``requested_assurance`` row and one to A-LMO. NONE IS REUSED AND NONE IS
#: RESPELLED.
RETIRED_REFUSAL_REASONS: Final[tuple[str, ...]] = (
    # There is no tolerance input to be absent, and none to have a domain.
    "declared_tolerance_absent",
    "declared_tolerance_out_of_domain",
    # Each named a MEASURED defect exceeding the declared tolerance. No defect
    # is measured on declared data; the predicate is decided exactly and its
    # failure is `declaration_not_exactly_admissible`, naming the predicate.
    "bob_povm_hermiticity_defect",
    "bob_povm_negative_part",
    "bob_povm_completeness_defect",
    # Named a family ADMITTED with a nonzero Hermiticity or positivity defect.
    # No family is admitted with a defect, so the state it named does not arise.
    "bob_povm_not_evaluable",
    # Forced the tier to the estimate for the same reason. Same disposition.
    "declared_operator_tolerance_open",
    # Refused a request naming the dropped third rung. There is no request
    # row and the rung is not carried in any form (PRINCIPLES.md section 10),
    # so there is no request to refuse and no value to reserve.
    "assurance_tier_not_available",
    # Withdrew an iterate on an oracle status that does not assert optimality.
    # No bracket reads the oracle's return or its status: the feasible side is
    # verified without them (frank-wolfe/req:verified-feasible-side), and
    # frank-wolfe/req:first-order-withdrawal withdraws for neither.
    "oracle_not_optimal",
    # Withdrew the bound for a geometry tag this implementation does not read.
    # frank-wolfe/req:acceptance-geometries refuses such a declaration at
    # admission, before any solve, so no run reaches a withdrawal for it and
    # no string names one.
    "acceptance_geometry_unsupported",
)


class GroupAPredicate(StrEnum):
    """The machine keys of the interface's ``group_a_declared_data`` rows.

    EVERY ROW IS DECIDED EXACTLY AND CARRIES NO WINDOW -- there is no number in
    this group. A refusal names the row that failed, which is what
    ``def:declaration`` asks for where it spells no string of its own: "the
    refusal names the predicate and the block, outcome or entry index at which
    it first failed".

    """

    #: The receiver family per sector block: the SECTOR MAP compared in its
    #: three components, Hermiticity, positive semidefiniteness, and
    #: completeness.
    BOB_POVM_ADMISSION = "bob_povm_admission"

    #: The declared-order completeness sum of each sector rounds nowhere. A ROW
    #: OF ITS OWN and not part of the one above, because a completeness defect
    #: of zero on a sum THAT ROUNDED does not say that the family is complete
    #: as declared: the two differ in the unsafe direction and by an amount no
    #: declared number bounds.
    BOB_POVM_SUMMATION_EXACT = "bob_povm_summation_exact"

    #: ``{M_x}`` Hermitian and positive semidefinite, the family complete, AND
    #: the completeness sum in the emitted index order verified to round
    #: nowhere.
    ALICE_POVM_EXACT = "alice_povm_exact"

    #: ``tau_A`` Hermitian, positive semidefinite and of trace one, WITH THE
    #: TRACE FORMED BY ADDITIONS OVER THE ROW INDEX verified to round nowhere.
    ALICE_MARGINAL_EXACT = "alice_marginal_exact"

    #: Each declared constraint operator HERMITIAN BLOCK BY BLOCK and
    #: sector-block diagonal, and its right-hand side of the type its tag
    #: declares. THE MACHINE KEY IS THE INTERFACE'S.
    #: Hermiticity is a predicate on the declared numbers and not a type
    #: condition, so it has a row; the tag and the typing are recorded beside it
    #: and COMPARE NO NUMBERS. POSITIVITY IS ASKED OF NO CONSTRAINT OPERATOR.
    CONSTRAINT_OPERATOR_EXACT = "constraint_operator_exact"

    #: The six conditions (W1)-(W6) that set the ``removable`` flag, plus the
    #: composition hypothesis of ``prop:removal-compose`` on the set a run
    #: actually deletes. A TOLERANCE MAY ONLY EVER REFUSE A REMOVAL, NEVER
    #: LICENSE ONE, which is why the row is decided at exactly zero.
    SECTOR_CRITERION = "sector_criterion"

    #: The declared acceptance data are a probability vector, respectively
    #: define a closed convex subset of the simplex on the acceptance alphabet
    #: (``def:admissible-acceptance-set``). ON THE EXACT ISLAND: exact rational
    #: arithmetic, never binary64.
    ACCEPTANCE_DATA_EXACT = "acceptance_data_exact"


class AssumptionId(StrEnum):
    """The assumptions this module OWNS, in the ledger's order.

    ONLY THE ASSUMPTIONS THIS MODULE OWNS AND A RUN EMITS (the interface's
    ``own_rows``): see the module docstring for the fate of each former
    member or retired id, which :data:`RETIRED_ASSUMPTION_IDS` names. The
    key-length premises this module owns, A-SEED to A-LAB below, are
    members. The two owned assumptions no run emits are not: A-SEPARATE
    (``ass:separate-executions``), live and reached by no key-rate root, and
    the superseded A-EVE-DIM, which :data:`RETIRED_ASSUMPTION_IDS` names;
    both keep their machine keys in the interface's ``unemitted_rows``.
    """

    #: The raw key sits in a dedicated fixed-length register and the
    #: error-correction transcript occupies one of ``lambda_ec`` bits, TOTAL
    #: AND NOT PER ROUND.
    A_KEYREG = "A-KEYREG"
    #: The privacy-amplification hash family is IDEAL two-universal. For a
    #: merely two-universal one the key-length expression must be tightened by
    #: ONE FURTHER BIT, in the unsafe direction.
    A_HASH = "A-HASH"
    #: The error-correction seed, the verification seed and the
    #: privacy-amplification hash choice are drawn with their laws, private
    #: until announced, independent of everything else and fresh each run;
    #: and, in trusted-source mode, the source's letters and the systems it
    #: prepares are independent of the adversary's registers, no purification
    #: of a prepared system ever reaching the adversary (``ass:seed`` (v),
    #: which ``lem:product-marginal`` reads). The machine key
    #: ``post_processing_seeds`` keeps its name: renaming it is a record change
    #: and the row's meaning is its assumption's text.
    A_SEED = "A-SEED"
    #: The acceptance set, ``n``, ``l``, ``lambda_EC``, the budgets and the
    #: declared authentication error bound and key consumption are fixed
    #: before the first round and applied unchanged (``ass:fixed``).
    A_FIXED = "A-FIXED"
    #: The implementation runs the analysed post-processing: the acceptance
    #: test, the abort on rejection, no further messages, the model's key or
    #: nothing, no early key use, the authentication post-processing
    #: (``ass:conform``).
    A_CONFORM = "A-CONFORM"
    #: The classical channel is authenticated by one scheme within ``eps_auth``
    #: consuming at most ``k_auth`` bits of pre-shared key, or is itself the
    #: authenticated channel with both zero (``ass:auth``). THE ROW BINDS THE
    #: DECLARED ``eps_auth`` AND ``k_auth``, zeros included.
    A_AUTH = "A-AUTH"
    #: Each party's laboratory is sealed: nothing about its records leaves it
    #: but its key, the public messages and, in trusted-source mode at the
    #: party of ``A``, the emitted systems, and the adversary acts on it only
    #: through what its declared measurements receive and the messages
    #: (``ass:lab``; category laboratory). ONE ROW PER PARTY, naming the party
    #: (:func:`laboratory_parties`). Replaces A-LAB-ALICE and A-LAB-BOB.
    A_LAB = "A-LAB"


#: The ledger's machine keys, one per own assumption, transcribed from the
#: interface's ``assumption_ledger.own_rows``. THE KEYS ARE BINDING FOR THIS
#: IMPLEMENTATION: the code is written onto these names, not the reverse.
ASSUMPTION_MACHINE_KEYS: Final[Mapping[AssumptionId, str]] = {
    AssumptionId.A_KEYREG: "key_register",
    AssumptionId.A_HASH: "pa_hash_family",
    AssumptionId.A_SEED: "post_processing_seeds",
    AssumptionId.A_FIXED: "parameters_fixed_before_run",
    AssumptionId.A_CONFORM: "post_processing_as_analysed",
    AssumptionId.A_AUTH: "classical_channel_authenticated",
    AssumptionId.A_LAB: "laboratory_sealed",
}

#: THE ROWS EMITTED ONCE PER PARTY OF THE DECLARATION, by machine key, each
#: row naming its party in the binding ``party`` (the interface's
#: ``emission_rule`` and ``binds`` for A-LAB). Every other row of this module
#: is emitted at most once and names no party.
PER_PARTY_ROWS: Final[frozenset[str]] = frozenset({
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_LAB],
})

#: THE OWN ROWS EMITTED "ON EVERY RUN THAT REPORTS A KEY LENGTH" (the
#: interface's ``emission_rule``), in the ledger's order: the premises
#: ``thm:keylength``, ``lem:ev-correctness`` and ``cor:composed-security``
#: declare. A-AUTH's row binds the declared ``eps_auth`` and ``k_auth``, which
#: the result carries beside the length as ``security_parameter`` and
#: ``net_key_length``. EVERY OWN ROW: no root of a run without a length reaches
#: A-KEYREG and A-HASH, so they are emitted with a length only.
KEY_LENGTH_ROWS: Final[tuple[AssumptionId, ...]] = (
    AssumptionId.A_KEYREG,
    AssumptionId.A_HASH,
    AssumptionId.A_SEED,
    AssumptionId.A_FIXED,
    AssumptionId.A_CONFORM,
    AssumptionId.A_AUTH,
    AssumptionId.A_LAB,
)

#: THE OWN ROWS A REPORTED FIRST-ORDER BOUND RESTS ON, emitted on every run
#: that reports one, with or without a key length: the
#: bound is ``frank-wolfe/thm:firstorder``, which rests through
#: ``thm:accumulated-entropy`` and ``lem:product-marginal`` on A-SEED (v) and
#: A-LAB. A subset of :data:`KEY_LENGTH_ROWS`, emitted in
#: its order. A-LAB ONLY WHERE ITS OWN RULE SAYS SO: without a length it is
#: emitted in trusted-source mode only, at the party of ``A``
#: (:func:`laboratory_parties`), because ``thm:accumulated-entropy`` uses it
#: in that mode only.
#: THE ROOT HALF OF THE SAME RULE: the result's certificate names
#: the first-order root whenever it reports a bound, a withheld length
#: included
#: (:func:`certiqs_key.solvers.frank_wolfe.general_keyrate.result_claim_roots`),
#: so these rows lie in the closure of the roots the result names.
#:
#: THE BOUND'S CLOSURE REACHES INHERITED PREMISES AS WELL. A-SEQ, A-RHOM, and
#: A-ATK and A-SRC where their conditions hold, are emitted with the bound by
#: :func:`assumption_ledger`.
#: A-ENS is not a row of this module (the interface's
#: ``inherited_rows`` carry none): on every pipeline route the transmitter's
#: own ledger, which a run emits always, carries A-ENS, or A-WCP in its place
#: on a decoy route (``runs.assumptions.COVERING_REFINEMENTS``), so the run's
#: manifest names it. A standalone engine result is not a run and carries no
#: route-exact set.
FIRST_ORDER_ROWS: Final[tuple[AssumptionId, ...]] = (
    AssumptionId.A_SEED,
    AssumptionId.A_LAB,
)

#: The reason code a key length is WITHHELD under when the declaration is not
#: known to be the protocol compiler's emission (``req:compiled-declaration-only``;
#: :mod:`certiqs_key.meat_core.provenance`). A withholding and not a refusal:
#: the run reports every other number. The code opens ``key_length_reason`` as
#: the other withholding codes do.
DECLARATION_NOT_COMPILED: Final[str] = "declaration_not_compiled"

#: THE OWN ASSUMPTIONS NO CODE PATH OF THIS MODULE DECIDES BEYOND THEIR
#: CLAUSES ON THE DECLARED DATA, in the ledger's order: the interface's
#: ``never_verified.own``. A member is exactly an assumption whose
#: ``verification`` header field is ``never`` (spec/claim-format.md section
#: 3.2), read from the shipped claim-closure table by machine key. Every own
#: assumption carries ``never``.
NEVER_VERIFIED: Final[tuple[AssumptionId, ...]] = tuple(
    identifier
    for identifier in AssumptionId
    if never_verified(ASSUMPTION_MACHINE_KEYS[identifier])
)

#: THE INHERITED ROWS, as their machine keys -- not as members of
#: :class:`AssumptionId`, because this module does not own them. Short ids are
#: repository-wide, so this module ASSUMES THE OWNER'S rather than restating one
#: of its own. The resolution of the short id to the owner's claim
#: file is the claim checker's; what travels in a run record is the key.
INHERITED_KEYS: Final[Mapping[str, str]] = {
    # (reductions' soundness assumption, key constraints_sound, is no row; see
    # RETIRED_ASSUMPTION_IDS.)
    #
    # protocol-compiler/ass:atk -- the licensed reduction over the round model
    # and the attack set. Engaged whenever the constraint list is non-empty and
    # a key length is wanted, on a run that reports a bound or a length (the
    # bound rests on it through lem:range); tested for PRESENCE and never for
    # truth.
    "A-ATK": "attack_set_license",
    # transmitter/ass:src -- one of the premises of lem:product-marginal.
    # Trusted-source mode at d_A >= 2, on a run that reports a bound or a
    # length; VACUOUS at d_A = 1 and NEVER DEMANDED THERE.
    "A-SRC": "source_replacement_license",
    # (reductions/ass:tsm, key test_statistics_model, is no row: no closure of
    # this module holds it; see RETIRED_ASSUMPTION_IDS.)
    #
    # protocol-compiler/ass:rhom -- one declaration describes every round. THE
    # KEY IS THE COMPILER'S OWN: `round_homogeneity` is the receiver's
    # for a different assumption. On a run that reports a bound or a length
    # (thm:accumulated-entropy rests on it).
    "A-RHOM": "round_homogeneity_declaration",
    # transmitter/ass:seq -- the sequential round structure, clauses (i), (ii)
    # and (iv), which thm:keylength consumes where the physical rounds are
    # mapped onto the round channels, and clause (v), every measuring party
    # measuring in round order, which lem:honest-attacks reads and through it
    # cor:composed-security, to reach every adversary of the
    # honest-authentication setting. Emitted on every run that reports a key
    # length or a first-order bound (the bound rests on it through
    # lem:product-marginal); the transmitter emits its own row always, and
    # the run record keeps one row per emitter.
    "A-SEQ": "sequential_round_model",
}

#: THE INHERITED ROWS NOTHING HERE MAY DECIDE, as their machine keys, in the
#: order of :data:`INHERITED_KEYS`: the interface's
#: ``never_verified.inherited``. Every inherited key whose assumption carries
#: ``verification: never`` in its OWNER's header, read from the shipped
#: claim-closure table, so the row carries its owner's mark.
INHERITED_NEVER_VERIFIED_KEYS: Final[tuple[str, ...]] = tuple(
    key for key in INHERITED_KEYS.values() if never_verified(key)
)

#: THE RETIRED SHORT IDS: each id this module once owned or emitted that is no
#: member of :class:`AssumptionId` now, with where it is read now
#: (``id -> successor``). Kept as strings so that a test can assert none of
#: them is a member. Nothing on a run path reads the values. NOT EVERY
#: NON-MEMBER IS HERE: the compiler's A-LINK, A-SPEC and A-ALICE-MEAS, which
#: the compiler's ledger emits (the module docstring), are not, and neither is
#: A-SEPARATE, which this module owns and no key-rate root reaches, so that it
#: is no ledger row, but which is not retired (the interface's
#: ``unemitted_rows``).
RETIRED_ASSUMPTION_IDS: Final[Mapping[str, str]] = {
    "A-DIM": "renamed A-PUR, keeping the machine key purifier_dim_ok; see A-PUR",
    "A-DTOL": "no successor: no declared tolerance exists",
    "A-SRC": "the transmitter's, inherited by machine key",
    "A-TSM": "reductions', inherited by machine key; emitted by reductions, not here",
    "A-SOUND": (
        "a conclusion of reductions' theorems "
        "(rem:sound-and-atk); no row of any ledger"
    ),
    "A-ROUNDHOM": "the compiler's A-RHOM, inherited by machine key",
    "A-ATK": (
        "protocol-compiler/ass:atk, inherited by machine key under this "
        "module's id"
    ),
    "A-ALPHA": (
        "meat-core/req:key-length-alpha-domain and "
        "req:objective-alpha-domain: each theorem states its own range"
    ),
    "A-DECL": (
        "meat-core/def:admissible-declaration, decided by "
        "req:declaration-admission, and req:compiled-declaration-only"
    ),
    "A-MARG": (
        "meat-core/lem:product-marginal, derived from the source's premises; "
        "the declaration field trusted_marginal stays"
    ),
    "A-PUR": "meat-core/def:hqkd-list: the purifier's dimension is defined",
    "A-ACC": (
        "meat-core/def:admissible-acceptance-set, decided by "
        "req:acceptance-set-admission"
    ),
    "A-LAB-ALICE": "meat-core/ass:lab (A-LAB), one row per party",
    "A-LAB-BOB": "meat-core/ass:lab (A-LAB), one row per party",
    "A-BLOCK": (
        "protocol-compiler/rem:block-restriction, proved by thm:reduction step 1"
    ),
    "A-EVE-DIM": (
        "superseded (meat-core/ass:eve-dim), assumed by no claim: the round "
        "model's registers are finite by definition, and cor:composed-security "
        "lifts to registers of any dimension through lem:memory-lift; its key "
        "adversary_registers_finite stays in the interface's unemitted_rows"
    ),
}


def laboratory_parties(
    *,
    trusted_source: bool,
    alice_party: str,
    key_length_reported: bool,
    first_order: bool,
) -> tuple[str, ...]:
    """Return the parties A-LAB's row is emitted at, in emission order.

    ``meat-core/ass:lab``; the interface's ``emission_rule`` for A-LAB: "once
    per party of the declaration, its row naming the party: on a run that
    reports a key length, at both parties, unconditionally, as
    thm:keylength assumes it at each of the two; on a run that reports a
    first-order bound and no key length, in trusted-source mode only and only
    at the party to which the party partition assigns A, the one instance
    thm:accumulated-entropy uses, and in untrusted-source mode not at all".
    The parties are the declaration's formal labels ``A`` and ``B``, in that
    order; ``alice_party`` is the label part (b) of the party partition gives
    the system ``A`` (``AliceFactor.party``), which need not be ``A``.
    """
    if key_length_reported:
        return ("A", "B")
    if first_order and trusted_source:
        return (str(alice_party),)
    return ()


def assumption_ledger(
    *,
    trusted_source: bool,
    alice_dim: int,
    alice_party: str,
    constraint_entries: int,
    key_length_wanted: bool,
    key_length_reported: bool,
    first_order: bool,
) -> tuple[str, ...]:
    """Return the ``assumption_ledger`` output row: the emitted machine keys.

    THE PRESENCE RULES ARE THE INTERFACE'S, and they FOLLOW the claims rather
    than adding to them: every row is a premise of a root the result names
    (the module docstring), so a run that reports neither a bound nor a
    length, whose one root ``lem:estimate`` rests on nothing, emits no row.
    The own rows (:data:`KEY_LENGTH_ROWS`) on every run that reports a key
    length, two of them (:data:`FIRST_ORDER_ROWS`) on every run that
    reports a first-order bound as well, A-LAB once per party
    :func:`laboratory_parties` names (so twice with a length, and without
    one only in trusted-source mode, once); the inherited A-RHOM and A-SEQ on
    every run that reports a bound or a length; A-ATK there too, and only
    where the constraint list is non-empty and a key length is wanted; A-SRC
    there too, and only in trusted-source mode at ``d_A >= 2`` -- vacuous at
    ``d_A = 1`` and NEVER DEMANDED THERE. A-LMO, the submodule's, is emitted
    on no run (the module docstring). The EMISSION rule is the
    interface's
    (its ``fixed_by_this_file``), because the claim files do not state an
    emission rule for a ledger they do not know is emitted.

    WHAT IS NO ROW. What the declaration
    and the acceptance set must satisfy is decided by the engine
    (``def:admissible-declaration``, ``def:admissible-acceptance-set`` and
    their requirements), the product marginal is ``lem:product-marginal``,
    the purifier's size is part of the definitions, and the block restriction
    is the compiler's remark ``rem:block-restriction``; the rows
    ``declaration_valid``, ``trusted_marginal``, ``purifier_dim_ok``,
    ``acceptance_convex`` and ``block_diagonal_feasible_set`` are no rows
    (:data:`RETIRED_ASSUMPTION_IDS`).

    Args:
        trusted_source: whether the marginal slot is filled.
        alice_dim: ``d_A``, read for the row whose presence rule
            degenerates at ``d_A = 1`` (A-SRC).
        alice_party: the party label of ``A`` (part (b) of the party
            partition), read for A-LAB's row without a length.
        constraint_entries: ``m``, the length of the declared constraint list.
        key_length_wanted: whether a key-length claim is being made; the
            attack-set licence is engaged only then.
        key_length_reported: whether the run REPORTS a key length -- not
            whether one was wanted: the premises of the secrecy theorem, the
            correctness lemma and the composed statement are what an emitted
            length rests on, and a run whose length was withheld rests on
            none of them.
        first_order: whether the run reports a first-order bound.

    Returns:
        The machine keys, in the ledger's order: the own rows, then the
        inherited ones.
    """
    # A REPORTED BOUND OR LENGTH: the roots the result then names
    # (frank-wolfe/thm:firstorder or cor:fo-dropped, and cor:keylength-bound
    # beside a length) reach every inherited row below through lem:range and
    # thm:accumulated-entropy; lem:estimate, the one root of a run that
    # reports neither, reaches none.
    bound_or_length = key_length_reported or first_order
    # THE OWN ROWS: "on every run that
    # reports a key length", A-AUTH with the declared eps_auth and k_auth
    # bound to it, which the result carries beside the length. A-SEED
    # and A-LAB also on every run that reports a first-order
    # bound: the bound rests on them through
    # lem:product-marginal. A-KEYREG and A-HASH only with a length: their only
    # roots are thm:keylength and lem:ev-correctness. A-LAB
    # once per party of laboratory_parties.
    parties = laboratory_parties(
        trusted_source=trusted_source,
        alice_party=alice_party,
        key_length_reported=key_length_reported,
        first_order=first_order,
    )
    keys: list[str] = []
    for member in KEY_LENGTH_ROWS:
        key = ASSUMPTION_MACHINE_KEYS[member]
        if key in PER_PARTY_ROWS:
            keys.extend(key for _ in parties)
        elif key_length_reported or (first_order and member in FIRST_ORDER_ROWS):
            keys.append(key)
    # THE ROW THE CONSTRAINT LIST ENGAGES. A-ATK is not engaged at an empty
    # list. No second row, reductions' constraints_sound, is emitted for
    # entries that came through a reductions chain: the soundness
    # of an emitted entry is a conclusion of that module's theorems, and
    # inside the security chain A-ATK implies it (lem:range (i)).
    if constraint_entries >= 1 and key_length_wanted and bound_or_length:
        keys.append(INHERITED_KEYS["A-ATK"])
    # VACUOUS AT d_A = 1 AND NEVER DEMANDED THERE: what A-SRC licenses is the
    # normalization, satisfied by every state, so it deletes no attack
    # (rem:modes-da1 (b5); transmitter/rem:da1).
    if trusted_source and alice_dim >= 2 and bound_or_length:
        keys.append(INHERITED_KEYS["A-SRC"])
    # (A-TSM is no row here: no closure of this module holds it -- only
    # remarks and requirements reach reductions/ass:tsm from here -- and
    # reductions emits it where its squashing results rest on it.)
    if bound_or_length:
        # protocol-compiler/ass:rhom, read by thm:accumulated-entropy, and
        # transmitter/ass:seq, consumed by thm:keylength and, through
        # lem:product-marginal, by the first-order bound.
        keys.append(INHERITED_KEYS["A-RHOM"])
        keys.append(INHERITED_KEYS["A-SEQ"])
    return tuple(keys)


#: THE DECLARED VALUES EACH ROW BINDS, by machine key, in the order each row
#: lists them (values are bound per assumption). Each name is a
#: value the engine holds on the run -- a declared input or a parameter --
#: and is bound because a clause of the row's
#: assumption is about it or is stated for it; the clause is given beside
#: each row. A row whose clauses are about the adversary or the run's
#: physical order and name no value the engine holds binds nothing. A-LAB's
#: ``party`` is the one name that is the row's own rather than a declared
#: value (:func:`assumption_bindings`).
ROW_BINDINGS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    # ass:keyreg (ii) the declared key holder computes Z_1^n; (iv) the
    # transcript occupies a fixed register of lambda_EC bits.
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_KEYREG]: ("lambda_ec", "key_holder"),
    # ass:hash (i) the privacy-amplification family has l-bit values and is
    # IDEAL two-universal (ideal_hash: whether the length was computed for an
    # ideal family; req:hash-penalty); (ii) the verification family has
    # ceil(log2(1/eps_EV))-bit values, read from the engine's deductions.
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_HASH]: (
        "key_length",
        "ideal_hash",
        "ev_hash_bits",
    ),
    # ass:seed (v) is stated "in trusted-source mode"; (i)-(iv) are about the
    # post-processing seeds, which no declared value describes.
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SEED]: ("source_mode",),
    # ass:fixed (i), in its order: the acceptance set, n, l, lambda_EC,
    # eps_PA, eps_EV, eps_auth and k_auth are fixed before the first round.
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_FIXED]: (
        "acceptance_set",
        "rounds",
        "key_length",
        "lambda_ec",
        "eps_pa",
        "eps_ev",
        "eps_auth",
        "k_auth",
    ),
    # ass:conform (i) the acceptance test; (ii) the post-processing messages,
    # the transcript of lambda_EC bits and the verification hash; (iv) the
    # l-bit key each party outputs.
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_CONFORM]: (
        "acceptance_set",
        "lambda_ec",
        "ev_hash_bits",
        "key_length",
    ),
    # ass:auth (ii) at most k_auth bits of key; (v) eps_0 + delta <= eps_auth;
    # (i) both zero for the authenticated channel itself.
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_AUTH]: ("eps_auth", "k_auth"),
    # ass:lab, stated for a party P: `party` the party the row is emitted for
    # (one row per party, :data:`PER_PARTY_ROWS`; bound from the row, not from
    # the declared values); the source mode, which with the label of A decides
    # the systems handed out of P's laboratory (trusted-source mode at the
    # party of A) and whether A is delivered into it (untrusted-source mode);
    # the party labels of the party partition, part (b), which decide the
    # systems delivered into it.
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_LAB]: (
        "party",
        "source_mode",
        "party_partition",
    ),
    # protocol-compiler/ass:atk: "for a non-empty constraint list CList that
    # is licensed for the declared source mode": the entries' right-hand-side
    # tags decide the licence (def:homog), the source mode its class; (i) the
    # certificate the chain's producer supplies, where it is supplied. The
    # shapes are the compiler's, so the run's one entry merges them.
    INHERITED_KEYS["A-ATK"]: (
        "constraint_entries",
        "source_mode",
        "attack_set_license",
    ),
    # transmitter/ass:src: its premise, "in trusted-source mode, which fills
    # the marginal slot with tau_A"; (ii) "her declared measurement {M_x}";
    # the party label of A (party_partition (b)), whose laboratory (i) names
    # (the transmitter binds no label, its
    # interface leaving it to this row). The first three shapes are the
    # transmitter's.
    INHERITED_KEYS["A-SRC"]: (
        "source_mode",
        "alice_marginal",
        "alice_povm",
        "party_partition",
    ),
    # protocol-compiler/ass:rhom (i): every round described by the same
    # declaration and source mode. The round count is this module's input.
    INHERITED_KEYS["A-RHOM"]: ("rounds", "source_mode"),
    # transmitter/ass:seq (ii): the post-processing after the n rounds; its
    # other clauses are about the physical order of each round's steps.
    INHERITED_KEYS["A-SEQ"]: ("rounds",),
})

#: The names a row binds only where the run holds the value: the
#: attack-set licence, only where the declaration carries one.
OPTIONAL_BINDINGS: Final[frozenset[str]] = frozenset({"attack_set_license"})


def assumption_bindings(
    ledger: Sequence[str],
    declared: Mapping[str, object],
    *,
    parties: Sequence[str] = (),
) -> LedgerBindings:
    """Return the declared values each emitted row binds, one entry per row.

    Values are bound per assumption: beside each row of ``ledger``, in its order, the
    ``(name, value)`` pairs :data:`ROW_BINDINGS` names for it, read from
    ``declared`` -- the values of one run, in the shape of
    :mod:`certiqs_key.domain.bindings` (an exact rational as ``"p/q"``, a
    binary64 parameter as itself, an operator by its shape and never
    inlined; the run's values are built by
    :func:`certiqs_key.solvers.frank_wolfe.general_keyrate.declared_values`).
    A name of :data:`OPTIONAL_BINDINGS` whose value is ``None`` is omitted;
    any other name ``declared`` lacks is an error, never a silent gap.

    THE ROW'S PARTY. A row of :data:`PER_PARTY_ROWS` binds ``party`` to the
    party it is emitted for, which is the row's and not a declared value:
    ``parties`` are those parties in emission order
    (:func:`laboratory_parties`), consumed one per such row.

    Raises:
        KeyError: a ledger key this module does not emit, or a required
            name absent from ``declared``.
        ValueError: ``parties`` does not hold exactly one party per row of
            :data:`PER_PARTY_ROWS` in ``ledger``.
    """
    remaining = list(parties)
    rows = []
    for key in ledger:
        pairs: list[tuple[str, object]] = []
        for name in ROW_BINDINGS[key]:
            if name == "party" and key in PER_PARTY_ROWS:
                if not remaining:
                    raise ValueError(
                        f"the ledger emits {key} at more parties than the "
                        f"{len(parties)} given"
                    )
                pairs.append((name, str(remaining.pop(0))))
                continue
            value = declared.get(name) if name in OPTIONAL_BINDINGS else declared[name]
            if value is None and name in OPTIONAL_BINDINGS:
                continue
            pairs.append((name, value))
        rows.append((key, tuple(pairs)))
    if remaining:
        raise ValueError(
            f"{len(remaining)} of the given parties name no per-party row of the "
            "ledger"
        )
    return tuple(rows)
