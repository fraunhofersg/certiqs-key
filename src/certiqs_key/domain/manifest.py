"""The operator-bundle manifest: envelope, alphabets, declaration, parameters.

The envelope is the one spec/architecture.md 4.1 puts on every top-level
artifact, in the subset that section says is in use now. The four deferred
fields -- ``artifact_id``, ``content_hash``, ``input_artifact_hashes`` and
``provenance`` -- are omitted, and because every model forbids extra keys they
are *rejected* rather than silently swallowed. 4.1's forward-compatibility
rule is what makes that the right behaviour: no field may be given a meaning
incompatible with the one it will carry once content-addressing switches on,
and accepting a hash field that nothing hashes would be exactly that.

The payload is the ``meat-core`` contract 0.4.0 Section 2.1 inputs table under
``declaration`` and its Section 2.4 parameters under ``parameters``, using that
contract's machine keys verbatim, plus one ``alphabets`` section that names the
finite sets those tables are indexed by. The alphabets are not an addition to
the contract's input set: the Section 2.1 table types ``announce_alice`` and
friends
as *total function tables*, and totality is not a statement about a table until
its domain and codomain are written down.

WHAT THIS FORMAT READS: 0.3.0 AND 0.4.0
=======================================
:data:`SUPPORTED_SCHEMA_VERSIONS` is ``("0.3.0", "0.4.0")``. A manifest stamped
``0.1.0`` or ``0.2.0`` is refused, by name, with a machine-readable reason
(:class:`~certiqs_key.domain._base.RetiredSchemaVersionError`, raised from
:func:`~certiqs_key.domain.bundle.parse_manifest`); an unknown version is refused
too, because there is no conversion path and guessing one is a silent repair.

The drop is spec/architecture.md 2.9 ("the bundle schema carries the
sector-block operator form and reads no earlier version that could express a
full-space operator"): a reader that still accepts them keeps the removed form
alive at the one boundary where it would matter. Nothing readable is lost that
cannot be rebuilt, because a bundle tree is regenerable from its instance.

THE STAMP IS THE LOWEST VERSION THAT CAN EXPRESS THE DOCUMENT
=============================================================
:data:`SCHEMA_VERSION` -- what a writer stamps on a payload of today's shape --
stays ``0.3.0``, and :data:`SCHEMA_VERSION_FACTORISED` is ``0.4.0``, the stamp
of a payload that uses a key 0.4.0 added. :func:`schema_version_for` computes
which of the two a payload needs and the manifest model REFUSES a stamp below
it, so the version on a bundle is a fact about that bundle rather than a fact
about the day it was written.

That rule is the one spec/architecture.md 4.1's forward-compatibility sentence
asks for at the only place it bites: a bundle for a one-``Q``-factor,
one-Alice-sector declaration is BYTE-IDENTICAL to what this format wrote before
0.4.0 existed -- same keys, same stamp, same bytes -- because the key 0.4.0
adds is written only when it is used (:meth:`Declaration.serialize`), and a reader
of an old bundle needs nothing new to read it. Stamping every new bundle 0.4.0
instead would have moved the stamp in files that say exactly what they said
before, and with it the frozen fixtures that pin them; a version that moves when
nothing else does is a version that says nothing.

THE THREE CONTRACT-0.3.0 SLOTS
==============================
``meat-core`` contract 0.3.0 widened the declaration type: ``alice_marginal``
became a *slot* over ``S_=(A) u {none}``, and ``source_replacement_license``
and ``party_partition`` joined the table. The three are carried as OPTIONAL
keys, and every absent key has exactly the meaning the contract gives it --
which is why widening the declaration needed no format version of its own:

* ``alice_marginal`` absent or ``null`` spells the slot value ``none``, which
  contract Remark ``rem:source-mode`` *defines* to be untrusted-source mode.
  That default is the conservative one: Remark ``rem:source-mode`` (a) proves
  ``h_low(untrusted) <= h_low(trusted)`` always, so a producer that omits the
  key loses rate and can never overstate it. ``null`` is deliberately not
  ``0`` -- ``tau_A = 0`` is inadmissible (``rem:source-mode`` (c)) and is
  rejected downstream by the trace-one check of def:admissible-declaration (ii);
* ``source_replacement_license`` absent means no A-SRC attestation was
  supplied, which closes the key-length gate of Section 4.19 whenever a
  ``tau_A`` is declared at ``d_A >= 2``;
* ``party_partition`` absent means the DEFAULT partition of Definition
  ``def:declaration`` (``pi_A(x, v) = x``, ``pi_B(x, v) = v``), which that
  definition says "reproduces versions 0.2.x of this contract verbatim".

Nothing in spec/architecture.md 4.1's forward-compatibility rule is strained:
no field is given a meaning incompatible with the one it already carried.

``reduction_chain``: THE ONE FIELD 0.2.0 ADDED, AND IT STAYS
============================================================
``reduction_chain`` entered the format at version 0.2.0 and is carried at
0.3.0 unchanged, still OPTIONAL. It is the ``reduction_chain`` slot
spec/architecture.md 4.2 lists beside the declaration and 3.6 asks bundle
validation to check ("every physical or source reduction is represented in the
reduction chain"). Before it a compiled chain travelled only in the protocol
compiler's own artifact; it is carried here for the identity link an
ideal-qubit slice reduces by, recorded in the bundle as an ``exact``
reduction.

IT SITS ON THE **PAYLOAD** AND NOT INSIDE ``declaration``, and the placement is
load-bearing rather than a matter of taste. It rests on two things, and
spec/architecture.md 4.2 is NOT one of them: that section lists the reduction
chain record beside the declaration without prescribing any nesting, in a flat
list that also names the trusted marginal, the constraint list and the
acceptance statistic -- all of which this format does nest inside
``payload.declaration``. So it settles nothing either way. What does settle
it:

* :class:`Declaration` is documented as exactly "the ``meat-core`` contract
  0.4.0 Section 2.1 inputs, by their machine keys", and a reduction chain is
  not one of those inputs -- it is ``protocol-compiler``'s OUTPUT key
  ``reduction_chain_record``. Nesting it there would put a key in the
  Section 2.1 input table that the consuming contract does not have, which is
  the one thing that table must not acquire;
* the protocol compiler's frozen oracle registry pins the wire
  :class:`Declaration` at SEVENTEEN fields -- the fifteen declaration slots
  plus ``acceptance_set`` and ``rounds``. A sixteenth declaration key would
  break it.

``reduction_chain`` is **carried, never interpreted**. This module checks its
shape -- the status vocabulary, a non-empty receiver segment, positive
dimensions, sector dimensions that sum to the system they decompose -- and
decides nothing about whether the reduction is sound. That is
``reductions``' and ``meat-core``'s, exactly as with ``acceptance_set``.
A violation of any of those shape conditions is a hard error and never a
warning (spec/architecture.md 3.6).

SCHEMA 0.3.0 AND THE ONE THING IT NARROWS
=========================================
Format version **0.3.0** adds no field. It narrows one: **an operator payload
is a** :class:`~certiqs_key.domain.arrays.BlockDiagonalOperator` **and nothing
else**. The two operator slots are ``payload.declaration.bob_povm`` and
``payload.declaration.constraint_list[*].operator``.

That is the design of spec/architecture.md 2.8, 2.9:
from construction to bundle, an operator is a list of sector blocks plus
the sector map that names them, sector-block-diagonality holds BY CONSTRUCTION,
and no ``d_Q x d_Q`` array is materialized on a live path.

**NOTHING IN THIS MODULE ENFORCES THAT NARROWING, AND THAT IS THE POINT.** The
narrowing is carried by the TYPE:
:data:`~certiqs_key.domain.arrays.OperatorRef` *is*
:class:`~certiqs_key.domain.arrays.BlockDiagonalOperator`, so a full-space
:class:`~certiqs_key.domain.arrays.ArrayDescriptor` in an operator slot is not a
document this format can express, and it is refused by ordinary field
validation naming the slot. There is no version conditional policing the
operator form, for spec/architecture.md 2.9's own reason: "nothing verifies
that off-sector entries vanish, because nothing can write them".

THE VERSIONS AND WHAT THEIR STAMPS MEAN
=======================================
Not a live rule -- :data:`SUPPORTED_SCHEMA_VERSIONS` above is the live rule --
but kept so that a reader of an old bundle knows what the stamp on it meant:

* **0.1.0** -- the original format. No ``reduction_chain`` field; an operator
  payload could be a full-space array or a list of blocks.
* **0.2.0** -- adds exactly one optional payload field, ``reduction_chain``,
  and changes the meaning of nothing else. Absent means "no reduction chain was
  recorded", which is what every 0.1.0 bundle says by construction, so a 0.1.0
  bundle and the same bundle re-stamped 0.2.0 denoted the same declaration.
* **0.3.0** -- adds no field and narrows the operator payload to the block
  form.
* **0.4.0** -- adds the OPTIONAL KEYS OF THE GENERAL FORMAT, all of them inside
  ``declaration``, and changes the meaning of nothing else. Absent, every one of
  them spells the DEGENERATE CASE, which is what every 0.3.0 bundle says by
  construction -- one measured factor, one undecomposed ``A``, POVM form, two
  independent messages and no scoped entry -- so a 0.3.0 bundle and the same
  bundle re-stamped 0.4.0 denote the same declaration, and a 0.3.0 bundle stays a
  0.3.0 bundle.

**0.1.0 and 0.2.0 are no longer read.** They can express a full-space operator,
which is the whole reason for the drop, and a bundle stamped either is refused
by name rather than converted -- converting one would require this module to
invent a sector map, which is a mathematical claim and not a format conversion.

SCHEMA 0.4.0 AND THE GENERAL FORMAT: THE KEYS, AND WHERE THEY LIVE
=================================================================
``def:declaration`` (DX1) makes the factorised sector map a SLOT of the
declaration, so ``payload.declaration.sector_factorisation`` is where it lives
and a record carrying it on the payload is refused by ordinary field
validation (every model forbids extra keys) (spec/architecture.md 4.1).

The keys 0.4.0 adds, each OPTIONAL and each absent in the degenerate case
(``protocol-compiler``/``meat-core`` ``def:declaration`` (DX1)--(DX6), and the
``general_format`` convention of both ``interface.yaml``):

``declaration.sector_factorisation``
    the ordered FACTOR LIST of (DX1). The product sector map, the product outcome
    alphabet and the joint sectors are DERIVED from it and are emitted by no one;
    ``sector_index_set``/``sector_dims`` keep their meaning and are what the
    ``Q`` side flattens to.
``declaration.alice_form``, ``declaration.alice_ensemble``
    which of (DX4)'s two slots is filled, and the blocks ``N_x`` where it is the
    ensemble slot -- in place of ``alice_povm`` and never beside it. The POVM the
    ensemble form DENOTES (``eq:ensemblepovm``) is not a key and is formed by no
    one.
``declaration.transcript``
    the ordered message list of (DX5). ``announce_alice`` and ``announce_bob``
    REMAIN the emitted form of the two-message case, so a transcript key appears
    only where ``L != 2`` or a later message reads an earlier one; the joint
    announcement alphabet and function are derived by ``eq:transcript`` and are
    not keys.
``constraint_list[*].scope``
    the measured factor of (DX6) an entry's operator is written against. The
    LIFTED operator is not a key and is formed by no one.

``declaration.alice_marginal_blocks``, ``alice_povm_blocks``, ``bob_povm_factors``
    THE GENERAL SPELLING OF THREE SLOTS THAT ALREADY HAVE ONE -- ``tau_A`` and
    ``{M_x}`` as block lists along ``T`` (DX2), and the measured family per factor
    (DX3). Each stands IN PLACE OF the degenerate key and never beside it, and
    :meth:`Declaration._exactly_one_spelling_per_slot` refuses a document that
    fills a slot twice.

    A SIBLING KEY RATHER THAN A WIDENED TYPE, which is a reading this
    implementation takes and records: widening ``alice_marginal`` or ``bob_povm``
    into a union would make every consumer that reads them today read a type it was
    not written for, at keys whose absence already carries meaning. A separate key
    cannot be mistaken for the dense one, and a consumer that has not learned the
    general format sees the marginal slot as EMPTY, which is untrusted-source mode
    and is the conservative reading (``meat-core`` ``rem:source-mode`` (a)).

``constraint_rhs_tag`` NEEDED NO SCHEMA CHANGE for the third tag value
``party_local``: this format has always carried the declared string and decided
nothing about what it means, and the type check that reads it is the consumer's
(``def:validator`` V6).
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import (
    Field,
    JsonValue,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

from certiqs_key.domain._base import StrictModel
from certiqs_key.domain.arrays import (
    ArrayDescriptor,
    OperatorRef,
)
from certiqs_key.domain.families import AliceForm
from certiqs_key.foundations.blocks import PRODUCT_LABEL_SEPARATOR, SystemTag

#: The version a writer stamps on a payload of TODAY'S SHAPE -- one ``Q``
#: factor, one undecomposed ``A`` -- which is every payload no producer in this
#: tree has yet learned to widen. A bundle declaring a version outside
#: :data:`SUPPORTED_SCHEMA_VERSIONS` is rejected: there is no conversion path,
#: and guessing one is a silent repair.
#:
#: IT DOES NOT MOVE WITH 0.4.0, and the module docstring says why: the
#: stamp is the lowest version that can express the document, so a bundle that
#: says what it said before says it in the same bytes.
SCHEMA_VERSION = "0.3.0"

#: The version a writer stamps once the payload carries a key 0.4.0 added -- the
#: GENERAL-FORMAT keys of the module docstring, every one of them inside
#: ``declaration``. A writer does not choose between the two:
#: :func:`schema_version_for` computes it from the payload, and the manifest model
#: refuses a stamp below what the payload needs.
#:
#: THE NAME SAYS "FACTORISED" although the version carries more than the
#: factorised map: what 0.4.0 means is the docstring's to say.
#: :data:`GENERAL_FORMAT_KEYS` is the list.
SCHEMA_VERSION_FACTORISED = "0.4.0"

#: Every version a reader accepts. Read support for 0.1.0 and 0.2.0 is dropped
#: (spec/architecture.md 2.9), because those versions can express a full-space
#: operator and a reader that accepts them keeps the removed form alive at the
#: one boundary where it would matter.
#:
#: The set a reader ACCEPTS is the ``Literal`` on
#: :attr:`OperatorBundleManifest.schema_version`; this tuple must not drift
#: from it.
SUPPORTED_SCHEMA_VERSIONS: tuple[str, ...] = ("0.3.0", "0.4.0")

#: The versions this format does not read. They are named
#: rather than folded into "unknown version" so that the refusal can say what
#: happened: a bundle stamped one of these was well-formed once, it is not
#: malformed now, and its instance can regenerate it. A version outside both
#: tuples is unknown and is refused as such.
RETIRED_SCHEMA_VERSIONS: tuple[str, ...] = ("0.1.0", "0.2.0")

#: The machine-readable reason a retired version is refused under. It is the
#: ``reason`` of :class:`~certiqs_key.domain._base.RetiredSchemaVersionError`.
RETIRED_SCHEMA_VERSION_REASON = "schema_version_retired"

#: The artifact kind this module reads and writes.
KIND = "operator-bundle"

#: ``<module-id>@<contract_version>``, with no pre-release suffix. The
#: ``meat-core`` contract Section 2.4 is explicit: "no artifact may claim a
#: draft version", so ``meat-core@0.5.0-draft`` is refused and
#: ``meat-core@0.5.0`` is not. The example names an ACCEPTED version
#: deliberately; this pattern pins none.
SPEC_VERSION_PATTERN = re.compile(
    r"^[a-z][a-z0-9-]*@(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){2}$"
)

#: Envelope fields spec/architecture.md 4.1 defers. Present in a manifest,
#: each is a hard error.
DEFERRED_ENVELOPE_FIELDS = (
    "artifact_id",
    "content_hash",
    "input_artifact_hashes",
    "provenance",
)


class KeyHolder(StrEnum):
    """The declared key holder ``h`` of the ``meat-core`` Section 2.1 table."""

    ALICE = "A"
    BOB = "B"


class PartyLabel(StrEnum):
    """Which party holds a declared system (contract Def. ``def:declaration``).

    Part (b) of the party partition: the label of the register ``A`` and one
    per declared tensor factor of every ``H(Q_s)``. It is *metadata* carrying a
    supplier obligation (``protocol-compiler``) that ``meat-core`` never
    verifies and no derivation consumes; the laboratory premise
    ``meat-core/ass:lab`` reads it as naming the parties' laboratories, and it
    is carried so that the obligation is written down where a reader of the
    bundle can see it.
    """

    ALICE = "A"
    BOB = "B"


class ConstraintRelation(StrEnum):
    """The relation of one constraint-list entry.

    Contract Section 2.1 writes ``bowtie_k in {preceq, =, succeq}`` ONCE and
    types only the right-hand side by source mode, so these three machine keys
    serve both modes: they denote the operator order when ``Theta_k`` is
    Hermitian on ``A`` (trusted-source mode) and the order of the reals when
    ``Theta_k = c_k`` is a scalar (untrusted-source mode; def:admissible-declaration
    (vi), Definition ``def:homog`` (b)). The spelling stays operator-shaped
    because the type of the bound, not the name of the relation, is what the
    mode changes.
    """

    PRECEQ = "preceq"
    EQ = "eq"
    SUCCEQ = "succeq"


class Alphabets(StrictModel):
    """The finite sets the declaration's tables are indexed by.

    Each is an ordered tuple of stable IDs. The order is canonical and is what
    a consumer must use when it turns an alphabet into array positions; JSON
    object key order is not a guarantee this format relies on.
    """

    alice_outcome: tuple[str, ...] = Field(min_length=1)
    bob_outcome: tuple[str, ...] = Field(min_length=1)
    #: The accepted two-message announcement alphabets. Empty in the general
    #: transcript format, where every message carries its own alphabet.
    alice_announcement: tuple[str, ...] = ()
    bob_announcement: tuple[str, ...] = ()
    acceptance_value: tuple[str, ...] = Field(min_length=1)
    key_value_count: Annotated[int, Field(ge=1)]


class Constraint(StrictModel):
    """One entry of the ``meat-core`` Section 2.1 ``constraint_list``.

    ``bound`` is ``Theta_k``, whose TYPE is fixed by the declared source mode
    (contract Definition ``def:declaration``; def:admissible-declaration (vi)): a
    Hermitian ``d_A x d_A`` array in trusted-source mode, and a real scalar
    ``c_k`` in untrusted-source mode. Both spellings are accepted here as
    *data* -- an array descriptor or a JSON number -- and which one a
    particular declaration is allowed to use is decided against its mode by
    ``meat-core`` itself. The
    distinction is not cosmetic: contract Remark ``rem:homog`` (a) exhibits a
    licensed attack set for which reading an untrusted-mode entry as the
    operator form ``Theta_k = c_k 1_A`` empties the feasible set.
    """

    operator: OperatorRef
    relation: ConstraintRelation
    bound: ArrayDescriptor | float
    #: The DECLARED FORM of this entry's right-hand side:
    #: ``homogeneous`` -- ``bound`` is the real scalar ``c_k``, the licensed
    #: form -- or ``general`` -- ``bound`` is a Hermitian ``Theta_k`` on ``A``,
    #: admissible input and never licensed (``protocol-compiler`` 0.3.0
    #: Definition ``def:homog``).
    #:
    #: REQUIRED, AND CARRYING NO DEFAULT.
    #: This format transports the tag; it does not
    #: invent one, and it does not read one off ``bound``, because the tag is a
    #: DECLARED datum and a format-supplied one "would be a code default
    #: deciding a security-relevant predicate ... on nobody's authority"
    #: (``meat-core``'s own constraint row).
    #:
    #: WHY REQUIRED RATHER THAN OPTIONAL-AND-REFUSED-DOWNSTREAM. Now that
    #: ``meat-core``'s licensed-class type check reads the tag off every
    #: entry, an entry without one cannot be consumed by anybody: the only
    #: outcome of admitting it here is a refusal three stages later, naming the
    #: engine rather than the producer that omitted it. Requiring it makes the
    #: bundle unreadable at the boundary, which is where the producer is still
    #: identifiable. The refusal is a
    #: :class:`~certiqs_key.domain._base.BundleValidationError` naming the entry,
    #: not a substituted ``general``.
    #: SINCE BATCH C3 THE VOCABULARY HAS A THIRD VALUE, ``party_local``, and this
    #: field needed no change to carry it: the format has always transported the
    #: declared string and decided nothing about what it means. What it means is
    #: ``def:homog``'s party-local form, and the type check that reads it -- the
    #: datum must be a real scalar and the scope must name a measured factor -- is
    #: the consumer's (``def:validator`` V6).
    constraint_rhs_tag: str
    #: THE ENTRY'S SCOPE OF ``def:declaration`` (DX6), OPTIONAL, new at 0.4.0: the
    #: label of the ONE measured factor of ``sector_factorisation`` that
    #: ``operator`` is a block list against. Absent is the degenerate case, one
    #: measured factor, where "the scope is that factor" -- so absence is a value
    #: and not an unknown.
    #:
    #: THE LIFTED OPERATOR IS NOT A KEY. (DX6)'s ``1 (x) O_k (x) 1`` "is never
    #: formed as a datum", here or downstream.
    scope: str | None = None

    @model_serializer(mode="wrap")
    def serialize(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        """Serialize the entry, WRITING ``scope`` ONLY WHERE ONE IS DECLARED.

        The stamp rule at the entry level: an entry of today's shape carries the
        bytes it carried before 0.4.0 existed, so a bundle whose entries are all
        unscoped is byte-identical to the one this format wrote for it yesterday.
        """
        document: dict[str, Any] = handler(self)
        if self.scope is None:
            document.pop("scope", None)
        return document

    @field_validator("bound", mode="before")
    @classmethod
    def _reject_boolean_bound(cls, value: object) -> object:
        """Reject ``true``/``false``, which JSON would otherwise widen to 1/0.

        ``mode="before"`` is load-bearing: by the time an "after" validator
        runs, pydantic has already widened ``True`` to ``1.0`` and the
        distinction is gone.
        """
        if isinstance(value, bool):
            raise ValueError(
                "a scalar constraint bound is a real number c_k, not a boolean"
            )
        return value


class AcceptanceSet(StrictModel):
    """The declared acceptance set, carried without being interpreted.

    ``geometry`` names the construction; its taxonomy belongs to
    ``statistics``, so this module records the tag and does not
    enumerate it -- deliberately, and still, now that that module has an
    accepted contract: enumerating another module's taxonomy in a wire FORMAT
    would make every extension of it a schema version bump. ``data`` holds JSON
    scalars and ``arrays`` holds array descriptors, both of which take part in
    the ordinary well-formedness checks. Whether the set is convex, closed, or
    a subset of the simplex is ``meat-core``'s to decide (its Definition
    def:admissible-acceptance-set); nothing here asserts it, and nothing here reads the
    sub-keys a tag puts in ``data``.
    """

    geometry: str = Field(min_length=1)
    data: dict[str, JsonValue] = Field(default_factory=dict)
    arrays: dict[str, ArrayDescriptor] = Field(default_factory=dict)


class PartyPartition(StrictModel):
    """The party partition ``P`` of contract Definition ``def:declaration``.

    Part (a) -- the READOUT MAPS -- is the only part any derivation consumes,
    and it is consumed only through def:admissible-declaration (viii): each party
    announces a function of its own readout, and the declared key holder
    computes the raw key from ITS OWN readout and the announcements
    (Eq. ``eq:partycomp``). ``readout_alice[x][v]`` and ``readout_bob[x][v]``
    are those total maps on ``X x V``, keyed the way every other binary table
    in this format is.

    Part (b) -- ``party_of_alice_system`` and ``party_of_sector_factors`` -- is
    system metadata: the party label of ``A``, and one label per declared
    tensor factor of each ``H(Q_s)``. It carries a supplier obligation
    (``protocol-compiler``) that ``meat-core`` never verifies and no
    derivation consumes; ``ass:lab`` (A-LAB) reads its labels as naming the
    parties' laboratories.

    DISCLOSED NARROWING inside part (b): the contract's ``def:declaration``
    names the tensor FACTORIZATION ``H(Q_s) = (x)_i H(Q_{s,i})`` as well as the
    labels, and this record carries only the labels -- the factor dimensions
    are not serialized. Nothing here or downstream reads them: part (b) is
    metadata for a supplier obligation this module never verifies, and the
    contract says in as many words that "no claim below depends on it". A
    consumer that needs the factorization is ``protocol-compiler``, whose
    contract will fix its own shape for it.

    OMITTING the whole record spells the DEFAULT partition of
    ``def:declaration`` -- ``pi_A(x, v) = x``, ``pi_B(x, v) = v``, ``A``
    labelled ``A`` and every ``Q_s`` labelled ``B`` -- which that definition
    says "reproduces versions 0.2.x of this contract verbatim".
    """

    readout_alice: dict[str, dict[str, str]]
    readout_bob: dict[str, dict[str, str]]
    alphabet_alice: tuple[str, ...] = Field(min_length=1)
    alphabet_bob: tuple[str, ...] = Field(min_length=1)
    party_of_alice_system: PartyLabel
    party_of_sector_factors: dict[str, tuple[PartyLabel, ...]]


class ReductionStatus(StrEnum):
    """The status of one reduction link (spec/architecture.md 4.3).

    The three-member vocabulary the architecture fixes -- ``exact``,
    ``certified_outer``, ``exploratory_numeric`` -- and there is no fourth. It
    is declared here rather than imported from
    :mod:`certiqs_key.protocol_compiler` because a
    wire format may not depend on a producer: the same vocabulary is spelled
    independently at both ends, and a disagreement is a defect a test catches
    rather than a silent coupling.

    NOTHING HERE BRANCHES ON A STATUS. spec/architecture.md 4.3's consequence
    -- "an ``exploratory_numeric`` link never satisfies a dependency a key
    length rests on" -- belongs to the consumer that decides it.
    ``certified_outer`` here is a LINK STATUS and not a tier, exactly as
    :class:`certiqs_key.domain.chain.LinkStatus` already records.
    """

    EXACT = "exact"
    CERTIFIED_OUTER = "certified_outer"
    EXPLORATORY_NUMERIC = "exploratory_numeric"


class ReductionSegment(StrEnum):
    """Which of the two ordered segments a link was written into.

    spec/architecture.md 3.2: *composition order is
    data* -- source maps before receiver squashing -- "even when the chain has
    one link, so that decoy support cannot later compose in the wrong order
    silently". Two named lists is how that order is carried.
    """

    SOURCE = "source"
    RECEIVER = "receiver"


class ReductionSide(StrEnum):
    """Whether a system descriptor is Alice-side or receiver-side."""

    ALICE = "alice"
    RECEIVER = "receiver"


class ReductionSystemDescriptor(StrictModel):
    """One source or target descriptor of a reduction link.

    ``sectors`` is the declared decomposition of the system, present only where
    a link declares one -- on the target of the last receiver link, which is the
    ``(Q, S, (d_s))`` a declaration is built from. Where it is present its
    dimensions must sum to :attr:`dim`; a decomposition that does not decompose
    its own system is a defect, refused rather than reconciled.
    """

    name: str = Field(min_length=1)
    dim: Annotated[int, Field(ge=1)] | None
    side: ReductionSide
    sectors: tuple[tuple[str, Annotated[int, Field(ge=1)]], ...] | None = None
    #: THE THIRD COMPONENT OF THIS DESCRIPTOR'S SECTOR MAP.
    #: ``protocol-compiler`` 0.3.0 emits it beside ``sectors`` on
    #: every link descriptor, and a model that forbade it rejected the whole
    #: chain as ``extra_forbidden`` -- which then read as ``receiver_segment``
    #: being empty, because a link that fails validation is not a link.
    #:
    #: PRESENT EXACTLY WHERE ``sectors`` IS, and that is decided rather than
    #: defaulted (:meth:`_kind_travels_with_the_map` below). The two are ONE
    #: OBJECT: Definition ``def:declaration`` says ``Smap`` is the ordered list
    #: "TOGETHER WITH the block kind that names what the identifiers mean; it
    #: is ONE OBJECT". A descriptor that declared identifiers without saying
    #: what they mean, or a kind for identifiers it did not declare, is half a
    #: map, and this format refuses half a map rather than completing it.
    sector_block_kind: str | None = None

    @model_validator(mode="after")
    def _kind_travels_with_the_map(self) -> ReductionSystemDescriptor:
        """Refuse a descriptor that declares one half of its sector map.

        FAIL-CLOSED AND NEVER INFERRED. ``protocol-compiler`` Section 2.5
        (``decide_never_infer``) forbids supplying a kind for identifiers
        somebody else wrote, and this format has even less standing to: it
        transports the map and decides nothing about what its identifiers mean.
        """
        if self.dim is None and self.side is not ReductionSide.ALICE:
            raise ValueError(
                "only an Alice-side source descriptor may carry dim=null; "
                "receiver descriptors are finite and (C1) reads their dimension"
            )
        if (self.sectors is None) != (self.sector_block_kind is None):
            declared, missing = (
                ("sectors", "sector_block_kind")
                if self.sectors is not None
                else ("sector_block_kind", "sectors")
            )
            raise ValueError(
                f"the descriptor {self.name!r} declares {declared} and no "
                f"{missing}. A sector map is ONE OBJECT -- the ordered list of "
                "identifiers and dimensions TOGETHER WITH the block kind that "
                "names what the identifiers mean (protocol-compiler 0.3.0, "
                "def:declaration) -- and half of one is refused rather than "
                "completed"
            )
        return self


class ReductionLink(StrictModel):
    """One typed link of the reduction chain, carried as data.

    Every slot is emitted whether or not it is empty. The reason is
    ``protocol-compiler``'s Requirement ``req:chain-record-slots``, and it applies just
    as much on the wire: "a record shape that omits an empty slot cannot later
    distinguish 'no entries' from 'entries not carried'".

    ``transported_constraints`` is a COUNT and not the entries themselves: the
    entries a link transports are emitted into the declaration's own
    ``constraint_list``, and duplicating them here would give one datum two
    homes. ``channel_supplied`` records whether the link presented its channel as
    data or only a theorem constructor -- the fact a reader needs in order to
    know whether an identity was CHECKED or assumed. The Kraus matrices
    themselves are not serialized, for the reason
    :mod:`certiqs_key.protocol_compiler`'s chain record gives.
    """

    link_id: str = Field(min_length=1)
    segment: ReductionSegment
    link_type: str = Field(min_length=1)
    source_descriptor: ReductionSystemDescriptor
    target_descriptor: ReductionSystemDescriptor
    status: ReductionStatus
    channel_supplied: bool
    transported_constraints: Annotated[int, Field(ge=0)]
    license_slot_present: bool
    license_slot_empty: bool


class ReductionChain(StrictModel):
    """The chain of typed links behind a declaration (spec/architecture.md 4.2).

    Two segments in their composition order, plus the correspondence between the
    physical outcome alphabet and the emitted one. ``source_segment`` is present
    and empty rather than absent where a protocol declares no source map, which
    is what makes "no source maps" distinguishable from "source maps not
    carried".

    ``receiver_segment`` is non-empty: the emitted receiver data IS the last
    receiver link's target, so a chain with no receiver link describes no
    declaration. An ideal-qubit protocol satisfies this with a single identity
    link at status ``exact``.
    """

    source_segment: tuple[ReductionLink, ...] = ()
    receiver_segment: tuple[ReductionLink, ...] = Field(min_length=1)
    #: ``(physical outcome, emitted outcome)`` pairs, in the chain's own order.
    outcome_correspondence: tuple[tuple[str, str], ...] = Field(min_length=1)


class ReceiverFactorSegment(StrictModel):
    """One measured factor's receiver chain and local outcome map."""

    factor_label: str = Field(min_length=1)
    party: str = Field(min_length=1)
    receiver_segment: tuple[ReductionLink, ...] = Field(min_length=1)
    outcome_correspondence: tuple[tuple[str, str], ...] = Field(min_length=1)


