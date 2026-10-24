"""The run report's page: summary, inputs, assumptions, diagnostics, appendix.

Report 0.9.0. Each test states a fact about the page a reader relies on;
the expectations are written by hand from the record or the fixture, never
read back from the renderer.
"""

from __future__ import annotations

import gzip
import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from tests.support.report_records import (
    as_first_order,
    completed_record,
    refused_record,
    snapped_record,
    synthetic_table,
)

from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_html,
    render_markdown,
)
from certiqs_key.runs.report._render import RESIDUE_NOTE, format_entry, residue_floor
from certiqs_key.runs.report.explain import (
    STATUS_LEGEND,
    about,
    partition_words,
    places,
    role_notes,
    roles_absent,
    roles_box,
)
from certiqs_key.runs.report.model import AssumptionEntry, KeyRateReport
from certiqs_key.runs.report.render_markdown import escape_markdown
from certiqs_key.runs.roles import PublicChoice, Roles, StationRoles

ROOT = Path(__file__).resolve().parents[2]
BBM92 = ROOT / "runs" / "report_examples" / "bbm92" / "record.json.gz"
DECOY = ROOT / "runs" / "report_examples" / "decoy_bb84" / "record.json.gz"


def bbm92() -> KeyRateReport:
    with gzip.open(BBM92, "rt", encoding="utf-8") as handle:
        return build_report(json.load(handle))


def decoy() -> KeyRateReport:
    """Return the decoy example: its chain is not attested, so A-LINK stays."""
    with gzip.open(DECOY, "rt", encoding="utf-8") as handle:
        return build_report(json.load(handle))


def bbm92_first_order() -> KeyRateReport:
    """Return the bbm92 example read as a first-order run (``as_first_order``)."""
    with gzip.open(BBM92, "rt", encoding="utf-8") as handle:
        return build_report(as_first_order(json.load(handle)))


def md(report: KeyRateReport) -> str:
    return render_markdown(report, contract_link=default_contract_link())


def html(report: KeyRateReport) -> str:
    return render_html(report, contract_link=default_contract_link())


