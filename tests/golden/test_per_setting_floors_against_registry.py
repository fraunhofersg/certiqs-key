"""The per-setting multi-click floors, against the hand-derived registry.

The receiver (receiver, reductions/wpfss) emits
the multi-click floor of each probe setting as guaranteed content
(``thm:emitted-bound`` Eq. ``eq:pmcsetting``, ``def:slot``), and the wpfss weight
route forms the weight of a joint letter ``(y_i, t)`` from the floor of its own
setting (``def:weight-route`` Eq. ``eq:weightroute``, ``prop:route``,
``rem:minweight``). Every expected value is the one frozen in
``tests/oracles/registry_per_setting_floors.py``, derived by hand from the claim
files and never from this code (PRINCIPLES.md 2.3).

THREE GROUPS HERE; the fourth, PSF-C (the ideal passive BB84 receiver with
a probe source), is ``test_per_setting_floors_led_against_registry.py``, which goes
with the removable probe-conditioning submodule.

* PSF-A/B -- the weight route on the registry's toy slots: the routed weights
  per case and per ``kappa``, EXACTLY; zero elsewhere; the uniform special case
  number for number; one case end to end through ``reduce_flat``.
* THE SLOT ROW -- the settings match, per-setting non-negativity and sum, and
  the refusal of an artifact whose receiver version does not state the
  per-setting weights (the wpfss interface key
  ``requires_a_receiver_version_stating_them``; ``req:supplier-version``).
* BIT-IDENTITY -- the probe-free instances (optical_bb84, decoy_bb84, bbm92)
  emit exactly the numbers of the ``t``-uniform route (``rem:minweight``, last
  paragraph).
"""

from __future__ import annotations

import importlib
from fractions import Fraction

import pytest
from reductions_support import RECEIVER_LEDGER_KEYS
from registry_per_setting_floors import (
    PER_SETTING_ROUTE_CASES,
    PerSettingRouteCase,
    lattice_floor,
)

from certiqs_key.foundations.exact import matrix
from certiqs_key.receiver.artifact import (
    FIRST_VERSION_STATING_THE_PER_SETTING_WEIGHTS,
    MATHEMATICAL_SPEC_VERSION,
)
from certiqs_key.receiver.docking import receiver_artifact_rows
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    ChannelGrading,
    HighPhotonBound,
    InheritedAssumption,
    LinkDeclaration,
    ProbeDeclaration,
    ProtocolDeclaration,
    ReceiverArtifactRows,
    ReductionCall,
    ReductionRequest,
    canonical_coarse_graining,
    product_form_dark_counts,
)
from certiqs_key.reductions.reasons import (
    LinkKind,
    LinkStage,
    RefusalReason,
    SourceMode,
)
from certiqs_key.reductions.wpfss import reduce_flat
from certiqs_key.reductions.wpfss.validation import (
    receiver_version_states_the_per_setting_weights,
    rule_high_photon_slot,
)
from certiqs_key.reductions.wpfss.weights import (
    bounded_letters,
    descend,
    minimum_off_letter_rate,
    weight_route,
)

F = Fraction


# ===========================================================================
#  PSF-A / PSF-B -- the weight route on the registry's toy slots
# ===========================================================================


def _coarse() -> object:
    """Return the K = 2 canonical alphabet (nc, c1, c2, mc) of every route case."""
    return canonical_coarse_graining(
        2, empty_letter="nc", single_letters={1: "c1", 2: "c2"}, multiclick_letter="mc"
    )


def _raw_channel(case: PerSettingRouteCase) -> object:
    """Return the raw R the case descends from: identity, or the product form."""
    if case.r_min == 0:
        return product_form_dark_counts(2, {1: F(0), 2: F(0)})
    return product_form_dark_counts(2, {1: F(1, 2), 2: F(1, 4)})


