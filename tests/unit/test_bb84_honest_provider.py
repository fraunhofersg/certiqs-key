"""The Slice-1 honest channel: exact, on the emitted declaration, and not a QBER.

Three things are checked here and nothing else needs a solver for any of them:
the provider reproduces the FROZEN noiseless statistics of
``tests/oracles/registry_protocol_compiler.py`` exactly, it reproduces the
closed form of ``bb84_targets.honest_phi`` at every ``Q``, and it refuses -- with
no default substituted -- every input the model does not cover.

The frozen registry is read and never written. The three ``phi_vector`` rows
it carries are the reason the provider is checked against Fraction EQUALITY rather than
against a tolerance: at ``Q = 0`` every number in the model is a rational with a small
denominator, and an implementation that agrees to 1e-12 and not exactly has done
floating-point arithmetic somewhere it should not have.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from bb84_targets import honest_phi
from instances.bb84.specification import (
    BB84_ACCEPTANCE_ALPHABET,
    bb84_specification,
)
from instances.common.honest.depolarized_bell_pair import (
    HonestModelError,
    depolarized_state,
    honest_distribution,
    sifted_error_rate,
    visibility,
)
from registry_instances_bb84 import BB84_CASES, BB84Case

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import is_binary64
from certiqs_key.protocol_compiler import compile_specification
from certiqs_key.runs.identifiers import sanitize, stable_id_map

pytestmark = pytest.mark.contract

#: The three weight pairs the frozen registry pins, in its own order.
WEIGHTS = tuple(
    (
        case.alice_weights[0],
        case.alice_weights[1],
        case.bob_weights[0],
        case.bob_weights[1],
    )
    for case in BB84_CASES
)


def compiled(alice_z: F, alice_x: F, bob_z: F, bob_x: F):
    """Return the emitted Band-A declaration at one weight pair."""
    result = compile_specification(bb84_specification(alice_z, alice_x, bob_z, bob_x))
    assert result.refuses is False, result.refusal
    assert result.declaration is not None
    return result.declaration


def compiled_or_refused(weights: tuple[F, F, F, F]):
    """Retain the dyadic numerical checks and assert the raw input refusal.

    The symmetric internal def:weighted guard rejects an off-binary64 weight
    during construction, before the emitted_value_not_representable
    compilation refusal. These cases return None, and every frozen rational
    stays intact.
    Ordinary public inputs use the recorded preparation path, covered in
    test_runs_numeric_inputs.py; they are not this raw-specification test.
    """
    if any(not is_binary64(weight) for weight in weights):
        with pytest.raises(MalformedInputError, match="not a binary64 number"):
            bb84_specification(*weights)
        return None
    result = compile_specification(bb84_specification(*weights))
    assert not result.refuses, result.refusal
    assert result.declaration is not None
    return result.declaration


# ---------------------------------------------------------------------------
#  Against the FROZEN registry, exactly.
# ---------------------------------------------------------------------------


@pytest.mark.oracle
@pytest.mark.parametrize("case", BB84_CASES, ids=[c.case_id for c in BB84_CASES])
def test_the_provider_reproduces_the_frozen_noiseless_phi_vector(
    case: BB84Case,
) -> None:
    """At ``Q = 0`` the provider IS the frozen ``phi_vector``, as Fractions.

    The registry computed those four numbers at ``omega = |Phi^+><Phi^+|``, which
    is exactly :func:`depolarized_state` at ``Q = 0`` (``v = 1``). A provider
    that drifted from the compiled declaration -- by re-deriving the POVMs from
    the specification, say, or by rounding anywhere -- would show up here as an
    inequality of rationals rather than as a small discrepancy.
    """
    # See :func:`compiled_or_refused` on the two classes of weight pair.
    declaration = compiled_or_refused(
        (*case.alice_weights, *case.bob_weights)  # type: ignore[arg-type]
    )
    if declaration is None:
        return
    distribution = honest_distribution(declaration, F(0))
    assert tuple(distribution[c] for c in BB84_ACCEPTANCE_ALPHABET) == case.phi_vector
    assert sum(distribution.values()) == 1


@pytest.mark.oracle
def test_the_frozen_rows_are_the_closed_form_at_zero_error() -> None:
    """The registry's own numbers and ``bb84_targets``'s derivation agree.

    Two independently authored halves of the same claim: the frozen row was
    hand-derived in the step-2 registry, and :func:`honest_phi` is derived again
    in ``tests/support/bb84_targets.py`` from the mixture. Neither was written
    from the other.
    """
    for case in BB84_CASES:
        closed = honest_phi(*case.alice_weights, *case.bob_weights, F(0))
        assert tuple(closed[c] for c in BB84_ACCEPTANCE_ALPHABET) == case.phi_vector


# ---------------------------------------------------------------------------
#  Against the closed form, at every Q.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("weights", WEIGHTS)
@pytest.mark.parametrize(
    "qber", [F(0), F(1, 100), F(1, 50), F(1, 20), F(11, 100), F(1, 4), F(49, 100)]
)
def test_the_provider_is_the_closed_form_at_every_error_rate(
    weights: tuple[F, F, F, F], qber: F
) -> None:
    """``Phi_D[omega(Q)]`` against ``bb84_targets.honest_phi``, as exact rationals."""
    # See :func:`compiled_or_refused` on the two classes of weight pair.
    declaration = compiled_or_refused(weights)
    if declaration is None:
        return
    assert honest_distribution(declaration, qber) == honest_phi(*weights, qber)


@pytest.mark.parametrize("weights", WEIGHTS)
@pytest.mark.parametrize("qber", [F(0), F(1, 50), F(11, 100), F(3, 10)])
def test_three_of_the_four_coordinates_do_not_move_with_the_error_rate(
    weights: tuple[F, F, F, F], qber: F
) -> None:
    """The structural fact the whole slice rests on.

    ``sum_a M_{(b,a)} = p^A_b 1_A`` and ``sum_y F_{(b',y)} = p^B_{b'} 1_Q``, so
    ``gen``, ``disc`` and the total ``ok + err`` are the same for EVERY state,
    let alone for every ``Q``. It is asserted here because everything in
    ``bb84_targets`` -- the one-dimensional reduced program above all -- is built
    on it.
    """
    alice_z, alice_x, bob_z, bob_x = weights
    # See :func:`compiled_or_refused` on the two classes of weight pair.
    declaration = compiled_or_refused(weights)
    if declaration is None:
        return
    distribution = honest_distribution(declaration, qber)
    assert distribution["gen"] == alice_z * bob_z
    assert distribution["disc"] == alice_z * bob_x + alice_x * bob_z
    assert distribution["ok"] + distribution["err"] == alice_x * bob_x


def test_the_error_mass_is_linear_in_the_model_parameter() -> None:
    """``Phi(err) = p^A_X p^B_X Q``: the one coordinate a state gets to choose."""
    declaration = compiled(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    for numerator in range(0, 25):
        qber = F(numerator, 50)
        assert honest_distribution(declaration, qber)["err"] == F(1, 4) * qber


def test_the_visibility_is_the_declared_one() -> None:
    assert visibility(F(0)) == 1
    assert visibility(F(1, 4)) == F(1, 2)
    assert visibility(F(49, 100)) == F(1, 50)


def test_the_honest_state_carries_the_declared_trusted_marginal() -> None:
    """``tr_Q omega(Q) = 1_A/2 = tau_A`` -- so the state is inside Eq. ``eq:feas``.

    Checked by the provider itself on every call, and asserted here so that the
    check is visible rather than only exercised. A honest state that missed the
    declared marginal would induce a distribution no feasible state realises,
    and the acceptance set built around it would be unreachable.
    """
    from certiqs_key.foundations.exact import equal, partial_trace_second

    declaration = compiled(F(3, 4), F(1, 4), F(7, 8), F(1, 8))
    assert declaration.alice_marginal is not None
    for qber in (F(0), F(1, 50), F(2, 5)):
        marginal = partial_trace_second(depolarized_state(qber), 2, 2)
        assert equal(marginal, declaration.alice_marginal)


# ---------------------------------------------------------------------------
#  QBER is a diagnostic, and the domain is guarded.
# ---------------------------------------------------------------------------


def test_the_sifted_error_rate_is_a_derived_diagnostic() -> None:
    """``err / (ok + err) = Q``, and it is nowhere the interface.

    spec/architecture.md 4.3: "QBER may be a derived diagnostic. It is not the
    general statistics interface." The value is the model's ``Q`` exactly, which
    is what makes it a legible diagnostic; what makes it not the interface is
    that :func:`honest_distribution` never produces it and nothing in the
    pipeline consumes it.
    """
    declaration = compiled(F(3, 4), F(1, 4), F(1, 2), F(1, 2))
    for qber in (F(1, 100), F(1, 20), F(11, 100)):
        assert sifted_error_rate(honest_distribution(declaration, qber)) == qber


def test_the_provider_refuses_a_marginal_the_honest_state_does_not_carry() -> None:
    """The guard is exercised, not merely asserted in the direction that holds.

    Every member of the Werner family has ``omega_A = 1_A/2``, so the positive
    check above cannot fail whether or not the guard exists. What must be
    exercised is the branch: a declaration whose ``tau_A`` the honest state
    MISSES induces a distribution no feasible state realises, and an acceptance
    set built around it would be unreachable (meat-core ``rem:hlow-range``).
    """
    from dataclasses import replace

    from certiqs_key.foundations.exact import matrix

    declaration = compiled(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    skewed = replace(declaration, alice_marginal=matrix(((F(3, 4), 0), (0, F(1, 4)))))
    with pytest.raises(HonestModelError, match="not the declared tau_A"):
        honest_distribution(skewed, F(1, 50))


def test_the_provider_refuses_an_untrusted_source_declaration() -> None:
    """No ``tau_A`` declared, so nothing here stands in for one.

    The source-replacement model of spec/architecture.md 4.3 is a
    trusted-marginal one; in untrusted-source mode the marginal slot is
    ``none`` and the provider refuses rather than supplying a default.
    """
    from dataclasses import replace

    declaration = compiled(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    untrusted = replace(declaration, alice_marginal=None)
    with pytest.raises(HonestModelError, match="untrusted-source mode"):
        honest_distribution(untrusted, F(1, 50))


def test_the_sifted_rate_refuses_where_there_is_no_sifted_subset() -> None:
    with pytest.raises(HonestModelError, match="no sifted subset"):
        sifted_error_rate({"ok": F(0), "err": F(0), "gen": F(1)})
    with pytest.raises(HonestModelError, match="not an outcome"):
        sifted_error_rate({"gen": F(1)})


@pytest.mark.parametrize("qber", [F(1, 2), F(3, 4), F(-1, 100), F(1)])
def test_an_error_rate_outside_the_model_domain_is_refused(qber: F) -> None:
    declaration = compiled(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    with pytest.raises(HonestModelError, match=r"\[0, 1/2\)"):
        honest_distribution(declaration, qber)


@pytest.mark.parametrize("qber", [0.02, "1/50", 0, 1])
def test_an_inexact_error_rate_is_refused_rather_than_widened(qber: object) -> None:
    """A ``float`` reaching the exact substrate is a defect, not a convenience.

    ``Fraction(0.02)`` is ``360287970189639/18014398509481984``, and every
    number downstream would be exact arithmetic on that. The refusal is at the
    boundary, where the caller can see it. Plain ``int`` is refused too: the
    annotation says ``Fraction`` and the guard enforces the annotation rather
    than a superset of it.
    """
    declaration = compiled(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    with pytest.raises(HonestModelError, match="exact rational"):
        honest_distribution(declaration, qber)  # type: ignore[arg-type]


def test_the_provider_refuses_a_declaration_it_does_not_model() -> None:
    """One qubit through one depolarizing channel, and nothing else.

    ``conjugation_example_specification`` compiles to a declaration with the
    same ``d_A d_Q = 4`` but a different acceptance alphabet, so it is NOT
    refused on dimension -- and it should not be, since the honest state is a
    perfectly good state for it. The case this guard exists for is a declaration
    whose ``A (x) Q`` is not two qubits at all.

    THE ``block_kind`` IS CARRIED FROM THE DECLARATION AND NOT SUPPLIED HERE.
    ``SectorStructure`` gained it as a REQUIRED component at
    ``protocol-compiler`` 0.3.0 -- the sector map is "ONE OBJECT" whose three
    components are all machine keys, "so that a consumer comparing sector maps
    can compare all three and not two of them" -- and a test naming a kind of
    its own would be deciding what the identifiers of somebody else's map mean,
    which that contract's Section 2.5 (``decide_never_infer``) forbids.
    Widening a dimension does not change what the blocks ARE, so the kind is
    the one the compiled declaration already carries.

    THE XFAIL THIS TEST CARRIED WAS MISATTRIBUTED. Its reason named the
    acceptance-data exactness of ``meat-core`` Section 2.6, and this test
    declares no acceptance set at all: it failed with a ``TypeError`` from the
    missing ``block_kind`` above, which is a test that was never updated for a
    required field rather than a refusal by any rule.
    """
    from dataclasses import replace

    from certiqs_key.protocol_compiler.spec import SectorStructure

    declaration = compiled(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    widened = replace(
        declaration,
        sectors=SectorStructure(
            labels=("s0",), dims=(3,), block_kind=declaration.sectors.block_kind
        ),
    )
    with pytest.raises(HonestModelError, match="d_A \\* d_Q = 4"):
        honest_distribution(widened, F(1, 50))


# ---------------------------------------------------------------------------
#  Stable IDs: a bijection, or a refusal.
# ---------------------------------------------------------------------------


def test_the_bb84_labels_sanitize_to_the_documented_ids() -> None:
    """``(Z,0) -> _Z_0_``: mechanical, and legible in a manifest."""
    assert sanitize("(Z,0)") == "_Z_0_"
    assert sanitize("(X,1)") == "_X_1_"
    assert sanitize("Z") == "Z"
    assert sanitize("gen") == "gen"
    assert sanitize("") == "_"


def test_a_label_collision_is_refused_rather_than_disambiguated() -> None:
    """Two labels mapping to one ID is a MERGE, and merges lose a row."""
    from certiqs_key.runs import SliceAssemblyError

    with pytest.raises(SliceAssemblyError, match="MERGE"):
        stable_id_map(("(Z,0)", "{Z;0}"), "alice_outcome")
    # `-`, `+` and `.` are admitted characters, so labels differing only in
    # those survive as distinct IDs and are NOT a collision.
    assert dict(stable_id_map(("(Z,0)", "[Z-0]"), "alice_outcome")) == {
        "(Z,0)": "_Z_0_",
        "[Z-0]": "_Z-0_",
    }


def test_the_map_is_total_and_order_preserving_on_the_bb84_alphabets() -> None:
    declaration = compiled(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    mapping = stable_id_map(declaration.alice_alphabet, "alice_outcome")
    assert tuple(mapping) == declaration.alice_alphabet
    assert len(set(mapping.values())) == len(declaration.alice_alphabet)
