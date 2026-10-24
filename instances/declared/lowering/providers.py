"""The drivers: a Band-A specification, or optical stations' providers.

Part of the lowering package (:mod:`instances.declared.lowering`): the last
layer, whose :class:`_Lowering` is the class :func:`~instances.declared.
lowering.lower` builds.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import TYPE_CHECKING

from certiqs_key.domain.constraints import (
    AttackSetLicense,
    ConstraintEntry,
)
from certiqs_key.foundations import exact
from certiqs_key.foundations.blocks import (
    BlockOperator,
    SectorStructure,
)
from certiqs_key.protocol_compiler.chain import (
    ReductionChain,
    Side,
    SystemDescriptor,
)
from certiqs_key.protocol_compiler.docking_reductions import dock_source_segment
from certiqs_key.protocol_compiler.spec import (
    DirectPovm,
    Party,
    ProtocolSpecification,
    PublicPart,
    ReceiverPart,
    SpecConstraints,
)
from certiqs_key.reductions import docking
from certiqs_key.reductions.docking import PartyLocalView
from certiqs_key.reductions.factors import (
    FactorCall,
    FactorEmission,
    assemble_factor_emissions,
)
from certiqs_key.reductions.inputs import outcome_label, probe_settings_of
from certiqs_key.reductions.wpfss import FlatInstanceBuilder
from certiqs_key.runs.pipeline import (
    DeviceEmission,
    MultiDeviceRequests,
    SpecificationProvider,
)
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.lowering.base import (
    _KIND,
    Lowered,
    _Constraints,
    _Optical,
    _Outcomes,
    _Source,
    _weighted_entry,
)
from instances.declared.lowering.honest import _HonestLowering

if TYPE_CHECKING:  # pragma: no cover - typing only
    from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
    from certiqs_key.reductions.artifact import ProofReductionArtifact
    from instances.common.honest import HonestContext


class _Lowering(_HonestLowering):
    """The state of one lowering: the document, the configuration's values."""

    # -- the drivers -----------------------------------------------------------

    def band_a(self) -> Lowered:
        """Lower a document whose stations are all declared POVMs (Band A).

        The chain carries no source segment: a ``wcp_decoy`` source, whose
        links would need one, is refused beside these stations at load
        (``wcp_decoy_needs_optical_stations``).
        """
        source = self.source()
        stations = [
            self.band_a_station(station, index)
            for index, station in enumerate(self.model.stations)
        ]
        parts: list[ReceiverPart] = []
        outcomes: list[_Outcomes] = []
        for index, lowered in enumerate(stations):
            station = lowered.station
            where = pointer("stations", index)
            receiver = lowered.receiver
            entries = lowered.outcomes
            weighting = self.weighting(station, entries, where)
            if weighting is not None:
                labels = tuple(entry.label for entry in entries)
                weighted = self.weighted_family(
                    station,
                    labels,
                    {
                        label: BlockOperator.of(
                            lowered.sectors, [lowered.elements[label]]
                        )
                        for label in labels
                    },
                    weighting,
                    where,
                )
                by_label = {entry.label: entry for entry in entries}
                entries = tuple(
                    _weighted_entry(
                        by_label[weighted.pairs[label][0]],
                        label,
                        weighted.pairs[label][1],
                    )
                    for label in weighted.alphabet
                )
                receiver = replace(receiver, choice_weighting=weighting)
            if self.multi:
                receiver = replace(
                    receiver, factor_label=station.id, chain=lowered.chain
                )
            parts.append(receiver)
            outcomes.append(_Outcomes(station.id, station.party, entries))
        factor_keys = (
            tuple(station.id for station in self.model.stations)
            if self.multi
            else ("s0",)
        )
        public, v_entries = self.public(source.entries, outcomes, factor_keys)
        block = self.constraints_block(docks=False)
        first = stations[0]
        alice = source.part.artifact.alice_sectors
        entries_, witness = self.user_constraints(block, first.sectors, alice)
        # ``auto`` on Band A is no witness: the library's witnesses are the
        # optical and multi-station constructions, and the qubit
        # instance declares none.
        specification = ProtocolSpecification(
            source=source.part,
            receiver=parts[0],
            further_receiver_factors=tuple(parts[1:]),
            public=public,
            sectors=first.sectors,
            chain=first.chain,
            constraints=SpecConstraints(
                entries=entries_,
                attack_set_license=block.licence,
                feasibility_witness=witness,
            ),
        )
        from instances.common.honest import StationFacts

        honest, raw, note, context = self.honest(
            self.source_facts(source),
            tuple(
                StationFacts(
                    id=lowered.station.id,
                    party=lowered.station.party,
                    kind="declared_povm",
                    dimension=lowered.receiver.physical_dim,
                )
                for lowered in stations
            ),
            source.labels,
            tuple(entry.label for entry in v_entries),
        )
        return Lowered(
            specification=specification,
            honest=honest,
            raw=raw,
            note=note,
            channel_interface=self.band_a_interface(stations),
            expansions=self.expansions,
            user_declared=self.user_declared,
            input_preparation=self.input_preparation,
            absent=self.absent,
            public=public,
            wcp_source=None if source.wcp is None else source.wcp.prepared,
            honest_context=context,
        )

    def optical(self) -> Lowered:
        """Lower a document whose stations are optical."""
        from instances.common.honest import StationFacts

        source = self.source()
        stations = [
            self.optical_station(station, index, source)
            for index, station in enumerate(self.model.stations)
        ]
        factor_keys = tuple(station.station.id for station in stations)
        public, v_entries = self.public(
            source.entries,
            [_Outcomes(s.station.id, s.station.party, s.entries) for s in stations],
            factor_keys,
        )
        block = self.constraints_block(docks=True)
        honest, raw, note, context = self.honest(
            self.source_facts(source),
            tuple(
                StationFacts(
                    id=s.station.id,
                    party=s.station.party,
                    kind="optical",
                    request=s.receiver.request,
                    choice_weighting=s.weighting,
                )
                for s in stations
            ),
            source.labels,
            tuple(entry.label for entry in v_entries),
        )
        channel = self.optical_interface(stations, source)
        lowered = Lowered(
            specification=None,
            honest=honest,
            raw=raw,
            note=note,
            channel_interface=channel,
            expansions=self.expansions,
            user_declared=self.user_declared,
            input_preparation=self.input_preparation,
            absent=self.absent,
            public=public,
            wcp_source=None if source.wcp is None else source.wcp.prepared,
            honest_context=context,
        )
        if not self.multi:
            lowered.device = stations[0].device
            lowered.specification_provider = self._one_station(
                source, stations[0], public, block
            )
            return lowered
        lowered.device = MultiDeviceRequests(
            devices=tuple(station.device for station in stations),
            specification_provider=self._several_stations(
                source, stations, public, block, context
            ),
            channel_interface_provider=self.bipartite_interface(stations),
        )
        return lowered

    def _check_alphabet(
        self, station: _Optical, emitted: Sequence[str], path: str
    ) -> None:
        """Hold the emitted alphabet against the one the tables were expanded over."""
        predicted = tuple(entry.label for entry in station.receiver.outcomes)
        if tuple(emitted) != predicted:
            raise DocumentError(
                f"the reductions emitted the outcome alphabet {list(emitted)}, "
                f"the lowering predicted {list(predicted)}; the rule tables would "
                "be over the wrong labels (a defect of the lowering, not of the "
                "document)",
                reason=DocumentReason.LOWERING_INCONSISTENT,
                path=path,
            )

    def _one_station(
        self,
        source: _Source,
        station: _Optical,
        public: PublicPart,
        block: _Constraints,
    ) -> SpecificationProvider:
        """Return the one-station provider: optical's and decoy's construction.

        The physical family is read off the target's preserved block
        (``reductions.docking.physical_family``); a source with links docks its
        segment; the reductions' entries and licence are docked unless
        ``docked: false``; the witness is the topology's or the
        document's own.
        """
        from instances.common.witness import below_cutoff, vacuum_output

        where = pointer("stations", 0)

        def build(
            receiver: ReceiverMeasurementArtifact, reduction: ProofReductionArtifact
        ) -> ProtocolSpecification:
            del receiver
            preserved = reduction.source_descriptor.channel_grading.preserved_dimension
            physical = SystemDescriptor(
                name="B", dim=preserved, side=Side.RECEIVER, sectors=None
            )
            target = docking.target_descriptor(reduction, sector_block_kind=_KIND)
            sectors = SectorStructure(
                labels=tuple(label for label, _ in target.sectors or ()),
                dims=tuple(dim for _, dim in target.sectors or ()),
                block_kind=_KIND,
            )
            chain = docking.reduction_chain(
                reduction, physical, sector_block_kind=_KIND
            )
            if source.part.source_links:
                chain = dock_source_segment(chain, source.part.source_links)
            flags = reduction.wpfss_data.flag_basis
            settings = probe_settings_of(flags)
            emitted = tuple(outcome_label(v, settings) for v in flags)
            self._check_alphabet(station, emitted, where)
            if station.weighting is not None:
                last = chain.receiver_segment[-1]
                assert last.target_alphabet is not None and last.target_povm is not None
                self.weighted_family(
                    station.station,
                    last.target_alphabet,
                    last.target_povm,
                    station.weighting,
                    where,
                )
            entries, witness = self.user_constraints(
                block, sectors, source.part.alice_sectors
            )
            docked_entries = (
                docking.constraint_entries(reduction, sector_block_kind=_KIND)
                if block.docked
                else ()
            )
            licence = self.joined_licence(
                docking.attack_set_license(reduction) if block.docked else None,
                block.licence,
            )
            if block.witness == "auto":
                witness = (
                    vacuum_output(source.part, sectors)
                    if source.part.source_links
                    else below_cutoff(source.part, sectors, preserved)
                )
            return ProtocolSpecification(
                source=source.part,
                receiver=ReceiverPart(
                    physical_dim=preserved,
                    physical_povm=DirectPovm(
                        alphabet=emitted,
                        elements=docking.physical_family(reduction, preserved),
                    ),
                    choice_weighting=station.weighting,
                    party=Party(station.station.party),
                ),
                public=public,
                sectors=sectors,
                chain=chain,
                constraints=SpecConstraints(
                    entries=(*docked_entries, *entries),
                    attack_set_license=licence,
                    feasibility_witness=witness,
                ),
            )

        return build

    def _several_stations(
        self,
        source: _Source,
        stations: Sequence[_Optical],
        public: PublicPart,
        block: _Constraints,
        context: HonestContext | None,
    ) -> Callable[[tuple[DeviceEmission, ...]], ProtocolSpecification]:
        """Return the several-station provider: bbm92's construction, generalised.

        Every station's chain is its own (``factor_scope`` its id); the factor
        emission is assembled from the stations' artefacts by the reductions
        (``assemble_factor_emissions``) where the document docks, and its
        scoped entries and joint licence are docked as the document's
        ``party_local_view`` reads them. A refused assembly is
        ``factor_assembly_refused``; a refused choice weighting
        ``choice_weighting_refused``. No station's chain carries
        a source segment: a ``wcp_decoy`` source, whose links would need one,
        is refused beside several stations at load
        (``wcp_decoy_needs_one_optical_station``).
        """
        from instances.common.witness import factor_uniform_below_cutoff

        ids = tuple(station.station.id for station in stations)
        view = PartyLocalView(block.view or PartyLocalView.OPERATOR)

        def build(emissions: tuple[DeviceEmission, ...]) -> ProtocolSpecification:
            if context is not None:
                context.set_emissions(emissions)
            reductions = tuple(emission.reduction for emission in emissions)
            combined: FactorEmission | None = None
            if block.docked:
                assembled = assemble_factor_emissions(
                    tuple(
                        FactorCall(emission.call, FlatInstanceBuilder(), _KIND, label)
                        for emission, label in zip(emissions, ids, strict=True)
                    ),
                    reductions,
                    declared_factor_order=ids,
                )
                if not isinstance(assembled, FactorEmission):
                    raise DocumentError(
                        "the reductions refused to assemble the stations' factor "
                        f"emission: {getattr(assembled, 'detail', assembled)}",
                        reason=DocumentReason.FACTOR_ASSEMBLY_REFUSED,
                        path="/stations",
                        module_reason=str(getattr(assembled, "reason", "")) or None,
                    )
                combined = assembled
            parts: list[ReceiverPart] = []
            chains: list[ReductionChain] = []
            for index, (emission, station) in enumerate(
                zip(emissions, stations, strict=True)
            ):
                where = pointer("stations", index)
                reduction = emission.reduction
                label = station.station.id
                preserved = (
                    reduction.source_descriptor.channel_grading.preserved_dimension
                )
                physical = SystemDescriptor(label, preserved, Side.RECEIVER, None)
                chain = docking.reduction_chain(
                    reduction,
                    physical,
                    target_name=label,
                    sector_block_kind=_KIND,
                    factor_scope=label,
                )
                chains.append(chain)
                last = chain.receiver_segment[-1]
                assert last.target_povm is not None and last.target_alphabet is not None
                self._check_alphabet(station, last.target_alphabet, where)
                if station.weighting is not None:
                    self.weighted_family(
                        station.station,
                        last.target_alphabet,
                        last.target_povm,
                        station.weighting,
                        where,
                    )
                data = reduction.source_descriptor.channel_grading.cutoff + 1
                parts.append(
                    ReceiverPart(
                        physical_dim=preserved,
                        physical_povm=DirectPovm(
                            alphabet=last.target_alphabet,
                            elements={
                                v: exact.direct_sum(member.blocks[:data])
                                for v, member in last.target_povm.items()
                            },
                        ),
                        choice_weighting=station.weighting,
                        party=Party(station.station.party),
                        factor_label=label,
                        chain=chain,
                    )
                )
            target = docking.target_descriptor(reductions[0], sector_block_kind=_KIND)
            sectors = SectorStructure(
                tuple(s for s, _ in target.sectors or ()),
                tuple(d for _, d in target.sectors or ()),
                _KIND,
            )
            entries, witness = self.user_constraints(
                block, sectors, source.part.alice_sectors
            )
            docked_entries: tuple[ConstraintEntry, ...] = ()
            docked_licence: AttackSetLicense | None = None
            if combined is not None:
                docked_entries = tuple(
                    docking.factor_constraint_entries(combined, party_local_view=view)
                )
                docked_licence = docking.factor_attack_set_license(
                    combined, party_local_view=view
                )
            if block.witness == "auto":
                witness = (
                    None
                    if combined is None or source.part.alice_dim != 1
                    else factor_uniform_below_cutoff(combined, reductions)
                )
            return ProtocolSpecification(
                source=source.part,
                receiver=parts[0],
                further_receiver_factors=tuple(parts[1:]),
                public=public,
                sectors=sectors,
                chain=chains[0],
                constraints=SpecConstraints(
                    entries=(*docked_entries, *entries),
                    attack_set_license=self.joined_licence(
                        docked_licence, block.licence
                    ),
                    feasibility_witness=witness,
                ),
            )

        return build
