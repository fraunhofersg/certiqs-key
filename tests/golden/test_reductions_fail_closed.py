"""Section ``sec:failclosed``: ALL TWENTY-SEVEN reasons, PRODUCED BY THE CODE.

The frozen 0.1.3 registry carries twenty-six ``RefusalCase`` entries over
twenty-four reason strings and twenty-one rows; 0.2.0 adds TWO STRINGS and
THREE ROWS, and 0.3.0 adds ONE OF EACH. This file builds, for each case, the
DECLARED DATUM the case names, runs the rule that decides it, and asserts the
reason the code emits is the frozen one. The union over the cases is then
asserted to be the whole 0.3.0 set -- so a twenty-eighth string cannot appear on
either side, and a missing one cannot pass unnoticed.

WHAT 0.3.0 ADDS HERE
====================
ONE BUILDER, for ``dark_counts_not_column_stochastic``. The row's own group of
cases -- the five frozen declarations of ``COLSTOCH_CASES``, the boundary
against the descent row, and the end-to-end reachability of the residue the row
exists for -- lives in ``test_reductions_column_stochastic.py``, because
those are statements about ONE row and this file's subject is the TOTALITY of
the vocabulary. What this file adds is that the new string is PRODUCED, and that
producing it does not disturb the count on either side.

"Every rule below is DECIDED FROM DECLARED DATA BEFORE ANYTHING IS EMITTED; a
failure produces a refusal with a machine-readable reason and NO ARTIFACT."

THE SUPERSEDED BLOCK-STRUCTURE CASE
===================================
``REFUSAL_CASES`` is marked ``superseded`` through its case ``R-block-structure``
(kind: INPUT SHAPE, and the only mark in the freeze whose
``still_valid_at_zero_tolerance`` is FALSE). Its declared datum is
"``M_{a|nb}`` with a non-zero (0,1) entry", an element of the ``nb`` branch WITH
COHERENCE BETWEEN THE m = 0 BLOCK AND THE ABOVE-CUTOFF ONE, and A DECLARATION
CANNOT PRESENT THAT AT 0.2.0 AT ALL: Section 4.14 restates the row as the
structural half and says why -- "the datum is a per-m list (Section 2.1), SO
THERE IS NO OFF-BLOCK ENTRY TO TEST". An inter-block coherence has no slot in a
per-m list of blocks.

THE CASE IS THEREFORE SUPERSEDED: its builder declares what the row does
refuse -- a MISSING block, which is one of the four things the row's own text
names -- and the numerical half belongs to the tolerance row, whose cases are
``TOL_ROW_CASES`` and ``TOL-scope-receiver-block-admit`` (the mark's named
replacements). This repository carries no tolerance at all, so they are not
replayed.

``REFUSAL_REASONS`` is marked ``superseded`` (kind: vocabulary) and is replaced
by ``REFUSAL_REASONS_0_2_0``: 26 strings over 24 rows, the 24 a subset of the
26, "NONE REMOVED, AND NONE INVENTED WHERE AN EXISTING ONE CARRIES THE REFUSAL".
Two builders are added for the two new strings.
"""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

import pytest
from reductions_support import (
    RECEIVER_LEDGER_KEYS,
    flat_call,
)
from registry_reductions import (
    BLK_GT_V0,
    BLK_GT_V1,
    CONSUMER_STRINGS_NOT_OURS_0_3_0,
    FAIL_CLOSED_ROW_COUNT_0_2_0,
    FAIL_CLOSED_ROW_COUNT_0_3_0,
    FAIL_CLOSED_ROW_COUNT_1_0_0,
    FAIL_CLOSED_ROWS_ADDED_0_2_0,
    FAIL_CLOSED_ROWS_ADDED_0_3_0,
    FAIL_CLOSED_ROWS_ADDED_1_0_0,
    FAIL_CLOSED_ROWS_REPLACED_1_0_0,
    REFUSAL_CASES,
    REFUSAL_REASONS,
    REFUSAL_REASONS_0_2_0,
    REFUSAL_REASONS_0_3_0,
    REFUSAL_REASONS_1_0_0,
    REFUSAL_REASONS_ADDED_1_0_0,
    REFUSAL_REASONS_REMOVED_1_0_0,
    SUPERSESSIONS,
    SUPERSESSIONS_0_3_0,
    WP3_FFSS_V0,
    WP3_FWP_V0,
    WP3_FWP_V1,
    WP3_M_V0,
    WP3_M_V1,
)

