"""THE Frank-Wolfe driver: every declaration runs here, with the dropped program.

``frank-wolfe/rem:fo-general-format`` (1): ``thm:firstorder`` holds AS WRITTEN
for a declaration in the general format, with ``Feas^J`` the set of lists over
the joint sectors, "because no step of that theorem reads a constraint row, the
number of measured factors or the number of Alice sectors". An accepted-format
declaration is the degenerate case entry for entry (``def:declaration``) and
runs here as the general declaration it is
(:func:`~certiqs_key.meat_core.declaration.general.general_from_accepted`).
This loop computes the bracket ``eq:hlb`` of ``thm:firstorder`` and the
per-iterate hypothesis gate; beyond that it carries

* **(2) of the same remark**: in trusted-source mode the
  linear minimisation splits into ONE INDEPENDENT CONIC PROGRAM PER ALICE
  SECTOR, and the feasible side of a bracket is a sum of per-sector lower
  bounds (``lem:feasible-side-dual`` (ii)), each verified from its own
  program's dual (``req:verified-feasible-side``);
* **the dropped program of ``def:dropped``**: a run may
  choose a dropped set, and the number it then reports is
  ``h_lb_dropped`` -- ``frank-wolfe/cor:fo-dropped``'s
  ``underline h^{FO,D}`` -- REPORTED UNDER ITS OWN NAME, WITH ``D`` BESIDE IT,
  AND NEVER AS ``h_lb``;
* **per-stage timing hooks**: seconds and call counts per
  stage, carried on the result and never inside a number;
* **a line search that uses the linearity of ``Phi``**: the statistics at a
  trial point are interpolated from the two endpoint statistics, and only the
  deficits are formed at the trial point. The trial values choose the step and
  nothing else: the accepted iterate's value is re-formed by
  :func:`~certiqs_key.meat_core.objective.joint.joint_objective_value`, so
  every objective and linearization a run reports comes from the direct path;
* **three recorded solver choices**
  (:mod:`~certiqs_key.solvers.frank_wolfe.joint_options`): the closed-form
  spectral oracle on the groups whose feasible set is a spectraplex, the
  pairwise step rule (:mod:`~certiqs_key.solvers.frank_wolfe.joint_pairwise`),
  and a warm start. Each changes the path, never what a bracket means: the
  gate below verifies the feasible side from each backend's dual under every
  choice, and the defaults are the plain loop;
* **a per-iterate observer**: an optional callable told ``(k, gap)`` at every iterate
  whose gap was formed. Nothing reads its return value, so it cannot change
  the outcome; an exception raised inside it propagates as the caller's bug;
* **one ``q`` rule, chosen by the acceptance set's geometry**
  (:mod:`~certiqs_key.solvers.frank_wolfe.q_rule`): on a canonical
  box ``q`` is the binary64 closed-form partial minimiser of ``f(J, .)`` at
  every point evaluated and every line-search trial, made an exact member of
  the set (a member by construction, not an exact argmin); a singleton keeps
  its one point; any other polytope steps toward the exact
  LP vertex, whose partial-minimum solve is not built. No
  setting chooses it and no protocol name enters it.

ONE DRIVER
==========
Every declaration runs here, an accepted-format one as its embedding. A
separate one-factor loop would not be bit-identical -- its line search would
differ -- so accepted-format numbers would differ by rounding-level and
convergence-level amounts; every hand-derived oracle holds on this loop.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterable, Mapping
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np

from certiqs_key.meat_core.errors import SupportError
from certiqs_key.meat_core.objective.joint import (
    NOTHING_DROPPED,
    DroppedSet,
    JointChoiParametrization,
    JointMaps,
    JointSector,
    joint_objective_value,
    joint_objective_value_at_statistics,
    joint_statistics,
    normalise_dropped_set,
)
from certiqs_key.meat_core.objective.joint_gradient import joint_gradient
from certiqs_key.meat_core.objective.joint_rows import joint_constraint_residual
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix, hermitian_part
from certiqs_key.meat_core.reasons import AssuranceReason, assumption_ledger
from certiqs_key.solvers.assessment import assess_first_order
from certiqs_key.solvers.capabilities.probe import (
    SPECTRAPLEX_REQUIREMENTS,
    require_capabilities,
)
from certiqs_key.solvers.frank_wolfe.acceptance_iterate import (
    AcceptanceIterate,
    AcceptanceVertex,
)
from certiqs_key.solvers.frank_wolfe.acceptance_iterate import (
    combine_frequencies as _combine_q,
)
from certiqs_key.solvers.frank_wolfe.driver import (
    OPTIMAL_ORACLE_STATUSES,
    STATUS_HYPOTHESIS_WITHDRAWN,
    STATUS_OBJECTIVE_INFINITE_AT_START,
    FrankWolfeOptions,
    _line_search,
)
from certiqs_key.solvers.frank_wolfe.joint_options import (
    PAIRWISE_FOLD_BELOW,
    PAIRWISE_SHRINK,
    hermiticity_defect,
    joint_choices,
    oracle_assignment,
)
from certiqs_key.solvers.frank_wolfe.joint_pairwise import (
    ActiveSet,
    FlatLayout,
    shrink_blocks,
    shrink_frequencies,
    shrink_frequencies_exact,
)
from certiqs_key.solvers.frank_wolfe.q_rule import BoxPartialMinimum, q_rule_for
from certiqs_key.solvers.frank_wolfe.verified import GroupSolve
from certiqs_key.solvers.oracles.acceptance import AcceptanceOracle
from certiqs_key.solvers.oracles.joint_rows import (
    PrebuiltRows,
    joint_label,
    joint_program_for_alice_sector,
    joint_program_untrusted,
    prebuilt_rows,
    split_joint_label,
)
from certiqs_key.solvers.oracles.protocol import (
    LinearOracle,
    OracleFailure,
    OracleSolution,
    SectorChoiProblem,
)
from certiqs_key.solvers.oracles.spectral import SpectralSectorChoiOracle
from certiqs_key.solvers.types import JointIterateGate, PointCheck, StageTimings
from certiqs_key.solvers.types import SearchResult as JointFrankWolfeResult

#: A caller's optional per-iterate hook: ``(k, gap)``, the iteration and the
#: Frank-Wolfe gap formed at it. IT MUST NOT CHANGE THE OUTCOME: nothing reads its
#: return value, and an exception raised inside it propagates as the caller's
#: bug rather than being swallowed. The run tier forwards it
#: (:meth:`certiqs_key.runs.flow.FlowRecorder.iterate`).
type IterateObserver = Callable[[int, float], None]

if TYPE_CHECKING:
    from certiqs_key.solvers.assessment import CandidateAssessment


def joint_run_metadata(maps: JointMaps, *, first_order: bool = False) -> dict[str, Any]:
    """Record the actual per-sector frames and the actual imposed row forms."""
    d = maps.declaration
    bases = {}
    rows = {}
    for t, frame in maps.parametrization.frames.items():
        if d.is_trusted_source:
            bases[t] = {
                "frame": "full" if frame.is_full_frame else "support",
                "input_dim": frame.input_dim,
                "alice_dim": d.alice_dim_of(t),
                "real": frame.iota.real.tolist(),
                "imag": frame.iota.imag.tolist(),
                "factor_real": frame.w.real.tolist(),
                "factor_imag": frame.w.imag.tolist(),
            }
        rows[t] = {
            str(i): ("conjugated_party_local" if entry.is_party_local else "conjugated")
            if d.is_trusted_source
            else ("party_local" if entry.is_party_local else "scalar")
            for i, entry in enumerate(d.constraint_list)
        }
    return {
        "choi_input_basis": bases,
        "constraint_row_form": rows,
        "assumption_ledger": assumption_ledger(
            trusted_source=d.is_trusted_source,
            alice_dim=d.alice_dim,
            alice_party=str(d.alice.party),
            constraint_entries=len(d.constraint_list),
            key_length_wanted=False,
            key_length_reported=False,
            first_order=first_order,
        ),
    }


def joint_initial_point(
    parametrization: JointChoiParametrization,
) -> dict[JointSector, Matrix]:
    """Return a point satisfying the coupling condition of its mode.

    Trusted: ``J_{t,s} = 1_{A_{0,t}} (x) 1_{Q_s} / (|S| d_s)``, whose partial
    traces sum to ``1_{A_{0,t}}`` for each ``t`` -- one coupling constraint per
    Alice sector, as ``thm:choi``'s general format writes them. Untrusted: the
    normalised identity on every joint block, whose total trace is one.

    IT SATISFIES NO DECLARED ROW BY CONSTRUCTION, and says so rather than
    pretending otherwise: a declaration with constraint rows needs a start the
    caller supplies or obtains from the oracle at zero cost.
    """
    declaration = parametrization.declaration
    pairs = parametrization.joint_sectors
    if declaration.is_trusted_source:
        count = len(declaration.sector_index_set)
        return {
            pair: np.asarray(
                np.kron(
                    np.eye(parametrization.input_dim(pair[0]), dtype=np.complex128),
                    np.eye(declaration.sector_dim(pair[1]), dtype=np.complex128)
                    / (count * declaration.sector_dim(pair[1])),
                ),
                dtype=np.complex128,
            )
            for pair in pairs
        }
    total = len(pairs)
    return {
        pair: np.asarray(
            np.eye(declaration.joint_block_dim(*pair), dtype=np.complex128)
            / (total * declaration.joint_block_dim(*pair)),
            dtype=np.complex128,
        )
        for pair in pairs
    }


def coupling_residuals(
    parametrization: JointChoiParametrization, choi: Mapping[JointSector, Matrix]
) -> dict[str, float]:
    """Return ONE COUPLING RESIDUAL PER ALICE SECTOR.

    ``frank-wolfe/interface.yaml``, ``declared_thresholds``,
    ``general_format_readings``, the ``iterate_coupling`` row: "ONE COUPLING
    RESIDUAL PER ALICE SECTOR, ``|| sum_s tr_{Q_s} J_{t,s} - 1_{A_{0,t}} ||_max``,
    each inside the SAME declared window". NO NEW WINDOW AND NO NEW NUMBER: the
    window is the accepted one and is read at this object. In untrusted-source
    mode the single scalar residual is returned under the one key the mode has.
    """
    declaration = parametrization.declaration
    if not declaration.is_trusted_source:
        total = sum(
            float(np.real(np.trace(as_matrix(choi[pair]))))
            for pair in parametrization.joint_sectors
        )
        return {"*": abs(total - 1.0)}
    out: dict[str, float] = {}
    for alice_sector in declaration.alice_sectors:
        input_dim = parametrization.input_dim(alice_sector)
        accumulated = np.zeros((input_dim, input_dim), dtype=np.complex128)
        for sector in declaration.sector_index_set:
            width = declaration.sector_dim(sector)
            block = as_matrix(choi[(alice_sector, sector)]).reshape(
                input_dim, width, input_dim, width
            )
            accumulated = accumulated + np.einsum("aqbq->ab", block)
        out[alice_sector] = float(
            np.max(np.abs(accumulated - np.eye(input_dim, dtype=np.complex128)))
        )
    return out


def _check_point(
    parametrization: JointChoiParametrization,
    choi: Mapping[JointSector, Matrix],
    options: FrankWolfeOptions,
    where: str,
    *,
    residuals_fatal: bool = True,
) -> PointCheck:
    """Return what a point measures, refusing one that is not in ``Feas^J`` at all.

    The declared joint-sector layout and per-block positive semidefiniteness at
    the repair window: a violation stops the run rather than being repaired.
    The two residual checks of ``rem:fo-iterate-checks`` -- the coupling
    condition of its mode at ``iterate_coupling`` and the declared rows at
    ``constraint_rows`` (``rem:feas-tol``) -- stop it too on a START or a
    warm-start SEED (``residuals_fatal``); on a point the loop CONSUMES, a
    residual above its window is measured and returned, and the gate
    WITHDRAWS that iterate's bracket under
    ``iterate_not_feasible`` while the run survives with its estimate
    (``req:first-order-withdrawal`` (iv)).
    """
    if set(choi) != set(parametrization.joint_sectors):
        raise SupportError(
            f"{where}: the point covers {sorted(choi)} but the declaration has "
            f"{sorted(parametrization.joint_sectors)}; leaving the declared "
            "joint-sector layout stops the run"
        )
    smallest = math.inf
    smallest_at = ""
    for pair in parametrization.joint_sectors:
        block = as_matrix(choi[pair])
        if not np.all(np.isfinite(block)):
            raise SupportError(f"{where}: non-finite block on {pair}")
        expected = parametrization.block_dim(pair)
        if block.shape != (expected, expected):
            raise SupportError(
                f"{where}: the block on {pair} has shape {block.shape}, expected "
                f"({expected}, {expected})"
            )
        values = np.linalg.eigvalsh(hermitian_part(block))
        if float(np.min(values)) < smallest:
            smallest = float(np.min(values))
            smallest_at = joint_label(pair)
    if smallest < -options.iterate_repair_window:
        raise SupportError(
            f"{where}: a block has minimum eigenvalue {smallest:.3e}, outside "
            "the positive semidefinite cone"
        )
    residuals = coupling_residuals(parametrization, choi)
    worst = max(residuals.values())
    if residuals_fatal and worst > options.iterate_coupling:
        raise SupportError(
            f"{where}: the coupling constraint of Alice sector "
            f"{max(residuals, key=lambda key: residuals[key])!r} is violated by "
            f"{worst:.3e}; in trusted-source mode there is one per sector "
            "(thm:choi, the general format) and each is decided inside the same "
            f"declared window {options.iterate_coupling:.1e}"
        )
    rows = joint_constraint_residual(parametrization, choi)
    if residuals_fatal and rows > options.constraint_rows:
        raise SupportError(
            f"{where}: declared constraint-row residual {rows:.3e} exceeds "
            f"the declared window {options.constraint_rows:.1e}"
        )
    return PointCheck(
        smallest=smallest,
        smallest_at=smallest_at,
        worst=worst,
        worst_at=str(max(residuals, key=lambda key: residuals[key])),
        rows=rows,
    )


def _combine(
    x: Mapping[JointSector, Matrix],
    s: Mapping[JointSector, Matrix],
    step: float,
) -> dict[JointSector, Matrix]:
    """Return ``(1 - step) x + step s``, blockwise over the joint sectors."""
    return {
        pair: hermitian_part(
            np.asarray((1.0 - step) * x[pair] + step * s[pair], np.complex128)
        )
        for pair in x
    }


def _combine_statistics(
    start: Mapping[str, float], end: Mapping[str, float], step: float
) -> dict[str, float]:
    """Return ``(1 - step) Phi(x) + step Phi(s)``, the statistics on the segment.

    ``eq:K-joint``'s ``Phi`` is linear, so this IS ``Phi`` at the combined
    point up to rounding. Used only to choose a step; see
    :func:`~certiqs_key.meat_core.objective.joint.joint_objective_value_at_statistics`.
    """
    return {
        chat: (1.0 - step) * value + step * end[chat] for chat, value in start.items()
    }


def _oracle_vertex(
    maps: JointMaps,
    oracle: LinearOracle,
    cost: Mapping[JointSector, Matrix],
    diagnostics: list[Mapping[str, Any]],
    rows: Mapping[str, PrebuiltRows] | None = None,
    *,
    assignment: Mapping[str, str] | None = None,
    spectral: LinearOracle | None = None,
    iteration: int | None = None,
    solves: dict[str, GroupSolve] | None = None,
) -> tuple[dict[JointSector, Matrix], bool]:
    """Return the linear minimiser over ``Feas^J``, PER ALICE SECTOR.

    ``thm:choi``'s general format makes ``Feas^J`` a Cartesian product over the
    Alice sectors in trusted-source mode, so the minimiser is assembled from one
    independent program per sector (``frank-wolfe/rem:fo-general-format`` (2)).
    In untrusted-source mode nothing splits and one program covers every joint
    sector. The minimiser serves the search; no bracket reads it.

    ``solves``, where given, receives per group the subproblem and the dual its
    backend returned (:class:`~certiqs_key.solvers.frank_wolfe.verified.GroupSolve`),
    from which the feasible side of the bracket is verified
    (``req:verified-feasible-side``). A group whose backend raises is entered
    with the dual the failure carries, before the failure propagates.

    ``assignment`` names the backend of each group (an Alice sector, or ``"*"``
    in untrusted-source mode), decided before the loop by
    :func:`~certiqs_key.solvers.frank_wolfe.joint_options.oracle_assignment`;
    absent, every group goes to ``oracle``. A group assigned ``"spectral"`` is
    served by ``spectral`` and by nothing else: there is no re-routing on a
    failure. Every call's diagnostics carry the group it served and the
    ``iteration`` it was made at (``None`` outside the loop), so a repair the
    backend records is located by block, iterate and depth
    (rem:fo-oracle-repair).
    """
    parametrization = maps.parametrization
    declaration = parametrization.declaration

    def backend(group: str) -> LinearOracle:
        if assignment is not None and assignment[group] == "spectral":
            if spectral is None:
                raise OracleFailure(
                    f"group {group!r} is assigned the spectral backend and none "
                    "was supplied"
                )
            return spectral
        return oracle

    def solve(group: str, problem: SectorChoiProblem) -> OracleSolution:
        try:
            solution = backend(group).minimize(problem)
        except OracleFailure as failure:
            if solves is not None:
                solves[group] = GroupSolve(problem, failure.dual)
            raise
        if solves is not None:
            solves[group] = GroupSolve(problem, solution.dual)
        return solution

    vertex: dict[JointSector, Matrix] = {}
    optimal = True
    if declaration.is_trusted_source:
        for alice_sector in declaration.alice_sectors:
            problem = joint_program_for_alice_sector(
                parametrization,
                alice_sector,
                cost,
                rows=None if rows is None else rows[alice_sector],
            )
            solution = solve(alice_sector, problem)
            diagnostics.append(
                {**solution.diagnostics, "group": alice_sector, "iteration": iteration}
            )
            optimal = optimal and _reports_optimal(solution.diagnostics)
            for sector in declaration.sector_index_set:
                vertex[(alice_sector, sector)] = as_matrix(solution.blocks[sector])
        return vertex, optimal
    solution = solve("*", joint_program_untrusted(parametrization, cost))
    diagnostics.append({**solution.diagnostics, "group": "*", "iteration": iteration})
    optimal = _reports_optimal(solution.diagnostics)
    for label, block in solution.blocks.items():
        vertex[split_joint_label(label)] = as_matrix(block)
    return vertex, optimal


def _reports_optimal(diagnostics: Mapping[str, Any]) -> bool:
    """Return whether a backend asserted optimality of its return.

    A DIAGNOSTIC (``oracle_optimal`` on the gate): no bracket reads the status,
    the feasible side being verified without it (``req:verified-feasible-side``),
    and no iterate is withdrawn for it (``req:first-order-withdrawal``). A
    backend that reports no status asserts nothing.
    """
    status = diagnostics.get("sol_status")
    return status in OPTIMAL_ORACLE_STATUSES


def _status_of(calls: Iterable[Mapping[str, Any]]) -> str:
    """Return one iterate's oracle status: the first non-optimal, else the first.

    An iterate calls one backend per group; the record names the status that
    decided ``oracle_optimal`` -- the first group's that asserted no
    optimality -- and otherwise the (optimal) status of the first call.
    """
    statuses = [str(entry.get("sol_status", "unknown")) for entry in calls]
    for status in statuses:
        if status not in OPTIMAL_ORACLE_STATUSES:
            return status
    return statuses[0] if statuses else "unknown"


def run_joint_frank_wolfe(
    maps: JointMaps,
    oracle: LinearOracle,
    acceptance: AcceptanceOracle,
    start: Mapping[JointSector, Matrix],
    alpha: float,
    options: FrankWolfeOptions | None = None,
    *,
    dropped: Iterable[tuple[str, JointSector]] | None = None,
    skip_key_inert: bool = True,
    anchor: Mapping[JointSector, Matrix] | None = None,
    observer: IterateObserver | None = None,
    deadline: float | None = None,
    stagnation_limit: int | None = None,
    assessment_observer: Callable[[CandidateAssessment], None] | None = None,
    start_q: AcceptanceIterate | None = None,
) -> JointFrankWolfeResult:
    """Run the driver from a feasible starting point.

    Returns the best point reached with its objective -- an ESTIMATE, which
    bounds the program's value from above -- and the first-order number of
    ``eq:hlb``, reported as ``h_lb`` when the dropped set is empty and as
    ``h_lb_dropped`` when it is not (``cor:fo-dropped``, ``eq:hlb-dropped``).

    ``options`` may be a
    :class:`~certiqs_key.solvers.frank_wolfe.joint_options.JointFrankWolfeOptions`
    choosing the oracle backend and the step rule; plain options run today's
    loop (QICS, vanilla). ``anchor`` is the interior point pairwise atoms are
    shrunk toward, the start when absent; a warm-started run passes the cold
    interior start. NO BRACKET READS THE ORACLE'S RETURN under either rule:
    its feasible side is verified from the backend's dual
    (``req:verified-feasible-side``), the pairwise rule moves along shrunk
    atoms, and the gate below never sees one.

    THE PAIRWISE ANCHOR IS CHECKED POSITIVE DEFINITE, AND THE VALUE RECORDED.
    The shrink keeps a positive weight on the anchor at every iterate, which is
    what makes (H-SUPP) reachable only when the anchor is positive definite. The
    interior start is by construction; a declaration with constraint rows
    anchors at the oracle's zero-cost vertex, an interior-point return that is
    in practice strictly feasible but not by construction. So its smallest
    block eigenvalue is measured, recorded under
    ``solver_report["pairwise"]["anchor_min_eigenvalue"]``, and a run whose
    anchor is not positive definite stops (fail closed) rather than running a
    rule whose premise does not hold.

    ``observer`` (:data:`IterateObserver`) is told ``(k, gap)`` at every
    iterate whose gap was formed, and changes nothing. ``assessment_observer``
    is an internal measurement hook for every completed gate, including a
    withdrawn gate whose gradient could not be formed; its return is ignored.

    ``start_q`` seeds the acceptance-side iterate where the set has no q rule
    (a polytope): the polish of ``req:bracket-on-reference`` (i) starts from a
    point of the search on the snapped declaration with that point's exact
    ``q``, formed on the exact island (``req:acceptance-iterate-exact``), and
    updates it by the same exact convex steps. Where the set has a q rule,
    ``q`` is that rule's exact minimiser at every point, as without it.
    """
    settings = options or FrankWolfeOptions()
    chosen = normalise_dropped_set(maps, dropped)
    parametrization = maps.parametrization
    timings = StageTimings()
    _check_point(parametrization, start, settings, "starting point")
    # A SUPPLIED START IS CHECKED FOR CONTENT TOO: _check_point tests the
    # Hermitian part's spectrum, which a non-Hermitian block would pass.
    for pair in parametrization.joint_sectors:
        defect = hermiticity_defect(as_matrix(start[pair]))
        if defect is not None:
            raise SupportError(f"starting point: the block on {pair} is {defect}")
    oracle_choice, step_rule, _ = joint_choices(settings)
    # DECIDED ONCE, FROM THE DECLARATION'S STRUCTURE, BEFORE ANY CALL: which
    # backend serves which group. Nothing below re-routes a group.
    assignment = oracle_assignment(parametrization, oracle_choice)
    spectral = _spectral_backend(parametrization, assignment)
    # q_t IS FORMED ON THE EXACT ISLAND (Remark rem:acc-side (alpha), (beta))
    # and EVALUATED AT ITS BINARY64 VIEW `q` (acceptance_iterate).
    q_iterate = AcceptanceIterate.start(acceptance) if start_q is None else start_q
    q = q_iterate.view
    # THE q RULE, DECIDED ONCE FROM THE ACCEPTANCE SET'S GEOMETRY (q_rule):
    # on a canonical box q is argmin_q f(J, q), made exact, at every point
    # evaluated; otherwise (None) the previous step toward the exact vertex.
    q_rule = q_rule_for(acceptance, maps, alpha)
    # The subproblem's rows are a function of
    # the declaration and the frame, so they are built ONCE per solve and only
    # the cost is rebuilt per iteration.
    rows = (
        prebuilt_rows(parametrization)
        if parametrization.declaration.is_trusted_source
        else None
    )
    # The joint sectors whose blocks some deficit reads: a trial point of the
    # line search forms only these (JointMaps.branch_plan).
    deficit_pairs = maps.deficit_pairs(chosen, skip_key_inert)
    point = dict(start)
    if q_rule is None:
        value = joint_objective_value(
            maps, q, point, alpha, dropped=chosen, skip_key_inert=skip_key_inert
        )
    else:
        # q_0 = q*(J_0), an exact member of the box: rem:acc-side (alpha).
        exact_start, value = q_rule.exact_at(
            maps, point, dropped=chosen, skip_key_inert=skip_key_inert
        )
        q_iterate = q_iterate.at(exact_start)
        q = q_iterate.view
    diagnostics: list[Mapping[str, Any]] = []
    gates: list[JointIterateGate] = []
    gap = math.inf
    withdrawn_at_a_hypothesis = False
    best_assessment: CandidateAssessment | None = None

    if math.isinf(value):
        returned = _check_point(
            parametrization, point, settings, "returned point", residuals_fatal=False
        )
        return JointFrankWolfeResult(
            objective=math.inf,
            choi=point,
            q=q,
            iterations=0,
            gap=math.inf,
            h_lb=None,
            h_lb_dropped=None,
            dropped_set=tuple(sorted(chosen)),
            withdrawal=str(AssuranceReason.OBJECTIVE_INFINITE),
            status=STATUS_OBJECTIVE_INFINITE_AT_START,
            timings=timings,
            solver_report=solver_report(
                oracle_choice,
                step_rule,
                assignment,
                [],
                None,
                timings,
                q_rule=q_rule_name(q_rule),
            ),
            returned_point=returned,
            estimate_point_relaxed_member=returned.established(settings),
            **joint_run_metadata(maps),
        )

    # THE PAIRWISE RULE'S STATE: the start as the one atom of weight one, and
    # the interior point every oracle atom is shrunk toward. None under the
    # vanilla rule, whose loop below is unchanged.
    active: ActiveSet | None = None
    layout: FlatLayout | None = None
    anchor_blocks: Any = None
    anchor_frequencies: Any = None
    anchor_exact: tuple[Fraction, ...] | None = None
    anchor_min_eigenvalue: float | None = None
    if step_rule == "pairwise":
        # UNDER THE EXACT q RULE THE ATOMS ARE J-ONLY: q is not a variable the
        # atoms carry but q*(J) at whatever J they combine to, so the layout
        # holds no acceptance values and every q half below is empty.
        layout = FlatLayout.of(
            parametrization.joint_sectors,
            [parametrization.block_dim(pair) for pair in parametrization.joint_sectors],
            tuple(q) if q_rule is None else (),
        )
        anchor_point = start if anchor is None else anchor
        anchor_min_eigenvalue = min(
            float(np.min(np.linalg.eigvalsh(hermitian_part(as_matrix(block)))))
            for block in anchor_point.values()
        )
        if not anchor_min_eigenvalue > 0.0:
            raise SupportError(
                "the pairwise rule's anchor is not positive definite (smallest "
                f"block eigenvalue {anchor_min_eigenvalue:.3e}): the shrunk atoms "
                "would keep no positive-definite component, so (H-SUPP) would "
                "not be reachable by construction. The run stops rather than "
                "running a rule whose premise does not hold (fail closed)"
            )
        anchor_blocks = layout.flatten(anchor_point)
        anchor_frequencies = layout.frequencies(q)
        # ON A MOVING GEOMETRY THE ATOMS' q HALVES AND THE WEIGHTS ARE EXACT
        # (joint_pairwise), so the rebuilt q_t is a convex combination with
        # exact rational weights of exact points of the set.
        anchor_exact = (
            None
            if q_iterate.exact is None or q_rule is not None
            else tuple(q_iterate.exact[chat] for chat in layout.values)
        )
        active = ActiveSet.single(
            layout.flatten(point), anchor_frequencies, anchor_exact
        )

    iteration = 0
    interrupted: str | None = None
    previous_point: dict[JointSector, Matrix] | None = None
    previous_q: dict[str, float] | None = None
    repeated = 0
    for iteration in range(1, settings.max_iterations + 1):
        if iteration > 1 and deadline is not None and time.perf_counter() >= deadline:
            interrupted = "budget_exhausted"
            iteration -= 1
            break
        if stagnation_limit is not None:
            unchanged = (
                previous_point is not None
                and previous_q == q
                and all(
                    np.array_equal(previous_point[pair], block)
                    for pair, block in point.items()
                )
            )
            repeated = repeated + 1 if unchanged else 0
            if repeated >= stagnation_limit:
                interrupted = "stagnated"
                iteration -= 1
                break
            previous_point = dict(point)
            previous_q = dict(q)
        assessment = assess_first_order(
            maps,
            oracle,
            acceptance,
            point,
            q_iterate,
            alpha,
            settings,
            chosen,
            rows,
            assignment,
            spectral,
            iteration,
            timings,
            diagnostics,
            value,
            skip_key_inert,
        )
        gates.append(assessment.gate)
        if assessment_observer is not None:
            assessment_observer(assessment)
        if assessment.contributes and (
            best_assessment is None
            or assessment.gate.linearization > best_assessment.gate.linearization
        ):
            best_assessment = assessment
        if assessment.gradient is None:
            withdrawn_at_a_hypothesis = True
            break
        gradient = assessment.gradient
        vertex = assessment.vertex
        vertex_q = assessment.vertex_q
        assert vertex is not None and vertex_q is not None
        acceptance_point = vertex_q.view
        gap = assessment.gap
        if observer is not None:
            observer(iteration, gap)
        if gap <= settings.gap_tolerance:
            break

        if active is not None and layout is not None:
            # THE PAIRWISE RULE. It receives the exact return only to build
            # its shrunk atom from; the bracket above has already consumed the
            # exact pair and nothing below changes it.
            moved = _pairwise_iteration(
                maps,
                layout,
                active,
                point,
                q_iterate,
                value,
                vertex,
                vertex_q,
                gradient.blocks,
                gradient.q,
                anchor_blocks,
                anchor_frequencies,
                anchor_exact,
                alpha,
                settings,
                chosen,
                skip_key_inert,
                deficit_pairs,
                timings,
                iteration,
                q_rule,
            )
            if moved is not None:
                active, point, q_iterate, value = moved
                q = q_iterate.view
            continue

        evaluations = 0
        started = time.perf_counter()
        # PHI IS LINEAR (eq:K-joint), so along the segment point -> vertex
        # Phi(point + t (vertex - point)) = (1 - t) Phi(point) + t Phi(vertex).
        # The two endpoint statistics are formed once per iteration and each
        # trial point interpolates them; the deficits, which are not linear,
        # are still formed at the trial point. The trial values only CHOOSE
        # the step: the value the iterate carries is re-evaluated below by
        # the ordinary direct path.
        statistics_point = joint_statistics(maps, point)
        statistics_vertex = joint_statistics(maps, vertex)

        # Only the blocks some deficit reads are combined at a trial point;
        # the statistics of every block are already in the interpolation.
        current_blocks = {pair: point[pair] for pair in deficit_pairs}
        target_blocks = {pair: vertex[pair] for pair in deficit_pairs}

        def evaluate(
            step: float,
            current: Mapping[JointSector, Matrix] = current_blocks,
            target: Mapping[JointSector, Matrix] = target_blocks,
            weights: Mapping[str, float] = q,
            weight_vertex: Mapping[str, float] = acceptance_point,
            phi_current: Mapping[str, float] = statistics_point,
            phi_target: Mapping[str, float] = statistics_vertex,
        ) -> float:
            nonlocal evaluations
            evaluations += 1
            if q_rule is not None:
                # g(J) = f(J, q*(J)) at the trial point: q is re-minimised.
                return q_rule.objective_at_statistics(
                    maps,
                    _combine(current, target, step),
                    _combine_statistics(phi_current, phi_target, step),
                    dropped=chosen,
                    skip_key_inert=skip_key_inert,
                )
            return joint_objective_value_at_statistics(
                maps,
                _combine_q(weights, weight_vertex, step),
                _combine(current, target, step),
                alpha,
                _combine_statistics(phi_current, phi_target, step),
                dropped=chosen,
                skip_key_inert=skip_key_inert,
            )

        step, candidate = _line_search(
            evaluate, settings.max_step, settings.line_search_iterations
        )
        refinements = 0
        while candidate >= value and refinements < settings.line_search_refinements:
            step, candidate = _line_search(
                evaluate, step, settings.line_search_iterations
            )
            refinements += 1
        timings.record("line_search", time.perf_counter() - started)
        timings.seconds.setdefault("objective_evaluations", 0.0)
        timings.calls["objective_evaluations"] = (
            timings.calls.get("objective_evaluations", 0) + evaluations
        )
        if candidate >= value:
            continue
        accepted_point = _combine(point, vertex, step)
        # THE TAKEN STEP IS RE-FORMED ON THE EXACT ISLAND; its view is what the
        # direct path below evaluates, so the value the iterate carries is the
        # objective at the point it is. Under the exact q rule q is formed
        # below, from the direct path's branch values at the accepted point.
        if q_rule is None:
            accepted_iterate = q_iterate.toward(vertex_q, step)
            accepted_q = accepted_iterate.view
        _check_point(
            parametrization,
            accepted_point,
            settings,
            f"iteration {iteration}",
            residuals_fatal=False,
        )
        # EVERY VALUE AN ITERATE CARRIES COMES FROM THE DIRECT PATH, which
        # forms Phi at the point itself. The interpolated trial value differs
        # from it by rounding only; the step is taken exactly when the direct
        # value improves, which is the rule the loop had before the line
        # search interpolated.
        started = time.perf_counter()
        if q_rule is None:
            accepted_value = joint_objective_value(
                maps,
                accepted_q,
                accepted_point,
                alpha,
                dropped=chosen,
                skip_key_inert=skip_key_inert,
            )
        else:
            exact_q, accepted_value = q_rule.exact_at(
                maps, accepted_point, dropped=chosen, skip_key_inert=skip_key_inert
            )
            accepted_iterate = q_iterate.at(exact_q)
        timings.record("accepted_point_objective", time.perf_counter() - started)
        if accepted_value >= value:
            # The interpolated search found a step the direct path does not
            # confirm. The iterate stays, as it does when the search itself
            # finds nothing; the loop is deterministic, so later iterations
            # repeat this. COUNTED, NOT ACTED ON: the count is a measurement
            # in the timings record and changes no stopping rule or status.
            timings.record("accepted_point_rejected", 0.0)
            continue
        point, q_iterate, value = accepted_point, accepted_iterate, accepted_value
        q = q_iterate.view

    contributing = [entry for entry in gates if entry.contributes]
    bracket = (
        max(entry.linearization for entry in contributing) if contributing else None
    )
    withdrawal = (
        None
        if contributing
        else (
            gates[-1].withdrawal if gates else str(AssuranceReason.ITERATE_NOT_FEASIBLE)
        )
    )
    # THE POINT THE ESTIMATE IS TAKEN AT, MEASURED ONCE AND NEVER FATALLY: the
    # gates measured the points the loop CONSUMED, and a run ending by the
    # iteration limit returns a line-searched point no gate saw. Recorded,
    # never acted on (rem:fo-returned-point).
    returned = _check_point(
        parametrization, point, settings, "returned point", residuals_fatal=False
    )
    if interrupted is not None:
        status = interrupted
    elif withdrawn_at_a_hypothesis:
        status = STATUS_HYPOTHESIS_WITHDRAWN
    elif gap <= settings.gap_tolerance:
        status = "converged"
    else:
        status = "iteration-limit"
    return JointFrankWolfeResult(
        objective=value,
        best_assessment=best_assessment,
        choi=point,
        q=q,
        iterations=iteration,
        gap=gap,
        h_lb=bracket if not chosen else None,
        h_lb_dropped=bracket if chosen else None,
        dropped_set=tuple(sorted(chosen)),
        withdrawal=withdrawal,
        status=status,
        gates=tuple(gates),
        oracle_diagnostics=tuple(diagnostics),
        timings=timings,
        solver_report=solver_report(
            oracle_choice,
            step_rule,
            assignment,
            diagnostics,
            active,
            timings,
            anchor_min_eigenvalue=anchor_min_eigenvalue,
            q_rule=q_rule_name(q_rule),
        ),
        returned_point=returned,
        estimate_point_relaxed_member=returned.established(settings),
        **joint_run_metadata(maps, first_order=bracket is not None),
    )


def _spectral_backend(
    parametrization: JointChoiParametrization, assignment: Mapping[str, str]
) -> LinearOracle | None:
    """Return the closed-form backend when some group is assigned it, probed.

    The probe of spec/architecture.md 7.3 runs on it as on any oracle: its
    declared capabilities must cover a spectraplex subproblem's needs.
    """
    if "spectral" not in assignment.values():
        return None
    backend = SpectralSectorChoiOracle()
    require_capabilities(
        backend.capabilities(),
        SPECTRAPLEX_REQUIREMENTS,
        sector_dims=[
            parametrization.block_dim(pair) for pair in parametrization.joint_sectors
        ],
    )
    return backend


def _search(
    evaluate: Any, upper: float, value: float, settings: FrankWolfeOptions
) -> tuple[float, float]:
    """Return the line search's step and value, refined as the vanilla loop does."""
    step, candidate = _line_search(evaluate, upper, settings.line_search_iterations)
    refinements = 0
    while candidate >= value and refinements < settings.line_search_refinements:
        step, candidate = _line_search(evaluate, step, settings.line_search_iterations)
        refinements += 1
    return step, candidate


