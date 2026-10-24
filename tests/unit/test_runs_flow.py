"""The composition-flow view, and the provenance graph it is.

The list carries its edges rather than a second description beside it.

The four properties of the provenance graph are: every consumed artefact id matches an
earlier emitted one; the Mermaid text is generated from the list; a forced
refusal marks the downstream stages ``not_executed``; and a preparation's
planned list matches the executed list's stages and consumed keys.

WHERE EACH ROUTE IS ASSERTED:

* the DIRECT FINITE POVM route, in this file, on a full run;
* the DEVICE route, on the oracle-free part of the path, in the section at the
  bottom of this file: the device prologue's three stages are exactly what a
  preparation runs, so the edges across them, their rendering and a forced
  refusal INSIDE the prologue cost no solve and are asserted in the default
  tier;
* the DEVICE route ON A COMPLETED RUN -- the executed list against the planned
  one, the solve's children, and the record against the checked-in schema -- in
  ``tests/integration/test_optical_bb84_slice.py``, which is ``slow`` because
  it solves.
"""

from __future__ import annotations

import logging
from fractions import Fraction as F
from pathlib import Path

import pytest
from instances.bb84.specification import (
    ConjugationConvention,
    bb84_specification,
    conjugation_example_specification,
)
from instances.common.honest.depolarized_bell_pair import honest_provider

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs import RunConfig
from certiqs_key.runs.flow import (
    DEVICE_PROLOGUE_KINDS,
    PLANNED_ARTEFACT_KINDS,
    PLANNED_CONFIG_KEYS,
    STAGE_MODULE,
    ArtefactKind,
    FlowRecorder,
    StageEvent,
    StageStatus,
    artefact_kind_of,
    mermaid,
)
from certiqs_key.runs.pipeline import (
    Preparation,
    SliceRefusal,
    SliceStage,
    prepare,
    run_slice,
)
from certiqs_key.runs.record import record_run

pytestmark = pytest.mark.contract

QBER = F(1, 50)
ORACLE = pytest.importorskip("qics") and None  # the import is the skip


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


def oracle():
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return QicsSectorChoiOracle()


@pytest.mark.requires_qics
def completed(tmp_path: Path, observer=None):  # noqa: ANN001
    outcome = run_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        honest_provider=honest_provider(QBER),
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        oracle=oracle(),
        directory=tmp_path / "bundle",
        created_by="test",
        declared_tolerance=0.0,
        alpha=1.5,
        observer=observer,
        run_id=config().digest(),
    )
    assert not isinstance(outcome, SliceRefusal), outcome
    return outcome


# ===========================================================================
#  The view itself (change 7)
# ===========================================================================


def test_a_refusal_stops_the_run_and_the_stages_after_it_are_not_executed() -> None:
    """The distinction the item asks for: refused is not unexecuted."""
    outcome = run_slice(
        conjugation_example_specification(ConjugationConvention.OMITTED),
        honest_provider=honest_provider(QBER),
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        oracle=object(),  # type: ignore[arg-type] - never reached
        directory=Path("unused"),
        created_by="test",
        declared_tolerance=0.0,
    )
    assert isinstance(outcome, SliceRefusal)
    statuses = {record.stage: record.status for record in outcome.stages}
    assert statuses[SliceStage.COMPILATION] is StageStatus.REFUSED
    assert statuses[SliceStage.HONEST_MODEL] is StageStatus.NOT_EXECUTED
    assert statuses[SliceStage.SOLVE] is StageStatus.NOT_EXECUTED
    # And the refusing module's own code travels with it.
    refused = next(
        record for record in outcome.stages if record.status is StageStatus.REFUSED
    )
    assert refused.reason == outcome.reason
    assert refused.module == "protocol-compiler"


