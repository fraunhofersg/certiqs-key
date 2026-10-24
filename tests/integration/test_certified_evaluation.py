"""The certified evaluation of the first-order bound, on the golden toys.

``meat-core/frank-wolfe/req:certified-evaluation``, by
``lem:certified-bracket``, ``lem:certified-bracket-enclosed`` and
``cor:certified-keylength``. CONTRACT TESTS,
each failing where its clause were broken:

* SOUNDNESS against the FROZEN hand-derived ``h_low`` of
  ``tests/oracles/registry.py`` (the entries ``test_verified_bracket_against_
  registry.py`` reads): every certified bracket lies at or below it, with no
  margin but the registry value's own binary64 rounding -- the first-order
  bracket needs ``1e-13`` there, for the unbudgeted arithmetic the certified
  one encloses;
* CONSISTENCY: the engine's binary64 gradient lies
  within ``1e-9`` of the largest entry, plus the radius, of the certified
  enclosure (measured at most ``1.8e-12``), so drift in either evaluation
  fails here; and the enclosures formed at 128 and at 256 bits overlap;
* each fail-closed clause: a point not on the exact island (i), a Choi block
  not positive definite (v)(a), (H-POS) on the whole acceptance support
  (v)(b), an undecided element and an element of no certified rank over a
  companion's enclosure (iv), the option ``off``, the arithmetic unavailable,
  and the withholding of (vii).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
from dummy_bundles import build_bundle as build_trusted_bundle
from mode_bundles import build_bundle as build_mode_bundle
from registry import ALPHA_GRID
from toy_declarations import SOURCE_MODE_TOYS, toy

from certiqs_key.foundations.exact import Cx
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.solvers.frank_wolfe.general_keyrate import _run_general
from certiqs_key.solvers.frank_wolfe.keyrate import general_declaration_of
from certiqs_key.solvers.problem import _prepare_general

pytest.importorskip("flint")
from certiqs_key.foundations import balls
from certiqs_key.solvers.frank_wolfe import certified

pytestmark = [pytest.mark.contract, pytest.mark.oracle, pytest.mark.requires_qics]


def _sibling(name: str) -> Any:
    """Load ``tests/golden/<name>.py``, whose hand-derived table this file reads."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "golden" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_golden_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: The hand-derived values, as test_verified_bracket_against_registry.py reads them.
EXPECTED = _sibling("test_verified_bracket_against_registry").EXPECTED


@dataclass
class _Run:
    maps: Any
    acceptance: Any
    alpha: float
    points: list[tuple[Any, Any, Any, int]]
    assessments: list[Any]


def _run(toy_id: str, alpha: float) -> _Run:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    candidate = toy(toy_id)
    builder = (
        build_mode_bundle if candidate in SOURCE_MODE_TOYS else build_trusted_bundle
    )
    declaration = general_declaration_of(declaration_from_bundle(builder(candidate)))
    oracle = QicsSectorChoiOracle()
    maps, acceptance = _prepare_general(declaration, oracle)
    run = _run_general(maps, oracle, acceptance, alpha, None, None, None)
    assessments = [kept.assessment for kept in run.reference_candidates]
    points = [(a.point, a.q_iterate, a.solves, a.gate.iteration) for a in assessments]
    return _Run(maps, acceptance, alpha, points, assessments)


def _evaluate(run: _Run, **options: Any) -> certified.CertifiedEvaluation:
    return certified.evaluate(
        run.maps, run.points, run.acceptance, run.alpha, **options
    )


@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("toy_id", list(EXPECTED))
def test_the_certified_bracket_lies_below_the_hand_derived_value(
    toy_id: str, alpha: float
) -> None:
    run = _run(toy_id, alpha)
    result = _evaluate(run)
    assert result.status == "certified", [p.detail for p in result.points]
    expected = EXPECTED[toy_id](alpha)
    rounding = Fraction(abs(expected)) * Fraction(1, 2**52)
    for point in result.points:
        assert point.bracket is not None
        assert point.bracket <= Fraction(expected) + rounding


def _overlap_or_contain(a: Any, b: Any) -> bool:
    return bool(a.overlaps(b))


