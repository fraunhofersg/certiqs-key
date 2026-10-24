"""The key-rate report's presentational points.

The run tier's wording (the seeds, the record's field names, the letter A),
the report prose and the links the Pages site does not serve. None moves a
number. Each test
states one fact a reader relies on; the expected texts are written by hand
from the committed example records and the hand-written synthetic ones,
never read back from the renderer.
"""

from __future__ import annotations

import copy
import gzip
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from tests.support.report_records import as_first_order, refused_record, synthetic_table

from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    pages_site_serves,
    render_excerpts_markdown,
    render_html,
    render_markdown,
)
from certiqs_key.runs.report._page import TIER_CLAUSE
from certiqs_key.runs.report._render import PAGES_SITE_SERVES, readable_value
from certiqs_key.runs.report.explain import binding_words, setup_brief
from certiqs_key.runs.report.glossary import terms
from certiqs_key.runs.report.inputs import input_label
from certiqs_key.runs.report.model import KeyRateReport
from certiqs_key.runs.report.setup import build_setup

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "runs" / "report_examples"


def example(name: str) -> dict[str, Any]:
    folder = EXAMPLES / name
    gz = folder / "record.json.gz"
    if gz.is_file():
        with gzip.open(gz, "rt", encoding="utf-8") as handle:
            data: dict[str, Any] = json.load(handle)
            return data
    loaded: dict[str, Any] = json.loads(
        (folder / "record.json").read_text(encoding="utf-8")
    )
    return loaded


def md(report: KeyRateReport, **options: Any) -> str:
    return render_markdown(report, contract_link=default_contract_link(), **options)


def between(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end, text.index(start))]


# --------------------------------------------------------------------------
# The toy-protocol check's presentational points
# --------------------------------------------------------------------------


def test_m5_a_missing_part_is_said_where_that_part_would_stand() -> None:
    record = refused_record(stage="compilation",
                            reason="band_a_outside_ideal_receiver")
    page = md(build_report(record, table=synthetic_table()))
    setup = between(page, 'id="setup"', 'id="inputs"')
    source = between(setup, 'id="setup-source"', 'id="setup-stations"')
    assert "The record holds no compiled source" in source
    stations = setup[setup.index('id="setup-stations"'):]
    assert "The record holds no receiver stage" in stations
    # Nothing of the kind stands before what a round is or the protocol.
    head = setup[:setup.index('id="setup-protocol"')]
    assert "The record holds no" not in head


def test_m8_public_choices_read_one_per_party() -> None:
    value = [
        {"choices": ["Z", "X", "Y"], "party": "A",
         "weights": {"X": 0.25, "Y": 0.25, "Z": 0.5}},
        {"choices": ["X", "Z"], "party": "B",
         "weights": {"X": "2/3", "Z": "1/3"}},
    ]
    assert binding_words("public_choices", value) == (
        "Alice: Z 0.5, X 0.25, Y 0.25; "
        "Bob: X 0.666667 (2/3), Z 0.333333 (1/3)"
    )
    # Anything of another shape is left to the generic words.
    assert binding_words("public_choices", "not a list") is None


def test_m8_a_value_written_out_in_full_below_is_not_cut_above_it() -> None:
    page = md(build_report(example("bbm92")))
    assert "characters, written out in full below" in page
    assert "characters; in full below)" not in page


def test_m9_an_input_name_that_makes_no_label_is_shown_verbatim() -> None:
    assert input_label("device.alice_y") == ""
    assert input_label("device.bob_z") == ""
    assert input_label("model.qber") == "QBER"
    assert input_label("device.alice_pbs_leak_reflected") == (
        "Alice's PBS leak reflected"
    )
    assert input_label("device.alice_efficiency") == "Alice's efficiency"
    assert input_label("parameters.eps_pa") == "Secrecy error ε_PA"


def test_m10_a_model_named_as_honest_is_not_prefixed_again() -> None:
    setup = build_setup(example("bb84"))
    assert setup["source"] is not None
    setup["source"]["honest_model"] = (
        "honest acceptance table declared in the protocol document"
    )
    lines = setup_brief(setup, [], None)
    source = next(line for line in lines if line.startswith("Source:"))
    assert source.endswith("; honest acceptance table declared in the protocol "
                           "document.")
    assert "honest model honest" not in source


def test_m11_the_glossary_s_template_terms_say_whose_they_are() -> None:
    found = {term.term: term.text for term in terms()}
    assert "BBM92's among them" in found["acceptance value label"]
    assert "the key rounds record gen" in found["acceptance value label"]
    assert found["acceptance map"].startswith("An input of some templates")