def _pairwise_iteration(
    maps: JointMaps,
    layout: FlatLayout,
    active: ActiveSet,
    point: Mapping[JointSector, Matrix],
    q_iterate: AcceptanceIterate,
    value: float,
    vertex: Mapping[JointSector, Matrix],
    vertex_q: AcceptanceVertex,
    gradient_blocks: Mapping[JointSector, Matrix],
    gradient_q: Mapping[str, float],
    anchor_blocks: Any,
    anchor_frequencies: Any,
    anchor_exact: tuple[Fraction, ...] | None,
    alpha: float,
    settings: FrankWolfeOptions,
    chosen: DroppedSet,
    skip_key_inert: bool,
    deficit_pairs: tuple[JointSector, ...],
    timings: StageTimings,
    iteration: int,
    q_rule: BoxPartialMinimum | None = None,
) -> tuple[ActiveSet, dict[JointSector, Matrix], AcceptanceIterate, float] | None:
    """One step of the pairwise rule: the better of a pairwise and a plain step.

    Returns the new active set, iterate, ``q`` and objective, or ``None`` when
    no step is taken. The PAIRWISE direction is ``a_new - a_away`` with the
    largest step ``w_away`` (capped at ``max_step``); the PLAIN direction is
    the vanilla step toward the same new atom, ``a_new - x``, up to
    ``max_step``. Both are line-searched with the interpolated ``Phi`` (``Phi``
    is linear), and the step whose searched value is lower is proposed; the
    plain step is also what is proposed when the pairwise direction gives no
    improvement at all. Every iteration whose TAKEN step is the plain one --
    counted after the direct re-evaluation accepts it -- is COUNTED
    (``pairwise_fallback`` in the timings, ``fallbacks`` in the report).

    WHY BOTH ARE SEARCHED, and not the plain step only when the pairwise one
    fails (measured on decoy BB84 at 10 dB, spectral oracle, 300
    iterations). The pairwise search nearly always finds SOME improvement, so
    a fallback on "no improvement" almost never fires, and a run of swap steps
    between small-weight atoms stalls: 0.0149 against vanilla's 0.0132 at 300
    iterations. Taking the better of the two gave 0.0078 (certified 0.0045
    against vanilla's 0.0031), at about 1.5x the line-search time. The step
    taken searches no higher than the plain step, which is the vanilla step
    toward the SHRUNK atom -- 1e-8 from the vanilla target -- so the rule keeps
    the vanilla loop's per-step decrease approximately, not exactly.

    The proposed iterate is REBUILT from its atoms, checked, and re-evaluated
    by the direct path; the step is taken exactly when that value improves,
    the vanilla loop's rule.

    UNDER THE EXACT q RULE (``q_rule``) the atoms are ``J``-only and both
    searches run on ``g(J) = f(J, q*(J))``: every trial re-minimises ``q``,
    and the accepted iterate's ``q`` is ``q*`` at the rebuilt ``J``, made
    exact (:mod:`~certiqs_key.solvers.frank_wolfe.q_rule`). The away score is
    then ``<grad_J, A_i>`` alone, which is the gradient of ``g`` at the
    iterate (Danskin: ``q_t`` is the partial minimiser, up to the snap).
    """
    started = time.perf_counter()
    evaluations = 0
    q = q_iterate.view
    new_blocks = shrink_blocks(layout, vertex, anchor_blocks)
    new_exact: tuple[Fraction, ...] | None = None
    if vertex_q.exact is not None and anchor_exact is not None:
        # The q half of the new atom, formed EXACTLY: (1 - delta) v + delta q_0
        # with v the exact vertex and q_0 the exact start, both in the set.
        new_exact = shrink_frequencies_exact(
            tuple(vertex_q.exact[chat] for chat in layout.values),
            anchor_exact,
        )
        new_frequencies = np.asarray([float(x) for x in new_exact], np.float64)
    else:
        new_frequencies = shrink_frequencies(
            layout.frequencies(vertex_q.view), anchor_frequencies
        )
    away = active.away_index(
        layout.flatten(gradient_blocks),
        np.asarray([gradient_q.get(chat, 0.0) for chat in layout.values]),
    )
    new_point = layout.unflatten(new_blocks)
    away_point = layout.unflatten(active.blocks[away])
    new_q = dict(zip(layout.values, new_frequencies.tolist(), strict=True))
    away_q = dict(zip(layout.values, active.frequencies[away].tolist(), strict=True))
    statistics_point = joint_statistics(maps, point)
    statistics_new = joint_statistics(maps, new_point)
    statistics_away = joint_statistics(maps, away_point)
    moves = {
        pair: np.asarray(new_point[pair] - away_point[pair], dtype=np.complex128)
        for pair in deficit_pairs
    }

    def pairwise_value(step: float) -> float:
        nonlocal evaluations
        evaluations += 1
        if q_rule is not None:
            return q_rule.objective_at_statistics(
                maps,
                {
                    pair: hermitian_part(
                        np.asarray(point[pair] + step * moves[pair], np.complex128)
                    )
                    for pair in deficit_pairs
                },
                {
                    chat: statistic
                    + step * (statistics_new[chat] - statistics_away[chat])
                    for chat, statistic in statistics_point.items()
                },
                dropped=chosen,
                skip_key_inert=skip_key_inert,
            )
        return joint_objective_value_at_statistics(
            maps,
            {
                chat: (
                    weight
                    if new_q[chat] == away_q[chat]
                    else weight + step * (new_q[chat] - away_q[chat])
                )
                for chat, weight in q.items()
            },
            {
                pair: hermitian_part(
                    np.asarray(point[pair] + step * moves[pair], np.complex128)
                )
                for pair in deficit_pairs
            },
            alpha,
            {
                chat: statistic + step * (statistics_new[chat] - statistics_away[chat])
                for chat, statistic in statistics_point.items()
            },
            dropped=chosen,
            skip_key_inert=skip_key_inert,
        )

    current_blocks = {pair: point[pair] for pair in deficit_pairs}
    target_blocks = {pair: new_point[pair] for pair in deficit_pairs}

    def plain_value(step: float) -> float:
        nonlocal evaluations
        evaluations += 1
        if q_rule is not None:
            return q_rule.objective_at_statistics(
                maps,
                _combine(current_blocks, target_blocks, step),
                _combine_statistics(statistics_point, statistics_new, step),
                dropped=chosen,
                skip_key_inert=skip_key_inert,
            )
        return joint_objective_value_at_statistics(
            maps,
            _combine_q(q, new_q, step),
            _combine(current_blocks, target_blocks, step),
            alpha,
            _combine_statistics(statistics_point, statistics_new, step),
            dropped=chosen,
            skip_key_inert=skip_key_inert,
        )

    upper = min(float(active.weights[away]), settings.max_step)
    pairwise_step, pairwise_candidate = _search(pairwise_value, upper, value, settings)
    plain_step, plain_candidate = _search(
        plain_value, settings.max_step, value, settings
    )
    proposal: ActiveSet | None = None
    plain = False
    if pairwise_candidate < value and pairwise_candidate <= plain_candidate:
        proposal = active.pairwise(
            away, new_blocks, new_frequencies, pairwise_step, new_exact
        )
    elif plain_candidate < value:
        plain = True
        proposal = active.frank_wolfe(
            new_blocks, new_frequencies, plain_step, new_exact
        )
    timings.record("line_search", time.perf_counter() - started)
    timings.seconds.setdefault("objective_evaluations", 0.0)
    timings.calls["objective_evaluations"] = (
        timings.calls.get("objective_evaluations", 0) + evaluations
    )
    if proposal is None:
        return None
    # The exact numbers are kept short, or given up (joint_pairwise).
    shortener = q_iterate.shortener
    proposal = proposal.bounded(None if shortener is None else shortener.shorten)
    rebuilt_blocks, rebuilt_frequencies = proposal.point()
    accepted_point = layout.unflatten(rebuilt_blocks)
    exact_q = proposal.exact_point()
    if q_rule is not None:
        # q*(J) at the rebuilt J, formed below from the direct path's values.
        accepted_iterate = q_iterate
    elif exact_q is not None:
        # sum_i w_i a_i over the rationals: exact weights summing to one, on
        # exact points of the set (Remark rem:acc-side (beta)).
        accepted_iterate = q_iterate.at(dict(zip(layout.values, exact_q, strict=True)))
    elif active.exact_weights is not None:
        # The exact side was given up at this step (ActiveSet.bounded): off
        # the island from here on, fail-closed.
        rebuilt_q = dict(zip(layout.values, rebuilt_frequencies.tolist(), strict=True))
        accepted_iterate = AcceptanceIterate(rebuilt_q, None, False)
    else:
        # No exact atoms: the binary64 rebuild, which keeps the record only
        # where no coordinate moved (a singleton, whose atoms all agree).
        rebuilt_q = dict(zip(layout.values, rebuilt_frequencies.tolist(), strict=True))
        accepted_iterate = AcceptanceIterate(
            rebuilt_q, None, q_iterate.on_island and rebuilt_q == q
        )
    accepted_q = accepted_iterate.view
    _check_point(
        maps.parametrization,
        accepted_point,
        settings,
        f"iteration {iteration}",
        residuals_fatal=False,
    )
    started = time.perf_counter()
    if q_rule is None:
        accepted_value = joint_objective_value(
            maps,
            accepted_q,
            accepted_point,
            alpha,
            dropped=chosen,
            skip_key_inert=skip_key_inert,
        )
    else:
        exact, accepted_value = q_rule.exact_at(
            maps, accepted_point, dropped=chosen, skip_key_inert=skip_key_inert
        )
        accepted_iterate = q_iterate.at(exact)
    timings.record("accepted_point_objective", time.perf_counter() - started)
    if accepted_value >= value:
        timings.record("accepted_point_rejected", 0.0)
        return None
    if plain:
        # Counted only once the direct path has accepted it: a step TAKEN.
        timings.record("pairwise_fallback", 0.0)
    return proposal, accepted_point, accepted_iterate, accepted_value


