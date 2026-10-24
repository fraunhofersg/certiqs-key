"""The protocol document's shape: one pydantic model per block, unknown keys refused.

WHY MODELS AND NOT A HAND-WRITTEN SCHEMA. The models are the one statement of
what a document may contain. The JSON Schema an agent reads
(``protocol-document.schema.json``) is generated from them by
:mod:`instances.declared.schema` and a test holds it current (PRINCIPLES.md
section 7: a generated view, never a second spelling). Every block forbids a key
it does not declare, so a misspelt key is refused with its path rather than
quietly ignored.

WHAT THE MODELS DECIDE, AND WHAT THEY DO NOT. They decide SHAPE: which keys
exist, which are required, which values are a number, a name, a matrix or a
rule list. They never decide a protocol: whether weights sum to one, whether a
POVM is complete, whether a coarse-graining is total is decided by the modules
the lowering hands these values to.

THE VALUE LANGUAGE IN THE TYPES. A *scalar* is a JSON integer, a
number string (read exactly by ``runs.inputs.exact_input``), ``{param}``,
``{expr}`` or ``{switch}``. A ``switch`` may stand wherever the type says
``Sw[...]``: every scalar, every matrix, every rule list, and the blocks a
template switches over (a station's reduction, the public part's tables, the
constraints, the honest model). Fields typed :data:`Exact` are expression
texts or integers: the run defaults, a preparation's family and
the derived defaults.

Only the configuration-independent blocks (``identity``, ``parameters``,
``presets``, ``snap``, ``preparations``, ``run_defaults``) are read before any
lowering; the others are modelled so that the schema is complete, and are
lowered per configuration.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    WithJsonSchema,
    model_validator,
)

from certiqs_key.runs.surface import Quantity

__all__ = [
    "FORMAT",
    "AlphabetNode",
    "Exact",
    "Expr",
    "Matrix",
    "ParamRef",
    "ParameterRow",
    "Pattern",
    "ProtocolDocument",
    "Rule",
    "RuleValue",
    "Rules",
    "Scalar",
    "StaticDocument",
    "Switch",
]

#: The document's ``format`` constant.
FORMAT = "certiqs-key/protocol-document"

_IDENTIFIER = r"^[A-Za-z_][A-Za-z0-9_]*$"


class _Block(BaseModel):
    """A block of the document: immutable, and refusing every undeclared key."""

    model_config = ConfigDict(extra="forbid", frozen=True)


def _label_text(value: object) -> object:
    """Read a JSON integer written where a label is expected as its decimal text."""
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return value


#: A label: a string, or a JSON integer read as its decimal text (``bit: [0, 1]``).
Text = Annotated[
    StrictStr,
    BeforeValidator(_label_text),
    WithJsonSchema({"type": ["string", "integer"]}),
]

#: An expression text or a JSON integer.
type Exact = StrictInt | StrictStr

#: A lattice exponent ``k`` of (D-LAT) (spec/architecture.md 2.9): the
#: snap and the reductions read ``1 <= k <= 53`` and nothing else, so a value
#: outside it is refused as the document's shape.
Lattice = Annotated[StrictInt, Field(ge=1, le=53)]

# ---------------------------------------------------------------------------
#  The value language
# ---------------------------------------------------------------------------


class ParamRef(_Block):
    """``{param: name}`` or ``{param: name, port: label}``: a configuration value."""

    param: str
    port: Text | None = None


class Expr(_Block):
    """``{expr: "..."}``: exact arithmetic over parameters.

    ``+ - * /``, parentheses, integer powers (``2^-30``), decimals, fractions,
    and the names of ``fraction`` and ``int`` parameters (``dark_count[H]``
    for one port). No functions and no irrational numbers.
    """

    expr: str


class Switch[T](_Block):
    """``{switch: name, cases: {value: node}, default?: node}`` over a choice."""

    switch: str
    cases: dict[str, T]
    default: T | None = None


#: A node that may be a switch over nodes of its own type.
type Sw[T] = T | Switch[T]

#: A value-language scalar.
type Scalar = StrictInt | StrictStr | ParamRef | Expr | Switch[Scalar]

#: A matrix entry: a scalar, or ``[re, im]`` (the ``serialize_matrix`` pair).
type Entry = Scalar | tuple[Scalar, Scalar]


class MatrixRows(_Block):
    """``{matrix: rows}``; ``serialize_matrix``'s output is accepted verbatim."""

    matrix: list[list[Entry]]


class OuterSpec(_Block):
    """The arguments of ``foundations.exact.outer_projector``."""

    vector: list[Entry]
    squared_norm: Scalar


