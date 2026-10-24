"""Instances, configurations, preparation and reports, as JSON (seconds each).

Nothing here is on the proof path:
every number comes from an instance's ``preparation`` or ``runner``, every
refusal from the engine's own checks, every report sentence from
``certiqs_key.runs.report``.

A PROTOCOL DOCUMENT IN PLACE OF AN INSTANCE. ``describe_instance``,
``prepare`` and ``jobs.start_run`` take a caller's protocol document -- a
parsed object, or a ``.json``/``.yaml``/``.yml`` file of at most 1 MiB --
instead of an instance id. It is read by :func:`instances.declared.load` as a
CUSTOM document, so a packaged instance's identity is refused
(``reserved_identity``), and its :class:`~instances.declared.DocumentSurface`
then stands where an instance's ``surface`` module stands: every function
below takes either. A refusal of the document has the one refusal shape with
``stage: "document"``, the document layer's ``reason``
(:class:`~instances.declared.DocumentReason`) and the JSON ``path`` into the
document. Nothing here ever reads a caller's tree as packaged: the packaged
loader, which reads only ``instances/<id>/protocol.yaml`` and is called by
that instance's own ``surface.py`` alone, is named
nowhere in ``runs/`` (``tests/integration/test_run_facade_documents.py`` holds
that), and a template is parsed for reading only.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading
import time
from collections.abc import Callable, Mapping
from fractions import Fraction
from functools import cache
from importlib import resources
from pathlib import Path
from types import ModuleType
from typing import Any, Final

__all__ = [
    "CREATED_BY",
    "DOCUMENT_STAGE",
    "INPUT_STAGE",
    "MAX_DETAIL_CHARS",
    "MAX_DOCUMENT_FILE_BYTES",
    "REPORT_FILES",
    "UnknownInstanceError",
    "approximate",
    "canonical_digest",
    "config_for",
    "describe_instance",
    "document_guide",
    "document_info",
    "document_refusal_codes",
    "engine_identity",
    "guarded",
    "honest_override",
    "instance_document",
    "job_key",
    "list_instances",
    "load_document",
    "preparation_file_stem",
    "preparation_summary",
    "prepare",
    "prepare_surface",
    "read_config",
    "read_json",
    "read_report",
    "refusal_codes",
    "refusal_from",
    "repo_root",
    "report_part",
    "report_summary",
    "resolve",
    "run_preparation",
    "runtime_note",
    "schema",
    "stored_document",
    "surface",
    "template",
    "template_path",
    "write_json_atomic",
    "write_report_files",
    "write_text_atomic",
]

#: What produced a record written through the facade. Never a path, a
#: timestamp or a run id (the runner's own rule for ``created_by``).
CREATED_BY: Final[str] = "certiqs-key/runs.facade"

#: The pseudo-stage of a refusal the instance's input checks raise before any
#: pipeline stage runs.
INPUT_STAGE: Final[str] = "input"

#: The pseudo-stage of a refusal of a caller's protocol document: it does not
#: read, has no meaning as a document, or cannot be lowered.
DOCUMENT_STAGE: Final[str] = "document"

#: The largest document file read through ``document_file``.
MAX_DOCUMENT_FILE_BYTES: Final[int] = 1 << 20

#: The file suffixes a document file may have (``instances.declared.reader``).
DOCUMENT_SUFFIXES: Final[tuple[str, ...]] = (".json", ".yaml", ".yml")

#: Where a packaged instance's protocol document lives, below its folder.
TEMPLATE_NAME: Final[str] = "protocol.yaml"

#: The schemas a caller may ask for, by short name: package data of
#: ``certiqs_key.runs`` and ``certiqs_key.runs.report``, and the protocol
#: document's schema beside the document layer that generates it.
SCHEMAS: Final[Mapping[str, tuple[str, str]]] = {
    "run-input": ("certiqs_key.runs", "run-input.schema.json"),
    "record": ("certiqs_key.runs", "record.schema.json"),
    "report": ("certiqs_key.runs.report", "report.schema.json"),
    "protocol-document": ("instances.declared", "protocol-document.schema.json"),
}

#: The engine's shared input preparation. A ``ValueError`` raised THERE inside
#: ``preparation`` is the instance refusing an input it cannot prepare
#: (``runs/input-preparation.md``); raised anywhere else it stays an error.
_INPUT_PREPARATION_MODULE: Final[str] = "certiqs_key.runs.inputs"


class UnknownInstanceError(KeyError):
    """An instance id that no discovered instance carries."""


def repo_root() -> Path:
    """Return the repository root this package sits in."""
    return Path(__file__).resolve().parents[2]


@cache
def _surfaces() -> dict[str, ModuleType]:
    import instances

    return {s.DESCRIPTOR.id: s for s in instances.discover()}


def surface(instance_id: str) -> ModuleType:
    """Return one instance's ``surface`` module by its descriptor id."""
    found = _surfaces().get(instance_id)
    if found is None:
        raise UnknownInstanceError(
            f"no instance {instance_id!r}; the instances are {sorted(_surfaces())}"
        )
    return found


def engine_identity() -> dict[str, Any]:
    """Return which engine answers: its commit and the schema versions it speaks.

    ``dirty`` is true when the working tree differs from the commit, so a
    record produced then cannot be reproduced from the commit alone. Computed
    afresh on every call: the clone is shared and may move under a running
    server (a pull, another agent's edit), and a cached identity would let a
    job of other code be reused.
    """
    from certiqs_key.runs.record import RECORD_SCHEMA_VERSION
    from certiqs_key.runs.report import REPORT_SCHEMA_VERSION

    def git(*args: str) -> str | None:
        try:
            done = subprocess.run(
                ["git", "--no-optional-locks", *args],
                cwd=repo_root(),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
                **_quiet_subprocess(),
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return str(done.stdout).strip()

    status = git("status", "--porcelain", "--untracked-files=no")
    return {
        "commit": git("rev-parse", "HEAD"),
        "dirty": None if status is None else bool(status),
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "report_schema_version": REPORT_SCHEMA_VERSION,
    }


def _quiet_subprocess() -> dict[str, Any]:
    """Return the options that keep a helper process from opening a console."""
    flags: int = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return {"creationflags": flags} if flags else {}


# ---------------------------------------------------------------------------
#  Files
# ---------------------------------------------------------------------------

_PARTIAL_COUNTER = iter(range(1 << 62))
_PARTIAL_LOCK = threading.Lock()


def _retrying(action: Any, attempts: int = 60) -> Any:
    """Run ``action``, retrying briefly while Windows reports the file busy.

    On Windows a file another process has open cannot be replaced, and one
    being replaced cannot be opened (``PermissionError``); this happens between
    a job's worker and the server reading its status. Both hold the file for
    microseconds, so a short backoff resolves it.
    """
    for attempt in range(attempts):
        try:
            return action()
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.005 * (1 + attempt % 10))
    raise AssertionError("unreachable")


