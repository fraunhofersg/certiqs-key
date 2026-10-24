"""Every ledger row agrees with the claim closure of the results it serves.

WHY THIS EXISTS. A test fails when ledger rows and closure disagree. At
runtime a disagreement is recorded and the run goes on (listing an extra
premise is the safe direction, and refusing a key rate over bookkeeping is
not); here it is fatal. Real emitters, the real shipped table, no solve:

* **meat-core**: every flag combination of its ``assumption_ledger``, against
  the closure of the meat-core roots that combination implies (the roots the
  general key-rate result names, plus the three properties on a length);
* **statistics**: the rows of each acceptance route, against that route's roots;
* **receiver**: every row, against both emission corollaries;
* **compiler, transmitter, receiver, reductions, statistics on each route**:
  the module's rows against the roots each row is attributed to on that
  route: the module's own, and for a row it carries for another module's
  result (``runs.assumptions.CARRIED_ROWS``) that module's too;
* **each route and outcome as a whole**: no discrepancy of any kind, and in
  particular no closure member that no module which ran could emit.

EVERY TEST HERE IS HARD. The inherited A-TSM row is dropped, A-KEYREG and
A-HASH are emitted only with a length, the inherited A-ATK, A-SRC, A-RHOM and
A-SEQ only with a bound or a length, and the result names the first-order root
whenever it reports a bound. A new disagreement is a strict xfail naming its
fix, or it is fixed.
"""

from __future__ import annotations

import itertools
from fractions import Fraction

import pytest
from tests.support.route_fixtures import OUTCOMES, ROUTES, route_result

from certiqs_key.domain.claim_closure import (
    claim_closure,
    roots_of_module,
    short_id_of,
)
from certiqs_key.meat_core.reasons import assumption_ledger
from certiqs_key.runs.assumptions import (
    CARRIED_ROWS,
    STATISTICS_ROOTS,
    DiscrepancyKind,
    EmittedRow,
    attribution_roots,
    emitted_rows,
    meat_core_roots,
    route_exact_assumptions,
    run_claim_roots,
)
from certiqs_key.solvers.frank_wolfe.general_keyrate import result_claim_roots
from certiqs_key.statistics.ledger import AcceptanceRoute
from certiqs_key.statistics.ledger import assumption_ledger as statistics_ledger

pytestmark = pytest.mark.contract


def _premises_outside(
    roots: dict[str, tuple[str, ...]], rows: list[EmittedRow]
) -> tuple[str, ...]:
    found = route_exact_assumptions(roots, rows)
    return found.kinds(DiscrepancyKind.EMITTED_NOT_IN_CLOSURE)


# ===========================================================================
#  meat-core: every flag combination
# ===========================================================================


def _meat_core_cases() -> list[object]:
    cases = []
    for trusted, alice_dim, entries, wanted, reported, first_order, dropped in (
        itertools.product(
            (True, False), (1, 2), (0, 1), (True, False), (True, False),
            (True, False), (True, False),
        )
    ):
        if reported and not first_order:
            continue  # GeneralKeyRateResult refuses a length without its bound
        if dropped and not first_order:
            continue  # a dropped program names its root only with a bound
        cases.append(
            pytest.param(
                trusted, alice_dim, entries, wanted, reported, first_order, dropped,
                id=f"trusted{trusted:d}-dA{alice_dim}-m{entries}-wanted{wanted:d}"
                f"-length{reported:d}-bound{first_order:d}-dropped{dropped:d}",
            )
        )
    return cases


