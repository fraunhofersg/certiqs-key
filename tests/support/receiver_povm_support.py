"""Shared helpers for the ``receiver-povm`` golden replays.

NO TESTS LIVE HERE, and this is not frozen evidence: ``tests/oracles/`` is the
frozen tree (``PRINCIPLES.md`` section 2.3) and this file is not in it. It exists
so that the exact-to-machine conversion of the frozen registry values, and the
declared-tolerance comparison the contract requires, are written once instead of
once per replay file.

THE FROZEN VALUES ARE EXACT AND THE MODULE'S EVALUATION IS NOT
=============================================================
``tests/oracles/registry_receiver_povm.py`` freezes every value exactly in
``Q[sqrt2] + i Q[sqrt2]``, because Theorem ``thm:exact-and-evaluated`` (i) makes
every asserted statement of the contract an identity or inequality between
exactly specified quantities. The module under test EVALUATES those statements
in IEEE-754 double precision, because Definition ``def:evaluation-model`` says the
contract does. So a replay compares a machine number against an exact one, and the
comparison needs a threshold.

**THE THRESHOLD IS THE DECLARED ONE.** ``TOLERANCE_FIXTURE_0_3_0`` is the
registry's documented stand-in for the contract's ``numerical_tolerances`` input
at registry 0.3.0 -- declared, never defaulted (``interface.yaml`` ``inputs``),
each member inside the declared domain ``[0, 1)`` -- and :data:`TOLERANCE` is
that fixture as the module's own ``NumericalTolerances``. Every replay compares
against a member of it, so no test invents a tolerance the contract does not
carry.

EIGHT MEMBERS, OF WHICH TWO ARE CONDITIONALLY REQUIRED. ``eps_6`` and
``eps_eig`` are "required exactly where an ``exact_window`` depth is declared,
refused when missing there, and neither required nor an error when no depth is
declared anywhere" (``inputs.numerical_tolerances``). :data:`TOLERANCE` carries
both, because the replays that exercise the exact window need them and a
supplied-and-unneeded tolerance is unused rather than an error -- the same rule
``eps_1`` and ``eps_3`` follow on route (i).
:data:`TOLERANCE_WITHOUT_EXACT_WINDOW` is the same tuple with the two ABSENT,
which is where every declaration without an exact window sits and which the
opt-out replays use.

**AND THE OBSERVED AGREEMENT IS FAR TIGHTER THAN THAT.**
:data:`MACHINE_AGREEMENT` is a TEST-SIDE strengthening: it is not a contract
tolerance, it enters no emitted quantity, and it exists only so that a defect of
size ``1e-4`` -- comfortably inside the declared ``eps_i = 1e-3`` -- cannot pass
unnoticed. :func:`assert_matches` asserts both.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction

import numpy as np
from registry_receiver_povm import Q2, TOLERANCE_FIXTURE_0_3_0, Alg, Mat

from certiqs_key.receiver import (
    Assurance,
    Beamsplitter,
    BoundData,
    CoarseGraining,
    DetectorPort,
    Element,
    ElementGraph,
    GramFamily,
    InputModes,
    Mode,
    ModeRouting,
    ModeSpace,
    NoClickFamily,
    NumericalTolerances,
    Polarization,
    PortMap,
    ProbeDeclaration,
    ProbeSetting,
    ReceiverRequest,
    Retarder,
    Scalar,
    raw_alphabet,
    unconditioned_family,
)
from certiqs_key.receiver.numerics import identity

#: The registry's 0.3.0 tolerance fixture, as the declared
#: `numerical_tolerances` input. EIGHT MEMBERS: the registry-0.2.0 six
#: unchanged plus `eps_6` and `eps_eig`, which the exact window adds and which
#: are conditionally required.
TOLERANCE = NumericalTolerances(
    eps_1=float(TOLERANCE_FIXTURE_0_3_0["eps_1"]),
    eps_2=float(TOLERANCE_FIXTURE_0_3_0["eps_2"]),
    eps_3=float(TOLERANCE_FIXTURE_0_3_0["eps_3"]),
    eps_4=float(TOLERANCE_FIXTURE_0_3_0["eps_4"]),
    eps_5=float(TOLERANCE_FIXTURE_0_3_0["eps_5"]),
    eps_gap=float(TOLERANCE_FIXTURE_0_3_0["eps_gap"]),
    eps_6=float(TOLERANCE_FIXTURE_0_3_0["eps_6"]),
    eps_eig=float(TOLERANCE_FIXTURE_0_3_0["eps_eig"]),
)

#: The same tuple with the two conditionally required members ABSENT -- None,
#: not zero. This is where every declaration that requests no exact window
#: sits, and the distinction is load-bearing: `eps_eig = 0` is a legal
#: declaration inside the domain `[0, 1)` and means something quite different
#: from "not declared".
TOLERANCE_WITHOUT_EXACT_WINDOW = NumericalTolerances(
    eps_1=TOLERANCE.eps_1,
    eps_2=TOLERANCE.eps_2,
    eps_3=TOLERANCE.eps_3,
    eps_4=TOLERANCE.eps_4,
    eps_5=TOLERANCE.eps_5,
    eps_gap=TOLERANCE.eps_gap,
    eps_6=None,
    eps_eig=None,
)

#: The declared tolerance mapping a request carrying NO exact-window depth
#: supplies: the six always-required members and neither conditional one.
DECLARED_TOLERANCES_WITHOUT_EXACT_WINDOW = {
    key: value
    for key, value in TOLERANCE_FIXTURE_0_3_0.items()
    if key not in ("eps_6", "eps_eig")
}

#: A TEST-SIDE strengthening, not a contract tolerance. See the module
#: docstring: the declared eps_i is 1e-3 and the observed agreement is at
#: double-precision level, so a replay that merely cleared the declared bound
#: would be a weak test.
MACHINE_AGREEMENT = 1e-9

_ROOT_TWO = math.sqrt(2.0)


def q2_value(value: Q2) -> float:
    """Return ``p + q sqrt2`` as a machine number."""
    return float(value[0]) + float(value[1]) * _ROOT_TWO


def alg_value(value: Alg) -> complex:
    """Return ``re + i im`` of ``Q[sqrt2] + i Q[sqrt2]`` as a machine number."""
    return complex(q2_value(value[0]), q2_value(value[1]))


def mat_value(matrix: Mat) -> np.ndarray:
    """Return a frozen exact matrix as a ``complex128`` array."""
    return np.asarray(
        [[alg_value(entry) for entry in row] for row in matrix], dtype=np.complex128
    )


def deviation(actual: object, expected: object) -> float:
    """Return the largest absolute difference between two arrays or scalars."""
    left = np.asarray(actual, dtype=np.complex128)
    right = np.asarray(expected, dtype=np.complex128)
    if left.shape != right.shape:
        raise AssertionError(f"shape {left.shape} against {right.shape}")
    if left.size == 0:
        return 0.0
    return float(np.max(np.abs(left - right)))


def assert_matches(
    actual: object, expected: object, tolerance_bound: float, where: str
) -> float:
    """Assert agreement, twice, and return the deviation.

    First against the DECLARED tolerance, which is the contract's own criterion
    and the only one an emitted verdict may rest on; then against
    :data:`MACHINE_AGREEMENT`, the test-side strengthening the module docstring
    explains. A replay that cleared the first and failed the second would be a
    finding about the implementation, not about the contract.
    """
    gap = deviation(actual, expected)
    assert gap <= tolerance_bound, (
        f"{where}: deviation {gap} exceeds declared {tolerance_bound}"
    )
    assert gap <= MACHINE_AGREEMENT, (
        f"{where}: deviation {gap} is inside the declared tolerance but above "
        f"the double-precision agreement {MACHINE_AGREEMENT} this band observes"
    )
    return gap


def sorted_spectrum(values: Sequence[Fraction]) -> list[float]:
    """Return a frozen exact spectrum as an ascending list of machine numbers."""
    return sorted(float(value) for value in values)


# ---------------------------------------------------------------------------
#  Two request builders, for the emission replays
#
#  Both are the registry's own receivers, presented as REQUESTS so that the
#  whole inputs-table -> outputs-table pass can be exercised end to end:
#
#  * `bb84_channel_only_request` is Example ex:bb84's channel-only receiver,
#    declared as an ELEMENT GRAPH (route iii) -- the beamsplitter, the
#    half-wave plate on the X arm and the routing of Example ex:bb84's own
#    chain -- whose compiled instrument must reproduce the frozen I-BB84
#    Gamma_Inp and Grams, and whose bound must reproduce Example ex:bb84bound;
#  * `probe_receiver_request` is I-PROBE, declared as an INSTRUMENT MATRIX
#    (route ii), with the two frozen probe settings, so that branch 1 through
#    predicate (X) and branch 2 with its window are both exercised in one
#    emission.
# ---------------------------------------------------------------------------


def _six_outcome_alphabet(ports: int) -> CoarseGraining:
    """Return Requirement req:declared-alphabet's coarse-graining at ``K`` ports."""
    letters = ("nc", *(f"sc_{index}" for index in range(ports)), "mc")
    assignment: dict[frozenset[int], str] = {}
    for pattern in raw_alphabet(ports):
        if not pattern:
            assignment[pattern] = "nc"
        elif len(pattern) == 1:
            assignment[pattern] = f"sc_{next(iter(pattern))}"
        else:
            assignment[pattern] = "mc"
    return CoarseGraining(ports, letters, assignment)


