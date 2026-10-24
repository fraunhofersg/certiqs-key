"""Library model ``depolarized_bell_pair``: exact, and not a QBER.

ONE MODEL for the qubit instance and a protocol document. The
text below is the instance's own.

spec/architecture.md 6 asks the qubit instance for "an analytic honest
distribution from the simulator". This module is that simulator, at its
smallest: one depolarizing qubit channel, evaluated in EXACT RATIONAL
ARITHMETIC against the declaration a compilation actually emitted.

WHAT THE PROVIDER EMITS, AND WHY IT IS NOT A QBER
=================================================
spec/architecture.md 4.3, on the normalized statistics artifact: "integer count
vector and explicit outcome alphabet, when counts exist; **total channel uses,
not merely sifted detections**; basis/test/generation counts ... QBER may be a
derived diagnostic. **It is not the general statistics interface.**"
spec/architecture.md 3.4 puts the same requirement on exactly this
provider and names the reason: a BB84 profile whose reduction makes ``Pr[T = gen]``
state-dependent must use the ``output_state`` test-statistics model (Assumption A-TSM)
and keep that mass inside ``Phi[omega]``.

So :func:`honest_distribution` returns a probability PER TOTAL CHANNEL USE on the
declared acceptance alphabet -- the ``p`` of an ``n * p`` framing, where ``n`` is
the round count and every declared outcome, the discarded ones included, carries
its own share of the mass. It sums to one over the WHOLE alphabet, never over a
sifted subset. :func:`sifted_error_rate` exists, is documented as a DIAGNOSTIC,
and is consumed by nothing here: it is the derived number a human reads, not the
interface.

THE STATE, AND WHERE ITS PARAMETER LIVES
========================================
Source replacement (spec/architecture.md 4.3) puts a trusted virtual source
system beside the transmitted one, and the honest channel acts on the
transmitted half. The honest joint state is the Werner family

    omega(Q) = v |Phi^+><Phi^+| + (1 - v) 1/4 ,        v = 1 - 2 Q ,

with ``|Phi^+> = (|00> + |11>)/sqrt2`` the state the BB84 specification's own
source-replacement certificate declares. ``Q`` is the SINGLE-BASIS ERROR
PARAMETER of the channel and a rational in ``[0, 1/2)``; it is a parameter of the
model, not an observed frequency, and this module never reads one.

Two facts about that family are checked rather than assumed, because both are
what make the honest state an admissible input:

* its ``A``-marginal is ``1_A / 2``, which is the ``tau_A`` the compiler emitted.
  :func:`honest_distribution` compares them EXACTLY and refuses on a mismatch --
  an honest state that misses the declared marginal is outside the feasible set
  of Eq. ``eq:feas`` and would produce a distribution no state can realise;
* the projector is exact: ``|Phi^+>`` has irrational amplitudes and a perfectly
  rational projector, which is why
  :func:`certiqs_key.foundations.exact.outer_projector` never takes the square root.

THE DISTRIBUTION IS THE EMITTED DECLARATION'S OWN
=================================================
``Phi_D[omega]`` is computed by :func:`certiqs_key.protocol_compiler.phi_distribution`
on the CandidateDeclaration a compilation emitted -- its POVMs, its announcements, its
acceptance-statistic table. Nothing is re-derived here from the specification, so the
provider cannot drift from what was actually compiled: a change to the compiler's
emission changes this distribution in the same commit, and a regression shows up as a
wrong number rather than as two consistent-looking halves.

``certiqs_key.foundations.exact`` is reached by its full module path. The compiler
package re-exports the substrate's constructors (``matrix``, ``vector``, ``Cx``)
but not the arithmetic this module needs (``add``, ``scale``,
``partial_trace_second``, ``outer_projector``), so the import is by module and is
named here rather than left to look accidental.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any, ClassVar, cast

from certiqs_key.foundations.exact import (
    Matrix,
    add,
    equal,
    identity,
    outer_projector,
    partial_trace_second,
    scale,
    vector,
)
from certiqs_key.protocol_compiler import (
    CandidateDeclaration,
    joint_distribution,
    phi_distribution,
)
from certiqs_key.runs.errors import RunError
from certiqs_key.runs.pipeline import (
    HonestProvider,
    RawJointProvider,
    factored_loss_applied,
    raw_factored_loss_applied,
)
from instances.common.honest.interface import HonestContext, precondition

__all__ = [
    "MODEL",
    "PHI_PLUS",
    "DepolarizedBellPair",
    "HonestModelError",
    "depolarized_state",
    "honest_distribution",
    "honest_provider",
    "raw_joint_distribution",
    "raw_joint_provider",
    "sifted_error_rate",
    "visibility",
]


class HonestModelError(RunError):
    """The honest channel model was asked for something it does not model.

    A Q outside the model's domain, a declaration this provider does not model,
    an honest state whose marginal is not the declared one. It derives from
    :class:`~certiqs_key.runs.errors.RunError` so that ``except RunError``
    still catches everything a run can raise, whichever tier raised it.
    """


#: ``|Phi^+><Phi^+|`` on ``A (x) Q``, exactly, with ``A`` first. The amplitudes
#: and squared norm are the ones the BB84 specification's own
#: source-replacement certificate declares.
PHI_PLUS: Matrix = outer_projector(vector([1, 0, 0, 1]), Fraction(2))

#: ``1_{AQ} / 4``: the fully depolarized end of the family, at ``v = 0``.
_MAXIMALLY_MIXED: Matrix = scale(Fraction(1, 4), identity(4))


def visibility(qber: Fraction) -> Fraction:
    """Return the channel visibility ``v = 1 - 2Q`` of the depolarizing model."""
    return 1 - 2 * _checked_qber(qber)


def depolarized_state(qber: Fraction) -> Matrix:
    """Return ``omega(Q)`` on ``A (x) Q``, exactly, with ``A`` first.

    The subsystem order is the one contract Section 2.5 fixes and
    :mod:`certiqs_key.protocol_compiler.statistics` reads: states live on ``A Q`` with
    the ``A`` factor first, so the composite index of ``(i, q)`` is ``i * d_Q + q``.
    Reversing it produces a different -- and silently plausible -- table at every
    non-product state, and ``|Phi^+>`` is the symmetric case where it would not even
    show.
    """
    v = visibility(qber)
    return add(scale(v, PHI_PLUS), scale(1 - v, _MAXIMALLY_MIXED))


def _checked_declaration(declaration: CandidateDeclaration, state: Matrix) -> None:
    """Refuse a declaration this provider does not model, on three grounds.

    Split out so that the coarse distribution and the raw one refuse on
    exactly the same grounds rather than one of them checking less.
    """
    expected = declaration.alice_dim * declaration.q_dim
    if expected != 4:
        raise HonestModelError(
            "this provider models one qubit through a depolarizing channel, so "
            f"it applies to a declaration with d_A * d_Q = 4; this one has "
            f"d_A = {declaration.alice_dim} and d_Q = {declaration.q_dim}"
        )
    marginal = partial_trace_second(state, declaration.alice_dim, declaration.q_dim)
    if declaration.alice_marginal is None:
        raise HonestModelError(
            "the honest state carries a trusted A-marginal, but the declaration "
            "is in untrusted-source mode and declares none; the source-"
            "replacement model of spec/architecture.md 4.3 is a trusted-marginal "
            "one and nothing here stands in for a tau_A that was not declared"
        )
    if not equal(marginal, declaration.alice_marginal):
        raise HonestModelError(
            "the A-marginal of the honest state is not the declared tau_A. Such "
            "a state is outside Eq. eq:feas, so the distribution it induces is "
            "reachable by no feasible state and an acceptance set built around "
            "it would be unreachable (meat-core Remark rem:hlow-range)"
        )


def honest_distribution(
    declaration: CandidateDeclaration, qber: Fraction
) -> dict[str, Fraction]:
    """Return ``p_honest`` on the declaration's own acceptance alphabet.

    One exact rational per declared acceptance value, summing to one over the
    WHOLE alphabet -- discarded rounds included. See the module docstring for
    why that, and not a sifted QBER, is the interface.

    Raises:
        HonestModelError: if ``qber`` is outside ``[0, 1/2)`` or is not an exact
            rational; if the declaration is not a two-qubit source-replacement
            one, so that the honest state does not live on its ``A (x) Q``; or
            if the emitted ``tau_A`` is not the marginal of the honest state, in
            which case the state is outside Eq. ``eq:feas``'s feasible set and
            the distribution it induces is reachable by no feasible state.
    """
    state = depolarized_state(qber)
    _checked_declaration(declaration, state)
    statistics = phi_distribution(declaration, state)
    if statistics.total != 1:
        # thm:measurements-and-statistics (iv) makes it one
        raise HonestModelError(  # pragma: no cover
            f"Phi[omega] sums to {statistics.total}, not 1"
        )
    return dict(statistics.values)


def sifted_error_rate(
    distribution: Mapping[str, Fraction], *, error: str = "err", correct: str = "ok"
) -> Fraction:
    """Return ``err / (ok + err)``: a DERIVED DIAGNOSTIC and not the interface.

    spec/architecture.md 4.3: "QBER may be a derived diagnostic. It is not the
    general statistics interface." Nothing in this package consumes this
    function's value; it exists so that a human reading a run can see the
    familiar number, and so that the distinction between it and
    :func:`honest_distribution` is written down in code rather than only in
    prose.

    Raises:
        HonestModelError: if the two named outcomes carry no mass between them,
            in which case there is no sifted subset to take a rate over. There is
            no default to substitute (contract Section 2.5, ``fail_closed``).
    """
    for label in (error, correct):
        if label not in distribution:
            raise HonestModelError(
                f"{label!r} is not an outcome of this distribution "
                f"{sorted(distribution)}"
            )
    total = distribution[error] + distribution[correct]
    if total == 0:
        raise HonestModelError(
            f"the outcomes {correct!r} and {error!r} carry no mass, so there is "
            "no sifted subset to take an error rate over"
        )
    return distribution[error] / total


def _checked_qber(qber: Fraction) -> Fraction:
    """Return ``Q`` after the domain check, or refuse.

    The type annotation is checked at run time and not merely declared: a
    ``float`` reaching the exact substrate would be silently widened by
    :class:`~fractions.Fraction`'s constructor into the nearest binary rational,
    and the resulting distribution would be exact arithmetic on a number nobody
    wrote down.
    """
    if not isinstance(qber, Fraction):
        raise HonestModelError(
            f"Q is an exact rational; got {qber!r} of type {type(qber).__name__}. "
            "A float reaching the exact substrate would be widened silently into "
            "the nearest binary rational, and the resulting distribution would be "
            "exact arithmetic on a number nobody wrote down"
        )
    if not 0 <= qber < Fraction(1, 2):
        raise HonestModelError(
            f"Q lies in [0, 1/2); got {qber}. At Q = 1/2 the visibility is zero "
            "and the honest state is the maximally mixed one, which carries no "
            "correlation to build a key from"
        )
    return qber


def raw_joint_distribution(
    declaration: CandidateDeclaration, qber: Fraction
) -> dict[tuple[str, str], Fraction]:
    """Return ``P_D[omega]`` on the RAW OUTCOME PAIRS ``X x V``, exactly.

    A preparation offers "the honest per-round distribution over the raw
    outcome pairs ``X x V`` ... before any coarse-graining to the acceptance
    alphabet", because an error-correction estimate, a conditional entropy and
    any per-outcome view need it and the acceptance alphabet cannot express
    them: the compiler declares only the holder's raw key map.

    THE SAME STATE AND THE SAME DECLARATION as
    :func:`honest_distribution`, through the compiler's own
    :func:`~certiqs_key.protocol_compiler.joint_distribution` rather than a
    second derivation -- so the coarse distribution IS this one summed over the
    acceptance fibres, and a change to the compiler's emission moves both in
    the same commit. It is the object the acceptance-alphabet distribution is
    obtained from.

    Raises:
        HonestModelError: on the same three grounds
            :func:`honest_distribution` refuses on.
    """
    state = depolarized_state(qber)
    _checked_declaration(declaration, state)
    return joint_distribution(declaration, state)


def raw_joint_provider(qber: Fraction) -> RawJointProvider:
    """Return the raw ``X x V`` model at ``qber`` as a declaration-only callable.

    See :func:`raw_joint_distribution`: it is the
    object the acceptance-alphabet distribution is obtained from, and this
    model computes it, so a preparation returns a table rather than ``None``.
    """

    def provider(
        declaration: CandidateDeclaration,
    ) -> dict[tuple[str, str], Fraction]:
        return dict(raw_joint_distribution(declaration, qber))

    return provider


def honest_provider(qber: Fraction) -> HonestProvider:
    """Return the depolarizing model at ``qber`` as a declaration-only callable.

    Args:
        qber: the honest channel's single-basis error parameter, an exact
            rational in ``[0, 1/2)``. A MODEL parameter and never an observed
            frequency -- see the module docstring.
    """

    def provider(declaration: CandidateDeclaration) -> dict[str, Fraction]:
        return dict(honest_distribution(declaration, qber))

    return provider


class DepolarizedBellPair:
    """The library entry: a trusted qubit source and a declared qubit POVM.

    PRECONDITIONS: a trusted source with ``d_A = 2`` and one
    ``declared_povm`` station of dimension 2. The model's own checks on the
    emitted declaration (``d_A * d_Q = 4``, the declared marginal) stay where
    they are, in :func:`_checked_declaration`.
    """

    name: ClassVar[str] = "depolarized_bell_pair"
    parameters: ClassVar[tuple[str, ...]] = ("qber",)

    def note(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> dict[str, Any]:
        """Return the qubit instance's note, with ``instance`` from the context."""
        return {
            "instance": context.instance,
            "model": (
                "depolarizing qubit channel, evaluated exactly on the emitted "
                "declaration"
            ),
            "module": __name__,
            "overridden": False,
        }

    def preconditions(self, context: HonestContext) -> None:
        """Refuse anything but one trusted qubit and one declared qubit POVM."""
        source = context.source
        precondition(
            self.name,
            source is not None and source.kind == "trusted" and source.alice_dim == 2,
            "it replaces one trusted qubit source, so it needs a trusted source "
            "with d_A = 2",
        )
        precondition(
            self.name,
            len(context.stations) == 1
            and context.stations[0].kind == "declared_povm"
            and context.stations[0].dimension == 2,
            "it measures one qubit, so it needs exactly one declared_povm station "
            "of dimension 2",
        )

    def providers(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> tuple[HonestProvider, RawJointProvider | None]:
        """Return the acceptance and raw providers at ``bound["qber"]``."""
        # The model's own domain check refuses a value that is not an exact
        # rational (``HonestModelError``); the cast only names the type.
        qber = cast(Fraction, bound["qber"])
        # A declared qubit POVM compiles no receiver, so no factored loss
        # exists to apply (receiver/detector-imperfections/
        # req:loss-before-evaluation is vacuous here).
        return (
            factored_loss_applied(honest_provider(qber)),
            raw_factored_loss_applied(raw_joint_provider(qber)),
        )


#: The one instance of this model the registry holds.
MODEL = DepolarizedBellPair()
