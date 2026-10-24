"""The reduction request: validate, hand the builder its turn, emit -- or refuse.

ONE ENTRY POINT, ONE ORDER, ONE OUTCOME
=======================================
:func:`reduce` is the whole surface of the core. It decides every fail-closed
row it owns, gives the INSTANCE BUILDER its turn, decides the rows whose
subject is the constructed target, and only then emits. The order is not
negotiable: "EVERY RULE IS DECIDED FROM DECLARED DATA BEFORE ANYTHING IS
EMITTED; a failure produces a refusal with a machine-readable reason and NO
ARTIFACT."

The return is a :class:`~certiqs_key.reductions.artifact.ReductionOutcome`
carrying an artifact OR a refusal and never both, together with the
verification report either way. NOTHING IS RAISED FOR A FAILED RULE.

WHAT THE BUILDER PARAMETER BUYS, AND WHY THE CORE HAS ONE
=========================================================
An entry point that hard-wired ONE construction (a branching flag-state
target) would have a normalizer reading that model's modes and entries, a
chain naming its channel, a descriptor carrying its register and a ledger
carrying its assumptions, so deleting the model would not be a deletion.

Here :func:`reduce` takes a :class:`~certiqs_key.reductions.instance.InstanceBuilder`
-- a Protocol with ONE method -- and the builder supplies the reduction
instance: its sectors, its transported set, its entries, its hypotheses record,
its declared model, its physical descriptor and the ledger rows it adds. THE
CORE NAMES NO CONSTRUCTION AND IMPORTS NO SUBMODULE. What the core keeps is
what ``def:reduction-instance``, ``def:emitnorm``, ``thm:emit``,
``cor:entries`` and ``thm:chain`` state over ANY instance: the row order, the
normalizer, the emitted-family admissibility row, the entry certification, the
chain and the artifact.

A run selects :func:`certiqs_key.reductions.wpfss.reduce_flat` or a
branching submodule's entry.

EVALUATION ORDER IS NOT REPORT ORDER, AND THE DIFFERENCE IS DELIBERATE
======================================================================
The report carries EVERY row of the reduction in the INTERFACE'S order, because
it asks for "every validation rule with its outcome" and a report should read
alongside the tables. WHICH rows those are is the core's plus the ones the
builder declares -- twenty-seven on the flat path, more on a branching
one -- merged and sorted on each row's declared place in the table
(:attr:`~certiqs_key.reductions.reasons.FailClosedRow.order`). The rules are
EVALUATED in dependency order, because several of them are statements about
data another rule must first make available. No evaluation order is fixed by
the interface, and a rule evaluated before its datum exists could only report
"not decided", which would be a worse report rather than a safer one.

The refusal a caller receives is the FIRST FAILING ROW IN THE INTERFACE'S ROW
ORDER, not the first one evaluated, so that two declarations failing the same
pair of rows always name the same reason.

A REQUESTED CARRIED OPERATOR SELECTS THE LICENSED ROUTE
=======================================================
"REQUESTING ANY ENTRY SELECTS THE ``licensed`` ROUTE, because a non-empty list
requires the licence." So a request that names an entry through
``carried_operators`` is a licensed-route request, whatever the ``route`` field
says, and :func:`reduce` records the selection in the verification report's
``route`` row rather than performing it silently.

WHY THAT READING AND NOT A REFUSAL. The sentence is not conditional and is not
phrased as a refusal, in a table whose every other rule of this kind is; its
reason clause gives the mechanism -- entries make ``CList`` non-empty, a
non-empty list requires the licence, and the licence is the licensed route.
``encoded`` is the DEFAULT, so a caller who names an entry and does not mention
the route has declared nothing about it, and the selection is the only reading
under which the default and the entry can both stand. The direction is also the
conservative one: the licensed route hands the adversary more (Corollary
``cor:monotone``) and requires a licence and a certificate the encoded route
does not. Nothing is weakened by the switch, and NOTHING IS SILENT.

WHAT THE MACHINE NEVER DOES
===========================
It substitutes no default for a missing datum, clips no weight, waives no fibre
condition, and emits no licence without its certificate. It recomputes no
receiver quantity: the supplier's weights and blocks are "referenced,
transported, and NEVER re-derived or re-quantified". It never upgrades
``bound_evaluation``. And it decides no assumption the ledger marks never
verifiable: for A-RECV it tests that the declared version resolves to an
accepted contract and names the artifact by version in the licence, and it
omits the row only where the run attests that it built the artifact and the
artifact is exact and rigorously evaluated
(:func:`receiver_row_omitted_on_provenance`); an assumption a submodule adds
is that submodule's, decided the same way.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace

from certiqs_key.foundations.exact import Matrix, is_positive_semidefinite
from certiqs_key.reductions.artifact import (
    BlockEmissionRecord,
    EmissionRecord,
    ProofReductionArtifact,
    ReductionOutcome,
    VerificationReport,
    assumption_ledger,
)
from certiqs_key.reductions.channels import ChannelWitness
from certiqs_key.reductions.companion import (
    CompanionAbsence,
    NoReferenceCompanion,
    ReferenceCompanion,
    reference_companion,
)
from certiqs_key.reductions.constraints import (
    ConstraintEntry,
    EntryWriting,
    issue_licence,
)
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import (
    InstanceSnapRecord,
    Label,
    ReductionCall,
    outcome_label,
)
from certiqs_key.reductions.instance import (
    BuildContext,
    InstanceBuilder,
    ReductionInstance,
)
from certiqs_key.reductions.joint import joint_classes
from certiqs_key.reductions.links import Chain, Link, SystemFamily
from certiqs_key.reductions.normalizer import JointClass, Normalization
from certiqs_key.reductions.reasons import (
    CORE_ASSUMPTIONS,
    CORE_FAIL_CLOSED_ROWS,
    OMITTED_ON_RECEIVER_PROVENANCE,
    PRESENT_ONLY_WITH_A_NON_EMPTY_CONSTRAINT_LIST,
    PRESENT_ONLY_WITH_A_NON_EMPTY_SOURCE_SEGMENT,
    PRESENT_ONLY_WITH_A_PRIVATE_SETTING,
    PRESENT_ONLY_WITH_A_SETTING_OR_A_CHOICE,
    SNAPPED_MEASUREMENT_ROW,
    AssumptionRow,
    FailClosedRow,
    FailClosedRule,
    LinkKind,
    LinkStatus,
    Refusal,
    RefusalReason,
    Route,
)
from certiqs_key.reductions.sectors import assemble_sector_blocks
from certiqs_key.reductions.validation import (
    ExactAdmissibilityDecision,
    RuleOutcome,
    resolve_route,
    rule_alphabet_order,
    rule_approximate,
    rule_block_structure_from_blocks,
    rule_chain,
    rule_constraint_certificate,
    rule_constraint_channel,
    rule_cutoff,
    rule_device_family,
    rule_emitted_family,
    rule_exact_admissibility,
    rule_lattice_exponent,
    rule_licence_presence,
    rule_licensed_hermiticity,
    rule_link_kind,
    rule_obstructions,
    rule_post_processing_order,
    rule_probe_weights,
    rule_receiver_spec,
    rule_requested_assurance,
    rule_route,
    rule_unsound_transplant,
)

__all__ = [
    "emitted_assumption_rows",
    "outcome_label",
    "receiver_row_omitted_on_provenance",
    "reduce",
]


@dataclass
class _Report:
    """Every row under construction, evaluated in dependency order.

    THE EVALUATION ORDER IS NOT THE REPORT ORDER AND NEED NOT BE. Rows are
    decided here in the order their data becomes available; the report is
    assembled in the INTERFACE'S row order, and the refusal a caller receives is
    the FIRST refusal in THAT order. So which reason a caller receives is fixed
    by the interface's ordering of its tables and not by the sequence of calls
    below.

    ``rows`` is the row set of THIS reduction -- the core's plus the builder's
    -- and it is what :meth:`finish` iterates. The number of rows is written
    nowhere: it is ``len(self.rows)``, which depends on the builder (twenty-seven
    flat, more on a branching path), and a spelled-out count in a docstring goes stale
    at every amendment.
    """

    outcomes: dict[str, RuleOutcome] = field(default_factory=dict)
    rows: dict[str, FailClosedRow] = field(default_factory=dict)

    def add_rows(self, rows: Sequence[FailClosedRow]) -> None:
        """Put a group of rows in this reduction's row set."""
        for row in rows:
            existing = self.rows.get(str(row.rule))
            if existing is not None and existing != row:
                raise MalformedInputError(
                    f"the row {row.rule!r} is declared twice with two readings; "
                    "a reduction reports one outcome per row"
                )
            self.rows[str(row.rule)] = row

    def order(self) -> tuple[str, ...]:
        """Return this reduction's rows, in the interface's table order."""
        return tuple(
            row.rule for row in sorted(self.rows.values(), key=lambda row: row.order)
        )

    def decide(self, rule: str, refusal: Refusal | None, detail: str = "") -> None:
        """Record a DECIDED row."""
        self.outcomes[str(rule)] = RuleOutcome(
            rule=rule, decided=True, refusal=refusal, detail=detail
        )

    def undecidable(self, rule: str, detail: str) -> None:
        """Record a row that could NOT be decided on this declaration.

        Not a pass. Every rule "is decided from declared data"; where a
        declaration does not carry the datum a row quantifies over, saying so is
        the honest record and reporting a vacuous success is not.
        """
        self.outcomes[str(rule)] = RuleOutcome(
            rule=rule, decided=False, refusal=None, detail=detail
        )

    def absorb(self, outcomes: Sequence[RuleOutcome]) -> None:
        """Take the outcomes a builder decided for the rows it owns."""
        for outcome in outcomes:
            self.outcomes[str(outcome.rule)] = outcome

    def passed(self, rules: Sequence[str]) -> bool:
        """Whether every named row has been decided and did not refuse."""
        return all(
            str(rule) in self.outcomes and self.outcomes[str(rule)].passed
            for rule in rules
        )

    def refused(self, rule: str) -> bool:
        """Whether the named row has been decided AND refused.

        The weaker companion of :meth:`passed`, for a row whose clauses are
        decided in two places: "has not refused so far" is what may gate the
        work that the row's remaining clause depends on, while "passed" is what
        may gate an emission.
        """
        outcome = self.outcomes.get(str(rule))
        return outcome is not None and outcome.refusal is not None

    def finish(
        self,
        receiver_spec_version: str,
        bound_evaluation: str,
        requested_assurance: str,
    ) -> VerificationReport:
        """Return the report with EVERY row of this reduction, in table order."""
        order = self.order()
        for rule in order:
            if rule not in self.outcomes:  # pragma: no cover - guarded by tests
                self.undecidable(rule, "not reached")
        return VerificationReport(
            outcomes=tuple(self.outcomes[rule] for rule in order),
            receiver_spec_version=receiver_spec_version,
            receiver_bound_evaluation=bound_evaluation,
            requested_assurance=requested_assurance,
        )


