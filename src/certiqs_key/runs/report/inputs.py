"""The report's "Your inputs": every declared input of a run, where it is in the record.

WHY THIS EXISTS. A security evaluation asks which values the key rate was
computed for and whether each was used as the proof requires
and the report binds those values to the assumptions that constrain them.
This module turns the record's configuration into one :class:`InputRow` per
declared input, each with a JSON Pointer (RFC 6901) to where the record holds
it, and maps an emitter's binding name to its record location
(:data:`INPUT_POINTERS`; emitters never know record paths).

MEANINGS ARE DATA, NEVER WRITTEN HERE. A model or device row takes its meaning
from the instance's parameter table as the record carries it
(``payload.instance.parameters``, :class:`~certiqs_key.runs.surface.ParameterSpec`
payloads). A run-level row takes its meaning from
:data:`~certiqs_key.runs.surface.RUN_PARAMETERS`. No sentence of run-tier prose
is authored here.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from fractions import Fraction
from typing import Any, Final, Literal

from certiqs_key.runs.report.model import Fact, InputRow
from certiqs_key.runs.surface import RUN_PARAMETERS

__all__ = [
    "BUDGET_INPUTS",
    "FACT_POINTERS",
    "INPUT_LABELS",
    "INPUT_POINTERS",
    "RUN_INPUTS",
    "analysed_config",
    "analysed_words",
    "build_facts",
    "build_inputs",
    "exact_with_decimal",
    "input_group",
    "input_label",
    "input_row_name",
    "parameter_alias",
    "pointer_join",
    "preparation_moves",
    "prepared_inputs",
    "resolve_pointer",
    "run_parameter_specs",
    "same_number",
    "upper_decimal",
]

type Section = Literal["run", "key-length", "model", "device", "solver"]

_MISSING: Final = object()
_NO_DEFAULT: Final = object()

#: THE RUN-LEVEL INPUTS, in display order: ``(name, section, pointer)``. The
#: names are the configuration's own (``RunConfig.to_payload`` keys, the
#: parameter block dotted), which are the stable ids an MCP tool addresses.
RUN_INPUTS: Final[tuple[tuple[str, Section, str], ...]] = (
    ("rounds", "run", "/payload/config/rounds"),
    ("completeness_budget", "run", "/payload/config/completeness_budget"),
    ("declared_tolerance", "run", "/payload/config/declared_tolerance"),
    ("parameters.alpha", "key-length", "/payload/config/parameters/alpha"),
    ("parameters.eps_pa", "key-length", "/payload/config/parameters/eps_pa"),
    ("parameters.eps_ev", "key-length", "/payload/config/parameters/eps_ev"),
    ("parameters.lambda_ec", "key-length", "/payload/config/parameters/lambda_ec"),
    ("parameters.eps_auth", "key-length", "/payload/config/parameters/eps_auth"),
    ("parameters.k_auth", "key-length", "/payload/config/parameters/k_auth"),
    ("parameters.reference_enclosure", "run",
     "/payload/config/parameters/reference_enclosure"),
    ("parameters.strict_snaps", "run",
     "/payload/config/parameters/strict_snaps"),
    ("parameters.statistics_check", "run",
     "/payload/config/parameters/statistics_check"),
    ("parameters.min_model_pass_probability", "run",
     "/payload/config/parameters/min_model_pass_probability"),
    ("alpha", "run", "/payload/config/alpha"),
    ("constrained", "run", "/payload/config/constrained"),
    ("endpoint_rule", "run", "/payload/config/endpoint_rule"),
    ("tail_evaluation", "run", "/payload/config/tail_evaluation"),
)

_RUN_NAMES: Final[frozenset[str]] = frozenset(name for name, _, _ in RUN_INPUTS)

type InputGroup = Literal["device", "budget", "engine"]

#: THE SECURITY BUDGETS of the inputs (report 0.9.0): the rows a user sets to
#: say how secure and how long the key is; every model and device row is
#: "device", every other row "engine".
BUDGET_INPUTS: Final[frozenset[str]] = frozenset({
    "rounds", "completeness_budget", "parameters.alpha", "parameters.eps_pa",
    "parameters.eps_ev", "parameters.lambda_ec", "parameters.eps_auth",
    "parameters.k_auth", "alpha",
})

#: THE READABLE NAME of each run-level input; labels, not meanings (a
#: meaning is the parameter table's).
INPUT_LABELS: Final[Mapping[str, str]] = {
    "rounds": "Rounds n",
    "completeness_budget": "Completeness budget",
    "declared_tolerance": "Declared tolerance τ",
    "parameters.alpha": "Rényi order \u03b1 (declared)",
    "parameters.eps_pa": "Secrecy error ε_PA",
    "parameters.eps_ev": "Error-verification error ε_EV",
    "parameters.lambda_ec": "Error-correction leakage λ_EC",
    "parameters.eps_auth": "Authentication error ε_auth",
    "parameters.k_auth": "Authentication key bits k_auth",
    "parameters.reference_enclosure": "Reference enclosure",
    "parameters.strict_snaps": "Strict option",
    "parameters.statistics_check": "Statistics check",
    "parameters.min_model_pass_probability": "Minimum model pass probability τ",
    "alpha": "Rényi order \u03b1 (configured)",
    "constrained": "Constrained solve",
    "endpoint_rule": "Endpoint rule",
    "tail_evaluation": "Tail evaluation",
    "alpha_search.coarse_points": "\u03b1 search: coarse grid points",
    "alpha_search.lower_alpha_minus_one": "\u03b1 search: lowest \u03b1 \u2212 1",
    "alpha_search.upper_alpha_minus_one": "\u03b1 search: highest \u03b1 \u2212 1",
    "alpha_search.refine_steps": "\u03b1 search: refinement steps",
    "solver.method": "Solver method",
    "solver.budget_seconds": "Solver time limit",
    "solver.max_iterations": "Solver step limit",
    "solver.advanced.method": "Solver method (advanced)",
    "solver.advanced.oracle": "Solver linear oracle",
    "solver.advanced.gap_tolerance": "Solver gap tolerance",
    "solver.advanced.warm_start": "Solver warm start",
    "solver.advanced.certified_evaluation": "Certified evaluation",
}

#: Party prefixes of an instance parameter's name, as a reader says them.
_PARTY_PREFIXES: Final[tuple[tuple[str, str], ...]] = (
    ("alice_", "Alice's "), ("bob_", "Bob's "),
)


#: Words of a parameter name a reader says as an acronym.
_ACRONYMS: Final[Mapping[str, str]] = {
    "qber": "QBER", "pbs": "PBS", "ec": "EC", "hwp": "HWP", "spdc": "SPDC",
}


def input_label(name: str) -> str:
    """Return the readable name of an input row, or ``""`` where none reads.

    A curated label first (:data:`INPUT_LABELS`); else the parameter's name in
    words, its party prefix as a possessive and an acronym in capitals
    ("Alice's dark count", "QBER"). A name with a one-letter word ("alice_y",
    a basis weight) makes no readable label ("Alice's y"): then ``""``, and the
    report shows the name verbatim in code beside its meaning.
    """
    if name in INPUT_LABELS:
        return INPUT_LABELS[name]
    bare = name.split(".", 1)[1] if name.startswith(("model.", "device.")) else name
    owner = ""
    for prefix, words in _PARTY_PREFIXES:
        if bare.startswith(prefix):
            owner, bare = words, bare.removeprefix(prefix)
            break
    parts = [part for part in bare.split("_") if part]
    if not parts or any(len(part) == 1 for part in parts):
        return ""
    phrase = " ".join(_ACRONYMS.get(part, part) for part in parts)
    if owner:
        return owner + phrase
    return phrase[:1].upper() + phrase[1:]


def input_group(name: str, section: str) -> InputGroup:
    """Return which inputs table a row belongs in (report 0.9.0)."""
    if section in ("model", "device"):
        return "device"
    return "budget" if name in BUDGET_INPUTS else "engine"


def parameter_alias(name: str) -> str | None:
    """Return the other spelling of a key-length parameter's name, if it has one.

    ``parameters.eps_auth`` and ``eps_auth`` name one input. A bare name that
    is ITSELF a run-level input is never an alias: ``alpha`` is the
    configuration's own ``alpha`` (``/payload/config/alpha``), not the
    key-length order ``parameters.alpha``, and the two are kept apart.
    """
    if name.startswith("parameters."):
        bare = name.removeprefix("parameters.")
        return None if bare in _RUN_NAMES else bare
    dotted = f"parameters.{name}"
    if dotted in _RUN_NAMES and name not in _RUN_NAMES:
        return dotted
    return None


#: A BINDING NAME OR AN ``input`` NAME TO ITS PLACE IN A RUN RECORD. The run
#: tier adds the ``pointer`` of a binding from here, and only where the pointer
#: resolves in the record at hand (``build.py``), so an entry naming a block a
#: route does not write is harmless. Names follow the binding vocabulary; a run-level
#: input is found under its own name and a key-length parameter also under its bare name
#: (:func:`parameter_alias`), so ``alpha`` and ``parameters.alpha`` resolve to
#: two different places.
INPUT_POINTERS: Final[Mapping[str, str]] = {
    **{name: pointer for name, _, pointer in RUN_INPUTS},
    **{
        alias: pointer
        for name, _, pointer in RUN_INPUTS
        if (alias := parameter_alias(name)) is not None
    },
    "key_length": "/payload/stages/key_rate/key_length",
    "net_key_length": "/payload/stages/key_rate/net_key_length",
    "security_parameter": "/payload/stages/key_rate/security_parameter",
    "acceptance_set": "/payload/stages/acceptance_construction",
    "acceptance_alphabet": "/payload/stages/acceptance_construction/outcomes",
    "honest_distribution": (
        "/payload/stages/acceptance_construction/honest_distribution"
    ),
    "honest_model": "/payload/honest_model_note",
    "specification": "/payload/compiled",
    "choice_weighting": "/payload/compiled/public/choice_weightings",
    "source_ensemble": "/payload/compiled/source",
    "receiver_family": "/payload/stages/receiver_construction",
    "declared_povm": "/payload/stages/receiver_construction",
    "reduction_chain": "/payload/stages/reduction",
    "intensities": "/payload/channel_interface/intensities",
    "source_cutoff": "/payload/channel_interface/source_cutoff",
    "optimizer_gap": "/payload/stages/key_rate/tolerances/optimizer_gap",
    "iterations": "/payload/stages/key_rate/iterations",
    "oracle": "/payload/stages/key_rate/backend",
    # Binding names whose data a 0.20.0 record holds (read off the
    # bindings of every instance's record): a binding carries the value it is
    # about by shape, and these point at the full datum.
    "source_mode": "/payload/compiled/source/source_mode",
    "alice_marginal": "/payload/compiled/source/alice_marginal",
    "alice_povm": "/payload/compiled/source/alice_povm",
    "public_choices": "/payload/compiled/source/public_choices",
    "signal_alphabet": "/payload/compiled/source/signal_alphabet",
    "key_holder": "/payload/compiled/public/key_holder",
    "ev_hash_bits": "/payload/stages/key_rate/deductions/error_verification",
    # An engine choice and an engine count, each with the record field it
    # shows in: ``ideal_hash`` is
    # the hash family's choice, recorded as the two-universal penalty it
    # deducts (``deductions_of``: 0 for an ideal hash, 1 otherwise), and
    # ``bracket_iterates`` counts the entries of the per-iterate record whose
    # bracket was not withdrawn.
    "ideal_hash": "/payload/stages/key_rate/deductions/two_universal_hash_penalty",
    "bracket_iterates": "/payload/stages/key_rate/per_iterate",
}

#: THE ROUTE FACTS a reader needs before the inputs: ``(name, pointer)``; a
#: fact whose pointer does not resolve in the record is not listed.
FACT_POINTERS: Final[tuple[tuple[str, str], ...]] = (
    ("source_mode", "/payload/stages/key_rate/security_gates/source_mode"),
    ("receiver_route", "/payload/stages/receiver_construction/receiver_route"),
    ("receiver_construction_route", "/payload/stages/receiver_construction/route"),
    ("reduction_route", "/payload/stages/reduction/route"),
    ("source_shape", "/payload/channel_interface/source_shape"),
    ("source_model", "/payload/channel_interface/source_model"),
    ("intensities", "/payload/channel_interface/intensities"),
    ("source_cutoff", "/payload/channel_interface/source_cutoff"),
    ("acceptance_geometry", "/payload/stages/acceptance_construction/geometry"),
    ("accumulation_branch",
     "/payload/stages/key_rate/security_gates/accumulation_branch"),
)


def _escape(token: str) -> str:
    """Escape one reference token (RFC 6901 section 3)."""
    return token.replace("~", "~0").replace("/", "~1")


def pointer_join(base: str, *tokens: str | int) -> str:
    """Return ``base`` extended by the escaped ``tokens``."""
    return base + "".join("/" + _escape(str(token)) for token in tokens)


def resolve_pointer(document: Any, pointer: str, default: Any = _NO_DEFAULT) -> Any:
    """Return the value at ``pointer`` in ``document`` (RFC 6901).

    Raises ``KeyError`` where it does not resolve, unless ``default`` is given.
    """
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        if default is _NO_DEFAULT:
            raise KeyError(pointer)
        return default
    node = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, Mapping) and token in node:
            node = node[token]
        elif (
            isinstance(node, list)
            and token.isdigit()
            and (token == "0" or not token.startswith("0"))
            and int(token) < len(node)
        ):
            node = node[int(token)]
        else:
            if default is _NO_DEFAULT:
                raise KeyError(pointer)
            return default
    return node


def run_parameter_specs() -> dict[str, Mapping[str, Any]]:
    """Return the run-level parameter table, by name, as JSON payloads.

    :data:`~certiqs_key.runs.surface.RUN_PARAMETERS`, one
    :class:`~certiqs_key.runs.surface.ParameterSpec` per configuration field
    with its meaning (record schema 0.20.0). Each spec is indexed under its own
    name and under its :func:`parameter_alias`, so either spelling of a
    key-length parameter finds it, and a bare name that is itself a run-level
    input (``alpha``) is never given another's spec.
    """
    table: dict[str, Mapping[str, Any]] = {}
    for spec in RUN_PARAMETERS:
        table[spec.name] = spec.as_payload()
    for name, found in list(table.items()):
        alias = parameter_alias(name)
        if alias is not None:
            table.setdefault(alias, found)
    return table


def _instance_specs(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return the instance's parameter table as the record carries it, or ``[]``."""
    instance = record["payload"].get("instance")
    if not isinstance(instance, Mapping):
        return []
    specs = instance.get("parameters")
    return [spec for spec in specs if isinstance(spec, Mapping)] if specs else []