class Outer(_Block):
    """``{outer: {vector, squared_norm}}``: ``v v^dag / N``, never a square root."""

    outer: OuterSpec


class IdentityMatrix(_Block):
    """``{identity: n}``."""

    identity: StrictInt


class ScaleSpec(_Block):
    """The arguments of ``foundations.exact.scale``."""

    factor: Entry
    of: Matrix


class Scale(_Block):
    """``{scale: {factor, of}}``."""

    scale: ScaleSpec


#: A matrix node.
type Matrix = MatrixRows | Outer | IdentityMatrix | Scale | Switch[Matrix]

# ---------------------------------------------------------------------------
#  The rule language
# ---------------------------------------------------------------------------


class Eq(_Block):
    """``{eq: path}``: matches where both sides exist and are equal."""

    eq: str


class Ne(_Block):
    """``{ne: path}``: matches where both sides exist and differ."""

    ne: str


class Not(_Block):
    """``{not: pattern}``."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    not_: Pattern = Field(alias="not")


#: A condition's pattern: equality, membership, a comparison or a negation.
type Pattern = Text | list[Text] | Eq | Ne | Not


class MessageValue(_Block):
    """``{label: template, attrs: {name: template}}``: a value later rules can read."""

    label: str
    attrs: dict[str, str] = {}


class IntOf(_Block):
    """``{int: path}``: the integer a component spells."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    int_: str = Field(alias="int")


#: A rule's value: a template, an integer literal, a message value, ``{int}``.
type RuleValue = StrictInt | StrictStr | MessageValue | IntOf | Switch[RuleValue]


class Rule(_Block):
    """``{when?: {path: pattern}, value: node}``; the first matching rule wins."""

    when: dict[str, Pattern] | None = None
    value: RuleValue


#: An ordered rule list, or a switch over rule lists.
type Rules = Sw[list[Rule]]

#: An enumerated entry: a label, or ``{label, ...attributes}``.
type EnumEntry = Text | dict[str, Text]


class EnumAlphabet(_Block):
    """``{enum: [label | {label, ...attrs}]}``."""

    enum: list[EnumEntry]
    attrs: dict[str, Text] = {}

    @model_validator(mode="after")
    def _labelled(self) -> EnumAlphabet:
        for entry in self.enum:
            if isinstance(entry, dict) and "label" not in entry:
                raise ValueError("an enumerated entry written as an object needs label")
        return self


class ProductSpec(_Block):
    """``dims`` (the first varies slowest) and the label template."""

    dims: dict[str, list[Text]]
    label: str


class ProductAlphabet(_Block):
    """``{product: {dims, label}}``."""

    product: ProductSpec
    attrs: dict[str, Text] = {}


class UnionAlphabet(_Block):
    """``{union: [parts]}``; each part may add constant ``attrs``."""

    union: list[AlphabetNode]
    attrs: dict[str, Text] = {}


#: An alphabet: inline, or the name of one under ``alphabets``.
type AlphabetNode = StrictStr | EnumAlphabet | ProductAlphabet | UnionAlphabet

# ---------------------------------------------------------------------------
#  identity, parameters, presets, snap, preparations, run_defaults
# ---------------------------------------------------------------------------


class Identity(_Block):
    """Who the document is: the descriptor's strings and the record label."""

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=64)
    title: str
    summary: str
    readme: str = Field(
        default="",
        description="A packaged template's README path; empty for a custom document.",
    )
    record_label: str | None = Field(
        default=None,
        description=(
            "The prefix of every identity string a run records; default "
            "declared.<id>, and only that for a custom document."
        ),
    )


class DomainOption(_Block):
    """One ``(value, meaning)`` pair of a ``choices`` domain."""

    value: str
    meaning: str


class Domain(_Block):
    """``ParameterDomain.as_payload``'s shape."""

    form: Literal["interval", "choices"]
    lower: Exact | None = None
    upper: Exact | None = None
    lower_open: StrictBool = False
    upper_open: StrictBool = False
    options: list[DomainOption] = []

    @model_validator(mode="after")
    def _one_form(self) -> Domain:
        if self.form == "choices" and (
            not self.options or self.lower is not None or self.upper is not None
        ):
            raise ValueError("a choices domain lists options and no bounds")
        if self.form == "interval" and self.options:
            raise ValueError("an interval domain lists no options")
        return self


#: A static number: an integer, a number string, or ``{expr}`` reading no name.
type StaticNumber = StrictInt | StrictStr | Expr

