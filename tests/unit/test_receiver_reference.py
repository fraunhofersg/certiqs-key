"""The receiver's dark-composed reference: exact route, enclosures, noise floor.

Contract tests of ``receiver/req:exact-route-decision``,
``receiver/thm:enclosed-blocks``, ``receiver/thm:exact-blocks``,
``receiver/detector-imperfections/req:dark-composed-reference``,
``receiver/detector-imperfections/prop:noise-floor`` and
``receiver/detector-imperfections/req:snap-fix``, with the snap of
``foundations/req:snap-reference`` reading the reference the way the declaring
instance will. Every expectation below is read off the declaration or a
claim, never off the function under test.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest
from probe_presence import requires_probe, with_probe
from receiver_povm_support import (
    DECLARED_TOLERANCES_WITHOUT_EXACT_WINDOW,
    MACHINE_AGREEMENT,
    bb84_channel_only_request,
    probe_free_matrix_request,
    probe_receiver_request,
)

from certiqs_key.foundations.reference import ReferenceKind, enclosure_pd
from certiqs_key.foundations.resting import RestingCause
from certiqs_key.foundations.snap import (
    BlockSnapRecord,
    BlockStatus,
    MeasurementSnap,
    SnapSettings,
    snap_measurement_family,
)
from certiqs_key.receiver import (
    Assurance,
    Beamsplitter,
    Element,
    ElementGraph,
    GenericBlock,
    GramFamily,
    InputModes,
    Mode,
    ModeSpace,
    Polarization,
    PortMap,
    ProbeDeclaration,
    ProbeSetting,
    ReceiverRequest,
    Retarder,
    construct_receiver,
)
from certiqs_key.receiver.artifact import EmittedBlocks, ReceiverMeasurementArtifact
from certiqs_key.receiver.construct import _dark_channel
from certiqs_key.receiver.dark import DarkCountChannel, DarkCountRoute
from certiqs_key.receiver.enclosure import Ball
from certiqs_key.receiver.factor import ESTABLISHING_CLAIMS as FACTOR_CLAIMS
from certiqs_key.receiver.generic import (
    BallField,
    FloatField,
    NoEnclosure,
    element_blocks,
    unconditioned_pairs,
)
from certiqs_key.receiver.numerics import PiMultiple
from certiqs_key.receiver.reference import (
    DARK_COMPOSITION_CLAIM,
    ExactRouteCause,
    ReferenceCause,
    dark_composed_reference,
    enclose_port_grams,
)
from certiqs_key.receiver.request import ValidatedRequest, validate_request
from certiqs_key.receiver.settings import setting_construction
from certiqs_key.receiver.snapfix import receiver_fix, receiver_fixes

pytestmark = pytest.mark.contract

NOISY = {
    "efficiencies": (Fraction(9, 10),) * 4,
    "dark_counts": (Fraction(1, 1000),) * 4,
}
#: Loss and dark counts whose products are dyadic, so that the binary64
#: evaluation of the dark-composed blocks can hit an exact entry exactly.
DYADIC_NOISY = {
    "efficiencies": (Fraction(7, 8),) * 4,
    "dark_counts": (Fraction(1, 1024),) * 4,
}
LATTICE = 40
TAU = 1e-9

#: The route-(ii) receivers: the probe-free twin of ``I-PROBE`` in every tree,
#: ``I-PROBE`` itself where the removable probe-conditioning submodule is present.
MATRIX_REQUESTS: tuple[Callable[[], ReceiverRequest], ...] = (
    probe_free_matrix_request,
    *with_probe(probe_receiver_request),
)
#: Whether the route-(iii) splitter receiver declares its second input a probe:
#: never in a tree without the submodule.
PROBE_FLAGS: tuple[bool, ...] = (False, *with_probe(True))


def _pi_plate(request: ReceiverRequest, coefficient: Fraction) -> ReceiverRequest:
    """Return the request with its half-wave plate at ``coefficient * pi``."""
    graph = request.element_graph
    assert graph is not None
    elements = tuple(
        replace(element, component=Retarder.half_wave(PiMultiple(coefficient), 0))
        if element.name == "hwp"
        else element
        for element in graph.elements
    )
    return replace(request, element_graph=ElementGraph(elements, graph.edges))


def _bb84_pi(photon_cutoff: int, **device: object) -> ReceiverRequest:
    """Return Example ex:bb84's receiver, its plate at pi/8 as a coefficient of pi."""
    return _pi_plate(
        bb84_channel_only_request(photon_cutoff=photon_cutoff, **device),  # type: ignore[arg-type]
        Fraction(1, 8),
    )


def _artifact(request: ReceiverRequest) -> ReceiverMeasurementArtifact:
    emission = construct_receiver(request)
    assert emission.refusal is None, emission.refusal
    assert emission.artifact is not None
    return emission.artifact


def _snap(family: EmittedBlocks, **policy: object) -> MeasurementSnap:
    """Snap the dark-composed family against its offered reference."""
    reference = family.reference.reference
    assert reference is not None
    data = {
        f"m={photons}": [block for _, block in letters]
        for photons, letters in family.dark_composed
    }
    return snap_measurement_family(
        data,
        alphabet=reference.alphabet,
        tolerance=TAU,
        lattice_exponent=LATTICE,
        site="receiver_photon_blocks",
        reference=reference,
        settings=SnapSettings(**policy),  # type: ignore[arg-type]
        setting=family.setting,
    )


