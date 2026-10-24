"""The shape every instance exports, defined ONCE and never per instance.

Nothing a consumer shows should be hardcoded to specific instances: protocols
and POVM visualizations all derive fully mechanistically from the relevant
parameters of the instance / run. For this tier that is THE UNIFORMITY RULE: one shape
for every instance -- the same exports, the same types, the same record keys -- so that
a consumer drives a new instance with no code of its own.

WHY THE TYPES ARE HERE AND THE VALUES ARE THERE
===============================================
An instance's parameters are its own: what they are called, what they mean,
what they default to and which of them are snapped. What they are PRESENTED AS
is not, and two instances that each invented a parameter table would give a
consumer two tables to learn. So the descriptor, the parameter spec, the
domain forms and the ``quantity`` vocabulary live in ``runs/`` -- which every
instance may import (spec/architecture.md 3.5) -- and no instance defines any
of them.

THE PROBLEM THIS SOLVES. Validating an instance's keys against frozen sets
and hand-written checks leaves the set of keys, their types, their domains and
their defaults existing only as code and docstrings, so every caller re-types
that list and it drifts. The instance's own key checks READ the table below,
so the table cannot be wrong about the instance that carries it.

WHAT IS NOT HERE, AND DELIBERATELY. Labels, units for display, slider ranges,
presets for a user interface, ordering for a form: presentation is the
consumer's and is explicitly not asked for. ``unit`` below is the unit a NUMBER
is in -- and is ``None`` for a dimensionless one -- not a string to render.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from pathlib import Path
from typing import Any, Final, cast

from certiqs_key.runs.config import (
    AdvancedSolverSettings,
    AlphaSearchSettings,
    RunConfig,
    SolverSettings,
)
from certiqs_key.runs.errors import RunInputKeyError, RunInputReason, RunInputValueError
from certiqs_key.runs.pipeline import PreparationOutcome, SliceOutcome
from certiqs_key.solvers.frank_wolfe.joint_options import ORACLE_CHOICES
from certiqs_key.solvers.types import (
    ADVANCED_METHODS,
    ORDINARY_METHODS,
    SearchRequest,
)
from certiqs_key.statistics.rules import EndpointRuleName, TailEvaluation

__all__ = [
    "DEFAULT_METHOD",
    "RUN_PARAMETERS",
    "InstanceDescriptor",
    "InstanceIdentity",
    "Kind",
    "ParameterDomain",
    "ParameterSpec",
    "Preparer",
    "Preset",
    "Quantity",
    "Runner",
    "Section",
    "applies",
    "at_least",
    "check_applicability",
    "check_keys",
    "choices",
    "closed_interval",
    "half_open",
    "open_interval",
    "readme_path",
    "solver_request",
    "unrestricted",
    "when",
]


class Section(StrEnum):
    """Where in the configuration a parameter lives.

    ``model`` and ``device`` are the configuration's two opaque mappings, an
    instance's own. The split is the configuration's and is not presentational:
    ``model`` is the CHANNEL and ``device`` is the APPARATUS, read by different
    providers at different stages, which is why an optical receiver's
    per-detector ``efficiency`` and an optical channel's ``transmittance`` can
    both exist without one of them being renamed.

    ``run``, ``key-length`` and ``solver`` are the configuration's OWN fields,
    described once for every instance by :data:`RUN_PARAMETERS` (record schema
    0.20.0): the composition (``rounds``, the completeness budget, the declared
    tolerance and the statistics request), the security statement's numbers
    (the ``parameters`` block) and the search settings (``solver``). No
    instance table carries one of them.
    """

    MODEL = "model"
    DEVICE = "device"
    RUN = "run"
    KEY_LENGTH = "key-length"
    SOLVER = "solver"


class Kind(StrEnum):
    """What a parameter's VALUE is, in the configuration's own types."""

    #: An exact rational. The house convention for a model parameter.
    FRACTION = "fraction"
    #: An integer, carried as an integral ``Fraction`` in the mapping.
    INT = "int"
    #: A NAME rather than a quantity -- the ``str`` half of ``device``'s
    #: deliberate widening, e.g. which reduction a device declares.
    CHOICE = "choice"
    #: One exact rational PER RECEIVER PORT: a ``Mapping`` from port label to
    #: ``Fraction``, keyed by :attr:`ParameterSpec.per_port_labels` and never by
    #: position or by a fixed count, because the number of ports is the
    #: receiver's declaration and not this format's.
    #:
    #: THE MAPPING IS THE ONLY ADMISSIBLE SHAPE, and it is stated here because
    #: this is the one place a consumer reads it from: a bare ``Fraction``
    #: meaning "the same value on every port" is NOT accepted, so that the
    #: shape of a value never depends on how uniform it happens to be and the
    #: instance's own reader and :func:`check_keys` cannot disagree about which
    #: shapes exist. A caller wanting one number on every port writes
    #: ``dict.fromkeys(spec.per_port_labels, value)``, which is the same
    #: declaration said once.
    PER_PORT_FRACTION = "per_port_fraction"
    #: A binary64 number that IS its datum (spec/architecture.md 2.8): the
    #: configuration's own floats, the declared tolerance and the key-length
    #: parameters. Used by :data:`RUN_PARAMETERS`; no instance declares one.
    FLOAT = "float"
    #: A list of names, or ``null`` (the configuration's outcome selector).
    LABELS = "labels"
    #: A structured value its ``meaning`` describes (a warm-start seed).
    RECORD = "record"
    #: A truth value: a run-level switch (the snap parameters,
    #: record schema 0.22.0). Used by :data:`RUN_PARAMETERS`; no instance
    #: declares one.
    BOOLEAN = "boolean"


class Quantity(StrEnum):
    """WHAT KIND OF NUMBER a parameter is: a small, closed vocabulary.

    A consumer attaches generic conversions and scales to these without knowing
    the parameter: a ``TRANSMITTANCE`` has a decibel reading, a ``PHOTON_NUMBER``
    is a cutoff to step through, an ``ANGLE_PI`` is in units of pi. THE
    VOCABULARY IS CLOSED AND IS DEFINED HERE, so that two instances cannot
    describe the same physical quantity under two names; an instance that needs
    a member this list does not have adds it here, in the open, rather than
    writing a string of its own.
    """

    PROBABILITY = "probability"
    TRANSMITTANCE = "transmittance"
    EFFICIENCY = "efficiency"
    ANGLE_PI = "angle_pi"
    COUNT = "count"
    PHOTON_NUMBER = "photon_number"
    MEAN_PHOTON_NUMBER = "mean_photon_number"
    CHOICE = "choice"
    #: A Renyi order ``alpha`` (the run-level parameters, record schema 0.20.0).
    RENYI_ORDER = "renyi_order"
    #: ``alpha - 1``, a Renyi order's offset above one: the outer alpha
    #: search's interval (record schema 0.24.0), which is log-spaced in it.
    RENYI_ORDER_OFFSET = "renyi_order_offset"
    #: A numerical ceiling or target: a declared tolerance, a gap target.
    TOLERANCE = "tolerance"
    #: A wall-clock duration.
    DURATION = "duration"
    #: A reference to an artefact by its file and content hash.
    ARTEFACT = "artefact"


@dataclass(frozen=True)
class ParameterDomain:
    """An instance's own validity condition for one parameter, AS DATA.

    Not a predicate and not a docstring: a consumer has to be able to show the
    admissible values without running the instance, and the instance has to be
    able to decide them without a second spelling. Two forms cover every
    parameter the instances declare -- an interval with its two ends open or
    closed, and a finite set of named choices -- and a third would be added
    here rather than invented in an instance.
    """

    #: ``interval``, ``choices`` or ``unrestricted``. The third is the run-level
    #: table's (:data:`RUN_PARAMETERS`), for a value whose kind is all there is
    #: to decide (a list of outcome labels, a warm-start seed); no instance
    #: parameter uses it.
    form: str
    lower: Fraction | None = None
    upper: Fraction | None = None
    lower_open: bool = False
    upper_open: bool = False
    #: ``(value, meaning)`` pairs, on the ``choices`` form.
    options: tuple[tuple[str, str], ...] = ()

    def admits(self, value: object) -> bool:
        """Whether this domain admits ``value``.

        An interval admits an exact rational, an integer, or a finite binary64
        number (a ``float`` is its own exact value); never a ``bool``.
        """
        if self.form == "unrestricted":
            return True
        if self.form == "choices":
            return any(value == option for option, _ in self.options)
        if isinstance(value, bool) or not isinstance(value, Fraction | int | float):
            return False
        if isinstance(value, float) and not math.isfinite(value):
            return False
        number = Fraction(value)
        if self.lower is not None and (
            number < self.lower or (self.lower_open and number == self.lower)
        ):
            return False
        return not (
            self.upper is not None
            and (number > self.upper or (self.upper_open and number == self.upper))
        )

    def as_payload(self) -> dict[str, Any]:
        """Return the domain as JSON, in the house conventions."""
        if self.form == "unrestricted":
            return {"form": "unrestricted"}
        if self.form == "choices":
            return {
                "form": "choices",
                "options": [
                    {"value": value, "meaning": meaning}
                    for value, meaning in self.options
                ],
            }
        return {
            "form": "interval",
            "lower": None if self.lower is None else str(self.lower),
            "upper": None if self.upper is None else str(self.upper),
            "lower_open": self.lower_open,
            "upper_open": self.upper_open,
        }


def open_interval(lower: Fraction | int, upper: Fraction | int) -> ParameterDomain:
    """Return ``(lower, upper)``."""
    return ParameterDomain(
        form="interval",
        lower=Fraction(lower),
        upper=Fraction(upper),
        lower_open=True,
        upper_open=True,
    )


def half_open(lower: Fraction | int, upper: Fraction | int) -> ParameterDomain:
    """Return ``[lower, upper)``."""
    return ParameterDomain(
        form="interval", lower=Fraction(lower), upper=Fraction(upper), upper_open=True
    )


def closed_interval(lower: Fraction | int, upper: Fraction | int) -> ParameterDomain:
    """Return ``[lower, upper]``."""
    return ParameterDomain(
        form="interval", lower=Fraction(lower), upper=Fraction(upper)
    )


def choices(*options: tuple[str, str]) -> ParameterDomain:
    """Return a finite set of ``(value, meaning)`` pairs."""
    return ParameterDomain(form="choices", options=tuple(options))


def at_least(lower: Fraction | int, *, open_end: bool = False) -> ParameterDomain:
    """Return ``[lower, inf)``, or ``(lower, inf)`` with ``open_end``."""
    return ParameterDomain(form="interval", lower=Fraction(lower), lower_open=open_end)


def unrestricted() -> ParameterDomain:
    """Return the domain that decides nothing beyond the parameter's kind."""
    return ParameterDomain(form="unrestricted")


