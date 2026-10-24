"""The structural fail-closed assertions the candidate-side pass can make.

Section 2.5 (``fail_closed``): "every failed check produces a refusal with a
machine-readable reason and NO declaration ... NO DEFAULT VALUE IS EVER
SUBSTITUTED FOR A MISSING DATUM, NO ENTRY IS SILENTLY DROPPED, AND NO LICENCE
IS EVER SYNTHESIZED."

Those are three separate promises and each is tested here separately, on the
code paths this pass owns. The gate outcomes of Table ``tab:gateoutcome`` --
which decide WHICH of the three permitted outcomes an emission produces -- are
the emission pass's and are not exercised here.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from protocol_blocks import (
    as_blocks,
    family_as_blocks,
    joint_as_blocks,
)

from certiqs_key.domain.constraints import ConstraintEntry, Relation
from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.errors import HypothesisError
from certiqs_key.foundations.exact import equal, identity, kron, matrix, scale
from certiqs_key.protocol_compiler import (
    CandidateDeclaration,
    Party,
    Refusal,
    RefusalReason,
    check_feasibility,
    default_party_partition,
    default_witness,
    refuse_fixed_fraction,
    validate,
    verify_witness,
)
from certiqs_key.transmitter import RetentionAttestation, SourceReplacementLicense

pytestmark = pytest.mark.contract

P_Z0 = matrix(((1, 0), (0, 0)))
P_Z1 = matrix(((0, 0), (0, 1)))
#: The block kind every fixture below declares: the shared format's
#: ``proof_sector`` (:class:`~certiqs_key.foundations.blocks.BlockKind`). The
#: contract NAMES the datum and the format FIXES the values, so open choice
#: ``OC-sector-block-kind`` is narrowed within that alphabet and still not
#: decided. ``proof_sector`` is the member these fixtures ARE: their
#: decomposition is "justified by dephasing or SOURCE REPLACEMENT", not photon
#: number (``physical_sector``) and not solver sparsity (``numerical_block``).
#: See :func:`instances.bb84.specification.band_a_block_kind` for the reading.
FIXTURE_BLOCK_KIND = BlockKind.PROOF_SECTOR

ONE_SECTOR_QUBIT = SectorStructure(
    labels=("s0",), dims=(2,), block_kind=FIXTURE_BLOCK_KIND
)


def _declaration(
    *,
    alice_marginal: object = None,
    constraint_list: tuple[ConstraintEntry, ...] = (),
) -> CandidateDeclaration:
    x_alphabet = ("x0", "x1")
    v_alphabet = ("v0", "v1")
    return CandidateDeclaration(
        alice_dim=2,
        alice_marginal=alice_marginal,  # type: ignore[arg-type]
        sectors=ONE_SECTOR_QUBIT,
        alice_alphabet=x_alphabet,
        alice_povm={"x0": P_Z0, "x1": P_Z1},
        bob_alphabet=v_alphabet,
        bob_povm=family_as_blocks(ONE_SECTOR_QUBIT, {"v0": P_Z0, "v1": P_Z1}),
        partition=default_party_partition(x_alphabet, v_alphabet),
        announce_alice={"x0": "alpha0", "x1": "alpha1"},
        announce_bob={"v0": "beta0", "v1": "beta1"},
        alice_announcement_alphabet=("alpha0", "alpha1"),
        bob_announcement_alphabet=("beta0", "beta1"),
        acceptance_alphabet=("g",),
        accept_statistic={
            (a, b): "g" for a in ("alpha0", "alpha1") for b in ("beta0", "beta1")
        },
        key_map={(x, v): x_alphabet.index(x) for x in x_alphabet for v in v_alphabet},
        key_alphabet=(0, 1),
        key_holder=Party.ALICE,
        constraint_list=constraint_list,
    )


# ---------------------------------------------------------------------------
#  NO DEFAULT VALUE IS EVER SUBSTITUTED FOR A MISSING DATUM
# ---------------------------------------------------------------------------


def test_the_empty_marginal_slot_is_null_and_never_a_zero_matrix() -> None:
    """Section 3's sentinel discipline, and what V2 does to the alternative."""
    untrusted = _declaration()
    assert untrusted.alice_marginal is None
    assert untrusted.is_trusted_mode is False
    assert validate(untrusted).passed is True

    zero_matrix = _declaration(alice_marginal=matrix(((0, 0), (0, 0))))
    assert zero_matrix.is_trusted_mode is True
    result = validate(zero_matrix)
    assert result.refusing_checks == ("V2",)
    assert result.outcome_of("V2").refusal is not None


def test_a_missing_acceptance_value_is_refused_and_never_completed() -> None:
    """Remark rem:phitotal: refused, not "completed with a default value"."""
    declaration = _declaration()
    partial = dict(declaration.accept_statistic)
    del partial[("alpha1", "beta1")]
    crippled = CandidateDeclaration(
        **{**declaration.__dict__, "accept_statistic": partial}
    )
    result = validate(crippled)
    assert "V1" in result.refusing_checks
    assert result.first_refusal is not None
    assert "default" in result.first_refusal.detail


