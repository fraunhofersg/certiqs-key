"""The emitted ``ReceiverMeasurementArtifact`` -- the fifteen keys of the outputs table.

The outputs table (``interface.yaml`` ``outputs``) is the payload of the
emitted artifact, key by key, and ``artifact_bindings.produces_note`` adds:
"No key beyond these fifteen is authorised."

EXACTLY ONE KEY IS CONDITIONAL
==============================
``receiver_construction`` is PRESENT EXACTLY WHEN ROUTE (iii) WAS USED and
ABSENT EXACTLY WHEN THE GRAMS OR THE INSTRUMENT MATRIX WERE SUPPLIED DIRECTLY
(``outputs.receiver_construction.presence_rule``). Both halves are a rule;
there is no third behaviour and no partial emission.
:meth:`ReceiverMeasurementArtifact.payload_keys` is that rule, and
:meth:`~ReceiverMeasurementArtifact.as_payload` emits exactly those keys.

WHAT IS NOT A KEY, AND WHY THE TIER IS NOT ONE
==============================================
The tier is NOT among the fifteen. An assurance is a property of the answer to
a REQUEST, not a field of the measurement description, so the requested
assurance rides on the emission record (:mod:`certiqs_key.receiver.construct`)
and the artifact stays at fifteen keys. What the artifact does carry is
``bound_evaluation``: ``rigorous`` where every setting's weight is the
enclosed one (Requirement ``req:rigorous-weight``), ``floating_point``
otherwise (Requirement ``req:evaluation-label``).

THE WIRE FORM OF ``receiver_construction``, ``efficiency_record`` AND THE
EMITTED ``R``
=========================================================================
The outputs table fixes the CONTENT of these three and NO WIRE FORM -- no field
names, no nesting, no encoding -- so naming them is a serialization decision of
this code with no proof-relevant content. ``efficiency_record`` is an object of
two members: ``rows``, every declared loss parameter as ``{value, element,
site}``, the value read as the parameter its element string names
(``detector-imperfections/req:efficiency-record``), and ``normalization``, the
factored loss with every declared efficiency beside the exact one compiled
(``detector-imperfections/req:normalization-record``), its rationals as exact
``p/q`` strings because the compiled efficiencies ARE those rationals.

**THE DECISION.** One JSON-shaped object per key, built by
:meth:`~ReceiverMeasurementArtifact.as_payload`, under three rules:

1. **Every index is a declared LABEL, never a position.** Ports appear as their
   declared labels, click patterns as sorted tuples of port labels, probe
   settings as their declared labels, modes as their declared labels. A payload
   is then readable, and joinable with the protocol declaration, without a
   second table mapping integers back to names -- which is the failure Requirement
   ``req:declared-alphabet`` names for the outcome alphabet and which applies to
   every other index for the same reason.
2. **Complex numbers are ``[re, im]`` pairs and matrices are row-major lists of
   them.** The evaluation model of Definition ``def:evaluation-model`` fixes the
   substrate as IEEE-754 double, so a pair of doubles is the whole content of
   an entry; a string encoding would invite a parser, and dropping the
   imaginary part would silently discard the retarder phase the
   ``waveplate_convention`` forbids dropping (``interface.yaml``
   ``conventions``).
3. **Nothing appears twice.** The port map is carried ONLY inside
   ``receiver_construction`` (no other key holds it); the Grams are carried only
   under ``port_grams``; the per-setting weights are carried only under
   ``high_photon_bounds`` and the per-setting BRANCH record only under
   ``bound_quantifier_domain``; the dark-count matrix stores only its non-zero
   entries, because (D2) makes every other entry zero by definition and storing
   the zeros would invite a consumer to sum over a dense matrix.

The emitted ``R`` additionally carries THREE SCALARS UNDER DISTINCT NAMES --
``r_min`` exactly as Eq. ``eq:rmin`` computes it, the capped coefficient
``rbar`` of Eq. ``eq:rbar`` and the composition correction ``delta_dc`` of
Eq. ``eq:darkdelta`` -- together with WHICH admissibility conditions were
checked rather than derived, which is the content of
``outputs.dark_count_channel`` with Remark ``rem:corrdark``: for the product
form both (D1) and (D2) are DERIVED (Theorem ``thm:dark-counts`` (i)); for a
declared ``R`` both must be CHECKED. The payload also names the inequality a
consumer composes with, Eq. ``eq:darkpmcslack``, because the same row states
it as part of the key's content, and not Eq. ``eq:darkpmc``, which holds only
for an exactly admissible ``R`` (Requirement ``req:dark-channel-record``).

THE WIRE FORM OF THE EXACT-WINDOW RECORD
========================================
``outputs.bound_quantifier_domain`` fixes the CONTENT -- per setting, the
declared depth ``m*_t``, the computed window values ``beta-hat*^(t)(n)`` for
``N < n <= m*_t`` that Eq. ``eq:elldef`` read ``p_mc^(t)`` from, and the fact
that Assumption ``ass:eig`` was invoked at that setting -- and fixes no field
names, no nesting and no encoding. The claims also fix what must NOT happen to
the numbers: Requirement ``req:exact-window-record`` has ``beta-hat*`` carried
in the artifact EXACTLY AS COMPUTED, so that a reader can recompute Eq.
``eq:elldef`` and see what the slack cost, and Remark ``rem:exacteig`` has no
computed value clamped into ``[0, 1]``.

**THE DECISION: one nested object under each per-setting row of
``bound_quantifier_domain``, keyed ``exact_window``, absent exactly where no
depth was declared** -- the same presence-is-the-rule shape
``receiver_construction`` already has, and the same three rules as above. It
carries the depth, the window rows ``(n, beta(n), beta-hat*(n), ell(n))``, the
window minimum, the middle minimum (``null`` where the index set is empty), the
remainder and its kind, and ``assumption_eig_invoked``. The row carries BOTH the
raw ``beta-hat*(n)`` and the ``ell(n)`` the inequality used, because that is
what makes the slack recomputable; neither is clamped.

HOW THE EMITTED PHOTON BLOCKS ARE INDEXED BY PROBE SETTING
==========================================================
The outputs table fixes one family per setting ``t`` in ``T``
(``outputs.photon_blocks``), the family being the CONDITIONAL one and complete
for each fixed ``t`` (``conventions.test_statistics_model``), the blocks
DARK-COMPOSED with their reference (Requirement ``req:dark-composed-reference``;
the bare blocks ride beside them until the consumer stops composing ``R``
itself, :class:`EmittedBlocks`), and for the bound BOTH the per-setting weights
and their minimum (``outputs.high_photon_bounds``). Whether the families are
keyed by the declared label, by an index into an ordering of ``T``, or by
nesting inside the block structure is NOT fixed.

**THE DECISION: keyed by the DECLARED probe-setting label, in the declared order
of ``T``.** ``T`` is a DATA-FLOW input supplied at run time by the protocol
declaration (``interface.yaml`` ``data_flow_inputs``), so the label is the
identifier the declaration itself uses; keying by it makes the artifact
joinable with the declaration without a second convention, while an index into
an ordering of ``T`` would be a convention this module chose and Theorem
``thm:emitted-bound`` quantifies over ``t`` as a SET MEMBER, not as a position.
It is the same reasoning as the outcome alphabet's ids
(:mod:`certiqs_key.receiver.coarse`), applied to the other declared alphabet.

**THE WIRE FORM OF ``photon_blocks``** is one object: ``exact_route``, the
decision of Requirement ``req:exact-route-decision`` (iv), once, because it is
a property of the declaration and not of a setting; and ``settings``, one entry
per setting with ``blocks`` (bare), ``dark_composed`` and ``reference`` -- the
kind offered per block with its largest radius, decision radius and leaf
radius, the cause where none is offered, and, where one is, its identity
(model, exact parameters, establishing claims) and the SHA-256 of its
enclosures written as exact rationals. The enclosures themselves are on the
artifact object (:attr:`EmittedBlocks.reference`) and not in the payload, which
travels in every preparation record and would grow to megabytes at a large
cutoff; the digest pins which reference was offered. The construction time of
the reference is a diagnostic of the object and is not in the payload either,
which must not depend on the machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Final

import numpy as np

from certiqs_key.receiver.bound import SettingBound
from certiqs_key.receiver.dark import DarkCountRoute
from certiqs_key.receiver.efficiency import EfficiencyRecord
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import Matrix, Scalar, to_float
from certiqs_key.receiver.reasons import AssumptionId
from certiqs_key.receiver.reference import SettingReference
from certiqs_key.receiver.residuals import Residual
from certiqs_key.receiver.snapfix import SnapFixContext

__all__ = [
    "ACCEPTED_CONTRACT_VERSION",
    "BOUND_EVALUATION",
    "COMPOSITION_RULE",
    "FIRST_VERSION_STATING_THE_PER_SETTING_WEIGHTS",
    "MATHEMATICAL_SPEC_VERSION",
    "OUTPUT_KEYS",
    "AssumptionRecord",
    "BlockDimension",
    "BoundQuantifierDomain",
    "DarkCountRecord",
    "EmittedBlocks",
    "HighPhotonBounds",
    "InputModeSpace",
    "OutcomeAlphabet",
    "ReceiverConstruction",
    "ReceiverMeasurementArtifact",
    "ResidualGap",
    "SlotEntry",
    "ValidationResults",
]

#: The accepted contract version this package implements: the outputs table's
#: `mathematical_spec_version` and the conventions section's last bullet ask for
#: the module id at the version OF THE ACCEPTED CONTRACT, and "an artifact may
#: not claim a draft version", so no `-draft` suffix can appear here.
#:
#: THE ACCEPTED VERSION IS A ``version`` OF spec/modules/receiver/module.yaml,
#: this repository's single source of truth for a module's version: the one
#: whose implementation is accepted. The pin moves with the code, so after a
#: presentational batch it trails the ``version:`` line (never passes it).
#: It is what a consumer reads to know whether the per-setting weights of
#: Thm. thm:emitted-bound (Eq. eq:pmcsetting) and Def. def:slot are stated
#: (reductions/wpfss req:supplier-version); FIRST_VERSION_STATING_THE_
#: PER_SETTING_WEIGHTS below names the first version that states them. The
#: frozen expectations that spell the string are edited by hand when it
#: moves, never regenerated from the code.
ACCEPTED_CONTRACT_VERSION: Final[str] = "0.9.0"
#: THE FIRST ACCEPTED VERSION WHOSE Thm. thm:emitted-bound CARRIES Eq. eq:pmcsetting
#: AND WHOSE Def. def:slot CARRIES A WEIGHT PER ENTRY AND SETTING. A fact about
#: this module's history, stated here once, for the consumer that must refuse
#: a per-setting read from an earlier version (reductions/wpfss
#: req:supplier-version; its interface key
#: `requires_a_receiver_version_stating_them`). Every version from this one on
#: states them; a version before it reported per-setting values beside the
#: minimum that were the content of no claim.
FIRST_VERSION_STATING_THE_PER_SETTING_WEIGHTS: Final[tuple[int, int, int]] = (0, 2, 0)
#: The emitted `mathematical_spec_version`. DERIVED FROM
#: :data:`ACCEPTED_CONTRACT_VERSION` and not a second literal, so the two cannot
#: drift, and :meth:`ReceiverMeasurementArtifact.__post_init__` raises on any
#: other value.
MATHEMATICAL_SPEC_VERSION: Final[str] = f"receiver@{ACCEPTED_CONTRACT_VERSION}"

#: interface.yaml `outputs.dark_count_channel`: "The inequality a consumer
#: composes with is Eq. eq:darkpmcslack, stated in rbar and delta_dc, not Eq.
#: eq:darkpmc, which holds only for an exactly admissible R" (Requirement
#: req:dark-channel-record). The artifact names it so that a consumer does not
#: have to infer which of the two the emitted scalars belong to.
COMPOSITION_RULE: Final[str] = (
    "eq:darkpmcslack: blk Mtilde^{(>N)}_{MC_K} >= ((1 - rbar) p_mc + rbar "
    "- delta_dc) id^{(>N)}"
)

#: interface.yaml `outputs.bound_evaluation` and Requirement req:evaluation-label:
#: `rigorous` where every setting's weight was formed by the rigorous evaluation
#: (req:rigorous-weight), `floating_point` otherwise; Theorem
#: thm:exact-and-evaluated (iii). The second is the fallback's label.
BOUND_EVALUATION: Final[str] = "floating_point"
BOUND_EVALUATIONS: Final[tuple[str, ...]] = ("rigorous", BOUND_EVALUATION)

#: The fifteen machine keys of the outputs table (interface.yaml `outputs`), in
#: the table's order.
OUTPUT_KEYS: Final[tuple[str, ...]] = (
    "input_mode_space",
    "outcome_alphabet",
    "port_grams",
    "receiver_construction",
    "photon_blocks",
    "block_dimensions",
    "efficiency_record",
    "dark_count_channel",
    "high_photon_bounds",
    "bound_quantifier_domain",
    "validation_results",
    "bound_evaluation",
    "assumption_ledger",
    "calibration_coverage",
    "mathematical_spec_version",
)


def _payload_scalar(value: Scalar) -> float:
    """Return an emitted scalar as the payload's machine number.

    THE MODULE'S EXISTING CONVENTION, applied unchanged: every declared exact
    parameter reaches the payload through
    :func:`~certiqs_key.receiver.numerics.to_float` at the serialization
    boundary (:func:`certiqs_key.receiver.construct._scalar` does the same for
    ``receiver_construction``), because the payload is JSON and a
    :class:`~fractions.Fraction` is not a JSON scalar.
    """
    return to_float(value)


def _exact_pair(value: Scalar) -> list[int]:
    """Return an emitted scalar as the exact pair ``[numerator, denominator]``.

    **THE SERIALIZATION DECISION FOR AN EXACT ENTRY OF ``R``, taken here.**
    Eq. ``eq:darkR`` is evaluated exactly on the generated route, and an
    artifact that then wrote the entries out as machine numbers would round
    away the very property the exact evaluation exists to give: a reader of
    the logged artifact could no longer see that the columns sum to exactly 1,
    which is Theorem ``thm:dark-counts`` (i) and the reason ``delta_dc`` is 0 on this
    route (Remark ``rem:d2slack``). So the exact value is carried BESIDE the
    machine number rather than instead of it: ``probability`` stays the
    ``float`` every existing reader expects, and ``probability_exact`` is the
    numerator/denominator pair, from which ``Fraction(n, d)`` reconstructs the
    entry EXACTLY.

    WHY A PAIR OF INTEGERS AND NOT A STRING OR A BARE FLOAT. Two integers are
    JSON-native, so the payload stays free of the ``Fraction`` objects the
    round-trip rule forbids, and they are exact in both directions, which a
    string is too but a float is not. A pair is also what rule 2 of the module
    docstring already uses for a complex entry, so the payload has one shape
    for ``a value that needs two numbers to be said exactly`` rather than two.

    A DECLARED ``float`` IS CARRIED EXACTLY TOO, and nothing is invented in
    doing so: a binary64 value IS a dyadic rational and ``Fraction(x)`` names
    it, so the pair on the declared route is the declarer's own number and not
    a rounding of it.
    """
    exact = Fraction(value)
    return [exact.numerator, exact.denominator]


def _complex_payload(value: complex) -> list[float]:
    """Return a complex number as the ``[re, im]`` pair of the module's rule 2."""
    return [float(value.real), float(value.imag)]


