"""What a real record's assumption manifest must say about its bound values.

WHY THIS EXISTS. meat-core binds the declaration it read back off the bundle,
whose labels are wire IDs (``runs/identifiers.py``: ``(Z,0)`` travels as
``_Z_0_``), so on every route whose labels the wire renames A-SRC would carry
``alice_povm`` twice -- the transmitter's in the declared spelling and the
engine's in the wire one -- and A-FIXED and A-CONFORM would bind an acceptance
alphabet the record's acceptance stage does not hold. The route fixtures dock
without the wire step, so no unit test can see it; these assertions run on
records of real solves (``tests/integration``), and check the record pointers
with them.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from certiqs_key.runs.report import build_report

__all__ = ["assert_bindings_in_declared_spelling"]

#: The engine's binding names rendered with no record pointer.
_POINTED: frozenset[str] = frozenset({"ideal_hash", "bracket_iterates"})


def assert_bindings_in_declared_spelling(document: Mapping[str, Any]) -> None:
    """Assert one value per bound name, every alphabet in the declared spelling.

    * every entry of the manifest binds each name once (a per-party row once
      per party);
    * every ``acceptance_set`` binding's alphabet is the acceptance stage's
      ``outcomes``, the declared acceptance values;
    * A-SRC, where engaged, carries one ``alice_povm``, whose alphabet is the
      compiled source's ``signal_alphabet`` (Alice's outcomes on a trusted
      source are its letters) and which every emitter of the row's
      ``alice_povm`` shares;
    * in the report built from the record, ``ideal_hash`` and
      ``bracket_iterates`` carry a record pointer.
    """
    payload = document["payload"]
    manifest = payload["assumption_manifest"]
    outcomes = list(payload["stages"]["acceptance_construction"]["outcomes"])
    for entry in manifest["assumptions"]:
        # A name once per emitting station and party: a row emitted once per
        # party (A-LAB, record 0.30.0) binds its own `party` at each, and a
        # station's binding that names its own party (A-SEQ's "measured
        # system") differs per station; every
        # other name is bound once.
        names = [
            (
                binding["name"],
                *(
                    tuple(sorted(
                        str(item.get(field)) for item in binding["emitted_by"]
                        if item.get(field) is not None
                    ))
                    for field in ("station", "party")
                ),
            )
            for binding in entry["bindings"]
        ]
        assert len(names) == len(set(names)), (entry["short_id"], names)
        for binding in entry["bindings"]:
            if binding["name"] == "acceptance_set":
                assert binding["value"]["alphabet"] == outcomes, entry["short_id"]
    for entry in manifest["assumptions"]:
        if entry["short_id"] != "A-SRC":
            continue
        povms = [b for b in entry["bindings"] if b["name"] == "alice_povm"]
        assert len(povms) == 1, povms
        (povm,) = povms
        assert povm["value"]["alphabet"] == list(
            payload["compiled"]["source"]["signal_alphabet"]
        )
        row_emitters = {emitter["module"] for emitter in entry["emitted_by"]}
        assert {item["module"] for item in povm["emitted_by"]} == (
            row_emitters & {"transmitter", "meat-core"}
        )
    report = build_report(document)
    for module_entries in (
        [e for g in report["sections"]["assumptions"]["groups"]
         for f in g["families"] for e in (f["head"], *f["members"])],
        report["sections"]["numerics"]["entries"],
    ):
        for entry in module_entries:
            for binding in entry["bindings"]:
                if binding["name"] in _POINTED:
                    assert binding.get("pointer"), (entry["short_id"], binding)
