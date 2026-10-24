"""Record excerpts: every record value a key-rate report cites, under its pointer.

WHY THIS EXISTS. A report names record values by JSON pointer (RFC 6901, from
the record root) so that every number can be traced; a reader holding only
the report folder cannot follow a pointer into a gzipped record of megabytes.
The CLI therefore writes
``record.html`` / ``record.md`` beside the report: each pointer the report
object holds, once, in the record's own order, as a heading whose anchor is
:func:`~certiqs_key.runs.report._render.excerpt_anchor` of the pointer, with
the value rendered readably. The report links each pointer it shows there.

READABLE, NOT COMPLETE. A mapping is a table of its fields (nested fields by
their relative path), a matrix a matrix, a list of more than
:data:`LIST_LIMIT` items is cut with a count, a nested part larger than
:data:`EXPAND_LIMIT` characters is summarised, and at most :data:`ROW_LIMIT`
rows are shown per pointer; the record stays the authority, and every cut
says so.

FIELD NAMES. A reader tracing a premise to its evidence meets the record's
own field names (``alice_povm``, ``virtual_transmitted_system``,
``source_alphabet``) with nothing to say what they hold (the EB reader
round). The page ends with the meaning of each name of
:data:`FIELD_WORDS` that occurs on it, written as data here, not read from
the claims.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from fractions import Fraction
from typing import Any, Final

from certiqs_key.runs.report._render import (
    Code,
    ExcerptLink,
    Link,
    Rich,
    Writer,
    excerpt_anchor,
    format_entry,
    format_value,
    report_pointers,
)
from certiqs_key.runs.report.inputs import resolve_pointer
from certiqs_key.runs.report.model import KeyRateReport, MatrixEntry
from certiqs_key.runs.report.setup import matrix_of

__all__ = [
    "EXPAND_LIMIT",
    "LIST_LIMIT",
    "ROW_LIMIT",
    "default_excerpt_link",
    "excerpt_pointers",
    "write_excerpts",
]

#: Items of a list shown before it is cut.
LIST_LIMIT: Final[int] = 200
#: Rows of one pointer's table before the rest is cut.
ROW_LIMIT: Final[int] = 400
#: A nested part longer than this (compact JSON characters) is summarised.
EXPAND_LIMIT: Final[int] = 5000
#: Matrices shown per pointer.
MATRIX_LIMIT: Final[int] = 64
#: A leaf longer than this (compact JSON characters) is cut.
_LEAF_LIMIT: Final[int] = 300

_MISSING: Final = object()

#: What a record field holds, by its name, for the names a reader meets in
#: the excerpts of the compiled protocol (``/payload/compiled``).
FIELD_WORDS: Final[Mapping[str, str]] = {
    "accept_statistic": "each pair of announcements with the acceptance value "
                        "a round with them records",
    "acceptance_alphabet": "the acceptance values a round can record",
    "alice_announcement_alphabet": "what Alice can announce in a round",
    "bob_announcement_alphabet": "what Bob can announce in a round",
    "announce_alice": "each of Alice's readouts with what she announces for it",
    "announce_bob": "each of Bob's readouts with what he announces for it",
    "key_map": "each pair of readouts with the key holder's raw key bit; perp "
               "marks a round that gives no key bit",
    "raw_key_map": "the same map as key_map, under the name the post-processing "
                   "reads",
    "key_alphabet": "the values a raw key bit takes",
    "key_holder": "the party (A or B) whose raw string both keys are computed "
                  "from",
    "party_partition": "which party holds each readout and each system of the "
                       "declaration",
    "choice_weightings": "the public choices whose weights depend on a "
                         "station's setting, one entry per weighted measurement",
    "source_alphabet": "in a choice weighting, the outcomes of the measurement "
                       "the weighting is declared at",
    "setting_map": "in a choice weighting, the setting each of those outcomes "
                   "belongs to",
    "source_mode": "whether the analysis trusts the source (trusted) or treats "
                   "it as the attacker's (untrusted)",
    "alice_dim": "the dimension of system A, the declaration's per-round letter "
                 "on Alice's side",
    "alice_povm": "the measurement on system A of the declaration; with a "
                  "trusted source, Alice's measurement in the source-replacement "
                  "picture, one operator per signal, which selects the signal "
                  "sent",
    "alice_marginal": "the reduced state of system A that the declaration fixes",
    "signal_alphabet": "the source's signals (its letters), in declared order",
    "virtual_transmitted_system": "the dimension of the transmitted system as "
                                  "the proof models it",
    "virtual_ensemble_weights": "the probability of each signal in the ensemble "
                                "the proof models",
    "public_choices": "the public choices the compiled source declares: each "
                      "one's party, choices and weights",
}

#: The anchor of the field names' section.
FIELD_NAMES_ANCHOR: Final[str] = "field-names"


def _order(record: Mapping[str, Any], pointer: str) -> tuple[int, ...] | None:
    """Return a pointer's position in the record's document order, or ``None``."""
    node: Any = record
    position: list[int] = []
    for raw in pointer[1:].split("/") if pointer else []:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, Mapping) and token in node:
            position.append(list(node).index(token))
            node = node[token]
        elif isinstance(node, list) and token.isdigit() and int(token) < len(node):
            position.append(int(token))
            node = node[int(token)]
        else:
            return None
    return tuple(position)


def excerpt_pointers(record: Mapping[str, Any], report: Any) -> list[str]:
    """Return the report's pointers, once, in the record's document order.

    A pointer the record does not resolve keeps its report order after every
    one it does.
    """
    pointers = report_pointers(report)
    placed = [(pointer, _order(record, pointer)) for pointer in pointers]
    found = sorted(
        ((order, pointer) for pointer, order in placed if order is not None),
    )
    return [pointer for _, pointer in found] + [
        pointer for pointer, order in placed if order is None
    ]


def _scalar(value: Any) -> bool:
    return value is None or isinstance(value, bool | int | float | str)


def _numeric(matrix: list[list[MatrixEntry]] | None) -> bool:
    if matrix is None:
        return False
    for row in matrix:
        for entry in row:
            for part in entry:
                if isinstance(part, str):
                    try:
                        Fraction(part)
                    except (ValueError, ZeroDivisionError):
                        return False
    return True


def _compact(value: Any) -> str:
    text = json.dumps(value, sort_keys=False, ensure_ascii=False)
    if len(text) > _LEAF_LIMIT:
        return f"{text[:_LEAF_LIMIT]}… ({len(text):,} characters; see the record)"
    return text


def _size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False))


class _Collector:
    """The rows and matrices of one pointer's value, within the limits."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str]] = []
        self.matrices: list[tuple[str, list[list[MatrixEntry]]]] = []
        self.cut = 0

    def row(self, path: str, text: str) -> None:
        if len(self.rows) >= ROW_LIMIT:
            self.cut += 1
            return
        self.rows.append((path or "(value)", text))

    def matrix(self, path: str, matrix: list[list[MatrixEntry]]) -> bool:
        if len(self.matrices) >= MATRIX_LIMIT:
            return False
        self.matrices.append((path or "(value)", matrix))
        return True

    def add(self, value: Any, path: str, depth: int) -> None:
        matrix = matrix_of(value) if isinstance(value, list) else None
        if _scalar(value):
            self.row(path, format_value(value))
        elif _numeric(matrix) and matrix is not None and len(matrix) == 1 == len(
            matrix[0]
        ):
            self.row(path, f"1 \u00d7 1 matrix: {format_entry(matrix[0][0])}")
        elif _numeric(matrix) and matrix is not None:
            shape = f"{len(matrix)} \u00d7 {len(matrix[0])} matrix"
            shown = self.matrix(path, matrix)
            self.row(path, f"{shape}, shown below" if shown else f"{shape}, not shown")
        elif depth > 0 and _size(value) > EXPAND_LIMIT:
            noun = (f"an object of {len(value)} fields" if isinstance(value, Mapping)
                    else f"a list of {len(value)} items")
            self.row(path, f"{noun} ({_size(value):,} characters); not shown, see "
                           "the record")
        elif isinstance(value, Mapping):
            if not value:
                self.row(path, "{}")
            for key, item in value.items():
                self.add(item, f"{path}/{key}" if path else str(key), depth + 1)
        elif isinstance(value, list):
            if not value:
                self.row(path, "[]")
            elif all(_scalar(item) for item in value):
                joined = ", ".join(format_value(item) for item in value[:LIST_LIMIT])
                if len(value) > LIST_LIMIT:
                    joined += f" … and {len(value) - LIST_LIMIT} more"
                self.row(path, joined)
            else:
                for index, item in enumerate(value[:LIST_LIMIT]):
                    self.add(item, f"{path}/{index}" if path else str(index),
                             depth + 1)
                if len(value) > LIST_LIMIT:
                    self.row(path, f"… and {len(value) - LIST_LIMIT} more items, "
                                   "not shown")
        else:
            self.row(path, _compact(value))


