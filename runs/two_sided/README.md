# Two-sided single-point records

`python -m runs.two_sided.point` runs exactly one point and writes the standard
run record to a new output directory. The record contains the full `RunConfig`,
supplier provenance, stage outcomes, a completed or refused result, and the
solver's gap diagnostics. Existing output directories are refused.
Before running, it writes `config.json` and `provenance.json` (code revision,
tracked modifications, Python/platform and the error-correction purpose).
An interrupted directory without `record.json` is an unfinished attempt.

This measurement recipe explicitly defaults to `--endpoint-rule bernstein`
for large round counts. `--endpoint-rule exact` selects the exact rule.
The choice is recorded in the configuration; instance API defaults and older
records retain their original choices.

Error correction is always explicit: `--lambda-ec` and a short
`--lambda-ec-purpose` are required. A zero value
also requires `--zero-ec-label`, for example
`--lambda-ec 0 --zero-ec-label diagnostic-no-ec`. This labels a diagnostic; it
does not supply an error-correction model or make zero leakage a production
claim. The default Frank-Wolfe budget is 2000 iterations.

Example preparation for one optical point:

```text
python -m runs.two_sided.point --instance optical_bb84 --route encoded \
  --map announcement-resolved --loss-db 5 --rounds 100000000 \
  --lambda-ec 120000 --lambda-ec-purpose "declared reconciliation cap" \
  --dark-count 1/1000000 --output build/two-sided/optical-5db
```

For BBM92, `--loss-db` means **total symmetric link loss**. The driver assigns
half the stated dB loss to Alice's arm and half to Bob's arm. Select the honest
source model with `--source-model ideal_pair` or `--source-model spdc`.

## Solver choices and warm starts

Candidate-search settings apply to every instance. They are recorded in
`config.solver`; resolved settings and method switches are in
`stages.key_rate.search_report`:

- `--oracle spectral` solves every linear subproblem whose feasible set is a
  spectraplex in closed form (BBM92's one program; decoy's Alice sectors of
  input dimension one) and the rest with QICS. Default `qics`.
- `--method` selects `fw`, `pairwise`, `factor`, `entropy`, `corrective` or
  `auto`. The default is explicit `fw`; `auto` is opt-in. Every method
  uses the same original first-order assessment. Unsupported explicit methods
  report their capability refusal.
- `--budget-seconds` bounds the whole solver across attempts; `--iterations`
  is a method-native work cap, and `--gap-target` is a diagnostic target.
  Neither changes a proof threshold.
- `--warm-start DIR` starts from the final iterate of a prior point's output
  directory `DIR` (its `final-iterate.json`, identified by sha256). The seed
  must live in the new point's feasible set -- same source mode, joint-sector
  layout and block dimensions, no constraint rows; in practice the same
  instance and route at another loss -- or the run is refused with a named
  reason: a missing or altered file before any directory is created, a
  mismatched seed as a recorded `solve`-stage refusal
  (`runs/general-records.md` lists the reasons). The seed's path is kept in
  the configuration as a locator and is not part of its digest.

Every completed general-format point writes `final-iterate.json` beside
`record.json` (format: `runs/general-records.md`).

`python -m runs.two_sided.chain` runs a list of loss points in order for one
instance and route, each warm-started from the previous one, with the same
options as a single point plus `--loss-db L1 L2 ...` and `--output-root`
(one directory per point, `<root>/<loss>db`):

```text
python -m runs.two_sided.chain --instance bbm92 --route encoded \
  --loss-db 9 10 11 --rounds 100000000 --lambda-ec 0 \
  --lambda-ec-purpose "diagnostic" --zero-ec-label "unreconciled diagnostic" \
  --dark-count 1/1000000 --oracle spectral --method pairwise \
  --output-root build/two-sided/chain-bbm92
```

The chain runs one point after another in one process; running instances or
routes in parallel is not its job.

## Proposed matrix recipe

The Cartesian recipes below are proposed measurements, not claims about
expected rates:

- loss: 0, 5, 10, 15, and 20 dB;
- instance: `optical_bb84`, `decoy_bb84`, and `bbm92`;
- route: `encoded`, `licensed`, and `licensed+two-sector`;
- acceptance map: each optical or decoy map being compared;
- BBM92 honest source: `ideal_pair` and `spdc`;
- declared dark-count values and an explicitly chosen integer `lambda_ec`.

Run one command per matrix cell with a distinct output directory. Sensitivity
recipes may then vary rounds, dark count, decoy intensities, SPDC mean-pair
number, and the declared error-correction leakage one axis at a time. Literature
values may be transcribed only with their citation and convention (especially
whether loss is total or per arm); this recipe supplies no literature numbers.
