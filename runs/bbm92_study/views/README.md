# runs/bbm92_study/views: the worked example's figures as TikZ and PGFPlots

The whitepaper's BBM92 worked example shows the protocol, receiver and
statistics views of its run, and the study's key-rate sweeps. This package
draws them as vector LaTeX (TikZ, PGFPlots, booktabs): the views from
view-model JSON, the key-rate figures natively from the sweeps'
`summary.csv` (`runs/bbm92_study/plot.py` keeps the
matplotlib quick looks). Each figure is a pure function from parsed data to a
LaTeX string; nothing is placed by an instance name.

    python -m runs.bbm92_study.views --viewmodels runs/bbm92_study/data/viewmodels \
        --out build/bbm92-views [--keyrate-data <dir>] [--station 0] [--preview]

It writes `views-preamble.tex`, one `<name>.tex` per figure and, beside it,
`<name>.caption.tex`: the proposed caption, plain text to paste into
`\caption{...}`. Every figure file starts with a comment naming its source
data and the pins. `--keyrate-data` reads `<dir>/<sweep>/summary.csv` for each
sweep that has one; a sweep without drawable data is skipped with a message,
and a figure drawn from a placeholder input is named in one.
`--preview` also writes and compiles `views-preview.tex` (see below).

## The snapshot: two device sets

The view inputs are one folder, `runs/bbm92_study/data/viewmodels/`, holding
the study's two device sets of the parameter table (`devices.tex`), each at
the study's headline point (10 dB, 10^6 expected coincidences):

    snapshot.json                 pins and files, per set
    perfect/  realistic/          one folder per set:
        protocol_map.json  optics.json  povm.json  povm-dark-composed.json
        preparation-extract.json
    realistic/record-extract.json the realistic run's record extract

The four view models are the view-model builders' output for the set's
preparation; `povm-dark-composed.json` is the POVM view drawn from
the photon-number blocks composed with the dark-count channel, so that dark
counts show. `preparation-extract.json` holds what the figures need of the
preparation that the view models do not carry: the declared detector
efficiencies and dark-click probabilities per party, the test fraction, and
each station's efficiency normalization (the factored loss and each port's
declared and compiled efficiency). `snapshot.json` names, per set, the engine
pin, the builders' commit and the record extract the set uses
(`record_extract`: a path in the folder, or `null`).

A single-set figure is drawn from the set `build.FIGURE_SET` names: the
realistic one for the protocol, both receiver figures, the statistics and the
key map; the perfect one for the single-set POVM. `povm-compare` draws both.

The statistics figure reads the realistic set's record extract, taken from a
run of the set's point. The generator prints a message whenever a set's
record extract is not from the set's engine pin.

## Using the figures in the whitepaper

The whitepaper's preamble must add two packages the figures need:

    \usepackage{pgfplots}
    \pgfplotsset{compat=1.18}
    \usepackage{booktabs}

then `\input{views-preamble}` once, after the whitepaper's figure style.
That style holds the figures' design tokens (palette, the two type sizes,
line, arrow and plot styles) and sets `\figtokensloaded`; the generated
preamble then skips its own copy of the same tokens (`tex.PALETTE`,
`tex.TOKEN_STYLES`), so each is defined once. A document without the
whitepaper's figure style gets the copy. A figure is
`\begin{figure}\centering\input{optics}\caption{...}\end{figure}`; the key map
is the body of a table float, `\begin{table}\centering\caption{...}\input{keymap}\end{table}`.

`optics-compact` is drawn to stand beside the parameter table: it is about
5 cm wide with its labels, under half the whitepaper's text width, and its
symbols are the table's. Two minipages in one float set the pair; the table
as it is (with its source column) is about a full text width wide, so beside
the figure it needs a narrower layout.

## Rules every figure follows

