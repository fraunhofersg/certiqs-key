# runs/bbm92_study: the BBM92 worked example's key-rate study

The sweeps, the summary and the figures behind the CERTIQS-KEY whitepaper's
key-rate figures and its BBM92 worked example. The committed data, every
point's run record with its summaries, is in `data/` (its `PROVENANCE.md`).

## The pieces

| Module | Does | Writes |
| --- | --- | --- |
| `sweeps.py` | declares every sweep as data: points as overrides of the bbm92 document's defaults | nothing |
| `run.py` | runs points resumably: λ_EC estimate, α search (or fixed α), one run record per point | `build/bbm92-study/<sweep>/<point>/` |
| `summarize.py` | condenses a sweep's point folders into one CSV | `runs/bbm92_study/data/<sweep>/summary.csv` |
| `asymptote.py` | the ideal-device asymptotic key rate in closed form, newly derived and checked against the runs; the figures' n → ∞ reference | nothing |
| `plot.py` | draws the figures from the CSVs only | `build/bbm92-study/figures/<id>-<sweep>.{pdf,png,dat}` |
| `views/` | TikZ/PGFPlots versions of the protocol, receiver/POVM and statistics views (its own README) | `.tex` |
| `numbers.py` | the numbers the whitepaper quotes, read from the committed data | JSON on stdout |
| `run.sh` | the full run from a clean checkout, then the committed data replaced | `runs/bbm92_study/data/` |

The engine parts it uses are in the run tier:
`certiqs_key.runs.alpha_search` (the outer α search, opt-in) and
`certiqs_key.runs.error_correction` (the λ_EC estimate, opt-in, f_EC = 1.1 from
`kamin2025renyi` §VII Eq. (123)).

## Running

```
python -m runs.bbm92_study.run loss qber --workers 4
python -m runs.bbm92_study.summarize loss qber
python -m runs.bbm92_study.plot           # needs the plots extra: pip install -e ".[plots]"
```

- **Resuming.** A point whose `record.json.gz` exists is skipped. Delete the
  point's folder to rerun it.
- **Blocked sweeps.** A sweep marked `blocked` in `sweeps.py` is refused unless
  `--allow-blocked` is given.
- **Run time.** Every point runs method auto, 600 s per solve; the
  realistic routes from cutoff 3 and the licensed route from cutoff 4 get
  7200 s, where 600 s does not converge. With four workers (`run.sh`'s
  default; `WORKERS=<n>` overrides) the whole study takes eight to ten hours:
  run it detached (`bash runs/bbm92_study/run.sh`).

## What the numbers mean

- **Rounds.** `rounds` is n, the channel uses: emitted-pair time slots, not
  detected coincidences. A point is declared by its expected `coincidences`, and
  n follows from the loss and the detectors (`sweeps.rounds_for`), because the
  registered experiments collect about 1e6 coincidences per block. The summary's `expected_coincidences` and
  `expected_sifted` are the exact counts from the honest model.
- **Devices.** The loss, rounds and routes sweeps run each point with the
  realistic source and receivers (`sweeps.REALISTIC`, every cited value) and
  with perfect ones (the ladder's top rung), at the same channel, so the
  devices' cost is seen apart from the channel's; the QBER sweep varies the source visibility for both. The
  figures draw the perfect ones as a dashed reference, with the closed-form
  asymptote of `asymptote.py` dotted; the parameter table
  (`views/devices.py`) lists both sets with their sources.
- **A round** is one emitted pair (`source_model: ideal_pair`), so n counts
  emitted pairs; the dark-click probability per detector and round is the
  dark-count rate times the coincidence window (1 kHz x 130 ps = 1.3e-7).
- **Loss.** `loss_db` is the total symmetric channel loss, split half per arm.
- **QBER.** `qber` is set through the Werner visibility, Q = (1 - v)/2.
- **α.** The α a point used is in the record's `stages.key_rate.alpha` and the
  summary's `alpha`. The record's `config.parameters.alpha` still shows the
  declared default (1.05). The search is opted into through
  `RunConfig.alpha_search` and recorded with its evaluations.
- **Termination.** `termination` is the portfolio's last attempt. Read it
  together with `gap`, the record's `frank_wolfe_gap` of the candidate h_lb came
  from: a `numerical_failure` beside a gap of 1e-7 is a finished bracket.
  `h_low - h_lb` is not a gap, because h_low may belong to another candidate.
- **h_lb above the estimate.** `first_order_minus_estimate` is positive where
  h_lb exceeds the returned estimate h_low. The estimate's point is only in the
  relaxed feasible set, by at most a few 1e-7 bits per round where it
  occurs. The column keeps it visible.

## How the whitepaper's numbers are produced

1. **One commit.** Every point of a figure is run at one clean commit that
   contains this package. A record's `git_dirty` reflects tracked files only,
   so run from a commit, not from a tree with untracked study code; `run.sh`
   refuses a modified tree and writes nothing tracked until the last point.
2. **Device values.** Each realistic value in `sweeps.py` is checked against a
   registered source, its locator given beside the value, and the captions
   cite them.
3. **The evidence.** The summary CSVs and every point's record are
   under `runs/bbm92_study/data/<sweep>/` (`run.sh` does it), and
   `data/PROVENANCE.md` names the commit, the machine and what is known to be
   wrong in the data.
4. **Export.** A figure goes into the whitepaper with its `.dat` and the
   commit; `python -m runs.bbm92_study.numbers` lists the numbers its prose
   quotes.
