"""The key-rate report's readability pass: the setup and rate beside the number.

The report holds two presentation rules:

- R1: the setup and the rate's unit beside the key length: source, loss,
  detector efficiency, dark counts and the post-processing costs near the
  number, the rate defined as bits per transmitted signal with the discarded
  rounds counted;
- R4: each quantity explained before its symbol, short decimals in the main
  text, long fractions and claim ids one link or one fold away.

A QKD researcher's reading of the report added these: the at-a-glance lines
one plain sentence each, their claim links and qualifiers in the section each
links; what a round is said before the protocol; the run settings that could
lengthen the key said to be run settings; the outcome list only where no table
names every outcome; the expected statistics' model and parameters; a budget
said to be a security parameter; the snaps before the long assumptions; the
operator tables explained and folded in HTML; the honest distribution of a
premise linked to the acceptance table instead of repeated.

A second reader's reading followed: the box as bold-led fragments with the
nuances one subsection down (Key rate considerations), one list of what
consumes key, the guarantee leading with its message and its review status a
list, the roles a run lacks a list, the snaps in the appendix, each premise's
table first with its text folded, long tables folded in HTML with a line
saying what they hold, parameter names defined, a registered source linked,
and symbols set as such in HTML.

Each test states a fact a reader relies on; the expected texts are written
by hand from the record or the fixture, never read back from the renderer.
No number the report states is changed by these tests' subject.
"""

from __future__ import annotations

import gzip
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any

from tests.support.report_records import (
    as_first_order,
    completed_record,
    snapped_record,
    synthetic_table,
)

from certiqs_key.runs.report import (
    build_report,
    build_sweep_report,
    default_contract_link,
    render_html,
    render_markdown,
    render_sweep_markdown,
)
from certiqs_key.runs.report.explain import costs, setup_brief
from certiqs_key.runs.report.inputs import (
    analysed_words,
    exact_with_decimal,
    upper_decimal,
)
from certiqs_key.runs.report.model import KeyRateReport

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "runs" / "report_examples"


def _example(name: str) -> dict[str, Any]:
    folder = EXAMPLES / name
    plain = folder / "record.json"
    if plain.is_file():
        loaded: dict[str, Any] = json.loads(plain.read_text(encoding="utf-8"))
        return loaded
    with gzip.open(folder / "record.json.gz", "rt", encoding="utf-8") as handle:
        zipped: dict[str, Any] = json.load(handle)
        return zipped


def md(report: KeyRateReport) -> str:
    return render_markdown(report, contract_link=default_contract_link())


