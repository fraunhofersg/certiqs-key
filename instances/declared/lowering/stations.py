"""The stations layer: Band-A and optical stations, weightings.

Part of the lowering package (:mod:`instances.declared.lowering`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from certiqs_key.foundations.blocks import (
    BlockKind,
    BlockOperator,
    SectorStructure,
)
from certiqs_key.protocol_compiler.chain import (
    Side,
    SystemDescriptor,
    band_a_chain,
)
from certiqs_key.protocol_compiler.reasons import Refusal
from certiqs_key.protocol_compiler.spec import (
    DirectPovm,
    Party,
    PublicChoices,
    ReceiverPart,
)
from certiqs_key.protocol_compiler.weights import (
    ChoiceWeighting,
    setting_joint_label,
    setting_weighted_family,
    weighted_family,
)
from certiqs_key.runs.pipeline import Station as RunStation
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.lowering.base import (
    _DECLARED,
    _BandA,
    _fraction,
    _Optical,
    _Source,
    _split,
    _weighted_entry,
)
from instances.declared.lowering.source import _SourceLowering
from instances.declared.model import (
    DeclaredPovm,
    Optical,
    Reduction,
    Station,
)
from instances.declared.optical import (
    KIND_OF_SOURCE,
    device_requests,
    receiver_request,
)
from instances.declared.rules import Entry, Variable
from instances.declared.values import unwrap

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass


class _StationLowering(_SourceLowering):
    """The stations layer: Band-A and optical stations, choice weightings."""

    # -- a station's choice weighting -------------------------------------------

    def weighting(
        self, station: Station, outcomes: Sequence[Entry], where: str
    ) -> ChoiceWeighting | None:
        """Return the station's ``ChoiceWeighting``, or ``None``.

        ``setting_of`` is a rule table over the station's outcomes (``v``);
        ``matrix`` is keyed ``"setting|choice"``.
        """
        node = station.choice_weighting
        if node is None:
            return None
        path = where + "/choice_weighting"
        expansion = self.expand(
            self.table_name(station, "setting_of"),
            node.setting_of,
            [Variable("v", tuple(outcomes))],
            path + "/setting_of",
        )
        settings, choices = tuple(node.settings), tuple(node.choices)
        weights: dict[tuple[str, str], Fraction] = {}
        for key, value in node.matrix.items():
            at = path + pointer("matrix", key)
            setting, choice = _split(key, settings, choices, at, "choice-weighting")
            weights[(setting, choice)] = _fraction(value, self.env, at)
        return ChoiceWeighting(
            choice_alphabet=choices,
            setting_alphabet=settings,
            setting_of={row.key[0]: str(row.value) for row in expansion.rows},
            matrix=weights,
        )

    @staticmethod
    def weighted_entries(
        outcomes: Sequence[Entry], weighting: ChoiceWeighting
    ) -> tuple[Entry, ...]:
        """Return the weighted family's labels, each ``v``'s components and ``choice``.

        The support is decided by the sign of each entry, ``v`` in the declared
        order and the choices in theirs (``setting_weighted_family``'s order):
        the alphabet the compiler emits for the station.
        """
        entries: list[Entry] = []
        for entry in outcomes:
            setting = weighting.setting_of.get(entry.label)
            for choice in weighting.choice_alphabet:
                if (
                    setting is not None
                    and weighting.matrix.get((setting, choice), 0) > 0
                ):
                    entries.append(
                        _weighted_entry(
                            entry, setting_joint_label(entry.label, choice), choice
                        )
                    )
        return tuple(entries)

    def weighted_family(
        self,
        station: Station,
        alphabet: Sequence[str],
        family: Mapping[str, BlockOperator],
        weighting: ChoiceWeighting,
        where: str,
    ) -> Any:
        """Run ``setting_weighted_family``, refusing ``choice_weighting_refused``."""
        weighted = setting_weighted_family(alphabet, family, weighting)
        if isinstance(weighted, Refusal):
            raise DocumentError(
                f"the compiler refused station {station.id!r}'s choice weighting: "
                f"{weighted.detail}",
                reason=DocumentReason.CHOICE_WEIGHTING_REFUSED,
                path=where + "/choice_weighting",
                module_reason=str(weighted.reason),
            )
        return weighted

    # -- a Band-A station --------------------------------------------------------

    def band_a_station(self, station: Station, index: int) -> _BandA:
        """Return a Band-A station's receiver part, outcomes, sectors and chain."""
        where = pointer("stations", index)
        measurement = station.measurement
        assert isinstance(measurement, DeclaredPovm)
        reduction, reduction_path = unwrap(
            station.reduction, self.env, where + "/reduction"
        )
        assert isinstance(reduction, Reduction)
        self._identity_reduction(reduction, reduction_path)
        party = Party(station.party)
        dimension = measurement.dimension
        povm: PublicChoices | DirectPovm
        if measurement.choice_family is not None:
            povm = self.choices(
                measurement.choice_family, party, where + "/measurement/choice_family"
            )
            family = weighted_family(povm)
            labels = tuple(family.alphabet)
            elements = dict(family.elements)
            joint = povm.joint_labels or {}
            components = {
                label: {"choice": choice, "outcome": outcome}
                for (outcome, choice), label in joint.items()
            }
            outcomes = tuple(Entry.of(label, components.get(label)) for label in labels)
        else:
            assert measurement.povm is not None
            elements = {
                label: self.matrix(node, where + pointer("measurement", "povm", label))
                for label, node in measurement.povm.items()
            }
            labels = tuple(elements)
            povm = DirectPovm(alphabet=labels, elements=elements)
            outcomes = tuple(Entry.of(label) for label in labels)
        kind = BlockKind.PROOF_SECTOR
        sectors = SectorStructure(labels=("s0",), dims=(dimension,), block_kind=kind)
        target = SystemDescriptor(
            station.id if self.multi else "Q",
            dimension,
            Side.RECEIVER,
            (("s0", dimension),),
            kind,
        )
        # The Band-A chain of def:banda (b), carrying its target alphabet, the
        # target POVM as one-block lists and the identity correspondence on
        # V = V^ph (instances/bb84/specification.py _band_a_chain).
        chain = band_a_chain(target)
        link = replace(
            chain.receiver_segment[0],
            target_alphabet=labels,
            target_povm={
                label: BlockOperator.of(sectors, [elements[label]]) for label in labels
            },
        )
        chain = replace(
            chain,
            receiver_segment=(link,),
            outcome_correspondence={label: label for label in labels},
        )
        self.flag(
            "receiver_povm",
            where + "/measurement",
            station.id,
            f"The measurement of station {station.id!r}, declared as a POVM. "
            f"{_DECLARED} The premise is that these matrices describe the "
            "receiver you have, performed in every round on that round's system "
            "alone, whatever happens in the other rounds (A-SPEC). The Band-A "
            "route the engine takes for a declared POVM rests on A-IDEAL: an ideal "
            "qubit measurement, on a transmitted system that is exactly a qubit, "
            "with unit efficiency, no loss, no dark counts, no multi-photon "
            "events and no misalignment. If "
            "your receiver is not such a measurement, A-IDEAL fails and the key "
            "length does not apply to it; declare it as an optical station "
            "(kind: optical) instead (instances/declared/README.md).",
        )
        receiver = ReceiverPart(physical_dim=dimension, physical_povm=povm, party=party)
        return _BandA(station, receiver, outcomes, sectors, chain, elements)

    def _identity_reduction(self, reduction: Reduction, path: str) -> None:
        """Refuse a declared_povm reduction that is not the identity link alone.

        ``{links: [{kind: identity}]}`` and nothing else. Every
        other field must keep its default: a value written there would have no
        effect on the Band-A chain, and a field accepted and dropped is a
        declaration the run silently ignores.
        """

        def refuse(detail: str, where: str) -> DocumentError:
            return DocumentError(
                "a declared_povm station's reduction is the identity link and "
                "nothing else, {links: [{kind: identity}]}: " + detail,
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path=where,
            )

        links, links_path = unwrap(reduction.links, self.env, path + "/links")
        if [(link.kind, link.requested_status) for link in links] != [
            ("identity", None)
        ]:
            raise refuse("the links are not [{kind: identity}]", links_path)
        carried, carried_path = unwrap(
            reduction.carried_operators, self.env, path + "/carried_operators"
        )
        if carried:
            raise refuse("it carries no operators", carried_path)
        fields = type(reduction).model_fields
        for name in fields:
            if name in ("links", "carried_operators"):
                continue
            value, where = unwrap(
                getattr(reduction, name), self.env, path + pointer(name)
            )
            if value != fields[name].default:
                raise refuse(f"{name} is not used on Band A", where)

    # -- an optical station ------------------------------------------------------

    def optical_station(
        self, station: Station, index: int, source: _Source
    ) -> _Optical:
        """Return an optical station's receiver, requests, weighting and outcomes."""
        where = pointer("stations", index)
        measurement = station.measurement
        assert isinstance(measurement, Optical)
        receiver = receiver_request(
            measurement,
            self.env,
            where,
            table=self.table_name(station, "coarse_graining"),
            work_bounds=self.work_bounds,
        )
        self.expansions[receiver.coarse.table] = receiver.coarse
        self.input_preparation.extend(receiver.conversions)
        self.absent.extend(receiver.absent)
        if receiver.characterisation:
            what = [item for item, _path in receiver.characterisation]
            self.flag(
                "receiver_characterisation",
                where + "/measurement",
                station.id,
                f"The measurement of station {station.id!r} is declared by "
                f"{', '.join(what)}. {_DECLARED} The engine takes the declared "
                "characterisation as exactly your device's (A-TRUST): it is not "
                "derived from catalogue optics, and the key length holds only if "
                "your device is what these numbers say.",
            )
        reduction, reduction_path = unwrap(
            station.reduction, self.env, where + "/reduction"
        )
        assert isinstance(reduction, Reduction)
        device = device_requests(
            receiver,
            reduction,
            self.env,
            reduction_path,
            source_mode=KIND_OF_SOURCE[self.model.source.kind],
            declared_by=station.declared_by or f"{self.record_label}.{station.id}",
            declared_tolerance=self.declared_tolerance,
            station=(
                RunStation(factor=station.id, party=station.party)
                if self.multi
                else None
            ),
            snap=self.snap,
        )
        weighting = self.weighting(station, receiver.outcomes, where)
        # The reduction is told whether this station's factor carries a public
        # choice, which A-TSM's emission rule reads: a document's station presents
        # its family directly, so its one possible choice is its `choice_weighting`.
        device = replace(device, public_choice_at_station=weighting is not None)
        entries = (
            receiver.outcomes
            if weighting is None
            else self.weighted_entries(receiver.outcomes, weighting)
        )
        return _Optical(station, receiver, device, weighting, entries)
