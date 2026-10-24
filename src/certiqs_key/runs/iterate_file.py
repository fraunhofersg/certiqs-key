"""A run's final iterate as a file beside its record: the seed of a warm start.

A run can start from a prior point's FINAL ITERATE
(:mod:`certiqs_key.solvers.frank_wolfe.joint_options`, ``warm_start``). The
iterate is a list of complex matrices, one per joint sector, and it is
persisted as ONE CANONICAL JSON FILE beside the run record, which the record
references by the sha256 of the file's bytes.

WHY A SIDECAR AND WHY JSON
==========================
* NOT INLINE: a record is read by people and by a frontend, and the matrices
  are the part of a run nobody reads. The record carries the hash; the file
  carries the numbers.
* JSON AND NOT ``.npz``: the house encoding of a record, and the one the
  record already uses for a matrix (``choi_input_basis``'s ``real``/``imag``
  lists). CANONICAL JSON (sorted keys, no whitespace, the run tier's one
  :func:`~certiqs_key.runs.config.canonical_json`) is byte-deterministic, so
  the same iterate hashes to the same seed on every machine -- a NumPy archive
  carries zip timestamps and would not. Python's float repr round-trips
  binary64 exactly, so nothing is rounded on the way through.
* THE FILE SAYS WHAT FEASIBLE SET IT LIVES IN: the source mode, the joint
  sectors with their block dimensions (the matrices' own shapes), how each
  block splits into its Alice factor and its sector factor (``layout``: equal
  sizes do not fix the split), the number of constraint rows the producing
  declaration had and the digest of those rows (``rows_sha256``,
  :func:`~certiqs_key.solvers.frank_wolfe.joint_options.constraint_rows_digest`),
  which is what
  :func:`~certiqs_key.solvers.frank_wolfe.joint_options.warm_start_point`
  compares before it admits the seed, together with the seed's content.
* TWO HASHES, TWO JOBS. The file's sha256 is what a configuration names and
  what the loader verifies before reading; the seed's IDENTITY in the solver
  is the sha256 of its blocks' canonical bytes, derived from the numbers
  (``joint_options.blocks_digest``), so it does not depend on the file format.

Format ``2`` added ``layout``; a format ``1`` file (written before it) still
loads and is compared by block shapes alone. Format ``3`` adds
``rows_sha256``, which lets a seed with constraint rows chain to a point with
the same rows; an older file loads without it, so it seeds only points without
rows.
"""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np

from certiqs_key.meat_core.objective.joint import JointSector
from certiqs_key.meat_core.objective.linalg import as_matrix
from certiqs_key.runs.config import RunConfig, WarmStartSeed, canonical_json
from certiqs_key.runs.errors import RunInputReason, RunInputValueError
from certiqs_key.runs.pipeline import SliceResult
from certiqs_key.runs.record import RunRecord
from certiqs_key.solvers.frank_wolfe.general_keyrate import GeneralKeyRateResult
from certiqs_key.solvers.frank_wolfe.joint_options import WarmStart
from certiqs_key.solvers.oracles.joint_rows import joint_label, split_joint_label

#: The file's kind and format version; the version moves with its shape.
ITERATE_KIND = "joint-final-iterate"
ITERATE_FORMAT_VERSION = "3"
#: Every format the loader reads.
READABLE_FORMAT_VERSIONS = ("1", "2", "3")
#: The file name a run writes beside its ``record.json``.
ITERATE_FILE_NAME = "final-iterate.json"


class WarmStartFileError(RunInputValueError):
    """A seed file that is not the one named, or not a seed at all.

    Its code is a member of :class:`~certiqs_key.runs.errors.RunInputReason`.
    """


def iterate_payload(
    result: GeneralKeyRateResult, *, config_digest: str | None = None
) -> dict[str, Any]:
    """Return the final iterate of a general run as a JSON-ready mapping.

    Raises:
        ValueError: if the result carries no final iterate.
    """
    if result.final_iterate is None:
        raise ValueError("this result carries no final iterate")
    gates = result.certificate["security_gates"]
    blocks = {
        joint_label(pair): {
            "real": as_matrix(block).real.tolist(),
            "imag": as_matrix(block).imag.tolist(),
        }
        for pair, block in result.final_iterate.items()
    }
    return {
        "kind": ITERATE_KIND,
        "format_version": ITERATE_FORMAT_VERSION,
        "source_mode": str(gates["source_mode"]),
        "constraint_count": int(gates["constraint_count"]),
        "layout": (
            None
            if result.final_iterate_layout is None
            else {
                key: dict(value) for key, value in result.final_iterate_layout.items()
            }
        ),
        "rows_sha256": result.final_iterate_rows_sha256,
        "producing_config_digest": config_digest,
        "blocks": blocks,
    }


def write_final_iterate(
    path: Path, result: GeneralKeyRateResult, *, config_digest: str | None = None
) -> str:
    """Write the final iterate as canonical JSON and return its sha256."""
    data = canonical_json(iterate_payload(result, config_digest=config_digest)).encode(
        "utf-8"
    )
    path.write_bytes(data)
    return sha256(data).hexdigest()