def _route(
    case: PerSettingRouteCase, kappa: int, *, uniform: bool = False
) -> dict[tuple[str, str], Fraction]:
    """Eq. ``eq:weightroute`` for the case's slot (or its uniform weight) at kappa."""
    coarse = _coarse()
    descended = descend(_raw_channel(case), coarse)  # type: ignore[arg-type]
    assert descended is not None
    settings = tuple(setting for setting, _ in case.settings)
    fibre = coarse.fibre(case.bounded_letter)  # type: ignore[attr-defined]
    bound = (
        HighPhotonBound.uniform(fibre, case.uniform_weight, settings)
        if uniform
        else HighPhotonBound(outcome_set=fibre, per_setting=case.slot_weights)
    )
    letters = bounded_letters((bound,), coarse, descended)  # type: ignore[arg-type]
    assert letters is not None
    joint = tuple((y, t) for t in settings for y in case.letters)
    weights = weight_route(
        letters,
        ProbeDeclaration(settings=settings, weights=dict(case.settings)),
        joint,
        lattice_exponent=kappa,
    )
    assert weights is not None
    return weights


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    "case", PER_SETTING_ROUTE_CASES, ids=lambda case: str(case.case_id)
)
def test_the_descended_matrix_and_r_min_are_the_frozen_ones(
    case: PerSettingRouteCase,
) -> None:
    """``lem:descent`` and ``r_min`` of Eq. ``eq:weightroute``, on the case's R."""
    coarse = _coarse()
    descended = descend(_raw_channel(case), coarse)  # type: ignore[arg-type]
    assert descended is not None
    for column, entries in case.descended_matrix:
        for row, value in entries:
            assert descended.value(row, column) == value, (row, column)
    assert descended.is_absorbing_at(case.bounded_letter)
    assert minimum_off_letter_rate(descended, case.bounded_letter) == case.r_min


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    "case", PER_SETTING_ROUTE_CASES, ids=lambda case: str(case.case_id)
)
def test_the_routed_weights_are_the_frozen_ones_per_kappa(
    case: PerSettingRouteCase,
) -> None:
    """O-PSF-ROUTE: each joint letter's weight is formed from ITS OWN SETTING's floor.

    EXACT equality of the routed weight at each ``(mc, t)``, of ``p`` and of
    ``1 - p`` per case and per ``kappa`` (the floor of Eq. ``eq:latdown``, never
    a rounding to nearest), zero at every other joint letter; and the unrounded
    weights of Eq. ``eq:weightroute`` at a lattice fine enough to hold them.
    """
    settings = tuple(setting for setting, _ in case.settings)
    for kappa, frozen, total in case.floored:
        weights = _route(case, kappa)
        expected = dict(frozen)
        for (y, t), weight in weights.items():
            assert weight == expected.get((y, t), F(0)), (kappa, y, t)
        assert sum(weights.values(), F(0)) == total, kappa
        assert 1 - sum(weights.values(), F(0)) == 1 - total
        for (y, t), weight in expected.items():
            assert weight == lattice_floor(
                dict(case.unrounded_weights)[(y, t)], kappa
            )
            del y, t
    unrounded = _route(case, 53)
    assert {v: w for v, w in unrounded.items() if w} == {
        v: w for v, w in case.unrounded_weights if w
    }
    assert sum(unrounded.values(), F(0)) == case.unrounded_total
    assert set(unrounded) == {(y, t) for t in settings for y in case.letters}


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    "case", PER_SETTING_ROUTE_CASES, ids=lambda case: str(case.case_id)
)
def test_the_uniform_route_is_the_special_case_and_weakly_smaller(
    case: PerSettingRouteCase,
) -> None:
    """O-PSF-UNIFORM: ``rem:minweight``'s comparison and its special case.

    The route handed the entry's UNIFORM weight ``min_t p_i^(t)`` at every
    setting gives the frozen uniform-route weights; the per-setting route is at
    least as large at every joint letter and gains exactly the frozen
    ``sum_t q_t (1 - r_min)(p^(t) - p_i)``; where the floors are equal (and at
    one setting) the two routes give the same numbers, entry for entry.
    """
    per_setting = _route(case, 53)
    uniform = _route(case, 53, uniform=True)
    assert {v: w for v, w in uniform.items() if w} == {
        v: w for v, w in case.uniform_route_weights if w
    }
    for outcome, weight in per_setting.items():
        assert weight >= uniform[outcome], outcome
    gain = sum(per_setting.values(), F(0)) - sum(uniform.values(), F(0))
    assert gain == case.per_setting_gain
    if len({weight for _, weight in case.slot_weights}) == 1:
        assert per_setting == uniform
        for kappa, _, _ in case.floored:
            assert _route(case, kappa) == _route(case, kappa, uniform=True)


