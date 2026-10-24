"""The general format's three solver choices: oracle, step rule, warm start.

What is tested and why each would fail on the defect it names:

* the DEFAULTS are the plain loop, bit for bit: pinned against the numbers the
  loop produced at a development commit (a regression pin, not an
  oracle; it moves only if the default path's arithmetic moves);
* the SPECTRAL backend agrees with QICS on random spectraplexes and returns a
  feasible point, refuses what is not a spectraplex, and is assigned exactly
  where the feasible set is one;
* under the PAIRWISE rule the bracket consumes the EXACT oracle return and never
  the shrunk atom (the unsafe side of ``eq:lmo``); its iterates stay coupled
  and positive definite; and on the toys below it certifies at least what the
  vanilla rule does at the same small budget;
* a WARM START is refused, with its named reason, on each mismatch;
* the new settings round-trip through the configuration and the record, and a
  configuration or record from before them still reads unchanged.
"""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import (
    BB84_ELEMENTS,
    decoy_like_general,
    maps_of,
    qubit_bb84_general,
    random_choi_point,
    two_factor_general,
)
from tests.support.platform_pins import (
    DARWIN_ARM64_ACCELERATE,
    WINDOWS_AMD64_OPENBLAS,
    PinTable,
    assert_pinned,
)

import certiqs_key.solvers.frank_wolfe.joint_driver as joint_driver
from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.meat_core.declaration.general import (
    GeneralConstraintEntry,
    GeneralDeclaration,
    GeneralRhsTag,
)
from certiqs_key.meat_core.errors import SupportError
from certiqs_key.meat_core.objective.joint import JointMaps, JointSector
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix
from certiqs_key.runs.config import (
    AdvancedSolverSettings,
    RunConfig,
    RunConfigError,
    SolverSettings,
    WarmStartSeed,
)
from certiqs_key.runs.surface import solver_request
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    coupling_residuals,
    joint_initial_point,
    run_joint_frank_wolfe,
)
from certiqs_key.solvers.frank_wolfe.joint_options import (
    PAIRWISE_FOLD_BELOW,
    PAIRWISE_SHRINK,
    WARM_START_MIX,
    JointFrankWolfeOptions,
    WarmStart,
    WarmStartRefused,
    blocks_digest,
    constraint_rows_digest,
    iterate_layout,
    oracle_assignment,
    warm_start_point,
)
from certiqs_key.solvers.frank_wolfe.joint_pairwise import ActiveSet
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle
from certiqs_key.solvers.oracles.protocol import (
    AffineRow,
    Coupling,
    OracleFailure,
    SectorChoiProblem,
)
from certiqs_key.solvers.oracles.spectral import (
    SpectralSectorChoiOracle,
    is_spectraplex,
)

REPOSITORY = Path(__file__).resolve().parents[2]
#: A run configuration written before the solver fields existed: the two-sided
#: sweep's phase-3, 10 dB, pair-resolved BBM92 point, copied unchanged from
#: that run's record, so that the test reads no run output.
PHASE3_CONFIG = REPOSITORY / "tests/data/two-sided-phase3-config/config.json"


def _untrusted_without_rows() -> GeneralDeclaration:
    return replace(two_factor_general(party_local=False), constraint_list=())


def _trusted_with_a_row(
    *, bound: float = 0.25, element: str = "z0"
) -> GeneralDeclaration:
    entry = GeneralConstraintEntry(
        scope="f0",
        operator_blocks={"q": BB84_ELEMENTS[element]},
        relation=ConstraintRelation.PRECEQ,
        bound=bound,
        rhs_tag=GeneralRhsTag.HOMOGENEOUS,
    )
    return replace(decoy_like_general(), constraint_list=(entry,))


def _toy(name: str) -> GeneralDeclaration:
    return {
        "decoy": decoy_like_general,
        "q3": lambda: qubit_bb84_general(messages=3),
        "tf_norows": _untrusted_without_rows,
    }[name]()


def _run_toy(
    name: str, options: FrankWolfeOptions
) -> tuple[JointMaps, joint_driver.JointFrankWolfeResult]:
    """Run a toy from a random coupled start, with a singleton acceptance set.

    From the interior start these symmetric toys are optimal at once; from a
    random point of the coupling set the loop has a path to take.
    """
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    maps = maps_of(_toy(name))
    start = random_choi_point(maps.parametrization, 1)
    values = list(maps.declaration.acceptance_values)
    acceptance = SingletonAcceptanceOracle({values[0]: 0.875, values[1]: 0.125})
    return maps, run_joint_frank_wolfe(
        maps, QicsSectorChoiOracle(), acceptance, start, 1.5, options
    )


# ---------------------------------------------------------------------------
# Defaults: the plain loop, bit for bit.
# ---------------------------------------------------------------------------

#: The loop at a development commit, 12 iterations of each toy from
#: ``random_choi_point(p, 1)`` at alpha 1.5 with the singleton (0.875, 0.125).
#: A REGRESSION PIN of the default path's arithmetic, captured by running that
#: commit; the objective, bracket and gap as hex, and the sha256 of the final
#: iterate's bytes in sorted joint-sector order.
#: KEYED BY PLATFORM (tests/support/platform_pins.py): the values are the
#: Windows machine's, plus the macOS arm64 value where one is recorded. A field
#: a platform has not recorded fails with the values to record.
#: THE BRACKET'S FEASIBLE SIDE is the bound verified from the oracle's dual
#: (frank-wolfe/req:verified-feasible-side), not the pairing with the return;
#: the objective, the gap and the iterate do not depend on it.
PINNED_DEFAULTS: PinTable = {
    WINDOWS_AMD64_OPENBLAS: {
        "decoy": {
            "objective": "0x1.a9bf73e987a28p+0",
            "bracket": "0x1.a8f411020bc04p+0",
            "gap": "0x1.980e889240d00p-9",
            "choi_sha256": (
                "7c462b66c286578bf9c5423717cfd9eaa7216734cc2228c0d4fc8ad2fc52af01"
            ),
        },
        "q3": {
            "objective": "0x1.5e8eed0fa77f0p+0",
            "bracket": "0x1.5b7e3a39dd898p+0",
            "gap": "0x1.89ac409a56c30p-7",
            "choi_sha256": (
                "972cc066363f627f2b480f322532217c4e0678fd0aab1c1b8cfcefa1b132ce83"
            ),
        },
        "tf_norows": {
            "objective": "0x1.5e8ae1f0e24b0p+0",
            "bracket": "0x1.5e7d1c55d73c2p+0",
            "gap": "0x1.b8bbe17598000p-13",
            "choi_sha256": (
                "05f9ae26459c026a549a13696b2e2be406b01e35a4b503a846adfce2ffbcb956"
            ),
        },
    },
    DARWIN_ARM64_ACCELERATE: {
        "tf_norows": {"objective": "0x1.5e8ae1f0de158p+0"},
    },
}

#: The three toys the pins name.
PINNED_TOYS: tuple[str, ...] = ("decoy", "q3", "tf_norows")


def _choi_digest(choi: Any) -> str:
    from hashlib import sha256

    digest = sha256()
    for pair in sorted(choi):
        digest.update(
            np.ascontiguousarray(np.asarray(choi[pair], np.complex128)).tobytes()
        )
    return digest.hexdigest()


@pytest.mark.pins
@pytest.mark.requires_qics
@pytest.mark.parametrize("name", PINNED_TOYS)
@pytest.mark.parametrize(
    "options",
    [FrankWolfeOptions(max_iterations=12), JointFrankWolfeOptions(max_iterations=12)],
    ids=["plain-options", "joint-options-at-defaults"],
)
def test_the_defaults_reproduce_the_pinned_plain_loop_bit_for_bit(
    name: str, options: FrankWolfeOptions
) -> None:
    _maps, result = _run_toy(name, options)
    assert result.h_lb is not None
    assert_pinned(
        PINNED_DEFAULTS,
        name,
        {
            "objective": result.objective.hex(),
            "bracket": result.h_lb.hex(),
            "gap": result.gap.hex(),
            "choi_sha256": _choi_digest(result.choi),
        },
        where="tests/unit/test_joint_solver_options.py, PINNED_DEFAULTS",
    )
    assert result.solver_report["oracle"] == "qics"
    assert result.solver_report["step_rule"] == "vanilla"
    assert result.solver_report["pairwise"] is None


# ---------------------------------------------------------------------------
# The spectral backend.
# ---------------------------------------------------------------------------


