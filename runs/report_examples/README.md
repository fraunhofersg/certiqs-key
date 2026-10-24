# Key-rate report examples

**These are run-tier snapshots, not oracles.** A snapshot proves that the
report renders deterministically and that a change to the rendering was
seen, not that the rendering is right. The key lengths in these records are
whatever the engine computed at the commit each record names; they pin
nothing, and no oracle value is ever taken from them. Correctness of the
report is held by hand-written expectations: `tests/unit/test_report_build.py`,
`test_report_checks.py`, `test_sweep_report.py`, `test_report_render.py`, the
reconciliation tests of the route-exact assumption set, and the two schemas.

**Every file below this folder is generated and never hand-edited.** Each
example folder is deleted and rewritten whole by `generate.py`.

## What is here

| folder | instance | configuration | solver step limit | outcome |
| --- | --- | --- | --- | --- |
| `bb84/` | `bb84` | the instance's `default_config` | 5 | key length |
| `bbm92/` | `bbm92` | the instance's `default_config` | 10 | key length |
| `decoy_bb84/` | `decoy_bb84` | the instance's `default_config` | 20 | key length |
| `optical_bb84/` | `optical_bb84` | the instance's `default_config` | 5 | key length |
| `refused/` | `bb84` | `default_config` with `eps_auth = 0.5` | 5 | refused at `solve`, `security_statement_vacuous` |
| `alpha-search-bb84/` | `bb84` | `default_config` with the opt-in outer alpha search (`alpha - 1` in [1e-4, 0.1], three grid points and one refinement: four runs) | 5 per run | key length, at the alpha the search chose |
| `sweep-bb84/` | `bb84` | `model.qber` 1/50 and 1/25, then 3/50 with `eps_auth = 0.5` | 5 | two key lengths, one refused point |
| `document-qubit_bb84_y/` | custom document `qubit_bb84_y` | the bb84 template with the Y basis in place of X, at its `default_config` | 5 | key length |
| `document-optical_bb84_port_grams/` | custom document `optical_bb84_port_grams` | the optical_bb84 template with Bob's receiver declared by its port Grams, at its `default_config` | 5 | key length |
| `document-bbm92_holder_b/` | custom document `bbm92_holder_b` | the bbm92 template with `key.holder: B`, at its `default_config` | 10 | key length |
| `document-bbm92_choice_at_bob/` | custom document `bbm92_choice_at_bob` | the bbm92 template with the test coin's `choice_weighting` at Bob's station only (the transcript's senders swapped, so the coin's holder announces first), at its `default_config` | 10 | key length |

**Compare key lengths across examples with care.** Every example stops its
Frank-Wolfe search at the step limit in the table, far from convergence, and
the limits differ (the paragraph below says why). Two examples' key lengths
therefore differ by their search budgets as well as by their protocols and
devices; each report gives its own limit under "Your inputs" (Engine
settings, `solver.max_iterations`) and the gap at which its search stopped
under the appendix's Diagnostics. None of these key lengths is a converged
figure for its protocol.

The configurations are declared in `generate.py` (`EXAMPLES`), which also
fixes each example's expected outcome and refuses to write one whose run
came out otherwise. The `document-*` examples run a CUSTOM protocol
document, built in `generate.py` from a
packaged template (`instances/<id>/protocol.yaml`) customised as its header
says and then edited; their reports show the items the document declared
itself ("Declared in the protocol document, not derived by the engine" in the
result, and the "vouched for by you" rows under the assumptions), and their
records carry the document itself under `payload.protocol_document`. The
two `document-bbm92_*` examples are entanglement-based runs whose roles the
other examples lack: Bob holds the key, or the only public choice is declared
at the second station, so that A-COIN is emitted from that factor. The `bb84`
and `decoy_bb84` reports list their templates' own declarations the same way.
Every run uses `SolverSettings(max_iterations=5)` (a
handful of Frank-Wolfe iterations: a record of every stage, nowhere near
convergence) and the QICS linear oracle (`QicsSectorChoiOracle`); everything
else is the instance's default. The two `document-bbm92_*` examples and
`bbm92` take ten iterations (`EB_DOCUMENT_SOLVER`), and
`decoy_bb84` twenty (`PM_LONG_SOLVER`): at five its first-order bound is
still negative and the key length 0, and the generator refuses to write a
key-length example whose key length is 0 (the outcome alone cannot see it).
Each record carries its instance block
(`InstanceIdentity(DESCRIPTOR, PARAMETERS)`), so the report's "Your inputs"
gives every input its meaning.

