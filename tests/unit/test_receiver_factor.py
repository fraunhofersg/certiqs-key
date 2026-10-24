"""The receiver's factor enclosures: the dilation, the count, the columns.

``receiver/detector-imperfections/req:dark-composed-reference`` (vii), by
``receiver/thm:factor-blocks``, ``receiver/def:port-dilation``,
``receiver/lem:fock-permanent-maps`` and
``receiver/component-catalogue/lem:catalogue-dilations``. CONTRACT TESTS, each
failing where its clause is broken:

* a loss row is formed only where the declared parameter that scales it is
  decided non-zero EXACTLY: ``1`` gives none, ``0.9999`` gives one;
* every loss factor completes its entry to an isometry, and the dilation of
  the ideal device is one (``Omega^dagger Omega = 1`` within its enclosure)
  whose port Grams are the instrument's;
* the count refuses where the columns would exceed the block's dimension (the
  lossy two-photon device) and admits the ideal analyser's rank-one blocks;
* the factor enclosure's members overlap the block's entrywise enclosure on
  every block of the three ideal canaries, and an element with no column is
  the one the dilation decides zero;
* none is offered on the probe-conditioned route, on a route with no
  dilation, or where the run declares enclosed references not used.
"""

from __future__ import annotations

from collections.abc import Iterator
from fractions import Fraction as F
from types import SimpleNamespace
from typing import Any

import pytest
from probe_presence import requires_probe

from certiqs_key.foundations.reference import fixes_rank
from certiqs_key.receiver import construct
from certiqs_key.receiver.catalogue import (
    Beamsplitter,
    GenericBlock,
    Loss,
    Mirror,
    Polarizer,
    PolarizingBeamsplitter,
    Retarder,
)
from certiqs_key.receiver.enclosure import Ball
from certiqs_key.receiver.factor import (
    LOSS_MODE,
    FactorCause,
    NoDilation,
    loss_factor,
    port_dilation,
)
from certiqs_key.receiver.generic import (
    BallField,
    compile_instrument,
    element_matrix,
    port_grams_of,
)
from certiqs_key.receiver.graph import topological_order
from certiqs_key.receiver.numerics import PiMultiple
from certiqs_key.receiver.request import InputRoute

pytestmark = pytest.mark.contract

FIELD = BallField(128)


def _contains_zero(ball: Ball) -> bool:
    return ball.re * ball.re + ball.im * ball.im <= ball.radius * ball.radius


def _gram(rows: list[list[Ball]], columns: int) -> list[list[Ball]]:
    """``X^dagger X`` of a rows-by-columns matrix of balls."""
    out = []
    for a in range(columns):
        row = []
        for b in range(columns):
            total = Ball(F(0))
            for line in rows:
                total = total + line[a].conjugate() * line[b]
            row.append(total)
        out.append(row)
    return out


def _is_identity(matrix: list[list[Ball]]) -> bool:
    return all(
        _contains_zero(entry - Ball(F(1 if i == j else 0)))
        for i, row in enumerate(matrix)
        for j, entry in enumerate(row)
    )


# lem:catalogue-dilations (i): the loss rows, decided exactly


@pytest.mark.parametrize(
    ("component", "rows"),
    [
        (Loss((1.0, 1.0)), 0),
        (Loss((1.0, 0.9999)), 1),
        (Mirror(1.0, 1.0, 0, 0, False), 0),
        (Mirror(1.0, 0.9999, 0, 0, False), 1),
        (Retarder.half_wave(PiMultiple(F(1, 7)), 0), 0),
        (Retarder.half_wave(PiMultiple(F(1, 7)), 1e-4), 2),
        (Beamsplitter(0.5, 0, 0, 0), 0),
        (Beamsplitter(0.5, 0, 1e-4, 0), 2),
        (PolarizingBeamsplitter(1, 0, 0, 0, 0, 0), 0),
        (PolarizingBeamsplitter(1, 0, 0, 0, 0, 0.25), 2),
        (Polarizer(PiMultiple(F(1, 7)), 1.0, 1.0), 0),
        (Polarizer(PiMultiple(F(1, 7)), 1.0, 0.0), 1),
        (Polarizer(PiMultiple(F(1, 7)), 0.9999, 0.0), 2),
    ],
)
def test_a_loss_row_is_formed_only_where_its_value_is_not_zero(
    component: Any, rows: int
) -> None:
    """Rows of ``D^flat``; the entry and its loss factor make an isometry."""
    theta = loss_factor(FIELD, component)
    assert len(theta) == rows
    gamma = element_matrix(FIELD, component)
    size = len(gamma)
    total = [
        [a + b for a, b in zip(row_g, row_t, strict=True)]
        for row_g, row_t in zip(_gram(gamma, size), _gram(theta, size), strict=True)
    ] if theta else _gram(gamma, size)
    assert _is_identity(total)


