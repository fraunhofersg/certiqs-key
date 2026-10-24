#!/usr/bin/env python3
r"""Motivation: a change whose dependents nobody can enumerate.

When a module's mathematics sits in a single LaTeX contract of thousands of
lines, every edit, however local, sits in that one file, so nobody can say
which claims a change reached: the re-review scope of a one-line repair and of
a new theorem are the same document, and a claim silently acquires
dependencies by standing next to them. This checker makes that scope
computable and turns an undeclared dependency into an error: one claim per
file, its edges declared in its own header, and a `\ref` into a claim the
header does not list, an assumption leant on but not declared, a cycle, a
citation without a locator or outside `refs/index.json`, a settled claim whose
proof is only a sketch, a `fact` (an imported published result) that is not
cited or that leans on a local theorem --
each of them a message with a file and a line rather than something a reader
is expected to notice.

It checks form only. Whether a proof is correct, whether an edge is
necessary and whether an assumption is reasonable are the verifier's and the
human's (`spec/claim-format.md` §6).

Status is local plus computed: a claim can be accepted conditional on its
dependencies being true (without those dependencies accepted yet). A header
`status` is the LOCAL judgement: this statement and this proof, given what
the file uses and assumes, were verified or accepted. The EFFECTIVE status is
computed here: the minimum, on the ladder draft < verified < accepted <
implemented, over the claim's transitive closure under `uses` and `assumes`,
itself included. A module's batch is accepted when its effective status is
accepted, so a module version keeps its meaning. A rule that refused a
settled claim resting on a draft one would make one substantive amendment
drop a status line and then demand the same edit in every claim of its
dependent closure, and the reverse edit after the review, a cascade that
records nothing a reader cannot compute from the graph.

Three details of the computation, each with its reason. `superseded` ranks
BELOW draft rather than being excluded, so a claim still resting on a
superseded statement says so (excluding it would let such a claim keep an
effective status that its closure no longer supports; `superseded` stays
outside the ladder for the local checks, which is what the exemption in
`spec/claim-format.md` §6 means). `mentions` is excluded, as it is
everywhere else: a mention is not a dependency. An `assumes` entry is
resolved by short id to the assumption that owns it, wherever it lives --
the declaration is a real dependency and short ids are unique
repository-wide, so a foreign module's assumption binds a claim exactly as a
local one does (the compiler's A-ATK is the case). The walk collects the
reachable set, so a cycle through the combined uses/assumes graph -- check 5
forbids one through `uses` alone, and nothing forbids one through both --
cannot make it diverge.

`--dependents` walks `uses` edges and, for an assumption, the `assumes`
declarations that name it (a restatement of the receiver's A-FLOAT, which
forty claims declare, would otherwise have an empty machine re-review scope
because only `uses` was indexed). Claims that merely `mention` the target are
listed separately and are not counted: a mention is not a dependency, but a
reviewer re-reading a changed claim wants to know who talks about it.

Reading-group anchors are checked for order and coverage to prevent stale
navigation. Graph exports include assumes as well as uses, human titles and
explicit boundary nodes; --focus selects a complete prerequisite closure.
Co-located summaries are checked as nonempty plain text: TeX in these fields
would bypass body symbol checks and render differently in PDF and Markdown.
Their accuracy remains a human judgement, not a new mathematical review gate.

A submodule may name sibling submodules (by bare name) and other cores'
modules or submodules (by full id) in its `depends_on`: a submodule may
compose the instance a sibling builds, the
weight route of wpfss uses the receiver's detector-imperfections results, and
a declared, acyclic edge is what lets a submodule be deleted together with
its dependents and nothing else; the alternative, a mention, would
under-record a real dependency (check 0b).

The claim body's cross-references are checked, each for an error class the
syntax invites (check 10). A cross-contract reference written as
`\texttt{module/label}` is neither validated nor linked, and a `\ref` to a
label that another contract defines as well is silently resolved by LaTeX to
the local one: `\xref{<full id>}` replaces both, and it is checked to name an
existing claim of another contract that the header declares, since a link the
PDF cannot resolve fails only as a bold marker in a page nobody opens.
`[[label]]` links in summaries and abstracts are checked for the same reason.
A `\label` defined twice in one assembled contract (a core and its
submodules) makes LaTeX's references ambiguous, and the contract, not the
claim file, is the namespace a `\ref` resolves in. `\cref` is refused because
cleveref is not loaded (the contract writes kinds out; a `\cref` would compile
to "??"). `\term` marks a defined phrase for the index of defined terms, so it
belongs inside a definition's statement and is defined once per contract.
`\tref{<phrase>}` (or `\tref[<defined phrase>]{<text>}` for an inflected form)
links a use of a defined term to its definition, and must resolve: to the
phrase this contract defines, else to the one contract that defines it.
Without it a reader meets repository jargon ("virtual ensemble") pages before
its definition with nothing to click, and a link that resolves nowhere would
print as plain text unnoticed.
`\repodoc` names a repository file and must name one that exists outside the
history folders, which a contract may not cite. The `req` kind (a requirement
on the implementation, no proof) and the optional `prominence` field are part
of the format.

An assumption carries `verification` (`never` or `partly`): whether the
engine decides what a proof takes from it. Stated by hand in several places
per assumption (claim text, interface ledger, code constant, golden ledger,
the run record's hand lists), it would disagree between them; one header
field is the source, with the criterion "load-bearing clause unchecked"
(spec/claim-format.md section 3.2). This requires it on every assumption and
refuses it elsewhere, and the claim-closure table carries it to the run
record.

An assumption has four more header fields, each refused on other kinds:
`category` (the component it is about, from one vocabulary,
`ASSUMPTION_CATEGORIES`), `affects` (which of secrecy, correctness and
completeness its failure puts at stake), `refines` (the short id of the
assumption it narrows, so families are recorded once and rendered grouped)
and `user_statement` (a longer plain-text reading a user checks against
their setup, under the rules of a summary and at most 900 characters). The
key-rate report is built from these headers, so a value outside its
vocabulary, a `refines` that names nothing or closes a cycle, or a reading
with TeX in it would surface as a broken report rather than as a finding
here.

`user_statement` is optional on every other kind but a definition, there a
plain-text reading of the result for a user who is not a proof expert, what
it guarantees or warns about, in words; non-normative, the statement wins.
The key-rate report shows its security statement to QKD experimentalists
and certification labs, who cannot read technical summaries. That reading
must live with the claim, where a statement change is seen beside it, not in
run-tier code where it would go stale. The same plain-text rules and length
limit hold wherever it stands (`check_user_statement`); a definition is
refused one, since it asserts nothing a user relies on.

The assumption checks hold an assumption to one format. Each answers an error
class:

- Required fields: `category`, `affects` and `user_statement` are required on
  every assumption. The key-rate report is built from them, and an assumption
  without them renders a blank row.
- `verification` is `never` or `partly`; `decided` and `discharged` are
  refused (a condition the engine decides is a definition plus a requirement,
  and one a theorem discharges is a lemma). These two values would let such
  conditions stay assumptions.
- Body references (`check_assumption_body`): an assumption's lead-in and
  statement reference, by `\ref`, `\eqref` or `\xref`, only definitions,
  the assumption itself and the assumption its `refines` names. An assumption
  that lists its consumers and points at theorems cannot be checked without
  them, and editing a consumer changes what the assumption appears to say.
  `\tref` needs no rule: check 10 holds `\term` to a definition's statement,
  so a `\tref` always lands on a definition.
- `affects` against the graph (`check_affects`): an assumption in the
  assumption closure of a secrecy root lists `secrecy`, one in a correctness
  root's closure lists `correctness`, and one in a composition root's closure
  lists at least one of the two (so an assumption whose `affects` is
  `completeness` alone is in none of the three). `affects` is hand-written,
  and where the claim graph decides it, a disagreement would print a wrong
  "at stake" line in every report. Only that direction is checked: a device
  premise reaches the key length through the run's route, not through claim
  edges (A-SPEC and A-SEPARATE are in no root's closure yet put
  secrecy at stake), so the converse is not decidable here. The roots are
  `SECRECY_ROOTS`, `CORRECTNESS_ROOTS` and `COMPOSITION_ROOTS` of
  `certiqs_key.domain.claim_closure`, imported inside the check, as
  `generate_claim_closure` imports that module: one declaration, read by the
  run record and by this check, so the two cannot name different roots. A
  root that names no claim while its module is in the tree is an error, since
  a renamed root would otherwise switch the check off silently; a tree
  without the root's module (a test fixture) skips that root.
- Unused assumptions (`check_unused_assumptions`): every assumption is
  declared in some claim's `assumes`, or refined by an assumption that is
  used. An undeclared assumption is in no closure and no report, yet reads
  as a premise in the contract (A-BLOCK).

An assumption may carry `presupposes`, and a role word in its plain texts
needs it (check 14, `check_role_words`). The error class: a plain text that
presupposes a role the run lacks. A key-rate report for an entanglement-based
run with an untrusted source and no probe would speak of "her source", "her
laser", "your source prepares" and "Bob's probe", because "Alice" means the
sender in most premise texts and a party's role in the formal model.
`presupposes` lists, from `ASSUMPTION_PRESUPPOSITIONS`, the roles a run must
have for the text to hold, and every sentence of the title, summary or
`user_statement` that names a role of `ROLE_WORDS` either has a `presupposes`
entry satisfying it or is conditioned (`CONDITION_WORDS`). This makes the
class detectable by form; whether the field is right is still the reviewer's.
The claim-closure table carries the field, so a run-tier guard can refuse a
run that engages a premise its roles do not satisfy. There is no `scope`
field: the run-tier rows already name the station or party they are emitted
for, and a header repeating that would drift from the emitters. The category
`laboratory` (a party's laboratory and its boundary with the channel and the
public messages) belongs to the vocabulary.

`--dependents`, `--assumptions` and `--effective` accept a short id
wherever they accept a claim id: assumptions are named by short id in code,
run records and conversation.

A definition's `assumes` is empty (check 4). "A definition asserts nothing
that could be false" (spec/style.md section 2), and since an assumption may
use definitions, a premise declared on a definition would let an assumption
reach itself through it, and would put that premise in the closure of every
claim using the definition. A premise sits on the claims that consume it, so
an assumption's closure is its own; a `fact` keeps its `assumes`, which holds
its hypotheses (spec/claim-format.md section 4.1).

The presentation rules of the format (`harness/check_presentation.py`,
which says why each one exists) run in every run (spec/claim-format.md
section 6). Three rules are among the checks proper: a header
carries no `origin` field (an unknown field, check 1: where text came from is
git's record), the claim environment carries no bracketed title (check 2: a
second title can drift from the header's, so the heading a reader sees
differs from the one the index, the bookmarks and the graphs show), and a
summary or abstract uses only the mapped Unicode set (checks 0 and 1: an
unmapped character does not render in the PDF).

The separation rules (check 13; exact checks plus targeted fixes, heuristics
never a tax) keep apart what a contract asserts, what it points at and what
binds code. Each answers an error class:

- `statement-ref-kind`: the statement of a result, definition, assumption or
  fact references no remark, requirement or example. A statement that points
  at claims it does not rest on leaves a reader unable to tell a hypothesis
  from a pointer (`spec/style.md` section 3.4).
- `uses-kind`: no result or definition lists a remark or a requirement in
  `uses`. Otherwise results rest on remarks, so arguments nobody has stated as
  a lemma, and no verifier has reviewed as one, sit in the proof closure of
  main results.
- `remark-implements`: a remark carries no `implements`, and neither a remark
  nor an example is `implemented`. Engine bindings belong to a requirement or
  a result; a remark is mathematics about mathematics and has no code.
- `mention-referenced`: every `mentions` entry is referenced in the body (a
  `\ref` or `\eqref` to a label it defines, or an `\xref`). `mentions` is a
  hand-kept list and drifts into entries naming claims the body never
  points at; with check 6 the field is exact in both directions.

The four rules are errors of every run. A finding renders as
`path:line: separation[<rule>]: message`.

Heuristics stay out of the checks: `--advice` prints the editorial
heuristics of `harness/check_advice.py` (long statements, statement
and proof references to claims only mentioned, headed paragraphs, second
tracks, inventory sentences), which says why each exists. It is imported only
under the flag, never changes the exit code and keeps no waiver list: a
warning must not become a productivity tax.

Usage:
    python -m harness.check_claims [--repo .] [--module <id>]
    python -m harness.check_claims --advice [--module <id>] [--rule <name>]
    python -m harness.check_claims --graph out.dot
    python -m harness.check_claims --dependents meat-core/def:homog
    python -m harness.check_claims --dependents A-ATK
    python -m harness.check_claims --assumptions meat-core/thm:constrained-accumulation
    python -m harness.check_claims --status
    python -m harness.check_claims --effective protocol-compiler/thm:gates

Exit code 1 on any error. Beyond the checks of `spec/claim-format.md` §6 it
validates `module.yaml` itself (check 0 below), because every other check and
the assembler read it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from harness.contract_navigation import (
    KIND_WORD,
    LINK_RE,
    SHORT_ID_LINK_RE,
    LinkTarget,
    Resolver,
    link_key,
    plain_sentences,
    plain_title,
    unmapped_characters,
)

KIND_ENV: dict[str, str] = {
    "thm": "theorem",
    "lem": "lemma",
    "prop": "proposition",
    "cor": "corollary",
    "def": "definition",
    "ass": "assumption",
    "rem": "remark",
    "ex": "example",
    "fact": "fact",
    "req": "requirement",
}
ENV_KIND: dict[str, str] = {env: kind for kind, env in KIND_ENV.items()}
PROOF_KINDS = frozenset({"thm", "lem", "prop", "cor"})
STATUSES = ("draft", "verified", "accepted", "implemented", "superseded")
SETTLED = ("verified", "accepted", "implemented")
# The ladder the effective status is a minimum over. `superseded` sits below
# `draft`: a claim resting on a superseded statement is less settled than one
# resting on a draft, not exempt from the question (see the module docstring).
STATUS_LADDER = ("superseded", "draft", "verified", "accepted", "implemented")
PROVENANCES = ("published", "newly-derived")
PROMINENCES = ("main", "standard", "technical")
NOT_MAIN_KINDS = frozenset({"rem", "ex"})
REQUIRED_HEADER = ("id", "kind", "title", "status", "uses", "assumes", "refs",
                   "provenance")
#: The header fields an assumption may carry for the key-rate report and for
#: its readers (spec/claim-format.md section 3), and the roles its text presupposes.
#: Refused on every other kind.
ASSUMPTION_FIELDS = ("category", "affects", "refines", "presupposes")
#: The kinds that may not carry a ``user_statement``: it is required on an
#: assumption and optional on every other kind but a definition, which
#: asserts nothing a user relies on.
USER_STATEMENT_REFUSED_KINDS = frozenset({"def"})
KNOWN_HEADER = frozenset(REQUIRED_HEADER) | {
    "mentions", "pending", "short_id", "implements", "lean",
    "supersedes", "notes", "summary", "prominence", "verification",
    "user_statement", *ASSUMPTION_FIELDS,
}
#: Whether the engine decides what a proof takes from an assumption
#: (spec/claim-format.md section 3.2); the run record's never-verified marks
#: are ``never``. An assumption is an unchecked premise, so these two are the
#: values it may carry.
ASSUMPTION_VERIFICATIONS = ("never", "partly")
#: The refused values, each with where such a condition goes instead. Neither
#: the renderer's sentences, the closure table nor the package's vocabulary
#: knows them.
REFUSED_VERIFICATIONS: dict[str, str] = {
    "decided": "a condition the engine decides is a definition plus a requirement",
    "discharged": "a condition a theorem discharges is a lemma",
}
#: The component of the protocol or the analysis an assumption is about, one
#: per assumption. The one
#: vocabulary: extend it here, and the renderers and the report follow; its
#: order is the order the front-matter assumption table groups by.
#: ``laboratory``: a party's laboratory,
#: its boundary with the quantum channel and the public messages.
ASSUMPTION_CATEGORIES = (
    "source", "receiver", "laboratory", "channel-and-adversary",
    "protocol-structure", "local-randomness", "post-processing", "honest-model",
    "supplied-artefact", "numerical-trust",
)
#: What an assumption's failure puts at stake: a non-empty subset, without repeats.
AFFECTS = ("secrecy", "correctness", "completeness")
#: The roles a run must have for an assumption's text to hold, its optional
#: ``presupposes`` list (spec/claim-format.md section 3). Absent means none. The
#: run-tier rows already name the
#: station or party they are emitted for, so a role is read there and the
#: header carries no scope of its own.
ASSUMPTION_PRESUPPOSITIONS = (
    "trusted-source",  # the run is in trusted-source mode
    "sends",           # a party's laboratory holds a trusted source whose emission
                       # enters the proof (trusted mode and d_A >= 2): at the
                       # emitting row's party where it names one, else some party
    "setting",         # a private per-round setting with at least two values
                       # exists at the station (at the row's station; at party or
                       # run level, at some station)
    "letters",         # the declaration's letter alphabet X has at least two letters
)
#: THE ROLE WORDS OF AN ASSUMPTION'S PLAIN TEXTS (``check_role_words``): per
#: role group, the presuppositions that satisfy it and the words and phrases
#: that name it (each a regular expression), matched whole-word and
#: case-insensitively, a space matching any run of whitespace and an
#: apostrophe either form. Tuned so that every
#: sentence it catches does presuppose the role; it is a form check and sees
#: only the words it lists. Left out, each for a reason:
#: ``send``/``sends``, which name the public messages every party sends as
#: often as quantum signals (A-CONFORM); ``emit``/``emits``, which name what
#: the engine and its modules emit (A-CONST, A-SPEC), a measurement's outcome
#: (A-MEAS) and a detector's back-flash (A-LAB), so only "source emits"
#: and "the physical source" stand for them; ``prepare`` inside the protocol
#: class "prepare-and-measure", which names no party's role; and a bare
#: ``probe``, since the receiver's probe declaration exists on every receiver
#: (vacuum only where none is declared, receiver/def:probe) and its settings,
#: states and mean photon numbers (A-EXACT, A-NOSEL, A-ROUND, A-TRUST, A-RECV)
#: are vacuous without a probe rather than false, so only a party's probe
#: ("Bob's probe", "his probe") presupposes one.
ROLE_WORDS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "sender": (("sends", "trusted-source"), (
        "laser", "lasers", "modulator", "modulators",
        "prepare(?!-and-measure)", "prepares", "prepared", "preparation",
        "Trojan", "her source", "his source", "your source", "Alice's source",
        "Bob's source", "the same source", "the physical source", "source emits",
        "from Alice to Bob",
    )),
    "setting": (("setting",), (
        "private setting", "private settings", "Bob's probe", "Alice's probe",
        "his probe", "her probe",
    )),
}
#: The words and phrases that condition a sentence, so that a role word in it
#: needs no ``presupposes``: the conditional conjunctions, a restrictive
#: ``whose`` ("a choice whose probabilities depend on his private setting",
#: A-COIN), and the two phrases that condition on the source mode itself
#: (A-SEED: "With a trusted source, ...", "in trusted-source mode ...").
CONDITION_WORDS = ("where", "if", "when", "whenever", "unless", "whose",
                   "with a trusted source", "in trusted-source mode")


def words_re(words: tuple[str, ...]) -> re.Pattern[str]:
    """Return one pattern for whole-word, case-insensitive role or condition words."""
    alternatives = "|".join(word.replace("'", "['\N{RIGHT SINGLE QUOTATION MARK}]")
                            .replace(" ", r"\s+") for word in words)
    return re.compile(r"(?<![\w-])(?:" + alternatives + r")(?!\w)", re.IGNORECASE)


ROLE_WORD_RES: dict[str, re.Pattern[str]] = {
    group: words_re(words) for group, (_roles, words) in ROLE_WORDS.items()}
CONDITION_RE = words_re(CONDITION_WORDS)
#: The assumption fields required on every assumption (``refines`` is optional).
ASSUMPTION_FIELDS_REQUIRED = ("category", "affects", "user_statement")
#: The longest ``user_statement`` as rendered (a link counted as "Kind 0.0").
USER_STATEMENT_CHARACTERS = 900
#: The separation rules (check 13, spec/claim-format.md section 6), each an
#: error of every run, with the property each checks; the module docstring
#: says why. A finding names its rule as ``separation[<rule>]``.
SEPARATION_RULES: dict[str, str] = {
    "statement-ref-kind": "a statement of a result, definition, assumption or fact "
                          "references no remark, requirement or example",
    "uses-kind": "no result or definition uses a remark or a requirement",
    "remark-implements": "a remark carries no implements; no remark or example is "
                         "implemented",
    "mention-referenced": "every mentions entry is referenced in the body",
}
#: Kinds whose statement references no remark, requirement or example.
STATEMENT_REF_KINDS = frozenset({"thm", "lem", "prop", "cor", "def", "ass", "fact"})
#: Kinds a statement of ``STATEMENT_REF_KINDS`` does not point at.
POINTER_KINDS = frozenset({"rem", "req", "ex"})
#: Kinds that list no remark or requirement in ``uses`` (``ass`` and ``fact``
#: use only definitions, check 4; an example is refused for every kind).
USES_KIND_CITERS = frozenset({"thm", "lem", "prop", "cor", "def"})
REQUIRED_MODULE = ("id", "kind", "version", "title", "order")
SHORT_ID_RE = re.compile(r"^A-[A-Z0-9][A-Z0-9-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ENV_BEGIN_RE = re.compile(r"\\begin\{(" + "|".join(ENV_KIND) + r")\}")
PROOF_RE = re.compile(r"\\begin\{proof\}(\[[^\]]*\])?")
LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
REF_RE = re.compile(r"\\(?:ref|cref|Cref|eqref)\{([^}]*)\}")
CITE_RE = re.compile(r"\\cite(\[[^\]]*\])?\{([^}]*)\}")
FORBIDDEN_RE = re.compile(
    r"\\(section|subsection|subsubsection|chapter|part|input|include"
    r"|documentclass|usepackage|begin\{document\})(?![A-Za-z])"
)   # the lookahead: \partial is not \part
XREF_RE = re.compile(r"\\xref\{([^}]*)\}")
TERM_RE = re.compile(r"\\term(?:\[[^\[\]{}]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}")
#: ``\term[gloss]{phrase}``: group 1 the one-line gloss (optional), group 2 the phrase.
TERM_GLOSS_RE = re.compile(
    r"\\term(?:\[([^\[\]{}]*)\])?\{((?:[^{}]|\{[^{}]*\})*)\}")
#: ``\tref[defined phrase]{text}``: group 1 the phrase if the text inflects it.
TREF_RE = re.compile(r"\\tref(?:\[([^\[\]{}]*)\])?\{((?:[^{}]|\{[^{}]*\})*)\}")
REPODOC_RE = re.compile(r"\\repodoc\{([^}]*)\}")
CREF_RE = re.compile(r"\\(cref|Cref|crefrange|Crefrange|cpageref|Cpageref|labelcref"
                     r"|namecref|nameCref)(?![A-Za-z])")
REPODOC_PATH_RE = re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$")
REPODOC_ANCHOR_RE = re.compile(r"^[A-Za-z0-9._-]*$")
#: Repository folders a contract never cites: history and working notes.
NOT_CITABLE_DIRS = ("reports", "state", "tmp", "context")
STATUS_COLOUR: dict[str, str] = {
    "draft": "#f4f4f4",
    "verified": "#d7e8fb",
    "accepted": "#cfead0",
    "implemented": "#a9d6ab",
    "superseded": "#e2e2e2",
}


class ClaimFormatError(Exception):
    """A claim file cannot be parsed far enough to be checked."""

    def __init__(self, line: int, message: str) -> None:
        """Record the 1-based line and the message to report."""
        super().__init__(message)
        self.line = line
        self.message = message


@dataclass(frozen=True, order=True)
class Error:
    """One finding, rendered as ``path:line: message``."""

    path: str
    line: int
    message: str
    module: str = ""
    rule: str = ""      # the separation rule of a check-13 finding, else ""

    def render(self) -> str:
        """Return the one-line rendering used on stdout."""
        return f"{self.path}:{self.line}: {self.message}"


@dataclass
class Module:
    """One core module or submodule, as read from its ``module.yaml``."""

    module_id: str
    kind: str
    path: Path
    rel: str
    meta: dict[str, Any]
    lines: list[str]
    parent: str | None = None
    depends_on: list[str] = field(default_factory=list)
    order: list[str] = field(default_factory=list)
    submodules: list[str] = field(default_factory=list)


@dataclass
class Claim:
    """One claim file: its header, its body and what the body references."""

    claim_id: str
    module_id: str
    label: str
    kind: str
    status: str
    path: Path
    rel: str
    lines: list[str]
    header: dict[str, Any]
    body: str
    body_start: int
    uses: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    assumes: list[str] = field(default_factory=list)
    own_labels: set[str] = field(default_factory=set)
    refs_seen: list[tuple[str, int]] = field(default_factory=list)
    resolved_uses: list[str] = field(default_factory=list)
    resolved_mentions: list[str] = field(default_factory=list)

    def line_of(self, field_name: str) -> int:
        """Return the file line of a header field, or 1 if it is absent."""
        return field_line(self.lines, field_name)

    def line_at(self, body: str, offset: int) -> int:
        """Return the file line of a character offset into the body."""
        return self.body_start + body[:offset].count("\n")


def contract_of(module_or_claim_id: str) -> str:
    r"""Return the core module whose assembled contract holds a module or claim.

    A contract is a core and its submodules; it is the namespace in which a
    ``\ref`` resolves and a ``\label`` must be unique.
    """
    return module_or_claim_id.split("/", 1)[0]


def a_kind(kind: str) -> str:
    """Return a claim kind as a noun with its article: "a remark", "an example"."""
    word = KIND_WORD.get(kind, "claim").lower()
    return f"{'an' if word[0] in 'aeiou' else 'a'} {word}"


def field_line(lines: list[str], name: str, default: int = 1) -> int:
    """Return the 1-based line on which a YAML key appears, else ``default``."""
    pattern = re.compile(r"^\s*%?\s*" + re.escape(name) + r"\s*:")
    for number, text in enumerate(lines, start=1):
        if pattern.match(text):
            return number
    return default


def strip_comments(text: str) -> str:
    """Blank out LaTeX comments, preserving every line and column position."""
    out: list[str] = []
    for line in text.split("\n"):
        index = 0
        while index < len(line):
            char = line[index]
            if char == "\\":
                index += 2
                continue
            if char == "%":
                line = line[:index] + " " * (len(line) - index)
                break
            index += 1
        out.append(line)
    return "\n".join(out)


def split_header(text: str) -> tuple[str, str, int]:
    """Split a claim file into its ``% ---`` header text, body and body line.

    Raises ``ClaimFormatError`` when the file does not open with a header
    block delimited by two ``% ---`` lines.
    """
    lines = text.split("\n")
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start >= len(lines) or lines[start].strip() != "% ---":
        raise ClaimFormatError(start + 1, "file does not start with a '% ---' header")
    header: list[str] = []
    index = start + 1
    while index < len(lines) and lines[index].strip() != "% ---":
        stripped = lines[index].lstrip()
        if not stripped.startswith("%"):
            raise ClaimFormatError(
                index + 1, "non-comment line inside the '% ---' header block"
            )
        content = stripped[1:]
        header.append(content[1:] if content.startswith(" ") else content)
        index += 1
    if index >= len(lines):
        raise ClaimFormatError(start + 1, "header block is not closed by '% ---'")
    body = "\n".join(lines[index + 1 :])
    return "\n".join(header), body, index + 2


def load_yaml_mapping(text: str) -> dict[str, Any]:
    """Parse YAML text that must be a mapping, raising on anything else."""
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ClaimFormatError(1, f"header is not valid YAML: {exc}") from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ClaimFormatError(1, "header does not parse as a YAML mapping")
    return {str(key): value for key, value in raw.items()}


def as_list(value: Any, name: str, line: int, errors_out: list[str]) -> list[str]:
    """Coerce a header field to a list of strings, recording a problem if not."""
    if value is None:
        return []
    if not isinstance(value, list):
        errors_out.append(f"{name}: must be a list (line {line})")
        return []
    return [str(item) for item in value]


def rel_path(repo: Path, path: Path) -> str:
    """Return a repo-relative path with forward slashes, for messages."""
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


@dataclass
class Repo:
    """Everything the checks read: modules, claims and the reference index."""

    root: Path
    modules: dict[str, Module] = field(default_factory=dict)
    claims: dict[str, Claim] = field(default_factory=dict)
    ref_ids: set[str] = field(default_factory=set)
    bibtex_keys: set[str] = field(default_factory=set)
    assumptions: dict[str, Claim] = field(default_factory=dict)
    errors: list[Error] = field(default_factory=list)
    known_labels: set[str] | None = None
    owners_cache: dict[tuple[str, str], str] | None = field(default=None, repr=False)
    terms_cache: dict[tuple[str, str], DefinedTerm] | None = field(
        default=None, repr=False)

    def separation(self, claim: Claim, line: int, rule: str, message: str) -> None:
        """Record an error of a separation rule (check 13), naming the rule."""
        self.errors.append(Error(claim.rel, line, f"separation[{rule}]: {message}",
                                 claim.module_id, rule))

    def error(self, path: Path | str, line: int, message: str,
              module: str = "") -> None:
        """Record one finding."""
        text = path if isinstance(path, str) else rel_path(self.root, path)
        self.errors.append(Error(text, line, message, module))

    def at(self, claim: Claim, line: int, message: str) -> None:
        """Record a finding at a body line of a claim file."""
        self.errors.append(Error(claim.rel, line, message, claim.module_id))

    def at_field(self, claim: Claim, name: str, message: str) -> None:
        """Record a finding at the header field ``name`` of a claim file."""
        self.at(claim, claim.line_of(name), message)


def load_reference_index(repo: Repo) -> None:
    """Read ``refs/index.json``: the citable universe and its bibtex keys."""
    index_path = repo.root / "refs" / "index.json"
    if not index_path.is_file():
        repo.error("refs/index.json", 1, "reference index not found")
        return
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        repo.error("refs/index.json", 1, f"cannot read reference index: {exc}")
        return
    entries = data.get("entries", []) if isinstance(data, dict) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        ref_id = str(entry.get("ref_id", ""))
        if not ref_id:
            continue
        repo.ref_ids.add(ref_id)
        repo.bibtex_keys.add(str(entry.get("bibtex_key") or ref_id))


def check_plain_summary(value: Any, field_name: str) -> None:
    """Reject empty or TeX-bearing explanations shared by PDF and Markdown.

    A non-ASCII character must come from the mapped set of
    ``contract_navigation.UNICODE_TEX``, which says how the PDF renders it.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonempty plain text")
    if "\\" in value or "$" in value:
        raise ValueError(f"{field_name} must be plain text "
                         "(no backslash or dollar sign)")
    unmapped = unmapped_characters(value)
    if unmapped:
        shown = ", ".join(f"U+{ord(char):04X}" for char in unmapped)
        raise ValueError(f"{field_name} carries {shown}, outside the mapped Unicode "
                         "set of harness/contract_navigation.py (UNICODE_TEX); add "
                         "the character there with the TeX that renders it")


