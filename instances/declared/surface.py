"""The uniform instance surface a protocol document defines.

WHY THE SURFACE IS BUILT FROM DATA. Every instance exports the same names in the
run tier's types (``runs/surface.py``), so that a consumer drives a new
instance with no code of its own. A document is an instance written as data,
and this module turns the configuration-independent half of it into exactly
those objects: ``DESCRIPTOR`` (an ``InstanceDescriptor``), ``PARAMETERS`` (one
``ParameterSpec`` per table row), ``PRESETS`` and ``default_config``. The
configuration-dependent half -- ``preparation`` and ``runner``, which lower the
source, the stations and the public part to the modules' constructors
(:mod:`instances.declared.lowering`) -- shares one reader, ``_read``, as every
instance's does, so a configuration ``preparation`` accepts is
one a run accepts. Band-A documents are run on a finished specification;
optical stations through their device requests and a specification provider,
one station or several.

HOW ``default_config`` COMBINES OVERRIDES.
Instances combine a caller's ``model=`` or ``device=`` with their base
differently, so a document says which it means:

1. the base is the table defaults (``None`` left out), then
   ``run_defaults.model`` and ``run_defaults.device``;
2. with ``derived_timing: base_only`` the ``derived`` expressions are evaluated
   on the base;
3. with ``sections: replace`` a caller's section replaces the base section,
   with ``merge`` its keys are laid over it; every other override replaces its
   field;
4. with ``derived_timing: unless_supplied`` each derived target the caller's
   section did not supply is evaluated on the combined values (a supplied
   ``None`` counts as supplied, and means absent);
5. every ``None`` in a section is dropped and ``RunConfig.from_inputs`` runs.

A derived expression that reads a parameter the combined values do not hold
leaves its target alone: the run tier's key check then decides the missing
value with its own code.

WHAT IS REFUSED AT LOAD, and only that: a reference that does not resolve (a
parameter, a station, an alphabet), an expression that does not parse, a
switch over something that is not a choice, an ``applies_when`` that does not
resolve inside its table (``check_applicability``), a station mix, topology
or source-and-station pairing the run tier has no route for (a ``wcp_decoy``
source beside ``declared_povm`` stations). No value is judged: a default
outside its domain is the run tier's ``check_keys`` refusal when a
configuration carries it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Any

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.alpha_search import searching_runner
from certiqs_key.runs.config import AdvancedSolverSettings, RunConfig, SolverSettings
from certiqs_key.runs.errors import RunError, RunInputReason, RunInputValueError
from certiqs_key.runs.inputs import (
    attach_input_preparation,
    attach_protocol_document,
    prepare_config_probabilities,
    prepare_probabilities,
)
from certiqs_key.runs.pipeline import (
    ChannelInterfaceProvider,
    HonestProvider,
    MultiDeviceRequests,
    PreparationOutcome,
    SliceOutcome,
    StageObserver,
    prepare,
    run_slice,
)
from certiqs_key.runs.surface import (
    InstanceDescriptor,
    Kind,
    ParameterDomain,
    ParameterSpec,
    Preset,
    Quantity,
    Runner,
    Section,
    check_applicability,
    check_keys,
    solver_request,
    when,
)
from instances.common.declare import snap_settings
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.lowering import Lowered, lower
from instances.declared.model import (
    Acceptance,
    Announcements,
    ExplicitPartition,
    Expr,
    HonestLibrary,
    Key,
    Optical,
    ParameterRow,
    ParamRef,
    ProtocolDocument,
    RunDefaults,
    StaticDocument,
    Switch,
    WcpDecoy,
    WitnessBlocks,
)
from instances.declared.reader import ReadDocument, read, read_canonical, read_packaged
from instances.declared.rules import (
    Entry,
    build_alphabet,
    build_alphabets,
    check_table,
    placeholders,
)
from instances.declared.values import (
    Environment,
    ParameterAbsentError,
    check_references,
    constant,
    evaluate_exact,
    parse_expression,
    walk,
)

if TYPE_CHECKING:  # pragma: no cover - the oracle is wiring, not configuration
    from certiqs_key.receiver import ReceiverRequest
    from certiqs_key.solvers.oracles.protocol import LinearOracle

__all__ = ["DocumentSurface", "load", "load_canonical", "load_packaged"]


def load(source: object, *, static: bool = False) -> DocumentSurface:
    """Return the surface of a custom document (a path, text or a parsed object).

    ``static=True`` reads only the configuration-independent blocks, which is
    what a fragment carries.
    """
    return DocumentSurface(read(source, static=static))


def load_packaged(path: Path, *, static: bool = False) -> DocumentSurface:
    """Return the surface of a packaged template, ``instances/<id>/protocol.yaml``."""
    return DocumentSurface(read_packaged(path, static=static))


def load_canonical(
    canonical: Mapping[str, Any],
    conversions: Sequence[Mapping[str, Any]] = (),
    *,
    static: bool = False,
) -> DocumentSurface:
    """Return the surface of a stored custom document, as the worker rebuilds it."""
    return DocumentSurface(read_canonical(canonical, conversions, static=static))


class DocumentSurface:
    """One document's instance surface."""

    def __init__(self, document: ReadDocument) -> None:
        """Build the descriptor, the table and the presets; check every reference."""
        model = document.model
        identity = model.identity
        #: The document as read: canonical tree, conversions, digest, model.
        self.document = document
        #: ``identity.record_label``, defaulted to ``declared.<id>``.
        self.record_label = identity.record_label or f"declared.{identity.id}"
        self.DESCRIPTOR = InstanceDescriptor(
            id=identity.id,
            title=identity.title,
            summary=identity.summary,
            readme=identity.readme,
        )
        #: Each station's port labels in port-map order (none on a declared POVM).
        self._ports: dict[str, tuple[str, ...]] = {
            station.id: tuple(
                port.label for port in getattr(station.measurement, "ports", ())
            )
            for station in model.stations
        }
        rows = model.parameters.table
        self._check_names(rows)
        self.PARAMETERS: tuple[ParameterSpec, ...] = tuple(
            self._parameter(row, pointer("parameters", "table", index))
            for index, row in enumerate(rows)
        )
        #: Each parameter's kind, by name: what the value language reads.
        self.kinds: dict[str, Kind] = {spec.name: spec.kind for spec in self.PARAMETERS}
        self._specs = {spec.name: spec for spec in self.PARAMETERS}
        self._check_applies_when(rows)
        self.PRESETS: tuple[Preset, ...] = tuple(
            Preset(
                name=preset.name,
                note=preset.note,
                model=self._section_values(
                    preset.model, Section.MODEL, pointer("presets", index, "model")
                ),
                device=self._section_values(
                    preset.device, Section.DEVICE, pointer("presets", index, "device")
                ),
            )
            for index, preset in enumerate(model.presets)
        )
        parameters = model.parameters
        #: Whether an absent model or device key is refused or read as its default.
        self.model_absent = parameters.model_absent
        self.device_absent = parameters.device_absent
        #: The order of the two ``check_keys`` calls.
        self.check_order: tuple[Section, Section] = (
            Section(parameters.check_order[0]),
            Section(parameters.check_order[1]),
        )
        #: The device rows whose kind is not ``choice``.
        self.numeric_device_fields: tuple[str, ...] = tuple(
            spec.name
            for spec in self.PARAMETERS
            if spec.section is Section.DEVICE and spec.kind is not Kind.CHOICE
        )
        self._check_preparation(model)
        self._defaults = model.run_defaults
        self._run = _RunFields(model.run_defaults)
        self._base = self._base_sections(model.run_defaults)
        self._derived = {
            target: (
                parse_expression(text, pointer("run_defaults", "derived", target))
                if isinstance(text, str)
                else None,
                text,
            )
            for target, text in model.run_defaults.derived.items()
        }
        self._check_derived()
        if isinstance(model, ProtocolDocument):
            self._check_document(model)

    # -- the document ------------------------------------------------------

    @property
    def digest(self) -> str:
        """The digest of the canonical tree."""
        return self.document.digest

    @property
    def canonical(self) -> dict[str, Any]:
        """The canonical tree, which is what is computed on and recorded."""
        return self.document.canonical

    @property
    def conversions(self) -> tuple[Mapping[str, Any], ...]:
        """The canonicalisation records."""
        return self.document.conversions

    @property
    def packaged(self) -> bool:
        """Whether this is a packaged template."""
        return self.document.packaged

    # -- default_config ----------------------------------------------------

    def default_config(self, **overrides: Any) -> RunConfig:
        """Return a runnable configuration, with overrides combined as above."""
        sections: dict[str, dict[str, Any]] = {
            name: dict(values) for name, values in self._base.items()
        }
        timing = self._defaults.derived_timing
        if timing == "base_only":
            self._derive(sections, supplied=None)
        supplied: dict[str, set[str]] = {}
        for name in ("model", "device"):
            if name in overrides:
                caller = dict(overrides.pop(name))
                supplied[name] = set(caller)
                sections[name] = (
                    caller
                    if self._defaults.sections == "replace"
                    else {**sections[name], **caller}
                )
        if timing == "unless_supplied":
            self._derive(sections, supplied=supplied)
        # The document's own conversion records come first, every call afresh,
        # then the caller's (appended on every load).
        records = list(self.conversions)
        records += [
            record
            for record in overrides.pop("input_preparation", ())
            if record not in records
        ]
        fields: dict[str, Any] = {
            **self._run.fields(),
            **{
                name: {key: value for key, value in values.items() if value is not None}
                for name, values in sections.items()
            },
            **overrides,
        }
        if records:
            fields["input_preparation"] = tuple(records)
        return RunConfig.from_inputs(
            numeric_device_fields=self.numeric_device_fields, **fields
        )

    def _derive(
        self,
        sections: dict[str, dict[str, Any]],
        *,
        supplied: Mapping[str, set[str]] | None,
    ) -> None:
        for target, (expression, text) in self._derived.items():
            section = str(self._specs[target].section)
            if supplied is not None and target in supplied.get(section, set()):
                continue
            path = pointer("run_defaults", "derived", target)
            environment = Environment(
                self.kinds, {**sections["model"], **sections["device"]}
            )
            try:
                value = (
                    Fraction(text)
                    if expression is None
                    else expression.evaluate(environment, path)
                )
            except ParameterAbsentError:
                continue
            sections[section][target] = value

    def _base_sections(self, defaults: RunDefaults) -> dict[str, dict[str, Any]]:
        base: dict[str, dict[str, Any]] = {
            str(section): {
                spec.name: spec.default
                for spec in self.PARAMETERS
                if spec.section is section and spec.default is not None
            }
            for section in (Section.MODEL, Section.DEVICE)
        }
        base["model"].update(
            self._section_values(
                defaults.model, Section.MODEL, pointer("run_defaults", "model")
            )
        )
        base["device"].update(
            self._section_values(
                defaults.device, Section.DEVICE, pointer("run_defaults", "device")
            )
        )
        return base

    # -- preparation and runner -------------------------------------------

    def _whole(self) -> ProtocolDocument:
        model = self.document.model
        if not isinstance(model, ProtocolDocument):
            raise DocumentError(
                "a static fragment carries no source, stations or public part, "
                "so it has nothing to prepare or run",
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
            )
        return model

    def _configured(self, config: RunConfig) -> RunConfig:
        """Run steps 1-3 of the reader: the snap, the key checks, the preparations."""
        model = self._whole()
        snap = model.snap
        config = prepare_config_probabilities(
            config,
            () if snap is None else tuple(tuple(group) for group in snap.groups),
            lattice_exponent=40 if snap is None else snap.lattice_exponent,
            numeric_device_fields=self.numeric_device_fields,
        )
        for section in self.check_order:
            absent = (
                self.model_absent if section is Section.MODEL else self.device_absent
            )
            check_keys(
                section,
                config.model if section is Section.MODEL else config.device,
                self.PARAMETERS,
                self.DESCRIPTOR.id,
                complete_for=config if absent == "refuse" else None,
            )
        for index, preparation in enumerate(model.preparations):
            environment = self._environment(config)
            family = [
                evaluate_exact(
                    entry, environment, pointer("preparations", index, "family", f)
                )
                for f, entry in enumerate(preparation.family)
            ]
            prepared = prepare_probabilities(
                family,
                tolerance=config.declared_tolerance,
                lattice_exponent=preparation.lattice_exponent,
                site=preparation.site,
            )
            sections: dict[str, dict[str, Any]] = {
                "model": dict(config.model),
                "device": dict(config.device),
            }
            for name, position in preparation.rebind.items():
                sections[str(self._specs[name].section)][name] = prepared.values[
                    position
                ]
            config = replace(
                config,
                model=sections["model"],
                device=sections["device"],
                input_preparation=(*config.input_preparation, prepared.record),
            )
        return config

    def _environment(self, config: RunConfig) -> Environment:
        """Return the values a node reads: table defaults, then the configuration."""
        values: dict[str, object] = {
            spec.name: spec.default
            for spec in self.PARAMETERS
            if spec.default is not None
        }
        values.update(config.model)
        values.update(config.device)
        return Environment(self.kinds, values)

    def resolve(self, config: RunConfig) -> dict[str, object]:
        """Return the parameter values a run of ``config`` reads.

        After the snap groups, the key checks and the preparations, with table
        defaults for absent keys: the values every node of the document is
        evaluated on.
        """
        return dict(self._environment(self._configured(config)).values)

    def _read(self, config: RunConfig) -> tuple[RunConfig, Lowered]:
        """Read and lower a configuration: the reader both entry points share.

        The records the lowering adds -- a ``wcp_decoy`` source's preparation
        record, the conversions of the receiver's float routes -- are appended
        to the configuration's ``input_preparation``, after the snap and the
        preparations, as decoy BB84 appends its source record.
        """
        config = self._configured(config)
        lowered = lower(
            self._whole(),
            self._environment(config),
            record_label=self.record_label,
            document_id=self.DESCRIPTOR.id,
            declared_tolerance=config.declared_tolerance,
            model_section=config.model,
            snap=snap_settings(config),
            # THE WORK BOUNDS ARE A CUSTOM DOCUMENT'S : a packaged
            # template is the repository's own and is bounded by its parameter
            # domains.
            work_bounds=not self.packaged,
        )
        if lowered.input_preparation:
            config = replace(
                config,
                input_preparation=(
                    *config.input_preparation,
                    *lowered.input_preparation,
                ),
            )
        return config, lowered

    def receiver_requests(self, config: RunConfig) -> tuple[ReceiverRequest, ...]:
        """Return the receiver requests ``preparation(config)`` would construct.

        The lowering alone, which builds each optical station's request and
        constructs nothing: what a cost estimate reads before a preparation
        (``runs/facade/estimate.py``). A Band-A document has none. Raises what
        the lowering raises.
        """
        _config, lowered = self._read(config)
        device = lowered.device
        if device is None:
            return ()
        if isinstance(device, MultiDeviceRequests):
            return tuple(station.receiver_request for station in device.devices)
        return (device.receiver_request,)

    @property
    def receiver_parameters(self) -> tuple[str, ...]:
        """The parameters an optical station's photon numbers read, in order.

        Each name a station's ``photon_cutoff`` or ``exact_window``
        reads (a ``{param}`` or a name in an ``{expr}``): what the cost
        estimate's receiver terms depend on (``runs/facade/estimate.py``). A
        source cutoff is not among them. Empty for a Band-A or static document.
        """
        model = self.document.model
        if not isinstance(model, ProtocolDocument):
            return ()
        nodes: list[object] = []
        for station in model.stations:
            measurement = station.measurement
            if not isinstance(measurement, Optical):
                continue
            nodes += [measurement.photon_cutoff, measurement.exact_window]
        names: list[str] = []
        for node in nodes:
            for item, where in walk(node, ""):
                if isinstance(item, ParamRef):
                    names.append(item.param)
                elif isinstance(item, Expr):
                    expression = parse_expression(item.expr, where)
                    names += [name for name, _port in expression.names()]
        return tuple(dict.fromkeys(names))

    def _record(self, lowered: Lowered) -> dict[str, Any]:
        return lowered.record(
            document_id=self.DESCRIPTOR.id,
            packaged=self.packaged,
            digest=self.digest,
            canonical=self.canonical,
            conversions=self.conversions,
        )

    @property
    def channel_interface(self) -> ChannelInterfaceProvider | None:
        """The channel-interface builder the document names, or ``None``.

        READ OFF THE DOCUMENT, NEVER LOWERED, so that attribute access cannot
        raise (the MCP server reads it on any document): the variant is not switchable,
        ``none`` and a static fragment give ``None``, and whether the builder
        fits the declared stations is the lowering's check at ``preparation``.
        """
        from instances.common import channel

        model = self.document.model
        node = getattr(model, "channel_interface", None)
        variant = "none" if node is None else node.variant
        if variant == "none":
            return None
        builder: ChannelInterfaceProvider = getattr(channel, variant)
        return builder

    @property
    def DEFAULT_HONEST_MODEL_NOTE(self) -> dict[str, Any]:
        """The honest-model note a run records when the document's model is used.

        The note of the lowering at ``default_config()``. Attribute access never
        raises: where that configuration does not lower (a refused default, a
        refused source, a static fragment), the note says which document's
        honest model it would be and that it was not built, and the refusal
        itself is ``preparation``'s to report.
        """
        try:
            return dict(self._read(self.default_config())[1].note)
        except (RunError, MalformedInputError) as failure:
            return {
                "instance": self.record_label,
                "model": "the protocol document's honest model, not built at the "
                "default configuration",
                "module": "instances.declared",
                "overridden": False,
                "not_built": str(getattr(failure, "reason", type(failure).__name__)),
            }

    def preparation(self, config: RunConfig) -> PreparationOutcome:
        """Run everything the document's protocol can run without an oracle."""
        config, lowered = self._read(config)
        outcome = prepare(
            config,
            **lowered.route(),
            raw_joint_provider=lowered.raw,
            channel_interface_provider=lowered.channel_interface,
        )
        return attach_protocol_document(
            attach_input_preparation(outcome, config), self._record(lowered)
        )

    def runner(
        self,
        oracle: LinearOracle,
        directory: Path,
        *,
        created_by: str,
        observer: StageObserver | None = None,
        honest_provider: HonestProvider | None = None,
        honest_model_note: dict[str, Any] | None = None,
    ) -> Runner:
        """Return the callable a sweep drives, with every instance's signature.

        ``honest_provider`` is an override: it replaces the document's honest
        model and suppresses its raw table, as every runner does.
        ``honest_model_note`` is recorded verbatim; without one the record
        carries the document's own note, marked ``overridden`` when a provider
        replaced its model.

        A configuration with ``alpha_search`` set runs the run tier's outer
        alpha search over this one-alpha run
        (:func:`~certiqs_key.runs.alpha_search.searching_runner`).
        """

        def run(config: RunConfig, bundle: Path) -> SliceOutcome:
            config, lowered = self._read(config)
            note = honest_model_note
            if note is None:
                # THE LIVE NOTE, not a copy: a library model may extend it
                # while the run is under way (the SPDC Gram preparation).
                note = lowered.note
                note["overridden"] = honest_provider is not None
            outcome = run_slice(
                **lowered.route(),
                honest_provider=(
                    honest_provider if honest_provider is not None else lowered.honest
                ),
                raw_joint_provider=None if honest_provider is not None else lowered.raw,
                rounds=config.rounds,
                completeness_budget=config.completeness_budget,
                parameters=config.parameters,
                eps_auth=config.eps_auth,
                k_auth=config.k_auth,
                oracle=oracle,
                directory=bundle,
                declared_tolerance=config.declared_tolerance,
                created_by=created_by,
                alpha=config.alpha,
                constrained=config.constrained,
                endpoint_rule=config.endpoint_rule,
                tail_evaluation=config.tail_evaluation,
                channel_interface_provider=lowered.channel_interface,
                request=solver_request(config.solver),
                observer=observer,
                run_id=config.digest(),
                honest_model_note=note,
                # meat-core/req:unreachable-acceptance-set: the honest
                # statistics are supplied where a provider replaced the
                # document's model or the document gives them as data (a
                # table or an envelope, which has no library context); the
                # caller's constraint entries are the document's explicit
                # ones, each flagged as declared.
                honest_supplied=(
                    honest_provider is not None or lowered.honest_context is None
                ),
                caller_constraint_entries=sum(
                    item.kind == "constraint_entry" for item in lowered.user_declared
                ),
                statistics_check=config.statistics_check,
                min_model_pass_probability=config.min_model_pass_probability,
            )
            return attach_protocol_document(
                attach_input_preparation(outcome, config), self._record(lowered)
            )

        return searching_runner(run, directory)

    # -- the table ---------------------------------------------------------

    def _check_names(self, rows: Sequence[ParameterRow]) -> None:
        seen: set[str] = set()
        for index, row in enumerate(rows):
            if row.name in seen:
                raise DocumentError(
                    f"the table declares {row.name!r} twice",
                    reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                    path=pointer("parameters", "table", index, "name"),
                )
            seen.add(row.name)

    def _station(self, station: str, path: str) -> tuple[str, ...]:
        if station not in self._ports:
            raise DocumentError(
                f"{station!r} names no station ({sorted(self._ports)})",
                reason=DocumentReason.STATION_REFERENCE_UNKNOWN,
                path=path,
            )
        return self._ports[station]

    def _parameter(self, row: ParameterRow, path: str) -> ParameterSpec:
        kind = Kind(row.kind)
        labels: tuple[str, ...] = ()
        if kind is Kind.PER_PORT_FRACTION:
            if row.per_port_of is None:
                raise DocumentError(
                    "a per_port_fraction parameter names the station whose ports "
                    "key it (per_port_of)",
                    reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                    path=path,
                )
            labels = self._station(row.per_port_of, path + pointer("per_port_of"))
            if not labels:
                raise DocumentError(
                    f"the station {row.per_port_of!r} declares no ports",
                    reason=DocumentReason.STATION_REFERENCE_UNKNOWN,
                    path=path + pointer("per_port_of"),
                )
        elif row.per_port_of is not None:
            raise DocumentError(
                "per_port_of is for a per_port_fraction parameter",
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path=path + pointer("per_port_of"),
            )
        if row.station is not None:
            self._station(row.station, path + pointer("station"))
        default = (
            None
            if row.default is None
            else _static(row.default, kind, labels, path + pointer("default"))
        )
        domain = row.domain
        return ParameterSpec(
            name=row.name,
            section=Section(row.section),
            kind=kind,
            quantity=Quantity(row.quantity),
            unit=row.unit,
            default=default,
            domain=ParameterDomain(
                form=domain.form,
                lower=_bound(domain.lower, path + pointer("domain", "lower")),
                upper=_bound(domain.upper, path + pointer("domain", "upper")),
                lower_open=domain.lower_open,
                upper_open=domain.upper_open,
                options=tuple(
                    (option.value, option.meaning) for option in domain.options
                ),
            ),
            snapped=row.snapped,
            meaning=row.meaning,
            per_port_labels=labels,
            applies_when=None,
            station=row.station,
        )

    def _check_applies_when(self, rows: Sequence[ParameterRow]) -> None:
        """Resolve each ``applies_when`` in the table, then let the run tier decide."""
        specs = list(self.PARAMETERS)
        for index, row in enumerate(rows):
            if row.applies_when is None:
                continue
            path = pointer("parameters", "table", index, "applies_when")
            conditions: dict[str, tuple[Any, ...]] = {}
            for name, values in row.applies_when.items():
                if name not in self._specs:
                    raise DocumentError(
                        f"applies_when names {name!r}, which is not a parameter of "
                        "this table",
                        reason=DocumentReason.UNKNOWN_PARAMETER_REFERENCE,
                        path=path + pointer(name),
                    )
                other = self._specs[name]
                conditions[name] = tuple(
                    _static(
                        value, other.kind, other.per_port_labels, path + pointer(name)
                    )
                    if other.kind is not Kind.PER_PORT_FRACTION
                    else value
                    for value in values
                )
            specs[index] = replace(specs[index], applies_when=when(conditions))
        self.PARAMETERS = tuple(specs)
        self._specs = {spec.name: spec for spec in self.PARAMETERS}
        try:
            check_applicability(self.PARAMETERS, self.DESCRIPTOR.id)
        except ValueError as failure:
            raise DocumentError(
                str(failure),
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path=pointer("parameters", "table"),
            ) from failure

    def _section_values(
        self, values: Mapping[str, Any], section: Section, path: str
    ) -> dict[str, Any]:
        """Read a section's static values by each parameter's kind."""
        result: dict[str, Any] = {}
        for name, value in values.items():
            spec = self._specs.get(name)
            if spec is None or spec.section is not section:
                raise DocumentError(
                    f"{name!r} is not a {section} parameter of this table",
                    reason=DocumentReason.UNKNOWN_PARAMETER_REFERENCE,
                    path=path + pointer(name),
                )
            result[name] = _static(
                value, spec.kind, spec.per_port_labels, path + pointer(name)
            )
        return result

    # -- preparation and derived defaults ----------------------------------

    def _numeric(self, name: str, path: str, *, section: Section | None = None) -> None:
        spec = self._specs.get(name)
        if spec is None or (section is not None and spec.section is not section):
            where = "" if section is None else f" {section}"
            raise DocumentError(
                f"{name!r} is not a{where} parameter of this table",
                reason=DocumentReason.UNKNOWN_PARAMETER_REFERENCE,
                path=path,
            )
        if spec.kind in (Kind.CHOICE, Kind.PER_PORT_FRACTION):
            raise DocumentError(
                f"{name} is a {spec.kind} parameter; a single number is needed here",
                reason=DocumentReason.VALUE_KIND_MISMATCH,
                path=path,
            )

    def _check_preparation(self, model: ProtocolDocument | StaticDocument) -> None:
        if model.snap is not None:
            for g, group in enumerate(model.snap.groups):
                for n, name in enumerate(group):
                    self._numeric(
                        name, pointer("snap", "groups", g, n), section=Section.DEVICE
                    )
        for p, preparation in enumerate(model.preparations):
            for f, entry in enumerate(preparation.family):
                if isinstance(entry, str):
                    path = pointer("preparations", p, "family", f)
                    parse_expression(entry, path).check(self.kinds, path)
            for name, index in preparation.rebind.items():
                path = pointer("preparations", p, "rebind", name)
                self._numeric(name, path)
                if not 0 <= index < len(preparation.family):
                    raise DocumentError(
                        f"index {index} is outside the family of "
                        f"{len(preparation.family)}",
                        reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                        path=path,
                    )

    def _check_derived(self) -> None:
        for target, (expression, _text) in self._derived.items():
            path = pointer("run_defaults", "derived", target)
            self._numeric(target, path)
            if expression is not None:
                expression.check(self.kinds, path)

    # -- the whole document ------------------------------------------------

    def _check_document(self, model: ProtocolDocument) -> None:
        """Refuse what no lowering could read: references, alphabets, topology."""
        check_references(
            model,
            self.kinds,
            options={
                spec.name: tuple(value for value, _meaning in spec.domain.options)
                for spec in self.PARAMETERS
                if spec.kind is Kind.CHOICE
            },
        )
        build_alphabets(model.alphabets)
        self._check_tables(model)
        ids = [station.id for station in model.stations]
        repeated = sorted({name for name in ids if ids.count(name) > 1})
        if repeated:
            raise DocumentError(
                f"station ids are distinct; {repeated} repeat",
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path="/stations",
            )
        kinds = {station.measurement.kind for station in model.stations}
        if len(kinds) > 1:
            raise DocumentError(
                "a document's stations are all declared_povm or all optical; the "
                "run tier has no route for a mix (MultiDeviceRequests takes "
                "DeviceRequests only)",
                reason=DocumentReason.STATION_KINDS_MIXED,
                path="/stations",
            )
        if isinstance(model.source, WcpDecoy) and kinds == {"declared_povm"}:
            raise DocumentError(
                "a wcp_decoy source needs optical stations: the declared_povm "
                "(Band-A) lowering docks no source segment, so the decoy "
                "source's links would reach the compiler on a chain that does "
                "not carry them; declare the receivers as optical stations",
                reason=DocumentReason.WCP_DECOY_NEEDS_OPTICAL_STATIONS,
                path="/stations",
            )
        if isinstance(model.source, WcpDecoy) and len(model.stations) > 1:
            raise DocumentError(
                f"a wcp_decoy source needs exactly one optical station, not "
                f"{len(model.stations)}: only the one-station optical lowering "
                "docks the decoy source's segment, the several-station lowering "
                "builds each station's chain without it, so the source's links "
                "would reach the compiler on chains that do not carry them; "
                "declare one optical receiver",
                reason=DocumentReason.WCP_DECOY_NEEDS_ONE_OPTICAL_STATION,
                path="/stations",
            )
        for node, path in _cases(model.honest, "/honest"):
            if isinstance(node, HonestLibrary) and node.station is not None:
                self._station(node.station, path + pointer("station"))
        self._check_topology(model)
        if isinstance(model.source, WcpDecoy):
            _check_letter_label(model.source.letter_label)

    def _check_tables(self, model: ProtocolDocument) -> None:
        """Check every rule table's references, in every switch case, at load.

        Each table binds its alphabet's variables. An alphabet the document
        writes is built here and its components checked; one the engine
        emits (a readout, a station's outcomes, a derived message alphabet)
        is checked by name now and by component at expansion.
        """
        named = model.alphabets
        public = model.public
        classes: dict[str, tuple[Entry, ...] | None] = {}
        if public.announcements is not None:
            cases = _cases(public.announcements, "/public/announcements")
            for node, where in cases:
                assert isinstance(node, Announcements)
                check_table(
                    "announce_alice", node.alice.map, {"x": None}, where + "/alice/map"
                )
                check_table(
                    "announce_bob", node.bob.map, {"v": None}, where + "/bob/map"
                )
                alice = build_alphabet(
                    node.alice.alphabet, named, where + "/alice/alphabet"
                )
                bob = build_alphabet(node.bob.alphabet, named, where + "/bob/alphabet")
                # One case: its classes are checked here; several: each
                # case's classes are the expansion's to check.
                classes["A"] = alice if len(cases) == 1 else None
                classes["B"] = bob if len(cases) == 1 else None
        else:
            assert public.transcript is not None
            ids = [message.id for message in public.transcript.messages]
            for index, name in enumerate(ids):
                if name in ("r", "o") or ids.index(name) != index:
                    raise DocumentError(
                        f"a message id names the message in later rules, so it is "
                        f"distinct and neither 'r' nor 'o' (the readout); {name!r} "
                        "is not",
                        reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                        path=pointer("public", "transcript", "messages", index, "id"),
                    )
            for index, message in enumerate(public.transcript.messages):
                where = pointer("public", "transcript", "messages", index)
                check_table(
                    f"message {message.id}",
                    message.table,
                    {"r": None, **classes},
                    where + pointer("table"),
                )
                classes[message.id] = (
                    None
                    if message.alphabet == "derived"
                    else build_alphabet(
                        message.alphabet, named, where + pointer("alphabet")
                    )
                )
        check_table("sifting", public.sifting, classes, "/public/sifting")
        for node, path in _cases(public.key, "/public/key"):
            assert isinstance(node, Key)
            check_table(
                "key", node.rule, {"o": None, **classes}, path + pointer("rule")
            )
        for node, path in _cases(public.acceptance, "/public/acceptance"):
            assert isinstance(node, Acceptance)
            check_table("acceptance", node.map, classes, path + pointer("map"))
        for index, station in enumerate(model.stations):
            where = pointer("stations", index)
            if isinstance(station.measurement, Optical):
                check_table(
                    "coarse_graining",
                    station.measurement.coarse_graining.map,
                    {"count": None, "port": None, "fired": None},
                    where + "/measurement/coarse_graining/map",
                )
            if station.choice_weighting is not None:
                check_table(
                    "setting_of",
                    station.choice_weighting.setting_of,
                    {"v": None},
                    where + "/choice_weighting/setting_of",
                )

    def _check_topology(self, model: ProtocolDocument) -> None:
        """Refuse three or more stations unless the restrictions below hold."""
        stations = model.stations
        partitions = [node for node, _ in _cases(model.public.partition, "")]
        if "factor_projection" in partitions and sorted(
            station.party for station in stations
        ) != ["A", "B"]:
            raise DocumentError(
                "factor_projection needs exactly one station per party",
                reason=DocumentReason.UNSUPPORTED_TOPOLOGY,
                path="/public/partition",
            )
        if len(stations) < 3:
            return
        if not all(isinstance(node, ExplicitPartition) for node in partitions):
            raise DocumentError(
                "with three or more stations the partition is written as rules",
                reason=DocumentReason.UNSUPPORTED_TOPOLOGY,
                path="/public/partition",
            )
        witness = (
            "auto"
            if model.constraints is None
            else model.constraints.feasibility_witness
        )
        if any(
            not (node == "none" or isinstance(node, WitnessBlocks))
            for node, _ in _cases(witness, "")
        ):
            raise DocumentError(
                "with three or more stations the feasibility witness is none or "
                "explicit; the library's is a two-factor construction",
                reason=DocumentReason.UNSUPPORTED_TOPOLOGY,
                path="/constraints/feasibility_witness",
            )
        if (
            model.channel_interface is not None
            and model.channel_interface.variant != "none"
        ):
            raise DocumentError(
                "with three or more stations the channel interface is none; the "
                "bipartite interface has two arms",
                reason=DocumentReason.UNSUPPORTED_TOPOLOGY,
                path="/channel_interface",
            )