def reduce(request: ReductionCall, builder: InstanceBuilder) -> ReductionOutcome:
    """Run a reduction request against one instance builder: emit or refuse.

    ``request`` carries the interface's three groups of declared inputs;
    ``builder`` is the one method that turns them into a reduction instance.
    See the module docstring for what each side owns.
    """
    artifact_rows = request.artifact_rows
    declaration = request.declaration
    declared = request.request
    report = _Report()
    report.add_rows(CORE_FAIL_CLOSED_ROWS)

    # --- the declared lattice exponent, FIRST ------------------------------
    # "THIS ROW RUNS FIRST AND REFUSES BEFORE ANYTHING IS CONSTRUCTED" -- a
    # statement about ORDER, so it is decided before any other declared datum
    # is read. A defaulted lattice "WOULD DECIDE A SECURITY-RELEVANT PREDICATE
    # ON NOBODY'S AUTHORITY" (spec/architecture.md 2.9, condition (D-LAT)).
    lattice_refusal = rule_lattice_exponent(
        declared.lattice_exponent,
        alphabet_sizes={
            "V": len(declaration.joint_alphabet),
            "Y": len(declaration.detection_alphabet),
            "T": len(declaration.probe_declaration.settings),
        },
    )
    report.decide(FailClosedRule.LATTICE_EXPONENT, lattice_refusal)
    kappa: int | None = (
        int(declared.lattice_exponent)  # type: ignore[call-overload]
        if lattice_refusal is None
        else None
    )

    # --- the run's strict option -------------------------------------------
    # foundations/req:snap-reference (iv), a run parameter recorded either
    # way: a moved class is refused at emission where no reference companion
    # is formed (req:emission-refusal), and disclosed otherwise.
    strict = bool(declared.strict_snaps)

    # --- the requested assurance is a LIVE rung ----------------------------
    assurance = _requested_assurance(declared.requested_assurance)
    report.decide(
        FailClosedRule.REQUESTED_ASSURANCE,
        rule_requested_assurance(assurance, live_rungs=_live_rungs()),
    )

    # --- rows decidable from the request and the declaration alone ---------
    declared_route = declared.route
    effective_route = (
        Route.LICENSED.value
        if declared.carried_operators and declared_route == Route.ENCODED.value
        else declared_route
    )
    selection_detail = (
        ""
        if effective_route == declared_route
        else (
            "the request names "
            f"{len(declared.carried_operators)} carried operator(s), which "
            'SELECTS the licensed route (constraint_list row: "Requesting any '
            "entry selects the licensed route, because a non-empty list "
            'requires the licence"); the declared route field read '
            f"{declared_route!r}"
        )
    )
    report.decide(FailClosedRule.ROUTE, rule_route(effective_route), selection_detail)
    route = resolve_route(effective_route)
    report.decide(
        FailClosedRule.POST_PROCESSING_ORDER,
        rule_post_processing_order(declared.squash_before_post_processing),
    )
    report.decide(
        FailClosedRule.UNSOUND_TRANSPLANT,
        rule_unsound_transplant(declared.carried_operators),
    )
    report.decide(FailClosedRule.LINK_KIND, rule_link_kind(declared.link_declarations))
    report.decide(
        FailClosedRule.APPROXIMATE, rule_approximate(declared.link_declarations)
    )
    report.decide(FailClosedRule.DEVICE_FAMILY, rule_device_family(artifact_rows))
    report.decide(
        FailClosedRule.RECEIVER_SPEC,
        rule_receiver_spec(artifact_rows, declared.accepted_receiver_versions),
    )
    report.decide(
        FailClosedRule.CUTOFF, rule_cutoff(declaration.photon_cutoff, artifact_rows)
    )
    report.decide(
        FailClosedRule.PROBE_WEIGHTS,
        rule_probe_weights(declaration.probe_declaration, lattice_exponent=kappa),
    )

    # --- Lemma lem:obstructions, on every relation the CALLER declares -----
    if declared.declared_relations:
        obstruction: Refusal | None = None
        for physical, target in declared.declared_relations:
            obstruction = rule_obstructions(physical, target)
            if obstruction is not None:
                break
        report.decide(
            FailClosedRule.OBSTRUCTIONS,
            obstruction,
            f"{len(declared.declared_relations)} declared relation(s) checked "
            "against Lemma lem:obstructions",
        )
    else:
        report.decide(
            FailClosedRule.OBSTRUCTIONS,
            None,
            "vacuous: the request declares no relation of its own, and the "
            "relation this module constructs is a theorem (prop:chain (i), "
            "the instance's existence theorem) rather than a declaration to "
            "refuse",
        )

    # --- the alphabet agreements -------------------------------------------
    # THE ROW IS NOT YET FULLY DECIDED HERE, and the report says so. The
    # alphabet, the echoed T and the basis-order clauses are decidable before
    # anything is built and are decided now, because a mismatch in any of them
    # must refuse before a target is constructed from disagreeing alphabets.
    # The declared-SECTOR-order clause is not: the sector order exists only
    # once the target does. So a pass here is recorded as NOT YET DECIDED
    # rather than as passed -- otherwise a report that ends at an earlier
    # refusal would show the row green although the declared sector order was
    # never compared.
    alphabet_refusal = rule_alphabet_order(
        artifact_rows,
        declaration.detection_alphabet,
        declaration.probe_declaration,
        declaration.joint_alphabet,
        declared.declared_sector_order,
        None,
        declared.declared_occupation_basis_order,
    )
    if alphabet_refusal is not None:
        report.decide(FailClosedRule.ALPHABET_ORDER, alphabet_refusal)
    else:
        report.undecidable(
            FailClosedRule.ALPHABET_ORDER,
            "the alphabet, the echoed T and the basis-order clauses hold; the "
            "declared-sector-order clause needs the constructed sector order "
            "and is decided after the target is built",
        )

    # --- the declared blocks, structurally then numerically ----------------
    # THE ROW READS THE RECEIVER'S OWN ALPHABETS, not the declaration's. A
    # disagreement between the two is the ALPHABET row, and reading the
    # declaration's letters here would attribute it to this row instead --
    # which, being the earlier row, is the reason a caller would receive.
    report.decide(
        FailClosedRule.BLOCK_STRUCTURE,
        rule_block_structure_from_blocks(
            artifact_rows.photon_blocks,
            artifact_rows.channel_grading,
            artifact_rows.detection_alphabet,
            artifact_rows.bound_quantifier_domain.settings,
            photon_blocks_form=artifact_rows.photon_blocks_form,
        ),
    )
    admissibility = ExactAdmissibilityDecision(None, ())
    if kappa is None:
        report.undecidable(
            FailClosedRule.EXACT_ADMISSIBILITY,
            "the lattice row refused, so there is no declared kappa and "
            "Eq. eq:latinv -- one of the five conjuncts of def:exactadm (c) -- "
            "has nothing to be decided against",
        )
    else:
        admissibility = rule_exact_admissibility(
            artifact_rows.photon_blocks,
            artifact_rows.channel_grading,
            artifact_rows.detection_alphabet,
            artifact_rows.bound_quantifier_domain.settings,
            lattice_exponent=kappa,
        )
        report.decide(
            FailClosedRule.EXACT_ADMISSIBILITY,
            admissibility.refusal,
            "the five conjuncts of Definition def:exactadm (c), DECIDED AND "
            "NOT MEASURED, in the substrate of Lemma lem:exactpsd: "
            + ", ".join(
                f"{name}={'pass' if held else 'FAIL'}"
                for name, held in admissibility.conjuncts
            )
            + ". No window appears anywhere and nothing is repaired: the "
            "perturbation this row does not see was absorbed AT THE INSTANCE, "
            "before this module was reached",
        )

    # --- the builder's turn -------------------------------------------------
    core_ready = report.passed(
        (
            FailClosedRule.BLOCK_STRUCTURE,
            FailClosedRule.PROBE_WEIGHTS,
            FailClosedRule.CUTOFF,
        )
    ) and not report.refused(FailClosedRule.ALPHABET_ORDER)
    classes: tuple[JointClass, ...] = ()
    if report.passed((FailClosedRule.PROBE_WEIGHTS,)) and not report.refused(
        FailClosedRule.ALPHABET_ORDER
    ):
        classes = joint_classes(
            declaration.probe_declaration, declaration.joint_alphabet
        )
    built = builder.build(
        BuildContext(
            request=request,
            lattice_exponent=kappa,
            route=route,
            classes=classes,
            core_ready=core_ready,
        )
    )
    report.add_rows(built.rows)
    report.absorb(built.outcomes)
    instance = built.instance

    if instance is None:
        for rule in (
            FailClosedRule.EMITTED_FAMILY,
            FailClosedRule.CHAIN,
            FailClosedRule.CONSTRAINT_CERTIFICATE,
            FailClosedRule.LICENCE_PRESENCE,
            FailClosedRule.CONSTRAINT_CHANNEL,
            FailClosedRule.LICENSED_HERMITICITY,
        ):
            report.undecidable(
                rule,
                "an earlier row refused or could not be decided, so no target "
                "was constructed and this row has nothing to decide on",
            )
        finished = report.finish(
            artifact_rows.mathematical_spec_version,
            artifact_rows.bound_evaluation,
            assurance,
        )
        return ReductionOutcome(
            artifact=None,
            refusal=finished.refusal
            or Refusal(
                reason=RefusalReason.CHAIN_ILL_FORMED,
                rule=str(FailClosedRule.CHAIN),
                detail="no target could be constructed from the declared data",
            ),
            verification_report=finished,
        )

    assert kappa is not None
    order = declaration.joint_alphabet

    # --- THE SECOND GATE: the family this module is about to emit ----------
    # "BEFORE THE ARTIFACT LEAVES, this module decides -- AGAIN EXACTLY -- that
    # THE FAMILY IT IS ABOUT TO EMIT IS ITSELF EXACTLY ADMISSIBLE, and refuses
    # NAMING THE PREDICATE when it is not."
    #
    # DECIDED ON THE WHOLE ASSEMBLED FAMILY AND ON ALL SIX. thm:emit (ii) states
    # the six of "the family {F_v}, PRESENTED AS THE SECTOR-BLOCK LIST
    # eq:instance-target", which is the direct sum over EVERY sector -- so the
    # row reads the assembled per-sector list and not the normalizer's data
    # sectors alone. A scalar sector's phi_s(v) is declared rather than
    # computed, and (I2)'s conditions on it are decided here, on the numbers
    # about to be emitted, exactly as a consumer re-deciding the six would.
    # The sector map is the block-structure row's subject and is carried
    # across: the emitted data sectors are built sector by sector from the
    # declared blocks and the grading is echoed unchanged, so clause (a) holds
    # exactly where that row passed.
    normalized = instance.normalized
    # THE REFERENCE COMPANION IS FORMED HERE WHERE THE STRICT OPTION NEEDS IT
    # (req:emission-refusal): a moved class is refused at emission exactly
    # where no companion that bypasses the normalizer is formed beside the
    # artefact. Elsewhere it is formed after every row passed, below; either
    # way a refused reduction carries none.
    companion: ReferenceCompanion | NoReferenceCompanion | None = None
    if (
        strict
        and normalized.moved
        and route is not None
        and not report.refused(FailClosedRule.EXACT_ADMISSIBILITY)
    ):
        companion = reference_companion(
            request,
            builder,
            lattice_exponent=kappa,
            route=route,
            classes=classes,
            emitted=_emitted_entries,
            classes_moved=True,
            requested=_requested_entries(instance, route),
        )
    if report.refused(FailClosedRule.EXACT_ADMISSIBILITY):
        # THE SECOND GATE HAS NO SUBJECT HERE. thm:emit is stated for declared
        # data that pass every refusal rule, and the six conditions are decided
        # "on the numbers about to be emitted"; where the declared blocks are
        # refused nothing is emitted, and the normalizer, which repairs nothing
        # it was handed (def:emitnorm, fourth property), has passed a class
        # outside D_adm through untouched. Deciding the row on it would report
        # a second refusal of the one defect the earlier row names.
        report.undecidable(
            FailClosedRule.EMITTED_FAMILY,
            "the declared blocks are not exactly admissible (the exact-"
            "admissibility row refused), so no family is about to be emitted "
            "and thm:emit's hypothesis does not hold; the normalizer repaired "
            "nothing it was handed",
        )
    else:
        report.decide(
            FailClosedRule.EMITTED_FAMILY,
            rule_emitted_family(
                assemble_sector_blocks(
                    instance.sectors, normalized.family, instance.scalar_values, order
                ),
                order,
                instance.sectors.dimensions,
                lattice_exponent=kappa,
                sector_map_agrees=report.passed((FailClosedRule.BLOCK_STRUCTURE,)),
                strict_refusal=(
                    _strict_refusal(normalized, companion)
                    if strict and isinstance(companion, NoReferenceCompanion)
                    else None
                ),
            ),
            "the six (D-EMIT) conditions of def:exactadm, decided on the numbers "
            "about to be emitted, AFTER def:emitnorm's steps; on declared data "
            "that pass the refusal rules this is a DEFENSIVE exact check "
            "(thm:emit (ii)), and the one refusal of a class that can occur is the "
            "strict option's (req:emission-refusal). "
            + (
                "The normalizer left every data sector on the declared lattice and "
                "moved nothing."
                if all(snap.already_on_lattice for snap in normalized.blocks)
                else "The normalizer acted; the per-sector displacement is in "
                "emission_record."
            )
            + (
                ""
                if not instance.hypotheses
                else " The instance's hypotheses (H), none of which reads a data "
                "sector (def:reduction-instance (I1), the stability clause): "
                + "; ".join(instance.hypotheses)
            ),
        )

    # --- the sector-order clause, decided now that the sectors exist -------
    constructed_sector_order = tuple(
        f"{group}:{name}" for group, name in instance.sectors.labels
    )
    report.decide(
        FailClosedRule.ALPHABET_ORDER,
        rule_alphabet_order(
            artifact_rows,
            declaration.detection_alphabet,
            declaration.probe_declaration,
            declaration.joint_alphabet,
            declared.declared_sector_order,
            constructed_sector_order,
            declared.declared_occupation_basis_order,
        ),
        "the declared-sector-order clause is decided HERE rather than in the "
        "first pass, because the sector order exists only once the target is "
        "constructed; the alphabet and basis clauses were decided before "
        "anything was built and are re-decided unchanged",
    )

    # --- the certificate, the licence, and the channel binding -------------
    # THEOREM DISCHARGE IS FOR THE ENTRIES THE INSTANCE BUILT, AND NO OTHER,
    # AND THE LOCATOR IS THE INSTANCE'S. What discharges an instance's own
    # entry is that instance's claim -- wpfss/cor:fssinstance for the flat
    # instance, cor:register-instance (ii) for a branching one -- so the
    # builder supplies the locator with the entry
    # (ReductionInstance.module_built_locators) and THE CORE NAMES NO
    # CONSTRUCTION. A caller's `carried_operators` entry is NOT in this
    # mapping: the builder decided it on declared data, and putting it here
    # would let a request reach a discharge it did not earn.
    # WHAT IS EMITTED IS DECIDED HERE, AGAINST WHAT THE INSTANCE HOLDS.
    entries = _emitted_entries(instance, route)
    emitted_labels = {entry.label for entry in entries}
    discharged = {
        label: instance.module_built_locators[label]
        for label in instance.module_built
        if label in emitted_labels
    }
    certificate_refusal = rule_constraint_certificate(
        entries,
        {},
        theorem_discharged=discharged,
        decided_before_this_row=instance.requested_locators,
    )
    preserved = tuple(normalized.family[v] for v in order)
    if certificate_refusal is None:
        certificate_refusal = _data_sector_positivity(entries, preserved)
    if instance.carried_operator_refusal is not None:
        # A requested carried operator was already refused by the builder; that
        # refusal is the one the caller receives, and it is not overwritten by
        # a later pass that sees only the entries which survived.
        certificate_refusal = instance.carried_operator_refusal
    report.decide(
        FailClosedRule.CONSTRAINT_CERTIFICATE,
        certificate_refusal,
        "the decidable half of Eq. eq:certificate is checked here; the "
        "above-cutoff half is Eq. eq:certweights, which the supplier certifies "
        "and Assumption A-RECV imports -- the supplier emits no above-cutoff "
        "block, so no pull-back is materialisable."
        + (
            ""
            if not discharged
            else " Discharged by theorem, per entry: "
            + "; ".join(
                f"{label} -> {locator}" for label, locator in discharged.items()
            )
        )
        + (
            ""
            if not instance.requested_locators
            else " Decided before this row, per entry: "
            + "; ".join(
                f"{label} -> {locator}"
                for label, locator in instance.requested_locators.items()
            )
        ),
    )

    # --- exact Hermiticity on the licensed route ---------------------------
    # DECIDED BEFORE THE LICENCE IS ISSUED, which is what Corollary cor:entries
    # assumes of it: "suppose -- AS [the interface] DECIDES BEFORE THAT ROUTE
    # IS TAKEN -- that every emitted constraint operator is EXACTLY Hermitian".
    # The fail-closed convention forbids symmetrizing one, so the row refuses
    # rather than repairing.
    hermiticity_refusal = rule_licensed_hermiticity(
        entries, route, lattice_exponent=kappa
    )
    if route is Route.LICENSED:
        report.decide(FailClosedRule.LICENSED_HERMITICITY, hermiticity_refusal)
    else:
        report.undecidable(
            FailClosedRule.LICENSED_HERMITICITY,
            "the row is scoped to the `licensed` route; the encoded route emits "
            "an empty list, so there is no emitted constraint operator to "
            "decide exact Hermiticity of",
        )

    licence = (
        None
        if hermiticity_refusal is not None
        else issue_licence(
            entries,
            declaration.source_mode,
            artifact_rows.mathematical_spec_version,
            # req:licence-record: PER ENTRY THE CLAIM THAT DISCHARGES IT -- the
            # instance's own locator for an entry it built, the locator the
            # builder recorded for a requested one -- and whether that claim
            # reads the supplier's facts.
            discharged_by={
                **instance.module_built_locators,
                **instance.requested_locators,
            },
            supplier_free=instance.supplier_free_entries,
        )
    )
    if hermiticity_refusal is not None:
        report.undecidable(
            FailClosedRule.LICENCE_PRESENCE,
            "the licensed-route Hermiticity row refused, so no licence was "
            "issued and the presence iff has nothing to decide on",
        )
    else:
        report.decide(
            FailClosedRule.LICENCE_PRESENCE,
            rule_licence_presence(entries, licence is not None),
        )
    # THE ENTRIES SIT ON THE LAST LINK, the instance's squashing link.
    report.decide(
        FailClosedRule.CONSTRAINT_CHANNEL,
        rule_constraint_channel(entries, instance.witness.identity),
    )

    # --- the chain ----------------------------------------------------------
    chain: Chain | None = None
    if not report.passed((FailClosedRule.LINK_KIND, FailClosedRule.APPROXIMATE)):
        # A declared kind this version reserves, or a status it never emits,
        # has no link to build: those two rows have already refused, and
        # inventing a link for a kind the interface refuses would only add a
        # second reason for one failure.
        report.undecidable(
            FailClosedRule.CHAIN,
            "a declared link kind is reserved and refused in this version, or a "
            "status other than `exact` was requested, so no link was built and "
            "Definition def:chain has nothing to decide on",
        )
    elif route is None:  # pragma: no cover - guarded by the route row
        report.undecidable(
            FailClosedRule.CHAIN,
            "the route row refused, so the squashing link's kind is not fixed",
        )
    else:
        chain_result = _build_chain(request, instance, entries, licence, route)
        if isinstance(chain_result, Refusal):
            report.decide(FailClosedRule.CHAIN, chain_result)
        else:
            chain = chain_result
            report.decide(FailClosedRule.CHAIN, rule_chain(chain))

    finished = report.finish(
        artifact_rows.mathematical_spec_version,
        artifact_rows.bound_evaluation,
        assurance,
    )
    refusal = finished.refusal
    if refusal is not None or chain is None or route is None:
        return ReductionOutcome(
            artifact=None,
            refusal=refusal
            or Refusal(
                reason=RefusalReason.CHAIN_ILL_FORMED,
                rule=str(FailClosedRule.CHAIN),
                detail="the declared chain does not realize the emitted target",
            ),
            verification_report=finished,
        )

    artifact = _emit(
        request,
        instance,
        entries,
        licence,
        chain,
        route,
        finished,
        _emission_record(
            normalized,
            kappa,
            tuple(c.label for c in classes),
            entries,
            instance.constant_rounding,
            strict=strict,
            enclosed_references_used=bool(declared.reference_enclosure),
        ),
    )
    # THE REFERENCE COMPANION, beside the emitted artefact and never in place
    # of it (req:reference-companion): the same builder run on the handed
    # reference, with the same lattice exponent, route and classes, its entries
    # emitted by the same rule (cor:entries). Formed only after every row
    # passed, so a refused reduction forms none; the artefact itself is
    # emitted as it is without a companion (item (v)).
    if companion is None:
        companion = reference_companion(
            request,
            builder,
            lattice_exponent=kappa,
            route=route,
            classes=classes,
            emitted=_emitted_entries,
            classes_moved=bool(normalized.moved),
            requested=_requested_entries(instance, route),
        )
    return ReductionOutcome(
        artifact=replace(artifact, reference_companion=companion),
        refusal=None,
        verification_report=finished,
    )


