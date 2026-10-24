"""What the Markdown and HTML renderers share: the primitives and section writers.

Since report 0.9.0 the run report's page order lives in
:mod:`certiqs_key.runs.report._page` (three layers: summary, detail,
appendix); this module keeps the primitives both use, the section writers the
page and the sweep share, and the sweep's walk.

WHY THIS EXISTS. The two renderers of the key-rate report
must show the same content in the
same order: sections R1-R6 under fixed headings, the not-counted flags first,
each claim as ``kind_word "title"`` with its summary and its contract link,
each assumption with its ``user_statement`` as the main text. Writing that
walk twice would let the two drift; here it is written once against a small
:class:`Writer` interface, and each renderer supplies the writer (escaping,
markup) and nothing else.

ONLY HEADINGS AND LABELS ARE AUTHORED HERE. Every sentence a reader sees is a
claim's own plain-text field, a value of the record, one of the three flag
texts the report object carries, a user-declared item's text (the protocol
document layer's own sentence, carried in the record), the setup section's
run-tier sentences (:mod:`certiqs_key.runs.report.setup`, carried in the
report object), or one of the
run-tier sentences of
``build.py`` that say why R3 and R4 are empty on a refused run
(:data:`~certiqs_key.runs.report.build.REFUSED_NOT_LISTED`,
:data:`~certiqs_key.runs.report.build.SWEEP_ALL_REFUSED`); table headers and
section headings are labels, and so are the few words around a λ_EC estimate
read from its side file (:class:`LambdaEcOrigin`). Deterministic: no render
time is printed, floats are ``repr`` (matrix entries: six significant
digits), and everything iterates in the report object's order.

LINKS IN CARRIED TEXT (report 0.8.0). Besides the
``[[...]]`` tokens, a plain-text segment links three things where they
resolve: a claim id the report's index carries (full, module-relative or the
bare ``kind:label`` of the text's own module,
:func:`~certiqs_key.runs.report.build.resolve_claim_mention`); a record
pointer the report object holds, to its record excerpt, where the caller
wrote excerpts (:func:`report_pointers`, :func:`excerpt_anchor`); and a
repository path, to ``<repo_base><path>``, where the caller gave a base
(:data:`REPO_PATH_RE`, :func:`cited_repo_paths`).
"""

from __future__ import annotations

import json
import math
import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any, ClassVar, Final

from certiqs_key.runs.report.build import (
    CLAIM_MENTION_RE,
    resolve_claim_mention,
)
from certiqs_key.runs.report.explain import (
    DEVICE_CATEGORIES,
    ENGINE_CATEGORIES,
    binding_words,
    consequence_words,
)
from certiqs_key.runs.report.glossary import Term, categories, term_anchor
from certiqs_key.runs.report.inputs import same_number
from certiqs_key.runs.report.model import (
    AlphaBound,
    AlphaSearchDetail,
    AlphaUsed,
    AssumptionEntry,
    AssumptionsSection,
    Binding,
    CategoryGroup,
    Check,
    ClaimRef,
    ContractAnchor,
    Emission,
    Flag,
    InputRow,
    MeasurementSnaps,
    NotEngaged,
    NumericsSection,
    Points,
    ReportIndex,
    SweepPoint,
    UserDeclared,
)

__all__ = [
    "PAGES_SITE_SERVES",
    "REPO_PATH_RE",
    "RESIDUE_NOTE",
    "SECTION_TITLES",
    "Anchor",
    "Code",
    "ContractLink",
    "ExcerptLink",
    "LambdaEcOrigin",
    "Link",
    "PointLink",
    "Rich",
    "Strong",
    "Writer",
    "cited_repo_paths",
    "default_contract_link",
    "excerpt_anchor",
    "format_entry",
    "format_value",
    "pages_site_serves",
    "parameter_anchor",
    "readable_value",
    "reference_urls",
    "report_pointers",
]

#: Builds the URL of a claim's statement from its contract anchor.
type ContractLink = Callable[[ContractAnchor], str]
#: Builds the URL of a sweep point's own report.
type PointLink = Callable[[SweepPoint], str]
#: Builds the URL of a record pointer's excerpt (report 0.8.0).
type ExcerptLink = Callable[[str], str]
#: A λ_EC estimate's side file, ``<record stem>.lambda-ec.json``, as read.
type LambdaEcOrigin = Mapping[str, Any]

#: THE SECTION HEADINGS of a run report, in page order (report 0.9.0): the
#: summary, the detail a reader needs, the appendix.
SECTION_TITLES: Final[Mapping[str, str]] = {
    "summary": "Summary",
    "setup": "Your QKD setup",
    "inputs": "Your inputs",
    "assumptions": "Assumptions you vouch for",
    "snaps": "Measurement snaps",
    "appendix": "Appendix",
}


#: The footnote of a block whose floating-point residue is shown as 0.
RESIDUE_NOTE: Final[str] = (
    "Entries below 1e-12 of the block's largest are floating-point residue and "
    "shown as 0; the unrounded values are in the record excerpt."
)
#: Relative to a block's largest entry, what counts as floating-point residue.
_RESIDUE: Final[float] = 1e-12

_LINK_RE: Final = re.compile(r"\[\[([^\[\]]+)\]\]")
_SHORT_ID_RE: Final = re.compile(r"^A-[A-Z0-9-]+$")
#: A record pointer in text: ``/payload`` and its tokens, up to a delimiter.
_POINTER_RE: Final = re.compile(r"/payload(?:/[^\s\"'<>,;()\[\]{}|]*)*")

#: A REPOSITORY PATH a report prints (an instance readme, an honest model's
#: derivation, a ``spec/`` section, ``created_by``): a relative path under one
#: of the tree's top-level folders, ending in a file extension.
REPO_PATH_RE: Final = re.compile(
    r"(?<![\w/.\-])((?:spec|instances|runs|src|reports|harness|tests|refs|state"
    r"|context)/[\w./\-]*[\w\-]\.[A-Za-z0-9]+)(?![\w/])"
)

#: Above this dimension a matrix is collapsed.
_COLLAPSE_ABOVE: Final[int] = 8


@dataclass(frozen=True)
class Link:
    """A link: its label and its target; ``code`` shows the label as code."""

    label: str
    href: str
    code: bool = False


@dataclass(frozen=True)
class Anchor:
    """A named place in the document a link may point at."""

    id: str


@dataclass(frozen=True)
class Code:
    """An identifier, shown verbatim (an id, a key, a pointer)."""

    text: str


@dataclass(frozen=True)
class Strong:
    """Text shown in bold: the key part of an at-a-glance fragment."""

    text: str


type Segment = str | Link | Anchor | Code | Strong
type Rich = list[Segment]


def default_contract_link(base: str = "") -> ContractLink:
    """Return ``f"{base}{pdf}#nameddest={anchor}"``; base ``""`` is repo-relative."""

    def link(contract: ContractAnchor) -> str:
        return f"{base}{contract['pdf']}#nameddest={contract['anchor']}"

    return link


def excerpt_anchor(pointer: str) -> str:
    """Return the anchor of a record pointer's excerpt: ``p-`` and a safe escape.

    Letters, digits, ``-`` and ``_`` stay; ``/`` becomes ``.``; every other
    character becomes ``~<hex>~``. The map is injective, so two pointers never
    share an anchor, and the result is safe in an ``id`` and a URL fragment.
    """
    parts: list[str] = []
    for char in pointer:
        if char.isascii() and (char.isalnum() or char in "-_"):
            parts.append(char)
        elif char == "/":
            parts.append(".")
        else:
            parts.append(f"~{ord(char):x}~")
    return "p-" + "".join(parts)


def report_pointers(document: Any) -> list[str]:
    """Return every record pointer a report object holds, once, in its order.

    A pointer is a string value starting ``/payload``: the ``pointer`` of a
    row, a fact, a binding, a setup step or family, and the ``*_pointer``
    fields alike.
    """
    found: dict[str, None] = {}

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str) and _POINTER_RE.fullmatch(value):
            found.setdefault(value)

    walk(document)
    return list(found)


