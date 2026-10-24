"""Independent vacuum, marginal, and Gaussian-matrix checks of the SPDC model."""

from fractions import Fraction as F

import numpy as np
import pytest
from instances.common.honest.spdc_pair import (
    SpdcModel,
    click_distribution,
    no_click_probability,
)

from certiqs_key.foundations.exact import Cx, identity, matrix, scale, zeros


def test_spdc_vacuum_and_single_arm_marginals():
    n = F(1, 16)
    assert no_click_probability(identity(2), identity(2), n) == 1 / (1 + n) ** 2
    assert no_click_probability(identity(2), zeros(2), n) == 1 / (1 + n) ** 2
    eta = F(3, 8)
    assert (
        no_click_probability(scale(eta, identity(2)), zeros(2), n)
        == 1 / (1 + n * eta) ** 2
    )
    assert no_click_probability(zeros(2), zeros(2), n) == 1


def test_two_by_two_formula_agrees_with_full_complex_gaussian_determinant():
    # A complex contraction makes transpose versus adjoint distinguishable.
    a = np.array([[0.375, 0.125j], [-0.125j, 0.25]])
    b = np.array([[0.25, 0.0625j], [-0.0625j, 0.5]])
    n = F(1, 8)
    loss = np.zeros((4, 4), dtype=np.complex128)
    loss[:2, :2], loss[2:, 2:] = a, b
    swap = np.block([[np.zeros((2, 2)), np.eye(2)], [np.eye(2), np.zeros((2, 2))]])
    anomalous = np.sqrt(float(n * (1 + n))) * swap
    moments = np.block(
        [[float(n) * np.eye(4), anomalous], [anomalous, float(n) * np.eye(4)]]
    )
    losses = np.block([[loss, np.zeros((4, 4))], [np.zeros((4, 4)), loss.T]])
    full = 1 / np.sqrt(np.linalg.det(np.eye(8) + moments @ losses))
    exact = no_click_probability(
        matrix([[Cx(F(z.real), F(z.imag)) for z in row] for row in a]),
        matrix([[Cx(F(z.real), F(z.imag)) for z in row] for row in b]),
        n,
    )
    assert full.imag == pytest.approx(0, abs=1e-14)
    assert float(exact) == pytest.approx(full.real, abs=1e-14)


def test_exact_inclusion_exclusion_normalizes_and_keeps_true_zeros():
    grams = (scale(F(1, 4), identity(2)),) * 4
    distribution = click_distribution(
        grams,
        grams,
        SpdcModel(mean_pairs=F(1, 16)),
        alice_dark=(F(0),) * 4,
        bob_dark=(F(0),) * 4,
    )
    assert sum(distribution.values(), F(0)) == 1
    assert min(distribution.values()) >= 0
    assert distribution[(0, 0)] == 1 / (1 + F(1, 32)) ** 2
    assert all(distribution[(0, mask)] == 0 for mask in range(1, 16))
    assert all(distribution[(mask, 0)] == 0 for mask in range(1, 16))


def test_zero_brightness_is_independent_dark_counts():
    grams = (scale(F(1, 4), identity(2)),) * 4
    dark = (F(1, 8),) * 4
    distribution = click_distribution(
        grams, grams, SpdcModel(mean_pairs=F(0)), alice_dark=dark, bob_dark=dark
    )
    for (left, right), probability in distribution.items():
        clicks = left.bit_count() + right.bit_count()
        assert probability == F(1, 8) ** clicks * F(7, 8) ** (8 - clicks)
