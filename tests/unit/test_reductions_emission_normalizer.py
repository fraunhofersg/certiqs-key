"""``def:emitnorm``, the fidelity-first snap: keep, snap for fidelity, last resort.

The normalizer is uncertified: no rung is decided and no class is certified.
``def:emitnorm`` keeps a class already on the lattice (1); snaps every other
class for fidelity (2), rounding to nearest with the off-diagonal entries
softened by ``1 - w`` for ``w = 0, 2^-kappa, ..., 2^-1`` and each component of
the residue placed on its HOST, the first element in the designation order
whose structural support holds it; and, where no ``w`` gives a positive
semidefinite family with every component hosted, takes the flagged last
resort (3). The two TIE tests of the rounding step and the second gate's test are
separate.

EVERY NUMBER BELOW IS DERIVED BY HAND IN THE TEST'S OWN DOCSTRING. Nothing
here is read back from the code it tests.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.exact import (
    Cx,
    conjugate_transpose,
    equal,
    is_positive_semidefinite,
    lattice_round,
    lattice_round_matrix,
    matrix,
    on_lattice,
    zeros,
)
from certiqs_key.reductions.normalizer import (
    ClassStatus,
    EmissionStep,
    JointClass,
    Normalization,
    normalize,
    round_down,
    structural_support,
)

#: One block at one setting with ``q_t = 1``.
SETTINGS = ("t0",)
WEIGHTS = {"t0": F(1)}


def _run(
    letters: tuple[str, ...],
    values: tuple[F, ...],
    kappa: int = 4,
) -> Normalization:
    """Put a family of 1x1 blocks through the normalizer at one setting."""
    names = tuple(letters)
    return normalize(
        {
            (letter, "t0"): (matrix([[value]]),)
            for letter, value in zip(names, values, strict=True)
        },
        classes=(
            JointClass(
                label="t0",
                weight=F(1),
                members=tuple((letter, "t0") for letter in names),
                names=names,
            ),
        ),
        sector_dimensions=[1],
        kappa=kappa,
    )


def _emitted(out: Normalization, letters: tuple[str, ...]) -> list[F]:
    return [out.family[(letter, "t0")][0][0][0].re for letter in letters]


# ---------------------------------------------------------------------------
#  Step (2): the snap for fidelity
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_four_outcome_class_is_rounded_to_nearest_and_hosted() -> None:
    r"""``|Y| = 4``, the largest trace attained TWICE.

    THE FAMILY. Four outcomes on one ``1 x 1`` data sector, ``q_t = 1``,
    ``kappa = 4`` (step ``1/16``), in sixty-fourths: ``A = (21, 21, 13, 9)/64``,
    summing to ``64/64 = 1``; none is on the lattice (``2^4 * 21/64 = 21/4``),
    so the class is NOT KEPT (step (1)) and is MOVED.

    STEP (2) AT ``w = 0`` (a ``1 x 1`` block has no off-diagonal entry): every
    element rounded to nearest -- ``21/64 -> 5/16`` (``5.25 -> 5``),
    ``21/64 -> 5/16``, ``13/64 -> 3/16``, ``9/64 -> 2/16`` -- summing to
    ``15/16``; the residue ``1/16`` sits on index 0, a single component,
    hosted by the first element in the designation order whose structural
    support contains it. The order ranks by exact trace and breaks the tie of
    ``y0`` and ``y1`` by the declared order, so the host is ``y0``: ``3/8``.
    Every element is non-negative, so ``w = 0`` is taken.

    SECOND ROUTE, units of ``2^-6``: ``(21, 21, 13, 9)``; one step is 4 units;
    the nearest multiples are ``20, 20, 12, 8`` (60 units), the residue 4 units
    goes to ``y0``: ``24``. ``Delta_s = 24 - 21 = 3`` units ``= 3/64``.
    """
    letters = ("y0", "y1", "y2", "y3")
    out = _run(letters, (F(21, 64), F(21, 64), F(13, 64), F(9, 64)))
    snap = out.blocks[0].classes["t0"]
    assert snap.status is ClassStatus.MOVED
    assert snap.step is EmissionStep.SNAP_FOR_FIDELITY
    assert snap.mixing_weight == 0
    assert snap.hosts == ("y0",)
    assert not snap.support_not_preserved
    assert _emitted(out, letters) == [F(3, 8), F(5, 16), F(3, 16), F(1, 8)]
    assert out.blocks[0].displacement_squared == F(3, 64) ** 2
    assert out.moved == ((0, snap),)


@pytest.mark.contract
def test_the_declared_order_and_not_the_dict_order_breaks_the_host_tie() -> None:
    """RELABELLING ``Y`` MOVES THE HOST, and that is the rule working.

    ``def:emitnorm``: the designation order breaks a tie of exact traces by the
    declared order of the class, "so the order is a function of the
    declaration and of nothing else". The family of the first test with the
    two tied letters exchanged in the declared order hosts the residue on the
    one that now comes first.
    """
    values = (F(21, 64), F(21, 64), F(13, 64), F(9, 64))
    out = _run(("yA", "yB", "yC", "yD"), values)
    assert out.blocks[0].classes["t0"].hosts == ("yA",)
    swapped = _run(("yB", "yA", "yC", "yD"), values)
    assert swapped.blocks[0].classes["t0"].hosts == ("yB",)


@pytest.mark.contract
def test_a_residue_is_hosted_only_where_the_support_holds_it() -> None:
    r"""Step (2): the host's structural support in the handed datum holds it.

    THE FAMILY, ``kappa = 2`` (step ``1/4``), ``q_t = 1``, four diagonal
    ``2 x 2`` elements: ``a = b = c = diag(1/3, 0)`` and ``d = diag(0, 1)``.
    Rounded to nearest: ``4/3 = 1.33 -> 1``, so ``a, b, c -> diag(1/4, 0)``;
    ``d`` is on the lattice. The residue ``1 - sum = diag(1/4, 0)`` is one
    component ``{0}``. In the designation order ``d`` comes first (trace 1),
    but index 0 lies outside its structural support ``{1}``; among ``a, b, c``
    (traces tied, declared order) the host is ``a``: ``diag(1/2, 0)``. Every
    element is positive semidefinite, so ``w = 0`` is taken.
    ``Delta_s = 1/2 - 1/3 = 1/6``.
    """
    letters = ("a", "b", "c", "d")
    third = matrix([[F(1, 3), 0], [0, 0]])
    blocks = {"a": third, "b": third, "c": third, "d": matrix([[0, 0], [0, 1]])}
    out = normalize(
        {(name, "t0"): (blocks[name],) for name in letters},
        classes=(JointClass("t0", F(1), tuple((n, "t0") for n in letters), letters),),
        sector_dimensions=[2],
        kappa=2,
    )
    snap = out.blocks[0].classes["t0"]
    assert snap.step is EmissionStep.SNAP_FOR_FIDELITY
    assert snap.hosts == ("a",)
    expected = {
        "a": matrix([[F(1, 2), 0], [0, 0]]),
        "b": matrix([[F(1, 4), 0], [0, 0]]),
        "c": matrix([[F(1, 4), 0], [0, 0]]),
        "d": matrix([[0, 0], [0, 1]]),
    }
    for name in letters:
        emitted = out.family[(name, "t0")][0]
        assert equal(emitted, expected[name]), name
        assert structural_support(emitted) <= structural_support(blocks[name])
    assert out.blocks[0].displacement_squared == F(1, 6) ** 2


@pytest.mark.contract
def test_the_off_diagonal_entries_soften_until_the_family_is_positive() -> None:
    r"""Step (2) at ``w = 1/2``: the mixture with the diagonal parts.

    THE FAMILY, ``3 x 3``, ``kappa = 4``, ``q_t = 1``: two rank-one elements
    coupling indices 0 and 1, ``P = [[1/32, 1/16], [1/16, 1/8]]`` and
    ``E = [[1/16, -1/16], [-1/16, 1/16]]``, their mirrors coupling 1 and 2,
    ``Q`` and ``G``, and three diagonal rank-one completions
    ``D0 = diag(29/32, 0, 0)``, ``D1 = diag(0, 5/8, 0)``,
    ``D2 = diag(0, 0, 29/32)``.

    BY HAND. ``P``'s ``(0, 0)`` entry ``1/32`` rounds to ``0`` (``0.5``, a
    tie, to the even ``0``) whatever ``w``, so ``P`` is positive only once its
    off-diagonal entry rounds to ``0``: ``16 (1/16)(1 - w) = 1 - w`` rounds
    to ``1`` at ``w = 0, 1/16, 1/8, 1/4`` and to ``0`` (a tie) at ``w = 1/2``;
    likewise ``Q``. At ``w = 1/2``, ``E`` and ``G`` lose their off-diagonal
    entries too (``-0.5 -> 0``): every element is diagonal, ``P = diag(0, 1/8,
    0)``, ``E = diag(1/16, 1/16, 0)``, ``Q = diag(0, 1/8, 0)``, ``G = diag(0,
    1/16, 1/16)``, ``D0 = 14/16`` (``14.5 -> 14``), ``D1 = 10/16``, ``D2 =
    14/16``. The residue ``diag(1/16, 0, 1/16)`` has the components ``{0}``
    and ``{2}``; in the designation order ``D0, D2, D1, P, Q, E, G`` (traces
    ``29/32`` tied, ``5/8``, ``5/32`` tied, ``1/8`` tied) they are hosted by
    ``D0`` and ``D2``: ``15/16`` each. Every element is positive and on the
    lattice, and no zero row or column is revived. ``Delta_s = 1/16`` (the
    off-diagonal entries of ``P``, ``Q``, ``E`` and ``G``).
    """
    p, r, e, s = F(1, 32), F(1, 8), F(1, 16), F(1, 16)
    blocks = {
        "P": matrix([[p, s, 0], [s, r, 0], [0, 0, 0]]),
        "E": matrix([[e, -s, 0], [-s, e, 0], [0, 0, 0]]),
        "Q": matrix([[0, 0, 0], [0, r, s], [0, s, p]]),
        "G": matrix([[0, 0, 0], [0, e, -s], [0, -s, e]]),
        "D0": matrix([[F(29, 32), 0, 0], [0, 0, 0], [0, 0, 0]]),
        "D1": matrix([[0, 0, 0], [0, F(5, 8), 0], [0, 0, 0]]),
        "D2": matrix([[0, 0, 0], [0, 0, 0], [0, 0, F(29, 32)]]),
    }
    names = tuple(blocks)
    out = normalize(
        {(name, "t0"): (blocks[name],) for name in names},
        classes=(JointClass("t0", F(1), tuple((n, "t0") for n in names), names),),
        sector_dimensions=[3],
        kappa=4,
    )
    snap = out.blocks[0].classes["t0"]
    assert snap.status is ClassStatus.MOVED
    assert snap.step is EmissionStep.SNAP_FOR_FIDELITY
    assert snap.mixing_weight == F(1, 2)
    assert snap.hosts == ("D0", "D2")
    expected = {
        "P": matrix([[0, 0, 0], [0, r, 0], [0, 0, 0]]),
        "E": matrix([[e, 0, 0], [0, e, 0], [0, 0, 0]]),
        "Q": matrix([[0, 0, 0], [0, r, 0], [0, 0, 0]]),
        "G": matrix([[0, 0, 0], [0, e, 0], [0, 0, e]]),
        "D0": matrix([[F(15, 16), 0, 0], [0, 0, 0], [0, 0, 0]]),
        "D1": matrix([[0, 0, 0], [0, F(5, 8), 0], [0, 0, 0]]),
        "D2": matrix([[0, 0, 0], [0, 0, 0], [0, 0, F(15, 16)]]),
    }
    for name in names:
        emitted = out.family[(name, "t0")][0]
        assert equal(emitted, expected[name]), name
        assert structural_support(emitted) <= structural_support(blocks[name])
    assert out.blocks[0].displacement_squared == F(1, 16) ** 2


# ---------------------------------------------------------------------------
#  Step (3): the flagged last resort
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_class_no_weight_makes_positive_takes_the_flagged_last_resort() -> None:
    r"""Step (3): no ``w`` of (2) gives a positive family.

    THE FAMILY, ``2 x 2``, ``kappa = 4``, ``q_t = 1``: ``P = [[1/33, 1/9],
    [1/9, 1/2]]`` (``det = 1/66 - 1/81 > 0``) and ``B = 1 - P``
    (``det = 16/33 - 1/81 > 0``).

    STEP (2) FAILS AT EVERY ``w``. ``P``'s ``(0, 0)`` entry ``16/33 = 0.48``
    rounds to ``0``, and its off-diagonal entry ``(16/9)(1 - w)`` rounds to
    ``2, 2, 2, 1, 1`` at ``w = 0, 1/16, 1/8, 1/4, 1/2`` -- never ``0`` -- so the
    rounded ``P`` has a zero diagonal beside a non-zero off-diagonal and is
    never positive. ``B``'s entries round to the complements (``512/33 =
    15.5 -> 16``; odd symmetry for the off-diagonal), so the residue is ``0``,
    there is no component, and nothing can lift ``P``.

    STEP (3). ``B^w = (1 - w) A + w (1/2) 1`` over the ``n = 2`` elements; the
    designation order is ``B`` (trace ``1.47``) then ``P``, so ``B`` takes the
    complement. At the first weight ``w = 1/16``: ``P^w_00 = (15/16)(1/33) +
    1/32 = 0.0597``, ``16 x = 0.955 -> 1``; ``P^w_01 = (15/16)(1/9) = 0.104``,
    ``16 x = 1.67 -> 2``; ``P^w_11 = 1/2``. So ``P' = [[1/16, 1/8], [1/8, 1/2]]``
    (``det = 1/32 - 1/64 > 0``) and ``B' = [[15/16, -1/8], [-1/8, 1/2]]``
    (``det = 15/32 - 1/64 > 0``): positive, so ``w = 1/16`` is taken, and the
    class is flagged ``support_not_preserved``. Every component had a host
    (there was none), so the cause is positivity, not a component without a
    host.
    """
    letters = ("P", "B")
    p = matrix([[F(1, 33), F(1, 9)], [F(1, 9), F(1, 2)]])
    b = matrix([[F(32, 33), F(-1, 9)], [F(-1, 9), F(1, 2)]])
    out = normalize(
        {("P", "t0"): (p,), ("B", "t0"): (b,)},
        classes=(JointClass("t0", F(1), (("P", "t0"), ("B", "t0")), letters),),
        sector_dimensions=[2],
        kappa=4,
    )
    snap = out.blocks[0].classes["t0"]
    assert snap.status is ClassStatus.MOVED
    assert snap.step is EmissionStep.LAST_RESORT
    assert snap.support_not_preserved
    assert not snap.component_without_host
    assert snap.mixing_weight == F(1, 16) and not snap.mixing_fallback
    assert snap.uniform_share == F(1, 2)
    assert snap.hosts == ("B",)
    assert equal(
        out.family[("P", "t0")][0], matrix([[F(1, 16), F(1, 8)], [F(1, 8), F(1, 2)]])
    )
    assert equal(
        out.family[("B", "t0")][0],
        matrix([[F(15, 16), F(-1, 8)], [F(-1, 8), F(1, 2)]]),
    )
    for name in letters:
        emitted = out.family[(name, "t0")][0]
        assert is_positive_semidefinite(emitted) and on_lattice(emitted, 4)


@pytest.mark.contract
def test_the_fall_back_reads_the_round_down_candidates() -> None:
    """Step (3)'s fall-back: the first candidate between ``0`` and the element.

    ``diag(5/32, 0)`` at ``kappa = 4``: the element itself is off the lattice;
    the shift by ``2^-4``, ``diag(3/32, -2/32)``, rounds to ``diag(1/8,
    -1/16)``, not positive; the scaling ``(15/16) diag(5/32, 0) =
    diag(75/512, 0)`` rounds to ``diag(1/8, 0)`` (``2.34 -> 2``), between
    ``0`` and the element: the fall-back takes it. A zero element comes back
    zero.
    """
    assert equal(
        round_down(matrix([[F(5, 32), 0], [0, 0]]), 4),
        matrix([[F(1, 8), 0], [0, 0]]),
    )
    assert equal(round_down(zeros(2), 4), zeros(2))


# ---------------------------------------------------------------------------
#  Step (1) and the sector support
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_class_on_the_lattice_is_kept() -> None:
    """Step (1): ``A' = A`` and ``Delta_s = 0``.

    ``(1/2, 1/4, 1/4)`` at ``kappa = 4`` is on the lattice (``8/16, 4/16,
    4/16``), so "no further step acts on it" (``def:emitnorm``, first
    property).
    """
    letters = ("y0", "y1", "y2")
    out = _run(letters, (F(1, 2), F(1, 4), F(1, 4)))
    snap = out.blocks[0].classes["t0"]
    assert snap.status is ClassStatus.KEPT
    assert snap.step is None
    assert out.blocks[0].already_on_lattice
    assert out.blocks[0].moved == ()
    assert out.blocks[0].displacement_squared == 0
    assert _emitted(out, letters) == [F(1, 2), F(1, 4), F(1, 4)]


@pytest.mark.contract
def test_an_element_outside_the_sector_support_is_touched_by_no_step() -> None:
    """``def:emitnorm``: the steps act on ``V_t n V^(s)`` and on nothing else.

    One data sector, class ``t`` with ``q_t = 1``, three outcomes; ``a`` is
    outside the declared support (exactly zero), ``b = 21/64`` and
    ``c = 43/64`` inside, at ``kappa = 4``. Rounded to nearest,
    ``b -> 5/16`` (``5.25 -> 5``) and ``c -> 11/16`` (``10.75 -> 11``),
    summing to ``1``: no residue, the class is moved at ``w = 0``, and ``a``
    comes back EXACTLY ZERO.
    """
    order = [("a", "t"), ("b", "t"), ("c", "t")]
    data = {
        ("a", "t"): (zeros(1),),
        ("b", "t"): (matrix([[F(21, 64)]]),),
        ("c", "t"): (matrix([[F(43, 64)]]),),
    }
    out = normalize(
        data,
        classes=(JointClass("t", F(1), tuple(order), ("a", "b", "c")),),
        sector_dimensions=[1],
        kappa=4,
        supports=[frozenset({("b", "t"), ("c", "t")})],
    )
    snap = out.blocks[0].classes["t"]
    assert snap.status is ClassStatus.MOVED
    assert snap.hosts == ()
    assert out.family[("a", "t")][0] == zeros(1)
    assert out.family[("b", "t")][0] == matrix([[F(5, 16)]])
    assert out.family[("c", "t")][0] == matrix([[F(11, 16)]])


@pytest.mark.contract
def test_an_incomplete_class_is_passed_through_and_never_repaired() -> None:
    """A handed class outside ``D_adm`` reaches step (4) untouched.

    Three zero elements are positive and on the lattice, so the class is
    KEPT -- and its sum ``0`` is not ``q_t 1``. The normalizer repairs nothing
    it was handed (``def:emitnorm``, fourth property); the six-condition row
    is the defensive check that refuses it (``thm:emit`` (ii)). A class that
    is not even positive semidefinite is recorded ``not_admissible`` and
    passed through the same way.
    """
    letters = ("y0", "y1", "y2")
    out = _run(letters, (F(0), F(0), F(0)))
    assert out.blocks[0].classes["t0"].status is ClassStatus.KEPT
    assert _emitted(out, letters) == [F(0), F(0), F(0)]
    negative = _run(("y0", "y1"), (F(-1, 64), F(65, 64)))
    assert negative.blocks[0].classes["t0"].status is ClassStatus.NOT_ADMISSIBLE
    assert _emitted(negative, ("y0", "y1")) == [F(-1, 64), F(65, 64)]


# ---------------------------------------------------------------------------
#  Rounding inside every candidate: TIES TO EVEN, and its odd symmetry
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_an_exact_tie_rounds_to_the_even_numerator_in_both_directions() -> None:
    """``def:emitnorm`` (2) at ``kappa = 4``, on the two smallest exact ties.

    A tie is an exact equality here and not a floating-point near-miss: the
    step runs on rationals, so ``x`` ties exactly when ``2^4 x`` is a half
    integer.

    ``1/32``: ``2^4 / 32 = 1/2``. The two nearest multiples are ``0`` and
    ``1/16``, with integer numerators ``0`` and ``1``; the EVEN one is ``0``,
    so ``1/32 -> 0`` -- **DOWN**.

    ``3/32``: ``2^4 * 3/32 = 3/2``. The nearest are ``1/16`` and ``2/16`` with
    numerators ``1`` and ``2``; the even one is ``2``, so ``3/32 -> 1/8`` --
    **UP**.

    THAT THE SAME RULE ROUNDS ONE TIE DOWN AND THE NEXT UP IS THE WHOLE
    DISCRIMINATOR: half-away-from-zero would round both up, and ties-toward-
    ``+infinity`` would round both up as well. Any rule that agrees with
    half-to-even on both of these agrees with it on every tie at this
    ``kappa``, the numerators alternating.

    SECOND ROUTE, in integer units of ``2^-5``: the family is ``1`` and ``3``
    units with a lattice step of ``2`` units, so each sits exactly one unit
    from each of two multiples; ``1`` is between ``0`` and ``2`` and ``3`` is
    between ``2`` and ``4``; the even-numerator multiples are ``0/16`` and
    ``2/16``. The two routes agree.
    """
    assert lattice_round(F(1, 32), 4) == F(0)
    assert lattice_round(F(3, 32), 4) == F(1, 8)
    assert lattice_round(F(5, 32), 4) == F(1, 8)
    assert lattice_round(F(7, 32), 4) == F(1, 4)
    # A NON-TIE IS UNTOUCHED BY THE RULE, which is what makes the rule about
    # ties only: 7/64 has fractional part 3/4 of a step and goes UP.
    assert lattice_round(F(7, 64), 4) == F(1, 8)
    assert lattice_round(F(29, 128), 4) == F(1, 4)


@pytest.mark.contract
def test_ties_to_even_is_odd_symmetric_and_a_hermitian_block_stays_hermitian() -> None:
    """The property ``def:emitnorm`` (2) gives as its REASON for the rule.

    "Negating a part negates both of the multiples nearest it and negates
    their numerators, WHICH PRESERVES EVENNESS, so the rounded value of a
    negated part is the negative of the rounded value of the part. THE STEP
    THEREFORE COMMUTES WITH ``A -> A-dagger`` ... AND A HERMITIAN BLOCK COMES
    OUT HERMITIAN. **THAT IS WHAT LICENSES THE ORDER OF THE STEPS**: step (1)
    is not re-run after step (2)."

    So this test is not decoration: if it failed, the IMPLEMENTATION'S STEP
    ORDER would be wrong, not just one entry.

    The block is Hermitian with both parts of its off-diagonal entry sitting on
    exact ties: ``A_01 = 1/32 + (3/32) i`` and ``A_10 = 1/32 - (3/32) i``. Each
    part rounds by the rule above -- ``1/32 -> 0`` and ``3/32 -> 1/8`` -- and
    the mirror parts round to the negatives of those, so the rounded block is
    ``[[1/2, i/8], [-i/8, 1/2]]`` and is Hermitian entry for entry.

    A TIE RULE THAT IS NOT ODD-SYMMETRIC WOULD BREAK THIS, and the contract
    names the one it has in mind: under ties toward ``+infinity``,
    ``+3/32 -> 1/8`` while ``-3/32 -> -1/16``, so the two mirror imaginary
    parts would no longer be opposite.
    """
    block = matrix(
        [
            [F(1, 2), Cx(F(1, 32), F(3, 32))],
            [Cx(F(1, 32), F(-3, 32)), F(1, 2)],
        ]
    )
    assert equal(block, conjugate_transpose(block))
    rounded = lattice_round_matrix(block, 4)
    # THE STEP COMMUTES WITH THE ADJOINT, which is the property itself.
    assert equal(rounded, conjugate_transpose(rounded))
    assert equal(
        lattice_round_matrix(conjugate_transpose(block), 4),
        conjugate_transpose(rounded),
    )
    assert rounded[0][1].re == F(0)
    assert rounded[0][1].im == F(1, 8)
    assert rounded[1][0].im == F(-1, 8)
    # ODD SYMMETRY, stated as the identity the argument uses.
    for value in (F(1, 32), F(3, 32), F(5, 32), F(7, 32), F(21, 64)):
        assert lattice_round(-value, 4) == -lattice_round(value, 4)


# ---------------------------------------------------------------------------
#  Step (4): the second gate
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_second_gate_decides_the_scalar_sectors_too() -> None:
    """thm:emit (ii): all six, on the family presented as the sector list.

    A scalar sector whose declared values do not sum to one exactly makes the
    emitted family a non-POVM. The row must refuse it, naming the predicate,
    exactly as it does for a data sector -- and a consumer re-deciding the six
    on the emitted family would otherwise not reach the producer's answer.
    """
    from certiqs_key.reductions.sectors import (
        Sector,
        SectorKind,
        SectorSet,
        assemble_sector_blocks,
    )
    from certiqs_key.reductions.validation import rule_emitted_family

    order = [("a", "t"), ("b", "t")]
    sectors = SectorSet(
        (
            Sector(label=("C", "0"), dimension=1, kind=SectorKind.DATA),
            Sector(label=("C", "a,t"), dimension=1, kind=SectorKind.SCALAR),
            Sector(label=("C", "b,t"), dimension=1, kind=SectorKind.SCALAR),
        )
    )
    data = {("a", "t"): (matrix([[F(1)]]),), ("b", "t"): (matrix([[F(0)]]),)}
    good = {
        ("C", "a,t"): {("a", "t"): F(1), ("b", "t"): F(0)},
        ("C", "b,t"): {("a", "t"): F(0), ("b", "t"): F(1)},
    }
    assert (
        rule_emitted_family(
            assemble_sector_blocks(sectors, data, good, order),
            order,
            sectors.dimensions,
            lattice_exponent=40,
            sector_map_agrees=True,
        )
        is None
    )

    bad = {  # sum_v phi = 3/4 on the first scalar sector, not 1
        ("C", "a,t"): {("a", "t"): F(1, 2), ("b", "t"): F(1, 4)},
        ("C", "b,t"): {("a", "t"): F(0), ("b", "t"): F(1)},
    }
    refusal = rule_emitted_family(
        assemble_sector_blocks(sectors, data, bad, order),
        order,
        sectors.dimensions,
        lattice_exponent=40,
        sector_map_agrees=True,
    )
    assert refusal is not None
    assert str(refusal.reason) == "emitted_family_not_admissible"
    assert "identity" in refusal.detail
    # A scalar value off the declared lattice is refused by the same row.
    off_lattice = {
        ("C", "a,t"): {("a", "t"): F(1, 3), ("b", "t"): F(2, 3)},
        ("C", "b,t"): {("a", "t"): F(0), ("b", "t"): F(1)},
    }
    lattice_refusal = rule_emitted_family(
        assemble_sector_blocks(sectors, data, off_lattice, order),
        order,
        sectors.dimensions,
        lattice_exponent=40,
        sector_map_agrees=True,
    )
    assert lattice_refusal is not None
    assert "eq:latinv" in lattice_refusal.detail
