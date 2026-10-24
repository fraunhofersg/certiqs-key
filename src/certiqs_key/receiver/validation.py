"""The cross-cutting input validations of the inputs and parameters tables.

Every function here returns a :class:`~certiqs_key.receiver.reasons.Refusal` or
``None`` and NEVER raises: the ``fail_closed`` convention (``interface.yaml``
``conventions``) says "every failed validation produces a refusal with a
machine-readable reason and no artifact", and its four clauses are each
attached to a named site --

    no default is substituted for a missing datum
        Requirement ``req:window-declaration``'s refusal -- no ``m_t`` at a
        setting where (X) fails -- and the ``numerical_tolerances`` input,
        declared, never defaulted, with its declared domain ``[0, 1)`` and its
        verbatim refusal;
    no parameter is clipped into its domain
        ``parameters.domains`` and Definition ``def:graph`` (E1), realised in
        :mod:`certiqs_key.receiver.catalogue`;
    no cycle is resolved
        Definition ``def:graph`` (E2) and Remark ``rem:noloops``, realised in
        :mod:`certiqs_key.receiver.graph`;
    no tolerance is ignored
        ``parameters.exactness`` and Assumption ``ass:exact``, realised in
        :func:`check_parameter_tolerances`.

The object-level validations live with their objects -- the mode space, the
input split and the port map in :mod:`certiqs_key.receiver.modes`; the catalogue
domains in :mod:`certiqs_key.receiver.catalogue`; the graph conditions in
:mod:`certiqs_key.receiver.graph`; the Gram family in
:mod:`certiqs_key.receiver.grams`; the probe declaration in
:mod:`certiqs_key.receiver.settings`; the dark-count channel in
:mod:`certiqs_key.receiver.dark`; the residuals in
:mod:`certiqs_key.receiver.residuals`. What is left here is what belongs to no
single object.

THE THREE ROUTES ARE MUTUALLY EXCLUSIVE AND A DOUBLE REQUEST IS REFUSED
=======================================================================
``interface.yaml`` ``input_routes.rule``: EXACTLY ONE of ``port_grams``,
``instrument_matrix`` and ``element_graph`` is present, and A REQUEST CARRYING
TWO IS REFUSED RATHER THAN RESOLVED BY PRECEDENCE. No precedence and no
reconciliation: the three routes CONVERGE on one canonical object
(``input_routes.convergence``), and two presentations of it are not guaranteed
to agree, so choosing would be inventing a check the contract does not state.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol

from certiqs_key.receiver.numerics import Scalar, tolerance_field_is_admissible
from certiqs_key.receiver.reasons import PROSE_REASONS, Refusal, RefusalReason

__all__ = [
    "ROUTE_KEYS",
    "ParameterRecord",
    "check_exact_window",
    "check_exactly_one_route",
    "check_parameter_tolerances",
    "check_photon_cutoff",
    "check_tail_window",
]

#: The three mutually exclusive input routes of interface.yaml
#: `input_routes.mutually_exclusive`, in its order: route (i), route (ii),
#: route (iii).
ROUTE_KEYS: tuple[str, ...] = ("port_grams", "instrument_matrix", "element_graph")


def check_exactly_one_route(present: Mapping[str, bool]) -> Refusal | None:
    """Return a refusal unless exactly one input route is present.

    ``interface.yaml`` ``input_routes.rule``. The refusal names the
    exactly-one-route rule as the failing condition; the contract spells no
    reason string for it (``refusals.named_without_a_spelling``), so the
    spelling is this module's (:mod:`certiqs_key.receiver.reasons`).
    """
    supplied = [key for key in ROUTE_KEYS if present.get(key, False)]
    if len(supplied) == 1:
        return None
    if not supplied:
        return Refusal(
            RefusalReason.INPUT_ROUTES_NOT_EXACTLY_ONE,
            f"no input route is present; input_routes requires exactly one of "
            f"{list(ROUTE_KEYS)}",
        )
    return Refusal(
        RefusalReason.INPUT_ROUTES_NOT_EXACTLY_ONE,
        f"the request carries {supplied}; input_routes requires exactly one of "
        f"{list(ROUTE_KEYS)} and REFUSES a request carrying two rather than "
        f"resolving it by precedence",
    )


class ParameterRecord(Protocol):
    """A declared record that carries parameters and their reserved field.

    A catalogue element (:class:`~certiqs_key.receiver.catalogue.Component`),
    a detector-layer row and a probe setting: the three records whose
    parameters Assumption ``ass:exact`` makes exact.
    """

    @property
    def tolerances(self) -> Mapping[str, Scalar]:
        """Return the reserved ``tolerance`` field, keyed by parameter name."""
        ...


def check_parameter_tolerances(
    records: Iterable[tuple[str, ParameterRecord]],
) -> Refusal | None:
    """Return a refusal if any reserved ``tolerance`` field is non-zero.

    Requirement ``req:reserved-tolerance-field``: "The engine validates the
    reserved tolerance field of every declared parameter as absent or exactly
    zero, and refuses it otherwise", because an ignored tolerance would be a
    silent claim that the device is exact (Assumption ``ass:exact``). The
    request passes every record that carries parameters
    (:meth:`certiqs_key.receiver.request.ReceiverRequest.parameter_records`):
    the elements, the detector-layer rows and the probe settings. The first
    non-zero field, in that order, is the refusal.

    The interface's reason is PROSE, "parameter uncertainty sets are out of
    scope", and is carried in the refusal's ``detail``; the machine key is this
    module's spelling. ``tolerance = 0`` exactly is admitted, and that is the
    one value that is.
    """
    for name, record in records:
        kind = getattr(record, "record_kind", "element")
        for parameter, value in record.tolerances.items():
            if not tolerance_field_is_admissible(value):
                return Refusal(
                    RefusalReason.PARAMETER_TOLERANCE_NOT_ZERO,
                    f'"{PROSE_REASONS["parameter_tolerance"]}": {kind} '
                    f"{name!r} declares tolerance = {value} on parameter "
                    f"{parameter!r}; this module admits only an absent or exactly "
                    f"zero field",
                )
    return None


def check_photon_cutoff(cutoff: int) -> Refusal | None:
    """Return a refusal unless the declared cutoff satisfies ``N >= 0``.

    ``interface.yaml`` ``inputs.photon_cutoff``, with ``parameters.photon_cutoff``:
    ``N`` is a DECLARED PROTOCOL PARAMETER, not a numerical convenience, and
    THIS MODULE DOES NOT CHOOSE IT AND DOES NOT OPTIMIZE IT.
    """
    if cutoff < 0:
        return Refusal(
            RefusalReason.PHOTON_CUTOFF_NEGATIVE,
            f"the declared photon cutoff N = {cutoff} is negative; the inputs "
            f"table requires N >= 0",
        )
    return None


def check_tail_window(
    cutoff: int,
    settings: Sequence[str],
    predicate_x: Mapping[str, bool],
    windows: Mapping[str, int],
) -> Refusal | None:
    """Return a refusal if the declared ``tail_window`` breaks an inputs-table rule.

    Three cases, settled and distinct:

    * a window MISSING at a setting where predicate (X) fails -- REFUSED.
      Requirement ``req:window-declaration``: a declaration supplying no
      window ``m_t`` at a setting where predicate (X) fails "is refused rather
      than defaulted", and that condition is decidable at input validation
      from declared data alone (Remark ``rem:flag-instances``), without
      computing a Gram, a determinant or an eigenvalue;
    * a window with ``m_t <= N`` -- REFUSED. ``interface.yaml``
      ``inputs.tail_window``: "m_t > N, validated", and the requirement refuses
      it at every setting, whatever its flag. The reason it cannot be relaxed
      is that the window ``{n : N < n <= m}`` would be EMPTY, so ``W_{N,m}``
      would be a minimum over nothing and the residual gap Eq. ``eq:resgap``
      would not be the finite real Lemma ``lem:windowtail`` (ii) and
      ``outputs.validation_results`` both require;
    * a window supplied where none is needed -- ADMITTED AND UNUSED.
      Requirement ``req:window-declaration``: a window ``m_t > N`` supplied at
      a setting whose flag is exact is UNUSED, NOT AN ERROR.
    """
    for setting in settings:
        window = windows.get(setting)
        if window is None:
            if predicate_x.get(setting, False):
                continue
            return Refusal(
                RefusalReason.TAIL_WINDOW_MISSING,
                f"setting {setting!r} fails predicate (X) -- its probe is on -- "
                f"and declares no tail_window m_t; Requirement "
                f"req:window-declaration refuses rather than defaulting one",
            )
        if window <= cutoff:
            return Refusal(
                RefusalReason.TAIL_WINDOW_NOT_ABOVE_CUTOFF,
                f"setting {setting!r} declares m_t = {window} at cutoff "
                f"N = {cutoff}; the inputs table requires m_t > N, and at "
                f"m_t <= N the window {{n : N < n <= m}} is empty",
            )
    return None


def check_exact_window(
    cutoff: int,
    settings: Sequence[str],
    predicate_x: Mapping[str, bool],
    tail_windows: Mapping[str, int],
    exact_windows: Mapping[str, int],
) -> Refusal | None:
    """Return a refusal if a declared ``exact_window`` depth is out of range.

    ``interface.yaml`` ``inputs.exact_window`` and Definition ``def:pmcex``'s
    opening sentence: a depth is "an integer with ``m*_t > N`` and, where
    predicate (X) fails at t, also ``m*_t <= m_t``". Requirement
    ``req:exact-window-declaration`` gives both conditions one verbatim reason,
    ``exact_window_depth_outside_declared_range``.

    THE SECOND CONDITION APPLIES ONLY WHERE (X) FAILS, and the asymmetry is not
    cosmetic. Where (X) holds no ``m_t`` is required at all
    (Requirement ``req:window-declaration``), branch 1 of Eq. ``eq:pmcex`` takes the
    remainder ``beta(m*_t + 1)`` by Lemma ``lem:exactwindow`` (ii), and nothing
    constrains the depth from above -- so a depth ABOVE an unused, supplied
    ``m_t`` is admitted there (the frozen
    ``XW-ADMIT-DEPTH-EXCEEDS-UNUSED-TAIL-WINDOW``). Where (X) fails, branch 2
    keeps its own analytic window and tail above the exact one, and ``m*_t <=
    m_t`` is what makes the two windows compose into the single window
    ``N < n <= m_t`` to which Lemma ``lem:exactwindow`` is applied (Remark
    ``rem:exact-window-remainders``). The boundary ``m*_t = m_t`` is ADMITTED,
    and its middle minimum is then over the empty index set.

    BOTH CHECKS ARE KIND (a) OF Definition ``def:tolmap``'s CLOSING
    ENUMERATION -- "a comparison of declared data against a declared domain" --
    which lists ``m*_t > N`` and ``m*_t <= m_t`` explicitly. NO TOLERANCE
    DECIDES EITHER, and none is consulted here. The conditional presence of
    ``eps_eig`` and ``eps_6`` is kind (b) and is decided in
    :func:`certiqs_key.receiver.numerics.tolerances_from_declaration`, before this,
    because those numbers decide the other validations.

    A DEPTH IS OPTIONAL AND PER SETTING. A setting carrying none is governed by
    Definition ``def:pmc``, which is not an error and is the whole opt-in rule;
    a declaration that carries a depth at some settings and not at others has
    its uniform weight BOUNDED BY THE SETTINGS WITHOUT ONE (Definition
    ``def:pmcex``, its per-setting paragraph).
    """
    for setting in settings:
        depth = exact_windows.get(setting)
        if depth is None:
            continue
        if depth <= cutoff:
            return Refusal(
                RefusalReason.EXACT_WINDOW_DEPTH_OUTSIDE_DECLARED_RANGE,
                f"setting {setting!r} declares the exact-window depth "
                f"m* = {depth} at cutoff N = {cutoff}; Definition def:pmcex "
                f"requires m*_t > N, and at m*_t <= N the window "
                f"{{n : N < n <= m*}} is empty",
            )
        if predicate_x.get(setting, False):
            continue
        window = tail_windows.get(setting)
        if window is None:
            # A missing m_t at a setting where (X) fails is refused by
            # check_tail_window, which runs first and names its own condition.
            continue
        if depth > window:
            return Refusal(
                RefusalReason.EXACT_WINDOW_DEPTH_OUTSIDE_DECLARED_RANGE,
                f"setting {setting!r} fails predicate (X) and declares the "
                f"exact-window depth m* = {depth} above its tail_window "
                f"m_t = {window}; Definition def:pmcex requires m*_t <= m_t "
                f"there, so that the exact and analytic windows compose into "
                f"the single window N < n <= m_t",
            )
    return None
