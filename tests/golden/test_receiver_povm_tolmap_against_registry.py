"""Definition ``def:tolmap`` and the declared tolerance domain, against the registry.

Golden replay of ``TOLERANCE_DOMAIN_CASES``, ``TOLMAP_I_CASES``,
``TOLMAP_II_RANK_CASES``, ``TOLMAP_IV_C_CASES``,
``TOLMAP_V_CONTRACTIVITY_CASES``, ``C_DIRECTION_CASES`` and ``TOLMAP_ITEMS``
(oracle entry ``O-RP-TOLMAP``), first frozen at registry 0.2.0 (a registry
version is one of tests/oracles/registry_receiver_povm.py, not of this module).

WHAT IS ON TRIAL. Definition ``def:tolmap`` fixes, for each exact admissibility
condition the contract evaluates, WHICH DECLARED TOLERANCE DECIDES IT "and by no
other threshold". The frozen cases come in ADMIT/REFUSE PAIRS that sit exactly
ON the boundary and exactly one declared unit beyond it, so an implementation
that got the side or the strictness of a comparison wrong fails one of the two.

THE FOUR EDGES THIS FILE EXISTS TO CATCH, none of which a looser test would see:

* ``lmin(A_k) = -eps_2`` EXACTLY is ADMITTED -- the comparison is ``>=``;
* ``lambda_i = eps_2`` EXACTLY is NOT COUNTED by Eq. ``eq:eps2rank`` -- the
  comparison inside the count is STRICT, and an implementation using ``>=``
  refuses a declaration the contract admits;
* ``c = -eps_2`` EXACTLY is ADMITTED AND IS NOT CLAMPED -- it enters
  Eq. ``eq:beta`` as it stands, and Remark ``rem:cdirection``'s parity split is
  frozen as four numbers;
* C10's LOSSLESS sub-case is decided TWO-SIDEDLY, so a block that passes the
  one-sided contraction test is NOT thereby lossless.
"""

from __future__ import annotations

from fractions import Fraction as F

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE
from registry_receiver_povm import (
    C_DIRECTION_BOUNDS,
    C_DIRECTION_CASES,
    TOLERANCE_DOMAIN_CASES,
    TOLERANCE_DOMAIN_CLOSED_AT,
    TOLERANCE_FIXTURE_0_3_0,
    TOLERANCES_ALWAYS_REQUIRED_0_3_0,
    TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0,
    TOLERANCES_UNUSED_ON_ROUTE_I,
    TOLMAP_I_CASES,
    TOLMAP_II_RANK_CASES,
    TOLMAP_ITEMS,
    TOLMAP_IV_C_CASES,
    TOLMAP_NOT_A_TEST_0_3_0,
    TOLMAP_OTHER_VALIDATION_KINDS_0_3_0,
    TOLMAP_RESIDUALS_ALREADY_COUNTED,
    TOLMAP_V_CONTRACTIVITY_CASES,
    is_superseded_0_3_0,
    rp_oracle,
)

from certiqs_key.receiver import TOLERANCE_DOMAIN as MODULE_TOLERANCE_DOMAIN
from certiqs_key.receiver import (
    TOLERANCE_KEYS,
    TOLERANCE_KEYS_ALL,
    TOLERANCE_KEYS_CONDITIONAL,
    BoundData,
    GenericBlock,
    GramFamily,
    NumericalTolerances,
    Refusal,
    RefusalReason,
    bound_function,
    check_bound_data,
    check_bound_data_admissible,
    check_gram_family_admissible,
    check_rank_against_port_sizes,
    epsilon_rank,
    tolerance_is_in_declared_domain,
    tolerances_from_declaration,
)
from certiqs_key.receiver.numerics import lambda_max, positive_part, residual_norm


def _diag(*entries: F) -> np.ndarray:
    """Return a real diagonal matrix from exact entries."""
    return np.diag([float(value) for value in entries]).astype(np.complex128)


