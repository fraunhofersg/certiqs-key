"""The fixed-length key length of C14, and the two gates that guard it.

contract.tex Theorem ``thm:keylength``, Eq. ``eq:keylength``, with the reported
value of Remark ``rem:plus2``::

    l_max = max{0, floor( n h_low - lambda_EC - ceil(log2(1/eps_EV))
                          - (alpha/(alpha-1)) log2(1/eps_PA) + 1 )}

The ``+1`` is this contract's, not the source's: the source region proves
secrecy for the ``^Omega_AT`` state with constant ``+2``, and this contract
spends one deterministic bit -- the announced error-verification acceptance flag
``F_acc`` -- to reach the ACCEPTED state (Remark ``rem:plus2``). An
implementation must not silently use ``+2``. The floor and the clamp at zero are
the platform's conservative integer-output rule, both in the safe direction
(spec/architecture.md 9: "final integer key length is rounded downward").

THREE GATES, ALL FAIL-CLOSED
============================
*The infinite-entropy gate.* Remark ``rem:hlow-range``: if ``h_low = +inf``
reaches this theorem, the conforming behaviour is to emit NO key-length claim
and report the declaration/acceptance mismatch. ``h_low = +inf`` means no
accepted frequency vector is absolutely continuous with respect to any reachable
statistics, so ``Pr[Omega_AT] = 0`` for every attack, the hypothesis
``Pr[Omega_AT] > 0`` of Theorem ``thm:accumulated-entropy`` fails, and there is
no run on which a
key would be produced. Substituting ``+inf`` into Eq. ``eq:keylength`` would
return an enormous integer, which is the failure this gate exists to forbid.

*The constraint gate.* the `inputs` table and thm:constrained-accumulation "Interface
consequence": a key-length output may be combined with a nonempty constraint
list only if (i) EVERY ENTRY IS IN THE LICENSED FORM OF THE DECLARED SOURCE
MODE -- the ``homogeneous`` tag of Definition ``def:homog``, carrying a real
scalar ``c_k``; A TYPE CHECK ON THE DECLARED TAG THAT COMPARES NO NUMBERS and
is decided at no window -- AND
(ii) ``attack_set_license`` is present, an attestation no program can verify,
which this module therefore never inspects beyond its presence. Without both,
the numerical machinery stays available (``h_low(L)`` is a legitimate output;
"numerical use outside the security chain is unrestricted") but its value must
not reach Eq. ``eq:keylength``: the tightening ``h_low(L) >= h_low({})`` is
purchased entirely by Assumption A-ATK.

*The source-replacement gate.* thm:constrained-accumulation, same paragraph: "a declared
``tau_A`` without ``source_replacement_license`` (Assumption A-SRC) must
hard-fail before any key-length output, and at ``d_A = 1`` the licence is
vacuous and must not be demanded (Remark ``rem:modes-da1`` (b5))". A declared
``tau_A`` deletes from the feasible set every state whose ``A``-marginal
differs, hence every attack that would have produced one -- a different KIND of
input from an entry of ``L`` and a more demanding one to justify -- so it is
gated the same way, and by an attestation this module likewise never verifies.
The two gates are INDEPENDENT: :func:`check_key_length_permitted` reports every
failure it finds, so neither can mask the other.

PART (i) DEGENERATES, AND MUST NOT READ AS A PASSED CHECK
=========================================================
Remark ``rem:cgate`` states plainly how much part (i) checks and when it checks
nothing:

* trusted-source mode with ``d_A >= 2`` -- a GENUINE restriction; the licensed
  class is the ``homogeneous`` tag, whose right-hand side ``c_k tau_A`` spans a
  one-dimensional subspace of the ``d_A^2``-dimensional real space of Hermitian
  operators on ``A``, and a declaration can fail it by declaring ``general``;
* ``d_A = 1`` -- a type check that rejects nothing a producer cannot trivially
  avoid: an entry declared ``general`` FAILS it, as at every ``d_A``
  (Definition ``def:homog``), but every ``1 x 1`` Hermitian ``Theta_k`` equals
  ``c_k tau_A`` (Proposition ``prop:trivial-alice-system`` (iii)), so such an
  entry could always have been declared homogeneous with the same condition;
* untrusted-source mode at any ``d_A`` -- VACUOUSLY TRUE: the entry TYPE is
  scalar by Definition ``def:declaration``, so part (i) degenerates from a
  mathematical condition to a type check a well-formed declaration passes by
  construction.

In the two degenerate cases a passing part (i) is evidence of nothing, and the
gate must still hard-fail on a missing attestation
(``req:degenerate-gate-report``). So :class:`LicensedClassCheck` carries
``vacuous`` beside ``licensed`` -- ``True`` exactly where part (i) PASSED in a
degenerate case, the field keeping its name because the gate report's keys do
not move -- a bare ``True`` is never the whole verdict, and
:func:`constraint_gate_report` puts the degeneracy into the certificate a
reader sees. Part (i) is not read as vacuously true at ``d_A = 1``: a
``general`` 1 x 1 entry is not licensed there.

THE PROVENANCE GATE
===================
``req:compiled-declaration-only``: a key length is reported only on a
declaration the protocol compiler emitted. On any other, condition (vii) of
``def:admissible-declaration`` (a non-empty feasible set) is decided by no code
path where constraints are declared, and nothing relates the declaration to the
protocol being run. How the engine knows is an in-memory token the run tier
passes (:class:`~certiqs_key.meat_core.provenance.CompilerEmission`); without
it the length is WITHHELD with :func:`declaration_provenance_failure`'s reason,
which opens with ``declaration_not_compiled``. The wire and the bundle format
are unchanged.

AND ONE REFUSAL THAT IS NOT A GATE
==================================
:func:`check_security_statement` refuses ``eps_PA + eps_EV + 2 eps_auth >= 1``
outright (``req:security-statement-not-vacuous``). It is listed apart from the three
because a gate WITHHOLDS THE LENGTH and leaves ``h_low`` on the record, while
this REFUSES THE RUN: there is no security statement for the length to be
reported under, so there is nothing to report partially. It is decided at
parameter validation, before any solve, and it is a DISCLOSED SCOPE NARROWING
of an input the claims admit rather than a condition any claim imposes. At the
default ``eps_auth = 0`` it is the two-budget rule.

THE COMPOSED SECURITY PARAMETER AND THE NET KEY
===============================================
Corollary ``cor:composed-security`` (iii): over an authentication scheme within
``eps_auth`` that consumes ``k_auth`` bits of pre-shared key (Assumption
A-AUTH), the protocol is ``(eps_PA + eps_EV + 2 eps_auth)``-secure, and when
both parties output an ``l``-bit key its net key gain is ``l - k_auth``.
:func:`composed_security` computes the two outputs the interface emits beside
``key_length`` -- ``security_parameter`` and ``net_key_length`` -- and neither
``eps_auth`` nor ``k_auth`` enters Eq. ``eq:keylength``: every key length is
what it was, and at the defaults ``eps_auth = 0``, ``k_auth = 0`` the net key
is the key length and the parameter is ``eps_PA + eps_EV``.

The acceptance probability is deliberately absent from the signature. The
accumulation penalty ``(alpha/(alpha-1)) log2(1/Pr[Omega_AT])`` cancels against
the ``Pr[Omega_AT]`` prefactor in the proof of Theorem ``thm:keylength``, so
``l_max`` carries no ``Pr[Omega_AT]`` dependence at all; accepting one as an
input would be adding a parameter the contract does not have.
"""

