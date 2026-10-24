"""Honest statistics given as data: a table, a raw joint table, an envelope.

WHY THIS IS LIBRARY CODE. Three places need the same few closures:
the run facade's honest override (a caller's table or envelope,
``runs/facade/core.py``), the decoy and bbm92 instances (a raw ``X x V`` table
pushed through the declaration's own announcement and acceptance maps) and the
protocol document's ``honest`` block, which offers exactly these forms besides
the library models, so they are written once, here.

NOTHING HERE WIDENS, TIGHTENS OR RENORMALISES. A table reaches the run's
``honest_provider`` injection point unchanged; the engine decides its
admissibility at the acceptance construction, and an envelope is Assumption
A-HON-ENV's ``HonestEnvelope`` as given.

A TABLE IS THE DEVICE'S STATISTICS AS GIVEN, so every provider built from one
here is declared to the run as applying every station's factored loss
(``receiver/detector-imperfections/req:loss-before-evaluation``;
:func:`~certiqs_key.runs.pipeline.factored_loss_applied`, and
:func:`~certiqs_key.runs.pipeline.raw_factored_loss_applied` for a raw
table's raw provider): it evaluates no emitted measurement, normalized or
not. :func:`aggregate` is not so declared, because what it aggregates is the
caller's: a model that builds a raw provider by evaluating the declaration
declares its own aggregate.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.runs.pipeline import (
    HonestProvider,
    RawJointProvider,
    factored_loss_applied,
    raw_factored_loss_applied,
)
from certiqs_key.statistics import HonestEnvelope

__all__ = [
    "aggregate",
    "envelope_provider",
    "raw_table_providers",
    "table_provider",
]


def aggregate(raw: RawJointProvider) -> HonestProvider:
    """Return the acceptance-alphabet provider a raw ``X x V`` provider induces.

    Each raw pair ``(x, v)`` is announced and accepted by the DECLARATION'S OWN
    maps (``announcement`` and ``acceptance_value``), so the coarse
    distribution is the raw one summed over the acceptance fibres and the two
    cannot drift. Every declared acceptance value is present, at zero where no
    raw pair lands on it.
    """

    def provider(declaration: CandidateDeclaration) -> dict[str, Fraction]:
        result = dict.fromkeys(declaration.acceptance_alphabet, Fraction())
        for (x, v), probability in raw(declaration).items():
            result[declaration.acceptance_value(declaration.announcement(x, v))] += (
                probability
            )
        return result

    return provider


def table_provider(table: Mapping[str, Fraction]) -> HonestProvider:
    """Return a provider that answers every declaration with ``table``, copied."""
    exact = dict(table)

    def provider(declaration: CandidateDeclaration) -> dict[str, Fraction]:
        return dict(exact)

    return factored_loss_applied(provider)


def raw_table_providers(
    table: Mapping[tuple[str, str], Fraction],
) -> tuple[HonestProvider, RawJointProvider]:
    """Return the acceptance and raw providers of a raw ``X x V`` table.

    The form a simulator's output takes: the raw table is offered as the run's
    raw provider, and the acceptance distribution is its :func:`aggregate`.
    """
    exact = dict(table)

    def raw(declaration: CandidateDeclaration) -> dict[tuple[str, str], Fraction]:
        return dict(exact)

    return factored_loss_applied(aggregate(raw)), raw_factored_loss_applied(raw)


def envelope_provider(
    lower: Mapping[str, Fraction], upper: Mapping[str, Fraction]
) -> HonestProvider:
    """Return a provider of the envelope ``[lower, upper]`` per acceptance label."""
    low, high = dict(lower), dict(upper)

    def provider(declaration: CandidateDeclaration) -> HonestEnvelope:
        return HonestEnvelope(lower=dict(low), upper=dict(high))

    return factored_loss_applied(provider)
