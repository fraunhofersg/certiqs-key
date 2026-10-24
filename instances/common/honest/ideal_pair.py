"""Library model ``ideal_pair``: an exact Bell pair with erasure on both arms.

ONE MODEL for bbm92 and a protocol document; the derivation is in
``pair_models.md`` beside this module. The text below is the instance's own.

Both local one-photon bases are [V, H]. The correlated Bell pair therefore
has amplitudes [1, 0, 0, 1]/sqrt(2). Visibility mixes its projector with I/4;
each erasure replaces the lost photon by vacuum. No source marginal is
declared to the security program: this state is only its honest-data model.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Any, ClassVar, cast

from certiqs_key.foundations.blocks import JointBlockOperator
from certiqs_key.foundations.exact import (
    Matrix,
    add,
    as_scalar,
    identity,
    outer_projector,
    scale,
    vector,
    zeros,
)
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.protocol_compiler.statistics import (
    joint_distribution,
    phi_distribution,
)
from certiqs_key.runs.pipeline import (
    HonestProvider,
    RawJointProvider,
    factored_loss_applied,
    raw_factored_loss_applied,
)
from instances.common.honest.interface import (
    HonestContext,
    channel_mode_labels,
    precondition,
)
from instances.common.honest.tables import aggregate

__all__ = [
    "MODEL",
    "PAIR_NOTE",
    "IdealPair",
    "IdealPairModel",
    "honest_provider",
    "honest_state",
    "ideal_pair_block",
    "pair_preconditions",
]

#: The note fields both pair models share: bbm92's own shape (its
#: ``pipeline.py``), which names no module and adds its coin and key bases.
PAIR_NOTE: Mapping[str, Any] = {
    "source_trusted": False,
    "model_derivation": "instances/common/honest/pair_models.md",
    "status": "honest-data model; no source security attestation",
}


@dataclass(frozen=True)
class IdealPair:
    """An isotropic Bell pair, followed by independent arm loss."""

    alice_transmittance: Fraction = Fraction(1)
    bob_transmittance: Fraction = Fraction(1)
    visibility: Fraction = Fraction(1)

    def __post_init__(self) -> None:
        """Check the declared exact model parameters."""
        for name in ("alice_transmittance", "bob_transmittance", "visibility"):
            value = getattr(self, name)
            if not isinstance(value, Fraction) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be an exact rational in [0, 1]")


def ideal_pair_block(alice_dim: int, bob_dim: int, model: IdealPair) -> Matrix:
    """Put vacuum and one-photon components inside two preserved Fock blocks.

    Index zero is vacuum and indices one/two are V/H. Higher photon numbers
    carry zero weight. The four erasure events have weights eta_A eta_B,
    eta_A(1-eta_B), (1-eta_A)eta_B and (1-eta_A)(1-eta_B).
    """
    if alice_dim < 3 or bob_dim < 3:
        raise ValueError("the ideal-pair model needs both cutoffs at least one")
    a, b, visibility = (
        model.alice_transmittance,
        model.bob_transmittance,
        model.visibility,
    )
    bell = outer_projector(vector([1, 0, 0, 1]), Fraction(2))
    photon = add(scale(visibility, bell), scale((1 - visibility) / 4, identity(4)))
    block = [list(row) for row in zeros(alice_dim * bob_dim, alice_dim * bob_dim)]
    for i, j, k, ell in product(range(2), repeat=4):
        row = (i + 1) * bob_dim + j + 1
        col = (k + 1) * bob_dim + ell + 1
        block[row][col] = photon[2 * i + j][2 * k + ell] * as_scalar(a * b)
    block[0][0] = block[0][0] + as_scalar((1 - a) * (1 - b))
    for i in range(2):
        index = (i + 1) * bob_dim
        block[index][index] = block[index][index] + as_scalar(a * (1 - b) / 2)
        index = i + 1
        block[index][index] = block[index][index] + as_scalar((1 - a) * b / 2)
    return tuple(tuple(row) for row in block)


def honest_state(
    declaration: CandidateDeclaration, model: IdealPair
) -> JointBlockOperator:
    """Return an honest joint-sector state, with no weight on either flag space."""
    factors = declaration.measured_factors
    if declaration.alice_dim != 1 or len(factors) != 2:
        raise ValueError("BBM92 needs d_A=1 and exactly two measured factors")
    if declaration.alice_marginal is not None:
        raise ValueError("the BBM92 source is untrusted and declares no marginal")
    if any(factor.sectors.dims[:2] != (1, 2) for factor in factors):
        raise ValueError(
            "BBM92 ideal-pair factors start with vacuum and one-photon sectors"
        )
    physical = ideal_pair_block(3, 3, model)
    blocks: list[Matrix] = []
    for ai, bi in product(
        range(len(factors[0].sectors.dims)), range(len(factors[1].sectors.dims))
    ):
        da, db = factors[0].sectors.dims[ai], factors[1].sectors.dims[bi]
        if ai <= 1 and bi <= 1:
            left = (0,) if ai == 0 else (1, 2)
            right = (0,) if bi == 0 else (1, 2)
            indices = tuple(i * 3 + j for i, j in product(left, right))
            blocks.append(
                tuple(tuple(physical[i][j] for j in indices) for i in indices)
            )
        else:
            blocks.append(zeros(da * db, da * db))
    return JointBlockOperator.of(declaration.sectors, 1, blocks)


def honest_provider(model: IdealPair) -> HonestProvider:
    """Return exact acceptance frequencies for the emitted two-station model."""

    def provider(declaration: CandidateDeclaration) -> Mapping[str, Fraction]:
        frequencies = phi_distribution(declaration, honest_state(declaration, model))
        if frequencies.total != 1:
            raise ValueError("BBM92 honest frequencies do not sum to one")
        return dict(frequencies.values)

    return provider


def pair_preconditions(name: str, context: HonestContext) -> None:
    """Refuse anything but an untrusted pair source into two H/V optical stations.

    Shared by both pair models: an ``untrusted`` source with
    ``d_A = 1`` and one letter; exactly two optical stations, of parties ``A``
    and then ``B`` in station order, each with the ``H`` and ``V`` channel
    modes of one path and a photon cutoff of at least one. The station order
    is the declared factor order, and :func:`honest_state` gives the first
    factor Alice's arm.
    """
    source = context.source
    precondition(
        name,
        source is not None
        and source.kind == "untrusted"
        and source.alice_dim == 1
        and len(source.alphabet) == 1,
        "the pair source is untrusted and declares nothing to Alice, so it "
        "needs an untrusted source with d_A = 1 and one letter",
    )
    stations = context.stations
    precondition(
        name,
        len(stations) == 2 and all(s.kind == "optical" for s in stations),
        "a pair has two arms, so it needs exactly two optical stations",
    )
    precondition(
        name,
        tuple(s.party for s in stations) == ("A", "B"),
        "the arms are Alice's and then Bob's, so the stations' parties must be "
        f"A and then B; got {[s.party for s in stations]}",
    )
    for station in stations:
        precondition(
            name,
            channel_mode_labels(station) is not None,
            f"station {station.id!r}: each photon's polarization is written into "
            "the H and V modes of one path, so the channel modes must be "
            "exactly those two",
        )
        cutoff = station.photon_cutoff
        precondition(
            name,
            cutoff is not None and cutoff >= 1,
            f"station {station.id!r}: each arm carries up to one photon, so the "
            f"photon cutoff must be at least 1; got {cutoff}",
        )


class IdealPairModel:
    """The library entry ``ideal_pair``, evaluated through the declaration's POVMs.

    The raw ``X x V`` table is the compiler's own ``joint_distribution`` at
    :func:`honest_state`, and the acceptance distribution its aggregation
    through the declaration's announcement and acceptance maps -- the wiring
    bbm92 used. It reads no letter by name, so it needs no letter map.
    """

    name: ClassVar[str] = "ideal_pair"
    parameters: ClassVar[tuple[str, ...]] = (
        "alice_transmittance",
        "bob_transmittance",
        "visibility",
    )

    def note(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> dict[str, Any]:
        """Return bbm92's note shape for this model."""
        return {"model": "ideal_pair", **PAIR_NOTE}

    def preconditions(self, context: HonestContext) -> None:
        """Refuse anything but an untrusted pair into two H/V optical stations."""
        pair_preconditions(self.name, context)

    def providers(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> tuple[HonestProvider, RawJointProvider | None]:
        """Return the aggregated and raw providers of the ideal pair.

        THE FACTORED LOSS OF EACH STATION IS APPLIED TO ITS ARM
        (``receiver/detector-imperfections/req:loss-before-evaluation``). The
        declaration's POVMs are each station's NORMALIZED station where its
        receiver was compiled at ``t < 1``, and the device is that station
        after the pure-loss channel ``Lambda^loss_t`` on its channel modes. On
        this model's arm -- a photon kept with the arm transmittance, else
        vacuum -- the pure-loss channel is erasure with probability ``1 - t``,
        and two erasures compose by multiplying their transmittances, so the
        state handed to the normalized declaration is the pair at the arm
        transmittances times each station's ``t``: exactly the device's
        statistics, each station with the ``t`` of its own record.

        ``t`` IS READ WHEN THE PROVIDER IS CALLED, NOT WHEN IT IS BUILT. The
        run calls it only after the device stage has decided each station's
        factor, so a factor outside ``[eta_max, 1]`` is the receiver's refusal
        ``efficiency_normalization_out_of_range``
        (``req:efficiency-normalization``) and never an exception raised while
        the document is lowered. The bound parameters are checked here.
        """
        alice, bob = context.stations
        declared = IdealPair(
            cast(Fraction, bound["alice_transmittance"]),
            cast(Fraction, bound["bob_transmittance"]),
            cast(Fraction, bound["visibility"]),
        )

        def raw(
            declaration: CandidateDeclaration,
        ) -> Mapping[tuple[str, str], Fraction]:
            device = IdealPair(
                declared.alice_transmittance * alice.factored_loss,
                declared.bob_transmittance * bob.factored_loss,
                declared.visibility,
            )
            return joint_distribution(declaration, honest_state(declaration, device))

        return factored_loss_applied(aggregate(raw)), raw_factored_loss_applied(raw)


#: The one instance of this model the registry holds.
MODEL = IdealPairModel()
