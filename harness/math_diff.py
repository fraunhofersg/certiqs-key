#!/usr/bin/env python3
r"""Motivation: a rewrite whose mathematics nobody can certify by eye.

`PRINCIPLES.md` §6 names three amendment routes. The **editorial** one says
that this tool "shows that no claim statement or proof changed", and until it
existed nothing did: a reviewer word-diffed the old and new file by hand. The
**presentational** route rewrites contracts for
readability -- statements and proofs rephrased, claims split, merged,
relabelled or re-kinded -- and an equivalence reviewer on artefacts only must
certify that no mathematics changed. On such a rewrite a raw `git diff` is
noise from the first line: every `\ref` is rewritten by a relabel, every
`Lemma~\ref{..}` becomes `\xref{..}`, a macro rename touches every formula, a
split scatters one statement over two files. The error class this tool exists
for is a hypothesis, quantifier, constant or inequality direction altered
inside a change that looks like wording -- invisible exactly when every line
of the diff changed.

So the tool removes presentation on both sides with the same normalisation and
reports what still differs, claim by claim and segment by segment, each
difference labelled math or prose. It is a lens, not an authority
(`harness/roles/equivalence-reviewer.md`): it never decides that two different
texts mean the same thing, it only shows that two texts are the same after the
normalisation below, and where they are not.

SEGMENTS. Per claim: `title`, `summary` and `user_statement` (header),
`lead-in` (body text before the claim environment), `statement` (the claim
environment's body), `proof` (every proof environment,
concatenated), `trailing` (text after the environment, around and after the
proofs), and the header fields `kind`, `status`, `uses`, `mentions`,
`assumes`, `refs`, `provenance`, `prominence`, `implements`, `short_id`,
`verification`, `supersedes`, and an assumption's `category`, `affects`,
`refines` and `presupposes`. The first three of these and `user_statement`
are compared so that an equivalence reviewer reading this report sees a
re-categorised assumption, a changed `affects` list, a new `refines` edge or
a rewritten `user_statement` -- the reading a user checks their setup
against. `affects` is compared as a set, like `refs`,
and so is an assumption's `presupposes`, the roles its text
presupposes, which a run-tier guard reads. Header, environment
and proof parsing reuse `check_claims` (`split_header`, `load_yaml_mapping`,
`strip_comments`, the environment table and `PROOF_RE`); the `requirement`
environment of the `req` kind is recognised as well.

NORMALISATION, identical on both sides, in this order:

1. LaTeX comments are stripped (`check_claims.strip_comments`; `\%` stays).
2. Every reference form becomes one token `REF(<target>)`: `\ref`, `\eqref`,
   `\cref`, `\Cref`, `\autoref`, `\xref`, `\labelcref`, `\nameref`,
   `\pageref`, `\cpageref` (each comma-separated target separately),
   `\texttt{...}` when the argument, with `\allowbreak` removed, has the
   shape of a claim label with zero, one or two module segments (a bare
   label, a partial id `<submodule>/<label>`, a full id), and `[[label]]`.
   A kind word immediately before it (Theorem, Lemma,
   Proposition, Corollary, Definition, Assumption, Remark, Example, Fact,
   Requirement, Equation, their plurals and the abbreviations Thm., Lem.,
   Prop., Cor., Def., Rem., Eq., Ex., Req., case-insensitive) is dropped with
   the tie or space after it, and a reference in bare parentheses loses them,
   so `Remark~\ref{rem:x}`, `\Cref{rem:x}`, `(\ref{rem:x})` and
   `\xref{m/rem:x}` compare equal. A claim label resolves to a full claim id
   the way `check_claims` resolves it: own module, the claim's `uses` and
   `mentions`, its assumptions' owners, the parent core of a submodule, then
   a label unique in the revision; a partial id resolves to the one full id
   ending in it; an unresolved label stays as written. The
   id then passes through the map (`--map`): an old id renamed to its new id,
   an old id merged into its target, and every part of a split and the old id
   it came from to one token `split(<old id>)`. Equation labels (`eq:...`)
   are local names and stay as written.
3. `\label{...}` is removed, and the claim environment's optional bracket
   title (and a proof's `[...]`) are cut off before normalising.
4. Macros of `spec/macros.tex` **as of each revision** are expanded to a fixed
   point: `\newcommand`, `\renewcommand`, `\providecommand` with a
   brace-delimited body (read with `check_symbols`' `DEFINITION_RE`,
   `read_group` and `substitute`), `\DeclareMathOperator` as
   `\operatorname{..}`, and `\let`. An argument not in braces is the next
   single token, as TeX reads it. Renaming a macro therefore does not look
   like a change, and the same macro text compares equal.
5. Presentation-only control sequences are dropped: the spacing commands
   `\, \; \: \! \> \ ` `~` `\quad \qquad` and the other fixed spaces,
   `\medskip \smallskip \bigskip`, the delimiter sizes `\big .. \Bigg` with
   their `l`/`r`/`m` variants, `\left \right \middle` (and the null
   delimiter `.` after the first two), `\displaystyle \textstyle
   \scriptstyle`, the break commands (`\allowbreak \nobreak \linebreak
   \newline \pagebreak ..`), `\noindent \par \hfill \strut \relax`, `\notag
   \nonumber`, `\vspace{..}` and `\hspace{..}` with their argument, the font
   declarations `\em \bf \it \bfseries \itshape \upshape \normalfont`, and the
   `sloppypar` environment. `\dfrac` and `\tfrac` become `\frac`, `\dbinom`
   and `\tbinom` become `\binom`. `\emph`, `\textbf`, `\textit`,
   `\boldsymbol`, `\term` and `\tref` are unwrapped (the command and its
   braces go, the content stays; the optional argument of `\term` and
   `\tref`, a gloss or the defined phrase a use links to, goes too: it is
   navigation, not mathematics).
6. Every display -- `equation`, `align`, `gather`, `multline`, `flalign`,
   `alignat`, `eqnarray` (starred or not), `\[..\]` and `$$..$$` -- is one
   kind of display, and `&` and `\\` (with a `\\[..]` spacing argument) are
   dropped at a display's own level and inside the layout environments
   `aligned`, `split`, `gathered`, `alignedat` and `multlined`; inside
   `cases`, a matrix or an array they are kept, because there they separate
   entries. Display and inline delimiters themselves carry no token: a
   formula moved from inline to display is the same formula.
7. The text is tokenised into TeX tokens: control sequences, braces, single
   symbols, words in prose, and single letters and digits in math (TeX reads
   `ab` and `a b` in math alike). Each token is marked prose, inline math or
   display math; the mark labels a difference and never makes one.

Two texts are **equal** when their token sequences agree without the grouping
braces `{` `}`; a difference in braces alone is noted, never failed.

COMPARISON. Claims are paired through the map: the same id, or `renames`
(chains `a -> b -> c` followed); a `split` compares the old statement with
the concatenation of the new statements in map order, and the same for every
other segment; a `merge` compares the concatenation of the old ones with the
new one. A claim that disappears or appears **without a map entry** fails as
unaccounted, because a statement then differs from nothing. A claim the map
lists under `deleted` **fails too**, reported as "deleted (declared in map)"
rather than as unaccounted: deleting a claim is never editorial, and the
editorial route relies on exit 0 meaning that no mathematics changed; on the
presentational route the equivalence reviewer reads the report anyway, so the
failure costs nothing there. The declaration still matters: it separates a deliberate
deletion, whose sentences are traced to where they moved, from an accident.
Header fields are compared after resolution and the
map: `uses` and `mentions` as sets of canonical ids (a split's parts citing
each other are dropped), the rest as values; a change of `status` is flagged
at the top of the report. A normalised sentence or display that left one
claim segment and appears (similarity >= 0.9, `difflib` ratio over its
tokens) in another claim or segment is reported as moved there, not only as a
deletion.

EXIT CODE 1 when any normalised statement or proof differs after the map, a
claim was deleted (declared in the map or not), or a claim appeared without a
map entry; 0 otherwise. Titles,
summaries, user statements, lead-ins, trailing text and header fields other
than the statement and proof are reported and never fail: a `user_statement`
is non-normative ("the statement wins", `spec/claim-format.md` §3), so an
edit to it alone exits 0 and is read, like a summary, in the report. 2 on
a usage error (an unknown revision or module).

KNOWN LIMITS, on purpose. Equivalence is never decided: a rephrased sentence
differs, and the reviewer reads it. Macro expansion covers brace-delimited
definitions without optional arguments; a `\def` with a parameter text is
left unexpanded on both sides. Dropping `&` and `\\` in a display merges
its rows, so reordering two rows of an `align` shows as a difference, and a
display that splits a formula differently at `&` compares equal. Letters and
digits in math are single tokens, so `x_12` and `x_{12}` compare equal. A
reference into a split claim resolves to its split group, not to the part.
`--module` compares and searches moved text only in the claims in scope.

Usage:
    python -m harness.math_diff OLD NEW [--map PATH] [--module ID] [--json]
    python -m harness.math_diff OLD --worktree [--map PATH] [--module ID]

OLD and NEW are git revisions; claim files are read from the object database
(`git ls-tree` and one `git cat-file --batch`, the same bytes `git show`
prints) without a checkout. `--worktree` reads NEW from the files on disk.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from harness.check_claims import (
    ENV_KIND,
    LABEL_RE,
    PROOF_RE,
    ClaimFormatError,
    in_scope,
    load_yaml_mapping,
    split_header,
    strip_comments,
)
from harness.check_symbols import (
    DEFINITION_RE,
    Macro,
    definition_name,
    read_group,
    substitute,
)

# --- Vocabulary ---------------------------------------------------------------

SEGMENTS = ("title", "summary", "user_statement", "lead-in", "statement", "proof",
            "trailing")
FAILING_SEGMENTS = frozenset({"statement", "proof"})
HEADER_FIELDS = ("kind", "status", "uses", "mentions", "assumes", "refs",
                 "provenance", "prominence", "implements", "short_id",
                 "verification", "supersedes", "category", "affects", "refines",
                 "presupposes")
LIST_FIELDS = frozenset({"uses", "mentions", "assumes", "refs", "affects",
                         "presupposes"})
ID_FIELDS = frozenset({"uses", "mentions"})

#: The claim environments: check_claims' nine plus the planned `requirement`.
CLAIM_ENVS: dict[str, str] = {**ENV_KIND, "requirement": "req"}
CLAIM_BEGIN_RE = re.compile(r"\\begin\{(" + "|".join(sorted(CLAIM_ENVS)) + r")\}")
PROOF_END = "\\end{proof}"
CLAIM_PATH_RE = re.compile(r"^spec/modules/([^/]+)/(?:([^/]+)/)?claims/([^/]+)\.tex$")
MACROS_PATH = "spec/macros.tex"

REF_COMMANDS = ("ref|eqref|cref|Cref|autoref|xref|labelcref|nameref|pageref"
                "|cpageref|Cpageref")
KIND_WORDS = (r"theorems?|lemmas?|lemmata|propositions?|corollary|corollaries"
              r"|definitions?|assumptions?|remarks?|examples?|facts?"
              r"|requirements?|equations?"
              r"|thms?\.|lems?\.|props?\.|cors?\.|defs?\.|rems?\.|eqs?\."
              r"|exs?\.|reqs?\.")
CLAIM_ID_SHAPE = r"(?:[a-z0-9-]+/){1,2}[a-z]+:[a-z0-9][a-z0-9-]*"
#: A claim id in \texttt, as the tree wrote them: bare, partial or full, and
#: broken for line breaking with \allowbreak.
TEXTTT_ID_SHAPE = (r"(?:[a-z0-9-]+/(?:\\allowbreak\s*)?){0,2}"
                   r"(?:thm|lem|prop|cor|def|ass|rem|ex|fact|req)"
                   r":(?:\\allowbreak\s*)?[a-z0-9][a-z0-9-]*")
ALLOWBREAK_RE = re.compile(r"\\allowbreak\s*")
LABEL_SHAPE = r"(?:[a-z0-9-]+/){0,2}[a-z]+:[a-z0-9][a-z0-9-]*"
REFERENCE_RE = re.compile(
    r"(?:(?<![A-Za-z\\])(?i:" + KIND_WORDS + r")(?:\s|~|\\ |\\,)*)?"
    r"(?:\\(?:" + REF_COMMANDS + r")\*?(?:\[[^\]]*\])?\s*\{([^{}]*)\}"
    r"|\\texttt\s*\{(" + TEXTTT_ID_SHAPE + r")\}"
    r"|\[\[(" + LABEL_SHAPE + r")\]\])"
)
REF_OPEN, REF_CLOSE = "\ue000", "\ue001"

TOKEN_RE = re.compile(
    REF_OPEN + "[^" + REF_CLOSE + "]*" + REF_CLOSE
    + r"|\\(?:begin|end)\s*\{[^{}]*\}"
    r"|\\[A-Za-z@]+"
    r"|\\[^A-Za-z@]"
    r"|\$\$|\$"
    r"|[^\W\d_]+"
    r"|\d+"
    r"|\S",
    re.S,
)
CS_RE = re.compile(r"\\(?:([A-Za-z@]+)|.)", re.S)
ENV_NAME_RE = re.compile(r"\\(begin|end)\s*\{([^{}]*)\}")
CONTROL_WORD_RE = re.compile(r"\\[A-Za-z@]+$")

_SIZES = [f"\\{size}{suffix}" for size in ("big", "Big", "bigg", "Bigg")
          for suffix in ("", "l", "r", "m")]
DROPPED = frozenset({
    "\\,", "\\;", "\\:", "\\!", "\\>", "\\ ", "\\/", "\\-", "~",
    "\\quad", "\\qquad", "\\enspace", "\\thinspace", "\\negthinspace",
    "\\medspace", "\\thickspace", "\\negmedspace", "\\negthickspace",
    "\\medskip", "\\smallskip", "\\bigskip", *_SIZES,
    "\\left", "\\right", "\\middle",
    "\\displaystyle", "\\textstyle", "\\scriptstyle", "\\scriptscriptstyle",
    "\\allowbreak", "\\nobreak", "\\linebreak", "\\newline", "\\break",
    "\\pagebreak", "\\nopagebreak", "\\smallbreak", "\\medbreak",
    "\\bigbreak", "\\goodbreak", "\\noindent", "\\indent", "\\par",
    "\\hfill", "\\strut", "\\relax", "\\notag", "\\nonumber",
    "\\em", "\\bf", "\\it", "\\bfseries", "\\itshape", "\\upshape",
    "\\normalfont",
})
#: Dropped commands that may carry an optional `[..]` argument, dropped too.
DROPPED_WITH_OPTION = frozenset({"\\linebreak", "\\pagebreak", "\\nopagebreak"})
#: Dropped together with their brace argument (and a star).
DROPPED_WITH_ARGUMENT = frozenset({"\\vspace", "\\hspace"})
UNWRAPPED = frozenset({"\\emph", "\\textbf", "\\textit", "\\boldsymbol",
                       "\\term", "\\tref"})
#: Unwrapped commands whose optional `[..]` argument is dropped with them.
UNWRAPPED_WITH_OPTION = frozenset({"\\term", "\\tref"})
RENAMED = {"\\dfrac": "\\frac", "\\tfrac": "\\frac",
           "\\dbinom": "\\binom", "\\tbinom": "\\binom"}
DISPLAY_ENVS = frozenset({
    "equation", "equation*", "align", "align*", "gather", "gather*",
    "multline", "multline*", "flalign", "flalign*", "alignat", "alignat*",
    "eqnarray", "eqnarray*", "displaymath",
})
LAYOUT_ENVS = frozenset({"aligned", "split", "gathered", "alignedat",
                         "multlined"})
DROPPED_ENVS = frozenset({"sloppypar"})
BRACES = frozenset({"{", "}"})
SENTENCE_END = frozenset({".", "?", "!"})
#: Rendering only: prose tokens written without a space before or after them.
TIGHT_BEFORE = frozenset({".", ",", ";", ":", ")", "]", "!", "?", "'", "}"})
TIGHT_AFTER = frozenset({"(", "[", "{", "`"})
MIN_UNIT_TOKENS = 5
MOVED_SIMILARITY = 0.9
CONTEXT_TOKENS = 4
FAST_LOADER: Any = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

#: One normalised token: its text and its mode, "p" prose, "m" inline math or
#: "d" display math.
Tok = tuple[str, str]


class MathDiffError(Exception):
    """A usage error: an unknown revision, module or unreadable input."""


# --- Reading a revision -------------------------------------------------------


@dataclass
class Revision:
    """The claim files and the macro file of one side of the comparison."""

    name: str
    files: dict[str, str]
    macros_text: str


def run_git(repo: Path, args: list[str], stdin: bytes | None = None) -> bytes:
    """Run one git command in ``repo`` and return its stdout."""
    result = subprocess.run(["git", "-C", str(repo), *args], input=stdin,
                            capture_output=True, check=False)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise MathDiffError(f"git {' '.join(args)} failed: {message}")
    return result.stdout


def cat_blobs(repo: Path, objects: Iterable[str]) -> dict[str, bytes]:
    """Read many blobs with one ``git cat-file --batch`` process."""
    wanted = sorted(set(objects))
    if not wanted:
        return {}
    data = run_git(repo, ["cat-file", "--batch"],
                   stdin=("\n".join(wanted) + "\n").encode("ascii"))
    blobs: dict[str, bytes] = {}
    position = 0
    for _object in wanted:
        newline = data.index(b"\n", position)
        header = data[position:newline].split()
        if len(header) != 3:
            raise MathDiffError(f"git cat-file: {data[position:newline]!r}")
        size = int(header[2])
        start = newline + 1
        blobs[header[0].decode("ascii")] = data[start:start + size]
        position = start + size + 1
    return blobs


def decode(raw: bytes) -> str:
    """Decode a file's bytes as UTF-8 with LF line ends."""
    return raw.decode("utf-8", "replace").replace("\r\n", "\n")