@pytest.mark.parametrize(
    ("trusted", "alice_dim", "entries", "wanted", "reported", "first_order", "dropped"),
    _meat_core_cases(),
)
def test_meat_core_rows_lie_in_the_closure_of_its_roots(
    trusted: bool, alice_dim: int, entries: int, wanted: bool, reported: bool,
    first_order: bool, dropped: bool,
) -> None:
    keys = assumption_ledger(
        trusted_source=trusted,
        alice_dim=alice_dim,
        alice_party="A",
        constraint_entries=entries,
        key_length_wanted=wanted,
        key_length_reported=reported,
        first_order=first_order,
    )
    # The roots general_keyrate's certificate names for this outcome: the
    # engine's own rule, the first-order root whenever a bound is reported.
    claim = result_claim_roots(
        bound_reported=first_order, dropped=dropped, key_length_reported=reported
    )
    roots = {"meat-core": meat_core_roots(claim, key_length_reported=reported)}
    rows = [EmittedRow(machine_key=key, emitted_by="meat-core") for key in keys]
    assert _premises_outside(roots, rows) == ()
    # And the other direction, on the engine alone: every premise of those
    # roots that the engine can emit is emitted, except where the declared
    # data disengage it (A-ATK at an empty list or with no length wanted,
    # A-SRC outside trusted-source mode at d_A >= 2). A-ENS is the
    # transmitter's row, which no engine-only run has.
    found = route_exact_assumptions(roots, rows)
    unemitted = {item.short_id for item in found.not_engaged}
    disengaged = set()
    if not (entries >= 1 and wanted):
        disengaged.add("A-ATK")
    if not (trusted and alice_dim >= 2):
        disengaged.add("A-SRC")
    # A-LAB without a length only in trusted-source mode, at the party of A
    # (its own emission rule): the closure does
    # not see the mode, thm:accumulated-entropy uses it in that mode only.
    if not reported and not trusted:
        disengaged.add("A-LAB")
    assert unemitted <= disengaged, unemitted - disengaged
    # The compiler's A-LINK, A-SPEC and A-ALICE-MEAS are premises of
    # thm:keylength, so the closure of a reported length holds them; they are
    # no row of the engine (the meat-core interface's a_link_note and
    # a_spec_note), and the compiler's own ledger, which no engine-only run
    # has, carries them.
    compiler_premises = {"A-LINK", "A-SPEC", "A-ALICE-MEAS"} if reported else set()
    no_emitter = set(found.kinds(DiscrepancyKind.IN_CLOSURE_NO_EMITTER))
    assert no_emitter - {"A-ENS"} == compiler_premises


# ===========================================================================
#  statistics and receiver, against their own roots
# ===========================================================================


@pytest.mark.parametrize("route", list(AcceptanceRoute))
def test_statistics_rows_lie_in_the_closure_of_the_route_s_roots(
    route: AcceptanceRoute,
) -> None:
    alphabet = ("ok", "err", "disc")
    rows = [
        EmittedRow(
            machine_key=row.machine_key,
            emitted_by="statistics",
            short_id=row.assumption_id,
            bindings=row.constrains,
        )
        for row in statistics_ledger(
            route, alphabet=alphabet, rounds=100, honest=[Fraction(1, 3)] * 3
        )
    ]
    roots = {"statistics": STATISTICS_ROOTS[route]}
    found = route_exact_assumptions(roots, rows)
    assert found.discrepancies == ()
    # And nothing the closure holds is left unemitted by the module.
    assert found.not_engaged == ()


@pytest.mark.parametrize(
    "root",
    # The probe-conditioned corollary is read from the table, which carries it
    # only while the removable probe-conditioning submodule is in the tree.
    [
        "receiver/cor:emitted-unconditioned",
        *roots_of_module("receiver/probe-conditioning"),
    ],
)
def test_every_receiver_row_lies_in_the_closure_of_either_corollary(root: str) -> None:
    result = route_result("wpfss-encoded")
    rows = [row for row in emitted_rows(result) if row.emitted_by == "receiver"]
    emitted = {row.short_id for row in rows}
    assert emitted <= set(claim_closure(root)["assumptions"])
    assert _premises_outside({"receiver": (root,)}, rows) == ()


# ===========================================================================
#  Each module on each route, against the roots its rows are attributed to
# ===========================================================================

MODULES = ("protocol-compiler", "transmitter", "receiver", "reductions", "statistics")


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("module", MODULES)
def test_each_module_s_rows_lie_in_the_closure_of_the_roots_they_serve(
    route: str, module: str
) -> None:
    """Row by row: the module's own roots, and a carrying module's for a carried row.

    The compiler's A-RECV (every route but Band A) is the one carried row the
    shipped routes emit: no compiler result assumes it, and the reductions
    results that rest on a supplied receiver artefact do.
    """
    result = route_result(route)
    roots = run_claim_roots(result)
    rows = [row for row in emitted_rows(result) if row.emitted_by == module]
    if module not in roots:
        assert rows == []
        return
    assert rows, f"{module} ran on {route} and emitted nothing"
    outside = [
        row.machine_key
        for row in rows
        if _premises_outside(
            {module: attribution_roots(module, short_id_of(row.machine_key), roots)},
            [row],
        )
    ]
    assert outside == []


