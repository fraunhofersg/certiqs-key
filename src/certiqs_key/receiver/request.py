"""The receiver request: the sixteen input machine keys of the inputs table.

One typed record carrying exactly the declared inputs, and one validator that
returns a :class:`~certiqs_key.receiver.reasons.Refusal` or a validated request and
NEVER raises. The ``fail_closed`` convention (``interface.yaml``
``conventions``): "every failed validation produces a refusal with a
machine-readable reason and no artifact".

THE THREE ROUTES ARE MUTUALLY EXCLUSIVE
=======================================
``interface.yaml`` ``input_routes.rule``: EXACTLY ONE of ``port_grams``,
``instrument_matrix`` and ``element_graph`` is present, and A REQUEST CARRYING
TWO IS REFUSED RATHER THAN RESOLVED BY PRECEDENCE. The three converge on the
canonical Gram family (``input_routes.convergence``) BEFORE any photon-number
reasoning begins, and two presentations of it are not guaranteed to agree, so
choosing would be inventing a check the contract does not state.

THE ORDER OF THE CHECKS IS THE ORDER THE CONTRACT MAKES THEM TESTABLE
=====================================================================
The declared tolerances come first, because without them "the ``fail_closed``
convention has no threshold to test" (``inputs.numerical_tolerances``) and no
later check can be evaluated at all. **That ordering carries more weight**:
Definition ``def:tolmap`` makes those numbers the things that DECIDE the other
validations, so a tolerance outside its declared domain ``[0, 1)`` has to refuse
-- with the contract-verbatim ``tolerance_outside_declared_domain`` -- BEFORE it
is used to decide anything. :func:`validate_request` reads the tolerances and
their domain first, and every later check consumes a member of the resulting
:class:`~certiqs_key.receiver.numerics.NumericalTolerances`.

Then the route rule, then the objects each route needs, then the declarations
that depend on them. Everything decidable BEFORE any Gram is computed is decided
here -- in particular the window requirement, which Requirement
``req:window-declaration`` makes "decidable at input validation from declared
data alone": the exact flag it reads is set by the construction of each
setting and read off the declaration (Remark ``rem:flag-instances``), without
computing a Gram, a determinant or an eigenvalue.

A RECEIVER WITH SOURCE MODES NEEDS THE SUBMODULE THAT CONDITIONS ON THEM. Its
setting family is constructed by the probe-conditioning submodule, which is
removable; where it is absent the request is refused with
``probe_conditioning_submodule_absent``, right after the probe declaration
itself is checked (:func:`~certiqs_key.receiver.settings.check_setting_construction`).

THE KEY `exact_window` IS OPT-IN
================================
``interface.yaml`` ``inputs.exact_window`` opens its row: "Opt-in, never
defaulted. Where a depth is present at a setting, the exact-window evaluation
of Def. def:pmcex gives that setting's p_mc^(t); where it is absent, Def.
def:pmc gives it, no block above the cutoff is formed, and the emitted value
is the one Eq. eq:pmcdef defines." So the empty mapping is not a default and is
not a value this module chose: it is the declaration that requests no exact
window anywhere. **No default depth is invented, including the minimal one**
-- the row's ``no_default_note``: the exact window is evaluated only where a
declaration requests it, never by default (Requirement
``req:weight-provenance``), because its cost is the caller's to accept and A
PLATFORM DEFAULT WOULD BE AN UNDECLARED NUMBER (the receiver design.md).

Its two validations are both decidable here, before any Gram exists, and both
are kind (a) or (b) of Definition ``def:tolmap``'s closing enumeration -- a
comparison against a declared domain, or a combinatorial predicate on the
declaration. NO NEW THRESHOLD DECIDES EITHER:

* ``m*_t > N`` always, and ``m*_t <= m_t`` where predicate (X) fails
  (:func:`~certiqs_key.receiver.validation.check_exact_window`);
* ``eps_eig`` and ``eps_6`` present wherever ANY depth is declared
  (:func:`~certiqs_key.receiver.numerics.tolerances_from_declaration`), which runs
  FIRST because those numbers decide the other validations.

THE ASSURANCE TIER IS THE PLATFORM'S VOCABULARY, NOT THIS MODULE'S
=================================================================
``requested_assurance`` is typed with
:class:`certiqs_key.foundations.assurance.Assurance`, and THIS IS THE MODULE OF
:mod:`certiqs_key.receiver` THAT IMPORTS THE TIER VOCABULARY. The platform has
ONE tier vocabulary and one home for it: that module's docstring states the
rule, ``tests/golden/test_fail_closed_against_registry.py`` keeps the tier
literal out of every engine module except its definition, and a second enum here
would be a second vocabulary that could drift from it. Nothing about this
contract changes by using it: Theorem ``thm:exact-and-evaluated`` (iii) still
says that no path in this module produces a label stronger than the
floating-point one, and :func:`certiqs_key.receiver.construct.resolve_assurance`
still answers every request ``estimate``. The tier-fallback string
``receiver_grams_not_enclosed`` is never produced (Requirement
``req:evaluation-label``) and is not a member of
:class:`certiqs_key.receiver.reasons.RefusalReason`, and no
path answers with a reason at all.

THE VALIDATED REQUEST IS THE NORMALIZED STATION
===============================================
Requirement ``detector-imperfections/req:efficiency-normalization``: a request
whose receiver declares no source modes and some efficiency ``eta_k > 0`` is
compiled AT ITS NORMALIZED STATION, the factored loss ``t`` being the declared
``efficiency_normalization`` or else the default, the largest declared
efficiency ``eta_max`` divided by ``99/100`` where ``eta_max < 99/100`` and
``1`` from there on (:func:`~certiqs_key.receiver.efficiency.default_factor`;
``spec/modules/receiver/design.md``, structural decision 14, says why it stops
short of ``eta_max``). The
factor is decided here, on declared data, and a declared one outside
``[eta_max, 1]`` (or a ``t < 1`` where the receiver is compiled at ``t = 1``)
is refused with the contract's ``efficiency_normalization_out_of_range``.
:attr:`ValidatedRequest.request` is then the request of the normalized
station -- the declared one with every detector efficiency replaced by the
EXACT rational ``eta_k / t`` -- so that every object computed downstream (the
Grams, the blocks, the exact window, the reference and its enclosures, the
weights, the dark-composed family) is the normalized station's on every
route, with no second site that could apply the factor or forget it.
:attr:`ValidatedRequest.declared` keeps the declaration as given, which is
what the efficiency record's rows carry (``req:efficiency-record``) beside the
normalization (``req:normalization-record``). At ``t = 1`` the two are one
object, so a request compiled at ``t = 1`` computes exactly what it did before
the normalization existed.

WHAT IS NOT VALIDATED HERE
==========================
The residuals of Definition ``def:residuals`` are statements about the
COMPUTED objects, so they are evaluated after construction
(:mod:`certiqs_key.receiver.construct`); a residual above its declared tolerance is
a refusal there, and for ``r_5`` the reason is the contract's own
``photon_block_positivity_residual_above_tolerance``. And the assumptions
the engine never verifies -- every one whose ``verification`` header field is
``never`` (spec/claim-format.md section 3.2), the ``never_verified_set`` of
``req:decidable-assumptions`` and Remark ``rem:unchecked-assumptions`` -- are
decided here in their clauses on the declared data and in nothing they say of
the physical receiver or the run.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from fractions import Fraction
from typing import ClassVar

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.receiver.catalogue import Component
from certiqs_key.receiver.coarse import CoarseGraining, check_coarse_graining
from certiqs_key.receiver.dark import (
    DarkCountChannel,
    check_dark_channel,
    check_dark_count_source,
)
from certiqs_key.receiver.efficiency import (
    EfficiencyNormalization,
    normalize_efficiencies,
)
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.grams import (
    GramFamily,
    check_gram_family_admissible,
    check_rank_against_port_sizes,
)
from certiqs_key.receiver.graph import ElementGraph, check_element_graph
from certiqs_key.receiver.modes import (
    InputModes,
    ModeSpace,
    PortMap,
    check_input_modes,
    check_mode_space,
    check_port_map,
)
from certiqs_key.receiver.numerics import (
    Matrix,
    NumericalTolerances,
    Scalar,
    lambda_max,
    to_float,
    tolerances_from_declaration,
)
from certiqs_key.receiver.reasons import Refusal, RefusalReason
from certiqs_key.receiver.settings import (
    ProbeDeclaration,
    check_probe_declaration,
    check_setting_construction,
    predicate_x_holds,
)
from certiqs_key.receiver.validation import (
    ParameterRecord,
    check_exact_window,
    check_exactly_one_route,
    check_parameter_tolerances,
    check_photon_cutoff,
    check_tail_window,
)

__all__ = [
    "Assurance",
    "DetectorPort",
    "InputRoute",
    "ReceiverRequest",
    "ValidatedRequest",
    "factored_loss",
    "normalized_station",
    "validate_request",
]


class InputRoute(StrEnum):
    """Which of the three mutually exclusive routes a request took."""

    #: A supplied admissible Gram family. Theorem thm:exact-and-evaluated (iv): "there
    #: is no compilation", so residuals r_1 and r_3 have nothing to evaluate on.
    PORT_GRAMS = "port_grams"
    #: A supplied instrument matrix, mapped to the Grams by Eq. eq:gramdef.
    INSTRUMENT_MATRIX = "instrument_matrix"
    #: A declared component graph, compiled by Theorem thm:compilation-well-defined.
    ELEMENT_GRAPH = "element_graph"


@dataclass(frozen=True)
class DetectorPort:
    """One row of the ``detector_layer`` input -- layer L1 (Remark ``rem:layers``).

    ``efficiency`` is ``eta_k`` and ``dark_count_probability`` is ``p_dc|k``,
    both in ``[0, 1]`` and both REQUIRED: the ``detector_layer`` input row
    carries ``p_dc|k`` for every port unconditionally, so a row that omits it
    declares no dark-count probability at all, and the ``fail_closed``
    convention forbids substituting one (a silent ``0`` would declare a
    noiseless detector).

    The efficiency enters as the terminal factor ``D_eta`` of Definition
    ``def:compile``; the dark counts "never enter ``Gamma`` at all and act on
    the outcome label" (Remark ``rem:layers``; Theorem ``thm:dark-counts``).
    """

    label: str
    efficiency: Scalar
    dark_count_probability: Scalar
    #: The reserved optional ``tolerance`` field of every declared parameter
    #: (Requirement ``req:reserved-tolerance-field``; Assumption ``ass:exact``),
    #: keyed by parameter name, as :class:`~certiqs_key.receiver.catalogue.Component`
    #: carries it. Absent or exactly zero is admitted and anything else is
    #: refused by :func:`certiqs_key.receiver.validation.check_parameter_tolerances`.
    #: Excluded from the hash, so that the record stays hashable.
    tolerances: Mapping[str, Scalar] = field(
        default_factory=dict, kw_only=True, hash=False
    )
    #: How a refusal names this record (``check_parameter_tolerances``).
    record_kind: ClassVar[str] = "detector-layer row"


@dataclass(frozen=True)
class ReceiverRequest:
    """The sixteen input machine keys of the inputs table (``interface.yaml``).

    ``port_grams``, ``instrument_matrix`` and ``element_graph`` are the three
    MUTUALLY EXCLUSIVE routes; exactly one is present.

    ``efficiency_normalization`` is optional, and ``None`` is the declaration
    that leaves the factored loss to its default, ``eta_max / (99/100)`` for
    a largest declared efficiency ``eta_max < 99/100`` and ``1`` from there on
    (``detector-imperfections/req:efficiency-normalization``); declaring ``1``
    turns the normalization off.

    ``exact_window`` is the one key the inputs table marks OPTIONAL, per
    setting (``optional: true``, ``per_setting: true``), and the empty mapping
    is the declaration that requests no exact window anywhere. It is the same
    shape ``tail_window`` already has and for the same reason -- a per-setting
    integer that some settings carry and others do not.
    """

    mode_space: ModeSpace
    input_modes: InputModes
    port_map: PortMap
    detector_layer: tuple[DetectorPort, ...]
    probe_declaration: ProbeDeclaration
    photon_cutoff: int
    numerical_tolerances: Mapping[str, Scalar]
    outcome_coarse_graining: CoarseGraining
    requested_assurance: Assurance
    port_grams: GramFamily | None = None
    instrument_matrix: Matrix | None = None
    element_graph: ElementGraph | None = None
    dark_count_channel: DarkCountChannel | None = None
    tail_window: Mapping[str, int] = field(default_factory=dict)
    #: The inputs table `exact_window`: {m*_t}, one integer per setting,
    #: OPTIONAL. The empty mapping is no depth declared anywhere, which
    #: Eq. eq:pmcdef governs alone, expression for expression (Def. def:pmc,
    #: last paragraph; Thm. thm:exact-and-evaluated (v)).
    exact_window: Mapping[str, int] = field(default_factory=dict)
    #: The inputs table `efficiency_normalization`: the factored loss t of
    #: detector-imperfections/def:normalized-station, OPTIONAL. ``None`` compiles
    #: a probe-free receiver at t = eta_max / (99/100) where eta_max < 99/100
    #: and at t = 1 from there on; a declared t must lie in [eta_max, 1], and 1
    #: turns the normalization off (req:efficiency-normalization).
    efficiency_normalization: Scalar | None = None

    def declares_exact_window(self) -> bool:
        """Return whether ANY setting's declaration carries a depth.

        The predicate Requirement ``req:exact-window-declaration`` scopes the
        two conditional tolerances to: declaring a depth AT ANY SETTING requires
        ``eps_eig`` and ``eps_6``. It is a property of the declaration, decided
        by finite inspection, and it is deliberately read off the mapping being
        non-empty rather than off the declared settings -- a depth keyed to a
        setting the probe declaration does not carry still makes the tolerances
        required, which is the fail-closed direction.
        """
        return bool(self.exact_window)

    def route(self) -> InputRoute | None:
        """Return the single route this request took, or ``None`` if not one."""
        present = [
            route
            for route, supplied in (
                (InputRoute.PORT_GRAMS, self.port_grams is not None),
                (InputRoute.INSTRUMENT_MATRIX, self.instrument_matrix is not None),
                (InputRoute.ELEMENT_GRAPH, self.element_graph is not None),
            )
            if supplied
        ]
        return present[0] if len(present) == 1 else None

    def elements(self) -> tuple[tuple[str, Component], ...]:
        """Return the declared elements, named; empty off route (iii)."""
        if self.element_graph is None:
            return ()
        return tuple(
            (element.name, element.component) for element in self.element_graph.elements
        )

    def parameter_records(self) -> tuple[tuple[str, ParameterRecord], ...]:
        """Return every declared record that carries parameters, named.

        Requirement ``req:reserved-tolerance-field`` validates the reserved
        ``tolerance`` field of EVERY declared parameter, and Assumption
        ``ass:exact`` says which those are: every declared component
        parameter, efficiency, dark-count probability and probe mean photon
        number. So the records are the elements of route (iii), under their
        declared names; each detector-layer row, as
        ``detector_layer.<port>``, carrying the efficiency and the dark-count
        probability; and each probe setting, as ``probe_declaration.<t>``,
        carrying the mean photon numbers.
        """
        return (
            *self.elements(),
            *((f"detector_layer.{port.label}", port) for port in self.detector_layer),
            *(
                (f"probe_declaration.{setting.label}", setting)
                for setting in self.probe_declaration.settings
            ),
        )


@dataclass(frozen=True)
class ValidatedRequest:
    """A request every decidable clause of the inputs table has been read against.

    Carries the resolved tolerances and the per-setting predicate (X), both of
    which the construction pass consumes and neither of which it may recompute
    differently: (X) is a property of the DECLARATION (Remark
    ``rem:flag-instances``) and is decided once, here.
    """

    #: The request the construction compiles: the NORMALIZED STATION's, every
    #: detector efficiency the exact rational eta_k / t
    #: (detector-imperfections/req:efficiency-normalization). The declared
    #: request itself where t = 1.
    request: ReceiverRequest
    route: InputRoute
    tolerances: NumericalTolerances
    predicate_x: Mapping[str, bool]
    #: The factored loss and every declared efficiency beside the compiled one
    #: (req:normalization-record), decided once, here.
    normalization: EfficiencyNormalization
    #: The request as declared. The efficiency record's rows read it
    #: (req:efficiency-record keeps the declared loss parameters).
    declared: ReceiverRequest


def factored_loss(request: ReceiverRequest) -> Fraction:
    """Return the factored loss ``t`` a request is compiled at.

    The one function a consumer outside this module reads ``t`` from when it
    holds the request rather than the emitted artifact -- an honest model,
    which must apply ``Lambda^loss_t`` before it evaluates the emitted
    measurement (``detector-imperfections/req:loss-before-evaluation``). It is
    the same decision :func:`validate_request` makes, so the two cannot
    disagree.

    Raises:
        HypothesisError: if the declared factor would be refused; a caller that
            needs the refusal record calls :func:`validate_request`.
    """
    normalization = _normalization(request)
    if isinstance(normalization, str):
        raise HypothesisError(normalization)
    return normalization.factored_loss


def _normalization(request: ReceiverRequest) -> EfficiencyNormalization | str:
    """Return the request's normalization, or the refusal's detail."""
    return normalize_efficiencies(
        [(port.label, port.efficiency) for port in request.detector_layer],
        declared_factor=request.efficiency_normalization,
        source_modes_declared=request.input_modes.has_probe,
    )


def _check_efficiency_normalization(
    request: ReceiverRequest,
) -> EfficiencyNormalization | Refusal:
    """Return the normalization, or refuse ``efficiency_normalization_out_of_range``.

    Requirement ``detector-imperfections/req:efficiency-normalization``,
    decided on declared data and exactly: a declared ``t`` outside
    ``[eta_max, 1]`` is refused, and so is a declared ``t < 1`` in a request
    with source modes or with every efficiency zero.
    """
    normalization = _normalization(request)
    if isinstance(normalization, str):
        return Refusal(
            RefusalReason.EFFICIENCY_NORMALIZATION_OUT_OF_RANGE, normalization
        )
    return normalization


def normalized_station(
    request: ReceiverRequest, normalization: EfficiencyNormalization
) -> ReceiverRequest:
    """Return the request of the normalized station -- def:normalized-station.

    Requirement ``detector-imperfections/req:efficiency-normalization``: the
    station compiled is the one at the EXACT rational efficiencies
    ``eta_k / t`` on every route; they replace the declared efficiencies of
    layer L1 as :class:`~fractions.Fraction` values, so that the exact
    statements, the reference and the enclosures are formed from them and the
    floating-point evaluation evaluates them as it evaluates every declared
    number (the evaluation model), and no value rounded from ``eta_k / t`` is
    declared in their place. Every other field is the declaration's. At
    ``t = 1`` the declared request itself is returned.
    """
    if not normalization.below_one:
        return request
    compiled = {port.label: port.compiled for port in normalization.ports}
    return replace(
        request,
        detector_layer=tuple(
            replace(port, efficiency=compiled[port.label])
            for port in request.detector_layer
        ),
    )


def validate_request(request: ReceiverRequest) -> ValidatedRequest | Refusal:
    """Return the validated request, or the first refusal, and never raise."""
    tolerances = tolerances_from_declaration(
        request.numerical_tolerances, request.declares_exact_window()
    )
    if isinstance(tolerances, Refusal):
        return tolerances

    route_refusal = check_exactly_one_route(
        {
            "port_grams": request.port_grams is not None,
            "instrument_matrix": request.instrument_matrix is not None,
            "element_graph": request.element_graph is not None,
        }
    )
    if route_refusal is not None:
        return route_refusal
    route = request.route()
    if route is None:  # pragma: no cover - the check above already refused
        return Refusal(
            RefusalReason.INPUT_ROUTES_NOT_EXACTLY_ONE,
            "exactly one input route must be present",
        )

    for refusal in (
        check_mode_space(request.mode_space),
        check_input_modes(request.mode_space, request.input_modes),
        check_port_map(request.mode_space, request.port_map),
        check_photon_cutoff(request.photon_cutoff),
        check_parameter_tolerances(request.parameter_records()),
        _check_detector_layer(request),
        _check_route_source(request, route, tolerances),
        check_probe_declaration(
            request.probe_declaration, request.input_modes.source_dimension
        ),
        check_setting_construction(request.input_modes.source_dimension),
    ):
        if refusal is not None:
            return refusal

    predicate_x = {
        setting.label: predicate_x_holds(
            request.probe_declaration,
            setting.label,
            request.input_modes.source_dimension,
        )
        for setting in request.probe_declaration.settings
    }
    for refusal in (
        check_tail_window(
            request.photon_cutoff,
            request.probe_declaration.labels,
            predicate_x,
            request.tail_window,
        ),
        check_exact_window(
            request.photon_cutoff,
            request.probe_declaration.labels,
            predicate_x,
            request.tail_window,
            request.exact_window,
        ),
        _check_dark_counts(request, tolerances),
        check_coarse_graining(request.outcome_coarse_graining),
        _check_alphabet_width(request),
    ):
        if refusal is not None:
            return refusal

    # detector-imperfections/req:efficiency-normalization: the factor is
    # decided last among the declared-data checks, after layer L1 is known to
    # carry one efficiency in [0, 1] per declared port, and the request every
    # later step compiles is the normalized station's.
    normalization = _check_efficiency_normalization(request)
    if isinstance(normalization, Refusal):
        return normalization
    return ValidatedRequest(
        normalized_station(request, normalization),
        route,
        tolerances,
        predicate_x,
        normalization,
        request,
    )


def _check_alphabet_width(request: ReceiverRequest) -> Refusal | None:
    """Return a refusal if ``cg`` is not declared on this receiver's ``2^[K]``."""
    declared = request.outcome_coarse_graining.port_count
    ports = request.port_map.port_count
    if declared != ports:
        return Refusal(
            RefusalReason.COARSE_GRAINING_NOT_TOTAL,
            f"the declared coarse-graining is on the raw alphabet of "
            f"{declared} port(s) but the port map declares K = {ports}",
        )
    return None