@dataclass(frozen=True)
class ParameterSpec:
    """One parameter of one instance, as data a consumer can act on.

    ``meaning`` is one sentence in the instance's own words -- the docstring's
    sentence, not a new one -- because a table that paraphrased would be a
    second description to keep true.

    ``applies_when`` says WHEN THE PARAMETER HAS AN EFFECT, as a condition on
    the values of OTHER parameters of the same table: a tuple of
    ``(name, allowed_values)`` pairs, all of which must hold (build it with
    :func:`when`). ``None`` means the parameter always has an effect.
    :func:`check_applicability` decides that every name exists, is not the
    parameter itself, and that every value is in that parameter's domain.

    IT CHANGES NOTHING A RUN DOES WITH A SUPPLIED VALUE. A configuration that
    sets an inapplicable parameter is accepted exactly as before,
    :func:`check_keys` decides its value against its domain exactly as before,
    and the instance ignores it exactly as before. It exists so that a form
    can say "used only when ``source_model`` is ``spdc``" without naming a
    parameter of its own. The one place the run path reads it is
    :func:`check_keys`' completeness check, through :func:`applies`: an input
    that would have no effect is never DEMANDED.
    """

    name: str
    section: Section
    kind: Kind
    quantity: Quantity
    #: The unit the NUMBER is in, or ``None`` where it is dimensionless. Not a
    #: string to render: a consumer's labels are its own.
    unit: str | None
    default: Any
    domain: ParameterDomain
    #: Whether the instance SNAPS what it declares from this parameter
    #: (spec/architecture.md 2.9). A reader of a run record can then tell which
    #: declared numbers the ``snaps`` block is about.
    snapped: bool
    meaning: str
    #: On :attr:`Kind.PER_PORT_FRACTION`: the receiver's own port-map labels,
    #: in the declared order. Empty on every other kind.
    per_port_labels: tuple[str, ...] = ()
    #: When the parameter has an effect: ``(other_name, allowed_values)``
    #: pairs, ANDed; ``None`` for always. See the class docstring.
    applies_when: tuple[tuple[str, tuple[Any, ...]], ...] | None = None
    #: WHICH STATION THE PARAMETER DESCRIBES, on an instance with several:
    #: the station's declared factor,
    #: :attr:`~certiqs_key.runs.pipeline.Station.factor` -- the value a run
    #: record's ``payload.stages.stations[i].factor`` and each per-station
    #: stage's ``station`` carry -- and ``None`` for a parameter that belongs
    #: to no one station, and for every parameter of a single-station
    #: instance. A reference to the station the instance declares on its
    #: ``DeviceRequests``, not a second declaration of it, so that a consumer
    #: attaches a parameter to its station without parsing the parameter's
    #: name. Advisory like :attr:`applies_when`: nothing on the run path
    #: reads it.
    station: str | None = None

    def as_payload(self) -> dict[str, Any]:
        """Return the spec as JSON, rationals as ``"p/q"`` strings.

        ``applies_when`` is ``null`` for a parameter that always has an effect,
        and otherwise an object from each other parameter's name to the list of
        its values under which this one has an effect, e.g.
        ``{"source_model": ["spdc"]}``. ``station`` is the station's factor
        label, or ``null``.
        """
        return {
            "name": self.name,
            "section": str(self.section),
            "kind": str(self.kind),
            "quantity": str(self.quantity),
            "unit": self.unit,
            "default": _jsonable_default(self.default),
            "domain": self.domain.as_payload(),
            "snapped": self.snapped,
            "meaning": self.meaning,
            "per_port_labels": list(self.per_port_labels),
            "applies_when": (
                None
                if self.applies_when is None
                else {
                    name: [_jsonable_default(value) for value in values]
                    for name, values in self.applies_when
                }
            ),
            "station": self.station,
        }


