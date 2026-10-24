"""What one run did, at every module boundary it crossed, as inspectable data.

THIS IS NOT AN ENVELOPE ARTIFACT, AND THE REASON IS NOT COSMETIC
================================================================
The artefact envelope (spec/architecture.md 4.1;
:class:`certiqs_key.domain.manifest.OperatorBundleManifest`) requires
``mathematical_spec_version``, the ``<module-id>@<version>`` of the accepted
contract governing the producing module. A run record has no producing module
and no contract -- the orchestration tier owns no mathematics, which is the
whole point of PRINCIPLES.md section 4 -- so there is no honest value for
that field. spec/architecture.md 4.1 forbids giving a field a meaning
incompatible with the one it will carry, and writing a module id there for a
record no module produced would be exactly that.

So a run record is its own ``kind`` with its own shape. It keeps the four
load-bearing envelope fields that DO apply (``kind``, ``schema_version``,
``created_by``, ``payload``), and it records the CONSUMED contract versions as
payload data -- a statement about the run, not a claim about the record.

The four content-addressing fields -- ``artifact_id``, ``content_hash``,
``input_artifact_hashes``, ``provenance`` -- are absent for the same reason
:mod:`certiqs_key.domain.manifest` omits them: they are spec/future-scope.md section 1,
and accepting a hash field that nothing hashes would give it an incompatible
meaning. When the artifact store lands, this record gains them; nothing here
blocks that. The payload's own ``provenance`` block (record 0.20.0) is not the
envelope's: it names only the engine that wrote the record
(:mod:`certiqs_key.runs.provenance`), hashes nothing, and is what a future
envelope block would carry as a subset.

WHAT IT RECORDS, AND WHY IT IS ALMOST FREE
==========================================
Every module on the path already returns a typed record with a machine-readable
reason when it declines, and :class:`~certiqs_key.runs.pipeline.SliceResult` already
carries every intermediate one so that "a caller can see what each stage produced
without re-running it". This module does not compute any of that. It transcribes
it, once, into something that survives the process -- which is the only part that
was missing.

A REFUSAL IS RECORDED, NOT SUPPRESSED
=====================================
A run that refused produces a record, with the refusing stage and that module's
own reason code. A sweep over a grid where half the points refuse is a legitimate
result and reads as one.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import StrEnum
from fractions import Fraction
from pathlib import Path
from typing import Any

from certiqs_key.domain.claim_closure import module_version
from certiqs_key.foundations.exact import Cx, serialize_matrix
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.reasons import RefusalReason
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.runs.assumptions import (
    emitted_rows,
    route_exact_assumptions,
    run_claim_roots,
)
from certiqs_key.runs.channel import (
    BipartiteChannelInterface,
    ModeIntensityChannelInterface,
)
from certiqs_key.runs.config import RunConfig, config_digest, parameters_payload
from certiqs_key.runs.direct_route import (
    DirectRoute,
    annotate_snap_records,
    certified_premises,
    direct_route,
)
from certiqs_key.runs.errors import RunError
from certiqs_key.runs.flow import mermaid, stage_list
from certiqs_key.runs.pipeline import (
    Preparation,
    SliceOutcome,
    SliceRefusal,
    SliceResult,
)
from certiqs_key.runs.provenance import engine_identity
from certiqs_key.runs.surface import InstanceIdentity
from certiqs_key.statistics import HonestEnvelope, PolytopeGeometry

__all__ = [
    "RECEIVER_ROUTES",
    "RECORD_SCHEMA_VERSION",
    "RecordedOutcome",
    "RunRecord",
    "jsonable",
    "jsonable_exact",
    "preparation_record",
    "public_and_source_tables",
    "receiver_payload",
    "receiver_route",
    "record_run",
    "reduction_payload",
    "write_record",
]

#: What the shared serializers of this module read: a finished run, or a
#: PREPARATION, which carries the same compilation, declaration, artefacts and
#: specification without having solved anything.
#:
#: THE UNION IS DECLARED BECAUSE THE SHARING IS REAL. A consumer can serialise
#: a preparation by calling :func:`receiver_payload`,
#: :func:`public_and_source_tables` and :func:`reduction_payload` on a
#: :class:`Preparation`, which works because each reads only attributes both
#: classes have. The names are public, this alias says what they accept, and
#: :func:`preparation_record` is the whole shape so that a consumer need not
#: assemble it at all.
type RecordedOutcome = SliceResult | Preparation

#: Bumped when the payload shape changes. Independent of every contract version
#: and of the operator-bundle format version.
#:
#: A RENAME OF A ``SliceStage`` VALUE OR A REFUSAL REASON BUMPS THIS, and the
#: schema beside it (``record.schema.json``) is what a consumer generates types
#: from: both are strings a reader files on, so moving one silently would move
#: a consumer's meaning without moving its version.
RECORD_SCHEMA_VERSION = "0.46.0"


def jsonable(value: object) -> Any:
    """Render exact rationals as ``"p/q"`` and leave everything else alone.

    A ``Fraction`` is not JSON, and rendering one as a float would discard the
    exactness ``statistics`` Section 2.5 requires of every number it
    emits. The string form round-trips through :class:`~fractions.Fraction`
    exactly.
    """
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, tuple | list):
        return [jsonable(v) for v in value]
    return value


def _config_payload(config: RunConfig) -> dict[str, Any]:
    """Return the run config, flattened. ``model`` and ``device`` pass through.

    ``declared_tolerance`` is recorded VERBATIM and as a JSON NUMBER, which is
    what it is: spec/architecture.md 2.8 makes ``tau`` a binary64 datum
    in ``[0, 1)`` and :class:`~certiqs_key.runs.config.RunConfig` refuses a run
    that declares none, so there is no ``null`` branch left to write and none is
    written. It replaces the 0.3.0 key ``operator_tolerance``, whose ``null``
    meant "absent, read as exactly zero" -- a reading that no longer exists.

    IT IS NOT WHAT ANY MODULE WAS TOLD, and the record must not be read as
    saying so. No module is told a tolerance at all -- the apparatus is
    absent from ``meat-core``, and no ``module_tolerance`` key records a
    zero -- and this number is the ceiling on the
    pre-snap defect the INSTANCE was allowed to repair. The ``snaps`` block
    below is where it was spent.
    """
    payload = {
        "rounds": config.rounds,
        "completeness_budget": str(config.completeness_budget),
        "declared_tolerance": config.declared_tolerance,
        # The key-length parameters and A-AUTH's two run inputs (0.20.0), by
        # the one writer the configuration's own payload uses.
        "parameters": parameters_payload(config),
        "model": jsonable(config.model),
        "device": jsonable(config.device),
        "alpha": config.alpha,
        "constrained": (
            None if config.constrained is None else list(config.constrained)
        ),
        # The three fields a sweep may vary, and the digest of the whole.
        # ``solver`` is ``null`` where the caller forwarded
        # nothing and the solver used its own defaults -- a record that wrote
        # the library's current numbers there would be asserting a budget it
        # was never given, and those defaults are the solver's to move.
        "solver": None if config.solver is None else config.solver.as_payload(),
        "endpoint_rule": config.endpoint_rule,
        "tail_evaluation": config.tail_evaluation,
        "config_digest": config_digest(config),
    }
    if config.input_preparation:
        payload["input_preparation"] = jsonable(config.input_preparation)
    name_fields = config.to_payload().get("device_name_fields")
    if name_fields:
        payload["device_name_fields"] = name_fields
    if config.alpha_search is not None:
        # The opt-in outer alpha search (0.24.0), only where set, as the
        # configuration's own payload writes it.
        payload["alpha_search"] = config.alpha_search.as_payload()
    return payload


def _acceptance_payload(result: SliceResult) -> dict[str, Any]:
    """Return the acceptance construction's outputs, as it reported them."""
    construction = result.acceptance
    payload: dict[str, Any] = {
        "geometry": type(construction.acceptance_set).__name__,
        "support": list(construction.acceptance_support),
        "completeness_certified": str(construction.completeness_certified),
        "completeness_exact": construction.completeness_exact,
        "outcomes": list(construction.acceptance_set.outcomes),
        # THE DISTRIBUTION USED, as "p/q" strings per acceptance
        # label -- rendering an exact rational as a float would discard the
        # exactness the construction requires of every number it is given --
        # and the per-round distribution over X x V beside it where the
        # instance's honest model computes it.
        "honest_distribution": _honest_distribution_payload(result),
        "raw_joint_distribution": (
            None
            if result.raw_joint_distribution is None
            else {
                f"{x}|{v}": str(value)
                for (x, v), value in result.raw_joint_distribution.items()
            }
        ),
        "endpoint_rule": construction.honest_model.endpoint_rule,
        "tail_evaluation": construction.honest_model.tail_evaluation,
        "box": _box_payload(construction.acceptance_set),
    }
    honest = result.honest_distribution
    if isinstance(honest, HonestEnvelope):
        # THE HONEST-ENVELOPE BATCH. A range [p^-, p^+] per acceptance label,
        # as "p/q" strings, and the tag the module recorded: completeness is
        # read relative to the envelope, not to one law. The key is absent on a
        # one-law run, so its record is unchanged.
        payload["honest_envelope"] = {
            "lower": {label: str(value) for label, value in honest.lower.items()},
            "upper": {label: str(value) for label, value in honest.upper.items()},
        }
        payload["honest_model_tag"] = construction.honest_model.tag
    return payload


