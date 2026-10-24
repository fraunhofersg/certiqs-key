"""The key-rate report as JSON-native types: what a renderer and an MCP tool read.

WHY THIS EXISTS. A key-rate report must answer what
a security evaluation asks of a claimed key rate. The record is the authority;
the report is a pure projection of it. These types fix the projection's shape
so that every renderer and adapter reads one object
and none of them assembles assumption text of its own.

PRESENTATION-FREE. Every field is data or the claims' own plain text (title,
summary, ``user_statement``), copied from the record's snapshot or the shipped
closure table. No HTML, Markdown or display wording lives here; the only
ordering is the semantic one (section order, the table's category order).

One helper lives here beside the types, :func:`group_entries`, the one way
the builder, the renderers and :func:`~certiqs_key.runs.report.select` flatten
category groups into entries.

``report.schema.json`` beside this file is the hand-written JSON Schema of the
same shape (the house rule of ``runs/record.schema.json``: written by hand,
validated by a test, never generated from these types).
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, Required, TypedDict

__all__ = [
    "AcceptanceCategory",
    "AlphaBound",
    "AlphaEvaluationRow",
    "AlphaSearchDetail",
    "AlphaUsed",
    "AssumptionEntry",
    "AssumptionsSection",
    "Binding",
    "CategoryGroup",
    "Check",
    "CheckOutcome",
    "ChecksSection",
    "ClaimRef",
    "CommonPart",
    "Completeness",
    "ConsequenceCounts",
    "ContractAnchor",
    "Deductions",
    "Detector",
    "DiagnosticRow",
    "Discrepancy",
    "DocumentInfo",
    "Emission",
    "EmissionSnap",
    "ExpectedStatistic",
    "Fact",
    "Family",
    "Flag",
    "GlanceItem",
    "Guarantee",
    "GuaranteeTerm",
    "HonestModel",
    "InputRow",
    "InstanceInfo",
    "KeyRateReport",
    "MatrixEntry",
    "MeasurementSnaps",
    "NoPositiveKey",
    "NotEngaged",
    "NumericsSection",
    "OperatorBlock",
    "OperatorElement",
    "OperatorFamily",
    "OpticalElement",
    "Outcome",
    "OutcomeLetter",
    "Points",
    "Preparation",
    "ProtocolSection",
    "ProtocolStep",
    "ProvenanceSection",
    "Refusal",
    "ReportIndex",
    "ResultSection",
    "RoundBlock",
    "RoundPremise",
    "RouteDelta",
    "Sections",
    "SecurityParameter",
    "SetupAcceptance",
    "SetupSection",
    "SetupSource",
    "SetupStation",
    "SnapBlock",
    "SnapRow",
    "SolverAttempt",
    "StatisticsCheck",
    "Summary",
    "SummaryItem",
    "SweepPoint",
    "SweepReport",
    "UserDeclared",
    "VouchGroup",
    "VouchLine",
    "group_entries",
]

#: What a run produced: a key length, a completed run without one, a refusal.
type Outcome = Literal["key-length", "no-key-length", "refused"]

#: A check's outcome on one run (``checks.py`` says what each means).
type CheckOutcome = Literal[
    "passed", "failed", "refused", "not-applicable", "not-reached"
]

#: WHERE A SWEEP ROW HOLDS: ``"all"`` (every completed point), or the indices
#: of the points that carry it. Only a sweep's rows carry it.
type Points = Literal["all"] | list[int]


class ContractAnchor(TypedDict):
    """Where a claim's statement is: the contract PDF and its named destination."""

    pdf: str
    anchor: str


class ClaimRef(TypedDict):
    """A linked claim: its plain title and summary, its status and its anchor."""

    id: str
    kind: str
    kind_word: str
    title: str
    summary: str
    #: The claim's plain reading for a user, where it carries one (0.9.0).
    user_statement: str | None
    status: str
    effective_status: str
    contract: ContractAnchor


class Binding(TypedDict, total=False):
    """One declared value an assumption's clauses are about.

    Exactly one of ``value`` (inline) and ``input`` (a named input of the
    protocol section) is present; ``pointer`` is the JSON Pointer of the value
    in the record where the run tier can name it. ``varies`` appears only in a
    sweep's common part, for a binding whose value differs between points.
    """

    name: Required[str]
    value: Any
    input: str
    pointer: str
    varies: bool
    emitted_by: Required[list[str]]


class Emission(TypedDict):
    """One emitter of an assumption's row on this run."""

    module: str
    station: int | None
    #: The party of a row emitted once per party (A-LAB; record 0.30.0),
    #: ``None`` elsewhere (0.17.0).
    party: str | None
    machine_key: str
    inherited_from: str | None


class AssumptionEntry(TypedDict):
    """One assumption of the run, as the record's snapshot carries it."""

    short_id: str
    owner: ClaimRef
    machine_key: str
    category: str | None
    affects: list[str] | None
    refines: str | None
    verification: str
    verification_sentence: str
    user_statement: str | None
    bindings: list[Binding]
    emitted_by: list[Emission]
    #: What the premise is about, in words: "Bob's station", "Your source"
    #: (0.9.0; :func:`certiqs_key.runs.report.explain.about`).
    about: str
    #: What fails if the premise fails, one phrase per ``affects`` (0.9.0).
    at_stake: list[str]
    #: The current closure table's text of the premise where it differs from
    #: the text frozen in the record, else ``None`` (0.10.0; a record made by an
    #: older engine).
    current_text: str | None
    #: The run-specific lines printed beside the premise (0.18.0): "Not on this
    #: run: ..." for its role-conditioned clauses whose condition fails here,
    #: and A-KEYREG's record of the key holder
    #: (:func:`certiqs_key.runs.report.explain.role_notes`).
    role_notes: list[str]
    points: NotRequired[Points]


