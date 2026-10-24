"""Exact data at the module boundary: the exact-rational verdict.

Implements ``def:conservative-evaluation``'s input half: an evaluation is
conservative when ``p^hon`` (or the envelope's vectors), ``ecomp`` and the
allocation ARE exact rationals, and every tail comparison an endpoint rule
makes is decided either exactly or against a bound that rounds the tail
UPWARD. The input half is decided here and refused with
``inputs_not_rational`` (``binomial-box/req:input-refusal``). The conventions of
``interface.yaml`` ("Exact arithmetic") say the same of the output side: "every
number this module emits is an exact rational".

WHY THIS FILE EXISTS BESIDE ``certiqs_key.foundations.exact``, WHICH HAS THE SAME
QUESTION AND A DIFFERENT ANSWER
===========================================================================
``foundations.exact.as_rational`` RAISES
:class:`~certiqs_key.foundations.errors.MalformedInputError` on a value that is not
an exact rational; :func:`as_exact_rational` below RETURNS ``None``. That is
not a style difference, it is the two modules' fail-closed semantics, and
neither may be substituted for the other:

* for ``foundations`` an inexact operator entry is a MALFORMED PRESENTATION -- there
  is no rule of any fail-closed table it can be read against, so refusing is
  the only conforming answer and an exception is the shape of a refusal;
* for this module an inexact ``p^hon``, ``ecomp`` or allocation entry is an
  INPUT-DOMAIN VIOLATION with a machine-readable code of its own,
  ``inputs_not_rational`` (Theorem ``thm:honest-containment`` (iii)), reported as DATA
  beside a construction that emitted no acceptance set. An exception here would make
  the tenth of ten codes unreachable, and
  :mod:`certiqs_key.statistics.errors` says in as many words that a caller must
  not be able to turn a refusal into a report code or a report code into a
  refusal.

So the predicate is shared in substance and the VERDICT TYPE is this module's.
What is NOT duplicated is anything either module could import: this file holds
one function and one alias.

WHAT COUNTS AS AN EXACT RATIONAL HERE, AND WHY A ``float`` DOES NOT
==================================================================
:func:`as_exact_rational` accepts anything Python registers as
``numbers.Rational`` -- ``int``, :class:`fractions.Fraction`, and the integer
types NumPy registers with that ABC -- and REFUSES everything else, ``float``
included. The refusal is the ``inputs_not_rational`` code of Theorem
``thm:honest-containment`` (iii) and it is a deliberate reading of a real subtlety.

A binary64 value *is* an exact rational -- a dyadic one -- so accepting it
would not violate the letter of ``def:conservative-evaluation``. What
violates it is presenting a float as if it were the intended value: ``0.1``
read as ``1/10`` is the one thing the exact-data condition rules out, because
the two differ and the comparison against a budget is decided by the
difference. A
``float`` argument carries no record of which of the two rationals its author
meant, so accepting one would make this module decide that on the caller's
behalf, silently, on every coordinate of ``p^hon``. Refusing costs the caller
one explicit conversion -- ``Fraction(1, 10)`` for the intended value,
``Fraction(0.1)`` for the dyadic one -- and that conversion is the caller
SAYING which rational it means.

THE TWO DIRECTED ROUNDINGS ARE NOT HERE
=======================================
The only place a number leaves the module as a machine number is the docking
adapter. THAT ADAPTER IS THE CONSUMER'S
(:mod:`certiqs_key.meat_core.docking_statistics`), so the directed roundings
live with it and this package has NO FLOATING-POINT PATH IN EITHER DIRECTION,
which is what ``conventions.no_binary64_anywhere`` of ``interface.yaml``
requires of it. The adapter imports
``certiqs_key.meat_core.acceptance.geometry``'s copy of the same construction
rather than carrying a third.
"""

from __future__ import annotations

import numbers
from fractions import Fraction

__all__ = [
    "Rational",
    "as_exact_rational",
]

#: What a caller may hand this module where the contract says "exact rational".
#: The runtime check is :func:`as_exact_rational`, which is stricter than this
#: alias can express: it also refuses a ``float``, which no annotation does.
Rational = Fraction | int


def as_exact_rational(value: object) -> Fraction | None:
    """Return ``value`` as an exact :class:`~fractions.Fraction`, else ``None``.

    ``None`` is the ``inputs_not_rational`` verdict of Theorem
    ``thm:honest-containment`` (iii), which the caller turns into an
    ``infeasibility_report``. See the module docstring for why a ``float`` is refused
    rather than converted, and why the verdict is a value here and an exception in
    ``foundations``.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, numbers.Rational):
        # int, bool and the NumPy integer types register here. Rebuilding from
        # the two integer parts keeps the result a plain Fraction whatever the
        # concrete type was.
        return Fraction(int(value.numerator), int(value.denominator))
    return None