def test_a_generic_block_takes_an_exact_decomposition() -> None:
    """C10: ``1 - G^dagger G = E^dagger D E`` formed and decided exactly."""
    half = loss_factor(FIELD, GenericBlock.of([[0.5, 0], [0, 1]]))
    assert len(half) == 1 and half[0][1].is_zero
    assert _contains_zero(half[0][0] * half[0][0] - Ball(F(3, 4)))
    # A rational square root is exact: the row (1, 0) of a block that drops a mode.
    (dropped,) = loss_factor(FIELD, GenericBlock.of([[0, 0], [0, 1]]))
    assert all(entry.is_exact for entry in dropped)
    assert (dropped[0].re, dropped[1].is_zero) == (F(1), True)
    assert loss_factor(FIELD, GenericBlock.of([[0, 1], [1, 0]])) == []
    with pytest.raises(NoDilation, match="C10"):
        loss_factor(FIELD, GenericBlock.of([[2, 0], [0, 1]]))


# def:port-dilation and lem:catalogue-dilations (ii) on a device


def _device(**parameters: Any) -> Any:
    """Return the optics receiver's validated request, channel and references."""
    from instances.common.optics import ReceiverParameters, receiver_request

    seen: list[tuple[Any, Any, Any]] = []
    real = construct.dark_composed_reference

    def spy(validated: Any, channel: Any, *args: Any, **kwargs: Any) -> Any:
        found = real(validated, channel, *args, **kwargs)
        seen.append((validated, channel, found))
        return found

    led = parameters.pop("led", None)
    exact_only = parameters.pop("exact_only", False)
    request = receiver_request(ReceiverParameters(**parameters), led)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(construct, "dark_composed_reference", spy)
        construct.construct_receiver(request, exact_reference_only=exact_only)
    ((validated, channel, references),) = seen
    return validated, channel, references


#: Declared at the factored loss one: these tests read the efficiency layer
#: itself (its loss rows), not the normalization
#: (receiver/detector-imperfections/req:efficiency-normalization).
IDEAL = {
    "half_wave_angle": F(1, 7),
    "photon_cutoff": 2,
    "efficiency_normalization": F(1),
}


def test_the_ideal_dilation_is_an_isometry_with_the_instruments_grams() -> None:
    validated, _, _ = _device(**IDEAL)
    dilation = port_dilation(validated, FIELD)
    inputs = len(validated.request.input_modes.subsystem_order())
    assert _is_identity(_gram([list(row) for row in dilation.rows], inputs))
    request = validated.request
    port_rows = [rows for _, rows in request.port_map.entries]
    gamma = compile_instrument(
        FIELD,
        request.element_graph,
        len(request.mode_space),
        topological_order(request.element_graph),
        port_rows,
        [port.efficiency for port in request.detector_layer],
    )
    grams = port_grams_of(
        FIELD, gamma, request.input_modes.subsystem_order(), port_rows
    )
    for k, gram in enumerate(grams):
        mine = _gram(
            [list(row) for row, port in zip(dilation.rows, dilation.ports, strict=True)
             if port == k],
            inputs,
        )
        for a, row in enumerate(gram):
            for b, entry in enumerate(row):
                assert _contains_zero(entry - mine[a][b])
    assert LOSS_MODE not in dilation.ports, "the ideal device has no loss mode"


@pytest.mark.parametrize(("eta", "rows"), [(F(1), 0), (F(9999, 10000), 4)])
def test_the_efficiency_layer_forms_a_row_only_below_one(eta: F, rows: int) -> None:
    validated, _, _ = _device(**IDEAL, efficiency=(eta,) * 4)
    dilation = port_dilation(validated, FIELD)
    assert dilation.ports.count(LOSS_MODE) == rows


