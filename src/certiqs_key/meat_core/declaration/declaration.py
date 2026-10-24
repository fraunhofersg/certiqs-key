"""The protocol declaration ``D`` of contract Definition ``def:declaration``.

This module holds the declaration as *data* and nothing else: the generated
maps of ``thm:protocol-channel`` and ``lem:branch-maps`` live in
:mod:`certiqs_key.meat_core.objective.branch`, the well-formedness checks of
``def:admissible-declaration`` in :mod:`certiqs_key.meat_core.declaration.validation`,
and the translation from a serialized operator bundle in
:mod:`certiqs_key.meat_core.declaration.bundle`.

Index conventions, fixed by contract.tex the conventions and transcribed in
``interface.yaml``:

* a state block ``omega_s`` lives on ``A (x) Q_s`` with the **A factor first**
  (``subsystem_order: A, Q, Etilde``), so ``M_x (x) F_v^{(s)}`` is the operator
  that reads it;
* a Choi block ``J_s`` lives on ``A_0 (x) Q_s`` with the **input factor A_0
  first** (``choi_ordering``);
* every alphabet is an ordered tuple of stable IDs and that order is what turns
  an alphabet into array positions.

The purifying register ``Etilde`` has no representation here, and that is a
statement of the contract rather than an omission: by Lemma
``lem:purifier-indep`` the rates do not depend on it, and ``h_low`` is a
function of the ``A Q``-marginal alone (C8, and the ``purifier_dim`` convention
of the conventions).

THE SOURCE MODE IS DERIVED, AND HAS NO FIELD
============================================
the conventions: "``source_model``: ``trusted`` or ``untrusted``,
*derived*, never separately declared -- it is ``trusted`` exactly when
``alice_marginal`` is present (Remark ``rem:modes-da1``). A second key
carrying the mode would be a second source of truth and is forbidden."

:attr:`ProtocolDeclaration.source_mode` is therefore a read-only property over
the marginal slot and not a stored field: there is no attribute to set
inconsistently, and no constructor argument that could disagree with the slot.
Fourteen statements of the contract branch on that one bit
(Definitions ``def:declaration``, ``def:homog``, ``def:roundmodel``,
``def:hqkd-list``, ``def:feasible``, Lemma ``lem:range``, Theorems
``thm:accumulated-entropy``, ``thm:removal``, ``thm:choi``,
``thm:constrained-accumulation``, ``thm:keylength``,
Corollary ``cor:full-gradient``, and lem:product-marginal and A-SRC), so a second
settable mode could put all fourteen into a state the contract has no statement
about.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from certiqs_key.domain.manifest import ConstraintRelation, KeyHolder, PartyLabel
from certiqs_key.meat_core.objective.linalg import Matrix, support_spectrum

#: Sifting failure: the value of the raw-key map ``r`` outside ``Z``. The
#: contract writes it ``perp``; the bundle format spells it ``None``.
PERP: None = None

#: The value of the MARGINAL SLOT in untrusted-source mode. contract Definition
#: ``def:declaration`` types the slot as ``S_=(A) u {none}``; the interface's `inputs`
#: table gives
#: ``none`` the machine value ``null``, and the Notation section records that it
#: is "deliberately not perp, which is the sifting-failure key value, and not 0,
#: which is inadmissible". Python spells all three ``None``/``0``; the constants
#: are kept apart here so that the distinction is visible at every use site.
NOMARG: None = None


class SourceMode(StrEnum):
    """The two source modes of contract Remark ``rem:modes-da1``.

    DERIVED from the marginal slot and never stored: see the module docstring.
    """

    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


@dataclass(frozen=True)
class PartyPartition:
    """The party partition ``P`` of contract Definition ``def:declaration``.

    Part (a) -- ``readout_alice`` and ``readout_bob``, the total maps
    ``pi_A, pi_B : X x V -> O_A, O_B`` -- is the only part any derivation
    consumes, and it is consumed only through def:admissible-declaration (viii): each
    party announces a function of its own readout, and the declared key holder
    computes the raw key from ITS OWN readout and the announcements
    (Eq. ``eq:partycomp``).

    Part (b) -- ``party_of_alice_system`` and ``party_of_sector_factors`` -- is
    system metadata carrying a ``protocol-compiler`` obligation that this module
    never verifies and no derivation consumes; one premise reads it,
    ``ass:lab`` (A-LAB), which takes its labels as naming the parties'
    laboratories, so a run attests the obligation there (``def:declaration``).

    :func:`default_party_partition` materializes the DEFAULT partition
    ``pi_A(x, v) = x``, ``pi_B(x, v) = v``, which ``def:declaration`` says
    "reproduces versions 0.2.x of this contract verbatim".
    """

    readout_alice: Mapping[tuple[str, str], str]
    readout_bob: Mapping[tuple[str, str], str]
    alphabet_alice: tuple[str, ...]
    alphabet_bob: tuple[str, ...]
    party_of_alice_system: PartyLabel
    party_of_sector_factors: Mapping[str, tuple[PartyLabel, ...]]
    #: Whether this record was materialized from the absent-partition default.
    is_default: bool = False


class RhsTag(StrEnum):
    """The DECLARED FORM of a constraint entry's right-hand side.

    ``def:homog``: a TYPE, not a MEASUREMENT. The
    two tags are the two forms a declaration may write, and which one an entry
    carries is DECLARED DATA: part (i) of the two-part gate is A TYPE CHECK ON
    THE DECLARED TAG AND COMPARES NO NUMBERS. It is decided at NO WINDOW, and
    the scalar declaration replaces the operator declaration precisely so that
    it could not be.

    WHY THE OPERATOR FORM WOULD BE UNSAFE, in the contract's own words: under
    the operator form "a
    declaration carrying an operator ``Theta_k`` merely NEAR ``c_k tau_A`` had
    to be admitted or refused by a numerical test, and admitting one was unsafe
    in a way no relaxation of this contract covers: the transport of Lemma
    ``lem:range`` (i) and Eq. ``eq:transport`` deliver exactly ``c_k tau_A`` on
    the right-hand side, while Eq. ``eq:feas-modes`` would impose the declared
    ``Theta_k``, and THE TWO FEASIBLE SETS ARE THEN NEITHER NESTED NOR
    RELATED".
    """

    #: A REAL SCALAR ``c_k``, from which the right-hand side ``Theta_k`` is
    #: CONSTRUCTED -- ``c_k tau_A`` in trusted-source mode, ``c_k`` itself in
    #: untrusted-source mode. THE LICENSED FORM IN BOTH MODES.
    HOMOGENEOUS = "homogeneous"

    #: A HERMITIAN ``Theta_k`` on ``A``. Admissible input in trusted-source
    #: mode -- "every structural and numerical claim of this contract is proved
    #: for it" -- and NEVER LICENSED, so a list containing one carries no
    #: key-length claim. That is the fail-closed direction. It does not exist
    #: in untrusted-source mode, where the right-hand side is a real number.
    GENERAL = "general"


@dataclass(frozen=True)
class ConstraintEntry:
    """One entry ``(O_k, bowtie_k, Theta_k)`` of the declared list ``L``.

    ``operator_blocks`` is ``O_k`` in its sector-block form, ``O_k^{(s)}`` on
    ``Q_s`` -- the only form an operator takes (spec/architecture.md 2.9), so
    sector-block-diagonality holds by construction.

    ``rhs_tag`` IS DECLARED DATA AND CARRIES NO DEFAULT. The `inputs` table
    makes the right-hand side arrive "IN ONE OF TWO TAGGED FORMS", and a tag
    this module supplied would be a code default deciding a security-relevant
    predicate -- the two-part gate's part (i) -- on nobody's authority. What
    each tag then requires of ``bound`` is checked by
    :mod:`certiqs_key.meat_core.declaration.validation` against the DECLARED
    SOURCE MODE:

    * ``homogeneous`` -- ``bound`` is the real scalar ``c_k``. In TRUSTED mode
      the right-hand side ``Theta_k = c_k tau_A`` is CONSTRUCTED from it by
      :meth:`right_hand_side`, so the transported bound and the imposed bound
      are THE SAME EXPRESSION in the same ``c_k`` and the same ``tau_A`` and
      agree BY CONSTRUCTION, with nothing compared and no window to compare at.
      In
      UNTRUSTED mode the entry reads ``tr[(1_A x O_k) omega] bowtie_k c_k``, a
      comparison of real numbers (Definition ``def:homog`` (b)).
    * ``general`` -- ``bound`` is a Hermitian ``Theta_k`` on ``A``, and the
      declaration must be in trusted-source mode. Remark ``rem:homog`` (a)
      exhibits a licensed attack set -- ``O = 1_Q``, ``succeq``, ``c = 1``,
      every CPTP map admissible -- for which reading an untrusted-mode entry as
      the operator ``c_k 1_A`` forces ``omega_A >= 1_A`` and empties the
      feasible set at ``d_A >= 2``, so the two spellings are not two spellings
      of one restriction.
    """

    operator_blocks: Mapping[str, Matrix]
    relation: ConstraintRelation
    #: The DECLARED right-hand side: the real scalar ``c_k`` under the
    #: ``homogeneous`` tag, the Hermitian ``Theta_k`` under ``general``.
    bound: Matrix | float
    #: Which of the two declared forms this entry is in. REQUIRED.
    rhs_tag: RhsTag

    @property
    def is_homogeneous(self) -> bool:
        """Return whether the entry declares the licensed scalar form."""
        return self.rhs_tag is RhsTag.HOMOGENEOUS

    @property
    def is_scalar(self) -> bool:
        """Return whether ``bound`` is carried as a real scalar."""
        return not isinstance(self.bound, np.ndarray)

    @property
    def scalar_bound(self) -> float:
        """Return ``c_k``; raise for an entry that declares an operator."""
        if isinstance(self.bound, np.ndarray):
            raise TypeError(
                "this entry is tagged `general` and carries an operator "
                "Theta_k; there is no scalar c_k to read"
            )
        return float(self.bound)

    @property
    def operator_bound(self) -> Matrix:
        """Return the DECLARED operator ``Theta_k``; raise for a scalar entry.

        THE DECLARED ONE, NOT THE CONSTRUCTED ONE. A ``homogeneous`` entry has
        no declared operator -- its right-hand side is BUILT from ``c_k`` by
        :meth:`right_hand_side` -- and returning ``c_k 1_A`` here would be
        exactly the unlicensed reading of Remark ``rem:homog`` (a).
        """
        if not isinstance(self.bound, np.ndarray):
            raise TypeError(
                "this entry is tagged `homogeneous` and carries the scalar "
                "c_k; there is no declared operator Theta_k to read, and "
                "forming c_k 1_A is exactly the unlicensed reading of Remark "
                "rem:homog (a). Use right_hand_side(tau_A), which CONSTRUCTS "
                "c_k tau_A"
            )
        return np.asarray(self.bound, dtype=np.complex128)

    def right_hand_side(self, alice_marginal: Matrix | None) -> Matrix | float:
        """Return the right-hand side this entry imposes, CONSTRUCTED not read.

        Definition ``def:homog`` as amended: for a ``homogeneous`` entry in
        TRUSTED-source mode the right-hand side is ``c_k tau_A``, formed here
        from the declared scalar and the declared marginal, so that
        Eq. ``eq:transport`` and Eq. ``eq:feas-modes`` "carry the same
        expression BY CONSTRUCTION". In untrusted-source mode there is no
        ``tau_A`` and the right-hand side is the real number ``c_k``. A
        ``general`` entry imposes the operator it declares.
        """
        if self.rhs_tag is RhsTag.GENERAL:
            return self.operator_bound
        if alice_marginal is None:
            return self.scalar_bound
        return self.scalar_bound * np.asarray(alice_marginal, dtype=np.complex128)


@dataclass(frozen=True)
class PolytopeData:
    """The data of the ``polytope`` geometry, carried as declared.

    The tag and its data are read AS DATA from the accepted
    ``statistics`` taxonomy, Definition ``def:taxonomy``: an
    integer row count ``m_row >= 0``, a matrix ``B`` with one column per element
    of ``Chat`` and one row per declared inequality, and a vector ``b``, denoting

        ``Gamma = {q in simplex(Chat) : B q <= b}`` .

    ``meat-core`` defines no tag vocabulary of its own -- the `inputs` table
    types ``acceptance_set`` as a closed convex subset of the simplex and
    enumerates no geometries -- and this is the SAME set as instantiation (b) of
    contract Remark ``rem:acc-side``, which is the one this module can certify.

    ``box_bounds`` is the optional CANONICAL BOX SUB-FORM: the pair
    ``(q^-, q^+)`` whose one-hot rows ``B`` already spells out. It is a
    sub-form of ``polytope`` and not a third tag, so a consumer that ignores it
    still reads a well-formed polytope; this module keeps it only to CHECK it
    against the rows, because declared data that contradicts itself is a defect
    that must be refused before anything is computed from it.

    The row order is the declaration's own and is never re-sorted here: ``rhs``
    is read positionally against ``rows``, and a dual multiplier is reported in
    that same order.
    """

    #: ``|Chat|`` -- the number of columns every row must have.
    columns: int
    #: ``B``, one tuple per row, each of length :attr:`columns`.
    rows: tuple[tuple[float, ...], ...]
    #: ``b``, one entry per row of :attr:`rows`.
    rhs: tuple[float, ...]
    #: ``(q^-, q^+)`` when the declaration claims canonical box form.
    box_bounds: tuple[tuple[float, ...], tuple[float, ...]] | None = None

    @property
    def m_row(self) -> int:
        """Return ``m_row``, the declared row count."""
        return len(self.rows)

    def restricted(self, indices: Sequence[int]) -> PolytopeData:
        """Return this polytope with its columns cut down to ``indices``.

        Remark ``rem:acc-side`` (b): every ``q`` in ``AcceptSet`` is
        supported in ``Chat_acc`` (Eq. ``eq:chacc-def``), so coordinates
        outside ``Chat_acc`` carry no mass and may be omitted from ``B``.
        Dropping those columns leaves the same set -- a point of the
        restricted system extends by zeros to a point of the declared one and
        back -- so the minimum is the same and the witness has the same rows.

        ``box_bounds`` is dropped rather than restricted: the restricted rows
        are not the canonical box rows of the restricted alphabet unless
        the dropped coordinates were exactly the ones with ``q^+ = 0``, and
        claiming a sub-form that may not hold is the defect the
        well-formedness check exists to catch.
        """
        return PolytopeData(
            columns=len(indices),
            rows=tuple(tuple(row[index] for index in indices) for row in self.rows),
            rhs=self.rhs,
        )


@dataclass(frozen=True)
class AcceptanceSet:
    """The declared acceptance set of def:admissible-acceptance-set.

    def:admissible-acceptance-set asks for a closed convex subset of the probability
    simplex on ``Chat``, and says nothing about how such a set is written down. The
    *representation* is owned by ``statistics``, whose accepted
    taxonomy fixes exactly two tags in its Definition ``def:taxonomy`` --
    ``singleton`` and ``polytope`` -- in deliberate one-to-one correspondence
    with the two instantiations contract Remark ``rem:acc-side`` certifies.
    Both are read here; every other tag is refused rather than guessed
    (:class:`~certiqs_key.meat_core.errors.UnsupportedDeclarationError`).

    Exactly one of :attr:`frequencies` and :attr:`polytope` carries the data,
    selected by :attr:`geometry`. The residual gap between
    def:admissible-acceptance-set's "any closed convex subset" and these two
    representations is disclosed where a third tag is refused, in the refusal's own
    message (:func:`~certiqs_key.meat_core.acceptance.geometry.acceptance_verdict`).
    """

    geometry: str
    #: ``q*`` of the ``singleton`` geometry; empty for a ``polytope``.
    frequencies: tuple[float, ...] = ()
    #: ``(m_row, B, b)`` of the ``polytope`` geometry; ``None`` otherwise.
    polytope: PolytopeData | None = None

    def as_vector(self) -> np.ndarray:
        """Return the single accepted frequency vector as an array."""
        return np.asarray(self.frequencies, dtype=np.float64)


@dataclass(frozen=True)
class KeyLengthParameters:
    """The finite-size parameters of the `parameters` table."""

    alpha: float
    eps_pa: float
    eps_ev: float
    lambda_ec: int


@dataclass(frozen=True)
class ProtocolDeclaration:
    """The tuple ``D`` of contract Definition ``def:declaration``.

    Construction performs no validation: a declaration is checked by
    :func:`certiqs_key.meat_core.declaration.validation.validate_declaration`,
    which every declaration parsed from an operator bundle runs
    (:func:`certiqs_key.meat_core.declaration.bundle.declaration_from_bundle`,
    spec/architecture.md 3.6). A declaration built in memory and handed
    directly to ``solve`` or ``solve_declaration`` does NOT run it, and the
    caller owns that check.
    """

    alice_dim: int
    #: The MARGINAL SLOT: ``tau_A`` in ``S_=(A)`` (trusted-source mode) or
    #: :data:`NOMARG` (untrusted-source mode). Read the mode off
    #: :attr:`source_mode`; there is no separate mode field.
    alice_marginal: Matrix | None
    sector_index_set: tuple[str, ...]
    sector_dims: Mapping[str, int]
    #: THE BLOCK KIND OF THE DECLARED SECTOR MAP, and a REQUIRED slot.
    #:
    #: The `inputs` table states of every operator-valued row that
    #: "a
    #: declared operator on Q arrives as the LIST OF ITS SECTOR BLOCKS together
    #: with the declared sector map -- THE BLOCK KIND, the block identifiers
    #: and their ordering -- and NEVER as a d_Q x d_Q array", and that "the
    #: structural check a consumer performs is the comparison of ITS OWN SECTOR
    #: MAP with the producer's". The kind is therefore a component of the datum
    #: this module compares, not a presentation detail of the wire, and the
    #: sector-map comparison is that comparison.
    #:
    #: ``None`` SPELLS "THE PRODUCER DECLARED NO KIND" AND IS REFUSED, with
    #: ``sector_map_disagreement``. It is admitted by the TYPE only so that the
    #: refusal is this module's, raised by the rule that owns condition (T),
    #: rather than a ``TypeError`` from Python -- and refused by the RULE
    #: because a map without a kind is not a map this module can compare its
    #: own against, and reading a default would be deciding a structural
    #: predicate on nobody's authority.
    #:
    #: WHICH KIND IS RIGHT IS NOT DECIDED HERE. meat-core's contract names the
    #: kind as a component of the map to be COMPARED and does not say which
    #: value its own map carries; the shared operator-bundle format is where a
    #: kind is constrained (spec/architecture.md 2.9), and this module
    #: compares producer against consumer and nothing else.

    alice_povm: Mapping[str, Matrix]
    bob_povm: Mapping[str, Mapping[str, Matrix]]
    announce_alice: Mapping[str, str]
    announce_bob: Mapping[str, str]
    accept_statistic: Mapping[tuple[str, str], str]
    key_map: Mapping[tuple[str, str], int | None]
    key_holder: KeyHolder
    acceptance_values: tuple[str, ...]
    key_value_count: int
    acceptance_set: AcceptanceSet
    rounds: int
    parameters: KeyLengthParameters
    #: THE BLOCK KIND OF THE DECLARED SECTOR MAP.
    #:
    #: The `inputs` table states of every operator-valued row that
    #: "a
    #: declared operator on Q arrives as the LIST OF ITS SECTOR BLOCKS together
    #: with the declared sector map -- THE BLOCK KIND, the block identifiers
    #: and their ordering -- and NEVER as a d_Q x d_Q array", and that "the
    #: structural check A CONSUMER performs is the comparison of ITS OWN SECTOR
    #: MAP with THE PRODUCER'S". The kind is therefore a component of the datum
    #: this module compares, not a presentation detail of the wire, and the
    #: sector-map comparison is that comparison.
    #:
    #: ``None`` SPELLS "NO PRODUCER MAP WAS COMPARED AGAINST", AND IT IS NOT A
    #: DEFAULTED KIND. On the ARTIFACT path a producer's map always carries a
    #: kind, :func:`~certiqs_key.meat_core.declaration.bundle.declaration_from_bundle`
    #: reads it, and
    #: :func:`~certiqs_key.meat_core.declaration.admission.check_sector_map` refuses a
    #: disagreement -- an absent kind included, because "a map without one is
    #: not a map this module can compare its own against". On the IN-MEMORY
    #: path there is no producer: the caller supplies the declaration and IS
    #: both sides of the comparison, so condition (T) has nothing to compare
    #: and this slot records that rather than asserting a kind nobody declared.
    #:
    #: WHICH KIND IS RIGHT IS NOT DECIDED HERE. meat-core's contract names the
    #: kind as a component of the map to be COMPARED and does not say which
    #: value its own map carries; which kinds exist and which an operator
    #: payload may declare belongs to the shared format (spec/architecture.md
    #: Section 3.3), one tier down.
    sector_block_kind: str | None = None
    constraint_list: tuple[ConstraintEntry, ...] = ()
    #: HOW MANY OF THE TRAILING ENTRIES OF :attr:`constraint_list` REACHED THIS
    #: MODULE THROUGH A REDUCTIONS CHAIN, and it is a provenance datum and not
    #: a mathematical one: no claim of this module reads it, no predicate is
    #: decided at it, and no number depends on it. IT DECIDES NOTHING: it
    #: decides no ledger row (reductions' soundness assumption is no row). It is read
    #: off the compiler's chain record and carried into the run record's
    #: key-rate payload as provenance.
    #:
    #: THE TRAILING ENTRIES, AND THE ORDER IS THE COMPILER'S OWN.
    #: ``protocol-compiler/def:compile`` fixes the concatenation: the
    #: specification's own entries first, then those transported by the links
    #: of ``R_src``, then those of ``R_rec``, each segment in its own order. So
    #: a count of transported entries names WHICH entries they are, and the
    #: first ``len(constraint_list) - this`` are the declared ones.
    #:
    #: ZERO IS "NOT ESTABLISHED", NOT "REFUTED", and it is the default for the
    #: same reason the sector-block kind's ``None`` is: on the in-memory path
    #: there is no producer to have said otherwise. A caller that docks a
    #: compiled declaration supplies the compiler's own chain record and this
    #: is read off it (:func:`certiqs_key.meat_core.docking.dock_declaration`);
    #: a caller that builds a declaration by hand has no chain.
    constraints_through_a_reductions_chain: int = 0
    attack_set_license: Mapping[str, object] | None = None
    #: The A-SRC attestation of the `inputs` table. Required whenever a
    #: ``tau_A`` is declared and ``d_A >= 2``; VACUOUS at ``d_A = 1``, where
    #: Remark ``rem:modes-da1`` (b5) says it must not be demanded.
    source_replacement_license: Mapping[str, object] | None = None
    #: ``None`` spells the DEFAULT partition of Definition ``def:declaration``.
    party_partition: PartyPartition | None = None

    @property
    def source_mode(self) -> SourceMode:
        """Return the DERIVED source mode (contract Remark ``rem:modes-da1``).

        ``trusted`` exactly when the marginal slot carries a ``tau_A``,
        ``untrusted`` when it carries ``none``. Derived, never declared.
        """
        if self.alice_marginal is None:
            return SourceMode.UNTRUSTED
        return SourceMode.TRUSTED

    @property
    def is_trusted_source(self) -> bool:
        """Return whether a trusted marginal is declared."""
        return self.source_mode is SourceMode.TRUSTED

    @property
    def trusted_marginal(self) -> Matrix:
        """Return ``tau_A``; raise in untrusted-source mode, where there is none."""
        if self.alice_marginal is None:
            raise TypeError(
                "this declaration is in untrusted-source mode: the marginal "
                "slot holds `none` and there is no tau_A. Nothing may stand in "
                "for it -- Definition def:untrusted-choi (b) records that "
                "substituting W_tau = 1_A gives an infeasible condition, and "
                "Remark transmitter/rem:source-mode (a) that tau_A = 1_A/d_A is a "
                "different, stronger declaration"
            )
        return np.asarray(self.alice_marginal, dtype=np.complex128)

    @property
    def partition(self) -> PartyPartition:
        """Return the declared party partition, materializing the default."""
        if self.party_partition is not None:
            return self.party_partition
        return default_party_partition(self)

    @property
    def alice_outcomes(self) -> tuple[str, ...]:
        """Return Alice's outcome alphabet in its declared order."""
        return tuple(self.alice_povm)

    @property
    def bob_outcomes(self) -> tuple[str, ...]:
        """Return Bob's joint outcome alphabet in its declared order.

        Every per-round classical choice of Bob -- detection outcome, setting,
        and round type -- is a component of ``v`` (the contract's scope). There
        is no separate test-fraction register anywhere in this package, which
        is the ``output_state`` model of Assumption A-TSM.
        """
        return tuple(self.bob_povm)

    @property
    def receiver_dim(self) -> int:
        """Return ``d_Q = sum_s d_s``."""
        return sum(self.sector_dims[s] for s in self.sector_index_set)

    def readout(self, holder: str, x: str, v: str) -> str:
        """Return ``pi_h(x, v)``, what party ``h`` physically observes.

        def:admissible-declaration (viii). Under the default partition this is ``x`` for
        ``h = A`` and ``v`` for ``h = B``.
        """
        partition = self.partition
        if holder == "A":
            return partition.readout_alice[(x, v)]
        return partition.readout_bob[(x, v)]

    def announcement(self, x: str, v: str) -> tuple[str, str]:
        """Return ``a(x, v) = (a_A(pi_A(x, v)), a_B(pi_B(x, v)))``.

        def:admissible-declaration (viii): a party's announcement is a function of its
        OWN READOUT. Under the default partition ``pi_A(x, v) = x`` and
        ``pi_B(x, v) = v``, so this is the plain expression verbatim.
        """
        partition = self.partition
        return (
            self.announce_alice[partition.readout_alice[(x, v)]],
            self.announce_bob[partition.readout_bob[(x, v)]],
        )

    def acceptance_value(self, x: str, v: str) -> str:
        """Return ``phi(a(x, v))``, the acceptance value of an outcome pair."""
        return self.accept_statistic[self.announcement(x, v)]

    def raw_key(self, x: str, v: str) -> int | None:
        """Return ``r(x, v)``, with ``None`` for sifting failure."""
        return self.key_map[(x, v)]

    def block_dim(self, sector: str) -> int:
        """Return ``d_A * d_s``, the dimension of the state block ``omega_s``."""
        return self.alice_dim * self.sector_dims[sector]

    def admissible_alice_isometry(self) -> Matrix:
        """Return an isometry onto ``S_A``, the admissible Alice subspace.

        contract Eq. ``eq:SA``: ``S_A = supp tau_A`` in trusted-source mode and
        all of ``H(A)`` in untrusted-source mode. Every feasible ``omega``
        satisfies ``supp omega  <=  S_A (x) H(Q)`` -- in untrusted mode
        vacuously, and in trusted mode because ``tr[(Pi^perp x 1) omega] =
        tr[Pi^perp tau_A] = 0`` forces it by positivity (Remark
        ``rem:modes-da1`` (d)).

        The columns returned are an orthonormal basis of ``S_A``. In trusted
        mode they are also an admissible declared isometry ``iota`` of
        Eq. ``eq:iota``; the contract "deliberately names none" as canonical
        and Remark ``rem:basis-invariance`` proves the choice immaterial to
        every quantity this module reports.
        """
        if self.alice_marginal is None:
            return np.eye(self.alice_dim, dtype=np.complex128)
        return support_isometry(self.trusted_marginal)


