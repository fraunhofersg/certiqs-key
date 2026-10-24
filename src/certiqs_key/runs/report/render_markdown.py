"""Render a key-rate report, or a sweep's, as Markdown.

WHY THIS EXISTS. A report must be readable where it is exported and pasted:
an issue, a review, a text editor (the report is record data plus generated
HTML and Markdown). This renderer is the Markdown writer of
the shared section walk in :mod:`certiqs_key.runs.report._render`; it adds
escaping and markup and nothing else.

ESCAPING. Every piece of text from the record or the table is escaped: the
backslash, the backtick, the asterisk, the underscore, both square brackets
and the pipe take a backslash; the ampersand and the less-than sign become
entities; a line break becomes a space. A text that STARTS A LINE and would
open a block there (a heading ``#``, a quote ``>``, a list item ``-``, ``+``
or ``1.`` followed by a space, a thematic break, a ``~~~`` fence) has that
character escaped too; nothing else is, so a number reads ``0.057`` and
``-0.2`` (no backslash inside a number). A
table cell never starts a block, so its text takes no block escape. An empty
identifier is written as a dash, not as an empty code span. Non-ASCII text (ε,
λ, δ) is written as is, the document being UTF-8. A space or parenthesis in a
link target is percent-encoded.
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

__all__ = [
    "escape_markdown",
    "render_excerpts_markdown",
    "render_markdown",
    "render_sweep_markdown",
]

_SPECIAL: Final[str] = "\\`*_[]|"
#: What would open a block where it starts a line: a heading, a quote, a list
#: marker followed by a space, a thematic break, a fence or a setext rule.
_BLOCK_START: Final = re.compile(
    r"^(\s*)(?=#{1,6}(?:\s|$)|>|[+\-](?:\s|$)|(?:-\s*){3,}$|=+\s*$|~~~)(.)"
)
#: An ordered-list marker ``1.`` or ``1)`` followed by a space or the end.
_ORDERED: Final = re.compile(r"^(\s*\d{1,9})([.)])(?=\s|$)")


def _intraword(text: str, index: int) -> bool:
    """Whether the character at ``index`` stands between two letters or digits.

    An underscore there opens and closes no emphasis (CommonMark), so it is
    left unescaped: ``ε_PA`` reads as written in a plain viewer, with no
    backslash before the underscore.
    """
    return (0 < index < len(text) - 1 and text[index - 1].isalnum()
            and text[index + 1].isalnum())


def escape_markdown(text: str, *, line_start: bool = True) -> str:
    """Return ``text`` safe as Markdown inline content and inside a table cell.

    ``line_start`` says whether the text may start a line, where a block
    marker must be escaped too; a table cell's text never does.
    """
    text = text.replace("&", "&amp;").replace("<", "&lt;")
    text = "".join(
        char if char == "_" and _intraword(text, index)
        else "\\" + char if char in _SPECIAL else char
        for index, char in enumerate(text)
    )
    text = " ".join(text.splitlines())
    if not line_start:
        return text
    text = _BLOCK_START.sub(r"\1\\\2", text, count=1)
    return _ORDERED.sub(r"\1\\\2", text, count=1)


def _href(href: str) -> str:
    return href.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def _code(text: str) -> str:
    code = " ".join(text.split())
    if not code:
        return "—"
    code = code.replace("`", "'").replace("|", "\\|")
    return f"`{code}`"


class _MarkdownWriter(Writer):
    def __init__(self) -> None:
        self._lines: list[str] = []

    def _rich(self, rich: Rich, *, line_start: bool = True) -> str:
        parts: list[str] = []
        for segment in rich:
            first = line_start and not parts
            if isinstance(segment, Link):
                if segment.code and segment.label.startswith("/payload"):
                    # A record pointer reads as a short link;
                    # the excerpt it opens is headed by the full pointer.
                    parts.append(f"[record]({_href(segment.href)})")
                    continue
                label = (
                    _code(segment.label) if segment.code
                    else escape_markdown(segment.label, line_start=False)
                )
                parts.append(f"[{label}]({_href(segment.href)})")
            elif isinstance(segment, Anchor):
                parts.append(f'<a id="{html.escape(segment.id)}"></a>')
            elif isinstance(segment, Code):
                parts.append(_code(segment.text))
            elif isinstance(segment, Strong):
                parts.append(f"**{escape_markdown(segment.text, line_start=False)}**")
            else:
                parts.append(escape_markdown(segment, line_start=first))
        return "".join(parts)

    def _block(self, *lines: str) -> None:
        if self._lines:
            self._lines.append("")
        self._lines.extend(lines)

    def heading(self, level: int, text: str, anchor: str | None = None) -> None:
        prefix = "" if anchor is None else f'<a id="{html.escape(anchor)}"></a>'
        self._block(
            f"{'#' * level} {prefix}{escape_markdown(text, line_start=False)}"
        )

    def paragraph(self, rich: Rich) -> None:
        self._block(self._rich(rich))

    def bullets(self, items: Sequence[Rich]) -> None:
        self._block(*(f"- {self._rich(item)}" for item in items))

    def numbered(self, items: Sequence[Rich]) -> None:
        self._block(*(
            f"{index}. {self._rich(item)}"
            for index, item in enumerate(items, start=1)
        ))

    def _table(self, header: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
        def line(cells: Sequence[str]) -> str:
            return "| " + " | ".join(cell or " " for cell in cells) + " |"

        self._block(line(header), line(["---"] * len(header)),
                    *(line(row) for row in rows))

    def table(
        self, header: Sequence[str | Rich], rows: Sequence[Sequence[Rich]]
    ) -> None:
        self._table(
            [escape_markdown(cell, line_start=False) if isinstance(cell, str)
             else self._rich(cell, line_start=False) for cell in header],
            [[self._rich(cell, line_start=False) for cell in row] for row in rows],
        )

    def matrix(
        self,
        caption: str,
        rows: Sequence[str],
        columns: Sequence[str],
        cells: Sequence[Sequence[str]],
    ) -> None:
        self._block(f"*{escape_markdown(caption, line_start=False)}*")
        self._table(
            [" ", *(escape_markdown(label, line_start=False) for label in columns)],
            [
                [f"**{escape_markdown(label, line_start=False)}**",
                 *(escape_markdown(cell, line_start=False) for cell in row)]
                for label, row in zip(rows, cells, strict=False)
            ],
        )

    def notice(self, title: str, items: Sequence[Rich]) -> None:
        self._block(
            f"> **{escape_markdown(title, line_start=False)}**",
            ">",
            *(f"> - {self._rich(item)}" for item in items),
        )

    def details(self, summary: str, body: Callable[[], None], *, open_: bool) -> None:
        del summary, open_
        body()

    def text(self) -> str:
        return "\n".join(self._lines) + "\n"


def render_markdown(
    report: KeyRateReport,
    *,
    contract_link: ContractLink,
    excerpt_link: ExcerptLink | None = None,
    repo_base: str | None = None,
    lambda_ec: LambdaEcOrigin | None = None,
    repo_served: Callable[[str], bool] | None = None,
) -> str:
    """Return one run's report as Markdown.

    ``excerpt_link`` links each record pointer to its excerpt
    (:func:`render_excerpts_markdown` writes them), ``repo_base`` each
    repository path, and ``repo_served`` (where given) only the paths it
    accepts, the rest printed in code; ``lambda_ec`` is the λ_EC estimate's
    side file.
    """
    return write_report(
        _MarkdownWriter(), report, contract_link,
        excerpt_link=excerpt_link, repo_base=repo_base, lambda_ec=lambda_ec,
        repo_served=repo_served,
    )


def render_sweep_markdown(
    sweep: SweepReport,
    *,
    contract_link: ContractLink,
    point_link: PointLink,
    repo_base: str | None = None,
    excerpt_link: ExcerptLink | None = None,
    excerpt_pointers: frozenset[str] = frozenset(),
    repo_served: Callable[[str], bool] | None = None,
) -> str:
    """Return a sweep's report as Markdown, each point linked by ``point_link``.

    ``excerpt_link`` links a pointer of ``excerpt_pointers`` (those of the
    point whose setup the sweep shows) to that point's record excerpts.
    """
    return write_sweep(_MarkdownWriter(), sweep, contract_link, point_link,
                       repo_base=repo_base, excerpt_link=excerpt_link,
                       excerpt_pointers=excerpt_pointers, repo_served=repo_served)


def render_excerpts_markdown(
    record: Mapping[str, Any],
    report: KeyRateReport,
    *,
    report_href: str | None = None,
) -> str:
    """Return the record excerpts of ``report`` as Markdown (``record.md``)."""
    return write_excerpts(_MarkdownWriter(), record, report, report_href=report_href)
