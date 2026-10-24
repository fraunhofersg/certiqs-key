"""How the transmitted system enters the receiver, as DATA of one shape.

To compute honest statistics for a channel of its own, a caller needs four
things: the source state and Alice's POVM are on the transmitter artefact,
Bob's POVM per photon number is on the receiver artefact's ``photon_blocks``,
and the map from raw outcome pairs to acceptance labels is on the compiled
declaration. The fourth -- **how the transmitted system A' enters the
receiver's channel input modes** -- would be known only inside each instance's
``honest.py``, so a caller would have to hardcode the encoding per instance.
That is exactly what the uniformity rule forbids.

WHAT IS HERE AND WHAT IS EXPLICITLY NOT
=======================================
Here: the SHAPE, and the reading of it. An instance fills it; the run tier
returns it from :func:`~certiqs_key.runs.pipeline.prepare` and writes it to the
record.

Not here, and not anywhere in this repository: **a channel model, a simulator
or a channel library**: a simulator is not within the scope of CERTIQS-KEY.
Composable noise channels, fibre-km-to-transmittance conversions and
detector presets live in the consumer. What stays here is each instance's own
honest model, unchanged, which a consumer uses as a cross-check oracle for
its simulator.

THE ONE SHAPE, ON EVERY INSTANCE
================================
An instance with a declared finite POVM and an identity link has no channel
modes and no photon cutoff: its ``A'`` IS the system the POVM is declared on,
so the encoding is the identity and ``channel_modes`` is ``None``. An instance
with a compiled receiver has both. **The keys are the same either way** -- an
absent stage sets its key to ``None`` and never uses a differently shaped one
-- so a consumer reads one record on both routes.

THE WHOLE MODE SPACE TRAVELS, NOT ONLY THE CHANNEL MODES
========================================================
Carrying the CHANNEL modes structured and nothing else would leave the other
modes of the same space -- ``X_H``, ``Xr_V`` and their siblings -- reaching a
consumer only as the label strings of the artefact's
``input_mode_space.mode_labels``, so a renderer could group the channel beams
by path and would have to draw the rest as unstructured rails.
:attr:`ChannelInterface.modes` is the whole declared space ``M`` with a
:class:`ModeRole` per mode, read off the artefact's own label lists, and
:attr:`ChannelInterface.channel_modes` is that list filtered -- one datum, so the two
cannot come to disagree about which mode is which.

THE BASIS ORDER IS THE TRAP, AND IT IS WHY THE LABELS TRAVEL
============================================================
``V`` and Bob's POVM must be read in ONE stated basis, and the receiver's Fock
basis is not the obvious one: occupation vectors are ordered ASCENDING
lexicographically, so on two modes the one-photon block is indexed
``[(0,1), (1,0)]`` -- the photon in the LAST mode first. Getting it backwards
produces a state that is still a state, still has the right marginal, and gives
the wrong error rate in one basis only, which is the hardest kind of mistake to
see. So :attr:`ChannelInterface.photon_blocks_basis` carries the labels IN THE
RECEIVER'S OWN ORDER and ``V``'s rows are in that order, and neither side has
to guess.

The COLUMN order is the same trap one axis over, and it has a guard rather
than a convention. ``V``'s columns are indexed in the artefact's
``channel_labels`` order, while :attr:`ChannelInterface.channel_modes` is
:attr:`ChannelInterface.modes` filtered and so inherits the ``mode_labels``
order -- two orders that Section 2.5 expects to agree and that
``receiver.modes.check_input_modes`` does not refuse for disagreeing. So
:func:`certiqs_key.runs.pipeline.run_slice` holds them against each other and
refuses the composition where they differ.

THE BLOCKS MAY BE A NORMALIZED STATION'S, AND THE FACTOR TRAVELS WITH THEM
==========================================================================
Where a receiver was compiled at its normalized station
(``receiver/detector-imperfections/req:efficiency-normalization``), its
``photon_blocks`` are not the device's: the device is the normalized station
after the pure-loss channel ``Lambda^loss_t`` of transmittance ``t`` on the
channel modes (``def:pure-loss``). A consumer that evaluated the blocks on its
channel's output ``rho`` would form the statistics of a receiver more
efficient than the device, so every interface that carries ``photon_blocks``
also carries that ``t`` as ``factored_loss``, read off the receiver
artefact's ``efficiency_record.normalization`` and written exactly, and the
consumer evaluates the blocks on ``Lambda^loss_t(rho)``
(``req:loss-before-evaluation``). At ``t = 1`` the channel is the identity.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Any

from certiqs_key.foundations.exact import Matrix, serialize_matrix
from certiqs_key.receiver.artifact import InputModeSpace

__all__ = [
    "BipartiteChannelInterface",
    "ChannelInterface",
    "ModeIntensityChannelInterface",
    "ModeRecord",
    "ModeRole",
    "OpticalChannelArm",
    "SourceChannelInterface",
    "mode_role",
]


class ModeRole(StrEnum):
    """What one declared mode of the receiver's mode space IS.

    THREE VALUES, AND THE MODE SPACE IS WHY IT IS NOT TWO. The receiver's
    ``input_mode_space`` key is ``Inp = Inp_C (disjoint union) Inp_S``, the
    channel/probe split of its INPUT modes -- and the declared mode space ``M``
    of Definition ``def:modes``, which the same artefact lists under
    ``mode_labels``, IS LARGER THAN ``Inp``. The optical BB84 instance declares
    eight modes of which exactly two are inputs; the other six are internal
    modes of the optical network that no input enters. A two-valued role would
    have to call those six something they are not, and calling them probe
    modes would be a plausible, wrong picture of the device -- which is the
    kind of mistake the structure exists to prevent, not to relabel.

    So :attr:`CHANNEL` and :attr:`PROBE` are the artefact's own two input
    lists, in the artefact's own words (the ``input_mode_space`` row calls it
    "the channel/probe split"), and :attr:`INTERNAL` is the rest of ``M``.

    THE THIRD SET IS THE CONTRACT'S OWN AND THIS NAMES IT RATHER THAN INVENTS
    IT. Definition ``def:instrument`` (ii) says of every mode of ``M`` that is
    not in ``Inp`` that it "carries vacuum at the input", and Assumption
    ``ass:vac`` (A-VAC) quantifies over exactly that set. So the category is
    receiver mathematics, and what is this tier's is only the WORD, chosen to
    match the consumers that call them internal modes.

    AND THE SET CONTAINS THE DETECTOR PORTS, which a renderer must know before
    it draws anything: ``def:instrument`` (iii) makes the ports pairwise
    disjoint subsets of ``M`` and NOT of ``Inp``, so on the optical BB84
    instance every one of the six internal modes (``X_H``, ``X_V``, ``Zr_H``,
    ``Zr_V``, ``Xr_H``, ``Xr_V``) is watched by a detector, each detector both
    polarizations of its path. ``internal`` therefore means "no input
    enters here", never "nothing happens here". The role is a rendering
    distinction and carries no mathematics of this tier's own.

    THE ROLE IS READ OFF THE ARTEFACT'S LISTS, NEVER OFF THE LABEL'S SPELLING.
    Parsing ``Xr_V`` for a leading ``X`` is exactly the guessing the structure
    exists to remove, and the two orders of the input split disagree exactly
    when a probe path label sorts before a channel one.
    """

    #: In ``channel_labels`` (``Inp_C``): the modes the channel acts on, and
    #: the modes the isometry ``V``'s columns are indexed by.
    CHANNEL = "channel"
    #: In ``source_labels`` (``Inp_S``): the probe-side input modes. EMPTY on a
    #: device that declares no probe source, which the optical BB84 instance
    #: does not.
    PROBE = "probe"
    #: In ``mode_labels`` and in neither input list: a mode of ``M`` that
    #: carries vacuum at the input (``def:instrument`` (ii), A-VAC). These are
    #: the modes an optics view calls internal and could otherwise only draw
    #: as unstructured rails, and they INCLUDE THE DETECTOR PORTS.
    INTERNAL = "internal"


def mode_role(label: str, space: InputModeSpace) -> ModeRole:
    """Return the role the ARTEFACT gives ``label``. One reading, in one place.

    An instance declaring the structured mode space calls this so that the
    role is read off the artefact's own lists and not off a label's spelling,
    and so that two instances cannot read the same split two ways. It is
    OFFERED AND NOT IMPOSED: an instance is free to decide the role itself, and
    :func:`certiqs_key.runs.pipeline.run_slice` holds whatever it declared
    against the artefact either way.

    Raises:
        KeyError: if ``label`` is not in the declared mode space at all. A
            default would put an invented role on a mode that does not exist.
    """
    if label not in space.mode_labels:
        raise KeyError(
            f"{label!r} is not in the declared mode space {list(space.mode_labels)}"
        )
    if label in space.channel_labels:
        return ModeRole.CHANNEL
    if label in space.source_labels:
        return ModeRole.PROBE
    return ModeRole.INTERNAL


@dataclass(frozen=True)
class ModeRecord:
    """One declared mode of the receiver's mode space, STRUCTURED.

    The declared mode space is carried as ``path``, ``polarization`` and
    ``tau`` and not only as a label string, so that a renderer groups beams by
    path without parsing labels. A label is presentation metadata; these three are the
    datum.
    """

    path: str
    polarization: str
    #: The temporal mode index of the receiver's own mode type.
    tau: int
    #: The receiver's own label for this mode, carried so that a reader can
    #: join to the receiver artefact without re-deriving the spelling.
    label: str
    #: Which half of the input split this mode is in. Defaulted to
    #: :attr:`ModeRole.CHANNEL`, the role every mode had when only channel modes
    #: were carried: the default states that fact and does not guess at a new
    #: one.
    role: ModeRole = ModeRole.CHANNEL

    def as_payload(self) -> dict[str, Any]:
        """Return the mode as JSON."""
        return {
            "path": self.path,
            "polarization": self.polarization,
            "tau": self.tau,
            "label": self.label,
            "role": str(self.role),
        }


@dataclass(frozen=True)
class ChannelInterface:
    """How ``A'`` enters the receiver, for one instance, as data.

    ``encoding`` is the ideal, LOSSLESS isometry ``V`` from ``A'`` into the
    space the receiver measures: exact entries, rows in
    :attr:`photon_blocks_basis`'s order where there is one and in
    :attr:`transmitted_basis`'s order where there is not, columns in
    :attr:`transmitted_basis`'s order. It is the IDEAL map and carries no loss
    and no noise: what a channel does to the encoded state is the channel's,
    and this is where the state enters.

    THE LOSS IN FRONT OF THE BLOCKS (``receiver/detector-imperfections/
    req:loss-before-evaluation``). :attr:`factored_loss` is the ``t`` the
    receiver was compiled at. The pure-loss channel ``Lambda^loss_t`` acts on
    the channel modes AFTER the channel and BEFORE ``photon_blocks`` are
    evaluated: a consumer evaluating the blocks on its channel's output
    ``rho`` evaluates them on ``Lambda^loss_t(rho)``, and on ``rho`` itself
    it would form the statistics of a more efficient receiver than the device.
    """

    #: ``dim H(A')``, as the transmitter artefact declares it.
    transmitted_dimension: int
    #: The basis labels of ``A'``, in the declared order.
    transmitted_basis: tuple[str, ...]
    #: EVERY declared mode of the receiver's mode space, structured and
    #: role-tagged, in the artefact's own ``mode_labels`` order -- or ``None``
    #: for an instance with a declared finite POVM, which has no mode space at
    #: all. See :attr:`channel_modes` for how it relates to that one.
    modes: tuple[ModeRecord, ...] | None
    #: ``N``, or ``None`` where there are no modes.
    photon_cutoff: int | None
    #: The Fock-basis labels of the receiver's ``photon_blocks``, in the
    #: receiver's own order, or ``None`` where there are none.
    photon_blocks_basis: tuple[str, ...] | None
    #: ``V``, exactly.
    encoding: Matrix
    #: The factored loss ``t`` of the receiver's
    #: ``efficiency_record.normalization``, exactly: ``Lambda^loss_t`` acts on
    #: the channel modes before :attr:`photon_blocks_basis`'s blocks are
    #: evaluated. ``None`` where no receiver is compiled (a declared finite
    #: POVM), which has no blocks for a loss to stand in front of.
    factored_loss: Fraction | None

    @property
    def channel_modes(self) -> tuple[ModeRecord, ...] | None:
        """The modes the channel acts on: :attr:`modes` in the channel role.

        A DERIVED VIEW AND NOT A SECOND FIELD. Were the internal modes of the
        mode space left to reach a consumer as bare label strings on
        ``receiver_artifact.input_mode_space.mode_labels``, an optics view
        could draw the channel rails by path and would have to draw the rest as
        unstructured rails. Carrying the
        whole space in one field and filtering it here means the two cannot
        disagree about which mode is which, which two fields would eventually
        do.

        ``None`` where there is no mode space, so the declared-finite-POVM
        route reads exactly as it did.
        """
        if self.modes is None:
            return None
        return tuple(mode for mode in self.modes if mode.role is ModeRole.CHANNEL)

    def as_payload(self) -> dict[str, Any]:
        """Return the interface as JSON, exact entries as ``"p/q"`` pairs.

        ``encoding`` goes through the exact substrate's own serializer, which
        has an inverse, so a consumer reads the isometry back without rounding.

        BOTH ``modes`` AND ``channel_modes`` ARE EMITTED, and the second is the
        first filtered. A consumer files on ``channel_modes`` --
        ``V``'s columns are indexed by those modes and by no others -- so
        dropping the key would break a reader to save a line. ``modes`` is the
        whole declared space, which is what an optics view needs.
        """
        return {
            "transmitted_system": {
                "dimension": self.transmitted_dimension,
                "basis": list(self.transmitted_basis),
            },
            "modes": (
                None
                if self.modes is None
                else [mode.as_payload() for mode in self.modes]
            ),
            "channel_modes": (
                None
                if self.channel_modes is None
                else [mode.as_payload() for mode in self.channel_modes]
            ),
            "photon_cutoff": self.photon_cutoff,
            "photon_blocks_basis": (
                None
                if self.photon_blocks_basis is None
                else list(self.photon_blocks_basis)
            ),
            "encoding": serialize_matrix(self.encoding),
            "factored_loss": _exact(self.factored_loss),
        }


@dataclass(frozen=True)
class OpticalChannelArm:
    """A station's physical mode space; the cutoff describes receiver evaluation.

    THE LOSS IN FRONT OF THE BLOCKS (``receiver/detector-imperfections/
    req:loss-before-evaluation``). :attr:`factored_loss` is the ``t`` this
    station's receiver was compiled at. The pure-loss channel
    ``Lambda^loss_t`` acts on this arm's channel modes before the station's
    ``photon_blocks`` are evaluated: a consumer evaluating them on the arm's
    input ``rho`` evaluates them on ``Lambda^loss_t(rho)``. Where ``rho`` is
    a joint state of both arms, the loss is ``id (x) Lambda^loss_t`` on this
    arm's factor, each arm with its own ``t``.
    """

    modes: tuple[ModeRecord, ...]
    photon_cutoff: int
    photon_blocks_basis: tuple[str, ...]
    #: The factored loss ``t`` of this station's receiver artefact
    #: (``efficiency_record.normalization``), exactly; ``1`` where the
    #: receiver was compiled at its declared efficiencies.
    factored_loss: Fraction

    @property
    def channel_modes(self) -> tuple[ModeRecord, ...]:
        """Read the declared channel-role subset in mode order."""
        return tuple(m for m in self.modes if m.role is ModeRole.CHANNEL)

    def as_payload(self) -> dict[str, Any]:
        """Serialize one station without merging its modes with another's."""
        return {
            "modes": [m.as_payload() for m in self.modes],
            "channel_modes": [
                m.as_payload() for m in self.modes if m.role is ModeRole.CHANNEL
            ],
            "photon_cutoff": self.photon_cutoff,
            "photon_blocks_basis": list(self.photon_blocks_basis),
            "factored_loss": _exact(self.factored_loss),
        }


