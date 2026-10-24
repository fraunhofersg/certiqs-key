"""``python -m certiqs_key.runs.report``: render any run record's key-rate report.

WHY THIS EXISTS. A record on disk must be turnable into its report without
writing a script; other adapters call the same functions, so this is a thin
adapter and decides nothing of its own.

Usage::

    python -m certiqs_key.runs.report RECORD [RECORD ...] [--format md|html|json]
           [--out PATH] [--sweep] [--contract-base URL] [--repo-base URL]
           [--pages-site] [--excerpts | --no-excerpts]

One record gives one report; several records, a directory (its ``*.json`` and
``*.json.gz`` files, by file name) or ``--sweep`` give a sweep report. A sweep
with ``--out DIR`` writes ``DIR/sweep.<ext>`` and each point's report as
``DIR/points/<NNNN>.<ext>``, linked relatively. Without ``--out`` the document
goes to standard output (UTF-8); a sweep written there still links its points
as ``points/<NNNN>.<ext>``, files that only ``--out DIR`` writes.

RECORD EXCERPTS (report 0.8.0). When a report is written to
a file (md or html), the record excerpts are written beside it, ``record.<ext>``
next to a run's report and ``points/<NNNN>.record.<ext>`` next to each point's,
and every record pointer the report shows links into them; ``--no-excerpts``
turns that off, ``--excerpts`` cannot turn it on for standard output.

``--repo-base`` (default none) links every repository path a report prints to
``<repo-base><path>``; a relative base takes one more ``../`` for a sweep's
point reports, as the contract base does. ``--pages-site`` renders for the
project's Pages site, which serves the contracts, digests, graphs and report
example pages only: a repository path the site does not serve (an instance
README, ``spec/architecture.md``) is then printed in code, not linked, since
the link would be dead there.

A λ_EC ESTIMATE beside a record, ``<record stem>.lambda-ec.json`` (the stem
without ``.json`` or ``.json.gz``), is read and shown under the λ_EC input; it
is a side file, never part of the record or the report object.

Exit codes: 0 on success; 2 when a record cannot be read or is not one this
report reads (the :class:`ReportInputError` reason is printed, e.g.
``record_schema_version``); 1 when the shipped closure table lacks a claim
the report cites (a packaging defect, not the record's).
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import zlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from certiqs_key.domain.claim_closure import ClaimClosureError
from certiqs_key.runs.report._render import (
    default_contract_link,
    pages_site_serves,
    report_pointers,
)
from certiqs_key.runs.report.build import (
    ReportInputError,
    build_report,
    build_sweep_report,
)
from certiqs_key.runs.report.excerpts import default_excerpt_link
from certiqs_key.runs.report.model import SweepPoint
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

__all__ = ["lambda_ec_path", "main", "read_lambda_ec"]

_EXTENSIONS = {"md": "md", "html": "html", "json": "json"}


def _read(path: Path) -> dict[str, Any]:
    """Read a ``.json`` or ``.json.gz`` record; refuse anything unreadable."""
    try:
        if path.name.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                data = json.load(handle)
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, EOFError, zlib.error) as exc:
        raise ReportInputError("unreadable_record", f"{path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ReportInputError("not_a_run_record", f"{path} holds no JSON object")
    return data


def lambda_ec_path(record: Path) -> Path:
    """Return where a record's λ_EC estimate sits: ``<stem>.lambda-ec.json``."""
    name = record.name
    for suffix in (".json.gz", ".json"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return record.with_name(f"{name}.lambda-ec.json")


def read_lambda_ec(record: Path) -> dict[str, Any] | None:
    """Return the λ_EC estimate beside a record, or ``None`` where there is none.

    An unreadable side file is reported on standard error and ignored: the
    report then says λ_EC was declared, which is what the record alone shows.
    """
    path = lambda_ec_path(record)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"warning: {path} is not readable JSON ({exc}); ignored",
              file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"warning: {path} holds no JSON object; ignored", file=sys.stderr)
        return None
    return data


def _paths(arguments: Sequence[str]) -> tuple[list[Path], bool]:
    """Return the record files named, and whether a directory was among them."""
    paths: list[Path] = []
    directory = False
    for argument in arguments:
        path = Path(argument)
        if path.is_dir():
            directory = True
            paths.extend(sorted(
                (found for found in path.iterdir()
                 if found.is_file()
                 and (found.name.endswith(".json") or found.name.endswith(".json.gz"))
                 # A λ_EC estimate beside a record is a side file, not a record.
                 and not found.name.endswith(".lambda-ec.json")),
                key=lambda found: found.name,
            ))
        else:
            paths.append(path)
    if not paths:
        raise ReportInputError("no_records", "no record files were named")
    return paths, directory


def _json(document: Any) -> str:
    return json.dumps(document, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def _emit(text: str, out: Path | None) -> None:
    if out is None:
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.flush()
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))


@dataclass(frozen=True)
class _Options:
    form: str
    contract_base: str
    repo_base: str | None
    excerpts: bool
    pages_site: bool = False

    @property
    def served(self) -> Callable[[str], bool] | None:
        """Which repository paths link: those the Pages site serves, or all."""
        return pages_site_serves if self.pages_site else None


