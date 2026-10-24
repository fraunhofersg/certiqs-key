"""The general-format reader takes a dense state in the A-first layout.

The general-format statistics functional must not read a DENSE state as the
contiguous direct sum of its joint blocks, while
:meth:`~certiqs_key.foundations.blocks.JointBlockOperator.dense` writes the A-FIRST
layout the ``subsystem_order`` convention fixes: the block at joint position ``(t, s)``
sits on the rows and columns ``(alice_start_t + a) * d_Q + start_s + l``. With one Alice
sector, or Alice sectors all of dimension 1, the two readings coincide; otherwise a
dense caller would get plausible wrong statistics and nothing would refuse.
:func:`certiqs_key.protocol_compiler.statistics._general_state_blocks` reads
the A-first layout.

THIS FILE PINS THE READER ITSELF, with no instance: a joint block operator with
two Alice sectors of dimensions ``(2, 1)`` and two measured sectors of
dimensions ``(1, 2)``, every entry a distinct non-zero exact number, read back
from its own ``dense()`` against a stand-in carrying the four fields the reader
reads off a :class:`~certiqs_key.protocol_compiler.CandidateDeclaration`, so
that removing a removable submodule, with the instance the fix was found on,
cannot remove the one test of a protocol_compiler fix; that instance's own
tests check its honest state end to end.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from typing import cast

import pytest

from certiqs_key.foundations.blocks import (
    BlockKind,
    JointBlockOperator,
    SectorStructure,
)
from certiqs_key.foundations.exact import Cx, Matrix
from certiqs_key.protocol_compiler import CandidateDeclaration
from certiqs_key.protocol_compiler.statistics import _general_state_blocks

ALICE_SECTORS = SectorStructure(
    labels=("a0", "a1"), dims=(2, 1), block_kind=BlockKind.PHYSICAL_SECTOR
)
Q_SECTORS = SectorStructure(
    labels=("q0", "q1"), dims=(1, 2), block_kind=BlockKind.PHYSICAL_SECTOR
)


@dataclass(frozen=True)
class _DeclarationStandIn:
    """The four fields ``_general_state_blocks`` reads off a declaration."""

    alice_sectors: SectorStructure
    sectors: SectorStructure

    @property
    def alice_dim(self) -> int:
        """Return ``d_A``, the sum of the Alice sector dimensions."""
        return self.alice_sectors.total_dim

    @property
    def q_dim(self) -> int:
        """Return ``d_Q``, the sum of the measured sector dimensions."""
        return self.sectors.total_dim


def _declaration() -> CandidateDeclaration:
    return cast(CandidateDeclaration, _DeclarationStandIn(ALICE_SECTORS, Q_SECTORS))


def _operator() -> JointBlockOperator:
    """Return the fixture: every entry of every joint block distinct and non-zero.

    Entry ``k`` (counted over the blocks in the joint order, row-major) is
    ``k + i / (k + 1)``, so no entry equals another and none equals the zero
    ``dense()`` writes off the blocks.
    """
    counter = iter(range(1, 1000))
    blocks: list[Matrix] = []
    for alice_dim in ALICE_SECTORS.dims:
        for q_dim in Q_SECTORS.dims:
            size = alice_dim * q_dim
            blocks.append(
                tuple(
                    tuple(
                        Cx(F(k), F(1, k + 1))
                        for k in (next(counter) for _ in range(size))
                    )
                    for _ in range(size)
                )
            )
    return JointBlockOperator.of(Q_SECTORS, ALICE_SECTORS, blocks)


def _contiguous_blocks(state: Matrix, dims: tuple[int, ...]) -> tuple[Matrix, ...]:
    """Return the DEFECTIVE reading: the dense array cut into contiguous blocks."""
    blocks: list[Matrix] = []
    start = 0
    for dim in dims:
        stop = start + dim
        blocks.append(tuple(tuple(row[start:stop]) for row in state[start:stop]))
        start = stop
    return tuple(blocks)


@pytest.mark.contract
def test_a_dense_state_is_read_back_to_its_own_blocks() -> None:
    """Definition ``def:phi``: one state, two presentations, one block list."""
    declaration = _declaration()
    operator = _operator()
    dense = operator.dense()
    assert len(dense) == 9
    assert _general_state_blocks(declaration, dense) == operator.blocks
    assert _general_state_blocks(declaration, operator) == operator.blocks


@pytest.mark.contract
def test_the_fixture_would_have_caught_the_contiguous_reading() -> None:
    """The comparison above is not vacuous at this fixture.

    Cutting the dense array into CONTIGUOUS joint blocks -- the defect -- gives
    a block list different from the operator's own, because an Alice sector of
    dimension 2 interleaves its rows with the other measured sector's.
    """
    operator = _operator()
    joint_dims = operator.joint_sectors().dims
    assert joint_dims == (2, 4, 1, 2)
    wrong = _contiguous_blocks(operator.dense(), joint_dims)
    assert wrong != operator.blocks
    assert _general_state_blocks(_declaration(), operator.dense()) != wrong
