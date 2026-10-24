"""The key-rate report's cap on how often devices as declared pass the test.

WHY THIS EXISTS. ``meat-core/req:unreachable-acceptance-set`` (v) asks the
report to show, beside every key length and in place of one on a run refused
under item (iv), the cap on the probability that devices the declaration
admits pass the acceptance test (``meat-core/prop:model-pass-bound`` (ii)):
``2^-x`` and a decimal, both rounded upward and labelled so, with the tier of
``b``, ``tau`` and whether the run was refused as the record carries that
decision; never as bits and never with the proven part or a share; and,
where there is no cap, that there is none and why. A cap shown rounded DOWN
would claim a smaller pass probability than is proven. The expected texts
and numbers are written by hand from the fixture, never read back from the
renderer.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest
from tests.support.report_records import (
    completed_record,
    refused_record,
    synthetic_table,
)

from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_html,
    render_markdown,
)
from certiqs_key.runs.report.explain import cap_probability_text, pass_exponent_text


def _block(
    exponent: float | None, *, tau: str = "1/2", refused: bool = False,
    decision: str | None = "exact", bound: float | None = 3e-8,
    tier: str = "certified", no_bound_reason: str | None = None,
) -> dict[str, Any]:
    cap = exponent is not None
    return {
        "checked": True, "unchecked_reason": None, "unchecked_premise": None,
        "statistics_check": "on", "honest_statistics_supplied": True,
        "caller_constraint_entries": 0,
        "min_model_pass_probability": tau, "rounds": 1_000_000_000,
        "alpha_0_rule": "fixed_order",
        "solve": {"alpha_0": 1.5, "bound": bound,
                  "bound_tier": None if bound is None else tier,
                  "no_bound_reason": no_bound_reason},
        "model_pass_exponent_bits": exponent,
        "model_pass_exponent_tier": tier if cap else None,
        "model_pass_decision": decision if cap else None,
        "no_cap_reason": None if cap else (
            "no_bound_formed" if bound is None else "bound_not_positive"
        ),
        "refused": refused,
        "orders": [{"alpha": 1.5, "proven_part_bits": 30.0}],
    }


def _completed(block: dict[str, Any]) -> Any:
    def edit(record: dict[str, Any]) -> None:
        record["payload"]["statistics_consistency"] = block

    return build_report(completed_record(edit=edit), table=synthetic_table())


def _refused(block: dict[str, Any]) -> Any:
    record = refused_record(stage="solve", reason="acceptance_set_unreachable")
    record["payload"]["statistics_consistency"] = block
    return build_report(record, table=synthetic_table())


def _md(report: Any) -> str:
    return render_markdown(report, contract_link=default_contract_link())


# --------------------------------------------------------------------------
# The numbers shown, rounded the safe way
# --------------------------------------------------------------------------


def test_the_shown_exponent_is_rounded_down() -> None:
    # Six significant digits toward zero: 9.999999999999998 shows 9.99999,
    # never 10; from 100000 on the integer part.
    assert pass_exponent_text(9.999999999999998) == "9.99999"
    assert pass_exponent_text(1.0) == "1"
    assert pass_exponent_text(0.5) == "0.5"
    assert pass_exponent_text(278712.9) == "278712"
    assert pass_exponent_text(0.41399999) == "0.413999"
    for value in (9.999999999999998, 0.41399999, 1.2349e-05, 278712.9, 7 / 30):
        assert Fraction(pass_exponent_text(value)) <= Fraction(value)
    with pytest.raises(ValueError):
        pass_exponent_text(0.0)


def test_the_decimal_cap_is_rounded_up() -> None:
    """Three significant digits, upward, derived by hand.

    2^-0.5 = 0.70710678... shows 0.708. An integer exponent is a power of two
    formed exactly: 2^-1 = 0.5, 2^-2 = 0.25, 2^-10 = 0.0009765625 shows
    9.77 x 10^-4. 2^-9.99999 = 2^-10 * 2^0.00001 = 0.00097656927... shows
    9.77 x 10^-4. 2^-100 = 7.8886e-31 shows 7.89 x 10^-31.
    """
    assert cap_probability_text("0.5") == "0.708"
    assert cap_probability_text("1") == "0.5"
    assert cap_probability_text("2") == "0.25"
    assert cap_probability_text("10") == "9.77 \u00d7 10^-4"
    assert cap_probability_text("9.99999") == "9.77 \u00d7 10^-4"
    assert cap_probability_text("100") == "7.89 \u00d7 10^-31"
    assert Fraction(cap_probability_text("0.5")) ** 2 >= Fraction(1, 2)


# --------------------------------------------------------------------------
# The sentences
# --------------------------------------------------------------------------

#: The hypothesis, evidence-level and same-run sentences every cap carries.
EVIDENCE = (
    "where in every round the acceptance value, given the earlier rounds, "
    "follows the statistics of a state the model admits."
)
NOT_A_PROOF = (
    "This is about the model, not your real devices: if they pass a test fixed "
    "before the run, that is evidence against the model only at the level of "
    "this cap, the stronger the smaller the cap, and not a proof."
)
SAME_RUN = (
    "An acceptance set built from the same run's frequencies passes by "
    "construction, so no such reading applies to it."
)


def test_an_unrefused_run_shows_the_cap_as_a_probability_beside_its_key() -> None:
    """With x = 1/2 against tau = 1/3, 2^-1/2 = 0.707... > 1/3, not refused."""
    report = _completed(_block(0.5, tau="1/3", decision="enclosure"))
    result = str(report["sections"]["summary"]["result"])
    assert (
        "Devices that behave as your declared model says pass this acceptance "
        "test with probability at most "
        "2^-0.5 \u2248 0.708 (both rounded upward; certified bound; "
        "[[meat-core/prop:model-pass-bound]]), " + EVIDENCE
    ) in result
    assert ("This is above your threshold min_model_pass_probability = 1/3, so "
            "the check does not refuse the run.") in result
    assert NOT_A_PROOF in result and SAME_RUN in result
    # Never bits, never the proven part, never a share.
    assert "bits of this key" not in result and "30 bits" not in result
    assert "share" not in result
    html = render_html(report, contract_link=default_contract_link())
    assert "at most 2<sup>\u22120.5</sup> \u2248 0.708 (both rounded upward" in html
    check = report["sections"]["result"]["statistics_check"]
    assert check["refused"] is False and check["min_model_pass_probability"] == "1/3"
    short = [c["text"] for c in report["sections"]["summary"]["considerations"]
             if c["text"].startswith("Devices that behave")]
    assert short == [
        "Devices that behave as your declared model says pass the acceptance test "
        "with probability at most 2^-0.5 \u2248 0.708 (rounded upward), above your "
        "threshold of 1/3."
    ]


def test_a_refused_run_shows_the_cap_in_place_of_a_key_length() -> None:
    report = _refused(_block(9.999999999999998, refused=True))
    texts = [c["text"] for c in report["sections"]["summary"]["considerations"]]
    (refusal,) = [t for t in texts if t.startswith("The accepted statistics")]
    assert refusal == (
        "The accepted statistics were checked against your declared model: no "
        "state it admits has per-round statistics that the acceptance test "
        "accepts ([[meat-core/req:unreachable-acceptance-set]], "
        "[[meat-core/prop:minimal-divergence]]). Devices that behave as your "
        "declared model says pass this "
        "acceptance test with probability at most 2^-9.99999 \u2248 9.77 \u00d7 "
        "10^-4 (both rounded upward; certified bound; "
        "[[meat-core/prop:model-pass-bound]]), " + EVIDENCE + " This is at most "
        "your threshold min_model_pass_probability = 1/2 (decided on the exact "
        "value, so a displayed value a little above the threshold is the upward "
        "rounding), so the run is refused and reports no key length. "
        + NOT_A_PROOF + " " + SAME_RUN
    )
    page = _md(report)
    assert "2^-9.99999 \u2248 9.77 \u00d7 10^-4" in page


def test_an_undecided_refusal_says_so() -> None:
    report = _refused(_block(1.5, tau="1/3", refused=True, decision="undecided"))
    texts = " ".join(c["text"] for c in report["sections"]["summary"]["considerations"])
    assert ("This is not shown to exceed your threshold "
            "min_model_pass_probability = 1/3 (the exact value lies too close to "
            "the threshold for the comparison to be decided either way, and an "
            "undecided comparison refuses)") in texts
    assert "This is at most your threshold" not in texts


def test_where_there_is_no_cap_the_report_says_so_and_why() -> None:
    nonpositive = str(_completed(_block(None, bound=-1e-12))
                      ["sections"]["summary"]["result"])
    assert ("no mismatch is proven (the certified lower bound on it is not "
            "positive), so there is no cap on how often devices as declared pass "
            "the test, and the check refuses nothing.") in nonpositive
    assert "pass this acceptance test" not in nonpositive
    unformed = str(_completed(_block(None, bound=None,
                                     no_bound_reason="first_order_withdrawn"))
                   ["sections"]["summary"]["result"])
    assert ("no bound on their mismatch was formed (first_order_withdrawn; "
            "[[meat-core/req:unreachable-acceptance-set]]), so a mismatch is "
            "neither proven nor ruled out, there is no cap on how often devices "
            "as declared pass the test, and the check refuses nothing.") in unformed


def test_a_record_before_the_cap_rule_has_no_check_in_its_report() -> None:
    """A 0.45.0 statistics_consistency (contradiction_share, no tau) is not read."""
    old = {"checked": True, "unchecked_reason": None, "contradiction_share": "1/100",
           "orders": [], "solve": None, "refused_as_whole": False}
    report = _completed(old)
    assert report["sections"]["result"]["statistics_check"] is None


def test_a_run_with_a_reference_companion_says_which_model_the_cap_is_of() -> None:
    """The cap is the searched declaration's; the companion is glossed plainly."""

    def edit(record: dict[str, Any]) -> None:
        record["payload"]["statistics_consistency"] = _block(0.5, tau="1/3")
        record["payload"]["stages"]["key_rate"]["reference_bracket"] = {
            "status": "counted"
        }

    report = build_report(completed_record(edit=edit), table=synthetic_table())
    result = str(report["sections"]["summary"]["result"])
    assert ("Devices that behave as your declared model says (in the rounded form "
            "the solver searched; the run also evaluated a refined form of your "
            "receiver model, the reference companion, and this cap is not shown "
            "to hold for it) pass this acceptance test") in result
    plain = str(_completed(_block(0.5, tau="1/3"))["sections"]["summary"]["result"])
    assert "reference companion" not in plain