def when(
    conditions: Mapping[str, Sequence[Any]],
) -> tuple[tuple[str, tuple[Any, ...]], ...]:
    """Return an :attr:`ParameterSpec.applies_when` from a plain mapping.

    ``when({"route": ("licensed", "licensed+two-sector")})`` reads "has an effect
    only when ``route`` is ``licensed`` or ``licensed+two-sector``"; several keys are
    ANDed. The result is a tuple so that the spec stays hashable.
    """
    return tuple((name, tuple(values)) for name, values in conditions.items())


def check_applicability(parameters: Sequence[ParameterSpec], instance: str) -> None:
    """Refuse an ``applies_when`` that does not resolve inside its own table.

    Every condition names ANOTHER parameter of ``parameters``, names it once,
    lists at least one value, and every value is admitted by that parameter's
    own domain. A per-port parameter cannot be a condition, because its value
    is a mapping and a condition compares a value. Called by each instance at
    import, so a table that does not resolve fails loudly before anything runs.

    Raises:
        ValueError: naming the parameter and the condition that fails.
    """
    table = {spec.name: spec for spec in parameters}
    for spec in parameters:
        if spec.applies_when is None:
            continue
        if not spec.applies_when:
            raise ValueError(
                f"{instance}: {spec.name}.applies_when is empty; write None for "
                "a parameter that always has an effect"
            )
        seen: set[str] = set()
        for name, values in spec.applies_when:
            if name == spec.name:
                raise ValueError(
                    f"{instance}: {spec.name}.applies_when refers to itself"
                )
            if name in seen:
                raise ValueError(
                    f"{instance}: {spec.name}.applies_when names {name!r} twice"
                )
            seen.add(name)
            other = table.get(name)
            if other is None:
                raise ValueError(
                    f"{instance}: {spec.name}.applies_when names {name!r}, which "
                    f"is not a parameter of this table ({sorted(table)})"
                )
            if other.kind is Kind.PER_PORT_FRACTION:
                raise ValueError(
                    f"{instance}: {spec.name}.applies_when names the per-port "
                    f"parameter {name!r}; a condition compares a single value"
                )
            if not values:
                raise ValueError(
                    f"{instance}: {spec.name}.applies_when lists no value of {name!r}"
                )
            for value in values:
                if not other.domain.admits(value):
                    raise ValueError(
                        f"{instance}: {spec.name}.applies_when allows {name} = "
                        f"{value!r}, outside that parameter's domain "
                        f"{other.domain.as_payload()}"
                    )