from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    diagonal,
    identity,
    matrix,
    scale,
    subtract,
)
from certiqs_key.reductions.channels import (
    ChannelWitness,
    split_blocks,
)
from certiqs_key.reductions.constraints import (
    ConstraintEntry,
)
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    CarriedOperatorRequest,
    ChannelGrading,
    CoarseGraining,
    ConstraintForm,
    DarkCountChannel,
    HighPhotonBound,
    InheritedAssumption,
    LinkDeclaration,
    ProbeDeclaration,
    ReceiverArtifactRows,
    canonical_coarse_graining,
    patterns,
    product_form_dark_counts,
)
from certiqs_key.reductions.links import Chain, Link, SystemFamily, identity_link
from certiqs_key.reductions.reasons import (
    CertificateKind,
    FailClosedRule,
    LinkKind,
    LinkStage,
    LinkStatus,
    Refusal,
    RefusalReason,
    Relation,
    Route,
    SourceMode,
    fail_closed_rules,
)
from certiqs_key.reductions.validation import (
    RULE_ORDER,
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
from certiqs_key.reductions.wpfss import reduce_flat
from certiqs_key.reductions.wpfss.construction import (
    flat_sectors,
    fss_instance_entry,
    fss_target,
    transported_cutoff_projectors,
    wp_adjoint,
    wpfss_target,
)
from certiqs_key.reductions.wpfss.validation import (
    WPFSS_ROWS,
    rule_absorbing,
    rule_column_stochastic,
    rule_descent,
    rule_fibre,
    rule_high_photon_slot,
    rule_total_weight,
)
from certiqs_key.reductions.wpfss.validation import (
    FailClosedRule as WpfssRule,
)
from certiqs_key.reductions.wpfss.weights import (
    BoundedLetter,
    descend,
)

#: ONE FROZEN ROW IS A REMOVABLE SUBMODULE'S. The frozen table of refusal
#: cases has one row per fail-closed row, and one of them,
#: :data:`REMOVABLE_CASE`, belongs to a submodule that may be deleted. Its case
#: is replayed, exactly as the freeze has it, in that submodule's own test
#: file; this file replays every other case and counts the vocabulary without
#: that row's string, which holds whether or not the submodule is in the tree.
REMOVABLE_CASE = "R-blinding-model"

F = Fraction
# The fixture's receiver version is the receiver's accepted one, which STATES
# the per-setting weights; the wpfss slot row refuses an artifact of a
# version that does not (req:supplier-version). Fixture data, not an oracle
# value.
ACCEPTED = ("receiver@0.9.0",)


def m(frozen: object) -> Matrix:
    """Convert a frozen registry matrix into the module's representation."""
    rows = frozen  # type: ignore[assignment]
    return matrix([[Cx(entry[0], entry[1]) for entry in row] for row in rows])  # type: ignore[index,union-attr]


def _artifact(**overrides: object) -> ReceiverArtifactRows:
    """Return a well-formed receiver-artifact declaration, mutated per case."""
    coarse = canonical_coarse_graining(
        2,
        empty_letter="y_empty",
        single_letters={1: "y_1", 2: "y_2"},
        multiclick_letter="y_mc",
    )
    letters = coarse.letters
    settings = ("t_off", "t_on")
    blocks = {
        (letter, setting): (matrix([[F(1, 4)]]),)
        for letter in letters
        for setting in settings
    }
    defaults: dict[str, object] = {
        "mathematical_spec_version": "receiver@0.9.0",
        "detection_alphabet": letters,
        "photon_blocks": blocks,
        "high_photon_bounds": (
            HighPhotonBound.uniform(coarse.fibre("y_mc"), F(1, 10), settings),
        ),
        "bound_quantifier_domain": BoundQuantifierDomain(cutoff=0, settings=settings),
        "dark_count_channel": product_form_dark_counts(2, {1: F(1, 5), 2: F(1, 4)}),
        "outcome_coarse_graining": coarse,
        "bound_evaluation": "floating_point",
        "channel_grading": ChannelGrading(block_dimensions=(1,)),
        "validation_results_present": True,
        "declared_device_family": (),
        "occupation_basis_order": (),
        # The supplier's machine keys, read from the receiver artifact's
        # ledger in the supplier's order (the frozen oracle, band 4); a case
        # that drops one is refused by the receiver-spec row.
        "inherited_assumption_ledger": _supplier_ledger(),
    }
    defaults.update(overrides)
    return ReceiverArtifactRows(**defaults)  # type: ignore[arg-type]


def _supplier_ledger(*, without: str | None = None) -> tuple[InheritedAssumption, ...]:
    """Return the supplier ledger rows, optionally missing one key."""
    return tuple(
        InheritedAssumption(machine_key=key)
        for key in RECEIVER_LEDGER_KEYS
        if key != without
    )


def _probe() -> ProbeDeclaration:
    return ProbeDeclaration(
        settings=("t_off", "t_on"), weights={"t_off": F(2, 3), "t_on": F(1, 3)}
    )


#: A LINK FAMILY'S POVM IS A LIST OF SECTOR-BLOCK LISTS, so these fixtures wrap each
#: frozen 3x3 element as a
#: ONE-BLOCK list: the frozen values are as frozen, every entry is still
#: compared by (C1), and the fixture declares no sector split it does not have.
def _one_block(*elements: Matrix) -> tuple[tuple[Matrix, ...], ...]:
    """Return a family as one block per element, the whole space being one block."""
    return tuple((element,) for element in elements)


def _wp_family() -> SystemFamily:
    return SystemFamily(
        description="Q = H(B_<=N) (+) H(flag) = C^3",
        dimension=3,
        povm=_one_block(m(WP3_FWP_V0), m(WP3_FWP_V1)),
    )


def _fss_family() -> SystemFamily:
    return SystemFamily(
        description="Q = H(B_<=N) (+) H(flag) = C^3",
        dimension=3,
        povm=_one_block(*fss_target((matrix([[F(2, 3)]]), matrix([[F(1, 3)]])))),
    )


def _physical_family() -> SystemFamily:
    return SystemFamily(
        description="B = C^3 with the cutoff split (1, 2)",
        dimension=3,
        povm=_one_block(m(WP3_M_V0), m(WP3_M_V1)),
    )


def _link(
    source: SystemFamily,
    target: SystemFamily,
    *,
    stage: LinkStage = LinkStage.RECEIVER,
    kind: LinkKind = LinkKind.WPFSS,
    carried_out: tuple[str, ...] = ("Pi_leq", "Pi_flag"),
    carried_in: tuple[str, ...] = ("Pi_leq", "Pi_gt"),
    link_id: str = "L",
) -> Link:
    return Link(
        stage=stage,
        kind=kind,
        source_family=source,
        target=target,
        channel_witness=ChannelWitness(identity=f"{link_id}:Lambda", equation="eq:Lwp"),
        carried_operator_pair=(carried_out, carried_in),
        reachable_set_statement="def:sound for this link's channel",
        constraint_entries=(),
        licence=None,
        status=LinkStatus.EXACT,
        link_id=link_id,
    )


#: The flat sector map of the WP3 fixture: one preserved data sector and the
#: two flag sectors, which is what an entry's SECTOR-BLOCK LIST is read against
#: (spec/architecture.md 2.8-2.9).
WP3_SECTORS = flat_sectors([1], ["v0", "v1"])


def _blocks(operator: Matrix) -> tuple[Matrix, ...]:
    """Return an operator as the sector-block list of :data:`WP3_SECTORS`."""
    return tuple(split_blocks(operator, list(WP3_SECTORS.dimensions)))


def _entry(mode: SourceMode = SourceMode.TRUSTED) -> ConstraintEntry:
    return fss_instance_entry(
        _blocks(m(WP3_FFSS_V0)),
        WP3_SECTORS,
        preserved_dim=1,
        alphabet_size=2,
        weight=F(1, 4),
        label="O^ = F^FSS_v0 - (1/4) Pi_flag",
        certified_against="Lambda-FSS",
        mode=mode,
    )


#: THE ONE RENAMED STRING, AND THE ONE OWNED BY A SUBMODULE. The frozen registry
#: is never regenerated, so it still carries
#: ``requested_assurance_shelved``; the row's subject is not a shelving but
#: a tier that is not one of the live ones, and the string it emits is
#: ``requested_assurance_unknown``. :data:`REMOVABLE_OWNED` is the removable
#: submodule's own string, spanned only where its row is reported.
FROZEN_TO_EMITTED = {"requested_assurance_shelved": "requested_assurance_unknown"}
REMOVABLE_OWNED = {"blinding_model_ill_formed"}


def emitted_spelling(frozen: str) -> str:
    """Return the string the code emits where the freeze carries ``frozen``."""
    return FROZEN_TO_EMITTED.get(frozen, frozen)


def emitted_vocabulary(frozen: object) -> set[str]:
    """Return a frozen vocabulary as the code spells it, the removable string aside."""
    return {emitted_spelling(item) for item in frozen} - REMOVABLE_OWNED


# ---------------------------------------------------------------------------
#  One builder per frozen refusal case: the declared datum, and the rule.
# ---------------------------------------------------------------------------


def _case_receiver_draft() -> Refusal | None:
    return rule_receiver_spec(
        _artifact(mathematical_spec_version="receiver-povm@0.1.3-draft"), ACCEPTED
    )


def _case_cutoff() -> Refusal | None:
    artifact = _artifact(
        bound_quantifier_domain=BoundQuantifierDomain(
            cutoff=2, settings=("t_off", "t_on")
        ),
        channel_grading=ChannelGrading(block_dimensions=(1, 1, 1)),
    )
    return rule_cutoff(1, artifact)


def _case_block_structure() -> Refusal | None:
    """R-block-structure, RETIRED AND REWRITTEN AT 0.2.0.

    The 0.1.3 datum -- an ``nb``-branch element with coherence across the
    cutoff -- CANNOT BE DECLARED at 0.2.0, the declared type being a per-``m``
    list with no slot for an inter-block entry. What the restated row refuses is
    a block that is MISSING, MIS-DIMENSIONED, or over the wrong alphabet or
    order; a MISSING block is declared here. Replacement cases for the numerical
    half the row shed: ``TOL_ROW_CASES``, ``TOL-scope-receiver-block-admit``.
    """
    artifact = _artifact()
    blocks = dict(artifact.photon_blocks)
    del blocks[("y_mc", "t_on")]
    return rule_block_structure_from_blocks(
        blocks,
        artifact.channel_grading,
        artifact.detection_alphabet,
        artifact.bound_quantifier_domain.settings,
    )


def _case_declaration_not_exactly_admissible() -> Refusal | None:
    """Refuse under the exact-admissibility row: a block that is not positive.

    The declared block has a NEGATIVE entry, so ``A >= 0`` fails and
    Eq. ``eq:psdtest`` refuses it exactly. There is no window: the row decides
    FIVE CONJUNCTS AT ZERO, with no caller-declared tolerance, and THE REFUSAL NAMES
    WHICH ONE FAILED.
    """
    artifact = _artifact()
    blocks = dict(artifact.photon_blocks)
    blocks[("y_mc", "t_on")] = (matrix([[F(-1, 4)]]),)
    return rule_exact_admissibility(
        blocks,
        artifact.channel_grading,
        artifact.detection_alphabet,
        artifact.bound_quantifier_domain.settings,
        lattice_exponent=4,
    ).refusal


def _case_lattice_exponent_not_declared() -> Refusal | None:
    """Refuse under the row that RUNS FIRST: no declared ``kappa``.

    FIRST IN THE SECTION. The lattice condition (D-LAT) gives the exponent
    "NO DEFAULT AND NO FALLBACK", and "a defaulted lattice would decide a
    security-relevant predicate ON
    NOBODY'S AUTHORITY".
    """
    return rule_lattice_exponent(None, alphabet_sizes={"V": 2, "Y": 2, "T": 1})


def _case_lattice_exponent_accumulation() -> Refusal | None:
    """Refuse the second inequality of the row UNDER THE SAME REASON.

    Eq. ``eq:latsumcond``: ``kappa + ceil(log2 max{|V|, |Y|, |T|}) <= 53``,
    "REFUSED UNDER THE SAME REASON". At ``kappa = 53`` any alphabet of two or
    more outcomes breaks it, and it is the condition Lemma ``lem:latsum`` needs
    to make ``def:exactadm`` (e) satisfiable rather than refusing every family.
    """
    return rule_lattice_exponent(53, alphabet_sizes={"V": 4, "Y": 2, "T": 2})


def _case_requested_assurance_unknown() -> Refusal | None:
    """Refuse a request naming a rung the live ladder does not have.

    spec/architecture.md 2.8 has EXACTLY TWO LIVE RUNGS and PRINCIPLES.md
    section 10 drops the third entirely, so the row's subject is a value
    outside the ladder rather than a named shelved one. "REFUSED RATHER THAN
    DEMOTED, a silent demotion being a caller receiving a weaker claim than it
    asked for without being told."

    THE DROPPED LABEL IS NOT WRITTEN HERE EITHER. The row is a membership test
    in the two live rungs, so the case is built from a value that is simply not
    one of them. Spelling the dropped string in a test would put back the
    writer the platform rule keeps out of this package.
    """
    return rule_requested_assurance(
        "a rung this ladder does not have", live_rungs=("estimate", "first-order")
    )


def _case_emitted_family_not_admissible() -> Refusal | None:
    """Refuse under THE SECOND GATE: the family this module is about to emit.

    The only row of Section 4.14 whose subject is not
    declared data. The frozen case names a step (4), a positivity ladder that
    could not restore positivity, and there is no such ladder or lift. The
    refusal of a class that can occur under ``def:emitnorm`` is the strict
    option's refusal of a moved class where no reference companion bypasses
    the normalizer (``req:emission-refusal``), which is what this builds; the
    row and its string are the frozen ones.
    """
    return rule_emitted_family(
        {},
        (),
        (),
        lattice_exponent=4,
        sector_map_agrees=True,
        strict_refusal=(
            "the strict option refuses the moved class 't0' at data sector 0: "
            "cause: no reference companion bypasses the normalizer"
        ),
    )


def _case_high_photon_slot() -> Refusal | None:
    """Refuse under the slot row: a NEGATIVE declared slot weight.

    ``p_i < 0`` contradicts the supplier's own slot guarantee (Assumption
    A-RECV) and is refused rather than consumed. The total-weight row cannot see
    it wherever ``r_min,i > 0``.
    """
    coarse = canonical_coarse_graining(
        2,
        empty_letter="y_empty",
        single_letters={1: "y_1", 2: "y_2"},
        multiclick_letter="y_mc",
    )
    settings = ("t_off", "t_on")
    return rule_high_photon_slot(
        (HighPhotonBound.uniform(coarse.fibre("y_mc"), F(-1, 10), settings),),
        settings,
        "receiver@0.9.0",
    )


def _case_licensed_hermiticity() -> Refusal | None:
    """Refuse under the licensed-route Hermiticity row, NEW AT 0.2.0.

    It carries the EXISTING ``constraint_without_certificate``.

    ON THE ``licensed`` ROUTE, UNCONDITIONALLY AT 1.0.0 -- the ``eps_op > 0``
    scope is gone with the tolerance. Definition ``def:licensed`` and Corollary
    ``cor:pullback`` "COMPARE A REAL CONSTANT WITH ``tr[O^ sigma]``, WHICH IS
    NOT A REAL NUMBER UNLESS ``O^ = O^-dagger``", and ``fail_closed`` forbids
    symmetrizing one, so the row refuses instead.
    """
    entry = ConstraintEntry(
        label="a non-Hermitian O^",
        # ONE SECTOR BLOCK, and the row decides Hermiticity per block: an entry
        # is its block list.
        operator=(matrix([[F(0), F(1)], [F(0), F(0)]]),),
        relation=Relation.GE,
        constant=F(0),
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against="Lambda-FSS",
        theta_typing="c_k in R (untrusted-source mode): a real number",
    )
    return rule_licensed_hermiticity((entry,), Route.LICENSED, lattice_exponent=4)


def _case_fibre_split() -> Refusal | None:
    # cg SPLITS the multiclick set across two letters, so no letter's fibre is
    # the bounded set: neither piece inherits a bound.
    assignment = {}
    letters = ("y_empty", "y_1", "y_2", "y_mc_a", "y_mc_b")
    for pattern in patterns(3):
        if len(pattern) == 0:
            assignment[pattern] = "y_empty"
        elif len(pattern) == 1:
            assignment[pattern] = "y_1" if 1 in pattern else "y_2"
        else:
            assignment[pattern] = "y_mc_a" if 1 in pattern else "y_mc_b"
    coarse = CoarseGraining(ports=3, letters=letters, assignment=assignment)
    multiclick = frozenset(pattern for pattern in patterns(3) if len(pattern) >= 2)
    return rule_fibre(
        (HighPhotonBound.uniform(multiclick, F(1, 10), ("off",)),), coarse
    )


def _case_descent() -> Refusal | None:
    channel = product_form_dark_counts(4, dict.fromkeys((1, 2, 3, 4), F(1, 3)))
    fibre_of_y_a = {
        frozenset({1, 2}),
        frozenset({1, 2, 4}),
        frozenset({1, 2, 3, 4}),
    }
    assignment = {}
    letters: list[str] = []
    for pattern in patterns(4):
        if len(pattern) >= 2:
            letter = "y_a" if pattern in fibre_of_y_a else "y_b"
        else:
            letter = "y_" + "".join(str(port) for port in sorted(pattern))
        assignment[pattern] = letter
        if letter not in letters:
            letters.append(letter)
    coarse = CoarseGraining(ports=4, letters=tuple(letters), assignment=assignment)
    return rule_descent(channel, coarse)


def _case_absorbing() -> Refusal | None:
    channel = product_form_dark_counts(2, {1: F(0), 2: F(1, 4)})
    coarse = canonical_coarse_graining(
        2,
        empty_letter="y_empty",
        single_letters={1: "y_1", 2: "y_2"},
        multiclick_letter="y_mc",
    )
    descended = descend(channel, coarse)
    assert descended is not None
    return rule_absorbing(
        (
            BoundedLetter(
                letter="y_1",
                weights=(("off", F(1, 5)),),
                absorbing=descended.is_absorbing_at("y_1"),
                r_min=F(0),
            ),
        )
    )


def _case_total_weight() -> Refusal | None:
    return rule_total_weight((F(1), F(0)))


def _case_probe_weights() -> Refusal | None:
    bad_sum = ProbeDeclaration(
        settings=("t0", "t1"), weights={"t0": F(2, 3), "t1": F(1, 2)}
    )
    zero_weight = ProbeDeclaration(
        settings=("t0", "t1"), weights={"t0": F(1), "t1": F(0)}
    )
    # BOTH violations are refused, and they fail different things.
    assert rule_probe_weights(zero_weight) is not None
    return rule_probe_weights(bad_sum)


def _case_relation_impossible() -> Refusal | None:
    physical = [diagonal([F(1), F(0)]), diagonal([F(0), F(1)])]
    target = [scale(F(1, 2), identity(2)), scale(F(1, 2), identity(2))]
    span_leg = rule_obstructions(physical, target)
    assert span_leg is not None
    # And the norm leg on the reverse relation F^FSS <= F^WP.
    preserved = (matrix([[F(1, 2)]]), matrix([[F(1, 2)]]))
    fss = fss_target(preserved)
    wp = wpfss_target(preserved, (F(1, 2), F(0)))
    return rule_obstructions(list(fss), list(wp))


def _case_chain_not_composable() -> Refusal | None:
    first = _link(_physical_family(), _wp_family(), link_id="L1")
    second = _link(_fss_family(), _fss_family(), kind=LinkKind.PINCHING, link_id="L2")
    return rule_chain(Chain(links=(first, second)))


def _case_chain_not_tuple_chained() -> Refusal | None:
    first = _link(
        _physical_family(), _wp_family(), carried_out=("Pi_leq",), link_id="L1"
    )
    second = _link(
        _wp_family(),
        _wp_family(),
        kind=LinkKind.PINCHING,
        carried_in=("Pi_flag",),
        link_id="L2",
    )
    return rule_chain(Chain(links=(first, second)))


def _case_stage_order() -> Refusal | None:
    receiver = identity_link(_physical_family(), link_id="L1")
    source = _link(
        _physical_family(),
        _physical_family(),
        stage=LinkStage.SOURCE,
        kind=LinkKind.IDENTITY,
        carried_out=(),
        carried_in=(),
        link_id="L2",
    )
    return rule_chain(Chain(links=(receiver, source)))


def _case_kind(kind: LinkKind) -> Callable[[], Refusal | None]:
    def build() -> Refusal | None:
        return rule_link_kind((LinkDeclaration(stage=LinkStage.RECEIVER, kind=kind),))

    return build


def _case_approximate() -> Refusal | None:
    return rule_approximate(
        (
            LinkDeclaration(
                stage=LinkStage.RECEIVER,
                kind=LinkKind.FSS,
                requested_status="certified_outer",
            ),
        )
    )


def _case_device_family() -> Refusal | None:
    return rule_device_family(_artifact(declared_device_family=("xi_1", "xi_2")))


def _case_no_certificate() -> Refusal | None:
    # The entry O^ = F^FSS_v0 - (1/2) Pi_flag, where the declared weight is 1/4.
    _, pi_flag = transported_cutoff_projectors(1, 2)
    operator = subtract(m(WP3_FFSS_V0), scale(F(1, 2), pi_flag))
    entry = ConstraintEntry(
        label="overclaimed",
        operator=_blocks(operator),
        relation=Relation.GE,
        constant=F(0),
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against="Lambda-FSS",
        theta_typing="Theta = c = 0",
    )
    pullback = wp_adjoint(operator, 1, (m(BLK_GT_V0), m(BLK_GT_V1)))
    return rule_constraint_certificate([entry], {"overclaimed": pullback})


def _case_data_dependent() -> Refusal | None:
    entry = ConstraintEntry(
        label="observed frequency of v0 in this run",
        operator=_blocks(m(WP3_FFSS_V0)),
        relation=Relation.GE,
        constant=F(1, 3),
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against="Lambda-FSS",
        theta_typing="Theta = c = 1/3",
        constant_is_declared=False,
    )
    return rule_constraint_certificate([entry], {entry.label: identity(3)})


def _case_licence_missing() -> Refusal | None:
    return rule_licence_presence([_entry()], licence_present=False)


def _case_licence_without_constraints() -> Refusal | None:
    return rule_licence_presence([], licence_present=True)


def _case_route_both() -> Refusal | None:
    return rule_route("both")


def _case_channel_mismatch() -> Refusal | None:
    return rule_constraint_channel([_entry()], "Lambda-WP")


def _case_alphabet_order() -> Refusal | None:
    artifact = _artifact()
    permuted = ("y_1", "y_empty", "y_2", "y_mc")
    probe = _probe()
    joint = tuple(
        (letter, setting) for setting in probe.settings for letter in permuted
    )
    return rule_alphabet_order(artifact, permuted, probe, joint)


def _case_post_processing_order() -> Refusal | None:
    return rule_post_processing_order(squash_first=True)


def _case_unsound_transplant() -> Refusal | None:
    request = CarriedOperatorRequest(
        label="sum_y F_(y,t0) = q_t0 1_Q",
        operator=identity(3),
        relation=Relation.EQ,
        constant=F(2, 3),
        certificate_kind=CertificateKind.IDENTITY,
        certified_against="Lambda-WP",
        form=ConstraintForm.OPERATOR,
    )
    return rule_unsound_transplant((request,))


def _case_column_stochastic() -> Refusal | None:
    # THE CONTRACT'S OWN DEFECT EXAMPLE, at the smallest scale that carries it:
    # K = 1, a matrix that is monotone and descends and whose empty column sums
    # to 999/1000 rather than to one. "A DARK-COUNT MATRIX WHOSE COLUMNS SUM TO
    # 1 ONLY TO WITHIN A ROUNDING ERROR, say -- IS STILL REFUSED, NOW BY THE
    # COLUMN-STOCHASTICITY ROW AND UNDER ITS OWN REASON STRING"
    # (Remark rem:tolboundary). No tolerance is passed because the rule takes
    # none: "the tolerance does not reach R".
    empty: frozenset[int] = frozenset()
    click = frozenset({1})
    channel = DarkCountChannel(
        ports=1,
        entries={
            (click, click): F(1),
            (click, empty): F(1, 5),
            (empty, empty): F(4, 5) - F(1, 1000),
        },
    )
    return rule_column_stochastic(channel)


def _case_declared_domination_link() -> Refusal | None:
    """Run a request DECLARING a ``family-dominating`` link, end to end.

    THE FROZEN ``R-kind-family-dominating`` CASE IS SUPERSEDED, NOT DELETED
    (there is no domination submodule). The freeze reserved the kind and refused it
    under
    ``link_kind_deferred``; ``req:reserved-link-kinds`` reserves only
    ``label-space``, so the link-kind row does not refuse it -- asserted here
    -- and no link of that kind is implemented, so a request that declares
    one is refused by the chain row under the existing ``chain_ill_formed``.
    """
    assert (
        rule_link_kind(
            (
                LinkDeclaration(
                    stage=LinkStage.RECEIVER, kind=LinkKind.FAMILY_DOMINATING
                ),
            )
        )
        is None
    )
    outcome = reduce_flat(
        flat_call(
            link_declarations=(
                LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.WPFSS),
                LinkDeclaration(
                    stage=LinkStage.RECEIVER, kind=LinkKind.FAMILY_DOMINATING
                ),
            )
        )
    )
    return outcome.refusal


