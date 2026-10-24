"""The request-to-artifact machine: validate, construct, and emit or refuse.

One entry point, :func:`construct_receiver`, and one outcome record,
:class:`ReceiverEmission`. ``interface.yaml`` ``conventions.fail_closed``:
"every failed validation produces a refusal with a machine-readable reason and
no artifact" -- so an emission carries an artifact or a refusal, never both and
never neither.

THE ORDER OF THE PASS
=====================
1. VALIDATE the declared inputs (:mod:`certiqs_key.receiver.request`). Everything
   decidable before a Gram exists is decided there, including the window
   requirement (Requirement ``req:window-declaration``, decidable by Remark
   ``rem:flag-instances``), and the refusal of a receiver with source modes
   where the submodule that conditions on them is absent.
2. CONSTRUCT the canonical object. The three routes converge here and nowhere
   earlier (``interface.yaml`` ``input_routes.convergence``): route (iii)
   compiles the graph by Theorem ``thm:compilation-well-defined``, route (ii)
   restricts the supplied matrix to the declared input columns by Theorem
   ``thm:port-grams`` (iv), route (i) IS the Gram family.
3. APPLY THE EFFICIENCY, exactly once, at the one structural site. On routes
   (ii) and (iii) that is the terminal left factor ``D_eta`` of Definition
   ``def:compile``, so the Grams read off the product are ``eta_k A_k``
   already; on route (i) there is no matrix, and Eq. ``eq:etagram`` is the same
   substitution applied to the declared family. Either way the efficiency
   enters ONCE and the emitted ``port_grams`` are the canonical object, on
   ``Inp``, AFTER the efficiency layer (``interface.yaml``
   ``outputs.port_grams``). For a receiver without source modes the
   efficiencies applied are the NORMALIZED station's, ``eta_k / t`` exactly
   (``detector-imperfections/req:efficiency-normalization``): validation
   hands this pass the normalized station's request, so this step, and every
   later one, cannot tell the two apart, and the factor ``t`` travels in the
   efficiency record (``req:normalization-record``).
4. FORM THE SETTING FAMILY, one no-click pair family per declared setting
   (Definition ``def:setting-family``), through the one seam
   :func:`~certiqs_key.receiver.settings.setting_construction`. With no probe
   it is the core's (Corollary ``cor:unconditioned-family``), which is
   Definition ``def:probe``'s "every statement about conditioning is
   vacuous"; with source modes it is the probe-conditioning submodule's, a
   NAMED DOWNSTREAM MAP and not a fourth route.
5. EVALUATE the blocks, the bound and the dark-count channel.
5a. DECIDE Definition ``def:tolmap`` (iv) on the bound data each setting
   yields, at the declared ``eps_2``, and REFUSE where it does not admit them.
   The decision is at the REQUEST BOUNDARY and its outcome is a refusal record
   naming the check, because item (iv) is a validation the contract states on
   declared data and the ``fail_closed`` convention governs every one of those
   (Requirement ``req:tolerance-tests``). :func:`construct_receiver` never
   raises on it.
5b. AT EVERY SETTING WHOSE DECLARATION CARRIES AN EXACT-WINDOW DEPTH, and at no
   other, form the blocks ``blk M_mc^{(=n)}`` for ``N < n <= m*_t`` and compute
   ``beta-hat*^(t)(n)`` (Definition ``def:exactbnd``); the emitted value is then
   Eq. ``eq:pmcex`` instead of Eq. ``eq:pmcdef``. **Where no depth is declared
   this step does not happen at all**, which is Definition ``def:pmc``'s
   invariant realized structurally rather than by a branch that agrees: "no
   ``beta*`` is formed, no eigenvalue of any block above the cutoff is computed,
   and Assumption ``ass:eig`` is not invoked".
6. REPORT the residuals of Definition ``def:residuals`` -- only those that
   exist on the route taken AND FOR THE EVALUATION REQUESTED (Requirement
   ``req:residual-emission``) -- and REFUSE where one exceeds its declared
   tolerance: a residual above its tolerance is a REFUSAL, not a warning
   (Requirement ``req:residual-refusal``). ``r_5`` is evaluated LAST on the
   emitted blocks themselves, because it is a maximum over every emitted
   ``v``, ``n`` and ``t`` at once; ``r_6`` is evaluated from the exact-window
   records the emitted values were read from, is a maximum over every setting
   carrying a depth and every index its depth names, and its key is ABSENT --
   not zero -- where no depth was declared.
7. EMIT the artifact, and answer the requested assurance fail-closed.

WHERE THE DARK-COUNT CHANNEL IS COMPOSED IN, AND WHERE NOT
=========================================================
``interface.yaml`` ``outputs.dark_count_channel.not_composed_note``: dark
counts are emitted as the channel ``R`` with ``r_min``, ``rbar`` and
``delta_dc``, are composed into the emitted photon blocks (Requirement
``req:dark-composed-reference``) and NOT into ``p_mc``; the consumer composes
them into the high-photon bound with Eq. ``eq:darkpmcslack`` (Requirement
``req:dark-channel-record``). Each setting's ``photon_blocks`` entry carries the
dark-composed blocks beside the bare ones (:class:`~certiqs_key.receiver.
artifact.EmittedBlocks`), and ``R`` is composed into the dark-composed blocks
once and not again (``outputs.photon_blocks.who_composes_note``): the docking
hands the bare blocks unless asked for the dark-composed ones and states which
it handed in the consumer's ``photon_blocks_form``, and ``reductions/wpfss``
composes ``R`` only into blocks handed in the bare form
(``reductions/wpfss/def:weight-route``). The step that builds them runs before
the residuals, and the residual ``r_5`` is evaluated on the bare blocks, before
any dark-count channel (``req:residual-emission``). :func:`_dark_record`
computes the three scalars and nothing in this pass applies them to an emitted
``p_mc``.

THE REFERENCE IS BUILT ON THE EXACT ISLAND, NEVER FROM THE BINARY64 BLOCKS
=========================================================================
:func:`~certiqs_key.receiver.reference.dark_composed_reference` decides the
exact route and encloses the dark-composed blocks from the declared values in
exact rational arithmetic (Requirements ``req:exact-route-decision``,
``req:dark-composed-reference``). It reads the validated request and the
emitted ``R`` and nothing this pass computed in floating point; it never
refuses: a declaration without a model admissible exactly gets a record whose
offered kind is ``none`` with its cause, and is not a refusal of the receiver
(``req:exact-route-decision`` (iv)).

THE TIER IS ANSWERED, NEVER GRANTED
===================================
Theorem ``thm:exact-and-evaluated`` (iii): an artifact whose Grams were
computed by the route-(iii) compiler carries the floating-point evaluation
label, and so does every other artifact of this module; NO PATH IN THIS MODULE
PRODUCES A STRONGER LABEL (Requirement ``req:evaluation-label``). And (iv) adds
that where the Grams are DECLARED the eigenvalue quantities of Theorem
``thm:multiclick-bound`` are STILL EVALUATED IN FLOATING POINT, SO (iii) STILL
APPLIES -- so the rule covers ALL THREE ROUTES, and reading (iv) as an
exemption for route (i) would be reading a narrowing of scope as a licence.
:func:`resolve_assurance` is that rule, and it has no branch that can return
``certified``. THE FALLBACK STRING IS NOT IN THIS MODULE'S VOCABULARY:
Requirement ``req:evaluation-label`` says ``receiver_grams_not_enclosed`` is
never produced (``interface.yaml`` ``refusals.tier_fallback``),
:class:`~certiqs_key.receiver.reasons.RefusalReason` has no such member, and
the reason slot is ``None`` on every path.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, replace
from typing import Final

import numpy as np

from certiqs_key.foundations.dyadic import float_down
from certiqs_key.receiver.artifact import (
    BOUND_EVALUATION,
    MATHEMATICAL_SPEC_VERSION,
    AssumptionRecord,
    BlockDimension,
    BoundQuantifierDomain,
    DarkCountRecord,
    EmittedBlocks,
    HighPhotonBounds,
    InputModeSpace,
    OutcomeAlphabet,
    ReceiverConstruction,
    ReceiverMeasurementArtifact,
    ResidualGap,
    SlotEntry,
    ValidationResults,
)
from certiqs_key.receiver.bound import (
    SettingBound,
    bound_data_from_family,
    check_bound_data_admissible,
    emitted_weight,
    emitted_weights,
    exact_window_values,
    setting_bound,
)
from certiqs_key.receiver.coarse import CoarseGraining, coarse_blocks
from certiqs_key.receiver.dark import (
    DarkCountChannel,
    DarkCountRoute,
    capped_coefficient,
    compose_blocks,
    composition_correction,
    minimum_multiclick_mass,
    product_form,
)
from certiqs_key.receiver.efficiency import (
    EfficiencyRecord,
    apply_uniform_efficiency,
    detector_layer_matrix,
    efficiency_record,
)
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.fock import block_dimension, occupation_vectors
from certiqs_key.receiver.grams import (
    GramFamily,
    deficiency_identity,
    port_grams,
    restrict_to_inputs,
)
from certiqs_key.receiver.graph import compile_element_graph, topological_order
from certiqs_key.receiver.numerics import RESIDUAL_NORM, Matrix, PiMultiple, to_float
from certiqs_key.receiver.povm import (
    NoClickFamily,
    element_block,
    multiclick_patterns,
    raw_alphabet,
)
from certiqs_key.receiver.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    CALIBRATION_COVERAGE_STATEMENT,
    NEVER_VERIFIED,
    AssumptionId,
    Refusal,
    RefusalReason,
)
from certiqs_key.receiver.reference import dark_composed_reference
from certiqs_key.receiver.request import (
    Assurance,
    InputRoute,
    ReceiverRequest,
    ValidatedRequest,
    validate_request,
)
from certiqs_key.receiver.residuals import (
    Residual,
    block_positivity_residual,
    check_residuals,
    evaluate_residuals,
    window_consistency_residual,
)
from certiqs_key.receiver.rigorous import EnclosedWeight, rigorous_weights
from certiqs_key.receiver.settings import setting_construction
from certiqs_key.receiver.snapfix import snap_fix_context

__all__ = [
    "EIGENVALUE_ROUTINE",
    "ReceiverEmission",
    "construct_receiver",
    "emitted_residuals",
    "resolve_assurance",
]

#: WHICH EXTREME-EIGENVALUE ROUTINE COMPUTES beta-hat*, named in the A-EIG
#: ledger row. The routine is this module's choice, decided in
#: :func:`certiqs_key.receiver.bound.exact_block_bound` with its reasons; the
#: contract names no algorithm and requires no such record, and the string is
#: carried so that a reader of an artifact can see WHICH ARITHMETIC
#: Assumption ass:eig is being asserted about, at a setting whose weight is
#: evaluated in floating point; a rigorous setting reads no computed eigenvalue
#: (req:rigorous-weight) and invokes no A-EIG.
EIGENVALUE_ROUTINE: Final[str] = (
    "numpy.linalg.eigvalsh (LAPACK divide-and-conquer symmetric eigensolver); "
    "direct, deterministic, no iteration bound and no undeclared threshold"
)


def resolve_assurance(
    requested: Assurance,
) -> tuple[Assurance, RefusalReason | None]:
    """Return the answered tier and the fallback reason -- Theorem thm:exact-and-evaluated (iii).

    ALWAYS ``estimate``, on every route, and the fallback reason is always
    ``None``: that is the whole content of the function, and it is sound
    because "a label withheld is never unsafe" (the proof of Theorem
    ``thm:exact-and-evaluated`` (iii)).

    A REQUEST NAMING ``certified`` CHANGES NOTHING EITHER. The tier is reached
    by the solver's certified evaluation (frank-wolfe/req:certified-
    evaluation), never by the receiver; a rigorous weight is recorded per
    setting (req:rigorous-weight), not as a tier. The fallback
    spelling ``receiver_grams_not_enclosed`` does not exist. The return type keeps the reason slot.
    """  # noqa: E501
    return Assurance.ESTIMATE, None


@dataclass(frozen=True)
class ReceiverEmission:
    """What the module answers a request with: an artifact OR a refusal.

    ``assurance`` is the ANSWERED tier and is ``estimate`` always;
    ``assurance_reason`` is ``None`` on every path. The one value it ever
    carried was the verbatim ``receiver_grams_not_enclosed`` of a ``certified``
    request answered down, and that tier and that spelling do not exist
    (PRINCIPLES.md section 10); the slot stays because the
    answered-tier contract is unchanged and a later rung may need it. Neither
    field is an artifact key -- the outputs table has fifteen and the tier is
    not one of them (see :mod:`certiqs_key.receiver.artifact`).
    """

    artifact: ReceiverMeasurementArtifact | None
    refusal: Refusal | None
    assurance: Assurance
    assurance_reason: RefusalReason | None

    def __post_init__(self) -> None:
        """Check the fail-closed shape: an artifact or a refusal, never both."""
        if (self.artifact is None) == (self.refusal is None):
            raise HypothesisError(
                "an emission carries exactly one of an artifact and a refusal; "
                "the fail_closed convention says a refusal emits NO artifact"
            )
        if self.assurance is not Assurance.ESTIMATE:
            raise HypothesisError(
                "no path in this module can produce a `certified` label "
                "(Theorem thm:exact-and-evaluated (iii))"
            )


def construct_receiver(
    request: ReceiverRequest, *, exact_reference_only: bool = False
) -> ReceiverEmission:
    """Validate, construct, and emit the artifact or a refusal. Never raises.

    ``exact_reference_only`` is ``req:dark-composed-reference`` (vi), for a
    run that declares enclosed references not used
    (``foundations/req:snap-reference`` (i)): the photon-block entry then
    carries its reference only on the blocks enclosed exactly and offers every
    other block as ``none`` with the cause ``enclosure_not_used``. The run
    tier passes it from the run option ``reference_enclosure``; every other
    run, and a caller outside a run, gets the full reference, which the
    instance hands beside its snap (``foundations/def:evaluated-off-snap``
    (i)).
    """
    assurance, reason = resolve_assurance(request.requested_assurance)
    validated = validate_request(request)
    if isinstance(validated, Refusal):
        return _refused(validated, assurance, reason)

    gamma, gamma_inp, family = _canonical_object(validated)

    settings = validated.request.probe_declaration.settings
    channel_dimension = validated.request.input_modes.channel_dimension
    construction = setting_construction(validated.request.input_modes.source_dimension)
    conditioned: dict[str, NoClickFamily] = {
        setting.label: construction.no_click_family(family, setting, channel_dimension)
        for setting in settings
    }

    bounds: list[SettingBound] = []
    for setting in settings:
        data = bound_data_from_family(conditioned[setting.label])
        # Def. def:tolmap (iv) AT THE REQUEST BOUNDARY. It is one of the five
        # threshold decisions the contract states on declared data, so a
        # declaration it does not admit is a REFUSAL naming its check and NOT
        # an exception: the `fail_closed` convention gives a refusal with a
        # machine-readable reason and no artifact (req:tolerance-tests), and
        # this function is documented to never raise.
        inadmissible = check_bound_data_admissible(data, validated.tolerances.eps_2)
        if inadmissible is not None:
            return _refused(inadmissible, assurance, reason)
        # THE EXACT WINDOW, AND ONLY WHERE A DEPTH WAS DECLARED. Def. def:pmc,
        # last paragraph: a declaration carrying no depth at any setting is
        # governed by Eq. eq:pmcdef ALONE -- NO beta* IS FORMED, NO EIGENVALUE
        # OF ANY BLOCK ABOVE THE CUTOFF IS COMPUTED, and Assumption ass:eig is
        # not invoked. `depth is None` is that branch, and it forms nothing.
        depth = validated.request.exact_window.get(setting.label)
        computed = (
            None
            if depth is None
            else exact_window_values(
                conditioned[setting.label], validated.request.photon_cutoff, depth
            )
        )
        bounds.append(
            setting_bound(
                setting.label,
                data,
                validated.request.photon_cutoff,
                validated.predicate_x[setting.label],
                validated.tolerances,
                validated.request.tail_window.get(setting.label),
                depth,
                computed,
            )
        )

    # req:rigorous-weight: every setting's weight formed again from the port
    # Gram enclosures, emitted rounded down; the floating-point weight stays
    # where no enclosure is formed, with the reason.
    rigorous = rigorous_weights(validated)
    bounds = [_rigorous(bound, rigorous[bound.setting]) for bound in bounds]

    channel = _dark_channel(validated)
    photon_blocks = _photon_blocks(
        validated, conditioned, channel, exact_only=exact_reference_only
    )
    residuals = emitted_residuals(
        validated, gamma, gamma_inp, family, conditioned, photon_blocks, bounds
    )
    gaps = _residual_gaps(validated, bounds)
    # req:residual-refusal, at its one site: every residual, then every gap.
    residual_refusal = check_residuals(residuals, gaps)
    if residual_refusal is not None:
        return _refused(residual_refusal, assurance, reason)

    artifact = ReceiverMeasurementArtifact(
        input_mode_space=_input_mode_space(validated),
        outcome_alphabet=_outcome_alphabet(validated),
        port_grams=tuple(zip(family.labels, family.matrices, strict=True)),
        receiver_construction=_receiver_construction(validated),
        photon_blocks=photon_blocks,
        block_dimensions=_block_dimensions(validated),
        efficiency_record=_efficiency_record(validated),
        dark_count_channel=_dark_record(validated, channel),
        high_photon_bounds=_high_photon_bounds(validated, bounds),
        bound_quantifier_domain=_bound_domain(validated, bounds),
        validation_results=ValidationResults(RESIDUAL_NORM, residuals, gaps),
        bound_evaluation=(
            "rigorous"
            if all(bound.evaluation == "rigorous" for bound in bounds)
            else BOUND_EVALUATION
        ),
        assumption_ledger=_assumption_ledger(validated, bounds),
        calibration_coverage=CALIBRATION_COVERAGE_STATEMENT,
        mathematical_spec_version=MATHEMATICAL_SPEC_VERSION,
    )
    return ReceiverEmission(artifact, None, assurance, reason)


def _rigorous(bound: SettingBound, evaluated: EnclosedWeight | str) -> SettingBound:
    """Return ``req:rigorous-weight`` (iv)-(vi) at one setting, rounded down."""
    if isinstance(evaluated, str):
        return replace(bound, fallback_reason=evaluated)
    return replace(
        bound,
        weight=float_down(evaluated.weight),
        evaluation="rigorous",
        enclosed=evaluated.as_record(),
        floating_point_weight=bound.weight,
    )


def _refused(
    refusal: Refusal, assurance: Assurance, reason: RefusalReason | None
) -> ReceiverEmission:
    """Return a refusal record with no artifact."""
    return ReceiverEmission(None, refusal, assurance, reason)


def _canonical_object(
    validated: ValidatedRequest,
) -> tuple[Matrix | None, Matrix | None, GramFamily]:
    """Return ``(Gamma_Inp, {eta_k A_k})`` -- where the input routes converge.

    Returns ``(Gamma, Gamma_Inp, {eta_k A_k})``. ``Gamma`` is the FULL compiled
    instrument matrix ``D_eta Gamma_G`` of Definition ``def:compile``, on
    ``C^M``, which is the object Eq. ``eq:res1`` writes ``r_1`` on;
    ``Gamma_Inp`` is its restriction to the declared input columns, which is
    what Theorem ``thm:port-grams`` (iv) says the pullback depends on and what
    Eq. ``eq:res3`` is written in (``interface.yaml``
    ``input_routes.convergence``). Both are ``None`` on route (i), where Theorem
    ``thm:exact-and-evaluated`` (iv) says "there is no compilation": ``r_1`` and
    ``r_3`` are statements ABOUT ``Gamma`` and have nothing to be evaluated on.
    """
    request = validated.request
    port_rows = [modes for _, modes in request.port_map.entries]
    efficiencies = [port.efficiency for port in request.detector_layer]

    if validated.route is InputRoute.PORT_GRAMS:
        declared = request.port_grams
        assert declared is not None
        return None, None, apply_uniform_efficiency(declared, efficiencies)

    if validated.route is InputRoute.INSTRUMENT_MATRIX:
        supplied = request.instrument_matrix
        assert supplied is not None
        base = supplied
    else:
        graph = request.element_graph
        assert graph is not None
        base = compile_element_graph(graph, len(request.mode_space))

    layer = detector_layer_matrix(port_rows, efficiencies, len(request.mode_space))
    gamma = np.asarray(layer @ base, dtype=np.complex128)
    gamma_inp = restrict_to_inputs(gamma, request.input_modes.subsystem_order())
    return (
        gamma,
        gamma_inp,
        GramFamily(request.port_map.labels, port_grams(gamma_inp, port_rows)),
    )


def emitted_residuals(
    validated: ValidatedRequest,
    gamma: Matrix | None,
    gamma_inp: Matrix | None,
    family: GramFamily,
    conditioned: Mapping[str, NoClickFamily],
    photon_blocks: Sequence[EmittedBlocks],
    bounds: Sequence[SettingBound],
) -> tuple[Residual, ...]:
    """Return every residual the artifact carries -- Definition def:residuals.

    Requirement ``req:residual-emission``, whole: the residuals that exist on
    the input route taken and for the evaluation requested, and no other.
    Their tolerances arrive in ``validated.tolerances``, which
    :func:`~certiqs_key.receiver.numerics.tolerances_from_declaration` built:
    ``eps_1`` and ``eps_3`` are declared on every route, route (i) included,
    where they are unused, and ``eps_6`` exactly where an exact-window depth
    is declared. The second half is asserted here as well, so that no ``r_6``
    row can be formed without its declared tolerance.

    ``r_1`` IS EVALUATED ON THE FULL ``Gamma``, as Eq. ``eq:res1`` writes it --
    ``r_1 = ||(Gamma^dagger Gamma - 1)_+||``, with no restriction to the
    declared input columns. The restricted value is a principal submatrix of
    the same defect and is therefore a LOWER BOUND on it, so a compiled
    ``Gamma`` overshooting contraction only in a column outside ``Inp`` would
    report a passing ``r_1`` where the contract's fails. ``r_3`` is written on
    ``Gamma_Inp`` by Eq. ``eq:res3`` itself and stays there.

    **BOTH ARE ABSENT ON ROUTE (i), AND ABSENT MEANS ABSENT.** ``gamma`` and
    ``gamma_inp`` are ``None`` there, so no ``r_1`` or ``r_3`` row is appended
    and the emitted ``validation_results`` carries no key for either --
    absent, not zero, because emitting 0 would report a check that was not
    made (Requirement ``req:residual-emission``).

    ``r_4`` is emitted "for each emitted ``n``" and, with a probe declared, once
    per declared setting, because a setting family carries a different POVM at
    each ``t`` (Definition ``def:setting-family`` (a)).

    ``r_5`` IS EVALUATED ONCE, ON THE EMITTED BLOCKS THEMSELVES, and is a single
    row: Eq. ``eq:res5`` is a maximum over every emitted outcome letter ``v``,
    every photon number ``0 <= n <= N``, and every setting ``t`` of the setting
    family at once (Definition ``def:residuals``). It is passed the BARE
    coarse-grained blocks of ``photon_blocks``, before any dark-count
    channel (req:residual-emission), rather than recomputing them, so that
    the residual is a statement about exactly what is emitted and cannot
    drift from it.

    ``r_6`` IS REQUEST-DEPENDENT, NOT ROUTE-DEPENDENT, AND IS APPENDED ONLY
    WHERE A DEPTH WAS DECLARED. Eq. ``eq:res6`` is a maximum over every setting
    carrying a depth and every index ``N < n <= m*_t`` that depth names, so it
    too is a single row, and it is computed from the ``ExactWindowRecord`` the
    emitted values were read from rather than from a second evaluation. Where
    no setting carries a depth, no row is appended and the emitted
    ``validation_results`` carries NO KEY for it -- absent, not zero, by the
    same rule and for the same reason as ``r_1`` and ``r_3`` on route (i)
    (Requirement ``req:residual-emission``).
    """
    request = validated.request
    if request.declares_exact_window() and validated.tolerances.eps_6 is None:
        raise HypothesisError(
            "an exact-window depth is declared and no eps_6 reached the "
            "residual emission; req:residual-emission requires it exactly "
            "there, and tolerances_from_declaration refuses its absence"
        )
    cutoff = request.photon_cutoff
    deficiency = None
    if gamma_inp is not None:
        unmonitored = request.port_map.unmonitored(len(request.mode_space))
        deficiency = deficiency_identity(gamma_inp, family, unmonitored)

    residuals: list[Residual] = []
    first = True
    for setting in request.probe_declaration.settings:
        block = evaluate_residuals(
            validated.tolerances,
            family,
            conditioned[setting.label],
            cutoff,
            gamma=gamma if first else None,
            deficiency=deficiency if first else None,
        )
        for residual in block:
            if residual.residual_id == "r_4":
                residuals.append(
                    Residual(
                        residual.residual_id,
                        residual.value,
                        residual.tolerance,
                        residual.norm,
                        residual.photons,
                        setting.label,
                    )
                )
            elif first:
                residuals.append(residual)
        first = False
    residuals.append(
        block_positivity_residual(
            [
                dict(letters)
                for emitted in photon_blocks
                for _, letters in emitted.blocks
            ],
            validated.tolerances,
        )
    )
    defects = [
        defect
        for record in bounds
        if record.exact_window is not None
        for defect in record.exact_window.window_consistency_defects()
    ]
    if any(record.exact_window is not None for record in bounds):
        residuals.append(window_consistency_residual(defects, validated.tolerances))
    return tuple(residuals)


def _residual_gaps(
    validated: ValidatedRequest, bounds: Sequence[SettingBound]
) -> tuple[ResidualGap, ...]:
    """Return the achieved gap at each setting that declares a window.

    ``interface.yaml`` ``outputs.validation_results``, and Lemma
    ``lem:windowtail`` (ii) for why it is a finite real. A setting that took
    branch 1 has no window in use and contributes no row -- Requirement
    ``req:window-declaration``: a window supplied at a setting whose flag is
    exact is UNUSED, not an error.
    """
    rows: list[ResidualGap] = []
    for record in bounds:
        if record.residual_gap is None or record.window is None:
            continue
        rows.append(
            ResidualGap(
                setting=record.setting,
                window=record.window,
                gap=record.residual_gap,
                tolerance=validated.tolerances.eps_gap,
            )
        )
    return tuple(rows)


def _dark_channel(validated: ValidatedRequest) -> DarkCountChannel:
    """Return the emitted ``R``: the declared one, or Eq. eq:darkR's form."""
    declared = validated.request.dark_count_channel
    if declared is not None:
        return declared
    probabilities = [
        port.dark_count_probability for port in validated.request.detector_layer
    ]
    return product_form(probabilities, DarkCountRoute.PER_PORT_PRODUCT_FORM)