@pytest.mark.parametrize("route", ROUTES)
def test_a_carried_row_is_outside_the_closure_of_its_emitter_s_own_roots(
    route: str,
) -> None:
    """Every entry of CARRIED_ROWS is needed: the emitter's own roots lack it.

    Were a compiler result to assume A-ALICE-MEAS or A-RECV again, the entry
    would attribute a row the module's own closure already holds, and this
    test asks for it to go.
    """
    roots = run_claim_roots(route_result(route))
    for module, carried in CARRIED_ROWS.items():
        own = {
            short_id
            for root in roots.get(module, ())
            for short_id in claim_closure(root)["assumptions"]
        }
        assert set(carried).isdisjoint(own), (module, set(carried) & own)


# ===========================================================================
#  Each route as a whole
# ===========================================================================


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("outcome", OUTCOMES)
def test_the_route_exact_set_has_no_discrepancy(route: str, outcome: str) -> None:
    result = route_result(route, outcome)
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    assert [(item.short_id, str(item.kind)) for item in found.discrepancies] == []


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("outcome", OUTCOMES)
def test_no_closure_member_lacks_an_emitter(route: str, outcome: str) -> None:
    """Hard on every route: nothing the run rests on is outside every ledger."""
    result = route_result(route, outcome)
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    assert found.kinds(DiscrepancyKind.IN_CLOSURE_NO_EMITTER) == ()


# ===========================================================================
#  The exact not-engaged set per route
# ===========================================================================

