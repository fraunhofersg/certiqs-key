"""The tagged virtual source: cutoffs, flags, the sector map and the weights.

spec/modules/transmitter/decoy/: Definition ``def:tagged-source`` (T1)-(T6),
Proposition ``prop:decoy-cert`` (the weight and the unit vector each letter
carries in each sector), and Remark ``rem:cutoffs``.

THE INDEX SET IS A FUNCTION OF THE DECLARED WEIGHTS, and this file computes it
rather than taking it as a datum. (T3): "A SECTOR THAT NO LETTER OF X PUTS
POSITIVE WEIGHT ON IS NOT DECLARED: the index set carries the sectors the
declaration uses, and it is read off the weights ... a declaration whose weights
change is a declaration whose sector list is read off them again, and NEITHER
LIST NEED CONTAIN THE OTHER." That is also what makes
``cor:emitted-decoy`` (v) true of a lowered weight: the rounded declaration "is a
different declaration, not a perturbation of one", and its sector list "may gain
a tail flag ... and it may lose a polarisation flag or a quantum sector".

WHAT IS DECLARED AND WHAT IS FORMED (the definition's closing paragraph).
DECLARED: the cutoffs (T1), the weights ``ptilde(n|mu)`` (T2), and the model's
alphabet, polarisation labels, intensities and label weights. FORMED, in exact
arithmetic: the tail weight ``eq:tailweight``, the index set ``eq:tset``, the
entries of the signal dyads (by the construction of ``cor:emitted-decoy``
(iv)(b), ``req:signal-dyads``: no dyad and no basis is read from a request),
and the weighted members of ``eq:rvirt``. DECLARED BY NOBODY: everything on
Alice's side -- ``A``, ``tau_A``, ``{M_x}`` and the certificate -- which
``lem:ensemble-presentation`` defines from the blocks.

ALICE'S SYSTEM IS NOT DECLARED HERE AT ALL (T5):
"a tagged source is presented as an ENSEMBLE PRESENTATION, in which ``A``, its
structure, ``tau_A`` and ``{M_x}`` are the objects ``eq:enspres`` defines,
``A_t`` being a copy of ``S_t`` sector by sector and in the same order". So the
matched pair is one structure read on both sides, "NOTHING ON ALICE'S SIDE IS
COMPRESSED, AND NO RANK IS READ".
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.blocks import Label, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    addition_rounds_nowhere,
    is_binary64,
    matrix,
)
from certiqs_key.transmitter.artifact import SECTOR_BLOCK_KIND
from certiqs_key.transmitter.certificate import RetentionAttestation
from certiqs_key.transmitter.decoy.bases import (
    EXHIBITED_PHOTON_NUMBERS,
    exhibited_signal_dyad,
)
from certiqs_key.transmitter.decoy.model import WcpLetter, WcpModel
from certiqs_key.transmitter.decoy.reasons import FlagFamily

__all__ = [
    "SectorKind",
    "TaggedSector",
    "TaggedSourceDeclaration",
    "TailWeight",
]


class SectorKind(StrEnum):
    """Which of the three summands of ``eq:avirt`` a declared sector is.

    ``QUANTUM``: ``S_n`` at ``n <= N_ent``, which "carries the signal states
    ``|n,a>`` themselves, one sector for all polarisations of that photon
    number". ``POLARISATION_FLAG``: ``C f_{n,a}`` at ``N_ent < n <= N_src``, one
    dimensional, one per polarisation, SHARED ACROSS INTENSITIES AND ROUND TYPES.
    ``TAIL_FLAG``: ``C f_{a,mu}``, one dimensional, shared across round types.
    """

    QUANTUM = "quantum"
    POLARISATION_FLAG = "polarisation_flag"
    TAIL_FLAG = "tail_flag"


#: The spellings a declared sector's identifier is built from. THEY ARE WIRE
#: IDENTIFIERS: a sector identifier is an HDF5 link name, so it is drawn from
#: ``domain.identifiers.IDENTIFIER_PATTERN`` and may not contain the shared
#: format's product separator ``__`` (``foundations.blocks``). The three prefixes are
#: distinct, so the three summands of ``eq:avirt`` cannot collide.
_QUANTUM_PREFIX: Final[str] = "n"
_POLARISATION_FLAG_PREFIX: Final[str] = "flag"
_TAIL_FLAG_PREFIX: Final[str] = "tail"
_PART_SEPARATOR: Final[str] = "-"

#: The dyad of a one-dimensional sector's own unit vector: the number ``1``. It
#: is the entry on every flag sector and on the vacuum
#: (``cor:emitted-decoy`` (iv)(b)), and it is a binary64 number, which is why
#: those sectors never meet ``formed_entry_not_declarable`` through their dyad.
_ONE_DIMENSIONAL_DYAD: Final[Matrix] = matrix(((1,),))


@dataclass(frozen=True)
class TaggedSector:
    """One member of the declared index set ``eq:tset``, with what it is.

    ``label`` is the wire identifier, ``dim`` is ``dim S_t`` -- "Every flag
    sector is one dimensional, and so is the quantum sector ``n = 0``" -- and the
    remaining fields say which summand of ``eq:avirt`` the sector is, so that
    :meth:`TaggedSourceDeclaration.weight_in` can read the weight and the unit
    vector off ``prop:decoy-cert`` without parsing the label back.
    """

    label: Label
    dim: int
    kind: SectorKind
    #: The photon number, for a quantum sector and a polarisation flag.
    photon_number: int | None = None
    #: The polarisation, for a polarisation flag and a tail flag.
    polarisation: Label | None = None
    #: The intensity, for a tail flag alone.
    intensity: Label | None = None


@dataclass(frozen=True)
class TailWeight:
    """``wtilde_mu`` of ``eq:tailweight``, formed exactly, with its (S) verdict.

    "the sum formed in increasing ``n`` and rounding nowhere". Both halves are
    carried: the exact value, and whether the accumulation that produced it was
    exact at every step. A tail weight that rounds is refused and never used --
    it is a FORMED quantity, and a formed quantity that is not admissible
    declared data is ``formed_entry_not_declarable``.
    """

    value: Fraction
    rounds_nowhere: bool


@dataclass(frozen=True)
class TaggedSourceDeclaration:
    """The declared data of ``def:tagged-source``, (T1) to (T6).

    NOTHING ON ALICE'S SIDE IS A FIELD HERE, and the absence is (T5): no retained
    system, no sector structure of ``A``, no marginal, no POVM and no
    certificate. What is emitted is an ENSEMBLE PRESENTATION, and those five are
    what ``lem:ensemble-presentation`` defines from it.
    """

    model: WcpModel
    #: ``N_ent`` (T1). Values above two are REFUSED by the emission, a scope
    #: decision and not a limit of the claims (``rem:cutoffs``: the claims are
    #: generic, ``N_ent <= 2`` is usable, the instance default is 1).
    entropy_cutoff: int
    #: ``N_src`` (T1).
    source_cutoff: int
    #: ``ptilde(n|mu)`` keyed by ``(photon number, intensity label)`` for every
    #: ``0 <= n <= N_src`` and every declared intensity. IT DEPENDS ON THE
    #: INTENSITY ALONE, not on the polarisation and not on the round type,
    #: "because the tail flag is shared across round types: one flag vector
    #: cannot be sent to two different tail states by one channel".
    sector_weights: Mapping[tuple[int, Label], Fraction]
    # No enclosure of ``P_mu(n)`` and no signal dyad is a field: the emission
    # forms the enclosure from the declared intensity
    # (``req:sector-weight-bound``) and the dyads from the polarisation parts
    # of the model (``req:signal-dyads``), and reads neither from a request.
    #: Which flag family the declaration requests. Anything finer than (T3) is
    #: REFUSED, so that the loss is not silent (``rem:no-intensity-split``).
    flag_family: FlagFamily = FlagFamily.SHARED
    #: Whether the declaration presents (T2) as a DECIDED EQUALITY with the
    #: Poisson weights, or asks for one to be represented exactly. Refused:
    #: "No condition of this submodule compares ptilde with P_mu for equality."
    weight_obligation_presented_as_equality: bool = False
    #: (SR3) as supplied, for the presentation the emission builds. Carried,
    #: never decided, never asserted.
    retention_attestation: RetentionAttestation | None = None

    def tail_weight(self, intensity: Label) -> TailWeight:
        """Return ``wtilde_mu`` of ``eq:tailweight``, THE SUM IN INCREASING ``n``.

        ``wtilde_mu = 1 - sum_{n <= N_src} ptilde(n|mu)``, "the sum formed in
        increasing ``n`` and rounding nowhere". The accumulation order is part of
        the datum, as every accumulation order in this repository is, and the
        (S) verdict travels with the value so that a caller refuses rather than
        rounds.
        """
        running = Fraction(0)
        rounds_nowhere = True
        for photon_number in range(self.source_cutoff + 1):
            weight = self.sector_weights[(photon_number, intensity)]
            if not _addition_is_exact(running, weight):
                rounds_nowhere = False
            running += weight
        value = Fraction(1) - running
        if not _addition_is_exact(Fraction(1), -running) or not is_binary64(value):
            rounds_nowhere = False
        return TailWeight(value=value, rounds_nowhere=rounds_nowhere)

    def sector_index_set(self) -> tuple[TaggedSector, ...]:
        """Return ``T`` of ``eq:tset``, READ OFF THE WEIGHTS, in the declared order.

        The order the definition declares: "the quantum sectors in increasing
        photon number, then the polarisation flags in the declared order of
        ``(n, a)``, then the tail flags in the declared order of ``(a, mu)``".

        A SECTOR NO LETTER PUTS POSITIVE WEIGHT ON IS NOT IN THE LIST. Three
        conditions, one per summand, each read off the declared weights and the
        formed tail weight: a quantum sector at ``n <= N_ent`` where some letter
        has ``ptilde(n|mu_x) > 0``; a polarisation flag ``(n, a)`` at
        ``N_ent < n <= N_src`` where some letter of that polarisation does; and a
        tail flag ``(a, mu)`` that some letter carries with ``wtilde_mu > 0``.
        """
        letters = self.model.alphabet
        tails = {
            name: self.tail_weight(name) for name in self.model.intensities
        }
        sectors: list[TaggedSector] = []
        for photon_number in self.quantum_photon_numbers():
            sectors.append(
                TaggedSector(
                    label=f"{_QUANTUM_PREFIX}{photon_number}",
                    dim=self._quantum_dim(photon_number),
                    kind=SectorKind.QUANTUM,
                    photon_number=photon_number,
                )
            )
        for photon_number in range(self.entropy_cutoff + 1, self.source_cutoff + 1):
            for polarisation in self.model.polarisations:
                if any(
                    letter.polarisation == polarisation
                    and self.sector_weights[(photon_number, letter.intensity)] > 0
                    for letter in letters
                ):
                    sectors.append(
                        TaggedSector(
                            label=_PART_SEPARATOR.join(
                                (
                                    _POLARISATION_FLAG_PREFIX,
                                    f"{_QUANTUM_PREFIX}{photon_number}",
                                    polarisation,
                                )
                            ),
                            dim=1,
                            kind=SectorKind.POLARISATION_FLAG,
                            photon_number=photon_number,
                            polarisation=polarisation,
                        )
                    )
        # "THEN THE TAIL FLAGS IN THE DECLARED ORDER OF (a, mu)", which is read
        # exactly as "(n, a)" is read for the polarisation flags above: the
        # model's DECLARED POLARISATION ORDER outer, its DECLARED INTENSITY
        # ORDER inner. A loop
        # over the LETTERS would give the alphabet's order -- a
        # third declared order, and one the definition does not name. The two
        # differ whenever the alphabet is intensity-major, and the order of a
        # sector list is a datum: it fixes the positions of every block list a
        # consumer reads.
        carried = {
            (letter.polarisation, letter.intensity) for letter in letters
        }
        for polarisation in self.model.polarisations:
            for intensity in self.model.intensities:
                if (polarisation, intensity) not in carried:
                    continue
                if tails[intensity].value <= 0:
                    continue
                sectors.append(
                    TaggedSector(
                        label=_PART_SEPARATOR.join(
                            (_TAIL_FLAG_PREFIX, polarisation, intensity)
                        ),
                        dim=1,
                        kind=SectorKind.TAIL_FLAG,
                        polarisation=polarisation,
                        intensity=intensity,
                    )
                )
        return tuple(sectors)

    def quantum_photon_numbers(self) -> tuple[int, ...]:
        """Return the photon numbers ``n <= N_ent`` of the quantum sectors of ``T``.

        (T3): a quantum sector ``S_n`` is declared where some letter puts
        positive weight on it, ``ptilde(n|mu_x) > 0``. Read off the weights
        alone, so that the emission can decide ``req:signal-dyads`` before any
        dimension of a sector is formed.
        """
        return tuple(
            photon_number
            for photon_number in range(self.entropy_cutoff + 1)
            if any(
                self.sector_weights[(photon_number, letter.intensity)] > 0
                for letter in self.model.alphabet
            )
        )

    def sector_structure(self) -> SectorStructure:
        """Return ``T`` as the shared format's sector map, block kind ``proof_sector``.

        (T5): the matched pair is "the structure of (T3) read on both sides", and
        "what it records is why a decomposition may be read off the declaration,
        and it is a statement about ``{M_x}``, ``tau_A`` and the certificate and
        about NO JOINT STATE".
        """
        sectors = self.sector_index_set()
        return SectorStructure(
            labels=tuple(sector.label for sector in sectors),
            dims=tuple(sector.dim for sector in sectors),
            block_kind=SECTOR_BLOCK_KIND,
        )

    def weight_in(self, sector: TaggedSector, letter: WcpLetter) -> Fraction:
        """Return ``w_{x,t}`` of ``prop:decoy-cert``: the weight ``rho^v_x`` carries.

        The proposition's own reading, case by case: ``ptilde(n|mu_x)`` on a
        quantum sector; ``ptilde(n|mu_x)`` on a polarisation flag ``(n, a)`` IF
        ``a_x = a`` and ``0`` otherwise; ``wtilde_mu`` on a tail flag
        ``(a, mu)`` if ``(a_x, mu_x) = (a, mu)`` and ``0`` otherwise.
        """
        if sector.kind is SectorKind.QUANTUM:
            assert sector.photon_number is not None
            return self.sector_weights[(sector.photon_number, letter.intensity)]
        if sector.kind is SectorKind.POLARISATION_FLAG:
            assert sector.photon_number is not None
            if sector.polarisation != letter.polarisation:
                return Fraction(0)
            return self.sector_weights[(sector.photon_number, letter.intensity)]
        if (sector.polarisation, sector.intensity) != (
            letter.polarisation,
            letter.intensity,
        ):
            return Fraction(0)
        return self.tail_weight(letter.intensity).value

    def dyad_in(self, sector: TaggedSector, letter: WcpLetter) -> Matrix:
        """Return ``|phi_{x,t}><phi_{x,t}|``, FORMED by the exhibited construction.

        ``req:signal-dyads``: ON EVERY FLAG SECTOR AND ON THE VACUUM it is the
        number ``1``, the sector being one dimensional and the dyad of its own
        unit vector; on a quantum sector ``n in {1, 2}`` it is ``|n,a><n,a|``
        with the entries ``cor:emitted-decoy`` (iv)(b) states, in the basis
        that corollary exhibits, for the vector of ``D`` the letter's
        polarisation is declared as. Outside the construction there is no dyad
        to form, and this raises; the emission refuses such a declaration
        first, with ``quantum_sector_outside_construction``.
        """
        if sector.kind is SectorKind.QUANTUM:
            assert sector.photon_number is not None
            return self.signal_dyad(sector.photon_number, letter.polarisation)
        return _ONE_DIMENSIONAL_DYAD

    def signal_dyad(self, photon_number: int, polarisation: Label) -> Matrix:
        """Return ``|n,a><n,a|`` of the quantum sector ``S_n``, formed once here.

        ``req:signal-dyads``: the number ``1`` at the vacuum, and at
        ``n in {1, 2}`` the dyad ``cor:emitted-decoy`` (iv)(b) writes for the
        vector of ``D`` the polarisation is declared as. This is the one place
        the dyads are formed: the emission decides its exact guard on the
        matrices this returns and builds the blocks from the same matrices.
        Outside the construction it raises.
        """
        outside = self.outside_construction(photon_number)
        if outside is not None:
            raise MalformedInputError(outside)
        if photon_number == 0:
            return _ONE_DIMENSIONAL_DYAD
        return exhibited_signal_dyad(
            photon_number, self.model.polarisation_parts[polarisation]
        )

    def outside_construction(self, photon_number: int) -> str | None:
        """Return why ``S_n`` lies outside the construction, or ``None``.

        ``req:signal-dyads``: at ``n in {1, 2}`` the dyads are formed only
        where every polarisation of ``Pol`` is declared as one of the four
        vectors of ``D``, distinct polarisations as distinct vectors, and
        ``|Pol| >= n + 1``. Distinctness is a condition of a quantum sector
        above the vacuum only, so it is decided here and not when the model is
        built: a vacuum-only declaration with two labels for one vector is
        admitted. The vacuum is always inside it;
        above two photons nothing is constructed (``req:entropy-cutoff``
        refuses ``N_ent >= 3`` first, under its own reason).
        """
        if photon_number == 0:
            return None
        if photon_number not in EXHIBITED_PHOTON_NUMBERS:
            return (
                f"cor:emitted-decoy (iv)(b) constructs no dyads at "
                f"n = {photon_number}; it exhibits a basis at one and at two "
                "photons only"
            )
        missing = [
            polarisation
            for polarisation in self.model.polarisations
            if polarisation not in self.model.polarisation_parts
        ]
        if missing:
            return (
                f"the quantum sector at n = {photon_number} is declared, and the "
                f"polarisations {missing} are not declared as one of the four "
                "vectors H, V, + and - of D; cor:emitted-decoy (iv)(b) forms "
                "the signal dyads only where every polarisation of Pol is one "
                "of them (req:signal-dyads)"
            )
        parts = self.model.polarisation_parts
        shared = sorted(
            {
                part
                for part in parts.values()
                if sum(1 for other in parts.values() if other == part) > 1
            }
        )
        if shared:
            return (
                f"the quantum sector at n = {photon_number} is declared, and "
                f"two polarisations are declared as the same vector of D "
                f"({shared}); cor:emitted-decoy (iv)(b) forms the signal dyads "
                "only where distinct polarisations are distinct vectors "
                "(req:signal-dyads)"
            )
        if len(self.model.polarisations) < photon_number + 1:
            return (
                f"the quantum sector at n = {photon_number} is declared with "
                f"|Pol| = {len(self.model.polarisations)}, and "
                "cor:emitted-decoy (iv)(b) forms the dyads at n photons only "
                f"with at least n + 1 = {photon_number + 1} polarisations, "
                "where S_n is the whole n-photon space (req:signal-dyads)"
            )
        return None

    def _quantum_dim(self, photon_number: int) -> int:
        """Return ``dim S_n``: one at the vacuum, ``n + 1`` inside the construction.

        ``def:wcp-model`` (W3): ``S_0 = C|vac>`` is one dimensional, "every
        polarisation sharing the vacuum". At ``n in {1, 2}`` with
        ``|Pol| >= n + 1`` polarisations of ``D``, ``S_n`` is the whole
        ``n``-photon space, of dimension ``n + 1`` (``cor:emitted-decoy``
        (iv)(b)). Outside the construction no dimension is formed.
        """
        outside = self.outside_construction(photon_number)
        if outside is not None:
            raise MalformedInputError(outside)
        return photon_number + 1


def _addition_is_exact(left: Fraction, right: Fraction) -> bool:
    """Whether one binary64 addition of two exact rationals is exact."""
    return addition_rounds_nowhere(Cx(left, Fraction(0)), Cx(right, Fraction(0)))