def _random_hermitian(rng: np.random.Generator, dim: int) -> Matrix:
    sample = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    return np.asarray((sample + sample.conj().T) / 2.0, dtype=np.complex128)


@pytest.mark.requires_qics
@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("coupling", [Coupling.UNIT_TRACE, Coupling.INPUT_IDENTITY])
def test_the_spectral_oracle_agrees_with_qics_on_random_spectraplexes(
    seed: int, coupling: Coupling
) -> None:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    rng = np.random.default_rng(seed)
    dims = {f"b{k}": int(dim) for k, dim in enumerate(rng.integers(1, 5, size=4))}
    problem = SectorChoiProblem(
        input_dim=1,
        block_dims=dims,
        cost={label: _random_hermitian(rng, dim) for label, dim in dims.items()},
        coupling=coupling,
    )
    assert is_spectraplex(problem)
    spectral = SpectralSectorChoiOracle().minimize(problem)
    conic = QicsSectorChoiOracle().minimize(problem)
    assert spectral.objective == pytest.approx(conic.objective, abs=1e-9)
    assert spectral.diagnostics["sol_status"] == "optimal"
    assert spectral.diagnostics["eigen_residual"] < 1e-12
    # THE RETURN IS FEASIBLE: positive semidefinite blocks of total trace one.
    total = 0.0
    for label, block in spectral.blocks.items():
        assert np.linalg.eigvalsh(as_matrix(block))[0] >= -1e-15
        total += float(np.real(np.trace(as_matrix(block))))
        assert block.shape == (dims[label], dims[label])
    assert total == pytest.approx(1.0, abs=1e-14)
    # AND IT ATTAINS THE CLOSED FORM: the smallest eigenvalue over the blocks.
    smallest = min(
        float(np.linalg.eigvalsh(as_matrix(cost))[0]) for cost in problem.cost.values()
    )
    assert spectral.objective == pytest.approx(smallest, abs=1e-12)


def test_the_spectral_oracle_refuses_what_is_not_a_spectraplex() -> None:
    cost = {"b": np.eye(2, dtype=np.complex128)}
    operator = SectorChoiProblem(
        input_dim=2,
        block_dims={"b": 1},
        cost=cost,
        coupling=Coupling.INPUT_IDENTITY,
    )
    with_row = SectorChoiProblem(
        input_dim=1,
        block_dims={"b": 2},
        cost=cost,
        coupling=Coupling.UNIT_TRACE,
        rows=(
            AffineRow(
                blocks={"b": np.eye(2, dtype=np.complex128)},
                relation=ConstraintRelation.PRECEQ,
                rhs=0.5,
            ),
        ),
    )
    for problem in (operator, with_row):
        assert not is_spectraplex(problem)
        with pytest.raises(OracleFailure, match="not a spectraplex"):
            SpectralSectorChoiOracle().minimize(problem)


@pytest.mark.parametrize(
    ("declaration", "expected"),
    [
        (_untrusted_without_rows, {"*": "spectral"}),
        (lambda: two_factor_general(party_local=False), {"*": "qics"}),
        (
            decoy_like_general,
            # vacuum and flag have d_A = 1; rank1 has a RANK-ONE marginal, so
            # its support frame has input dimension one; one has dimension 2.
            {
                "vacuum": "spectral",
                "flag": "spectral",
                "rank1": "spectral",
                "one": "qics",
            },
        ),
        (lambda: qubit_bb84_general(messages=3), {"t0": "qics"}),
        (
            _trusted_with_a_row,
            {"vacuum": "qics", "flag": "qics", "rank1": "qics", "one": "qics"},
        ),
    ],
    ids=[
        "untrusted",
        "untrusted-rows",
        "trusted-dim1-and-dim2",
        "trusted-dim2",
        "trusted-rows",
    ],
)
def test_the_backend_is_assigned_exactly_where_the_set_is_a_spectraplex(
    declaration: Any, expected: dict[str, str]
) -> None:
    parametrization = maps_of(declaration()).parametrization
    assert oracle_assignment(parametrization, "spectral") == expected
    assert set(oracle_assignment(parametrization, "qics").values()) == {"qics"}


@pytest.mark.requires_qics
def test_a_mixed_run_records_the_backend_of_every_call() -> None:
    _maps, result = _run_toy(
        "decoy", JointFrankWolfeOptions(max_iterations=4, oracle="spectral")
    )
    report = result.solver_report
    assert report["oracle_assignment"]["one"] == "qics"
    by_group: dict[str, set[str]] = {}
    for entry in result.oracle_diagnostics:
        by_group.setdefault(entry["group"], set()).add(entry["backend"])
    assert by_group == {
        group: {backend} for group, backend in report["oracle_assignment"].items()
    }
    assert report["oracle_calls"] == {
        "qics": result.iterations,
        "spectral": 3 * result.iterations,
    }
    assert report["spectral_evidence"]["max_eigen_residual"] < 1e-12
    assert result.h_lb is not None


# ---------------------------------------------------------------------------
# The pairwise rule.
# ---------------------------------------------------------------------------


