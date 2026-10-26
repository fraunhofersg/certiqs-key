# Pitfalls

Traps of this tree and its tooling, each of which costs a run or an edit
when met unawares. It is a note, not a tool, and adds no check. Each entry
says what happens and what to do instead.

## Committing when several agents share one clone

- **Never build a commit's file list from `git status`.** In a shared clone,
  `git status` also lists other sessions' uncommitted work, and a list built
  from it (even a filtered one) stages their in-progress files. List the paths
  your change wrote, or stage per directory you own. If it happens anyway, do
  not reset: restore the other session's paths in the index alone (`git
  restore --staged --source=<commit>~1 -- <paths>`), commit, and tell the
  session. Its working tree is untouched.

## Writing files

- **Write tracked files with LF.** Python's `open(path, "w")` is text mode and
  writes CRLF on Windows, so a script that rewrites a tracked file silently
  converts every line; on a frozen oracle that reads as the wholesale rewrite
  PRINCIPLES.md §2.3 exists to catch. Pass `newline="\n"` (or write bytes).
  `.gitattributes` (`* text=auto eol=lf`) is correct and fixes checkouts, not
  what a tool writes.
- **Modified but identical.** A file can show as modified while being
  byte-identical to `HEAD` (a stale stat cache): `git update-index
  --really-refresh -- <paths>` clears that and discards nothing. A file that
  really holds CRLF was written by a tool: rewrite its bytes in place. Never
  repair either with `git checkout --`: in a shared clone it discards other
  agents' edits.
- **Long paths.** On Windows a copy of the repository under a deep folder
  (a temporary directory) cannot be assembled: a group graph's file name runs
  to a hundred characters, the path passes Windows' 260, and writing it fails
  with `FileNotFoundError`. Put copies at a short path, such as the clone's
  git-ignored `tmp/`.
- **Backslashes through the shell.** The Bash tool mangles backslashes in
  heredocs, and `sed` in Git Bash fails silently on patterns containing them;
  a Python heredoc that touches LaTeX turns `\c` into a control character and
  the edit misses. Write the script to a file and run it.

## YAML (claim headers, open items, `module.yaml`)

- A colon inside an unquoted plain scalar (a history line, a human's words
  written by a script) breaks the file.
- No backslash before a quote in a claim header's `notes` or in a
  double-quoted history line; both the header parser and PyYAML refuse it.
  Quote a human's words with single quotes and keep double quotes out of them.
  Writing them through `repr` chooses double quotes on an apostrophe.
- Duplicate keys are silent: PyYAML keeps the last one.

## Running checks

- `pytest -q` prints its summary twice under the `pyproject.toml` addopts;
  use `-o addopts=""` for one readable summary.
- When several agents share one clone, a transient red in `tests/harness` or
  `pytest` is usually another agent's in-flight edit: find which file before
  touching anything, and run a script that rewrites claim files or an
  interface only when no other agent holds them.
- `assemble_contract --check` judges PDF freshness by modification time for
  uncommitted files and by last-commit time for committed ones, so a fresh
  clone passes without a rebuild. A source committed after its PDF still
  counts as current when the part the PDF reads is unchanged since the PDF's
  commit; for `refs/references.bib` that part is the entries the tex cites,
  so registering a reference no contract cites leaves every PDF current, and
  for a digest's `contract.tex` it is the labels and what numbers them, so a
  changed "Used by" line stales the contract PDF but not the digest.
  `latexmk -c` leaves `contract.bbl`, which is git-ignored.
- Accepting a claim can dangle a sibling's use of it:
  `python -m harness.check_claims --dependents <id>` lists who rests on it.
- A test never encodes the repository's calendar (a date that will pass).
- A mutation check (change a frozen value, expect a red, restore) can be
  fooled by a stale `.pyc` when the restored file has the same size and the
  same modification second; run it with `PYTHONDONTWRITEBYTECODE=1` and
  `-p no:cacheprovider`.
- A bit-for-bit pin (`float.hex()` of a result) holds only on the platform
  that recorded it. Another BLAS (Accelerate on macOS arm64, not Windows'
  build) rounds a product differently in its last bit, a Frank-Wolfe run
  carries that to about 1e-8 (a pairwise run on Linux x86_64 OpenBLAS: up to
  1e-4 in the bracket), and a one-ulp defect can land on a different entry
  and trip a different condition. Such pins are therefore keyed by platform
  (`tests/support/platform_pins.py`): each platform records its own values,
  and an unrecorded platform, case or field skips with a message that names
  its key and prints this run's values to paste, so record yours there rather
  than overwriting another platform's. The key does not make them portable:
  OpenBLAS picks its kernel by CPU at run time, and on one machine
  `OPENBLAS_CORETYPE` alone changes every pinned value. The pairwise rule
  moves most, because its vertex choices are near-ties that the last bit
  decides. The values stay sound (every bracket lies below every platform's
  objective), so a pin that fails on another machine is expected and is not a
  defect. The pinned tests therefore carry the `pins` marker, which the
  default tier deselects (`tests/conftest.py`); run `pytest -m pins` on the
  machine that recorded them. A snapshot compares a value that is rounding noise (a
  validation residual of order 1e-16) by whether it lies within its
  tolerance, not by its digits, and a floating-point evaluation (the
  receiver's photon-number blocks and port Grams) within four ulps of one.
- On macOS and Linux the venv's interpreter is `.venv/bin/python`, not the
  README's `.venv/Scripts/python`.
- The venv's package is an editable install of the main clone's `src/`, so
  Python run from a `git worktree` imports the MAIN clone's `certiqs_key`,
  not the worktree's. A run record's `provenance.engine` is read from the
  imported package's checkout, so a worktree run then records the main
  clone's commit and its other agents' uncommitted edits as `git_dirty`. For
  tests or runs from a worktree set `PYTHONPATH="<worktree>/src;<worktree>"`
  (`;` on Windows, `:` elsewhere) and check
  `python -c "import certiqs_key; print(certiqs_key.__file__)"`; for a run
  meant as evidence also check that a finished record names the worktree's
  HEAD with `git_dirty` false.

## Reading sources

- Read a source paper's PDF with `pdftotext -layout -enc UTF-8`; the default
  mode drops the arrows of Rényi entropies and relation subscripts. A PDF that
  claims a password is often not encrypted.
- Verify what a subagent reports against the tree, and resolve an open item
  against the tree before starting it: both go stale faster than they read.
