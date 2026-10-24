"""Which frozen toy declarations ``meat-core`` 1.0.0 admits, and why the rest are not.

NEW AT 1.0.0, AND IT EXISTS BECAUSE THE AMENDMENT REFUSES A FROZEN TOY. Version
1.0.0 adds condition **(S)** to Definition ``def:optol`` -- the declared-order
completeness sum must round nowhere -- and puts the ``alice_povm_exact`` and
``alice_marginal_exact`` rows of Section 2.6 at exactly 0 with a round-nowhere
clause of their own. Those are conditions on the DECLARED NUMBERS that no
version before 1.0.0 stated, so a declaration frozen under an earlier version
can satisfy every condition that version had and fail one of these.

NOTHING FROZEN IS EDITED HERE. The toy declarations in ``tests/oracles`` are
byte-immutable evidence and this module changes none of them: it RECORDS which
of them the
1.0.0 admission rule refuses, with the reason and the arithmetic, so that a
consumer iterating the frozen list exercises its own subject on the
declarations the module admits and asserts the refusal on the others rather
than tripping over it.

THE ONE REFUSAL, AND IT IS THE CONTRACT'S OWN HAZARD RATHER THAN A DEFECT
========================================================================
``TOY-3(m=3)`` declares the fully dephased family with ``F_v^{(s0)} = [1/3]``
for three outcomes on a one-dimensional sector. ``1/3`` is not a binary64
number: the declared entry is
``fl(1/3) = 6004799503160661 / 2^54``, and

* the DECLARED-ORDER computed sum is ``fl(fl(fl(1/3) + fl(1/3)) + fl(1/3))``,
  which is EXACTLY ``1.0`` -- the first addition is exact and the second
  rounds UP by half an ulp;
* the REAL sum is ``3 * fl(1/3) = 1 - 2^-54``, which is NOT ``1``.

So under the 0.5.0 rule all three defects read zero and the family was
``exactly_admissible`` with a key length, while ``sum_v F_v != 1_Q`` of the
declared numbers -- the family is not a POVM, ``V_msm`` is not an isometry,
``Phi[omega]`` is not a probability vector, and by Lemma ``lem:optol-defined``
(iii) ``h_qkd`` is not defined for them. That is the hazard Definition
``def:optol`` exhibits at ``(1, 2^-60, 2^-60)``, instantiated in this
repository's own frozen evidence, and closing it is exactly what condition (S)
is for. The refusal is ``bob_povm_summation_rounds``, at EVERY ``tau_num``
including 0, and the frozen registry entry is ``O-BOB-POVM-SUMMATION-ROUNDS``.

WHAT IS *NOT* WITHDRAWN. Every frozen VALUE derived for ``TOY-3(m=3)`` --
``h_low = log2 3``, its sector classes, its Kraus operators -- is unchanged as
mathematics: those are statements about the real numbers ``1/3``, and the
registry derives them from the exhibited form and not from the binary64 data.
What 1.0.0 withdraws is this module's claim to compute them FROM THIS
DECLARATION, because the declaration's numbers are not the family the
derivation is about. The producer's remedy is the contract's own sentence:
"emit numbers whose defining sums close exactly in binary64, DYADIC ENTRIES
SUFFICING" -- which every other ``TOY-3(m)`` at a power-of-two ``m`` already
does, ``m = 2`` included.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

#: The frozen toy declarations the 1.0.0 admission rule REFUSES, mapping the
#: toy id to the machine-readable reason string. One entry, and the derivation
#: is in the module docstring above.
REFUSED_AT_1_0_0: Mapping[str, str] = {
    "TOY-3(m=3)": "bob_povm_summation_rounds",
}


def admitted[T](toys: Iterable[T]) -> tuple[T, ...]:
    """Return the toys 1.0.0 admits, in order, from a frozen list of records.

    Reads ``toy_id`` off each record. A caller that wants the refusals asserts
    them through :data:`REFUSED_AT_1_0_0` rather than by filtering silently:
    the refusal is a CONTRACT consequence and is tested as one.
    """
    return tuple(
        toy for toy in toys if getattr(toy, "toy_id", None) not in REFUSED_AT_1_0_0
    )


def admitted_ids(toy_ids: Iterable[str]) -> tuple[str, ...]:
    """Return the ids 1.0.0 admits, in order."""
    return tuple(toy_id for toy_id in toy_ids if toy_id not in REFUSED_AT_1_0_0)


def is_refused(toy: Any) -> bool:
    """Return whether this toy id or record is one 1.0.0 refuses."""
    identifier = toy if isinstance(toy, str) else getattr(toy, "toy_id", None)
    return identifier in REFUSED_AT_1_0_0