def _pattern_labels(
    validated: ValidatedRequest, pattern: frozenset[int]
) -> tuple[str, ...]:
    """Return a click pattern as a sorted tuple of declared PORT LABELS."""
    labels = validated.request.port_map.labels
    return tuple(labels[index] for index in sorted(pattern))


def _input_mode_space(validated: ValidatedRequest) -> InputModeSpace:
    """Return the ``input_mode_space`` key -- both orders, and the split."""
    space = validated.request.mode_space
    inputs = validated.request.input_modes
    labels = space.labels
    return InputModeSpace(
        mode_labels=labels,
        input_labels=tuple(labels[index] for index in inputs.subsystem_order()),
        channel_labels=tuple(labels[index] for index in inputs.channel),
        source_labels=tuple(labels[index] for index in inputs.source),
    )


def _outcome_alphabet(validated: ValidatedRequest) -> OutcomeAlphabet:
    """Return the ``outcome_alphabet`` key -- stable IDs, labels as metadata."""
    coarse = validated.request.outcome_coarse_graining
    return OutcomeAlphabet(
        letters=tuple(
            (coarse.identifier(letter), letter) for letter in coarse.alphabet
        ),
        fibres=tuple(
            (
                letter,
                tuple(
                    _pattern_labels(validated, pattern)
                    for pattern in coarse.fibre(letter)
                ),
            )
            for letter in coarse.alphabet
        ),
    )


