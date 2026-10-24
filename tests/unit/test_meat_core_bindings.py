"""The engine's assumption bindings and the roots its result names.

Values are bound per assumption: beside each row of its ledger an emitter
records the declared values the row's assumption's clauses are about.
meat-core's ledger is a tuple of bare machine keys, so the values travel beside
it as ``assumption_bindings`` on the general key-rate result (one entry per
row, in the ledger's order; :mod:`certiqs_key.domain.bindings` for the shape).

WHAT IS HELD HERE.

* The NAMES each row binds, hand-written below from the assumption each row
  states as the claim files stand:
  ``spec/modules/meat-core/claims/ass-*.tex``,
  ``spec/modules/meat-core/frank-wolfe/claims/ass-lmo.tex``,
  ``protocol-compiler/claims/ass-atk.tex`` and ``ass-rhom.tex``,
  ``transmitter/claims/ass-src.tex`` and ``ass-seq.tex``. The clause each
  name comes from is ``meat_core.reasons.ROW_BINDINGS``' comment and the
  interface's ``assumption_ledger.binds``.
* The VALUES, against the declaration and the run parameters they are read
  from, on general declarations of each shape (trusted and untrusted mode, a
  constraint list with and without an attack-set licence, a singleton and a
  polytope acceptance set).
* That the shapes the engine binds for A-ATK and A-SRC are the compiler's and
  the transmitter's, value for value, on every route, once the run tier has
  read the engine's wire IDs back into the declared spelling, so the run's
  one entry per assumption merges them; and the run tier's join.
* The roots a result names for each outcome.

No number of any result is read.
"""

from __future__ import annotations

import math
from dataclasses import replace
from types import SimpleNamespace

import pytest
from tests.support.general_toys import (
    decoy_like_general,
    qubit_bb84_general,
    two_factor_general,
)
from tests.support.route_fixtures import ROUTES, docked, route_result

from certiqs_key.domain.bindings import is_immutable, ledger_bindings_record
from certiqs_key.domain.claim_closure import (
    CERTIFIED_REFERENCE_ROOT,
    CERTIFIED_ROOT,
    DROPPED_ROOT,
    ESTIMATE_ROOT,
    FIRST_ORDER_ROOT,
    KEY_LENGTH_ROOT,
    REFERENCE_ROOT,
    claim_closure,
)
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    PolytopeData,
)
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.finitekey.result import deductions_of
from certiqs_key.meat_core.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    INHERITED_KEYS,
    OPTIONAL_BINDINGS,
    ROW_BINDINGS,
    assumption_bindings,
    assumption_ledger,
    laboratory_parties,
)
from certiqs_key.runs.assumptions import (
    emitted_rows,
    route_exact_assumptions,
    run_claim_roots,
)
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    declared_values,
    result_claim_roots,
)

pytestmark = pytest.mark.contract

#: Short id -> machine key, for every row the engine's ledger may carry.
KEY: dict[str, str] = {
    **{str(identifier): key for identifier, key in ASSUMPTION_MACHINE_KEYS.items()},
    **INHERITED_KEYS,
}

