"""Write the frozen snapshot of the Python instances' last run.

Runnable only at the development commit the snapshot was made at, which is
not in the public history: there ``instances/{bb84,optical_bb84,decoy_bb84,
bbm92}`` were still Python and ``tests/integration/
test_declared_equivalence.py`` still held its grid (``CASES``), and neither
exists in this repository. It is kept beside the snapshot so that what the
snapshot holds, and how it was stripped, can be read (``README.md``).

Usage, from the root of a checkout of that commit::

    python <path to this file> <output folder>
"""

from __future__ import annotations

import copy
import gzip
import json
import sys
from pathlib import Path
from typing import Any

#: The wall-clock fields of a record, as the equivalence gate stripped them.
CLOCK = frozenset(
    {
        "wall_time_s",
        "elapsed_seconds",
        "preparation_seconds",
        "solver_seconds",
        "seconds",
        "timings",
    }
)


def _clock(key: str, container: dict[str, Any]) -> bool:
    if key in CLOCK or key == "provenance":
        return True
    ident = container.get("id")
    return (
        key in ("id", "digest")
        and isinstance(ident, str)
        and ident.startswith("key_rate_result:")
    )


def strip(value: Any) -> Any:
    """Drop the wall clock and provenance at any depth (the gate's rule)."""
    if isinstance(value, dict):
        return {k: strip(v) for k, v in value.items() if not _clock(k, value)}
    if isinstance(value, list):
        return [strip(item) for item in value]
    return value


def outcome_of(surface: Any, overrides: dict[str, Any]) -> dict[str, Any]:
    """Return a surface's configuration payload and preparation, or its refusal."""
    from tests.support.declared_equivalence import copied

    from certiqs_key.runs.record import preparation_record

    try:
        config = surface.default_config(**copied(copy.deepcopy(overrides)))
    except Exception as failure:
        return {
            "config": None,
            "raised": [type(failure).__name__, str(getattr(failure, "reason", ""))],
        }
    entry: dict[str, Any] = {"config": json.loads(json.dumps(config.to_payload()))}
    try:
        outcome = surface.preparation(config)
    except Exception as failure:
        entry["raised"] = [type(failure).__name__, str(getattr(failure, "reason", ""))]
        return entry
    record = preparation_record(outcome)
    # A Python instance recorded ``None`` here; a template its document.
    record.pop("protocol_document", None)
    entry["kind"] = type(outcome).__name__
    entry["record"] = strip(json.loads(json.dumps(record)))
    return entry


def main() -> None:
    """Write one ``<instance>.json.gz`` per instance into the output folder."""
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, ".")
    import tests.integration.test_declared_equivalence as gate
    from instances import surface_of

    snapshot: dict[str, dict[str, Any]] = {}
    for instance, label, overrides in gate.CASES:
        python = surface_of(instance)
        entry = snapshot.setdefault(
            instance,
            {
                "instance": instance,
                "static": {
                    "descriptor": python.DESCRIPTOR.as_payload(),
                    "parameters": [spec.as_payload() for spec in python.PARAMETERS],
                    "presets": [preset.as_payload() for preset in python.PRESETS],
                },
                "cases": {},
            },
        )
        assert label not in entry["cases"], (instance, label)
        entry["cases"][label] = outcome_of(python, overrides)
    for instance, entry in snapshot.items():
        text = json.dumps(entry, indent=None, sort_keys=True, separators=(",", ":"))
        data = json.loads(text)
        assert data == json.loads(json.dumps(entry))
        with (
            (out / f"{instance}.json.gz").open("wb") as raw,
            gzip.GzipFile(
                filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0
            ) as handle,
        ):
            handle.write(text.encode("utf-8"))
        print(instance, len(entry["cases"]), "cases")


if __name__ == "__main__":
    main()