from __future__ import annotations

import math
import numbers
import operator
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.errors import (
    SecurityGateError,
    SecurityStatementVacuousError,
)
from certiqs_key.meat_core.provenance import CompilerEmission
from certiqs_key.meat_core.reasons import DECLARATION_NOT_COMPILED, RefusalReason


@dataclass(frozen=True)
class LicensedClassCheck:
    """Part (i) of the two-part gate, with its degeneracy attached.

    ``licensed`` alone is never the whole verdict.
    ``req:degenerate-gate-report`` requires that a passing part (i) not read as
    evidence of anything where it is degenerate -- at ``d_A = 1`` and in
    untrusted-source mode (``rem:cgate``) -- so ``vacuous`` and ``reason``
    travel with it everywhere it goes. ``vacuous`` is ``True`` exactly where
    part (i) passed in one of those two cases; a FAILING part (i) is a verdict
    and carries ``vacuous=False`` at every ``d_A``.
    """

    licensed: bool
    vacuous: bool
    reason: str
    #: ``(c_k)_k`` when every entry declares the scalar form; ``None`` when one
    #: does not, and the empty tuple for an empty list.
    scalars: tuple[float, ...] | None


def licensed_class_check(declaration: ProtocolDeclaration) -> LicensedClassCheck:
    """Return part (i) of the gate for the DECLARED SOURCE MODE, with its degeneracy.

    A TYPE CHECK ON THE DECLARED TAG, AT EVERY ``d_A``, AND IT COMPARES NO
    NUMBERS. Definition ``def:homog`` reads the licensed class of
    ``protocol-compiler/def:homog``: a licensed entry declares the
    ``homogeneous`` form and its right-hand side is CONSTRUCTED from the
    declared ``c_k``; a ``general`` entry declares a Hermitian ``Theta_k`` and
    "remains admissible input, every structural and numerical claim of this
    module being proved for it, but it is never licensed, so a list containing
    one carries no key-length claim, which is the safe direction".

    NO WINDOW. The check does not ask whether ``Theta_k = c_k tau_A`` by
    projecting onto ``tau_A`` and comparing a residual against a declared
    relative window: the interface's ``declared_thresholds.group_c_retired``
    lists ``homogeneity`` because THE PREDICATE IS NOT NUMERICAL. Part (i) is
    not read as vacuously true at ``d_A = 1``, so no ``general`` 1 x 1 entry is
    licensed with its ``c_k`` read off the operator; the type check holds at
    every ``d_A`` (``rem:cgate``,
    ``protocol-compiler/rem:degenerate``).

    Remark ``rem:cgate`` fixes the three cases and which of them check
    anything; the ``reason`` returned is that remark's own reading, so that a
    reader of a certificate does not have to reconstruct it, and ``vacuous``
    is Requirement ``req:degenerate-gate-report``'s flag: ``True`` exactly
    where a PASSING part (i) is evidence of nothing.
    """
    if not declaration.constraint_list:
        return LicensedClassCheck(
            licensed=True,
            vacuous=True,
            reason=(
                "the declared constraint list is empty, so no gate applies "
                "(the `inputs` table: the gate is on m >= 1)"
            ),
            scalars=(),
        )
    if not declaration.is_trusted_source:
        # def:homog (b): the right-hand side IS a real scalar, which Assumption
        # def:admissible-declaration (vi) already makes the entry type, so part (i)
        # degenerates from a mathematical condition to a type check every well-formed
        # declaration passes. `validate_declaration` has already refused the
        # `general` tag here, so every surviving entry carries its c_k.
        return LicensedClassCheck(
            licensed=True,
            vacuous=True,
            reason=(
                "VACUOUS (Remark rem:cgate): in untrusted-source mode the "
                "licensed class of Definition def:homog (b) IS the scalar "
                "class, which def:admissible-declaration (vi) already makes the entry "
                "type, so part (i) degenerates from a mathematical condition "
                "to a type check every well-formed declaration passes. It "
                "rejects nothing, and the constrained branch rests ENTIRELY on "
                "the attack_set_license attestation, which no program can "
                "verify"
            ),
            scalars=tuple(entry.scalar_bound for entry in declaration.constraint_list),
        )
    # TRUSTED-SOURCE MODE: part (i) IS the tag, at every d_A.
    unlicensed = [
        index
        for index, entry in enumerate(declaration.constraint_list)
        if not entry.is_homogeneous
    ]
    if unlicensed:
        return LicensedClassCheck(
            licensed=False,
            vacuous=False,
            reason=(
                f"entries {unlicensed} declare the `general` form of "
                "Definition def:homog -- a Hermitian Theta_k on A -- which is "
                "ADMISSIBLE INPUT and is NEVER LICENSED, at any d_A, so this "
                "list carries no key-length claim. THE VERDICT IS A TYPE CHECK "
                "ON THE DECLARED TAG AND COMPARES NO NUMBERS: an entry merely "
                "NEAR c_k tau_A would have been admissible under a numerical "
                "test and unsafe in a way no relaxation of this contract "
                "covers"
                + (
                    ". At d_A = 1 the check rejects only what a producer can "
                    "trivially avoid: every 1x1 Hermitian Theta_k equals "
                    "c_k tau_A (Proposition prop:trivial-alice-system (iii)), "
                    "so the entry could have been declared homogeneous with "
                    "the same condition (Remark rem:cgate)"
                    if declaration.alice_dim == 1
                    else ""
                )
            ),
            scalars=None,
        )
    scalars = tuple(entry.scalar_bound for entry in declaration.constraint_list)
    if declaration.alice_dim == 1:
        # prop:trivial-alice-system (iii): every 1x1 Hermitian Theta_k EQUALS
        # c_k tau_A, tau_A being [1], so the check that just passed rejects
        # nothing a producer could not have avoided: a passing part (i) here is
        # evidence of nothing (req:degenerate-gate-report).
        return LicensedClassCheck(
            licensed=True,
            vacuous=True,
            reason=(
                "DEGENERATE (Remark rem:cgate): at d_A = 1 part (i) is a type "
                "check that rejects nothing a producer cannot trivially avoid. "
                "Every entry is declared homogeneous, as the check requires at "
                "every d_A, but every 1x1 Hermitian Theta_k equals c_k tau_A "
                "(Proposition prop:trivial-alice-system (iii)), so a general "
                "entry could always have been declared homogeneous with the "
                "same condition. The pass is evidence of nothing, and the "
                "constrained branch rests ENTIRELY on the attack_set_license "
                "attestation, which no program can verify"
            ),
            scalars=scalars,
        )
    return LicensedClassCheck(
        licensed=True,
        vacuous=False,
        reason=(
            "a GENUINE restriction (Remark rem:cgate): in trusted-source mode "
            f"with d_A = {declaration.alice_dim} >= 2 the licensed class is the "
            "`homogeneous` tag, whose right-hand side c_k tau_A spans a "
            "one-dimensional subspace of the d_A^2-dimensional real space of "
            "Hermitian operators on A, and a declaration can fail it by "
            "declaring the `general` form instead"
        ),
        scalars=scalars,
    )


