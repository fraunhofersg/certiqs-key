"""Definition ``def:joint-family``: the classes, the weights, the joint POVM.

WHY THIS FILE EXISTS. ``def:joint-family`` makes the class decomposition a
DATUM -- the core normalizer acts per class and may not know that a class is a
probe setting -- so the two functions that produce it get a test of their own.

NOTHING FROZEN IS READ HERE. The weights and blocks below are chosen in this
file, because what is asserted is the DEFINITION's own content: the classes
partition the declared order of ``V``, the weights are the declared ``q_t``,
and ``M_{(y,t)} = q_t M~_{y|t}`` is a POVM by Lemma ``lem:linear`` (ii). The
frozen numbers of the weight route are asserted where they belong, in the
``wpfss`` goldens.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.exact import add, diagonal, equal, identity, zeros
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import ProbeDeclaration
from certiqs_key.reductions.joint import joint_classes, joint_family

PROBE = ProbeDeclaration(
    settings=("t0", "t1"), weights={"t0": F(2, 3), "t1": F(1, 3)}
)
#: ``y`` FASTEST AND ``t`` SLOWEST, which is the declared grouping the
#: alphabet-order row validates and this file consumes.
ORDER = (("a", "t0"), ("b", "t0"), ("a", "t1"), ("b", "t1"))


@pytest.mark.contract
def test_the_classes_partition_the_declared_order_of_v() -> None:
    """``V = bigsqcup_t V_t`` with ``q_t > 0`` and ``sum_t q_t = 1`` exactly."""
    classes = joint_classes(PROBE, ORDER)
    assert [group.label for group in classes] == ["t0", "t1"]
    assert [group.weight for group in classes] == [F(2, 3), F(1, 3)]
    assert sum((group.weight for group in classes), start=F(0)) == 1
    members = [member for group in classes for member in group.members]
    assert sorted(members) == sorted(ORDER)
    assert len(set(members)) == len(ORDER)
    # THE MEMBERS ARE IN THE DECLARED ORDER OF V, filtered to the class; the
    # order is a declared datum and is never constructed.
    assert classes[0].members == (("a", "t0"), ("b", "t0"))
    # ``names`` is what a member is called WITHIN its class -- the detection
    # letter -- which is what def:emitnorm (3) records as its designated
    # element.
    assert classes[0].names == ("a", "b")
    assert classes[1].names == ("a", "b")


@pytest.mark.contract
def test_a_setting_with_no_outcome_is_refused_rather_than_dropped() -> None:
    """No default is substituted for a missing datum."""
    with pytest.raises(MalformedInputError):
        joint_classes(PROBE, (("a", "t0"), ("b", "t0")))
    with pytest.raises(MalformedInputError):
        joint_classes(ProbeDeclaration(settings=(), weights={}), ORDER)


@pytest.mark.contract
def test_the_joint_family_is_a_povm_and_the_weights_are_inside_it() -> None:
    """``M_{(y,t)} = q_t M~_{y|t}``: a POVM by ``lem:linear`` (ii).

    "WHAT (ii) COSTS IS NOTHING -- the private variable never enters ``Q``: the
    target space is unchanged, no block is opened, and NO CONSTRAINT IS
    PRODUCED, the weights ``q_t`` being carried by the target effects
    themselves."
    """
    conditional = {
        ("a", "t0"): diagonal([F(1), F(0)]),
        ("b", "t0"): diagonal([F(0), F(1)]),
        ("a", "t1"): diagonal([F(1, 2), F(1, 2)]),
        ("b", "t1"): diagonal([F(1, 2), F(1, 2)]),
    }
    joint = joint_family(conditional, PROBE, ORDER)
    total = zeros(2)
    for outcome in ORDER:
        total = add(total, joint[outcome])
    assert equal(total, identity(2))
    # THE WEIGHT IS INSIDE THE ELEMENT and nothing free-standing is produced.
    assert equal(joint[("a", "t0")], diagonal([F(2, 3), F(0)]))
    assert equal(joint[("a", "t1")], diagonal([F(1, 6), F(1, 6)]))
    # And the per-class sum is q_t times the identity, which is what the
    # normalizer's step (3) restores.
    for group in joint_classes(PROBE, ORDER):
        accumulated = zeros(2)
        for member in group.members:
            accumulated = add(accumulated, joint[member])
        assert equal(accumulated, diagonal([group.weight, group.weight]))
