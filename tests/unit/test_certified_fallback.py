"""Where the certified evaluation runs a second time, and what it names then.

``meat-core/frank-wolfe/req:certified-evaluation`` (i), (vi), (ix):
:func:`~certiqs_key.solvers.frank_wolfe.general_keyrate._certify` with the
evaluation itself stubbed, so that each branch of the trigger is decided on
what the companion's evaluation returned:

* THE FALLBACK runs where the companion certified no point -- once more on the
  searched declaration, with the search's points and solves and the dropped
  set, no companion handed -- and nowhere else: not where a companion point is
  certified (a ``withheld`` one included), not under ``strict_snaps``, not
  where the arithmetic is unavailable, not where no companion's bracket counts;
* an inconsistency of a block's two enclosures (item (iv)(c)) runs the
  evaluation on the searched declaration too, naming the cause that withdraws
  the bracket;
* the claim roots of a fallback result name ``cor:certified-keylength`` and
  never ``cor:certified-keylength-reference`` (item (vi)).

The claim closure of ``cor:certified-keylength-reference`` reaches
``lem:certified-bracket-enclosed`` and
``meat-core/cor:reference-companion-factors``.
"""

from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from certiqs_key.domain import claim_closure
from certiqs_key.domain.claim_closure import (
    CERTIFIED_REFERENCE_ROOT,
    CERTIFIED_ROOT,
    KEY_LENGTH_ROOT,
    REFERENCE_ROOT,
)
from certiqs_key.solvers.frank_wolfe import general_keyrate
from certiqs_key.solvers.frank_wolfe.certified_record import (
    CERTIFIER_UNAVAILABLE,
    EVALUATION_OFF,
    FACTOR_ENCLOSURE_INCONSISTENT,
    NOT_CERTIFIED,
    ON_REFERENCE_COMPANION,
    ON_SEARCHED,
    RANK_NOT_CERTIFIED,
    CertifiedEvaluation,
    CertifiedPoint,
)
from certiqs_key.solvers.frank_wolfe.general_keyrate import result_claim_roots
from certiqs_key.solvers.frank_wolfe.reference import KeptPoint

pytestmark = pytest.mark.contract


def _evaluation(*reasons: str, seconds: float = 1.0) -> CertifiedEvaluation:
    """One point; certified where no reason is given."""
    if not reasons:
        point = CertifiedPoint(0, 7, True, F(1), F(-1, 2))
        return CertifiedEvaluation(
            "on", "certified", F(1, 2), (point,), seconds=seconds
        )
    point = CertifiedPoint(0, 7, False, reasons=reasons)
    return CertifiedEvaluation(
        "on", NOT_CERTIFIED, None, (point,), (NOT_CERTIFIED,), seconds=seconds
    )


RUN = SimpleNamespace(
    reference_candidates=[
        KeptPoint(
            SimpleNamespace(  # type: ignore[arg-type]
                point="P", q_iterate="Q", solves="S", gate=SimpleNamespace(iteration=7)
            ),
            ("best", "last"),
            1,
        )
    ],
    dropped_set=(),
)
#: The companion's points as req:certified-evaluation (i) selects them
#: (ReferenceBracket.certification_points): the point as consumed, with its
#: fresh solve on the companion.
REFERENCE = SimpleNamespace(
    maps="companion maps",
    certification_points=lambda: [
        SimpleNamespace(
            point_set="search",
            sequence=1,
            candidate=SimpleNamespace(
                point="P", q_iterate="Q", gate=SimpleNamespace(iteration=7)
            ),
            reference=SimpleNamespace(solves="fresh"),
        )
    ],
)