#: A static parameter value: a number, a name, or one number per port.
type StaticValue = Annotated[
    StaticNumber | dict[str, StaticNumber], Field(union_mode="left_to_right")
]


class ParameterRow(_Block):
    """One parameter: a row of the run tier's ``ParameterSpec`` table."""

    name: str = Field(pattern=_IDENTIFIER)
    section: Literal["model", "device"]
    kind: Literal["fraction", "int", "choice", "per_port_fraction"]
    quantity: Quantity
    unit: str | None = None
    default: StaticValue | None = None
    domain: Domain
    snapped: StrictBool
    meaning: str
    applies_when: dict[str, list[Text]] | None = None
    station: str | None = Field(
        default=None,
        description="The id of the station this parameter describes, if one.",
    )
    per_port_of: str | None = Field(
        default=None,
        description=(
            "For kind per_port_fraction: the id of the station whose port labels "
            "key the value, in port-map order. A single number as a default "
            "means that number on every port."
        ),
    )


class Parameters(_Block):
    """The parameter table, and what an absent configuration key means."""

    model_absent: Literal["refuse", "default"] = Field(
        default="refuse",
        description=(
            "refuse: a configuration must declare every applicable model key; "
            "default: an absent key reads the table default."
        ),
    )
    device_absent: Literal["refuse", "default"] = Field(
        default="refuse", description="As model_absent, for the device section."
    )
    check_order: tuple[Literal["model", "device"], Literal["model", "device"]] = Field(
        default=("model", "device"),
        description=(
            "The order the two sections are checked in, so which refusal a "
            "configuration faulty in both reports first."
        ),
    )
    table: list[ParameterRow]

    @model_validator(mode="after")
    def _both_sections(self) -> Parameters:
        if set(self.check_order) != {"model", "device"}:
            raise ValueError("check_order names model and device once each")
        return self


class PresetBlock(_Block):
    """A named parameter set; values are numbers or ``{expr}`` without names."""

    name: str
    note: str = ""
    model: dict[str, StaticValue] = {}
    device: dict[str, StaticValue] = {}


class Snap(_Block):
    """One ``prepare_config_probabilities`` call."""

    lattice_exponent: Lattice
    groups: list[list[str]] = []


class Preparation(_Block):
    """One further ``prepare_probabilities`` call that rebinds parameters."""

    site: str
    lattice_exponent: Lattice
    family: list[Exact] = Field(
        description="A probability family: expressions over parameters, summing to one."
    )
    rebind: dict[str, StrictInt] = Field(
        description=(
            "Each parameter replaced by the prepared family's entry at this index."
        )
    )


class KeyLengthBlock(_Block):
    """``KeyLengthParameters``, plus A-AUTH's two run inputs."""

    alpha: Exact
    eps_pa: Exact
    eps_ev: Exact
    lambda_ec: Exact
    eps_auth: Exact | None = None
    k_auth: Exact | None = None


class AdvancedSolverBlock(_Block):
    """``AdvancedSolverSettings``, without a warm start: the expert choices."""

    method: str | None = None
    oracle: str | None = None
    gap_tolerance: Exact | None = None
    certified_evaluation: str | None = None


class SolverBlock(_Block):
    """``SolverSettings``: the ordinary choices, the expert ones under ``advanced``."""

    method: str | None = None
    budget_seconds: Exact | None = None
    max_iterations: Exact | None = None
    advanced: AdvancedSolverBlock | None = None


class RunDefaults(_Block):
    """The base of ``default_config`` and how a caller's overrides combine with it."""

    rounds: Exact
    completeness_budget: Exact
    declared_tolerance: Exact
    parameters: KeyLengthBlock
    alpha: Exact | None = None
    constrained: list[str] | None = None
    endpoint_rule: str | None = None
    tail_evaluation: str | None = None
    solver: SolverBlock | None = None
    model: dict[str, StaticValue] = {}
    device: dict[str, StaticValue] = {}
    sections: Literal["replace", "merge"] = Field(
        default="replace",
        description=(
            "How a caller's model= or device= combines with the base section: "
            "replace it whole, or lay the caller's keys over it."
        ),
    )
    derived: dict[str, Exact] = Field(
        default={},
        description=(
            "Defaults computed from other parameters, as expressions, e.g. "
            "exact_window: photon_cutoff + 1."
        ),
    )
    derived_timing: Literal["base_only", "unless_supplied"] | None = Field(
        default=None,
        description=(
            "base_only: derived is evaluated on the base, before a caller's "
            "sections; unless_supplied: on the combined values, for each key "
            "the caller's section did not supply. Required with derived."
        ),
    )

    @model_validator(mode="after")
    def _timed(self) -> RunDefaults:
        if self.derived and self.derived_timing is None:
            raise ValueError("derived defaults need a derived_timing")
        return self


