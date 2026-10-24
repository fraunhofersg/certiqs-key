# The CERTIQS-KEY MCP server

This lets the AI tool you already use (Claude Code, Cursor or Codex) compute a
finite-size key rate for your QKD setup. The agent maps your description onto
one of the engine's protocol instances, or writes it as a protocol document
when no instance describes it. The engine checks it, runs it, and returns the
key rate with a **key-rate report**: every assumption the number rests on,
each in plain language. **You** review that report. The key rate applies to
your device only if those assumptions hold for it.

The server is an adapter over the run tier's facade (`runs/facade`). It
decides no number, no refusal and no sentence of the report, and it is not on
the proof path (`PRINCIPLES.md` §9, "Clear piping").

## Set it up

1. Clone this repository and install the engine with the server's
   dependencies, as in the top-level `README.md`:

   ```
   python -m venv .venv
   .venv/Scripts/python -m pip install -e ".[oracle-qics,certify,mcp]"   # Windows
   .venv/bin/python -m pip install -e ".[oracle-qics,certify,mcp]"       # macOS, Linux
   ```

2. Print the configuration for your client. The paths in it are absolute
   paths into this clone:

   ```
   python runs/mcp/launch.py --print-config claude   # or cursor, codex, all
   ```

3. Add it to your client:
   - **Claude Code**: run the printed `claude mcp add ...` line, or paste the
     JSON into a project's `.mcp.json`.
   - **Cursor**: paste the JSON into `~/.cursor/mcp.json`, or into
     `<project>/.cursor/mcp.json`.
   - **Codex**: paste the TOML into `~/.codex/config.toml`. It raises Codex's
     start-up timeout to 30 s, because the first call imports the engine.

The server is started as `<python> <clone>/runs/mcp/launch.py`. That works
from any working directory. If the configured Python lacks the dependencies,
the launcher hands over to the clone's `.venv`; to use another environment,
set `CERTIQS_KEY_PYTHON`.

The repository deliberately ships no `.mcp.json` of its own. If it did, every
agent developing the engine in this clone would be offered the server.

## The tools

| Tool | What it does | Time |
| --- | --- | --- |
| `list_instances` | the protocol instances, each with its protocol-document `template` where it has one and a `runtime` line (the expected preparation time at its defaults and the parameters it grows with), and the engine's identity (commit, schema versions) | instant |
| `describe_instance` | every parameter: meaning, unit, domain, default; presets; a complete `default_config`; `runtime` (which parameters drive the preparation time). Given a `document` or `document_file` instead, it validates that protocol document and describes it the same way | instant |
| `get_reference` | the workflow, an instance's README, a JSON schema (`run-input`, `record`, `report`, `protocol-document`), an instance's `template`, the `document-guide`, the refusal codes | instant |
| `prepare` | reads and checks a configuration and prepares it without solving: the resolved config, the snaps, the acceptance alphabet, the honest distribution and the `estimate`, or a refusal with the engine's reason code. Takes an instance or a document. Past the budget it starts a preparation job instead; `prepare(job=...)` returns that job's summary | about 1 s, or instant (a job) |
| `start_run` | starts a run in the background and returns a job id with the preparation's `estimate`. Takes an instance or a document | instant |
| `run_status` | a job's state and progress (a run or a preparation; expected against elapsed seconds), or the recent jobs | instant |
| `cancel_run` | stops a job | about 1 s |
| `get_report` | the report: by default the result plus every assumption with its `user_statement`; any part by its stable path (`assumptions/A-ENS`, `inputs/rounds`, ...) | instant |

**Your own statistics.** `prepare` and `start_run` take an optional `honest`
argument. It replaces the instance's honest channel model with your measured
statistics:
- a `table`, which is one law, or
- an `envelope`, which is a range per outcome (Assumption A-HON-ENV).

Either form needs a `source` saying where the statistics come from. The record
names the replacement, and the report lists it as an input you vouch for.

