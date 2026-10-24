"""``reductions/lem:precomposition`` as a property, and its counterexample.

The lemma: an attack admissible for a licensed list (Hermitian ``O_k``, real
``c_k``) stays admissible after ANY channel ``Gamma`` is composed in front of
it, in trusted-source mode (i), untrusted-source mode (ii) and for
``party_local`` entries (iii); and (iv) the inclusion fails for a Hermitian
right-hand side that is not a multiple of the identity, which is why the
licensed-only rule of ``reductions/def:chain`` refuses a ``general`` entry
beside a source link. The refusal itself is tested in
``tests/unit/test_protocol_general_format.py``
(``test_a_general_entry_beside_a_non_empty_source_segment_is_refused``); this
file tests the mathematics the refusal rests on, which no other
test covers.

No engine code implements the lemma, since it is an inclusion of attack
sets, so the test is linear algebra on small dimensions: channels are random
Kraus families, adjoints are formed from them, and each condition is decided
by an eigenvalue. Binary64, per the floats-by-default rule; every
tolerance is rounding. Each ``c_k`` is chosen TIGHT (an extreme eigenvalue of
the attack's own adjoint), so the hypothesis holds with equality somewhere
and a precomposition that lowered it would be caught.

Part (iii)'s condition quantifies over every reference ``R'`` and every
``X >= 0``; that is the statement that the map
``Lambda(X) = A^dagger(X (x) D (x) 1_{E''})``, ``D = O_k - c_k 1``, is
COMPLETELY POSITIVE, which one Choi matrix decides. Precomposition turns
``Lambda`` into ``Gamma^dagger o Lambda``.
"""

from __future__ import annotations

import numpy as np
import pytest

_ATOL = 1e-12
_SEEDS = tuple(range(8))

Kraus = list[np.ndarray]


def _random_channel(
    rng: np.random.Generator, d_in: int, d_out: int, rank: int
) -> Kraus:
    """Return the Kraus operators of a random CPTP map ``d_in -> d_out``."""
    shape = (d_out * rank, d_in)
    stacked = rng.normal(size=shape) + 1j * rng.normal(size=shape)
    isometry, _ = np.linalg.qr(stacked)
    return [isometry[k * d_out : (k + 1) * d_out, :] for k in range(rank)]


def _adjoint(kraus: Kraus, operator: np.ndarray) -> np.ndarray:
    """Return ``Phi^dagger(Y) = sum_k K_k^dagger Y K_k``."""
    return sum(k.conj().T @ operator @ k for k in kraus)


def _compose(first: Kraus, second: Kraus) -> Kraus:
    """Return the Kraus family of ``second o first``."""
    return [b @ a for a in first for b in second]


def _random_hermitian(rng: np.random.Generator, dim: int) -> np.ndarray:
    sample = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    return (sample + sample.conj().T) / 2


def _eigenvalues(operator: np.ndarray) -> np.ndarray:
    return np.linalg.eigvalsh((operator + operator.conj().T) / 2)


# Dimensions: E_pre, E', Q, E'' and, in untrusted mode, A. E_pre and E' differ
# so that Gamma is not an endomorphism.
_D_PRE, _D_E, _D_Q, _D_EVE, _D_A = 3, 2, 2, 2, 2


@pytest.mark.parametrize("untrusted", [False, True], ids=["i-trusted", "ii-untrusted"])
@pytest.mark.parametrize("seed", _SEEDS)
def test_scalar_entries_survive_precomposition(untrusted: bool, seed: int) -> None:
    """(i), (ii): ``A^dagger(Z) >= c 1`` implies ``(A o Gamma)^dagger(Z) >= c 1``."""
    rng = np.random.default_rng(seed)
    d_out = (_D_A if untrusted else 1) * _D_Q * _D_EVE
    attack = _random_channel(rng, _D_E, d_out, rank=3)
    gamma = _random_channel(rng, _D_PRE, _D_E, rank=3)
    observable = _random_hermitian(rng, _D_Q)
    tested = np.kron(
        np.kron(np.eye(_D_A if untrusted else 1), observable), np.eye(_D_EVE)
    )
    before = _eigenvalues(_adjoint(attack, tested))
    after = _eigenvalues(_adjoint(_compose(gamma, attack), tested))
    # succeq with the tight constant c = min eigenvalue; preceq with c = max.
    assert after.min() >= before.min() - _ATOL
    assert after.max() <= before.max() + _ATOL


def test_an_equality_entry_survives_precomposition() -> None:
    """(i) with ``=``: a replacement attack has ``A^dagger(Z) = tr[Z sigma] 1``."""
    rng = np.random.default_rng(99)
    sigma_vector = rng.normal(size=_D_Q * _D_EVE) + 1j * rng.normal(size=_D_Q * _D_EVE)
    sigma_vector /= np.linalg.norm(sigma_vector)
    # Replacement channel rho -> tr[rho] |s><s|, Kraus |s><i|.
    attack = [np.outer(sigma_vector, np.eye(_D_E)[i]) for i in range(_D_E)]
    gamma = _random_channel(rng, _D_PRE, _D_E, rank=2)
    tested = np.kron(_random_hermitian(rng, _D_Q), np.eye(_D_EVE))
    constant = np.real(sigma_vector.conj() @ tested @ sigma_vector)
    assert np.allclose(_adjoint(attack, tested), constant * np.eye(_D_E), atol=_ATOL)
    assert np.allclose(
        _adjoint(_compose(gamma, attack), tested),
        constant * np.eye(_D_PRE),
        atol=_ATOL,
    )