def read_revision(repo: Path, rev: str) -> Revision:
    """Read every claim file and ``spec/macros.tex`` at a git revision."""
    try:
        sha = run_git(repo, ["rev-parse", "--verify", "--quiet",
                             f"{rev}^{{commit}}"]).decode("ascii").strip()
    except MathDiffError as exc:
        raise MathDiffError(f"'{rev}' is not a commit of {repo}") from exc
    listing = run_git(repo, ["ls-tree", "-r", "-z", "--full-tree", sha, "--",
                             "spec/modules", MACROS_PATH])
    entries: list[tuple[str, str]] = []
    for record in listing.split(b"\0"):
        if not record:
            continue
        meta, _, raw_path = record.partition(b"\t")
        parts = meta.split()
        path = raw_path.decode("utf-8")
        if len(parts) == 3 and parts[1] == b"blob" and (
                path == MACROS_PATH or CLAIM_PATH_RE.match(path)):
            entries.append((path, parts[2].decode("ascii")))
    blobs = cat_blobs(repo, (obj for _path, obj in entries))
    files = {path: decode(blobs[obj]) for path, obj in entries
             if path != MACROS_PATH}
    macros = next((decode(blobs[obj]) for path, obj in entries
                   if path == MACROS_PATH), "")
    return Revision(f"{rev} ({sha[:10]})", files, macros)