**A custom protocol** that none of the instances describes is written as a
**protocol document**: JSON or YAML that declares the protocol's parameters,
source, receiver, public announcements, key map and honest model, in the
format of `instances/declared/README.md`. The agent:

1. takes the nearest template: `get_reference("template", name="bb84")`
   returns `instances/bb84/protocol.yaml` as text and as a JSON object.
   There is one for each of `bb84`, `optical_bb84`, `decoy_bb84` and
   `bbm92`; `list_instances` names each under `template`;
2. edits a copy: a new `identity.id`, title and summary, no `identity.readme`
   or `identity.record_label` (the packaged instances' ids and the
   `instances.` labels are reserved for their own templates), and none of
   the other reserved strings the template's header names (optical_bb84's
   and decoy_bb84's stations and source write `instances.` labels; one
   `reserved_identity` refusal lists every such place: rename each, such
   as your own `attested_by`, or delete the optional field or block),
   then whatever differs. Exact numbers are written as strings (`"0.02"`, `"1/50"`); a
   JSON float is read as its binary64 value, and the replacement is
   recorded;
3. validates it with `describe_instance(document=...)`, or
   `document_file=<absolute path>` for a local `.json`, `.yaml` or `.yml`
   file of at most 1 MiB (a relative or network path is refused, and a file
   that is not a protocol document is refused without quoting it). A
   refusal comes back as data:
   `{refused, stage: "document", reason, path, detail}`, where `path` is the
   JSON pointer of the offending place and `reason` one of
   `get_reference("refusal-codes")`'s `document_refusal_codes`;
4. runs `prepare` and `start_run` with the same document, leaving `instance`
   empty, and reads the report with `get_report` as for an instance.

Anything the document declared itself, rather than the engine deriving it, is
listed under `user_declared` in `prepare`'s summary and in the report: a
directly declared receiver POVM, a receiver declared by port Grams, an
instrument matrix, a C10 block or a dark-count channel, explicit constraints,
an attack-set licence, a feasibility witness, a retention attestation. **Each one is yours to vouch
for**, and so are a shipped template's own: bb84's declared qubit POVM and
decoy_bb84's retention attestation are listed the same way when you run
those instances, because whoever uses the key rates takes responsibility for
them.

Supported: directly declared receiver measurements (Band A) and optical
receivers (an element graph of catalogue components, port Grams or an
instrument matrix), one station or several; trusted, untrusted and
weak-coherent decoy (`wcp_decoy`) sources; the accepted public-part format
or a transcript of any length; `factor_projection` and choice weightings.
The four templates show each of these in use: `bb84` (Band A),
`optical_bb84` (an optical receiver of catalogue components),
`decoy_bb84` (a `wcp_decoy` source and a transcript) and `bbm92` (two
stations, `factor_projection`, a choice weighting).

A document is bounded in the work it may ask for, not only in its size: an
alphabet of at most 4,096 labels, a rule table of at most 16,384 keys, and
Hilbert-space dimensions of at most 64 (`instances/declared/limits.py`, far
above what the packaged instances use), and an optical station of at most
photon cutoff 7, 8 detector ports and a bounded receiver work. Past them it
is refused with `document_too_large`, before the work starts, so every call
still returns in seconds. The packaged instances themselves keep their own
parameter ranges (optical_bb84 admits a cutoff of 16): only a custom
document is held to the work bounds.

