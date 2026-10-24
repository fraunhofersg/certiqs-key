"""Clauses of the certified tier no other default-tier test pins.

Each test kills a mutant that would survive the other default-tier tests, and
each passes on the code:

* ``receiver/def:enclosed-weight`` (iii) with predicate (X) failing: the
  remainder ``T_m = 1 - sum_k beta_k d_k^m`` (eq:windowtail). No receiver of
  the suite reaches a weight where ``T_m`` binds, so ``T_m`` read as
  ``beta(m)`` survives. Hand-derived: ``K = 2``, ``gamma = 1/2``,
  ``beta_k = 1``, ``c = 1/8``, ``d_k = 1/4``, ``N = 1``, ``m = 2``:
  ``beta(2) = 1 + (1/2)(1/64) - 2 (1/16) = 113/128``,
  ``T_2 = 1 - 2/16 = 7/8``, so the weight is ``max{0, min{113/128, 7/8}} = 7/8``.
* ``foundations/def:tiers`` (iii) for the companion's enclosure as balls:
  ``Ball.enclosure(C, r)`` must contain every ``X`` with ``|X - C| <= r``
  (a mutant that halves the radii fails).
* ``cor:certified-keylength`` (ii) through ``cor:fo-keylength``: a non-ideal
  hash costs one bit, as ``key_length_from_bound`` charges it.
* ``receiver/req:rigorous-weight`` (iii), ``def:enclosed-weight`` (i): the four
  directions on enclosures with a radius.
* ``receiver/req:evaluation-label``: ``rigorous`` only where every setting is.
* ``req:certified-evaluation`` (vi): the floor refined until it is decided,
  however close ``c - tau`` lies to an integer.
"""

from __future__ import annotations

import cmath
from fractions import Fraction

import pytest
from probe_presence import requires_probe

from certiqs_key.meat_core.finitekey.keylength import (
    certified_key_length,
    key_length_from_bound,
)
from certiqs_key.receiver.rigorous import EnclosedWeight, enclosed_weight

pytestmark = pytest.mark.contract


def test_the_remainder_binds_where_predicate_x_fails() -> None:
    data = EnclosedWeight(
        gamma=Fraction(1, 2),
        betas=(Fraction(1), Fraction(1)),
        c=Fraction(1, 8),
        ds=(Fraction(1, 4), Fraction(1, 4)),
        window=(),
    )
    weight = enclosed_weight(data, cutoff=1, predicate_x=False, window=2, depth=None)
    assert weight == Fraction(7, 8)


def test_the_ball_of_an_enclosure_holds_every_member() -> None:
    pytest.importorskip("flint")
    from certiqs_key.foundations import balls
    from certiqs_key.foundations.exact import Cx

    r = Fraction(1, 1000)
    centre = ((Cx(Fraction(1), Fraction(0)), Cx(Fraction(1, 3), Fraction(-1, 5))),)
    with balls.precision(128):
        ball = balls.Ball.enclosure(
            (centre[0], (centre[0][1].conjugate(), Cx(Fraction(2), Fraction(0)))),
            [[r, r], [r, r]],
        )
        for angle in (0.0, 0.7, 1.9, 3.1, 4.4):
            z = cmath.rect(float(r) * (1 - 2.0**-30), angle)
            member = balls.flint.acb(
                balls.real(Fraction(1, 3) + Fraction(z.real)),
                balls.real(Fraction(-1, 5) + Fraction(z.imag)),
            )
            assert ball.m[0, 1].contains(member)


@pytest.mark.parametrize("eps_pa", [2.0**-30, 1e-10])
def test_a_non_ideal_hash_costs_the_bit_the_first_order_length_charges(
    eps_pa: float,
) -> None:
    common = {
        "rounds": 10**6,
        "lambda_ec": 1000,
        "eps_ev": 1e-10,
        "eps_pa": eps_pa,
        "alpha": 1.5,
    }
    h = Fraction(1, 2)
    ideal, _ = certified_key_length(h=h, ideal_hash=True, **common)
    plain, _ = certified_key_length(h=h, ideal_hash=False, **common)
    assert plain == ideal - 1
    first, _ = key_length_from_bound(h=0.5, ideal_hash=False, **common)
    assert plain == first