def homogeneous_scalars(
    declaration: ProtocolDeclaration,
) -> tuple[float, ...] | None:
    """Return ``(c_k)_k`` if every declared entry is in the licensed form.

    A convenience over :func:`licensed_class_check` for callers that only need
    the constants. It deliberately does NOT report whether the check was
    degenerate; a caller deciding anything on this alone should be using
    :func:`licensed_class_check` instead.
    """
    return licensed_class_check(declaration).scalars


def source_license_required(declaration: ProtocolDeclaration) -> bool:
    """Return whether Assumption A-SRC's attestation must be demanded.

    the `inputs` table and thm:constrained-accumulation: required whenever a
    ``tau_A`` is declared,
    EXCEPT at ``d_A = 1``, where Remark ``rem:modes-da1`` (b5) proves the
    licence vacuous -- "what it licenses is the condition ``tr omega = 1``,
    satisfied by every normalized state, so it deletes no attack. An
    implementation must not demand the attestation at ``d_A = 1``." In
    untrusted-source mode A-SRC is NOT ASSERTED and there is no attestation to
    demand.
    """
    return declaration.is_trusted_source and declaration.alice_dim > 1


def source_license_failure(declaration: ProtocolDeclaration) -> str | None:
    """Return the A-SRC gate's failure clause, or ``None`` when the gate opens.

    THE SINGLE STATEMENT OF THE A-SRC GATE. :func:`check_source_license` and
    :func:`check_key_length_permitted` both read the verdict AND the wording
    from here, rather than raising their own message from the same
    :func:`source_license_required` predicate, so the two entry points differ
    only in the scope they cover: this one gate, or every gate at once.
    """
    if not source_license_required(declaration):
        return None
    if declaration.source_replacement_license is not None:
        return None
    return (
        "(A-SRC) a tau_A is declared at d_A = "
        f"{declaration.alice_dim} >= 2 but the declaration carries no "
        "source_replacement_license (thm:constrained-accumulation). A trusted "
        "marginal DELETES from the feasible set every state whose A-marginal "
        "differs, hence every attack that would have produced one -- a "
        "different kind of input from an entry of L, and a more demanding one "
        "to justify -- so it is admitted into the security chain only behind a "
        "supplier attestation this module never verifies. The sound "
        "declaration without it is untrusted-source mode (the marginal slot "
        "left at `none`), which Remark transmitter/rem:source-mode (a) proves can only "
        "lower h_low"
    )


def check_source_license(declaration: ProtocolDeclaration) -> None:
    """Raise unless this declaration's A-SRC gate (thm:constrained-accumulation) opens.

    A scoped view of :func:`check_key_length_permitted`, reading its verdict
    from the same :func:`source_license_failure` clause: this function reports
    the A-SRC gate alone, which is what a caller inspecting the source-mode
    machinery wants, while the key-length entry point reports every gate at
    once.

    Raises:
        SecurityGateError: if a ``tau_A`` is declared at ``d_A >= 2`` without
            ``source_replacement_license``.
    """
    failure = source_license_failure(declaration)
    if failure is None:
        return
    raise SecurityGateError(
        "thm:constrained-accumulation: a declared tau_A must hard-fail before any "
        f"key-length output unless the A-SRC gate opens. Failing: {failure}"
    )


def constraint_gate_report(declaration: ProtocolDeclaration) -> dict[str, object]:
    """Return the two-part gate and the A-SRC gate as a machine-readable record.

    What it is for: ``req:degenerate-gate-report`` requires that a passing
    part (i) not read as evidence where it is degenerate, at ``d_A = 1`` and in
    untrusted-source mode (``rem:cgate``). A boolean in a log cannot carry
    that, so this record does -- it names the mode, the verdict, the
    degeneracy (under the key ``licensed_class_vacuous``) and the reason, and
    it travels into the ``optimizer_certificate`` a reader of a result sees.
    """
    check = licensed_class_check(declaration)
    licensed = declaration.attack_set_license is not None
    return {
        "source_mode": str(declaration.source_mode),
        "constraint_count": len(declaration.constraint_list),
        "licensed_class_passed": check.licensed,
        "licensed_class_vacuous": check.vacuous,
        "licensed_class_reason": check.reason,
        "attack_set_license_present": licensed,
        "attack_set_license_note": (
            "an attestation of Assumption A-ATK: not machine-checkable, never "
            "inspected beyond its presence"
        ),
        "source_replacement_license_required": source_license_required(declaration),
        "source_replacement_license_present": (
            declaration.source_replacement_license is not None
        ),
        "source_replacement_license_note": (
            "an attestation of Assumption A-SRC: not machine-checkable, never "
            "inspected beyond its presence; VACUOUS at d_A = 1 and NOT ASSERTED "
            "in untrusted-source mode, where it must not be demanded"
        ),
        "key_length_permitted": key_length_permitted(declaration),
    }


def key_length_permitted(declaration: ProtocolDeclaration) -> bool:
    """Return whether every gate opens (`inputs` table, thm:constrained-accumulation).

    A bare boolean, and deliberately not the whole story: where part (i) is
    degenerate a ``True`` here means only that nothing was rejected. Use
    :func:`licensed_class_check` or :func:`constraint_gate_report` when the
    distinction matters.
    """
    if source_license_failure(declaration) is not None:
        return False
    if not declaration.constraint_list:
        return True
    return (
        licensed_class_check(declaration).licensed
        and declaration.attack_set_license is not None
    )


def check_key_length_permitted(declaration: ProtocolDeclaration) -> None:
    """Raise unless a key-length output may be emitted for this declaration.

    EVERY failure found is reported, not the first: thm:constrained-accumulation gates
    the constraint list and the trusted marginal independently, and letting one
    mask the other would hide half of what a supplier still owes.

    Raises:
        SecurityGateError: naming each gate that failed. Both parts of the
            constraint gate are independently load-bearing -- membership of the
            licensed class without a licence is not enough, and a licence for an
            unlicensed list is not either -- and the A-SRC gate is independent
            of both.
    """
    failures: list[str] = []
    source_failure = source_license_failure(declaration)
    if source_failure is not None:
        failures.append(source_failure)
    if declaration.constraint_list:
        check = licensed_class_check(declaration)
        if not check.licensed:
            failures.append(f"(i) {check.reason}")
        if declaration.attack_set_license is None:
            failures.append(
                "(ii) the declaration carries no attack_set_license, the "
                "supplier attestation of Assumption A-ATK"
                + (
                    " -- and part (i) is "
                    + ("VACUOUS" if not declaration.is_trusted_source else "DEGENERATE")
                    + " here, so the gate rests entirely on this attestation "
                    "(Remark rem:cgate)"
                    if check.vacuous
                    else ""
                )
            )
    if not failures:
        return
    raise SecurityGateError(
        "the `inputs` table / thm:constrained-accumulation: a key-length output may be "
        "emitted only when every gate opens. Failing: "
        + "; ".join(failures)
        + ". The numerical value h_low(L) remains available -- numerical use "
        "outside the security chain is unrestricted -- but it must not reach "
        "Eq. eq:keylength, because the tightening h_low(L) >= h_low({}) is "
        "purchased entirely by A-ATK (Theorem thm:constrained-accumulation) "
        "and the marginal "
        "restriction entirely by A-SRC"
    )


