"""Library model ``single_photon_loss_depolarizing``: one photon, a depolarizer, loss.

ONE MODEL for optical BB84, any instance written in Python that reads
:data:`PHI_PLUS_FOCK`, and a protocol document. The text below is
the instance's own.

WHAT THE MODEL IS
=================
Source replacement puts a trusted virtual qubit ``A`` beside the transmitted
system, and the honest channel acts on the transmitted half. Here that half is
OPTICAL: two polarization modes, and what arrives at Bob is a state on the
truncated Fock space ``H(C_{<=N})`` the receiver's blocks are graded by. The
honest model is the simplest one that has anything to say about loss:

    rho(Q, eta) = eta * [ omega(Q) on A (x) C_1 ]  +  (1 - eta) * [ tau_A (x) vac ]

-- a single photon that arrives with probability ``eta`` carrying the Werner
state ``omega(Q) = v |Phi+><Phi+| + (1 - v) 1/4``, ``v = 1 - 2Q``, and vacuum
otherwise. Both ``Q`` and ``eta`` are exact rationals and MODEL parameters, never
observed frequencies; a ``float`` is refused rather than widened, for the reason
:mod:`instances.common.honest.depolarized_bell_pair` gives.

DARK COUNTS ARE NOT IN THE STATE, AND THAT IS THE POINT
=======================================================
They are in the POVM. ``receiver`` Definition ``def:darkadm`` puts the
dark-count channel ``R`` on the detector layer, so a declaration's dark counts
reach the distribution through Bob's own emitted blocks rather than through
anything written here. The exit condition's "degrades against dark-count rate"
is therefore a statement about the DEVICE, tested by changing a device parameter
and re-running -- not a statement about a term this module adds.

The same holds for detector efficiency: ``eta_k`` is a device parameter and lives
on the receiver, while ``eta`` here is the CHANNEL's transmittance. A run that
wants a lossy channel and perfect detectors, or the reverse, says so in the two
places separately, and the run record carries both.

WHY THE DISTRIBUTION IS READ THROUGH THE COMPILED DECLARATION
=============================================================
The squashed target ``H(Q) = H(C_{<=N}) (+) H(Flag)`` carries the physical
subspace as its first summand, and the weight-preserving flag-state squasher
PRESERVES the below-cutoff blocks -- restricted to that summand, the emitted
``F_v`` is the declared ``blk M_v``. So a state supported entirely on
``H(C_{<=N})``, which this one is for every ``N >= 1``, can be embedded into
``H(Q)`` by padding with zeros, and

    tr[(1 (x) F_v) omega_Q]  =  tr[(1 (x) M_v) rho]

exactly. The embedded state is a feasible state of the squashed model with the
same ``A``-marginal, and its statistics ARE the physical ones.

That is what lets this module hand the state to
:func:`certiqs_key.protocol_compiler.phi_distribution` and read the acceptance
distribution off the declaration a compilation actually emitted, rather than re-deriving
the announcement and acceptance tables here. A change to the compiler's emission changes
this distribution in the same commit, and a regression shows up as a wrong number rather
than as two consistent-looking halves. The preservation property itself is asserted in
the tests rather than assumed.

THE FOCK BASIS ORDER IS THE TRAP, AND IT IS NOT THE OBVIOUS ONE
===============================================================
:mod:`certiqs_key.receiver.fock` fixes occupation vectors in ASCENDING lexicographic
order, so on two modes the one-photon block is indexed ``[(0,1), (1,0)]`` -- the
photon in the LAST mode first. The channel's modes are declared ``(Z_H, Z_V)``,
so the one-photon block's basis is ``[|V>, |H>]`` and NOT ``[|H>, |V>]``. That is
verified against the emitted blocks in the tests; here it means
``|Phi+> = (|0>_A|H> + |1>_A|V>)/sqrt2`` has amplitudes ``[0, 1, 1, 0]`` on
``A (x) C_1`` and not ``[1, 0, 0, 1]``. Getting it backwards produces a state
that is still a state, still has the right marginal, and gives the wrong error
rate in the X basis only -- which is the hardest kind of mistake to see.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any, ClassVar, cast

from certiqs_key.foundations.exact import (
    ONE,
    Matrix,
    add,
    equal,
    identity,
    outer_projector,
    partial_trace_second,
    scale,
    vector,
    zeros,
)
from certiqs_key.protocol_compiler import (
    CandidateDeclaration,
    joint_distribution,
    phi_distribution,
)
from certiqs_key.runs.pipeline import (
    HonestProvider,
    RawJointProvider,
    factored_loss_applied,
    raw_factored_loss_applied,
)
from instances.common.errors import OpticalModelError
from instances.common.honest.interface import (
    HonestContext,
    channel_mode_labels,
    precondition,
)

__all__ = [
    "MODEL",
    "PHI_PLUS_FOCK",
    "SinglePhotonLossDepolarizing",
    "channel_state",
    "honest_distribution",
    "honest_provider",
    "preserved_dimension",
    "raw_joint_distribution",
    "raw_joint_provider",
    "visibility",
]

#: ``|Phi+><Phi+|`` on ``A (x) C_1``, exactly, with ``A`` first and the ONE-PHOTON
#: block in its own ascending-occupation basis ``[|V>, |H>]``. See the module
#: docstring: the amplitudes are ``[0, 1, 1, 0]`` for that reason and no other.
PHI_PLUS_FOCK: Matrix = outer_projector(vector([0, 1, 1, 0]), Fraction(2))

#: ``1_{A (x) C_1} / 4``: the fully depolarized end of the family, at ``v = 0``.
_MAXIMALLY_MIXED: Matrix = scale(Fraction(1, 4), identity(4))


def preserved_dimension(cutoff: int) -> int:
    """Return ``dim H(C_{<=N})`` for two modes: ``(N+1)(N+2)/2``.

    The ``m``-photon block of two modes has dimension ``m + 1``, and the
    preserved space is their direct sum for ``m <= N``.
    """
    if cutoff < 0:
        raise OpticalModelError(f"the photon cutoff N is non-negative; got {cutoff}")
    return (cutoff + 1) * (cutoff + 2) // 2


def visibility(qber: Fraction) -> Fraction:
    """Return the channel visibility ``v = 1 - 2Q`` of the depolarizing model."""
    return 1 - 2 * _checked(qber, "Q", upper=Fraction(1, 2), open_upper=True)


def channel_state(
    *, qber: Fraction, transmittance: Fraction, cutoff: int, q_dim: int
) -> Matrix:
    """Return the honest joint state on ``A (x) Q``, exactly, with ``A`` first.

    Args:
        qber: ``Q``, the single-basis error parameter of the depolarizing
            channel, an exact rational in ``[0, 1/2)``.
        transmittance: ``eta``, the probability that the photon arrives, an exact
            rational in ``[0, 1]``. At ``eta = 0`` every round is vacuum and Bob
            never clicks except on dark counts.
        cutoff: ``N``. Only ``N >= 1`` can carry a single photon; at ``N = 0``
            the preserved space is the vacuum alone and this model has nothing to
            put in it.
        q_dim: the declaration's ``d_Q``. The state is padded with zeros on the
            flag sectors, which is what makes it a state of the squashed model
            with the physical statistics.
    """
    if cutoff < 1:
        raise OpticalModelError(
            "this model sends one photon, so it needs a cutoff of at least 1; "
            f"got N = {cutoff}. At N = 0 the preserved space is the vacuum alone "
            "and no single-photon state fits in it"
        )
    preserved = preserved_dimension(cutoff)
    if q_dim < preserved:
        raise OpticalModelError(
            f"the declaration's d_Q is {q_dim}, which is smaller than the "
            f"preserved dimension {preserved} at N = {cutoff}; this is not a "
            "declaration of the squashed model this instance builds"
        )
    weight = _checked(transmittance, "eta", upper=Fraction(1), open_upper=False)
    v = visibility(qber)
    photon = add(scale(v, PHI_PLUS_FOCK), scale(1 - v, _MAXIMALLY_MIXED))
    return add(
        scale(weight, _embedded_photon(photon, q_dim)),
        scale((1 - weight) * Fraction(1, 2), _vacuum(q_dim)),
    )


def _embedded_photon(block: Matrix, q_dim: int) -> Matrix:
    """Return a ``4 x 4`` operator on ``A (x) C_1`` placed inside ``A (x) Q``.

    ``A`` is first, so the composite index of ``(i, c)`` is ``i * q_dim + c``.
    The one-photon block sits at ``C`` indices 1 and 2, immediately after the
    one-dimensional vacuum block; every higher photon block and every flag sector
    carries no weight, because this source sends one photon.
    """
    out = [list(row) for row in zeros(2 * q_dim, 2 * q_dim)]
    for alice_row in range(2):
        for photon_row in range(2):
            row = alice_row * q_dim + 1 + photon_row
            for alice_col in range(2):
                for photon_col in range(2):
                    column = alice_col * q_dim + 1 + photon_col
                    out[row][column] = block[alice_row * 2 + photon_row][
                        alice_col * 2 + photon_col
                    ]
    return tuple(tuple(row) for row in out)


def _vacuum(q_dim: int) -> Matrix:
    """Return ``1_A (x) |vac><vac|`` on ``A (x) Q``, unnormalized.

    Scaled by ``(1 - eta) / 2`` it is ``(1 - eta) tau_A (x) |vac><vac|`` at
    ``tau_A = 1_A / 2``, which is the declared marginal.
    """
    out = [list(row) for row in zeros(2 * q_dim, 2 * q_dim)]
    for alice in range(2):
        out[alice * q_dim][alice * q_dim] = ONE
    return tuple(tuple(row) for row in out)


def _checked_state(
    declaration: CandidateDeclaration,
    *,
    qber: Fraction,
    transmittance: Fraction,
    cutoff: int,
) -> Matrix:
    """Return the honest state, refused on the three grounds this model has.

    Split out so that the coarse distribution and the raw ``X x V`` one
    refuse on exactly the same grounds rather than one of them checking less.
    """
    if declaration.alice_dim != 2:
        raise OpticalModelError(
            "this model replaces one qubit source, so it applies to a "
            f"declaration with d_A = 2; this one has {declaration.alice_dim}"
        )
    state = channel_state(
        qber=qber,
        transmittance=transmittance,
        cutoff=cutoff,
        q_dim=declaration.q_dim,
    )
    if declaration.alice_marginal is None:
        raise OpticalModelError(
            "the honest state carries a trusted A-marginal, but the declaration "
            "is in untrusted-source mode and declares none; nothing here stands "
            "in for a tau_A that was not declared"
        )
    marginal = partial_trace_second(state, declaration.alice_dim, declaration.q_dim)
    if not equal(marginal, declaration.alice_marginal):
        raise OpticalModelError(
            "the A-marginal of the honest state is not the declared tau_A. Such "
            "a state is outside Eq. eq:feas, so the distribution it induces is "
            "reachable by no feasible state and an acceptance set built around "
            "it would be unreachable (meat-core Remark rem:hlow-range)"
        )
    return state


def raw_joint_distribution(
    declaration: CandidateDeclaration,
    *,
    qber: Fraction,
    transmittance: Fraction,
    cutoff: int,
) -> dict[tuple[str, str], Fraction]:
    """Return ``P_D[omega]`` on the RAW OUTCOME PAIRS ``X x V``, exactly.

    The same state and the same declaration as
    :func:`honest_distribution`, through the compiler's own
    :func:`~certiqs_key.protocol_compiler.joint_distribution`, so that the
    coarse distribution IS this one summed over the acceptance fibres and the
    two cannot drift.
    """
    state = _checked_state(
        declaration, qber=qber, transmittance=transmittance, cutoff=cutoff
    )
    return joint_distribution(declaration, state)


def honest_distribution(
    declaration: CandidateDeclaration,
    *,
    qber: Fraction,
    transmittance: Fraction,
    cutoff: int,
) -> dict[str, Fraction]:
    """Return ``p_honest`` on the declaration's own acceptance alphabet.

    One exact rational per declared acceptance value, summing to one over the
    WHOLE alphabet -- the discarded rounds included, which is where loss goes.

    Raises:
        OpticalModelError: if a parameter is outside its domain or is not an
            exact rational; if the declaration is not a two-dimensional-Alice
            squashed one; or if the emitted ``tau_A`` is not the marginal of the
            honest state, in which case the state is outside Eq. ``eq:feas``'s
            feasible set and the distribution it induces is reachable by no
            feasible state.
    """
    state = _checked_state(
        declaration, qber=qber, transmittance=transmittance, cutoff=cutoff
    )
    statistics = phi_distribution(declaration, state)
    if statistics.total != 1:
        # thm:measurements-and-statistics (iv) makes it one
        raise OpticalModelError(  # pragma: no cover
            f"Phi[omega] sums to {statistics.total}, not 1"
        )
    return dict(statistics.values)


def honest_provider(
    *, qber: Fraction, transmittance: Fraction, cutoff: int
) -> HonestProvider:
    """Return the optical model at these parameters as a declaration-only callable."""

    def provider(declaration: CandidateDeclaration) -> Mapping[str, Fraction]:
        return honest_distribution(
            declaration, qber=qber, transmittance=transmittance, cutoff=cutoff
        )

    return provider


def raw_joint_provider(
    *, qber: Fraction, transmittance: Fraction, cutoff: int
) -> RawJointProvider:
    """Return the raw ``X x V`` model at these parameters, as a callable."""

    def provider(
        declaration: CandidateDeclaration,
    ) -> Mapping[tuple[str, str], Fraction]:
        return raw_joint_distribution(
            declaration, qber=qber, transmittance=transmittance, cutoff=cutoff
        )

    return provider


def _checked(
    value: Fraction, name: str, *, upper: Fraction, open_upper: bool
) -> Fraction:
    """Return an exact rational after its domain check, or refuse.

    The annotation is checked at run time and not merely declared: a ``float``
    reaching the exact substrate would be widened silently by
    :class:`~fractions.Fraction` into the nearest binary rational, and the
    resulting distribution would be exact arithmetic on a number nobody wrote
    down.
    """
    if not isinstance(value, Fraction):
        raise OpticalModelError(
            f"{name} is an exact rational; got {value!r} of type "
            f"{type(value).__name__}. A float would be widened silently into the "
            "nearest binary rational, and the resulting distribution would be "
            "exact arithmetic on a number nobody wrote down"
        )
    if value < 0 or (value >= upper if open_upper else value > upper):
        bound = f"[0, {upper})" if open_upper else f"[0, {upper}]"
        raise OpticalModelError(f"{name} lies in {bound}; got {value}")
    return value


class SinglePhotonLossDepolarizing:
    """The library entry: a trusted qubit sent as one photon into one station.

    PRECONDITIONS: a trusted source with ``d_A = 2``; one optical
    station whose channel modes are the ``H`` and ``V`` modes of one path (the
    encoding :func:`channel_state` writes the photon into); a photon cutoff of
    at least one. The station's cutoff is the one context fact the providers
    read.
    """

    name: ClassVar[str] = "single_photon_loss_depolarizing"
    parameters: ClassVar[tuple[str, ...]] = ("qber", "transmittance")

    def note(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> dict[str, Any]:
        """Return optical BB84's note, with ``instance`` from the context."""
        return {
            "instance": context.instance,
            "model": (
                "one photon through a depolarizing channel with loss, evaluated "
                "exactly on the emitted declaration; dark counts are in the POVM "
                "and not in the state"
            ),
            "module": __name__,
            "overridden": False,
        }

    def preconditions(self, context: HonestContext) -> None:
        """Refuse anything but one trusted qubit into one H/V optical station."""
        source = context.source
        precondition(
            self.name,
            source is not None and source.kind == "trusted" and source.alice_dim == 2,
            "it replaces one trusted qubit source, so it needs a trusted source "
            "with d_A = 2",
        )
        precondition(
            self.name,
            len(context.stations) == 1 and context.stations[0].kind == "optical",
            "it sends one photon to one receiver, so it needs exactly one optical "
            "station",
        )
        station = context.stations[0]
        precondition(
            self.name,
            channel_mode_labels(station) is not None,
            "the photon's polarization is written into the H and V modes of one "
            "path, so the station's channel modes must be exactly those two",
        )
        cutoff = station.photon_cutoff
        precondition(
            self.name,
            cutoff is not None and cutoff >= 1,
            f"it sends one photon, so it needs a photon cutoff of at least 1; got "
            f"{cutoff}",
        )

    def providers(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> tuple[HonestProvider, RawJointProvider | None]:
        """Return the acceptance and raw providers at the station's cutoff.

        THE STATION'S FACTORED LOSS IS APPLIED TO THE PHOTON
        (``receiver/detector-imperfections/req:loss-before-evaluation``): the
        emitted blocks are the NORMALIZED station's where the receiver was
        compiled at ``t < 1``, the device being that station after the
        pure-loss channel ``Lambda^loss_t``. On this model's input -- one
        photon with probability ``eta``, else vacuum -- that channel is
        erasure with probability ``1 - t``, so the state handed to the
        declaration is the model's at transmittance ``eta * t``, exactly.

        ``t`` IS READ WHEN A PROVIDER IS CALLED, NOT WHEN IT IS BUILT. The run
        calls it only after the device stage has decided the station's factor,
        so a factor outside ``[eta_max, 1]`` is the receiver's refusal
        ``efficiency_normalization_out_of_range``
        (``req:efficiency-normalization``) and never an exception raised while
        the document is lowered.
        """
        station = context.stations[0]
        cutoff = station.photon_cutoff
        assert cutoff is not None
        # The model's own domain checks refuse a value that is not an exact
        # rational (``OpticalModelError``); the casts only name the type.
        qber = cast(Fraction, bound["qber"])
        declared = cast(Fraction, bound["transmittance"])

        def honest(declaration: CandidateDeclaration) -> Mapping[str, Fraction]:
            return honest_distribution(
                declaration,
                qber=qber,
                transmittance=declared * station.factored_loss,
                cutoff=cutoff,
            )

        def raw(
            declaration: CandidateDeclaration,
        ) -> Mapping[tuple[str, str], Fraction]:
            return raw_joint_distribution(
                declaration,
                qber=qber,
                transmittance=declared * station.factored_loss,
                cutoff=cutoff,
            )

        return factored_loss_applied(honest), raw_factored_loss_applied(raw)


#: The one instance of this model the registry holds.
MODEL = SinglePhotonLossDepolarizing()
