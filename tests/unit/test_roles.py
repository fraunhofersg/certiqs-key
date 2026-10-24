"""The role vector of a run record (``certiqs_key.runs.roles``; spec/pm-eb-roles).

WHY THESE TESTS EXIST. The report and the guards G1-G7 read each party's role
from one helper (role-audit.md section 2.2: SENDS, MEASURES_A, DRAWS_LETTER,
STATIONS, SETTING, CHOOSES, HOLDS_KEY, SOURCE_TRUSTED); a wrong predicate would
put "Your source" back on an untrusted run or hide a trivial premise from G1.
Every payload here is a hand-written fragment of a record in the shape the
named example writes (bbm92: untrusted, two stations, Alice's coin;
a probe station: trusted, one station with an on/off probe, Bob's coin; bb84:
Band A, no factorisation; an older record's single ``choice_weighting`` and
announcement tables), so each expectation is a fact about a hand-written
input, not a value read back from the helper.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.runs.roles import (
    PARTY_NAMES,
    PRESUPPOSITIONS,
    ROLE_CONDITIONED_CLAUSES,
    TRIVIAL_WHEN,
    label_order,
    not_on_this_run,
    party_name,
    presupposition_holds,
    row_station,
    run_roles,
    unmet_presuppositions,
)

ROOT = Path(__file__).resolve().parents[2]


def _support(rows: list[tuple[str, str, str]]) -> list[list[str]]:
    return [list(row) for row in rows]


def bbm92_payload() -> dict[str, Any]:
    """BBM92's roles: untrusted, d_A = 1, x0; coin at Alice's station; holder A."""
    return {
        "compiled": {
            "source": {"source_mode": "untrusted", "alice_dim": 1,
                       "signal_alphabet": ["x0"], "virtual_transmitted_system": 1,
                       "public_choices": None},
            "public": {
                "key_holder": "A",
                "party_partition": {
                    "alice_system_party": "A",
                    "alice_readout_alphabet": ["(H,gen)", "(H,test)"],
                    "bob_readout_alphabet": ["H", "V"],
                },
                "sector_factorisation": [
                    {"label": "alice_station", "party": "A", "system": "Q"},
                    {"label": "bob_station", "party": "B", "system": "Q"},
                ],
                "choice_weightings": [{
                    "factor": "alice_station", "setting_alphabet": ["off"],
                    "choice_alphabet": ["gen", "test"],
                    "setting_map": {"H": "off"},
                    "support": _support([("(H,gen)", "H", "gen"),
                                         ("(H,test)", "H", "test")]),
                }],
                "transcript": [{"sender": "A"}, {"sender": "B"}],
            },
        },
        "stages": {"stations": [
            {"index": 0, "factor": "alice_station", "party": "A",
             "receiver": {"bound_quantifier_domain": {"probe_alphabet": ["off"]}}},
            {"index": 1, "factor": "bob_station", "party": "B",
             "receiver": {"bound_quantifier_domain": {"probe_alphabet": ["off"]}}},
        ]},
    }


def probe_station_payload() -> dict[str, Any]:
    """Return a probe station's roles: trusted d_A = 2; station f0 (B), probe off/on."""
    return {
        "compiled": {
            "source": {"source_mode": "trusted", "alice_dim": 2,
                       "signal_alphabet": ["(Z,0)", "(Z,1)", "(X,0)", "(X,1)"],
                       "virtual_transmitted_system": 2,
                       "public_choices": {"party": "A", "choices": ["Z", "X"]}},
            "public": {
                "key_holder": "B",
                "party_partition": {
                    "alice_system_party": "A",
                    "alice_readout_alphabet": ["(Z,0)"],
                    "bob_readout_alphabet": ["(H,off,gen)", "(H,on,test)"],
                },
                "sector_factorisation": [{"label": "f0", "party": "B", "system": "Q"}],
                "choice_weightings": [{
                    "factor": "f0", "setting_alphabet": ["off", "on"],
                    "choice_alphabet": ["gen", "test"],
                    "setting_map": {"H,off": "off", "H,on": "on"},
                    "support": _support([("(H,off,gen)", "H,off", "gen"),
                                         ("(H,on,test)", "H,on", "test")]),
                }],
                "transcript": [{"sender": "B"}, {"sender": "A"}],
            },
        },
        "stages": {"receiver_construction": {"probe_alphabet": ["off", "on"]}},
    }


