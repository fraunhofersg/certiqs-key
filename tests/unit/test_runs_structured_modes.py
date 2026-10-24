"""The whole declared mode space travels structured, and the artefact holds it.

Carrying only CHANNEL modes as ``path``/``polarization``/``tau`` would leave the
internal modes -- ``X_H``, ``Xr_V`` and their siblings -- reaching a consumer as
the bare label strings of ``receiver_artifact.input_mode_space.mode_labels``,
and an optics view could group the channel beams by path but would have to
draw the rest as unstructured rails.

WHAT IS TESTED HERE AND WHY EACH ONE IS NEEDED.

1. The role is READ OFF THE ARTEFACT'S OWN LABEL LISTS and not off a label's
   spelling. This is the property the whole design rests on: ``Xr_V`` reads
   ``internal`` because the artefact lists it in ``mode_labels`` and in
   neither input list -- NOT because it starts with an X, and not ``probe``,
   which this instance has none of. A test that only checked "every mode has a
   role" would pass on an implementation that parsed the spelling.
2. ``channel_modes`` is a DERIVED view of ``modes``, so the two cannot come to
   disagree.
3. The run tier HOLDS THE TWO TOGETHER. The instance may declare the
   structured space, because the artefact has only labels and parsing one back
   is the guessing the structure exists to remove -- and the price is that an
   instance could declare a space the artefact does not have. That would draw
   rails of the right shape with the wrong content, which is the hardest kind
   of mistake to see, so it is a hard error and this is the test of it.
"""

from dataclasses import replace
from typing import Any

import pytest

from certiqs_key.receiver.artifact import InputModeSpace
from certiqs_key.runs.channel import (
    ChannelInterface,
    ModeRecord,
    ModeRole,
    mode_role,
)
from certiqs_key.runs.errors import SliceAssemblyError
from certiqs_key.runs.pipeline import Preparation, _check_declared_modes, prepare

pytestmark = pytest.mark.contract


def prepared() -> Preparation:
    """Return the optical instance's preparation, through its own surface."""
    from instances.optical_bb84.surface import default_config, preparation

    outcome = preparation(default_config())
    assert isinstance(outcome, Preparation), outcome
    return outcome


# ===========================================================================
#  1. The role is the artefact's split
# ===========================================================================


def test_every_declared_mode_travels_structured_and_not_as_a_label() -> None:
    """The mode space the artefact lists, in its order, with the triple on each.

    The assertion is against the ARTEFACT's ``mode_labels``, which is the
    authority on what the space is and on the order it is listed in.
    """
    outcome = prepared()
    interface = outcome.channel_interface
    artifact = outcome.receiver_artifact
    assert interface is not None
    assert artifact is not None
    assert interface.modes is not None

    labels = tuple(artifact.input_mode_space.mode_labels)
    assert tuple(mode.label for mode in interface.modes) == labels
    for mode in interface.modes:
        assert mode.path
        assert mode.polarization
        assert isinstance(mode.tau, int)


def test_the_role_of_each_mode_is_read_off_the_artefact_s_label_lists() -> None:
    """Read each role off the artefact's own three label lists.

    ``channel`` on ``channel_labels``, ``probe`` on ``source_labels``, and
    ``internal`` on a mode of ``M`` that is in neither.

    THE THIRD VALUE IS NOT A CONVENIENCE. This device declares eight modes and
    exactly TWO inputs: ``mode_labels`` is the mode space ``M`` of Definition
    ``def:modes`` and ``input_labels`` is ``Inp``, and ``M`` is the larger.
    Calling the other six probe modes would be a plausible and wrong picture of
    the device, so the assertion below is on all three values and on which
    labels get which.

    IT IS ALSO WHAT MAKES THE TEST ABLE TO FAIL: two roles are actually
    present here, and an implementation that returned one constant would pass
    a test that only checked "every mode has a role".
    """
    outcome = prepared()
    interface = outcome.channel_interface
    artifact = outcome.receiver_artifact
    assert interface is not None
    assert artifact is not None
    assert interface.modes is not None

    space = artifact.input_mode_space
    by_role: dict[ModeRole, set[str]] = {role: set() for role in ModeRole}
    for mode in interface.modes:
        by_role[mode.role].add(mode.label)

    assert by_role[ModeRole.CHANNEL] == set(space.channel_labels)
    assert by_role[ModeRole.PROBE] == set(space.source_labels)
    assert by_role[ModeRole.INTERNAL] == set(space.mode_labels) - set(
        space.input_labels
    )
    # This device: two channel modes, no probe source, six internal modes.
    assert by_role[ModeRole.CHANNEL]
    assert by_role[ModeRole.INTERNAL]
    assert not by_role[ModeRole.PROBE]