def declaration_provenance_failure(compiled: CompilerEmission | None) -> str | None:
    """Return why a key length is withheld for want of provenance, or ``None``.

    ``req:compiled-declaration-only``: "The engine reports a key length ...
    only on a declaration that the protocol compiler emitted; on any other
    declaration it reports none." ``compiled`` is the run tier's token that
    the declaration is the compiler's emission
    (:class:`~certiqs_key.meat_core.provenance.CompilerEmission`); without it
    the length is withheld. A WITHHOLDING AND NOT A REFUSAL: the bound, the
    estimate and every other number stay on the record, as on every other
    closed gate. The reason opens with the code
    :data:`~certiqs_key.meat_core.reasons.DECLARATION_NOT_COMPILED`.
    """
    if compiled is not None:
        if not isinstance(compiled, CompilerEmission):
            raise TypeError(
                "compiled must be a CompilerEmission or None, got "
                f"{type(compiled).__name__}"
            )
        return None
    return (
        f"{DECLARATION_NOT_COMPILED} (req:compiled-declaration-only): no key "
        "length is reported, because the declaration did not arrive with the "
        "run tier's word (a CompilerEmission) that the protocol compiler "
        "emitted it. On a declaration from anywhere else the non-empty "
        "feasible set (def:admissible-declaration (vii)) is decided by no code "
        "path where constraints are declared, and nothing relates the "
        "declaration to the protocol being run. The bound and the estimate "
        "remain reported; this withholds the length and refuses nothing"
    )


def check_declaration_compiled(compiled: CompilerEmission | None) -> None:
    """Raise unless the declaration is known to be the compiler's emission.

    The form of :func:`declaration_provenance_failure` for the two
    declaration-level entry points below, which report every other closed
    gate as a :class:`SecurityGateError` too; the solver's record catches
    none of them and withholds instead.

    Raises:
        SecurityGateError: carrying :func:`declaration_provenance_failure`'s
            reason.
    """
    failure = declaration_provenance_failure(compiled)
    if failure is not None:
        raise SecurityGateError(failure)


def check_alpha_key_length(alpha: float) -> None:
    """Raise unless ``alpha`` lies in ``(1, 2)``: ``req:key-length-alpha-domain``.

    Every KEY-LENGTH statement is confined to that interval: the Renyi
    leftover-hashing import of C14 is stated there (``rem:alpha-domain``).
    Claims C3-C12, C16 and C17 individually hold on ``(1, inf)``, which is a
    different guard, ``req:objective-alpha-domain``, and lives in
    :mod:`certiqs_key.meat_core.objective.objective`.
    """
    if not 1.0 < alpha < 2.0:
        raise SecurityGateError(
            "Requirement req:key-length-alpha-domain: every key-length "
            "statement of this contract requires alpha in (1, 2); got "
            f"alpha={alpha!r}"
        )


def check_authentication_parameters(eps_auth: float, k_auth: int) -> None:
    """Raise unless ``eps_auth`` and ``k_auth`` lie in their declared domains.

    The `parameters` table, rows ``eps_auth`` -- ``[0, 1)``, default 0 -- and
    ``k_auth`` -- a non-negative integer number of bits, default 0. They are
    the parameters of Assumption ``ass:auth``: ``eps_auth`` bounds the
    scheme's error on an ideal key plus the distance of the key the run uses
    from an ideal one (clauses (iii)-(v)), and ``k_auth`` bounds the key the
    scheme consumes (clause (ii)). Neither enters Eq. ``eq:keylength``; they
    enter the security parameter and the net key of
    ``cor:composed-security`` (iii) and, ``eps_auth`` only, the gate of
    ``req:security-statement-not-vacuous``.

    The domain joint with the two budgets, ``eps_pa + eps_ev + 2 eps_auth < 1``,
    is :func:`check_security_statement`'s and is refused there with its own
    reason, not here.

    Raises:
        ValueError: on an ``eps_auth`` outside ``[0, 1)`` (NaN included) or a
            ``k_auth`` that is not a non-negative integer.
    """
    _check_authentication_error(eps_auth)
    _authentication_key_bits(k_auth)


def _check_authentication_error(eps_auth: object) -> None:
    """Raise ``ValueError`` unless ``eps_auth`` is a real number in ``[0, 1)``.

    A ``bool`` is refused, as for ``k_auth``, and so is any non-real value, so
    both parameters fail with the one documented error.
    """
    if (
        isinstance(eps_auth, bool)
        or not isinstance(eps_auth, numbers.Real)
        or not 0.0 <= float(eps_auth) < 1.0
    ):
        raise ValueError(
            f"the `parameters` table: eps_auth lies in [0, 1); got {eps_auth!r}"
        )


def _authentication_key_bits(k_auth: int) -> int:
    """Return ``k_auth`` as an ``int`` after checking it is a non-negative integer.

    ``operator.index`` admits every integer type (a NumPy integer included)
    and refuses a float, so a fractional bit count is refused rather than
    truncated; a ``bool`` is refused as the type error it is.
    """
    if isinstance(k_auth, bool):
        raise ValueError("the `parameters` table: k_auth is a non-negative integer")
    try:
        bits = operator.index(k_auth)
    except TypeError:
        raise ValueError(
            "the `parameters` table: k_auth is a non-negative integer; "
            f"got {k_auth!r}"
        ) from None
    if bits < 0:
        raise ValueError(
            f"the `parameters` table: k_auth is a non-negative integer; got {bits}"
        )
    return bits


