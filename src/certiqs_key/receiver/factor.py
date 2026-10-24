"""The factor enclosures the receiver offers beside its reference blocks.

WHY THIS EXISTS. The projector of an ideal analyser at an angle off the
``pi/8`` grid has irrational entries and a rank below its dimension; its
entrywise enclosure fixes no rank (``foundations/cor:least-eigenvalue-over-
enclosure`` (iv)), so a certified evaluation over the reference companion
certifies no point of it (``meat-core/frank-wolfe/rem:certified-scope``).
Read through the columns of an isometric dilation of the instrument, the same
block is ``L W L^dagger`` with enclosed columns and an exact core, and a Gram
floor fixes its rank (``foundations/cor:rank-over-factor-enclosure``). This
module forms that reading: ``receiver/detector-imperfections/
req:dark-composed-reference`` (vii), by ``receiver/thm:factor-blocks`` and
``receiver/component-catalogue/lem:catalogue-dilations``.

THE PASS, ON A RECEIVER WITHOUT PROBE INPUTS AND A COMPONENT GRAPH
=================================================================
1. **The port dilation** (:func:`port_dilation`; the lemma's (ii)): the
   elements compiled in the order of the linear extension as
   :func:`~certiqs_key.receiver.generic.compile_instrument` compiles them,
   restricted to the declared input modes, and beside them each element's
   loss rows ``Theta_j X_{j-1}`` (the lemma's (i), :func:`loss_factor`) and
   the efficiency layer's ``sqrt(1 - eta_k)`` rows. A loss row is formed only
   where the declared value that scales it is decided, in exact rational
   arithmetic, to make it non-zero: whether an element is lossless is read
   off its declared parameters, never off a computed number. A generic block
   (C10) gets its loss factor from a decomposition ``1 - G^dagger G =
   E^dagger D E`` formed and decided exactly; where none is formed, no
   dilation is. The entries are enclosed in the receiver's ball arithmetic
   (``receiver/lem:enclosure-arithmetic``), and rows enclosed exactly as zero
   are dropped.
2. **The count** (:func:`factor_enclosures`), per photon number ``n`` and
   letter ``v``, BEFORE ANY PERMANENT: the occupation vectors of weight ``n``
   on the dilation's rows with ``R_{cg^-1(v)|S_m} > 0``, counted per split of
   the photons over the ports and the loss modes, against the block's
   dimension. A factor enclosure with more columns than that fixes no rank,
   so none is formed (``columns_exceed_dimension``).
3. **The columns** (the theorem's (i)-(iii)): ``c_m = Fock(Omega)^dagger
   |m>``, entry ``conj(per Omega[m|m']) sqrt(1/(m! m'!))``; a column enclosed
   exactly as zero is dropped; the core is ``diag(R_{cg^-1(v)|S_m})``, exact
   rationals.

None is formed on the probe-conditioned route (its blocks are formed through
determinant prefactors, not a port dilation), on a route that declares port
Grams or an instrument matrix (the requirement's (b), which this engine does
not form; see :class:`FactorCause`), or in a run that declares enclosed
references not used (item (vi)). Each such block records its cause.
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.errors import HypothesisError as FoundationsHypothesis
from certiqs_key.foundations.exact import (
    ZERO,
    Cx,
    Matrix,
    conjugate_transpose,
    equal,
    factor_form,
    identity,
    matmul,
    subtract,
)
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.receiver.catalogue import (
    Beamsplitter,
    Component,
    GenericBlock,
    Loss,
    Mirror,
    ModeRouting,
    PhaseShifter,
    Polarizer,
    PolarizingBeamsplitter,
    Retarder,
    Rotator,
)
from certiqs_key.receiver.enclosure import Ball
from certiqs_key.receiver.generic import (
    BallField,
    GenericMatrix,
    _beamsplitter_core,
    _declared,
    _matmul,
    _permanent_by_tables,
    element_matrix,
)
from certiqs_key.receiver.graph import topological_order
from certiqs_key.receiver.request import InputRoute, ValidatedRequest

__all__ = [
    "ESTABLISHING_CLAIMS",
    "FactorCause",
    "FactorOffer",
    "PortDilation",
    "factor_enclosures",
    "loss_factor",
    "port_dilation",
]

#: The claims that establish a block's membership of the factor enclosure the
#: receiver forms on the component-graph route (``req:dark-composed-reference``
#: (vii); ``foundations/req:snap-reference`` (i) leaves them to this module).
ESTABLISHING_CLAIMS: Final[tuple[str, ...]] = (
    "receiver/thm:factor-blocks (iii)",
    "receiver/component-catalogue/lem:catalogue-dilations (ii)",
)

#: The mode a loss row belongs to, in :attr:`PortDilation.ports`.
LOSS_MODE: Final[int] = -1


class FactorCause(StrEnum):
    """Why a block carries no factor enclosure (``req:dark-composed-reference``)."""

    #: A receiver with probe inputs: its blocks are not formed through a port
    #: dilation.
    PROBE_CONDITIONED = "probe_conditioned"
    #: No port dilation of the declaration is formed: a route that declares
    #: port Grams or an instrument matrix (the requirement's (b), which this
    #: engine does not form), or a generic block with no exact decomposition.
    NO_PORT_DILATION = "no_port_dilation"
    #: More occupation vectors with a positive weight than the block's
    #: dimension: such a factor enclosure fixes no rank.
    COLUMNS_EXCEED_DIMENSION = "columns_exceed_dimension"
    #: The run declares enclosed references not used (item (vi)).
    ENCLOSED_REFERENCES_NOT_USED = "enclosed_references_not_used"


@dataclass(frozen=True)
class FactorOffer:
    """One block's factor enclosure for one letter, or why there is none."""

    factor: FactorEnclosure | None
    cause: FactorCause | None = None
    detail: str = ""

    def as_record(self) -> dict[str, object]:
        """JSON-ready: carried with its columns and largest radius, or the cause."""
        if self.factor is not None:
            radius = self.factor.largest_radius
            return {
                "carried": True,
                "columns": self.factor.columns,
                "largest_radius": str(radius),
                "largest_radius_float": float(radius),
            }
        return {
            "carried": False,
            "cause": None if self.cause is None else str(self.cause),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class PortDilation:
    """A port dilation ``Omega`` of the instrument (``receiver/def:port-dilation``).

    ``rows`` are the rows of ``Omega`` that are not enclosed exactly as zero,
    each over the declared inputs in their subsystem order; ``ports`` gives
    each row's port index, or :data:`LOSS_MODE` for a loss mode.
    """

    rows: tuple[tuple[Ball, ...], ...]
    ports: tuple[int, ...]


class NoDilation(Exception):
    """No port dilation is formed; the message says why."""


# ---------------------------------------------------------------------------
#  lem:catalogue-dilations (i): the loss factor of an entry
# ---------------------------------------------------------------------------


def _times(value: Cx, factor: Fraction) -> Cx:
    return Cx(value.re * factor, value.im * factor)


def _exact_decomposition(m: Matrix) -> tuple[Matrix, tuple[Fraction, ...]] | None:
    """Return ``(E, d)`` with ``m = E^dagger diag(d) E``, ``d > 0``, decided exactly.

    ``thm:factor-blocks`` (iv), the decomposition the requirement's (vii)(a)
    asks of a generic block: ``m = E_0^dagger X E_0`` exactly
    (:func:`~certiqs_key.foundations.exact.factor_form`, ``X`` positive
    definite), then ``X = U^dagger D U`` by the exact symmetric elimination,
    ``E = U E_0``; the identity is then decided exactly. ``None`` where ``m``
    is not positive semidefinite exactly; no row where ``m`` is zero.
    """
    try:
        found = factor_form(m)
    except FoundationsHypothesis:
        return None
    if found is None:
        return (), ()
    e0, x = found
    size = len(x)
    upper = [[ZERO] * size for _ in range(size)]
    d: list[Fraction] = []
    for k in range(size):
        pivot = x[k][k].re - sum(
            (d[i] * upper[i][k].squared_modulus for i in range(k)), Fraction(0)
        )
        if pivot <= 0:  # pragma: no cover - X is positive definite exactly
            return None
        d.append(pivot)
        upper[k][k] = Cx(Fraction(1), Fraction(0))
        for j in range(k + 1, size):
            total = x[k][j]
            for i in range(k):
                total = total - _times(upper[i][k].conjugate() * upper[i][j], d[i])
            upper[k][j] = total.over(pivot)
    e = matmul(tuple(tuple(row) for row in upper), e0)
    scaled = tuple(
        tuple(_times(entry, value) for entry in row)
        for row, value in zip(e, d, strict=True)
    )
    if not equal(matmul(conjugate_transpose(e), scaled), m):
        return None  # pragma: no cover - the identity holds by construction
    return e, tuple(d)


def _rows_of(
    field: BallField, scaled: Sequence[tuple[Fraction, Sequence[Ball]]]
) -> GenericMatrix[Ball]:
    """Return the rows ``sqrt(s) * row`` of the pairs whose ``s`` is not zero."""
    return [
        [field.sqrt(value) * entry for entry in row]
        for value, row in scaled
        if value != 0
    ]


def loss_factor(field: BallField, component: Component) -> GenericMatrix[Ball]:
    """Return the loss factor ``Theta`` of a catalogue entry over ``field``.

    Implements ``receiver/component-catalogue/lem:catalogue-dilations`` (i):
    ``Gamma^dagger Gamma + Theta^dagger Theta = 1`` on the entry's support. A
    row is formed only where the declared value that scales it is decided
    non-zero exactly (``D^flat``), so a lossless entry has none. The rows are
    over the support, in the catalogue's mode order (C1 and C2 on ``(p1H,
    p1V, p2H, p2V)``). Raises :class:`NoDilation` on a generic block with no
    exact decomposition of ``1 - G^dagger G``.
    """
    one, nil = field.one(), field.zero()
    if isinstance(component, Beamsplitter):
        core = _beamsplitter_core(
            field, _declared(component.transmittance), component.phase
        )
        rows: GenericMatrix[Ball] = []
        for i, loss in enumerate((component.loss_1, component.loss_2)):
            y = _declared(loss)
            if y == 0:
                continue
            root = field.sqrt(y)
            for polarisation in range(2):
                row = [nil] * 4
                for column in range(2):
                    row[2 * column + polarisation] = root * core[i][column]
                rows.append(row)
        return rows
    if isinstance(component, PolarizingBeamsplitter):
        # Xi^dagger [B(t_H) (+) B(t_V)] Xi on (p1H, p1V, p2H, p2V), as the
        # entry's element has it before its attenuation.
        core_h = _beamsplitter_core(
            field, _declared(component.transmittance_h), component.phase_h
        )
        core_v = _beamsplitter_core(
            field, _declared(component.transmittance_v), component.phase_v
        )
        block = [[nil] * 4 for _ in range(4)]
        for r in range(2):
            for c in range(2):
                block[2 * r][2 * c] = core_h[r][c]
                block[2 * r + 1][2 * c + 1] = core_v[r][c]
        losses = (component.loss_1, component.loss_2)
        return _rows_of(
            field, [(_declared(losses[r // 2]), block[r]) for r in range(4)]
        )
    if isinstance(component, Retarder):
        y = _declared(component.loss)
        return _rows_of(field, [(y, [one, nil]), (y, [nil, one])])
    if isinstance(component, Mirror):
        return _rows_of(
            field,
            [
                (1 - _declared(component.reflectivity_h), [one, nil]),
                (1 - _declared(component.reflectivity_v), [nil, one]),
            ],
        )
    if isinstance(component, Loss):
        size = len(component.efficiencies)
        return _rows_of(
            field,
            [
                (1 - _declared(eta), [one if j == i else nil for j in range(size)])
                for i, eta in enumerate(component.efficiencies)
            ],
        )
    if isinstance(component, Polarizer):
        cos, sin = field.cos_sin(component.angle)
        return _rows_of(
            field,
            [
                (1 - _declared(component.pass_transmittance), [cos, sin]),
                (1 - _declared(component.leak_transmittance), [-sin, cos]),
            ],
        )
    if isinstance(component, Rotator | PhaseShifter | ModeRouting):
        return []
    if isinstance(component, GenericBlock):
        g = tuple(
            tuple(Cx(Fraction(float(z.real)), Fraction(float(z.imag))) for z in row)
            for row in component.block
        )
        deficit = subtract(identity(len(g[0])), matmul(conjugate_transpose(g), g))
        found = _exact_decomposition(deficit)
        if found is None:
            raise NoDilation(
                "a generic block whose 1 - G^dagger G has no exact decomposition "
                "E^dagger D E (lem:catalogue-dilations (i), C10)"
            )
        e, d = found
        return [
            [field.sqrt(value) * field.gaussian(entry.re, entry.im) for entry in row]
            for row, value in zip(e, d, strict=True)
        ]
    raise FoundationsHypothesis(  # pragma: no cover - the catalogue is closed
        f"no loss factor for catalogue entry {type(component).__name__}"
    )


# ---------------------------------------------------------------------------
#  lem:catalogue-dilations (ii): the dilation of a compiled graph
# ---------------------------------------------------------------------------


def port_dilation(validated: ValidatedRequest, field: BallField) -> PortDilation:
    """Return the port dilation of a component graph, its zero rows dropped.

    Implements ``receiver/component-catalogue/lem:catalogue-dilations`` (ii):
    ``X_0`` the inclusion of the declared inputs, ``X_j = Gamma_{e_j}
    X_{j-1}`` in the order of the linear extension; the rows ``D_eta X_L`` on
    the modes, the efficiency layer's ``Theta_eta X_L`` (one row per mode of a
    port with ``eta_k < 1``, decided exactly) and each element's
    ``Theta_j X_{j-1}``. The rows on the modes are those of the compiled
    instrument matrix (:func:`~certiqs_key.receiver.generic.compile_instrument`
    computes them the same way), so the ports' Grams are the instrument's.
    Raises :class:`NoDilation` off the component-graph route or where a
    generic block has no exact decomposition.
    """
    request = validated.request
    graph = request.element_graph
    if validated.route is not InputRoute.ELEMENT_GRAPH or graph is None:
        raise NoDilation(
            "the route declares port Grams or an instrument matrix; the engine "
            "forms no decomposition of them (req:dark-composed-reference (vii)(b))"
        )
    order = topological_order(graph)
    assert order is not None  # (E2) is refused at validation
    mode_count = len(request.mode_space)
    columns = request.input_modes.subsystem_order()
    x: GenericMatrix[Ball] = [
        [field.one() if mode == column else field.zero() for column in columns]
        for mode in range(mode_count)
    ]
    loss_rows: GenericMatrix[Ball] = []
    for name in order:
        element = graph.element(name)
        support_rows = [x[mode] for mode in element.support]
        theta = loss_factor(field, element.component)
        if theta:
            loss_rows.extend(_matmul(field, theta, support_rows))
        updated = _matmul(field, element_matrix(field, element.component), support_rows)
        x = list(x)
        for position, mode in enumerate(element.support):
            x[mode] = updated[position]
    owner = {
        row: k for k, (_, rows) in enumerate(request.port_map.entries) for row in rows
    }
    etas = [_declared(port.efficiency) for port in request.detector_layer]
    rows: GenericMatrix[Ball] = []
    ports: list[int] = []
    for mode in range(mode_count):
        k = owner.get(mode, LOSS_MODE)
        scale = field.one() if k == LOSS_MODE else field.sqrt(etas[k])
        rows.append([scale * entry for entry in x[mode]])
        ports.append(k)
    for mode in range(mode_count):
        k = owner.get(mode, LOSS_MODE)
        if k != LOSS_MODE and etas[k] != 1:
            root = field.sqrt(1 - etas[k])
            rows.append([root * entry for entry in x[mode]])
            ports.append(LOSS_MODE)
    rows.extend(loss_rows)
    ports.extend([LOSS_MODE] * len(loss_rows))
    kept = [i for i, row in enumerate(rows) if not all(entry.is_zero for entry in row)]
    return PortDilation(
        tuple(tuple(rows[i]) for i in kept), tuple(ports[i] for i in kept)
    )


# ---------------------------------------------------------------------------
#  thm:factor-blocks (i)-(iii): the count, the columns, the factor enclosure
# ---------------------------------------------------------------------------


def _vectors(size: int, photons: int) -> Iterator[tuple[int, ...]]:
    """Yield the occupation vectors of ``size`` modes and weight ``photons``."""
    if size == 0:
        if photons == 0:
            yield ()
        return
    for first in range(photons, -1, -1):
        for rest in _vectors(size - 1, photons - first):
            yield (first, *rest)


def _admitted(
    dilation: PortDilation,
    photons: int,
    weight: Mapping[frozenset[int], Fraction],
    limit: int,
) -> list[tuple[tuple[int, ...], frozenset[int]]] | None:
    """Return the vectors of weight ``n`` of positive weight; ``None`` past ``limit``.

    The count of ``req:dark-composed-reference`` (vii), decided before any
    column is computed: per split of the photons over the groups of rows (the
    ports and the loss modes), the vectors number ``prod C(r_g + n_g - 1,
    n_g)`` and share the click pattern of the ports with a photon.
    """
    groups: dict[int, list[int]] = {}
    for row, port in enumerate(dilation.ports):
        groups.setdefault(port, []).append(row)
    keys = sorted(groups)
    total, chosen = 0, []
    for split in _vectors(len(keys), photons):
        pattern = frozenset(k for k, count in zip(keys, split, strict=True)
                            if count and k != LOSS_MODE)
        if weight.get(pattern, Fraction(0)) <= 0:
            continue
        total += math.prod(
            math.comb(len(groups[k]) + count - 1, count)
            for k, count in zip(keys, split, strict=True)
        )
        if total > limit:
            return None
        chosen.append((split, pattern))
    out: list[tuple[tuple[int, ...], frozenset[int]]] = []
    for split, pattern in chosen:
        parts = [list(_vectors(len(groups[k]), count))
                 for k, count in zip(keys, split, strict=True)]
        for combination in _product(parts):
            vector = [0] * len(dilation.ports)
            for k, part in zip(keys, combination, strict=True):
                for row, count in zip(groups[k], part, strict=True):
                    vector[row] = count
            out.append((tuple(vector), pattern))
    return out


def _product(
    parts: Sequence[Sequence[tuple[int, ...]]],
) -> Iterator[tuple[tuple[int, ...], ...]]:
    if not parts:
        yield ()
        return
    for head in parts[0]:
        for tail in _product(parts[1:]):
            yield (head, *tail)


def _column(
    field: BallField,
    dilation: PortDilation,
    vector: tuple[int, ...],
    inputs: Sequence[tuple[int, ...]],
) -> list[Ball]:
    """Return ``c_m``: ``conj(per Omega[m|m']) sqrt(1/(m! m'!))`` over ``m'``.

    ``thm:factor-blocks`` (i), (ii), with ``lem:fock-permanent-maps`` (ii):
    the permanent over the rows ``m`` names and the inputs ``m'`` names, by
    the grouped sum of :func:`~certiqs_key.receiver.generic.
    _permanent_by_tables`; an entry whose every term has a factor enclosed
    exactly as zero is the exact zero.
    """
    used = [row for row, count in enumerate(vector) if count]
    counts = [vector[row] for row in used]
    cache: dict[tuple[int, int, int], Ball] = {}

    def powers(i: int, j: int, count: int) -> Ball:
        key = (i, j, count)
        if key not in cache:
            entry = dilation.rows[used[i]][j]
            cache[key] = entry if count == 1 else powers(i, j, count - 1) * entry
        return cache[key]

    left = math.prod(math.factorial(count) for count in counts)
    column = []
    for target in inputs:
        permanent = _permanent_by_tables(field, counts, target, powers)
        right = math.prod(math.factorial(count) for count in target)
        column.append(permanent.conjugate() * field.sqrt(Fraction(1, left * right)))
    return column


def factor_enclosures(
    dilation: PortDilation,
    field: BallField,
    *,
    photons: int,
    inputs: int,
    weights: Mapping[str, Mapping[frozenset[int], Fraction]],
) -> dict[str, FactorOffer]:
    """Return, per letter, the factor enclosure of the block ``F~^(n)_{v|off}``.

    Implements ``receiver/detector-imperfections/req:dark-composed-reference``
    (vii) by ``receiver/thm:factor-blocks`` (iii) at the weights
    ``w_S = R_{cg^-1(v)|S}`` (``weights``, exact rationals): the count against
    the block's dimension ``binom(inputs + n - 1, n)`` first (none past it,
    ``columns_exceed_dimension``), then the columns of the admitted vectors,
    those enclosed exactly as zero dropped, with the core of their weights.
    The block's rows are in the occupation basis order of the reference.
    """
    from certiqs_key.receiver.fock import occupation_vectors

    basis = occupation_vectors(inputs, photons)
    dimension = len(basis)
    offers: dict[str, FactorOffer] = {}
    for letter, weight in weights.items():
        admitted = _admitted(dilation, photons, weight, dimension)
        if admitted is None:
            offers[letter] = FactorOffer(
                None,
                FactorCause.COLUMNS_EXCEED_DIMENSION,
                f"more than {dimension} occupation vectors of weight {photons} "
                "with a positive weight",
            )
            continue
        centre: list[list[Cx]] = [[] for _ in range(dimension)]
        radii: list[list[Fraction]] = [[] for _ in range(dimension)]
        core: list[Fraction] = []
        for vector, pattern in admitted:
            column = _column(field, dilation, vector, basis)
            if all(entry.is_zero for entry in column):
                continue
            for i, entry in enumerate(column):
                centre[i].append(entry.centre)
                radii[i].append(entry.radius)
            core.append(weight[pattern])
        offers[letter] = FactorOffer(
            FactorEnclosure(
                tuple(tuple(row) for row in centre),
                tuple(tuple(row) for row in radii),
                tuple(core),
            )
        )
    return offers