class FactorReductionChain(StrictModel):
    """The source segment once, then one receiver segment per measured factor."""

    source_segment: tuple[ReductionLink, ...] = ()
    receiver_factor_segments: tuple[ReceiverFactorSegment, ...] = Field(min_length=1)


class SectorFactorRecord(StrictModel):
    """One factor of a factorised sector map (spec/architecture.md 2.9).

    The wire spelling of :class:`~certiqs_key.foundations.blocks.SectorFactor`: the
    SYSTEM it decomposes, the PARTY that holds it, and that factor's own ordered
    ``((s, d_s))_s``. NEW AT SCHEMA 0.4.0.

    THE BLOCK KIND IS NOT HERE, and its absence is the rule rather than an
    omission: "the factors of one map carry one block kind, because the
    flattened map carries one" (2.9), and the declaration already has exactly
    one key for it -- :attr:`Declaration.sector_block_kind`. A per-factor kind
    would be a second home for one datum and would let a document declare the
    mixture 2.9 refuses.

    ``system`` IS a fixed alphabet -- the round model has the retained ``A`` and
    a measured ``Q`` and no third system -- where ``party`` is the declaration's
    own string, exactly as 2.9 splits them.
    """

    system: SystemTag
    party: str = Field(min_length=1)
    sectors: tuple[tuple[str, Annotated[int, Field(ge=1)]], ...] = Field(min_length=1)
    #: THE FACTOR'S OWN NAME, OPTIONAL, and absent is the position default
    #: :func:`~certiqs_key.foundations.blocks.default_factor_label`. It is not the
    #: party: a party may hold two factors, so a scoped constraint entry's ``scope`` is
    #: compared against THESE labels and never against party labels
    #: (``protocol-compiler`` ``def:declaration`` (DX6), ``def:validator`` V6).
    #: ``reductions``' factor emission declares one per factor and carries the
    #: party beside it.
    label: str | None = Field(default=None, min_length=1)

    @model_serializer(mode="wrap")
    def serialize(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        """Write ``label`` only where one is declared, so the default costs no bytes."""
        document: dict[str, Any] = handler(self)
        if self.label is None:
            document.pop("label", None)
        return document

    @model_validator(mode="after")
    def _check_identifiers(self) -> SectorFactorRecord:
        """Refuse a factor that cannot be read back out of the flattening.

        THE OTHER HALF OF THAT RULE IS DECIDED OVER THE LIST, not here, because
        it is about a PAIR of adjacent factors: a label may not end where the
        separator begins unless its factor is the last, nor begin where the
        separator ends unless its factor is the first, or two different product
        sectors collide under one flattened identifier
        (:func:`~certiqs_key.foundations.blocks.check_product_join`). A record has no
        neighbours, so :mod:`certiqs_key.domain.validation` decides it for the
        whole ``sector_factorisation`` by building the shared type -- one home
        for one rule, as with the product's other refusals.
        """
        labels = [label for label, _ in self.sectors]
        if len(set(labels)) != len(labels):
            raise ValueError(
                f"the factor scoped to party {self.party!r} repeats a sector "
                "identifier; a factor's identifiers enumerate a set"
            )
        for label in labels:
            if PRODUCT_LABEL_SEPARATOR in label:
                raise ValueError(
                    f"the sector identifier {label!r} contains the declared "
                    f"product separator {PRODUCT_LABEL_SEPARATOR!r}, so the "
                    "flattened identifier would not say which factor supplied "
                    "which part"
                )
        return self


class MessageRecord(StrictModel):
    """One message of the transcript protocol (``def:declaration`` (DX5)).

    The wire spelling of :class:`~certiqs_key.domain.announcements.Message`: the
    SENDER, that message's own finite alphabet, and the TOTAL table over the
    sender's readout and the earlier messages. NEW AT SCHEMA 0.4.0.

    ``table`` is a list of ``[readout, [earlier ...], value]`` triples and not a
    nested object, for the reason every other binary table in this format is a
    list of pairs: a JSON object key is a string, and the earlier-message half of
    the domain is a TUPLE whose components a consumer reads apart. Flattening it
    into one joined string would make the general format need a separator
    convention where (DX5) declares none.

    THE JOINT ALPHABET AND THE JOINT FUNCTION ARE NOT CARRIED. ``eq:transcript``
    derives both from these tables, and the ``transcript`` output row says so:
    "they are derived by ``eq:transcript``, as the sifting predicate and the
    key-live set are derived and are not keys today".
    """

    sender: PartyLabel
    alphabet: tuple[str, ...] = Field(min_length=1)
    table: tuple[tuple[str, tuple[str, ...], str], ...]


class FactorFamilyRecord(StrictModel):
    """One measured factor's declared family (``def:declaration`` (DX3)).

    The wire spelling of :class:`~certiqs_key.domain.families.FactorFamily`: that
    factor's party, its own ordered alphabet and one block list per letter against
    that factor's own sector map. NEW AT SCHEMA 0.4.0.

    NO ENTRY OF A PRODUCT IS CARRIED. ``F_v = (x)_f F^f_{v_f}`` is the RULE
    ``eq:productfamily``, a theorem about the factors' exact numbers
    (``reductions/thm:emitted-product`` (i)), and "no entry of a product is
    emitted, declared or rounded"; the product alphabet and the product sector map
    are derived from the factor list and this record's alphabet.
    """

    party: str = Field(min_length=1)
    alphabet: tuple[str, ...] = Field(min_length=1)
    members: dict[str, OperatorRef]


class Declaration(StrictModel):
    """The ``meat-core`` contract Section 2.1 inputs, by machine key.

    Its general-format keys are optional and each spells its degenerate value by
    absence; the module docstring lists them and says what 0.4.0 is.
    """

    alice_dim: Annotated[int, Field(ge=1)]
    #: The MARGINAL SLOT of contract Definition ``def:declaration``: ``tau_A``
    #: in ``S_=(A)`` (trusted-source mode) or the machine value ``null``,
    #: spelling the slot value ``none`` (untrusted-source mode). Its two values
    #: ARE the two source modes, which is why this format carries no separate
    #: mode key -- contract Section 2.5 calls a second one "a second source of
    #: truth" and forbids it.
    #:
    #: THE SLOT HAS TWO SPELLINGS SINCE 0.4.0, ONE PER FORMAT, and it is still ONE
    #: SLOT: this key in the degenerate case and :attr:`alice_marginal_blocks`
    #: where an ``A`` factor is declared. A declaration in trusted-source mode
    #: fills exactly one of the two, and BOTH ABSENT is the value ``nomarg``,
    #: which is the same rule read on the slot rather than on one key.
    alice_marginal: ArrayDescriptor | None = None
    #: ``(tau_A^(t))_t`` AS A BLOCK LIST ALONG ``T`` (``def:declaration`` (DX2);
    #: the ``alice_marginal.blocks`` output row), OPTIONAL, new at 0.4.0 and IN
    #: PLACE OF :attr:`alice_marginal`: "one block per Alice sector, each Hermitian
    #: and positive semidefinite, with ``sum_t tr tau_A^(t) = 1`` summed without
    #: rounding". A SINGULAR BLOCK IS ADMISSIBLE AND NO RANK IS CARRIED
    #: (``meat-core/lem:choi-factor`` (iv)).
    #:
    #: A SIBLING KEY AND NOT A WIDENED TYPE, which is a reading of the row this
    #: implementation takes and records: widening ``alice_marginal`` to a union
    #: would make every consumer that reads a dense ``tau_A`` today read a type it
    #: was not written for, at a key whose absence already carries a security
    #: meaning. A separate key cannot be mistaken for the dense one, and a consumer
    #: that has not learned the general format sees the slot as EMPTY -- which is
    #: untrusted-source mode, the conservative reading (``meat-core``
    #: ``rem:source-mode`` (a)).
    alice_marginal_blocks: OperatorRef | None = None
    #: The A-SRC attestation of contract Section 2.1. Optional; required
    #: whenever ``alice_marginal`` is present and ``alice_dim >= 2``, and
    #: VACUOUS at ``d_A = 1`` where Remark ``rem:source-mode`` (b5) says it
    #: "must not be demanded". Not machine-checkable; ``meat-core`` acts on its
    #: presence and never on its content.
    source_replacement_license: dict[str, JsonValue] | None = None
    #: The party partition ``P``. Absent spells the default partition.
    party_partition: PartyPartition | None = None
    sector_index_set: tuple[str, ...] = Field(min_length=1)
    sector_dims: dict[str, Annotated[int, Field(ge=1)]]
    #: THE THIRD COMPONENT OF THE ONE SECTOR MAP: the block
    #: kind that names what the identifiers of ``sector_index_set`` MEAN
    #: (``protocol-compiler`` 0.3.0 Definition ``def:declaration``). All three
    #: components are machine keys "so that a consumer comparing sector maps
    #: can compare all three and not two of them".
    #:
    #: NO VOCABULARY IS FIXED HERE: that contract never enumerates block kinds
    #: and no claim quantifies over them, so this format carries the declared
    #: string and decides nothing about what it MEANS. What it does decide
    #: is that it is THERE: the field is REQUIRED and has no default.
    #: ``sector_index_set`` and ``sector_dims`` have always been required, and the block
    #: kind is the third component of the same object -- a declaration carrying two of
    #: three is one whose consumer's structural check cannot be completed, and
    #: completing it here would be this format inventing what somebody else's
    #: identifiers mean. Absence is refused at the boundary, where the producer
    #: is still identifiable, rather than three stages downstream.
    sector_block_kind: str
    #: THE FACTORISED SECTOR MAP OF (DX1), OPTIONAL, A SLOT OF ``declaration``
    #: (spec/architecture.md 4.1).
    #:
    #: ABSENT IS THE SINGLE-FACTOR DEFAULT and carries the whole of today's
    #: meaning: one ``Q`` factor whose map is ``sector_index_set`` with
    #: ``sector_dims``, and one undecomposed ``A`` of dimension ``alice_dim``. So a
    #: 0.3.0 bundle is a factorised declaration already -- the degenerate one --
    #: and nothing infers a factorisation it was not given.
    #:
    #: PRESENT, IT MUST AGREE WITH THE KEYS IT REFINES, and that is decided in
    #: :mod:`certiqs_key.domain.validation` rather than here: the ``Q`` side
    #: flattens to ``sector_index_set``/``sector_dims`` in that order, the ``A``
    #: side's dimensions sum to ``alice_dim``, and the ``A`` factor's party is the
    #: ``party_of_alice_system`` of the declared party partition where one is
    #: present. Neither key is superseded -- this one says how the same map
    #: factorises, which is a refinement and not a second declaration of it.
    #:
    #: ``party_partition.party_of_sector_factors`` IS A DIFFERENT DATUM and is not
    #: cross-checked against this key. It labels the declared TENSOR factors of
    #: each ``H(Q_s)``, one list per sector, whereas a factor here is a factor of
    #: the sector MAP. The two share the word "factor" and nothing else.
    #:
    #: A PRESENT-BUT-EMPTY PRODUCT IS REFUSED BY THE SCHEMA, not defaulted to the
    #: single-factor reading: absence already spells that, so an empty list is a
    #: producer that meant to say something and said nothing.
    sector_factorisation: tuple[SectorFactorRecord, ...] | None = Field(
        default=None, min_length=1
    )
    #: WHICH OF (DX4)'s TWO SLOTS ALICE'S MEASUREMENT FILLS, OPTIONAL, new at
    #: 0.4.0. Absent spells ``povm``, which is today's format. ``ensemble`` is
    #: emitted in TRUSTED MODE ONLY, and then ``alice_ensemble`` stands in place of
    #: ``alice_povm``; an ensemble form beside a ``null`` marginal slot is what the
    #: consumer refuses with ``ensemble_form_in_untrusted_mode``, and this format
    #: transports the declared form rather than deciding it.
    alice_form: AliceForm | None = None
    #: ``{M_x}`` in the degenerate case: one matrix on ``A`` per ``x``, ``A``
    #: carrying no sector decomposition. EMPTY exactly where another of (DX4)'s
    #: spellings carries Alice's measurement -- :attr:`alice_povm_blocks` in POVM
    #: form with a declared ``A`` factor, :attr:`alice_ensemble` in ensemble form.
    #: The type does not move, so a consumer written against the degenerate case
    #: reads the key it always read.
    alice_povm: dict[str, ArrayDescriptor] = Field(default_factory=dict)
    #: ``{M_x}`` AS BLOCK LISTS ALONG ``T`` (``def:declaration`` (DX2)), OPTIONAL,
    #: new at 0.4.0 and IN PLACE OF :attr:`alice_povm`: ``M_x^(t)`` Hermitian and
    #: positive semidefinite per Alice sector with ``sum_x M_x^(t) = 1_{A_t}``. A
    #: SIBLING KEY for :attr:`alice_marginal_blocks`'s reason.
    alice_povm_blocks: dict[str, OperatorRef] | None = None
    #: ``{N_x}``, ONE BLOCK LIST PER SIGNAL LABEL ALONG ``T``, present exactly in
    #: ensemble form and IN PLACE OF ``alice_povm`` (``def:declaration`` (DX4),
    #: ``eq:ensembleform``). The declared blocks, passed through unchanged, with
    #: ``sum_x N_x^(t) = tau_A^(t)`` decided exactly per Alice sector by the
    #: consumer.
    #:
    #: THE DENOTED POVM IS NOT A KEY AND IS NOT CARRIED: ``eq:ensemblepovm`` is
    #: "defined, in general irrational and formed by no one", and that it is a POVM
    #: is ``thm:sifting-and-key`` (v).
    alice_ensemble: dict[str, OperatorRef] | None = None
    #: The measured family against ``Smap``, in the degenerate case. EMPTY exactly
    #: where :attr:`bob_povm_factors` carries it instead; the type does not move,
    #: for :attr:`alice_povm`'s reason.
    bob_povm: dict[str, OperatorRef] = Field(default_factory=dict)
    #: THE ORDERED PER-FACTOR FAMILY LIST OF (DX3), OPTIONAL, new at 0.4.0 and IN
    #: PLACE OF :attr:`bob_povm`: one :class:`FactorFamilyRecord` per measured
    #: factor, in the product order, PLUS THE PRODUCT RULE ``eq:productfamily``,
    #: which is a rule and not a datum. No entry of a product is carried.
    bob_povm_factors: tuple[FactorFamilyRecord, ...] | None = Field(
        default=None, min_length=1
    )
    announce_alice: dict[str, str]
    announce_bob: dict[str, str]
    #: THE TRANSCRIPT PROTOCOL OF (DX5), OPTIONAL, new at 0.4.0. Absent is the
    #: two-message case, whose emitted form STAYS the pair ``announce_alice`` /
    #: ``announce_bob`` (the ``transcript`` output row), so this key appears only
    #: where the accepted pair cannot express the public discussion -- ``L != 2``,
    #: or a message that reads an earlier one.
    transcript: tuple[MessageRecord, ...] | None = Field(default=None, min_length=1)
    #: ``phi`` in the accepted two-message format.  The nested object keeps the
    #: 0.3.0 bytes unchanged.  It is empty exactly when the transcript spelling
    #: below carries the same declaration for an arbitrary message count.
    accept_statistic: dict[str, dict[str, str]] = Field(default_factory=dict)
    #: ``phi`` on the DERIVED transcript alphabet ``prod_m C_m``.  A list of
    #: ``[[kappa_1, ..., kappa_L], chat]`` pairs because a JSON object key cannot
    #: carry the tuple without inventing a separator.  NEW AT SCHEMA 0.4.0 and
    #: present exactly with :attr:`transcript`.
    accept_statistic_general: tuple[tuple[tuple[str, ...], str], ...] | None = None
    key_map: dict[str, dict[str, int | None]]
    key_holder: KeyHolder
    constraint_list: tuple[Constraint, ...] = ()
    attack_set_license: dict[str, JsonValue] | None = None
    acceptance_set: AcceptanceSet
    rounds: Annotated[int, Field(ge=1)]

    #: THE 0.4.0 KEYS, in the model's order. The stamp rule and the serializer both
    #: read this tuple, so the two cannot drift: a key added to the model and not
    #: here would be written into a 0.3.0-stamped document.
    GENERAL_FORMAT_KEYS: ClassVar[tuple[str, ...]] = (
        "sector_factorisation",
        "alice_form",
        "alice_marginal_blocks",
        "alice_povm_blocks",
        "alice_ensemble",
        "bob_povm_factors",
        "transcript",
        "accept_statistic_general",
    )

    @model_validator(mode="after")
    def _exactly_one_spelling_per_slot(self) -> Declaration:
        """Refuse a declaration that fills a slot twice, or leaves one empty.

        THREE SLOTS HAVE TWO SPELLINGS EACH since 0.4.0 -- the marginal slot,
        Alice's measurement slot and the measured family -- and a declaration fills
        exactly ONE spelling of each, the degenerate one or the general one. A
        document carrying both would leave a consumer to decide which one the
        declaration is about, which is the "second source of truth" this format
        refuses everywhere.

        ALICE'S MEASUREMENT SLOT HAS THREE SPELLINGS AND STILL ONE VALUE: (DX4)'s
        POVM form in its dense and its block reading, and its ensemble form, which
        stands "in place of the POVM slots".

        THE MARGINAL SLOT'S EMPTY VALUE IS BOTH SPELLINGS ABSENT, which is
        ``nomarg`` and is the only thing that is.

        THIS IS A TYPING CONDITION AND NOT THE MODE CHECK. That an ensemble form
        beside an empty marginal slot is refused is D(iii)'s general-format clause,
        decided by the consumer at check V3 with
        ``ensemble_form_in_untrusted_mode``; this format transports the declared
        form and refuses only a document that says two things at once.
        """
        if self.alice_marginal is not None and self.alice_marginal_blocks is not None:
            raise ValueError(
                "payload.declaration fills the marginal slot twice, as a dense "
                "alice_marginal AND as the block list alice_marginal_blocks; the "
                "slot is ONE slot with one spelling per format (def:declaration "
                "(DX2)), and both absent is the value nomarg"
            )
        ensemble = self.alice_form is AliceForm.ENSEMBLE
        filled = [
            name
            for name, value in (
                ("alice_povm", self.alice_povm),
                ("alice_povm_blocks", self.alice_povm_blocks),
                ("alice_ensemble", self.alice_ensemble),
            )
            if value
        ]
        if len(filled) != 1:
            raise ValueError(
                f"payload.declaration fills {filled or 'no'} spelling(s) of "
                "Alice's measurement slot; (DX4) declares ONE slot and a "
                "declaration fills exactly one of alice_povm, alice_povm_blocks "
                "and alice_ensemble"
            )
        if ensemble != (filled == ["alice_ensemble"]):
            raise ValueError(
                f"payload.declaration declares alice_form "
                f"{(self.alice_form or AliceForm.POVM).value!r} and fills "
                f"{filled[0]!r}; the ensemble blocks N_x are the declared datum of "
                "the ensemble form and of no other (def:declaration (DX4), "
                "eq:ensembleform)"
            )
        if bool(self.bob_povm) == (self.bob_povm_factors is not None):
            twice = "twice" if self.bob_povm else "not at all"
            raise ValueError(
                f"payload.declaration declares the measured family {twice}: "
                "bob_povm is the degenerate spelling and bob_povm_factors the "
                "per-factor one of (DX3), and a declaration carries exactly one"
            )
        if self.transcript is None:
            if self.accept_statistic_general is not None:
                raise ValueError(
                    "payload.declaration carries accept_statistic_general without "
                    "a transcript; the general table is indexed by the derived "
                    "transcript alphabet"
                )
            if not self.accept_statistic:
                raise ValueError(
                    "payload.declaration carries no accept_statistic table for "
                    "the accepted two-message format"
                )
        elif self.accept_statistic or self.accept_statistic_general is None:
            raise ValueError(
                "payload.declaration with a transcript fills exactly "
                "accept_statistic_general and leaves the degenerate nested "
                "accept_statistic empty"
            )
        return self

    def general_format_keys(self) -> tuple[str, ...]:
        """Return the 0.4.0 keys this declaration USES, in the model's order.

        The stamp rule of the module docstring reads this: a declaration using none
        of them is a document schema 0.3.0 can express, and one using any of them
        needs :data:`SCHEMA_VERSION_FACTORISED`. It is computed rather than
        declared so that no producer can stamp a version its payload contradicts,
        in either direction.
        """
        used = [
            key
            for key in self.GENERAL_FORMAT_KEYS
            if getattr(self, key) is not None
        ]
        if any(entry.scope is not None for entry in self.constraint_list):
            used.append("constraint_list[*].scope")
        return tuple(used)

    @model_serializer(mode="wrap")
    def serialize(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        """Serialize the declaration, WRITING A 0.4.0 KEY ONLY WHEN IT IS USED.

        The other half of the stamp rule, moved here from the payload with the
        keys: a declaration that takes every degenerate value is written exactly as
        this format wrote it before 0.4.0 existed -- same keys, same order, same
        bytes -- because an unused key is not emitted as ``null``.

        THE THREE DEGENERATE SPELLINGS ARE DROPPED WHERE THEY ARE EMPTY, for the
        same reason and not as an extra rule: an empty ``alice_povm`` or
        ``bob_povm`` in the general format is the absence of that spelling, and a
        document of TODAY'S shape has both non-empty and so keeps them.

        THE PRE-0.4.0 OPTIONAL KEYS ARE NOT TOUCHED BY THIS: ``alice_marginal``,
        ``source_replacement_license``, ``party_partition`` and
        ``attack_set_license`` are each emitted as ``null`` where they are absent,
        as they always were, because omitting one now would move the bytes this
        rule exists to keep still.
        """
        document: dict[str, Any] = handler(self)
        for key in self.GENERAL_FORMAT_KEYS:
            if getattr(self, key) is None:
                document.pop(key, None)
        for degenerate in ("alice_povm", "bob_povm"):
            if not getattr(self, degenerate):
                document.pop(degenerate, None)
        return document


class Parameters(StrictModel):
    """The ``meat-core`` contract 0.4.0 Section 2.4 parameters, by machine key.

    The bounds are the contract's declared domains. ``alpha`` is open on both
    ends: ``(1, 2)`` is the intersection of the accumulation and
    leftover-hashing imports, and an endpoint is outside it.
    """

    alpha: Annotated[float, Field(gt=1.0, lt=2.0)]
    eps_pa: Annotated[float, Field(gt=0.0, le=1.0)]
    eps_ev: Annotated[float, Field(gt=0.0, le=1.0)]
    lambda_ec: Annotated[int, Field(ge=0)]


class Payload(StrictModel):
    """The mathematical content of an operator bundle."""

    alphabets: Alphabets
    declaration: Declaration
    parameters: Parameters
    #: The chain of typed reduction links, OPTIONAL. Absent means no chain was
    #: recorded. It sits here rather than among :class:`Declaration`'s
    #: keys because that model is the ``meat-core`` Section 2.1 INPUT table
    #: and this is
    #: a ``protocol-compiler`` OUTPUT key -- see the module docstring, which also
    #: records why spec/architecture.md 4.2 does not decide the placement.
    #: Carried, never interpreted: this format checks its shape and decides
    #: nothing about whether the reduction is sound.
    reduction_chain: ReductionChain | FactorReductionChain | None = None

    #: THE PAYLOAD CARRIES NO ``sector_factorisation``. ``def:declaration``
    #: (DX1) gives it a home, so it is a declaration key
    #: (:attr:`Declaration.sector_factorisation`) and a document carrying it
    #: here is refused as ``extra_forbidden``.


def schema_version_for(payload: Payload) -> str:
    """Return the LOWEST schema version that can express ``payload``.

    The stamp rule of the module docstring, in one place: a payload whose
    DECLARATION uses a key 0.4.0 added needs :data:`SCHEMA_VERSION_FACTORISED`,
    and every other payload needs :data:`SCHEMA_VERSION`. A producer calls this
    instead of choosing, and
    :meth:`OperatorBundleManifest._check_the_stamp_expresses_the_payload` refuses a
    manifest stamped below what its payload needs -- so a bundle whose version
    says 0.3.0 is a bundle a 0.3.0 reader can read, and that is a fact about the
    file rather than a promise about the producer.

    IT READS THE DECLARATION AND NOT THE PAYLOAD, because every 0.4.0 key is
    inside ``declaration``;
    :meth:`Declaration.general_format_keys` is the list, and it is computed from
    the document rather than declared beside it.
    """
    if payload.declaration.general_format_keys():
        return SCHEMA_VERSION_FACTORISED
    return SCHEMA_VERSION


class OperatorBundleManifest(StrictModel):
    """``manifest.json``: spec/architecture.md 4.1's envelope, around a payload."""

    kind: Literal["operator-bundle"]
    #: The versions a reader accepts. ``0.1.0`` and ``0.2.0`` are retired
    #: (:data:`RETIRED_SCHEMA_VERSIONS`) and named in their own refusal; see
    #: the module docstring for the versions and spec/architecture.md 2.9 for
    #: the decision, and :func:`schema_version_for` for which of the two live
    #: versions a given payload is stamped.
    schema_version: Literal["0.3.0", "0.4.0"]
    mathematical_spec_version: str
    created_by: str = Field(min_length=1)
    implementation_version: str = Field(min_length=1)
    assumptions: dict[str, JsonValue] = Field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    payload: Payload

    @field_validator("schema_version", mode="before")
    @classmethod
    def _name_a_retired_version(cls, value: object) -> object:
        """Say which version a retired stamp is, rather than "unknown version".

        ``mode="before"`` is load-bearing: the ``Literal`` annotation would
        otherwise refuse the document first, with a message that names only
        what is accepted and not what was found. A bundle stamped 0.1.0 or
        0.2.0 was well-formed when it was written and is not malformed now, so
        the refusal says so and says what to do about it.

        THE TYPED REFUSAL IS AT THE READER, NOT HERE. Pydantic wraps whatever
        this raises into a ``ValidationError``, which carries a string and not
        a class, so a caller could not branch on it. The machine-readable
        refusal -- :class:`~certiqs_key.domain._base.RetiredSchemaVersionError`,
        with :data:`RETIRED_SCHEMA_VERSION_REASON` and the declared version on
        it -- is raised by :func:`~certiqs_key.domain.bundle.parse_manifest`
        before this model ever sees the document. This validator is what makes
        a direct ``model_validate`` say the same thing in prose.
        """
        if isinstance(value, str) and value in RETIRED_SCHEMA_VERSIONS:
            raise ValueError(
                f"schema version {value!r} is retired: this reader accepts "
                f"{list(SUPPORTED_SCHEMA_VERSIONS)} and nothing else "
                "(spec/architecture.md 2.9). A retired version can express "
                "a full-space "
                "operator payload, which is the whole reason read support was "
                "dropped; a bundle is not converted, because re-blocking an "
                "operator would require inventing a sector map, which is a "
                "mathematical claim and not a format conversion. Regenerate "
                "the bundle from its instance"
            )
        return value

    @model_validator(mode="after")
    def _check_the_stamp_expresses_the_payload(self) -> OperatorBundleManifest:
        """Refuse a stamp that is not the one this payload needs.

        BOTH DIRECTIONS ARE REFUSED, because the stamp is the LOWEST version
        that can express the document and that makes it a fact about the file:
        a payload carrying a 0.4.0 key stamped 0.3.0 is a document that lies
        about itself, which is the failure a version string exists to prevent,
        and a payload of today's shape stamped 0.4.0 tells a 0.3.0 reader it
        cannot read a document it can -- and would move the bytes of a bundle
        that says exactly what it said before. :func:`schema_version_for` is
        therefore the only authority on the stamp, and the refusal names the
        payload key that decides it rather than the version alone.
        """
        required = schema_version_for(self.payload)
        if self.schema_version != required:
            used = self.payload.declaration.general_format_keys()
            presence = (
                f"uses the 0.4.0 key(s) {list(used)}"
                if used
                else "uses no 0.4.0 key"
            )
            raise ValueError(
                f"schema_version {self.schema_version!r} is not the version "
                f"this payload is stamped with, {required!r}: the stamp is the "
                "lowest version that can express the document, and "
                f"payload.declaration {presence}, which is what decides it. "
                "Stamp schema_version_for(payload)"
            )
        return self

    @field_validator("mathematical_spec_version")
    @classmethod
    def _check_spec_version(cls, value: str) -> str:
        """Reject a spec version that is not an accepted contract version."""
        if not SPEC_VERSION_PATTERN.fullmatch(value):
            raise ValueError(
                f"{value!r} is not '<module-id>@<contract_version>' with a "
                "released contract version; the meat-core contract Sec. 2.4 "
                "forbids an artifact from claiming a draft version"
            )
        return value
