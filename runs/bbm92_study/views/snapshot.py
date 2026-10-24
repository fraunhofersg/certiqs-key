r"""Take the snapshot the figures are drawn from: two device sets, and their extracts.

    python -m runs.bbm92_study.views.snapshot --set realistic \
        --viewmodels <build>/realistic \
        --prepared <build>/realistic/inputs/prepare.json \
        [--record <run-record.json>] \
        --frontend-commit <builders commit> --engine-pin <engine commit> \
        --out runs/bbm92_study/data/viewmodels

The figure generator reads one folder and nothing else, so that a figure in the
whitepaper can be traced to the files it was drawn from. The folder holds one
subfolder per device set of the study (:data:`SETS`, ``perfect`` and
``realistic``) and ``snapshot.json``, which names, per set, the pins and the
files. This script fills one set's subfolder and its entry:

* the view models of :data:`VIEW_MODELS` (``protocol_map.json``,
  ``optics.json``, ``povm.json`` and ``povm-dark-composed.json``) are copied
  from ``--viewmodels``, written by the view-model builders
  from the preparation of the set's headline point, with line endings
  normalised to LF;
* ``preparation-extract.json`` holds what the figures need of that
  preparation and the view models do not carry: the declared detector
  parameters per party, the declared test fraction, and each station's
  efficiency normalization (the factored loss and every port's declared and
  compiled efficiency), which the POVM is drawn at;
* ``record-extract.json``, with ``--record``, holds the few fields of the
  set's run record the statistics figure reads: the honest distribution and
  the acceptance box per outcome, the round count and the completeness budget.
  A run record is about a megabyte; the extract is what a figure needs.
  Without ``--record`` the set keeps the record extract its entry names, which
  may be a shared one at the folder's top (:func:`read_snapshot` returns it,
  and the generator says when its engine commit is not the set's pin).

WHERE THE BOX COMES FROM
========================
A record of the current schema carries the box in its
``acceptance_construction`` stage (``box``, ``{label: {lower, upper}}``, exact
rationals), beside the outcomes and the honest distribution, and the extract
reads it there; the record may be gzipped. An older record lacks it: the box
is then part of the declaration handed to the solver, in the run's operator
bundle beside the record (``payload.stages.bundle.directory``, under a folder
named after the record). Its ``acceptance_set.data.box_bounds`` is
``[lower, upper]`` in the order of the bundle's ``alphabets.acceptance_value``,
whose names are the record's outcome labels with every non-alphanumeric
character replaced by ``_``. The extract pairs the two lists by position and
refuses if any name disagrees.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

__all__ = [
    "SETS",
    "SET_FILES",
    "SNAPSHOT",
    "VIEW_MODELS",
    "extract_preparation",
    "extract_record",
    "main",
    "read_snapshot",
]

SETS: tuple[str, ...] = ("perfect", "realistic")
"""The study's device sets, one subfolder each."""

VIEW_MODELS: tuple[str, ...] = (
    "protocol_map.json",
    "optics.json",
    "povm.json",
    "povm-dark-composed.json",
)
"""The view models the figures read, as the builders write them."""

PREPARATION = "preparation-extract.json"
RECORD = "record-extract.json"
SNAPSHOT = "snapshot.json"

SET_FILES: Mapping[str, str] = {
    "protocol_map": "protocol_map.json",
    "optics": "optics.json",
    "povm": "povm.json",
    "povm_dark": "povm-dark-composed.json",
    "preparation": PREPARATION,
}
"""A set's files, by the key the generator reads them under; the record
extract is found through ``snapshot.json`` (key ``record_extract``)."""

_PARTIES: Mapping[str, str] = {"A": "alice", "B": "bob"}
"""The run configuration's per-party prefixes (``alice_efficiency``, ...)."""