#: THE NAMES EACH ROW BINDS, hand-written from the claims (module docstring).
#: ``attack_set_license`` only where the declaration carries one.
EXPECTED_NAMES: dict[str, tuple[str, ...]] = {
    # ass:keyreg (ii) the declared holder; (iv) lambda_EC bits.
    "A-KEYREG": ("lambda_ec", "key_holder"),
    # ass:hash (i) l-bit values, ideal family; (ii) ceil(log2(1/eps_EV)) bits.
    "A-HASH": ("key_length", "ideal_hash", "ev_hash_bits"),
    # ass:seed (v) "in trusted-source mode".
    "A-SEED": ("source_mode",),
    # ass:fixed (i), in its order.
    "A-FIXED": (
        "acceptance_set", "rounds", "key_length", "lambda_ec",
        "eps_pa", "eps_ev", "eps_auth", "k_auth",
    ),
    # ass:conform (i) the test; (ii) the messages; (iv) the l-bit key.
    "A-CONFORM": ("acceptance_set", "lambda_ec", "ev_hash_bits", "key_length"),
    # ass:auth (ii), (v).
    "A-AUTH": ("eps_auth", "k_auth"),
    # ass:lab, stated for a party P: the party the row is emitted for, the
    # source mode, and the party labels of the partition, part (b).
    "A-LAB": ("party", "source_mode", "party_partition"),
    # protocol-compiler/ass:atk: the licensed non-empty list, its mode, (i).
    "A-ATK": ("constraint_entries", "source_mode", "attack_set_license"),
    # transmitter/ass:src: the premise (mode, tau_A) and (ii) {M_x}.
    # (and the party label of A, whose laboratory (i) names, party_partition
    # (b)).
    "A-SRC": ("source_mode", "alice_marginal", "alice_povm", "party_partition"),
    # protocol-compiler/ass:rhom (i): every round, one declaration and mode.
    "A-RHOM": ("rounds", "source_mode"),
    # transmitter/ass:seq (ii): after the n rounds.
    "A-SEQ": ("rounds",),
    # (frank-wolfe/ass:lmo is superseded and its row is emitted on no run, so it
    # binds nothing.)
}


def _values(
    d: GeneralDeclaration,
    *,
    key_length: int | None = 7,
    eps_auth: float = 2.0**-40,
    k_auth: int = 256,
    ideal_hash: bool = True,
) -> dict[str, object]:
    return declared_values(
        d,
        key_length=key_length,
        eps_auth=eps_auth,
        k_auth=k_auth,
        ideal_hash=ideal_hash,
        deductions=deductions_of(
            lambda_ec=d.parameters.lambda_ec,
            eps_ev=d.parameters.eps_ev,
            eps_pa=d.parameters.eps_pa,
            alpha=d.parameters.alpha,
            ideal_hash=ideal_hash,
        ),
    )


def _parties(d: GeneralDeclaration) -> tuple[str, ...]:
    """Return the parties A-LAB's rows name on a run reporting a key length."""
    return laboratory_parties(
        trusted_source=d.is_trusted_source,
        alice_party=str(d.alice.party),
        key_length_reported=True,
        first_order=True,
    )


def _full_ledger(d: GeneralDeclaration) -> tuple[str, ...]:
    return assumption_ledger(
        trusted_source=d.is_trusted_source,
        alice_dim=d.alice_dim,
        alice_party=str(d.alice.party),
        constraint_entries=len(d.constraint_list),
        key_length_wanted=True,
        key_length_reported=True,
        first_order=True,
    )


def _licensed() -> GeneralDeclaration:
    return replace(
        two_factor_general(party_local=False),
        attack_set_license={"supplier": "reductions@test", "statement": "licensed"},
    )


def _polytope() -> GeneralDeclaration:
    return replace(
        qubit_bb84_general(),
        acceptance_set=AcceptanceSet(
            geometry="polytope",
            polytope=PolytopeData(
                columns=2, rows=((1.0, 0.0), (0.0, -1.0)), rhs=(0.75, -0.25)
            ),
        ),
    )


DECLARATIONS = {
    "qubit-bb84-trusted": qubit_bb84_general,
    "decoy-like-trusted": decoy_like_general,
    "two-factor-untrusted-constrained": lambda: two_factor_general(party_local=False),
    "two-factor-licensed": _licensed,
    "qubit-bb84-polytope": _polytope,
}


# ===========================================================================
#  The names
# ===========================================================================


def test_every_row_the_engine_can_emit_names_its_bindings() -> None:
    assert {key: ROW_BINDINGS[key] for key in ROW_BINDINGS} == {
        KEY[short_id]: names for short_id, names in EXPECTED_NAMES.items()
    }
    assert set(ROW_BINDINGS) == set(KEY.values())
    assert {"attack_set_license"} == OPTIONAL_BINDINGS


