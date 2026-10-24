r"""Staleness guard: the report's plain-words prose against the claims it paraphrases.

WHY THIS EXISTS. The report's prose is mostly automated and not at risk of
going stale when contracts change: the report quotes a claim's own title, summary and
``user_statement`` from the closure table, which ``harness.generate_claim_closure``
regenerates from the claim headers. Two kinds of report prose are written by
hand and only paraphrase claims: the run-tier sentences of
``src/certiqs_key/runs/report/explain.py`` (each listed in its ``PARAPHRASES``
with the claims it leans on) and the glossary texts of
``src/certiqs_key/runs/report/glossary.yaml`` (each naming its claim in
``see``). Nothing regenerates those, so when a claim's statement changes the
prose may silently say something the claim no longer says.

THE GUARD. For every claim the prose paraphrases, ``data/
report_paraphrase_pins.json`` holds a digest of the claim's STATEMENT (the
body of its theorem environment, read as ``harness.math_diff.parse_claim``
reads it: header excluded, comments stripped, whitespace collapsed). When a
statement changes, this test fails and names the sentences and glossary
terms to re-read. A summary or a proof that changes alone does not trip it.

AFTER RE-READING (and correcting the prose where it no longer agrees), refresh
the pins by running this test with ``CERTIQS_UPDATE_PARAPHRASE_PINS=1``::

    CERTIQS_UPDATE_PARAPHRASE_PINS=1 python -m pytest \\
        tests/unit/test_report_paraphrase_pins.py -o addopts=""

which rewrites the pin file; commit it with the prose, saying what was re-read.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from certiqs_key.runs.report.explain import PARAPHRASES
from certiqs_key.runs.report.glossary import terms

ROOT = Path(__file__).resolve().parents[2]
PINS = Path(__file__).resolve().parent / "data" / "report_paraphrase_pins.json"
UPDATE = "CERTIQS_UPDATE_PARAPHRASE_PINS"

#: Run in a subprocess from the repository root: ``tests/harness`` is itself a
#: package named ``harness`` and shadows the tools in this process (the reason
#: tests/harness loads them by path).
_DIGESTS = """
import hashlib, json, sys
from pathlib import Path
from harness.math_diff import parse_claim
out = {}
given = json.loads(sys.stdin.read())
for path in given["paths"]:
    text = (Path(given["root"]) / path).read_text(encoding="utf-8")
    raw = parse_claim(path, text)
    statement = " ".join(raw.statement.split())
    out[path] = hashlib.sha256(statement.encode("utf-8")).hexdigest()
print(json.dumps(out))
"""


def _claim_path(claim_id: str) -> str:
    """Return a claim file's repository path (``module[/sub]/claims/kind-label``)."""
    module, _, label = claim_id.rpartition("/")
    kind, _, name = label.partition(":")
    return f"spec/modules/{module}/claims/{kind}-{name}.tex"


def _digests(claims: list[str], root: Path = ROOT) -> dict[str, str]:
    """Return the statement digest of every claim, read by harness.math_diff."""
    paths = [_claim_path(claim) for claim in claims]
    done = subprocess.run(
        [sys.executable, "-c", _DIGESTS], cwd=ROOT,
        input=json.dumps({"root": str(root), "paths": paths}),
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    found: dict[str, str] = json.loads(done.stdout)
    return {claim: found[_claim_path(claim)] for claim in claims}


def _prose() -> dict[str, list[str]]:
    """Return, per paraphrased claim, the prose that paraphrases it."""
    found: dict[str, list[str]] = {}
    for sentence, claims in PARAPHRASES.items():
        for claim in claims:
            found.setdefault(claim, []).append(f"explain.py {sentence}")
    for term in terms():
        if term.see_claim is not None:
            found.setdefault(term.see_claim, []).append(
                f"glossary.yaml '{term.term}'"
            )
    return {claim: sorted(names) for claim, names in sorted(found.items())}


def _current() -> dict[str, dict[str, object]]:
    prose = _prose()
    digests = _digests(list(prose))
    return {
        claim: {"statement_sha256": digests[claim], "paraphrased_by": names}
        for claim, names in prose.items()
    }


def test_every_paraphrased_claim_has_a_file() -> None:
    for claim in _prose():
        assert (ROOT / _claim_path(claim)).is_file(), claim


def test_no_paraphrased_statement_changed_since_its_prose_was_read() -> None:
    current = _current()
    if os.environ.get(UPDATE):
        PINS.parent.mkdir(parents=True, exist_ok=True)
        PINS.write_text(json.dumps(current, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    pinned = json.loads(PINS.read_text(encoding="utf-8"))
    changed = [
        f"{claim}: re-read " + ", ".join(map(str, entry["paraphrased_by"]))  # type: ignore[call-overload]
        for claim, entry in current.items()
        if claim not in pinned
        or pinned[claim]["statement_sha256"] != entry["statement_sha256"]
    ]
    unused = [f"{claim}: pinned but no longer paraphrased"
              for claim in sorted(set(pinned) - set(current))]
    assert not changed and not unused, (
        "a claim the report's prose paraphrases changed (or the prose names a "
        "new claim, or no longer names a pinned one). Re-read the prose named, "
        f"correct it if needed, then set {UPDATE}=1 and rerun this test to "
        "refresh the pins:\n" + "\n".join([*changed, *unused])
    )


def test_a_changed_statement_is_caught_and_a_changed_header_is_not(
    tmp_path: Path,
) -> None:
    claim = "meat-core/thm:keylength"
    relative = _claim_path(claim)
    text = (ROOT / relative).read_text(encoding="utf-8")
    header_end = text.index("% ---", text.index("% ---") + 1)
    copy = tmp_path / relative
    copy.parent.mkdir(parents=True)
    (before,) = _digests([claim]).values()

    copy.write_bytes(text.replace("% summary:", "% summary: edited", 1).encode())
    assert _digests([claim], tmp_path)[claim] == before

    label = "\\label{thm:keylength}"
    body = text[header_end:]
    edited = body.replace(label, label + " edited", 1)
    assert edited != body
    copy.write_bytes((text[:header_end] + edited).encode())
    assert _digests([claim], tmp_path)[claim] != before
