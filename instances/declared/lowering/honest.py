"""The honest layer: the library model and the channel interface.

Part of the lowering package (:mod:`instances.declared.lowering`).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.runs.pipeline import (
    DeviceEmission,
    HonestProvider,
    LossAppliedProvider,
    LossAppliedRawProvider,
    RawJointProvider,
    factored_loss_applied,
    raw_factored_loss_applied,
)
from certiqs_key.runs.surface import Kind
from certiqs_key.transmitter.decoy import WcpModel
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.lowering.base import (
    _BandA,
    _fraction,
    _Optical,
    _Source,
    _split,
    _topology,
)
from instances.declared.lowering.constraints import _ConstraintLowering
from instances.declared.model import (
    HonestAcceptanceTable,
    HonestEnvelope,
    HonestLibrary,
    HonestRawTable,
    ParamRef,
)
from instances.declared.values import unwrap

if TYPE_CHECKING:  # pragma: no cover - typing only
    from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
    from certiqs_key.runs.channel import ChannelInterface, SourceChannelInterface
    from certiqs_key.runs.pipeline import ChannelInterfaceProvider
    from instances.common.honest import HonestContext, SourceFacts, StationFacts


class _HonestLowering(_ConstraintLowering):
    """The honest layer: the library model, tables, the channel interface."""

    # -- the honest model ------------------------------------------------------

    def source_facts(self, source: _Source) -> SourceFacts:
        from instances.common.honest import SourceFacts

        wcp: WcpModel | None = None if source.wcp is None else source.wcp.tagged.model
        return SourceFacts(
            kind="wcp_decoy"
            if source.kind == "wcp_decoy"
            else "untrusted"
            if source.kind == "untrusted"
            else "trusted",
            alice_dim=source.alice_dim,
            alphabet=source.labels,
            wcp=wcp,
        )

    def honest(
        self,
        source: SourceFacts,
        stations: tuple[StationFacts, ...],
        x_labels: tuple[str, ...],
        v_labels: tuple[str, ...],
    ) -> tuple[
        HonestProvider, RawJointProvider | None, dict[str, Any], HonestContext | None
    ]:
        """Return the honest and raw providers, the note, and a library context."""
        from instances.common.honest import HonestContext, build
        from instances.common.honest.tables import (
            envelope_provider,
            raw_table_providers,
            table_provider,
        )

        node, path = unwrap(self.model.honest, self.env, "/honest")
        base: dict[str, Any] = {
            "instance": self.record_label,
            "module": "instances.declared",
            "overridden": False,
        }
        honest: HonestProvider
        raw: RawJointProvider | None = None
        context: HonestContext | None = None
        # Whether the providers' own marker may stand for every station: a
        # declared table is the device's statistics whatever stations it has.
        covered = True
        if isinstance(node, HonestLibrary):
            # ``station`` names the station a model describes where there are
            # several; without it the model is told every station.
            selected = (
                stations
                if node.station is None
                else tuple(s for s in stations if s.id == node.station)
            )
            context = HonestContext(
                instance=self.record_label,
                stations=selected,
                source=source,
                declared_tolerance=self.declared_tolerance,
            )
            bind: dict[str, Fraction | str] = {
                name: self._bound(value, path + pointer("bind", name))
                for name, value in node.bind.items()
            }
            built = build(node.library, bind, context)
            honest, raw, note = built.honest, built.raw, built.note
            covered = _covers_every_normalized_station(stations, selected)
        elif isinstance(node, HonestAcceptanceTable):
            table = {
                label: _fraction(
                    value, self.env, path + pointer("acceptance_table", label)
                )
                for label, value in node.acceptance_table.items()
            }
            honest = table_provider(table)
            note = {
                **base,
                "model": "honest acceptance table declared in the protocol document",
                "source": node.source,
            }
        elif isinstance(node, HonestRawTable):
            negative = sorted(
                key
                for key, value in node.raw_table.items()
                if _fraction(value, self.env, path + pointer("raw_table", key)) < 0
            )
            if negative:
                # The engine decides the AGGREGATED law (statistics refuses a
                # point that is not a distribution), and a raw table whose
                # negative entries cancel aggregates to a valid one; the
                # record would then carry a negative probability as the raw
                # table. An acceptance table and an envelope
                # reach statistics unaggregated, which refuses them itself.
                raise DocumentError(
                    f"a raw table holds probabilities; {negative} are negative",
                    reason=DocumentReason.HONEST_TABLE_INVALID,
                    path=path + pointer("raw_table", negative[0]),
                )
            joint = {
                _split(
                    key,
                    x_labels,
                    v_labels,
                    path + pointer("raw_table", key),
                    "raw-table",
                ): _fraction(value, self.env, path + pointer("raw_table", key))
                for key, value in node.raw_table.items()
            }
            honest, raw = raw_table_providers(joint)
            note = {
                **base,
                "model": "honest raw X x V table declared in the protocol document",
                "source": node.source,
            }
        else:
            assert isinstance(node, HonestEnvelope)
            lower = {
                label: _fraction(
                    value, self.env, path + pointer("envelope", "lower", label)
                )
                for label, value in node.envelope.lower.items()
            }
            upper = {
                label: _fraction(
                    value, self.env, path + pointer("envelope", "upper", label)
                )
                for label, value in node.envelope.upper.items()
            }
            honest = envelope_provider(lower, upper)
            note = {
                **base,
                "model": "honest envelope declared in the protocol document",
                "source": node.source,
            }
        # The document's own note fields are NESTED under ``document``,
        # never laid over the model's: the report prints this note, and a
        # document must not rewrite which model ran or whether it was
        # overridden. In place, because a library model's note is live (a
        # model may extend it at run time).
        if node.note:
            note["document"] = dict(node.note)
        # receiver/detector-imperfections/req:loss-before-evaluation: a library
        # model declares that it applies each station's factored loss, and a
        # declared table, raw table or envelope is the device's statistics as
        # the document gives them; both providers come back wrapped
        # (instances.common.honest.tables), and each wrapper is kept through
        # the guard below, which would otherwise hide it. A library model told
        # a subset of the stations declares the loss of those it was told
        # only, so its marker is kept only where every other station is at
        # t = 1; otherwise the run refuses factored_loss_not_applied.
        guarded = _guarded(honest)
        if covered and isinstance(honest, LossAppliedProvider):
            guarded = factored_loss_applied(guarded)
        guarded_raw = None if raw is None else _guarded(raw)
        if (
            covered
            and guarded_raw is not None
            and isinstance(raw, LossAppliedRawProvider)
        ):
            guarded_raw = raw_factored_loss_applied(guarded_raw)
        return guarded, guarded_raw, note, context

    def _bound(self, node: object, path: str) -> Fraction | str:
        """Return one bound model parameter: a number, or a choice's value.

        A ``{param: name}`` of a ``choice`` parameter binds that parameter's
        value, for a library model that takes a choice; every other node is a
        number.
        """
        if (
            isinstance(node, ParamRef)
            and node.port is None
            and self.env.kinds.get(node.param) is Kind.CHOICE
        ):
            return self.env.choice(node.param, path)
        return _fraction(node, self.env, path)

    def _honest_name(self) -> str:
        """Return the library model's name, where the honest model is one."""
        node, _ = unwrap(self.model.honest, self.env, "/honest")
        return node.library if isinstance(node, HonestLibrary) else "declared_table"

    # -- the channel interface -------------------------------------------------

    def _variant(self) -> str:
        node = self.model.channel_interface
        return "none" if node is None else node.variant

    def band_a_interface(
        self, stations: Sequence[_BandA]
    ) -> ChannelInterfaceProvider | None:
        variant = self._variant()
        if variant == "none":
            return None
        if variant == "qubit_identity":
            dims = [station.receiver.physical_dim for station in stations]
            if dims != [2]:
                raise _topology(
                    "qubit_identity describes one declared qubit receiver; this "
                    f"document declares stations of dimensions {dims}",
                    "/channel_interface/variant",
                )
            from instances.common.channel import qubit_identity

            provider: Callable[[Any], ChannelInterface] = qubit_identity
            return provider
        raise _topology(
            f"the channel interface {variant!r} describes an optical receiver; a "
            "declared_povm station takes qubit_identity or none",
            "/channel_interface/variant",
        )

    def optical_interface(
        self, stations: Sequence[_Optical], source: _Source
    ) -> ChannelInterfaceProvider | None:
        """Return the one-station route's channel-interface provider, or ``None``."""
        from instances.common.channel import mode_intensity, single_photon

        variant = self._variant()
        path = "/channel_interface/variant"
        if variant == "none":
            return None
        if variant == "bipartite" and self.multi:
            return None  # carried by MultiDeviceRequests; see bipartite_interface
        if self.multi or variant in ("qubit_identity", "bipartite"):
            raise _topology(
                f"the channel interface {variant!r} does not describe "
                f"{len(stations)} optical station(s): one station takes "
                "single_photon or mode_intensity, two take bipartite",
                path,
            )
        space = stations[0].receiver.space
        if variant == "single_photon":

            def photon(
                artifact: ReceiverMeasurementArtifact | None,
            ) -> ChannelInterface:
                return single_photon(artifact, modes=space)

            return photon
        wcp = source.wcp
        if wcp is None:
            raise _topology(
                "mode_intensity describes weak coherent pulses; it needs a "
                "wcp_decoy source",
                path,
            )
        intensities = wcp.tagged.model.intensities
        cutoff = wcp.tagged.source_cutoff

        def pulses(artifact: ReceiverMeasurementArtifact | None) -> Any:
            return mode_intensity(artifact, intensities, cutoff, modes=space)

        return pulses

    def bipartite_interface(
        self, stations: Sequence[_Optical]
    ) -> Callable[[tuple[DeviceEmission, ...]], SourceChannelInterface] | None:
        """Return the several-station route's channel interface (bbm92's), or none."""
        from certiqs_key.receiver.modes import ModeSpace
        from instances.common.channel import bipartite

        if self._variant() != "bipartite" or not self.multi:
            return None
        if len(stations) != 2:
            raise _topology(
                "the bipartite interface has two arms", "/channel_interface/variant"
            )
        node = self.model.channel_interface
        assert node is not None
        if node.source_model is None:
            source_model = self._honest_name()
        else:
            resolved, _ = unwrap(
                node.source_model, self.env, "/channel_interface/source_model"
            )
            source_model = str(resolved)
        # Each arm's modes are read by label from the stations' declared modes;
        # a label two stations both declare names one (path, polarization).
        # The label carries no tau, so where the two stations declare that
        # label at different tau the first station's tau is the one the
        # interface records (each receiver holds its own tau to one value; the
        # interface is a description, not a declaration a module decides).
        seen: dict[str, Any] = {}
        for station in stations:
            for mode in station.receiver.space.modes:
                seen.setdefault(mode.label, mode)
        modes = ModeSpace.declare(seen.values())
        parameters = dict(self.model_section)

        def interface(emissions: tuple[DeviceEmission, ...]) -> SourceChannelInterface:
            return bipartite(emissions, source_model, parameters, modes=modes)

        return interface