def applies(
    spec: ParameterSpec,
    values: Mapping[str, object],
    parameters: Sequence[ParameterSpec],
) -> bool:
    """Whether ``spec`` has an effect under the configuration ``values``.

    ``values`` holds the configuration's declared values of every section by
    name (names are unique across the table; :func:`check_applicability`
    resolves conditions over the whole table the same way). A condition
    naming a parameter the configuration does not declare reads that
    parameter's table default, which is what the instance reads for it; a
    ``None`` default satisfies no condition. ``applies_when = None`` always
    applies.
    """
    if spec.applies_when is None:
        return True
    table = {other.name: other for other in parameters}
    return all(
        values.get(name, table[name].default) in allowed
        for name, allowed in spec.applies_when
    )


def _jsonable_default(value: object) -> Any:
    """Render a default in the house conventions: ``"p/q"``, never a float."""
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable_default(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_jsonable_default(item) for item in value]
    return value


@dataclass(frozen=True)
class InstanceDescriptor:
    """Who an instance is: the three strings and the path of its README."""

    id: str
    title: str
    #: One or two sentences. What the instance IS, not how to run it.
    summary: str
    #: The README's path, relative to the repository root.
    readme: str

    def as_payload(self) -> dict[str, str]:
        """Return the descriptor as JSON."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "readme": self.readme,
        }


@dataclass(frozen=True)
class Preset:
    """A named parameter set, as data. May be absent; never required.

    The named fixtures ``instances/bb84/parameters.yaml`` already carries are
    presets; an instance with none exports an empty tuple rather than a
    placeholder.
    """

    name: str
    #: One line on what the preset is for.
    note: str
    model: Mapping[str, Fraction] = ()  # type: ignore[assignment]
    device: Mapping[str, Fraction | str] = ()  # type: ignore[assignment]

    def as_payload(self) -> dict[str, Any]:
        """Return the preset as JSON, rationals as ``"p/q"`` strings."""
        return {
            "name": self.name,
            "note": self.note,
            "model": {key: str(value) for key, value in dict(self.model).items()},
            "device": {
                key: (str(value) if isinstance(value, Fraction) else value)
                for key, value in dict(self.device).items()
            },
        }


@dataclass(frozen=True)
class InstanceIdentity:
    """Which instance a run record is of: its descriptor and its parameter table.

    WHAT :func:`~certiqs_key.runs.record.record_run` WRITES AS THE RECORD'S
    ``instance`` BLOCK (record schema 0.20.0): the descriptor's four strings and
    every :class:`ParameterSpec` of the instance, so a reader of the record --
    the key-rate report's "Your inputs" -- gives each model and device value
    its meaning, unit and domain without importing the instance. A caller that
    knows its instance passes ``InstanceIdentity(DESCRIPTOR, PARAMETERS)``;
    one that does not records ``null``, and the report says so.
    """

    descriptor: InstanceDescriptor
    parameters: tuple[ParameterSpec, ...]

    def as_payload(self) -> dict[str, Any]:
        """Return the record's ``instance`` block."""
        return {
            **self.descriptor.as_payload(),
            "parameters": [spec.as_payload() for spec in self.parameters],
        }


def _run(
    name: str,
    section: Section,
    kind: Kind,
    quantity: Quantity,
    domain: ParameterDomain,
    meaning: str,
    *,
    unit: str | None = None,
    default: Any = None,
    applies_when: tuple[tuple[str, tuple[Any, ...]], ...] | None = None,
) -> ParameterSpec:
    """Return one row of :data:`RUN_PARAMETERS`; none is snapped by an instance."""
    return ParameterSpec(
        name=name,
        section=section,
        kind=kind,
        quantity=quantity,
        unit=unit,
        default=default,
        domain=domain,
        snapped=False,
        meaning=meaning,
        applies_when=applies_when,
    )