@pytest.mark.parametrize(
    ("toy_id", "alpha"),
    [("TOY-5", 1.05), ("TOY-6", 1.5), ("TOY-8-T", 1.25), ("TOY-4b", 1.9)],
)
def test_the_engine_gradient_lies_in_the_certified_enclosure(
    toy_id: str, alpha: float
) -> None:
    run = _run(toy_id, alpha)
    low = _evaluate(run, precision=128)
    high = _evaluate(run, precision=256)
    for assessment, point, fine in zip(
        run.assessments, low.points, high.points, strict=True
    ):
        assert point.certified and fine.certified
        engine = assessment.gradient
        scale = max(abs(float(x.mid())) for x in point.gradient_q.values())
        for chat, ball in point.gradient_q.items():
            assert abs(engine.q[chat] - float(ball.mid())) <= 1e-9 * scale + float(
                ball.rad()
            )
            assert _overlap_or_contain(ball, fine.gradient_q[chat])
        blocks = point.gradient_blocks
        scale = max(
            abs(complex(float(b.m[i, j].real.mid()), float(b.m[i, j].imag.mid())))
            for b in blocks.values()
            for i in range(b.shape[0])
            for j in range(b.shape[0])
        )
        for pair, ball in blocks.items():
            computed = np.asarray(engine.blocks[pair])
            n = ball.shape[0]
            for i in range(n):
                for j in range(n):
                    entry = ball.m[i, j]
                    centre = complex(float(entry.real.mid()), float(entry.imag.mid()))
                    assert (
                        abs(computed[i, j] - centre) <= 1e-9 * scale + 2 * ball.radius()
                    )
                    assert entry.overlaps(fine.gradient_blocks[pair].m[i, j])


@pytest.fixture(scope="module")
def toy5() -> _Run:
    return _run("TOY-5", 1.25)


def test_a_point_off_the_exact_island_is_not_certified(toy5: _Run) -> None:
    point, q, solves, iteration = toy5.points[0]
    off = replace(q, on_island=False)
    result = certified.evaluate(
        toy5.maps, [(point, off, solves, iteration)], toy5.acceptance, toy5.alpha
    )
    assert result.status == "not_certified"
    assert result.points[0].reasons == ("acceptance_iterate_not_exact",)


def test_a_block_not_positive_definite_is_not_certified(toy5: _Run) -> None:
    point, q, solves, iteration = toy5.points[0]
    pair = next(iter(point))
    singular = dict(point)
    singular[pair] = np.zeros_like(np.asarray(point[pair]))
    result = certified.evaluate(
        toy5.maps, [(singular, q, solves, iteration)], toy5.acceptance, toy5.alpha
    )
    assert result.points[0].reasons == ("block_not_positive_definite",)


def test_positivity_is_decided_on_every_value_of_the_acceptance_support() -> None:
    """(v)(b): (H-POS) on the whole acceptance support, key-live or not.

    TOY-8-T's support is two values, neither key-live: a ``q_t`` vanishing on
    one of them is not certified, though no deficit reads it.
    """
    run = _run("TOY-8-T", 1.5)
    point, q, solves, iteration = run.points[0]
    exact = (
        dict(q.exact)
        if q.exact is not None
        else {c: Fraction(v) for c, v in q.view.items()}
    )
    assert not set(run.maps.acceptance_support) & set(run.maps.chat_key)
    exact[run.maps.acceptance_support[-1]] = Fraction(0)
    zeroed = replace(q, exact=exact, view={c: float(v) for c, v in exact.items()})
    result = certified.evaluate(
        run.maps, [(point, zeroed, solves, iteration)], run.acceptance, run.alpha
    )
    assert result.points[0].reasons == ("positivity_not_certified",)


def test_the_acceptance_side_subtracts_the_radius(toy5: _Run) -> None:
    """(v)(d), ``lem:certified-bracket`` (ii): ``b^A`` lies below every member.

    Wide balls (radius 1/8) around the gradient: ``b^A`` is the exact minimum
    at the centre less the radius, at most the value of the lowest member.
    """
    d = toy5.maps.declaration
    wide = balls.flint.arb(0, balls.real(Fraction(1, 8)))
    with balls.precision(128):
        g_q = {
            c: balls.real(Fraction(3, 2)) + wide for c in toy5.maps.acceptance_support
        }
        b_a = certified._acceptance_side(d, toy5.acceptance, g_q)
    lowest = sum(
        (Fraction(3, 2) - Fraction(1, 8)) * Fraction(x)
        for c, x in zip(d.acceptance_values, d.acceptance_set.frequencies, strict=True)
        if c in g_q
    )
    assert b_a <= lowest