def read_worktree(repo: Path) -> Revision:
    """Read every claim file and ``spec/macros.tex`` from the files on disk."""
    base = repo / "spec" / "modules"
    files: dict[str, str] = {}
    for path in [*base.glob("*/claims/*.tex"), *base.glob("*/*/claims/*.tex")]:
        rel = path.relative_to(repo).as_posix()
        if CLAIM_PATH_RE.match(rel):
            files[rel] = decode(path.read_bytes())
    macros_path = repo / MACROS_PATH
    macros = decode(macros_path.read_bytes()) if macros_path.is_file() else ""
    return Revision("worktree", dict(sorted(files.items())), macros)


# --- Macros -------------------------------------------------------------------


def parse_macros(text: str) -> dict[str, Macro]:
    r"""Read the simple macro definitions of a ``spec/macros.tex`` text.

    Brace-delimited ``\newcommand``/``\renewcommand``/``\providecommand``
    bodies (over several lines if need be), ``\DeclareMathOperator`` as
    ``\operatorname{..}`` and ``\let``; anything else (``\newlength``, a
    ``\def`` with a parameter text) is left unexpanded.
    """
    macros: dict[str, Macro] = {}
    clean = strip_comments(text)
    for match in DEFINITION_RE.finditer(clean):
        name = definition_name(match)
        if name is None or match.group(6):
            continue
        line = clean.count("\n", 0, match.start()) + 1
        if match.group(5):
            following = re.match(r"\s*=?\s*(\\[A-Za-z@]+|\\.|\S)",
                                 clean[match.end():])
            if following:
                macros[name] = Macro(name, 0, following.group(1), "", line)
            continue
        group = read_group(clean, match.end())
        if group is None:
            continue
        body = group[0]
        if match.group(3):
            star = "*" if match.group(0).startswith("\\DeclareMathOperator*") else ""
            body = f"\\operatorname{star}{{{body}}}"
        nargs = int(match.group(2)) if match.group(2) else 0
        macros[name] = Macro(name, nargs, body, "", line)
    return macros


def read_argument(text: str, index: int) -> tuple[str, int] | None:
    """Read one macro argument: a brace group, else the next single token."""
    group = read_group(text, index)
    if group is not None:
        return group
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] == "}":
        return None
    token = CS_RE.match(text, index)
    if token is not None:
        return token.group(0), token.end()
    return text[index], index + 1


def expand_macros(text: str, macros: dict[str, Macro], rounds: int = 12) -> str:
    """Expand every known macro in ``text`` to a fixed point (bounded)."""
    if not macros:
        return text
    for _round in range(rounds):
        out: list[str] = []
        position = 0
        changed = False
        for match in CS_RE.finditer(text):
            if match.start() < position:
                continue
            name = match.group(1)
            macro = macros.get(name) if name else None
            if macro is None:
                continue
            cursor = match.end()
            args: list[str] = []
            for _argument in range(macro.nargs):
                got = read_argument(text, cursor)
                if got is None:
                    break
                args.append(got[0])
                cursor = got[1]
            if len(args) != macro.nargs:
                continue
            body = substitute(macro.body, tuple(args))
            out.append(text[position:match.start()])
            out.append(body)
            if (CONTROL_WORD_RE.search(body) and cursor < len(text)
                    and text[cursor].isalpha()):
                out.append(" ")
            position = cursor
            changed = True
        out.append(text[position:])
        text = "".join(out)
        if not changed:
            break
    return text


# --- Claims -------------------------------------------------------------------


@dataclass
class RawClaim:
    """One claim file split into its header and body segments."""

    claim_id: str
    module_id: str
    label: str
    path: str
    header: dict[str, Any]
    lead_in: str
    statement: str
    proofs: list[str]
    trailing: str
    notes: list[str] = field(default_factory=list)

    def entries(self, name: str) -> list[str]:
        """Return a list-valued header field as strings (empty if absent)."""
        value = self.header.get(name)
        if isinstance(value, list):
            return [str(item).strip() for item in value]
        return []


def split_option(text: str) -> tuple[str, str]:
    """Split a leading ``[..]`` (balanced, braces respected) off ``text``."""
    stripped = text.lstrip()
    if not stripped.startswith("["):
        return "", text
    depth = brace = 0
    for index, char in enumerate(stripped):
        if char == "{":
            brace += 1
        elif char == "}":
            brace -= 1
        elif brace == 0 and char == "[":
            depth += 1
        elif brace == 0 and char == "]":
            depth -= 1
            if depth == 0:
                return stripped[1:index], stripped[index + 1:]
    return "", text


def claim_identity(path: str) -> tuple[str, str, str]:
    """Return (claim id, module id, label) derived from a claim file's path."""
    match = CLAIM_PATH_RE.match(path)
    if match is None:
        raise MathDiffError(f"{path} is not a claim file path")
    core, sub, stem = match.groups()
    module_id = f"{core}/{sub}" if sub else core
    label = stem.replace("-", ":", 1)
    return f"{module_id}/{label}", module_id, label


def load_header(text: str) -> dict[str, Any]:
    """Parse a header with libyaml when present, else as ``check_claims`` does.

    Speed only: the pure-Python loader was two thirds of a whole-tree run. A
    header the fast loader refuses goes to ``check_claims.load_yaml_mapping``,
    which raises the checker's own ``ClaimFormatError``.
    """
    try:
        raw = yaml.load(text, Loader=FAST_LOADER)     # a safe loader, C or Python
    except yaml.YAMLError:
        return load_yaml_mapping(text)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        return load_yaml_mapping(text)
    return {str(k): v for k, v in raw.items()}