#: THE FROZEN CASES A LATER AMENDMENT SUPERSEDES, each mapped to the reason the
#: code now gives and the builder that produces it. The frozen record keeps its
#: reason; the live side is compared THROUGH THIS MAP, with its reason.
SUPERSEDED_CASES: dict[str, tuple[str, Callable[[], Refusal | None]]] = {
    "R-kind-family-dominating": ("chain_ill_formed", _case_declared_domination_link),
}


#: One builder per frozen ``RefusalCase.case_id``. Every frozen case is covered
#: and no builder exists without one, which the totality test below asserts.
BUILDERS: dict[str, Callable[[], Refusal | None]] = {
    "R-receiver-draft": _case_receiver_draft,
    "R-cutoff": _case_cutoff,
    "R-block-structure": _case_block_structure,
    "R-fibre-split": _case_fibre_split,
    "R-descent": _case_descent,
    "R-absorbing": _case_absorbing,
    "R-total-weight": _case_total_weight,
    "R-probe-weights": _case_probe_weights,
    "R-relation-impossible": _case_relation_impossible,
    "R-chain-not-composable": _case_chain_not_composable,
    "R-stage-order": _case_stage_order,
    "R-kind-source-map": _case_kind(LinkKind.SOURCE_MAP),
    "R-kind-family-dominating": _case_kind(LinkKind.FAMILY_DOMINATING),
    "R-kind-label-space": _case_kind(LinkKind.LABEL_SPACE),
    "R-approximate": _case_approximate,
    "R-device-family": _case_device_family,
    "R-no-certificate": _case_no_certificate,
    "R-data-dependent": _case_data_dependent,
    "R-licence-missing": _case_licence_missing,
    "R-licence-without-constraints": _case_licence_without_constraints,
    "R-route-both": _case_route_both,
    "R-channel-mismatch": _case_channel_mismatch,
    "R-alphabet-order": _case_alphabet_order,
    "R-post-processing-order": _case_post_processing_order,
    "R-unsound-transplant": _case_unsound_transplant,
}

