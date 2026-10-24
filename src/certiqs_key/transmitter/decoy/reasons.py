"""The decoy submodule's machine vocabulary: its refusals and one assumption.

spec/modules/transmitter/decoy/interface.yaml, ``refusal_reasons``. NONE OF THE
CORE'S STRINGS IS REUSED FOR A NEW CONDITION and none of these has a frozen
spelling (``frozen_spellings: []``).

WHY A REASONS MODULE OF ITS OWN, as a removable submodule of reductions has. A submodule
owns its strings, so that a reader of the core's vocabulary is not told about
conditions the core does not state, and so that the two files can be reviewed at
their own scales. The two strings this submodule TRIPS MOST are the core's --
``formed_entry_not_declarable`` and ``ensemble_presentation_not_admissible`` --
and they are imported and not re-spelled, because "the condition is a condition
of the ensemble presentation and not of the decoy source".
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from certiqs_key.domain.claim_closure import never_verified
from certiqs_key.transmitter.reasons import RefusalReason

__all__ = [
    "DECOY_ASSUMPTION_MACHINE_KEYS",
    "DECOY_NEVER_VERIFIED",
    "DecoyAssumptionId",
    "DecoyRefusal",
    "DecoyRefusalReason",
    "FlagFamily",
    "RoundType",
]


class DecoyRefusalReason(StrEnum):
    """Every machine-readable reason this submodule can emit, in its table's order."""

    #: For some ``(n, mu)`` with ``n <= N_src`` the declared ptilde is negative,
    #: or lies above the lower end of the enclosure of ``P_mu(n)`` the emission
    #: forms from the declared ``mu`` (``lem:poisson-enclosure``,
    #: ``req:sector-weight-bound``). The report names the first ``(n, mu)`` at
    #: which it fails.
    SECTOR_WEIGHT_ABOVE_POISSON = "sector_weight_above_poisson"
    #: The declaration presents ``ptilde(n|mu) = P_mu(n)`` as a DECIDED
    #: EQUALITY, or asks for the Poisson weight to be represented exactly. "Its
    #: right-hand side is a transcendental number and is not a declared datum",
    #: so no condition of this submodule compares the two for equality.
    SECTOR_WEIGHT_AS_EQUALITY = "sector_weight_as_equality"
    #: The cutoffs are not integers with ``0 <= N_ent <= N_src``, which is (T1).
    CUTOFFS_OUT_OF_ORDER = "cutoffs_out_of_order"
    #: ``N_ent >= 3``. A SCOPE REFUSAL WITH ITS OWN REASON, not a consequence of
    #: any claim: every claim of this submodule is stated for arbitrary
    #: ``N_ent``, and what is missing is a construction of exactly admissible
    #: signal data on ``S_n`` at odd photon numbers from three.
    ENTROPY_CUTOFF_ABOVE_TWO = "entropy_cutoff_above_two"
    #: The index set carries a quantum sector at ``n = 1`` or ``n = 2`` and some
    #: polarisation is not declared as one of the four vectors of ``D``, or
    #: there are fewer than ``n + 1`` polarisations; or a formed dyad fails to
    #: be a rank-one projector with ``tr[X_a X_b] = |<a|b>|^(2n)``
    #: (``req:signal-dyads``).
    QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION = "quantum_sector_outside_construction"
    #: The declaration carries a polarisation flag per intensity at a photon
    #: number ``N_ent < n <= N_src``, or any flag family finer than (T3)
    #: declares. "It is refused so that the loss is not silent."
    FLAG_FAMILY_SPLIT_BY_INTENSITY = "flag_family_split_by_intensity"