def _family(*matrices: np.ndarray) -> GramFamily:
    """Return a Gram family labelled ``A_1``, ``A_2``, ..."""
    labels = tuple(f"A_{index + 1}" for index in range(len(matrices)))
    return GramFamily(labels, tuple(matrices))


# ---------------------------------------------------------------------------
#  The declared domain [0, 1)
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_declared_tolerance_domain_is_replayed_case_by_case() -> None:
    """Remark rem:tolerancedomain, with its verbatim refusal."""
    assert rp_oracle("O-RP-TOLMAP").claims == ("RC9",)
    # `TOLERANCE_DOMAIN` -- the registry's 0.2.0 pair -- is marked in
    # SUPERSEDED_BY_0_3_0 as the enumeration of a SIX-member tuple's domain; the
    # interval itself is unchanged and is read off the module's own constant.
    assert is_superseded_0_3_0("TOLERANCE_DOMAIN")
    low, high = MODULE_TOLERANCE_DOMAIN
    assert (low, high) == (0.0, 1.0)
    assert TOLERANCE_DOMAIN_CLOSED_AT == (True, False)
    assert tolerance_is_in_declared_domain(low) is True
    assert tolerance_is_in_declared_domain(high) is False
    for case in TOLERANCE_DOMAIN_CASES:
        declared = dict(TOLERANCE_FIXTURE_0_3_0) | {case.key: case.value}
        outcome = tolerances_from_declaration(declared, False)
        if case.admitted:
            assert not isinstance(outcome, Refusal), case.case_id
            assert case.refusal_reason is None, case.case_id
        else:
            assert isinstance(outcome, Refusal), case.case_id
            assert str(outcome.reason) == case.refusal_reason, case.case_id
        assert tolerance_is_in_declared_domain(float(case.value)) is case.admitted


@pytest.mark.contract
@pytest.mark.oracle
def test_the_five_tolmap_items_are_the_ones_the_code_consumes() -> None:
    """Def. def:tolmap: FIVE items still, and the two the amendment adds NEITHER.

    ``TOLMAP_ITEMS`` -- the registry's 0.2.0 five-row table -- is marked in
    ``SUPERSEDED_BY_0_3_0`` with kind ``incomplete`` -- NOT ``reframed``, which
    is a different kind of that freeze -- and its own reason reads "THE FIVE
    ITEMS ARE STILL FIVE ... INCOMPLETE, not superseded: nothing here is
    false". An ``incomplete`` mark licenses ADDING assertions and never
    deleting them, so the five-row map is replayed here BESIDE the mark, the
    way ``TOLERANCE_DOMAIN`` is replayed beside its own.
    What the registry-0.3.0 amendment adds is TWO DECLARED NUMBERS THAT DECIDE
    NO EXACT CONDITION: Def. def:tolmap's preamble names both -- ``eps_6``
    decides no exact condition on declared data and bounds a computed quantity
    only, and ``eps_eig`` decides NOTHING AT ALL. So there is still no sixth
    item, and this module consumes neither as a threshold.
    """
    assert is_superseded_0_3_0("TOLMAP_ITEMS")
    # THE FIVE ROWS THE MARK LEAVES TRUE, replayed rather than dropped.
    assert len(TOLMAP_ITEMS) == 5
    assert {item for item, _, _ in TOLMAP_ITEMS} == {
        "(i)",
        "(ii)",
        "(iii)",
        "(iv)",
        "(v)",
    }
    deciding = {item: key for item, key, _ in TOLMAP_ITEMS}
    assert deciding["(i)"] == "eps_2"
    assert deciding["(ii)"] == "eps_2"
    assert deciding["(iii)"] == "eps_4 and eps_2"
    assert deciding["(iv)"] == "eps_2"
    assert deciding["(v)"] == "eps_1"
    # r_1 and r_2 are not a sixth item: they ARE (v) and the positivity half
    # of (i), written as residuals.
    assert {row[0] for row in TOLMAP_RESIDUALS_ALREADY_COUNTED} == {"r_1", "r_2"}
    # THE TWO NEW NUMBERS DECIDE NOTHING, and the registry freezes the sites
    # that say so.
    assert {row[0] for row in TOLMAP_NOT_A_TEST_0_3_0} >= {"eps_6", "eps_eig"}
    # Every tolerance the map names is a member of the declared eight, and the
    # six always-required ones are exactly the module's TOLERANCE_KEYS.
    assert set(TOLERANCES_UNUSED_ON_ROUTE_I) <= set(TOLERANCE_FIXTURE_0_3_0)
    assert TOLERANCE_KEYS == TOLERANCES_ALWAYS_REQUIRED_0_3_0
    assert (
        tuple(key for key, _ in TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0)
        == TOLERANCE_KEYS_CONDITIONAL
    )
    assert set(TOLERANCE_KEYS_ALL) == set(TOLERANCE_FIXTURE_0_3_0)
    # The kinds of validation that consume NO tolerance now include the
    # exact-window ones (kind (a) and kind (b) of the closing enumeration).
    kinds = dict(TOLMAP_OTHER_VALIDATION_KINDS_0_3_0)
    assert any("m*_t" in row for rows in kinds.values() for row in rows)


