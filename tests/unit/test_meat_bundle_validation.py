"""Bundle validation: every check of spec/architecture.md 3.6, as a hard error.

"A failure is a hard error, never a warning and never a repair: a bundle that
does not validate produces no result at all."

Each test below breaks exactly one clause of def:admissible-declaration,
def:admissible-acceptance-set or A-TSM in an otherwise valid bundle and asserts that the
failure is an exception naming the clause. The bundles are built from the frozen toys
and mutated in memory; nothing under ``tests/oracles/`` is modified.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

ORACLE_TREE = Path(__file__).resolve().parents[1] / "oracles"
if str(ORACLE_TREE) not in sys.path:
    sys.path.insert(0, str(ORACLE_TREE))

from dummy_bundles import bundle_documents  # noqa: E402
from toy_declarations import toy  # noqa: E402

from certiqs_key.domain.arrays import DenseArray  # noqa: E402
from certiqs_key.domain.bundle import OperatorBundle, parse_manifest  # noqa: E402
from certiqs_key.meat_core.declaration.admission import (  # noqa: E402
    AdmissionError,
    AdmissionRefusal,
    GroupAPredicate,
)
from certiqs_key.meat_core.declaration.bundle import (  # noqa: E402
    declaration_from_bundle,
)
from certiqs_key.meat_core.declaration.validation import (  # noqa: E402
    MATHEMATICAL_SPEC_VERSION,
    REQUIRED_ASSUMPTIONS,
)
from certiqs_key.meat_core.errors import (  # noqa: E402
    DeclarationError,
    UnsupportedDeclarationError,
)


def documents(toy_id: str = "TOY-1") -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a fresh (manifest, arrays) pair for a frozen toy."""
    return bundle_documents(toy(toy_id))


def build(manifest: dict[str, Any], arrays: dict[str, Any]) -> OperatorBundle:
    """Return the parsed bundle of a manifest and its arrays."""
    return OperatorBundle(manifest=parse_manifest(manifest), arrays=arrays)


@pytest.mark.contract
def test_a_valid_bundle_validates() -> None:
    """The baseline: every mutation below starts from a bundle that passes."""
    manifest, arrays = documents()
    declaration = declaration_from_bundle(build(manifest, arrays))
    assert declaration.alice_dim == 1
    assert declaration.sector_index_set == ("s0", "s1")
    assert str(declaration.key_holder) == "B"