def bb84_channel_only_request(
    photon_cutoff: int = 2,
    requested: Assurance = Assurance.FIRST_ORDER,
    efficiencies: tuple[Scalar, ...] = (1, 1, 1, 1),
    dark_counts: tuple[Scalar, ...] = (0, 0, 0, 0),
    exact_window: dict[str, int] | None = None,
) -> ReceiverRequest:
    """Return Example ex:bb84's channel-only receiver as a route-(iii) request.

    Eight declared modes on four paths; the chain is Example ex:bb84's own --
    C1 at ``x = p_Z = 1/2`` on the ``(Chan, Led)`` path pair, the C3 preset
    ``HWP(pi/8)`` on the ``X`` arm, and the C9 routing to the four ports. The
    probe path carries VACUUM and is not declared as a source mode, which is
    the "channel-only receiver" of that example's last paragraph: ``Inp_S`` is
    empty, so ``T = {off}`` by Definition ``def:probe`` and predicate (X) holds
    by its FIRST clause.

    ``exact_window`` DEFAULTS TO NO DEPTH ANYWHERE, which is the opt-out and is
    where every declaration without an exact window sits; a caller that wants
    the exact window declares one, and the two conditional tolerances are then
    supplied with it. Nothing here invents a depth: ``interface.yaml``
    ``inputs.exact_window.no_default_note`` says "a platform default would be
    an undeclared number" (design.md, decision 12).
    """
    depths = dict(exact_window or {})
    modes = [
        Mode(path, polarization, 0)
        for path in ("Chan", "Led", "X", "Z")
        for polarization in (Polarization.H, Polarization.V)
    ]
    space = ModeSpace.declare(modes)
    index = {mode.label: position for position, mode in enumerate(space.modes)}
    permutation = list(range(len(space)))
    for first, second in (
        ("Chan_H", "Z_H"),
        ("Chan_V", "Z_V"),
        ("Led_H", "X_H"),
        ("Led_V", "X_V"),
    ):
        permutation[index[first]] = index[second]
        permutation[index[second]] = index[first]
    graph = ElementGraph(
        (
            Element(
                "bs",
                Beamsplitter(Fraction(1, 2), 0, 0, 0),
                (index["Chan_H"], index["Chan_V"], index["Led_H"], index["Led_V"]),
            ),
            Element(
                "hwp",
                Retarder.half_wave(math.pi / 8, 0),
                (index["Led_H"], index["Led_V"]),
            ),
            Element("route", ModeRouting(tuple(permutation)), tuple(range(len(space)))),
        ),
        (("bs", "hwp"), ("hwp", "route")),
    )
    labels = ("H", "V", "+", "-")
    return ReceiverRequest(
        mode_space=space,
        input_modes=InputModes(channel=(index["Chan_H"], index["Chan_V"]), source=()),
        port_map=PortMap(
            (
                ("H", (index["Z_H"],)),
                ("V", (index["Z_V"],)),
                ("+", (index["X_H"],)),
                ("-", (index["X_V"],)),
            )
        ),
        detector_layer=tuple(
            DetectorPort(label, efficiency, dark)
            for label, efficiency, dark in zip(
                labels, efficiencies, dark_counts, strict=True
            )
        ),
        probe_declaration=ProbeDeclaration.probe_free(),
        photon_cutoff=photon_cutoff,
        numerical_tolerances=(
            dict(TOLERANCE_FIXTURE_0_3_0)
            if depths
            else dict(DECLARED_TOLERANCES_WITHOUT_EXACT_WINDOW)
        ),
        outcome_coarse_graining=_six_outcome_alphabet(4),
        requested_assurance=requested,
        element_graph=graph,
        exact_window=depths,
    )