def group_abstract(meta: dict[str, Any], start: str) -> str:
    """Read an optional abstract by its existing anchor, without another partition."""
    for group in meta.get("reading_groups") or []:
        if group["start"] == start:
            return str(group.get("abstract", ""))
    return ""


def reading_groups(meta: dict[str, Any]) -> list[tuple[str, list[str]]]:
    """Partition order at validated group anchors; default to one claims group."""
    order = [str(label) for label in meta.get("order", []) or []]
    groups = meta.get("reading_groups")
    if groups is None or groups == []:
        return [("Claims", order)] if order else []
    if not isinstance(groups, list):
        raise ValueError("reading_groups must be a list of {title, start} mappings")
    starts: list[int] = []
    titles: list[str] = []
    for group in groups:
        if (not isinstance(group, dict) or not {"title", "start"} <= set(group)
                or set(group) - {"title", "start", "abstract"}):
            raise ValueError("reading_groups entries need title and start, "
                             "with an optional abstract")
        if "abstract" in group:
            check_plain_summary(group["abstract"], "reading_groups abstract")
        title, start = group["title"], group["start"]
        if not isinstance(title, str) or not title.strip():
            raise ValueError("reading_groups title must be nonempty text")
        if start not in order:
            raise ValueError(f"reading_groups start '{start}' is not in order")
        position = order.index(start)
        if starts and position <= starts[-1]:
            raise ValueError("reading_groups starts must be unique and follow order")
        starts.append(position)
        titles.append(title)
    if starts[0] != 0:
        raise ValueError("reading_groups must start at the first claim in order")
    ends = [*starts[1:], len(order)]
    return [(title, order[start:end])
            for title, start, end in zip(titles, starts, ends, strict=True)]