@pytest.mark.requires_qics
def test_under_pairwise_the_bracket_reads_no_atom_and_the_pairing_the_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Recompute every gate's bracket and its diagnostic pairing.

    The bracket's feasible side is the verified bound
    (``req:verified-feasible-side``), so the bracket is
    ``objective + b^F - <G, J>``, to the bit; the diagnostic
    ``oracle_pairing`` is the pairing with the EXACT return, and not with the
    shrunk atom the step moved along. The bracket is not the pairing with the
    exact return.
    """
    seen: list[dict[str, Any]] = []
    gradient = joint_driver.joint_gradient
    vertex_of = joint_driver._oracle_vertex

    def recording_gradient(maps: Any, q: Any, point: Any, *args: Any, **kw: Any) -> Any:
        value = gradient(maps, q, point, *args, **kw)
        seen.append({"q": dict(q), "point": dict(point), "gradient": value})
        return value

    def recording_vertex(*args: Any, **kw: Any) -> Any:
        vertex, optimal = vertex_of(*args, **kw)
        seen[-1]["vertex"] = {pair: block.copy() for pair, block in vertex.items()}
        return vertex, optimal

    monkeypatch.setattr(joint_driver, "joint_gradient", recording_gradient)
    monkeypatch.setattr(joint_driver, "_oracle_vertex", recording_vertex)
    maps, result = _run_toy(
        "decoy",
        JointFrankWolfeOptions(
            max_iterations=8, oracle="spectral", step_rule="pairwise"
        ),
    )
    anchor = random_choi_point(maps.parametrization, 1)
    assert len(result.gates) == len(seen) == 8
    for gate, entry in zip(result.gates, seen, strict=True):
        slope = entry["gradient"]

        def pairing(
            target: dict[JointSector, Matrix], slope: Any = slope
        ) -> float:
            total = 0.0
            for pair, block in slope.blocks.items():
                total += float(np.real(np.trace(block @ as_matrix(target[pair]))))
            return total

        # The singleton acceptance set: v = q, so the q pairing is zero. The
        # gate's own order of operations: b^F, less each block's pairing.
        assert gate.feasible_side_bound is not None
        direction = gate.feasible_side_bound
        for pair, block in slope.blocks.items():
            direction -= float(
                np.real(np.trace(block @ as_matrix(entry["point"][pair])))
            )
        assert gate.linearization == gate.objective + direction
        assert gate.oracle_pairing == pairing(entry["vertex"])
        shrunk = {
            pair: (1.0 - PAIRWISE_SHRINK) * block + PAIRWISE_SHRINK * anchor[pair]
            for pair, block in entry["vertex"].items()
        }
        assert gate.oracle_pairing != pairing(shrunk)


#: The margin of the pairwise-against-vanilla measurement below.
PAIRWISE_MEASUREMENT_MARGIN = 1e-7


@pytest.mark.requires_qics
@pytest.mark.parametrize("name", ["decoy", "q3", "tf_norows"])
def test_pairwise_certifies_at_least_vanilla_at_equal_small_budgets(name: str) -> None:
    """On these toys, with the same oracle; this is a measurement, not a theorem.

    The bracket is a maximum over noisy per-iterate linearizations and no rule
    guarantees it iteration by iteration. What the rule does guarantee is that
    each step searches at least as low as the vanilla step from the same
    iterate; the certified number following is what these toys show.
    """
    budget = 30
    _maps, vanilla = _run_toy(name, JointFrankWolfeOptions(max_iterations=budget))
    maps, pairwise = _run_toy(
        name, JointFrankWolfeOptions(max_iterations=budget, step_rule="pairwise")
    )
    assert vanilla.h_lb is not None and pairwise.h_lb is not None
    # A STATED MARGIN, because the comparison is a measurement and not a
    # theorem: on macOS arm64 the tf_norows pair fell 1.2e-8 the other way
    # where on the recording machine the order was comparably close. 1e-7 is that
    # shortfall with a margin of eight; a pairwise bracket below vanilla's by
    # more than that would still fail.
    assert pairwise.h_lb >= vanilla.h_lb - PAIRWISE_MEASUREMENT_MARGIN
    # The iterate stays in the coupling set and positive definite at every gate.
    # The residual is the conic oracle's own feasibility (its returns are
    # atoms), far inside the declared window, and no larger than vanilla's
    # order of magnitude.
    residual = max(coupling_residuals(maps.parametrization, pairwise.choi).values())
    assert residual < 1e-9
    assert residual < 100 * max(
        1e-14, *coupling_residuals(maps.parametrization, vanilla.choi).values()
    )
    assert all(gate.withdrawal is None for gate in pairwise.gates)
    assert min(gate.min_block_eigenvalue for gate in pairwise.gates) > 0.0
    assert (
        min(
            float(np.linalg.eigvalsh(as_matrix(block))[0])
            for block in pairwise.choi.values()
        )
        > 0.0
    )
    report = pairwise.solver_report["pairwise"]
    assert report["shrink"] == PAIRWISE_SHRINK
    assert report["fold_below"] == PAIRWISE_FOLD_BELOW
    # The plain step was taken, and counted, on some iterations.
    assert 0 < report["fallbacks"] < budget
    assert report["active_atoms"] >= 1


def test_the_active_set_folds_exactly_and_drops_only_zero_weight() -> None:
    rng = np.random.default_rng(4)
    atoms = rng.normal(size=(5, 6)) + 1j * rng.normal(size=(5, 6))
    frequencies = np.asarray([[0.5, 0.25, 0.25]] * 5, dtype=np.float64)
    frequencies[:, 0] = [0.5, 0.25, 0.5, 0.125, 0.5]
    weights = np.asarray([0.6, 0.3, 1e-13, 0.1 - 2e-13, 1e-13])
    active = ActiveSet(atoms, frequencies, weights)
    before_blocks, before_q = active.point()
    tidied = active.tidied()
    after_blocks, after_q = tidied.point()
    # Two tiny atoms folded into the heaviest: fewer atoms, same point.
    assert tidied.size == 3
    assert float(np.sum(tidied.weights)) == pytest.approx(
        float(np.sum(weights)), abs=1e-16
    )
    assert np.max(np.abs(after_blocks - before_blocks)) < 1e-15
    assert np.max(np.abs(after_q - before_q)) < 1e-15
    # A coordinate every atom agrees on is carried exactly, never re-formed.
    assert after_q[1] == 0.25 and after_q[2] == 0.25
    # A drop step: the away atom's weight reaches exactly zero and it leaves.
    # tidied holds weights (0.1, 0.3, 0.6); moving all 0.3 off the second atom
    # removes it and adds the new atom with that weight.
    stepped = tidied.pairwise(1, atoms[0], frequencies[0], float(tidied.weights[1]))
    assert stepped.size == 3
    assert np.all(stepped.weights > 0.0)
    assert sorted(stepped.weights.tolist()) == sorted(tidied.weights.tolist())
    assert not any(np.array_equal(row, tidied.blocks[1]) for row in stepped.blocks)


# ---------------------------------------------------------------------------
# Warm starts.
# ---------------------------------------------------------------------------


def _seed(declaration: GeneralDeclaration, **changes: Any) -> WarmStart:
    parametrization = maps_of(declaration).parametrization
    blocks = dict(random_choi_point(parametrization, 2))
    fields: dict[str, Any] = {
        "blocks": blocks,
        "source_mode": "trusted" if declaration.is_trusted_source else "untrusted",
        "constraint_count": len(declaration.constraint_list),
        "file_sha256": "0" * 64,
    }
    fields.update(changes)
    return WarmStart(**fields)


def test_a_warm_start_mixes_the_seed_with_the_interior_start() -> None:
    declaration = decoy_like_general()
    parametrization = maps_of(declaration).parametrization
    seed = _seed(declaration)
    interior = joint_initial_point(parametrization)
    start = warm_start_point(parametrization, seed, interior)
    for pair, block in start.items():
        expected = (1.0 - WARM_START_MIX) * seed.blocks[
            pair
        ] + WARM_START_MIX * interior[pair]
        assert np.array_equal(block, expected)
    assert max(coupling_residuals(parametrization, start).values()) < 1e-12


def test_a_warm_start_is_refused_on_each_mismatch() -> None:
    trusted = decoy_like_general()
    parametrization = maps_of(trusted).parametrization
    interior = joint_initial_point(parametrization)
    good = _seed(trusted)
    pair = next(iter(good.blocks))
    cases = {
        "warm_start_source_mode_mismatch": _seed(trusted, source_mode="untrusted"),
        # A seed that declared rows, with no digest to show which: refused on
        # a point without rows (and on one with rows, below).
        "warm_start_constraint_rows_mismatch": _seed(trusted, constraint_count=1),
        "warm_start_layout_mismatch": _seed(
            trusted, blocks={p: b for p, b in good.blocks.items() if p != pair}
        ),
        "warm_start_block_dims_mismatch": _seed(
            trusted,
            blocks={
                **good.blocks,
                pair: np.eye(
                    as_matrix(good.blocks[pair]).shape[0] + 1, dtype=np.complex128
                ),
            },
        ),
    }
    for reason, seed in cases.items():
        with pytest.raises(WarmStartRefused) as refusal:
            warm_start_point(parametrization, seed, interior)
        assert refusal.value.reason == reason
    # A declaration WITH rows refuses a seed that had none, and a seed whose
    # rows are other rows (rows are compared by digest).
    with_rows = maps_of(_trusted_with_a_row()).parametrization
    other_rows = constraint_rows_digest(_trusted_with_a_row(bound=0.375))
    assert other_rows is not None
    for seed in (good, _seed(trusted, constraint_count=1, rows_sha256=other_rows)):
        with pytest.raises(WarmStartRefused) as refusal:
            warm_start_point(with_rows, seed, joint_initial_point(with_rows))
        assert refusal.value.reason == "warm_start_constraint_rows_mismatch"


def test_the_rows_digest_names_the_data_that_define_the_rows() -> None:
    """``constraint_rows_digest``: none without rows, and every datum counts.

    The digest decides whether a seed with rows lives in a point's feasible
    set, so each datum that shapes the rows must move it: the bound, the
    operator, and in trusted-source mode the marginal (which builds a
    homogeneous right-hand side and the frame the rows are conjugated by).
    """
    assert constraint_rows_digest(decoy_like_general()) is None
    base = constraint_rows_digest(_trusted_with_a_row())
    assert base is not None and len(base) == 64
    assert constraint_rows_digest(_trusted_with_a_row()) == base
    assert constraint_rows_digest(_trusted_with_a_row(bound=0.375)) != base
    assert constraint_rows_digest(_trusted_with_a_row(element="z1")) != base
    declaration = _trusted_with_a_row()
    assert declaration.alice_marginal is not None
    moved = replace(
        declaration,
        alice_marginal={
            label: np.asarray(block) * 1.0
            + (1e-3 if label == next(iter(declaration.alice_marginal)) else 0.0)
            * np.eye(np.asarray(block).shape[0])
            for label, block in declaration.alice_marginal.items()
        },
    )
    assert constraint_rows_digest(moved) != base


def test_a_seed_with_the_same_rows_is_admitted_and_mixed_toward_the_cold_start() -> (
    None
):
    """Same rows, same feasible set: the seed is admitted, mixed toward J_0.

    J_0 is the cold start of a point with rows -- the oracle's zero-cost
    vertex, which satisfies the rows as the interior start need not -- and the
    driver passes it; the mix is exactly ``(1 - eps) J_prev + eps J_0``. The row
    here is ``F_z0 <= 1 tau_A``, which every coupled point satisfies, so the
    random seed is inside it and the test is about the mix alone.
    """
    declaration = _trusted_with_a_row(bound=1.0)
    parametrization = maps_of(declaration).parametrization
    digest = constraint_rows_digest(declaration)
    seed = _seed(declaration, rows_sha256=digest)
    assert seed.constraint_count == 1
    cold = joint_initial_point(parametrization)
    start = warm_start_point(parametrization, seed, cold)
    for pair, block in start.items():
        expected = (1.0 - WARM_START_MIX) * seed.blocks[pair] + WARM_START_MIX * cold[
            pair
        ]
        assert np.array_equal(block, expected)
    assert seed.as_payload()["rows_sha256"] == digest
    assert seed.as_payload()["constraint_count"] == 1


@pytest.mark.requires_qics
def test_a_seed_with_rows_chains_to_the_next_point_and_the_bracket_stands(
    tmp_path: Path,
) -> None:
    """A licensed-style chain: a seed with rows warm-starts the next point.

    Two points with the SAME rows and different statistics (the analogue of two
    loss points of a licensed route: the rows come from the receiver, the
    statistics from the channel). The first runs cold; its final iterate,
    written and read back through the seed file, starts the second, whose
    certificate is then valid in full: a first-order bound, every gate that
    contributes carrying no withdrawal, and the seed's rows digest on the
    record. A seed from a point with OTHER rows is refused by name.
    """
    from certiqs_key.runs.iterate_file import (
        ITERATE_FILE_NAME,
        load_warm_start,
        seed_of,
        write_final_iterate,
    )
    from certiqs_key.solvers.frank_wolfe.general_keyrate import solve_general
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    oracle = QicsSectorChoiOracle()
    first = replace(
        _trusted_with_a_row(),
        acceptance_set=replace(
            _trusted_with_a_row().acceptance_set, frequencies=(0.875, 0.125)
        ),
    )
    second = replace(
        first,
        acceptance_set=replace(first.acceptance_set, frequencies=(0.8125, 0.1875)),
    )
    cold = solve_general(
        first, oracle, options=JointFrankWolfeOptions(max_iterations=6)
    )
    assert cold.final_iterate_rows_sha256 == constraint_rows_digest(first)
    write_final_iterate(tmp_path / ITERATE_FILE_NAME, cold, config_digest="c" * 64)
    seed = load_warm_start(seed_of(tmp_path))
    assert seed.rows_sha256 == constraint_rows_digest(second)

    for step_rule in ("vanilla", "pairwise"):
        warm = solve_general(
            second,
            oracle,
            options=JointFrankWolfeOptions(
                max_iterations=6, step_rule=step_rule, warm_start=seed
            ),
        )
        assert warm.h_lb is not None, step_rule
        gates = warm.certificate["per_iterate"]
        assert any(gate["withdrawal"] is None for gate in gates), step_rule
        report = warm.certificate["joint_solver"]
        assert report["warm_start"]["rows_sha256"] == seed.rows_sha256
        if step_rule == "pairwise":
            # The anchor is the zero-cost start, checked positive definite.
            assert report["pairwise"]["anchor_min_eigenvalue"] > 0.0

    other = replace(
        _trusted_with_a_row(bound=0.375), acceptance_set=second.acceptance_set
    )
    with pytest.raises(WarmStartRefused) as refusal:
        solve_general(
            other,
            oracle,
            options=JointFrankWolfeOptions(max_iterations=2, warm_start=seed),
        )
    assert refusal.value.reason == "warm_start_constraint_rows_mismatch"


@pytest.mark.requires_qics
def test_a_warm_started_general_run_records_its_seed_and_round_trips_the_file(
    tmp_path: Path,
) -> None:
    from certiqs_key.runs.iterate_file import (
        ITERATE_FILE_NAME,
        WarmStartFileError,
        load_warm_start,
        seed_of,
        write_final_iterate,
    )
    from certiqs_key.solvers.frank_wolfe.general_keyrate import solve_general
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    declaration = replace(
        decoy_like_general(),
        acceptance_set=replace(
            decoy_like_general().acceptance_set, frequencies=(0.875, 0.125)
        ),
    )
    oracle = QicsSectorChoiOracle()
    cold = solve_general(
        declaration, oracle, options=JointFrankWolfeOptions(max_iterations=3)
    )
    assert cold.certificate["joint_solver"]["warm_start"] is None
    assert "final_iterate" not in cold.as_payload()
    digest = write_final_iterate(
        tmp_path / ITERATE_FILE_NAME, cold, config_digest="c" * 64
    )
    seed = seed_of(tmp_path)
    assert seed.sha256 == digest
    loaded = load_warm_start(seed)
    assert cold.final_iterate is not None
    for pair, block in cold.final_iterate.items():
        assert np.array_equal(loaded.blocks[pair], as_matrix(block))
    warm = solve_general(
        declaration,
        oracle,
        options=JointFrankWolfeOptions(max_iterations=3, warm_start=loaded),
    )
    provenance = warm.certificate["joint_solver"]["warm_start"]
    assert provenance["file_sha256"] == digest
    assert provenance["mix"] == WARM_START_MIX
    assert provenance["blocks_sha256"] == blocks_digest(cold.final_iterate)
    json.dumps(warm.as_payload())
    # A file whose bytes are not the named ones is refused, not read.
    with pytest.raises(WarmStartFileError) as refusal:
        load_warm_start(WarmStartSeed(file=seed.file, sha256="f" * 64))
    assert refusal.value.reason == "warm_start_hash_mismatch"


# ---------------------------------------------------------------------------
# Configuration, record and the accepted path.
# ---------------------------------------------------------------------------


def test_the_settings_round_trip_and_choosing_none_keeps_the_old_payload() -> None:
    config = RunConfig.from_payload(
        json.loads(PHASE3_CONFIG.read_text(encoding="utf-8"))
    )
    # A CONFIGURATION FROM BEFORE THE NEW FIELDS reads, and writes back the same
    # payload -- so the same digest.
    old = json.loads(PHASE3_CONFIG.read_text(encoding="utf-8"))
    assert config.to_payload() == old
    assert config.solver is not None and config.solver.method is None
    chosen = config.with_(
        solver=SolverSettings(
            max_iterations=300,
            advanced=AdvancedSolverSettings(
                oracle="spectral",
                method="pairwise",
                warm_start=WarmStartSeed(
                    file="prior/final-iterate.json", sha256="a" * 64
                ),
            ),
        )
    )
    assert RunConfig.from_payload(chosen.to_payload()) == chosen
    assert chosen.digest() != config.digest()
    assert chosen.to_payload()["solver"]["advanced"]["warm_start"] == {
        "file": "prior/final-iterate.json",
        "sha256": "a" * 64,
    }


def test_the_settings_refuse_unknown_names_and_malformed_hashes() -> None:
    with pytest.raises(RunConfigError) as refusal:
        AdvancedSolverSettings(oracle="mosek")
    assert refusal.value.reason == "solver_oracle_not_admitted"
    with pytest.raises(RunConfigError) as refusal:
        SolverSettings(method="away")
    assert refusal.value.reason == "solver_method_not_admitted"
    with pytest.raises(RunConfigError) as refusal:
        WarmStartSeed(file="x", sha256="not-a-hash")
    assert refusal.value.reason == "warm_start_hash_malformed"


def test_solver_options_map_the_choices_and_only_when_made() -> None:
    plain = solver_request(SolverSettings(max_iterations=7))
    assert plain.method == "auto" and plain.max_iterations == 7
    joint = solver_request(
        SolverSettings(
            max_iterations=7, advanced=AdvancedSolverSettings(oracle="spectral")
        )
    )
    assert (joint.oracle, joint.method, joint.warm_start) == (
        "spectral",
        "auto",
        None,
    )
    assert joint.max_iterations == 7


def test_the_record_writes_the_chosen_options_as_json() -> None:
    from certiqs_key.runs.record import _solver_options_payload

    seed = _seed(
        decoy_like_general(), file_sha256="b" * 64, source="prior/final-iterate.json"
    )
    options = JointFrankWolfeOptions(
        max_iterations=3, step_rule="pairwise", warm_start=seed
    )

    class _Outcome:
        solver_options = options

    payload = _solver_options_payload(_Outcome())  # type: ignore[arg-type]
    assert payload is not None
    assert payload["step_rule"] == "pairwise" and payload["oracle"] == "qics"
    assert payload["warm_start"]["file_sha256"] == "b" * 64
    assert payload["warm_start"]["blocks_sha256"] == seed.blocks_sha256
    json.dumps(payload)


@pytest.mark.requires_qics
def test_a_degenerate_declaration_takes_the_choices_on_the_one_driver() -> None:
    """One driver: the accepted format takes the choices too.

    A degenerate declaration runs on the joint driver like every
    other one, so the choice is made and recorded, never refused or ignored --
    for the degenerate general declaration and for the accepted-format
    declaration it is.
    """
    from certiqs_key.solvers.frank_wolfe.keyrate import solve_declaration
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    declaration = qubit_bb84_general()
    assert declaration.is_degenerate
    options = JointFrankWolfeOptions(max_iterations=4, step_rule="pairwise")
    for form in (declaration, declaration.as_accepted()):
        result = solve_declaration(form, QicsSectorChoiOracle(), options=options)
        assert result.solver_report["step_rule"] == "pairwise"
        assert result.solver_report["pairwise"]["anchor_min_eigenvalue"] > 0.0


def test_the_two_sided_point_takes_the_choices_and_the_chain_seeds_each_point(
    tmp_path: Path,
) -> None:
    from runs.two_sided import chain
    from runs.two_sided.point import build_config, parser

    from certiqs_key.runs.record import RunRecord

    base = [
        "--instance",
        "bbm92",
        "--route",
        "encoded",
        "--rounds",
        "1000",
        "--lambda-ec",
        "0",
        "--zero-ec-label",
        "diagnostic",
        "--lambda-ec-purpose",
        "diagnostic",
        "--dark-count",
        "1/1000000",
        "--iterations",
        "5",
        "--oracle",
        "spectral",
        "--method",
        "pairwise",
    ]
    arguments = parser().parse_args(
        [*base, "--loss-db", "10", "--output", str(tmp_path / "p")]
    )
    _surface, config = build_config(arguments)
    assert config.solver is not None
    assert config.solver.method is None
    assert config.solver.advanced == AdvancedSolverSettings(
        oracle="spectral", method="pairwise"
    )

    seen: list[Any] = []

    def fake_point(single: Any, *, oracle: object) -> RunRecord:
        seen.append(single)
        return RunRecord("run-record", "test", "test", {"final_iterate": {"file": "x"}})

    chained = chain.parser().parse_args(
        [*base, "--loss-db", "9", "10", "11", "--output-root", str(tmp_path / "chain")]
    )
    records = chain.run_chain(chained, oracle="oracle", run_point=fake_point)
    assert len(records) == 3
    assert [single.loss_db for single in seen] == [9.0, 10.0, 11.0]
    assert getattr(seen[0], "warm_start", None) is None
    assert seen[1].warm_start.resolve() == (
        tmp_path / "chain" / "9db" / "final-iterate.json"
    )
    assert seen[2].warm_start.resolve() == (
        tmp_path / "chain" / "10db" / "final-iterate.json"
    )


# ---------------------------------------------------------------------------
# Pairwise, polytope, spectral failure, warm-start and observer rows.
# ---------------------------------------------------------------------------


def _polytope_toy() -> GeneralDeclaration:
    from certiqs_key.meat_core.declaration.declaration import (
        AcceptanceSet,
        PolytopeData,
    )

    return replace(
        decoy_like_general(),
        acceptance_set=AcceptanceSet(
            geometry="polytope",
            polytope=PolytopeData(
                columns=2, rows=((1.0, 0.0), (-1.0, 0.0)), rhs=(0.7, -0.3)
            ),
        ),
    )


@pytest.mark.requires_qics
def test_under_pairwise_the_acceptance_half_consumes_the_exact_vertex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On a POLYTOPE, where the q half of an atom is really shrunk.

    The MEMBERSHIP of q_t is not what is asserted here
    (tests/unit/test_joint_polytope_iterate_exact.py asserts it); what is
    asserted is that each bracket pairs the gradient with the EXACT acceptance
    minimizer ``acceptance.minimize(cost)``, never the shrunk one.
    """
    from certiqs_key.solvers.frank_wolfe.general_keyrate import _prepare_general
    from certiqs_key.solvers.frank_wolfe.joint_pairwise import shrink_frequencies
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    oracle = QicsSectorChoiOracle()
    maps, acceptance = _prepare_general(_polytope_toy(), oracle)
    seen: list[dict[str, Any]] = []
    gradient = joint_driver.joint_gradient
    vertex_of = joint_driver._oracle_vertex

    def recording_gradient(m: Any, q: Any, point: Any, *args: Any, **kw: Any) -> Any:
        value = gradient(m, q, point, *args, **kw)
        seen.append({"q": dict(q), "point": dict(point), "gradient": value})
        return value

    def recording_vertex(*args: Any, **kw: Any) -> Any:
        vertex, optimal = vertex_of(*args, **kw)
        seen[-1]["vertex"] = {pair: block.copy() for pair, block in vertex.items()}
        return vertex, optimal

    monkeypatch.setattr(joint_driver, "joint_gradient", recording_gradient)
    monkeypatch.setattr(joint_driver, "_oracle_vertex", recording_vertex)
    start = random_choi_point(maps.parametrization, 1)
    result = run_joint_frank_wolfe(
        maps,
        oracle,
        acceptance,
        start,
        1.5,
        JointFrankWolfeOptions(max_iterations=8, step_rule="pairwise"),
    )
    values = list(maps.declaration.acceptance_values)
    q0 = np.asarray([acceptance.start()[chat] for chat in values])
    differs = 0
    for gate, entry in zip(result.gates, seen, strict=True):
        slope = entry["gradient"]
        exact = acceptance.minimize({chat: slope.q.get(chat, 0.0) for chat in values})
        shrunk_vector = shrink_frequencies(
            np.asarray([exact[chat] for chat in values]), q0
        )
        shrunk = dict(zip(values, shrunk_vector.tolist(), strict=True))

        def linearization(
            v: dict[str, float],
            entry: Any = entry,
            slope: Any = slope,
            gate: Any = gate,
        ) -> float:
            # The feasible side is the verified bound (req:verified-feasible-
            # side); the acceptance side is what this test is about.
            direction = gate.feasible_side_bound
            for pair, block in slope.blocks.items():
                direction -= float(
                    np.real(np.trace(block @ as_matrix(entry["point"][pair])))
                )
            for chat, rate in slope.q.items():
                shift = v[chat] - entry["q"][chat]
                if shift != 0.0:
                    direction += rate * shift
            return float(gate.objective + direction)

        assert gate.linearization == linearization(exact)
        if shrunk != exact:
            differs += 1
            assert gate.linearization != linearization(shrunk)
    assert differs > 0


