"""Reading a protocol document: one canonical tree, its conversions and its digest.

WHY ONE CANONICAL TREE. A document arrives as
JSON text, YAML text, or an object an MCP client already parsed, and the same
document must mean the same numbers on every route: in ``prepare``, in the
worker that runs it later, and in the record. So every route is turned into
ONE tree of JSON integers, strings, booleans, nulls, lists and objects, and
nothing reads anything else. A non-integer number written in text becomes the
string of its source text (``0.02`` becomes ``"0.02"``), so it is read exactly
later; a binary64 float arriving in an object becomes the exact rational
string of its value, and the replacement is listed in ``conversions`` in the
shape of ``runs.inputs``' ``numeric_input_conversion`` record (PRINCIPLES.md
section 9: ordinary numbers, prepared and recorded by the engine's own rule).
The digest is taken over that tree, and the tree and its conversions are what
is stored and reloaded (:func:`read_canonical`).

THE YAML READER KNOWS FEWER WORDS THAN YAML 1.1. Its
booleans are ``true`` and ``false`` only, so ``off`` and ``on`` -- a probe
setting, a switch case -- stay strings; its integers are decimal only, so octal
and hex spellings stay strings; it reads no timestamps; and a float is the
text it was written as. A repeated key is refused rather than silently
overwritten.

THE READER IS A TRUST BOUNDARY. A document can come from an MCP client, so
reading it is bounded: the text's length, the tree's depth and its node count
are capped, and YAML aliases are refused outright (an alias is never needed to
write a document, and a few lines of nested aliases expand to a billion
nodes). A document past a bound is ``document_unreadable``; nothing here lets
an input exhaust the stack or memory.

WHAT IS REFUSED HERE: text that does not parse, a tree that is not a document
(``document_unreadable``), a version this reader does not know
(``format_version_unsupported``), a shape the models refuse
(``document_schema_violation``), and an identity a custom document may not
claim (``reserved_identity``). Nothing here reads a value.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from certiqs_key.runs.config import canonical_json
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.limits import check_dimensions
from instances.declared.model import (
    FORMAT,
    ProtocolDocument,
    StaticDocument,
    Switch,
    TrustedEnsemble,
    WcpDecoy,
)

__all__ = [
    "MAX_DEPTH",
    "MAX_NODES",
    "MAX_TEXT_LENGTH",
    "PACKAGED_NAME",
    "ReadDocument",
    "canonicalize",
    "digest",
    "parse_text",
    "read",
    "read_canonical",
    "read_packaged",
]

#: The file name of a packaged document: ``instances/<id>/protocol.yaml``.
PACKAGED_NAME = "protocol.yaml"

_INSTANCES = Path(__file__).resolve().parent.parent

#: The longest document text, in characters (1 MiB).
MAX_TEXT_LENGTH = 1 << 20
#: The deepest nesting of objects and lists.
MAX_DEPTH = 64
#: The most values (objects, lists and scalars) one document may hold.
MAX_NODES = 200_000

type Canonical = dict[str, Any]


@dataclass(frozen=True)
class ReadDocument:
    """A document read and validated: its canonical tree and what was made of it."""

    #: The canonical tree, which is what was computed on.
    canonical: Canonical
    #: The canonicalisation records, one per binary64 float replaced.
    conversions: tuple[Mapping[str, Any], ...]
    #: ``sha256`` of the canonical tree's canonical JSON.
    digest: str
    #: Whether this is a packaged template.
    packaged: bool
    #: The validated model: :class:`ProtocolDocument`, or :class:`StaticDocument`
    #: for a static read.
    model: ProtocolDocument | StaticDocument


# ---------------------------------------------------------------------------
#  Parsing text
# ---------------------------------------------------------------------------

_BOOL = "tag:yaml.org,2002:bool"
_INT = "tag:yaml.org,2002:int"
_FLOAT = "tag:yaml.org,2002:float"
_TIMESTAMP = "tag:yaml.org,2002:timestamp"
_VALUE = "tag:yaml.org,2002:value"


def _repeated(keys: Sequence[str]) -> list[str]:
    return sorted(key for key, count in Counter(keys).items() if count > 1)


class _DocumentLoader(yaml.SafeLoader):
    """``SafeLoader`` with three changes; repeats and aliases refused."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        """Refuse an alias: no document needs one, and aliases nest exponentially."""
        if self.check_event(yaml.events.AliasEvent):
            event = self.peek_event()  # type: ignore[no-untyped-call]
            raise yaml.composer.ComposerError(
                None, None, "a document uses no YAML aliases", event.start_mark
            )
        return super().compose_node(parent, index)

    def construct_mapping(
        self, node: yaml.MappingNode, deep: bool = False
    ) -> dict[Any, Any]:
        """Build a mapping whose keys are their source text; refuse a repeated key."""
        written = [
            key.value
            for key, _value in node.value
            if isinstance(key, yaml.ScalarNode) and key.tag != "tag:yaml.org,2002:merge"
        ]
        repeated = _repeated(written)
        if repeated:
            raise yaml.constructor.ConstructorError(
                None, None, f"repeated keys {repeated}", node.start_mark
            )
        self.flatten_mapping(node)
        result: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, yaml.ScalarNode):
                raise yaml.constructor.ConstructorError(
                    None, None, "a key is a scalar", key_node.start_mark
                )
            result[key_node.value] = self.construct_object(value_node, deep=deep)
        return result


_DocumentLoader.yaml_implicit_resolvers = {
    first: [
        (tag, regexp)
        for tag, regexp in resolvers
        if tag not in (_BOOL, _INT, _FLOAT, _TIMESTAMP, _VALUE)
    ]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_DocumentLoader.add_implicit_resolver(
    _BOOL, re.compile(r"^(?:true|false)$"), list("tf")
)
_DocumentLoader.add_implicit_resolver(
    _INT, re.compile(r"^[-+]?[0-9]+$"), list("-+0123456789")
)


def _float_as_text(loader: yaml.SafeLoader, node: yaml.Node) -> str:
    """Return an explicitly tagged float as the text it was written as."""
    return str(loader.construct_scalar(node))  # type: ignore[arg-type]


def _decimal_int(loader: yaml.SafeLoader, node: yaml.Node) -> int:
    """Return an integer in base ten; ``SafeLoader`` reads a leading zero as octal."""
    return int(str(loader.construct_scalar(node)))  # type: ignore[arg-type]


_DocumentLoader.add_constructor(_FLOAT, _float_as_text)
_DocumentLoader.add_constructor(_INT, _decimal_int)


def _refuse_constant(text: str) -> None:
    raise ValueError(f"{text} is not a JSON number")


def _no_repeats(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    repeated = _repeated([key for key, _value in pairs])
    if repeated:
        raise ValueError(f"repeated keys {repeated}")
    return dict(pairs)


def parse_text(text: str, *, syntax: str | None = None) -> Any:
    """Parse document text; ``syntax`` is ``json`` or ``yaml``, else guessed.

    JSON keeps every non-integer number as its source text
    (``parse_float=str``); YAML uses the restricted loader above. Guessed, a
    text beginning with ``{`` is read as JSON and, if that fails, as YAML (a
    YAML flow mapping begins the same way).
    """
    if len(text) > MAX_TEXT_LENGTH:
        raise DocumentError(
            f"a document is at most {MAX_TEXT_LENGTH} characters; this one has "
            f"{len(text)}",
            reason=DocumentReason.DOCUMENT_UNREADABLE,
        )
    if syntax is None and text.lstrip().startswith("{"):
        try:
            return _parse(text, "json")
        except DocumentError:
            return _parse(text, "yaml")
    return _parse(text, syntax or "yaml")


def _parse(text: str, syntax: str) -> Any:
    try:
        if syntax == "json":
            return json.loads(
                text,
                parse_float=str,
                parse_constant=_refuse_constant,
                object_pairs_hook=_no_repeats,
            )
        return yaml.load(text, Loader=_DocumentLoader)
    except (ValueError, yaml.YAMLError) as failure:
        raise DocumentError(
            f"the document does not parse as {syntax}: {failure}",
            reason=DocumentReason.DOCUMENT_UNREADABLE,
        ) from failure
    except RecursionError:
        raise DocumentError(
            f"the document nests deeper than this reader follows (at most {MAX_DEPTH})",
            reason=DocumentReason.DOCUMENT_UNREADABLE,
        ) from None


# ---------------------------------------------------------------------------
#  The canonical tree
# ---------------------------------------------------------------------------


def canonicalize(value: object) -> tuple[Canonical, tuple[dict[str, Any], ...]]:
    """Return the canonical tree of a parsed document and its conversion records.

    A ``float`` becomes ``str(Fraction(x))`` with a ``numeric_input_conversion``
    record at ``document:<json pointer>``, in ``runs.inputs``' meaning: the
    input is the float's own exact value, so the displacement is zero, and
    ``written`` keeps the float's shortest spelling. A ``Fraction`` or
    ``Decimal`` from a Python caller becomes its exact string with none.
    Anything that is not JSON is refused, and so is a tree deeper than
    :data:`MAX_DEPTH` or larger than :data:`MAX_NODES` (a cyclic object is
    both).
    """
    conversions: list[dict[str, Any]] = []
    count = 0

    def visit(node: object, path: str, depth: int) -> object:
        nonlocal count
        count += 1
        if count > MAX_NODES:
            raise DocumentError(
                f"a document holds at most {MAX_NODES} values",
                reason=DocumentReason.DOCUMENT_UNREADABLE,
                path=path,
            )
        if depth > MAX_DEPTH:
            raise DocumentError(
                f"a document nests at most {MAX_DEPTH} deep",
                reason=DocumentReason.DOCUMENT_UNREADABLE,
                path=path,
            )
        if node is None or isinstance(node, bool | str):
            return node
        if isinstance(node, int):
            return node
        if isinstance(node, float):
            if not math.isfinite(node):
                raise DocumentError(
                    f"{node!r} is not a finite number",
                    reason=DocumentReason.DOCUMENT_UNREADABLE,
                    path=path,
                )
            exact = str(Fraction(node))
            conversions.append(
                {
                    "site": f"document:{path}",
                    "path": path,
                    "rule": "numeric_input_conversion",
                    "input_type": "float",
                    "input_value": exact,
                    "prepared_value": exact,
                    "total_displacement": "0",
                    "written": repr(node),
                }
            )
            return exact
        if isinstance(node, Fraction):
            return str(node)
        if isinstance(node, Decimal):
            if not node.is_finite():
                raise DocumentError(
                    f"{node!r} is not a finite number",
                    reason=DocumentReason.DOCUMENT_UNREADABLE,
                    path=path,
                )
            return str(node)
        if isinstance(node, Mapping):
            result: dict[str, object] = {}
            for key, item in node.items():
                if not isinstance(key, str):
                    raise DocumentError(
                        f"an object key is a string; got {key!r}",
                        reason=DocumentReason.DOCUMENT_UNREADABLE,
                        path=path,
                    )
                result[key] = visit(item, path + pointer(key), depth + 1)
            return result
        if isinstance(node, list | tuple):
            return [
                visit(item, path + pointer(index), depth + 1)
                for index, item in enumerate(node)
            ]
        raise DocumentError(
            f"{type(node).__name__} is not JSON",
            reason=DocumentReason.DOCUMENT_UNREADABLE,
            path=path,
        )

    tree = visit(value, "", 0)
    if not isinstance(tree, dict):
        raise DocumentError(
            "a document is one JSON object",
            reason=DocumentReason.DOCUMENT_UNREADABLE,
        )
    return tree, tuple(conversions)


def digest(canonical: Canonical) -> str:
    """Return ``sha256`` of the tree's canonical JSON (sorted keys, no spaces).

    The rule of ``runs.facade.core.canonical_digest``, computed from the run
    tier's ``canonical_json`` because ``instances`` may not import ``runs/``'s
    facade.
    """
    return hashlib.sha256(canonical_json(canonical).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
#  Reading and validating
# ---------------------------------------------------------------------------


def read(source: object, *, static: bool = False) -> ReadDocument:
    """Read a custom document from a path, text, or a parsed object.

    A :class:`~pathlib.Path` is read by its suffix (``.json``, ``.yaml`` or
    ``.yml``); a ``str`` is document text; a mapping is a parsed document.
    ``static=True`` validates only the configuration-independent blocks
    (:class:`StaticDocument`), which is what a fragment carries.
    """
    tree, conversions = canonicalize(_parse_source(source))
    return _validated(tree, conversions, packaged=False, static=static)


def read_packaged(path: Path, *, static: bool = False) -> ReadDocument:
    """Read a packaged template from ``instances/<id>/protocol.yaml``.

    Only a document at that place whose ``identity.id`` is the folder's name is
    packaged; anything else is refused, because packaged is what lets a
    document write the reserved identity strings.
    """
    resolved = path.resolve()
    if resolved.name != PACKAGED_NAME or resolved.parent.parent != _INSTANCES:
        raise DocumentError(
            f"{path} is not instances/<id>/{PACKAGED_NAME}; only a document there "
            "is packaged",
            reason=DocumentReason.RESERVED_IDENTITY,
        )
    tree, conversions = canonicalize(_parse_source(path))
    document = _validated(tree, conversions, packaged=True, static=static)
    if document.model.identity.id != resolved.parent.name:
        raise DocumentError(
            f"a packaged document's id is its folder's name, "
            f"{resolved.parent.name!r}; this one says "
            f"{document.model.identity.id!r}",
            reason=DocumentReason.RESERVED_IDENTITY,
            path="/identity/id",
        )
    return document


def read_canonical(
    canonical: Mapping[str, Any],
    conversions: Sequence[Mapping[str, Any]] = (),
    *,
    static: bool = False,
) -> ReadDocument:
    """Reload a stored custom document's tree and conversions, as the worker does.

    The tree must already be canonical: a float in it is refused rather than
    converted a second time, so that a stored document cannot drift from what
    ``prepare`` computed on. It is always read as a custom document; a
    packaged template is read only from its file (:func:`read_packaged`).
    """
    tree, again = canonicalize(canonical)
    if again:
        raise DocumentError(
            "a stored document is canonical and holds no float; "
            f"{again[0]['path']} does",
            reason=DocumentReason.DOCUMENT_UNREADABLE,
            path=str(again[0]["path"]),
        )
    return _validated(
        tree,
        tuple(dict(record) for record in conversions),
        packaged=False,
        static=static,
    )


def _parse_source(source: object) -> object:
    if isinstance(source, Path):
        syntax = {".json": "json", ".yaml": "yaml", ".yml": "yaml"}.get(
            source.suffix.lower()
        )
        if syntax is None:
            raise DocumentError(
                f"{source.name}: a document file is .json, .yaml or .yml",
                reason=DocumentReason.DOCUMENT_UNREADABLE,
            )
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as failure:
            raise DocumentError(
                f"{source} cannot be read: {failure}",
                reason=DocumentReason.DOCUMENT_UNREADABLE,
            ) from failure
        return parse_text(text, syntax=syntax)
    if isinstance(source, str):
        return parse_text(source)
    return source


def _validated(
    tree: Canonical,
    conversions: tuple[Mapping[str, Any], ...],
    *,
    packaged: bool,
    static: bool,
) -> ReadDocument:
    if tree.get("format") != FORMAT:
        raise DocumentError(
            f"format is {FORMAT!r}; got {tree.get('format')!r}",
            reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
            path="/format",
        )
    version = tree.get("format_version")
    if version not in ("1", 1) or isinstance(version, bool):
        raise DocumentError(
            f"this reader knows format_version '1'; got {version!r}",
            reason=DocumentReason.FORMAT_VERSION_UNSUPPORTED,
            path="/format_version",
        )
    # One spelling, so that one document has one digest.
    tree = {**tree, "format_version": "1"}
    kind: type[BaseModel] = StaticDocument if static else ProtocolDocument
    try:
        model = kind.model_validate(tree)
    except ValidationError as failure:
        raise _schema_error(failure, tree) from None
    assert isinstance(model, ProtocolDocument | StaticDocument)
    check_dimensions(tree)
    if not packaged:
        _check_identity(model)
    return ReadDocument(tree, conversions, digest(tree), packaged, model)


def _schema_error(failure: ValidationError, tree: Canonical) -> DocumentError:
    """Turn pydantic's errors into one refusal at the most specific real path.

    Pydantic's locations interleave keys of the tree with the names of union
    branches it tried; walking the tree keeps only the keys, which gives a JSON
    pointer a reader can follow. The deepest one is the most specific.
    """
    best: tuple[int, str, str] | None = None
    for error in failure.errors():
        node: object = tree
        parts: list[str | int] = []
        for step in error["loc"]:
            found, child = _child(node, step)
            if found:
                node = child
                parts.append(step)
        candidate = (len(parts), pointer(*parts), str(error["msg"]))
        if best is None or candidate[0] > best[0]:
            best = candidate
    assert best is not None
    count = failure.error_count()
    more = f" (and {count - 1} more alternatives refused)" if count > 1 else ""
    return DocumentError(
        f"{best[2]}{more}",
        reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
        path=best[1],
    )


def _child(node: object, step: str | int) -> tuple[bool, object]:
    """Return whether ``step`` is a key or index of ``node``, and what it reaches."""
    if isinstance(node, dict) and isinstance(step, str) and step in node:
        return True, node[step]
    if isinstance(node, list) and isinstance(step, int) and 0 <= step < len(node):
        return True, node[step]
    return False, None


# ---------------------------------------------------------------------------
#  Reserved identities
# ---------------------------------------------------------------------------


def _check_identity(model: ProtocolDocument | StaticDocument) -> None:
    """Refuse a custom document that claims a packaged instance's identity.

    EVERY CLAIM IS NAMED IN ONE REFUSAL. A custom document is usually a
    template copied and edited, and a template writes several reserved strings
    (optical_bb84's station, decoy_bb84's source and station): the refusal's
    ``path`` is the first, and its detail lists every other place, so that one
    round of edits clears them all.
    """
    from instances import INSTANCE_PACKAGES

    identity = model.identity
    found: list[tuple[str, str]] = []
    if identity.readme:
        found.append(
            (
                "/identity/readme",
                "a custom document names no readme: the field is a path in this "
                "repository, served as a file, and only a packaged template's is "
                "one",
            )
        )
    if identity.id in INSTANCE_PACKAGES:
        found.append(
            (
                "/identity/id",
                f"{identity.id!r} is a packaged instance's id; a custom document "
                "takes another",
            )
        )
    default = f"declared.{identity.id}"
    if identity.record_label is not None and identity.record_label != default:
        found.append(
            (
                "/identity/record_label",
                f"a custom document's record_label is {default!r}; got "
                f"{identity.record_label!r}",
            )
        )
    for value, path in _identity_strings(model):
        if value.startswith("instances.") and path != "/identity/record_label":
            found.append(
                (
                    path,
                    f"{value!r} begins with 'instances.', which only a packaged "
                    "template may write",
                )
            )
    if not found:
        return
    (path, detail), others = found[0], found[1:]
    if others:
        detail += "; also reserved: " + ", ".join(where for where, _ in others)
    # RENAME A REQUIRED FIELD, NEVER DELETE IT: an attestation without
    # ``attested_by`` is a schema violation.
    if any(where.endswith("/attested_by") for where, _ in found):
        detail += (
            ". Write your own value in each reserved place (for attested_by, who "
            "attests the retention) or delete the optional field or block "
            "(retention_attestation as a whole)"
        )
    raise DocumentError(detail, reason=DocumentReason.RESERVED_IDENTITY, path=path)


def _identity_strings(
    model: ProtocolDocument | StaticDocument,
) -> list[tuple[str, str]]:
    """Return every identity string a document writes into a record, with its path."""
    found: list[tuple[str, str]] = []
    if model.identity.record_label is not None:
        found.append((model.identity.record_label, "/identity/record_label"))
    if not isinstance(model, ProtocolDocument):
        return found
    for index, station in enumerate(model.stations):
        if station.declared_by is not None:
            found.append((station.declared_by, f"/stations/{index}/declared_by"))
    source = model.source
    if isinstance(source, TrustedEnsemble | WcpDecoy):
        attestation = source.retention_attestation
        if attestation is not None:
            found.append(
                (attestation.attested_by, "/source/retention_attestation/attested_by")
            )
    if isinstance(source, WcpDecoy) and source.record_site is not None:
        found.append((source.record_site, "/source/record_site"))
    if isinstance(source, WcpDecoy) and source.record_label is not None:
        found.append((source.record_label, "/source/record_label"))

    def honest(node: object, path: str) -> None:
        if isinstance(node, Switch):
            for case, branch in node.cases.items():
                honest(branch, path + pointer("cases", case))
            if node.default is not None:
                honest(node.default, path + pointer("default"))
            return
        note = getattr(node, "note", {})
        for key in ("instance", "module"):
            if isinstance(note.get(key), str):
                found.append((note[key], path + pointer("note", key)))

    honest(model.honest, "/honest")
    return found