def _component_parameters(component: object) -> tuple[tuple[str, object], ...]:
    """Return every declared parameter of an element, by its declared name.

    ``interface.yaml`` ``outputs.receiver_construction`` asks for the declared
    element graph WITH EVERY PARAMETER, so the record is derived from the
    element's own fields rather than from a hand-written list that could fall
    behind one.

    EVERY FIELD SHAPE THE CATALOGUE CAN PRESENT IS SERIALIZED EXPLICITLY, and
    ``None`` among them. Deriving the record from the fields is what keeps it
    complete, but it also means this function meets whatever an entry declares,
    so an unhandled shape would turn a VALIDATED request into a raise inside
    the emission pass -- neither a refusal nor an artifact, which is exactly
    what :func:`construct_receiver` promises cannot happen. Entry C10 is the
    one the contract calls out -- it makes route (ii) a SPECIAL CASE of route
    (iii) (Remark ``rem:entry-roles``) -- and it is covered by a test that
    drives a single generic block through the whole pass.
    """
    rows: list[tuple[str, object]] = []
    for entry in fields(component):  # type: ignore[arg-type]
        if entry.name == "tolerances":
            continue
        value = getattr(component, entry.name)
        if isinstance(value, np.ndarray):
            rows.append(
                (
                    entry.name,
                    [
                        [[float(cell.real), float(cell.imag)] for cell in row]
                        for row in value
                    ],
                )
            )
        elif isinstance(value, tuple | list):
            rows.append((entry.name, [_scalar(item) for item in value]))
        elif isinstance(value, bool) or value is None:
            rows.append((entry.name, value))
        else:
            rows.append((entry.name, _scalar(value)))
    return tuple(rows)