def _covers_every_normalized_station(
    stations: Sequence[StationFacts], selected: Sequence[StationFacts]
) -> bool:
    """Return whether every station a model was not told is at ``t = 1``.

    ``receiver/detector-imperfections/req:loss-before-evaluation``: a library
    model applies the factored loss of the stations in its context and of no
    other, so its marker stands for the run only where each station outside
    ``selected`` is compiled at ``t = 1``. A station with no receiver request
    (a declared POVM) compiles no receiver and is at one. A station whose
    declared factor the receiver will refuse is not known to be at one, and
    is counted as not covered; the device stage refuses it with
    ``efficiency_normalization_out_of_range`` before the marker is read.
    """
    told = {station.id for station in selected}
    for station in stations:
        if station.id in told or station.request is None:
            continue
        try:
            if station.factored_loss < 1:
                return False
        except HypothesisError:
            return False
    return True


def _guarded[F: Callable[..., Any]](provider: F) -> F:
    """Re-raise an honest model's arithmetic failure as ``honest_model_failed``.

    The one wrapped call site of the honest library: a builtin
    ``ArithmeticError`` from a model would otherwise escape the facade as an
    error rather than a coded refusal. No other exception is caught.
    """

    def call(*args: Any, **kwargs: Any) -> Any:
        try:
            return provider(*args, **kwargs)
        except ArithmeticError as failure:
            raise DocumentError(
                f"the honest model failed: {failure}",
                reason=DocumentReason.HONEST_MODEL_FAILED,
                path="/honest",
            ) from failure

    return call  # type: ignore[return-value]