def _blocks_payload(
    blocks: tuple[tuple[int, tuple[tuple[str, Matrix], ...]], ...],
) -> list[dict[str, object]]:
    """Return one setting's blocks, per photon number and letter."""
    return [
        {
            "photons": photons,
            "elements": [
                {"letter": letter, "block": _matrix_payload(block)}
                for letter, block in letters
            ],
        }
        for photons, letters in blocks
    ]


def _matrix_payload(matrix: Matrix) -> list[list[list[float]]]:
    """Return a matrix as row-major lists of ``[re, im]`` pairs."""
    array = np.asarray(matrix, dtype=np.complex128)
    return [[_complex_payload(complex(entry)) for entry in row] for row in array]


def _setting_payload(record: SettingBound) -> dict[str, object]:
    """Return one per-setting row of ``bound_quantifier_domain``.

    The branch fields, plus the exact-window object of the module docstring,
    PRESENT EXACTLY WHERE A DEPTH WAS DECLARED and absent everywhere else. The
    absence is the rule and not an omission: at a setting governed by
    Definition ``def:pmc`` no ``beta*`` was formed, so there is nothing to
    report, and a row of zeros would report a computation that was not made.

    ``definition`` names which of Definition ``def:pmc`` and Definition
    ``def:pmcex`` produced the value, which is what Requirement
    ``req:weight-provenance`` asks for: the artifact says WHICH of the two
    definitions PRODUCED EACH weight AND AT WHAT DEPTH.
    """
    row: dict[str, object] = {
        "setting": record.setting,
        "branch": str(record.branch),
        "predicate_x": record.predicate_x,
        "window": record.window,
        "definition": record.definition,
        "assumption_eig_invoked": record.assumption_eig_invoked,
        "evaluation": record.evaluation,
        "fallback_reason": record.fallback_reason,
        "enclosed": None if record.enclosed is None else dict(record.enclosed),
        "floating_point_weight": record.floating_point_weight,
    }
    exact = record.exact_window
    if exact is not None:
        row["exact_window"] = {
            "depth": exact.depth,
            # beta-hat* EXACTLY AS COMPUTED, beside the analytic bound and the
            # ell the inequality used, so that Eq. eq:elldef is recomputable
            # and the cost of eps_eig is visible (Req. req:exact-window-record).
            "window": [
                {
                    "photons": photons,
                    "beta": analytic,
                    "beta_star_computed": computed,
                    "ell": floor,
                }
                for photons, analytic, computed, floor in exact.rows
            ],
            "window_minimum": exact.window_minimum,
            "middle_minimum": exact.middle_minimum,
            "middle_window_empty": exact.middle_window_empty,
            "remainder": exact.remainder,
            "remainder_kind": exact.remainder_kind,
        }
    return row