def test_n2_outcomes_and_signal_states_keep_their_declared_order() -> None:
    # The document declares (Z,0), (Z,1), (Y,0), (Y,1); the record's canonical
    # tree holds its states sorted, (Y,0) first.
    setup = build_setup(example("document-qubit_bb84_y"))
    declared = ["(Z,0)", "(Z,1)", "(Y,0)", "(Y,1)"]
    assert [letter["letter"] for letter in setup["stations"][0]["outcomes"]] == declared
    assert setup["source"] is not None
    (states,) = [family for family in setup["source"]["families"]
                 if family["title"].startswith("Signal states")]
    elements = states["blocks"][0]["elements"]
    assert [element["outcome"] for element in elements] == declared


def test_n4_n7_an_appendix_mapping_reads_as_words() -> None:
    assert readable_value({"gap_tolerance": None, "max_iterations": 5}) == (
        "gap_tolerance = none; max_iterations = 5"
    )
    assert readable_value({"oracle": {"name": "qics", "capabilities": ["a", "b"]}}) == (
        "oracle = (name = qics; capabilities = (a, b))"
    )
    assert readable_value({}) == "none"
    assert readable_value(["gen", "ok"]) == "gen, ok"
    page = md(build_report(example("bbm92")))
    appendix = page[page.index('id="appendix"'):]
    assert not re.search(r"\| \{\"", appendix)
    assert '"max_iterations": 10' not in appendix
    assert "max_iterations = 10" in appendix


def test_n5_a_custom_document_s_empty_readme_reads_none() -> None:
    page = md(build_report(example("document-bbm92_holder_b")))
    assert "| readme | none |" in page
    assert "| readme |   |" not in page


def test_n6_a_qubit_run_s_glossary_and_stations_carry_no_optical_terms() -> None:
    qubit = md(build_report(example("bb84")))
    glossary = qubit[qubit.index('id="glossary"'):]
    for anchor in ("g-element-graph", "g-exact-window", "g-temporal-mode-index",
                   "g-route-encoded-licensed", "g-photon-cutoff-n"):
        assert f'id="{anchor}"' not in glossary, anchor
    stations = between(qubit, 'id="setup"', 'id="inputs"')
    assert "| Photon cutoff N |" not in stations
    assert "| Exact window |" not in stations
    optical = md(build_report(example("bbm92")))
    assert 'id="g-photon-cutoff-n"' in optical[optical.index('id="glossary"'):]
    assert "| Photon cutoff N | 1 |" in optical


def test_n7_an_input_with_no_effect_says_when_it_would_have_one() -> None:
    report = build_report(example("bbm92"))
    rows = {row["name"]: row for row in report["sections"]["protocol"]["inputs"]}
    assert rows["model.mean_pairs"]["not_used"] == (
        "has no effect under the declared values: it applies only where "
        "source_model is spdc"
    )
    # The source table repeats it beside the value (the stage-9 reader asked
    # why 1/32 pairs sit beside a detection probability of 1).
    source = between(md(report), 'id="setup-source"', 'id="station-')
    assert ("0.03125; has no effect under the declared values: it applies only "
            "where source_model is spdc") in source


# --------------------------------------------------------------------------
# The run tier's minor points
# --------------------------------------------------------------------------


def test_n1_the_review_status_says_every_route_theorem_is_accepted() -> None:
    # bb84's route has no reduction, so no root of the verified
    # reductions/req:recv-row-provenance batch stands among its roots.
    report = build_report(example("bb84"))
    assert report["sections"]["result"]["route_claims_below_accepted"] == []
    assert report["sections"]["result"]["route_claims_accepted"] is True
    guarantee = between(md(report), 'id="guarantee"', 'id="roles"')
    assert ("Every route theorem they reach it through (the roots of this run's "
            "assumption manifest) is accepted with everything it rests "
            "on.") in guarantee


def test_n1_a_manifest_without_roots_states_no_route_status() -> None:
    record = example("bb84")
    record["payload"]["assumption_manifest"]["roots"] = {}
    report = build_report(record)
    assert report["sections"]["result"]["route_claims_accepted"] is False
    assert "Every route theorem" not in md(report)


