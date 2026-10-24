"""One run's inputs, as a value that can be held, compared and swept over.

WHAT A RUN CONFIG IS, AND WHAT IT IS NOT
========================================
It is NOT a pile of parameters that belong to nobody. Almost every field below is
owned by some module and is transcribed here unchanged:

    rounds                  ``meat-core`` Section 2.1 (``n``)
    parameters              ``meat-core`` Section 2.4 (alpha, eps_pa, eps_ev,
                            lambda_ec)
    eps_auth, k_auth        ``meat-core``'s parameters rows of A-AUTH, solve
                            inputs beside the declaration (written into the
                            ``parameters`` block of the payload)
    declared_tolerance      spec/architecture.md 2.8 -- the instance's own
                            number, owned by no module (see below)
    completeness_budget     ``statistics`` (``eps_comp``)
    constrained             ``statistics`` (the outcome selector)
    model                   the INSTANCE's channel model, opaque here
    device                  the INSTANCE's physical device, opaque here

What this record owns is the **composition**: the fact that these particular
values were selected together for one run. That is a real gap and not a
bookkeeping convenience. :mod:`certiqs_key.meat_core.docking` says of ``rounds`` that
"no row of Section 2.1 supplies it and no row of Section 2.2 emits it", and says
the same of the Section 2.4 parameters -- they are REQUIRED ARGUMENTS there
precisely because a default would be one module supplying a datum it does not
own. Something has to select them, that something is a run, and this is the
record of what it selected.

``model`` AND ``device`` ARE OPAQUE AND STAY OPAQUE
===================================================
The instance's channel-model parameters -- ``qber`` for the BB84 depolarizing
model -- travel here as a mapping this package never reads. Interpreting it would
put channel-model vocabulary in the orchestration tier, which is the ownership
inversion PRINCIPLES.md section 4 exists to prevent: an instance's provider factory
reads it, and nothing else does. Values are exact rationals, the house convention for
model parameters; a model needing otherwise is a widening decision, not a cast.

``device`` is the same field for the PHYSICAL APPARATUS rather than the channel:
the splitting ratio, the waveplate angle, the per-port efficiency and dark-count
probability, the photon cutoff. It is a SECOND mapping and not more keys in the
first, because the two are read by different providers at different stages --
:data:`~certiqs_key.runs.pipeline.DeviceProvider` before compilation and
:data:`~certiqs_key.runs.pipeline.HonestProvider` after it -- and an instance whose
receiver and whose channel share a parameter name would otherwise have to
rename one of them. The qubit bb84 instance declares neither and carries an
empty mapping.

Its values are :data:`DeviceValue`, and each of the two widenings past
``Fraction`` is DELIBERATE rather than a hole. ``model``'s own rule above says a
model parameter that is not an exact rational "is a widening decision, not a
cast", and these are those decisions, taken once for ``device``:

* ``str``, because not every declaration a device makes is a quantity. The
  optical instances sweep a ``route`` axis whose values are ``encoded``,
  ``licensed`` and ``licensed+two-sector``, which name WHICH REDUCTION IS
  DECLARED over one unchanged apparatus. Encoding those as numbers would put a
  decoding table somewhere and would print an integer in the run record where
  the record should say what was declared;
* ``Mapping[str, Fraction]``, because an apparatus has PARTS. A receiver's
  detection efficiency and dark-count probability are one number PER DETECTOR,
  and the optical instance declares four of each. The mapping is keyed by the
  receiver's OWN PORT LABELS -- ``Kind.PER_PORT_FRACTION``'s
  ``per_port_labels``, read off the port map -- and never by position or by a
  count, because how many detectors there are is the receiver's declaration and
  not this format's. A flat ``efficiency_0 ... efficiency_3`` would be that
  count written into the configuration's key space; a scalar meaning "the same
  on every port" would make the shape of a value depend on how uniform it
  happens to be, and the instance's reader and its key check would then have
  two shapes to agree about. So there is ONE shape per kind, and
  :func:`~certiqs_key.runs.surface.check_keys` decides it from the table.

``model`` is NOT widened with either: a channel-model parameter is a physical
quantity by construction, and no instance has asked otherwise.

``declared_tolerance`` IS NOT ONE OF THEM
=========================================
It is a first-class field with **no default and no fallback**, and what it is is
fixed by spec/architecture.md 2.8, quoted here rather than paraphrased:

    Each instance declares exactly one numerical tolerance ``tau`` in its run
    configuration. It is the **ceiling on the pre-snap defect an instance may
    repair**: a declared block whose measured defect -- Hermiticity,
    positivity, completeness, column-stochasticity, a probability sum --
    exceeds ``tau`` is a modelling error and is refused; one within ``tau`` is
    snapped onto an exactly admissible family and the snap is recorded with the
    defect it corrected. Modules receive no tolerance to reason with [...]
    Consequence, stated plainly: a tolerance never widens what a security
    predicate admits; it only bounds how far an instance may move its own
    declaration.

and

    ``tau`` itself has **no default and no fallback**: a run whose
    configuration does not declare it is refused, because a defaulted ceiling
    on repair decides a security-relevant act on nobody's authority.

Three consequences this record carries, and none of them is this tier's
invention:

* it is a binary64 ``float`` in ``[0, 1)``. 2.8: "``tau`` lies in ``[0, 1)``
  [...] **The upper limit is derived, not chosen:** at ``tau >= 1`` a
  completeness condition is satisfied by the all-zero family". Absence, a value
  outside the interval and a value that is not a ``float`` are each a typed
  refusal at construction (:class:`RunConfigError`), never a substituted
  number;
* **no module is told a tolerance at all.** ``meat-core`` has no tolerance
  row, ``declaration_from_bundle`` and ``solve_bundle`` take no tolerance, and
  ``reductions`` and ``protocol-compiler`` carry none. THIS FIELD IS NOT A
  ZERO ANYTHING IS TOLD: it is the ceiling on the pre-snap defect the
  INSTANCE may repair, spent before a module sees the data
  (:mod:`certiqs_key.runs.pipeline`, "THIS TIER PASSES NO TOLERANCE");
* it is a *numerical* tolerance sized on the defects the engine's own
  arithmetic produces (2.8): not a device-uncertainty budget, not
  characterization error. ``eps_gap`` and ``eps_eig`` are slacks the instance
  declares to the receiver, a supplier, and are declared separately
  (``foundations/req:tolerance-scope`` (iii)): ``eps_gap`` bounds a residual
  gap the receiver checks, and ``eps_eig`` bounds the error of the receiver's
  floating-point evaluation of an eigenvalue under its assumption A-EIG
  (``receiver/ass:eig``, ``foundations/req:exact-island``) and is never
  derived from the declared tolerance.

There is no "absent means exact" reading of the tolerance: an absent row does
not *mean* anything here, because there is no absent row.
:func:`certiqs_key.runs.record._config_payload` records ``declared_tolerance``
under its own name.

THERE IS NO REQUESTED TIER
==========================
``meat-core`` takes no requested tier (the interface's
``retired_parameter_rows``: "there is no ``requested_assurance``"), because
the bracket is accumulated during the same solver run and declining to report
it would report less about the same numbers. spec/architecture.md 2.8: "Every run
reports both numbers and a ``reported_tier`` field saying which is the claim", and the
ACHIEVED tier is on the result and is never silently upgraded.

So there is no such field. A configuration slot that
reached no module would be a number recorded as though it had decided
something, which is the one thing this record must not do -- every other field
here is owned by a module and transcribed unchanged.

NO DEFAULTS FOR ANYTHING A MODULE OWNS
======================================
``rounds``, ``completeness_budget`` and ``parameters`` have no default here, for
the reason :mod:`certiqs_key.meat_core.docking` gives for refusing them: substituting
one would be this tier deciding a value a contract owns. ``alpha`` defaults to
``None`` meaning "the declared default", which is a deferral rather than a
decision, and the two remaining defaults reproduce ``meat-core``'s own
(``first-order``, which is that module's own default at 1.0.0 and the headline
tier of spec/architecture.md 2.8) and ``statistics``'s own (all
outcomes constrained).
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from fractions import Fraction
from hashlib import sha256
from typing import Any, Final, cast

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.meat_core.finitekey.keylength import check_authentication_parameters
from certiqs_key.runs.errors import RunInputReason, RunInputValueError
from certiqs_key.solvers.frank_wolfe.joint_options import ORACLE_CHOICES
from certiqs_key.solvers.types import ADVANCED_METHODS, ORDINARY_METHODS
from certiqs_key.statistics.rules import EndpointRuleName, TailEvaluation

__all__ = [
    "ADVANCED_SOLVER_KEYS",
    "NO_DECLARED_TOLERANCE",
    "ORDINARY_SOLVER_KEYS",
    "RETIRED_PARAMETERS",
    "AdvancedSolverSettings",
    "AlphaSearchError",
    "AlphaSearchSettings",
    "DeviceValue",
    "RunConfig",
    "RunConfigError",
    "SolverSettings",
    "WarmStartSeed",
    "canonical_json",
    "config_digest",
    "parameters_payload",
]

#: What one ``device`` key may carry: an exact rational, a NAME, or one exact
#: rational PER RECEIVER PORT keyed by the port map's own labels. The three
#: forms and the reason each exists are in the module docstring; which of them
#: a given key takes is fixed by its ``Kind`` in the instance's parameter table
#: (:mod:`certiqs_key.runs.surface`), so a caller never has to guess and
#: :func:`~certiqs_key.runs.surface.check_keys` decides it from the same table.
type DeviceValue = Fraction | str | Mapping[str, Fraction]


class RunConfigError(RunInputValueError):
    """A run configuration cannot be constructed, and the reason is named.

    A hard error rather than a :class:`~certiqs_key.runs.pipeline.SliceRefusal`,
    because nothing has been composed yet: there is no stage to attribute the
    outcome to and no module whose vocabulary it would be in. It carries a
    machine-readable :attr:`reason` all the same, so that a caller -- a sweep
    driver, an instance's entry point, a test -- can tell "the tolerance was
    not declared" from "the tolerance is outside its domain" without reading
    prose. The code is a member of the run tier's one input vocabulary,
    :class:`~certiqs_key.runs.errors.RunInputReason`.
    """


class _ToleranceNotDeclared:
    """The one object that spells "this configuration declared no tolerance"."""

    __slots__ = ()

    def __repr__(self) -> str:
        """Render as what it means, so a traceback reads correctly."""
        return "<no declared_tolerance>"


#: The value :attr:`RunConfig.declared_tolerance` holds when nothing was
#: declared -- which is refused at construction and therefore never survives
#: one. IT IS NOT A DEFAULT: it is the absence of a value, spelled so that the
#: refusal can be typed. spec/architecture.md 2.8 requires the field to have
#: "no default and no fallback", and Python's own missing-argument ``TypeError``
#: would refuse without a reason code, which is the one thing a fail-closed
#: boundary here owes its caller.
#:
#: It is annotated ``float`` so that every reader of
#: :attr:`RunConfig.declared_tolerance` sees a ``float`` and none of them has to
#: narrow a union that a valid config can never be in. The cast is confined to
#: this module and the object is unusable as a number by construction: it has no
#: ``__float__``, no ordering and no arithmetic, so any path that skipped the
#: check below fails loudly on first use rather than computing with a sentinel.
NO_DECLARED_TOLERANCE: Final[float] = cast(float, _ToleranceNotDeclared())


@dataclass(frozen=True)
class WarmStartSeed:
    """Which prior final iterate a run starts from: a locator and a content hash.

    ``file`` is where the seed was read (a path as the caller gave it, best
    relative); ``sha256`` is the hash of that file's bytes, and it is the
    seed's IDENTITY: the loader refuses a file whose bytes do not hash to it,
    so a record naming this seed names exactly one iterate wherever the file
    has since moved.

    THE PATH IS A LOCATOR AND STAYS OUT OF THE DIGEST. It is carried in the
    payload so a caller can re-run the configuration, but
    :func:`config_digest` drops it: two requests starting from the same seed
    bytes are the same request wherever the file lies.
    """

    file: str
    sha256: str

    def __post_init__(self) -> None:
        """Refuse a hash that is not one."""
        digest = self.sha256
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise RunConfigError(
                f"warm_start sha256 is {digest!r}; a seed is identified by the "
                "64-character lowercase hex sha256 of its file",
                reason=RunInputReason.WARM_START_HASH_MALFORMED,
            )

    def as_payload(self) -> dict[str, str]:
        """Return the seed's locator and identity as JSON."""
        return {"file": self.file, "sha256": self.sha256}


