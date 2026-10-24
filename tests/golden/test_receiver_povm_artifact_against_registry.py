"""The emitted artifact against the FROZEN registry -- the emission pass.

Golden replay of ``BOUND_EVALUATION_V1``,
``RECEIVER_CONSTRUCTION_PRESENCE``, ``OUTPUT_KEYS_0_3_0``, ``OUTPUT_PRESENCE``,
``INPUT_KEYS_0_3_0``, ``INPUT_ROUTES``, ``CONVENTION_KEYS``, ``SLOT_RECORD``,
``OUTCOME_ALPHABET`` and ``ENCLOSURE_DIRECTIONS`` (oracle entries
``O-RP-NUMERICS`` and ``O-RP-INTERFACE``).

``TIER_CASES`` AND ``FALLBACK-CERTIFIED-TO-ESTIMATE`` ARE NOT REPLAYED HERE
ANY MORE. Three of the four frozen tier rows request ``certified``, the tier
PRINCIPLES.md section 10 drops, and the frozen refusal row is that fallback;
with the enum member gone there is no request that can reach either. The rows
stay in the frozen registry, unedited, and
``test_receiver_povm_refusals_against_registry`` still accounts for the
refusal row as one no builder produces.

THE TWO RECEIVERS ARE THE REGISTRY'S OWN, DRIVEN END TO END. The BB84 request
is Example ``ex:bb84``'s channel-only receiver DECLARED AS AN ELEMENT GRAPH, so
the emission exercises the whole route-(iii) path -- compile, efficiency,
condition, block, bound, residual, emit -- and must land on ``I-BB84``'s frozen
Grams and Example ``ex:bb84bound``'s frozen ``p_mc``. The probe request is
``I-PROBE`` declared as an instrument matrix, and lands on ``BD-PROBE-OFF-N1``
and ``BD-PROBE-ON-N1-M3``.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest
from probe_presence import requires_probe, with_probe
from receiver_povm_support import (
    TOLERANCE,
    assert_matches,
    bb84_channel_only_request,
    mat_value,
    probe_free_matrix_request,
    probe_receiver_request,
)
from registry_receiver_povm import (
    BOUND_DATA_CASES,
    BOUND_EVALUATION_RIGOROUS,
    BOUND_EVALUATION_V1,
    CONVENTION_KEYS_0_2_0,
    ENCLOSURE_DIRECTIONS,
    INPUT_KEYS_0_3_0,
    INPUT_ROUTES,
    INSTRUMENT_CASES,
    OUTCOME_ALPHABET,
    OUTPUT_KEYS_0_3_0,
    OUTPUT_PRESENCE,
    RECEIVER_CONSTRUCTION_PRESENCE,
    SLOT_RECORD,
    is_superseded_0_3_0,
    rp_oracle,
)

from certiqs_key.receiver import (
    BOUND_EVALUATION,
    MATHEMATICAL_SPEC_VERSION,
    ROUTE_KEYS,
    ReceiverRequest,
    construct_receiver,
)
from certiqs_key.receiver import OUTPUT_KEYS as MODULE_OUTPUT_KEYS
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact

#: The route-(ii) receivers: the probe-free twin of ``I-PROBE`` in every tree,
#: ``I-PROBE`` itself where the removable probe-conditioning submodule is present.
MATRIX_REQUESTS = (probe_free_matrix_request, *with_probe(probe_receiver_request))


def _artifact(request: ReceiverRequest) -> ReceiverMeasurementArtifact:
    """Return the emitted artifact, asserting the emission did not refuse."""
    emission = construct_receiver(request)
    assert emission.refusal is None, emission.refusal
    assert emission.artifact is not None
    return emission.artifact


@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_vocabulary_is_the_frozen_one() -> None:
    """The inputs and outputs tables: FIFTEEN input keys, fifteen output keys.

    And three routes. ``INPUT_KEYS`` -- the registry's fourteen-name 0.2.0
    tuple -- is marked in ``SUPERSEDED_BY_0_3_0``, and the mark is on the tuple
    AS AN ENUMERATION OF THE INPUT SURFACE and not on any name in it, the
    registry's note reading "fourteen names in this tuple are all still input
    keys and all still mean what they meant". Its replacement is
    ``INPUT_KEYS_0_3_0``, the same fourteen plus ``exact_window``, the declared
    depth ``{m*_t}``, optional per setting; nothing is removed.
    """
    assert rp_oracle("O-RP-INTERFACE").claims != ()
    assert MODULE_OUTPUT_KEYS == OUTPUT_KEYS_0_3_0
    assert len(OUTPUT_KEYS_0_3_0) == 15
    assert ROUTE_KEYS == INPUT_ROUTES
    assert is_superseded_0_3_0("INPUT_KEYS")
    # The request type carries the fifteen input machine keys and the one
    # receiver 0.7.0 adds (detector-imperfections/req:efficiency-normalization),
    # and no more.
    from dataclasses import fields

    assert tuple(sorted(f.name for f in fields(ReceiverRequest))) == tuple(
        sorted((*INPUT_KEYS_0_3_0, "efficiency_normalization"))
    )
    assert len(INPUT_KEYS_0_3_0) == 15
    assert "exact_window" in INPUT_KEYS_0_3_0
    # And the artifact type carries the fifteen output keys, in the table order.
    assert (
        tuple(f.name for f in fields(ReceiverMeasurementArtifact)) == OUTPUT_KEYS_0_3_0
    )
    # CONVENTION_KEYS (16 bullets) is marked `incomplete` in
    # SUPERSEDED_BY_0_2_0 and is REPLACED HERE by CONVENTION_KEYS_0_2_0,
    # which adds `numerical_tolerance_assignment` between `numerics` and
    # `fail_closed` (the interface conventions, bullet 15).
    assert len(CONVENTION_KEYS_0_2_0) == 17
    assert "numerical_tolerance_assignment" in CONVENTION_KEYS_0_2_0


@pytest.mark.contract
@pytest.mark.oracle
def test_the_receiver_construction_presence_rule_on_all_three_routes() -> None:
    """`receiver_construction`: present exactly on route (iii), absent on (i)/(ii)."""
    frozen = {row[0]: row for row in RECEIVER_CONSTRUCTION_PRESENCE}
    assert set(frozen) == {"RC-ROUTE-I", "RC-ROUTE-II", "RC-ROUTE-III"}

    compiled = _artifact(bb84_channel_only_request())
    assert frozen["RC-ROUTE-III"][2] is True
    assert compiled.receiver_construction is not None
    assert "receiver_construction" in compiled.payload_keys()

    for build in MATRIX_REQUESTS:
        supplied = _artifact(build())
        assert frozen["RC-ROUTE-II"][2] is False
        assert supplied.receiver_construction is None
        assert "receiver_construction" not in supplied.payload_keys()
        assert set(supplied.payload_keys()) == set(OUTPUT_KEYS_0_3_0) - {
            "receiver_construction"
        }

        declared = _artifact(_route_one_request(build))
        assert frozen["RC-ROUTE-I"][2] is False
        assert declared.receiver_construction is None
        # The presence rule as the frozen table states it, key by key.
        for key, presence in OUTPUT_PRESENCE:
            if presence == "always":
                assert key in compiled.payload_keys() and key in supplied.payload_keys()
            else:
                assert presence == "route (iii) only"
                assert key in compiled.payload_keys()
                assert key not in supplied.payload_keys()


def _route_one_request(build: Callable[[], ReceiverRequest]) -> ReceiverRequest:
    """Return a route-(ii) receiver's Grams supplied DIRECTLY -- route (i)."""
    from dataclasses import replace

    from certiqs_key.receiver import GramFamily

    compiled = _artifact(build())
    family = GramFamily(
        tuple(label for label, _ in compiled.port_grams),
        tuple(matrix for _, matrix in compiled.port_grams),
    )
    return replace(build(), instrument_matrix=None, port_grams=family)


