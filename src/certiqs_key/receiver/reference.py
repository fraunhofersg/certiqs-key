"""The dark-composed reference the receiver offers for a snap of its blocks.

Requirement ``req:dark-composed-reference`` (detector-imperfections) with
Requirement ``req:exact-route-decision`` (core): for every declaration whose
model is an admissible receiver exactly, the ``photon_blocks`` entry carries,
per probe setting and per photon number ``n <= N``, a complex enclosure with a
Hermitian centre of every dark-composed block, computed in exact rational
arithmetic with no binary64 value as an input. Those enclosures, with the
family they enclose, are the REFERENCE a declaring instance hands beside its
snap (``foundations/req:snap-reference`` (i), ``foundations/
def:evaluated-off-snap`` (i)), one per setting, with constant ``1``.

THE PASS
========
1. **Decide the exact route and enclose the port Grams**
   (:func:`enclose_port_grams`, Requirement ``req:exact-route-decision``):

   * route (i), declared Grams, and route (ii), a declared instrument matrix:
     the Grams ``eta_k A_k`` (Eq. ``eq:etagram``; on route (ii)
     ``D_eta E_k D_eta = eta_k E_k`` on the rows of port ``k``) are computed
     from the declared values as Gaussian rationals and decided Hermitian and
     admissible exactly (item (i)); where they are, the declaration is on
     the exact route and each Gram is enclosed exactly, by itself;
   * route (iii), a component graph: every generic block (C10) is decided a
     contraction exactly; then the instrument matrix and the Grams are
     compiled in the exact arithmetic of
     :mod:`certiqs_key.receiver.radicals` and decided Gaussian-rational
     (item (ii)), and enclosed exactly on the route or from their exact
     expressions off it; where a parameter is not represented (a non-zero
     angle in radians among them) they are enclosed by the rules from
     square-root and angle enclosures (item (iii));
   * the decision and its cause are recorded (item (iv)).

2. **Enclose the blocks** at every setting (:func:`dark_composed_reference`):
   the lifted no-click operators through permanents (Theorem
   ``thm:enclosed-blocks`` (ii) unconditioned; for a setting family a
   submodule constructs, the enclosure that submodule states, reached through
   :func:`~certiqs_key.receiver.settings.setting_construction`), inclusion and
   exclusion, the
   dark-count channel (Corollary ``cor:exact-dark-composed`` (i)), the zeros
   item (ii)(a) of the requirement keeps exact, and the Hermitian centre of
   Lemma ``lem:enclosure-arithmetic`` (v).

   On a receiver without probe inputs declared by a component graph, each
   block carries besides the factor enclosure of item (vii) where the count
   admits it (:mod:`certiqs_key.receiver.factor`), and records it per letter.

3. **Record the offered kind** of every block: ``exact`` where every radius is
   zero, ``enclosed`` with the largest radius and the largest radius of the
   leaf enclosures otherwise, ``none`` with the cause where no reference is
   offered (items (iii), (iv)).

IN A RUN THAT DECLARES ENCLOSED REFERENCES NOT USED
===================================================
Item (vi) of the requirement binds items (ii) and (iii) in every run, because
the reference is the HANDED REFERENCE the instance passes beside its snap and
the run's first-order bound reads (``foundations/def:evaluated-off-snap`` (i);
``meat-core/frank-wolfe/req:bracket-on-reference``). Only a run that declares
enclosed references not used (``reference_enclosure`` off) is offered the
reference on the blocks it encloses exactly alone, each an exact reference of
its block, offered as ``exact``; every other block is offered as ``none`` with
the cause ``enclosure_not_used`` of ``foundations/req:snap-reference``
(iii)(a), and carries no enclosure (:func:`dark_composed_reference` with
``exact_only``). The block arithmetic that decides whether a block is
enclosed exactly still runs: it is what that decision takes, and nothing
beyond it is read.

THE KIND OFFERED IS NOT THE KIND THE SNAP RAN ON
================================================
A snap records per block the kind of the reference IT ran on
(``foundations/req:who-snaps``): ``exact`` on the centres of an exact block,
``none`` on the floating-point blocks; and the kind HANDED beside it, which is
the offered kind. That is the snap's record, written by the declaring
instance; this module offers.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, fields
from enum import StrEnum
from fractions import Fraction
from typing import Final

import numpy as np

from certiqs_key.foundations.exact import Cx, is_hermitian, is_positive_semidefinite
from certiqs_key.foundations.reference import (
    Enclosure,
    Reference,
    ReferenceBlock,
    ReferenceIdentity,
    ReferenceKind,
    enclosure_pd,
)
from certiqs_key.receiver.catalogue import GenericBlock
from certiqs_key.receiver.dark import DarkCountChannel, DarkCountRoute
from certiqs_key.receiver.enclosure import (
    DEFAULT_BITS,
    Ball,
    BallMatrix,
    hermitian_centred,
)
from certiqs_key.receiver.factor import (
    ESTABLISHING_CLAIMS as FACTOR_CLAIMS,
)
from certiqs_key.receiver.factor import (
    FactorCause,
    FactorOffer,
    NoDilation,
    PortDilation,
    factor_enclosures,
    port_dilation,
)
from certiqs_key.receiver.generic import (
    BallField,
    GenericMatrix,
    NoClickPairs,
    NoEnclosure,
    RecordingField,
    compile_instrument,
    dark_composed_blocks,
    element_blocks,
    port_grams_of,
)
from certiqs_key.receiver.graph import topological_order
from certiqs_key.receiver.numerics import PiMultiple, Scalar
from certiqs_key.receiver.radicals import NotRepresented, Radical, RadicalField
from certiqs_key.receiver.request import InputRoute, ValidatedRequest
from certiqs_key.receiver.settings import UNCONDITIONED, setting_construction

__all__ = [
    "DARK_COMPOSITION_CLAIM",
    "ESTABLISHING_CLAIMS_UNCONDITIONED",
    "MODEL",
    "ExactRouteCause",
    "ExactRouteDecision",
    "GramEnclosures",
    "OfferedBlock",
    "ReferenceCause",
    "SettingReference",
    "block_label",
    "dark_composed_reference",
    "dark_weights",
    "decide_dark_channel_exactly",
    "enclose_port_grams",
]

#: The model a reference of the receiver encloses (``foundations/req:who-snaps``
#: names the reference's model): the dark-composed family.
MODEL: Final[str] = "receiver/detector-imperfections/def:dark-composed"

#: The claims that establish the enclosure, positivity and completeness of the
#: reference, which ``foundations/req:snap-reference`` (i) leaves to the
#: constructing module: Requirement req:dark-composed-reference (iii).
#: The dark-count composition's claim comes first, then the claims of the
#: construction that produced the setting family
#: (:attr:`~certiqs_key.receiver.settings.SettingConstruction.enclosure_claims`):
#: Theorem thm:enclosed-blocks (ii) through Corollary cor:exact-dark-composed
#: (iii) for an unconditioned receiver, the enclosure claim of the
#: constructing submodule for a setting family a submodule constructs.
DARK_COMPOSITION_CLAIM: Final[str] = (
    "receiver/detector-imperfections/cor:exact-dark-composed (ii)"
)
ESTABLISHING_CLAIMS_UNCONDITIONED: Final[tuple[str, ...]] = (
    DARK_COMPOSITION_CLAIM,
    *UNCONDITIONED.enclosure_claims,
)

_ZERO: Final[Fraction] = Fraction(0)


def block_label(photons: int) -> str:
    """Return the label of the block of photon number ``n``: ``m=n``.

    The label the declaring instance gives the same block when it snaps the
    family (``instances/common/declare.py``), so that the reference and the
    data name their blocks alike (``foundations/def:exact-reference``: the
    blocks of one sector map, in its order).
    """
    return f"m={photons}"


# ---------------------------------------------------------------------------
#  req:exact-route-decision
# ---------------------------------------------------------------------------


class ExactRouteCause(StrEnum):
    """Why a declaration is off the exact route -- req:exact-route-decision (iv)."""

    #: A parameter or angle the exact arithmetic of (ii) does not represent,
    #: a non-zero angle given in radians among them.
    PARAMETER_NOT_REPRESENTED = "parameter_not_represented"
    #: Port Grams computed exactly that are not Gaussian-rational.
    GRAMS_NOT_GAUSSIAN_RATIONAL = "port_grams_not_gaussian_rational"
    #: No model admissible exactly: declared port Grams that are not Hermitian.
    GRAMS_NOT_HERMITIAN = "declared_port_grams_not_hermitian"
    #: No model admissible exactly: a declared family that is not an
    #: admissible Gram family exactly (admitted only at the receiver tolerances).
    FAMILY_NOT_ADMISSIBLE = "declared_family_not_admissible_exactly"
    #: No model admissible exactly: a generic block that is not a contraction.
    GENERIC_BLOCK_NOT_CONTRACTION = "generic_block_not_contraction_exactly"

    @property
    def leaves_no_exact_model(self) -> bool:
        """Whether the cause is one of "no model admissible exactly"."""
        return self in (
            ExactRouteCause.GRAMS_NOT_HERMITIAN,
            ExactRouteCause.FAMILY_NOT_ADMISSIBLE,
            ExactRouteCause.GENERIC_BLOCK_NOT_CONTRACTION,
        )


@dataclass(frozen=True)
class ExactRouteDecision:
    """The decision of Requirement ``req:exact-route-decision`` and its record.

    Implements the record of ``receiver/req:exact-route-decision`` (iv):
    ``decided_by`` is the item that decided ((i) for declared Grams or a
    declared matrix, (ii) for a component graph); ``on_exact_route`` whether
    it places the declaration on the exact route; ``has_exact_model`` whether
    the declaration has a model admissible exactly; and, off the route, the
    ``cause`` with a ``detail`` naming what failed.
    """

    input_route: InputRoute
    decided_by: str
    has_exact_model: bool
    on_exact_route: bool
    cause: ExactRouteCause | None = None
    detail: str = ""

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {
            "input_route": str(self.input_route),
            "decided_by": self.decided_by,
            "has_exact_model": self.has_exact_model,
            "on_exact_route": self.on_exact_route,
            "cause": None if self.cause is None else str(self.cause),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class GramEnclosures:
    """Complex enclosures of the port Grams -- req:exact-route-decision (iii).

    ``largest_leaf`` is the largest radius of the square-root and angle
    enclosures the Grams were computed from (zero where they are exact).
    """

    grams: tuple[BallMatrix, ...]
    largest_leaf: Fraction

    @property
    def exact(self) -> bool:
        """Whether every Gram is enclosed exactly."""
        return all(
            entry.is_exact for gram in self.grams for row in gram for entry in row
        )

    def loss_established(self) -> bool:
        """Decide ``1 - A_Sigma`` positive definite, so ``lmax(A_Sigma) < 1``.

        Through ``foundations/lem:enclosure-psd`` (i) on the Hermitian-centred
        enclosure of ``1 - A_Sigma`` (Lemma ``lem:enclosure-arithmetic`` (v));
        on exact Grams it is the exact decision. ``False`` says that
        ``lmax(A_Sigma) < 1`` is not established, which is what the
        last-resort fix of Requirement ``req:snap-fix`` reads
        before naming the ports of declared efficiency ``1``.
        """
        size = len(self.grams[0])
        total = [
            [
                (Ball(Fraction(1)) if i == j else Ball(_ZERO))
                - _sum_balls(gram[i][j] for gram in self.grams)
                for j in range(size)
            ]
            for i in range(size)
        ]
        centre, radii = hermitian_centred(total)
        return enclosure_pd(centre, radii)


def _sum_balls(values: Iterable[Ball]) -> Ball:
    total = Ball(_ZERO)
    for value in values:
        total = total + value
    return total


def _cx_of(entry: complex) -> Cx:
    """Return a declared binary64 complex entry as the Gaussian rational it is."""
    return Cx(Fraction(float(entry.real)), Fraction(float(entry.imag)))


def _declared(value: Scalar) -> Fraction:
    return Fraction(value)


def _exact_matrix(rows: Sequence[Sequence[Cx]]) -> tuple[tuple[Cx, ...], ...]:
    return tuple(tuple(row) for row in rows)


def _cx_identity_minus(matrix: Sequence[Sequence[Cx]]) -> tuple[tuple[Cx, ...], ...]:
    one = Fraction(1)
    return tuple(
        tuple(
            Cx((one if i == j else _ZERO) - entry.re, -entry.im)
            for j, entry in enumerate(row)
        )
        for i, row in enumerate(matrix)
    )


def _cx_sum(matrices: Sequence[Sequence[Sequence[Cx]]], size: int) -> list[list[Cx]]:
    total = [[Cx(_ZERO, _ZERO) for _ in range(size)] for _ in range(size)]
    for matrix in matrices:
        for i in range(size):
            for j in range(size):
                total[i][j] = total[i][j] + matrix[i][j]
    return total


def _decide_declared_family(
    grams: Sequence[Sequence[Sequence[Cx]]],
) -> tuple[ExactRouteCause | None, str]:
    """Decide Hermiticity and exact admissibility of a Gaussian-rational family.

    Requirement ``req:exact-route-decision`` (i), Eq. ``eq:exact-admissible``:
    every ``A_k`` Hermitian and positive semidefinite, and
    ``1 - A_[K] >= 0``, decided by the exact ``LDL^*`` of
    :func:`certiqs_key.foundations.exact.is_positive_semidefinite`.
    """
    for index, gram in enumerate(grams):
        if not is_hermitian(_exact_matrix(gram)):
            return (
                ExactRouteCause.GRAMS_NOT_HERMITIAN,
                f"port Gram {index} is not Hermitian",
            )
    for index, gram in enumerate(grams):
        if not is_positive_semidefinite(_exact_matrix(gram)):
            return (
                ExactRouteCause.FAMILY_NOT_ADMISSIBLE,
                f"port Gram {index} is not positive semidefinite exactly",
            )
    size = len(grams[0])
    total = _cx_sum(grams, size)
    if not is_positive_semidefinite(_cx_identity_minus(total)):
        return (
            ExactRouteCause.FAMILY_NOT_ADMISSIBLE,
            "1 - A_[K] is not positive semidefinite exactly",
        )
    return None, ""


def _exact_balls(grams: Sequence[Sequence[Sequence[Cx]]]) -> tuple[BallMatrix, ...]:
    return tuple(
        [[Ball.of_cx(entry) for entry in row] for row in gram] for gram in grams
    )


def _declared_entries_finite(validated: ValidatedRequest) -> bool:
    """Whether every declared operator entry is finite.

    A declared value is the dyadic rational a FINITE binary64 number denotes
    (``foundations/def:binary64`` (iii)); a non-finite entry denotes none, so
    the declaration determines no model at all, let alone one admissible
    exactly, and it is recorded as such rather than converted.
    """
    request = validated.request
    operators: list[object] = []
    if request.port_grams is not None:
        operators.extend(request.port_grams.matrices)
    if request.instrument_matrix is not None:
        operators.append(request.instrument_matrix)
    if request.element_graph is not None:
        operators.extend(
            element.component.block
            for element in request.element_graph.elements
            if isinstance(element.component, GenericBlock)
        )
    return all(bool(np.all(np.isfinite(np.asarray(op)))) for op in operators)


def _route_i_ii_grams(validated: ValidatedRequest) -> list[list[list[Cx]]]:
    """Return ``eta_k A_k`` exactly on route (i) or (ii)."""
    request = validated.request
    efficiencies = [_declared(port.efficiency) for port in request.detector_layer]
    if validated.route is InputRoute.PORT_GRAMS:
        declared = request.port_grams
        assert declared is not None
        bases = [
            [[_cx_of(entry) for entry in row] for row in matrix]
            for matrix in declared.matrices
        ]
    else:
        supplied = request.instrument_matrix
        assert supplied is not None
        columns = request.input_modes.subsystem_order()
        exact = [[_cx_of(entry) for entry in row] for row in supplied]
        bases = []
        for _, rows in request.port_map.entries:
            gram: list[list[Cx]] = []
            for a in columns:
                gram_row: list[Cx] = []
                for b in columns:
                    total = Cx(_ZERO, _ZERO)
                    for row in rows:
                        total = total + exact[row][a].conjugate() * exact[row][b]
                    gram_row.append(total)
                gram.append(gram_row)
            bases.append(gram)
    return [
        [[Cx(entry.re * eta, entry.im * eta) for entry in row] for row in base]
        for base, eta in zip(bases, efficiencies, strict=True)
    ]


def _generic_blocks_contract(validated: ValidatedRequest) -> tuple[bool, str]:
    """Decide ``Gamma_Sigma^dagger Gamma_Sigma <= 1`` for every C10 block exactly."""
    graph = validated.request.element_graph
    assert graph is not None
    for element in graph.elements:
        component = element.component
        if not isinstance(component, GenericBlock):
            continue
        exact = [[_cx_of(entry) for entry in row] for row in component.block]
        size = len(exact)
        product = [
            [_column_product(exact, a, b) for b in range(size)] for a in range(size)
        ]
        if not is_positive_semidefinite(_cx_identity_minus(product)):
            return False, f"generic block {element.name!r} is not a contraction exactly"
    return True, ""


def _column_product(matrix: Sequence[Sequence[Cx]], a: int, b: int) -> Cx:
    """Return ``(X^dagger X)_ab``, exactly."""
    total = Cx(_ZERO, _ZERO)
    for row in matrix:
        total = total + row[a].conjugate() * row[b]
    return total


def enclose_port_grams(
    validated: ValidatedRequest, bits: int = DEFAULT_BITS
) -> tuple[ExactRouteDecision, GramEnclosures | None]:
    """Decide the exact route and enclose the port Grams.

    Implements ``receiver/req:exact-route-decision`` (i)-(iv) and the port-Gram
    half of ``receiver/def:exact-route``. Returns the recorded decision and,
    for a declaration with a model admissible exactly, complex enclosures of
    its port Grams computed in exact rational arithmetic -- exact on the exact
    route -- or ``None`` where there is no such model.
    """
    request = validated.request
    route = validated.route
    if not _declared_entries_finite(validated):
        non_finite = (
            ExactRouteCause.GENERIC_BLOCK_NOT_CONTRACTION
            if route is InputRoute.ELEMENT_GRAPH
            else ExactRouteCause.FAMILY_NOT_ADMISSIBLE
        )
        item = "(ii)" if route is InputRoute.ELEMENT_GRAPH else "(i)"
        return (
            ExactRouteDecision(
                route, item, False, False, non_finite, "a declared entry is not finite"
            ),
            None,
        )
    if route in (InputRoute.PORT_GRAMS, InputRoute.INSTRUMENT_MATRIX):
        grams = _route_i_ii_grams(validated)
        cause, detail = _decide_declared_family(grams)
        if cause is not None:
            return (
                ExactRouteDecision(route, "(i)", False, False, cause, detail),
                None,
            )
        return (
            ExactRouteDecision(route, "(i)", True, True),
            GramEnclosures(_exact_balls(grams), _ZERO),
        )

    contracts, detail = _generic_blocks_contract(validated)
    if not contracts:
        return (
            ExactRouteDecision(
                route,
                "(ii)",
                False,
                False,
                ExactRouteCause.GENERIC_BLOCK_NOT_CONTRACTION,
                detail,
            ),
            None,
        )
    graph = request.element_graph
    assert graph is not None
    order = topological_order(graph)
    assert order is not None  # (E2) is refused at validation
    mode_count = len(request.mode_space)
    port_rows = [rows for _, rows in request.port_map.entries]
    efficiencies = [port.efficiency for port in request.detector_layer]
    columns = request.input_modes.subsystem_order()

    recorder = RecordingField()
    compile_instrument(recorder, graph, mode_count, order, port_rows, efficiencies)
    try:
        field = RadicalField(recorder.radicands)
        gamma = compile_instrument(
            field, graph, mode_count, order, port_rows, efficiencies
        )
        exact_grams = port_grams_of(field, gamma, columns, port_rows)
    except NotRepresented as reason:
        ball = BallField(bits)
        gamma_b = compile_instrument(
            ball, graph, mode_count, order, port_rows, efficiencies
        )
        grams_b = port_grams_of(ball, gamma_b, columns, port_rows)
        return (
            ExactRouteDecision(
                route,
                "(ii)",
                True,
                False,
                ExactRouteCause.PARAMETER_NOT_REPRESENTED,
                str(reason),
            ),
            GramEnclosures(grams_b, ball.largest_leaf),
        )
    if all(
        entry.is_gaussian_rational
        for gram in exact_grams
        for row in gram
        for entry in row
    ):
        return (
            ExactRouteDecision(route, "(ii)", True, True),
            GramEnclosures(
                tuple(
                    [[Ball.of_cx(entry.as_cx()) for entry in row] for row in gram]
                    for gram in exact_grams
                ),
                _ZERO,
            ),
        )
    largest = _ZERO
    enclosed: list[BallMatrix] = []
    for gram in exact_grams:
        rows_b: BallMatrix = []
        for row in gram:
            row_b: list[Ball] = []
            for entry in row:
                ball_entry, leaf = _radical_ball(entry, bits)
                largest = max(largest, leaf)
                row_b.append(ball_entry)
            rows_b.append(row_b)
        enclosed.append(rows_b)
    return (
        ExactRouteDecision(
            route,
            "(ii)",
            True,
            False,
            ExactRouteCause.GRAMS_NOT_GAUSSIAN_RATIONAL,
            "a port Gram computed exactly has an entry outside Q(i)",
        ),
        GramEnclosures(tuple(enclosed), largest),
    )


def _radical_ball(entry: Radical, bits: int) -> tuple[Ball, Fraction]:
    return entry.to_ball(bits)


# ---------------------------------------------------------------------------
#  req:dark-composed-reference
# ---------------------------------------------------------------------------


class ReferenceCause(StrEnum):
    """Why the entry offers no reference -- req:dark-composed-reference (iv)."""

    #: The declaration has no model admissible exactly
    #: (req:exact-route-decision (i), (ii)); the route record names why.
    NO_EXACT_MODEL = "no_model_admissible_exactly"
    #: A declared dark-count matrix that does not satisfy (D1) and (D2) exactly.
    DARK_CHANNEL_NOT_EXACT = "dark_count_channel_not_admissible_exactly"
    #: A reciprocal that the enclosure of a setting family a submodule
    #: constructs forms, and that receives no enclosure
    #: (detector-imperfections/req:dark-composed-reference (iv)).
    RECIPROCAL_NOT_ENCLOSED = "reciprocal_not_enclosed"
    #: Item (vi), per block: the run declares enclosed references not used,
    #: and the block is not enclosed exactly, so no enclosure of it is carried
    #: (the cause ``enclosure_not_used`` of ``foundations/req:snap-reference``
    #: (iii)(a)).
    ENCLOSURE_NOT_USED = "enclosure_not_used"


@dataclass(frozen=True)
class OfferedBlock:
    """The reference kind the entry OFFERS for one block -- req (iii), (iv).

    ``exact`` where every radius of the block is zero; ``enclosed`` with the
    largest radius of the block, the largest decision radius ``rho`` of its
    elements and the largest radius of the leaf enclosures (square roots,
    trigonometric values) from which the centres are computed; ``none`` where
    the entry offers no reference.
    """

    label: str
    photons: int
    kind: ReferenceKind
    largest_radius: Fraction | None = None
    rho: Fraction | None = None
    input_radius: Fraction | None = None
    #: Why a block offered as ``none`` carries no reference, where the cause
    #: is the block's own (item (vi): enclosed references not used); ``None``
    #: where the setting's cause (:attr:`SettingReference.cause`) says it.
    cause: ReferenceCause | None = None
    #: Item (vii), per letter: the factor enclosure carried beside the
    #: block's entrywise enclosure, with its columns and largest radius, or
    #: why none is. Empty where the block offers no reference.
    factors: tuple[tuple[str, FactorOffer], ...] = ()

    def as_record(self) -> dict[str, object]:
        """JSON-ready: exact rationals as strings, with a float diagnostic."""

        def text(value: Fraction | None) -> str | None:
            return None if value is None else str(value)

        record: dict[str, object] = {
            "block": self.label,
            "photons": self.photons,
            "kind": str(self.kind),
            "largest_radius": text(self.largest_radius),
            "largest_radius_float": (
                None if self.largest_radius is None else float(self.largest_radius)
            ),
            "rho": text(self.rho),
            "input_radius": text(self.input_radius),
        }
        # Written only where the block has a cause of its own (item (vi)), so
        # that the record of a block offered as before is the record it was.
        if self.cause is not None:
            record["cause"] = str(self.cause)
        if self.factors:
            record["factor_enclosures"] = {
                letter: offer.as_record() for letter, offer in self.factors
            }
        return record


@dataclass(frozen=True)
class SettingReference:
    """The reference offered at one probe setting, with its record.

    Implements the reference half of ``receiver/detector-imperfections/
    req:dark-composed-reference`` (ii)-(iv) at one setting: the
    :class:`~certiqs_key.foundations.reference.Reference` (or ``None``), the
    kind offered per block, the cause where there is no reference, and the
    exact-route decision of ``receiver/req:exact-route-decision`` (iv).
    """

    setting: str
    exact_route: ExactRouteDecision
    reference: Reference | None
    offered: tuple[OfferedBlock, ...]
    cause: ReferenceCause | None = None
    detail: str = ""
    #: Whether ``lmax(A_Sigma) < 1`` is established on the Gram enclosures
    #: (:meth:`GramEnclosures.loss_established`); ``None`` without enclosures.
    loss_established: bool | None = None
    #: Wall-clock seconds the construction of this setting's reference took.
    #: A performance diagnostic; not in the payload,
    #: which must not depend on the machine.
    seconds: float = field(default=0.0, compare=False)

    @property
    def offered_kinds(self) -> dict[str, ReferenceKind]:
        """The offered kind of every block, by label."""
        return {block.label: block.kind for block in self.offered}

    def enclosures_record(self) -> list[dict[str, object]] | None:
        """Return the enclosures as exact rationals written as strings, or ``None``."""
        if self.reference is None:
            return None
        return [
            {
                "block": block.label,
                "elements": [
                    {"letter": letter, **element.as_record()}
                    for letter, element in zip(
                        self.reference.alphabet, block.elements, strict=True
                    )
                ],
            }
            for block in self.reference.blocks
        ]

    def enclosures_digest(self) -> str | None:
        """Return the SHA-256 of the canonical JSON of :meth:`enclosures_record`."""
        enclosures = self.enclosures_record()
        if enclosures is None:
            return None
        canonical = json.dumps(enclosures, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def as_record(self, *, enclosures: bool = False) -> dict[str, object]:
        """JSON-ready: the offered kinds, the cause, the identity, the enclosures.

        The enclosures themselves are carried only on request: their exact
        rationals grow quickly with the cutoff (hundreds of kilobytes at
        ``N = 4``), and the artifact's payload travels in every preparation
        record. The payload carries their SHA-256 instead
        (``enclosures_sha256``), which pins exactly which reference was
        offered; :attr:`reference` holds them, and ``enclosures=True`` writes
        them out.
        """
        record: dict[str, object] = {
            "setting": self.setting,
            "offered": [block.as_record() for block in self.offered],
            "cause": None if self.cause is None else str(self.cause),
            "detail": self.detail,
            "loss_established": self.loss_established,
        }
        if self.reference is not None:
            record["identity"] = self.reference.identity.as_record()
            record["constant"] = str(self.reference.constant)
            record["alphabet"] = list(self.reference.alphabet)
            record["enclosures_sha256"] = self.enclosures_digest()
            if enclosures:
                record["enclosures"] = self.enclosures_record()
        return record


def decide_dark_channel_exactly(channel: DarkCountChannel) -> tuple[bool, str]:
    """Decide (D1) and (D2) of ``def:darkadm`` exactly on the declared entries.

    Requirement ``req:dark-composed-reference`` (ii): "whose ``R`` satisfies
    (D1) and (D2) exactly, decided in exact arithmetic on its declared entries
    on the declared dark-count route". On the generated route they are
    theorems (``thm:dark-counts`` (i)) and :func:`~certiqs_key.receiver.dark.
    product_form` evaluates Eq. ``eq:darkR`` exactly, so nothing is decided.
    """
    if channel.route is DarkCountRoute.PER_PORT_PRODUCT_FORM:
        return True, ""
    for column in channel.patterns():
        entries = channel.columns.get(column, {})
        total = Fraction(0)
        for row, value in entries.items():
            exact = Fraction(value)
            if exact < 0:
                return False, (
                    f"(D1) R_{{{sorted(row)}|{sorted(column)}}} = {exact} is negative"
                )
            if exact != 0 and not column <= row:
                return False, (
                    f"(D2) R_{{{sorted(row)}|{sorted(column)}}} = {exact} is not zero "
                    f"although {sorted(column)} is not a subset of {sorted(row)}"
                )
            total += exact
        if total != 1:
            return False, f"(D1) column {sorted(column)} sums to {total}, not 1"
    return True, ""


def dark_weights(
    channel: DarkCountChannel,
    fibres: Mapping[str, Sequence[frozenset[int]]],
) -> dict[str, dict[frozenset[int], Fraction]]:
    """Return ``R_{cg^-1(v)|S'} = sum_{S in cg^-1(v)} R_{S|S'}``, exactly."""
    return {
        letter: {
            column: sum(
                (Fraction(channel.entry(row, column)) for row in fibre), Fraction(0)
            )
            for column in channel.patterns()
        }
        for letter, fibre in fibres.items()
    }


def _vanishing_patterns(
    validated: ValidatedRequest,
    channel: DarkCountChannel,
    pairs: NoClickPairs[Ball],
    photons: int,
) -> set[frozenset[int]]:
    """Return the click patterns ``S`` whose ``Mtilde_S^{(n)}`` is shown to vanish.

    Requirement ``req:dark-composed-reference`` (ii)(a):

    * for the unconditioned receiver on the generated dark-count route, and
      for no other receiver or route, by ``prop:noise-floor`` (v): with
      ``Z = {k : p_k = 0}``, ``Mtilde_S^{(n)} = 0`` when ``|S cap Z| > n``,
      and ``Mtilde_S = 0`` for every ``S`` missing a port with ``p_k = 1``;
    * for ``S`` empty and ``n >= 1``, by ``prop:noise-floor`` (iv), at a setting
      whose ``B^(t)`` was computed exactly and is the identity.
    """
    request = validated.request
    ports = request.port_map.port_count
    vanishing: set[frozenset[int]] = set()
    unconditioned = not request.input_modes.source
    if unconditioned and channel.route is DarkCountRoute.PER_PORT_PRODUCT_FORM:
        probabilities = [
            Fraction(port.dark_count_probability) for port in request.detector_layer
        ]
        silent = {k for k, value in enumerate(probabilities) if value == 0}
        certain = {k for k, value in enumerate(probabilities) if value == 1}
        for pattern in channel.patterns():
            if len(pattern & silent) > photons or not certain <= pattern:
                vanishing.add(pattern)
    if photons >= 1:
        _, operator = pairs[frozenset(range(ports))]
        size = len(operator)
        identity = all(
            operator[i][j].is_exact
            and operator[i][j].im == 0
            and operator[i][j].re == (1 if i == j else 0)
            for i in range(size)
            for j in range(size)
        )
        if identity:
            vanishing.add(frozenset())
    return vanishing


def _identity_parameters(validated: ValidatedRequest, setting: str) -> dict[str, str]:
    """Return the exact parameters a reference names (``foundations/req:who-snaps``).

    Every scalar is written as the exact rational it denotes. A declared
    operator -- the port Grams of route (i), the instrument matrix of route
    (ii), a C10 block, a declared dark-count matrix -- is written as the
    SHA-256 of its exact form (:func:`_exact_operator_digest`,
    :func:`_dark_channel_digest`), the entries being the Gaussian rationals the
    declared binary64 numbers denote: those, not their binary64 evaluation in
    the artifact's ``port_grams``, are what the reference is formed from, and
    the digest is recomputable from the declaration alone.
    """
    request = validated.request
    parameters: dict[str, str] = {
        "input_route": str(validated.route),
        "probe_setting": setting,
        "photon_cutoff": str(request.photon_cutoff),
    }
    for port in request.detector_layer:
        parameters[f"detector.{port.label}.efficiency"] = str(Fraction(port.efficiency))
        parameters[f"detector.{port.label}.dark_count_probability"] = str(
            Fraction(port.dark_count_probability)
        )
    probe = request.probe_declaration.setting(setting)
    for index, value in enumerate(probe.mean_photon_numbers):
        parameters[f"probe.{setting}.nbar_{index}"] = str(Fraction(value))
    graph = request.element_graph
    if graph is not None:
        for element in graph.elements:
            component = element.component
            for entry in fields(component):
                if entry.name == "tolerances":
                    continue
                value = getattr(component, entry.name)
                if entry.name == "block":
                    parameters[f"{element.name}.block.sha256"] = _exact_operator_digest(
                        value
                    )
                    continue
                parameters[f"{element.name}.{entry.name}"] = _parameter_text(value)
    if request.dark_count_channel is not None:
        parameters["dark_count_channel.sha256"] = _dark_channel_digest(
            request.dark_count_channel
        )
    if request.port_grams is not None and validated.route is InputRoute.PORT_GRAMS:
        for label, matrix in zip(
            request.port_grams.labels, request.port_grams.matrices, strict=True
        ):
            parameters[f"port_grams.{label}.sha256"] = _exact_operator_digest(matrix)
    if (
        request.instrument_matrix is not None
        and validated.route is InputRoute.INSTRUMENT_MATRIX
    ):
        parameters["instrument_matrix.sha256"] = _exact_operator_digest(
            request.instrument_matrix
        )
    return parameters


def _canonical_digest(payload: object) -> str:
    """Return the SHA-256 of ``payload``'s canonical JSON (sorted, compact)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _exact_operator_digest(matrix: object) -> str:
    """Return the SHA-256 of a declared operator's exact form.

    The exact form is the list of rows, each entry ``[re, im]`` with ``re``
    and ``im`` the exact rationals (``str(Fraction)``) the declared binary64
    parts denote (``foundations/def:binary64`` (iii)), serialised as compact
    JSON with sorted keys.
    """
    rows = np.asarray(matrix, dtype=np.complex128)
    exact = [
        [[str(entry.re), str(entry.im)] for entry in (_cx_of(value) for value in row)]
        for row in rows
    ]
    return _canonical_digest(exact)