def _applies(
    spec: Mapping[str, Any], values: Mapping[str, Any], table: Mapping[str, Any]
) -> bool | None:
    """Whether a spec has an effect under the declared values (``surface.applies``).

    Read off the payload form: ``applies_when`` maps another parameter's name
    to the values under which this one has an effect; an undeclared parameter
    reads its table default.
    """
    conditions = spec.get("applies_when")
    if conditions is None:
        return True
    if not isinstance(conditions, Mapping):
        return None
    for name, allowed in conditions.items():
        other = table.get(name)
        value = values.get(name, None if other is None else other.get("default"))
        if value not in list(allowed):
            return False
    return True


def _not_used(spec: Mapping[str, Any] | None) -> str:
    """Return what an input with no effect on this run says: when it would have one.

    WHY: "has no effect under the declared values" alone left a reader asking
    why a mean pair number of 1/32 sits beside a detection probability of 1
    (the stage-9 experimentalist reader); the parameter's own ``applies_when``
    says under which values of which input it applies.
    """
    conditions = None if spec is None else spec.get("applies_when")
    if not isinstance(conditions, Mapping) or not conditions:
        return "has no effect under the declared values"
    where = "; ".join(
        f"{name} is " + " or ".join(str(value) for value in allowed)
        if isinstance(allowed, list | tuple) else f"{name} is {allowed}"
        for name, allowed in conditions.items()
    )
    return f"has no effect under the declared values: it applies only where {where}"