def cited_repo_paths(document: str, repo_base: str) -> list[str]:
    """Return the repository paths a rendered report links through ``repo_base``.

    Every link target ``<repo_base><path>`` with no fragment, ``path`` a
    :data:`REPO_PATH_RE` path, once and sorted; what a package build copies
    into the package at its repository path (contract PDFs, which carry a
    ``#nameddest`` fragment, are listed by the build's own rule).
    """
    pattern = re.compile(
        re.escape(repo_base) + r"((?:spec|instances|runs|src|reports|harness|tests"
        r"|refs|state|context)/[^#\"'()\s<>]+)(?=[\"')])"
    )
    return sorted({
        match.group(1) for match in pattern.finditer(document)
        if REPO_PATH_RE.fullmatch(match.group(1))
    })


#: WHAT THE PAGES SITE SERVES, as repository paths with ``*`` matching one
#: path segment: the same patterns as ``ALLOW`` of harness/build_pages_site.py,
#: which builds the site (tests/unit/test_report_publication_sweep.py keeps
#: the two equal; the package cannot import the harness). A report published there
#: links a repository path only where the site serves it; any other path
#: (an instance README, spec/architecture.md) would be a dead link on the
#: site and is printed as code instead.
PAGES_SITE_SERVES: Final[tuple[str, ...]] = (
    "spec/modules/*/contract.pdf",
    "spec/modules/*/digest.pdf",
    "spec/modules/*/graphs/*.svg",
    "spec/modules/*/graphs/*.pdf",
    "spec/module-graph.svg",
    "spec/module-graph.pdf",
    "spec/overview/overview.pdf",
    "runs/report_examples/*/report.html",
    "runs/report_examples/*/record.html",
    "runs/report_examples/*/sweep.html",
    "runs/report_examples/*/points/*.html",
    "runs/bbm92_study/data/headline-report/report.html",
    "runs/bbm92_study/data/headline-report/record.html",
    "whitepaper/*.pdf",
)

_SERVED_RE: Final = tuple(
    re.compile("".join("[^/]+" if part == "*" else re.escape(part)
                       for part in re.split(r"(\*)", pattern)) + r"\Z")
    for pattern in PAGES_SITE_SERVES
)


def pages_site_serves(path: str) -> bool:
    """Return whether the Pages site serves a repository path.

    The patterns are :data:`PAGES_SITE_SERVES`.
    """
    return any(pattern.match(path) for pattern in _SERVED_RE)