def check_security_statement(
    eps_pa: float, eps_ev: float, eps_auth: float = 0.0
) -> None:
    """Raise unless the budgets leave a security statement to make.

    Requirement ``req:security-statement-not-vacuous``: a run whose budgets
    satisfy ``eps_PA + eps_EV + 2 eps_auth >= 1`` is REFUSED with
    ``security_statement_vacuous``, the sum decided exactly on the three
    declared numbers before any program is built, so before any solve and
    before any key length is computed. At the default ``eps_auth = 0`` this is
    the two-budget rule ``eps_PA + eps_EV >= 1``.

    WHY THE SUM AND WHY AT ONE. What a run reports is the
    ``(eps_PA + eps_EV + 2 eps_auth)``-security of Corollary
    ``cor:composed-security`` (iii), which at ``eps_auth = 0`` equals
    ``eps_PA + eps_EV``, the parameter of (ii) (and numerically of (i)). A
    statement with a parameter of one or more bounds the distinguishing
    advantage by one or more, which every protocol satisfies -- including the
    one that publishes the key -- so the statement distinguishes nothing and
    the length reported under it claims nothing. ``cor:keylength-bound`` (b)
    singles the corner out in its own proof and disowns it, and the
    ``eps_EV`` parameter row records it.

    EVERY BUDGET KEEPS ITS DECLARED DOMAIN and none is narrowed on its own:
    ``eps_EV = 1`` with a small ``eps_PA`` is refused and ``eps_EV = 0.75``
    with ``eps_PA = 0.2`` is not, because the predicate is on the SUM, which
    is what the security statement is stated in. The domain checks that
    precede this one are unchanged and still fire first, so a budget outside
    ``(0, 1]`` is still a ``ValueError`` and never this refusal; ``eps_auth``'s
    own domain ``[0, 1)`` is decided here, first, because the solve paths call
    this function before anything else and a negative ``eps_auth`` would make
    the sum the wrong number.

    THE SUM IS FORMED EXACTLY and never in binary64. The
    budgets are machine numbers and therefore dyadic rationals;
    :class:`fractions.Fraction` adds them, and doubles ``eps_auth``, without
    rounding, so the rule is decided on the quantity it is stated in rather
    than on a rounding of it.

    THE ARITHMETIC OF ``eq:keylength`` AND ``eq:keylength-h`` IS UNTOUCHED.
    This gate decides whether the expression is
    EVALUATED FOR A RUN, never what it evaluates to; the independent reference
    implementation in ``tests/oracles/reference.py`` carries no gate and the
    frozen registry is not edited, so the corner's arithmetic value remains
    checkable and checked.

    Raises:
        SecurityStatementVacuousError: on ``eps_pa + eps_ev + 2 eps_auth >= 1``,
            carrying ``reason = security_statement_vacuous``.
        ValueError: on an ``eps_auth`` outside ``[0, 1)``.
    """
    _check_authentication_error(eps_auth)
    # EXACTLY, ON THE THREE DECLARED BINARY64 NUMBERS READ AS THE DYADIC
    # RATIONALS THEY ARE, which is the row's own word and this module's
    # discipline everywhere else on declared data: a completeness sum that
    # rounds is refused, positivity is decided by a rational LDL rather than by
    # an eigenvalue, and the reason is the same one -- A COMPUTED QUANTITY IS
    # NOT THE QUANTITY A RULE IS ABOUT. The binary64 sum is a rounding of the
    # sum the rule is stated in, and the rounding is reachable: at
    # eps_PA = 1 - 2^-53 and eps_EV = 2^-54 the exact sum is 1 - 2^-54, below
    # one, while the computed sum ties-to-even to exactly 1.0 and would refuse
    # a run whose security statement is not empty. Such an error would be
    # one-sided in the refusing direction, so nothing would be overstated by
    # it; the exact sum is one line all the same.
    total = Fraction(eps_pa) + Fraction(eps_ev) + 2 * Fraction(eps_auth)
    if total >= 1:
        raise SecurityStatementVacuousError(
            "the `parameters` table: eps_PA + eps_EV + 2 eps_auth = "
            f"{eps_pa!r} + {eps_ev!r} + 2*{eps_auth!r} = {float(total)!r} "
            "(formed exactly) >= 1, so the (eps_PA + eps_EV + 2 eps_auth)-"
            "security statement of cor:composed-security (iii) -- at "
            "eps_auth = 0 the (eps_PA + eps_EV)-statement of (ii) -- is EMPTY: "
            "a distinguishing advantage bounded by one or more is bounded for "
            "every protocol, including one that publishes the key -- and NO "
            "KEY LENGTH IS REPORTED UNDER IT. cor:keylength-bound (b) excludes "
            "this corner rather than claiming it: its proof records that "
            "ell = 1 satisfies the expression at eps_PA = eps_EV = 1 under a "
            "security statement that is empty. THE ARITHMETIC IS NOT IN "
            "QUESTION and is unchanged; THE RUN IS REFUSED. Every budget keeps "
            "its domain and the refusal is on their SUM "
            "(req:security-statement-not-vacuous). A DISCLOSED SCOPE "
            "NARROWING",
            reason=RefusalReason.SECURITY_STATEMENT_VACUOUS,
        )


@dataclass(frozen=True)
class ComposedSecurity:
    """The two outputs ``cor:composed-security`` (iii) puts beside a key length.

    Emitted exactly when ``key_length`` is (the interface's ``outputs`` rows
    ``security_parameter`` and ``net_key_length``).
    """

    #: ``eps_PA + eps_EV + 2 eps_auth``, the parameter the reported key length
    #: carries, as the binary64 number AT OR ABOVE the exact sum: the value is
    #: a bound on a distinguishing advantage, and reporting it rounded down
    #: would understate it. At the dyadic budgets of every instance the sum is
    #: exact and nothing is rounded.
    security_parameter: float
    #: ``key_length - k_auth`` in bits, WITH NO CLAMP: zero or negative is the
    #: report that the run consumed at least as much pre-shared key as it
    #: produced.
    net_key_length: int


def _float_at_or_above(value: Fraction) -> float:
    """Return the binary64 number nearest ``value`` from above, or ``value`` itself.

    ``float`` of a :class:`fractions.Fraction` rounds to nearest, which may
    land below; one step up then gives the smallest binary64 number at or
    above the exact value.
    """
    nearest = float(value)
    if Fraction(nearest) < value:
        return math.nextafter(nearest, math.inf)
    return nearest


def composed_security(
    *,
    key_length: int,
    eps_pa: float,
    eps_ev: float,
    eps_auth: float = 0.0,
    k_auth: int = 0,
) -> ComposedSecurity:
    """Return ``security_parameter`` and ``net_key_length`` of an emitted length.

    Corollary ``cor:composed-security`` (iii): under Assumptions ``ass:auth``,
    ``ass:fixed`` and ``ass:conform``, run with the authentication
    post-processing over the classical channel of ``ass:auth``, the protocol
    is ``(eps_PA + eps_EV + 2 eps_auth)``-secure in the sense of Def. 3.8 of
    the cited source, and when both parties output an ``l``-bit key its net
    key gain is ``l_net = l - k_auth`` bits; for ``l_net <= 0`` the run yields
    no net key. The engine's ``key_length`` is exactly the case in which both
    parties output a key, so a caller calls this on every emitted length and
    on no other. The statement holds against an adversary whose memory has
    any dimension, whatever the order in which the source releases its
    signals, under the premises the run lists (A-SEQ with its clause (v),
    A-LAB at both parties and A-CONFORM among them): the corollary reaches
    every such adversary through ``lem:memory-lift`` and
    ``lem:honest-attacks``, so no premise on the adversary's memory is
    emitted.

    ``eps_auth`` is charged TWICE, by the triangle inequality of the
    corollary's proof; a tighter ``eps_PA + eps_EV + eps_auth`` is expected
    and not derived (design.md, Limitations). The parameter bounds ONE
    execution. The parameters of separate executions add under A-SEPARATE
    (``cor:separate-executions``); a key reused from one execution in
    another, for example to authenticate it, is not covered by that sum and
    enters through ``eps_auth``, which then includes that key's distance
    from an ideal key (``rem:repeated-executions``).

    At ``eps_auth = 0`` and ``k_auth = 0`` -- the defaults, which the report
    flags as an authentication error and a key consumption that are not
    counted -- the parameter is ``eps_PA + eps_EV`` and the net key is the key
    length.

    Raises:
        ValueError: on a parameter outside its declared domain, or a negative
            ``key_length``.
        SecurityStatementVacuousError: on ``eps_pa + eps_ev + 2 eps_auth >= 1``,
            where there is no security statement to report.
    """
    if key_length < 0:
        raise ValueError("the `outputs` table: key_length is a non-negative integer")
    if not 0.0 < eps_pa <= 1.0:
        raise ValueError("the `parameters` table: eps_pa lies in (0, 1]")
    if not 0.0 < eps_ev <= 1.0:
        raise ValueError("the `parameters` table: eps_ev lies in (0, 1]")
    check_authentication_parameters(eps_auth, k_auth)
    check_security_statement(eps_pa, eps_ev, eps_auth)
    parameter = Fraction(eps_pa) + Fraction(eps_ev) + 2 * Fraction(eps_auth)
    return ComposedSecurity(
        security_parameter=_float_at_or_above(parameter),
        net_key_length=key_length - _authentication_key_bits(k_auth),
    )


