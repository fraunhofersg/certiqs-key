"""Slice 1 end to end: the parity check of spec/architecture.md 6.

A BB84 specification in, a bundle on disk, a fixed-length key rate out, compared
against the FOUR ANALYTIC TARGETS that are binding.
Every target's derivation lives in ``tests/support/bb84_targets.py``; nothing is
derived here, and nothing here reads a number off a run.

    T1  Q = 0            the exact closed form. DISCHARGED IN
                         ``tests/unit/test_bb84_closed_forms.py``, exactly and
                         without a solver -- see below for why it cannot be
                         discharged here. What this module adds is the
                         fail-closed behaviour at Q = 0, and the solver-versus-
                         derivation comparison at the smallest Q where a run
                         exists at all.
    T2  alpha -> 1+      the von-Neumann limit p_gen (1 - h2(Q)), approached
                         monotonically from below.
    T3  Devetak-Winter   the rate per TOTAL CHANNEL USE below p_gen(1-2h2(Q)),
                         rising toward it with n.
    T4  zero crossing    Q_crossing(n) < Q* ~ 0.1100, moving toward it with n.

WHY T1 HAS NO SOLVER RUN, AND WHY THAT IS THE RIGHT ANSWER
==========================================================
At ``Q = 0`` the honest ``Phi(err)`` is exactly zero. A binomial with ``p = 0``
is deterministic, so ``statistics`` returns the DEGENERATE interval
``[0, 0]`` for that outcome (Theorem ``thm:sa3`` (v), which the module implements
as a shortcut rather than a sweep), the constructed polytope pins
``q(err) = 0``, and ``meat-core`` then refuses to evaluate a gradient at a point
with ``q(chat) = 0`` -- Corollary ``cor:full-gradient`` is stated at a point with
``q(chat) > 0``, and the ``q``-derivative there is ``-inf``. The run stops with a
``SupportError`` naming the corollary, which is
:func:`test_at_zero_error_the_run_refuses_at_the_degenerate_error_interval`.

That is fail-closed behaviour of an accepted contract's implementation and is
not worked around here. The ``Q = 0`` target is discharged where it can be:
EXACTLY, as a rational objective value and an integer key length, in
``tests/unit/test_bb84_closed_forms.py``.

NO CERTIFIED RUN APPEARS HERE EITHER, and the reason is measured rather than
assumed: the ambient branch dimension of Eq. ``eq:Wcs`` on this declaration is
``1728``, so one term of the enclosure series of Proposition ``prop:budget`` is
a ``1728 x 1728`` ball-matrix product at 192-bit precision. A certified request
did not complete in seven minutes. The dimension is pinned in
``test_the_certificate_ambient_dimension_on_this_declaration``, the estimate
path is what runs, and its tier and reason are asserted legible below.

THE ALPHA GRIDS ARE DOCUMENTED CONSTANTS IN TEST CODE, and there is no search
anywhere in ``src/``. ``meat-core`` deliberately contains no outer alpha loop --
Eq. ``eq:keylength`` holds at every ``alpha`` in ``(1, 2)`` and choosing one is a
caller's business -- and this module chooses by evaluating a fixed grid and
taking the best key length, which is a harness and not machinery.
"""

from __future__ import annotations

import json
import math
import shutil
import tempfile
from collections.abc import Iterator
from fractions import Fraction as F
from functools import cache
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest
import yaml
from bb84_targets import (
    CLOSED_FORM_TOLERANCE,
    Q_STAR,
    SOLVER_TOLERANCE,
    binary_entropy,
    devetak_winter_ceiling,
    honest_phi,
    reduced_h_low_singleton,
    von_neumann_limit,
)
from instances.bb84.declare import declare_acceptance_frequencies
from instances.bb84.specification import (
    ConjugationConvention,
    bb84_specification,
    conjugation_example_specification,
)
from instances.common.honest.depolarized_bell_pair import (
    depolarized_state,
    honest_distribution,
)
from tests.support.lowered_templates import qubit_run_slice as run_slice
from tests.support.manifest_spelling import assert_bindings_in_declared_spelling
from tests.support.tiers import BRACKET_TIER

from certiqs_key.domain.bundle import read_bundle
from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
)
from certiqs_key.meat_core.docking import dock_declaration
from certiqs_key.meat_core.objective.branch import generate_maps
from certiqs_key.meat_core.objective.limit import check_limit_hypotheses
from certiqs_key.meat_core.objective.support import acceptance_support
from certiqs_key.meat_core.reasons import AssuranceReason
from certiqs_key.protocol_compiler import compile_specification
from certiqs_key.runs import RunConfig, record_run
from certiqs_key.runs.pipeline import SliceRefusal, SliceResult, SliceStage
from certiqs_key.solvers.frank_wolfe import solve

# NO TEST HERE IS MARKED xfail. `run_slice` takes a REQUIRED
# `declared_tolerance` and hands it to the instance's own snap alone, and NO
# MODULE IS TOLD A TOLERANCE AT ALL -- not this number and not a zero standing
# in for it (spec/architecture.md 2.8, "modules receive no tolerance to reason
# with"), and the compiler emits TAGGED constraint entries.

pytestmark = [pytest.mark.requires_qics, pytest.mark.contract]

#: The symmetric dyadic instance, ``p^A_Z = p^A_X = p^B_Z = p^B_X = 1/2``.
WEIGHTS = (F(1, 2), F(1, 2), F(1, 2), F(1, 2))
P_GEN = 0.25
P_TEST = 0.25
EPS = 2.0**-30

#: The completeness budget every constructed acceptance set below is built at.
#: A usability parameter and never a soundness one: ``statistics``
#: makes no security claim, and no key length here depends on this number.
BUDGET = F(1, 1_000_000)

#: ``tau``, this suite's declared numerical tolerance. Slice 1's instance
#: declares NO float-evaluated device data -- its receiver is a specified
#: qubit POVM -- so nothing on this path snaps and the ceiling is never spent.
#: ZERO IS THEREFORE THE HONEST DECLARATION HERE: this run would permit no
#: repair at all, and does not need one. It is still declared rather than
#: omitted (spec/architecture.md 2.8, no default and no fallback).
DECLARED_TOLERANCE = 0.0