def test_the_option_off_and_an_absent_library_leave_the_run_as_it_is(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    off = _evaluate(toy5, option="off")
    assert (off.status, off.reasons, off.certified_bound) == (
        "off",
        ("certified_evaluation_off",),
        None,
    )
    monkeypatch.setattr(balls, "AVAILABLE", False)
    absent = _evaluate(toy5)
    assert absent.status == "not_certified" and absent.certified_bound is None
    assert absent.reasons == ("not_certified", "certifier_unavailable")


def test_an_upstream_premise_withholds_the_tier(toy5: _Run) -> None:
    result = _evaluate(toy5, withheld=("receiver_weight_floating_point",))
    assert result.status == "withheld" and not result.reported
    assert result.certified_bound is not None
    assert result.reasons == ("receiver_weight_floating_point",)


@dataclass(frozen=True)
class _Factor:
    position: int
    alphabet: tuple[str, ...]
    centres: dict[str, tuple[Any, ...]]
    radii: dict[str, tuple[Any, ...]]
    factor_enclosures: dict[str, tuple[Any, ...]] = field(default_factory=dict)
    #: ``CompanionFactor.label``, which the certifier names a factor by.
    label: str = "f0"


def _companion(run: _Run, change: Any) -> Iterator[Any]:
    """Return factor 0 of the declaration as an exact enclosure, one block changed."""
    factor = run.maps.declaration.factors[0]
    centres: dict[str, tuple[Any, ...]] = {}
    radii: dict[str, tuple[Any, ...]] = {}
    for letter in factor.alphabet:
        blocks = []
        rads = []
        for sector in factor.sectors.labels:
            block = np.asarray(factor.blocks[letter][sector], dtype=np.complex128)
            n = block.shape[0]
            centre = tuple(
                tuple(Cx(Fraction(z.real), Fraction(z.imag)) for z in row)
                for row in block
            )
            radius = tuple(tuple(Fraction(0) for _ in range(n)) for _ in range(n))
            centre, radius = change(letter, sector, centre, radius)
            blocks.append(centre)
            rads.append(radius)
        centres[letter], radii[letter] = tuple(blocks), tuple(rads)
    return iter([_Factor(0, factor.alphabet, centres, radii)])


def _key_element(run: _Run, inert_pair: bool = False) -> tuple[str, str]:
    """Return a non-zero element of factor 0 at a key-active (or key-inert) pair."""
    d = run.maps.declaration
    for (chat, pair), inert in run.maps.key_inert.items():
        if inert is not inert_pair or chat not in run.maps.chat_key:
            continue
        sector = d.split_sector(pair[1])[0]
        for letter in d.factors[0].alphabet:
            if np.any(np.asarray(d.factors[0].blocks[letter][sector]) != 0):
                return letter, sector
    raise AssertionError("no key-active element")


def test_an_undecided_element_fails_closed(toy5: _Run) -> None:
    """Item (iv): centre 0, a radius not 0 -- zero or not is undecided.

    At a KEY-INERT pair, where no rank is asked: an undecided element entering
    a pass class with Alice's element non-zero fails every point all the same,
    since it could change key-inertness itself (``lem:certified-bracket-enclosed``
    (a)).
    """
    target = _key_element(toy5, inert_pair=True)
    tiny = Fraction(1, 2**130)

    def change(letter: str, sector: str, centre: Any, radius: Any) -> Any:
        if (letter, sector) != target:
            return centre, radius
        n = len(centre)
        zero = Cx(Fraction(0), Fraction(0))
        return (
            tuple(tuple(zero for _ in range(n)) for _ in range(n)),
            tuple(tuple(tiny for _ in range(n)) for _ in range(n)),
        )

    companion = type("C", (), {"factors": tuple(_companion(toy5, change))})()
    result = _evaluate(toy5, companion=companion)
    assert result.status == "not_certified"
    assert all(p.reasons == ("rank_not_certified",) for p in result.points)


def test_the_rank_rule_over_an_enclosure() -> None:
    """Item (iv) and ``cor:least-eigenvalue-over-enclosure`` (iv), element by element.

    A positive definite block with radii certifies its rank; a rank-one block
    with a radius on every entry fixes no row at zero and certifies none; a
    row whose centre and radii are all 0 is dropped (``E`` the coordinate
    selection); centre 0 with a radius is undecided; all 0 is zero.
    """
    zero, one = Cx(Fraction(0), Fraction(0)), Cx(Fraction(1), Fraction(0))
    half = Cx(Fraction(1, 2), Fraction(0))
    tiny = Fraction(1, 2**130)
    with balls.precision(128):
        definite = certified._enclosed_element(
            ((one, half), (half, one)), [[tiny, tiny], [tiny, tiny]]
        )
        rank_one = certified._enclosed_element(
            ((one, one), (one, one)), [[tiny, tiny], [tiny, tiny]]
        )
        dropped = certified._enclosed_element(
            ((one, zero), (zero, zero)), [[tiny, 0], [0, 0]]
        )
        undecided = certified._enclosed_element(
            ((zero, zero), (zero, zero)), [[tiny, 0], [0, 0]]
        )
        nothing = certified._enclosed_element(
            ((zero, zero), (zero, zero)), [[0, 0], [0, 0]]
        )
    assert definite.form is not None and len(definite.form[0]) == 2
    assert rank_one.form is None and rank_one.cause is not None
    assert rank_one.zero is False
    assert dropped.form is not None and dropped.form[0] == ((one, zero),)
    assert undecided.zero is None and undecided.form is None
    assert nothing.zero is True


def test_an_exact_enclosure_certifies_as_the_declaration_does(toy5: _Run) -> None:
    companion = type("C", (), {"factors": tuple(_companion(toy5, lambda *a: a[2:]))})()
    plain, enclosed = _evaluate(toy5), _evaluate(toy5, companion=companion)
    assert enclosed.status == "certified"
    assert enclosed.certified_bound == plain.certified_bound


# ---------------------------------------------------------------------------
#  Item (iv)(b), (c) end to end: a factor enclosure injected on one block
# ---------------------------------------------------------------------------
#
# The receiver emits no factor enclosure here, so these inject one on factor 0 of
# TOY-5's companion, whose blocks are 1 x 1: a block c > 0 read with the entrywise
# radius c, which the recentring turns into centre 0, so the entrywise rule leaves it
# undecided, and with the factor enclosure (q, t, 1), q a dyadic near sqrt(c), of which
# c is a member ((q - t)^2 <= c <= (q + t)^2, decided below), as (H-FAC) asks.


def _root_box(c: Fraction, scale: int = 2**120) -> tuple[Fraction, Fraction]:
    """Return ``(q, t)`` with ``(q - t)^2 <= c <= (q + t)^2``, decided exactly."""
    import math

    q = Fraction(math.isqrt(int(c * scale * scale)), scale)
    t = Fraction(1, 2**100)
    assert (q - t) ** 2 <= c <= (q + t) ** 2
    return q, t


def _with_factor(
    run: _Run,
    target: tuple[str, str],
    scale: Fraction,
    *,
    undecided: bool = True,
    alone: bool = False,
) -> Any:
    """Return the companion with a factor enclosure ``scale q`` on ``target``.

    ``undecided``: the entrywise radius ``c``, so the entrywise rule leaves the
    block undecided; otherwise radius 0, so it decides the block first.
    ``alone``: every other letter's block at the target's sector set to an
    exact zero, so the target is the one element of its pass class there.
    """
    from certiqs_key.foundations.reference import FactorEnclosure

    found: dict[str, Any] = {}
    zero = Cx(Fraction(0), Fraction(0))

    def change(letter: str, sector: str, centre: Any, radius: Any) -> Any:
        if sector == target[1] and letter != target[0] and alone:
            return ((zero,),), ((Fraction(0),),)
        if (letter, sector) != target:
            return centre, radius
        ((value,),) = centre
        q, t = _root_box(value.re)
        found["factor"] = FactorEnclosure(
            ((Cx(scale * q, Fraction(0)),),), ((t,),), (Fraction(1),)
        )
        return centre, ((value.re if undecided else Fraction(0),),)

    (factor,) = _companion(run, change)
    sectors = run.maps.declaration.factors[0].sectors.labels
    enclosures = tuple(
        found["factor"] if s == target[1] else None for s in sectors
    )
    carried = replace(factor, factor_enclosures={target[0]: enclosures})
    return type("C", (), {"factors": (carried,)})()


def test_a_block_the_factor_rule_decides_certifies(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Item (iv)(b): where the entrywise rule fixes no rank, the factor fixes it.

    A 1 x 1 block whose entrywise rule fixes no rank is undecided, and then its
    enclosure, read by the statistics, is too wide for (H-POS); the case the
    factor form exists for, a rank-deficient block of dimension 2 or more that
    the entrywise rule decides not zero with no rank, has no golden toy. So
    the entrywise rule's form is withheld on the target block (radius 0: the
    statistics read it exactly), standing in for that case. TOY-5's key-active
    pass class reads two Bob letters on Alice's one row; the other letter is
    an exact zero (``alone``), since an enclosed ``E_v`` beside another
    element on the same rows fails closed (the next test). The run certifies
    with ``E`` the box of ``L^dagger`` through :func:`certified._class`'s
    per-element factorisation, within ``1e-9`` of the same companion read
    exactly. The companion is no POVM; the evaluation decides nothing of that.
    """
    target = _key_element(toy5)
    companion = _with_factor(toy5, target, Fraction(1), undecided=False, alone=True)
    exact = _evaluate(toy5, companion=companion)
    assert exact.status == "certified", [p.detail for p in exact.points]
    decided: list[Any] = []
    real_rule, real_entrywise = certified._factor_rule, certified._enclosed_element

    def rule(factor: Any) -> Any:
        result = real_rule(factor)
        decided.append(result)
        return result

    def entrywise(centre: Any, radii: Any) -> Any:
        element = real_entrywise(centre, radii)
        if centre == ((Cx(Fraction(1, 2), Fraction(0)),),):
            return certified._Element(element.full, False, cause="no rank (test)")
        return element

    monkeypatch.setattr(certified, "_factor_rule", rule)
    monkeypatch.setattr(certified, "_enclosed_element", entrywise)
    enclosed = _evaluate(toy5, companion=companion)
    assert enclosed.status == "certified", [p.detail for p in enclosed.points]
    assert [d for d, _ in decided] == [False], "the factor rule decided the block"
    assert exact.certified_bound is not None and enclosed.certified_bound is not None
    assert abs(enclosed.certified_bound - exact.certified_bound) <= Fraction(1, 10**9)


def test_an_enclosed_element_beside_another_on_alices_rows_fails_closed(
    toy5: _Run,
) -> None:
    """Prototype pitfall 5.3 item 3, end to end: rows dependent through ``q``.

    In TOY-5's key-active class both Bob letters sit on Alice's one row; with
    one of them read through its enclosed factor the stack's rows are
    dependent through an irrational relation no exact factorisation sees, and
    the floor of ``N`` fails closed.
    """
    result = _evaluate(
        toy5, companion=_with_factor(toy5, _key_element(toy5), Fraction(1))
    )
    assert result.status == "not_certified"
    assert {p.reasons for p in result.points} == {("floor_not_certified",)}


@pytest.mark.parametrize("inert", [False, True])
def test_an_inconsistent_block_fails_every_point_at_any_pair(
    toy5: _Run, inert: bool
) -> None:
    """Item (iv)(c): members ``(2q)^2 = 4c`` lie outside the disc ``|X - c| <= c``.

    Every point fails with ``factor_enclosure_inconsistent``, at a key-active
    pair and at a key-inert one alike, which the caller reads as the bracket
    withdrawn (``req:bracket-on-reference`` (iv)).
    """
    target = _key_element(toy5, inert_pair=inert)
    result = _evaluate(toy5, companion=_with_factor(toy5, target, Fraction(2)))
    assert result.status == "not_certified" and result.inconsistent
    assert {p.reasons for p in result.points} == {("factor_enclosure_inconsistent",)}


# ---------------------------------------------------------------------------
#  The fail-closed reasons reached, and the record's rounding
# ---------------------------------------------------------------------------
#
# ``support_not_established`` ((iii)(a)), ``floor_not_certified``
# ((iii)(b)) and ``acceptance_geometry_not_certified`` ((v)(d)) are mapped from
# lower-level failures; testing only the lower-level ``NotCertified`` would let
# a mapping that dropped or renamed a reason, or let ``NotCertified`` escape
# the evaluation as an error, pass; so would the positivity of K and P, the
# rank rule at a key-active pair and the record's downward rounding.


def _not_certified(*_: Any, **__: Any) -> Any:
    raise balls.NotCertified("forced by the test")


def test_a_gram_not_certified_is_support_not_established(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(balls, "cholesky_upper", _not_certified)
    result = _evaluate(toy5)
    assert result.status == "not_certified"
    assert {p.reasons for p in result.points} == {("support_not_established",)}


def test_a_floor_not_certified_is_floor_not_certified(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(balls, "power", _not_certified)
    result = _evaluate(toy5)
    assert result.status == "not_certified"
    assert {p.reasons for p in result.points} == {("floor_not_certified",)}


def test_an_acceptance_geometry_not_solved_exactly_is_not_certified(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The singleton branch of _acceptance_side is switched off, so the toy's
    # (non-exact) singleton oracle stands for a geometry no exact oracle solves.
    # Each q_t is given its exact view, which a singleton's iterate lacks, so
    # that the point passes item (i) and reaches the acceptance side (the
    # guard that reads q off its binary64 view only on the singleton reads the
    # geometry too).
    monkeypatch.setattr(certified, "SINGLETON", "no-such-geometry")
    exact = [
        (point, replace(q, exact={c: Fraction(v) for c, v in q.view.items()}), s, i)
        for point, q, s, i in toy5.points
    ]
    result = certified.evaluate(toy5.maps, exact, toy5.acceptance, toy5.alpha)
    assert result.status == "not_certified"
    assert {p.reasons for p in result.points} == {
        ("acceptance_geometry_not_certified",)
    }


def test_the_recorded_bounds_are_rounded_toward_minus_infinity(toy5: _Run) -> None:
    """(vi), (ix): h_cert "entering every binary64 use rounded toward -inf"."""
    from certiqs_key.foundations.dyadic import float_down

    result = _evaluate(toy5)
    assert result.certified_bound is not None
    record = result.as_record(first_order=None, first_order_key_length=None)
    assert record["certified_bound"] == float_down(result.certified_bound)
    assert Fraction(record["certified_bound"]) <= result.certified_bound
    for point, entry in zip(result.points, record["points"], strict=True):
        assert point.bracket is not None
        assert entry["certified_bracket"] == float_down(point.bracket)


def test_a_k_not_certified_positive_is_positivity_not_certified(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(v)(b): K^J at a key-live value must have a positive lower end."""
    real = certified._deficit
    calls: list[int] = []

    def sunk(classes: Any, choi: Any, alpha: Any, where: Any) -> Any:
        value, gradient = real(classes, choi, alpha, where)
        calls.append(1)
        return value - balls.real(10**6), gradient

    monkeypatch.setattr(certified, "_deficit", sunk)
    result = _evaluate(toy5)
    assert calls, "TOY-5 has a key-active pair at a key-live value"
    assert {p.reasons for p in result.points} == {("positivity_not_certified",)}


def test_a_p_not_certified_positive_is_positivity_not_certified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(v)(b): P^J on every value of the acceptance support.

    TOY-8-T's support values are not key-live, so only the P check guards them.
    """
    run = _run("TOY-8-T", 1.5)
    real = certified._statistics_operators

    def negated(model: Any, *args: Any) -> None:
        real(model, *args)
        for key, value in list(model.gamma.items()):
            model.gamma[key] = value.scale(-1)

    monkeypatch.setattr(certified, "_statistics_operators", negated)
    result = _evaluate(run)
    assert {p.reasons for p in result.points} == {("positivity_not_certified",)}


def test_an_element_of_no_certified_rank_at_a_key_active_pair_fails_every_point(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(iv): a block with no certified rank at a pair that is not key-inert.

    Every golden toy's measured blocks are 1 x 1, so no companion of a toy can
    carry a rank-deficient element; the element at TOY-5's key-active pair is
    replaced by one decided non-zero with no factor form, which is what
    ``_enclosed_element`` returns for such a block.
    """
    target = _key_element(toy5, inert_pair=False)
    real = certified._bob_elements

    def without_rank(maps: Any, companion: Any) -> Any:
        elements = real(maps, companion)
        element = elements[target]
        elements[target] = certified._Element(
            element.full, False, cause="forced: no certified rank"
        )
        return elements

    monkeypatch.setattr(certified, "_bob_elements", without_rank)
    result = _evaluate(toy5)
    assert result.status == "not_certified"
    assert {p.reasons for p in result.points} == {("rank_not_certified",)}


def test_the_cross_check_runs_before_any_other_failure(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Item (iv)(c) at every block: a frame not enclosed does not hide a defect.

    The inconsistency withdraws the companion's bracket, so it is decided
    before Alice's frames, whose failure would otherwise mark every point
    first and leave the defective carrier's bracket standing.
    """

    def no_frame(model: Any) -> Any:
        raise certified._Fail("frame_not_enclosed", "forced by the test")

    monkeypatch.setattr(certified, "_alice", no_frame)
    target = _key_element(toy5, inert_pair=True)
    result = _evaluate(toy5, companion=_with_factor(toy5, target, Fraction(2)))
    assert result.inconsistent
    assert {p.reasons for p in result.points} == {("factor_enclosure_inconsistent",)}


def test_q_is_read_off_its_binary64_view_only_on_the_singleton(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Item (i): elsewhere than on the singleton the point fails closed.

    TOY-5's singleton iterate has no exact view; read as another geometry's
    it is not the exact rational iterate item (i) asks for.
    """
    point, q, solves, iteration = toy5.points[0]
    assert q.exact is None and q.on_island
    monkeypatch.setattr(certified, "SINGLETON", "no-such-geometry")
    result = certified.evaluate(
        toy5.maps, [(point, q, solves, iteration)], toy5.acceptance, toy5.alpha
    )
    assert result.points[0].reasons == ("acceptance_iterate_not_exact",)


def test_a_factor_enclosure_failing_its_decisions_is_not_read(toy5: _Run) -> None:
    """``foundations/req:snap-reference`` (i): such a factor enclosure is not read."""
    from certiqs_key.foundations.reference import FactorEnclosure

    target = _key_element(toy5)
    bad = FactorEnclosure(
        ((Cx(Fraction(1), Fraction(0)),),), ((Fraction(-1),),), (Fraction(1),)
    )
    sectors = toy5.maps.declaration.factors[0].sectors.labels
    (factor,) = _companion(toy5, lambda *a: a[2:])
    carried = replace(
        factor,
        factor_enclosures={
            target[0]: tuple(bad if s == target[1] else None for s in sectors)
        },
    )
    assert certified._carried(carried, target[0], sectors.index(target[1])) is None
    # Read, its member 1 against the block 1/2 would be inconsistent.
    result = _evaluate(toy5, companion=type("C", (), {"factors": (carried,)})())
    assert result.status == "certified"


def test_a_boxed_form_inconsistent_with_itself_fails_every_point(
    toy5: _Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reordered form's own consistency checks fail closed, not by crashing.

    A broken invariant of the reordered form (here: one block key fewer than
    the parts it names, at :func:`certified._product`) is a defect of the
    engine that no claim admits. It marks every point
    ``boxed_form_inconsistent``, so the run's number stays first order
    (req:certified-evaluation (vi)), as with every other step not established.
    """
    original = certified._product

    def one_key_short(parts: Any, blocks: Any) -> Any:
        return original(parts, list(blocks)[:-1])

    monkeypatch.setattr(certified, "_product", one_key_short)
    result = _evaluate(toy5)
    assert result.status == "not_certified" and result.certified_bound is None
    assert {p.reasons for p in result.points} == {("boxed_form_inconsistent",)}
