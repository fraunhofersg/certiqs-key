"""Every never-verified mark in the tree equals its assumption's header field.

WHY THIS TEST EXISTS. Whether a run rests on an assumption unverified could
be written by hand in up to five places per assumption -- the claim text, the
interface ledger, a code constant, a golden ledger and the run record's own
hand lists -- and places written by hand disagree. There is one source, under
one criterion (the load-bearing clause is unchecked): an assumption's
``verification`` header field (spec/claim-format.md section 3.2). The
claim-closure table carries the field
into the package (``certiqs_key/domain/claim_closure.json``) and every module
and the run record derive their marks from it.

What this test holds to ``verification == "never"``, read from the claim
files themselves:

* the table: every assumption has one machine key and every key one
  assumption, and the table's field is the header's (that the whole table is
  current is ``tests/harness/test_generate_claim_closure.py``);
* every ``never_verified`` list and every row flag of every ``interface.yaml``;
* every code constant that states a mark;
* every emitted ledger that carries a flag, and every emitted key is one the
  table knows;
* the run record's mark per machine key, which reads the table by machine key
  whatever module emitted the row.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from tests.support.route_fixtures import ROUTES, route_result

from certiqs_key.domain.claim_closure import ClaimClosureError, never_verified

ROOT = Path(__file__).resolve().parents[2]
MODULES = ROOT / "spec" / "modules"
TABLE = ROOT / "src" / "certiqs_key" / "domain" / "claim_closure.json"

_FIELD = re.compile(r"^% (kind|short_id|verification): *(\S+)\s*$", re.MULTILINE)


def _headers() -> dict[str, str]:
    """Return ``{short id: verification}`` read from every assumption file."""
    found: dict[str, str] = {}
    for path in sorted(MODULES.rglob("claims/*.tex")):
        fields = dict(_FIELD.findall(path.read_text(encoding="utf-8")))
        if fields.get("kind") != "ass":
            continue
        assert "short_id" in fields and "verification" in fields, path
        assert fields["short_id"] not in found, f"{fields['short_id']} twice"
        found[fields["short_id"]] = fields["verification"]
    return found


HEADERS = _headers()
ASSUMPTIONS: dict[str, dict[str, Any]] = json.loads(TABLE.read_text(encoding="utf-8"))[
    "assumptions"
]
KEY_OF = {short_id: str(row["machine_key"]) for short_id, row in ASSUMPTIONS.items()}
NEVER_IDS = frozenset(s for s, v in HEADERS.items() if v == "never")
NEVER_KEYS = frozenset(KEY_OF[s] for s in NEVER_IDS)


def _interface(module: str) -> dict[str, Any]:
    document = yaml.safe_load(
        (MODULES / module / "interface.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(document, dict)
    return document


def _output(document: dict[str, Any], name: str) -> dict[str, Any]:
    return next(row for row in document["outputs"] if row["name"] == name)


def _ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row["id"]) for row in rows]


def _never(ids: list[str]) -> set[str]:
    return {short_id for short_id in ids if short_id in NEVER_IDS}


# --------------------------------------------------------------------------
# The table against the headers
# --------------------------------------------------------------------------


def test_every_assumption_has_one_machine_key_and_every_key_one_assumption() -> None:
    assert set(ASSUMPTIONS) == set(HEADERS)
    keys = list(KEY_OF.values())
    assert all(keys), [s for s, k in KEY_OF.items() if not k or k == "None"]
    assert "None" not in keys
    assert len(set(keys)) == len(keys), sorted(k for k in keys if keys.count(k) > 1)
    for short_id, row in ASSUMPTIONS.items():
        assert row["verification"] == HEADERS[short_id], short_id


def test_the_accessor_reads_the_field_by_machine_key() -> None:
    for short_id, key in KEY_OF.items():
        assert never_verified(key) is (short_id in NEVER_IDS), (short_id, key)
    # The statistics keys are identifiers, not `key = value` readings of the
    # honest_model record.
    assert KEY_OF["A-HON"] == "honest_rounds_iid"
    assert never_verified("honest_rounds_iid") is ("A-HON" in NEVER_IDS)


def test_a_key_that_names_no_assumption_is_refused() -> None:
    """Fail-closed: the record stops rather than writing an unmarked row."""
    with pytest.raises(ClaimClosureError, match="names no assumption"):
        never_verified("receiver_povm_characterized")
    with pytest.raises(ClaimClosureError, match="names no assumption"):
        never_verified("honest_model = envelope_honest_rounds")
    with pytest.raises(ClaimClosureError, match="names no assumption"):
        never_verified("honest_model = iid_honest_rounds")


# --------------------------------------------------------------------------
# The interfaces
# --------------------------------------------------------------------------


def _walk(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


@pytest.mark.parametrize(
    "path",
    sorted(MODULES.rglob("interface.yaml")),
    ids=lambda p: p.parent.relative_to(MODULES).as_posix(),
)
def test_every_interface_row_flag_and_key_is_the_assumption_s(path: Path) -> None:
    """A row naming an assumption carries its one key and its one mark."""
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    for row in _walk(document):
        short_id = row.get("id")
        if short_id not in ASSUMPTIONS:
            continue
        if "machine_key" in row:
            assert row["machine_key"] == KEY_OF[short_id], (path, short_id)
        for flag in ("never_verified", "never_verifiable"):
            if flag in row:
                assert row[flag] is (short_id in NEVER_IDS), (path, short_id, flag)


def test_meat_core_s_lists() -> None:
    document = _interface("meat-core")
    ledger, never = document["assumption_ledger"], document["never_verified"]
    own = _ids(ledger["own_rows"])
    inherited = _ids(ledger["inherited_rows"]["rows"])
    submodule = _ids(ledger["submodule_rows"])
    assert set(never["own"]) == _never(own)
    assert set(never["inherited"]) == _never(inherited)
    assert set(never["submodule"]) == _never(submodule)
    # An assumption no run emits still carries a machine key (the closure
    # table needs one); its never mark is listed like any other row's.
    unemitted = _ids(ledger["unemitted_rows"]["rows"])
    assert set(never["unemitted"]) == _never(unemitted)
    # No row is discharged: A-BLOCK, the one that was, is
    # protocol-compiler/rem:block-restriction.
    assert "discharged_rows" not in ledger
    assert "discharged_rather_than_verified" not in never


def test_the_protocol_compiler_s_lists() -> None:
    document = _interface("protocol-compiler")
    ledger, never = document["assumption_ledger"], document["never_verified"]
    own = _ids(ledger["own_rows"])
    inherited = _ids(ledger["inherited_rows"])
    assert set(never["own"]) == _never(own)
    assert set(never["inherited"]) == _never(inherited)
    # A-BLOCK, the one consumer obligation, is not a ledger row.
    assert "consumer_obligation" not in never


def test_the_receiver_s_list() -> None:
    document = _interface("receiver")
    rows = _ids(_output(document, "assumption_ledger")["rows"])
    assert set(document["never_verified_set"]) == _never(rows)


def test_reductions_lists() -> None:
    document = _interface("reductions")
    ledger = _output(document, "assumption_ledger")
    core = _ids(ledger["core_rows"])
    assumed = _ids(ledger["assumed_from_another_module"])
    never = document["never_verified"]
    assert set(never["core"]) == _never(core)
    assert set(never["assumed_from_another_module"]) == _never(assumed)


def test_statistics_lists() -> None:
    document = _interface("statistics")
    ledger, never = document["assumption_ledger"], document["never_verified"]
    assert set(never["own"]) == _never(_ids(ledger["own_rows"]))
    # The field has no `partly` today; a list beside `own` would be a second
    # vocabulary (spec/claim-format.md section 3.2). No row is inherited
    # (A-TSM is no premise of a result this module reports).
    assert set(never) == {"own", "note"}
    assert "inherited_rows" not in ledger


def test_the_transmitter_s_list() -> None:
    document = _interface("transmitter")
    rows = _ids(_output(document, "assumption_ledger")["rows"])
    assert set(document["never_verified"]["own"]) == _never(rows)
    decoy = _output(_interface("transmitter/decoy"), "assumption_ledger")["rows"]
    assert all("never_verified" in row for row in decoy)


# --------------------------------------------------------------------------
# The code constants
# --------------------------------------------------------------------------


def test_the_receiver_s_constant() -> None:
    from certiqs_key.receiver.reasons import ASSUMPTION_MACHINE_KEYS, NEVER_VERIFIED

    assert {str(i) for i in NEVER_VERIFIED} == _never(
        [str(i) for i in ASSUMPTION_MACHINE_KEYS]
    )
    for identifier, key in ASSUMPTION_MACHINE_KEYS.items():
        assert key == KEY_OF[str(identifier)]


def test_reductions_constants() -> None:
    from certiqs_key.reductions.reasons import (
        ASSUMPTION_MACHINE_KEYS,
        CORE_ASSUMPTIONS,
        NEVER_VERIFIED,
    )

    for row in CORE_ASSUMPTIONS:
        assert row.machine_key == KEY_OF[row.identifier], row.identifier
        assert row.never_verifiable is (row.identifier in NEVER_IDS), row.identifier
    assert {str(i) for i in NEVER_VERIFIED} == _never(
        [str(i) for i in ASSUMPTION_MACHINE_KEYS]
    )


def _statistics_rows() -> tuple[Any, ...]:
    """Return the rows of both routes: every row the module can emit."""
    from fractions import Fraction

    from certiqs_key.statistics.ledger import AcceptanceRoute, assumption_ledger

    half = Fraction(1, 2)
    return tuple(
        row
        for route in AcceptanceRoute
        for row in assumption_ledger(
            route, alphabet=("a", "b"), rounds=10, honest=(half, half),
        )
    )


def test_statistics_constant() -> None:
    from certiqs_key.statistics.ledger import LEDGER_IDS, MACHINE_KEYS

    for short_id in LEDGER_IDS:
        assert MACHINE_KEYS[short_id] == KEY_OF[short_id], short_id
    for row in _statistics_rows():
        assert row.machine_key == KEY_OF[row.assumption_id], row.assumption_id
        assert row.never_verified is (row.assumption_id in NEVER_IDS), row.assumption_id


def test_the_protocol_compiler_s_constants() -> None:
    from certiqs_key.protocol_compiler.reasons import (
        ASSUMPTION_MACHINE_KEYS,
        INHERITED_KEYS,
        INHERITED_NEVER_VERIFIED_KEYS,
        NEVER_VERIFIED,
    )

    assert {str(i) for i in NEVER_VERIFIED} == _never(
        [str(i) for i in ASSUMPTION_MACHINE_KEYS]
    )
    for short_id, key in INHERITED_KEYS.items():
        assert key == KEY_OF[short_id], short_id
    assert set(INHERITED_NEVER_VERIFIED_KEYS) == {
        key for key in INHERITED_KEYS.values() if key in NEVER_KEYS
    }
    # The compiler emits no A-RECV row on any route
    # (assumption_ledger.a_recv_not_emitted_note): reductions' key is in none
    # of its tables.
    assert "A-RECV" not in INHERITED_KEYS
    assert KEY_OF["A-RECV"] not in INHERITED_NEVER_VERIFIED_KEYS
    # The interface's inherited rows and the code's map are one table.
    rows = _interface("protocol-compiler")["assumption_ledger"]["inherited_rows"]
    assert {row["id"]: row["machine_key"] for row in rows} == dict(INHERITED_KEYS)


def test_meat_core_s_constants() -> None:
    from certiqs_key.meat_core.reasons import (
        ASSUMPTION_MACHINE_KEYS,
        INHERITED_KEYS,
        INHERITED_NEVER_VERIFIED_KEYS,
        NEVER_VERIFIED,
    )

    assert {str(i) for i in NEVER_VERIFIED} == _never(
        [str(i) for i in ASSUMPTION_MACHINE_KEYS]
    )
    for short_id, key in INHERITED_KEYS.items():
        assert key == KEY_OF[short_id], short_id
    assert set(INHERITED_NEVER_VERIFIED_KEYS) == {
        key for key in INHERITED_KEYS.values() if key in NEVER_KEYS
    }
    # A-LMO is superseded and emitted on no run, so the code carries no constant for its
    # key; the closure table still lists it, with the key the submodule's ledger row
    # gives it and its never-verified field.
    assert KEY_OF["A-LMO"] == "exact_linear_oracle"
    assert "exact_linear_oracle" in NEVER_KEYS


def test_the_transmitter_s_constants() -> None:
    from certiqs_key.transmitter.decoy.reasons import (
        DECOY_ASSUMPTION_MACHINE_KEYS,
        DECOY_NEVER_VERIFIED,
    )
    from certiqs_key.transmitter.reasons import ASSUMPTION_MACHINE_KEYS, NEVER_VERIFIED

    assert {str(i) for i in NEVER_VERIFIED} == _never(
        [str(i) for i in ASSUMPTION_MACHINE_KEYS]
    )
    assert {str(i) for i in DECOY_NEVER_VERIFIED} == _never(
        [str(i) for i in DECOY_ASSUMPTION_MACHINE_KEYS]
    )
    for mapping in (ASSUMPTION_MACHINE_KEYS, DECOY_ASSUMPTION_MACHINE_KEYS):
        for identifier, key in mapping.items():
            assert key == KEY_OF[str(identifier)]


# --------------------------------------------------------------------------
# The emitted ledgers
# --------------------------------------------------------------------------


def _receiver_rows() -> tuple[Any, ...]:
    from receiver_povm_support import bb84_channel_only_request

    from certiqs_key.receiver import construct_receiver

    emission = construct_receiver(bb84_channel_only_request())
    assert emission.artifact is not None
    return tuple(emission.artifact.assumption_ledger)


def _reductions_entries() -> tuple[Any, ...]:
    from certiqs_key.reductions.artifact import assumption_ledger
    from certiqs_key.reductions.reasons import CORE_ASSUMPTIONS

    return assumption_ledger(
        {}, "receiver-povm@0.3.0", rows=CORE_ASSUMPTIONS
    )


def _engine_keys() -> tuple[str, ...]:
    from certiqs_key.meat_core.reasons import assumption_ledger

    return assumption_ledger(
        trusted_source=True,
        alice_dim=2,
        alice_party="A",
        constraint_entries=1,
        key_length_wanted=True,
        key_length_reported=True,
        first_order=True,
    )


def _compiler_keys() -> tuple[str, ...]:
    from certiqs_key.protocol_compiler.reasons import (
        ASSUMPTION_MACHINE_KEYS,
        INHERITED_KEYS,
    )

    return (*ASSUMPTION_MACHINE_KEYS.values(), *INHERITED_KEYS.values())


def test_every_emitted_flag_is_the_field() -> None:
    for record in _receiver_rows():
        assert record.never_verified is (record.machine_key in NEVER_KEYS)
    for entry in _reductions_entries():
        assert entry.never_verifiable is (entry.machine_key in NEVER_KEYS)
    for row in _statistics_rows():
        assert row.never_verified is (row.machine_key in NEVER_KEYS)


@pytest.mark.contract
def test_the_engine_names_a_src_in_trusted_mode_at_d_a_at_least_2() -> None:
    """A-SRC's row is emitted in trusted-source mode at ``d_A >= 2`` only.

    Vacuous at ``d_A = 1`` and never demanded there (``rem:modes-da1`` (b5)).
    There is no A-MARG row (its key ``trusted_marginal`` is not emitted): the
    product marginal is ``meat-core/lem:product-marginal``, and no ledger names
    it. On a run that reports a first-order bound or
    a key length, whose roots rest on A-SRC; a run that reports neither, whose
    one root ``lem:estimate`` rests on nothing, emits no row.
    """
    from certiqs_key.meat_core.reasons import INHERITED_KEYS, assumption_ledger

    src = INHERITED_KEYS["A-SRC"]
    for trusted in (True, False):
        for alice_dim in (1, 2, 4):
            for reported, bound in ((False, True), (True, True), (False, False)):
                keys = assumption_ledger(
                    trusted_source=trusted,
                    alice_dim=alice_dim,
                    alice_party="A",
                    constraint_entries=0,
                    key_length_wanted=True,
                    key_length_reported=reported,
                    first_order=bound,
                )
                expected = trusted and alice_dim >= 2 and bound
                assert "trusted_marginal" not in keys
                assert (src in keys) is expected, (trusted, alice_dim, bound)


def test_every_emitted_bare_key_is_one_the_table_knows() -> None:
    """The compiler, the engine and the transmitter emit keys without a flag."""
    from certiqs_key.transmitter.decoy.emit import DECOY_ASSUMPTION_LEDGER
    from certiqs_key.transmitter.reasons import ASSUMPTION_MACHINE_KEYS

    known = set(KEY_OF.values())
    for key in (
        *_engine_keys(),
        *_compiler_keys(),
        *ASSUMPTION_MACHINE_KEYS.values(),
        *DECOY_ASSUMPTION_LEDGER,
    ):
        assert key in known, key


# --------------------------------------------------------------------------
# The run record
# --------------------------------------------------------------------------


@pytest.mark.parametrize("route", ROUTES)
def test_every_record_entry_carries_its_assumption_s_field(route: str) -> None:
    """Every emitter's rows, one manifest: one entry per id, the field's mark.

    Since record schema 0.20.0 the manifest is the route-exact set, whose
    entries carry the closure table's snapshot of each assumption, the
    ``verification`` field included, instead of a per-row mark. Read on the
    real emitters of every route fixture (no solve), with a reductions entry
    whose own flag is deliberately wrong: the entry reads the table, not the
    emitter, so it carries its owner's field.
    """
    from dataclasses import replace

    from certiqs_key.runs.assumptions import (
        emitted_rows,
        route_exact_assumptions,
        run_claim_roots,
    )

    result = route_result(route)
    if result.reduction_artifact is not None:
        wrong = tuple(
            replace(entry, never_verifiable=not entry.never_verifiable)
            for entry in result.reduction_artifact.assumption_ledger
        )
        result.reduction_artifact = replace(
            result.reduction_artifact, assumption_ledger=wrong
        )
    payload = route_exact_assumptions(
        run_claim_roots(result), emitted_rows(result)
    ).as_payload()
    assert payload["assumptions"]
    for entry in payload["assumptions"]:
        assert entry["verification"] == HEADERS[entry["short_id"]], entry["short_id"]
        assert entry["machine_key"] == KEY_OF[entry["short_id"]]


def test_the_record_refuses_a_row_whose_key_names_no_assumption() -> None:
    from certiqs_key.runs.assumptions import EmittedRow, route_exact_assumptions

    row = EmittedRow(
        machine_key="receiver_povm_characterized", emitted_by="protocol-compiler"
    )
    with pytest.raises(ClaimClosureError, match="names no assumption"):
        route_exact_assumptions({}, [row])


def test_every_header_is_in_the_package_s_vocabulary() -> None:
    """``decided`` and ``discharged`` left with record schema 0.20.0."""
    from certiqs_key.domain.claim_closure import VERIFICATIONS

    assert set(HEADERS.values()) <= VERIFICATIONS
    assert {"never", "partly"} == VERIFICATIONS