def _bundle_name(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", label)


def _detectors(device: Mapping[str, Any]) -> dict[str, Any]:
    """Return a configuration's detector parameters, keyed by party."""
    return {
        party: {
            "efficiency": device.get(f"{prefix}_efficiency", {}),
            "dark_count": device.get(f"{prefix}_dark_count", {}),
        }
        for party, prefix in _PARTIES.items()
        if f"{prefix}_efficiency" in device or f"{prefix}_dark_count" in device
    }


def _record_box(stage: Mapping[str, Any], outcomes: Sequence[str]) -> tuple[
    list[Any], list[Any]
]:
    """Return the box from the record's own stage, in the outcomes' order."""
    box = stage["box"]
    if set(box) != set(outcomes):
        raise ValueError("the record's box and its outcomes name different labels")
    return (
        [box[label]["lower"] for label in outcomes],
        [box[label]["upper"] for label in outcomes],
    )


def extract_record(
    record: Mapping[str, Any],
    manifest: Mapping[str, Any] | None,
    origin: Mapping[str, str],
) -> dict[str, Any]:
    """Return the record extract the statistics figure reads.

    The box is the record's own (``acceptance_construction.box``) where it
    carries one, else the bundle ``manifest``'s (module docstring).
    """
    payload = record["payload"]
    stage = payload["stages"]["acceptance_construction"]
    outcomes = [str(o) for o in stage["outcomes"]]
    honest = stage["honest_distribution"]
    if "box" in stage:
        lower, upper = _record_box(stage, outcomes)
        return _extract(payload, stage, outcomes, honest, lower, upper, origin)
    if manifest is None:
        raise ValueError("the record carries no box and no bundle manifest was given")
    names = [str(n) for n in manifest["payload"]["alphabets"]["acceptance_value"]]
    lower, upper = manifest["payload"]["declaration"]["acceptance_set"]["data"][
        "box_bounds"
    ]
    if (
        len(names) != len(outcomes)
        or len(lower) != len(outcomes)
        or len(upper) != len(outcomes)
    ):
        raise ValueError(
            "the bundle's acceptance alphabet and the record's outcomes differ "
            "in length"
        )
    for label, name in zip(outcomes, names, strict=True):
        if _bundle_name(label) != name:
            raise ValueError(f"outcome {label!r} does not match bundle name {name!r}")
    return _extract(payload, stage, outcomes, honest, lower, upper, origin)


def _extract(
    payload: Mapping[str, Any],
    stage: Mapping[str, Any],
    outcomes: Sequence[str],
    honest: Mapping[str, Any],
    lower: Sequence[Any],
    upper: Sequence[Any],
    origin: Mapping[str, str],
) -> dict[str, Any]:
    config = payload["config"]
    device = config.get("device", {})
    return {
        "kind": "bbm92-study-record-extract",
        "origin": dict(origin),
        "engine_commit": payload["provenance"]["engine"]["git_commit"],
        "rounds": config["rounds"],
        "completeness_budget": config["completeness_budget"],
        "endpoint_rule": stage.get("endpoint_rule"),
        "test_fraction": device.get("test_fraction"),
        "outcomes": [
            {
                "label": label,
                "honest": str(honest[label]),
                "box_lower": float(Fraction(str(lo))),
                "box_upper": float(Fraction(str(hi))),
            }
            for label, lo, hi in zip(outcomes, lower, upper, strict=True)
        ],
        "device": _detectors(device),
    }


def extract_preparation(
    prepared: Mapping[str, Any], origin: Mapping[str, str]
) -> dict[str, Any]:
    """Return the preparation extract: declared detectors, test fraction, normalization.

    ``prepared`` is the builders' preparation of the set's point
    (``config`` the run configuration sent, ``stations[]`` the compiled
    stations with their receivers' ``efficiency_record``).
    """
    if prepared.get("refused"):
        raise ValueError("the preparation was refused; there is nothing to draw")
    device = prepared["config"].get("device", {})
    normalization = []
    for station in prepared["stations"]:
        record = station["receiver"]["efficiency_record"]["normalization"]
        normalization.append(
            {
                "station": int(station["index"]),
                "party": station.get("party"),
                "factored_loss": str(record["factored_loss"]),
                "factor_declared": bool(record["factor_declared"]),
                "applied": bool(record["applied"]),
                "ports": [
                    {
                        "port": str(p["port"]),
                        "declared": str(p["declared_efficiency"]),
                        "compiled": str(p["compiled_efficiency"]),
                    }
                    for p in record["ports"]
                ],
            }
        )
    return {
        "kind": "bbm92-study-preparation-extract",
        "origin": dict(origin),
        "config_digest": prepared.get("config_digest"),
        "rounds": prepared["config"].get("rounds"),
        "test_fraction": device.get("test_fraction"),
        "device": _detectors(device),
        "normalization": normalization,
    }


def _load(path: Path) -> Any:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads(path.read_text(encoding="utf-8"))


def read_snapshot(folder: Path) -> dict[str, Any]:
    """Return the parsed snapshot: ``{"snapshot": ..., "sets": {set: {key: ...}}}``.

    Each set maps the keys of :data:`SET_FILES` to parsed JSON, plus
    ``record_extract`` (parsed, or ``None`` where the entry names none) and
    ``files``, the path of each file relative to ``folder``, for the
    generated files' headers.
    """
    snapshot = _load(folder / SNAPSHOT)
    sets: dict[str, Any] = {}
    for name, entry in snapshot["sets"].items():
        files = {key: f"{name}/{file}" for key, file in SET_FILES.items()}
        data: dict[str, Any] = {
            key: _load(folder / path) for key, path in files.items()
        }
        record = entry.get("record_extract")
        data["record_extract"] = _load(folder / record) if record else None
        if record:
            files["record_extract"] = record
        data["files"] = files
        sets[name] = data
    return {"snapshot": snapshot, "sets": sets}


def _dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Copy one set's view models, write its extracts and its snapshot entry."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--set", required=True, choices=SETS, dest="device_set")
    parser.add_argument("--viewmodels", type=Path, required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--record", type=Path)
    parser.add_argument(
        "--bundle", type=Path, help="the record's bundle folder, if not beside it"
    )
    parser.add_argument("--frontend-commit", required=True)
    parser.add_argument("--engine-pin", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    folder = args.out / args.device_set
    folder.mkdir(parents=True, exist_ok=True)
    for name in VIEW_MODELS:
        text = (args.viewmodels / name).read_text(encoding="utf-8")
        (folder / name).write_text(
            text.replace("\r\n", "\n"), encoding="utf-8", newline="\n"
        )
    prepared = _load(args.prepared)
    _dump(
        folder / PREPARATION,
        extract_preparation(prepared, {"prepared": args.prepared.name}),
    )
    path = args.out / SNAPSHOT
    snapshot: dict[str, Any] = (
        _load(path)
        if path.is_file()
        else {"kind": "bbm92-study-viewmodel-snapshot", "sets": {}}
    )
    entry: dict[str, Any] = dict(snapshot["sets"].get(args.device_set, {}))
    entry.update(
        {
            "engine_pin": args.engine_pin,
            "frontend_commit": args.frontend_commit,
            "view_models": list(VIEW_MODELS),
            "preparation_extract": f"{args.device_set}/{PREPARATION}",
        }
    )
    entry.setdefault("record_extract", None)
    if args.record is not None:
        record = _load(args.record)
        stage = record["payload"]["stages"]["acceptance_construction"]
        # sweep/point/record.json.gz, as the study's data folder holds it
        origin = {"record": "/".join(args.record.parts[-3:])}
        manifest = None
        if "box" not in stage:
            bundle = args.bundle or (
                args.record.parent
                / args.record.stem
                / record["payload"]["stages"]["bundle"]["directory"]
            )
            manifest = _load(bundle / "manifest.json")
            origin["bundle"] = f"{args.record.stem}/{bundle.name}/manifest.json"
        _dump(folder / RECORD, extract_record(record, manifest, origin))
        entry["record_extract"] = f"{args.device_set}/{RECORD}"
    snapshot["sets"][args.device_set] = entry
    _dump(path, snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