@dataclass(frozen=True, slots=True)
class DecoyRefusal:
    """A refusal of this submodule: ONE OF ITS OWN STRINGS, OR ONE OF THE CORE'S.

    The union in the type is the interface's own division. The conditions of
    this submodule's table are its own -- the weight obligation, its equality
    reading, the cutoffs, the entropy cutoff's scope, the construction of the
    signal dyads and the flag family -- and two are the CORE's, listed under
    ``reasons_of_the_core_this_submodule_trips_most``:
    ``formed_entry_not_declarable``, because the condition "is a condition of the
    ensemble presentation and not of the decoy source", and
    ``ensemble_presentation_not_admissible`` for (E1), (E2) or (E3). Re-spelling
    either here would be two names for one refusal.

    THE CORE'S BLOCK-FORM AND PURE-FORM STRINGS CANNOT FIRE ON AN ARTEFACT OF
    THIS SUBMODULE: "no certificate is declared, and the conditions of the block
    form are theorems" (the interface's
    ``certificate_conditions_are_not_decided_here``).
    """

    reason: DecoyRefusalReason | RefusalReason
    detail: str

    def as_machine_record(self) -> dict[str, str]:
        """Return the refusal as a machine record."""
        return {"reason": str(self.reason), "detail": self.detail}


class RoundType(StrEnum):
    """The third component of a letter, ``def:wcp-model`` (W2).

    A DATUM THAT CHANGES NOTHING THE SOURCE EMITS: ``rho_x`` "is independent of
    the round type" (W4), and the tail flag is shared across round types, which
    is why the declared weights depend on the intensity alone.
    """

    TEST = "test"
    GEN = "gen"


class FlagFamily(StrEnum):
    """Which flag family a declaration requests, so that the finer one has a name.

    ``SHARED`` is the family ``def:tagged-source`` (T3) declares: one
    polarisation flag per ``(n, a)``, shared by every intensity and both round
    types. ``SPLIT_BY_INTENSITY`` is the finer family ``rem:no-intensity-split``
    is about, and it is REFUSED -- it "would give up exactly what the
    declaration is for", the sharing of one flag across intensities being "the
    decoy content of the declaration", and it would lose it silently if the
    emission did not refuse it.

    THE ENUM EXISTS SO THAT THE REFUSAL HAS SOMETHING TO FIRE ON. A finer family
    is a REQUEST a declarer makes, not a shape this submodule can detect after
    the fact: the emission builds the index set itself from the weights, so
    without a declared request there would be nothing to refuse and
    ``flag_family_split_by_intensity`` would be a string no code path could
    emit.
    """

    SHARED = "shared"
    SPLIT_BY_INTENSITY = "split_by_intensity"


class DecoyAssumptionId(StrEnum):
    """The one assumption this submodule declares, by its short id.

    A-WCP takes THE PLACE OF A-ENS for a specification whose ensemble is
    declared by this source model: ``ass:wcp`` refines A-ENS (its ``refines``
    field), and its lead-in says it "asserts the emission A-ENS asserts and
    adds the conditions this model needs, so it is never the weaker of the
    two". Its ``verification`` field is ``never``: this submodule records it
    and never asserts it of any apparatus. IT CARRIES NO ARITHMETIC: the
    source identity of the tagging link is a theorem about the declared
    numbers and holds of them exactly (``rem:wcp-virtual-model``).
    """

    A_WCP = "A-WCP"


#: The ledger's machine key for A-WCP, as this submodule's interface declares
#: it (``outputs.assumption_ledger.rows``; the core's ``ledger_spelling`` maps
#: the short id to it).
DECOY_ASSUMPTION_MACHINE_KEYS: Final[MappingProxyType[DecoyAssumptionId, str]] = (
    MappingProxyType({DecoyAssumptionId.A_WCP: "wcp_source_model"})
)

#: THE ASSUMPTIONS OF THIS SUBMODULE NO CODE PATH DECIDES: every member whose
#: ``verification`` header field is ``never`` (spec/claim-format.md section
#: 3.2), read from the shipped claim-closure table by machine key.
#: A-WCP is one (its field is ``never``).
DECOY_NEVER_VERIFIED: Final[tuple[DecoyAssumptionId, ...]] = tuple(
    identifier
    for identifier in DecoyAssumptionId
    if never_verified(DECOY_ASSUMPTION_MACHINE_KEYS[identifier])
)
