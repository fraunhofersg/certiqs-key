"""The public layer: the partition, the tables, the transcript.

Part of the lowering package (:mod:`instances.declared.lowering`).
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from certiqs_key.domain.announcements import AnnouncementTranscript, Message
from certiqs_key.foundations.blocks import (
    PRODUCT_LABEL_SEPARATOR,
)
from certiqs_key.protocol_compiler.spec import (
    PERP,
    KeyValue,
    Party,
    PartyPartition,
    PublicPart,
    Sifting,
    default_party_partition,
)
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.limits import MAX_TABLE_ROWS, check_size
from instances.declared.lowering.base import (
    _joint,
    _Outcomes,
    _topology,
)
from instances.declared.lowering.stations import _StationLowering
from instances.declared.model import (
    Announcements,
    ExplicitPartition,
    Key,
    Readout,
)
from instances.declared.rules import Entry, Variable
from instances.declared.values import unwrap

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass


class _PublicLowering(_StationLowering):
    """The public layer: partition, sifting, key, acceptance, transcript."""

    # -- the public part -------------------------------------------------------

    def partition(
        self,
        x_entries: tuple[Entry, ...],
        stations: Sequence[_Outcomes],
        factor_keys: tuple[str, ...],
    ) -> tuple[PartyPartition, dict[str, tuple[Entry, ...]], tuple[Entry, ...]]:
        """Return the partition, each party's readout entries and Bob's ``V``.

        ``V`` is the one station's outcomes, or the joint alphabet of several.
        """
        node, path = unwrap(self.model.public.partition, self.env, "/public/partition")
        v_entries = (
            stations[0].entries if len(stations) == 1 else _joint(stations, "/stations")
        )
        x_labels = [entry.label for entry in x_entries]
        if node in ("default", "factor_projection"):
            # Both build their readout tables over X x V entry by entry, so
            # they are bounded as an expanded table is.
            check_size(
                len(x_labels) * len(v_entries),
                MAX_TABLE_ROWS,
                f"the {node} partition's readout tables",
                path,
            )
        if node == "default":
            partition = default_party_partition(
                x_labels, [entry.label for entry in v_entries]
            )
            return partition, {"A": x_entries, "B": v_entries}, v_entries
        if node == "factor_projection":
            return (*self._factor_projection(x_labels, stations, path), v_entries)
        assert isinstance(node, ExplicitPartition)
        partition, readouts = self._partition(
            node,
            path,
            Variable("x", x_entries),
            Variable("v", v_entries),
            factor_keys,
        )
        return partition, readouts, v_entries

    def _factor_projection(
        self, x_labels: Sequence[str], stations: Sequence[_Outcomes], path: str
    ) -> tuple[PartyPartition, dict[str, tuple[Entry, ...]]]:
        """Return bbm92's partition: each party reads its own station's factor.

        Exactly one station per party (the load-time topology check); the
        joint label is the product of the stations' labels in station order.
        """
        position = {station.party: index for index, station in enumerate(stations)}
        if len(stations) != 2 or set(position) != {"A", "B"}:
            raise _topology(
                "factor_projection needs exactly one station per party", path
            )
        combinations = list(itertools.product(*(s.entries for s in stations)))
        joint = [
            PRODUCT_LABEL_SEPARATOR.join(entry.label for entry in combination)
            for combination in combinations
        ]
        readout = {
            party: {
                (x, v): combination[position[party]].label
                for x in x_labels
                for combination, v in zip(combinations, joint, strict=True)
            }
            for party in ("A", "B")
        }
        alice, bob = stations[position["A"]], stations[position["B"]]
        partition = PartyPartition(
            alice_readout=readout["A"],
            bob_readout=readout["B"],
            alice_readout_alphabet=tuple(entry.label for entry in alice.entries),
            bob_readout_alphabet=tuple(entry.label for entry in bob.entries),
            sector_factor_parties=tuple((Party(s.party),) for s in stations),
        )
        return partition, {"A": alice.entries, "B": bob.entries}

    def _partition(
        self,
        node: ExplicitPartition,
        path: str,
        x: Variable,
        v: Variable,
        factor_keys: tuple[str, ...],
    ) -> tuple[PartyPartition, dict[str, tuple[Entry, ...]]]:
        """Return an explicit partition: two readout maps over ``X x V``."""
        readouts: dict[str, tuple[Entry, ...]] = {}
        tables: dict[str, dict[tuple[str, str], str]] = {}
        for party, readout, name in (
            ("A", node.alice_readout, "alice_readout"),
            ("B", node.bob_readout, "bob_readout"),
        ):
            assert isinstance(readout, Readout)
            readouts[party] = self.alphabet(
                readout.alphabet, path + pointer(name, "alphabet")
            )
            expansion = self.expand(
                name, readout.map, [x, v], path + pointer(name, "map")
            )
            tables[party] = {
                (row.key[0], row.key[1]): str(row.value) for row in expansion.rows
            }
        parties: tuple[tuple[Party, ...], ...] = ()
        if node.sector_factor_parties:
            # One entry per factor, in the factors' declared order: Band A's one
            # sector s0, or the stations by id. The factorization is metadata
            # no theorem reads (PartyPartition), so it is carried, not decided.
            unknown = sorted(set(node.sector_factor_parties) - set(factor_keys))
            if unknown:
                raise DocumentError(
                    f"sector_factor_parties names {unknown}; the factors are "
                    f"{list(factor_keys)}",
                    reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                    path=path + "/sector_factor_parties",
                )
            parties = tuple(
                (Party(node.sector_factor_parties[key]),)
                for key in factor_keys
                if key in node.sector_factor_parties
            )
        partition = PartyPartition(
            alice_readout=tables["A"],
            bob_readout=tables["B"],
            alice_readout_alphabet=tuple(entry.label for entry in readouts["A"]),
            bob_readout_alphabet=tuple(entry.label for entry in readouts["B"]),
            sector_factor_parties=parties,
        )
        return partition, readouts

    def public(
        self,
        x_entries: tuple[Entry, ...],
        stations: Sequence[_Outcomes],
        factor_keys: tuple[str, ...],
    ) -> tuple[PublicPart, tuple[Entry, ...]]:
        """Return the public part and Bob's ``V``."""
        partition, readouts, v_entries = self.partition(
            x_entries, stations, factor_keys
        )
        public = self.model.public
        if public.transcript is not None:
            return self._transcript(partition, readouts), v_entries
        announcements, where = unwrap(
            public.announcements, self.env, "/public/announcements"
        )
        assert isinstance(announcements, Announcements)
        classes = {
            "A": self.alphabet(announcements.alice.alphabet, where + "/alice/alphabet"),
            "B": self.alphabet(announcements.bob.alphabet, where + "/bob/alphabet"),
        }
        alice = self.expand(
            "announce_alice",
            announcements.alice.map,
            [Variable("x", readouts["A"])],
            where + "/alice/map",
        )
        bob = self.expand(
            "announce_bob",
            announcements.bob.map,
            [Variable("v", readouts["B"])],
            where + "/bob/map",
        )
        class_vars = [Variable("A", classes["A"]), Variable("B", classes["B"])]
        sifting, key_rule, holder, key_alphabet, alphabet, accept = self._tables(
            class_vars, readouts
        )
        return (
            PublicPart(
                partition=partition,
                announce_alice={row.key[0]: str(row.value) for row in alice.rows},
                announce_bob={row.key[0]: str(row.value) for row in bob.rows},
                alice_announcement_alphabet=tuple(
                    entry.label for entry in classes["A"]
                ),
                bob_announcement_alphabet=tuple(entry.label for entry in classes["B"]),
                sifting=sifting,
                key_rule=key_rule,
                holder=holder,
                key_alphabet=key_alphabet,
                acceptance_alphabet=alphabet,
                accept_statistic={
                    (key[0], key[1]): value for key, value in accept.items()
                },
            ),
            v_entries,
        )

    def _tables(
        self,
        class_vars: Sequence[Variable],
        readouts: Mapping[str, tuple[Entry, ...]],
    ) -> tuple[
        dict[tuple[str, ...], Sifting],
        dict[tuple[str, tuple[str, ...]], KeyValue],
        Party,
        tuple[int, ...],
        tuple[str, ...],
        dict[tuple[str, ...], str],
    ]:
        """Expand the sifting, key and acceptance rules over the classes."""
        public = self.model.public
        sifting = self.expand("sifting", public.sifting, class_vars, "/public/sifting")
        key_node, key_path = unwrap(public.key, self.env, "/public/key")
        assert isinstance(key_node, Key)
        holder = Party(key_node.holder)
        key = self.expand(
            "key",
            key_node.rule,
            [Variable("o", readouts[str(holder)]), *class_vars],
            key_path + "/rule",
        )
        acceptance_node, acceptance_path = unwrap(
            public.acceptance, self.env, "/public/acceptance"
        )
        acceptance = self.expand(
            "acceptance", acceptance_node.map, class_vars, acceptance_path + "/map"
        )
        accept = {tuple(row.key): str(row.value) for row in acceptance.rows}
        alphabet = (
            tuple(acceptance_node.alphabet)
            if acceptance_node.alphabet is not None
            else tuple(dict.fromkeys(accept.values()))
        )
        return (
            {
                tuple(row.key): self._sifting(row.value, sifting.path)
                for row in sifting.rows
            },
            {
                (row.key[0], tuple(row.key[1:])): self._key_value(row.value, key.path)
                for row in key.rows
            },
            holder,
            tuple(key_node.alphabet),
            alphabet,
            accept,
        )

    def _transcript(
        self,
        partition: PartyPartition,
        readouts: Mapping[str, tuple[Entry, ...]],
    ) -> PublicPart:
        """Return the public part of a transcript of any length.

        Message ``k`` is a table over the sender's readout ``r`` and every
        earlier message, by id; its alphabet is declared, or ``derived``: the
        values the table takes, in first appearance, with the attributes their
        rule wrote. The classes are the messages' product, last fastest, which
        is the transcript's own joint alphabet.
        """
        public = self.model.public
        transcript = public.transcript
        assert transcript is not None
        messages: list[Message] = []
        earlier: list[Variable] = []
        sent: dict[str, list[str]] = {"A": [], "B": []}
        for index, message in enumerate(transcript.messages):
            where = pointer("public", "transcript", "messages", index)
            expansion = self.expand(
                f"message_{message.id}",
                message.table,
                [Variable("r", readouts[message.sender]), *earlier],
                where + "/table",
            )
            entries = (
                expansion.alphabet()
                if message.alphabet == "derived"
                else self.alphabet(message.alphabet, where + "/alphabet")
            )
            labels = tuple(entry.label for entry in entries)
            messages.append(
                Message(
                    sender=message.sender,
                    alphabet=labels,
                    table={
                        (row.key[0], tuple(row.key[1:])): str(row.value)
                        for row in expansion.rows
                    },
                )
            )
            sent[message.sender].extend(labels)
            earlier.append(Variable(message.id, entries))
        sifting, key_rule, holder, key_alphabet, alphabet, accept = self._tables(
            earlier, readouts
        )
        declared = public.announcement_alphabets
        alphabets = (
            {party: tuple(dict.fromkeys(labels)) for party, labels in sent.items()}
            if declared is None
            else {"A": tuple(declared.A), "B": tuple(declared.B)}
        )
        return PublicPart(
            partition=partition,
            announce_alice={},
            announce_bob={},
            alice_announcement_alphabet=alphabets["A"],
            bob_announcement_alphabet=alphabets["B"],
            sifting=sifting,
            key_rule=key_rule,
            holder=holder,
            key_alphabet=key_alphabet,
            acceptance_alphabet=alphabet,
            accept_statistic={},
            transcript=AnnouncementTranscript(tuple(messages)),
            accept_statistic_general=accept,
        )

    @staticmethod
    def _sifting(value: object, path: str) -> Sifting:
        if value in ("pass", "fail"):
            return Sifting(str(value))
        raise DocumentError(
            f"a sifting value is pass or fail; a rule gave {value!r}",
            reason=DocumentReason.RULE_VALUE_INVALID,
            path=path,
        )

    @staticmethod
    def _key_value(value: object, path: str) -> KeyValue:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if value == PERP:
            return PERP
        raise DocumentError(
            f"a key value is an integer or perp; a rule gave {value!r} "
            "(write {int: o.bit} to read a component as an integer)",
            reason=DocumentReason.RULE_VALUE_INVALID,
            path=path,
        )