#: The candidate search method a configuration that chooses none runs: THE
#: ONE PLACE the run tier resolves an absent ``solver.method``
#: (:func:`solver_request`). The solver tier's own ``SearchRequest`` default is
#: not read for it, so moving this default is this line and its tests.
#: ``auto``: on every shipped instance at its run defaults it gave the same
#: or a larger key than ``fw`` and converged in less time, where ``fw``
#: stopped at its iteration cap.
#: Its work is wall-clock time, so a caller needing a run that repeats
#: exactly chooses ``fw``.
DEFAULT_METHOD: Final[str] = "auto"


_METHOD_MEANINGS: Mapping[str, str] = {
    "fw": "plain Frank-Wolfe, bounded by max_iterations",
    "auto": "the coordinator's schedule: factor, then entropy, then corrective "
    "from the best point and cold (a Frank-Wolfe stage where corrective is "
    "unsupported), under one wall budget",
    "pairwise": "Frank-Wolfe with the pairwise step rule",
    "factor": "full complex normalized-factor candidates with bounded L-BFGS storage",
    "entropy": "an entropy-limit QICS initializer followed by finite-alpha factor "
    "polish",
    "corrective": "bounded corrective simplex search, retaining the best evaluated "
    "mixture",
}
_ORACLE_MEANINGS: Mapping[str, str] = {
    "qics": "every subproblem to the conic oracle",
    "spectral": "every spectraplex subproblem to the closed-form spectral backend, "
    "every other to the conic oracle",
}

