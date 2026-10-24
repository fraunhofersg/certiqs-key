"""The key-rate report's checks: the conditions the engine decided on a run.

WHY THIS EXISTS. An evaluator asks which conditions were checked rather than
assumed (CC Part 1 7.1.4: an assumption is "not tested in any way"). An
engine-decided condition is a definition plus a requirement rather than
an assumption, so the report lists those decisions here, each with the claims
that state it, the decided datum where the record holds one and a JSON
Pointer to the evidence. The receiver's route is the first of them.

THE TABLE IS DATA. :data:`CHECKS` is ordered by the stage of the run that
decides each check (:class:`~certiqs_key.runs.stages.SliceStage` order), which
is what lets a refused record mark the refusing check ``refused`` and every
later one ``not-reached``. The refusal codes a check answers for are the
owning modules' own enum members, imported, so a code that does not exist
cannot be named here. Every claim id is one the closure table carries
(``tests/unit/test_report_checks.py``).

OUTCOMES. ``passed``: the run went past the check and, where the record holds
the decided datum, it is shown. ``failed``: a check that withholds an output
rather than refusing the run (a closed key-length gate, no contributing
iterate) did not open; the run continued without the output it gates.
``refused``: the run stopped here. ``not-applicable``: the route does not
take the check, or the record holds nothing it decides on. ``not-reached``:
the run stopped before it, or at a stage the record does not name.

A REFUSED RECORD (``build.py``): the check the refusal code belongs to reads
``refused``; a check before it (or, when no check owns the code, before the
refusing stage) reads ``not-applicable`` where its evaluation on the record
says so and ``passed`` otherwise, or ``not-reached`` where its evaluation finds the
check was never reached (a receiver route on a record refused at compilation
with no receiver stage); every other check reads ``not-reached``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Final

from certiqs_key.meat_core.reasons import RefusalReason as MeatRefusal
from certiqs_key.protocol_compiler.reasons import RefusalReason as CompilerRefusal
from certiqs_key.receiver.reasons import RefusalReason as ReceiverRefusal
from certiqs_key.runs.report.inputs import preparation_moves, resolve_pointer
from certiqs_key.runs.report.model import CheckOutcome
from certiqs_key.runs.stages import SliceStage
from certiqs_key.statistics.reasons import InfeasibilityReason

__all__ = [
    "CHECKS",
    "CHECK_CLAIMS",
    "CheckSpec",
    "Evaluation",
    "stage_index",
]

#: ``(outcome, value, pointer)`` of a check on a completed record.
type Evaluation = tuple[CheckOutcome, Any, str | None]

_KEY_RATE = "/payload/stages/key_rate"
_RECEIVER = "/payload/stages/receiver_construction"
_ACCEPTANCE = "/payload/stages/acceptance_construction"


@dataclass(frozen=True)
class CheckSpec:
    """One check: its stable id, one-line title, claims, stage, refusal codes."""

    id: str
    title: str
    claims: tuple[str, ...]
    #: The :class:`SliceStage` value that decides it; ``None`` for what the
    #: instance decides before the first stage (its snaps).
    stage: str | None
    #: The owning module's refusal codes that mean THIS check refused the run.
    reasons: frozenset[str]
    evaluate: Callable[[Mapping[str, Any]], Evaluation]


def stage_index(stage: str | None) -> int:
    """Return a stage's position on the path; ``-1`` before the first stage."""
    if stage is None:
        return -1
    order = [str(member) for member in SliceStage]
    return order.index(stage) if stage in order else len(order)


def _get(record: Mapping[str, Any], pointer: str) -> Any:
    return resolve_pointer(record, pointer, None)


def _receiver_route(record: Mapping[str, Any]) -> tuple[Any, str | None]:
    """Return the receiver route and its pointer: ``receiver_route``, else ``route``."""
    for field in ("receiver_route", "route"):
        pointer = f"{_RECEIVER}/{field}"
        value = _get(record, pointer)
        if value is not None:
            return value, pointer
    return None, None


