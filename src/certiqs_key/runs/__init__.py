"""The orchestration tier: composing modules into runs, and recording what they said.

spec/architecture.md 3.3 and PRINCIPLES.md section 4. This package drives the modules
that own the mathematics and owns none of it. Nothing here has a mathematical contract,
nothing here is gated, and nothing here may compute a bound, an entropy, a POVM or an
acceptance set of its own.

WHAT THIS TIER OWNS, AND IT IS NOT NOTHING
==========================================
The retraction of ``proof-assembler`` (spec/modules.yaml; spec/future-scope.md) settled
that a composition root states no mathematics and is therefore not a module. It
did not settle that composing states nothing at all. Three things are genuinely
owned here, and each is real:

``the composition``
    :class:`~certiqs_key.runs.config.RunConfig` -- the fact that a particular
    ``rounds``, completeness budget and parameter block were selected TOGETHER
    for one run. :mod:`certiqs_key.meat_core.docking` records that no row of
    ``protocol-compiler``'s contract supplies ``rounds`` and no row emits it;
    something has to select it, and a run is that something.
``the order``
    the stages of :mod:`certiqs_key.runs.pipeline` -- eight for a declared-POVM
    slice, eleven for one whose Bob is a physical device -- and the rule that a
    REFUSAL by any of them is carried out as data rather than raised.
``the record``
    :mod:`certiqs_key.runs.record` -- what each module said at each boundary, in a
    form that survives the process. Deliberately NOT an envelope artifact; that
    module's docstring says why.

WHAT IT MUST NOT OWN
====================
Channel-model vocabulary, backend selection, and any protocol's identity. The
honest channel model arrives as a :data:`~certiqs_key.runs.pipeline.HonestProvider`
from an instance; the linear oracle arrives as an argument with no default,
because the capability probe that decides whether an oracle can serve a
declaration is ``meat-core``'s gate, which refuses an oracle that cannot
(spec/architecture.md 3.3, 7.3), and constructing a backend here would decide
something this tier does not own.

    alpha_search  the opt-in outer alpha search, run inside every instance's
                  runner where a configuration asks for it
    config        one run's inputs, as a swept-over, recorded value
    errors        the hard errors, the rule that a REFUSAL is not one, and the
                  closed vocabulary of input-refusal codes
    identifiers   presentation labels in, HDF5-safe stable IDs out
    iterate_file  a general run's final iterate, the seed of a warm start
    pipeline      the ordered stages, and the typed outcome they produce
    record        what one run did at every module boundary it crossed
    sweep         a grid and a loop, and deliberately nothing else
    wire          a docked declaration and its chain, as a schema 0.2.0 bundle
"""

from __future__ import annotations

from certiqs_key.runs.config import (
    RunConfig,
    SolverSettings,
    canonical_json,
    config_digest,
)
from certiqs_key.runs.errors import (
    RunError,
    RunInputError,
    RunInputReason,
    SliceAssemblyError,
)
from certiqs_key.runs.flow import StageRecord, StageStatus, mermaid, stage_list
from certiqs_key.runs.identifiers import sanitize, stable_id_map
from certiqs_key.runs.pipeline import (
    AdaptedRows,
    AdapterRefusal,
    DeviceEmission,
    DeviceRequests,
    HonestProvider,
    MultiDeviceRequests,
    Preparation,
    PreparationOutcome,
    RawJointProvider,
    RowsAdapter,
    SliceOutcome,
    SliceRefusal,
    SliceResult,
    SliceStage,
    SpecificationProvider,
    Station,
    prepare,
    run_slice,
)
from certiqs_key.runs.record import (
    RECORD_SCHEMA_VERSION,
    RecordedOutcome,
    RunRecord,
    jsonable,
    jsonable_exact,
    preparation_record,
    public_and_source_tables,
    receiver_payload,
    record_run,
    reduction_payload,
    write_record,
)
from certiqs_key.runs.sweep import SweptRun, grid, sweep
from certiqs_key.runs.wire import (
    WireLabels,
    build_bundle,
    bundle_documents,
    wire_labels,
)

__all__ = [
    "RECORD_SCHEMA_VERSION",
    "AdaptedRows",
    "AdapterRefusal",
    "DeviceEmission",
    "DeviceRequests",
    "HonestProvider",
    "MultiDeviceRequests",
    "Preparation",
    "PreparationOutcome",
    "RawJointProvider",
    "RecordedOutcome",
    "RowsAdapter",
    "RunConfig",
    "RunError",
    "RunInputError",
    "RunInputReason",
    "RunRecord",
    "SliceAssemblyError",
    "SliceOutcome",
    "SliceRefusal",
    "SliceResult",
    "SliceStage",
    "SolverSettings",
    "SpecificationProvider",
    "StageRecord",
    "StageStatus",
    "Station",
    "SweptRun",
    "WireLabels",
    "build_bundle",
    "bundle_documents",
    "canonical_json",
    "config_digest",
    "grid",
    "jsonable",
    "jsonable_exact",
    "mermaid",
    "preparation_record",
    "prepare",
    "public_and_source_tables",
    "receiver_payload",
    "record_run",
    "reduction_payload",
    "run_slice",
    "sanitize",
    "stable_id_map",
    "stage_list",
    "sweep",
    "wire_labels",
    "write_record",
]