def test_a_route_with_declared_grams_forms_no_dilation() -> None:
    validated = SimpleNamespace(
        route=InputRoute.PORT_GRAMS, request=SimpleNamespace(element_graph=None)
    )
    with pytest.raises(NoDilation, match=r"\(vii\)\(b\)"):
        port_dilation(validated, FIELD)  # type: ignore[arg-type]


# req:dark-composed-reference (vii): the count and the offers


def _offers(references: Any) -> dict[tuple[str, str], Any]:
    (reference,) = references
    return {
        (block.label, letter): offer
        for block in reference.offered
        for letter, offer in block.factors
    }


def test_the_ideal_analysers_blocks_carry_rank_one_factors() -> None:
    """``N = 2``: rank one at every single click, zero where nothing can click.

    The two-photon multiclick element has six output patterns in a block of
    dimension three: the count refuses it before any permanent.
    """
    _, _, references = _device(**IDEAL)
    offers = _offers(references)
    for photons in (1, 2):
        for letter in ("H", "V", "D", "A"):
            factor = offers[(f"m={photons}", letter)].factor
            assert factor is not None and factor.columns == 1 and fixes_rank(factor)
        nothing = offers[(f"m={photons}", "nc")].factor
        assert nothing is not None and nothing.columns == 0
    refused = offers[("m=2", "mc")]
    assert refused.factor is None
    assert refused.cause is FactorCause.COLUMNS_EXCEED_DIMENSION
    (reference,) = references
    assert reference.reference is not None
    claims = reference.reference.identity.establishing_claims
    assert "receiver/thm:factor-blocks (iii)" in claims
    assert "receiver/component-catalogue/lem:catalogue-dilations (ii)" in claims
    record = reference.as_record()
    blocks = {block["block"]: block for block in record["offered"]}
    assert blocks["m=2"]["factor_enclosures"]["mc"]["cause"] == (
        "columns_exceed_dimension"
    )
    assert blocks["m=1"]["factor_enclosures"]["H"]["columns"] == 1


def test_the_count_refuses_the_lossy_two_photon_device() -> None:
    """Efficiency 9/10, no dark counts: ``1 + 4`` patterns at ``n = 2`` in dimension 3.

    One photon in the port and one in each of the four loss modes: the count
    refuses the block, which the certified evaluation then reads through its
    entrywise enclosure alone (and certifies through the fallback).
    """
    _, _, references = _device(**IDEAL, efficiency=(F(9, 10),) * 4)
    offers = _offers(references)
    assert offers[("m=1", "H")].factor is not None
    for letter in ("H", "V", "D", "A"):
        assert offers[("m=2", letter)].cause is FactorCause.COLUMNS_EXCEED_DIMENSION


@requires_probe
def test_the_probe_conditioned_route_offers_none() -> None:
    from instances.common.led import LedProbe

    _, _, references = _device(photon_cutoff=1, led=LedProbe(window=4))
    for reference in references:
        for offer in _offers([reference]).values():
            assert offer.factor is None
            assert offer.cause is FactorCause.PROBE_CONDITIONED


def test_enclosed_references_not_used_offer_none() -> None:
    _, _, references = _device(**IDEAL, exact_only=True)
    offers = _offers(references)
    assert offers and all(
        offer.cause is FactorCause.ENCLOSED_REFERENCES_NOT_USED
        for offer in offers.values()
    )


def _members_overlap(enclosure: Any) -> bool:
    """``L W L^dagger`` over the box overlaps the entrywise enclosure entry by entry."""
    factor = enclosure.factor
    columns = [
        [Ball(c.re, c.im, r) for c, r in zip(row, rad, strict=True)]
        for row, rad in zip(factor.centre, factor.radii, strict=True)
    ]
    size = factor.dimension
    for i in range(size):
        for j in range(size):
            total = Ball(F(0))
            for m, weight in enumerate(factor.core):
                term = columns[i][m] * columns[j][m].conjugate()
                total = total + term.scaled(weight)
            centre = enclosure.centre[i][j]
            gap = total - Ball(centre.re, centre.im, enclosure.radii[i][j])
            if not _contains_zero(gap):
                return False
    return True