def _requested_assurance(value: object) -> str:
    """Return the declared ``requested_assurance``, unchanged, as a string.

    THE VALUE IS READ AND THE ROW DECIDES IT. This function validates nothing
    about the tier: it converts the declared datum to the string the row
    compares and the verification report records, and
    :func:`certiqs_key.reductions.validation.rule_requested_assurance` refuses a
    value that is not one of the live rungs.

    THE ROW'S SUBJECT IS A VALUE THAT IS NOT ONE OF THE TIERS of
    ``foundations/def:tiers`` -- ``estimate``, ``first-order`` and, under
    PRINCIPLES.md section 10, ``certified`` -- which is
    exactly what ``requested_assurance_unknown`` names; a string that is no
    tier receives that reason, and only a value of another type is malformed.

    NOTHING HERE DECIDES A TIER. This module "PROPAGATES THE UPSTREAM
    ``bound_evaluation`` VALUE UNCHANGED AND NEVER UPGRADES IT", the
    verification report carries the request beside it, and the emitted
    ``status`` is ``exact`` whatever was requested.
    """
    if not isinstance(value, str):
        raise MalformedInputError(
            f"requested_assurance = {value!r} is not a tier label; the row "
            "compares a declared STRING against the live rungs, and a value of "
            "another type is not a presentation of the row at all"
        )
    return value


