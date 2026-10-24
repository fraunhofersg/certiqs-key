"""The two hard errors every module of this repository raises, in one place.

ONE PAIR FOR THE REPOSITORY. No module can import a sibling, so declaring the
pair once per module would duplicate the same two classes and the same two
paragraphs of motivation. :mod:`certiqs_key.foundations` is the floor every
package may import (PRINCIPLES.md section 4), and
:mod:`certiqs_key.foundations.exact` raises both, so the pair lives here and a
module re-exports what it raises.

ALMOST NOTHING IS AN ERROR. A failed validation rule produces a REFUSAL --
data, with a machine-readable reason, returned instead of an artifact -- and is
never raised. The distinction is load-bearing and must stay visible from the
outside: a refusal says "the declared data fail a named rule of this module's
interface"; an exception says "the argument is not a presentation of an input
the interface types at all, so no rule can be read against it". A caller must
not be able to turn a refusal into an exception or an exception into a reason
code, and no code path of this repository converts one into the other.

The two classes below are for exactly the two things that are not rule
failures.

:class:`MalformedInputError`
    An argument no rule can be tested against, so that refusing it would have
    to invent a reason string that no interface fixes -- a ragged matrix, an
    entry presented as a ``float`` where the substrate takes exact rationals
    (see :mod:`certiqs_key.foundations.exact`), a POVM list whose members do not all
    have the declared dimension, a coarse-graining that is not total.

:class:`HypothesisError`
    A stated hypothesis of the statement being evaluated does not hold, so the
    question has no answer rather than a negative one. The Loewner order
    compares HERMITIAN operators; a comparison whose left-hand side is not
    Hermitian has no truth value rather than the value ``False``, and returning
    ``False`` would report a failed certificate where none was tested.

NEITHER CLASS MAY EVER CARRY A REFUSAL REASON.
"""

from __future__ import annotations

__all__ = [
    "CertiqsError",
    "HypothesisError",
    "MalformedInputError",
]


class CertiqsError(Exception):
    """Base class for every hard error of this repository's modules."""


class MalformedInputError(CertiqsError):
    """An argument is not a presentation of an input the interface types.

    NOT a failed validation rule, and deliberately not one of the refusal
    reasons a module's ``reasons`` module spells. Every fail-closed rule is
    stated on declared data of declared shape, and a rule can only be negated
    by data the rule can be read against. A matrix presented with rows of
    differing length enumerates no operator, so ``M_v >= 0`` and
    ``sum_v M_v = 1_B`` are untestable rather than false.
    """


class HypothesisError(CertiqsError):
    """A stated hypothesis of the statement being evaluated does not hold.

    Distinct from a refusal. The Loewner comparisons this repository runs --
    ``blk M^{>N}_v >= p_v 1`` and ``Lambda^dagger(O^_k) bowtie_k c_k 1_B`` --
    are defined on Hermitian operators. Asking for one on a non-Hermitian
    left-hand side is asking a question no contract poses, and answering
    ``False`` would record a failed certificate where none was tested.
    """