def key_length(
    *,
    rounds: int,
    h_low: float,
    lambda_ec: int,
    eps_ev: float,
    eps_pa: float,
    alpha: float,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
) -> int:
    """Return ``l_max`` of Remark ``rem:plus2``.

    Args:
        rounds: ``n >= 1``.
        h_low: bits per round, in ``[0, +inf]``. ``+inf`` raises; see the
            module docstring.
        lambda_ec: the error-correction transcript register length in bits.
            TOTAL, not per round: Assumption A-KEYREG fixes a fixed-length
            ``lambda_EC``-bit register (shorter transcripts padded, so
            ``dim(L_EC) = 2^{lambda_EC}`` exactly) and the chain-rule penalty of
            C14 counts that register DIMENSION rather than an average length.
        eps_ev: the correctness budget, in ``(0, 1]``.
        eps_pa: the secrecy budget, in ``(0, 1]``.
        alpha: the Renyi order, in ``(1, 2)`` (``req:key-length-alpha-domain``).
        ideal_hash: whether the privacy-amplification family is IDEAL
            two-universal (Assumption A-HASH). For a merely two-universal
            family the contract records a one-bit penalty, applied here when
            this is ``False``. Assuming the ideal family on a merely
            two-universal one is off by one bit in the unsafe direction
            (Requirement ``req:hash-penalty``).
        eps_auth: the authentication error bound of Assumption A-AUTH, in
            ``[0, 1)``, default 0. It does NOT enter the expression; it enters
            the gate of :func:`check_security_statement` and the security
            parameter of :func:`composed_security`.
        k_auth: the authentication key consumption of Assumption A-AUTH, a
            non-negative integer, default 0. It does NOT enter the expression;
            it is validated here so that a run declaring a bad one is refused
            before a length, and it enters only the net key of
            :func:`composed_security`.

    Raises:
        SecurityGateError: on ``h_low = +inf`` (no key-length claim may be
            emitted) or an ``alpha`` outside ``(1, 2)``.
        SecurityStatementVacuousError: on ``eps_pa + eps_ev + 2 eps_auth >= 1``,
            the corner gate of :func:`check_security_statement`.
        ValueError: on a parameter outside its declared domain.
    """
    # THE ORDER IS THE INTERFACE TABLE'S, AND THE TABLE IS THE ACCEPTED
    # ARTEFACT: `security_statement_not_vacuous` is order 7 and
    # `alpha_in_the_profile_domain` is order 8, so the corner is decided FIRST
    # and the Renyi order after it. The two solve paths resolve the pair
    # that way -- the corner gate is their first statement and alpha is
    # decided later, inside the key-length call -- and so do these two
    # functions, so the same pair of rules gives one answer whichever door a
    # caller uses. Nothing unsafe would follow otherwise, both rules refusing;
    # what cannot stand is a code path disagreeing with the table.
    if rounds < 1:
        raise ValueError("the `inputs` table: rounds must satisfy n >= 1")
    if lambda_ec < 0:
        raise ValueError("the `parameters` table: lambda_ec is a non-negative integer")
    if not 0.0 < eps_pa <= 1.0:
        raise ValueError("the `parameters` table: eps_pa lies in (0, 1]")
    if not 0.0 < eps_ev <= 1.0:
        raise ValueError("the `parameters` table: eps_ev lies in (0, 1]")
    check_authentication_parameters(eps_auth, k_auth)
    check_security_statement(eps_pa, eps_ev, eps_auth)
    check_alpha_key_length(alpha)
    if math.isnan(h_low) or h_low < 0.0:
        raise ValueError(f"the `outputs` table: h_low lies in [0, +inf]; got {h_low!r}")
    if math.isinf(h_low):
        raise SecurityGateError(
            "h_low = +inf reached Theorem thm:keylength. Remark "
            "rem:hlow-range: emit NO key-length claim and report the "
            "declaration/acceptance mismatch -- no accepted frequency vector "
            "is absolutely continuous with respect to any reachable "
            "Phi[omega], so Pr[Omega_AT] = 0 for every attack and there is no "
            "run on which a key would be produced"
        )
    # log2(1/eps) is written -log2(eps): the same real number, and it does not
    # overflow for an eps below 2^-1024, where 1.0/eps would become inf and turn
    # a finite deduction into a crash.
    bound = (
        rounds * h_low
        - lambda_ec
        - math.ceil(-math.log2(eps_ev))
        - (alpha / (alpha - 1.0)) * (-math.log2(eps_pa))
        + 1.0
    )
    if not ideal_hash:
        bound -= 1.0
    return max(0, math.floor(bound))


def _ceil_log2_reciprocal(epsilon: float) -> int:
    """Return ``ceil(log2(1/eps))`` for a machine ``eps`` in ``(0, 1]``, exactly.

    ``math.frexp`` splits ``eps = f 2^k`` with ``f in [0.5, 1)``, EXACTLY -- it
    is a bit-field read, not an approximation. Then
    ``log2(eps) in [k-1, k)``, with the left end attained exactly when
    ``f = 1/2``; in either case ``ceil(-log2(eps)) = 1 - k``, because ``1 - k``
    is an integer, ``-log2(eps) <= 1 - k`` and ``-log2(eps) > -k``. No
    logarithm is evaluated, so no rounding of one can move the ceiling across
    an integer.
    """
    return 1 - math.frexp(epsilon)[1]


