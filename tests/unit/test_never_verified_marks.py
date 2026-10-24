"""The never-verifiable marks of reductions and receiver, read three ways.

A-MEAS and A-ROUND-SQ in reductions, A-NOSEL and A-ROUND in receiver, are
marked never verifiable.

Each assumption carries a ``verification`` header field (spec/claim-format.md
section 3.2), and the two requirements below point at it instead of listing
the set:

* ``reductions/req:never-verified-assumptions``: "The engine marks as never
  verifiable (never_verified) the row, in the assumption ledger, of every
  assumption that the engine never verifies, as that assumption's own text
  says, whether this contract, one of its submodules or another module states
  it" -- the six core rows, A-MEAS, A-ROUND-SQ, A-RECV, A-PROBE, A-TSM and
  A-CONST, and the transmitter's A-SRC and A-SEQ, whose owner's field is
  ``never`` (A-DIM's setting is ``def:system-setting``, a definition; the
  adversary's registers are the round model's and no row, meat-core's
  A-EVE-DIM being superseded; there is no A-SOUND);
* ``receiver/req:decidable-assumptions``: "The assumptions that the engine
  never verifies, each saying so in its own text ..., form
  never_verified_set" -- A-TRUST, A-PASSIVE, A-VAC, A-MODES, A-THRESH,
  A-PORT, A-EXACT, A-NOSEL, A-ROUND and A-EIG.

A-ACYC, A-PROBE-DIAG and A-FLOAT are not assumptions
(A-ACYC is condition (E2) of
``receiver/def:graph``, A-PROBE-DIAG is ``def:probe`` with
``req:probe-diagonal-admission``, A-FLOAT is ``def:evaluation-model``), so
every row the receiver's ledger carries is never verified.

The sets below are written out by hand from those fields, not read off the
code. Each is checked against the code's constant, the interface's list and
the rows an emission actually carries; tests/unit/test_never_verified_agree.py
holds every such place to the field itself. No number is involved: the marks
change what a ledger says of a row, never a value.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from certiqs_key.receiver.reasons import NEVER_VERIFIED as RECEIVER_NEVER_VERIFIED
from certiqs_key.reductions.artifact import assumption_ledger
from certiqs_key.reductions.reasons import CORE_ASSUMPTIONS
from certiqs_key.reductions.reasons import NEVER_VERIFIED as REDUCTIONS_NEVER_VERIFIED

ROOT = Path(__file__).resolve().parents[2]

#: reductions/req:never-verified-assumptions, the core's rows, by short id.
REDUCTIONS_CLAIMED = {
    "A-MEAS",
    "A-ROUND-SQ",
    "A-RECV",
    "A-PROBE",
    "A-TSM",
    "A-CONST",
}

#: The rows reductions takes from another module, each with its owner's mark:
#: the transmitter's A-SRC and A-SEQ and foundations'
#: A-SNAP
#: (ass:snapped-measurement, ``verification: never``), the row
#: req:emission-record carries exactly where a block rests on a snap. A-SNAP
#: is not among the code's CORE_ASSUMPTIONS, which every emission carries: its
#: row is SNAPPED_MEASUREMENT_ROW, appended where its presence rule holds.
REDUCTIONS_ASSUMED_ALWAYS = {"A-SRC", "A-SEQ"}
REDUCTIONS_ASSUMED = REDUCTIONS_ASSUMED_ALWAYS | {"A-SNAP"}

#: receiver/req:decidable-assumptions, by short id.
RECEIVER_CLAIMED = {
    "A-TRUST",
    "A-PASSIVE",
    "A-VAC",
    "A-MODES",
    "A-THRESH",
    "A-PORT",
    "A-EXACT",
    "A-NOSEL",
    "A-ROUND",
    "A-EIG",
}


def _interface(module: str) -> dict[str, Any]:
    path = ROOT / "spec" / "modules" / module / "interface.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def test_the_reductions_marks_are_the_requirement_s_rows() -> None:
    from certiqs_key.reductions.reasons import SNAPPED_MEASUREMENT_ROW

    assert {str(member) for member in REDUCTIONS_NEVER_VERIFIED} == (
        REDUCTIONS_CLAIMED | REDUCTIONS_ASSUMED_ALWAYS
    )
    assert SNAPPED_MEASUREMENT_ROW.never_verifiable is True
    document = _interface("reductions")
    assert set(document["never_verified"]["core"]) == REDUCTIONS_CLAIMED
    assert set(document["never_verified"]["assumed_from_another_module"]) == (
        REDUCTIONS_ASSUMED
    )
    ledger = next(
        row for row in document["outputs"] if row["name"] == "assumption_ledger"
    )
    marked = {row["id"] for row in ledger["core_rows"] if row["never_verifiable"]}
    assert marked == REDUCTIONS_CLAIMED
    assumed = {
        row["id"]
        for row in ledger["assumed_from_another_module"]
        if row["never_verifiable"]
    }
    assert assumed == REDUCTIONS_ASSUMED
    # The code's rows carry the same flag row for row, and A-SRC and A-SEQ,
    # another module's, carry their owner's mark.
    in_code = {row.identifier for row in CORE_ASSUMPTIONS if row.never_verifiable}
    assert in_code == REDUCTIONS_CLAIMED | REDUCTIONS_ASSUMED_ALWAYS


def test_the_emitted_reductions_ledger_carries_the_marks() -> None:
    """What reaches a run manifest is the emitted row, so the flag is read there."""
    ledger = assumption_ledger({}, "receiver-povm@0.3.0")
    flags = {entry.assumption_id: entry.never_verifiable for entry in ledger}
    for identifier in ("A-MEAS", "A-ROUND-SQ", "A-RECV"):
        assert flags[identifier] is True, identifier
    assert "A-EVE-DIM" not in flags
    for identifier in ("A-PROBE", "A-TSM", "A-CONST", "A-SRC", "A-SEQ"):
        assert flags[identifier] is True, identifier
    assert {key for key, flag in flags.items() if flag} == (
        REDUCTIONS_CLAIMED | REDUCTIONS_ASSUMED_ALWAYS
    )


def test_the_receiver_marks_are_the_requirement_s_set() -> None:
    assert {str(member) for member in RECEIVER_NEVER_VERIFIED} == RECEIVER_CLAIMED
    assert set(_interface("receiver")["never_verified_set"]) == RECEIVER_CLAIMED
    # Every row of the ledger is a member (there are no `decided` rows).
    assert {str(member) for member in RECEIVER_NEVER_VERIFIED} == {
        str(row["id"])
        for row in next(
            output
            for output in _interface("receiver")["outputs"]
            if output["name"] == "assumption_ledger"
        )["rows"]
    }


def test_the_emitted_receiver_ledger_carries_the_marks() -> None:
    from receiver_povm_support import bb84_channel_only_request

    from certiqs_key.receiver import construct_receiver

    emission = construct_receiver(bb84_channel_only_request())
    assert emission.artifact is not None
    flags = {
        str(row.assumption_id): row.never_verified
        for row in emission.artifact.assumption_ledger
    }
    assert {key for key, flag in flags.items() if flag} == RECEIVER_CLAIMED
    assert flags["A-NOSEL"] is True
    assert flags["A-ROUND"] is True
    assert flags["A-EXACT"] is True
    assert all(flags.values())
