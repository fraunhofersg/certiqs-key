"""The exact block quantity beta*(n) (registry RC8), against the registry.

Golden replay of group RP-S: ``EXACT_BLOCK_CASES``, ``BB84_EXACT_BLOCK_FORM``
and ``EXACTBASIC_HALVES`` (oracle entry ``O-RP-EXACT-BLOCK``), first frozen at
registry 0.3.0 (a registry version is one of
tests/oracles/registry_receiver_povm.py, not of this module).

WHAT IS BEING REPLAYED, AND WHY IT IS THE LOAD-BEARING HALF OF THE AMENDMENT.
Definition ``def:exactbnd`` names the exact per-block quantity

    beta*(n) = lmin( blk M_mc^{(=n)} )

and Examples ``ex:bb84bound`` and ``ex:bb84exact`` show the defect it answers on
the worked BB84 receiver (``interface.yaml``
``inputs.photon_cutoff.depth_motivation_note``): ``beta(n) = 1 - 2^{2-n}``, so
Eq. ``eq:pmcdef`` emits ``p_mc = 0`` at the cutoff ``N = 1`` WHILE THE EXACT
MINIMUM EIGENVALUE OF THE TWO-PHOTON BLOCK OF THE SAME DEVICE IS 1/2. Every
value below is computed from the CONSTRUCTED receiver -- the module's own
``multiclick_block`` at an index above the cutoff -- and not from a closed form;
where Example ``ex:bb84exact`` states one, it is checked AGAINST the
construction rather than substituted for it.

THE TWO HALVES OF LEMMA lem:exactbasic NEED DIFFERENT HYPOTHESES:

    beta(n) <= beta*(n) <= 1      from thm:multiclick-bound's hypotheses ALONE
    beta*(n) >= 0                 ONLY under Eq. eq:mcpos (M_mc >= 0)

``EB-POSITIVITY-COUNTEREXAMPLE-N1`` and ``-N2`` are Remark
``rem:exactpositivity``'s own instance, which separates them exactly: every
hypothesis of Theorem ``thm:multiclick-bound`` holds there and ``beta* = -3``.

WHAT IS *NOT* CLAIMED HERE. ``beta-hat*`` is a floating-point evaluation and
Theorem ``thm:exact-and-evaluated`` (ii) "asserts no bound on the difference" between it
and the exact quantity, for this quantity exactly as for every other. What the replay
shows is that this module's evaluation REPRODUCES the frozen exact values at
double-precision agreement on the frozen receivers -- evidence, not an
enclosure, and Assumption ``ass:eig`` is what carries the gap.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest
from receiver_povm_support import (
    MACHINE_AGREEMENT,
    bb84_no_click_family,
    beamsplitter_no_click_family,
    positivity_counterexample_family,
)
from registry_receiver_povm import (
    BB84_EXACT_BLOCK_FORM,
    EXACT_BLOCK_CASES,
    EXACTBASIC_HALVES,
    rp_oracle,
)

from certiqs_key.receiver import (
    bound_data_from_family,
    bound_function,
    exact_block_bound,
    multiclick_block,
    multiclick_eigenvalue,
)
from certiqs_key.receiver.fock import block_dimension
from certiqs_key.receiver.numerics import eigenvalues
from certiqs_key.receiver.povm import NoClickFamily

#: The frozen receivers this file can construct, by the identifier the registry
#: gives them. The two I-PROBE settings are conditioned families and are
#: exercised end to end in the exact-window replay instead, where the whole
#: inputs-to-artifact pass builds them.
_BB84 = "I-BB84 (channel-only, Ex. ex:bb84bound)"
_BS = "I-BS (two detectors, ONE channel input mode, no probe)"
_COUNTEREXAMPLE = (
    "Rem. rem:exactpositivity's instance (NOT a receiver of this contract)"
)

#: p_Z per frozen I-BB84 case. The registry's `receiver` field names the device
#: and the case id names the point; the two together fix the Grams.
_P_Z = {
    "EB-BB84-N2-PZ-HALF": Fraction(1, 2),
    "EB-BB84-N2-PZ-SEVEN-TENTHS": Fraction(7, 10),
    "EB-BB84-N2-PZ-QUARTER": Fraction(1, 4),
    "EB-BB84-N3-PZ-HALF": Fraction(1, 2),
}


def _family(case_id: str, receiver: str, dimension: int) -> NoClickFamily | None:
    """Return the no-click family of one frozen case, or None if not built here."""
    if receiver == _BB84:
        return bb84_no_click_family(_P_Z[case_id])
    if receiver == _BS:
        return beamsplitter_no_click_family()
    if receiver == _COUNTEREXAMPLE:
        return positivity_counterexample_family(dimension)
    return None


@pytest.mark.contract
@pytest.mark.oracle
def test_the_exact_block_quantity_is_the_frozen_minimum_eigenvalue() -> None:
    """Definition def:exactbnd, Eq. eq:exactbnd, on the constructed receivers.

    The value AND the block's dimension: Definition ``def:exactbnd`` says the
    matrix has dimension ``binom(D + n - 1, n)`` with ``D = |Inp_C|``, and an
    implementation that formed the block on the wrong space would agree on
    ``I-BS`` (where every block is a scalar) and disagree on ``I-BB84``.
    """
    assert rp_oracle("O-RP-EXACT-BLOCK").claims == ("RC8",)
    seen = 0
    for case in EXACT_BLOCK_CASES:
        family = _family(case.case_id, case.receiver, case.channel_modes)
        if family is None:
            continue
        seen += 1
        block = multiclick_block(family, case.photon_number)
        assert block.shape == (case.block_dimension, case.block_dimension), case.case_id
        assert case.block_dimension == block_dimension(
            case.channel_modes, case.photon_number
        ), case.case_id
        value = exact_block_bound(family, case.photon_number)
        assert abs(value - float(case.beta_star)) <= MACHINE_AGREEMENT, case.case_id
        # The diagnostic of Requirement req:weight-provenance is the same number: it is
        # the quantity Eq. eq:mcbound bounds, and Def. def:exactbnd names it. IT IS
        # CHECKED AGAINST THE FROZEN VALUE AND NOT AGAINST `value`: comparing
        # the two routes would assert nothing, because `exact_block_bound` IS
        # `lambda_min(multiclick_block(...))` and this is `lambda_min` of the
        # block already in hand, so they agree bit for bit whatever either one
        # computes.
        assert (
            abs(multiclick_eigenvalue(block) - float(case.beta_star))
            <= MACHINE_AGREEMENT
        ), case.case_id
        # THE WHOLE FROZEN SPECTRUM, not only its minimum. The registry derives
        # every one of these by hand from Eq. eq:exactbnd -- each case carries
        # the derivation in its `derives_from` -- so the construction is read
        # against an independently derived value at every eigenvalue and not
        # only at the one Def. def:exactbnd reads off. The dimension is checked
        # above; this is what lives inside it, and an implementation that built
        # the right-sized block on the wrong vectors would pass the first check
        # and fail here.
        spectrum = sorted(float(entry) for entry in eigenvalues(block))
        frozen = sorted(float(entry) for entry in case.spectrum)
        assert len(spectrum) == len(frozen) == case.block_dimension, case.case_id
        for got, want in zip(spectrum, frozen, strict=True):
            assert abs(got - want) <= MACHINE_AGREEMENT, case.case_id
    # Every receiver this file can construct is exercised, and there are eight.
    assert seen == 8


@pytest.mark.contract
@pytest.mark.oracle
def test_the_analytic_bound_and_its_gap_are_the_frozen_ones() -> None:
    """Eq. eq:mcbound: beta(n) <= beta*(n), with the frozen gap.

    THE GAP IS THE AMENDMENT'S WHOLE SUBJECT. It is ``1/2`` at the BB84
    two-photon block at ``p_Z = 1/2`` -- "half the block's weight, discarded by
    Eq. ``eq:pmcdef`` at the cutoff ``N = 1``" -- and it is EXACTLY ZERO at
    every one-dimensional channel space, where Eq. ``eq:mcbound`` holds with
    equality and the exact window buys nothing.
    """
    for case in EXACT_BLOCK_CASES:
        family = _family(case.case_id, case.receiver, case.channel_modes)
        if family is None:
            continue
        data = bound_data_from_family(family)
        analytic = bound_function(data, case.photon_number)
        assert abs(analytic - float(case.beta_analytic)) <= MACHINE_AGREEMENT, (
            case.case_id
        )
        exact = exact_block_bound(family, case.photon_number)
        assert abs((exact - analytic) - float(case.gap)) <= MACHINE_AGREEMENT, (
            case.case_id
        )
        # Eq. eq:mcbound itself, at every frozen index: the analytic bound is
        # never above the eigenvalue it bounds.
        assert analytic <= exact + MACHINE_AGREEMENT, case.case_id
        if case.channel_modes == 1:
            # A one-dimensional channel space makes every block a scalar and
            # Eq. eq:mcbound an EQUALITY.
            assert case.gap == 0
            assert case.block_dimension == 1


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_halves_of_lemma_exactbasic_come_apart_at_the_counterexample() -> None:
    """Lemma lem:exactbasic, and Remark rem:exactpositivity's own instance.

    ``beta*(n) <= 1`` needs only Theorem ``thm:multiclick-bound``'s hypotheses, through
    the operator form Eq. ``eq:mcupper``; ``beta*(n) >= 0`` needs Eq.
    ``eq:mcpos`` and DOES NOT FOLLOW from them. The counterexample holds every
    hypothesis of that theorem and has ``beta* = -3``, so it separates the two
    halves exactly -- and Theorem ``thm:multiclick-bound`` is untouched there, the
    same data giving ``beta(n) = -3`` and Eq. ``eq:mcbound`` holding with
    EQUALITY.
    """
    halves = {row[0]: row[1] for row in EXACTBASIC_HALVES}
    assert halves["beta(n) <= beta*(n)"].startswith("the hypotheses")
    assert halves["beta*(n) <= 1"].startswith("the hypotheses")
    assert "AN ADDED HYPOTHESIS" in halves["beta*(n) >= 0"]

    for case in EXACT_BLOCK_CASES:
        family = _family(case.case_id, case.receiver, case.channel_modes)
        if family is None:
            continue
        exact = exact_block_bound(family, case.photon_number)
        # The UPPER half holds everywhere, counterexample included.
        assert exact <= 1.0 + MACHINE_AGREEMENT, case.case_id
        # The LOWER half holds exactly where Eq. eq:mcpos does.
        if case.mcpos_holds:
            assert exact >= -MACHINE_AGREEMENT, case.case_id
        else:
            assert exact < 0.0, case.case_id
            assert float(case.beta_star) == -3.0, case.case_id

    # And the numbers agree with the analytic bound at the counterexample, which
    # is the point rather than a coincidence.
    family = positivity_counterexample_family(2)
    data = bound_data_from_family(family)
    assert data.c == pytest.approx(0.0, abs=MACHINE_AGREEMENT)
    assert all(value == pytest.approx(1.0, abs=MACHINE_AGREEMENT) for value in data.ds)
    for photons in (1, 2, 3):
        assert bound_function(data, photons) == pytest.approx(
            -3.0, abs=MACHINE_AGREEMENT
        )
        assert exact_block_bound(family, photons) == pytest.approx(
            -3.0, abs=MACHINE_AGREEMENT
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_bb84_two_photon_block_matches_the_closed_form_of_ex_bb84exact() -> None:
    """Example ex:bb84exact, Eq. eq:bb84exact2 and Eq. eq:bb84exactvalue.

    THE CLOSED FORM IS A CHECK ON THE CONSTRUCTION AND NOT ITS SOURCE. The
    registry says so of its own derivation, and the same order is kept here: the
    block is built by the module, its spectrum is read off, and the closed form
    ``beta*(2) = 1 - p_Z^2 - p_X^2`` is compared against it afterwards -- at
    three values of ``p_Z``, so that the agreement is not a coincidence of the
    symmetric point.
    """
    assert BB84_EXACT_BLOCK_FORM  # the registry carries the derivation
    for case in EXACT_BLOCK_CASES:
        if case.receiver != _BB84 or case.photon_number != 2:
            continue
        p_z = float(_P_Z[case.case_id])
        p_x = 1.0 - p_z
        family = bb84_no_click_family(_P_Z[case.case_id])
        spectrum = sorted(
            float(value) for value in eigenvalues(multiclick_block(family, 2))
        )
        frozen = [float(value) for value in case.spectrum]
        assert len(spectrum) == 3 == len(frozen), case.case_id
        for got, want in zip(spectrum, frozen, strict=True):
            assert abs(got - want) <= MACHINE_AGREEMENT, case.case_id
        # Eq. eq:bb84exactvalue: beta*(2) = 1 - p_Z^2 - p_X^2 against
        # beta(2) = 1 - 2 p_Z^2 - 2 p_X^2, "a gap of p_Z^2 + p_X^2 > 0 at every
        # (p_Z, p_X)".
        closed = 1.0 - p_z**2 - p_x**2
        assert abs(spectrum[0] - closed) <= MACHINE_AGREEMENT, case.case_id
        assert float(case.gap) == pytest.approx(p_z**2 + p_x**2, abs=1e-12)


@pytest.mark.contract
def test_no_block_above_the_cutoff_is_formed_unless_one_is_asked_for() -> None:
    """Def. def:pmc's opt-in invariant, at the one function that forms a block.

    :func:`exact_block_bound` is the ONLY route in this package to a block above
    the cutoff, and it takes the index as an argument: there is no default depth
    and no path that reaches it without one. The invariant that a declaration
    requesting no depth forms nothing is realized by the caller never calling
    it, which the emission replay checks end to end.
    """
    family = bb84_no_click_family(Fraction(1, 2))
    # It is a pure function of the family and the index -- no tolerance, no
    # threshold, no state -- which is what makes "no depth, no block" checkable
    # at the call site rather than inside.
    first = exact_block_bound(family, 2)
    second = exact_block_bound(family, 2)
    assert first == second
    # And it reads the emitted-block construction at an index BELOW the cutoff
    # too, which is Def. def:exactbnd's "no new object is introduced" -- read
    # against a value DERIVED FROM THE CONTRACT rather than against
    # `multiclick_eigenvalue` of the same block, which would only restate this
    # function's own body.
    #
    # WHERE THE ZERO COMES FROM. Eq. eq:bb84exactblock of Example ex:bb84exact
    # (spec/modules/receiver/component-catalogue/claims/ex-bb84exact.tex)
    # states, for this channel-only receiver and every n >= 1,
    #
    #     blk M_mc^{(=n)} = id^{(=n)} - p_Z^n (|n_H><n_H| + |n_V><n_V|)
    #                                 - p_X^n (|n_+><n_+| + |n_-><n_-|).
    #
    # At n = 1 the occupation vectors ARE the one-photon states, so each
    # bracket is a resolution of the identity on C^2 -- {|H>, |V>} and
    # {|+>, |->} are both orthonormal bases -- and the block collapses to
    # (1 - p_Z - p_X) id = 0, because p_Z + p_X = 1. The one-photon multiclick
    # block of this receiver is the ZERO operator at every p_Z, so
    # beta*(1) = 0. That is the same fact as the analytic beta(1) = 1 - 2^{2-1}
    # = -1 being slack by exactly 1, and it is why Example ex:bb84bound's
    # cutoff N = 1 has nothing to emit before the two-photon block it discards.
    #
    # WHAT THIS PINS, AND WHAT IT DOES NOT. The zero is right, and it is read
    # off the contract rather than off the code -- but it is not a fingerprint
    # of THIS receiver. At n = 1 every Fock(.)^{(1)} is the operator itself, so
    # Eq. eq:Mmc reads
    #     id + (K-1)(id - A_Sigma) - sum_k (id - A_Sigma + A_k) = 0
    # identically, for every K and every Gram family, lossless or not. So the
    # two assertions below catch a CORRUPTED BLOCK, and an exact_block_bound
    # that stops routing through it -- both of which they do catch -- and they
    # do NOT separate I-BB84 from any other unconditioned receiver. The
    # receiver's own identity is pinned one index up, by the frozen spectrum at
    # n = 2 in the first test of this file.
    block = multiclick_block(family, 1)
    assert block.shape == (2, 2)
    # The whole block, not only its extreme eigenvalue: the derivation above
    # gives the zero OPERATOR, and checking the operator keeps this assertion
    # independent of which eigenvalue routine A-EIG's risk sits on.
    assert float(np.max(np.abs(block))) <= MACHINE_AGREEMENT
    assert abs(exact_block_bound(family, 1)) <= MACHINE_AGREEMENT