@dataclass(frozen=True)
class AdvancedSolverSettings:
    """The expert search choices of ``solver.advanced``: none a proof threshold.

    An ordinary configuration needs none of these: :class:`SolverSettings`'
    ``method``, ``budget_seconds`` and ``max_iterations`` are the public
    tier, and this block holds what a benchmark or a study tunes beyond them.
    ``method`` overrides the ordinary method with one of the expert methods
    (:data:`~certiqs_key.solvers.types.ADVANCED_METHODS`); setting both is
    refused by :class:`SolverSettings`. Every field ``None`` is the block not
    chosen, and :class:`SolverSettings` normalises it away.
    """

    #: An expert candidate search method, overriding ``solver.method``.
    method: str | None = None
    #: The general format's linear-oracle choice, ``"qics"`` or ``"spectral"``.
    #: ``None`` takes the solver's own (``"qics"``).
    oracle: str | None = None
    #: The duality-gap stopping tolerance, a diagnostic quality target.
    #: ``None`` takes the driver's own.
    gap_tolerance: float | None = None
    #: A prior point's final iterate to start from; ``None`` is a cold start.
    warm_start: WarmStartSeed | None = None
    #: ``frank-wolfe/req:certified-evaluation``'s option, ``"on"``, ``"off"``
    #: or ``"strict"``; ``None`` takes ``on``.
    certified_evaluation: str | None = None

    def __post_init__(self) -> None:
        """Refuse a choice that is not one, rather than clamping it."""
        if self.method is not None and self.method not in ADVANCED_METHODS:
            hint = (
                f"; {self.method!r} is an ordinary method, set solver.method"
                if self.method in ORDINARY_METHODS
                else ""
            )
            raise RunConfigError(
                f"advanced candidate method {self.method!r} is not admitted; "
                f"admitted: {list(ADVANCED_METHODS)}{hint}",
                reason=RunInputReason.SOLVER_METHOD_NOT_ADMITTED,
            )
        if self.gap_tolerance is not None and not (
            math.isfinite(self.gap_tolerance) and self.gap_tolerance > 0.0
        ):
            raise RunConfigError(
                f"gap_tolerance is {self.gap_tolerance!r}; a stopping tolerance "
                "is a finite positive number",
                reason=RunInputReason.SOLVER_GAP_TOLERANCE_NOT_POSITIVE,
            )
        if self.certified_evaluation not in (None, "on", "off", "strict"):
            raise RunConfigError(
                f"certified_evaluation is {self.certified_evaluation!r}; admitted: "
                "on, off, strict",
                reason=RunInputReason.SOLVER_CERTIFIED_EVALUATION_NOT_ADMITTED,
            )
        if self.oracle is not None and self.oracle not in ORACLE_CHOICES:
            raise RunConfigError(
                f"oracle is {self.oracle!r}; admitted: {list(ORACLE_CHOICES)}",
                reason=RunInputReason.SOLVER_ORACLE_NOT_ADMITTED,
            )

    def chosen(self) -> bool:
        """Return whether any field is chosen; an empty block is no block."""
        return any(getattr(self, name) is not None for name in ADVANCED_SOLVER_KEYS)

    def as_payload(self) -> dict[str, object]:
        """Return the chosen fields as JSON; an unchosen one is not written."""
        payload: dict[str, object] = {}
        if self.method is not None:
            payload["method"] = self.method
        if self.oracle is not None:
            payload["oracle"] = self.oracle
        if self.gap_tolerance is not None:
            payload["gap_tolerance"] = self.gap_tolerance
        if self.warm_start is not None:
            payload["warm_start"] = self.warm_start.as_payload()
        if self.certified_evaluation is not None:
            payload["certified_evaluation"] = self.certified_evaluation
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> AdvancedSolverSettings:
        """Return the block a payload of :meth:`as_payload` describes.

        A key the block does not read is refused
        (``solver_key_not_admitted``), so a misspelt choice is not silently
        the solver's own.
        """
        unknown = sorted(set(payload) - set(ADVANCED_SOLVER_KEYS))
        if unknown:
            raise RunConfigError(
                f"solver.advanced carries {unknown}; it reads "
                f"{sorted(ADVANCED_SOLVER_KEYS)}",
                reason=RunInputReason.SOLVER_KEY_NOT_ADMITTED,
            )
        gap = payload.get("gap_tolerance")
        oracle = payload.get("oracle")
        seed = payload.get("warm_start")
        return cls(
            method=payload.get("method"),
            oracle=None if oracle is None else str(oracle),
            gap_tolerance=None if gap is None else float(gap),
            warm_start=(
                None
                if seed is None
                else WarmStartSeed(file=str(seed["file"]), sha256=str(seed["sha256"]))
            ),
            certified_evaluation=payload.get("certified_evaluation"),
        )