def _box_payload(
    acceptance_set: PolytopeGeometry,
) -> dict[str, dict[str, str]] | None:
    """Return the acceptance box ``[q^-, q^+]`` per outcome label, or ``None``.

    The box is the canonical-box sub-form of a polytope acceptance set
    (``box_bounds``, positional against ``outcomes``), keyed here by the
    record's outcome labels with each bound an exact ``"p/q"`` string, so a
    reader of the record alone sees the intervals the key length rests on.
    ``None`` where the set carries no box: a singleton, or a general polytope.
    """
    if acceptance_set.box_bounds is None:
        return None
    lower, upper = acceptance_set.box_bounds
    return {
        str(label): {"lower": str(low), "upper": str(high)}
        for label, low, high in zip(
            acceptance_set.outcomes, lower, upper, strict=True
        )
    }


def _honest_distribution_payload(result: SliceResult) -> dict[str, str] | None:
    """Return the one-law table, or ``None`` when the run used an envelope."""
    honest = result.honest_distribution
    if isinstance(honest, HonestEnvelope):
        return None
    return {label: str(value) for label, value in honest.items()}


def _receiver_surface(
    result: RecordedOutcome, declared_povm: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    """Return the receiver surface, present and shaped the same on EVERY route.

    On the other routes (supplied artefact; declared finite POVM with identity
    link), the same key holds the route name and the POVM that route supplies.
    So this key is never absent: what changes is the ``route``
    and what hangs off it, and a consumer reads one key on all three.

    THE DECLARED-FINITE ROUTE'S POVM IS THE DECLARED ``{F_v}``, per sector
    block, which is what that route supplies in place of a construction. It is
    PASSED IN rather than read here because the two outcomes carry it in
    different places and in different number types: a finished run has the
    DOCKED declaration's, as floats, and a preparation has the compiled
    declaration's own, exactly. See :func:`preparation_record`.

    IT IS PASSED AS A CALLABLE AND NOT A VALUE, so that the compiled-receiver
    route does not pay for a table it sets to ``None`` -- and, which is the
    reason that matters, so that a failure inside
    :func:`_declared_povm` cannot come out of a route that never reads it
    (its ``strict=True`` zip raises on a sector/block length mismatch).
    """
    artifact = result.receiver_artifact
    if artifact is not None:
        payload = receiver_payload(result)
        payload["route"] = "compiled_receiver"
        payload["receiver_route"] = receiver_route(result)
        payload["declared_povm"] = None
        return payload
    return {
        "refused": False,
        "route": "declared_finite_povm",
        "receiver_route": receiver_route(result),
        # EVERY KEY THE OTHER ROUTE CARRIES, SET TO NULL. An instance that
        # lacks a stage omits the key or sets it to null, never a differently
        # shaped key.
        "photon_cutoff": None,
        "probe_alphabet": None,
        "block_dimensions": None,
        "bound_evaluation": None,
        "calibration_coverage": None,
        "dark_count_route": None,
        "residuals": None,
        "assumptions": None,
        "assumption_ledger": None,
        "efficiency_normalization": None,
        "elements": None,
        # ``edges`` and ``coarse_graining`` hang off a CONSTRUCTION; the
        # property "the same keys on every route" is held by
        # ``test_the_two_routes_record_the_same_keys``.
        "edges": None,
        "coarse_graining": None,
        "modes": None,
        "port_map": None,
        "rows_adaptation": None,
        "declared_povm": declared_povm(),
    }


#: How a run's receiver was given, the closed list of
#: ``stages.receiver_construction.receiver_route`` (record schema 0.20.0;
#: ``receiver/def:compile``'s three input routes and Band A's declared POVM).
#: ``per-station`` where the stations of a two-station run were given
#: differently; each ``stages.stations[i]`` then names its own.
RECEIVER_ROUTES: tuple[str, ...] = (
    "port-grams",
    "instrument-matrix",
    "element-graph",
    "declared-finite-povm",
    "per-station",
)


def _artifact_route(artifact: ReceiverMeasurementArtifact) -> str:
    """Return the input route one receiver artefact was constructed from.

    READ OFF THE ARTEFACT'S PRESENCES, which its interface fixes (the outputs
    table and ``req:residual-emission``): ``receiver_construction`` is present
    exactly on route (iii), the element graph; the residuals ``r_1`` and
    ``r_3`` are emitted exactly on routes (ii) and (iii), so on a supplied
    family without a construction they say instrument matrix, and their
    absence says port Grams (route (i), where "there is no compilation").
    """
    if artifact.receiver_construction is not None:
        return "element-graph"
    residuals = {row.residual_id for row in artifact.validation_results.residuals}
    if residuals & {"r_1", "r_3"}:
        return "instrument-matrix"
    return "port-grams"


def receiver_route(outcome: RecordedOutcome | SliceRefusal) -> str:
    """Return how the run's receiver was given, one of :data:`RECEIVER_ROUTES`.

    A run with no receiver artefact at all took Band A's declared finite POVM
    (the compiler's identity link, ``protocol-compiler/thm:band-a``). Otherwise
    every receiver the run constructed -- the single device's, or each
    station's -- is read by :func:`_artifact_route`; one route is that route,
    two are ``per-station``. Derived at record time and never declared, so the
    record cannot name a route its artefacts contradict.
    """
    receivers = [
        *([] if outcome.receiver_artifact is None else [outcome.receiver_artifact]),
        *(emission.receiver for emission in outcome.device_artifacts),
    ]
    if not receivers:
        return "declared-finite-povm"
    routes = {_artifact_route(artifact) for artifact in receivers}
    return routes.pop() if len(routes) == 1 else "per-station"


def _docked_povm(result: SliceResult) -> dict[str, Any]:
    """Return a finished run's declared ``{F_v}``: the DOCKED one, as floats.

    What the solve was actually handed, per sector block. The exact operators of
    the same run reach a reader through the bundle on disk, which the record
    names, so nothing is lost by recording these as the floats the rest of this
    stage's keys are in.
    """
    if isinstance(result.docked, GeneralDeclaration):
        return {"factors": [
            {"label": f.label, "party": str(f.party), "members": {
                v: {s: _blocks(b) for s, b in blocks.items()}
                for v, blocks in f.blocks.items()
            }} for f in result.docked.factors
        ]}
    return {
        label: {sector: _blocks(block) for sector, block in blocks.items()}
        for label, blocks in result.docked.bob_povm.items()
    }


def _declared_povm(preparation: Preparation) -> dict[str, Any]:
    """Return a preparation's declared ``{F_v}``: the COMPILER's own, EXACTLY.

    A preparation has no docked declaration and no bundle, so this is the only
    place the operators of that route reach a consumer -- and it therefore
    emits them through the exact substrate's own serializer, which has an
    inverse, rather than through the float rendering a finished run's
    ``declared_povm`` uses. THE NESTING IS THE SAME (the label, then the sector
    block) AND THE LEAF TYPE IS NOT: a run's entry is ``[re, im]`` as floats
    and a preparation's is the exact ``"p/q"`` pair. Said here because a
    consumer that generated one type from the run schema would otherwise be
    surprised by the other.
    """
    declaration = preparation.declaration
    if declaration.bob_factors is not None:
        return {"factors": [
            {
                "party": family.party,
                "members": {
                    letter: {
                        sector: serialize_matrix(block)
                        for sector, block in zip(
                            family.sectors.labels, family.member(letter).blocks,
                            strict=True,
                        )
                    }
                    for letter in family.alphabet
                },
            }
            for family in declaration.bob_factors.factors
        ]}
    labels = declaration.sectors.labels
    return {
        str(label): {
            str(sector): serialize_matrix(block)
            for sector, block in zip(labels, operator.blocks, strict=True)
        }
        for label, operator in declaration.bob_povm.items()
    }


def _blocks(block: Any) -> list[list[list[float]]]:
    """Return one declared block as JSON: real and imaginary parts, per entry."""
    import numpy as np

    array = np.asarray(block)
    return [
        [[float(entry.real), float(entry.imag)] for entry in row] for row in array
    ]


def _structured_modes(result: RecordedOutcome) -> list[dict[str, Any]] | None:
    """Return the receiver's declared mode space as STRUCTURED modes.

    The declared mode space is carried as structured modes (``path``,
    ``polarization``, ``tau``), not only as label strings, so that a renderer
    groups beams by path without parsing labels. The artefact carries
    the labels, which are presentation metadata; the triple is the datum, and
    parsing ``Z_H`` back into a path and a polarization is exactly the guessing
    the structure exists to remove.

    IT COMES OFF THE CHANNEL INTERFACE where the instance declared one,
    because that is where an instance says which modes the channel acts on in
    structured form. A run with no channel interface reports ``None``.

    IT IS THE WHOLE DECLARED SPACE, and not the channel half. Returning
    ``channel_modes`` alone would leave the probe-side modes of the same
    space reaching a consumer only as the label strings of ``port_map``, so an
    optics view could group the channel beams by path but would have to draw
    the rest as unstructured rails. Each mode carries its
    :class:`~certiqs_key.runs.channel.ModeRole`, so a reader filters what it
    wants, and ``port_map`` stays the join to the artefact's own two orders.
    """
    interface = result.channel_interface
    if isinstance(interface, BipartiteChannelInterface):
        return None  # station mode spaces stay separate in channel_interface.arms
    if isinstance(interface, ModeIntensityChannelInterface):
        return [mode.as_payload() for mode in interface.arm.modes]
    if interface is None or interface.modes is None:
        return None
    return [mode.as_payload() for mode in interface.modes]


def receiver_payload(result: RecordedOutcome) -> dict[str, Any]:
    """``receiver``'s emitted artifact, in the keys it named them.

    Nothing is summarized into a verdict. The residuals travel with their own
    declared tolerances because Theorem ``thm:exact-and-evaluated`` (ii) asserts NO
    BOUND on the difference between the emitted floats and the exact quantities, so a
    reader who wants to know how close the device came must be able to see it.

    Raises:
        RunError: if ``result`` carries no receiver artefact. The function is
            public, so the caller is someone else and a bare ``assert`` -- an
            ``AssertionError`` with an empty message, or under ``-O`` no error
            at all -- is not an acceptable answer.
    """
    artifact = result.receiver_artifact
    if artifact is None:
        raise RunError(
            "receiver_payload is about a COMPILED receiver and this outcome "
            "has no receiver artefact: it took the declared-finite-POVM "
            "route. Read `stages.receiver_construction` (record_run) or "
            "`receiver_construction` (preparation_record), which is present "
            "on every route and names which one in its `route` key"
        )
    domain = artifact.bound_quantifier_domain
    payload: dict[str, Any] = {
        "refused": False,
        "photon_cutoff": domain.photon_cutoff,
        "probe_alphabet": list(domain.probe_alphabet),
        "block_dimensions": [
            {"photons": row.photons, "dimension": row.dimension}
            for row in artifact.block_dimensions
        ],
        "bound_evaluation": artifact.bound_evaluation,
        "calibration_coverage": artifact.calibration_coverage,
        "dark_count_route": str(artifact.dark_count_channel.route),
        "residuals": [
            {
                "residual_id": residual.residual_id,
                "value": residual.value,
                "tolerance": residual.tolerance,
                "photons": residual.photons,
                "setting": residual.setting,
            }
            for residual in artifact.validation_results.residuals
        ],
        "assumptions": {
            record.machine_key: record.never_verified
            for record in artifact.assumption_ledger
        },
        # THE ARTEFACT'S OWN ASSUMPTION LEDGER, row for row with the values each
        # row constrains, in the artefact's wire form (0.44.0). Where the
        # reductions artefact omits its A-RECV row, the supplier's keys reach
        # the record from here and not from that row
        # (reductions/req:recv-row-provenance (iii)); each stations[i].receiver
        # carries the same list in the artefact's payload.
        "assumption_ledger": jsonable(
            [
                {
                    "id": str(record.assumption_id),
                    "machine_key": record.machine_key,
                    "never_verified": record.never_verified,
                    "constrains": dict(record.constrains),
                }
                for record in artifact.assumption_ledger
            ]
        ),
        # THE EFFICIENCY NORMALIZATION (0.38.0;
        # receiver/detector-imperfections/req:normalization-record): the
        # factored loss the receiver was compiled at, every declared
        # efficiency beside the exact one compiled, and whether and why it
        # was applied, as the artefact's efficiency_record carries it. Since
        # 0.40.0 applied exactly where t < 1, and a factor of one, declared
        # or by default, is the reason factor_one (factor_declared says
        # which).
        "efficiency_normalization": (
            artifact.efficiency_record.normalization.as_payload()
        ),
    }
    construction = artifact.receiver_construction
    payload["modes"] = _structured_modes(result)
    payload["port_map"] = {
        "channel_labels": list(artifact.input_mode_space.channel_labels),
        "mode_labels": list(artifact.input_mode_space.mode_labels),
    }
    if construction is not None:
        payload["elements"] = [
            {
                "name": name,
                "catalogue_id": entry_id,
                "support": [str(mode) for mode in support],
                "parameters": jsonable(dict(parameters)),
            }
            for name, entry_id, support, parameters in construction.elements
        ]
        payload["edges"] = [list(edge) for edge in construction.edges]
        payload["coarse_graining"] = jsonable(
            {
                "letters": list(artifact.outcome_alphabet.letters),
                "fibres": {
                    letter: [list(pattern) for pattern in patterns]
                    for letter, patterns in artifact.outcome_alphabet.fibres
                },
            }
        )
    else:
        payload["elements"] = None
        payload["edges"] = None
        payload["coarse_graining"] = None
    if result.rows_adaptation is not None:
        # The caller's, verbatim and uninterpreted. See
        # :data:`certiqs_key.runs.pipeline.RowsAdapter`: what a run DECLARED rather
        # than what a module computed, and a run that declared something says so.
        payload["rows_adaptation"] = jsonable(dict(result.rows_adaptation))
    return payload


def public_and_source_tables(result: RecordedOutcome) -> dict[str, Any]:
    """Return the FULL public and source tables, not summaries.

    A reader of a record -- a report generator, a notebook, an inspector --
    needs the party partition with each party's readout alphabet, the two
    announcement maps with their alphabets, the sifting per announcement class,
    the key rule with its holder and alphabet and the built raw key map, the
    acceptance statistic and its alphabet, the public choices with their
    weights, the choice weighting a receiver factor declared (with its
    letters and the factor it applies to), and the transmitter artefact's
    source mode. Every one of them is
    already emitted by the compiler under the outputs table's own key, so this
    TRANSCRIBES the compiler's own record rather than re-deriving anything: a
    table this tier derived could differ from the one that was compiled, which
    is the whole failure mode the compiler's cross-validation exists to stop.

    THE EXACT ENTRIES CROSS AS ``"p/q"`` STRINGS, by :func:`jsonable_exact`:
    the compiler's machine record carries exact Gaussian rationals, which are
    the right form for a consumer that re-decides and are not JSON.
    """
    record = result.compilation.as_machine_record()
    public = {
        key: jsonable_exact(record.get(key))
        for key in (
            "party_partition",
            "announce_alice",
            "announce_bob",
            "accept_statistic",
            "key_map",
            "key_holder",
            "acceptance_alphabet",
            "label_index_map",
        )
    }
    declaration = result.declaration
    for key in ("transcript", "accept_statistic_general", "sector_factorisation"):
        if key in record:
            public[key] = jsonable_exact(record[key])
    public["alice_announcement_alphabet"] = list(
        declaration.alice_announcement_alphabet
    )
    public["bob_announcement_alphabet"] = list(declaration.bob_announcement_alphabet)
    public["key_alphabet"] = list(declaration.key_alphabet)
    # THE BUILT RAW KEY MAP AND THE SIFTING ARE THE COMPILER'S EMITTED ONES:
    # ``key_map`` above IS the built map (the compiler emits it under that key
    # after building it from the key rule), and the sifting per announcement
    # class is what ``accept_statistic`` carries -- the two are read off the
    # emitted record rather than reconstructed from the specification, because
    # a table this tier derived could differ from the compiled one.
    public["raw_key_map"] = public["key_map"]
    public["choice_weightings"] = _choice_weightings(record)

    artifact = result.specification.source.artifact if result.specification else None
    source: dict[str, Any] = {
        "source_mode": None if artifact is None else str(artifact.source_mode),
        "alice_dim": record.get("alice_dim"),
        "alice_marginal": jsonable_exact(record.get("alice_marginal")),
        "alice_povm": jsonable_exact(record.get("alice_povm")),
        "public_choices": None,
    }
    for key in (
        "alice_form", "alice_ensemble", "alice_povm_blocks", "alice_marginal_blocks"
    ):
        if key in record:
            source[key] = jsonable_exact(record[key])
    if artifact is not None:
        source["signal_alphabet"] = list(artifact.signal_alphabet)
        source["virtual_transmitted_system"] = artifact.virtual_transmitted_system
        source["virtual_ensemble_weights"] = jsonable_exact(
            dict(artifact.virtual_ensemble_weights)
        )
    choices = (
        None
        if result.specification is None
        else result.specification.source.alice_choices
    )
    if choices is not None:
        source["public_choices"] = {
            "party": str(choices.party),
            "choices": list(choices.choices),
            "weights": jsonable_exact(dict(choices.weights)),
        }
    return {"public": public, "source": source}


def _choice_weightings(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the def:weighted public choices the measured factors declared.

    THE COMPILER'S OWN ``choice_weighting_record``, TRANSCRIBED: one entry per
    measured factor at which a weighting was applied, in the factors' order,
    each naming its ``factor`` (``req:choice-weighting-record``; record
    0.30.0). Per entry the setting
    alphabet ``T``, the choice alphabet ``F`` in its declared order, the
    matrix ``P(f | t)`` keyed ``"<setting>|<choice>"`` with ``"p/q"`` values,
    the setting map ``t: V -> T``, and the support ``V_P`` as ``[label, v, f]``
    rows -- which is what lets a reader explain the choice component of an
    emitted label such as ``(H,gen)``. NO PARTY: the compiler's entry names
    the factor only (in the basic format a factor's party label may differ by
    sector); a station's party is ``stages.stations[i].party``.

    Until 0.30.0 this was ``compiled.public.choice_weighting``, one object or
    ``null``, and a specification weighting two factors was refused here.
    Empty where no factor declared a weighting (the compiler's record is
    ``None`` then) and on a refusal.
    """
    weightings = record.get("choice_weighting_record")
    if weightings is None:
        return []
    if not isinstance(weightings, Sequence) or isinstance(weightings, str):
        raise RunError(
            "the compiled record's choice_weighting_record is one entry per "
            f"weighted factor; got {type(weightings).__name__}"
        )
    return [jsonable_exact(entry) for entry in weightings]


def jsonable_exact(value: Any) -> Any:
    """Render a compiler payload as JSON: exact numbers as strings, never floats.

    A module's machine record carries exact Gaussian rationals, which is the
    right form for a consumer that re-decides and is not JSON; the string
    forms are the ones :func:`~certiqs_key.foundations.exact.serialize_matrix`
    writes. Nothing is rounded.
    """
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, Cx):
        return [str(value.re), str(value.im)]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: jsonable_exact(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {_key(key): jsonable_exact(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [jsonable_exact(item) for item in value]
    if isinstance(value, StrEnum):
        return str(value)
    return value


def _key(key: Any) -> str:
    """Render a mapping key as a string, joining a pair with ``|``."""
    if isinstance(key, tuple):
        return "|".join(str(part) for part in key)
    return str(key)



def reduction_payload(result: RecordedOutcome) -> dict[str, Any]:
    """``reductions``' emitted artifact, at the granularity a reader needs.

    The target POVM itself is NOT here: it reaches the disk in the bundle, which
    is the artifact of record for operators. What is here is the shape a reader
    checks a bundle against -- the sector decomposition, the chain, the licence
    slot -- and the tolerance record, which travels with the declaration by
    Section 4.13's own rule.

    Raises:
        RunError: if ``result`` carries no reduction artefact. See
            :func:`receiver_payload` for why a public function states this
            rather than asserting it.
    """
    artifact = result.reduction_artifact
    if artifact is None:
        raise RunError(
            "reduction_payload is about a run that went through `reductions` "
            "and this outcome has no reduction artefact: the declared-finite-"
            "POVM route runs no reduction stage. A caller that does not know "
            "which route it has tests `result.reduction_artifact` first, as "
            "record_run and preparation_record both do"
        )
    descriptor = artifact.target_descriptor
    report = artifact.verification_report
    return {
        "refused": False,
        "route": str(artifact.route),
        "status": str(artifact.status),
        "target_dimension": descriptor.dimension,
        "target_sectors": [
            {"label": list(label), "dimension": dimension}
            for label, dimension in zip(
                descriptor.sectors.labels, descriptor.sectors.dimensions, strict=True
            )
        ],
        "outcome_correspondence": len(artifact.outcome_correspondence),
        "constraint_entries": len(artifact.constraint_list),
        "attack_set_license_present": artifact.attack_set_license is not None,
        "transported_operators": len(artifact.transported_operators),
        "chain": [
            {
                "link_id": link.link_id,
                "stage": str(link.stage),
                "kind": str(link.kind),
                "status": str(link.status),
            }
            for link in artifact.reduction_chain.links
        ],
        # THE PRODUCER'S OWN SNAP, in the position ``operator_tolerance_record``
        # held. It is never ``None`` (``reductions`` 1.0.1): a producer
        # that emitted anything established the six (D-EMIT) conditions of
        # spec/architecture.md 2.9, and this is what it established them on. The
        # per-block half is lifted into the top-level ``snaps`` block as well,
        # where a reader looking for "what moved on this run" will look.
        "emission_record": jsonable(artifact.emission_record.as_machine_record()),
        # THE REFERENCE COMPANION (0.27.0; reductions/req:reference-companion
        # (v), (vi)): its per-block record and a digest of its exact data, or
        # the reason none was emitted beside this artefact.
        "reference_companion": (
            None
            if artifact.reference_companion is None
            else jsonable(artifact.reference_companion.as_record())
        ),
        "receiver_spec_version": report.receiver_spec_version,
        "receiver_bound_evaluation": report.receiver_bound_evaluation,
        "requested_assurance": report.requested_assurance,
        # 0.44.0 (reductions/req:recv-row-provenance): the receiver artefact's
        # version where the artefact omitted its A-RECV row, the run having
        # built that receiver artefact, exact and rigorous; empty where the row
        # is emitted. A station's reduction carries the same key in its
        # machine record.
        "receiver_row_omitted_on_provenance": list(
            artifact.receiver_row_omitted_on_provenance
        ),
    }


def _solver_options_payload(result: SliceResult) -> dict[str, Any] | None:
    """Return the forwarded Frank-Wolfe budget, or ``None`` for the default.

    ``None`` here means "the caller forwarded nothing and
    :func:`~certiqs_key.solvers.frank_wolfe.solve_bundle` used its own declared
    default"; it does NOT mean "no budget applied". A record that substituted
    the library's current defaults would be this tier asserting a number it was
    never given, and the defaults are the solver's to move.
    """
    options = result.solver_options
    if options is None:
        return None
    # A field whose value is not JSON (the general format's warm-start seed)
    # records its own identity through ``as_payload``, never its matrices.
    return {
        field.name: (
            value.as_payload() if hasattr(value, "as_payload") else value
        )
        for field in fields(options)
        for value in (getattr(options, field.name),)
    }


def _solver_request_payload(result: SliceResult) -> dict[str, Any] | None:
    """Record the resolved common request, with seed identity but no matrices."""
    request = result.solver_request
    if request is None:
        return None
    return {
        field.name: value.as_payload() if hasattr(value, "as_payload") else value
        for field in fields(request)
        for value in (getattr(request, field.name),)
    }


def _snaps_payload(
    result: SliceResult, decision: DirectRoute | None = None
) -> dict[str, Any]:
    """Return every snap this run performed, from the two places entitled to one.

    spec/architecture.md 2.8, "Who snaps": declared data is snapped by the
    declarer, once, "by the snapping table of ``foundations/snap.py`` (§2.9)", and
    there are exactly two such parties on this path:

    * **the instance**, on what it declares about its device -- the receiver's
      blocks -- before any module sees them. That record arrives here as the
      rows adapter's report;
    * **the producer**, on its own emission, "where its exact construction lands
      off the binary64 lattice". That is ``reductions``'
      :class:`~certiqs_key.reductions.artifact.EmissionRecord`, one
      :class:`~certiqs_key.reductions.artifact.BlockEmissionRecord` per block.

    A CONSUMER NEVER APPEARS HERE, and its absence is the invariant this block
    exists to make visible: "no module repairs what it was handed". A third
    origin in this list would be a defect.

    NOTHING IS COMPUTED, SUMMARIZED OR RECONCILED. The two sources measure
    different objects at different points of the path and their numbers are not
    commensurable -- the instance's displacement is on a receiver POVM block,
    the producer's on the operators it emitted -- so they are transcribed side
    by side under their own origins rather than added up.
    """
    instance = (
        result.rows_adaptation
        if decision is None or result.device_artifacts
        else annotate_snap_records(result.rows_adaptation, decision.station(None))
    )
    payload: dict[str, Any] = {
        "declared_tolerance": result.declared_tolerance,
        "instance": None if instance is None else jsonable(instance),
    }
    if decision is not None:
        # THE RUN'S DECISION ON THE DIRECT ROUTE (0.27.0;
        # frank-wolfe/req:bracket-on-reference (v)): which blocks were
        # evaluated off their snap and which still rest on A-SNAP, beside the
        # compiled companion's record. Read by the manifest and the report.
        compiled = result.reference_companion
        payload["reference_companion"] = {
            **decision.as_record(),
            "compiled": None if compiled is None else jsonable(compiled.as_record()),
        }
    artifact = result.reduction_artifact
    if artifact is None:
        # The route that supplies a finished specification runs no producer, so
        # there is no emission to record. An empty list would claim a producer
        # ran and moved nothing.
        payload["producer"] = None
        payload.update(_snap_extrema(result, None))
        return payload
    emission = artifact.emission_record
    machine = emission.as_machine_record()
    payload["producer"] = {
        "lattice_exponent": emission.lattice_exponent,
        "six_condition_outcomes": jsonable(dict(emission.six_condition_outcomes)),
        "lattice_invariant_statement": emission.lattice_invariant_statement,
        "displaced": emission.displaced,
        # The normaliser's run settings and reference kind (always exact: the
        # handed datum is its own reference), and the data sectors with a
        # moved class, named provisionally (reductions/req:emission-record).
        "run_settings": jsonable(machine["run_settings"]),
        "reference_kind": emission.reference_kind,
        "snapped_measurement_assumption": jsonable(
            emission.snapped_measurement_assumption
        ),
        # Per data sector, per class: kept, or moved with its step, hosts,
        # weight and flag (def:emitnorm); and whether the run evaluated the
        # sector off its snap, which only a sector with a moved class can be
        # (0.28.0).
        "blocks": [
            {
                **jsonable(block.as_machine_record()),
                "evaluated_off_snap": _emission_evaluated_off(
                    decision, block.block_index
                ),
            }
            for block in emission.blocks
        ],
    }
    payload.update(_snap_extrema(result, emission))
    return payload


def _emission_evaluated_off(decision: DirectRoute | None, index: int) -> bool:
    """Whether one data sector of the single-device emission was evaluated off."""
    station = None if decision is None else decision.station(None)
    return station is not None and index in station.emission_sectors


def _snap_extrema(
    result: SliceResult, emission: Any | None
) -> dict[str, float | None]:
    """Return ``snap_max_defect`` and ``snap_max_displacement`` over the run.

    THE TWO SUMMARY NUMBERS THE REFERENCE DATASET CARRIES BY THOSE NAMES. They
    are a MAXIMUM OVER WHAT IS ALREADY RECORDED and not a second
    measurement: every per-step record stays beside them, because "the largest
    displacement over a run is a different fact from the displacement of one
    block" and a reader checking that a displacement is of the same order as
    the defect it corrects needs them paired.

    ``None`` on both where nothing was snapped -- which is the qubit slice's
    case, its receiver being a declared POVM -- because ``0.0`` would say a
    snap ran and moved nothing.

    WHAT IS MAXIMISED OVER, AND WHAT IS NOT. The defect is the instance's
    pre-snap defect, the number ``tau`` is the ceiling on; the displacement is
    the instance's lattice displacement together with the producer's per-block
    one. The two origins are not added and not reconciled -- they measure
    different objects at different points of the path -- but a MAXIMUM over
    displacements is still a displacement, which is why the second half takes
    both and the first half takes only the instance's: a producer's emission
    has no pre-snap defect against a declared ceiling, since it is verifying
    its own construction rather than repairing a declaration.
    """
    defects: list[float] = []
    displacements: list[float] = []
    for adaptation in _adaptations(result.rows_adaptation):
        for block in _measurement_blocks(adaptation):
            # A block snapped WITH a usable reference has no pre-snap defect
            # against tau: its defects are zero on the reference's ground
            # (``defects_ground`` ``reference``), and only measured ones count.
            pre_snap = block.get("pre_snap")
            if block.get("defects_ground") == "measured" and isinstance(
                pre_snap, Mapping
            ):
                defects.extend(
                    value for value in pre_snap.values() if isinstance(value, float)
                )
            moved = block.get("displacement")
            if isinstance(moved, float):
                displacements.append(moved)
    if emission is not None:
        displacements.extend(
            block.displacement
            for block in emission.blocks
            if isinstance(block.displacement, float)
        )
    return {
        "snap_max_defect": max(defects) if defects else None,
        "snap_max_displacement": max(displacements) if displacements else None,
    }


def _adaptations(adaptation: Mapping[str, object] | None) -> list[Mapping[str, Any]]:
    """Return the instance snap records of a run: the single one, or each station's."""
    if adaptation is None:
        return []
    stations = adaptation.get("stations")
    if isinstance(stations, Sequence) and not isinstance(stations, str):
        return [station for station in stations if isinstance(station, Mapping)]
    return [adaptation]


def _measurement_blocks(adaptation: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return every block record of an instance's measurement-family snaps."""
    snaps = adaptation.get("measurement_snaps")
    if not isinstance(snaps, Sequence) or isinstance(snaps, str):
        return []
    return [
        block
        for snap in snaps
        if isinstance(snap, Mapping)
        for block in (snap.get("blocks") or ())
        if isinstance(block, Mapping)
    ]


def _consumed_versions(result: SliceResult) -> dict[str, str]:
    """Return the module version of every module that contributed, as PAYLOAD.

    spec/architecture.md 3.3: the record "is deliberately NOT an envelope
    artefact: no module produced it, so it has no honest module version, and it
    carries the consumed module versions as payload data instead". 4.4 makes
    those versions part of the assumption manifest: "the MODULE VERSION of
    every module that contributed, taken from the envelope of each consumed
    artefact".

    EVERY ONE IS READ OFF WHAT THE MODULE EMITTED, with one exception that is
    named rather than hidden. ``meat-core``'s comes off the key-rate result,
    the compiler's off its own emitted record, the receiver's and the
    reduction's off their artefacts, and the transmitter's off the artefact the
    compiler read its source part from -- which is the compiler's own rule
    ("the transmitter's keys read off the transmitter artefact's own ledger")
    applied one tier up. ``statistics`` emits no version string at all (its
    interface says the CONSUMING RECORD carries it), so its consumed version is read
    from the generated claim-closure table
    (:func:`certiqs_key.domain.claim_closure.module_version`), which
    ``harness/generate_claim_closure.py`` writes from
    ``spec/modules/statistics/module.yaml`` and whose ``--check`` keeps it current.

    A MODULE THAT DID NOT RUN HAS NO ROW. The direct finite route invokes
    neither the receiver nor ``reductions``, and a row saying so would be a
    version consumed by nothing.
    """
    versions: dict[str, str] = {
        "meat-core": result.key_rate.mathematical_spec_version,
        # OFF THE EMITTED RECORD, not off an import of the compiler's constant:
        # a version read from an import is a version this tier asserts rather
        # than one it was handed.
        "protocol-compiler": str(
            result.compilation.as_machine_record()["mathematical_spec_version"]
        ),
        "statistics": f"statistics@{module_version('statistics')}",
    }
    specification = result.specification
    if specification is not None:
        versions["transmitter"] = (
            specification.source.artifact.mathematical_spec_version
        )
    if result.receiver_artifact is not None:
        versions["receiver"] = result.receiver_artifact.mathematical_spec_version
    if result.reduction_artifact is not None:
        versions["reductions"] = result.reduction_artifact.mathematical_spec_version
    for station, emission in enumerate(result.device_artifacts):
        versions[f"receiver.station{station}"] = (
            emission.receiver.mathematical_spec_version
        )
        versions[f"reductions.station{station}"] = (
            emission.reduction.mathematical_spec_version
        )
    return versions


def _assumption_manifest(result: SliceResult) -> dict[str, Any]:
    """Return the machine-generated assumption manifest of 4.4: the route-exact set.

    "Every result carries an assumption manifest, and this is required"
    (PRINCIPLES.md section 2.1). It is machine-generated, never hand-written,
    and it is assembled HERE because the run tier is the only place that holds
    every consumed artefact at once.

    FROM RECORD SCHEMA 0.20.0 IT IS THE ROUTE-EXACT SET
    (:mod:`certiqs_key.runs.assumptions`): the top-level
    results this run used, per module
    (:func:`~certiqs_key.runs.assumptions.run_claim_roots`), and every ledger
    row every emitter emitted with the values it binds
    (:func:`~certiqs_key.runs.assumptions.emitted_rows`), reconciled into one
    entry per engaged assumption against the union of those roots' closures
    (:func:`~certiqs_key.runs.assumptions.route_exact_assumptions`). Each
    entry carries the closure table's text snapshot and ``verification``
    field, so the record stays readable after the engine pin moves.
    A per-emitter listing would show A-SEQ several times (the transmitter,
    reductions and meat-core) and A-RECV once per station; each is one entry,
    with every emitter, and A-RECV's supplier version is the reductions
    emitter's ``inherited_from``. Where every reductions artefact omitted its
    A-RECV row (``reductions/req:recv-row-provenance``), A-RECV is listed as
    not engaged, discharged by that requirement.

    THE CLAIM GRAPH (record 0.13.0). ``claim_closure`` carries, for every root
    of the run, the claims and the assumption short ids with their owning
    claims, read from the generated package data of
    :mod:`certiqs_key.domain.claim_closure`. This tier computes no closure; a
    root the table lacks, or a row whose machine key names no assumption,
    raises :class:`~certiqs_key.domain.claim_closure.ClaimClosureError` rather
    than writing a manifest short of its claims. A disagreement between the
    rows and the closures is recorded under ``discrepancies`` and never refuses
    the record.
    """
    reconciled = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    return {
        **reconciled.as_payload(),
        "module_versions": _consumed_versions(result),
        "reported_tier": str(result.key_rate.reported_tier),
    }


def _key_rate_payload(result: SliceResult) -> dict[str, Any]:
    """``meat-core``'s result, including every field that withholds a claim.

    ONE RECORD FOR EVERY RUN (0.12.0): the general result's payload with its
    certificate merged in. BOTH LIVE TIERS, ON EVERY RUN, WITH A FIELD NAMING
    THE CLAIM (spec/architecture.md 2.8): ``h_low`` is the ``estimate``, a
    diagnostic that bounds the true ``h_low`` from ABOVE; ``h_lb`` (or
    ``h_lb_dropped`` beside its dropped set) is the ``first-order`` rung's
    lower bound, absent where no bracket was reported; ``first_order_clamped``
    says whether ``max{0, h_lb}`` clamped; ``reported_tier`` NAMES THE CLAIM
    the headline ``key_length`` carries. ``h_lb <= h_low`` is a consequence of
    exact real arithmetic, not a floating-point invariant, so their
    difference is a diagnostic a reader forms from the two.

    ``solver_options`` carries the forwarded budget: a record that
    reports ``iteration-limit`` without saying what the budget was is one a
    reader cannot act on.
    """
    rate = result.key_rate
    payload = rate.as_payload()
    payload["solver_options"] = _solver_options_payload(result)
    payload["solver_request"] = _solver_request_payload(result)
    payload.update(dict(rate.certificate))
    # THE CERTIFIED NUMBER'S PREMISE AT THE SNAP (0.35.0;
    # frank-wolfe/req:certified-evaluation (ix)): only the run holds the snap
    # records that name the moved blocks, so the run writes them here.
    premises = certified_premises(result)
    if premises is not None and isinstance(payload.get("certified"), Mapping):
        payload["certified"] = {**payload["certified"], **premises}
    return dict(jsonable(payload))


@dataclass(frozen=True)
class RunRecord:
    """One run's inspectable log. ``payload`` is JSON-ready."""

    kind: str
    schema_version: str
    created_by: str
    payload: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return the record as a plain JSON-ready mapping."""
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "created_by": self.created_by,
            "payload": dict(self.payload),
        }


def record_run(
    outcome: SliceOutcome,
    config: RunConfig,
    *,
    created_by: str,
    instance: InstanceIdentity | None = None,
) -> RunRecord:
    """Transcribe one completed or refused run into a :class:`RunRecord`.

    Args:
        outcome: what :func:`certiqs_key.runs.pipeline.run_slice` returned.
        config: the config that produced it, recorded so that a record is
            self-contained -- reading one should not require the script.
        created_by: what drove the run. Never an absolute path, timestamp or run
            ID (spec/architecture.md 2.6).
        instance: which instance ran, ``InstanceIdentity(DESCRIPTOR,
            PARAMETERS)`` of its surface, written as the ``instance`` block so
            that a reader gives every model and device value its meaning
            without importing the instance (0.20.0). ``None`` -- a test, a
            caller that composed a run by hand -- records ``null``.
    """
    payload: dict[str, Any] = {
        "config": _config_payload(config),
        "refused": outcome.refuses,
        "contracts": {},
        "stages": {},
        "instance": None if instance is None else instance.as_payload(),
        # WHICH ENGINE WROTE IT (0.20.0): distribution version, git commit and
        # dirty flag, null outside a checkout; on a refusal as well, since a
        # refusal is reproduced on the same code.
        "provenance": {"engine": dict(engine_identity())},
        # THE PROTOCOL DOCUMENT (0.21.0): verbatim, or null off the document
        # route; on a refusal as well, which must still name its protocol.
        "protocol_document": _protocol_document(outcome),
        # THE CHECK OF THE ACCEPTANCE SET AGAINST THE FEASIBLE STATISTICS
        # (0.37.0; meat-core/req:unreachable-acceptance-set (v)): whether the
        # run is checked and why not, on every run, and on a checked one the
        # bound with its tier and each order's comparison. Null only on an
        # outcome no run_slice returned (a hand-built one).
        "statistics_consistency": (
            None
            if outcome.statistics_consistency is None
            else jsonable(outcome.statistics_consistency.as_record())
        ),
    }

    if isinstance(outcome, SliceRefusal):
        if outcome.device_artifacts:
            payload["stages"]["stations"] = _station_payloads(outcome)
        stage: dict[str, Any] = {
            "refused": True,
            "reason": outcome.reason,
            "detail": outcome.detail,
        }
        if outcome.rule is not None:
            # ``reductions`` names the ROW that decided as well as the
            # reason, and the two are different facts.
            stage["rule"] = outcome.rule
        if outcome.plausibility is not None:
            # The run tier's own refusal (0.25.0): the bound and the ceiling
            # it exceeded, both, beside the estimate. Since 0.37.0 the core's
            # acceptance_set_unreachable refusal carries it too, and the
            # branch below names meat-core as the refuser there.
            stage["refused_by"] = "runs"
            stage["plausibility"] = jsonable(dict(outcome.plausibility))
        if outcome.reason == str(RefusalReason.ACCEPTANCE_SET_UNREACHABLE):
            # The core's own refusal at the solve stage (0.37.0;
            # meat-core/req:unreachable-acceptance-set (iv)); its numbers are
            # in payload.statistics_consistency.
            stage["refused_by"] = "meat-core"
        payload["stages"][str(outcome.stage)] = stage
        stages = stage_list(outcome)
        payload["composition_flow"] = {
            "stages": [entry.as_record() for entry in stages],
            "mermaid": mermaid(stages),
        }
        return RunRecord(
            kind="run-record",
            schema_version=RECORD_SCHEMA_VERSION,
            created_by=created_by,
            payload=payload,
        )

    payload["contracts"] = _consumed_versions(outcome)
    # WHICH HONEST MODEL, VERBATIM AND UNINTERPRETED. The key is present
    # on every route: ``null`` says no caller named one, which is the case a
    # reader of a record needs to be able to tell from "an override was used
    # and here is what it was".
    payload["honest_model_note"] = (
        None
        if outcome.honest_model_note is None
        else jsonable(dict(outcome.honest_model_note))
    )
    payload["assumption_manifest"] = _assumption_manifest(outcome)
    payload["stages"] = {
        "compilation": {"refused": False},
        "acceptance_construction": {
            "refused": False,
            **_acceptance_payload(outcome),
        },
        "bundle": {
            "directory": outcome.bundle_directory.name,
            "schema_version": outcome.bundle.manifest.schema_version,
        },
        "key_rate": _key_rate_payload(outcome),
        # PRESENT ON EVERY ROUTE, with ``route`` naming which.
        "receiver_construction": _receiver_surface(
            outcome, lambda: _docked_povm(outcome)
        ),
    }
    # the full tables, transcribed from the compiler's own record.
    payload["compiled"] = public_and_source_tables(outcome)
    # how A' entered the receiver, where the instance declared it.
    payload["channel_interface"] = (
        None
        if outcome.channel_interface is None
        else outcome.channel_interface.as_payload()
    )
    # TOP-LEVEL AND NOT A STAGE. A snap is not something a stage did: it is what
    # a DECLARING party asserted, and the two parties that make one sit at
    # different points of the path. Section 3.8 asks the run record to carry
    # every snap, and a reader looking for "what moved on this run" should find
    # one block rather than two stages to join.
    decision = direct_route(outcome)
    payload["snaps"] = _snaps_payload(outcome, decision)
    if outcome.reduction_artifact is not None:
        payload["stages"]["reduction"] = reduction_payload(outcome)
    if outcome.device_artifacts:
        payload["stages"]["stations"] = _station_payloads(outcome, decision)
    stages = stage_list(outcome)
    payload["composition_flow"] = {
        "stages": [stage.as_record() for stage in stages],
        "mermaid": mermaid(stages),
    }
    return RunRecord(
        kind="run-record",
        schema_version=RECORD_SCHEMA_VERSION,
        created_by=created_by,
        payload=payload,
    )


def _protocol_document(
    outcome: Preparation | SliceResult | SliceRefusal,
) -> dict[str, Any] | None:
    """Return the protocol document block (0.21.0), JSON-ready, or ``None``."""
    document = outcome.protocol_document
    return None if document is None else dict(jsonable(dict(document)))


def _station_payloads(
    outcome: Preparation | SliceResult | SliceRefusal,
    decision: DirectRoute | None = None,
) -> list[dict[str, Any]]:
    """Keep each station's identity, supplier record and preparation displacement.

    ``factor`` and ``party`` are the station's declared identity
    (:class:`~certiqs_key.runs.pipeline.Station`), held against the compiled
    declaration's measured factors before the record exists; a per-station
    stage of ``composition_flow`` names its station by that ``factor``.
    ``receiver_route`` is how that station's receiver was given (0.20.0).
    """
    return [
        {
            "index": index,
            "factor": None if emission.station is None else emission.station.factor,
            "party": None if emission.station is None else emission.station.party,
            # How this station's receiver was given (0.20.0; :func:`receiver_route`).
            "receiver_route": _artifact_route(emission.receiver),
            "receiver": jsonable(emission.receiver.as_payload()),
            "reduction": jsonable(emission.reduction.as_machine_record()),
            # Each block carries the run's decision on a completed run
            # (``evaluated_off_snap``, and on a moved block that rests its
            # cause and group; :mod:`certiqs_key.runs.direct_route`).
            "rows_adaptation": jsonable(
                emission.rows_adaptation
                if decision is None
                else annotate_snap_records(
                    emission.rows_adaptation, decision.station(index)
                )
            ),
        }
        for index, emission in enumerate(outcome.device_artifacts)
    ]


def preparation_record(outcome: Preparation | SliceRefusal) -> dict[str, Any]:
    """Transcribe one PREPARATION into a JSON-ready mapping.

    WHY THIS EXISTS, AND IT IS NOT THAT A RUN RECORD WAS MISSING A FUNCTION.
    :func:`certiqs_key.runs.pipeline.prepare` returns the snap records, the
    compiled declaration's public part, the acceptance alphabet, the receiver
    artefact and the reduction record, in seconds and without an oracle, and
    a consumer would otherwise assemble the JSON shape itself out of this
    module's helpers (:func:`public_and_source_tables`, :func:`receiver_payload`,
    :func:`reduction_payload`, :func:`jsonable`, :func:`jsonable_exact`),
    pinning itself to five names. They are public, and this is the shape, so that a
    consumer serialising a preparation calls ONE function and the engine owns what it
    emits.

    IT IS NOT A ``RunRecord``, and the type says so. A run record carries the
    configuration, the assumption manifest and the consumed contract versions
    because a run PRODUCED A KEY LENGTH and those are what make the number
    citable. A preparation produced no number: it has no solve, no acceptance
    set and no bundle, so a ``kind`` of ``run-record`` and a
    ``schema_version`` beside it would claim a record of something that did not
    happen. What comes back is a mapping, and a caller that wants an envelope
    around it writes its own.

    A REFUSED PREPARATION IS TRANSCRIBED, NOT SUPPRESSED, on the same grounds
    as a refused run: it carries the refusing stage, that module's own reason
    code, the rule it cites, the stage list up to the refusal, and the receiver
    artefact where the prologue got that far.

    ITS SHAPE MOVES WITH :data:`RECORD_SCHEMA_VERSION`, which is the version a
    caller wrapping this in an envelope of its own writes. It carries no
    ``schema_version`` key ITSELF for the reason above -- there is no record
    here to version, only a mapping -- but a consumer must not be
    pinned to a shape with no number at all. So: the keys below change only when that
    constant moves, ``tests/unit/test_runs_preparation_record.py`` holds the
    key set against it, and a change here is a change there.

    THE KEYS THAT ALSO EXIST ON A RUN RECORD ARE THE SAME KEYS: ``compiled``,
    ``stages``, ``channel_interface``, ``rows_adaptation`` and
    ``receiver_construction`` are what ``record_run`` emits under those names,
    built by the same functions. The one leaf that differs is
    ``receiver_construction.declared_povm``, which is exact here and float
    there, for the reason :func:`_declared_povm` gives.
    """
    stages = [entry.as_record() for entry in stage_list(outcome)]
    if isinstance(outcome, SliceRefusal):
        return {
            **(
                {"stations": _station_payloads(outcome)}
                if outcome.device_artifacts else {}
            ),
            "refused": True,
            "stage": str(outcome.stage),
            "reason": outcome.reason,
            "detail": outcome.detail,
            "rule": outcome.rule,
            "stages": stages,
            "receiver_artifact": (
                None
                if outcome.receiver_artifact is None
                else outcome.receiver_artifact.as_payload()
            ),
            "protocol_document": _protocol_document(outcome),
        }
    declaration = outcome.declaration
    artifact = outcome.receiver_artifact
    raw = outcome.raw_joint_distribution
    return {
        **(
            {"stations": _station_payloads(outcome)} if outcome.device_artifacts else {}
        ),
        "refused": False,
        "acceptance_alphabet": list(outcome.acceptance_alphabet),
        # the full tables, transcribed from the compiler's own
        # record, by the same function the run record uses.
        "compiled": public_and_source_tables(outcome),
        "sectors": {
            "labels": [str(label) for label in declaration.sectors.labels],
            "dimensions": list(declaration.sectors.dims),
            "block_kind": str(declaration.sectors.block_kind),
        },
        "alice_povm": {
            str(label): serialize_matrix(matrix)
            for label, matrix in declaration.alice_povm.items()
        },
        # PRESENT ON EVERY ROUTE, with ``route`` naming which.
        "receiver_construction": _receiver_surface(
            outcome, lambda: _declared_povm(outcome)
        ),
        "receiver_artifact": None if artifact is None else artifact.as_payload(),
        "reduction": (
            None if outcome.reduction_artifact is None else reduction_payload(outcome)
        ),
        "rows_adaptation": (
            None
            if outcome.rows_adaptation is None
            else jsonable(dict(outcome.rows_adaptation))
        ),
        "raw_joint_distribution": (
            None
            if raw is None
            else {f"{x}|{v}": str(value) for (x, v), value in raw.items()}
        ),
        # how A' enters the receiver, where the instance declared it.
        "channel_interface": (
            None
            if outcome.channel_interface is None
            else outcome.channel_interface.as_payload()
        ),
        "transmitter_artifact": jsonable_exact(
            outcome.specification.source.artifact.as_machine_record()
        ),
        "stages": stages,
        "declaration_artefact": (
            None
            if outcome.declaration_artefact is None
            else outcome.declaration_artefact.as_record()
        ),
        # The protocol document (0.21.0), the key the run record writes.
        "protocol_document": _protocol_document(outcome),
    }


def write_record(path: Path, record: RunRecord) -> None:
    """Write ``record`` as indented JSON. Never overwrites.

    The refusal to overwrite is :func:`certiqs_key.domain.write_bundle`'s rule, for
    the same reason: a run log that can silently replace a previous run's record
    is not a log.
    """
    if path.exists():
        raise FileExistsError(f"a run record already exists at {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
