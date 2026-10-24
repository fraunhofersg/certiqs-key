"""The click-pattern POVM, block by photon number.

Definition ``def:clickalphabet`` and Theorem ``thm:click-povm``, in the prefactor form
of a setting family (Definition ``def:setting-family`` (b)), which also covers
the elements of a setting family a submodule constructs, so that nothing has
to be re-derived there.

WHAT THE OBJECT IS
==================
The joint no-click data of a receiver is, per port subset ``J``, a PAIR

    Pvac(J) = c_J Fock(1 - B_J)

-- Eq. ``eq:prefactorform``. Unconditioned (Theorem ``thm:click-povm`` (ii)) every
``c_J = 1`` and ``B_J = A_J``; at a setting a submodule constructs, conditioned
on a declared probe state, the pair carries a prefactor that is in general
not one and that a Gram cannot absorb, since ``c Fock(1 - A)`` is
``Fock(1 - A')`` for no ``A'`` unless ``c = 1``. :class:`NoClickFamily` is that
pair family, and every element below is built from it -- which is exactly
why a conditioned multiclick element needs no separate implementation.

POSITIVITY DOES NOT COME FROM THE ALTERNATING SUM
=================================================
Remark ``rem:positivity``: Eq. ``eq:incexc`` is an alternating sum of positive
operators and nothing about its form makes it positive -- the element of a
non-empty outcome ``S`` has ``2^|S|`` terms, half of them with a minus sign.
Positivity is established BEFORE the expansion, in Theorem
``thm:click-povm`` (i), from the physical construction of Definition
``def:physmodel`` -- ``K`` commuting binary projective measurements on disjoint
output mode sets, pulled back through an isometry. Nothing here re-derives it,
and nothing here clips a computed eigenvalue to enforce it: a computed block
that fails positivity is a DIAGNOSTIC failure reported through the residuals of
Definition ``def:residuals``, never a matrix quietly repaired.

WHAT THE BLOCK STRUCTURE IS, AND IS NOT
=======================================
Remark ``rem:blockmeaning``. The grading of Theorem ``thm:click-povm`` (iii) is by the
TOTAL photon number of the declared inputs; with a probe declared that is not
the CHANNEL photon number, and the channel grading is recovered only under a
condition on the probe state, which the submodule that conditions on it
states. The emitted low-photon blocks are operators on
the channel space and are NOT the compressions ``P(<=N) M_S P(<=N)``; "emitting
them is a decomposition of the physical POVM, never a squashing argument".
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations

import numpy as np

from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.fock import block_dimension, fock_block
from certiqs_key.receiver.grams import GramFamily
from certiqs_key.receiver.numerics import Matrix, identity

__all__ = [
    "NoClickFamily",
    "coarse_elements",
    "completeness_defect",
    "element_block",
    "emitted_photon_blocks",
    "multiclick_block",
    "multiclick_patterns",
    "no_click_block",
    "raw_alphabet",
    "single_click_block",
    "single_click_patterns",
    "subset_sum_blocks",
    "unconditioned_family",
]


def raw_alphabet(port_count: int) -> tuple[frozenset[int], ...]:
    """Return ``2^[K]``, the raw click alphabet of Def. ``def:clickalphabet``.

    Ordered by cardinality and then lexicographically, which is a presentation
    choice with no proof-relevant content: every statement about ``M_S`` is
    indexed by the SET ``S``, never by its position.
    """
    ports = range(port_count)
    return tuple(
        frozenset(combination)
        for size in range(port_count + 1)
        for combination in combinations(ports, size)
    )


def single_click_patterns(port_count: int) -> tuple[frozenset[int], ...]:
    """Return ``SC_K = {{k}}`` -- Eq. ``eq:mcsc``."""
    return tuple(frozenset({k}) for k in range(port_count))


def multiclick_patterns(port_count: int) -> tuple[frozenset[int], ...]:
    """Return ``MC_K = {S : |S| >= 2}`` -- Eq. ``eq:mcsc``."""
    return tuple(pattern for pattern in raw_alphabet(port_count) if len(pattern) >= 2)


@dataclass(frozen=True)
class NoClickFamily:
    """The joint no-click data ``{(c_J, B_J)}_{J subset of [K]}``.

    ``prefactors`` and ``effective_grams`` are keyed by the port subset. The
    operators act on ``C^Inp`` unconditioned and on ``C^{Inp_C}`` conditioned,
    and ``dimension`` is the dimension of that space.
    """

    port_count: int
    dimension: int
    prefactors: Mapping[frozenset[int], float]
    effective_grams: Mapping[frozenset[int], Matrix]

    def pair(self, ports: Iterable[int]) -> tuple[float, Matrix]:
        """Return ``(c_J, B_J)`` for a port subset."""
        key = frozenset(ports)
        if key not in self.prefactors:
            raise HypothesisError(
                f"the no-click family carries no subset {sorted(key)}"
            )
        return self.prefactors[key], self.effective_grams[key]

    def pi_vac_block(self, ports: Iterable[int], photons: int) -> Matrix:
        """Return ``Pvac(J)^{(n)} = c_J Fock(1 - B_J)^{(n)}``.

        Theorem ``thm:port-grams`` (iii) unconditioned, the prefactor form
        Eq. ``eq:family-prefactor`` at a setting a submodule constructs; the
        two are the same expression at ``c_J = 1``.
        """
        prefactor, gram = self.pair(ports)
        return np.asarray(
            prefactor * fock_block(identity(self.dimension) - gram, photons),
            dtype=np.complex128,
        )

    def block_dimension(self, photons: int) -> int:
        """Return the expected dimension of the ``n``-photon block."""
        return block_dimension(self.dimension, photons)


def unconditioned_family(family: GramFamily) -> NoClickFamily:
    """Return the no-click family of an unconditioned receiver.

    Theorem ``thm:click-povm`` (ii): ``Pvac(J) = Fock(1 - A_J)``, i.e. every prefactor
    is ``1`` and every effective Gram is the subset sum ``A_J``. Corollary
    ``cor:unconditioned-family`` makes it the setting family with
    ``B = A_Sigma``, ``B_k`` the subset sum over the other ports, and
    ``gamma = beta_k = 1``.
    """
    prefactors: dict[frozenset[int], float] = {}
    grams: dict[frozenset[int], Matrix] = {}
    for subset in raw_alphabet(family.port_count):
        prefactors[subset] = 1.0
        grams[subset] = family.subset(sorted(subset))
    return NoClickFamily(
        port_count=family.port_count,
        dimension=family.dimension,
        prefactors=prefactors,
        effective_grams=grams,
    )


def element_block(
    family: NoClickFamily, pattern: Iterable[int], photons: int
) -> Matrix:
    r"""Return ``blk M_S^{(=n)}`` by Eq. ``eq:incexc`` / Eq. ``eq:blockMS``.

        M_S = sum over T subset of S of (-1)^{|T|} Pvac(([K] \ S) union T)

    At ``n = 0`` this is ``delta_{S, empty}``: no photon, no click, by the
    binomial identity in the proof of Theorem ``thm:click-povm`` (iii).
    """
    clicked = frozenset(pattern)
    silent = frozenset(range(family.port_count)) - clicked
    size = family.block_dimension(photons)
    total = np.zeros((size, size), dtype=np.complex128)
    for count in range(len(clicked) + 1):
        for chosen in combinations(sorted(clicked), count):
            sign = -1.0 if count % 2 else 1.0
            total = total + sign * family.pi_vac_block(
                silent | frozenset(chosen), photons
            )
    return np.asarray(total, dtype=np.complex128)


def no_click_block(family: NoClickFamily, photons: int) -> Matrix:
    """Return ``blk M_nc^{(=n)} = Pvac([K])^{(n)}`` -- Eq. ``eq:Mnc``."""
    return family.pi_vac_block(range(family.port_count), photons)


def single_click_block(family: NoClickFamily, port: int, photons: int) -> Matrix:
    r"""Return ``blk M_{sc_k}^{(=n)}`` -- Eq. ``eq:Msc``.

    ``Pvac([K] \ {k}) - Pvac([K])``: "port every-other dark" minus "all dark".
    """
    others = frozenset(range(family.port_count)) - {port}
    return np.asarray(
        family.pi_vac_block(others, photons)
        - family.pi_vac_block(range(family.port_count), photons),
        dtype=np.complex128,
    )


def multiclick_block(family: NoClickFamily, photons: int) -> Matrix:
    r"""Return ``blk M_mc^{(=n)}`` -- Eq. ``eq:Mmc``, and Eq. ``eq:family-mc``.

        M_mc = 1 + (K - 1) Pvac([K]) - sum_k Pvac([K] \ {k})

    Remark ``rem:k-minus-1``: the coefficient is ``K - 1`` and not ``K`` because
    each single-click element already contains one subtraction of the all-dark
    element. An error by one in this coefficient changes the bound by
    ``gamma c^n``, a term that vanishes on every block ``n >= 1`` when ``c = 0``
    and survives when ``c > 0``: the error would be invisible in the first case
    and material in the second.
    """
    ports = range(family.port_count)
    size = family.block_dimension(photons)
    total = np.asarray(np.eye(size, dtype=np.complex128), dtype=np.complex128)
    total = total + (family.port_count - 1) * family.pi_vac_block(ports, photons)
    for port in ports:
        others = frozenset(ports) - {port}
        total = total - family.pi_vac_block(others, photons)
    return np.asarray(total, dtype=np.complex128)


def coarse_elements(family: NoClickFamily, photons: int) -> dict[str, Matrix]:
    """Return the ``K + 2`` coarse elements of Theorem ``thm:click-povm`` (iv).

    Keyed ``"nc"``, ``"sc_0"``..``"sc_{K-1}"`` and ``"mc"``. These are the
    operators ``interface.yaml`` ``outputs.photon_blocks`` emits after the declared
    coarse-graining, and they are the BARE blocks, before the dark-count
    channel: ``R`` is emitted separately and the consumer composes.
    """
    blocks: dict[str, Matrix] = {"nc": no_click_block(family, photons)}
    for port in range(family.port_count):
        blocks[f"sc_{port}"] = single_click_block(family, port, photons)
    blocks["mc"] = multiclick_block(family, photons)
    return blocks


def completeness_defect(family: NoClickFamily, photons: int) -> Matrix:
    """Return ``1 - sum_{S subset of [K]} blk M_S^{(=n)}`` -- Eq. ``eq:res4``.

    Summed over the RAW alphabet by Eq. ``eq:incexc``, NOT by taking the
    multiclick element to be the complement: the latter would make the residual
    identically zero by construction and would report nothing. The error this
    residual exists to catch is the implementation that enumerates the emitted
    letters and forgets that ``mc`` aggregates ``2^K - K - 1`` raw patterns.
    """
    size = family.block_dimension(photons)
    total = np.zeros((size, size), dtype=np.complex128)
    for pattern in raw_alphabet(family.port_count):
        total = total + element_block(family, pattern, photons)
    return np.asarray(np.eye(size, dtype=np.complex128) - total, dtype=np.complex128)


def emitted_photon_blocks(
    family: NoClickFamily, cutoff: int
) -> tuple[dict[str, Matrix], ...]:
    """Return the coarse blocks for every emitted ``n`` in ``0 <= n <= N``.

    ``interface.yaml`` ``parameters.photon_cutoff``: the cutoff ``N`` is a
    declared protocol parameter, not a numerical convenience; it fixes which
    blocks are emitted exactly, and THIS MODULE DOES NOT CHOOSE IT AND DOES NOT
    OPTIMIZE IT.
    """
    if cutoff < 0:
        raise HypothesisError("the photon cutoff N is non-negative")
    return tuple(coarse_elements(family, photons) for photons in range(cutoff + 1))


def subset_sum_blocks(
    family: NoClickFamily, patterns: Sequence[Iterable[int]], photons: int
) -> Matrix:
    """Return ``sum_{S in O} blk M_S^{(=n)}`` for a declared outcome set.

    The object Definition ``def:slot`` indexes the strengthening slot by, and
    the left-hand side of Theorem ``thm:coarse-graining`` (ii).
    """
    size = family.block_dimension(photons)
    total = np.zeros((size, size), dtype=np.complex128)
    for pattern in patterns:
        total = total + element_block(family, pattern, photons)
    return np.asarray(total, dtype=np.complex128)