def _scalar(value: object) -> object:
    """Return a declared parameter as a payload scalar, converted once.

    ``None`` is carried through as ``None`` rather than converted: an absent
    optional field is a declared absence and the payload says so, which is the
    only reading that neither invents a value nor raises inside the emission
    pass.
    """
    if value is None:
        return None
    if isinstance(value, bool | str | int):
        return value
    if isinstance(value, PiMultiple):
        # Presentation (b) of `interface.yaml` `parameters.units`: the
        # coefficient is the declared datum and what the artifact carries.
        return {"pi_coefficient": str(value.coefficient)}
    return to_float(value)  # type: ignore[arg-type]


def _receiver_construction(validated: ValidatedRequest) -> ReceiverConstruction | None:
    """Return ``receiver_construction``, present exactly on route (iii).

    ``interface.yaml`` ``outputs.receiver_construction.presence_rule`` states
    both halves of the rule, and this is the only key that carries the port
    map or the probe declaration.
    """
    if validated.route is not InputRoute.ELEMENT_GRAPH:
        return None
    request = validated.request
    graph = request.element_graph
    assert graph is not None
    labels = request.mode_space.labels
    return ReceiverConstruction(
        elements=tuple(
            (
                element.name,
                element.component.entry_id,
                tuple(labels[index] for index in element.support),
                _component_parameters(element.component),
            )
            for element in graph.elements
        ),
        edges=graph.edges,
        port_map=tuple(
            (label, tuple(labels[index] for index in modes))
            for label, modes in request.port_map.entries
        ),
        probe_declaration=tuple(
            (setting.label, setting.diagonal())
            for setting in request.probe_declaration.settings
        ),
    )