class Family(TypedDict):
    """An assumption with the present members that refine it, or one standing alone."""

    head: AssumptionEntry
    members: list[AssumptionEntry]


class CategoryGroup(TypedDict):
    """The families of one category, in the table's category order."""

    category: str | None
    families: list[Family]


class NotEngaged(TypedDict, total=False):
    """A closure member a ran module's emission rule excluded on this route."""

    short_id: Required[str]
    module: Required[str]
    reason: Required[str]
    discharged_by: str
    points: Points


class Discrepancy(TypedDict):
    """A disagreement between the ledger rows and the claim closure."""

    short_id: str
    kind: str
    emitted_by: Any
    detail: Any
    points: NotRequired[Points]


class UserDeclared(TypedDict):
    """A premise the protocol document supplied itself (record schema 0.21.0).

    Declared in the run's protocol document (the user's own or a shipped
    template), not derived by the engine; the user vouches for it. Copied
    from the record's ``protocol_document.user_declared``: an explicit
    constraint entry, attack-set licence or feasibility witness, a declared
    receiver POVM, a declared receiver characterisation (port Grams, an
    instrument matrix, a C10 block, a dark-count channel), or a retention
    attestation. ``text`` is the document
    layer's own sentence; ``assumptions`` the short ids it stands under
    (empty for a witness); ``pointer`` where the record holds it.
    """

    kind: str
    path: str
    label: str
    text: str
    assumptions: list[str]
    pointer: str
    points: NotRequired[Points]


class AssumptionsSection(TypedDict):
    """R3: the premises the user vouches for, grouped by category and family."""

    groups: list[CategoryGroup]
    not_engaged: list[NotEngaged]
    discrepancies: list[Discrepancy]
    #: Every premise the run's protocol document (the user's own or a shipped
    #: template) supplied itself, not derived by the engine and vouched for
    #: by the user, each naming the assumption it stands under (0.3.0).
    user_declared: list[UserDeclared]


class AlphaEvaluationRow(TypedDict):
    """One run of the outer alpha search, as the record's ``alpha`` child lists it."""

    alpha: float
    #: ``coarse`` or ``refine``.
    phase: str
    key_length: int | None
    h_lb: float | None
    #: What the search ranked; ``None`` on a run without a key length.
    score: float | None
    reason: str | None
    seconds: float
    #: Why the search set this evaluation aside (its bracket stayed wide), or
    #: ``None`` (record 0.34.0; report 0.24.0).
    set_aside: str | None


class AlphaUsed(TypedDict):
    """The Renyi order of a run's key length, and what chose it (0.6.0).

    ``chosen_by`` is ``outer-search`` where the run tier's opt-in search chose
    it (the record's configuration carries ``alpha_search``), ``configuration``
    where the configuration fixed ``alpha``, and ``declaration`` where the run
    solved at ``parameters.alpha``. ``value`` is the key-rate result's own
    alpha; without one, the search's chosen alpha (``None`` where it chose
    none) or the configured or declared order.
    """

    value: float | None
    chosen_by: Literal["outer-search", "configuration", "declaration"]
    #: ``[1 + lower, 1 + upper]``, the alpha interval searched; search only.
    searched_range: list[float] | None
    #: How many runs the search made; search only.
    runs: int | None
    #: Where the record holds the value.
    pointer: str | None
    #: Where the outer search found no alpha with a positive key length, why
    #: (the record's ``no_positive_key.reason``, record 0.40.0); else ``None``.
    #: ``value`` is then the alpha of the evaluation with the largest h_low,
    #: which the run reports (report 0.32.0).
    no_positive_key: str | None


class AlphaBound(TypedDict):
    """A bound the alpha search saw, and the alpha it was formed at."""

    alpha: float
    h_lb: float


class NoPositiveKey(TypedDict):
    """The alpha search's outcome where no alpha gave a key (record 0.40.0).

    The run reported is the evaluation with the largest ``h_low``; the largest
    bounds are diagnostics, ``largest_h_lb_searched`` the bound on the
    declaration the solve searched where the reported ``h_lb`` is the
    reference companion's (report 0.32.0).
    """

    reported_alpha: float
    h_low: float | None
    largest_h_lb: AlphaBound | None
    largest_h_lb_searched: AlphaBound | None
    reason: str


class AlphaSearchDetail(TypedDict):
    """The outer alpha search behind a run, every evaluation included (0.6.0)."""

    #: The record's search block: the solve stage's ``alpha`` child detail.
    pointer: str
    rule: str | None
    reads: str | None
    settings: dict[str, Any]
    chosen_alpha: float | None
    evaluations: list[AlphaEvaluationRow]
    #: Why the refinement stopped before its steps were spent, or ``None``
    #: (record 0.34.0; report 0.24.0).
    refinement_stopped: str | None
    #: Where no alpha gave a positive key length, the search's outcome, or
    #: ``None`` (record 0.40.0; report 0.32.0).
    no_positive_key: NoPositiveKey | None


