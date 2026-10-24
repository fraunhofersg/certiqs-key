"""Reading the compiler's emitted declaration into this module's type.

THIS MODULE IS NOT PART OF THE PACKAGE SURFACE, and that is deliberate. It is
the only file of :mod:`certiqs_key.meat_core` that imports
:mod:`certiqs_key.protocol_compiler`, and importing it from ``__init__`` would
put the compiler's exact Gaussian-rational substrate on the import path of a
package whose own mathematics is binary64 linear algebra. Reach it at
``certiqs_key.meat_core.docking``; nothing else in this package imports it.

IT LIVES WITH THE CONSUMER, AND THE DIRECTION IS THE REASON. Imports point
downward only (PRINCIPLES.md section 4), so the code that converts an emitted
declaration into this module's type belongs to THE CONSUMER THAT READS IT.
design.md, "Where the code is", says it in the same words: the consumer reads
the supplier, so that conversion lives here and not in the compiler.

WHAT THIS MODULE MAY NOT DO
===========================
It modifies nothing of :mod:`certiqs_key.domain` and extends no schema ON ITS
OWN AUTHORITY. Adding a field to the frozen operator-bundle wire format is a
HUMAN decision (spec/architecture.md 4.1; PRINCIPLES.md section 2.4), and this
file takes none: the two the declaration carries -- ``sector_block_kind`` and
the per-entry ``constraint_rhs_tag`` -- cross as required manifest fields with
no default. What still does NOT travel are the
SIX COMPILER-ONLY KEYS of the compiler's own outputs table --
``acceptance_alphabet``, ``label_index_map``, ``reduction_chain_record``,
``key_length_eligible``, ``gate_report``, ``refusal``. They stay in the
compiler's artefact, which is self-contained by design.

ONE OF THE SIX CARRIES SOMETHING BOTH CONTRACTS MUST AGREE ON, AND THIS IS
WHERE THE SUBSTITUTE CARRIER IS NAMED. Row (7) of ``consumer_agreement`` says
the declared summation order travels under the key ``label_index_map``, emitted
so that THE ONE ORDER THE TWO CONTRACTS MUST AGREE ON HAS A DATUM ON THE WIRE.
That key is compiler-only and is excluded here, so the named carrier does not
exist across this boundary. THE ORDER NEVERTHELESS TRAVELS, by a different
datum: the alphabets the manifest carries are ORDERED TUPLES in the emitted
index order -- ``alice_povm`` and ``bob_povm`` are keyed dictionaries whose
insertion order is ``declaration.alice_alphabet`` and
``declaration.bob_alphabet``, and ``acceptance_values`` and
``sector_index_set`` are tuples -- so this module re-accumulates in the order
the compiler decided in, which is what ``eq:declorder`` requires of it. THE
SUBSTANCE HOLDS AND THE CARRIER THE CONTRACT NAMES DOES NOT, and that is
recorded here rather than left for a reader to reconcile. Closing the gap
properly is a wire item -- a ``label_index_map`` field on the manifest -- and
it is a human decision, not this file's.

THE THREE THINGS THE CALLER MUST SUPPLY, AND WHO OWNS THEM
==========================================================
NONE OF THE THREE IS THE COMPILER'S, and its own ``not_inputs`` preamble names
two of them as inputs of this engine that are not outputs of it:

``acceptance_set``
    owned by ``statistics``. The compiler emits the acceptance ALPHABET and the
    acceptance-statistic map; THE ACCEPTANCE SET IS NOT ITS OUTPUT.
``rounds``
    a run parameter, selected by the run tier (spec/architecture.md 3.3). No
    row of the compiler's outputs table supplies it.
``parameters`` (``alpha``, ``eps_pa``, ``eps_ev``, ``lambda_ec``)
    THIS module's ``parameters`` table, and the compiler's says in as many
    words that ``alpha`` is not a parameter of its contract and that it has no
    free numerical parameter at all.

They are REQUIRED ARGUMENTS of :func:`dock_declaration` rather than optional
ones with defaults, because a default would be this function supplying a datum
nobody declared -- which is what the fail-closed convention forbids ("NO
DEFAULT VALUE IS EVER SUBSTITUTED FOR A MISSING DATUM") and exactly the kind of
quiet ownership creep the two "not outputs" rows exist to prevent.

THE ONE EMISSION SITE, AND WHY IT IS NOT A CONVERSION
====================================================
:func:`to_complex128` is the only place a number leaves this module's exact
substrate, and IT DOES NOT CONVERT ANYTHING. The conventions
(``no_snapping``): "AN EMITTED MATRIX ENTRY THAT THIS MODULE WAS HANDED IS THE
ENTRY IT WAS HANDED ... this module therefore never snaps, in either of the two
senses spec/architecture.md 2.9 distinguishes". And ``def:exact`` opens
with the premise that makes that possible: "Declared operator data arrives as
binary64 numbers, and a binary64 number is a dyadic rational: IT IS THE NUMBER
IT DENOTES AND THERE IS NO EXACT OBJECT BEHIND IT of which it is an
approximation."

So the rule here is DECIDE, THEN WRITE. Every entry is decided to be a binary64
number FIRST, by ``matrix_is_binary64``; on an entry that passes, ``float`` is
the identity, and the array carries the numbers this module decided on,
unchanged. An entry that fails is REFUSED and nothing is emitted -- which is
the same route Definition ``def:weighted`` fixes for the one family this module
constructs ("it refuses, and it declares no k"), and the same route
spec/architecture.md 2.9
section 7.2.1 calls a producer's first option.

A ROUNDING ARGUMENT DOES NOT APPLY HERE. It would run: "``2/3`` has no
binary64 form, so the conversion is inexact in general ... a rounding at this
boundary cannot flip a verdict this module reached." The premise would be true
of a module whose substrate held arbitrary rationals; it is not true of one
whose declared data is binary64 by type. And the conclusion is too narrow
anyway: a rounding here would not flip a verdict THIS module
reached, but it would hand the CONSUMER numbers this module never decided
anything about, and the consumer decides (H), (P), (C) and (S) on exactly those
numbers at exactly zero. Silently rounding into that is the thing
``no_snapping`` forbids.

WHAT IS STILL TRUE, AND WORTH STATING PLAINLY: every decision this module's
package makes is made EXACTLY AND BEFORE THIS BOUNDARY. V1--V8, (SR1)--(SR2),
the interface conditions, the licensed-class test and the gates all run on
Gaussian rationals; nothing downstream of :func:`to_complex128` is compared,
ordered or decided here. The consumer re-validates what it receives with its
own fail-closed check, which is the point of docking rather than trusting.

NO COMPLEX VALUE IS EVER NARROWED TO A REAL ONE on this path: the target dtype
is ``complex128`` and the conversion builds complex entries directly, so the
repository-wide ``filterwarnings = error`` has no ``ComplexWarning`` to catch.
A real-typed target would be the place it would bite, and there is none.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction

import numpy as np
import numpy.typing as npt

from certiqs_key.domain.constraints import ConstraintEntry, Relation, RhsTag
from certiqs_key.domain.manifest import ConstraintRelation, KeyHolder, PartyLabel
from certiqs_key.foundations.blocks import BlockOperator, Label
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix, is_binary64, matrix_is_binary64
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
    PartyPartition,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.declaration import (
    ConstraintEntry as ConsumerConstraintEntry,
)
from certiqs_key.meat_core.declaration.declaration import (
    RhsTag as ConsumerRhsTag,
)
from certiqs_key.meat_core.provenance import CompilerEmission
from certiqs_key.protocol_compiler.declaration import (
    MATHEMATICAL_SPEC_VERSION as COMPILER_SPEC_VERSION,
)
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.protocol_compiler.spec import PERP, Party

__all__ = [
    "CONSUMER_RHS_TAG",
    "RELATION_TO_CONSUMER",
    "compiler_emission",
    "dock_declaration",
    "sector_blocks",
    "to_complex128",
    "transported_entry_count",
]

#: The three ordering symbols, in the consuming format's spelling. That format
#: "stays operator-shaped because the type of the bound, not the name of the
#: relation, is what the mode changes" -- which is the same reading this
#: package takes in :class:`certiqs_key.protocol_compiler.spec.Relation`.
RELATION_TO_CONSUMER: dict[Relation, ConstraintRelation] = {
    Relation.LE: ConstraintRelation.PRECEQ,
    Relation.EQ: ConstraintRelation.EQ,
    Relation.GE: ConstraintRelation.SUCCEQ,
}

#: The two declared forms, in the consuming format's spelling. THE TWO
#: VOCABULARIES COINCIDE, which is not an accident: both are Definition
#: ``def:homog``'s, and the consumer's own row says the tag "IS DECLARED DATA
#: AND CARRIES NO DEFAULT". The map is written out rather than relying on the
#: string values matching, so that a rename on either side is a type error
#: here instead of a silent mis-tag.
CONSUMER_RHS_TAG: dict[RhsTag, ConsumerRhsTag] = {
    RhsTag.HOMOGENEOUS: ConsumerRhsTag.HOMOGENEOUS,
    RhsTag.GENERAL: ConsumerRhsTag.GENERAL,
}


def to_complex128(
    operator: Matrix, *, what: str = "an emitted operator"
) -> npt.NDArray[np.complex128]:
    """Emit one exact operator in the consumer's machine representation.

    THE ONE EMISSION SITE OF THIS PACKAGE, AND IT DECIDES BEFORE IT WRITES.
    Every entry is decided to be a binary64 number first; ``float`` is then the
    IDENTITY on it, and what the array carries is the numbers this module
    decided on, unchanged. See the module docstring for why that is an emission
    and not a conversion.

    ``what`` names the operator in the refusal, so that a caller is told WHICH
    emitted object was off the lattice and not merely that one was.
    """
    if not matrix_is_binary64(operator):
        raise MalformedInputError(
            f"{what} carries an entry that is not a binary64 number, so "
            "emitting it into the complex128 format would ROUND it. Definition "
            "def:exact opens 'Declared operator data arrives as binary64 "
            "numbers, and a binary64 number IS the number it denotes', and "
            "the conventions (no_snapping) adds that 'an emitted matrix "
            "entry that "
            "this module was handed IS the entry it was handed' -- this module "
            "never snaps, in either of the two senses spec/architecture.md 2.9 "
            "distinguishes. The route Definition def:weighted fixes for the one "
            "family this module CONSTRUCTS is the same one, and it is the route "
            "taken here: 'it refuses, and it declares no k'"
        )
    return np.array(
        [
            [complex(float(entry.re), float(entry.im)) for entry in row]
            for row in operator
        ],
        dtype=np.complex128,
    )


def _binary64_scalar(value: Fraction, what: str) -> float:
    """Emit one declared real scalar, deciding the lattice first.

    The scalar right-hand side ``c_k`` of a ``homogeneous`` constraint entry is
    the one NUMBER that crosses this boundary outside a matrix, and ``float``
    on a :class:`~fractions.Fraction` rounds exactly as it does on a matrix
    entry. The same decision therefore guards it, for the same reason and with
    the same refusal.
    """
    if not is_binary64(value):
        raise MalformedInputError(
            f"{what} is {value}, which is not a binary64 number; emitting it "
            "would round a declared datum, and this module never repairs what "
            "it was handed (the conventions, no_snapping; Definition "
            "def:exact)"
        )
    return float(value)


def sector_blocks(
    operator: BlockOperator,
    labels: tuple[Label, ...],
    *,
    what: str = "an emitted Q-operator",
) -> dict[str, npt.NDArray[np.complex128]]:
    """Return the operator's blocks, keyed by sector identifier.

    THE OPERATOR IS ALREADY ITS BLOCKS, so this is a re-keying and
    not a split: Definition ``def:declaration``, "an operator on ``Q`` is given
    as one array ``F^(s)`` in ``L(Q_s)`` per ``s``, against the sector map
    ``Smap``, and THAT LIST IS THE OPERATOR". There is no slicing of a
    ``d_Q x d_Q`` array along the sector decomposition and no re-check that
    discarded off-diagonal blocks are zero, because "nothing verifies that the
    off-sector entries are zero, BECAUSE NOTHING CAN WRITE THEM" (the conventions,
    ``operator_form``). Emitting the blocks as binary64 arrays is where this
    module ends and the wire format begins, and every block is decided to be on
    the lattice before it is written (:func:`to_complex128`).
    """
    return {
        label: to_complex128(block, what=f"{what}, block {label!r}")
        for label, block in zip(labels, operator.blocks, strict=True)
    }


def _sector_of(index: int, dims: tuple[int, ...]) -> int:
    """Return which declared sector a composite index falls in."""
    start = 0
    for sector, dim in enumerate(dims):
        if start <= index < start + dim:
            return sector
        start += dim
    raise MalformedInputError("index outside the declared sector decomposition")


def _consumer_entry(
    entry: ConstraintEntry,
    labels: tuple[Label, ...],
    dims: tuple[int, ...],
    index: int = 0,
) -> ConsumerConstraintEntry:
    """Convert one constraint entry to the consuming format, TAG AND ALL.

    The consumer's own row requires the tag and supplies no default: "a tag
    this module supplied would be a code default deciding a security-relevant
    predicate ... on nobody's authority". This module has one and it is read
    off the datum, never off a supplier's field (Definition ``def:homog``), so
    the two ends carry the same object for the same reason.

    An entry whose right-hand-side slot holds NEITHER admitted type has no tag,
    and check V6 refuses it before any declaration is emitted; reaching this
    function with one is a hypothesis violation rather than an occasion to
    invent a tag.

    BOTH SHAPES OF RIGHT-HAND SIDE ARE DECIDED ON THE LATTICE BEFORE THEY ARE
    EMITTED -- the real scalar ``c_k`` of a ``homogeneous`` entry and the
    Hermitian matrix ``Theta_k`` of a ``general`` one -- as are the entry's
    operator blocks. Check V3 tests ``O^_k``'s Hermiticity and check V6 tests
    ``Theta_k``'s, but no check of Definition ``def:validator`` reads lattice
    membership of either, so this boundary is where the premise Definition
    ``def:exact`` opens with is enforced rather than assumed.
    """
    number = index + 1
    bound: npt.NDArray[np.complex128] | float
    bound = (
        _binary64_scalar(entry.rhs, f"the scalar right-hand side c_{number}")
        if isinstance(entry.rhs, Fraction)
        else to_complex128(
            entry.rhs.dense()
            if isinstance(entry.rhs, BlockOperator)
            else entry.rhs,
            what=f"the matrix right-hand side Theta_{number}",
        )
    )
    tag = entry.tag
    if tag is None:
        raise MalformedInputError(
            "a constraint entry crossing the boundary carries the tag its "
            "right-hand-side TYPE fixes; this entry's slot holds neither "
            "admitted object, which check V6 refuses (Definition def:homog)"
        )
    return ConsumerConstraintEntry(
        operator_blocks=sector_blocks(
            entry.operator, labels, what=f"the constraint operator O^_{number}"
        ),
        relation=RELATION_TO_CONSUMER[entry.relation],
        bound=bound,
        rhs_tag=CONSUMER_RHS_TAG[tag],
    )


def _consumer_partition(declaration: CandidateDeclaration) -> PartyPartition:
    """Convert the party partition, and say whether it IS the default.

    THE DEFAULT PARTITION IS SPELLED EXPLICITLY BY THIS MODULE -- open
    choice ``OC-party-partition``, decided in
    :func:`certiqs_key.protocol_compiler.spec.default_party_partition`'s
    docstring and realized here. The readouts and labels are always tabulated and handed
    across; ``is_default`` is COMPUTED from them rather than declared, so the
    flag cannot disagree with the tables it summarizes.

    THE DOCKING CONSEQUENCE, which is why the choice is named at all: the
    consuming wire format types ``party_partition`` as optional and says
    "absent spells the default partition", so a compiler that spelled the
    default BY ABSENCE would hand across a record from which the readout
    alphabets ``O_A`` and ``O_B`` would have to be RECONSTRUCTED -- and they
    coincide with ``X`` and ``V`` only under the default, which is exactly the
    accident Definition ``def:target``'s closing sentence warns about. Spelling
    it explicitly costs two tables and removes the reconstruction.
    """
    partition = declaration.partition
    is_default = (
        all(
            partition.alice_readout[(x, v)] == x for x, v in declaration.outcome_pairs()
        )
        and all(
            partition.bob_readout[(x, v)] == v for x, v in declaration.outcome_pairs()
        )
        and partition.alice_readout_alphabet == declaration.alice_alphabet
        and partition.bob_readout_alphabet == declaration.bob_alphabet
    )
    return PartyPartition(
        readout_alice=dict(partition.alice_readout),
        readout_bob=dict(partition.bob_readout),
        alphabet_alice=partition.alice_readout_alphabet,
        alphabet_bob=partition.bob_readout_alphabet,
        party_of_alice_system=(
            PartyLabel.ALICE
            if partition.alice_system_party is Party.ALICE
            else PartyLabel.BOB
        ),
        party_of_sector_factors={
            label: tuple(
                PartyLabel.ALICE if party is Party.ALICE else PartyLabel.BOB
                for party in factors
            )
            for label, factors in zip(
                declaration.sectors.labels,
                partition.sector_factor_parties
                or ((PartyLabel.BOB,),) * declaration.sectors.count,
                strict=False,
            )
        },
        is_default=is_default,
    )


def transported_entry_count(record: Mapping[str, object]) -> int:
    """Return how many entries of ``CList`` a reductions chain transported.

    THE SUPPLIER'S OWN DATUM, READ AND NOT RE-DERIVED. ``record`` is the
    compiler's ``reduction_chain_record``: two segments in the order
    ``def:compile`` concatenates them, each an ordered list of link records,
    each link record carrying ``transported_constraints`` -- THE COUNT of the
    entries that link contributed. Summing the counts gives the length of the
    transported TAIL of the emitted ``constraint_list``, because the
    concatenation puts the specification's own entries first.

    WHY THE ENGINE READS IT, given that no claim of this module reads it: it
    is carried as provenance into the run record's key-rate payload, and
    decides no row and no number (the soundness of THE LIST THAT MODULE
    EMITS is no ledger row).

    NOTHING IS INFERRED FROM A MALFORMED RECORD. A segment that is not a list,
    a link that is not a mapping, or a count that is not a non-negative integer
    is REFUSED rather than skipped or read as zero: zero is the answer for "no
    chain transported anything", and a record this function could not read must
    not be able to produce it.
    """
    total = 0
    for segment_name in ("source_segment", "receiver_segment"):
        segment = record.get(segment_name, [])
        if not isinstance(segment, list):
            raise MalformedInputError(
                f"the reduction chain record: {segment_name!r} is a list of "
                "link records (protocol-compiler `reduction_chain_record`); "
                f"got {type(segment).__name__}"
            )
        for link in segment:
            if not isinstance(link, Mapping):
                raise MalformedInputError(
                    f"the reduction chain record: every entry of {segment_name!r} "
                    "is a link record"
                )
            count = link.get("transported_constraints")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise MalformedInputError(
                    "the reduction chain record: `transported_constraints` is "
                    f"the number of entries a link transported; got {count!r}"
                )
            total += count
    return total


def _transported_against_the_list(
    record: Mapping[str, object] | None, entries: Sequence[object]
) -> int:
    """Return the transported count, REFUSED if it contradicts the list.

    A chain record describing more transported entries than the emitted
    ``CList`` HAS is not a record of that list. It is the same shape of
    disagreement as ``sector_map_disagreement`` -- a supplier record and the
    artefact it describes saying different things -- and this module refuses
    those rather than reading whichever it happens to hold: reading either
    would record a provenance the two artefacts contradict.

    IT CAN ONLY ARISE BY PAIRING TWO ARTEFACTS FROM DIFFERENT COMPILATIONS,
    which is a caller error and not a data path this repository has; that is
    why it is a refusal at the boundary and not a claim about anything.
    """
    if record is None:
        return 0
    count = transported_entry_count(record)
    if count > len(entries):
        raise MalformedInputError(
            f"the reduction chain record describes {count} transported "
            f"constraint entries and the emitted constraint list has "
            f"{len(entries)}. A record cannot transport more entries than the "
            "list it describes carries: by protocol-compiler/def:compile the "
            "transported entries are a TAIL of CList, so the count is at most "
            "its length. The two artefacts are not from one compilation"
        )
    return count


def dock_declaration(
    declaration: CandidateDeclaration,
    *,
    acceptance_set: AcceptanceSet,
    rounds: int,
    parameters: KeyLengthParameters,
    reduction_chain_record: Mapping[str, object] | None = None,
) -> ProtocolDeclaration:
    """Fill this module's declaration from the FIFTEEN shared keys.

    The three keyword arguments are the caller's to supply and this module's
    to refuse to invent -- see the module docstring for who owns each. They are
    keyword-only so that a call site cannot supply them positionally and get
    them the wrong way round.

    NOTHING IS ADJUSTED FOR THE CONSUMER. The values handed across are the ones
    this module emitted, converted and re-shaped -- per-sector blocks for
    ``bob_povm``, ``None`` for ``perp`` in the key map, the consuming
    spelling for the relation symbols -- and nothing is rounded, clipped,
    reordered or completed. The consumer's own
    ``validate_declaration`` is then an INDEPENDENT check of the same
    mathematics at the other end of the pipe, which is what makes it worth
    running; a docking adapter that repaired its input would collapse two
    fail-closed paths into one.

    ALL THREE COMPONENTS OF THE SECTOR MAP CROSS, and the comparison the
    contract asks for has something to compare. Definition ``def:declaration``
    makes ``sector_index_set``, ``sector_dims`` and ``sector_block_kind``
    machine keys "so that a consumer comparing sector maps can compare ALL
    THREE AND NOT TWO OF THEM". The consuming declaration has a slot for the
    kind and this hands the declared value across as the wire string, which is
    the shared format's ``BlockKind`` value (spec/architecture.md 2.9).

    NOTHING HERE INVENTS A KIND. ``SectorStructure`` refuses to be built
    without one, so there is no path on which this function would have to
    choose; and it hands over the value it was given rather than re-deriving
    one, which is the same rule the tag follows.

    THE TAG CROSSES TOO, in :func:`_consumer_entry`, and an entry that cannot
    carry one does not dock at all.

    ``reduction_chain_record`` IS THE FOURTH THING THE CALLER SUPPLIES, and it
    is the ONE OPTIONAL one. It is the compiler's own compiler-only key of that
    name -- which does not cross this boundary in the declaration, the
    declaration being the fifteen shared keys -- and what is taken from it is
    :func:`transported_entry_count`, the length of the transported tail of
    ``CList``. It decides NO LEDGER ROW AND NO NUMBER (the inherited
    ``constraints_sound`` is no row), and the count is carried as provenance
    only.

    ITS DEFAULT IS NOT A SUBSTITUTED DATUM, which the other three may not have.
    Absent, it records that NO CHAIN RECORD WAS SUPPLIED, and the docked
    declaration then says that no entry is established to have come through a
    reductions chain -- the state a hand-built declaration is in anyway. The
    difference from the other three is that each of them is read by the
    MATHEMATICS and a default would silently change a number, while this one
    is provenance only, and its absent state has a meaning of its own.
    """
    labels = declaration.sectors.labels
    dims = declaration.sectors.dims
    key_map: dict[tuple[str, str], int | None] = {}
    for pair, value in declaration.key_map.items():
        key_map[pair] = None if value == PERP else int(value)
    return ProtocolDeclaration(
        alice_dim=declaration.alice_dim,
        alice_marginal=(
            None
            if declaration.alice_marginal is None
            # EVERY entry of tau_A, and not only its diagonal. Check V2 reads
            # the trace, which touches the diagonal alone, so the off-diagonal
            # entries are decided HERE and nowhere earlier.
            else to_complex128(
                declaration.alice_marginal, what="the declared marginal tau_A"
            )
        ),
        sector_index_set=labels,
        sector_dims=dict(zip(labels, dims, strict=True)),
        sector_block_kind=declaration.sectors.block_kind.value,
        alice_povm={
            label: to_complex128(
                declaration.alice_povm[label], what=f"the emitted M_{label!r}"
            )
            for label in declaration.alice_alphabet
        },
        bob_povm={
            label: sector_blocks(
                declaration.bob_povm[label], labels, what=f"the emitted F_{label!r}"
            )
            for label in declaration.bob_alphabet
        },
        announce_alice=dict(declaration.announce_alice),
        announce_bob=dict(declaration.announce_bob),
        accept_statistic=dict(declaration.accept_statistic),
        key_map=key_map,
        key_holder=(
            KeyHolder.ALICE if declaration.key_holder is Party.ALICE else KeyHolder.BOB
        ),
        acceptance_values=declaration.acceptance_alphabet,
        key_value_count=len(declaration.key_alphabet),
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
        constraint_list=tuple(
            _consumer_entry(entry, labels, dims, index)
            for index, entry in enumerate(declaration.constraint_list)
        ),
        constraints_through_a_reductions_chain=_transported_against_the_list(
            reduction_chain_record, declaration.constraint_list
        ),
        attack_set_license=(
            None
            if declaration.attack_set_license is None
            else {
                "supplier": declaration.attack_set_license.supplier,
                "statement": declaration.attack_set_license.statement,
            }
        ),
        source_replacement_license=(
            None
            if declaration.source_replacement_license is None
            else _license_record(declaration.source_replacement_license)
        ),
        party_partition=_consumer_partition(declaration),
    )


def _license_record(licence: object) -> dict[str, object]:
    """Return the source-replacement licence as the consumer's opaque record.

    A PASS-THROUGH ACROSS THE BOUNDARY TOO. This engine acts on its PRESENCE
    and never on its content, and the compiler may never assert (SR3)
    of an apparatus (``transmitter/req:attestation-record``), so the record that crosses
    carries the same ``asserted_by_this_module = False`` the emitted one does.
    """
    from certiqs_key.transmitter.certificate import SourceReplacementLicense

    if not isinstance(licence, SourceReplacementLicense):  # pragma: no cover
        raise MalformedInputError(
            "the source-replacement licence is this module's record"
        )
    return licence.as_machine_record()


def compiler_emission(declaration: CandidateDeclaration) -> CompilerEmission:
    """Return the token that ``declaration`` is the protocol compiler's emission.

    ``req:compiled-declaration-only``: a key length is reported only on a
    declaration the compiler emitted. THE TOKEN IS MINTED HERE because this is
    the one file of the package that reads the compiler's type: the run tier
    calls it on the declaration its compilation emitted and passes the token,
    in memory, beside the bundle it writes and reads back
    (:mod:`certiqs_key.meat_core.provenance`).
    The bundle and the wire carry nothing of it.

    Raises:
        TypeError: on anything but a compiler declaration.
    """
    if not isinstance(declaration, CandidateDeclaration):
        raise TypeError(
            "compiler_emission takes the compiler's emitted CandidateDeclaration, "
            f"got {type(declaration).__name__}"
        )
    return CompilerEmission(emitted_by=COMPILER_SPEC_VERSION)
