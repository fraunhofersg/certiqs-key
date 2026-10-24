"""The constraint wire records: the relation, the right-hand-side tag, the entry.

WHAT THIS FILE HOLDS. Four frozen types, here so that no module imports the
protocol compiler: :class:`Relation`, :class:`RhsTag`, :class:`ConstraintEntry` and
:class:`AttackSetLicense`.

THEY ARE THE CONSUMER'S SPELLING, AND THE REDUCTIONS MODULE KEEPS ITS OWN.
:class:`Relation` here spells the three ordering symbols as WORDS (``le``,
``eq``, ``ge``); :class:`certiqs_key.reductions.reasons.Relation` spells the
same three as OPERATORS (``<=``, ``=``, ``>=``), which is the spelling the
reductions claims are stated in. The map between them is a rename and not a
reinterpretation: the two spellings denote THE SAME THREE RELATIONS at the two
levels. Likewise
:class:`ConstraintEntry` here carries a :class:`BlockOperator` and a
right-hand side, while the reductions module's own entry carries its exact
matrix, its certificate case and its channel witness; the docking converts one
into the other, once, in one direction.

NOTHING HERE DECIDES ANYTHING. These are records: they hold declared data and
the one property :attr:`ConstraintEntry.tag`, which READS the tag off the type
of the datum rather than measuring anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from certiqs_key.foundations.blocks import BlockOperator, Label
from certiqs_key.foundations.exact import Matrix

__all__ = [
    "AttackSetLicense",
    "ConstraintEntry",
    "Relation",
    "RhsTag",
]


class Relation(StrEnum):
    """One of the three ordering symbols a constraint entry may carry.

    Read in the Loewner order when the marginal slot is filled and in the real
    order when it is not; the two relation sets collapse to one set of three
    symbols in the wire record.
    """

    LE = "le"
    EQ = "eq"
    GE = "ge"


class RhsTag(StrEnum):
    """The DECLARED FORMS a constraint entry's right-hand side takes.

    "A ``homogeneous`` entry declares a real scalar ``c_k``, a ``general``
    entry declares a Hermitian ``Theta_k`` on ``A``. In untrusted-source mode
    ONLY THE SCALAR FORM EXISTS." The tag IS that type and is read off it --
    FOR THE TWO UNTAGGED FORMS, which is the scope ``def:homog``'s closing
    paragraph gives that rule.

    ``general`` IS ADMISSIBLE AND IS NEVER LICENSED: "every structural claim is
    proved for it -- BUT IT IS NOT LICENSED, so a list containing one CARRIES
    NO KEY-LENGTH CLAIM, WHICH IS THE FAIL-CLOSED DIRECTION."

    ``PARTY_LOCAL`` IS THE THIRD FORM, NEW IN BATCH C3 (``def:homog``, the
    party-local form; ``def:declaration`` (DX6)), and it is the one member whose
    presence is NOT decidable from the datum: it carries a real scalar exactly
    as ``homogeneous`` does, so "the entry is ``party_local`` exactly when it
    ARRIVES carrying that tag value, and check V6 then requires the slot to hold
    a real scalar and the scope to name a measured factor". NOTHING IS INFERRED:
    an entry arriving without the tag is never read party-locally, whatever
    supplier emitted it.
    """

    HOMOGENEOUS = "homogeneous"
    GENERAL = "general"
    PARTY_LOCAL = "party_local"


@dataclass(frozen=True)
class ConstraintEntry:
    """One entry ``(O^_k, bowtie_k, rhs_k)`` of a transported constraint list.

    ``operator`` is a target-space operator and is therefore A BLOCK LIST
    against the sector map; its Hermiticity is decided per block by the
    consumer. ``rhs`` is of one of exactly two ADMITTED FORMS and the form IS
    the tag: a real scalar spells ``homogeneous``; a dense matrix on
    undecomposed ``A`` or a block list on the Alice-sector map spells
    ``general``.

    ``arriving_tag`` IS NOT THE TAG. "Where an ARRIVING entry -- in the
    declared constraint part or transported by a link -- carries an explicit
    tag field, the consumer compares that field with the type of the datum it
    names and A DISAGREEMENT IS A REFUSAL"; on a candidate declaration the
    field has no subject, so it defaults to ``None``, and "an entry carrying no
    tag field is NOT REFUSED: the tag is the type and is read off it".
    """

    operator: BlockOperator
    relation: Relation
    rhs: Matrix | BlockOperator | Fraction
    #: The tag an ARRIVING entry declared, where it declared one. Never the
    #: emitted ``constraint_rhs_tag``, which is :attr:`tag` -- EXCEPT for
    #: ``party_local``, the one form whose tag the datum does not fix.
    arriving_tag: RhsTag | None = None
    #: THE ENTRY'S SCOPE ``f_k``, NEW IN BATCH C3 (``def:declaration`` (DX6);
    #: ``def:spec`` (e')): the label of the ONE measured factor its operator is a
    #: block list against. ``None`` is the accepted format's case, where there is
    #: one measured factor and "the scope is that factor" -- so absence is the
    #: degenerate value and never an unknown.
    #:
    #: THE LIFTED OPERATOR IS NOT A FIELD AND IS FORMED BY NO ONE: (DX6)'s
    #: ``1 (x) O_k (x) 1`` "is never formed as a datum", and a consumer contracts
    #: a joint block against ``O_k``'s block on its own tensor factor instead.
    scope: Label | None = None

    @property
    def rhs_is_scalar(self) -> bool:
        """Whether the right-hand side is presented as a real scalar."""
        return isinstance(self.rhs, Fraction)

    @property
    def is_party_local(self) -> bool:
        """Whether the entry ARRIVED tagged ``party_local`` (``def:homog``).

        A PRESENCE TEST ON THE ARRIVING FIELD AND NOT A PROPERTY OF THE DATUM.
        "The type of the datum does not separate the two: the entry is
        ``party_local`` exactly when it arrives carrying that tag value." That
        the slot then holds a real scalar is check V6's decision and not this
        property's; reading the type here would either infer the tag or refuse
        the entry before the check that names the refusal has run.
        """
        return self.arriving_tag is RhsTag.PARTY_LOCAL

    @property
    def tag(self) -> RhsTag | None:
        """Return the emitted ``constraint_rhs_tag``, READ OFF THE DATUM.

        ``None`` where the slot holds neither admitted object, which the
        consumer "refuses BY TYPE AND NOT MEASURED". Deciding Hermiticity of a
        matrix right-hand side is the consumer's own and is decided there, not
        here: a non-Hermitian matrix is still of ``general`` TYPE, and
        "deciding Hermiticity does not make the tag a measured property".

        THE ONE EXCEPTION IS ``party_local`` AND IT IS THE CLAIM'S OWN. Its
        right-hand-side slot holds a real scalar, "as a ``homogeneous`` entry's
        does, so the type of the datum does not separate the two"; an entry of
        ``eq:declaration`` "DOES carry a tag field where it is tagged
        ``party_local``, which is the one place the accepted sentence's 'no tag
        field independent of that type' does not reach". So the arriving field
        decides this member and nothing else does -- and only beside a real
        scalar: a ``party_local`` tag beside a matrix is left reading
        ``general``, which is the disagreement V6 refuses rather than a tag this
        record invents.
        """
        rhs: object = self.rhs
        if isinstance(rhs, Fraction):
            return (
                RhsTag.PARTY_LOCAL if self.is_party_local else RhsTag.HOMOGENEOUS
            )
        if isinstance(rhs, (tuple, BlockOperator)):
            return RhsTag.GENERAL
        return None


@dataclass(frozen=True)
class AttackSetLicense:
    """The ``attack_set_license`` pass-through record.

    Carried, never read, never verified and never synthesized. A consumer
    passing its gate on this record "records that an attestation was supplied.
    It asserts nothing about attack-set inclusion." What DOES assert the
    inclusion is the reductions module's own licence theorem, whose hypothesis
    and discharging assumption are named inside the statement string so that a
    reader can follow the assertion back to its theorem.
    """

    supplier: str
    statement: str