#: THE CONFIGURATION'S OWN FIELDS, described once for every instance (record
#: schema 0.20.0): one row per key of
#: :meth:`~certiqs_key.runs.config.RunConfig.to_payload` other than the
#: instance's ``model`` and ``device`` mappings and the conversion record, the
#: ``parameters`` and ``solver`` blocks dotted
#: (``tests/unit/test_run_parameters.py`` holds the names to that payload).
#:
#: WHY HERE. An instance's table says what ITS parameters mean; these are the
#: run tier's, and a reader of a record (the key-rate report's "Your inputs",
#: an agent through the MCP server) needs the same meaning, unit and domain
#: for ``parameters.eps_auth`` as for ``model.qber``. Each meaning is the
#: sentence of the field's own comment or of meat-core's parameters row, not a
#: new description. ``parameters.alpha`` (the declaration's key-length order)
#: and ``alpha`` (the order a run solves at) are two rows.
RUN_PARAMETERS: tuple[ParameterSpec, ...] = (
    _run(
        "rounds", Section.RUN, Kind.INT, Quantity.COUNT, at_least(1),
        "the number of rounds (n), total channel uses; the same n reaches the "
        "acceptance construction and the declaration "
        "(statistics/req:matched-alphabet)",
    ),
    _run(
        "completeness_budget", Section.RUN, Kind.FRACTION, Quantity.PROBABILITY,
        half_open(0, 1),
        "the completeness budget (eps_comp) of the acceptance construction; it "
        "buys completeness and never soundness",
    ),
    _run(
        "declared_tolerance", Section.RUN, Kind.FLOAT, Quantity.TOLERANCE,
        half_open(0, 1),
        "the ceiling (tau) on the pre-snap defect the instance may repair "
        "(spec/architecture.md 2.8); required, with no default, and told to no "
        "module",
    ),
    _run(
        "parameters.alpha", Section.KEY_LENGTH, Kind.FLOAT, Quantity.RENYI_ORDER,
        at_least(1, open_end=True),
        "the Renyi order (alpha) of the declaration; every key-length statement "
        "requires alpha in (1, 2) (req:key-length-alpha-domain)",
    ),
    _run(
        "parameters.eps_pa", Section.KEY_LENGTH, Kind.FLOAT, Quantity.PROBABILITY,
        ParameterDomain(form="interval", lower=Fraction(0), upper=Fraction(1),
                        lower_open=True),
        "the privacy-amplification (secrecy) budget of the key-length expression; "
        "eps_pa + eps_ev + 2 eps_auth < 1 (req:security-statement-not-vacuous)",
    ),
    _run(
        "parameters.eps_ev", Section.KEY_LENGTH, Kind.FLOAT, Quantity.PROBABILITY,
        ParameterDomain(form="interval", lower=Fraction(0), upper=Fraction(1),
                        lower_open=True),
        "the error-verification (correctness) budget; eps_pa + eps_ev + 2 eps_auth "
        "< 1 (req:security-statement-not-vacuous)",
    ),
    _run(
        "parameters.lambda_ec", Section.KEY_LENGTH, Kind.INT, Quantity.COUNT,
        at_least(0),
        "the error-correction transcript length in bits, total and not per round: "
        "a fixed-length register of that many bits (ass:keyreg)",
        unit="bit",
    ),
    _run(
        "parameters.eps_auth", Section.KEY_LENGTH, Kind.FLOAT, Quantity.PROBABILITY,
        half_open(0, 1),
        "authentication error bound: the scheme's error on an ideal key plus the "
        "key's trace distance delta from an ideal key; delta = 0 for a fresh key, "
        "and for a key from an earlier run a distance you bound and declare "
        "(ass:auth). It enters the security parameter twice and never the key "
        "length",
        default=0.0,
    ),
    _run(
        "parameters.k_auth", Section.KEY_LENGTH, Kind.INT, Quantity.COUNT,
        at_least(0),
        "the pre-shared key bits the authentication scheme consumes in one run "
        "(ass:auth (ii)); the net key is the key length minus k_auth",
        unit="bit",
        default=0,
    ),
    _run(
        "parameters.reference_enclosure", Section.RUN, Kind.BOOLEAN, Quantity.CHOICE,
        unrestricted(),
        "whether the instance hands beside its snap of its receiver measurement "
        "the blocks of the reference known through rigorous rational "
        "enclosures (foundations/req:snap-reference (i)); off, only the blocks "
        "known exactly are handed, and the reference companion carries the "
        "snapped block on every other moved block, which then rests on A-SNAP "
        "in the group no_usable_reference (cause enclosure_not_used)",
        default=True,
    ),
    _run(
        "parameters.strict_snaps", Section.RUN, Kind.BOOLEAN,
        Quantity.CHOICE, unrestricted(),
        "the strict option: whether the run refuses wherever a moved block of "
        "a measurement snap or a moved class of the emission would rest on "
        "A-SNAP, rather than disclosing it, and reports no key length that "
        "rests on it (foundations/req:snap-reference (iv))",
        default=False,
    ),
    _run(
        "parameters.statistics_check", Section.RUN, Kind.CHOICE, Quantity.CHOICE,
        choices(
            ("on", "check a run whose honest statistics are supplied or whose "
             "declaration carries a constraint entry you declared"),
            ("off", "do not check it; the record names A-REACH as unchecked"),
        ),
        "the check of the acceptance set against the statistics the declared "
        "model can produce (meat-core/req:unreachable-acceptance-set): once per "
        "run it bounds the mismatch from below and caps the probability that "
        "devices behaving as declared pass the acceptance test",
        default="on",
    ),
    _run(
        "parameters.min_model_pass_probability", Section.RUN, Kind.FRACTION,
        Quantity.PROBABILITY, ParameterDomain(
            form="interval", lower=Fraction(0), upper=Fraction(1), lower_open=True
        ),
        "the smallest probability (tau) with which devices behaving as declared "
        "must be able to pass the acceptance test: a checked run whose proven "
        "cap on that probability is at most tau is refused as a whole, with no "
        "key length (meat-core/req:unreachable-acceptance-set (iv))",
        default=Fraction(1, 2),
    ),
    _run(
        "alpha", Section.RUN, Kind.FLOAT, Quantity.RENYI_ORDER,
        at_least(1, open_end=True),
        "the Renyi order the run solves at; unset, the run solves at "
        "parameters.alpha, or lets alpha_search choose it where that is set "
        "(never both)",
    ),
    # THE OPT-IN OUTER ALPHA SEARCH (record schema 0.24.0), dotted like
    # ``solver``: the block is absent unless chosen, and each default below is
    # what an absent key of a chosen block reads (AlphaSearchSettings).
    _run(
        "alpha_search.lower_alpha_minus_one", Section.RUN, Kind.FLOAT,
        Quantity.RENYI_ORDER_OFFSET, open_interval(0, 1),
        "the smallest alpha - 1 the outer alpha search evaluates; set, the run "
        "chooses alpha from the honest model before the protocol runs, and "
        "alpha must then be unset",
        default=AlphaSearchSettings().lower,
    ),
    _run(
        "alpha_search.upper_alpha_minus_one", Section.RUN, Kind.FLOAT,
        Quantity.RENYI_ORDER_OFFSET, open_interval(0, 1),
        "the largest alpha - 1 the outer alpha search evaluates, above the "
        "smallest and below 1 so that alpha stays in (1, 2) "
        "(req:key-length-alpha-domain)",
        default=AlphaSearchSettings().upper,
    ),
    _run(
        "alpha_search.coarse_points", Section.RUN, Kind.INT, Quantity.COUNT,
        at_least(2),
        "the points of the search's coarse grid, log-spaced in alpha - 1 with "
        "both ends included; each is one run",
        default=AlphaSearchSettings().coarse_points,
    ),
    _run(
        "alpha_search.refine_steps", Section.RUN, Kind.INT, Quantity.COUNT,
        at_least(0),
        "the golden-section refinement runs after the grid, around its best "
        "point; each is one run",
        default=AlphaSearchSettings().refine_steps,
    ),
    _run(
        "constrained", Section.RUN, Kind.LABELS, Quantity.CHOICE, unrestricted(),
        "which acceptance outcomes the acceptance set constrains; unset, every "
        "outcome is constrained, and an empty list is a selector in its own "
        "right",
    ),
    _run(
        "endpoint_rule", Section.RUN, Kind.CHOICE, Quantity.CHOICE,
        choices(
            (str(EndpointRuleName.EXACT), "the exact binomial quantile rule"),
            (str(EndpointRuleName.BERNSTEIN), "the closed-form Bernstein rule"),
        ),
        "statistics' endpoint rule for the acceptance box",
        default=str(EndpointRuleName.EXACT),
    ),
    _run(
        "tail_evaluation", Section.RUN, Kind.CHOICE, Quantity.CHOICE,
        choices(
            (str(TailEvaluation.SWEEP), "the closed tail forms, swept from zero"),
            (str(TailEvaluation.ENCLOSURE), "the local enclosures large n needs"),
        ),
        "how statistics decides a tail comparison; it never changes what is "
        "decided",
        default=str(TailEvaluation.SWEEP),
    ),
    _run(
        "solver.method", Section.SOLVER, Kind.CHOICE, Quantity.CHOICE,
        choices(*((name, _METHOD_MEANINGS[name]) for name in ORDINARY_METHODS)),
        f"the candidate search method; unset, {DEFAULT_METHOD} is taken",
    ),
    _run(
        "solver.budget_seconds", Section.SOLVER, Kind.FLOAT, Quantity.DURATION,
        at_least(0, open_end=True),
        "one solver-wide wall-clock time limit, including all attempts and "
        "assessments",
        unit="s",
    ),
    _run(
        "solver.max_iterations", Section.SOLVER, Kind.INT, Quantity.COUNT,
        at_least(1),
        "a method-native work cap (under auto, of the Frank-Wolfe stages "
        "only); unset, the solver's own is taken",
    ),
    _run(
        "solver.advanced.method", Section.SOLVER, Kind.CHOICE, Quantity.CHOICE,
        choices(*((name, _METHOD_MEANINGS[name]) for name in ADVANCED_METHODS)),
        "an expert candidate search method, overriding solver.method (setting "
        "both is refused); unset, solver.method decides",
    ),
    _run(
        "solver.advanced.oracle", Section.SOLVER, Kind.CHOICE, Quantity.CHOICE,
        choices(*((name, _ORACLE_MEANINGS[name]) for name in ORACLE_CHOICES)),
        "the linear-oracle choice; unset, the solver's own (qics) is taken",
    ),
    _run(
        "solver.advanced.gap_tolerance", Section.SOLVER, Kind.FLOAT,
        Quantity.TOLERANCE,
        at_least(0, open_end=True),
        "a diagnostic gap target, finite and positive; unset, the solver's own "
        "is taken",
    ),
    _run(
        "solver.advanced.warm_start", Section.SOLVER, Kind.RECORD,
        Quantity.ARTEFACT,
        unrestricted(),
        "a prior point's final iterate to start from, named by its file and the "
        "sha256 of that file; unset, the run starts cold",
    ),
    _run(
        "solver.advanced.certified_evaluation", Section.SOLVER, Kind.CHOICE,
        Quantity.CHOICE,
        choices(
            ("on", "certify the first-order bound where possible, else report it"),
            ("off", "do not run the certified evaluation"),
            ("strict", "refuse a run whose bound cannot be certified"),
        ),
        "the certified evaluation of the first-order bound; unset, it is on",
    ),
)