def _photon_blocks(
    validated: ValidatedRequest,
    conditioned: dict[str, NoClickFamily],
    channel: DarkCountChannel,
    *,
    exact_only: bool = False,
) -> tuple[EmittedBlocks, ...]:
    """Return the emitted low-photon blocks, keyed by declared probe setting.

    Per setting: the bare coarse-grained blocks; the dark-composed blocks of
    Requirement ``req:dark-composed-reference`` (i), in binary64, by
    Thm. ``thm:dark-counts`` (ii) (:func:`~certiqs_key.receiver.dark.compose_blocks`)
    and the fibre sums of Eq. ``eq:dark-composed``; and the reference of items
    (ii)-(iv) (:func:`~certiqs_key.receiver.reference.dark_composed_reference`),
    computed in exact rational arithmetic and never from the binary64 blocks.
    """
    coarse = validated.request.outcome_coarse_graining
    cutoff = validated.request.photon_cutoff
    references = {
        reference.setting: reference
        for reference in dark_composed_reference(
            validated, channel, exact_only=exact_only
        )
    }
    families: list[EmittedBlocks] = []
    for setting in validated.request.probe_declaration.settings:
        family = conditioned[setting.label]
        blocks = tuple(
            (
                photons,
                tuple(
                    (letter, block)
                    for letter, block in coarse_blocks(family, coarse, photons).items()
                ),
            )
            for photons in range(cutoff + 1)
        )
        composed = tuple(
            (photons, _dark_composed_letters(family, coarse, channel, photons))
            for photons in range(cutoff + 1)
        )
        reference = references[setting.label]
        families.append(
            EmittedBlocks(
                setting.label,
                blocks,
                composed,
                reference,
                snap_fix_context(validated, channel, reference),
            )
        )
    return tuple(families)