# ---------------------------------------------------------------------------
#  source
# ---------------------------------------------------------------------------


class Attestation(_Block):
    """A user's (SR3) retention attestation: recorded, never verified."""

    attested_by: str
    statement: str


class ChoiceFamily(_Block):
    """A weighted choice family, lowered to ``PublicChoices``."""

    choices: list[Text]
    weights: dict[str, Scalar]
    conditional_alphabets: dict[str, list[Text]]
    conditional_elements: dict[str, dict[str, Matrix]] | Literal["conjugate_states"]
    joint_label: str


class AliceChoices(_Block):
    """Alice's measurement as a choice family."""

    choice_family: ChoiceFamily


class AlicePovm(_Block):
    """Alice's measurement as a direct POVM."""

    povm: dict[str, Matrix]


class Sectors(_Block):
    """A ``SectorStructure``."""

    labels: list[Text]
    dims: list[StrictInt]
    block_kind: str


class PureCertificate(_Block):
    """``SourceReplacementCertificate``."""

    form: Literal["pure"]
    psi: Matrix
    virtual_dim: StrictInt
    virtual_weights: dict[str, Scalar] | None = None
    virtual_states: dict[str, Matrix] | None = None


class BlockCertificate(_Block):
    """``BlockFormCertificate``."""

    form: Literal["block"]
    alice_sectors: Sectors
    virtual_sectors: Sectors
    alice_marginal_blocks: list[Matrix]
    psi_blocks: list[Matrix]
    virtual_weights: dict[str, Scalar]
    virtual_blocks: dict[str, list[Matrix]]


class PresentationCertificate(_Block):
    """``EnsemblePresentation``."""

    form: Literal["ensemble_presentation"]
    virtual_sectors: Sectors
    weighted_blocks: dict[str, list[Matrix]]


type Certificate = Annotated[
    PureCertificate | BlockCertificate | PresentationCertificate,
    Field(discriminator="form"),
]


class TrustedEnsemble(_Block):
    """A trusted source: an ensemble of states with a source-replacement certificate."""

    kind: Literal["trusted_ensemble"]
    alphabet: AlphabetNode
    alice_dim: StrictInt | None = None
    transmitted_dim: StrictInt
    weights: dict[str, Scalar]
    states: dict[str, Matrix]
    alice: AliceChoices | AlicePovm | None = None
    alice_marginal: Matrix | None = None
    certificate: Certificate
    retention_attestation: Attestation | None = None

    @model_validator(mode="after")
    def _presentation_without_alice(self) -> TrustedEnsemble:
        presented = isinstance(self.certificate, PresentationCertificate)
        alice = (self.alice_dim, self.alice, self.alice_marginal)
        if presented and any(item is not None for item in alice):
            raise ValueError(
                "an ensemble_presentation certificate declares no alice_dim, "
                "alice or alice_marginal"
            )
        if not presented and any(item is None for item in alice):
            raise ValueError(
                "this certificate needs alice_dim, alice and alice_marginal"
            )
        return self


class Polarisation(_Block):
    """One WCP polarisation and the attributes its letters carry."""

    label: Text
    part: Literal["H", "V", "+", "-"]
    attrs: dict[str, Text] = {}


class Intensity(_Block):
    """One WCP intensity."""

    name: Text
    mu: Scalar


class Generation(_Block):
    """What a generation round sends."""

    intensity: Text
    polarisations: list[Text]


class TestRounds(_Block):
    """What a test round sends, and the test coin."""

    coin: Scalar
    intensity_probabilities: dict[str, Scalar]
    polarisations: list[Text]


class WcpDecoy(_Block):
    """A tagged weak-coherent-pulse source, through ``emit_decoy_declaration``."""

    kind: Literal["wcp_decoy"]
    polarisations: list[Polarisation]
    intensities: list[Intensity]
    generation: Generation
    test: TestRounds
    entropy_cutoff: Scalar
    source_cutoff: Scalar
    lattice_exponent: Lattice = 24
    flag_family: Literal["shared", "split_by_intensity"] = "shared"
    letter_label: str = Field(
        default="{round}-{intensity}-{polarisation}",
        description=(
            "Each letter's label; it reads round (gen or test), intensity and "
            "polarisation."
        ),
    )
    record_site: str | None = Field(
        default=None,
        description=(
            "The prefix of the preparation records' sites (<site>.test_coin, "
            "...); default the document's id."
        ),
    )
    record_label: str | None = Field(
        default=None,
        description=(
            "The instance string of the source's preparation record; default "
            "<record_label>.source."
        ),
    )
    retention_attestation: Attestation | None = None