def _carried(references: Any) -> Iterator[Any]:
    for reference in references:
        if reference.reference is None:
            continue
        for block in reference.reference.blocks:
            for enclosure in block.elements:
                if enclosure.factor is not None:
                    yield enclosure


@pytest.mark.parametrize(
    "parameters",
    [IDEAL, {"half_wave_angle": F(1, 7), "photon_cutoff": 1}],
    ids=["optical-N2", "N1"],
)
def test_the_members_overlap_the_entrywise_enclosure(parameters: Any) -> None:
    """The prototype's ``contain.py``: one element, two enclosures that meet."""
    _, _, references = _device(**parameters)
    carried = list(_carried(references))
    assert carried
    assert all(_members_overlap(enclosure) for enclosure in carried)


#: The three ideal canaries at angle 1/7 (tests/integration/
#: test_key_rate_canaries.py), by instance and device.
IDEAL_CANARIES = {
    "optical-N2-ideal-angle-1/7": (
        "optical_bb84",
        {"photon_cutoff": F(2), "exact_window": F(3), "half_wave_angle": F(1, 7)},
    ),
    "decoy-N1-ideal-angle-1/7": ("decoy_bb84", {"half_wave_angle": F(1, 7)}),
    "bbm92-spdc-angle-1/7-at-bob": (
        "bbm92",
        {"source_model": "spdc", "bob_half_wave_angle": F(1, 7)},
    ),
}


@pytest.mark.parametrize("name", list(IDEAL_CANARIES))
def test_on_every_ideal_canary_the_two_enclosures_meet(name: str) -> None:
    """Every carried block of every station: ``L W L^dagger`` meets its enclosure.

    The preparation alone (no solve) builds each station's reference.
    """
    import importlib

    from certiqs_key.runs.config import SolverSettings

    instance, device = IDEAL_CANARIES[name]
    surface = importlib.import_module(f"instances.{instance}.surface")
    base = surface.default_config(solver=SolverSettings(method="fw", max_iterations=3))
    seen: list[Any] = []
    real = construct.dark_composed_reference

    def spy(validated: Any, channel: Any, *args: Any, **kwargs: Any) -> Any:
        found = real(validated, channel, *args, **kwargs)
        seen.append(found)
        return found

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(construct, "dark_composed_reference", spy)
        surface.preparation(base.with_(device={**base.device, **device}))
    carried = [enclosure for found in seen for enclosure in _carried(found)]
    assert carried, "a factor enclosure is carried"
    assert all(_members_overlap(enclosure) for enclosure in carried)


def _stub(
    elements: tuple[Any, ...], eta: F = F(1), mode_count: int = 1
) -> Any:
    """Return a validated request of a one-port receiver on mode 0, input 0."""
    from certiqs_key.receiver.graph import ElementGraph

    return SimpleNamespace(
        route=InputRoute.ELEMENT_GRAPH,
        request=SimpleNamespace(
            element_graph=ElementGraph(elements=elements),
            mode_space=tuple(range(mode_count)),
            input_modes=SimpleNamespace(subsystem_order=lambda: (0,)),
            port_map=SimpleNamespace(entries=(("p", (0,)),)),
            detector_layer=(SimpleNamespace(efficiency=eta),),
        ),
    )


def test_an_elements_loss_rows_enter_the_dilation() -> None:
    """C7 at 1/2 on the one mode: the port row and the loss row, ``1/2`` each."""
    from certiqs_key.receiver.graph import Element

    dilation = port_dilation(_stub((Element("loss", Loss((F(1, 2),)), (0,)),)), FIELD)
    assert dilation.ports == (0, LOSS_MODE)
    assert _is_identity(_gram([list(row) for row in dilation.rows], 1))


def test_a_value_a_float_would_round_to_one_still_forms_its_row() -> None:
    """Decided in exact arithmetic: ``1 - 10^-30`` is not ``1``, though its float is."""
    near = F(10**30 - 1, 10**30)
    assert float(near) == 1.0
    dilation = port_dilation(_stub((), eta=near), FIELD)
    assert dilation.ports.count(LOSS_MODE) == 1
    assert _is_identity(_gram([list(row) for row in dilation.rows], 1))
    (row,) = loss_factor(FIELD, Loss((near,)))
    assert not row[0].is_zero