@pytest.mark.requires_qics
def test_a_spectral_failure_is_never_re_routed_to_qics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A spectral group whose backend fails stops the run."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    class CountingQics(QicsSectorChoiOracle):
        def __init__(self) -> None:
            super().__init__()
            self.input_dims: list[int] = []

        def minimize(self, problem: SectorChoiProblem) -> Any:
            self.input_dims.append(problem.input_dim)
            return super().minimize(problem)

    def failing(self: Any, problem: SectorChoiProblem) -> Any:
        raise OracleFailure("spectral backend failed (test)")

    monkeypatch.setattr(SpectralSectorChoiOracle, "minimize", failing)
    maps = maps_of(decoy_like_general())
    oracle = CountingQics()
    values = list(maps.declaration.acceptance_values)
    with pytest.raises(OracleFailure, match="spectral backend failed"):
        run_joint_frank_wolfe(
            maps,
            oracle,
            SingletonAcceptanceOracle({values[0]: 0.875, values[1]: 0.125}),
            random_choi_point(maps.parametrization, 1),
            1.5,
            JointFrankWolfeOptions(max_iterations=3, oracle="spectral"),
        )
    assert all(dim != 1 for dim in oracle.input_dims)


@pytest.mark.requires_qics
@pytest.mark.parametrize("step_rule", ["vanilla", "pairwise"])
def test_the_iterate_observer_sees_every_gap_and_changes_nothing(
    step_rule: str,
) -> None:
    """The per-iterate observer sees every gap and changes nothing.

    It is told
    ``(k, gap)`` at every iterate whose gap was formed, and the run is the same
    run to the last bit with it and without it.
    """
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    maps = maps_of(decoy_like_general())
    values = list(maps.declaration.acceptance_values)
    options = JointFrankWolfeOptions(max_iterations=8, step_rule=step_rule)

    def run(observer: Any = None) -> joint_driver.JointFrankWolfeResult:
        return run_joint_frank_wolfe(
            maps,
            QicsSectorChoiOracle(),
            SingletonAcceptanceOracle({values[0]: 0.875, values[1]: 0.125}),
            random_choi_point(maps.parametrization, 1),
            1.5,
            options,
            observer=observer,
        )

    seen: list[tuple[int, float]] = []
    watched = run(lambda k, gap: seen.append((k, gap)))
    plain = run()
    assert watched.objective.hex() == plain.objective.hex()
    assert watched.h_lb is not None and plain.h_lb is not None
    assert watched.h_lb.hex() == plain.h_lb.hex()
    assert watched.gap.hex() == plain.gap.hex()
    assert watched.iterations == plain.iterations
    assert _choi_digest(watched.choi) == _choi_digest(plain.choi)
    assert watched.gates == plain.gates
    # One call per iterate that formed a gap, in order, the last one the gap
    # the run reports.
    assert [k for k, _ in seen] == [
        gate.iteration for gate in watched.gates if not math.isnan(gate.linearization)
    ]
    assert seen[-1][1] == watched.gap