def format_value(value: Any) -> str:
    """Return a value as text: exact integers, ``repr`` floats, compact JSON."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _is_zero(part: str | float, floor: float = 0.0) -> bool:
    if isinstance(part, float):
        return part == 0.0 or abs(part) < floor
    try:
        return Fraction(part) == 0
    except (ValueError, ZeroDivisionError):
        return part.strip() in {"0", "-0", "0.0"}


def _part(part: str | float) -> str:
    """Return one real part: an exact string as is, binary64 to 6 digits.

    An exact fraction with a long denominator reads decimal first, the
    fraction beside it: ``≈ 0.5 (549755813889/1099511627776)``.
    """
    if isinstance(part, str):
        if "/" in part:
            try:
                value = Fraction(part)
            except (ValueError, ZeroDivisionError):
                return part
            if value.denominator > 1000:
                return f"≈ {float(value):.6g} ({part})"
        return part
    if part == 0.0:
        return "0"
    return f"{part:.6g}"


def magnitude(part: str | float) -> float:
    """Return the modulus of one real part of a matrix entry (0 if unreadable)."""
    if isinstance(part, float):
        return abs(part)
    try:
        return abs(float(Fraction(part)))
    except (ValueError, ZeroDivisionError, OverflowError):
        return 0.0


def residue_floor(entries: Iterable[Sequence[str | float]]) -> float:
    """Return below what a binary64 part counts as residue: 1e-12 of the largest."""
    largest = max(
        (magnitude(part) for entry in entries for part in entry), default=0.0
    )
    return _RESIDUE * largest


def is_residue(entry: Sequence[str | float], floor: float) -> bool:
    """Whether a binary64 part of ``entry`` is non-zero but below ``floor``."""
    return any(
        isinstance(part, float) and part != 0.0 and abs(part) < floor
        for part in entry
    )


def format_entry(entry: Sequence[str | float], floor: float = 0.0) -> str:
    """Return a matrix entry ``[re, im]`` as text: ``a``, ``bi`` or ``a + bi``.

    An exact ``"p/q"`` string is shown exactly (decimal first, the fraction
    beside it, where the denominator exceeds 1000); a binary64 number to six
    significant digits,
    in e-notation where small. A binary64 part below ``floor`` (the block's
    floating-point residue, :func:`residue_floor`) is shown as 0.
    """
    real, imaginary = entry[0], entry[1] if len(entry) > 1 else 0.0
    if isinstance(real, float) and _is_zero(real, floor):
        real = 0.0
    if _is_zero(imaginary, floor):
        return _part(real)
    negative = magnitude(imaginary) > 0 and _negative(imaginary)
    imag = _imaginary(_part(_absolute(imaginary) if negative else imaginary))
    if _is_zero(real):
        return f"{'-' if negative else ''}{imag}"
    sign = "\u2212" if negative else "+"
    return f"{_part(real)} {sign} {imag}"


#: An exact fraction as :func:`_part` shows it, ``p/q``.
_SHORT_FRACTION: Final = re.compile(r"^(\d+)/(\d+)$")


def _imaginary(part: str) -> str:
    """Return an imaginary part with its ``i``: ``i/8``, ``3i/8``, ``0.5i``.

    A fraction takes the i in its numerator: ``1/8i`` reads as 1/(8i), which
    is -i/8. A decimal with its fraction beside it is bracketed before the i.
    """
    found = _SHORT_FRACTION.match(part)
    if found is not None:
        numerator, denominator = found.groups()
        return f"{'' if numerator == '1' else numerator}i/{denominator}"
    return f"({part})i" if " " in part else f"{part}i"


def _negative(part: str | float) -> bool:
    """Whether one real part of a matrix entry is below zero."""
    if isinstance(part, float):
        return part < 0
    try:
        return Fraction(part) < 0
    except (ValueError, ZeroDivisionError):
        return part.strip().startswith("-")


def _absolute(part: str | float) -> str | float:
    """Return one real part without its sign, exact strings kept exact."""
    if isinstance(part, float):
        return abs(part)
    return part.strip().lstrip("-")


class Writer(ABC):
    """The markup a renderer supplies; every argument is unescaped text.

    ``links_terms`` says whether the first label naming a glossary term links
    to it (HTML); Markdown prints the glossary at the end and links nothing.
    """

    links_terms: ClassVar[bool] = False

    @abstractmethod
    def heading(self, level: int, text: str, anchor: str | None = None) -> None:
        """Write a heading, with an anchor id where given."""

    @abstractmethod
    def paragraph(self, rich: Rich) -> None:
        """Write a paragraph."""

    @abstractmethod
    def bullets(self, items: Sequence[Rich]) -> None:
        """Write a bulleted list."""

    @abstractmethod
    def numbered(self, items: Sequence[Rich]) -> None:
        """Write a numbered list."""

    @abstractmethod
    def table(
        self, header: Sequence[str | Rich], rows: Sequence[Sequence[Rich]]
    ) -> None:
        """Write a table: a header row of labels and rows of rich cells."""

    @abstractmethod
    def matrix(
        self,
        caption: str,
        rows: Sequence[str],
        columns: Sequence[str],
        cells: Sequence[Sequence[str]],
    ) -> None:
        """Write a matrix with its caption and its row and column basis labels."""

    @abstractmethod
    def notice(self, title: str, items: Sequence[Rich]) -> None:
        """Write a prominent notice (the not-counted flags)."""

    @abstractmethod
    def details(self, summary: str, body: Callable[[], None], *, open_: bool) -> None:
        """Write collapsible content; ``body`` writes it."""

    @abstractmethod
    def text(self) -> str:
        """Return the document."""


@dataclass
class _Context:
    """What resolving a link needs: the index, the link builders, what is shown."""

    index: ReportIndex
    contract_link: ContractLink
    present: set[str] = field(default_factory=set)
    #: Whether the page renders the numerical-trust premises ("The engine's
    #: numerics"), which a first-order run's floating-point gap links to;
    #: without them the gap links to Not counted, which names it too.
    numerics: bool = False
    inputs: set[str] = field(default_factory=set)
    #: How ``points: "all"`` reads: "all completed points" in a sweep with a
    #: refused point, whose rows are the completed points'.
    all_points: str = "all points"
    #: Where a record pointer's excerpt is, or ``None`` without excerpts.
    excerpt_link: ExcerptLink | None = None
    #: The pointers the excerpts hold (the report object's).
    pointers: frozenset[str] = frozenset()
    #: The prefix of a repository path's link, or ``None`` (plain text).
    repo_base: str | None = None
    #: Which repository paths the place the page is published at serves; a
    #: path it does not serve is printed in code, not linked (``None``: every
    #: path links). The Pages site serves contracts, digests, graphs and the
    #: example pages only (:func:`pages_site_serves`).
    repo_served: Callable[[str], bool] | None = None
    #: Whether the first label naming a glossary term links to it (HTML).
    link_terms: bool = False
    #: The glossary entries by alias, and the terms already linked.
    aliases: Mapping[str, Term] = field(default_factory=dict)
    linked: set[str] = field(default_factory=set)
    #: The acceptance outcomes, printed once in the setup and referenced
    #: wherever a value repeats them.
    outcomes: tuple[str, ...] = ()
    #: Each acceptance outcome's honest probability as the setup's acceptance
    #: table shows it; a binding that holds the same probabilities links that
    #: table instead of repeating them.
    honest: Mapping[str, float] = field(default_factory=dict)
    #: The parameters of the honest model the page names by their key, each
    #: with its readable label and its meaning from the instance's parameter
    #: table: the glossary defines each, and the setup links it there.
    parameters: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    #: The verification sentence said once for the group being written; an
    #: entry whose sentence differs says its own.
    common_verification: str | None = None
    #: What an input that has no effect on this run says about it, by name
    #: (the setup's source table repeats it beside the value).
    unused: Mapping[str, str] = field(default_factory=dict)
    #: Whether the page describes a photon-number station (or none): the
    #: glossary's optical entries are printed only then.
    optical: bool = True


def _label(text: str, ctx: _Context | None) -> Rich:
    """Return a label, linked to its glossary entry the first time (HTML)."""
    if ctx is None or not ctx.link_terms:
        return [text]
    term = ctx.aliases.get(text)
    if term is None or term.term in ctx.linked:
        return [text]
    ctx.linked.add(term.term)
    return [Link(text, f"#{term.anchor}")]


def _header(labels: Sequence[str], ctx: _Context | None) -> list[str | Rich]:
    return [_label(label, ctx) for label in labels]


def _claim_link(claim: ClaimRef, ctx: _Context) -> Link:
    return Link(f'{claim["kind_word"]} "{claim["title"]}"',
                ctx.contract_link(claim["contract"]))


def _module_of(claim_id: str | None) -> str | None:
    if claim_id is None or ":" not in claim_id:
        return None
    return claim_id.split(":", 1)[0].rsplit("/", 1)[0] or None


#: A registered reference id as the report prints one (``kamin2025renyi``).
_REF_ID_RE: Final = re.compile(r"\b([a-z]+\d{4}[a-z0-9]*)\b")

#: The registry of citable sources, where the renderer runs from a checkout.
_REFERENCES: Final[Path] = (
    Path(__file__).resolve().parents[4] / "refs" / "index.json"
)


@cache
def reference_urls() -> Mapping[str, str]:
    """Return the link of each registered reference: its DOI, else its arXiv page.

    WHY: a reference id the report prints (the source of f_EC, say) is a
    pointer a reader should be able to follow. refs/index.json is the only
    citable universe; it is read where the renderer runs from a checkout, and
    without it (an installed package) the id stays plain text.
    """
    if not _REFERENCES.is_file():
        return {}
    data = json.loads(_REFERENCES.read_text(encoding="utf-8"))
    urls: dict[str, str] = {}
    for entry in data.get("entries") or ():
        if not isinstance(entry, Mapping) or not entry.get("ref_id"):
            continue
        if entry.get("doi"):
            urls[str(entry["ref_id"])] = f"https://doi.org/{entry['doi']}"
        elif entry.get("arxiv_id"):
            urls[str(entry["ref_id"])] = (
                f"https://arxiv.org/abs/{entry['arxiv_id']}"
                + str(entry.get("arxiv_version") or "")
            )
        elif entry.get("url"):
            urls[str(entry["ref_id"])] = str(entry["url"])
    return urls


def parameter_anchor(name: str) -> str:
    """Return the glossary anchor of a parameter the page names by its key."""
    return term_anchor(f"param {name}")


def _linkify(text: str, ctx: _Context, module: str | None = None) -> Rich:
    """Split plain text at the claim ids, record pointers and repo paths it names.

    Each resolves to a link where it can (a claim of the index; a pointer of
    the excerpts; a path, given a repository base); anything else stays text.
    """
    found: list[tuple[int, int, Segment]] = []
    claims = ctx.index["claims"]
    mentions = ctx.index.get("mentions") or {}
    for match in CLAIM_MENTION_RE.finditer(text):
        token = match.group(1).rstrip(".")
        claim_id = resolve_claim_mention(token, claims, module)
        if claim_id is not None:
            found.append((match.start(1), match.start(1) + len(token),
                          _claim_link(claims[claim_id], ctx)))
        elif token in mentions or f"{module}/{token}" in mentions:
            # A claim the closure table does not carry, linked by its id, or a bare id
            # of the text's own module; the label stays the id as written.
            anchor = mentions.get(token) or mentions[f"{module}/{token}"]
            found.append((match.start(1), match.start(1) + len(token),
                          Link(token, ctx.contract_link(anchor))))
    if ctx.excerpt_link is not None:
        for match in _POINTER_RE.finditer(text):
            pointer = match.group(0)
            while pointer and pointer not in ctx.pointers and pointer[-1] in ".:":
                pointer = pointer[:-1]
            if pointer in ctx.pointers:
                found.append((match.start(), match.start() + len(pointer),
                              Link(pointer, ctx.excerpt_link(pointer), code=True)))
    for match in _REF_ID_RE.finditer(text):
        url = reference_urls().get(match.group(1))
        if url is not None:
            found.append((match.start(1), match.end(1), Link(match.group(1), url)))
    if ctx.repo_base is not None:
        for match in REPO_PATH_RE.finditer(text):
            path = match.group(1)
            served = ctx.repo_served is None or ctx.repo_served(path)
            found.append((match.start(1), match.end(1),
                          Link(path, ctx.repo_base + path) if served
                          else Code(path)))
    if not found:
        return [text] if text else []
    rich: Rich = []
    position = 0
    for start, end, segment in sorted(found, key=lambda item: (item[0], -item[1])):
        if start < position:
            continue
        if start > position:
            rich.append(text[position:start])
        rich.append(segment)
        position = end
    if position < len(text):
        rich.append(text[position:])
    return rich


def _rich_text(text: str, ctx: _Context, module: str | None = None) -> Rich:
    """Split carried text at its ``[[...]]`` tokens and resolve each to a link.

    The text between tokens is linked further by :func:`_linkify`; ``module``
    is the text's own module, against which a bare ``kind:label`` resolves.
    """
    rich: Rich = []
    position = 0
    for match in _LINK_RE.finditer(text):
        if match.start() > position:
            rich.extend(_linkify(text[position:match.start()], ctx, module))
        target = match.group(1).strip()
        rich.append(_target(target, ctx))
        position = match.end()
    if position < len(text):
        rich.extend(_linkify(text[position:], ctx, module))
    return rich


def _target(target: str, ctx: _Context) -> Segment:
    """Return the link a ``[[...]]`` target renders as, or the bare target."""
    if _SHORT_ID_RE.match(target):
        if target in ctx.present:
            return Link(target, f"#{target}")
        owner = ctx.index["assumptions"].get(target)
        claim = None if owner is None else ctx.index["claims"].get(owner)
        if claim is not None:
            return Link(target, ctx.contract_link(claim["contract"]))
        return target
    claim = ctx.index["claims"].get(target)
    if claim is not None:
        return _claim_link(claim, ctx)
    mention = (ctx.index.get("mentions") or {}).get(target)
    return target if mention is None else Link(target, ctx.contract_link(mention))


def _claim_item(claim: ClaimRef, ctx: _Context) -> Rich:
    return [_claim_link(claim, ctx), ": ",
            *_rich_text(claim["summary"], ctx, _module_of(claim["id"]))]


def _joined(segments: Iterable[Segment], separator: str = ", ") -> Rich:
    rich: Rich = []
    for position, segment in enumerate(segments):
        if position:
            rich.append(separator)
        rich.append(segment)
    return rich


def readable_value(value: Any) -> str:
    """Return a table cell's value in words: a mapping as ``key = value; ...``.

    WHY: an appendix cell printed as raw JSON (``{"gap_tolerance": null}``)
    reads as a rendering fault and puts ``null`` into English. A mapping reads
    ``key = value`` joined by ``; ``, a list by ``, ``, a nested one in
    parentheses, an absent value (JSON null) inside one as ``none`` and an
    empty list or mapping inside one as ``empty`` (``constrained`` null and
    ``[]`` mean different things); a scalar as :func:`format_value`. Every key
    and every value stays.
    """
    if isinstance(value, Mapping):
        if not value:
            return "none"
        return "; ".join(
            f"{key} = {_nested_value(item)}" for key, item in value.items()
        )
    if isinstance(value, list):
        if not value:
            return "none"
        return ", ".join(_nested_value(item) for item in value)
    return format_value(value)


def _nested_value(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, Mapping | list):
        return "(" + readable_value(value) + ")" if value else "empty"
    return readable_value(value)


def _value(value: Any, ctx: _Context | None = None) -> Rich:
    text = readable_value(value)
    return [text] if ctx is None else _linkify(text, ctx) or [text]


def _pointer(pointer: str | None, ctx: _Context | None = None) -> Rich:
    if not pointer:
        return []
    if ctx is not None and ctx.excerpt_link is not None and pointer in ctx.pointers:
        return [Link(pointer, ctx.excerpt_link(pointer), code=True)]
    return [Code(pointer)]


def _points_label(points: Points, all_points: str) -> str:
    """Return where a sweep row holds: ``all points`` or ``points 0, 2``.

    ``"all"`` means every COMPLETED point; ``all_points`` says so where a
    point was refused ("all completed points").
    """
    if points == "all":
        return all_points
    return "points " + ", ".join(str(index) for index in points)


# --------------------------------------------------------------------------
# Section writers, shared by the run and the sweep
# --------------------------------------------------------------------------


def _flags(writer: Writer, flags: Sequence[Flag], ctx: _Context) -> None:
    if not flags:
        return
    writer.notice(
        "Not counted",
        [
            [Code(flag["parameter"] if flag["value"] is None
                  else f"{flag['parameter']} = {format_value(flag['value'])}"),
             ": ", flag["text"], " (",
             *_joined(_target(short_id, ctx) for short_id in flag["assumptions"]),
             ")",
             *([] if "points" not in flag
               else [" [", _points_label(flag["points"], ctx.all_points), "]"])]
            for flag in flags
        ],
    )


def _declared_item(item: UserDeclared, ctx: _Context) -> Rich:
    premises = item["assumptions"]
    return [
        Code(item["kind"]), " ", Code(item["label"]), ": ", item["text"],
        *([] if not premises else [
            " (", *_joined(_target(short_id, ctx) for short_id in premises), ")"
        ]),
        *([] if "points" not in item
          else [" [", _points_label(item["points"], ctx.all_points), "]"]),
    ]


def _user_declared(
    writer: Writer, items: Sequence[UserDeclared], ctx: _Context
) -> None:
    """Show what the protocol document declared, styled like the flags (0.3.0).

    Worded for a shipped template as for the user's own document: either may
    declare, and the user who runs it vouches.
    """
    if not items:
        return
    writer.notice(
        "Declared in the protocol document, not derived by the engine",
        [_declared_item(item, ctx) for item in items],
    )


def _declared_by_you(
    writer: Writer, items: Sequence[UserDeclared], ctx: _Context, level: int = 3
) -> None:
    """List the user-declared premises under the assumptions they name (0.3.0)."""
    if not items:
        return
    writer.heading(level, "Declared in the protocol document, vouched for by you")
    writer.table(
        ["Assumption", "Kind", "Label", "Declared", "Record"],
        [
            [
                _joined(_target(short_id, ctx) for short_id in item["assumptions"])
                or ["—"],
                [Code(item["kind"])],
                [Code(item["label"])],
                [item["text"],
                 *([] if "points" not in item
                   else [" [", _points_label(item["points"], ctx.all_points), "]"])],
                _pointer(item["pointer"], ctx),
            ]
            for item in items
        ],
    )


def _claim_list(
    writer: Writer, title: str, claims: Sequence[ClaimRef], ctx: _Context,
    level: int = 3,
) -> None:
    if not claims:
        return
    writer.heading(level, title)
    writer.bullets([_claim_item(claim, ctx) for claim in claims])


#: Above this length a binding's value is cut, with a link to the record.
_LONG_VALUE: Final[int] = 200


def _words(value: Any, outcomes: Sequence[str] = ()) -> str:
    """Return a binding value in words: lists joined, mappings as ``k = v``.

    A list that is the acceptance alphabet reads as "the N acceptance
    outcomes", printed once in the setup (a value written in full would repeat it).
    """
    if isinstance(value, list):
        if outcomes and [str(item) for item in value] == list(outcomes):
            return f"the {len(outcomes)} acceptance outcomes (see Acceptance test)"
        return ", ".join(_words(item, outcomes) for item in value)
    if isinstance(value, Mapping):
        return ", ".join(
            f"{key} = {_words(item, outcomes)}" for key, item in value.items()
        )
    return with_decimal(value)


def _binding_value(binding: Binding, ctx: _Context) -> Rich:
    """Return a binding's value in words."""
    if binding.get("varies"):
        return ["varies between the points"]
    if "value" in binding:
        value = binding["value"]
        special = binding_words(binding["name"], value)
        if special is not None:
            return _linkify(special, ctx) or [special]
        if ctx.outcomes and isinstance(value, list) and (
            [str(item) for item in value] == list(ctx.outcomes)
        ):
            return [Link(f"the {len(ctx.outcomes)} acceptance outcomes",
                         "#setup-acceptance")]
        if _same_as_table(value, ctx):
            pointer = str(binding.get("pointer") or "")
            exact: Rich = (
                [" (exact fractions: ", Link("record", ctx.excerpt_link(pointer)), ")"]
                if ctx.excerpt_link is not None and pointer in ctx.pointers else []
            )
            return ["the honest probability of each acceptance outcome, as in ",
                    Link("the table under Acceptance test", "#setup-acceptance"),
                    *exact]
        words = _words(value, ctx.outcomes)
        if not words:
            # An empty list or mapping: a blank after the colon reads as a
            # value lost in rendering.
            return ["none"]
        if len(words) <= _LONG_VALUE:
            return _linkify(words, ctx) or [words]
        rows = _outcome_rows(binding, ctx)
        if rows is not None:
            nonzero = sum(1 for _, found in rows if found != 0)
            return [f"{nonzero} nonzero of {len(rows)} probabilities, in the table "
                    "below"]
        if _cut_in_full(binding, ctx) is not None:
            # Written out in full beneath, folded: a cut preview here would
            # print its start twice.
            return [f"{len(words):,} characters, written out in full below"]
        tail: Rich = (
            [Link("see the record", ctx.excerpt_link(str(binding.get("pointer"))))]
            if ctx.excerpt_link is not None else ["see the record"]
        )
        return [words[:160].rstrip() + f"… ({len(words):,} characters; ", *tail, ")"]
    name = binding.get("input", binding["name"])
    if name in ctx.inputs:
        return [Link(name, f"#input-{name}")]
    return [Code(name)]


