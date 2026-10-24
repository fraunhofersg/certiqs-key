"""One finished-run stand-in per route, built from the real emitters, no solve.

WHY THIS EXISTS. The route-exact assumption set
(``certiqs_key.runs.assumptions``) reads a finished run's ledgers and roots; a
finished run needs a QICS solve, and the reconciliation needs none of its
numbers. So each route here is the instance's own ``preparation`` (the device
prologue and the compilation, the code path ``run_slice`` shares), the
statistics ledger the construction map emits for its box
(:func:`certiqs_key.statistics.ledger.assumption_ledger` on
``AcceptanceRoute.CONSTRUCTED_BOX``, with a uniform honest law: the rows do not
depend on the law's values), and the engine's ledger from
:func:`certiqs_key.meat_core.reasons.assumption_ledger` with the flags the
general key-rate result passes it, for one of three outcomes:

* ``key-length``: a first-order bound and a reported length, whose
  certificate names ``[FIRST_ORDER_ROOT, KEY_LENGTH_ROOT]``;
* ``estimate``: no bound and no length, ``[ESTIMATE_ROOT]``;
* ``bound-withheld``: a bound whose length a closed gate withheld,
  ``[ESTIMATE_ROOT, FIRST_ORDER_ROOT]`` .

These are the three outcomes ``GeneralKeyRateResult`` admits; the roots are the
engine's own rule
(:func:`~certiqs_key.solvers.frank_wolfe.general_keyrate.result_claim_roots`),
and a length without a bound is refused there. The engine's bindings are the
engine's own (:func:`~certiqs_key.meat_core.reasons.assumption_bindings` of
:func:`~certiqs_key.solvers.frank_wolfe.general_keyrate.declared_values`), read
off the route's compiled declaration docked and taken through the wire step as
the engine reads it (:func:`docked`), with a dyadic singleton acceptance set
and fixed run parameters: no number is computed from them, and the bindings do
not depend on the law. The stand-in carries the run's
:class:`~certiqs_key.runs.wire.WireLabels` as ``labels``, as a ``SliceResult``
does, so the run tier's join reads the engine's wire IDs back into the declared
spelling exactly as on a real run (a fixture that docked without the wire step
could not see that the engine binds wire IDs).

"""

from __future__ import annotations

import importlib
from fractions import Fraction
from functools import cache
from types import SimpleNamespace
from typing import Any

from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
)
from certiqs_key.meat_core.declaration.general import (
    GeneralDeclaration,
    general_from_accepted,
)
from certiqs_key.meat_core.docking import dock_declaration
from certiqs_key.meat_core.finitekey.result import deductions_of
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.reasons import assumption_bindings, laboratory_parties
from certiqs_key.meat_core.reasons import assumption_ledger as meat_core_ledger
from certiqs_key.runs.general_wire import build_general_bundle
from certiqs_key.runs.pipeline import Preparation, _chain_record_through_weighting
from certiqs_key.runs.wire import WireLabels, build_bundle
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    declared_values,
    result_claim_roots,
)
from certiqs_key.statistics.ledger import AcceptanceRoute
from certiqs_key.statistics.ledger import assumption_ledger as statistics_ledger

#: Route name -> (instance package, device overrides or None). One per route
#: the design names (section 2.5): Band A, the flat reduction (encoded and
#: licensed), the flat reduction with A-EIG not invoked, decoy, and
#: the untrusted two-station route.
_ROUTES: dict[str, tuple[str, dict[str, Any] | None]] = {
    # The direct finite route: Band A, trusted source, d_A = 2, a public
    # choice, no device prologue.
    "band-a": ("bb84", None),
    # The flat reduction (wpfss) with a receiver supplier, encoded route.
    "wpfss-encoded": ("optical_bb84", None),
    # The flat reduction on the licensed route: a constraint list, an
    # attack-set licence.
    "wpfss-licensed": ("optical_bb84", {"route": "licensed"}),
    # No exact window: A-EIG is emitted and not invoked.
    "wpfss-no-window": ("optical_bb84", {"exact_window": None}),
    # The decoy transmitter's tagged source.
    "decoy": ("decoy_bb84", None),
    # Untrusted source at d_A = 1, two stations.
    "untrusted-two-station": ("bbm92", None),
}

ROUTES: tuple[str, ...] = tuple(_ROUTES)
OUTCOMES: tuple[str, ...] = ("key-length", "estimate", "bound-withheld")


@cache
def preparation(route: str) -> tuple[Preparation, Any]:
    """Return the route's preparation and the configuration it prepared."""
    package, device = _ROUTES[route]
    surface = importlib.import_module(f"instances.{package}.surface")
    config = surface.default_config()
    if device is not None:
        merged = {**dict(config.device), **device}
        config = surface.default_config(
            device={key: value for key, value in merged.items() if value is not None}
        )
    prepared = surface.preparation(config)
    assert isinstance(prepared, Preparation), (route, prepared)
    return prepared, config


def statistics_rows(prepared: Preparation, rounds: int) -> tuple[Any, ...]:
    """Return the rows the construction map's box emits for this alphabet."""
    alphabet = tuple(prepared.acceptance_alphabet)
    law = [Fraction(1, len(alphabet))] * len(alphabet)
    return statistics_ledger(
        AcceptanceRoute.CONSTRUCTED_BOX, alphabet=alphabet, rounds=rounds, honest=law
    )