def same_number(first: Any, second: Any) -> bool:
    """Return whether two recorded numbers (``p/q`` strings, ints, floats) are equal.

    A requested ``0.1`` and its prepared ``205/2048`` differ; ``"1/8"`` and
    ``0.125`` do not. Anything that is not a number compares as text.
    """
    try:
        return Fraction(str(first)) == Fraction(str(second))
    except (ValueError, ZeroDivisionError):
        return str(first) == str(second)


def exact_with_decimal(value: Any) -> str:
    """Return a number decimal first, its exact ``p/q`` beside it where they differ.

    ``205/2048`` reads ``0.100098 (205/2048)``; ``1/8`` reads ``0.125``, the
    decimal being the exact value. Anything that is not a number is its text.
    """
    try:
        found = Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return str(value)
    if found.denominator == 1:
        return str(value)
    decimal = f"{float(found):.6g}"
    return decimal if Fraction(decimal) == found else f"{decimal} ({found})"


def upper_decimal(value: Any) -> tuple[str, bool] | None:
    """Return a bound as three significant digits rounded UP, and whether exact.

    An upper bound such as ε* stays an upper bound when shown short:
    ``12274.../26328...`` (4.6620...e-07) reads ``4.67e-07``, never
    ``4.66e-07``. ``None`` where the value is not a number.
    """
    try:
        found = Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return None
    if found <= 0:
        return (f"{float(found):.3g}", True)
    exponent = math.floor(math.log10(float(found)))
    # Correct the float logarithm's last-digit error at a power of ten.
    while Fraction(10) ** exponent > found:
        exponent -= 1
    while Fraction(10) ** (exponent + 1) <= found:
        exponent += 1
    scale = Fraction(10) ** (exponent - 2)
    shown = math.ceil(found / scale) * scale
    return (f"{float(shown):.3g}", shown == found)