#: THE THREE ROWS 0.2.0 ADDS, with the builder for each. Two carry a NEW string
#: and the third carries an EXISTING one, which is why the row count moves by
#: three and the string count by two.
#:
#: SUPERSEDED IN ONE ENTRY AT 1.0.0 AND NOT DELETED. The tolerance row is
#: REPLACED IN PLACE by the exact-admissibility row and its string is renamed
#: (``FAIL_CLOSED_ROWS_REPLACED_1_0_0``), so the 0.2.0 pairing is re-pointed at
#: the row that stands where it stood rather than dropped: the test below still
#: asserts that three rows arrived at 0.2.0 and that the third carried an
#: existing string, which is the fact the freeze is about.
BUILDERS_0_2_0: dict[str, Callable[[], Refusal | None]] = {
    "declaration_not_exactly_admissible": _case_declaration_not_exactly_admissible,
    "high_photon_slot_ill_formed": _case_high_photon_slot,
    "licensed_hermiticity (constraint_without_certificate)": (
        _case_licensed_hermiticity
    ),
}

#: THE FOUR ROWS 1.0.0 ADDS OR REPLACES, with the builder for each. THREE ARE
#: NEW (the lattice-exponent row, which RUNS FIRST; the requested-assurance
#: row; the emitted-family row, THE SECOND GATE) and ONE IS REPLACED IN PLACE.
#: The lattice-exponent row is built twice because Section 4.14 refuses BOTH of
#: its inequalities "UNDER THE SAME REASON".
BUILDERS_1_0_0: dict[str, Callable[[], Refusal | None]] = {
    "lattice_exponent_not_declared": _case_lattice_exponent_not_declared,
    "lattice_exponent_not_declared (eq:latsumcond)": (
        _case_lattice_exponent_accumulation
    ),
    "requested_assurance_unknown": _case_requested_assurance_unknown,
    "declaration_not_exactly_admissible": _case_declaration_not_exactly_admissible,
    "emitted_family_not_admissible": _case_emitted_family_not_admissible,
}