class _RunFields:
    """The run fields of ``run_defaults``, evaluated once at load.

    The numbers are document constants: an expression here may not read a
    parameter. The run tier's own objects (``KeyLengthParameters``,
    ``SolverSettings``) are built at each ``default_config`` call, so that
    their checks run where every other configuration check runs.
    """

    def __init__(self, defaults: RunDefaults) -> None:
        def at(*parts: str) -> str:
            return pointer("run_defaults", *parts)

        self.rounds = _constant_int(defaults.rounds, at("rounds"))
        self.completeness_budget = _constant(
            defaults.completeness_budget, at("completeness_budget")
        )
        self.declared_tolerance = _binary64(
            defaults.declared_tolerance, at("declared_tolerance")
        )
        key = defaults.parameters
        self.alpha = _binary64(key.alpha, at("parameters", "alpha"))
        self.eps_pa = _binary64(key.eps_pa, at("parameters", "eps_pa"))
        self.eps_ev = _binary64(key.eps_ev, at("parameters", "eps_ev"))
        self.lambda_ec = _constant_int(key.lambda_ec, at("parameters", "lambda_ec"))
        self.extra: dict[str, Any] = {}
        if key.eps_auth is not None:
            self.extra["eps_auth"] = _binary64(
                key.eps_auth, at("parameters", "eps_auth")
            )
        if key.k_auth is not None:
            self.extra["k_auth"] = _constant_int(key.k_auth, at("parameters", "k_auth"))
        if defaults.alpha is not None:
            self.extra["alpha"] = _binary64(defaults.alpha, at("alpha"))
        if defaults.constrained is not None:
            self.extra["constrained"] = tuple(defaults.constrained)
        if defaults.endpoint_rule is not None:
            self.extra["endpoint_rule"] = defaults.endpoint_rule
        if defaults.tail_evaluation is not None:
            self.extra["tail_evaluation"] = defaults.tail_evaluation
        self.solver: dict[str, Any] | None = None
        if defaults.solver is not None:
            solver = defaults.solver
            self.solver = {
                "max_iterations": None
                if solver.max_iterations is None
                else _constant_int(
                    solver.max_iterations, at("solver", "max_iterations")
                ),
                "method": solver.method,
                "budget_seconds": None
                if solver.budget_seconds is None
                else _binary64(solver.budget_seconds, at("solver", "budget_seconds")),
            }
            expert = solver.advanced
            if expert is not None:
                self.solver["advanced"] = {
                    "method": expert.method,
                    "oracle": expert.oracle,
                    "gap_tolerance": None
                    if expert.gap_tolerance is None
                    else _binary64(
                        expert.gap_tolerance,
                        at("solver", "advanced", "gap_tolerance"),
                    ),
                    "certified_evaluation": expert.certified_evaluation,
                }

    def fields(self) -> dict[str, Any]:
        """Return the base fields of ``RunConfig.from_inputs``."""
        fields: dict[str, Any] = {
            "rounds": self.rounds,
            "completeness_budget": self.completeness_budget,
            "parameters": KeyLengthParameters(
                alpha=self.alpha,
                eps_pa=self.eps_pa,
                eps_ev=self.eps_ev,
                lambda_ec=self.lambda_ec,
            ),
            "declared_tolerance": self.declared_tolerance,
            **self.extra,
        }
        if self.solver is not None:
            solver = dict(self.solver)
            if solver.get("advanced") is not None:
                solver["advanced"] = AdvancedSolverSettings(**solver["advanced"])
            fields["solver"] = SolverSettings(**solver)
        return fields