@dataclass(frozen=True)
class InputModeSpace:
    """``input_mode_space``: the ordered labels and the channel/probe split.

    Two orders, and both are emitted because they are different objects
    (``interface.yaml`` ``conventions.subsystem_order``): ``mode_labels`` is
    the order ``M`` is LISTED in, Definition ``def:modes``'s lexicographic key;
    ``input_labels`` is the order that INDEXES ``C^Inp`` and therefore every
    Gram and every block matrix, ``Inp_C`` before ``Inp_S``.
    """

    mode_labels: tuple[str, ...]
    input_labels: tuple[str, ...]
    channel_labels: tuple[str, ...]
    source_labels: tuple[str, ...]


@dataclass(frozen=True)
class OutcomeAlphabet:
    """``outcome_alphabet``: the ordered emitted alphabet and ``cg``.

    Stable ids, the labels presentation metadata (``interface.yaml``
    ``outputs.outcome_alphabet``). The ID is the letter's position in the
    DECLARED order of ``V`` (decided in :mod:`certiqs_key.receiver.coarse`);
    ``fibres`` is the declared surjection written out, click patterns as sorted
    tuples of PORT LABELS.
    """

    letters: tuple[tuple[int, str], ...]
    fibres: tuple[tuple[str, tuple[tuple[str, ...], ...]], ...]


