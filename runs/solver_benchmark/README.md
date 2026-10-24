# Solver benchmark gym

A developer tool; not needed to compute a key rate.

Compare candidate solvers on the same public protocol declarations, with
failures, preparation, search and certification included in the evidence.
This tool proposes no change to the certified evaluator or production defaults.

From the repository's development environment:

```powershell
python -m runs.solver_benchmark.run --profile fast --methods fw pairwise factor entropy corrective auto --out build/solver-gym/baseline
python -m runs.solver_benchmark.summarize build/solver-gym/baseline --out build/solver-gym/baseline-summary
```

For a quick screen, plan six attempts with a 300-second aggregate allowance:

```powershell
python -m runs.solver_benchmark.run --methods auto factor --only qubit-control optical-loss bbm-realistic --seconds 10 --total-seconds 300 --out build/solver-gym/quick
```

The aggregate cap can leave later attempts unstarted; timeout cleanup can
briefly exceed the allowance. Use a fresh output directory for a new screen.

The fast profile uses 30 seconds of search per case; slow uses 180 seconds and
adds cutoff and conditioning stress cases. `--only` selects case IDs.
`--dry-run` lists tasks and the maximum aggregate allowance without running
them. `--seconds`, `--process-seconds`, `--total-seconds`, `--memory-gib`, and
`--repeats` set explicit limits. The default aggregate allowance is two hours;
tasks outside it remain visibly unstarted. One numerical worker runs at a time,
with BLAS/OpenMP thread counts set to one. Windows workers use a committed-memory
job limit and kill-on-close; POSIX workers use `RLIMIT_AS` and a process group.
The parent enforces the process wall-time limit, including setup and shutdown.

The profiles cover qubit, optical BB84, BBM92 and decoy BB84; encoded and licensed
routes; realistic loss, efficiencies and dark counts; near-one orders; tiny
source weights; and high photon cutoffs. Diagnostic cases retain known failure
regimes. Each case states its purpose in `cases.py`. Every paired variant uses
the same exact endpoint rule with the `enclosure` tail evaluator,
which can conservatively widen undecided endpoint brackets. The sweep evaluator
is unsuitable for the large round counts here. Estimated error correction uses
the same declared model and `f_ec` and its preparation time is charged.

## Read the results

Prefer coverage of certified results, then attained certified bound/key at a
fixed total cost. Report failures, refusals, timeouts and unstarted tasks beside
successful results. A lower diagnostic search gap does not establish a better
certified key, and is not a certified optimality gap. Bounds on the searched and
reference declarations are separate quantities. A scalar `target_bound` in a
case is comparable only to that case's `target_declaration` (default
`reference_companion`; qubit declarations ordinarily use `searched`).
An operational `target_key_length` instead accepts any valid reported certified
declaration by default. A non-null `target_declaration` restricts either target
kind to that declaration; a null bound-target declaration retains the default.
The reported target time is the final observed certification time, an upper
bound on time to target, not an interpolated first crossing. Use a budget ladder
to study time-quality tradeoffs.

`candidate_supported` distinguishes requested-method capability from whole-run
certificate coverage. An unsupported method can still obtain a useful final
certificate through reference-companion polish; preserve that result without
crediting the requested solver with a target hit. `candidate_methods_run` names
the executed search attempts, while reference polish remains in the evidence.
For an outer `alpha_search`, use `target_key_length`, never `target_bound`:
entropy terms at different orders are not the same optimization objective.
Only one target kind may be set. Selected alpha and its search trace are retained.
The search allowance applies to each evaluated order in an outer alpha search;
the hard process cap and reported elapsed time cover the entire run.

Each attempt retains configuration, ordinary compressed run record, final
iterate where available, diagnostic log, completion status and compact summary.
The CSV is a view; JSON retains the supporting diagnostics. The manifest names
the git revision and planned cases, resource limits and order seed. Use a clean
tracked checkout for publishable timings. Resume requires the same revision,
configuration, allowance and plugin source; interrupted attempts remain
interrupted rather than silently rerunning. A fresh output directory starts a
new experiment. A shortened final process allowance is recorded explicitly.
Summary `elapsed_kind` distinguishes measured parent time from an interrupted
attempt's conservatively imputed process cap. Aggregate charged-time medians
must not describe that imputation as a measured completion time.

