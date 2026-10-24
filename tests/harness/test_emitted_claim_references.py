r"""Every claim reference written into a string of the shipped code resolves.

MOTIVATION, AND THE ERROR CLASS IT CATCHES. Refusal details, witnesses, reason
strings and report text name claims as free text -- ``"the proof of Proposition
prop:rule-exact (vi)"``, ``equation="eq:Lfss: ..."``,
``"meat-core/frank-wolfe/req:first-order-withdrawal"`` -- and those strings
leave the engine: they are written into run records, refusal records and the
key-rate report, where a reader follows them to a contract. Nothing resolved
them. ``harness.check_claims`` resolves the references inside claim files, and
``harness.relabel`` rewrites a code string only where it can prove the label
names the renamed claim; a claim that was retired or split, or a label typed
wrongly in the first place, left the string pointing at nothing, and no tool
said so. Two such strings reached the frontend's captured fixtures (an equation
label no claim file defines in the wpfss witness, and "Theorem prop:rule-exact"
for a proposition), and a sweep of the
code found more, among them the report's link for the first-order hypotheses to
a remark that no longer states the withdrawal.

WHAT IT CHECKS. Every string constant of ``src/``, ``runs/`` and
``instances/`` (parsed with ``ast``, so comments and code are not read) is
searched for a reference ``kind:label`` or ``module/kind:label``, ``kind``
one of the claim kinds of ``spec/claim-format.md`` or ``eq``/``tab``. It
resolves when

- with a module prefix: a module whose id is the prefix, or ends in
  ``/<prefix>`` (the run record writes module-relative ids such as
  ``frank-wolfe/cor:fo-keylength``), has a claim file of that label or a
  claim body that defines it with ``\label``;
- without one: some claim file anywhere has that label or defines it.

A title-case word written directly before the reference that names a kind
("Theorem", "Remarks", "Eq.") must name the reference's own kind:
"Theorem prop:rule-exact" is the error this guards against. A lower-case
or upper-case word is prose ("a theorem (prop:chain)", "a THEOREM") and is
not read as a kind word.

EMITTED STRINGS AND DOCSTRINGS. A string constant that is a statement of its
own (a module, class or function docstring, or an attribute's docstring) is
documentation, not output; every other constant can reach a record, a refusal
or a report. Both are checked and both must resolve: a dangling name in a
docstring points a reader of the code at nothing just as surely. The two are
separate tests so that a failure says which kind of text it is in.

WHAT IT DOES NOT CHECK. Short assumption ids (``A-SNAP``) are not its
subject; comments are not parsed; and whether the claim a string names is
the RIGHT claim for the sentence around it is a reviewer's judgement
(PRINCIPLES.md section 3, "agents own the mechanical"), never this test's.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCANNED = ("src", "runs", "instances")

#: The claim kinds (``spec/claim-format.md``), plus the two label prefixes a
#: claim body defines for its displays.
KINDS = ("thm", "lem", "prop", "cor", "def", "ass", "rem", "ex", "fact", "req",
         "eq", "tab")

#: A word that names a kind, singular or plural, as prose writes it before a
#: reference.
KIND_WORDS: dict[str, str] = {
    "theorem": "thm", "theorems": "thm",
    "lemma": "lem", "lemmas": "lem", "lemmata": "lem",
    "proposition": "prop", "propositions": "prop",
    "corollary": "cor", "corollaries": "cor",
    "definition": "def", "definitions": "def",
    "assumption": "ass", "assumptions": "ass",
    "remark": "rem", "remarks": "rem",
    "example": "ex", "examples": "ex",
    "fact": "fact", "facts": "fact",
    "requirement": "req", "requirements": "req",
    "equation": "eq", "equations": "eq", "eq.": "eq", "eqs.": "eq",
    "table": "tab", "tables": "tab",
}

#: A reference. A label a docstring wraps after one of its hyphens
#: (``cor:least-eigenvalue-over-`` / ``enclosure``) is read joined.
REFERENCE_RE = re.compile(
    r"(?<![\w/:.-])"
    r"(?P<prefix>(?:[a-z0-9][a-z0-9-]*/)*)"
    r"(?P<kind>" + "|".join(KINDS) + r")"
    r":(?P<label>[A-Za-z0-9](?:[A-Za-z0-9:]|-(?:\n[ \t]*(?=[a-z0-9]))?)*)"
)
PRECEDING_WORD_RE = re.compile(r"([A-Za-z]+\.?)[\s`'\"(]*$")
LABEL_RE = re.compile(r"\\label\{([^}]*)\}")


@dataclass(frozen=True)
class Finding:
    """One reference that does not resolve, or carries the wrong kind word."""

    path: str
    line: int
    reference: str
    problem: str
    docstring: bool

    def __str__(self) -> str:
        """Return the finding as ``path:line: 'reference': problem``."""
        return f"{self.path}:{self.line}: {self.reference!r}: {self.problem}"


def claim_labels() -> dict[str, set[str]]:
    """Map each module id to the labels its claim files carry or define."""
    modules: dict[str, set[str]] = {}
    base = ROOT / "spec" / "modules"
    for path in sorted(base.rglob("claims/*.tex")):
        module_id = path.parent.parent.relative_to(base).as_posix()
        labels = modules.setdefault(module_id, set())
        kind, _, slug = path.stem.partition("-")
        labels.add(f"{kind}:{slug}")
        labels.update(LABEL_RE.findall(path.read_text(encoding="utf-8")))
    return modules


def _docstring_constants(tree: ast.AST) -> set[int]:
    """Return the ids of the string constants that are statements of their own."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            found.add(id(node.value))
    return found