def _live_rungs() -> tuple[str, ...]:
    """Return the LIVE rung labels, as strings.

    THE SECOND OF THE TWO SITES THAT REACH THE PLATFORM TIER VOCABULARY, and
    the import is function-local for the reasons :func:`_requested_assurance`
    gives. The strings are RETURNED rather than compared here, so that
    :mod:`certiqs_key.reductions.validation` -- which decides the row -- carries
    no tier literal either.

    THERE IS NO SHELVED RUNG TO LEAVE OUT. Every member of
    :class:`~certiqs_key.foundations.assurance.Assurance` is a
    tier of ``foundations/def:tiers`` (``certified`` among them,
    PRINCIPLES.md section 10), so the ladder is the whole enum and
    the row refuses anything outside it under ``requested_assurance_unknown``.
    """
    from certiqs_key.foundations.assurance import Assurance

    return tuple(str(member.value) for member in Assurance)


def _emitted_entries(
    instance: ReductionInstance, route: Route | None
) -> tuple[ConstraintEntry, ...]:
    """Corollary ``cor:entries``: WHAT IS EMITTED, against what the instance HOLDS.

    The ``constraint_list`` row states the emission rule as a statement about
    the REQUEST and about the instance's own list, AND THE TWO ARE DIFFERENT
    OBJECTS: "EMPTY WHERE THE REQUEST CARRIES NO ENTRY, **WHATEVER ENTRIES THE
    INSTANCE'S OWN LIST CONTAINS**; WHERE THE REQUEST CARRIES ENTRIES, the
    entries the instance carries ... plus any further entry requested through
    ``carried_operators`` whose certificate a claim decides on the emitted
    numbers" (``cor:entries`` (iii); ``req:uncertified-operator-refused``), which
    the builder decided before this pass. ``wpfss``'s two routes
    are that submodule's instance of the two cases -- the ``encoded`` route is
    the request that carries no entry -- and a request naming a carried operator
    SELECTS the licensed route before this point, so the encoded route reaches
    here with nothing requested.

    SO THE EMISSION DECIDES THE EMPTINESS, AND A BUILDER DOES NOT. An instance's
    own entry list is its own claim's: a route may enter it, where that
    instance's proposition says so, but an instance may equally hold an entry
    ITS CLAIM PUTS THERE UNCONDITIONALLY -- a branching instance's branch-weight
    entry is one -- and the row's "whatever entries the instance's own list
    contains" is exactly about that case. Deciding the emptiness inside a
    builder would make the two objects one and leave the instance's list disagreeing
    with the claim that states it, at the one place the claims distinguish them.
    The route
    that emits no entry emits an empty list and no licence.
    """
    if route is Route.ENCODED:
        return ()
    return tuple(instance.entries)


