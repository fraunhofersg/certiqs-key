"""How the report reads the fallback and a bracket withdrawn as inconsistent.

``meat-core/frank-wolfe/req:certified-evaluation`` (i), (vi), (ix) and
``req:bracket-on-reference`` (iv), (v), as the report reads record 0.35.0.
The report examples run neither case, so ``certified_basis`` and the snaps
section's reading of the two were pinned by their paraphrase pins alone.
"""

from __future__ import annotations

from typing import Any

import pytest

from certiqs_key.runs.report.explain import certified_basis
from certiqs_key.runs.report.snaps import _fallback_sentence, _route_reading

pytestmark = pytest.mark.contract


def _result(on: str | None, fallback: bool, premises: list[str]) -> Any:
    return {
        "certified_on": on,
        "certified_fallback": fallback,
        "certified_premises": premises,
    }


def test_the_fallback_names_the_searched_declaration_and_a_snap() -> None:
    text = certified_basis(_result("searched", True, ["A-SNAP"]))
    assert "rounded measurement the solver searched, not on your receiver model" in text
    assert "no number is formed from the two together" in text
    assert "[[A-SNAP]]" in text


def test_on_the_companion_with_no_premise_no_snap_is_named() -> None:
    text = certified_basis(_result("reference_companion", False, []))
    assert "reference companion" in text and "A-SNAP" not in text
    assert certified_basis(_result(None, False, [])) == ""


def test_the_snaps_section_reads_the_fallback_and_the_inconsistency() -> None:
    fallback: dict[str, Any] = {
        "snaps": {"reference_companion": {"fallback": True}},
        "stages": {"key_rate": {"reference_bracket": {"status": "counted"}}},
    }
    status, reason = _route_reading(fallback, "counted", None)
    assert (status, reason) == ("counted", "companion_not_certified")
    sentence = _fallback_sentence(status, reason, technical=False)
    assert sentence is not None and "rest on A-SNAP" in sentence
    counted: dict[str, Any] = {
        "snaps": {"reference_companion": {"fallback": False}},
        "stages": {"key_rate": {"reference_bracket": {"status": "counted"}}},
    }
    assert (
        _fallback_sentence(*_route_reading(counted, "counted", None), technical=False)
        is None
    )
    withdrawn: dict[str, Any] = {
        "snaps": {"reference_companion": {"fallback": False}},
        "stages": {
            "key_rate": {
                "reference_bracket": {
                    "status": "withdrawn",
                    "cause": "factor_enclosure_inconsistent",
                }
            }
        },
    }
    status, reason = _route_reading(
        withdrawn, "withdrawn", "reference_bracket_withdrawn"
    )
    assert reason == "factor_enclosure_inconsistent"
    sentence = _fallback_sentence(status, reason, technical=False)
    assert sentence is not None and "defect of the engine" in sentence