def between(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


# --------------------------------------------------------------------------
# R1: the rate and the costs beside the key length
# --------------------------------------------------------------------------


def test_the_rate_is_defined_where_it_is_given() -> None:
    # optical_bb84: 1,810 bits from 10,000 rounds, trusted source.
    summary = build_report(_example("optical_bb84"))["sections"]["summary"]
    assert ("outputs a key of \u2113 = 1,810 bits: a key rate of 0.181 bits per "
            "round, \u2113 divided by all n rounds, the rounds that give no raw "
            "key bit included (each round sends one signal, so this is also the "
            "rate per signal sent).") in summary["result"]
    # optical_bb84's devices are ideal, so the idealised fragment comes first;
    # the key rate has a fragment of its own.
    glance = [(item["lead"], item["text"]) for item in summary["at_a_glance"]]
    assert [lead for lead, _ in glance[:4]] == [
        "Idealised example", "Optical BB84 with a characterized receiver",
        "Key length \u2113 = 1,810 bits", "Key rate \u2113/n = 0.181 bits per round",
    ]
    assert glance[3][1] == ", every round counted"
    # On bbm92's untrusted run "every round counted" says it: no parenthesis
    # on what one round delivers.
    bbm92 = build_report(_example("bbm92"))["sections"]["summary"]
    assert "untrusted source delivers" not in bbm92["result"]
    assert "the rounds that give no raw key bit included. Its security" in (
        bbm92["result"])


def test_the_costs_are_the_records_deductions_named_before_their_symbols() -> None:
    # optical_bb84's record: lambda_EC 0, verification 30, privacy
    # amplification 21 * 30 = 630 (stored as 629.9999999999994), one bit back.
    report = build_report(_example("optical_bb84"))
    deductions = report["sections"]["result"]["deductions"]
    assert deductions is not None
    assert deductions["privacy_amplification"] == 629.9999999999994
    # One list that adds up: n h_cert = 10,000 x 0.2469219838151957 (the
    # record's certified bound) = 2,469.22; less 0, 30 and 630, plus one,
    # 1,810.22, rounded down to 1,810; k_auth 0 declared, net 1,810.
    assert report["sections"]["summary"]["costs"] == [
        "The accumulated entropy, bounded below by n·h_cert \u2248 2,469.2 bits "
        "(n = 10,000 rounds, h_cert = 0.246922 bits per round).",
        "Less 0 bits that error correction reveals (λ_EC, as declared).",
        "Less a 30-bit hash for error verification (⌈log₂(1/ε_EV)⌉).",
        "Less 630 bits that privacy amplification costs for a finite key "
        "(\u03b1/(\u03b1\u22121)·log₂(1/ε_PA)).",
        "Plus one bit, a constant of the bound: its source's derivation adds "
        "two, and one of them pays for announcing whether error verification "
        "passed ([[meat-core/rem:plus2]]).",
        "Rounded down to a whole bit, the key length is \u2113 = 1,810 bits.",
        "Authentication consumes k_auth = 0 bits of pre-shared key per run "
        "(declared); an aborted run may consume as many.",
        "You gain \u2113 \u2212 k_auth = 1,810 bits.",
    ]
    page = md(report)
    result = between(page, 'id="result"', 'id="setup-brief"')
    assert ("From the accumulated entropy to the key you gain ([Theorem \"Secrecy "
            "of the key from the accumulated entropy\"]") in result
    assert "- Authentication consumes k_auth = 0 bits" in result
    # The net key is said once, in the list, not in the result paragraph.
    assert "Net of the pre-shared key" not in page
    # The record holds them; without excerpts the pointer is shown as code.
    assert "Record: `/payload/stages/key_rate/deductions`." in result


def test_a_hash_penalty_and_a_fractional_cost_are_said() -> None:
    def deductions(record: dict[str, Any]) -> None:
        record["payload"]["stages"]["key_rate"]["deductions"] = {
            "error_correction_lambda_ec": 1200.0,
            "error_verification": 30.0,
            "privacy_amplification": 535.7142857142857,
            "accepted_state_flag_bonus": 1.0,
            "two_universal_hash_penalty": 1.0,
        }

    report = build_report(completed_record(edit=deductions), table=synthetic_table())
    lines = report["sections"]["summary"]["costs"]
    assert "Less 1,200 bits that error correction reveals (λ_EC, as declared)." in (
        lines)
    assert any(line.startswith("Less 535.7 bits that privacy amplification costs")
               for line in lines)
    # The penalty is the privacy-amplification hash's, not verification's.
    assert ("Less a further 1 bit(s), since the privacy-amplification family is "
            "only two-universal, not ideal ([[meat-core/req:hash-penalty]]).") in lines
    assert any(line.startswith("Plus one bit, a constant of the bound")
               for line in lines)
    assert any(line.startswith("Rounded down to a whole bit") for line in lines)


def test_no_key_length_states_no_costs() -> None:
    report = build_report(_example("refused"))
    assert report["sections"]["result"]["deductions"] is None
    assert report["sections"]["summary"]["costs"] == []
    assert costs(report["sections"]["result"], 0) == []


def test_the_setup_in_brief_follows_the_result_with_loss_and_detectors() -> None:
    page = md(build_report(_example("optical_bb84")))
    brief = between(page, 'id="setup-brief"', 'id="guarantee"')
    assert "- Channel: transmittance 1 (no loss)." in brief
    assert ("4 detectors (detection efficiency 1, dark-click probability per "
            "round 0)") in brief


def test_a_transmittance_reads_with_its_loss_in_decibels() -> None:
    setup: Any = {
        "source": {"mode": "trusted", "trusted": True, "honest_model": None,
                   "honest_parameters": {"transmittance": "1/2"}},
        "stations": [{
            "name": "Bob's station", "route": "element-graph", "elements": [],
            "photon_cutoff": None,
            "detectors": [
                {"port": "H", "modes": None,
                 "parameters": {"efficiency": "4/5",
                                "dark-click probability per round": 1e-6}},
                {"port": "V", "modes": None,
                 "parameters": {"efficiency": "9/10",
                                "dark-click probability per round": 1e-6}},
            ],
        }],
    }
    lines = setup_brief(setup, [], None)
    assert "Channel: transmittance 0.5 (3.01 dB loss)." in lines
    assert ("Bob's station: an optical element graph, 2 detectors (detection "
            "efficiency 0.8 to 0.9, dark-click probability per round 1e-06).") \
        in lines


def test_the_sweep_gives_each_points_rate() -> None:
    folder = EXAMPLES / "sweep-bb84"
    records = [json.loads(path.read_text(encoding="utf-8"))
               for path in sorted(folder.glob("run-*.json"))]
    page = render_sweep_markdown(
        build_sweep_report(records), contract_link=default_contract_link(),
        point_link=lambda point: f"points/{point['index']:04d}.md",
    )
    summary = between(page, 'id="points-summary"', 'id="guarantee"')
    assert "| Key length | Bits per round | ε |" in summary
    # Point 0: 1,170 bits from 10,000 rounds.
    assert "| 1,170 | 0.117 |" in summary
    assert ("Bits per round is a point's key length divided by all its n "
            "rounds") in summary


# --------------------------------------------------------------------------
# R4: the quantity before its symbol, decimals first
# --------------------------------------------------------------------------


def test_an_upper_bound_is_rounded_up_when_shown_short() -> None:
    star = ("12274314747403010828602090626394071406757370061721672840037/"
            "26328072917139296674479506920917608079723773850137277813577744384")
    # 4.6620...e-07: three digits rounded down would understate the bound.
    assert upper_decimal(star) == ("4.67e-07", False)
    assert upper_decimal("1/1000000") == ("1e-06", True)
    assert upper_decimal("9995/10000000") == ("0.001", False)
    assert upper_decimal("1") == ("1", True)
    assert upper_decimal("not a number") is None


def test_completeness_leads_with_the_chance_and_folds_the_fraction() -> None:
    page = md(build_report(_example("optical_bb84")))
    guarantee = between(page, 'id="guarantee"', 'id="vouch"')
    assert ("Completeness. On this run an honest run fails the acceptance test "
            "with probability at most 4.67e-07 (ε\\*, rounded up; [its exact "
            "value](#setup-acceptance)).") in guarantee
    assert "/26328072917139296674479506920917608079723773850137277813577744384" \
        not in guarantee
    acceptance = between(page, 'id="setup-acceptance"', 'id="setup-expected"')
    assert ("An honest run fails it with probability at most 4.67e-07 (ε\\*, "
            "rounded up; its exact value is in the table below), within your "
            "completeness budget of 1e-06 (the completeness parameter ε_comp "
            "you allow).") in acceptance
    assert ("| Certified completeness ε\\* | at most 4.67e-07 (rounded up; the "
            "exact fraction is below) |") in acceptance
    # The exact fraction is kept, one fold away.
    assert ("ε\\* = 12274314747403010828602090626394071406757370061721672840037/"
            "26328072917139296674479506920917608079723773850137277813577744384"
            ) in acceptance


def test_decimals_come_first_with_the_exact_value_beside() -> None:
    assert exact_with_decimal("205/2048") == "0.100098 (205/2048)"
    assert exact_with_decimal("1/8") == "0.125"
    assert exact_with_decimal(3) == "3"
    assert analysed_words("205/2048", "1/10") == (
        "0.100098 (exactly 205/2048; requested 0.1)")
    page = md(build_report(_example("optical_bb84")))
    inputs = between(page, 'id="inputs-budget"', 'id="inputs-engine"')
    # A budget of 2^-30 is shown short, its power of two exact.
    assert "| 9.31e-10 (2^-30) |" in inputs
    assert ("the number of rounds (n), total channel uses") in inputs


def test_the_summarys_claims_read_by_title() -> None:
    page = md(build_report(_example("optical_bb84")))
    summary = between(page, 'id="summary"', 'id="setup"')
    assert '[Remark "What a certified number rests on"]' in summary
    assert ('[Requirement "The check of the acceptance set against the feasible '
            'statistics"]') in summary
    assert "[meat-core/req:unreachable-acceptance-set]" not in summary
    assert "[meat-core/frank-wolfe/rem:certified-scope]" not in summary


def test_the_certified_basis_names_the_quantity_before_h_cert() -> None:
    result = build_report(_example("optical_bb84"))["sections"]["summary"]["result"]
    assert ("The key length rests on a certified lower bound, h_cert, on the "
            "attacker's worst-case uncertainty per round about the raw key.") in result


# --------------------------------------------------------------------------
# A QKD researcher's reading
# --------------------------------------------------------------------------

#: A ``[[...]]`` token that names a claim (its id holds a slash); a premise's
#: short id (``[[A-SNAP]]``) holds none.
_CLAIM_LINK = re.compile(r"\[\[[^\]]*/[^\]]*\]\]")


def _premise(page: str, short_id: str) -> str:
    """Return one premise's part of a Markdown page, up to the next heading."""
    start = page.index(f'<a id="{short_id}"></a>')
    heading = re.compile(r"\n#{2,5} ").search(page, start)
    return page[start:heading.start() if heading else len(page)]


def test_the_box_holds_fragments_and_the_considerations_hold_the_nuances() -> None:
    """Each fragment bold-led and linked; no claim link in the box.

    Everything the box no longer says stands one subsection down, still in
    the summary: each consideration one sentence with its link.
    """
    for name in ("bbm92", "optical_bb84", "document-bbm92_holder_b", "bb84"):
        summary = build_report(_example(name))["sections"]["summary"]
        for item in summary["at_a_glance"]:
            assert item["lead"] and item["anchor"], (name, item)
            assert not _CLAIM_LINK.search(item["lead"] + item["text"]), (name, item)
            assert not item["text"].endswith("."), (name, item)
        for line in summary["considerations"]:
            assert line["anchor"], (name, line)
            if not line["text"].startswith("What is idealised"):
                assert not _CLAIM_LINK.search(line["text"]), (name, line)
                assert not re.search(r"\.\s+[A-Z]", line["text"]), (name, line)
    page = md(build_report(_example("bbm92")))
    top = between(page, 'id="summary"', 'id="result"')
    assert ("> - **Key length \u2113 = 40,192,819 bits** from n = 100,000,000 rounds "
            "([The result](#result))") in top
    assert ("> - **Key rate \u2113/n = 0.402 bits per round**, every round counted "
            "([The result](#result))") in top
    considerations = between(page, 'id="considerations"', 'id="result"')
    # bbm92's run is not checked against its model: A-REACH is the reader's.
    assert ("- The accepted statistics were not checked against your declared "
            "model, so that a state your declared devices admit can produce them "
            "([A-REACH](#A-REACH)) is yours to vouch for. See [The result]"
            "(#result).") in considerations
    assert "- The key length is certified: " in considerations


def test_the_qualifiers_stand_where_each_line_points() -> None:
    report = build_report(_example("optical_bb84"))
    summary = report["sections"]["summary"]
    lines = {item["text"].split(":", 1)[0]: item for item in summary["considerations"]}
    certified = lines["The key length is certified"]
    assert certified["text"] == (
        "The key length is certified: its bound was formed again with every "
        "arithmetic step exact or rigorously enclosed, so the certified "
        "evaluation adds no premise about numerics; the premises the run lists "
        "remain.")
    assert certified["anchor"] == "how-computed"
    how = between(md(report), 'id="how-computed"', 'id="security-claims"')
    assert ("the premises of the run remain ([Corollary \"Key length from the "
            "certified bracket\"]") in how
    (check,) = [item for item in summary["considerations"]
                if item["text"].startswith("The accepted statistics")]
    assert check["anchor"] == "result"
    assert "[[meat-core/req:unreachable-acceptance-set]]" in summary["result"]


def test_the_run_settings_that_could_lengthen_the_key_say_what_they_are() -> None:
    page = md(build_report(_example("bbm92")))
    contents = between(page, 'id="contents"', 'id="summary"')
    assert "[Choices that could lengthen the key](#levers)" in contents
    levers = between(page, 'id="levers"', 'id="setup"')
    assert levers.startswith('id="levers"></a>Choices that could lengthen the key')
    assert ("These are run settings that change \u2113 without changing your "
            "devices or the security statement. Your device values change it "
            "too; a sweep over them shows how.") in levers
    assert "What would change the number" not in page


def test_with_a_snap_fix_the_lead_excepts_it() -> None:
    from certiqs_key.runs.report.explain import LEVERS_SNAP

    assert LEVERS_SNAP == (
        "The settings below other than a measurement-snap fix change \u2113 "
        "without changing your devices or the security statement; a "
        "measurement-snap fix changes which premises the key length rests on "
        "(A-SNAP) as well. Your device values change \u2113 too; a sweep over "
        "them shows how.")


def test_the_expected_statistics_name_their_model_and_its_parameters() -> None:
    record = _example("bbm92")
    # bbm92's honest model ideal_pair at transmittance 1 and visibility 1; its
    # mean pair number has no effect under these values and is not named. The
    # statistics are what the declared stations record.
    setup = build_report(record)["sections"]["setup"]
    assert setup["expected_basis"] == (
        "These statistics are expected from the honest model ideal_pair, "
        "evaluated with its parameters at their ideal values (transmittance 1, "
        "visibility 1), as your declared stations record them (with their "
        "detector efficiencies, dark counts and settings; see the stations "
        "above).")
    record["payload"]["config"]["model"].update(
        alice_transmittance="1/2", bob_transmittance="1/2", visibility="49/50")
    report = build_report(record)
    assert report["sections"]["setup"]["expected_basis"].startswith(
        "These statistics are expected from the honest model ideal_pair, "
        "evaluated with Alice's transmittance 0.5, Bob's transmittance 0.5 and "
        "visibility 0.98, as your declared stations record them")
    expected = between(md(report), 'id="setup-expected"', 'id="inputs"')
    assert ("These statistics are expected from the honest model ideal_pair, "
            "evaluated with Alice's transmittance 0.5") in expected
    # With a supplied distribution the record does not tie the raw joint
    # distribution, the statistics' source, to it: the sentence says no more.
    record["payload"]["honest_model_note"] = {"overridden": True, "model": "table"}
    assert build_report(record)["sections"]["setup"]["expected_basis"] == (
        "These statistics come from the record's honest raw joint distribution; "
        "the acceptance test is built around a distribution supplied with the "
        "run in place of the instance's honest model, so the two need not agree.")


def test_a_budget_is_said_to_be_an_epsilon_you_choose() -> None:
    page = md(build_report(_example("optical_bb84")))
    budgets = between(page, 'id="inputs-budget"', 'id="inputs-engine"')
    assert budgets.startswith('id="inputs-budget"></a>Budgets (the ε you choose)')
    assert ("A budget is an error probability (an ε) you choose before the run. "
            "ε_PA, ε_EV and ε_auth make up the security parameter "
            "ε = ε_PA + ε_EV + 2ε_auth. The completeness budget ε_comp is not "
            "part of ε: it bounds only how often an honest run fails the "
            "acceptance test.") in budgets
    glossary = page[page.index('id="glossary"'):]
    assert ('<a id="g-budget"></a>budget: An error probability (an ε) that you '
            "choose before the run.") in glossary


def test_the_snaps_are_in_the_appendix_and_the_summary_keeps_their_status() -> None:
    page = md(build_report(_example("bbm92")))
    assert (page.index('id="inputs"') < page.index('id="assumptions"')
            < page.index('id="appendix"') < page.index('id="measurement-snaps"')
            < page.index('id="snaps-detail"'))
    contents = between(page, 'id="contents"', 'id="summary"')
    appendix = next(line for line in contents.splitlines()
                    if line.startswith("- [Appendix]"))
    assert ("[How the number was computed](#how-computed) · [Measurement snaps]"
            "(#measurement-snaps) · [Measurement snaps in detail](#snaps-detail)"
            ) in appendix
    # A run resting on A-SNAP says so in the summary's considerations.
    snapped = build_report(snapped_record(), table=synthetic_table())
    assert any(line["text"].startswith("Some moved measurement blocks rest on "
                                       "[[A-SNAP]]")
               and line["anchor"] == "measurement-snaps"
               for line in snapped["sections"]["summary"]["considerations"])


def test_the_long_tables_are_folded_in_html_with_what_they_hold() -> None:
    report = build_report(_example("bbm92"))
    station = between(md(report), 'id="station-alice_station"',
                      'id="station-bob_station"')
    lead = ("Why these tables are shown: they are the measurement the key length "
            "is computed for, which [A-EXACT](#A-EXACT) and [A-SPEC](#A-SPEC) ask "
            "you to vouch for as your receiver's. What to check: that the 1-photon "
            "operators agree with your detectors' efficiencies and the splitting "
            "ratios above, and that the table with dark counts agrees with your "
            "dark-count probability.")
    assert lead in station
    assert station.index(lead) < station.index("#### POVM per photon number")
    # Markdown has no fold; HTML folds each form and the acceptance table
    # under a line that says what it holds.
    page = render_html(report, contract_link=default_contract_link())
    for summary in (
        "POVM per photon number: one operator table per outcome and photon "
        "number, before dark counts",
        "POVM with dark counts: the same with the declared dark counts composed in",
        "Squashed target POVM: the finite model the proof analyses in place of "
        "the device",
        "Acceptance categories: the honest probability, the allowed frequency and "
        "the allowed count of each of the 79 outcomes",
    ):
        assert f"<details><summary>{summary}</summary>" in page, summary


def test_each_premise_shows_its_table_first_and_folds_its_text() -> None:
    report = build_report(_example("bbm92"))
    page = render_html(report, contract_link=default_contract_link())
    entry = page[page.index('id="A-REACH"'):]
    entry = entry[:entry.index("<h", 10)]
    assert entry.index("<table>") < entry.index(
        "<details><summary>A-REACH in full: its text and what it binds on this "
        "run</summary>")
    assert "<td>At stake</td>" in entry


def test_what_consumes_key_is_one_list() -> None:
    page = md(build_report(_example("bbm92")))
    result = between(page, 'id="result"', 'id="setup-brief"')
    # bbm92: k_auth 0 declared, so the key length is the net key.
    assert ("- Authentication consumes k_auth = 0 bits of pre-shared key per run "
            "(declared); an aborted run may consume as many.\n- You gain \u2113 "
            "\u2212 k_auth = 40,192,819 bits.") in result


def test_the_guarantee_leads_with_its_message_and_lists_the_review_status() -> None:
    page = md(build_report(_example("bbm92")))
    guarantee = between(page, 'id="guarantee"', 'id="roles"')
    assert guarantee.index("A run either aborts") < guarantee.index("| Parameter")
    assert guarantee.index("| Parameter") < guarantee.index("Completeness. On this run")
    assert guarantee.index("Completeness. On this run") < guarantee.index(
        "One execution.") < guarantee.index("[Review status](#status-legend): the "
                                            "lowest status of the claims below")
    assert "\n- [Corollary \"Security of the protocol and its net key\"]" in guarantee


def test_the_roles_a_run_lacks_are_a_list() -> None:
    page = md(build_report(_example("bbm92")))
    roles = between(page, 'id="roles"', 'id="vouch"')
    assert ("Not on this run, so the parts of the premises that apply only with "
            "them do not apply here (each premise says which):\n\n"
            "- A trusted source: the source is untrusted.\n") in roles


def test_html_sets_a_symbols_subscript_and_markdown_leaves_it_unescaped() -> None:
    report = build_report(_example("optical_bb84"))
    page = render_html(report, contract_link=default_contract_link())
    assert "ε<sub>PA</sub>" in page and "2<sup>\u221229</sup>" in page
    assert "ε_PA" in md(report) and "ε\\_PA" not in md(report)


def test_the_honest_distribution_links_the_acceptance_table() -> None:
    record = _example("bbm92")
    report = build_report(record)
    page = md(report)
    for short_id in ("A-HON-ENV", "A-REACH"):
        part = _premise(page, short_id)
        assert ("- honest_distribution: the honest probability of each "
                "acceptance outcome, as in [the table under Acceptance test]"
                "(#setup-acceptance)") in part
        assert "characters; in full below" not in part
    # Without the table, the premise lays out the nonzero entries itself.
    honest = record["payload"]["stages"]["acceptance_construction"][
        "honest_distribution"]
    nonzero = sum(1 for value in honest.values() if Fraction(str(value)) != 0)
    zero = next(key for key, value in honest.items() if Fraction(str(value)) == 0)
    acceptance = report["sections"]["setup"]["acceptance"]
    assert acceptance is not None
    acceptance["categories"] = []
    acceptance["honest"] = []
    part = _premise(md(report), "A-REACH")
    assert (f"- honest_distribution: {nonzero} nonzero of {len(honest)} "
            "probabilities, in the table below") in part
    assert "| gen |" in part
    assert f"| {zero.replace('|', chr(92) + '|')} |" not in part


def test_on_a_first_order_run_the_snaps_say_the_bound_is_at_the_centres() -> None:
    # The fixture's block m=1 is moved and evaluated off its snap on an
    # enclosed reference; the fixture is a first-order run.
    first_order = build_report(snapped_record(), table=synthetic_table())
    snaps = first_order["sections"]["protocol"]["measurement_snaps"]
    assert snaps is not None
    assert any(sentence.endswith(
        "; on this first-order run, where your model is known only through "
        "rigorous intervals, the bound is evaluated at their centres "
        "([[meat-core/frank-wolfe/rem:fo-arithmetic]]).")
        for sentence in snaps["plain"])
    record = snapped_record()
    record["payload"]["stages"]["key_rate"]["reported_tier"] = "certified"
    certified = build_report(record, table=synthetic_table())["sections"][
        "protocol"]["measurement_snaps"]
    assert certified is not None
    assert not any("centres" in sentence for sentence in certified["plain"])


# --------------------------------------------------------------------------
# The experimentalist reader's findings and the summary's additions
# --------------------------------------------------------------------------


def test_free_authentication_is_said_only_where_nothing_is_counted() -> None:
    # bbm92: ε_auth 0 and k_auth 0, an idealisation said at a glance.
    leads = [item["lead"] for item in build_report(_example("bbm92"))["sections"][
        "summary"]["at_a_glance"]]
    assert "Free authentication" in leads
    # A run that declares a pre-shared key for authentication pays for it.
    paid = build_report(completed_record(k_auth=7, net_key_length=12_338),
                        table=synthetic_table())
    assert "Free authentication" not in [
        item["lead"] for item in paid["sections"]["summary"]["at_a_glance"]]


def test_budget_means_only_the_epsilon_you_choose() -> None:
    page = md(build_report(as_first_order(_example("bbm92"))))
    summary = between(page, 'id="summary"', 'id="setup"')
    # The floating-point arithmetic has no bound on its rounding error, said so;
    # "budget" is left to the ε you choose (A-FIXED's "error budgets").
    assert "no error budget" not in summary
    # Not only rounding: on a reference companion the bound is evaluated at
    # the centres of the intervals too (rem:fo-arithmetic).
    assert "no bound on its numerical error" in summary
    assert "no bound on their numerical error" in summary
    assert "rounding error" not in summary
    # The solver's wall-clock limit is a time limit; its key keeps its name.
    record = _example("bbm92")
    record["payload"]["config"]["solver"]["budget_seconds"] = 600
    (row,) = [row for row in build_report(record)["sections"]["protocol"]["inputs"]
              if row["name"] == "solver.budget_seconds"]
    assert (row["label"], row["meaning"]) == (
        "Solver time limit",
        "one solver-wide wall-clock time limit, including all attempts and "
        "assessments")


def test_the_result_says_plainly_why_h_lb_is_not_proved() -> None:
    result = build_report(as_first_order(_example("bbm92")))["sections"]["summary"][
        "result"]
    assert ("The bound's proof is exact, and the minima it uses are bounded from "
            "below in exact arithmetic, not taken from the solver. Its objective "
            "and gradient, though, are computed in floating point with no bound "
            "on their numerical error, so the computed h_lb is not proved to lie "
            "below h_low") in result


def test_what_you_vouch_for_counts_in_a_table_and_says_what_stale_texts_mean() -> None:
    page = md(build_report(_example("bbm92")))
    vouch = between(page, 'id="vouch"', 'id="not-counted"')
    # bbm92: 26 premises by their recorded affects: 25 put security at stake,
    # none about a supplied artefact (A-RECV discharged on the run's own exact,
    # rigorous receiver artefacts; A-LINK on its attested links); A-HON-ENV
    # completeness only.
    assert ("| Premises of this run | Count |\n| --- | --- |\n"
            "| Can break security if they fail | 25 |\n"
            "| Affect only completeness") in vouch
    assert "| All premises of this run | 26 |" in vouch
    assert "of them, about artefacts supplied to the engine" not in vouch
    # decoy keeps A-LINK, its chain not attested: the artefact row and group.
    decoy = between(md(build_report(_example("decoy_bb84"))), 'id="vouch"',
                    'id="not-counted"')
    assert ("| Can break security if they fail | 26 |\n"
            "| of them, about artefacts supplied to the engine and its numerics "
            "| 1: A-LINK |\n") in decoy
    assert "| All premises of this run | 27 |" in decoy
    assert "Artefacts and the engine (1):\n\n- [A-LINK](#A-LINK): Every link " in decoy


# --------------------------------------------------------------------------
# The soundness review of the experimentalist round and a lab reader
# --------------------------------------------------------------------------


def test_an_older_engines_premise_is_read_by_the_current_contract() -> None:
    """The note says the current text is the one to vouch for; so is its reading.

    A-ALPHABET as an older engine froze it: completeness only, an earlier
    text. The current contract puts secrecy at stake as well, so the
    premise counts as able to break security and its one-liner is the
    current summary's first sentence.
    """
    record = _example("bbm92")
    for entry in record["payload"]["assumption_manifest"]["assumptions"]:
        if entry["short_id"] == "A-ALPHABET":
            entry["affects"] = ["completeness"]
            entry["user_statement"] = "An earlier wording of this premise."
            entry["summary"] = "An earlier summary. With a second sentence."
    summary = build_report(record)["sections"]["summary"]
    (line,) = [line for group in summary["vouch"] for line in group["entries"]
               if line["short_id"] == "A-ALPHABET"]
    assert line["consequence"] == "security"
    assert line["summary"] == ("In every one of the n rounds of the run an "
                               "acceptance value of the alphabet is recorded.")
    assert "A-ALPHABET" in summary["stale"]
    page = md(build_report(record))
    assert ("Vouch for both texts; where they differ, the stricter one "
            "applies.") in page
    entry = page[page.index('<a id="A-ALPHABET"></a>'):]
    assert "| If it fails | security (the key may leak) |" in entry[:2000]


def test_the_review_status_names_the_premises_outside_its_claims() -> None:
    guarantee = build_report(_example("bbm92"))["sections"]["summary"]["guarantee"]
    assert guarantee is not None and guarantee["outside"] is not None
    # A receiver premise is outside the security statement's closure; the
    # laboratory, authentication and seed premises are inside it.
    assert "A-EXACT" in guarantee["outside"]
    assert not {"A-LAB", "A-AUTH", "A-SEED"} & set(guarantee["outside"])


def test_free_authentication_is_compared_to_devices_only_where_they_are_ideal() -> None:
    def free(record: dict[str, Any]) -> str:
        (item,) = [item for item in build_report(record)["sections"]["summary"][
            "at_a_glance"] if item["lead"] == "Free authentication"]
        return item["text"]

    # bbm92's committed devices are ideal: the comparison holds.
    assert free(_example("bbm92")).endswith("an idealisation like the device values")
    # With characterised devices there is no device idealisation to compare to.
    record = _example("bbm92")
    device = record["payload"]["config"]["device"]
    for party in ("alice", "bob"):
        device[f"{party}_efficiency"] = dict.fromkeys("HVDA", "9/10")
        device[f"{party}_dark_count"] = dict.fromkeys("HVDA", "1/1000000")
        device[f"{party}_pbs_leak_transmitted"] = "1/1000"
        device[f"{party}_pbs_leak_reflected"] = "1/100"
    assert free(record).endswith("k_auth = 0), an idealisation")


def test_a_key_length_clamped_at_zero_says_so() -> None:
    def deductions(record: dict[str, Any]) -> None:
        key_rate = record["payload"]["stages"]["key_rate"]
        key_rate["deductions"] = {
            "error_correction_lambda_ec": 1e12, "error_verification": 30.0,
            "privacy_amplification": 630.0, "accepted_state_flag_bonus": 1.0,
            "two_universal_hash_penalty": 0.0,
        }

    report = build_report(completed_record(key_length=0, net_key_length=0,
                                           edit=deductions),
                          table=synthetic_table())
    assert ("Rounded down to a whole bit and clamped at 0, the key length is "
            "\u2113 = 0 bits.") in report["sections"]["summary"]["costs"]


def test_the_epsilon_parenthesis_names_twice_the_authentication_error() -> None:
    from certiqs_key.runs.report.explain import at_a_glance

    result = build_report(_example("bbm92"))["sections"]["result"]
    result["security_parameter"]["terms"]["eps_auth"] = 1e-10
    box, _ = at_a_glance(result, 28, None)
    (item,) = [item for item in box if item["lead"].startswith("Security parameter")]
    assert item["text"].endswith(
        "(ε_PA = 9.31e-10, ε_EV = 9.31e-10, 2ε_auth = 2e-10)")


def test_the_premises_are_said_to_be_sufficient_not_necessary() -> None:
    glance = build_report(_example("bbm92"))["sections"]["summary"]["at_a_glance"]
    (item,) = [item for item in glance if item["lead"].endswith("premises")]
    assert item["text"] == (" for you to vouch for: the key length and \u03b5 are "
                            "guaranteed when all of them hold")


def test_a_first_order_run_names_the_gap_no_premise_covers() -> None:
    # cor:composed-security: a first-order run also needs its computed
    # h_lb <= h_low, which no premise covers; the sufficiency line says so.
    from certiqs_key.runs.report.explain import at_a_glance

    result = build_report(_example("bbm92"))["sections"]["result"]
    result["reported_tier"] = "first-order"
    box, _ = at_a_glance(result, 28, None)
    (item,) = [item for item in box if item["lead"].endswith("premises")]
    assert item["text"].endswith(
        "when all of them hold and the computed h_lb lies below h_low, which no "
        "premise covers")


def test_a_first_order_entropy_line_states_no_lower_bound() -> None:
    # thm:firstorder: the computed h_lb is not proved to lie below h_low.
    report = build_report(_example("optical_bb84"))
    first = costs(report["sections"]["result"], 0, ("h_lb", 0.25))[0]
    assert first.startswith(
        "The accumulated entropy as the computed first-order bound "
        "gives it, n·h_lb "
        "\u2248 2,500 bits (not proved to lie below n·h_low; n = 10,000 rounds")
    assert "bounded below" not in first


def test_the_constant_bit_reads_by_its_title() -> None:
    page = md(build_report(_example("bbm92")))
    assert '[Remark "The constant in the key length and the source\'s convention"]' in (
        page)