def _dark_composed_letters(
    family: NoClickFamily,
    coarse: CoarseGraining,
    channel: DarkCountChannel,
    photons: int,
) -> tuple[tuple[str, Matrix], ...]:
    """Return ``blk Ftilde_v^{(=n)}`` per letter, in binary64.

    Implements Eq. ``eq:dark-composed`` of
    ``detector-imperfections/def:dark-composed`` as Requirement
    ``req:dark-composed-reference`` (i) states it, for the emitted ``R``:
    ``Mtilde_S = sum_{S'} R_{S|S'} M_{S'}`` (Thm. ``thm:dark-counts`` (ii)), then
    the sum over the fibre of ``v``.
    """
    raw = {
        pattern: element_block(family, pattern, photons)
        for pattern in raw_alphabet(family.port_count)
    }
    composed = compose_blocks(channel, raw)
    size = family.block_dimension(photons)
    letters: list[tuple[str, Matrix]] = []
    for letter in coarse.alphabet:
        total = np.zeros((size, size), dtype=np.complex128)
        for pattern in coarse.fibre(letter):
            total = total + composed[pattern]
        letters.append((letter, np.asarray(total, dtype=np.complex128)))
    return tuple(letters)


def _block_dimensions(validated: ValidatedRequest) -> tuple[BlockDimension, ...]:
    """Return the expected channel-block dimensions and the basis order."""
    channel = validated.request.input_modes.channel_dimension
    return tuple(
        BlockDimension(
            photons=photons,
            dimension=block_dimension(channel, photons),
            occupation_vectors=occupation_vectors(channel, photons),
        )
        for photons in range(validated.request.photon_cutoff + 1)
    )