#: PER ROUTE, every ``(short id, module, discharged)`` listed as not engaged,
#: the same for every outcome. Hand-written, each against the antecedent of
#: the statement that keeps the row out (the emitting module's
#: ``emission_rule``, the receiver's conditional invocation, or the claim
#: that discharges it):
#:
#: * A-ALICE-MEAS (compiler) where a key length is reported
#:   (:data:`_LENGTH_ONLY`): "wherever no source-replacement certificate is
#:   demanded (untrusted-source mode, or d_A = 1)"; every trusted route at
#:   d_A >= 2 demands one, and the untrusted route has one letter. It is in
#:   the closure only through meat-core/thm:keylength, cor:keylength-bound and
#:   cor:composed-security, the roots of a reported length: no compiler result
#:   assumes it (the compiler carries the row for meat-core, CARRIED_ROWS).
#: * A-ATK (compiler, meat-core): emitted only with m >= 1; every route but
#:   the licensed one has an empty constraint list (on Band A, thm:band-a
#:   (iii): "the attack-set licence is not invoked").
#: * A-LINK on Band A: discharged by thm:band-a (v) (``DISCHARGED_ON_ROUTE``).
#:   A-PRESENT is no assumption: def:well-formed-spec (iv), decided on every
#:   route.
#: * A-LINK (compiler) where the one receiver segment is the single exact
#:   instance link of this run's flat-instance reductions artefact, with the
#:   identity outcome correspondence and no source segment
#:   (req:link-row-provenance (ii); the run passes ``chain_provenance``): the
#:   three one-station wpfss routes, the licensed one included, whose chain
#:   carries no domination link, and (per factor) the untrusted
#:   two-station route, whose two stations are each such a link. Not on decoy
#:   (a source segment) or a branching route (no claim
#:   shows its read-off to be a compression), which emit it.
#:   Discharged by req:link-row-provenance, which the run names as a root
#:   exactly there (``DISCHARGED_ON_ROUTE``).
#: * A-CONST (reductions) on every route whose emitted constraint list is
#:   empty: "only where the emitted constraint list is non-empty"
#:   (req:assumption-ledger; ass:constdecl holds vacuously of an empty list).
#:   Not on the licensed route, which emits its entry.
#: * A-EIG (receiver) where no setting declares an exact window: emitted and
#:   not invoked (ass:eig; def:pmcex).
#: * A-SRC on the untrusted route, under every module whose ledger can carry
#:   it: no source-replacement certificate is demanded in untrusted mode
#:   (transmitter/ass:src; meat-core's rule "trusted-source mode at
#:   d_A >= 2"), while thm:certificate-sufficiency keeps it in the closure.
#: * A-SNAP (reductions) on every route with a reduction whose record names no
#:   block as resting on it: reductions/req:emission-record and
#:   domination/req:domination-record carry the row "exactly where there is
#:   one" resting block, while thm:emit (vi) keeps it in the closure of the
#:   emission roots. Not on a
#:   route whose default rests on a snap and emits it engaged, nor on Band A,
#:   which has no reduction.
_TRUSTED_EMPTY_LIST = {
    ("A-ATK", "protocol-compiler", False),
    ("A-ATK", "meat-core", False),
}
#: Listed only where a key length is reported, on every route.
_LENGTH_ONLY = {("A-ALICE-MEAS", "protocol-compiler", False)}
#: On the untrusted route, A-ENS is in the closure only through meat-core's
#: frank-wolfe/thm:firstorder and the roots of a reported length: no compiler
#: or transmitter root of that route holds it, and an estimate names
#: lem:estimate alone.
_ENS_WITH_A_BOUND = {
    ("A-ENS", "transmitter", False),
    ("A-ENS", "protocol-compiler", False),
}
_SNAP_CARRIED = ("A-SNAP", "reductions", False)
# A-PRESENT is not on band-a; A-LINK (compiler, on provenance) joined the three
# one-station wpfss routes; A-CONST (reductions, empty list) joined every route but the
# licensed one that has a reduction.
_LINK_ON_PROVENANCE = ("A-LINK", "protocol-compiler", True)
_CONST_EMPTY_LIST = ("A-CONST", "reductions", False)
#: A-EIG, emitted and invoked nowhere: every setting of an
#: exact-route receiver carries the enclosed weight (receiver/req:rigorous-
#: weight), and a setting with an enclosed weight does not invoke A-EIG,
#: whatever its depth (receiver/req:eig-ledger-row).
_EIG_RIGOROUS = ("A-EIG", "receiver", False)
#: A-RECV (reductions) on every route with a reduction: the run built each
#: receiver artefact itself, every one with a model admissible exactly and
#: every weight evaluated rigorously, so each reductions artefact omits its
#: A-RECV row and the run names reductions/req:recv-row-provenance as a root,
#: which discharges it (``DISCHARGED_ON_ROUTE``). Not on Band A, which has no
#: reduction.
_RECV_ON_PROVENANCE = ("A-RECV", "reductions", True)
# A-PROBE (reductions) at
# a station whose setting set is {*}, and A-TSM where in addition no public
# choice is applied at its factor (req:assumption-ledger): the probe-free
# stations of the wpfss and decoy routes, and BBM92's stations (A-TSM stays
# engaged at Alice's, which carries the test coin). On the untrusted route
# A-ENS (transmitter, and the compiler's copy) is emitted in trusted mode only
# and is listed where meat-core's roots hold it (_ENS_WITH_A_BOUND);
# A-ALICE-MEAS is not emitted at one letter; and A-LINK is omitted on
# provenance at both stations (req:link-row-provenance (ii), per factor).
_PROBE_FREE = {
    ("A-PROBE", "reductions", False),
    ("A-TSM", "reductions", False),
}
EXPECTED_NOT_ENGAGED: dict[str, set[tuple[str, str, bool]]] = {
    "band-a": _TRUSTED_EMPTY_LIST | {
        ("A-LINK", "protocol-compiler", True),
    },
    "wpfss-encoded": _TRUSTED_EMPTY_LIST | _PROBE_FREE | {
        _SNAP_CARRIED,
        _LINK_ON_PROVENANCE,
        _CONST_EMPTY_LIST,
        _EIG_RIGOROUS,
        _RECV_ON_PROVENANCE,
    },
    "wpfss-licensed": _PROBE_FREE | {
        _SNAP_CARRIED,
        _LINK_ON_PROVENANCE,
        _EIG_RIGOROUS,
        _RECV_ON_PROVENANCE,
    },
    "wpfss-no-window": _TRUSTED_EMPTY_LIST | _PROBE_FREE | {
        ("A-EIG", "receiver", False),
        _SNAP_CARRIED,
        _LINK_ON_PROVENANCE,
        _CONST_EMPTY_LIST,
        _RECV_ON_PROVENANCE,
    },
    "decoy": _TRUSTED_EMPTY_LIST | _PROBE_FREE | {
        _SNAP_CARRIED, _CONST_EMPTY_LIST, _EIG_RIGOROUS, _RECV_ON_PROVENANCE
    },
    "untrusted-two-station": {
        _EIG_RIGOROUS,
        _SNAP_CARRIED,
        _CONST_EMPTY_LIST,
        _RECV_ON_PROVENANCE,
        ("A-ATK", "protocol-compiler", False),
        ("A-ATK", "meat-core", False),
        ("A-SRC", "protocol-compiler", False),
        ("A-SRC", "transmitter", False),
        ("A-SRC", "reductions", False),
        ("A-SRC", "meat-core", False),
        ("A-PROBE", "reductions", False),
        _LINK_ON_PROVENANCE,
    },
}


