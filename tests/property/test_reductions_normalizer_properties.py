"""Properties of the emission normalizer, ``def:emitnorm``, on random data.

The properties ``def:emitnorm`` states of its output, each decided exactly on
families hypothesis draws -- Hermitian, positive semidefinite and complete at
a class weight, with Gaussian-rational entries, off the lattice in general:

* the declared datum is on the lattice, Hermitian, positive semidefinite and
  CLASS COMPLETE, so the six-condition row never refuses it -- the decision
  of step (4) is a defensive check (``thm:emit`` (ii), proof);
* FIFTH PROPERTY: outside the last resort (3), no element gains a row or
  column the handed element does not hold (structural support);
* a class on the lattice is kept unchanged; a moved class names the step
  that snapped it, and the weight of (2) is ``0`` or a weight of the ladder.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from certiqs_key.foundations.exact import (
    Matrix,
    add,
    equal,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    matrix,
    on_lattice,
    scale,
    subtract,
    zeros,
)
from certiqs_key.reductions.normalizer import (
    ClassStatus,
    EmissionStep,
    JointClass,
    normalize,
    structural_support,
)
from certiqs_key.reductions.validation import rule_emitted_family

Q_WEIGHT = Fraction(1)


@st.composite
def _psd_block(draw: st.DrawFn, dim: int) -> Matrix:
    """Draw a real symmetric positive semidefinite block with small entries."""
    if dim == 1:
        return matrix(
            [[draw(st.fractions(min_value=0, max_value=1, max_denominator=97))]]
        )
    a = draw(st.fractions(min_value=0, max_value=1, max_denominator=97))
    c = draw(st.fractions(min_value=0, max_value=1, max_denominator=97))
    t = draw(st.fractions(min_value=-1, max_value=1, max_denominator=13))
    b = t * min(a, c)
    return matrix([[a, b], [b, c]])


@st.composite
def _class(draw: st.DrawFn) -> tuple[int, tuple[Matrix, ...]]:
    """Draw a complete class: ``k - 1`` small drawn elements and the rest."""
    dim = draw(st.sampled_from((1, 2)))
    count = draw(st.integers(min_value=2, max_value=4))
    drawn = [
        scale(Fraction(1, 2 * count), draw(_psd_block(dim))) for _ in range(count - 1)
    ]
    total = zeros(dim)
    for element in drawn:
        total = add(total, element)
    last = subtract(scale(Q_WEIGHT, identity(dim)), total)
    return dim, (*drawn, last)


@pytest.mark.contract
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    data=_class(),
    kappa=st.integers(min_value=2, max_value=10),
)
def test_the_declared_datum_has_the_six_properties(
    data: tuple[int, tuple[Matrix, ...]], kappa: int
) -> None:
    """``def:emitnorm``'s properties on a random complete class."""
    dim, family = data
    names = tuple(f"y{index}" for index in range(len(family)))
    members = tuple((name, "t") for name in names)
    out = normalize(
        {member: (element,) for member, element in zip(members, family, strict=True)},
        classes=(JointClass("t", Q_WEIGHT, members, names),),
        sector_dimensions=[dim],
        kappa=kappa,
    )
    snap = out.blocks[0].classes["t"]
    emitted = [out.family[member][0] for member in members]

    # On the lattice, Hermitian, positive, complete: the second gate passes.
    total = zeros(dim)
    for element in emitted:
        assert is_hermitian(element)
        assert is_positive_semidefinite(element)
        assert on_lattice(element, kappa)
        total = add(total, element)
    assert equal(total, scale(Q_WEIGHT, identity(dim)))
    assert (
        rule_emitted_family(
            dict(out.family),
            members,
            (dim,),
            lattice_exponent=kappa,
            sector_map_agrees=True,
        )
        is None
    )

    if snap.status is ClassStatus.KEPT:
        assert all(equal(a, b) for a, b in zip(family, emitted, strict=True))
        assert snap.step is None
    else:
        assert snap.status is ClassStatus.MOVED
        ladder = {Fraction(1, 1 << level) for level in range(1, kappa + 1)}
        if snap.step is EmissionStep.SNAP_FOR_FIDELITY:
            assert snap.mixing_weight in {Fraction(0), *ladder}
        else:
            assert snap.step is EmissionStep.LAST_RESORT
            assert snap.mixing_fallback or snap.mixing_weight in ladder

    # Fifth property: no zero row or column revived, save the last resort.
    if snap.step is not EmissionStep.LAST_RESORT:
        for handed, declared in zip(family, emitted, strict=True):
            assert structural_support(declared) <= structural_support(handed)
    else:
        assert snap.support_not_preserved