class DiagnosticRow(TypedDict):
    """One solver diagnostic with its readable name and its reading (0.9.0)."""

    name: str
    label: str
    value: Any
    explanation: str | None
    pointer: str | None


class SolverAttempt(TypedDict):
    """How one attempt of the candidate search stopped (0.9.0)."""

    method: str
    termination: str
    iterations: int | None
    seconds: float | None
    bound_after: float | None
    #: Why a corrective probe series stopped after this probe (``target_met``,
    #: ``stage_deadline``, ``no_bracket_progress``, ``search_<termination>``),
    #: or ``None`` where it continued or the attempt is no probe (0.24.0).
    stop_reason: str | None
    #: Whether the attempt resumed a stage that had stopped before its budget
    #: was spent; ``None`` where the record does not say (0.24.0).
    resumed: bool | None


class NumericsSection(TypedDict):
    """R4: the trusted engine numerics and the solve's diagnostics."""

    entries: list[AssumptionEntry]
    diagnostics: dict[str, Any]
    #: The diagnostics with a readable name and a reading each (0.9.0).
    explained: list[DiagnosticRow]
    #: Every attempt of the candidate search, where the record lists them.
    solver_attempts: list[SolverAttempt]
    #: How the search stopped as a whole: the gap target met or not, how the
    #: attempts ended, the time used of the budget and an iteration cap that
    #: ended a stage; ``None`` without a search report (0.24.0).
    solve_stop: str | None
    #: The outer alpha search behind the run, or ``None`` for a run at one
    #: alpha and in a sweep's common part (0.6.0).
    alpha_search: AlphaSearchDetail | None


class Check(TypedDict):
    """One condition the engine decided on this run (R5)."""

    id: str
    title: str
    claims: list[ClaimRef]
    #: ``varies`` only in a sweep, where ``point_outcomes`` then gives each
    #: point's outcome in point order.
    outcome: CheckOutcome | Literal["varies"]
    value: Any
    pointer: str | None
    value_varies: NotRequired[bool]
    point_outcomes: NotRequired[list[CheckOutcome]]


class ChecksSection(TypedDict):
    """R5: the checks, the decided rows still emitted, the route-discharged rows."""

    checks: list[Check]
    decided_rows: list[AssumptionEntry]
    discharged_on_route: list[NotEngaged]


class Flag(TypedDict):
    """A run parameter left at a zero default that the key length does not count."""

    id: str
    parameter: str
    value: Any
    text: str
    assumptions: list[str]
    #: Sweep only: the completed points that raise it, ``"all"`` or indices.
    points: NotRequired[Points]


class Refusal(TypedDict):
    """The refusing stage with its module's own reason code."""

    stage: str
    reason: str | None
    detail: str | None
    rule: Any
    #: The numbers a solve-stage refusal's record holds under
    #: ``stages.solve.plausibility`` (0.32.0): ``bound_name``, ``bound`` and
    #: ``h_low``; absent where the record holds none.
    plausibility: NotRequired[dict[str, Any]]


class SecurityParameter(TypedDict):
    """The composed security parameter as recorded; never computed here."""

    value: float | None
    terms: dict[str, Any]
    auth_factor: int


class Completeness(TypedDict):
    """The completeness figure as the acceptance construction certified it."""

    eps_star: str | None
    claim: ClaimRef


class Deductions(TypedDict):
    """The bits the key length deducts and adds back, as the record states them.

    The record's ``key_rate.deductions``, term by term
    (``meat-core/thm:keylength``, Eq. ``eq:keylength``); ``None`` for a term
    the record does not carry.
    """

    error_correction: float | None
    error_verification: float | None
    privacy_amplification: float | None
    #: The one bit the theorem adds back.
    added_back: float | None
    #: The engine's further deduction for a hash not declared ideal.
    hash_penalty: float | None
    pointer: str


class StatisticsCheck(TypedDict):
    """The check of the acceptance set against the feasible statistics (0.26.0).

    Read from the record's ``statistics_consistency`` in its 0.46.0 shape
    (``meat-core/req:unreachable-acceptance-set`` (iv), (v); report 0.36.0):
    the bound ``b`` with its tier, the cap's exponent ``x`` with its tier and
    how item (iv) decided, ``tau``, why there is no cap where there is none,
    and whether the run was refused, decided on the exact ``x``. The
    per-order diagnostic ``n f`` is not read: the report does not show it.
    """

    checked: bool
    #: ``out_of_scope`` or ``opted_out`` where not checked.
    unchecked_reason: str | None
    bound: float | None
    bound_tier: str | None
    alpha_0: float | None
    #: Why no bound was formed, where the run is checked and none was.
    no_bound_reason: str | None
    #: ``x`` of ``meat-core/prop:model-pass-bound`` (ii), rounded toward
    #: ``-inf``: devices as declared pass the test with probability at most
    #: ``2^(-x)`` (0.35.0; record 0.45.0). ``None`` where ``b <= 0``, no
    #: bound was formed, or the record is older.
    model_pass_exponent_bits: float | None
    #: The tier of ``b`` that ``x`` is formed from, with it.
    model_pass_exponent_tier: str | None
    #: How item (iv) decided ``x >= log2(1/tau)``: ``exact``, ``enclosure`` or
    #: ``undecided`` (which refuses); ``None`` where there is no cap (0.36.0).
    model_pass_decision: str | None
    #: ``tau``, ``"p/q"`` (0.36.0).
    min_model_pass_probability: str | None
    #: ``bound_not_positive`` or ``no_bound_formed`` where a checked run whose
    #: solve ran has no cap (0.36.0).
    no_cap_reason: str | None
    #: Whether item (iv) refused the run, as decided on the exact ``x``.
    refused: bool
    #: Whether a reference companion was admitted for the run (the record's
    #: ``key_rate.reference_bracket`` status ``counted`` or ``withdrawn``):
    #: the cap is then that of the declaration the solver searched, not the
    #: companion's (0.36.0).
    companion_admitted: bool
    pointer: str