class Untrusted(_Block):
    """An untrusted source, through ``emit_artifact``."""

    kind: Literal["untrusted"]
    alphabet: AlphabetNode
    transmitted_dim: StrictInt
    weights: dict[str, Scalar]
    states: dict[str, Matrix] | None = None
    alice_dim: StrictInt
    alice_povm: dict[str, Matrix]


type Source = Annotated[
    TrustedEnsemble | WcpDecoy | Untrusted, Field(discriminator="kind")
]

# ---------------------------------------------------------------------------
#  stations
# ---------------------------------------------------------------------------


class DeclaredPovm(_Block):
    """A measurement declared as matrices (Band A)."""

    kind: Literal["declared_povm"]
    dimension: StrictInt
    choice_family: ChoiceFamily | None = None
    povm: dict[str, Matrix] | None = None

    @model_validator(mode="after")
    def _one_form(self) -> DeclaredPovm:
        if (self.choice_family is None) == (self.povm is None):
            raise ValueError("a declared_povm gives exactly one of choice_family, povm")
        if (
            self.choice_family is not None
            and self.choice_family.conditional_elements == "conjugate_states"
        ):
            raise ValueError("conjugate_states is Alice's convention only")
        return self


class Mode(_Block):
    """One mode of ``ModeSpace.declare``."""

    path: str
    polarization: Literal["H", "V"]
    tau: StrictInt = 0


#: The description of every ``_pi`` field of the catalogue entries.
_PI = (
    "In units of pi: the catalogue field without _pi receives float(value) * pi, "
    "an integer 0 exactly 0."
)


class BeamsplitterParams(_Block):
    """C1."""

    transmittance: Scalar | None = None
    phase_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    loss_1: Scalar | None = None
    loss_2: Scalar | None = None


class PolarizingBeamsplitterParams(_Block):
    """C2."""

    transmittance_h: Scalar | None = None
    transmittance_v: Scalar | None = None
    phase_h_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    phase_v_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    loss_1: Scalar | None = None
    loss_2: Scalar | None = None


class RetarderParams(_Block):
    """C3, general."""

    retardance_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    angle_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    loss: Scalar | None = None


class WaveplateParams(_Block):
    """C3, half- and quarter-wave."""

    angle_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    loss: Scalar | None = None


class RotatorParams(_Block):
    """C4."""

    rotation_angle_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )


class MirrorParams(_Block):
    """C5."""

    reflectivity_h: Scalar | None = None
    reflectivity_v: Scalar | None = None
    phase_h_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    phase_v_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    handedness_flip: StrictBool | None = None


class PhaseShifterParams(_Block):
    """C6."""

    phases_pi: list[Scalar] | None = Field(
        default=None,
        description="Each phase in units of pi, by the same rule as every _pi field.",
    )


class LossParams(_Block):
    """C7."""

    efficiencies: list[Scalar] | None = None


class PolarizerParams(_Block):
    """C8."""

    angle_pi: Scalar | None = Field(
        default=None,
        description=_PI,
    )
    pass_transmittance: Scalar | None = None
    leak_transmittance: Scalar | None = None


class ModeRoutingParams(_Block):
    """C9."""

    permutation: list[StrictInt] | None = None


class GenericBlockParams(_Block):
    """C10."""

    block: Matrix | None = None


class _Element(_Block):
    name: str
    support: list[str]


class BeamsplitterElement(_Element):
    """A C1 element."""

    component: Literal["beamsplitter"]
    params: BeamsplitterParams = BeamsplitterParams()


class PolarizingBeamsplitterElement(_Element):
    """A C2 element."""

    component: Literal["polarizing_beamsplitter"]
    params: PolarizingBeamsplitterParams = PolarizingBeamsplitterParams()


class RetarderElement(_Element):
    """A general C3 element."""

    component: Literal["retarder"]
    params: RetarderParams = RetarderParams()


class WaveplateElement(_Element):
    """A half- or quarter-wave C3 element."""

    component: Literal["half_wave", "quarter_wave"]
    params: WaveplateParams = WaveplateParams()


class RotatorElement(_Element):
    """A C4 element."""

    component: Literal["rotator"]
    params: RotatorParams = RotatorParams()


class MirrorElement(_Element):
    """A C5 element."""

    component: Literal["mirror"]
    params: MirrorParams = MirrorParams()


