# CERTIQS-KEY

Finite-size, fixed-length key rates for QKD protocols from the
marginal-constrained entropy accumulation theorem (MEAT), with every
assumption a key length rests on traced to the claim that needs it.

It is meant for QKD experimentalists and vendors who need a key length they can
defend, for evaluators who must decide what a claimed key rate rests on, and for
security-proof researchers. It covers discrete-variable protocols; bundled are
BB84 (ideal qubits, and with an optical receiver), decoy-state BB84 with weak
coherent pulses, and entanglement-based BBM92.

The [whitepaper](whitepaper/certiqs-key-whitepaper.pdf) says what CERTIQS-KEY
is and how it was built. The mathematics is split into seven modules; each
module's *contract* is a set of *claims* (definitions, assumptions, theorems,
requirements on the code), one file each, rendered as a PDF. The
[project site](https://fraunhofersg.github.io/certiqs-key/latest/) serves the
contracts so that a claim link opens the contract at the claim.

**Status.** An early research release. The contracts and the code were
drafted, reviewed and implemented by AI agents under human direction; human
review is partial. Do not use its key
lengths for security-critical deployment. A claim's status `accepted` records
the maintainers' acceptance of its batch after independent review by an AI
verifier, not a human check of every proof. Most batches of this release
were drafted and reviewed by models of one provider; the whitepaper (§5.1)
discusses what that means for the independence of the review.

**Using it.** The recommended way is through the AI agent you already use:
the [MCP server](#recommended-through-an-ai-agent-mcp) lets it describe your
setup to the engine, run it and hand you the result. Whichever way you run it,
the output to read is the **key-rate report**: the key length together with
every premise it rests on, in plain language, each linked to its claim. The
key length holds for your devices only if those premises do.

| You want to… | Open |
| --- | --- |
| Read a claim | the contracts on the [project site](https://fraunhofersg.github.io/certiqs-key/latest/), or `spec/modules/<module>/claims/`; the main results are collected in [spec/overview/overview.pdf](spec/overview/overview.pdf) |
| See a key-rate report | the [BBM92 headline report](https://fraunhofersg.github.io/certiqs-key/latest/runs/bbm92_study/data/headline-report/report.html) of the whitepaper's study ([runs/bbm92_study/](runs/bbm92_study/README.md)), and [runs/report_examples/](runs/report_examples/README.md) |
| Compute a key rate | [through an AI agent](#recommended-through-an-ai-agent-mcp) (recommended), or [from Python](#from-python-a-key-length-from-a-bundled-protocol), then [instances/README.md](instances/README.md) |
| See how claims are written and reviewed | [PRINCIPLES.md](PRINCIPLES.md), [spec/claim-format.md](spec/claim-format.md), the roles in [harness/README.md](harness/README.md#roles) |
| Read the architecture | [spec/architecture.md](spec/architecture.md), [spec/modules.yaml](spec/modules.yaml), [viewing guide](harness/contract-reading.md) |
| Find a source | [refs/index.json](refs/index.json) |

## Recommended: through an AI agent (MCP)

`runs/mcp` is a Model Context Protocol server for Claude Code, Cursor and
Codex. Your agent describes your setup in an instance's parameters, or writes
it as a protocol document from an instance's template, has the engine check
and run it, and returns the key rate with its **key-rate report** for you to
review. Install it from a clone and print each client's configuration:

```bash
git clone https://github.com/fraunhofersg/certiqs-key.git
cd certiqs-key
python -m venv .venv
source .venv/bin/activate        # Git Bash: .venv/Scripts/activate; PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[oracle-qics,certify,mcp]"
python runs/mcp/launch.py --print-config all
```

[runs/mcp/README.md](runs/mcp/README.md) says how to add it to each client.

## From Python: a key length from a bundled protocol

You need Python 3.12 or later and `git`; the package is installed from the
clone. This installs the engine with its linear oracle (the conic solver QICS)
and the certified tier's ball arithmetic, runs the bundled `bb84` instance
(ideal qubit BB84) at its defaults, prints the key length and writes the
key-rate report. The commands are for a POSIX shell (on Windows, Git Bash).

```bash
git clone https://github.com/fraunhofersg/certiqs-key.git
cd certiqs-key
python -m venv .venv
source .venv/bin/activate        # Git Bash: .venv/Scripts/activate
python -m pip install -e ".[oracle-qics,certify]"
python - <<'EOF'
import shutil, sys; sys.path.insert(0, ".")   # instances/ ships with the checkout
from pathlib import Path
from certiqs_key.runs import record_run, write_record
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle
from instances.bb84.surface import default_config, runner

out = Path("build/first-run")
shutil.rmtree(out, ignore_errors=True)   # start empty: a run does not overwrite a record
config = default_config()
run = runner(QicsSectorChoiOracle(), out / "bundle", created_by="first-run")
record = record_run(run(config, 0), config, created_by="first-run")
write_record(out / "record.json", record)
stage = record.as_dict()["payload"]["stages"]["key_rate"]
print("key length:", stage["key_length"], "bits from", stage["rounds"], "rounds")
print("tier:", stage["reported_tier"], "| solver:", stage["solver_status"])
EOF
python -m certiqs_key.runs.report build/first-run/record.json \
  --out build/first-run/report.md --contract-base ../../ --repo-base ../../
```

It prints

```text
key length: 1814 bits from 10000 rounds
tier: certified | solver: relative_gap_met
```

**Read the key-rate report**, `build/first-run/report.md` (`--format html`
for HTML): the key length with every premise it rests on, its links reaching
the contracts and files of the checkout. `record.json` beside it is the run
record the report is rendered from. The other bundled protocols are listed in
[instances/README.md](instances/README.md); each has a `surface` module with
the same `default_config` and `runner`.

**Your own protocol** is a protocol document. The smallest complete one is
[instances/bb84/protocol.yaml](instances/bb84/protocol.yaml); the bundled
`bbm92`, `optical_bb84` and `decoy_bb84` instances each have one too, with
detectors, efficiencies and dark counts declared. Copy one, change it as its
header comment says (a new identity first), and in the script above replace
the `instances.bb84.surface` import by `from instances.declared import load`
and `surface = load(Path("my_protocol.yaml"))`, then use
`surface.default_config` and `surface.runner`. The format guide is
[instances/declared/README.md](instances/declared/README.md).

> **Before you trust a number**
>
> - **The defaults are ideal.** The bundled instances default to ideal
>   devices (detector efficiency 1, no dark counts, no channel loss, no
>   misalignment) and to λ_EC = 0, which charges nothing for the bits your
>   error correction reveals. Set your own values (each instance's README
>   lists its parameters) and the λ_EC of your code.
> - **Solver effort.** A default run searches under a 120 s budget per
>   evaluation. A search that stops early still reports a lower bound,
>   possibly far below the value; the report states the solver status and
>   the gap.
> - **Reference values at zero loss.** The hand-derived reference values the
>   tests compare with are all at zero channel loss. Under loss, optical BB84
>   with dark-click probabilities near 1e-6 can be refused with
>   `negative_objective`; the refusal reports no key length rather than an
>   overstated one.
> - **Read the tier and the premises.** `certified` means that every
>   arithmetic step of the bound was exact or rigorously enclosed; it is not
>   certification by an evaluation body. A `first-order` number is proved in
>   exact real arithmetic but evaluated in floating point, and an `estimate`
>   backs no key length. Whatever the tier, the key length holds only for the
>   devices exactly as declared and only if every premise the report lists
>   under "What you vouch for" holds.

## Choosing a solver

The solver's choice changes how tight the bound is and how long the run takes,
never whether the bound is sound: whatever it returns is formed and checked
by the same assessor. Without a `method` a run uses `auto`, which runs several
searches under one wall-clock budget and keeps the best. `fw` (plain
Frank-Wolfe, bounded by `max_iterations`) repeats exactly, since its work is
counted in iterations rather than time. Choose with
`default_config(solver=SolverSettings(method="fw", max_iterations=500))`
(`certiqs_key.runs.config`), or in a protocol document under
`run_defaults.solver`. The other settings are listed with their defaults in
[runs/general-records.md](runs/general-records.md#solver-settings).

## Running one

`certiqs_key.runs` composes the modules into a run and records what each of
them said at each boundary; `instances/` carries the protocols. `instances/` is
not part of the installed distribution: `pip install` ships `src/` alone, so a
caller puts the checkout on `sys.path` ([instances/NOTES.md](instances/NOTES.md)
says why).

## Development

```bash
git clone https://github.com/fraunhofersg/certiqs-key.git
cd certiqs-key
python -m venv .venv
source .venv/bin/activate        # Git Bash: .venv/Scripts/activate
python -m pip install -e ".[dev,oracle-qics,certify,plots,mcp]"
```

The contract PDFs and claim graphs are built with a TeX distribution
(`latexmk`) and Graphviz (`dot`). The checks CI runs, all expected to pass in
the activated environment:

```bash
python -m harness.check_claims
python -m harness.check_symbols
ruff check harness tests src instances runs
mypy harness ; mypy src instances runs
python -m pytest -q
```

Every tool of the harness says why it exists ([harness/README.md](harness/README.md));
agents and maintainers start at [AGENTS.md](AGENTS.md).

## Issues and contributions

Issues are welcome, including a key length you think is too long or a claim
you think is wrong; soundness defects may be raised as public issues. Pull
requests only after contacting us in an issue.

## Citing

Cite the whitepaper:

> E. X. Huber, B. Verghese, M. Croci, I. George, M. Kasper and M. Tomamichel,
> *CERTIQS-KEY: Towards certifiable QKD key rates with AI-developed security
> proofs*, whitepaper (2026),
> <https://fraunhofersg.github.io/certiqs-key/v0.1.0/whitepaper/certiqs-key-whitepaper.pdf>.

A release also carries a `CITATION.cff`, which GitHub's "Cite this repository"
reads.

## Licence

CERTIQS-KEY is free software under the GNU Affero General Public License,
version 3 only (`AGPL-3.0-only`; the full text is [LICENSE](LICENSE)). You may
run, study and change it for any purpose, commercial in-house use included. If
you distribute it, or let others use a changed version over a network, you pass
on its source under the same licence. Third-party material in the tree and its
terms are listed in [NOTICE](NOTICE).

Copyright (C) 2026 Fraunhofer Singapore Research Ltd. To use CERTIQS-KEY under
other terms, for example inside a closed product, contact
elias.x.huber@fraunhofer.sg.
