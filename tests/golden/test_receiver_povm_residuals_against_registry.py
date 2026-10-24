"""The residual identities r_1 to r_4 (registry RC9), against the registry.

Golden replay of ``RESIDUAL_CASES`` (oracle entry ``O-RP-NUMERICS``).

EVERY PASSING RESIDUAL IS EXACTLY ZERO -- not small, zero -- because the frozen
data are exact and the identities are exact (Theorem ``thm:exact-and-evaluated`` (i)).
Every failing one is a REAL mistake an implementation makes, not an arbitrary
perturbation: a supplied non-contraction (``r_1``), a supplied non-positive
Gram (``r_2``), the deficiency identity with the unmonitored term dropped
(``r_3``), and blockwise completeness with the multiclick aggregate forgotten
(``r_4``).

THE NORM IS DECLARED WITH THE VERDICT. The registry freezes each failing
residual under BOTH natural readings of the norm Definition ``def:residuals``
left unnamed at registry 0.1.3, so that the REFUSAL VERDICT is frozen while the
NUMBER is not; the module declares the spectral norm, and the tests below check
the module's value against the spectral column AND that the verdict is the same
under the Frobenius column.
"""

from __future__ import annotations

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, mat_value
from registry_receiver_povm import (
    INSTRUMENT_CASES,
    POVM_BLOCK_CASES,
    RESIDUAL_CASES,
    rp_oracle,
)

from certiqs_key.receiver import (
    RESIDUAL_NORM,
    GramFamily,
    Residual,
    check_residuals,
    coarse_elements,
    completeness_defect,
    deficiency_identity,
    evaluate_residuals,
    port_grams,
    unconditioned_family,
)
from certiqs_key.receiver.grams import DeficiencyIdentity
from certiqs_key.receiver.numerics import residual_norm
from certiqs_key.receiver.reasons import RESIDUAL_REASONS
from certiqs_key.receiver.residuals import (
    contractivity_residual,
    deficiency_residual,
    positivity_residual,
)


def _family(case_id: str) -> tuple[np.ndarray, GramFamily, tuple[int, ...]]:
    """Return the frozen instrument matrix, Gram family and unmonitored rows."""
    case = next(c for c in INSTRUMENT_CASES if c.case_id == case_id)
    gamma_inp = mat_value(case.gamma_inp)
    labels = tuple(label for label, _ in case.port_map)
    rows = [modes for _, modes in case.port_map]
    return gamma_inp, GramFamily(labels, port_grams(gamma_inp, rows)), case.unmonitored


def _residual(case_id: str) -> Residual:
    """Return the module's value for one frozen residual case."""
    if case_id == "R1-PASS-BB84":
        gamma_inp, _, _ = _family("I-BB84")
        return contractivity_residual(gamma_inp, TOLERANCE)
    if case_id == "R1-FAIL":
        supplied = np.diag([1.5, 0.0]).astype(np.complex128)
        return contractivity_residual(supplied, TOLERANCE)
    if case_id == "R2-PASS-RANK2":
        _, family, _ = _family("I-RANK2")
        return positivity_residual(family, TOLERANCE)
    if case_id == "R2-FAIL":
        declared = GramFamily(("1",), (np.diag([1.0, -0.5]).astype(np.complex128),))
        return positivity_residual(declared, TOLERANCE)
    if case_id == "R3-PASS-UNMONITORED":
        gamma_inp, family, unmonitored = _family("I-UNMONITORED")
        return deficiency_residual(
            deficiency_identity(gamma_inp, family, unmonitored), TOLERANCE
        )
    if case_id == "R3-FAIL-DROPPED-UNMONITORED-TERM":
        gamma_inp, family, _ = _family("I-UNMONITORED")
        # THE MISTAKE: E_un = 0, i.e. the unmonitored term dropped.
        return deficiency_residual(
            deficiency_identity(gamma_inp, family, ()), TOLERANCE
        )
    if case_id == "R4-PASS-BB84-n2":
        _, family, _ = _family("I-BB84")
        no_click = unconditioned_family(family)
        return Residual(
            "r_4",
            residual_norm(completeness_defect(no_click, 2)),
            TOLERANCE.eps_4,
            RESIDUAL_NORM,
            photons=2,
        )
    if case_id == "R4-FAIL-MULTICLICK-OMITTED":
        _, family, _ = _family("I-BB84")
        no_click = unconditioned_family(family)
        blocks = coarse_elements(no_click, 2)
        # THE MISTAKE: the six emitted letters enumerated, `mc` forgotten.
        partial = sum(block for key, block in blocks.items() if key != "mc")
        return Residual(
            "r_4",
            residual_norm(np.eye(3) - partial),
            TOLERANCE.eps_4,
            RESIDUAL_NORM,
            photons=2,
        )
    raise AssertionError(f"no builder for {case_id}")


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_residual_is_reproduced_under_the_declared_norm() -> None:
    """Definition def:residuals, Eqs. eq:res1 through eq:res4."""
    assert rp_oracle("O-RP-NUMERICS").claims == ("RC9",)
    assert RESIDUAL_NORM == "spectral"
    for case in RESIDUAL_CASES:
        residual = _residual(case.case_id)
        assert residual.residual_id == case.residual_id, case.case_id
        assert residual.value == pytest.approx(
            float(case.value_spectral), abs=TOLERANCE.eps_2
        ), case.case_id
        assert residual.passes is case.passes, case.case_id
        assert residual.tolerance == TOLERANCE.residual_bound(case.residual_id)
        assert residual.norm == RESIDUAL_NORM


