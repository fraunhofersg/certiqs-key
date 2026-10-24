"""The certified evaluation's per-point reasons, spelled alike everywhere.

WHY THIS EXISTS. A per-point reason is named in four places: the frank-wolfe
interface (``certified_evaluation.reasons.per_point``), the constants the
evaluation raises (``certified_record``), and the two per-point enums of the
run record's schema (``points`` and ``companion_points``). A reason added to
some of them and not the others (``boxed_form_inconsistent`` was added to all
four by hand) would let a record that the engine writes fail its own schema,
or leave a reason the interface does not document.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from certiqs_key.solvers.frank_wolfe import certified_record

ROOT = Path(__file__).resolve().parents[2]
INTERFACE = ROOT / "spec" / "modules" / "meat-core" / "frank-wolfe" / "interface.yaml"
SCHEMA = ROOT / "src" / "certiqs_key" / "runs" / "record.schema.json"


def _interface_per_point() -> list[str]:
    def find(node: Any) -> list[str] | None:
        if isinstance(node, dict):
            reasons = node.get("reasons")
            if isinstance(reasons, dict) and "per_point" in reasons:
                return list(reasons["per_point"])
            for value in node.values():
                found = find(value)
                if found is not None:
                    return found
        return None

    found = find(yaml.safe_load(INTERFACE.read_text(encoding="utf-8")))
    assert found is not None, "no reasons.per_point in the frank-wolfe interface"
    return found


def _schema_point_enums() -> list[list[str]]:
    enums: list[list[str]] = []

    def walk(node: Any, key: str | None) -> None:
        if isinstance(node, dict):
            reasons = node.get("items", {}).get("properties", {}).get("reasons", {})
            if key in ("points", "companion_points") and "enum" in reasons.get(
                "items", {}
            ):
                enums.append(list(reasons["items"]["enum"]))
            for name, value in node.items():
                walk(value, name)
        elif isinstance(node, list):
            for value in node:
                walk(value, key)

    walk(json.loads(SCHEMA.read_text(encoding="utf-8")), None)
    return enums


def test_the_per_point_reasons_agree_everywhere() -> None:
    per_point = _interface_per_point()
    assert len(per_point) == len(set(per_point))
    enums = _schema_point_enums()
    assert len(enums) == 2
    for enum in enums:
        assert set(enum) == set(per_point)
    constants = {
        value
        for name, value in vars(certified_record).items()
        if name.isupper() and isinstance(value, str)
    }
    assert set(per_point) <= constants
    assert "boxed_form_inconsistent" in per_point