@pytest.mark.contract
@pytest.mark.oracle
def test_bound_evaluation_is_rigorous_where_every_weight_is() -> None:
    """`outputs.bound_evaluation`, req:evaluation-label, Def. def:evaluation-model.

    Derived by hand (``registry_receiver_povm`` notes the
    clause): these three requests are on the exact route, so every setting's
    weight is the enclosed one and the label is `rigorous`; the module's
    fallback label stays the version-1 value.
    """
    assert BOUND_EVALUATION == BOUND_EVALUATION_V1
    requests = [bb84_channel_only_request()]
    for build in MATRIX_REQUESTS:
        requests += [build(), _route_one_request(build)]
    for request in requests:
        artifact = _artifact(request)
        assert artifact.bound_evaluation == BOUND_EVALUATION_RIGOROUS
        assert artifact.mathematical_spec_version == MATHEMATICAL_SPEC_VERSION
        # The emitted pin is an accepted version of
        # spec/modules/receiver/module.yaml, the one the code implements. The literal is
        # kept beside the constant on purpose -- a test that only compared the
        # artifact with the module constant would pass on any string -- and is
        # written by hand when the pin moves, never regenerated.
        assert artifact.mathematical_spec_version == "receiver@0.9.0"
        assert "draft" not in artifact.mathematical_spec_version