@dataclass(frozen=True)
class ReceiverConstruction:
    """``receiver_construction``: present exactly when route (iii) was used.

    ``interface.yaml`` ``outputs.receiver_construction``: the declared element
    graph WITH EVERY PARAMETER, the port map, and the probe declaration -- THE
    REPRODUCIBLE INPUT THE GRAMS WERE COMPUTED FROM. This is the only key that
    carries the port map (rule 3 of the module docstring).
    """

    elements: tuple[
        tuple[str, str, tuple[str, ...], tuple[tuple[str, object], ...]], ...
    ]
    edges: tuple[tuple[str, str], ...]
    port_map: tuple[tuple[str, tuple[str, ...]], ...]
    probe_declaration: tuple[tuple[str, tuple[float, ...]], ...]


@dataclass(frozen=True)
class EmittedBlocks:
    """``photon_blocks`` at one probe setting -- one family per declared setting.

    THREE THINGS PER SETTING (``interface.yaml`` ``outputs.photon_blocks``):

    * ``blocks`` -- the BARE binary64 blocks of the COARSE-GRAINED POVM, before
      the dark-count channel, on which the residual ``r_5`` runs
      (``req:residual-emission``). The docking hands them unless asked for the
      dark-composed ones and states the form it handed in the consumer's
      ``photon_blocks_form``; ``reductions/wpfss`` composes ``R`` into blocks
      handed in this form and into no other (``def:weight-route``,
      ``rem:darkcompose``, ``lem:descent``; the interface row's
      ``who_composes_note``);
    * ``dark_composed`` -- the binary64 blocks of the DARK-COMPOSED family,
      ``Ftilde_v = sum_{S'} R_{cg^-1(v)|S'} M_{S'}`` (Requirement
      ``req:dark-composed-reference`` (i)), already composed with the
      artifact's ``dark_count_channel``; a consumer reading these does not
      compose ``R`` again (item (v));
    * ``reference`` -- the reference the receiver offers for a snap of the
      dark-composed family at this setting, exact or enclosed, with the kind
      offered per block, or none with its cause (items (ii)-(iv)), and the
      exact-route decision of Requirement ``req:exact-route-decision`` (iv).

    ``fix_context`` is not a payload field: it is what the fixes of
    Requirement ``req:snap-fix`` read about this declaration
    (:func:`certiqs_key.receiver.snapfix.receiver_fixes`), for the declaring
    instance that records a snap of the family.

    Remark ``rem:blockmeaning``: the blocks are operators on the channel space
    and are NOT the compressions of the full elements.
    """

    setting: str
    blocks: tuple[tuple[int, tuple[tuple[str, Matrix], ...]], ...]
    dark_composed: tuple[tuple[int, tuple[tuple[str, Matrix], ...]], ...]
    reference: SettingReference
    fix_context: SnapFixContext