def test_the_four_directions_on_enclosures_with_a_radius() -> None:
    """The four directions of receiver/req:rigorous-weight (iii).

    def:enclosed-weight (i): g <= gamma, b_k >= beta_k, c = 1 - u with
    u >= lmax(B), d_k = 1 - l_k with l_k <= lmin(B_k).

    Every receiver of the suite has exact (radius-0) prefactors and Grams, so
    taking gamma, beta_k or c from the wrong end of its ball survives. Here
    each ball has radius r: 1 x 1 Grams 1/2 (all ports) and 1/4 (all but one),
    prefactors 3/4 and 7/8.
    """
    from certiqs_key.receiver.enclosure import Ball
    from certiqs_key.receiver.generic import BallField
    from certiqs_key.receiver.rigorous import _enclosed_data

    r = Fraction(1, 1000)
    every = frozenset({0, 1})
    pairs = {
        every: (
            Ball(Fraction(3, 4), Fraction(0), r),
            [[Ball(Fraction(1, 2), Fraction(0), r)]],
        ),
        frozenset({1}): (
            Ball(Fraction(7, 8), Fraction(0), r),
            [[Ball(Fraction(1, 4), Fraction(0), r)]],
        ),
        frozenset({0}): (
            Ball(Fraction(7, 8), Fraction(0), r),
            [[Ball(Fraction(1, 4), Fraction(0), r)]],
        ),
    }
    data = _enclosed_data(BallField(), pairs, 2, 1, None)
    assert data.gamma <= Fraction(3, 4) - r
    assert all(b >= Fraction(7, 8) + r for b in data.betas)
    assert data.c <= Fraction(1, 2) - r
    assert all(d >= Fraction(3, 4) + r for d in data.ds)


@requires_probe
def test_one_floating_point_setting_labels_the_artifact_floating_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """receiver/req:evaluation-label: `rigorous` only where EVERY setting is.

    The receiver with a probe source (settings ``off`` and ``on``), built by
    ``instances.common.optics`` rather than through an instance a removable
    submodule brings, so that this file stays outside that submodule's
    removability list.
    """
    from instances.common.led import LedProbe
    from instances.common.optics import ReceiverParameters, receiver_request

    from certiqs_key.receiver import construct as construct_module
    from certiqs_key.receiver.construct import construct_receiver
    from certiqs_key.receiver.rigorous import PORT_GRAMS_NOT_ENCLOSED

    request = receiver_request(ReceiverParameters(photon_cutoff=1), LedProbe(window=4))
    assert construct_receiver(request).artifact.bound_evaluation == "rigorous"
    real = construct_module.rigorous_weights

    def one_falls_back(validated: object) -> dict[str, object]:
        out = dict(real(validated))
        assert len(out) >= 2, "a receiver with two settings"
        out[sorted(out)[-1]] = PORT_GRAMS_NOT_ENCLOSED
        return out

    monkeypatch.setattr(construct_module, "rigorous_weights", one_falls_back)
    artifact = construct_receiver(request).artifact
    assert artifact is not None
    evaluations = {s.evaluation for s in artifact.bound_quantifier_domain.per_setting}
    assert evaluations == {"rigorous", "floating_point"}
    assert artifact.bound_evaluation == "floating_point"


@pytest.mark.parametrize("eps_pa", [1e-10, 3e-11, 0.1])
@pytest.mark.parametrize("offset", ["1e-150", "-1e-150"])
def test_the_floor_needs_the_refinement_however_close(
    eps_pa: float, offset: str
) -> None:
    """req:certified-evaluation (vi): refine until floor(c - U) = floor(c - L).

    The suite's closest case (``c - tau`` within ``1e-45`` of an integer) is
    decided by the first enclosure, so taking it without refining survives;
    ``1e-150`` is not.
    """
    mpmath = pytest.importorskip("mpmath")
    mpmath.mp.dps = 260
    rounds, lambda_ec, eps_ev, alpha, k = 10**8, 12345, 1e-10, 1.05, 2_000_000
    a = mpmath.mpf(Fraction(alpha).numerator) / Fraction(alpha).denominator
    eps = mpmath.mpf(Fraction(eps_pa).numerator) / Fraction(eps_pa).denominator
    tau = a / (a - 1) * mpmath.log(1 / eps, 2)
    from certiqs_key.meat_core.finitekey.keylength import _ceil_log2

    ceil_ev = _ceil_log2(1 / Fraction(eps_ev))
    target = mpmath.mpf(k) + mpmath.mpf(offset) + tau + lambda_ec + ceil_ev - 1
    h = Fraction(mpmath.nstr(target / rounds, 240))
    length, _ = certified_key_length(
        rounds=rounds,
        h=h,
        lambda_ec=lambda_ec,
        eps_ev=eps_ev,
        eps_pa=eps_pa,
        alpha=alpha,
    )
    assert length == (k if not offset.startswith("-") else k - 1)