def read_module(repo: Repo, path: Path, module_id: str,
                parent: str | None) -> Module | None:
    """Read and structurally validate one ``module.yaml`` (check 0)."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    try:
        meta = load_yaml_mapping(text)
    except ClaimFormatError as exc:
        repo.error(path, exc.line, exc.message, module_id)
        return None
    module = Module(
        module_id=module_id,
        kind=str(meta.get("kind", "")),
        path=path.parent,
        rel=rel_path(repo.root, path),
        meta=meta,
        lines=lines,
        parent=parent,
    )
    for name in REQUIRED_MODULE:
        if name not in meta:
            repo.error(path, 1, f"module.yaml: required field '{name}' is missing",
                       module_id)
    expected_id = module_id.split("/")[-1]
    declared = str(meta.get("id", ""))
    if declared not in {expected_id, module_id}:
        repo.error(path, field_line(lines, "id"),
                   f"module.yaml: id '{declared}' does not match the directory "
                   f"'{expected_id}'", module_id)
    want_kind = "submodule" if parent else "core"
    if module.kind != want_kind:
        repo.error(path, field_line(lines, "kind"),
                   f"module.yaml: kind '{module.kind}' should be '{want_kind}' at "
                   "this depth", module_id)
    problems: list[str] = []
    module.depends_on = as_list(meta.get("depends_on"), "depends_on",
                                field_line(lines, "depends_on"), problems)
    module.order = as_list(meta.get("order"), "order",
                           field_line(lines, "order"), problems)
    module.submodules = as_list(meta.get("submodules"), "submodules",
                                field_line(lines, "submodules"), problems)
    try:
        if "abstract" in meta:
            check_plain_summary(meta["abstract"], "abstract")
        reading_groups({**meta, "order": module.order})
    except ValueError as exc:
        problems.append(str(exc))
    for problem in problems:
        repo.error(path, 1, f"module.yaml: {problem}", module_id)
    return module


def discover_modules(repo: Repo) -> None:
    """Walk ``spec/modules/`` for core modules and one level of submodules."""
    root = repo.root / "spec" / "modules"
    if not root.is_dir():
        repo.error("spec/modules", 1, "no spec/modules directory found")
        return
    for core_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        meta_path = core_dir / "module.yaml"
        if not meta_path.is_file():
            repo.error(rel_path(repo.root, core_dir), 1,
                       "module directory has no module.yaml")
            continue
        core = read_module(repo, meta_path, core_dir.name, None)
        if core is None:
            continue
        repo.modules[core.module_id] = core
        for sub_dir in sorted(p for p in core_dir.iterdir() if p.is_dir()):
            sub_meta = sub_dir / "module.yaml"
            if not sub_meta.is_file():
                continue
            sub_id = f"{core.module_id}/{sub_dir.name}"
            sub = read_module(repo, sub_meta, sub_id, core.module_id)
            if sub is None:
                continue
            repo.modules[sub_id] = sub
            for deeper in sorted(p for p in sub_dir.iterdir() if p.is_dir()):
                if (deeper / "module.yaml").is_file():
                    repo.error(deeper / "module.yaml", 1,
                               "a submodule may not contain a further module",
                               sub_id)


def check_sibling_dependencies(repo: Repo) -> None:
    """Check 0b: a submodule's ``depends_on`` names siblings or foreign modules.

    A submodule may extend
    a sibling (compose the instance the sibling builds), named
    by its bare name, or lean on another core's module or submodule (the
    weight route of wpfss consumes the receiver's detector-imperfections and
    probe-conditioning results), named by its full id. A sibling edge must
    point at an existing sibling and the sibling graph must be acyclic, so
    that a submodule can be deleted together with everything that depends on
    it and nothing else; a foreign edge must name an existing module outside
    the submodule's own core.
    """
    for module_id in sorted(repo.modules):
        module = repo.modules[module_id]
        if not module.parent:
            continue
        own = module_id.rsplit("/", 1)[1]
        for entry in module.depends_on:
            sibling_id = f"{module.parent}/{entry}"
            is_sibling = entry != own and sibling_id in repo.modules
            is_foreign = (entry in repo.modules and entry != module.parent
                          and not entry.startswith(f"{module.parent}/"))
            if not (is_sibling or is_foreign):
                repo.error(module.path / "module.yaml",
                           field_line(module.lines, "depends_on"),
                           f"module.yaml: depends_on '{entry}' is not a sibling "
                           f"submodule of {module.parent} nor the id of another "
                           "core's module (a submodule inherits its core's "
                           "depends_on and may add those two kinds only)",
                           module_id)
    # cycles among siblings, per core
    for core_id in sorted(m for m in repo.modules if "/" not in m):
        siblings = {m.rsplit("/", 1)[1]: m for m in repo.modules
                    if m.startswith(f"{core_id}/")}
        state: dict[str, int] = {}
        for name in sorted(siblings):
            _visit_sibling(repo, siblings, state, name, [])


def _visit_sibling(repo: Repo, siblings: dict[str, str], state: dict[str, int],
                   name: str, trail: list[str]) -> None:
    """Depth-first walk of one core's sibling graph; a back edge is a cycle."""
    if state.get(name) == 2:
        return
    if state.get(name) == 1:
        cycle = [*trail[trail.index(name):], name]
        module = repo.modules[siblings[name]]
        repo.error(module.path / "module.yaml", field_line(module.lines, "depends_on"),
                   "module.yaml: sibling depends_on cycle " + " -> ".join(cycle),
                   siblings[name])
        return
    state[name] = 1
    for entry in repo.modules[siblings[name]].depends_on:
        if entry in siblings:
            _visit_sibling(repo, siblings, state, entry, [*trail, name])
    state[name] = 2


