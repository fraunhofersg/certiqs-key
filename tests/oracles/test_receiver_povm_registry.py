"""The ``receiver-povm`` registry is well formed and bound to 0.2.0.

Five things this pins, and two it deliberately does not.

1. **Traceability.** Every claim ID a registry entry names exists in
   the interface transcription of the accepted ``contract.tex`` -- re-authored
   at 0.2.0 and naming 0.1.3 as ``supersedes``; all of RC1-RC12 are covered;
   the provenance counts are the RECOUNT (0 published-theorem, 12
   newly-derived, 0 open); and the machine-key vocabulary frozen in the
   registry -- fourteen input keys,
   fifteen output keys, three routes, ten catalogue entries, SEVENTEEN
   conventions, twelve ledger rows, and the SIX reason strings 0.2.0 spells --
   is the one that file carries.
2. **Admissibility (ADR-0003).** No expected value here comes from MATLAB,
   OpenQKDSecurity, CVX, MOSEK or Julia. The guard reuses
   ``registry.INADMISSIBLE_SOURCES``, imported rather than restated, so the four
   registries cannot drift on what an admissible oracle is.
3. **Well-formedness.** Unique ids, a kind from ``registry.KINDS``, a derivation
   long enough to redo on paper, and NOT ONE FLOAT ANYWHERE in the frozen data.
4. **Well-formedness of every frozen mathematical object, IN EXACT ARITHMETIC.**
   Hermiticity and positive semidefiniteness of every Gram and every POVM block
   (by Sylvester's criterion on exact principal minors, not by a numerical
   eigenvalue with a tolerance); blockwise completeness; column-stochasticity
   and monotonicity of every dark-count channel; admissibility of every
   bound-data tuple.
5. **Internal consistency of the frozen tables.** Relations that hold *among the
   frozen numbers*: the Grams of an instrument recomputed from its instrument
   matrix by Eq. ``eq:gramdef``; the deficiency identity Eq. ``eq:deficiencyid``
   with both of its summands; ``r_min`` recomputed from the frozen dark-count
   matrix by Eq. ``eq:rmin``; ``beta(n)`` recomputed from the frozen bound data
   by Eq. ``eq:beta``; ``p_mc`` recomputed from ``beta`` by Definition
   ``def:pmc``; the residual gap against the closed form of Lemma
   ``lem:windowtail`` (ii); the Schur prefactor and effective Gram recomputed
   from the frozen Grams by Eq. ``eq:schur``. These catch a transcription typo.
   THE DERIVATION IN THE ENTRY, NOT THE TABLE, STAYS AUTHORITATIVE.
6. **The 0.2.0 amendment, and the hand-off it creates.** Section 14 pins the
   delta: the fifth residual and the defect ``rho`` of Eq. ``eq:rhodef``, the
   declared tolerance domain at both endpoints, Definition ``def:tolmap`` item
   by item with each admit/refuse pair ON its boundary, the dark-count scalars
   ``rbar`` and ``delta_dc`` with Eq. ``eq:darkpmcslack`` composed exactly, the
   (X)-only branch selector, and Section 2.6 as a key vocabulary. It also pins
   the SUPERSESSION LIST: every 0.1.3 object the amendment invalidates or leaves
   stale is marked, never deleted or silently edited, and a run-B test file that
   has moved to ``receiver-povm@0.2.0`` may not assert a marked object without
   naming the guard.

**What is deliberately absent, first: any reconstruction of the module.** Nothing
here compiles a graph, builds a Fock functor, assembles a POVM from an isometry,
applies an efficiency layer or conditions a state on a probe. Every assertion
either SUBSTITUTES A FROZEN VALUE INTO A CONTRACT EQUATION or RELATES TWO FROZEN
FIELDS OF THE SAME CASE. In particular the frozen photon-number blocks of the
Fock functor are NOT rebuilt by symmetrizing tensor powers -- that would be the
implementation, checking run B's solver against a second copy of itself written
in the test tree -- and are instead checked structurally: the declared basis
order against the lexicographic enumeration the convention fixes, the block
dimension against ``binom(|Inp_C| + n - 1, n)``, the spectrum against the trace,
and, where the operator is diagonal, the entries against Eq. ``eq:spectrum``.

**And second: no assertion that ``src/certiqs_key/receiver/`` is absent on disk.**
That directory does not exist as this is written, and run B creates it. An
assertion about its absence would pass today and fail the moment the module it
guards is written, and a test that must be deleted to make progress is not a
freeze. What IS asserted, and stays true forever, is the property that actually
matters: THE FROZEN EVIDENCE IS INDEPENDENT OF THE IMPLEMENTATION -- no import
line in the registry or in this file names ``certiqs_key``, and importing the
registry does not pull ``certiqs_key.receiver`` into ``sys.modules``. That is the
same reading ``test_protocol_compiler_registry.py`` took for its own module, in
the same two-run band.
"""

from __future__ import annotations

import itertools
import math
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
import yaml
from registry_receiver_povm import (
    A_EIG_WITNESS,
    ADDITIVITY_CASES,
    AMENDMENT_SPEC_VERSION_MARKER,
    AMENDMENT_SPEC_VERSION_MARKER_0_3_0,
    ASSUMPTION_ROWS_0_3_0,
    BB84_EXACT_BLOCK_FORM,
    BETA_ZERO_AND_C_SLACK,
    BOUND_DATA_CASES,
    BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0,
    BOUND_EVALUATION_V1,
    C_DIRECTION_BOUNDS,
    C_DIRECTION_CASES,
    CATALOGUE_CASES,
    CATALOGUE_IDS,
    CHANGE_REQUEST_CANDIDATES,
    CLAIM_IDS,
    COARSE_GRAINING_CASES,
    COLLAPSE_SLACK_CASES,
    COLLAPSE_SLACK_COUNTS,
    COMPILE_CASES,
    CONDITIONAL_COMPLETENESS_CASES,
    CONVENTION_KEYS,
    CONVENTION_KEYS_0_2_0,
    CONVENTION_KEYS_0_3_0,
    D2_SLACK_CASES,
    D_ETA_CASES,
    DARK_CASES,
    DARK_COMPOSITION_N2,
    DARK_IMPROVEMENT_CASES,
    DARK_ROUTE_EXCLUSIVITY_CASES,
    DARK_SLACK_CASES,
    DECIBEL_CONVERSIONS,
    EFFICIENCY_CASES,
    EFFICIENCY_RECORD,
    ENCLOSURE_DIRECTIONS,
    EXACT_BLOCK_CASES,
    EXACT_COMPOSITE_CASES,
    EXACT_WINDOW_ADMISSIBLE_CHOICES,
    EXACT_WINDOW_BRANCH_REMAINDERS,
    EXACT_WINDOW_CASES,
    EXACT_WINDOW_VALIDATION_CASES,
    EXACTBASIC_HALVES,
    EXTINCTION_CASES,
    FOCK_CASES,
    INADMISSIBLE_SOURCES,
    INCLUSION_EXCLUSION_CASES,
    INPUT_KEYS,
    INPUT_KEYS_0_3_0,
    INPUT_ROUTES,
    INSTRUMENT_CASES,
    KINDS,
    MIXED_SETTING_CASES,
    MODE_ORDER_CASES,
    NO_WORSE_CASES,
    NO_WORSE_UNDER_EVALUATION,
    NOSLACK_STATEMENTS,
    NOT_SUPERSEDED_BY_0_2_0,
    NOT_SUPERSEDED_BY_0_3_0,
    ONE_MODE_PER_PORT_CASES,
    OPT_IN_INVARIANT,
    OUTCOME_ALPHABET,
    OUTPUT_KEYS,
    OUTPUT_KEYS_0_3_0,
    OUTPUT_PRESENCE,
    PATH_PRODUCT_CASES,
    PENDING_RETIREMENT_AT_RUN_B,
    PENDING_RETIREMENT_AT_RUN_B_0_3_0,
    PMC_BRANCH_CASES,
    PMC_X_CLAUSE_CASES,
    POVM_BLOCK_CASES,
    POVM_DEFECT_UNDER_WIDENED_D1,
    PROBE_CASES,
    Q2,
    REASON_EMITS_ARTIFACT_0_3_0,
    REASON_VOCABULARY_0_2_0,
    REASON_VOCABULARY_0_3_0,
    RECEIVER_CONSTRUCTION_PRESENCE,
    REFUSAL_CASES,
    REFUSAL_CASES_0_2_0,
    REFUSAL_CASES_0_3_0,
    REFUSAL_REASONS_ADDED_AT_0_3_0,
    REFUSAL_REASONS_VERBATIM,
    REFUSAL_REASONS_VERBATIM_0_2_0,
    REFUSAL_REASONS_VERBATIM_0_3_0,
    REFUSALS_NAMED_WITHOUT_A_SPELLING,
    REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0,
    REPRESENTATION_INDEPENDENCE_CASES,
    RES5_EXPECTATION_CASES,
    RESIDUAL5_CASES,
    RESIDUAL6_CASES,
    RESIDUAL6_REQUEST_PRESENCE,
    RESIDUAL_CASES,
    RESIDUAL_NORM_0_2_0,
    RESIDUAL_ROUTE_PRESENCE,
    RESIDUAL_SCOPING_0_3_0,
    RMIN_TRAP_CASES,
    RP_ORACLES,
    SLOT_RECORD,
    SUPERSEDED_BY_0_2_0,
    SUPERSEDED_BY_0_3_0,
    THERMAL_OCCUPATION_WEIGHTS,
    TIER_CASES,
    TIER_FALLBACK_REASON_VERBATIM,
    TOLERANCE_DOMAIN,
    TOLERANCE_DOMAIN_CASES,
    TOLERANCE_DOMAIN_CLOSED_AT,
    TOLERANCE_DOMAIN_DEGENERACIES,
    TOLERANCE_FIXTURE,
    TOLERANCE_FIXTURE_0_2_0,
    TOLERANCE_FIXTURE_0_3_0,
    TOLERANCE_UPPER_BOUND_CONSUMERS,
    TOLERANCES_ALWAYS_REQUIRED_0_3_0,
    TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0,
    TOLERANCES_UNUSED_ON_ROUTE_I,
    TOLMAP_I_CASES,
    TOLMAP_II_RANK_CASES,
    TOLMAP_ITEMS,
    TOLMAP_IV_BAND,
    TOLMAP_IV_BAND_CLOSED_AT,
    TOLMAP_IV_BAND_COST,
    TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS,
    TOLMAP_IV_BAND_FIXTURE,
    TOLMAP_IV_C_CASES,
    TOLMAP_IV_DERIVATION,
    TOLMAP_IV_NO_BEHAVIOUR_CHANGE,
    TOLMAP_IV_PRECEDENCE_CASES,
    TOLMAP_NOT_A_TEST_0_3_0,
    TOLMAP_OTHER_VALIDATION_KINDS,
    TOLMAP_OTHER_VALIDATION_KINDS_0_3_0,
    TOLMAP_RESIDUALS_ALREADY_COUNTED,
    TOLMAP_V_CONTRACTIVITY_CASES,
    WINDOW_REQUIREMENT_CASES,
    Alg,
    Mat,
    alg,
    alg_add,
    alg_conj,
    alg_mul,
    im_,
    is_superseded,
    is_superseded_0_3_0,
    q2,
    q2_neg,
    rp_oracle,
    rt,
    supersession,
    supersession_0_3_0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTERFACE_PATH = REPO_ROOT / "spec" / "modules" / "receiver" / "interface.yaml"
CONTRACT_VERSION = "0.3.0"
# The module's current version (spec/modules/receiver/module.yaml); the
# interface's pin is an accepted version no later than it, the frozen registry
# keeps the old.
MODULE_VERSION = str(
    yaml.safe_load((INTERFACE_PATH.parent / "module.yaml").read_text("utf-8"))[
        "version"
    ]
)
SUPERSEDED_VERSION = "0.2.0"
SYMBOLS_VERSION = "0.3.0"

#: THE AMENDMENT THE FROZEN 0.3.0 REGISTRY DOES NOT CARRY, compared THROUGH
#: THIS NAMED DELTA rather than edited into the frozen record (an oracle is
#: never regenerated from the code it tests, PRINCIPLES.md section 2.3).
#: receiver 0.7.0, the efficiency normalization
#: (detector-imperfections/req:efficiency-normalization): ONE input key,
#: appended after the frozen fifteen, and ONE contract-verbatim refusal,
#: appended after the frozen eight, which the reason vocabulary carries before
#: the tier fallback.
INPUT_KEYS_ADDED_AT_0_7_0: tuple[str, ...] = ("efficiency_normalization",)
REFUSAL_REASONS_ADDED_AT_0_7_0: tuple[str, ...] = (
    "efficiency_normalization_out_of_range",
)


def _interface() -> dict[str, Any]:
    with INTERFACE_PATH.open(encoding="utf-8") as handle:
        document: dict[str, Any] = yaml.safe_load(handle)
    return document


# ---------------------------------------------------------------------------
#  Exact arithmetic helpers, used only by the checks below
#
#  Everything here works in Q[sqrt2] + i Q[sqrt2] and NEVER converts to float.
#  `_q2_sign` decides the sign of p + q sqrt2 exactly, by comparing p^2 with
#  2 q^2 when the two terms have opposite signs; that is what lets positive
#  semidefiniteness be decided by Sylvester's criterion WITHOUT A TOLERANCE.
# ---------------------------------------------------------------------------

ZERO: Alg = rt(0)


def _q2_sign(value: Q2) -> int:
    p, q = value
    if q == 0:
        return (p > 0) - (p < 0)
    if p == 0:
        return (q > 0) - (q < 0)
    if p > 0 and q > 0:
        return 1
    if p < 0 and q < 0:
        return -1
    # Opposite signs: compare p^2 against 2 q^2.
    lhs, rhs = p * p, 2 * q * q
    if lhs == rhs:
        return 0
    bigger_is_p = lhs > rhs
    return (1 if p > 0 else -1) if bigger_is_p else (1 if q > 0 else -1)


def _is_real(value: Alg) -> bool:
    return value[1] == (Fraction(0), Fraction(0))


def _mat_add(a: Mat, b: Mat) -> Mat:
    return tuple(
        tuple(alg_add(x, y) for x, y in zip(ra, rb, strict=True))
        for ra, rb in zip(a, b, strict=True)
    )


def _mat_neg(a: Mat) -> Mat:
    return tuple(tuple((q2_neg(e[0]), q2_neg(e[1])) for e in row) for row in a)


def _mat_mul(a: Mat, b: Mat) -> Mat:
    n, k, m = len(a), len(b), len(b[0])
    out = []
    for i in range(n):
        row = []
        for j in range(m):
            acc = ZERO
            for t in range(k):
                acc = alg_add(acc, alg_mul(a[i][t], b[t][j]))
            row.append(acc)
        out.append(tuple(row))
    return tuple(out)


def _dagger(a: Mat) -> Mat:
    return tuple(
        tuple(alg_conj(a[i][j]) for i in range(len(a))) for j in range(len(a[0]))
    )


def _identity(n: int) -> Mat:
    return tuple(tuple(rt(1) if i == j else ZERO for j in range(n)) for i in range(n))


def _rows(a: Mat, keep: tuple[int, ...]) -> Mat:
    return tuple(a[i] for i in keep)


def _is_hermitian(a: Mat) -> bool:
    n = len(a)
    return all(a[i][j] == alg_conj(a[j][i]) for i in range(n) for j in range(n))


def _det(a: Mat) -> Alg:
    n = len(a)
    total = ZERO
    for perm in itertools.permutations(range(n)):
        sign = 1
        seen = list(perm)
        for i in range(n):
            for j in range(i + 1, n):
                if seen[i] > seen[j]:
                    sign = -sign
        term = rt(sign)
        for i, j in enumerate(perm):
            term = alg_mul(term, a[i][j])
        total = alg_add(total, term)
    return total


def _principal_minor(a: Mat, idx: tuple[int, ...]) -> Alg:
    return _det(tuple(tuple(a[i][j] for j in idx) for i in idx))


def _is_psd(a: Mat) -> bool:
    """Exact positive semidefiniteness of a Hermitian matrix.

    A Hermitian matrix is positive semidefinite IFF every PRINCIPAL minor is
    non-negative (not merely the leading ones, which decide definiteness). The
    matrices frozen here are at most 4x4, so the 2^n - 1 minors are cheap, and
    every one of them is real because the matrix is Hermitian.
    """
    n = len(a)
    if not _is_hermitian(a):
        return False
    for size in range(1, n + 1):
        for idx in itertools.combinations(range(n), size):
            minor = _principal_minor(a, idx)
            if not _is_real(minor):
                return False
            if _q2_sign(minor[0]) < 0:
                return False
    return True


def _loewner_leq(a: Mat, b: Mat) -> bool:
    return _is_psd(_mat_add(b, _mat_neg(a)))


def _trace(a: Mat) -> Alg:
    total = ZERO
    for i in range(len(a)):
        total = alg_add(total, a[i][i])
    return total


def _occupations(modes: int, photons: int) -> tuple[tuple[int, ...], ...]:
    """Occupation vectors of a given weight, in ASCENDING LEXICOGRAPHIC order.

    That is the order Section 2.5 `subsystem_order` fixes, read as the module
    docstring of the registry records. It is combinatorics on the declared
    convention and reconstructs nothing about the Fock functor.
    """
    return tuple(
        sorted(
            v
            for v in itertools.product(range(photons + 1), repeat=modes)
            if sum(v) == photons
        )
    )


def _block_dimension(modes: int, photons: int) -> int:
    return math.comb(modes + photons - 1, photons)


def _subsets(port_count: int) -> tuple[tuple[int, ...], ...]:
    out: list[tuple[int, ...]] = []
    for size in range(port_count + 1):
        out += [
            tuple(sorted(s)) for s in itertools.combinations(range(port_count), size)
        ]
    return tuple(out)


def _no_floats(obj: Any, trail: str = "") -> None:
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, float):
        raise AssertionError(f"float found at {trail}: {obj!r}")
    if isinstance(obj, (int, str, Fraction)):
        return
    if isinstance(obj, (tuple, list, set, frozenset)):
        for i, item in enumerate(obj):
            _no_floats(item, f"{trail}[{i}]")
        return
    if isinstance(obj, dict):
        for key, value in obj.items():
            _no_floats(key, f"{trail}.key")
            _no_floats(value, f"{trail}[{key!r}]")
        return
    if hasattr(obj, "__dataclass_fields__"):
        for field_name in obj.__dataclass_fields__:
            _no_floats(getattr(obj, field_name), f"{trail}.{field_name}")
        return
    raise AssertionError(f"unexpected type at {trail}: {type(obj)!r}")


# ---------------------------------------------------------------------------
#  1. Traceability against the G4 interface
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
#  NINE INTERFACE-TRANSCRIPTION CHECKS ARE NOT REPLAYED IN THIS REPOSITORY.
#
#  They read sections of an earlier interface transcription that
#  `spec/modules/receiver/interface.yaml` deliberately does not have: the
#  `claims:` and `assumptions:` ledgers (one claim file each under
#  `spec/modules/receiver/claims/`, where `python -m harness.check_claims`
#  is the executable form), `contract_version` (now `module.yaml`'s
#  `version`), `delta_from_0_2_0`, `change_requests`, `change_requests_open`
#  and a status file the module does not have. They are not rewritten
#  against the claim files here:
#
#    test_interface_yaml_exists_and_names_the_accepted_contract
#    test_every_oracle_claim_id_exists_in_the_interface
#    test_provenance_counts_match_the_recount
#    test_refs_are_present_exactly_where_a_provenance_block_names_a_locator
#    test_the_interface_carries_the_thirteen_assumption_ledger_rows
#    test_the_interface_is_the_0_3_0_amendment
#    test_the_interface_delta_names_every_change_with_its_site
#    test_the_0_2_0_change_request_candidates_are_all_cleared
#    test_the_0_3_0_change_request_candidates_are_all_cleared
#
#  Nothing frozen was edited for this: the registry rows they read are
#  untouched and every OTHER check below still replays them.
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_registry_covers_every_claim_of_the_contract() -> None:
    covered = {claim for entry in RP_ORACLES for claim in entry.claims}
    assert set(CLAIM_IDS) <= covered
    # Every claim is ALSO pinned by an entry that names it and few others, so
    # the coverage is not carried by the interface entry alone.
    focused = {
        claim
        for entry in RP_ORACLES
        if len(entry.claims) == 1
        for claim in entry.claims
    }
    assert set(CLAIM_IDS) == focused


@pytest.mark.contract
def test_the_interface_conventions_include_the_sixteen_0_1_3_bullets() -> None:
    """The 0.1.3 sixteen, all still present and all still saying what they said.

    Section 2.5 gained a SEVENTEENTH bullet at 0.2.0 and changed the text of two
    of these; the count assertion moved to
    ``test_the_interface_conventions_are_the_seventeen_bullets``, and
    CONVENTION_KEYS is marked in SUPERSEDED_BY_0_2_0 as INCOMPLETE rather than
    edited.
    """
    conventions = _interface()["conventions"]
    for key in CONVENTION_KEYS:
        assert key in conventions, key
    assert len(CONVENTION_KEYS) == 16
    assert conventions["log_base"] == 2
    assert conventions["entropy_units"] == "bits"
    # Inherited and USED NOWHERE HERE: no Renyi quantity occurs in the contract.
    assert conventions["entropy_variant"] == "sandwiched-renyi"
    assert conventions["arrow"] == "up"
    assert conventions["alpha_domain"] == "(1, 2)"
    assert conventions["test_statistics_model"] == "output_state"
    assert conventions["round_homogeneity"] == "required"
    assert conventions["numerics"] == BOUND_EVALUATION_V1 == "floating_point"
    assert conventions["mirror_handedness"].strip()
    # The ONE default value the contract itself fixes.
    assert "default false" in conventions["mirror_handedness"].lower()
    # THE MODULE ID IS `receiver` HERE, `receiver-povm` IN THE FROZEN
    # STRING. THE CODE HAS FOLLOWED -- `artifact.py`
    # binds `receiver@0.1.2` and an artifact reports the id this interface
    # spells. The frozen MATHEMATICAL_SPEC_VERSION_0_3_0 still reads
    # `receiver-povm@0.3.0` and is meant to: it records what the 0.3.0
    # freeze bound, and MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2 is
    # beside it for what the code binds.
    # The bullet names the interface's pin, the version whose implementation
    # is accepted. A pin moves with the code that implements a version, so
    # after a presentational batch it may trail module.yaml's version, never
    # pass it (tests/unit/test_emitted_pins.py holds the code to the pin).
    pin = _interface()["artifact_bindings"]["mathematical_spec_version"]
    assert conventions["artifact_bindings_mathematical_spec_version"] == pin
    module_id, _, pinned = pin.partition("@")
    assert module_id == "receiver"
    assert "draft" not in pinned
    assert tuple(map(int, pinned.split("."))) <= tuple(
        map(int, MODULE_VERSION.split("."))
    )
    # The beamsplitter bullet was QUALIFIED at 0.2.0 (CR-3): TWO conditions
    # where 0.1.3 stated one, and the input-side factor named.
    assert "TWO CONDITIONS" in conventions["beamsplitter_convention"]
    for key in (
        "matrix_convention",
        "composition_order",
        "embedding",
        "subsystem_order",
        "polarization_basis",
        "waveplate_convention",
        "beamsplitter_convention",
        "povm_index_convention",
        "fail_closed",
    ):
        assert conventions[key].strip(), key
    # The precedence rule is the load-bearing clause of `subsystem_order`.
    assert "PRECEDENCE" in conventions["subsystem_order"]