# ---------------------------------------------------------------------------
#  (i) route-(i) Gram admissibility at eps_2
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_tolmap_item_i_admits_and_refuses_at_the_declared_eps_2() -> None:
    """Def. def:tolmap (i): lmin(A_k) >= -eps_2 and lmax(A_Sigma) <= 1 + eps_2."""
    families = {
        "TOLMAP-I-LMIN-BOUNDARY-ADMIT": _family(
            _diag(F(1, 2), F(-1, 1000)), _diag(F(1, 4), F(0))
        ),
        "TOLMAP-I-LMIN-REFUSE": _family(
            _diag(F(1, 2), F(-1, 500)), _diag(F(1, 4), F(0))
        ),
        "TOLMAP-I-LMAX-BOUNDARY-ADMIT": _family(
            _diag(F(1001, 1000), F(0)), _diag(F(0), F(0))
        ),
        "TOLMAP-I-LMAX-REFUSE": _family(_diag(F(501, 500), F(0)), _diag(F(0), F(0))),
    }
    for case in TOLMAP_I_CASES:
        family = families[case.case_id]
        outcome = check_gram_family_admissible(family, TOLERANCE)
        assert (outcome is None) is case.admitted, case.case_id
        if not case.admitted:
            assert isinstance(outcome, Refusal)
            assert outcome.reason is RefusalReason.PORT_GRAMS_NOT_ADMISSIBLE
        # The quantity the item compares is the frozen one.
        if case.quantity == "lmin(A_1)":
            value = float(np.min(np.linalg.eigvalsh(family.matrices[0]).real))
        else:
            value = lambda_max(family.a_sigma)
        assert value == pytest.approx(float(case.value), abs=1e-12), case.case_id


@pytest.mark.contract
def test_the_admission_and_the_residual_are_one_test_at_eps_2() -> None:
    """Def. def:tolmap (i): the same declared number, in the same units."""
    from certiqs_key.receiver.residuals import positivity_residual

    admitted = _family(_diag(F(1, 2), F(-1, 1000)), _diag(F(1, 4), F(0)))
    refused = _family(_diag(F(1, 2), F(-1, 500)), _diag(F(1, 4), F(0)))
    assert check_gram_family_admissible(admitted, TOLERANCE) is None
    assert positivity_residual(admitted, TOLERANCE).passes is True
    assert check_gram_family_admissible(refused, TOLERANCE) is not None
    assert positivity_residual(refused, TOLERANCE).passes is False


