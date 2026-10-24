"""Preparation shared by all candidate-search methods within frank-wolfe's contract."""

from __future__ import annotations

import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, cast

import numpy as np

from certiqs_key.meat_core.acceptance.box import CanonicalBox, canonical_box
from certiqs_key.meat_core.acceptance.geometry import (
    minimal_acceptance_support,
    polytope_of,
    polytope_support_and_exact_start,
)
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.declaration.general_validation import (
    validate_general_declaration,
)
from certiqs_key.meat_core.declaration.validation import validate_acceptance_set
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.finitekey.keylength import check_security_statement
from certiqs_key.meat_core.objective.joint import (
    DroppedSet,
    JointMaps,
    JointSector,
    build_joint_maps,
    joint_choi_parametrization,
    normalise_dropped_set,
)
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.capabilities.probe import (
    SECTOR_CHOI_REQUIREMENTS,
    Capability,
    require_capabilities,
)
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    _check_point,
    _oracle_vertex,
    _spectral_backend,
    joint_initial_point,
)
from certiqs_key.solvers.frank_wolfe.joint_options import (
    joint_choices,
    oracle_assignment,
    warm_start_point,
)
from certiqs_key.solvers.oracles.acceptance import (
    AcceptanceOracle,
    ExactAcceptanceOracle,
    SingletonAcceptanceOracle,
    acceptance_oracle,
)
from certiqs_key.solvers.oracles.joint_rows import PrebuiltRows, prebuilt_rows
from certiqs_key.solvers.oracles.protocol import LinearOracle
from certiqs_key.solvers.types import SEARCH_METHODS, SearchRequest


@dataclass(frozen=True)
class PreparedProblem:
    """A single target problem; bounds never cross these per-solve objects."""

    maps: JointMaps
    oracle: LinearOracle
    acceptance: AcceptanceOracle
    alpha: float
    anchor: Mapping[JointSector, Matrix]
    initial: Mapping[JointSector, Matrix]
    settings: FrankWolfeOptions
    dropped: DroppedSet
    assignment: Mapping[str, str]
    spectral: LinearOracle | None
    rows: Mapping[str, PrebuiltRows] | None
    skip_key_inert: bool = True
    preparation_seconds: float = 0.0
    capabilities: Mapping[str, Any] = field(default_factory=dict)
    search_method: str | None = None


def prepared_from_maps(
    maps: JointMaps,
    oracle: LinearOracle,
    acceptance: AcceptanceOracle,
    alpha: float,
    options: FrankWolfeOptions | None = None,
    *,
    dropped: Iterable[tuple[str, JointSector]] | None = None,
    start: Mapping[JointSector, Matrix] | None = None,
    search_method: str | None = None,
) -> PreparedProblem:
    """Resolve structural dispatch and starts once, preserving seed refusals."""
    if search_method is not None and search_method not in SEARCH_METHODS:
        raise ValueError(f"unknown prepared search method {search_method!r}")
    started = time.perf_counter()
    settings = options or FrankWolfeOptions()
    choice, _, warm = joint_choices(settings)
    if start is not None and warm is not None:
        raise ValueError("a run takes an explicit start or a warm start, not both")
    assignment = oracle_assignment(maps.parametrization, choice)
    spectral = _spectral_backend(maps.parametrization, assignment)
    rows = (
        prebuilt_rows(maps.parametrization)
        if maps.declaration.is_trusted_source
        else None
    )
    if start is not None and search_method in ("fw", "pairwise"):
        # An explicit FW replay uses its supplied start as the anchor. The
        # old driver never called an unused zero-cost oracle in this case.
        anchor = dict(start)
    else:
        anchor = joint_initial_point(maps.parametrization)
        if maps.declaration.constraint_list:
            zero = {pair: np.zeros_like(block) for pair, block in anchor.items()}
            # Preserve the original preparation call: the zero-cost anchor
            # uses the supplied backend, before gradient-oracle dispatch.
            anchor, _ = _oracle_vertex(maps, oracle, zero, [])
    point = dict(start) if start is not None else anchor
    if warm is not None:
        point = warm_start_point(maps.parametrization, warm, anchor, settings)
    _check_point(maps.parametrization, point, settings, "starting point")
    geometry = (
        "singleton"
        if isinstance(acceptance, SingletonAcceptanceOracle)
        else "box"
        if hasattr(acceptance, "box")
        else "polytope"
    )
    return PreparedProblem(
        maps,
        oracle,
        acceptance,
        alpha,
        anchor,
        point,
        settings,
        normalise_dropped_set(maps, dropped),
        assignment,
        spectral,
        rows,
        preparation_seconds=time.perf_counter() - started,
        search_method=search_method,
        capabilities={
            "source_mode": str(maps.declaration.source_mode),
            "acceptance": geometry,
            "extra_rows": bool(maps.declaration.constraint_list),
            "block_dimensions": [
                maps.parametrization.block_dim(pair)
                for pair in maps.parametrization.joint_sectors
            ],
        },
    )


def prepare_problem(
    declaration: GeneralDeclaration,
    oracle: LinearOracle,
    *,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    dropped: Iterable[tuple[str, JointSector]] | None = None,
    start: Mapping[JointSector, Matrix] | None = None,
) -> PreparedProblem:
    """Validate the declaration and prepare the target with original admission."""
    from dataclasses import replace

    if request is not None:
        if options is not None:
            raise ValueError("supply request or internal replay options, not both")
        options = request.fw_options()
    started = time.perf_counter()
    maps, acceptance = _prepare_general(declaration, oracle)
    result = prepared_from_maps(
        maps,
        oracle,
        acceptance,
        declaration.parameters.alpha if alpha is None else alpha,
        options,
        dropped=dropped,
        start=start,
        search_method=(request or SearchRequest.from_options(options)).method,
    )
    return replace(result, preparation_seconds=time.perf_counter() - started)