def _probe_graph_request(
    transmittance: Fraction, probe: bool = True
) -> ReceiverRequest:
    """Return a route-(iii) receiver: one splitter mixing two declared inputs.

    With ``probe`` the second input is a probe mode; without it both inputs
    are channel modes and the receiver is probe-free. The port Grams carry
    ``sqrt(x (1 - x))`` in their off-diagonal entries, which is irrational at
    ``x = 1/3``.
    """
    space = ModeSpace.declare(
        Mode(path, polarization, 0)
        for path in ("C", "L")
        for polarization in (Polarization.H, Polarization.V)
    )
    index = {mode.label: position for position, mode in enumerate(space.modes)}
    graph = ElementGraph(
        (
            Element(
                "bs",
                Beamsplitter(transmittance, 0, 0, 0),
                (index["C_H"], index["C_V"], index["L_H"], index["L_V"]),
            ),
        ),
    )
    request = probe_receiver_request()
    request = replace(
        request,
        mode_space=space,
        input_modes=InputModes(channel=(index["C_H"],), source=(index["L_H"],)),
        port_map=PortMap((("1", (index["C_H"],)), ("2", (index["L_H"],)))),
        probe_declaration=ProbeDeclaration(
            (ProbeSetting("off", (0,)), ProbeSetting("on", (Fraction(1, 2),)))
        ),
        numerical_tolerances=dict(DECLARED_TOLERANCES_WITHOUT_EXACT_WINDOW),
        requested_assurance=Assurance.ESTIMATE,
        instrument_matrix=None,
        element_graph=graph,
    )
    if probe:
        return request
    return replace(
        request,
        input_modes=InputModes(channel=(index["C_H"], index["L_H"]), source=()),
        probe_declaration=ProbeDeclaration.probe_free(),
        tail_window={},
    )


# ---------------------------------------------------------------------------
#  req:exact-route-decision
# ---------------------------------------------------------------------------


def test_a_plate_given_as_a_coefficient_of_pi_is_on_the_exact_route() -> None:
    """Item (ii): at pi/8 behind ideal splitters the port Grams are rational."""
    decision, grams = enclose_port_grams(validate_request(_bb84_pi(2)))
    assert decision.has_exact_model and decision.on_exact_route
    assert decision.decided_by == "(ii)" and decision.cause is None
    assert grams is not None and grams.exact


def test_a_plate_given_in_radians_is_off_the_route_and_its_grams_enclosed() -> None:
    """Items (ii)-(iv): a non-zero radian angle is not represented; enclosed instead."""
    request = bb84_channel_only_request(photon_cutoff=2)
    decision, grams = enclose_port_grams(validate_request(request))
    assert decision.has_exact_model and not decision.on_exact_route
    assert decision.cause is ExactRouteCause.PARAMETER_NOT_REPRESENTED
    assert "radians" in decision.detail
    assert grams is not None and not grams.exact
    assert 0 < grams.largest_leaf <= Fraction(1, 2**120)


def test_declared_grams_and_a_declared_matrix_are_decided_by_item_i() -> None:
    """Item (i): the declared operator itself, decided exactly."""
    for build in MATRIX_REQUESTS:
        request = build()
        decision, grams = enclose_port_grams(validate_request(request))
        assert decision.decided_by == "(i)" and decision.on_exact_route
        assert grams is not None and grams.exact
        supplied = _artifact(request)
        family = GramFamily(
            tuple(label for label, _ in supplied.port_grams),
            tuple(matrix for _, matrix in supplied.port_grams),
        )
        route_i = replace(request, instrument_matrix=None, port_grams=family)
        decision_i, grams_i = enclose_port_grams(validate_request(route_i))
        assert decision_i.input_route == "port_grams" and decision_i.on_exact_route
        assert grams_i is not None and grams_i.exact


def test_a_family_admissible_only_at_the_tolerance_has_no_exact_model() -> None:
    """Items (i), (iv) with req:dark-composed-reference (iv): no reference, a cause.

    The route-(ii) receivers' Grams sum to ``1/2``; doubled and stretched by
    ``2^-20`` they sum to ``(1 + 2^-20) 1``, which ``eps_2`` admits and the
    exact decision of ``1 - A_[K] >= 0`` does not.
    """
    for build in MATRIX_REQUESTS:
        request = build()
        supplied = _artifact(request)
        stretched = GramFamily(
            tuple(label for label, _ in supplied.port_grams),
            tuple(
                np.asarray(matrix * (2 + 2.0**-19), dtype=np.complex128)
                for _, matrix in supplied.port_grams
            ),
        )
        route_i = replace(request, instrument_matrix=None, port_grams=stretched)
        artifact = _artifact(route_i)  # admitted at eps_2: not a refusal
        for family in artifact.photon_blocks:
            offered = family.reference
            assert offered.reference is None
            assert offered.cause is ReferenceCause.NO_EXACT_MODEL
            assert offered.exact_route.cause is ExactRouteCause.FAMILY_NOT_ADMISSIBLE
            assert all(block.kind is ReferenceKind.NONE for block in offered.offered)


