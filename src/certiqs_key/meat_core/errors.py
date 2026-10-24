"""Hard errors of the ``meat-core`` engine.

Every failure here is an exception. Nothing warns, repairs, or substitutes a
default: spec/architecture.md 3.6 requires bundle failures to be hard errors,
and spec/architecture.md 2.5 requires the same fail-closed posture at the output end.
The contract
adds two failures of its own that an implementation must reproduce -- the
``h_low = +inf`` branch of Remark ``rem:hlow-range`` and the two-part
constraint gate of the `inputs` table / thm:constrained-accumulation -- and
both raise from here.

A THIRD IS THE IMPLEMENTATION'S AND NOT THE CONTRACT'S:
:class:`SecurityStatementVacuousError` refuses the corner
``eps_PA + eps_EV + 2 eps_auth >= 1`` (``req:security-statement-not-vacuous``;
the two-budget rule at the default ``eps_auth = 0``), which the claims admit
and this implementation declines to run. It is declared as
a scope narrowing rather than presented as a contract failure, which is why it
is said here.
"""

from __future__ import annotations


class MeatError(Exception):
    """Base class for every ``meat-core`` failure."""


class DeclarationError(MeatError):
    """A protocol declaration is not admissible or violates an input-row domain.

    Admissibility is ``def:admissible-declaration``.

    Raised by ``certiqs_key.meat_core.declaration.validation``. The message names the
    offending component and the clause it violates.
    """


class UnsupportedDeclarationError(MeatError):
    """The declaration is well-formed but outside this implementation's coverage.

    Distinct from :class:`DeclarationError`: nothing is wrong with the input,
    the engine simply declines to answer rather than deciding something the
    accepted contract leaves open. Refusing is the fail-closed alternative to
    improvising: a scope narrowing is DISCLOSED and never folded into a result
    (spec/architecture.md 2.5).
    """


class SecurityGateError(MeatError):
    """A key-length output was requested on a path the contract forbids.

    The two cases, both from contract.tex: ``h_low = +inf`` reaching Theorem
    ``thm:keylength`` (Remark ``rem:hlow-range``: emit no key-length claim),
    and a nonempty constraint list without BOTH tau_A-homogeneity and
    ``attack_set_license`` (the `inputs` table, thm:constrained-accumulation
    "Interface consequence").
    """


class SecurityStatementVacuousError(MeatError):
    """The declared budgets leave no security statement for a run to make.

    ``eps_PA + eps_EV + 2 eps_auth >= 1`` (``eps_PA + eps_EV >= 1`` at the
    default ``eps_auth = 0``), decided at parameter validation -- before any
    solve and before any key length is computed -- and the run is REFUSED with
    :attr:`reason` ``security_statement_vacuous``.

    NOT A :class:`SecurityGateError`, and the distinction is the whole
    behaviour. A security gate withholds the KEY LENGTH and leaves ``h_low`` on
    the record -- numerical use outside the security chain is unrestricted
    (``rem:no-constraints``) -- and the Frank-Wolfe driver catches it to do
    exactly that. THIS REFUSES THE RUN: there is no number to report under a
    security statement nobody can use, so it must not be caught by the handler
    that converts a closed gate into a partial answer. It is a refusal in the
    sense of :class:`~certiqs_key.meat_core.reasons.RefusalReason` -- NO OUTPUT
    AT ALL -- and it carries its machine-readable reason like the others.

    THE ARITHMETIC IS UNTOUCHED. ``eq:keylength-h`` still computes what
    ``cor:keylength-bound`` says it computes, and the corner's value is still
    the claim's; what this refuses is the RUN that would advertise a
    first-order key-length claim at a parameter point ``cor:keylength-bound``
    (b) disowns in its own proof. A DISCLOSED SCOPE NARROWING, never a reading
    of a claim.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        """Store the machine-readable refusal reason beside the prose."""
        super().__init__(message)
        #: ``security_statement_vacuous``, the member of
        #: :class:`~certiqs_key.meat_core.reasons.RefusalReason`. A string
        #: rather than the enum, for the reason
        #: :class:`GradientHypothesisError` gives: this module imports nothing
        #: from ``reasons`` and the dependency must not be turned round.
        self.reason = reason


class CertificationRefusedError(MeatError):
    """A ``strict`` run not reported at the certified tier: refused, no key length.

    ``meat-core/frank-wolfe/req:certified-evaluation`` (viii); :attr:`reason`
    is ``certification_refused`` (the core interface's refusal row), and the
    message names the certified evaluation's reasons. A run without the strict
    option never refuses for this cause.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        """Store the machine-readable refusal reason beside the prose."""
        super().__init__(message)
        self.reason = reason


class SupportError(MeatError):
    """A gradient or oracle step left the declared support face.

    contract.tex Theorem ``thm:gradient`` (ii): gradients may be evaluated only
    at iterates whose support is maximal. spec/architecture.md 7.2 (5):
    directions or oracle returns that enlarge the working support, jump to an
    incomparable subface, or leave the declared sector layout are rejected --
    the run stops rather than continuing on an unvalidated face.
    """


class GradientHypothesisError(SupportError):
    """A hypothesis of Theorem ``thm:firstorder`` (ii) failed AT AN ITERATE.

    A :class:`SupportError` still, so every caller that already handled one
    keeps working; what it adds is :attr:`reason`, the machine-readable
    withdrawal string Requirement ``req:first-order-withdrawal`` names for that
    hypothesis. THAT IS THE WHOLE POINT OF THE SUBCLASS: a failed
    hypothesis WITHDRAWS ``h_lb`` and "LEAVES THE ESTIMATE" with a reason a
    consumer can route on, so the driver must be able to tell WHICH hypothesis
    failed from the exception alone rather than by matching prose.

    RAISING IS NOT THE FAIL-CLOSED BEHAVIOUR ON THE LIVE PATH and this class
    does not make it so. The gradient routines raise because they cannot return
    a number; it is the DRIVER that converts the failure into a withdrawal
    (:func:`certiqs_key.solvers.frank_wolfe.joint_driver.run_joint_frank_wolfe`),
    and a run
    that let this escape would report no result at all -- no estimate, no
    reason -- where spec/architecture.md 2.5 requires the estimate to survive.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        """Build the failure with the withdrawal reason it must carry."""
        super().__init__(message)
        #: The machine-readable withdrawal reason of Requirement
        #: ``req:first-order-withdrawal``. A string rather than the enum, because
        #: :mod:`certiqs_key.meat_core.reasons` imports nothing from here and
        #: the dependency must not be turned round.
        self.reason = reason


class SectorOperationError(MeatError):
    """A structure-changing operation on the declared sectors was refused.

    contract.tex Remark ``rem:classes`` permits exactly two: restriction of the
    K-sum to key-active sectors (an identity, C7) and deletion of a sector
    whose (RM1)-(RM3) hypotheses are checked (Theorem ``thm:removal``).
    Dropping a constraint-active sector (Proposition ``prop:retention``) and
    merging or averaging sectors (Proposition ``prop:no-averaging``) both
    overstate the key and have no code path.
    """


class HypothesisError(MeatError):
    """A claim's stated hypotheses do not hold, so its conclusion is not used.

    Raised by the alpha -> 1+ validation oracle of C16 when Theorem
    ``thm:oracle``'s hypotheses (H1) or (H2) fail: the conforming behaviour is
    to refuse the comparison, not to report a limit anyway.
    """