@dataclass(frozen=True)
class _PreparedAcceptanceStart:
    """One solve's unchanged oracle with its already-computed starting point.

    An :class:`~certiqs_key.solvers.oracles.acceptance.ExactAcceptanceOracle`:
    the start is kept EXACT (``exact_frequencies``, Remark ``rem:acc-side``
    (alpha)) and ``frequencies`` is its rounding, and the exact vertex is the
    wrapped polytope oracle's.
    """

    oracle: ExactAcceptanceOracle
    frequencies: Mapping[str, float]
    exact_frequencies: Mapping[str, Fraction]

    @property
    def exact_island(self) -> bool:
        # The protocol's flag, read ONCE, by AcceptanceIterate.start, as the
        # record of q_0; every later gate records the driver's own iterate
        # (acceptance_iterate), not this property.
        return self.oracle.exact_island

    def start(self) -> dict[str, float]:
        return dict(self.frequencies)

    def minimize(self, gradient: Mapping[str, float]) -> dict[str, float]:
        return self.oracle.minimize(gradient)

    def exact_start(self) -> dict[str, Fraction]:
        return dict(self.exact_frequencies)

    def exact_minimize(self, gradient: Mapping[str, float]) -> dict[str, Fraction]:
        return self.oracle.exact_minimize(gradient)

    def exact_contains(self, point: Mapping[str, Fraction]) -> bool:
        return self.oracle.exact_contains(point)


@dataclass(frozen=True)
class _CanonicalBoxAcceptance(_PreparedAcceptanceStart):
    """General-only fast LP; legacy oracle construction remains unchanged.

    Exposing ``box`` and ``values`` is also what selects the loop's exact
    ``q`` rule (:func:`~certiqs_key.solvers.frank_wolfe.q_rule.q_rule_for`):
    this oracle is built exactly when ``canonical_box`` recognises the
    declared set, so the selection reads the geometry and nothing else.
    """

    box: CanonicalBox
    values: tuple[str, ...]

    def minimize(self, gradient: Mapping[str, float]) -> dict[str, float]:
        result = self.box.minimum(tuple(gradient[value] for value in self.values))
        if result is None:
            return self.oracle.minimize(gradient)
        return dict(zip(self.values, (float(v) for v in result.argmin), strict=True))

    def exact_minimize(self, gradient: Mapping[str, float]) -> dict[str, Fraction]:
        result = self.box.minimum(tuple(gradient[value] for value in self.values))
        if result is None:
            return self.oracle.exact_minimize(gradient)
        return dict(zip(self.values, result.argmin, strict=True))


def _prepare_general(
    d: GeneralDeclaration,
    oracle: LinearOracle,
    *,
    eps_auth: float = 0.0,
) -> tuple[JointMaps, AcceptanceOracle]:
    # req:security-statement-not-vacuous, first: the corner is decided on the
    # declared budgets and the run's authentication error bound (A-AUTH,
    # default 0, at which it is the two-budget rule), before any program.
    check_security_statement(d.parameters.eps_pa, d.parameters.eps_ev, eps_auth)
    validate_general_declaration(d)
    if d.rounds < 1 or d.key_value_count < 1:
        raise DeclarationError("rounds and key_value_count must be positive")
    # These routines read only the shared acceptance_set/acceptance_values
    # fields, never an operator or a source mode. Reuse the exact
    # def:admissible-acceptance-set check.
    acceptance_view = cast(ProtocolDeclaration, d)
    validate_acceptance_set(acceptance_view)
    p = joint_choi_parametrization(d)
    required = set(SECTOR_CHOI_REQUIREMENTS)
    if d.constraint_list:
        required.add(Capability.INEQUALITY_ROWS)
    require_capabilities(
        oracle.capabilities(),
        required,
        sector_dims=[p.block_dim(pair) for pair in p.joint_sectors],
    )
    acceptance = acceptance_oracle(acceptance_view)
    data = polytope_of(d.acceptance_set)
    if data is None:
        support = minimal_acceptance_support(acceptance_view)
    else:
        if not isinstance(acceptance, ExactAcceptanceOracle):  # pragma: no cover
            raise TypeError("a polytope's acceptance oracle hands out exact points")
        box = canonical_box(data)
        prepared = (
            polytope_support_and_exact_start(data)
            if box is None
            else box.support_and_exact_start()
        )
        if prepared is None:
            raise DeclarationError("the declared polytope has no starting point")
        indices, exact_start = prepared
        support = tuple(d.acceptance_values[index] for index in indices)
        exact_frequencies = dict(zip(d.acceptance_values, exact_start, strict=True))
        start_frequencies = {
            chat: float(value) for chat, value in exact_frequencies.items()
        }
        acceptance = (
            _PreparedAcceptanceStart(acceptance, start_frequencies, exact_frequencies)
            if box is None
            else _CanonicalBoxAcceptance(
                acceptance,
                start_frequencies,
                exact_frequencies,
                box,
                d.acceptance_values,
            )
        )
    return build_joint_maps(p, acceptance_support=support), acceptance
