"""A preparation has a public serializer, so no consumer reads private names.

A consumer serialising a preparation with private helpers of
``certiqs_key.runs.record`` -- ``_public_and_source_tables``,
``_receiver_payload``, ``_reduction_payload``, ``_jsonable`` and
``_jsonable_exact`` -- would be pinned to names an ordinary rename could break
without a word.

WHAT IS TESTED HERE AND WHY.

1. :func:`preparation_record` exists, is reachable from the package root, and
   is JSON: one call, and the engine owns the shape.
2. THE FIVE NAMES ARE PUBLIC. The test that matters most, because the
   failure mode is silence: if someone re-privatises one, a consumer breaks
   at import and this fails first.
3. It works on BOTH ROUTES and on a REFUSAL. A serializer that only handled
   the happy path would push the other two back onto the caller, who would
   assemble the shape from private helpers.
4. Its keys agree with ``record_run``'s where they share a name, so a consumer
   reading a preparation and then a run reads one vocabulary.
"""

import json
from fractions import Fraction as F
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs import RunConfig, preparation_record
from certiqs_key.runs.pipeline import Preparation, SliceRefusal, prepare

pytestmark = pytest.mark.contract

QBER = F(1, 50)


def config(**changes: object) -> RunConfig:
    base = {
        "rounds": 2_000,
        "completeness_budget": F(1, 1_000_000),
        "parameters": KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        "declared_tolerance": 0.0,
        "model": {"qber": QBER},
    }
    return RunConfig(**{**base, **changes})  # type: ignore[arg-type]


def direct_route() -> Any:
    """Return the declared-finite-POVM route: the qubit instance's surface."""
    from instances.bb84.surface import default_config, preparation

    return preparation(default_config())


def device_route() -> Any:
    """Return the device route: the optical instance's surface."""
    from instances.optical_bb84.surface import default_config, preparation

    return preparation(default_config())


# ===========================================================================
#  1. It exists, and it is JSON
# ===========================================================================


@pytest.mark.parametrize("route", [direct_route, device_route])
def test_a_preparation_serialises_through_one_public_call(route) -> None:  # noqa: ANN001
    """One function, no private names, and the result survives ``json``."""
    outcome = route()
    assert isinstance(outcome, Preparation), outcome
    payload = preparation_record(outcome)
    assert payload["refused"] is False
    assert json.loads(json.dumps(payload)) == payload


def test_it_is_not_a_run_record_and_does_not_pretend_to_be_one() -> None:
    """No ``kind``, no ``schema_version``: nothing produced a key length.

    A ``kind`` of ``run-record`` on a preparation would claim a record of
    something that did not happen -- there is no solve, no acceptance set and
    no bundle -- and spec/architecture.md 4.1 forbids giving a field a meaning
    incompatible with the one it carries.
    """
    payload = preparation_record(direct_route())
    assert "kind" not in payload
    assert "schema_version" not in payload
    assert "config" not in payload
    assert "assumption_manifest" not in payload


# ===========================================================================
#  2. The five private names are gone
# ===========================================================================


def test_the_five_private_helpers_the_gateway_pinned_are_public_now() -> None:
    """The pin risk itself, asserted rather than described.

    A consumer that imported these five names read the record module's
    internals. They are public, and a re-privatisation fails here before it
    reaches anyone downstream.
    """
    from certiqs_key.runs import record as module

    for name in (
        "jsonable",
        "jsonable_exact",
        "receiver_payload",
        "public_and_source_tables",
        "reduction_payload",
        "preparation_record",
    ):
        assert hasattr(module, name), name
        assert name in module.__all__, name

    for gone in (
        "_jsonable",
        "_jsonable_exact",
        "_receiver_payload",
        "_public_and_source_tables",
        "_reduction_payload",
    ):
        assert not hasattr(module, gone), gone


def test_the_public_names_are_reachable_from_the_package_root() -> None:
    """A consumer imports from ``certiqs_key.runs`` and not from a submodule."""
    import certiqs_key.runs as runs

    for name in (
        "jsonable",
        "jsonable_exact",
        "receiver_payload",
        "public_and_source_tables",
        "reduction_payload",
        "preparation_record",
        "RecordedOutcome",
    ):
        assert name in runs.__all__, name
        assert hasattr(runs, name), name


