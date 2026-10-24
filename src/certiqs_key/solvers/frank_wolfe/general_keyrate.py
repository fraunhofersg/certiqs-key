"""The result record of every run: the joint driver's numbers, gated, assembled.

EVERY DECLARATION ENDS HERE (one driver): an accepted-format
declaration arrives embedded as the degenerate general declaration it is
(:func:`certiqs_key.solvers.frank_wolfe.keyrate.solve`), so this record is the
one record a run writes. The general rows are licensed by def:homog in either
source mode. Their supplier's A-ATK attestation remains mandatory; no numeric
row check supplies it. The dropped bound retains its own name through the
result and the gate.

THE KEY LENGTH IS ``cor:fo-keylength``: the core's ``cor:keylength-bound`` at
``h = h_lb`` (:func:`key_length_from_first_order`), from the bracket of
``thm:firstorder`` and nothing else; ``h_low`` is a convergence diagnostic and
no length is computed from it. On a run reported at the certified tier it is
``cor:certified-keylength`` at the certified number instead, computed exactly
(``req:certified-evaluation`` (vi)), and ``h_lb`` is recorded beside it.

AND IT IS REPORTED ONLY ON A COMPILED DECLARATION
(``meat-core/req:compiled-declaration-only``): :func:`solve_general` takes
``compiled``, the run tier's in-memory token that the protocol compiler emitted
the declaration (:class:`~certiqs_key.meat_core.provenance.CompilerEmission`),
and without it withholds the length with a reason opening
``declaration_not_compiled``. The bound, the estimate and everything else are
reported as before.

THE CLAIM ROOTS AND THE LEDGER FOLLOW WHAT IS REPORTED:
the certificate names the first-order root whenever a bound is reported
(:func:`result_claim_roots`), and the ledger emits the rows of those roots'
closures; beside each row, the declared values it binds
(:func:`declared_values`,
:func:`certiqs_key.meat_core.reasons.assumption_bindings`).
"""

from __future__ import annotations

import math
import time
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, replace
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np

from certiqs_key.domain.bindings import LedgerBindings
from certiqs_key.domain.claim_closure import (
    CERTIFIED_REFERENCE_ROOT,
    CERTIFIED_ROOT,
    DROPPED_ROOT,
    ESTIMATE_ROOT,
    FIRST_ORDER_ROOT,
    KEY_LENGTH_ROOT,
    REFERENCE_ROOT,
    module_version,
)
from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.declaration.companion import (
    AdmittedCompanion,
    admit_reference_companion,
)
from certiqs_key.meat_core.declaration.declaration import (
    SourceMode,
)
from certiqs_key.meat_core.declaration.general import GeneralDeclaration, GeneralRhsTag
from certiqs_key.meat_core.declaration.general_sectors import general_sector_report
from certiqs_key.meat_core.declaration.validation import (
    MATHEMATICAL_SPEC_VERSION,
)
from certiqs_key.meat_core.errors import (
    CertificationRefusedError,
    MeatError,
    SecurityGateError,
)
from certiqs_key.meat_core.finitekey.keylength import (
    certified_key_length,
    check_authentication_parameters,
    composed_security,
    declaration_provenance_failure,
    key_length_from_bound,
)
from certiqs_key.meat_core.finitekey.result import deductions_of
from certiqs_key.meat_core.objective.joint import (
    JointMaps,
    JointSector,
    evaluate_joint_branches,
    joint_statistics,
)
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.meat_core.objective.support import support_band_report
from certiqs_key.meat_core.provenance import CompilerEmission
from certiqs_key.meat_core.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    DECLARATION_NOT_COMPILED,
    INHERITED_KEYS,
    REASON_TEXT,
    AssuranceReason,
    RefusalReason,
    assumption_bindings,
    assumption_ledger,
    laboratory_parties,
)
from certiqs_key.solvers.capabilities.probe import probe_environment
from certiqs_key.solvers.frank_wolfe.certified_record import (
    CERTIFIER_UNAVAILABLE,
    EVALUATION_OFF,
    FACTOR_ENCLOSURE_INCONSISTENT,
    ON_REFERENCE_COMPANION,
    ON_SEARCHED,
    CertifiedEvaluation,
)
from certiqs_key.solvers.frank_wolfe.driver import ACCUMULATION_RULE, FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    IterateObserver,
    JointFrankWolfeResult,
)
from certiqs_key.solvers.frank_wolfe.joint_options import (
    constraint_rows_digest,
    iterate_layout,
    joint_choices,
)
from certiqs_key.solvers.frank_wolfe.reference import (
    REFERENCE_POLISH_SHARE,
    ReferenceBracket,
    bracket_on_reference,
    reference_record,
)
from certiqs_key.solvers.oracles.acceptance import (
    AcceptanceOracle,
)
from certiqs_key.solvers.oracles.protocol import LinearOracle
from certiqs_key.solvers.problem import _prepare_general as _prepare_general
from certiqs_key.solvers.types import SearchRequest

if TYPE_CHECKING:
    from certiqs_key.protocol_compiler.companion import CompiledReferenceCompanion