def _check_detector_layer(request: ReceiverRequest) -> Refusal | None:
    """Return a refusal if layer L1 does not match the declared port map.

    ``interface.yaml`` ``inputs.detector_layer``: ``eta_k`` and ``p_dc|k`` in
    ``[0, 1]``, one row per declared port. The range is decided EXACTLY, on the
    rational the declared number denotes, after refusing a non-finite one: a
    binary64 comparison would pass an exact rational a hair above one (which
    rounds to ``1.0``) or below zero, and the default factor of
    ``detector-imperfections/req:efficiency-normalization`` would then be
    formed from an efficiency outside the declared domain.
    """
    labels = tuple(port.label for port in request.detector_layer)
    if labels != request.port_map.labels:
        return Refusal(
            RefusalReason.PORT_MAP_MALFORMED,
            f"the detector layer declares ports {list(labels)} and the port map "
            f"declares {list(request.port_map.labels)}; layer L1 carries one row "
            f"per declared port, in the port map's order",
        )
    for port in request.detector_layer:
        for name, declared in (
            ("eta", port.efficiency),
            ("p_dc", port.dark_count_probability),
        ):
            value = to_float(declared)
            if not math.isfinite(value) or not 0 <= Fraction(declared) <= 1:
                return Refusal(
                    RefusalReason.PORT_MAP_MALFORMED,
                    f"port {port.label!r} declares {name} = {declared}; the inputs "
                    f"table's `detector_layer` requires the closed interval [0, 1]",
                )
    return None