def test_irrational_grams_are_enclosed_from_their_exact_expressions() -> None:
    """Items (ii)-(iii): represented, computed exactly, not in Q(i), then enclosed."""
    for probe in PROBE_FLAGS:
        request = _probe_graph_request(Fraction(1, 3), probe)
        decision, grams = enclose_port_grams(validate_request(request))
        assert decision.has_exact_model and not decision.on_exact_route
        assert decision.cause is ExactRouteCause.GRAMS_NOT_GAUSSIAN_RATIONAL
        assert grams is not None and not grams.exact
        # At x = 1/2 the cross term sqrt(x (1 - x)) = 1/2 is rational.
        half, half_grams = enclose_port_grams(
            validate_request(_probe_graph_request(Fraction(1, 2), probe))
        )
        assert half.on_exact_route and half_grams is not None and half_grams.exact


# ---------------------------------------------------------------------------
#  thm:exact-blocks, thm:enclosed-blocks, req:dark-composed-reference
# ---------------------------------------------------------------------------


def test_radius_zero_everywhere_at_the_dyadic_defaults() -> None:
    """thm:exact-blocks (iii): exact up to one photon, and the blocks are dyadic.

    The ideal receiver at N = 1 with the plate at pi/8: every radius is zero,
    every centre is a dyadic rational with a denominator of at most 4 -- a
    lattice value, which a snap keeps at weight zero -- and the binary64 block
    is its evaluation (``cos(pi/4)`` in binary64 is not ``sqrt(2)/2``, so the
    agreement is to rounding, not exact).
    """
    artifact = _artifact(_bb84_pi(1))
    for family in artifact.photon_blocks:
        reference = family.reference.reference
        assert reference is not None and reference.kind is ReferenceKind.EXACT
        for (_, letters), block in zip(
            family.dark_composed, reference.blocks, strict=True
        ):
            for (_, matrix), element in zip(letters, block.elements, strict=True):
                assert element.is_exact
                for i, row in enumerate(element.centre):
                    for j, entry in enumerate(row):
                        assert entry.re.denominator in (1, 2, 4)
                        assert entry.im == 0
                        value = complex(matrix[i][j])
                        assert abs(value - float(entry.re)) <= MACHINE_AGREEMENT


def test_radius_zero_up_to_one_photon_at_rational_parameters() -> None:
    """thm:exact-blocks (iii) with cor:exact-dark-composed (i) at x = 1/3, eta, p_dc."""
    request = _bb84_pi(2, **NOISY)
    graph = request.element_graph
    assert graph is not None
    elements = tuple(
        replace(element, component=Beamsplitter(Fraction(1, 3), 0, 0, 0))
        if element.name == "bs"
        else element
        for element in graph.elements
    )
    request = replace(request, element_graph=ElementGraph(elements, graph.edges))
    artifact = _artifact(request)
    kinds = [block.kind for block in artifact.photon_blocks[0].reference.offered]
    assert kinds == [ReferenceKind.EXACT, ReferenceKind.EXACT, ReferenceKind.ENCLOSED]
    assert artifact.photon_blocks[0].reference.exact_route.on_exact_route


def test_a_coarse_enclosure_contains_the_binary64_evaluation() -> None:
    """thm:exact-and-evaluated (vi): the evaluation approximates what is enclosed.

    At a leaf precision of 2^-24 every radius dominates the binary64 rounding,
    and with dyadic loss and dark counts the exact entries of this device are
    binary64 numbers that its evaluation hits; so every entry of every
    dark-composed binary64 block lies in its enclosure, entry by entry.
    """
    request = bb84_channel_only_request(photon_cutoff=2, **DYADIC_NOISY)  # type: ignore[arg-type]
    validated = validate_request(request)
    references = dark_composed_reference(validated, _dark_channel(validated), bits=24)
    artifact = _artifact(request)
    for family, offered in zip(artifact.photon_blocks, references, strict=True):
        assert offered.reference is not None
        for (_, letters), block in zip(
            family.dark_composed, offered.reference.blocks, strict=True
        ):
            for (_, matrix), element in zip(letters, block.elements, strict=True):
                for i, row in enumerate(element.centre):
                    for j, centre in enumerate(row):
                        value = complex(matrix[i][j])
                        dx = Fraction(value.real) - centre.re
                        dy = Fraction(value.imag) - centre.im
                        radius = element.radii[i][j]
                        assert dx * dx + dy * dy <= radius * radius


@pytest.mark.parametrize(
    "request_",
    [
        bb84_channel_only_request(photon_cutoff=2, **NOISY),  # type: ignore[arg-type]
        _bb84_pi(2, **NOISY),
        probe_free_matrix_request(photon_cutoff=1),
        pytest.param(probe_receiver_request(photon_cutoff=1), marks=requires_probe),
    ],
    ids=["radians", "pi", "matrix", "probe"],
)
def test_the_enclosure_agrees_with_the_binary64_evaluation(
    request_: ReceiverRequest,
) -> None:
    """At the default precision: within the radius plus binary64 rounding."""
    artifact = _artifact(request_)
    for family in artifact.photon_blocks:
        reference = family.reference.reference
        assert reference is not None
        for (_, letters), block in zip(
            family.dark_composed, reference.blocks, strict=True
        ):
            for (_, matrix), element in zip(letters, block.elements, strict=True):
                centre = np.asarray(
                    [
                        [complex(float(c.re), float(c.im)) for c in row]
                        for row in element.centre
                    ]
                )
                radius = np.asarray([[float(r) for r in row] for row in element.radii])
                assert np.all(np.abs(matrix - centre) <= radius + MACHINE_AGREEMENT)