#: The two values of ``solver_report["q_rule"]``: the closed-form box solve of
#: :mod:`~certiqs_key.solvers.frank_wolfe.q_rule`, or the previous step toward
#: the exact LP vertex (every geometry the box solve does not serve; on a
#: singleton that step never moves ``q``).
Q_RULE_BOX_PARTIAL_MINIMUM = "box-partial-minimum"
Q_RULE_VERTEX_STEP = "vertex-step"


def q_rule_name(q_rule: BoxPartialMinimum | None) -> str:
    """Return the name the record gives the ``q`` rule a run was decided on."""
    return Q_RULE_VERTEX_STEP if q_rule is None else Q_RULE_BOX_PARTIAL_MINIMUM


def solver_report(
    oracle_choice: str,
    step_rule: str,
    assignment: Mapping[str, str],
    diagnostics: Iterable[Mapping[str, Any]],
    active: ActiveSet | None,
    timings: StageTimings,
    *,
    q_rule: str,
    anchor_min_eigenvalue: float | None = None,
) -> dict[str, Any]:
    """Return how the loop ran, for the record. Evidence, never an input.

    The ``q`` rule the acceptance set's geometry selected (``q_rule``:
    ``box-partial-minimum`` or ``vertex-step``, :func:`q_rule_name`); the
    oracle choice and the backend each group was assigned before the loop;
    the calls each backend served; the largest eigen-residual
    ``||C v - lambda v||`` and the largest ``|<C, v v^dagger> - lambda|`` over
    the spectral calls (evidence a reader may weigh; they discharge nothing);
    and, under the pairwise rule, its constants, its fallback count, the
    final number of active atoms and the anchor's smallest block eigenvalue
    (checked positive before the loop).
    """
    calls: dict[str, int] = {}
    residual = 0.0
    consumed = 0.0
    spectral_calls = 0
    for entry in diagnostics:
        name = str(entry.get("backend", "unknown"))
        calls[name] = calls.get(name, 0) + 1
        if name == "spectral":
            spectral_calls += 1
            residual = max(residual, float(entry["eigen_residual"]))
            consumed = max(consumed, abs(float(entry["consumed_minus_eigenvalue"])))
    report: dict[str, Any] = {
        "oracle": oracle_choice,
        "step_rule": step_rule,
        "q_rule": q_rule,
        "oracle_assignment": dict(sorted(assignment.items())),
        "oracle_calls": dict(sorted(calls.items())),
        "spectral_evidence": (
            {
                "calls": spectral_calls,
                "max_eigen_residual": residual,
                "max_abs_consumed_minus_eigenvalue": consumed,
            }
            if spectral_calls
            else None
        ),
        "pairwise": None,
    }
    if step_rule == "pairwise":
        report["pairwise"] = {
            "shrink": PAIRWISE_SHRINK,
            "fold_below": PAIRWISE_FOLD_BELOW,
            # Iterations whose TAKEN step (accepted by the direct path) was
            # the plain Frank-Wolfe step, because it searched lower than the
            # pairwise step or the pairwise direction did not improve.
            "fallbacks": timings.calls.get("pairwise_fallback", 0),
            "active_atoms": None if active is None else active.size,
            "anchor_min_eigenvalue": anchor_min_eigenvalue,
        }
    return report


