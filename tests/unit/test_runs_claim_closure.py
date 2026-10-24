"""A run record names the claim graph its number rests on, as the checker computes it.

PRINCIPLES.md section 2.1 and spec/architecture.md 4.4: the assumption manifest
names "the claim ids of the theorem and its transitive ``uses`` closure" and
every assumption short id in it. The record reads them from the generated
package data (``certiqs_key.domain.claim_closure``, a generated table); this test holds
one produced record's closure against ``harness/check_claims.py`` itself -- the walk
``check_claims --assumptions <root>`` prints -- so the table and the checker cannot say
two things. The table's freshness is ``tests/harness/test_generate_claim_closure.py``.
"""

from __future__ import annotations

import importlib.util
import sys
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

import pytest

from certiqs_key.domain.claim_closure import (
    CLAIM_ROOTS,
    ClaimClosureError,
    claim_closure,
    module_version,
)
from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs import RunConfig
from certiqs_key.runs.pipeline import SliceRefusal
from certiqs_key.runs.record import record_run

pytestmark = pytest.mark.contract

ROOT = Path(__file__).resolve().parents[2]


def _check_claims() -> ModuleType:
    """Return ``harness/check_claims.py``, loaded by path.

    As in tests/harness/test_claim_implements_resolve.py: a test package is
    also named ``harness``, so the tool is loaded from its file.
    """
    name = "_harness_check_claims"
    if name in sys.modules:
        return sys.modules[name]
    # The tool imports harness.contract_navigation, and under pytest the name
    # `harness` is the test package: register the tool's module under that
    # dotted name first, so the import finds it in sys.modules.
    helper = "harness.contract_navigation"
    if helper not in sys.modules:
        helper_spec = importlib.util.spec_from_file_location(
            helper, ROOT / "harness" / "contract_navigation.py"
        )
        assert helper_spec is not None and helper_spec.loader is not None
        sys.modules[helper] = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(sys.modules[helper])
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "harness" / "check_claims.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _expected(repo: object, root: str) -> dict[str, object]:
    """Return the walk of ``check_claims --assumptions <root>``, table-shaped."""
    tool = _check_claims()
    claims = [root, *tool.uses_closure(repo, root)]
    short_ids = {
        short_id
        for claim_id in claims
        for short_id in repo.claims[claim_id].assumes  # type: ignore[attr-defined]
    }
    return {
        "claims": claims,
        "assumptions": {
            short_id: repo.assumptions[short_id].claim_id  # type: ignore[attr-defined]
            for short_id in sorted(short_ids)
        },
    }


def test_an_unknown_root_is_an_error_not_an_empty_closure() -> None:
    """4.4: a manifest that cannot be generated is an error that refuses the result."""
    with pytest.raises(ClaimClosureError):
        claim_closure("meat-core/thm:no-such-claim")
    with pytest.raises(ClaimClosureError):
        module_version("no-such-module")


def test_every_root_a_result_may_name_is_in_the_table() -> None:
    for root in CLAIM_ROOTS:
        assert claim_closure(root)["claims"][0] == root


@pytest.mark.requires_qics
def test_a_record_s_claim_closure_is_the_checker_s(tmp_path: Path) -> None:
    """One produced record, each of its roots against the checker's walk."""
    from instances.bb84.specification import bb84_specification
    from instances.common.honest.depolarized_bell_pair import honest_provider

    from certiqs_key.runs.pipeline import run_slice
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    config = RunConfig(
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        declared_tolerance=0.0,
        model={"qber": F(1, 50)},
    )
    outcome = run_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        honest_provider=honest_provider(F(1, 50)),
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=config.parameters,
        oracle=QicsSectorChoiOracle(),
        directory=tmp_path / "bundle",
        created_by="test",
        declared_tolerance=0.0,
        alpha=1.5,
        run_id=config.digest(),
    )
    assert not isinstance(outcome, SliceRefusal), outcome
    payload = record_run(outcome, config, created_by="test").payload
    manifest = payload["assumption_manifest"]
    closure = manifest["claim_closure"]
    # The closure is keyed by every root of the run, per module in the manifest's
    # `roots`, the key-rate result's claim_roots among them -- not by those alone.
    every_root = list(
        dict.fromkeys(root for roots in manifest["roots"].values() for root in roots)
    )
    assert list(closure) == every_root
    assert set(payload["stages"]["key_rate"]["claim_roots"]) <= set(closure)
    assert manifest["roots"]["meat-core"][: len(
        payload["stages"]["key_rate"]["claim_roots"]
    )] == payload["stages"]["key_rate"]["claim_roots"]
    assert closure, "a completed run names at least one claim root"

    repo = _check_claims().load_repo(ROOT)
    assert not repo.errors
    for root, entry in closure.items():
        assert entry == _expected(repo, root), root
    statistics = repo.modules["statistics"].meta["version"]
    assert manifest["module_versions"]["statistics"] == f"statistics@{statistics}"