def test_the_float_instance_of_the_generic_pipeline_agrees_with_numpy() -> None:
    """One generic pipeline: its binary64 instance reproduces the emitted blocks."""
    artifact = _artifact(bb84_channel_only_request(photon_cutoff=2))
    field = FloatField()
    grams = [
        [[complex(x) for x in row] for row in matrix]
        for _, matrix in artifact.port_grams
    ]
    pairs = unconditioned_pairs(field, grams)
    family = artifact.photon_blocks[0]
    coarse = artifact.outcome_alphabet.fibres
    labels = tuple(label for label, _ in artifact.port_grams)
    for photons, letters in family.blocks:
        raw = element_blocks(field, pairs, len(labels), photons)
        for (letter, block), (fibre_letter, fibre) in zip(letters, coarse, strict=True):
            assert letter == fibre_letter
            total = sum(
                (
                    np.asarray(raw[frozenset(labels.index(p) for p in pattern)])
                    for pattern in fibre
                ),
                np.zeros_like(block),
            )
            assert np.max(np.abs(total - block)) <= MACHINE_AGREEMENT


def test_without_dark_counts_the_dark_composed_blocks_are_the_bare_ones() -> None:
    """req:dark-composed-reference (i) with R the identity."""
    for family in _artifact(bb84_channel_only_request(photon_cutoff=2)).photon_blocks:
        for (n, bare), (m, composed) in zip(
            family.blocks, family.dark_composed, strict=True
        ):
            assert n == m
            for (a, x), (b, y) in zip(bare, composed, strict=True):
                assert a == b and np.array_equal(x, y)


def test_dark_counts_are_composed_into_the_offered_blocks() -> None:
    """req:dark-composed-reference (i), (v): with p_dc > 0 the families differ."""
    family = _artifact(
        bb84_channel_only_request(photon_cutoff=1, **NOISY)
    ).photon_blocks[0]
    bare = dict(dict(family.blocks)[0])
    composed = dict(dict(family.dark_composed)[0])
    # On the vacuum only a dark count clicks: R_{S|empty} > 0 for every S.
    assert bare["sc_0"][0, 0] == 0
    assert composed["sc_0"][0, 0] > 0


# ---------------------------------------------------------------------------
#  The zeros kept exact: req:dark-composed-reference (ii)(a)
# ---------------------------------------------------------------------------


def test_without_dark_counts_a_click_on_the_vacuum_is_an_exact_zero_off_the_route() -> (
    None
):
    """(ii)(a) by prop:noise-floor (v): |S cap Z| > n gives an exact zero block."""
    artifact = _artifact(bb84_channel_only_request(photon_cutoff=2))
    reference = artifact.photon_blocks[0].reference.reference
    assert reference is not None
    vacuum = dict(zip(reference.alphabet, reference.block("m=0").elements, strict=True))
    for letter in ("sc_0", "sc_1", "sc_2", "sc_3", "mc"):
        assert vacuum[letter].is_exact and vacuum[letter].is_structurally_zero
    one = dict(zip(reference.alphabet, reference.block("m=1").elements, strict=True))
    assert one["mc"].is_structurally_zero  # two clicks need two photons


def test_without_loss_the_no_click_element_is_an_exact_zero_on_every_photon_block() -> (
    None
):
    """(ii)(a) by prop:noise-floor (iv): B computed exactly and equal to the identity.

    At n = 2 the entries between (2,0) and (1,1) carry a 1/sqrt2 and are not
    exact by thm:exact-blocks; the rule keeps them exact zeros all the same.
    """
    reference = _artifact(_bb84_pi(2)).photon_blocks[0].reference.reference
    assert reference is not None
    for label in ("m=1", "m=2"):
        nc = dict(zip(reference.alphabet, reference.block(label).elements, strict=True))
        assert nc["nc"].is_structurally_zero


# ---------------------------------------------------------------------------
#  prop:noise-floor
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "request_",
    [
        bb84_channel_only_request(photon_cutoff=2, **NOISY),  # type: ignore[arg-type]
        _bb84_pi(2, **NOISY),
        _bb84_pi(3, **DYADIC_NOISY),
    ],
    ids=["radians", "pi", "pi-N3"],
)
def test_loss_and_dark_counts_make_every_element_decided_positive_definite(
    request_: ReceiverRequest,
) -> None:
    """prop:noise-floor (i), (iii): every element PD, decided on the enclosure.

    Declared at the factored loss one: the loss that makes the floor is the
    detectors' own, which the full normalization would move out of the
    station (detector-imperfections/rem:normalization-scope).
    """
    request_ = replace(request_, efficiency_normalization=Fraction(1))
    for family in _artifact(request_).photon_blocks:
        reference = family.reference.reference
        assert reference is not None
        for block in reference.blocks:
            for element in block.elements:
                assert enclosure_pd(element.centre, element.radii)