def _strings(path: Path) -> Iterator[tuple[int, str, bool]]:
    """Yield (line, text, is_docstring) for every string constant of a file."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    docstrings = _docstring_constants(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value, id(node) in docstrings


def _resolve(prefix: str, label: str, modules: dict[str, set[str]],
             everywhere: set[str]) -> str:
    """Return why ``prefix``/``label`` does not resolve, or "" when it does."""
    if not prefix:
        return "" if label in everywhere else "no claim file has or defines it"
    wanted = prefix.rstrip("/")
    candidates = [module for module in modules
                  if module == wanted or module.endswith("/" + wanted)]
    if not candidates:
        return f"no module {wanted!r}"
    if any(label in modules[module] for module in candidates):
        return ""
    return f"module {candidates[0]!r} has no claim file that has or defines it"


def findings(paths: list[Path] | None = None) -> list[Finding]:
    """Return every unresolved reference and wrong kind word in the scanned code."""
    modules = claim_labels()
    everywhere = set().union(*modules.values())
    if paths is None:
        paths = [path for top in SCANNED for path in sorted((ROOT / top).rglob("*.py"))]
    out: list[Finding] = []
    for path in paths:
        rel = (path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT)
               else path.name)
        for line, text, docstring in _strings(path):
            for match in REFERENCE_RE.finditer(text):
                kind = match.group("kind")
                written = re.sub(r"\s+", "", match.group("label"))
                label = kind + ":" + written.rstrip(":-")
                reference = match.group("prefix") + label
                problem = _resolve(match.group("prefix"), label, modules, everywhere)
                word = PRECEDING_WORD_RE.search(text[: match.start()])
                named = (KIND_WORDS.get(word.group(1).lower())
                         if word and word.group(1).istitle() else None)
                if word is not None and named is not None and named != kind:
                    problem = (problem + "; " if problem else "") + (
                        f"the word {word.group(1)!r} names a {named}, "
                        f"the label a {kind}")
                if problem:
                    out.append(Finding(rel, line, reference, problem, docstring))
    return out


def test_every_claim_reference_in_an_emitted_string_resolves() -> None:
    """Strings that reach a record, a refusal or a report name real claims."""
    bad = [str(finding) for finding in findings() if not finding.docstring]
    assert not bad, (
        "claim references in emitted strings that do not resolve against "
        "spec/modules/**/claims, or carry the wrong kind word:\n  "
        + "\n  ".join(bad))


def test_every_claim_reference_in_a_docstring_resolves() -> None:
    """Docstrings name real claims, so a reader of the code finds them."""
    bad = [str(finding) for finding in findings() if finding.docstring]
    assert not bad, (
        "claim references in docstrings that do not resolve against "
        "spec/modules/**/claims, or carry the wrong kind word:\n  "
        + "\n  ".join(bad))


def test_the_resolver_catches_what_it_exists_for(tmp_path: Path) -> None:
    """A dangling label, a wrong kind word and an unknown module are caught."""
    probe = tmp_path / "probe.py"
    probe.write_text(
        '"""Docstring naming Remark rem:no-such-remark."""\n'
        'A = "eq:no-such-equation: P_S o Lambda_C"\n'
        'B = "the proof of Theorem prop:rule-exact (vi)"\n'
        'C = "no-such-module/def:freq"\n'
        'D = "Proposition prop:rule-exact and statistics/def:freq"\n'
        'E = "meat-core/frank-wolfe/req:first-order-withdrawal"\n'
        'F = "frank-wolfe/req:first-order-withdrawal"\n',
        encoding="utf-8")
    found = findings([probe])
    by_reference = {(f.reference, f.docstring): f.problem for f in found}
    assert set(by_reference) == {
        ("rem:no-such-remark", True),
        ("eq:no-such-equation", False),
        ("prop:rule-exact", False),
        ("no-such-module/def:freq", False),
    }, found
    assert "names a thm" in by_reference[("prop:rule-exact", False)]