def test_n1_a_root_the_table_lacks_states_no_route_status() -> None:
    record = example("bb84")
    roots = record["payload"]["assumption_manifest"]["roots"]
    roots.setdefault("receiver", []).append("receiver/thm:no-such-claim")
    report = build_report(record)
    assert report["sections"]["result"]["route_claims_accepted"] is False
    assert "Every route theorem" not in md(report)


def test_n4_the_band_a_error_bar_line_cites_a_ideal() -> None:
    page = md(build_report(example("bb84")))
    not_counted = between(page, 'id="not-counted"', 'id="levers"')
    assert ("A measured value with an error bar is not covered: the result applies "
            "to the exact declared values ([A-IDEAL](#A-IDEAL), [A-ENS](#A-ENS)).") \
        in not_counted


def test_a_seed_says_no_party_is_fixed_to_draw_the_seeds() -> None:
    page = md(build_report(example("bbm92")))
    seed = between(page, 'id="A-SEED"', 'id="category-post-processing"')
    assert ("Which party draws each post-processing seed (the error-correction "
            "seed, the error-verification seed and the privacy-amplification "
            "hash) is not fixed by the analysed post-processing") in seed


def test_the_record_excerpts_end_with_what_their_field_names_mean() -> None:
    record = example("bb84")
    page = render_excerpts_markdown(record, build_report(record))
    names = page[page.index('id="field-names"'):]
    assert ("`key_map`: each pair of readouts with the key holder's raw key bit; "
            "perp marks a round that gives no key bit.") in names
    # Only names the page shows are explained.
    assert "`setting_map`" not in names


def test_the_letter_a_is_in_the_glossary() -> None:
    page = md(build_report(example("bbm92")))
    assert 'id="g-a-the-letter"' in page[page.index('id="glossary"'):]


# --------------------------------------------------------------------------
# The stage-9 readers' report prose
# --------------------------------------------------------------------------


def test_the_guarantee_says_whether_the_first_order_clause_applies() -> None:
    certified = between(md(build_report(example("bbm92"))),
                        'id="guarantee"', 'id="roles"')
    assert TIER_CLAUSE["certified"] in certified
    first_order = between(md(build_report(as_first_order(example("bbm92")))),
                          'id="guarantee"', 'id="roles"')
    assert TIER_CLAUSE["first-order"] in first_order
    assert TIER_CLAUSE["certified"] not in first_order


def test_a_station_s_component_values_name_a_exact() -> None:
    report = build_report(example("bbm92"))
    rows = {row["name"]: row for row in report["sections"]["protocol"]["inputs"]}
    for name in ("device.alice_efficiency", "device.bob_dark_count",
                 "device.alice_pbs_leak_reflected", "device.bob_half_wave_angle"):
        assert "A-EXACT" in rows[name]["covered_by"], name
        # The inference is the report's, kept apart from the record's bindings.
        assert "A-EXACT" not in rows[name]["bound_by"], name
    # An analysis choice and the honest model's channel are not device values.
    for name in ("device.alice_photon_cutoff", "device.alice_exact_window",
                 "model.alice_transmittance", "device.test_fraction"):
        assert "A-EXACT" not in rows[name]["covered_by"], name


def test_a_single_receiver_s_component_values_name_a_exact() -> None:
    # F-2: optical_bb84's parameters name no station (one receiver); its
    # protocol document declares the receiver's detectors and elements with
    # them.
    report = build_report(example("optical_bb84"))
    rows = {row["name"]: row for row in report["sections"]["protocol"]["inputs"]}
    for name in ("device.efficiency", "device.dark_count", "device.basis_split",
                 "device.half_wave_angle"):
        assert rows[name]["covered_by"] == ["A-EXACT"], name
    for name in ("device.photon_cutoff", "device.exact_window",
                 "device.efficiency_normalization", "model.transmittance",
                 "model.qber"):
        assert rows[name]["covered_by"] == [], name
    page = md(report)
    device = between(page, 'id="inputs-device"', 'id="inputs-budget"')
    assert "[A-EXACT](#A-EXACT) asks you to vouch that every number you declared " \
        "for a receiver component" in device
    # A decoy source's intensities and the protocol's choice weights are not
    # receiver components.
    decoy = build_report(example("decoy_bb84"))
    found = {row["name"]: row for row in decoy["sections"]["protocol"]["inputs"]}
    assert found["device.efficiency"]["covered_by"] == ["A-EXACT"]
    for name in ("device.mu_signal", "device.gamma", "device.test_signal"):
        assert found[name]["covered_by"] == [], name