@pytest.mark.contract
def test_a_foreign_mathematical_spec_version_is_refused() -> None:
    """Contract Section 2.5: the artifact binding names the ACCEPTED contract."""
    assert MATHEMATICAL_SPEC_VERSION == "meat-core@1.28.0"
    manifest, arrays = documents()
    # An older version, not an imaginary future one: a bundle naming a
    # superseded version must be refused. The case is about a version behind
    # the current one, not about a fixed string.
    manifest["mathematical_spec_version"] = "meat-core@0.3.0"
    with pytest.raises(DeclarationError, match="mathematical_spec_version"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_a_fixed_fraction_test_statistics_model_is_refused() -> None:
    """Assumption A-TSM: nothing in this contract licenses ``fixed_fraction``.

    The sharpest of the convention checks: the difference is a security break,
    not a configuration preference.
    """
    manifest, arrays = documents()
    manifest["assumptions"]["test_statistics_model"] = "fixed_fraction"
    with pytest.raises(DeclarationError, match="fixed_fraction"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
@pytest.mark.parametrize("key", sorted(REQUIRED_ASSUMPTIONS))
def test_every_declared_convention_is_required_and_checked(key: str) -> None:
    """Contract Section 2.5: an undeclared convention is not a default."""
    manifest, arrays = documents()
    del manifest["assumptions"][key]
    with pytest.raises(DeclarationError, match=key):
        declaration_from_bundle(build(manifest, arrays))

    manifest, arrays = documents()
    manifest["assumptions"][key] = "something-else"
    with pytest.raises(DeclarationError, match=key):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_a_non_normalized_trusted_marginal_is_refused() -> None:
    """def:admissible-declaration (ii): ``tau_A`` is a normalized state.

    RE-POINTED AT 1.0.0 at the reason and not at the verdict. Contract Section
    2.6's ``alice_marginal_exact`` row decides ``tr tau_A = 1`` at EXACTLY 0
    and names the predicate that failed, where 0.4.0 compared the trace against
    an undeclared ``1e-10`` window and attributed the refusal to
    def:admissible-declaration (ii). The clause is still def:admissible-declaration
    (ii)'s; what changed is which row decides it and that the decision is exact.
    """
    manifest, arrays = documents()
    arrays["/declaration/alice_marginal"] = DenseArray(np.array([[0.5]]))
    with pytest.raises(AdmissionError, match="alice_marginal_exact") as raised:
        declaration_from_bundle(build(manifest, arrays))
    assert raised.value.predicate is GroupAPredicate.ALICE_MARGINAL_EXACT
    assert "the exact trace of tau_A is not 1" in str(raised.value)


@pytest.mark.contract
def test_a_negative_trusted_marginal_is_refused() -> None:
    """def:admissible-declaration (ii): ``tau_A`` is positive semidefinite.

    A SPECTRAL FLOOR AT EXACTLY 0 at 1.0.0, decided by a rational ``LDL^*``
    rather than by an eigenvalue against a window (Section 2.6,
    ``alice_marginal_exact``).
    """
    manifest, arrays = documents("TOY-7")
    arrays["/declaration/alice_marginal"] = DenseArray(np.diag([1.5, -0.5]))
    with pytest.raises(AdmissionError, match="positive semidefinite") as raised:
        declaration_from_bundle(build(manifest, arrays))
    assert raised.value.predicate is GroupAPredicate.ALICE_MARGINAL_EXACT


@pytest.mark.contract
def test_an_incomplete_alice_povm_is_refused() -> None:
    """def:admissible-declaration (iii): ``sum_x M_x = 1_A``.

    RE-POINTED AT 1.0.0: the ``alice_povm_exact`` row of Section 2.6 decides it
    at EXACTLY 0, over the rationals, and the refusal names the predicate.
    """
    manifest, arrays = documents()
    arrays["/declaration/alice_povm/x0"] = DenseArray(np.array([[0.5]]))
    with pytest.raises(AdmissionError, match="alice_povm_exact") as raised:
        declaration_from_bundle(build(manifest, arrays))
    assert raised.value.predicate is GroupAPredicate.ALICE_POVM_EXACT
    assert "the exact sum sum_x M_x is not 1_A" in str(raised.value)


@pytest.mark.contract
def test_an_incomplete_bob_povm_is_refused_per_sector() -> None:
    """Admissibility (iii): the family is complete per sector, decided EXACTLY.

    THE VERDICT IS NOT A MEASURED DEFECT. An ``np.allclose`` against a constant
    declared for itself, or a MEASURED completeness defect against a declared
    tolerance -- here ``0.75 + 0.5 - 1 = 0.25`` on ``s1``, a defect of ``1/4``
    under the string ``bob_povm_completeness_defect`` -- would decide it
    otherwise. Neither exists: no defect is measured on declared data and the
    three defect-named strings are not emitted, so what the refusal carries is
    the PREDICATE and the SECTOR, under the one exact refusal.

    THE EXACT RESIDUE IS STILL IN THE MESSAGE, as a RATIONAL rather than a
    float: the squared entrywise residue of the exact sum is ``1/16``, which is
    ``(1/4)^2``. It is reported and nothing is compared against it.
    """
    manifest, arrays = documents()
    arrays["/declaration/bob_povm/v0/s1"] = DenseArray(np.array([[0.75]]))
    with pytest.raises(AdmissionError, match=re.escape("residue")) as raised:
        declaration_from_bundle(build(manifest, arrays))
    assert raised.value.reason is AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE
    assert raised.value.predicate is GroupAPredicate.BOB_POVM_ADMISSION
    assert "'s1'" in str(raised.value)
    assert "1/16" in str(raised.value)
    # An AdmissionError IS a DeclarationError: the declaration is
    # refused and no result is produced, exactly as at 0.4.0.
    assert isinstance(raised.value, DeclarationError)


@pytest.mark.contract
def test_a_negative_povm_element_is_refused() -> None:
    """Admissibility (iii): every block positive semidefinite, decided EXACTLY.

    Same reasoning as the test above. ``F_v0^(s0) = [-1/2]`` would be a
    NEGATIVE PART of ``1/2`` measured against a declared tolerance, under
    ``bob_povm_negative_part``; the measurement and the string do not exist and
    the decision is an exact one -- a rational ``LDL^*`` with the zero-pivot
    rule, no eigenvalue and no threshold.

    THE TWO PERTURBATIONS CANCEL IN THE SUM, so the family is still complete
    and positivity is the ONLY condition that fails. The refusal names the
    BLOCK, which is what makes the two distinguishable without a defect number:
    a completeness failure names a sector and this names an outcome and a
    sector.
    """
    manifest, arrays = documents()
    arrays["/declaration/bob_povm/v0/s0"] = DenseArray(np.array([[-0.5]]))
    arrays["/declaration/bob_povm/v1/s0"] = DenseArray(np.array([[1.5]]))
    with pytest.raises(
        AdmissionError, match=re.escape("NOT EXACTLY POSITIVE SEMIDEFINITE")
    ) as raised:
        declaration_from_bundle(build(manifest, arrays))
    assert raised.value.reason is AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE
    assert raised.value.predicate is GroupAPredicate.BOB_POVM_ADMISSION
    assert "'v0'" in str(raised.value)
    assert "'s0'" in str(raised.value)


@pytest.mark.contract
def test_a_sector_map_disagreement_is_detected_not_reconciled() -> None:
    """Definition ``def:optol`` (T), and it is a TYPE rule.

    A test that declared a FULL-SPACE ``bob_povm`` element in order to check
    that a non-block-diagonal one is rejected rather than truncated would rest
    on the argument that "a caller holding a non-block-diagonal Bob
    POVM element must be able to serialize it, or ``meat-core`` could never
    detect the violation it is required to reject". spec/architecture.md 2.9 records
    that the argument is CORRECT IN ITS OWN TERMS and removes the full-space
    form by a change of premise: a producer emits one array per sector, so the
    violation is unrepresentable and there is nothing left to detect.

    WHAT IS TESTED is the comparison spec/architecture.md 2.9 names in the same
    breath -- the
    SECTOR MAP, block identifiers and their ordering against the consumer's own
    -- "which is the only failure mode the representation admits". Its reason
    is ``sector_map_disagreement``; a (T) failure does not travel the unnamed
    malformed-declaration path.
    """
    manifest, arrays = documents()
    blocks = manifest["payload"]["declaration"]["bob_povm"]["v0"]["blocks"]
    blocks["sX"] = blocks.pop("s1")
    with pytest.raises(AdmissionError) as raised:
        declaration_from_bundle(build(manifest, arrays))
    assert raised.value.reason is AdmissionRefusal.SECTOR_MAP_DISAGREEMENT
    assert str(raised.value.reason) == "sector_map_disagreement"
    # NOT RECONCILED: the map is refused rather than renamed, re-ordered or
    # projected onto the consumer's own (Remark rem:optol-interface (3)).
    assert "sX" in str(raised.value)
    assert "nothing is projected, re-ordered or renamed" in str(raised.value)


@pytest.mark.contract
def test_the_sector_map_ordering_is_part_of_the_map() -> None:
    """The half of (T) an implementation comparing SETS would miss.

    The block identifiers agree and their ORDER does not. That is a
    disagreement because Eq. ``eq:declorder`` forms each sector's completeness
    sum in the declared order and binary64 addition is not associative, so two
    maps naming the same sectors in different orders ask condition (S) a
    different question. spec/architecture.md 2.9's own description of the sector map is
    "the
    block kind, the block identifiers AND THEIR ORDERING".
    """
    manifest, arrays = documents()
    descriptor = manifest["payload"]["declaration"]["bob_povm"]["v0"]
    blocks = descriptor["blocks"]
    descriptor["blocks"] = {name: blocks[name] for name in reversed(list(blocks))}
    with pytest.raises(AdmissionError) as raised:
        declaration_from_bundle(build(manifest, arrays))
    assert raised.value.reason is AdmissionRefusal.SECTOR_MAP_DISAGREEMENT
    assert "THE ORDERING DOES NOT" in str(raised.value)


@pytest.mark.contract
def test_sifting_that_is_not_announcement_determined_is_refused() -> None:
    """def:admissible-declaration (v): ``r = perp`` exactly on the fail classes."""
    manifest, arrays = documents()
    manifest["payload"]["declaration"]["key_map"]["x0"]["v1"] = None
    with pytest.raises(DeclarationError, match=r"def:admissible-declaration \(v\)"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_a_raw_key_value_outside_the_alphabet_is_refused() -> None:
    """def:admissible-declaration (iv): ``r`` maps into ``Z u {perp}``."""
    manifest, arrays = documents()
    manifest["payload"]["declaration"]["key_map"]["x0"]["v1"] = 7
    with pytest.raises(DeclarationError, match=r"def:admissible-declaration \(iv\)"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_a_key_map_the_holder_cannot_compute_is_refused() -> None:
    """def:admissible-declaration (viii): holder computability.

    TOY-1 declares ``h = B`` and ``r(x, v) = v``, which Bob can compute. Moving
    the holder to Alice makes the same map uncomputable -- with Alice's single
    outcome and one announcement class, ``r`` would have to be constant.
    """
    manifest, arrays = documents()
    manifest["payload"]["declaration"]["key_holder"] = "A"
    with pytest.raises(DeclarationError, match=r"def:admissible-declaration \(viii\)"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_a_non_hermitian_constraint_bound_is_refused() -> None:
    """Admissibility (vi): ``Theta_k`` is Hermitian on ``A``, decided EXACTLY.

    THE PREDICATE IS AN EXACT DECISION, not a window. Deciding it with the
    objective's ``HERMITICITY_TOLERANCE``, a constant of its linear algebra,
    would be a WINDOW ON DECLARED DATA;
    ``constraint_operator_exact`` is a Group A row of the interface and every
    Group A row is decided at exactly zero. POSITIVITY IS ASKED OF NO
    CONSTRAINT OPERATOR, here or anywhere.
    """
    manifest, arrays = documents("TOY-7")
    arrays["/declaration/constraint/0/bound"] = DenseArray(
        np.array([[1.0, 1.0], [0.0, 0.5]])
    )
    with pytest.raises(AdmissionError, match="NOT EXACTLY HERMITIAN") as raised:
        declaration_from_bundle(build(manifest, arrays))
    assert raised.value.reason is AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE
    assert raised.value.predicate is GroupAPredicate.CONSTRAINT_OPERATOR_EXACT


@pytest.mark.contract
def test_an_acceptance_vector_that_is_not_a_distribution_is_refused() -> None:
    """def:admissible-acceptance-set: a subset of the probability simplex."""
    manifest, arrays = documents("TOY-4a")
    manifest["payload"]["declaration"]["acceptance_set"]["data"]["frequencies"] = [
        0.25,
        0.25,
    ]
    with pytest.raises(DeclarationError, match="def:admissible-acceptance-set"):
        declaration_from_bundle(build(manifest, arrays))

    manifest, arrays = documents("TOY-4a")
    manifest["payload"]["declaration"]["acceptance_set"]["data"]["frequencies"] = [
        -0.25,
        1.25,
    ]
    with pytest.raises(DeclarationError, match="negative"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_an_unread_acceptance_geometry_is_refused_rather_than_guessed() -> None:
    """def:admissible-acceptance-set admits more than any declared taxonomy names.

    ``ball`` is a perfectly good closed convex subset of the simplex and no tag
    of the accepted ``statistics-acceptance`` 0.1.2 taxonomy names it, so it is
    refused rather than guessed at -- which is also what contract Remark
    ``rem:acc-side`` instructs for a set fitting neither of its two
    instantiations. The tag ``polytope`` is read.
    """
    manifest, arrays = documents()
    manifest["payload"]["declaration"]["acceptance_set"]["geometry"] = "ball"
    with pytest.raises(UnsupportedDeclarationError, match="not read by this"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_a_non_identity_permutation_is_refused_rather_than_interpreted() -> None:
    """The format checks a permutation is one; the contract does not say what.

    Which is why applying a non-identity one would be an improvisation.
    """
    manifest, arrays = documents()
    manifest["payload"]["declaration"]["bob_povm"]["v0"]["block_permutation"] = [1, 0]
    with pytest.raises(UnsupportedDeclarationError, match="block_permutation"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_a_missing_sector_block_is_refused() -> None:
    """Admissibility (iii): every block of a block-diagonal operator is declared."""
    manifest, arrays = documents()
    del manifest["payload"]["declaration"]["bob_povm"]["v0"]["blocks"]["s1"]
    # The format's own block_permutation check would fire first; drop it so that
    # the bundle is well-formed AS DATA and only meat-core's clause is left.
    manifest["payload"]["declaration"]["bob_povm"]["v0"]["block_permutation"] = [0]
    with pytest.raises(DeclarationError, match="s1"):
        declaration_from_bundle(build(manifest, arrays))


@pytest.mark.contract
def test_a_declared_array_that_is_absent_is_refused() -> None:
    """A manifest and its arrays are one artifact; a dangling dataset is an error."""
    manifest, arrays = documents()
    del arrays["/declaration/alice_marginal"]
    with pytest.raises(DeclarationError, match="carries no such array"):
        declaration_from_bundle(build(manifest, arrays))
