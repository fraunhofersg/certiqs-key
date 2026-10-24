"""Support dimensions and the acceptance support -- what (H-SUPP) is measured against.

Each function answers a question ``frank-wolfe/thm:firstorder`` asks; neither
belongs to the certificate chain, which is not built (PRINCIPLES.md section
10).

* ``ambient_branch_dimension`` is ``d_{chat,s} = dim H(R XY C_A C_B A Q_s)`` of
  Eq. ``eq:Wcs``, a property of the DECLARATION alone -- the ambient space the
  branch operator lives on, which is NOT the reference (H-SUPP) compares
  against: that is ``dim W_{chat,s}``, :func:`branch_support_dimension`.
* ``acceptance_support`` is ``Chat_acc`` of Eq. ``eq:chacc-def``, which Lemma
  ``lem:fo-khyp`` makes the index set hypothesis (H-POS) is STATED ON -- "and
  not on ``Chat``, because on ``Chat`` it would be UNSATISFIABLE whenever
  ``Chat_acc`` is a proper subset, a case def:admissible-acceptance-set admits".

NO PERTURBATION GOES WITH THEM. Remark ``rem:fo-nopert``
records that the perturbation route is CLOSED -- "with that band gone,
the phrase `after an explicit perturbation` in Theorem ``thm:gradient`` (ii) HAS
NO ACCOUNTED INSTANCE anywhere in this contract" -- and (H-NOPERT) forbids a
perturbation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from certiqs_key.meat_core.acceptance.geometry import minimal_acceptance_support
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.objective.linalg import (
    FACTOR_SUPPORT_CUTOFF,
    SUPPORT_CUTOFF,
    Matrix,
    factor_support,
)


def ambient_branch_dimension(declaration: ProtocolDeclaration, sector: str) -> int:
    """Return ``d_{chat,s} = dim H(R XY C_A C_B A Q_s)`` of Eq. ``eq:Wcs``.

    Factor by factor, and each is a property of the DECLARATION alone:

    * ``R`` carries the raw-key alphabet ``Z_perp = Z u {perp}``, so
      ``dim R = d_Z + 1``;
    * ``XY`` carries the outcome pair, so ``dim XY = |X| |V|``;
    * ``C_A C_B`` carries the announcement, so
      ``dim C_A C_B = |C_A| |C_B|`` -- the declared alphabets, not the realized
      classes;
    * ``A`` and ``Q_s`` carry the input block, ``d_A d_s``.
    """
    key_values = declaration.key_value_count + 1
    pairs = len(declaration.alice_outcomes) * len(declaration.bob_outcomes)
    classes = len(set(declaration.announce_alice.values())) * len(
        set(declaration.announce_bob.values())
    )
    return key_values * pairs * classes * declaration.block_dim(sector)


def acceptance_support(declaration: ProtocolDeclaration) -> tuple[str, ...]:
    """Return ``Chat_acc``, the acceptance support of Eq. ``eq:chacc-def``.

    It is the union of the supports of every ``q`` in ``AcceptSet``, the minimal
    choice of a support, and it is what is taken, in both geometries: the
    support of the one declared vector for a ``singleton``, and the coordinates
    whose maximum over the set is positive for a ``polytope``. A superset would
    be conforming -- the frozen ``PMIN-box-support-superset`` case is built to
    say so, and to say the minimum is the same either way -- but a smaller
    ``Chat_acc`` leaves fewer hypotheses to certify rather than more.
    """
    return minimal_acceptance_support(declaration)


@dataclass(frozen=True)
class BranchSupport:
    """``dim W_{chat,s}`` and the band count beside it, from ONE decomposition.

    Both are read off the singular values of the Kraus stack of Eq.
    ``eq:Kstack``, relative to the largest one:

    * ``dimension`` counts those above ``sqrt(support_cutoff)``
      (:data:`~certiqs_key.meat_core.objective.linalg.FACTOR_SUPPORT_CUTOFF`):
      the right side of Eq. ``eq:hsupp-check``;
    * ``band`` counts those in ``(support_cutoff, sqrt(support_cutoff)]``:
      directions of ``ran K`` that a ``sigma`` window at ``support_cutoff``
      would have counted and that ``rank X`` counts only at an input ``J``
      with ``cond(J) > support_cutoff / sigma_rel^2``, since they enter
      ``X`` with weight ``sigma^2``. A DIAGNOSTIC AND NOTHING READS IT: it is
      recorded so that a reader of a run sees where the one-ruler reading of
      ``frank-wolfe/rem:fo-one-ruler`` set a direction aside -- the second
      exposure ``frank-wolfe/rem:fo-check-exposures`` names, which no claim
      bounds.
    """

    dimension: int
    band: int


def branch_support(kraus_stack: Sequence[Matrix]) -> BranchSupport:
    """Return ``dim W_{chat,s}`` and the band count of one Kraus stack.

    ONCE PER PAIR ``(chat, s)``, FROM THE DECLARATION AND ``W_tau``, AND NOT
    FROM ANY ITERATE. That is what makes it a reference: an iterate-dependent
    reference would move with the thing it is the reference for.

    ONE RULER FOR BOTH SIDES OF Eq. ``eq:hsupp-check``
    (``frank-wolfe/rem:fo-one-ruler``). ``X`` is
    ``K (1 (x) J) K^dagger``, so a direction of ``ran K`` with singular value
    ``sigma`` enters ``X`` with weight ``sigma^2`` times an eigenvalue of
    ``J``; ``rank X`` counts eigenvalues at ``support_cutoff``, so ``dim W`` is
    read at ``sqrt(support_cutoff)`` on ``sigma`` -- which is the
    ``support_cutoff`` row read on ``X(1) = K K^dagger`` and no number of its
    own. Reading the reference at ``support_cutoff`` on ``sigma`` (the
    ``branch_support_dim`` row, not carried) would make a direction with
    ``sigma`` between the two windows fail the comparison at every iterate.

    THE ERROR IS ONE-SIDED AND ON THE UNSAFE SIDE IN ONE DIRECTION ONLY. A
    TOO-SMALL value passes a rank-deficient block: the second exposure of
    Remark ``rem:fo-check-exposures``, a genuine direction whose relative
    weight in ``X(1)`` is at most ``support_cutoff`` not being counted. A
    value computed too LARGE can only fail the comparison, which withdraws
    ``h_lb``.

    Args:
        kraus_stack: the operators of Eq. ``eq:Kstack`` for one ``(chat, s)``.
    """
    if not kraus_stack:
        return BranchSupport(dimension=0, band=0)
    # SIDE BY SIDE, WHICH IS WHAT Eq. eq:Kstack WRITES AND WHAT ITS RANK IS
    # ABOUT. K_{chat,s} maps the DIRECT SUM over kappa of H(A_0 Q_s) into the
    # one ambient space, so its matrix is the blocks in a ROW and
    # eq:Kstack-rank reads dim W = rank K = dim(sum_kappa ran K_kappa V). A
    # COLUMN stack has the rank of the sum of the blocks' ROW spaces instead,
    # a different number and one capped by the common column count -- while
    # dim W may be as large as |K_pass(chat)| dim S_adm d_s.
    stacked = np.hstack(
        [np.asarray(block, dtype=np.complex128) for block in kraus_stack]
    )
    values = np.linalg.svd(stacked, compute_uv=False)
    kept = factor_support(values)
    dimension = int(np.count_nonzero(kept))
    if values.size == 0 or float(values[0]) == 0.0:
        return BranchSupport(dimension=dimension, band=0)
    above_cutoff = values > SUPPORT_CUTOFF * float(values[0])
    band = int(np.count_nonzero(above_cutoff & ~kept))
    return BranchSupport(dimension=dimension, band=band)


def branch_support_dimension(kraus_stack: Sequence[Matrix]) -> int:
    """Return ``dim W_{chat,s}`` as the numerical rank of the Kraus stack.

    The right side of Eq. ``eq:hsupp-check``, read at ``sqrt(support_cutoff)``
    relative to the stack's largest singular value; :func:`branch_support`
    says why and returns the band count beside it.
    """
    return branch_support(kraus_stack).dimension


def support_band_report(
    bands: Mapping[tuple[str, Any], int], key_inert: Mapping[tuple[str, Any], bool]
) -> dict[str, Any]:
    """Return the ``map_validation_report`` entry of the band counts.

    Per KEY-ACTIVE pair ``(chat, s)`` -- the pairs (H-SUPP) is asked of -- the
    number of directions of ``ran K_{chat,s}`` whose singular value lies in
    ``(support_cutoff, sqrt(support_cutoff)]`` relative to the largest: the
    directions the one-ruler reading of ``frank-wolfe/rem:fo-one-ruler``
    leaves out of ``dim W_{chat,s}``. Computed with the reference, once per
    run and never per iterate. A DIAGNOSTIC: it decides nothing and bounds
    nothing; a positive count says where the second exposure of
    ``frank-wolfe/rem:fo-check-exposures`` could
    sit.
    """
    pairs: dict[str, dict[str, int]] = {}
    for (chat, pair), count in bands.items():
        if key_inert[(chat, pair)]:
            continue
        pairs.setdefault(str(chat), {})[str(pair)] = int(count)
    return {
        "support_cutoff": SUPPORT_CUTOFF,
        "factor_support_cutoff": FACTOR_SUPPORT_CUTOFF,
        "relative_to": "the largest singular value of the pair's Kraus stack",
        "pairs": pairs,
        "note": (
            "per key-active pair, the directions of ran K whose singular value "
            "lies in (support_cutoff, sqrt(support_cutoff)] relative to the "
            "largest: not counted in dim W under rem:fo-one-ruler, and no "
            "rank of X counts them either. Diagnostic only; decides nothing"
        ),
    }