def _probability_rows(value: Any) -> list[tuple[str, Fraction]] | None:
    """Return a mapping of names to probabilities as rows, or ``None``.

    Every value must be a number in [0, 1] (an exact ``p/q`` or a float);
    anything else (an envelope of bounds, say) is not a probability map.
    """
    if not isinstance(value, Mapping) or not value:
        return None
    rows: list[tuple[str, Fraction]] = []
    for key, item in value.items():
        if isinstance(item, bool) or not isinstance(item, int | float | str):
            return None
        try:
            found = Fraction(str(item).strip())
        except (ValueError, ZeroDivisionError):
            return None
        if not 0 <= found <= 1:
            return None
        rows.append((str(key), found))
    return rows


def _outcome_rows(binding: Binding, ctx: _Context) -> list[tuple[str, Fraction]] | None:
    """Return a binding's probabilities per acceptance outcome as rows, or None.

    The honest distribution, or a probability map whose keys are all
    acceptance outcomes; any other mapping is not read as one.
    """
    rows = _probability_rows(binding.get("value"))
    if rows is None:
        return None
    if binding["name"] == "honest_distribution" or (
        ctx.outcomes and {key for key, _ in rows} <= set(ctx.outcomes)
    ):
        return rows
    return None


def _same_as_table(value: Any, ctx: _Context) -> bool:
    """Whether a binding holds the probabilities the acceptance table shows.

    Each of its outcomes is in the table with the same binary64 value, and
    every outcome of the table it omits has probability 0 there.
    """
    rows = _probability_rows(value)
    if rows is None or not ctx.honest:
        return False
    held = dict(rows)
    if not set(held) <= set(ctx.honest):
        return False
    return all(float(held[key]) == ctx.honest[key] for key in held) and all(
        ctx.honest[key] == 0 for key in ctx.honest if key not in held
    )