#: The keys of ``solver.advanced``: :class:`AdvancedSolverSettings`' fields.
ADVANCED_SOLVER_KEYS: Final[tuple[str, ...]] = (
    "method",
    "oracle",
    "gap_tolerance",
    "warm_start",
    "certified_evaluation",
)

#: The keys of ``solver`` beside ``advanced``: the ordinary tier.
ORDINARY_SOLVER_KEYS: Final[tuple[str, ...]] = (
    "method",
    "budget_seconds",
    "max_iterations",
)


@dataclass(frozen=True)
class SolverSettings:
    """Recorded search effort and method choices, never proof thresholds.

    TWO TIERS. The ordinary one is what a user chooses: ``method`` (``auto``
    or ``fw``, :data:`~certiqs_key.solvers.types.ORDINARY_METHODS`),
    ``budget_seconds``, which bounds the whole coordinator, and
    ``max_iterations``, a method-native work cap of an explicit method; under
    ``auto`` it caps the Frank-Wolfe stages only, and the factor, entropy and
    corrective stages run to their own convergence or their share of
    ``budget_seconds``. Everything else -- an expert method, the oracle, the
    diagnostic gap target, a warm start, the certified evaluation's option --
    is :class:`AdvancedSolverSettings` under ``advanced``. An absent method
    takes the default :func:`~certiqs_key.runs.surface.solver_request`
    resolves. Support, feasibility, row and oracle gates remain solver-owned.
    """

    #: The ordinary candidate search method, ``"auto"`` or ``"fw"``; absent
    #: takes the default ``solver_request`` resolves.
    method: str | None = None
    #: One solver-wide wall budget, including all attempts and assessments.
    budget_seconds: float | None = None
    #: The work cap: Frank-Wolfe iterations, or an explicit factor, entropy
    #: or corrective method's own; under ``auto`` the Frank-Wolfe stages'
    #: only. ``None`` takes the driver's own.
    max_iterations: int | None = None
    #: The expert choices; ``None`` (or a block choosing nothing, normalised
    #: to ``None``) takes the solver's own for each.
    advanced: AdvancedSolverSettings | None = None

    def __post_init__(self) -> None:
        """Refuse a budget or method that is not one, rather than clamping it."""
        if self.method is not None and self.method not in ORDINARY_METHODS:
            hint = (
                f"; {self.method!r} is an advanced method, set "
                "solver.advanced.method"
                if self.method in ADVANCED_METHODS
                else ""
            )
            raise RunConfigError(
                f"candidate method {self.method!r} is not admitted; admitted: "
                f"{list(ORDINARY_METHODS)}{hint}",
                reason=RunInputReason.SOLVER_METHOD_NOT_ADMITTED,
            )
        if self.budget_seconds is not None and not (
            math.isfinite(self.budget_seconds) and self.budget_seconds > 0
        ):
            raise RunConfigError(
                "budget_seconds must be finite and positive",
                reason=RunInputReason.SOLVER_BUDGET_NOT_POSITIVE,
            )
        if self.max_iterations is not None and self.max_iterations < 1:
            raise RunConfigError(
                f"max_iterations is {self.max_iterations}; a budget of fewer "
                "than one iteration runs no loop at all",
                reason=RunInputReason.SOLVER_BUDGET_NOT_POSITIVE,
            )
        if self.advanced is not None and not self.advanced.chosen():
            object.__setattr__(self, "advanced", None)
        if (
            self.method is not None
            and self.advanced is not None
            and self.advanced.method is not None
        ):
            raise RunConfigError(
                f"solver.method is {self.method!r} and solver.advanced.method is "
                f"{self.advanced.method!r}; choose one",
                reason=RunInputReason.SOLVER_METHOD_SET_TWICE,
            )

    @classmethod
    def from_choices(
        cls,
        *,
        method: str | None = None,
        budget_seconds: float | None = None,
        max_iterations: int | None = None,
        oracle: str | None = None,
        gap_tolerance: float | None = None,
        warm_start: WarmStartSeed | None = None,
        certified_evaluation: str | None = None,
    ) -> SolverSettings:
        """Return the settings of flat choices, each placed in its tier.

        For a research command line or a benchmark that names any of the six
        methods: an ordinary one (``auto``, ``fw``) becomes ``method``, an
        expert one ``advanced.method``, and an unknown one is refused as
        ``method`` refuses it. The expert keys go under ``advanced``.
        """
        expert = method if method in ADVANCED_METHODS else None
        return cls(
            method=None if expert is not None else method,
            budget_seconds=budget_seconds,
            max_iterations=max_iterations,
            advanced=AdvancedSolverSettings(
                method=expert,
                oracle=oracle,
                gap_tolerance=gap_tolerance,
                warm_start=warm_start,
                certified_evaluation=certified_evaluation,
            ),
        )

    @property
    def chosen_method(self) -> str | None:
        """Return the method chosen in either tier, ``None`` where neither chose."""
        if self.advanced is not None and self.advanced.method is not None:
            return self.advanced.method
        return self.method

    def as_payload(self) -> dict[str, object]:
        """Return the fields as JSON.

        ``max_iterations`` is always written (``null`` where nothing was
        chosen); ``method``, ``budget_seconds`` and the ``advanced`` block are
        WRITTEN ONLY WHEN CHOSEN, and inside the block only its chosen keys.
        """
        payload: dict[str, object] = {"max_iterations": self.max_iterations}
        if self.method is not None:
            payload["method"] = self.method
        if self.budget_seconds is not None:
            payload["budget_seconds"] = self.budget_seconds
        if self.advanced is not None:
            payload["advanced"] = self.advanced.as_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> SolverSettings:
        """Return the settings a payload of :meth:`as_payload` describes.

        A key the settings do not read is refused
        (``solver_key_not_admitted``); one of the keys that live under
        ``advanced`` is refused with that place named.
        """
        if "step_rule" in payload:
            raise RunConfigError(
                "historical step_rule requires the explicit benchmark replay adapter",
                reason=RunInputReason.SOLVER_METHOD_NOT_ADMITTED,
            )
        known = {*ORDINARY_SOLVER_KEYS, "advanced"}
        unknown = sorted(set(payload) - known)
        if unknown:
            moved = [key for key in unknown if key in ADVANCED_SOLVER_KEYS]
            where = (
                f"; {', '.join(moved)} belongs under solver.advanced" if moved else ""
            )
            raise RunConfigError(
                f"solver carries {unknown}; it reads {sorted(known)}{where}",
                reason=RunInputReason.SOLVER_KEY_NOT_ADMITTED,
            )
        iterations = payload.get("max_iterations")
        advanced = payload.get("advanced")
        return cls(
            method=payload.get("method"),
            budget_seconds=(
                None
                if payload.get("budget_seconds") is None
                else float(payload["budget_seconds"])
            ),
            max_iterations=None if iterations is None else int(iterations),
            advanced=(
                None
                if advanced is None
                else AdvancedSolverSettings.from_payload(advanced)
            ),
        )