def _efficiency_record(validated: ValidatedRequest) -> EfficiencyRecord:
    """Return the efficiency record: req:efficiency-record and req:normalization-record.

    Off route (iii) there is no declared chain, so the only declared loss
    parameters are the per-port ``eta_k`` of layer L1 -- which is what
    Requirement ``req:efficiency-convention`` says the record is FOR: whether
    the declared Grams came from power data or from click data "is a declared
    field" (Remark ``rem:powervsclick`` says why it is not inferable from the
    numbers).

    THE ROWS ARE THE DECLARATION'S. They are read off the DECLARED request, so
    each detector row carries the efficiency as declared even where the
    receiver was compiled at its normalized station; the normalization
    (``detector-imperfections/req:normalization-record``) carries the factored
    loss and every declared efficiency beside the exact ``eta_k / t``
    compiled, and says whether and why it was applied.
    """
    request = validated.declared
    chain: list[tuple[str, str, tuple[tuple[float, str], ...]]] = []
    if request.element_graph is not None:
        order = compile_order(validated)
        for name in order:
            element = request.element_graph.element(name)
            chain.append(
                (name, element.component.entry_id, element.component.loss_parameters())
            )
    detector = tuple(
        (port.label, to_float(port.efficiency)) for port in request.detector_layer
    )
    return EfficiencyRecord(
        rows=efficiency_record(tuple(chain), detector),
        normalization=validated.normalization,
    )


def compile_order(validated: ValidatedRequest) -> tuple[str, ...]:
    """Return the compiled order of the declared elements.

    Theorem ``thm:compilation-well-defined`` (i): every linear extension of a
    well-formed graph compiles to the same matrix, so any one of them is THE compiled
    order and the position it gives an element is well defined -- which is what makes
    ``site`` in the composition record meaningful. The one Theorem
    ``thm:compilation-well-defined``
    (iv) names is a topological sort, and that is the one taken here.
    """
    graph = validated.request.element_graph
    assert graph is not None
    order = topological_order(graph)
    if order is None:  # pragma: no cover - (E2) refused before this is reached
        raise HypothesisError("the declared graph admits no linear extension")
    return order


def _dark_record(
    validated: ValidatedRequest, channel: DarkCountChannel
) -> DarkCountRecord:
    """Return the emitted ``R`` with its THREE scalars and what was checked.

    ``interface.yaml`` ``outputs.dark_count_channel``: the matrix, the route,
    which admissibility conditions were checked, and ``r_min``, ``rbar``,
    ``delta_dc`` under distinct names (Requirement ``req:dark-channel-record``).

    ``r_min`` IS EMITTED AS Eq. ``eq:rmin`` COMPUTES IT and is never modified --
    it may exceed 1 or be negative, and both are signals a reader is entitled to
    see. ``rbar`` is Eq. ``eq:rbar`` beside it, a coefficient. ``delta_dc`` is
    Eq. ``eq:darkdelta`` and follows THE ROUTE: 0 where the channel is the
    product form, because there (D1) and (D2) are theorems and there is no slack
    to carry, and ``eps_4 + (K + 1) eps_2`` where it was declared and tested.
    """
    derived: tuple[str, ...]
    checked: tuple[str, ...]
    if channel.route is DarkCountRoute.PER_PORT_PRODUCT_FORM:
        derived, checked = ("D1", "D2"), ()
    else:
        derived, checked = (), ("D1", "D2")
    minimum = minimum_multiclick_mass(channel)
    columns = tuple(
        (
            _pattern_labels(validated, column),
            tuple(
                (_pattern_labels(validated, row), value)
                for row, value in sorted(
                    channel.columns.get(column, {}).items(),
                    key=lambda item: sorted(item[0]),
                )
            ),
        )
        for column in channel.patterns()
    )
    return DarkCountRecord(
        route=channel.route,
        columns=columns,
        r_min=minimum,
        r_bar=capped_coefficient(minimum),
        delta_dc=composition_correction(
            channel.route, channel.port_count, validated.tolerances
        ),
        conditions_derived=derived,
        conditions_checked=checked,
    )


