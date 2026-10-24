#!/usr/bin/env python3
r"""Motivation: what an editor looks for, without a tax on everyone else.

Contracts can hold statements that a reader cannot use, of kinds a machine
can point at but cannot judge: a very long remark; a definition's lead-in
listing dozens of claims; a theorem with many pointers in its statement;
`\emph{Range.}`-style headed paragraphs inside a theorem, which
are often several claims in one; a "general format" second track inside a
result; sentences that are inventories of claims the generated "Used by" and
"Imports" lines already show; and statements and proofs pointing at claims the
header only mentions, where a reader cannot tell a pointer from a dependency
(in a proof naming an assumption, possibly a premise nobody declared).

Each of these is sometimes right: a long remark that should be long stays
long. So none of them is a check. A warning must not become a
productivity tax. These heuristics are therefore advice, run only on demand in an
explicit
editorial pass (`harness/roles/editor.md`):

- `python -m harness.check_claims --advice [--module <id>] [--rule <name>]`
  is the only entry point, and `check_claims` imports this module only under
  that flag, so no default run pays for it or prints it;
- advice never changes the exit code: only the default checks set it;
- there is no waiver list, baseline or acknowledgement of any kind: a hit
  needs no answer, and a drafter or verifier is never asked to answer one;
- the thresholds are the constants below, changed by ordinary review.

`tests/harness/test_check_advice.py` pins all of this. The rules reuse
`check_claims`' reader, as `check_presentation` does, and parse nothing of
their own.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from harness.check_claims import (
    POINTER_KINDS,
    PROOF_RE,
    REF_RE,
    STATEMENT_REF_KINDS,
    XREF_RE,
    Claim,
    Repo,
    a_kind,
    contract_of,
    environment_span,
    in_scope,
    label_owners,
    strip_comments,
)
from harness.contract_navigation import ABBREVIATIONS

#: Words (whitespace-separated, comments stripped) above which a statement of
#: each kind is flagged; kinds not listed are never flagged.
STATEMENT_WORDS: dict[str, int] = {
    "rem": 500, "def": 600, "thm": 400, "lem": 400, "prop": 400, "cor": 300,
    "ass": 250, "req": 300,
}
LEAD_IN_WORDS = 150
INVENTORY_REFERENCES = 6

#: Every advice rule, in report order, with the heuristic it applies.
RULES: dict[str, str] = {
    "long-statement": "a statement longer than its kind's threshold in words",
    "long-lead-in": f"a lead-in longer than {LEAD_IN_WORDS} words",
    "statement-ref-mention": "a statement (thm, lem, prop, cor, def, ass, fact) "
                             "references a claim the header only mentions",
    "proof-ref-mention": "a proof references a claim the header only mentions",
    "statement-heading": r"\emph{Capitalised.} paragraph headings in a result or "
                         "definition statement (one hit per statement)",
    "general-format-track": "'general format' in a result or definition statement "
                            "(one hit per statement)",
    "inventory-sentence": f"one sentence with {INVENTORY_REFERENCES} or more "
                          "references",
}
#: "A result or definition": the kinds whose statement the heading and
#: general-format heuristics read.
RESULT_KINDS = frozenset({"thm", "lem", "prop", "cor", "def"})
HEADING_RE = re.compile(r"\\emph\{\s*([A-Z][^{}]*\.)\s*\}")
GENERAL_FORMAT_RE = re.compile(r"general[\s~]+format", re.I)
#: Where a sentence ends: after . ! or ? before a capital or a command, at a
#: blank line, and at an \item (a list item reads as its own sentence).
SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\\(])|\n[ \t]*\n|\\item(?![A-Za-z])")


@dataclass(frozen=True, order=True)
class Advice:
    """One advice hit, rendered like a check_claims finding."""

    path: str
    line: int
    rule: str
    message: str
    module: str = ""

    def render(self) -> str:
        """Return the one-line rendering used on stdout."""
        return f"{self.path}:{self.line}: advice[{self.rule}]: {self.message}"


class Collector:
    """Accumulates advice for one repository."""

    def __init__(self, repo: Repo) -> None:
        """Start an empty collection over ``repo``."""
        self.repo = repo
        self.hits: list[Advice] = []

    def claim(self, claim: Claim, line: int, rule: str, message: str) -> None:
        """Record one hit at a line of a claim file, under a key of ``RULES``."""
        assert rule in RULES, rule
        self.hits.append(Advice(claim.rel, line, rule, message, claim.module_id))


def words(text: str) -> int:
    """Count whitespace-separated words, TeX included."""
    return len(text.split())


@dataclass(frozen=True)
class Reference:
    r"""One ``\ref``, ``\eqref`` or ``\xref`` in a body, resolved to its claim."""

    offset: int
    written: str
    target: str


def references(repo: Repo, claim: Claim, body: str, start: int,
               end: int) -> list[Reference]:
    r"""Return the references in ``body[start:end]`` that resolve to another claim.

    A ``\ref`` resolves in the claim's contract (``label_owners``), as LaTeX
    reads it; each label of a comma list counts. A reference to the claim's
    own labels is left out.
    """
    owners = label_owners(repo)
    contract = contract_of(claim.claim_id)
    found: list[Reference] = []
    for match in REF_RE.finditer(body, start, end):
        command = match.group(0).split("{", 1)[0]
        for raw in match.group(1).split(","):
            label = raw.strip()
            owner = owners.get((contract, label))
            if owner is not None and owner != claim.claim_id:
                found.append(Reference(match.start(), f"{command}{{{label}}}", owner))
    for match in XREF_RE.finditer(body, start, end):
        target = match.group(1).strip()
        if target in repo.claims and target != claim.claim_id:
            found.append(Reference(match.start(), f"\\xref{{{target}}}", target))
    return sorted(found, key=lambda ref: ref.offset)


def only_mentioned(repo: Repo, claim: Claim) -> set[str]:
    """Return the claims the header mentions and neither uses nor assumes."""
    declared = set(claim.resolved_uses)
    for short_id in claim.assumes:
        owner = repo.assumptions.get(short_id)
        if owner is not None:
            declared.add(owner.claim_id)
    return set(claim.resolved_mentions) - declared


def proof_spans(body: str, start: int) -> list[tuple[int, int]]:
    """Return the content spans of the proof environments after ``start``."""
    spans = []
    for match in PROOF_RE.finditer(body, start):
        close = body.find("\\end{proof}", match.end())
        spans.append((match.end(), len(body) if close == -1 else close))
    return spans


def target_words(repo: Repo, target_id: str) -> str:
    """Return a target as "a remark ('<id>')", with its short id if it has one."""
    target = repo.claims[target_id]
    short_id = target.header.get("short_id")
    suffix = f", {short_id}" if short_id else ""
    return f"{a_kind(target.kind)} ('{target_id}'{suffix})"


def check_lengths(out: Collector, claim: Claim, body: str, begin: int,
                  content: int, close: int) -> None:
    """``long-statement`` and ``long-lead-in``."""
    limit = STATEMENT_WORDS.get(claim.kind)
    count = words(body[content:close])
    if limit is not None and count > limit:
        out.claim(claim, claim.line_at(body, content), "long-statement",
                  f"the statement has {count} words, above {limit} for "
                  f"{a_kind(claim.kind)}: it may carry commentary, an inventory or a "
                  "second track that a remark, a lead-in or design.md would hold")
    lead = words(body[:begin])
    if lead > LEAD_IN_WORDS:
        out.claim(claim, claim.body_start, "long-lead-in",
                  f"the lead-in has {lead} words, above {LEAD_IN_WORDS}: a lead-in "
                  "says in a sentence or two what the claim is for")


def check_mention_references(out: Collector, claim: Claim, body: str,
                             content: int, close: int, end: int) -> None:
    """``statement-ref-mention`` and ``proof-ref-mention``."""
    repo = out.repo
    mentioned = only_mentioned(repo, claim)
    if not mentioned:
        return
    if claim.kind in STATEMENT_REF_KINDS:
        for ref in references(repo, claim, body, content, close):
            # A remark, requirement or example is the separation rule
            # statement-ref-kind's (check 13), never advice.
            if (ref.target in mentioned
                    and repo.claims[ref.target].kind not in POINTER_KINDS):
                out.claim(claim, claim.line_at(body, ref.offset),
                          "statement-ref-mention",
                          f"the statement references {ref.written}, "
                          f"{target_words(repo, ref.target)}, which the header only "
                          "mentions: a pointer belongs in the lead-in, a dependency "
                          "in uses or assumes")
    for start, stop in proof_spans(body, end):
        for ref in references(repo, claim, body, start, stop):
            if ref.target not in mentioned:
                continue
            what = target_words(repo, ref.target)
            if repo.claims[ref.target].kind == "ass":
                message = (f"possible missed premise: the proof references "
                           f"{ref.written}, {what}, which the header only mentions; "
                           "if the proof rests on it, it belongs in assumes")
            else:
                message = (f"the proof references {ref.written}, {what}, which the "
                           "header only mentions; if the proof rests on it, it "
                           "belongs in uses")
            out.claim(claim, claim.line_at(body, ref.offset), "proof-ref-mention",
                      message)


def check_statement_shape(out: Collector, claim: Claim, body: str, content: int,
                          close: int) -> None:
    """``statement-heading`` and ``general-format-track``: one hit per statement."""
    if claim.kind not in RESULT_KINDS:
        return
    headings = list(HEADING_RE.finditer(body, content, close))
    if headings:
        shown = ", ".join(f"\\emph{{{match.group(1)}}}" for match in headings)
        out.claim(claim, claim.line_at(body, headings[0].start()), "statement-heading",
                  f"the statement of {a_kind(claim.kind)} has headed paragraphs "
                  f"({shown}): they are often several claims in one, or commentary")
    tracks = list(GENERAL_FORMAT_RE.finditer(body, content, close))
    if tracks:
        times = "once" if len(tracks) == 1 else f"{len(tracks)} times"
        out.claim(claim, claim.line_at(body, tracks[0].start()), "general-format-track",
                  f"the statement of {a_kind(claim.kind)} names the general format "
                  f"{times}: a second track may be a claim of its own, or a remark")


def sentences(body: str) -> list[tuple[int, int]]:
    """Split a body into sentence spans (offsets); abbreviations end none."""
    spans: list[tuple[int, int]] = []
    start = 0
    for match in SENTENCE_END_RE.finditer(body):
        before = body[start:match.start()].rsplit(None, 1)
        word = before[-1].rstrip(".").lstrip("(").lower() if before else ""
        if body[match.start() - 1:match.start()] == "." and word in ABBREVIATIONS:
            continue
        spans.append((start, match.start()))
        start = match.end()
    spans.append((start, len(body)))
    return spans


def check_inventory(out: Collector, claim: Claim, body: str) -> None:
    """``inventory-sentence``: the whole body, lead-in, statement and proof."""
    for start, stop in sentences(body):
        found = references(out.repo, claim, body, start, stop)
        if len(found) >= INVENTORY_REFERENCES:
            out.claim(claim, claim.line_at(body, found[0].offset),
                      "inventory-sentence",
                      f"one sentence holds {len(found)} references: an inventory of "
                      "claims is what the generated Used by, Assumed by and Imports "
                      "lines and the graphs already show")


def advice(repo: Repo) -> list[Advice]:
    """Run every heuristic over a loaded repository."""
    out = Collector(repo)
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        body = strip_comments(claim.body)
        span = environment_span(body)
        if span is None:
            continue                # check_claims' identity check reports it
        check_lengths(out, claim, body, span.begin, span.content, span.close)
        check_mention_references(out, claim, body, span.content, span.close,
                                 span.end)
        check_statement_shape(out, claim, body, span.content, span.close)
        check_inventory(out, claim, body)
    return sorted(out.hits)


def report_advice(repo: Repo, wanted: str | None, scope: str,
                  rule: str | None = None) -> int:
    """Print the advice in scope and a count per rule; return how many hits.

    The layout is the presentation rules': one ``path:line: message`` line per
    hit, then per rule its hits, the files they stand in and the heuristic,
    and a closing line saying that nothing blocks. The caller never derives
    an exit code from the return value.
    """
    rules = [rule] if rule else list(RULES)
    hits = [hit for hit in advice(repo)
            if hit.rule in rules and in_scope(hit.module, wanted)]
    for hit in hits:
        print(hit.render())
    counts = dict.fromkeys(rules, 0)
    files: dict[str, set[str]] = {name: set() for name in rules}
    for hit in hits:
        counts[hit.rule] += 1
        files[hit.rule].add(hit.path)
    width = max(len(name) for name in [*rules, "total"])
    print(f"advice under {scope}: hits, files, heuristic")
    for name in rules:
        print(f"  {name.ljust(width)} {counts[name]:6} {len(files[name]):6}  "
              f"{RULES[name]}")
    every = {path for paths in files.values() for path in paths}
    print(f"  {'total'.ljust(width)} {len(hits):6} {len(every):6}")
    premises = sum(1 for hit in hits if hit.message.startswith("possible missed"))
    if premises:
        print(f"  of the proof references, {premises} name an assumption the "
              "header does not declare (possible missed premises)")
    print("advice only: nothing here blocks, and no hit needs an answer")
    return len(hits)