#: What an instance's ``preparation`` IS: a configuration in, everything that
#: needs no oracle out (:func:`~certiqs_key.runs.pipeline.prepare`, with
#: this instance's own wiring).
#:
#: IT IS PART OF THE UNIFORM SURFACE BECAUSE ``prepare`` IS OTHERWISE
#: UNREACHABLE PER INSTANCE. ``prepare`` takes the device requests, the
#: specification provider and the two optional providers -- exactly the wiring
#: the instance owns -- so a consumer that wanted the acceptance alphabet, the
#: snap records or the planned stage list before committing to a solve would
#: have to rebuild that wiring itself. It shares its
#: reader with :data:`Runner`, so a configuration this accepts is one the run
#: accepts.
type Preparer = Callable[[RunConfig], PreparationOutcome]

#: What an instance's ``runner`` returns: the callable a sweep drives.
#: :func:`~certiqs_key.runs.sweep.sweep` types the runner exactly this way, and
#: the point is that an instance BUILDS one rather than every caller
#: re-doing the wiring (the providers, the device requests, the route, the
#: ``run_slice`` arguments) that a sweep tool did by hand.
type Runner = Callable[[RunConfig, int], SliceOutcome]

#: THE RUN TABLE'S OWN CONDITIONS RESOLVE INSIDE IT.
check_applicability(RUN_PARAMETERS, "run")