def probe_receiver_request(
    photon_cutoff: int = 1,
    requested: Assurance = Assurance.ESTIMATE,
    window: int = 3,
    exact_window: dict[str, int] | None = None,
) -> ReceiverRequest:
    """Return the frozen ``I-PROBE`` receiver as a route-(ii) request.

    One channel mode and one declared source mode, the input basis ordered
    CHANNEL FIRST as the ``subsystem_order`` convention requires, with the two
    frozen probe settings: ``off`` at ``Gamma^(t) = 0`` -- predicate (X)'s
    SECOND clause, branch 1 -- and ``on`` at ``nbar = 1``, where (X) fails and
    branch 2 uses the declared window. The per-port dark-count probabilities
    are ``DARK-K2``'s.

    ``exact_window`` DEFAULTS TO NO DEPTH ANYWHERE. Where depths are supplied
    the two conditionally required tolerances are supplied with them, which is
    what Requirement ``req:exact-window-declaration`` requires of a declaration
    carrying a depth AT ANY SETTING.
    """
    depths = dict(exact_window or {})
    space = ModeSpace.declare(
        (Mode("C", Polarization.H, 0), Mode("L", Polarization.H, 0))
    )
    gamma = np.asarray([[0.5, 0.5], [0.5, -0.5]], dtype=np.complex128)
    return ReceiverRequest(
        mode_space=space,
        input_modes=InputModes(channel=(0,), source=(1,)),
        port_map=PortMap((("1", (0,)), ("2", (1,)))),
        detector_layer=(
            DetectorPort("1", 1, Fraction(1, 10)),
            DetectorPort("2", 1, Fraction(1, 5)),
        ),
        probe_declaration=ProbeDeclaration(
            (ProbeSetting("off", (0,)), ProbeSetting("on", (1,)))
        ),
        photon_cutoff=photon_cutoff,
        numerical_tolerances=(
            dict(TOLERANCE_FIXTURE_0_3_0)
            if depths
            else dict(DECLARED_TOLERANCES_WITHOUT_EXACT_WINDOW)
        ),
        outcome_coarse_graining=_six_outcome_alphabet(2),
        requested_assurance=requested,
        instrument_matrix=gamma,
        tail_window={"on": window},
        exact_window=depths,
    )