@pytest.mark.contract
@pytest.mark.oracle
def test_no_verdict_turns_on_the_unnamed_norm() -> None:
    """The registry freezes both norm readings, and they agree on the verdict."""
    for case in RESIDUAL_CASES:
        bound = TOLERANCE.residual_bound(case.residual_id)
        spectral_verdict = float(case.value_spectral) <= bound
        frobenius_verdict = float(case.value_frobenius_squared) <= bound
        assert spectral_verdict is frobenius_verdict is case.passes, case.case_id
        if case.passes:
            # A passing residual is EXACTLY zero, which no norm can change.
            assert case.value_spectral == 0
            assert case.value_frobenius_squared == 0
    # And the one case where the two readings genuinely differ numerically.
    differing = next(
        c for c in RESIDUAL_CASES if c.case_id == "R4-FAIL-MULTICLICK-OMITTED"
    )
    assert differing.value_spectral != differing.value_frobenius_squared


@pytest.mark.contract
def test_a_residual_above_tolerance_is_a_refusal_not_a_warning() -> None:
    """Definition def:residuals, closing sentence."""
    for case in RESIDUAL_CASES:
        residual = _residual(case.case_id)
        refusal = check_residuals((residual,))
        if case.passes:
            assert refusal is None, case.case_id
        else:
            assert refusal is not None, case.case_id
            assert refusal.reason is RESIDUAL_REASONS[case.residual_id], case.case_id
            assert RESIDUAL_NORM in refusal.detail


@pytest.mark.contract
def test_the_emitted_residual_set_is_eq_res4() -> None:
    """Eq. eq:res4 is emitted FOR EACH EMITTED n; r_1 and r_3 need a Gamma."""
    gamma_inp, family, unmonitored = _family("I-BB84")
    no_click = unconditioned_family(family)
    terms = deficiency_identity(gamma_inp, family, unmonitored)
    residuals = evaluate_residuals(
        TOLERANCE, family, no_click, cutoff=2, gamma=gamma_inp, deficiency=terms
    )
    identifiers = [residual.residual_id for residual in residuals]
    assert identifiers == ["r_1", "r_2", "r_3", "r_4", "r_4", "r_4"]
    assert [r.photons for r in residuals if r.residual_id == "r_4"] == [0, 1, 2]
    assert check_residuals(residuals) is None
    # Route (i): no compilation, so r_1 and r_3 have nothing to evaluate on.
    route_one = evaluate_residuals(TOLERANCE, family, no_click, cutoff=0)
    assert [residual.residual_id for residual in route_one] == ["r_2", "r_4"]


@pytest.mark.contract
def test_the_residual_matrix_of_the_omitted_multiclick_is_the_multiclick_block() -> (
    None
):
    """R4-FAIL-MULTICLICK-OMITTED: the error is exactly M_mc, not noise."""
    _, family, _ = _family("I-BB84")
    no_click = unconditioned_family(family)
    blocks = coarse_elements(no_click, 2)
    partial = sum(block for key, block in blocks.items() if key != "mc")
    frozen = next(c for c in POVM_BLOCK_CASES if c.case_id == "PB-BB84-n2")
    assert float(np.max(np.abs(np.eye(3) - partial - blocks["mc"]))) <= TOLERANCE.eps_4
    assert (
        float(np.max(np.abs(blocks["mc"] - mat_value(frozen.multiclick))))
        <= TOLERANCE.eps_4
    )


@pytest.mark.contract
def test_the_deficiency_residual_uses_both_summands() -> None:
    """Eq. eq:res3 with Eq. eq:deficiencyid, on the instrument that needs both."""
    gamma_inp, family, unmonitored = _family("I-UNMONITORED")
    correct = deficiency_identity(gamma_inp, family, unmonitored)
    dropped = deficiency_identity(gamma_inp, family, ())
    assert isinstance(correct, DeficiencyIdentity)
    assert deficiency_residual(correct, TOLERANCE).passes is True
    assert deficiency_residual(dropped, TOLERANCE).passes is False