@requires_probe
def test_the_probe_conditioned_family_with_a_noise_floor_is_decided_definite() -> None:
    """prop:noise-floor (i) at every setting of a probe-conditioned receiver."""
    request = probe_receiver_request(photon_cutoff=1)
    request = replace(
        request,
        detector_layer=tuple(
            replace(port, efficiency=Fraction(9, 10)) for port in request.detector_layer
        ),
    )
    conditioned = (DARK_COMPOSITION_CLAIM, *setting_construction(2).enclosure_claims)
    for family in _artifact(request).photon_blocks:
        reference = family.reference.reference
        assert reference is not None
        assert reference.identity.establishing_claims == conditioned
        for block in reference.blocks:
            for element in block.elements:
                assert enclosure_pd(element.centre, element.radii)


def test_without_loss_the_no_click_element_is_not_definite() -> None:
    """prop:noise-floor (iv): lmax(A_Sigma) = 1 makes the no-click block singular."""
    request = _bb84_pi(1, dark_counts=(Fraction(1, 1000),) * 4)
    reference = _artifact(request).photon_blocks[0].reference.reference
    assert reference is not None
    nc = dict(zip(reference.alphabet, reference.block("m=1").elements, strict=True))
    assert not enclosure_pd(nc["nc"].centre, nc["nc"].radii)


# ---------------------------------------------------------------------------
#  The reference as a snap reads it
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "request_",
    [
        bb84_channel_only_request(photon_cutoff=2),
        _bb84_pi(2, **NOISY),
        probe_free_matrix_request(photon_cutoff=1),
        pytest.param(probe_receiver_request(photon_cutoff=1), marks=requires_probe),
    ],
    ids=["radians", "pi", "matrix", "probe"],
)
def test_every_offered_reference_passes_the_reference_row(
    request_: ReceiverRequest,
) -> None:
    """foundations/req:snap-reference (i): decided and established, by its claims.

    Where a block carries a factor enclosure, the claims that establish its
    membership are named besides (req:dark-composed-reference (vii)).
    """
    for family in _artifact(request_).photon_blocks:
        reference = family.reference.reference
        assert reference is not None
        assert reference.decide().usable
        assert reference.labels == tuple(f"m={n}" for n, _ in family.blocks)
        carried = any(
            element.factor is not None
            for block in reference.blocks
            for element in block.elements
        )
        source = request_.input_modes.source_dimension
        construction = (
            DARK_COMPOSITION_CLAIM,
            *setting_construction(source).enclosure_claims,
        )
        assert reference.identity.establishing_claims == (
            construction + FACTOR_CLAIMS if carried else construction
        )
        offered = {block.label: block.kind for block in family.reference.offered}
        assert offered == reference.block_kinds


def test_an_ideal_device_in_a_rotated_basis_keeps_its_exact_blocks() -> None:
    """rem:noise-floor-receiver; foundations/req:snap-reference (ii).

    The ideal passive BB84 receiver at N = 2 and a balanced basis choice: the
    blocks of at most one photon are exact dyadic lattice values, kept; the
    two-photon block is irrational, its reference enclosed, so it is moved,
    snapped from the data, and its enclosure is handed beside the snap. It
    rests on nothing the snap decides: the run decides whether it is
    evaluated off its snap.
    """
    record = _snap(_artifact(_bb84_pi(2)).photon_blocks[0]).record
    blocks = {block.block: block for block in record.blocks}
    assert blocks["m=0"].status is BlockStatus.KEPT
    assert blocks["m=1"].status is BlockStatus.KEPT
    two = blocks["m=2"]
    assert two.status is BlockStatus.MOVED
    assert two.reference_kind is ReferenceKind.NONE
    assert two.handed is not None and two.handed.kind is ReferenceKind.ENCLOSED
    assert two.cause is None
    assert record.resting_blocks == ()
    assert record.handed_blocks == ("m=0", "m=1", "m=2")


def test_a_noisy_device_hands_every_block() -> None:
    """The noise floor in the reference: every block moved, every block handed."""
    for request in (
        bb84_channel_only_request(photon_cutoff=2, **NOISY),  # type: ignore[arg-type]
        _bb84_pi(2, **NOISY),
    ):
        record = _snap(_artifact(request).photon_blocks[0]).record
        for block in record.blocks:
            assert block.status is BlockStatus.MOVED, block.block
            assert block.handed is not None, block.block
            assert not block.rests_on_assumption, block.block


def test_enclosed_references_switched_off_hand_the_exact_blocks_alone() -> None:
    """req:snap-fix (ii): the fix names the kinds offered.

    At pi/8 the blocks of at most one photon are exact and are handed; the
    two-photon block is enclosed, not handed, and rests in the group no
    usable reference with the cause enclosure_not_used.
    """
    family = _artifact(_bb84_pi(2, **NOISY)).photon_blocks[0]
    record = _snap(family, reference_enclosure=False).record
    causes = {block.block: block.cause for block in record.blocks}
    assert causes == {"m=0": None, "m=1": None, "m=2": RestingCause.ENCLOSURE_NOT_USED}
    assert record.handed_blocks == ("m=0", "m=1")
    fixes = receiver_fixes(family.fix_context, record)
    assert set(fixes) == {"m=2"}
    assert (
        "m=0: exact" in fixes["m=2"] and "m=2: enclosed (largest radius" in fixes["m=2"]
    )
    assert "reference_enclosure on" in fixes["m=2"]