- **Fonts**: two sizes, Fira Sans: `\figmain` (7.5 pt) and
  `\figsmall` (6.25 pt); no text below 6.25 pt (sub- and superscripts in math
  take TeX's usual smaller size). Plots set labels and direct labels in
  `\figmain`, ticks in `\figsmall`, tick numbers in the figure font.
- **Colour**: the whitepaper's tokens: the
  accent (`blue!55!black`) and greys; series navy, vermilion, sky,
  ink, apart in greyscale; a muted grey for a reference series; lane colours
  in the protocol swimlane only. The whitepaper's `vouch` red is not used.
- **Direct labels**: a line plot names its series at the line ends, right of
  the axis, each joined to its line by a leader; the ladder names its blocks
  at the top rung's bars. A legend above keys only line styles.
- **Attached labels**: in `optics-compact` every symbol sits in a tint tag
  touching its element; splitters 4.6 mm, detectors 2.6 mm in radius.
- **Captions, not annotations**: what explains, qualifies or gives provenance
  (legends in words, counts of what is not shown, notes on sources, pointers
  to other figures) is in the caption, written from the same data; the drawing
  keeps axis, lane and step labels, the names of what is drawn, values that
  belong to an element, and direct series labels.

## The figures and what they read

| File | Shows | Reads |
| --- | --- | --- |
| `protocol.tex` | A swimlane: lanes in `LANE_ORDER` (Source, Alice, Public, Bob, Eve; others after) as columns, steps (source, transmission, measurement, announcements, sifting, key rule, acceptance statistic) as rows. Boxes take 80 % of a lane; a register read more than a row later runs in the lane's gutter, so no wire passes behind a box. Quantum wires heavy with square tags, classical thin with round tags. Titles merged ("channel, arms 0 and 1"), "party X" dropped, the measurement shown as its POVM symbol, the station's choice on one line. | `protocol_map.json`: `lanes`, `steps[]` (`type`, `title`, `operations[]` with `id`, `lane`, `title`, `math`, `inputs`, `outputs`), `registers[]`, `label_legend.choices`. Realistic set. The test checks the choice weights against each set's `test_fraction`. |
| `optics.tex` | The receiver of one station as a mode circuit: a rail per mode with its input role, elements in element-graph order with their class, name and parameters, the passive basis choice, detectors, one line "all detectors: η, p_dc" when they agree, "unmonitored (loss)" outputs (the receiver contract's rem:unmonitored). | `optics.json`: `stations[i]` (`modes`, `rails`, `elements`, `ports`, `assumptions`); a retarder's `angle` and `retardance` as `{"pi_coefficient": "p/q"}` or as radians. Detector values the view model does not attach come from `preparation-extract.json` `device[party]`; the caption says so. Realistic set. |
| `optics-compact.tex` | The same receiver as a compact beam diagram for beside the parameter table, about half a text width: a line per beam path, the channel entering from the left, splitters as cubes with their splitting face, the plate as a bar, detectors at the beam ends; every element labelled by the table's symbol (`T`, `ε`, the plate angle `π/8 + θ/2`, `η_H` ... `η_A`, one line "all detectors: p_dc"), no values. The symbols are `devices.SYMBOLS`, which the table uses too. The layout draws a tree of beams and refuses anything else. | `optics.json`: `stations[i]` (`modes[].path`, `elements`, `ports`), every station's plate angle (where they differ the plate shows `+ θ/2` and the caption names the station where `θ` is zero). Realistic set. |
| `devices.tex` | The body of a table float: the parameter table, perfect and realistic values per quantity with its symbol and the cited source of each realistic value; the channel a row of its own. | `runs/bbm92_study/sweeps.py` `REALISTIC`; the symbols are `devices.SYMBOLS`. No view model. |
| `povm.tex` | The station's POVM, one row per photon-number block (n = 0, n = 1) under shared outcome headers; cells shaded by magnitude, entries printed; real and imaginary rows for a complex block; click patterns under each outcome. | `povm.json`: the `photon_blocks` group of the station (`blocks[]`, `outcomes[].fibre`). Perfect set. |
| `povm-compare.tex` | The station's POVM for the perfect (left) and the realistic (right) set: one row per outcome with its click patterns, per set the n = 0 and n = 1 blocks side by side under their basis kets, one shading scale per photon number shared by both sets, every entry printed. The caption says that the realistic entries are at the normalized efficiencies (the factored loss, each declared efficiency beside the one used) and what the dark counts give at n = 0. | Each set's `povm-dark-composed.json` (the `photon_blocks` group of the station); the realistic set's `preparation-extract.json` `normalization[station]`. |
| `statistics.tex` | Two panels on the outcomes in the support: "honest p" (log beyond one decade) and "acceptance box around p" (`q - p` in 1e-4), a rule between the outcome groups. | The realistic set's record extract (`snapshot.json`): `outcomes[]`, `rounds`, `completeness_budget`, `endpoint_rule`. |
| `keymap.tex` | The body of a table float: sifting pass (bold) / fail (muted ×) per announcement class, a dot where no outcome announces it; and per readout of the key holder, its announcement, the classes that key it, the key bit. | `protocol_map.json`: the `sifting` and `key_rule` steps' tables. Realistic set. |
| `keyrate-loss.tex` (F1) | Key rate per round against total loss, a line per block of coincidences, log y; below, the rate over the perfect asymptote, the blocks named at the line ends. | `loss/summary.csv` |
| `keyrate-qber.tex` (F2) | Key rate against QBER (%), a line per loss, log y. | `qber/summary.csv` |
| `keyrate-rounds.tex` (F3) | Key rate against n, log-log, a panel per loss on a shared y range, expected coincidences on a top axis. | `rounds/summary.csv` |
| `keyrate-solvers.tex` (F4) | The entropy bound h_lb per solver method as a line, the h_lb..h_low bracket as a band, against alpha − 1. | `solvers/summary.csv` |
| `keyrate-alpha.tex` (F7) | Key length relative to its maximum per block against alpha − 1, the maximum starred, the blocks named at the line ends. | `alpha/summary.csv` |

The key-rate figures leave out points without a positive key length (and
points not yet run); the caption counts them. Series labels sit at line ends,
data inline (`\addplot table`), so each file is self-contained.

## The preview

`views-preview.tex` mirrors the whitepaper's preamble (T1
fonts, British babel, csquotes, the AMS packages, graphicx, xcolor, TikZ with
`arrows.meta`) plus `pgfplots` and `booktabs`, and sets each figure in its
float with its proposed caption. After a clean compile the latexmk
auxiliaries are removed.

## Regenerating at a new pin

The view models come from the builders of a separate application, not
published here; `snapshot.json` names its commit and the engine pin of each
set. To move the snapshot to a new engine
pin:

1. Build each set's view models at the study's headline point with those
   builders, from the engine checkout at the new pin, giving `perfect/` and
   `realistic/`, each with the four view models and `inputs/prepare.json`, the
   preparation.
2. Run the study's headline point of each set on the same engine commit,
   keeping the run record and its bundle folder beside it (a set without a
   run keeps the record extract its `snapshot.json` entry names).
3. Refill the snapshot, one set at a time (copies the four view models,
   writes `preparation-extract.json`, with `--record` also
   `record-extract.json`, and the set's entry in `snapshot.json`):

       python -m runs.bbm92_study.views.snapshot --set realistic \
           --viewmodels <build>/realistic \
           --prepared <build>/realistic/inputs/prepare.json \
           [--record <run-record.json>] \
           --frontend-commit <builders commit> --engine-pin <engine commit> \
           --out runs/bbm92_study/data/viewmodels

4. Check that `snapshot.json` names the new commits.
5. Re-summarise the sweeps (`python -m runs.bbm92_study.summarize ...`) and
   regenerate the figures with the command at the top and `--keyrate-data`;
   check `views-preview.pdf`, and run `pytest tests/unit/test_bbm92_study_views.py`.

The test runs the generator on the committed snapshot and on small synthetic
summaries and checks the files' structure and the rules above; it does not
compile LaTeX.