class AlphaSearchError(RunConfigError):
    """An alpha-search setting that is not one, refused rather than clamped.

    Coded like every other configuration refusal
    (``alpha_search_setting_out_of_domain``), and still a ``ValueError``.
    """


@dataclass(frozen=True)
class AlphaSearchSettings:
    """Where and how hard the outer alpha search looks: search effort, no threshold.

    THE OPT-IN OUTER SEARCH OF THE RUN TIER (the declared alpha stays the
    default). :attr:`RunConfig.alpha_search` carries it; the search itself is
    :mod:`certiqs_key.runs.alpha_search`, which says why it is sound and what
    it ranks. It is defined HERE, beside the configuration that carries it,
    because that module runs the pipeline and the configuration may not import
    it.

    The interval is in ``alpha - 1``. Its upper end must keep alpha inside
    ``(1, 2)``, the profile domain of ``meat-core/req:key-length-alpha-domain``.
    """

    #: The smallest ``alpha - 1`` evaluated.
    lower: float = 1e-5
    #: The largest ``alpha - 1`` evaluated.
    upper: float = 0.25
    #: Points of the coarse grid, log-spaced in ``alpha - 1``, ends included.
    coarse_points: int = 6
    #: Evaluations of the golden-section refinement after the grid.
    refine_steps: int = 5

    def __post_init__(self) -> None:
        """Refuse an interval or a budget that is not one."""
        for name in ("lower", "upper"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, float | int):
                raise AlphaSearchError(
                    f"alpha_search {name} is {value!r}; it is a number",
                    reason=RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN,
                )
        for name in ("coarse_points", "refine_steps"):
            value = getattr(self, name)
            if type(value) is not int:
                raise AlphaSearchError(
                    f"alpha_search {name} is {value!r}; it is an integer",
                    reason=RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN,
                )
        if not (math.isfinite(self.lower) and math.isfinite(self.upper)):
            raise AlphaSearchError(
                "the alpha - 1 interval must be finite",
                reason=RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN,
            )
        if not 0.0 < self.lower < self.upper < 1.0:
            raise AlphaSearchError(
                f"the alpha - 1 interval [{self.lower!r}, {self.upper!r}] must satisfy "
                "0 < lower < upper < 1, so that alpha stays in (1, 2)",
                reason=RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN,
            )
        if self.coarse_points < 2:
            raise AlphaSearchError(
                f"coarse_points is {self.coarse_points}; a grid needs two ends",
                reason=RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN,
            )
        if self.refine_steps < 0:
            raise AlphaSearchError(
                f"refine_steps is {self.refine_steps}",
                reason=RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN,
            )

    def coarse_grid(self) -> tuple[float, ...]:
        """Return the grid's alpha values, ascending."""
        lo, hi = math.log(self.lower), math.log(self.upper)
        last = self.coarse_points - 1
        return tuple(1.0 + math.exp(lo + (hi - lo) * i / last) for i in range(last + 1))

    def as_payload(self) -> dict[str, Any]:
        """Return the settings as JSON."""
        return {
            "lower_alpha_minus_one": self.lower,
            "upper_alpha_minus_one": self.upper,
            "coarse_points": self.coarse_points,
            "refine_steps": self.refine_steps,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> AlphaSearchSettings:
        """Return the settings a payload of :meth:`as_payload` describes.

        An absent key takes the class default, so ``{}`` is the default
        search; a key this class does not write is refused, because a
        misspelt bound silently searching the default interval would be a
        configuration that does not say what it does.
        """
        known = {"lower_alpha_minus_one", "upper_alpha_minus_one", "coarse_points",
                 "refine_steps"}
        unknown = sorted(set(payload) - known)
        if unknown:
            raise AlphaSearchError(
                f"alpha_search carries {unknown}; it reads {sorted(known)}",
                reason=RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN,
            )
        defaults = cls()
        return cls(
            lower=payload.get("lower_alpha_minus_one", defaults.lower),
            upper=payload.get("upper_alpha_minus_one", defaults.upper),
            coarse_points=payload.get("coarse_points", defaults.coarse_points),
            refine_steps=payload.get("refine_steps", defaults.refine_steps),
        )


@dataclass(frozen=True)
class RunConfig:
    """Everything one run needs that is not a callable or a filesystem path.

    Deliberately excludes the linear oracle, the provider callables and the
    output directory. Those are wiring, not configuration: they cannot be
    serialized, compared or swept over, and holding them here would make a config
    un-recordable. :func:`certiqs_key.runs.pipeline.run_slice` takes them as separate
    arguments.
    """

    #: ``n``, total channel uses. Reaches BOTH the acceptance construction and
    #: the declaration from this one field, because
    #: ``statistics/req:matched-alphabet`` requires them to agree.
    rounds: int
    #: ``eps_comp``. Buys COMPLETENESS and never soundness.
    completeness_budget: Fraction
    #: ``meat-core`` Section 2.4, verbatim.
    parameters: KeyLengthParameters
    #: ``eps_auth``, A-AUTH's error bound (``meat-core`` interface, parameters
    #: row ``eps_auth``: ``[0, 1)``, default 0): the authentication scheme's
    #: error on an ideal key plus the trace distance of the key the run uses
    #: from an ideal one (``ass:auth`` (iii)-(v)). It enters the security
    #: parameter twice and the corner gate of
    #: ``req:security-statement-not-vacuous``, never the key-length
    #: expression. A RUN INPUT AND NOT A FIELD OF ``parameters``: the engine
    #: takes it beside the declaration, as ``solve_bundle``'s keyword, so the
    #: bundle format does not move. The default is meat-core's own; the
    #: key-rate report flags a zero as an authentication error not counted.
    eps_auth: float = 0.0
    #: ``k_auth``, the pre-shared key bits the authentication scheme consumes
    #: in one run (``ass:auth`` (ii); parameters row ``k_auth``: a
    #: non-negative integer, default 0), subtracted from the key length to give
    #: ``net_key_length``. The same reason it is a run input as ``eps_auth``.
    k_auth: int = 0
    #: The instance's channel-model parameters. Never read by this package.
    model: Mapping[str, Fraction] = field(default_factory=dict)
    #: The instance's physical-device parameters. Never read by this package.
    #: A value is an exact rational; a string where the declaration it makes is
    #: a NAME rather than a quantity; or one exact rational per receiver port,
    #: keyed by the port map's own labels -- see :data:`DeviceValue` and the
    #: module docstring.
    device: Mapping[str, DeviceValue] = field(default_factory=dict)
    #: ``tau``, the one numerical tolerance this instance declares
    #: (spec/architecture.md 2.8): the **ceiling on the pre-snap defect an
    #: instance may repair**, a binary64 ``float`` in ``[0, 1)``. REQUIRED --
    #: the assignment below is a sentinel and not a default, and a config that
    #: does not declare it is refused with reason
    #: ``declared_tolerance_absent``. It is not passed to any module: the
    #: modules receive ``0`` (spec/architecture.md 2.8).
    declared_tolerance: float = NO_DECLARED_TOLERANCE
    #: The Renyi order to solve at; ``None`` takes the declared default.
    alpha: float | None = None
    #: THE OPT-IN OUTER ALPHA SEARCH: where set, an
    #: instance's runner runs the configuration once per searched alpha and
    #: returns the best run with the search attached
    #: (:func:`certiqs_key.runs.alpha_search.searching_runner`). ``None``, the
    #: default, solves at :attr:`alpha` or the declared one. Setting both is
    #: refused (``alpha_and_alpha_search_both_set``): a fixed order and a
    #: search for one are two different requests.
    alpha_search: AlphaSearchSettings | None = None
    #: Which acceptance outcomes the acceptance set constrains. ``None`` is the
    #: declared default and is distinct from ``()``, an admissible selector in
    #: its own right.
    constrained: tuple[str, ...] | None = None
    #: The solver budget. ``None`` is the solver's own defaults and is
    #: not a pair of numbers this tier wrote down; see :class:`SolverSettings`.
    solver: SolverSettings | None = None
    #: ``statistics``' ``endpoint_rule`` request field, forwarded to
    #: :class:`~certiqs_key.statistics.AcceptanceRequest` and recorded in the
    #: ``honest_model`` record that module emits. The default is that module's
    #: own (``exact``); the
    #: other admissible value is ``bernstein``. IT IS HERE BECAUSE A SWEEP MAY
    #: VARY IT: the interface names it a request field, and a sweep over ``n``
    #: that could not switch rules would be a sweep the interface admits and
    #: this tier does not.
    endpoint_rule: str = str(EndpointRuleName.EXACT)
    #: ``statistics``' ``tail_evaluation`` request field, the same way. The
    #: default is ``sweep``, the exact rule's running-sum evaluation and the
    #: parity route; ``enclosure`` is the local Stirling-and-geometric route
    #: that large ``n`` needs.
    tail_evaluation: str = str(TailEvaluation.SWEEP)
    #: Declaring-boundary numerical preparation, absent on unchanged old inputs.
    input_preparation: tuple[Mapping[str, Any], ...] = ()
    #: THE TWO SNAP PARAMETERS (``foundations/req:snap-reference`` (i), (iv);
    #: spec/architecture.md 2.8, "What is not a switch"). They reach the
    #: receiver construction, the instance's snap of its receiver family
    #: (:class:`~certiqs_key.foundations.snap.SnapSettings`) and the reduction
    #: request. The record's ``parameters`` block writes both always; the
    #: configuration's payload, and so its digest, writes each where it is not
    #: its default (:func:`parameters_payload`).
    #:
    #: ``reference_enclosure``: whether enclosed references are used. Off, the
    #: instance hands only the blocks of its reference known exactly, so the
    #: reference companion carries the snapped block on the others, which rest
    #: on A-SNAP in the group ``no usable reference``, which the run output
    #: documents and traces.
    reference_enclosure: bool = True
    #: The strict option: whether a run refuses wherever a moved block would
    #: rest on A-SNAP, rather than disclosing it
    #: (``foundations/req:snap-reference`` (iv)). Off by default; no other
    #: option conditions it.
    strict_snaps: bool = False
    #: THE CHECK OF THE ACCEPTANCE SET AGAINST THE FEASIBLE STATISTICS
    #: (``meat-core/req:unreachable-acceptance-set``; record schema 0.37.0).
    #: ``statistics_check``: ``on`` (default) checks a run whose honest
    #: statistics are supplied as numbers or whose declaration carries a
    #: constraint entry the caller declared; ``off`` opts such a run out, and
    #: its record names A-REACH as unchecked. ``min_model_pass_probability``,
    #: ``tau`` in ``(0, 1]`` (default ``1/2``, exact): a checked run whose cap
    #: on the probability that devices as declared pass the acceptance test is
    #: at most ``tau`` is refused as a whole (record schema 0.46.0). Written
    #: into the configuration's payload, and so its digest, only where not
    #: their default, as the snap parameters are.
    statistics_check: str = "on"
    min_model_pass_probability: Fraction = Fraction(1, 2)

    @classmethod
    def from_inputs(
        cls, *, numeric_device_fields: tuple[str, ...] = (), **inputs: Any
    ) -> RunConfig:
        """Prepare ordinary numerical inputs, recording every conversion.

        Instance surfaces call this constructor. ``RunConfig`` itself remains
        the typed prepared configuration, preserving its existing validation.
        """
        from certiqs_key.runs.inputs import prepare_config_inputs

        return cls(
            **prepare_config_inputs(inputs, numeric_device_fields=numeric_device_fields)
        )

    def __post_init__(self) -> None:
        """Refuse a configuration that does not declare a usable ``tau``.

        Three refusals, each with its own reason code, because they call for
        three different corrections. Nothing is substituted in any of them:
        spec/architecture.md 2.8 says a defaulted ceiling on repair "decides a
        security-relevant act on nobody's authority", and a coerced one decides
        it just as much.

        Raises:
            RunConfigError: with ``reason`` one of
                ``declared_tolerance_absent`` (nothing was declared),
                ``declared_tolerance_not_binary64`` (something was declared
                that is not a ``float`` -- an ``int``, a ``Fraction``, a
                ``bool``, a string), or ``declared_tolerance_out_of_domain``
                (a ``float`` outside ``[0, 1)``, NaN included).
        """
        tolerance = self.declared_tolerance
        if tolerance is NO_DECLARED_TOLERANCE:
            raise RunConfigError(
                "this run declares no numerical tolerance. "
                "spec/architecture.md 2.8: 'tau itself has no default and no "
                "fallback: a run whose configuration does not declare it is "
                "refused, because a defaulted ceiling on repair decides a "
                "security-relevant act on nobody's authority'. Pass "
                "declared_tolerance explicitly; 0.0 is how a run declares the "
                "exact reading",
                reason=RunInputReason.DECLARED_TOLERANCE_ABSENT,
            )
        # bool is a subclass of int and neither is a float; both are refused by
        # the same test, and the message says which was passed.
        if type(tolerance) is not float:
            raise RunConfigError(
                f"declared_tolerance is {tolerance!r}, a "
                f"{type(tolerance).__name__}. The engine is binary64 end to "
                "end (spec/architecture.md 2.8) and a declared value IS its "
                "binary64 datum, so this number is a float and is not widened "
                "from one: pass 0.0 rather than 0, and a float rather than a "
                "Fraction",
                reason=RunInputReason.DECLARED_TOLERANCE_NOT_BINARY64,
            )
        self._check_statistics_request()
        self._check_alpha_search()
        self._check_authentication_parameters()
        self._check_snap_settings()
        self._check_statistics_check()
        if math.isnan(tolerance) or not 0.0 <= tolerance < 1.0:
            raise RunConfigError(
                f"declared_tolerance is {tolerance!r}, outside [0, 1). "
                "spec/architecture.md 2.8 fixes that interval repo-wide and "
                "derives its upper limit: 'at tau >= 1 a completeness "
                "condition is satisfied by the all-zero family, whose residue "
                "against the identity is exactly one on every block, so the "
                "admission rule would stop constraining the family at all'. A "
                "module may narrow it further and states its reason; nothing "
                "may widen it",
                reason=RunInputReason.DECLARED_TOLERANCE_OUT_OF_DOMAIN,
            )

    def _check_statistics_request(self) -> None:
        """Refuse a rule or an evaluation ``statistics`` does not admit.

        DECIDED HERE AS WELL AS THERE, and that is the ``decide_never_infer``
        convention rather than a duplicated rule: the supplier refuses an
        unknown value with its own machine-readable code, and a configuration
        that could hold one would be a RECORD of a run that cannot happen --
        swept over, serialized, digested and compared, all before the module
        that owns the vocabulary ever sees it. The values are read from that
        module's own enums, so the two cannot drift.
        """
        rules = {str(name) for name in EndpointRuleName}
        if self.endpoint_rule not in rules:
            raise RunConfigError(
                f"endpoint_rule is {self.endpoint_rule!r}; statistics admits "
                f"{sorted(rules)} (binomial-box/def:endpoint-rule)",
                reason=RunInputReason.ENDPOINT_RULE_NOT_ADMITTED,
            )
        evaluations = {str(name) for name in TailEvaluation}
        if self.tail_evaluation not in evaluations:
            raise RunConfigError(
                f"tail_evaluation is {self.tail_evaluation!r}; statistics "
                f"admits {sorted(evaluations)}",
                reason=RunInputReason.TAIL_EVALUATION_NOT_ADMITTED,
            )

    def _check_alpha_search(self) -> None:
        """Refuse a search that is not one, and a search beside a fixed ``alpha``.

        ``alpha`` says "solve at this order"; ``alpha_search`` says "choose the
        order". A configuration holding both would be a record of two requests
        at once, and which one ran would be this tier's guess.
        """
        search = self.alpha_search
        if search is None:
            return
        if not isinstance(search, AlphaSearchSettings):
            raise AlphaSearchError(
                f"alpha_search is {search!r}, a {type(search).__name__}; it is an "
                "AlphaSearchSettings (or its payload through RunConfig.from_payload)",
                reason=RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN,
            )
        if self.alpha is not None:
            raise RunConfigError(
                f"this configuration sets alpha = {self.alpha!r} and an alpha "
                "search; set one: alpha fixes the order a run solves at, "
                "alpha_search chooses it",
                reason=RunInputReason.ALPHA_AND_ALPHA_SEARCH_BOTH_SET,
            )

    def _check_authentication_parameters(self) -> None:
        """Refuse an ``eps_auth`` or ``k_auth`` outside its declared domain.

        DECIDED BY ``meat-core``'s OWN CHECK
        (:func:`~certiqs_key.meat_core.finitekey.keylength.check_authentication_parameters`),
        here as well as at the solve, for the reason
        :meth:`_check_statistics_request` gives: a configuration that could
        hold such a value would be a record of a run that cannot happen. The
        joint condition ``eps_pa + eps_ev + 2 eps_auth < 1`` is not decided
        here: it is the engine's corner gate, and a run that meets it is
        recorded as a refusal with the engine's own reason
        (``security_statement_vacuous``).
        """
        if type(self.eps_auth) not in (float, int):
            raise RunConfigError(
                f"eps_auth is {self.eps_auth!r}, a {type(self.eps_auth).__name__}; "
                "it is a binary64 number (RunConfig.from_inputs converts an exact "
                "input and records the conversion)",
                reason=RunInputReason.AUTHENTICATION_PARAMETER_OUT_OF_DOMAIN,
            )
        try:
            check_authentication_parameters(self.eps_auth, self.k_auth)
        except ValueError as failure:
            raise RunConfigError(
                str(failure),
                reason=RunInputReason.AUTHENTICATION_PARAMETER_OUT_OF_DOMAIN,
            ) from failure

    def _check_snap_settings(self) -> None:
        """Refuse a snap parameter that is not a boolean.

        Decided here as well as at the snap, for the reason
        :meth:`_check_statistics_request` gives: a configuration that could
        hold such a value would be a record of a run that cannot happen.
        """
        for name in ("reference_enclosure", "strict_snaps"):
            value = getattr(self, name)
            if type(value) is not bool:
                raise RunConfigError(
                    f"{name} is {value!r}, a {type(value).__name__}; it is a "
                    "boolean",
                    reason=RunInputReason.SNAP_SETTING_OUT_OF_DOMAIN,
                )

    def _check_statistics_check(self) -> None:
        """Refuse ``statistics_check`` or ``min_model_pass_probability`` off domain.

        ``meat-core/req:unreachable-acceptance-set``: the option is ``on`` or
        ``off``, and ``tau`` lies in ``(0, 1]``. ``tau`` is an exact rational
        (:meth:`from_inputs` converts a binary64 input exactly and records
        the conversion), so the comparison of item (iv) is made on it.
        """
        if self.statistics_check not in ("on", "off"):
            raise RunConfigError(
                f"statistics_check is {self.statistics_check!r}; admitted: on, off",
                reason=RunInputReason.STATISTICS_CHECK_SETTING_OUT_OF_DOMAIN,
            )
        tau = self.min_model_pass_probability
        if type(tau) is not Fraction or not 0 < tau <= 1:
            raise RunConfigError(
                f"min_model_pass_probability is {tau!r}; it is an exact rational "
                "in (0, 1] (RunConfig.from_inputs converts a number and records "
                "it)",
                reason=RunInputReason.STATISTICS_CHECK_SETTING_OUT_OF_DOMAIN,
            )

    def to_payload(self) -> dict[str, Any]:
        """Return this configuration as JSON, invertible by :meth:`from_payload`.

        spec/architecture.md 2.6 is why: "a run is reproducible from its
        bundle", so the configuration is serialized and read back. A caller can
        re-run a record's configuration, submit one as JSON, and recognise two
        identical requests.

        THE HOUSE CONVENTIONS, AND NEITHER IS NEW HERE. An exact rational is a
        ``"p/q"`` string and never a float, because a float would discard the
        exactness the acceptance construction requires of every number it is
        given; and ``declared_tolerance`` is a JSON number, because it IS its
        binary64 datum (spec/architecture.md 2.8) -- with the ABSENCE spelled
        out, as :data:`NO_DECLARED_TOLERANCE`'s own key, so that a payload can
        describe the one configuration this class refuses to construct and the
        refusal happens on the way back in rather than being lost.

        ``device`` values are :data:`DeviceValue` and the three forms are
        distinguished on the way out, because each widening is deliberate: a
        route name is a NAME and a rendered ``"p/q"`` of it would be a number
        nobody declared, and a per-port mapping is a JSON OBJECT of ``"p/q"``
        strings keyed by the port labels rather than a flattened list, so that
        the record says which detector each number belongs to.

        ``eps_auth`` and ``k_auth`` are written into the ``parameters`` block
        beside the four key-length parameters where they are not 0 (record
        schema 0.20.0; :func:`parameters_payload`), so a configuration that
        declares neither digests as it did before they existed.
        """
        payload = {
            "rounds": self.rounds,
            "completeness_budget": str(self.completeness_budget),
            "parameters": parameters_payload(self, defaults=False),
            "model": {key: str(value) for key, value in self.model.items()},
            "device": {key: _device_wire(value) for key, value in self.device.items()},
            "declared_tolerance": (
                None
                if self.declared_tolerance is NO_DECLARED_TOLERANCE
                else self.declared_tolerance
            ),
            "alpha": self.alpha,
            "constrained": (
                None if self.constrained is None else list(self.constrained)
            ),
            "solver": None if self.solver is None else self.solver.as_payload(),
            "endpoint_rule": self.endpoint_rule,
            "tail_evaluation": self.tail_evaluation,
        }
        numeric_names = [
            name
            for name, value in self.device.items()
            if isinstance(value, str) and _is_rational(value)
        ]
        if numeric_names:
            # Only ambiguous name spellings need this discriminator; old
            # payloads with ordinary route names retain their exact shape.
            payload["device_name_fields"] = numeric_names
        if self.alpha_search is not None:
            # WRITTEN ONLY WHEN SET (record schema 0.24.0), so a configuration
            # without the opt-in search keeps the payload -- and the digest --
            # it had before the search existed.
            payload["alpha_search"] = self.alpha_search.as_payload()
        if self.input_preparation:
            payload["input_preparation"] = list(self.input_preparation)
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> RunConfig:
        """Return the configuration a payload of :meth:`to_payload` describes.

        THE EXACT INVERSE, and the property test says so:
        ``from_payload(to_payload(c)) == c`` for every configuration this class
        can construct. A ``device`` value that is not a ``"p/q"`` string stays a
        string, which is the widening ``model`` deliberately does not have.

        A payload whose ``declared_tolerance`` is ``null`` describes the
        configuration that declares none, and reconstructing it raises
        :class:`RunConfigError` with ``declared_tolerance_absent`` -- the same
        refusal the constructor gives, at the same place. That is the point of
        spelling the absence rather than omitting the key: a payload can say
        "this run declared no tolerance", and reading it back says so too.
        """
        _refuse_retired_parameters(payload)
        parameters = payload["parameters"]
        solver = payload.get("solver")
        tolerance = payload.get("declared_tolerance")
        search = payload.get("alpha_search")
        return cls.from_inputs(
            rounds=int(payload["rounds"]),
            completeness_budget=(
                payload["completeness_budget"]
                if isinstance(payload["completeness_budget"], float)
                else Fraction(payload["completeness_budget"])
            ),
            parameters=KeyLengthParameters(
                alpha=float(parameters["alpha"]),
                eps_pa=float(parameters["eps_pa"]),
                eps_ev=float(parameters["eps_ev"]),
                lambda_ec=parameters["lambda_ec"],
            ),
            eps_auth=float(parameters.get("eps_auth", 0.0)),
            k_auth=parameters.get("k_auth", 0),
            reference_enclosure=parameters.get("reference_enclosure", True),
            strict_snaps=parameters.get("strict_snaps", False),
            statistics_check=parameters.get("statistics_check", "on"),
            min_model_pass_probability=_rational(
                parameters.get("min_model_pass_probability", Fraction(1, 2))
            ),
            model={
                key: value if isinstance(value, float) else Fraction(value)
                for key, value in payload.get("model", {}).items()
            },
            device={
                key: value
                if key in payload.get("device_name_fields", ())
                else _device_value(value)
                for key, value in payload.get("device", {}).items()
            },
            declared_tolerance=(
                NO_DECLARED_TOLERANCE if tolerance is None else float(tolerance)
            ),
            alpha=None if payload.get("alpha") is None else float(payload["alpha"]),
            alpha_search=(
                None if search is None else AlphaSearchSettings.from_payload(search)
            ),
            constrained=(
                None
                if payload.get("constrained") is None
                else tuple(payload["constrained"])
            ),
            solver=None if solver is None else SolverSettings.from_payload(solver),
            endpoint_rule=str(payload.get("endpoint_rule", EndpointRuleName.EXACT)),
            tail_evaluation=str(payload.get("tail_evaluation", TailEvaluation.SWEEP)),
            input_preparation=tuple(payload.get("input_preparation", ())),
        )

    def digest(self) -> str:
        """Return the content digest of this configuration: sha256 of its JSON.

        ``config_digest(config)``: sha256 of the canonical JSON (sorted keys,
        no whitespace) of ``to_payload``, recorded in the run record. It is
        what any caller's cache keys on, what a log line uses as a run id, and
        what a consumer compares to recognise two identical requests.

        NO STORE AND NO CACHE IN THE ENGINE. spec/architecture.md 2.6 is
        explicit that "content-addressing and a provenance envelope earn their
        cost once more than one producer exists; until then the platform needs a
        FILE FORMAT, not a store", and this is a function of a value rather than
        an index of anything. It is also NOT the envelope's deferred
        ``content_hash`` (spec/future-scope.md section 1), which is about an
        ARTEFACT and is still deferred; this hashes a request.
        """
        return config_digest(self)

    def with_(self, **changes: object) -> RunConfig:
        """Return a copy with ``changes`` applied -- the sweep axis primitive.

        A thin :func:`dataclasses.replace`, named so that a sweep reads as a
        sequence of derived configs rather than as reconstruction from parts.
        Every refusal of :meth:`__post_init__` is re-decided on the copy, so a
        sweep axis cannot walk a config out of ``[0, 1)``.
        """
        if "input_preparation" not in changes:
            # An overwritten section no longer denotes the recorded inputs.
            # In particular a newly supplied exact Fraction must not inherit
            # an earlier float's rounding-cell allowance at the same value.
            changes["input_preparation"] = tuple(
                row
                for row in self.input_preparation
                if not any(
                    row.get("site", "") == key
                    or row.get("site", "").startswith(key + ".")
                    for key in changes
                )
            )
        return replace(self, **changes)  # type: ignore[arg-type]


#: Run parameters the engine no longer has, each with what replaced it
#: (``None``: nothing). A payload naming one is refused with
#: ``retired_parameter`` rather than read as if the key were absent: a caller
#: asking for certified snaps would otherwise get the default silently.
RETIRED_PARAMETERS: Final[Mapping[str, str | None]] = {
    "certify_snaps": None,
    "certified_weight_ceiling": None,
    "strict_certification": "strict_snaps",
    "contradiction_share": "min_model_pass_probability",
}
#: What a retired parameter's refusal says where its replacement is no
#: rename: the share of the key length gave way to a threshold on the cap
#: (``meat-core/req:unreachable-acceptance-set`` (iv), record schema 0.46.0).
_RETIRED_NOTES: Final[Mapping[str, str]] = {
    "contradiction_share": (
        "the one-percent share of the key length is no longer a refusal rule; "
        "a checked run is refused where the cap on the probability that "
        "devices as declared pass the acceptance test is at most "
        "min_model_pass_probability (default 1/2)"
    ),
}


def _refuse_retired_parameters(payload: Mapping[str, Any]) -> None:
    """Refuse a payload naming a retired run parameter (top level or ``parameters``).

    Raises:
        RunConfigError: with reason ``retired_parameter``, naming the key and
            its replacement where it has one.
    """
    blocks: list[tuple[str, Mapping[str, Any]]] = [("", payload)]
    parameters = payload.get("parameters")
    if isinstance(parameters, Mapping):
        blocks.append(("parameters.", parameters))
    for prefix, block in blocks:
        for name, replacement in RETIRED_PARAMETERS.items():
            if name not in block:
                continue
            what = (
                f"it is now {prefix}{replacement}"
                if replacement is not None
                else "snaps are no longer certified; a run evaluates its "
                "first-order bound on the reference companion instead "
                "(meat-core/frank-wolfe/req:bracket-on-reference)"
            )
            raise RunConfigError(
                f"{prefix}{name} is a retired run parameter: "
                + _RETIRED_NOTES.get(name, what),
                reason=RunInputReason.RETIRED_PARAMETER,
            )


def _rational(value: Any) -> Any:
    """Return a payload's ``min_model_pass_probability``: ``"p/q"`` read exactly.

    The payload writes the exact rational as ``"p/q"``, which is read back
    here so that the round trip records no conversion; any other value goes
    to :meth:`RunConfig.from_inputs`, which converts a number exactly and
    records it, or refuses what is not one.
    """
    if isinstance(value, str):
        try:
            return Fraction(value)
        except ValueError:
            return value
    return value


def _device_wire(value: DeviceValue) -> Any:
    """Render one ``device`` value as JSON, in the house conventions.

    A per-port mapping stays a MAPPING on the wire -- an object keyed by the
    receiver's port labels -- because the labels are the datum. Flattening it
    to a list would record the ports by position, which is the fixed count the
    per-port kind exists to avoid, and a reader would have to know the port
    order to say which detector a number belonged to.
    """
    if isinstance(value, Mapping):
        return {str(port): str(entry) for port, entry in value.items()}
    return str(value) if isinstance(value, Fraction) else value


def _device_value(value: Any) -> DeviceValue:
    """Return the ``device`` value a payload entry describes: the exact inverse.

    An object is a per-port mapping and its entries are exact rationals: a
    device key whose value is an object has kind ``per_port_fraction`` in the
    instance's table, and that kind admits nothing else, so there is no second
    reading to choose between here.
    """
    if isinstance(value, Mapping):
        return {str(port): Fraction(entry) for port, entry in value.items()}
    return Fraction(value) if _is_rational(value) else cast(str, value)


def _is_rational(value: object) -> bool:
    """Whether a device payload value is a rendered exact rational.

    The ``device`` mapping carries ``Fraction | str`` and the round trip has to
    put each back where it came from. A rendered rational is what
    :class:`~fractions.Fraction` accepts and a route name is not: ``"1/2"`` and
    ``"3"`` are rationals, ``"licensed+two-sector"`` is a name. The test is the
    constructor's own, so no second grammar is invented here.
    """
    if not isinstance(value, str):
        return False
    try:
        Fraction(value)
    except ValueError:
        return False
    return True


def parameters_payload(config: RunConfig, *, defaults: bool = True) -> dict[str, Any]:
    """Return the ``parameters`` block of a configuration's payload and record.

    The four key-length parameters of ``meat-core`` Section 2.4 and A-AUTH's
    two (record schema 0.20.0), as JSON numbers: the floats are their binary64
    data and the two bit counts integers. ONE WRITER for the configuration's
    payload and the run record's ``config``, so that the two blocks cannot
    disagree about which numbers the security statement was made with.

    ``defaults=False`` is the configuration's own payload: A-AUTH's two are
    written there only when they are not meat-core's default 0, as
    :meth:`SolverSettings.as_payload` writes its later fields only when
    chosen, so a configuration that declares neither keeps the payload -- and
    the digest -- it had before they existed. The run record writes both
    always (``defaults=True``): a reader of a record sees the zero it was
    computed with, which the key-rate report flags as not counted.
    """
    payload: dict[str, Any] = {
        "alpha": config.parameters.alpha,
        "eps_pa": config.parameters.eps_pa,
        "eps_ev": config.parameters.eps_ev,
        "lambda_ec": config.parameters.lambda_ec,
    }
    if defaults or config.eps_auth != 0:
        payload["eps_auth"] = config.eps_auth
    if defaults or config.k_auth != 0:
        payload["k_auth"] = config.k_auth
    # THE SNAP PARAMETERS, by the same rule as A-AUTH's two: the record
    # writes both always, and the configuration's payload -- so its digest --
    # writes each where it is not its default, so a configuration that
    # chooses neither keeps the digest it had.
    if defaults or config.reference_enclosure is not True:
        payload["reference_enclosure"] = config.reference_enclosure
    if defaults or config.strict_snaps is not False:
        payload["strict_snaps"] = config.strict_snaps
    # THE STATISTICS CHECK (meat-core/req:unreachable-acceptance-set; record
    # schema 0.37.0), by the same rule: the record writes both always, the
    # configuration's payload each where it is not its default. tau is an
    # exact rational, written "p/q".
    if defaults or config.statistics_check != "on":
        payload["statistics_check"] = config.statistics_check
    if defaults or config.min_model_pass_probability != Fraction(1, 2):
        payload["min_model_pass_probability"] = str(
            config.min_model_pass_probability
        )
    return payload


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Return the canonical JSON of a payload: sorted keys, no whitespace.

    ONE CANONICALISATION FOR THE WHOLE RUN TIER. The configuration digest and
    the artefact digests of the stage list are the same function of the same
    shape, and two spellings of "canonical" would give two digests of one
    object.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def config_digest(config: RunConfig) -> str:
    """Return ``sha256`` of the canonical JSON of ``config.to_payload()``.

    A warm-start seed enters BY ITS HASH ONLY: its ``file`` locator is removed
    before hashing (:class:`WarmStartSeed`). Every other key is hashed as
    written, so a configuration without a seed digests as it always did.
    """
    payload = config.to_payload()
    solver = payload.get("solver")
    if isinstance(solver, dict):
        advanced = solver.get("advanced")
        if isinstance(advanced, dict) and isinstance(advanced.get("warm_start"), dict):
            seed = dict(advanced["warm_start"])
            seed.pop("file", None)
            payload["solver"] = {
                **solver,
                "advanced": {**advanced, "warm_start": seed},
            }
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()