def _snaps(record: Mapping[str, Any]) -> Evaluation:
    """Decide the snaps against tau: the measurement blocks' and the instance's.

    The record's ``snap_max_defect`` covers the measurement blocks only, so a
    probability family the instance moved before the run (a protocol
    document's ``snap.groups``, :func:`preparation_moves`) is tested too: its
    normalization defect, the one ``tau`` admits it with, beside the
    measurement blocks'. The value keeps the record's field as it states it
    and names the moves by site under keys of their own, so that a run whose
    inputs moved does not read as one where nothing was snapped; a family
    admitted by its float rounding cells is named as left out of the test.
    """
    snaps = _get(record, "/payload/snaps")
    if not isinstance(snaps, Mapping):
        return "not-applicable", None, None
    defect = snaps.get("snap_max_defect")
    tolerance = snaps.get("declared_tolerance")
    if tolerance is None:
        tolerance = _get(record, "/payload/config/declared_tolerance")
    moves = preparation_moves(record)
    # A family admitted by its float rounding cells rather than by tau
    # (runs/inputs.py prepare_probabilities) has a defect tau does not bound,
    # so it is left out of the test, and the value says so.
    bounded = [
        *([] if defect is None else [defect]),
        *(move["normalization_defect"] for move in moves
          if move["normalization_defect"] is not None
          and move["admission"] != "float_rounding_cells"),
    ]
    # The record's field as it states it; the input moves under their own.
    value: dict[str, Any] = {"snap_max_defect": defect,
                             "declared_tolerance": tolerance}
    if moves:
        defects = [move["normalization_defect"] for move in moves
                   if move["normalization_defect"] is not None]
        value["inputs_moved"] = {move["site"]: move["displacement"] for move in moves}
        value["input_normalization_defect"] = max(defects) if defects else None
        excluded = [move["site"] for move in moves
                    if move["admission"] == "float_rounding_cells"]
        if excluded:
            value["not_tested_against_tau"] = dict.fromkeys(
                excluded, "admitted by its float rounding cells")
    within = not bounded or (
        tolerance is not None and max(bounded) <= tolerance
    )
    return ("passed" if within else "failed"), value, "/payload/snaps"


def _route(record: Mapping[str, Any]) -> Evaluation:
    """Return the receiver route; ``not-reached`` where no route was taken.

    A record refused at its compilation stage with no receiver stage on its
    path (Band A's declared POVM, whose route the compiled specification
    fixes) never reached a route, so the check is not passed. A run refused
    while building its receiver, or past compilation, took one even where its
    refused record does not name it.
    """
    value, pointer = _receiver_route(record)
    if value is None and _refused_at(record) == str(SliceStage.COMPILATION) and (
        not _on_path(record, str(SliceStage.RECEIVER_CONSTRUCTION))
    ):
        return "not-reached", None, None
    return "passed", value, pointer


def _refused_at(record: Mapping[str, Any]) -> str | None:
    """Return the stage a refused record names as refusing, else ``None``."""
    if not _get(record, "/payload/refused"):
        return None
    stages = _get(record, "/payload/stages")
    for stage, entry in (stages.items() if isinstance(stages, Mapping) else ()):
        if isinstance(entry, Mapping) and entry.get("refused") is True:
            return str(stage)
    return None


def _on_path(record: Mapping[str, Any], stage: str) -> bool:
    """Whether the record's composition flow or stages name ``stage``."""
    if _get(record, f"/payload/stages/{stage}") is not None:
        return True
    flow = _get(record, "/payload/composition_flow/stages")
    return any(
        isinstance(item, Mapping) and item.get("stage") == stage
        for item in (flow if isinstance(flow, list) else ())
    )


def _graph(record: Mapping[str, Any]) -> Evaluation:
    value, pointer = _receiver_route(record)
    if value != "element-graph":
        return "not-applicable", value, pointer
    return "passed", value, pointer


def _probe(record: Mapping[str, Any]) -> Evaluation:
    modes = _get(record, f"{_RECEIVER}/modes")
    probes = [
        mode for mode in modes or ()
        if isinstance(mode, Mapping) and mode.get("role") == "probe"
    ]
    if not probes:
        return "not-applicable", None, None
    return "passed", len(probes), f"{_RECEIVER}/modes"


def _stage_passed(pointer: str) -> Callable[[Mapping[str, Any]], Evaluation]:
    def evaluate(record: Mapping[str, Any]) -> Evaluation:
        found = _get(record, pointer)
        return "passed", None, pointer if found is not None else None

    return evaluate


def _alphabet(record: Mapping[str, Any]) -> Evaluation:
    outcomes = _get(record, f"{_ACCEPTANCE}/outcomes")
    if outcomes is None:
        return "passed", None, None
    return "passed", list(outcomes), f"{_ACCEPTANCE}/outcomes"


