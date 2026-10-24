"""The assumption ledger this module emits with every acceptance set.

``interface.yaml``, ``assumption_ledger``: the own rows, "emitted as the
`assumption_ledger` output key: the machine key of each row below, as
`emission_rule` says". The emission is the interface's own
(``fixed_by_this_file``, the ``assumption_ledger (the emission)`` row): no
claim says the keys are emitted, and this module emits a ledger because the
transmitter, reductions, compiler and meat-core artefacts all do and a run
manifest is assembled from them (spec/architecture.md section 4.4).

EVERY ROW IS TRANSCRIBED FROM THE INTERFACE, short id, machine key and owner,
and ``never_verified`` IS READ FROM THE ASSUMPTION'S ``verification`` HEADER
FIELD (spec/claim-format.md section 3.2) through the shipped claim-closure
table, by machine key; the interface's ``never_verified`` block lists the
same rows. A-HON, A-HON-ENV and A-REACH are honest-model premises the
completeness argument consumes and no code path decides; A-ALPHABET is the
clause that the run records an acceptance value in every round
(``ass:alphabet``), which no code path decides. Two conditions are no
assumption and carry no row: that the alphabet, its enumeration and the round
count are the consuming declaration's is ``def:matched-alphabet``, decided by
``req:matched-alphabet`` at bundle validation (``runs.pipeline``), and exact
data with conservative tail comparisons is ``def:conservative-evaluation``,
whose input half ``binomial-box/req:input-refusal`` decides
(:func:`certiqs_key.statistics.exact.as_exact_rational`).

EVERY MACHINE KEY IS AN IDENTIFIER. The honest-model rows are not
``key = value`` readings of the ``honest_model`` record
(``honest_model = iid_honest_rounds``), prose a report could not key on; they
are ``honest_rounds_iid`` (A-HON) and
``honest_rounds_within_envelope`` (A-HON-ENV), and which honest model the
figure was computed under is the ``honest_model`` value the row binds.

THE ROWS FOLLOW THE ROUTE THAT PRODUCED THE ACCEPTANCE SET (``emission_rule``): a row is
emitted where a result this module reports rests on it, and nowhere else, so that what a
run lists is what its results assume (the route-exact set). The key is the route,
not the bare geometry tag: a ``polytope`` a profile declared would rest on
none of the box's results, and keying on the tag would list them for it.

* :attr:`AcceptanceRoute.CONSTRUCTED_BOX` -- the canonical box the
  construction map emits: A-HON-ENV, A-ALPHABET and A-REACH. The emitted
  completeness figure is the one of ``binomial-box/thm:completeness-bound``,
  which assumes A-HON-ENV and A-ALPHABET; the box's honest containment is
  ``binomial-box/thm:honest-containment``, which assumes A-ALPHABET and
  A-REACH; the emitted acceptance support is ``thm:box-oracle`` (i)'s, which
  assumes A-ALPHABET. A-HON is not emitted: none of them declares it, and a
  one-law run is the degenerate envelope, for which A-HON-ENV is A-HON
  (``lem:hon-degenerate``); the bound ``honest_model`` value
  (``iid_honest_rounds``) says so.
* :attr:`AcceptanceRoute.DECLARED_SINGLETON` -- a declared singleton, which
  the construction map never emits (``singleton/rem:singleton-honest``):
  A-HON and A-ALPHABET, the two ``singleton/thm:singleton-completeness``
  declares. Its honest input is the point form only
  (``singleton/req:singleton-point-form``), so an envelope is refused here.

THERE IS NO INHERITED A-TSM ROW. No theorem, lemma, proposition,
corollary or definition of this module rests on ``reductions/ass:tsm``: only
the remarks ``binomial-box/rem:sound-indep`` and
``binomial-box/rem:guard-activation`` declare it, and no completeness result
reaches it. The reductions artefact emits A-TSM where its own claims rest on
it.

EACH ROW CARRIES THE DECLARED VALUES ITS ASSUMPTION'S CLAUSES ARE ABOUT
(``constrains``, as the receiver's ledger rows do; the values are bound per assumption).
Each name is an input of the inputs table, or ``honest_model``, the tag of the output
record of that name. THE VALUES ARE IMMUTABLE: strings, integers and tuples of ``(name,
value)`` pairs, exact rationals written ``"p/q"``, so a row, and the construction that
carries it, stays hashable and cannot be altered after it is emitted. The run tier turns
the pairs into JSON objects when it writes a record.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from types import MappingProxyType
from typing import Final

from certiqs_key.domain.claim_closure import never_verified
from certiqs_key.statistics.errors import HypothesisError, MalformedInputError

__all__ = [
    "EMISSION_BY_ROUTE",
    "ENVELOPE_MODEL_TAG",
    "HONEST_MODEL_TAG",
    "LEDGER_CLAIMS",
    "LEDGER_IDS",
    "MACHINE_KEYS",
    "AcceptanceRoute",
    "AssumptionLedgerRow",
    "assumption_ledger",
    "honest_model_tag",
]

#: The value of the ``honest_model`` tag under Assumption A-HON: the honest
#: law of a point form or of a degenerate envelope. Defined here, beside the
#: ledger that binds it, and re-exported by
#: :mod:`certiqs_key.statistics.construction`, whose record carries it.
HONEST_MODEL_TAG: Final[str] = "iid_honest_rounds"

#: The tag under A-HON-ENV, recorded when the honest envelope is NOT
#: degenerate. A degenerate envelope is A-HON (``statistics/lem:hon-
#: degenerate``) and keeps :data:`HONEST_MODEL_TAG`, so a one-law record reads
#: as it always has.
ENVELOPE_MODEL_TAG: Final[str] = "envelope_honest_rounds"


class AcceptanceRoute(StrEnum):
    """The route that produced an acceptance set, which decides its ledger."""

    #: The canonical box of ``binomial-box/def:construction``: every result of
    #: :func:`certiqs_key.statistics.construction.construct`.
    CONSTRUCTED_BOX = "constructed-box"
    #: A singleton a profile declares (``singleton/thm:singleton-completeness``);
    #: no code path emits one today.
    DECLARED_SINGLETON = "declared-singleton"


@dataclass(frozen=True)
class AssumptionLedgerRow:
    """One emitted ledger row: its owner, whether anyone decides it, its values."""

    assumption_id: str
    machine_key: str
    never_verified: bool
    #: The module that owns the assumption: ``statistics`` for every row.
    owner: str
    #: The claim that states the assumption, ``<module>/<label>``.
    claim: str
    #: The declared values the assumption's clauses are about, as immutable
    #: ``(name, value)`` pairs (the module docstring).
    constrains: tuple[tuple[str, object], ...] = ()


#: Every short id this ledger can emit, in the interface's ``own_rows`` order.
LEDGER_IDS: Final[tuple[str, ...]] = ("A-HON", "A-HON-ENV", "A-ALPHABET", "A-REACH")

#: The machine key of each, as the interface's ``own_rows`` give it.
MACHINE_KEYS: Final[Mapping[str, str]] = MappingProxyType({
    "A-HON": "honest_rounds_iid",
    "A-HON-ENV": "honest_rounds_within_envelope",
    "A-ALPHABET": "acceptance_recorded_every_round",
    "A-REACH": "honest_reachable",
})

#: The claim that states each.
LEDGER_CLAIMS: Final[Mapping[str, str]] = MappingProxyType({
    "A-HON": "statistics/ass:hon",
    "A-HON-ENV": "statistics/ass:hon-env",
    "A-ALPHABET": "statistics/ass:alphabet",
    "A-REACH": "statistics/ass:reach",
})

#: The interface's ``emission_rule``: the rows emitted on each route, in
#: ``own_rows`` order. Each is the assumption closure of the results that
#: route reports (the module docstring names them).
EMISSION_BY_ROUTE: Final[Mapping[AcceptanceRoute, tuple[str, ...]]] = (
    MappingProxyType({
        AcceptanceRoute.CONSTRUCTED_BOX: ("A-HON-ENV", "A-ALPHABET", "A-REACH"),
        AcceptanceRoute.DECLARED_SINGLETON: ("A-HON", "A-ALPHABET"),
    })
)


def honest_model_tag(honest_upper: Sequence[Fraction] | None) -> str:
    """Return the ``honest_model`` tag: the envelope's when one is non-degenerate.

    ``honest_upper`` is ``None`` for a law or a degenerate envelope, as the
    resolved request carries it. The one place the tag is decided, so the
    record and the ledger cannot disagree on it.
    """
    return HONEST_MODEL_TAG if honest_upper is None else ENVELOPE_MODEL_TAG


def _law(
    alphabet: Sequence[str], values: Sequence[Fraction]
) -> tuple[tuple[str, str], ...]:
    """Return a vector on the alphabet as ``(outcome, "p/q")`` pairs."""
    return tuple(
        (label, str(value)) for label, value in zip(alphabet, values, strict=True)
    )


def assumption_ledger(
    route: AcceptanceRoute | str,
    *,
    alphabet: Sequence[str],
    rounds: int,
    honest: Sequence[Fraction],
    honest_upper: Sequence[Fraction] | None = None,
) -> tuple[AssumptionLedgerRow, ...]:
    """Return the rows emitted on this route, with the values each binds.

    ``honest`` is the honest law on ``alphabet`` in its declared order, or the
    lower vector of a non-degenerate envelope whose upper vector is
    ``honest_upper`` (``None`` for a law or a degenerate envelope, which is
    read as its law). The rows are the interface's ``emission_rule`` for the
    route (:data:`EMISSION_BY_ROUTE`), each with the declared values its
    assumption's clauses are about:

    * A-HON (``ass:hon``: the n rounds' statistics on Chat i.i.d. with the
      declared law) and A-HON-ENV (``ass:hon-env``: each of the n rounds'
      conditional law inside the declared envelope): ``honest_model`` (the
      tag, :func:`honest_model_tag`), the declared honest input
      (``honest_distribution``, or ``honest_envelope`` with its ``lower`` and
      ``upper``) and ``rounds``.
    * A-ALPHABET (``ass:alphabet``: an acceptance value in Chat recorded in
      every one of the n rounds): ``acceptance_alphabet`` and ``rounds``.
    * A-REACH (``ass:reach``: a feasible state whose law lies in the declared
      envelope): the declared honest input. The other half of its clause, the
      consuming declaration's feasible set, is not an input of this module.

    An unknown route, vectors that do not match the alphabet, and a declared
    singleton with a non-degenerate envelope (the singleton's honest input is
    the point form, ``singleton/req:singleton-point-form``) are refused.
    """
    try:
        resolved = AcceptanceRoute(str(route))
    except ValueError as exc:
        raise MalformedInputError(
            f"no assumption ledger for the route {route!r}; the routes are "
            f"{[str(r) for r in AcceptanceRoute]}"
        ) from exc
    if len(honest) != len(alphabet) or (
        honest_upper is not None and len(honest_upper) != len(alphabet)
    ):
        raise MalformedInputError(
            "the honest vectors and the acceptance alphabet differ in length"
        )
    if resolved is AcceptanceRoute.DECLARED_SINGLETON and honest_upper is not None:
        raise HypothesisError(
            "a declared singleton's honest input is a single law "
            "(singleton/req:singleton-point-form); a non-degenerate envelope "
            "has no singleton ledger"
        )
    declared: tuple[str, object] = (
        ("honest_distribution", _law(alphabet, honest))
        if honest_upper is None
        else ("honest_envelope", (("lower", _law(alphabet, honest)),
                                  ("upper", _law(alphabet, honest_upper))))
    )
    honest_rows: tuple[tuple[str, object], ...] = (
        ("honest_model", honest_model_tag(honest_upper)),
        declared,
        ("rounds", rounds),
    )
    constrains: Mapping[str, tuple[tuple[str, object], ...]] = {
        "A-HON": honest_rows,
        "A-HON-ENV": honest_rows,
        "A-ALPHABET": (("acceptance_alphabet", tuple(alphabet)), ("rounds", rounds)),
        "A-REACH": (declared,),
    }
    return tuple(
        AssumptionLedgerRow(
            assumption_id=short_id,
            machine_key=MACHINE_KEYS[short_id],
            never_verified=never_verified(MACHINE_KEYS[short_id]),
            owner="statistics",
            claim=LEDGER_CLAIMS[short_id],
            constrains=constrains[short_id],
        )
        for short_id in EMISSION_BY_ROUTE[resolved]
    )