@pytest.mark.contract
def test_the_interface_key_vocabulary_is_the_frozen_one() -> None:
    document = _interface()
    inputs = tuple(row["name"] for row in document["inputs"])
    outputs = tuple(row["name"] for row in document["outputs"])
    # `requested_assurance` stays a frozen input key: the certified tier is
    # dropped but the field still carries `estimate` and `first-order`. The
    # 0.7.0 key follows the frozen fifteen (INPUT_KEYS_ADDED_AT_0_7_0).
    assert inputs == INPUT_KEYS_0_3_0 + INPUT_KEYS_ADDED_AT_0_7_0
    assert outputs == OUTPUT_KEYS_0_3_0 == OUTPUT_KEYS
    assert len(INPUT_KEYS_0_3_0) == 15
    assert len(outputs) == 15
    # ONE input key is added and none is removed; the 0.2.0 tuple is marked.
    assert set(INPUT_KEYS_0_3_0) - set(INPUT_KEYS) == {"exact_window"}
    assert not set(INPUT_KEYS) - set(INPUT_KEYS_0_3_0)
    assert is_superseded_0_3_0("INPUT_KEYS")
    assert tuple(document["input_routes"]["mutually_exclusive"]) == INPUT_ROUTES
    routed = tuple(row["name"] for row in document["inputs"] if row["route"])
    assert routed == INPUT_ROUTES
    # Two key NAMES appear on both sides and mean different objects.
    both = {row["name"] for row in document["key_name_reused_on_both_sides"]}
    assert both == set(inputs) & set(outputs) == {"port_grams", "dark_count_channel"}


@pytest.mark.contract
def test_the_receiver_construction_presence_rule() -> None:
    """The ONE conditional output key, and both halves of its rule."""
    outputs = {row["name"]: row for row in _interface()["outputs"]}
    conditional = {name for name, row in outputs.items() if row["presence"] != "always"}
    assert conditional == {"receiver_construction"}
    assert outputs["receiver_construction"]["presence"] == "route (iii) only"
    assert dict(OUTPUT_PRESENCE) == {
        name: row["presence"] for name, row in outputs.items()
    }
    # All three routes are frozen, and exactly one carries the key.
    assert len(RECEIVER_CONSTRUCTION_PRESENCE) == 3
    present = {route for _, route, flag, _ in RECEIVER_CONSTRUCTION_PRESENCE if flag}
    assert present == {"element_graph"}
    assert {route for _, route, _, _ in RECEIVER_CONSTRUCTION_PRESENCE} == set(
        INPUT_ROUTES
    )


@pytest.mark.contract
def test_the_catalogue_ids_and_the_two_layers() -> None:
    document = _interface()
    ids = tuple(row["id"] for row in document["component_catalogue"])
    assert ids == CATALOGUE_IDS
    assert len(ids) == 10
    for row in document["component_catalogue"]:
        assert row["domain"].strip(), row["id"]
        assert row["lossless_exactly_when"].strip(), row["id"]
    # L1 and L2 are LAYERS and deliberately NOT rows of the catalogue.
    layers = {row["id"] for row in document["layers"]}
    assert layers == {"L1", "L2"}
    assert layers.isdisjoint(ids)
    # Every catalogue entry is exercised by at least one frozen case, at an
    # interior AND a boundary parameter tuple where the entry has both.
    covered = {case.entry_id for case in CATALOGUE_CASES}
    assert covered == set(CATALOGUE_IDS)
    for entry_id in CATALOGUE_IDS:
        positions = {c.position for c in CATALOGUE_CASES if c.entry_id == entry_id}
        assert positions == {"interior", "boundary"}, entry_id


@pytest.mark.contract
def test_the_0_1_3_change_request_candidates_are_recorded_as_the_pass_left_them() -> (
    None
):
    """The 0.1.3 list, unedited: ten candidates, six cleared, four routed.

    All four routed items are CLOSED by the 0.2.0 amendment, which is asserted
    in ``test_the_0_2_0_change_request_candidates_are_all_cleared``; the tuple
    itself is marked in SUPERSEDED_BY_0_2_0 rather than rewritten, because run A
    does not edit a previous pass's evidence.
    """
    assert len(CHANGE_REQUEST_CANDIDATES) == 10
    verdicts = [row[0] for row in CHANGE_REQUEST_CANDIDATES]
    assert sum(v.startswith("CLEARED") for v in verdicts) == 6
    routed = [row for row in CHANGE_REQUEST_CANDIDATES if row[0].startswith("ROUTED")]
    assert len(routed) == 4
    for row in routed:
        assert "does not block this freeze" in row[0]
        assert any(f"CR-{i}" in row[0] for i in range(1, 5)), row[0]
    assert is_superseded("CHANGE_REQUEST_CANDIDATES")


# ---------------------------------------------------------------------------
#  2. Admissibility, well-formedness and independence
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_no_inadmissible_source_is_named() -> None:
    """ADR-0003, with the guard imported from registry.py rather than restated."""
    assert INADMISSIBLE_SOURCES == (
        "MATLAB",
        "OpenQKDSecurity",
        "CVX",
        "MOSEK",
        "Julia",
    )
    blob = "\n".join(
        entry.subject + entry.derivation + "".join(entry.hypotheses)
        for entry in RP_ORACLES
    )
    for banned in INADMISSIBLE_SOURCES:
        assert banned not in blob, banned


@pytest.mark.contract
def test_entries_are_well_formed() -> None:
    ids = [entry.oracle_id for entry in RP_ORACLES]
    assert len(set(ids)) == len(ids)
    for entry in RP_ORACLES:
        assert entry.oracle_id.startswith("O-RP-"), entry.oracle_id
        assert entry.kind in KINDS, (entry.oracle_id, entry.kind)
        assert entry.assurance == "estimate", entry.oracle_id
        assert entry.subject.strip(), entry.oracle_id
        # Long enough to redo on paper.
        assert len(entry.derivation) > 600, (entry.oracle_id, len(entry.derivation))
        assert rp_oracle(entry.oracle_id) is entry


@pytest.mark.contract
def test_not_one_float_appears_in_the_frozen_values() -> None:
    """The whole substrate is exact; a float would be an approximation."""
    for name, obj in (
        ("FOCK_CASES", FOCK_CASES),
        ("COMPILE_CASES", COMPILE_CASES),
        ("CATALOGUE_CASES", CATALOGUE_CASES),
        ("INSTRUMENT_CASES", INSTRUMENT_CASES),
        ("REPRESENTATION", REPRESENTATION_INDEPENDENCE_CASES),
        ("POVM_BLOCK_CASES", POVM_BLOCK_CASES),
        ("COARSE_GRAINING_CASES", COARSE_GRAINING_CASES),
        ("BOUND_DATA_CASES", BOUND_DATA_CASES),
        ("RESIDUAL_CASES", RESIDUAL_CASES),
        ("EFFICIENCY_CASES", EFFICIENCY_CASES),
        ("DARK_CASES", DARK_CASES),
        ("PROBE_CASES", PROBE_CASES),
        ("REFUSAL_CASES", REFUSAL_CASES),
        ("MODE_ORDER_CASES", MODE_ORDER_CASES),
        ("TOLERANCE_FIXTURE", TOLERANCE_FIXTURE),
        ("RMIN_TRAP_CASES", RMIN_TRAP_CASES),
        ("DECIBEL_CONVERSIONS", DECIBEL_CONVERSIONS),
        ("BETA_ZERO_AND_C_SLACK", BETA_ZERO_AND_C_SLACK),
        ("THERMAL_OCCUPATION_WEIGHTS", THERMAL_OCCUPATION_WEIGHTS),
        ("D_ETA_CASES", D_ETA_CASES),
        ("EFFICIENCY_RECORD", EFFICIENCY_RECORD),
        ("DARK_IMPROVEMENT_CASES", DARK_IMPROVEMENT_CASES),
        ("DARK_COMPOSITION_N2", DARK_COMPOSITION_N2),
        ("CONDITIONAL_COMPLETENESS", CONDITIONAL_COMPLETENESS_CASES),
        ("ADDITIVITY_CASES", ADDITIVITY_CASES),
        ("INCLUSION_EXCLUSION", INCLUSION_EXCLUSION_CASES),
        ("PATH_PRODUCT_CASES", PATH_PRODUCT_CASES),
        ("ONE_MODE_PER_PORT", ONE_MODE_PER_PORT_CASES),
        ("EXTINCTION_CASES", EXTINCTION_CASES),
    ):
        _no_floats(obj, name)


@pytest.mark.contract
def test_the_registry_is_independent_of_the_module_it_pins() -> None:
    """Self-containment. NOT an assertion that the package is absent on disk."""
    for name in ("registry_receiver_povm.py", Path(__file__).name):
        source = (Path(__file__).parent / name).read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                assert "certiqs_key" not in stripped, (name, stripped)
    # Importing the frozen evidence must not pull the implementation in.
    # Checked in a FRESH interpreter: the in-process form of this assertion
    # was order-dependent once the package existed (any earlier test module
    # importing certiqs_key.receiver made it fail without the registry being at
    # fault).
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "import registry_receiver_povm; "
            "print('certiqs_key.receiver' in sys.modules)",
            str(Path(__file__).parent),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert probe.stdout.strip() == "False", probe.stdout


@pytest.mark.contract
def test_the_0_1_3_tolerance_fixture_is_a_fixture_and_not_a_frozen_value() -> None:
    """Section 2.1 makes `numerical_tolerances` a DECLARED, never-defaulted input.

    So the registry may not carry one as a property of a number. What it carries
    is a fixture playing the role of that declared input.

    THIS IS A STATEMENT ABOUT THE 0.1.3 FIXTURE, which is kept unedited: its
    six keys are 0.1.3's, with eps_hyp strictly positive as Definition def:pmc
    then required. 0.2.0 removes eps_hyp with predicate (C) and adds eps_5, so
    TOLERANCE_FIXTURE is marked in SUPERSEDED_BY_0_2_0 and
    TOLERANCE_FIXTURE_0_2_0 is the declared tuple the amendment states; see
    ``test_the_0_2_0_tolerance_fixture_is_the_declared_tuple``.
    """
    assert is_superseded("TOLERANCE_FIXTURE")
    assert set(TOLERANCE_FIXTURE) == {
        "eps_1",
        "eps_2",
        "eps_3",
        "eps_4",
        "eps_gap",
        "eps_hyp",
    }
    assert all(isinstance(v, Fraction) for v in TOLERANCE_FIXTURE.values())
    assert all(v >= 0 for v in TOLERANCE_FIXTURE.values())
    assert TOLERANCE_FIXTURE["eps_hyp"] > 0
    # Every PASSING residual is EXACTLY zero, which no norm can change.
    for case in RESIDUAL_CASES:
        if case.passes:
            assert case.value_spectral == 0, case.case_id
            assert case.value_frobenius_squared == 0, case.case_id


# ---------------------------------------------------------------------------
#  3. RC1 -- the Fock blocks, checked STRUCTURALLY and never rebuilt
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_fock_blocks_carry_the_declared_basis_order_and_dimension() -> None:
    for case in FOCK_CASES:
        modes = len(case.mode_labels)
        expected = _occupations(modes, case.photon_number)
        assert case.basis_order == expected, case.case_id
        dim = _block_dimension(modes, case.photon_number)
        assert len(case.basis_order) == dim, case.case_id
        assert len(case.block) == dim, case.case_id
        assert all(len(row) == dim for row in case.block), case.case_id
    # The dimension rule of Section 2.2 `block_dimensions`, spelled out at
    # |Inp_C| = 2 for n = 0, 1, 2.
    assert [_block_dimension(2, n) for n in (0, 1, 2)] == [1, 2, 3]
    assert _occupations(2, 1) == ((0, 1), (1, 0))
    assert _occupations(2, 2) == ((0, 2), (1, 1), (2, 0))


@pytest.mark.contract
def test_diagonal_fock_blocks_agree_with_eq_spectrum() -> None:
    """Eq. eq:spectrum on the cases where the operator is diagonal.

    For a DIAGONAL X the block is diagonal with entry prod_j x_j^{m_j} at the
    occupation vector m. Substituting the frozen operator entries into that
    formula, in the frozen basis order, checks the order and the entries at
    once -- without reconstructing the functor for a general operator.
    """
    for case in FOCK_CASES:
        x = case.operator
        n = len(x)
        if any(x[i][j] != ZERO for i in range(n) for j in range(n) if i != j):
            continue
        for row, m in enumerate(case.basis_order):
            for col in range(len(case.basis_order)):
                value = case.block[row][col]
                if row != col:
                    assert value == ZERO, (case.case_id, row, col)
                    continue
                expected = rt(1)
                for j, power in enumerate(m):
                    for _ in range(power):
                        expected = alg_mul(expected, x[j][j])
                assert value == expected, (case.case_id, m)


@pytest.mark.contract
def test_fock_spectra_are_consistent_with_the_frozen_block() -> None:
    for case in FOCK_CASES:
        if case.spectrum is None:
            continue
        trace = _trace(case.block)
        assert _is_real(trace), case.case_id
        assert trace[0] == q2(sum(case.spectrum)), case.case_id
        assert len(case.spectrum) == len(case.basis_order), case.case_id
    # Eq. eq:blockbounds, the two ATTAINED endpoints, on the one case that
    # exists to freeze them: lmin(A) = 1/4 and lmax(A) = 3/4 give
    # (1 - 3/4)^2 = 1/16 and (1 - 1/4)^2 = 9/16.
    case = next(c for c in FOCK_CASES if c.case_id == "FOCK-SPECTRUM-n2")
    spectrum = case.spectrum
    assert spectrum is not None
    assert min(spectrum) == Fraction(1, 16)
    assert max(spectrum) == Fraction(9, 16)
    assert _is_hermitian(case.block)
    assert _is_psd(case.block)


# ---------------------------------------------------------------------------
#  4. RC2 -- compilation
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_compiled_matrices_are_contractions_and_lossless_iff_unitary() -> None:
    for case in COMPILE_CASES:
        if case.compiled is None:
            assert case.refused_condition in {"E1", "E2", "E3"}, case.case_id
            assert case.lossless is None, case.case_id
            continue
        assert case.refused_condition is None, case.case_id
        n = len(case.compiled)
        product = _mat_mul(_dagger(case.compiled), case.compiled)
        # Theorem thm:compilation-well-defined (ii): admissibility BY CONSTRUCTION.
        assert _loewner_leq(product, _identity(n)), case.case_id
        # Theorem thm:compilation-well-defined (iii): unitary IFF every element is
        # lossless.
        assert (product == _identity(n)) is case.lossless, case.case_id


@pytest.mark.contract
def test_the_three_well_formedness_conditions_are_separated() -> None:
    """(E1), (E2) and (E3) each fail ALONE in one frozen graph."""
    refused = {c.refused_condition for c in COMPILE_CASES if c.compiled is None}
    assert refused == {"E1", "E2", "E3"}
    # A cycle has NO linear extension at all -- the whole content of (E2).
    cyclic = next(c for c in COMPILE_CASES if c.refused_condition == "E2")
    assert cyclic.linear_extensions == ()
    # (E3) fails on a graph with TWO linear extensions and intersecting
    # supports; and the SAME two elements compile when an edge orders them.
    e3 = next(c for c in COMPILE_CASES if c.refused_condition == "E3")
    assert len(e3.linear_extensions) == 2
    supports = [set(el[2]) for el in e3.elements]
    assert supports[0] & supports[1]
    ordered = next(c for c in COMPILE_CASES if c.case_id == "G-ORDERED")
    assert [el[1] for el in ordered.elements] == [el[1] for el in e3.elements]
    assert ordered.edges and not e3.edges
    assert ordered.compiled is not None
    # Independence of the sort: the parallel graph has two extensions and one
    # compiled matrix, and its elements have DISJOINT supports.
    par = next(c for c in COMPILE_CASES if c.case_id == "G-PARALLEL")
    assert len(par.linear_extensions) == 2
    assert not set(par.elements[0][2]) & set(par.elements[1][2])
    # Every linear extension really is one: it lists every element once and
    # respects every declared edge.
    for case in COMPILE_CASES:
        names = [el[0] for el in case.elements]
        for order in case.linear_extensions:
            assert sorted(order) == sorted(names), case.case_id
            for tail, head in case.edges:
                assert order.index(tail) < order.index(head), case.case_id


# ---------------------------------------------------------------------------
#  5. RC3 -- the catalogue
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_every_catalogue_matrix_is_a_contraction_with_its_lossless_verdict() -> None:
    for case in CATALOGUE_CASES:
        n = len(case.matrix)
        product = _mat_mul(_dagger(case.matrix), case.matrix)
        assert _is_hermitian(product), case.case_id
        # Theorem thm:catalogue-admissibility: admissible on the WHOLE declared domain.
        assert _loewner_leq(product, _identity(n)), case.case_id
        # ... and lossless EXACTLY on the subfamily Table tab:catalogue names.
        assert (product == _identity(n)) is case.lossless, case.case_id
        assert case.position in {"interior", "boundary"}, case.case_id
        assert case.entry_id in CATALOGUE_IDS, case.case_id


@pytest.mark.contract
def test_the_beamsplitter_determinant_and_the_dropped_phase_pair() -> None:
    """Section 2.5 `beamsplitter_convention`: real at phi = 0 with det = -1."""
    lossless_c1 = [c for c in CATALOGUE_CASES if c.entry_id == "C1" and c.lossless]
    assert lossless_c1
    for case in lossless_c1:
        assert case.determinant == rt(-1), case.case_id
    real_at_zero = next(c for c in CATALOGUE_CASES if c.case_id == "C1-interior")
    assert all(_is_real(e) for row in real_at_zero.matrix for e in row)
    # The 50:50 case carries sqrt2 and is NOT rational, and it is exact anyway.
    half = next(c for c in CATALOGUE_CASES if c.case_id == "C1-half")
    assert any(e[0][1] != 0 for row in half.matrix for e in row)
    assert half.determinant == rt(-1)
    # The retarder phase, frozen twice: the contract's element and the variant
    # an implementation produces if it drops exp(-i delta / 2).
    kept = next(c for c in CATALOGUE_CASES if c.case_id == "C3-hwp-rational")
    dropped = next(c for c in CATALOGUE_CASES if c.case_id == "C3-hwp-DROPPED-PHASE")
    assert kept.matrix != dropped.matrix
    # They differ by exactly the factor -i on every entry, and BOTH are unitary.
    minus_i = alg(q2(), q2(-1))
    for row_k, row_d in zip(kept.matrix, dropped.matrix, strict=True):
        for e_k, e_d in zip(row_k, row_d, strict=True):
            assert e_k == alg_mul(minus_i, e_d)
    assert kept.lossless and dropped.lossless
    # And the decibel conversions are exact at the three frozen decades.
    assert dict(DECIBEL_CONVERSIONS) == {
        0: Fraction(1),
        10: Fraction(1, 10),
        20: Fraction(1, 100),
    }


# ---------------------------------------------------------------------------
#  6. RC4 -- Grams, the deficiency identity, the rank bound
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_frozen_grams_agree_with_the_frozen_instrument_matrix() -> None:
    """Eq. eq:gramdef, recomputed exactly: A_k = Gamma_Inp^dagger E_k Gamma_Inp."""
    for case in INSTRUMENT_CASES:
        grams = dict(case.grams)
        nin = len(case.gamma_inp[0])
        total = tuple(tuple(ZERO for _ in range(nin)) for _ in range(nin))
        for label, rows in case.port_map:
            block = _rows(case.gamma_inp, rows)
            recomputed = _mat_mul(_dagger(block), block)
            assert recomputed == grams[label], (case.case_id, label)
            total = _mat_add(total, recomputed)
        assert total == case.a_sigma, case.case_id
        identity = _identity(nin)
        assert _mat_add(identity, _mat_neg(total)) == case.deficiency, case.case_id


@pytest.mark.contract
def test_every_gram_is_hermitian_and_positive_semidefinite() -> None:
    """Theorem thm:port-grams (i), decided EXACTLY by Sylvester's criterion."""
    for case in INSTRUMENT_CASES:
        nin = len(case.gamma_inp[0])
        for label, gram in case.grams:
            assert _is_hermitian(gram), (case.case_id, label)
            assert _is_psd(gram), (case.case_id, label)
        assert _is_psd(case.a_sigma), case.case_id
        # sum_k A_k <= 1, and the deficiency is positive semidefinite.
        assert _loewner_leq(case.a_sigma, _identity(nin)), case.case_id
        assert _is_psd(case.deficiency), case.case_id


@pytest.mark.contract
def test_the_deficiency_identity_with_both_of_its_summands() -> None:
    """Eq. eq:deficiencyid, and the two frozen cases that separate the summands."""
    for case in INSTRUMENT_CASES:
        nin = len(case.gamma_inp[0])
        identity = _identity(nin)
        gtg = _mat_mul(_dagger(case.gamma_inp), case.gamma_inp)
        through_dilation = _mat_add(identity, _mat_neg(gtg))
        unmonitored_block = _rows(case.gamma_inp, case.unmonitored)
        if case.unmonitored:
            reached_unmonitored = _mat_mul(
                _dagger(unmonitored_block), unmonitored_block
            )
        else:
            reached_unmonitored = tuple(
                tuple(ZERO for _ in range(nin)) for _ in range(nin)
            )
        assert _mat_add(through_dilation, reached_unmonitored) == case.deficiency, (
            case.case_id
        )
        assert _is_psd(through_dilation), case.case_id
        assert _is_psd(reached_unmonitored), case.case_id
        # `lossless` is the ISOMETRY property of Gamma_Inp, NOT zero deficiency.
        assert (gtg == identity) is case.lossless, case.case_id
    # The pair that separates the two summands and the two properties.
    sub = next(c for c in INSTRUMENT_CASES if c.case_id == "I-DILATION-SUB")
    dil = next(c for c in INSTRUMENT_CASES if c.case_id == "I-DILATION-UNITARY")
    assert dict(sub.grams) == dict(dil.grams)
    assert sub.deficiency == dil.deficiency
    assert sub.lossless is False and dil.lossless is True
    assert sub.unmonitored == () and dil.unmonitored == (1,)


