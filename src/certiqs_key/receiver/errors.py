"""Hard errors of the ``receiver`` module.

MOST FAILURES HERE ARE NOT ERRORS. The ``fail_closed`` convention
(``interface.yaml`` ``conventions``) says that "every failed validation
produces a refusal with a machine-readable reason and no artifact", and
Requirement ``req:residual-refusal`` says of a residual above its declared
tolerance that it "is a refusal, not a warning". A refusal is therefore DATA -- a
:class:`certiqs_key.receiver.reasons.Refusal` returned instead of an object -- and
it is never raised. The distinction is load-bearing: a caller must not be able
to turn a refusal into an exception, or an exception into a refusal reason,
because the two say different things. A refusal says "the declared data fail a
named check of this contract"; an exception says "the argument is not a
presentation of an input this contract types at all, so no check can be read
against it".

The two exceptions below are for exactly the things that are not check
failures.

* :class:`MalformedInputError` -- an argument no clause of the inputs table
  (``interface.yaml`` ``inputs``) can be tested against, so that refusing it
  would have to invent a reason: a ragged matrix, a non-square instrument
  matrix, a parameter that is neither an integer, a :class:`~fractions.Fraction`
  nor a ``float``, a port index outside the declared mode space.
* :class:`HypothesisError` -- a stated hypothesis of the theorem being
  evaluated does not hold, so the quantity being asked for has no value rather
  than a wrong one. Theorem ``thm:multiclick-bound`` is stated under
  Eq. ``eq:bbkhyp`` and ``gamma <= beta_k``; Lemma ``lem:fock-block-spectrum`` under
  ``0 <= A <= 1``; a probe conditioning under ``Gamma >= 0`` diagonal.
  Evaluating one of them outside its hypothesis is a programming error and is
  not reachable from a validated request, which checks the hypotheses first.

Neither is a refusal reason, and neither ever appears in an emitted artifact.
"""

from __future__ import annotations

__all__ = [
    "HypothesisError",
    "MalformedInputError",
    "ReceiverError",
]


class ReceiverError(Exception):
    """Base class for every ``receiver`` hard error."""


class MalformedInputError(ReceiverError):
    """An argument is not a presentation of an input this contract types.

    NOT a failed check, and deliberately not one of the refusal reasons of
    :mod:`certiqs_key.receiver.reasons`. Every validity condition of the inputs
    table is stated on declared data of a declared shape -- an ordered mode list,
    disjoint port sets, a square instrument matrix, a Hermitian Gram family --
    and a condition can only be negated by data the condition can be read
    against. A matrix presented with rows of differing length enumerates no
    operator, so ``Gamma^dagger Gamma <= 1`` is untestable rather than false.
    """


class HypothesisError(ReceiverError):
    """A stated hypothesis of the theorem being evaluated does not hold.

    Distinct from a refusal: a refusal is what the module emits when declared
    data fail a named check on well-typed input. This is what a caller gets for
    asking a question the contract does not pose -- the bound of Theorem
    ``thm:multiclick-bound`` on data violating Eq. ``eq:bounddata``, the spectrum of
    Lemma ``lem:fock-block-spectrum`` on an operator outside ``[0, 1]``, or a
    probe conditioning at a negative mean photon number.
    """