def test_the_internal_modes_are_the_ones_that_used_to_arrive_as_labels_only() -> None:
    """``X_H`` carries its path.

    Named rather than left implicit: with the string and nothing else, an
    optics view could not tell which rail ``Xr_V`` was on without parsing it.
    """
    outcome = prepared()
    interface = outcome.channel_interface
    assert interface is not None
    assert interface.modes is not None

    internal = [mode for mode in interface.modes if mode.role is ModeRole.INTERNAL]
    assert {mode.label for mode in internal} >= {"X_H", "Xr_V"}
    for mode in internal:
        assert mode.path
        assert mode.polarization in {"H", "V"}


# ===========================================================================
#  2. channel_modes is derived
# ===========================================================================


def test_channel_modes_is_the_channel_half_of_modes_and_not_a_second_field() -> None:
    """``channel_modes`` still means the modes ``V``'s columns index."""
    outcome = prepared()
    interface = outcome.channel_interface
    artifact = outcome.receiver_artifact
    assert interface is not None
    assert artifact is not None
    assert interface.channel_modes is not None

    assert tuple(mode.label for mode in interface.channel_modes) == tuple(
        artifact.input_mode_space.channel_labels
    )
    assert all(mode.role is ModeRole.CHANNEL for mode in interface.channel_modes)
    # The isometry's columns are indexed by these and by no others.
    assert len(interface.transmitted_basis) == len(interface.channel_modes)


def test_a_route_with_no_mode_space_reports_none_for_both() -> None:
    """The declared-finite-POVM route: one shape, the keys null and not absent."""
    from instances.bb84.surface import channel_interface

    interface = channel_interface()
    assert interface.modes is None
    assert interface.channel_modes is None
    payload = interface.as_payload()
    assert payload["modes"] is None
    assert payload["channel_modes"] is None


def test_the_payload_carries_the_role_and_survives_json() -> None:
    """A renderer reads the role off the record, not off the spelling."""
    import json

    outcome = prepared()
    interface = outcome.channel_interface
    assert interface is not None
    payload = interface.as_payload()
    assert json.loads(json.dumps(payload)) == payload
    assert {entry["role"] for entry in payload["modes"]} == {"channel", "internal"}
    assert {entry["role"] for entry in payload["channel_modes"]} == {"channel"}


def test_the_receiver_surface_of_a_preparation_carries_the_whole_space() -> None:
    """``stages.receiver_construction.modes`` is the space, not its channel half.

    This is the key the report asked for: "structured internal modes in the
    receiver payload".
    """
    from certiqs_key.runs.record import preparation_record

    payload = preparation_record(prepared())
    modes = payload["receiver_construction"]["modes"]
    assert modes is not None
    assert {entry["role"] for entry in modes} == {"channel", "internal"}


# ===========================================================================
#  3. The run tier holds the declaration against the artefact
# ===========================================================================


def _prepare_with(mangle) -> Any:  # noqa: ANN001
    """Return the optical preparation with its channel interface mangled.

    The device requests and the specification provider are the optical
    template's lowering, the provider at the merged-discard map.
    """
    from instances.optical_bb84.surface import channel_interface, default_config
    from tests.support.lowered_templates import MERGED_DISCARD, lowered

    config = default_config()
    lowering = lowered(
        "optical_bb84",
        config.with_(device={**config.device, "acceptance_map": MERGED_DISCARD}),
    )[1]
    assert channel_interface is not None

    def provider(artifact):  # noqa: ANN001, ANN202
        return mangle(channel_interface(artifact))

    return prepare(
        config,
        device=lowering.device,
        specification_provider=lowering.specification_provider,
        channel_interface_provider=provider,
    )


def test_a_declared_space_the_artefact_does_not_have_is_a_hard_error() -> None:
    """A dropped mode is a composition error, not a refusal.

    Neither module declined: the receiver emitted a well-formed artefact and
    the instance returned a well-formed interface. What disagrees is the
    composition, which is the run tier's (spec/architecture.md 3.3).
    """

    def drop_one(interface: ChannelInterface) -> ChannelInterface:
        assert interface.modes is not None
        return replace(interface, modes=interface.modes[1:])

    with pytest.raises(SliceAssemblyError, match="declared the mode space"):
        _prepare_with(drop_one)


def test_a_reordered_space_is_a_hard_error_too() -> None:
    """THE ORDER IS PART OF THE DATUM, because it is the artefact's own order.

    A consumer joining the structured modes to the artefact's ``mode_labels``
    by position would read every mode as a different one, and every value it
    drew would be plausible.
    """

    def reverse(interface: ChannelInterface) -> ChannelInterface:
        assert interface.modes is not None
        return replace(interface, modes=tuple(reversed(interface.modes)))

    with pytest.raises(SliceAssemblyError, match="declared the mode space"):
        _prepare_with(reverse)