def _probability_table(writer: Writer, name: str, rows: Sequence[tuple[str, Fraction]],
                       ctx: _Context) -> None:
    """Write a probability map's nonzero entries as a table, collapsed."""
    nonzero = [(key, found) for key, found in rows if found != 0]

    def body() -> None:
        writer.table(
            _header(["Outcome", "Probability", "Exact"], ctx),
            [[[key], [f"{float(found):.6g}"], [str(found)]] for key, found in nonzero],
        )

    writer.details(f"{name}: the {len(nonzero)} nonzero entries", body, open_=False)


#: A cut binding value up to this many characters is shown in full beneath
#: the premise; a longer one links the record.
IN_FULL_LIMIT: Final[int] = 5000


def _cut_in_full(binding: Binding, ctx: _Context) -> str | None:
    """Return a cut binding's full value where no record link can show it.

    "(387 characters; see the record)" without a link leaves the value
    unreadable; it is then written out in full, collapsed.
    """
    if binding.get("varies") or "value" not in binding:
        return None
    value = binding["value"]
    if binding_words(binding["name"], value) is not None:
        return None
    if ctx.outcomes and isinstance(value, list) and (
        [str(item) for item in value] == list(ctx.outcomes)
    ):
        return None
    if _same_as_table(value, ctx):
        return None
    words = _words(value, ctx.outcomes)
    if len(words) <= _LONG_VALUE:
        return None
    if _outcome_rows(binding, ctx) is not None:
        # Written as a table of its nonzero entries instead (_entry).
        return None
    # Report v2 last round, item 5: a record excerpt shows a large nested part
    # as "not shown", so a cut value up to IN_FULL_LIMIT characters is written
    # out here in full, collapsed, whether or not a record link exists.
    if len(words) <= IN_FULL_LIMIT:
        return words
    pointer = binding.get("pointer")
    linked = bool(pointer) and ctx.excerpt_link is not None and pointer in ctx.pointers
    return None if linked else words


def _long_probabilities(
    binding: Binding, ctx: _Context
) -> list[tuple[str, Fraction]] | None:
    """Return a cut probability map that no table on the page shows, or None."""
    if binding.get("varies") or "value" not in binding:
        return None
    value = binding["value"]
    if binding_words(binding["name"], value) is not None or _same_as_table(value, ctx):
        return None
    if len(_words(value, ctx.outcomes)) <= _LONG_VALUE:
        return None
    return _outcome_rows(binding, ctx)


def _in_full(writer: Writer, name: str, full: str, ctx: _Context) -> None:
    """Write a cut binding's value in full, collapsed."""
    def body() -> None:
        writer.paragraph(_linkify(full, ctx) or [full])

    writer.details(f"{name} in full", body, open_=False)


def _binding_name(name: str, ctx: _Context) -> str:
    """Return a binding's name, readable where the glossary has the key."""
    term = ctx.aliases.get(name)
    return name if term is None else f"{term.term} ({name})"


#: THE CLAIM STATUS LABELS: "Status:
#: verified" beside "The engine does not verify this assumption" read as a
#: check on hardware. The status is how far the claim's text has been
#: reviewed; the glossary entries "review status" and "effective status" say
#: so where the label first appears.
REVIEW_STATUS: Final[str] = "Review status of the claim"
REVIEW_STATUS_CLOSURE: Final[str] = "Review status with its dependencies"
#: A premise's one status row: the claim's status and, where it differs,
#: the lowest over everything it rests on (the stage-9 readers found two
#: rows that read the same on every premise).
REVIEW_STATUS_ROW: Final[str] = "Review status"


def _status_cell(status: str, effective: str) -> str:
    """Return a claim's review status and its status with its dependencies."""
    if status == effective:
        return f"{status}, also with everything it rests on"
    return f"{status}; with everything it rests on: {effective}"


def _entry(writer: Writer, entry: AssumptionEntry, ctx: _Context, level: int) -> None:
    """Write one premise: its summary table first, its text and bindings beneath.

    The table (what it is about, what is at stake, what a failure means, the
    claim's summary and status, the statement link and the reference fields)
    is what a reader scans; the premise's own text, an earlier wording, the
    role notes and what it binds on this run follow, folded in HTML
    (Markdown has no fold and writes them in order after the table).
    """
    owner = entry["owner"]
    module = _module_of(owner["id"])
    writer.heading(level, f"{entry['short_id']}: {owner['title']}", entry["short_id"])
    stake = "; ".join(entry["at_stake"]) or "not recorded"
    # Report v2 last round, item 3: the consequence tag, from ``affects``.
    effect = consequence_words(entry["short_id"], entry["affects"])
    rows: list[list[Rich]] = [
        [["About"], [entry["about"] or "not recorded"]],
        [["At stake"], [stake]],
        [["If it fails"], [effect]],
    ]
    if "points" in entry:
        rows.append([["Points"], [_points_label(entry["points"], ctx.all_points)]])
    rows.append([["Summary"], _rich_text(owner["summary"], ctx, module)])
    rows.append([[REVIEW_STATUS_ROW],
                 [_status_cell(owner["status"], owner["effective_status"])]])
    rows.append([["Statement"], [_claim_link(owner, ctx)]])
    rows.append([["Category"], _value(entry["category"])])
    if entry["refines"]:
        rows.append([["Refines"], [_target(entry["refines"], ctx)]])
    # The verification sentence the group's lead already says once is not
    # repeated on every premise; a premise whose sentence differs says it.
    if not (entry["verification"] == "never"
            and entry["verification_sentence"] == ctx.common_verification):
        rows.append([["Verification"], [entry["verification_sentence"]]])
    rows.append([["Machine key"], [Code(entry["machine_key"])]])
    rows.append([
        ["Emitted by"],
        _joined(Code(_emission_label(emission)) for emission in entry["emitted_by"]),
    ])
    writer.table(_header(["Field", "Value"], ctx), rows)

    frozen = entry["user_statement"] or owner["summary"]
    current = entry["current_text"]
    bindings = entry["bindings"]

    def body() -> None:
        writer.paragraph(_rich_text(frozen if current is None else current, ctx,
                                    module))
        if current is not None:
            writer.paragraph([
                "The run record carries an earlier wording of this premise "
                "(below); the current wording is the one above. Vouch for both; "
                "where they differ, the stricter one applies."
            ])
            writer.details(f"The earlier wording of {entry['short_id']}",
                           lambda: writer.paragraph(_rich_text(frozen, ctx, module)),
                           open_=False)
        # Run-specific lines beneath the statement.
        for note in entry.get("role_notes") or ():
            writer.paragraph(_rich_text(note, ctx, module))
        if not bindings:
            return
        writer.paragraph(["For this run:"])
        writer.bullets([
            [_binding_name(binding["name"], ctx), ": ", *_binding_value(binding, ctx)]
            for binding in bindings
        ])
        for binding in bindings:
            full = _cut_in_full(binding, ctx)
            if full is not None:
                _in_full(writer, _binding_name(binding["name"], ctx), full, ctx)
            probabilities = _long_probabilities(binding, ctx)
            if probabilities is not None:
                _probability_table(writer, _binding_name(binding["name"], ctx),
                                   probabilities, ctx)

    writer.details(
        f"{entry['short_id']} in full: its text"
        + (", the role notes" if entry.get("role_notes") else "")
        + (" and what it binds on this run" if bindings else ""),
        body, open_=False,
    )