def _render_one(
    record: Mapping[str, Any],
    options: _Options,
    *,
    excerpts: str | None = None,
    report_name: str | None = None,
    lambda_ec: Mapping[str, Any] | None = None,
) -> tuple[str, str | None]:
    """Return a run's report and, where ``excerpts`` names their file, its excerpts."""
    report = build_report(record)
    if options.form == "json":
        return _json(report), None
    link = default_contract_link(options.contract_base)
    excerpt_link = None if excerpts is None else default_excerpt_link(excerpts)
    if options.form == "html":
        text = render_html(report, contract_link=link, excerpt_link=excerpt_link,
                           repo_base=options.repo_base, lambda_ec=lambda_ec,
                           repo_served=options.served)
        found = (None if excerpts is None
                 else render_excerpts_html(record, report, report_href=report_name))
        return text, found
    text = render_markdown(report, contract_link=link, excerpt_link=excerpt_link,
                           repo_base=options.repo_base, lambda_ec=lambda_ec,
                           repo_served=options.served)
    found = (None if excerpts is None
             else render_excerpts_markdown(record, report, report_href=report_name))
    return text, found


def _absolute(base: str) -> bool:
    """Whether a contract base is a URL or an absolute path, on either OS."""
    return (
        "://" in base
        or PurePosixPath(base).is_absolute()
        or PureWindowsPath(base).is_absolute()
    )


def _stepped(base: str | None) -> str | None:
    """Return a base as seen from one folder deeper (a sweep's point reports)."""
    if base is None or _absolute(base):
        return base
    return "../" + base


def _render_sweep(
    records: list[dict[str, Any]],
    paths: list[Path],
    options: _Options,
    out: Path | None,
) -> None:
    extension = _EXTENSIONS[options.form]
    sweep = build_sweep_report(records)

    def point_link(point: SweepPoint) -> str:
        return f"points/{point['index']:04d}.{extension}"

    link = default_contract_link(options.contract_base)
    # The sweep shows the setup of one point; its pointers link to that
    # point's excerpts, which are written below.
    shown = sweep["common"]["setup_point"]
    excerpt_link = None
    pointers: frozenset[str] = frozenset()
    if options.excerpts and out is not None and shown is not None:
        excerpt_link = default_excerpt_link(f"points/{shown:04d}.record.{extension}")
        pointers = frozenset(report_pointers(build_report(records[shown])))
    if options.form == "json":
        text = _json(sweep)
    elif options.form == "html":
        text = render_sweep_html(sweep, contract_link=link, point_link=point_link,
                                 repo_base=options.repo_base,
                                 excerpt_link=excerpt_link, excerpt_pointers=pointers,
                                 repo_served=options.served)
    else:
        text = render_sweep_markdown(sweep, contract_link=link, point_link=point_link,
                                     repo_base=options.repo_base,
                                     excerpt_link=excerpt_link,
                                     excerpt_pointers=pointers,
                                     repo_served=options.served)
    if out is None:
        _emit(text, None)
        return
    _emit(text, out / f"sweep.{extension}")
    # A point's report sits one folder below the sweep, so a relative
    # contract base needs one more step up there; a URL or an absolute path
    # (a Windows drive path included) does not.
    point_options = _Options(
        options.form, _stepped(options.contract_base) or "",
        _stepped(options.repo_base), options.excerpts, options.pages_site,
    )
    for point, record, path in zip(sweep["points"], records, paths, strict=True):
        stem = f"{point['index']:04d}"
        excerpts = f"{stem}.record.{extension}" if options.excerpts else None
        report, found = _render_one(
            record, point_options, excerpts=excerpts,
            report_name=f"{stem}.{extension}", lambda_ec=read_lambda_ec(path),
        )
        _emit(report, out / point_link(point))
        if found is not None and excerpts is not None:
            _emit(found, out / "points" / excerpts)


def main(argv: Sequence[str] | None = None) -> int:
    """Render the report of one record or a sweep; return the exit code."""
    parser = argparse.ArgumentParser(
        prog="python -m certiqs_key.runs.report",
        description="Render the key-rate report of run records.",
    )
    parser.add_argument("records", nargs="+",
                        help="run record files (.json, .json.gz) or a directory")
    parser.add_argument("--format", choices=sorted(_EXTENSIONS), default="md",
                        help="output format (default md)")
    parser.add_argument("--out", type=Path, default=None,
                        help="output file; for a sweep, an output directory "
                             "(without it a sweep goes to stdout and its point "
                             "links name files that are not written)")
    parser.add_argument("--sweep", action="store_true",
                        help="render a sweep report even from one record")
    parser.add_argument("--contract-base", default="",
                        help="prefix of every contract PDF link (default: "
                             "repo-relative spec/modules/...)")
    parser.add_argument("--repo-base", default=None,
                        help="prefix of a link to every repository path the report "
                             "prints (default: none, plain text)")
    parser.add_argument("--pages-site", action="store_true",
                        help="render for the Pages site: a repository path the "
                             "site does not serve is printed, not linked")
    parser.add_argument("--excerpts", action=argparse.BooleanOptionalAction,
                        default=None,
                        help="write the record excerpts beside the report and link "
                             "every record pointer to them (default: on when "
                             "--out is given and the format is md or html)")
    args = parser.parse_args(argv)
    excerpts = (
        args.out is not None and args.format != "json"
        and args.excerpts is not False
    )
    options = _Options(args.format, args.contract_base, args.repo_base, excerpts,
                       args.pages_site)
    try:
        paths, directory = _paths(args.records)
        records = [_read(path) for path in paths]
        if args.sweep or directory or len(records) > 1:
            _render_sweep(records, paths, options, args.out)
        else:
            extension = _EXTENSIONS[args.format]
            name = f"record.{extension}" if excerpts else None
            report, found = _render_one(
                records[0], options, excerpts=name,
                report_name=None if args.out is None else args.out.name,
                lambda_ec=read_lambda_ec(paths[0]),
            )
            _emit(report, args.out)
            if found is not None and args.out is not None and name is not None:
                _emit(found, args.out.parent / name)
    except ReportInputError as error:
        print(f"error: {error.reason}: {error.detail}", file=sys.stderr)
        return 2
    except ClaimClosureError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