def check_keys(
    section: Section,
    declared: Mapping[str, object],
    parameters: Sequence[ParameterSpec],
    instance: str,
    *,
    complete_for: RunConfig | None = None,
) -> None:
    """Refuse a key this instance does not read, or a value outside its domain.

    THE INSTANCE'S OWN KEY CHECK, READING THE TABLE, so that it cannot drift:
    there is one table and this is what reads it.

    ``complete_for=config`` is for a section the instance reads WITHOUT A
    FALLBACK: then every parameter of the section must be declared that
    APPLIES under ``config`` (:func:`applies`, over both of its sections),
    except one whose table default is ``None`` -- the table's own spelling of
    "absent means the instance resolves it" (an ``exact_window``). An
    inapplicable parameter is not demanded, because it would have no effect;
    supplied, it is decided and ignored as before. An instance whose reader
    keeps a value of its own for an absent key passes nothing.

    Every refusal carries a code of
    :class:`~certiqs_key.runs.errors.RunInputReason`,
    so that no instance words one of its own.

    Raises:
        RunInputKeyError: ``unknown_parameter`` naming the unknown keys and what
            the instance does read; ``missing_parameter`` naming what a
            complete section lacks; ``port_labels_mismatch`` for a per-port
            mapping keyed by anything but the port labels.
        RunInputValueError: ``wrong_kind`` for a value that is not of its
            parameter's kind (a name where a rational is declared, a scalar
            where one rational per port is); ``not_an_integer`` for a
            non-integral value of an integer parameter; ``outside_domain``
            for a value its own domain does not admit.
    """
    known = {spec.name for spec in parameters if spec.section is section}
    unknown = set(declared) - known
    if unknown:
        raise RunInputKeyError(
            f"{instance} reads {sorted(known)} in its {section} section; this "
            f"configuration carries {sorted(unknown)} as well",
            reason=RunInputReason.UNKNOWN_PARAMETER,
        )
    table = {spec.name: spec for spec in parameters if spec.section is section}
    if complete_for is not None:
        values = {**complete_for.model, **complete_for.device}
        missing = sorted(
            name
            for name, spec in table.items()
            if spec.default is not None
            and name not in declared
            and applies(spec, values, parameters)
        )
        if missing:
            raise RunInputKeyError(
                f"{instance} reads every parameter of its {section} section; "
                f"this configuration does not declare {missing}",
                reason=RunInputReason.MISSING_PARAMETER,
            )
    for name, value in declared.items():
        spec = table[name]
        if spec.kind is Kind.PER_PORT_FRACTION:
            # ONE SHAPE, DECIDED HERE AND NOWHERE ELSE. A per-port value
            # is a mapping, and a scalar must not fall through to the domain
            # check below to be accepted here and refused by the instance's
            # own reader. The kind fixes the shape and this decides it.
            if not isinstance(value, Mapping):
                raise RunInputValueError(
                    f"{instance}: {name} is one rational PER PORT, a mapping "
                    f"keyed by {list(spec.per_port_labels)}; got {value!r} of "
                    f"type {type(value).__name__}. One value on every port is "
                    "written dict.fromkeys(spec.per_port_labels, value)",
                    reason=RunInputReason.WRONG_KIND,
                )
            _check_per_port(spec, value, instance)
            continue
        _check_scalar(spec, name, value, instance)


def _check_scalar(spec: ParameterSpec, name: str, value: object, instance: str) -> None:
    """Refuse one value that is not of its parameter's kind or not in its domain.

    The kind is decided before the domain so that a caller learns WHAT is wrong:
    a name where a rational is declared is ``wrong_kind``, not a number that
    happens to lie outside an interval.
    """
    admitted: tuple[type, ...] = (
        (float, int) if spec.kind is Kind.FLOAT else (Fraction, int)
    )
    if spec.kind is not Kind.CHOICE and (
        isinstance(value, bool) or not isinstance(value, admitted)
    ):
        raise RunInputValueError(
            f"{instance}: {name} is a {spec.kind} parameter; got {value!r} of "
            f"type {type(value).__name__}",
            reason=RunInputReason.WRONG_KIND,
        )
    if spec.kind is Kind.INT and Fraction(cast(Fraction | int, value)).denominator != 1:
        raise RunInputValueError(
            f"{instance}: {name} is an integer; got {value!r}",
            reason=RunInputReason.NOT_AN_INTEGER,
        )
    if not spec.domain.admits(value):
        raise RunInputValueError(
            f"{instance}: {name} is {value!r}, outside the declared domain "
            f"{spec.domain.as_payload()}",
            reason=RunInputReason.OUTSIDE_DOMAIN,
        )


def _check_per_port(
    spec: ParameterSpec, value: Mapping[str, object], instance: str
) -> None:
    """Refuse a per-port mapping that is not keyed by the port map's labels."""
    labels = set(spec.per_port_labels)
    if set(value) != labels:
        raise RunInputKeyError(
            f"{instance}: {spec.name} is keyed by the receiver's port labels "
            f"{sorted(labels)}; this one carries {sorted(value)}",
            reason=RunInputReason.PORT_LABELS_MISMATCH,
        )
    for port, entry in value.items():
        _check_scalar(spec, f"{spec.name}[{port!r}]", entry, instance)


def solver_request(settings: SolverSettings | None) -> SearchRequest:
    """Resolve the recorded search choices without exposing proof thresholds.

    The effective method is ``solver.advanced.method``, else
    ``solver.method``, else :data:`DEFAULT_METHOD`.
    """
    from certiqs_key.runs.iterate_file import load_warm_start

    defaults = SearchRequest(method=DEFAULT_METHOD)
    if settings is None:
        return defaults
    advanced = settings.advanced or AdvancedSolverSettings()
    return SearchRequest(
        method=settings.chosen_method or DEFAULT_METHOD,
        budget_seconds=settings.budget_seconds,
        max_iterations=(
            defaults.max_iterations
            if settings.max_iterations is None
            else settings.max_iterations
        ),
        gap_target=(
            defaults.gap_target
            if advanced.gap_tolerance is None
            else advanced.gap_tolerance
        ),
        oracle=advanced.oracle or defaults.oracle,
        certified_evaluation=advanced.certified_evaluation or "on",
        warm_start=(
            None
            if advanced.warm_start is None
            else load_warm_start(advanced.warm_start)
        ),
    )


def readme_path(module_file: str) -> str:
    """Return an instance's README path, relative to the repository root.

    Computed from the module rather than written down, so that a moved package
    cannot leave a descriptor pointing at nothing.
    """
    package = Path(module_file).resolve().parent
    return f"instances/{package.name}/README.md"
