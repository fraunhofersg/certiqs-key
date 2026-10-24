"""Guards G1-G7 of the PM/EB roles over every committed report example.

WHY THIS EXISTS. A BBM92 report must not show source premises on an untrusted
run, "Bob's" setting at Alice's station, or premises trivially satisfied on the
run: the report has to work for general DV PM and EB protocols. The guards
(``tests/support/role_guards.py``, each with its motivation) hold every
example a reader is shown to the role vector of its own run:

* G1 no engaged premise is structurally trivial;
* G2 untrusted: no source premise, no source group on the page;
* G3 a station premise names only its station's party, no singular role noun;
* G4 every engaged premise's ``presupposes`` holds at its scope;
* G5 one engaged A-LAB row per party with a role, on a key-length run;
* G6 A-COIN over every factor is ``tests/unit/test_pm_eb_coin_and_lab_premises.py``'s
  ``test_a_coin_at_the_second_factor_alone_emits_a_coin``;
* G7 untrusted: no ``transmitter/fact:sr`` root and no A-ENS; trusted: the
  two together.

``test_every_example_passes_the_guards`` reads the COMMITTED records, which an
engine regenerates at a commit (``runs/report_examples/README.md``); it is red
for a record an older engine wrote until the examples are regenerated, and
then holds the regenerated ones, the EB examples included (it reads every
entry of ``EXAMPLES``). The same guards over fresh runs of the
current engine are ``tests/integration/test_role_guards_fresh.py``. The other
tests here show, on hand-written records, that each guard fails on the defect
it names.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from runs.report_examples.generate import EXAMPLES, read_record, record_paths
from tests.support.report_records import completed_record, synthetic_table
from tests.support.role_guards import (
    checked,
    g1_no_trivial_premise,
    g2_untrusted_has_no_source,
    g3_station_names_its_own_party,
    g4_presuppositions_hold,
    g5_one_laboratory_per_party,
    g7_roots_follow_the_mode,
    violations,
)

RECORDS: list[tuple[str, Path]] = [
    (f"{example.name}/{path.name}", path)
    for example in EXAMPLES for path in record_paths(example)
]


@pytest.mark.parametrize(("name", "path"), RECORDS, ids=[name for name, _ in RECORDS])
def test_every_example_passes_the_guards(name: str, path: Path) -> None:
    found = violations(checked(read_record(path)))
    assert found == {}, f"{name}: {found}"


# --------------------------------------------------------------------------
# Each guard fails on its defect (hand-written records)
# --------------------------------------------------------------------------


def _row(module: str, station: int | None = None, party: str | None = None
         ) -> dict[str, Any]:
    return {"module": module, "station": station, "party": party,
            "machine_key": "", "inherited_from": None}


def _premise(short_id: str, category: str, rows: list[dict[str, Any]], *,
             title: str = "A premise", presupposes: list[str] | None = None,
             bindings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "short_id": short_id, "machine_key": short_id.lower(),
        "owner": f"meat-core/ass:{short_id.lower()}", "title": title,
        "summary": f"Summary of {short_id}.", "user_statement": None,
        "category": category, "affects": ["secrecy"], "refines": None,
        "verification": "never", "verification_sentence": "",
        "status": "accepted", "effective_status": "accepted",
        "contract": {"pdf": "spec/modules/meat-core/contract.pdf",
                     "anchor": f"claim-meat-core/ass:{short_id.lower()}"},
        "presupposes": presupposes or [],
        "emitted_by": rows, "bindings": bindings or [],
    }


def _laboratory(*parties: str) -> dict[str, Any]:
    return _premise(
        "A-LAB", "laboratory", [_row("meat-core", party=party) for party in parties],
        bindings=[{"name": "party", "value": party,
                   "emitted_by": [{"module": "meat-core", "station": None,
                                   "party": party}]}
                  for party in parties],
    )


def _eb_record(*premises: dict[str, Any], roots: dict[str, list[str]] | None = None
               ) -> dict[str, Any]:
    """BBM92's roles: untrusted, d_A = 1, two stations (A, B), no probe."""
    def edit(record: dict[str, Any]) -> None:
        payload = record["payload"]
        payload["compiled"] = {
            "source": {"source_mode": "untrusted", "alice_dim": 1,
                       "signal_alphabet": ["x0"], "virtual_transmitted_system": 1},
            "public": {"key_holder": "A", "choice_weightings": [],
                       "party_partition": {"alice_system_party": "A"},
                       "transcript": [{"sender": "A"}, {"sender": "B"}]},
        }
        payload["stages"]["stations"] = [
            {"index": 0, "factor": "alice_station", "party": "A",
             "receiver": {"bound_quantifier_domain": {"probe_alphabet": ["off"]}}},
            {"index": 1, "factor": "bob_station", "party": "B",
             "receiver": {"bound_quantifier_domain": {"probe_alphabet": ["off"]}}},
        ]
        manifest = payload["assumption_manifest"]
        # The fixture's A-ALICE-MEAS is trivial at one letter (G1); a run
        # with BBM92's roles does not emit it.
        manifest["assumptions"] = [
            *(entry for entry in manifest["assumptions"]
              if entry["short_id"] != "A-ALICE-MEAS"),
            _laboratory("A", "B"), *premises,
        ]
        manifest["roots"] = roots or {"transmitter": [
            "transmitter/thm:certificate-sufficiency"]}
    return completed_record(edit=edit)