# ---------------------------------------------------------------------------
#  req:snap-fix
# ---------------------------------------------------------------------------


def test_the_last_resort_fix_names_the_ports() -> None:
    """The support_not_preserved paragraph: efficiency 1, dark-count probability 0.

    The ideal device declares efficiency 1 and dark-count probability 0 in
    every port, so lmax(A_Sigma) < 1 is not established and every R entry of
    a click on the vacuum is 0; a block the last resort snapped names both,
    and the noise the device has.
    """
    family = _artifact(bb84_channel_only_request(photon_cutoff=2)).photon_blocks[0]
    block = BlockSnapRecord(
        block="m=1",
        status=BlockStatus.MOVED,
        reference_kind=ReferenceKind.NONE,
        support_not_preserved=True,
    )
    fix = receiver_fix(family.fix_context, block)
    assert fix is not None and "support_not_preserved" in fix
    assert "['H', 'V', '+', '-'] declare efficiency 1" in fix
    assert "dark-count probability of 0 or 1" in fix
    assert "loss and dark counts the device has" in fix


def test_the_fix_without_a_reference_names_its_cause() -> None:
    """Item (i)(a): the declared family is not admissible exactly."""
    for build in MATRIX_REQUESTS:
        request = build()
        supplied = _artifact(request)
        stretched = GramFamily(
            tuple(label for label, _ in supplied.port_grams),
            tuple(
                np.asarray(matrix * (2 + 2.0**-19), dtype=np.complex128)
                for _, matrix in supplied.port_grams
            ),
        )
        family = _artifact(
            replace(request, instrument_matrix=None, port_grams=stretched)
        ).photon_blocks[0]
        block = BlockSnapRecord(
            block="m=0",
            status=BlockStatus.MOVED,
            reference_kind=ReferenceKind.NONE,
            cause=RestingCause.NO_REFERENCE,
        )
        fix = receiver_fix(family.fix_context, block)
        assert fix is not None
        assert "no model admissible exactly" in fix
        assert "declared_family_not_admissible_exactly" in fix


# ---------------------------------------------------------------------------
#  The wire form and the docking switch
# ---------------------------------------------------------------------------


def test_the_payload_records_the_route_once_and_the_offered_kinds_per_setting() -> None:
    """req:exact-route-decision (iv); req:dark-composed-reference (iii), (iv)."""
    for build in MATRIX_REQUESTS:
        payload = _artifact(build()).as_payload()["photon_blocks"]
        assert isinstance(payload, dict)
        assert payload["exact_route"]["on_exact_route"] is True
        for setting in payload["settings"]:
            assert {"blocks", "dark_composed", "reference", "setting"} <= set(setting)
            offered = setting["reference"]["offered"]
            assert all(
                block["kind"] in ("exact", "enclosed", "none") for block in offered
            )
            identity = setting["reference"]["identity"]
            assert identity["model"].endswith("def:dark-composed")
            assert len(setting["reference"]["enclosures_sha256"]) == 64
            assert "enclosures" not in setting["reference"]


def test_the_enclosures_are_written_out_on_request_and_match_their_digest() -> None:
    """The payload pins the reference by digest; the object writes it out exactly."""
    offered = _artifact(_bb84_pi(2, **NOISY)).photon_blocks[0].reference
    full = offered.as_record(enclosures=True)
    enclosures = full["enclosures"]
    assert isinstance(enclosures, list) and len(enclosures) == 3
    assert full["enclosures_sha256"] == offered.enclosures_digest()
    first = enclosures[0]["elements"][0]
    # The factor enclosure carried beside the block is written with it.
    assert set(first) == {"letter", "centre", "radii", "factor"}
    assert all(isinstance(entry, str) for row in first["centre"] for entry in row)


def test_docking_hands_over_the_dark_composed_blocks_only_when_asked() -> None:
    """req:dark-composed-reference (v): the consumer in force reads the bare ones."""
    from certiqs_key.receiver.docking import receiver_artifact_rows
    from certiqs_key.reductions.inputs import ReceiverArtifactRows

    artifact = _artifact(bb84_channel_only_request(photon_cutoff=1, **NOISY))
    bare = receiver_artifact_rows(artifact)
    composed = receiver_artifact_rows(artifact, dark_composed=True)
    assert isinstance(bare, ReceiverArtifactRows)
    assert isinstance(composed, ReceiverArtifactRows)
    assert bare.photon_blocks[("sc_0", "off")][0][0][0].is_zero
    assert not composed.photon_blocks[("sc_0", "off")][0][0][0].is_zero
    # Item (v): the consumer is told the form, so it does not compose R again.
    assert bare.photon_blocks_form == "bare"
    assert composed.photon_blocks_form == "dark_composed"


def test_the_reference_construction_records_its_time() -> None:
    """A diagnostic only: present on the object, absent from the payload."""
    artifact = _artifact(_bb84_pi(1))
    assert artifact.photon_blocks[0].reference.seconds >= 0
    payload = artifact.as_payload()["photon_blocks"]
    assert isinstance(payload, dict)
    assert "seconds" not in payload["settings"][0]["reference"]
    assert math.isfinite(artifact.photon_blocks[0].reference.seconds)