SUPPLIER_LEDGER = tuple(
    InheritedAssumption(machine_key=key) for key in RECEIVER_LEDGER_KEYS
)


def _toy_call(
    case: PerSettingRouteCase,
    kappa: int,
    *,
    version: str = MATHEMATICAL_SPEC_VERSION,
    bounds: tuple[HighPhotonBound, ...] | None = None,
) -> ReductionCall:
    """Return the case's slot as a full receiver-row declaration at N = 0.

    The vacuum never clicks (``M_{nc|t}^(0) = 1``), so the blocks are an exact
    POVM at each setting; the dark counts are the case's product form.
    """
    coarse = _coarse()
    settings = tuple(setting for setting, _ in case.settings)
    fibre = coarse.fibre(case.bounded_letter)  # type: ignore[attr-defined]
    rows = ReceiverArtifactRows(
        mathematical_spec_version=version,
        detection_alphabet=case.letters,
        photon_blocks={
            (y, t): (matrix([[F(1) if y == "nc" else F(0)]]),)
            for y in case.letters
            for t in settings
        },
        high_photon_bounds=(
            (HighPhotonBound(outcome_set=fibre, per_setting=case.slot_weights),)
            if bounds is None
            else bounds
        ),
        bound_quantifier_domain=BoundQuantifierDomain(cutoff=0, settings=settings),
        dark_count_channel=_raw_channel(case),  # type: ignore[arg-type]
        outcome_coarse_graining=coarse,  # type: ignore[arg-type]
        bound_evaluation="floating_point",
        channel_grading=ChannelGrading(block_dimensions=(1,)),
        validation_results_present=True,
        declared_device_family=(),
        occupation_basis_order=(),
        inherited_assumption_ledger=SUPPLIER_LEDGER,
    )
    declaration = ProtocolDeclaration(
        probe_declaration=ProbeDeclaration(
            settings=settings, weights=dict(case.settings)
        ),
        detection_alphabet=case.letters,
        photon_cutoff=0,
        source_mode=SourceMode.UNTRUSTED,
        joint_alphabet=tuple((y, t) for t in settings for y in case.letters),
    )
    request = ReductionRequest(
        link_declarations=(
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.WPFSS),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
        route="encoded",
        accepted_receiver_versions=(version,),
        requested_assurance="estimate",
        lattice_exponent=kappa,
    )
    return ReductionCall(rows, declaration, request)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    "case",
    [case for case in PER_SETTING_ROUTE_CASES if len(case.settings) == 2],
    ids=lambda case: str(case.case_id),
)
def test_the_per_setting_route_end_to_end_emits_the_frozen_weights(
    case: PerSettingRouteCase,
) -> None:
    """``cor:emitted-flat`` on the case's slot: the emitted weights are frozen ones.

    Through ``reduce_flat`` at the case's finest frozen ``kappa`` up to 40 (the
    admissible lattice exponents of the ``lattice_exponent`` row): the emitted
    certified weights, their total and the flag values ``p_v + (1 - p)
    delta_{vf}`` of Eq. ``eq:flat-scalars`` at the bounded letter.
    """
    kappa, frozen, total = max(
        (row for row in case.floored if row[0] <= 40), key=lambda row: row[0]
    )
    outcome = reduce_flat(_toy_call(case, kappa))
    assert outcome.emitted, outcome.refusal
    artifact = outcome.artifact
    assert artifact is not None
    emitted = dict(
        zip(artifact.wpfss_data.flag_basis, artifact.wpfss_data.weights, strict=True)
    )
    expected = dict(frozen)
    assert emitted == {v: expected.get(v, F(0)) for v in emitted}
    assert artifact.wpfss_data.total == total


