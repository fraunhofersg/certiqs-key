"""Render a key-rate report, or a sweep's, as one self-contained HTML file.

WHY THIS EXISTS. A report is handed to a partner with its assumptions
attached (PRINCIPLES.md section 1); a single HTML file opens anywhere, offline.
This
renderer is the HTML writer of the shared section walk in
:mod:`certiqs_key.runs.report._render`; it adds escaping and markup only.

SELF-CONTAINED AND INERT. One file: inline CSS (light and dark through
``prefers-color-scheme``), no ``<script>``, no external font, image or style
sheet. The only links leaving the file are the contract links the caller's
``contract_link`` builds, and, where the caller asks for them, the record
excerpt links (``excerpt_link``, the ``record.html`` written beside the
report), the repository links (``repo_base``) and, in a sweep, the per-point
report links the caller's ``point_link`` builds; every other ``href`` is an
in-page anchor. Every value is escaped with :func:`html.escape`.
Deterministic: no render time is printed.
"""

from __future__ import annotations

import html
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Final

from certiqs_key.runs.report._page import write_report, write_sweep
from certiqs_key.runs.report._render import (
    Anchor,
    Code,
    ContractLink,
    ExcerptLink,
    LambdaEcOrigin,
    Link,
    PointLink,
    Rich,
    Strong,
    Writer,
)
from certiqs_key.runs.report.excerpts import write_excerpts
from certiqs_key.runs.report.model import KeyRateReport, SweepReport

__all__ = ["render_excerpts_html", "render_html", "render_sweep_html"]

_STYLE: Final[str] = """
:root { color-scheme: light dark; --fg: #1d1f23; --bg: #ffffff; --muted: #5b6270;
  --rule: #d4d8de; --notice: #fff4e0; --notice-rule: #c77d00; --link: #0b5cad; }
@media (prefers-color-scheme: dark) {
  :root { --fg: #e3e6ea; --bg: #16181c; --muted: #9aa3ae; --rule: #3a3f47;
    --notice: #33280f; --notice-rule: #e0a030; --link: #7ab8ff; }
}
body { font-family: system-ui, sans-serif; color: var(--fg); background: var(--bg);
  max-width: 72rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.45; }
a { color: var(--link); }
h1, h2 { border-bottom: 1px solid var(--rule); padding-bottom: .2rem; }
table { border-collapse: collapse; margin: .6rem 0; width: 100%; }
th, td { border: 1px solid var(--rule); padding: .25rem .45rem; text-align: left;
  vertical-align: top; overflow-wrap: anywhere; }
th { color: var(--muted); font-weight: 600; }
table.matrix { width: auto; display: inline-table; margin: .3rem 1rem .3rem 0; }
table.matrix td { font-variant-numeric: tabular-nums; text-align: right; }
table.matrix caption { text-align: left; font-weight: 600; }
code { font-size: .9em; overflow-wrap: anywhere; }
.notice { border: 2px solid var(--notice-rule); background: var(--notice);
  padding: .4rem 1rem; margin: .8rem 0; }
.notice > strong { display: block; margin: .3rem 0; }
details { margin: .4rem 0; }
summary { cursor: pointer; color: var(--muted); }
""".strip()


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


#: A symbol with a subscript the report writes in plain text (ε_PA, h_lb,
#: λ_EC, k_auth, f_EC, d_Z): one letter, an underscore, the subscript.
_SUBSCRIPT: Final = re.compile(
    r"(?<![\w/#.\-])([\u03b5\u03bb\u03b1\u03b4\u03c4hkfndp])_([A-Za-z]+)(?!\w)"
)
#: A power of two written ``2^-29``, or ``2^-0.413`` (a pass cap's exponent
#: below one).
_POWER: Final = re.compile(r"(?<![\w^])(\d+)\^(-?\d+(?:\.\d+)?)(?!\w)")


def _math(text: str) -> str:
    """Return escaped prose with its symbols' subscripts and powers set as such.

    WHY: a reader of the HTML took ``ε_PA`` and ``2^-29`` for LaTeX that did
    not render. Only prose is touched; code, links and record pointers keep
    their text.
    """
    text = _SUBSCRIPT.sub(r"\1<sub>\2</sub>", text)
    return _POWER.sub(lambda found: f"{found.group(1)}<sup>"
                      f"{found.group(2).replace('-', chr(0x2212))}</sup>", text)