def _emission_label(emission: Emission) -> str:
    """Return one emitter as ``module``, ``module@station0`` or ``module@partyA``."""
    label = emission["module"]
    if emission["station"] is not None:
        label += f"@station{emission['station']}"
    if emission.get("party") is not None:
        label += f"@party{emission['party']}"
    return label


def _not_engaged(writer: Writer, items: Sequence[NotEngaged], title: str,
                 ctx: _Context, level: int = 3) -> None:
    if not items:
        return
    writer.heading(level, title)
    discharged = any("discharged_by" in item for item in items)
    marked = any("points" in item for item in items)
    rows: list[list[Rich]] = []
    for item in items:
        row: list[Rich] = [
            [_target(item["short_id"], ctx)], [Code(item["module"])],
            _rich_text(item["reason"], ctx, item["module"]),
        ]
        if discharged:
            by = item.get("discharged_by")
            row.append([] if by is None else [Code(by)])
        if marked:
            row.append(
                [_points_label(item["points"], ctx.all_points)]
                if "points" in item else []
            )
        rows.append(row)
    header = ["Assumption", "Module", "Reason"]
    if discharged:
        header.append("Discharged by")
    if marked:
        header.append("Points")
    writer.table(header, rows)


#: The two groups of premises, by category.
_PREMISE_GROUPS: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    ("premises-devices", "Premises about your devices and setup", DEVICE_CATEGORIES),
    ("premises-engine", "Premises about artefacts and the engine", ENGINE_CATEGORIES),
)

#: Said once per group instead of under every premise of that kind.
UNVERIFIED: Final[str] = (
    "The engine does not verify these premises; a run that rests on one records "
    "it as unverified. Where a premise's own text says the engine checks a part "
    "of it (its inputs, say), that part is checked and the rest is yours; a "
    "premise whose verification differs says so under it."
)


def _families(
    groups: Sequence[CategoryGroup], extra: Sequence[AssumptionEntry]
) -> dict[str | None, list[tuple[AssumptionEntry, list[AssumptionEntry]]]]:
    """Return the families by category, the ``extra`` entries standing alone."""
    found: dict[str | None, list[tuple[AssumptionEntry, list[AssumptionEntry]]]] = {}
    for group in groups:
        found.setdefault(group["category"], []).extend(
            (family["head"], family["members"]) for family in group["families"]
        )
    for entry in extra:
        found.setdefault(entry["category"] or "numerical-trust", []).append((entry, []))
    return found


def _assumptions(
    writer: Writer, section: AssumptionsSection, ctx: _Context,
    empty_because: str | None = None,
    engine: Sequence[AssumptionEntry] = (),
    title: str = SECTION_TITLES["assumptions"],
) -> None:
    """Write the premises in two groups, by category and ``refines`` family.

    ``engine`` are the trusted engine numerics, which fold into the second
    group.
    """
    writer.heading(2, title, "assumptions")
    if empty_because is not None:
        writer.paragraph([empty_because])
    by_category = _families(section["groups"], engine)
    known = categories()
    # The short ids the page lists, which pick a category's intro: an older
    # record listing A-EVE-DIM keeps the attacker intro it was written with.
    listed = {
        entry["short_id"]
        for families in by_category.values()
        for head, members in families
        for entry in (head, *members)
    }
    for anchor, heading, names in _PREMISE_GROUPS:
        present: list[str | None] = [name for name in names if by_category.get(name)]
        if anchor == "premises-devices":
            # A category the table does not order, and none, stand with the
            # premises about the setup: they are not the engine's.
            present += [
                name for name in by_category
                if name not in DEVICE_CATEGORIES and name not in ENGINE_CATEGORIES
            ]
        if not present:
            continue
        writer.heading(3, heading, anchor)
        entries = [
            entry for name in present for head, members in by_category[name]
            for entry in (head, *members)
        ]
        sentences = [entry["verification_sentence"] for entry in entries
                     if entry["verification"] == "never"]
        ctx.common_verification = (
            max(set(sentences), key=sentences.count) if sentences else None
        )
        if sentences:
            writer.paragraph([UNVERIFIED])
        for name in present:
            category = None if name is None else known.get(name)
            writer.heading(
                4,
                category.heading if category is not None else (name or "Uncategorised"),
                f"category-{name or 'none'}",
            )
            if category is not None:
                writer.paragraph([category.intro_for(listed)])
            for head, members in by_category[name]:
                _entry(writer, head, ctx, 5)
                for member in members:
                    _entry(writer, member, ctx, 6)
    _declared_by_you(writer, section["user_declared"], ctx)
    if section["discrepancies"]:
        writer.heading(3, "Ledger and closure disagree")
        writer.table(
            ["Assumption", "Kind", "Emitted by", "Detail", "Points"],
            [
                [[_target(item["short_id"], ctx)], [Code(item["kind"])],
                 _value(item["emitted_by"], ctx), _value(item["detail"], ctx),
                 [_points_label(item["points"], ctx.all_points)]
                 if "points" in item else []]
                for item in section["discrepancies"]
            ],
        )


def _diagnostics(
    writer: Writer, section: NumericsSection, ctx: _Context, level: int
) -> None:
    """Write the solver diagnostics, one reading each, and its attempts."""
    rows = section["explained"]
    if rows:
        writer.heading(level, "Diagnostics", "diagnostics")
        writer.table(
            _header(["Diagnostic", "Value", "What it means"], ctx),
            [
                [[*_label(row["label"], ctx), " (", Code(row["name"]), ")"],
                 ["none"] if row["value"] == {} else _value(row["value"], ctx),
                 _text_or_dash(row["explanation"], ctx)]
                for row in rows
            ],
        )
    elif section["diagnostics"]:
        writer.heading(level, "Diagnostics", "diagnostics")
        writer.table(
            ["Diagnostic", "Value"],
            [[[Code(name)], _value(value, ctx)]
             for name, value in section["diagnostics"].items()],
        )
    if section["solve_stop"]:
        writer.paragraph(["How the search stopped, as a whole: ",
                          *_rich_text(section["solve_stop"], ctx)])
    attempts = section["solver_attempts"]
    if attempts:
        def table() -> None:
            writer.table(
                _header(["Attempt", "Method", "Steps", "Seconds",
                         "How it stopped", "Why it stopped", "Resumed",
                         "Bound after"], ctx),
                [
                    [[str(index)], [attempt["method"]], _value(attempt["iterations"]),
                     ["—" if attempt["seconds"] is None
                      else f"{attempt['seconds']:.3g}"],
                     [attempt["termination"]],
                     ["—" if attempt["stop_reason"] is None
                      else attempt["stop_reason"]],
                     ["—" if attempt["resumed"] is None
                      else "yes" if attempt["resumed"] else "no"],
                     ["—" if attempt["bound_after"] is None
                      else f"{attempt['bound_after']:.6g}"]]
                    for index, attempt in enumerate(attempts, start=1)
                ],
            )

        writer.details(f"How each of the {len(attempts)} solver attempts stopped",
                       table, open_=False)


#: The "alpha chosen by" row where the outer search found no alpha with a
#: positive key length (record 0.40.0).
NO_KEY_CHOSEN_BY: Final[str] = (
    "none: no alpha the outer search evaluated gives a key; the run shown is "
    "the evaluation with the largest estimate h_low"
)


def _bound_text(found: AlphaBound | None) -> str:
    """Return a bound the alpha search saw, with its alpha, or a dash."""
    if found is None:
        return "—"
    return f"{found['h_lb']:.6g} at alpha {found['alpha']:.6g}"


#: The labels of what chose a run's Renyi order (report 0.6.0).
_ALPHA_CHOSEN_BY: Final[Mapping[str, str]] = {
    "outer-search": "the outer alpha search",
    "configuration": "the configuration (alpha)",
    "declaration": "the declaration (parameters.alpha)",
}