@pytest.mark.contract
def test_the_gram_hermiticity_defect_is_measured_in_the_spectral_norm() -> None:
    """Def. def:residuals: ||.|| IS THE SPECTRAL NORM, at this site too.

    Eq. eq:rhodef's first entry is exactly ||X - X^dagger||, and def:residuals
    fixes the norm "throughout eq:res1-eq:rhodef".  The two readings are not
    the same number: for a 3 x 3 skew defect with every off-diagonal entry s
    the ENTRYWISE maximum is s while the SPECTRAL norm is sqrt(3) s, so a
    family sitting between them is admitted under one reading and refused
    under the contract's.  Every frozen Gram of the registry is Hermitian, so
    without this witness nothing in the suite distinguishes the two.
    """
    skew = np.array([[0, 1, 1], [-1, 0, 1], [-1, -1, 0]], dtype=np.complex128)
    defect = 7e-4  # entrywise 7e-4 <= eps_2 = 1e-3 < sqrt(3) * 7e-4
    gram = np.diag([0.25, 0.25, 0.25]).astype(np.complex128) + 0.5 * defect * skew
    entrywise = float(np.max(np.abs(gram - gram.conj().T)))
    spectral = residual_norm(gram - gram.conj().T)
    assert entrywise <= TOLERANCE.eps_2 < spectral
    outcome = check_gram_family_admissible(_family(gram), TOLERANCE)
    assert isinstance(outcome, Refusal)
    assert outcome.reason is RefusalReason.PORT_GRAMS_NOT_ADMISSIBLE
    assert "spectral norm" in outcome.detail
    # Its Hermitian part is admitted: the defect is the only thing refused.
    hermitian = 0.5 * (gram + gram.conj().T)
    assert check_gram_family_admissible(_family(hermitian), TOLERANCE) is None


# ---------------------------------------------------------------------------
#  (ii) the eps_2-rank rule
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_eps_2_rank_rule_and_both_directions_of_its_cutoff() -> None:
    """Eq. eq:eps2rank: STRICT, ABSOLUTE, and two-sided (rem:ranktwosided)."""
    grams = {
        "TOLMAP-II-RANK-EXACT-ONE-ADMIT": (_diag(F(1, 2), F(0)), 1),
        "TOLMAP-II-RANK-BOUNDARY-NOT-COUNTED-ADMIT": (
            _diag(F(1, 2), F(1, 1000)),
            1,
        ),
        "TOLMAP-II-RANK-UNDER-REPORTED-ADMIT": (_diag(F(1, 2), F(1, 2000)), 1),
        "TOLMAP-II-RANK-OVER-REPORTED-REFUSE": (_diag(F(1, 2), F(1, 500)), 1),
        "TOLMAP-II-RANK-TWO-MODE-PORT-ADMIT": (_diag(F(1, 2), F(1, 500)), 2),
    }
    for case in TOLMAP_II_RANK_CASES:
        gram, port_size = grams[case.case_id]
        assert epsilon_rank(gram, TOLERANCE.eps_2) == int(case.value), case.case_id
        family = _family(gram)
        outcome = check_rank_against_port_sizes(family, [port_size], TOLERANCE)
        assert (outcome is None) is case.admitted, case.case_id
        if not case.admitted:
            assert isinstance(outcome, Refusal)
            assert str(outcome.reason) == case.refusal_reason, case.case_id


@pytest.mark.contract
def test_the_eps_2_rank_threshold_is_absolute_and_not_relative() -> None:
    """Def. def:tolmap (ii): "the threshold is ABSOLUTE and it is eps_2".

    A relative cutoff would make the decision at a nearly dark port "a MILLION
    TIMES TIGHTER than at a lossless one". Here two Grams differ by a factor
    ``1e-6`` and the ABSOLUTE rule reports different counts, which a relative
    one could not.
    """
    bright = _diag(F(1, 2), F(1, 100))
    dark = _diag(F(1, 2000000), F(1, 100000000))
    assert epsilon_rank(bright, TOLERANCE.eps_2) == 2
    assert epsilon_rank(dark, TOLERANCE.eps_2) == 0
    # And at eps_2 = 0 the rule decides EXACTLY (rem:tolerancedomain's closed
    # end): a declarer who wants the exact condition declares 0.
    assert epsilon_rank(dark, 0.0) == 2