class ResultSection(TypedDict):
    """R1: the result and the security statement it is an instance of."""

    outcome: Outcome
    refusal: Refusal | None
    key_length: int | None
    net_key_length: int | None
    rate_per_round: float | None
    rounds: int | None
    #: The Renyi order the key length is at, and what chose it (0.6.0).
    alpha: AlphaUsed
    reported_tier: str | None
    #: On a run reported at the certified tier, the declaration its number is
    #: formed on, ``reference_companion`` or ``searched``, and whether that is
    #: the fallback of ``meat-core/frank-wolfe/req:certified-evaluation`` (i)
    #: (0.22.0; record 0.35.0). ``None`` and ``False`` on any other run or an
    #: older record.
    certified_on: str | None
    certified_fallback: bool
    #: The premise at the snap that number rests on, the record's
    #: ``certified.premises`` (``["A-SNAP"]`` or empty; 0.22.0).
    certified_premises: list[str]
    key_length_reason: str | None
    key_length_reason_code: str | None
    reason_text: str | None
    security_parameter: SecurityParameter
    completeness: Completeness | None
    statement_claims: list[ClaimRef]
    #: The route theorems of the run's assumption manifest (its ``roots``)
    #: whose effective status is below accepted, which the review-status
    #: paragraph names (0.21.0); empty where every one is.
    route_claims_below_accepted: list[ClaimRef]
    #: Whether the manifest names route theorems and every one is at an
    #: accepted effective status (0.33.0).
    route_claims_accepted: bool
    per_execution: list[ClaimRef]
    #: Raised only when the outcome is ``key-length``: each flag qualifies a
    #: number that exists only beside a key length.
    not_counted: list[Flag]
    #: What the protocol document declared that the engine did not derive
    #: (0.3.0); empty off the document route and on a 0.20.0 record.
    user_declared: list[UserDeclared]
    limitations: list[ClaimRef]
    #: The check of the acceptance set against the feasible statistics
    #: (0.26.0; record 0.37.0); ``None`` on an older record.
    statistics_check: StatisticsCheck | None
    #: What the key length deducts for post-processing (0.28.0); ``None``
    #: where the record carries no deductions (no key length).
    deductions: Deductions | None


class InstanceInfo(TypedDict):
    """Who the instance is, as the record names it."""

    id: str
    title: str
    summary: str
    readme: str


class DocumentInfo(TypedDict):
    """Which protocol document a run was lowered from (0.3.0)."""

    id: str
    format_version: str
    packaged: bool
    digest: str


class Fact(TypedDict):
    """One fact about the run's route, read off the record."""

    name: str
    value: Any
    pointer: str


class InputRow(TypedDict):
    """One declared input of the run, with its meaning where a table gives one."""

    name: str
    section: Literal["run", "key-length", "model", "device", "solver"]
    value: Any
    default: Any
    is_default: bool | None
    unit: str | None
    quantity: str | None
    domain: Any
    meaning: str | None
    applies: bool | None
    station: str | None
    snapped: bool | None
    pointer: str
    bound_by: list[str]
    #: The premises the report infers cover the value, beside the record's
    #: bindings in ``bound_by`` (0.34.0): A-EXACT on a declared receiver
    #: component value (build._exact_inputs).
    covered_by: list[str]
    #: Which inputs table the row is in (0.9.0): ``device`` (device and
    #: channel), ``budget`` (security budgets) or ``engine`` (engine settings).
    group: Literal["device", "budget", "engine"]
    #: A readable name beside the configuration's own (0.9.0).
    label: str
    #: Why the value was not used on this run, or ``None`` (0.9.0).
    not_used: str | None
    #: The value the run analysed where a preparation replaced the requested
    #: ``value`` (a protocol document's ``rebind``), exact ``p/q``; ``None``
    #: where the requested value is the analysed one (0.25.0).
    prepared: str | None


class HonestModel(TypedDict):
    """Which honest model produced the distribution, verbatim."""

    note: Any
    tag: Any


class Preparation(TypedDict):
    """Where the record keeps the input preparation and the snaps, with extrema."""

    input_preparation_pointer: str | None
    snaps_pointer: str | None
    declared_tolerance: float | None
    #: The record's own extrema, over the measurement blocks: null where none
    #: was snapped, even where the instance moved an input.
    snap_max_defect: float | None
    snap_max_displacement: float | None
    #: Where the instance moved an input family before the run (0.32.0;
    #: inputs.preparation_moves): the largest move and the largest
    #: normalization defect of the moved families. Absent where none moved.
    input_max_displacement: NotRequired[float]
    input_normalization_defect: NotRequired[float | None]


