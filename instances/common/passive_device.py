"""Shared passive receiver reductions and certified Eq. 27 requests.

Extracted from optical BB84 without changing its declarations or record labels.
The caller selects source mode and provenance; no source or protocol is declared
here. Exact certificate checks remain owned by reductions.

A caller with a probe source (:class:`~instances.common.optics.ProbeSource`)
also declares the reductions' probe classes ``T`` with their class weights
``q_t`` and may pass its own reduction entry point; without them the
declaration is the probe-free one.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from fractions import Fraction

import numpy

from certiqs_key.foundations.blocks import JointBlockOperator, SectorStructure
from certiqs_key.foundations.exact import (
    Matrix,
    direct_sum,
    equal,
    identity,
    kron,
    loewner_ge,
    matrix,
    scale,
    spectral_bounds,
    subtract,
)
from certiqs_key.foundations.snap import SnapSettings
from certiqs_key.reductions import docking as reductions_docking
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.constraints import ConstraintEntry
from certiqs_key.reductions.inputs import (
    CarriedOperatorRequest,
    ConstraintForm,
    LinkDeclaration,
    ProbeDeclaration,
    ReductionRequest,
)
from certiqs_key.reductions.inputs import ProtocolDeclaration as ReductionDeclaration
from certiqs_key.reductions.reasons import (
    CertificateKind,
    LinkKind,
    LinkStage,
    Relation,
    SourceMode,
)
from certiqs_key.reductions.wpfss import reduce_flat
from certiqs_key.reductions.wpfss.construction import transported_cutoff_projectors
from certiqs_key.runs.pipeline import (
    CarriedOperatorProvider,
    DeviceRequests,
    ReductionEntry,
)
from instances.common.declare import rows_adapter
from instances.common.errors import OpticalDeviceError
from instances.common.optics import (
    RAW_LETTERS,
    ProbeSource,
    ReceiverParameters,
    receiver_request,
)

LATTICE_EXPONENT = 40
#: Both snap parameters at their own defaults: enclosed references used, not
#: strict.
DEFAULT_SNAP_SETTINGS = SnapSettings()
#: The receiver contract versions this instance's declaration is written
#: against: the receiver's accepted version, which states the per-setting
#: multi-click weights (thm:emitted-bound eq:pmcsetting). Widened only by hand,
#: the fail-closed direction.
ACCEPTED_RECEIVER_VERSIONS = ("receiver@0.9.0",)
PROBE_SETTING = "off"
ENCODED = "encoded"
LICENSED = "licensed"
LICENSED_TWO_SECTOR = "licensed+two-sector"
ROUTES = (ENCODED, LICENSED, LICENSED_TWO_SECTOR)


def passive_device_requests(
    parameters: ReceiverParameters,
    *,
    declared_tolerance: float,
    route: str = ENCODED,
    source_mode: SourceMode = SourceMode.TRUSTED,
    declared_by: str = "instances.optical_bb84.declare",
    probe: ProbeSource | None = None,
    setting_weights: Mapping[str, Fraction] | None = None,
    reduction_entry: ReductionEntry = reduce_flat,
    snap: SnapSettings = DEFAULT_SNAP_SETTINGS,
) -> DeviceRequests:
    """Return the three declarations, plus this instance's rows adapter.

    Args:
        parameters: the optics. See
            :class:`~instances.common.optics.ReceiverParameters`.
        declared_tolerance: ``tau``, this instance's ONE declared numerical
            tolerance. REQUIRED, no default: spec/architecture.md 2.8
            gives it none, "because a defaulted ceiling on repair decides a
            security-relevant act on nobody's authority". It reaches exactly one
            place -- the rows adapter, which is this instance's SNAP -- and is
            the CEILING ON THE PRE-SNAP DEFECT that snap may repair. It is not
            ``eps_op``: ``reductions``
            1.0.1 has no tolerance row, and its
            :class:`~certiqs_key.reductions.inputs.ReductionRequest` carries
            :data:`LATTICE_EXPONENT` in that position instead.
        route: which of :data:`ROUTES`. See that constant: the three arms run
            IDENTICAL optics, channel and source, so a difference between two of
            them is a difference between the two reductions and nothing else.
        probe: the probe source, or ``None`` for the probe-free receiver
            (:func:`~instances.common.optics.receiver_request`).
        setting_weights: the reductions' class weights ``q_t`` (Assumption
            A-PROBE), keyed by exactly the probe's settings.
            REQUIRED WITH ``probe`` AND REFUSED WITHOUT IT: a probe-free receiver
            has ``T = {off}`` and ``q_off = 1``, and there is nothing to choose.
            The weights are the caller's PREPARED numbers; ``reductions``
            decides them exactly (positive, on the ``2^-40`` lattice, summing to
            one) and refuses ``probe_weights_ill_formed`` otherwise.
        reduction_entry: the reduction instance the device declares; the flat
            one by default.
        snap: the run's two snap parameters
            (:func:`instances.common.declare.snap_settings` of the run's
            configuration): they reach the receiver construction (whether
            its reference is offered on exact blocks only), this instance's
            snap of its receiver family and the reduction request
            (``reference_enclosure``, ``strict_snaps``), which
            records them. The default is each parameter's own default.

    Raises:
        OpticalDeviceError: on an unknown route. The three names are this
            instance's, not ``reductions``'; that module's own
            ``route_not_single_valued`` refusal is about the string it receives,
            which is only ever one of the two it declares. Also on setting
            weights given without a probe, or a probe without them, or weights
            not keyed by the probe's settings.
    """
    if route not in ROUTES:
        raise OpticalDeviceError(f"the route is one of {list(ROUTES)}; got {route!r}")
    settings: tuple[str, ...] = (PROBE_SETTING,)
    weights: dict[str, Fraction] = {PROBE_SETTING: Fraction(1)}
    if probe is None and setting_weights is not None:
        raise OpticalDeviceError(
            "probe class weights are declared only for a receiver with a probe; "
            "the probe-free receiver has T = {off} and q_off = 1"
        )
    if probe is not None:
        if setting_weights is None or set(setting_weights) != set(probe.settings):
            raise OpticalDeviceError(
                "a receiver with a probe declares one class weight per setting, "
                f"keyed by exactly {list(probe.settings)}; got "
                f"{None if setting_weights is None else sorted(setting_weights)}"
            )
        settings = probe.settings
        weights = {setting: setting_weights[setting] for setting in settings}
    declaration = ReductionDeclaration(
        probe_declaration=ProbeDeclaration(settings=settings, weights=weights),
        detection_alphabet=RAW_LETTERS,
        photon_cutoff=parameters.photon_cutoff,
        # NO BRANCHING-MODEL ROW. A model with branches is a REMOVABLE
        # submodule's, and the core's declaration is five rows. A receiver
        # without branches therefore declares nothing about one, which is
        # what removability means.
        source_mode=source_mode,
        joint_alphabet=tuple(
            (letter, setting) for setting in settings for letter in RAW_LETTERS
        ),
    )
    encoded = route == ENCODED
    return DeviceRequests(
        receiver_request=receiver_request(parameters, probe),
        reduction_declaration=declaration,
        # THE FLAT REDUCTION INSTANCE, DECLARED HERE AND NOT DEFAULTED IN THE
        # RUN TIER. This receiver has no branches, so the instance the
        # chain is built over is ``cor:emitted-flat``'s: the physical system is
        # the channel space itself and no register is amplified into anything.
        # A model with branches is a removable submodule's and the choice an
        # entry point, so a receiver without branches names the flat one; a
        # caller whose device has branches passes their entry.
        reduction_entry=reduction_entry,
        reduction_request=ReductionRequest(
            link_declarations=(
                LinkDeclaration(
                    stage=LinkStage.RECEIVER,
                    kind=LinkKind.WPFSS if encoded else LinkKind.FSS,
                ),
            ),
            route=ENCODED if encoded else "licensed",
            accepted_receiver_versions=ACCEPTED_RECEIVER_VERSIONS,
            requested_assurance="estimate",
            lattice_exponent=LATTICE_EXPONENT,
            strict_snaps=snap.strict,
            reference_enclosure=snap.reference_enclosure,
        ),
        reference_enclosure=snap.reference_enclosure,
        rows_adapter=rows_adapter(
            tolerance=declared_tolerance,
            lattice_exponent=LATTICE_EXPONENT,
            settings=snap,
            declared_by=declared_by,
        ),
        carried_operator_provider=(
            two_sector_provider() if route == LICENSED_TWO_SECTOR else None
        ),
    )


def two_sector_provider() -> CarriedOperatorProvider:
    """Return the provider that asks for Eq. ``eq:two-sector-entry``'s ``a > 0`` entry.

    THE ENTRY IS BUILT FROM THE MODULE'S OWN BASELINE ENTRY, not written from
    scratch beside it. Corollary ``cor:fssinstance`` already emits
    ``O_0 = F^FSS_e - b Pi_Flag >= 0`` on the licensed route with the certified
    weight ``b``; this asks for ``O = O_0 - a Pi_{<=N}``, which is exactly
    Eq. ``eq:two-sector-entry``'s operator carrying THE MODULE'S OWN ``b`` and one
    declared ``a``. So the two licensed arms differ in ``a`` and in nothing
    else, which is what makes the comparison between them a comparison.

    WHY THAT IS THE STRONGER CONSTRAINT, and it is a theorem rather than a hope.
    Remark ``rem:published``: ``O^ = O^|_{a=0} - a Pi_{<=N}`` with ``a >= 0`` and
    ``Pi_{<=N} >= 0``, so ``tr[O^|_{a=0} sigma] >= tr[O^ sigma]`` for every
    ``sigma >= 0`` and the ``a > 0`` entry "cuts the strictly smaller set and is
    the stronger constraint, UNCONDITIONALLY".

    ``a`` IS DECLARED DEVICE DATA AND IS DECLARED CONSERVATIVELY. Remark
    ``rem:published`` defines it as ``lmin(blk M^{<=N}_e)``, an eigenvalue and in
    general irrational; what makes the entry admissible is not its being minimal
    but Eq. ``eq:certificate`` holding, which the module decides EXACTLY -- "a
    caller declaring smaller values gets a weaker but equally certified entry;
    one declaring larger values gets ``constraint_without_certificate``". So this
    proposes a dyadic floor of the floating ``lmin``, accepts it only if the
    module's own exact :func:`~certiqs_key.foundations.exact.loewner_ge` holds, and
    otherwise declares the exact Gershgorin lower bound, which certifies by
    construction. See :func:`_largest_certifiable_floor`.

    ``a`` HOLDS OF THE RECEIVER MODEL AS WELL AS OF THE SNAP. The run forms its
    bound on the reference companion, and the companion carries this entry
    only where ``a`` is certified there too (``reductions/wpfss/
    cor:flat-companion``, Eq. ``eq:companion-two-sector``: every below-cutoff block of
    the companion's centre clears ``a`` by its row-sum radius;
    ``reductions/req:reference-companion`` (iii)). A floor read off the snapped
    block alone can exceed the model's own, the snap having moved the block by
    about the size of ``a`` itself at small dark counts, and the entry would
    then be dropped from the companion. So where the first-pass artefact carries
    a companion, ``a`` is the smaller of the two certifiable floors
    (:func:`_reference_floor`): a device constant true of the model, which is
    what ``rem:published`` asks of it.

    THE ENTRY IS OMITTED, NOT WEAKENED, WHERE ``a`` WOULD BE ZERO. At ``a = 0``
    the request is the baseline entry under a second label, and asking for it
    would add a duplicate rather than a constraint. That is the IDEAL device's
    case and it is not a defect: with unit efficiency and no dark counts, no
    state of at most ``N`` photons can produce a multi-click at all, so
    ``blk M^{<=N}_mc = 0``, ``lmin = 0``, and the published entry has nothing to
    add over the default. The arm separates exactly where a sub-cutoff
    multi-click has nonzero probability -- which is where the dark counts are.
    """

    def build(artifact: ProofReductionArtifact) -> tuple[CarriedOperatorRequest, ...]:
        preserved = artifact.source_descriptor.channel_grading.preserved_dimension
        alphabet = len(artifact.target_povm)
        pi_leq, pi_flag = transported_cutoff_projectors(preserved, alphabet)
        requests: list[CarriedOperatorRequest] = []
        for entry in artifact.constraint_list:
            if (
                entry.certificate_kind is not CertificateKind.POSITIVITY
                or entry.relation is not Relation.GE
                or entry.constant != 0
            ):
                continue
            outcome = _outcome_of_baseline_entry(artifact, entry, pi_flag)
            if outcome is None:
                continue
            block = reductions_docking.preserved_block(
                artifact.target_povm[outcome], preserved
            )
            below = _largest_certifiable_floor(block)
            reference = _reference_floor(artifact, outcome, preserved)
            if reference is not None:
                below = min(below, reference)
            if below == 0:
                continue
            requests.append(
                CarriedOperatorRequest(
                    label=f"{entry.label} - {below} Pi_leq",
                    # THE REQUEST IS WHOLE-SPACE AND THE EMISSION IS PER BLOCK.
                    # An EMITTED entry carries its operator as the sector-block
                    # list of spec/architecture.md 2.9; a REQUESTED one carries
                    # the d_Q x d_Q rendering, which
                    # ``certify_carried_operators`` splits against the sector
                    # map on the way in. So the baseline entry is re-assembled
                    # by ``direct_sum`` before ``a Pi_{<=N}`` is subtracted, and
                    # the pair of projectors is that same rendering
                    # (:func:`transported_cutoff_projectors`).
                    operator=subtract(
                        direct_sum(list(entry.operator)), scale(below, pi_leq)
                    ),
                    relation=Relation.GE,
                    constant=Fraction(0),
                    certificate_kind=CertificateKind.POSITIVITY,
                    certified_against=artifact.squashing_channel.identity,
                    form=ConstraintForm.EXPECTATION,
                )
            )
        return tuple(requests)

    return build


def _outcome_of_baseline_entry(
    artifact: ProofReductionArtifact,
    entry: ConstraintEntry,
    pi_flag: Matrix,
) -> tuple[str, str] | None:
    """Return the outcome whose ``F^FSS_e - b Pi_Flag`` this entry is.

    RECOVERED FROM THE OPERATOR, never parsed out of the label. The module does
    the same on the way back in (``_two_sector_certificate`` recovers ``a`` and ``b``
    from the declared operator rather than trusting them), and a label is a
    string this instance does not own.
    """
    baseline = direct_sum(list(entry.operator))
    for outcome, element in artifact.target_povm.items():
        residual = subtract(direct_sum(list(element)), baseline)
        weight = residual[len(residual) - 1][len(residual) - 1].re
        if equal(residual, scale(weight, pi_flag)):
            return outcome
    return None


def _reference_floor(
    artifact: ProofReductionArtifact, outcome: tuple[str, str], preserved: int
) -> Fraction | None:
    """Return a dyadic ``a >= 0`` the reference companion certifies, or ``None``.

    ``reductions/wpfss/cor:flat-companion``, Eq. ``eq:companion-two-sector``: the
    companion carries the entry where ``C^(m)_e - (a + rho_m) 1 >= 0`` on every
    below-cutoff block ``m``, ``C`` the centre of the companion's recentred
    datum and ``rho_m = max_i sum_l R^(m)_{e,il}``. Per block, the floor of
    :func:`_largest_certifiable_floor` on ``C^(m)_e - rho_m 1``, which that
    function certifies exactly; the smallest over the blocks is returned.
    ``None`` where the artefact carries no companion, which then constrains
    nothing.
    """
    from certiqs_key.reductions.companion import ReferenceCompanion

    companion = artifact.reference_companion
    if not isinstance(companion, ReferenceCompanion):
        return None
    floors: list[Fraction] = []
    remaining = preserved
    for centre, radii in zip(
        companion.target_centre[outcome],
        companion.target_radius[outcome],
        strict=True,
    ):
        if remaining <= 0:
            break
        remaining -= len(centre)
        rho = max((sum(row, Fraction(0)) for row in radii), default=Fraction(0))
        unit = identity(len(centre))
        # Exact by construction: the floor certifies C - rho 1 >= floor 1,
        # which is C >= (floor + rho) 1.
        floors.append(
            _largest_certifiable_floor(subtract(centre, scale(rho, unit)))
        )
    return min(floors, default=Fraction(0))


#: Denominator of the dyadic grid a candidate ``a`` is proposed on. ``2^-40`` is
#: far below every tolerance in this slice, so the floor loses nothing a run
#: could see, and a dyadic constant stays short in the run record.
_DYADIC = 2**40


def _largest_certifiable_floor(block: Matrix) -> Fraction:
    """Return a dyadic ``a >= 0`` this instance can certify ``blk M^{<=N} >= a 1``.

    EXACT THROUGHOUT, AND WITH AN EXACT FALLBACK. The floating eigenvalue only
    PROPOSES a value; what accepts it is the module's own exact Loewner test.
    Where the proposal fails that test, the value declared is instead the
    Gershgorin lower bound :func:`~certiqs_key.foundations.exact.spectral_bounds`
    returns, which is an EXACT RATIONAL LOWER BOUND on the spectrum and so
    certifies by construction. Both branches end in a declared rational the
    module can discharge; neither trusts a float.

    Remark ``rem:published`` calls ``a`` a minimum eigenvalue, but what makes the
    entry admissible is Eq. ``eq:certificate`` holding, not ``a`` being minimal:
    "a caller declaring smaller values gets a weaker but equally certified
    entry". So a loose proposal costs strength and never soundness.
    """
    size = len(block)
    if size == 0:
        return Fraction(0)
    unit = identity(size)
    dense = numpy.array(
        [[complex(entry.re, entry.im) for entry in row] for row in block],
        dtype=complex,
    )
    smallest = float(numpy.linalg.eigvalsh(dense)[0])
    proposed = max(Fraction(math.floor(smallest * _DYADIC), _DYADIC), Fraction(0))
    if proposed > 0 and loewner_ge(block, scale(proposed, unit)):
        return proposed
    guaranteed = spectral_bounds(block).lower
    return max(guaranteed, Fraction(0))


def below_cutoff_witness(
    alice_marginal: Matrix,
    sectors: SectorStructure,
    alice_dim: int,
    preserved: int,
) -> JointBlockOperator:
    """Return ``omega* = tau_A (x) 1_{<=N}/d_{<=N}``, the below-cutoff witness.

    The feasibility witness of one trusted optical station:
    ``alice_marginal`` is the source artefact's ``tau_A`` on ``alice_dim``,
    ``sectors`` the declaration's own sector map, ``preserved`` the preserved
    block's dimension. Public, for
    :func:`instances.common.witness.below_cutoff` and any instance built on
    this station.

    AS A BLOCK LIST, NOT AS A ``d_A d_Q`` ARRAY (0.3.0). Theorem ``thm:feasibility``
    (ii): "The verification of a candidate is finite AND PER BLOCK: NO ARRAY OF
    DIMENSION ``d_A d_Q`` IS FORMED AT ANY POINT". The sector leg of V7 is
    therefore structural and the only thing compared is the map, which is why
    this function is handed the declaration's own
    :class:`~certiqs_key.foundations.blocks.SectorStructure` rather than a
    dimension: a
    witness built against a second map of the same dimensions would be refused
    on the block kind, and correctly.

    THE PRESERVED SUMMAND IS THE LEADING SECTORS AND NOT ONE OF THEM. The
    emitted map carries ``H(C_{<=N})`` PER PHOTON NUMBER, not as a single
    sector (so ``sectors.dims[0]`` is not the preserved dimension) -- for
    ``N = 1`` the sectors are ``(C, 0)`` and ``(C, 1)`` of dimensions 1 and
    2, then one flag sector per emitted letter -- and the preserved
    dimension is their sum. So the state is spread over the leading sectors
    as ``1_{<=N}/d_{<=N}`` restricted to each, which is the same operator
    written on a finer map, and every flag block is the exact zero of its
    own size. That is the presentation of "``Pi_Flag omega* = 0``" rather
    than a claim about it, on either map.

    WHY A WITNESS IS NEEDED AT ALL ON THE LICENSED ROUTES. Theorem ``thm:feasibility``
    (i) proves the compiler's own default ``tau_A (x) 1_Q/d_Q`` feasible only
    for an EMPTY constraint list, and the licensed routes have a non-empty one.
    The maximally mixed target state genuinely fails it here -- it spreads
    ``1/d_Q`` over each flag dimension, where Corollary ``cor:fssinstance``'s
    entry asks for at least the certified weight ``b`` -- so the compiler
    refuses ``no_feasibility_witness``, which Remark ``rem:completeness`` says
    means "I WAS NOT SHOWN A FEASIBLE STATE, never THERE IS NONE". This is what
    it asks to be shown.

    WHY THIS ONE, AND WHY IT DISCHARGES EVERY ENTRY THIS INSTANCE CAN DECLARE.
    The state is supported entirely on the preserved summand, so
    ``Pi_Flag omega* = 0`` and every entry's flag term drops. What is left is
    decided by the SAME inequality that certifies the entry:

    * Corollary ``cor:fssinstance``'s entry ``F_e - b Pi_Flag`` evaluates to
      ``tr[blk M^{<=N}_e] / d_{<=N} >= 0``, because ``F_e >= 0``;
    * Eq. ``eq:two-sector-entry``'s ``F_e - a Pi_{<=N} - b Pi_Flag`` evaluates to
      ``(tr[blk M^{<=N}_e] - a d_{<=N}) / d_{<=N} >= 0``, which is exactly
      ``blk M^{<=N}_e >= a 1`` traced -- the certificate
      :func:`_largest_certifiable_floor` already established EXACTLY.

    So the witness cannot fail an entry this instance declares, and it is not a
    number tuned until the compiler agreed. It is also block-diagonal for the
    declared sectors by construction, being supported in the preserved ones,
    and its Alice marginal is ``tau_A`` because the factor is a state.

    IT IS PHYSICAL, not a formal device: it is the "at most ``N`` photons"
    corner of the target, uniformly mixed. Nothing is claimed about the honest
    state, which this is not; ``def:feasible`` asks for SOME feasible state.
    """
    blocks: list[Matrix] = []
    remaining = preserved
    for dim in sectors.dims:
        if remaining > 0:
            if dim > remaining:  # pragma: no cover - the descriptor fixes it
                raise OpticalDeviceError(
                    f"the preserved dimension {preserved} does not end on a "
                    f"sector boundary of {list(sectors.dims)}"
                )
            blocks.append(
                kron(alice_marginal, scale(Fraction(1, preserved), identity(dim)))
            )
            remaining -= dim
            continue
        size = alice_dim * dim
        blocks.append(matrix(tuple(tuple(0 for _ in range(size)) for _ in range(size))))
    if remaining != 0:  # pragma: no cover - the descriptor fixes it
        raise OpticalDeviceError(
            f"the sector map {list(sectors.dims)} carries fewer than the "
            f"{preserved} preserved dimensions the channel grading declares"
        )
    return JointBlockOperator.of(sectors, alice_dim, blocks)
