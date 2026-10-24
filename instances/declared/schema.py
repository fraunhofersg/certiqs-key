"""Write, or check, the protocol document's JSON Schema from the models.

    python -m instances.declared.schema           # rewrite the committed schema
    python -m instances.declared.schema --check   # exit 1 if it is stale

WHY GENERATED. The schema is what an agent reads to write a document (the MCP
server serves it), and the models in :mod:`instances.declared.model`
are what the reader enforces. A hand-kept schema would be a second statement of
the format that drifts from the first; generating it makes it a view
(PRINCIPLES.md section 7), and ``tests/unit/test_declared_schema.py`` fails when
the committed file is not the one these models produce.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from instances.declared.model import FORMAT, ProtocolDocument

__all__ = ["SCHEMA_PATH", "main", "schema", "schema_text"]

#: Where the generated schema is committed.
SCHEMA_PATH = Path(__file__).resolve().parent / "protocol-document.schema.json"


def schema() -> dict[str, Any]:
    """Return the JSON Schema of a protocol document."""
    generated = ProtocolDocument.model_json_schema()
    return {
        **generated,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "certiqs-key/protocol-document.schema.json",
        "description": (
            f"A {FORMAT} document, format_version 1. Generated from "
            "instances/declared/model.py by python -m instances.declared.schema; "
            "do not edit. The format guide is instances/declared/README.md."
        ),
    }


def schema_text() -> str:
    """Return the schema as the committed file holds it."""
    return json.dumps(schema(), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the schema, or with ``--check`` report whether it is current."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if stale")
    arguments = parser.parse_args(argv)
    text = schema_text()
    if arguments.check:
        current = SCHEMA_PATH.exists() and SCHEMA_PATH.read_bytes() == text.encode(
            "utf-8"
        )
        if not current:
            print(f"{SCHEMA_PATH} is stale; run python -m instances.declared.schema")
            return 1
        return 0
    SCHEMA_PATH.write_bytes(text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
