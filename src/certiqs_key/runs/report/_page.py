"""The run report's page: three layers, walked once for both writers (0.9.0).

WHY THIS EXISTS. A report answerable only by assembling it -- engine
internals before the key length, no plain meaning of ε, no layout, dozens of
inputs in one table -- cannot be read. The page is ordered in three layers:

1. the summary: the box at a glance (terse fragments) and the key rate
   considerations beneath it, the result in words with what consumes key,
   the setup in brief, what the guarantee means (the claims' own plain
   readings), what you vouch for, what is not counted, the choices that could
   lengthen the key;
2. the detail a reader needs: the setup (what a round is, the protocol, the
   stations with their POVMs folded in HTML), the inputs in three tables,
   then the assumptions grouped by what they are about, each premise's table
   first and its text folded in HTML;
3. the appendix, collapsed in HTML: how the number was computed, the
   measurement snaps, every security claim, the checks, the route,
   provenance, the glossary.

Like :mod:`certiqs_key.runs.report._render`, whose primitives it uses, this
module authors headings, labels and the few leads that say why a part is
shown (the operator tables, the premises on what a round is); its other
sentences are the report object's (:mod:`certiqs_key.runs.report.explain`
builds the summary's) or the claims' own. The glossary prints the terms that
occur on the page: a tracking writer records the page's text as it is written.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from fractions import Fraction
from typing import Any, Final

from certiqs_key.runs.report._render import (
    _CHECK_HEADER,
    RESIDUE_NOTE,
    REVIEW_STATUS,
    REVIEW_STATUS_CLOSURE,
    SECTION_TITLES,
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
    _alpha_rows,
    _alpha_search,
    _assumptions,
    _check_rows,
    _claim_link,
    _claim_list,
    _Context,
    _diagnostics,
    _entry,
    _flags,
    _header,
    _inputs,
    _joined,
    _label,
    _measurement_snaps,
    _module_of,
    _not_engaged,
    _pairs,
    _pointer,
    _rich_text,
    _target,
    _user_declared,
    _value,
    format_entry,
    is_residue,
    parameter_anchor,
    report_pointers,
    residue_floor,
    with_decimal,
)
from certiqs_key.runs.report.build import (
    REFUSED_DECLARED_BELOW,
    REFUSED_NOT_LISTED,
    SWEEP_ALL_REFUSED,
)
from certiqs_key.runs.report.explain import (
    AT_A_GLANCE_TITLE,
    CERTIFIED_CLAIM,
    COSTS_LEAD,
    FIRSTORDER_CLAIM,
    KEYLENGTH_CLAIM,
    LEVERS_LEAD,
    LEVERS_SNAP,
    ROLES_ABSENT_LEAD,
    STATUS_LEGEND,
    consequence_rows,
    draft_sentence,
    epsilon_text,
    refused_numbers,
)
from certiqs_key.runs.report.explain import statement_status as explain_statement_status
from certiqs_key.runs.report.glossary import Term, terms
from certiqs_key.runs.report.inputs import input_label, upper_decimal
from certiqs_key.runs.report.model import (
    ClaimRef,
    Guarantee,
    InputRow,
    KeyRateReport,
    MeasurementSnaps,
    OperatorBlock,
    OperatorFamily,
    RoundBlock,
    SetupAcceptance,
    SetupSection,
    SetupStation,
    Summary,
    SweepPoint,
    SweepReport,
    group_entries,
)

__all__ = ["write_report", "write_sweep"]

#: The summary's subsections, in order.
_SUMMARY_PARTS: Final[tuple[tuple[str, str], ...]] = (
    ("considerations", "Key rate considerations"),
    ("result", "The result"),
    ("setup-brief", "Your setup in brief"),
    ("guarantee", "What the guarantee means"),
    ("roles", "Roles on this run"),
    ("vouch", "What you vouch for"),
    ("not-counted", "Not counted"),
    ("levers", "Choices that could lengthen the key"),
)

#: The appendix's subsections, in order.
_APPENDIX_PARTS: Final[tuple[tuple[str, str], ...]] = (
    ("how-computed", "How the number was computed"),
    ("measurement-snaps", "Measurement snaps"),
    ("snaps-detail", "Measurement snaps in detail"),
    ("security-claims", "Security claims"),
    ("checks", "Checks the engine ran"),
    ("not-engaged", "Not engaged on this route"),
    ("route", "Route, instance and preparation"),
    ("provenance", "Provenance"),
    ("glossary", "Glossary"),
)


# --------------------------------------------------------------------------
# A writer that remembers what the page says (for the glossary)
# --------------------------------------------------------------------------


def _plain(rich: Rich) -> str:
    parts: list[str] = []
    for segment in rich:
        if isinstance(segment, Link):
            parts.append(segment.label)
        elif isinstance(segment, Code | Strong):
            parts.append(segment.text)
        elif isinstance(segment, str):
            parts.append(segment)
    return "".join(parts)


def _cell_text(cell: str | Rich) -> str:
    return cell if isinstance(cell, str) else _plain(cell)


class _Tracker(Writer):
    """Forward every call to ``inner`` and keep the page's plain text."""

    def __init__(self, inner: Writer) -> None:
        self.inner = inner
        self.seen: list[str] = []
        self.links_terms = inner.links_terms  # type: ignore[misc]

    def heading(self, level: int, text: str, anchor: str | None = None) -> None:
        self.seen.append(text)
        self.inner.heading(level, text, anchor)

    def paragraph(self, rich: Rich) -> None:
        self.seen.append(_plain(rich))
        self.inner.paragraph(rich)

    def bullets(self, items: Sequence[Rich]) -> None:
        self.seen.extend(_plain(item) for item in items)
        self.inner.bullets(items)

    def numbered(self, items: Sequence[Rich]) -> None:
        self.seen.extend(_plain(item) for item in items)
        self.inner.numbered(items)

    def table(
        self, header: Sequence[str | Rich], rows: Sequence[Sequence[Rich]]
    ) -> None:
        self.seen.extend(_cell_text(cell) for cell in header)
        self.seen.extend(_plain(cell) for row in rows for cell in row)
        self.inner.table(header, rows)

    def matrix(
        self,
        caption: str,
        rows: Sequence[str],
        columns: Sequence[str],
        cells: Sequence[Sequence[str]],
    ) -> None:
        self.seen.extend([caption, *rows, *columns])
        self.inner.matrix(caption, rows, columns, cells)

    def notice(self, title: str, items: Sequence[Rich]) -> None:
        self.seen.append(title)
        self.seen.extend(_plain(item) for item in items)
        self.inner.notice(title, items)

    def details(self, summary: str, body: Callable[[], None], *, open_: bool) -> None:
        self.seen.append(summary)
        self.inner.details(summary, body, open_=open_)

    def text(self) -> str:
        return self.inner.text()