def bb84_payload() -> dict[str, Any]:
    """bb84 (Band A): no factorisation; Bob's basis choice bound by A-COIN only."""
    return {
        "compiled": {
            "source": {"source_mode": "trusted", "alice_dim": 2,
                       "signal_alphabet": ["(Z,0)", "(Z,1)", "(X,0)", "(X,1)"],
                       "virtual_transmitted_system": 2,
                       "public_choices": {"party": "A", "choices": ["Z", "X"]}},
            "public": {"key_holder": "A", "party_partition": {},
                       "choice_weightings": [], "transcript": [],
                       "announce_alice": [["x", "Z"]], "announce_bob": [["v", "Z"]]},
        },
        "stages": {"receiver_construction": {"probe_alphabet": None}},
        "assumption_manifest": {"assumptions": [{
            "short_id": "A-COIN",
            "bindings": [{"name": "public_choices", "value": [
                {"party": "A", "choices": ["Z", "X"]},
                {"party": "B", "choices": ["Z", "X"]},
            ]}],
        }]},
    }


def test_presuppositions_are_the_checkers_vocabulary() -> None:
    """runs/roles.py and harness/check_claims.py name the same four roles.

    The checker's tuple is read from its source (``tests/harness`` is a package
    named ``harness`` and shadows the tools in a test process).
    """
    tree = ast.parse((ROOT / "harness" / "check_claims.py").read_text(encoding="utf-8"))
    (value,) = [
        node.value for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name)
                and target.id == "ASSUMPTION_PRESUPPOSITIONS"
                for target in node.targets)
    ]
    assert tuple(PRESUPPOSITIONS) == tuple(ast.literal_eval(value))


def test_the_formal_labels_read_alice_and_bob() -> None:
    assert dict(PARTY_NAMES) == {"A": "Alice", "B": "Bob"}
    assert party_name("A") == "Alice"
    assert party_name("B") == "Bob"
    assert party_name("C") == "party C"