def analysed_words(prepared: Any, requested: Any) -> str:
    """Return a prepared value, decimal first, with the request beside it.

    ``0.100098 (exactly 205/2048; requested 0.1)``: the value the run
    analysed, then what was asked for.
    """
    text = exact_with_decimal(prepared)
    decimal, _, exact = text.partition(" (")
    inner = f"exactly {exact[:-1]}; " if exact else ""
    return f"{decimal} ({inner}requested {exact_with_decimal(requested)})"


#: Where a run record keeps its input preparation records, and where a protocol
#: document's preparations say which parameter each prepared value replaces.
_PREPARATION_POINTER: Final = "/payload/snaps/instance/input_preparation"
_DOCUMENT_PREPARATIONS: Final = "/payload/protocol_document/canonical/preparations"


#: The site a protocol document's ``snap.groups`` family is recorded at:
#: ``device.<a>+<b>``, its section and its parameters joined in the group's
#: order (``runs/inputs.py`` ``prepare_config_probabilities``).
_GROUP_SITE: Final = re.compile(r"^(?:model|device)\.(\w+(?:\+\w+)*)$")


def _fraction(value: Any) -> Fraction | None:
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return None


def preparation_moves(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return each instance input preparation that moved a value, as recorded.

    WHY: a probability family the instance put onto its lattice before the
    run (a protocol document's ``snap.groups``, a preparation) is recorded
    under ``snaps/instance/input_preparation`` and nowhere else: the record's
    ``snap_max_defect`` and ``snap_max_displacement`` are taken over the
    measurement blocks alone (``runs/record.py`` ``_snap_extrema``), so a
    report reading only them says nothing moved. Each item is one entry whose
    ``total_displacement`` is not zero: its ``site``, its ``index`` in that
    list and ``pointer``, the ``parameters`` its site names where it is a
    document group's (``device.bob_x+bob_z``; empty otherwise), the
    ``input_values`` and ``prepared_values``, the largest move
    ``displacement`` (a float of the exact difference), and the
    ``normalization_defect`` the entry was admitted with against the declared
    tolerance (a float; ``None`` where not recorded) with its ``admission``.
    """
    entries = resolve_pointer(record, _PREPARATION_POINTER, None)
    if not isinstance(entries, list):
        return []
    moves: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            continue
        shifts = [_fraction(item) for item in entry.get("total_displacement") or ()]
        moved = [abs(shift) for shift in shifts if shift is not None and shift != 0]
        if not moved:
            continue
        site = str(entry.get("site") or "")
        values = entry.get("prepared_values")
        named = _GROUP_SITE.match(site)
        names = named.group(1).split("+") if named else []
        defect = _fraction(entry.get("normalization_defect"))
        moves.append({
            "site": site,
            "index": index,
            "pointer": pointer_join(_PREPARATION_POINTER, index),
            "parameters": names if isinstance(values, list)
            and len(names) == len(values) else [],
            "input_values": list(entry.get("input_values") or ()),
            "prepared_values": list(values) if isinstance(values, list) else [],
            "displacement": float(max(moved)),
            "normalization_defect": None if defect is None else float(defect),
            "admission": entry.get("admission"),
        })
    return moves


def prepared_inputs(record: Mapping[str, Any]) -> dict[str, tuple[str, str]]:
    """Map each parameter a preparation replaced to the value analysed, with pointer.

    Two kinds of preparation replace a parameter. A protocol document's
    ``snap.groups`` family moves its parameters onto the lattice, each in
    place: its record's site names them (:func:`preparation_moves`), and the
    i-th prepared value is the i-th parameter's. A document's preparation
    names a family of probabilities, the site its record carries, and
    ``rebind``: which member of the PREPARED family each named parameter
    becomes for the rest of the run (``instances/declared/surface.py``); it
    runs after the snap, so its value is the one analysed. The configuration
    the record holds is the one requested, so ``device.test_fraction`` there
    is what the user asked for and the prepared member is what was analysed.
    Returns ``{parameter: (prepared value, record pointer of that value)}``;
    empty where the record has no preparation that replaces a parameter.
    """
    found: dict[str, tuple[str, str]] = {}
    for move in preparation_moves(record):
        for position, name in enumerate(move["parameters"]):
            found[name] = (
                str(move["prepared_values"][position]),
                pointer_join(move["pointer"], "prepared_values", position),
            )
    preparations = resolve_pointer(record, _DOCUMENT_PREPARATIONS, None)
    entries = resolve_pointer(record, _PREPARATION_POINTER, None)
    if not isinstance(preparations, list) or not isinstance(entries, list):
        return found
    by_site: dict[str, int] = {}
    for index, entry in enumerate(entries):
        if isinstance(entry, Mapping) and isinstance(entry.get("site"), str):
            by_site.setdefault(entry["site"], index)
    for preparation in preparations:
        if not isinstance(preparation, Mapping):
            continue
        rebind = preparation.get("rebind")
        at = by_site.get(str(preparation.get("site")))
        if not isinstance(rebind, Mapping) or at is None:
            continue
        values = entries[at].get("prepared_values")
        if not isinstance(values, list):
            continue
        for name, position in rebind.items():
            if isinstance(position, int) and 0 <= position < len(values):
                found[str(name)] = (
                    str(values[position]),
                    pointer_join(_PREPARATION_POINTER, at, "prepared_values",
                                 position),
                )
    return found


def analysed_config(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the record's configuration with each prepared parameter replaced.

    The ``model`` and ``device`` values a preparation rebound read as the
    prepared value the run analysed (:func:`prepared_inputs`); everything else
    is the configuration as recorded.
    """
    config = resolve_pointer(record, "/payload/config", None)
    if not isinstance(config, Mapping):
        return {}
    prepared = prepared_inputs(record)
    analysed = dict(config)
    for section in ("model", "device"):
        block = config.get(section)
        if isinstance(block, Mapping):
            analysed[section] = {
                key: prepared[key][0] if key in prepared else value
                for key, value in block.items()
            }
    return analysed


def build_inputs(
    record: Mapping[str, Any], bound_by: Mapping[str, Sequence[str]]
) -> list[InputRow]:
    """Return one :class:`InputRow` per declared input of ``record``.

    ``bound_by`` maps an input row name to the short ids whose bindings name
    it. Model and device rows cover every key the configuration declares and
    every parameter of the instance's table it does not (the instance read
    that parameter's default, which is what :func:`surface.applies` assumes);
    a declared key the table does not know is listed with no meaning.
    """
    config = record["payload"]["config"]
    run_specs = run_parameter_specs()
    rows: list[InputRow] = []

    # Whether a run-level setting has an effect is read as an instance's is
    # (surface.applies).
    run_values = {
        name: value
        for name, _, pointer in RUN_INPUTS
        if (value := resolve_pointer(record, pointer, _MISSING)) is not _MISSING
    }
    for name, run_section, pointer in RUN_INPUTS:
        value = run_values.get(name, _MISSING)
        if value is _MISSING:
            continue
        spec = run_specs.get(name)
        applies: bool | None = None
        if spec is not None and spec.get("applies_when") is not None:
            conditions = spec.get("applies_when")
            known = isinstance(conditions, Mapping) and all(
                condition in run_values for condition in conditions
            )
            applies = _applies(spec, run_values, run_specs) if known else None
        rows.append(_row(name, run_section, value, pointer, spec, bound_by, applies))

    # The opt-in outer alpha search (record 0.24.0), dotted like ``solver``
    # and listed only where the configuration asked for it.
    search = config.get("alpha_search")
    if isinstance(search, Mapping):
        for key in sorted(search):
            name = f"alpha_search.{key}"
            rows.append(
                _row(name, "run", search[key],
                     pointer_join("/payload/config/alpha_search", key),
                     run_specs.get(name), bound_by, None)
            )

    # The solver block, dotted; its ``advanced`` block (record 0.43.0) one
    # level deeper, so each expert choice is a row of its own.
    solver = config.get("solver")
    if isinstance(solver, Mapping):
        for key in sorted(solver):
            advanced = solver[key]
            if key == "advanced" and isinstance(advanced, Mapping):
                tier = pointer_join("/payload/config/solver", key)
                for inner in sorted(advanced):
                    name = f"solver.advanced.{inner}"
                    rows.append(
                        _row(name, "solver", advanced[inner],
                             pointer_join(tier, inner), run_specs.get(name),
                             bound_by, None)
                    )
                continue
            name = f"solver.{key}"
            spec = run_specs.get(name)
            rows.append(
                _row(name, "solver", solver[key],
                     pointer_join("/payload/config/solver", key), spec, bound_by,
                     None)
            )

    specs = _instance_specs(record)
    table = {str(spec["name"]): spec for spec in specs}
    prepared = prepared_inputs(record)
    blocks: dict[Section, Mapping[str, Any]] = {}
    device_sections: tuple[Section, ...] = ("model", "device")
    for section in device_sections:
        found = config.get(section)
        blocks[section] = found if isinstance(found, Mapping) else {}
    declared: dict[str, Any] = {**blocks["model"], **blocks["device"]}
    for section, block in blocks.items():
        section_name = str(section)
        listed: set[str] = set()
        for key in sorted(block):
            spec = table.get(key)
            row = _row(f"{section_name}.{key}", section, block[key],
                       pointer_join("/payload/config", section_name, key), spec,
                       bound_by, _applies(spec, declared, table) if spec else None)
            if key in prepared:
                row["prepared"] = prepared[key][0]
            rows.append(row)
            listed.add(key)
        for index, spec in enumerate(specs):
            name = str(spec["name"])
            if spec.get("section") != section_name or name in listed:
                continue
            rows.append(
                _row(f"{section_name}.{name}", section, spec.get("default"),
                     pointer_join("/payload/instance/parameters", index, "default"),
                     spec, bound_by, _applies(spec, declared, table))
            )
    return rows


def _row(
    name: str,
    section: Section,
    value: Any,
    pointer: str,
    spec: Mapping[str, Any] | None,
    bound_by: Mapping[str, Sequence[str]],
    applies: bool | None,
) -> InputRow:
    """Return one input row, its meaning and domain read from ``spec``."""
    default = None if spec is None else spec.get("default")
    return {
        "name": name,
        "section": section,
        "value": value,
        "default": default,
        "is_default": None if spec is None else value == default,
        "unit": None if spec is None else spec.get("unit"),
        "quantity": None if spec is None else spec.get("quantity"),
        "domain": None if spec is None else spec.get("domain"),
        "meaning": None if spec is None else spec.get("meaning"),
        "applies": applies,
        "station": None if spec is None else spec.get("station"),
        "snapped": None if spec is None else spec.get("snapped"),
        "pointer": pointer,
        "bound_by": sorted(set(bound_by.get(name, ()))),
        "covered_by": [],
        "group": input_group(name, section),
        "label": input_label(name),
        "not_used": _not_used(spec) if applies is False else None,
        "prepared": None,
    }


def input_row_name(binding_name: str, rows: Iterable[str]) -> str | None:
    """Return the input row a binding name refers to, or ``None``.

    A binding names an input by its row name or the configuration's bare
    name (``eps_auth``, ``rounds``, ``qber``); the row is the first of the
    name itself, its :func:`parameter_alias`, and its ``model.`` and
    ``device.`` spellings that exists. ``alpha`` is the run-level row and
    ``parameters.alpha`` the key-length one.
    """
    names = set(rows)
    for candidate in (
        binding_name,
        parameter_alias(binding_name),
        f"model.{binding_name}",
        f"device.{binding_name}",
    ):
        if candidate is not None and candidate in names:
            return candidate
    return None


def build_facts(record: Mapping[str, Any]) -> list[Fact]:
    """Return the route facts the record holds, each with its pointer."""
    facts: list[Fact] = []
    for name, pointer in FACT_POINTERS:
        value = resolve_pointer(record, pointer, _MISSING)
        if value is _MISSING or value is None:
            continue
        facts.append({"name": name, "value": value, "pointer": pointer})
    stations = resolve_pointer(record, "/payload/stages/stations", None)
    if isinstance(stations, list):
        facts.append(
            {"name": "stations", "value": len(stations),
             "pointer": "/payload/stages/stations"}
        )
    return facts
