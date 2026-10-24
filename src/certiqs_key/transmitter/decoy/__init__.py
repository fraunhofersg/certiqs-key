"""``decoy``: the phase-randomised weak-coherent-pulse source, tagged.

The submodule spec/modules/transmitter/decoy/ owns, in its own words: the source
model (``def:wcp-model``) with its physical-source assumption A-WCP in the place
of A-ENS (``ass:wcp``); the tagged virtual source with its two cutoffs, its
polarisation and tail flags and its matched sector map (``def:tagged-source``);
the one channel from the tagged virtual source to the weak coherent source
(``prop:tagging``), which is the soundness claim of the source-link kind
``tagging``; the ensemble presentation of the tagged source
(``prop:decoy-cert``); and what the emission declares (``cor:emitted-decoy``),
with the two remarks that fence the cutoffs and the flag family.

THE ADMITTED CONSUMER PATH. The tagging link is admitted through
``DecoySourceDeclaration.as_transmitter_artifact``. The compiler's
C3 ensemble form consumes its weighted blocks directly. The raw
``as_source_specification`` view supplies data without admitting provenance;
the core refuses that view with ``source_segment_not_from_admitting_module``.
An unknown source kind uses ``source_link_kind_not_admitted`` in new outputs.

WHAT THIS PACKAGE MAY NOT DO. It imports the core of its own module and nothing
else: ``depends_on_modules: []``, "no sibling submodule, no foreign module". The
enclosure of the Poisson weights that (T2) is decided against is formed here,
in exact rational arithmetic, by ``lem:poisson-enclosure``
(:mod:`certiqs_key.transmitter.decoy.enclosure`, ``req:sector-weight-bound``),
and the signal dyads by the construction of ``cor:emitted-decoy`` (iv)(b)
(:mod:`certiqs_key.transmitter.decoy.bases`, ``req:signal-dyads``); neither is
read from a request, and no tolerance enters either.

NOTHING HERE COMPRESSES, SNAPS OR ROUNDS. ``A_t`` is a copy of ``S_t`` whatever
the rank of the sector's marginal, the declared blocks are the emitted ones, and
a number that cannot be represented is REFUSED rather than moved.
"""

from __future__ import annotations

from certiqs_key.transmitter.decoy.bases import (
    BB84_POLARISATION_ORDER,
    EXHIBITED_PHOTON_NUMBERS,
    exhibited_signal_dyad,
)
from certiqs_key.transmitter.decoy.emit import (
    DECOY_ASSUMPTION_LEDGER,
    MATHEMATICAL_SPEC_VERSION,
    TAGGING_OBLIGATION,
    DecoyResult,
    DecoySourceDeclaration,
    emit_decoy_declaration,
)
from certiqs_key.transmitter.decoy.enclosure import (
    POISSON_INDEX_THRESHOLD,
    PoissonEnclosure,
    PoissonEnclosureTable,
    poisson_enclosures,
    poisson_index,
)
from certiqs_key.transmitter.decoy.model import WcpLetter, WcpModel
from certiqs_key.transmitter.decoy.reasons import (
    DECOY_ASSUMPTION_MACHINE_KEYS,
    DECOY_NEVER_VERIFIED,
    DecoyAssumptionId,
    DecoyRefusal,
    DecoyRefusalReason,
    FlagFamily,
    RoundType,
)
from certiqs_key.transmitter.decoy.tagged import (
    SectorKind,
    TaggedSector,
    TaggedSourceDeclaration,
    TailWeight,
)

__all__ = [
    "BB84_POLARISATION_ORDER",
    "DECOY_ASSUMPTION_LEDGER",
    "DECOY_ASSUMPTION_MACHINE_KEYS",
    "DECOY_NEVER_VERIFIED",
    "EXHIBITED_PHOTON_NUMBERS",
    "MATHEMATICAL_SPEC_VERSION",
    "POISSON_INDEX_THRESHOLD",
    "TAGGING_OBLIGATION",
    "DecoyAssumptionId",
    "DecoyRefusal",
    "DecoyRefusalReason",
    "DecoyResult",
    "DecoySourceDeclaration",
    "FlagFamily",
    "PoissonEnclosure",
    "PoissonEnclosureTable",
    "RoundType",
    "SectorKind",
    "TaggedSector",
    "TaggedSourceDeclaration",
    "TailWeight",
    "WcpLetter",
    "WcpModel",
    "emit_decoy_declaration",
    "exhibited_signal_dyad",
    "poisson_enclosures",
    "poisson_index",
]