def _requested_entries(
    instance: ReductionInstance, route: Route | None
) -> tuple[tuple[ConstraintEntry, EntryWriting | None], ...]:
    """Return the requested entries the artefact carries, with their writings.

    ``reductions/req:reference-companion`` (iii): the companion forms each at
    the writing of ``eq:instance-entry`` by which the builder recognised it.
    """
    return tuple(
        (entry, instance.requested_writings.get(entry.label))
        for entry in _emitted_entries(instance, route)
        if entry.label in instance.requested_locators
    )


def _data_sector_positivity(
    entries: Sequence[ConstraintEntry], data: Sequence[Sequence[Matrix]]
) -> Refusal | None:
    """Check the half of an instance's entry certificate that IS decidable here.

    ``def:reduction-instance`` (I4) requires every module-built entry's
    certificate Eq. ``eq:certificate`` to be discharged "for every admissible
    datum under (H)", and the instance's claim discharges it. PART OF THAT
    DISCHARGE READS THE EMITTED DATA SECTORS AND IS THEREFORE DECIDABLE ON THE
    NUMBERS THIS MODULE IS ABOUT TO EMIT: every entry this module emits is
    positive on the data sectors, the operator being formed from them by
    subtracting a multiple of a scalar-sector projector. The rest of the
    discharge rests on a hypothesis in (H) -- an above-cutoff fact the supplier
    certifies and Assumption A-RECV imports -- which this module names and can
    never verify, and on which nothing is decided here.

    THE OVERLAP WITH THE EMITTED-FAMILY ROW IS DELIBERATE AND IS NOT A DOUBLE
    DECISION. That row decides ``def:exactadm`` (c) on the whole emitted family
    per sector block; this decides ONE SUMMAND OF ONE ENTRY'S PULL-BACK, and it
    is the certificate row that refuses where it fails, naming
    Eq. ``eq:certificate`` rather than (D-EMIT). Two rows, two reasons, one
    fact -- which is what lets a reader of the refusal tell which obligation was
    not met.

    DECIDED PER DATA SECTOR BLOCK, on the block list the normalizer declared: a
    direct sum is positive exactly when every block is, and the refusal can
    then name WHICH block failed, which a decision on the assembled sum cannot
    (spec/architecture.md 2.8-2.9).
    """
    if not entries:
        return None
    for index, blocks in enumerate(data):
        for position, block in enumerate(blocks):
            if not is_positive_semidefinite(block):
                return Refusal(
                    reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                    rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
                    detail=(
                        f"the emitted data sector {position} at outcome index "
                        f"{index} is not positive, so the data-sector summand "
                        "of the entry's pull-back is not positive and "
                        "eq:certificate fails (def:reduction-instance (I4))"
                    ),
                )
    return None