@dataclass(frozen=True)
class BlockDimension:
    """``block_dimensions``: the expected dimension and the basis order.

    ``binom(|Inp_C| + n - 1, n)`` with the occupation-vector basis order of
    Definition ``def:fock``, ascending lexicographic (``interface.yaml``
    ``conventions.subsystem_order``).
    """

    photons: int
    dimension: int
    occupation_vectors: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class DarkCountRecord:
    """``dark_count_channel``: the matrix, three scalars, and what was checked.

    Only the NON-ZERO entries of each column are stored (rule 3 of the module
    docstring). Remark ``rem:corrdark`` fixes ``conditions_*``: for the product
    form both conditions are DERIVED (Theorem ``thm:dark-counts`` (i)); for a
    declared ``R`` both must be CHECKED, and the artifact records which of the
    two routes the emitted ``R`` came from.

    THE THREE SCALARS ARE THREE OBJECTS, NOT ONE REPAIRED TWICE
    (``interface.yaml`` ``outputs.dark_count_channel``; Requirement
    ``req:dark-channel-record``; Remark ``rem:d2slack``):

    * ``r_min`` is Eq. ``eq:rmin`` AS COMPUTED and is EMITTED UNMODIFIED. It may
      exceed 1 and it may be negative, both reachable under the widened (D1),
      and it is the only one from which a reader can see that a declared
      channel produced ``r_min > 1`` at all, ITSELF A SIGNAL THAT THE
      DECLARATION IS OFF BY MORE THAN ROUNDING (the lead-in of Requirement
      ``req:dark-channel-record``);
    * ``r_bar`` is Eq. ``eq:rbar``, ``min{r_min, 1}``: a COEFFICIENT in a stated
      inequality, not a repair of ``r_min`` and not a clamp of ``R`` (Remark
      ``rem:d2slack`` (d)). It is NOT floored at 0;
    * ``delta_dc`` is Eq. ``eq:darkdelta``, a function of the ROUTE and the
      declared tolerances alone.

    ``composition_rule`` names Eq. ``eq:darkpmcslack`` as the inequality a
    consumer composes with, which ``outputs.dark_count_channel`` and
    Requirement ``req:dark-channel-record`` state and which is NOT Eq.
    ``eq:darkpmc``.

    THE ENTRIES AND THE TWO SCALARS ARE
    :data:`~certiqs_key.receiver.numerics.Scalar`, NOT ``float``, AND ON THE
    GENERATED ROUTE THEY ARE EXACT. Eq. ``eq:darkR`` is evaluated in exact
    rational arithmetic (:func:`certiqs_key.receiver.dark.product_form`), so the
    emitted ``R`` has columns summing to EXACTLY 1 and ``r_min`` and ``rbar``
    are the exact rationals Eq. ``eq:rmin`` and Eq. ``eq:rbar`` define. That
    is what makes Theorem ``thm:dark-counts`` (i)'s (D1) and (D2) BY CONSTRUCTION
    true of the matrix this record carries, and it is why Remark
    ``rem:d2slack`` may set ``delta_dc = 0`` on this route: there is no slack
    to carry because there is none. On the DECLARED route the entries are the
    declarer's own numbers, unrepaired, decided at ``eps_4``/``eps_2`` by
    Definition ``def:tolmap`` (iii).
    """

    route: DarkCountRoute
    columns: tuple[
        tuple[tuple[str, ...], tuple[tuple[tuple[str, ...], Scalar], ...]], ...
    ]
    r_min: Scalar
    r_bar: Scalar
    delta_dc: float
    conditions_derived: tuple[str, ...]
    conditions_checked: tuple[str, ...]
    composition_rule: str = COMPOSITION_RULE


