"""The run report as a reader finds it: at a glance, the setup, links, prose.

Each test states what the reader finds; the expectations are written by hand from the
bbm92
example's record or a fixture, never read back from the renderer.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

from tests.support.report_records import (
    as_first_order,
    refused_record,
    snapped_record,
    synthetic_table,
)

from certiqs_key.runs.report import build_report, default_contract_link, render_markdown
from certiqs_key.runs.report.build import _mentions, _Table
from certiqs_key.runs.report.explain import FO_ARITHMETIC_CLAIM
from certiqs_key.runs.report.glossary import terms
from certiqs_key.runs.report.model import EmissionSnap, KeyRateReport
from certiqs_key.runs.report.setup import _paths, build_setup
from certiqs_key.runs.report.snaps import resting_sectors

ROOT = Path(__file__).resolve().parents[2]
BBM92 = ROOT / "runs" / "report_examples" / "bbm92" / "record.json.gz"


def record() -> dict[str, Any]:
    with gzip.open(BBM92, "rt", encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
        return data


def bbm92() -> KeyRateReport:
    return build_report(record())


def bbm92_first_order() -> KeyRateReport:
    """Return the bbm92 example read as a first-order run (``as_first_order``)."""
    return build_report(as_first_order(record()))


def md(report: KeyRateReport) -> str:
    return render_markdown(report, contract_link=default_contract_link())


def between(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


# --------------------------------------------------------------------------
# At a glance
# --------------------------------------------------------------------------


def test_at_a_glance_names_the_number_and_what_it_is_conditional_on() -> None:
    """The box: terse fragments, the key part in bold; the nuances beneath it."""
    # On a first-order run (the committed example certifies), read off
    # ``as_first_order``.
    report = bbm92_first_order()
    summary = report["sections"]["summary"]
    items = summary["at_a_glance"]
    result = report["sections"]["result"]
    # Every premise of the run, those about artefacts and the engine included,
    # stands in one of the three groups.
    premises = sum(1 + len(line["refinements"]) for group in summary["vouch"]
                   for line in group["entries"])
    # bbm92's devices are ideal: one short fragment says so first; then the
    # setup (no loss, efficiency 1, its honest statistics at visibility 1 with
    # no dark counts give QBER 0), the number, the ε its budgets set (2^-30
    # each), and authentication at no cost (ε_auth 0, k_auth 0).
    assert [(item["lead"], item["text"], item["anchor"]) for item in items] == [
        ("Idealised example", ", not a characterised device", "inputs"),
        ("BBM92 with two passive stations",
         ", no loss, detector efficiency 1, expected QBER 0", "setup"),
        (f"Key length \u2113 = {result['key_length']:,} bits",
         f" from n = {result['rounds']:,} rounds", "result"),
        (f"Key rate \u2113/n = {result['rate_per_round']:.3g} bits per round",
         ", every round counted", "result"),
        ("Security parameter \u03b5 = 1.86e-09 (2^-29)",
         ", the target you set (ε_PA = 9.31e-10, ε_EV = 9.31e-10)", "guarantee"),
        ("Free authentication",
         ": the run assumes an authenticated classical channel at no cost "
         "(\u03b5_auth = 0, k_auth = 0), an idealisation like the device values",
         "not-counted"),
        # The bbm92 example declares lambda_EC = 0 (the reader round).
        ("No error-correction cost counted",
         ": \u03bb_EC = 0 as declared, so for a run that sends an "
         "error-correction transcript this key length is too long",
         "not-counted"),
        (f"{premises} premises",
         " for you to vouch for: the key length and \u03b5 are guaranteed when "
         "all of them hold and the computed h_lb lies below h_low, which no "
         "premise covers",
         "vouch"),
        ("Model-based",
         ": no measured data analysed; the acceptance test is built around your "
         "honest model's predictions", "setup-acceptance"),
    ]
    # The considerations, one line each: the statistics, the tier, then what
    # is idealised; bbm92's committed example rests on no snap.
    lines = summary["considerations"]
    assert not any("[[A-SNAP]] (effective" in line["text"] for line in lines)
    assert lines[-1]["text"].startswith(
        "What is idealised: the run's device values")
    assert "([[A-EXACT]])" in lines[-1]["text"]
    assert lines[-2]["text"] == (
        "The key length is a first-order number: its bound is computed in "
        "floating point with no bound on its numerical error, which no premise "
        "covers."
    )
    assert lines[-2]["anchor"] == "how-computed"
    # The qualifiers and the claim stand where the line points.
    note = summary["tier_note"]
    assert note.endswith(f"([[{FO_ARITHMETIC_CLAIM}]]).")
    assert "it is not a key length from verified numerics" in note
    how = between(md(report), 'id="how-computed"', 'id="diagnostics"')
    assert "it is not a key length from verified numerics" in how


def test_at_a_glance_is_the_first_thing_under_the_summary() -> None:
    page = md(bbm92())
    top = between(page, 'id="summary"', 'id="result"')
    assert "> **At a glance**" in top
    assert ("> - **Security parameter ε = 1.86e-09 (2^-29)**, the target you set "
            "(ε_PA = 9.31e-10, ε_EV = 9.31e-10) ([What the guarantee means]"
            "(#guarantee))") in top
    # The considerations stand right after the box, before the result.
    assert top.index("> **At a glance**") < top.index(
        '<a id="considerations"></a>Key rate considerations')


def test_a_refused_run_says_no_key_at_a_glance() -> None:
    report = build_report(refused_record(), table=synthetic_table())
    (item,) = report["sections"]["summary"]["at_a_glance"]
    assert item["lead"] == "No key"
    assert item["text"].startswith(": the run was refused at its ")
    assert item["text"].endswith(", so nothing is certified")


def test_the_status_legend_has_an_anchor_the_draft_word_links_to() -> None:
    page = md(bbm92())
    assert '#### <a id="status-legend"></a>What a claim\'s status means' in page


# --------------------------------------------------------------------------
# The setup
# --------------------------------------------------------------------------


def test_the_mode_note_points_at_the_readme_without_promising_a_drawing() -> None:
    setup = build_setup(record())
    notes = [note for station in setup["stations"] for note in station["notes"]]
    assert not any("drawn" in note for note in notes)
    assert any("The instance's own description is in instances/bbm92/README.md."
               in note for note in notes)


def test_a_station_identical_to_one_above_points_to_it() -> None:
    part = between(md(bbm92()), 'id="setup"', 'id="inputs"')
    # The anchor is the station's factor label (the per-setting loop of
    # setup.py does not overwrite it with None).
    assert ("Identical to [Alice's station](#station-alice_station): the same "
            "input route") in part
    assert part.count("#### Optical elements") == 1


def test_a_station_whose_only_setting_is_off_says_so_once() -> None:
    setup = build_setup(record())
    for station in setup["stations"]:
        assert any(note.startswith("This station has no probe: its one setting is "
                                   "off") for note in station["notes"])
        titles = [family["title"] for family in station["families"]]
        assert "POVM per photon number" in titles
        assert "POVM with dark counts" in titles
        labels = [block["title"] for family in station["families"]
                  for block in family["blocks"]]
        assert not any(label.startswith("setting off") for label in labels)


def test_beamsplitter_path_words_count_the_output_losses() -> None:
    modes = ["Z_H", "Z_V", "X_H", "X_V"]
    assert _paths("C1", {"transmittance": "1/2"}, modes) == (
        "a photon from path Z stays in path Z with probability 1/2 and otherwise "
        "moves to path X"
    )
    lossy = _paths("C1", {"transmittance": "1/2", "loss_1": "1/10", "loss_2": 0},
                   modes)
    assert lossy == (
        "a photon from path Z goes towards path Z with probability 1/2 and "
        "towards path X with probability 1 \u2212 1/2; output Z then loses a "
        "fraction 1/10 and output X a fraction 0"
    )
    assert "stays" not in _paths(
        "C2", {"transmittance_h": 1, "transmittance_v": 0, "loss_2": "1/5"},
        ["Z_H", "Z_V", "Zr_H", "Zr_V"],
    )


def test_the_acceptance_note_names_every_input_of_the_box() -> None:
    # On a record without the box (before 0.36.0) the note says how the engine
    # builds it; a record with the box lists it (tests/unit/
    # test_record_acceptance_box.py).
    data = record()
    del data["payload"]["stages"]["acceptance_construction"]["box"]
    acceptance = build_setup(data)["acceptance"]
    assert acceptance is not None
    assert ("with the round count n, which outcomes are constrained and how the "
            "budget is split, the engine builds them from these "
            "([[statistics/binomial-box/def:construction]]).") in acceptance["text"]
    # The claim reads by its title, not its id.
    assert ('[Definition "The construction map"](spec/modules/statistics/'
            "contract.pdf#nameddest=claim-statistics/binomial-box/def:construction)"
            ) in md(bbm92())


# --------------------------------------------------------------------------
# Assumptions and the appendix
# --------------------------------------------------------------------------


def test_a_cut_value_without_a_record_link_is_written_in_full() -> None:
    page = md(bbm92())
    assert "characters, written out in full below" in page
    assert "characters; see the record)" not in page


def test_the_engine_s_key_length_reason_is_verbatim_and_explained() -> None:
    page = md(bbm92())
    assert "| key length reason |" not in page
    assert "its capitals are the engine's emphasis, not the report's." in page


def test_a_bare_id_in_a_module_s_emission_rule_links_to_that_module() -> None:
    page = md(bbm92())
    # It reads by its title where the closure table carries the claim.
    assert '[Theorem "Exact emission of a reduction instance"](spec/modules/' \
        "reductions/contract.pdf#nameddest=claim-reductions/thm:emit)" in page
    # A bare id the table lacks stays the id, linked to that module.
    assert "[def:pmcex](spec/modules/receiver/contract.pdf#nameddest=" \
        "claim-receiver/def:pmcex)" in page


def test_a_module_path_outside_the_registered_contracts_stays_plain() -> None:
    table = _Table(synthetic_table())
    found = _mentions(["see nowhere-module/thm:made-up"], set(), table, ())
    assert found == {}


# --------------------------------------------------------------------------
# Prose
# --------------------------------------------------------------------------


def test_composable_does_not_promise_every_later_use() -> None:
    (term,) = [term for term in terms() if term.term == "composable"]
    assert "keeps holding" not in term.text
    assert "not that every later use of the key is covered" in term.text
    assert term.see == "meat-core/rem:repeated-executions"


def test_the_setup_brief_names_the_premises_the_source_is_part_of() -> None:
    brief = bbm92()["sections"]["summary"]["setup_brief"][0]
    # The brief states what the premises cover.
    assert "is part of [[A-LAB]] and [[A-MODES]] under What you vouch for" in brief
    assert "concern Alice's station" not in brief


def test_a_moved_sector_rests_only_where_the_run_did_not_evaluate_it_off() -> None:
    def row(rests: bool) -> EmissionSnap:
        return {"station": None, "data_sector": 3, "moved_classes": [],
                "evaluated_off_snap": not rests, "rests_on_assumption": rests,
                "group": None, "group_fix": None, "pointer": "/x"}

    assert resting_sectors([row(True)]) == [3]
    assert resting_sectors([row(False)]) == []


def test_at_a_glance_names_a_snap_the_run_rests_on_with_its_status() -> None:
    # A hand-built record whose m=2 block rests on A-SNAP; the example records
    # are snapshots of an earlier record shape.
    report = build_report(snapped_record(), table=synthetic_table())
    (snap,) = [item for item in report["sections"]["summary"]["considerations"]
               if item["text"].startswith("Some moved measurement blocks rest on")]
    status = report["sections"]["summary"]["drafts"]
    assert snap["text"].startswith(
        "Some moved measurement blocks rest on [[A-SNAP]] (effective status "
        + ("draft" if "A-SNAP" in status else "")
    )
    assert snap["anchor"] == "measurement-snaps"
    page = render_markdown(report, contract_link=default_contract_link())
    top = between(page, 'id="summary"', 'id="result"')
    assert "effective status [draft](#status-legend)" in top