def test_every_route_fixture_has_an_expected_not_engaged_set() -> None:
    assert set(ROUTES) <= set(EXPECTED_NOT_ENGAGED)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("outcome", OUTCOMES)
def test_the_not_engaged_set_is_exactly_what_the_statements_justify(
    route: str, outcome: str
) -> None:
    result = route_result(route, outcome)
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    listed = {
        (item.short_id, item.module, item.discharged_by is not None)
        for item in found.not_engaged
    }
    expected = set(EXPECTED_NOT_ENGAGED[route])
    if outcome == "key-length":
        expected |= _LENGTH_ONLY
    if route == "untrusted-two-station" and outcome != "estimate":
        expected |= _ENS_WITH_A_BOUND
    # A-LAB without a length is emitted in trusted-source mode only
    # (meat-core/ass:lab's emission rule): on the
    # untrusted route a bound without a length leaves it not engaged, though
    # thm:accumulated-entropy's closure, which does not see the mode, holds it.
    if route == "untrusted-two-station" and outcome == "bound-withheld":
        expected.add(("A-LAB", "meat-core", False))
    assert listed == expected


@pytest.mark.parametrize("outcome", OUTCOMES)
def test_a_row_the_compiler_reads_off_the_transmitter_says_why_it_is_absent(
    outcome: str,
) -> None:
    """The compiler's A-SRC row on the untrusted route.

    The compiler's emission rule for the transmitter's rows names their
    source, "read off the transmitter artefact's own ledger", not a condition
    a route meets; the reason says the transmitter's ledger did not carry it.
    """
    result = route_result("untrusted-two-station", outcome)
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    reasons = {(item.short_id, item.module): item.reason for item in found.not_engaged}
    assert reasons[("A-SRC", "protocol-compiler")] == (
        "not on the transmitter artefact's ledger on this route"
    )


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("outcome", OUTCOMES)
def test_no_source_rule_is_quoted_as_a_condition_not_met(
    route: str, outcome: str
) -> None:
    """No not-engaged reason reads "read off ...; not met on this route"."""
    result = route_result(route, outcome)
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    assert [
        (item.short_id, item.module)
        for item in found.not_engaged
        if "read off" in item.reason and "not met" in item.reason
    ] == []


# ===========================================================================
#  The omission of A-LINK names what it rests on (req:link-row-provenance)
# ===========================================================================

#: The routes on which the run passes ``chain_provenance`` and the compiler
#: omits A-LINK under req:link-row-provenance (ii), by hand: the one-station
#: flat-instance routes whose chain is the instance link alone.
# The untrusted two-station route is included: the
# discharge is per measured factor and both of its stations are flat instances.
_LINK_ROW_ON_PROVENANCE = {
    "wpfss-encoded", "wpfss-licensed", "wpfss-no-window", "untrusted-two-station",
}


@pytest.mark.parametrize("route", ROUTES)
def test_the_requirement_is_a_compiler_root_exactly_where_a_link_is_omitted_on_it(
    route: str,
) -> None:
    """A run omitting the row names the requirement.

    req:link-row-provenance uses the reductions theorems that prove every
    clause of A-LINK, so naming it puts what the omission rests on into the
    run's claim closure; its own closure does not hold A-LINK.
    """
    result = route_result(route)
    compiler_roots = run_claim_roots(result)["protocol-compiler"]
    named = "protocol-compiler/req:link-row-provenance" in compiler_roots
    assert named == (route in _LINK_ROW_ON_PROVENANCE)
    assert result.compilation.link_row_omitted_on_provenance == named
    ledger = result.compilation.assumption_ledger
    assert ("reduction_chain_sound" in ledger) == (
        route != "band-a" and route not in _LINK_ROW_ON_PROVENANCE
    )
    closure = claim_closure("protocol-compiler/req:link-row-provenance")
    assert "A-LINK" not in closure["assumptions"]