class SnapBlock(TypedDict):
    """One block of the instance's measurement-family snap (0.4.0).

    Read off the record's ``measurement_snaps`` (``foundations/
    req:who-snaps``), with the run's decision written on each block: its
    status, kept or moved; the reference kind the snap ran on; the kind and
    radii of the reference handed beside it; and, for a moved block that rests
    on A-SNAP, its cause with the receiver's fix where it gives one (else the
    foundations fix), its group and the group's fix (0.15.0).
    """

    station: str | None
    setting: str | None
    block: str
    #: ``kept`` or ``moved`` (``foundations/def:snap``).
    status: str
    #: What the snap ran on: ``exact`` (the centres of an exact reference) or
    #: ``none`` (the receiver's floating-point blocks).
    reference_kind: str
    #: The kind of the reference handed beside the snap, ``exact`` or
    #: ``enclosed``; ``None`` where none is handed (0.15.0).
    handed_kind: str | None
    #: The largest radius of the handed reference on the block.
    handed_radius: str | None
    #: The largest radius of the enclosures of the irrational inputs.
    input_radius: str | None
    cause: str | None
    fix: str | None
    #: The group of ``foundations/req:snap-reference`` (iii) of a block resting
    #: on A-SNAP, and the group's fix (0.5.0); ``None`` otherwise.
    group: str | None
    group_fix: str | None
    support_not_preserved: bool
    rests_on_assumption: bool
    #: Whether the run evaluated the moved block off its snap (0.14.0; record
    #: 0.27.0; ``foundations/def:evaluated-off-snap``): its key length reads
    #: the receiver model there, so the block does not rest on A-SNAP. False
    #: on a kept block, which is the model itself (0.15.0).
    evaluated_off_snap: bool
    pointer: str


class EmissionSnap(TypedDict):
    """One data sector in which the emission normaliser moved a class (0.4.0)."""

    station: str | None
    data_sector: int
    #: Per moved class: ``class``, ``step`` and ``support_not_preserved``, as
    #: the record writes them (0.15.0).
    moved_classes: list[dict[str, Any]]
    #: Whether the run evaluated the sector off its snap (0.14.0): the
    #: reference companion carries none of the normaliser's data.
    evaluated_off_snap: bool
    #: Whether the sector rests on A-SNAP after the run's decision (0.15.0).
    rests_on_assumption: bool
    #: The group of a resting sector, and the group's fix (0.15.0).
    group: str | None
    group_fix: str | None
    pointer: str


class SnapRow(TypedDict):
    """One snap block as a reader reads it (0.10.0)."""

    #: The station by its party ("Alice's station"), or ``None`` for the one
    #: receiver of a run whose record names no station.
    station: str | None
    #: The photon number in words ("0 photons (vacuum)"), with a setting
    #: other than "off".
    photons: str
    status: str
    rests_on_assumption: bool
    #: Whether the block was evaluated off its snap (0.14.0).
    evaluated_off_snap: bool
    #: The group in words where the block rests on A-SNAP, else ``None``.
    group: str | None
    fix: str | None
    pointer: str


class MeasurementSnaps(TypedDict):
    """How every measurement-family snap of the run entered the result (0.4.0).

    The report's snap section: per block whether it was kept or moved, the
    reference handed beside it, and for a moved block resting on A-SNAP its
    group, cause and fix; the emission normaliser's moved sectors; the run's
    enclosure and strict settings; and the warnings a reader must see
    (``support_not_preserved``, blocks resting on A-SNAP). ``sentences`` and
    ``warnings`` are the run tier's plain-words reading of those rows.
    """

    settings: dict[str, Any]
    sentences: list[str]
    warnings: list[str]
    blocks: list[SnapBlock]
    emission: list[EmissionSnap]
    rests_on_a_snap: bool
    #: ``A-SNAP`` where the assumption manifest lists it, else ``None``.
    assumption: str | None
    #: Three to five plain sentences a reader meets first (0.10.0): what a
    #: snap is, whether the key length depends on it, why, the fix.
    plain: list[str]
    #: One readable row per block (0.10.0); the raw rows are ``blocks``.
    rows: list[SnapRow]
    #: The run's decision on the direct route (0.14.0; record 0.27.0,
    #: ``snaps.reference_companion.status``): ``counted`` where the key length
    #: is computed from the bound on the reference companion; ``None`` on an
    #: older record.
    direct_route: str | None
    #: How many moved blocks of the stations were evaluated off their snap.
    evaluated_off_snap: int


#: ONE MATRIX ENTRY (0.8.0): ``[re, im]``, each an exact ``"p/q"`` string (or
#: an exact integer written as a string) or a binary64 number, as the record
#: holds it; a renderer formats it and never rounds an exact one.
type MatrixEntry = list[str | float]


class OperatorElement(TypedDict):
    """One outcome's operator on one block (0.8.0)."""

    outcome: str
    #: Rows of entries; row ``i``, column ``j`` is ``<i|M|j>`` in the block's basis.
    matrix: list[list[MatrixEntry]]


