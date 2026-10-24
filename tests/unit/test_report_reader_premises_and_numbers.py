"""The run report as a reader finds it: premises, what is not counted, numbers.

Each test states what the reader finds on the page; the expectations are
written by hand from the bbm92 example's record, never read back from the
renderer.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

from tests.support.report_records import as_first_order

from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_html,
    render_markdown,
)
from certiqs_key.runs.report.__main__ import main
from certiqs_key.runs.report._page import _epsilon
from certiqs_key.runs.report._render import RESIDUE_NOTE, UNVERIFIED, with_decimal
from certiqs_key.runs.report.explain import (
    COMPLETENESS_CLAIM,
    PER_EXECUTION_CLAIM,
    binding_words,
)
from certiqs_key.runs.report.model import KeyRateReport
from certiqs_key.runs.report.setup import build_setup

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
# One line per refines-family, the devices first
# --------------------------------------------------------------------------


def test_vouch_lists_one_line_per_family_with_its_refinements() -> None:
    summary = bbm92()["sections"]["summary"]
    # The receivers first; BBM92's source is untrusted, so no source group
    # (spec/pm-eb-roles, role-audit.md section 7, report change 3), and the
    # laboratories follow in the table's category order.
    abouts = [group["about"] for group in summary["vouch"]]
    # No artefact group: A-RECV is discharged on the run's own exact, rigorous
    # receiver artefacts and A-LINK on its attested links.
    assert abouts == ["Your devices and setup", "How the run is carried out"]
    # The receivers first in the devices group; BBM92's untrusted source
    # engages no source premise.
    devices = summary["vouch"][0]["entries"]
    assert devices[0]["short_id"] == "A-MEAS"
    lines = {line["short_id"]: line for group in summary["vouch"]
             for line in group["entries"]}
    # A-PASSIVE refines A-TRUST: it is named on A-TRUST's line, not its own.
    assert "A-PASSIVE" not in lines
    assert "A-PASSIVE" in lines["A-TRUST"]["refinements"]
    part = between(md(bbm92()), 'id="vouch"', 'id="not-counted"')
    # Each line is the premise's one-liner, its claim summary's first sentence.
    assert ("- [A-TRUST](#A-TRUST): The declared instrument describes the "
            "physical receiver exactly, and the receiver is under the legitimate "
            "party's control. — security; 7 refinements: ") in part


# --------------------------------------------------------------------------
# The three forms of the measurement, the paths and the mode names
# --------------------------------------------------------------------------


def test_one_sentence_says_what_each_form_of_the_measurement_is() -> None:
    part = between(md(bbm92()), 'id="setup"', 'id="inputs"')
    assert part.count(
        "The measurement appears below in 3 forms: per photon number, the "
        "receiver's measurement as declared, before dark counts; the same with "
        "the declared dark counts composed in; and the squashed target POVM, the "
        "finite model the proof analyses in place of the device ("
    ) == 1, "Bob's station is identical to Alice's and points to it"


def test_a_beamsplitter_says_which_path_light_goes_to() -> None:
    setup = build_setup(record())
    bob = next(station for station in setup["stations"] if station["party"] == "B")
    words = {element["name"]: element["description"] for element in bob["elements"]}
    assert "H stays in path Z, V is reflected into path Zr" in words["pbs_z"]
    assert "H stays in path X, V is reflected into path Xr" in words["pbs_x"]
    assert ("a photon from path Z stays in path Z with probability 0.5 and "
            "otherwise moves to path X") in words["bs"]
    assert any(note.startswith(
        "Mode names are the instance's labels, a path and a polarisation: "
        "Xr_V is V-polarised light in path Xr."
    ) for note in bob["notes"])


# --------------------------------------------------------------------------
# Not counted
# --------------------------------------------------------------------------


def test_not_counted_opens_with_the_exact_values_and_the_numerics() -> None:
    # On a first-order run (the committed example certifies), read off
    # ``as_first_order``.
    items = bbm92_first_order()["sections"]["summary"]["not_counted"]
    assert items[0]["text"] == (
        "A measured value with an error bar is not covered: the result applies "
        "to the exact declared values ([[A-EXACT]])."
    )
    # The bound trusts no solver step;
    # what is left uncounted is its binary64 objective and gradient.
    assert items[1]["text"] == (
        "The first-order bound's objective and gradient are computed in "
        "floating point with no bound on their numerical error "
        "([[meat-core/frank-wolfe/rem:fo-arithmetic]])."
    )
    assert items[1]["anchor"] == "how-computed"
    part = between(md(bbm92_first_order()), 'id="not-counted"', 'id="levers"')
    assert "See [How the number was computed](#how-computed)." in part


def test_the_guarantee_s_paragraphs_are_not_repeated_under_not_counted() -> None:
    items = bbm92()["sections"]["summary"]["not_counted"]
    for claim in (COMPLETENESS_CLAIM, PER_EXECUTION_CLAIM):
        assert not any(claim in item["text"] for item in items)
    assert any(item["anchor"] == "guarantee" for item in items)
    page = md(bbm92())
    assert page.count("bounds one thing only: the chance that an honest run") == 1


# --------------------------------------------------------------------------
# Links and numbers
# --------------------------------------------------------------------------


def test_markdown_writes_a_record_pointer_as_a_short_link(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    assert main([str(BBM92), "--format", "md", "--out", str(out)]) == 0
    page = out.read_text(encoding="utf-8")
    assert "[record](record.md#p-.payload.stages.acceptance_construction)" in page
    assert "[`/payload" not in page
    html = render_html(bbm92(), contract_link=default_contract_link())
    assert "/payload/stages/acceptance_construction" in html


def test_an_exact_fraction_shows_its_decimal() -> None:
    # Decimal first; the fraction beside it only where the decimal is not
    # exact.
    assert with_decimal("4/5") == "0.8"
    assert with_decimal("1/32") == "0.03125"
    assert with_decimal("205/2048") == "0.100098 (205/2048)"
    assert with_decimal("1") == "1"
    assert with_decimal(0.5) == "0.5"
    assert with_decimal(2.0 ** -30) == "9.31e-10 (2^-30)"
    assert "| 0.03125; has no effect under the declared values" in md(bbm92())


def _example_records() -> list[dict[str, Any]]:
    found = []
    for path in sorted((ROOT / "runs" / "report_examples").glob("*/record.json*")):
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                found.append(json.load(handle))
        else:
            found.append(json.loads(path.read_text(encoding="utf-8")))
    return found


def test_every_mentioned_claim_id_links_to_a_claim_that_exists() -> None:
    # The report resolves a mention from the record's claim graph and the
    # registered module paths without reading spec/; this test reads spec/
    # to check that every link it so builds has a claim file behind it.
    mentions: dict[str, Any] = {}
    for data in _example_records():
        mentions.update(build_report(data)["index"].get("mentions") or {})
    assert "def:protocol" in mentions, "a bare id the closure table lacks"
    for token, anchor in mentions.items():
        claim = anchor["anchor"].removeprefix("claim-")
        module, _, local = claim.rpartition("/")
        kind, _, label = local.partition(":")
        path = ROOT / "spec" / "modules" / module / "claims" / f"{kind}-{label}.tex"
        assert path.is_file(), (token, claim)
        assert claim.endswith(token.rpartition("/")[2]), (token, claim)
        assert anchor["pdf"] == f"spec/modules/{module.split('/')[0]}/contract.pdf"


# --------------------------------------------------------------------------
# Further reader checks
# --------------------------------------------------------------------------


def test_the_acceptance_test_says_what_the_record_holds_of_its_intervals() -> None:
    data = record()
    acceptance = build_setup(data)["acceptance"]
    assert acceptance is not None
    honest = acceptance["honest"]
    assert [row["outcome"] for row in honest] == acceptance["outcomes"]
    assert abs(sum(row["probability"] for row in honest) - 1) < 1e-9
    # Record 0.36.0 lists the box: one category row per outcome.
    assert [row["outcome"] for row in acceptance["categories"]] == acceptance[
        "outcomes"]
    assert "The table of acceptance categories" in acceptance["text"]
    # A record without the box says it does not list the intervals.
    del data["payload"]["stages"]["acceptance_construction"]["box"]
    older = build_setup(data)["acceptance"]
    assert older is not None and older["categories"] == []
    assert "does not list the intervals themselves" in older["text"]


def test_tau_and_invoked_at_are_said_in_words() -> None:
    tau = binding_words("tau", 0)
    assert tau is not None and tau.startswith("0, the temporal or spectral index")
    assert "not the declared tolerance" in tau
    one = binding_words("invoked_at", ["off"])
    assert one is not None and one.startswith("'off', the setting with no probe light")
    assert "not a switch of the exact window" in one
    assert one.endswith("so the setting's multi-click weight rests on this premise")
    none = binding_words("invoked_at", [])
    assert none is not None and "not drawn on" in none
    assert binding_words("eps_eig", 1e-9) is None
    text = md(bbm92())
    part = between(text, 'id="assumptions"', 'id="appendix"')
    assert "(tau): 0, the temporal or spectral index of every mode label" in part


def test_the_group_sentence_on_verification_admits_partial_checks() -> None:
    assert "that part is checked and the rest is yours" in UNVERIFIED
    assert "a premise whose verification differs says so under it" in UNVERIFIED


def test_an_epsilon_that_is_a_power_of_two_also_reads_as_one() -> None:
    assert _epsilon(2.0 ** -30) == "9.31e-10 (2^-30)"
    assert _epsilon(2.0 ** -29) == "1.86e-09 (2^-29)"
    assert _epsilon(0.0) == "0"
    assert _epsilon(1e-9) == "1e-09"
    assert _epsilon(None) == "—"


def test_the_residue_note_says_unrounded() -> None:
    assert "the unrounded values are in the record excerpt" in RESIDUE_NOTE