def _certify(
    monkeypatch: pytest.MonkeyPatch,
    companion: CertifiedEvaluation,
    searched: CertifiedEvaluation,
    *,
    reference: Any = REFERENCE,
    strict_snaps: bool = False,
    option: str = "on",
) -> tuple[CertifiedEvaluation, list[tuple[Any, Any, dict[str, Any]]]]:
    from certiqs_key.solvers.frank_wolfe import certified

    calls: list[tuple[Any, Any, dict[str, Any]]] = []

    def evaluate(maps: Any, points: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append((maps, points, kwargs))
        return companion if kwargs.get("companion") is not None else searched

    monkeypatch.setattr(certified, "evaluate", evaluate)
    result = general_keyrate._certify(
        "searched maps",  # type: ignore[arg-type]
        RUN,  # type: ignore[arg-type]
        reference,
        "acceptance",  # type: ignore[arg-type]
        1.5,
        option=option,
        companion="compiled companion",  # type: ignore[arg-type]
        withheld=(),
        strict_snaps=strict_snaps,
    )
    return result, calls


def test_a_companion_that_certifies_is_the_one_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, calls = _certify(monkeypatch, _evaluation(), _evaluation())
    assert len(calls) == 1
    maps, points, kwargs = calls[0]
    assert maps == "companion maps" and kwargs["companion"] == "compiled companion"
    assert points == [("P", "Q", "fresh", 7)], "the companion's fresh solves"
    assert result.declaration == ON_REFERENCE_COMPANION
    assert result.companion_points is None and not result.fallback


def test_a_companion_that_certifies_nothing_falls_back_to_the_searched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    companion = _evaluation(RANK_NOT_CERTIFIED, seconds=0.25)
    result, calls = _certify(monkeypatch, companion, _evaluation(seconds=0.5))
    assert len(calls) == 2
    first, second = calls
    assert first[0] == "companion maps" and first[2]["companion"] is not None
    assert second[0] == "searched maps" and second[2].get("companion") is None
    assert second[1] == [("P", "Q", "S", 7)], "the search's points and solves"
    assert second[2]["dropped"] == frozenset()
    assert result.declaration == ON_SEARCHED and result.fallback
    assert result.status == "certified" and result.certified_bound == F(1, 2)
    assert result.companion_points == companion.points
    assert result.bracket_withdrawn is None
    assert result.seconds == 0.75


@pytest.mark.parametrize(
    "companion",
    [
        _evaluation(RANK_NOT_CERTIFIED),  # under strict_snaps
        CertifiedEvaluation(
            "on", NOT_CERTIFIED, None, reasons=(NOT_CERTIFIED, CERTIFIER_UNAVAILABLE)
        ),
        CertifiedEvaluation(
            "on",
            "withheld",
            F(1, 2),
            (CertifiedPoint(0, 7, True, F(1), F(-1, 2)),),
            ("receiver_weight_floating_point",),
        ),
    ],
    ids=["strict_snaps", "certifier_unavailable", "withheld"],
)
def test_the_fallback_runs_nowhere_else(
    monkeypatch: pytest.MonkeyPatch, companion: CertifiedEvaluation
) -> None:
    strict = companion.reasons == (NOT_CERTIFIED,)
    result, calls = _certify(
        monkeypatch, companion, _evaluation(), strict_snaps=strict
    )
    assert len(calls) == 1
    assert result.declaration == ON_REFERENCE_COMPANION and not result.fallback


def test_without_a_counted_companion_bracket_the_searched_is_the_one_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, calls = _certify(monkeypatch, _evaluation(), _evaluation(), reference=None)
    assert [call[0] for call in calls] == ["searched maps"]
    assert result.declaration == ON_SEARCHED and not result.fallback
    assert result.companion_points is None


def test_an_inconsistent_companion_withdraws_and_runs_on_the_searched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Item (iv)(c): the cause is named for the caller, under strict_snaps too."""
    companion = _evaluation(FACTOR_ENCLOSURE_INCONSISTENT)
    result, calls = _certify(
        monkeypatch, companion, _evaluation(), strict_snaps=True
    )
    assert [call[0] for call in calls] == ["companion maps", "searched maps"]
    assert result.bracket_withdrawn == FACTOR_ENCLOSURE_INCONSISTENT
    assert result.declaration == ON_SEARCHED and not result.fallback
    assert result.companion_points == companion.points


def test_the_option_off_runs_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    result, calls = _certify(
        monkeypatch, _evaluation(), _evaluation(), option="off"
    )
    assert calls == [] and result is EVALUATION_OFF


def test_the_record_keeps_the_companions_points_only_where_it_ran_twice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fallback, _ = _certify(monkeypatch, _evaluation(RANK_NOT_CERTIFIED), _evaluation())
    record = fallback.as_record(first_order=0.25, first_order_key_length=10)
    assert record["declaration"] == "searched"
    reasons = [p["reasons"] for p in record["companion_points"]]
    assert reasons == [["rank_not_certified"]]
    assert record["certified_minus_first_order"] == 0.25
    plain, _ = _certify(monkeypatch, _evaluation(), _evaluation())
    assert "companion_points" not in plain.as_record(
        first_order=None, first_order_key_length=None
    )


# req:certified-evaluation (vi): the roots of a fallback result


def test_a_fallback_result_names_the_searched_corollary_only() -> None:
    roots = result_claim_roots(
        bound_reported=True,
        dropped=False,
        key_length_reported=True,
        reference=True,
        certified=True,
        fallback=True,
    )
    assert roots == [REFERENCE_ROOT, CERTIFIED_ROOT, KEY_LENGTH_ROOT]
    assert CERTIFIED_REFERENCE_ROOT not in roots
    with pytest.raises(ValueError, match="beside a companion's bound only"):
        result_claim_roots(
            bound_reported=True,
            dropped=False,
            key_length_reported=True,
            certified=True,
            fallback=True,
        )


# The reference corollary's closure reaches the enclosed lemma


def test_the_reference_corollary_reaches_the_enclosed_lemma() -> None:
    """``meat-core/certified-reference-closure``: the closure a run names reaches it.

    Read off the generated table the run names claims from
    (``harness.generate_claim_closure``; its currency is
    ``tests/harness/test_generate_claim_closure.py``'s).
    """
    table = json.loads(
        Path(claim_closure.__file__).with_name("claim_closure.json").read_text(
            encoding="utf-8"
        )
    )
    reached = set(table["roots"][CERTIFIED_REFERENCE_ROOT]["claims"])
    assert "meat-core/frank-wolfe/lem:certified-bracket-enclosed" in reached
    assert "meat-core/cor:reference-companion-factors" in reached
