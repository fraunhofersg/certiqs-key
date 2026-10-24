"""A certified run names its corollary and its report shows h_cert as the key's number.

``foundations/req:tiers``: "the number at that strongest tier is the headline
key rate, and the key length the run reports is formed from it; a number at a
weaker tier is recorded beside it". ``frank-wolfe/req:certified-evaluation``
(vi): where the run is reported at the certified tier its key length is that
of ``cor:certified-keylength``, which the result therefore names among its
claim roots (the manifest names the claim that licenses the number).

A certified qubit-BB84 run (the ``bb84`` report example) must not name only
``thm:firstorder`` and ``cor:keylength-bound``, show no ``h_cert``, describe
``h_lb`` as "The first-order lower bound on h_low that the key length uses",
or let "How the number was computed" read the first-order theorem's "The
headline key rate rests on this bound".
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

pytestmark = [pytest.mark.contract, pytest.mark.requires_qics]
pytest.importorskip("qics")
pytest.importorskip("flint")

#: The opening words of the two claims' readings.
CERTIFIED_READING = "The certified key rate is the best of a few brackets"
FIRST_ORDER_READING = "The headline key rate rests on this bound"


def _example_record(name: str) -> dict[str, Any]:
    """Return the record of one run report example, run afresh."""
    from instances import surface_of
    from runs.report_examples import generate as examples

    from certiqs_key.runs.surface import InstanceIdentity
    from certiqs_key.runs.sweep import sweep
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    example = next(e for e in examples.EXAMPLES if e.name == name)
    surface = surface_of(example.instance)
    identity = InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS))
    with tempfile.TemporaryDirectory() as scratch:
        runner = surface.runner(QicsSectorChoiOracle(), Path(scratch), created_by="t")
        (point,) = sweep(
            example.configs(surface), runner, created_by="t", instance=identity
        )
        found: dict[str, Any] = point.record.as_dict()
        return found


@pytest.fixture(scope="module")
def record() -> dict[str, Any]:
    """Return the record of the ``bb84`` report example: qubit BB84, certified."""
    return _example_record("bb84")


def test_a_certified_run_on_the_reference_companion_names_both_corollaries() -> None:
    """The ``optical_bb84`` example forms its number on the reference companion.

    Its roots are the companion's bound, the certified corollary and the one
    that carries it over to the protocol the companion declares
    (``cor:certified-keylength-reference``), and naming them leaves no
    premise in the closure that the route does not emit.
    """
    from certiqs_key.domain.claim_closure import (
        CERTIFIED_REFERENCE_ROOT,
        CERTIFIED_ROOT,
        KEY_LENGTH_ROOT,
        REFERENCE_ROOT,
    )

    optical = _example_record("optical_bb84")
    key_rate = optical["payload"]["stages"]["key_rate"]
    assert key_rate["reported_tier"] == "certified"
    assert key_rate["claim_roots"] == [
        REFERENCE_ROOT,
        CERTIFIED_ROOT,
        CERTIFIED_REFERENCE_ROOT,
        KEY_LENGTH_ROOT,
    ]
    assert optical["payload"]["assumption_manifest"]["discrepancies"] == []


def test_a_certified_run_names_the_corollary_its_key_length_comes_from(
    record: dict[str, Any],
) -> None:
    from certiqs_key.domain.claim_closure import (
        CERTIFIED_REFERENCE_ROOT,
        CERTIFIED_ROOT,
    )

    key_rate = record["payload"]["stages"]["key_rate"]
    assert key_rate["reported_tier"] == "certified"
    assert CERTIFIED_ROOT in key_rate["claim_roots"]
    # bb84 forms its number on the searched declaration, not on a companion.
    assert CERTIFIED_REFERENCE_ROOT not in key_rate["claim_roots"]
    # Naming it adds no premise the route does not emit.
    assert record["payload"]["assumption_manifest"]["discrepancies"] == []


def test_a_certified_report_shows_h_cert_and_not_h_lb_as_the_key_s_number(
    record: dict[str, Any],
) -> None:
    from certiqs_key.runs.report import build_report

    key_rate = record["payload"]["stages"]["key_rate"]
    h_cert = key_rate["certified"]["certified_bound"]
    report = build_report(record)
    text = json.dumps(report)
    assert repr(h_cert) in text  # the headline number is shown
    assert "that the key length uses" not in text
    rows = {row["name"]: row for row in report["sections"]["numerics"]["explained"]}
    assert rows["h_cert"]["value"] == h_cert
    assert rows["h_cert"]["pointer"] == (
        "/payload/stages/key_rate/certified/certified_bound"
    )
    assert "from which the key length is computed" in rows["h_cert"]["explanation"]
    assert "recorded beside the certified bound" in rows["h_lb"]["explanation"]


def test_how_the_number_was_computed_reads_the_certified_corollary(
    record: dict[str, Any],
) -> None:
    from certiqs_key.runs.report import (
        build_report,
        default_contract_link,
        render_markdown,
    )

    markdown = render_markdown(
        build_report(record), contract_link=default_contract_link()
    )
    appendix = markdown[markdown.index('<a id="how-computed"></a>') :]
    assert CERTIFIED_READING in appendix
    assert FIRST_ORDER_READING not in markdown
    assert "that the key length uses" not in markdown