_constant = constant


def _constant_int(node: int | str, path: str) -> int:
    value = constant(node, path)
    if value.denominator != 1:
        raise DocumentError(
            f"an integer is required here; {node!r} is {value}",
            reason=DocumentReason.EXPRESSION_NOT_INTEGRAL,
            path=path,
        )
    return int(value)


def _binary64(node: int | str, path: str) -> float:
    """Return a binary64 field: the value its literal denotes, correctly rounded."""
    value = _constant(node, path)
    try:
        return float(value)
    except OverflowError:
        raise RunInputValueError(
            f"{path}: {node!r} is outside the binary64 range",
            reason=RunInputReason.OUTSIDE_BINARY64,
        ) from None


def _bound(node: int | str | None, path: str) -> Fraction | None:
    return None if node is None else _constant(node, path)


def _static(
    value: object, kind: Kind, labels: Sequence[str], path: str
) -> Fraction | str | dict[str, Fraction]:
    """Read a static parameter value by its parameter's kind.

    A ``choice`` value is a name; a ``fraction`` or ``int`` value is a
    ``Fraction`` however written; a per-port
    value is a mapping of ``Fraction``s in port-map order, and a single number
    there means that number on every port.
    """
    if kind is Kind.CHOICE:
        if not isinstance(value, str):
            raise DocumentError(
                f"a choice value is a name; got {value!r}",
                reason=DocumentReason.VALUE_KIND_MISMATCH,
                path=path,
            )
        return value
    if kind is Kind.PER_PORT_FRACTION:
        if not isinstance(value, Mapping):
            return dict.fromkeys(labels, _exact(value, path))
        mapping = {
            str(port): _exact(entry, path + pointer(str(port)))
            for port, entry in value.items()
        }
        if set(mapping) == set(labels):
            return {label: mapping[label] for label in labels}
        return mapping
    if isinstance(value, Mapping):
        raise DocumentError(
            f"a {kind} value is one number, not a mapping",
            reason=DocumentReason.VALUE_KIND_MISMATCH,
            path=path,
        )
    return _exact(value, path)


