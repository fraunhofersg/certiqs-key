# AGENTS.md

CERTIQS-KEY computes fixed-length MEAT key rates for QKD protocols with every
assumption traceable.

This file is what an agent needs before it reads anything else. It restates
nothing: each rule has one home, linked below.

## Read in this order

1. `PRINCIPLES.md`: what the project wants and why. Every plan is aligned
   against it. It wins over every other file.
2. `state/DASHBOARD.md`: decisions waiting on the maintainer, the status map, open
   findings, the tasks in order. It is generated from `state/open-items/`.
3. The umbrella open item of the effort you join, if any (an open `task` whose brief
   carries the effort's plan and status). There is no separate plan file.
4. `spec/claim-format.md` before touching any claim file; `spec/modules.yaml`
   before touching any module; `spec/style.md` before rewriting contract prose
   (the editor role; a drafter needs only its mechanical part, which the
   checker enforces).

## The rules that are not negotiable

- **Humans accept, agents propose.** Only the maintainer moves a claim to `accepted`
  or an implementation batch to accepted.
- **Git plus human review is the ledger.** Do not build locks, hash chains,
  receipts or successor records. Do not add a check without writing its
  motivation into the tool's header and `harness/README.md`.
- **Cite only registered ref-ids with locators** from `refs/index.json`.
  A result without a registered source is derived in full and tagged
  `newly-derived`.
- **An independent verifier sees artefacts only**, on a different model family
  from the drafter, and its brief never names the drafter's reasoning.
  `harness/roles/verifier.md` says how "different model family" is judged and
  what to do when a runtime reaches only one.
- **Put the model choice to the human directing the session at its start.**
  When the session's work will run a drafter/implementer and reviewer loop,
  ask at the outset which models take each role, with a recommended pairing
  and its reason (separation under PRINCIPLES.md §2.2, cost, quality), before
  the first such agent runs. Skip the question only when no such loop is
  needed or the prompt already names the models.
- **Commit with explicit paths.** Never `git add -A` while another agent may
  be writing. Commit messages say what and why.

## Conventions (the default way, not rules)

- **Record a decision where it takes effect.** Write the effect into the file
  it changes; the commit that does so quotes the maintainer's words and ends with the
  trailer `Decided-by: <maintainer's name>` (above `Co-Authored-By`), written only for a
  decision the maintainer made in their own words. A decision queued as an open item
  also closes that item with a `decision:` field. Prefer this to an
  append-only decision log, which repeats the file and the commit while it
  grows (PRINCIPLES.md §2.4-2.5). This is about project decisions; logs of
  other kinds, such as a key-rate run's record, are a separate question.
- **Name the command, never its count.** Normative prose (claim files,
  `interface.yaml`, `design.md`) names claims and names the
  `check_claims` command that computes a fact about the graph; it never
  restates a number the command returns (`spec/claim-format.md` §4.5). A dated
  list of claims is a snapshot; the command is the authority.
- **Ask the maintainer with options and a recommended one**, through the question tool
  where the runtime has one, and gather the questions of a run at its end
  rather than stopping mid-pipeline; a question that must wait becomes an
  open item with `needs_human: true`.
- **Re-ask on conflict.** If an answer of theirs conflicts with work done since
  the question was put, do not record it: put the question again with the
  current options and the conflict stated; re-ask rather than naively record.
- **Interview before a structural change** (a module or submodule added,
  split, moved or retired): the maintainer aligns on the intended structure first.
  The batch that makes the change updates the prose describing it, `spec/architecture.md`, `spec/future-scope.md`, `spec/notation.md` and
  `harness/README.md`, and greps for the old names so the documentation stays
  current.
- **After every claim change** run `python -m harness.assemble_contract --all`
  (every contract with its digest, the graphs and the overview, rebuilt only
  where something changed; all tracked), then `python -m harness.dashboard`.
- **Review scope.** Claim changes and the mathematics in `src/` get the
  independent artefacts-only review; run-tier code, tests, reports and
  instance docs get ordinary review by the driver and no report of their own.
  A presentational rewrite (PRINCIPLES.md §6) gets the artefacts-only
  equivalence review instead of a soundness round, reading
  `harness.math_diff`'s report.
- **Nothing lives only in a scratchpad or an agent's memory.** An effort's
  plan and handoff is its umbrella open item plus its `reports/` folder.
- **Known traps** (CRLF from Python, YAML quoting, backslashes through the
  shell, transient reds in a shared clone, reading source PDFs):
  `harness/PITFALLS.md`.

## Layout

| Path | Contents | Rules |
| --- | --- | --- |
| `PRINCIPLES.md` | the manifesto | changes in the open, human-accepted |
| `spec/` | architecture, notation, future scope, module registry, claim files | normative; `spec/modules/<id>/contract.tex` is generated |
| `src/certiqs_key/` | module code, one package per module of `spec/modules.yaml` | downward imports only |
| `instances/`, `runs/` | protocol data; composition and result records | where a user docks |
| `harness/` | tools, role files; each tool with a written motivation | ordinary code review |
| `state/` | dashboard, open items (an effort's plan is its umbrella item) | human entry point; current status, history is git |
| `reports/` | a note on how the claims are reviewed (`reports/README.md`) and one design brief; the review reports and working papers are kept internally | never authority |
| `refs/` | `index.json` (the only citable universe: bibliographic data and versions) | read-only |
| `tests/` | unit, golden, oracles, property, integration, harness | oracles are never regenerated from code |

## Tool commands

```
python -m harness.check_claims [--module <id>] [--status] [--dependents <id>] [--graph out.dot]   # also the spec/style.md rules the checker can see
python -m harness.check_symbols [--module <id>] [--unused]   # macros used and undefined; part-A expansions against spec/notation.md
python -m harness.assemble_contract --all [--check] [--no-pdf]   # every contract and digest (tex and PDF), the graphs and spec/overview/; only what changed
python -m harness.assemble_contract <module-id> [--check] [--no-pdf]   # one module's contract, digest and graphs, PDFs rebuilt
python -m harness.dashboard [--check]   # regenerates state/DASHBOARD.md from the open items and claims
python harness/generate_bibliography.py [--check]
python -m harness.generate_claim_closure [--check]   # the claim-closure table a run record reads (package data)
python -m harness.check_history [--check] [--strict] [--summary] [--category C]   # history in shipped files; exceptions in harness/history_allow.yaml
python -m harness.math_diff OLD (NEW | --worktree) [--map relabel-map.json] [--module <id>]   # what mathematics changed, presentation normalised away
python -m harness.relabel OLD_ID NEW_ID [--dry-run] [--map-out PATH]   # rename, re-kind or move a claim everywhere it is named
python -m certiqs_key.runs.report RECORD... [--format md|html|json] [--out PATH] [--sweep]   # the key-rate report of a run record or a sweep
python -m runs.report_examples.generate [--instance ID] [--render-only | --check]   # the committed report examples (snapshots, not oracles)
pytest tests/harness -q -o addopts=""
ruff check harness tests src instances runs
mypy harness ; mypy src instances runs   # one import graph each; `mypy src` alone does not see instances/
git log --grep "^Decided-by:"      # every recorded human decision
```

The environment is rebuilt from `pyproject.toml` (`README.md`, "Development").