# ===========================================================================
#  The slot row, per setting, and the receiver version it reads
# ===========================================================================


def _two_setting_case() -> PerSettingRouteCase:
    return next(case for case in PER_SETTING_ROUTE_CASES if case.case_id == "PSF-2S-R0")


@pytest.mark.contract
def test_the_slot_row_refuses_every_per_setting_malformation() -> None:
    """The ``high_photon_slot`` row as amended by B1b, one refusal per clause.

    Settings not exactly T (missing, extra, repeated), a negative weight at one
    setting, a sum above one at one setting -- each refused
    ``high_photon_slot_ill_formed``, the row's one reason; the well-formed
    per-setting slot is admitted.
    """
    case = _two_setting_case()
    fibre = _coarse().fibre(case.bounded_letter)  # type: ignore[attr-defined]
    settings = ("off", "on")
    good = HighPhotonBound(outcome_set=fibre, per_setting=case.slot_weights)
    assert rule_high_photon_slot((good,), settings, MATHEMATICAL_SPEC_VERSION) is None
    malformed = {
        "missing-setting": (
            HighPhotonBound(outcome_set=fibre, per_setting=(("off", F(1, 2)),)),
        ),
        "extra-setting": (
            HighPhotonBound(
                outcome_set=fibre,
                per_setting=(("off", F(1, 2)), ("on", F(3, 4)), ("dim", F(0))),
            ),
        ),
        "repeated-setting": (
            HighPhotonBound(
                outcome_set=fibre, per_setting=(("off", F(1, 2)), ("off", F(1, 2)))
            ),
        ),
        "negative-at-one-setting": (
            HighPhotonBound(
                outcome_set=fibre, per_setting=(("off", F(1, 2)), ("on", F(-1, 8)))
            ),
        ),
        "sum-above-one-at-one-setting": (
            HighPhotonBound(
                outcome_set=fibre, per_setting=(("off", F(1, 4)), ("on", F(3, 4)))
            ),
            HighPhotonBound(
                outcome_set=frozenset({frozenset({1})}),
                per_setting=(("off", F(1, 4)), ("on", F(1, 2))),
            ),
        ),
    }
    for name, bounds in malformed.items():
        refusal = rule_high_photon_slot(bounds, settings, MATHEMATICAL_SPEC_VERSION)
        assert refusal is not None, name
        assert refusal.reason is RefusalReason.HIGH_PHOTON_SLOT_ILL_FORMED, name


@pytest.mark.contract
@pytest.mark.parametrize(
    "version",
    ["receiver@0.1.2", "receiver@0.1.0", "receiver-povm@0.3.0", "receiver@0.2.0-draft"],
)
def test_an_artifact_of_a_version_not_stating_the_weights_is_refused(
    version: str,
) -> None:
    """``req:supplier-version``: per-setting weights only from a version stating them.

    The wpfss interface key ``requires_a_receiver_version_stating_them``: at a
    receiver version that does not state them the per-setting values are the
    content of no claim, so they are not read -- the artifact is REFUSED
    ``high_photon_slot_ill_formed``, not read at its uniform weight.
    Refused even where the caller lists the version as accepted, and even
    for a probe-free artifact whose one weight is the one
    the route would read: the claim it would be read under is not the claim the
    import quotes.
    """
    assert not receiver_version_states_the_per_setting_weights(version)
    case = _two_setting_case()
    refused = reduce_flat(_toy_call(case, 4, version=version))
    assert not refused.emitted
    assert refused.refusal is not None
    assert refused.refusal.reason is RefusalReason.HIGH_PHOTON_SLOT_ILL_FORMED
    one = next(c for c in PER_SETTING_ROUTE_CASES if c.case_id == "PSF-1S-R0")
    probe_free = reduce_flat(_toy_call(one, 1, version=version))
    assert not probe_free.emitted
    assert probe_free.refusal is not None
    assert probe_free.refusal.reason is RefusalReason.HIGH_PHOTON_SLOT_ILL_FORMED
    # The same declarations at the version that states them are emitted.
    assert reduce_flat(_toy_call(case, 4)).emitted
    assert reduce_flat(_toy_call(one, 1)).emitted