class OperatorBlock(TypedDict):
    """The operators of one block, one per outcome, on a labelled basis (0.8.0).

    ``basis`` labels the rows (and the columns unless ``column_basis`` is
    given, as for a rectangular instrument matrix) in the order the record
    lists the entries; ``basis_note`` says where that order comes from.
    """

    title: str
    basis: list[str]
    column_basis: list[str] | None
    basis_note: str | None
    elements: list[OperatorElement]
    #: Whether every entry is an exact string.
    exact: bool
    pointer: str | None


class OperatorFamily(TypedDict):
    """A family of operators the record holds for a station or the source (0.8.0).

    ``kind`` says which: the receiver's bare photon-number blocks, the
    dark-count-composed blocks, the squashed target POVM, a declared finite
    POVM, declared port Grams or an instrument matrix, or the source's
    operators. ``text`` is the run tier's one-sentence reading of what the
    family is, ``claims`` the claim ids it rests on.
    """

    kind: Literal[
        "photon-blocks", "dark-composed", "target-povm", "declared-povm",
        "port-grams", "instrument-matrix", "source",
    ]
    title: str
    text: str | None
    claims: list[str]
    blocks: list[OperatorBlock]
    pointer: str | None


class OutcomeLetter(TypedDict):
    """One letter of a station's outcome alphabet, explained (0.8.0)."""

    letter: str
    meaning: str
    #: The click patterns (sets of detector ports) the letter collects, or
    #: ``None`` where the record holds none.
    patterns: list[list[str]] | None


class OpticalElement(TypedDict):
    """One element of a station's element graph, in words (0.8.0)."""

    name: str
    component: str | None
    description: str
    modes: list[str]


class Detector(TypedDict):
    """One detector port of a station: the modes it collects and its parameters."""

    port: str
    modes: list[str] | None
    parameters: dict[str, Any]


class SetupStation(TypedDict):
    """One measuring station (or the single receiver) of the run (0.8.0)."""

    index: int | None
    label: str | None
    party: str | None
    name: str
    route: str | None
    route_text: str
    channel_modes: list[str]
    outcomes: list[OutcomeLetter]
    elements: list[OpticalElement]
    edges: list[list[str]]
    detectors: list[Detector]
    photon_cutoff: int | None
    exact_window: Any
    families: list[OperatorFamily]
    notes: list[str]
    claims: list[str]
    pointer: str | None


class RoundPremise(TypedDict):
    """One premise the cut of a detection record into rounds bears on (0.29.0)."""

    short_id: str
    #: A short gloss of what the premise's own text says about rounds; the
    #: full text is under "Assumptions you vouch for".
    gloss: str


class RoundBlock(TypedDict):
    """What a round is, said before the protocol's steps (0.29.0)."""

    text: str
    premises: list[RoundPremise]


class ProtocolStep(TypedDict):
    """One step of the protocol as the record describes it (0.8.0)."""

    title: str
    text: str
    pointer: str | None


class SetupSource(TypedDict):
    """The source: its mode, its honest model and what the record holds of it."""

    mode: str | None
    trusted: bool | None
    text: str
    honest_model: str | None
    honest_parameters: dict[str, Any]
    derivation: str | None
    status: str | None
    #: The signal alphabet with its weights, ``{"label", "weight"}``.
    signals: list[dict[str, Any]]
    families: list[OperatorFamily]
    pointer: str | None


class AcceptanceCategory(TypedDict):
    """One acceptance category: what the honest model predicts, what passes."""

    outcome: str
    #: The honest model's probability of the category, or ``None``.
    probability: float | None
    #: The box interval ``[q^-, q^+]`` of the frequency, exact ``p/q``.
    lower: str
    upper: str
    #: The counts out of ``rounds`` the interval admits, ends included:
    #: ``ceil(n q^-)`` to ``floor(n q^+)``; ``None`` without a round count.
    count_min: int | None
    count_max: int | None
    rounds: int | None


class SetupAcceptance(TypedDict):
    """The acceptance test: what it constrains, its rows, its completeness."""

    rows: int | None
    outcomes: list[str]
    #: How many outcomes the honest distribution gives positive probability.
    support: int | None
    endpoint_rule: str | None
    geometry: str | None
    completeness_budget: Any
    completeness_certified: str | None
    text: str
    claims: list[str]
    pointer: str | None
    #: Each outcome's honest probability, ``{"outcome", "probability"}``
    #: (0.12.0): what the record holds of the intervals.
    honest: list[dict[str, Any]]
    #: One row per acceptance category where the record carries the box
    #: (record 0.36.0): its honest probability, its interval of frequencies
    #: and, with the round count, the counts the test accepts. Empty where the
    #: record carries no box.
    categories: list[AcceptanceCategory]


class ExpectedStatistic(TypedDict):
    """One expected statistic of the honest model, in decimals, and how computed."""

    name: str
    value: float | None
    how: str
    pointer: str | None


class GlanceItem(TypedDict):
    """One fragment of the at-a-glance box (0.30.0): its key part in bold.

    ``lead`` is shown in bold, ``text`` follows it (carried text with
    ``[[...]]`` links), ``anchor`` is the section it links.
    """

    lead: str
    text: str
    anchor: str | None


class SummaryItem(TypedDict):
    """One line of the summary: carried text with ``[[...]]`` links (0.9.0)."""

    text: str
    pointer: str | None
    #: An in-page anchor the line refers to for its details (0.12.0).
    anchor: str | None


