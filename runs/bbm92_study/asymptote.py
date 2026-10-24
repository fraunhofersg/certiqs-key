r"""The asymptotic key rate of the study's ideal-device BBM92, in closed form.

The figures draw it as the ``n -> infinity`` reference of the ideal-detector
curves; the realistic curves (dark counts,
mismatch) have no closed form and get none.

THE SETTING. bbm92 with ideal devices: detectors of efficiency 1 and no dark
counts, an exact 50:50 passive basis choice at both stations, no PBS leakage,
aligned plates, and the source's Werner state of visibility ``v``, so that
each key basis shows the bit error ``Q = (1 - v) / 2``. Each arm transmits
with its transmittance; ``loss_db`` is the total, ``eta_A eta_B =
10^(-loss_db/10)``. A round is a test round with probability ``gamma``
(``test_fraction``, default 1/8); a generation round is a key round when both
stations click once and announce the same basis, ``Z`` or ``X`` (both are key
bases by default). Error correction is charged ``f_EC`` times the Shannon
limit, ``lambda_EC = f_EC n H(K_A | K_B)`` on the key rounds.

THE RATE (newly derived for this study, not cited). Per round,

    r_inf = (1 - gamma) * eta_A eta_B * 1/2 * (1 - h(Q) - f_EC h(Q)),

floored at 0, with ``h`` the binary entropy:

1. A generation round is a key round with probability ``eta_A eta_B * 1/2``:
   both photons arrive (ideal detectors click exactly when a photon arrives),
   and two independent fair basis choices agree with probability 1/2.
2. On a key round in basis Z the phase error is the bit error of basis X, and
   vice versa; for the Werner state both are Q. The entropy of Alice's key bit
   given Eve is at least ``1 - h(Q)`` (the entropic uncertainty relation for
   the complementary bases Z and X). The bound is attained, so it is the
   asymptotic rate: the test statistics (Z and X outcomes, matched and
   mismatched) do not fix the Y correlation, and the Bell-diagonal state with
   weights ``(1-Q)^2, Q(1-Q), Q(1-Q), Q^2`` (bit and phase errors independent)
   reproduces them with ``H(K_A|E) = 1 - H(weights) + h(Q) = 1 - h(Q)``. The
   Werner state itself leaves Eve less (0.945 against 0.919 bits at Q = 1 %),
   but the engine bounds the worst state the data admit.
3. Bob's bit differs from Alice's with probability Q, so error correction
   costs ``f_EC h(Q)`` per key round.
4. As ``n -> infinity`` the finite-size terms of the key length vanish and the
   searched Renyi order tends to 1, where the Renyi entropy bound meets the
   von Neumann rate; the test fraction stays the run's.

WHAT CHECKS IT. The engine's ideal-device draft runs lie below this rate at
every point and approach it as n grows: the ratio is 0.9998 at 0 dB and
n = 1e11, 0.9993 at 10 dB, 0.9977 at 20 dB.
A finite-n run above it would refute it; ``tests/unit/test_bbm92_study_asymptote.py``
pins the closed form, and the study's summaries are checked against it when
the figures are built.
"""

from __future__ import annotations

import math
from fractions import Fraction

__all__ = [
    "TEST_FRACTION",
    "binary_entropy",
    "ideal_rate",
    "ideal_rate_per_coincidence",
]

#: bbm92's default ``test_fraction`` (instances/bbm92/protocol.yaml); the study
#: never overrides it, and a test checks the two agree.
TEST_FRACTION = Fraction(1, 8)


def binary_entropy(p: float) -> float:
    """Return ``h(p)`` in bits, with ``h(0) = h(1) = 0``."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def ideal_rate_per_coincidence(
    qber: float, f_ec: float, test_fraction: float = float(TEST_FRACTION)
) -> float:
    """Return the asymptotic key bits per coincidence, the same at every loss."""
    h = binary_entropy(qber)
    return max(0.0, (1.0 - test_fraction) * 0.5 * (1.0 - h - f_ec * h))


def ideal_rate(
    loss_db: float,
    qber: float,
    f_ec: float,
    test_fraction: float = float(TEST_FRACTION),
) -> float:
    """Return the asymptotic key rate per round of the ideal-device BBM92."""
    return float(10.0 ** (-loss_db / 10.0)) * ideal_rate_per_coincidence(
        qber, f_ec, test_fraction
    )