def _dark_channel_digest(channel: DarkCountChannel) -> str:
    """Return the SHA-256 of a declared dark-count matrix's exact entries.

    The exact form is the list of ``[column, row, value]`` over the non-zero
    declared entries, ``column`` and ``row`` the sorted port lists of the
    patterns ``S'`` and ``S`` and ``value`` the exact rational
    ``R_{S|S'}`` (``str(Fraction)``), sorted, serialised as compact JSON.
    """
    entries = sorted(
        [sorted(column), sorted(row), str(Fraction(value))]
        for column, rows in channel.columns.items()
        for row, value in rows.items()
        if Fraction(value) != 0
    )
    return _canonical_digest([channel.route.value, channel.port_count, entries])


def _parameter_text(value: object) -> str:
    if isinstance(value, PiMultiple):
        return str(value)
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int | float | Fraction):
        return str(Fraction(value))
    if isinstance(value, tuple | list):
        return "(" + ", ".join(_parameter_text(item) for item in value) + ")"
    return str(value)


def _none_blocks(cutoff: int) -> tuple[OfferedBlock, ...]:
    return tuple(
        OfferedBlock(block_label(n), n, ReferenceKind.NONE) for n in range(cutoff + 1)
    )


def _zero_block(size: int) -> GenericMatrix[Ball]:
    return [[Ball(_ZERO) for _ in range(size)] for _ in range(size)]