def test_a_subnormalized_witness_is_not_normalized_before_testing() -> None:
    # The right-hand side is tight enough that the DEFAULT candidate fails
    # too (it gives 1/2), so the supplied witness is the one on trial.
    entry = ConstraintEntry(
        operator=as_blocks(ONE_SECTOR_QUBIT, P_Z0), relation=Relation.GE, rhs=F(3, 4)
    )
    declaration = _declaration(constraint_list=(entry,))
    half = joint_as_blocks(ONE_SECTOR_QUBIT, 2, scale(F(1, 8), identity(4)))
    verification = verify_witness(declaration, half)
    assert verification.trace_one is False
    assert verification.passes is False
    outcome = check_feasibility(declaration, half)
    assert outcome.passes is False
    assert outcome.witness is None


def test_the_default_witness_is_exhibited_and_is_not_a_substituted_marginal() -> None:
    """Remark rem:notfallback: ``1_A / d_A`` is never substituted for ``nomarg``."""
    untrusted = _declaration()
    assert equal(default_witness(untrusted).dense(), scale(F(1, 4), identity(4)))
    # The witness is maximally mixed, and the DECLARATION still imposes no
    # marginal condition -- a state with any A-marginal remains feasible.
    from certiqs_key.protocol_compiler import in_feasible_set

    state = joint_as_blocks(
        ONE_SECTOR_QUBIT, 2, kron(P_Z0, scale(F(1, 2), identity(2)))
    )
    assert in_feasible_set(untrusted, state) is True
    trusted = _declaration(alice_marginal=scale(F(1, 2), identity(2)))
    assert in_feasible_set(trusted, state) is False


# ---------------------------------------------------------------------------
#  NO ENTRY IS SILENTLY DROPPED
# ---------------------------------------------------------------------------


def test_every_constraint_entry_is_carried_into_every_check() -> None:
    entries = tuple(
        ConstraintEntry(
            operator=as_blocks(ONE_SECTOR_QUBIT, P_Z0),
            relation=Relation.GE,
            rhs=F(1, 4),
        )
        for _ in range(3)
    )
    declaration = _declaration(constraint_list=entries)
    assert len(declaration.constraint_list) == 3
    verification = verify_witness(declaration, default_witness(declaration))
    assert len(verification.constraint_values) == 3
    from certiqs_key.protocol_compiler import decidability_counts

    assert decidability_counts(declaration).block_conditions == 0
    record = declaration.as_machine_record()
    assert isinstance(record["constraint_list"], list)
    assert len(record["constraint_list"]) == 3


def test_a_mistyped_entry_is_refused_and_never_transformed() -> None:
    """The proof of thm:typing (D(vi)): "check V6 rejects exactly such an entry"."""
    # THE MARGINAL SLOT HOLDS nomarg on this fixture, "where ONLY THE SCALAR
    # FORM EXISTS" (Definition def:homog), so a MATRIX right-hand side is what
    # V6 refuses here. Through 0.2.0 the refusal ran the other way.
    mistyped = ConstraintEntry(
        operator=as_blocks(ONE_SECTOR_QUBIT, P_Z0),
        relation=Relation.GE,
        rhs=scale(F(1, 2), P_Z0),
    )
    declaration = _declaration(constraint_list=(mistyped,))
    result = validate(declaration)
    assert result.refusing_checks == ("V6",)
    # AND THE ENTRY IS STILL THERE: nothing was dropped or coerced.
    assert declaration.constraint_list == (mistyped,)
    assert declaration.constraint_list[0].rhs is mistyped.rhs


# ---------------------------------------------------------------------------
#  NO LICENCE IS EVER SYNTHESIZED
# ---------------------------------------------------------------------------


def test_an_absent_attestation_stays_absent() -> None:
    record = SourceReplacementLicense(
        sr1_holds=True, sr2_holds=True, retention_attestation=None
    )
    assert record.attestation_supplied is False
    assert record.as_machine_record()["sr3_attestation"] is None
    assert record.as_machine_record()["sr3_asserted_by_this_module"] is False


def test_the_module_cannot_construct_a_licence_that_asserts_sr3() -> None:
    attestation = RetentionAttestation(attested_by="supplier", statement="A retained")
    with pytest.raises(HypothesisError):
        SourceReplacementLicense(
            sr1_holds=True,
            sr2_holds=True,
            retention_attestation=attestation,
            asserted_by_this_module=True,
        )


def test_an_absent_attack_set_licence_stays_absent_in_the_record() -> None:
    declaration = _declaration()
    assert declaration.attack_set_license is None
    assert declaration.as_machine_record()["attack_set_license"] is None


# ---------------------------------------------------------------------------
#  A REFUSAL IS A RECORD, AND AN EXCEPTION IS SOMETHING ELSE
# ---------------------------------------------------------------------------