def _check_route_source(
    request: ReceiverRequest, route: InputRoute, tolerances: NumericalTolerances
) -> Refusal | None:
    """Return a refusal if the supplied route object fails its declared domain."""
    if route is InputRoute.PORT_GRAMS:
        return _check_declared_grams(request, tolerances)
    if route is InputRoute.INSTRUMENT_MATRIX:
        return _check_declared_matrix(request, tolerances)
    graph = request.element_graph
    if graph is None:  # pragma: no cover - the route says otherwise
        return None
    return check_element_graph(graph, len(request.mode_space), tolerances)


def _check_declared_grams(
    request: ReceiverRequest, tolerances: NumericalTolerances
) -> Refusal | None:
    """Check route (i): admissibility and the inputs table's rank consistency."""
    family = request.port_grams
    if family is None:  # pragma: no cover - the route says otherwise
        return None
    if family.labels != request.port_map.labels:
        return Refusal(
            RefusalReason.PORT_GRAMS_NOT_ADMISSIBLE,
            f"the declared Gram family is keyed {list(family.labels)} and the "
            f"port map declares {list(request.port_map.labels)}",
        )
    if family.dimension != request.input_modes.dimension:
        return Refusal(
            RefusalReason.PORT_GRAMS_NOT_ADMISSIBLE,
            f"the declared Grams act on a space of dimension {family.dimension} "
            f"and the declared input space has dimension "
            f"{request.input_modes.dimension}",
        )
    refusal = check_gram_family_admissible(family, tolerances)
    if refusal is not None:
        return refusal
    sizes = [len(modes) for _, modes in request.port_map.entries]
    return check_rank_against_port_sizes(family, sizes, tolerances)