def dark_composed_reference(
    validated: ValidatedRequest,
    channel: DarkCountChannel,
    bits: int = DEFAULT_BITS,
    *,
    exact_only: bool = False,
) -> tuple[SettingReference, ...]:
    """Return the reference the receiver offers at every probe setting.

    Implements ``receiver/detector-imperfections/req:dark-composed-reference``
    (ii)-(iv) and (vii), through ``receiver/req:exact-route-decision`` (iii) for the
    port Grams, ``receiver/thm:enclosed-blocks`` (ii) for the blocks (for a
    setting family a submodule constructs, the enclosure that submodule
    states), ``receiver/detector-imperfections/cor:exact-dark-composed`` (i),
    (ii) for the composition with the dark counts, and
    ``receiver/lem:enclosure-arithmetic`` (v) for the Hermitian centres. On
    the exact route, with the Grams enclosed exactly, every block ``n <= 1``
    has radius zero (``receiver/thm:exact-blocks`` (iii), or the exactness
    claim of the constructing submodule).

    Item (vii): on a receiver without probe inputs declared by a component
    graph, every block also carries, per letter, the factor enclosure of
    :func:`~certiqs_key.receiver.factor.factor_enclosures` where the count
    admits it, and records it or its cause (:class:`OfferedBlock`).

    ``exact_only`` is item (vi), for a run that declares enclosed references
    not used: the reference carries only the blocks enclosed exactly, and
    every other block is offered as ``none`` with the cause
    :attr:`ReferenceCause.ENCLOSURE_NOT_USED`; a setting none of
    whose blocks is enclosed exactly carries no reference, with no cause of
    its own (nothing of item (iv) is decided by withholding it).
    """
    request = validated.request
    cutoff = request.photon_cutoff
    settings = request.probe_declaration.settings
    decision, grams = enclose_port_grams(validated, bits)

    def none_for_all(
        cause: ReferenceCause, detail: str, loss: bool | None
    ) -> tuple[SettingReference, ...]:
        return tuple(
            SettingReference(
                setting.label,
                decision,
                None,
                _none_blocks(cutoff),
                cause,
                detail,
                loss_established=loss,
            )
            for setting in settings
        )

    if grams is None:
        return none_for_all(ReferenceCause.NO_EXACT_MODEL, decision.detail, None)
    loss = grams.loss_established()
    exact_channel, channel_detail = decide_dark_channel_exactly(channel)
    if not exact_channel:
        return none_for_all(ReferenceCause.DARK_CHANNEL_NOT_EXACT, channel_detail, loss)

    coarse = request.outcome_coarse_graining
    alphabet = coarse.alphabet
    fibres = {letter: coarse.fibre(letter) for letter in alphabet}
    weights = dark_weights(channel, fibres)
    ports = request.port_map.port_count
    channel_dimension = request.input_modes.channel_dimension
    conditioned = bool(request.input_modes.source)
    construction = setting_construction(request.input_modes.source_dimension)
    claims = (DARK_COMPOSITION_CLAIM, *construction.enclosure_claims)
    # Item (vii): the port dilation, formed once, where a factor enclosure can
    # be formed at all; otherwise the cause every block records.
    dilation: PortDilation | None = None
    no_factor = FactorOffer(None)
    if conditioned:
        no_factor = FactorOffer(
            None,
            FactorCause.PROBE_CONDITIONED,
            "the blocks of a receiver with probe inputs are not formed through a "
            "port dilation",
        )
    elif exact_only:
        no_factor = FactorOffer(
            None,
            FactorCause.ENCLOSED_REFERENCES_NOT_USED,
            "the run declares enclosed references not used (item (vi))",
        )
    else:
        try:
            dilation = port_dilation(validated, BallField(bits))
        except NoDilation as reason:
            no_factor = FactorOffer(None, FactorCause.NO_PORT_DILATION, str(reason))
    inputs = len(request.input_modes.subsystem_order())

    references: list[SettingReference] = []
    for setting in settings:
        started = time.perf_counter()
        if not all(
            math.isfinite(float(value)) for value in setting.mean_photon_numbers
        ):
            references.append(
                SettingReference(
                    setting.label,
                    decision,
                    None,
                    _none_blocks(cutoff),
                    ReferenceCause.NO_EXACT_MODEL,
                    "a declared mean photon number is not finite",
                    loss_established=loss,
                )
            )
            continue
        ball = BallField(bits)
        try:
            pairs = construction.no_click_pairs(
                ball, grams.grams, channel_dimension, setting
            )
        except NoEnclosure as reason:
            references.append(
                SettingReference(
                    setting.label,
                    decision,
                    None,
                    _none_blocks(cutoff),
                    ReferenceCause.RECIPROCAL_NOT_ENCLOSED,
                    str(reason),
                    loss_established=loss,
                    seconds=time.perf_counter() - started,
                )
            )
            continue
        blocks: list[ReferenceBlock] = []
        offered: list[OfferedBlock] = []
        carried = False
        for photons in range(cutoff + 1):
            block_field = BallField(bits)
            raw = element_blocks(block_field, pairs, ports, photons)
            composed = dark_composed_blocks(block_field, raw, weights, alphabet)
            vanishing = _vanishing_patterns(validated, channel, pairs, photons)
            offers = (
                dict.fromkeys(alphabet, no_factor)
                if dilation is None
                else factor_enclosures(
                    dilation,
                    BallField(bits),
                    photons=photons,
                    inputs=inputs,
                    weights={letter: weights[letter] for letter in alphabet},
                )
            )
            elements: list[Enclosure] = []
            for letter in alphabet:
                matrix = composed[letter]
                if all(pattern in vanishing for pattern in fibres[letter]):
                    matrix = _zero_block(len(matrix))
                centre, radii = hermitian_centred(matrix)
                factor = offers[letter].factor
                carried = carried or factor is not None
                elements.append(Enclosure(centre, radii, factor))
            exact = all(element.is_exact for element in elements)
            leaf = max(grams.largest_leaf, block_field.largest_leaf, ball.largest_leaf)
            label = block_label(photons)
            if exact_only and not exact:
                # Item (vi): not enclosed exactly, and the run declares
                # enclosed references not used, so no enclosure is carried.
                offered.append(
                    OfferedBlock(
                        label,
                        photons,
                        ReferenceKind.NONE,
                        cause=ReferenceCause.ENCLOSURE_NOT_USED,
                    )
                )
                continue
            block = ReferenceBlock(label, tuple(elements), None if exact else leaf)
            blocks.append(block)
            offered.append(
                OfferedBlock(
                    label,
                    photons,
                    block.kind,
                    max(element.largest_radius for element in elements),
                    block.rho,
                    block.input_radius,
                    factors=tuple((letter, offers[letter]) for letter in alphabet),
                )
            )
        reference = (
            Reference(
                alphabet=alphabet,
                blocks=tuple(blocks),
                constant=Fraction(1),
                identity=ReferenceIdentity(
                    MODEL,
                    _identity_parameters(validated, setting.label),
                    # Item (vii): the claims that establish a block's
                    # membership of its factor enclosure, where one is carried.
                    establishing_claims=claims + (FACTOR_CLAIMS if carried else ()),
                ),
            )
            if blocks
            else None
        )
        references.append(
            SettingReference(
                setting.label,
                decision,
                reference,
                tuple(offered),
                loss_established=loss,
                seconds=time.perf_counter() - started,
            )
        )
    return tuple(references)