@pytest.mark.contract
def test_the_rank_bound_and_both_arguments_of_its_minimum() -> None:
    """Theorem thm:port-grams (ii): rk A_k <= min(|Inp|, |P_k|), both sides attained."""
    seen = set()
    for case in INSTRUMENT_CASES:
        nin = len(case.gamma_inp[0])
        ranks = dict(case.ranks)
        for label, rows in case.port_map:
            bound = min(nin, len(rows))
            assert ranks[label] <= bound, (case.case_id, label)
            if ranks[label] == bound:
                seen.add("inp" if nin <= len(rows) else "port")
            # The rank of a Gram is the rank of the matrix it is built from,
            # which is bounded by the number of rows AND by the number of
            # columns; checked here against the frozen block's own row count.
            assert ranks[label] <= len(rows), (case.case_id, label)
    assert seen == {"inp", "port"}
    # Theorem thm:representation-independence (iv): the one-mode-per-port criterion,
    # holding and failing.
    verdicts = {cid: (flag, rank) for cid, flag, rank, _ in ONE_MODE_PER_PORT_CASES}
    for cid, (flag, rank) in verdicts.items():
        case = next(c for c in INSTRUMENT_CASES if c.case_id == cid)
        assert max(dict(case.ranks).values()) == rank, cid
        assert (rank <= 1) is flag, cid
    assert {flag for flag, _ in verdicts.values()} == {True, False}
    # Corollary cor:extinction, with its dimension caveat recorded.
    assert {c[2] for c in EXTINCTION_CASES} == {True, False}
    caveat = next(c for c in EXTINCTION_CASES if c[0] == "EXT-DIM3-CAVEAT")
    assert caveat[3] == 2


# ---------------------------------------------------------------------------
#  7. RC6 and RC7 -- the click-pattern POVM and the coarse-graining
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_every_povm_block_is_psd_and_the_block_is_complete() -> None:
    """Theorem thm:click-povm (i), restricted to a photon-number sector."""
    for case in POVM_BLOCK_CASES:
        instrument = next(
            i for i in INSTRUMENT_CASES if i.case_id == case.instrument_case_id
        )
        modes = len(instrument.gamma_inp[0])
        assert case.basis_order == _occupations(modes, case.photon_number), case.case_id
        dim = _block_dimension(modes, case.photon_number)
        assert len(case.basis_order) == dim, case.case_id
        total = tuple(tuple(ZERO for _ in range(dim)) for _ in range(dim))
        for pattern, block in case.elements:
            assert len(block) == dim, (case.case_id, pattern)
            assert _is_hermitian(block), (case.case_id, pattern)
            assert _is_psd(block), (case.case_id, pattern)
            total = _mat_add(total, block)
        assert _is_hermitian(case.multiclick), case.case_id
        assert _is_psd(case.multiclick), case.case_id
        total = _mat_add(total, case.multiclick)
        # Completeness on the block, which is residual r_4 set to zero.
        assert total == _identity(dim), case.case_id
        # The elements are the SIX coarse letters: no-click, one per port, and
        # the multiclick aggregate.
        ports = [label for label, _ in instrument.port_map]
        assert [p for p, _ in case.elements] == [()] + [(p,) for p in ports], (
            case.case_id
        )


@pytest.mark.contract
def test_no_photon_no_click() -> None:
    """Theorem thm:click-povm (iii): blk M^{(=0)}_S = delta_{S, empty}."""
    zero_blocks = [c for c in POVM_BLOCK_CASES if c.photon_number == 0]
    assert zero_blocks
    for case in zero_blocks:
        elements = dict(case.elements)
        assert elements[()] == _identity(1), case.case_id
        for pattern, block in case.elements:
            if pattern:
                assert block == ((ZERO,),), (case.case_id, pattern)
        assert case.multiclick == ((ZERO,),), case.case_id


@pytest.mark.contract
def test_the_multiclick_block_dominates_its_bound() -> None:
    """Eq. eq:mcbound: blk M^{(=n)}_mc >= beta(n), with the slack visible."""
    strict = 0
    for case in POVM_BLOCK_CASES:
        dim = len(case.basis_order)
        floor = tuple(
            tuple(rt(case.beta_at_n) if i == j else ZERO for j in range(dim))
            for i in range(dim)
        )
        assert _loewner_leq(floor, case.multiclick), case.case_id
        # The frozen spectrum is consistent with the frozen block.
        assert len(case.multiclick_spectrum) == dim, case.case_id
        trace = _trace(case.multiclick)
        assert _is_real(trace), case.case_id
        assert trace[0] == q2(sum(case.multiclick_spectrum)), case.case_id
        assert min(case.multiclick_spectrum) >= case.beta_at_n, case.case_id
        if min(case.multiclick_spectrum) > case.beta_at_n:
            strict += 1
    # Remark rem:notsharp: the bound is NOT the eigenvalue, and at least one
    # frozen block shows the slack.
    assert strict >= 1


@pytest.mark.contract
def test_the_inclusion_exclusion_identities() -> None:
    """Eq. eq:recoverpivac: Pi_vac(J) is the sum over the patterns avoiding J."""
    blocks = {case.case_id: case for case in POVM_BLOCK_CASES}
    assert INCLUSION_EXCLUSION_CASES
    for case_id, block_id, avoided, pi_vac, patterns in INCLUSION_EXCLUSION_CASES:
        case = blocks[block_id]
        elements = dict(case.elements)
        dim = len(case.basis_order)
        total = tuple(tuple(ZERO for _ in range(dim)) for _ in range(dim))
        for pattern in patterns:
            assert set(pattern).isdisjoint(avoided), (case_id, pattern)
            total = _mat_add(total, elements[pattern])
        assert total == pi_vac, case_id


@pytest.mark.contract
def test_coarse_graining_fibres_partition_the_raw_alphabet() -> None:
    """Definition def:coarse: cg is a total surjection, so its fibres partition."""
    for case in COARSE_GRAINING_CASES:
        ports = case.port_labels
        expected = {
            tuple(sorted(s, key=ports.index))
            for size in range(len(ports) + 1)
            for s in itertools.combinations(ports, size)
        }
        seen: list[tuple[str, ...]] = []
        for _, patterns in case.fibres:
            seen += [tuple(sorted(p, key=ports.index)) for p in patterns]
        assert len(seen) == len(set(seen)), case.case_id
        assert set(seen) == expected, case.case_id
        assert len(expected) == 2 ** len(ports), case.case_id
        letters = {label for label, _ in case.fibres}
        assert letters == {label for _, label in case.alphabet}, case.case_id
        assert case.surjective is True, case.case_id
        # Stable IDs, and the labels are presentation metadata.
        ids = [i for i, _ in case.alphabet]
        assert len(set(ids)) == len(ids), case.case_id
    # The six-letter K = 4 instance of Remark req:declared-alphabet, and a SECOND
    # coarse-graining on the same ports, so the alphabet is visibly data.
    six = next(c for c in COARSE_GRAINING_CASES if c.case_id == "CG-SIX")
    assert six.alphabet == OUTCOME_ALPHABET
    others = [
        c
        for c in COARSE_GRAINING_CASES
        if c.port_labels == six.port_labels and c.case_id != "CG-SIX"
    ]
    assert others and any(c.alphabet != six.alphabet for c in others)
    # Theorem thm:coarse-graining (ii): the version-1 slot's outcome set is exactly the
    # fibre of `mc`, so the bound on the letter IS p_mc.
    for row in ADDITIVITY_CASES:
        case_id, block_id, outcome_set, bound, _letter, letter_bound = row
        assert bound == letter_bound, case_id
        block = next(c for c in POVM_BLOCK_CASES if c.case_id == block_id)
        assert min(block.multiclick_spectrum) >= bound, case_id
        assert all(len(s) >= 2 for s in outcome_set), case_id


# ---------------------------------------------------------------------------
#  8. RC8 -- the bound, the branch selector, and the unreachable predicate
# ---------------------------------------------------------------------------


def _beta(case: Any, photons: int) -> Fraction:
    """Eq. eq:beta at the frozen bound data, with the convention 0^0 = 1."""

    def power(base: Fraction) -> Fraction:
        return Fraction(1) if photons == 0 else base**photons

    return Fraction(
        1
        + (case.port_count - 1) * case.gamma * power(case.c)
        - sum(b * power(d) for b, d in zip(case.betas, case.ds, strict=True))
    )


@pytest.mark.contract
def test_bound_data_are_admissible_and_beta_is_the_frozen_value() -> None:
    """Definition def:bounddata Eq. eq:bounddata, and Eq. eq:beta."""
    for case in BOUND_DATA_CASES:
        assert case.port_count >= 1, case.case_id
        assert len(case.betas) == case.port_count, case.case_id
        assert len(case.ds) == case.port_count, case.case_id
        # 0 <= gamma <= beta_k <= 1 and 0 <= c <= d_k <= 1.
        assert 0 <= case.gamma <= 1, case.case_id
        assert all(case.gamma <= b <= 1 for b in case.betas), case.case_id
        assert 0 <= case.c <= 1, case.case_id
        assert all(case.c <= d <= 1 for d in case.ds), case.case_id
        for photons, value in case.beta_values:
            assert _beta(case, photons) == value, (case.case_id, photons)
        # Theorem thm:multiclick-bound's closing sentence: beta <= 1 everywhere.
        for photons in range(0, 6):
            assert _beta(case, photons) <= 1, (case.case_id, photons)


@pytest.mark.contract
def test_p_mc_is_the_value_the_declared_branch_produces() -> None:
    """Definition def:pmc Eq. eq:pmcdef, both branches, and Prop. prop:slotvalid."""
    for case in BOUND_DATA_CASES:
        cutoff = case.photon_cutoff
        if case.branch == "1":
            assert case.predicate == "X", case.case_id
            assert case.window is None, case.case_id
            assert case.p_mc == max(Fraction(0), _beta(case, cutoff + 1)), case.case_id
        else:
            assert case.branch in {"2", "lemma-only"}, case.case_id
            assert case.predicate is None, case.case_id
            window = case.window
            assert window is not None and window > cutoff, case.case_id
            minimum = min(_beta(case, n) for n in range(cutoff + 1, window + 1))
            tail = 1 - sum(
                b * d**window for b, d in zip(case.betas, case.ds, strict=True)
            )
            assert minimum == case.window_minimum, case.case_id
            assert tail == case.tail, case.case_id
            assert max(Fraction(0), minimum - tail) == case.residual_gap, case.case_id
            assert case.p_mc == max(Fraction(0), min(minimum, tail)), case.case_id
            # Lemma lem:windowtail (ii): the CLOSED FORM of the gap at m = N + 1.
            if window == cutoff + 1:
                closed = (case.port_count - 1) * case.gamma * case.c ** (cutoff + 1)
                assert case.residual_gap == closed, case.case_id
        # Proposition prop:slotvalid: p_mc in [0, 1].
        assert 0 <= case.p_mc <= 1, case.case_id
    # p_mc is ZERO at some configurations and POSITIVE at others, and the same
    # receiver gives both at different cutoffs.
    values = {c.case_id: c.p_mc for c in BOUND_DATA_CASES}
    assert values["BD-BB84-N1-ZERO"] == 0
    assert values["BD-BB84-N2"] == Fraction(1, 2)
    assert values["BD-BB84-N3"] == Fraction(3, 4)
    assert 0 in set(values.values()) and any(v > 0 for v in values.values())
    # Both clauses of predicate (X) are exercised, and branch 2 as well.
    branches = {c.branch for c in BOUND_DATA_CASES}
    assert branches == {"1", "2", "lemma-only"}


@pytest.mark.contract
def test_the_0_1_3_beta_zero_tuple_is_internally_consistent() -> None:
    """The 0.1.3 CR-4 evidence, unedited, re-checked against its own data.

    Its first three fields -- the case id, beta(0) and the slack -- are carried
    into COLLAPSE_SLACK_CASES unchanged. Its FOURTH field is "whether predicate
    (C) fires", and 0.2.0 deletes predicate (C), so the tuple is marked in
    SUPERSEDED_BY_0_2_0; what rem:noslack now states is asserted in
    ``test_the_collapse_slack_is_never_positive``.
    """
    assert is_superseded("BETA_ZERO_AND_C_SLACK")
    frozen = {
        cid: (b0, slack, fires) for cid, b0, slack, fires in BETA_ZERO_AND_C_SLACK
    }
    assert set(frozen) == {c.case_id for c in BOUND_DATA_CASES}
    for case in BOUND_DATA_CASES:
        b0 = _beta(case, 0)
        recorded_b0, slack, fires = frozen[case.case_id]
        assert recorded_b0 == b0, case.case_id
        assert slack == -b0, case.case_id
        assert b0 >= 0, case.case_id
        assert fires is False, case.case_id
    zeros = {cid for cid, (b0, _, _) in frozen.items() if b0 == 0}
    positives = {cid for cid, (b0, _, _) in frozen.items() if b0 > 0}
    assert zeros and positives
    for case in BOUND_DATA_CASES:
        if case.branch == "1":
            assert frozen[case.case_id][0] == 0, case.case_id


@pytest.mark.contract
def test_the_window_requirement_is_decidable_from_the_declaration() -> None:
    """Remark rem:windowdecidable, and the three distinct outcomes."""
    assert len(WINDOW_REQUIREMENT_CASES) == 4
    for _, predicate_x, required, outcome in WINDOW_REQUIREMENT_CASES:
        # Required at exactly the settings where (X) fails, and at no others.
        assert required is (not predicate_x)
        assert outcome.strip()
    unused = [
        row for row in WINDOW_REQUIREMENT_CASES if "UNUSED, NOT AN ERROR" in row[3]
    ]
    assert len(unused) == 2
    # Every branch-2 case declares a window strictly above the cutoff.
    for case in BOUND_DATA_CASES:
        if case.branch != "1":
            assert case.window is not None, case.case_id
            assert case.window > case.photon_cutoff, case.case_id
    # The strengthening slot: r = 1, the multiclick set, the minimum over T.
    record = dict(SLOT_RECORD)
    assert record["entry_count"] == "1"
    assert "MC_K" in record["outcome_set"]
    assert "MINIMUM" in record["weight"]


# ---------------------------------------------------------------------------
#  9. RC9 -- residuals, the norm question, and the fail-closed tier rule
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_0_1_3_residual_verdicts_hold_under_the_now_named_norm() -> None:
    """0.1.3 named no matrix norm and this registry froze both readings (OIC-3).

    0.2.0 names the SPECTRAL norm, which closes OIC-3 and changes NO value here:
    every failing residual was frozen with its spectral norm in
    ``value_spectral``. The second reading is no longer a reading of anything,
    and the one case where the two numbers differ is marked in
    SUPERSEDED_BY_0_2_0. This test keeps both assertions, because the verdicts
    hold under either and under the named one in particular.
    """
    assert RESIDUAL_NORM_0_2_0 == "spectral"
    seen = set()
    for case in RESIDUAL_CASES:
        assert case.residual_id in {"r_1", "r_2", "r_3", "r_4"}, case.case_id
        seen.add((case.residual_id, case.passes))
        bound = TOLERANCE_FIXTURE[case.tolerance_key]
        assert case.tolerance_key == f"eps_{case.residual_id[-1]}", case.case_id
        if case.passes:
            assert case.value_spectral == 0, case.case_id
            assert case.value_frobenius_squared == 0, case.case_id
            assert case.value_spectral <= bound, case.case_id
        else:
            assert case.value_spectral > bound, case.case_id
            assert case.value_frobenius_squared > bound, case.case_id
    # All four residuals, each passing AND failing.
    assert seen == {(f"r_{i}", flag) for i in range(1, 5) for flag in (True, False)}
    # The one case where the two readings genuinely differ numerically.
    differ = [
        c
        for c in RESIDUAL_CASES
        if c.value_spectral != 0 and c.value_spectral != c.value_frobenius_squared
    ]
    assert differ


@pytest.mark.contract
def test_the_tier_rule_is_fail_closed_on_every_route() -> None:
    """Theorem thm:exact-and-evaluated (iii)-(iv): NO path produces a `certified` label."""  # noqa: E501
    assert BOUND_EVALUATION_V1 == "floating_point"
    certified_requests = [row for row in TIER_CASES if row[2] == "certified"]
    assert len(certified_requests) == 3
    routes = {row[1] for row in certified_requests}
    assert routes == {
        f"({r}) {k}" for r, k in zip(("i", "ii", "iii"), INPUT_ROUTES, strict=True)
    }
    for _, _, _, answered, reason in certified_requests:
        assert answered == "estimate"
        assert reason == REFUSAL_REASONS_VERBATIM[0]
    estimate_request = next(row for row in TIER_CASES if row[2] == "estimate")
    assert estimate_request[3] == "estimate"
    assert estimate_request[4] is None
    # Remark rem:ia: the DIRECTION the deferred enclosures must round.
    directions = {name: way for name, way, _ in ENCLOSURE_DIRECTIONS}
    assert directions["lmax(B)"] == "UPPER enclosure"
    assert directions["lmin(B_k)"] == "LOWER enclosure"


# ---------------------------------------------------------------------------
#  10. RC10 -- efficiency, exactly once
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_uniform_efficiency_is_a_scalar_on_the_gram_and_preserves_rank() -> None:
    """Theorem thm:efficiency (i) Eq. eq:etagram, recomputed on the frozen Grams."""
    bb84 = next(c for c in INSTRUMENT_CASES if c.case_id == "I-BB84")
    grams = dict(bb84.grams)
    for case in EFFICIENCY_CASES:
        if not case.uniform_within_port:
            continue
        dim = len(bb84.gamma_inp[0])
        total = tuple(tuple(ZERO for _ in range(dim)) for _ in range(dim))
        for label, eta, before, after in case.ports:
            scaled = tuple(
                tuple(alg_mul(rt(eta), entry) for entry in row) for row in grams[label]
            )
            total = _mat_add(total, scaled)
            # eta_k > 0 preserves the rank.
            assert eta > 0, case.case_id
            assert before == after, (case.case_id, label)
        assert total == case.weighted_total, case.case_id
        # A multiple of A_Sigma only when the efficiencies agree.
        etas = {eta for _, eta, _, _ in case.ports}
        assert case.is_multiple_of_a_sigma is (len(etas) == 1), case.case_id
    # Non-uniform within a port: the rank CAN drop (Remark rem:effrank).
    drop = next(c for c in EFFICIENCY_CASES if not c.uniform_within_port)
    assert any(after < before for _, _, before, after in drop.ports)
    assert not drop.is_multiple_of_a_sigma


@pytest.mark.contract
def test_the_detector_layer_has_one_site_and_keeps_its_second_summand() -> None:
    """Definition def:compile's D_eta, and the trap of dropping E_unmonitored."""
    cases = {row[0]: row for row in D_ETA_CASES}
    unit = cases["DETA-UNIT"]
    assert unit[1] == (Fraction(1), Fraction(1))
    assert unit[2] == (Fraction(1), Fraction(1), Fraction(1))
    # D_eta = 1 at unit efficiency (thm:compilation-well-defined (iii)).
    assert unit[3] is True
    interior = cases["DETA-INTERIOR"]
    wrong = cases["DETA-WITHOUT-SECOND-SUMMAND"]
    assert interior[1] == wrong[1]
    # They differ ONLY on the unmonitored mode, and the wrong one zeroes it.
    assert interior[2][:2] == wrong[2][:2]
    assert interior[2][2] == Fraction(1) and wrong[2][2] == Fraction(0)
    # sqrt(eta_k) is the entry: 9/25 -> 3/5.
    assert interior[2][0] ** 2 == interior[1][0]
    # The composition record: every transmittance, and equal values as two rows.
    values = [value for value, _, _ in EFFICIENCY_RECORD]
    assert len(values) > len(set(values)), "no duplicated value to exercise (iv)"
    for value, element, site in EFFICIENCY_RECORD:
        assert 0 <= value <= 1
        assert element.strip()
        assert site.strip()
    elements = [element for _, element, _ in EFFICIENCY_RECORD]
    assert len(set(elements)) == len(elements)
    # The deficiency identity against a path-product audit that DISAGREES.
    for case_id, deficiency, audit, discrepancy, _ in PATH_PRODUCT_CASES:
        assert deficiency != audit, case_id
        assert audit - deficiency == discrepancy, case_id
    mz = next(c for c in INSTRUMENT_CASES if c.case_id == "I-MZ")
    assert mz.deficiency == ((ZERO, ZERO), (ZERO, ZERO))


# ---------------------------------------------------------------------------
#  11. RC11 -- dark counts
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_dark_channels_are_column_stochastic_and_carry_their_monotonicity() -> None:
    """Definition def:darkadm (D1) and (D2), on the frozen columns."""
    for case in DARK_CASES:
        columns = dict(case.columns)
        assert set(columns) == set(_subsets(case.port_count)), case.case_id
        for source, entries in case.columns:
            # (D1): non-negative and summing to one, EXACTLY.
            assert all(value >= 0 for _, value in entries), (case.case_id, source)
            assert sum(value for _, value in entries) == 1, (case.case_id, source)
            assert len({row for row, _ in entries}) == len(entries), case.case_id
        # (D2): every non-zero entry has S' contained in S.
        monotone = all(
            set(source) <= set(row)
            for source, entries in case.columns
            for row, value in entries
            if value > 0
        )
        assert monotone is case.monotone, case.case_id
        assert case.column_stochastic is True, case.case_id
        # Eq. eq:darkR where the product form generated the channel.
        if case.p_dc is not None:
            for source, entries in case.columns:
                frozen = dict(entries)
                for row in _subsets(case.port_count):
                    expected = Fraction(0)
                    if set(source) <= set(row):
                        expected = Fraction(1)
                        for k in set(row) - set(source):
                            expected *= case.p_dc[k]
                        for k in range(case.port_count):
                            if k not in row:
                                expected *= 1 - case.p_dc[k]
                    assert frozen.get(row, Fraction(0)) == expected, (
                        case.case_id,
                        source,
                        row,
                    )