def _check_declared_matrix(
    request: ReceiverRequest, tolerances: NumericalTolerances
) -> Refusal | None:
    """Check route (ii) -- Def. ``def:tolmap`` (v), at the declared ``eps_1``.

    The shape is Definition ``def:instrument`` (iv), rows-by-outputs and
    columns-by-inputs over ``M``. The contractivity test is item (v): "the
    matrix is admitted when ``lmax(Gamma^dagger Gamma) <= 1 + eps_1``".

    **THE ADMISSION AND THE RESIDUAL ARE THE SAME TEST ON THE SAME NUMBER**, and
    the contract proves it rather than asserting an analogy.
    ``Gamma^dagger Gamma`` is Hermitian positive semidefinite, so
    ``(Gamma^dagger Gamma - 1)_+`` has eigenvalues ``(lambda_i - 1)_+`` and
    Eq. ``eq:r1islmax`` gives

        r_1 = ||(Gamma^dagger Gamma - 1)_+|| = (lmax(Gamma^dagger Gamma) - 1)_+ ,

    so "``r_1 <= eps_1``" and "``lmax(Gamma^dagger Gamma) <= 1 + eps_1``" are
    the SAME TEST. This function evaluates ``lmax`` directly, the form item (v)
    writes; :mod:`certiqs_key.receiver.residuals` evaluates the positive-part norm,
    the form Eq. ``eq:res1`` writes; the identity is why they can never
    disagree, and a property test holds them to it.

    ONE-SIDED AS A TEST, TWO-SIDED IN ITS CONSEQUENCES: it admits ``lmax`` in
    ``(1, 1 + eps_1]``, which the exact condition excludes -- deliberately,
    since a lossless receiver has ``lmax = 1`` EXACTLY and "a computed value one
    rounding unit above 1 would refuse it" -- and "refuses nothing that the
    exact condition, applied to the same computed number, would admit".

    ROUTE (ii) CARRIES NO SEPARATE GRAM ADMISSIBILITY CHECK, and that is a
    theorem rather than an omission: Theorem ``thm:port-grams`` (i) DERIVES
    ``sum_k A_k <= Gamma_Inp^dagger Gamma_Inp <= 1`` from contractivity. That
    derivation is an implication between EXACT quantities and transports NO
    ADMISSION: the computed ``lmax(A_Sigma)`` and the computed ``c`` are
    separate evaluations, and Definition ``def:tolmap`` (iv) decides the bound
    data on this route as on every other (Remark ``rem:bound-data-band``;
    ``interface.yaml`` ``inputs.instrument_matrix``).
    """
    gamma = request.instrument_matrix
    if gamma is None:  # pragma: no cover - the route says otherwise
        return None
    size = len(request.mode_space)
    if gamma.shape != (size, size):
        return Refusal(
            RefusalReason.INSTRUMENT_MATRIX_NOT_CONTRACTION,
            f"the supplied instrument matrix has shape {gamma.shape} on a "
            f"declared mode space of {size} modes; Definition def:instrument "
            f"(iv) indexes it rows-by-outputs and columns-by-inputs over M",
        )
    largest = lambda_max(gamma.conj().T @ gamma)
    if largest > 1.0 + tolerances.eps_1:
        return Refusal(
            RefusalReason.INSTRUMENT_MATRIX_NOT_CONTRACTION,
            f"the supplied instrument matrix is not a contraction: "
            f"lmax(Gamma^dagger Gamma) = {largest}, above 1 + eps_1 = "
            f"{1.0 + tolerances.eps_1}; by eq:r1islmax this is the test "
            f"r_1 <= eps_1 on the same number",
        )
    return None