def test_no_check_raises_on_a_candidate_it_can_refuse() -> None:
    """Every V-check returns a verdict; the exceptions are for other data."""
    from certiqs_key.protocol_compiler import (
        check_v1,
        check_v2,
        check_v3,
        check_v4,
        check_v5,
        check_v6,
        check_v8,
    )

    broken = CandidateDeclaration(
        **{
            **_declaration().__dict__,
            "alice_povm": {"x0": P_Z0, "x1": P_Z0},
            "alice_marginal": matrix(((2, 0), (0, -1))),
        }
    )
    for check in (check_v1, check_v2, check_v3, check_v4, check_v5, check_v6, check_v8):
        outcome = check(broken)
        assert isinstance(outcome.passed, bool)
        if not outcome.passed:
            assert isinstance(outcome.refusal, Refusal)


def test_an_unevaluable_check_is_reported_failing_and_never_passing() -> None:
    declaration = _declaration()
    partial = dict(declaration.accept_statistic)
    del partial[("alpha1", "beta1")]
    crippled = CandidateDeclaration(
        **{**declaration.__dict__, "accept_statistic": partial}
    )
    result = validate(crippled)
    # V5 and V8 quantify over X x V through a; V7 needs Eq. eq:feas-modes to
    # be well posed. All three are blocked by V1 and none is reported passing.
    assert set(result.unevaluated_checks) == {"V5", "V7", "V8"}
    for check in result.unevaluated_checks:
        outcome = result.outcome_of(check)
        assert outcome.passed is False
        assert outcome.evaluated is False
        assert outcome.refusal is not None
        assert "never as passing" in outcome.refusal.detail.lower()


def test_the_fixed_fraction_refusal_needs_no_input_key() -> None:
    from certiqs_key.protocol_compiler import INPUT_KEYS

    refusal = refuse_fixed_fraction("a caller-level model selection")
    assert refusal.reason is RefusalReason.FIXED_FRACTION_REQUESTED
    # WHAT THIS TEST IS ABOUT IS THE ABSENCE: the typed input table carries NO arrival
    # for the test-statistics model, so the refusal of Theorem ``thm:choice-encoding``
    # (iv) holds BY CONSTRUCTION and has no key to be triggered by. That is an open
    # question, which is why the absence is asserted by name rather than by a
    # count. There are eleven input keys.
    assert len(INPUT_KEYS) == 11
    assert "test_statistics_model" not in INPUT_KEYS
    assert "fixed_fraction" not in " ".join(INPUT_KEYS)


def test_a_divergent_virtual_ensemble_at_empty_source_segment_is_not_emitted() -> None:
    """At L_s = 0 the certificate's virtual pair IS the specified pair.

    Definition def:spec (a): "When L_s = 0 that system and that ensemble ARE
    the specified ones"; the "One reading at every L_s" paragraph and Theorem
    thm:pc12 (i) read the certificate on the specified pair there. A
    presentation where the two diverge is not a state of affairs the contract
    admits, and it must not become a trusted, key-length-eligible emission
    describing a source other than the specified one.
    """
    from dataclasses import replace

    from instances.bb84.specification import (
        P_Z0,
        P_Z1,
        bb84_specification,
        conjugate_projector,
    )

    from certiqs_key.foundations.errors import MalformedInputError
    from certiqs_key.protocol_compiler import compile_specification
    from certiqs_key.protocol_compiler.spec import PublicChoices

    spec = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    choices = spec.source.alice_povm
    swapped_alice = PublicChoices(
        party=Party.ALICE,
        choices=choices.choices,
        weights=choices.weights,
        conditional_alphabets=choices.conditional_alphabets,
        conditional_elements={
            "Z": {"0": conjugate_projector(P_Z1), "1": conjugate_projector(P_Z0)},
            "X": choices.conditional_elements["X"],
        },
        joint_labels=choices.joint_labels,
    )
    # THE CERTIFICATE TRAVELS INSIDE THE LICENCE RECORD, and the
    # ARTEFACT carries the virtual pair a consumer receives. The mutation
    # is the same mutation: the certificate's own pair is swapped while
    # the artefact's stays put, so (SR1)/(SR2) hold against the
    # certificate's OWN pair and only the typing stipulation can catch it.
    licence = spec.source.artifact.source_replacement_license
    assert licence is not None
    assert licence.certificate is not None
    cert = replace(
        licence.certificate,
        virtual_states={
            "(Z,0)": P_Z1,
            "(Z,1)": P_Z0,
            "(X,0)": licence.certificate.virtual_states["(X,0)"],
            "(X,1)": licence.certificate.virtual_states["(X,1)"],
        },
    )
    mutated = replace(
        spec,
        source=replace(
            spec.source,
            alice_choices=swapped_alice,
            artifact=replace(
                spec.source.artifact,
                source_replacement_license=replace(licence, certificate=cert),
            ),
        ),
    )
    # (SR1)/(SR2) hold against the certificate's OWN pair, so only the
    # def:spec (a) stipulation can catch the divergence. Either failure mode
    # is conforming; silent emission is the one outcome the typing forbids.
    try:
        result = compile_specification(mutated)
    except MalformedInputError:
        return
    assert result.refuses