class _HtmlWriter(Writer):
    links_terms = True

    def __init__(self, title: str) -> None:
        self._title = title
        self._parts: list[str] = []

    def _rich(self, rich: Rich) -> str:
        parts: list[str] = []
        for segment in rich:
            if isinstance(segment, Link):
                label = _escape(segment.label)
                if segment.code:
                    label = f"<code>{label}</code>"
                parts.append(f'<a href="{_escape(segment.href)}">{label}</a>')
            elif isinstance(segment, Anchor):
                parts.append(f'<span id="{_escape(segment.id)}"></span>')
            elif isinstance(segment, Code):
                parts.append(
                    f"<code>{_escape(segment.text)}</code>" if segment.text.strip()
                    else "—"
                )
            elif isinstance(segment, Strong):
                parts.append(f"<strong>{_math(_escape(segment.text))}</strong>")
            else:
                parts.append(_math(_escape(segment)))
        return "".join(parts)

    def heading(self, level: int, text: str, anchor: str | None = None) -> None:
        identity = "" if anchor is None else f' id="{_escape(anchor)}"'
        self._parts.append(f"<h{level}{identity}>{_math(_escape(text))}</h{level}>")

    def paragraph(self, rich: Rich) -> None:
        self._parts.append(f"<p>{self._rich(rich)}</p>")

    def bullets(self, items: Sequence[Rich]) -> None:
        body = "".join(f"<li>{self._rich(item)}</li>" for item in items)
        self._parts.append(f"<ul>{body}</ul>")

    def numbered(self, items: Sequence[Rich]) -> None:
        body = "".join(f"<li>{self._rich(item)}</li>" for item in items)
        self._parts.append(f"<ol>{body}</ol>")

    def table(
        self, header: Sequence[str | Rich], rows: Sequence[Sequence[Rich]]
    ) -> None:
        head = "".join(
            f"<th>{_escape(cell) if isinstance(cell, str) else self._rich(cell)}</th>"
            for cell in header
        )
        body = "".join(
            "<tr>" + "".join(f"<td>{self._rich(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        self._parts.append(
            f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        )

    def matrix(
        self,
        caption: str,
        rows: Sequence[str],
        columns: Sequence[str],
        cells: Sequence[Sequence[str]],
    ) -> None:
        head = "<th></th>" + "".join(
            f'<th scope="col">{_escape(label)}</th>' for label in columns
        )
        body = "".join(
            f'<tr><th scope="row">{_escape(label)}</th>'
            + "".join(f"<td>{_escape(cell)}</td>" for cell in row) + "</tr>"
            for label, row in zip(rows, cells, strict=False)
        )
        self._parts.append(
            f'<table class="matrix"><caption>{_escape(caption)}</caption>'
            f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        )

    def notice(self, title: str, items: Sequence[Rich]) -> None:
        body = "".join(f"<li>{self._rich(item)}</li>" for item in items)
        self._parts.append(
            f'<div class="notice"><strong>{_escape(title)}</strong>'
            f"<ul>{body}</ul></div>"
        )

    def details(self, summary: str, body: Callable[[], None], *, open_: bool) -> None:
        self._parts.append(
            f"<details{' open' if open_ else ''}><summary>{_escape(summary)}</summary>"
        )
        body()
        self._parts.append("</details>")

    def text(self) -> str:
        return "\n".join([
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_escape(self._title)}</title>",
            f"<style>\n{_STYLE}\n</style>",
            "</head>",
            "<body>",
            *self._parts,
            "</body>",
            "</html>",
        ]) + "\n"


def render_html(
    report: KeyRateReport,
    *,
    contract_link: ContractLink,
    excerpt_link: ExcerptLink | None = None,
    repo_base: str | None = None,
    lambda_ec: LambdaEcOrigin | None = None,
    repo_served: Callable[[str], bool] | None = None,
) -> str:
    """Return one run's report as a self-contained HTML document.

    ``excerpt_link`` links each record pointer to its excerpt
    (:func:`render_excerpts_html` writes them), ``repo_base`` each repository
    path, and ``repo_served`` (where given) only the paths it accepts, the
    rest printed in code (the Pages site: :func:`pages_site_serves`);
    ``lambda_ec`` is the λ_EC estimate's side file.
    """
    return write_report(
        _HtmlWriter("Key-rate report"), report, contract_link,
        excerpt_link=excerpt_link, repo_base=repo_base, lambda_ec=lambda_ec,
        repo_served=repo_served,
    )


def render_sweep_html(
    sweep: SweepReport,
    *,
    contract_link: ContractLink,
    point_link: PointLink,
    repo_base: str | None = None,
    excerpt_link: ExcerptLink | None = None,
    excerpt_pointers: frozenset[str] = frozenset(),
    repo_served: Callable[[str], bool] | None = None,
) -> str:
    """Return a sweep's report as a self-contained HTML document.

    ``excerpt_link`` links a pointer of ``excerpt_pointers`` (those of the
    point whose setup the sweep shows) to that point's record excerpts.
    """
    return write_sweep(
        _HtmlWriter("Key-rate sweep report"), sweep, contract_link, point_link,
        repo_base=repo_base, excerpt_link=excerpt_link,
        excerpt_pointers=excerpt_pointers, repo_served=repo_served,
    )


def render_excerpts_html(
    record: Mapping[str, Any],
    report: KeyRateReport,
    *,
    report_href: str | None = None,
) -> str:
    """Return the record excerpts of ``report`` as HTML (``record.html``)."""
    return write_excerpts(_HtmlWriter("Record excerpts"), record, report,
                          report_href=report_href)