def between(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


def assumptions_part(text: str) -> str:
    """Return the assumptions section: it ends at the appendix.

    The measurement snaps stand before it, so the long
    assumptions section sits last before the appendix.
    """
    end = 'id="appendix"'
    return between(text, 'id="assumptions"', end)


# --------------------------------------------------------------------------
# Layer 1: the summary
# --------------------------------------------------------------------------


def test_the_page_opens_with_contents_then_the_summary() -> None:
    text = md(bbm92())
    headings = re.findall(r"^(#{1,3}) (?:<a id=\"([^\"]+)\"></a>)?", text, re.M)
    anchors = [anchor for _, anchor in headings[:10]]
    # The setup in brief follows the result, beside the number.
    # The considerations of the number follow the box, still on the first
    # screen.
    assert anchors == ["", "contents", "summary", "considerations", "result",
                       "setup-brief", "guarantee", "roles", "vouch", "not-counted"]
    contents = between(text, 'id="contents"', 'id="summary"')
    for anchor in ("#summary", "#setup", "#inputs", "#assumptions",
                   "#appendix", "#glossary"):
        assert f"]({anchor})" in contents
    # The snap section is listed where the record has one (record 0.28.0),
    # in the appendix.
    snapped = md(build_report(snapped_record(), table=synthetic_table()))
    appendix_line = next(line for line in between(
        snapped, 'id="contents"', 'id="summary"').splitlines()
        if line.startswith("- [Appendix]"))
    assert "](#measurement-snaps)" in appendix_line


def test_the_result_weaves_the_values_into_one_paragraph() -> None:
    report = build_report(completed_record(k_auth=7, net_key_length=12_338),
                          table=synthetic_table())
    sentence = report["sections"]["summary"]["result"]
    assert sentence.startswith(
        "From n = 1,000,000,000 rounds the protocol, unless it aborts, outputs a "
        "key of "
        "\u2113 = 12,345 bits"
    )
    # What the authentication consumes and what you gain are in the costs list.
    assert "k_auth" not in sentence
    lines = report["sections"]["summary"]["costs"]
    assert lines[-2:] == [
        "Authentication consumes k_auth = 7 bits of pre-shared key per run "
        "(declared); an aborted run may consume as many.",
        "You gain \u2113 \u2212 k_auth = 12,338 bits.",
    ]


def test_a_refusal_says_why_and_that_nothing_is_certified() -> None:
    report = build_report(refused_record(eps_pa=0.5, eps_ev=0.5),
                          table=synthetic_table())
    summary = report["sections"]["summary"]
    assert summary["result"].startswith("The run was refused at its solve stage")
    assert "nothing is certified" in summary["result"]
    assert summary["guarantee"] is None
    assert "no security guarantee applies" in md(report)


def test_the_guarantee_quotes_the_claims_own_readings() -> None:
    report = bbm92()
    index = report["index"]["claims"]
    guarantee = report["sections"]["summary"]["guarantee"]
    assert guarantee is not None
    assert guarantee["claim"] == "meat-core/cor:composed-security"
    text = md(report)
    part = between(text, 'id="guarantee"', 'id="vouch"')
    for claim_id in ("meat-core/cor:composed-security",
                     "meat-core/rem:repeated-executions",
                     "meat-core/rem:completeness-scope"):
        reading = index[claim_id]["user_statement"]
        assert reading
        # The reading's first words appear, escaped as the renderer escapes
        # them (an underscore in ε_PA, an asterisk in ε*).
        first = reading.split(".")[0][:40]
        assert escape_markdown(first, line_start=False) in part
        assert f"nameddest=claim-{claim_id})" in part
    symbols = [term["symbol"] for term in guarantee["terms"]]
    assert symbols == ["ε", "ε_PA", "ε_EV", "ε_auth"]
    # The quantity before its symbol, decimal first; 1/1000000 is exactly
    # 1e-06, so nothing is rounded.
    # Completeness leads with this run's figure, then the remark's reading.
    assert ("Completeness. On this run an honest run fails the acceptance test "
            "with probability at most 1e-06 (ε\\*; [its exact value]"
            "(#setup-acceptance)). The completeness figure") in part


def test_what_you_vouch_for_groups_premises_by_object() -> None:
    report = bbm92()
    summary = report["sections"]["summary"]
    groups = {group["about"]: [short_id for line in group["entries"]
                               for short_id in (line["short_id"], *line["refinements"])]
              for group in summary["vouch"]}
    # Two groups by the premises' categories: the run built both receiver
    # artefacts itself, exact and rigorous, so A-RECV is discharged
    # (reductions/req:recv-row-provenance), and both stations' links are
    # attested, so A-LINK is too; no premise about an artefact remains.
    assert list(groups) == ["Your devices and setup", "How the run is carried out"]
    assert not any("A-RECV" in ids for ids in groups.values())
    # Where a chain is not attested, A-LINK forms the third group.
    assert [group["about"] for group in decoy()["sections"]["summary"]["vouch"]][
        -1] == "Artefacts and the engine"
    assert "A-PASSIVE" in groups["Your devices and setup"]
    # One laboratory premise, emitted at both parties (spec/pm-eb-roles, R1).
    assert "A-LAB" in groups["Your devices and setup"]
    assert "A-AUTH" in groups["Your devices and setup"]
    assert "A-CONFORM" in groups["How the run is carried out"]
    lines = {line["short_id"]: line["about"]
             for group in summary["vouch"] for line in group["entries"]}
    # A-PASSIVE refines A-TRUST and is named on its line.
    assert lines["A-TRUST"] == "Alice's and Bob's stations"
    # A-LMO and A-EIG are not engine numerics: every receiver
    # weight of the regenerated example is enclosed
    # (receiver/req:rigorous-weight), so the receiver records A-EIG as invoked
    # nowhere; and A-RECV is discharged on the run's own exact, rigorous
    # receiver artefacts, so no engine-internal premise remains.
    assert summary["internal"] == []
    # decoy's unattested chain keeps A-LINK, which is its engine group.
    other = decoy()["sections"]["summary"]
    assert other["internal"] == ["A-LINK"]
    assert [line["short_id"] for line in other["vouch"][-1]["entries"]] == [
        "A-LINK"
    ]


def test_not_counted_and_the_levers_name_only_what_the_record_names() -> None:
    report = bbm92()
    summary = report["sections"]["summary"]
    texts = [item["text"] for item in summary["not_counted"]]
    assert any("[[A-EXACT]]" in text for text in texts)
    assert any(text.endswith("([[meat-core/rem:declared-measurement]])")
               for text in texts)
    levers = [item["text"] for item in summary["levers"]]
    assert any(text.startswith("Rényi order: ") for text in levers)
    assert not any(text.startswith("Error correction") for text in levers), (
        "this example declares λ_EC = 0; no lever is named for it"
    )


def test_the_lambda_ec_lever_names_its_estimate_when_one_sits_beside() -> None:
    report = build_report(completed_record(lambda_ec=275), table=synthetic_table())
    (lever,) = [item for item in report["sections"]["summary"]["levers"]
                if item["text"].startswith("Error correction")]
    assert "λ_EC = 275 bits" in lever["text"]
    text = render_markdown(report, contract_link=default_contract_link(),
                           lambda_ec={"f_ec": 1.1, "lambda_ec": 275})
    part = between(text, 'id="levers"', 'id="setup"')
    assert "It was estimated with f_EC = 1.1 ([how](#lambda-ec-origin))." in part


# --------------------------------------------------------------------------
# Layer 2: inputs and assumptions
# --------------------------------------------------------------------------


def test_inputs_are_split_into_three_tables_with_readable_names() -> None:
    report = bbm92()
    groups = {row["name"]: row["group"]
              for row in report["sections"]["protocol"]["inputs"]}
    assert groups["device.bob_efficiency"] == "device"
    assert groups["model.visibility"] == "device"
    assert groups["parameters.eps_pa"] == "budget"
    assert groups["rounds"] == "budget"
    assert groups["solver.max_iterations"] == "engine"
    assert groups["endpoint_rule"] == "engine"
    text = md(report)
    order = [text.index(f'id="inputs-{key}"') for key in ("device", "budget", "engine")]
    assert order == sorted(order)
    header = "| Input | Value | Unit | Meaning | Premises |"
    assert text.count(header) == 3
    row = next(line for line in text.splitlines() if "`device.bob_efficiency`" in line)
    assert row.startswith('| <a id="input-device.bob_efficiency"></a>Bob\'s efficiency')
    # The example runs at the default efficiency, so no default is repeated.
    assert "| 1 (each of A, D, H, V) |" in row


def test_a_searched_alpha_says_the_declared_one_was_not_used() -> None:
    (alpha,) = [row for row in bbm92()["sections"]["protocol"]["inputs"]
                if row["name"] == "parameters.alpha"]
    report = bbm92()
    if report["sections"]["result"]["alpha"]["chosen_by"] == "outer-search":
        assert alpha["not_used"] == "not used: alpha was searched"
    else:
        assert alpha["not_used"] is None


def test_premises_are_grouped_with_an_intro_and_the_unverified_sentence_once() -> None:
    text = md(bbm92())
    part = assumptions_part(text)
    devices = part.index('id="premises-devices"')
    assert devices < part.index('id="category-receiver"')
    # No numerical-trust premise on a run whose receiver weights are all
    # enclosed, and no supplied-artefact one where the run built its receiver
    # artefacts (A-RECV discharged) and attested its links (A-LINK): bbm92
    # has no engine group.
    assert 'id="category-numerical-trust"' not in part
    assert 'id="premises-engine"' not in part
    assert part.count("The engine does not verify these premises") == 1
    # The engine group, where a premise about an artefact remains (decoy's
    # A-LINK): after the devices, with its own intro.
    other = assumptions_part(md(decoy()))
    engine = other.index('id="premises-engine"')
    assert other.index('id="premises-devices"') < engine
    assert engine < other.index('id="category-supplied-artefact"')
    assert other.count("The engine does not verify these premises") == 2
    assert "Evidence for them comes from" in other
    # The per-premise "never verified" sentence lives in the details only.
    assert "Bindings" not in part
    # Each premise opens with its table, what it is about first; its text
    # and bindings follow.
    entry = part[part.index('id="A-PASSIVE"'):]
    table = entry.split("\n\n")[1]
    assert table.startswith("| Field | Value |\n| --- | --- |\n"
                            "| About | Alice's and Bob's stations |\n"
                            "| At stake | secrecy")


#: BBM92's roles, written by hand: an untrusted source, Alice's station first
#: (with the test coin) and Bob's second.
EB_ROLES = Roles(
    source_mode="untrusted", source_trusted=False, alice_party="A", alice_dim=1,
    letters=("x0",), transmitted_dim=1, key_holder="A",
    stations=(
        StationRoles(0, "alice_station", "A", ("off",), True, "A"),
        StationRoles(1, "bob_station", "B", ("off",), False, None),
    ),
    choosers=frozenset({"A"}), message_senders=("A", "B"),
)
#: BB84's roles: Alice sends, Bob is the one receiver (no station index).
PM_ROLES = Roles(
    source_mode="trusted", source_trusted=True, alice_party="A", alice_dim=2,
    letters=("(Z,0)", "(Z,1)", "(X,0)", "(X,1)"), transmitted_dim=2,
    key_holder="A", stations=(StationRoles(None, None, "B", (), True, None),),
    choosers=frozenset({"A", "B"}), message_senders=("A", "B"),
)


def _entry(short_id: str, category: str | None,
           rows: list[tuple[str, int | None, str | None]],
           machine_key: str = "") -> AssumptionEntry:
    report = build_report(completed_record(), table=synthetic_table())
    (found,) = [entry for group in report["sections"]["assumptions"]["groups"]
                for family in group["families"]
                for entry in (family["head"], *family["members"])
                if entry["short_id"] == "A-TRUST"]
    entry = dict(found)
    entry["short_id"], entry["category"] = short_id, category
    entry["machine_key"] = machine_key
    entry["emitted_by"] = [
        {"module": module, "station": station, "party": party,
         "machine_key": machine_key, "inherited_from": None}
        for module, station, party in rows
    ]
    return entry  # type: ignore[return-value]


@pytest.mark.parametrize(
    ("roles", "category", "rows", "expected"),
    [
        (EB_ROLES, "receiver", [("receiver", 0, None), ("receiver", 1, None)],
         "Alice's and Bob's stations"),
        (EB_ROLES, "receiver", [("receiver", 1, None)], "Bob's station"),
        (EB_ROLES, "receiver", [("receiver", None, None)], "Your receivers"),
        (PM_ROLES, "source", [("transmitter", None, None)], "Your source"),
        (EB_ROLES, "numerical-trust", [("meat-core", None, None)],
         "The engine's numerics"),
        (EB_ROLES, "receiver", [("receiver", 2, None)], "Station 2"),
        # A station-scoped row is named by its station in every category
        # (spec/pm-eb-roles: A-PROBE or A-TSM at Alice's station on BBM92).
        (EB_ROLES, "local-randomness", [("reductions", 0, None)], "Alice's station"),
        (EB_ROLES, "protocol-structure", [("reductions", 0, None)],
         "Alice's station"),
        (PM_ROLES, "local-randomness", [("reductions", None, None)],
         "Bob's station"),
        # Emitted at the stations and for the run: the category's object,
        # except where a receiver or supplied-artefact premise named them.
        (EB_ROLES, "channel-and-adversary",
         [("reductions", 0, None), ("reductions", 1, None), ("meat-core", None, None)],
         "The classical channel and the attacker"),
        (EB_ROLES, "supplied-artefact",
         [("protocol-compiler", None, None), ("reductions", 0, None),
          ("reductions", 1, None)],
         "Alice's and Bob's stations"),
        # A per-party row names each party's laboratory and its stations, and
        # never "Your receivers".
        (EB_ROLES, "laboratory", [("meat-core", None, "A"), ("meat-core", None, "B")],
         "Alice's laboratory (station alice_station) and Bob's laboratory "
         "(station bob_station)"),
        (PM_ROLES, "laboratory", [("meat-core", None, "A"), ("meat-core", None, "B")],
         "Alice's laboratory and Bob's laboratory (the receiver)"),
        (PM_ROLES, "receiver", [("protocol-compiler", None, None)], "Bob's station"),
    ],
)
def test_about_names_the_object(
    roles: Roles, category: str | None,
    rows: list[tuple[str, int | None, str | None]], expected: str,
) -> None:
    entry = _entry("A-X", category, rows)
    assert about(entry, roles) == expected


def test_an_older_records_laboratory_premise_names_its_party() -> None:
    """Record 0.29.0's A-LAB-BOB carried no party; its machine key names it."""
    entry = _entry("A-LAB-BOB", "receiver", [("meat-core", None, None)],
                   machine_key="bob_laboratory_sealed")
    assert about(entry, EB_ROLES) == "Bob's laboratory (station bob_station)"


#: BBM92's roles with Bob's test coin (the document-bbm92_choice_at_bob shape).
EB_COIN_AT_BOB = replace(
    EB_ROLES,
    public_choices=(PublicChoice("B", True, "bob_station", ("gen", "test"), False),),
)


def test_roles_box_says_who_does_what_on_an_eb_run() -> None:
    """Hand-written roles, hand-written expectations."""
    assert roles_box(EB_COIN_AT_BOB) == [
        "Neither party sends: the untrusted source delivers one system to each "
        "station. The source, its pump, timing and trigger electronics "
        "included, counts as outside every laboratory wherever it stands "
        "([[A-LAB]]).",
        "Measuring stations: Alice's station (alice_station), Bob's station "
        "(bob_station).",
        "Key: Alice holds it, computed from the detection results of Alice's "
        "station (alice_station).",
        "Public choices: gen or test, drawn at Bob's station.",
    ]
    # What the run lacks is a list of its own, its information kept.
    assert roles_absent(EB_COIN_AT_BOB) == [
        "A trusted source: the source is untrusted.",
        "A private setting: no station has one.",
        "A second letter: the declaration has one letter (x0), the per-round "
        "value a sender would prepare on Alice's side.",
    ]


def test_roles_box_on_a_pm_run() -> None:
    pm = replace(PM_ROLES, public_choices=(
        PublicChoice("A", False, None, ("Z", "X"), False),
        PublicChoice("B", True, None, ("Z", "X"), False),
    ))
    lines = roles_box(pm)
    assert lines[0] == "Alice sends: the trusted source's signals enter the proof."
    assert lines[1] == "Measuring station: Bob's station (the receiver)."
    assert lines[2] == "Key: Alice holds it, computed from her letters."
    assert lines[3] == ("Public choices: Z or X, drawn by Alice with the letter; "
                        "Z or X, drawn at Bob's station.")


def test_a_premise_names_its_clauses_not_on_this_run() -> None:
    """A premise names the clauses that are not on this run."""
    probe = _entry("A-TSM", "protocol-structure", [("reductions", 1, None)])
    assert role_notes(probe, EB_ROLES) == [
        "Not on this run: its probe setting, since no station it is about has a "
        "private setting."
    ]
    register = _entry("A-KEYREG", "post-processing", [("meat-core", None, None)])
    assert role_notes(register, EB_ROLES) == [
        "On this run Alice holds the key; her own record here is the detection "
        "results of Alice's station (alice_station)."
    ]
    assert role_notes(register, PM_ROLES) == [
        "On this run Alice holds the key; her own record here is her letters."
    ]


def test_the_laboratory_line_keeps_trojan_horse_light_on_the_run() -> None:
    """Only the trusted-source clauses leave an EB run."""
    lab = _entry("A-LAB", "laboratory",
                 [("meat-core", None, "A"), ("meat-core", None, "B")])
    off, kept = role_notes(lab, EB_ROLES)
    assert off.startswith("Not on this run: the clauses about a trusted source "
                          "in the party's laboratory")
    assert "Trojan-horse" not in off
    assert kept.startswith(
        "Light sent into a laboratory to read out a letter, a setting")
    # A record that does not say whether the source is trusted drops nothing.
    unknown = replace(EB_ROLES, source_trusted=None)
    assert role_notes(lab, unknown) == []
    assert role_notes(lab, PM_ROLES) == []


def test_the_checklist_places_premises_the_roles_tie_to_a_place() -> None:
    """A-COIN, the source premises and A-KEYREG have places."""
    coin = _entry("A-COIN", "local-randomness", [("protocol-compiler", None, None)])
    assert places(coin, EB_COIN_AT_BOB) == ["Bob's station (bob_station)"]
    pm = replace(PM_ROLES, public_choices=(
        PublicChoice("A", False, None, ("Z", "X"), False),
        PublicChoice("B", True, None, ("Z", "X"), False),
    ))
    assert places(coin, pm) == ["Alice's laboratory", "Bob's station (the receiver)"]
    source = _entry("A-ENS", "source", [("transmitter", None, None)])
    assert places(source, PM_ROLES) == ["Alice's laboratory"]
    assert places(source, EB_ROLES) == []
    register = _entry("A-KEYREG", "post-processing", [("meat-core", None, None)])
    assert places(register, replace(EB_ROLES, key_holder="B")) == ["Bob's laboratory"]


def test_a_party_partition_binding_reads_in_words() -> None:
    assert partition_words(
        {"alice_system": "A", "measured_factors": ["A", "B"]}, EB_ROLES
    ) == ("system A: party A (Alice); measured stations: alice_station (Alice), "
          "bob_station (Bob)")
    assert partition_words(
        {"alice_system": "A", "measured_factors": ["B"]}, PM_ROLES
    ) == "system A: party A (Alice); measured station: the receiver (Bob)"


def test_a_coin_names_where_its_choices_are_drawn() -> None:
    """A coin names where its choices are drawn."""
    coin = _entry("A-COIN", "local-randomness", [("protocol-compiler", None, None)])
    assert about(coin, EB_COIN_AT_BOB) == (
        "Your random number generators (the choice drawn at Bob's station)")


def test_the_acceptance_outcomes_are_listed_once_in_the_table_and_referenced() -> None:
    """No list of the outcomes where the table names every one.

    The bbm92 record's acceptance box has one row per outcome, so the
    category table lists them all and the separate list is dropped; a value
    that repeats the alphabet links to the table.
    """
    report = bbm92()
    text = md(report)
    with gzip.open(BBM92, "rt", encoding="utf-8") as handle:
        record = json.load(handle)
    outcomes = [str(item) for item in
                record["payload"]["stages"]["acceptance_construction"]["outcomes"]]
    acceptance = between(text, 'id="setup-acceptance"', 'id="setup-expected"')
    assert f"The {len(outcomes)} acceptance outcomes: " not in text
    rows = [line.split(" | ", 1)[0][2:].replace("\\|", "|")
            for line in acceptance.splitlines() if line.startswith("| ")]
    for outcome in outcomes:
        assert outcome in rows, outcome
    assert f"[the {len(outcomes)} acceptance outcomes](#setup-acceptance)" in text
    # Without a table that lists every outcome, the list is printed once.
    setup = report["sections"]["setup"]["acceptance"]
    assert setup is not None
    setup["categories"] = []
    setup["honest"] = setup["honest"][:3]
    listing = ", ".join(outcomes).replace("|", "\\|")
    assert md(report).count(f"The {len(outcomes)} acceptance outcomes: {listing}.") == 1


# --------------------------------------------------------------------------
# Matrices and weights
# --------------------------------------------------------------------------


def test_floating_point_residue_prints_as_zero_with_one_note() -> None:
    entries: list[list[Any]] = [[0.2, 0.0], [0.0, -6.16e-33], [2.2e-16, 0.0]]
    floor = residue_floor(entries)
    assert floor == pytest.approx(0.2e-12)
    assert format_entry([0.0, -6.16e-33], floor) == "0"
    assert format_entry([2.2e-16, 0.0], floor) == "0"
    assert format_entry([0.2, 1.7e-17], floor) == "0.2"
    assert format_entry([0.2, 1.7e-17]) == "0.2 + 1.7e-17i"
    # Exact entries are never treated as residue.
    assert format_entry(["1/549755813888", "0"], 1.0) == (
        "≈ 1.81899e-12 (1/549755813888)")
    # Decimal first on an imaginary part too, its sign outside the bracket.
    assert format_entry(["1/2", "-1/549755813888"]) == (
        "1/2 \u2212 (≈ 1.81899e-12 (1/549755813888))i")
    assert format_entry([0.0, -0.5]) == "-0.5i"
    text = md(bbm92())
    one_photon = text[text.index("*Outcome nc*"):]
    one_photon = one_photon[:one_photon.index("####")]
    assert "e-33" not in one_photon
    assert one_photon.count(RESIDUE_NOTE) == 1


# --------------------------------------------------------------------------
# Layer 3: the appendix
# --------------------------------------------------------------------------


def test_diagnostics_are_read_and_solver_attempts_listed() -> None:
    report = bbm92()
    numerics = report["sections"]["numerics"]
    rows = {row["name"]: row for row in numerics["explained"]}
    assert rows["h_lb"]["label"] == "First-order lower bound h_lb"
    status = rows["solver_status"]["explanation"]
    assert status is not None and "does not enter h_lb" in status
    # No solver trust is named: the bound's feasible side is verified
    # (req:verified-feasible-side).
    assert "A-LMO" not in status
    assert "[[meat-core/frank-wolfe/thm:firstorder]]" in status
    record_attempts = [
        attempt["termination"] for attempt in numerics["solver_attempts"]
    ]
    assert record_attempts, "the bbm92 example's record lists the search's attempts"
    page = html(report)
    assert f"How each of the {len(record_attempts)} solver attempts stopped" in page


def test_appendix_subsections_are_collapsed_in_html_only() -> None:
    page = html(bbm92())
    appendix = page[page.index('id="appendix"'):]
    for key in ("how-computed", "security-claims", "checks", "route", "provenance"):
        heading = appendix.index(f'id="{key}"')
        assert appendix[heading:].split("\n", 2)[1].startswith("<details><summary>")
    assert "<details open><summary>Glossary</summary>" in appendix
    text = md(bbm92())
    assert "<details" not in text


def test_the_status_legend_and_the_draft_sentence() -> None:
    report = bbm92()
    text = md(report)
    provenance = text[text.index('id="provenance"'):text.index('id="glossary"')]
    for name, _ in STATUS_LEGEND:
        assert f"- {name}: " in provenance
    drafts = report["sections"]["summary"]["drafts"]
    if drafts:
        assert "whose effective status is still draft" in provenance


# --------------------------------------------------------------------------
# Staleness, snaps for a reader, the sweep
# --------------------------------------------------------------------------


def test_a_frozen_text_that_differs_from_the_current_contract_is_shown() -> None:
    table = synthetic_table()
    table["assumptions"]["A-AUTH"] = {
        "owner": "meat-core/ass:auth",
        "user_statement": "The current reading of A-AUTH, changed since the run.",
    }
    report = build_report(completed_record(), table=table)
    entries = {entry["short_id"]: entry
               for group in report["sections"]["assumptions"]["groups"]
               for family in group["families"]
               for entry in (family["head"], *family["members"])}
    assert entries["A-AUTH"]["current_text"] == (
        "The current reading of A-AUTH, changed since the run.")
    assert entries["A-KEYREG"]["current_text"] is None
    assert report["sections"]["summary"]["stale"] == ["A-AUTH"]
    text = md(report)
    assert "1 premise text of this run differs from the current contracts" in text
    entry = text[text.index('id="A-AUTH"'):]
    entry = entry[:entry.index("For this run")]
    current = entry.index("The current reading of A-AUTH, changed since the run.")
    note = entry.index("The run record carries an earlier wording of this premise")
    earlier = entry.index("Every classical message of your protocol")
    assert current < note < earlier  # the current text first
    assert build_report(completed_record(), table=synthetic_table())[
        "sections"]["summary"]["stale"] == []


def test_the_snap_section_reads_in_plain_sentences_and_a_readable_table() -> None:
    report = build_report(snapped_record(), table=synthetic_table())
    snaps = report["sections"]["protocol"]["measurement_snaps"]
    assert snaps is not None
    assert snaps["plain"][0].startswith(
        "Before solving, the engine rounds each station's measurement operators")
    assert 2 <= len(snaps["plain"]) <= 6
    rows = {row["photons"]: row for row in snaps["rows"]}
    assert set(rows) == {"0 photons (vacuum)", "1 photon", "2 photons"}
    assert rows["0 photons (vacuum)"]["status"].startswith("kept exactly")
    assert rows["1 photon"]["status"].startswith("rounded, and evaluated off")
    assert rows["2 photons"]["status"] == "rounded (last resort)"
    for row in snaps["rows"]:
        assert row["station"] is None
        assert "weight" not in row
        if row["rests_on_assumption"]:
            assert row["group"] is not None and row["fix"]
    page = md(report)
    assert "no: evaluated off its snap" in page
    assert "yes (last resort)" in page


def test_the_plain_snap_sentences_follow_the_groups_generically() -> None:
    from certiqs_key.runs.report.snaps import plain_sentences

    def block(status: str, group: str | None, *, off: bool = False) -> dict[str, Any]:
        rests = group is not None
        return {"block": "m=1", "setting": "off", "station": None,
                "status": status, "group": group,
                "group_fix": None if group is None else f"fix for {group}",
                "rests_on_assumption": rests, "evaluated_off_snap": off}

    blocks = [block("moved", "last_resort"), block("moved", "a_new_group"),
              block("moved", None, off=True), block("kept", None)]
    sentences = plain_sentences(blocks, 3.0e-12)  # type: ignore[arg-type]
    assert "is 3.0e-12. How far an entry moves" in sentences[0]
    assert ("does not bound how far the key length can move "
            "([[meat-core/rem:declared-measurement]])") in sentences[0]
    assert sentences[1].startswith("1 of the 4 blocks of your stations are kept")
    assert sentences[2].startswith("On 1 of the 3 moved blocks of your stations "
                                   "the key length is computed from your receiver")
    assert sentences[3].startswith("On 2 of the 3 moved blocks of your stations "
                                   "the analysis does not account for the rounding")
    assert "1 block could be rounded only by the last resort" in sentences[4]
    assert "1 block rests on A-SNAP (a new group)" in sentences[4]
    assert sentences[5] == ("What to change: Fix for last_resort. "
                            "Or: Fix for a_new_group.")
    calm = plain_sentences(  # type: ignore[arg-type]
        [block("kept", None), block("moved", None, off=True)], None
    )
    assert calm[-1] == (
        "The rounding adds no premise: the key length does not rest on A-SNAP, "
        "so nothing in this section asks anything of you."
    )


def test_vouch_groups_by_category_and_the_channel_names_the_parties() -> None:
    report = bbm92()
    summary = report["sections"]["summary"]
    abouts = [group["about"] for group in summary["vouch"]]
    assert len(abouts) == len(set(abouts))
    assert "Your devices and setup" in abouts
    assert "Alice's and Bob's stations" not in abouts
    channel = next(line for line in summary["setup_brief"]
                   if line.startswith("Channel:"))
    assert channel == ("Channel: Alice's arm transmittance 1 (no loss), "
                       "Bob's 1 (no loss).")
    protocol = summary["setup_brief"][0]
    # No model of what the source delivers, and what else may reach a station
    # is A-LAB's and A-MODES'.
    assert ("untrusted source (the proof uses no model of the source: whatever "
            "it delivers into the stations' declared input modes is treated as "
            "prepared by the attacker") in protocol
    assert "[[A-LAB]] and [[A-MODES]]" in protocol
    assert "second case" not in md(report)


def test_the_sweep_page_has_the_same_layers_and_links_shown_point_excerpts(
    tmp_path: Path,
) -> None:
    from certiqs_key.runs.report.__main__ import main

    folder = ROOT / "runs" / "report_examples" / "sweep-bb84"
    out = tmp_path / "out"
    records = sorted(str(path) for path in folder.glob("run-*.json"))
    assert main([*records, "--format", "md", "--out", str(out)]) == 0
    text = (out / "sweep.md").read_text(encoding="utf-8")
    anchors = re.findall(r"^## <a id=\"([^\"]+)\"></a>", text, re.M)
    assert anchors == ["contents", "summary", "setup", "inputs", "assumptions",
                       "points", "appendix"]
    summary = between(text, 'id="summary"', 'id="setup"')
    assert "](points/0000.md)" in summary and "| ε |" in summary
    assert "This is the setup of point 0 ([its report](points/0000.md))." in text
    links = re.findall(r"\]\((points/0000\.record\.md#[^)]+)\)", text)
    assert links
    excerpts = (out / "points" / "0000.record.md").read_text(encoding="utf-8")
    for link in links:
        assert f'<a id="{link.split("#", 1)[1]}"></a>' in excerpts
    assert "| Measurement snaps |" in text or "Measurement snaps" in text


def test_no_page_calls_the_first_order_bound_certified() -> None:
    """h_lb is a first-order bound, weaker than a certificate.

    With the certified tier a page
    names a certified lower bound where the run is reported at that tier, and
    it is h_cert: a first-order page names none, and no line calls h_lb one.
    """
    from runs.report_examples.generate import EXAMPLES, read_record, record_paths

    first_order = md(bbm92_first_order()).lower()
    assert "certified lower bound" not in first_order
    pages = [first_order] + [
        md(build_report(read_record(path))).lower()
        for example in EXAMPLES for path in record_paths(example)
    ]
    for text in pages:
        assert "certified first-order" not in text
        assert "never validity" not in text
        assert "lies above the true minimum" not in text
        for line in text.splitlines():
            if "certified lower bound" in line:
                assert "h_cert" in line, line


def test_no_page_says_a_snap_is_proven_harmless() -> None:
    """A certified weight proves domination, not harmlessness."""
    from runs.report_examples.generate import EXAMPLES, read_record, record_paths

    for example in EXAMPLES:
        for path in record_paths(example):
            text = md(build_report(read_record(path))).lower()
            assert "proven harmless" not in text
            assert "entries moved by at most" not in text


def test_the_reduction_s_resting_emission_is_in_the_plain_layer() -> None:
    """Clause (ii) of A-SNAP, the reduction's emission.

    On a hand-built record, a moved class of the
    reduction's emission that the run did not evaluate off its snap; the
    example records are snapshots of an earlier record shape.
    """
    report = build_report(
        snapped_record(emission_rests=True), table=synthetic_table()
    )
    snaps = report["sections"]["protocol"]["measurement_snaps"]
    assert snaps is not None
    (row,) = snaps["emission"]
    assert row["data_sector"] == 0 and row["rests_on_assumption"] is True
    assert any("The reduction's own rounding of what it emits rests on "
               "[[A-SNAP]] at data sector(s) 0" in sentence
               for sentence in snaps["plain"])


def test_the_guarantee_names_the_floating_point_gap_on_a_first_order_run() -> None:
    """No premise covers the floating-point h_lb.

    The reading of cor:composed-security names it; with a closure table whose
    reading does not, the page adds the sentence itself.
    """
    text = md(bbm92_first_order())
    part = between(text, 'id="guarantee"', 'id="vouch"')
    assert r"computed h_lb ≤ h_low, which no premise covers" in part
    assert "On this run it also needs" not in part
    table = synthetic_table()
    report = build_report(completed_record(), table=table)
    synthetic = between(md(report), 'id="guarantee"', 'id="vouch"')
    assert ("On this run it also needs the computed lower bound on the "
            r"attacker's worst-case uncertainty per round (h_lb) to lie below "
            r"that worst case (h_low)") in synthetic
    vouch = between(text, 'id="vouch"', 'id="not-counted"')
    assert ("None of them covers the floating-point arithmetic of the "
            "first-order bound") in vouch


def test_the_shared_combination_wording_follows_who_sends() -> None:
    """A signal only where Alice sends."""
    from certiqs_key.runs.report.setup import combined_words

    assert combined_words(EB_ROLES) == "readouts"
    assert combined_words(PM_ROLES) == "signal and readouts"
    assert combined_words(replace(PM_ROLES, alice_dim=1)) == "letter and readouts"
    assert combined_words(replace(PM_ROLES, source_trusted=False)) == (
        "letter and readouts")


def test_the_public_choice_step_names_every_choice() -> None:
    """bb84's Bob draws Z or X at his station too."""
    path = ROOT / "runs" / "report_examples" / "bb84" / "record.json"
    report = build_report(json.loads(path.read_text(encoding="utf-8")))
    (step,) = [step for step in report["sections"]["setup"]["protocol"]
               if step["title"].startswith("Public choice")]
    assert step["title"] == "Public choices"
    assert step["text"] == (
        "Alice draws a public choice: Z with probability 0.5, X with probability "
        "0.5. At Bob's station, a public choice is drawn: Z with probability 0.5, "
        "X with probability 0.5."
    )


# --------------------------------------------------------------------------
# Idealised examples and the first-order gap
# --------------------------------------------------------------------------


def _row(name: str, section: str, quantity: str | None, value: Any) -> Any:
    return {"name": name, "section": section, "quantity": quantity, "value": value,
            "prepared": None}


def test_idealised_device_values_are_named_at_a_glance() -> None:
    """Item 1: by kind, every port at its ideal extreme; nothing otherwise."""
    from certiqs_key.runs.report.explain import idealised

    rows = [
        _row("device.efficiency", "device", "efficiency", {"H": "1", "V": "1"}),
        _row("device.dark_count", "device", "probability", {"H": "0", "V": "0"}),
        _row("model.visibility", "model", "probability", "1"),
        _row("device.test_fraction", "device", "probability", "1/8"),
    ]
    item = idealised(rows, {"A-EXACT"}, EB_ROLES)
    assert item is not None
    assert item["text"] == (
        "Idealised example, not a characterised device. The run's device values "
        "are at "
        "their ideal extreme (detection efficiency 1, dark-click probability 0): "
        "the key length covers only a device with exactly these values "
        "([[A-EXACT]]). The run's honest model is at its ideal extreme (visibility "
        "1): "
        "the acceptance test is built for statistics a real device may not show. "
        "For such a device the completeness figure \u03b5* no longer bounds how "
        "often it aborts, possibly on almost every run; security is unaffected."
    )
    # After the one-line headline, the line says what is idealised.
    after = idealised(rows, {"A-EXACT"}, EB_ROLES, after_headline=True)
    assert after is not None and after["text"].startswith(
        "What is idealised: the run's device values are at their ideal extreme")
    assert "Idealised example" not in after["text"]
    # A-EXACT is linked only where it is a premise of the run.
    unlinked = idealised(rows, set(), EB_ROLES)
    assert unlinked is not None and "[[A-EXACT]]" not in unlinked["text"]
    real = [
        _row("device.efficiency", "device", "efficiency", {"H": "1", "V": "9/10"}),
        _row("device.dark_count", "device", "probability", {"H": "1/1000000"}),
        _row("model.visibility", "model", "probability", "99/100"),
    ]
    assert idealised(real, {"A-EXACT"}, EB_ROLES) is None


def test_security_side_idealisations_are_named_first() -> None:
    """A-IDEAL, a trusted qubit ensemble (A-ENS), a vacuum decoy (A-WCP)."""
    from certiqs_key.runs.report.explain import idealised

    item = idealised([], {"A-IDEAL", "A-ENS"}, PM_ROLES)
    assert item is not None
    assert item["text"] == (
        "Idealised example, not a characterised device. The run's receiver is the "
        "ideal "
        "qubit receiver of the Band-A route ([[A-IDEAL]]): no real optical "
        "receiver meets this premise, so the key length covers no real receiver. "
        "The run's trusted source emits exactly the declared qubit states, one per "
        "round ([[A-ENS]])."
    )
    decoy = idealised(
        [_row("device.mu_vacuum", "device", "mean_photon_number", "0"),
         _row("device.mu_signal", "device", "mean_photon_number", "4/5")],
        {"A-WCP"}, replace(PM_ROLES, transmitted_dim=31),
    )
    assert decoy is not None and decoy["text"].endswith(
        "The run's decoy source emits exactly the declared intensities, among them "
        "mu_vacuum = 0 ([[A-WCP]]).")


def test_only_a_security_bearing_idealisation_is_called_an_idealised_example(
) -> None:
    """The headline needs A-IDEAL, a qubit A-ENS, a vacuum decoy or ideal devices."""
    from certiqs_key.runs.report.explain import (
        IDEALISED_HEADLINE,
        IDEALISED_HONEST_MODEL,
        idealisation_bears_on_security,
        idealised,
    )

    model_only = [_row("model.visibility", "model", "probability", "1")]
    assert not idealisation_bears_on_security(model_only, {"A-EXACT"}, EB_ROLES)
    for after in (False, True):
        item = idealised(model_only, {"A-EXACT"}, EB_ROLES, after_headline=after)
        assert item is not None
        assert item["text"].startswith(
            "Idealised honest model, bearing on completeness only. The run's "
            "honest model is at its ideal extreme (visibility 1)")
        assert IDEALISED_HEADLINE not in item["text"]
    device = [_row("device.efficiency", "device", "efficiency", {"H": "1"}),
              *model_only]
    assert idealisation_bears_on_security(device, {"A-EXACT"}, EB_ROLES)
    assert idealisation_bears_on_security([], {"A-IDEAL"}, PM_ROLES)
    assert idealisation_bears_on_security([], {"A-ENS"}, PM_ROLES)

    # On a run: bbm92 with real device values keeps only its ideal honest
    # model (visibility 1, transmittance 1), so no headline opens the box.
    from runs.report_examples.generate import read_record

    record = read_record(ROOT / "runs" / "report_examples" / "bbm92" / "record.json.gz")
    device_config = record["payload"]["config"]["device"]
    for party in ("alice", "bob"):
        device_config[f"{party}_efficiency"] = dict.fromkeys("HVDA", "9/10")
        device_config[f"{party}_dark_count"] = dict.fromkeys("HVDA", "1/1000000")
        device_config[f"{party}_pbs_leak_transmitted"] = "1/1000"
        device_config[f"{party}_pbs_leak_reflected"] = "1/100"
    summary = build_report(record)["sections"]["summary"]
    glance = summary["at_a_glance"]
    # The setup fragment opens the box where no idealisation bears on security.
    assert glance[0]["lead"] == "BBM92 with two passive stations"
    assert glance[1]["lead"].startswith("Key length")
    assert all(item["lead"] != "Idealised example" for item in glance)
    assert summary["considerations"][-1]["text"].startswith(IDEALISED_HONEST_MODEL)
    # The committed record, with ideal devices, opens with the headline; what
    # is idealised closes the considerations.
    ideal = build_report(read_record(
        ROOT / "runs" / "report_examples" / "bbm92" / "record.json.gz"
    ))["sections"]["summary"]
    assert (ideal["at_a_glance"][0]["lead"] + ideal["at_a_glance"][0]["text"]
            + ".") == IDEALISED_HEADLINE
    assert ideal["considerations"][-1]["text"].startswith(
        "What is idealised: the run's device values")


def test_the_efficiency_normalization_is_no_device_value() -> None:
    """Normalization 1 turns factoring off; it is not "detection efficiency 1"."""
    from certiqs_key.runs.report.explain import (
        IDEALISED_HEADLINE,
        idealisation_bears_on_security,
        idealised,
    )

    rows = [
        _row("device.efficiency", "device", "efficiency", dict.fromkeys("HVDA", "4/5")),
        _row("device.dark_count", "device", "probability",
             dict.fromkeys("HVDA", "1/1000000")),
        _row("device.pbs_leak_transmitted", "device", "probability", "1/1000"),
        _row("device.pbs_leak_reflected", "device", "probability", "1/100"),
        _row("device.efficiency_normalization", "device", "transmittance", "1"),
        _row("device.alice_efficiency_normalization", "device", "transmittance", "1"),
    ]
    assert not idealisation_bears_on_security(rows, {"A-EXACT"}, PM_ROLES)
    assert idealised(rows, {"A-EXACT"}, PM_ROLES) is None

    # On a run: bbm92 with real devices and both normalizations at 1.
    from runs.report_examples.generate import read_record

    record = read_record(ROOT / "runs" / "report_examples" / "bbm92" / "record.json.gz")
    device_config = record["payload"]["config"]["device"]
    for party in ("alice", "bob"):
        device_config[f"{party}_efficiency"] = dict.fromkeys("HVDA", "4/5")
        device_config[f"{party}_dark_count"] = dict.fromkeys("HVDA", "1/1000000")
        device_config[f"{party}_pbs_leak_transmitted"] = "1/1000"
        device_config[f"{party}_pbs_leak_reflected"] = "1/100"
        device_config[f"{party}_efficiency_normalization"] = "1"
    summary = build_report(record)["sections"]["summary"]
    assert all(item["lead"] != "Idealised example" for item in summary["at_a_glance"])
    texts = [item["text"] for item in summary["considerations"]]
    assert IDEALISED_HEADLINE not in texts
    assert not any("detection efficiency 1" in text for text in texts)


def test_outcomes_that_admit_no_count_are_said_to_abort_on_one_round() -> None:
    """A count range of exactly 0: one such round fails the test."""
    from certiqs_key.runs.report.setup import _zero_count_words

    def row(outcome: str, upper: str, count_max: int | None) -> Any:
        return {"outcome": outcome, "probability": 0.0, "lower": "0",
                "upper": upper, "count_min": 0, "count_max": count_max,
                "rounds": None if count_max is None else 100}

    assert _zero_count_words([row("ok", "1/2", 50)]) == ""
    assert _zero_count_words([row("ok", "1/2", 50), row("err", "0", 0)]) == (
        " One outcome, err, admits a count of exactly 0: a single round with it "
        "fails the acceptance test, and your implementation must abort the run "
        "([[A-CONFORM]])."
    )
    # An upper end below 1/n admits no count either; without n, q+ = 0 decides.
    assert _zero_count_words(
        [row("a", "1/1000", 0), row("b", "0", None), row("c", "1/2", 50)]
    ).startswith(" 2 of the 3 outcomes admit a count of exactly 0: a single round "
                 "with any of them fails the acceptance test")
    from runs.report_examples.generate import read_record

    path = ROOT / "runs" / "report_examples" / "bbm92" / "record.json.gz"
    report = build_report(read_record(path))
    acceptance = report["sections"]["setup"]["acceptance"]
    assert acceptance is not None
    assert "of the 79 outcomes admit a count of exactly 0" in acceptance["text"]


def test_premises_are_counted_and_tagged_by_consequence() -> None:
    """Item 3: from each premise's affects."""
    from certiqs_key.runs.report.explain import (
        consequence,
        consequence_rows,
        consequence_words,
    )

    assert consequence(["secrecy"]) == "security"
    assert consequence(["correctness", "completeness"]) == "security"
    assert consequence(["completeness"]) == "completeness"
    assert consequence(None) == "security"
    # The artefact and numerics premises count by their affects too.
    assert consequence_rows(
        {"security": 26, "engine": ["A-RECV", "A-EIG"], "completeness": 3}
    ) == [
        ("Can break security if they fail", "26"),
        ("of them, about artefacts supplied to the engine and its numerics",
         "2: A-RECV, A-EIG"),
        ("Affect only completeness: how often an honest run aborts, or whether "
         "it yields a key", "3"),
        ("All premises of this run", "29"),
    ]
    # Only what the premise's affects puts at stake.
    assert consequence_words("A-LAB", ["secrecy"]) == "security (the key may leak)"
    assert consequence_words("A-X", ["correctness"]) == (
        "security (the two keys may differ)")
    # A-REACH has no words of its own: its affects put secrecy at stake, since
    # a failure lets the key length grow with the mismatch
    # (meat-core/prop:minimal-divergence; statistics/ass:reach).
    assert consequence_words("A-REACH", ["secrecy", "completeness"]) == (
        "security (the key may leak)")
    assert consequence_words("A-HON-ENV", ["completeness"]) == (
        "only how often an honest run aborts, never security")


def test_the_security_statements_review_status_is_said() -> None:
    """Item 6: each claim's status, then the lowest with its dependencies."""
    from certiqs_key.runs.report.explain import statement_status

    claims: list[Any] = [
        {"id": "meat-core/cor:composed-security", "status": "implemented",
         "effective_status": "verified"},
        {"id": "meat-core/thm:keylength", "status": "accepted",
         "effective_status": "accepted"},
    ]
    formed: list[Any] = [
        {"id": "meat-core/frank-wolfe/cor:fo-reference", "status": "accepted",
         "effective_status": "accepted"},
        claims[0],
    ]
    # The main message leads (the lowest status), then one line per claim.
    stated = statement_status(claims, formed)
    assert stated is not None
    assert stated.lead == (
        "Review status: the lowest status of the claims below, with everything "
        "they rest on in the claim graph, is: reviewed adversarially by an AI "
        "model, not yet accepted by a person.")
    # What was reviewed and accepted: the statement, or the statement and code.
    assert stated.items == [
        "[[meat-core/cor:composed-security]], the security statement: statement "
        "and code reviewed adversarially by an AI model and accepted by the "
        "project's human owner.",
        "[[meat-core/thm:keylength]], the security statement: statement reviewed "
        "adversarially by an AI model and accepted by the project's human owner.",
        "[[meat-core/frank-wolfe/cor:fo-reference]], on this run: statement "
        "reviewed adversarially by an AI model and accepted by the project's "
        "human owner.",
    ]
    # Without the closures the tail says the table does not tell; it names
    # no premise as outside, since a route premise may lie beneath a claim.
    assert stated.tail == (
        "The closure table does not state which of this run's premises lie "
        "beneath these claims; each carries its own review status under "
        "Assumptions you vouch for.")
    on_sweep = statement_status(claims, formed, (), ["A-EXACT"], sweep=True)
    assert on_sweep is not None and "through this sweep's own route" in (
        on_sweep.tail)
    # With them it names the premises outside, and only those.
    named = statement_status(claims, formed, (), ["A-EXACT", "A-SPEC"])
    assert named is not None and named.tail == (
        "The premises [[A-EXACT]] and [[A-SPEC]] are not beneath the claims above "
        "in the claim graph: they enter through this run's own route, and each "
        "carries its own review status under Assumptions you vouch for.")
    assert statement_status([]) is None


def test_the_status_legend_is_ordered_lowest_first() -> None:
    """spec/claim-format.md section 6 (check 9) ranks superseded lowest."""
    assert [name for name, _ in STATUS_LEGEND] == [
        "superseded", "draft", "verified", "accepted", "implemented",
        "effective status",
    ]


def test_the_receiver_artefact_is_at_the_one_receiver() -> None:
    """A-RECV, and A-LINK with a receiver segment only."""
    recv = _entry("A-RECV", "supplied-artefact",
                  [("protocol-compiler", None, None), ("reductions", None, None)])
    assert places(recv, PM_ROLES) == ["Bob's station (the receiver)"]
    link = _entry("A-LINK", "supplied-artefact", [("protocol-compiler", None, None)])
    link["bindings"] = [{"name": "reduction_chain", "emitted_by": [], "value": {
        "receiver_segment": [{"link_id": "L1"}], "source_segment": []}}]
    assert places(link, PM_ROLES) == ["Bob's station (the receiver)"]
    link["bindings"][0]["value"]["source_segment"] = [{"link_id": "S1"}]
    assert places(link, PM_ROLES) == []


def test_what_a_round_is_is_said_before_the_protocol() -> None:
    """What a round is, before the steps; only what the premises say."""
    from certiqs_key.runs.report.setup import round_block

    # Only engaged premises, not a complete list, the untrusted source's
    # clock line only on an untrusted run.
    block = round_block({"A-SPEC", "A-IDEAL", "A-LAB", "A-ALPHABET"}, True)
    ids = [premise["short_id"] for premise in block["premises"]]
    # A-LAB stands before A-FIXED where that is engaged, else last.
    assert ids == ["A-SPEC", "A-IDEAL", "A-ALPHABET", "A-LAB"]
    glosses = {premise["short_id"]: premise["gloss"] for premise in block["premises"]}
    assert "untrusted source" not in glosses["A-LAB"]
    # No security condition is dropped: a lost round and a dropped no-click
    # bin stay visible (A-SPEC, and A-ALPHABET whose text puts security at stake).
    assert glosses["A-SPEC"] == (
        "each round's recorded outcome is what the declared measurement gives, "
        "so a detection lost from its round or filed in another, or a no-click "
        "bin dropped, is a security matter")
    # A-ALPHABET itself puts completeness at stake; its own text names the
    # security matter through A-SPEC and A-CONFORM, and so does its gloss.
    assert glosses["A-ALPHABET"] == (
        "all n rounds are in the record (the acceptance test is evaluated on all "
        "n rounds); a measured round missing from it, a lost time tag or "
        "no-click bin included, leaves the counts wrong and is a security matter "
        "under [[A-SPEC]] and [[A-CONFORM]]")
    assert block["text"] == (
        "A round is one use of the protocol as declared, recording its own "
        "outcomes. How a time-tagged system cuts its detection record into rounds "
        "(time bins, coincidence windows, how the stations synchronise) is yours "
        "to choose, and your declaration must describe it. Every one of the n "
        "rounds counts: where your measurement has a no-click outcome, a time bin "
        "in which nothing clicks is a round with that outcome, not one to drop."
    )
    (lab,) = round_block({"A-LAB"}, False)["premises"]
    assert lab["gloss"].endswith(
        "not a clock or trigger line from the untrusted source")
    # The steps follow; the first gives the round count and points back.
    setup = bbm92()["sections"]["setup"]
    step = setup["protocol"][0]
    assert step == {"title": "Rounds",
                    "text": "The protocol runs n = 100,000,000 rounds.",
                    "pointer": "/payload/config/rounds"}
    assert setup["round"] is not None
    assert "A-ROUND" in [premise["short_id"] for premise in setup["round"]["premises"]]
    page = md(bbm92())
    block_md = between(page, 'id="setup-round"', 'id="setup-protocol"')
    assert ("- [A-ROUND](#A-ROUND): the same receiver behaviour in every round"
            in block_md)
    protocol = between(page, 'id="setup-protocol"', 'id="setup-source"')
    assert ("1. Rounds: The protocol runs n = 100,000,000 rounds. See "
            "[What a round is](#setup-round) above.") in protocol
    assert "[A-SPEC]" not in protocol


def test_every_route_theorem_below_accepted_is_named_in_the_review_status() -> None:
    """A route theorem below accepted is named, never left silent.

    The review-status paragraph names the security statements and the run's
    key-length roots and says the device and route premises carry their own
    status; the route theorems of the receiver, reductions, statistics and
    transmitter modules, the assumption manifest's roots, are named there only
    where one is below accepted (report schema 0.21.0: while the certified
    tier's receiver amendments are verified and not yet accepted). So every
    route theorem below accepted is in ``route_claims_below_accepted`` and in
    the paragraph's words, and nothing accepted is.
    """
    from runs.report_examples.generate import EXAMPLES, read_record, record_paths

    from certiqs_key.domain.claim_closure import closure_table
    from certiqs_key.runs.report.build import build_report
    from certiqs_key.runs.report.explain import statement_status

    claims = closure_table()["claims"]
    for example in EXAMPLES:
        for path in record_paths(example):
            record = read_record(path)
            payload = record["payload"]
            roots = (payload.get("assumption_manifest") or {}).get("roots") or {}
            result = build_report(record)["sections"]["result"]
            shown = {claim["id"] for claim in result["statement_claims"]}
            below = {
                claim for found in roots.values() for claim in found
                if claim not in shown
                and claims[claim]["effective_status"] not in ("accepted", "implemented")
            }
            named = {claim["id"] for claim in result["route_claims_below_accepted"]}
            assert named == below, (path, named, below)
            stated = statement_status(result["statement_claims"], (),
                                      result["route_claims_below_accepted"])
            words = "" if stated is None else stated.text()
            for claim_id in below:
                assert f"[[{claim_id}]]" in words, (path, claim_id)


def test_the_first_order_gap_links_to_a_section_the_page_renders() -> None:
    """No dangling "The engine's numerics".

    A first-order run whose receiver weights are all enclosed engages no
    numerical-trust premise, so the page renders no such section; the gap then
    links to Not counted, which names it. A certified page names no gap.
    """
    first_order = md(bbm92_first_order())
    vouch = between(first_order, 'id="vouch"', 'id="not-counted"')
    assert "None of them covers the floating-point arithmetic" in vouch
    assert "#category-numerical-trust" not in first_order
    assert "(#not-counted)" in vouch
    certified = md(bbm92())
    assert "None of them covers the floating-point arithmetic" not in certified
    assert "#category-numerical-trust" not in certified