class PhaseShifterElement(_Element):
    """A C6 element."""

    component: Literal["phase_shifter"]
    params: PhaseShifterParams = PhaseShifterParams()


class LossElement(_Element):
    """A C7 element."""

    component: Literal["loss"]
    params: LossParams = LossParams()


class PolarizerElement(_Element):
    """A C8 element."""

    component: Literal["polarizer"]
    params: PolarizerParams = PolarizerParams()


class ModeRoutingElement(_Element):
    """A C9 element."""

    component: Literal["mode_routing"]
    params: ModeRoutingParams = ModeRoutingParams()


class GenericBlockElement(_Element):
    """A C10 element."""

    component: Literal["generic_block"]
    params: GenericBlockParams = GenericBlockParams()


type Element = Annotated[
    BeamsplitterElement
    | PolarizingBeamsplitterElement
    | RetarderElement
    | WaveplateElement
    | RotatorElement
    | MirrorElement
    | PhaseShifterElement
    | LossElement
    | PolarizerElement
    | ModeRoutingElement
    | GenericBlockElement,
    Field(discriminator="component"),
]


class Port(_Block):
    """One port of the ``PortMap``, in port-map order."""

    label: Text
    modes: list[str]


class Detector(_Block):
    """One ``DetectorPort``."""

    port: Text
    efficiency: Scalar
    dark_count: Scalar


class CoarseGraining(_Block):
    """The letters and the rules over click patterns."""

    letters: list[dict[str, Text]]
    map: Rules

    @model_validator(mode="after")
    def _labelled(self) -> CoarseGraining:
        if any("label" not in letter for letter in self.letters):
            raise ValueError("every coarse-graining letter has a label")
        return self


class Optical(_Block):
    """An optical receiver, lowered to ``ReceiverRequest``."""

    kind: Literal["optical"]
    modes: list[Mode]
    channel_modes: list[str]
    source_modes: list[str] = []
    route: Literal["element_graph", "port_grams", "instrument_matrix"]
    elements: list[Element] = []
    edges: list[tuple[str, str]] = []
    port_grams: dict[str, Matrix] | None = Field(
        default=None,
        description=(
            "route port_grams: one Gram per port label, on the input modes "
            "(channel then source); converted to binary64 with a recorded "
            "conversion per inexact entry."
        ),
    )
    instrument_matrix: Matrix | None = Field(
        default=None,
        description=(
            "route instrument_matrix: the |M| x |Inp| transfer matrix; converted "
            "to binary64 with a recorded conversion per inexact entry."
        ),
    )
    ports: list[Port]
    detectors: list[Detector]
    dark_count_channel: Matrix | None = Field(
        default=None,
        description=(
            "A declared dark-count channel R on the 2^K click patterns, rows and "
            "columns in the order: by number of ports fired, then "
            "lexicographically by port position. Requires every detector's "
            "dark_count to be 0."
        ),
    )
    coarse_graining: CoarseGraining
    photon_cutoff: Scalar
    exact_window: Scalar | None = Field(
        default=None,
        description="The exact-window depth at the probe setting off, or none.",
    )
    tolerances: dict[str, Exact] | None = Field(
        default=None,
        description=(
            "The receiver's numerical tolerances; default eps_1..eps_5 and eps_gap "
            "at 1e-3, and eps_6 and eps_eig at 1e-3 where a window is declared."
        ),
    )
    requested_assurance: Literal["estimate"] = "estimate"
    efficiency_normalization: Scalar | None = Field(
        default=None,
        description=(
            "The factored loss t the receiver is compiled at: its detector "
            "efficiencies are divided by t and the common loss t is handed to "
            "the channel, which leaves the observed statistics unchanged. "
            "Absent, for a receiver without source modes: the largest "
            "detector efficiency divided by 99/100, or 1 where that efficiency "
            "is at least 99/100. Declared: a number in [largest efficiency, "
            "1]; 1 turns the normalization off."
        ),
    )


type Measurement = Annotated[DeclaredPovm | Optical, Field(discriminator="kind")]


class Link(_Block):
    """One reduction link."""

    kind: Literal[
        "identity", "fss", "wpfss", "register-mixture", "flags-enough", "pinching"
    ]
    requested_status: str | None = None


class LibraryOperator(_Block):
    """A carried operator from the library (``two_sector_floor``)."""

    library: Literal["two_sector_floor"]