def test_the_report_holds_no_party_map_of_its_own() -> None:
    """The one map is roles.PARTY_NAMES (role-audit.md section 4: three copies)."""
    for path in sorted((ROOT / "src" / "certiqs_key" / "runs" / "report").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert '"Alice"' not in text and '"Bob"' not in text, path.name


def test_bbm92_roles() -> None:
    roles = run_roles(bbm92_payload())
    assert roles.source_trusted is False
    assert not roles.has_letters
    for party in ("A", "B"):
        assert not roles.sends(party)
        assert not roles.measures_a(party)
        assert not roles.draws_letter(party)
        assert roles.has_lab(party)
    assert roles.holds_key("A") and not roles.holds_key("B")
    assert roles.chooses("A") and not roles.chooses("B")
    alice, bob = roles.stations
    assert (alice.index, alice.factor, alice.party) == (0, "alice_station", "A")
    assert (bob.index, bob.factor, bob.party) == (1, "bob_station", "B")
    assert not alice.setting and not bob.setting
    assert alice.choice_applied and not bob.choice_applied
    assert alice.setting_recorded_by == "A"
    assert roles.stations_of("A") == (alice,)


def test_probe_station_roles() -> None:
    roles = run_roles(probe_station_payload())
    assert roles.source_trusted is True
    assert roles.sends("A") and not roles.sends("B")
    assert roles.holds_key("B")
    assert roles.chooses("A") and roles.chooses("B")
    (station,) = roles.stations
    assert (station.index, station.factor, station.party) == (None, "f0", "B")
    assert station.settings == ("off", "on")
    assert station.setting and station.choice_applied
    assert station.setting_recorded_by == "B"
    assert roles.message_senders == ("B", "A")


def test_a_single_receiver_without_a_factorisation_is_bobs() -> None:
    """The declaration's default partition labels the one measured factor B."""
    roles = run_roles(bb84_payload())
    (station,) = roles.stations
    assert (station.index, station.party, station.settings) == (None, "B", ())
    # Bob's basis choice, bound by A-COIN, is applied at his station; Alice's
    # presentation is drawn with her letter.
    assert station.choice_applied
    assert roles.chooses("B")
    assert roles.message_senders == ("A", "B")


def test_an_older_records_single_weighting_and_tables() -> None:
    payload = bbm92_payload()
    public = payload["compiled"]["public"]
    (weighting,) = public.pop("choice_weightings")
    del weighting["factor"]
    weighting["party"] = "A"
    public["choice_weighting"] = weighting
    public.pop("transcript")
    public["announce_alice"] = [["x", "a"]]
    roles = run_roles(payload)
    assert roles.stations[0].choice_applied
    assert not roles.stations[1].choice_applied
    assert roles.chooses("A")
    assert roles.message_senders == ("A",)


def test_untrusted_with_a_measured_letter_system() -> None:
    payload = bbm92_payload()
    payload["compiled"]["source"].update(alice_dim=2, signal_alphabet=["0", "1"])
    roles = run_roles(payload)
    assert roles.measures_a("A") and not roles.sends("A")


def test_a_drawn_letter() -> None:
    payload = bbm92_payload()
    payload["compiled"]["source"].update(signal_alphabet=["0", "1"])
    assert run_roles(payload).draws_letter("A")


def test_presuppositions_hold_at_their_scope() -> None:
    eb, pm = run_roles(bbm92_payload()), run_roles(probe_station_payload())
    assert not presupposition_holds("trusted-source", eb)
    assert presupposition_holds("trusted-source", pm)
    assert not presupposition_holds("letters", eb)
    assert presupposition_holds("letters", pm)
    assert presupposition_holds("sends", pm, party="A")
    assert not presupposition_holds("sends", pm, party="B")
    assert presupposition_holds("sends", pm)
    assert not presupposition_holds("sends", eb)
    assert not presupposition_holds("setting", eb, station=0)
    assert not presupposition_holds("setting", eb)
    assert presupposition_holds("setting", pm)
    assert not presupposition_holds("setting", pm, station=3)
    with pytest.raises(ValueError, match="unknown presupposition"):
        presupposition_holds("measures", eb)


def test_unmet_presuppositions_name_the_scope() -> None:
    eb = run_roles(bbm92_payload())
    assert unmet_presuppositions(
        ["setting"], eb, [{"module": "reductions", "station": 0, "party": None}]
    ) == [("setting", "station 0")]
    assert unmet_presuppositions(
        ["sends"], eb, [{"module": "meat-core", "station": None, "party": "A"}]
    ) == [("sends", "party A")]
    assert unmet_presuppositions(["trusted-source"], eb, []) == [
        ("trusted-source", "run")
    ]
    pm = run_roles(probe_station_payload())
    assert unmet_presuppositions(
        ["setting", "trusted-source"], pm,
        [{"module": "reductions", "station": None, "party": None}],
    ) == []


def test_a_row_is_at_its_station_or_the_one_receiver() -> None:
    eb, pm = run_roles(bbm92_payload()), run_roles(probe_station_payload())
    assert row_station(eb, {"module": "reductions", "station": 1}) is eb.stations[1]
    assert row_station(eb, {"module": "reductions", "station": None}) is None
    assert row_station(pm, {"module": "reductions", "station": None}) is pm.stations[0]
    assert row_station(pm, {"module": "meat-core", "station": None}) is None
    assert row_station(pm, {"module": "meat-core", "station": None,
                            "party": "B"}) is None


def _binding(name: str, value: Any) -> dict[str, Any]:
    return {"name": name, "value": value}


def test_the_triviality_registry() -> None:
    """G1's predicates, each on a trivial and a non-trivial row."""
    eb, pm = run_roles(bbm92_payload()), run_roles(probe_station_payload())
    trivial = TRIVIAL_WHEN
    assert trivial["A-PROBE"]([_binding("q_off", "1")], pm, None)
    assert trivial["A-PROBE"]([_binding("q_off", "15/16"),
                               _binding("q_on", "1/16")], pm, None) is None
    assert trivial["A-PROBE"]([], eb, 0)
    assert trivial["A-ENS"]([], eb, None)
    assert trivial["A-ENS"]([_binding("source_ensemble", {
        "signal_alphabet": ["x0"], "transmitted_dim": 1})], pm, None)
    assert trivial["A-ENS"]([_binding("source_ensemble", {
        "signal_alphabet": ["0", "1"], "transmitted_dim": 2})], pm, None) is None
    assert trivial["A-ALICE-MEAS"]([], eb, None)
    assert trivial["A-ALICE-MEAS"]([], pm, None) is None
    assert trivial["A-SPEC"]([_binding("alice_povm", [])], eb, None)
    assert trivial["A-SPEC"]([_binding("specification", {})], eb, None) is None
    assert trivial["A-TSM"]([], eb, 1)
    assert trivial["A-TSM"]([], eb, 0) is None
    assert trivial["A-TSM"]([], pm, None) is None
    assert trivial["A-COIN"]([_binding("choice_weighting", [
        {"choice_alphabet": ["gen"]}])], eb, None)
    assert trivial["A-COIN"]([_binding("choice_weighting", [
        {"choice_alphabet": ["gen", "test"]}])], eb, None) is None
    assert trivial["A-COIN"]([_binding("public_choices", [
        {"choices": ["Z"]}, {"choices": ["Z", "X"]}])], eb, None) is None
    assert trivial["A-VAC"]([_binding("undeclared_input_modes", [])], eb, 0)
    assert trivial["A-VAC"]([_binding("undeclared_input_modes", ["X_H"])],
                            eb, 0) is None
    assert trivial["A-EIG"]([_binding("invoked_at", [])], eb, 0)
    assert trivial["A-EIG"]([_binding("invoked_at", ["off"])], eb, 0) is None


# --------------------------------------------------------------------------
# Setting recorder, announcements before the bar, role-conditioned clauses
# --------------------------------------------------------------------------


def test_the_setting_recorder_needs_one_matching_party() -> None:
    """Identically named readout letters at both parties name no one."""
    payload = probe_station_payload()
    partition = payload["compiled"]["public"]["party_partition"]
    partition["alice_readout_alphabet"] = list(partition["bob_readout_alphabet"])
    (station,) = run_roles(payload).stations
    assert station.setting_recorded_by is None


def test_the_public_choices_say_who_draws_them_and_where() -> None:
    (coin,) = run_roles(bbm92_payload()).public_choices
    assert (coin.party, coin.at_station, coin.factor, coin.choices,
            coin.setting_dependent) == ("A", True, "alice_station",
                                        ("gen", "test"), False)
    letter, weighted = run_roles(probe_station_payload()).public_choices
    assert (letter.party, letter.at_station, letter.choices) == ("A", False,
                                                                  ("Z", "X"))
    assert (weighted.party, weighted.factor, weighted.setting_dependent) == (
        "B", "f0", True)


def _labelled(senders: tuple[str, str], labels: list[str]) -> dict[str, Any]:
    first, second = senders
    return {
        "transcript": [
            {"sender": first, "alphabet": ["gen:Z", "gen:X", "test:H"]},
            {"sender": second, "alphabet": ["Z", "X", "H"]},
        ],
        "acceptance_alphabet": labels,
    }


def test_the_label_order_is_read_off_the_labels_not_the_transcript() -> None:
    """Whose announcement stands before the bar."""
    labels = ["gen", "gen:Z|X", "test:H|H"]
    assert label_order(_labelled(("A", "B"), labels)) == ("A", "B")
    assert label_order(_labelled(("B", "A"), labels)) == ("B", "A")
    # A probe station's shape: Bob sends first, the label writes Alice's letter
    # first; a part is matched without its round-kind prefix.
    public = {
        "transcript": [
            {"sender": "B", "alphabet": ["gen:nc,off", "test:nc,off"]},
            {"sender": "A", "alphabet": ["Z", "(Z,0)"]},
        ],
        "acceptance_alphabet": ["gen", "gen|nc,off", "test:(Z,0)|nc,off"],
    }
    assert label_order(public) == ("A", "B")
    assert label_order({"acceptance_alphabet": ["gen", "ok"]}) is None


def test_role_conditioned_clauses_not_on_this_run() -> None:
    """The clauses whose condition fails, with the reason."""
    eb, pm = run_roles(bbm92_payload()), run_roles(probe_station_payload())
    station = [{"module": "receiver", "station": 0, "party": None}]
    assert [clause for clause, _ in not_on_this_run("A-TRUST", eb, station)] == [
        "the probe states"
    ]
    receiver = [{"module": "receiver", "station": None}]
    assert not_on_this_run("A-TRUST", pm, receiver) == []
    assert [reason for _, reason in not_on_this_run("A-SEQ", eb, [])] == [
        "the source is untrusted"
    ]
    assert not_on_this_run("A-SEQ", pm, []) == []
    # The trusted source in a laboratory, any d_A.
    assert not_on_this_run("A-LAB", eb, [])[0][1] == (
        "the source is untrusted and counts as outside every laboratory")
    da1 = run_roles(probe_station_payload())
    assert not_on_this_run("A-LAB", replace(da1, alice_dim=1), []) == []
    assert not_on_this_run("A-LAB", replace(eb, source_trusted=None), []) == []
    assert not_on_this_run("A-COIN", pm, []) == []
    assert [clause for clause, _ in not_on_this_run("A-COIN", eb, [])] == [
        "a choice whose probabilities depend on a station's private setting",
        "its mention of Alice's letter",
    ]
    assert "A-VAC" not in ROLE_CONDITIONED_CLAUSES
    assert not_on_this_run("A-AUTH", eb, []) == []


def test_the_response_mode_clause_is_off_where_no_such_mode_is_declared() -> None:
    payload = bbm92_payload()
    payload["assumption_manifest"] = {"assumptions": [{"short_id": "A-MEAS"}]}
    assert run_roles(payload).response_modes is False
    assert [clause for clause, _ in not_on_this_run(
        "A-ROUND-SQ", run_roles(payload), [])] == [
        "the same response in each declared detector-response mode"]
    # No manifest: the record does not say, and nothing is marked.
    assert run_roles(bbm92_payload()).response_modes is None
    for short_id, clauses in ROLE_CONDITIONED_CLAUSES.items():
        assert short_id.startswith("A-") and clauses