#: THE ONE ROW 0.3.0 ADDS, with its one NEW string. Here the row count and the
#: string count move together, which is a coincidence of this amendment and not
#: a rule -- at 0.2.0 three rows carried two strings.
BUILDERS_0_3_0: dict[str, Callable[[], Refusal | None]] = {
    "dark_counts_not_column_stochastic": _case_column_stochastic,
}


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", REFUSAL_CASES, ids=lambda case: str(case.case_id))
def test_each_frozen_refusal_case_is_produced_by_the_code(case: object) -> None:
    """The declared datum the case names, run through the rule that decides it.

    ONE CASE IS SKIPPED HERE, and none is deleted: :data:`REMOVABLE_CASE` is a
    removable submodule's row, replayed exactly as the freeze has it in that
    submodule's own test file.
    """
    if case.case_id not in BUILDERS:  # type: ignore[attr-defined]
        assert case.case_id == REMOVABLE_CASE  # type: ignore[attr-defined]
        pytest.skip("a removable submodule's row, replayed in its own file")
    builder = BUILDERS[case.case_id]  # type: ignore[attr-defined]
    reason = case.reason  # type: ignore[attr-defined]
    if case.case_id in SUPERSEDED_CASES:  # type: ignore[attr-defined]
        reason, builder = SUPERSEDED_CASES[case.case_id]  # type: ignore[attr-defined]
    refusal = builder()
    assert refusal is not None, case.case_id  # type: ignore[attr-defined]
    assert str(refusal.reason) == reason, case.case_id  # type: ignore[attr-defined]
    # A refusal is a RECORD: it carries the reason, the row that decided it, and
    # the offending datum in prose. It is never raised.
    assert refusal.rule
    assert refusal.detail
    assert refusal.as_machine_record()["reason"] == reason


