"""Which top-level results a run used, per module, on each route.

WHY THIS EXISTS. The route-exact set is the closure of "the run's actual
top-level results", so a root chosen
wrongly moves what a user is asked to vouch for. ``run_claim_roots`` chooses
them in the run tier; this file holds
each choice to a hand-written expectation on one fixture per route
(``tests/support/route_fixtures.py``), and holds the run tier's two
re-readings of a compiler predicate (Band A, a declared public choice) to the
rows the compiler emitted under the same predicate. The expectations are
written from the claims each rule cites (``certiqs_key.runs.assumptions``),
not read back from the code.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from tests.support.route_fixtures import (
    OUTCOMES,
    ROUTES,
    route_result,
)

from certiqs_key.domain.claim_closure import (
    ESTIMATE_ROOT,
    FIRST_ORDER_ROOT,
    KEY_LENGTH_ROOT,
    closure_table,
)
from certiqs_key.protocol_compiler.compile import public_choice_declared
from certiqs_key.protocol_compiler.declared_premises import is_band_a
from certiqs_key.reductions.reasons import LinkKind
from certiqs_key.runs.assumptions import (
    _reductions_roots,
    meat_core_roots,
    run_claim_roots,
)
from certiqs_key.runs.errors import RunError

pytestmark = pytest.mark.contract

GATES = (
    "protocol-compiler/thm:gates",
    "protocol-compiler/thm:validator-soundness",
    "protocol-compiler/thm:measurements-and-statistics",
    "protocol-compiler/thm:sifting-and-key",
    "protocol-compiler/thm:typing",
)
CHAIN = "protocol-compiler/thm:chain-consumption"
CHOICE = "protocol-compiler/thm:choice-encoding"
CORE_SOURCE = ("transmitter/thm:certificate-sufficiency", "transmitter/fact:sr")
BOX = (
    "statistics/binomial-box/thm:completeness-bound",
    "statistics/binomial-box/thm:honest-containment",
    "statistics/thm:box-oracle",
)
UNCONDITIONED = ("receiver/cor:emitted-unconditioned",)
FLAT = ("reductions/wpfss/cor:emitted-flat",)
#: Where the run passes chain_provenance and the compiler omits A-LINK under
#: req:link-row-provenance (ii) -- the three one-station flat-instance routes --
#: the run names that requirement as a compiler root, so that the theorems the
#: omission rests on are in its closure.
PROVENANCE = "protocol-compiler/req:link-row-provenance"
#: Where every reductions artefact of the run omitted its A-RECV row under
#: reductions/req:recv-row-provenance -- every route with a reduction, each
#: building its receiver artefacts itself, exact and rigorous -- the run names
#: that requirement as a reductions root, beside the results of the supplied
#: artefact, so that the receiver theorems the omission rests on are in its
#: closure.
RECV_PROVENANCE = "reductions/req:recv-row-provenance"

#: Per route, the device-side roots. Band A: the compiler's Band-A theorem and
#: no receiver or reductions module at all. Every route but decoy declares a
#: public choice (its weighted basis choice). The licensed route adds the
#: licence theorem; the decoy source is its submodule's corollary.
EXPECTED: dict[str, dict[str, tuple[str, ...]]] = {
    "band-a": {
        "protocol-compiler": (*GATES, "protocol-compiler/thm:band-a", CHOICE),
        "transmitter": CORE_SOURCE,
    },
    "wpfss-encoded": {
        "protocol-compiler": (*GATES, CHAIN, CHOICE, PROVENANCE),
        "transmitter": CORE_SOURCE,
        "receiver": UNCONDITIONED,
        "reductions": (*FLAT, RECV_PROVENANCE),
    },
    "wpfss-licensed": {
        "protocol-compiler": (*GATES, CHAIN, CHOICE, PROVENANCE),
        "transmitter": CORE_SOURCE,
        "receiver": UNCONDITIONED,
        "reductions": (*FLAT, "reductions/thm:licence", RECV_PROVENANCE),
    },
    "wpfss-no-window": {
        "protocol-compiler": (*GATES, CHAIN, CHOICE, PROVENANCE),
        "transmitter": CORE_SOURCE,
        "receiver": UNCONDITIONED,
        "reductions": (*FLAT, RECV_PROVENANCE),
    },
    "decoy": {
        "protocol-compiler": (*GATES, CHAIN),
        "transmitter": ("transmitter/decoy/cor:emitted-decoy",),
        "receiver": UNCONDITIONED,
        "reductions": (*FLAT, RECV_PROVENANCE),
    },
    # Untrusted, so fact:sr is no transmitter root; both stations' links are attested,
    # so the compiler omits A-LINK on provenance and names the requirement.
    "untrusted-two-station": {
        "protocol-compiler": (*GATES, CHAIN, CHOICE, PROVENANCE),
        "transmitter": ("transmitter/thm:certificate-sufficiency",),
        "receiver": UNCONDITIONED,
        "reductions": (*FLAT, RECV_PROVENANCE),
    },
}

KEY_LENGTH = (
    FIRST_ORDER_ROOT,
    KEY_LENGTH_ROOT,
    "meat-core/thm:keylength",
    "meat-core/lem:ev-correctness",
    "meat-core/cor:composed-security",
)
MEAT_CORE = {
    "key-length": KEY_LENGTH,
    "estimate": (ESTIMATE_ROOT,),
    # A withheld length's result names the root of the bound it still reports.
    "bound-withheld": (ESTIMATE_ROOT, FIRST_ORDER_ROOT),
}


def test_every_route_of_the_design_has_a_fixture() -> None:
    expected = set(EXPECTED)
    assert set(ROUTES) == expected


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("outcome", OUTCOMES)
def test_the_roots_of_each_route(route: str, outcome: str) -> None:
    roots = run_claim_roots(route_result(route, outcome))
    assert roots == {
        **EXPECTED[route],
        "statistics": BOX,
        "meat-core": MEAT_CORE[outcome],
    }


@pytest.mark.parametrize("route", ROUTES)
def test_every_root_chosen_is_a_root_the_table_carries(route: str) -> None:
    carried = set(closure_table()["roots"])
    for roots in run_claim_roots(route_result(route)).values():
        assert set(roots) <= carried


@pytest.mark.parametrize("route", ROUTES)
def test_the_public_choice_predicate_is_the_compiler_s(route: str) -> None:
    """The run tier reads A-COIN's predicate; it matches the emitted row.

    The run tier calls the compiler's own predicate rather than a copy (a copy
    would read the first factor only).
    """
    result = route_result(route)
    emitted = "public_choice_weights" in result.compilation.assumption_ledger
    assert public_choice_declared(result.specification) is emitted


@pytest.mark.parametrize("route", ROUTES)
def test_band_a_is_where_the_compiler_emitted_a_ideal(route: str) -> None:
    """``thm:band-a`` is chosen exactly where A-IDEAL ("BAND A ONLY") is emitted."""
    result = route_result(route)
    spec = result.specification
    assert is_band_a(spec.chain, spec.sectors) is (
        "ideal_qubit_receiver" in result.compilation.assumption_ledger
    )


def test_the_receiver_root_follows_inp_s() -> None:
    """``cor:emitted-conditioned`` where a probe input exists, else unconditioned."""
    for route in ROUTES:
        result = route_result(route)
        receivers = [
            *([] if result.receiver_artifact is None else [result.receiver_artifact]),
            *(emission.receiver for emission in result.device_artifacts),
        ]
        probed = {bool(r.input_mode_space.source_labels) for r in receivers}
        roots = run_claim_roots(result).get("receiver", ())
        if probed == {True}:
            assert roots == ("receiver/probe-conditioning/cor:emitted-conditioned",)
        elif probed == {False}:
            assert roots == UNCONDITIONED


def test_a_module_that_did_not_run_has_no_roots() -> None:
    roots = run_claim_roots(route_result("band-a"))
    assert "receiver" not in roots and "reductions" not in roots


def test_meat_core_adds_the_three_properties_only_on_a_length() -> None:
    estimate = meat_core_roots([ESTIMATE_ROOT], key_length_reported=False)
    assert estimate == (ESTIMATE_ROOT,)
    dropped = "meat-core/frank-wolfe/cor:fo-dropped"
    assert meat_core_roots([dropped, KEY_LENGTH_ROOT], key_length_reported=True) == (
        dropped, KEY_LENGTH_ROOT, *KEY_LENGTH[2:]
    )


def test_a_result_without_its_specification_is_an_error() -> None:
    result = route_result("band-a")
    stripped = SimpleNamespace(**{**vars(result), "specification": None})
    with pytest.raises(RunError, match="specification"):
        run_claim_roots(stripped)  # type: ignore[arg-type]


# ===========================================================================
#  Reductions artefacts no route fixture reaches
# ===========================================================================


def _artefact(rows: list[tuple[str, str | None]], kind: LinkKind,
              licence: bool = False,
              omitted: tuple[str, ...] = ()) -> SimpleNamespace:
    return SimpleNamespace(
        assumption_ledger=[
            SimpleNamespace(assumption_id=short_id, inherited_from=inherited)
            for short_id, inherited in rows
        ],
        reduction_chain=SimpleNamespace(links=[SimpleNamespace(kind=kind)]),
        attack_set_license=object() if licence else None,
        receiver_row_omitted_on_provenance=omitted,
    )


CORE_ROWS: list[tuple[str, str | None]] = [
    ("A-MEAS", None), ("A-ROUND-SQ", None),
    ("A-CONST", None), ("A-SEQ", None),
]


def test_a_core_emission_is_thm_emit_and_its_licence() -> None:
    """No submodule row and no flat link: the core's emission theorem."""
    assert _reductions_roots(_artefact(CORE_ROWS, LinkKind.IDENTITY)) == (
        "reductions/thm:emit",
    )
    assert _reductions_roots(_artefact(CORE_ROWS, LinkKind.IDENTITY, True)) == (
        "reductions/thm:emit", "reductions/thm:licence",
    )