@pytest.mark.contract
def test_r_min_runs_over_the_no_click_column_too() -> None:
    """Eq. eq:rmin and Remark rem:rmintrap, the named trap."""
    for case in DARK_CASES:
        masses = dict(case.mc_mass)
        for source, entries in case.columns:
            assert masses[source] == sum(
                value for row, value in entries if len(row) >= 2
            ), (case.case_id, source)
        non_multiclick = [s for s in _subsets(case.port_count) if len(s) < 2]
        if not case.monotone:
            # A refused channel emits no r_min, and absorption FAILS.
            assert case.r_min_without_noclick is None, case.case_id
            assert any(
                masses[s] != 1 for s in _subsets(case.port_count) if len(s) >= 2
            ), case.case_id
            continue
        # Theorem thm:dark-counts (iii): multiclick absorption.
        for source in _subsets(case.port_count):
            if len(source) >= 2:
                assert masses[source] == 1, (case.case_id, source)
        assert case.r_min == min(masses[s] for s in non_multiclick), case.case_id
        # THE TRAP: the minimum sits on the NO-CLICK column, and the
        # single-click-only minimum is strictly larger and would be invalid.
        assert case.r_min == masses[()], case.case_id
        assert case.r_min_without_noclick == min(
            masses[s] for s in non_multiclick if len(s) == 1
        ), case.case_id
        assert case.r_min < case.r_min_without_noclick, case.case_id
    # Eq. eq:rmintrapnum's own numbers at K = 4.
    for case_id, ports, p, no_click, single, r_min, wrong in RMIN_TRAP_CASES:
        assert no_click == 1 - (1 - p) ** ports - ports * p * (1 - p) ** (ports - 1)
        assert single == 1 - (1 - p) ** (ports - 1)
        assert (r_min, wrong) == (no_click, single), case_id
        assert r_min < wrong, case_id
    # Theorem thm:dark-counts (iv): the bound improves, and never worsens.
    for case_id, r_min, p_mc, improved in DARK_IMPROVEMENT_CASES:
        assert improved == (1 - r_min) * p_mc + r_min, case_id
        assert improved >= p_mc, case_id
        assert improved - p_mc == r_min * (1 - p_mc), case_id


@pytest.mark.contract
def test_the_dark_composition_preserves_the_povm_on_a_block() -> None:
    """Theorem thm:dark-counts (ii), on I-BS's two-photon block with DARK-K2."""
    block = next(c for c in POVM_BLOCK_CASES if c.case_id == "PB-BS-n2")
    instrument = next(c for c in INSTRUMENT_CASES if c.case_id == "I-BS")
    labels = [label for label, _ in instrument.port_map]
    bare: dict[tuple[int, ...], Fraction] = {}
    for pattern, matrix in block.elements:
        key = tuple(sorted(labels.index(p) for p in pattern))
        assert _is_real(matrix[0][0])
        bare[key] = matrix[0][0][0][0]
    assert _is_real(block.multiclick[0][0])
    bare[(0, 1)] = block.multiclick[0][0][0][0]
    channel = next(c for c in DARK_CASES if c.case_id == "DARK-K2")
    columns = dict(channel.columns)
    composed = {}
    for row in _subsets(2):
        composed[row] = sum(
            dict(columns[source]).get(row, Fraction(0)) * bare[source]
            for source in _subsets(2)
        )
    assert dict(DARK_COMPOSITION_N2) == composed
    # STILL A POVM on the block.
    assert sum(composed.values()) == 1
    assert all(value >= 0 for value in composed.values())


# ---------------------------------------------------------------------------
#  12. RC12 -- probe conditioning
# ---------------------------------------------------------------------------


def _frac(value: Alg) -> Fraction:
    assert _is_real(value), value
    assert value[0][1] == 0, value
    return value[0][0]


@pytest.mark.contract
def test_the_schur_prefactor_and_effective_gram_are_the_frozen_values() -> None:
    """Eq. eq:schur, recomputed from the frozen Grams at one probe mode."""
    for case in PROBE_CASES:
        assert len(case.channel_modes) == 1 and len(case.probe_modes) == 1
        grams = dict(case.grams)
        nbar = case.gamma_diagonal[0]
        for ports, prefactor, effective in case.conditioned:
            block = tuple(
                tuple(
                    sum((_frac(grams[p][i][j]) for p in ports), Fraction(0))
                    for j in range(2)
                )
                for i in range(2)
            )
            a_cc, a_cs, a_sc, a_ss = block[0][0], block[0][1], block[1][0], block[1][1]
            # c(A, Gamma) = 1 / det(1 + Gamma A_LedLed), one probe mode.
            assert prefactor == Fraction(1) / (1 + nbar * a_ss), (case.case_id, ports)
            # Theorem thm:gaussian-schur (i): the prefactor lies in (0, 1].
            assert 0 < prefactor <= 1, (case.case_id, ports)
            if nbar == 0:
                expected = a_cc
            else:
                inverse = Fraction(1) / (Fraction(1) / nbar + a_ss)
                expected = a_cc - a_cs * inverse * a_sc
            assert _frac(effective[0][0]) == expected, (case.case_id, ports)
            # 0 <= A^eff <= A_ChanChan <= 1.
            assert 0 <= expected <= a_cc <= 1, (case.case_id, ports)
        by_ports = {tuple(p): (g, _frac(e[0][0])) for p, g, e in case.conditioned}
        gamma, b_total = by_ports[("1", "2")]
        beta_1, b_1 = by_ports[("2",)]
        beta_2, b_2 = by_ports[("1",)]
        # Theorem thm:gaussian-schur (iv): gamma <= beta_k.
        assert gamma <= beta_1 and gamma <= beta_2, case.case_id
        # Lemma lem:schurmono: 0 <= B_k <= B <= 1, which is Eq. eq:bbkhyp.
        assert 0 <= b_1 <= b_total <= 1, case.case_id
        assert 0 <= b_2 <= b_total <= 1, case.case_id
        # Remark rem:condpair: the Schur map is NOT additive in the port set.
        if case.gamma_diagonal[0] > 0:
            assert b_1 + b_2 != b_total, case.case_id
        # Eq. eq:cd feeds the bound data of the paired RC8 case.
        bound = next(
            b for b in BOUND_DATA_CASES if b.case_id == case.bound_data_case_id
        )
        assert bound.c == 1 - b_total, case.case_id
        assert set(bound.ds) == {1 - b_1, 1 - b_2}, case.case_id
        assert bound.gamma == gamma, case.case_id
        assert set(bound.betas) == {beta_1, beta_2}, case.case_id
    # The vacuum setting reproduces the UNCONDITIONED channel blocks exactly.
    vacuum = next(c for c in PROBE_CASES if c.gamma_diagonal == (Fraction(0),))
    grams = dict(vacuum.grams)
    for ports, prefactor, effective in vacuum.conditioned:
        assert prefactor == 1
        channel_block = sum((_frac(grams[p][0][0]) for p in ports), Fraction(0))
        assert _frac(effective[0][0]) == channel_block


@pytest.mark.contract
def test_the_conditional_family_is_complete_at_each_fixed_setting() -> None:
    """Theorem thm:conditional-povm (ii), via Eq. eq:condmc on the frozen data."""
    probes = {case.case_id: case for case in PROBE_CASES}
    for case_id, probe_id, photons, elements, total in CONDITIONAL_COMPLETENESS_CASES:
        case = probes[probe_id]
        by_ports = {tuple(p): (g, _frac(e[0][0])) for p, g, e in case.conditioned}
        gamma, b_total = by_ports[("1", "2")]
        beta_1, b_1 = by_ports[("2",)]
        beta_2, b_2 = by_ports[("1",)]
        frozen = dict(elements)
        no_click = gamma * (1 - b_total) ** photons
        assert frozen[()] == no_click, case_id
        assert frozen[("1",)] == beta_1 * (1 - b_1) ** photons - no_click, case_id
        assert frozen[("2",)] == beta_2 * (1 - b_2) ** photons - no_click, case_id
        multiclick = (
            1 + no_click - beta_1 * (1 - b_1) ** photons - beta_2 * (1 - b_2) ** photons
        )
        assert frozen[("1", "2")] == multiclick, case_id
        # Complete FOR EACH FIXED t, and every element non-negative.
        assert sum(frozen.values()) == total == 1, case_id
        assert all(value >= 0 for value in frozen.values()), case_id
    # The Gaussian tier is occupation-diagonal BY CONSTRUCTION.
    for occupation, weight in THERMAL_OCCUPATION_WEIGHTS:
        assert weight == Fraction(1) ** occupation / Fraction(2) ** (occupation + 1)
    assert all(w > 0 for _, w in THERMAL_OCCUPATION_WEIGHTS)


# ---------------------------------------------------------------------------
#  13. The interface: refusals, precedence, representation
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_representation_cases_relate_their_grams_to_their_matrices() -> None:
    """Theorem thm:representation-independence (i) and (iii), recomputed by Eq. eq:gramdef."""  # noqa: E501
    for case in REPRESENTATION_INDEPENDENCE_CASES:
        for matrix, ports, grams in (
            (case.gamma_a, case.port_map_a, case.grams_a),
            (case.gamma_b, case.port_map_b, case.grams_b),
        ):
            assert len(ports) == len(grams), case.case_id
            for index, rows in enumerate(ports):
                block = _rows(matrix, rows)
                assert _mat_mul(_dagger(block), block) == grams[index], (
                    case.case_id,
                    index,
                )
        same_matrix = case.gamma_a == case.gamma_b
        assert same_matrix is case.matrices_equal, case.case_id
        same_grams = tuple(case.grams_a) == tuple(case.grams_b)
        assert same_grams is case.grams_equal, case.case_id
    # The pair that separates the covered and uncovered halves of rem:bsconv.
    covered = next(
        c
        for c in REPRESENTATION_INDEPENDENCE_CASES
        if c.case_id.endswith("OUTPUT-PHASE")
    )
    uncovered = next(
        c for c in REPRESENTATION_INDEPENDENCE_CASES if c.case_id.endswith("SYMMETRIC")
    )
    assert covered.gamma_a == uncovered.gamma_a
    assert covered.grams_equal is True and uncovered.grams_equal is False
    # And a case where two matrices of DIFFERENT SHAPES share one Gram family.
    realize = next(
        c for c in REPRESENTATION_INDEPENDENCE_CASES if c.case_id == "REP-REALIZE-RANK2"
    )
    assert len(realize.gamma_a) != len(realize.gamma_b)
    assert realize.grams_equal is True


def _mode_sort_key(label: tuple[str, str, int]) -> tuple[str, int, bool]:
    """Definition def:modes: lexicographic in (path, tau, polarization).

    The KEY is (p, tau, pi), which is NOT the order the label components are
    written in, and H sorts before V.
    """
    return (label[0], label[2], label[1] == "V")


@pytest.mark.contract
def test_the_subsystem_order_takes_precedence_over_the_mode_listing() -> None:
    """Section 2.5 `subsystem_order`, in both directions."""
    assert len(MODE_ORDER_CASES) == 2
    for case in MODE_ORDER_CASES:
        count = len(case.labels)
        assert sorted(case.mode_space_order) == list(range(count)), case.case_id
        assert sorted(case.input_index_order) == list(range(count)), case.case_id
        disagree = case.mode_space_order != case.input_index_order
        assert disagree is case.orders_disagree, case.case_id
        # Definition def:modes sorts on (path, tau, polarization), H before V.
        assert list(case.labels) == sorted(case.labels, key=_mode_sort_key), (
            case.case_id
        )
    assert {c.orders_disagree for c in MODE_ORDER_CASES} == {True, False}
    # The disagreeing case is the one where a probe path label sorts first.
    disagreeing = next(c for c in MODE_ORDER_CASES if c.orders_disagree)
    assert disagreeing.input_index_order[0] != 0


@pytest.mark.contract
def test_refusals_name_a_condition_and_only_one_spells_a_reason() -> None:
    """Section 2.5 `fail_closed`, and the spelling trap."""
    ids = [case.case_id for case in REFUSAL_CASES]
    assert len(set(ids)) == len(ids)
    verbatim = [case for case in REFUSAL_CASES if case.reason_is_verbatim]
    assert len(verbatim) == 1
    assert verbatim[0].reason == REFUSAL_REASONS_VERBATIM[0]
    for case in REFUSAL_CASES:
        assert case.failing_condition.strip(), case.case_id
        assert case.subject.strip(), case.case_id
        assert len(case.derives_from) > 120, case.case_id
        if not case.reason_is_verbatim:
            # Any reason carried is the contract's PROSE, never a machine key.
            assert case.reason is None or " " in case.reason, case.case_id
            assert case.reason != REFUSAL_REASONS_VERBATIM[0], case.case_id
    conditions = {case.failing_condition for case in REFUSAL_CASES}
    for named in ("(E1)", "(E2)", "(E3)", "(D2)"):
        assert named in conditions, named
    # The interface-level refusals the band asked for, all present.
    required = {
        "REF-TWO-ROUTES",
        "REF-NONZERO-TOLERANCE",
        "REF-OUT-OF-DOMAIN-NOT-CLIPPED",
    }
    assert required <= set(ids)
    tolerance_case = next(
        c for c in REFUSAL_CASES if c.case_id == "REF-NONZERO-TOLERANCE"
    )
    assert tolerance_case.reason == "parameter uncertainty sets are out of scope"


# ---------------------------------------------------------------------------
#  14. THE 0.2.0 AMENDMENT
#
#  Everything below pins the delta between 0.1.3 and 0.2.0. The 0.1.3 sections
#  above are unchanged except where a statement they made about the CONTRACT
#  ceased to be true of it; those places are marked in the docstring of each
#  test and in SUPERSEDED_BY_0_2_0.
# ---------------------------------------------------------------------------


def _herm_part(block: Mat) -> Mat:
    """(X + X^dagger) / 2, exactly."""
    half = alg(q2(Fraction(1, 2)))
    return tuple(
        tuple(
            alg_mul(half, alg_add(block[i][j], alg_conj(block[j][i])))
            for j in range(len(block))
        )
        for i in range(len(block))
    )


def _skew_part(block: Mat) -> Mat:
    """X - X^dagger, exactly."""
    return tuple(
        tuple(
            alg_add(block[i][j], _neg(alg_conj(block[j][i]))) for j in range(len(block))
        )
        for i in range(len(block))
    )


def _neg(value: Alg) -> Alg:
    return (q2_neg(value[0]), q2_neg(value[1]))


def _shift(block: Mat, amount: Fraction) -> Mat:
    """Block + amount * identity, exactly."""
    n = len(block)
    return tuple(
        tuple(
            alg_add(block[i][j], alg(q2(amount))) if i == j else block[i][j]
            for j in range(n)
        )
        for i in range(n)
    )


def _expectation(block: Mat, psi: tuple[Alg, ...]) -> Alg:
    """<psi|X|psi>, exactly."""
    total = ZERO
    for j, left in enumerate(psi):
        for k, right in enumerate(psi):
            total = alg_add(total, alg_mul(alg_conj(left), alg_mul(block[j][k], right)))
    return total


@pytest.mark.contract
def test_the_interface_conventions_are_the_seventeen_bullets() -> None:
    """Section 2.5 gained `numerical_tolerance_assignment`; nothing else moved."""
    conventions = _interface()["conventions"]
    assert len(CONVENTION_KEYS_0_2_0) == 17
    # 0.3.0 adds no bullet and removes none: the seventeen are the same
    # seventeen, and CONVENTION_KEYS_0_3_0 asserts the identity rather than
    # restating the list.
    assert CONVENTION_KEYS_0_3_0 == CONVENTION_KEYS_0_2_0
    assert not is_superseded_0_3_0("CONVENTION_KEYS_0_2_0")
    for key in CONVENTION_KEYS_0_2_0:
        assert key in conventions, key
    # Exactly one bullet is new, and the sixteen 0.1.3 names are a prefix-set.
    added = set(CONVENTION_KEYS_0_2_0) - set(CONVENTION_KEYS)
    assert added == {"numerical_tolerance_assignment"}
    assert not set(CONVENTION_KEYS) - set(CONVENTION_KEYS_0_2_0)
    # Its position is between `numerics` and `fail_closed`.
    order = list(CONVENTION_KEYS_0_2_0)
    assert order.index("numerics") + 1 == order.index("numerical_tolerance_assignment")
    assert order.index("numerical_tolerance_assignment") + 1 == order.index(
        "fail_closed"
    )
    # The bullet names every deciding tolerance, and the map agrees with
    # TOLMAP_ITEMS on which tolerance decides which item.
    mapping = conventions["numerical_tolerance_assignment_map"]
    assert set(mapping) == {
        "eps_1",
        "eps_2",
        "eps_3",
        "eps_4",
        "eps_5",
        "eps_6",
        "eps_gap",
        "eps_eig",
    }
    assert set(mapping) == set(TOLERANCE_FIXTURE_0_3_0)
    deciding = {key for key, value in mapping.items() if value["decides"]}
    assert deciding == {"eps_1", "eps_2", "eps_4"}
    # eps_eig is the ONE member that neither decides nor bounds: it is
    # SUBTRACTED (Def. def:tolmap's preamble and closing enumeration).
    for key, value in mapping.items():
        if key == "eps_eig":
            assert value["bounds"] is None
            assert value["decides"] is None
            assert value["note"].strip()
        else:
            assert value["bounds"], key
    assert {name for name, _ in TOLMAP_NOT_A_TEST_0_3_0} == {"eps_eig", "eps_6"}
    # The eps_2 entry carries the 0.3.0 ruling: item (iv) decides c ALONE.
    assert "ALONE" in mapping["eps_2"]["decides"]
    assert "REFUSED" in mapping["eps_2"]["decides"]


@pytest.mark.contract
def test_the_interface_refusal_table_is_the_frozen_vocabulary() -> None:
    """Section 2.6 at 0.3.0: EIGHT spelled refusals, one spelled fallback.

    And the 0.7.0 amendment, through its named delta: the ninth refusal
    follows the frozen eight, in the table and in the vocabulary, the tier
    fallback last.
    """
    refusals = _interface()["refusals"]
    assert (
        tuple(refusals["reason_strings_verbatim"])
        == REFUSAL_REASONS_VERBATIM_0_3_0 + REFUSAL_REASONS_ADDED_AT_0_7_0
    )
    assert len(REFUSAL_REASONS_VERBATIM_0_3_0) == 8
    assert refusals["tier_fallback"]["reason"] == TIER_FALLBACK_REASON_VERBATIM
    assert refusals["tier_fallback"]["emits_artifact"] is True
    assert (
        tuple(refusals["reason_vocabulary"])
        == REASON_VOCABULARY_0_3_0[:8]
        + REFUSAL_REASONS_ADDED_AT_0_7_0
        + REASON_VOCABULARY_0_3_0[8:]
    )
    assert len(REASON_VOCABULARY_0_3_0) == 9
    # The five 0.2.0 reasons are a PREFIX of the eight, character for
    # character, and the three added are the exact window's.
    assert REFUSAL_REASONS_VERBATIM_0_3_0[:5] == REFUSAL_REASONS_VERBATIM_0_2_0
    assert REFUSAL_REASONS_VERBATIM_0_3_0[5:] == REFUSAL_REASONS_ADDED_AT_0_3_0
    assert len(REFUSAL_REASONS_ADDED_AT_0_3_0) == 3
    assert is_superseded_0_3_0("REFUSAL_REASONS_VERBATIM_0_2_0")
    assert is_superseded_0_3_0("REASON_VOCABULARY_0_2_0")
    # The table's rows carry the eight, then the 0.7.0 one, in order, and none
    # emits an artifact.
    rows = refusals["table"]
    assert (
        tuple(row["reason"] for row in rows)
        == REFUSAL_REASONS_VERBATIM_0_3_0 + REFUSAL_REASONS_ADDED_AT_0_7_0
    )
    for row in rows:
        assert row["emits_artifact"] is False, row["reason"]
        assert row["condition"].strip()
        assert row["stated_at"].strip()
    assert {row["reason"] for row in rows if row.get("new_at") == "0.3.0"} == set(
        REFUSAL_REASONS_ADDED_AT_0_3_0
    )
    assert {row["reason"] for row in rows if row.get("new_at") == "0.7.0"} == set(
        REFUSAL_REASONS_ADDED_AT_0_7_0
    )
    assert dict(REASON_EMITS_ARTIFACT_0_3_0) == {
        **dict.fromkeys(REFUSAL_REASONS_VERBATIM_0_3_0, False),
        TIER_FALLBACK_REASON_VERBATIM: True,
    }
    # SEVEN sites are named WITHOUT a spelling at 0.3.0, and they carry no key.
    unspelled = refusals["named_without_a_spelling"]
    assert len(unspelled) == len(REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0) == 7
    assert REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0[:6] == (
        REFUSALS_NAMED_WITHOUT_A_SPELLING
    )
    assert is_superseded_0_3_0("REFUSALS_NAMED_WITHOUT_A_SPELLING")
    for row in unspelled:
        assert "reason" not in row, row["condition"]
        assert row["stated_at"].strip()
    # The seventh is Def. def:tolmap (iv)'s, and the interface says in terms
    # that the contract declines to spell it rather than that it forgot.
    seventh = unspelled[6]
    assert seventh["new_at"] == "0.3.0"
    assert "def:tolmap (iv)" in seventh["stated_at"]
    assert "DELIBERATELY ADDS NONE" in seventh["no_string_deliberately"]
    # The earlier vocabularies are SUBSETS and are marked, never edited.
    assert set(REFUSAL_REASONS_VERBATIM) <= set(REASON_VOCABULARY_0_3_0)
    assert set(REASON_VOCABULARY_0_2_0) <= set(REASON_VOCABULARY_0_3_0)
    assert is_superseded("REFUSAL_REASONS_VERBATIM")


