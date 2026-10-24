"""The transcript protocol: an ordered list of public messages, and nothing else.

WHAT THIS IS. ``protocol-compiler`` / ``meat-core`` ``def:declaration`` (DX5): the
announcement slot holds an ordered list of ``L >= 1`` MESSAGES; message ``m``
carries a sender ``pi_m``, a finite alphabet ``C_m`` and a TOTAL table

    a_m : O_{pi_m} x C_1 x ... x C_{m-1} -> C_m .

The joint announcement function is DERIVED from the tables by composition
(``eq:transcript``) and the joint alphabet is ``K = prod_m C_m``; neither is
declared by anyone, which is why neither is a field of this record.

WHY IT IS IN ``domain/`` AND NOT IN THE COMPILER. The transcript is a slot of the
declaration, so the compiler emits it and ``meat-core`` reads it: it is a shared
wire record of exactly the kind ``blocks``, ``constraints`` and ``chain`` are, and
a second spelling at the consuming end is a vocabulary that can disagree with
itself. Nothing here decides anything -- totality is check V1's and V8's, and
this record's only refusals are for arguments no clause can be read against.

THE TWO-MESSAGE CASE IS THE ACCEPTED FORMAT, ENTRY FOR ENTRY. ``(DX5)``: "the two
maps ``a_A``, ``a_B`` above are the transcript with ``L = 2``,
``pi = (A, B)``, ``C_1 = C_A``, ``C_2 = C_B``, ``a_1 = a_A`` and
``a_2(o, kappa_1) = a_B(o)``." :func:`two_message_transcript` is that reading, and
a declaration that says what it said before carries no transcript key at all --
the pair ``announce_alice`` / ``announce_bob`` "remains the emitted form of that
case" (the ``transcript`` output row). So this type is what the GENERAL format
needs and never a re-spelling of what the degenerate one already has.

NO MEASUREMENT READS A MESSAGE. (DX5)'s last sentence is a statement about the
declaration's shape and is carried by the TYPE here as it is there: the
measurement families are the fixed families of (DX3) and (DX4) and this record has
no slot a per-message measurement could be written into. ``ex:transcript`` names
the timing premise it is read under (``transmitter/ass:seq``); nothing here
asserts it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from certiqs_key.foundations.blocks import Label
from certiqs_key.foundations.errors import MalformedInputError

__all__ = [
    "AnnouncementTranscript",
    "Message",
    "two_message_transcript",
]


@dataclass(frozen=True)
class Message:
    """One message of a transcript protocol: its sender, alphabet and table.

    ``table`` is keyed by ``(readout, earlier)`` where ``readout`` is the
    sender's readout letter and ``earlier`` is the tuple of the messages before
    this one, in their order -- which IS the signature (DX5) declares, so a
    table keyed any other way is not of the declared type. For the FIRST message
    ``earlier`` is the empty tuple, and that is the signature's own degenerate
    value rather than a special case.

    ``sender`` IS A PARTY LABEL AND THE PARTY SET IS UNCHANGED (``def:spec``
    (d')): "it is ``{A, B}``, with the two readout maps of ``P``", and no third
    party is introduced by the general format.
    """

    sender: Label
    alphabet: tuple[Label, ...]
    table: Mapping[tuple[Label, tuple[Label, ...]], Label]

    def __post_init__(self) -> None:
        """Refuse a message with no sender or no alphabet."""
        if not self.sender:
            raise MalformedInputError(
                "a message of the transcript carries a sender pi_m in {A, B} "
                "(def:declaration (DX5)); the empty label names no party"
            )
        if not self.alphabet:
            raise MalformedInputError(
                "a message's alphabet C_m is finite and NON-EMPTY (D(i)); an "
                "empty one has no value the table could take"
            )
        if len(set(self.alphabet)) != len(self.alphabet):
            raise MalformedInputError(
                f"the message alphabet {list(self.alphabet)} repeats a letter; "
                "an alphabet is a set listed in its declared order"
            )


@dataclass(frozen=True)
class AnnouncementTranscript:
    """The announcement slot of (DX5): ``L >= 1`` messages, in their order.

    THE JOINT ALPHABET AND THE JOINT FUNCTION ARE DERIVED AND ARE NOT FIELDS.
    :meth:`joint_alphabet` is ``prod_m C_m`` in the product order, last message
    fastest, and :meth:`joint_announcement` is ``eq:transcript`` evaluated at the
    declared tables. A record carrying either as a datum would carry one object
    twice, and the interface's own row says so: "the joint announcement function
    and its alphabet are NOT KEYS".

    THE SIGNATURE CLAUSE IS WHERE TOTALITY IS DECIDED, AND IT IS NOT DECIDED
    HERE. :meth:`missing_cell` answers "which cell of which table is
    untabulated" and returns it; refusing on it is check V1's, whose refusal
    names the table. That split is the same one the rest of ``domain/`` keeps:
    this tier MEASURES and the consumer DECIDES.
    """

    messages: tuple[Message, ...]

    def __post_init__(self) -> None:
        """Refuse an empty transcript; (DX5) declares ``L >= 1``."""
        if not self.messages:
            raise MalformedInputError(
                "a transcript protocol declares L >= 1 messages "
                "(def:declaration (DX5)); an empty list announces nothing and "
                "leaves phi, sigma and r_hold with no domain"
            )

    @property
    def length(self) -> int:
        """Return ``L``, the number of declared messages."""
        return len(self.messages)

    @property
    def senders(self) -> tuple[Label, ...]:
        """Return ``(pi_m)_m`` in the declared order."""
        return tuple(message.sender for message in self.messages)

    def alphabets(self) -> tuple[tuple[Label, ...], ...]:
        """Return ``(C_m)_m`` in the declared order."""
        return tuple(message.alphabet for message in self.messages)

    def prefixes(self, index: int) -> tuple[tuple[Label, ...], ...]:
        """Return ``C_1 x ... x C_{index}`` in the product order, last fastest.

        The earlier-message half of message ``index``'s domain. At ``index = 0``
        it is the one empty tuple, which is the first message's own signature and
        not a missing value.
        """
        prefixes: list[tuple[Label, ...]] = [()]
        for message in self.messages[:index]:
            prefixes = [
                (*prefix, letter) for prefix in prefixes for letter in message.alphabet
            ]
        return tuple(prefixes)

    def joint_alphabet(self) -> tuple[tuple[Label, ...], ...]:
        """Return ``K = prod_m C_m`` in the product order, last message fastest.

        A tuple of tuples and NOT a joined string, deliberately: an announcement
        class of the accepted format is the pair ``(c_A, c_B)`` and a consumer
        reads its components, so the general format's class is the ``L``-tuple and
        a reader takes it apart the same way. At ``L = 2`` this is
        ``C_A x C_B`` in the order ``eq:jointann`` fixes, class for class.
        """
        return self.prefixes(self.length)

    def missing_cell(
        self, readouts: Mapping[Label, Sequence[Label]]
    ) -> tuple[int, Label, tuple[Label, ...]] | None:
        """Return the first untabulated cell of any table, or ``None``.

        ``readouts`` maps a party label to that party's readout alphabet
        ``O_pi``. The walk is message by message in the declared order and, inside
        a message, the readout letter slowest and the earlier-message prefix
        fastest, so the cell returned is the FIRST one in a declared order rather
        than the first one a dictionary happened to yield.

        WHAT IS RETURNED IS A LOCATION AND NOT A VERDICT: ``(message index
        0-based, readout letter, prefix)``. A sender with no readout alphabet in
        ``readouts`` is a malformed argument and not an untabulated cell -- the
        party partition declares the alphabets, and inventing an empty one would
        report every table total.
        """
        for index, message in enumerate(self.messages):
            alphabet = readouts.get(message.sender)
            if alphabet is None:
                raise MalformedInputError(
                    f"message {index + 1} is sent by party {message.sender!r}, "
                    "for which no readout alphabet O_pi was supplied; the party "
                    "partition declares them (def:spec (d'))"
                )
            for readout in alphabet:
                for prefix in self.prefixes(index):
                    if (readout, prefix) not in message.table:
                        return (index, readout, prefix)
        return None

    def joint_announcement(
        self, readout_of: Callable[[Label], Label]
    ) -> tuple[Label, ...]:
        """Return ``a(x, v)`` of ``eq:transcript`` at one outcome pair.

        ``readout_of`` returns ``rd_pi(x, v)`` for a party label, which is the
        only thing the composition reads of the pair -- so this function is
        ``eq:transcript`` and nothing else: ``kappa_m = a_m(rd_{pi_m}(x, v),
        kappa_1, ..., kappa_{m-1})``, accumulated in the declared order.

        A MISSING CELL RAISES RATHER THAN DEFAULTING. The composition of a
        partial table has no value, and substituting one would make V1's totality
        clause unreachable through this function; the location is
        :meth:`missing_cell`'s and the refusal is the consumer's.
        """
        transcript: list[Label] = []
        for index, message in enumerate(self.messages):
            readout = readout_of(message.sender)
            cell = (readout, tuple(transcript))
            try:
                transcript.append(message.table[cell])
            except KeyError as error:
                raise MalformedInputError(
                    f"the table of message {index + 1} is not tabulated at "
                    f"{cell!r}; eq:transcript composes TOTAL tables (D(viii))"
                ) from error
        return tuple(transcript)


def two_message_transcript(
    alice_announcement_alphabet: Sequence[Label],
    bob_announcement_alphabet: Sequence[Label],
    announce_alice: Mapping[Label, Label],
    announce_bob: Mapping[Label, Label],
    alice_readout_alphabet: Sequence[Label],
    bob_readout_alphabet: Sequence[Label],
    *,
    alice: Label = "A",
    bob: Label = "B",
) -> AnnouncementTranscript:
    """Return the ACCEPTED format's announcement pair AS a transcript.

    (DX5)'s own degenerate reading: ``L = 2``, ``pi = (A, B)``, ``C_1 = C_A``,
    ``C_2 = C_B``, ``a_1 = a_A`` and ``a_2(o, kappa_1) = a_B(o)`` -- Bob's table
    ignoring ``kappa_1``, which is what makes the two announcements independent.

    IT IS A READING AND NOT A CONVERSION ON THE EMITTED PATH. The compilation map
    "converts neither form into the other"; what this function is for is a
    derivation or a test that wants to check the degenerate case of a
    general-format statement against the accepted one, and
    ``tests/unit/test_domain_announcements.py`` is where that check lives. No
    emitted declaration of the accepted format carries a transcript key.

    A cell missing from either announcement map is left MISSING here: the table
    is built from the cells the maps have, so :meth:`
    AnnouncementTranscript.missing_cell` finds exactly the readouts the maps do
    not tabulate, and nothing is completed.
    """
    first: dict[tuple[Label, tuple[Label, ...]], Label] = {
        (readout, ()): announce_alice[readout]
        for readout in alice_readout_alphabet
        if readout in announce_alice
    }
    second: dict[tuple[Label, tuple[Label, ...]], Label] = {
        (readout, (first_letter,)): announce_bob[readout]
        for readout in bob_readout_alphabet
        if readout in announce_bob
        for first_letter in alice_announcement_alphabet
    }
    return AnnouncementTranscript(
        messages=(
            Message(
                sender=alice,
                alphabet=tuple(alice_announcement_alphabet),
                table=first,
            ),
            Message(
                sender=bob, alphabet=tuple(bob_announcement_alphabet), table=second
            ),
        )
    )