class GuaranteeTerm(TypedDict):
    """One row of the ε table beneath the guarantee (0.9.0)."""

    symbol: str
    value: float | None
    meaning: str


class Guarantee(TypedDict):
    """What the guarantee means: the claims quoted and the ε table (0.9.0)."""

    #: ``meat-core/cor:composed-security``, whose ``user_statement`` is the
    #: headline; ``None`` on a run without a key length.
    claim: str | None
    terms: list[GuaranteeTerm]
    per_execution: str | None
    completeness: str | None
    eps_star: str | None
    #: The run's premises not beneath the claims of the review status in the
    #: claim graph (0.32.0); ``None`` where the closure table states no closure.
    outside: list[str] | None


class VouchLine(TypedDict):
    """One premise family of the summary's "What you vouch for" (0.9.0).

    Since 0.12.0 one line per ``refines`` family: the parent premise, with
    the short ids of the premises that refine it.
    """

    short_id: str
    title: str
    #: What the premise's failure affects (0.19.0): ``security`` (secrecy or
    #: correctness) or ``completeness`` (only how often an honest run aborts).
    consequence: str
    #: What the premise is about (0.10.0), e.g. "Alice's and Bob's stations".
    about: str
    refinements: list[str]
    #: Each refinement's consequence, in the order of ``refinements``
    #: (0.20.0).
    refinement_consequences: list[str]
    #: The premise's existing one-liner: its claim summary's first sentence
    #: (0.31.0).
    summary: str


class ConsequenceCounts(TypedDict):
    """The premises of a run counted by what their failure affects (0.31.0)."""

    security: int
    #: The premises about supplied artefacts and the engine's numerics that
    #: can break security, by short id.
    engine: list[str]
    completeness: int


class WhereRow(TypedDict):
    """One place of the per-station checklist: the premises about it (0.18.0)."""

    #: "Alice's laboratory", "Bob's station (bob_station)", or the premises
    #: about no one station or laboratory.
    place: str
    premises: list[str]


class VouchGroup(TypedDict):
    """The premises of one group, under its heading (0.10.0).

    Since 0.31.0 three groups by category (explain.VOUCH_GROUPS): your
    devices and setup, how the run is carried out, artefacts and the engine.
    """

    about: str
    entries: list[VouchLine]


class Summary(TypedDict):
    """Layer 1 of the report: the summary a reader needs first (0.9.0).

    Built by :mod:`certiqs_key.runs.report.explain` from the other sections;
    every sentence is that module's or a claim's own text.
    """

    #: The box at the top: terse fragments, each with its key part in bold
    #: and its section linked (0.30.0; 0.13.0 as sentences).
    at_a_glance: list[GlanceItem]
    #: "Key rate considerations", right after the box: each nuance of the
    #: number in one sentence with its link (0.30.0).
    considerations: list[SummaryItem]
    result: str
    #: What consumes key and what remains, one line each: the post-processing
    #: deductions, the key length, the authentication's pre-shared key and the
    #: net key; empty where the run reports no key length (0.30.0; 0.28.0 as
    #: one sentence).
    costs: list[str]
    guarantee: Guarantee | None
    setup_brief: list[str]
    #: "Roles on this run", from the role vector (0.18.0;
    #: :func:`certiqs_key.runs.report.explain.roles_box`).
    roles: list[str]
    #: The roles this run does not have, one line each, beneath the roles
    #: (0.30.0; a sentence of ``roles`` before).
    roles_absent: list[str]
    vouch: list[VouchGroup]
    #: "Where each premise applies": per party laboratory and station the
    #: premises about it, then those about none (0.18.0; R6).
    where: list[WhereRow]
    #: The premises counted by consequence (0.31.0; one sentence since 0.19.0).
    consequences: ConsequenceCounts
    #: The premises about artefacts and the engine, by short id.
    internal: list[str]
    #: Each of them's consequence, in the order of ``internal`` (0.20.0).
    internal_consequences: list[str]
    not_counted: list[SummaryItem]
    #: "Choices that could lengthen the key": run settings that change the
    #: key length without changing the devices or the security statement.
    levers: list[SummaryItem]
    #: The tier's full sentence, said under "How the number was computed",
    #: whose short form is among the considerations; empty where the run
    #: reports no key length or names no tier (0.29.0).
    tier_note: str
    #: The premises whose effective status is draft, by short id.
    drafts: list[str]
    #: The premises whose frozen text differs from the current contract's
    #: (0.10.0), by short id.
    stale: list[str]


class SetupSection(TypedDict):
    """Your QKD setup, built from the record only (0.8.0).

    The protocol's steps, the source, each measuring station with its
    outcome alphabet, element list and the POVM per setting and photon-number
    block on a labelled basis, the squashed target POVM, the acceptance test
    and the honest model's expected statistics. The three notes lists say
    what the record does not hold, each where its part would stand (0.33.0);
    nothing absent
    is invented.
    """

    #: What a round is and the premises on it, before the steps; ``None``
    #: where the record holds no round count (0.29.0).
    round: RoundBlock | None
    protocol: list[ProtocolStep]
    source: SetupSource | None
    stations: list[SetupStation]
    acceptance: SetupAcceptance | None
    expected: list[ExpectedStatistic]
    #: Which model the expected statistics come from, one sentence: the honest
    #: model and the parameters it was evaluated with, or a supplied law
    #: (0.29.0); empty where no expected statistic is given.
    expected_basis: str
    #: Why the source is not described (0.33.0).
    source_notes: list[str]
    #: Why no station is described (0.33.0).
    station_notes: list[str]
    #: Why an expected statistic is not given (0.33.0).
    expected_notes: list[str]