def test_a_route_without_a_device_prologue_omits_those_stages() -> None:
    """Absent, not present and empty: a null row would invite a question."""
    outcome = prepare(
        config(), specification=bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert isinstance(outcome, Preparation)
    stages = {record.stage for record in outcome.stages}
    assert SliceStage.RECEIVER_CONSTRUCTION not in stages
    assert SliceStage.REDUCTION not in stages


def test_the_mermaid_text_is_generated_from_the_list_and_nothing_else() -> None:
    """One source. A node per stage, in order, with its status in the label."""
    outcome = prepare(
        config(), specification=bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert isinstance(outcome, Preparation)
    text = mermaid(outcome.stages)
    assert text.startswith("flowchart TD\n")
    for index, record in enumerate(outcome.stages):
        assert f"s{index}[" in text
        assert str(record.stage) in text
        assert STAGE_MODULE[record.stage] in text
    # Every node is linked to the next one, and the count is the list's.
    assert text.count("-->") == len(outcome.stages) - 1


def test_every_stage_of_the_view_names_the_module_that_owns_it() -> None:
    """The run tier owns the order and no mathematics."""
    outcome = prepare(
        config(), specification=bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert isinstance(outcome, Preparation)
    for record in outcome.stages:
        assert record.module == STAGE_MODULE[record.stage]


# ===========================================================================
#  The provenance edges
# ===========================================================================


@pytest.mark.requires_qics
def test_every_consumed_artefact_was_emitted_by_an_earlier_stage(
    tmp_path: Path,
) -> None:
    """THE PROPERTY THAT MAKES IT A GRAPH, on the direct finite route.

    An edge is an id in one stage's ``emits`` and a later stage's ``consumes``.
    A consumed id with no earlier emission would be an edge to nothing, which
    is what a topology inferred from imports would produce.
    """
    outcome = completed(tmp_path)
    emitted: dict[str, int] = {}
    for index, record in enumerate(outcome.stages):
        for identifier in record.consumes_artefacts:
            assert identifier in emitted, (record.stage, identifier)
            assert emitted[identifier] <= index
        for artefact in record.emits:
            emitted.setdefault(artefact.identifier, index)
    # And the run produced every kind this route has: no receiver, no
    # reduction, and the seven the direct route emits.
    kinds = {
        str(artefact.kind) for record in outcome.stages for artefact in record.emits
    }
    # ``docked_declaration`` is in the set because the docking stage emits an
    # artefact, so the recorded graph shows the honest model reaching the
    # solve. A new kind appearing here is not a slip to be absorbed -- this
    # expectation is what makes adding one a decision -- so it is listed
    # rather than the assertion loosened.
    assert kinds == {
        "transmitter_artifact",
        "declaration",
        "honest_distribution",
        "acceptance_set",
        "docked_declaration",
        "bundle",
        "key_rate_result",
    }


@pytest.mark.requires_qics
def test_the_digests_are_this_tier_s_own_and_are_stable(tmp_path: Path) -> None:
    """sha256 of the canonical JSON of the payload as the record writes it.

    NOT the envelope's ``content_hash``, which stays deferred with the artefact
    store: a hash field that nothing hashes may not be given a meaning
    incompatible with the one it will carry. This one is hashed here and says
    so.
    """
    outcome = completed(tmp_path)
    for record in outcome.stages:
        for artefact in record.emits:
            assert len(artefact.digest) == 64
            assert artefact.identifier == f"{artefact.kind}:{artefact.digest[:12]}"
    bundle = tmp_path / "bundle"
    assert bundle.exists()


@pytest.mark.requires_qics
def test_the_solve_stage_carries_its_children_and_one_alpha(tmp_path: Path) -> None:
    """Serialised by this tier from the result, with no module change.

    And the alpha child is ONE, because there is no outer search: run_slice
    takes one alpha and runs once (spec/architecture.md 6). A grid over alpha is a
    grid of runs, each carrying its own child, which is what makes key length
    against alpha plottable from the records alone.
    """
    outcome = completed(tmp_path)
    solve = next(
        record for record in outcome.stages if record.stage is SliceStage.SOLVE
    )
    names = [child.name for child in solve.children]
    assert names == [
        "bundle_validation",
        "map_generation_and_cross_validation",
        "frank_wolfe",
        "alpha",
        "key_length_assembly",
    ]
    alpha = next(child for child in solve.children if child.name == "alpha")
    assert alpha.detail["searched"] is False
    assert alpha.detail["alpha"] == 1.5
    # Wall times only where this tier measured one, which is nowhere inside.
    assert all(child.wall_time_s is None for child in solve.children)
    assert solve.wall_time_s is not None and solve.wall_time_s > 0.0


@pytest.mark.requires_qics
def test_the_record_carries_the_graph_and_its_rendering(tmp_path: Path) -> None:
    """Both, under one key, and the text is the list's own rendering."""
    outcome = completed(tmp_path)
    payload = record_run(outcome, config(), created_by="test").payload
    flow = payload["composition_flow"]
    assert [entry["stage"] for entry in flow["stages"]] == [
        str(record.stage) for record in outcome.stages
    ]
    assert flow["mermaid"] == mermaid(outcome.stages)
    assert all("consumes" in entry and "emits" in entry for entry in flow["stages"])


# ===========================================================================
#  The observer and the log
# ===========================================================================


@pytest.mark.requires_qics
def test_the_observer_sees_every_boundary_and_changes_no_outcome(
    tmp_path: Path,
) -> None:
    """Started before, finished or refused after, and the run is the same run.

    INSIDE THE SOLVE, ONE ``iterate`` EVENT PER FRANK-WOLFE ITERATE, carrying the
    iteration and its gap, between the solve's ``started`` and ``finished`` and nowhere
    else.
    """
    seen: list[StageEvent] = []
    with_observer = completed(tmp_path / "a", observer=seen.append)
    without = completed(tmp_path / "b")

    assert next(event.kind for event in seen) == "started"
    assert {event.kind for event in seen} == {"started", "finished", "iterate"}
    started = [event.stage for event in seen if event.kind == "started"]
    finished = [event.stage for event in seen if event.kind == "finished"]
    assert started == finished
    assert all(
        event.wall_time_s is not None for event in seen if event.kind == "finished"
    )

    iterates = [event for event in seen if event.kind == "iterate"]
    assert all(event.stage is SliceStage.SOLVE for event in iterates)
    assert [event.iteration for event in iterates] == list(
        range(1, len(iterates) + 1)
    )
    assert all(event.gap is not None for event in iterates)
    solve_start = next(
        index
        for index, event in enumerate(seen)
        if event.kind == "started" and event.stage is SliceStage.SOLVE
    )
    solve_end = next(
        index
        for index, event in enumerate(seen)
        if event.kind == "finished" and event.stage is SliceStage.SOLVE
    )
    assert all(
        solve_start < index < solve_end
        for index, event in enumerate(seen)
        if event.kind == "iterate"
    )
    certificate = with_observer.key_rate.certificate
    assert iterates[-1].gap == certificate["frank_wolfe_gap"]

    # THE OUTCOME IS UNCHANGED, which is the one thing an observer may not do.
    assert with_observer.key_rate.key_length == without.key_rate.key_length
    assert with_observer.key_rate.h_low == without.key_rate.h_low
    assert with_observer.key_rate.h_lb == without.key_rate.h_lb


def test_an_exception_inside_the_observer_is_the_caller_s_bug() -> None:
    """It propagates. Swallowing it would turn a defect into a quieter run."""

    def explode(event: StageEvent) -> None:
        raise RuntimeError("the caller's bug")

    recorder = FlowRecorder(device_prologue=False, observer=explode)
    with pytest.raises(RuntimeError, match="the caller's bug"):
        recorder.start(SliceStage.COMPILATION)


def test_one_structured_line_per_transition_with_the_run_id_and_the_stage(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """On ``certiqs_key.runs``, and the library configures no handler."""
    recorder = FlowRecorder(
        device_prologue=False, run_id="deadbeef", observer=None
    )
    with caplog.at_level(logging.INFO, logger="certiqs_key.runs"):
        recorder.start(SliceStage.COMPILATION)
        recorder.executed(SliceStage.COMPILATION)
    records = [entry for entry in caplog.records if entry.name == "certiqs_key.runs"]
    assert len(records) == 2
    for entry in records:
        assert entry.run_id == "deadbeef"  # type: ignore[attr-defined]
        assert entry.stage == "compilation"  # type: ignore[attr-defined]
        assert entry.stage_module == "protocol-compiler"  # type: ignore[attr-defined]
    assert [entry.event for entry in records] == ["started", "finished"]  # type: ignore[attr-defined]


def test_the_library_installs_no_handler() -> None:
    """A library that chose where a caller's output goes would be deciding."""
    from certiqs_key.runs.flow import LOGGER

    assert LOGGER.handlers == []


# ===========================================================================
#  prepare's planned list against the executed one
# ===========================================================================


@pytest.mark.requires_qics
def test_the_planned_list_matches_the_executed_one_on_a_successful_run(
    tmp_path: Path,
) -> None:
    """Same stages, same consumed keys, same artefact kinds.

    This is what keeps the two honest. A stage that started reading a new
    configuration key and did not say so in ``PLANNED_CONFIG_KEYS`` fails here
    rather than leaving a preparation that quietly under-reports.

    THE EXECUTED LIST MUST STATE ITS OWN KEYS. Comparing ``plan.consumes_config``
    against ``run.consumes_config or PLANNED_CONFIG_KEYS[run.stage]`` would let
    an executed stage that recorded NO keys fall back to the planned table and
    pass -- which is precisely the under-reporting the paragraph above says the
    test exists to catch. There is no fallback.

    THE ARTEFACT KINDS ARE HELD THE SAME WAY, with
    ``PLANNED_ARTEFACT_KINDS``. A planned stage cannot name artefact IDS -- an
    id is ``<kind>:<digest prefix>`` of something that has been computed -- so
    without that table a preparation's graph would have configuration edges
    and nothing else. The table is a declaration, and this is where it is held
    against what a run actually consumed; a stage that started consuming a new
    KIND and did not say so fails here. The comparison is on the kinds in
    ORDER, not as sets, because a stage handed two artefacts of one kind
    consumed two things.
    """
    planned = prepare(
        config(), specification=bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert isinstance(planned, Preparation)
    executed = completed(tmp_path)

    assert [record.stage for record in planned.stages] == [
        record.stage for record in executed.stages
    ]
    for plan, run in zip(planned.stages, executed.stages, strict=True):
        assert set(plan.consumes_config) == set(run.consumes_config), plan.stage
        # ... and both are the declared table, which is the third source that
        # would otherwise be free to drift from the two.
        assert set(plan.consumes_config) == set(PLANNED_CONFIG_KEYS[plan.stage])
        assert plan.consumes_artefact_kinds == run.consumes_artefact_kinds, plan.stage
        # An executed stage's kinds are read back off the ids it recorded, so
        # this also asserts that the two halves of one record agree.
        assert run.consumes_artefact_kinds == tuple(
            artefact_kind_of(identifier) for identifier in run.consumes_artefacts
        ), run.stage


@pytest.mark.requires_qics
def test_the_docking_stage_emits_what_the_bundle_write_consumes(
    tmp_path: Path,
) -> None:
    """The trace does not stop at ``docking``: the graph reaches the solve.

    ``docking`` emits an artefact that ``bundle_write`` consumes, so the
    recorded composition graph shows the honest model and the acceptance set
    reaching the solve. Asserted as a CHAIN rather than as the presence of a
    key, because what matters is the reachability and not the field.
    """
    executed = completed(tmp_path)
    stages = {record.stage: record for record in executed.stages}

    docking = stages[SliceStage.DOCKING]
    emitted = [artefact.identifier for artefact in docking.emits]
    assert [artefact.kind for artefact in docking.emits] == [
        ArtefactKind.DOCKED_DECLARATION
    ]
    assert emitted[0] in stages[SliceStage.BUNDLE_WRITE].consumes_artefacts

    # The whole path, one edge at a time: the honest distribution reaches the
    # solve. Each link is "emitted here, consumed there" and nothing else.
    honest = stages[SliceStage.HONEST_MODEL].emits[0].identifier
    assert honest in stages[SliceStage.ACCEPTANCE_CONSTRUCTION].consumes_artefacts
    acceptance = stages[SliceStage.ACCEPTANCE_CONSTRUCTION].emits[0].identifier
    assert acceptance in docking.consumes_artefacts
    bundle = stages[SliceStage.BUNDLE_WRITE].emits[0].identifier
    assert bundle in stages[SliceStage.SOLVE].consumes_artefacts


def test_a_planned_stage_on_the_direct_route_promises_no_prologue_artefact() -> None:
    """The compilation consumes nothing where there was no device prologue.

    ``PLANNED_ARTEFACT_KINDS`` names a receiver artefact and a reduction chain
    for the compilation, which is true on the device route and false on the
    other one. A planned edge to a stage that is not on this route would be a
    promise the run cannot keep.

    WHAT THIS ASSERTS AND WHAT IT DOES NOT. The compilation has ALREADY RUN by
    the time ``prepare`` returns, so its entry here is the recorded one and the
    empty tuple below is what the run consumed -- NOT the route filter of
    ``_planned_kinds`` doing its work. The filter is exercised on
    a recorder driven directly, in
    ``test_the_route_filter_drops_the_prologue_kinds_a_direct_route_cannot_emit``
    below.
    """
    planned = prepare(
        config(), specification=bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert isinstance(planned, Preparation)
    stages = {record.stage: record for record in planned.stages}
    assert stages[SliceStage.COMPILATION].consumes_artefact_kinds == ()
    # ... while the stages after it still promise their own edges.
    assert stages[SliceStage.SOLVE].consumes_artefact_kinds == (ArtefactKind.BUNDLE,)


def test_a_planned_stage_on_the_device_route_promises_the_prologue_s_artefacts() -> (
    None
):
    """And on the device route the compilation's two edges ARE promised.

    The other half of the test above: dropping the two kinds unconditionally
    would have passed that one.
    """
    outcome = prepared_device_route()
    assert isinstance(outcome, Preparation)
    stages = {record.stage: record for record in outcome.stages}
    # The compilation RAN in a preparation, so it carries ids, not kinds from
    # the table -- and the kinds read back off those ids are the two.
    assert stages[SliceStage.COMPILATION].consumes_artefact_kinds == (
        ArtefactKind.RECEIVER_ARTIFACT,
        ArtefactKind.REDUCTION_CHAIN,
    )
    assert stages[SliceStage.DOCKING].consumes_artefact_kinds == (
        ArtefactKind.DECLARATION,
        ArtefactKind.ACCEPTANCE_SET,
    )


@pytest.mark.requires_qics
def test_every_row_of_the_declared_kind_table_is_held_by_a_run(
    tmp_path: Path,
) -> None:
    """The table is a DECLARATION, and four of its ten rows would be held by nothing.

    Mutating those rows would leave the suite green without this test.
    ``FlowRecorder.planned`` returns the RECORDED entry for any stage that has
    already run, and a preparation always runs the compilation (and, on the
    device route, the three prologue stages). So the planned-versus-executed
    tests compare run-derived kinds against run-derived kinds for
    ``receiver_construction``, ``receiver_docking``, ``reduction`` and
    ``compilation``, and those four rows of the table were asserted nowhere.

    This is the artefact-kind half of what the config-key half already had:
    that test compares the plan and the run AND both against
    ``PLANNED_CONFIG_KEYS``, which is the third source that would otherwise be
    free to drift from the two.
    """
    executed = completed(tmp_path)
    for record in executed.stages:
        assert record.status is StageStatus.EXECUTED, record.stage
        declared = tuple(
            kind
            for kind in PLANNED_ARTEFACT_KINDS[record.stage]
            # The direct route: the two kinds only a device prologue emits are
            # not promised, because no stage on this route emits them.
            if kind not in DEVICE_PROLOGUE_KINDS
        )
        assert record.consumes_artefact_kinds == declared, record.stage


def test_the_route_filter_drops_the_prologue_kinds_a_direct_route_cannot_emit() -> (
    None
):
    """``_planned_kinds`` on a recorder driven directly, which is the only way in.

    Through :func:`prepare` the filter is unreachable: the one stage whose row
    names a prologue kind and which is NOT itself in the prologue is the
    compilation, and that has always executed by the time ``planned`` is
    called. Driving the recorder itself is
    what exercises the branch, and a recorder is a public class of this module.
    """
    direct = FlowRecorder(device_prologue=False).planned()
    compilation = next(
        record for record in direct if record.stage is SliceStage.COMPILATION
    )
    assert compilation.status is StageStatus.PLANNED
    assert compilation.consumes_artefact_kinds == ()

    device = FlowRecorder(device_prologue=True).planned()
    with_prologue = next(
        record for record in device if record.stage is SliceStage.COMPILATION
    )
    assert with_prologue.consumes_artefact_kinds == (
        ArtefactKind.RECEIVER_ARTIFACT,
        ArtefactKind.REDUCTION_CHAIN,
    )
    # ... and the stages the direct route does not run are absent from it
    # rather than present and empty.
    assert SliceStage.RECEIVER_DOCKING not in {record.stage for record in direct}


def test_a_kind_is_read_off_an_id_and_never_guessed() -> None:
    """:func:`artefact_kind_of` reads what the id carries.

    An id IS ``<kind>:<digest prefix>``, so this is a parse and not an
    inference -- which is the whole reason a planned entry may carry kinds
    without breaking the rule that every recorded edge comes from what was
    passed.
    """
    assert artefact_kind_of("bundle:0123456789ab") is ArtefactKind.BUNDLE
    assert (
        artefact_kind_of("docked_declaration:0123456789ab")
        is ArtefactKind.DOCKED_DECLARATION
    )
    # A silent fallback would put an invented kind on a graph edge.
    with pytest.raises(ValueError, match="not an artefact id"):
        artefact_kind_of("bundle")
    with pytest.raises(ValueError):
        artefact_kind_of("not_a_kind:0123456789ab")


# ===========================================================================
#  The DEVICE route, on everything that needs no oracle
# ===========================================================================


def prepared_device_route(**overrides: object):
    """Return the optical instance's own preparation, through its own surface.

    NO INSTANCE IS NAMED IN AN ASSERTION BELOW; what is named here is which
    route is being exercised, and this is the repository's device route. The
    preparation runs the three prologue stages and the compilation and stops
    where the oracle would be needed, which is why this whole section costs
    hundredths of a second and is default-tier.
    """
    from instances.optical_bb84.surface import default_config, preparation

    return preparation(default_config(**overrides))


def test_the_device_route_records_its_three_prologue_stages_in_order() -> None:
    """The half of the graph that carries the receiver and the reduction."""
    prepared = prepared_device_route()
    assert isinstance(prepared, Preparation), prepared
    executed = [
        record.stage
        for record in prepared.stages
        if record.status is StageStatus.EXECUTED
    ]
    assert executed == [
        SliceStage.RECEIVER_CONSTRUCTION,
        SliceStage.RECEIVER_DOCKING,
        SliceStage.REDUCTION,
        SliceStage.COMPILATION,
    ]
    assert prepared.receiver_artifact is not None
    assert prepared.reduction_artifact is not None


def test_every_consumed_artefact_on_the_device_route_was_emitted_earlier() -> None:
    """The first property of the provenance graph, on the route with a prologue.

    And the prologue's emissions are CONSUMED rather than dangling: the
    compilation names the receiver artefact and the reduction chain its
    specification was built from, so the graph is connected from the first
    stage to the last rather than starting again at the compiler.
    """
    prepared = prepared_device_route()
    assert isinstance(prepared, Preparation), prepared
    emitted: dict[str, int] = {}
    for index, record in enumerate(prepared.stages):
        for identifier in record.consumes_artefacts:
            assert identifier in emitted, (record.stage, identifier)
            assert emitted[identifier] <= index
        for artefact in record.emits:
            emitted.setdefault(artefact.identifier, index)
    kinds = {
        str(artefact.kind) for record in prepared.stages for artefact in record.emits
    }
    # The two kinds only this route has, beside the compiler's own two.
    assert {"receiver_artifact", "reduction_chain"} <= kinds
    compilation = next(
        record
        for record in prepared.stages
        if record.stage is SliceStage.COMPILATION
    )
    assert len(compilation.consumes_artefacts) == 2


def test_the_mermaid_text_of_the_device_route_is_generated_from_its_list() -> None:
    """The second property, on the route with three more nodes.

    The renderer is told nothing about routes: it draws what the list says, so
    a route it has never seen renders correctly.
    """
    prepared = prepared_device_route()
    assert isinstance(prepared, Preparation), prepared
    text = mermaid(prepared.stages)
    assert text.startswith("flowchart TD\n")
    assert text.count("-->") == len(prepared.stages) - 1
    for index, record in enumerate(prepared.stages):
        assert f"s{index}[" in text
        assert str(record.stage) in text
    for stage in (
        SliceStage.RECEIVER_CONSTRUCTION,
        SliceStage.RECEIVER_DOCKING,
        SliceStage.REDUCTION,
    ):
        assert str(stage) in text


def test_a_refusal_inside_the_device_prologue_stops_the_route() -> None:
    """The third property, forced AT A PROLOGUE STAGE.

    The forcing is the honest one and not a stub: the instance's receiver is
    compiled from float-evaluated optics, so its declared family has a
    completeness defect of about ``1.1e-16`` that the instance repairs by
    snapping -- and a run declaring ``tau = 0`` has permitted no repair at all.
    The rows adapter refuses with the receiver's own code, at the docking
    stage, and every stage after it is ``not_executed`` rather than absent.

    IT IS ALSO WHERE ``declared_tolerance`` IS SPENT, which is the one entry of
    ``PLANNED_CONFIG_KEYS`` naming a key this tier does not hand over:
    the instance's adapter closes over the ceiling and spends it here.

    ``tau`` decides only a snap made
    WITHOUT a usable reference; the default device is snapped against its
    exact reference and kept, whatever ``tau``. The forcing is therefore a
    two-photon device whose reference is enclosed, in a run that declares
    enclosed references not used: its blocks are snapped from the binary64
    data, whose completeness defect ``tau = 0`` does not permit.
    """
    from instances.optical_bb84.surface import default_config

    base = default_config()
    refused = prepared_device_route(
        device={**base.device, "photon_cutoff": F(2), "exact_window": F(3)},
        declared_tolerance=0.0,
        reference_enclosure=False,
    )
    assert isinstance(refused, SliceRefusal), refused
    assert refused.stage is SliceStage.RECEIVER_DOCKING
    statuses = {record.stage: record.status for record in refused.stages}
    assert statuses[SliceStage.RECEIVER_CONSTRUCTION] is StageStatus.EXECUTED
    assert statuses[SliceStage.RECEIVER_DOCKING] is StageStatus.REFUSED
    for stage in (
        SliceStage.REDUCTION,
        SliceStage.COMPILATION,
        SliceStage.SOLVE,
    ):
        assert statuses[stage] is StageStatus.NOT_EXECUTED, stage
    docking = next(
        record
        for record in refused.stages
        if record.stage is SliceStage.RECEIVER_DOCKING
    )
    assert docking.reason == refused.reason
    assert docking.consumes_config == ("declared_tolerance",)


def test_a_reason_with_a_quotation_mark_does_not_break_the_mermaid_text() -> None:
    """A refusing module's reason is carried VERBATIM into a node label.

    This tier neither owns that vocabulary nor edits it, so the renderer
    escapes rather than rewrites: an unescaped ``"`` would close the label
    early and produce text no renderer accepts.
    Every reason code in the tree is an identifier today, which is what makes
    this latent rather than broken.
    """
    from certiqs_key.runs.flow import StageRecord

    record = StageRecord(
        stage=SliceStage.COMPILATION,
        module="protocol-compiler",
        status=StageStatus.REFUSED,
        reason='the module said "no"',
    )
    text = mermaid([record])
    assert '"no"' not in text
    assert "#quot;no#quot;" in text
    # The label is still ONE node on ONE line, which is what the escaping is
    # for: the text below the header is a single node declaration.
    assert len(text.strip().splitlines()) == 2


@pytest.mark.requires_qics
def test_a_non_degenerate_envelope_reaches_the_record(tmp_path: Path) -> None:
    """The honest envelope through the run tier.

    A provider returning an envelope built from two BB84 honest laws: the run
    completes, the record carries the envelope and the tag, the one-law table
    is null, and the honest artefact points at the envelope.
    """
    from certiqs_key.statistics import HonestEnvelope

    low_model = honest_provider(F(1, 60))
    high_model = honest_provider(F(1, 40))

    def envelope_provider(declaration):  # noqa: ANN001, ANN202
        low = dict(low_model(declaration))
        high = dict(high_model(declaration))
        return HonestEnvelope(
            lower={key: min(low[key], high[key]) for key in low},
            upper={key: max(low[key], high[key]) for key in low},
        )

    outcome = run_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        honest_provider=envelope_provider,
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        oracle=oracle(),
        directory=tmp_path / "bundle",
        created_by="test",
        declared_tolerance=0.0,
        alpha=1.5,
        run_id=config().digest(),
    )
    assert not isinstance(outcome, SliceRefusal), outcome
    record = record_run(outcome, config(), created_by="test")
    stage = record.payload["stages"]["acceptance_construction"]
    assert stage["honest_distribution"] is None
    assert stage["honest_model_tag"] == "envelope_honest_rounds"
    lower, upper = stage["honest_envelope"]["lower"], stage["honest_envelope"]["upper"]
    assert set(lower) == set(upper)
    assert any(F(lower[key]) < F(upper[key]) for key in lower)