@pytest.mark.contract
@pytest.mark.oracle
def test_the_four_rows_1_0_0_adds_or_replaces_produce_their_strings() -> None:
    """THREE ROWS ADDED AND ONE REPLACED IN PLACE, against FOUR new strings.

    The counts do NOT move together here, which is the fact the registry
    freezes separately: three rows arrive, four strings arrive, and one string
    leaves -- because the row that is REPLACED keeps its position and renames
    its reason.

    THE LATTICE-EXPONENT ROW IS BUILT TWICE. Section 4.14 refuses BOTH of its
    inequalities -- ``1 <= kappa <= 53`` and Eq. ``eq:latsumcond`` -- "UNDER THE
    SAME REASON", so one builder is not evidence that the second inequality is
    decided at all.
    """
    produced = {
        name: str(builder().reason)  # type: ignore[union-attr]
        for name, builder in BUILDERS_1_0_0.items()
    }
    assert produced == {
        "lattice_exponent_not_declared": "lattice_exponent_not_declared",
        "lattice_exponent_not_declared (eq:latsumcond)": (
            "lattice_exponent_not_declared"
        ),
        "requested_assurance_unknown": "requested_assurance_unknown",
        "declaration_not_exactly_admissible": "declaration_not_exactly_admissible",
        "emitted_family_not_admissible": "emitted_family_not_admissible",
    }
    assert {
        row: emitted_spelling(reason)
        for row, reason in FAIL_CLOSED_ROWS_ADDED_1_0_0
    } == {
        "the lattice-exponent row (RUNS FIRST)": "lattice_exponent_not_declared",
        "the requested-assurance row": "requested_assurance_unknown",
        "the emitted-family row (THE SECOND GATE)": "emitted_family_not_admissible",
    }
    assert len(FAIL_CLOSED_ROWS_ADDED_1_0_0) == 3
    assert len(FAIL_CLOSED_ROWS_REPLACED_1_0_0) == 1
    assert len(REFUSAL_REASONS_ADDED_1_0_0) == 4
    assert len(REFUSAL_REASONS_REMOVED_1_0_0) == 1
    # THE ROW THAT RUNS FIRST RUNS FIRST. "This row runs first and refuses
    # before anything is constructed" is a statement about ORDER, and
    # RULE_ORDER is built from the enum, so the enum's first member is what
    # decides which reason a caller receives when two rows would refuse.
    assert RULE_ORDER[0] is FailClosedRule.LATTICE_EXPONENT
    assert REFUSAL_REASONS_1_0_0[0] == "lattice_exponent_not_declared"


