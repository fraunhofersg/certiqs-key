"""The operator bundle on disk: a directory of ``manifest.json`` + ``arrays.h5``.

spec/architecture.md 4.1 is explicit about what the first milestone needs:
"a **file format**: something that writes a problem out and reads a result back
with its dimensions, bases and orderings intact. Not an artifact store". So
this module writes two files into a directory and reads them back, and that is
the whole of it. There is no content hash, no artifact id, no provenance block
and no store; those are deferred to spec/future-scope.md 1, and 4.1's
forward-compatibility rule is honoured by *omitting* them rather than by
inventing weaker versions now.

Round trip::

    directory/
      manifest.json    envelope, alphabets, function tables, array descriptors
      arrays.h5        numbers only

Writing validates before it writes anything, so a bundle on disk that failed
validation does not exist. Reading validates after loading, so a bundle that
loads is one every consumer may rely on structurally. Both directions fail
closed (spec/architecture.md 2.5, 3.6).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from certiqs_key.domain._base import BundleValidationError, RetiredSchemaVersionError
from certiqs_key.domain.arrays import ArrayPayload
from certiqs_key.domain.hdf5 import read_arrays, write_arrays
from certiqs_key.domain.manifest import (
    DEFERRED_ENVELOPE_FIELDS,
    RETIRED_SCHEMA_VERSION_REASON,
    RETIRED_SCHEMA_VERSIONS,
    SUPPORTED_SCHEMA_VERSIONS,
    OperatorBundleManifest,
)
from certiqs_key.domain.validation import collect_descriptors, validate_bundle

#: The manifest file inside a bundle directory.
MANIFEST_FILENAME = "manifest.json"

#: The array file inside a bundle directory.
ARRAYS_FILENAME = "arrays.h5"


@dataclass(frozen=True, eq=False)
class OperatorBundle:
    """A manifest together with the arrays it declares.

    ``arrays`` is keyed by dataset path, exactly as the descriptors in
    ``manifest`` name them.
    """

    manifest: OperatorBundleManifest
    arrays: Mapping[str, ArrayPayload]


def parse_manifest(document: Any) -> OperatorBundleManifest:
    """Parse a decoded JSON document into a manifest.

    Raises:
        RetiredSchemaVersionError: if the document is stamped a schema version
            this reader does not accept
            (spec/architecture.md 2.9). It is
            checked FIRST and as its own type: a caller that meets an old
            bundle needs to know that the fix is to regenerate it from its
            instance, and that is a different act from fixing a malformed one.
        BundleValidationError: if the document is not a valid manifest, or if
            it carries one of the envelope fields spec/architecture.md 4.1
            defers.
    """
    if isinstance(document, dict):
        declared = document.get("schema_version")
        if isinstance(declared, str) and declared in RETIRED_SCHEMA_VERSIONS:
            raise RetiredSchemaVersionError(
                f"manifest declares schema_version {declared!r}, which this "
                f"reader does not accept; it reads "
                f"{list(SUPPORTED_SCHEMA_VERSIONS)} and nothing else "
                "(spec/architecture.md 2.8). A retired version can "
                "express a full-space operator payload, which is why read "
                "support was dropped. The bundle is not converted: re-blocking "
                "an operator would require inventing a sector map, which is a "
                "mathematical claim and not a format conversion. Regenerate "
                "the bundle from its instance",
                reason=RETIRED_SCHEMA_VERSION_REASON,
                declared_version=declared,
                supported_versions=tuple(SUPPORTED_SCHEMA_VERSIONS),
                retired_versions=tuple(RETIRED_SCHEMA_VERSIONS),
            )
        deferred = [name for name in DEFERRED_ENVELOPE_FIELDS if name in document]
        if deferred:
            raise BundleValidationError(
                f"manifest carries deferred envelope fields {deferred}; "
                "content-addressing is deferred to spec/future-scope.md 1 and no "
                "field may be given a meaning incompatible with the one it "
                "will carry then (spec/architecture.md 4.1). Omit them"
            )
    try:
        return OperatorBundleManifest.model_validate(document)
    except ValidationError as error:
        raise BundleValidationError(_format_validation_error(error)) from error


def _format_validation_error(error: ValidationError) -> str:
    """Render a Pydantic error as messages naming the offending key paths."""
    lines = []
    for detail in error.errors():
        location = ".".join(str(part) for part in detail["loc"]) or "<root>"
        lines.append(f"{location}: {detail['msg']}")
    return "manifest is not well-formed:\n  " + "\n  ".join(lines)


def write_bundle(directory: Path, bundle: OperatorBundle) -> None:
    """Write ``bundle`` into ``directory``, validating first, all or nothing.

    Both files are staged under temporary names inside ``directory`` and moved
    into place only once both have been written. Any failure -- validation, a
    malformed array, a full disk, a failing rename -- leaves the directory as
    it was found, so a later attempt at the same path is not blocked by the
    wreckage of an earlier one. That is what makes this module's own invariant
    true: a bundle that failed to validate does not exist, not even in part.

    Raises:
        BundleValidationError: if the bundle does not validate, or if either
            target file already exists. Overwriting is not offered: silently
            replacing half of a bundle is the kind of repair
            spec/architecture.md 3.6 forbids.
    """
    validate_bundle(bundle.manifest, bundle.arrays)
    manifest_path = directory / MANIFEST_FILENAME
    arrays_path = directory / ARRAYS_FILENAME
    for path in (manifest_path, arrays_path):
        if path.exists():
            raise BundleValidationError(
                f"{path} already exists; write_bundle never overwrites a bundle"
            )
    directory.mkdir(parents=True, exist_ok=True)
    descriptors = {
        dataset: descriptor
        for dataset, (descriptor, _) in collect_descriptors(bundle.manifest).items()
    }
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=directory))
    placed: list[Path] = []
    try:
        staged_manifest = staging / MANIFEST_FILENAME
        staged_arrays = staging / ARRAYS_FILENAME
        # newline="\n" is not cosmetic. manifest.json is the artifact a
        # content_hash will be taken over once spec/architecture.md 4.1 stops
        # deferring one, and a hash over platform-dependent line endings would
        # be worthless. The canonical bytes are LF on every platform.
        staged_manifest.write_text(
            dump_manifest(bundle.manifest), encoding="utf-8", newline="\n"
        )
        write_arrays(staged_arrays, descriptors, bundle.arrays)
        for source, destination in (
            (staged_arrays, arrays_path),
            (staged_manifest, manifest_path),
        ):
            os.replace(source, destination)
            placed.append(destination)
    except BaseException:
        for path in placed:
            path.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def dump_manifest(manifest: OperatorBundleManifest) -> str:
    """Serialize a manifest to the canonical ``manifest.json`` text."""
    document = manifest.model_dump(mode="json")
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def read_bundle(directory: Path) -> OperatorBundle:
    """Read and validate the bundle in ``directory``.

    Raises:
        BundleValidationError: if either file is missing or the bundle does not
            validate.
    """
    manifest_path = directory / MANIFEST_FILENAME
    arrays_path = directory / ARRAYS_FILENAME
    for path in (manifest_path, arrays_path):
        if not path.is_file():
            raise BundleValidationError(f"{path} is missing; a bundle is both files")
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise BundleValidationError(
            f"{manifest_path} is not valid JSON: {error}"
        ) from error
    manifest = parse_manifest(document)
    descriptors = {
        dataset: descriptor
        for dataset, (descriptor, _) in collect_descriptors(manifest).items()
    }
    arrays = read_arrays(arrays_path, descriptors)
    validate_bundle(manifest, arrays)
    return OperatorBundle(manifest=manifest, arrays=arrays)