def test_a_non_finite_declared_entry_has_no_exact_model() -> None:
    """foundations/def:binary64 (iii): a non-finite number denotes no declared value."""
    for build in MATRIX_REQUESTS:
        bad = replace(
            build(),
            instrument_matrix=np.asarray(
                [[0.5, float("nan")], [0.5, -0.5]], dtype=np.complex128
            ),
        )
        validated = validate_request(bad)
        assert isinstance(validated, ValidatedRequest)
        decision, grams = enclose_port_grams(validated)
        assert grams is None and not decision.has_exact_model
        assert decision.cause is ExactRouteCause.FAMILY_NOT_ADMISSIBLE


# ---------------------------------------------------------------------------
#  The shipped default receiver (instances/common/optics.py)
# ---------------------------------------------------------------------------


def test_the_shipped_default_receiver_is_kept() -> None:
    """thm:exact-blocks (iii); req:exact-route-decision (ii); req:snap-reference (ii).

    The instance declares its plate angle in units of pi and hands it over in
    that presentation, so the default device (ideal, N = 1) is on the exact
    route, every block is offered exact, and the snap keeps every block.
    """
    from instances.common import optics

    artifact = _artifact(optics.receiver_request(optics.ReceiverParameters()))
    for family in artifact.photon_blocks:
        assert family.reference.exact_route.on_exact_route
        assert {block.kind for block in family.reference.offered} == {
            ReferenceKind.EXACT
        }
        record = _snap(family).record
        assert all(block.status is BlockStatus.KEPT for block in record.blocks)


def test_the_shipped_default_plate_evaluates_to_the_radian_value() -> None:
    """presentation_rule (b): the evaluation is fl(fl(c) * fl(pi)), unchanged."""
    from instances.common import optics

    graph = optics.element_graph(optics.ReceiverParameters())
    plate = {element.name: element.component for element in graph.elements}["hwp"]
    assert isinstance(plate, Retarder)
    radians = Retarder.half_wave(float(Fraction(1, 8)) * math.pi, loss=0)
    assert np.array_equal(plate.matrix(), radians.matrix())


# ---------------------------------------------------------------------------
#  The identity names the exact declared operators (foundations/req:who-snaps)
# ---------------------------------------------------------------------------


def _exact_digest(matrix: object) -> str:
    """Recompute the digest the identity documents, from the declaration."""
    rows = [
        [[str(Fraction(z.real)), str(Fraction(z.imag))] for z in map(complex, row)]
        for row in np.asarray(matrix, dtype=np.complex128)
    ]
    text = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_the_identity_names_the_declared_instrument_matrix_exactly() -> None:
    """Route (ii): the declared matrix, not its binary64 port Grams."""
    for build in MATRIX_REQUESTS:
        request = build()
        reference = _artifact(request).photon_blocks[0].reference.reference
        assert reference is not None
        parameters = reference.identity.parameters
        assert parameters["instrument_matrix.sha256"] == _exact_digest(
            request.instrument_matrix
        )
        perturbed = np.asarray(request.instrument_matrix, dtype=np.complex128).copy()
        perturbed[0, 0] += 2.0**-50
        assert parameters["instrument_matrix.sha256"] != _exact_digest(perturbed)


def test_the_identity_names_the_declared_port_grams_exactly() -> None:
    """Route (i): each declared Gram by the digest of its exact entries."""
    for build in MATRIX_REQUESTS:
        request = build()
        supplied = _artifact(request)
        family = GramFamily(
            tuple(label for label, _ in supplied.port_grams),
            tuple(matrix for _, matrix in supplied.port_grams),
        )
        route_i = replace(request, instrument_matrix=None, port_grams=family)
        reference = _artifact(route_i).photon_blocks[0].reference.reference
        assert reference is not None
        parameters = reference.identity.parameters
        for label, matrix in zip(family.labels, family.matrices, strict=True):
            assert parameters[f"port_grams.{label}.sha256"] == _exact_digest(matrix)
        assert "instrument_matrix.sha256" not in parameters


def _with_generic_block(block: np.ndarray, probe: bool = True) -> ReceiverRequest:
    """Return the route-(iii) splitter receiver with a C10 block after its splitter."""
    request = _probe_graph_request(Fraction(1, 2), probe)
    graph = request.element_graph
    assert graph is not None
    elements = (*graph.elements, Element("blk", GenericBlock(block), (1, 3)))
    return replace(request, element_graph=ElementGraph(elements, (("bs", "blk"),)))


def test_the_identity_names_a_generic_block_exactly() -> None:
    """Route (iii): a C10 block is named by the digest of its exact entries."""
    block = np.asarray([[0.5, 0.5], [0.5, -0.5]], dtype=np.complex128)
    for probe in PROBE_FLAGS:
        reference = _artifact(_with_generic_block(block, probe)).photon_blocks[0]
        assert reference.reference.reference is not None
        parameters = reference.reference.reference.identity.parameters
        assert parameters["blk.block.sha256"] == _exact_digest(block)


# ---------------------------------------------------------------------------
#  Fail-closed paths of the reference and the fixes that name them
# ---------------------------------------------------------------------------


def _identity_columns(ports: int) -> dict[frozenset[int], dict[frozenset[int], float]]:
    patterns = [
        frozenset(port for port in range(ports) if pattern >> port & 1)
        for pattern in range(1 << ports)
    ]
    return {pattern: {pattern: 1.0} for pattern in patterns}