def _write_value(writer: Writer, value: Any, names: set[str] | None = None) -> None:
    """Write one pointer's value; ``names`` collects the field names it shows."""
    if _scalar(value):
        writer.paragraph([Code(format_value(value))])
        return
    collector = _Collector()
    collector.add(value, "", 0)
    if names is not None:
        names.update(part for path, _ in collector.rows for part in path.split("/"))
    if len(collector.rows) > 1 or collector.rows[0][0] != "(value)":
        writer.table(["Field", "Value"],
                     [[[Code(path)], [text]] for path, text in collector.rows])
    elif not collector.matrices:
        writer.paragraph([collector.rows[0][1]])
    if collector.cut:
        writer.paragraph([f"{collector.cut} more fields are not shown; see the "
                          "record."])
    for path, matrix in collector.matrices:
        labels = [str(index) for index in range(1, len(matrix) + 1)]
        columns = [str(index) for index in range(1, len(matrix[0]) + 1)]
        writer.matrix(path, labels, columns,
                      [[format_entry(entry) for entry in row] for row in matrix])


def write_excerpts(
    writer: Writer,
    record: Mapping[str, Any],
    report: KeyRateReport,
    *,
    report_href: str | None = None,
) -> str:
    """Write the excerpts of every pointer of ``report`` and return the document."""
    pointers = excerpt_pointers(record, report)
    writer.heading(1, "Record excerpts")
    lead: Rich = [
        "Every record value the key-rate report cites, once, under its JSON "
        "pointer (RFC 6901) from the record root, in the record's order. "
        f"Report id {report['id']}."
    ]
    if report_href is not None:
        lead += [" ", Link("Back to the report", report_href)]
    names: set[str] = set()
    for pointer in pointers:
        names.update(pointer.split("/"))
    writer.paragraph(lead)
    for pointer in pointers:
        writer.heading(2, pointer, excerpt_anchor(pointer))
        value = resolve_pointer(record, pointer, _MISSING)
        if value is _MISSING:
            writer.paragraph(["The record holds nothing at this pointer."])
            continue
        _write_value(writer, value, names)
    explained = [name for name in FIELD_WORDS if name in names]
    if explained:
        writer.heading(2, "What the field names mean", FIELD_NAMES_ANCHOR)
        writer.bullets([[Code(name), ": ", FIELD_WORDS[name] + "."]
                        for name in explained])
    return writer.text()


def default_excerpt_link(href: str) -> ExcerptLink:
    """Return ``f"{href}#{excerpt_anchor(pointer)}"``: links into one excerpts file."""

    def link(pointer: str) -> str:
        return f"{href}#{excerpt_anchor(pointer)}"

    return link