def write_text_atomic(path: Path, text: str) -> None:
    """Replace ``path`` with ``text``, never leaving it half-written."""
    with _PARTIAL_LOCK:
        serial = next(_PARTIAL_COUNTER)
    partial = path.with_name(f"{path.name}.{os.getpid()}.{serial}.partial")
    partial.write_text(text, encoding="utf-8", newline="\n")
    try:
        _retrying(lambda: os.replace(partial, path))
    finally:
        if partial.exists():
            partial.unlink()


def write_json_atomic(path: Path, value: Any) -> None:
    """Replace ``path`` with ``value`` as JSON, never leaving it half-written."""
    write_text_atomic(
        path, json.dumps(value, indent=1, ensure_ascii=False, sort_keys=True)
    )


def read_json(path: Path) -> Any:
    """Return a JSON file's value, ``None`` if it does not exist.

    A file that is busy is retried; one that stays unreadable raises, so a
    caller never mistakes "momentarily unreadable" for "absent".
    """
    try:
        text = _retrying(lambda: path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    return json.loads(text)


def canonical_digest(value: Any) -> str:
    """Return the sha256 of a value's canonical JSON (sorted keys, no spaces)."""
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
#  Instances
# ---------------------------------------------------------------------------


def template_path(instance_id: str) -> Path | None:
    """Return a packaged instance's protocol document, ``None`` if it has none.

    Only a discovered instance's id is looked up, so no caller's string ever
    becomes a path.
    """
    if instance_id not in _surfaces():
        return None
    path = repo_root() / "instances" / instance_id / TEMPLATE_NAME
    return path if path.is_file() else None


def list_instances() -> list[dict[str, Any]]:
    """Return every discovered instance's descriptor, in discovery order.

    An instance with a protocol document names it under ``template``
    (repository-relative): the starting point of a custom protocol.
    """
    listed = []
    for instance_id, s in _surfaces().items():
        entry = {
            **s.DESCRIPTOR.as_payload(),
            "presets": [preset.name for preset in s.PRESETS],
            "runtime": runtime_note(s)["summary"],
        }
        if template_path(instance_id) is not None:
            entry["template"] = f"instances/{instance_id}/{TEMPLATE_NAME}"
        listed.append(entry)
    return listed


def describe_instance(
    instance_id: str = "",
    *,
    document: Any = None,
    document_file: str | None = None,
) -> dict[str, Any]:
    """Return what a caller needs to write a configuration for one instance.

    ``instance`` is the block a run record carries as ``payload.instance``
    (its parameters: section ``model`` or ``device``); ``run_parameters`` the
    run tier's own fields, described once for every instance
    (``runs/surface.py`` ``RUN_PARAMETERS``); ``default_config`` a complete
    configuration to start from.

    WITH A DOCUMENT this is the document's validation: it is read
    and every reference in it checked, and the same shape is returned for it,
    with ``document`` (its id, digest, and ``packaged: false``) and
    ``conversions`` (each binary64 float of an object document, replaced by
    its exact value and recorded); or a refusal with ``stage: "document"``.
    What depends on a configuration -- the lowering to the modules -- is
    ``prepare``'s.
    """
    from certiqs_key.runs.surface import RUN_PARAMETERS, InstanceIdentity

    if document is None and not document_file:
        s: Any = surface(instance_id)
    else:
        s = load_document(instance_id, document, document_file)
        if isinstance(s, dict):
            return s
    try:
        default = s.default_config().to_payload()
    except _engine_input_errors() as error:
        if not _is_document(s):
            raise
        return refusal_from(error, DOCUMENT_STAGE)
    if _is_document(s):
        # The engine's own key checks on the document's defaults, at once: a
        # default outside its domain is refused here rather than at prepare.
        checked = config_for(s, default)
        if isinstance(checked, dict):
            return {**checked, "stage": DOCUMENT_STAGE, "path": "/parameters"}
    described = {
        "instance": InstanceIdentity(s.DESCRIPTOR, tuple(s.PARAMETERS)).as_payload(),
        "run_parameters": [spec.as_payload() for spec in RUN_PARAMETERS],
        "presets": [preset.as_payload() for preset in s.PRESETS],
        "default_config": default,
        "runtime": runtime_note(s),
    }
    info = document_info(s)
    if info is not None:
        described["document"] = info
        described["conversions"] = [dict(record) for record in s.conversions]
    return described


def runtime_note(s: Any) -> dict[str, Any]:
    """Return what drives an instance's preparation time, and its default's estimate.

    The parameters that drive it are those the estimate reads: the receivers'
    photon cutoffs and windows (the instance's optional
    ``receiver_parameters``; a source cutoff is not among them, its cost is
    negligible); the estimate at ``default_config()`` is
    :func:`runs.facade.estimate.estimate_preparation`'s. ``summary`` is the
    one line ``list_instances`` shows (the expected
    runtime and its reason are transparent to any user).
    """
    from runs.facade.estimate import estimate_preparation

    drivers = list(getattr(s, "receiver_parameters", ()))
    try:
        default = estimate_preparation(s, s.default_config())
    except Exception:  # a document whose defaults do not read: unknown
        default = {"expected_seconds": None}
    seconds = default.get("expected_seconds")
    at_default = (
        "unknown at the defaults"
        if seconds is None
        else f"{default['duration']} to prepare at the defaults"
    )
    if drivers:
        grows = (
            f"; grows steeply with {', '.join(drivers)} (the receivers' photon "
            "cutoffs and windows): prepare states the expected time and runs in "
            "the background past the budget"
        )
    else:
        grows = "; no receiver photon cutoff or window to raise"
    return {
        "summary": at_default + grows,
        "driven_by": drivers,
        "expected_seconds_at_defaults": seconds,
    }


# ---------------------------------------------------------------------------
#  Protocol documents
# ---------------------------------------------------------------------------


def _is_document(s: Any) -> bool:
    from instances.declared import DocumentSurface

    return isinstance(s, DocumentSurface)


def document_info(s: Any) -> dict[str, Any] | None:
    """Return a document surface's ``{id, digest, packaged}``; ``None`` otherwise."""
    if not _is_document(s):
        return None
    return {"id": s.DESCRIPTOR.id, "digest": s.digest, "packaged": s.packaged}


#: The longest refusal ``detail`` and ``path`` a reply carries, in characters:
#: a document can make either as long as itself.
MAX_DETAIL_CHARS: Final[int] = 2_000
MAX_PATH_CHARS: Final[int] = 500


def _clipped(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... ({len(text) - limit} characters more)"


def _document_refusal(detail: str, *, reason: str, path: str = "") -> dict[str, Any]:
    return {
        "refused": True,
        "stage": DOCUMENT_STAGE,
        "reason": reason,
        "path": _clipped(path, MAX_PATH_CHARS),
        "detail": _clipped(detail, MAX_DETAIL_CHARS),
    }


def _unreadable(detail: str) -> dict[str, Any]:
    return _document_refusal(detail, reason="document_unreadable")


def _parse_failure(failure: BaseException | None) -> str:
    """Return where a file failed to parse -- line and column, never its text.

    A YAML or JSON parser's message quotes the offending source line, and
    ``document_file`` can name any file the server can read; so only the
    position is reported.
    """
    import yaml

    if isinstance(failure, yaml.MarkedYAMLError) and failure.problem_mark is not None:
        mark = failure.problem_mark
        return f" at line {mark.line + 1}, column {mark.column + 1}"
    if isinstance(failure, json.JSONDecodeError):
        return f" at line {failure.lineno}, column {failure.colno}"
    return ""


def _document_file(name: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return a document file's parsed tree, or the refusal of what is no document.

    The file is named by an ABSOLUTE path: a relative one would be read
    against the server's working directory, which the client chose. A UNC or
    device path -- one that begins with two backslashes or two slashes -- is
    refused before it is touched: opening one can reach out to the network. A
    file that does not parse, or parses to something that is not a protocol
    document, is refused without quoting any of its content.
    """
    from instances.declared import DocumentError
    from instances.declared.model import FORMAT
    from instances.declared.reader import parse_text

    network = ("\\\\", "//")
    if name.startswith(network) or Path(name).drive.startswith(network):
        return None, _unreadable(
            "a document file is a local path; a network or device path "
            "(beginning with two backslashes or slashes) is not read"
        )
    path = Path(name).expanduser()
    if not path.is_absolute():
        return None, _unreadable(
            f"document_file is an absolute path; {name!r} is relative, and the "
            "server's working directory is not yours to rely on"
        )
    if path.suffix.lower() not in DOCUMENT_SUFFIXES:
        return None, _unreadable(f"{path}: a document file is .json, .yaml or .yml")
    try:
        size = path.stat().st_size
    except OSError as failure:
        return None, _unreadable(
            f"{path} cannot be read: {failure.strerror or 'error'}"
        )
    if not path.is_file():
        return None, _unreadable(f"{path} is not a file")
    if size > MAX_DOCUMENT_FILE_BYTES:
        return None, _unreadable(
            f"{path} has {size} bytes; a document file has at most "
            f"{MAX_DOCUMENT_FILE_BYTES}"
        )
    syntax = "json" if path.suffix.lower() == ".json" else "yaml"
    try:
        tree = parse_text(path.read_text(encoding="utf-8"), syntax=syntax)
    except (OSError, UnicodeDecodeError):
        return None, _unreadable(f"{path} cannot be read as UTF-8 text")
    except DocumentError as error:
        return None, _unreadable(
            f"{path} does not parse as {syntax.upper()}"
            f"{_parse_failure(error.__cause__)}"
        )
    if not isinstance(tree, dict) or tree.get("format") != FORMAT:
        return None, _unreadable(
            f"{path} is not a protocol document: its top level has no format: {FORMAT}"
        )
    return tree, None


def load_document(
    instance_id: str, document: Any, document_file: str | None = None
) -> Any:
    """Return a caller's protocol document as an instance surface, or a refusal.

    Exactly one of ``document`` (a parsed JSON object) and ``document_file``
    (an absolute path) is given. The document is read as a CUSTOM one
    (:func:`instances.declared.load`): a packaged instance's id, an
    ``instances.`` label or a ``readme`` is ``reserved_identity``. A non-empty
    ``instance_id`` must be the document's ``identity.id``.
    """
    from instances.declared import DocumentError, load

    if document is not None and document_file:
        return _unreadable("give a document or a document_file, not both")
    source: Any
    if document_file:
        source, refused = _document_file(document_file)
        if refused is not None:
            return refused
    elif isinstance(document, Mapping):
        source = document
    else:
        return _unreadable(
            f"a document is one JSON object; got {type(document).__name__}"
        )
    try:
        s = load(source)
    except DocumentError as error:
        return refusal_from(error)
    except _engine_input_errors() as error:
        return refusal_from(error, DOCUMENT_STAGE)
    if instance_id and instance_id != s.DESCRIPTOR.id:
        return _document_refusal(
            f"the instance argument {instance_id!r} is not this document's "
            f"identity.id {s.DESCRIPTOR.id!r}; leave instance empty or give the "
            "document's id",
            reason="document_schema_violation",
            path="/identity/id",
        )
    return s


def job_key(request: Mapping[str, Any]) -> str:
    """Return the digest that keys a job: what makes two requests identical.

    The instance, the configuration digest, the honest override and the
    engine commit; for a protocol document also its digest and its
    conversions, so that an object document's ``0.5`` (a recorded float) and
    a YAML ``1/2`` -- one digest -- are not answered by each other's runs.
    Computed from the fields ``request.json`` stores, so the worker can
    recompute it.
    """
    asked: dict[str, Any] = {
        "instance": request.get("instance"),
        "config_digest": request.get("config_digest"),
        "honest": request.get("honest"),
        "engine": (request.get("engine") or {}).get("commit"),
    }
    if request.get("document_digest") is not None:
        asked["document"] = request["document_digest"]
        asked["document_conversions"] = request.get("document_conversions")
    if request.get("kind") is not None:
        # A preparation job is not the run of the same request.
        asked["kind"] = request["kind"]
    return canonical_digest(asked)


def stored_document(request: Mapping[str, Any]) -> Any:
    """Rebuild a job's document surface from its ``request.json``, or a refusal.

    The stored canonical tree and conversions are reloaded with
    :func:`instances.declared.load_canonical`, the reader ``prepare`` used,
    and the result must carry the digest the
    request was keyed by.
    """
    from instances.declared import DocumentError, load_canonical

    conversions = request.get("document_conversions") or []
    if not isinstance(conversions, list) or not all(
        isinstance(record, dict) for record in conversions
    ):
        return _unreadable(
            "the stored document's conversions are not a list of records"
        )
    try:
        s = load_canonical(request["document"], tuple(conversions))
    except DocumentError as error:
        return refusal_from(error)
    except _engine_input_errors() as error:
        return refusal_from(error, DOCUMENT_STAGE)
    if s.digest != request.get("document_digest"):
        return _unreadable(
            "the stored document's digest is not the one its job was started "
            f"with ({s.digest} against {request.get('document_digest')})"
        )
    return s


def resolve(
    instance_id: str, document: Any = None, document_file: str | None = None
) -> Any:
    """Return the surface a request names -- an instance or a document -- or a refusal.

    An unknown instance is the refusal ``unknown_instance``.
    """
    if document is not None or document_file:
        return load_document(instance_id, document, document_file)
    try:
        return surface(instance_id)
    except UnknownInstanceError as error:
        return {**refusal_from(error), "reason": "unknown_instance"}


def template(instance_id: str) -> dict[str, Any]:
    """Return a packaged instance's protocol document: its text and its JSON tree.

    The tree is the document's canonical form (decimals as their exact
    strings), which a caller edits and passes back as ``document``. It is
    parsed for reading only and never loaded as packaged here. Raises
    ``KeyError`` for an instance with no template.
    """
    from instances.declared.reader import canonicalize, parse_text

    path = template_path(instance_id)
    if path is None:
        offered = sorted(name for name in _surfaces() if template_path(name))
        raise KeyError(
            f"instance {instance_id!r} has no protocol document; the templates "
            f"are {offered}"
        )
    text = path.read_text(encoding="utf-8")
    tree, _conversions = canonicalize(parse_text(text, syntax="yaml"))
    return {
        "instance": instance_id,
        "path": str(path),
        "yaml": text,
        "document": tree,
        "customise": (
            "Copy it and customise it as the comment block at the top of its "
            "yaml says: give identity a new id, title and summary; delete "
            "identity.readme and identity.record_label; delete or rewrite every "
            "other reserved string, which are each station's declared_by, the "
            "source's record_label and the source's "
            "retention_attestation.attested_by (write who attests the retention, "
            "or delete the retention_attestation block). A custom document may "
            "claim no packaged id and no string beginning with 'instances.'. "
            "Edit what differs, then describe_instance(document=...) to "
            "validate; a reserved_identity refusal lists every place still "
            "reserved."
        ),
    }


def document_guide() -> dict[str, Any]:
    """Return the protocol-document format guide, ``instances/declared/README.md``."""
    path = repo_root() / "instances" / "declared" / "README.md"
    return {"name": "README.md", "path": str(path), "markdown": path.read_text("utf-8")}


def document_refusal_codes() -> list[str]:
    """Return the protocol document's closed vocabulary of refusal codes."""
    from instances.declared import DocumentReason

    return [str(code) for code in DocumentReason]


def instance_document(instance_id: str, name: str | None = None) -> dict[str, Any]:
    """Return an instance's README, or a markdown file beside it that it names.

    Only the README and the ``.md`` files in the instance's own folder are
    served, so nothing outside the instance is reachable by name.
    """
    readme = repo_root() / surface(instance_id).DESCRIPTOR.readme
    folder = readme.parent
    available = sorted(path.name for path in folder.glob("*.md"))
    # A name is matched against the listing as a whole string, so a path
    # ("../x/README.md", an absolute path) can never resolve outside.
    if name is not None and name not in available:
        raise KeyError(
            f"instance {instance_id!r} has no document {name!r}; it has {available}"
        )
    target = readme if name is None else folder / name
    return {
        "instance": instance_id,
        "name": target.name,
        "path": str(target),
        "available": available,
        "markdown": target.read_text(encoding="utf-8"),
    }


def schema(name: str) -> dict[str, Any]:
    """Return one of :data:`SCHEMAS` by short name."""
    if name not in SCHEMAS:
        raise KeyError(f"no schema {name!r}; the schemas are {sorted(SCHEMAS)}")
    package, filename = SCHEMAS[name]
    loaded: dict[str, Any] = json.loads(
        resources.files(package).joinpath(filename).read_text(encoding="utf-8")
    )
    return loaded


def refusal_codes() -> list[str]:
    """Return the engine's closed vocabulary of input-refusal codes."""
    from certiqs_key.runs.errors import RunInputReason

    return [str(code) for code in RunInputReason]


# ---------------------------------------------------------------------------
#  Configurations
# ---------------------------------------------------------------------------


def refusal_from(error: BaseException, stage: str = INPUT_STAGE) -> dict[str, Any]:
    """Return an engine input error as a refusal: its reason code and text.

    A protocol document's refusal (``instances.declared.DocumentError``) is
    always at the stage ``document`` and also names its ``path``, the JSON
    pointer into the document, and a wrapped module's own reason where one was.
    """
    from instances.declared.errors import DocumentError

    if isinstance(error, DocumentError):
        refusal = _document_refusal(
            error.detail, reason=str(error.reason), path=error.path
        )
        if error.module_reason is not None:
            refusal["module_reason"] = error.module_reason
        return refusal
    reason = getattr(error, "reason", None) or type(error).__name__
    detail = error.args[0] if isinstance(error, KeyError) and error.args else str(error)
    return {
        "refused": True,
        "stage": stage,
        "reason": str(reason),
        "detail": _clipped(str(detail), MAX_DETAIL_CHARS),
    }


def _engine_input_errors() -> tuple[type[BaseException], ...]:
    """Return the engine's own classes for "this request is not one it accepts".

    ``RunError`` covers ``RunConfigError`` and every instance's input errors;
    ``MalformedInputError`` is a constructor refusing its arguments.
    """
    from certiqs_key.foundations.errors import MalformedInputError
    from certiqs_key.runs.errors import RunError

    return (RunError, MalformedInputError)


def read_config(instance_id: str, payload: Mapping[str, Any]) -> Any:
    """Return the ``RunConfig`` a payload describes, or a refusal.

    The payload is read by ``RunConfig.from_payload`` and its model and device
    keys by the instance's own ``check_keys`` over its parameter table, the
    checks the instance's ``preparation`` runs first. Builtin exceptions count
    as input refusals HERE ONLY, while the payload is read; an unknown
    instance is the refusal ``unknown_instance``.
    """
    s = resolve(instance_id)
    if isinstance(s, dict):
        return s
    return config_for(s, payload)


def config_for(s: Any, payload: Mapping[str, Any]) -> Any:
    """Return the ``RunConfig`` a payload describes for a surface, or a refusal.

    :func:`read_config` for a surface in hand: an instance's ``surface``
    module or a protocol document's.
    """
    from certiqs_key.runs import RunConfig
    from certiqs_key.runs.surface import Section, check_keys

    reading_errors: tuple[type[BaseException], ...] = (
        *_engine_input_errors(),
        KeyError,
        ValueError,
        TypeError,
    )
    try:
        config = RunConfig.from_payload(payload)
        check_keys(Section.MODEL, config.model, s.PARAMETERS, s.DESCRIPTOR.id)
        check_keys(Section.DEVICE, config.device, s.PARAMETERS, s.DESCRIPTOR.id)
    except reading_errors as error:
        return refusal_from(error)
    return config


def _raised_in(error: BaseException, module: str) -> bool:
    tb = error.__traceback__
    if tb is None:
        return False
    while tb.tb_next is not None:
        tb = tb.tb_next
    return tb.tb_frame.f_globals.get("__name__") == module


def run_preparation(s: ModuleType, config: Any) -> Any:
    """Return the instance's preparation outcome, or a refusal dict.

    Inside ``preparation`` only the engine's input classes, and a
    ``ValueError`` of the shared input preparation, are refusals.
    """
    return guarded(lambda: s.preparation(config))


def guarded(call: Callable[[], Any]) -> Any:
    """Return ``call()``, or the refusal of an input the engine does not accept.

    Only the engine's input classes, and a ``ValueError`` of the shared input
    preparation, are refusals; anything else is raised. The run worker calls
    the runner through this, as ``prepare`` calls ``preparation``.
    """
    try:
        return call()
    except _engine_input_errors() as error:
        return refusal_from(error)
    except ValueError as error:
        if _raised_in(error, _INPUT_PREPARATION_MODULE):
            return refusal_from(error)
        raise


# ---------------------------------------------------------------------------
#  Honest statistics from elsewhere
# ---------------------------------------------------------------------------


def honest_override(
    override: Mapping[str, Any] | None, instance_id: str
) -> tuple[Callable[[Any], Any] | None, dict[str, Any] | None] | dict[str, Any]:
    """Return ``(honest_provider, honest_model_note)`` for an override, or a refusal.

    A ``table`` is one honest law and an ``envelope`` a range per acceptance
    label (Assumption A-HON-ENV); both reach the runner through its
    ``honest_provider`` injection point unchanged -- nothing here widens,
    tightens or renormalises them, and the engine decides their admissibility
    at the acceptance construction. The note says, in the record, that the
    instance's own honest model was replaced and by what (``source`` is the
    user's own words), so the key-rate report shows it among the inputs.
    """
    if override is None:
        return None, None
    kinds = [kind for kind in ("table", "envelope") if override.get(kind) is not None]
    source = override.get("source")
    if len(kinds) != 1 or not isinstance(source, str) or not source.strip():
        return {
            "refused": True,
            "stage": INPUT_STAGE,
            "reason": "honest_override_malformed",
            "detail": "an honest override carries exactly one of 'table' or "
            "'envelope', and a non-empty 'source' saying where the "
            "statistics come from",
        }
    # The providers are the honest-model library's table forms, which a
    # protocol document offers as well.
    from instances.common.honest.tables import envelope_provider, table_provider

    try:
        if kinds == ["table"]:
            exact = {str(k): _exact(v) for k, v in override["table"].items()}
            provider: Callable[[Any], Any] = table_provider(exact)
            form = "table"
        else:
            lower = {
                str(k): _exact(v) for k, v in override["envelope"]["lower"].items()
            }
            upper = {
                str(k): _exact(v) for k, v in override["envelope"]["upper"].items()
            }
            provider = envelope_provider(lower, upper)
            form = "envelope"
    except (
        KeyError,
        ValueError,
        TypeError,
        ZeroDivisionError,
        AttributeError,
    ) as error:
        return {
            **refusal_from(error),
            "reason": "honest_override_malformed",
        }
    note = {
        "instance": instance_id,
        "model": f"caller-supplied honest {form} (replaces the instance's own model)",
        "module": "runs.facade",
        "overridden": True,
        "source": source.strip(),
        "digest": canonical_digest({form: override[form]}),
    }
    return provider, note


def _exact(value: Any) -> Fraction:
    """Read one honest probability: an exact string only.

    A JSON number is refused rather than read: ``Fraction(0.1)`` is the
    binary64 neighbour of 0.1, not 1/10, and nothing would record that
    conversion. ``"0.1"`` and ``"1/10"`` are read
    exactly.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"honest probabilities are exact strings such as '1/10' or '0.1'; "
            f"got {value!r}"
        )
    return Fraction(value)


def _override_labels(override: Mapping[str, Any]) -> set[str]:
    if override.get("table") is not None:
        return {str(label) for label in override["table"]}
    envelope = override["envelope"]
    return {str(label) for label in (*envelope["lower"], *envelope["upper"])}


# ---------------------------------------------------------------------------
#  Preparation
# ---------------------------------------------------------------------------


def prepare(
    instance_id: str,
    payload: Mapping[str, Any],
    honest: Mapping[str, Any] | None = None,
    *,
    document: Any = None,
    document_file: str | None = None,
) -> dict[str, Any]:
    """Read, key-check and prepare one configuration: no oracle, seconds.

    Returns an envelope ``{kind: "preparation", engine, instance, config,
    config_digest, preparation}`` around the engine's
    ``preparation_record`` (which deliberately carries no envelope of its
    own, so a caller writes one), or a refusal. ``config`` is the
    configuration as the engine READ it, every default resolved, which is
    what a user confirms before a run. With an honest override, its labels
    are compared with the acceptance alphabet, which the engine will decide
    again at the run.

    With a ``document`` or ``document_file`` in place of an instance, the
    document is read (:func:`load_document`) and its configuration-dependent
    lowering runs as well; the envelope adds ``document`` (id, digest,
    packaged), and the preparation carries ``protocol_document``.
    """
    s = resolve(instance_id, document, document_file)
    if isinstance(s, dict):
        return s
    return prepare_surface(s, payload, honest)


def prepare_surface(
    s: Any, payload: Mapping[str, Any], honest: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """:func:`prepare` for a surface in hand (an instance's or a document's).

    The envelope carries ``estimate``, the preparation's expected seconds and
    the parameters driving them (:mod:`runs.facade.estimate`), computed before
    preparing, so every summary states them.
    """
    from certiqs_key.runs import preparation_record
    from runs.facade.estimate import estimate_preparation

    instance_id = s.DESCRIPTOR.id
    config = config_for(s, payload)
    if isinstance(config, dict):
        return config
    if honest is not None:
        checked = honest_override(honest, instance_id)
        if isinstance(checked, dict):
            return checked
    estimate = estimate_preparation(s, config)
    outcome = run_preparation(s, config)
    if isinstance(outcome, dict):
        return outcome
    record = preparation_record(outcome)
    envelope: dict[str, Any] = {
        "kind": "preparation",
        "engine": engine_identity(),
        "instance": instance_id,
        "config": config.to_payload(),
        "config_digest": config.digest(),
        "preparation": record,
        "estimate": estimate,
    }
    info = document_info(s)
    if info is not None:
        envelope["document"] = info
    if honest is not None and not record.get("refused"):
        envelope["honest_override"] = dict(honest)
        alphabet = set(record.get("acceptance_alphabet") or ())
        labels = _override_labels(honest)
        envelope["honest_override_labels"] = {
            "missing": sorted(alphabet - labels),
            "unknown": sorted(labels - alphabet),
        }
    return envelope


def approximate(value: Any) -> Any:
    """Return an exact ``"p/q"`` as a short decimal string, for reading only."""
    if isinstance(value, str):
        try:
            number = Fraction(value)
        except (ValueError, ZeroDivisionError):
            return value
        if number.denominator == 1:
            return str(number.numerator)
        return f"{float(number):.6g}"
    return value


def preparation_summary(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Return what a user confirms before a run, small enough for one reply.

    The resolved configuration, the acceptance alphabet, every snap with its
    size (the instance repairing a declared number by at most the declared
    tolerance), the planned stages, and the honest distribution rounded for
    reading (the exact one is in the full envelope). Anything else of the
    preparation is named under ``parts`` and read in full by name.
    """
    record = envelope["preparation"]
    document = _document_summary(envelope)
    if record.get("refused"):
        return {
            "refused": True,
            "stage": record.get("stage"),
            "reason": record.get("reason"),
            "detail": record.get("detail"),
            "rule": record.get("rule"),
            "config": envelope["config"],
            "document": document,
            "estimate": envelope.get("estimate"),
        }
    adaptation = record.get("rows_adaptation") or {}
    snaps = _snaps(adaptation)
    summary: dict[str, Any] = {
        "refused": False,
        "instance": envelope["instance"],
        "document": document,
        # The expected seconds and what drives them, stated before and after.
        "estimate": envelope.get("estimate"),
        # What the protocol document declared itself, which the user vouches
        # for: the key-rate report lists the same items.
        "user_declared": [
            {key: item.get(key) for key in ("kind", "label", "path", "assumptions")}
            for item in (record.get("protocol_document") or {}).get("user_declared", [])
        ],
        "config": envelope["config"],
        "config_digest": envelope["config_digest"],
        "acceptance_alphabet": record.get("acceptance_alphabet"),
        "snaps": {
            "declared_tolerance": adaptation.get("declared_tolerance")
            or envelope["config"].get("declared_tolerance"),
            "count": len(snaps),
            "largest_pre_snap_defect": max(
                (snap["pre_snap_defect"] or 0.0 for snap in snaps), default=0.0
            ),
            # The run's two snap settings, and what the instance's own snap
            # record says before any solve: a moved block on which no
            # reference is handed rests on A-SNAP whatever the run does; a
            # moved block on which one is handed rests only where the run
            # does not evaluate it off its snap, which the run decides after
            # its search (runs/direct_route.py). So the preparation names those
            # blocks as pending, and the run's answer is
            # report_summary()["measurement_snaps"].
            "snap_settings": adaptation.get("snap_settings")
            or next(
                (
                    station.get("snap_settings")
                    for station in adaptation.get("stations") or []
                    if isinstance(station, Mapping)
                ),
                None,
            ),
            "rests_on_a_snap_by_the_instance_record": any(
                snap["rests_on_assumption"] for snap in snaps
            ),
            "moved_blocks_pending_the_run": [
                {key: snap[key] for key in ("station", "setting", "block")}
                for snap in snaps
                if snap["status"] == "moved" and snap["handed_reference_kind"]
            ],
            "entries": snaps[:40],
            "omitted": max(0, len(snaps) - 40),
        },
        "input_preparation": _compact_rows(adaptation.get("input_preparation")),
        "stages": [
            {
                key: stage.get(key)
                for key in ("stage", "station", "module", "status", "reason")
            }
            for stage in record.get("stages", [])
        ],
        "parts": sorted(record),
    }
    override = envelope.get("honest_override")
    if override is None:
        summary["honest_model"] = "the instance's own model"
        summary["honest_distribution_approx"] = _approximate_table(
            record.get("raw_joint_distribution") or {}
        )
    else:
        # The run uses the override, not the instance's model: show what it
        # will use.
        form = "table" if override.get("table") is not None else "envelope"
        summary["honest_model"] = (
            f"REPLACED by the caller's {form} (source: {override.get('source')!r}); "
            "the instance's own distribution is part 'raw_joint_distribution' "
            "and is NOT used by the run"
        )
        summary["honest_distribution_approx"] = (
            _approximate_table(override["table"])
            if form == "table"
            else {
                bound: _approximate_table(override["envelope"][bound])
                for bound in ("lower", "upper")
            }
        )
        summary["honest_override_labels"] = envelope["honest_override_labels"]
    return summary


def _document_summary(envelope: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the document a preparation lowered: id, digest, unmatched rule keys.

    ``unmatched`` counts, per expanded rule table, the keys no rule matched
    (listed, not refused); the keys are part ``protocol_document``.
    """
    info = envelope.get("document")
    if info is None:
        return None
    block = envelope["preparation"].get("protocol_document") or {}
    unmatched = {
        name: len(keys) for name, keys in (block.get("unmatched") or {}).items() if keys
    }
    return {"id": info["id"], "digest": info["digest"], "unmatched": unmatched}


def preparation_file_stem(envelope: Mapping[str, Any]) -> str:
    """Return the file name, without suffix, a preparation envelope is kept under.

    An instance's is ``<instance>-<config digest>``; a document's adds its own
    digest, so that two documents of one id never share a file.
    """
    config = str(envelope["config_digest"])[:12]
    info = envelope.get("document")
    if info is None:
        return f"{envelope['instance']}-{config}"
    return f"declared_{info['id']}-{str(info['digest'])[:12]}-{config}"


def _approximate_table(table: Mapping[str, Any]) -> Any:
    if len(table) > 120:
        return f"{len(table)} entries; read the full preparation"
    return {label: approximate(value) for label, value in table.items()}


def _snaps(adaptation: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every block of a preparation's measurement snaps, single-station and per station.

    A multi-station instance carries its snaps under ``stations``, each with
    the module that declared them; missing them would make bbm92 look snap-free. One
    entry per block of the instance's measurement-family snap (record 0.28.0):
    its setting, status (kept or moved), what the snap started from, the kind
    of the reference handed beside it, its group and cause where it rests on
    A-SNAP, flags, and its largest measured pre-snap defect (``None`` where the
    snap started from a reference, whose defects are zero by its definition).
    """

    def entries(record: Mapping[str, Any], label: str | None) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for snap in record.get("measurement_snaps") or []:
            for block in snap.get("blocks") or []:
                pre_snap = block.get("pre_snap") or {}
                measured = block.get("defects_ground") == "measured"
                out.append({
                    "station": label,
                    "site": snap.get("site"),
                    "setting": snap.get("setting"),
                    "block": block.get("block"),
                    "status": block.get("status"),
                    "reference_kind": block.get("reference_kind"),
                    "handed_reference_kind": block.get("handed_reference_kind"),
                    "group": block.get("group"),
                    "cause": block.get("cause"),
                    "support_not_preserved": bool(block.get("support_not_preserved")),
                    "rests_on_assumption": bool(block.get("rests_on_assumption")),
                    "pre_snap_defect": (
                        max(pre_snap.values(), default=0.0) if measured else None
                    ),
                })
        return out

    found = entries(adaptation, None)
    for index, station in enumerate(adaptation.get("stations") or []):
        found += entries(station, station.get("declared_by") or f"station {index}")
    return found


def _compact_rows(rows: Any, limit: int = 600) -> Any:
    """Keep each row's short fields; name the long ones instead of copying them.

    Input preparation is where the engine moved the user's own numbers
    (``prepared_values``, ``total_displacement``), so it is shown, but its
    shape is the instance's, so long values are elided by size, not by name.
    """
    if not isinstance(rows, list):
        return rows
    compact = []
    for row in rows:
        if not isinstance(row, Mapping):
            compact.append(row)
            continue
        kept: dict[str, Any] = {}
        for key, value in row.items():
            size = len(json.dumps(value, default=str))
            kept[key] = value if size <= limit else f"({size} chars; full preparation)"
        compact.append(kept)
    return compact


# ---------------------------------------------------------------------------
#  Reports
# ---------------------------------------------------------------------------

#: The report files :func:`write_report_files` writes beside a record.
REPORT_FILES: Final[Mapping[str, str]] = {
    "json": "report.json",
    "markdown": "report.md",
    "html": "report.html",
}


def write_report_files(record: Mapping[str, Any], directory: Path) -> dict[str, str]:
    """Build a record's key-rate report and write it as JSON, Markdown and HTML.

    The HTML file is the one a human reviews: it is self-contained and links
    every normative statement into its contract (absolute ``file:`` links into
    this clone, so they open from wherever the file is). Raises the report's
    own ``ReportInputError`` for a record it cannot read.
    """
    from certiqs_key.runs.report import (
        build_report,
        default_contract_link,
        render_html,
        render_markdown,
    )

    report = build_report(record)
    link = default_contract_link(repo_root().as_uri() + "/")
    texts = {
        "json": json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True),
        "markdown": render_markdown(report, contract_link=link),
        "html": render_html(report, contract_link=link),
    }
    paths: dict[str, str] = {}
    for form, rendered in texts.items():
        path = directory / REPORT_FILES[form]
        write_text_atomic(path, rendered)
        paths[form] = str(path)
    return paths


def read_report(directory: Path) -> dict[str, Any]:
    """Return the report object written by :func:`write_report_files`."""
    loaded: dict[str, Any] = json.loads(
        (directory / REPORT_FILES["json"]).read_text(encoding="utf-8")
    )
    return loaded


def report_part(report: Mapping[str, Any], path: str) -> Any:
    """Return the part of a report a stable path names (``report.select``)."""
    from certiqs_key.runs.report import select

    return select(report, path)  # type: ignore[arg-type]


def _compact(rows: Any, keep: tuple[str, ...]) -> Any:
    if isinstance(rows, list):
        return [
            {k: row[k] for k in keep if k in row} if isinstance(row, Mapping) else row
            for row in rows
        ]
    return rows


def _vouch_entry(entry: Mapping[str, Any], *, numerics: bool = False) -> dict[str, Any]:
    """One assumption as a user reads it, with ITS OWN category and refinement."""
    return {
        "short_id": entry["short_id"],
        "title": entry["owner"]["title"],
        "category": entry.get("category"),
        "refines": entry.get("refines"),
        "verification": entry.get("verification"),
        "user_statement": entry.get("user_statement"),
        **({"engine_numerics": True} if numerics else {}),
    }


def report_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return the report a user reviews, small enough for one reply.

    The result, the inputs as the engine read them, the honest model, and
    EVERY assumption the result rests on with its ``user_statement`` -- the
    plain reading by which a user decides whether it holds for their device.
    Each part is readable in full through :func:`report_part` by the path
    given (``assumptions/A-ENS``, ``inputs/rounds``, ``checks``, ...).
    """
    sections = report["sections"]
    result = sections["result"]
    protocol = sections["protocol"]
    assumptions = sections["assumptions"]
    vouch = [
        _vouch_entry(entry)
        for group in assumptions["groups"]
        for family in group["families"]
        for entry in (family["head"], *family["members"])
    ]
    # The engine's numerical premises (A-EIG, ...) are assumptions the
    # result rests on as well; the report keeps them in its numerics section.
    vouch += [
        _vouch_entry(entry, numerics=True)
        for entry in (sections.get("numerics") or {}).get("entries", [])
    ]
    # WHAT THE PROTOCOL DOCUMENT DECLARED ITSELF (report 0.3.0): explicit
    # constraints, licences and witnesses, a declared receiver POVM or
    # receiver characterisation, a retention attestation. Each is the user's
    # to vouch for, so the promise of "EVERY assumption" holds on the
    # document route too.
    declared = result.get("user_declared") or []
    vouch += [
        {
            "kind": item.get("kind"),
            "label": item.get("label"),
            "text": item.get("text"),
            "assumptions": item.get("assumptions"),
            "user_declared": True,
        }
        for item in declared
    ]
    completeness = result.get("completeness") or {}
    security = result.get("security_parameter") or {}
    # Whether the run rests on A-SNAP, read where the run's decision is
    # (runs/report/snaps.py): the preparation summary cannot say it for a
    # moved block on which the reference is handed.
    snaps = protocol.get("measurement_snaps")
    return {
        "report_id": report["id"],
        "result": {
            "outcome": result.get("outcome"),
            "refusal": result.get("refusal"),
            "key_length": result.get("key_length"),
            "net_key_length": result.get("net_key_length"),
            "rate_per_round": result.get("rate_per_round"),
            "rounds": result.get("rounds"),
            # the Renyi order and what chose it: the outer search, the
            # configuration or the declaration (report 0.6.0)
            "alpha": result.get("alpha"),
            "reported_tier": result.get("reported_tier"),
            "key_length_reason_code": result.get("key_length_reason_code"),
            "key_length_reason": result.get("key_length_reason"),
            "reason_text": result.get("reason_text"),
            "security_parameter": security.get("value"),
            "completeness_eps_star_approx": approximate(completeness.get("eps_star")),
            # every caveat in full: what is NOT counted in this key length
            "not_counted": result.get("not_counted"),
            # what the protocol document declared, not the engine derived
            "user_declared": declared,
            "limitations": _compact(
                result.get("limitations"), ("id", "title", "summary")
            ),
        },
        "instance": protocol["instance"],
        "document": protocol.get("document"),
        "facts": {fact["name"]: fact["value"] for fact in protocol.get("facts", [])},
        "inputs": [
            {
                key: row.get(key)
                for key in ("name", "section", "value", "is_default", "unit", "snapped")
            }
            for row in protocol.get("inputs", [])
        ],
        "honest_model": (protocol.get("honest_model") or {}).get("note"),
        "measurement_snaps": (
            None
            if snaps is None
            else {
                "rests_on_a_snap": snaps.get("rests_on_a_snap"),
                "warnings": snaps.get("warnings"),
                "resting_blocks": [
                    {key: block.get(key) for key in (
                        "station", "setting", "block", "status", "group",
                        "group_fix", "cause",
                    )}
                    for block in snaps.get("blocks") or []
                    if block.get("rests_on_assumption")
                ],
            }
        ),
        "assumptions_to_vouch_for": vouch,
        "assumptions_not_engaged": sorted(
            {row["short_id"] for row in assumptions.get("not_engaged", [])}
        ),
        "discrepancies": assumptions.get("discrepancies", []),
        "checks": _compact(sections["checks"]["checks"], ("id", "title", "outcome")),
    }