@pytest.mark.contract
def test_every_verbatim_reason_a_case_names_is_in_the_vocabulary() -> None:
    """No frozen case invents a seventh spelling."""
    named: set[str] = set()
    for case in REFUSAL_CASES_0_2_0:
        if case.reason_is_verbatim:
            assert case.reason is not None, case.case_id
            named.add(case.reason)
        else:
            # An unspelled refusal carries the contract's PROSE or nothing.
            assert case.reason is None or " " in case.reason, case.case_id
        assert case.failing_condition.strip(), case.case_id
        assert len(case.derives_from) > 200, case.case_id
    for case in REFUSAL_CASES_0_3_0:
        if case.reason_is_verbatim:
            assert case.reason is not None, case.case_id
            named.add(case.reason)
        else:
            assert case.reason is None, case.case_id
        assert case.failing_condition.strip(), case.case_id
        assert len(case.derives_from) > 200, case.case_id
    assert named == set(REASON_VOCABULARY_0_3_0)
    for res6_case in RESIDUAL6_CASES:
        if res6_case.refusal_reason is not None:
            assert res6_case.refusal_reason in REASON_VOCABULARY_0_3_0, (
                res6_case.case_id
            )
    for xw_case in EXACT_WINDOW_VALIDATION_CASES:
        if xw_case.refusal_reason is not None:
            assert xw_case.refusal_reason in REASON_VOCABULARY_0_3_0, xw_case.case_id
    # Def. def:tolmap (iv)'s refusal carries NO key, deliberately.
    for band_case in TOLMAP_IV_PRECEDENCE_CASES:
        assert band_case.refusal_reason is None, band_case.case_id
    for res5_case in RESIDUAL5_CASES:
        if res5_case.refusal_reason is not None:
            assert res5_case.refusal_reason in REASON_VOCABULARY_0_2_0, (
                res5_case.case_id
            )
    for domain_case in TOLERANCE_DOMAIN_CASES:
        if domain_case.refusal_reason is not None:
            assert domain_case.refusal_reason in REASON_VOCABULARY_0_2_0, (
                domain_case.case_id
            )
    for tolmap_case in (
        *TOLMAP_I_CASES,
        *TOLMAP_II_RANK_CASES,
        *TOLMAP_IV_C_CASES,
        *TOLMAP_V_CONTRACTIVITY_CASES,
    ):
        if tolmap_case.refusal_reason is not None:
            assert tolmap_case.refusal_reason in REASON_VOCABULARY_0_2_0
    for _, _, _, _, _, reason in DARK_ROUTE_EXCLUSIVITY_CASES:
        if reason is not None:
            assert reason in REASON_VOCABULARY_0_2_0
    # Exactly ONE frozen case emits an artifact: the tier fallback, and it is
    # in the 0.2.0 table. Not one 0.3.0 case emits one -- all four are
    # refusals under `fail_closed`.
    emitting = [
        case
        for case in (*REFUSAL_CASES_0_2_0, *REFUSAL_CASES_0_3_0)
        if case.emits_artifact
    ]
    assert len(emitting) == 1
    assert emitting[0].reason == TIER_FALLBACK_REASON_VERBATIM


@pytest.mark.contract
def test_the_0_2_0_tolerance_fixture_is_the_declared_tuple() -> None:
    """Section 2.1: six members, eps_5 in and eps_hyp out, each in [0, 1)."""
    assert set(TOLERANCE_FIXTURE_0_2_0) == {
        "eps_1",
        "eps_2",
        "eps_3",
        "eps_4",
        "eps_5",
        "eps_gap",
    }
    assert len(TOLERANCE_FIXTURE_0_2_0) == 6 == len(TOLERANCE_FIXTURE)
    assert "eps_hyp" not in TOLERANCE_FIXTURE_0_2_0
    assert "eps_5" not in TOLERANCE_FIXTURE
    low, high = TOLERANCE_DOMAIN
    assert (low, high) == (Fraction(0), Fraction(1))
    assert TOLERANCE_DOMAIN_CLOSED_AT == (True, False)
    for key, value in TOLERANCE_FIXTURE_0_2_0.items():
        assert isinstance(value, Fraction), key
        assert low <= value < high, key
    # The interface's own row describes the 0.3.0 tuple, which has EIGHT
    # members; the six above are still a subset of it and still required on
    # every declaration. The 0.2.0 fixture is marked, never edited.
    assert is_superseded_0_3_0("TOLERANCE_FIXTURE_0_2_0")
    assert set(TOLERANCE_FIXTURE_0_2_0) < set(TOLERANCE_FIXTURE_0_3_0)
    row = next(r for r in _interface()["inputs"] if r["name"] == "numerical_tolerances")
    assert row["arity"] == 8
    assert tuple(row["members"]) == tuple(TOLERANCE_FIXTURE_0_3_0)
    assert row["declared_domain"] == "[0, 1)"
    assert row["never_defaulted"] is True
    assert row["domain_refusal_reason"] == "tolerance_outside_declared_domain"


@pytest.mark.contract
def test_the_tolerance_domain_admits_zero_and_refuses_one() -> None:
    """Rem. rem:tolerancedomain: [0, 1), half-open, both ends frozen."""
    low, high = TOLERANCE_DOMAIN
    seen_admitted = seen_refused = 0
    for case in TOLERANCE_DOMAIN_CASES:
        inside = low <= case.value < high
        assert case.admitted is inside, case.case_id
        if case.admitted:
            assert case.refusal_reason is None, case.case_id
            seen_admitted += 1
        else:
            assert case.refusal_reason == "tolerance_outside_declared_domain"
            seen_refused += 1
        assert case.key in TOLERANCE_FIXTURE_0_2_0, case.case_id
        assert len(case.derives_from) > 120, case.case_id
    assert seen_admitted >= 3 and seen_refused >= 3
    # BOTH ENDPOINTS ARE PRESENT, which is the whole point of a half-open
    # interval: 0 is admitted and 1 is refused.
    values = {case.value: case.admitted for case in TOLERANCE_DOMAIN_CASES}
    assert values[Fraction(0)] is True
    assert values[Fraction(1)] is False
    # And a value on each side of the interval is refused.
    assert any(case.value < 0 and not case.admitted for case in TOLERANCE_DOMAIN_CASES)
    assert any(case.value > 1 and not case.admitted for case in TOLERANCE_DOMAIN_CASES)
    # The five degeneracies the remark names, one per def:tolmap item.
    assert len(TOLERANCE_DOMAIN_DEGENERACIES) == 5
    assert {item for item, _ in TOLERANCE_DOMAIN_DEGENERACIES} == {
        item for item, _, _ in TOLMAP_ITEMS
    }
    assert len(TOLERANCE_UPPER_BOUND_CONSUMERS) == 2


@pytest.mark.contract
def test_rho_is_the_maximum_of_its_two_defects() -> None:
    """Eq. eq:rhodef and Prop. prop:res5 (i), (ii), (iv), in exact arithmetic.

    The two defects are checked WITHOUT an eigenvalue routine: the skew part's
    spectral norm is pinned by ``S^dagger S = d^2 I`` and the negativity by
    ``H + n I`` being PSD while ``H + (n - delta) I`` is not.
    """
    for case in RESIDUAL5_CASES:
        skew = _skew_part(case.block)
        herm = _herm_part(case.block)
        n = len(case.block)
        zero = tuple(tuple(ZERO for _ in range(n)) for _ in range(n))
        # Hermiticity defect.
        assert _is_hermitian(case.block) is case.hermitian, case.case_id
        if case.hermitian:
            assert skew == zero, case.case_id
            assert case.hermiticity_defect == 0, case.case_id
        else:
            assert skew != zero, case.case_id
            assert case.hermiticity_defect > 0, case.case_id
            gram = _mat_mul(_dagger(skew), skew)
            scaled = tuple(
                tuple(
                    alg(q2(case.hermiticity_defect**2)) if i == j else ZERO
                    for j in range(n)
                )
                for i in range(n)
            )
            assert gram == scaled, case.case_id
        # Negativity defect: H + n I is PSD and one notch less is not.
        assert case.negativity_defect >= 0, case.case_id
        assert _is_psd(_shift(herm, case.negativity_defect)), case.case_id
        if case.negativity_defect > 0:
            notch = case.negativity_defect / 2
            assert not _is_psd(_shift(herm, notch)), case.case_id
        else:
            assert _is_psd(herm), case.case_id
        # The maximum, the verdict, and the reason.
        assert case.rho == max(case.hermiticity_defect, case.negativity_defect)
        bound = TOLERANCE_FIXTURE_0_2_0[case.tolerance_key]
        assert case.tolerance_key == "eps_5", case.case_id
        assert case.passes is (case.rho <= bound), case.case_id
        if case.passes:
            # Prop. prop:res5 (i) and (iv): an emitted block has rho = 0
            # EXACTLY, being a compression of a positive operator.
            assert case.rho == 0, case.case_id
            assert case.hermitian, case.case_id
            assert _is_psd(case.block), case.case_id
            assert case.refusal_reason is None, case.case_id
        else:
            assert case.rho > bound, case.case_id
            assert (
                case.refusal_reason
                == "photon_block_positivity_residual_above_tolerance"
            ), case.case_id
    # Prop. prop:res5 (ii): on a Hermitian block rho IS the eq:res2 form.
    hermitian_failures = [
        case for case in RESIDUAL5_CASES if case.hermitian and not case.passes
    ]
    assert hermitian_failures
    for case in hermitian_failures:
        assert case.hermiticity_defect == 0, case.case_id
        assert case.rho == case.negativity_defect, case.case_id
    # Both kinds of defect are exercised, separately.
    assert any(
        c.hermiticity_defect > 0 and c.negativity_defect == 0 for c in RESIDUAL5_CASES
    )
    assert any(
        c.negativity_defect > 0 and c.hermiticity_defect == 0 for c in RESIDUAL5_CASES
    )
    assert sum(1 for c in RESIDUAL5_CASES if c.passes) >= 2
    # The norm is NAMED at 0.2.0; OIC-3 is closed.
    assert RESIDUAL_NORM_0_2_0 == "spectral"
    assert (
        _interface()["outputs"][
            [row["name"] for row in _interface()["outputs"]].index("validation_results")
        ]["residual_norm"]
        == RESIDUAL_NORM_0_2_0
    )


@pytest.mark.contract
def test_the_expectation_bounds_of_prop_res5_iii_are_attained() -> None:
    """Re <psi|X|psi> >= -rho and |Im <psi|X|psi>| <= rho/2, both tight."""
    blocks = {case.case_id: case for case in RESIDUAL5_CASES}
    vectors: dict[str, tuple[Alg, ...]] = {
        "psi = (1, 0)": (rt(1), ZERO),
        "psi = (1, i)/sqrt2": (rt(0, Fraction(1, 2)), im_(0, Fraction(1, 2))),
        "psi = (0, 1)": (ZERO, rt(1)),
    }
    tight = set()
    for (
        case_id,
        description,
        re_part,
        im_part,
        neg_rho,
        half_rho,
        which,
    ) in RES5_EXPECTATION_CASES:
        case = blocks[case_id]
        assert neg_rho == -case.rho, case_id
        assert half_rho == case.rho / 2, case_id
        psi = vectors[description]
        # The vector is a unit vector in the exact arithmetic.
        norm = ZERO
        for component in psi:
            norm = alg_add(norm, alg_mul(alg_conj(component), component))
        assert norm == rt(1), description
        value = _expectation(case.block, psi)
        assert value == alg(q2(re_part), q2(im_part)), (case_id, description)
        assert re_part >= neg_rho, (case_id, description)
        assert abs(im_part) <= half_rho, (case_id, description)
        if which == "real":
            assert re_part == neg_rho, (case_id, description)
            tight.add("real")
        elif which == "imaginary":
            assert abs(im_part) == half_rho, (case_id, description)
            tight.add("imaginary")
    # BOTH bounds are attained somewhere, so neither constant can be weakened.
    assert tight == {"real", "imaginary"}


@pytest.mark.contract
def test_which_residuals_exist_on_which_route() -> None:
    """Def. def:residuals: r_1 and r_3 are ABSENT on route (i), not zero."""
    presence = {
        route: (present, absent) for route, present, absent in RESIDUAL_ROUTE_PRESENCE
    }
    assert set(presence) == set(INPUT_ROUTES)
    all_five = ("r_1", "r_2", "r_3", "r_4", "r_5")
    for route, (present, absent) in presence.items():
        assert tuple(sorted(set(present) | set(absent))) == all_five, route
        assert not set(present) & set(absent), route
        # r_2, r_4, r_5 exist everywhere.
        assert {"r_2", "r_4", "r_5"} <= set(present), route
    assert presence["port_grams"][1] == ("r_1", "r_3")
    assert presence["instrument_matrix"][1] == ()
    assert presence["element_graph"][1] == ()
    # The two tolerances that go unused on route (i) are still DECLARED.
    assert TOLERANCES_UNUSED_ON_ROUTE_I == ("eps_1", "eps_3")
    for key in TOLERANCES_UNUSED_ON_ROUTE_I:
        assert key in TOLERANCE_FIXTURE_0_2_0
    # The interface's own row agrees, route by route.
    row = next(r for r in _interface()["outputs"] if r["name"] == "validation_results")
    table = row["residual_route_presence"]
    for route, (present, absent) in presence.items():
        key = next(k for k in table if k.endswith(route))
        assert tuple(table[key]["present"]) == present, route
        assert tuple(table[key]["absent"] or ()) == absent, route


@pytest.mark.contract
def test_def_tolmap_decides_each_condition_at_its_declared_tolerance() -> None:
    """Def. def:tolmap: five items, and no other threshold anywhere."""
    assert len(TOLMAP_ITEMS) == 5
    assert [item for item, _, _ in TOLMAP_ITEMS] == [
        "(i)",
        "(ii)",
        "(iii)",
        "(iv)",
        "(v)",
    ]
    deciding = {tolerance for _, tolerance, _ in TOLMAP_ITEMS}
    assert deciding == {"eps_2", "eps_4 and eps_2", "eps_1"}
    # Every case names an item, a declared tolerance, and a threshold read
    # from that tolerance -- never a constant of the module.
    for case in (
        *TOLMAP_I_CASES,
        *TOLMAP_II_RANK_CASES,
        *TOLMAP_IV_C_CASES,
        *TOLMAP_V_CONTRACTIVITY_CASES,
    ):
        assert case.item in {"(i)", "(ii)", "(iv)", "(v)"}, case.case_id
        assert case.tolerance_key in TOLERANCE_FIXTURE_0_2_0, case.case_id
        assert len(case.derives_from) > 150, case.case_id
    eps_1 = TOLERANCE_FIXTURE_0_2_0["eps_1"]
    eps_2 = TOLERANCE_FIXTURE_0_2_0["eps_2"]
    # (i) admissibility: lmin >= -eps_2 and lmax <= 1 + eps_2, both sides.
    for case in TOLMAP_I_CASES:
        assert case.tolerance_key == "eps_2", case.case_id
        if case.quantity.startswith("lmin"):
            assert case.threshold == -eps_2, case.case_id
            assert case.admitted is (case.value >= case.threshold), case.case_id
        else:
            assert case.threshold == 1 + eps_2, case.case_id
            assert case.admitted is (case.value <= case.threshold), case.case_id
    assert {case.admitted for case in TOLMAP_I_CASES} == {True, False}
    # (ii) the eps_2-rank rule, and BOTH directions of the two-sided cutoff.
    for case in TOLMAP_II_RANK_CASES:
        assert case.tolerance_key == "eps_2", case.case_id
        assert case.quantity.startswith("rk_{eps_2}"), case.case_id
        assert case.admitted is (case.value <= case.threshold), case.case_id
        if not case.admitted:
            assert case.refusal_reason == "port_gram_rank_exceeds_port_size"
    assert any("UNDER-REPORTED" in c.case_id for c in TOLMAP_II_RANK_CASES)
    assert any("OVER-REPORTED" in c.case_id for c in TOLMAP_II_RANK_CASES)
    assert any("BOUNDARY-NOT-COUNTED" in c.case_id for c in TOLMAP_II_RANK_CASES)
    # (iv) the unclamped c, admitted down to -eps_2 and no further.
    for case in TOLMAP_IV_C_CASES:
        assert case.tolerance_key == "eps_2", case.case_id
        assert case.threshold in {Fraction(0), -eps_2}, case.case_id
        assert case.admitted is (case.value >= -eps_2), case.case_id
    assert {case.admitted for case in TOLMAP_IV_C_CASES} == {True, False}
    # (v) contractivity at eps_1, one-sided as a test.
    for case in TOLMAP_V_CONTRACTIVITY_CASES:
        assert case.tolerance_key == "eps_1", case.case_id
        if case.quantity.startswith("lmax"):
            assert case.threshold == 1 + eps_1, case.case_id
            assert case.admitted is (case.value <= case.threshold), case.case_id
        else:
            assert case.threshold == eps_1, case.case_id
            assert case.admitted is (case.value <= case.threshold), case.case_id
    assert {case.admitted for case in TOLMAP_V_CONTRACTIVITY_CASES} == {True, False}
    # The completeness claim: three OTHER kinds and no fourth.
    assert len(TOLMAP_OTHER_VALIDATION_KINDS) == 3
    for kind, members in TOLMAP_OTHER_VALIDATION_KINDS:
        assert kind.strip() and members
    assert {name for name, _ in TOLMAP_RESIDUALS_ALREADY_COUNTED} == {"r_1", "r_2"}


@pytest.mark.contract
def test_eq_r1islmax_is_an_identity_at_every_contractivity_case() -> None:
    """Eq. eq:r1islmax makes two tests one.

    r_1 = (lmax(Gamma^dagger Gamma) - 1)_+, so the admission test and the
    residual test are the SAME test on the SAME number.
    """
    eps_1 = TOLERANCE_FIXTURE_0_2_0["eps_1"]
    checked = 0
    for case in TOLMAP_V_CONTRACTIVITY_CASES:
        if not case.quantity.startswith("lmax"):
            continue
        checked += 1
        r_1 = max(Fraction(0), case.value - 1)
        # The two tests agree, at every case, on both sides.
        assert (case.value <= 1 + eps_1) is (r_1 <= eps_1), case.case_id
        assert case.admitted is (r_1 <= eps_1), case.case_id
    assert checked >= 3
    # The unitary instrument gives r_1 = 0 exactly.
    unitary = next(c for c in TOLMAP_V_CONTRACTIVITY_CASES if "UNITARY" in c.case_id)
    assert unitary.value == 1
    assert max(Fraction(0), unitary.value - 1) == 0
    assert unitary.admitted
    # And a case ADMITTED strictly above 1, which the exact condition excludes.
    widened = [
        c
        for c in TOLMAP_V_CONTRACTIVITY_CASES
        if c.quantity.startswith("lmax") and c.admitted and c.value > 1
    ]
    assert widened


@pytest.mark.contract
def test_the_unclamped_c_is_conservative_at_odd_n_and_not_at_even_n() -> None:
    """Rem. rem:cdirection, on BOTH sides, at c = -eps_2."""
    eps_2 = TOLERANCE_FIXTURE_0_2_0["eps_2"]
    port_count = 2
    gamma = Fraction(1)
    betas = (Fraction(1), Fraction(1))
    ds = (Fraction(1, 2), Fraction(1, 2))
    c = -eps_2

    def beta(n: int, c_value: Fraction) -> Fraction:
        power = Fraction(1) if n == 0 else c_value**n
        tail = sum(
            b * (d**n if n else Fraction(1)) for b, d in zip(betas, ds, strict=True)
        )
        return 1 + (port_count - 1) * gamma * power - tail

    parities = set()
    for n, parity, at_c, at_zero, difference, magnitude in C_DIRECTION_CASES:
        assert parity == ("odd" if n % 2 else "even"), n
        assert at_c == beta(n, c), n
        assert at_zero == beta(n, Fraction(0)), n
        assert difference == at_c - at_zero, n
        assert abs(difference) == magnitude == (port_count - 1) * gamma * abs(c) ** n, n
        if parity == "odd":
            # Conservative: the evaluated bound is BELOW the value at c = 0.
            assert difference < 0, n
        else:
            # It can EXCEED it, which is the half a one-sided account omits.
            assert difference > 0, n
        parities.add(parity)
    assert parities == {"odd", "even"}
    # The two stated bounds, and both are ATTAINED on these data.
    odd_bound = {label: value for label, value, _ in C_DIRECTION_BOUNDS}
    assert odd_bound["odd n, conservative (below)"] == (port_count - 1) * eps_2
    assert odd_bound["even n >= 2, can exceed (above)"] == (port_count - 1) * eps_2**2
    first_odd = next(row for row in C_DIRECTION_CASES if row[0] == 1)
    first_even = next(row for row in C_DIRECTION_CASES if row[0] == 2)
    assert abs(first_odd[4]) == (port_count - 1) * eps_2
    assert abs(first_even[4]) == (port_count - 1) * eps_2**2
    # The even-n bound consumes eps_2 <= 1, which is the declared domain.
    assert eps_2 <= 1
    for n, parity, _, _, _, magnitude in C_DIRECTION_CASES:
        if parity == "even":
            assert magnitude <= (port_count - 1) * eps_2**2, n