def _occurs(term: Term, text: str) -> bool:
    return any(
        re.search(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", text)
        for alias in term.aliases
    )


# --------------------------------------------------------------------------
# Small pieces
# --------------------------------------------------------------------------


def _claims_tail(claims: Sequence[str], ctx: _Context) -> Rich:
    found = [ctx.index["claims"][claim] for claim in claims
             if claim in ctx.index["claims"]]
    if not found:
        return []
    return [" Statement: ", *_joined(_claim_link(claim, ctx) for claim in found), "."]


def _record_tail(pointer: str | None, ctx: _Context) -> Rich:
    return [] if not pointer else [" Record: ", *_pointer(pointer, ctx), "."]


def _reading(claim_id: str | None, ctx: _Context) -> Rich:
    """Return a claim's plain reading (its user_statement or summary) and link."""
    if claim_id is None or claim_id not in ctx.index["claims"]:
        return []
    claim = ctx.index["claims"][claim_id]
    text = claim["user_statement"] or claim["summary"]
    return [*_rich_text(text, ctx, _module_of(claim_id)), " Statement: ",
            _claim_link(claim, ctx), "."]


def _appendix_part(
    writer: Writer, key: str, body: Callable[[], None]
) -> None:
    """Write one appendix subsection: its heading, its body collapsed (HTML)."""
    title = dict(_APPENDIX_PARTS)[key]
    writer.heading(3, title, key)
    writer.details(title, body, open_=key == "glossary")


# --------------------------------------------------------------------------
# Layer 1: the summary
# --------------------------------------------------------------------------


def _toc(writer: Writer, report: KeyRateReport) -> None:
    def parts(items: Sequence[tuple[str, str]]) -> Rich:
        return _joined((Link(title, f"#{anchor}") for anchor, title in items), " · ")

    has_snaps = report["sections"]["protocol"]["measurement_snaps"] is not None
    writer.heading(2, "Contents", "contents")
    summary = report["sections"]["summary"]
    summary_parts = [
        part for part in _SUMMARY_PARTS
        if (part[0] != "roles" or summary["roles"])
        and (part[0] != "considerations" or summary["considerations"])
    ]
    items: list[Rich] = [
        [Link(SECTION_TITLES["summary"], "#summary"), ": ", *parts(summary_parts)],
        [Link(SECTION_TITLES["setup"], "#setup")],
        [Link(SECTION_TITLES["inputs"], "#inputs")],
        [Link(SECTION_TITLES["assumptions"], "#assumptions")],
    ]
    absent = {
        *(() if has_snaps else ("measurement-snaps", "snaps-detail")),
        *(() if report["sections"]["assumptions"]["not_engaged"]
          else ("not-engaged",)),
    }
    items.append([Link(SECTION_TITLES["appendix"], "#appendix"), ": ",
                  *parts([part for part in _APPENDIX_PARTS if part[0] not in absent])])
    writer.bullets(items)


#: The tag of a line of What you vouch for, by its consequence (report v2 last
#: round, item 3).
_CONSEQUENCE_TAG: Final[Mapping[str, str]] = {
    "security": "security",
    # One tag for every premise whose affects name completeness alone, whose
    # consequences differ in detail.
    "completeness": "completeness only",
}


def _tagged(short_ids: Sequence[str], tags: Sequence[str]) -> Rich:
    """Return linked premise ids, each with its consequence tag."""
    rich: Rich = []
    for position, short_id in enumerate(short_ids):
        if position:
            rich.append(", ")
        rich.append(Link(short_id, f"#{short_id}"))
        if position < len(tags):
            rich.append(f" ({_CONSEQUENCE_TAG.get(tags[position], tags[position])})")
    return rich


#: The guarantee's qualification on a first-order run:
#: the premise list does not cover the floating-point h_lb.
FIRST_ORDER_GAP: Final[str] = (
    "On this run it also needs the computed lower bound on the attacker's "
    "worst-case uncertainty per round (h_lb) to lie below that worst case "
    "(h_low), which no premise covers: the bound's proof is exact, and its "
    "objective and gradient are computed in floating point with no bound on "
    "their numerical error ([[meat-core/frank-wolfe/thm:firstorder]])."
)


#: Whether the guarantee's clause on a first-order run's computed h_lb
#: applies, by the run's reported tier: the claim's reading states it for
#: every run, and a reader of a certified run could not tell (the stage-9
#: experimentalist reader).
TIER_CLAUSE: Final[Mapping[str, str]] = {
    "certified": (
        "This run's key length is certified (h_cert, every arithmetic step exact "
        "or rigorously enclosed), so the clause on a first-order run's computed "
        "h_lb does not apply to it."
    ),
    "first-order": (
        "This run's key length is first-order, so that clause applies: its "
        "computed h_lb is not proved to lie below h_low."
    ),
}


#: Where the composable criterion takes its authenticated channel from:
#: A-AUTH, whose user_statement (meat-core/ass:auth) says that no composable
#: proof for this timing-aware channel is published yet.
COMPOSABLE_AUTH: Final[str] = (
    "The composable statement takes its authenticated classical channel from "
    "[[A-AUTH]], whose own text says that no composable proof for this "
    "timing-aware channel is published yet; Wegman-Carter authentication with "
    "separate keys per direction approximates it."
)


def _completeness_tail(star: str) -> Rich:
    """Return ε* of the run in a decimal rounded up, the exact value one link away."""
    shown = upper_decimal(star)
    if shown is None:
        return [f" On this run ε* = {star}."]
    decimal, exact = shown
    return [
        " On this run an honest run fails the acceptance test with probability "
        f"at most {decimal} (ε*" + ("" if exact else ", rounded up") + "; ",
        Link("its exact value", "#setup-acceptance"), ").",
    ]


def _epsilon(value: float | None) -> str:
    """Return an ε, a power of two also as ``2^-k``."""
    return epsilon_text(value)


#: Where a summary line's "See ..." points, by anchor.
_SEE_TITLES: Final[Mapping[str, str]] = {
    "result": "The result",
    "guarantee": "What the guarantee means",
    "inputs": "Your inputs",
    "setup": "Your QKD setup",
    "not-counted": "Not counted",
    "setup-acceptance": "Acceptance test",
    "vouch": "What you vouch for",
    "measurement-snaps": "Measurement snaps",
    "how-computed": "How the number was computed",
    "levers": "Choices that could lengthen the key",
    "diagnostics": "Diagnostics",
}


def _see(anchor: str | None) -> Rich:
    """Return " See <part>." for a summary line that names its details."""
    if anchor is None:
        return []
    return [" See ", Link(_SEE_TITLES.get(anchor, "details"), f"#{anchor}"), "."]


def _glance_link(anchor: str | None) -> Rich:
    """Return " (<part>)" linking an at-a-glance fragment to its section."""
    if anchor is None:
        return []
    return [" (", Link(_SEE_TITLES.get(anchor, "details"), f"#{anchor}"), ")"]


def _link_first(rich: Rich, word: str, href: str) -> Rich:
    """Return ``rich`` with the first whole ``word`` in its text made a link.

    The status legend is linked where "draft" first appears.
    """
    pattern = re.compile(rf"\b{re.escape(word)}\b")
    out: Rich = []
    done = False
    for segment in rich:
        if done or not isinstance(segment, str):
            out.append(segment)
            continue
        found = pattern.search(segment)
        if found is None:
            out.append(segment)
            continue
        out += [segment[:found.start()], Link(word, href), segment[found.end():]]
        done = True
    return [segment for segment in out if segment != ""]


def _numerics_link(ctx: _Context) -> Link:
    """Return where the first-order floating-point gap is explained on this page.

    "The engine's numerics" where the page renders a numerical-trust premise;
    otherwise Not counted, whose first-order line names the gap: a run whose
    receiver weights are all enclosed engages no such premise
    (``receiver/req:eig-ledger-row``).
    """
    if ctx.numerics:
        return Link("The engine's numerics", "#category-numerical-trust")
    return Link("Not counted", "#not-counted")


def _guarantee(
    writer: Writer, guarantee: Guarantee | None, ctx: _Context, *, sweep: bool,
    first_order: bool = False, formed: Sequence[ClaimRef] = (),
    route: Sequence[ClaimRef] = (), route_accepted: bool = False,
    tier: str | None = None,
) -> None:
    """Write what the guarantee means: the claims' readings and the ε table.

    On a sweep the claims are the points' common ones and each point's ε is
    its own, so the table is left to the points.
    """
    if guarantee is None:
        writer.paragraph([
            "No point output a key, so no security guarantee applies."
            if sweep else
            "This run output no key, so no security guarantee applies to it."
        ])
        return
    # The statement's own reading (quoted verbatim) leads; then its numbers
    # on this run, completeness with this run's figure first, one execution,
    # and the review status last, as a list.
    writer.paragraph(_reading(guarantee["claim"], ctx)
                     or ["The closure table carries no reading of the "
                         "security statement."])
    claim = ctx.index["claims"].get(guarantee["claim"] or "")
    reading = "" if claim is None else claim["user_statement"] or ""
    # The reading of cor:composed-security names the gap itself; an older
    # table's reading gets it from here.
    if first_order and "h_lb" not in reading:
        writer.paragraph([*_rich_text(FIRST_ORDER_GAP, ctx), " (",
                          _numerics_link(ctx), ")"])
    elif "h_lb" in reading and tier is not None and tier in TIER_CLAUSE:
        # The reading names the first-order clause for every run; this run's
        # tier says whether it applies here (the stage-9 readers).
        writer.paragraph(_rich_text(TIER_CLAUSE[tier], ctx))
    if "composable" in reading:
        # The reading calls the criterion composable; the authenticated
        # channel it takes from A-AUTH has no published composable proof
        # (A-AUTH's own text), which a reader of the reading alone missed.
        writer.paragraph(_rich_text(COMPOSABLE_AUTH, ctx))
    if sweep:
        writer.paragraph([
            "It holds for each point that output a key, separately, with that "
            "point's own ε (", Link("the points", "#points-summary"), ")."
        ])
    else:
        writer.table(
            _header(["Parameter", "Value on this run", "What it bounds"], ctx),
            [
                [_label(term["symbol"], ctx),
                 [_epsilon(term["value"])],
                 [term["meaning"]]]
                for term in guarantee["terms"]
            ],
        )
    if guarantee["completeness"] is not None:
        star = guarantee["eps_star"]
        writer.paragraph([
            "Completeness.",
            *([" "] if star is None or sweep else [*_completeness_tail(star), " "]),
            *_reading(guarantee["completeness"], ctx),
        ])
    if guarantee["per_execution"] is not None:
        writer.paragraph(["One execution. ",
                          *_reading(guarantee["per_execution"], ctx)])
    # Report v2 last round, item 6: the statement's own review status.
    stated = explain_statement_status(
        [found for found in (ctx.index["claims"].get(claim_id) for claim_id in
                             (guarantee["claim"] or "", KEYLENGTH_CLAIM))
         if found is not None],
        formed,
        route,
        guarantee.get("outside"),
        sweep=sweep,
        route_accepted=route_accepted,
    )
    if stated is not None:
        writer.paragraph(_link_first(_rich_text(stated.lead, ctx), "Review status",
                                     "#status-legend"))
        writer.bullets([_rich_text(item, ctx) for item in stated.items])
        writer.paragraph(_rich_text(stated.tail, ctx))


def _summary(
    writer: Writer, report: KeyRateReport, ctx: _Context,
    lambda_ec: LambdaEcOrigin | None,
) -> None:
    summary: Summary = report["sections"]["summary"]
    titles = dict(_SUMMARY_PARTS)
    writer.heading(2, SECTION_TITLES["summary"], "summary")
    if summary["at_a_glance"]:
        writer.notice(AT_A_GLANCE_TITLE, [
            [Strong(item["lead"]), *_rich_text(item["text"], ctx),
             *_glance_link(item["anchor"])]
            for item in summary["at_a_glance"]
        ])
    if summary["considerations"]:
        # Each nuance of the number in one line, still on the first screen.
        writer.heading(3, titles["considerations"], "considerations")
        writer.bullets([
            _link_first([*_rich_text(item["text"], ctx), *_see(item["anchor"])],
                        "draft", "#status-legend")
            for item in summary["considerations"]
        ])

    writer.heading(3, titles["result"], "result")
    writer.paragraph(_rich_text(summary["result"], ctx))
    deductions = report["sections"]["result"]["deductions"]
    if summary["costs"]:
        writer.paragraph(_rich_text(COSTS_LEAD, ctx))
        writer.bullets([_rich_text(line, ctx) for line in summary["costs"]])
        pointer = None if deductions is None else deductions["pointer"]
        if pointer:
            writer.paragraph(["Record: ", *_pointer(pointer, ctx), "."])

    # The setup beside the number it was computed for, before what the
    # guarantee means.
    writer.heading(3, titles["setup-brief"], "setup-brief")
    writer.bullets([_rich_text(line, ctx) for line in summary["setup_brief"]])
    writer.paragraph(["The details: ", Link(SECTION_TITLES["setup"], "#setup"), "."])

    writer.heading(3, titles["guarantee"], "guarantee")
    _guarantee(writer, summary["guarantee"], ctx, sweep=False,
               first_order=report["sections"]["result"]["reported_tier"]
               == "first-order",
               formed=report["sections"]["result"]["statement_claims"],
               route=report["sections"]["result"]["route_claims_below_accepted"],
               route_accepted=report["sections"]["result"].get(
                   "route_claims_accepted", False),
               tier=report["sections"]["result"]["reported_tier"])

    if summary["roles"]:
        # Each party's role on this
        # run, read off the record (runs/roles.py), before the premises.
        writer.heading(3, titles["roles"], "roles")
        writer.bullets([_rich_text(line, ctx) for line in summary["roles"]])
        if summary["roles_absent"]:
            writer.paragraph([ROLES_ABSENT_LEAD])
            writer.bullets([_rich_text(line, ctx) for line in summary["roles_absent"]])

    writer.heading(3, titles["vouch"], "vouch")
    if summary["vouch"]:
        intro: Rich = [
            "The key length rests on the premises below, and the engine cannot "
            "check them. Each links to its statement and to what it means for "
            "this run.",
        ]
        if report["sections"]["result"]["reported_tier"] == "first-order":
            intro += [
                " None of them covers the floating-point arithmetic of the "
                "first-order bound (see ", _numerics_link(ctx), ").",
            ]
        writer.paragraph(intro)
        # The premises by consequence, as a table; each line below carries
        # its tag.
        writer.table(_header(["Premises of this run", "Count"], ctx),
                     [[[label], [count]]
                      for label, count in consequence_rows(summary["consequences"])])
    for group in summary["vouch"]:
        count = sum(1 + len(line["refinements"]) for line in group["entries"])
        writer.paragraph([f"{group['about']} ({count}):"])
        # Each premise by its existing one-liner, linked to its full text.
        writer.bullets([
            [Link(line["short_id"], f"#{line['short_id']}"), ": ",
             *_rich_text(line["summary"] or line["title"], ctx),
             " \u2014 ", _CONSEQUENCE_TAG.get(line["consequence"], line["consequence"]),
             *([] if not line["refinements"] else [
                 f"; {len(line['refinements'])} "
                 + ("refinement: " if len(line["refinements"]) == 1
                    else "refinements: "),
                 *_tagged(line["refinements"],
                          line.get("refinement_consequences") or []),
             ])]
            for line in group["entries"]
        ])
    if summary["where"]:
        # The certification lab's per-station checklist; the table also holds the
        # artefact and numerics premises named below it.
        writer.paragraph(["Where each premise applies (every premise of this "
                          "run, by the laboratory or station it applies at):"])
        writer.table(
            _header(["Where", "Premises"], ctx),
            [[[row["place"]],
              _joined(Link(short_id, f"#{short_id}") for short_id in row["premises"])]
             for row in summary["where"]],
        )
    _user_declared(writer, report["sections"]["result"]["user_declared"], ctx)
    draft = draft_sentence(summary["drafts"])
    if draft is not None:
        writer.paragraph(_link_first(_rich_text(draft, ctx), "draft",
                                     "#status-legend"))
    stale = summary["stale"]
    if stale:
        writer.paragraph([
            (f"{len(stale)} premise texts of this run differ" if len(stale) > 1
             else "1 premise text of this run differs")
            + " from the current contracts because the run was made by an older "
            "engine: ",
            *_joined(Link(short_id, f"#{short_id}") for short_id in stale),
            ". Each premise shows the current text with the earlier one beneath "
            "it, and its one-liner and what is at stake follow the current "
            "contract or the stricter of the two. Vouch for both texts; where "
            "they differ, the stricter one applies. A run with the current engine "
            "records the current texts.",
        ])

    writer.heading(3, titles["not-counted"], "not-counted")
    if summary["not_counted"]:
        lines: list[Rich] = []
        for item in summary["not_counted"]:
            line = _rich_text(item["text"], ctx)
            # The part that says the rest, by its heading.
            line += _see(item["anchor"])
            lines.append(line)
        writer.bullets(lines)
    else:
        writer.paragraph(["The record names nothing the key length leaves out."])

    writer.heading(3, titles["levers"], "levers")
    levers: list[Rich] = []
    for item in summary["levers"]:
        rich = _rich_text(item["text"], ctx)
        if item["pointer"] == "/payload/config/parameters/lambda_ec" and lambda_ec:
            f_ec = lambda_ec.get("f_ec")
            rich += [
                " It was estimated" + ("" if f_ec is None else f" with f_EC = {f_ec}")
                + " (", Link("how", "#lambda-ec-origin"), ")."
            ]
        levers.append(rich)
    if levers:
        snap_fix = any(item["text"].startswith("Measurement snap:")
                       for item in summary["levers"])
        writer.paragraph([LEVERS_SNAP if snap_fix else LEVERS_LEAD])
        writer.bullets(levers)
    else:
        writer.paragraph(["The record names no run setting that could lengthen "
                          "the key."])


# --------------------------------------------------------------------------
# Layer 2: the setup (report 0.8.0), the inputs
# --------------------------------------------------------------------------

#: The caption word of a family's matrices.
_CAPTION: Final[Mapping[str, str]] = {
    "port-grams": "Port",
    "instrument-matrix": "",
    "source": "",
}


def _caption(family: OperatorFamily, outcome: str) -> str:
    word = _CAPTION.get(family["kind"], "Outcome")
    return f"{word} {outcome}".strip()


def _entries(block: OperatorBlock) -> list[Sequence[str | float]]:
    return [entry for element in block["elements"]
            for row in element["matrix"] for entry in row]


def _text(text: str) -> Rich:
    return [text]


def _scalar_table(
    writer: Writer, blocks: Sequence[OperatorBlock], family: OperatorFamily,
    ctx: _Context,
) -> None:
    """Write the one-dimensional blocks of a family as one table, outcome by row."""
    outcomes = list(dict.fromkeys(
        element["outcome"] for block in blocks for element in block["elements"]
    ))
    values: dict[tuple[str, str], str] = {}
    residue = False
    for block in blocks:
        floor = residue_floor(_entries(block))
        for element in block["elements"]:
            entry = element["matrix"][0][0]
            residue = residue or is_residue(entry, floor)
            values[(block["title"], element["outcome"])] = format_entry(entry, floor)
    word = _CAPTION.get(family["kind"], "Outcome") or "Operator"
    writer.table(
        _header([word, *(f"{block['title']} ({block['basis'][0]})"
                         if block["basis"] and block["basis"][0] != block["title"]
                         else block["title"] for block in blocks)], ctx),
        [
            [_label(outcome, ctx),
             *(_text(values.get((block["title"], outcome), "—")) for block in blocks)]
            for outcome in outcomes
        ],
    )
    if residue:
        writer.paragraph([RESIDUE_NOTE])


def _matrix_block(
    writer: Writer, block: OperatorBlock, family: OperatorFamily, ctx: _Context
) -> None:
    rows = block["basis"]
    columns = block["column_basis"] or block["basis"]
    note = block["basis_note"]
    writer.paragraph([
        f"{block['title'][:1].upper()}{block['title'][1:]}. ",
        *([note] if note else ["Basis: ", "; ".join(
            f"{index}. {label}" for index, label in enumerate(rows, start=1)
        ), "."]),
        *_record_tail(block["pointer"], ctx),
    ])
    floor = residue_floor(_entries(block))
    residue = any(is_residue(entry, floor) for entry in _entries(block))
    for element in block["elements"]:
        cells = [[format_entry(entry, floor) for entry in row]
                 for row in element["matrix"]]
        caption = _caption(family, element["outcome"])
        size = max(len(cells), len(cells[0]) if cells else 0)

        def body(caption: str = caption, cells: list[list[str]] = cells) -> None:
            writer.matrix(caption, rows, columns, cells)

        if size > 8:
            writer.details(
                f"{caption}: {len(cells)} \u00d7 {len(cells[0])} matrix", body,
                open_=False,
            )
        else:
            body()
    if residue:
        writer.paragraph([RESIDUE_NOTE])


def _family(
    writer: Writer, family: OperatorFamily, ctx: _Context, level: int
) -> None:
    writer.heading(level, family["title"])
    lead: Rich = [
        *([] if family["text"] is None else _rich_text(family["text"], ctx)),
        *_claims_tail(family["claims"], ctx),
    ]
    if lead:
        writer.paragraph(lead)
    scalar = [
        block for block in family["blocks"]
        if all(len(element["matrix"]) == 1 and len(element["matrix"][0]) == 1
               for element in block["elements"])
    ]
    if scalar:
        _scalar_table(writer, scalar, family, ctx)
    for block in family["blocks"]:
        if block not in scalar:
            _matrix_block(writer, block, family, ctx)


def _parameter_label(name: str, ctx: _Context) -> Rich:
    """Return "Honest model: <name>", the name linked to its glossary definition."""
    if f"model.{name}" not in ctx.parameters:
        return [f"Honest model: {name}"]
    return ["Honest model: ", Link(name, f"#{parameter_anchor(f'model.{name}')}")]


def _parameter_value(name: str, value: Any, ctx: _Context) -> Rich:
    """Return an honest-model parameter's value, and where it has no effect, why.

    A parameter of another honest model than the run's (the SPDC mean pair
    number beside an ideal pair source) printed bare read as one the run
    used (the stage-9 experimentalist reader); the inputs table's note on it
    is repeated here.
    """
    text = with_decimal(value)
    unused = ctx.unused.get(f"model.{name}")
    return [text if unused is None else f"{text}; {unused}"]


def _fields(
    writer: Writer, rows: Sequence[tuple[str | Rich, Rich]], ctx: _Context
) -> None:
    writer.table(_header(["Field", "Value"], ctx),
                 [[_label(name, ctx) if isinstance(name, str) else name, value]
                  for name, value in rows])


def _station_key(station: SetupStation) -> str:
    return station["label"] or (
        "receiver" if station["index"] is None else str(station["index"])
    )


#: What names a station rather than describes it; with every record pointer,
#: left out when two stations are compared.
_STATION_NAMING: Final[frozenset[str]] = frozenset(
    {"index", "label", "party", "name", "pointer"}
)


def _station_data(station: SetupStation) -> str:
    """Return a station's description without its names and record pointers."""
    def strip(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: strip(item) for key, item in value.items()
                    if key not in _STATION_NAMING}
        if isinstance(value, list):
            return [strip(item) for item in value]
        return value

    return json.dumps(strip(dict(station)), sort_keys=True, default=str)


def _same_station(
    writer: Writer, station: SetupStation, same: SetupStation, ctx: _Context
) -> None:
    """Write a station identical to one above as a pointer to it."""
    name = station["name"]
    writer.heading(3, name[:1].upper() + name[1:], f"station-{_station_key(station)}")
    _fields(writer, [
        ("Party", _value(station["party"])),
        ("Station", _value(station["label"])),
        ("Record", _pointer(station["pointer"], ctx) or ["—"]),
    ], ctx)
    writer.paragraph([
        "Identical to ",
        Link(same["name"], f"#station-{_station_key(same)}"),
        ": the same input route, outcome alphabet, optical elements, detectors "
        "and measurement, read from this station's own record.",
    ])


def _long_fraction(value: Any) -> bool:
    """Whether a recorded ``p/q`` is too long to read in a sentence or a cell."""
    return isinstance(value, str) and "/" in value and len(value) > 24


def _star_cell(value: Any) -> Rich:
    """Return ε* decimal first: rounded up where inexact, a long fraction below."""
    shown = None if value is None else upper_decimal(value)
    if shown is None:
        return _value(value)
    decimal, exact = shown
    if exact:
        return _text(with_decimal(value))
    if _long_fraction(value):
        return [f"at most {decimal} (rounded up; the exact fraction is below)"]
    return [f"at most {decimal} (rounded up; exactly {value})"]


def _parameters(
    inputs: Sequence[InputRow], setup: SetupSection | None
) -> dict[str, tuple[str, str]]:
    """Return the honest model's parameters the setup's source table names.

    Each with its readable label and its meaning from the instance's
    parameter table; one without a meaning there is not defined.
    """
    source = None if setup is None else setup["source"]
    named = set() if source is None else {
        f"model.{name}" for name in source["honest_parameters"]
    }
    return {row["name"]: (row["label"], str(row["meaning"]))
            for row in inputs if row["name"] in named and row["meaning"]}


def _unused(inputs: Sequence[InputRow]) -> dict[str, str]:
    """Return what an input that has no effect on this run says about it, by name."""
    return {row["name"]: row["not_used"] for row in inputs if row["not_used"]}


def _optical(setup: SetupSection | None, inputs: Sequence[InputRow] = ()) -> bool:
    """Whether the page describes a photon-number receiver.

    A run whose stations are all declared finite POVMs (a qubit run) has no
    photon cutoff, exact window, element graph or squashing route, and its
    glossary leaves their optical entries out. A page that describes no station
    (a run refused before the receiver) keeps them where its inputs declare a
    photon cutoff, which an optical instance's inputs table still prints.
    """
    if setup is not None and setup["stations"]:
        return any(station["photon_cutoff"] is not None or station["elements"]
                   for station in setup["stations"])
    return any(row["name"].endswith("photon_cutoff") for row in inputs)


def _tabled(acceptance: SetupAcceptance) -> set[str]:
    """Return the outcomes the setup's acceptance table lists, one row each."""
    if acceptance["categories"]:
        return {row["outcome"] for row in acceptance["categories"]}
    return {str(row["outcome"]) for row in acceptance["honest"]}


def _table_probabilities(acceptance: SetupAcceptance | None) -> dict[str, float]:
    """Return each outcome's honest probability as the acceptance table shows it."""
    if acceptance is None:
        return {}
    if acceptance["categories"]:
        return {row["outcome"]: row["probability"]
                for row in acceptance["categories"] if row["probability"] is not None}
    return {str(row["outcome"]): float(row["probability"])
            for row in acceptance["honest"]}


def _probability(value: float | None) -> str:
    """Return a probability as six significant digits, or a dash."""
    return "—" if value is None else f"{value:.6g}"


def _frequency_range(lower: str, upper: str) -> str:
    """Return an acceptance interval of frequencies in decimals, ends included."""
    low, high = float(Fraction(lower)), float(Fraction(upper))
    if low == high:
        return f"exactly {low:.6g}"
    return f"{low:.6g} to {high:.6g}"


def _count_range(low: int | None, high: int | None, rounds: int | None) -> str:
    """Return the counts an interval admits out of the run's rounds."""
    if low is None or high is None or rounds is None:
        return "—"
    if low > high:
        return f"none of {rounds:,}"
    if low == high:
        return f"exactly {low:,} of {rounds:,}"
    return f"{low:,} to {high:,} of {rounds:,}"


def _station(writer: Writer, station: SetupStation, ctx: _Context) -> None:
    key = _station_key(station)
    name = station["name"]
    writer.heading(3, name[:1].upper() + name[1:], f"station-{key}")
    rows: list[tuple[str, Rich]] = [
        ("Party", _value(station["party"])),
        ("Station", _value(station["label"])),
        ("Input route", [station["route_text"]]),
    ]
    # A station with no photon-number model (a declared finite POVM) has no
    # channel modes, cutoff or exact window: three dashes there read as
    # values missing, and named optical terms the run does not use (n6).
    if (station["channel_modes"] or station["photon_cutoff"] is not None
            or station["exact_window"] is not None):
        rows += [
            ("Channel modes", [", ".join(station["channel_modes"]) or "—"]),
            ("Photon cutoff N", _value(station["photon_cutoff"])),
            ("Exact window", _value(station["exact_window"])),
        ]
    rows.append(("Record", _pointer(station["pointer"], ctx) or ["—"]))
    if station["claims"]:
        rows.append(("Statement", _joined(
            _claim_link(ctx.index["claims"][claim], ctx)
            for claim in station["claims"] if claim in ctx.index["claims"]
        ) or ["—"]))
    _fields(writer, rows, ctx)
    if station["outcomes"]:
        writer.heading(4, "Outcome alphabet")
        writer.table(
            _header(["Letter", "Meaning", "Click patterns"], ctx),
            [
                [[Code(letter["letter"])], [letter["meaning"]],
                 ["—" if letter["patterns"] is None else "; ".join(
                     "{" + ", ".join(pattern) + "}" for pattern in letter["patterns"]
                 )]]
                for letter in station["outcomes"]
            ],
        )
    if station["elements"]:
        writer.heading(4, "Optical elements")
        writer.table(
            _header(["Element", "What it is"], ctx),
            [[[Code(element["name"])], [element["description"]]]
             for element in station["elements"]],
        )
        if station["edges"]:
            writer.paragraph([
                "Order of the elements (light passes the first before the "
                "second): ",
                ", ".join(" → ".join(edge) for edge in station["edges"]), ".",
            ])
    if station["detectors"]:
        writer.heading(4, "Detectors")
        names = list(dict.fromkeys(
            name for detector in station["detectors"] for name in detector["parameters"]
        ))
        writer.table(
            _header(["Port", "Collects modes", *names], ctx),
            [
                [[Code(detector["port"])],
                 ["—" if detector["modes"] is None else ", ".join(detector["modes"])],
                 *(_text(with_decimal(detector["parameters"].get(name)))
                   for name in names)]
                for detector in station["detectors"]
            ],
        )
    for note in station["notes"]:
        writer.paragraph(_rich_text(note, ctx))
    families = station["families"]
    forms = _forms(station, ctx)
    lead = _measurement_lead(station, ctx)
    if not lead:
        if forms:
            writer.paragraph(forms)
        for family in families:
            _family(writer, family, ctx, 4)
        return
    # The POVM per photon number, with dark counts and the squashed target:
    # said why they are shown, then each folded in HTML under a line that
    # says what it holds (Markdown has no fold and writes them in place).
    writer.paragraph(lead)
    if forms:
        writer.paragraph(forms)
    for family in families:
        def tables(family: OperatorFamily = family) -> None:
            _family(writer, family, ctx, 4)

        inside = _FOLD_WORDS.get(family["kind"])
        writer.details(
            family["title"] + ("" if inside is None else f": {inside}"),
            tables, open_=False,
        )


#: What each form of a station's measurement is, by kind.
_FORM_WORDS: Final[tuple[tuple[str, str], ...]] = (
    ("photon-blocks", "per photon number, the receiver's measurement as "
                      "declared, before dark counts"),
    ("dark-composed", "the same with the declared dark counts composed in"),
    ("target-povm", "the squashed target POVM, the finite model the proof "
                    "analyses in place of the device"),
)


#: What each folded form of a station's measurement holds, by kind: the
#: line a reader sees before opening it.
_FOLD_WORDS: Final[Mapping[str, str]] = {
    "photon-blocks": "one operator table per outcome and photon number, before "
                     "dark counts",
    "dark-composed": "the same with the declared dark counts composed in",
    "target-povm": "the finite model the proof analyses in place of the device",
}


def _measurement_lead(station: SetupStation, ctx: _Context) -> Rich:
    """Return why a station's operator tables are shown and what to check in them.

    They are the measurement the key length is computed for, which the
    engaged A-EXACT and A-SPEC ask the user to vouch for; with a POVM per
    photon number, its 1-photon operators carry the detector efficiencies and
    splitting ratios, and with dark counts composed in, the dark-count
    probability. Empty for a station without operator tables.
    """
    kinds = {family["kind"] for family in station["families"]}
    if not kinds & {kind for kind, _ in _FORM_WORDS}:
        return []
    premises = [f"[[{short_id}]]" for short_id in ("A-EXACT", "A-SPEC")
                if short_id in ctx.present]
    text = (
        "Why these tables are shown: they are the measurement the key length is "
        "computed for, "
        + (f"which {' and '.join(premises)} ask you to vouch for"
           if premises else "which is yours to vouch for")
        + " as your receiver's. What to check: "
    )
    checks: list[str] = []
    if "photon-blocks" in kinds:
        checks.append("that the 1-photon operators agree with your detectors' "
                      "efficiencies and the splitting ratios above")
    if "dark-composed" in kinds:
        checks.append("that the table with dark counts agrees with your "
                      "dark-count probability")
    if not checks:
        checks.append("that the operators describe your receiver")
    return _rich_text(text + ", and ".join(checks) + ".", ctx)


def _forms(station: SetupStation, ctx: _Context) -> Rich:
    """Return the one sentence that says what each form of the POVM is."""
    kinds = {family["kind"]: family for family in station["families"]}
    present = [(kind, words) for kind, words in _FORM_WORDS if kind in kinds]
    if len(present) < 2:
        return []
    rich: Rich = [f"The measurement appears below in {len(present)} forms: "]
    for position, (kind, words) in enumerate(present):
        if position:
            rich.append("; and " if position == len(present) - 1 else "; ")
        rich.append(words)
        linked = [ctx.index["claims"][claim] for claim in kinds[kind]["claims"]
                  if claim in ctx.index["claims"]]
        if kind == "target-povm" and linked:
            rich += [" (", *_joined(_claim_link(claim, ctx) for claim in linked), ")"]
    rich.append(".")
    return rich


def _signals(signals: Sequence[Mapping[str, Any]]) -> Rich:
    """Return the source's signals with their weights, one cell."""
    return [", ".join(
        f"{signal['label']} (weight {with_decimal(signal['weight'])})"
        for signal in signals
    )]


#: The block that says what a round is, before the protocol's steps.
ROUND_TITLE: Final[str] = "What a round is"
ROUND_ANCHOR: Final[str] = "setup-round"


def _round(writer: Writer, block: RoundBlock, ctx: _Context) -> None:
    """Write what a round is and the premises on it, each glossed (0.29.0)."""
    writer.heading(3, ROUND_TITLE, ROUND_ANCHOR)
    writer.paragraph(_rich_text(block["text"], ctx))
    if block["premises"]:
        writer.paragraph([
            "How you cut the record into rounds bears on these premises, each in "
            "full under ", Link(SECTION_TITLES["assumptions"], "#assumptions"), ":",
        ])
        writer.bullets([
            _rich_text(f"[[{premise['short_id']}]]: {premise['gloss']}.", ctx)
            for premise in block["premises"]
        ])


def _setup(
    writer: Writer, setup: SetupSection, ctx: _Context, lead: Rich | None = None
) -> None:
    """Write "Your QKD setup" (report 0.8.0; runs/report/setup.py)."""
    writer.heading(2, SECTION_TITLES["setup"], "setup")
    if lead:
        writer.paragraph(lead)
    block = setup["round"]
    if block is not None:
        _round(writer, block, ctx)
    writer.heading(3, "Protocol", "setup-protocol")
    see_round: Rich = [" See ", Link(ROUND_TITLE, f"#{ROUND_ANCHOR}"), " above."]
    writer.numbered([
        [f"{step['title']}: ", *_rich_text(step["text"], ctx),
         *(see_round if block is not None
           and step["pointer"] == "/payload/config/rounds" else []),
         *_record_tail(step["pointer"], ctx)]
        for step in setup["protocol"]
    ])
    source = setup["source"]
    # Each note on what the record does not hold stands where its part
    # would, under that part's heading.
    if source is None and setup["source_notes"]:
        writer.heading(3, "Source", "setup-source")
        for note in setup["source_notes"]:
            writer.paragraph(_rich_text(note, ctx))
    if source is not None:
        writer.heading(3, "Source", "setup-source")
        writer.paragraph(_rich_text(source["text"], ctx))
        rows: list[tuple[str | Rich, Rich]] = [
            ("Source mode", _value(source["mode"])),
            ("Trusted", _value(source["trusted"])),
            ("Honest model", _value(source["honest_model"])),
            *((_parameter_label(name, ctx), _parameter_value(name, value, ctx))
              for name, value in source["honest_parameters"].items()),
            ("How the honest model is derived", _value(source["derivation"], ctx)),
            ("Status", _value(source["status"])),
        ]
        # No row where the source emits no declared signal (an untrusted
        # source with a placeholder letter; setup.py says so in the text).
        if source["signals"]:
            rows.append(("Signals", _signals(source["signals"])))
        rows.append(("Record", _pointer(source["pointer"], ctx) or ["—"]))
        _fields(writer, rows, ctx)
        for family in source["families"]:
            _family(writer, family, ctx, 4)
    if not setup["stations"] and setup["station_notes"]:
        writer.heading(3, "Stations", "setup-stations")
        for note in setup["station_notes"]:
            writer.paragraph(_rich_text(note, ctx))
    shown: list[SetupStation] = []
    for station in setup["stations"]:
        same = next((earlier for earlier in shown
                     if _station_data(earlier) == _station_data(station)), None)
        if same is None:
            _station(writer, station, ctx)
            shown.append(station)
        else:
            _same_station(writer, station, same, ctx)
    acceptance = setup["acceptance"]
    if acceptance is not None:
        writer.heading(3, "Acceptance test", "setup-acceptance")
        writer.paragraph([*_rich_text(acceptance["text"], ctx),
                          *_claims_tail(acceptance["claims"], ctx)])
        _fields(writer, [
            ("Acceptance categories", _value(acceptance["rows"])),
            ("Outcomes the honest model gives positive probability",
             _value(acceptance["support"])),
            ("Endpoint rule", _value(acceptance["endpoint_rule"])),
            ("Geometry", _value(acceptance["geometry"])),
            ("Completeness budget",
             _text(with_decimal(acceptance["completeness_budget"]))),
            ("Certified completeness ε*",
             _star_cell(acceptance["completeness_certified"])),
            ("Record", _pointer(acceptance["pointer"], ctx) or ["—"]),
        ], ctx)
        star = acceptance["completeness_certified"]
        if _long_fraction(star):
            def exact() -> None:
                writer.paragraph([f"ε* = {star}"])

            writer.details("ε* as an exact fraction", exact, open_=False)
        outcomes = acceptance["outcomes"]
        categories = acceptance["categories"]
        honest = acceptance["honest"]
        # The list repeats the table below where the table names every outcome.
        if outcomes and not set(outcomes) <= _tabled(acceptance):
            writer.paragraph([f"The {len(outcomes)} acceptance outcomes: ",
                              ", ".join(outcomes), "."])
        if categories:
            def box() -> None:
                writer.table(
                    _header(["Acceptance category", "Honest probability",
                             "Allowed frequency", "Allowed count"], ctx),
                    [[[row["outcome"]], [_probability(row["probability"])],
                      [_frequency_range(row["lower"], row["upper"])],
                      [_count_range(row["count_min"], row["count_max"],
                                    row["rounds"])]]
                     for row in categories],
                )

            # Folded in HTML; its line says what it holds.
            writer.details(
                f"Acceptance categories: the honest probability, the allowed "
                f"frequency and the allowed count of each of the "
                f"{len(categories)} outcomes", box, open_=False,
            )
        elif honest:
            def table() -> None:
                writer.table(
                    _header(["Acceptance outcome", "Honest probability"], ctx),
                    [[[str(row["outcome"])], [f"{row['probability']:.6g}"]]
                     for row in honest],
                )

            writer.details(
                f"Honest probability of each of the {len(honest)} outcomes", table,
                open_=False,
            )
    if setup["expected"] or setup["expected_notes"]:
        writer.heading(3, "Expected statistics of the honest model", "setup-expected")
        if setup["expected"] and setup["expected_basis"]:
            writer.paragraph(_rich_text(setup["expected_basis"], ctx))
        if setup["expected"]:
            writer.table(
                _header(["Statistic", "Value", "How it is computed", "Record"], ctx),
                [
                    [[item["name"]],
                     ["—" if item["value"] is None else f"{item['value']:.6g}"],
                     [item["how"]], _pointer(item["pointer"], ctx)]
                    for item in setup["expected"]
                ],
            )
        for note in setup["expected_notes"]:
            writer.paragraph(_rich_text(note, ctx))


def _inputs_section(
    writer: Writer, report: KeyRateReport, ctx: _Context,
    lambda_ec: LambdaEcOrigin | None,
) -> None:
    writer.heading(2, SECTION_TITLES["inputs"], "inputs")
    writer.paragraph([
        "Every value the run was computed for, in three tables: your devices and "
        "the channel, the budgets (the ε you choose), and the engine's settings. "
        "A value shows its default where it differs from it."
    ])
    _inputs(writer, report["sections"]["protocol"]["inputs"], ctx, lambda_ec)


def _snaps_section(writer: Writer, snaps: MeasurementSnaps, ctx: _Context) -> None:
    """Write the measurement snaps as a reader meets them.

    An appendix part: what the snaps mean for the number is said in the
    summary's Key rate considerations, which link here.
    """
    # The sentence that the run rests on A-SNAP is the plain sentences' own;
    # what else must be seen (support not preserved, a discrepancy) stays.
    shown = [warning for warning in snaps["warnings"]
             if not warning.startswith("The key rate rests on assumption A-SNAP")]
    if shown:
        writer.notice("Warning", [_rich_text(warning, ctx) for warning in shown])
    for sentence in snaps["plain"]:
        writer.paragraph(_rich_text(sentence, ctx))
    if snaps["rows"]:
        writer.table(
            _header(["Station", "Photon number", "Status", "Rests on A-SNAP?",
                     "Fix"], ctx),
            [
                [[row["station"] or "your receiver"],
                 _label(row["photons"], ctx),
                 _rich_text(row["status"], ctx),
                 ["yes" + ("" if row["group"] is None else f" ({row['group']})")
                  if row["rests_on_assumption"]
                  else "no: evaluated off its snap" if row.get("evaluated_off_snap")
                  else "no"],
                 _rich_text(row["fix"], ctx) if row["fix"] else ["—"]]
                for row in snaps["rows"]
            ],
        )
    writer.paragraph([
        "Every block's reference, radii, flags and record pointers, the "
        "reduction's own rounding and the run settings: ",
        Link("Measurement snaps in detail", "#snaps-detail"), ".",
    ])


# --------------------------------------------------------------------------
# Layer 3: the appendix
# --------------------------------------------------------------------------


def _how_computed(writer: Writer, report: KeyRateReport, ctx: _Context) -> None:
    sections = report["sections"]
    result = sections["result"]
    # The claim of the number the key length is computed from: on a run
    # reported at the certified tier the certified corollary, not the
    # first-order theorem, whose reading says the key rate rests on h_lb.
    bound_claim = (
        CERTIFIED_CLAIM if result["reported_tier"] == "certified" else FIRSTORDER_CLAIM
    )
    refusal = result["refusal"]
    if refusal is not None:
        # The readings explain how a key length is formed; a refused run has
        # none, so they would explain a headline rate it does not have.
        writer.paragraph(_rich_text(refused_numbers(result), ctx))
    else:
        for claim_id in (KEYLENGTH_CLAIM, bound_claim):
            reading = _reading(claim_id, ctx)
            if reading:
                writer.paragraph(reading)
    note = sections["summary"]["tier_note"]
    if note:
        writer.paragraph(_rich_text(note, ctx))
    security = result["security_parameter"]
    pairs: list[tuple[str, Any]] = [("outcome", result["outcome"])]
    if refusal is not None:
        pairs += [("refused at stage", refusal["stage"]),
                  ("reason", refusal["reason"]), ("detail", refusal["detail"]),
                  ("rule", refusal["rule"])]
    pairs += [
        ("key length", result["key_length"]),
        ("net key length", result["net_key_length"]),
        ("rate per round", result["rate_per_round"]),
        ("rounds", result["rounds"]),
        *_alpha_rows(result["alpha"]),
        ("reported tier", result["reported_tier"]),
        ("security parameter", security["value"]),
        *((f"term {name}", value) for name, value in security["terms"].items()),
        ("authentication factor", security["auth_factor"]),
        ("completeness ε*",
         None if result["completeness"] is None
         else result["completeness"]["eps_star"]),
        ("key length reason code", result["key_length_reason_code"]),
        ("reason text", result["reason_text"]),
    ]
    _pairs(writer, "Result", pairs, ctx)
    reason = result["key_length_reason"]
    if reason:
        # The raw row's capitals read as shouting; the engine's
        # own line is kept verbatim, collapsed, with one line saying what it is.
        writer.paragraph([
            "The engine also records why the key length is what it is in one "
            "line of its own, kept verbatim below; its capitals are the engine's "
            "emphasis, not the report's."
        ])
        writer.details("The engine's key-length reason, verbatim",
                       lambda: writer.paragraph(_rich_text(str(reason), ctx)),
                       open_=False)
    numerics = sections["numerics"]
    _diagnostics(writer, numerics, ctx, 4)
    search = numerics["alpha_search"]
    if search is not None:
        _alpha_search(writer, search, ctx, 4)


def _security_claims(writer: Writer, report: KeyRateReport, ctx: _Context) -> None:
    result = report["sections"]["result"]
    _claim_list(writer, "Security statement", result["statement_claims"], ctx, 4)
    _claim_list(writer, "Per execution", result["per_execution"], ctx, 4)
    if result["completeness"] is not None:
        _claim_list(writer, "Completeness", [result["completeness"]["claim"]], ctx, 4)
    _claim_list(writer, "Limitations", result["limitations"], ctx, 4)


def _checks(writer: Writer, report: KeyRateReport, ctx: _Context) -> None:
    checks = report["sections"]["checks"]
    writer.table(_header(_CHECK_HEADER, ctx), _check_rows(checks["checks"], ctx))
    if checks["decided_rows"]:
        writer.heading(4, "Decided conditions")
        for entry in checks["decided_rows"]:
            _entry(writer, entry, ctx, 5)
    _not_engaged(writer, checks["discharged_on_route"], "Discharged on this route",
                 ctx, 4)


def _route(writer: Writer, report: KeyRateReport, ctx: _Context) -> None:
    protocol = report["sections"]["protocol"]
    instance = protocol["instance"]
    writer.heading(4, "Instance")
    _pairs(writer, "Instance", [("instance", None)] if instance is None
           else list(instance.items()), ctx)
    document = protocol["document"]
    if document is not None:
        writer.heading(4, "Protocol document")
        _pairs(writer, "Document", list(document.items()), ctx)
    if protocol["facts"]:
        writer.heading(4, "Route")
        writer.table(
            _header(["Fact", "Value", "Record"], ctx),
            [[[Code(fact["name"])], _value(fact["value"], ctx),
              _pointer(fact["pointer"], ctx)]
             for fact in protocol["facts"]],
        )
    writer.heading(4, "Honest model")
    _pairs(writer, "Honest model", list(protocol["honest_model"].items()), ctx)
    writer.heading(4, "Preparation")
    _pairs(writer, "Preparation", list(protocol["preparation"].items()), ctx)


def _status_legend(writer: Writer) -> None:
    """Write what a claim's status means, the target of every "Review status" link."""
    writer.heading(4, "What a claim's status means", "status-legend")
    writer.bullets([[f"{name}: {meaning}."] for name, meaning in STATUS_LEGEND])


def _provenance(writer: Writer, report: KeyRateReport, ctx: _Context) -> None:
    provenance = report["sections"]["provenance"]
    fields: Mapping[str, Any] = provenance
    _status_legend(writer)
    draft = draft_sentence(report["sections"]["summary"]["drafts"])
    if draft is not None:
        writer.paragraph(_rich_text(draft, ctx))
    _pairs(writer, "Provenance", [
        (name, fields[name])
        for name in ("report_id", "record_schema_version", "report_schema_version",
                     "created_by", "config_digest", "engine", "platform",
                     "final_iterate", "reproduce")
    ], ctx)
    writer.heading(4, "Module versions")
    _pairs(writer, "Versions", list(provenance["module_versions"].items()), ctx)
    writer.heading(4, "Claim status")
    if provenance["claim_status"]:
        writer.table(
            _header(["Claim", REVIEW_STATUS, REVIEW_STATUS_CLOSURE], ctx),
            [[[Code(item["id"])], [item["status"]], [item["effective_status"]]]
             for item in provenance["claim_status"]],
        )
    else:
        # A table with a header and no rows reads as a rendering fault.
        writer.paragraph([
            "No claim status is listed: the run was refused before any result "
            "named a claim." if report["sections"]["result"]["refusal"] is not None
            else "No claim status is listed: the record names no claim."
        ])
    writer.heading(4, "Solver and tolerances")
    _pairs(writer, "Setting", [*provenance["solver"].items(),
                               *provenance["tolerances"].items()], ctx)
    if provenance["artefacts"]:
        writer.heading(4, "Artefacts")
        writer.table(
            _header(["Stage", "Station", "Kind", "Digest"], ctx),
            [[_value(item["stage"]), _value(item["station"]), _value(item["kind"]),
              [Code(str(item["digest"]))]]
             for item in provenance["artefacts"]],
        )


def _glossary(writer: Writer, tracker: _Tracker, ctx: _Context) -> None:
    page = "\n".join(tracker.seen)
    used = sorted(
        (term for term in terms()
         if (term.term in ctx.linked or _occurs(term, page))
         and (ctx.optical or not term.optical)),
        key=lambda term: term.term.lower(),
    )
    entries: list[tuple[str, Rich]] = []
    for term in used:
        see: Rich = []
        if term.see_claim is not None and term.see_claim in ctx.index["claims"]:
            see = [" See ", _claim_link(ctx.index["claims"][term.see_claim], ctx), "."]
        elif term.see is not None and term.see_claim is None:
            see = [" See ", *_rich_text(term.see, ctx), "."]
        entries.append((term.term,
                        [Anchor(term.anchor), term.term, ": ", term.text, *see]))
    # The honest model's parameters the setup names by their key, defined by
    # the instance's own parameter table (never by this module).
    for name, (label, meaning) in ctx.parameters.items():
        short = name.rsplit(".", 1)[-1]
        entries.append((short, [
            Anchor(parameter_anchor(name)), short, ": ", meaning.rstrip(".") + ".",
            " The instance's parameter ", Code(name),
            *([" (", label, ")"] if label else []), "; its value "
            "on this run is under ", Link("Your inputs", f"#input-{name}"), ".",
        ]))
    items = [rich for _, rich in sorted(entries, key=lambda item: item[0].lower())]
    if items:
        writer.bullets(items)
    else:
        writer.paragraph(["No glossary term occurs on this page."])


def _appendix(
    writer: Writer, report: KeyRateReport, ctx: _Context, tracker: _Tracker
) -> None:
    writer.heading(2, SECTION_TITLES["appendix"], "appendix")
    _appendix_part(writer, "how-computed", lambda: _how_computed(writer, report, ctx))
    snaps = report["sections"]["protocol"]["measurement_snaps"]
    if snaps is not None:
        _appendix_part(writer, "measurement-snaps",
                       lambda: _snaps_section(writer, snaps, ctx))
        _appendix_part(writer, "snaps-detail",
                       lambda: _measurement_snaps(writer, snaps, ctx, level=None))
    _appendix_part(writer, "security-claims",
                   lambda: _security_claims(writer, report, ctx))
    _appendix_part(writer, "checks", lambda: _checks(writer, report, ctx))
    not_engaged = report["sections"]["assumptions"]["not_engaged"]
    if not_engaged:
        _appendix_part(writer, "not-engaged", lambda: _not_engaged(
            writer, not_engaged, "Closure members excluded on this route", ctx, 4))
    _appendix_part(writer, "route", lambda: _route(writer, report, ctx))
    _appendix_part(writer, "provenance", lambda: _provenance(writer, report, ctx))
    _appendix_part(writer, "glossary", lambda: _glossary(writer, tracker, ctx))


# --------------------------------------------------------------------------
# The run report
# --------------------------------------------------------------------------


def write_report(
    writer: Writer,
    report: KeyRateReport,
    contract_link: ContractLink,
    *,
    excerpt_link: ExcerptLink | None = None,
    repo_base: str | None = None,
    lambda_ec: LambdaEcOrigin | None = None,
    repo_served: Callable[[str], bool] | None = None,
) -> str:
    """Walk one run report through ``writer`` and return the document.

    ``excerpt_link`` links every record pointer to its excerpt (the caller
    writes the excerpts); ``repo_base`` links every repository path the report
    prints, and ``repo_served`` (where given) only those it accepts, the rest
    printed in code; ``lambda_ec`` is the λ_EC estimate's side file, shown
    under the λ_EC input. Without them pointers and paths are plain text.
    """
    tracker = _Tracker(writer)
    sections = report["sections"]
    entries = [
        *group_entries(sections["assumptions"]["groups"]),
        *sections["numerics"]["entries"],
        *sections["checks"]["decided_rows"],
    ]
    acceptance = sections["setup"]["acceptance"]
    ctx = _Context(
        index=report["index"],
        contract_link=contract_link,
        present={entry["short_id"] for entry in entries},
        numerics=any(entry.get("category") == "numerical-trust" for entry in entries),
        inputs={row["name"] for row in sections["protocol"]["inputs"]},
        excerpt_link=excerpt_link,
        pointers=frozenset(report_pointers(report)),
        repo_base=repo_base,
        repo_served=repo_served,
        link_terms=writer.links_terms,
        aliases={alias: term for term in terms() for alias in term.aliases},
        outcomes=() if acceptance is None else tuple(acceptance["outcomes"]),
        honest=_table_probabilities(acceptance),
        parameters=_parameters(sections["protocol"]["inputs"], sections["setup"]),
        unused=_unused(sections["protocol"]["inputs"]),
        optical=_optical(sections["setup"], sections["protocol"]["inputs"]),
    )
    tracker.heading(1, "Key-rate report")
    _toc(tracker, report)
    _summary(tracker, report, ctx, lambda_ec)
    _setup(tracker, sections["setup"], ctx)
    _inputs_section(tracker, report, ctx, lambda_ec)
    refusal = sections["result"]["refusal"]
    empty_because = (
        None if refusal is None
        else REFUSED_NOT_LISTED.format(
            stage=refusal["stage"] or "unknown", reason=refusal["reason"]
        ) + (" " + REFUSED_DECLARED_BELOW
             if sections["assumptions"]["user_declared"] else "")
    )
    # The long assumptions section sits last before the appendix, which holds
    # the measurement snaps.
    _assumptions(tracker, sections["assumptions"], ctx, empty_because,
                 engine=sections["numerics"]["entries"])
    _appendix(tracker, report, ctx, tracker)
    return writer.text()


# --------------------------------------------------------------------------
# The sweep report (report 0.10.0)
# --------------------------------------------------------------------------

#: The sweep page's sections, in order.
_SWEEP_PARTS: Final[tuple[tuple[str, str], ...]] = (
    ("summary", "Summary"),
    ("setup", "Your QKD setup"),
    ("inputs", "Your inputs"),
    ("assumptions", "Assumptions you vouch for"),
    ("points", "Per-point differences"),
    ("appendix", "Appendix"),
)

_SWEEP_APPENDIX: Final[tuple[tuple[str, str], ...]] = (
    ("checks", "Checks the engine ran"),
    ("not-engaged", "Not engaged on this route"),
    ("provenance", "Provenance"),
    ("glossary", "Glossary"),
)


def _snap_cell(point: SweepPoint) -> str:
    if point["rests_on_a_snap"] is None:
        return "—"
    if point["rests_on_a_snap"]:
        blocks, sectors = point["resting_blocks"], point["resting_sectors"]
        parts = [f"{blocks} block" + ("" if blocks == 1 else "s")]
        if sectors:
            parts.append(f"{sectors} emission sector" + ("" if sectors == 1 else "s"))
        return f"rests on A-SNAP ({', '.join(parts)})"
    return "kept, or evaluated off its snap"


def _sweep_summary(
    writer: Writer, sweep: SweepReport, ctx: _Context, point_link: PointLink
) -> None:
    common = sweep["common"]
    writer.heading(2, "Summary", "summary")
    writer.heading(3, "The points", "points-summary")
    writer.table(
        _header(["Point", *(input_label(name) or name for name in sweep["varying"]),
                 "Key length", "Bits per round", "ε", "Outcome", "Report"], ctx),
        [
            [[str(point["index"])],
             *(_text(with_decimal(point["values"].get(name)))
               for name in sweep["varying"]),
             ["—" if point["key_length"] is None else f"{point['key_length']:,}"],
             ["—" if point["rate_per_round"] is None
              else f"{point['rate_per_round']:.3g}"],
             ["—" if point["security_parameter"] is None
              else f"{point['security_parameter']:.3g}"],
             [point["outcome"]],
             [Link("report", point_link(point))]]
            for point in sweep["points"]
        ],
    )
    writer.paragraph([
        "Bits per round is a point's key length divided by all its n rounds, "
        "the rounds that give no raw key bit included."
    ])
    writer.heading(3, "What the guarantee means", "guarantee")
    _guarantee(writer, common["guarantee"], ctx, sweep=True,
               first_order=any(point["reported_tier"] == "first-order"
                               for point in sweep["points"]))
    writer.heading(3, "Not counted", "not-counted")
    _flags(writer, common["not_counted"], ctx)
    if common["limitations"]:
        writer.bullets([
            [*_rich_text(claim["summary"], ctx, _module_of(claim["id"])), " (",
             _claim_link(claim, ctx), ")"]
            for claim in common["limitations"]
        ])
    writer.heading(3, "What you vouch for", "vouch")
    count = len(group_entries(common["assumptions"]["groups"]))
    numerics = len(common["numerics"]["entries"])
    writer.paragraph([
        f"The points rest on {count} premises about your devices, the setup and "
        f"supplied artefacts, and {numerics} about the engine's numerics, listed "
        "once under ",
        Link(SECTION_TITLES["assumptions"], "#assumptions"),
        "; a premise that only some points rest on names them.",
    ])
    _user_declared(writer, common["user_declared"], ctx)


def _sweep_points(
    writer: Writer, sweep: SweepReport, ctx: _Context, point_link: PointLink
) -> None:
    writer.heading(2, "Per-point differences", "points")
    writer.paragraph([
        "What differs from point to point: the varying inputs, each point's own "
        "numbers, its route and whether its key length rests on a measurement "
        "snap. Each point's report has the rest."
    ])
    header = ["Point", "Label", *sweep["varying"], "Key length", "Net key length",
              "Rate per round", "Tier", "Security parameter", "Outcome", "Route",
              "Measurement snaps", "Report"]
    writer.table(_header(header, ctx), [
        [
            [str(point["index"])],
            _value(point["label"]),
            *(_text(with_decimal(point["values"].get(name)))
               for name in sweep["varying"]),
            _value(point["key_length"]),
            _value(point["net_key_length"]),
            _value(point["rate_per_round"]),
            _value(point["reported_tier"]),
            _value(point["security_parameter"]),
            [point["outcome"]] if point["refusal"] is None
            else [point["outcome"], " ", Code(str(point["refusal"]["reason"]))],
            ["—" if point["route_signature"] is None
             else "differs" if point["route_differs"] else "common"],
            [_snap_cell(point)],
            [Link("report", point_link(point))],
        ]
        for point in sweep["points"]
    ])
    differing = [point for point in sweep["points"] if point["route_differs"]]
    if differing:
        writer.heading(3, "Points on another route")
        writer.table(
            _header(["Point", "Added", "Removed"], ctx),
            [[[str(point["index"])],
              _joined(_target(i, ctx) for i in point["route_delta"]["added"]),
              _joined(_target(i, ctx) for i in point["route_delta"]["removed"])]
             for point in differing],
        )


def write_sweep(
    writer: Writer,
    sweep: SweepReport,
    contract_link: ContractLink,
    point_link: PointLink,
    *,
    repo_base: str | None = None,
    excerpt_link: ExcerptLink | None = None,
    excerpt_pointers: frozenset[str] = frozenset(),
    repo_served: Callable[[str], bool] | None = None,
) -> str:
    """Walk one sweep report through ``writer`` and return the document.

    The same layers as a run: the summary (the points'
    key lengths and the guarantee once), the setup of the first completed
    point with what varies, the shared inputs and premises once, the
    per-point differences, the appendix. A record pointer links to the
    excerpts of the point whose setup is shown, where ``excerpt_link`` is
    given and the pointer is one of that point's (``excerpt_pointers``).
    """
    tracker = _Tracker(writer)
    common = sweep["common"]
    refused = [point for point in sweep["points"] if point["refusal"] is not None]
    entries = [
        *group_entries(common["assumptions"]["groups"]),
        *common["numerics"]["entries"],
        *common["decided_rows"],
    ]
    setup = common["setup"]
    acceptance = None if setup is None else setup["acceptance"]
    ctx = _Context(
        index=sweep["index"],
        contract_link=contract_link,
        present={entry["short_id"] for entry in entries},
        numerics=any(entry.get("category") == "numerical-trust" for entry in entries),
        inputs={row["name"] for row in common["inputs"]},
        all_points="all completed points" if refused else "all points",
        excerpt_link=excerpt_link,
        pointers=excerpt_pointers,
        repo_base=repo_base,
        repo_served=repo_served,
        link_terms=writer.links_terms,
        aliases={alias: term for term in terms() for alias in term.aliases},
        outcomes=() if acceptance is None else tuple(acceptance["outcomes"]),
        honest=_table_probabilities(acceptance),
        parameters=_parameters(common["inputs"], setup),
        unused=_unused(common["inputs"]),
        optical=_optical(setup, common["inputs"]),
    )
    tracker.heading(1, "Key-rate sweep report")
    tracker.heading(2, "Contents", "contents")
    tracker.bullets([
        [Link(title, f"#{anchor}"),
         *([": ", *_joined((Link(sub, f"#{key}") for key, sub in _SWEEP_APPENDIX),
                           " · ")] if anchor == "appendix" else [])]
        for anchor, title in _SWEEP_PARTS
    ])
    _sweep_summary(tracker, sweep, ctx, point_link)
    if setup is not None and common["setup_point"] is not None:
        shown = next(point for point in sweep["points"]
                     if point["index"] == common["setup_point"])
        varying = ", ".join(sweep["varying"])
        _setup(tracker, setup, ctx, lead=[
            f"This is the setup of point {shown['index']} (",
            Link("its report", point_link(shown)), "). "
            + (f"Across the points these inputs vary: {varying}; each point's "
               "values are in the points table, and everything below that does "
               "not depend on them holds for every point."
               if varying else "No input varies across the points."),
        ])
    else:
        tracker.heading(2, SECTION_TITLES["setup"], "setup")
        tracker.paragraph(["No point completed, so no setup is shown."])
    tracker.heading(2, SECTION_TITLES["inputs"], "inputs")
    tracker.paragraph([
        "The inputs equal at every point; those that vary are in the points table."
    ])
    _inputs(tracker, common["inputs"], ctx)
    empty_because = (
        SWEEP_ALL_REFUSED if len(refused) == len(sweep["points"]) else None
    )
    _assumptions(tracker, common["assumptions"], ctx, empty_because,
                 engine=common["numerics"]["entries"])
    _sweep_points(tracker, sweep, ctx, point_link)

    tracker.heading(2, SECTION_TITLES["appendix"], "appendix")
    titles = dict(_SWEEP_APPENDIX)

    def part(key: str, body: Callable[[], None]) -> None:
        tracker.heading(3, titles[key], key)
        tracker.details(titles[key], body, open_=key == "glossary")

    def checks() -> None:
        tracker.table(_header(_CHECK_HEADER, ctx), _check_rows(common["checks"], ctx))
        if common["decided_rows"]:
            tracker.heading(4, "Decided conditions")
            for entry in common["decided_rows"]:
                _entry(tracker, entry, ctx, 5)
        _not_engaged(tracker, common["discharged_on_route"],
                     "Discharged on the route", ctx, 4)

    def provenance() -> None:
        # The guarantee's and the drafts' links to the legend land here.
        _status_legend(tracker)
        _pairs(tracker, "Sweep", [
            ("id", sweep["id"]),
            ("points", len(sweep["points"])),
            ("record schema", sweep["record_schema_version"]),
            ("report schema", sweep["report_schema_version"]),
        ], ctx)
        instance = common["instance"]
        _pairs(tracker, "Instance", [("instance", None)] if instance is None
               else list(instance.items()), ctx)
        _pairs(tracker, "Provenance", list(common["provenance"].items()), ctx)

    part("checks", checks)
    part("not-engaged", lambda: _not_engaged(
        tracker, common["assumptions"]["not_engaged"], "Not engaged on the route",
        ctx, 4))
    part("provenance", provenance)
    part("glossary", lambda: _glossary(tracker, tracker, ctx))
    return writer.text()
