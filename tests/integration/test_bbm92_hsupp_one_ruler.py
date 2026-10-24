"""BBM92 at photon cutoff 2 and 3 with ``key_bases = ZX`` reaches first order.

The regression of the one-ruler rule of ``frank-wolfe/rem:fo-one-ruler``. Without it
every such run ended at iteration 1 with ``solver_status: hypothesis-withdrawn``,
``assurance_reason: gradient_hypothesis_support`` and no ``h_lb``, whatever the dark
count: the reference ``dim W`` was read at 1e-12 on the Kraus stack's singular values
and counted snapped directions near 3e-11 relative that a rank of the branch operator
counts only at an input with a condition number above ``support_cutoff / (3e-11)^2``,
about 1e9. Read at ``sqrt(support_cutoff)``, the comparison passes at the iterates and
the rung is reached.

Three Frank-Wolfe iterations each: what is asserted is that the hypothesis is
not withdrawn, that the record carries the band count and that the number is
certified on the reference companion with no premise at the snap, not a
converged number. The cutoff-3 runs take longer and are marked ``slow``.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import jsonschema
import pytest

from certiqs_key.runs.config import SolverSettings
from certiqs_key.runs.pipeline import SliceResult
from certiqs_key.runs.record import record_run

pytestmark = pytest.mark.requires_qics

SCHEMA = json.loads(
    (
        Path(__file__).resolve().parents[2]
        / "src/certiqs_key/runs/record.schema.json"
    ).read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    ("cutoff", "window", "dark"),
    [
        pytest.param(2, 5, Fraction(0), id="N2-dark0"),
        pytest.param(2, 5, Fraction(1, 1_000_000), id="N2-dark1e-6"),
        pytest.param(3, 4, Fraction(0), id="N3-dark0", marks=pytest.mark.slow),
        pytest.param(
            3, 4, Fraction(1, 1_000_000), id="N3-dark1e-6", marks=pytest.mark.slow
        ),
    ],
)
def test_bbm92_zx_above_cutoff_one_reaches_first_order(
    cutoff: int,
    window: int,
    dark: Fraction,
    tmp_path: Path,
) -> None:
    from instances.bbm92.surface import default_config, runner

    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    device = dict(default_config().device)
    for station in ("alice", "bob"):
        device[f"{station}_photon_cutoff"] = cutoff
        device[f"{station}_exact_window"] = window
        device[f"{station}_dark_count"] = dict.fromkeys(("H", "V", "D", "A"), dark)
    device["key_bases"] = "ZX"
    config = default_config(
        device=device, solver=SolverSettings(method="fw", max_iterations=3)
    )
    outcome = runner(QicsSectorChoiOracle(), tmp_path, created_by="one-ruler")(
        config, 0
    )
    assert isinstance(outcome, SliceResult), outcome
    rate = outcome.key_rate
    certificate = rate.certificate
    assert certificate["solver_status"] != "hypothesis-withdrawn"
    assert certificate["assurance_reason"] == "first_order_reported"
    assert rate.h_lb is not None
    # THE TIER. Both stations' blocks are known through enclosures here, and for several
    # replaced factors (meat-core/prop:reference-companion,
    # frank-wolfe/lem:certified-bracket-enclosed) the certifier reads both. The number
    # is certified on the companion, with and without dark counts. With them every
    # block of a station at the vacuum is a non-zero 1 x 1 scalar, so elements of a
    # pass class share one boxed block of the other station; their rows are grouped by
    # the tuple of their boxed blocks (lem:certified-bracket-enclosed (b), the stack;
    # req:certified-evaluation (iii)(a)), the exact dependence between their exact
    # factors is reduced exactly, and the floor of N is certified. A grouping per
    # element leaves C with dependent rows here, and the floor of N fails.
    assert str(rate.reported_tier) == "certified"
    assert rate.certified is not None
    assert rate.certified["declaration"] == "reference_companion"
    assert not rate.certified.get("companion_points")
    # On the companion the bracket is formed through elements of two boxed blocks in
    # key-live classes: its value stays at the first-order number's (measured -6.2e-6
    # at N = 2 and -2.5e-5 at N = 3 without dark counts, +3.5e-7 and -2.6e-7 with).
    gap = rate.certified["certified_minus_first_order"]
    assert gap is not None and abs(gap) <= 1e-4 * max(1.0, abs(rate.h_lb))

    # THE RECORD SAYS WHERE THE ONE RULER SET A DIRECTION ASIDE: per key-active
    # pair, the directions between the two windows.
    band = rate.map_validation_report["hsupp_reference_band"]
    assert band["factor_support_cutoff"] ** 2 == pytest.approx(
        band["support_cutoff"]
    )
    counts = [n for pairs in band["pairs"].values() for n in pairs.values()]
    assert counts and all(isinstance(n, int) and n >= 0 for n in counts)
    # Directions are counted only where the emission keeps every class. At
    # dark 0 every class of the handed datum is on the lattice and KEPT
    # (reductions/def:emitnorm (1)), the emission is the handed datum, and the
    # band counts directions. At dark 1e-6 the classes are off the lattice and
    # the normalizer rounds each element DOWN to a lattice matrix between 0 and
    # the element (def:emitnorm (3)), absorbing the residue into the designated
    # positive-definite element; it adds no near-singular direction, and the
    # band is empty (measured: every pair 0).
    # The regression this file pins -- the hypothesis is not withdrawn and
    # first order is reached -- is asserted above for both.
    if dark == 0:
        assert sum(counts) > 0

    document = record_run(outcome, config, created_by="one-ruler").as_dict()
    jsonschema.validate(document, SCHEMA)
    recorded = document["payload"]["stages"]["key_rate"]["map_validation_report"]
    assert recorded["hsupp_reference_band"] == band
    # A number formed on the companion rests on no premise at the snap (one formed
    # in the fallback would rest on A-SNAP for the blocks the companion carried).
    premises = document["payload"]["stages"]["key_rate"]["certified"]["premises"]
    assert premises == []