def scan_body(claim: Claim) -> None:
    """Collect labels, references and the environment facts of a claim body."""
    body = strip_comments(claim.body)
    claim.own_labels = {match.group(1) for match in LABEL_RE.finditer(body)}
    for match in REF_RE.finditer(body):
        line = claim.body_start + body[: match.start()].count("\n")
        for target in match.group(1).split(","):
            stripped = target.strip()
            if stripped:
                claim.refs_seen.append((stripped, line))


def read_claim(repo: Repo, module: Module, path: Path) -> Claim | None:
    """Read one claim file's header and body; header checks run separately."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    try:
        header_text, body, body_start = split_header(text)
        header = load_yaml_mapping(header_text)
    except ClaimFormatError as exc:
        repo.error(path, exc.line, exc.message, module.module_id)
        return None
    label = path.stem.replace("-", ":", 1)
    claim = Claim(
        claim_id=f"{module.module_id}/{label}",
        module_id=module.module_id,
        label=label,
        kind=str(header.get("kind", "")),
        status=str(header.get("status", "")),
        path=path,
        rel=rel_path(repo.root, path),
        lines=lines,
        header=header,
        body=body,
        body_start=body_start,
    )
    problems: list[str] = []
    claim.uses = as_list(header.get("uses"), "uses", claim.line_of("uses"), problems)
    claim.mentions = as_list(header.get("mentions"), "mentions",
                             claim.line_of("mentions"), problems)
    claim.pending = as_list(header.get("pending"), "pending",
                            claim.line_of("pending"), problems)
    claim.assumes = as_list(header.get("assumes"), "assumes",
                            claim.line_of("assumes"), problems)
    for problem in problems:
        repo.error(path, 1, problem, module.module_id)
    scan_body(claim)
    return claim


def load_claims(repo: Repo) -> None:
    """Read every claim file of every discovered module."""
    for module in repo.modules.values():
        claims_dir = module.path / "claims"
        if not claims_dir.is_dir():
            repo.error(module.rel, 1, "module has no claims/ directory",
                       module.module_id)
            continue
        for path in sorted(claims_dir.glob("*.tex")):
            stem = path.stem
            if "-" not in stem:
                repo.error(path, 1,
                           "file name must be '<kind>-<slug>.tex'", module.module_id)
                continue
            kind, slug = stem.split("-", 1)
            if kind not in KIND_ENV or not SLUG_RE.match(slug):
                repo.error(path, 1,
                           f"file name '{path.name}' is not '<kind>-<slug>.tex' with "
                           f"kind in {', '.join(KIND_ENV)}", module.module_id)
                continue
            claim = read_claim(repo, module, path)
            if claim is None:
                continue
            if claim.claim_id in repo.claims:
                repo.error(path, 1, f"duplicate claim id '{claim.claim_id}'",
                           module.module_id)
                continue
            repo.claims[claim.claim_id] = claim


def check_header(repo: Repo, claim: Claim) -> None:
    """Check 1: required fields, vocabularies, provenance/refs consistency."""
    header = claim.header
    for name in REQUIRED_HEADER:
        if name not in header:
            repo.at(claim, 1, f"header: required field '{name}' is missing")
    for name in header:
        if name not in KNOWN_HEADER:
            repo.at_field(claim, name, f"header: unknown field '{name}'")
    if claim.kind and claim.kind not in KIND_ENV:
        repo.at_field(claim, "kind", f"header: kind '{claim.kind}' is not one of "
                      f"{', '.join(KIND_ENV)}")
    if claim.status and claim.status not in STATUSES:
        repo.at_field(claim, "status", f"header: status '{claim.status}' is not "
                      f"one of {', '.join(STATUSES)}")
    if not str(header.get("title", "")).strip():
        repo.at_field(claim, "title", "header: title is empty")
    if "summary" in header:
        try:
            check_plain_summary(header["summary"], "summary")
        except ValueError as exc:
            repo.at_field(claim, "summary", f"header: {exc}")
    provenance = str(header.get("provenance", ""))
    if provenance and provenance not in PROVENANCES:
        repo.at_field(claim, "provenance", f"header: provenance '{provenance}' is "
                      f"not one of {', '.join(PROVENANCES)}")
    if provenance == "published" and not (header.get("refs") or []):
        repo.at_field(claim, "provenance", "header: provenance 'published' "
                      "requires a non-empty refs list")
    if claim.kind == "fact" and provenance and provenance != "published":
        repo.at_field(claim, "provenance", "header: a fact is an imported result "
                      "and must have provenance 'published' (with refs)")
    short_id = header.get("short_id")
    if claim.kind == "ass":
        if short_id is None:
            repo.at(claim, 1, "header: an assumption requires a short_id 'A-...'")
        elif not SHORT_ID_RE.match(str(short_id)):
            repo.at_field(claim, "short_id", f"header: short_id '{short_id}' is "
                          "not of the form 'A-UPPERCASE'")
    elif short_id is not None:
        repo.at_field(claim, "short_id", "header: short_id is for assumptions only")
    verification = header.get("verification")
    if claim.kind == "ass":
        allowed = ", ".join(ASSUMPTION_VERIFICATIONS)
        if verification is None:
            repo.at(claim, 1, "header: an assumption requires a verification "
                    f"({allowed}; spec/claim-format.md section 3.2)")
        elif str(verification) in REFUSED_VERIFICATIONS:
            repo.at_field(claim, "verification", f"header: verification "
                          f"'{verification}' is refused on an assumption, which is "
                          f"an unchecked premise: "
                          f"{REFUSED_VERIFICATIONS[str(verification)]} "
                          "(spec/claim-format.md section 3.2)")
        elif str(verification) not in ASSUMPTION_VERIFICATIONS:
            repo.at_field(claim, "verification", f"header: verification "
                          f"'{verification}' is not one of {allowed}")
    elif verification is not None:
        repo.at_field(claim, "verification",
                      "header: verification is for assumptions only")
    check_assumption_fields(repo, claim)
    if header.get("implements") is not None and ":" not in str(header["implements"]):
        repo.at_field(claim, "implements",
                      "header: implements must read 'python.module.path:symbol'")
    if claim.kind == "rem" and header.get("implements"):
        tops = (", and its status then tops at 'accepted'"
                if claim.status == "implemented" else "")
        repo.separation(claim, claim.line_of("implements"), "remark-implements",
                        "a remark carries no implements (it is mathematics about "
                        "mathematics and has no code); the binding belongs to the "
                        "requirement, definition or result whose object the symbol "
                        f"computes{tops}")
    if "prominence" in header:
        prominence = str(header["prominence"])
        if prominence not in PROMINENCES:
            repo.at_field(claim, "prominence", f"header: prominence '{prominence}' "
                          f"is not one of {', '.join(PROMINENCES)}")
        elif prominence == "main" and claim.kind in NOT_MAIN_KINDS:
            repo.at_field(claim, "prominence", "header: a remark or an example is "
                          "never a main result; use prominence standard or technical")


def rendered_plain_text(repo: Repo, module_id: str, text: str) -> str:
    """Return a plain-text field as a reader sees it: a link as "Kind 0.0".

    A link to an assumption reads as its short id; a link that resolves to
    nothing stays as written (check 12 reports it). The length rules of
    summaries and of ``user_statement`` measure this text.
    """
    def link(match: re.Match[str]) -> str:
        target = link_target(repo, module_id, match.group(1))
        if target is None:
            return match.group(0)
        return target.short_id or f"{KIND_WORD.get(target.kind, 'Claim')} 0.0"
    return " ".join(LINK_RE.sub(link, text).split())


def check_user_statement(repo: Repo, claim: Claim) -> None:
    """Check 1 (continued): a ``user_statement`` is plain text of bounded length.

    Required on an assumption (``check_assumption_fields``), optional on every
    other kind but a definition (``USER_STATEMENT_REFUSED_KINDS``), where it
    is refused; wherever it stands it obeys the rules of a summary and has at
    most ``USER_STATEMENT_CHARACTERS`` characters as rendered.
    """
    if "user_statement" not in claim.header:
        return
    if claim.kind in USER_STATEMENT_REFUSED_KINDS:
        repo.at_field(claim, "user_statement", "header: a definition carries no "
                      "user_statement; it asserts nothing a user relies on "
                      "(spec/claim-format.md section 3)")
        return
    value = claim.header["user_statement"]
    try:
        check_plain_summary(value, "user_statement")
    except ValueError as exc:
        repo.at_field(claim, "user_statement", f"header: {exc}")
    else:
        shown = rendered_plain_text(repo, claim.module_id, str(value))
        if len(shown) > USER_STATEMENT_CHARACTERS:
            repo.at_field(claim, "user_statement",
                          f"header: user_statement has {len(shown)} characters "
                          f"as rendered (at most {USER_STATEMENT_CHARACTERS})")


def check_assumption_fields(repo: Repo, claim: Claim) -> None:
    """Check 1 (continued): the assumption fields of the key-rate report.

    ``category``, ``affects``, ``refines`` and ``presupposes`` are refused on
    every other kind; ``ASSUMPTION_FIELDS_REQUIRED`` are required on an
    assumption (``refines`` and ``presupposes`` are optional). A
    ``user_statement`` is checked wherever it stands (``check_user_statement``).
    That ``refines`` resolves and is acyclic is ``check_refines``; that
    ``affects`` agrees with the claim graph is ``check_affects``; that a role
    word of the plain texts is presupposed or conditioned is
    ``check_role_words``.
    """
    header = claim.header
    check_user_statement(repo, claim)
    if claim.kind != "ass":
        for name in ASSUMPTION_FIELDS:
            if name in header:
                repo.at_field(claim, name, f"header: {name} is for assumptions only")
        return
    for name in ASSUMPTION_FIELDS_REQUIRED:
        if name not in header:
            repo.at(claim, 1, f"header: an assumption requires {name} "
                    "(spec/claim-format.md section 3)")
    if "category" in header:
        category = header["category"]
        if not isinstance(category, str) or category not in ASSUMPTION_CATEGORIES:
            repo.at_field(claim, "category", f"header: category '{category}' is not "
                          f"one of {', '.join(ASSUMPTION_CATEGORIES)}")
    if "affects" in header:
        affects = header["affects"]
        if not isinstance(affects, list) or not affects:
            repo.at_field(claim, "affects", "header: affects must be a non-empty "
                          f"list drawn from {', '.join(AFFECTS)}")
        else:
            for item in affects:
                if not isinstance(item, str) or item not in AFFECTS:
                    repo.at_field(claim, "affects", f"header: affects '{item}' is "
                                  f"not one of {', '.join(AFFECTS)}")
            repeated = sorted({str(item) for item in affects
                               if affects.count(item) > 1})
            for item in repeated:
                repo.at_field(claim, "affects",
                              f"header: affects lists '{item}' twice")
    if "refines" in header:
        refines = header["refines"]
        if not isinstance(refines, str) or not SHORT_ID_RE.match(refines):
            repo.at_field(claim, "refines", f"header: refines '{refines}' is not "
                          "an assumption short id 'A-UPPERCASE'")
    if "presupposes" in header:
        roles = header["presupposes"]
        allowed = ", ".join(ASSUMPTION_PRESUPPOSITIONS)
        if not isinstance(roles, list):
            repo.at_field(claim, "presupposes", "header: presupposes must be a list "
                          f"drawn from {allowed}")
        else:
            for item in roles:
                if not isinstance(item, str) or item not in ASSUMPTION_PRESUPPOSITIONS:
                    repo.at_field(claim, "presupposes", f"header: presupposes "
                                  f"'{item}' is not one of {allowed}")
            for item in sorted({str(item) for item in roles if roles.count(item) > 1}):
                repo.at_field(claim, "presupposes",
                              f"header: presupposes lists '{item}' twice")


def presupposed_roles(claim: Claim) -> list[str]:
    """Return an assumption's ``presupposes`` entries; absent or malformed is none."""
    roles = claim.header.get("presupposes")
    return [str(item) for item in roles] if isinstance(roles, list) else []