@pytest.mark.contract
def test_dark_channels_carry_their_three_scalars_and_compose_by_eq_darkpmcslack() -> (
    None
):
    """Eq. eq:rmin, eq:rbar, eq:darkdelta, eq:darkpmcslack and eq:darkoverstate."""
    eps_2 = TOLERANCE_FIXTURE_0_2_0["eps_2"]
    eps_4 = TOLERANCE_FIXTURE_0_2_0["eps_4"]
    routes = set()
    for case in DARK_SLACK_CASES:
        k = case.port_count
        subsets = _subsets(k)
        multiclick = {s for s in subsets if len(s) >= 2}
        routes.add(case.route)
        assert case.route in {"generated", "declared"}, case.case_id
        if case.columns:
            assert {sp for sp, _ in case.columns} == set(subsets), case.case_id
            # (D1) and (D2) recomputed from the frozen entries.
            d1 = True
            for _, entries in case.columns:
                column_sum = Fraction(0)
                for _, entry in entries:
                    column_sum += entry
                    if entry < -eps_4:
                        d1 = False
                if abs(column_sum - 1) > eps_4:
                    d1 = False
            d2 = all(
                not (not set(sp) <= set(s) and v > eps_2)
                for sp, entries in case.columns
                for s, v in entries
            )
            if case.route == "declared":
                assert case.d1_admitted is d1, case.case_id
                assert case.d2_admitted is d2, case.case_id
                assert case.admitted is (d1 and d2), case.case_id
            # The multiclick masses are the frozen columns, re-added.
            recomputed = tuple(
                (sp, sum(v for s, v in entries if s in multiclick))
                for sp, entries in case.columns
            )
            assert case.mc_mass == recomputed, case.case_id
        if not case.admitted:
            # fail_closed: a refusal emits NO artifact, so no scalar.
            assert case.failing_condition in {"(D1)", "(D2)"}, case.case_id
            for value in (
                case.r_min,
                case.r_bar,
                case.delta_dc,
                case.composed_slack,
                case.composed_exact_form,
            ):
                assert value is None, case.case_id
            continue
        assert case.failing_condition is None, case.case_id
        # An admitted channel emits every scalar; bind them once.
        assert case.r_min is not None, case.case_id
        assert case.r_bar is not None, case.case_id
        assert case.delta_dc is not None, case.case_id
        assert case.r_bar_cost is not None, case.case_id
        assert case.r_bar_cost_bound is not None, case.case_id
        assert case.r_min_upper_bound is not None, case.case_id
        assert case.p_mc is not None, case.case_id
        assert case.composed_slack is not None, case.case_id
        assert case.composed_exact_form is not None, case.case_id
        assert case.overstatement is not None, case.case_id
        r_bar = case.r_bar
        delta = case.delta_dc
        p_mc = case.p_mc
        slack = case.composed_slack
        exact_form = case.composed_exact_form
        # Eq. eq:rmin: the minimum over EVERY non-multiclick column.
        r_min = min(v for sp, v in case.mc_mass if sp not in multiclick)
        assert case.r_min == r_min, case.case_id
        # Eq. eq:rbar, and the cost bound Eq. eq:rbarcost.
        assert r_bar == min(r_min, Fraction(1)), case.case_id
        assert r_bar <= 1, case.case_id
        assert case.r_bar_cost == r_min - r_bar, case.case_id
        assert case.r_bar_cost >= 0, case.case_id
        assert case.r_bar_cost_bound == (k + 2) * eps_4, case.case_id
        assert case.r_bar_cost <= case.r_bar_cost_bound, case.case_id
        # Eq. eq:darkdelta, BY ROUTE.
        expected_delta = (
            Fraction(0) if case.route == "generated" else eps_4 + (k + 1) * eps_2
        )
        assert delta == expected_delta, case.case_id
        if case.route == "generated":
            assert delta == 0, case.case_id
            # For an exactly admissible R, r_min <= 1 for free.
            assert r_min <= 1, case.case_id
            assert case.r_min_upper_bound == Fraction(1), case.case_id
            assert r_bar == r_min, case.case_id
        else:
            # Eq. eq:rminupper: the widened (D1) permits r_min > 1.
            assert case.r_min_upper_bound == 1 + (k + 2) * eps_4, case.case_id
            assert r_min <= case.r_min_upper_bound, case.case_id
        # The composition, both forms, and the difference between them.
        assert 0 <= p_mc <= 1, case.case_id
        assert slack == (1 - r_bar) * p_mc + r_bar - delta, case.case_id
        assert exact_form == (1 - r_min) * p_mc + r_min, case.case_id
        assert case.overstatement == (r_min - r_bar) * (1 - p_mc) + delta, case.case_id
        assert exact_form - slack == case.overstatement, case.case_id
        # The improvement threshold, and it agrees with the composed value.
        assert case.improves_on_p_mc is (r_bar * (1 - p_mc) >= delta)
        assert case.improves_on_p_mc is (slack >= p_mc), case.case_id
    assert routes == {"generated", "declared"}
    # ON THE GENERATED ROUTE THE TWO FORMS COINCIDE, which is what the contract
    # says, and they reproduce the 0.1.3 values exactly.
    generated = [c for c in DARK_SLACK_CASES if c.route == "generated"]
    assert generated
    for case in generated:
        assert case.composed_slack == case.composed_exact_form, case.case_id
        assert case.overstatement == 0, case.case_id
    improvements = {row[0]: row[3] for row in DARK_IMPROVEMENT_CASES}
    by_id = {case.case_id: case for case in DARK_SLACK_CASES}
    assert by_id["DS-GENERATED-K2"].composed_slack == improvements["IMP-K2-HALF"]
    assert by_id["DS-GENERATED-K3"].composed_slack == improvements["IMP-K3-HALF"]
    # A DECLARED channel with r_min > 1 exists, and eq:darkpmc is FALSE there.
    witness = by_id["DS-DECLARED-WITNESS-K4"]
    assert witness.r_min is not None and witness.r_min > 1
    assert witness.r_bar == 1
    assert witness.composed_exact_form is not None and witness.composed_exact_form > 1
    assert witness.composed_slack is not None and witness.composed_slack <= 1
    # And one where the slack costs more than the dark counts gain.
    assert any(case.improves_on_p_mc is False for case in DARK_SLACK_CASES)
    # A negative r_min is admitted and is NOT floored: no step uses the sign.
    negative = by_id["DS-DECLARED-D1-NEGATIVE-ADMIT-K2"]
    assert negative.r_min is not None and negative.r_min < 0
    assert negative.r_bar == negative.r_min


@pytest.mark.contract
def test_eq_d2slack_holds_on_every_admitted_multiclick_column() -> None:
    """Eq. eq:d2slack: R_{MC|S'} >= 1 - delta_dc for S' in MC, against 1."""
    by_id = {case.case_id: case for case in DARK_SLACK_CASES}
    assert D2_SLACK_CASES
    for case_id, column, achieved, bound, exact in D2_SLACK_CASES:
        case = by_id[case_id]
        assert case.admitted, case_id
        assert len(column) >= 2, (case_id, column)
        assert exact == 1, case_id
        assert case.delta_dc is not None
        assert bound == 1 - case.delta_dc, case_id
        assert dict(case.mc_mass)[column] == achieved, (case_id, column)
        assert achieved >= bound, (case_id, column)
        # Theorem thm:dark-counts (iii) is what the widened test relaxes.
        assert achieved <= exact, (case_id, column)
    # Theorem thm:dark-counts (ii) is stated, not repaired: both defects are named.
    assert len(POVM_DEFECT_UNDER_WIDENED_D1) == 2
    assert {what for what, _, _ in POVM_DEFECT_UNDER_WIDENED_D1} == {
        "completeness",
        "positivity",
    }


@pytest.mark.contract
def test_the_two_dark_count_routes_are_exclusive() -> None:
    """Section 2.1 / Def. def:darkadm, closing change request CR-1."""
    assert len(DARK_ROUTE_EXCLUSIVITY_CASES) == 4
    seen = set()
    for (
        case_id,
        declares_r,
        nonzero_pdc,
        admitted,
        route,
        reason,
    ) in DARK_ROUTE_EXCLUSIVITY_CASES:
        seen.add((declares_r, nonzero_pdc))
        # Refused exactly when BOTH are supplied.
        assert admitted is not (declares_r and nonzero_pdc), case_id
        if admitted:
            assert route in {"generated", "declared"}, case_id
            assert route == ("declared" if declares_r else "generated"), case_id
            assert reason is None, case_id
        else:
            assert route is None, case_id
            assert reason == "dark_count_channel_declared_twice", case_id
    # All four combinations, so the rule is pinned and not just its refusal.
    assert seen == {(False, False), (False, True), (True, False), (True, True)}
    refusal = next(
        case
        for case in REFUSAL_CASES_0_2_0
        if case.case_id == "REF-DARK-DECLARED-TWICE"
    )
    assert refusal.reason_is_verbatim
    assert refusal.reason == "dark_count_channel_declared_twice"


@pytest.mark.contract
def test_branch_one_is_taken_exactly_where_predicate_x_holds() -> None:
    """Def. def:pmc at 0.2.0: predicate (X) alone selects branch 1."""
    cases = {case.case_id: case for case in BOUND_DATA_CASES}
    for case_id, x_holds, branch, lemma, needs_window in PMC_BRANCH_CASES:
        case = cases[case_id]
        assert case.branch == branch, case_id
        # Branch 1 exactly where (X) holds, and nowhere else.
        assert x_holds is (branch == "1"), case_id
        assert lemma == ("lem:collapse" if x_holds else "lem:windowtail"), case_id
        # The only predicate a branch-1 case can name is (X).
        assert case.predicate == ("X" if branch == "1" else None), case_id
        # A window is required exactly where (X) fails.
        assert needs_window is (not x_holds), case_id
        assert (case.window is not None) is needs_window, case_id
        if needs_window:
            assert case.window is not None and case.window > case.photon_cutoff
    # NO frozen case anywhere names a predicate other than (X).
    predicates = {case.predicate for case in BOUND_DATA_CASES} - {None}
    assert predicates == {"X"}
    # Both clauses of (X) are exercised, and the case where it fails although
    # the slack is in fact zero.
    assert len(PMC_X_CLAUSE_CASES) == 3
    clauses = [clause for _, clause, _ in PMC_X_CLAUSE_CASES]
    assert any(c.startswith("first") for c in clauses)
    assert any(c.startswith("second") for c in clauses)
    assert any(c.startswith("NEITHER") for c in clauses)


@pytest.mark.contract
def test_the_collapse_slack_is_never_positive() -> None:
    """Rem. rem:noslack: sigma = -beta(0) <= 0 at every receiver.

    THIS REPLACES the 0.1.3 test of the same computation, which read the same
    quantity as "the slack predicate (C) tests" against the declared margin
    eps_hyp. 0.2.0 deletes (C) and eps_hyp; the computation is unchanged and is
    now the contract's own, so what is asserted is what rem:noslack states.
    """
    cases = {case.case_id: case for case in BOUND_DATA_CASES}
    frozen = {row[0]: row for row in COLLAPSE_SLACK_CASES}
    assert set(frozen) == set(cases)
    zeros = positives = 0
    for case_id, beta_zero, sigma, holds in COLLAPSE_SLACK_CASES:
        case = cases[case_id]
        computed = _beta(case, 0)
        assert beta_zero == computed, case_id
        assert sigma == -beta_zero, case_id
        # THE STATEMENT: beta(0) >= 0, so the slack is never positive.
        assert beta_zero >= 0, case_id
        assert sigma <= 0, case_id
        # Eq. eq:collapsehyp holds IFF beta(0) is exactly zero.
        assert holds is (beta_zero == 0), case_id
        zeros += beta_zero == 0
        positives += beta_zero > 0
    counts = dict(COLLAPSE_SLACK_COUNTS)
    assert counts["total"] == len(COLLAPSE_SLACK_CASES)
    assert counts["beta(0) = 0 exactly, so eq:collapsehyp holds"] == zeros
    assert counts["beta(0) > 0, so eq:collapsehyp fails"] == positives
    assert counts["sigma > 0 anywhere"] == 0
    assert zeros and positives
    # Every branch-1 case has beta(0) = 0 exactly, which is what (X) certifies
    # from the declaration without computing anything.
    for case in BOUND_DATA_CASES:
        if case.branch == "1":
            assert frozen[case.case_id][1] == 0, case.case_id
    # The 0.1.3 tuple agrees on the first three fields; only its fourth --
    # "whether predicate (C) fires" -- is superseded.
    old = {row[0]: (row[1], row[2]) for row in BETA_ZERO_AND_C_SLACK}
    for case_id, beta_zero, sigma, _ in COLLAPSE_SLACK_CASES:
        assert old[case_id] == (beta_zero, sigma), case_id
    assert is_superseded("BETA_ZERO_AND_C_SLACK")
    # Rem. rem:noslack's conclusions are carried, all six.
    assert len(NOSLACK_STATEMENTS) == 6
    for statement, why in NOSLACK_STATEMENTS:
        assert statement.strip() and why.strip()


@pytest.mark.contract
def test_the_supersession_list_is_well_formed() -> None:
    """Every mark names a site, a reason and a replacement, and resolves."""
    names = [entry.name for entry in SUPERSEDED_BY_0_2_0]
    assert len(set(names)) == len(names)
    module = sys.modules["registry_receiver_povm"]
    kinds = set()
    for entry in SUPERSEDED_BY_0_2_0:
        assert entry.superseded_by == "0.2.0", entry.name
        assert entry.kind in {"superseded", "incomplete", "reframed"}, entry.name
        kinds.add(entry.kind)
        assert entry.contract_site.strip(), entry.name
        assert len(entry.reason) > 120, entry.name
        assert entry.table.strip(), entry.name
        # The table it names exists in the registry.
        assert hasattr(module, entry.table), entry.table
        # Where it names a row rather than a table, the row exists in it.
        if entry.table != entry.name:
            table = getattr(module, entry.table)
            ids = {
                getattr(row, "case_id", getattr(row, "oracle_id", None))
                for row in table
            }
            assert entry.name in ids, (entry.table, entry.name)
        # Every replacement resolves: a module attribute, or a case id in one.
        for replacement in entry.replacement:
            assert _resolves(module, replacement), (entry.name, replacement)
            # A replacement is never itself superseded.
            assert not is_superseded(replacement), (entry.name, replacement)
        # Only an outright retirement may have no replacement, and it must say
        # so in its reason.
        if not entry.replacement:
            assert "RETIRED OUTRIGHT" in entry.reason, entry.name
    assert kinds == {"superseded", "incomplete", "reframed"}
    # The helpers agree with the table.
    for entry in SUPERSEDED_BY_0_2_0:
        assert is_superseded(entry.name)
        assert supersession(entry.name) is entry
    assert not is_superseded("DECIBEL_CONVERSIONS")
    assert supersession("DECIBEL_CONVERSIONS") is None
    # The rows that carry a `superseded_by` field are exactly the marked rows.
    marked_in_place = {
        _row_id(row)
        for table in (
            RESIDUAL_CASES,
            REFUSAL_CASES,
            DARK_CASES,
            BOUND_DATA_CASES,
            RP_ORACLES,
        )
        for row in table
        if getattr(row, "superseded_by", None) is not None
    }
    listed = {entry.name for entry in SUPERSEDED_BY_0_2_0 if entry.table != entry.name}
    assert marked_in_place == listed, (marked_in_place, listed)
    for table in (
        RESIDUAL_CASES,
        REFUSAL_CASES,
        DARK_CASES,
        BOUND_DATA_CASES,
        RP_ORACLES,
    ):
        for row in table:
            mark = getattr(row, "superseded_by", None)
            assert mark in {None, "0.2.0"}, row
    # The list is complete in both directions.
    assert len(NOT_SUPERSEDED_BY_0_2_0) >= 8
    for what, why in NOT_SUPERSEDED_BY_0_2_0:
        assert what.strip() and len(why) > 60, what


def _row_id(row: Any) -> str:
    """Return the case id of a frozen row, or the oracle id of an entry."""
    identifier = getattr(row, "case_id", None)
    if identifier is None:
        identifier = row.oracle_id
    assert isinstance(identifier, str)
    return identifier


def _resolves(module: Any, name: str) -> bool:
    if hasattr(module, name):
        return True
    for attribute in dir(module):
        value = getattr(module, attribute)
        if not isinstance(value, tuple):
            continue
        for row in value:
            if getattr(row, "case_id", None) == name:
                return True
            if getattr(row, "oracle_id", None) == name:
                return True
            if isinstance(row, tuple) and row and row[0] == name:
                return True
    return False


@pytest.mark.contract
def test_no_superseded_case_is_asserted_unmarked_by_a_run_b_test() -> None:
    """The hand-off invariant.

    A run-B test file that has moved to the amendment -- which it declares by
    naming ``receiver-povm@0.2.0`` -- may not assert a marked 0.1.3 object
    unless it names ``SUPERSEDED_BY_0_2_0`` itself. A file still pinned to
    0.1.3 is pre-amendment; its references are the pending work run A recorded,
    and the scan may only SHRINK from that list, never grow.
    """
    marked = [entry.name for entry in SUPERSEDED_BY_0_2_0]
    files = sorted(
        list((REPO_ROOT / "tests" / "golden").glob("test_receiver_povm_*.py"))
        + list((REPO_ROOT / "tests" / "unit").glob("test_receiver_*.py"))
        + list((REPO_ROOT / "tests" / "property").glob("test_receiver_povm_*.py"))
    )
    assert files, "no run-B receiver tests found"
    found: set[tuple[str, str]] = set()
    for path in files:
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPO_ROOT).as_posix()
        on_amendment = AMENDMENT_SPEC_VERSION_MARKER in source
        acknowledges = "SUPERSEDED_BY_0_2_0" in source or "is_superseded" in source
        for name in marked:
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])"
            if not re.search(pattern, source):
                continue
            found.add((relative, name))
            if acknowledges:
                continue
            assert not on_amendment, (
                f"{relative} has moved to {AMENDMENT_SPEC_VERSION_MARKER} and still "
                f"asserts the superseded {name!r} without naming "
                "SUPERSEDED_BY_0_2_0; retire or rewrite it"
            )
    pending = set(PENDING_RETIREMENT_AT_RUN_B)
    assert found <= pending, sorted(found - pending)
    # Every pending pair names a file that exists and a marked object.
    for relative, name in PENDING_RETIREMENT_AT_RUN_B:
        assert (REPO_ROOT / relative).exists(), relative
        assert is_superseded(name), name


@pytest.mark.contract
def test_not_one_float_appears_in_the_0_2_0_frozen_values() -> None:
    """The 0.2.0 substrate is exact too."""
    for name, obj in (
        ("TOLERANCE_FIXTURE_0_2_0", TOLERANCE_FIXTURE_0_2_0),
        ("TOLERANCE_DOMAIN", TOLERANCE_DOMAIN),
        ("TOLERANCE_DOMAIN_CASES", TOLERANCE_DOMAIN_CASES),
        ("RESIDUAL5_CASES", RESIDUAL5_CASES),
        ("RES5_EXPECTATION_CASES", RES5_EXPECTATION_CASES),
        ("RESIDUAL_ROUTE_PRESENCE", RESIDUAL_ROUTE_PRESENCE),
        ("TOLMAP_I_CASES", TOLMAP_I_CASES),
        ("TOLMAP_II_RANK_CASES", TOLMAP_II_RANK_CASES),
        ("TOLMAP_IV_C_CASES", TOLMAP_IV_C_CASES),
        ("TOLMAP_V_CONTRACTIVITY_CASES", TOLMAP_V_CONTRACTIVITY_CASES),
        ("C_DIRECTION_CASES", C_DIRECTION_CASES),
        ("C_DIRECTION_BOUNDS", C_DIRECTION_BOUNDS),
        ("DARK_SLACK_CASES", DARK_SLACK_CASES),
        ("D2_SLACK_CASES", D2_SLACK_CASES),
        ("DARK_ROUTE_EXCLUSIVITY_CASES", DARK_ROUTE_EXCLUSIVITY_CASES),
        ("COLLAPSE_SLACK_CASES", COLLAPSE_SLACK_CASES),
        ("COLLAPSE_SLACK_COUNTS", COLLAPSE_SLACK_COUNTS),
        ("PMC_BRANCH_CASES", PMC_BRANCH_CASES),
        ("REFUSAL_CASES_0_2_0", REFUSAL_CASES_0_2_0),
        ("SUPERSEDED_BY_0_2_0", SUPERSEDED_BY_0_2_0),
    ):
        _no_floats(obj, name)


# ---------------------------------------------------------------------------
#  15. THE 0.3.0 AMENDMENT
#
#  Everything below pins the delta between 0.2.0 and 0.3.0. The 0.1.3 and 0.2.0
#  sections above are untouched, and the assertions that were version-pinned at
#  interface.yaml have been REPOINTED at the version it now describes -- not
#  weakened, not skipped, not xfailed. Every frozen NUMBER of both earlier
#  passes still replays exactly as it was frozen.
# ---------------------------------------------------------------------------


def _beta_at(case: Any, n: int) -> Fraction:
    """Eq. eq:beta on a case's own bound data, with the convention 0^0 = 1."""
    k = len(case.betas)
    cn = Fraction(1) if n == 0 else case.c**n
    return (
        Fraction(1)
        + (k - 1) * case.gamma * cn
        - sum(
            b * (Fraction(1) if n == 0 else d**n)
            for b, d in zip(case.betas, case.ds, strict=True)
        )
    )


def _tail_at(case: Any, m: int) -> Fraction:
    return Fraction(1) - sum(
        b * (d**m) for b, d in zip(case.betas, case.ds, strict=True)
    )


@pytest.mark.contract
def test_the_0_3_0_tolerance_fixture_is_the_declared_tuple() -> None:
    """Section 2.1: EIGHT members, six required always and two on the opt-in route."""
    assert set(TOLERANCE_FIXTURE_0_3_0) == {
        "eps_1",
        "eps_2",
        "eps_3",
        "eps_4",
        "eps_5",
        "eps_6",
        "eps_gap",
        "eps_eig",
    }
    assert len(TOLERANCE_FIXTURE_0_3_0) == 8
    # The 0.2.0 six are exactly the members required on EVERY declaration.
    assert set(TOLERANCES_ALWAYS_REQUIRED_0_3_0) == set(TOLERANCE_FIXTURE_0_2_0)
    assert len(TOLERANCES_ALWAYS_REQUIRED_0_3_0) == 6
    conditional = {key for key, _ in TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0}
    assert conditional == {"eps_6", "eps_eig"}
    assert not conditional & set(TOLERANCES_ALWAYS_REQUIRED_0_3_0)
    assert conditional | set(TOLERANCES_ALWAYS_REQUIRED_0_3_0) == set(
        TOLERANCE_FIXTURE_0_3_0
    )
    for _, why in TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0:
        assert "exact_window" in why or "exact window" in why
    # Rem. rem:tolerancedomain: the domain is UNCHANGED and covers all eight.
    low, high = TOLERANCE_DOMAIN
    assert (low, high) == (Fraction(0), Fraction(1))
    assert TOLERANCE_DOMAIN_CLOSED_AT == (True, False)
    for key, value in TOLERANCE_FIXTURE_0_3_0.items():
        assert isinstance(value, Fraction), key
        assert low <= value < high, key
    # The domain object stands; only its FRAMING is stale, so it is `reframed`.
    assert supersession_0_3_0("TOLERANCE_DOMAIN").kind == "reframed"
    # The interface row agrees on which members are conditional.
    row = next(r for r in _interface()["inputs"] if r["name"] == "numerical_tolerances")
    assert tuple(row["always_required"]) == TOLERANCES_ALWAYS_REQUIRED_0_3_0
    assert set(row["conditionally_required"]) == conditional
    assert row["conditionally_required_on"].strip()
    assert (
        row["missing_conditional_refusal_reason"]
        == "exact_window_declared_without_required_tolerance"
    )