def test_the_shared_serializers_accept_a_preparation_as_well_as_a_run() -> None:
    """The duck-typing the gateway relied on is declared and exercised.

    ``receiver_payload``, ``public_and_source_tables`` and
    ``reduction_payload`` read only attributes both classes carry. Nothing
    stated that, nothing typed it and nothing tested it; ``RecordedOutcome``
    states it and this exercises it.
    """
    from certiqs_key.runs.record import (
        public_and_source_tables,
        receiver_payload,
        reduction_payload,
    )

    outcome = device_route()
    assert isinstance(outcome, Preparation)
    assert set(public_and_source_tables(outcome)) == {"public", "source"}
    assert receiver_payload(outcome)["refused"] is False
    assert reduction_payload(outcome)["refused"] is False


def test_the_shape_is_pinned_to_the_record_schema_version() -> None:
    """The key set, held against the version a caller would file it under.

    ``preparation_record`` carries no ``schema_version`` of its own -- there is
    no producing module and no record to version -- but a consumer is pinned
    to a mapping, and a mapping with no number anywhere is not an improvement. The
    docstring says the shape moves with ``RECORD_SCHEMA_VERSION``; this is what makes
    that true rather than aspirational, so a key added or removed here fails until the
    constant and its note move with it.
    """
    from certiqs_key.runs.record import RECORD_SCHEMA_VERSION

    # 0.8.0 adds the general format's solver choices
    # to the RUN record (config.solver, key_rate.joint_solver); this
    # preparation record's key set did not move.
    # 0.9.0 drops the probe component from a
    # probe-free receiver's labels and adds compiled.public.choice_weighting;
    # this record's top-level key set did not move.
    # 0.10.0 adds `factor` and `party` inside each
    # `stations` entry and `station` on each stage entry; the top-level key
    # set did not move.
    # 0.11.0 adds map_validation_report's
    # hsupp_reference_band to the RUN record and drops the retired
    # branch_support_dim threshold row; this record's key set did not move.
    # 0.12.0 is one Frank-Wolfe driver -- every RUN
    # record's key_rate is the general payload -- and a probe-free receiver
    # no longer emits A-PROBE-DIAG; this record's key set did not move.
    # 0.13.0 adds assumption_manifest.claim_closure
    # to the RUN record; a preparation carries no manifest, so this record's
    # key set did not move.
    # 0.14.0 withdraws on a coupling residual and
    # adds oracle_return_coupling_residual to the RUN record's per_iterate;
    # this record's key set did not move.
    # 0.15.0 adds joint_solver.q_rule to the RUN
    # record's key_rate; this record's key set did not move.
    # 0.16.0 changes the RUN record's manifest rows
    # (statistics' ledger, the compiler's A-RECV key, four never-verified
    # marks); a preparation carries no manifest, so this record's key set did
    # not move.
    # 0.17.0 marks the engine's
    # never-verified rows, spells statistics' A-TSM row with its owner's key
    # and adds one refusal reason; the preparation block is unchanged.
    # 0.18.0 marks
    # every RUN record's manifest row by its assumption's `verification` field
    # and drops the engine's A-MARG row at d_A = 1; a
    # preparation carries no manifest, so this record's key set did not move.
    # 0.19.0 adds the common search request/report to runs; preparation is unchanged.
    # 0.20.0 reshapes the
    # RUN record's manifest and adds its instance and provenance blocks; this
    # record's top-level key set did not move, and its receiver_construction
    # gains receiver_route as the run record's does.
    # 0.21.0 adds
    # protocol_document to the run record and to this one (null off the
    # document route).
    # 0.22.0 reshapes
    # the instance's snap record (rows_adaptation: measurement_snaps) and adds
    # the domination record to the reduction payload; this record's top-level
    # key set did not move.
    # 0.23.0 adds
    # the group of every snap block and reshapes the domination record
    # (no added flag sectors, per-pair readings); this record's top-level key
    # set did not move.
    # 0.24.0 adds
    # config.alpha_search where set and the searched alpha child of the run
    # record; this record's top-level key set did not move.
    # 0.25.0 adds
    # the plausibility refusal and reduction.entries_not_in_force (and each
    # station's); this record's top-level key set did not move.
    # 0.26.0 adds
    # certify_snaps to the parameters, the snap settings and the domination
    # record, the group and cause certification_not_requested and the
    # blocks' underlying_cause; this record's top-level key set did not move.
    # 0.27.0 adds the run
    # record's reference_bracket and snaps.reference_companion, each snap
    # block's evaluated_off_snap and handed_reference_kind, each snap's
    # handed_reference and the reduction's reference_companion; this record's
    # top-level key set did not move (its reduction carries the companion's
    # record, its rows_adaptation the handed reference).
    # 0.28.0
    # removes certify_snaps and certified_weight_ceiling, the domination
    # record, entries_not_in_force and every weight, and names a block kept or
    # moved; this record's top-level key set did not move.
    # 0.29.0
    # renames strict_certification to strict_snaps and A-SNAP's machine key
    # to snapped_measurement, forms the companion on a producer-only run and
    # carries requested entries on it; this record's top-level key set did
    # not move.
    # 0.30.0 merges the two
    # laboratory premises into A-LAB, emitted once per party with a party on
    # every manifest emitter, and turns compiled.public.choice_weighting into
    # choice_weightings, one entry per weighted factor; this record's
    # top-level key set did not move.
    # 0.31.0
    # renames the route licensed+eq27 to licensed+two-sector; no key moves.
    # 0.32.0
    # adds the verified feasible side per bracket to the RUN record's
    # key_rate and drops A-LMO's row and the oracle-return residuals; a
    # preparation carries none of them, so this record's key set did not move.
    # 0.33.0 adds stages.key_rate.certified, the certified tier, the solver
    # option and the receiver's per-setting evaluation; a preparation carries
    # none of them, so this record's key set did not move.
    # 0.34.0 adds the alpha search's set-aside fields to a searched RUN
    # record's alpha child; a preparation carries none, so this record's key
    # set did not move.
    # 0.35.0
    # adds the certified record's declaration, premises, resting blocks and
    # companion points, the reference bracket's cause and two resting causes;
    # a preparation carries none of them, so this record's key set did not move.
    # 0.36.0 adds the acceptance box to a RUN record's acceptance
    # construction; a preparation has no acceptance construction, so this
    # record's key set did not move.
    # 0.37.0 adds statistics_consistency to a RUN record (completed or
    # refused); a preparation solves nothing, so this record's key set did not
    # move.
    # 0.38.0 makes the receiver artefact's efficiency_record an object (its
    # rows and the efficiency normalization) and adds efficiency_normalization
    # inside receiver_construction; this record's top-level key set did not
    # move.
    # 0.39.0 adds factored_loss to the channel interface beside the photon
    # blocks; this record's top-level key set did not move.
    # 0.40.0 records the efficiency normalization as applied exactly where
    # t < 1 and names a factor of one, declared or by default, factor_one;
    # no key moved.
    # 0.41.0 drops the A-EVE-DIM row (the reductions artefact's ledger here,
    # and a run's manifest); no key moved.
    # 0.42.0 adds the licence's per-entry discharge inside a reduction
    # artefact and renames an efficiency row's transmittance to value; this
    # record's top-level key set did not move.
    # 0.43.0 splits the configuration's solver block into the ordinary
    # choices and an advanced block; this record carries no configuration.
    # 0.44.0 adds receiver_row_omitted_on_provenance inside a reduction
    # artefact and its payload, and the compiler's ledger no longer carries
    # A-RECV; this record's top-level key set did not move.
    # 0.45.0 adds the pass cap's exponent inside statistics_consistency,
    # which a preparation does not carry. 0.46.0 reshapes that block (the
    # refusal on the cap); a preparation carries none.
    assert RECORD_SCHEMA_VERSION == "0.46.0"
    assert set(preparation_record(direct_route())) == {
        "refused",
        "acceptance_alphabet",
        "compiled",
        "sectors",
        "alice_povm",
        "receiver_construction",
        "receiver_artifact",
        "reduction",
        "rows_adaptation",
        "raw_joint_distribution",
        "channel_interface",
        "transmitter_artifact",
        "stages",
        "declaration_artefact",
        "protocol_document",
    }