def _log2_reciprocal_upper(epsilon: float) -> Fraction:
    """Return an exact rational at or ABOVE ``log2(1/eps)`` for ``eps`` in ``(0, 1]``.

    Two branches, and the split is what keeps the first-order key length both
    rigorous and tight:

    * ``eps = 2^{k-1}`` exactly -- which every declared budget in practice is,
      and every frozen fixture -- gives ``log2(1/eps) = 1 - k`` EXACTLY, an
      integer :func:`_ceil_log2_reciprocal` reads off ``math.frexp``. Using an
      enclosure here would throw away a whole key bit at every such parameter
      set, because the enclosure's upper endpoint sits strictly above an
      integer the true value attains.
    * otherwise the value is irrational. The term is SUBTRACTED, so what is
      needed is an UPPER bound, and this branch forms one in exact rational
      arithmetic on Python integers, trusting no libm (a ``math.log2``
      rounded up by one ulp would trust the platform's ``log2`` to one
      ulp). With ``eps = p / 2^k``, ``p`` odd of bit length ``L``,
      ``log2(1/eps) = k - (L - 1) - log2(r)`` for ``r = p / 2^(L-1)`` in
      ``[1, 2)``; ``ln r = 2 atanh(z)`` with ``z = (r - 1) / (r + 1)`` in
      ``[0, 1/3)``, whose series has positive terms, so a partial sum is a
      lower bound and the tail after ``J`` terms is at most
      ``2 z^(2J+1) / ((2J+1)(1 - z^2))``; the same series at ``z = 1/3``
      bounds ``ln 2`` from above. The result is rounded UP to
      :data:`_LOG2_BITS` fractional bits.

    What is fixed by the contract is the DIRECTION: the floor of a lower bound
    on the expression is at or below the floor of the true value, which is the
    conservative side (a float bound that rounds up across an integer boundary
    yields one bit too many). Corollary ``cor:fo-keylength`` fixes the formula
    and says nothing about how a transcendental term is bounded; this bound is
    rigorous, so it
    rests on no platform property.
    """
    numerator, denominator = epsilon.as_integer_ratio()
    shift = denominator.bit_length() - 1
    if numerator == 1:
        return Fraction(shift)
    length = numerator.bit_length()
    half = 1 << (length - 1)
    ln_r_low = _two_atanh_bounds(Fraction(numerator - half, numerator + half))[0]
    upper = shift - (length - 1) - ln_r_low / _LN2_UPPER
    scale = 1 << _LOG2_BITS
    return Fraction(-((-upper.numerator * scale) // upper.denominator), scale)


#: Fractional bits of the rigorous upper bound on ``log2(1/eps)``, and the
#: terms of the ``atanh`` series that reach them: ``9^-(J+1) < 2^-(BITS+8)``
#: at ``z < 1/3``.
_LOG2_BITS = 128
_ATANH_TERMS = math.ceil((_LOG2_BITS + 8) / math.log2(9)) + 1


def _two_atanh_bounds(
    z: Fraction, terms: int = _ATANH_TERMS
) -> tuple[Fraction, Fraction]:
    """Return rational lower and upper bounds on ``2 atanh(z)``, ``0 <= z <= 1/3``."""
    total = Fraction(0)
    square = z * z
    power = z
    for j in range(terms):
        total += power / (2 * j + 1)
        power *= square
    tail = power / ((2 * terms + 1) * (1 - square))
    return 2 * total, 2 * (total + tail)


#: An exact rational upper bound on ``ln 2 = 2 atanh(1/3)``.
_LN2_UPPER = _two_atanh_bounds(Fraction(1, 3))[1]


def _exact_first_order_floor(
    rounds: int,
    bound: float,
    lambda_ec: int,
    eps_ev: float,
    eps_pa: float,
    alpha: float,
    ideal_hash: bool,
) -> int:
    """Return ``floor`` of Eq. ``eq:keylength-fo``, evaluated over the rationals.

    ``bound`` is ``B = max{0, h_lb}``, the number Corollary
    ``cor:fo-keylength`` consumes.

    Every term but one is exact rational data: ``bound`` is a machine number
    and hence a rational, ``n`` and ``lambda_EC`` are integers,
    ``alpha/(alpha-1)`` is a quotient of machine numbers, and
    ``ceil(log2(1/eps_EV))`` is the integer :func:`_ceil_log2_reciprocal`
    returns without evaluating a logarithm.

    The one possibly-transcendental term, ``log2(1/eps_PA)``, is SUBTRACTED, so
    a lower bound on the whole expression needs an UPPER bound on it, which
    :func:`_log2_reciprocal_upper` supplies.

    ``floor`` is monotone, so the floor of a rigorous lower bound is at or below
    the floor of the true value -- the conservative direction, and the reason
    this does not merely re-derive the floating-point answer with more work.

    The arithmetic is :class:`fractions.Fraction`, from the standard library.
    """
    total = (
        rounds * Fraction(bound)
        - lambda_ec
        - _ceil_log2_reciprocal(eps_ev)
        - (Fraction(alpha) / (Fraction(alpha) - 1)) * _log2_reciprocal_upper(eps_pa)
        + 1
    )
    if not ideal_hash:
        total -= 1
    return math.floor(total)


def key_length_from_bound(
    *,
    rounds: int,
    h: float,
    lambda_ec: int,
    eps_ev: float,
    eps_pa: float,
    alpha: float,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
) -> tuple[int, bool]:
    """Return ``l_max`` of ``cor:keylength-bound``, and whether it clamped.

    ``eq:keylength-h``: ``thm:keylength``'s expression WITH NO NEW FLOOR, NO
    ADDITIONAL TERM AND NO EXACT ARITHMETIC, consuming ``max{0, h}`` in place
    of ``h_low`` for ANY ``h`` established to satisfy ``h <= h_low``.

    THE CORE ASSERTS NOTHING ABOUT WHERE ``h`` CAME FROM, and that is the whole
    of what this signature says. ``cor:keylength-bound``'s closing paragraph is
    the docking point: a second solver submodule -- a conic program with a dual
    certificate, say -- docks here with a DIFFERENT bound and a different trust
    root, and nothing of the core changes when it does. THE NAME AND THE
    PARAMETER SAY SO: they read ``key_length_from_bound`` and ``h``, where
    ``key_length_from_first_order`` and ``h_lb`` would make a conic submodule
    call the Frank-Wolfe function by name and pass its own bound as somebody
    else's bracket --
    exactly the coupling the split was made to remove.
    :func:`certiqs_key.solvers.frank_wolfe.general_keyrate.key_length_from_first_order`
    is the instance at ``h = h_lb``.

    THE CLAMP IS APPLIED BEFORE THE EXPRESSION and is reported beside the
    length: the caller's ``h`` carries the UNCLAMPED value and what reaches the
    expression is ``max{0, h}``. The clamp does not repair a bound that came
    out too high (``frank-wolfe/rem:fo-arithmetic``): a negative ``h`` is not
    unsound and is not repaired, it simply supports no positive length, which
    is clause (b) of ``cor:keylength-bound``.

    MONOTONICITY CARRIES VERBATIM. All four conclusions of ``prop:monotone``
    hold for this length, because the proof carries word for word with
    ``max{0, h}`` in place of ``h_low`` -- the bound depends on none of
    ``(lambda_EC, eps_EV, eps_PA)``.

    ``eps_auth`` AND ``k_auth`` ARE VALIDATED AND DO NOT ENTER THE EXPRESSION,
    as in :func:`key_length`: ``eps_auth`` enters the corner gate, and both
    enter the two outputs of :func:`composed_security` that the corollary's
    composed statement puts beside the length.

    Returns:
        ``(l_max, clamped)``, with ``clamped`` true exactly when ``h < 0``.

    Raises:
        SecurityGateError: on an ``alpha`` outside ``(1, 2)``.
            ``req:key-length-alpha-domain`` confines EVERY key-length statement
            to that interval, ``cor:keylength-bound`` named alongside
            ``thm:keylength`` when it does so.
        SecurityStatementVacuousError: on ``eps_pa + eps_ev + 2 eps_auth >= 1``,
            the corner gate of :func:`check_security_statement`. IT IS NOT A
            ``SecurityGateError`` and is not caught by the handlers that turn
            a closed gate into an absent length: the run is refused.
        ValueError: on a parameter outside its declared domain, or an ``h``
            that is NaN or ``+inf``. ``-inf`` is unreachable on a run that
            reports a bound at all and is accepted as the clamped case.
    """
    # THE ORDER IS THE INTERFACE TABLE'S, AND THE TABLE IS THE ACCEPTED
    # ARTEFACT: `security_statement_not_vacuous` is order 7 and
    # `alpha_in_the_profile_domain` is order 8, so the corner is decided FIRST
    # and the Renyi order after it. The two solve paths resolve the pair
    # that way -- the corner gate is their first statement and alpha is
    # decided later, inside the key-length call -- and so do these two
    # functions, so the same pair of rules gives one answer whichever door a
    # caller uses. Nothing unsafe would follow otherwise, both rules refusing;
    # what cannot stand is a code path disagreeing with the table.
    if rounds < 1:
        raise ValueError("the `inputs` table: rounds must satisfy n >= 1")
    if lambda_ec < 0:
        raise ValueError("the `parameters` table: lambda_ec is a non-negative integer")
    if not 0.0 < eps_pa <= 1.0:
        raise ValueError("the `parameters` table: eps_pa lies in (0, 1]")
    if not 0.0 < eps_ev <= 1.0:
        raise ValueError("the `parameters` table: eps_ev lies in (0, 1]")
    check_authentication_parameters(eps_auth, k_auth)
    check_security_statement(eps_pa, eps_ev, eps_auth)
    check_alpha_key_length(alpha)
    if math.isnan(h) or h == math.inf:
        raise ValueError(f"the `outputs` table: h lies in [-inf, +inf); got {h!r}")
    clamped = not (h >= 0.0)
    bound = 0.0 if clamped else h
    return (
        max(
            0,
            _exact_first_order_floor(
                rounds, bound, lambda_ec, eps_ev, eps_pa, alpha, ideal_hash
            ),
        ),
        clamped,
    )


def _ceil_log2(value: Fraction) -> int:
    """Return the least ``k`` with ``2^k >= value > 0``, comparing powers of two."""
    k = value.numerator.bit_length() - value.denominator.bit_length()
    while Fraction(2) ** k < value:
        k += 1
    while Fraction(2) ** (k - 1) >= value:
        k -= 1
    return k


def certified_key_length(
    *,
    rounds: int,
    h: Fraction,
    lambda_ec: int,
    eps_ev: float,
    eps_pa: float,
    alpha: float,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
) -> tuple[int, bool]:
    """Return ``l_max`` of ``def:max-key-length`` at ``max{0, h}``, exactly; the clamp.

    ``meat-core/frank-wolfe/req:certified-evaluation`` (vi), for the certified
    number ``h``: ``c = n h - lambda_EC - ceil(log2(1/eps_EV)) + 1`` exact (the
    ceiling by :func:`_ceil_log2`), and ``tau = (alpha/(alpha - 1))
    log2(1/eps_PA)`` exact where ``1/eps_PA`` is a power of two, otherwise
    enclosed in ``[L, U]`` by the ``atanh`` series and refined until
    ``floor(c - U) = floor(c - L)``, which is then ``floor(c - tau)``: ``tau``
    is irrational there, so the refinement ends. The parameters are refused
    exactly as :func:`key_length_from_bound` refuses them; ``ideal_hash``
    false subtracts the one bit it subtracts there.
    """
    key_length_from_bound(
        rounds=rounds,
        h=0.0,
        lambda_ec=lambda_ec,
        eps_ev=eps_ev,
        eps_pa=eps_pa,
        alpha=alpha,
        ideal_hash=ideal_hash,
        eps_auth=eps_auth,
        k_auth=k_auth,
    )
    clamped = h < 0
    c = rounds * max(Fraction(0), h) - lambda_ec - _ceil_log2(1 / Fraction(eps_ev)) + 1
    if not ideal_hash:
        c -= 1
    order = Fraction(alpha) / (Fraction(alpha) - 1)
    numerator, denominator = Fraction(eps_pa).as_integer_ratio()
    shift = denominator.bit_length() - 1
    if numerator == 1:
        return max(0, math.floor(c - order * shift)), clamped
    length = numerator.bit_length()
    half = 1 << (length - 1)
    z = Fraction(numerator - half, numerator + half)
    terms = _ATANH_TERMS
    while True:
        low_r, high_r = _two_atanh_bounds(z, terms)
        low_2, high_2 = _two_atanh_bounds(Fraction(1, 3), terms)
        whole = shift - (length - 1)
        low, high = order * (whole - high_r / low_2), order * (whole - low_r / high_2)
        if math.floor(c - high) == math.floor(c - low):
            return max(0, math.floor(c - high)), clamped
        terms *= 2


def key_length_for_declaration(
    declaration: ProtocolDeclaration,
    h_low: float,
    *,
    compiled: CompilerEmission | None = None,
    alpha: float | None = None,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
) -> int:
    """Return ``l_max`` for a declaration, after every gate.

    The entry point a caller should use: it applies the two-part constraint
    gate, the parameters the declaration carries with their own gates, and
    LAST the provenance gate of ``req:compiled-declaration-only``
    (``compiled``, the run tier's token that the compiler emitted the
    declaration; without it no length), so that every other gate keeps its
    reason.

    ``alpha`` must be the SAME order the supplied ``h_low`` was computed at.
    Eq. ``eq:keylength`` uses one Renyi order in both places -- inside
    ``h_low(alpha)`` and inside the deduction
    ``(alpha/(alpha-1)) log2(1/eps_PA)`` -- because both come from the same
    accumulation and leftover-hashing chain. It defaults to the declared
    parameter, and passing a different one than ``h_low`` was computed at would
    mix two chains.

    ``eps_auth`` and ``k_auth`` are the run's A-AUTH parameters (default 0);
    they are keyword inputs beside ``ideal_hash`` rather than fields of the
    declaration's parameters, because the operator bundle a declaration
    travels in carries no slot for them.
    """
    check_key_length_permitted(declaration)
    parameters = declaration.parameters
    length = key_length(
        rounds=declaration.rounds,
        h_low=h_low,
        lambda_ec=parameters.lambda_ec,
        eps_ev=parameters.eps_ev,
        eps_pa=parameters.eps_pa,
        alpha=parameters.alpha if alpha is None else alpha,
        ideal_hash=ideal_hash,
        eps_auth=eps_auth,
        k_auth=k_auth,
    )
    # req:compiled-declaration-only, decided LAST, as on the solve path, so
    # that every other closed gate (the constraint and A-SRC gates, the alpha
    # domain, the corner) keeps its own reason.
    check_declaration_compiled(compiled)
    return length


def key_length_from_bound_for_declaration(
    declaration: ProtocolDeclaration,
    h: float,
    *,
    compiled: CompilerEmission | None = None,
    alpha: float | None = None,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
) -> tuple[int, bool]:
    """Return ``l_max`` from ANY lower bound, after every gate.

    ``cor:keylength-bound`` is stated under the hypotheses of ``thm:keylength``,
    so the SAME gates apply: the two-part constraint gate of the `inputs`
    table, the A-SRC gate of thm:constrained-accumulation, the ``alpha in
    (1, 2)`` confinement of ``req:key-length-alpha-domain``, and last the
    provenance gate of ``req:compiled-declaration-only`` (``compiled``). A
    better bound never lifts a gate -- the tightening
    ``h_low(L) >= h_low({})`` is still purchased entirely by A-ATK, and the
    marginal restriction entirely by A-SRC.
    """
    check_key_length_permitted(declaration)
    parameters = declaration.parameters
    length = key_length_from_bound(
        rounds=declaration.rounds,
        h=h,
        lambda_ec=parameters.lambda_ec,
        eps_ev=parameters.eps_ev,
        eps_pa=parameters.eps_pa,
        alpha=parameters.alpha if alpha is None else alpha,
        ideal_hash=ideal_hash,
        eps_auth=eps_auth,
        k_auth=k_auth,
    )
    # req:compiled-declaration-only, decided LAST, as on the solve path, so
    # that every other closed gate (the constraint and A-SRC gates, the alpha
    # domain, the corner) keeps its own reason.
    check_declaration_compiled(compiled)
    return length