@pytest.mark.parametrize("name", list(DECLARATIONS))
def test_one_entry_per_row_in_the_ledger_s_order_with_the_names(name: str) -> None:
    d = DECLARATIONS[name]()
    ledger = _full_ledger(d)
    bindings = assumption_bindings(ledger, _values(d), parties=_parties(d))
    assert tuple(key for key, _ in bindings) == ledger
    short = {key: short_id for short_id, key in KEY.items()}
    for key, pairs in bindings:
        expected = tuple(
            item
            for item in EXPECTED_NAMES[short[key]]
            if item != "attack_set_license" or d.attack_set_license is not None
        )
        assert tuple(pair[0] for pair in pairs) == expected, (name, key)
    assert is_immutable(bindings)
    # The one JSON form an artefact writes them in.
    record = ledger_bindings_record(bindings)
    assert list(record) == list(dict.fromkeys(ledger))


def test_a_missing_value_is_an_error_and_an_absent_licence_is_omitted() -> None:
    d = two_factor_general(party_local=False)
    values = _values(d)
    assert values["attack_set_license"] is None
    (atk,) = assumption_bindings((KEY["A-ATK"],), values)
    assert [pair[0] for pair in atk[1]] == ["constraint_entries", "source_mode"]
    del values["rounds"]
    with pytest.raises(KeyError, match="rounds"):
        assumption_bindings((KEY["A-SEQ"],), values)
    with pytest.raises(KeyError):
        assumption_bindings(("no_such_key",), _values(d))


# ===========================================================================
#  The values, against the declaration
# ===========================================================================


@pytest.mark.parametrize("name", list(DECLARATIONS))
def test_the_values_are_the_declaration_s(name: str) -> None:
    d = DECLARATIONS[name]()
    bound = {
        key: dict(pairs)
        for key, pairs in assumption_bindings(
            _full_ledger(d), _values(d), parties=_parties(d)
        )
        if key != KEY["A-LAB"]
    }
    p = d.parameters

    keyreg = bound[KEY["A-KEYREG"]]
    assert keyreg == {"lambda_ec": p.lambda_ec, "key_holder": str(d.key_holder)}

    ev_bits = math.ceil(-math.log2(p.eps_ev))
    assert bound[KEY["A-HASH"]] == {
        "key_length": 7, "ideal_hash": True, "ev_hash_bits": ev_bits,
    }
    assert isinstance(bound[KEY["A-HASH"]]["ev_hash_bits"], int)

    assert bound[KEY["A-SEED"]] == {"source_mode": str(d.source_mode)}

    acceptance = bound[KEY["A-FIXED"]]["acceptance_set"]
    assert dict(acceptance)["geometry"] == d.acceptance_set.geometry  # type: ignore[arg-type]
    assert dict(acceptance)["alphabet"] == tuple(d.acceptance_values)  # type: ignore[arg-type]
    if d.acceptance_set.polytope is not None:
        assert dict(acceptance)["inequalities"] == d.acceptance_set.polytope.m_row  # type: ignore[arg-type]
    else:
        assert dict(acceptance)["frequencies"] == d.acceptance_set.frequencies  # type: ignore[arg-type]
    assert bound[KEY["A-FIXED"]] == {
        "acceptance_set": acceptance,
        "rounds": d.rounds,
        "key_length": 7,
        "lambda_ec": p.lambda_ec,
        "eps_pa": p.eps_pa,
        "eps_ev": p.eps_ev,
        "eps_auth": 2.0**-40,
        "k_auth": 256,
    }
    assert bound[KEY["A-CONFORM"]] == {
        "acceptance_set": acceptance,
        "lambda_ec": p.lambda_ec,
        "ev_hash_bits": ev_bits,
        "key_length": 7,
    }
    assert bound[KEY["A-AUTH"]] == {"eps_auth": 2.0**-40, "k_auth": 256}
    # A-LAB, one row per party, A then B on a run reporting a length; the
    # party labels by position (the label of A, then each measured factor's).
    labs = [
        dict(pairs)
        for key, pairs in assumption_bindings(
            _full_ledger(d), _values(d), parties=_parties(d)
        )
        if key == KEY["A-LAB"]
    ]
    partition = (
        ("alice_system", str(d.alice.party)),
        ("measured_factors", tuple(str(f.party) for f in d.factors)),
    )
    assert labs == [
        {"party": party, "source_mode": str(d.source_mode),
         "party_partition": partition}
        for party in ("A", "B")
    ]

    if d.constraint_list:
        atk = bound[KEY["A-ATK"]]
        assert dict(atk["constraint_entries"]) == {  # type: ignore[arg-type]
            "count": len(d.constraint_list),
            "rhs_tags": tuple(str(e.rhs_tag) for e in d.constraint_list),
        }
        assert atk["source_mode"] == str(d.source_mode)
        if d.attack_set_license is not None:
            assert atk["attack_set_license"] == (
                ("supplier", str(d.attack_set_license["supplier"])),
            )
    else:
        assert KEY["A-ATK"] not in bound

    if d.is_trusted_source and d.alice_dim >= 2:
        src = bound[KEY["A-SRC"]]
        assert src["source_mode"] == "trusted"
        assert dict(src["alice_marginal"]) == {  # type: ignore[arg-type]
            "dimension": d.alice_dim,
            "sector_dims": tuple(d.alice_dim_of(s) for s in d.alice_sectors),
        }
        assert dict(src["alice_povm"]) == {  # type: ignore[arg-type]
            "form": str(d.alice_form),
            "alphabet": tuple(d.alice_alphabet),
            "dimension": d.alice_dim,
        }
        assert dict(src["party_partition"])["alice_system"] == str(  # type: ignore[arg-type]
            d.alice.party
        )
    else:
        assert KEY["A-SRC"] not in bound

    assert bound[KEY["A-RHOM"]] == {
        "rounds": d.rounds, "source_mode": str(d.source_mode),
    }
    assert bound[KEY["A-SEQ"]] == {"rounds": d.rounds}
    assert "exact_linear_oracle" not in bound