def _build_chain(
    request: ReductionCall,
    instance: ReductionInstance,
    entries: Sequence[ConstraintEntry],
    licence: object | None,
    route: Route,
) -> Chain | Refusal:
    """Build one typed link per declared kind, in the declared order.

    EVERY LINK IS BUILT HONESTLY FOR ITS KIND and the three conditions of
    Definition ``def:chain`` are then DECIDED on the result -- they are not
    arranged to hold. A ``flags-enough`` link, for instance, lands on a family
    whose base block has been replaced, which is not the emitted target, so
    (C1) fails and the chain is refused.

    WHICH KIND THE SQUASHING LINK MUST CARRY IS THE INSTANCE'S. It declares the
    kinds that may name it, those of them whose choice is BOUND TO THE ROUTE,
    and the one the resolved route expects; the core compares and refuses,
    naming Remark ``rem:tworoutes``. Declaring two squashing links makes the
    second's source the first's target rather than the physical family, and
    (C1) refuses it.
    """
    physical = SystemFamily(
        description=instance.physical_family_description, dimension=None, povm=None
    )
    target = SystemFamily(
        description=instance.target_descriptor.space_formula,
        dimension=instance.target_dimension,
        povm=instance.target_povm,
    )
    carried_labels = tuple(entry.label for entry in instance.transported)
    # lem:precomposed-instance (ii): a precomposed instance's pull-backs are
    # Phi^dagger of its own; the transported operators themselves, their
    # certificates and constants are unchanged (wpfss/req:normalized-link-record
    # (iii)).
    pullback_labels = tuple(
        instance.pullback_expression(entry.pullback_expression)
        for entry in instance.transported
    )
    squashing_reachable = (
        "{ (Lambda (x) id)(rho) : rho in S^ph }, Definition "
        "def:sound for the instance's channel"
        if instance.precomposition is None
        else instance.precomposition.reachable_set_statement
    )

    links: list[Link] = []
    current = physical
    # (C2) is a statement about ADJACENT links: link i's O^_out must be link
    # i+1's O_in. The tuple is therefore CARRIED THROUGH rather than restated
    # per kind -- which is also what Example ex:identity permits of an identity
    # link, "the carried tuple EMPTY OR THE IDENTITY ON ANY DECLARED
    # OPERATORS".
    incoming: tuple[str, ...] = ()
    for index, declared in enumerate(request.request.link_declarations):
        link_id = f"L{index + 1}-{declared.kind.value}"
        first = not links
        if declared.kind is LinkKind.IDENTITY:
            link = Link(
                stage=declared.stage,
                kind=declared.kind,
                source_family=current,
                target=current,
                channel_witness=ChannelWitness(
                    identity=f"{link_id}:id",
                    equation="Lambda_l = id (ex:identity; prop:preorder)",
                ),
                carried_operator_pair=(incoming, incoming),
                reachable_set_statement="the whole declared input family S^ph",
                constraint_entries=(),
                licence=None,
                status=LinkStatus.EXACT,
                link_id=link_id,
            )
        elif declared.kind in instance.squashing_kinds:
            expected = instance.expected_squashing_kind
            if (
                declared.kind in instance.route_bound_kinds
                and declared.kind is not expected
            ):
                return Refusal(
                    reason=RefusalReason.CHAIN_ILL_FORMED,
                    rule=str(FailClosedRule.CHAIN),
                    detail=(
                        f"link {index} declares kind {declared.kind.value!r} on "
                        f"the {route.value} route, whose squashing link is "
                        f"{expected.value!r}: the two routes run on DIFFERENT "
                        "channels (rem:tworoutes)"
                    ),
                )
            link = Link(
                stage=declared.stage,
                kind=declared.kind,
                source_family=current,
                target=target,
                channel_witness=instance.witness,
                carried_operator_pair=(
                    carried_labels,
                    pullback_labels if first else incoming,
                ),
                reachable_set_statement=squashing_reachable,
                constraint_entries=tuple(entries),
                licence=licence,  # type: ignore[arg-type]
                status=LinkStatus.EXACT,
                link_id=link_id,
            )
        elif declared.kind is LinkKind.PINCHING:
            link = Link(
                stage=declared.stage,
                kind=declared.kind,
                source_family=current,
                target=current,
                channel_witness=ChannelWitness(
                    identity=f"{link_id}:P_S",
                    equation="P_S of prop:pinching, P_S+ = P_S",
                    parameters=("the instance's sector set",),
                ),
                carried_operator_pair=(incoming, incoming),
                reachable_set_statement=(
                    "every reachable state is BLOCK DIAGONAL for the instance's "
                    "sector decomposition -- a sound constraint by "
                    "cor:blockdiag (ii)"
                ),
                constraint_entries=(),
                licence=None,
                status=LinkStatus.EXACT,
                link_id=link_id,
            )
        elif declared.kind is LinkKind.FLAGS_ENOUGH:
            # A genuine cor:flagsenough link, whose target replaces the base
            # block. It is BUILT, not special-cased, and (C1) then decides
            # whether it belongs in this chain.
            link = Link(
                stage=declared.stage,
                kind=declared.kind,
                source_family=current,
                target=SystemFamily(
                    description=(
                        "the same system with the zero-weight block replaced by "
                        "(1/|V|) 1 (eq:flagsenough)"
                    ),
                    dimension=current.dimension,
                    povm=None,
                ),
                channel_witness=ChannelWitness(
                    identity=f"{link_id}:flags-enough",
                    equation=(
                        "eq:flagsenough (measure-and-prepare into the flag block)"
                    ),
                ),
                carried_operator_pair=(carried_labels, carried_labels),
                reachable_set_statement=(
                    "every reachable state has ZERO WEIGHT in the base block"
                ),
                constraint_entries=(),
                licence=None,
                status=LinkStatus.EXACT,
                link_id=link_id,
            )
        elif declared.kind is LinkKind.FAMILY_DOMINATING:
            # THE DOMINATION LINK IS STATED AND EMITTED BY NO REQUIREMENT
            # (domination/def:domination-link; req:reserved-link-kinds): a
            # request that declares one names a link this module does not
            # build.
            return Refusal(
                reason=RefusalReason.CHAIN_ILL_FORMED,
                rule=str(FailClosedRule.CHAIN),
                detail=(
                    f"link {index} declares kind 'family-dominating'; the "
                    "domination link is stated by the domination submodule "
                    "and emitted by no requirement, so no link of that kind "
                    "is built"
                ),
            )
        else:  # pragma: no cover - rule_link_kind refuses these first
            return Refusal(
                reason=RefusalReason.CHAIN_ILL_FORMED,
                rule=str(FailClosedRule.CHAIN),
                detail=(
                    f"link {index} declares kind {declared.kind.value!r}, which "
                    "this version reserves and refuses; no link of that kind is "
                    "built"
                ),
            )
        links.append(link)
        current = link.target
        incoming = link.carried_operator_pair[0]

    if not links:
        return Refusal(
            reason=RefusalReason.CHAIN_ILL_FORMED,
            rule=str(FailClosedRule.CHAIN),
            detail=(
                "a chain has at least one link (def:chain, k >= 1); the identity "
                "link is RECORDED RATHER THAN OMITTED, because an empty chain "
                "would leave the artifact unable to say whether a reduction was "
                "performed and found trivial or never considered (ex:identity)"
            ),
        )
    if not links[-1].target.matches(target):
        return Refusal(
            reason=RefusalReason.CHAIN_ILL_FORMED,
            rule=str(FailClosedRule.CHAIN),
            detail=(
                "the declared chain's final target is not the emitted target, "
                "so the composite does not realize the artifact"
            ),
        )
    return Chain(links=tuple(links))