# Part (iii): Q = Q_1 (x) Q_2, the entry scoped to the SECOND factor.
_D_Q1, _D_Q2 = 2, 2
_D_OP = np.diag([0.5, -0.5]).astype(np.complex128)  # O = |0><0|, c = 1/2


def _lambda_choi(attack: Kraus, d_in: int, deficit: np.ndarray) -> np.ndarray:
    """Return the Choi matrix of ``X -> A^dagger(X (x) D (x) 1_{E''})`` on ``Q_1``."""
    blocks = []
    for i in range(_D_Q1):
        row = []
        for j in range(_D_Q1):
            unit = np.zeros((_D_Q1, _D_Q1), dtype=np.complex128)
            unit[i, j] = 1.0
            row.append(
                _adjoint(attack, np.kron(np.kron(unit, deficit), np.eye(_D_EVE)))
            )
        blocks.append(row)
    choi = np.block(blocks)
    assert choi.shape == (_D_Q1 * d_in, _D_Q1 * d_in)
    return choi


def _product_attack(rng: np.random.Generator) -> Kraus:
    """Return a measure-and-prepare attack with PRODUCT outputs on ``Q_1 Q_2``.

    ``A(rho) = sum_j tr[P_j rho] sigma_j (x) tau_j (x) epsilon_j``, with each
    ``tau_j`` weighted towards ``|0>`` so that ``tr[D tau_j] >= 0``. Then
    ``Lambda(X) = sum_j tr[X sigma_j] tr[D tau_j] P_j`` is completely positive:
    the attack satisfies the party-local entry although ``D`` is indefinite.
    """
    kraus: Kraus = []
    povm = _random_channel(rng, _D_E, 1, rank=3)  # rows of an isometry: a POVM
    for element in povm:
        s = rng.normal(size=_D_Q1) + 1j * rng.normal(size=_D_Q1)
        t = np.asarray([1.0 + abs(rng.normal()), 0.3 * rng.normal()], dtype=complex)
        e = rng.normal(size=_D_EVE) + 1j * rng.normal(size=_D_EVE)
        output = np.kron(np.kron(s, t), e)
        output /= np.linalg.norm(output)
        # Kraus |out><e_j|: rho -> <e_j|rho|e_j> |out><out|, P_j = |e_j><e_j|.
        kraus.append(np.outer(output, element.reshape(-1)).astype(np.complex128))
    return kraus


@pytest.mark.parametrize("relation", ["succeq", "preceq"])
@pytest.mark.parametrize("seed", _SEEDS)
def test_party_local_entries_survive_precomposition(relation: str, seed: int) -> None:
    """(iii): ``Lambda`` completely positive implies ``Gamma^dagger o Lambda`` is."""
    rng = np.random.default_rng(seed)
    deficit = _D_OP if relation == "succeq" else -_D_OP
    attack = _product_attack(rng)
    if relation == "preceq":
        # Weight the Q_2 outputs towards |1> instead: tr[-D tau_j] >= 0.
        swap = np.kron(np.kron(np.eye(_D_Q1), np.fliplr(np.eye(_D_Q2))), np.eye(_D_EVE))
        attack = [swap @ k for k in attack]
    assert np.allclose(
        sum(k.conj().T @ k for k in attack), np.eye(_D_E), atol=_ATOL
    )  # trace preserving
    before = _lambda_choi(attack, _D_E, deficit)
    assert _eigenvalues(before).min() >= -_ATOL
    gamma = _random_channel(rng, _D_PRE, _D_E, rank=3)
    after = _lambda_choi(_compose(gamma, attack), _D_PRE, deficit)
    assert _eigenvalues(after).min() >= -_ATOL


def test_the_party_local_condition_is_not_vacuous() -> None:
    """A generic attack FAILS the party-local entry, so passing it means something.

    ``D`` is indefinite, so the condition is not implied by positivity; a random
    channel violates it at some seed, which is what makes the precomposition
    test above a test.
    """
    minima = []
    for seed in _SEEDS:
        rng = np.random.default_rng(seed)
        attack = _random_channel(rng, _D_E, _D_Q1 * _D_Q2 * _D_EVE, rank=3)
        minima.append(_eigenvalues(_lambda_choi(attack, _D_E, _D_OP)).min())
    assert min(minima) < -1e-3


def test_iv_a_hermitian_right_hand_side_is_not_preserved() -> None:
    """(iv), the lemma's own counterexample, entry for entry.

    ``E_pre = E' = Q = C^2``, ``E''`` trivial, ``A = id``,
    ``O = Theta = |0><0|``, ``Gamma(rho) = tr[rho] |1><1|``. Every number is 0
    or 1, so binary64 is exact here.
    """
    ket0 = np.asarray([1.0, 0.0])
    ket1 = np.asarray([0.0, 1.0])
    observable = theta = np.outer(ket0, ket0)
    identity: Kraus = [np.eye(2)]
    gamma: Kraus = [np.outer(ket1, ket0), np.outer(ket1, ket1)]  # Kraus |1><i|
    assert np.array_equal(sum(k.T @ k for k in gamma), np.eye(2))
    # The condition holds for A with equality ...
    assert np.array_equal(_adjoint(identity, observable), theta)
    # ... and fails after precomposition: (A o Gamma)^dagger(O) = 0.
    composed = _adjoint(_compose(gamma, identity), observable)
    assert np.array_equal(composed, np.zeros((2, 2)))
    assert _eigenvalues(composed - theta).min() == -1.0
    # The scalar entry from the same operator, c = 0, is NOT broken: that is
    # the contrast the lemma draws.
    assert _eigenvalues(composed - 0.0 * np.eye(2)).min() >= 0.0
