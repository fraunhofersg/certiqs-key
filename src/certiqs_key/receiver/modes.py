"""The declared mode space, the input split, and the port map.

Definitions ``def:modes`` and ``def:instrument``, and the ``subsystem_order``
convention of ``interface.yaml`` ``conventions``.

TWO ORDERS, TWO JOBS, AND A PRECEDENCE RULE BETWEEN THEM
========================================================
This is the one place in the module where getting an index wrong would be
silent, so both orders are named types rather than conventions in a comment.

* :func:`mode_space_order` is Definition ``def:modes`` -- LEXICOGRAPHIC IN
  ``(p, tau, pi)`` WITH ``H`` BEFORE ``V``. Note that the sort key is
  ``(p, tau, pi)`` and NOT the order in which the components of the label are
  written. It is the order ``M`` is LISTED in: the emitted
  ``input_mode_space`` label list and the row and column order of ``Gamma`` on
  ``C^M``.
* :meth:`InputModes.subsystem_order` is the ``subsystem_order`` convention --
  ``Inp_C`` before ``Inp_S``, each block internally in the order it inherits
  from ``M``. It is the order that indexes ``C^Inp``, and therefore EVERY
  Gram, every ``A_J``, every conditioned block matrix and every photon-number
  block.

The two disagree exactly when a probe path label sorts before a channel path
label, and the convention states which wins where: the subsystem order takes
PRECEDENCE, being the order that indexes ``C^Inp``, every Gram and every block
matrix, while the order of Definition ``def:modes`` is the order in which
``M`` is listed in the artifact.

THE ORDER IS NOT DECLARED, IT IS DERIVED
========================================
Definition ``def:modes`` does not offer a choice of order: a mode space is a
finite set of labels and "the order is lexicographic in ``(p, tau, pi)`` with
``H`` before ``V``". :meth:`ModeSpace.declare` therefore SORTS the declared
labels by that key rather than accepting whatever order they arrived in, and
the ``mode_space`` input row's "the order is the emitted order"
(``interface.yaml`` ``inputs``) is then a statement about what the artifact
lists, not a second degree of freedom. No refusal exists for a
list presented out of order, because there is nothing to refuse.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from certiqs_key.receiver.errors import MalformedInputError
from certiqs_key.receiver.reasons import Refusal, RefusalReason

__all__ = [
    "InputModes",
    "Mode",
    "ModeSpace",
    "Polarization",
    "PortMap",
    "check_input_modes",
    "check_mode_space",
    "check_port_map",
    "mode_space_order",
]


class Polarization(StrEnum):
    """The declared polarization index of Definition ``def:modes``."""

    H = "H"
    V = "V"

    @property
    def order_index(self) -> int:
        """Return the sort position: ``H`` before ``V``."""
        return 0 if self is Polarization.H else 1


@dataclass(frozen=True, order=False)
class Mode:
    """One declared optical mode ``m = (p, pi, tau)`` of Definition def:modes.

    ``tau`` is RESERVED: Definition ``def:modes`` says it is carried in the
    label and in the emitted artifact, it may take only a single declared value
    in this contract, and no catalogue entry (Definition
    ``def:catalogue-entries``) reads or writes it (Assumption ``ass:thresh``).
    RESERVED IS NOT OPTIONAL: it is part of the label, it is DECLARED, and it
    carries no default -- the ``fail_closed`` convention forbids substituting
    one, and the single-value rule is a check on what was declared rather than
    on what was assumed.
    """

    path: str
    polarization: Polarization
    tau: int

    @property
    def sort_key(self) -> tuple[str, int, int]:
        """Return the Definition ``def:modes`` key: ``(p, tau, pi)``."""
        return (self.path, self.tau, self.polarization.order_index)

    @property
    def label(self) -> str:
        """Return a human label; presentation metadata, never an index."""
        return f"{self.path}_{self.polarization}"


def mode_space_order(modes: Sequence[Mode]) -> tuple[int, ...]:
    """Return the Definition ``def:modes`` order as indices into ``modes``.

    Lexicographic in ``(p, tau, pi)`` with ``H`` before ``V``.
    """
    return tuple(sorted(range(len(modes)), key=lambda i: modes[i].sort_key))


@dataclass(frozen=True)
class ModeSpace:
    """The declared mode space ``M``, in the Definition ``def:modes`` order."""

    modes: tuple[Mode, ...]

    @classmethod
    def declare(cls, modes: Iterable[Mode]) -> ModeSpace:
        """Return the mode space of these labels, sorted by Def. def:modes."""
        listed = tuple(modes)
        return cls(tuple(listed[i] for i in mode_space_order(listed)))

    def __len__(self) -> int:
        """Return ``|M|``."""
        return len(self.modes)

    def index(self, mode: Mode) -> int:
        """Return the position of a mode in ``M``."""
        try:
            return self.modes.index(mode)
        except ValueError as exc:  # pragma: no cover - defensive
            raise MalformedInputError(f"{mode!r} is not a declared mode") from exc

    @property
    def labels(self) -> tuple[str, ...]:
        """Return the emitted label list, in the ``M`` order."""
        return tuple(mode.label for mode in self.modes)


def check_mode_space(space: ModeSpace) -> Refusal | None:
    """Return a refusal if the declared mode space is not well formed.

    ``interface.yaml`` ``inputs.mode_space``: "finite, non-empty, pairwise
    distinct labels". Definition ``def:modes`` and Assumption ``ass:thresh``
    add that ``tau`` "may take only a single declared value in this contract";
    that is decidable by inspection of this key, since every declared label
    carries its ``tau``, and the contract names no separate check identifier
    for it (``tau_validation_note``), so none is invented -- the identity
    named is the single-``tau`` rule itself.
    """
    if not space.modes:
        return Refusal(
            RefusalReason.MODE_SPACE_MALFORMED,
            "the declared mode space is empty; the inputs table requires a "
            "finite, non-empty label list",
        )
    if len(set(space.modes)) != len(space.modes):
        return Refusal(
            RefusalReason.MODE_SPACE_MALFORMED,
            "the declared mode space repeats a label; the inputs table requires "
            "pairwise distinct labels",
        )
    taus = {mode.tau for mode in space.modes}
    if len(taus) > 1:
        return Refusal(
            RefusalReason.MODE_SPACE_TAU_NOT_SINGLE_VALUED,
            f"the reserved index tau takes {len(taus)} distinct values "
            f"{sorted(taus)}; Definition def:modes and Assumption ass:thresh "
            f"admit a single declared value in this contract",
        )
    return None


@dataclass(frozen=True)
class InputModes:
    r"""The declared input split ``Inp = Inp_C (disjoint union) Inp_S``.

    Both members are indices into the mode space, each listed in the order it
    inherits from ``M``. Definition ``def:instrument`` (ii): ``Inp_C`` are the
    channel modes (the adversary's access) and ``Inp_S`` the declared source
    (probe) modes; every mode of ``M \ Inp`` carries vacuum at the input
    (Assumption ``ass:vac``). ``Inp_S`` empty is legal and means "no probe".
    """

    channel: tuple[int, ...]
    source: tuple[int, ...] = ()

    def subsystem_order(self) -> tuple[int, ...]:
        """Return the order that indexes ``C^Inp``: ``Inp_C`` then ``Inp_S``.

        The ``subsystem_order`` convention, and the order that takes precedence
        over Definition ``def:modes`` wherever the two disagree.
        """
        return self.channel + self.source

    @property
    def dimension(self) -> int:
        """Return ``|Inp|``."""
        return len(self.channel) + len(self.source)

    @property
    def channel_dimension(self) -> int:
        """Return ``|Inp_C|``, which fixes the emitted block dimensions."""
        return len(self.channel)

    @property
    def source_dimension(self) -> int:
        """Return ``|Inp_S|``."""
        return len(self.source)

    @property
    def has_probe(self) -> bool:
        """Return whether any source mode is declared."""
        return bool(self.source)


def check_input_modes(space: ModeSpace, inputs: InputModes) -> Refusal | None:
    """Return a refusal if the declared input split is not well formed.

    ``interface.yaml`` ``inputs.input_modes``: ``Inp`` a subset of ``M``, ``Inp_C``
    non-empty, the two blocks disjoint.
    """
    indices = inputs.subsystem_order()
    if any(index < 0 or index >= len(space) for index in indices):
        return Refusal(
            RefusalReason.INPUT_MODES_MALFORMED,
            "a declared input mode lies outside the declared mode space",
        )
    if len(set(indices)) != len(indices):
        return Refusal(
            RefusalReason.INPUT_MODES_MALFORMED,
            "the channel and source blocks are not disjoint, or repeat a mode; "
            "Definition def:instrument (ii) declares a disjoint union",
        )
    if not inputs.channel:
        return Refusal(
            RefusalReason.INPUT_MODES_CHANNEL_EMPTY,
            "Inp_C is empty; the inputs table requires a non-empty channel block",
        )
    return None


@dataclass(frozen=True)
class PortMap:
    """The declared detector ports ``{P_k}`` of Definition def:instrument (iii).

    Pairwise disjoint subsets of ``M``, ``K >= 1``. A mode in no port is
    UNDETECTED, and Remark ``rem:unmonitored`` makes that partition "a
    declaration": deleting the row of an unmonitored output mode changes no
    ``A_J``, which is why Requirement ``req:declared-port-map`` takes the port
    map as "a declared input" and "never infers" it from the matrix.
    """

    entries: tuple[tuple[str, tuple[int, ...]], ...]

    @property
    def labels(self) -> tuple[str, ...]:
        """Return the port labels, in the declared order."""
        return tuple(label for label, _ in self.entries)

    @property
    def port_count(self) -> int:
        """Return ``K``."""
        return len(self.entries)

    def modes_of(self, index: int) -> tuple[int, ...]:
        """Return the modes collected by port ``index``."""
        return self.entries[index][1]

    def unmonitored(self, mode_count: int) -> tuple[int, ...]:
        """Return the declared modes lying in no port.

        The support of ``E_un`` in the deficiency identity Eq.
        ``eq:deficiencyid`` and the second summand of ``D_eta``.
        """
        covered = {mode for _, modes in self.entries for mode in modes}
        return tuple(index for index in range(mode_count) if index not in covered)


def check_port_map(space: ModeSpace, ports: PortMap) -> Refusal | None:
    """Return a refusal if the declared port map is not well formed.

    ``interface.yaml`` ``inputs.port_map``: ``K >= 1``, pairwise disjoint
    subsets of ``M``.
    """
    if ports.port_count < 1:
        return Refusal(
            RefusalReason.PORT_MAP_MALFORMED,
            "no port is declared; the inputs table requires K >= 1",
        )
    seen: set[int] = set()
    for label, modes in ports.entries:
        if any(index < 0 or index >= len(space) for index in modes):
            return Refusal(
                RefusalReason.PORT_MAP_MALFORMED,
                f"port {label!r} collects a mode outside the declared mode space",
            )
        if len(set(modes)) != len(modes):
            return Refusal(
                RefusalReason.PORT_MAP_MALFORMED,
                f"port {label!r} lists a mode twice",
            )
        overlap = seen & set(modes)
        if overlap:
            return Refusal(
                RefusalReason.PORT_MAP_MALFORMED,
                f"port {label!r} overlaps an earlier port on modes "
                f"{sorted(overlap)}; Definition def:instrument (iii) declares "
                f"pairwise disjoint ports",
            )
        seen |= set(modes)
    if len(set(ports.labels)) != ports.port_count:
        return Refusal(
            RefusalReason.PORT_MAP_MALFORMED,
            "two ports carry the same label",
        )
    return None
