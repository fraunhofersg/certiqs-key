"""``wpfss/prop:precomposed-blocks``: blocks supplied with the dark counts composed.

``wpfss/def:weight-route``, the two input forms: in the DARK-COMPOSED form the
supplied preserved blocks are the family the model takes below the cutoff
after the dark counts, step 1 is NOT applied to them again, and the datum is
step 2 alone. Part (ii) of the proposition: where no snap moved a block, the
flat instance formed from ``R^cg B`` in the dark-composed form and the one
formed from ``B`` in the bare form are ONE instance -- same handed datum, same
emission. The contract test below would fail if the dark-composed form
composed ``R^cg`` a second time, or if it read anything but the supplied
blocks below the cutoff.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from reductions_support import flat_call

from certiqs_key.foundations.exact import add, equal, scale, zeros
from certiqs_key.reductions.wpfss import reduce_flat
from certiqs_key.reductions.wpfss.weights import descend


@pytest.mark.contract
def test_the_dark_composed_form_is_the_same_instance_where_no_snap_moved_a_block() -> (
    None
):
    """Part (ii): ``A = q_t R^cg B`` in the bare form equals ``q_t B~`` in the other.

    THE FIXTURE, BY HAND. The flat fixture's blocks are sixteenths and
    thirty-seconds; its dark counts are ``p_1 = 3/16``, ``p_2 = 1/4``, so
    every entry of ``R^cg`` is a product of ``3/16, 13/16, 1/4, 3/4`` and a
    multiple of ``2^-6``. ``B~ = R^cg B`` therefore has denominators dividing
    ``2^11`` and is on the declared ``2^-12`` lattice, complete per block by the
    column-stochasticity of ``R^cg`` -- an exactly admissible declaration of
    its own. Supplying it in the dark-composed form must emit EXACTLY the
    bare form's artefact numbers: the same target, the same weights.
    """
    bare_call = flat_call()
    rows = bare_call.artifact_rows
    descended = descend(rows.dark_count_channel, rows.outcome_coarse_graining)
    composed = {}
    for letter, setting in rows.photon_blocks:
        blocks = []
        for index, dim in enumerate(rows.channel_grading.block_dimensions):
            total = zeros(dim)
            for column in descended.letters:
                coefficient = descended.value(letter, column)
                total = add(
                    total,
                    scale(coefficient, rows.photon_blocks[(column, setting)][index]),
                )
            blocks.append(total)
        composed[(letter, setting)] = tuple(blocks)
    dark_call = replace(
        bare_call,
        artifact_rows=replace(
            rows, photon_blocks=composed, photon_blocks_form="dark_composed"
        ),
    )
    bare = reduce_flat(bare_call)
    dark = reduce_flat(dark_call)
    assert bare.artifact is not None, bare.refusal
    assert dark.artifact is not None, dark.refusal
    for outcome, element in bare.artifact.target_povm.items():
        other = dark.artifact.target_povm[outcome]
        assert all(equal(a, b) for a, b in zip(element, other, strict=True)), outcome
    assert dark.artifact.wpfss_data == bare.artifact.wpfss_data
    # And composing a second time is NOT what the dark-composed form does: the
    # composed blocks read as BARE would be post-processed again and differ.
    twice = reduce_flat(
        replace(bare_call, artifact_rows=replace(rows, photon_blocks=composed))
    )
    assert twice.artifact is not None
    assert any(
        not all(
            equal(a, b)
            for a, b in zip(element, twice.artifact.target_povm[outcome], strict=True)
        )
        for outcome, element in bare.artifact.target_povm.items()
    )


@pytest.mark.contract
def test_a_form_outside_the_two_is_refused_as_no_block_structure() -> None:
    """The ``photon_blocks_form`` input row: ``bare | dark_composed``, else refused."""
    call = flat_call()
    outcome = reduce_flat(
        replace(
            call, artifact_rows=replace(call.artifact_rows, photon_blocks_form="raw")
        )
    )
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == "no_block_structure"
    assert "photon_blocks_form" in outcome.refusal.detail