def _statistics_inputs(record: Mapping[str, Any]) -> Evaluation:
    geometry = _get(record, f"{_ACCEPTANCE}/geometry")
    if isinstance(geometry, str) and "singleton" in geometry.lower():
        return "not-applicable", geometry, f"{_ACCEPTANCE}/geometry"
    pointer = f"{_ACCEPTANCE}/geometry" if geometry is not None else None
    return "passed", geometry, pointer


def _admission(record: Mapping[str, Any]) -> Evaluation:
    return "passed", None, _KEY_RATE if _get(record, _KEY_RATE) is not None else None


def _alpha(record: Mapping[str, Any]) -> Evaluation:
    pointer = f"{_KEY_RATE}/alpha"
    value = _get(record, pointer)
    if value is None:
        pointer = "/payload/config/parameters/alpha"
        value = _get(record, pointer)
    return "passed", value, pointer


def _budgets(record: Mapping[str, Any]) -> Evaluation:
    parameters = _get(record, "/payload/config/parameters") or {}
    value = {
        name: parameters.get(name) for name in ("eps_pa", "eps_ev", "eps_auth")
    }
    return "passed", value, "/payload/config/parameters"


def _key_gate(record: Mapping[str, Any]) -> Evaluation:
    pointer = f"{_KEY_RATE}/security_gates/key_length_permitted"
    permitted = _get(record, pointer)
    if permitted is None:
        return "not-applicable", None, None
    return ("passed" if permitted else "failed"), permitted, pointer


def _first_order(record: Mapping[str, Any]) -> Evaluation:
    gates = _get(record, f"{_KEY_RATE}/per_iterate")
    if not isinstance(gates, list):
        return "not-applicable", None, None
    contributing = sum(
        1 for gate in gates
        if isinstance(gate, Mapping) and gate.get("withdrawal") is None
    )
    value = {"contributing": contributing, "withdrawn": len(gates) - contributing}
    return (
        ("passed" if contributing else "failed"),
        value,
        f"{_KEY_RATE}/per_iterate",
    )


def _reported_length(record: Mapping[str, Any]) -> Evaluation:
    pointer = f"{_KEY_RATE}/key_length"
    length = _get(record, pointer)
    if length is None:
        return "not-applicable", None, None
    return "passed", length, pointer


def _codes(*members: object) -> frozenset[str]:
    return frozenset(str(member) for member in members)