def test_the_authentication_zeros_and_a_merely_two_universal_family_are_bound() -> None:
    """A-AUTH binds the zeros; A-HASH binds the hash choice made."""
    d = qubit_bb84_general()
    values = _values(d, eps_auth=0.0, k_auth=0, ideal_hash=False)
    bound = dict(assumption_bindings((KEY["A-AUTH"], KEY["A-HASH"]), values))
    assert dict(bound[KEY["A-AUTH"]]) == {"eps_auth": 0.0, "k_auth": 0}
    assert dict(bound[KEY["A-HASH"]])["ideal_hash"] is False


# ===========================================================================
#  Merging with the compiler's and the transmitter's rows, and the join
# ===========================================================================


@pytest.mark.parametrize("route", ROUTES)
def test_the_shared_rows_bind_the_compiler_s_and_the_transmitter_s_values(
    route: str,
) -> None:
    """A-ATK and A-SRC, value for value; A-RHOM's source mode; on every route.

    THE ENGINE'S VALUES AS THE RUN TIER JOINS THEM. The engine binds the
    declaration it read back off the bundle, whose labels are wire IDs; the
    join reads them back through the run's ``WireLabels``. Read raw, the
    engine's A-SRC differs from the transmitter's on every route whose Alice
    labels the wire renames.
    """
    result = route_result(route)
    engine = {
        row.machine_key: row.bindings
        for row in emitted_rows(result)
        if row.emitted_by == "meat-core"
    }
    compiler = dict(result.compilation.assumption_bindings)
    transmitter = dict(result.specification.source.artifact.assumption_bindings)
    atk, src, rhom = KEY["A-ATK"], KEY["A-SRC"], KEY["A-RHOM"]
    if atk in engine:
        compiler_atk = dict(compiler[atk])
        for name, value in engine[atk]:
            assert compiler_atk[name] == value, (route, name)
    if src in engine:
        # The transmitter's names, value for value; the engine adds the
        # party label of A, which the transmitter does not bind (R2).
        shared = tuple(pair for pair in engine[src] if pair[0] != "party_partition")
        assert shared == transmitter[src], route
    assert dict(engine[rhom])["source_mode"] == dict(compiler[rhom])["source_mode"]
    assert dict(engine[rhom])["rounds"] == docked(route).rounds