def _declared_channel_family(
    columns: dict[frozenset[int], dict[frozenset[int], float]],
) -> EmittedBlocks:
    declared = DarkCountChannel(4, DarkCountRoute.DECLARED_MATRIX, columns)
    request = replace(
        bb84_channel_only_request(photon_cutoff=1), dark_count_channel=declared
    )
    return _artifact(request).photon_blocks[0]  # admitted at the tolerances


def _no_reference_block() -> BlockSnapRecord:
    return BlockSnapRecord(
        block="m=0",
        status=BlockStatus.MOVED,
        reference_kind=ReferenceKind.NONE,
        cause=RestingCause.NO_REFERENCE,
    )


def test_a_declared_dark_channel_whose_column_misses_one_offers_no_reference() -> None:
    """req:dark-composed-reference (ii), (iv): (D1) decided exactly, 2^-40 short."""
    columns = _identity_columns(4)
    columns[frozenset()] = {frozenset(): 1.0 - 2.0**-40}
    family = _declared_channel_family(columns)
    assert family.reference.reference is None
    assert family.reference.cause is ReferenceCause.DARK_CHANNEL_NOT_EXACT
    assert "(D1)" in family.reference.detail
    assert all(block.kind is ReferenceKind.NONE for block in family.reference.offered)
    # req:snap-fix (i)(b).
    fix = receiver_fix(family.fix_context, _no_reference_block())
    assert fix is not None
    assert "does not satisfy (D1) and (D2) exactly" in fix
    assert "column-stochastic and monotone" in fix
    assert "generated dark-count route" in fix


def test_a_declared_dark_channel_off_its_monotone_pattern_offers_no_reference() -> None:
    """req:dark-composed-reference (ii), (iv): (D2) decided exactly at 2^-40."""
    columns = _identity_columns(4)
    columns[frozenset({0})] = {frozenset({0}): 1.0 - 2.0**-40, frozenset(): 2.0**-40}
    family = _declared_channel_family(columns)
    assert family.reference.reference is None
    assert family.reference.cause is ReferenceCause.DARK_CHANNEL_NOT_EXACT
    assert "(D2)" in family.reference.detail


def test_a_generic_block_contractive_only_at_the_tolerance_has_no_exact_model() -> None:
    """req:exact-route-decision (ii), (iv): C10 decided a contraction exactly."""
    stretched = np.asarray([[1.0 + 2.0**-40, 0.0], [0.0, 1.0]], dtype=np.complex128)
    for probe in PROBE_FLAGS:
        family = _artifact(_with_generic_block(stretched, probe)).photon_blocks[0]
        route = family.reference.exact_route
        assert not route.has_exact_model and not route.on_exact_route
        assert route.cause is ExactRouteCause.GENERIC_BLOCK_NOT_CONTRACTION
        assert "'blk'" in route.detail
        assert family.reference.reference is None
        assert family.reference.cause is ReferenceCause.NO_EXACT_MODEL


def test_declared_grams_hermitian_only_at_the_tolerance_have_no_exact_model() -> None:
    """req:exact-route-decision (i), (iv): Hermiticity decided exactly."""
    for build in MATRIX_REQUESTS:
        request = build()
        supplied = _artifact(request)
        matrices = [np.asarray(matrix).copy() for _, matrix in supplied.port_grams]
        matrices[0][0, 1] += 2.0**-40
        declared = GramFamily(
            tuple(label for label, _ in supplied.port_grams), tuple(matrices)
        )
        route_i = replace(request, instrument_matrix=None, port_grams=declared)
        family = _artifact(route_i).photon_blocks[0]
        route = family.reference.exact_route
        assert route.cause is ExactRouteCause.GRAMS_NOT_HERMITIAN
        assert route.cause.leaves_no_exact_model
        assert family.reference.reference is None
        assert family.reference.cause is ReferenceCause.NO_EXACT_MODEL


@requires_probe
def test_a_reciprocal_without_an_enclosure_offers_no_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:dark-composed-reference (iv) at a probe-conditioned setting.

    A reciprocal of the conditioning that receives no enclosure leaves the
    setting without a reference and records why; it is not a refusal of the
    receiver. The failure is forced, because a declared probe makes
    ``det(1 + Gamma A_LedLed) >= 1`` and no declaration reaches it at the
    default precision; what is tested is the routing of the failure, beside
    the rule itself on a ball whose radius reaches its centre.
    """
    assert Ball(Fraction(1), Fraction(0), Fraction(1)).reciprocal() is None

    def no_enclosure(self: BallField, value: Ball) -> Ball:
        raise NoEnclosure("forced: no rational l exceeds the radius")

    monkeypatch.setattr(BallField, "reciprocal", no_enclosure)
    artifact = _artifact(probe_receiver_request())
    for family in artifact.photon_blocks:
        assert family.reference.reference is None
        assert family.reference.cause is ReferenceCause.RECIPROCAL_NOT_ENCLOSED
        assert "forced" in family.reference.detail
    # req:snap-fix (i)(c).
    fix = receiver_fix(artifact.photon_blocks[0].fix_context, _no_reference_block())
    assert fix is not None
    assert "req:dark-composed-reference (iv)" in fix
    assert "smaller radii" in fix