def test_a_mode_given_the_wrong_role_is_a_hard_error() -> None:
    """The role is read off the split; declaring it otherwise is caught.

    This is the assertion that stops a future instance from deciding a role
    from a label's spelling and being believed.
    """

    def flip_a_role(interface: ChannelInterface) -> ChannelInterface:
        assert interface.modes is not None
        first, *rest = interface.modes
        flipped = (
            ModeRole.PROBE if first.role is not ModeRole.PROBE else ModeRole.CHANNEL
        )
        return replace(interface, modes=(replace(first, role=flipped), *rest))

    with pytest.raises(SliceAssemblyError, match="with role"):
        _prepare_with(flip_a_role)


def test_nothing_is_checked_where_there_is_no_mode_space() -> None:
    """A ``None`` space on the direct route is checked against nothing.

    The guard must not turn the route that HAS no mode space into an error, so
    the case is asserted rather than assumed.
    """
    from fractions import Fraction

    from instances.bb84.specification import bb84_specification
    from instances.bb84.surface import channel_interface

    from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
    from certiqs_key.runs import RunConfig

    half = Fraction(1, 2)
    config = RunConfig(
        rounds=2_000,
        completeness_budget=Fraction(1, 1_000_000),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        declared_tolerance=0.0,
        model={"qber": Fraction(1, 50)},
    )
    outcome = prepare(
        config,
        specification=bb84_specification(half, half, half, half),
        channel_interface_provider=lambda _artifact: channel_interface(),
    )
    assert isinstance(outcome, Preparation)
    assert outcome.channel_interface is not None
    assert outcome.channel_interface.modes is None


def test_a_mode_record_defaults_to_the_channel_role() -> None:
    """The default states a fact and does not guess at one.

    A mode built without a role is a channel mode, which is why the defaulted
    field is correct for every construction site that names no role.
    """
    mode = ModeRecord(path="Z", polarization="H", tau=0, label="Z_H")
    assert mode.role is ModeRole.CHANNEL
    assert mode.as_payload()["role"] == "channel"


def test_a_probe_input_reads_as_probe_and_not_as_internal() -> None:
    """The second value, which no instance in the tree declares.

    ``by_role[PROBE] == set(space.source_labels)`` above is
    ``set() == set()`` on the only instance with a mode space, so swapping the
    ``PROBE`` and ``INTERNAL`` returns of :func:`mode_role` would change
    nothing the suite saw. This declares a probe
    source directly, and declares it on a label that SORTS BEFORE the channel
    one -- the case :func:`mode_role`'s own docstring names as the one where
    the two orders of the input split disagree, and which nothing else builds.
    """
    space = InputModeSpace(
        mode_labels=("A_H", "Z_H", "Z_V"),
        # Inp_C before Inp_S, which is NOT the mode-space order here: the
        # receiver's subsystem_order convention takes precedence where the two
        # disagree.
        input_labels=("Z_H", "A_H"),
        channel_labels=("Z_H",),
        source_labels=("A_H",),
    )
    assert mode_role("Z_H", space) is ModeRole.CHANNEL
    assert mode_role("A_H", space) is ModeRole.PROBE
    assert mode_role("Z_V", space) is ModeRole.INTERNAL


def test_the_channel_half_is_in_the_artefact_s_own_channel_order() -> None:
    """The isometry's columns and the derived view must index the same modes.

    ``channel_modes`` is a derived view. That attribute is
    :attr:`ChannelInterface.modes` FILTERED, so it is in the artefact's
    ``mode_labels`` order; ``transmitted_basis`` and the columns of ``V`` are
    built in its ``channel_labels`` order. ``check_input_modes`` decides range,
    disjointness and non-emptiness and NOT that ``Inp_C`` ascends in ``M``, so
    the two CAN disagree on an artefact nothing refuses -- and a consumer
    reading ``V`` against ``channel_modes`` would then swap two polarizations,
    which is a state with the right marginal and the wrong error rate in one
    basis only.
    """
    outcome = prepared()
    artifact = outcome.receiver_artifact
    interface = outcome.channel_interface
    assert artifact is not None
    assert interface is not None
    space = artifact.input_mode_space
    assert tuple(mode.label for mode in interface.channel_modes or ()) == tuple(
        space.channel_labels
    )

    # AND THE GUARD CATCHES THE CASE THE RECEIVER DOES NOT REFUSE: a channel
    # block declared in the other order. The artefact is well formed and the
    # interface is well formed; what disagrees is the composition.
    reversed_channel = tuple(reversed(space.channel_labels))
    mangled = replace(
        artifact,
        input_mode_space=InputModeSpace(
            mode_labels=space.mode_labels,
            input_labels=reversed_channel + space.source_labels,
            channel_labels=reversed_channel,
            source_labels=space.source_labels,
        ),
    )
    with pytest.raises(SliceAssemblyError, match="channel_labels"):
        _check_declared_modes(interface, mangled)


def test_the_role_reading_refuses_a_label_outside_the_declared_space() -> None:
    """A default would put an invented role on a mode that does not exist."""
    outcome = prepared()
    artifact = outcome.receiver_artifact
    assert artifact is not None
    with pytest.raises(KeyError, match="not in the declared mode space"):
        mode_role("not_a_mode", artifact.input_mode_space)