# ===========================================================================
#  3. Both routes and a refusal
# ===========================================================================


def test_the_two_routes_carry_the_same_keys() -> None:
    """One shape on every instance.

    A consumer reads one record on both routes: what changes is the ``route``
    inside ``receiver_construction`` and what hangs off it, never which keys
    are present.
    """
    direct = preparation_record(direct_route())
    device = preparation_record(device_route())
    assert set(direct) == set(device)
    assert set(direct["receiver_construction"]) == set(
        device["receiver_construction"]
    )
    assert direct["receiver_construction"]["route"] == "declared_finite_povm"
    assert device["receiver_construction"]["route"] == "compiled_receiver"


def test_the_declared_route_carries_its_povm_exactly() -> None:
    """A preparation has no bundle, so this is where the operators reach a reader.

    The leaf type differs from a finished run's ``declared_povm``, which is
    float: a preparation's is the exact ``"p/q"`` pair, because there is no
    bundle on disk to recover the exact operators from. The NESTING is the
    same, which is what a consumer navigates by.
    """
    from certiqs_key.foundations.exact import deserialize_matrix, equal

    outcome = direct_route()
    assert isinstance(outcome, Preparation)
    payload = preparation_record(outcome)
    declared = payload["receiver_construction"]["declared_povm"]
    assert declared
    assert json.loads(json.dumps(declared)) == declared

    # THE ROUND TRIP IS THE TEST. Every entry read back equals the operator the
    # compiler emitted, so a consumer that re-decides is re-deciding on the
    # same numbers and not on a rendering of them.
    sectors = [str(label) for label in outcome.declaration.sectors.labels]
    for label, operator in outcome.declaration.bob_povm.items():
        blocks = declared[str(label)]
        assert list(blocks) == sectors
        for sector, block in zip(sectors, operator.blocks, strict=True):
            assert equal(deserialize_matrix(blocks[sector]), block)


