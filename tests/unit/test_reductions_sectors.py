"""The sector set's STRUCTURAL REFUSALS, and what they keep out.

Motivation: ``SectorSet.sectors_inside``'s refusal of a range that cuts a
sector block in half is the check that keeps
:meth:`~certiqs_key.reductions.sectors.SectorSet.block_projector` from being an
ambient construction, and the whole suite left it -- and the two refusals of
``__post_init__`` beside it -- unexecuted. A refusal path that never runs is one that
could be mis-wired without the suite noticing, which holds for the fail-closed rows and
for the same reason here.

WHAT IS ASSERTED HERE. That a range which is not a run of whole sectors is
refused naming the range, the block and the section that removed the ambient
form; that a run of whole sectors is not refused and IS the projector it names,
written out independently of the code; and that a sector set which is not one
is refused. Nothing here compares the code with itself.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.exact import Cx, identity, zeros
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.sectors import Sector, SectorKind, SectorSet


def _two_by_two() -> SectorSet:
    """Two data sectors of dimension two: ``dim H(Q) = 4``, offsets 0 and 2."""
    return SectorSet(
        sectors=(
            Sector(label=("C", "0"), dimension=2, kind=SectorKind.DATA),
            Sector(label=("C", "1"), dimension=2, kind=SectorKind.DATA),
        )
    )


@pytest.mark.contract
def test_a_range_that_cuts_a_sector_block_in_half_is_refused() -> None:
    """2.9: a range over a block list is A RUN OF WHOLE SECTORS or it is none.

    Acting on half a block entrywise is the ambient construction
    spec/architecture.md 2.9 removed, so the alignment decision refuses rather
    than returning an operator that is not a sum of sector projectors --
    ``block_projector`` reads it, so the refusal reaches every caller of the
    sums an instance transports and of an entry's ``Pi_b``.
    """
    sectors = _two_by_two()
    with pytest.raises(MalformedInputError) as raised:
        sectors.sectors_inside(0, 1)
    detail = str(raised.value)
    assert "[0, 1)" in detail and "[0, 2)" in detail
    assert "cuts the sector block" in detail
    assert "spec/architecture.md 2.9" in detail
    # The same refusal through the projector, and on a range that starts inside
    # one block and ends inside the next.
    with pytest.raises(MalformedInputError):
        sectors.block_projector(1, 2)
    with pytest.raises(MalformedInputError):
        sectors.block_projector(0, 3)


@pytest.mark.contract
def test_a_run_of_whole_sectors_is_the_projector_it_names() -> None:
    """The passing side of the same decision, written out independently.

    The expected blocks are written here rather than read back from the code:
    ``1_{d_s}`` on every sector inside the range and the zero block on every
    sector outside it, which is what ``Pi`` MEANS as a sector-block list.
    """
    sectors = _two_by_two()
    assert sectors.sectors_inside(0, 2) == (True, False)
    assert sectors.sectors_inside(2, 2) == (False, True)
    assert sectors.sectors_inside(0, 4) == (True, True)
    assert list(sectors.block_projector(2, 2)) == [zeros(2), identity(2)]
    assert list(sectors.block_projector(0, 4)) == [identity(2), identity(2)]
    # An empty range names the zero operator and is not a refusal: it covers no
    # sector, so it cuts none.
    assert sectors.sectors_inside(2, 0) == (False, False)
    assert list(sectors.block_projector(2, 0)) == [zeros(2), zeros(2)]
    # The blocks ARE what the definition says, entry for entry.
    one, nil = Cx(F(1), F(0)), Cx(F(0), F(0))
    assert sectors.block_projector(0, 2)[0] == ((one, nil), (nil, one))
    assert sectors.block_projector(0, 2)[1] == ((nil, nil), (nil, nil))


@pytest.mark.contract
def test_a_sector_set_that_is_not_one_is_refused() -> None:
    """``def:reduction-instance`` (I2): a target has sectors, and they are a SET.

    The two refusals of ``__post_init__``, unexecuted by the suite until now.
    The order IS the datum, so two sectors carrying the same ``(group, name)``
    would leave the emitted ``target_descriptor`` naming one sector twice and a
    consumer's sector-map comparison with nothing to distinguish them.
    """
    with pytest.raises(MalformedInputError) as empty:
        SectorSet(sectors=())
    assert "at least one sector" in str(empty.value)
    duplicate = Sector(label=("C", "0"), dimension=1, kind=SectorKind.DATA)
    with pytest.raises(MalformedInputError) as repeated:
        SectorSet(sectors=(duplicate, duplicate))
    assert "same (group, name)" in str(repeated.value)