def _high_photon_bounds(
    validated: ValidatedRequest, bounds: Sequence[SettingBound]
) -> HighPhotonBounds:
    """Return the strengthening slot: its single entry ``(MC_K, (p_mc^(t))_t)``.

    Definition ``def:slot``: one weight per setting, each guaranteed at its own
    setting (Theorem ``thm:emitted-bound``, Eq. ``eq:pmcsetting``), and the entry's
    uniform weight ``p_mc``, their minimum (Eq. ``eq:pmcstatement``); at a
    probe-free receiver the entry is ``(MC_K, p_mc)``.
    """
    ports = validated.request.port_map.port_count
    outcome_set = tuple(
        _pattern_labels(validated, pattern) for pattern in multiclick_patterns(ports)
    )
    return HighPhotonBounds(
        entries=(
            SlotEntry(
                outcome_set,
                per_setting=emitted_weights(bounds),
                weight=emitted_weight(bounds),
            ),
        ),
    )


def _bound_domain(
    validated: ValidatedRequest, bounds: Sequence[SettingBound]
) -> BoundQuantifierDomain:
    """Return the literal quantifier statement and the per-setting branch record."""
    return BoundQuantifierDomain(
        statement="for all n > N and all t in T",
        photon_cutoff=validated.request.photon_cutoff,
        probe_alphabet=validated.request.probe_declaration.labels,
        per_setting=tuple(bounds),
    )


def _assumption_ledger(
    validated: ValidatedRequest, bounds: Sequence[SettingBound]
) -> tuple[AssumptionRecord, ...]:
    """Return the ledger with the declared values each assumption constrains.

    ``interface.yaml`` ``outputs.assumption_ledger``. Where a constrained
    parameter is emitted elsewhere under its own key it is not repeated here
    (the wire-form rule of :mod:`certiqs_key.receiver.artifact`); where it is
    not -- the undeclared vacuum modes, the reserved ``tau`` -- this row is
    where it is written down. ``never_verified`` is
    ``True`` for exactly the rows of ``never_verified_set``
    (``req:decidable-assumptions``;
    :data:`~certiqs_key.receiver.reasons.NEVER_VERIFIED`, read from each
    assumption's ``verification`` header field).

    THE A-EIG ROW EXISTS ON EVERY ARTIFACT AND RECORDS WHERE IT WAS INVOKED.
    The outputs table asks for the machine keys of the assumption files, one
    row per file and every row on every artifact; the lead-in of Assumption
    ``ass:eig`` has the assumption named, DECLARED WITH ITS ``eps_eig``, and
    carried in the artifact's assumption ledger BESIDE THE SETTINGS AT WHICH IT
    WAS INVOKED (Requirement ``req:eig-ledger-row``). On a declaration that
    requests no exact window that list is EMPTY and ``eps_eig`` is ``None`` --
    absent, not zero -- which is the honest record of the same lead-in: a
    declaration that requests no exact window does not invoke it, and its
    emitted value does not depend on it.

    THE ROW ALSO NAMES THE ROUTINE, WHICH IS THIS MODULE'S CHOICE AND NOT A
    CONTRACT REQUIREMENT. The contract requires the ledger row and the
    per-setting invocation record (Requirement ``req:eig-ledger-row``;
    ``interface.yaml`` ``outputs.bound_quantifier_domain``) and names no
    routine, so naming the eigenvalue routine here is this module's choice:
    the assumption is about an arithmetic, and an artifact that does not say
    which arithmetic leaves a reader unable to judge the one thing the
    assumption is about. The choice and its reasons are
    :func:`certiqs_key.receiver.bound.exact_block_bound`'s, and NOTHING HERE
    CLAIMS AN ENCLOSURE.

    EVERY ROW IS EMITTED ON EVERY ARTIFACT, and no row is conditional
    (``outputs.assumption_ledger`` ``content``). The conditions this module
    decides on the declared data -- (E2) of Def. ``def:graph`` and the
    occupation-diagonal probe states of Def. ``def:probe`` -- have no row
    (``decided_conditions_note``): they are refused when they fail
    (``req:graph-refusal``, ``req:probe-diagonal-admission``).
    """
    request = validated.request
    declared_inputs = set(request.input_modes.subsystem_order())
    labels = request.mode_space.labels
    # Every reserved tolerance field the declaration carries, on every record
    # that carries parameters (req:reserved-tolerance-field): validation has
    # admitted each only as exactly zero.
    tolerance_fields = [
        f"{name}.{parameter}"
        for name, record in request.parameter_records()
        for parameter in record.tolerances
    ]
    graph = request.element_graph
    constrains: dict[AssumptionId, tuple[tuple[str, object], ...]] = {
        AssumptionId.A_TRUST: (),
        AssumptionId.A_PASSIVE: (
            ()
            if graph is None
            else (
                (
                    "catalogue_entries",
                    sorted({e.component.entry_id for e in graph.elements}),
                ),
            )
        ),
        AssumptionId.A_VAC: (
            (
                "undeclared_input_modes",
                [
                    labels[index]
                    for index in range(len(request.mode_space))
                    if index not in declared_inputs
                ],
            ),
        ),
        AssumptionId.A_MODES: (),
        AssumptionId.A_THRESH: (("tau", request.mode_space.modes[0].tau),),
        AssumptionId.A_PORT: (("ports", list(request.port_map.labels)),),
        AssumptionId.A_EXACT: (("declared_tolerance_fields", tolerance_fields),),
        AssumptionId.A_NOSEL: (),
        AssumptionId.A_ROUND: (),
        AssumptionId.A_EIG: (
            ("eps_eig", validated.tolerances.eps_eig),
            (
                "invoked_at",
                [record.setting for record in bounds if record.assumption_eig_invoked],
            ),
            ("eigenvalue_routine", EIGENVALUE_ROUTINE),
        ),
    }
    return tuple(
        AssumptionRecord(
            assumption_id=identifier,
            machine_key=ASSUMPTION_MACHINE_KEYS[identifier],
            never_verified=identifier in NEVER_VERIFIED,
            constrains=constrains[identifier],
        )
        for identifier in AssumptionId
    )