def test_a_refused_preparation_is_transcribed_and_not_suppressed() -> None:
    """The refusing stage, that module's own reason, and the stages so far.

    On the same grounds as a refused run: a sweep over a grid where half the
    points refuse is a legitimate result and reads as one, so a serializer that
    only handled the happy path would push the other case back onto the caller
    -- which is how the private-helper assembly started.

    THE REFUSAL IS A REAL ONE AND NOT A STUB. The optical instance's receiver
    is compiled from float-evaluated optics, so its declared family has a
    completeness defect of about ``1.1e-16`` that the instance repairs by
    snapping, and a run declaring ``tau = 0`` has permitted no repair at all.
    The rows adapter refuses at the docking stage with the receiver's own code,
    which is the same forcing ``tests/unit/test_runs_flow.py`` uses.

    ``tau`` decides only a snap made
    without a usable reference, so the forcing is a two-photon device (an
    enclosed reference) in a run that declares enclosed references not used.
    """
    from instances.optical_bb84.surface import default_config, preparation

    base = default_config()
    outcome = preparation(
        base.with_(
            device={**base.device, "photon_cutoff": F(2), "exact_window": F(3)},
            declared_tolerance=0.0,
            reference_enclosure=False,
        )
    )
    assert isinstance(outcome, SliceRefusal), outcome
    payload = preparation_record(outcome)
    assert payload["refused"] is True
    assert payload["stage"] == str(outcome.stage)
    assert payload["reason"] == outcome.reason
    assert payload["detail"] == outcome.detail
    # The prologue got as far as the receiver, so the artefact is carried: a
    # caller that wants to see WHAT was refused has it.
    assert payload["receiver_artifact"] is not None
    assert [entry["stage"] for entry in payload["stages"]] == [
        str(record.stage) for record in outcome.stages
    ]
    assert json.loads(json.dumps(payload)) == payload


# ===========================================================================
#  4. One vocabulary with the run record
# ===========================================================================


@pytest.mark.requires_qics
def test_the_shared_keys_agree_with_a_run_record_of_the_same_configuration(
    tmp_path: Path,
) -> None:
    """``compiled`` means the same in a preparation and in a finished run.

    Asserting ``payload["compiled"] == public_and_source_tables(outcome)`` and
    ``payload["stages"] == [e.as_record() for e in outcome.stages]`` would
    compare :func:`preparation_record` with the calls it makes, so it would
    pass on any implementation, including one emitting a table no run agrees
    with.

    What is actually worth holding is that the two OUTCOMES agree: the tables
    are transcribed from the compiler's own machine record, and a preparation
    and a run of the same specification compile the same declaration, so a
    consumer that reads one and then the other reads one vocabulary. That
    costs a solve, which is why this is ``requires_qics``.
    """
    from instances.bb84.specification import bb84_specification
    from instances.common.honest.depolarized_bell_pair import honest_provider

    from certiqs_key.runs import record_run, run_slice
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    half = F(1, 2)
    specification = bb84_specification(half, half, half, half)
    settings = config()

    prepared = prepare(settings, specification=specification)
    assert isinstance(prepared, Preparation), prepared

    finished = run_slice(
        specification,
        honest_provider=honest_provider(QBER),
        rounds=settings.rounds,
        completeness_budget=settings.completeness_budget,
        parameters=settings.parameters,
        oracle=QicsSectorChoiOracle(),
        directory=tmp_path / "bundle",
        created_by="test",
        declared_tolerance=settings.declared_tolerance,
        alpha=1.5,
    )
    assert not isinstance(finished, SliceRefusal), finished

    payload = preparation_record(prepared)
    run = record_run(finished, settings, created_by="test")
    assert payload["compiled"] == run.payload["compiled"]
    assert set(payload["compiled"]) == {"public", "source"}
    # And the receiver surface carries the same KEYS on both, which is what
    # lets a consumer navigate a preparation with the run record's own type.
    assert set(payload["receiver_construction"]) == set(
        run.payload["stages"]["receiver_construction"]
    )