class ExplicitOperator(_Block):
    """A carried-operator request written out; the reductions certify it.

    ``certified_against`` is not a field: it is read from the first-pass
    artefact's squashing channel, never from the document.
    """

    label: str
    operator: Matrix
    relation: Literal["ge", "le", "eq"]
    constant: Scalar
    certificate_kind: Literal["identity", "positivity", "spectral"]
    form: Literal["expectation", "operator"] = "expectation"


class Reduction(_Block):
    """The station's photon-number reduction (a ``ReductionRequest``)."""

    links: Sw[list[Link]]
    route: Sw[Literal["encoded", "licensed"]] | None = None
    carried_operators: Sw[list[LibraryOperator | ExplicitOperator]] = []
    squash_before_post_processing: StrictBool | None = None
    declared_sector_order: list[str] | None = None
    declared_occupation_basis_order: list[list[str]] | None = None
    declared_relations: list[tuple[list[Matrix], list[Matrix]]] = []
    accepted_receiver_versions: list[str] = Field(
        default=["receiver@0.9.0"],
        description=(
            "The receiver versions the reduction accepts (Assumption A-RECV); "
            "only the default is admitted."
        ),
    )
    lattice_exponent: Lattice = 40


class ChoiceWeighting(_Block):
    """The compiler's ``ChoiceWeighting``; ``matrix`` is keyed ``"setting|choice"``."""

    choices: list[Text]
    settings: list[Text]
    setting_of: Rules
    matrix: dict[str, Scalar]


class Station(_Block):
    """One station, in declared order; ``id`` is its factor label."""

    id: str
    party: Literal["A", "B"]
    declared_by: str | None = None
    measurement: Measurement
    reduction: Sw[Reduction]
    choice_weighting: ChoiceWeighting | None = None


# ---------------------------------------------------------------------------
#  public, constraints, honest, channel_interface
# ---------------------------------------------------------------------------


class Readout(_Block):
    """An alphabet and the rules mapping into it."""

    alphabet: AlphabetNode
    map: Rules


class Announcements(_Block):
    """The accepted format's two announcement maps."""

    alice: Readout
    bob: Readout


class ExplicitPartition(_Block):
    """A partition written as rules."""

    alice_readout: Readout
    bob_readout: Readout
    sector_factor_parties: dict[str, Literal["A", "B"]] = {}


class TranscriptMessage(_Block):
    """One message; ``alphabet: derived`` lists the table's values in order."""

    id: str
    sender: Literal["A", "B"]
    alphabet: AlphabetNode = Field(
        description=(
            "The message alphabet, or the word derived: the table's values in "
            "order of first appearance."
        )
    )
    table: Rules


class Transcript(_Block):
    """A transcript of any length."""

    messages: list[TranscriptMessage] = Field(min_length=1)


class AnnouncementAlphabets(_Block):
    """The parties' announcement alphabets under a transcript."""

    A: list[Text]
    B: list[Text]


class Key(_Block):
    """The key map: holder, alphabet and rules over ``(o, class)``."""

    holder: Literal["A", "B"]
    alphabet: list[StrictInt]
    rule: Rules


class Acceptance(_Block):
    """The acceptance map and, optionally, its alphabet order."""

    alphabet: list[Text] | None = None
    map: Rules


class Public(_Block):
    """The public part: partition, announcements or transcript, and the tables.

    Exactly one of announcements (two maps) and transcript (any number of
    messages) is given.
    """

    partition: Sw[Literal["default", "factor_projection"] | ExplicitPartition] = (
        "default"
    )
    announcements: Sw[Announcements] | None = Field(
        default=None,
        description=(
            "The accepted format's two announcement maps with their alphabets; "
            "may switch as a whole, where a choice changes an alphabet."
        ),
    )
    transcript: Transcript | None = None
    announcement_alphabets: AnnouncementAlphabets | None = None
    sifting: Rules
    key: Sw[Key]
    acceptance: Sw[Acceptance]

    @model_validator(mode="after")
    def _one_announcement_form(self) -> Public:
        if (self.announcements is None) == (self.transcript is None):
            raise ValueError(
                "the public part gives exactly one of announcements, transcript"
            )
        if self.announcement_alphabets is not None and self.transcript is None:
            raise ValueError("announcement_alphabets is for the transcript form only")
        return self


class Blocks(_Block):
    """An operator written as its sector blocks."""

    blocks: dict[str, Matrix]


class ConstraintEntry(_Block):
    """An explicit, flagged ``ConstraintEntry``."""

    label: str
    operator: Blocks
    relation: Literal["ge", "le", "eq"]
    rhs: Scalar | Matrix | Blocks
    tag: str | None = None
    scope: str | None = None