@pytest.mark.requires_qics
def test_a_warm_start_and_an_explicit_start_together_are_refused() -> None:
    """Mutually exclusive solver options are refused."""
    from certiqs_key.solvers.frank_wolfe.general_keyrate import (
        solve_general_declaration,
    )
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    declaration = decoy_like_general()
    parametrization = maps_of(declaration).parametrization
    with pytest.raises(ValueError, match="not both"):
        solve_general_declaration(
            declaration,
            QicsSectorChoiOracle(),
            options=JointFrankWolfeOptions(warm_start=_seed(declaration)),
            start=joint_initial_point(parametrization),
        )


def test_the_spectral_oracle_on_a_degenerate_complex_minimum() -> None:
    """A twice-degenerate minimum in one block, tied by another."""
    rng = np.random.default_rng(11)
    sample = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
    unitary, _ = np.linalg.qr(sample)
    first = unitary @ np.diag([-2.0, -2.0, 1.0, 3.0]) @ unitary.conj().T
    problem = SectorChoiProblem(
        input_dim=1,
        block_dims={"a": 4, "b": 2},
        cost={
            "a": np.asarray(first, dtype=np.complex128),
            "b": np.diag([-2.0, 5.0]).astype(np.complex128),
        },
        coupling=Coupling.INPUT_IDENTITY,
    )
    solution = SpectralSectorChoiOracle().minimize(problem)
    assert solution.objective == pytest.approx(-2.0, abs=1e-12)
    total = sum(float(np.real(np.trace(block))) for block in solution.blocks.values())
    assert total == pytest.approx(1.0, abs=1e-14)
    for block in solution.blocks.values():
        spectrum = np.linalg.eigvalsh(as_matrix(block))
        assert spectrum[0] >= -1e-15
        assert int(np.sum(spectrum > 1e-12)) <= 1


