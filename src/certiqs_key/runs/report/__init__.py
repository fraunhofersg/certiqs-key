"""The key-rate report: everything needed to qualify a key rate, from its run record.

WHY THIS EXISTS. Every key-rate run yields a key-rate report, so that every
question a QKD security evaluation asks of a claimed key rate can be answered
from it, with the assumptions a user must vouch for stated in their own words
and every normative statement linked into its contract.

    model            the report object as JSON-native types (MCP returns them)
    build            a record to a report; N records of one instance to a sweep
    inputs           the declared inputs and where the record holds them
    checks           the conditions the engine decided
    setup            "Your QKD setup", read off the record (0.8.0)
    excerpts         the record excerpts the report's pointers link to (0.8.0)
    render_markdown  Markdown
    render_html      one self-contained HTML file
    __main__         ``python -m certiqs_key.runs.report``

The record is the authority and the report a pure projection of it: nothing
here computes a number, and no run-tier code authors assumption text.
``report.schema.json`` (package data) is the object's hand-written schema.

READY FOR ADAPTERS: every part is addressable by a
stable id through :func:`select`, the object holds data and the claims' plain
text only, and the CLI is a thin adapter over the same functions.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import cache
from importlib import resources
from typing import Any, Final

from certiqs_key.runs.report._render import (
    cited_repo_paths,
    default_contract_link,
    pages_site_serves,
)
from certiqs_key.runs.report.build import (
    REPORT_SCHEMA_VERSION,
    SUPPORTED_RECORD_SCHEMA_VERSION,
    SUPPORTED_RECORD_SCHEMA_VERSIONS,
    ReportInputError,
    build_report,
    build_sweep_report,
    record_id,
)
from certiqs_key.runs.report.excerpts import default_excerpt_link
from certiqs_key.runs.report.model import (
    KeyRateReport,
    SweepReport,
    group_entries,
)
from certiqs_key.runs.report.render_html import (
    render_excerpts_html,
    render_html,
    render_sweep_html,
)
from certiqs_key.runs.report.render_markdown import (
    render_excerpts_markdown,
    render_markdown,
    render_sweep_markdown,
)

__all__ = [
    "REPORT_SCHEMA_VERSION",
    "SCHEMA_NAME",
    "SUPPORTED_RECORD_SCHEMA_VERSION",
    "SUPPORTED_RECORD_SCHEMA_VERSIONS",
    "KeyRateReport",
    "ReportInputError",
    "SweepReport",
    "build_report",
    "build_sweep_report",
    "cited_repo_paths",
    "default_contract_link",
    "default_excerpt_link",
    "pages_site_serves",
    "record_id",
    "render_excerpts_html",
    "render_excerpts_markdown",
    "render_html",
    "render_markdown",
    "render_sweep_html",
    "render_sweep_markdown",
    "report_schema",
    "select",
]

#: The package-data file beside this module.
SCHEMA_NAME: Final[str] = "report.schema.json"


@cache
def _schema_text() -> str:
    return (
        resources.files("certiqs_key.runs.report")
        .joinpath(SCHEMA_NAME)
        .read_text(encoding="utf-8")
    )


def report_schema() -> dict[str, Any]:
    """Return the report's JSON Schema (2020-12), a fresh copy."""
    schema: dict[str, Any] = json.loads(_schema_text())
    return schema


def _entries(part: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    checks = part.get("checks")
    decided = (
        checks["decided_rows"] if isinstance(checks, Mapping)
        else part.get("decided_rows", [])
    )
    return [
        *group_entries(part["assumptions"]["groups"]),
        *part["numerics"]["entries"],
        *decided,
    ]


def select(report: KeyRateReport | SweepReport, path: str) -> Any:
    """Return the part of a report a stable path names.

    Paths: ``<section id>`` (``result``, ``setup``, ``protocol``, ``assumptions``,
    ``numerics``, ``checks``, ``provenance``; a sweep's ``common``,
    ``varying``, ``points``), ``assumptions/<A-...>``, ``inputs/<input name>``,
    ``checks/<check id>``, ``claims/<claim id>`` and, on a sweep,
    ``points/<index>``. Raises ``KeyError`` naming the path where nothing
    matches.
    """
    kind, _, key = path.partition("/")
    document: Mapping[str, Any] = report
    if report["kind"] == "key-rate-report":
        part: Mapping[str, Any] = document["sections"]
        checks = part["checks"]["checks"]
    else:
        part = document["common"]
        checks = part["checks"]
    if not key:
        if kind in part:
            return part[kind]
        if kind in document:
            return document[kind]
        raise KeyError(path)
    if kind == "assumptions":
        for entry in _entries(part):
            if entry["short_id"] == key:
                return entry
    elif kind == "inputs":
        rows = part["protocol"]["inputs"] if "protocol" in part else part["inputs"]
        for row in rows:
            if row["name"] == key:
                return row
    elif kind == "checks":
        for check in checks:
            if check["id"] == key:
                return check
    elif kind == "claims":
        claims = document["index"]["claims"]
        if key in claims:
            return claims[key]
    elif kind == "points" and "points" in document and key.isdigit():
        points = document["points"]
        if int(key) < len(points):
            return points[int(key)]
    raise KeyError(path)
