"""Hand-derived values for the efficiency normalization (receiver batch N).

FROZEN ORACLE: every value here is derived by hand from the claims below and
the device they are stated for, NEVER computed by the module it tests
(PRINCIPLES.md section 2.3). A change to the engine that moves one of these is
a defect or a claim amendment, never a reason to edit this file.

Claims: ``receiver/detector-imperfections/def:normalized-station``,
``prop:efficiency-normalization``, ``rem:normalization-gain``,
``req:efficiency-normalization``, ``req:loss-before-evaluation``;
``reductions/wpfss/cor:normalized-flat``.

THE DEVICE. The ideal balanced passive BB84 receiver of
``instances/common/optics.py`` at its defaults: basis split 1/2, half-wave
plate at pi/8, perfect polarizing beamsplitters, no dark counts, the channel
modes ``(Z_H, Z_V)`` and the four ports H, V, D, A; every port at the same
efficiency ``eta``.

0. THE DEFAULT FACTOR (req:efficiency-normalization). With ``eta_max`` the
   largest declared efficiency, the default is ``t = eta_max / (99/100)
   = eta_max * 100/99`` where ``eta_max < 99/100``, and ``t = 1`` from
   ``99/100`` on. A port at ``eta_max`` is then compiled at
   ``eta_max / t = 99/100`` exactly. By hand:

   * ``eta_max = 1/5``: ``t = (1/5)(100/99) = 100/495 = 20/99``;
   * ``eta_max = 3/5``: ``t = (3/5)(100/99) = 300/495 = 20/33``.

   The FULL normalization ``t = eta_max`` stays declarable; it compiles a
   port at ``eta_max`` at efficiency one, which is what items 1 and 2 also
   record, under ``*_FULL``.

1. THE TWO-PHOTON MULTICLICK BLOCK (rem:normalization-gain).
   Lossless optics give ``A_Sigma = 1`` and ``A_k = (1/2) P_k``, ``P_k`` the
   projector on the port's polarization ``psi_k`` (H, V, D, A). On the
   two-photon block, with ideal detectors, the no-click element vanishes and
   the single-click element of port ``k`` is ``(1/4) |psi_k psi_k><psi_k psi_k|``,
   both photons in mode ``psi_k`` with probability ``(1/2)^2``. In the
   occupation basis ``|2,0>, |1,1>, |0,2>`` of (H, V):

       HH = (1, 0, 0),  VV = (0, 0, 1),
       DD = (1/2, 1/sqrt2, 1/2),  AA = (1/2, -1/sqrt2, 1/2),

   so ``sum_k |psi_k psi_k><psi_k psi_k| = [[3/2,0,1/2],[0,1,0],[1/2,0,3/2]]``
   and

       M_mc^(=2) = 1 - (1/4) [[3/2,0,1/2],[0,1,0],[1/2,0,3/2]]
                 = [[5/8, 0, -1/8], [0, 3/4, 0], [-1/8, 0, 5/8]],

   eigenvalues ``1/2, 3/4, 3/4``. At efficiency ``eta`` on every port a
   multiclick needs both photons detected, so the block is ``eta^2`` times
   this matrix (rem:normalization-gain). The matrix is symmetric under the
   reversal ``|2,0> <-> |0,2>``, so the engine's ascending occupation order
   ``|0,2>, |1,1>, |2,0>`` gives the same matrix.

   * at ``eta = 1/5`` compiled at ``t = 1``: ``(1/25)`` times the matrix;
   * at ``eta = 1/5`` with ``t = eta_max = 1/5`` declared (the full
     normalization: every efficiency of the normalized station is one): the
     matrix itself;
   * at ``eta = 1/5`` by default (``t = 20/99``, item 0: every efficiency of
     the normalized station is ``(1/5)(99/20) = 99/100``): ``(99/100)^2 =
     9801/10000`` times the matrix;
   * the exact-window value at ``N = 1``, depth 2, is ``lambda_min`` of the
     block, ``1/2`` times the scale: ``(1/25)(1/2) = 1/50`` at ``t = 1``,
     ``1/2`` at the full normalization, and ``(9801/10000)(1/2) =
     9801/20000`` by default.

2. THE PULL-BACK ON THE ONE-PHOTON BLOCK (prop:efficiency-normalization (i)).
   ``Lambda^loss_t`` keeps a photon with probability ``t``, so on the
   one-photon block ``blk_1 M_S = t blk_1 M'_S + (1 - t) blk_0 M'_S``. For the
   single click ``{H}`` at ``eta = 3/5`` on every port, no dark counts:
   ``blk_1 M_{H} = (3/5)(1/2)|H><H| = (3/10)|H><H|``. The normalized station
   at the full normalization ``t = 3/5`` has every efficiency one,
   ``blk_1 M'_{H} = (1/2)|H><H|`` and ``blk_0 M'_{H} = 0``, and
   ``(3/5)(1/2) = 3/10``. By default ``t = 20/33`` (item 0), every efficiency
   ``(3/5)(33/20) = 99/100``, so ``blk_1 M'_{H} = (99/100)(1/2)|H><H| =
   (99/200)|H><H|`` and ``blk_0 M'_{H} = 0``; the pull-back is
   ``(20/33)(99/200) = 1980/6600 = 3/10``, the device's value again.

3. STATISTICS INVARIANCE (req:loss-before-evaluation; the open item's example).
   bbm92 with the ideal pair at visibility 47/50, arm transmittances
   ``(1/10, 1/1000)``, efficiencies ``3/5`` (Alice) and ``1/5`` (Bob) on every
   port, no dark counts, cutoff 1: each station is pure loss ``eta`` then an
   ideal station, so the honest law is that of transmittances
   ``(1/10 * 3/5, 1/1000 * 1/5) = (3/50, 1/5000)`` with efficiency one, and
   ``P(both detect) = (3/50)(1/5000) = 3/250000``; ``P(neither detects) =
   (47/50)(4999/5000) = 234953/250000``. None of this depends on ``t``: the
   law is the device's at every factor.

4. THE STATION THE DEFAULT NORMALIZES TO (cor:normalized-flat). By default
   (item 0) Alice's station is compiled at ``t = 20/33`` and Bob's at
   ``t = 20/99``, both at efficiency ``99/100`` on every port. The same law
   from stations DECLARED at ``99/100`` (whose default factor is ``1``) needs
   arm transmittances ``x`` with ``x (99/100)`` equal to the device's
   detection transmittances of item 3: ``x_A = (3/50)(100/99) = 300/4950 =
   2/33`` and ``x_B = (1/5000)(100/99) = 100/495000 = 1/4950``; equivalently
   ``x = (arm transmittance) t``: ``(1/10)(20/33) = 2/33`` and
   ``(1/1000)(20/99) = 1/4950``.
"""