@pytest.mark.contract
def test_the_first_version_stating_the_weights_is_the_supplier_s_own() -> None:
    """The version fact is read from the receiver, which emits it (no copy here)."""
    assert FIRST_VERSION_STATING_THE_PER_SETTING_WEIGHTS == (0, 2, 0)
    assert MATHEMATICAL_SPEC_VERSION == "receiver@0.9.0"
    assert receiver_version_states_the_per_setting_weights(MATHEMATICAL_SPEC_VERSION)
    assert receiver_version_states_the_per_setting_weights("receiver@0.2.1")
    assert receiver_version_states_the_per_setting_weights("receiver@1.0.0")
    assert not receiver_version_states_the_per_setting_weights("receiver")
    assert not receiver_version_states_the_per_setting_weights("reductions@0.12.0")


# ===========================================================================
#  BIT-IDENTITY -- the probe-free instances emit the t-uniform route's numbers
# ===========================================================================


def _probe_free_emissions(instance: str) -> list[tuple[object, object]]:
    """Return ``(receiver artifact, reduction artifact)`` per station of an instance."""
    surface = importlib.import_module(f"instances.{instance}.surface")
    prepared = surface.preparation(surface.default_config())
    if prepared.device_artifacts:
        return [(d.receiver, d.reduction) for d in prepared.device_artifacts]
    return [(prepared.receiver_artifact, prepared.reduction_artifact)]


@pytest.mark.contract
@pytest.mark.parametrize("instance", ["optical_bb84", "decoy_bb84", "bbm92"])
def test_a_probe_free_instance_emits_the_uniform_route_numbers(instance: str) -> None:
    """``rem:minweight``, last paragraph: no probe-free declaration's number moves.

    At ``T = {off}`` the receiver's slot entry has the ONE weight that is its
    uniform weight, the docked entry is exactly the ``t``-uniform one, and
    every emitted certified weight is the t-uniform route's
    ``lat(q_t((1 - r_min,i) p_i + r_min,i))`` -- recomputed here from the
    receiver's uniform weight and the docked dark-count channel, with the floor
    of the domain substrate and not the weight route under test.
    """
    for receiver, reduction in _probe_free_emissions(instance):
        assert receiver is not None and reduction is not None
        entries = receiver.high_photon_bounds.entries  # type: ignore[attr-defined]
        rows = receiver_artifact_rows(receiver)  # type: ignore[arg-type]
        assert isinstance(rows, ReceiverArtifactRows), rows
        assert rows.bound_quantifier_domain.settings == ("off",)
        descended = descend(rows.dark_count_channel, rows.outcome_coarse_graining)
        assert descended is not None
        kappa = reduction.emission_record.lattice_exponent  # type: ignore[attr-defined]
        expected: dict[tuple[str, str], Fraction] = {}
        for entry, bound in zip(entries, rows.high_photon_bounds, strict=True):
            assert entry.per_setting == (("off", entry.weight),)
            assert bound == HighPhotonBound.uniform(
                bound.outcome_set, Fraction(entry.weight), ("off",)
            )
            letter = next(
                y
                for y in rows.outcome_coarse_graining.letters
                if rows.outcome_coarse_graining.fibre(y) == bound.outcome_set
            )
            r_min = minimum_off_letter_rate(descended, letter)
            uniform = Fraction(entry.weight)
            expected[(letter, "off")] = lattice_floor(
                F(1) * ((1 - r_min) * uniform + r_min), kappa
            )
        data = reduction.wpfss_data  # type: ignore[attr-defined]
        emitted = dict(zip(data.flag_basis, data.weights, strict=True))
        for outcome, weight in emitted.items():
            assert weight == expected.get(outcome, F(0)), outcome
        assert reduction.mathematical_spec_version == "reductions@0.21.0"  # type: ignore[attr-defined]