@pytest.mark.contract
@pytest.mark.oracle
def test_every_reason_of_the_vocabulary_is_produced_by_the_code() -> None:
    """THE TOTALITY PROOF AT 1.0.0: THIRTY strings, produced by the code.

    The set of reasons the code emits across the frozen cases, the three 0.2.0
    rows, the one 0.3.0 row and the four 1.0.0 rows equals
    ``REFUSAL_REASONS_1_0_0`` equals the module's enum. A THIRTY-FIRST STRING
    CANNOT APPEAR ON EITHER SIDE without this failing -- which is the check
    that keeps the four ``meat-core`` strings this text quotes out of this
    module's vocabulary.

    THE 1.0.0 AMENDMENT BREAKS THE SUBSET CHAIN, AND THAT IS THE POINT. Every
    earlier amendment only ADDED, so each superseded vocabulary was a PROPER
    SUBSET of its successor. 1.0.0 REMOVES ONE STRING --
    ``declaration_outside_tolerance`` -- so the chain is asserted up to 0.3.0
    and then broken deliberately, with the removal named. Asserting a subset
    here would have made the test pass by not looking at the removal, which is
    exactly the drift a totality proof exists to catch.
    """
    produced = set()
    for case_id, builder in BUILDERS.items():
        # The superseded case still runs its frozen builder here: the
        # link-kind row still produces the string for `source-map` and
        # `label-space`, and the superseded one produces `chain_ill_formed`.
        if case_id in SUPERSEDED_CASES:
            builder = SUPERSEDED_CASES[case_id][1]
        refusal = builder()
        assert refusal is not None
        produced.add(str(refusal.reason))
    # THE 0.1.3 TWENTY-FOUR ARE UNTOUCHED BY THIS AMENDMENT: the string 1.0.0
    # removes arrived at 0.2.0, so every builder here still fires and the set
    # they produce is the 0.1.3 vocabulary unchanged -- LESS the removable
    # row's string, which is its submodule's to carry.
    assert produced == set(REFUSAL_REASONS) - REMOVABLE_OWNED
    assert len(produced) == 23

    for builder in BUILDERS_0_2_0.values():
        refusal = builder()
        assert refusal is not None
        produced.add(str(refusal.reason))

    for builder in BUILDERS_0_3_0.values():
        refusal = builder()
        assert refusal is not None
        produced.add(str(refusal.reason))

    for builder in BUILDERS_1_0_0.values():
        refusal = builder()
        assert refusal is not None
        produced.add(str(refusal.reason))

    assert produced == emitted_vocabulary(REFUSAL_REASONS_1_0_0)

    # THE ONE STRING ADDED SINCE THE FREEZE, wpfss's row 29
    # (wpfss/req:normalized-branch-refusal): its rule at a factored loss below
    # one, the case the frozen registry does not carry.
    from certiqs_key.reductions.wpfss.validation import rule_normalized_branch

    branch = rule_normalized_branch(Fraction(1, 2))
    assert branch is not None
    assert rule_normalized_branch(Fraction(1)) is None
    produced.add(str(branch.reason))
    # THE CORE ENUM IS THIRTY OF THE THIRTY-ONE: the thirty-first is the
    # removable submodule's own string and is spelled there, so that deleting
    # that directory takes it with it.
    assert produced == {str(reason) for reason in RefusalReason}
    assert len(produced) == 30

    # THE CHAIN, up to the version at which it breaks.
    assert (
        set(REFUSAL_REASONS) < set(REFUSAL_REASONS_0_2_0) < set(REFUSAL_REASONS_0_3_0)
    )
    # AND THE BREAK, named: 1.0.0 removes one string and adds four.
    assert set(REFUSAL_REASONS_REMOVED_1_0_0) == {"declaration_outside_tolerance"}
    assert set(REFUSAL_REASONS_REMOVED_1_0_0) <= set(REFUSAL_REASONS_0_3_0)
    assert set(REFUSAL_REASONS_REMOVED_1_0_0).isdisjoint(REFUSAL_REASONS_1_0_0)
    assert emitted_vocabulary(REFUSAL_REASONS_ADDED_1_0_0) == {
        "lattice_exponent_not_declared",
        "requested_assurance_unknown",
        "declaration_not_exactly_admissible",
        "emitted_family_not_admissible",
    }
    assert set(REFUSAL_REASONS_ADDED_1_0_0) <= set(REFUSAL_REASONS_1_0_0)
    assert not set(REFUSAL_REASONS_0_3_0) <= set(REFUSAL_REASONS_1_0_0)
    # THE FOUR CONSUMER STRINGS ARE NOT OURS, checked rather than remembered.
    assert set(CONSUMER_STRINGS_NOT_OURS_0_3_0).isdisjoint(REFUSAL_REASONS_1_0_0)
    assert set(CONSUMER_STRINGS_NOT_OURS_0_3_0).isdisjoint(produced)

    mark = next(
        record for record in SUPERSESSIONS if record.symbol == "REFUSAL_REASONS"
    )
    assert mark.kind == "vocabulary"
    assert mark.replacement == (
        "REFUSAL_REASONS_0_2_0",
        "REFUSAL_REASONS_ADDED_0_2_0",
    )
    mark_0_3_0 = next(
        record
        for record in SUPERSESSIONS_0_3_0
        if record.symbol == "REFUSAL_REASONS_0_2_0"
    )
    assert mark_0_3_0.kind == "vocabulary"
    assert mark_0_3_0.replacement == (
        "REFUSAL_REASONS_0_3_0",
        "REFUSAL_REASONS_ADDED_0_3_0",
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_three_rows_0_2_0_adds_carry_the_strings_the_freeze_names() -> None:
    """THREE ROWS, TWO STRINGS: the counts do not determine each other.

    ``FAIL_CLOSED_ROWS_ADDED_0_2_0`` freezes the pairing, and the third row --
    the licensed-route Hermiticity row -- carries the EXISTING
    ``constraint_without_certificate``.
    """
    produced = {
        name: str(builder().reason)  # type: ignore[union-attr]
        for name, builder in BUILDERS_0_2_0.items()
    }
    # THE ROW THAT STANDS WHERE THE 0.2.0 TOLERANCE ROW STOOD now carries the
    # 1.0.0 string, and FAIL_CLOSED_ROWS_REPLACED_1_0_0 is the frozen record of
    # that replacement. The 0.2.0 tuple is asserted UNCHANGED beside it: it is
    # history, and re-pointing it in place would erase what 0.2.0 did.
    assert produced["declaration_not_exactly_admissible"] == (
        "declaration_not_exactly_admissible"
    )
    assert produced["high_photon_slot_ill_formed"] == "high_photon_slot_ill_formed"
    assert produced["licensed_hermiticity (constraint_without_certificate)"] == (
        "constraint_without_certificate"
    )
    assert dict(FAIL_CLOSED_ROWS_ADDED_0_2_0) == {
        "the declared-tolerance row": "declaration_outside_tolerance",
        "the high-photon slot row": "high_photon_slot_ill_formed",
        "the licensed-route exact-Hermiticity row": ("constraint_without_certificate"),
    }
    assert len(FAIL_CLOSED_ROWS_ADDED_0_2_0) == 3
    assert len({reason for _, reason in FAIL_CLOSED_ROWS_ADDED_0_2_0}) == 3
    assert {row: (was, now) for row, was, now in FAIL_CLOSED_ROWS_REPLACED_1_0_0} == {
        "the declared-blocks row": (
            "declaration_outside_tolerance",
            "declaration_not_exactly_admissible",
        )
    }
    assert FAIL_CLOSED_ROW_COUNT_0_3_0 == 25
    # TWENTY-ONE IN THE CORE ENUM; the other seven are the submodules' and
    # are merged per call, so the frozen twenty-eight is the union.
    assert len(FailClosedRule) + len(WPFSS_ROWS) + 1 == (
        FAIL_CLOSED_ROW_COUNT_1_0_0
    ) == 28


@pytest.mark.contract
@pytest.mark.oracle
def test_the_one_row_0_3_0_adds_carries_the_one_string_the_freeze_names() -> None:
    """ONE ROW, ONE STRING, and the counts move together only by coincidence.

    ``FAIL_CLOSED_ROW_COUNT_0_2_0`` is marked ``superseded`` at 0.3.0 and is
    asserted here as history: twenty-four became twenty-five. The reason count
    is frozen SEPARATELY from the row count "because the two do not determine
    each other: at 0.2.0 three rows carried two strings, and at 0.3.0 one row
    carries one".
    """
    produced = {
        name: str(builder().reason)  # type: ignore[union-attr]
        for name, builder in BUILDERS_0_3_0.items()
    }
    assert produced == {
        "dark_counts_not_column_stochastic": "dark_counts_not_column_stochastic"
    }
    assert dict(FAIL_CLOSED_ROWS_ADDED_0_3_0) == {
        "the column-stochasticity row": "dark_counts_not_column_stochastic"
    }
    assert len(FAIL_CLOSED_ROWS_ADDED_0_3_0) == 1
    assert FAIL_CLOSED_ROW_COUNT_0_2_0 == 24
    assert FAIL_CLOSED_ROW_COUNT_0_3_0 == 25
    # THE LIVE COUNT IS 1.0.0's. The two frozen counts above are HISTORY and
    # are asserted as such; what the enum must equal is the accepted contract's
    # row count, which the amendment took from twenty-five to twenty-eight.
    # TWENTY-ONE IN THE CORE ENUM; the other seven are the submodules' and
    # are merged per call, so the frozen twenty-eight is the union.
    assert len(FailClosedRule) + len(WPFSS_ROWS) + 1 == (
        FAIL_CLOSED_ROW_COUNT_1_0_0
    ) == 28
    # The row carries exactly this one string, and no other row carries it.
    carriers = [
        rule
        for rule, reasons in fail_closed_rules().items()
        if RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC in reasons
    ]
    assert carriers == [WpfssRule.COLUMN_STOCHASTIC]


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_case_has_a_builder_and_every_builder_a_frozen_case() -> None:
    """No case is skipped and no builder invents a failure the freeze lacks.

    ONE CASE IS RETIRED AND REWRITTEN: ``R-block-structure``, whose 0.1.3 datum
    cannot be declared at 0.2.0. It keeps its case id and its reason -- the row
    and the string are unchanged -- and its builder now declares the structural
    failure the restated row refuses. The mark is asserted here so that a reader
    of this file meets it.
    """
    frozen = {case.case_id for case in REFUSAL_CASES}
    assert set(BUILDERS) == frozen - {REMOVABLE_CASE}
    assert len(REFUSAL_CASES) == 26
    marked = [case for case in REFUSAL_CASES if getattr(case, "superseded_by", None)]
    assert [case.case_id for case in marked] == ["R-block-structure"]
    assert marked[0].superseded_by == "0.2.0"
    assert marked[0].superseded_replacement == (
        "TOL_ROW_CASES",
        "TOL-scope-receiver-block-admit",
    )
    mark = next(record for record in SUPERSESSIONS if record.symbol == "REFUSAL_CASES")
    assert mark.kind == "input shape"
    assert mark.still_valid_at_zero_tolerance is False
    deferred = [case for case in REFUSAL_CASES if case.reason == "link_kind_deferred"]
    assert len(deferred) == 3


@pytest.mark.contract
def test_a_chain_can_fail_c2_as_well_as_c1_with_the_same_reason() -> None:
    """Definition ``def:chain``: (C1) and (C2) are two routes to one reason."""
    refusal = _case_chain_not_tuple_chained()
    assert refusal is not None
    assert refusal.reason is RefusalReason.CHAIN_ILL_FORMED
    assert "(C2)" in refusal.detail


#: THE CONJUNCTS OF ``def:exactadm`` the admissibility row decides, and a
#: declared block that breaks each. "A fail-closed row whose refusal path never
#: executes is a row whose refusal could be mis-wired without the suite
#: noticing". Each case names the locator
#: the detail must carry AND the conjunct the row must record as failed.
ADMISSIBILITY_CONJUNCTS: tuple[tuple[str, str, Matrix], ...] = (
    ("def:exactadm (b)", "hermiticity", matrix([[Cx(F(1, 4), F(1, 8))]])),
    ("eq:psdtest", "positivity", matrix([[F(-1, 4)]])),
    ("eq:latinv", "lattice_invariant", matrix([[F(1, 3)]])),
    ("def:exactadm (d)", "completeness", matrix([[F(1, 8)]])),
)


@pytest.mark.contract
@pytest.mark.parametrize(
    ("locator", "conjunct", "block"),
    ADMISSIBILITY_CONJUNCTS,
    ids=[case[1] for case in ADMISSIBILITY_CONJUNCTS],
)
def test_each_admissibility_conjunct_produces_its_own_refusal_detail(
    locator: str, conjunct: str, block: Matrix
) -> None:
    """Row 6 names WHICH conjunct failed, and each is reachable.

    The fail-closed table requires that "THE REFUSAL NAMES WHICH ONE FAILED";
    this establishes that property for the five of ``def:exactadm`` (c).
    """
    artifact = _artifact()
    blocks = dict(artifact.photon_blocks)
    blocks[("y_mc", "t_on")] = (block,)
    decision = rule_exact_admissibility(
        blocks,
        artifact.channel_grading,
        artifact.detection_alphabet,
        artifact.bound_quantifier_domain.settings,
        lattice_exponent=4,
    )
    refusal = decision.refusal
    assert refusal is not None
    assert refusal.reason is RefusalReason.DECLARATION_NOT_EXACTLY_ADMISSIBLE
    assert refusal.rule == str(FailClosedRule.EXACT_ADMISSIBILITY)
    assert locator in refusal.detail
    assert dict(decision.conjuncts)[conjunct] is False
    # THE HONEST DECLARATION IS NOT REFUSED, so each case is the block and not
    # the fixture.
    assert (
        rule_exact_admissibility(
            artifact.photon_blocks,
            artifact.channel_grading,
            artifact.detection_alphabet,
            artifact.bound_quantifier_domain.settings,
            lattice_exponent=4,
        ).refusal
        is None
    )


@pytest.mark.contract
def test_the_declared_order_sum_conjunct_is_decided_and_is_never_the_first() -> None:
    """``def:exactadm`` (e), the fifth conjunct, and WHY IT CANNOT FAIL ALONE.

    The row decides "the declared-order completeness sum ROUNDS NOWHERE", and
    the branch that records it as failed is reachable -- here at ``kappa = 53``
    with the declared blocks ``1, 2^-53, -2^-53, 0``, whose second partial sum
    ``1 + 2^-53`` is not a binary64 number.

    IT IS NEVER THE FIRST FAILING CONJUNCT OF AN OTHERWISE ADMISSIBLE FAMILY,
    and that is a fact about the other four rather than a gap in this test.
    Where (b), (c), (d) and Eq. ``eq:latinv`` all hold, every block is positive
    with diagonal entries in ``[0, 1]`` summing to one, so by Cauchy-Schwarz
    every partial sum of an entry has modulus at most one and is a multiple of
    ``2^-kappa`` with ``kappa <= 53`` -- hence exactly a binary64 number, and
    the sum rounds nowhere. The case below is therefore built with positivity
    broken, which is what makes the overshoot possible at all: the row records
    positivity as the refusal and (e) as a failed conjunct beside it.
    """
    artifact = _artifact()
    tiny = F(1, 2**53)
    values = (F(1), tiny, -tiny, F(0))
    blocks = dict(artifact.photon_blocks)
    for letter, value in zip(artifact.detection_alphabet, values, strict=True):
        blocks[(letter, "t_on")] = (matrix([[value]]),)
    decision = rule_exact_admissibility(
        blocks,
        artifact.channel_grading,
        artifact.detection_alphabet,
        ("t_on",),
        lattice_exponent=53,
    )
    recorded = dict(decision.conjuncts)
    # The family IS exactly complete and IS on the lattice; what it is not is
    # positive, and what its declared-order sum does is round.
    assert recorded["completeness"] is True
    assert recorded["lattice_invariant"] is True
    assert recorded["hermiticity"] is True
    assert recorded["positivity"] is False
    assert recorded["declared_order_sum"] is False
    assert decision.refusal is not None
    assert "eq:psdtest" in decision.refusal.detail