def _declared(value: object, inverse: dict[str, str]) -> object:
    """Return a label-bearing binding with its ``alphabet`` read back."""
    assert isinstance(value, tuple)
    return tuple(
        (part, tuple(inverse[x] for x in item) if part == "alphabet" else item)
        for part, item in value
    )


@pytest.mark.parametrize("route", ROUTES)
def test_the_run_tier_joins_the_engine_s_bindings(route: str) -> None:
    """Row for row, the engine's bindings, the two label-bearing names read back.

    ``alice_povm``'s alphabet through the inverse of the run's
    ``alice_outcome`` bijection and ``acceptance_set``'s through that of
    ``acceptance_value``; every other value is the engine's own.
    """
    result = route_result(route)
    rows = [row for row in emitted_rows(result) if row.emitted_by == "meat-core"]
    assert tuple(row.machine_key for row in rows) == result.key_rate.assumption_ledger
    inverse = {
        "alice_povm": {w: x for x, w in result.labels.alice_outcome.items()},
        "acceptance_set": {w: c for c, w in result.labels.acceptance_value.items()},
    }
    expected = tuple(
        (
            key,
            tuple(
                (name, _declared(value, inverse[name]) if name in inverse else value)
                for name, value in bindings
            ),
        )
        for key, bindings in result.key_rate.assumption_bindings
    )
    assert tuple((row.machine_key, row.bindings) for row in rows) == expected
    # The acceptance alphabet the join records is the declared one, which the
    # acceptance stage of a record holds.
    for row in rows:
        acceptance = dict(row.bindings).get("acceptance_set")
        if acceptance is not None:
            assert isinstance(acceptance, tuple)
            assert dict(acceptance)["alphabet"] == tuple(
                result.labels.acceptance_value
            ), (route, row.machine_key)
    # The route-exact set merges identical values across emitters: A-SRC
    # (transmitter, compiler's copy, engine) and A-ATK (compiler, engine)
    # carry each name once.
    found = route_exact_assumptions(run_claim_roots(result), emitted_rows(result))
    for entry in found.entries:
        # One value per name on EVERY entry (A-SRC must not carry alice_povm
        # twice, once in each spelling, while the engine's goes unread) -- per
        # emitting station and party: A-LAB's `party` is bound once per party,
        # and a station's binding that names its own party (A-SEQ's "measured
        # system") once per station.
        names = [
            (
                name,
                tuple(sorted(str(item[1]) for item in items if item[1] is not None)),
                tuple(sorted(str(item[2]) for item in items if item[2] is not None)),
            )
            for name, _, items in entry.bindings
        ]
        assert len(names) == len(set(names)), (route, entry.short_id)
        if entry.short_id == "A-SRC":
            emitters = {
                module for _, _, items in entry.bindings for module, *_ in items
            }
            assert {"transmitter", "meat-core"} <= emitters


def test_a_result_whose_bindings_do_not_follow_its_ledger_is_refused() -> None:
    """``GeneralKeyRateResult`` holds one entry per ledger row, in its order."""
    from certiqs_key.solvers.frank_wolfe.general_keyrate import GeneralKeyRateResult

    stand_in = SimpleNamespace(
        assumption_ledger=("key_register",),
        assumption_bindings=(("pa_hash_family", ()),),
    )
    with pytest.raises(ValueError, match="one entry per assumption_ledger row"):
        GeneralKeyRateResult.__post_init__(stand_in)  # type: ignore[arg-type]


# ===========================================================================
#  The roots the result names (C2 (a))
# ===========================================================================