def test_a_seed_whose_content_or_split_does_not_fit_is_refused() -> None:
    """The split, finiteness, Hermiticity and the coupling window."""
    declaration = decoy_like_general()
    parametrization = maps_of(declaration).parametrization
    interior = joint_initial_point(parametrization)
    layout = iterate_layout(parametrization)
    warm_start_point(parametrization, _seed(declaration, layout=layout), interior)
    good = _seed(declaration)
    pair = next(p for p in good.blocks if as_matrix(good.blocks[p]).shape[0] > 1)
    other_split = {
        "alice_factor_dims": {
            **layout["alice_factor_dims"],
            pair[0]: layout["alice_factor_dims"][pair[0]] + 1,
        },
        "sector_dims": layout["sector_dims"],
    }
    skewed = as_matrix(good.blocks[pair]).copy()
    skewed[0, 1] += 0.1
    broken = as_matrix(good.blocks[pair]).copy()
    broken[0, 0] = np.nan
    doubled = {
        p: (2.0 * as_matrix(b) if p[0] == pair[0] else b)
        for p, b in good.blocks.items()
    }
    cases: list[tuple[str, WarmStart]] = [
        ("warm_start_block_dims_mismatch", _seed(declaration, layout=other_split)),
        (
            "warm_start_not_feasible",
            _seed(declaration, blocks={**good.blocks, pair: skewed}),
        ),
        (
            "warm_start_not_feasible",
            _seed(declaration, blocks={**good.blocks, pair: broken}),
        ),
        ("warm_start_not_feasible", _seed(declaration, blocks=doubled)),
    ]
    for reason, seed in cases:
        with pytest.raises(WarmStartRefused) as refusal:
            warm_start_point(parametrization, seed, interior)
        assert refusal.value.reason == reason


def test_an_explicit_non_hermitian_start_is_refused() -> None:
    """The explicit ``start`` argument."""
    from certiqs_key.meat_core.errors import SupportError

    maps = maps_of(decoy_like_general())
    start = dict(joint_initial_point(maps.parametrization))
    pair = next(p for p in start if as_matrix(start[p]).shape[0] > 1)
    skewed = as_matrix(start[pair]).copy()
    skewed[0, 1] += 1e-3
    start[pair] = skewed
    values = list(maps.declaration.acceptance_values)
    with pytest.raises(SupportError, match="not Hermitian"):
        run_joint_frank_wolfe(
            maps,
            SpectralSectorChoiOracle(),
            SingletonAcceptanceOracle({values[0]: 0.5, values[1]: 0.5}),
            start,
            1.5,
        )


def test_a_seed_is_identified_by_its_blocks_and_compared_by_them() -> None:
    """The identity is derived, not asserted, and options compare by it."""
    declaration = decoy_like_general()
    interior = joint_initial_point(maps_of(declaration).parametrization)
    first = _seed(declaration, file_sha256="1" * 64)
    same_numbers = _seed(declaration, file_sha256="2" * 64, source="elsewhere")
    assert first.blocks_sha256 == blocks_digest(first.blocks)
    assert first == same_numbers and hash(first) == hash(same_numbers)
    moved = {
        pair: (1.0 - 1e-3) * as_matrix(block) + 1e-3 * as_matrix(interior[pair])
        for pair, block in first.blocks.items()
    }
    other = _seed(declaration, blocks=moved)
    assert other != first
    assert JointFrankWolfeOptions(warm_start=first) == JointFrankWolfeOptions(
        warm_start=same_numbers
    )
    assert JointFrankWolfeOptions(warm_start=first) != JointFrankWolfeOptions(
        warm_start=other
    )


def test_the_digest_names_the_seed_by_hash_and_not_by_path() -> None:
    """The path is a locator; the chain writes it relative."""
    from hashlib import sha256

    from runs.two_sided import chain

    from certiqs_key.runs.config import canonical_json

    config = RunConfig.from_payload(json.loads(PHASE3_CONFIG.read_text("utf-8")))

    def seeded(file: str, digest: str) -> RunConfig:
        return config.with_(
            solver=SolverSettings(
                advanced=AdvancedSolverSettings(
                    warm_start=WarmStartSeed(file=file, sha256=digest)
                )
            )
        )

    here = seeded("a/final-iterate.json", "a" * 64)
    assert here.digest() == seeded("C:/elsewhere/final-iterate.json", "a" * 64).digest()
    assert here.digest() != seeded("a/final-iterate.json", "c" * 64).digest()
    # A configuration without a seed digests exactly as before.
    assert (
        config.digest()
        == sha256(canonical_json(config.to_payload()).encode("utf-8")).hexdigest()
    )
    inside = Path.cwd() / "build" / "x" / "final-iterate.json"
    assert not chain._relative(inside).is_absolute()