#: The run parameters the docked fixture declarations carry.
PARAMETERS = KeyLengthParameters(
    alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=1_000
)
ROUNDS = 1_000_000


@cache
def wired(route: str) -> tuple[GeneralDeclaration, WireLabels]:
    """Return the route's declaration as the engine reads it, with the wire labels.

    The run tier's docking (``run_slice``: the general docking for a general
    candidate, the accepted one otherwise) with a dyadic singleton
    acceptance set on the route's acceptance alphabet, :data:`ROUNDS` and
    :data:`PARAMETERS`; then ``run_slice``'s wire step: the bundle writer of
    the docked form (``build_bundle`` or ``build_general_bundle``, with the
    chain record read through the compiler's weighting) and
    ``declaration_from_bundle`` on what it built, embedded in the general
    form as the solve embeds it. The bundle is read in memory: ``run_slice``
    also writes it to disk and reads it back, and checks that round trip
    digest-identical, so the disk changes no label. No solve reads it.
    """
    prepared, _ = preparation(route)
    candidate = prepared.declaration
    size = len(prepared.acceptance_alphabet)
    # A DYADIC singleton, which sums to one exactly: the bundle read decides
    # def:admissible-acceptance-set in exact arithmetic, and 1/3 three times
    # does not (the docking alone never decided it).
    frequencies = tuple(
        [2.0 ** -(index + 1) for index in range(size - 1)] + [2.0 ** -(size - 1)]
    )
    acceptance = AcceptanceSet(geometry="singleton", frequencies=frequencies)
    docked_form: Any
    if candidate.is_general_format:
        docked_form = dock_general_candidate(
            candidate,
            acceptance_set=acceptance,
            rounds=ROUNDS,
            parameters=PARAMETERS,
            reduction_chain_record=prepared.compilation.reduction_chain_record,
        )
        writer: Any = build_general_bundle
    else:
        docked_form = dock_declaration(
            candidate, acceptance_set=acceptance, rounds=ROUNDS, parameters=PARAMETERS
        )
        writer = build_bundle
    bundle, labels = writer(
        docked_form,
        alice_announcements=candidate.alice_announcement_alphabet,
        bob_announcements=candidate.bob_announcement_alphabet,
        reduction_chain=_chain_record_through_weighting(
            prepared.compilation.reduction_chain_record,
            prepared.compilation.choice_weightings,
        ),
        created_by="tests/support/route_fixtures",
    )
    reread = declaration_from_bundle(bundle)
    if not isinstance(reread, GeneralDeclaration):
        reread = general_from_accepted(reread)
    return reread, labels


def docked(route: str) -> GeneralDeclaration:
    """Return the route's declaration as the engine reads it (:func:`wired`)."""
    return wired(route)[0]


def meat_core_result(route: str, outcome: str) -> SimpleNamespace:
    """Return the engine result's ledger, bindings, certificate roots and length."""
    reported = outcome == "key-length"
    first_order = outcome in ("key-length", "bound-withheld")
    declaration = docked(route)
    ledger = meat_core_ledger(
        trusted_source=declaration.is_trusted_source,
        alice_dim=declaration.alice_dim,
        alice_party=str(declaration.alice.party),
        constraint_entries=len(declaration.constraint_list),
        key_length_wanted=True,
        key_length_reported=reported,
        first_order=first_order,
    )
    values = declared_values(
        declaration,
        key_length=1 if reported else None,
        eps_auth=0.0,
        k_auth=0,
        ideal_hash=True,
        deductions=deductions_of(
            lambda_ec=PARAMETERS.lambda_ec,
            eps_ev=PARAMETERS.eps_ev,
            eps_pa=PARAMETERS.eps_pa,
            alpha=PARAMETERS.alpha,
            ideal_hash=True,
        ),
    )
    roots = result_claim_roots(
        bound_reported=first_order, dropped=False, key_length_reported=reported
    )
    return SimpleNamespace(
        assumption_ledger=ledger,
        assumption_bindings=assumption_bindings(
            ledger,
            values,
            parties=laboratory_parties(
                trusted_source=declaration.is_trusted_source,
                alice_party=str(declaration.alice.party),
                key_length_reported=reported,
                first_order=first_order,
            ),
        ),
        certificate={"claim_roots": roots},
        key_length=1 if reported else None,
    )


def route_result(route: str, outcome: str = "key-length") -> SimpleNamespace:
    """Return a finished-run stand-in: what the adapters read of a SliceResult."""
    prepared, config = preparation(route)
    return SimpleNamespace(
        labels=wired(route)[1],
        compilation=prepared.compilation,
        specification=prepared.specification,
        receiver_artifact=prepared.receiver_artifact,
        reduction_artifact=prepared.reduction_artifact,
        device_artifacts=prepared.device_artifacts,
        acceptance=SimpleNamespace(
            assumption_ledger=statistics_rows(prepared, config.rounds)
        ),
        key_rate=meat_core_result(route, outcome),
    )