# ---------------------------------------------------------------------------
#  (iv) the unclamped c
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_tolmap_item_iv_admits_c_down_to_minus_eps_2_and_never_clamps() -> None:
    """Def. def:tolmap (iv) and Rem. rem:cdirection, on both sides.

    THE NEGATION IS A REFUSAL AND NOT AN EXCEPTION. Item (iv) is one of the
    five threshold decisions the contract states on DECLARED data, so a
    declaration it does not admit is a failed validation, and the
    `fail_closed` convention gives every one of those "a refusal with a
    machine-readable reason and no artifact". An earlier reading of this test codified
    `pytest.raises` as the negation, which asserted a failure mode the contract
    does not state and the registry does not freeze -- the frozen case carries
    the failing CONDITION and no reason string, because the contract spells
    none for this check.
    """
    for case in TOLMAP_IV_C_CASES:
        data = BoundData(2, 1.0, (1.0, 1.0), float(case.value), (0.5, 0.5))
        outcome = check_bound_data_admissible(data, TOLERANCE.eps_2)
        assert (outcome is None) is case.admitted, case.case_id
        if not case.admitted:
            assert isinstance(outcome, Refusal), case.case_id
            assert outcome.reason is RefusalReason.BOUND_DATA_NOT_ADMISSIBLE
            # The contract SPELLS NO REASON for this check, so the frozen case
            # carries none and the key is this module's own.
            assert case.refusal_reason is None, case.case_id
            # The detail names the label, the measured c and the declared eps_2.
            assert "def:tolmap (iv)" in outcome.detail
            assert str(float(case.value)) in outcome.detail
            assert str(TOLERANCE.eps_2) in outcome.detail
        else:
            # An ADMITTED c is returned untouched -- the datum the decision was
            # made on is not repaired, and eq:beta receives it as it stands.
            check_bound_data(data)
            assert data.c == float(case.value), case.case_id
    # NOTHING IS CLAMPED: the admitted c = -eps_2 enters eq:beta as it stands,
    # and the frozen parity split is what it produces.
    admitted = BoundData(2, 1.0, (1.0, 1.0), -float(TOLERANCE.eps_2), (0.5, 0.5))
    at_zero = BoundData(2, 1.0, (1.0, 1.0), 0.0, (0.5, 0.5))
    for photons, parity, value, zero_value, signed, magnitude in C_DIRECTION_CASES:
        evaluated = bound_function(admitted, photons)
        assert evaluated == pytest.approx(float(value), abs=1e-15), photons
        assert bound_function(at_zero, photons) == pytest.approx(
            float(zero_value), abs=1e-15
        ), photons
        difference = evaluated - bound_function(at_zero, photons)
        assert difference == pytest.approx(float(signed), abs=1e-15), photons
        assert abs(difference) == pytest.approx(float(magnitude), abs=1e-15), photons
        # The direction, by parity: conservative at odd n, not at even n.
        assert (difference < 0.0) is (parity == "odd"), photons
    bounds = {row[0]: row[1] for row in C_DIRECTION_BOUNDS}
    assert float(bounds["odd n, conservative (below)"]) == pytest.approx(
        TOLERANCE.eps_2
    )
    assert float(bounds["even n >= 2, can exceed (above)"]) == pytest.approx(
        TOLERANCE.eps_2**2
    )