Files in a run folder: `record.json` (or `record.json.gz`), `report.md`,
`report.html`, and the record excerpts every record pointer of the report
links to, `record.md` and `record.html`. In the sweep
folder: `run-NNNN.json`, `sweep.md`, `sweep.html` and each point's report
under `points/`, with its excerpts as `points/NNNN.record.{md,html}`.
Repository paths a report prints link relative to the file, as the contract
links do, in the Markdown. The HTML is the page the project's Pages site
serves (`harness/build_pages_site.py`, whose `ALLOW` list names what the site
serves): there a repository path the site does not serve (an instance README, `spec/architecture.md`) is printed in
code, not linked (`--pages-site`). A record larger than
512 KiB is written `.json.gz`; every committed file stays under 1 MiB.
Contract links are relative to the file (`../../../spec/modules/...`), so
they open the committed PDFs from a checkout.

## Which engine wrote them

Each record names its engine in `payload.provenance.engine`
(`git_commit`, `git_dirty`). The records are one full generation at record
schema 0.46.0, run on a clean checkout of
`3203843199ea99a9d152155416440f0d3de5dbb2` on Windows (Python 3.14), so they
carry `git_dirty: false`; the reports and excerpts are rendered from them at
report schema 0.36.0.

The platform matters for the trailing digits. At these few Frank-Wolfe
iterations the brackets carry last-bit differences of the BLAS, so a
generation on another platform (Linux x86_64 with OpenBLAS, for one) can move
h_low, h_lb, h_cert and some key lengths in their trailing digits, by less
than 1e-3 relative, with no engine change; compare a regeneration's numbers
with these on the same platform. `tests/integration/test_report_examples.py`
checks that this README names the commit of every record; a regeneration
updates the commit, the schema and the platform above.

## How to regenerate

```
python -m runs.report_examples.generate                  # re-run every example (QICS; one to two minutes), then render
python -m runs.report_examples.generate --instance bb84  # only bb84's examples (bb84, refused, sweep-bb84)
python -m runs.report_examples.generate --instance qubit_bb84_y  # one document example, by its document's id
python -m runs.report_examples.generate --render-only    # re-render the committed records, no solve
python -m runs.report_examples.generate --check          # compare a fresh rendering, write nothing; exit 1 on a difference
```

- A **record schema bump** needs a full re-run (the snapshot test requires
  every committed record at the current version, even where the report still
  reads the older one).
- A change to the **report code** or to a cited claim's title or summary in
  the **claim-closure table** needs `--render-only`: the report quotes the
  table, so such a change moves the snapshots without any run.
- Run a full generation from a clean checkout where possible (a fresh clone
  of the commit), so that `git_dirty` is false and no uncommitted change
  reaches the records.

A single report can be rendered by hand with the same bytes:
`python -m certiqs_key.runs.report runs/report_examples/bb84/record.json
--format md --out <folder>/report.md --contract-base ../../../ --repo-base
../../../` (the HTML adds `--pages-site`; a sweep: the `run-*.json` files
with `--out <folder>`); the snapshot test checks that this agrees with the
generator.

## Review rule

The commit that changes a snapshot says why, and the reviewer reads the
snapshot diff, not only the code diff. A snapshot diff that moves a number
with no engine change is a defect to investigate, never a regeneration to
accept.
