"""Exact source admission and independently evaluated enclosure boundaries.

The preparation is the library's (:mod:`instances.common.wcp`) in decoy BB84's
shape (``tests/support/lowered_templates.py``, ``wcp_source``): the Python
decoy instance's ``prepare_source``.
"""

from decimal import Decimal, localcontext
from fractions import Fraction as F

import pytest
from tests.support.lowered_templates import wcp_source as prepare_source

from certiqs_key.transmitter.decoy import emit_decoy_declaration, poisson_enclosures


@pytest.mark.parametrize("mu", [F(0), F(1, 100), F(1, 2), F(4, 5), F(3)])
def test_poisson_enclosure_against_high_precision(mu: F):
    with localcontext() as ctx:
        ctx.prec = 110
        value = Decimal(mu.numerator) / Decimal(mu.denominator)
        poisson = (-value).exp()
        for n, enclosure in enumerate(poisson_enclosures(mu, 8).enclosures):
            if n:
                poisson *= value / n
            lo = Decimal(enclosure.lower.numerator) / Decimal(
                enclosure.lower.denominator
            )
            hi = Decimal(enclosure.upper.numerator) / Decimal(
                enclosure.upper.denominator
            )
            assert lo <= poisson <= hi


@pytest.mark.parametrize("entropy_cutoff", [0, 1, 2])
def test_ordinary_inputs_emit_without_formed_entry_rounding(entropy_cutoff: int):
    source = prepare_source(
        intensities={"signal": 0.8, "weak": F(1, 5), "vacuum": 0},
        test_intensity_probabilities=[0.1, 0.3, 0.6],
        gamma=0.1,
        entropy_cutoff=entropy_cutoff,
    )
    emitted = emit_decoy_declaration(source.tagged).require()
    assert emitted.presentation is not None
    model = source.tagged.model
    assert len(model.alphabet) == 14
    assert sum(model.weights.values()) == 1
    assert model.weights["gen-signal-H"] == model.weights["gen-signal-V"]
    for name in model.intensities:
        assert (
            len({model.weights[f"test-{name}-{pol}"] for pol in model.polarisations})
            == 1
        )
    for (n, name), weight in source.tagged.sector_weights.items():
        table = poisson_enclosures(model.intensities[name], source.tagged.source_cutoff)
        assert 0 <= weight <= table.enclosures[n].lower
    assert source.record["categories"]["total_displacement"]


def test_vacuum_has_no_tail_and_all_labels_share_one_sector():
    source = prepare_source(
        intensities={"signal": 0}, test_intensity_probabilities=[1], gamma=F(1, 2)
    )
    declaration = emit_decoy_declaration(source.tagged).require()
    assert declaration.presentation.virtual_sectors.dims == (1,)
    assert source.tagged.sector_weights[0, "signal"] == 1


def test_tiny_positive_category_refuses_instead_of_losing_support():
    with pytest.raises(ValueError, match="support"):
        prepare_source(
            intensities={"signal": 0.5},
            test_intensity_probabilities=[1],
            gamma=F(1, 1 << 40),
        )


def test_fraction_normalization_error_cannot_borrow_float_allowance():
    with pytest.raises(ValueError, match="normalization"):
        prepare_source(
            intensities={"signal": 0.5, "weak": 0.1},
            test_intensity_probabilities=[F(1, 3), F(1, 2)],
            gamma=F(1, 2),
            tolerance=0.0,
        )