@pytest.mark.contract
@pytest.mark.oracle
def test_the_compiled_bb84_receiver_reproduces_its_frozen_grams_and_bound() -> None:
    """Route (iii) end to end: Example ex:bb84 and Example ex:bb84bound."""
    frozen = next(c for c in INSTRUMENT_CASES if c.case_id == "I-BB84")
    artifact = _artifact(bb84_channel_only_request(photon_cutoff=2))
    emitted = dict(artifact.port_grams)
    for label, matrix in frozen.grams:
        assert_matches(
            emitted[label], mat_value(matrix), TOLERANCE.eps_2, f"I-BB84 {label}"
        )
    # Example ex:bb84bound: p_mc = 1/2 at N = 2 and 3/4 at N = 3, branch 1 by (X).
    for cutoff, case_id in (
        (2, "BD-BB84-N2"),
        (3, "BD-BB84-N3"),
        (1, "BD-BB84-N1-ZERO"),
    ):
        case = next(c for c in BOUND_DATA_CASES if c.case_id == case_id)
        artifact = _artifact(bb84_channel_only_request(photon_cutoff=cutoff))
        assert artifact.high_photon_bounds.entries[0].weight == pytest.approx(
            float(case.p_mc), abs=TOLERANCE.eps_2
        ), case_id
        record = artifact.bound_quantifier_domain.per_setting[0]
        assert str(record.branch) == case.branch
        # The key reports the BRANCH and (X) (`one_predicate_note`); registry
        # 0.1.3's field "which predicate selected branch 1" went with
        # predicate (C) at registry 0.2.0.
        assert record.predicate_x is (case.branch == "1")
        # T = {off} by Definition def:probe, so the printed value IS the emitted
        # p_mc and not one of several per-setting values.
        assert artifact.bound_quantifier_domain.probe_alphabet == ("off",)
        assert artifact.high_photon_bounds.per_setting == (
            ("off", pytest.approx(float(case.p_mc), abs=TOLERANCE.eps_2)),
        )


@pytest.mark.contract
@pytest.mark.oracle
@requires_probe
def test_the_probe_receiver_emits_both_branches_in_one_artifact() -> None:
    """Definition def:pmc across a declared alphabet, and the minimum over T."""
    artifact = _artifact(probe_receiver_request(photon_cutoff=1, window=3))
    off = next(c for c in BOUND_DATA_CASES if c.case_id == "BD-PROBE-OFF-N1")
    on = next(c for c in BOUND_DATA_CASES if c.case_id == "BD-PROBE-ON-N1-M3")
    weights = dict(artifact.high_photon_bounds.per_setting)
    assert weights["off"] == pytest.approx(float(off.p_mc), abs=TOLERANCE.eps_2)
    assert weights["on"] == pytest.approx(float(on.p_mc), abs=TOLERANCE.eps_2)
    # The emitted value is the MINIMUM over T (Definition def:pmc).
    assert artifact.high_photon_bounds.entries[0].weight == pytest.approx(
        min(weights.values()), abs=TOLERANCE.eps_2
    )
    records = {r.setting: r for r in artifact.bound_quantifier_domain.per_setting}
    assert str(records["off"].branch) == "1"
    assert records["off"].predicate_x is True
    assert str(records["on"].branch) == "2"
    assert records["on"].predicate_x is False
    assert records["on"].window == on.window
    # The achieved residual gap is reported at the setting that declares a window.
    gaps = {gap.setting: gap for gap in artifact.validation_results.residual_gaps}
    assert set(gaps) == {"on"}
    assert gaps["on"].gap == pytest.approx(
        float(on.residual_gap or 0), abs=TOLERANCE.eps_gap
    )
    assert gaps["on"].passes is True