def test_a_flat_emission_without_a_supplier_falls_back_to_thm_emit() -> None:
    """``wpfss/cor:emitted-flat`` rests on a supplied receiver (A-RECV)."""
    assert _reductions_roots(_artefact(CORE_ROWS, LinkKind.WPFSS)) == (
        "reductions/thm:emit",
    )
    supplied = [*CORE_ROWS, ("A-RECV", "receiver@0.9.0")]
    assert _reductions_roots(_artefact(supplied, LinkKind.FSS)) == FLAT


def test_an_omitted_supplier_row_selects_the_supplied_roots() -> None:
    """``req:recv-row-provenance``: no A-RECV row, the same roots as with one.

    An artefact whose A-RECV row was omitted on the run's attestation records
    the receiver artefact's version in ``receiver_row_omitted_on_provenance``;
    it rests on a supplied receiver artefact all the same, so its roots are
    those of the artefact that carries the row, and not the fallback
    ``thm:emit`` of an artefact without a supplier.
    """
    supplied = [*CORE_ROWS, ("A-RECV", "receiver@0.9.0")]
    omitted = _artefact(CORE_ROWS, LinkKind.FSS, omitted=("receiver@0.9.0",))
    assert _reductions_roots(omitted) == _reductions_roots(
        _artefact(supplied, LinkKind.FSS)
    ) == FLAT
    assert _reductions_roots(_artefact(CORE_ROWS, LinkKind.FSS)) == (
        "reductions/thm:emit",
    )



