"""The channel interface as data, and the honest model checked against it.

A caller computing
honest statistics for a channel of its own has three of the four things it
needs on artefacts already; the fourth -- HOW THE TRANSMITTED SYSTEM ``A'``
ENTERS THE RECEIVER'S CHANNEL INPUT MODES -- lived only inside each instance's
``honest.py``, so a simulator would have hardcoded the encoding per instance.

THE TEST that matters is the one that makes the data trustworthy: the
instance's own ``honest.py`` equals
``Tr[(A_x (x) B_v) (id (x) Lambda_inst)(V Psi V^dagger)]`` COMPUTED FROM THESE
DATA, exactly. If the declared encoding were the transpose of the real one --
the ascending-occupation trap -- the state would still be a state with the
right marginal and the distribution would differ in one basis only, which is
what this catches.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from instances.bb84.specification import bb84_specification
from instances.bb84.surface import channel_interface as qubit_interface
from instances.common.honest.depolarized_bell_pair import PHI_PLUS, honest_distribution

from certiqs_key.foundations.exact import (
    Matrix,
    add,
    conjugate_transpose,
    equal,
    identity,
    kron,
    matmul,
    partial_trace_second,
    scale,
    zeros,
)
from certiqs_key.protocol_compiler import compile_specification, phi_distribution
from certiqs_key.runs.channel import ChannelInterface

pytestmark = pytest.mark.contract

QBERS = (F(0), F(1, 100), F(1, 20))


def depolarised(psi: Matrix, qber: F, dimension: int) -> Matrix:
    """Return ``(id (x) Lambda_depol)(Psi)`` on ``A (x) A'``, exactly.

    ``Lambda_depol(rho) = v rho + (1 - v) tr[rho] 1/d`` with ``v = 1 - 2Q``,
    which is the depolarizing channel both instances declare. Applied to a
    maximally entangled ``Psi`` it gives the Werner family, and that identity
    is what the two honest models are written in -- so this function is the
    CHANNEL side of the formula and nothing else.
    """
    visibility = 1 - 2 * qber
    mixed = scale(F(1, 2 * dimension), identity(2 * dimension))
    return add(scale(visibility, psi), scale(1 - visibility, mixed))


# ===========================================================================
#  The shape, on every instance
# ===========================================================================


def test_the_interface_of_a_declared_finite_povm_is_the_identity() -> None:
    """No modes, no cutoff, and ``V`` the identity on ``A'``.

    The keys are present and null rather than absent: one shape for every
    instance, so a consumer reads one record on both routes.
    """
    interface = qubit_interface()
    assert isinstance(interface, ChannelInterface)
    assert interface.transmitted_dimension == 2
    assert interface.transmitted_basis == ("0", "1")
    assert interface.channel_modes is None
    assert interface.photon_cutoff is None
    assert interface.photon_blocks_basis is None
    assert equal(interface.encoding, identity(2))


def test_the_interface_survives_json_and_its_encoding_is_exact() -> None:
    """A consumer reads the isometry back without rounding."""
    import json

    from certiqs_key.foundations.exact import deserialize_matrix

    payload = qubit_interface().as_payload()
    assert json.loads(json.dumps(payload)) == payload
    assert equal(deserialize_matrix(payload["encoding"]), qubit_interface().encoding)


# ===========================================================================
#  The qubit instance: V is the identity, so the formula is the model
# ===========================================================================


@pytest.mark.parametrize("qber", QBERS)
def test_the_qubit_honest_model_is_the_formula_computed_from_the_data(
    qber: F,
) -> None:
    """``honest.py`` == ``Tr[(A_x (x) B_v)(id (x) Lambda)(V Psi V^dag)]``.

    On this route ``V`` is the identity, so the formula reduces to the channel
    applied to the declared ``Psi`` -- and that is the point: the interface
    says the encoding is trivial, and the test shows that reading it that way
    reproduces the instance's own numbers rather than merely being consistent
    with them.
    """
    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    declaration = result.declaration
    assert declaration is not None

    interface = qubit_interface()
    encoding = interface.encoding
    psi = PHI_PLUS  # the certificate's Psi on A (x) A', with A first

    # (id (x) V) Psi (id (x) V)^dagger, which is Psi itself here.
    embedded = matmul(
        matmul(kron(identity(2), encoding), psi),
        conjugate_transpose(kron(identity(2), encoding)),
    )
    state = depolarised(embedded, qber, interface.transmitted_dimension)

    assert dict(phi_distribution(declaration, state).values) == honest_distribution(
        declaration, qber
    )


# ===========================================================================
#  The optical instance: V is the single-photon encoding
# ===========================================================================


@pytest.mark.parametrize("qber", QBERS)
@pytest.mark.parametrize("transmittance", [F(1), F(1, 2), F(1, 8)])
def test_the_optical_honest_model_is_the_formula_computed_from_the_data(
    qber: F, transmittance: F
) -> None:
    """The same equality, where ``V`` is a genuine isometry into Fock space.

    THE CHANNEL, WRITTEN IN THE INTERFACE'S OWN TERMS. The instance's
    ``Lambda_inst`` is the depolarizer on the polarization qubit followed by
    loss: with probability ``eta`` the encoded photon arrives, and otherwise
    the receiver sees vacuum with Alice's marginal untouched. Both halves are
    expressed here through ``V`` and ``Psi`` alone -- nothing reaches into
    ``honest.py`` for a state -- and the result is compared against what that
    module builds.

    THE ASCENDING-OCCUPATION TRAP IS WHAT THIS CATCHES. If ``V``'s two columns
    were swapped the state would still be a state with the right marginal, and
    the X-basis error rate alone would move.
    """
    from instances.common.honest.single_photon_loss_depolarizing import channel_state
    from instances.common.honest.single_photon_loss_depolarizing import (
        honest_distribution as optical_honest,
    )
    from instances.common.optics import ReceiverParameters
    from instances.optical_bb84.surface import channel_interface
    from optical_bb84_prologue import run_prologue

    prologue = run_prologue(
        ReceiverParameters(photon_cutoff=1), declared_tolerance=1e-12
    )
    declaration = prologue.compilation.declaration
    assert declaration is not None
    interface = channel_interface(prologue.receiver)
    assert interface.channel_modes is not None
    assert interface.photon_cutoff == 1

    q_dim = declaration.q_dim
    preserved = len(interface.photon_blocks_basis or ())

    # (id (x) V) applied to the DEPOLARISED source state, padded onto Q.
    psi = PHI_PLUS  # the same Psi: both instances declare the same source
    depolarised_source = depolarised(psi, qber, interface.transmitted_dimension)
    encoded = matmul(
        matmul(
            kron(identity(2), interface.encoding),
            depolarised_source,
        ),
        conjugate_transpose(kron(identity(2), interface.encoding)),
    )
    arrived = _padded(encoded, alice_dim=2, source_dim=preserved, q_dim=q_dim)

    # ... and the lost half: vacuum, with Alice's marginal untouched. The
    # vacuum is basis vector 0 of the declared Fock order, which the interface
    # states rather than this test assuming.
    assert (interface.photon_blocks_basis or ())[0] == "0,0"
    vacuum = _vacuum(alice_dim=2, q_dim=q_dim)
    marginal = partial_trace_second(
        depolarised_source, 2, interface.transmitted_dimension
    )
    state = add(
        scale(transmittance, arrived),
        scale(1 - transmittance, kron(marginal, vacuum)),
    )

    built = channel_state(
        qber=qber, transmittance=transmittance, cutoff=1, q_dim=q_dim
    )
    assert equal(state, built)
    assert dict(phi_distribution(declaration, state).values) == optical_honest(
        declaration, qber=qber, transmittance=transmittance, cutoff=1
    )


def _padded(operator: Matrix, *, alice_dim: int, source_dim: int, q_dim: int) -> Matrix:
    """Return an ``A (x) C_{<=N}`` operator placed inside ``A (x) Q``.

    ``A`` is first, so the composite index of ``(i, c)`` is ``i * q_dim + c``;
    every flag sector carries no weight, which is what "the source sends at
    most one photon" means on the squashed space.
    """
    out = [list(row) for row in zeros(alice_dim * q_dim, alice_dim * q_dim)]
    for a_row in range(alice_dim):
        for c_row in range(source_dim):
            row = a_row * q_dim + c_row
            for a_col in range(alice_dim):
                for c_col in range(source_dim):
                    column = a_col * q_dim + c_col
                    out[row][column] = operator[a_row * source_dim + c_row][
                        a_col * source_dim + c_col
                    ]
    return tuple(tuple(entry) for entry in out)


def _vacuum(*, alice_dim: int, q_dim: int) -> Matrix:
    """Return ``|vac><vac|`` on ``Q``: basis vector 0 of the declared order."""
    del alice_dim
    out = [list(row) for row in zeros(q_dim, q_dim)]
    out[0][0] = identity(1)[0][0]
    return tuple(tuple(entry) for entry in out)


# ===========================================================================
#  The factored loss travels with the blocks it stands in front of
# ===========================================================================

#: The detector ports of every optical instance's common passive receiver.
_PORTS = ("H", "V", "D", "A")


def test_the_channel_interface_names_each_arms_factored_loss() -> None:
    """req:loss-before-evaluation: a consumer evaluating photon_blocks reads t."""
    from instances.bbm92 import surface

    base = surface.default_config()
    prepared = surface.preparation(
        base.with_(
            device={
                **base.device,
                "alice_efficiency": dict.fromkeys(_PORTS, F(3, 5)),
                "bob_efficiency": dict.fromkeys(_PORTS, F(1, 5)),
            }
        )
    )
    arms = prepared.channel_interface.as_payload()["arms"]
    # The default factor eta_max / (99/100): (3/5)(100/99), (1/5)(100/99).
    assert [arm["factored_loss"] for arm in arms] == ["20/33", "20/99"]


@pytest.mark.parametrize("instance", ["optical_bb84", "decoy_bb84"])
def test_a_single_station_interface_names_its_factored_loss(instance: str) -> None:
    """req:loss-before-evaluation, on the single-photon and the WCP interfaces.

    The factor is the receiver artefact's own
    (``efficiency_record.normalization``), written exactly; at a declared
    ``t = 1`` it is ``"1"``, so a consumer reads the key on every run.
    """
    import importlib

    surface = importlib.import_module(f"instances.{instance}.surface")
    base = surface.default_config()
    for device, expected in (
        # The default factor (3/5)(100/99) = 20/33.
        ({"efficiency": dict.fromkeys(_PORTS, F(3, 5))}, "20/33"),
        (
            {
                "efficiency": dict.fromkeys(_PORTS, F(3, 5)),
                "efficiency_normalization": F(1),
            },
            "1",
        ),
    ):
        prepared = surface.preparation(base.with_(device={**base.device, **device}))
        receiver = prepared.receiver_artifact
        assert receiver is not None
        assert str(receiver.efficiency_record.normalization.factored_loss) == expected
        payload = prepared.channel_interface.as_payload()
        arm = payload.get("arm", payload)
        assert arm["factored_loss"] == expected


def test_the_declared_finite_povm_interface_has_no_factored_loss() -> None:
    """No receiver is compiled on that route, so the key is present and null."""
    interface = qubit_interface()
    assert interface.factored_loss is None
    assert interface.as_payload()["factored_loss"] is None