class ProtocolSection(TypedDict):
    """R2: the protocol and every declared input."""

    instance: InstanceInfo | None
    #: The protocol document, or ``None`` off the document route (0.3.0).
    document: DocumentInfo | None
    facts: list[Fact]
    inputs: list[InputRow]
    honest_model: HonestModel
    preparation: Preparation
    #: The measurement snaps (0.4.0), or ``None`` where the run made none
    #: (a declared POVM, a refusal before the receiver, a record before 0.22.0).
    measurement_snaps: MeasurementSnaps | None


class ProvenanceSection(TypedDict):
    """R6: what produced the record, and how to reproduce it."""

    engine: dict[str, Any] | None
    created_by: str
    config_digest: str | None
    record_schema_version: str
    report_schema_version: str
    report_id: str
    module_versions: dict[str, Any]
    claim_status: list[dict[str, str]]
    solver: dict[str, Any]
    tolerances: dict[str, Any]
    platform: Any
    artefacts: list[dict[str, Any]]
    final_iterate: dict[str, Any] | None
    reproduce: dict[str, str]


class Sections(TypedDict):
    """The sections, R1-R6, the setup (0.8.0) and the summary (0.9.0)."""

    summary: Summary
    result: ResultSection
    setup: SetupSection
    protocol: ProtocolSection
    assumptions: AssumptionsSection
    numerics: NumericsSection
    checks: ChecksSection
    provenance: ProvenanceSection


class ReportIndex(TypedDict):
    """Every claim the report links, and the owner of every linked assumption id.

    A renderer resolves a ``[[...]]`` token of carried text through it without
    reading the closure table, and an MCP tool addresses a claim by id.
    ``mentions`` (0.12.0) maps a claim id that carried text names but the
    closure table does not carry, as written (``<module>|<id>`` for a bare
    ``kind:label``), to its contract anchor.
    """

    claims: dict[str, ClaimRef]
    assumptions: dict[str, str]
    mentions: NotRequired[dict[str, ContractAnchor]]


class KeyRateReport(TypedDict):
    """One run's key-rate report."""

    kind: Literal["key-rate-report"]
    report_schema_version: str
    record_schema_version: str
    id: str
    sections: Sections
    index: ReportIndex


class RouteDelta(TypedDict):
    """Engaged assumption ids a point adds to, or lacks from, the common route."""

    added: list[str]
    removed: list[str]


class SweepPoint(TypedDict):
    """One point of a sweep: its varying inputs and its own numbers, never summed."""

    index: int
    label: str | None
    record_id: str
    values: dict[str, Any]
    outcome: Outcome
    key_length: int | None
    net_key_length: int | None
    rate_per_round: float | None
    reported_tier: str | None
    security_parameter: float | None
    refusal: Refusal | None
    route_signature: str | None
    route_differs: bool
    route_delta: RouteDelta
    #: The not-counted flags this point raises that not every completed point
    #: raises; those every completed point raises are in the common part.
    flags: list[str]
    #: Whether this point's key length rests on a measurement snap (0.10.0),
    #: ``None`` where the point made no snap; and how many snap blocks rest.
    rests_on_a_snap: bool | None
    resting_blocks: int
    #: How many data sectors of the reduction's emission rest on A-SNAP.
    resting_sectors: int


class CommonPart(TypedDict):
    """What a sweep shows once, each row marked with the points it holds at.

    The inputs and provenance are those equal at every point. The not-counted
    flags, assumptions, numerics, rows not engaged or discharged, and
    discrepancies are the UNION over the completed points, each row with its
    ``points``, so no premise or flag a point carries is left out. A check
    whose outcome differs between points reads ``varies`` with every point's
    outcome.
    """

    instance: InstanceInfo | None
    inputs: list[InputRow]
    not_counted: list[Flag]
    user_declared: list[UserDeclared]
    limitations: list[ClaimRef]
    per_execution: list[ClaimRef]
    assumptions: AssumptionsSection
    numerics: NumericsSection
    checks: list[Check]
    discharged_on_route: list[NotEngaged]
    decided_rows: list[AssumptionEntry]
    provenance: dict[str, Any]
    #: The setup of the first completed point, shown once (0.10.0): the varying
    #: inputs are what differs from it; ``None`` where no point completed.
    setup: SetupSection | None
    setup_point: int | None
    #: The guarantee the points share (its claims; each point's ε is its own).
    guarantee: Guarantee | None


class SweepReport(TypedDict):
    """A sweep's report: the common part, what varies, and one row per point."""

    kind: Literal["key-rate-sweep-report"]
    report_schema_version: str
    record_schema_version: str
    id: str
    common: CommonPart
    varying: list[str]
    points: list[SweepPoint]
    index: ReportIndex


def group_entries(groups: list[CategoryGroup]) -> list[AssumptionEntry]:
    """Return the entries of category groups, heads before their members."""
    return [
        entry
        for group in groups
        for family in group["families"]
        for entry in (family["head"], *family["members"])
    ]