# ---------------------------------------------------------------------------
#  (v) route-(ii) contractivity and C10's (E1)
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_tolmap_item_v_decides_contractivity_and_c10_at_eps_1() -> None:
    """Def. def:tolmap (v), with eq:r1islmax and C10's two-sided lossless test."""
    blocks = {
        "TOLMAP-V-BB84-UNITARY-ADMIT": _diag(F(1), F(1)),
        "TOLMAP-V-ADMITTED-ABOVE-ONE": _diag(F(4001, 4000), F(0)),
        "TOLMAP-V-REFUSE-JUST-ABOVE": _diag(F(2001, 2000), F(0)),
        "TOLMAP-V-C10-E1-REFUSE": _diag(F(2), F(0)),
        "TOLMAP-V-C10-LOSSLESS-ADMIT": _diag(F(4001, 4000), F(1)),
        "TOLMAP-V-C10-NOT-LOSSLESS": _diag(F(1, 2), F(1)),
    }
    for case in TOLMAP_V_CONTRACTIVITY_CASES:
        block = blocks[case.case_id]
        entry = GenericBlock(block)
        if case.quantity.startswith("lmax"):
            value = lambda_max(block.conj().T @ block)
            assert value == pytest.approx(float(case.value), abs=1e-12), case.case_id
            outcome = entry.check_domain(TOLERANCE)
            assert (outcome is None) is case.admitted, case.case_id
        else:
            defect = block.conj().T @ block - np.eye(block.shape[0])
            value = residual_norm(defect)
            assert value == pytest.approx(float(case.value), abs=1e-12), case.case_id
            # The LOSSLESS verdict, decided TWO-SIDEDLY at eps_1.
            assert entry.is_lossless_under(TOLERANCE) is case.admitted, case.case_id


@pytest.mark.contract
def test_eq_r1islmax_is_an_identity_at_every_frozen_contractivity_case() -> None:
    """Eq. eq:r1islmax: r_1 and the admission are one test on one number."""
    for block in (
        _diag(F(1), F(1)),
        _diag(F(4001, 4000), F(0)),
        _diag(F(2001, 2000), F(0)),
        _diag(F(2), F(0)),
        _diag(F(1, 2), F(1)),
    ):
        product = block.conj().T @ block
        r_1 = residual_norm(positive_part(product - np.eye(block.shape[0])))
        assert r_1 == pytest.approx(max(0.0, lambda_max(product) - 1.0), abs=1e-14)
        # And the two tests agree, which is what the identity buys.
        assert (r_1 <= TOLERANCE.eps_1) is (
            lambda_max(product) <= 1.0 + TOLERANCE.eps_1
        )


@pytest.mark.contract
def test_the_two_sidedness_of_c10_s_lossless_test_is_load_bearing() -> None:
    """Def. def:tolmap (v): a contraction is not thereby lossless."""
    block = _diag(F(1, 2), F(1))
    entry = GenericBlock(block)
    # Passes (E1) as a contraction ...
    assert entry.check_domain(TOLERANCE) is None
    # ... and is NOT lossless: a one-sided test would have said it was.
    assert entry.is_lossless_under(TOLERANCE) is False


@pytest.mark.contract
def test_no_tolerance_is_defaulted_at_any_deciding_site() -> None:
    """The inputs table: declared, never defaulted, checked structurally.

    Every function that decides one of the five items takes the declared tuple
    (or a member of it) as a REQUIRED argument. A default anywhere would be a
    substituted datum, which `fail_closed` forbids.
    """
    import inspect

    from certiqs_key.receiver import bound as bound_module
    from certiqs_key.receiver import dark, grams

    deciders = (
        grams.check_gram_family_admissible,
        grams.check_rank_against_port_sizes,
        dark.check_dark_channel,
        bound_module.check_bound_data_admissible,
        GenericBlock.check_domain,
        GenericBlock.is_lossless_under,
    )
    for function in deciders:
        signature = inspect.signature(function)
        parameters = [
            parameter
            for name, parameter in signature.parameters.items()
            if name in {"tolerances", "tolerance", "epsilon"}
        ]
        assert parameters, function.__qualname__
        for parameter in parameters:
            assert parameter.default is inspect.Parameter.empty, function.__qualname__
    # And the tolerance type itself has no field default.
    for field in NumericalTolerances.__dataclass_fields__.values():
        assert field.default is not None
        assert repr(field.default).startswith("<dataclasses._MISSING")