def _exact(value: object, path: str) -> Fraction:
    """Read a static number: an integer, a number string or ``{expr}``, no name."""
    if isinstance(value, Expr):
        return constant(value.expr, path + pointer("expr"))
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise DocumentError(
            f"a number is an integer, a number string or {{expr}}; got {value!r}",
            reason=DocumentReason.VALUE_KIND_MISMATCH,
            path=path,
        )
    return constant(value, path)


def _check_letter_label(template: str) -> None:
    """Refuse a WCP letter label that cannot name its letters apart, at load.

    A letter is a round, an intensity and a polarisation (``def:wcp-model``
    (W2)); the label reads only those, and names the round and the
    polarisation, without which a generation and a test letter, or two
    polarisations, would share a label. One that omits the intensity can
    still collide across intensities, which the transmitter's model refuses.
    """
    from instances.declared.wcp import LETTER_FIELDS

    names = set(placeholders(template))
    unknown = sorted(names - set(LETTER_FIELDS))
    if unknown:
        raise DocumentError(
            f"the letter label {template!r} reads {unknown}; it may read "
            f"{list(LETTER_FIELDS)}",
            reason=DocumentReason.RULE_REFERENCE_UNKNOWN,
            path="/source/letter_label",
        )
    missing = [name for name in ("round", "polarisation") if name not in names]
    if missing:
        raise DocumentError(
            f"the letter label {template!r} does not read {missing}, so two "
            "letters would share a label",
            reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
            path="/source/letter_label",
        )


def _cases(node: object, path: str) -> list[tuple[object, str]]:
    """Return every node a switch may choose (the node itself if it is none)."""
    if not isinstance(node, Switch):
        return [(node, path)]
    found: list[tuple[object, str]] = []
    for case, branch in node.cases.items():
        found += _cases(branch, path + pointer("cases", case))
    if node.default is not None:
        found += _cases(node.default, path + pointer("default"))
    return found