def _alpha_rows(alpha: AlphaUsed) -> list[tuple[str, Any]]:
    """Return the result table's rows on the Renyi order and what chose it."""
    rows: list[tuple[str, Any]] = [
        ("Rényi order alpha", alpha["value"]),
        ("alpha chosen by",
         NO_KEY_CHOSEN_BY if alpha.get("no_positive_key")
         else _ALPHA_CHOSEN_BY.get(alpha["chosen_by"], alpha["chosen_by"])),
    ]
    if alpha["chosen_by"] == "outer-search":
        rows += [
            ("alpha searched over", alpha["searched_range"]),
            ("alpha search runs", alpha["runs"]),
        ]
    return rows


def _alpha_search(
    writer: Writer, search: AlphaSearchDetail, ctx: _Context, level: int = 3
) -> None:
    """Write the outer alpha search: its settings, then every run it made."""
    writer.heading(level, "Alpha search", "alpha-search")
    no_key = search.get("no_positive_key")
    if no_key is not None:
        writer.paragraph([
            "No positive key. ", no_key["reason"],
            " The run shown is the evaluation at alpha "
            f"{no_key['reported_alpha']:.6g}, the one with the largest estimate "
            "h_low; its key length is 0.",
        ])
    _pairs(writer, "Alpha search", [
        ("chosen alpha",
         search["chosen_alpha"] if no_key is None
         else "none: no alpha gives a positive key length"),
        *([] if no_key is None else [
            ("estimate reported (largest h_low)",
             "—" if no_key["h_low"] is None
             else f"{no_key['h_low']:.6g} at alpha {no_key['reported_alpha']:.6g}"),
            ("largest h_lb (diagnostic)", _bound_text(no_key["largest_h_lb"])),
            ("largest h_lb on the declaration the solver searched (diagnostic)",
             _bound_text(no_key["largest_h_lb_searched"])),
        ]),
        ("runs", len(search["evaluations"])),
        ("settings", search["settings"]),
        ("rule", search["rule"]),
        ("reads", search["reads"]),
        ("refinement stopped", search["refinement_stopped"] or "no: every step ran"),
        ("record", search["pointer"]),
    ], ctx)
    rows = search["evaluations"]

    def table() -> None:
        writer.table(
            ["alpha", "Phase", "Key length", "h_lb", "Score", "Reason",
             "Set aside", "Seconds"],
            [
                [_value(row["alpha"]), [row["phase"]], _value(row["key_length"]),
                 _value(row["h_lb"]), _value(row["score"]), _value(row["reason"]),
                 ["—" if row["set_aside"] is None else row["set_aside"]],
                 _value(row["seconds"])]
                for row in rows
            ],
        )

    writer.details(f"Every run of the search ({len(rows)})", table, open_=False)


def _outcome(check: Check) -> Rich:
    """Return a check's outcome; a sweep's ``varies`` lists each point's."""
    if check["outcome"] != "varies":
        return [check["outcome"]]
    outcomes = check.get("point_outcomes", [])
    return ["varies: ", "; ".join(
        f"{index}: {outcome}" for index, outcome in enumerate(outcomes)
    )]


def _check_rows(checks: Sequence[Check], ctx: _Context) -> list[list[Rich]]:
    return [
        [
            [Code(check["id"]), " ", check["title"]],
            _outcome(check),
            ["varies"] if check.get("value_varies") else _value(check["value"], ctx),
            _joined(_claim_link(claim, ctx) for claim in check["claims"]),
            _pointer(check["pointer"], ctx),
        ]
        for check in checks
    ]


_CHECK_HEADER: Final = ["Check", "Outcome", "Value", "Claims", "Record"]

#: The λ_EC row of the inputs (report 0.8.0).
_LAMBDA_EC_ROW: Final[str] = "parameters.lambda_ec"
_LAMBDA_EC_ANCHOR: Final[str] = "lambda-ec-origin"

#: The labels of a λ_EC side file's fields; another field shows under its key.
_LAMBDA_EC_FIELDS: Final[tuple[tuple[str, str], ...]] = (
    ("formula", "Formula"),
    ("f_ec", "f_EC, the error-correction inefficiency"),
    ("f_ec_source", "Source of f_EC"),
    ("conditional_entropy_bits_per_round",
     "Conditional entropy per round (bits) of the key given the other party's data"),
    ("rounds", "Rounds n"),
    ("key_holder", "Key holder"),
    ("p_pass", "p_pass, the honest probability that a round passes sifting"),
    ("lambda_ec", "λ_EC (bits)"),
)


def _meaning(row: InputRow, ctx: _Context, lambda_ec: LambdaEcOrigin | None) -> Rich:
    rich = [] if row["meaning"] is None else _rich_text(row["meaning"], ctx)
    if row["name"] != _LAMBDA_EC_ROW:
        return rich or ["—"]
    tail: Rich = (
        [" How λ_EC was chosen: estimated from the honest model (",
         Link("how", f"#{_LAMBDA_EC_ANCHOR}"), ")."]
        if lambda_ec is not None
        else [" How λ_EC was chosen: declared by you (no estimate sits beside "
              "the record)."]
    )
    return [*rich, *tail]


#: The budgets table's title: the configuration's word with what it means.
BUDGETS_TITLE: Final[str] = "Budgets (the ε you choose)"

#: The three inputs tables.
_INPUT_TABLES: Final[tuple[tuple[str, str, str], ...]] = (
    ("device", "Device and channel", "inputs-device"),
    ("budget", BUDGETS_TITLE, "inputs-budget"),
    ("engine", "Engine settings", "inputs-engine"),
)


#: WHAT A BUDGET IS, where the budgets table stands. WHY: "budget" (the
#: claims' word and the configuration's, ``completeness_budget``) must be
#: recognised as an ε: each is an error probability chosen before the run,
#: three of them make up the security parameter ε, and the completeness
#: budget is not part of it.
BUDGET_LEAD: Final[str] = (
    "A budget is an error probability (an ε) you choose before the run. ε_PA, "
    "ε_EV and ε_auth make up the security parameter ε = ε_PA + ε_EV + 2ε_auth. "
    "The completeness budget ε_comp is not part of ε: it bounds only how often "
    "an honest run fails the acceptance test. The table also holds the round "
    "count and the other inputs of the key length."
)


#: WHAT A-EXACT ASKS OF EVERY DECLARED COMPONENT VALUE, where the device
#: table stands on a run that engages it: the Premises column names A-EXACT
#: only beside the values the record ties to a receiver, so the lead says
#: what it asks of each (receiver/ass:exact's user_statement).
EXACT_LEAD: Final[str] = (
    "[[A-EXACT]] asks you to vouch that every number you declared for a "
    "receiver component (each efficiency, dark-count probability, probe mean "
    "photon number and other component parameter) is the device's true value, "
    "not an estimate with an error bar. It applies to every such value, "
    "whether or not the Premises column names it there: the column names it "
    "only beside the values the report could tie to a receiver."
)


_FRACTION: Final = re.compile(r"^-?\d+/\d+$")


def with_decimal(value: Any) -> str:
    """Return a value as text, decimal first.

    An exact ``p/q`` reads as its decimal, with the fraction beside it where
    the decimal is not exact: ``4/5`` is ``0.8``, ``205/2048`` is
    ``0.100098 (205/2048)``. A small float that is a power of two, as a
    budget of ``2^-30`` is, reads ``9.31e-10 (2^-30)``: the power is exact.
    """
    text = format_value(value)
    if isinstance(value, str) and _FRACTION.match(value.strip()):
        try:
            found = Fraction(value)
        except (ValueError, ZeroDivisionError):
            return text
        if found.denominator > 1:
            decimal = f"{float(found):.6g}"
            return decimal if Fraction(decimal) == found else f"{decimal} ({text})"
    if isinstance(value, float) and 0 < value < 1e-3:
        mantissa, exponent = math.frexp(value)
        if mantissa == 0.5:
            return f"{value:.3g} (2^{exponent - 1})"
    return text


