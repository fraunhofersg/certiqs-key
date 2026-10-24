# Provenance: the BBM92 study's runs

The evidence behind the CERTIQS-KEY whitepaper's key-rate figures: every
point of the study `runs/bbm92_study/` declares, with its run record.

## What was run

- **Engine and study code:** commit `a5a73ec`, a pre-release export of this
  repository made for the run; it is not in the published history. The
  published code is that commit's apart from comments, docstrings and
  messages: the maintainers compared the two trees with
  `python -m harness.same_code <that tree> <this tree>`, a comparison that
  needs that tree and so cannot be repeated from the published history. All 313 records name `a5a73ec` in `provenance.engine` with
  `git_dirty: false`.
- **Blocks:** 3e4, 1e5 and 1e6 expected coincidences for the loss, alpha and
  ladder sweeps, the ladder's n taken where the fully realistic devices
  expect that many coincidences at 0 dB, plus an n = 1e10 reference.
- **Where:** a clean checkout of that commit with `PYTHONPATH` set to its
  own `src` (harness/PITFALLS.md), on Windows; the first finished record was
  checked for its commit before the run was left alone.
- **How:** about eight and a half hours on four workers, one pool for every
  sweep (`../run.sh`; `run-log.txt` is its log, one line per point). 313
  points, every one `certified_reported`, no errors.
- **Devices:** the realistic set (`sweeps.REALISTIC`, every value cited in
  the parameter table; PBS leaks 1e-3 transmitted and 1e-2 reflected) and
  the perfect set (the ladder's top rung), at the same channel. A round is
  one emitted pair.
- **Solver:** method auto, 600 s per solve; the routes sweep's slow points
  at 7200 s, each licensed point taking its encoded twin's alpha and the
  realistic points above cutoff 3 the alpha realistic encoded N3 chose; the
  four `SPECTRAL_POINTS` with the spectral oracle.

## What is known to be wrong in this data

- **Realistic routes did not all converge:** at cutoff 5, encoded (250,011
  bits) and licensed (166,443) stopped on their 7200 s budget with relative
  gaps of 11 % and 33 %; licensed N2 (286,337) stopped on its budget and
  licensed N4 (288,878) stagnated. All of them lie below the 289,376 bits of
  cutoff 1 (the routes sweep's own solve of the headline setup, whose
  headline point gives 289,368 in the other sweeps); the other realistic
  route points meet their gap target. The whitepaper does not use the
  routes figure.
- **Relative gaps above 1e-3**, among points with a positive key: rounds up
  to 3.7e-3 (realistic, 30 dB, 3e4 coincidences); every other sweep but
  routes and the solvers comparison stays below 1e-3. The points without a
  key (11 in qber, 4 in rounds, 25 in alpha, 1 in solvers) are the smallest
  blocks, the highest QBERs and the extreme Rényi orders, with bounds at or
  below zero. The solvers sweep's fw and pairwise points are the comparison
  methods and are expected to stop wide.

## What is here

| Path | Contents |
| --- | --- |
| `<sweep>/summary.csv` | one row per point, written by `python -m runs.bbm92_study.summarize` with the study code of `a5a73ec` |
| `<sweep>/<point>/record.json.gz` | the point's run record |
| `<sweep>/<point>/point.json` | the point as the study declared it |
| `<sweep>/<point>/lambda-ec.json` | the lambda_EC estimate (f_EC = 1.1) |
| `routes/<point>/alpha-from.json` | the alpha a route point borrowed (the licensed points, and realistic encoded N4 and N5) |
| `headline-report/` | the headline point's key-rate report, rendered from its record (its README) |
| `viewmodels/` | the view-model snapshot, the inputs of the protocol, optics, POVM and statistics figures (`snapshot.json` names its commits; `../views/README.md`) |

## Reproducing

Solves that stop on their time budget can end at a different iterate on
another machine or under another load, so a rerun need not match these
records bit for bit; that is why the records themselves are kept. The
figures are rebuilt from the summaries with
`python -m runs.bbm92_study.views --viewmodels runs/bbm92_study/data/viewmodels --out <dir> --keyrate-data runs/bbm92_study/data --preview`.