@dataclass(frozen=True)
class GeneralKeyRateResult:
    """A serializable general-format result, with separately named bounds."""

    alpha: float
    rounds: int
    h_low: float
    h_lb: float | None
    h_lb_dropped: float | None
    dropped_set: tuple[tuple[str, JointSector], ...]
    key_length: int | None
    #: ``eps_PA + eps_EV + 2 eps_auth`` of ``cor:composed-security`` (iii),
    #: at or above the exact sum; present exactly when ``key_length`` is
    #: (the interface's ``security_parameter`` output row).
    security_parameter: float | None
    #: ``key_length - k_auth``, unclamped; present exactly when
    #: ``key_length`` is (the interface's ``net_key_length`` output row).
    net_key_length: int | None
    key_length_reason: str
    #: The code ``key_length_reason`` opens with, one of
    #: :data:`KEY_LENGTH_REASON_CODES` (so a consumer need not read it off the
    #: prose with a regular expression). ``first_order_reported``
    #: exactly when a key length is reported.
    key_length_reason_code: str
    reported_tier: Assurance
    first_order_clamped: bool
    optimized_q: Mapping[str, float]
    predicted_statistics: Mapping[str, float]
    block_contributions: Mapping[str, Mapping[str, float]]
    sector_weight_report: Mapping[str, Any]
    certificate: Mapping[str, Any]
    sector_report: Mapping[str, Any]
    map_validation_report: Mapping[str, Any]
    #: One machine key per emitted row, in the ledger's order: A-LAB's key
    #: once per party it is emitted at (meat-core/ass:lab).
    assumption_ledger: tuple[str, ...]
    #: The short ids of the rows, each ONCE, in first-row order: a set of
    #: assumptions, not a list of rows.
    assumption_ids: tuple[str, ...]
    #: Beside each row of ``assumption_ledger``, in its order, the declared
    #: values the row's assumption is about
    #: (:func:`certiqs_key.meat_core.reasons.assumption_bindings`).
    #: NOT IN THE RUN RECORD'S ``key_rate`` (:meth:`as_payload`): the run
    #: tier joins them into the route-exact set
    #: (:func:`certiqs_key.runs.assumptions.emitted_rows`), which the record
    #: carries.
    assumption_bindings: LedgerBindings
    deductions: Mapping[str, float]
    #: The declaration's provenance count, carried into the record's key-rate
    #: payload. It decides no ledger row (A-SOUND is no row) and no number.
    constraint_entries_through_a_reductions_chain: int
    #: Whether the point ``h_low`` is the objective at is ESTABLISHED in the
    #: relaxed set ``rem:fo-returned-point`` rests the estimate on: positivity
    #: at exactly ``0``, the coupling and the declared rows each inside its
    #: window (rule (3)), measured once on the returned point. ``False`` says
    #: the estimate's premise was not established at that point; it changes
    #: no bound, tier or length. The measurement is in
    #: ``certificate["group_b_worst"]`` under ``returned_point``.
    estimate_point_relaxed_member: bool
    search_report: Mapping[str, Any] = field(default_factory=dict)
    mathematical_spec_version: str = MATHEMATICAL_SPEC_VERSION
    #: THE RUN'S FINAL ITERATE ``J``, so that a caller can persist it as the
    #: seed of a warm start (:mod:`certiqs_key.runs.iterate_file`). NOT PART OF
    #: THE PAYLOAD: a record references the persisted file by content hash and
    #: never inlines the matrices.
    final_iterate: Mapping[JointSector, Matrix] | None = field(
        default=None, repr=False, compare=False
    )
    #: How each block of ``final_iterate`` splits (``joint_options.iterate_layout``),
    #: persisted with it so a warm start can compare more than block sizes.
    final_iterate_layout: Mapping[str, Any] | None = field(
        default=None, repr=False, compare=False
    )
    #: The producing declaration's ``constraint_rows_digest``, persisted with
    #: the iterate so that a warm start across points with rows can compare
    #: the rows and not only their count.
    final_iterate_rows_sha256: str | None = field(
        default=None, repr=False, compare=False
    )
    #: THE BRACKET ON THE REFERENCE COMPANION (frank-wolfe ``reference_bracket``;
    #: ``req:bracket-on-reference`` (vi)), on a run handed a compiled reference
    #: companion; ``None`` on every other run. Where ``counted``, ``h_lb`` above
    #: IS the bound on the companion and the key length is formed from it;
    #: ``snapped`` holds the bound on the searched declaration and the key
    #: length it would give, a diagnostic from which no length is reported.
    reference_bracket: Mapping[str, Any] | None = None
    #: THE CERTIFIED EVALUATION (frank-wolfe ``certified_evaluation.record``;
    #: ``req:certified-evaluation`` (ix)) on a run that forms a first-order
    #: number; ``None`` on every other run. Where its ``status`` is
    #: ``certified`` the key length is formed from ``certified_bound`` and the
    #: tier is ``certified``; ``h_lb`` stays the first-order number.
    certified: Mapping[str, Any] | None = None
    #: THE CERTIFIED NUMBER EXACTLY, ``h^cert`` as the evaluation formed it,
    #: where a point was certified; ``None`` otherwise. ``certified`` records
    #: it rounded toward ``-inf``. NOT PART OF THE PAYLOAD: read in memory by
    #: the run tier, which forms case (b)'s comparison length from the number
    #: certified on the searched declaration in the fallback
    #: (``meat-core/req:unreachable-acceptance-set`` (iv)(b)); no key length of
    #: the run reads it.
    certified_exact: Fraction | None = field(
        default=None, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Reject a tier or bound name unsupported by this record."""
        if tuple(key for key, _ in self.assumption_bindings) != self.assumption_ledger:
            raise ValueError(
                "assumption_bindings carries one entry per assumption_ledger row, "
                "in its order"
            )
        if self.key_length_reason_code not in KEY_LENGTH_REASON_CODES:
            raise ValueError(
                f"key_length_reason_code {self.key_length_reason_code!r} is not "
                "one of KEY_LENGTH_REASON_CODES"
            )
        if (self.key_length_reason_code in REPORTED_REASONS) != (
            self.key_length is not None
        ):
            raise ValueError(
                f"key_length_reason_code is one of {sorted(REPORTED_REASONS)} "
                "exactly when a key length is reported"
            )
        bound = self.h_lb_dropped if self.dropped_set else self.h_lb
        if (self.h_lb is not None and self.dropped_set) or (
            self.h_lb_dropped is not None and not self.dropped_set
        ):
            raise ValueError("the bound name must match the declared dropped set")
        first = self.reported_tier in (Assurance.FIRST_ORDER, Assurance.CERTIFIED)
        if (self.reported_tier is Assurance.CERTIFIED) != (
            self.key_length_reason_code == CERTIFIED_REASON
        ):
            raise ValueError("the certified tier is reported with its own reason code")
        if first != (bound is not None and self.key_length is not None):
            raise ValueError(
                "first-order requires a lower bound and its emitted length"
            )
        if self.key_length is not None and not first:
            raise ValueError("an estimate cannot emit a key length")
        # THE COMPOSED STATEMENT TRAVELS WITH THE LENGTH AND ONLY WITH IT: both
        # output rows read "emitted exactly when `key_length` is", because the
        # engine's key_length is the case in which both parties output a key
        # (cor:composed-security (iii)).
        if (self.security_parameter is None) != (self.key_length is None) or (
            self.net_key_length is None
        ) != (self.key_length is None):
            raise ValueError(
                "security_parameter and net_key_length are emitted exactly when "
                "key_length is"
            )
        # THE LABEL WITHOUT ITS EVIDENCE. `first-order` says every hypothesis
        # held at each contributing iterate, and the index set of eq:hlb is
        # FINITE AND NON-EMPTY, so a record claiming it must point at one.
        if first and not any(
            gate.get("withdrawal") is None
            for gate in self.certificate.get("per_iterate", ())
        ) and not (
            self.reference_bracket is not None
            and self.reference_bracket.get("counted") is True
        ):
            raise ValueError(
                "first-order requires a contributing iterate in the PER-ITERATE record"
            )

    @property
    def assurance(self) -> Assurance:
        """Return the ACHIEVED tier, as the frank-wolfe interface's row reads it.

        ``certified`` where the certified evaluation certified a point and the
        run is reported at that tier (``optimizer_certificate``: "the
        certified tier where the certified evaluation certified a point and
        the run is reported at it"); ``first-order`` otherwise exactly when a
        bound is present. A reading and not a record field. It differs from
        ``reported_tier`` where a closed gate or an uncompiled declaration
        withholds the key length: the bracket is still earned, and the claim
        is still only the estimate; a point certified there is recorded under
        ``certified`` and achieves no tier.
        """
        if self.reported_tier is Assurance.CERTIFIED:
            return Assurance.CERTIFIED
        bound = self.h_lb_dropped if self.dropped_set else self.h_lb
        return Assurance.ESTIMATE if bound is None else Assurance.FIRST_ORDER

    @property
    def rate_per_round(self) -> float | None:
        """Return the emitted length per total round."""
        return None if self.key_length is None else self.key_length / self.rounds

    def as_payload(self) -> dict[str, Any]:
        """Return the general result under the production payload keys."""
        payload = asdict(self)
        del payload["final_iterate"]
        del payload["final_iterate_layout"]
        del payload["final_iterate_rows_sha256"]
        del payload["certified_exact"]
        # THE BINDINGS ARE NOT REPEATED HERE: the run record carries them in
        # its route-exact assumption set, beside each assumption, merged with
        # every other emitter's (record schema 0.20.0;
        # certiqs_key.runs.assumptions). ``security_parameter`` and
        # ``net_key_length`` travel here since the same bump, null without a
        # key length, and so does the sentence for the reason code.
        del payload["assumption_bindings"]
        payload["reason_text"] = KEY_LENGTH_REASON_TEXT.get(
            self.key_length_reason_code
        )
        payload["reported_tier"] = str(self.reported_tier)
        payload["optimizer_certificate"] = payload.pop("certificate")
        payload["rate_per_round"] = self.rate_per_round
        payload["h_low_is_infinite"] = math.isinf(self.h_low)
        if math.isinf(self.h_low):
            payload["h_low"] = "inf"
        if self.dropped_set:
            payload["h_low_dropped"] = payload.pop("h_low")
            payload["h_low_dropped_is_infinite"] = payload.pop("h_low_is_infinite")
        for name in ("h_lb", "h_lb_dropped"):
            if payload[name] is None:
                del payload[name]
        payload["first_order_minus_estimate"] = self.first_order_minus_estimate
        return payload

    @property
    def first_order_minus_estimate(self) -> float | None:
        """Return ``h_lb - h_low`` WITH ITS SIGN, a diagnostic that decides nothing.

        ``frank-wolfe/rem:fo-arithmetic`` (b): "An implementation records the
        difference with its sign". ``h_lb <= h_low`` is a consequence of exact
        arithmetic, not a floating-point invariant, so a positive value is
        evidence about the unbudgeted binary64 evaluation and refuses nothing.
        ``None`` where no bound is present or ``h_low`` is infinite; the dropped
        bound is paired with the dropped program's objective.
        """
        bound = self.h_lb_dropped if self.dropped_set else self.h_lb
        if bound is None or math.isinf(self.h_low):
            return None
        return bound - self.h_low


#: What ``assurance_reason`` says on a run that EARNED the rung. Not one of the
#: interface's machine-readable strings: those name why something was refused
#: or withdrawn, and nothing was.
FIRST_ORDER_REASON = "first_order_reported"

#: The sentence for :data:`FIRST_ORDER_REASON`, beside the withdrawal reasons'
#: ``REASON_TEXT``: the reason every successful run carries has a text.
FIRST_ORDER_REASON_TEXT = (
    "every hypothesis of frank-wolfe/thm:firstorder held at a contributing "
    "iterate and nothing withdrew its bracket, so the lower bound h_lb is "
    "established and the key length is computed from max{0, h_lb} by "
    "cor:keylength-bound at h = h_lb (frank-wolfe/cor:fo-keylength); h_low is "
    "a convergence diagnostic and not what the length is computed from"
)

#: What ``key_length_reason`` opens with where the key length is formed from
#: the certified number (``req:certified-evaluation`` (vi)).
CERTIFIED_REASON = "certified_reported"

#: The sentence for :data:`CERTIFIED_REASON`.
CERTIFIED_REASON_TEXT = (
    "the bracket was formed again at the run's final points from the "
    "declaration's data with every arithmetic step exact or rigorously "
    "enclosed (frank-wolfe/req:certified-evaluation), and the key length is "
    "computed exactly from max{0, h_cert} by frank-wolfe/cor:certified-keylength; "
    "the first-order number and its key length are recorded beside it"
)

#: What the reason adds where the certified number is formed in the fallback
#: of ``req:certified-evaluation`` (i): on the searched declaration, item (vi).
FALLBACK_REASON_TEXT = (
    ". IN THE FALLBACK (frank-wolfe/req:certified-evaluation (i)): the "
    "reference companion certified no point, so h_cert is certified on the "
    "searched, snapped declaration and bounds that declaration's value; the "
    "blocks the companion carried rest on A-SNAP "
    "(foundations/ass:snapped-measurement) for this key length, and h_lb, the "
    "bound on the companion, stays the run's first-order number, recorded "
    "beside it and combined with nothing"
)

#: The codes that travel with a reported key length, one per tier.
REPORTED_REASONS: frozenset[str] = frozenset({FIRST_ORDER_REASON, CERTIFIED_REASON})

#: A closed key-length gate of ``thm:constrained-accumulation``; the failing
#: parts are named in the prose.
SECURITY_GATE_CLOSED_REASON = "security_gate_closed"
#: ``req:key-length-alpha-domain``: the one ``SecurityGateError``
#: :func:`~certiqs_key.meat_core.finitekey.keylength.key_length_from_bound`
#: raises (its docstring: "on an ``alpha`` outside ``(1, 2)``").
ALPHA_OUTSIDE_KEY_LENGTH_DOMAIN_REASON = "alpha_outside_key_length_domain"

#: Why a run with ``h_low = +inf`` emits no key length (``rem:hlow-range``).
HLOW_INFINITE_REASON = (
    "rem:hlow-range: h_low = +inf, so no accepted frequency vector is absolutely "
    "continuous with respect to any reachable Phi[omega], Pr[Omega_AT] = 0 for "
    "every attack, the hypothesis Pr[Omega_AT] > 0 of thm:accumulated-entropy "
    "fails, and there is "
    "no run on which a key would be produced. The value is PROPAGATED AND NEVER "
    "CLAMPED, and NO KEY-LENGTH CLAIM is emitted"
)


#: EVERY CODE ``key_length_reason`` MAY OPEN WITH, the closed list
#: ``key_length_reason_code`` takes its value from (record schema 0.20.0):
#: :data:`FIRST_ORDER_REASON` on a reported length; a withdrawal or another
#: :class:`~certiqs_key.meat_core.reasons.AssuranceReason` where no bound was
#: established (``objective_infinite`` at ``h_low = +inf``); a closed gate; the
#: key-length order outside its domain; a declaration without the compiler's
#: token. ``record.schema.json`` lists the same strings, and a test holds the
#: two equal.
KEY_LENGTH_REASON_CODES: frozenset[str] = frozenset(
    {
        FIRST_ORDER_REASON,
        CERTIFIED_REASON,
        SECURITY_GATE_CLOSED_REASON,
        ALPHA_OUTSIDE_KEY_LENGTH_DOMAIN_REASON,
        DECLARATION_NOT_COMPILED,
        *(str(reason) for reason in AssuranceReason),
    }
)

#: One sentence per code, for a reader of a record who should not have to open
#: the contract; written into the record as ``stages.key_rate.reason_text``.
#: A withdrawal's sentence is meat-core's own ``REASON_TEXT``; a code with no
#: sentence there or here (an acceptance-set code, which reaches a record only
#: through ``objective_infinite``) gives ``null``.
KEY_LENGTH_REASON_TEXT: Mapping[str, str] = {
    **{str(code): text for code, text in REASON_TEXT.items()},
    FIRST_ORDER_REASON: FIRST_ORDER_REASON_TEXT,
    CERTIFIED_REASON: CERTIFIED_REASON_TEXT,
    str(AssuranceReason.OBJECTIVE_INFINITE): HLOW_INFINITE_REASON,
    SECURITY_GATE_CLOSED_REASON: (
        "a security gate of thm:constrained-accumulation did not open; a "
        "key-length output is emitted only when every gate opens, and "
        "key_length_reason names each failing part. h_low and any bound stay "
        "reported and reach no key length"
    ),
    ALPHA_OUTSIDE_KEY_LENGTH_DOMAIN_REASON: (
        "req:key-length-alpha-domain: every key-length statement requires the "
        "Renyi order alpha in (1, 2), and the run's order lies outside it, so "
        "no key length is computed; the bound stays reported"
    ),
    DECLARATION_NOT_COMPILED: (
        "req:compiled-declaration-only: the declaration did not arrive with the "
        "run tier's token that the protocol compiler emitted it, so the key "
        "length is withheld; the bound and the estimate stay reported"
    ),
}


class NegativeObjectiveError(MeatError):
    """A negative computed estimate. NAMES THE VALUE AND THE POINT.

    Typed rather than bare because the ``h_low`` output row says so in terms: a
    bare exception is not a conforming implementation of the rule, and THE
    REASON MUST BE READABLE BY THE CALLER. The objective is non-negative at
    every point of the EXACT feasible set, so a negative value signals a
    violated hypothesis rather than a small number, and it is never clamped.
    """

    def __init__(
        self,
        message: str,
        *,
        reason: RefusalReason,
        value: float,
        point: Mapping[str, object],
    ) -> None:
        """Store the reason, the value and the point beside the prose."""
        super().__init__(message)
        self.reason = reason
        self.value = value
        self.point = point


def key_length_from_first_order(
    *,
    rounds: int,
    h_lb: float,
    lambda_ec: int,
    eps_ev: float,
    eps_pa: float,
    alpha: float,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
) -> tuple[int, bool]:
    """``cor:fo-keylength``: the core's corollary at ``h = h_lb``.

    THE WHOLE OF THE INSTANCE IS THE ARGUMENT NAME. ``cor:fo-keylength`` is
    ``cor:keylength-bound`` with the Frank-Wolfe bound in place of an arbitrary
    one -- the same expression, no new floor, no additional term, no exact
    arithmetic -- and what makes ``h_lb`` an admissible ``h`` is
    ``frank-wolfe/thm:firstorder`` (ii), (iiib) and (iv), its feasible side
    verified by ``frank-wolfe/req:verified-feasible-side``. None of that is the
    core's business, which is why the core's function takes ``h`` and this one
    takes ``h_lb``. A sibling solver submodule writes its own, against its own
    bound, and calls the same core corollary.

    ``eps_auth`` and ``k_auth`` are A-AUTH's (default 0) and pass through to
    the core unchanged: they enter its corner gate and not the expression.
    """
    return key_length_from_bound(
        rounds=rounds,
        h=h_lb,
        lambda_ec=lambda_ec,
        eps_ev=eps_ev,
        eps_pa=eps_pa,
        alpha=alpha,
        ideal_hash=ideal_hash,
        eps_auth=eps_auth,
        k_auth=k_auth,
    )


def result_claim_roots(
    *,
    bound_reported: bool,
    dropped: bool,
    key_length_reported: bool,
    reference: bool = False,
    certified: bool = False,
    fallback: bool = False,
) -> list[str]:
    """Return the claim roots a result names in ``certificate["claim_roots"]``.

    THE ROOT OF EVERY NUMBER THE RESULT REPORTS:

    * a key length: the bound's root -- ``frank-wolfe/thm:firstorder``, or
      ``frank-wolfe/cor:fo-dropped`` for a dropped program -- and
      ``cor:keylength-bound``, the corollary the length is computed by;
    * a bound and no length (a closed gate, a withheld length):
      ``lem:estimate``, the claim of the reported tier, and the bound's root,
      because the record carries ``h_lb`` and a number the record carries
      carries its claim's premises;
    * neither: ``lem:estimate``, whose closure holds no assumption.

    A length is never reported without a bound (:class:`GeneralKeyRateResult`
    refuses it), so ``key_length_reported`` implies ``bound_reported``.

    ``reference``: the bound is the one formed on the reference companion
    (``frank-wolfe/req:bracket-on-reference`` (iii)), whose root is
    ``frank-wolfe/cor:fo-reference`` in place of ``thm:firstorder``.
    ``certified``: the run is reported at the certified tier, so its key
    length is formed from the certified number, and
    ``frank-wolfe/cor:certified-keylength``, the corollary that licenses it,
    joins the bound's root on every route; on the reference route
    ``frank-wolfe/cor:certified-keylength-reference``, which carries it over
    to the protocol the companion declares, joins beside it
    (``req:certified-evaluation`` (vi)). Neither adds a premise to the
    first-order length's: the companion case is split off the
    corollary, so its closure is
    ``frank-wolfe/cor:fo-keylength``'s and the reference corollary's is
    ``cor:fo-reference``'s, which ``tests/unit/test_meat_core_bindings.py``
    holds. The bound's root stays named: the record carries ``h_lb`` beside
    the certified number.

    ``fallback``: the certified number is formed on the searched declaration
    in the fallback of ``req:certified-evaluation`` (i), the run's first-order
    number staying the companion's. The roots are then ``cor:fo-reference``
    (the first-order number recorded), ``cor:certified-keylength`` and
    ``cor:keylength-bound``, never ``cor:certified-keylength-reference`` (item
    (vi)): no number formed on the companion reaches the key length.
    """
    if key_length_reported and not bound_reported:
        raise ValueError("a key length is reported only with its bound")
    if certified and not key_length_reported:
        raise ValueError("the certified tier is reported only with its key length")
    if fallback and not (certified and reference):
        raise ValueError("the fallback certifies beside a companion's bound only")
    bound_root = (
        REFERENCE_ROOT if reference else DROPPED_ROOT if dropped else FIRST_ORDER_ROOT
    )
    if certified:
        companion = [CERTIFIED_REFERENCE_ROOT] if reference and not fallback else []
        return [bound_root, CERTIFIED_ROOT, *companion, KEY_LENGTH_ROOT]
    if key_length_reported:
        return [bound_root, KEY_LENGTH_ROOT]
    if bound_reported:
        return [ESTIMATE_ROOT, bound_root]
    return [ESTIMATE_ROOT]


def _acceptance_set_shape(d: GeneralDeclaration) -> tuple[tuple[str, object], ...]:
    """Return the declared acceptance set as a binding binds it.

    Its geometry tag and the alphabet ``Chat`` on whose simplex it lies, and
    its data: the accepted frequency vector of a ``singleton`` inline (one
    binary64 number per letter), the number of declared inequalities of a
    ``polytope`` (its rows stay in the declaration, as an operator would).
    """
    acceptance = d.acceptance_set
    shape: list[tuple[str, object]] = [
        ("geometry", acceptance.geometry),
        ("alphabet", tuple(d.acceptance_values)),
    ]
    if acceptance.polytope is not None:
        shape.append(("inequalities", acceptance.polytope.m_row))
    else:
        shape.append(("frequencies", tuple(acceptance.frequencies)))
    return tuple(shape)


def declared_values(
    d: GeneralDeclaration,
    *,
    key_length: int | None,
    eps_auth: float,
    k_auth: int,
    ideal_hash: bool,
    deductions: Mapping[str, float],
) -> dict[str, object]:
    """Return the values of one run that the ledger's rows may bind.

    Every name of :data:`certiqs_key.meat_core.reasons.ROW_BINDINGS`, read
    from the declaration and the run's parameters, in the shape
    of :mod:`certiqs_key.domain.bindings`: a binary64 parameter as itself, an
    operator by its shape (alphabet and dimension) and never inlined. The
    shapes of ``constraint_entries``, ``alice_marginal``, ``alice_povm`` and
    ``attack_set_license`` are those the compiler and the transmitter bind
    for the same rows, so that the run's one entry per assumption can merge
    identical values. The labels in them (``alice_povm``'s and
    ``acceptance_set``'s alphabets) are the declaration's own, which on a
    run are the bundle's stable IDs; the run tier reads those back into the
    declared spelling before it joins the rows (``runs/assumptions.py``).

    ``ev_hash_bits`` is the error-verification deduction the engine computed,
    ``ceil(log2(1/eps_EV))`` (``deductions_of``), read and not recomputed.
    ``key_length`` is ``None`` on a run
    that reports none, where no row that binds it is emitted.
    """
    licence = d.attack_set_license
    return {
        "rounds": d.rounds,
        "lambda_ec": d.parameters.lambda_ec,
        "eps_pa": d.parameters.eps_pa,
        "eps_ev": d.parameters.eps_ev,
        "eps_auth": eps_auth,
        "k_auth": k_auth,
        "key_length": key_length,
        "ideal_hash": ideal_hash,
        "ev_hash_bits": int(deductions["error_verification"]),
        "key_holder": str(d.key_holder),
        "acceptance_set": _acceptance_set_shape(d),
        "source_mode": str(d.source_mode),
        # Part (b) of the party partition, the labels A-LAB reads as naming
        # the parties' laboratories (meat-core/ass:lab): the label of A and
        # each measured factor's, in the factors' declared order. By position
        # and not by factor name: on the engine's side the names are the
        # bundle's stable IDs, which the run tier does not map back.
        "party_partition": (
            ("alice_system", str(d.alice.party)),
            ("measured_factors", tuple(str(f.party) for f in d.factors)),
        ),
        "alice_marginal": (
            ("dimension", d.alice_dim),
            ("sector_dims", tuple(d.alice_dim_of(s) for s in d.alice_sectors)),
        ),
        "alice_povm": (
            ("form", str(d.alice_form)),
            ("alphabet", tuple(d.alice_alphabet)),
            ("dimension", d.alice_dim),
        ),
        "constraint_entries": (
            ("count", len(d.constraint_list)),
            ("rhs_tags", tuple(str(e.rhs_tag) for e in d.constraint_list)),
        ),
        "attack_set_license": (
            None if licence is None else (("supplier", str(licence["supplier"])),)
        ),
    }


def gate_failures(gates: Mapping[str, Any]) -> list[str]:
    """Return every closed part of the key-length gate, named, never only the first.

    thm:constrained-accumulation gates the constraint list and the trusted marginal
    independently,
    and letting one mask the other would hide half of what a supplier still
    owes: (i) the licensed class, (ii) the ``attack_set_license`` (A-ATK), and
    the ``source_replacement_license`` (A-SRC).
    """
    failures = []
    if not gates["licensed_class_passed"]:
        failures.append(
            "(i) an entry declares the `general` form of def:homog, which is "
            "admissible input and never licensed, at any d_A"
        )
    if gates["constraint_count"] and not gates["attack_set_license_present"]:
        failures.append(
            "(ii) the declaration carries no attack_set_license, the supplier "
            "attestation of Assumption A-ATK"
            + (
                " -- and part (i) is "
                + (
                    "VACUOUS"
                    if gates["source_mode"] != str(SourceMode.TRUSTED)
                    else "DEGENERATE"
                )
                + " here, so the gate rests entirely on this attestation "
                "(Remark rem:cgate)"
                if gates["licensed_class_vacuous"]
                else ""
            )
        )
    if (
        gates["source_replacement_license_required"]
        and not gates["source_replacement_license_present"]
    ):
        failures.append(
            "(A-SRC) a tau_A is declared at d_A >= 2 and no "
            "source_replacement_license attests Assumption A-SRC"
        )
    return failures


def _licensed_class_reason(d: GeneralDeclaration, licensed: bool, vacuous: bool) -> str:
    """Return Remark rem:cgate's reading of part (i) for this declaration.

    The same three readings as
    :func:`certiqs_key.meat_core.finitekey.keylength.licensed_class_check`, in
    the general format: vacuous in untrusted-source mode, degenerate at total
    ``d_A = 1`` (a type check rejecting only a ``general`` tag a producer can
    avoid), genuine in trusted-source mode at ``d_A >= 2``.
    """
    if not d.constraint_list:
        return (
            "the declared constraint list is empty, so no gate applies (the "
            "`inputs` table: the gate is on m >= 1)"
        )
    if not licensed:
        return (
            "an entry declares the `general` form of def:homog -- admissible "
            "input, NEVER LICENSED, at any d_A -- so this list carries no "
            "key-length claim. THE VERDICT IS A TYPE CHECK ON THE DECLARED TAG "
            "AND COMPARES NO NUMBERS"
            + (
                ". At d_A = 1 it rejects only what a producer can trivially "
                "avoid: every 1x1 Hermitian Theta_k equals c_k tau_A, so the "
                "entry could have been declared homogeneous with the same "
                "condition (Remark rem:cgate)"
                if d.alice_dim == 1
                else ""
            )
        )
    if vacuous:
        return (
            (
                "VACUOUS (Remark rem:cgate): in untrusted-source mode the "
                "licensed class of def:homog (b) IS the scalar class, so part "
                "(i) is a type check every well-formed declaration passes"
                if not d.is_trusted_source
                else "DEGENERATE (Remark rem:cgate): at d_A = 1 part (i) is a "
                "type check that rejects nothing a producer cannot trivially "
                "avoid, every 1x1 Hermitian Theta_k being c_k tau_A"
            )
            + ". The pass is evidence of nothing, about a party-local entry "
            "included (req:degenerate-gate-report), and the constrained branch "
            "rests ENTIRELY on the attack_set_license attestation, which no "
            "program can verify"
        )
    return (
        "a GENUINE restriction (Remark rem:cgate): in trusted-source mode at "
        "d_A >= 2 the licensed class is the `homogeneous` (or `party_local`) "
        "tag, and a declaration can fail it by declaring the `general` form"
    )


def group_b_worst(
    run: JointFrankWolfeResult, options: FrankWolfeOptions
) -> dict[str, dict[str, Any]]:
    """Return each per-run Group B row with its window and the WORST quantity met.

    The interfaces' promise (``declared_thresholds``, Group B): each row "is
    recorded in ``optimizer_certificate`` with the worst quantity it was
    compared against on the run". A READING of what the run already measured
    -- the per-iterate gates and the oracle diagnostics -- and never an input:
    per row the declared window, the worst quantity, the iterate it occurred at
    and the block (or Alice sector, or group) it sat in. ``worst`` is ``None``
    where the run compared nothing against the row.

    The rows decided where an object is BUILT rather than per iterate
    (``choi_isometry``, ``support_cutoff``, ``degeneracy_window``,
    ``internal_hermiticity``, ``limit_membership``) are not measured on an
    iterate and are not listed; their windows are in ``thresholds``.
    """
    gates = run.gates

    def extreme(key: str, *, largest: bool) -> dict[str, Any]:
        if not gates:
            return {"worst": None, "iteration": None, "at": None}
        values = [getattr(gate, key) for gate in gates]
        index = max(
            range(len(values)), key=lambda i: values[i] if largest else -values[i]
        )
        gate = gates[index]
        at = {
            "min_block_eigenvalue": gate.min_block_eigenvalue_at,
            "coupling_residual": gate.coupling_residual_at,
        }.get(key)
        return {"worst": values[index], "iteration": gate.iteration, "at": at}

    # THE POINT THE ESTIMATE IS TAKEN AT, measured once at loop exit and not
    # an iterate (``iteration`` is None): a run ending by the iteration limit
    # returns a point no gate consumed.
    final = run.returned_point

    def returned(worst: float | None, at: str | None) -> dict[str, Any]:
        return {"worst": worst, "iteration": None, "at": at}

    returned_positivity = returned(
        None if final is None else final.smallest,
        None if final is None else final.smallest_at,
    )
    returned_coupling = returned(
        None if final is None else final.worst,
        None if final is None else final.worst_at,
    )
    returned_rows = returned(None if final is None else final.rows, None)
    # NOTHING IS MEASURED ON THE ORACLE'S RETURN (req:iterate-checks): no
    # bracket reads it, so the rows carry the consumed and the returned point.
    rows_point = extreme("constraint_row_residual", largest=True)
    coupling_point = extreme("coupling_residual", largest=True)
    repairs = [
        (entry.get("iteration"), entry.get("group"), repair)
        for entry in run.oracle_diagnostics
        for repair in entry.get("repairs", ())
    ]
    deepest = min(repairs, key=lambda item: item[2]["min_eigenvalue"], default=None)
    return {
        "iterate_positivity": {
            "declared": 0.0,
            "kind": "spectral_floor",
            **extreme("min_block_eigenvalue", largest=False),
            "returned_point": returned_positivity,
        },
        "iterate_repair_window": {
            "declared": options.iterate_repair_window,
            "kind": "spectral_floor",
            "worst": None,
            "iteration": None,
            "at": None,
            "note": (
                "this driver takes the REJECT branch of rem:fo-iterate-repair "
                "and repairs no formed iterate, so nothing was compared "
                "against the window as a repair"
            ),
        },
        "iterate_coupling": {
            "declared": options.iterate_coupling,
            "kind": "entrywise",
            "consumed_point": coupling_point,
            "returned_point": returned_coupling,
        },
        "constraint_rows": {
            "declared": options.constraint_rows,
            "kind": "spectral_floor",
            "consumed_point": rows_point,
            "returned_point": returned_rows,
        },
        "oracle_repair_window": {
            "declared": thresholds.declared(thresholds.ORACLE_REPAIR_WINDOW),
            "kind": "spectral_floor",
            "repairs": len(repairs),
            "worst": None if deepest is None else deepest[2]["min_eigenvalue"],
            "iteration": None if deepest is None else deepest[0],
            "at": (
                None
                if deepest is None
                else {"group": deepest[1], "block": deepest[2].get("block")}
            ),
        },
        "optimizer_gap": {
            "declared": options.gap_tolerance,
            "kind": "not_a_predicate",
            "worst": run.gap,
            "iteration": run.iterations,
            "at": None,
        },
    }


def general_security_gates(d: GeneralDeclaration) -> dict[str, Any]:
    """Read licensed forms and supplier attestations, never infer coverage.

    Part (i) is a TYPE CHECK ON THE DECLARED TAG AT EVERY TOTAL ``d_A``
    (``meat-core/def:homog`` reading ``protocol-compiler/def:homog``): an entry
    is licensed when it is tagged ``homogeneous`` or ``party_local``, and a
    ``general`` entry is never licensed, at ``d_A = 1`` included.

    ``licensed_class_vacuous`` is ``True`` exactly where a PASSING part (i) is
    evidence of nothing (``req:degenerate-gate-report``): in untrusted-source
    mode and at total ``d_A = 1``, a party-local entry among the entries or
    not -- the requirement says the pass is no evidence "about a party-local
    entry either" (``rem:cgate``, the general-format paragraph). A party-local
    tag implies no canonicity. An attack_set_license is the supplier
    attestation for the whole list, including party-local entries; the engine
    does not prove that attestation.
    """
    licensed = all(
        e.rhs_tag in (GeneralRhsTag.HOMOGENEOUS, GeneralRhsTag.PARTY_LOCAL)
        for e in d.constraint_list
    )
    source_required = d.is_trusted_source and d.alice_dim >= 2
    attack_present = d.attack_set_license is not None
    source_present = d.source_replacement_license is not None
    vacuous = not d.constraint_list or (
        licensed and (not d.is_trusted_source or d.alice_dim == 1)
    )
    return {
        "source_mode": str(d.source_mode),
        "constraint_count": len(d.constraint_list),
        "licensed_class_passed": licensed,
        "licensed_class_vacuous": vacuous,
        # A BOOLEAN CANNOT CARRY VACUITY (rem:cgate): where part (i) rejects
        # nothing, a passing part (i) is evidence of nothing, and the record
        # says so in words beside the verdict.
        "licensed_class_reason": _licensed_class_reason(d, licensed, vacuous),
        "attack_set_license_present": attack_present,
        "attack_set_license": d.attack_set_license,
        "source_replacement_license_required": source_required,
        "source_replacement_license_present": source_present,
        "source_replacement_license": d.source_replacement_license,
        "party_local_entries": [
            i for i, e in enumerate(d.constraint_list) if e.is_party_local
        ],
        "canonicity_claimed": False,
        "accumulation_branch": (
            "thm:constrained-accumulation"
            if d.constraint_list
            else "thm:accumulated-entropy"
        ),
        "key_length_permitted": licensed
        and (not d.constraint_list or attack_present)
        and (not source_required or source_present),
    }


def _run_general(
    maps: JointMaps,
    oracle: LinearOracle,
    acceptance: AcceptanceOracle,
    alpha: float,
    options: FrankWolfeOptions | None,
    dropped: Iterable[tuple[str, JointSector]] | None,
    start: Mapping[JointSector, Matrix] | None,
    observer: IterateObserver | None = None,
    request: SearchRequest | None = None,
    preparation_seconds: float = 0.0,
    *,
    refuse_negative: bool = True,
) -> JointFrankWolfeResult:
    """Prepare the problem from the maps and run the search.

    ``refuse_negative`` is :func:`~certiqs_key.solvers.solve.solve_prepared`'s:
    true for the key-rate solve, false for the statistics check's solve
    (``meat-core/req:unreachable-acceptance-set`` (ii)).
    """
    from dataclasses import replace

    from certiqs_key.solvers.problem import prepared_from_maps
    from certiqs_key.solvers.solve import solve_prepared

    if options is not None and request is not None:
        raise ValueError(
            "supply a SearchRequest or internal FW replay options, not both"
        )
    chosen = request or SearchRequest.from_options(options)
    settings = options if request is None else request.fw_options()
    problem = prepared_from_maps(
        maps,
        oracle,
        acceptance,
        alpha,
        settings,
        dropped=dropped,
        start=start,
        search_method=chosen.method,
    )
    problem = replace(
        problem, preparation_seconds=problem.preparation_seconds + preparation_seconds
    )
    return solve_prepared(
        problem, chosen, observer=observer, refuse_negative=refuse_negative
    )


def solve_general_declaration(
    d: GeneralDeclaration,
    oracle: LinearOracle,
    *,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    dropped: Iterable[tuple[str, JointSector]] | None = None,
    start: Mapping[JointSector, Matrix] | None = None,
    observer: IterateObserver | None = None,
    request: SearchRequest | None = None,
) -> JointFrankWolfeResult:
    """Validate, dock acceptance geometry and run the joint solver."""
    preparation_started = time.perf_counter()
    maps, acceptance = _prepare_general(d, oracle)
    preparation_seconds = time.perf_counter() - preparation_started
    return _run_general(
        maps,
        oracle,
        acceptance,
        d.parameters.alpha if alpha is None else alpha,
        options,
        dropped,
        start,
        observer,
        request,
        preparation_seconds,
    )


def solve_general(
    d: GeneralDeclaration,
    oracle: LinearOracle,
    *,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
    dropped: Iterable[tuple[str, JointSector]] | None = None,
    start: Mapping[JointSector, Matrix] | None = None,
    observer: IterateObserver | None = None,
    request: SearchRequest | None = None,
    compiled: CompilerEmission | None = None,
    companion: CompiledReferenceCompanion | None = None,
    certification_withheld: tuple[str, ...] = (),
    strict_snaps: bool = False,
) -> GeneralKeyRateResult:
    """Run a declaration and emit its gated key-length record.

    ``observer`` is told ``(k, gap)`` at every iterate and changes nothing.

    ``compiled`` is the run tier's token that the protocol compiler emitted
    ``d`` (``req:compiled-declaration-only``). Without it every number is
    computed and reported as with it, and the key length is WITHHELD: where a
    length would otherwise have been reported, ``key_length_reason`` opens
    with ``declaration_not_compiled`` and says why. A closed gate or a
    withdrawn bound keeps its own reason, since no length was due anyway.

    ``eps_auth`` and ``k_auth`` are the run's A-AUTH parameters (the
    interface's ``eps_auth`` and ``k_auth`` rows, default 0, which the report
    flags as not counted). They are decided first, with the corner gate of
    ``req:security-statement-not-vacuous``, and enter no number but the two
    outputs of ``cor:composed-security`` (iii) emitted beside a key length.

    ``companion`` is the compiled reference companion the protocol compiler
    emitted beside ``d`` (``protocol-compiler/req:reference-companion-compiled``),
    or ``None``. Where given, it is admitted beside ``d`` before the search,
    evaluation-only, with no run of its own
    (``meat-core/req:companion-admission``); where admitted, the share
    ``reference_polish_share`` of the evaluation's wall budget is set aside
    from the search, and after the search on ``d`` the bound is formed on the
    companion at the search's points and at those of the polish, a short
    search on the companion's own program
    (``frank-wolfe/req:bracket-on-reference`` (i)): where some point
    contributes, that bound is the run's first-order number and the key
    length is formed from it (item (iii)); otherwise the run falls back to
    the bound on ``d`` with ``reference_bracket_withdrawn`` (item (iv)). Both
    are recorded in ``reference_bracket``, the polish under its ``polish``.

    THE CERTIFIED EVALUATION (``frank-wolfe/req:certified-evaluation``) runs
    after that bracket and before the key length, on the declaration the
    first-order number is formed on and at its points, as the request's
    ``certified_evaluation`` says (``on`` by default, ``off``, ``strict``).
    Where it certifies a point and ``certification_withheld`` (item (vii)'s
    reasons, which the run tier finds upstream of the declaration) is empty,
    the key length is that of ``cor:certified-keylength``, computed exactly,
    and the tier is ``certified``; otherwise every number is the first-order
    run's, with the reasons, and ``strict`` refuses
    (:class:`~certiqs_key.meat_core.errors.CertificationRefusedError`).

    Where the companion's bracket counts but its evaluation certifies no
    point, the evaluation runs once more on ``d`` (THE FALLBACK of item (i),
    :func:`_certify`), unless ``strict_snaps`` -- the run option of
    ``foundations/req:snap-reference`` (iv), which the run tier passes -- is
    set: a number certified there carries the key length, on ``d``, and the
    companion's first-order number stays ``h_lb``; the run tier then names
    the blocks the companion carried as resting on A-SNAP
    (``runs/direct_route.py``). Where the evaluation finds a block's two
    enclosures inconsistent (item (iv)(c)), the companion's bracket is
    withdrawn with that cause and the run's first-order number is formed on
    ``d`` again (``req:bracket-on-reference`` (iv)), before any key length.

    A run that forms no first-order number (its bound withdrawn) has no
    certified evaluation, so ``strict`` does not refuse it: it reports the
    estimate and no key length.
    """
    check_authentication_parameters(eps_auth, k_auth)
    preparation_started = time.perf_counter()
    maps, acceptance = _prepare_general(d, oracle, eps_auth=eps_auth)
    preparation_seconds = time.perf_counter() - preparation_started
    order = d.parameters.alpha if alpha is None else alpha
    # THE COMPANION IS ADMITTED BEFORE THE SEARCH (meat-core/req:companion-
    # admission), beside the admitted d, so that the polish's share of the
    # evaluation's wall budget is set aside before the search on d begins
    # (frank-wolfe/req:bracket-on-reference (i)): a search its budget stops,
    # where the snapped statistics also slow it, still leaves the polish its
    # time. No share is set aside where the companion is not admitted, where
    # a dropped program runs (it is neither evaluated on the companion nor
    # polished) or where the evaluation has no wall budget.
    admitted: AdmittedCompanion | None = None
    admission: dict[str, Any] | None = None
    if companion is not None:
        admission_result = admit_reference_companion(d, companion)
        admission = admission_result.as_record()
        if isinstance(admission_result, AdmittedCompanion):
            admitted = admission_result
    search_request = request
    polish_budget: float | None = None
    if admitted is not None and not tuple(dropped or ()) and request is not None:
        from certiqs_key.solvers.solve import evaluation_wall_budget

        wall = evaluation_wall_budget(request)
        if wall is not None:
            polish_budget = wall * float(REFERENCE_POLISH_SHARE)
            search_request = replace(request, budget_seconds=wall - polish_budget)
    run = _run_general(
        maps,
        oracle,
        acceptance,
        order,
        options,
        dropped,
        start,
        observer,
        search_request,
        preparation_seconds,
    )
    if run.objective < 0:
        # A NEGATIVE ESTIMATE IS A TYPED REFUSAL AND IS NEVER CLAMPED (the
        # `outputs` table, the h_low row): zero cannot stand in for it. The
        # floor the relaxed family leaves is stated rather than guessed --
        # frank-wolfe/rem:feas-tol (c'') -- so this can fire against a point
        # that is otherwise in order, and that is intended.
        raise NegativeObjectiveError(
            "the h_low output row: the computed h_low is "
            f"{run.objective!r}, which is NEGATIVE. The objective is "
            "non-negative at every point of the EXACT feasible set, so a "
            "negative value signals a violated hypothesis rather than a small "
            "number, and it is NOT CLAMPED. At a point of Feas^J(epsilon) the "
            "objective is bounded below by -(alpha/(alpha-1)) "
            "log2(1 + d_{A_0} epsilon) and by nothing larger "
            "(frank-wolfe/rem:feas-tol (c''))",
            reason=RefusalReason.NEGATIVE_OBJECTIVE,
            value=run.objective,
            point={str(pair): block.tolist() for pair, block in run.choi.items()},
        )
    gates = general_security_gates(d)
    settings = (
        request.fw_options() if request is not None else options or FrankWolfeOptions()
    )
    snapped_bound = run.h_lb_dropped if run.dropped_set else run.h_lb
    # THE DIRECT ROUTE (frank-wolfe/req:bracket-on-reference): the bound is
    # formed on the admitted companion at the search's points and at those
    # of the polish, a short search on the companion's own program within
    # the share set aside above. It counts where some point contributes
    # (iii); otherwise d's bound stands, recorded with the reason
    # reference_bracket_withdrawn (iv). The polish's objective values are no
    # estimate of the run and refuse nothing (req:negative-estimate-refused):
    # the refusal above reads the search on d alone.
    reference: ReferenceBracket | None = None
    if admitted is not None:
        reference = bracket_on_reference(
            admitted,
            maps,
            oracle,
            acceptance,
            order,
            settings,
            run.reference_candidates,
            dropped=run.dropped_set,
            polish_budget_seconds=polish_budget,
        )
    counted = reference is not None and reference.counted
    bound = (
        reference.h_lb_reference
        if counted and reference is not None
        else snapped_bound
    )
    option = "on" if request is None else request.certified_evaluation
    certification = (
        None
        if bound is None
        else _certify(
            maps,
            run,
            reference if counted else None,
            acceptance,
            order,
            option=option,
            companion=companion,
            withheld=certification_withheld,
            strict_snaps=strict_snaps,
        )
    )
    if (
        certification is not None
        and certification.bracket_withdrawn is not None
        and reference is not None
    ):
        # THE BRACKET WITHDRAWN AFTER IT COUNTED (req:bracket-on-reference
        # (iv), its second cause; req:certified-evaluation (iv)(c)): a block's
        # two enclosures are inconsistent, a defect of a carrier, and the
        # companion's first-order number read its entrywise enclosure, which
        # may be the defective one. The run's first-order number is formed on
        # d again, before any key length; the evaluation already ran there.
        reference = reference.withdrawn(
            certification.bracket_withdrawn,
            "the certified evaluation found the two enclosures of a block the "
            "companion carries inconsistent (req:certified-evaluation (iv)(c)): "
            "an engine defect in the carriers of the factor enclosures, to be "
            "reported; the run's first-order number is the bound on the "
            "searched declaration",
        )
        counted = False
        bound = snapped_bound
        if bound is None:
            certification = None
    first_order_length: int | None = None
    length = None
    clamped = False
    # NO BOUND, NO LENGTH: the machine-readable code first, the reason after.
    # `code` is that code, set beside the prose at every assignment.
    code = str(run.withdrawal or AssuranceReason.ITERATE_NOT_FEASIBLE)
    reason = (
        f"{run.withdrawal or AssuranceReason.ITERATE_NOT_FEASIBLE}: no h_lb -- "
        "the bracket was withdrawn or never formed, so cor:keylength-bound has "
        "no h established to satisfy h <= h_low. h_low is the objective at the "
        "returned point, an estimate (lem:estimate), and no length is computed "
        "from it"
    )
    if math.isinf(run.objective):
        # INDEPENDENT OF THE GATES, and reported first: no feasible statistics
        # are compatible with the acceptance set.
        code = str(AssuranceReason.OBJECTIVE_INFINITE)
        reason = HLOW_INFINITE_REASON
    elif not gates["key_length_permitted"]:
        code = SECURITY_GATE_CLOSED_REASON
        reason = (
            "security_gate_closed (thm:constrained-accumulation): a key-length output "
            "may be emitted "
            "only when every gate opens. Failing: "
            + "; ".join(gate_failures(gates))
            + ". h_low remains available -- numerical use outside the security "
            "chain is unrestricted -- but it reaches no key length"
        )
    elif bound is not None:
        try:
            length, clamped = key_length_from_first_order(
                rounds=d.rounds,
                h_lb=bound,
                lambda_ec=d.parameters.lambda_ec,
                eps_ev=d.parameters.eps_ev,
                eps_pa=d.parameters.eps_pa,
                alpha=order,
                ideal_hash=ideal_hash,
                eps_auth=eps_auth,
                k_auth=k_auth,
            )
            first_order_length = length
            code = FIRST_ORDER_REASON
            reason = (
                f"{FIRST_ORDER_REASON}: computed from max{{0, h_lb}} by "
                "cor:keylength-bound (eq:keylength-h), instantiated at h = h_lb "
                "by frank-wolfe/cor:fo-keylength"
                + (
                    " with the bound of frank-wolfe/cor:fo-dropped"
                    if run.dropped_set
                    else ""
                )
                + (
                    ". h_lb IS THE BOUND ON THE REFERENCE COMPANION, formed at the "
                    "search's points (frank-wolfe/cor:fo-reference, "
                    "req:bracket-on-reference); the bound on the searched, "
                    "snapped declaration is recorded beside it as a diagnostic "
                    "and no length is formed from it"
                    if counted
                    else ""
                )
                + ". NO NEW FLOOR, NO ADDITIONAL TERM AND NO EXACT ARITHMETIC; "
                "h_low is a convergence diagnostic and NOT what this length was "
                "computed from"
                + (
                    ". THE CLAMP APPLIED: h_lb was negative, which is not unsound "
                    "and is not repaired -- it supports no positive length "
                    "(frank-wolfe/rem:fo-arithmetic)"
                    if clamped
                    else ""
                )
            )
            if certification is not None and certification.reported:
                assert certification.certified_bound is not None
                length, clamped = certified_key_length(
                    rounds=d.rounds,
                    h=certification.certified_bound,
                    lambda_ec=d.parameters.lambda_ec,
                    eps_ev=d.parameters.eps_ev,
                    eps_pa=d.parameters.eps_pa,
                    alpha=order,
                    ideal_hash=ideal_hash,
                    eps_auth=eps_auth,
                    k_auth=k_auth,
                )
                code = CERTIFIED_REASON
                reason = (
                    f"{CERTIFIED_REASON}: {CERTIFIED_REASON_TEXT}"
                    + (FALLBACK_REASON_TEXT if certification.fallback else "")
                    + (". THE CLAMP APPLIED: h_cert was negative" if clamped else "")
                )
        except SecurityGateError as failure:
            code = ALPHA_OUTSIDE_KEY_LENGTH_DOMAIN_REASON
            reason = str(failure)
    # req:certified-evaluation (viii): strict refuses where the run is not
    # reported at the certified tier, naming the reasons; no key length.
    if option == "strict" and certification is not None and not certification.reported:
        raise CertificationRefusedError(
            "frank-wolfe/req:certified-evaluation (viii): certified_evaluation is "
            f"strict and the run is not certified ({certification.status}: "
            + ", ".join(certification.reasons)
            + f"; per point on the {certification.declaration} declaration: "
            + "; ".join(
                f"{p.index}: {', '.join(p.reasons) or 'certified'}"
                for p in certification.points
            )
            + (
                ""
                if certification.companion_points is None
                else "; per point on the reference companion: "
                + "; ".join(
                    f"{p.index}: {', '.join(p.reasons) or 'certified'}"
                    for p in certification.companion_points
                )
            )
            + ")",
            reason=str(RefusalReason.CERTIFICATION_REFUSED),
        )
    # req:compiled-declaration-only, decided LAST so that every other closed
    # gate keeps its own reason: a length the bound supports is withheld on a
    # declaration the run tier did not vouch for as the compiler's emission.
    provenance = declaration_provenance_failure(compiled)
    if length is not None and provenance is not None:
        length = None
        clamped = False
        code = DECLARATION_NOT_COMPILED
        reason = provenance
    tier = (
        Assurance.ESTIMATE
        if length is None
        else Assurance.CERTIFIED
        if code == CERTIFIED_REASON
        else Assurance.FIRST_ORDER
    )
    # THE KEY LENGTH THE SNAPPED BOUND WOULD GIVE (req:bracket-on-reference
    # (iii): recorded beside it as a diagnostic, and no key length is formed
    # from it). The same expression at the same parameters, where the gates
    # let a length be formed at all; never reported as the run's.
    snapped_length: int | None = None
    if (
        companion is not None
        and snapped_bound is not None
        and gates["key_length_permitted"]
        and not math.isinf(run.objective)
    ):
        try:
            snapped_length, _ = key_length_from_first_order(
                rounds=d.rounds,
                h_lb=snapped_bound,
                lambda_ec=d.parameters.lambda_ec,
                eps_ev=d.parameters.eps_ev,
                eps_pa=d.parameters.eps_pa,
                alpha=order,
                ideal_hash=ideal_hash,
                eps_auth=eps_auth,
                k_auth=k_auth,
            )
        except SecurityGateError:
            snapped_length = None
    # cor:composed-security (iii), on every emitted length and on no other.
    composed = (
        None
        if length is None
        else composed_security(
            key_length=length,
            eps_pa=d.parameters.eps_pa,
            eps_ev=d.parameters.eps_ev,
            eps_auth=eps_auth,
            k_auth=k_auth,
        )
    )
    ledger = assumption_ledger(
        trusted_source=d.is_trusted_source,
        alice_dim=d.alice_dim,
        alice_party=str(d.alice.party),
        constraint_entries=len(d.constraint_list),
        key_length_wanted=True,
        key_length_reported=length is not None,
        first_order=bound is not None,
    )
    _, _, warm = joint_choices(settings)
    certificate = {
        "accumulation_rule": ACCUMULATION_RULE,
        "solver_status": run.status,
        "search": dict(run.search_report),
        "iterations": run.iterations,
        "frank_wolfe_gap": run.gap,
        "oracle_diagnostics": list(run.oracle_diagnostics),
        "choi_input_basis": dict(run.choi_input_basis),
        "constraint_row_form": dict(run.constraint_row_form),
        "security_gates": gates,
        "per_iterate": [asdict(gate) for gate in run.gates],
        "timings": asdict(run.timings),
        # THE BACKEND'S FULL CAPABILITY IDENTITY, as data (spec/architecture.md
        # 7.3: the probe's record "lands in the result record").
        "backend": probe_environment(oracle.capabilities()),
        "tolerances": {
            "optimizer_gap": settings.gap_tolerance,
            "iterate_coupling": settings.iterate_coupling,
            "iterate_repair_window": settings.iterate_repair_window,
            "constraint_rows": settings.constraint_rows,
        },
        # EACH GROUP B ROW WITH THE WORST QUANTITY IT MET ON THIS RUN, where it
        # sat and at which iterate (interface.yaml, declared_thresholds, Group
        # B; rem:fo-oracle-repair for the oracle-return repairs).
        "group_b_worst": group_b_worst(run, settings),
        # HOW THE LOOP RAN (joint_options): the oracle choice with the backend
        # of every group, the step rule with its counts, the spectral
        # evidence, and the warm start's seed identity. None of it is read by
        # any number above.
        "joint_solver": {
            **dict(run.solver_report),
            "warm_start": None if warm is None else warm.as_payload(),
        },
        "assurance_reason": run.withdrawal or FIRST_ORDER_REASON,
        # READ FROM THE GENERATED TABLE (certiqs_key.domain.claim_closure),
        # which harness/generate_claim_closure.py writes from each module.yaml:
        # no hand-kept mirror of an accepted version. The roots are that
        # module's names, the one list the table covers.
        "module_versions": {
            module: module_version(module)
            for module in ("meat-core", "meat-core/frank-wolfe")
        },
        # THE ROOT OF EVERY REPORTED NUMBER, the bound's included where a
        # gate withheld the length.
        "claim_roots": result_claim_roots(
            bound_reported=bound is not None,
            dropped=bool(run.dropped_set),
            key_length_reported=length is not None,
            reference=counted,
            certified=tier is Assurance.CERTIFIED,
            fallback=(
                tier is Assurance.CERTIFIED
                and certification is not None
                and certification.fallback
            ),
        ),
    }
    if not d.is_trusted_source:
        del certificate["choi_input_basis"]
        del certificate["constraint_row_form"]
    short_ids = {value: str(key) for key, value in ASSUMPTION_MACHINE_KEYS.items()}
    short_ids.update({value: key for key, value in INHERITED_KEYS.items()})
    states = maps.parametrization.state_from_choi(run.choi)
    weights = {str(pair): float(np.trace(block).real) for pair, block in states.items()}
    branch_values = evaluate_joint_branches(
        maps, run.choi, order, dropped=frozenset(run.dropped_set)
    )
    deductions = deductions_of(
        lambda_ec=d.parameters.lambda_ec,
        eps_ev=d.parameters.eps_ev,
        eps_pa=d.parameters.eps_pa,
        alpha=order,
        ideal_hash=ideal_hash,
    )
    bindings = assumption_bindings(
        ledger,
        declared_values(
            d,
            key_length=length,
            eps_auth=eps_auth,
            k_auth=k_auth,
            ideal_hash=ideal_hash,
            deductions=deductions,
        ),
        # A-LAB's row names its party (meat-core/ass:lab): the parties the
        # ledger emitted it at, in order.
        parties=laboratory_parties(
            trusted_source=d.is_trusted_source,
            alice_party=str(d.alice.party),
            key_length_reported=length is not None,
            first_order=bound is not None,
        ),
    )
    return GeneralKeyRateResult(
        alpha=order,
        search_report=dict(run.search_report),
        rounds=d.rounds,
        h_low=run.objective,
        estimate_point_relaxed_member=run.estimate_point_relaxed_member,
        h_lb=bound if counted else run.h_lb,
        h_lb_dropped=run.h_lb_dropped,
        dropped_set=run.dropped_set,
        key_length=length,
        security_parameter=None if composed is None else composed.security_parameter,
        net_key_length=None if composed is None else composed.net_key_length,
        key_length_reason=reason,
        key_length_reason_code=code,
        reported_tier=tier,
        first_order_clamped=clamped,
        optimized_q=run.q,
        predicted_statistics=joint_statistics(maps, run.choi),
        block_contributions={
            chat: {str(pair): value for pair, value in branch.deficits.items()}
            for chat, branch in branch_values.items()
        },
        sector_weight_report={
            "weights": weights,
            "sum": sum(weights.values()),
            "residue_against_one": sum(weights.values()) - 1,
        },
        certificate=certificate,
        sector_report=asdict(general_sector_report(maps)),
        map_validation_report={
            "declaration_admitted_exactly": True,
            "factor_labels": [f.label for f in d.factors],
            "alice_sectors": list(d.alice_sectors),
            # Per key-active joint pair, the directions of the Kraus stack in
            # (support_cutoff, sqrt(support_cutoff)] relative -- set aside by
            # the one-ruler reading of dim W (rem:fo-one-ruler). Computed
            # with the maps, never per iterate; a diagnostic only.
            "hsupp_reference_band": support_band_report(
                maps.support_bands, maps.key_inert
            ),
        },
        assumption_ledger=ledger,
        # A SET OF IDS, each once: A-LAB's row is emitted once per party
        # (meat-core/ass:lab), and the ledger above lists one key per row.
        assumption_ids=tuple(dict.fromkeys(short_ids[key] for key in ledger)),
        assumption_bindings=bindings,
        deductions=deductions,
        constraint_entries_through_a_reductions_chain=d.constraints_through_a_reductions_chain,
        final_iterate=dict(run.choi),
        final_iterate_layout=iterate_layout(maps.parametrization),
        final_iterate_rows_sha256=constraint_rows_digest(d),
        reference_bracket=reference_record(
            reference,
            admission,
            snapped_bound=snapped_bound,
            snapped_key_length=snapped_length,
        ),
        certified_exact=(
            None if certification is None else certification.certified_bound
        ),
        certified=(
            None
            if certification is None
            else certification.as_record(
                # Item (ix): the first-order number on the declaration the
                # points were evaluated on, the searched one's in the fallback.
                first_order=snapped_bound if certification.fallback else bound,
                first_order_key_length=first_order_length,
            )
        ),
    )


def _certify(
    maps: JointMaps,
    run: JointFrankWolfeResult,
    reference: ReferenceBracket | None,
    acceptance: AcceptanceOracle,
    alpha: float,
    *,
    option: str,
    companion: CompiledReferenceCompanion | None,
    withheld: tuple[str, ...],
    strict_snaps: bool = False,
) -> CertifiedEvaluation:
    """Run ``req:certified-evaluation``: (i) its declarations and points, then the rest.

    On the reference companion where its bracket counts (its maps, its
    compilation's enclosures, and the at most five contributing points of
    the search and the polish together with the largest brackets there, each
    with that point's solve there); otherwise on the searched declaration at
    the best four contributing points and the last, with the search's solves. With the
    option ``off`` the record says so and the evaluation is never imported,
    so such a run never loads the ball arithmetic or its library
    (``tests/integration/test_key_rate_pipeline.py::
    test_a_run_with_the_evaluation_off_never_imports_the_certifier``).

    ONCE MORE ON THE SEARCHED DECLARATION, in two cases of item (i), the
    companion's points kept in ``companion_points``:

    * THE FALLBACK: the companion certified no point. Not where the run
      declares ``strict_snaps`` (``foundations/req:snap-reference`` (iv)), not
      where the arithmetic is unavailable, and not where a companion point is
      certified (a ``withheld`` evaluation certified one);
    * the companion's evaluation found a block's two enclosures inconsistent
      (item (iv)(c)): ``bracket_withdrawn`` names the cause, and the caller
      withdraws the companion's bracket (``req:bracket-on-reference`` (iv)).
      This runs under ``strict_snaps`` too: the run's first-order number is
      then formed on the searched declaration, as on any run without a
      companion, and the run tier's strict option refuses after the solve.

    The number certified there is a bound on the searched declaration's
    value and is never combined with anything formed on the companion.
    """
    if option == "off":
        return EVALUATION_OFF
    from certiqs_key.solvers.frank_wolfe import certified

    def tagged(
        evaluation: CertifiedEvaluation, tags: list[tuple[str, int]]
    ) -> CertifiedEvaluation:
        # Each certified point's set and consumption order, in the order the
        # points were handed (certified.evaluate forms one entry per point).
        return replace(
            evaluation,
            points=tuple(
                replace(point, point_set=point_set, sequence=sequence)
                for point, (point_set, sequence) in zip(
                    evaluation.points, tags, strict=False
                )
            ),
        )

    def on_searched() -> CertifiedEvaluation:
        points = [
            (kept.assessment.point, kept.assessment.q_iterate, kept.assessment.solves,
             kept.assessment.gate.iteration)
            for kept in run.reference_candidates
        ]
        searched = certified.evaluate(
            maps,
            points,
            acceptance,
            alpha,
            option=option,
            dropped=frozenset(run.dropped_set),
            withheld=withheld,
        )
        return replace(
            tagged(
                searched,
                [("search", kept.sequence) for kept in run.reference_candidates],
            ),
            declaration=ON_SEARCHED,
        )

    if reference is None or reference.maps is None:
        return on_searched()
    # ON THE COMPANION, the at most five contributing points of the search's
    # and the polish's sets together with the largest brackets there, a
    # point in both counted once (req:certified-evaluation (i);
    # ReferenceBracket.certification_points), each with its solve there.
    chosen = reference.certification_points()
    points = [
        (
            item.candidate.point,
            item.candidate.q_iterate,
            None if item.reference is None else item.reference.solves,
            item.candidate.gate.iteration,
        )
        for item in chosen
    ]
    first = replace(
        tagged(
            certified.evaluate(
                reference.maps,
                points,
                acceptance,
                alpha,
                option=option,
                companion=companion,
                withheld=withheld,
            ),
            [(str(item.point_set), item.sequence) for item in chosen],
        ),
        declaration=ON_REFERENCE_COMPANION,
    )
    if first.inconsistent:
        second = on_searched()
        return replace(
            second,
            companion_points=first.points,
            bracket_withdrawn=FACTOR_ENCLOSURE_INCONSISTENT,
            seconds=first.seconds + second.seconds,
        )
    if (
        first.certified_bound is not None
        or strict_snaps
        or CERTIFIER_UNAVAILABLE in first.reasons
    ):
        return first
    second = on_searched()
    return replace(
        second, companion_points=first.points, seconds=first.seconds + second.seconds
    )