def test_a_qubit_run_names_no_a_exact_beside_its_inputs() -> None:
    report = build_report(example("bb84"))
    assert all(row["covered_by"] == []
               for row in report["sections"]["protocol"]["inputs"])
    assert "asks you to vouch that every number you declared" not in md(report)


def test_a_premise_has_one_status_row_and_no_repeated_verification() -> None:
    page = md(build_report(example("bbm92")))
    premises = between(page, 'id="assumptions"', 'id="appendix"')
    assert "| Review status with its dependencies |" not in premises
    assert "| Review status | accepted, also with everything it rests on |" in premises
    assert ("| Verification | The engine does not verify this assumption"
            not in premises)
    # The group's lead says it once.
    assert "The engine does not verify these premises" in premises


def test_the_pump_and_trigger_of_an_untrusted_source_are_outside_the_labs() -> None:
    page = md(build_report(example("bbm92")))
    roles = between(page, 'id="roles"', 'id="vouch"')
    assert ("The source, its pump, timing and trigger electronics included, counts "
            "as outside every laboratory wherever it stands "
            "([A-LAB](#A-LAB)).") in roles


def test_the_snap_section_says_it_asks_nothing_where_no_premise_is_added() -> None:
    page = md(build_report(example("bbm92")))
    assert ("The rounding adds no premise: the key length does not rest on A-SNAP, "
            "so nothing in this section asks anything of you.") in page


# --------------------------------------------------------------------------
# Links the Pages site does not serve
# --------------------------------------------------------------------------


def _site_builder() -> ModuleType:
    """Return ``harness/build_pages_site.py``, loaded by path.

    ``tests/harness/`` is a package named ``harness`` too, so the tool is
    loaded from its file, as tests/harness/test_build_pages_site.py does.
    """
    name = "_harness_build_pages_site"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, ROOT / "harness" / "build_pages_site.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def test_the_served_patterns_are_the_site_builder_s() -> None:
    tool = _site_builder()
    assert PAGES_SITE_SERVES == tool.ALLOW
    for path in ("spec/modules/meat-core/contract.pdf", "instances/bbm92/README.md",
                 "spec/architecture.md", "runs/report_examples/bb84/report.html",
                 "runs/report_examples/bb84/report.md"):
        assert pages_site_serves(path) == tool.allowed(path), path


def test_a_page_for_the_site_prints_an_unserved_path_in_code() -> None:
    report = build_report(example("bbm92"))
    base = "../../../"
    site = render_html(report, contract_link=default_contract_link(base),
                       repo_base=base, repo_served=pages_site_serves)
    assert 'href="../../../instances/' not in site
    assert 'href="../../../spec/architecture.md"' not in site
    assert "<code>instances/bbm92/README.md</code>" in site
    assert "<code>spec/architecture.md</code>" in site
    # A contract stays linked: the site serves it.
    assert 'href="../../../spec/modules/meat-core/contract.pdf#' in site
    # Without the site's filter every path links, as in a checkout.
    local = md(copy.deepcopy(report), repo_base=base)
    assert "](../../../instances/bbm92/README.md)" in local


# --------------------------------------------------------------------------
# K2b: the soundness check's findings and the reader round
# --------------------------------------------------------------------------


def test_f6_an_empty_container_is_not_read_as_null() -> None:
    assert readable_value({"constrained": None, "selector": [], "map": {}}) == (
        "constrained = none; selector = empty; map = empty"
    )


def test_f7_a_page_without_stations_keeps_optical_terms_its_inputs_use() -> None:
    from certiqs_key.runs.report._page import _optical

    cutoff: Any = {"name": "device.photon_cutoff"}
    assert _optical(None, [cutoff]) is True
    assert _optical(None, []) is False


def test_f9_the_key_holder_s_field_says_both_keys_come_from_its_string() -> None:
    record = example("bb84")
    page = render_excerpts_markdown(record, build_report(record))
    assert ("`key_holder`: the party (A or B) whose raw string both keys are "
            "computed from.") in page


def test_an_idealised_honest_model_names_its_exact_zero_outcomes() -> None:
    page = md(build_report(example("bbm92")))
    considerations = between(page, 'id="considerations"', 'id="result"')
    assert ("The acceptance test built from it admits a count of exactly 0 "
            "in ") in considerations
    assert "makes the run abort ([A-CONFORM](#A-CONFORM); see Acceptance test)" \
        in considerations
    assert "possibly on almost every run" not in considerations