def _emission_record(
    normalized: Normalization,
    kappa: int,
    classes: Sequence[Label],
    entries: Sequence[ConstraintEntry],
    constant_rounding: Mapping[str, str],
    *,
    strict: bool,
    enclosed_references_used: bool,
) -> EmissionRecord:
    """Build the emitted ``emission_record`` (``req:emission-record``). ALWAYS PRESENT.

    The six condition outcomes are recorded as passes, and that is not an
    assertion made here: this function is reached only after the emitted-family
    row has DECIDED all six and not refused, "SINCE OTHERWISE THERE WOULD BE NO
    ARTIFACT".

    ``constant_rounding`` is the instance's per-entry record of
    ``cor:entries`` (iii): the direction a caller-declared constant off the
    lattice was rounded in, which ``thm:emit`` (iv) says "is recorded in
    ``emission_record``". Only an entry whose constant WAS rounded appears; an
    entry emitted at the constant its caller declared has no direction to
    record, and asserting one would be a record of something that did not
    happen. The emitted constant is carried beside the direction so that a
    reader sees both numbers without reading the entry back.
    """
    emitted = {entry.label: entry.constant for entry in entries}
    return EmissionRecord(
        lattice_exponent=kappa,
        constant_rounding_directions=tuple(
            (label, str(emitted.get(label, "")), direction)
            for label, direction in constant_rounding.items()
        ),
        six_condition_outcomes={
            "sector_map": True,
            "hermiticity": True,
            "positivity": True,
            "completeness": True,
            "declared_order_sum": True,
            "lattice_invariant": True,
        },
        blocks=tuple(
            BlockEmissionRecord(
                block_index=snap.block_index,
                already_on_lattice=snap.already_on_lattice,
                displacement=snap.displacement,
                displacement_squared=snap.displacement_squared,
                classes={label: snap.classes[label] for label in classes},
            )
            for snap in normalized.blocks
        ),
        strict_snaps=strict,
        enclosed_references_used=enclosed_references_used,
    )


#: The fixes ``req:emission-refusal`` names for a moved class a strict run
#: refuses at emission: declared numbers on which the construction stays on
#: the lattice; for a class snapped by the last resort (3), also the device's
#: noise. A reference handed beside the snap is no fix here: the companion
#: that would bypass the normalizer is missing because no claim establishes
#: (H-REF) for the instance, not for want of a reference.
_STRICT_FIX = (
    "declared numbers on which the exact construction stays on the lattice, "
    "so that the class is kept"
)
_STRICT_FIX_LAST_RESORT = (
    "; and a model that includes the device's loss and dark counts, so that "
    "the elements of the class are positive definite on the sector"
)


def _strict_refusal(
    normalized: Normalization, absence: NoReferenceCompanion
) -> str | None:
    """Return the strict option's refusal of the first moved class, or ``None``.

    ``req:emission-refusal``: where the run declares the strict option and no
    reference companion is formed beside the artefact, which with a moved
    class happens only where no claim of this module establishes (H-REF) for
    the instance (``req:reference-companion``), every moved class would rest
    on ``foundations/ass:snapped-measurement``, and the first is named with
    its data sector, its cause and the fix. The cause names the companion's
    own reason for being absent, so that the defensive absence
    (``CompanionAbsence.NOT_BUILT``) is not reported as a missing (H-REF)
    claim.
    """
    for index, snap in normalized.moved:
        last_resort = snap.support_not_preserved
        cause = "no reference companion bypasses the normalizer (" + (
            "no claim of this module establishes (H-REF) for the instance"
            if absence.reason is CompanionAbsence.NO_H_REF_CLAIM
            else f"{absence.reason}: {absence.detail}"
            if absence.detail
            else str(absence.reason)
        ) + ")"
        if last_resort:
            cause += (
                "; snapped by the last resort (3): a component of its residue "
                "has no host"
                if snap.component_without_host
                else "; snapped by the last resort (3): no weight of (2) gives a "
                "positive semidefinite family"
            )
        fix = _STRICT_FIX + (_STRICT_FIX_LAST_RESORT if last_resort else "")
        return (
            f"the strict option refuses the moved class {snap.label!r} at data "
            f"sector {index}: cause: {cause}; fix: {fix} (req:emission-refusal)"
        )
    return None


def receiver_row_omitted_on_provenance(call: ReductionCall) -> tuple[str, ...]:
    """Return the versions of the receiver artifact whose A-RECV row is omitted.

    Implements the decision of ``reductions/req:recv-row-provenance``: the
    artifact's version, once, where the row of ``ass:recv`` is omitted, and
    ``()`` where it is emitted. The emission records the result in
    ``receiver_row_omitted_on_provenance`` and drops the row exactly where it
    is non-empty (:func:`emitted_assumption_rows`).

    A REDUCTION INSTANCE READS ONE SUPPLIER ARTIFACT, ``call.artifact_rows``,
    so "for every supplier artifact it read" is that one. The row is omitted
    only where all of the following hold, and emitted wherever one fails:

    * (i), (iii) -- THE RUN'S WORD, never read from the artifact:
      ``call.receiver_provenance`` is passed and names the rows read, their
      imported part exactly (the declaration's own fields set aside;
      :meth:`~certiqs_key.reductions.provenance.ReceiverProvenance.names`).
      Only the run tier mints it, for an artifact it built and handed on as
      emitted, whose ledger its record carries
      (:func:`certiqs_key.runs.receiver_provenance.attest_receiver_provenance`).
    * (ii) -- DECIDED HERE, ON THE ARTIFACT: its declared version is the one
      the installed receiver module states for the artifacts it emits, and it
      passes ``req:supplier-version-accepted`` and
      ``req:supplier-ledger-refusals``
      (:func:`~certiqs_key.reductions.validation.rule_receiver_spec`, against
      the caller's ``accepted_receiver_versions``).
    * (iv) -- DECIDED HERE, ON THE ARTIFACT: its exact-route record says its
      declaration has a model admissible exactly
      (``receiver/req:exact-route-decision`` (iv);
      :attr:`~certiqs_key.reductions.inputs.ReceiverArtifactRows.exact_model_admissible`),
      and its ``bound_evaluation`` is ``rigorous``
      (``receiver/req:evaluation-label``), every per-setting weight formed by
      the rigorous evaluation of ``receiver/req:rigorous-weight``. A weight
      evaluated in floating point -- A-EIG's case among them -- and a
      declaration admitted only within the receiver tolerances keep the row.

    THE IMPORT IS FUNCTION-LOCAL AND POINTS DOWNWARD, for the reason
    :func:`~certiqs_key.reductions.validation.required_receiver_keys` gives:
    the installed receiver's version and its evaluation label are the
    receiver's own vocabulary, read where the decision is taken.
    """
    provenance = call.receiver_provenance
    rows = call.artifact_rows
    if provenance is None or not provenance.names(rows):
        return ()
    from certiqs_key.receiver.artifact import (
        BOUND_EVALUATIONS,
        MATHEMATICAL_SPEC_VERSION,
    )

    if rows.mathematical_spec_version != MATHEMATICAL_SPEC_VERSION:
        return ()
    if rule_receiver_spec(rows, call.request.accepted_receiver_versions) is not None:
        return ()
    if not rows.exact_model_admissible or rows.bound_evaluation != BOUND_EVALUATIONS[0]:
        return ()
    return (rows.mathematical_spec_version,)


