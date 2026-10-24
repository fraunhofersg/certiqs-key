"""``reduce_flat``: the emission with no branches, as an instance builder.

WHAT THIS FILE IS. The one method
:class:`certiqs_key.reductions.instance.InstanceBuilder` asks for, and the
entry point a run selects when no branching model is declared. It decides the
six rows this submodule owns, runs the classical post-processing of steps 1 and
2, routes the certified weights, and hands the core the flat instance of
``prop:flat-instance``.

THE ROWS ARE DECIDED WHETHER OR NOT AN INSTANCE IS BUILT, because the
verification report carries every row of the reduction with its outcome and a
row that could not be decided must say so rather than be absent.

THE ORDER THE ROWS ARE DECIDED IN IS THE ORDER THEIR DATA BECOMES AVAILABLE and
is not the order they are reported in: the absorbing row needs ``R^cg``, which
needs descent; the weight row needs the weight route, which needs the absorbing
check. The refusal a caller receives is the first failing row in the
INTERFACE'S order, which the core decides when it assembles the report.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import ClassVar

from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.reductions.artifact import ReductionOutcome
from certiqs_key.reductions.emit import reduce
from certiqs_key.reductions.inputs import JointOutcome, ReductionCall, probe_settings_of
from certiqs_key.reductions.instance import BuildContext, BuildOutcome, precompose
from certiqs_key.reductions.reasons import Refusal
from certiqs_key.reductions.validation import RuleOutcome
from certiqs_key.reductions.wpfss.construction import (
    flat_instance,
    normalized_precomposition,
)
from certiqs_key.reductions.wpfss.validation import (
    WPFSS_ROWS,
    FailClosedRule,
    rule_absorbing,
    rule_column_stochastic,
    rule_descent,
    rule_fibre,
    rule_high_photon_slot,
    rule_total_weight,
)
from certiqs_key.reductions.wpfss.weights import (
    BoundedLetter,
    DescendedChannel,
    bounded_letters,
    descend,
    post_processed_preserved_factors,
    weight_route,
)

__all__ = ["FLAT_ROWS", "FlatInstanceBuilder", "reduce_flat"]

#: The rows a flat reduction adds to the core's twenty-one, in table order.
FLAT_ROWS = WPFSS_ROWS


@dataclass(frozen=True)
class FlatInstanceBuilder:
    """The builder of ``prop:flat-instance``, and of ``cor:normalized-flat``.

    :meth:`build` is what the core calls, and what a builder that lifts the
    flat instance -- a branching one -- reads before lifting it. Where the
    receiver artefact carries a factored loss ``t < 1`` (its blocks are the
    normalized station's), the instance built is the flat instance
    precomposed with the pure-loss channel of transmittance ``t``
    (``cor:normalized-flat``; ``reductions/lem:precomposed-instance``).
    """

    #: THE CLAIM THAT ESTABLISHES (H-REF) of ``reductions/cor:reference-companion``
    #: for this instance (``reductions/req:reference-companion``: the companion
    #: is emitted only where a claim of the module establishes it). A builder
    #: without this attribute gets no companion.
    companion_claim: ClassVar[str] = "reductions/wpfss/cor:flat-companion"
    #: The claim stating, for this instance, the condition on an enclosure of
    #: the companion's datum under which a requested entry's certificate holds
    #: there, by writing kind (``reductions/req:reference-companion`` (iii)):
    #: Eq. ``eq:companion-two-sector`` for the operator ``eq:two-sector-entry``.
    companion_entry_claims: ClassVar[Mapping[str, str]] = MappingProxyType(
        {"two_sector": "reductions/wpfss/cor:flat-companion (eq:companion-two-sector)"}
    )
    #: THE CLAIM THAT SHOWS THIS INSTANCE'S RULE OF (I1) A NON-NEGATIVE
    #: COMBINATION (``reductions/req:reference-companion`` (vii)), by which the
    #: companion carries the handed reference's factor enclosures to its datum
    #: (:meth:`datum_factors`). A builder without it carries none; a branching
    #: builder, which lifts this instance, names none.
    factor_claim: ClassVar[str] = "reductions/wpfss/cor:flat-companion"

    def datum_factors(
        self,
        call: ReductionCall,
        factors: Mapping[JointOutcome, tuple[FactorEnclosure | None, ...]],
    ) -> dict[JointOutcome, tuple[FactorEnclosure | None, ...]] | None:
        """Return the factor enclosure of every element of the companion's datum.

        ``reductions/cor:companion-factor-enclosure`` (i) with the coefficients
        of ``reductions/wpfss/cor:flat-companion``
        (:func:`~certiqs_key.reductions.wpfss.weights.
        post_processed_preserved_factors`); ``factors`` are the handed blocks'
        own, keyed as ``photon_blocks`` is. ``None`` where ``R^cg`` is not
        formed (the descent row refuses), as no datum is then.
        """
        rows = call.artifact_rows
        descended = descend(rows.dark_count_channel, rows.outcome_coarse_graining)
        if descended is None:
            return None
        return post_processed_preserved_factors(
            rows,
            call.declaration.probe_declaration,
            descended,
            call.declaration.joint_alphabet,
            factors,
        )

    def build(self, context: BuildContext) -> BuildOutcome:
        """Decide this submodule's rows and return the flat instance, or none."""
        call = context.request
        artifact_rows = call.artifact_rows
        declaration = call.declaration
        outcomes: dict[str, RuleOutcome] = {}

        def decide(rule: str, refusal: Refusal | None, detail: str = "") -> None:
            outcomes[rule] = RuleOutcome(
                rule=rule, decided=True, refusal=refusal, detail=detail
            )

        def undecidable(rule: str, detail: str) -> None:
            outcomes[rule] = RuleOutcome(
                rule=rule, decided=False, refusal=None, detail=detail
            )

        # THE COLUMN-STOCHASTICITY ROW IS DECIDED ON THE DECLARED R AND ON
        # NOTHING ELSE, so it needs no coarse-graining and no descended matrix,
        # and it is decided before either. It does NOT gate the rows below it:
        # the defect this row exists for is one "NO OTHER ROW CATCHES", and
        # suppressing the descent, absorbing and total-weight decisions on a
        # declaration this row refuses would replace that checkable fact with
        # silence. No artifact is emitted in any case, and the reason a caller
        # receives is this row's, it coming first among these in the table.
        decide(
            FailClosedRule.COLUMN_STOCHASTIC,
            rule_column_stochastic(artifact_rows.dark_count_channel),
        )

        descended: DescendedChannel | None = None
        descent_refusal = rule_descent(
            artifact_rows.dark_count_channel, artifact_rows.outcome_coarse_graining
        )
        decide(FailClosedRule.DESCENT, descent_refusal)
        if descent_refusal is None:
            descended = descend(
                artifact_rows.dark_count_channel,
                artifact_rows.outcome_coarse_graining,
            )

        fibre_refusal = rule_fibre(
            artifact_rows.high_photon_bounds, artifact_rows.outcome_coarse_graining
        )
        decide(FailClosedRule.FIBRE, fibre_refusal)

        letters: tuple[BoundedLetter, ...] | None = None
        if descended is not None and fibre_refusal is None:
            letters = bounded_letters(
                artifact_rows.high_photon_bounds,
                artifact_rows.outcome_coarse_graining,
                descended,
            )
        if letters is None:
            undecidable(
                FailClosedRule.ABSORBING,
                "R^cg or the bounded letters are unavailable: Eq. eq:absorbing "
                "is a statement about the DESCENDED matrix at each bounded "
                "letter",
            )
        else:
            decide(FailClosedRule.ABSORBING, rule_absorbing(letters))

        # THE SLOT, PER SETTING: the slot is read only from a
        # receiver version stating the per-setting weights, so an artifact of
        # an earlier version is refused whatever its weights, a probe-free and
        # setting-uniform one included (req:supplier-version;
        # requires_a_receiver_version_stating_them); its settings are the
        # supplied blocks' T, and each entry's weights are non-negative and sum
        # to at most one at every setting.
        supplied_settings = probe_settings_of(artifact_rows.photon_blocks)
        decide(
            FailClosedRule.HIGH_PHOTON_SLOT,
            rule_high_photon_slot(
                artifact_rows.high_photon_bounds,
                supplied_settings,
                artifact_rows.mathematical_spec_version,
            ),
        )

        # The emitted weights, ROUNDED DOWN onto the declared lattice
        # (Eq. eq:latdown). The row below reads THE EMITTED weights and not the
        # exact ones, so `p < 1` is decided of the numbers that leave. Eq.
        # eq:weightroute reads at (y_i, t) the weight OF THAT SETTING, so the
        # route runs only where every entry carries a weight at every declared
        # setting; a slot that does not is the slot row's refusal, and the
        # total is then not formed rather than formed from a default.
        kappa = context.lattice_exponent
        declared_settings = set(declaration.probe_declaration.settings)
        slot_covers_the_settings = all(
            declared_settings <= set(bound.settings)
            for bound in artifact_rows.high_photon_bounds
        )
        weights: dict[JointOutcome, Fraction] | None = None
        if (
            letters is not None
            and rule_absorbing(letters) is None
            and kappa is not None
            and slot_covers_the_settings
        ):
            weights = weight_route(
                letters,
                declaration.probe_declaration,
                declaration.joint_alphabet,
                lattice_exponent=kappa,
            )
        if weights is None:
            undecidable(
                FailClosedRule.TOTAL_WEIGHT,
                "the weight family of Eq. eq:weightroute is unavailable (no "
                "descended matrix, a fibre or absorbing refusal, no lattice, or "
                "a slot without a weight at some declared setting), so p is not "
                "formed; p_v < 0 and p > 1 remain impossibilities (lem:ple1)",
            )
        else:
            decide(
                FailClosedRule.TOTAL_WEIGHT,
                rule_total_weight([weights[v] for v in declaration.joint_alphabet]),
            )

        reported = tuple(outcomes[str(row.rule)] for row in WPFSS_ROWS)
        if (
            not context.core_ready
            or weights is None
            or descended is None
            or context.route is None
            or not outcomes[FailClosedRule.TOTAL_WEIGHT].passed
        ):
            return BuildOutcome(rows=WPFSS_ROWS, outcomes=reported, instance=None)

        instance = flat_instance(
            context, descended=descended, weights=weights, route=context.route
        )
        if isinstance(instance, Refusal):  # pragma: no cover - defensive
            return BuildOutcome(rows=WPFSS_ROWS, outcomes=reported, instance=None)
        if artifact_rows.factored_loss < 1:
            # cor:normalized-flat; req:normalized-link-record. The blocks are
            # the NORMALIZED STATION's, so the reduction of the receiver is the
            # flat instance precomposed with the pure-loss channel of the
            # factored loss: every emitted number is the flat instance's, and
            # the link records the loss in front.
            instance = precompose(
                instance, normalized_precomposition(artifact_rows.factored_loss)
            )
        return BuildOutcome(rows=WPFSS_ROWS, outcomes=reported, instance=instance)


def reduce_flat(request: ReductionCall) -> ReductionOutcome:
    """Run a reduction with NO branching model: ``cor:emitted-flat``.

    The physical system is the channel space itself. Every emitted number is
    the one a DEGENERATE branching model -- one mode, a one-dimensional
    register -- would produce, with the ampliation removed; a parity test on the
    carried golden inputs shows it.
    """
    return reduce(request, FlatInstanceBuilder())
