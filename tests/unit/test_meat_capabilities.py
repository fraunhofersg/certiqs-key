"""The capability probe, and what it does when the oracle is not there.

spec/architecture.md 7.3: "The probe refuses: if the proof instance requires a
capability the active oracle does not declare, the run stops with a capability
error -- never a silent fallback to a solver that cannot represent the
problem."  QICS is an OPTIONAL extra on purpose: that behaviour is only
testable in an environment where the oracle is genuinely absent. This
environment has QICS installed, so the absence is simulated at the one seam the
implementation goes through -- ``qics_available`` -- rather than by
uninstalling it. The seam exists for exactly this reason: no module in
``certiqs_key.solvers`` imports ``qics`` at import time.
"""

from __future__ import annotations

from typing import Any

import pytest

from certiqs_key.solvers.capabilities import probe as probe_module
from certiqs_key.solvers.capabilities.probe import (
    QICS_INSTALL_HINT,
    SECTOR_CHOI_REQUIREMENTS,
    Capability,
    CapabilityError,
    OracleCapabilities,
    describe,
    probe_environment,
    qics_available,
    qics_version,
    require_capabilities,
)

FULL = OracleCapabilities(
    name="test-oracle",
    version="0",
    capabilities=frozenset(Capability),
)


@pytest.mark.contract
def test_the_required_capability_set_is_the_architecture_spec_s() -> None:
    """spec/architecture.md 7.4, minimum requirements for the backbone slice."""
    assert (
        frozenset(
            {
                Capability.COMPLEX_HERMITIAN_PSD,
                Capability.DIRECT_SUM_SECTORS,
                Capability.CHOI_FORM,
                Capability.EQUALITY_ROWS,
            }
        )
        == SECTOR_CHOI_REQUIREMENTS
    )


@pytest.mark.contract
def test_a_declared_capability_set_that_covers_the_requirement_passes() -> None:
    """The positive case; everything below is the negative one."""
    require_capabilities(FULL, SECTOR_CHOI_REQUIREMENTS, sector_dims=[2, 4])


@pytest.mark.contract
@pytest.mark.parametrize("missing", sorted(SECTOR_CHOI_REQUIREMENTS))
def test_an_undeclared_capability_stops_the_run(missing: Capability) -> None:
    """Each required capability is independently load-bearing."""
    declared = OracleCapabilities(
        name="partial",
        version="0",
        capabilities=frozenset(SECTOR_CHOI_REQUIREMENTS) - {missing},
    )
    with pytest.raises(CapabilityError, match=str(missing)):
        require_capabilities(declared, SECTOR_CHOI_REQUIREMENTS)


@pytest.mark.contract
def test_every_missing_capability_is_named_at_once() -> None:
    """A user is not sent round the loop one capability at a time."""
    declared = OracleCapabilities(name="empty", version="0", capabilities=frozenset())
    with pytest.raises(CapabilityError) as failure:
        require_capabilities(declared, SECTOR_CHOI_REQUIREMENTS)
    for capability in SECTOR_CHOI_REQUIREMENTS:
        assert str(capability) in str(failure.value)


@pytest.mark.contract
def test_a_declared_block_size_bound_is_enforced() -> None:
    """`max_sector_dim` is a declaration like any other, and it is checked."""
    declared = OracleCapabilities(
        name="small",
        version="0",
        capabilities=frozenset(Capability),
        max_sector_dim=3,
    )
    require_capabilities(declared, SECTOR_CHOI_REQUIREMENTS, sector_dims=[1, 3])
    with pytest.raises(CapabilityError, match="max_sector_dim"):
        require_capabilities(declared, SECTOR_CHOI_REQUIREMENTS, sector_dims=[1, 4])


@pytest.mark.contract
def test_the_probe_records_the_backend_identity_as_data() -> None:
    """spec/architecture.md 7.3: versions and declared capabilities, no handles."""
    record = probe_environment(FULL)
    assert set(record) >= {"python", "numpy", "scipy", "qics", "oracle"}
    assert record["oracle"]["name"] == "test-oracle"
    assert sorted(record["oracle"]["capabilities"]) == sorted(
        str(item) for item in Capability
    )
    import json

    json.dumps(record)  # data only: a solver handle would not survive this
    assert "oracle test-oracle" in describe(record)


@pytest.mark.contract
def test_the_absent_oracle_path_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """The case the optional extra exists for: QICS is not installed.

    The adapter refuses to be constructed at all, with the install instruction,
    instead of raising an ImportError from the middle of a solve.
    """
    from certiqs_key.solvers.oracles.qics import adapter

    monkeypatch.setattr(adapter, "qics_available", lambda: False)
    with pytest.raises(CapabilityError) as failure:
        adapter.QicsSectorChoiOracle()
    assert "not installed" in str(failure.value)
    assert "oracle-qics" in str(failure.value)
    assert QICS_INSTALL_HINT in str(failure.value)


@pytest.mark.contract
def test_the_probe_reports_the_install_hint_when_the_oracle_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """spec/architecture.md 7.3 and 8: detect and report; never install."""
    monkeypatch.setattr(probe_module, "qics_available", lambda: False)
    monkeypatch.setattr(probe_module, "qics_version", lambda: None)
    record = probe_environment(None)
    assert record["qics"] is None
    assert record["oracle"] is None
    assert record["qics_hint"] == QICS_INSTALL_HINT
    assert "pip install" in record["qics_hint"]


@pytest.mark.contract
def test_the_solver_refuses_to_run_without_the_capabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The end-to-end fail-closed path: probe first, numerics never.

    A stand-in oracle that declares nothing is handed to the solver; the run
    stops at the probe, before any subproblem is built. The stand-in records
    whether it was ever asked to minimize anything -- it must not have been.
    """
    import sys
    from pathlib import Path

    oracle_tree = Path(__file__).resolve().parents[1] / "oracles"
    if str(oracle_tree) not in sys.path:
        sys.path.insert(0, str(oracle_tree))
    from dummy_bundles import build_bundle
    from toy_declarations import toy

    from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
    from certiqs_key.solvers.frank_wolfe import solve

    calls: list[Any] = []

    class DeclaresNothing:
        """An oracle that declares nothing and must never be called."""

        def capabilities(self) -> OracleCapabilities:
            return OracleCapabilities(
                name="declares-nothing", version="0", capabilities=frozenset()
            )

        def minimize(self, problem: Any) -> Any:
            calls.append(problem)
            raise AssertionError("the probe should have stopped the run")

    declaration = declaration_from_bundle(build_bundle(toy("TOY-1")))
    with pytest.raises(CapabilityError):
        solve(declaration, DeclaresNothing())
    assert calls == []


@pytest.mark.contract
@pytest.mark.requires_qics
def test_the_qics_oracle_declares_what_the_subproblem_needs() -> None:
    """With the extra installed, the declared set covers the requirement."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    assert qics_available()
    declared = QicsSectorChoiOracle().capabilities()
    assert declared.capabilities >= SECTOR_CHOI_REQUIREMENTS
    assert Capability.INEQUALITY_ROWS in declared.capabilities
    assert declared.version == qics_version()
    require_capabilities(declared, SECTOR_CHOI_REQUIREMENTS)
