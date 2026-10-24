"""The hard errors this module raises, re-exported from ``foundations.errors``.

ALMOST NOTHING HERE IS AN ERROR. "Every failed validation produces a refusal
with a machine-readable reason and NO ARTIFACT. No default is substituted for a
missing datum, no weight is clipped into range, no fibre condition is waived,
and no licence is emitted without its certificate." A refusal is therefore DATA
-- a :class:`certiqs_key.reductions.reasons.Refusal` carrying one of the
strings the interface fixes verbatim -- and it is never raised. The distinction
is load-bearing and must stay visible from the outside: a refusal says "the
declared data fail a named fail-closed rule"; an exception says "the argument is
not a presentation of an input the interface types at all, so no rule can be
read against it".

THE CLASSES LIVE IN FOUNDATIONS, THE DISTINCTION IS THIS MODULE'S.
:class:`MalformedInputError` and :class:`HypothesisError` are raised by
:mod:`certiqs_key.foundations.exact` -- the exact substrate, at the floor every
module imports -- so they live in :mod:`certiqs_key.foundations.errors` and
this file re-exports what this module raises. The base class is
:class:`certiqs_key.foundations.errors.CertiqsError`, re-exported here as
:data:`ReductionsError`: a base class per module could not be a base class of an
error the shared substrate raises.

NEITHER CLASS MAY EVER CARRY A REFUSAL REASON, and no code path converts one
into the other. That is what keeps "the module refused this declaration" and
"the caller handed the module something it does not type" two different
statements to a consumer.
"""

from __future__ import annotations

from certiqs_key.foundations.errors import (
    CertiqsError,
    HypothesisError,
    MalformedInputError,
)

__all__ = [
    "HypothesisError",
    "MalformedInputError",
    "ReductionsError",
]

#: The base class of every hard error this module raises. It is the shared one:
#: see the module docstring for why a per-module base could not be.
ReductionsError = CertiqsError