def parse_claim(path: str, text: str) -> RawClaim:
    """Read one claim file's header and cut its body into segments."""
    claim_id, module_id, label = claim_identity(path)
    notes: list[str] = []
    try:
        header_text, body, _line = split_header(text)
        header = load_header(header_text)
    except ClaimFormatError as exc:
        header, body = {}, text
        notes.append(f"header not parsed ({exc.message}); the file is read as body")
    body = strip_comments(body)
    begin = CLAIM_BEGIN_RE.search(body)
    if begin is None:
        notes.append("no claim environment; the whole body is read as lead-in")
        return RawClaim(claim_id, module_id, label, path, header, body, "", [], "",
                        notes)
    end_tag = f"\\end{{{begin.group(1)}}}"
    end = body.find(end_tag, begin.end())
    if end == -1:
        notes.append(f"{end_tag} missing; the statement runs to the end")
        end = len(body)
    _title, statement = split_option(body[begin.end():end])
    rest = body[end + len(end_tag):] if end < len(body) else ""
    proofs: list[str] = []
    between: list[str] = []
    cursor = 0
    for match in PROOF_RE.finditer(rest):
        if match.start() < cursor:
            continue
        between.append(rest[cursor:match.start()])
        stop = rest.find(PROOF_END, match.end())
        stop = len(rest) if stop == -1 else stop
        proofs.append(rest[match.end():stop])
        cursor = min(len(rest), stop + len(PROOF_END))
    between.append(rest[cursor:])
    return RawClaim(claim_id, module_id, label, path, header,
                    body[:begin.start()], statement, proofs, "\n".join(between),
                    notes)


class Resolver:
    """Resolves a reference target to a full claim id within one revision."""

    def __init__(self, claims: dict[str, RawClaim]) -> None:
        """Index the revision's claims by label and assumption short id."""
        self.claims = claims
        self.by_label: dict[str, list[str]] = {}
        self.by_short_id: dict[str, str] = {}
        for claim_id, claim in sorted(claims.items()):
            self.by_label.setdefault(claim.label, []).append(claim_id)
            short_id = str(claim.header.get("short_id") or "").strip()
            if short_id:
                self.by_short_id.setdefault(short_id, claim_id)

    @staticmethod
    def use_entry(claim: RawClaim, entry: str) -> str:
        """Resolve a ``uses``/``mentions`` entry as ``check_claims`` does."""
        return entry if "/" in entry else f"{claim.module_id}/{entry}"

    def target(self, claim: RawClaim, wanted: str) -> str:
        """Return the full claim id a label names from ``claim``, else the label."""
        wanted = ALLOWBREAK_RE.sub("", wanted).strip()
        if "/" in wanted and wanted not in self.claims:
            found = [c for c in self.claims if c.endswith("/" + wanted)]
            if len(found) == 1:
                return found[0]
        if "/" in wanted or wanted.startswith("eq:"):
            return wanted
        local = f"{claim.module_id}/{wanted}"
        if local in self.claims:
            return local
        for entry in [*claim.entries("uses"), *claim.entries("mentions")]:
            full = self.use_entry(claim, entry)
            if full in self.claims and self.claims[full].label == wanted:
                return full
        for short_id in claim.entries("assumes"):
            owner = self.by_short_id.get(short_id)
            if owner is not None and self.claims[owner].label == wanted:
                return owner
        if "/" in claim.module_id:
            parent = f"{claim.module_id.split('/')[0]}/{wanted}"
            if parent in self.claims:
                return parent
        found = self.by_label.get(wanted, [])
        return found[0] if len(found) == 1 else wanted


# --- The map ------------------------------------------------------------------


@dataclass
class ClaimMap:
    """The old-to-new claim map of a rewrite (``--map``)."""

    renames: dict[str, str] = field(default_factory=dict)
    splits: dict[str, list[str]] = field(default_factory=dict)
    merges: dict[str, list[str]] = field(default_factory=dict)
    deleted: list[str] = field(default_factory=list)
    source: str = "none"
    final_renames: dict[str, str] = field(default_factory=dict)
    merged_into: dict[str, str] = field(default_factory=dict)
    split_part_of: dict[str, str] = field(default_factory=dict)

    def prepare(self, old_ids: set[str], new_ids: set[str]) -> None:
        """Fix the map against the two sides before anything is normalised.

        Rename chains (a -> b -> c) are followed to an id present on the new
        side, so a cumulative map applies to any base. A split groups its
        parts only when its old id exists on the old side: under a cumulative
        map whose split happened before the base, both sides already carry
        the parts and must compare them as themselves.
        """
        self.final_renames = {}
        for old, new in self.renames.items():
            seen = {old}
            while new not in new_ids and new in self.renames and new not in seen:
                seen.add(new)
                new = self.renames[new]
            self.final_renames[old] = new
        self.merged_into = {old: new for new, olds in self.merges.items()
                            for old in olds}
        self.split_part_of = {part: old for old, parts in self.splits.items()
                              if old in old_ids for part in parts}

    def canon_old(self, claim_id: str) -> str:
        """Return the canonical form of an id read on the old side."""
        if claim_id in self.final_renames:
            return self.final_renames[claim_id]
        if claim_id in self.splits:
            return f"split({claim_id})"
        return self.merged_into.get(claim_id, claim_id)

    def canon_new(self, claim_id: str) -> str:
        """Return the canonical form of an id read on the new side."""
        origin = self.split_part_of.get(claim_id)
        return f"split({origin})" if origin else claim_id