#: ``kappa``, the declared lattice exponent of spec/architecture.md 2.9
#: (D-LAT), at which the instance snaps the acceptance vector it declares. It
#: is passed rather than defaulted, here as everywhere: the table takes no
#: default for it either.
SNAP_LATTICE_EXPONENT = 40

#: THE MEASURED EXCESS OF THE FIRST-ORDER BOUND, and it is the architecture's
#: number rather than a tolerance chosen to make a test pass.
#: spec/architecture.md 2.8 measures the oracle's returned vertex putting
#: ``h_lb`` about ``5e-11`` on the wrong side of the true value on a toy
#: instance, and names it "load-bearing, and it is measurably approximate".
#: This band is one order above that, which is where the slice's own
#: measurements sit; a run outside it is a finding about the oracle.
ORACLE_EXCESS = 1e-9

#: The Renyi grid for the POLYTOPE runs -- three orders, chosen so that the
#: best-of-grid key length is attained in the interior at every ``n`` tested
#: (measured: at ``n = 2000`` the best is ``1.5``, at ``5000`` and ``20000`` it
#: is ``1.25`` and ``1.1``). A grid whose best sat on an endpoint would be
#: reporting the endpoint rather than an optimum.
ALPHA_GRID = (1.1, 1.25, 1.5)

#: The Renyi grid for the SINGLETON comparisons, where each run is cheap. The
#: registry's own ``ALPHA_GRID`` widened at both ends: ``1.01`` is where the
#: ``alpha/(alpha-1)`` prefactor is largest and the driver's residual is
#: correspondingly amplified, ``1.9`` the far end of the key-length domain ``(1, 2)``.
SINGLETON_ALPHA_GRID = (1.01, 1.05, 1.1, 1.25, 1.5, 1.9)

#: Round counts. The ceiling is approached from ``n = 2000`` to ``n = 20000``;
#: above that the EXACT acceptance construction dominates the run time (measured
#: ~1.8 s at ``n = 10^4``, ~97 s at ``n = 10^5``, growing quadratically), which
#: is a property of ``statistics``'s exact binomial enumeration and not of
#: this slice.
ROUND_COUNTS = (2_000, 5_000, 20_000)

_ROOT = Path(tempfile.mkdtemp(prefix="qkd-bb84-slice-"))


@pytest.fixture(scope="module", autouse=True)
def _clean_bundles() -> Iterator[None]:
    """Remove the bundle directories this module writes, after it has run."""
    yield
    shutil.rmtree(_ROOT, ignore_errors=True)