class Licence(_Block):
    """An explicit, flagged attack-set licence."""

    statement: str


class WitnessBlocks(_Block):
    """An explicit, flagged feasibility witness."""

    blocks: list[Matrix]


class Constraints(_Block):
    """Docking of the reductions' constraints, and the explicit, flagged escapes."""

    docked: Sw[StrictBool] = True
    party_local_view: Sw[Literal["operator", "licensed_scalar"]] | None = None
    entries: Sw[list[ConstraintEntry]] = []
    attack_set_license: Licence | None = None
    feasibility_witness: Sw[Literal["auto", "none"] | WitnessBlocks] = "auto"


class HonestLibrary(_Block):
    """An honest model from the engine's library, bound to parameter values."""

    library: str
    station: str | None = None
    bind: dict[str, Scalar] = {}
    note: dict[str, Any] = {}


class HonestAcceptanceTable(_Block):
    """A table over the acceptance alphabet."""

    acceptance_table: dict[str, Scalar]
    source: str
    note: dict[str, Any] = {}


class HonestRawTable(_Block):
    """A joint table over ``X x V``, keyed ``"x|v"``."""

    raw_table: dict[str, Scalar]
    source: str
    note: dict[str, Any] = {}


class EnvelopeBounds(_Block):
    """The two sides of an honest envelope."""

    lower: dict[str, Scalar]
    upper: dict[str, Scalar]


class HonestEnvelope(_Block):
    """``HonestEnvelope``."""

    envelope: EnvelopeBounds
    source: str
    note: dict[str, Any] = {}


type Honest = Sw[
    HonestLibrary | HonestAcceptanceTable | HonestRawTable | HonestEnvelope
]


class ChannelInterfaceBlock(_Block):
    """Which channel-interface builder applies."""

    variant: Literal[
        "qubit_identity", "single_photon", "mode_intensity", "bipartite", "none"
    ] = "none"
    source_model: Sw[StrictStr] | None = Field(
        default=None,
        description=(
            "bipartite only: the source model the interface names; default the "
            "honest model's name. Its parameters are the configuration's model "
            "section."
        ),
    )


# ---------------------------------------------------------------------------
#  the document
# ---------------------------------------------------------------------------


class ProtocolDocument(_Block):
    """A protocol document. Guide: instances/declared/README.md."""

    format: Literal["certiqs-key/protocol-document"]
    format_version: Literal["1", 1]
    identity: Identity
    parameters: Parameters
    presets: list[PresetBlock] = []
    snap: Snap | None = None
    preparations: list[Preparation] = []
    run_defaults: RunDefaults
    alphabets: dict[str, AlphabetNode] = {}
    source: Source
    stations: list[Station] = Field(min_length=1)
    public: Public
    constraints: Constraints | None = None
    honest: Honest
    channel_interface: ChannelInterfaceBlock | None = None
    #: Opaque, recorded verbatim, never read.
    annotations: dict[str, Any] = {}

    @model_validator(mode="after")
    def _derived_is_reserved(self) -> ProtocolDocument:
        if "derived" in self.alphabets:
            raise ValueError("'derived' names the derived message alphabet")
        return self


class _View(BaseModel):
    """A projection: reads the keys it names and ignores the rest."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class PortView(_View):
    """A port's label."""

    label: Text


class MeasurementView(_View):
    """A measurement's port labels, where it has ports."""

    ports: list[PortView] = []


class StationView(_View):
    """A station's id and port labels."""

    id: str
    measurement: MeasurementView | None = None


class StaticDocument(BaseModel):
    """The configuration-independent part of a document, or a fragment of one.

    Validates ``identity``, ``parameters``, ``presets``, ``snap``,
    ``preparations`` and ``run_defaults`` exactly as :class:`ProtocolDocument`
    does, reads only each station's id and port labels, and refuses a
    top-level key no document has. The other blocks are not read, so a
    fragment carrying only the static blocks validates; a whole document
    validates as :class:`ProtocolDocument` as well.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    format: Literal["certiqs-key/protocol-document"]
    format_version: Literal["1", 1]
    identity: Identity
    parameters: Parameters
    presets: list[PresetBlock] = []
    snap: Snap | None = None
    preparations: list[Preparation] = []
    run_defaults: RunDefaults
    stations: list[StationView] = []

    @model_validator(mode="before")
    @classmethod
    def _known_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            unknown = sorted(set(data) - set(ProtocolDocument.model_fields))
            if unknown:
                raise ValueError(f"no document has the top-level keys {unknown}")
        return data