def first_order_bracket(
    maps: JointMaps,
    q: Mapping[str, float],
    choi: Mapping[JointSector, Matrix],
    alpha: float,
    vertex_q: Mapping[str, float],
    vertex: Mapping[JointSector, Matrix],
    *,
    dropped: DroppedSet = NOTHING_DROPPED,
    skip_key_inert: bool = True,
) -> float:
    """Return ``eq:hlb`` at ONE iterate with ONE given pair ``(v_t, S_t)``.

    The objective at the iterate plus the two linearisation pairings, which is
    the expression ``cor:fo-dropped`` reads as
    ``underline h^{FO,D}_alpha`` when ``D`` is non-empty and
    ``thm:firstorder``'s ``eq:hlb`` when it is empty. A lower bound only where
    the pair satisfies both inequalities of ``eq:lmo``; the engine's own gate
    forms its brackets with the verified feasible side instead
    (``thm:firstorder`` (iv), ``req:verified-feasible-side``). Exposed on its
    own because the expression is a statement about an iterate and a pair and
    not about a loop, and a test can therefore check it without a backend.
    """
    gradient = joint_gradient(
        maps, q, choi, alpha, dropped=dropped, skip_key_inert=skip_key_inert
    )
    objective = joint_objective_value(
        maps, q, choi, alpha, dropped=dropped, skip_key_inert=skip_key_inert
    )
    total = objective
    for pair, block in gradient.blocks.items():
        difference = as_matrix(vertex[pair]) - as_matrix(choi[pair])
        total += float(np.real(np.trace(block @ difference)))
    for chat, slope in gradient.q.items():
        shift = vertex_q[chat] - q[chat]
        if shift != 0.0:
            total += slope * shift
    return total


__all__ = [
    "IterateObserver",
    "JointFrankWolfeResult",
    "JointIterateGate",
    "StageTimings",
    "coupling_residuals",
    "first_order_bracket",
    "hermiticity_defect",
    "joint_gradient",
    "joint_initial_point",
    "joint_label",
    "joint_objective_value",
    "q_rule_name",
    "run_joint_frank_wolfe",
    "solver_report",
]