# ===========================================================================
#  A root resting on the probe-conditioning submodule, of any submodule
# ===========================================================================


def test_a_conditioned_root_of_any_submodule_is_kept_exactly_on_a_probe_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_reductions_roots``: the rule is the root's closure, not wpfss's name.

    A synthetic table, so that the case holds where the submodule is absent:
    a reductions submodule ``reductions/other`` with two roots resting on the
    supplied receiver (A-RECV), one of them also on a claim of the
    conditioning submodule, and the flat instance's conditioned weight route.
    On a probe-free run the conditioned root is left out; on a probe run it
    is named beside the flat conditioned route.
    """
    from certiqs_key.runs import assumptions

    plain = "reductions/other/cor:plain"
    conditioned = "reductions/other/cor:conditioned"
    route = "reductions/wpfss/cor:route-conditioned"
    closures = {
        plain: {"claims": [plain], "assumptions": ["A-RECV"]},
        conditioned: {
            "claims": [conditioned, "receiver/probe-conditioning/thm:x"],
            "assumptions": ["A-RECV"],
        },
        route: {
            "claims": [route, "receiver/probe-conditioning/thm:x"],
            "assumptions": ["A-RECV"],
        },
    }
    roots = {"reductions/other": [plain, conditioned], "reductions/wpfss": [route]}
    owners = {"A-OTHER": "reductions/other/ass:other", "A-RECV": "reductions/ass:recv"}
    monkeypatch.setattr(assumptions, "claim_closure", lambda root: closures[root])
    monkeypatch.setattr(assumptions, "roots_of_module", lambda module: roots[module])
    monkeypatch.setattr(
        assumptions, "assumption_info", lambda short_id: {"owner": owners[short_id]}
    )
    artefact = _artefact(
        [("A-OTHER", None), ("A-RECV", "receiver@0.9.0")], LinkKind.IDENTITY
    )
    assert _reductions_roots(artefact) == (plain,)  # type: ignore[arg-type]
    assert _reductions_roots(artefact, probe_conditioned=True) == (  # type: ignore[arg-type]
        plain, conditioned, route,
    )