def probe_free_matrix_request(
    photon_cutoff: int = 1,
    requested: Assurance = Assurance.ESTIMATE,
) -> ReceiverRequest:
    """Return the ``I-PROBE`` optics, both inputs channel modes: route (ii), no probe.

    The probe-free twin of :func:`probe_receiver_request`: the same declared
    modes, instrument matrix, port map and detectors (``DARK-K2``'s dark-count
    probabilities), with both input modes declared as CHANNEL modes, so that
    ``Inp_S`` is empty, ``T = {off}`` by Definition ``def:probe`` and the
    receiver is the core's own (Cor. ``cor:unconditioned-family``). Its port
    Grams are the probe receiver's, on the same two-mode input space. The core
    tests of route (ii) -- and of route (i), its Grams supplied directly -- run
    on it, so that they run where the removable probe-conditioning submodule
    is absent (``tests/support/probe_presence.py``).
    """
    return replace(
        probe_receiver_request(photon_cutoff, requested),
        input_modes=InputModes(channel=(0, 1), source=()),
        probe_declaration=ProbeDeclaration.probe_free(),
        tail_window={},
    )


# ---------------------------------------------------------------------------
#  The no-click families the exact-window replays evaluate Eq. eq:exactbnd on
#
#  Definition ``def:exactbnd`` is stated "under the hypotheses of Theorem
#  thm:multiclick-bound" -- on the pair family ``{(c_J, B_J)}`` of Eq.
#  ``eq:prefactorform`` -- and it says in terms that NO NEW OBJECT IS
#  INTRODUCED: the block is the one Eq. ``eq:blockMS`` already builds, "evaluated
#  at an index above the cutoff instead of below it". So every builder below
#  produces a :class:`~certiqs_key.receiver.povm.NoClickFamily`, and the replays
#  call the module's own ``multiclick_block`` through ``exact_block_bound``.
# ---------------------------------------------------------------------------


def bb84_no_click_family(p_z: Fraction) -> NoClickFamily:
    """Return ``I-BB84``'s unconditioned no-click family at a declared ``p_Z``.

    The Grams of Eq. ``eq:bb84grams``: ``A_H = p_Z |H><H|``, ``A_V = p_Z |V><V|``,
    ``A_+ = p_X |+><+|``, ``A_- = p_X |-><-|`` with ``p_X = 1 - p_Z``, whose sum
    is ``id_2`` -- so ``c = 1 - lmax(A_Sigma) = 0``, which is the lossless
    probe-free case Lemma ``lem:windowtail`` (iii) names.

    ``Inp_C = {Chan_H, Chan_V}`` gives ``D = 2``, so the ``n``-photon block has
    dimension ``binom(n + 1, n) = n + 1`` and the exact window has something to
    find: this is the ONE frozen receiver whose channel space is more than one
    dimensional.
    """
    p_x = 1 - p_z
    ket_h = np.array([[1.0], [0.0]], dtype=np.complex128)
    ket_v = np.array([[0.0], [1.0]], dtype=np.complex128)
    ket_p = (ket_h + ket_v) / math.sqrt(2.0)
    ket_m = (ket_h - ket_v) / math.sqrt(2.0)
    grams = (
        float(p_z) * (ket_h @ ket_h.conj().T),
        float(p_z) * (ket_v @ ket_v.conj().T),
        float(p_x) * (ket_p @ ket_p.conj().T),
        float(p_x) * (ket_m @ ket_m.conj().T),
    )
    return unconditioned_family(GramFamily(("H", "V", "+", "-"), grams))