@pytest.mark.contract
def test_the_exact_block_quantity_is_the_minimum_of_its_own_spectrum() -> None:
    """Def. def:exactbnd, and Lem. lem:exactbasic's two halves separated."""
    assert len(EXACT_BLOCK_CASES) >= 8
    for case in EXACT_BLOCK_CASES:
        # beta* IS the minimum eigenvalue, and the spectrum is frozen whole.
        assert case.beta_star == min(case.spectrum), case.case_id
        assert list(case.spectrum) == sorted(case.spectrum), case.case_id
        # The dimension is binom(D + n - 1, n) with D = |Inp_C|.
        assert case.block_dimension == _block_dimension(
            case.channel_modes, case.photon_number
        ), case.case_id
        assert len(case.spectrum) == case.block_dimension, case.case_id
        # Eq. eq:exactbasic, FIRST inequality: beta(n) <= beta*(n). It is
        # Eq. eq:mcbound and needs no hypothesis beyond thm:multiclick-bound's.
        assert case.gap == case.beta_star - case.beta_analytic, case.case_id
        assert case.gap >= 0, case.case_id
        # Eq. eq:exactbasic, SECOND inequality: beta*(n) <= 1, likewise
        # unconditional -- and it holds at the counterexample too.
        assert case.beta_star <= 1, case.case_id
        # beta*(n) >= 0 needs Eq. eq:mcpos, and ONLY there.
        if case.mcpos_holds:
            assert 0 <= case.beta_star <= 1, case.case_id
        else:
            assert case.beta_star < 0, case.case_id
        assert len(case.derives_from) > 200, case.case_id
    # Eq. eq:mcpos fails at EXACTLY the two counterexample rows, and they are
    # Rem. rem:exactpositivity's instance: beta* = -3 with beta = -3, so
    # Eq. eq:mcbound holds WITH EQUALITY and thm:multiclick-bound is untouched.
    failing = [c for c in EXACT_BLOCK_CASES if not c.mcpos_holds]
    assert {c.case_id for c in failing} == {
        "EB-POSITIVITY-COUNTEREXAMPLE-N1",
        "EB-POSITIVITY-COUNTEREXAMPLE-N2",
    }
    for case in failing:
        assert case.beta_star == case.beta_analytic == Fraction(-3), case.case_id
        assert case.gap == 0, case.case_id
        assert set(case.spectrum) == {Fraction(-3)}, case.case_id
    # THE EXACT WINDOW BUYS SOMETHING ONLY WHERE THE CHANNEL SPACE HAS ROOM:
    # every one-dimensional channel space has gap 0, and every gap > 0 case
    # has D >= 2.
    for case in EXACT_BLOCK_CASES:
        if case.channel_modes == 1:
            assert case.gap == 0, case.case_id
        if case.gap > 0:
            assert case.channel_modes >= 2, case.case_id
    assert any(c.gap > 0 for c in EXACT_BLOCK_CASES)
    # The two halves of the lemma are recorded with the hypothesis each needs.
    assert len(EXACTBASIC_HALVES) == 5
    unconditional = [h for h in EXACTBASIC_HALVES if "ALONE" in h[1]]
    assert len(unconditional) == 2
    assert any("Eq. eq:mcpos" in h[1] for h in EXACTBASIC_HALVES)
    assert any("EXACTLY ONE STEP" in h[0] for h in EXACTBASIC_HALVES)
    # The general block form is recorded as a statement, not as numbers.
    assert len(BB84_EXACT_BLOCK_FORM) >= 5
    for statement, site in BB84_EXACT_BLOCK_FORM:
        assert statement.strip() and site.strip()


@pytest.mark.contract
def test_the_bb84_exact_block_agrees_with_its_closed_form() -> None:
    """Eq. eq:bb84exactvalue CHECKS the hand computation at three values of p_Z."""
    known = {
        "EB-BB84-N2-PZ-HALF": Fraction(1, 2),
        "EB-BB84-N2-PZ-SEVEN-TENTHS": Fraction(7, 10),
        "EB-BB84-N2-PZ-QUARTER": Fraction(1, 4),
    }
    for case_id, p_z in known.items():
        case = next(c for c in EXACT_BLOCK_CASES if c.case_id == case_id)
        p_x = 1 - p_z
        # The spectrum, from the projector decomposition of Eq. eq:bb84exact2.
        assert case.spectrum == tuple(
            sorted((1 - p_x**2, 1 - p_z**2, 1 - p_z**2 - p_x**2))
        ), case_id
        # Eq. eq:bb84exactvalue, both sides, and the gap the example names.
        assert case.beta_star == 1 - p_z**2 - p_x**2, case_id
        assert case.beta_analytic == 1 - 2 * p_z**2 - 2 * p_x**2, case_id
        assert case.gap == p_z**2 + p_x**2 > 0, case_id
        assert case.channel_modes == 2 and case.block_dimension == 3, case_id
    # The three-photon block is frozen at p_Z = 1/2 ONLY, and the case says
    # why: at p_Z = 7/10 the answer leaves Q[sqrt2].
    n3 = [c for c in EXACT_BLOCK_CASES if c.photon_number == 3 and c.channel_modes == 2]
    assert len(n3) == 1
    assert n3[0].case_id == "EB-BB84-N3-PZ-HALF"
    assert n3[0].spectrum == (
        Fraction(13, 16),
        Fraction(13, 16),
        Fraction(15, 16),
        Fraction(15, 16),
    )
    # The trace of the frozen spectrum against the trace of the block:
    # 4 - 2 p_Z^3 - 2 p_X^3 at p_Z = p_X = 1/2.
    assert sum(n3[0].spectrum) == 4 - 2 * Fraction(1, 8) - 2 * Fraction(1, 8)
    assert "436468" in n3[0].derives_from


@pytest.mark.contract
def test_the_exact_window_composite_is_the_lemma_it_evaluates() -> None:
    """Lem. lem:exactwindow: Eq. eq:exactcomposite, both disjuncts of the tail."""
    for case in EXACT_COMPOSITE_CASES:
        window = [value for _, value in case.ell_values]
        assert min(window) == case.window_minimum, case.case_id
        assert min(case.window_minimum, case.tau) == case.inner_minimum, case.case_id
        assert max(Fraction(0), case.inner_minimum) == case.p_value, case.case_id
        # The lemma asserts 0 <= P <= 1.
        assert 0 <= case.p_value <= 1, case.case_id
        # The window is over N < n <= m*, and m* > N makes it non-empty.
        assert case.exact_depth > case.photon_cutoff, case.case_id
        assert [n for n, _ in case.ell_values] == list(
            range(case.photon_cutoff + 1, case.exact_depth + 1)
        ), case.case_id
        # Eq. eq:tailadm has two disjuncts and both are exercised.
        assert case.tailadm_disjunct in {"nonpositive", "below the infimum"}
        if case.tailadm_disjunct == "nonpositive":
            assert case.tau <= 0, case.case_id
        # The P = 0 branch is the ONE step that uses Eq. eq:mcpos.
        assert case.uses_mcpos_branch == (case.p_value == 0), case.case_id
        assert len(case.derives_from) > 200, case.case_id
    disjuncts = {case.tailadm_disjunct for case in EXACT_COMPOSITE_CASES}
    assert disjuncts == {"nonpositive", "below the infimum"}
    # Both the window and the remainder bind somewhere, and the upper limit
    # P = 1 is attained.
    composites = EXACT_COMPOSITE_CASES
    assert any(c.inner_minimum == c.tau < c.window_minimum for c in composites)
    assert any(c.inner_minimum == c.window_minimum < c.tau for c in composites)
    assert any(c.p_value == 1 for c in EXACT_COMPOSITE_CASES)
    assert sum(c.uses_mcpos_branch for c in EXACT_COMPOSITE_CASES) >= 2
    # The minimum runs over the WHOLE window: one case has its minimum in the
    # middle, which an implementation reading only the first index would miss.
    multi = [c for c in EXACT_COMPOSITE_CASES if len(c.ell_values) > 1]
    assert multi
    assert any(c.window_minimum != c.ell_values[0][1] for c in multi), (
        "no case has its window minimum away from the first index"
    )
    # The three admissible choices, each with the hypothesis it needs.
    assert len(EXACT_WINDOW_ADMISSIBLE_CHOICES) == 3
    assert {part for part, _, _, _ in EXACT_WINDOW_ADMISSIBLE_CHOICES} == {
        "(i)",
        "(ii)",
        "(iii)",
    }
    part_i = next(row for row in EXACT_WINDOW_ADMISSIBLE_CHOICES if row[0] == "(i)")
    assert "NONE" in part_i[2]
    part_ii = next(row for row in EXACT_WINDOW_ADMISSIBLE_CHOICES if row[0] == "(ii)")
    assert "eq:collapsehyp" in part_ii[2]


@pytest.mark.contract
def test_the_emitted_exact_window_value_is_eq_pmcex() -> None:
    """Def. def:pmcex, term by term, on both branches, re-derived from the data."""
    assert len(EXACT_WINDOW_CASES) >= 12
    for case in EXACT_WINDOW_CASES:
        n0, m = case.photon_cutoff, case.exact_depth
        # The depth constraints Def. def:pmcex states.
        assert m > n0, case.case_id
        if not case.predicate_x:
            assert case.tail_window is not None, case.case_id
            assert m <= case.tail_window, case.case_id
        # The window is exactly N < n <= m*_t, and each row is Eq. eq:elldef.
        assert [n for n, _, _, _ in case.window] == list(range(n0 + 1, m + 1)), (
            case.case_id
        )
        for n, analytic, computed, ell in case.window:
            assert analytic == _beta_at(case, n), (case.case_id, n)
            assert ell == max(analytic, computed - case.eps_eig), (case.case_id, n)
            # Eq. eq:elldef FLOORS at the analytic bound, always.
            assert ell >= analytic, (case.case_id, n)
        assert case.window_minimum == min(e for _, _, _, e in case.window), case.case_id
        # The branch's own remainder, and which lemma part makes it admissible.
        if case.branch == "1":
            assert case.predicate_x, case.case_id
            assert case.remainder == _beta_at(case, m + 1), case.case_id
            assert case.middle_window_minimum is None, case.case_id
            arguments = [case.window_minimum, case.remainder]
        else:
            assert not case.predicate_x, case.case_id
            assert case.remainder == _tail_at(case, case.tail_window), case.case_id
            middle = list(range(m + 1, case.tail_window + 1))
            if middle:
                assert not case.middle_window_empty, case.case_id
                assert case.middle_window_minimum == min(
                    _beta_at(case, n) for n in middle
                ), case.case_id
                arguments = [
                    case.window_minimum,
                    case.middle_window_minimum,
                    case.remainder,
                ]
            else:
                # THE EMPTY MIDDLE MINIMUM IS +INFINITY AND INACTIVE, NOT ZERO.
                assert case.middle_window_empty, case.case_id
                assert case.middle_window_minimum is None, case.case_id
                assert m == case.tail_window, case.case_id
                arguments = [case.window_minimum, case.remainder]
        assert case.p_mc == max(Fraction(0), min(arguments)), case.case_id
        # Thm. thm:emitted-bound's range, exactly, and NOTHING is clamped into it.
        assert 0 <= case.p_mc <= 1, case.case_id
        # r_6 over this window.
        assert case.r6 == max(
            max(Fraction(0), analytic - computed)
            for _, analytic, computed, _ in case.window
        ), case.case_id
        assert case.eig_assumption_holds, case.case_id
        assert len(case.derives_from) > 300, case.case_id
    # Both branches, and every binding pattern, are exercised.
    assert {c.branch for c in EXACT_WINDOW_CASES} == {"1", "2"}
    assert any(c.middle_window_empty for c in EXACT_WINDOW_CASES)
    assert any(c.p_mc == 0 for c in EXACT_WINDOW_CASES)
    assert any(c.p_mc == c.remainder < c.window_minimum for c in EXACT_WINDOW_CASES), (
        "no case where the analytic remainder strictly binds"
    )
    assert any(c.window_minimum < c.remainder for c in EXACT_WINDOW_CASES), (
        "no case where the exact window strictly binds"
    )
    # eps_eig is exercised across the declared domain, INCLUDING the split
    # Eq. eq:bb84exactemit names at 1/2 and a value above it.
    slacks = {c.eps_eig for c in EXACT_WINDOW_CASES}
    assert {Fraction(0), Fraction(1, 1000), Fraction(1, 2), Fraction(3, 4)} <= slacks
    for slack in slacks:
        assert 0 <= slack < 1
    # Which remainder each branch keeps, and the m* constraint that goes with it.
    assert len(EXACT_WINDOW_BRANCH_REMAINDERS) == 2
    branch_one = next(r for r in EXACT_WINDOW_BRANCH_REMAINDERS if r[0] == "1")
    assert branch_one[1] is True
    assert "m*_t > N only" in branch_one[4]
    branch_two = next(r for r in EXACT_WINDOW_BRANCH_REMAINDERS if r[0] == "2")
    assert branch_two[1] is False
    assert "m*_t <= m_t" in branch_two[4]


@pytest.mark.contract
def test_eq_bb84exactemit_is_the_family_the_example_states() -> None:
    """Ex. ex:bb84exact: p_mc = max{0, 1/2 - eps_eig}, split at eps_eig = 1/2."""
    family = [
        case
        for case in EXACT_WINDOW_CASES
        if case.case_id.startswith("EX-BB84-N1-M2-EIG")
    ]
    assert len(family) == 4
    for case in family:
        assert case.photon_cutoff == 1 and case.exact_depth == 2
        assert case.window == ((2, Fraction(0), Fraction(1, 2), case.window[0][3]),)
        assert case.remainder == Fraction(1, 2)
        # Eq. eq:bb84exactemit, verbatim as an expression.
        expected = max(Fraction(0), Fraction(1, 2) - case.eps_eig)
        assert case.p_mc == expected, case.case_id
        # And 0.2.0 emits ZERO at this cutoff, at every one of the four.
        assert case.p_mc_without_depth == 0, case.case_id
    # The split: strictly below 1/2 the value is positive, at and above it 0.
    for case in family:
        if case.eps_eig < Fraction(1, 2):
            assert case.p_mc > 0, case.case_id
        else:
            assert case.p_mc == 0, case.case_id
    # BD-BB84-N1-ZERO is the SAME device at the SAME cutoff with NO depth, and
    # it is superseded by nothing: the two coexist.
    zero = next(c for c in BOUND_DATA_CASES if c.case_id == "BD-BB84-N1-ZERO")
    assert zero.photon_cutoff == 1 and zero.p_mc == 0
    assert not is_superseded_0_3_0("BOUND_DATA_CASES")


@pytest.mark.contract
def test_prop_exactnoworse_holds_at_every_frozen_declaration() -> None:
    """Prop. prop:exactnoworse, and the one step that does not survive floats."""
    by_id = {case.case_id: case for case in EXACT_WINDOW_CASES}
    assert {cid for cid, _, _, _ in NO_WORSE_CASES} == set(by_id)
    strict = equal = 0
    for case_id, without, with_depth, relation in NO_WORSE_CASES:
        case = by_id[case_id]
        assert without == case.p_mc_without_depth, case_id
        assert with_depth == case.p_mc, case_id
        assert with_depth >= without, case_id
        if relation == "strictly greater":
            assert with_depth > without, case_id
            strict += 1
        else:
            assert relation == "equal", case_id
            assert with_depth == without, case_id
            equal += 1
    assert strict >= 5 and equal >= 4
    # Eq. eq:pmcdef, re-derived independently at every case, is what the
    # `without` column holds.
    for case in EXACT_WINDOW_CASES:
        if case.predicate_x:
            expected = max(Fraction(0), _beta_at(case, case.photon_cutoff + 1))
        else:
            window = min(
                _beta_at(case, n)
                for n in range(case.photon_cutoff + 1, case.tail_window + 1)
            )
            expected = max(Fraction(0), min(window, _tail_at(case, case.tail_window)))
        assert expected == case.p_mc_without_depth, case.case_id
    # Rem. rem:noworsefl: TWO steps survive an evaluation and ONE does not, and
    # the one that does not is branch 1's remainder comparison.
    assert len(NO_WORSE_UNDER_EVALUATION) == 3
    surviving = [row for row in NO_WORSE_UNDER_EVALUATION if row[1]]
    not_surviving = [row for row in NO_WORSE_UNDER_EVALUATION if not row[1]]
    assert len(surviving) == 2 and len(not_surviving) == 1
    assert "branch 1" in not_surviving[0][0]
    assert "EXACT VALUES" in not_surviving[0][2]


@pytest.mark.contract
def test_the_opt_in_invariant_leaves_every_earlier_bound_case_standing() -> None:
    """Def. def:pmc: no depth anywhere -> no beta*, no ass:eig, 0.2.0's value."""
    assert len(OPT_IN_INVARIANT) == len(BOUND_DATA_CASES)
    frozen = {case.case_id for case in BOUND_DATA_CASES}
    assert {row[0] for row in OPT_IN_INVARIANT} == frozen
    for case_id, declared, formed, invoked, r6_emitted, unchanged in OPT_IN_INVARIANT:
        assert declared is False, case_id
        assert formed is False, case_id
        assert invoked is False, case_id
        assert r6_emitted is False, case_id
        assert unchanged is True, case_id
    # The four the amendment would change IF a depth were declared, re-derived
    # rather than asserted, each against its own frozen case.
    assert len(BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0) == 4
    named = {
        "BD-BB84-N1-ZERO",
        "BD-BB84-N2",
        "BD-BB84-N3",
        "BD-BB84-PZ-QUARTER-N2",
    }
    assert {row[0] for row in BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0} == named
    for case_id, cutoff, p_mc, why in BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0:
        case = next(c for c in BOUND_DATA_CASES if c.case_id == case_id)
        assert case.photon_cutoff == cutoff, case_id
        assert case.p_mc == p_mc, case_id
        assert len(why) > 120, case_id
        # Eq. eq:pmcdef, re-derived: every one of the four takes branch 1.
        assert case.branch == "1" and case.predicate == "X", case_id
        assert case.p_mc == max(Fraction(0), _beta_at(case, cutoff + 1)), case_id
    assert {row[2] for row in BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0} == {
        Fraction(0),
        Fraction(1, 2),
        Fraction(3, 4),
        Fraction(1, 8),
    }
    # NOT ONE bound-data table or row is marked at 0.3.0.
    assert not is_superseded_0_3_0("BOUND_DATA_CASES")
    for case in BOUND_DATA_CASES:
        assert getattr(case, "superseded_by", None) in {None, "0.2.0"}, case.case_id


@pytest.mark.contract
def test_the_two_kinds_of_setting_mix_and_the_minimum_is_over_T() -> None:
    """Def. def:pmcex: the depth is per SETTING, and p_mc is the min over T."""
    assert len(MIXED_SETTING_CASES) == 4
    for case in MIXED_SETTING_CASES:
        values = [value for _, _, _, _, value in case.per_setting]
        assert case.p_mc == min(values), case.case_id
        assert len(case.per_setting) == 2, case.case_id
        for _, declared, depth, definition, _ in case.per_setting:
            assert declared == (depth is not None), case.case_id
            expected = "eq:pmcex" if declared else "eq:pmcdef"
            assert expected in definition, case.case_id
            if depth is not None:
                assert depth > case.photon_cutoff, case.case_id
        # Ass. ass:eig is invoked exactly where SOME setting carries a depth.
        assert case.eig_invoked == any(d for _, d, _, _, _ in case.per_setting), (
            case.case_id
        )
        assert len(case.derives_from) > 200, case.case_id
    # All four combinations of "depth here / not there" are frozen.
    patterns = {
        tuple(declared for _, declared, _, _, _ in case.per_setting)
        for case in MIXED_SETTING_CASES
    }
    assert patterns == {(False, False), (True, False), (False, True), (True, True)}
    # AND THE EMITTED VALUE IS THE SAME AT ALL FOUR, because this receiver's
    # channel space is one dimensional -- which the cases say in terms.
    assert len({case.p_mc for case in MIXED_SETTING_CASES}) == 1
    both = next(c for c in MIXED_SETTING_CASES if c.case_id == "MIX-DEPTH-AT-BOTH")
    assert "NO FROZEN RECEIVER" in both.derives_from


@pytest.mark.contract
def test_r6_is_the_window_consistency_defect_and_is_one_sided() -> None:
    """Eq. eq:res6: exact value 0, refuse-only, and silent on the overshoot."""
    eps_6 = TOLERANCE_FIXTURE_0_3_0["eps_6"]
    for case in RESIDUAL6_CASES:
        for _, _, analytic, computed, exact, defect in case.entries:
            assert defect == max(Fraction(0), analytic - computed), case.case_id
            # The EXACT beta* always dominates the analytic beta: that is
            # Lem. lem:exactbasic, and it is why r_6's exact value is 0.
            assert exact >= analytic, case.case_id
        assert case.r6 == max(row[-1] for row in case.entries), case.case_id
        assert case.passes == (case.r6 <= eps_6), case.case_id
        assert (case.refusal_reason is None) == case.passes, case.case_id
        if case.refusal_reason is not None:
            assert (
                case.refusal_reason
                == "window_eigenvalue_consistency_residual_above_tolerance"
            ), case.case_id
        # `is_overshoot` is CHECKABLE, against the exact value r_6 never sees.
        assert case.is_overshoot == any(
            computed > exact for _, _, _, computed, exact, _ in case.entries
        ), case.case_id
        assert len(case.derives_from) > 200, case.case_id
    # THE UNSEEN DIRECTION IS FROZEN AS A PASS, and it is the only overshoot.
    overshoots = [case for case in RESIDUAL6_CASES if case.is_overshoot]
    assert len(overshoots) == 1
    assert overshoots[0].case_id == "R6-PASS-OVERSHOOT-BLIND"
    assert overshoots[0].passes is True
    assert overshoots[0].r6 == 0
    # The maximum runs over indices AND over settings, and both are exercised
    # by a case whose FIRST entry is clean and whose second is not.
    multi_index = [
        case
        for case in RESIDUAL6_CASES
        if len({n for _, n, _, _, _, _ in case.entries}) > 1
    ]
    multi_setting = [
        case
        for case in RESIDUAL6_CASES
        if len({t for t, _, _, _, _, _ in case.entries}) > 1
    ]
    assert multi_index and multi_setting
    for case in multi_index + multi_setting:
        if not case.passes:
            assert case.entries[0][-1] == 0, case.case_id
            assert case.entries[-1][-1] > eps_6, case.case_id
    # A small undershoot INSIDE the tolerance passes: r_6 is a residual, not
    # an exact-zero assertion.
    inside = [case for case in RESIDUAL6_CASES if case.passes and case.r6 > 0]
    assert inside
    for case in inside:
        assert 0 < case.r6 <= eps_6, case.case_id


