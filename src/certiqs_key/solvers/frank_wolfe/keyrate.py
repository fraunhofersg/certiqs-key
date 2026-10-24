"""End to end: an operator bundle or a declaration in, the general record out.

The run in order: bundle validation (spec/architecture.md 3.6), the capability
probe (7.3), the joint sector-Choi problem and the ONE Frank-Wolfe loop (7.2),
and a result whose tier is the one the checks support and never a stronger one
(2.5, 2.8).

ONE DRIVER. A declaration
of the accepted format is the degenerate case of the general format entry for
entry (``def:declaration``'s general-format paragraph), and
``frank-wolfe/rem:fo-general-format`` (1) states that ``thm:firstorder`` holds
as written there. So an accepted-format declaration is embedded by
:func:`~certiqs_key.meat_core.declaration.general.general_from_accepted` and
runs on :func:`~certiqs_key.solvers.frank_wolfe.joint_driver.run_joint_frank_wolfe`,
the loop every declaration runs, and its result is the general record
(:class:`~certiqs_key.solvers.frank_wolfe.general_keyrate.GeneralKeyRateResult`).

THE ORCHESTRATION LIVES UNDER ``solvers/`` AND THAT IS A LAYERING CHOICE: this
package already imports :mod:`certiqs_key.meat_core.objective`, and putting the
assembly the other way round would make the two packages import each other at
module load. ``solvers`` is the SUBMODULE's code (core = program + formulation;
submodule frank-wolfe) and is REMOVABLE like any submodule declared so: deleting
it leaves a core that states the program, solves nothing and reports the
estimate at a point somebody else supplies. The two docking claims,
``lem:estimate`` and ``cor:keylength-bound``, are what make that a coherent
contract rather than a gap.

WHAT THE RETURNED ``h_low`` IS
==============================
The value of the objective at the point the optimiser returned. Every point of
``Qacc x Feas`` has objective value at least ``h_low``, so the reported number
is an UPPER estimate of the value and nothing says how far above it lies
(``lem:estimate``). The point is established only in the RELAXED set
(``frank-wolfe/rem:feas-tol``), so what a run is in is
``frank-wolfe/thm:firstorder`` (iiia): THE REPORTED NUMBER IS NOT ESTABLISHED
TO LIE ON EITHER SIDE OF ``h_low``.

THE TIER IS ACHIEVED AND NEVER REQUESTED
========================================
Both live numbers are reported on every run (spec/architecture.md 2.8;
``frank-wolfe/rem:fo-interface``): ``h_low`` is the objective at the
returned point, ``h_lb`` the bracket, present when every hypothesis held and
absent with a machine-readable reason otherwise, and ``reported_tier`` names
which one carries the claim. A comparison of the two is a diagnostic and never
an assertion (``frank-wolfe/rem:fo-arithmetic`` (b)); both are on the record.

DECLARED DATA IS EXACTLY ADMISSIBLE OR THE RUN IS REFUSED
=========================================================
No entry point below takes a tolerance (spec/architecture.md 2.8). The
security-statement gate and the exact admission of ``def:declaration`` are
decided FIRST, before the capability probe and before any numerical work, so
a declaration whose blocks are not exactly Hermitian and exactly positive
semidefinite never reaches ``sqrt(F_v)``.

ONLY A COMPILED DECLARATION GETS A KEY LENGTH
=============================================
``meat-core/req:compiled-declaration-only``: :func:`solve` and
:func:`solve_bundle` take ``compiled``, the run tier's in-memory token that the
protocol compiler emitted the declaration
(:class:`~certiqs_key.meat_core.provenance.CompilerEmission`). The bundle
carries no such datum and its format is unchanged, so the run tier, which
compiles, writes the bundle and reads it back, passes the token beside the
bundle it reread. Without the token the length is withheld
(``declaration_not_compiled``) and every other number is reported.
:func:`solve_declaration` returns raw solver numbers and no length, and takes
none.

THE KEY LENGTH COMES FROM ANY LOWER BOUND
=========================================
``cor:keylength-bound`` is the warrant: for ANY ``h <= h_low`` the key-length
expression of ``thm:keylength`` holds with ``max{0, h}`` in place of ``h_low``.
What this submodule supplies is the instance ``h = h_lb``
(``frank-wolfe/cor:fo-keylength``,
:func:`~certiqs_key.solvers.frank_wolfe.general_keyrate.key_length_from_first_order`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from certiqs_key.domain.bundle import OperatorBundle
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.declaration.general import (
    GeneralDeclaration,
    general_from_accepted,
)
from certiqs_key.meat_core.declaration.validation import validate_declaration
from certiqs_key.meat_core.finitekey.consistency import DivergenceBound
from certiqs_key.meat_core.finitekey.keylength import (
    check_authentication_parameters,
    check_security_statement,
)
from certiqs_key.meat_core.provenance import CompilerEmission
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    GeneralKeyRateResult,
    NegativeObjectiveError,
    solve_general,
    solve_general_declaration,
)
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    IterateObserver,
    JointFrankWolfeResult,
)
from certiqs_key.solvers.oracles.protocol import LinearOracle
from certiqs_key.solvers.types import SearchRequest

if TYPE_CHECKING:
    from certiqs_key.protocol_compiler.companion import CompiledReferenceCompanion

__all__ = [
    "NegativeObjectiveError",
    "bound_minimal_divergence_of_bundle",
    "general_declaration_of",
    "solve",
    "solve_bundle",
    "solve_declaration",
]


def general_declaration_of(
    declaration: ProtocolDeclaration | GeneralDeclaration,
    *,
    eps_auth: float = 0.0,
) -> GeneralDeclaration:
    """Return the general declaration a run solves, after the accepted gates.

    An accepted-format declaration is decided BY ITS OWN RULES FIRST -- the
    security-statement corner and every Group A row of ``validate_declaration``
    -- and only then embedded: a declaration that did not come through a bundle
    would otherwise reach the program with rows undecided. A general
    declaration is decided by the general validator the solve calls.
    ``eps_auth`` is the run's A-AUTH error bound (default 0), which the corner
    of ``req:security-statement-not-vacuous`` counts twice.
    """
    if isinstance(declaration, GeneralDeclaration):
        return declaration
    check_security_statement(
        declaration.parameters.eps_pa, declaration.parameters.eps_ev, eps_auth
    )
    validate_declaration(declaration)
    return general_from_accepted(declaration)


def solve_declaration(
    declaration: ProtocolDeclaration | GeneralDeclaration,
    oracle: LinearOracle,
    *,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    observer: IterateObserver | None = None,
) -> JointFrankWolfeResult:
    """Run the Frank-Wolfe loop on a validated declaration; raw solver numbers.

    ``alpha`` defaults to the declared key-length parameter; an explicit value
    is permitted anywhere in the structural domain ``(1, inf)`` of
    ``meat-core/req:objective-alpha-domain``, and the key-length gate
    downstream confines a KEY-LENGTH statement to ``(1, 2)``
    (``meat-core/req:key-length-alpha-domain``). The gates of
    :func:`general_declaration_of` run here too, because this entry point
    returns raw numbers and a caller must not reach the loop by taking the door
    that computes no key length.
    """
    return solve_general_declaration(
        general_declaration_of(declaration),
        oracle,
        alpha=alpha,
        options=options,
        request=request,
        observer=observer,
    )


def solve_bundle(
    bundle: OperatorBundle,
    oracle: LinearOracle,
    *,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
    observer: IterateObserver | None = None,
    compiled: CompilerEmission | None = None,
    companion: CompiledReferenceCompanion | None = None,
    certification_withheld: tuple[str, ...] = (),
    strict_snaps: bool = False,
) -> GeneralKeyRateResult:
    """Return the result record of a serialized operator bundle.

    The exact admission reaches the declared family TWICE -- once at bundle
    validation and once inside :func:`solve` -- and the two are the same call
    on the same numbers, so the verdict cannot differ between the file path
    and the in-memory path.

    ``compiled`` is the run tier's token that the compiler emitted the
    declaration this bundle carries (``req:compiled-declaration-only``);
    without it no key length is reported. ``companion`` is the compiled
    reference companion beside it, evaluation-only and never in the bundle
    (``protocol-compiler/req:reference-companion-compiled`` (iv)); see
    :func:`~certiqs_key.solvers.frank_wolfe.general_keyrate.solve_general`,
    as for ``strict_snaps``, the run option of
    ``foundations/req:snap-reference`` (iv), which keeps the certified
    evaluation's fallback from running.
    """
    return solve(
        declaration_from_bundle(bundle),
        oracle,
        alpha=alpha,
        options=options,
        request=request,
        ideal_hash=ideal_hash,
        eps_auth=eps_auth,
        k_auth=k_auth,
        observer=observer,
        compiled=compiled,
        companion=companion,
        certification_withheld=certification_withheld,
        strict_snaps=strict_snaps,
    )


def bound_minimal_divergence_of_bundle(
    bundle: OperatorBundle,
    oracle: LinearOracle,
    *,
    alpha_0: float,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    eps_auth: float = 0.0,
) -> DivergenceBound:
    """``meat-core/req:unreachable-acceptance-set`` (i), (ii) on a bundle's declaration.

    The declaration the run searches is the one :func:`solve_bundle` reads off
    the same bundle, behind the same gates
    (:func:`general_declaration_of`); the solve is
    :func:`~certiqs_key.solvers.frank_wolfe.minimal_divergence.bound_minimal_divergence`.
    """
    from certiqs_key.solvers.frank_wolfe.minimal_divergence import (
        bound_minimal_divergence,
    )

    check_authentication_parameters(eps_auth, 0)
    return bound_minimal_divergence(
        general_declaration_of(declaration_from_bundle(bundle), eps_auth=eps_auth),
        oracle,
        alpha_0=alpha_0,
        request=request,
        options=options,
        eps_auth=eps_auth,
    )


def solve(
    declaration: ProtocolDeclaration | GeneralDeclaration,
    oracle: LinearOracle,
    *,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    ideal_hash: bool = True,
    eps_auth: float = 0.0,
    k_auth: int = 0,
    observer: IterateObserver | None = None,
    compiled: CompilerEmission | None = None,
    companion: CompiledReferenceCompanion | None = None,
    certification_withheld: tuple[str, ...] = (),
    strict_snaps: bool = False,
) -> GeneralKeyRateResult:
    """Return the result record of a declaration, on the one driver.

    IT TAKES NO TOLERANCE AND SERVES NO TIER REQUEST: declared data is exactly
    admissible or the run is refused, and the tier is ACHIEVED.

    ``compiled`` is the run tier's token that the protocol compiler emitted
    the declaration (``req:compiled-declaration-only``). Without it the key
    length is WITHHELD, with a reason opening ``declaration_not_compiled``,
    and nothing else changes; a withholding is not a refusal.

    ``observer`` is called once per iterate with ``(k, gap)``
    (:data:`~certiqs_key.solvers.frank_wolfe.joint_driver.IterateObserver`);
    it cannot change the outcome.

    Raises:
        SecurityStatementVacuousError: on ``eps_PA + eps_EV + 2 eps_auth >= 1``,
            the first thing decided after A-AUTH's two parameter domains.
        ValueError: on an ``eps_auth`` outside ``[0, 1)`` or a ``k_auth`` that
            is not a non-negative integer.
        DeclarationError: on a datum missing or outside its domain.
        AdmissionError: on a declared family, marginal or constraint operator
            that is not exactly admissible. NO RESULT OF ANY KIND is produced.
        NegativeObjectiveError: on a negative computed estimate, which is
            never clamped.
    """
    # A-AUTH's two parameters are decided before anything else, the error
    # bound's domain and k_auth's here and the corner they enter next
    # (req:security-statement-not-vacuous), so a bad one is refused before any
    # validation of the declaration.
    check_authentication_parameters(eps_auth, k_auth)
    return solve_general(
        general_declaration_of(declaration, eps_auth=eps_auth),
        oracle,
        alpha=alpha,
        options=options,
        request=request,
        ideal_hash=ideal_hash,
        eps_auth=eps_auth,
        k_auth=k_auth,
        observer=observer,
        compiled=compiled,
        companion=companion,
        certification_withheld=certification_withheld,
        strict_snaps=strict_snaps,
    )