def beamsplitter_no_click_family() -> NoClickFamily:
    """Return ``I-BS``: two detectors, ONE channel input mode, no probe.

    ``K = 2``, ``gamma = beta_k = 1``, ``A_1 = A_2 = 1/2`` on a ONE-dimensional
    channel space. Every block is then a scalar --
    ``binom(1 + n - 1, n) = 1`` at every ``n`` -- so Eq. ``eq:mcbound`` holds
    WITH EQUALITY and the exact window buys exactly nothing. That is not an edge
    case: it is every receiver with a one-dimensional channel space, and it is
    why the depth is opt-in.
    """
    half = np.array([[0.5]], dtype=np.complex128)
    return unconditioned_family(GramFamily(("1", "2"), (half, half)))


def positivity_counterexample_family(dimension: int) -> NoClickFamily:
    """Return Remark ``rem:exactpositivity``'s instance -- NOT a receiver.

    ``K = 4``, ``gamma = beta_k = 1``, ``B = id`` and ``B_k = 0``. Every
    hypothesis of Theorem ``thm:multiclick-bound`` holds -- ``0 <= B_k <= B <= id``
    reads ``0 <= 0 <= id <= id`` -- while
    ``M_mc = id + 3 Fock(0) - 4 Fock(id)`` is ``-3 id`` on every block ``n >= 1``.

    WHAT THE INSTANCE EXCLUDES IS THE OPERATOR, NOT THE NUMBERS: the same data
    give ``c = 0`` and ``d_k = 1``, so ``beta(n) = -3`` too and Eq. ``eq:mcbound``
    holds with equality. It is built here directly from the pair family rather
    than from a Gram family, because no admissible Gram family produces it --
    which is the whole content of the remark.
    """
    ports = range(4)
    whole = frozenset(ports)
    prefactors = {whole: 1.0}
    grams = {whole: identity(dimension)}
    for port in ports:
        others = whole - {port}
        prefactors[others] = 1.0
        grams[others] = np.zeros((dimension, dimension), dtype=np.complex128)
    return NoClickFamily(
        port_count=4,
        dimension=dimension,
        prefactors=prefactors,
        effective_grams=grams,
    )


def bound_data_of(case: object) -> BoundData:
    """Return a frozen case's ``(gamma, {beta_k}, c, {d_k})`` as the module's own.

    Works for any frozen row carrying ``port_count``, ``gamma``, ``betas``,
    ``c`` and ``ds`` -- the shape ``BoundDataCase`` and ``ExactWindowCase``
    share.
    """
    return BoundData(
        port_count=case.port_count,  # type: ignore[attr-defined]
        gamma=float(case.gamma),  # type: ignore[attr-defined]
        betas=tuple(float(value) for value in case.betas),  # type: ignore[attr-defined]
        c=float(case.c),  # type: ignore[attr-defined]
        ds=tuple(float(value) for value in case.ds),  # type: ignore[attr-defined]
    )


def tolerances_at(eps_eig: Fraction) -> NumericalTolerances:
    """Return the registry-0.3.0 fixture with a case's own declared ``eps_eig``.

    Every other member is the fixture's. ``eps_eig`` varies per frozen case
    because it is the one declared number Eq. ``eq:elldef`` SUBTRACTS, and the
    frozen family ``EX-BB84-N1-M2-EIG-*`` sweeps it across the declared domain
    to exercise Eq. ``eq:bb84exactemit``'s outer maximum on both sides of
    ``1/2``.
    """
    return NumericalTolerances(
        eps_1=TOLERANCE.eps_1,
        eps_2=TOLERANCE.eps_2,
        eps_3=TOLERANCE.eps_3,
        eps_4=TOLERANCE.eps_4,
        eps_5=TOLERANCE.eps_5,
        eps_gap=TOLERANCE.eps_gap,
        eps_6=TOLERANCE.eps_6,
        eps_eig=float(eps_eig),
    )