@pytest.mark.contract
def test_r6_presence_is_request_dependent_where_r1_and_r3_are_route_dependent() -> None:
    """Def. def:residuals: two different presence rules, on two different axes."""
    for declaration, route, present, eps_declared in RESIDUAL6_REQUEST_PRESENCE:
        assert route in INPUT_ROUTES, route
        assert present == ("a depth" in declaration), declaration
        # eps_6 is declared exactly where r_6 exists.
        assert eps_declared == present, declaration
    # r_6's presence does not depend on the route: for each declaration the
    # verdict is the same on all three.
    for declaration in {row[0] for row in RESIDUAL6_REQUEST_PRESENCE}:
        verdicts = {
            row[2] for row in RESIDUAL6_REQUEST_PRESENCE if row[0] == declaration
        }
        assert len(verdicts) == 1, declaration
    # The six residuals side by side, each on its own axis.
    assert len(RESIDUAL_SCOPING_0_3_0) == 6
    axes = {name: axis for name, axis, _ in RESIDUAL_SCOPING_0_3_0}
    assert axes == {
        "r_1": "route",
        "r_2": "none",
        "r_3": "route",
        "r_4": "none",
        "r_5": "none",
        "r_6": "request",
    }
    # The 0.2.0 route table is INCOMPLETE at 0.3.0 -- not wrong, incomplete.
    assert supersession_0_3_0("RESIDUAL_ROUTE_PRESENCE").kind == "incomplete"
    for route, present, absent in RESIDUAL_ROUTE_PRESENCE:
        assert "r_6" not in present and "r_6" not in absent, route
    # And the interface carries BOTH tables on the one output row.
    row = next(r for r in _interface()["outputs"] if r["name"] == "validation_results")
    request = row["residual_request_presence"]
    assert request["no_depth_declared_anywhere"]["absent"] == ["r_6"]
    assert request["depth_declared_at_some_setting"]["present"] == ["r_6"]
    assert "r_6" in row["symbol"]


@pytest.mark.contract
def test_a_violated_eig_assumption_emits_an_over_large_lower_bound() -> None:
    """Ass. ass:eig's `If violated` column, made concrete and caught by nothing."""
    witness = dict(A_EIG_WITNESS)
    assert "EX-BS-N1-M2-OVERSHOOT" in witness["case"]
    assert witness["declared eps_eig"] == "1/1000"
    assert "VIOLATED" in witness["Eq. eq:eigassumption"]
    assert "749/1000" in witness["emitted p_mc"]
    assert "1/2" in witness["the true uniform bound it claims"]
    assert "249/1000" in witness["the excess"]
    # r_6 PASSES on it -- the unseen direction, from the other side.
    assert witness["r_6"].startswith("0")
    assert "R6-PASS-OVERSHOOT-BLIND" in witness["r_6"]
    overshoot = next(
        case for case in RESIDUAL6_CASES if case.case_id == "R6-PASS-OVERSHOOT-BLIND"
    )
    assert overshoot.passes and overshoot.r6 == 0 and overshoot.is_overshoot
    # The arithmetic, re-derived: ell(2) = max{beta(2), beta-hat*(2) - eps_eig}
    # with beta(2) = 1/2 and beta-hat*(2) = 3/4, capped by beta(3) = 3/4.
    eps_eig = Fraction(1, 1000)
    ell = max(Fraction(1, 2), Fraction(3, 4) - eps_eig)
    assert ell == Fraction(749, 1000)
    assert max(Fraction(0), min(ell, Fraction(3, 4))) == Fraction(749, 1000)
    # And the true infimum it claims to bound is 1/2 (EB-BS-N2), so the
    # emitted value EXCEEDS it -- the unsafe direction.
    exact = next(case for case in EXACT_BLOCK_CASES if case.case_id == "EB-BS-N2")
    assert exact.beta_star == Fraction(1, 2)
    assert Fraction(749, 1000) > exact.beta_star
    # ARCHITECTURE_SPEC.md Section 7.3 does NOT catch it: the value is in
    # [0, 1], which is exactly Rem. rem:exacteig's asymmetry.
    assert 0 <= Fraction(749, 1000) <= 1
    assert "NOT TRIGGERED" in witness["ARCHITECTURE_SPEC.md Section 7.3"]
    assert "NOTHING" in witness["what catches it"]
    # No case in EXACT_WINDOW_CASES violates the assumption: the witness is
    # deliberately kept out of the table of supported values.
    assert all(case.eig_assumption_holds for case in EXACT_WINDOW_CASES)
    assert "EX-BS-N1-M2-OVERSHOOT" not in {c.case_id for c in EXACT_WINDOW_CASES}
    caveat = witness["what run B must NOT do with this case"]
    assert "WITNESS" in caveat and "not as a value the contract supports" in caveat


@pytest.mark.contract
def test_the_exact_window_validation_is_domain_and_predicate_only() -> None:
    """Def. def:pmcex's four validations, and no new threshold among them."""
    for case in EXACT_WINDOW_VALIDATION_CASES:
        if case.exact_depth is None:
            expected: str | None = None
        elif not (case.eps_eig_declared and case.eps_6_declared):
            expected = "exact_window_declared_without_required_tolerance"
        elif case.exact_depth <= case.photon_cutoff or (
            not case.predicate_x
            and case.tail_window is not None
            and case.exact_depth > case.tail_window
        ):
            expected = "exact_window_depth_outside_declared_range"
        else:
            expected = None
        assert case.refusal_reason == expected, case.case_id
        assert case.admitted == (expected is None), case.case_id
        assert len(case.derives_from) > 200, case.case_id
    # BOTH BOUNDARIES ARE ADMITTED and both violations are refused.
    ids = {case.case_id: case for case in EXACT_WINDOW_VALIDATION_CASES}
    assert ids["XW-ADMIT-MINIMAL-DEPTH"].exact_depth == (
        ids["XW-ADMIT-MINIMAL-DEPTH"].photon_cutoff + 1
    )
    equals = ids["XW-ADMIT-DEPTH-EQUALS-TAIL-WINDOW"]
    assert equals.exact_depth == equals.tail_window and equals.admitted
    # The m* <= m_t constraint is SCOPED to settings where (X) fails: the same
    # arithmetic is admitted where (X) holds and refused where it does not.
    unused = ids["XW-ADMIT-DEPTH-EXCEEDS-UNUSED-TAIL-WINDOW"]
    refused = ids["XW-REFUSE-DEPTH-EXCEEDS-TAIL-WINDOW"]
    assert unused.exact_depth > unused.tail_window and unused.admitted
    assert refused.exact_depth > refused.tail_window and not refused.admitted
    assert unused.predicate_x and not refused.predicate_x
    # The opt-out is admitted with NEITHER conditional tolerance.
    opt_out = ids["XW-ADMIT-NO-DEPTH-NO-CONDITIONAL-TOLERANCES"]
    assert opt_out.exact_depth is None and opt_out.admitted
    assert not opt_out.eps_eig_declared and not opt_out.eps_6_declared
    # ONE reason string covers both missing tolerances.
    missing = [
        case
        for case in EXACT_WINDOW_VALIDATION_CASES
        if case.refusal_reason == "exact_window_declared_without_required_tolerance"
    ]
    assert len(missing) == 2
    assert {case.eps_eig_declared for case in missing} == {True, False}
    assert {case.eps_6_declared for case in missing} == {True, False}
    # Def. def:tolmap's closing enumeration classifies all four, and adds NO
    # threshold: the depth constraints are kind (a), the conditional presence
    # kind (b), and r_6 kind (c).
    kinds = dict(TOLMAP_OTHER_VALIDATION_KINDS_0_3_0)
    domain_kind = next(k for k in kinds if "declared domain" in k)
    combinatorial = next(k for k in kinds if "combinatorial" in k)
    residual_kind = next(k for k in kinds if "residual tests" in k)
    assert "m*_t > N" in kinds[domain_kind]
    assert "m*_t <= m_t" in kinds[domain_kind]
    assert any("eps_eig and eps_6" in entry for entry in kinds[combinatorial])
    assert "r_6 against eps_6" in kinds[residual_kind]
    # The 0.2.0 copy is INCOMPLETE and is marked, never edited.
    assert supersession_0_3_0("TOLMAP_OTHER_VALIDATION_KINDS").kind == "incomplete"
    for _, entries in TOLMAP_OTHER_VALIDATION_KINDS:
        assert not any("m*_t" in entry for entry in entries)
    # eps_eig is not a test of any kind, and the table says so.
    assert {name for name, _ in TOLMAP_NOT_A_TEST_0_3_0} == {"eps_eig", "eps_6"}


@pytest.mark.contract
def test_def_tolmap_iv_decides_c_alone_and_the_band_is_refused() -> None:
    """Def. def:tolmap (iv) at 0.3.0: item (iv) wins, Eq. eq:tolmapband refused."""
    eps_1 = TOLMAP_IV_BAND_FIXTURE["eps_1"]
    eps_2 = TOLMAP_IV_BAND_FIXTURE["eps_2"]
    assert eps_1 > eps_2, "the band is only reachable at eps_1 > eps_2"
    assert (-eps_1, -eps_2) == TOLMAP_IV_BAND
    assert TOLMAP_IV_BAND_CLOSED_AT == (True, False)
    low, high = TOLMAP_IV_BAND
    for case in TOLMAP_IV_PRECEDENCE_CASES:
        assert (case.eps_1, case.eps_2) == (eps_1, eps_2), case.case_id
        assert case.in_band == (low <= case.c < high), case.case_id
        assert case.item_iv_admits == (case.c >= -case.eps_2), case.case_id
        assert case.losing_reading_admits == (case.c >= -case.eps_1), case.case_id
        # ITEM (iv) WINS, at every case.
        assert case.admitted == case.item_iv_admits, case.case_id
        # THE BAND IS EXACTLY WHERE THE TWO READINGS DISAGREE.
        assert case.in_band == (
            case.losing_reading_admits and not case.item_iv_admits
        ), case.case_id
        # No reason string is invented: the contract spells none here.
        assert case.refusal_reason is None, case.case_id
        assert len(case.derives_from) > 200, case.case_id
    # The band is bracketed: inside (twice, including the CLOSED left end),
    # at the OPEN right end, below it, and at the lossless anchor c = 0.
    inside = [case for case in TOLMAP_IV_PRECEDENCE_CASES if case.in_band]
    assert len(inside) == 2
    assert all(not case.admitted for case in inside)
    assert any(case.c == -eps_1 for case in inside), "the left endpoint is IN"
    right = next(case for case in TOLMAP_IV_PRECEDENCE_CASES if case.c == -eps_2)
    assert not right.in_band, "the right endpoint is OUT of the band"
    assert right.admitted, "the right endpoint is admitted"
    band_cases = TOLMAP_IV_PRECEDENCE_CASES
    assert any(case.c < -eps_1 and not case.admitted for case in band_cases)
    assert any(case.c == 0 and case.admitted for case in TOLMAP_IV_PRECEDENCE_CASES)
    # At eps_1 = eps_2 the band is EMPTY -- which is the MAIN fixture, and is
    # why these cases carry one of their own.
    a, b, interval, empty = TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS
    assert a == b and empty and interval == (-a, -b)
    assert TOLERANCE_FIXTURE_0_3_0["eps_1"] == TOLERANCE_FIXTURE_0_3_0["eps_2"]
    assert not any(-a <= case.value < -b for case in TOLMAP_IV_C_CASES), (
        "a 0.2.0 c case cannot be in an empty band"
    )
    # STEP (3), QUANTITATIVELY: the stated error term would be FALSE on an
    # admitted value under the losing reading.
    cost = dict(TOLMAP_IV_BAND_COST)
    k_minus_1 = cost["K - 1, at the BB84 receiver's K = 4"]
    assert k_minus_1 == 3
    stated = cost["the STATED even-n bound (K-1) eps_2^2, at eps_2 = 1/1000"]
    assert stated == k_minus_1 * eps_2**2
    losing = cost[
        "the bound that would be TRUE under the losing reading, "
        "(K-1) eps_1^2 at eps_1 = 1/100"
    ]
    assert losing == k_minus_1 * eps_1**2
    assert cost["the factor between them, (eps_1 / eps_2)^2"] == (eps_1 / eps_2) ** 2
    assert losing / stated == (eps_1 / eps_2) ** 2
    actual = cost[
        "the ACTUAL even-n = 2 overshoot at the admitted band value "
        "c = -1/200, namely (K-1) gamma |c|^2"
    ]
    band_value = next(
        case.c
        for case in TOLMAP_IV_PRECEDENCE_CASES
        if case.in_band and case.c != -eps_1
    )
    assert band_value == Fraction(-1, 200)
    assert actual == k_minus_1 * abs(band_value) ** 2
    excess = cost[
        "by what factor that actual overshoot exceeds the STATED bound (K-1) eps_2^2"
    ]
    assert excess == actual / stated > 1, "the stated bound would not be violated"
    # Rem. rem:cdirection's bounds STAY IN eps_2 and are not restated: the
    # 0.2.0 cases are not marked.
    assert not is_superseded_0_3_0("C_DIRECTION_CASES")
    assert not is_superseded_0_3_0("TOLMAP_IV_C_CASES")
    # The four derivation steps, the losing reading and the refusal.
    assert len(TOLMAP_IV_DERIVATION) == 6
    steps = {label for label, _ in TOLMAP_IV_DERIVATION}
    assert {"(1)", "(2)", "(3)", "(4)"} <= steps
    assert any("the reading that loses" in label for label in steps)
    assert any("refusal" in label for label in steps)
    text = dict(TOLMAP_IV_DERIVATION)
    assert "NO IMPLICATION" in text["(2)"] or "NO IMPLICATION" in text["(2)"].upper()
    assert "NOT REDUNDANT ON ROUTE (i)" in text["(2)"]
    # AND NO BEHAVIOUR CHANGES: every row of the table is True.
    assert len(TOLMAP_IV_NO_BEHAVIOUR_CHANGE) == 7
    assert all(unchanged for _, unchanged in TOLMAP_IV_NO_BEHAVIOUR_CHANGE)
    # The refusal is frozen WITHOUT a spelling, deliberately.
    unspelled = next(
        case
        for case in REFUSAL_CASES_0_3_0
        if case.case_id == "REF-TOLMAP-IV-C-REFUSED-NO-SPELLING"
    )
    assert unspelled.reason is None and not unspelled.reason_is_verbatim
    assert not unspelled.emits_artifact
    assert "deliberately adds none" in unspelled.derives_from.lower()
    assert "NO SPELLING IS INVENTED" in unspelled.derives_from


@pytest.mark.contract
def test_the_0_3_0_supersession_list_is_well_formed() -> None:
    """Every 0.3.0 mark names a site, a reason and a replacement, and resolves."""
    names = [entry.name for entry in SUPERSEDED_BY_0_3_0]
    assert len(set(names)) == len(names)
    module = sys.modules["registry_receiver_povm"]
    kinds = set()
    for entry in SUPERSEDED_BY_0_3_0:
        assert entry.superseded_by == "0.3.0", entry.name
        assert entry.kind in {"superseded", "incomplete", "reframed"}, entry.name
        kinds.add(entry.kind)
        assert entry.contract_site.strip(), entry.name
        assert len(entry.reason) > 120, entry.name
        # THIS PASS MARKS WHOLE OBJECTS AND NEVER ROWS, because marking a row
        # would mean writing a field an earlier pass froze.
        assert entry.name == entry.table, entry.name
        assert hasattr(module, entry.table), entry.table
        assert entry.replacement, entry.name
        for replacement in entry.replacement:
            assert _resolves(module, replacement), (entry.name, replacement)
            assert not is_superseded_0_3_0(replacement), (entry.name, replacement)
    assert kinds == {"superseded", "incomplete", "reframed"}
    for entry in SUPERSEDED_BY_0_3_0:
        assert is_superseded_0_3_0(entry.name)
        assert supersession_0_3_0(entry.name) is entry
    assert not is_superseded_0_3_0("BOUND_DATA_CASES")
    assert supersession_0_3_0("BOUND_DATA_CASES") is None
    # NOT ONE ROW anywhere carries a 0.3.0 in-place mark, which is what makes
    # this pass purely additive in the strictest sense.
    for table in (
        RESIDUAL_CASES,
        REFUSAL_CASES,
        DARK_CASES,
        BOUND_DATA_CASES,
        RP_ORACLES,
    ):
        for row in table:
            assert getattr(row, "superseded_by", None) in {None, "0.2.0"}, row
    # The two lists are disjoint in what they mark IN PLACE and additive in
    # what they name: the 0.2.0 record is untouched.
    assert len(SUPERSEDED_BY_0_2_0) == 17
    # The list is complete in both directions.
    assert len(NOT_SUPERSEDED_BY_0_3_0) >= 8
    for what, why in NOT_SUPERSEDED_BY_0_3_0:
        assert what.strip() and len(why) > 60, what
    # And the headline: NOT ONE FROZEN NUMBER is superseded.
    numeric_tables = (
        "BOUND_DATA_CASES",
        "RESIDUAL_CASES",
        "DARK_CASES",
        "RESIDUAL5_CASES",
        "TOLMAP_I_CASES",
        "TOLMAP_II_RANK_CASES",
        "TOLMAP_IV_C_CASES",
        "TOLMAP_V_CONTRACTIVITY_CASES",
        "C_DIRECTION_CASES",
        "DARK_SLACK_CASES",
        "COLLAPSE_SLACK_CASES",
        "PMC_BRANCH_CASES",
        "FOCK_CASES",
        "CATALOGUE_CASES",
        "INSTRUMENT_CASES",
        "POVM_BLOCK_CASES",
        "EFFICIENCY_CASES",
        "PROBE_CASES",
    )
    for name in numeric_tables:
        assert not is_superseded_0_3_0(name), name


@pytest.mark.contract
def test_no_0_3_0_marked_object_is_asserted_unmarked_by_a_run_b_test() -> None:
    """The 0.3.0 hand-off invariant, alongside the 0.2.0 one.

    A run-B test file that has moved to THIS amendment -- which it declares by
    naming ``receiver-povm@0.3.0`` -- may not assert a 0.3.0-marked object
    unless it names ``SUPERSEDED_BY_0_3_0`` itself. A file still pinned to
    0.2.0 is pre-amendment; its references are the pending work run A recorded,
    and the scan may only SHRINK from that list, never grow.
    """
    marked = [entry.name for entry in SUPERSEDED_BY_0_3_0]
    files = sorted(
        list((REPO_ROOT / "tests" / "golden").glob("test_receiver_povm_*.py"))
        + list((REPO_ROOT / "tests" / "unit").glob("test_receiver_*.py"))
        + list((REPO_ROOT / "tests" / "property").glob("test_receiver_povm_*.py"))
    )
    assert files, "no run-B receiver tests found"
    found: set[tuple[str, str]] = set()
    for path in files:
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPO_ROOT).as_posix()
        on_amendment = AMENDMENT_SPEC_VERSION_MARKER_0_3_0 in source
        acknowledges = (
            "SUPERSEDED_BY_0_3_0" in source or "is_superseded_0_3_0" in source
        )
        for name in marked:
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])"
            if not re.search(pattern, source):
                continue
            found.add((relative, name))
            if acknowledges:
                continue
            assert not on_amendment, (
                f"{relative} has moved to {AMENDMENT_SPEC_VERSION_MARKER_0_3_0} and "
                f"still asserts the superseded {name!r} without naming "
                "SUPERSEDED_BY_0_3_0; retire or rewrite it"
            )
    pending = set(PENDING_RETIREMENT_AT_RUN_B_0_3_0)
    assert found <= pending, sorted(found - pending)
    for relative, name in PENDING_RETIREMENT_AT_RUN_B_0_3_0:
        assert (REPO_ROOT / relative).exists(), relative
        assert is_superseded_0_3_0(name), name


@pytest.mark.contract
def test_the_0_3_0_oracle_entries_cover_the_amendment() -> None:
    """Five new entries, RP-S to RP-W, on RC8 and RC9."""
    new = {
        "O-RP-EXACT-BLOCK": ("RC8",),
        "O-RP-EXACT-WINDOW": ("RC8",),
        "O-RP-RES6": ("RC9",),
        "O-RP-EXACT-WINDOW-VALIDATION": ("RC8", "RC9"),
        "O-RP-TOLMAP-IV": ("RC9",),
    }
    ids = {entry.oracle_id for entry in RP_ORACLES}
    assert set(new) <= ids
    assert len(RP_ORACLES) == 23
    for oracle_id, claims in new.items():
        entry = rp_oracle(oracle_id)
        assert entry.claims == claims, oracle_id
        assert entry.kind in KINDS, oracle_id
        assert entry.assurance == "estimate", oracle_id
        assert len(entry.derivation) > 600, oracle_id
        assert entry.superseded_by is None, oracle_id
        for banned in INADMISSIBLE_SOURCES:
            assert banned not in entry.derivation + entry.subject, oracle_id
    # The two claims the amendment touches are exactly RC8 and RC9, which is
    # what contract.tex Section 1.1 says of each of its seven items.
    touched = {claim for oracle_id in new for claim in rp_oracle(oracle_id).claims}
    assert touched == {"RC8", "RC9"}
    # The four entries that carry hypotheses name Eq. eq:mcpos or Ass. ass:eig.
    with_hypotheses = [
        rp_oracle(oracle_id) for oracle_id in new if rp_oracle(oracle_id).hypotheses
    ]
    assert len(with_hypotheses) == 4
    blob = " ".join(h for entry in with_hypotheses for h in entry.hypotheses)
    assert "eq:mcpos" in blob and "ass:eig" in blob


@pytest.mark.contract
def test_not_one_float_appears_in_the_0_3_0_frozen_values() -> None:
    """The 0.3.0 substrate is exact too."""
    for name, obj in (
        ("TOLERANCE_FIXTURE_0_3_0", TOLERANCE_FIXTURE_0_3_0),
        ("TOLMAP_IV_BAND_FIXTURE", TOLMAP_IV_BAND_FIXTURE),
        ("TOLMAP_IV_BAND", TOLMAP_IV_BAND),
        ("TOLMAP_IV_BAND_COST", TOLMAP_IV_BAND_COST),
        ("TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS", TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS),
        ("TOLMAP_IV_PRECEDENCE_CASES", TOLMAP_IV_PRECEDENCE_CASES),
        ("EXACT_BLOCK_CASES", EXACT_BLOCK_CASES),
        ("EXACT_COMPOSITE_CASES", EXACT_COMPOSITE_CASES),
        ("EXACT_WINDOW_CASES", EXACT_WINDOW_CASES),
        ("EXACT_WINDOW_VALIDATION_CASES", EXACT_WINDOW_VALIDATION_CASES),
        ("RESIDUAL6_CASES", RESIDUAL6_CASES),
        ("RESIDUAL6_REQUEST_PRESENCE", RESIDUAL6_REQUEST_PRESENCE),
        ("NO_WORSE_CASES", NO_WORSE_CASES),
        ("MIXED_SETTING_CASES", MIXED_SETTING_CASES),
        (
            "BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0",
            BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0,
        ),
        ("OPT_IN_INVARIANT", OPT_IN_INVARIANT),
        ("ASSUMPTION_ROWS_0_3_0", ASSUMPTION_ROWS_0_3_0),
        ("REFUSAL_CASES_0_3_0", REFUSAL_CASES_0_3_0),
        ("SUPERSEDED_BY_0_3_0", SUPERSEDED_BY_0_3_0),
    ):
        _no_floats(obj, name)
