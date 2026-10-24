"""Capability probing and the fail-closed gate (spec/architecture.md 7.3)."""

from __future__ import annotations

from certiqs_key.solvers.capabilities.probe import (
    SECTOR_CHOI_REQUIREMENTS,
    SPECTRAPLEX_REQUIREMENTS,
    Capability,
    CapabilityError,
    OracleCapabilities,
    probe_environment,
    qics_available,
    require_capabilities,
)

__all__ = [
    "SECTOR_CHOI_REQUIREMENTS",
    "SPECTRAPLEX_REQUIREMENTS",
    "Capability",
    "CapabilityError",
    "OracleCapabilities",
    "probe_environment",
    "qics_available",
    "require_capabilities",
]