@dataclass(frozen=True)
class SlotEntry:
    """One entry ``(O_i, (p_i^(t))_{t in T})`` of the slot, Definition ``def:slot``.

    ``per_setting`` is the entry's weight AT EACH DECLARED SETTING, in the
    declared order of ``T``: the GUARANTEED CONTENT,
    ``sum_{S in O_i} blk M^{(>N)}_{S|t} >= p_i^(t) 1`` at that setting (Theorem
    ``thm:emitted-bound``, Eq. ``eq:pmcsetting``). ``weight`` is the entry's
    UNIFORM WEIGHT ``p_i = min_t p_i^(t)``, guaranteed at every setting
    (Eq. ``eq:pmcstatement``); a one-setting entry has one weight and the two
    are one number, the ``(O_i, p_i)`` of Definition ``def:slot``'s one-setting
    clause. The two are formed by
    :func:`~certiqs_key.receiver.bound.emitted_weights` and
    :func:`~certiqs_key.receiver.bound.emitted_weight` from the same per-setting
    records, and a record in which the uniform weight is not their minimum is a
    programming error and is raised.
    """

    outcome_set: tuple[tuple[str, ...], ...]
    per_setting: tuple[tuple[str, float], ...]
    weight: float

    def __post_init__(self) -> None:
        """Refuse an entry whose uniform weight is not its per-setting minimum."""
        if not self.per_setting:
            raise HypothesisError(
                "a slot entry carries a weight at every declared setting, and T "
                "is non-empty (Definition def:slot)"
            )
        if self.weight != min(weight for _, weight in self.per_setting):
            raise HypothesisError(
                f"the uniform weight {self.weight!r} of a slot entry is the minimum "
                "over T of its per-setting weights (Definition def:slot), which "
                f"is {min(weight for _, weight in self.per_setting)!r}"
            )


@dataclass(frozen=True)
class HighPhotonBounds:
    """``high_photon_bounds``: the strengthening slot, one weight per setting.

    ``interface.yaml`` ``outputs.high_photon_bounds``: the SINGLE entry
    ``(MC_K, (p_mc^(t))_{t in T})``, ONE WEIGHT PER PROBE SETTING, EACH
    GUARANTEED AT ITS OWN SETTING (Theorem ``thm:emitted-bound``, Eq.
    ``eq:pmcsetting``), together with the entry's UNIFORM WEIGHT ``p_mc``.
    Like ``photon_blocks``, this is the BARE pre-dark-count bound. The
    per-setting weights live in the entry and nowhere else, so the payload
    carries them once (rule 3 of the module docstring); :attr:`per_setting` is
    a READING of the single entry, not a second record.
    """

    entries: tuple[SlotEntry, ...]

    @property
    def per_setting(self) -> tuple[tuple[str, float], ...]:
        """Return ``(t, p_mc^(t))`` of the single entry, in the order of ``T``."""
        if len(self.entries) != 1:
            raise HypothesisError(
                "this module emits r = 1 slot entry (Definition def:slot); the "
                "per-setting weights are read per entry otherwise"
            )
        return self.entries[0].per_setting


@dataclass(frozen=True)
class BoundQuantifierDomain:
    """``bound_quantifier_domain``: the literal statement and the branch record.

    ``interface.yaml`` ``outputs.bound_quantifier_domain``: the literal
    statement ``for all n > N and all t in T``, with ``N`` and ``T`` echoed;
    and, PER SETTING, which branch of Definition ``def:pmc`` was taken -- BRANCH
    1 EXACTLY WHERE PREDICATE (X) HOLDS -- and the declared window ``m_t`` where
    branch 2 was. The branch-1 selector is predicate (X) alone
    (``one_predicate_note``), so each
    :class:`~certiqs_key.receiver.bound.SettingBound` carries the branch,
    ``(X)`` and the window, and no fourth field.

    WHERE A DEPTH ``m*_t`` WAS DECLARED the row also carries the depth, the
    computed window values ``beta-hat*^(t)(n)``, ``N < n <= m*_t``, that Eq.
    ``eq:elldef`` read ``p_mc^(t)`` from, and the fact that Assumption
    ``ass:eig`` was invoked at that setting, because the emitted ``p_mc`` is a
    function of declared data alone only at a setting governed by Definition
    ``def:pmc``; at a setting governed by Definition ``def:pmcex`` it is a
    function of the declared data AND OF THOSE COMPUTED WINDOW VALUES, which is
    why they are carried here (``computed_values_note``).
    """

    statement: str
    photon_cutoff: int
    probe_alphabet: tuple[str, ...]
    per_setting: tuple[SettingBound, ...]


@dataclass(frozen=True)
class ResidualGap:
    """The achieved residual gap Eq. ``eq:resgap`` at one setting.

    ``interface.yaml`` ``outputs.validation_results``: reported AT EACH
    SETTING THAT DECLARES A WINDOW, and a FINITE REAL by Lemma
    ``lem:windowtail`` (ii).
    """

    setting: str
    window: int
    gap: float
    tolerance: float

    @property
    def passes(self) -> bool:
        """Return whether the achieved gap is within the declared eps_gap."""
        return self.gap <= self.tolerance