@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_slot_and_alphabet_are_the_frozen_shape() -> None:
    """Definition def:slot's single-entry shape, and the outputs table's stable IDs."""
    record = dict(SLOT_RECORD)
    artifact = _artifact(bb84_channel_only_request())
    assert len(artifact.high_photon_bounds.entries) == int(record["entry_count"])
    entry = artifact.high_photon_bounds.entries[0]
    # MC_K = {S : |S| >= 2}: at K = 4 that is eleven raw patterns.
    assert len(entry.outcome_set) == 11
    assert all(len(pattern) >= 2 for pattern in entry.outcome_set)
    assert 0.0 <= entry.weight <= 1.0
    # The alphabet: six letters at K = 4, stable IDs, labels as metadata.
    assert len(artifact.outcome_alphabet.letters) == len(OUTCOME_ALPHABET)
    identifiers = [identifier for identifier, _ in artifact.outcome_alphabet.letters]
    assert identifiers == list(range(len(identifiers)))
    fibres = dict(artifact.outcome_alphabet.fibres)
    assert len(fibres["mc"]) == 11
    assert fibres["nc"] == ((),)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_blocks_and_dimensions_agree_with_the_frozen_ones() -> None:
    """`outputs.photon_blocks` and `block_dimensions`, per probe setting."""
    from registry_receiver_povm import POVM_BLOCK_CASES

    artifact = _artifact(bb84_channel_only_request(photon_cutoff=2))
    assert [row.photons for row in artifact.block_dimensions] == [0, 1, 2]
    assert [row.dimension for row in artifact.block_dimensions] == [1, 2, 3]
    assert artifact.block_dimensions[2].occupation_vectors == ((0, 2), (1, 1), (2, 0))
    assert len(artifact.photon_blocks) == 1
    blocks = dict(artifact.photon_blocks[0].blocks)
    frozen = next(c for c in POVM_BLOCK_CASES if c.case_id == "PB-BB84-n2")
    emitted = dict(blocks[2])
    assert_matches(
        emitted["mc"], mat_value(frozen.multiclick), TOLERANCE.eps_4, "emitted mc block"
    )
    # Complete on every emitted block: Theorem thm:click-povm (i) restricted to n.
    for photons, letters in artifact.photon_blocks[0].blocks:
        total = sum(block for _, block in letters)
        size = artifact.block_dimensions[photons].dimension
        assert_matches(
            total, np.eye(size), TOLERANCE.eps_4, f"completeness n={photons}"
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_enclosure_directions_are_frozen_and_implemented() -> None:
    """Remark rem:ia: the extension, and which way it must round.

    Derived by hand from receiver/req:rigorous-weight (iii) and
    def:enclosed-weight (i): the rigorous evaluation takes ``c`` from an UPPER
    bound on ``lmax(B)`` and each ``d_k`` from a LOWER bound on ``lmin(B_k)``,
    the directions frozen here, so the enclosed ``c`` lies at or below the
    floating-point one and each enclosed ``d_k`` at or above it (to rounding);
    the artifact is `rigorous`.
    """
    assert len(ENCLOSURE_DIRECTIONS) == 2
    quantities = {row[0] for row in ENCLOSURE_DIRECTIONS}
    assert quantities == {"lmax(B)", "lmin(B_k)"}
    directions = {row[0]: row[1] for row in ENCLOSURE_DIRECTIONS}
    assert directions["lmax(B)"] == "UPPER enclosure"
    assert directions["lmin(B_k)"] == "LOWER enclosure"
    artifact = _artifact(bb84_channel_only_request())
    assert artifact.bound_evaluation == "rigorous"
    from fractions import Fraction

    from certiqs_key.receiver.bound import bound_data_from_family
    from certiqs_key.receiver.construct import _canonical_object
    from certiqs_key.receiver.request import validate_request
    from certiqs_key.receiver.settings import setting_construction

    validated = validate_request(bb84_channel_only_request())
    family = _canonical_object(validated)[2]
    floating = bound_data_from_family(setting_construction(0).no_click_family(
        family, validated.request.probe_declaration.settings[0],
        validated.request.input_modes.channel_dimension))
    enclosed = artifact.bound_quantifier_domain.per_setting[0].enclosed
    assert enclosed is not None
    assert Fraction(enclosed["c"]) <= Fraction(floating.c) + Fraction(1, 2**50)
    for d_enclosed, d_float in zip(enclosed["ds"], floating.ds, strict=True):
        assert Fraction(d_enclosed) >= Fraction(d_float) - Fraction(1, 2**50)


@pytest.mark.contract
def test_a_single_c10_block_emits_and_agrees_with_route_ii() -> None:
    """Entry C10 (def:catalogue-entries): one block spanning the receiver must emit.

    Declaring it is route (ii) presented as route (iii), and it must emit the
    same Grams.
    """
    from dataclasses import replace

    from certiqs_key.receiver import Element, ElementGraph, GenericBlock

    for build in MATRIX_REQUESTS:
        supplied = build()
        assert supplied.instrument_matrix is not None
        graph = ElementGraph(
            (Element("blk", GenericBlock(supplied.instrument_matrix), (0, 1)),)
        )
        compiled = replace(supplied, instrument_matrix=None, element_graph=graph)
        reference = _artifact(supplied)
        emission = construct_receiver(compiled)  # must not raise
        assert emission.refusal is None, emission.refusal
        assert emission.artifact is not None
        assert emission.artifact.receiver_construction is not None
        for (label, expected), (other, actual) in zip(
            reference.port_grams, emission.artifact.port_grams, strict=True
        ):
            assert label == other
            assert_matches(
                actual, expected, TOLERANCE.eps_2, f"C10 route (iii) {label}"
            )