@dataclass(frozen=True)
class ModeIntensityChannelInterface:
    """An optical source specified by modes and intensity."""

    arm: OpticalChannelArm
    intensities: Mapping[str, Fraction]
    source_cutoff: int
    source_model: str = "phase_randomized_weak_coherent_pulse"

    def as_payload(self) -> dict[str, Any]:
        """Record intensities exactly and keep the source cutoff explicit."""
        return {
            "source_shape": "mode_and_intensity",
            "source_model": self.source_model,
            "intensities": {key: str(value) for key, value in self.intensities.items()},
            "source_cutoff": self.source_cutoff,
            "arm": self.arm.as_payload(),
        }


@dataclass(frozen=True)
class BipartiteChannelInterface:
    """Two arms in station order, and the declared joint source model."""

    arms: tuple[OpticalChannelArm, OpticalChannelArm]
    source_model: str
    source_parameters: Mapping[str, Fraction]

    def as_payload(self) -> dict[str, Any]:
        """Record both arms in station order and the supplied source model."""
        return {
            "source_shape": "bipartite",
            "source_model": self.source_model,
            "source_parameters": {
                key: str(value) for key, value in self.source_parameters.items()
            },
            "arms": [arm.as_payload() for arm in self.arms],
        }


type SourceChannelInterface = (
    ChannelInterface | ModeIntensityChannelInterface | BipartiteChannelInterface
)


def _exact(value: Fraction | None) -> str | None:
    """Return a factored loss as its exact ``"p/q"`` (``"1"`` at one), or ``None``."""
    return None if value is None else str(value)