def _guarded(record: dict[str, Any]) -> Any:
    return checked(record, synthetic_table())


def test_the_clean_hand_written_record_passes() -> None:
    assert violations(_guarded(_eb_record())) == {}


def test_g1_finds_a_probe_premise_at_a_station_with_one_setting() -> None:
    probe = _premise(
        "A-PROBE", "local-randomness", [_row("reductions", 0)],
        bindings=[{"name": "q_off", "value": "1",
                   "emitted_by": [{"module": "reductions", "station": 0,
                                   "party": None}]}],
    )
    (found,) = g1_no_trivial_premise(_guarded(_eb_record(probe)))
    assert found.startswith("A-PROBE") and "one setting" in found


def test_g2_finds_a_source_premise_on_an_untrusted_run() -> None:
    ensemble = _premise("A-ENS", "source", [_row("transmitter")],
                        presupposes=["trusted-source"])
    c = _guarded(_eb_record(ensemble))
    found = g2_untrusted_has_no_source(c)
    assert "A-ENS has category source" in found
    assert "A-ENS presupposes ['trusted-source']" in found
    # The report itself groups it elsewhere: no source heading on the page.
    assert 'id="category-source"' not in c.markdown


def test_g3_finds_another_partys_name_at_a_station() -> None:
    wrong = _premise("A-TSM", "protocol-structure", [_row("reductions", 0)],
                     title="Bob's private setting is modelled")
    (found,) = g3_station_names_its_own_party(_guarded(_eb_record(wrong)))
    assert found == "A-TSM title names ['Bob']"
    both = _premise("A-TSM", "protocol-structure", [_row("reductions", 0)],
                    title="A register Alice and Bob cannot see")
    assert g3_station_names_its_own_party(_guarded(_eb_record(both))) == []


def test_g3_finds_a_singular_role_noun_in_a_station_binding() -> None:
    measured = _premise(
        "A-MEAS", "receiver", [_row("reductions", 0), _row("reductions", 1)],
        bindings=[{"name": "the measuring party's device", "value": "declared",
                   "emitted_by": [{"module": "reductions", "station": 0,
                                   "party": None}]}],
    )
    (found,) = g3_station_names_its_own_party(_guarded(_eb_record(measured)))
    assert "the measuring party's" in found


def test_g4_finds_an_unmet_presupposition_at_the_rows_scope() -> None:
    probe = _premise("A-X", "local-randomness", [_row("reductions", 1)],
                     presupposes=["setting"])
    assert g4_presuppositions_hold(_guarded(_eb_record(probe))) == [
        "A-X presupposes setting at station 1"
    ]


def test_g5_finds_a_party_without_its_laboratory_row() -> None:
    def edit(record: dict[str, Any]) -> None:
        manifest = record["payload"]["assumption_manifest"]
        manifest["assumptions"] = [
            entry for entry in manifest["assumptions"] if entry["short_id"] != "A-LAB"
        ] + [_laboratory("A")]
    record = _eb_record()
    edit(record)
    (found,) = g5_one_laboratory_per_party(_guarded(record))
    assert found.startswith("party B has 0 engaged A-LAB row(s)")


def test_g7_finds_the_source_replacement_root_on_an_untrusted_run() -> None:
    record = _eb_record(roots={"transmitter": ["transmitter/fact:sr"]})
    assert g7_roots_follow_the_mode(_guarded(record)) == [
        "untrusted run names transmitter/fact:sr as a root"
    ]
