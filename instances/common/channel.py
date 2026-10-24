"""How the transmitted system enters a receiver: the four channel-interface builders.

WHY THEY ARE SHARED. The builders serve the qubit
instance (the qubit identity), the optical one (the single-photon encoding),
the decoy one (the mode-and-intensity description) and bbm92 (the two-armed
one), and an instance written in Python may reuse any of them. A protocol
document chooses one of
them by name (``channel_interface: {variant: ...}``), so they live here:

- :func:`qubit_identity` -- ``A'`` IS the declared qubit, the isometry is the
  identity;
- :func:`single_photon` -- a single photon in one path's two polarization
  modes, read off the receiver artefact's own Fock basis order;
- :func:`mode_intensity` -- physical WCP modes and intensities, no finite
  encoding;
- :func:`bipartite` -- one optical arm per station of a pair source.

The structured modes (path, polarization, ``tau``) are the DECLARATION'S, not
parsed out of the artefact's label strings: ``modes`` is the declared mode
space, and it defaults to the common passive receiver's
(:func:`instances.common.optics.mode_space`), which is what every instance
declares today.

Every builder that carries a receiver's ``photon_blocks`` also carries that
receiver's factored loss ``t``, read off the artefact's own
``efficiency_record.normalization`` (:func:`_factored_loss`): the blocks are
the normalized station's where ``t < 1``, and a consumer evaluates them on
``Lambda^loss_t`` of its channel's output
(``receiver/detector-imperfections/req:loss-before-evaluation``).
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from certiqs_key.foundations.exact import identity, matrix
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.receiver.docking import DockingRefusal, receiver_artifact_rows
from certiqs_key.receiver.modes import ModeSpace
from certiqs_key.runs.channel import (
    BipartiteChannelInterface,
    ChannelInterface,
    ModeIntensityChannelInterface,
    ModeRecord,
    OpticalChannelArm,
    mode_role,
)
from certiqs_key.runs.pipeline import DeviceEmission
from instances.common.errors import OpticalDeviceError
from instances.common.optics import mode_space

__all__ = ["bipartite", "mode_intensity", "qubit_identity", "single_photon"]


def qubit_identity(
    receiver: ReceiverMeasurementArtifact | None = None,
) -> ChannelInterface:
    """Return how ``A'`` enters a declared qubit receiver: it IS the receiver.

    The simple route: a declared finite POVM
    and an explicit identity link, so there is no mode space to enter and no
    photon cutoff to enter it up to. ``A'`` is the qubit Bob's POVM is declared
    on, the isometry is the IDENTITY, and ``modes`` and
    ``photon_blocks_basis`` are ``None`` rather than absent -- one shape for
    every instance, an absent stage setting its key to null. ``None`` for the
    whole space is ``None`` for its channel half too, so ``channel_modes``
    reads exactly as it did before that field became a derived view.

    The argument is the receiver artefact a run built, and this builder
    IGNORES it: there is none on this route. It is in the signature because the
    surface is one shape on every instance, and a consumer calls it the same
    way either way.

    THE BASIS LABELS ARE THE DECLARATION'S OWN. ``|0>`` and ``|1>`` are the
    computational basis the BB84 instance states its four signal
    projectors in, and a consumer reads Alice's POVM and Bob's in the same one
    because there is only one.
    """
    return ChannelInterface(
        transmitted_dimension=2,
        transmitted_basis=("0", "1"),
        modes=None,
        photon_cutoff=None,
        photon_blocks_basis=None,
        encoding=identity(2),
        # No receiver is compiled on this route, so there are no blocks for a
        # factored loss to stand in front of.
        factored_loss=None,
    )


def single_photon(
    receiver: ReceiverMeasurementArtifact | None,
    *,
    modes: ModeSpace | None = None,
) -> ChannelInterface:
    """Return how the polarization qubit ``A'`` enters an optical receiver.

    THE ENCODING IS A SINGLE PHOTON IN THE CHANNEL PATH'S TWO POLARIZATION
    MODES: ``|H>`` is one photon in the first channel mode, ``|V>`` one photon
    in the second, and the ideal lossless isometry ``V`` maps the qubit into
    the one-photon block of the preserved Fock space. A caller computing
    statistics for a channel of its own needs it and could only have hardcoded
    it.

    ``V`` IS BUILT FROM THE RECEIVER'S OWN BASIS ORDER AND NOT FROM A
    CONVENTION WRITTEN HERE. The occupation vectors are ordered ascending
    lexicographically, so on two modes the one-photon block is indexed
    ``[(0,1), (1,0)]`` -- the photon in the LAST mode first -- and the column
    for ``|H>`` is found by LOOKING UP the vector with a one in the first
    channel mode rather than by counting. Getting that backwards gives a state
    that is still a state with the right marginal and the wrong error rate in
    one basis only.

    Raises:
        OpticalDeviceError: where no receiver artefact is supplied, or where
            the declared basis carries no single-photon vector for a channel
            mode. This encoding is ABOUT a constructed receiver and there is
            nothing to return without one.
    """
    if receiver is None:
        raise OpticalDeviceError(
            "the optical instance's channel interface is about a CONSTRUCTED "
            "receiver: it reads the declared mode space and the Fock basis "
            "order off the artefact, and there is no encoding without one"
        )
    rows = receiver_artifact_rows(receiver)
    if isinstance(rows, DockingRefusal):  # pragma: no cover - guarded upstream
        raise OpticalDeviceError(f"the receiver artefact does not dock: {rows.detail}")
    space = receiver.input_mode_space
    channel = space.channel_labels
    # THE STRUCTURED MODES ARE THE DECLARATION'S, read back from the declared
    # mode space rather than parsed out of the artefact's label strings: the
    # artefact carries the labels, which are presentation metadata, and the
    # declaration carries the (path, polarization, tau) triple, structured.
    declared = {mode.label: mode for mode in (modes or mode_space()).modes}
    basis = rows.occupation_basis_order
    cutoff = rows.bound_quantifier_domain.cutoff

    columns: list[int] = []
    for index, _label in enumerate(channel):
        wanted = tuple(
            "1" if position == index else "0" for position in range(len(channel))
        )
        if wanted not in basis:
            raise OpticalDeviceError(
                f"the declared Fock basis {list(basis)} carries no single-photon "
                f"vector for channel mode {index}; this encoding needs one"
            )
        columns.append(basis.index(wanted))

    dimension = len(basis)
    encoding = matrix(
        tuple(
            tuple(1 if row == columns[column] else 0 for column in range(len(channel)))
            for row in range(dimension)
        )
    )
    return ChannelInterface(
        transmitted_dimension=len(channel),
        # THE BASIS OF ``A'`` IS THE CHANNEL MODES' POLARIZATIONS, in the
        # receiver's own order, because that is what the qubit IS here: a
        # polarization degree of freedom on one path.
        transmitted_basis=tuple(str(declared[label].polarization) for label in channel),
        # THE WHOLE DECLARED SPACE ``M``, ROLE-TAGGED, and not the channel
        # modes alone. The role comes from the ARTEFACT'S OWN LABEL LISTS, so
        # nothing here reads a mode's spelling to decide what it is. ON THE
        # COMMON PASSIVE RECEIVER SIX OF THE EIGHT MODES ARE INTERNAL: it
        # declares no probe source, and its only two input modes are the
        # channel path's two polarizations.
        modes=tuple(
            ModeRecord(
                path=declared[label].path,
                polarization=str(declared[label].polarization),
                tau=declared[label].tau,
                label=label,
                role=mode_role(label, space),
            )
            for label in space.mode_labels
        ),
        photon_cutoff=cutoff,
        photon_blocks_basis=tuple(",".join(vector) for vector in basis),
        encoding=encoding,
        factored_loss=_factored_loss(receiver),
    )


def mode_intensity(
    receiver: ReceiverMeasurementArtifact | None,
    intensities: Mapping[str, Fraction],
    source_cutoff: int,
    *,
    modes: ModeSpace | None = None,
) -> ModeIntensityChannelInterface:
    """Describe physical WCP modes and intensities without a finite encoding."""
    if receiver is None:
        raise ValueError("the decoy channel interface requires its receiver artifact")
    rows = receiver_artifact_rows(receiver)
    if isinstance(rows, DockingRefusal):
        raise ValueError(rows.detail)
    declared = {mode.label: mode for mode in (modes or mode_space()).modes}
    space = receiver.input_mode_space
    arm = OpticalChannelArm(
        modes=tuple(
            ModeRecord(
                path=declared[label].path,
                polarization=str(declared[label].polarization),
                tau=declared[label].tau,
                label=label,
                role=mode_role(label, space),
            )
            for label in space.mode_labels
        ),
        photon_cutoff=rows.bound_quantifier_domain.cutoff,
        photon_blocks_basis=tuple(
            ",".join(vector) for vector in rows.occupation_basis_order
        ),
        factored_loss=_factored_loss(receiver),
    )
    return ModeIntensityChannelInterface(arm, intensities, source_cutoff)


def bipartite(
    emissions: tuple[DeviceEmission, ...],
    source_model: str,
    source_parameters: Mapping[str, Fraction],
    *,
    modes: ModeSpace | None = None,
) -> BipartiteChannelInterface:
    """Describe one optical arm per station of a two-station pair source."""
    arms = []
    declared_modes = {mode.label: mode for mode in (modes or mode_space()).modes}
    for emission in emissions:
        artifact = emission.receiver
        space = artifact.input_mode_space
        arms.append(
            OpticalChannelArm(
                modes=tuple(
                    ModeRecord(
                        declared_modes[label].path,
                        str(declared_modes[label].polarization),
                        declared_modes[label].tau,
                        label,
                        mode_role(label, space),
                    )
                    for label in space.mode_labels
                ),
                photon_cutoff=emission.call.declaration.photon_cutoff,
                photon_blocks_basis=tuple(
                    f"n={entry.photons}:"
                    + ",".join(str(v) for v in entry.occupation_vectors)
                    for entry in artifact.block_dimensions
                ),
                factored_loss=_factored_loss(artifact),
            )
        )
    return BipartiteChannelInterface(
        arms=(arms[0], arms[1]),
        source_model=source_model,
        source_parameters=source_parameters,
    )


def _factored_loss(receiver: ReceiverMeasurementArtifact) -> Fraction:
    """Return the factored loss ``t`` the receiver artefact records, exactly.

    ``receiver/detector-imperfections/req:normalization-record``: the factor
    is the artefact's own, so the interface cannot name a ``t`` other than
    the one the blocks were compiled at.
    """
    return receiver.efficiency_record.normalization.factored_loss