def support_isometry(operator: Matrix) -> Matrix:
    """Return a deterministic orthonormal basis of ``supp(operator)``, as columns.

    Eigenvectors of the strictly positive spectrum, ordered by DESCENDING
    eigenvalue and phase-fixed so that the entry of largest modulus in each
    column is real and positive. The ordering and the phase convention are an
    implementation choice, licensed in as many words by the conventions --
    "ANY orthonormal basis of ``supp tau_A`` may be declared" -- and made
    deterministic so that a run is reproducible from its bundle alone
    (spec/architecture.md 2.6). What the contract requires in exchange is that
    the choice be RECORDED, which
    :mod:`certiqs_key.meat_core.finitekey.result` does through
    ``optimizer_certificate.choi_input_basis``.
    """
    values, vectors = support_spectrum(operator)
    keep = [index for index in range(values.size) if values[index] > 0.0]
    keep.sort(key=lambda index: -float(values[index]))
    if not keep:
        raise ValueError("the operator has empty support; there is no basis to fix")
    columns = []
    for index in keep:
        column = np.asarray(vectors[:, index], dtype=np.complex128)
        pivot = int(np.argmax(np.abs(column)))
        phase = column[pivot] / abs(column[pivot])
        columns.append(column / phase)
    return np.asarray(np.stack(columns, axis=1), dtype=np.complex128)


def default_party_partition(declaration: ProtocolDeclaration) -> PartyPartition:
    """Return the DEFAULT partition of contract Definition ``def:declaration``.

    ``pi_A(x, v) = x``, ``pi_B(x, v) = v``, ``A`` labelled ``A`` and every
    ``Q_s`` labelled ``B`` with one declared tensor factor apiece. The
    definition says it "reproduces versions 0.2.x of this contract verbatim",
    which is why an absent partition is this and not a refusal.
    """
    pairs = [
        (x, v) for x in declaration.alice_outcomes for v in declaration.bob_outcomes
    ]
    return PartyPartition(
        readout_alice={(x, v): x for x, v in pairs},
        readout_bob={(x, v): v for x, v in pairs},
        alphabet_alice=declaration.alice_outcomes,
        alphabet_bob=declaration.bob_outcomes,
        party_of_alice_system=PartyLabel.ALICE,
        party_of_sector_factors=dict.fromkeys(
            declaration.sector_index_set, (PartyLabel.BOB,)
        ),
        is_default=True,
    )
