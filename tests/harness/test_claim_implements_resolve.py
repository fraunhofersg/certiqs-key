"""Every ``implements`` field resolves, and the landed code is bound to a claim.

MOTIVATION, AND THE ERROR CLASS IT CATCHES. PRINCIPLES.md section 5 asks each
claim file to carry "when one exists, the code symbol that implements it", and
the implementation verifier's first duty is "for every ``implements`` link: the
function does what the claim states". A claim whose implementing symbol is
named only in a docstring cannot be re-reviewed when the symbol moves, and a
claim whose ``implements`` field names a symbol that has been renamed or
deleted points the verifier at nothing. ``harness.check_claims`` checks the
FORM of the field -- that it reads ``python.module.path:symbol`` -- and, below
status ``implemented``, does not resolve it; this test resolves it.

WHAT IT DOES NOT DEMAND. A claim with no ``implements`` field is not a
failure: most claims are definitions and remarks with no symbol of their own,
and binding one lazily is what the field is for. What the second test pins is
the SPECIFIC claims the reductions code binds, so that a later edit that drops
one is visible.

REMOVABILITY. A submodule declared removable may be absent from
a tree while its claim files are still present -- that is the state the
removability check runs in. There
the whole implementing PACKAGE is gone rather than one symbol, which this test
asserts and then passes over: a missing package is the removal, a missing
symbol inside a present package is the defect. Its removability list deletes
its claim files too (its interface.yaml, ``removability``), and a
bound claim absent together with its module directory is passed over by the
same reasoning.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _check_claims() -> ModuleType:
    """Return ``harness/check_claims.py``, loaded BY PATH.

    ``tests/harness/`` is itself a package named ``harness``, so a plain
    ``import harness.check_claims`` from inside it resolves to the test
    package and not to the tool. The other tests in this directory avoid the
    collision by running the tool as a subprocess; this one needs the loaded
    claims rather than the exit code, so it loads the file directly. The path
    is the only thing this indirection adds.
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

#: The claims the reductions code binds. Each names the symbol that
#: implements it.
REDUCTIONS_BOUND_CLAIMS = (
    "reductions/def:reduction-instance",
    "reductions/def:emitnorm",
    "reductions/thm:emit",
    "reductions/cor:entries",
    "reductions/thm:chain",
    "reductions/cor:flag-instance",
    "reductions/cor:register-instance",
    "reductions/wpfss/prop:flat-instance",
    "reductions/wpfss/cor:emitted-flat",
)


def _claims() -> dict[str, object]:
    return dict(_check_claims().load_repo(ROOT).claims)


def _package_present(module_path: str) -> bool:
    """Whether the implementing module is in this tree at all.

    A removable submodule's package may be absent; a symbol inside a present
    package may not.
    """
    try:
        return importlib.util.find_spec(module_path) is not None
    except ModuleNotFoundError:
        return False


def test_every_implements_field_resolves() -> None:
    absent: list[str] = []
    for claim_id, claim in sorted(_claims().items()):
        target = claim.header.get("implements")  # type: ignore[attr-defined]
        if not target:
            continue
        module_path, _, symbol = str(target).partition(":")
        if not _package_present(module_path):
            absent.append(f"{claim_id} -> {target}")
            continue
        module = importlib.import_module(module_path)
        assert hasattr(module, symbol), f"{claim_id} -> {target}"
    # Whatever was absent was absent AS A PACKAGE -- the removal of a removable
    # submodule -- and not as a symbol inside a package this tree has.
    for entry in absent:
        module_path = entry.split(" -> ", 1)[1].split(":", 1)[0]
        parent = module_path.rsplit(".", 1)[0]
        assert not _package_present(parent), entry


@pytest.mark.parametrize("claim_id", REDUCTIONS_BOUND_CLAIMS)
def test_the_reductions_code_is_bound_to_its_claim(claim_id: str) -> None:
    claims = _claims()
    # A REMOVED SUBMODULE TAKES ITS CLAIM FILES WITH IT: its removability list
    # deletes the spec directory as well as the package (its interface.yaml,
    # `removability.spec`). Its bound claims are then absent WITH their
    # directory, which is the removal; a claim absent from a directory that is
    # still there is the defect, and the lookup below reports it.
    module_dir = ROOT / "spec" / "modules" / claim_id.rsplit("/", 1)[0]
    if claim_id not in claims and not module_dir.is_dir():
        pytest.skip(f"{module_dir.relative_to(ROOT).as_posix()} is not in this tree")
    claim = claims[claim_id]
    target = claim.header.get("implements")  # type: ignore[attr-defined]
    assert target, claim_id
    module_path, _, symbol = str(target).partition(":")
    assert symbol, target
    if not _package_present(module_path):
        pytest.skip(f"{module_path} is not present in this tree")
    assert hasattr(importlib.import_module(module_path), symbol), target