#: THE CHECK TABLE, in stage order. Titles are one line each, run-tier labels.
CHECKS: Final[tuple[CheckSpec, ...]] = (
    CheckSpec(
        id="snaps-within-tolerance",
        title="Instance snaps within the declared tolerance",
        claims=(),
        stage=None,
        reasons=frozenset(),
        evaluate=_snaps,
    ),
    CheckSpec(
        id="receiver-route",
        title="Receiver route",
        claims=("receiver/def:compile",),
        stage=str(SliceStage.RECEIVER_CONSTRUCTION),
        reasons=frozenset(),
        evaluate=_route,
    ),
    CheckSpec(
        id="element-graph-acyclic",
        title="Declared element graph well formed",
        claims=("receiver/def:graph", "receiver/req:graph-refusal"),
        stage=str(SliceStage.RECEIVER_CONSTRUCTION),
        reasons=_codes(
            ReceiverRefusal.GRAPH_CONDITION_E1_FAILED,
            ReceiverRefusal.GRAPH_CONDITION_E2_FAILED,
            ReceiverRefusal.GRAPH_CONDITION_E3_FAILED,
        ),
        evaluate=_graph,
    ),
    CheckSpec(
        id="probe-states-diagonal",
        title="Probe declaration admitted",
        claims=("receiver/def:probe", "receiver/req:probe-diagonal-admission"),
        stage=str(SliceStage.RECEIVER_CONSTRUCTION),
        reasons=_codes(
            ReceiverRefusal.PROBE_ALPHABET_EMPTY,
            ReceiverRefusal.PROBE_ALPHABET_LABEL_REPEATED,
            ReceiverRefusal.PROBE_SETTING_OFF_MISSING,
            ReceiverRefusal.PROBE_MEAN_PHOTON_NUMBER_NEGATIVE,
            ReceiverRefusal.PROBE_DECLARED_WITHOUT_SOURCE_MODES,
            ReceiverRefusal.PROBE_CONDITIONING_SUBMODULE_ABSENT,
        ),
        evaluate=_probe,
    ),
    CheckSpec(
        id="specification-well-formed",
        title="Specification well formed",
        claims=(
            "protocol-compiler/def:well-formed-spec",
            "protocol-compiler/thm:validator-soundness",
        ),
        stage=str(SliceStage.COMPILATION),
        reasons=_codes(
            CompilerRefusal.CHECK_V1_FAILED,
            CompilerRefusal.CHECK_V2_FAILED,
            CompilerRefusal.CHECK_V3_FAILED,
            CompilerRefusal.CHECK_V4_FAILED,
            CompilerRefusal.CHECK_V5_FAILED,
            CompilerRefusal.CHECK_V6_FAILED,
            CompilerRefusal.CHECK_V8_FAILED,
        ),
        evaluate=_stage_passed("/payload/stages/compilation"),
    ),
    CheckSpec(
        id="compiler-gates",
        title="Compiler emission gates",
        claims=("protocol-compiler/thm:gates",),
        stage=str(SliceStage.COMPILATION),
        reasons=_codes(
            CompilerRefusal.GATE_G1_FAILED,
            CompilerRefusal.GATE_G2_FAILED,
            CompilerRefusal.GATE_G3A_FAILED,
            CompilerRefusal.GATE_G3B_FAILED,
        ),
        evaluate=_stage_passed("/payload/compiled"),
    ),
    CheckSpec(
        id="exact-statistics-inputs",
        title="Acceptance-set inputs admissible",
        claims=("statistics/binomial-box/req:input-refusal",),
        stage=str(SliceStage.ACCEPTANCE_CONSTRUCTION),
        reasons=frozenset(str(member) for member in InfeasibilityReason),
        evaluate=_statistics_inputs,
    ),
    CheckSpec(
        id="matched-alphabet",
        title="Acceptance alphabet matches the declaration",
        claims=("statistics/req:matched-alphabet",),
        stage=str(SliceStage.ACCEPTANCE_CONSTRUCTION),
        reasons=frozenset(),
        evaluate=_alphabet,
    ),
    CheckSpec(
        id="declaration-admitted",
        title="Declaration exactly admissible",
        claims=("meat-core/req:exact-admission",),
        stage=str(SliceStage.SOLVE),
        reasons=_codes(MeatRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE),
        evaluate=_admission,
    ),
    CheckSpec(
        id="alpha-range",
        title="Rényi order of the key length",
        # The requirement that takes the place of an A-ALPHA assumption.
        claims=("meat-core/req:key-length-alpha-domain",),
        stage=str(SliceStage.SOLVE),
        reasons=frozenset(),
        evaluate=_alpha,
    ),
    CheckSpec(
        id="security-statement-not-vacuous",
        title="Security statement not vacuous",
        claims=("meat-core/req:security-statement-not-vacuous",),
        stage=str(SliceStage.SOLVE),
        reasons=_codes(MeatRefusal.SECURITY_STATEMENT_VACUOUS),
        evaluate=_budgets,
    ),
    CheckSpec(
        id="key-length-gate",
        title="Key-length security gates",
        claims=(
            "meat-core/req:constrained-key-gate",
            "meat-core/req:marginal-licence-gate",
            "meat-core/thm:constrained-accumulation",
        ),
        stage=str(SliceStage.SOLVE),
        reasons=frozenset(),
        evaluate=_key_gate,
    ),
    CheckSpec(
        id="first-order-hypotheses",
        title="First-order hypotheses at the contributing iterates",
        claims=(
            "meat-core/frank-wolfe/req:first-order-withdrawal",
            "meat-core/frank-wolfe/thm:firstorder",
        ),
        stage=str(SliceStage.SOLVE),
        reasons=frozenset(),
        evaluate=_first_order,
    ),
    CheckSpec(
        id="reported-key-length",
        title="Reported key length",
        claims=("meat-core/req:reported-key-length",),
        stage=str(SliceStage.SOLVE),
        reasons=frozenset(),
        evaluate=_reported_length,
    ),
)

#: Every claim id the check table cites, in table order, without repeats.
CHECK_CLAIMS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(claim for check in CHECKS for claim in check.claims)
)