**Long preparations.** A preparation is quick at the defaults and can take
minutes at the far end of an instance's range: optical_bb84 prepares photon
cutoff 8 in 10 to 30 s, 9 in one to two minutes and 10 in ten to twenty,
depending on the machine's load. So every preparation is ESTIMATED first,
from the configuration alone (`runs/facade/estimate.py`: the photon cutoffs,
the exact and tail windows and the detector ports of each receiver,
calibrated on measured preparations). Every reply about it says how long and
why: `prepare`'s summary and `start_run`'s reply carry `estimate`
(`expected_seconds`, `duration` in words, `why`, `basis`; `extrapolated` past
the measured range; a capped figure reads "more than ..."; past a day,
`advice` says it will not finish in practice and to choose a smaller cutoff
or window -- it is still not refused), and `run_status` shows it beside
`elapsed_s`. A preparation whose estimate, doubled for safety, passes the
budget (20 s; `CERTIQS_KEY_PREPARE_BUDGET_S`) runs in the background:
`prepare` returns at once with `{state: "starting", job, kind: "prepare",
expected_seconds, duration, why, tell_the_user}`, the agent tells you the
expected time and its reason, polls `run_status(job)`, and `prepare(job=...)`
then returns the same summary the call would have (its envelope kept in the
job's directory). A run job prepares once itself, so a `prepare` beforehand
is its own cost and its result is not reused by the run; `start_run` past
the budget leaves even its quick check to the run's worker, so a refusal
then ends the job `refused`, with its reason in `run_status`. The estimate
is an order of magnitude, not a promise; where it cannot be read (an
instance that does not state its receivers, a configuration that does not
lower) it is `unknown` and the preparation runs in the call.

## Where things go

Jobs are written under `~/.certiqs-key/jobs/<job>/`, or under
`$CERTIQS_KEY_JOBS_DIR` if you set it. Each job directory holds:
- `request.json`;
- `status.json`;
- `events.jsonl`;
- `record.json`, the run record and the authority;
- `report.json`, `report.md` and `report.html`, the report to review, with
  links into the contracts in this clone;
- `worker.log`.

`prepare` writes the full preparation under `preparations/`, and a reference
too large for one reply (the protocol-document schema) is written under
`references/`. Any other reply too large for one tool result -- a large
document can make one -- is written under `replies/`, and the reply names the
file beside its outcome (refused or not, the document's digest, the job). A protocol document's jobs are named `declared_<id>-...`, so
they never share a name with an instance's, and their `request.json` holds the
document in its canonical form, which the worker reads back.

| Setting | Meaning |
| --- | --- |
| `CERTIQS_KEY_JOBS_DIR` | where jobs are written |
| `CERTIQS_KEY_MAX_JOBS` | concurrent jobs (runs and preparation jobs), default 2; a further one is refused until one finishes |
| `CERTIQS_KEY_PREPARE_BUDGET_S` | a preparation whose estimate, doubled, passes this many seconds runs in the background, default 20 |
| `CERTIQS_KEY_PYTHON` | the interpreter the launcher hands over to |

An identical request is answered with the job that already ran it. Identical
means the same instance, configuration digest, honest override and engine
commit, which is read afresh for every request, and for a protocol document
the same document digest: any edit, an annotation included, is a new job.
Every reply that names a document's job names its `document.digest`. A run made while the clone had
uncommitted changes is never reused, and nothing is reused while it has them,
because two such runs are not known to have run the same code.

`start_run` prepares the configuration before it starts a worker, so a request
the engine refuses costs no run. A cancel stops a run within about a second,
unless the run has begun writing its record; it then finishes normally.

Honest probabilities are exact strings (`"1/10"`, `"0.1"`). A JSON number is
refused, because `0.1` as a number is not 1/10.

## Built for three clients at once

The clients differ in what they tolerate, so the server keeps to the
narrowest:

- **Fast calls.** Every tool returns in seconds; a run is a background job,
  and so is a preparation estimated past the budget. Codex gives a tool call
  60 s by default.
- **Small replies.** Every reply stays under about 15k tokens, below Claude
  Code's 25k cap. Anything larger is written to a file and named.
- **Few, flat tools.** There are eight tools, and Cursor loads about 40 across
  all servers. Each takes flat inputs (strings, a boolean, objects; an optional
  object is "object or null"), with no `$ref` anywhere. The full input schema
  is served by `get_reference`.
- **No reliance on extras.** Some clients do not read MCP resources or server
  instructions, so everything is reachable through the tools, and
  `get_reference("workflow")` repeats the instructions.
- **Fast start.** The engine is imported on the first call, not at start-up.

`tests/integration/test_mcp_server.py` holds the server to these, including a
whole workflow over a real stdio connection started from outside the clone.