def test_a_step_limited_search_with_a_large_gap_is_said_in_the_summary() -> None:
    decoy = between(md(build_report(example("decoy_bb84"))),
                    'id="considerations"', 'id="result"')
    assert ("The solver stopped at its step limit after 20 steps with its "
            "estimate of h_low above its first-order bound h_lb by a relative "
            "gap of 0.614") in decoy
    # decoy_bb84 is certified (R2-1 of the round-2 check).
    assert ("Stopping early does not invalidate the key length: it makes the "
            "bound looser, not invalid") in decoy
    assert "The key length is valid as it stands" not in decoy
    # A gap below one percent is not named (bbm92's is about 7e-06).
    bbm92 = between(md(build_report(example("bbm92"))),
                    'id="considerations"', 'id="result"')
    assert "relative gap" not in bbm92


def test_a_reach_s_category_label_does_not_deny_security() -> None:
    page = md(build_report(example("decoy_bb84")))
    reach = between(page, 'id="A-REACH"', 'id="premises-engine"')
    assert "not security" not in reach
    assert "| If it fails | security" in reach


def test_the_guarantee_names_the_authenticated_channel_composability_rests_on() -> None:
    guarantee = between(md(build_report(example("bbm92"))),
                        'id="guarantee"', 'id="roles"')
    assert ("The composable statement takes its authenticated classical channel "
            "from [A-AUTH](#A-AUTH), whose own text says that no composable proof "
            "for this timing-aware channel is published yet") in guarantee
    assert "reviewed adversarially by an AI model and accepted by the project's " \
        "human owner" in guarantee


def test_the_announcements_come_after_the_round_s_measurements() -> None:
    page = md(build_report(example("bb84")))
    step = between(page, "5. Announcements:", "6. ")
    assert ("Each announcement is computed from the announcing party's own "
            "readout (the record's announcement tables)") in step
    # A-SEQ makes it a premise, not a fact (R2-4).
    assert ("So the analysis assumes that no announcement, a basis included, "
            "comes before a measurement of its round; you vouch for this under "
            "[A-SEQ](#A-SEQ).") in step


def test_the_reader_round_s_terms_are_in_the_glossary() -> None:
    decoy = md(build_report(example("decoy_bb84")))
    glossary = decoy[decoy.index('id="glossary"'):]
    for anchor in ("g-sr3", "g-decimal-precision"):
        assert f'id="{anchor}"' in glossary, anchor
    six = md(build_report(example("document-qubit_bb84_y")))
    assert 'id="g-band-a-route"' in six[six.index('id="glossary"'):]


# --------------------------------------------------------------------------
# K2c: the round-2 soundness check
# --------------------------------------------------------------------------


def test_the_large_gap_line_claims_no_more_on_a_first_order_run() -> None:
    page = md(build_report(as_first_order(example("decoy_bb84"))))
    considerations = between(page, 'id="considerations"', 'id="result"')
    assert "The key length is valid as it stands" not in considerations
    assert "Stopping early does not invalidate the key length" not in considerations
    assert ("The guarantee's first-order clause still applies: the computed h_lb "
            "is not proved to lie below h_low") in considerations


def test_the_device_lead_promises_a_exact_for_every_value_not_every_row() -> None:
    report = build_report(example("optical_bb84"))
    rows = {row["name"]: row for row in report["sections"]["protocol"]["inputs"]}
    # The document declares it through an expression, "1 - pbs_leak_reflected".
    assert rows["device.pbs_leak_reflected"]["covered_by"] == ["A-EXACT"]
    device = between(md(report), 'id="inputs-device"', 'id="inputs-budget"')
    assert ("It applies to every such value, whether or not the Premises column "
            "names it there: the column names it only beside the values the "
            "report could tie to a receiver.") in device
    assert "beside each such value the record ties to a receiver" not in device


def test_the_certified_line_names_only_the_engine_premises_the_run_lists() -> None:
    qubit = between(md(build_report(example("bb84"))),
                    'id="considerations"', 'id="result"')
    assert "the premises the run lists remain." in qubit
    assert "about artefacts and the engine" not in qubit
    decoy = between(md(build_report(example("decoy_bb84"))),
                    'id="considerations"', 'id="result"')
    # decoy's chain is not attested, so A-LINK stays; its receiver artefact
    # is the run's own, exact and rigorous, so A-RECV is discharged
    # (reductions/req:recv-row-provenance) and not named.
    assert ("the premises the run lists remain, [A-LINK](#A-LINK), about an "
            "artefact or the engine, among them.") in decoy
    assert "[A-RECV](#A-RECV)" not in decoy