def load_map(path: str | None, repo: Path) -> tuple[ClaimMap, list[str]]:
    """Read a ``--map`` JSON file; a missing file or key is an empty map."""
    if path is None:
        return ClaimMap(), []
    candidate = Path(path)
    if not candidate.is_file() and not candidate.is_absolute():
        candidate = repo / path
    if not candidate.is_file():
        return ClaimMap(source=f"{path} (not found: empty map)"), [
            f"map file {path} not found; an empty map is used"]
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MathDiffError(f"cannot read map {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise MathDiffError(f"map {path} is not a JSON object")

    def mapping(name: str) -> dict[str, Any]:
        value = data.get(name) or {}
        if not isinstance(value, dict):
            raise MathDiffError(f"map {path}: '{name}' must be an object")
        return value

    renames = {str(k): str(v) for k, v in mapping("renames").items()}
    splits = {str(k): [str(p) for p in v] for k, v in mapping("splits").items()}
    merges = {str(k): [str(p) for p in v] for k, v in mapping("merges").items()}
    deleted = data.get("deleted") or []
    if not isinstance(deleted, list):
        raise MathDiffError(f"map {path}: 'deleted' must be a list")
    return ClaimMap(renames, splits, merges, [str(d) for d in deleted],
                    source=path), []


# --- Normalisation ------------------------------------------------------------


def replace_references(text: str, resolve: Callable[[str], str]) -> str:
    """Turn every reference form into a resolved placeholder (step 2)."""
    def one(match: re.Match[str]) -> str:
        raw = match.group(1) or match.group(2) or match.group(3) or ""
        raw = ALLOWBREAK_RE.sub("", raw)
        targets = [t.strip() for t in raw.split(",") if t.strip()]
        return " " + " ".join(f"{REF_OPEN}{resolve(t)}{REF_CLOSE}"
                              for t in targets) + " "

    return REFERENCE_RE.sub(one, text)


def lex(text: str) -> list[str]:
    """Tokenise LaTeX into control sequences, braces, symbols, words, numbers."""
    tokens: list[str] = []
    for match in TOKEN_RE.finditer(text):
        token = match.group(0)
        if token[0] == REF_OPEN:
            tokens.append(f"REF({token[1:-1]})")
            continue
        env = ENV_NAME_RE.match(token)
        if env is not None:
            tokens.append(f"\\{env.group(1)}{{{env.group(2).strip()}}}")
            continue
        if len(token) == 2 and token[0] == "\\" and token[1].isspace():
            token = "\\ "
        tokens.append(token)
    return tokens


def brace_partners(tokens: Sequence[str]) -> dict[int, int]:
    """Map the index of every ``{`` to the index of its matching ``}``."""
    partners: dict[int, int] = {}
    stack: list[int] = []
    for index, token in enumerate(tokens):
        if token == "{":
            stack.append(index)
        elif token == "}" and stack:
            partners[stack.pop()] = index
    return partners


def option_end(tokens: Sequence[str], index: int) -> int:
    """Return the index after a ``[..]`` starting at ``index``, else ``index``."""
    if index >= len(tokens) or tokens[index] != "[":
        return index
    depth = 0
    for position in range(index, len(tokens)):
        if tokens[position] == "{":
            depth += 1
        elif tokens[position] == "}":
            depth -= 1
        elif tokens[position] == "]" and depth == 0:
            return position + 1
    return index


def drop_presentation(tokens: list[str]) -> list[str]:
    """Drop spacing and sizing, unwrap emphasis, rename fraction forms (step 5)."""
    partners = brace_partners(tokens)
    drop: set[int] = set()
    for index, token in enumerate(tokens):
        if index in drop:
            continue
        nxt = index + 1
        if token in UNWRAPPED:
            drop.add(index)
            if token in UNWRAPPED_WITH_OPTION:
                end = option_end(tokens, nxt)
                drop.update(range(nxt, end))
                nxt = end
            if nxt < len(tokens) and tokens[nxt] == "{" and nxt in partners:
                drop.update((nxt, partners[nxt]))
        elif token in DROPPED:
            drop.add(index)
            if token in ("\\left", "\\right") and nxt < len(tokens) \
                    and tokens[nxt] == ".":
                drop.add(nxt)
            if token in DROPPED_WITH_OPTION:
                drop.update(range(nxt, option_end(tokens, nxt)))
        elif token in DROPPED_WITH_ARGUMENT:
            drop.add(index)
            if nxt < len(tokens) and tokens[nxt] == "*":
                drop.add(nxt)
                nxt += 1
            if nxt < len(tokens) and tokens[nxt] == "{" and nxt in partners:
                drop.update(range(nxt, partners[nxt] + 1))
    return [RENAMED.get(token, token) for index, token in enumerate(tokens)
            if index not in drop]


def assign_modes(tokens: list[str]) -> list[Tok]:
    """Mark tokens prose/math/display; unify displays; drop row marks (step 6)."""
    partners = brace_partners(tokens)
    frames: list[tuple[str, str]] = []
    out: list[Tok] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        kinds = [kind for kind, _name in frames]
        mode = "d" if "display" in kinds else "m" if "inline" in kinds else "p"
        top = kinds[-1] if kinds else ""
        env = ENV_NAME_RE.match(token)
        if token == "$$" or token in ("\\[", "\\]"):
            if frames and frames[-1][0] == "display" and token != "\\[":
                frames.pop()
            elif token != "\\]":
                frames.append(("display", token))
        elif token == "$":
            if frames and frames[-1] == ("inline", "$"):
                frames.pop()
            else:
                frames.append(("inline", "$"))
        elif token == "\\(":
            frames.append(("inline", token))
        elif token == "\\)":
            if frames and frames[-1][0] == "inline":
                frames.pop()
        elif env is not None and env.group(1) == "begin":
            name = env.group(2)
            if name in DISPLAY_ENVS or name in LAYOUT_ENVS:
                frames.append(("display" if name in DISPLAY_ENVS else "layout",
                               name))
                if name in LAYOUT_ENVS:     # aligned[t]; after equation, [ is math
                    index = option_end(tokens, index)
                if name.startswith(("alignat", "alignedat")) and \
                        index < len(tokens) and tokens[index] == "{":
                    index = partners.get(index, index) + 1
            elif name in DROPPED_ENVS:
                frames.append(("dropped", name))
            else:
                frames.append(("env", name))
                out.append((token, mode))
        elif env is not None:
            name = env.group(2)
            position = next((i for i in range(len(frames) - 1, -1, -1)
                             if frames[i][1] == name), None)
            kind = frames[position][0] if position is not None else "env"
            if position is not None:
                del frames[position:]
            if kind == "env":
                out.append((token, mode))
        elif token in ("&", "\\\\") and top in ("display", "layout"):
            if token == "\\\\":
                if index < len(tokens) and tokens[index] == "*":
                    index += 1
                index = option_end(tokens, index)
        elif mode != "p" and len(token) > 1 and (token.isalpha() or token.isdigit()):
            out.extend((char, mode) for char in token)
        else:
            out.append((token, mode))
    return out


def collapse_parentheses(toks: list[Tok]) -> list[Tok]:
    """Drop the bare parentheses around a single reference token."""
    out: list[Tok] = []
    index = 0
    while index < len(toks):
        if (index + 2 < len(toks) and toks[index][0] == "("
                and toks[index + 1][0].startswith("REF(")
                and toks[index + 2][0] == ")"):
            out.append(toks[index + 1])
            index += 3
            continue
        out.append(toks[index])
        index += 1
    return out


def normalise_text(text: str, resolve: Callable[[str], str],
                   macros: dict[str, Macro]) -> list[Tok]:
    """Apply the whole normalisation of the module docstring to one text."""
    if not text.strip():
        return []
    text = replace_references(text, resolve)
    text = LABEL_RE.sub(" ", text)
    text = expand_macros(text, macros)
    return collapse_parentheses(assign_modes(drop_presentation(lex(text))))


def key(toks: Iterable[Tok]) -> list[str]:
    """Return the comparison key of a token sequence: its text without braces."""
    return [text for text, _mode in toks if text not in BRACES]


# --- Normalised claims --------------------------------------------------------


@dataclass
class NormClaim:
    """One claim after normalisation: its segments and canonical header."""

    claim_id: str
    segments: dict[str, list[Tok]]
    header: dict[str, Any]
    notes: list[str]


@dataclass
class Side:
    """One side of the comparison: its claims, resolver, macros and map view."""

    revision: Revision
    claims: dict[str, RawClaim]
    resolver: Resolver
    macros: dict[str, Macro]
    canon: Callable[[str], str]
    cache: dict[str, NormClaim] = field(default_factory=dict)

    def normalised(self, claim_id: str) -> NormClaim:
        """Normalise one claim of this side (memoised)."""
        if claim_id not in self.cache:
            self.cache[claim_id] = normalise_claim(self, self.claims[claim_id])
        return self.cache[claim_id]

    def resolve(self, raw: RawClaim, target: str) -> str:
        """Resolve a reference target of ``raw`` and pass a claim id through the map."""
        found = self.resolver.target(raw, target)
        return self.canon(found) if ":" in found and "/" in found else found

    def signature(self, raw: RawClaim) -> tuple[list[str], list[str]]:
        """Return everything outside the text that normalising ``raw`` reads.

        That is every reference target as resolved and mapped on this side,
        and the canonical ``uses``/``mentions`` entries. Two sides that hold
        the same file text and the same macro file and agree on this
        signature normalise the claim identically, so the comparison may
        skip it (`claim_unchanged`).
        """
        texts = [raw.lead_in, raw.statement, *raw.proofs, raw.trailing,
                 str(raw.header.get("title") or ""),
                 str(raw.header.get("summary") or ""),
                 str(raw.header.get("user_statement") or "")]
        targets = [self.resolve(raw, target.strip())
                   for text in texts for match in REFERENCE_RE.finditer(text)
                   for target in (match.group(1) or match.group(2)
                                  or match.group(3) or "").split(",")
                   if target.strip()]
        edges = [self.canon(self.resolver.use_entry(raw, entry))
                 for name in sorted(ID_FIELDS) for entry in raw.entries(name)]
        return targets, edges


def build_side(revision: Revision, canon: Callable[[str], str],
               parsed: dict[tuple[str, str], RawClaim]) -> Side:
    """Parse every claim of a revision and index it for resolution.

    ``parsed`` is shared between the two sides: a file whose path and text are
    the same on both is parsed once.
    """
    claims: dict[str, RawClaim] = {}
    for path, text in revision.files.items():
        claim = parsed.get((path, text))
        if claim is None:
            claim = parsed[(path, text)] = parse_claim(path, text)
        claims[claim.claim_id] = claim
    return Side(revision, claims, Resolver(claims), parse_macros(revision.macros_text),
                canon)


def claim_unchanged(old_side: Side, new_side: Side, claim_id: str) -> bool:
    """Whether a claim normalises identically on both sides without normalising.

    True when both sides hold the same parsed file (same path, same text),
    the same macro file, and the same resolved references and edges.
    """
    old, new = old_side.claims[claim_id], new_side.claims[claim_id]
    return (old is new
            and old_side.revision.macros_text == new_side.revision.macros_text
            and old_side.signature(old) == new_side.signature(new))


def normalise_claim(side: Side, raw: RawClaim) -> NormClaim:
    """Normalise every segment and the meaningful header fields of one claim."""
    def resolve(target: str) -> str:
        return side.resolve(raw, target)

    def norm(text: str) -> list[Tok]:
        return normalise_text(text, resolve, side.macros)

    segments = {
        "title": norm(str(raw.header.get("title") or "")),
        "summary": norm(str(raw.header.get("summary") or "")),
        "user_statement": norm(str(raw.header.get("user_statement") or "")),
        "lead-in": norm(raw.lead_in),
        "statement": norm(raw.statement),
        "proof": [tok for proof in raw.proofs for tok in norm(proof)],
        "trailing": norm(raw.trailing),
    }
    header: dict[str, Any] = {}
    for name in HEADER_FIELDS:
        if name in ID_FIELDS:
            header[name] = sorted({side.canon(side.resolver.use_entry(raw, entry))
                                   for entry in raw.entries(name)})
        elif name in LIST_FIELDS:
            header[name] = sorted({" ".join(entry.split())
                                   for entry in raw.entries(name)})
        else:
            value = raw.header.get(name)
            header[name] = None if value is None or str(value).strip() == "" \
                else str(value).strip()
    return NormClaim(raw.claim_id, segments, header, list(raw.notes))


# --- Pairing ------------------------------------------------------------------


@dataclass
class Pair:
    """Old claims and the new claims they became, and how."""

    relation: str      # same, renamed, split, merged, deleted, removed, added
    old_ids: list[str]
    new_ids: list[str]

    def ids(self) -> list[str]:
        """Return every id of the pair, old then new."""
        return [*self.old_ids, *self.new_ids]

    def title(self) -> str:
        """Return the ``old -> new`` heading of the pair."""
        old = ", ".join(f"`{i}`" for i in self.old_ids) or "(none)"
        new = ", ".join(f"`{i}`" for i in self.new_ids) or "(none)"
        if self.relation == "same":
            return old
        return f"{old} -> {new} ({self.relation})"


def pair_claims(old_ids: set[str], new_ids: set[str],
                cmap: ClaimMap) -> tuple[list[Pair], list[str]]:
    """Pair old and new claims through the (prepared) map.

    Returns the pairs and the map's problems: entries naming a claim the side
    they refer to does not have. A problem never fails the run by itself; an
    old claim it leaves unpaired is reported as removed, which does.
    """
    problems: list[str] = []
    merged_into = cmap.merged_into
    # New ids a map entry claims, counted only for entries whose old side is
    # here: under a cumulative map an entry applied before the base names a
    # new id that exists on both sides and pairs with itself.
    mapped_new = (
        {new for old, new in cmap.final_renames.items()
         if old in old_ids and new != old}
        | {p for old, parts in cmap.splits.items() if old in old_ids for p in parts}
        | {new for new, olds in cmap.merges.items()
           if any(o in old_ids for o in olds)})
    rename_targets = set(cmap.renames.values())
    for old in sorted(cmap.renames):
        if old not in old_ids and old not in rename_targets:
            problems.append(f"renames: '{old}' is not a claim of the old side")
    for old, parts in sorted(cmap.splits.items()):
        if old not in old_ids:
            problems.append(f"splits: '{old}' is not a claim of the old side")
        problems.extend(f"splits: part '{p}' of '{old}' is not a claim of the "
                        "new side" for p in parts if p not in new_ids)
    for new, olds in sorted(cmap.merges.items()):
        if new not in new_ids:
            problems.append(f"merges: '{new}' is not a claim of the new side")
        problems.extend(f"merges: '{o}' (into '{new}') is not a claim of the old "
                        "side" for o in olds if o not in old_ids)
    problems.extend(f"deleted: '{d}' is not a claim of the old side"
                    for d in cmap.deleted if d not in old_ids)
    pairs: list[Pair] = []
    used_old: set[str] = set()
    used_new: set[str] = set()

    def add(relation: str, olds: list[str], news: list[str]) -> None:
        pairs.append(Pair(relation, olds, news))
        used_old.update(olds)
        used_new.update(news)

    for old in sorted(old_ids):
        if old in used_old:
            continue
        if old in cmap.final_renames and cmap.final_renames[old] != old:
            new = cmap.final_renames[old]
            if new in new_ids and new not in used_new:
                add("renamed", [old], [new])
            else:
                problems.append(f"renames: '{old}' -> '{new}', which is not a "
                                "claim of the new side")
                add("removed", [old], [])
        elif old in cmap.splits:
            add("split", [old], [p for p in cmap.splits[old]
                                 if p in new_ids and p not in used_new])
        elif old in merged_into:
            new = merged_into[old]
            olds = [o for o in cmap.merges[new] if o in old_ids and o not in used_old]
            add("merged", olds, [new] if new in new_ids and new not in used_new
                else [])
        elif old in cmap.deleted:
            add("deleted", [old], [])
        elif old in new_ids and old not in mapped_new:
            add("same", [old], [old])
        else:
            add("removed", [old], [])
    for new in sorted(new_ids - used_new):
        add("added", [], [new])
    return pairs, problems


# --- Comparison ---------------------------------------------------------------


@dataclass
class SegmentDiff:
    """How one segment of a pair differs."""

    segment: str
    fails: bool
    brace_only: bool
    ops: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Moved:
    """A sentence or display that left one claim segment for another."""

    text: str
    from_id: str
    from_segment: str
    to_id: str
    to_segment: str
    similarity: float


@dataclass
class PairReport:
    """Everything the report says about one pair."""

    pair: Pair
    headers: list[dict[str, Any]] = field(default_factory=list)
    segments: list[SegmentDiff] = field(default_factory=list)
    moved_out: list[Moved] = field(default_factory=list)
    moved_in: list[Moved] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def fails(self) -> bool:
        """Whether this pair makes the run exit 1 (a deletion always does)."""
        return (self.pair.relation in ("deleted", "removed", "added")
                or any(s.fails for s in self.segments))

    @property
    def status_change(self) -> dict[str, Any] | None:
        """Return the status header change, if there is one."""
        return next((h for h in self.headers if h["field"] == "status"), None)

    def worth_reporting(self) -> bool:
        """Whether the pair appears in the report at all."""
        return bool(self.pair.relation != "same" or self.headers or self.segments
                    or self.moved_out or self.moved_in or self.notes)


def needs_space(left: Tok, right: Tok) -> bool:
    """Whether a rendering puts a space between two tokens.

    Prose words are separated, math is written tight (a space only where TeX
    needs one, after a control word before a letter), and a switch between
    prose and math is separated, all but before closing punctuation.
    """
    a, b = left[0], right[0]
    if a.startswith("REF(") or b.startswith("REF("):
        return True
    if left[1] == "p" or right[1] == "p":
        if b in TIGHT_BEFORE or a in TIGHT_AFTER or b == "{" or "-" in (a, b):
            return False
        contraction = a == "'" and b in ("s", "t", "re", "ve", "ll", "d")
        return "\\_" not in (a, b) and not contraction
    return bool(CONTROL_WORD_RE.match(a)) and b[0].isalpha()


def render(toks: Sequence[Tok]) -> str:
    """Render tokens as readable LaTeX-like text."""
    parts: list[str] = []
    for index, tok in enumerate(toks):
        if index and needs_space(toks[index - 1], tok):
            parts.append(" ")
        parts.append(tok[0])
    return "".join(parts)


def op_kind(toks: Iterable[Tok]) -> str:
    """Label a difference math, prose or both, from its tokens' modes."""
    modes = {"math" if mode in ("m", "d") else "prose" for _text, mode in toks}
    return "math+prose" if len(modes) == 2 else modes.pop() if modes else "prose"


def diff_ops(old: list[Tok], new: list[Tok]) -> list[dict[str, str]]:
    """Return the token-level differences of two segments, braces-only ops skipped."""
    matcher = difflib.SequenceMatcher(None, [t for t, _ in old], [t for t, _ in new],
                                      autojunk=False)
    ops: list[dict[str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        gone, came = old[i1:i2], new[j1:j2]
        if all(t in BRACES for t, _ in [*gone, *came]):
            continue
        ops.append({
            "op": tag,
            "kind": op_kind([*gone, *came]),
            "old": render(gone),
            "new": render(came),
            "before": render(old[max(0, i1 - CONTEXT_TOKENS):i1]),
            "after": render(old[i2:i2 + CONTEXT_TOKENS]),
        })
    return ops


def compare_segment(name: str, old: list[Tok], new: list[Tok]) -> SegmentDiff | None:
    """Compare one segment; None when equal including braces."""
    if key(old) == key(new):
        if [t for t, _ in old] != [t for t, _ in new]:
            return SegmentDiff(name, fails=False, brace_only=True)
        return None
    return SegmentDiff(name, fails=name in FAILING_SEGMENTS, brace_only=False,
                       ops=diff_ops(old, new))


def group_header(claims: list[NormClaim], own: set[str]) -> dict[str, Any]:
    """Combine the canonical headers of a claim group (one claim, or split parts)."""
    combined: dict[str, Any] = {}
    for name in HEADER_FIELDS:
        if name in LIST_FIELDS:
            values: set[str] = set()
            for claim in claims:
                values.update(claim.header[name])
            combined[name] = sorted(values - own if name in ID_FIELDS else values)
        else:
            distinct = sorted({claim.header[name] for claim in claims
                               if claim.header[name] is not None})
            combined[name] = " | ".join(distinct) if distinct else None
    return combined


def compare_headers(old: dict[str, Any], new: dict[str, Any]) -> list[dict[str, Any]]:
    """List the header fields that differ between two combined headers."""
    changes: list[dict[str, Any]] = []
    for name in HEADER_FIELDS:
        if old[name] == new[name]:
            continue
        change: dict[str, Any] = {"field": name, "old": old[name], "new": new[name]}
        if name in LIST_FIELDS:
            change["added"] = sorted(set(new[name]) - set(old[name]))
            change["removed"] = sorted(set(old[name]) - set(new[name]))
        changes.append(change)
    return changes


def concatenated(claims: list[NormClaim], segment: str) -> list[Tok]:
    """Concatenate one segment over a claim group, in order."""
    return [tok for claim in claims for tok in claim.segments[segment]]


def compare_pair(pair: Pair, old_side: Side, new_side: Side) -> PairReport:
    """Compare one pair's segments and headers."""
    report = PairReport(pair)
    if pair.relation == "same" and claim_unchanged(old_side, new_side,
                                                   pair.old_ids[0]):
        raw = old_side.claims[pair.old_ids[0]]
        report.notes.extend(f"{raw.claim_id}: {note}" for note in raw.notes)
        return report
    olds = [old_side.normalised(i) for i in pair.old_ids]
    news = [new_side.normalised(i) for i in pair.new_ids]
    for claim in [*olds, *news]:
        report.notes.extend(f"{claim.claim_id}: {note}" for note in claim.notes)
    if pair.relation in ("deleted", "removed", "added"):
        return report
    for segment in SEGMENTS:
        found = compare_segment(segment, concatenated(olds, segment),
                                concatenated(news, segment))
        if found is not None:
            report.segments.append(found)
    own = ({old_side.canon(i) for i in pair.old_ids}
           | {new_side.canon(i) for i in pair.new_ids})
    report.headers = compare_headers(group_header(olds, own), group_header(news, own))
    return report


# --- Moved text ---------------------------------------------------------------


@dataclass(frozen=True)
class Unit:
    """A normalised sentence or display of one claim segment."""

    claim_id: str
    segment: str
    key: tuple[str, ...]
    text: str


def units(claim_id: str, segment: str, toks: list[Tok]) -> list[Unit]:
    """Cut a segment into displays and sentences long enough to track."""
    pieces: list[list[Tok]] = []
    current: list[Tok] = []
    for tok in toks:
        if current and (tok[1] == "d") != (current[-1][1] == "d"):
            pieces.append(current)
            current = []
        current.append(tok)
        if tok[1] == "p" and tok[0] in SENTENCE_END:
            pieces.append(current)
            current = []
    if current:
        pieces.append(current)
    return [Unit(claim_id, segment, tuple(key(piece)), render(piece))
            for piece in pieces if len(key(piece)) >= MIN_UNIT_TOKENS]


def similarity(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    """Return the difflib ratio of two token tuples, cheap bounds first."""
    if left == right:
        return 1.0
    total = len(left) + len(right)
    if total == 0 or 2 * min(len(left), len(right)) / total < MOVED_SIMILARITY:
        return 0.0
    matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
    if matcher.real_quick_ratio() < MOVED_SIMILARITY:
        return 0.0
    if matcher.quick_ratio() < MOVED_SIMILARITY:
        return 0.0
    return matcher.ratio()


def unmatched(mine: list[Unit], theirs: list[Unit]) -> list[Unit]:
    """Return the units of ``mine`` with no similar unit in ``theirs``."""
    exact = {unit.key for unit in theirs}
    return [unit for unit in mine if unit.key not in exact
            and not any(similarity(unit.key, other.key) >= MOVED_SIMILARITY
                        for other in theirs)]


def find_moved(reports: list[PairReport], old_side: Side, new_side: Side) -> int:
    """Attach moved sentences and displays to the pairs they left and reached."""
    removed: list[tuple[PairReport, Unit]] = []
    added: list[tuple[PairReport, Unit]] = []
    for report in reports:
        pair = report.pair
        changed = {s.segment for s in report.segments if not s.brace_only}
        if pair.relation in ("deleted", "removed", "added"):
            changed = set(SEGMENTS)
        for segment in sorted(changed):
            mine = [u for i in pair.old_ids for u in
                    units(i, segment, old_side.normalised(i).segments[segment])]
            theirs = [u for i in pair.new_ids for u in
                      units(i, segment, new_side.normalised(i).segments[segment])]
            removed.extend((report, u) for u in unmatched(mine, theirs))
            added.extend((report, u) for u in unmatched(theirs, mine))
    count = 0
    for origin, unit in removed:
        best: tuple[float, PairReport, Unit] | None = None
        for target, other in added:
            score = similarity(unit.key, other.key)
            if score >= MOVED_SIMILARITY and (best is None or score > best[0]):
                best = (score, target, other)
        if best is None:
            continue
        score, target, other = best
        moved = Moved(unit.text, unit.claim_id, unit.segment, other.claim_id,
                      other.segment, round(score, 3))
        origin.moved_out.append(moved)
        if target is not origin or other.segment != unit.segment:
            target.moved_in.append(moved)
        count += 1
    return count


# --- The run ------------------------------------------------------------------


@dataclass
class Result:
    """A whole comparison, ready to render."""

    old_name: str
    new_name: str
    map_source: str
    module: str | None
    counts: dict[str, int]
    reports: list[PairReport]
    flags: list[str]
    problems: list[str]

    @property
    def exit_code(self) -> int:
        """Return 1 when a statement or proof differs or a claim is unmapped."""
        return 1 if any(report.fails for report in self.reports) else 0


def compare(old: Revision, new: Revision, cmap: ClaimMap,
            module: str | None) -> Result:
    """Compare two revisions through a map, optionally under one module."""
    parsed: dict[tuple[str, str], RawClaim] = {}
    old_side = build_side(old, cmap.canon_old, parsed)
    new_side = build_side(new, cmap.canon_new, parsed)
    if module is not None and not any(
            in_scope(claim.module_id, module)
            for side in (old_side, new_side) for claim in side.claims.values()):
        raise MathDiffError(f"--module '{module}' has no claims on either side")
    cmap.prepare(set(old_side.claims), set(new_side.claims))
    pairs, problems = pair_claims(set(old_side.claims), set(new_side.claims), cmap)

    def scoped(claim_id: str) -> bool:
        return module is None or in_scope(claim_id.rsplit("/", 1)[0], module)

    pairs = [p for p in pairs if any(scoped(i) for i in p.ids())]
    if module is not None:
        problems = [p for p in problems
                    if any(scoped(i) for i in re.findall(r"'([^']+)'", p))]
    reports = [compare_pair(pair, old_side, new_side) for pair in pairs]
    moved = find_moved(reports, old_side, new_side)
    shown = [r for r in reports if r.worth_reporting()]
    relations = [r.pair.relation for r in reports]
    counts = {
        "old_claims": sum(len(p.old_ids) for p in pairs),
        "new_claims": sum(len(p.new_ids) for p in pairs),
        **{relation: relations.count(relation) for relation in
           ("same", "renamed", "split", "merged", "deleted", "removed", "added")},
        "statements_differ": sum(any(s.segment == "statement" and s.fails
                                     for s in r.segments) for r in reports),
        "proofs_differ": sum(any(s.segment == "proof" and s.fails
                                 for s in r.segments) for r in reports),
        "other_segments_differ": sum(1 for r in reports for s in r.segments
                                     if not s.fails and not s.brace_only),
        "brace_only": sum(1 for r in reports for s in r.segments if s.brace_only),
        "header_changes": sum(len(r.headers) for r in reports),
        "status_changes": sum(r.status_change is not None for r in reports),
        "moved": moved,
    }
    flags: list[str] = []
    for report in shown:
        change = report.status_change
        if change is not None:
            flags.append(f"status changed: {report.pair.title()}: "
                         f"{change['old']} -> {change['new']}")
    for report in shown:
        relation = report.pair.relation
        if relation in ("removed", "added"):
            flags.append(f"{relation} without a map entry, unaccounted (fails): "
                         f"{report.pair.title()}")
        elif relation == "deleted":
            flags.append("deleted (declared in map) (fails): "
                         f"`{report.pair.old_ids[0]}`")
    return Result(old.name, new.name, cmap.source, module, counts, shown, flags,
                  problems)


# --- Rendering ----------------------------------------------------------------


def code(text: str) -> str:
    """Wrap text in a Markdown code span that survives backticks inside it."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * (longest + 1)
    return f"{fence} {text} {fence}" if text else "(empty)"


def render_op(op: dict[str, str]) -> str:
    """Render one token difference as a wdiff-style Markdown line."""
    middle = []
    if op["old"]:
        middle.append(f"[-{op['old']}-]")
    if op["new"]:
        middle.append(f"{{+{op['new']}+}}")
    context = " ".join(part for part in (op["before"], " ".join(middle), op["after"])
                       if part)
    return f"- {op['kind']}: {code('... ' + context + ' ...')}"


def render_header(change: dict[str, Any]) -> str:
    """Render one header change as a Markdown line."""
    name = change["field"]
    if name in LIST_FIELDS:
        parts = [f"+{code(v)}" for v in change["added"]]
        parts += [f"-{code(v)}" for v in change["removed"]]
        return f"- `{name}`: " + ", ".join(parts)
    line = f"- `{name}`: {code(str(change['old']))} -> {code(str(change['new']))}"
    return line + ("  **(status change)**" if name == "status" else "")


def render_markdown(result: Result) -> str:
    """Render the result as the Markdown report."""
    c = result.counts
    lines = [
        f"# math_diff: {result.old_name} -> {result.new_name}",
        "",
        f"Map: {result.map_source}. Scope: {result.module or 'all modules'}.",
        "",
        "| | count |",
        "| --- | --- |",
        f"| claims compared, old / new | {c['old_claims']} / {c['new_claims']} |",
        f"| unchanged ids / renamed / split / merged | {c['same']} / {c['renamed']}"
        f" / {c['split']} / {c['merged']} |",
        f"| deleted, declared in map (fail) | {c['deleted']} |",
        f"| removed / added without a map entry (fail) | {c['removed']} / "
        f"{c['added']} |",
        f"| statements that differ (fail) | {c['statements_differ']} |",
        f"| proofs that differ (fail) | {c['proofs_differ']} |",
        f"| other segments that differ (reported) | {c['other_segments_differ']} |",
        f"| segments differing in braces only (noted) | {c['brace_only']} |",
        f"| header changes / status changes | {c['header_changes']} / "
        f"{c['status_changes']} |",
        f"| moved sentences or displays | {c['moved']} |",
        "",
    ]
    if result.exit_code:
        lines.append("**Result: a statement or proof differs after normalisation, "
                     "or a claim was deleted or is unaccounted for (exit 1).**")
    else:
        lines.append("**Result: no statement or proof differs after "
                     "normalisation (exit 0).**")
    if result.flags or result.problems:
        lines += ["", "## Flags", ""]
        lines += [f"- **{flag}**" for flag in result.flags]
        lines += [f"- map: {problem}" for problem in result.problems]
    if not result.reports:
        lines += ["", "No differences after normalisation."]
        return "\n".join(lines) + "\n"
    lines += ["", "## Claims"]
    for report in result.reports:
        lines += ["", f"### {report.pair.title()}"]
        if report.pair.relation in ("renamed", "split", "merged") and not (
                report.headers or report.segments or report.moved_out
                or report.moved_in or report.notes):
            lines += ["", "No differences after normalisation."]
        if report.headers:
            lines += ["", "Header:"]
            lines += [render_header(change) for change in report.headers]
        for segment in report.segments:
            if segment.brace_only:
                lines += ["", f"{segment.segment}: equal; differs in grouping "
                          "braces only (noted)."]
                continue
            verdict = "**differs (fails)**" if segment.fails else \
                "differs (reported, does not fail)"
            lines += ["", f"{segment.segment}: {verdict}", ""]
            lines += [render_op(op) for op in segment.ops]
        for moved in report.moved_out:
            lines.append(f"- moved: {code(moved.text)} from `{moved.from_id}` "
                         f"({moved.from_segment}) to `{moved.to_id}` "
                         f"({moved.to_segment}), similarity {moved.similarity}")
        for moved in report.moved_in:
            if moved in report.moved_out:
                continue
            lines.append(f"- moved here: {code(moved.text)} from `{moved.from_id}` "
                         f"({moved.from_segment}) to `{moved.to_id}` "
                         f"({moved.to_segment}), similarity {moved.similarity}")
        lines += [f"- note: {note}" for note in report.notes]
    return "\n".join(lines) + "\n"


def moved_json(moved: Moved) -> dict[str, Any]:
    """Return a moved unit as JSON."""
    return {"text": moved.text, "from": moved.from_id,
            "from_segment": moved.from_segment, "to": moved.to_id,
            "to_segment": moved.to_segment, "similarity": moved.similarity}


def render_json(result: Result) -> str:
    """Render the result as JSON, the machine-readable twin of the Markdown."""
    data = {
        "old": result.old_name,
        "new": result.new_name,
        "map": result.map_source,
        "module": result.module,
        "exit_code": result.exit_code,
        "counts": result.counts,
        "flags": result.flags,
        "map_problems": result.problems,
        "claims": [{
            "relation": r.pair.relation,
            "old": r.pair.old_ids,
            "new": r.pair.new_ids,
            "fails": r.fails,
            "headers": r.headers,
            "segments": [{"segment": s.segment, "fails": s.fails,
                          "brace_only": s.brace_only, "ops": s.ops}
                         for s in r.segments],
            "moved_out": [moved_json(m) for m in r.moved_out],
            "moved_in": [moved_json(m) for m in r.moved_in],
            "notes": r.notes,
        } for r in result.reports],
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


# --- Command line -------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="python -m harness.math_diff",
        description="Show which claim statements, proofs and other segments "
                    "differ between two revisions after normalising away "
                    "presentation (PRINCIPLES.md section 6).")
    parser.add_argument("old", metavar="OLD", help="the base git revision")
    parser.add_argument("new", metavar="NEW", nargs="?", default=None,
                        help="the git revision to compare with OLD")
    parser.add_argument("--worktree", action="store_true",
                        help="compare OLD with the claim files on disk")
    parser.add_argument("--map", default=None, metavar="PATH",
                        help="JSON old-to-new claim map: renames, splits, "
                             "merges, deleted (full claim ids)")
    parser.add_argument("--module", default=None, metavar="ID",
                        help="only claims of this module (a core includes its "
                             "submodules)")
    parser.add_argument("--json", action="store_true",
                        help="print JSON instead of Markdown")
    parser.add_argument("--repo", default=".", help="repository root (default: .)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the comparison and print the report; return the exit code."""
    args = build_parser().parse_args(argv)
    if (args.new is None) == (not args.worktree):
        print("error: give exactly one of NEW or --worktree", file=sys.stderr)
        return 2
    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"error: --repo {args.repo} is not a directory", file=sys.stderr)
        return 2
    try:
        cmap, map_notes = load_map(args.map, repo)
        old = read_revision(repo, args.old)
        new = read_worktree(repo) if args.worktree else read_revision(repo, args.new)
        result = compare(old, new, cmap, args.module)
    except MathDiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result.problems[:0] = map_notes
    output = render_json(result) if args.json else render_markdown(result)
    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.stdout.flush()
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