@dataclass(frozen=True)
class ValidationResults:
    """``validation_results``: the residuals that exist, and the achieved gaps.

    Each WITH PASS OR FAIL AGAINST ITS DECLARED TOLERANCE (``interface.yaml``
    ``outputs.validation_results``), and with the NORM named beside them -- the
    SPECTRAL norm, which Definition ``def:residuals`` states.

    THE RESIDUAL SET FOLLOWS THE ROUTE AND THE REQUEST. ``r_2``, ``r_4`` and
    ``r_5`` on every route; ``r_1`` and ``r_3`` on routes (ii) and (iii) ONLY;
    ``r_6`` exactly at the settings carrying an exact-window depth. On route
    (i) the keys of ``r_1`` and ``r_3`` are simply NOT IN ``residuals`` --
    absent, exactly as ``receiver_construction`` is absent off route (iii), and
    NOT EMITTED AS ZERO, WHICH WOULD REPORT A CHECK THAT WAS NOT MADE
    (Requirement ``req:residual-emission``). Nothing in this class fills a
    missing row in, and the payload is a list of the rows that exist.
    """

    norm: str
    residuals: tuple[Residual, ...]
    residual_gaps: tuple[ResidualGap, ...]


@dataclass(frozen=True)
class AssumptionRecord:
    """One row of ``assumption_ledger``.

    ``interface.yaml`` ``outputs.assumption_ledger``: the MACHINE KEYS of the
    assumption files, WITH THE DECLARED VALUES OF THE PARAMETERS EACH ONE
    CONSTRAINS. ``never_verified`` is ``True`` for exactly the rows
    of ``never_verified_set`` (``req:decidable-assumptions``): the assumptions
    whose ``verification`` header field is ``never`` (spec/claim-format.md
    section 3.2), :data:`~certiqs_key.receiver.reasons.NEVER_VERIFIED`. Every
    row has the same four fields on every artifact; no field is conditional.
    """

    assumption_id: AssumptionId
    machine_key: str
    never_verified: bool
    constrains: tuple[tuple[str, object], ...]


def _assumption_payload(row: AssumptionRecord) -> dict[str, object]:
    """Return one row of ``assumption_ledger`` in the payload's wire form."""
    return {
        "id": str(row.assumption_id),
        "machine_key": row.machine_key,
        "never_verified": row.never_verified,
        "constrains": dict(row.constrains),
    }