@pytest.mark.requires_qics
def test_a_plain_step_the_direct_path_rejects_is_not_counted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``fallbacks`` counts plain steps TAKEN, not proposed.

    The plain search is made to win every iteration and the direct path to
    refuse every step, so every plain proposal is rejected.
    """
    monkeypatch.setattr(joint_driver, "joint_objective_value", lambda *a, **k: 1.0)

    def search(evaluate: Any, upper: float, value: float, settings: Any) -> Any:
        return (0.5 * upper, 0.1 if evaluate.__name__ == "plain_value" else 0.9)

    monkeypatch.setattr(joint_driver, "_search", search)
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    values = list(maps.declaration.acceptance_values)
    iterations = 3
    result = run_joint_frank_wolfe(
        maps,
        QicsSectorChoiOracle(),
        SingletonAcceptanceOracle({values[0]: 0.5, values[1]: 0.5}),
        point,
        1.5,
        JointFrankWolfeOptions(
            max_iterations=iterations,
            gap_tolerance=-float("inf"),
            oracle="spectral",
            step_rule="pairwise",
        ),
    )
    assert result.timings.calls["accepted_point_rejected"] == iterations
    assert result.solver_report["pairwise"]["fallbacks"] == 0


def test_a_warm_start_file_that_is_not_one_leaves_no_directory(tmp_path: Path) -> None:
    """The file half: verified before anything is written."""
    from runs.two_sided.point import parser, run_point

    from certiqs_key.runs.iterate_file import WarmStartFileError

    seed = tmp_path / "final-iterate.json"
    seed.write_text("{}", encoding="utf-8")
    output = tmp_path / "point"
    arguments = parser().parse_args(
        [
            "--instance", "bbm92", "--route", "encoded", "--rounds", "1000",
            "--lambda-ec", "0", "--zero-ec-label", "d", "--lambda-ec-purpose", "d",
            "--loss-db", "10", "--warm-start", str(seed), "--output", str(output),
        ]
    )  # fmt: skip
    with pytest.raises(WarmStartFileError) as refusal:
        run_point(arguments, oracle="unused")
    assert refusal.value.reason == "warm_start_not_an_iterate"
    assert not output.exists()


@pytest.mark.parametrize("kind", ["missing-file", "directory-without-seed"])
def test_a_missing_warm_start_file_is_a_named_refusal(
    tmp_path: Path, kind: str
) -> None:
    """``warm_start_file_missing`` reaches the command line."""
    from runs.two_sided.point import parser, run_point

    from certiqs_key.runs.iterate_file import WarmStartFileError

    seed = tmp_path / "absent"
    if kind == "directory-without-seed":
        seed.mkdir()
    output = tmp_path / "point"
    arguments = parser().parse_args(
        [
            "--instance", "bbm92", "--route", "encoded", "--rounds", "1000",
            "--lambda-ec", "0", "--zero-ec-label", "d", "--lambda-ec-purpose", "d",
            "--loss-db", "10", "--warm-start", str(seed), "--output", str(output),
        ]
    )  # fmt: skip
    with pytest.raises(WarmStartFileError) as refusal:
        run_point(arguments, oracle="unused")
    assert refusal.value.reason == "warm_start_file_missing"
    assert not output.exists()


@pytest.mark.requires_qics
def test_a_mismatched_seed_is_a_recorded_refusal_not_a_traceback(
    tmp_path: Path,
) -> None:
    """The solver half: a decoy seed offered to BBM92 is refused as data."""
    from runs.two_sided.point import parser, run_point

    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    common = [
        "--route", "encoded", "--rounds", "100000000", "--lambda-ec", "0",
        "--zero-ec-label", "d", "--lambda-ec-purpose", "d",
        "--dark-count", "1/1000000", "--iterations", "2", "--loss-db", "10",
    ]  # fmt: skip
    oracle = QicsSectorChoiOracle()
    decoy = tmp_path / "decoy"
    run_point(
        parser().parse_args(
            ["--instance", "decoy_bb84", *common, "--output", str(decoy)]
        ),
        oracle=oracle,
    )
    arguments = parser().parse_args(
        [
            "--instance", "bbm92", *common, "--oracle", "spectral",
            "--warm-start", str(decoy), "--output", str(tmp_path / "bbm92"),
        ]
    )  # fmt: skip
    record = run_point(arguments, oracle=oracle)
    assert record.payload["refused"] is True
    assert record.payload["stages"]["solve"]["reason"] == (
        "warm_start_source_mode_mismatch"
    )
    assert (tmp_path / "bbm92" / "record.json").exists()
    assert not (tmp_path / "bbm92" / "final-iterate.json").exists()


# ---------------------------------------------------------------------------
# Oracle returns off the coupling set, anchor and rows-digest refusals.
# ---------------------------------------------------------------------------


class _ReturnsThis:
    """An oracle returning a fixed point, one Alice-sector program at a time.

    The driver asks one program per Alice sector in declaration order, so the
    stub hands back that sector's blocks, keyed by the measured sector.
    """

    def __init__(self, maps: JointMaps, point: dict[JointSector, Matrix]) -> None:
        self._sectors = list(maps.declaration.alice_sectors)
        self._point = point
        self._next = 0

    def capabilities(self) -> Any:
        from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

        return QicsSectorChoiOracle().capabilities()

    def minimize(self, problem: SectorChoiProblem) -> Any:
        from certiqs_key.solvers.oracles.protocol import OracleSolution

        alice = self._sectors[self._next % len(self._sectors)]
        self._next += 1
        return OracleSolution(
            blocks={
                sector: np.array(block, copy=True)
                for (t, sector), block in self._point.items()
                if t == alice
            },
            objective=0.0,
            diagnostics={"sol_status": "optimal"},
        )


@pytest.mark.requires_qics
def test_a_return_outside_the_rows_withdraws_nothing() -> None:
    """``req:iterate-checks``: nothing is checked on the point the oracle returned.

    An oracle return whose declared-row residual exceeds ``constraint_rows``
    lies outside ``Feas^J(epsilon)``. The bracket does not pair with it, so it
    is not withdrawn under ``iterate_not_feasible``. The bracket reads no
    return: its feasible side is the bound verified from the dual
    (``req:verified-feasible-side``), here zero multipliers, the stub returning
    none; and "neither the point the oracle returned at that iterate nor its
    status removes the iterate" (``req:first-order-withdrawal``).
    """
    from certiqs_key.meat_core.objective.joint_rows import joint_constraint_residual
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    maps = maps_of(_trusted_with_a_row())
    zero = {
        pair: np.zeros_like(block)
        for pair, block in joint_initial_point(maps.parametrization).items()
    }
    start, _ = joint_driver._oracle_vertex(maps, QicsSectorChoiOracle(), zero, [])
    outside = random_choi_point(maps.parametrization, 2)
    window = FrankWolfeOptions().constraint_rows
    assert joint_constraint_residual(maps.parametrization, outside) > window
    values = list(maps.declaration.acceptance_values)
    result = run_joint_frank_wolfe(
        maps,
        _ReturnsThis(maps, dict(outside)),  # type: ignore[arg-type]
        SingletonAcceptanceOracle({values[0]: 0.875, values[1]: 0.125}),
        start,
        1.5,
        FrankWolfeOptions(max_iterations=1),
    )
    assert math.isfinite(result.objective)
    assert result.withdrawal is None
    (gate,) = result.gates
    assert gate.contributes
    assert result.h_lb == gate.linearization
    assert gate.constraint_row_residual <= window
    assert set(gate.feasible_side_multipliers.values()) == {"zero"}
    assert not hasattr(gate, "oracle_return_row_residual")


def test_an_anchor_that_is_not_positive_definite_stops_the_pairwise_run() -> None:
    """The anchor check's refusal branch (fail closed, never assumed)."""
    maps = maps_of(decoy_like_general())
    values = list(maps.declaration.acceptance_values)
    singular = {
        pair: np.zeros_like(block)
        for pair, block in joint_initial_point(maps.parametrization).items()
    }
    with pytest.raises(SupportError, match="anchor is not positive definite"):
        run_joint_frank_wolfe(
            maps,
            QicsLikeNeverCalled(),  # type: ignore[arg-type]
            SingletonAcceptanceOracle({values[0]: 0.875, values[1]: 0.125}),
            random_choi_point(maps.parametrization, 1),
            1.5,
            JointFrankWolfeOptions(max_iterations=2, step_rule="pairwise"),
            anchor=singular,
        )


class QicsLikeNeverCalled:
    """An oracle the anchor refusal must stop the run before consulting."""

    def capabilities(self) -> Any:
        from certiqs_key.solvers.capabilities.probe import (
            Capability,
            OracleCapabilities,
        )

        return OracleCapabilities(
            name="never", version="0", capabilities=frozenset(Capability)
        )

    def minimize(self, problem: object) -> Any:
        raise AssertionError("the anchor check should have stopped the run")


def test_a_seed_with_matching_rows_but_outside_them_is_refused() -> None:
    """The rows digest names the feasible set; the seed must still be in it.

    A seed whose rows digest matches the point's is admitted to the content
    check, and a seed that violates those rows is refused there, by name,
    rather than started from.
    """
    declaration = _trusted_with_a_row()
    parametrization = maps_of(declaration).parametrization
    seed = _seed(declaration, rows_sha256=constraint_rows_digest(declaration))
    from certiqs_key.meat_core.objective.joint_rows import joint_constraint_residual

    assert (
        joint_constraint_residual(parametrization, seed.blocks)
        > FrankWolfeOptions().constraint_rows
    )
    with pytest.raises(WarmStartRefused) as refusal:
        warm_start_point(parametrization, seed, joint_initial_point(parametrization))
    assert refusal.value.reason == "warm_start_not_feasible"
    assert "constraint-row residual" in str(refusal.value)


# ---------------------------------------------------------------------------
# The coupling check withdraws where the rows do (meat-core/coupling-check-
# stops-run; req:first-order-withdrawal (iv); rem:fo-iterate-checks).
# ---------------------------------------------------------------------------

