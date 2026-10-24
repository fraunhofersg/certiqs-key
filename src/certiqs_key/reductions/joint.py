"""Definition ``def:joint-family``: the joint alphabet, its classes, its weights.

WHAT THE DEFINITION SAYS. For each setting ``t`` of a finite ``T`` a
conditional POVM ``{M~_{y|t}}_y`` and lattice weights ``q_t > 0`` with
``sum_t q_t = 1`` exactly; the JOINT FAMILY is ``M_{(y,t)} = q_t M~_{y|t}`` on
``V = Y x T`` (a POVM by Lemma ``lem:linear`` (ii)); the CLASSES are
``V_t = Y x {t}``; ``T`` is a singleton with ``q = 1`` when no private setting
is declared.

WHAT (ii) COSTS IS NOTHING -- "the private variable never enters ``Q``: the
target space is unchanged, no block is opened, and NO CONSTRAINT IS PRODUCED,
the weights ``q_t`` being carried by the target effects themselves". That is the
structural reason no ``fixed_fraction`` test-statistics model is admitted: the
setting enters as a WEIGHT INSIDE the POVM elements, so no free-standing
fraction exists to emit.

WHAT IS NOT HERE. :func:`joint_family` is step 2 of "what the receiver
artifact is consumed for". Step 1 -- the dark-count post-processing ``R^cg`` --
and the weight route are the ``wpfss`` submodule's
(:mod:`certiqs_key.reductions.wpfss.weights`), because they are about one
squasher's device model, while the classes and the weights are what ANY
protocol with a private setting has.

:func:`joint_classes` serves the core normalizer, which acts per class, so the
class decomposition is a datum and not a pair of loops over ``Y`` and ``T``;
nothing about it is decided here,
the declared order of ``V`` being consumed exactly as declared.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from certiqs_key.foundations.exact import Matrix, scale
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import JointOutcome, ProbeDeclaration
from certiqs_key.reductions.normalizer import JointClass

__all__ = ["joint_classes", "joint_family"]


def joint_classes(
    probe: ProbeDeclaration, joint_alphabet: Sequence[JointOutcome]
) -> tuple[JointClass, ...]:
    """Return ``V = bigsqcup_t V_t`` with its exact weights, in the declared order.

    The members of each class are taken FROM THE DECLARED ORDER of ``V``,
    filtered to that setting, so the order within a class is the declared one
    and nothing is constructed: "THE ORDER IS A DECLARED DATUM AND IS
    VALIDATED, NEVER CONSTRUCTED". The alphabet-order row decides that the
    declared ``V`` is the product ``Y x T`` in the grouping the notation fixes;
    this function consumes the result.

    ``names`` is the member's name within its class -- the detection letter
    ``y`` of ``v = (y, t)`` -- which is what ``def:emitnorm`` (2) and (3)
    record as a host.
    """
    if not probe.settings:
        raise MalformedInputError("T is finite and NON-EMPTY")
    classes: list[JointClass] = []
    for setting in probe.settings:
        members = tuple(v for v in joint_alphabet if v[1] == setting)
        if not members:
            raise MalformedInputError(
                f"the declared setting {setting!r} carries no outcome of V"
            )
        classes.append(
            JointClass(
                label=setting,
                weight=probe.weights[setting],
                members=members,
                names=tuple(v[0] for v in members),
            )
        )
    return tuple(classes)


def joint_family(
    family: Mapping[JointOutcome, Matrix],
    probe: ProbeDeclaration,
    joint_alphabet: Sequence[JointOutcome],
) -> dict[JointOutcome, Matrix]:
    """``M_{(y,t)} := q_t M~_{y|t}`` on ``V = Y x T``.

    Licensed by Lemma ``lem:linear`` (ii): it is a POVM by
    ``sum_{y,t} q_t M~_{y|t} = sum_t q_t 1 = 1``.

    ``joint_alphabet`` is the DECLARED order of ``V`` and is used as given; see
    :class:`certiqs_key.reductions.inputs.ProtocolDeclaration` for why the order
    is consumed and never constructed.
    """
    return {
        outcome: scale(probe.weights[outcome[1]], family[outcome])
        for outcome in joint_alphabet
    }