def test_the_result_names_the_root_of_every_number_it_reports() -> None:
    assert result_claim_roots(
        bound_reported=True, dropped=False, key_length_reported=True
    ) == [FIRST_ORDER_ROOT, KEY_LENGTH_ROOT]
    assert result_claim_roots(
        bound_reported=True, dropped=True, key_length_reported=True
    ) == [DROPPED_ROOT, KEY_LENGTH_ROOT]
    # A withheld length: the tier's claim and the bound's.
    assert result_claim_roots(
        bound_reported=True, dropped=False, key_length_reported=False
    ) == [ESTIMATE_ROOT, FIRST_ORDER_ROOT]
    assert result_claim_roots(
        bound_reported=True, dropped=True, key_length_reported=False
    ) == [ESTIMATE_ROOT, DROPPED_ROOT]
    assert result_claim_roots(
        bound_reported=False, dropped=False, key_length_reported=False
    ) == [ESTIMATE_ROOT]
    with pytest.raises(ValueError, match="only with its bound"):
        result_claim_roots(
            bound_reported=False, dropped=False, key_length_reported=True
        )


@pytest.mark.parametrize(
    ("dropped", "reference"), [(False, False), (True, False), (False, True)]
)
def test_a_certified_key_length_names_its_corollary(
    dropped: bool, reference: bool
) -> None:
    """``req:certified-evaluation`` (vi): the corollary that licenses the length.

    On every route a result reported at the certified tier names
    ``cor:certified-keylength`` beside the bound's root, and on the reference
    route ``cor:certified-keylength-reference`` beside it, with the full lists
    asserted.
    """
    roots = result_claim_roots(
        bound_reported=True,
        dropped=dropped,
        key_length_reported=True,
        reference=reference,
        certified=True,
    )
    assert CERTIFIED_ROOT in roots
    bound = (
        REFERENCE_ROOT if reference else DROPPED_ROOT if dropped else FIRST_ORDER_ROOT
    )
    companion = [CERTIFIED_REFERENCE_ROOT] if reference else []
    assert roots == [bound, CERTIFIED_ROOT, *companion, KEY_LENGTH_ROOT]
    # The certified tier is reported only with its key length.
    with pytest.raises(ValueError, match="only with its key length"):
        result_claim_roots(
            bound_reported=True,
            dropped=dropped,
            key_length_reported=False,
            reference=reference,
            certified=True,
        )


@pytest.mark.parametrize("bound", [FIRST_ORDER_ROOT, DROPPED_ROOT, REFERENCE_ROOT])
def test_the_certified_roots_add_no_premise_to_the_first_order_length(
    bound: str,
) -> None:
    """Why the rule above names the certified roots unconditionally.

    The companion case is split off (``lem:certified-bracket-enclosed``,
    ``cor:certified-keylength-reference``), so the
    closure of ``cor:certified-keylength`` is that of the first-order key
    length, within every bound root's closure with ``cor:keylength-bound``'s,
    and the reference corollary's is within ``cor:fo-reference``'s. A root
    that added a premise would put in a run's closure what no module of its
    route emits, which the run tier reports as a discrepancy. A corollary that
    used ``cor:fo-reference`` and ``prop:reference-companion`` unconditionally
    would be named on the reference route only.
    """
    premises = set(claim_closure(bound)["assumptions"]) | set(
        claim_closure(KEY_LENGTH_ROOT)["assumptions"]
    )
    assert set(claim_closure(CERTIFIED_ROOT)["assumptions"]) <= premises
    if bound == REFERENCE_ROOT:
        assert set(claim_closure(CERTIFIED_REFERENCE_ROOT)["assumptions"]) <= premises


def test_a_run_reporting_only_the_estimate_emits_no_row() -> None:
    """``lem:estimate`` rests on no assumption."""
    for trusted in (True, False):
        for alice_dim in (1, 2):
            for entries in (0, 2):
                assert assumption_ledger(
                    trusted_source=trusted,
                    alice_dim=alice_dim,
                    alice_party="A",
                    constraint_entries=entries,
                    key_length_wanted=True,
                    key_length_reported=False,
                    first_order=False,
                ) == ()