def _per_port(value: Any) -> str:
    """Return a value in words; a per-port mapping as ``v (each of H, V)``."""
    if isinstance(value, Mapping) and value:
        values = {with_decimal(item) for item in value.values()}
        if len(values) == 1:
            return f"{values.pop()} (each of {', '.join(map(str, value))})"
        return ", ".join(f"{key} = {with_decimal(item)}" for key, item in value.items())
    return with_decimal(value)


def _input_value(row: InputRow) -> Rich:
    """Return an input's value, its default where it differs, and if unused."""
    if row["name"] == "parameters.alpha" and row["not_used"]:
        return [row["not_used"]]
    text = _per_port(row["value"])
    prepared = row["prepared"]
    if prepared is not None and not same_number(prepared, row["value"]):
        text = (f"{with_decimal(prepared)}, prepared from the requested "
                f"{_per_port(row['value'])} and analysed")
        # How far the preparation moved it, exactly where both are numbers:
        # a move onto the 2^-40 lattice shows the same six digits on both
        # sides, and the move is what tells them apart.
        try:
            moved = abs(Fraction(str(prepared)) - Fraction(str(row["value"])))
        except (ValueError, ZeroDivisionError):
            moved = None
        if moved:
            text += f" (moved by {float(moved):.3g})"
    if row["is_default"] is False and row["default"] is not None:
        text += f"; default {_per_port(row['default'])}"
    if row["not_used"]:
        # A check that was asked for and did not run reads "on (not run: why)".
        text += (f" ({row['not_used']})" if row["not_used"].startswith("not run:")
                 else f"; {row['not_used']}")
    return [text]


def _inputs(
    writer: Writer, rows: Sequence[InputRow], ctx: _Context,
    lambda_ec: LambdaEcOrigin | None = None, level: int = 3,
) -> None:
    """Write the inputs in three tables; the record pointer links the name."""
    for group, title, anchor in _INPUT_TABLES:
        found = [row for row in rows if row["group"] == group]
        if not found:
            continue
        writer.heading(level, title, anchor)
        if group == "budget":
            writer.paragraph([BUDGET_LEAD])
        if group == "device" and "A-EXACT" in ctx.present:
            writer.paragraph(_rich_text(EXACT_LEAD, ctx))
        writer.table(
            _header(["Input", "Value", "Unit", "Meaning", "Premises"], ctx),
            [
                [
                    # An input whose name makes no readable label shows the
                    # name alone, verbatim in code (m9).
                    [Anchor(f"input-{row['name']}"), row["label"], " (",
                     *_name_link(row, ctx), ")"] if row["label"]
                    else [Anchor(f"input-{row['name']}"), *_name_link(row, ctx)],
                    _input_value(row),
                    _value(row["unit"]),
                    _meaning(row, ctx, lambda_ec),
                    _joined(Link(sid, f"#{sid}") for sid in dict.fromkeys(
                        [*row["bound_by"], *row.get("covered_by", ())]))
                    or ["—"],
                ]
                for row in found
            ],
        )
    if lambda_ec is not None and any(row["name"] == _LAMBDA_EC_ROW for row in rows):
        _lambda_ec_origin(writer, rows, lambda_ec, ctx, level + 1)


def _name_link(row: InputRow, ctx: _Context) -> Rich:
    """Return an input's configuration name, linked to its record excerpt."""
    pointer = row["pointer"]
    if ctx.excerpt_link is not None and pointer in ctx.pointers:
        return [Link(row["name"], ctx.excerpt_link(pointer), code=True)]
    return [Code(row["name"])]


def _lambda_ec_origin(
    writer: Writer, rows: Sequence[InputRow], origin: LambdaEcOrigin, ctx: _Context,
    level: int = 4,
) -> None:
    """Write how λ_EC was estimated, from the side file beside the record."""
    writer.heading(level, "How λ_EC was chosen", _LAMBDA_EC_ANCHOR)
    writer.paragraph([
        "The run's λ_EC was estimated before the run from the honest model, and "
        "the estimate was written beside the record "
        "(<record stem>.lambda-ec.json). It is not part of the record."
    ])
    known = dict(_LAMBDA_EC_FIELDS)
    pairs = [(known[key], origin[key]) for key, _ in _LAMBDA_EC_FIELDS if key in origin]
    pairs += [(str(key), value) for key, value in origin.items() if key not in known]
    # f_EC links its definition in the glossary.
    writer.table(["Estimate", "Value"], [
        [[Link("f_EC", f"#{term_anchor('f_EC')}"), name.removeprefix("f_EC")]
         if name.startswith("f_EC,") else _label(name, ctx),
         _value(value, ctx)]
        for name, value in pairs
    ])
    declared = next(row["value"] for row in rows if row["name"] == _LAMBDA_EC_ROW)
    if "lambda_ec" in origin and origin["lambda_ec"] != declared:
        writer.notice("λ_EC differs", [[
            f"The estimate beside the record gives λ_EC = "
            f"{format_value(origin['lambda_ec'])}, the record declares "
            f"{format_value(declared)}: the side file is not this run's."
        ]])


def _snap_flags(block: Mapping[str, Any]) -> str:
    flags = [
        *(["rests on A-SNAP"] if block.get("rests_on_assumption") else []),
        *(["evaluated off its snap"] if block.get("evaluated_off_snap") else []),
        *(["support_not_preserved"] if block.get("support_not_preserved") else []),
    ]
    return ", ".join(flags)


def _text_or_dash(text: str | None, ctx: _Context) -> Rich:
    return ["—"] if text is None else _rich_text(text, ctx)


def _measurement_snaps(
    writer: Writer, snaps: MeasurementSnaps, ctx: _Context, level: int | None = 3
) -> None:
    """Write the measurement snaps in detail (report 0.4.0; runs/report/snaps.py).

    Since 0.10.0 a run report shows the reader's layer (``plain``, ``rows``) in
    the page and this detail in its appendix, without a heading of its own
    (``level`` ``None``).
    """
    if level is not None:
        writer.heading(level, SECTION_TITLES["snaps"], "measurement-snaps")
    if snaps["warnings"] and level is not None:
        writer.notice("Warning", [_rich_text(warning, ctx)
                                  for warning in snaps["warnings"]])
    writer.bullets([_rich_text(sentence, ctx) for sentence in snaps["sentences"]])
    if snaps["assumption"] is not None:
        writer.paragraph(
            ["Assumption this rests on: ", _target(snaps["assumption"], ctx)]
        )
    if snaps["blocks"]:
        writer.table(
            _header(["Block", "Setting", "Station", "Status", "Snapped from",
                     "Reference handed", "Largest radius", "Input radius",
                     "Group", "What to change", "Cause (detail)", "Fix (detail)",
                     "Flags", "Record"], ctx),
            [
                [
                    [Code(block["block"])],
                    _value(block["setting"]),
                    _value(block["station"]),
                    [block["status"]],
                    [block["reference_kind"]],
                    _value(block["handed_kind"]),
                    _value(block["handed_radius"]),
                    _value(block["input_radius"]),
                    _value(block["group"]),
                    _text_or_dash(block["group_fix"], ctx),
                    _text_or_dash(block["cause"], ctx),
                    _text_or_dash(block["fix"], ctx),
                    [_snap_flags(block)],
                    _pointer(block["pointer"], ctx),
                ]
                for block in snaps["blocks"]
            ],
        )
    if snaps["emission"]:
        writer.table(
            ["Data sector", "Station", "Moved classes", "Evaluated off its snap",
             "Group", "Record"],
            [
                [
                    _value(row["data_sector"]),
                    _value(row["station"]),
                    _value(row["moved_classes"], ctx),
                    _value(row["evaluated_off_snap"]),
                    _value(row["group"]),
                    _pointer(row["pointer"], ctx),
                ]
                for row in snaps["emission"]
            ],
        )
    writer.table(_header(["Run setting", "Value"], ctx), [
        [_label(name, ctx), _value(value, ctx)]
        for name, value in snaps["settings"].items()
    ])


def _pairs(
    writer: Writer, header: str, pairs: Iterable[tuple[str, Any]],
    ctx: _Context | None = None,
) -> None:
    # An empty text (a custom document's readme) reads "none", not a blank
    # cell that looks like a value lost in rendering (n5).
    writer.table([header, "Value"],
                 [[_label(name, ctx), ["none"] if value == "" else _value(value, ctx)]
                  for name, value in pairs])