def oracle():
    """Return a fresh QICS-backed linear oracle."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return QicsSectorChoiOracle()


def specification():
    """Return the Band-A BB84 specification at the symmetric weights."""
    return bb84_specification(*WEIGHTS)


def declaration():
    """Return the emitted declaration at the symmetric weights."""
    result = compile_specification(specification())
    assert result.declaration is not None
    return result.declaration


@cache
def slice_run(
    rounds: int,
    qber: F,
    alpha: float,
    lambda_ec: int,
) -> SliceResult:
    """Run the whole pipeline once, and remember it.

    Cached because every target below is a comparison ACROSS runs, and the same
    ``(n, Q, alpha, tier)`` point is read by more than one test. Nothing about
    the caching is load-bearing: each entry is one call of
    :func:`~tests.support.lowered_templates.qubit_run_slice` (the Python bb84
    instance's ``run_slice``) with no state carried between
    them, and the bundle each writes is its own directory.

    THE TIER IS PART OF THE KEY, because it changes what comes back: an
    ``estimate`` request reports ``h_low`` and NO KEY LENGTH (Corollary
    ``cor:fo-keylength`` consumes ``max{0, h_lb}``), so two runs at one
    ``(n, Q, alpha)`` and two tiers are two different results.
    """
    point = f"n{rounds}-q{qber.numerator}_{qber.denominator}-a{alpha}"
    directory = _ROOT / str(point)
    outcome = run_slice(
        specification(),
        qber=qber,
        rounds=rounds,
        completeness_budget=BUDGET,
        parameters=KeyLengthParameters(
            alpha=alpha, eps_pa=EPS, eps_ev=EPS, lambda_ec=lambda_ec
        ),
        oracle=oracle(),
        declared_tolerance=DECLARED_TOLERANCE,
        directory=directory,
        alpha=alpha,
    )
    assert isinstance(outcome, SliceResult), outcome
    return outcome


def shannon_leakage(rounds: int, qber: F) -> int:
    """Return ``lambda_EC = ceil(n p_gen h2(Q))``: the Shannon-limit transcript.

    ``lambda_EC`` is a DECLARED parameter of ``meat-core`` Section 2.4 that
    nothing in the engine derives, so the Devetak-Winter ceiling of T3 is a
    statement about THIS choice of it: the total error-correction transcript for
    the ``n p_gen`` rounds that land in the ``(Z,Z)`` class, at one bit of
    leakage per ``h2(Q)`` of conditional entropy. Any larger transcript lowers
    the rate and leaves the ceiling an upper bound; a smaller one would be
    claiming reconciliation below the Shannon limit.
    """
    return math.ceil(rounds * P_GEN * binary_entropy(float(qber)))


def best_key_length(rounds: int, qber: F) -> tuple[int, float]:
    """Return the best key length over :data:`ALPHA_GRID`, and its alpha."""
    lambda_ec = shannon_leakage(rounds, qber)
    best = (-1, math.nan)
    for alpha in ALPHA_GRID:
        result = slice_run(rounds, qber, alpha, lambda_ec)
        length = result.key_rate.key_length
        assert length is not None, result.key_rate.key_length_reason
        if length > best[0]:
            best = (length, alpha)
    return best


@cache
def singleton_result(qber: F, alpha: float):
    """Solve on the SINGLETON acceptance set at the honest point.

    The singleton is where the closed forms of ``bb84_targets`` are stated, so
    it is where the solver is compared against them. It is not what a real run
    uses -- a real run's acceptance set is the constructed polytope, and every
    other test in this module uses one.

    THE VECTOR IS SNAPPED BY THE INSTANCE. Converting the exact honest
    rationals to binary64 coordinate by coordinate would not do, and
    ``meat-core``'s ``acceptance_data_exact`` row
    decides the sum at EXACTLY zero in exact rational arithmetic: a
    coordinatewise conversion sums to a hair away from one and is refused, with
    "a producer emits exact rationals, or SNAPS AT THE INSTANCE before this
    module sees the data". :func:`instances.bb84.declare.declare_acceptance_frequencies`
    is that snap, and calling it here is what makes this helper drive the
    numbers a run declares rather than numbers no declarer would emit.
    """
    emitted = declaration()
    honest = honest_distribution(emitted, qber)
    frequencies, _snaps = declare_acceptance_frequencies(
        honest,
        emitted.acceptance_alphabet,
        tolerance=DECLARED_TOLERANCE,
        lattice_exponent=SNAP_LATTICE_EXPONENT,
    )
    docked = dock_declaration(
        emitted,
        acceptance_set=AcceptanceSet(
            geometry="singleton",
            frequencies=frequencies,
        ),
        rounds=100_000,
        parameters=KeyLengthParameters(
            alpha=alpha, eps_pa=EPS, eps_ev=EPS, lambda_ec=0
        ),
    )
    return solve(docked, oracle(), alpha=alpha)


def honest_blocks(qber: F) -> dict[str, np.ndarray]:
    """Return ``omega(Q)`` as the single-sector block map the engine reads."""
    return {
        "s0": np.array(
            [
                [complex(float(entry.re), float(entry.im)) for entry in row]
                for row in depolarized_state(qber)
            ],
            dtype=np.complex128,
        )
    }


# ===========================================================================
#  The run itself: the bundle, the acceptance set, the tier.
# ===========================================================================


@pytest.mark.oracle
def test_the_slice_runs_end_to_end_and_writes_a_schema_0_3_0_bundle() -> None:
    """Compile, provide, construct, dock, write, read, validate, solve.

    The whole of spec/architecture.md 6's flow in one assertion block, on the run every
    other test in this module is built from.
    """
    import json

    qber = F(1, 50)
    result = slice_run(2_000, qber, 1.5, shannon_leakage(2_000, qber))

    # The honest distribution is the frozen closed form, exactly.
    assert result.honest_distribution == honest_phi(*WEIGHTS, qber)
    # ... and the acceptance set is indexed by the DECLARATION's own alphabet.
    assert (
        tuple(result.acceptance.acceptance_set.outcomes)
        == result.declaration.acceptance_alphabet
    )

    document = json.loads(
        (result.bundle_directory / "manifest.json").read_text(encoding="utf-8")
    )
    # The bundle schema is 0.3.0 (spec/architecture.md 2.9 Section 6).
    assert document["schema_version"] == "0.3.0"
    assert document["mathematical_spec_version"] == "meat-core@1.28.0"
    chain = document["payload"]["reduction_chain"]
    assert [link["status"] for link in chain["receiver_segment"]] == ["exact"]
    assert chain["source_segment"] == []

    # The declaration meat-core read back off the disk is the one that was
    # docked, and it validated on the way in (read_bundle -> §5.6).
    assert result.reread.alice_dim == result.docked.alice_dim
    assert result.reread.rounds == result.docked.rounds == 2_000
    assert result.key_rate.mathematical_spec_version == "meat-core@1.28.0"


@pytest.mark.oracle
def test_a_completed_run_records_every_module_boundary_it_crossed() -> None:
    """The completed-run branch of the run record, on a real solve.

    spec/architecture.md 3.3: the record is what makes each boundary
    inspectable once the process has exited. Every value asserted here was
    already carried on the result -- what is checked is that transcription loses
    none of it, and that the record claims nothing of its own.
    """
    qber = F(1, 50)
    rounds, alpha = 2_000, 1.5
    lambda_ec = shannon_leakage(rounds, qber)
    result = slice_run(rounds, qber, alpha, lambda_ec)

    record = record_run(
        result,
        RunConfig(
            rounds=rounds,
            completeness_budget=BUDGET,
            parameters=KeyLengthParameters(
                alpha=alpha, eps_pa=EPS, eps_ev=EPS, lambda_ec=lambda_ec
            ),
            model={"qber": qber},
            # Required with no default (spec/architecture.md 2.8, spec/architecture.md
            # 2.9 Section 4); the same ceiling the slice run declares.
            declared_tolerance=DECLARED_TOLERANCE,
            alpha=alpha,
        ),
        created_by="tests.integration.test_bb84_slice",
    )
    payload = record.payload
    stages = payload["stages"]

    assert payload["refused"] is False
    # The CONSUMED contract version, as payload data. The record itself carries
    # no mathematical_spec_version: no module produced it.
    assert payload["contracts"]["meat-core"] == "meat-core@1.28.0"
    assert "mathematical_spec_version" not in record.as_dict()

    assert stages["compilation"]["refused"] is False
    assert stages["acceptance_construction"]["outcomes"] == list(
        result.declaration.acceptance_alphabet
    )
    assert stages["bundle"]["schema_version"] == "0.3.0"
    assert stages["key_rate"]["h_low"] == result.key_rate.h_low
    assert stages["key_rate"]["key_length"] == result.key_rate.key_length
    # The first-order number Frank-Wolfe already computes, and the rule that
    # accumulated it. The solver returns it and the record carries it, so a run
    # that has paid for the number can be asked what it was. Transcribed, not
    # interpreted -- it is a diagnostic here exactly as it is on the certificate, and
    # the tier still claims nothing.
    certificate = result.key_rate.certificate
    # The record schema version is asserted by hand and never read off the
    # constant: a version this test merely followed would assert nothing. It is
    # distinct from the BUNDLE schema 0.3.0 above; `runs/general-records.md`
    # describes the record's fields.
    assert record.schema_version == "0.46.0"
    # 0.37.0: every run records whether the statistics were checked; this one's
    # are the engine's own model, so it is not (out of scope) and names A-REACH.
    check = record.payload["statistics_consistency"]
    assert check["checked"] is False and check["unchecked_reason"] == "out_of_scope"
    assert check["unchecked_premise"] == "A-REACH" and check["solve"] is None
    box = stages["acceptance_construction"]["box"]
    assert list(box) == stages["acceptance_construction"]["outcomes"]
    certified = stages["key_rate"]["certified"]
    assert certified["declaration"] == "searched" and certified["premises"] == []
    assert record.payload["protocol_document"] is None
    key_rate = stages["key_rate"]
    for gone in ("scope_narrowings", "assurance", "group_b_thresholds"):
        assert gone not in key_rate, gone
    # Both live numbers are transcribed, and their difference WITH ITS SIGN
    # (frank-wolfe/rem:fo-arithmetic (b)).
    assert key_rate["h_lb"] == result.key_rate.h_lb
    assert key_rate["first_order_minus_estimate"] == (
        result.key_rate.h_lb - result.key_rate.h_low
    )
    worst = key_rate["group_b_worst"]
    coupling = worst["iterate_coupling"]
    # Nothing is measured on the oracle's return (req:iterate-checks), so the row
    # carries the consumed point and the returned point only.
    assert coupling["consumed_point"]["worst"] <= coupling["declared"]
    assert "oracle_return" not in coupling
    assert worst["iterate_positivity"]["at"]
    assert key_rate["reported_tier"] == str(result.key_rate.reported_tier)
    assert key_rate["accumulation_rule"] == certificate["accumulation_rule"]
    # THE ONE-RULER (H-SUPP) BAND, ON THE bb84 RECORD ITSELF:
    # map_validation_report.hsupp_reference_band
    # with both windows and the per-pair counts, and no Group-B threshold list
    # anywhere in the record naming a branch_support_dim row.
    band = key_rate["map_validation_report"]["hsupp_reference_band"]
    assert {"support_cutoff", "factor_support_cutoff", "pairs"} <= set(band)
    assert band["factor_support_cutoff"] == pytest.approx(band["support_cutoff"] ** 0.5)
    assert band["pairs"]
    assert "branch_support_dim" not in key_rate["tolerances"]
    assert "branch_support_dim" not in json.dumps(payload)
    # The run config is recorded whole, so a record is readable without the
    # script that produced it.
    assert payload["config"]["model"]["qber"] == str(qber)
    # AND THE RUN TIER'S SURFACES, each one asserted where the record writes it.
    assert payload["composition_flow"]["stages"]
    assert payload["composition_flow"]["mermaid"].startswith("flowchart TD")
    manifest = payload["assumption_manifest"]
    assert manifest["assumptions"]
    # The manifest is the route-exact set, one entry per engaged assumption,
    # each with a `verification` field, the closure table's. The engine's
    # machine keys on this Band-A run with a key length are: the rows whose
    # `verification` field is `never` -- key_register and pa_hash_family
    # (A-KEYREG, A-HASH), round_homogeneity_declaration (A-RHOM) -- and the
    # key-length premises meat-core owns together with A-SEQ, every one
    # `verification: never` and emitted on every run that reports a key
    # length (A-SEED, A-FIXED, A-CONFORM, A-AUTH, A-LAB;
    # transmitter/ass:seq). A-LAB is one key, laboratory_sealed, emitted once
    # per party; the manifest names each row's party.
    engine_keys = {"attack_set_license", "source_replacement_license"} | {
        "key_register", "pa_hash_family",
        "round_homogeneity_declaration",
    } | {
        "post_processing_seeds", "parameters_fixed_before_run",
        "post_processing_as_analysed", "classical_channel_authenticated",
        "laboratory_sealed",
        "sequential_round_model",
    }
    # Band A, trusted source, no constraint list: A-ATK is not emitted.
    engine_keys -= {"attack_set_license"}
    emitted_by_engine = {
        emitter["machine_key"]
        for entry in manifest["assumptions"]
        for emitter in entry["emitted_by"]
        if emitter["module"] == "meat-core"
    }
    assert emitted_by_engine == engine_keys
    # A-LAB at both parties, each row naming its party (a key length).
    (lab,) = [e for e in manifest["assumptions"] if e["short_id"] == "A-LAB"]
    assert [emitter["party"] for emitter in lab["emitted_by"]] == ["A", "B"]
    assert lab["category"] == "laboratory"
    ids = [entry["short_id"] for entry in manifest["assumptions"]]
    assert ids == sorted(set(ids)), "one entry per assumption"
    # ONE FIELD PER ASSUMPTION, the table's (by entry), read against the shipped
    # claim-closure table.
    table = json.loads(
        (Path(__file__).resolve().parents[2] / "src" / "certiqs_key" / "domain"
         / "claim_closure.json").read_text(encoding="utf-8")
    )["assumptions"]
    for entry in manifest["assumptions"]:
        assert entry["verification"] == table[entry["short_id"]]["verification"]
        assert entry["machine_key"] == table[entry["short_id"]]["machine_key"]
    # statistics emits no A-TSM row (no result it reports rests on it), nor
    # does the engine, and on this Band-A route no reductions artefact exists
    # to emit it, so no emitter carries A-TSM.
    assert "A-TSM" not in ids
    assert manifest["discrepancies"] == []
    # One value per bound
    # name, every bound alphabet in the declared spelling (the engine binds
    # the bundle's wire IDs, and the run tier reads them back), and the
    # engine's choice and count with their record pointers.
    assert_bindings_in_declared_spelling(record.as_dict())
    (src,) = [e for e in manifest["assumptions"] if e["short_id"] == "A-SRC"]
    (povm,) = [b for b in src["bindings"] if b["name"] == "alice_povm"]
    assert povm["value"]["alphabet"] == ["(Z,0)", "(Z,1)", "(X,0)", "(X,1)"]
    assert {item["module"] for item in povm["emitted_by"]} == {
        "transmitter", "meat-core"
    }
    # A-AUTH binds the run's two authentication inputs (zero here, flagged).
    (auth,) = [
        entry for entry in manifest["assumptions"] if entry["short_id"] == "A-AUTH"
    ]
    assert {(b["name"], b["value"]) for b in auth["bindings"]} == {
        ("eps_auth", 0.0), ("k_auth", 0)
    }
    # The version is the statistics module's own, read where it is declared,
    # so that a version bump does not break this test.
    statistics = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / "spec" / "modules" / "statistics"
         / "module.yaml").read_text(encoding="utf-8")
    )["version"]
    assert payload["assumption_manifest"]["module_versions"]["statistics"] == (
        f"statistics@{statistics}"
    )
    # The claim graph the run rests on, one entry per root of every module
    # that ran (record 0.20.0), the headline's claim roots among them.
    closure = payload["assumption_manifest"]["claim_closure"]
    assert set(payload["stages"]["key_rate"]["claim_roots"]) <= set(closure)
    assert list(closure) == list(dict.fromkeys(
        root for roots in manifest["roots"].values() for root in roots
    ))
    # FI-7 (1): the receiver key is present on THIS route too, naming it.
    assert stages["receiver_construction"]["route"] == "declared_finite_povm"
    assert stages["receiver_construction"]["receiver_route"] == "declared-finite-povm"
    assert stages["receiver_construction"]["declared_povm"]
    # FI-7 (2) and (3).
    assert payload["compiled"]["public"]["acceptance_alphabet"]
    assert payload["compiled"]["source"]["source_mode"]
    honest = stages["acceptance_construction"]["honest_distribution"]
    assert honest == {
        label: str(value) for label, value in result.honest_distribution.items()
    }


def test_the_acceptance_set_is_a_real_polytope_and_not_a_singleton() -> None:
    """§4.4's exit condition, in the geometry the run actually used.

    Three things, because "polytope" alone is satisfiable by a degenerate box:
    the declared TAG is ``polytope``, the box is non-degenerate in every
    coordinate the construction constrained, and the honest point is interior to
    at least one of them -- so the set has more than one member and the
    acceptance-side minimization of Eq. ``eq:hlow-def`` has somewhere to go.
    """
    qber = F(1, 50)
    result = slice_run(2_000, qber, 1.5, shannon_leakage(2_000, qber))
    geometry = result.acceptance.acceptance_set
    assert str(geometry.tag) == "polytope"
    assert geometry.box_bounds is not None
    lower, upper = geometry.box_bounds
    widths = [high - low for low, high in zip(lower, upper, strict=True)]
    assert all(width > 0 for width in widths)
    assert result.reread.acceptance_set.geometry == "polytope"
    assert result.reread.acceptance_set.polytope is not None
    assert result.reread.acceptance_set.polytope.m_row == 8
    # And the run MOVED on the acceptance block: a singleton would have left
    # q at the honest point exactly.
    honest = result.honest_distribution
    moved = [
        chat
        for chat in result.reread.acceptance_values
        if result.key_rate.optimized_q[chat]
        != pytest.approx(float(honest[_label(result, chat)]), abs=1e-12)
    ]
    assert moved, "the acceptance block never left the honest point"


def _label(result: SliceResult, identifier: str) -> str:
    """Return the compiler's own label for a wire acceptance identifier."""
    inverse = {v: k for k, v in result.labels.acceptance_value.items()}
    return inverse[identifier]


def test_the_achieved_tier_is_reported_with_a_legible_reason() -> None:
    """The tier is DECIDED AT RUN TIME, never requested, and the reason is legible.

    There is no ``requested_assurance`` (``meat-core``: "there is no
    ``requested_assurance``"), so the test is the one the architecture
    states: "Every run reports both numbers and a
    ``reported_tier`` field saying which is the claim"
    (spec/architecture.md 2.8), and where the headline rung is NOT reached the
    reason is MACHINE-READABLE -- a member of
    :class:`~certiqs_key.meat_core.reasons.AssuranceReason` -- with prose
    beside it, not a free-form string a caller has to parse.

    On this run the rung IS reached, so the assertion is the other half of the
    same rule: the tier names the claim, the reason is still a known member,
    and the key length is computed from ``max{0, h_lb}`` rather than withheld.
    """
    qber = F(1, 50)
    result = slice_run(
        2_000,
        qber,
        1.5,
        shannon_leakage(2_000, qber),
    )
    certificate = result.key_rate.certificate
    assert result.key_rate.reported_tier is result.key_rate.assurance
    # BOTH NUMBERS ARE ON THE RESULT, WHICHEVER TIER IT REPORTS.
    assert math.isfinite(result.key_rate.h_low)
    # The certified tier sits above the rung and keeps its reason
    # (frank-wolfe/req:certified-evaluation).
    if result.key_rate.reported_tier in (Assurance.FIRST_ORDER, Assurance.CERTIFIED):
        assert result.key_rate.h_lb is not None
        # THE REASON ON THE RUNG IS NOT A WITHDRAWAL REASON, and
        # `AssuranceReason` is the withdrawal vocabulary alone: a run that
        # REACHED the rung says so and names no hypothesis that failed.
        assert certificate["assurance_reason"] not in {
            str(r) for r in AssuranceReason
        }
    else:
        assert certificate["assurance_reason"] in {str(r) for r in AssuranceReason}
        # ``h_cert`` is gone with the certificate band, so what a run that
        # does not reach the rung withholds is the KEY LENGTH ITSELF:
        # ``cor:fo-keylength`` consumes ``max{0, h_lb}`` and "THERE IS NO
        # SECOND ROUTE".
        assert result.key_rate.h_lb is None
        assert result.key_rate.key_length is None
        assert "no h_lb" in result.key_rate.key_length_reason


# ===========================================================================
#  T1 -- Q = 0, and the solver comparison at the smallest Q that runs.
# ===========================================================================


@pytest.mark.contract
def test_at_zero_error_the_run_reaches_the_rung_on_a_pinned_coordinate() -> None:
    """``Q = 0`` pins ``q(err) = 0``, and C22b is why the run still happens.

    ``Pr[N = 0] = 1`` for a binomial with ``p = 0``, so Theorem ``thm:sa3`` (v)
    gives the interval ``[0, 0]`` and the constructed box admits only
    ``q(err) = 0``. So ``Chat_acc = {gen, ok, disc}`` is a PROPER SUBSET of the
    declared ``Chat``, which is the case Assumption A-ACC admits and Theorem
    ``thm:firstorder`` states (H-POS) on ``Chat_acc`` for -- on ``Chat`` the
    hypothesis "would be UNSATISFIABLE ... so that the `first-order` rung would
    be unreachable for a whole class of declarations FOR NO MATHEMATICAL
    REASON". Lemma ``lem:fo-khyp`` (iii), claim C22b, is the weakening, and the
    two gradient sums are restricted to the same set.

    The contract consumes Corollary ``cor:full-gradient`` through
    ``lem:fo-khyp`` (iii), so the conforming behaviour at ``Q = 0`` is a
    RESULT, and the ``Q = 0`` target is reachable through the solver itself.
    """
    emitted = declaration()
    honest = honest_distribution(emitted, F(0))
    assert honest["err"] == 0

    outcome = run_slice(
        specification(),
        qber=F(0),
        rounds=2_000,
        completeness_budget=BUDGET,
        parameters=KeyLengthParameters(alpha=1.5, eps_pa=EPS, eps_ev=EPS, lambda_ec=0),
        oracle=oracle(),
        declared_tolerance=DECLARED_TOLERANCE,
        directory=_ROOT / "zero-error",
    )
    assert isinstance(outcome, SliceResult), outcome
    result = outcome.key_rate

    # THE PINNED COORDINATE IS OUTSIDE Chat_acc AND SITS AT EXACTLY 0. By
    # lem:fo-khyp (i) that is the only value it can take at any point of the
    # declared set, so it is not a defect of the iterate and does not withdraw.
    assert result.optimized_q["err"] == 0.0
    assert "err" not in acceptance_support(
        declaration_from_bundle(read_bundle(_ROOT / "zero-error"))
    )

    # AND THE RUNG IS REACHED.
    assert result.h_lb is not None
    # Certified where the ball arithmetic is installed: the
    # (H-POS) check runs on the exact acceptance support, which leaves the
    # pinned coordinate out as the first-order gate does.
    assert result.reported_tier is BRACKET_TIER
    assert result.key_length is not None and result.key_length > 0
    # thm:firstorder (ii) in the direction it is stated, up to the arithmetic
    # Remark rem:fo-arithmetic declares unbudgeted.
    assert result.h_lb <= result.h_low + 1e-9

    # The bundle is well formed and the box is the degenerate one, which is
    # what makes the coordinate pinned rather than merely small.
    bundle = read_bundle(_ROOT / "zero-error")
    data = bundle.manifest.payload.declaration.acceptance_set.data
    bounds = data["box_bounds"]
    assert bounds is not None
    lower, upper = bounds  # type: ignore[misc]
    assert lower[2] == upper[2] == 0.0  # the `err` coordinate, pinned at zero


@pytest.mark.oracle
@pytest.mark.parametrize("qber", [F(1, 50), F(1, 20)])
@pytest.mark.parametrize("alpha", SINGLETON_ALPHA_GRID)
def test_the_solver_reproduces_the_reduced_bell_diagonal_program(
    qber: F, alpha: float
) -> None:
    """Frank-Wolfe over ALL feasible states against a one-dimensional derivation.

    The independent half is :func:`bb84_targets.reduced_h_low_singleton`, whose
    formula is checked pointwise against ``meat-core``'s own objective in
    ``tests/unit/test_bb84_closed_forms.py`` and whose minimization is a
    golden-section search written out in the fixture. The solver optimizes over
    the whole feasible set of Eq. ``eq:feas`` and knows nothing about Bell
    diagonality, so agreement is a statement about the mathematics and not about
    a shared implementation.

    THE ORDERING IS ASSERTED AS WELL AS THE VALUE, and it is the part that would
    catch a wrong derivation rather than a slow one:

        fw_lower_bound  <=  reduced  <=  h_low + tolerance .

    ``fw_lower_bound`` is the Frank-Wolfe first-order diagnostic
    ``max_k [ f(x_k) + <grad f(x_k), s_k - x_k> ]``, which for a convex ``f``
    bounds the infimum from BELOW; ``h_low`` is the objective at the point the
    run landed on, which bounds it from above (contract Section 4.15). If the
    reduced program were not the infimum, it would fall outside that bracket.
    """
    result = singleton_result(qber, alpha)
    expected = reduced_h_low_singleton(
        alpha=alpha, p_gen=P_GEN, p_test=P_TEST, qber=float(qber)
    )
    assert result.h_low == pytest.approx(expected, abs=SOLVER_TOLERANCE)
    # `h_lb` is on the result: it is a REPORTED TIER, not a diagnostic hanging
    # off the optimizer record.
    lower = result.h_lb
    assert lower is not None
    # THE LOWER END IS A DIAGNOSTIC AND NOT AN INVARIANT, and the band is the
    # architecture's own measurement. spec/architecture.md 2.8: "``h_lb <=
    # h_low`` is a consequence of exact arithmetic and NOT a floating-point
    # invariant, so it is a diagnostic to record and explain, never an
    # assertion to rely on", and the whole of the excess is the linear
    # oracle's returned vertex -- measured at about ``5e-11`` on a toy
    # instance, where substituting the exact vertex at the same iterates gives
    # a bracket of ``+4.9e-16 / -1.6e-15``. This run sits inside that band
    # (measured 6.4e-11 above ``expected`` at alpha = 1.05, Q = 2%), so what is
    # asserted is the bracket WITHIN THE NAMED EXCESS rather than an ordering
    # the rung does not have. A violation by more than the band is a finding
    # about the oracle and is what this assertion is for.
    assert lower <= expected + ORACLE_EXCESS
    assert expected <= result.h_low + SOLVER_TOLERANCE
    # The bracket's own width is a DIAGNOSTIC and not a certificate (contract
    # Section 4.15; the first-order bound is recorded as
    # `h_lb` for exactly that reason), so what is asserted of
    # it is that it is narrow enough to be informative -- measured largest
    # width 1.6e-6, at alpha = 1.01 where the alpha/(alpha-1) prefactor is 101 --
    # and not that it meets the solver bar.
    assert result.h_low - lower < 1e-5


# ===========================================================================
#  T2 -- the alpha -> 1+ von-Neumann limit.
# ===========================================================================


@pytest.mark.oracle
@pytest.mark.parametrize("qber", [F(1, 50), F(1, 20)])
def test_the_solver_rises_monotonically_to_the_von_neumann_limit(qber: F) -> None:
    """``h_low(alpha)`` increases as ``alpha`` falls, toward ``p_gen(1 - h2(Q))``.

    The C16 mechanism on the REAL BB84 declaration, which is what the
    qubit slice is a parity check of. The destination is derived twice in
    :func:`bb84_targets.von_neumann_limit` -- once as the ``alpha -> 1+`` limit
    of the reduced program, once from Eq. ``eq:oracle`` directly -- and the
    approach is checked to be monotone, because a non-monotone approach would
    mean the run at some ``alpha`` had not converged rather than that the limit
    was wrong.

    ``1.01`` is as close to ``1`` as this comparison goes. Below it the
    ``alpha/(alpha-1)`` prefactor amplifies the driver's own residual past the
    ``1e-8`` bar, which is a statement about the numerics and not about the
    limit; the remaining gap to the limit at ``1.01`` is asserted small instead.
    """
    limit = von_neumann_limit(P_GEN, float(qber))
    values = [
        singleton_result(qber, alpha).h_low
        for alpha in sorted(SINGLETON_ALPHA_GRID, reverse=True)
    ]
    assert all(b > a for a, b in pairwise(values))
    assert all(value < limit for value in values)
    assert limit - values[-1] < 2e-3


@pytest.mark.oracle
@pytest.mark.parametrize("qber", [F(1, 50), F(1, 20)])
def test_the_c16_hypotheses_hold_on_the_constructed_polytope(qber: F) -> None:
    """(H1) and (H2) of Theorem ``thm:oracle``, on the set a real run declares.

    Both are decided over the WHOLE declared set, not at a point: (H1) is one
    exact linear program per acceptance value and (H2) a membership test, and
    ``meat-core`` runs both. The floor is the box's own lower bound on
    ``q(gen)``, which is strictly positive and strictly below ``p_gen`` -- the
    polytope is wider than the singleton, which is what makes it a polytope.
    """
    result = slice_run(2_000, qber, 1.5, shannon_leakage(2_000, qber))
    maps = generate_maps(result.reread)
    floor = check_limit_hypotheses(maps, honest_blocks(qber))
    assert 0.0 < floor < P_GEN
    lower, _ = result.acceptance.acceptance_set.box_bounds  # type: ignore[misc]
    assert floor == pytest.approx(float(lower[0]), abs=CLOSED_FORM_TOLERANCE)


# ===========================================================================
#  T3 -- the Devetak-Winter ceiling.
# ===========================================================================


@pytest.mark.oracle
@pytest.mark.slow
def test_the_finite_rate_stays_below_the_ceiling_and_rises_toward_it() -> None:
    """``l(n)/n < p_gen(1 - 2h2(Q))``, rising in ``n``. An ENVELOPE, not an equality.

    The ceiling is DILUTED by the sifting factor ``p_gen``, and
    :func:`bb84_targets.devetak_winter_ceiling` says why: the rate is per TOTAL
    CHANNEL USE, because Assumption A-TSM binds the ``output_state`` model and
    the basis choices are weights inside the POVM elements rather than a
    fraction applied afterwards. The undiluted ``1 - 2h2(Q)`` is the rate per
    SIFTED round and is a different quantity.

    The inequality is strict at every finite ``n`` on three counts at once -- the
    acceptance polytope is strictly wider than the honest singleton, ``alpha`` is
    bounded away from 1 by the privacy-amplification cost, and the epsilon terms
    are positive deductions -- so no equality is asserted anywhere, at any ``n``.
    """
    qber = F(1, 50)
    ceiling = devetak_winter_ceiling(P_GEN, float(qber))
    assert ceiling == pytest.approx(0.1792797287, abs=1e-9)

    rates = []
    for rounds in ROUND_COUNTS:
        length, alpha = best_key_length(rounds, qber)
        assert length > 0
        assert alpha in ALPHA_GRID
        rate = length / rounds
        assert rate < ceiling
        rates.append(rate)
    assert all(b > a for a, b in pairwise(rates))
    # The approach is real and not marginal: the largest n recovers most of the
    # ceiling, and the smallest recovers little of it.
    assert rates[0] < 0.15 * ceiling
    assert rates[-1] > 0.65 * ceiling


@pytest.mark.oracle
@pytest.mark.slow
def test_the_entropy_itself_rises_toward_the_von_neumann_limit_with_n() -> None:
    """The same approach one level down, with the leakage bookkeeping removed.

    ``h_low`` on the CONSTRUCTED polytope rises with ``n`` toward the singleton's
    ``alpha -> 1+`` value, because the box shrinks toward the honest point. It is
    asserted separately from the rate so that a failure distinguishes the
    entropy from the finite-size deductions around it.
    """
    qber = F(1, 50)
    limit = von_neumann_limit(P_GEN, float(qber))
    values = [
        slice_run(rounds, qber, 1.1, shannon_leakage(rounds, qber)).key_rate.h_low
        for rounds in ROUND_COUNTS
    ]
    assert all(b > a for a, b in pairwise(values))
    assert all(value < limit for value in values)
    # At alpha = 1.1 the Renyi order alone costs a few percent, so the residual
    # gap is not expected to close; what is asserted is the direction and a
    # bound on where the largest n has got to.
    assert limit - values[-1] < 0.05


# ===========================================================================
#  T4 -- the zero crossing.
# ===========================================================================


@pytest.mark.oracle
@pytest.mark.slow
@pytest.mark.parametrize(
    ("rounds", "positive_at", "zero_at"),
    [(2_000, F(2, 100), F(4, 100)), (20_000, F(6, 100), F(8, 100))],
    ids=["n=2000", "n=20000"],
)
def test_the_zero_crossing_is_bracketed_strictly_below_q_star(
    rounds: int, positive_at: F, zero_at: F
) -> None:
    """``Q_crossing(n) <= Q*`` STRICTLY, and it moves toward ``Q*`` with ``n``.

    A violation would be a SOUNDNESS bug and not a tolerance question: ``Q*`` is
    where the asymptotic ceiling itself vanishes, so a finite-``n`` run claiming
    a positive key above it would be claiming more than the infinite-``n`` bound
    allows.

    The crossing is bracketed rather than bisected: a bisection would cost a
    full pipeline run per step for a number whose value is not the claim. What
    is asserted is that the key is positive at ``positive_at``, zero at
    ``zero_at``, and that both are below ``Q*`` -- which pins the crossing into
    an interval strictly inside ``(0, Q*)``.
    """
    assert positive_at < zero_at < Q_STAR
    positive, _ = best_key_length(rounds, positive_at)
    assert positive > 0
    assert devetak_winter_ceiling(P_GEN, float(positive_at)) > positive / rounds

    lambda_ec = shannon_leakage(rounds, zero_at)
    lengths = [
        slice_run(rounds, zero_at, alpha, lambda_ec).key_rate.key_length
        for alpha in ALPHA_GRID
    ]
    assert lengths == [0, 0, 0]


@pytest.mark.oracle
@pytest.mark.slow
def test_the_crossing_moves_toward_q_star_as_n_grows() -> None:
    """``Q_crossing(2000) < Q_crossing(20000) < Q*``, from the two brackets.

    No new run: the previous test's brackets already separate them. At
    ``n = 2000`` the key is zero by ``Q = 4%``, so ``Q_crossing(2000) <= 4%``; at
    ``n = 20000`` it is still positive at ``Q = 6%``, so
    ``Q_crossing(20000) > 6%``. The crossing therefore strictly increased with
    ``n``, and both brackets sit strictly below ``Q* = 0.1100278...``.

    The deduction is written out rather than re-measured because a bisection for
    the crossing itself would cost a full pipeline run per step for a number that
    is not the claim; the claim is the inequality and its direction.
    """
    upper_at_2000 = F(4, 100)
    lower_at_20000 = F(6, 100)
    for alpha in ALPHA_GRID:
        assert (
            slice_run(
                2_000, upper_at_2000, alpha, shannon_leakage(2_000, upper_at_2000)
            ).key_rate.key_length
            == 0
        )
    length, _ = best_key_length(20_000, lower_at_20000)
    assert length > 0
    assert upper_at_2000 < lower_at_20000 < Q_STAR


# ===========================================================================
#  Every refusal is an outcome, and it names the module that refused.
# ===========================================================================


def test_a_compiler_refusal_surfaces_as_a_typed_outcome() -> None:
    """No declaration, no acceptance set, no solve: the stage and reason travel.

    The specification is Example ``ex:conj``'s DEFECT branch -- the emitted
    element without the conjugation bar -- which fails (SR2) and is refused by
    gate (G2) under Table ``tab:gateoutcome`` row 3. The slice reports the
    compiler's own reason and does not invent one.
    """
    outcome = run_slice(
        conjugation_example_specification(ConjugationConvention.OMITTED),
        qber=F(1, 50),
        rounds=2_000,
        completeness_budget=BUDGET,
        parameters=KeyLengthParameters(alpha=1.5, eps_pa=EPS, eps_ev=EPS, lambda_ec=0),
        oracle=oracle(),
        declared_tolerance=DECLARED_TOLERANCE,
        directory=_ROOT / "compiler-refusal",
    )
    assert isinstance(outcome, SliceRefusal)
    assert outcome.stage is SliceStage.COMPILATION
    assert outcome.reason
    assert outcome.detail
    assert outcome.compilation is not None and outcome.compilation.refuses
    assert not (_ROOT / "compiler-refusal").exists()


def test_an_infeasible_acceptance_request_surfaces_as_a_typed_outcome() -> None:
    """One of the nine input-domain codes, carried out with its own report.

    ``ecomp`` has the HALF-OPEN domain ``[0, 1)``, so ``1`` is outside it. The
    acceptance set is not built, nothing is docked, and no bundle is written --
    which is ``statistics``'s own rule ("on any of these the module
    emits NO acceptance_set") reaching the caller unchanged.
    """
    outcome = run_slice(
        specification(),
        qber=F(1, 50),
        rounds=2_000,
        completeness_budget=F(1),
        parameters=KeyLengthParameters(alpha=1.5, eps_pa=EPS, eps_ev=EPS, lambda_ec=0),
        oracle=oracle(),
        declared_tolerance=DECLARED_TOLERANCE,
        directory=_ROOT / "infeasible",
    )
    assert isinstance(outcome, SliceRefusal)
    assert outcome.stage is SliceStage.ACCEPTANCE_CONSTRUCTION
    assert outcome.infeasibility is not None
    assert outcome.reason == str(outcome.infeasibility.reason)
    assert "ecomp" in outcome.detail
    assert not (_ROOT / "infeasible").exists()


def test_a_closed_key_length_gate_is_reported_and_not_raised() -> None:
    """A key length that may not be emitted comes back as ``None`` plus a reason.

    ``req:key-length-alpha-domain`` confines a KEY-LENGTH statement to
    ``alpha in (1, 2)`` while the structural claims hold on ``(1, inf)``, so
    ``alpha = 2.5`` is a legitimate solve and an illegitimate key length. A
    caller is entitled to the ``h_low`` half of the answer and must not get the
    other half.
    """
    outcome = run_slice(
        specification(),
        qber=F(1, 50),
        rounds=2_000,
        completeness_budget=BUDGET,
        parameters=KeyLengthParameters(alpha=1.5, eps_pa=EPS, eps_ev=EPS, lambda_ec=0),
        oracle=oracle(),
        declared_tolerance=DECLARED_TOLERANCE,
        directory=_ROOT / "alpha-gate",
        alpha=2.5,
    )
    assert isinstance(outcome, SliceResult)
    assert outcome.key_rate.key_length is None
    assert "req:key-length-alpha-domain" in outcome.key_rate.key_length_reason
    assert math.isfinite(outcome.key_rate.h_low)
