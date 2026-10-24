"""The optical BB84 device prologue, run without a solver, for tests to share.

spec/architecture.md 6's first three device stages -- receiver construction, docking
through this instance's rows adapter, and the reduction -- plus the compilation
that turns their two artifacts into a declaration. That is everything up to the
acceptance set, and it is the part with no solver in it: three unit modules and
the integration module all need a real declaration and none of them should pay
for a Frank-Wolfe run to get one.

WHY IT IS A COPY OF THE ORDER AND NOT A CALL INTO IT
====================================================
:func:`certiqs_key.runs.pipeline._run_device_prologue` runs exactly these stages and
is private. A test that reached into it would be asserting against a name the
orchestration tier does not publish; a test that re-ran the stages by hand in a
different ORDER would be asserting against a path no run takes -- and
``reductions`` Section 2.2 says of its own three steps that "THE ORDER IS
PART OF THE INTERFACE, NOT AN IMPLEMENTATION DETAIL".

So this helper composes the PUBLIC entry points in the published order, and
:func:`test_the_prologue_here_agrees_with_the_one_a_run_takes` in
``tests/unit/test_optical_bb84_device.py`` pins it against what
:func:`~certiqs_key.runs.pipeline.run_slice` actually does. If the pipeline's order
changes, that test fails rather than this helper silently testing a path that no
longer exists.

WHERE THE DEVICE COMES FROM. The optical BB84 instance is its template,
``instances/optical_bb84/protocol.yaml``: the device requests and the
specification provider are the template's lowering
(``tests/support/lowered_templates.py``), at the configuration the receiver's
parameters, the route and the acceptance map name.

Not frozen and not a registry entry. ``tests/oracles/`` is the frozen tree of
the frozen oracle registry and this file is not in it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from instances.common.optics import ReceiverParameters
from tests.support.lowered_templates import ENCODED, MERGED_DISCARD, optical_lowered

from certiqs_key.protocol_compiler.compile import (
    CompilationResult,
    compile_specification,
)
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.receiver.docking import DockingRefusal, receiver_artifact_rows
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.inputs import ReductionCall
from certiqs_key.runs.pipeline import AdapterRefusal, DeviceRequests

__all__ = ["Prologue", "PrologueRefused", "run_prologue"]


class PrologueRefused(Exception):
    """A stage declined. Carries the stage and that module's own reason.

    An exception rather than a returned union because a test that wanted the
    refusal asks for it explicitly with :func:`pytest.raises`, and a test that
    wanted the declaration should not have to unpack one.
    """

    def __init__(self, stage: str, reason: str, detail: str) -> None:
        """Record the stage, the module's own reason, and its message."""
        super().__init__(f"{stage}: {reason}: {detail}")
        self.stage = stage
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Prologue:
    """Everything the three device stages produced, plus the compilation."""

    receiver: ReceiverMeasurementArtifact
    reduction: ProofReductionArtifact
    compilation: CompilationResult
    #: What this instance's rows adapter reported, or ``None`` where none ran.
    adaptation: object | None = None

    @property
    def declaration(self) -> CandidateDeclaration:
        """The compiled declaration. Raises where the compilation refused."""
        declaration = self.compilation.declaration
        if declaration is None:  # pragma: no cover - guarded by run_prologue
            raise PrologueRefused("compilation", "refused", "no declaration")
        return declaration


def run_prologue(
    parameters: ReceiverParameters | None = None,
    *,
    route: str = ENCODED,
    declared_tolerance: float = 1e-12,
    alice_z: Fraction = Fraction(1, 2),
    alice_x: Fraction = Fraction(1, 2),
    acceptance_map: str = MERGED_DISCARD,
) -> Prologue:
    """Run the three device stages and the compilation, in the published order.

    ``acceptance_map`` names which of the template's acceptance maps
    (:data:`~tests.support.lowered_templates.ACCEPTANCE_MAPS`) the declaration
    carries. The default is the coarsest arm, so that every caller written
    before there was a second one keeps compiling the declaration it compiled.
    ``alice_z`` and ``alice_x`` are Alice's basis weights, which the template's
    source fixes at ``1/2``; other weights lower the template with exactly its
    source weights edited (:func:`~tests.support.lowered_templates.
    optical_lowered`).

    Raises:
        PrologueRefused: where a module declined, naming the stage and that
            module's own machine-readable reason.
    """
    # ``tau``, the sweep's own declared ceiling. A DEFAULT IS ADMISSIBLE HERE
    # AND NOWHERE ELSE: this is a test helper, the number it declares is the
    # number the fig. 1 grid declares, and a test that wants a
    # different one passes it. Nothing in ``src/`` defaults it.
    lowering = optical_lowered(
        parameters,
        route=route,
        acceptance_map=acceptance_map,
        declared_tolerance=declared_tolerance,
        alice_z=alice_z,
        alice_x=alice_x,
    )
    device = lowering.device
    assert isinstance(device, DeviceRequests)
    assert lowering.specification_provider is not None

    emission = construct_receiver(device.receiver_request)
    if emission.refusal is not None:
        raise PrologueRefused(
            "receiver_construction",
            str(emission.refusal.reason),
            emission.refusal.detail,
        )
    artifact = emission.artifact
    assert artifact is not None

    # The run tier's order (runs/pipeline.py _run_device_prologue): the
    # instance's adapter docks the artefact itself, in the dark-composed form
    # it snaps and declares; without one the bare rows cross.
    adaptation: object | None = None
    if device.rows_adapter is not None:
        adapted = device.rows_adapter(artifact)
        if isinstance(adapted, AdapterRefusal):
            raise PrologueRefused("receiver_docking", adapted.reason, adapted.detail)
        rows, adaptation = adapted.rows, adapted.report
    else:
        docked = receiver_artifact_rows(artifact)
        if isinstance(docked, DockingRefusal):
            raise PrologueRefused("receiver_docking", str(docked.reason), docked.detail)
        rows = docked

    request = device.reduction_request
    # THE INSTANCE'S OWN ENTRY POINT, as the run tier takes it: which
    # reduction instance a device declares is the device's statement and not
    # this helper's.
    outcome = device.reduction_entry(
        ReductionCall(rows, device.reduction_declaration, request)
    )
    if outcome.refusal is not None:
        raise PrologueRefused(
            "reduction", str(outcome.refusal.reason), outcome.refusal.detail
        )
    reduction = outcome.artifact
    assert reduction is not None

    if device.carried_operator_provider is not None:
        requested = device.carried_operator_provider(reduction)
        if requested:
            outcome = device.reduction_entry(
                ReductionCall(
                    rows,
                    device.reduction_declaration,
                    replace(request, carried_operators=requested),
                )
            )
            if outcome.refusal is not None:
                raise PrologueRefused(
                    "reduction", str(outcome.refusal.reason), outcome.refusal.detail
                )
            assert outcome.artifact is not None
            reduction = outcome.artifact

    specification = lowering.specification_provider(artifact, reduction)
    compilation = compile_specification(specification)
    if compilation.refusal is not None:
        raise PrologueRefused(
            "compilation",
            str(compilation.refusal.reason),
            compilation.refusal.detail,
        )
    return Prologue(
        receiver=artifact,
        reduction=reduction,
        compilation=compilation,
        adaptation=adaptation,
    )