def attach_final_iterate(
    record: RunRecord, outcome: object, config: RunConfig, directory: Path
) -> RunRecord:
    """Write a run's final iterate beside its record and name it in the record.

    THE ONE WRITER OF ``payload.final_iterate``.
    The step decides WHETHER a run has a final iterate -- a completed run (a
    :class:`~certiqs_key.runs.pipeline.SliceResult`
    whose ``key_rate`` is a
    :class:`~certiqs_key.solvers.frank_wolfe.general_keyrate.GeneralKeyRateResult`
    carrying one) -- and, where it does, writes :data:`ITERATE_FILE_NAME` into
    ``directory`` with :func:`write_final_iterate` and returns ``record`` with
    ``payload.final_iterate = {"file": ITERATE_FILE_NAME, "sha256": ...}``.
    ``file`` is relative to the directory the record is written in, which is
    ``directory``; ``sha256`` is the file's, the hash a warm start names.

    A run without one -- a refusal -- gets neither the file
    nor the key, and ``record`` is returned unchanged. There is one writer, so
    that a consumer wanting its records to seed warm starts too does not copy
    it and give the key two writers that could drift.

    Raises:
        FileExistsError: if ``directory`` already holds a final iterate; a
            record's seed is never silently replaced.
    """
    if not (
        isinstance(outcome, SliceResult)
        and outcome.key_rate.final_iterate is not None
    ):
        return record
    path = directory / ITERATE_FILE_NAME
    if path.exists():
        raise FileExistsError(f"a final iterate already exists at {path}")
    digest = write_final_iterate(
        path, outcome.key_rate, config_digest=config.digest()
    )
    payload = dict(record.payload)
    payload["final_iterate"] = {"file": ITERATE_FILE_NAME, "sha256": digest}
    return replace(record, payload=payload)


def seed_of(path: Path) -> WarmStartSeed:
    """Return the configuration's name for a seed file: its path and hash.

    ``path`` may be the file or the directory of a prior point, in which case
    :data:`ITERATE_FILE_NAME` inside it is meant.
    """
    file = path / ITERATE_FILE_NAME if path.is_dir() else path
    try:
        data = file.read_bytes()
    except OSError as error:
        raise WarmStartFileError(
            f"no warm-start seed can be read at {file.as_posix()}: {error}",
            reason=RunInputReason.WARM_START_FILE_MISSING,
        ) from error
    return WarmStartSeed(file=file.as_posix(), sha256=sha256(data).hexdigest())


def load_warm_start(seed: WarmStartSeed) -> WarmStart:
    """Read a seed file, refusing one whose bytes are not the named ones.

    Raises:
        WarmStartFileError: ``warm_start_file_missing`` when there is no file
            at the locator, ``warm_start_hash_mismatch`` when the file's sha256
            is not the seed's, ``warm_start_not_an_iterate`` when the file is
            not a final-iterate file of a known format version.
    """
    try:
        data = Path(seed.file).read_bytes()
    except OSError as failure:
        raise WarmStartFileError(
            f"no warm-start file can be read at {seed.file}: {failure}",
            reason=RunInputReason.WARM_START_FILE_MISSING,
        ) from failure
    actual = sha256(data).hexdigest()
    if actual != seed.sha256:
        raise WarmStartFileError(
            f"the warm-start file {seed.file} hashes to {actual}, not to the "
            f"named {seed.sha256}; the seed is identified by its hash and this "
            "is a different file",
            reason=RunInputReason.WARM_START_HASH_MISMATCH,
        )
    payload = json.loads(data)
    if (
        payload.get("kind") != ITERATE_KIND
        or payload.get("format_version") not in READABLE_FORMAT_VERSIONS
    ):
        raise WarmStartFileError(
            f"{seed.file} is not a {ITERATE_KIND} file of a format in "
            f"{READABLE_FORMAT_VERSIONS}",
            reason=RunInputReason.WARM_START_NOT_AN_ITERATE,
        )
    blocks: dict[JointSector, Any] = {
        split_joint_label(label): np.asarray(entry["real"], dtype=np.float64)
        + 1j * np.asarray(entry["imag"], dtype=np.float64)
        for label, entry in payload["blocks"].items()
    }
    return WarmStart(
        blocks=blocks,
        source_mode=str(payload["source_mode"]),
        constraint_count=int(payload["constraint_count"]),
        file_sha256=seed.sha256,
        source=seed.file,
        layout=payload.get("layout"),
        rows_sha256=payload.get("rows_sha256"),
    )


__all__ = [
    "ITERATE_FILE_NAME",
    "ITERATE_FORMAT_VERSION",
    "ITERATE_KIND",
    "READABLE_FORMAT_VERSIONS",
    "WarmStartFileError",
    "attach_final_iterate",
    "iterate_payload",
    "load_warm_start",
    "seed_of",
    "write_final_iterate",
]