from __future__ import annotations

from fractions import Fraction

__all__ = [
    "BOTH_DETECT",
    "DEFAULT_COMPILED_EFFICIENCY",
    "DEFAULT_FACTOR_ONE_FIFTH",
    "DEFAULT_FACTOR_THREE_FIFTHS",
    "DEFAULT_NORMALIZED_TRANSMITTANCES",
    "MULTICLICK_DEFAULT_SCALE",
    "MULTICLICK_TWO_PHOTON",
    "NEITHER_DETECTS",
    "NORMALIZED_TRANSMITTANCES",
    "ONE_PHOTON_H_DEFAULT",
    "ONE_PHOTON_H_DEVICE",
    "ONE_PHOTON_H_FULL",
    "WINDOW_DEFAULT",
    "WINDOW_FULL",
    "WINDOW_UNNORMALIZED",
]

F = Fraction

#: Item 0: the default factor at eta_max = 1/5, (1/5)(100/99).
DEFAULT_FACTOR_ONE_FIFTH: Fraction = F(20, 99)
#: Item 0: the default factor at eta_max = 3/5, (3/5)(100/99).
DEFAULT_FACTOR_THREE_FIFTHS: Fraction = F(20, 33)
#: Item 0: the efficiency a port at eta_max is compiled at by default.
DEFAULT_COMPILED_EFFICIENCY: Fraction = F(99, 100)

#: Item 1: ``M_mc^(=2)`` of the ideal receiver, in the basis |2,0>, |1,1>, |0,2>.
MULTICLICK_TWO_PHOTON: tuple[tuple[Fraction, ...], ...] = (
    (F(5, 8), F(0), F(-1, 8)),
    (F(0), F(3, 4), F(0)),
    (F(-1, 8), F(0), F(5, 8)),
)

#: Item 1: the scale of that block by default at eta = 1/5, (99/100)^2.
MULTICLICK_DEFAULT_SCALE: Fraction = F(9801, 10000)

#: Item 1: the exact-window value at n = 2 for eta = 1/5, compiled at t = 1.
WINDOW_UNNORMALIZED: Fraction = F(1, 50)
#: Item 1: the same at the full normalization t = 1/5: the station is ideal.
WINDOW_FULL: Fraction = F(1, 2)
#: Item 1: the same by default, t = 20/99: every port at 99/100.
WINDOW_DEFAULT: Fraction = F(9801, 20000)

#: Item 2: blk_1 of the single click {H} at eta = 3/5, as the coefficient of |H><H|.
ONE_PHOTON_H_DEVICE: Fraction = F(3, 10)
#: Item 2: the same at the full normalization, t = 3/5.
ONE_PHOTON_H_FULL: Fraction = F(1, 2)
#: Item 2: the same by default, t = 20/33: every port at 99/100.
ONE_PHOTON_H_DEFAULT: Fraction = F(99, 200)

#: Item 3: the transmittances the device's law equals at efficiency one.
NORMALIZED_TRANSMITTANCES: tuple[Fraction, Fraction] = (F(3, 50), F(1, 5000))
#: Item 3: the probability that both stations register a click.
BOTH_DETECT: Fraction = F(3, 250000)
#: Item 3: the probability that neither station registers a click.
NEITHER_DETECTS: Fraction = F(234953, 250000)

#: Item 4: the arm transmittances of stations declared at 99/100 with the law
#: of item 3, the stations the default normalizes the device to.
DEFAULT_NORMALIZED_TRANSMITTANCES: tuple[Fraction, Fraction] = (
    F(2, 33),
    F(1, 4950),
)