def test_rows_enclosed_exactly_as_zero_are_dropped() -> None:
    """A mode no input reaches is no row of the dilation (and counts no vector)."""
    dilation = port_dilation(_stub((), mode_count=3), FIELD)
    assert len(dilation.rows) == 1
    assert all(not all(entry.is_zero for entry in row) for row in dilation.rows)


def test_the_count_comes_before_any_permanent() -> None:
    """The lossy two-photon block is refused with no column computed."""
    from certiqs_key.receiver import factor as factor_module
    from certiqs_key.receiver.factor import factor_enclosures

    validated, channel, _ = _device(**IDEAL, efficiency=(F(9, 10),) * 4)
    dilation = port_dilation(validated, FIELD)
    calls: list[Any] = []
    real = factor_module._column

    def counted(*args: Any) -> Any:
        calls.append(args[2])
        return real(*args)

    from certiqs_key.receiver.reference import dark_weights

    coarse = validated.request.outcome_coarse_graining
    weights = dark_weights(channel, {"H": coarse.fibre("H")})
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(factor_module, "_column", counted)
        offers = factor_enclosures(
            dilation, FIELD, photons=2, inputs=2, weights=weights
        )
    assert offers["H"].cause is FactorCause.COLUMNS_EXCEED_DIMENSION
    assert calls == []


def test_the_core_is_the_exact_dark_weight() -> None:
    """With dark counts the vacuum block's one column weighs ``(1 - p)^4`` exactly."""
    p = F(1, 10**6)
    _, _, references = _device(**IDEAL, dark_count=(p,) * 4)
    offer = _offers(references)[("m=0", "nc")]
    assert offer.factor is not None and offer.factor.core == ((1 - p) ** 4,)
    # Dark counts add clicks and remove none: on a lossless device one photon
    # clicks H alone only from the pattern {H}, so the block keeps one column,
    # its weight the three silent ports' (1 - p)^3.
    single = _offers(references)[("m=1", "H")].factor
    assert single is not None and single.core == ((1 - p) ** 3,)


def test_the_columns_are_conjugated_on_a_complex_instrument() -> None:
    """A quarter-wave plate at ``pi/8`` before two one-mode ports.

    ``c_m`` is the conjugate of the permanent, so ``c c^dagger`` is the port's
    Gram ``A_0`` and not its transpose; on a complex instrument the two differ.
    """
    from certiqs_key.receiver.graph import Element, ElementGraph

    plate = Retarder.quarter_wave(PiMultiple(F(1, 8)), 0)
    validated = SimpleNamespace(
        route=InputRoute.ELEMENT_GRAPH,
        request=SimpleNamespace(
            element_graph=ElementGraph(elements=(Element("qwp", plate, (0, 1)),)),
            mode_space=(0, 1),
            input_modes=SimpleNamespace(subsystem_order=lambda: (0, 1)),
            port_map=SimpleNamespace(entries=(("h", (0,)), ("v", (1,)))),
            detector_layer=(
                SimpleNamespace(efficiency=F(1)), SimpleNamespace(efficiency=F(1))
            ),
        ),
    )
    from certiqs_key.receiver.factor import factor_enclosures

    dilation = port_dilation(validated, FIELD)  # type: ignore[arg-type]
    offers = factor_enclosures(
        dilation, FIELD, photons=1, inputs=2, weights={"h": {frozenset({0}): F(1)}}
    )
    factor = offers["h"].factor
    assert factor is not None and factor.columns == 1
    gamma = compile_instrument(FIELD, validated.request.element_graph, 2,
                               ("qwp",), [(0,), (1,)], [1, 1])
    (gram, _) = port_grams_of(FIELD, gamma, (0, 1), [(0,), (1,)])
    assert any(not entry.is_zero and entry.im != 0 for row in gram for entry in row)
    column = [
        Ball(c.re, c.im, r)
        for (c,), (r,) in zip(factor.centre, factor.radii, strict=True)
    ]
    # The block's rows are the occupation basis, ascending lexicographic:
    # (0, 1), a photon in input 1, comes first.
    from certiqs_key.receiver.fock import occupation_vectors

    mode = [vector.index(1) for vector in occupation_vectors(2, 1)]
    for a in range(2):
        for b in range(2):
            member = column[a] * column[b].conjugate()
            assert _contains_zero(member - gram[mode[a]][mode[b]])