def _check_dark_counts(
    request: ReceiverRequest, tolerances: NumericalTolerances
) -> Refusal | None:
    """Return a refusal if the dark-count declaration is not admissible.

    ROUTE EXCLUSIVITY COMES FIRST: a request supplying a declared ``R``
    together with any non-zero ``p_dc|k`` is refused with the contract-verbatim
    ``dark_count_channel_declared_twice`` (the inputs table, Requirement
    ``req:dark-route-exclusive``, the refusal rules).

    **THEN (D1) AT ``eps_4`` AND (D2) AT ``eps_2`` ON THE DECLARED ROUTE, AND
    ON THAT ROUTE ALONE.** Definition ``def:tolmap`` (iii) scopes both to "a
    *declared* ``R``", and Remark ``rem:corrdark`` says of the other route that
    for the product form both are DERIVED (Theorem ``thm:dark-counts`` (i)). Remark
    ``rem:d2slack`` (b) puts it as the reason ``delta_dc`` is 0 there: (D1) and
    (D2) are THEOREMS there (Theorem ``thm:dark-counts`` (i)) and NOT TESTS, so
    there is no slack to carry. Applying the threshold to the generated form
    would apply a test the contract states is not applied, and the
    floating-point evaluation of Eq. ``eq:darkR``'s column sums could then
    refuse a channel (D1) holds for BY THEOREM. The window is narrow --
    ``eps_4`` also bounds the completeness residual ``r_4``, which is non-zero
    at the same order -- and the direction is conservative, but a test the
    contract does not state is not this module's to apply.

    ``delta_dc`` IS UNAFFECTED and stays route-based: Eq. ``eq:darkdelta`` is a
    two-case definition ON THE ROUTE, decided in
    :func:`certiqs_key.receiver.dark.composition_correction` and not here.
    """
    probabilities = [port.dark_count_probability for port in request.detector_layer]
    source_refusal = check_dark_count_source(request.dark_count_channel, probabilities)
    if source_refusal is not None:
        return source_refusal
    channel = request.dark_count_channel
    if channel is None:
        # THE GENERATED ROUTE: (D1) and (D2) are theorems here and are not
        # tested. The product form is built so that the emitted route is
        # recorded, and nothing about it is decided under a threshold.
        return None
    if channel.port_count != request.port_map.port_count:
        return Refusal(
            RefusalReason.DARK_CONDITION_D1_FAILED,
            f"the declared dark-count channel is on the raw alphabet of "
            f"{channel.port_count} port(s) but the port map declares "
            f"K = {request.port_map.port_count}",
        )
    return check_dark_channel(channel, tolerances)