@pytest.mark.parametrize("route", sorted(_LINK_ROW_ON_PROVENANCE))
def test_the_omitted_link_row_names_the_requirement_that_omits_it(route: str) -> None:
    """The reason names what discharges it."""
    result = route_result(route)
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    (item,) = [i for i in found.not_engaged if i.short_id == "A-LINK"]
    assert item.discharged_by == "protocol-compiler/req:link-row-provenance"


# ===========================================================================
#  The omission of A-RECV names what it rests on (req:recv-row-provenance)
# ===========================================================================

#: The routes on which every reductions artefact omits its A-RECV row under
#: reductions/req:recv-row-provenance, by hand: every route with a reduction,
#: each building its receiver artefacts itself, exact and rigorous.
_RECV_ROW_ON_PROVENANCE = {
    "wpfss-encoded", "wpfss-licensed", "wpfss-no-window", "decoy",
    "untrusted-two-station",
}


@pytest.mark.parametrize("route", ROUTES)
def test_the_requirement_is_a_reductions_root_exactly_where_a_recv_is_omitted(
    route: str,
) -> None:
    """A run whose every reductions artefact omits the row names the requirement.

    req:recv-row-provenance uses the receiver theorems that prove both clauses
    of A-RECV for an exact, rigorous receiver artefact the run built, so naming
    it puts what the omission rests on into the run's claim closure; its own
    closure holds neither A-RECV nor A-EIG. No compiler row of A-RECV exists
    on any route.
    """
    result = route_result(route)
    roots = run_claim_roots(result)
    named = "reductions/req:recv-row-provenance" in roots.get("reductions", ())
    assert named == (route in _RECV_ROW_ON_PROVENANCE)
    reductions = [
        *([] if result.reduction_artifact is None else [result.reduction_artifact]),
        *(emission.reduction for emission in result.device_artifacts),
    ]
    for artifact in reductions:
        assert bool(artifact.receiver_row_omitted_on_provenance) == named
        assert ("A-RECV" in {e.assumption_id for e in artifact.assumption_ledger}) != (
            named
        )
    assert "receiver_artifact_accepted" not in result.compilation.assumption_ledger
    closure = claim_closure("reductions/req:recv-row-provenance")
    assert "A-RECV" not in closure["assumptions"]
    assert "A-EIG" not in closure["assumptions"]


@pytest.mark.parametrize("route", sorted(_RECV_ROW_ON_PROVENANCE))
def test_the_omitted_supplier_row_names_the_requirement_that_omits_it(
    route: str,
) -> None:
    """The reason names what discharges it, and nothing is a discrepancy."""
    result = route_result(route)
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    (item,) = [i for i in found.not_engaged if i.short_id == "A-RECV"]
    assert item.module == "reductions"
    assert item.discharged_by == "reductions/req:recv-row-provenance"
    assert "A-RECV" not in {entry.short_id for entry in found.entries}
    assert [d for d in found.discrepancies if d.short_id == "A-RECV"] == []


@pytest.mark.parametrize("route", ROUTES)
def test_every_carried_row_lies_in_the_closure_of_its_carriers(route: str) -> None:
    """CARRIED_ROWS names a carrier whose roots really assume the row.

    The per-module test reaches only the carried rows a route emits; no
    shipped route emits A-ALICE-MEAS, so this reads the map itself.
    """
    roots = run_claim_roots(route_result(route))
    for module, carried in CARRIED_ROWS.items():
        for short_id, carriers in carried.items():
            present = [carrier for carrier in carriers if carrier in roots]
            if not present:
                continue
            closure = {
                assumption
                for carrier in present
                for root in roots[carrier]
                for assumption in claim_closure(root)["assumptions"]
            }
            assert short_id in closure, (route, module, short_id, carriers)