@dataclass(frozen=True)
class ReceiverMeasurementArtifact:
    """The emitted artifact: the fifteen keys of the outputs table and no more.

    ``receiver_construction`` is ``None`` exactly on routes (i) and (ii) and
    present exactly on route (iii); :meth:`payload_keys` and
    :meth:`as_payload` enforce both halves of that rule.
    """

    input_mode_space: InputModeSpace
    outcome_alphabet: OutcomeAlphabet
    port_grams: tuple[tuple[str, Matrix], ...]
    receiver_construction: ReceiverConstruction | None
    photon_blocks: tuple[EmittedBlocks, ...]
    block_dimensions: tuple[BlockDimension, ...]
    efficiency_record: EfficiencyRecord
    dark_count_channel: DarkCountRecord
    high_photon_bounds: HighPhotonBounds
    bound_quantifier_domain: BoundQuantifierDomain
    validation_results: ValidationResults
    bound_evaluation: str
    assumption_ledger: tuple[AssumptionRecord, ...]
    calibration_coverage: str
    mathematical_spec_version: str

    def __post_init__(self) -> None:
        """Refuse an artifact that misreports the numerics or the spec version.

        Neither is a validation of declared data -- both are constants of this
        version -- so a wrong value is a programming error and is raised, not
        refused. Requirement ``req:evaluation-label``: ``bound_evaluation`` is
        ``floating_point`` on every artifact; ``interface.yaml``
        ``outputs.mathematical_spec_version``: "an artifact may not claim a
        draft version".
        """
        rigorous = all(
            record.evaluation == "rigorous"
            for record in self.bound_quantifier_domain.per_setting
        )
        if self.bound_evaluation != BOUND_EVALUATIONS[0 if rigorous else 1]:
            raise HypothesisError(
                f"bound_evaluation is {self.bound_evaluation!r}; it is `rigorous` "
                "exactly where every setting's weight is (req:evaluation-label)"
            )
        if self.mathematical_spec_version != MATHEMATICAL_SPEC_VERSION:
            raise HypothesisError(
                f"mathematical_spec_version is "
                f"{self.mathematical_spec_version!r}; the outputs table fixes it to "
                f"{MATHEMATICAL_SPEC_VERSION!r} of the ACCEPTED contract"
            )

    def payload_keys(self) -> tuple[str, ...]:
        """Return the keys this artifact emits, in the outputs table's order.

        The ``receiver_construction`` presence rule, both halves: present
        exactly when route (iii) was used, absent exactly when the Grams or the
        instrument matrix were supplied directly.
        """
        if self.receiver_construction is not None:
            return OUTPUT_KEYS
        return tuple(key for key in OUTPUT_KEYS if key != "receiver_construction")

    def as_payload(self) -> dict[str, object]:
        """Return the artifact as a JSON-ready payload -- the module's wire form.

        Every value is a ``str``, ``int``, ``float``, ``bool``, ``list`` or
        ``dict``; every index is a declared label; every complex number is an
        ``[re, im]`` pair; and nothing appears twice.
        """
        payload: dict[str, object] = {
            "input_mode_space": {
                "mode_labels": list(self.input_mode_space.mode_labels),
                "input_labels": list(self.input_mode_space.input_labels),
                "channel_labels": list(self.input_mode_space.channel_labels),
                "source_labels": list(self.input_mode_space.source_labels),
            },
            "outcome_alphabet": {
                "letters": [
                    {"id": identifier, "label": label}
                    for identifier, label in self.outcome_alphabet.letters
                ],
                "coarse_graining": [
                    {"letter": letter, "fibre": [list(pattern) for pattern in fibre]}
                    for letter, fibre in self.outcome_alphabet.fibres
                ],
            },
            "port_grams": [
                {"port": label, "gram": _matrix_payload(matrix)}
                for label, matrix in self.port_grams
            ],
            "photon_blocks": {
                "exact_route": (
                    self.photon_blocks[0].reference.exact_route.as_record()
                    if self.photon_blocks
                    else None
                ),
                "settings": [
                    {
                        "setting": family.setting,
                        "blocks": _blocks_payload(family.blocks),
                        "dark_composed": _blocks_payload(family.dark_composed),
                        "reference": family.reference.as_record(),
                    }
                    for family in self.photon_blocks
                ],
            },
            "block_dimensions": [
                {
                    "photons": row.photons,
                    "dimension": row.dimension,
                    "occupation_vectors": [list(v) for v in row.occupation_vectors],
                }
                for row in self.block_dimensions
            ],
            "efficiency_record": {
                "rows": [
                    {
                        "value": row.value,
                        "element": row.element,
                        "site": row.site,
                    }
                    for row in self.efficiency_record.rows
                ],
                "normalization": self.efficiency_record.normalization.as_payload(),
            },
            "dark_count_channel": {
                "route": str(self.dark_count_channel.route),
                "columns": [
                    {
                        "column": list(column),
                        "entries": [
                            {
                                "row": list(row),
                                "probability": _payload_scalar(value),
                                "probability_exact": _exact_pair(value),
                            }
                            for row, value in entries
                        ],
                    }
                    for column, entries in self.dark_count_channel.columns
                ],
                "r_min": _payload_scalar(self.dark_count_channel.r_min),
                "r_bar": _payload_scalar(self.dark_count_channel.r_bar),
                "delta_dc": self.dark_count_channel.delta_dc,
                "conditions_derived": list(self.dark_count_channel.conditions_derived),
                "conditions_checked": list(self.dark_count_channel.conditions_checked),
                "composition_rule": self.dark_count_channel.composition_rule,
            },
            "high_photon_bounds": {
                "entries": [
                    {
                        "outcome_set": [list(pattern) for pattern in entry.outcome_set],
                        "weight": entry.weight,
                        "per_setting": [
                            {"setting": setting, "weight": weight}
                            for setting, weight in entry.per_setting
                        ],
                    }
                    for entry in self.high_photon_bounds.entries
                ],
            },
            "bound_quantifier_domain": {
                "statement": self.bound_quantifier_domain.statement,
                "photon_cutoff": self.bound_quantifier_domain.photon_cutoff,
                "probe_alphabet": list(self.bound_quantifier_domain.probe_alphabet),
                "per_setting": [
                    _setting_payload(record)
                    for record in self.bound_quantifier_domain.per_setting
                ],
            },
            "validation_results": {
                "norm": self.validation_results.norm,
                "residuals": [
                    {
                        "residual": residual.residual_id,
                        "photons": residual.photons,
                        "value": residual.value,
                        "tolerance": residual.tolerance,
                        "passes": residual.passes,
                    }
                    for residual in self.validation_results.residuals
                ],
                "residual_gaps": [
                    {
                        "setting": gap.setting,
                        "window": gap.window,
                        "gap": gap.gap,
                        "tolerance": gap.tolerance,
                        "passes": gap.passes,
                    }
                    for gap in self.validation_results.residual_gaps
                ],
            },
            "bound_evaluation": self.bound_evaluation,
            "assumption_ledger": [
                _assumption_payload(row) for row in self.assumption_ledger
            ],
            "calibration_coverage": self.calibration_coverage,
            "mathematical_spec_version": self.mathematical_spec_version,
        }
        construction = self.receiver_construction
        if construction is not None:
            payload["receiver_construction"] = {
                "route": "element_graph",
                "elements": [
                    {
                        "name": name,
                        "entry_id": entry_id,
                        "support": list(support),
                        "parameters": dict(parameters),
                    }
                    for name, entry_id, support, parameters in construction.elements
                ],
                "edges": [list(edge) for edge in construction.edges],
                "port_map": [
                    {"port": label, "modes": list(modes)}
                    for label, modes in construction.port_map
                ],
                "probe_declaration": [
                    {"setting": label, "mean_photon_numbers": list(values)}
                    for label, values in construction.probe_declaration
                ],
            }
        return {key: payload[key] for key in self.payload_keys()}
