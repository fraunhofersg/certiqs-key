"""The weight-preserving and flag-state targets, and the FLAT reduction instance.

WHAT THIS SUBMODULE IS. One squasher: the flag-state squasher with certified
weights, and the two targets it emits. The core states ``thm:emit``,
``cor:entries`` and ``thm:chain`` over ``def:reduction-instance``; this file
proves nothing and builds the instance those theorems are then applied to --
``prop:flat-instance`` and ``cor:emitted-flat``, the emission with NO BRANCHES.

THE FLAT INSTANCE'S PHYSICAL SYSTEM IS THE CHANNEL SPACE ITSELF, WITH NO
REGISTER. Reaching the case without branches by declaring a DEGENERATE
branching model -- one mode, register POVM the ``1 x 1`` identity -- would
ampliate every emitted object by a one-dimensional register. The flat instance
emits the same numbers with the ampliation removed, which is exactly why it
exists. A parity test on the carried
golden inputs shows the two agree on every emitted number, the register
bookkeeping aside.

WHAT IS COMPUTED HERE AND WHAT DELIBERATELY IS NOT. The adjoints are the closed
forms the claims prove -- Eq. ``eq:WPadjoint``, Eq. ``eq:L2adjoint`` -- and the
channel is never materialised: the receiver supplier emits NO ABOVE-CUTOFF
BLOCK, "so neither map can be materialised from the artifact -- and neither
need be, SINCE THE CONSUMER NEVER APPLIES IT". :func:`mprime_family`,
:func:`wp_adjoint` and :func:`noise_adjoint` take the above-cutoff data as an
argument because A TOY INSTANCE HAS IT and the claims' identities are checkable
on one; the emitted target is built from the preserved blocks and the weights
alone.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.exact import (
    Matrix,
    add,
    dimension,
    direct_sum,
    identity,
    real_part,
    scale,
    subtract,
    zeros,
)
from certiqs_key.reductions.artifact import (
    ExactIdentity,
    SourceDescriptor,
    TargetDescriptor,
    WpfssData,
)
from certiqs_key.reductions.channels import (
    ChannelWitness,
    TransportedOperator,
    flag_diagonal,
    flag_projector,
    split_blocks,
)
from certiqs_key.reductions.constraints import (
    TWO_SECTOR_DECIDED_CLAIM,
    CertifiedEntry,
    ConstraintEntry,
    DeclaredForm,
    certify_carried_operators,
    restricted_entry,
    theta_typing,
)
from certiqs_key.reductions.errors import HypothesisError, MalformedInputError
from certiqs_key.reductions.inputs import JointOutcome, Label, outcome_label
from certiqs_key.reductions.instance import (
    BuildContext,
    Precomposition,
    ReductionInstance,
)
from certiqs_key.reductions.reasons import (
    AssumptionId,
    CertificateKind,
    LinkKind,
    Refusal,
    Relation,
    Route,
    SourceMode,
)
from certiqs_key.reductions.sectors import (
    Sector,
    SectorKind,
    SectorSet,
    assemble_sector_blocks,
    party_name,
    party_partition_statement,
    sector_projector_label,
)
from certiqs_key.reductions.wpfss.weights import (
    DescendedChannel,
    post_processed_preserved_blocks,
)

__all__ = [
    "CHANNEL_GROUP",
    "FSS_INSTANCE_LOCATOR",
    "PURE_LOSS_IDENTITY",
    "PureLossWitness",
    "flat_instance",
    "flat_scalar_values",
    "flat_sector_transport",
    "flat_sectors",
    "fss_instance_entry",
    "fss_target",
    "mprime_family",
    "noise_adjoint",
    "normalized_precomposition",
    "transported_cutoff_projectors",
    "two_sector_entry",
    "wp_adjoint",
    "wpfss_target",
]

#: The sector group the flat instance's sectors are named under: the channel
#: system. A register-conditioned lift RELABELS them under its branch's name,
#: which is the whole of what the conditioning does to a sector set.
CHANNEL_GROUP: Label = "C"

#: WHAT DISCHARGES THIS INSTANCE'S OWN ENTRIES, supplied to the core with the
#: instance (``ReductionInstance.module_built_locators``). It is THIS
#: SUBMODULE'S corollary and it is named here, because the core "names no
#: construction": a core that spelled one submodule's corollary would attribute
#: every other instance's entries to a certificate they did not earn.
FSS_INSTANCE_LOCATOR: str = (
    "Corollary cor:fssinstance: Lambda^FSS+(O^) = "
    "blk M^{<=N}_o (+) (blk M^{>N}_o - p_o 1) >= 0, the first summand "
    "because M_o is positive and the second by eq:certweights (imported "
    "under Assumption A-RECV)"
)


def wpfss_target(
    preserved: Sequence[Matrix], weights: Sequence[Fraction]
) -> tuple[Matrix, ...]:
    """Eq. ``eq:WPFSS``: the multi-bound weight-preserving flag-state target.

    ``F^WP_v = blk M^{<=N}_v (+) ( p_v 1_Flag + (1 - p) |v><v|_Flag )``, with
    ``p = sum_v p_v``.

    BUILT FROM DECLARED DATA ALONE: the preserved blocks the supplier emits and
    the weights of Eq. ``eq:weightroute``. No above-cutoff block appears, which
    is why the target is emittable while the channel is not.

    The index of ``v`` in ``preserved`` IS its flag basis index, and that index
    is the position of ``v`` in the DECLARED order of ``V``. Nothing here
    reorders.
    """
    if len(preserved) != len(weights):
        raise MalformedInputError("one weight per outcome is required")
    size = len(weights)
    if size == 0:
        raise MalformedInputError("the alphabet is non-empty")
    total = sum(weights, start=Fraction(0))
    out: list[Matrix] = []
    for index, block in enumerate(preserved):
        flag = add(
            scale(weights[index], identity(size)),
            scale(1 - total, flag_projector(size, index)),
        )
        out.append(direct_sum([block, flag]))
    return tuple(out)


def fss_target(preserved: Sequence[Matrix]) -> tuple[Matrix, ...]:
    """Eq. ``eq:FSS``: the flag-state-squasher target, the ``p_v == 0`` case.

    ``F^FSS_v = blk M^{<=N}_v (+) |v><v|_Flag``. This is the target of the
    ``licensed`` route, in which "the certified weights are NOT encoded in the
    target and travel instead as the constraint entry of Corollary
    ``cor:fssinstance``".
    """
    size = len(preserved)
    if size == 0:
        raise MalformedInputError("the alphabet is non-empty")
    return tuple(
        direct_sum([block, flag_projector(size, index)])
        for index, block in enumerate(preserved)
    )


def mprime_family(
    above_cutoff: Sequence[Matrix], weights: Sequence[Fraction]
) -> tuple[Matrix, ...]:
    """Eq. ``eq:Lwp``'s ``M'_v = (blk M^{>N}_v - p_v 1) / (1 - p)``.

    A POVM on ``H(B_{>N})`` by Proposition ``prop:chain`` (i): ``M'_v >= 0`` by
    Eq. ``eq:certweights`` and ``sum_v M'_v = (1 - p)1/(1 - p) = 1`` by block
    completeness. The division by ``1 - p`` is why ``p = 1`` is a genuine
    refusal and why Remark ``rem:peqone`` records that the refusal is
    conservative rather than an obstruction.

    ONLY A TOY INSTANCE CAN CALL THIS. The above-cutoff blocks are not emitted
    by the supplier; see the module docstring.
    """
    if len(above_cutoff) != len(weights):
        raise MalformedInputError("one weight per outcome is required")
    total = sum(weights, start=Fraction(0))
    if total >= 1:
        raise HypothesisError(
            "eq:Lwp divides by 1 - p and is stated for p < 1; a declaration "
            "reaching p = 1 is refused with total_weight_not_below_one, not "
            "constructed (rem:peqone)"
        )
    size = dimension(above_cutoff[0])
    return tuple(
        scale(
            Fraction(1, 1) / (1 - total),
            add(block, scale(-weights[index], identity(size))),
        )
        for index, block in enumerate(above_cutoff)
    )


def wp_adjoint(x: Matrix, preserved_dim: int, mprime: Sequence[Matrix]) -> Matrix:
    """Eq. ``eq:WPadjoint``, the adjoint of ``Lambda^WP`` on a block observable.

    ``Lambda^WP+(X_<=N (+) X_Flag) = X_<=N (+) sum_v <v|X_Flag|v> M'_v``.

    "The output of ``Lambda^WP`` is block diagonal, so ONLY THE DIAGONAL BLOCKS
    of an observable contribute to Eq. ``eq:pairing``", and within the flag
    block only its DIAGONAL ENTRIES do. That is the whole content of the closed
    form, and it is why the two realizing channels of a relation agree on the
    span of ``{F_v} u {O^_k}`` and may differ off it (Lemma ``lem:statistics``,
    last clause).

    Passing ``mprime = (blk M^{>N}_v)_v`` gives ``Lambda^FSS+`` instead, which
    is the ``p_v == 0`` case of the same computation (Eq. ``eq:Lfss``).
    """
    size = len(mprime)
    preserved, flag = split_blocks(x, [preserved_dim, size])
    above_dim = dimension(mprime[0])
    accumulated = zeros(above_dim)
    for index, coefficient in enumerate(flag_diagonal(flag)):
        weight = real_part(coefficient, "a flag-block diagonal entry")
        if weight == 0:
            continue
        accumulated = add(accumulated, scale(weight, mprime[index]))
    return direct_sum([preserved, accumulated])


def noise_adjoint(x: Matrix, preserved_dim: int, weights: Sequence[Fraction]) -> Matrix:
    """Eq. ``eq:L2adjoint``: the adjoint of the flag-noise channel ``Lambda~``.

    ``Lambda~+(X_<=N (+) X_Flag) = X_<=N (+) ( (1-p) X_Flag + tr[mu X_Flag] 1 )``
    with ``mu = sum_v p_v |v><v|``. Proposition ``prop:chain`` (ii) proves
    ``F^WP <=_{Lambda~} F^FSS`` and the exact composition
    ``Lambda^FSS = Lambda~ o Lambda^WP`` on ALL of ``T(B)``, "including states
    with COHERENCES ACROSS THE CUTOFF, WHICH BOTH SIDES DISCARD".
    """
    size = len(weights)
    total = sum(weights, start=Fraction(0))
    preserved, flag = split_blocks(x, [preserved_dim, size])
    trace_mu = sum(
        (
            weights[index] * real_part(entry, "a flag-block diagonal entry")
            for index, entry in enumerate(flag_diagonal(flag))
        ),
        start=Fraction(0),
    )
    noisy = add(scale(1 - total, flag), scale(trace_mu, identity(size)))
    return direct_sum([preserved, noisy])


def transported_cutoff_projectors(
    preserved_dim: int, alphabet_size: int
) -> tuple[Matrix, Matrix]:
    """Eq. ``eq:transportproj``: the pair ``(Pi_{<=N}, Pi_Flag)`` on ``Q``.

    Proposition ``prop:chain`` (i) transports them to ``(Pi_{<=N}, Pi_{>N})`` on
    ``B``, under BOTH ``Lambda^WP`` and ``Lambda^FSS``: at ``X = Pi_{<=N}`` the
    flag term of Eq. ``eq:WPadjoint`` vanishes and the preserved block passes
    through; at ``X = Pi_Flag`` the preserved block vanishes and the flag term is
    ``sum_v M'_v = 1``. Both pull-backs are POSITIVE though NEITHER IS A MULTIPLE
    OF THE IDENTITY, which is what admits the default pair on the trivial
    certificate ``(c = 0, >=)``.

    THE WHOLE-SPACE RENDERING, AND ON NO EMISSION PATH. What the instance
    transports and what an entry carries are sector-block lists, read on the
    sector map by
    :meth:`~certiqs_key.reductions.sectors.SectorSet.block_projector`
    (spec/architecture.md 2.8-2.9). This pair is the ``d_Q x d_Q`` rendering of that
    same operator, for a whole-space computation -- a pull-back through
    :func:`wp_adjoint`, a frozen dense comparison -- exactly as
    :meth:`~certiqs_key.reductions.sectors.SectorSet.dense_projectors` is, and
    nothing under ``src/`` emits it.
    """
    total = preserved_dim + alphabet_size
    preserved = direct_sum([identity(preserved_dim), zeros(alphabet_size)])
    flag = direct_sum([zeros(preserved_dim), identity(alphabet_size)])
    if len(preserved) != total or len(flag) != total:  # pragma: no cover
        raise MalformedInputError("inconsistent target dimension")
    return preserved, flag


def flat_sector_transport(
    sectors: SectorSet,
    *,
    certified_against: str,
    route: Route,
) -> tuple[TransportedOperator, ...]:
    """Proposition ``prop:flat-instance`` (I3): one entry per sector projector.

    (I3) gives the flat instance's transported set as
    ``{Pi_leq, Pi_flag} u {Pi_(m)}_{m<=N} u {Pi_(f)}_{f in V}``, with pull-backs
    ``Pleq``, ``Pgt``, "the photon-number projectors ``P_m^Chan``, and
    ``Mwp_f`` resp. ``blk M^{>N}_f`` read as operators on ``Chan`` supported in
    ``Chan_{>N}``". THIS FUNCTION IS THE SECOND AND THIRD PART; the first is
    :func:`transported_cutoff_projectors`, the two SUMS of sector projectors
    the instance transports besides, which keep their own names.

    THE PULL-BACKS ARE THE PROOF'S OWN COMPUTATION, from the adjoint
    Eq. ``eq:WPadjoint`` at ``X = Pi_(m)`` and at ``X = Pi_(f)``:
    ``Lwp+(Pi_(m)) = P_m^Chan`` and
    ``Lwp+(Pi_(f)) = sum_v <v|f><f|v> Mwp_v = Mwp_f``, the same computation at
    ``p_v = 0`` giving ``blk M^{>N}_f`` for ``Lfss``. ALL THREE ARE POSITIVE,
    being a projector, a positive block and a POVM element respectively, so
    each carries the trivial certificate ``(c = 0, >=)`` of
    ``cor:pullback`` (ii) -- which is what
    ``def:reduction-instance``'s third consequence asserts of every sector
    projector of every instance, without reading the construction.

    NO PULL-BACK IS A MATRIX HERE and none can be: ``P_m^Chan`` is an operator
    on the Fock space ``H(Chan)``, which carries no declared finite dimension
    (``def:system-setting`` permits exactly that), and ``Mwp_f`` and
    ``blk M^{>N}_f`` are built from the above-cutoff blocks THE SUPPLIER
    DOES NOT EMIT. Each is recorded as the claim's expression, which is what
    ``TransportedOperator`` carries a ``pullback_expression`` for.
    """
    licensed = route is Route.LICENSED
    above = "blk M^{>N}" if licensed else "Mwp"
    adjoint = "Lfss+" if licensed else "Lwp+"
    # "At p_v = 0 THE SAME COMPUTATION gives blk M^{>N}_f for Lfss": one
    # adjoint, read at the route's weights (prop:flat-instance (I3)).
    equation = "eq:WPadjoint at p_v = 0" if licensed else "eq:WPadjoint"
    out: list[TransportedOperator] = []
    for sector, projector in zip(sectors.sectors, sectors.projectors(), strict=True):
        name = sector.label[1]
        if sector.kind is SectorKind.DATA:
            pullback = f"P^Chan_{name}"
        else:
            pullback = f"{above}_{name}"
        expression = (
            f"{pullback} (prop:flat-instance (I3): "
            f"{adjoint}(Pi_({name})) = {pullback}, {equation})"
        )
        out.append(
            TransportedOperator(
                label=sector_projector_label(sector.label),
                target_operator=projector,
                pullback=None,
                pullback_expression=expression,
                certificate_kind=CertificateKind.POSITIVITY,
                relation=Relation.GE,
                constant=Fraction(0),
                certified_against=certified_against,
            )
        )
    return tuple(out)


def fss_instance_entry(
    fss_target_element: Sequence[Matrix],
    sectors: SectorSet,
    preserved_dim: int,
    alphabet_size: int,
    weight: Fraction,
    *,
    label: str,
    certified_against: str,
    mode: SourceMode,
) -> ConstraintEntry:
    """Eq. ``eq:fssentry``: ``O^ = F^FSS_o - p_o Pi_Flag``, ``>=``, ``c = 0``.

    Corollary ``cor:fssinstance``, the DEFAULT LICENSED ENTRY. Its pull-back is
    ``Lambda^FSS+(O^) = M_o - p_o Pi_{>N} = blk M^{<=N}_o (+) (blk M^{>N}_o -
    p_o 1) >= 0``, positive "the first summand because ``M_o`` is, and the
    second by Eq. ``eq:certweights``" -- exactly the two sentences of the
    corollary's proof.

    NOTE WHAT IS NOT POSITIVE: ``O^`` itself. Its flag block has the entry
    ``-p_o`` at every outcome other than ``o``, so it is NOT a positive operator
    on ``Q``; what is positive is its pull-back, "which is the whole content of
    the certificate" (Corollary ``cor:pullback`` (ii)). An implementation that
    tested positivity on ``Q`` would refuse the default entry.

    THE ELEMENT ARRIVES AS ITS SECTOR-BLOCK LIST AND SO DOES THE ENTRY, which
    is the one operator form spec/architecture.md 2.8-2.9 admits; the flag
    projector subtracted is ``Pi_Flag`` read on the sector map
    (:meth:`~certiqs_key.reductions.sectors.SectorSet.block_projector`), so
    nothing here writes a ``dim H(Q) x dim H(Q)`` array.
    """
    pi_flag = sectors.block_projector(preserved_dim, alphabet_size)
    operator = tuple(
        subtract(block, scale(weight, flag_block))
        for block, flag_block in zip(fss_target_element, pi_flag, strict=True)
    )
    return ConstraintEntry(
        label=label,
        operator=operator,
        relation=Relation.GE,
        constant=Fraction(0),
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against=certified_against,
        theta_typing=theta_typing(mode, Fraction(0)),
        form=DeclaredForm.HOMOGENEOUS if mode is SourceMode.TRUSTED else None,
    )


def two_sector_entry(
    fss_target_element: Sequence[Matrix],
    sectors: SectorSet,
    preserved_dim: int,
    alphabet_size: int,
    below_cutoff_bound: Fraction,
    above_cutoff_bound: Fraction,
    *,
    label: str,
    certified_against: str,
    mode: SourceMode,
) -> ConstraintEntry:
    """Eq. ``eq:two-sector-entry``: ``O^ = F^FSS_e - a Pi_{<=N} - b Pi_Flag``.

    With ``bowtie = >=`` and ``c = 0``.

    The ``a > 0`` entry of Remark ``rem:published``, whose pull-back is
    ``M_e - a Pi_{<=N} - b Pi_{>N} = (blk M^{<=N}_e - a 1) (+) (blk M^{>N}_e - b 1)
    >= 0`` "by the definitions of ``a`` and ``b`` and the transported projectors
    of Eq. ``eq:transportproj``".

    ``a`` AND ``b`` ARE DECLARED, NOT COMPUTED. The remark defines them as
    minimum eigenvalues, which are in general irrational; what makes the entry
    admissible is not their being minimal but Eq. ``eq:certificate`` holding,
    which is decided exactly. A caller declaring smaller values gets a weaker
    but equally certified entry; one declaring larger values gets
    ``constraint_without_certificate``.

    WHAT MAY NEVER BE EMITTED, transcribed because it is a live hazard: the CAP
    form of the published inequality, ``W <= (p(e) - a)/(b - a)``, "contains the
    run's OBSERVED ``p(e)``, and Assumption A-CONST admits only constants
    declared before the run. The admissible object is the OPERATOR ENTRY
    ``eq:two-sector-entry`` with relation ``>=`` and ``c = 0``, of which the cap is a
    run-time consequence and not a declaration." Nothing here forms a cap.

    BLOCK BY BLOCK, like every operator on ``Q``: the element is its
    sector-block list and the two projectors are read on the sector map.
    """
    pi_leq = sectors.block_projector(0, preserved_dim)
    pi_flag = sectors.block_projector(preserved_dim, alphabet_size)
    operator = tuple(
        subtract(
            subtract(block, scale(below_cutoff_bound, leq_block)),
            scale(above_cutoff_bound, flag_block),
        )
        for block, leq_block, flag_block in zip(
            fss_target_element, pi_leq, pi_flag, strict=True
        )
    )
    return ConstraintEntry(
        label=label,
        operator=operator,
        relation=Relation.GE,
        constant=Fraction(0),
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against=certified_against,
        theta_typing=theta_typing(mode, Fraction(0)),
        form=DeclaredForm.HOMOGENEOUS if mode is SourceMode.TRUSTED else None,
    )


def flat_sectors(
    block_dimensions: Sequence[int], flag_labels: Sequence[str]
) -> SectorSet:
    """Return the flat instance's sectors: the preserved blocks, then the flags.

    ``SecSet_dat = {(C, m) : m <= N}`` with ``d_{(C,m)} = dim H(C_m)``, in
    INCREASING ``m``; ``SecSet_sc = {(C, f) : f in V}``, one-dimensional, in the
    DECLARED ORDER OF ``V``. That is the order the emitted flag basis is written
    in and the order every emitted list inherits; nothing here constructs it.
    """
    if not block_dimensions:
        raise MalformedInputError("the channel grading declares at least one block")
    if not flag_labels:
        raise MalformedInputError("the alphabet is non-empty")
    data = [
        Sector(label=(CHANNEL_GROUP, str(m)), dimension=dim, kind=SectorKind.DATA)
        for m, dim in enumerate(block_dimensions)
    ]
    flags = [
        Sector(label=(CHANNEL_GROUP, name), dimension=1, kind=SectorKind.SCALAR)
        for name in flag_labels
    ]
    return SectorSet(tuple(data + flags))


def flat_scalar_values(
    flag_labels: Sequence[str],
    order: Sequence[JointOutcome],
    weights: Mapping[JointOutcome, Fraction],
    *,
    encoded: bool,
) -> dict[tuple[Label, str], dict[JointOutcome, Fraction]]:
    """Return ``phi_f(v)`` for the flat instance's scalar sectors.

    On the ENCODED route ``phi_f(v) = p_v + (1 - p) delta_{vf}``, which is the
    flag block of Eq. ``eq:WPFSS`` read one basis vector at a time; on the
    LICENSED route ``phi_f(v) = delta_{vf}``, Eq. ``eq:FSS``'s bare projector,
    "in which THE CERTIFIED WEIGHTS ARE NOT ENCODED IN THE TARGET AND TRAVEL
    INSTEAD AS THE CONSTRAINT ENTRY".

    ``1 - p`` IS RECOMPUTED FROM THE EMITTED WEIGHTS AND IS NEVER ROUNDED
    SEPARATELY, "because the flag sector's completeness is the identity
    ``sum_v p_v + (1 - p) = 1`` and ROUNDING BOTH SIDES INDEPENDENTLY WOULD
    BREAK IT". The recomputation is the subtraction below and there is no second
    site.
    """
    total = sum((weights[v] for v in order), start=Fraction(0))
    complement = Fraction(1) - total
    return {
        (CHANNEL_GROUP, name): {
            outcome: (
                (weights[outcome] + (complement if position == index else Fraction(0)))
                if encoded
                else (Fraction(1) if position == index else Fraction(0))
            )
            for position, outcome in enumerate(order)
        }
        for index, name in enumerate(flag_labels)
    }


def flat_instance(
    context: BuildContext,
    *,
    descended: DescendedChannel,
    weights: Mapping[JointOutcome, Fraction],
    route: Route,
) -> ReductionInstance | Refusal:
    """``prop:flat-instance``: the post-processed joint family on the channel.

    The joint post-processed family on ``Chan``, block diagonal at the cutoff
    with the routed certified weights and ``p < 1``, IS a reduction instance:

    * DATA SECTORS ``(m)``, ``m <= N``, with ``A^{(m)}_v = blk M^{=m}_v`` --
      class complete, because each conditional family is complete per photon
      block and step 2 multiplies by ``q_t``;
    * SCALAR SECTORS ``(f)``, ``f in V``, with ``phi_f(v)`` as
      :func:`flat_scalar_values` gives it;
    * HYPOTHESES (H): the above-cutoff blocks form a POVM with the certified
      weights (``prop:route`` through the receiver's facts, A-RECV), UNTOUCHED
      BY THE NORMALIZER -- which is the stability clause here;
    * the channel ``PinS o Lwp`` or ``PinS o Lfss``, with the transported set
      ``{Pi_leq, Pi_flag} u {Pi_(m)}_{m<=N} u {Pi_(f)}_{f in V}`` of (I3): the
      transported PAIR of ``prop:chain`` (i) together with EVERY SECTOR
      PROJECTOR, which ``def:reduction-instance`` (I3) requires of every
      instance (:func:`flat_sector_transport`);
    * ENTRIES: none on the encoded route, ``cor:fssinstance`` on the licensed
      one;
    * the class-marginal identity discharged by ``lem:linear`` (ii).

    THE PHYSICAL SYSTEM IS ``Chan`` ITSELF: no register, no ampliation. See the
    module docstring.
    """
    call = context.request
    artifact_rows = call.artifact_rows
    declaration = call.declaration
    order = declaration.joint_alphabet
    settings = declaration.probe_declaration.settings
    flag_labels = tuple(outcome_label(v, settings) for v in order)
    block_dimensions = artifact_rows.channel_grading.block_dimensions

    sectors = flat_sectors(block_dimensions, flag_labels)
    normalized = context.normalize(
        post_processed_preserved_blocks(
            artifact_rows, declaration.probe_declaration, descended, order
        ),
        sectors.data_dimensions,
        sectors.data_supports,
    )
    scalar_values = flat_scalar_values(
        flag_labels, order, weights, encoded=route is Route.ENCODED
    )
    # (I2)'s family AS THE SECTOR-BLOCK LIST, one square block per sector and
    # no direct sum: "F_v = (+)_s F_v^(s) is what that list MEANS, not an
    # object the artifact carries".
    blocks = assemble_sector_blocks(sectors, normalized.family, scalar_values, order)
    target = tuple(blocks[outcome] for outcome in order)

    preserved_dim = sum(block_dimensions)
    size = len(order)
    witness = ChannelWitness(
        identity="Lambda-wpfss-fss" if route is Route.LICENSED else "Lambda-wpfss-wp",
        equation="prop:flat-instance (I3): P_S o Lambda_C",
        parameters=(
            "Lambda_C=" + ("eq:Lfss" if route is Route.LICENSED else "eq:Lwp"),
            "sector pinching composed last (prop:pinching)",
        ),
    )
    # The two SUMS of sector projectors, as sector-block lists: Eq.
    # eq:transportproj's pair read on the sector map rather than as dense
    # arrays. An ENTRY's operator is a
    # sector-block list too, built from the same pair; the dense rendering of
    # transported_cutoff_projectors is on no emission path.
    pi_leq = sectors.block_projector(0, preserved_dim)
    pi_flag = sectors.block_projector(preserved_dim, size)
    # (I3)'s set, in the proposition's own order: the two SUMS of sector
    # projectors this instance transports besides, then EVERY SECTOR PROJECTOR.
    # The two sums come first because
    # they are what prop:chain (i) transports and what the frozen record of
    # a run pins; the per-sector half is prop:flat-instance (I3)'s
    # second and third parts.
    transported = (
        TransportedOperator(
            label="Pi_leq",
            target_operator=pi_leq,
            pullback=None,
            pullback_expression="Pi_{<=N} (eq:transportproj)",
            certificate_kind=CertificateKind.POSITIVITY,
            relation=Relation.GE,
            constant=Fraction(0),
            certified_against=witness.identity,
        ),
        TransportedOperator(
            label="Pi_flag",
            target_operator=pi_flag,
            pullback=None,
            pullback_expression="Pi_{>N} (eq:transportproj)",
            certificate_kind=CertificateKind.POSITIVITY,
            relation=Relation.GE,
            constant=Fraction(0),
            certified_against=witness.identity,
        ),
        *flat_sector_transport(
            sectors, certified_against=witness.identity, route=route
        ),
    )

    module_built: list[ConstraintEntry] = []
    if route is Route.LICENSED:
        for index, outcome in enumerate(order):
            weight = weights[outcome]
            if weight == 0:
                # At p_o = 0 the entry degenerates to F^FSS_o >= 0, which is
                # true of every target element and constrains nothing, so
                # emitting it would add a licence obligation for no content.
                continue
            module_built.append(
                restricted_entry(
                    target[index],
                    sectors,
                    (0, preserved_dim + size),
                    (preserved_dim, size),
                    weight,
                    label=f"F^FSS_{flag_labels[index]} - {weight} Pi_flag",
                    certified_against=witness.identity,
                    mode=declaration.source_mode,
                )
            )

    requested = certify_carried_operators(
        call.request.carried_operators,
        source_mode=declaration.source_mode,
        probe=declaration.probe_declaration,
        target_povm=target,
        order=order,
        sectors=sectors,
        branch=(0, preserved_dim + size),
        data_part=(0, preserved_dim),
        flag_part=(preserved_dim, size),
        weights=weights,
        lattice_exponent=context.lattice_exponent or 0,
        default_carried=tuple(
            (operator.label, operator.target_operator) for operator in transported
        ),
        # wpfss/cor:two-sector-decided states the two-sector entry's decided
        # certificate for THIS instance, the flat instance on the licensed
        # route; a request reaches here only on that route.
        two_sector_claim=TWO_SECTOR_DECIDED_CLAIM,
        instance_labels=tuple(entry.label for entry in module_built),
    )
    carried_refusal = requested if isinstance(requested, Refusal) else None
    certified: tuple[CertifiedEntry, ...] = (
        () if isinstance(requested, Refusal) else requested
    )

    displaced = any(snap.displacement_squared > 0 for snap in normalized.blocks)
    # The station's party, by name, for the bindings that name it.
    party = party_name(declaration.party_label)
    return ReductionInstance(
        sectors=sectors,
        normalized=normalized,
        scalar_values=scalar_values,
        target_povm=target,
        witness=witness,
        transported=transported,
        entries=tuple(module_built) + tuple(item.entry for item in certified),
        module_built=tuple(entry.label for entry in module_built),
        module_built_locators={
            entry.label: FSS_INSTANCE_LOCATOR for entry in module_built
        },
        requested_locators={item.entry.label: item.locator for item in certified},
        requested_writings={
            item.entry.label: item.writing
            for item in certified
            if item.writing is not None
        },
        constant_rounding={
            item.entry.label: item.rounding
            for item in certified
            if item.rounding is not None
        },
        supplier_free_entries=frozenset(
            item.entry.label for item in certified if not item.reads_supplier
        ),
        carried_operator_refusal=carried_refusal,
        hypotheses=(
            "the above-cutoff blocks form a POVM with the certified weights of "
            "eq:certweights, imported under A-RECV, and the normalizer never "
            "reads one",
            "the descended dark-count matrix is exactly column-stochastic and "
            "absorbing at every bounded letter (the wpfss rows decide both on "
            "declared data)",
        ),
        source_descriptor=SourceDescriptor(
            channel_grading=artifact_rows.channel_grading,
            branch_register=None,
            description=(
                "B = C: the channel Fock space with its declared photon-number "
                "grading, and no register"
            ),
        ),
        physical_family_description=(
            "B = C: the channel Fock space with its declared photon-number "
            "grading; the POVM is not materialisable because the supplier emits "
            "no above-cutoff block"
        ),
        target_descriptor=TargetDescriptor(
            sectors=sectors,
            dimension=sectors.total_dimension,
            # THE DECLARED PARTY OF THE INSTANCE, Bob's where the declaration
            # carries no label -- which is every declaration of this
            # repository, so the emitted sentence is the accepted one word for
            # word (def:reduction-instance (I2); thm:emit (ii)).
            party_partition=party_partition_statement(declaration.party_label),
            dimension_formula="sum_{m<=N} dim H(C_m) + |V| (prop:flat-instance)",
            space_formula="H(Q) = H(C_<=N) (+) H(Flag) (eq:WPFSS, eq:FSS)",
        ),
        exact_identity=ExactIdentity(
            statement="Lambda^dagger(F_v) = M'_v for every v in V",
            holds_by=(
                "Corollary cor:emitted-flat with thm:emit (iii): exactly, with "
                "no error term, for the DECLARED model of def:emitnorm"
            ),
            emission_snap_disposition=(
                ""
                if not displaced
                else (
                    "THE EMISSION NORMALIZER ACTED. The identity is asserted of "
                    "M', THE DECLARED POST-PROCESSED FAMILY ON C, and it is an "
                    "identity ON C with no ampliation. status = exact is "
                    "truthful PRECISELY BECAUSE THE IDENTITY IS RE-ESTABLISHED "
                    "FOR M' rather than asserted of a construction the artifact "
                    "does not carry (rem:emitclaim). The per-sector "
                    "displacement Delta_s is in emission_record; NO BOUND "
                    "RELATING A KEY LENGTH COMPUTED FROM THE EMITTED "
                    "DECLARATION TO ONE COMPUTED FROM ANY OTHER FAMILY IS "
                    "ASSERTED (thm:emit (v))"
                )
            ),
        ),
        reachable_set_statement=(
            "S^rch = { (id_{A^n} (x) Lambda^{(x)n} (x) id_E)(rho) : rho in "
            "S^ph_E } for the emitted Lambda and the declared family of "
            "physical inputs (Definition def:sound, Eq. eq:reachable); the "
            "sound families this artifact asserts are those of Corollary "
            "cor:transported case (i), every one of which holds on EVERY "
            "reachable state"
        ),
        weight_record=WpfssData(
            flag_basis=tuple(order),
            weights=tuple(weights[outcome] for outcome in order),
            cutoff=declaration.photon_cutoff,
            total=sum((weights[outcome] for outcome in order), start=Fraction(0)),
            encoded_in_target=route is Route.ENCODED,
        ),
        weights=weights,
        # No row for the adversary's registers: their dimension is declared
        # nowhere and no claim assumes it. The target's dimension is decided
        # data of def:system-setting, which is a definition and no ledger row.
        ledger_rows={
            # THE STATION'S PARTY, BY NAME: this row is emitted on every
            # station, Alice's included. It names the instance's declared party
            # (Bob where none is declared), not a singular role noun, because a
            # run has two stations. The name decides nothing.
            AssumptionId.A_MEAS: (
                (f"{party}'s device enters through one POVM", "declared"),
            ),
            # A-ROUND-SQ is a premise about the device (reductions/ass:round):
            # one physical POVM
            # for every round, no memory across rounds. The declared model and
            # the squashing channel are this module's own objects, one for
            # every round by req:round-homogeneous-emission, so the binding
            # does not name them. The station's party by name, like A-MEAS.
            AssumptionId.A_ROUND_SQ: (
                (
                    f"{party}'s physical POVM",
                    "one for every round, no memory across rounds",
                ),
            ),
            AssumptionId.A_RECV: (
                (
                    "receiver mathematical_spec_version",
                    artifact_rows.mathematical_spec_version,
                ),
                ("bound_evaluation", artifact_rows.bound_evaluation),
                ("photon_cutoff N", str(declaration.photon_cutoff)),
            ),
            AssumptionId.A_PROBE: tuple(
                (f"q_{setting}", str(declaration.probe_declaration.weights[setting]))
                for setting in declaration.probe_declaration.settings
            ),
            AssumptionId.A_TSM: (("test_statistics_model", "output_state"),),
            # A-SEQ is the transmitter's `ass:seq`, which
            # `def:protocol` declares -- the round's public messages follow
            # every measurement of the round -- and it is emitted
            # unconditionally, the number of measuring parties not being a
            # datum that definition reads. No claim of this module
            # rests on the source segment being empty (there is no A-NOSRC row),
            # and whether it is empty is DATA in the emitted `reduction_chain`.
            AssumptionId.A_SEQ: (
                (
                    "round order",
                    "every measurement of the round precedes the round's "
                    "public messages (transmitter/ass:seq, def:protocol)",
                ),
                # Readable as the systems this station measures, its party named.
                ("measured system", f"the systems {party}'s station measures"),
            ),
            # Bound only where the row is emitted: A-CONST is present where the
            # emitted constraint list is non-empty (req:assumption-ledger), so
            # on the encoded route, which emits none, nothing reads this.
            AssumptionId.A_CONST: (
                ("route", route.value),
                (
                    "constants c_k",
                    "0 (cor:fssinstance)"
                    if route is Route.LICENSED
                    else "none emitted",
                ),
            ),
        },
        extra_assumptions=(),
        squashing_kinds=frozenset({LinkKind.WPFSS, LinkKind.FSS}),
        route_bound_kinds=frozenset({LinkKind.WPFSS, LinkKind.FSS}),
        expected_squashing_kind=(
            LinkKind.FSS if route is Route.LICENSED else LinkKind.WPFSS
        ),
    )


# ---------------------------------------------------------------------------
#  The flat instance of a normalized station: cor:normalized-flat
# ---------------------------------------------------------------------------

#: The identity of the pure-loss channel's witness, the channel the
#: precomposed instance of a normalized station applies FIRST.
PURE_LOSS_IDENTITY: Final[str] = "Lambda-loss"


@dataclass(frozen=True)
class PureLossWitness(ChannelWitness):
    """The witness of ``Lambda^loss_t``, with ``t`` recorded under ``factored_loss``.

    ``receiver/detector-imperfections/def:pure-loss``: every channel mode
    through a beamsplitter of transmittance ``t`` with vacuum in its other
    input, the reflected light discarded. Like every witness it is a record
    and not evaluable data; Requirement ``req:normalized-link-record`` (i)
    asks that it carry ``t`` under ``factored_loss``, exactly, which the
    machine record adds beside the generic keys.
    """

    factored_loss: Fraction = field(default=Fraction(1), kw_only=True)

    def as_machine_record(self) -> dict[str, object]:
        """Return the generic witness record with ``factored_loss`` beside it."""
        return {**super().as_machine_record(), "factored_loss": str(self.factored_loss)}


def normalized_precomposition(factored_loss: Fraction) -> Precomposition:
    """Return the loss a normalized station's flat instance is precomposed with.

    Corollary ``cor:normalized-flat``: the flat instance built on the
    normalized station at the factored loss ``t``, precomposed with
    ``Phi = Lambda^loss_t``, is a reduction instance for the receiver itself,
    with the flat instance's datum, sectors, scalar values, target,
    transported set, entries, constants and class-marginal flag (item (i)),
    and Theorem ``thm:emit`` holds of it with the normalized emission and the
    channel ``Lambda o Phi`` (item (ii)). Requirement
    ``req:normalized-link-record`` names the four slots of the link that
    change, and this record is what fills them through
    :func:`~certiqs_key.reductions.instance.precompose`:

    (i) the channel witness, the flat instance's preceded by the pure-loss
        channel on the channel modes, ``t`` under ``factored_loss``;
    (ii) the source family, the receiver's measurement, which is the
        pull-back through the loss of the normalized station's
        (``receiver/detector-imperfections/prop:efficiency-normalization``);
    (iii) each pull-back of the carried tuple through ``Lambda^loss_t^dagger``;
    (iv) the reachable-set statement, the composite channel's
        (``reductions/def:sound``).

    The target, routed weights, transported operators, entries, constants,
    certificate cases and licence are not touched: they are the flat
    instance's, unchanged.
    """
    if not 0 < factored_loss < 1:
        raise MalformedInputError(
            "a flat instance is precomposed with the pure-loss channel only at a "
            f"factored loss in (0, 1); got {factored_loss}"
        )
    return Precomposition(
        witness=PureLossWitness(
            identity=PURE_LOSS_IDENTITY,
            equation=(
                "Lambda^loss_t: pure loss of transmittance t on every channel "
                "mode, vacuum in the other input, the reflected light discarded "
                "(receiver/detector-imperfections/def:pure-loss)"
            ),
            parameters=(f"t = {factored_loss}", "on the channel modes Inp_C"),
            factored_loss=factored_loss,
        ),
        adjoint="Lambda^loss_t^dagger",
        source_family_description=(
            "B = C: the channel Fock space with its declared photon-number "
            "grading; the source family is the RECEIVER'S measurement, the "
            "pull-back (Lambda^loss_t)^dagger of the normalized station's at "
            f"factored loss t = {factored_loss} "
            "(receiver/detector-imperfections/prop:efficiency-normalization; "
            "cor:normalized-flat); the POVM is not materialisable because the "
            "supplier emits no above-cutoff block"
        ),
        reachable_set_statement=(
            "{ ((Lambda o Lambda^loss_t) (x) id)(rho) : rho in S^ph }, "
            "Definition def:sound for the composite channel: the pure-loss "
            f"channel of transmittance t = {factored_loss} on the channel "
            "modes, then the flat instance's channel (cor:normalized-flat (i))"
        ),
    )