#: How far the perturbed return and the perturbed start leave the coupling
#: window: well outside ``iterate_coupling`` and far inside positivity.
COUPLING_EXCESS = 1e-3


class _ScalesOneReturn:
    """QICS, except that its ``at``-th return is scaled by ``1 + COUPLING_EXCESS``.

    Scaling keeps every block positive semidefinite and moves only the
    coupling residual of the return (by ``COUPLING_EXCESS``, in untrusted-
    source mode where the coupling is the summed trace): the one failure a
    long run met at iteration 1085.
    """

    def __init__(self, at: int) -> None:
        from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

        self._inner = QicsSectorChoiOracle()
        self._at = at
        self._calls = 0

    def capabilities(self) -> Any:
        return self._inner.capabilities()

    def minimize(self, problem: SectorChoiProblem) -> Any:
        self._calls += 1
        solution = self._inner.minimize(problem)
        if self._calls != self._at:
            return solution
        return replace(
            solution,
            blocks={
                key: (1.0 + COUPLING_EXCESS) * np.asarray(block)
                for key, block in solution.blocks.items()
            },
        )


def _run_with_one_return_off_coupling(at: int) -> joint_driver.JointFrankWolfeResult:
    """Run the untrusted toy without rows, one call per iterate, return ``at`` scaled.

    ``at = 0`` scales nothing: the same run with every return inside.
    """
    maps = maps_of(_untrusted_without_rows())
    values = list(maps.declaration.acceptance_values)
    return run_joint_frank_wolfe(
        maps,
        _ScalesOneReturn(at=at),  # type: ignore[arg-type]
        SingletonAcceptanceOracle({values[0]: 0.875, values[1]: 0.125}),
        random_choi_point(maps.parametrization, 1),
        1.5,
        FrankWolfeOptions(max_iterations=4),
    )


def _run_with_the_second_return_off_coupling() -> joint_driver.JointFrankWolfeResult:
    """Run the untrusted toy without rows, return 2 scaled."""
    return _run_with_one_return_off_coupling(2)


@pytest.mark.requires_qics
def test_a_return_outside_the_coupling_window_withdraws_nothing() -> None:
    """``req:iterate-checks``: the return off the coupling withdraws no bracket.

    The oracle return at iterate 2 carries a coupling residual above
    ``iterate_coupling``. The bracket reads no return, so it is not withdrawn
    and iterate 2 contributes, with the same bracket as the unscaled run (its
    dual and its consumed point are those of that run), and the run completes.
    """
    result = _run_with_the_second_return_off_coupling()
    clean = _run_with_one_return_off_coupling(0)
    window = FrankWolfeOptions().iterate_coupling
    first, second = result.gates[0], result.gates[1]
    assert first.withdrawal is None
    assert second.coupling_residual <= window
    assert second.withdrawal is None
    assert second.linearization == clean.gates[1].linearization
    assert second.oracle_pairing != clean.gates[1].oracle_pairing
    assert result.status == "iteration-limit"
    assert result.iterations == 4
    assert math.isfinite(result.objective)
    # The earlier bracket stands, exactly as after a row failure.
    assert result.withdrawal is None
    contributing = [gate for gate in result.gates if gate.contributes]
    assert result.h_lb == max(gate.linearization for gate in contributing)


@pytest.mark.requires_qics
def test_a_consumed_point_outside_the_coupling_window_withdraws() -> None:
    """req:first-order-withdrawal (iv): the next point, a combination with that return.

    The step toward the scaled return makes the point consumed at iterate 3
    fail the coupling check: it withdraws under ``iterate_not_feasible``
    rather than stopping the run. The CONSUMED point is what is checked.
    """
    result = _run_with_the_second_return_off_coupling()
    window = FrankWolfeOptions().iterate_coupling
    third = result.gates[2]
    assert third.coupling_residual > window
    assert third.min_block_eigenvalue >= 0.0
    assert third.constraint_row_residual <= FrankWolfeOptions().constraint_rows
    assert third.withdrawal == "iterate_not_feasible"
    assert len(result.gates) == 4


def test_a_start_or_a_seed_outside_the_coupling_window_still_stops() -> None:
    """A START or a warm-start SEED off the coupling window is refused, not run.

    Only a point the loop consumes and an oracle return withdraw; the point a
    run begins from must already lie in the relaxed set.
    """
    declaration = _untrusted_without_rows()
    maps = maps_of(declaration)
    parametrization = maps.parametrization
    off = {
        pair: (1.0 + COUPLING_EXCESS) * np.asarray(block)
        for pair, block in random_choi_point(parametrization, 1).items()
    }
    assert (
        max(coupling_residuals(parametrization, off).values())
        > FrankWolfeOptions().iterate_coupling
    )
    values = list(maps.declaration.acceptance_values)
    with pytest.raises(SupportError, match="starting point: the coupling"):
        run_joint_frank_wolfe(
            maps,
            QicsLikeNeverCalled(),  # type: ignore[arg-type]
            SingletonAcceptanceOracle({values[0]: 0.875, values[1]: 0.125}),
            off,
            1.5,
            FrankWolfeOptions(max_iterations=2),
        )
    seed = _seed(declaration, blocks=off)
    with pytest.raises(WarmStartRefused) as refusal:
        warm_start_point(parametrization, seed, joint_initial_point(parametrization))
    assert refusal.value.reason == "warm_start_not_feasible"
    assert "coupling constraint" in str(refusal.value)


@pytest.mark.requires_qics
def test_a_returned_point_outside_the_coupling_window_is_on_the_record() -> None:
    """A returned point outside the coupling window is recorded.

    The LAST return is scaled, so the run ends by the iteration limit at a
    line-searched point no gate consumed. Its coupling residual is measured
    once at loop exit and recorded under ``returned_point``, and the flag says
    the estimate's point is not established in the relaxed set; the bracket
    and the status are what they would be without the measurement.
    """
    from certiqs_key.solvers.frank_wolfe.general_keyrate import group_b_worst

    result = _run_with_one_return_off_coupling(4)
    window = FrankWolfeOptions().iterate_coupling
    assert result.status == "iteration-limit"
    assert result.returned_point is not None
    measured = max(coupling_residuals(
        maps_of(_untrusted_without_rows()).parametrization, result.choi
    ).values())
    assert result.returned_point.worst == measured
    assert measured > window
    # Every gate read inside: the returned point is the one place it shows.
    assert all(gate.coupling_residual <= window for gate in result.gates)
    assert result.estimate_point_relaxed_member is False
    worst = group_b_worst(result, FrankWolfeOptions())
    assert worst["iterate_coupling"]["consumed_point"]["worst"] <= window
    assert worst["iterate_coupling"]["returned_point"] == {
        "worst": measured,
        "iteration": None,
        "at": "*",
    }
    assert worst["iterate_positivity"]["returned_point"]["worst"] >= 0.0
    assert worst["constraint_rows"]["returned_point"]["worst"] == 0.0
    # A record, not a gate: the brackets of iterates 1-3 stand.
    contributing = [gate for gate in result.gates if gate.contributes]
    assert contributing
    assert result.h_lb == max(gate.linearization for gate in contributing)


@pytest.mark.requires_qics
def test_a_returned_point_inside_every_window_is_established() -> None:
    """The flag is true where positivity, coupling and rows each pass."""
    from certiqs_key.solvers.frank_wolfe.general_keyrate import group_b_worst

    result = _run_with_one_return_off_coupling(0)
    assert result.returned_point is not None
    assert result.estimate_point_relaxed_member is True
    worst = group_b_worst(result, FrankWolfeOptions())
    returned = worst["iterate_coupling"]["returned_point"]
    assert returned["worst"] <= FrankWolfeOptions().iterate_coupling
    assert worst["iterate_positivity"]["returned_point"]["worst"] >= 0.0


def test_the_estimate_point_flag_reads_all_three_checks() -> None:
    """``PointCheck.established`` is rule (3) whole, and each check takes a point out.

    Positivity at exactly 0, coupling inside ``iterate_coupling`` and rows
    inside ``constraint_rows``; a point at both windows is in.
    """
    options = FrankWolfeOptions()
    coupling, rows = options.iterate_coupling, options.constraint_rows
    check = joint_driver.PointCheck
    assert check(0.0, "a", coupling, "*", rows).established(options)
    assert not check(-1e-15, "a", 0.0, "*", 0.0).established(options)
    assert not check(0.0, "a", 2 * coupling, "*", 0.0).established(options)
    assert not check(0.0, "a", 0.0, "*", 2 * rows).established(options)