def shortened(sentence: str, start: int, end: int, width: int = 100) -> str:
    """Return ``sentence`` cut to about ``width`` characters around a match."""
    if len(sentence) <= width:
        return sentence
    left = max(0, start - (width - (end - start)) // 2)
    right = min(len(sentence), left + width)
    left = max(0, right - width)
    return (("..." if left else "") + sentence[left:right].strip()
            + ("..." if right < len(sentence) else ""))


def check_role_words(repo: Repo, claim: Claim) -> None:
    """Check 14: an assumption's role words are presupposed or conditioned.

    Each sentence of the title (one sentence), the ``summary`` and the
    ``user_statement``, as rendered, that names a role of ``ROLE_WORDS``
    needs a ``presupposes`` entry satisfying that role group or a condition
    word of ``CONDITION_WORDS``. The module docstring says why.
    """
    if claim.kind != "ass":
        return
    roles = set(presupposed_roles(claim))
    for name in ("title", "summary", "user_statement"):
        text = claim.header.get(name)
        if not isinstance(text, str) or not text.strip():
            continue
        sentences = ([plain_title(text)] if name == "title" else
                     plain_sentences(rendered_plain_text(repo, claim.module_id, text)))
        for sentence in sentences:
            if CONDITION_RE.search(sentence):
                continue
            for group, pattern in ROLE_WORD_RES.items():
                satisfying = ROLE_WORDS[group][0]
                match = pattern.search(sentence)
                if match is None or roles & set(satisfying):
                    continue
                shown = shortened(sentence, match.start(), match.end())
                repo.at_field(
                    claim, name,
                    f"presupposes: the {name} sentence \"{shown}\" uses the {group} "
                    f"word '{match.group(0)}' unconditioned; declare presupposes: "
                    f"[{' or '.join(satisfying)}] if the text needs that role, or "
                    f"condition the sentence ({', '.join(CONDITION_WORDS)}; "
                    "spec/claim-format.md section 3)")


def check_refines(repo: Repo) -> None:
    """Check 8b: ``refines`` names another assumption, and the families are acyclic.

    An assumption refines at most one other, so the refines graph is a set of
    chains; following each from its start either ends or meets itself.
    """
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        target = claim.header.get("refines")
        if claim.kind != "ass" or not isinstance(target, str) \
                or not SHORT_ID_RE.match(target):
            continue
        own = str(claim.header.get("short_id", "")).strip()
        if target == own:
            repo.at_field(claim, "refines",
                          f"refines: {own} refines itself")
            continue
        if target not in repo.assumptions:
            repo.at_field(claim, "refines",
                          f"refines: '{target}' names no assumption")
            continue
        trail = [own]
        node: str | None = target
        while node is not None and node not in trail:
            trail.append(node)
            nxt = repo.assumptions[node].header.get("refines") \
                if node in repo.assumptions else None
            node = nxt if isinstance(nxt, str) and nxt in repo.assumptions else None
        if node == own:
            repo.at_field(claim, "refines", "refines: cycle "
                          + " -> ".join([*trail, own]))


#: The module of the root tuples ``check_affects`` reads (imported inside it).
ROOTS_MODULE = "certiqs_key.domain.claim_closure"
#: Where those tuples live, for a finding about a root that names no claim.
ROOTS_SOURCE = "src/certiqs_key/domain/claim_closure.py"


def affects_roots() -> dict[str, tuple[str, ...]]:
    """Return the secrecy, correctness and composition roots, by property.

    Imported here rather than at the top: the run record reads the same
    tuples, so they have one declaration (``ROOTS_MODULE``), and only this
    check of the checker needs the package.
    """
    from certiqs_key.domain.claim_closure import (
        COMPOSITION_ROOTS,
        CORRECTNESS_ROOTS,
        SECRECY_ROOTS,
    )
    return {"secrecy": tuple(SECRECY_ROOTS), "correctness": tuple(CORRECTNESS_ROOTS),
            "composition": tuple(COMPOSITION_ROOTS)}


def check_affects(repo: Repo,
                  roots: dict[str, tuple[str, ...]] | None = None) -> None:
    """Check 8c: ``affects`` says what the claim graph says is at stake.

    For each root of ``roots`` (default: ``affects_roots()``), every assumption
    in its ``assumption_closure`` lists ``secrecy`` (a secrecy root),
    ``correctness`` (a correctness root), or at least one of the two (a
    composition root). An assumption whose ``affects`` is missing or malformed
    is skipped: check 1 reports it. A root that names no claim is an error
    when its module is in the tree, and skipped when it is not (a fixture).
    """
    wanted = affects_roots() if roots is None else roots
    for prop in ("secrecy", "correctness", "composition"):
        for root in wanted.get(prop, ()):
            if root not in repo.claims:
                if root.rsplit("/", 1)[0] in repo.modules:
                    repo.error(ROOTS_SOURCE, 1,
                               f"affects: the {prop} root '{root}' of "
                               f"{ROOTS_MODULE} names no claim, so the affects "
                               "check cannot read its closure; rename the root "
                               "with the claim")
                continue
            for short_id in assumption_closure(repo, root):
                owner = repo.assumptions.get(short_id)
                if owner is None:
                    continue        # check 8 reports an assumes naming nothing
                affects = owner.header.get("affects")
                if not isinstance(affects, list) or not affects:
                    continue        # check 1 reports a missing or malformed field
                listed = {str(item) for item in affects}
                if prop == "composition":
                    if listed & {"secrecy", "correctness"}:
                        continue
                    needed = "secrecy or correctness"
                elif prop in listed:
                    continue
                else:
                    needed = prop
                repo.at_field(owner, "affects",
                              f"affects: {short_id} is in the assumption closure "
                              f"of the {prop} root '{root}', so its failure puts "
                              f"{needed} at stake; affects lists "
                              f"{', '.join(sorted(listed))}")


def check_unused_assumptions(repo: Repo) -> None:
    """Check 8d: every assumption is used.

    An assumption is used when some claim lists its short id in ``assumes``,
    or when an assumption that is used names it in ``refines`` (a family is
    declared through its members).

    A SUPERSEDED assumption is exempt: it has been superseded, so being in no
    closure is what it should be. Without the exemption the first assumption
    to be superseded (A-LMO) could only
    be kept by a superseded claim declaring it in ``assumes`` for the check's
    sake alone.
    """
    used = {short_id for claim in repo.claims.values() for short_id in claim.assumes}
    queue = list(used)
    while queue:
        owner = repo.assumptions.get(queue.pop())
        parent = owner.header.get("refines") if owner is not None else None
        if isinstance(parent, str) and parent not in used:
            used.add(parent)
            queue.append(parent)
    for short_id in sorted(repo.assumptions):
        if short_id not in used:
            claim = repo.assumptions[short_id]
            if str(claim.header.get("status", "")) == "superseded":
                continue
            repo.at_field(claim, "short_id",
                          f"unused assumption: no claim declares {short_id} in "
                          "assumes, and no used assumption refines it, so it is "
                          "in no closure and no report; declare it on the claims "
                          "that rest on it, or retire it")


def check_identity(repo: Repo, claim: Claim) -> None:
    """Check 2: id, file name, environment, label and proof agree; no env title."""
    declared = str(claim.header.get("id", ""))
    if declared != claim.claim_id:
        repo.at_field(claim, "id", f"identity: id '{declared}' does not match the "
                      f"path-derived id '{claim.claim_id}'")
    file_kind = claim.path.stem.split("-", 1)[0]
    if claim.kind and claim.kind != file_kind:
        repo.at_field(claim, "kind", f"identity: kind '{claim.kind}' does not match "
                      f"the file name kind '{file_kind}'")
    body = strip_comments(claim.body)
    forbidden = FORBIDDEN_RE.search(body)
    if forbidden:
        repo.at(claim, claim.line_at(body, forbidden.start()),
                f"identity: a claim file may not contain \\{forbidden.group(1)}")
    matches = list(ENV_BEGIN_RE.finditer(body))
    if len(matches) != 1:
        repo.at(claim, claim.body_start, "identity: expected exactly one claim "
                f"environment, found {len(matches)}")
        return
    match = matches[0]
    env = match.group(1)
    env_line = claim.line_at(body, match.start())
    if env != KIND_ENV.get(file_kind, ""):
        repo.at(claim, env_line, f"identity: environment '{env}' does not match kind "
                f"'{file_kind}' (expected '{KIND_ENV.get(file_kind, '')}')")
    if optional_argument(body, match.end()) is not None:
        repo.at(claim, env_line, f"identity: \\begin{{{env}}} carries a bracketed "
                "title; the header title is the claim's only title and the "
                "assembler prints it")
    end = body.find(f"\\end{{{env}}}", match.end())
    if end == -1:
        repo.at(claim, env_line, f"identity: \\begin{{{env}}} is never closed")
    span = body[match.end() : end if end != -1 else len(body)]
    labels = [m.group(1) for m in LABEL_RE.finditer(span)
              if not m.group(1).startswith("eq:")]
    if not labels:
        repo.at(claim, env_line,
                f"identity: the {env} environment carries no \\label")
    elif labels[0] != claim.label:
        repo.at(claim, env_line, f"identity: \\label{{{labels[0]}}} should be "
                f"\\label{{{claim.label}}}")
    proof = PROOF_RE.search(body)
    needs_proof = file_kind in PROOF_KINDS
    if needs_proof and proof is None:
        repo.at(claim, env_line,
                f"identity: kind '{file_kind}' requires a proof environment")
    if not needs_proof and proof is not None:
        repo.at(claim, claim.line_at(body, proof.start()),
                f"identity: kind '{file_kind}' must carry no proof environment")


def resolve_use(repo: Repo, claim: Claim, entry: str) -> str | None:
    """Resolve one ``uses`` entry to a claim id, or None if it does not exist."""
    candidate = entry if "/" in entry else f"{claim.module_id}/{entry}"
    return candidate if candidate in repo.claims else None


def allowed_modules(repo: Repo, module: Module) -> set[str]:
    """Return the module ids a claim of ``module`` may ``use`` besides its own.

    A core uses its ``depends_on``. A submodule uses its core, its core's
    ``depends_on`` and the sibling submodules its own
    ``depends_on`` names (a composition may use the instance a sibling
    builds, and the edge must be one-directional and acyclic so that
    deleting the dependent submodule leaves the rest green).
    """
    if not module.parent:
        return set(module.depends_on)
    allowed = {module.parent, *repo.modules[module.parent].depends_on}
    for entry in module.depends_on:
        sibling = f"{module.parent}/{entry}"
        allowed.add(sibling if sibling in repo.modules else entry)
    return allowed


def check_edges(repo: Repo, claim: Claim) -> None:
    """Check 3: every ``uses`` entry resolves and respects the module fences."""
    module = repo.modules[claim.module_id]
    allowed = allowed_modules(repo, module)
    for entry in claim.uses:
        target_id = resolve_use(repo, claim, entry)
        if target_id is None:
            repo.at_field(claim, "uses",
                          f"edges: uses '{entry}' does not resolve to a claim")
            continue
        claim.resolved_uses.append(target_id)
        target_kind = repo.claims[target_id].kind
        if target_kind == "ex":
            repo.at_field(claim, "uses", f"edges: uses '{target_id}' is an example; "
                          "an example is never a dependency, list it in mentions")
        elif claim.kind in USES_KIND_CITERS and target_kind in ("rem", "req"):
            repo.separation(claim, claim.line_of("uses"), "uses-kind",
                            f"uses '{target_id}', {a_kind(target_kind)}; "
                            f"{a_kind(claim.kind)} rests on no remark or "
                            "requirement: demote the edge to mentions, or re-kind the "
                            "target (a definition when it defines, a lemma when it "
                            "asserts)")
        target_module = target_id.rsplit("/", 1)[0]
        if target_module == claim.module_id:
            continue
        if target_module.startswith(f"{claim.module_id}/"):
            repo.at_field(claim, "uses", "edges: a core claim may not use the "
                          f"submodule claim '{target_id}'")
        elif target_module not in allowed:
            repo.at_field(claim, "uses", f"edges: uses '{target_id}' crosses into "
                          "a module not in depends_on")
    # A mention is not a dependency: it must resolve, but it may point anywhere
    # (a forward reference to a consequence in a consumer module is its point),
    # and it takes part in neither the cycle check nor --dependents.
    for entry in claim.mentions:
        target_id = resolve_use(repo, claim, entry)
        if target_id is None:
            repo.at_field(claim, "mentions",
                          f"edges: mentions '{entry}' does not resolve to a claim")
            continue
        claim.resolved_mentions.append(target_id)


def check_leaves(repo: Repo, claim: Claim) -> None:
    """Check 4: assumptions and facts are leaves; definitions assume nothing.

    An assumption uses only definitions and assumes nothing; a fact (an
    imported result, stated in this repository's terms) uses only definitions,
    so that nothing proved here is smuggled into a quotation. A definition's
    ``assumes`` is empty: it fixes meaning and asserts nothing that could be
    false, and an assumption that uses it would otherwise reach itself through
    it (see the module docstring); the claims that consume the premise declare
    it.
    """
    if claim.kind == "def":
        if claim.assumes:
            repo.at_field(claim, "assumes",
                          "leaves: a definition's assumes list must be empty "
                          "(a definition asserts nothing that could be false; "
                          "the claims that rest on the premise declare it)")
        return
    if claim.kind not in ("ass", "fact"):
        return
    noun = "an assumption" if claim.kind == "ass" else "a fact"
    if claim.kind == "ass" and claim.assumes:
        repo.at_field(claim, "assumes",
                      "leaves: an assumption's assumes list must be empty")
    for target_id in claim.resolved_uses:
        kind = repo.claims[target_id].kind
        if kind != "def":
            repo.at_field(claim, "uses", f"leaves: {noun} may only use "
                          f"definitions, but uses '{target_id}' ({kind})")


def check_acyclicity(repo: Repo) -> None:
    """Check 5: the ``uses`` graph carries no cycle."""
    colour: dict[str, int] = {}
    stack: list[str] = []
    reported: set[tuple[str, str]] = set()

    def visit(node: str) -> None:
        colour[node] = 1
        stack.append(node)
        for target in repo.claims[node].resolved_uses:
            if colour.get(target, 0) == 0:
                visit(target)
            elif colour.get(target) == 1 and (node, target) not in reported:
                reported.add((node, target))
                cycle = [*stack[stack.index(target) :], target]
                repo.at_field(repo.claims[node], "uses",
                              "acyclicity: uses cycle " + " -> ".join(cycle))
        stack.pop()
        colour[node] = 2

    for claim_id in sorted(repo.claims):
        if colour.get(claim_id, 0) == 0:
            visit(claim_id)


def declared_claims(repo: Repo, claim: Claim) -> list[str]:
    """Return the claims a claim's header declares: uses, mentions, assumes owners."""
    declared = [*claim.resolved_uses, *claim.resolved_mentions]
    for short_id in claim.assumes:
        owner = repo.assumptions.get(short_id)
        if owner is not None:
            declared.append(owner.claim_id)
    return declared


def all_labels(repo: Repo) -> set[str]:
    """Return every label any claim body defines (computed once per repository)."""
    if repo.known_labels is None:
        repo.known_labels = {label for other in repo.claims.values()
                             for label in other.own_labels}
    return repo.known_labels


def label_owners(repo: Repo) -> dict[tuple[str, str], str]:
    r"""Map (contract, label) to the claim defining it: where a ``\ref`` resolves.

    Computed once per repository. Where a contract defines a label twice
    (check 11 reports it), the first claim in id order wins.
    """
    if repo.owners_cache is None:
        owners: dict[tuple[str, str], str] = {}
        for claim_id in sorted(repo.claims):
            for label in sorted(repo.claims[claim_id].own_labels):
                owners.setdefault((contract_of(claim_id), label), claim_id)
        repo.owners_cache = owners
    return repo.owners_cache


def check_references(repo: Repo, claim: Claim) -> None:
    r"""Check 6: every \ref target is local, used, mentioned, assumed or pending.

    A ``pending`` entry names a label of a claim that does not exist yet; once
    a claim anywhere defines that label the entry is stale and must become a
    ``uses`` or ``mentions`` entry, so the checker refuses it. The reverse
    direction, that every ``mentions`` entry is referenced, is the separation
    rule ``mention-referenced`` (check 13).
    """
    check_mentions_referenced(repo, claim)
    allowed = set(claim.own_labels)
    for target_id in [*claim.resolved_uses, *claim.resolved_mentions]:
        target = repo.claims[target_id]
        allowed.add(target.label)
        allowed |= target.own_labels
    for short_id in claim.assumes:
        owner = repo.assumptions.get(short_id)
        if owner is not None:
            allowed.add(owner.label)
    known = all_labels(repo)
    for entry in claim.pending:
        if entry in known:
            repo.at_field(claim, "pending", f"references: pending '{entry}' is no "
                          "longer pending, a claim defines it; move it to uses or "
                          "mentions")
        else:
            allowed.add(entry)
    for wanted, line in claim.refs_seen:
        if wanted in allowed:
            continue
        if wanted in known:
            repo.at(claim, line, f"references: \\ref{{{wanted}}} is an undeclared "
                    "dependency; add the claim that defines it to uses or mentions")
        else:
            repo.at(claim, line, f"references: \\ref{{{wanted}}} resolves to no "
                    "label in any claim; list it in pending if its claim is "
                    "not written yet")


def check_mentions_referenced(repo: Repo, claim: Claim) -> None:
    r"""Check 13, ``mention-referenced``: the body references every mention.

    A mention counts as referenced when the body (lead-in, statement or proof,
    comments stripped) holds a ``\ref`` or ``\eqref`` to a label that resolves,
    in the claim's contract, to the mentioned claim, or an ``\xref`` naming it.
    A ``[[...]]`` link in a summary and a name in ``notes`` do not count: a
    link needs no header entry, and notes are plain text.
    """
    if not claim.resolved_mentions:
        return
    owners = label_owners(repo)
    contract = contract_of(claim.claim_id)
    referenced = {owners.get((contract, wanted)) for wanted, _ in claim.refs_seen}
    body = strip_comments(claim.body)
    referenced |= {match.group(1).strip() for match in XREF_RE.finditer(body)}
    for target_id in dict.fromkeys(claim.resolved_mentions):
        if target_id not in referenced:
            repo.separation(claim, claim.line_of("mentions"), "mention-referenced",
                            f"mentions '{target_id}', which the body never "
                            "references (\\ref, \\eqref or \\xref); delete the "
                            "entry (a summary link or a name in notes needs none)")


def check_statement_references(repo: Repo, claim: Claim) -> None:
    r"""Check 13, ``statement-ref-kind``: a statement points at no rem, req or ex.

    Covers the statement (the claim environment's content, comments stripped)
    of a theorem, lemma, proposition, corollary, definition, assumption or
    fact: no ``\ref`` or ``\eqref`` to a label that resolves, in the claim's
    contract, to a remark, requirement or example, and no ``\xref`` to one.
    Lead-ins and proofs are not covered, nor the statements of remarks,
    requirements and examples, whose job is to point.
    """
    if claim.kind not in STATEMENT_REF_KINDS:
        return
    body = strip_comments(claim.body)
    span = environment_span(body)
    if span is None:
        return
    owners = label_owners(repo)
    contract = contract_of(claim.claim_id)

    def report(offset: int, written: str, target_id: str) -> None:
        kind = repo.claims[target_id].kind
        repo.separation(claim, claim.line_at(body, offset), "statement-ref-kind",
                        f"the statement references {written}, {a_kind(kind)} "
                        f"('{target_id}'); the statement of {a_kind(claim.kind)} "
                        "references no remark, requirement or example: "
                        "move the pointer to the lead-in or the proof, or delete it "
                        "where the target's Used by line already links back")

    for match in REF_RE.finditer(body, span.content, span.close):
        for raw in match.group(1).split(","):
            label = raw.strip()
            owner = owners.get((contract, label))
            if owner is not None and repo.claims[owner].kind in POINTER_KINDS:
                report(match.start(), f"\\ref{{{label}}}", owner)
    for match in XREF_RE.finditer(body, span.content, span.close):
        target_id = match.group(1).strip()
        target = repo.claims.get(target_id)
        if target is not None and target.kind in POINTER_KINDS:
            report(match.start(), f"\\xref{{{target_id}}}", target_id)


def check_assumption_body(repo: Repo, claim: Claim) -> None:
    r"""Check 6b: an assumption's body references only definitions and its parent.

    Covers the whole body of an assumption (lead-in and statement, comments
    stripped; an assumption has no proof): every ``\ref`` and ``\eqref``
    whose label resolves, in the claim's contract, to a claim, and every
    ``\xref``, names a definition, the assumption itself, or the assumption
    its ``refines`` names. A label that resolves nowhere is check 6's.
    """
    if claim.kind != "ass":
        return
    body = strip_comments(claim.body)
    owners = label_owners(repo)
    contract = contract_of(claim.claim_id)
    parent = repo.assumptions.get(str(claim.header.get("refines", "")))
    allowed = {claim.claim_id, *([parent.claim_id] if parent is not None else [])}

    def report(offset: int, written: str, target_id: str) -> None:
        kind = repo.claims[target_id].kind
        repo.at(claim, claim.line_at(body, offset),
                f"assumption body: references {written}, {a_kind(kind)} "
                f"('{target_id}'); an assumption's body references only "
                "definitions and the assumption it refines: state the condition "
                "through a definition, and move a pointer to a consumer or a "
                "remark out of the assumption (spec/claim-format.md section 4.3)")

    for match in REF_RE.finditer(body):
        for raw in match.group(1).split(","):
            label = raw.strip()
            owner = owners.get((contract, label))
            if owner is not None and owner not in allowed \
                    and repo.claims[owner].kind != "def":
                report(match.start(), f"\\ref{{{label}}}", owner)
    for match in XREF_RE.finditer(body):
        target_id = match.group(1).strip()
        target = repo.claims.get(target_id)
        if target is not None and target_id not in allowed and target.kind != "def":
            report(match.start(), f"\\xref{{{target_id}}}", target_id)


def check_citations(repo: Repo, claim: Claim) -> None:
    """Check 7: cites carry a locator and a registered key; refs are registered."""
    body = strip_comments(claim.body)
    for match in CITE_RE.finditer(body):
        line = claim.line_at(body, match.start())
        if not (match.group(1) or "")[1:-1].strip():
            repo.at(claim, line, "citations: \\cite without a locator; write "
                    "\\cite[Thm. 3]{key}")
        for raw in match.group(2).split(","):
            key = raw.strip()
            if key and key not in repo.bibtex_keys:
                repo.at(claim, line, f"citations: bibtex key '{key}' is not "
                        "generated from refs/index.json")
    for entry in claim.header.get("refs") or []:
        text = str(entry)
        ref_id, _, locator = text.partition(",")
        if not locator.strip():
            repo.at_field(claim, "refs",
                          f"citations: refs entry '{text}' has no locator")
        if ref_id.strip() not in repo.ref_ids:
            repo.at_field(claim, "refs", f"citations: refs entry names "
                          f"'{ref_id.strip()}', which is not registered in "
                          "refs/index.json")


def index_assumptions(repo: Repo) -> None:
    """Map every short id to the assumption that owns it (first one wins)."""
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        if claim.kind != "ass":
            continue
        short_id = str(claim.header.get("short_id", "")).strip()
        if short_id and short_id not in repo.assumptions:
            repo.assumptions[short_id] = claim


def check_short_ids(repo: Repo) -> None:
    """Check 8: short ids are unique repository-wide and every assumes exists."""
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        if claim.kind != "ass":
            continue
        short_id = str(claim.header.get("short_id", "")).strip()
        owner = repo.assumptions.get(short_id)
        if owner is not None and owner is not claim:
            repo.at_field(claim, "short_id", f"short ids: '{short_id}' is already "
                          f"used by '{owner.claim_id}'")
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        for entry in claim.assumes:
            if entry not in repo.assumptions:
                repo.at_field(claim, "assumes",
                              f"short ids: assumes '{entry}' names no assumption")


def check_status(repo: Repo, claim: Claim) -> None:
    """Check 9: a settled claim carries a full proof, no pending, an implements.

    What a settled claim rests on is not an error here: a claim may be
    accepted conditional on its dependencies, and the
    checker computes the effective status instead (``effective_status``,
    ``--effective``, and the second number of every ``--status`` cell). What
    stays is what is local to the file: a settled claim's proof is complete,
    its references are all to existing claims, and `implemented` names the
    symbol it implements.
    """
    if claim.status in SETTLED:
        body = strip_comments(claim.body)
        proof = PROOF_RE.search(body)
        if proof and "sketch" in (proof.group(1) or "").lower():
            repo.at(claim, claim.line_at(body, proof.start()),
                    f"status: a '{claim.status}' claim carries a proof sketch")
        if claim.pending:
            repo.at_field(claim, "pending", f"status: a '{claim.status}' claim "
                          f"still has {len(claim.pending)} pending reference(s)")
    if claim.status == "implemented" and not claim.header.get("implements"):
        repo.at_field(claim, "status",
                      "status: 'implemented' requires an implements field")
    # A remark that carries implements is reported once, by check_header.
    bound_remark = claim.kind == "rem" and bool(claim.header.get("implements"))
    if (claim.status == "implemented" and claim.kind in ("rem", "ex")
            and not bound_remark):
        repo.separation(claim, claim.line_of("status"), "remark-implements",
                        f"status: {a_kind(claim.kind)} is never 'implemented' (it "
                        "has no code, so its status tops at 'accepted')")


@dataclass(frozen=True)
class EnvSpan:
    """Offsets of the claim environment in a comment-stripped body."""

    env: str
    begin: int                       # at \begin{env}
    title: tuple[int, int] | None    # the bracketed title, brackets included
    content: int                     # after the title (or after \begin{env})
    close: int                       # at \end{env}; len(body) if never closed
    end: int                         # after \end{env}


def optional_argument(text: str, index: int) -> tuple[int, int] | None:
    """Return the span of a ``[...]`` argument at ``index`` (after spaces).

    As LaTeX reads it: the first ``]`` outside braces closes it.
    """
    start = index
    while start < len(text) and text[start] in " \t\n":
        start += 1
    if start >= len(text) or text[start] != "[":
        return None
    depth = 0
    position = start + 1
    while position < len(text):
        char = text[position]
        if char == "\\":
            position += 2           # a control symbol (\] or \{) delimits nothing
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "]" and depth <= 0:
            return start, position + 1
        position += 1
    return None


def environment_span(body: str) -> EnvSpan | None:
    """Locate the first claim environment of a comment-stripped body."""
    match = ENV_BEGIN_RE.search(body)
    if match is None:
        return None
    env = match.group(1)
    title = optional_argument(body, match.end())
    content = title[1] if title else match.end()
    closing = f"\\end{{{env}}}"
    close = body.find(closing, content)
    if close == -1:
        return EnvSpan(env, match.start(), title, content, len(body), len(body))
    return EnvSpan(env, match.start(), title, content, close, close + len(closing))


def xref_problem(repo: Repo, claim: Claim, target: str, declared: set[str]) -> str:
    r"""Return why ``\xref{target}`` in ``claim`` is wrong, or "" when it is right."""
    if "/" not in target:
        return "needs a full claim id (module/label)"
    if target not in repo.claims:
        return "names no claim"
    if contract_of(target) == contract_of(claim.claim_id):
        other = repo.claims[target]
        return ("names a claim of this contract; refer to it as "
                f"{KIND_WORD.get(other.kind, 'Claim')}~\\ref{{{other.label}}}")
    if target not in declared:
        return ("is not declared: list it in uses or mentions (or its short id "
                "in assumes)")
    return ""


def repodoc_problem(root: Path, argument: str) -> str:
    r"""Return why ``\repodoc{argument}`` is wrong, or "" if it names a citable file."""
    path, _, anchor = argument.partition("#")
    if not REPODOC_PATH_RE.match(path) or ".." in path.split("/"):
        return ("must be a repository-relative path of letters, digits and "
                "'._-/' (with an optional #anchor)")
    if not REPODOC_ANCHOR_RE.match(anchor):
        return "has an anchor with characters outside letters, digits and '._-'"
    if path.split("/", 1)[0] in NOT_CITABLE_DIRS:
        return (f"points into {path.split('/', 1)[0]}/, which a contract never "
                f"cites ({', '.join(d + '/' for d in NOT_CITABLE_DIRS)})")
    if not (root / path).is_file():
        return "names no file of the repository"
    return ""


def check_body_commands(repo: Repo, claim: Claim) -> None:
    r"""Check 10: the body's cross-reference and marking commands.

    ``\cref`` is refused (cleveref is not loaded); ``\xref`` must name an
    existing, declared claim of another contract; ``\repodoc`` an existing,
    citable file; ``\term`` sits inside a definition's statement.
    """
    body = strip_comments(claim.body)
    for match in CREF_RE.finditer(body):
        repo.at(claim, claim.line_at(body, match.start()),
                f"body: \\{match.group(1)} is not available (cleveref is not "
                "loaded); write the kind out, as in Lemma~\\ref{lem:x}")
    declared = set(declared_claims(repo, claim))
    for match in XREF_RE.finditer(body):
        target = match.group(1).strip()
        problem = xref_problem(repo, claim, target, declared)
        if problem:
            repo.at(claim, claim.line_at(body, match.start()),
                    f"body: \\xref{{{target}}} {problem}")
    for match in REPODOC_RE.finditer(body):
        argument = match.group(1).strip()
        problem = repodoc_problem(repo.root, argument)
        if problem:
            repo.at(claim, claim.line_at(body, match.start()),
                    f"body: \\repodoc{{{argument}}} {problem}")
    span = environment_span(body)
    for match in TERM_RE.finditer(body):
        inside = span is not None and span.content <= match.start() < span.close
        if claim.kind != "def" or not inside:
            repo.at(claim, claim.line_at(body, match.start()),
                    f"body: \\term{{{match.group(1)}}} marks a defined phrase and "
                    "belongs inside a definition's statement")
    for match in TREF_RE.finditer(body):
        phrase = match.group(1) or match.group(2)
        found = resolve_term(repo, contract_of(claim.claim_id), phrase)
        if isinstance(found, str):
            repo.at(claim, claim.line_at(body, match.start()),
                    f"body: \\tref names '{phrase.strip()}', which {found}")


def term_key(text: str) -> str:
    r"""Normalise a ``\term`` argument: one defined phrase, however it is spaced."""
    return " ".join(text.split()).lower()


@dataclass(frozen=True)
class DefinedTerm:
    r"""A phrase a definition marks with ``\term``, with its gloss and its claim."""

    claim_id: str
    phrase: str     # as written in the \term argument
    gloss: str      # the one-line gloss of \term[gloss]{..}, or ""

    @property
    def contract(self) -> str:
        """The contract (core module) whose PDF defines the term."""
        return contract_of(self.claim_id)

    @property
    def anchor(self) -> str:
        """The named destination of the definition in its contract's PDF."""
        return "term-" + (re.sub(r"[^a-z0-9]+", "-", term_key(self.phrase))
                          .strip("-") or "x")


def defined_terms(repo: Repo) -> dict[tuple[str, str], DefinedTerm]:
    r"""Return every ``\term`` of the tree by (contract, normalised phrase).

    The first definition wins where a contract defines a phrase twice (check 11
    reports the second).
    """
    if repo.terms_cache is None:
        terms: dict[tuple[str, str], DefinedTerm] = {}
        for claim_id in sorted(repo.claims):
            body = strip_comments(repo.claims[claim_id].body)
            for match in TERM_GLOSS_RE.finditer(body):
                phrase = " ".join(match.group(2).split())
                terms.setdefault((contract_of(claim_id), term_key(phrase)),
                                 DefinedTerm(claim_id, phrase,
                                             " ".join((match.group(1) or "").split())))
        repo.terms_cache = terms
    return repo.terms_cache


def resolve_term(repo: Repo, contract: str, phrase: str) -> DefinedTerm | str:
    """Resolve a phrase used in ``contract``: its own definition, else the one other.

    Returns the problem as a sentence when there is none or more than one.
    """
    terms = defined_terms(repo)
    key = term_key(phrase)
    if (contract, key) in terms:
        return terms[(contract, key)]
    others = sorted(term.contract for (_c, k), term in terms.items() if k == key)
    if len(others) == 1:
        return terms[(others[0], key)]
    if not others:
        return "no \\term of any contract defines"
    return ("several contracts define (" + ", ".join(others) + "); "
            "define it in this contract or rename one")


def check_contract_namespaces(repo: Repo) -> None:
    r"""Check 11: labels and defined terms are unique within an assembled contract.

    The contract (a core and its submodules) is where a ``\ref`` resolves, so a
    label defined twice there makes a reference ambiguous; a phrase marked with
    ``\term`` twice would carry two definitions into one index of terms.
    """
    labels: dict[tuple[str, str], str] = {}
    terms: dict[tuple[str, str], str] = {}
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        contract = contract_of(claim_id)
        body = strip_comments(claim.body)
        here: set[str] = set()
        for match in LABEL_RE.finditer(body):
            label = match.group(1)
            other = labels.setdefault((contract, label), claim_id)
            if other != claim_id or label in here:
                where = "this claim" if other == claim_id else f"'{other}'"
                repo.at(claim, claim.line_at(body, match.start()),
                        f"labels: \\label{{{label}}} is already defined by "
                        f"{where} in the contract of {contract}")
            here.add(label)
        here_terms: set[str] = set()
        for match in TERM_RE.finditer(body):
            term = term_key(match.group(1))
            other = terms.setdefault((contract, term), claim_id)
            if other != claim_id or term in here_terms:
                where = "this claim" if other == claim_id else f"'{other}'"
                repo.at(claim, claim.line_at(body, match.start()),
                        f"terms: \\term{{{match.group(1)}}} is already defined by "
                        f"{where} in the contract of {contract}")
            here_terms.add(term)


def link_target(repo: Repo, module_id: str, target: str) -> LinkTarget | None:
    r"""Resolve one ``[[...]]`` target written in ``module_id``'s fields.

    A full id names its claim anywhere; a bare label names the claim of the
    field's contract that carries it (a label is unique in its contract, so
    a submodule's field reaches a core claim by its label, as ``\ref`` does).
    """
    key = link_key(target, module_id)
    if SHORT_ID_LINK_RE.match(key):
        owner = repo.assumptions.get(key)
        if owner is None:
            return None
        return LinkTarget(owner.claim_id, owner.kind, owner.label,
                          str(owner.header.get("title", owner.label)), short_id=key)
    claim = repo.claims.get(key)
    if claim is None and "/" not in target.strip():
        contract = contract_of(module_id)
        found = [other for other in repo.claims.values()
                 if other.label == target.strip()
                 and contract_of(other.claim_id) == contract]
        claim = found[0] if len(found) == 1 else None
    if claim is None:
        return None
    return LinkTarget(claim.claim_id, claim.kind, claim.label,
                      str(claim.header.get("title", claim.label)))


def link_resolver(repo: Repo, module_id: str) -> Resolver:
    """Return the resolver the renderers use for one module's plain-text fields."""
    return lambda target: link_target(repo, module_id, target)


@dataclass(frozen=True)
class PlainField:
    """One plain-text field: a claim summary or a module or group abstract."""

    module_id: str
    name: str            # "summary", "user_statement", "abstract" or
                         # "reading_groups abstract"
    text: str
    path: str
    line: int
    claim: Claim | None = None


def plain_text_fields(repo: Repo) -> Iterator[PlainField]:
    """Yield every present, textual summary and abstract of the repository."""
    for module_id in sorted(repo.modules):
        module = repo.modules[module_id]
        abstract = module.meta.get("abstract")
        if isinstance(abstract, str):
            yield PlainField(module_id, "abstract", abstract, module.rel,
                             field_line(module.lines, "abstract"))
        groups = module.meta.get("reading_groups")
        for group in groups if isinstance(groups, list) else []:
            if isinstance(group, dict) and isinstance(group.get("abstract"), str):
                start = str(group.get("start", ""))
                line = next((number for number, text in enumerate(module.lines, 1)
                             if re.search(r"start:\s*['\"]?" + re.escape(start)
                                          + r"(?![A-Za-z0-9:-])", text)),
                            field_line(module.lines, "reading_groups"))
                yield PlainField(module_id, "reading_groups abstract",
                                 group["abstract"], module.rel, line)
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        summary = claim.header.get("summary")
        if isinstance(summary, str):
            yield PlainField(claim.module_id, "summary", summary, claim.rel,
                             claim.line_of("summary"), claim)
        statement = claim.header.get("user_statement")
        if (claim.kind not in USER_STATEMENT_REFUSED_KINDS
                and isinstance(statement, str)):
            yield PlainField(claim.module_id, "user_statement", statement, claim.rel,
                             claim.line_of("user_statement"), claim)


def check_links(repo: Repo) -> None:
    """Check 12: every ``[[...]]`` link of a summary or abstract resolves."""
    for item in plain_text_fields(repo):
        for match in LINK_RE.finditer(item.text):
            target = match.group(1).strip()
            if target and link_target(repo, item.module_id, target) is not None:
                continue
            what = ("names no assumption short id" if SHORT_ID_LINK_RE.match(target)
                    else "names no claim (a bare label is read in this contract, "
                    "a full id anywhere)")
            repo.errors.append(Error(item.path, item.line,
                                     f"links: {item.name} link [[{target}]] {what}",
                                     item.module_id))


def check_order(repo: Repo, module: Module) -> None:
    """Check 0 (continued): ``order`` lists each of the module's claims once."""
    present = {claim.label for claim in repo.claims.values()
               if claim.module_id == module.module_id}
    line = field_line(module.lines, "order")
    seen: set[str] = set()
    for entry in module.order:
        if entry in seen:
            repo.error(module.rel, line,
                       f"module.yaml: order lists '{entry}' twice", module.module_id)
        seen.add(entry)
        if entry not in present:
            repo.error(module.rel, line,
                       f"module.yaml: order lists '{entry}', which is not a claim "
                       "of this module", module.module_id)
    for label in sorted(present - seen):
        repo.error(module.rel, line,
                   f"module.yaml: claim '{label}' is missing from order",
                   module.module_id)


def load_repo(root: Path) -> Repo:
    """Load and check a repository, returning it with its findings attached."""
    repo = Repo(root=root)
    load_reference_index(repo)
    discover_modules(repo)
    check_sibling_dependencies(repo)
    load_claims(repo)
    index_assumptions(repo)
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        check_header(repo, claim)
        check_identity(repo, claim)
        check_edges(repo, claim)
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        check_leaves(repo, claim)
        check_references(repo, claim)
        check_statement_references(repo, claim)
        check_assumption_body(repo, claim)
        check_role_words(repo, claim)
        check_citations(repo, claim)
        check_status(repo, claim)
        check_body_commands(repo, claim)
    check_acyclicity(repo)
    check_short_ids(repo)
    check_refines(repo)
    check_affects(repo)
    check_unused_assumptions(repo)
    check_contract_namespaces(repo)
    check_links(repo)
    for module_id in sorted(repo.modules):
        check_order(repo, repo.modules[module_id])
    return repo


def in_scope(module_id: str, wanted: str | None) -> bool:
    """Return whether a module id falls under a ``--module`` filter."""
    if wanted is None:
        return True
    return module_id == wanted or module_id.startswith(f"{wanted}/")


def dependents_of(repo: Repo, claim_id: str) -> list[str]:
    """Return the transitive dependents of a claim: its re-review scope.

    An edge is a ``uses`` entry or, for an assumption, an ``assumes`` entry
    naming its short id; the walk is transitive over both.
    """
    reverse: dict[str, list[str]] = {}
    for other in repo.claims.values():
        for target in other.resolved_uses:
            reverse.setdefault(target, []).append(other.claim_id)
        for short_id in other.assumes:
            owner = repo.assumptions.get(short_id)
            if owner is not None:
                reverse.setdefault(owner.claim_id, []).append(other.claim_id)
    seen: set[str] = set()
    queue = list(reverse.get(claim_id, []))
    while queue:
        node = queue.pop()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(reverse.get(node, []))
    return sorted(seen)


def mentioned_by(repo: Repo, claim_id: str) -> list[str]:
    """Return the claims that list ``claim_id`` in ``mentions`` (not transitive)."""
    return sorted(other.claim_id for other in repo.claims.values()
                  if claim_id in other.resolved_mentions)


def uses_closure(repo: Repo, claim_id: str) -> list[str]:
    """Return the transitive claims a claim rests on, itself excluded."""
    seen: set[str] = set()
    queue = list(repo.claims[claim_id].resolved_uses)
    while queue:
        node = queue.pop()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(repo.claims[node].resolved_uses)
    return sorted(seen)


def assumption_closure(repo: Repo, claim_id: str) -> dict[str, list[str]]:
    """Return the assumption short ids a claim rests on, with who declares each.

    The walk is the claim and its transitive ``uses`` closure; every short id
    those claims list in ``assumes`` is in the closure, mapped to the sorted
    claims that declare it. It is the one walk of ``--assumptions`` and of the
    generated claim-closure table (``harness/generate_claim_closure.py``), so
    the two cannot disagree. Sorted by short id.
    """
    sources: dict[str, list[str]] = {}
    for member in [claim_id, *uses_closure(repo, claim_id)]:
        for short_id in repo.claims[member].assumes:
            sources.setdefault(short_id, []).append(member)
    return {short_id: sorted(sources[short_id]) for short_id in sorted(sources)}


def status_rank(status: str) -> int:
    """Rank a header status on ``STATUS_LADDER``; an unknown status ranks below all.

    A status outside the vocabulary is already an error of check 1; ranking it
    lowest keeps the effective status from silently reading as settled while
    that error stands.
    """
    return STATUS_LADDER.index(status) if status in STATUS_LADDER else -1


def status_closure(repo: Repo, claim_id: str) -> set[str]:
    """Return the claims a claim's status depends on, itself included.

    The edges are ``uses`` and ``assumes`` (each short id resolved to the
    assumption that owns it, in whatever module it lives); ``mentions`` is not
    a dependency and is excluded. The walk collects a reachable set, so it
    terminates even if the combined graph carries a cycle.
    """
    seen = {claim_id}
    queue = [claim_id]
    while queue:
        claim = repo.claims[queue.pop()]
        targets = list(claim.resolved_uses)
        for short_id in claim.assumes:
            owner = repo.assumptions.get(short_id)
            if owner is not None:
                targets.append(owner.claim_id)
        for target in targets:
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def effective_status(repo: Repo, claim_id: str) -> tuple[str, list[str]]:
    """Return a claim's effective status and the claims that bind it.

    The effective status is the minimum header status over the claim's
    ``uses``/``assumes`` closure, itself included. The
    binders are the weakest claims of that closure: what a reader re-reads to
    lift the claim. A claim binds itself when nothing it rests on is weaker.
    """
    closure = status_closure(repo, claim_id)
    weakest = min(status_rank(repo.claims[node].status) for node in closure)
    binders = sorted(node for node in closure
                     if status_rank(repo.claims[node].status) == weakest)
    return repo.claims[binders[0]].status, binders


def effective_status_map(repo: Repo) -> dict[str, str]:
    """Return every claim's effective status, keyed by claim id."""
    return {claim_id: effective_status(repo, claim_id)[0] for claim_id in repo.claims}


def write_graph(repo: Repo, target: Path, wanted: str | None,
                focus: str | None = None) -> None:
    """Write declared dependencies as DOT, SVG or PDF, with optional focus."""
    from harness.claim_graph import export_graph

    export_graph(repo, target, wanted, focus)


def status_counts(repo: Repo, module_id: str) -> tuple[dict[str, int], int]:
    """Return a module's claim counts by status and its pending-reference count."""
    counts = dict.fromkeys(STATUSES, 0)
    pending = 0
    for claim in repo.claims.values():
        if claim.module_id != module_id:
            continue
        if claim.status in counts:
            counts[claim.status] += 1
        pending += len(claim.pending)
    return counts, pending


def effective_counts(repo: Repo, module_id: str,
                     effective: dict[str, str] | None = None) -> dict[str, int]:
    """Return a module's claim counts by effective status.

    ``effective`` is the map ``effective_status_map`` returns; pass it when
    counting several modules so the closures are walked once.
    """
    if effective is None:
        effective = effective_status_map(repo)
    counts = dict.fromkeys(STATUSES, 0)
    for claim_id, claim in repo.claims.items():
        if claim.module_id != module_id:
            continue
        status = effective.get(claim_id, "")
        if status in counts:
            counts[status] += 1
    return counts


def print_status(repo: Repo, wanted: str | None) -> None:
    """Print claim counts per module and status, header and effective, and pending.

    Each status cell is the header count with the effective count in
    parentheses: the header status is the local judgement, the effective
    status the minimum over the claim's uses/assumes closure.
    """
    modules = [m for m in sorted(repo.modules) if in_scope(m, wanted)]
    effective = effective_status_map(repo)
    width = max([len("module")] + [len(m) for m in modules], default=6)
    header = "module".ljust(width) + "".join(s.rjust(13) for s in STATUSES)
    print(header + "pending".rjust(9) + "total".rjust(8))
    totals = dict.fromkeys(STATUSES, 0)
    eff_totals = dict.fromkeys(STATUSES, 0)
    total_pending = 0
    for module_id in modules:
        counts, pending = status_counts(repo, module_id)
        eff = effective_counts(repo, module_id, effective)
        for status in STATUSES:
            totals[status] += counts[status]
            eff_totals[status] += eff[status]
        total_pending += pending
        row = module_id.ljust(width) + "".join(
            f"{counts[s]} ({eff[s]})".rjust(13) for s in STATUSES)
        print(row + str(pending).rjust(9) + str(sum(counts.values())).rjust(8))
    row = "TOTAL".ljust(width) + "".join(
        f"{totals[s]} ({eff_totals[s]})".rjust(13) for s in STATUSES)
    print(row + str(total_pending).rjust(9) + str(sum(totals.values())).rjust(8))
    print("header count (effective count): the header status is the local "
          "judgement,")
    print("the effective status the minimum over the uses/assumes closure "
          "(--effective <id>).")


def query_target(repo: Repo, wanted: str) -> str | None:
    """Resolve a query's argument: a claim id, or an assumption's short id.

    A short id stands for the assumption claim that owns it (assumptions are named by
    short id in code, run
    records and conversation).
    """
    if wanted in repo.claims:
        return wanted
    owner = repo.assumptions.get(wanted.strip())
    return owner.claim_id if owner is not None else None


def run_queries(repo: Repo, args: argparse.Namespace) -> int:
    """Answer the query flags; return 1 if a query names an unknown claim."""
    failed = 0
    if args.graph:
        try:
            write_graph(repo, Path(args.graph), args.module, args.focus)
            print(f"wrote {args.graph}")
        except (ValueError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            failed = 1
    for name in ("dependents", "assumptions", "effective"):
        flag = getattr(args, name)
        if not flag:
            continue
        resolved = query_target(repo, flag)
        if resolved is None:
            print(f"error: --{name} '{flag}' is not a claim id or an assumption "
                  "short id", file=sys.stderr)
            failed = 1
        setattr(args, name, resolved)
    if args.dependents:
        found = dependents_of(repo, args.dependents)
        print(f"dependents of {args.dependents} ({len(found)}):")
        for claim_id in found:
            print(f"  {claim_id}  [{repo.claims[claim_id].status}]")
        talkers = mentioned_by(repo, args.dependents)
        print(f"mentioned by, not a dependency ({len(talkers)}):")
        for claim_id in talkers:
            print(f"  {claim_id}  [{repo.claims[claim_id].status}]")
    if args.assumptions:
        sources = assumption_closure(repo, args.assumptions)
        print(f"assumption closure of {args.assumptions} ({len(sources)}):")
        for short_id, declarers in sources.items():
            print(f"  {short_id}  via {', '.join(declarers)}")
    if args.effective:
        status, binders = effective_status(repo, args.effective)
        print(args.effective)
        print(f"  header status:    {repo.claims[args.effective].status}")
        print(f"  effective status: {status}")
        print(f"  bound by ({len(binders)}):")
        for claim_id in binders:
            own = " (itself)" if claim_id == args.effective else ""
            print(f"    {claim_id}  [{repo.claims[claim_id].status}]{own}")
    if args.status:
        print_status(repo, args.module)
    return failed


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="python -m harness.check_claims",
        description="Check claim files against spec/claim-format.md §6.")
    parser.add_argument("--repo", default=".", help="repository root (default: .)")
    parser.add_argument("--module", default=None,
                        help="report only findings of this module id")
    parser.add_argument("--graph", default=None, metavar="OUT.DOT|OUT.SVG|OUT.PDF",
                        help="write uses/assumes dependencies (SVG/PDF need Graphviz)")
    parser.add_argument("--focus", default=None, metavar="CLAIM-ID",
                        help="with --graph: full prerequisite closure, across modules")
    parser.add_argument("--dependents", default=None, metavar="ID",
                        help="list the transitive dependents of a claim id or an "
                             "assumption short id (for an assumption: the claims "
                             "declaring it and theirs); claims that only mention it "
                             "are listed separately")
    parser.add_argument("--assumptions", default=None, metavar="ID",
                        help="list the transitive assumption closure of a claim id "
                             "(or an assumption short id)")
    parser.add_argument("--effective", default=None, metavar="ID",
                        help="print a claim's (or an assumption short id's) header "
                             "status, its effective status "
                             "(the minimum over its uses/assumes closure) and the "
                             "claim(s) that bind it")
    parser.add_argument("--status", action="store_true",
                        help="print a table of claims per module and status, each "
                             "cell the header count with the effective count in "
                             "parentheses")
    parser.add_argument("--advice", action="store_true",
                        help="also print the editorial heuristics of "
                             "harness/check_advice.py, for an explicit editorial "
                             "pass; advice never changes the exit code")
    parser.add_argument("--rule", default=None, metavar="NAME",
                        help="with --advice: only this heuristic")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Check the repository, answer any query, and return the exit code."""
    args = build_parser().parse_args(argv)
    if args.focus and not args.graph:
        print("error: --focus requires --graph", file=sys.stderr)
        return 1
    if args.rule and not args.advice:
        print("error: --rule requires --advice", file=sys.stderr)
        return 1
    if args.advice:
        # Imported only under the flag: advice is never part of a default run.
        from harness.check_advice import RULES as ADVICE_RULES
        if args.rule and args.rule not in ADVICE_RULES:
            print(f"error: --rule '{args.rule}' is not an advice rule; one of "
                  + ", ".join(ADVICE_RULES), file=sys.stderr)
            return 1
    root = Path(args.repo)
    if not root.is_dir():
        print(f"error: --repo {args.repo} is not a directory", file=sys.stderr)
        return 1
    repo = load_repo(root)
    if args.module is not None and args.module not in repo.modules:
        print(f"error: --module '{args.module}' is not a module", file=sys.stderr)
        return 1
    errors = [e for e in sorted(repo.errors) if in_scope(e.module, args.module)
              or not e.module]
    for error in errors:
        print(error.render())
    scope = args.module or "spec/modules"
    # Imported here: check_presentation builds on this module's reader.
    from harness.check_presentation import report_presentation
    presentation = report_presentation(repo, args.module, scope)
    if args.advice:
        from harness.check_advice import report_advice
        report_advice(repo, args.module, scope, args.rule)   # never an exit code
    failed = run_queries(repo, args)
    if errors:
        print(f"{len(errors)} error(s) in {scope}", file=sys.stderr)
        return 1
    if presentation:
        print(f"{presentation} presentation finding(s) in {scope} (the default "
              "checks pass)", file=sys.stderr)
        return 1
    # The checks always run on the whole repository (an edge may cross into
    # any module); the summary names what the filter reports on.
    n_claims = sum(1 for c in repo.claims.values()
                   if in_scope(c.module_id, args.module))
    n_modules = sum(1 for m in repo.modules if in_scope(m, args.module))
    print(f"ok: {n_claims} claim(s) in {n_modules} module(s) under {scope}"
          + ("" if args.module is None else
             f" (all {len(repo.claims)} claims checked)"))
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