def emitted_assumption_rows(
    chain: Chain,
    *,
    rests_on_a_snap: bool = False,
    emits_constraints: bool = True,
    settings: Sequence[Label] | None = None,
    public_choice_applied: bool | None = None,
    receiver_row_omitted: bool = False,
) -> tuple[AssumptionRow, ...]:
    """Return the core rows THIS emission carries, in the ledger's order.

    SIX CONDITIONAL ROWS, AND THIS IS THE ONE PLACE THEIR CONDITIONS ARE
    READ, because this is where the data they are about live -- the emitted
    chain, the emitted constraint list, the declared setting set, what the
    caller says of a public choice at the station, the emission record, the
    declaring party's snap record, and the decision on the receiver
    artifact's provenance. Every other row is unconditional:
    every emission rests on it whatever it emits, and a ledger that dropped
    one would understate what the artifact rests on.

    A-RECV (``ass:recv``) is present on every emission save where
    ``receiver_row_omitted``: :func:`receiver_row_omitted_on_provenance` found
    the receiver artifact read to be one the run attests it built, exact and
    rigorously evaluated (``req:recv-row-provenance``), where both clauses of
    ``ass:recv`` hold by the receiver's theorems under its own ledger, which
    the run's record carries. The default keeps the row, the safe direction
    for a caller that does not say.

    A-PROBE (``ass:probe``) is present exactly where ``settings`` has at least
    two values, and A-TSM (``ass:tsm``) where it does or where a public choice
    is applied at the measurement the emitted family describes
    (``public_choice_applied``), the row being emitted where the caller does
    not say (``None``) (``req:assumption-ledger``: at ``T = {*}`` with no choice their
    clauses hold vacuously). ``settings`` ``None`` keeps both rows, the safe direction
    for a caller that does not say.

    A-CONST (``ass:constdecl``) is present exactly where ``emits_constraints``:
    the emitted constraint list is non-empty. Its statement is a condition on
    the constants of emitted entries and holds vacuously of an empty list
    (``req:assumption-ledger``), so the encoded route, which emits none, does not rest
    on it. The default keeps the row, the safe direction for a caller that does not
    say.

    A-SNAP, foundations' ``ass:snapped-measurement``, is present exactly where
    ``rests_on_a_snap``: the emission record names a data sector with a moved
    class, or the declaring party's snap record a moved block, as resting on
    it, provisionally (``thm:emit`` (vi); ``req:emission-record``); the run's
    record decides which rest.

    THE SOUNDNESS OF THE EMITTED ENTRIES IS NO ROW. It is a conclusion of
    ``thm:chain``, ``cor:entries`` and ``thm:licence``
    (``rem:sound-and-atk``), and the engine inherits no row for it.

    A-SRC is the transmitter's source-replacement attestation, which
    ``lem:source-transfer`` reads through ``transmitter/thm:certificate-sufficiency``
    (iii), and it is present "whenever the emitted chain's source segment is NON-EMPTY"
    (``assumption_ledger.assumed_from_another_module``) -- the chain object this
    emission carries, not a datum any rule re-derives. EVERY ARTEFACT EMITTED
    TODAY HAS AN EMPTY SEGMENT, so the row is absent from every one of them;
    naming it there would tell a consumer that the transmitter owes a
    source-replacement attestation for a replacement nothing in the artefact
    performed.

    A-SEQ, the other row this ledger assumes from that module, is
    UNCONDITIONAL: ``def:protocol`` declares it and does not read how many
    parties measure, and with one measuring party the key is the assumption it
    always was. There is no row for the adversary's registers: ``lem:sep``
    reads them as finite-dimensional, which is the round model's, and the
    engine lifts the run's security statement to an adversary of any memory
    (``meat-core/lem:memory-lift``).
    """
    source_segment_is_empty = not chain.source_segment
    private_setting = settings is None or len(settings) >= 2
    setting_or_choice = private_setting or public_choice_applied is not False
    core = tuple(
        row
        for row in CORE_ASSUMPTIONS
        if not (
            not private_setting
            and row.identifier in PRESENT_ONLY_WITH_A_PRIVATE_SETTING
        )
        and not (
            not setting_or_choice
            and row.identifier in PRESENT_ONLY_WITH_A_SETTING_OR_A_CHOICE
        )
        and not (
            source_segment_is_empty
            and row.identifier in PRESENT_ONLY_WITH_A_NON_EMPTY_SOURCE_SEGMENT
        )
        and not (
            not emits_constraints
            and row.identifier in PRESENT_ONLY_WITH_A_NON_EMPTY_CONSTRAINT_LIST
        )
        and not (
            receiver_row_omitted and row.identifier in OMITTED_ON_RECEIVER_PROVENANCE
        )
    )
    return (*core, SNAPPED_MEASUREMENT_ROW) if rests_on_a_snap else core


def _snap_resting(
    emission_record: EmissionRecord, instance_snap: InstanceSnapRecord | None
) -> tuple[str, ...]:
    """Return the blocks the artefact names as resting on A-SNAP, provisionally.

    The emission record's data sectors with a moved class
    (``req:emission-record``) and the declaring party's moved blocks
    (``foundations/req:who-snaps``), each once, in that order. Which of them
    rest is the run's decision after its search (``thm:emit`` (vi)).
    """
    names = [
        f"emission: data sector {index} ({detail})"
        for index, detail in emission_record.moved_sectors
    ]
    for block in () if instance_snap is None else instance_snap.moved:
        detail = "reference handed" if block.handed else str(block.cause)
        names.append(f"instance_snap: {block.name} ({detail})")
    return tuple(dict.fromkeys(names))


def _emit(
    request: ReductionCall,
    instance: ReductionInstance,
    entries: Sequence[ConstraintEntry],
    licence: object | None,
    chain: Chain,
    route: Route,
    report: VerificationReport,
    emission_record: EmissionRecord,
) -> ProofReductionArtifact:
    """Assemble the emitted keys. Nothing here validates; validation is done."""
    order = request.declaration.joint_alphabet
    ledger_rows: Mapping[str, tuple[tuple[str, object], ...]] = instance.ledger_rows
    # The declared rows under their presence rules: A-SRC is read off the
    # chain, A-CONST off the emitted constraint list, A-SNAP off the emission
    # record and the declaring party's snap record
    # (emitted_assumption_rows), a submodule's rows off its instance.
    resting = _snap_resting(emission_record, request.artifact_rows.instance_snap)
    if resting:
        ledger_rows = {
            **ledger_rows,
            SNAPPED_MEASUREMENT_ROW.identifier: (("resting_blocks", resting),),
        }
    # req:recv-row-provenance: the A-RECV row is omitted, and the omission
    # recorded with the artifact's version, only where the run attests it
    # built the receiver artifact and the artifact is exact and rigorous.
    omitted = receiver_row_omitted_on_provenance(request)
    rows: tuple[AssumptionRow, ...] = (
        emitted_assumption_rows(
            chain,
            rests_on_a_snap=bool(resting),
            emits_constraints=bool(entries),
            settings=request.declaration.probe_declaration.settings,
            public_choice_applied=request.public_choice_applied,
            receiver_row_omitted=bool(omitted),
        )
        + instance.extra_assumptions
    )
    return ProofReductionArtifact(
        source_descriptor=instance.source_descriptor,
        target_descriptor=instance.target_descriptor,
        target_povm={
            outcome: instance.target_povm[index] for index, outcome in enumerate(order)
        },
        outcome_correspondence={outcome: outcome for outcome in order},
        squashing_channel=instance.witness,
        exact_identity=instance.exact_identity,
        transported_operators=tuple(instance.transported),
        reachable_set_statement=instance.reachable_set_statement,
        constraint_list=tuple(entries),
        attack_set_license=licence,  # type: ignore[arg-type]
        wpfss_data=instance.weight_record,
        reduction_chain=chain,
        verification_report=report,
        assumption_ledger=assumption_ledger(
            ledger_rows,
            request.artifact_rows.mathematical_spec_version,
            request.artifact_rows.inherited_assumption_ledger,
            rows,
        ),
        emission_record=emission_record,
        route=route,
        receiver_row_omitted_on_provenance=omitted,
    )