## Ordered warm chains

`--warm-chain` seeds each variant from its own immediately preceding case in
the supplied case-list order, separately within each repeat. Variant order is
still shuffled within each case; repeats begin cold. `--only` filters the list
without changing its order. Use an explicit `--cases` list of compatible
declarations, for example an ordered loss sweep:

```powershell
python -m runs.solver_benchmark.run --cases loss-chain.json --methods factor auto pairwise --warm-chain --seconds 20 --out build/solver-gym/loss-chain
```

The canonical manifest records each planned `warm_predecessor` ID. At launch,
`task.json` records the actual `warm_start` path and `warm_start_reason`. The
first case is explicitly cold (`chain_first`); a missing completion, an
unsuccessful predecessor, or a missing final iterate also produces an explicit
cold start. The runner never skips backward to an older successful seed or
borrows from another variant/repeat. A completed predecessor need not have a
positive certified key to supply a candidate seed.

The worker's seed loader, hash recording, feasible-set/row admission
and interior mixing remain in force. An incompatible or malformed available
seed can refuse the run; the runner does not silently retry it cold. Only the
final numerical iterate is transferred, not the selected alpha or optimizer
state. Summaries expose the requested seed metadata and the current run's
selected `alpha`; a seed request is not proof that admission succeeded.

Every predecessor remains an ordinary charged task, including failed or
interrupted predecessors. `warm_chain_elapsed_seconds` in the summary adds the
recorded worker costs of that variant/repeat's whole case prefix, including
cold fallbacks; it is absent where a required cost is unknown. Per-task
`elapsed_seconds` remains the incremental cost. For a warm chain,
`certified_target_observed_seconds` uses the charged prefix, so the seed is
never free in a target-time comparison. Other variants' work remains visible in their own rows and the matrix
total. Resume keeps completed and interrupted task files unchanged and requires
the same chain plan and mode. An interrupted task is charged its recorded
effective process cap; a task file without that field is conservatively
charged the matrix's full process cap.

## Experimental variants

`--cases cases.json` accepts a list with the same shape as `cases.py`.
`--variants variants.json` accepts entries such as:

```json
[
  {"id": "baseline", "method": "factor", "oracle": "qics"},
  {"id": "experiment", "method": "factor", "oracle": "qics",
   "plugin": "path/to/experiment.py"}
]
```

A standalone experimental file may expose `install()` to replace candidate
search helpers, and/or `create_oracle()` to supply a linear oracle. Its source
is copied into the run directory before execution. This is an explicit local
research seam, not a security sandbox or a production solver registry. Inspect
the patch boundary: experiments must not alter the assessor, certifier, scoring,
declaration or assurance labels. Finalists require fresh-process reassessment
without their experimental patches before adoption recommendations. Ordinary
run records remain the authority for what the engine reported.

A variant may include an `environment` object for recorded experimental
parameters. Numerical-library thread variables always retain the runner's cap.
A `capture` file may expose `install(path)` to observe the actual certifier
inputs in `certifier-inputs.jsonl` for later fixed-point replay. Its source is
also copied into the run directory and its overhead is charged. The observer
must return the production result unchanged; it is not an alternative verifier.

`native_solver_settings: true` preserves the instance's ordinary solver
settings instead of applying the gym's method, oracle, iteration, gap and
search-budget overrides. Give that variant `method: "native"`; the actual
method is in its run record. Its reported search budget is absent and the
external process cap still applies. Physics, statistics and estimated error
correction remain the declared gym case: this compares native solver effort,
not the instance's literal factory-default demonstration.

`literal_defaults: true` measures that demonstration: the instance's
`default_config()` runs unchanged (rounds, alpha, statistics, tail evaluator,
error-correction leakage and solver settings), so give its case only `id`,
`instance` and `reason`, with no `f_ec`. An optional `method` replaces only
`solver.method`; omit it, or give `null`, to keep the document's method. The
`--seconds` allowance does not apply; only the external process cap does.

Plugin snapshots cover the named file, not its transitive imports. Use the
recorded clean git revision for the whole checkout when reproducing a plugin
with local helpers; a copied top-level file alone is not a portable experiment.

No optional numerical backend is installed by this tool. Experimental backend
dependencies belong in a disposable environment until justified for adoption.
