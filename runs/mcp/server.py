"""The CERTIQS-KEY MCP server: the run tier's facade as tools for any AI agent.

WHY THIS EXISTS. A QKD vendor, evaluator or researcher describes their setup
to the AI tool they already use; through these tools the agent maps it onto
an instance's declared parameters, has the engine check and prepare it, runs
it, and hands back a key rate with its key-rate report, which the user reviews.
The server is an ADAPTER
over the artefact schemas and the facade (``PRINCIPLES.md`` section 9):
every tool is one call of :mod:`runs.facade`, nothing here decides a number,
a refusal or a sentence of the report, and nothing is on the proof path.

BUILT FOR THREE CLIENTS AT ONCE -- Claude Code, Cursor and Codex -- and so
for the narrowest of them:

* every tool returns within seconds; a run is a background job (Codex gives a
  tool call 60 s by default), started, asked about and read, and so is a
  preparation whose estimated cost exceeds the budget
  (``runs/facade/estimate.py``), its expected
  seconds and their reason stated in the reply;
* every reply fits one tool result (Claude Code caps one at 25k tokens):
  large artefacts are written to files and named, and read in parts by a
  stable path;
* few tools (Cursor loads about 40 across all servers) with flat input
  schemas (an object, a string), the full input schema served as data by
  ``get_reference`` rather than inlined with ``$ref``s some clients drop;
* everything reachable through tools, because not every client reads MCP
  resources or the server's instructions; ``get_reference("workflow")``
  repeats the instructions;
* the engine is imported on the first call, not at start-up, so the
  handshake stays inside Codex's 10 s ``startup_timeout_sec``.

A CUSTOM PROTOCOL is a protocol document (``instances/declared``):
``describe_instance``, ``prepare`` and ``start_run`` take a ``document``
(object) or ``document_file`` (path) in place of an instance, so the tool count
stays at eight. ``describe_instance`` with a document is its validation;
``get_reference`` serves the document's schema, the packaged templates and the
format guide.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Final

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

__all__ = ["INSTRUCTIONS", "build_server", "main"]

#: Largest reply, in characters of JSON, before a part is written to a file
#: instead (about 15k tokens, under Claude Code's 25k default cap).
MAX_REPLY_CHARS: Final[int] = 60_000

INSTRUCTIONS: Final[str] = """\
CERTIQS-KEY computes finite-size key rates for QKD protocols, each with a
key-rate report stating every assumption the result rests on. You formalise
the user's protocol; the engine accepts or refuses it; the USER reviews the
report. A key rate is only as good as the match between the report and the
user's real device, so never hide a choice from the user.

Workflow:
1. list_instances, then describe_instance for the one matching the user's
   protocol. Each parameter has a meaning, unit, domain and default; the
   run-level parameters (rounds, security budgets, solver) are described
   once for every instance.
2. Build the config from describe_instance's default_config, changing only
   what the user declared. Exact numbers are strings: "1/8", "0.02", "3".
   Never invent a value the user did not give: ask, or keep the default
   AND tell the user it is a default. declared_tolerance is required.
3. Optionally pass the user's own measured statistics as `honest`:
   {"table": {label: prob}, "source": "<where they come from>"} or
   {"envelope": {"lower": {...}, "upper": {...}}, "source": ...}; labels are
   prepare's acceptance_alphabet.
4. prepare: the engine reads and checks the config without solving. A
   refusal names the engine's reason code; fix and retry. Show the user the
   resolved config (every default), the snaps (numbers the engine repaired
   within the declared tolerance) and the honest distribution.
   RUNTIME: every prepare reply carries `estimate` (expected_seconds,
   duration in words, and why: the photon cutoffs, windows and detector
   ports driving it; `extrapolated` past the measured range, `advice` when
   it will not finish in practice). When it may pass the budget prepare does
   not wait: it returns {state: "starting", job, kind: "prepare",
   expected_seconds, duration, why, tell_the_user}. TELL THE USER the
   expected time and its reason before waiting, poll run_status(job) (it
   shows expected vs elapsed), then prepare(job=<job>) returns the summary.
   A cheaper configuration (a smaller cutoff or window) is the user's
   choice to make.
5. start_run, then run_status until the state is final (done, refused,
   error, cancelled, lost). The run's job prepares once itself (a prepare
   call beforehand is its own cost and is not reused), which the reply's
   estimate covers; the solve comes on top, seconds to many minutes: cap it
   with config.solver.budget_seconds or max_iterations if the user wants.
6. get_report: the result and EVERY assumption with its plain-language
   user_statement, and every item the protocol document declared itself
   (user_declared: a shipped template's, such as bb84's declared POVM, as
   well as a custom document's). Walk the user through the assumptions to
   vouch for and give them the report.html path to review. Do not call the
   key rate secure on the user's behalf.

A protocol no instance describes is written as a PROTOCOL DOCUMENT:
a. Take the nearest template: list_instances names each instance's
   `template`; get_reference('template', name=<instance>) returns it as YAML
   and as a JSON object. The format: get_reference('document-guide'); the
   schema: get_reference('schema', name='protocol-document').
b. Edit a copy: a new identity.id, title and summary, no identity.readme or
   identity.record_label (packaged ids are reserved), then what differs.
   Write exact numbers as strings ("0.02", "1/50"): a JSON float becomes
   its binary64 value, recorded as a conversion.
c. describe_instance(document=<object>) or (document_file=<ABSOLUTE path to
   a .json, .yaml or .yml file>) validates it; a refusal names a reason and
   the JSON path in the document. Its default_config is the config to start
   from.
d. prepare and start_run with the same document (instance empty), as in
   steps 4-6. Everything in prepare's and the report's user_declared (a
   declared receiver POVM or characterisation, explicit constraints, a
   licence, a witness, a retention attestation) the engine did NOT derive:
   tell the user each one is theirs to vouch for.
Optical stations, decoy (wcp_decoy) sources, transcripts of any length,
several stations, factor_projection and choice weightings are lowered as
well; the optical_bb84, decoy_bb84 and bbm92 templates show them. Their
stations and source write further reserved strings, which one
reserved_identity refusal lists together: rename each (write your own
attested_by, for one) or delete the optional field or block, as the
template's header says.
A reply too large for one tool result names a file to read instead.
"""


#: The largest value of a ``keep`` key repeated beside a spilled reply.
_KEEP_CHARS: Final[int] = 2_000


def _fit(
    value: Any,
    *,
    what: str,
    spill: Path | None = None,
    keep: tuple[str, ...] = (),
) -> Any:
    """Return ``value``, or a pointer to a file holding it when it is too large.

    EVERY TOOL'S REPLY PASSES THROUGH HERE: a protocol
    document can make any reply as large as itself. The file is ``spill``, or
    one named by the reply's digest under ``<jobs>/replies/``, written
    atomically; the pointer repeats the ``keep`` keys whose values are short
    (a refusal's reason, a document's digest), so the caller learns the
    outcome without reading the file.
    """
    from runs.facade import core, jobs

    text = json.dumps(value, ensure_ascii=False, default=str)
    if len(text) <= MAX_REPLY_CHARS:
        return value
    if spill is None:
        slug = "".join(c if c.isalnum() else "-" for c in what)[:40]
        digest = core.canonical_digest(text)[:12]
        spill = jobs.jobs_root() / "replies" / f"{slug}-{digest}.json"
    spill.parent.mkdir(parents=True, exist_ok=True)
    core.write_text_atomic(spill, text)
    kept = {
        key: value[key]
        for key in keep
        if isinstance(value, dict)
        and key in value
        and len(json.dumps(value[key], default=str)) <= _KEEP_CHARS
    }
    return {
        **kept,
        "too_large_for_one_reply": True,
        "what": what,
        "size_chars": len(text),
        "file": str(spill),
        "hint": "read the file, or ask for a narrower part",
    }


#: The keys a spilled reply keeps: whether it was refused and why, and which
#: document and job it is about.
_OUTCOME: Final[tuple[str, ...]] = (
    "refused",
    "stage",
    "reason",
    "path",
    "job",
    "kind",
    "state",
    "reused",
    "instance",
    "document",
    "config_digest",
    "expected_seconds",
    "why",
)


def _guard(call: Any) -> Any:
    """Turn a lookup failure (unknown job, part, document) into a tool error."""
    try:
        return call()
    except KeyError as error:
        raise ToolError(str(error.args[0] if error.args else error)) from error


_READ_ONLY = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, open_world_hint=False
)

OptionalInstance = Annotated[
    str,
    Field(
        description="An instance id from list_instances, e.g. 'optical_bb84'. "
        "With a document: empty, or the document's identity.id."
    ),
]
Document = Annotated[
    dict[str, Any],
    Field(
        description="Optional: a custom protocol as a protocol document (a JSON "
        "object), in place of an instance. Start from get_reference('template', "
        "name=...); schema: get_reference('schema', name='protocol-document')."
    ),
]
DocumentFile = Annotated[
    str,
    Field(
        description="Optional: the ABSOLUTE path of a protocol document file "
        "(.json, .yaml or .yml, at most 1 MiB, on this machine), in place of "
        "document."
    ),
]
Config = Annotated[
    dict[str, Any],
    Field(
        description="A run configuration in RunConfig payload form: start from "
        "describe_instance's default_config. Full schema: "
        "get_reference('schema', name='run-input'), $defs/run_config."
    ),
]
OptionalConfig = Annotated[
    dict[str, Any],
    Field(
        description="A run configuration in RunConfig payload form: start from "
        "describe_instance's default_config. Full schema: "
        "get_reference('schema', name='run-input'), $defs/run_config. Not "
        "needed with job."
    ),
]
Honest = Annotated[
    dict[str, Any],
    Field(
        description="Optional: the user's own honest statistics replacing the "
        "instance's model, {'table': {label: 'p/q'}, 'source': '...'} or "
        "{'envelope': {'lower': {...}, 'upper': {...}}, 'source': '...'}. "
        "Empty object for none."
    ),
]


def build_server() -> MCPServer:
    """Return the server with its tools registered."""
    server = MCPServer(
        name="certiqs-key",
        title="CERTIQS-KEY key-rate engine",
        instructions=INSTRUCTIONS,
    )

    @server.tool(annotations=_READ_ONLY)
    def list_instances() -> dict[str, Any]:
        """List the QKD protocol instances this engine runs, and the engine's identity.

        Start here; then describe_instance for the one that matches the user's
        protocol. get_reference('workflow') explains the whole procedure.
        """
        from runs.facade import core

        return dict(
            _fit(
                {
                    "engine": core.engine_identity(),
                    "instances": core.list_instances(),
                    "next": "describe_instance(instance); "
                    "get_reference('workflow') for the procedure",
                },
                what="instances",
            )
        )

    @server.tool(annotations=_READ_ONLY)
    def describe_instance(
        instance: OptionalInstance = "",
        document: Document | None = None,
        document_file: DocumentFile = "",
    ) -> dict[str, Any]:
        """Describe one instance: each parameter's meaning, unit, domain, default.

        Returns the instance's own parameters (sections model = channel and
        device = apparatus), the run-level parameters shared by every
        instance, named presets, and a complete default_config to start from.
        The instance's README: get_reference('instance-readme', instance=...).

        With a document or document_file instead, VALIDATES that protocol
        document and describes it the same way, adding its id and digest; or
        returns a refusal with a reason and the JSON path in the document. An
        unknown instance id is a tool error; a document's problem is a refusal.
        """
        from runs.facade import core

        described = _guard(
            lambda: core.describe_instance(
                instance, document=document, document_file=document_file or None
            )
        )
        return dict(_fit(described, what="describe_instance", keep=_OUTCOME))

    @server.tool(annotations=_READ_ONLY)
    def get_reference(
        topic: Annotated[
            str,
            Field(
                description="'workflow', 'instance-readme' (with instance; optional "
                "name of another .md beside it), 'schema' (name: run-input, record, "
                "report or protocol-document), 'template' (name: an instance id; "
                "its protocol document), 'document-guide' (the protocol-document "
                "format), or 'refusal-codes'."
            ),
        ],
        instance: Annotated[str, Field(description="For 'instance-readme'.")] = "",
        name: Annotated[
            str, Field(description="Schema, document or template name.")
        ] = "",
    ) -> dict[str, Any]:
        """Read the workflow, a README, a JSON schema, a template or refusal codes."""
        from runs.facade import core, jobs

        if topic == "workflow":
            return {"workflow": INSTRUCTIONS}
        if topic == "instance-readme":
            document = _guard(lambda: core.instance_document(instance, name or None))
            fitted = dict(_fit(document, what="document"))
            fitted.setdefault("path", document["path"])
            return fitted
        if topic == "schema":
            chosen = name or "run-input"
            return {
                "name": chosen,
                "schema": _fit(
                    _guard(lambda: core.schema(chosen)),
                    spill=jobs.jobs_root() / "references" / f"schema-{chosen}.json",
                    what=f"schema {chosen}",
                ),
            }
        if topic == "template":
            template = _guard(lambda: core.template(name or instance))
            fitted = dict(
                _fit(
                    template,
                    spill=jobs.jobs_root()
                    / "references"
                    / f"template-{template['instance']}.json",
                    what=f"template {template['instance']}",
                )
            )
            fitted.setdefault("path", template["path"])
            return fitted
        if topic == "document-guide":
            guide = core.document_guide()
            fitted = dict(_fit(guide, what="document-guide"))
            fitted.setdefault("path", guide["path"])
            return fitted
        if topic == "refusal-codes":
            return {
                "input_refusal_codes": core.refusal_codes(),
                "document_refusal_codes": core.document_refusal_codes(),
            }
        raise ToolError(
            f"no topic {topic!r}; the topics are workflow, instance-readme, "
            "schema, template, document-guide, refusal-codes"
        )

    @server.tool(
        # Not read-only: past the budget it starts a worker that may run long.
        annotations=ToolAnnotations(
            read_only_hint=False, destructive_hint=False, open_world_hint=False
        )
    )
    def prepare(
        config: OptionalConfig | None = None,
        instance: OptionalInstance = "",
        honest: Honest | None = None,
        part: Annotated[
            str,
            Field(
                description="Optional: one part of the full preparation by name "
                "(the summary lists them under 'parts'), e.g. 'receiver_construction' "
                "or 'protocol_document'."
            ),
        ] = "",
        document: Document | None = None,
        document_file: DocumentFile = "",
        job: Annotated[
            str,
            Field(
                description="Optional: a preparation job id that an earlier prepare "
                "started in the background; returns its summary once finished "
                "(poll run_status first). No config needed."
            ),
        ] = "",
    ) -> dict[str, Any]:
        """Check and prepare a configuration WITHOUT solving: the dry run.

        Returns a refusal with the engine's reason code, or a summary: the
        config as the engine read it (every default resolved), the acceptance
        alphabet, the snaps, the planned stages, the honest distribution, and
        the estimate (expected seconds and why). The full preparation is
        written to a file named in 'file'. With a protocol document, also its
        id and digest; every reply lists what the document declared itself
        (user_declared), which the user vouches for.

        A preparation that may take longer than the budget (20 s by default,
        with a safety factor of 2 on the estimate) runs in the background:
        the reply is {state: 'starting', job, kind: 'prepare',
        expected_seconds, duration, why, tell_the_user}. Tell the user the
        expected time and why, poll run_status(job), then prepare(job=job).
        A run started later prepares again in its own job.
        """
        from runs.facade import core, jobs
        from runs.facade.estimate import estimate_preparation

        if job:
            result = _guard(lambda: jobs.preparation_result(job))
            if "summary" not in result:
                return dict(_fit(result["status"], what="prepare-job", keep=_OUTCOME))
            summary = result["summary"]
            return _prepared(summary, Path(summary["file"]), part)
        if config is None:
            raise ToolError("prepare needs a config, or the job of a preparation")
        s = core.resolve(instance, document, document_file or None)
        if isinstance(s, dict):
            return dict(_fit(s, what="prepare-refusal", keep=_OUTCOME))
        read = core.config_for(s, config)
        if not isinstance(read, dict):
            estimate = estimate_preparation(s, read)
            if estimate["background"]:
                started = jobs.start_preparation(
                    s, config, honest or None, estimate=estimate
                )
                return dict(
                    _fit(
                        _background(started, estimate),
                        what="prepare-job",
                        keep=_OUTCOME,
                    )
                )
        envelope = core.prepare_surface(s, config, honest or None)
        if envelope.get("refused"):
            return dict(_fit(envelope, what="prepare-refusal", keep=_OUTCOME))
        summary = jobs.write_preparation(envelope)
        return _prepared(summary, Path(summary["file"]), part)

    def _prepared(summary: dict[str, Any], spill: Path, part: str) -> dict[str, Any]:
        """Return a finished preparation's summary, or one part of it, fitted."""
        if part:
            from runs.facade.core import read_json

            record = (read_json(spill) or {}).get("preparation") or {}
            if part not in record:
                raise ToolError(f"no part {part!r}; the parts are {sorted(record)}")
            return {
                "part": part,
                "value": _fit(record[part], what=part),
                "file": str(spill),
            }
        return dict(
            _fit(
                summary,
                spill=spill.with_name(f"{spill.stem}-summary.json"),
                what="preparation summary",
                keep=(*_OUTCOME, "file"),
            )
        )

    def _background(
        started: dict[str, Any], estimate: dict[str, Any]
    ) -> dict[str, Any]:
        """Return a preparation job's start, its expected runtime and reason first."""
        from runs.facade import jobs
        from runs.facade.estimate import statement

        if started.get("refused"):
            return started
        state = started.get("state")
        if state == "done":
            # An identical request already prepared: nothing runs now.
            tell = "An identical preparation has already finished."
            then = "prepare(job=<job>) returns its summary"
        elif state in jobs.FINAL_STATES:
            tell = f"An identical preparation already ended {state}."
            then = "run_status(job) says why; prepare(job=<job>) returns what it left"
        else:
            tell = statement(estimate) + " It runs in the background."
            then = (
                "poll run_status(job) until the state is final; then "
                "prepare(job=<job>) returns the summary"
            )
        reply = {
            "state": state,
            "job": started.get("job"),
            "kind": "prepare",
            "reused": started.get("reused"),
            "expected_seconds": estimate.get("expected_seconds"),
            "duration": estimate.get("duration"),
            "why": estimate.get("why"),
            "extrapolated": estimate.get("extrapolated"),
            "budget_seconds": estimate.get("budget_seconds"),
            "basis": estimate.get("basis"),
            "instance": started.get("instance"),
            "document": started.get("document"),
            "config_digest": started.get("config_digest"),
            "tell_the_user": tell,
            "next": then,
        }
        if started.get("refusal") is not None:
            reply["refusal"] = started["refusal"]
        return reply

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False, destructive_hint=False, open_world_hint=False
        )
    )
    def start_run(
        config: Config,
        instance: OptionalInstance = "",
        honest: Honest | None = None,
        reuse: Annotated[
            bool,
            Field(
                description="Answer an identical earlier request with its job "
                "(default)."
            ),
        ] = True,
        document: Document | None = None,
        document_file: DocumentFile = "",
    ) -> dict[str, Any]:
        """Start a key-rate run in the background; returns a job id at once.

        Call prepare first, with the same instance or document. The run's job
        prepares once itself (prepare's result is not reused); the reply's
        estimate states that preparation's expected time and why, and the
        solve comes on top.

        Poll run_status(job) until the state is final, then get_report(job).
        """
        from runs.facade import jobs

        started = jobs.start_run(
            instance,
            config,
            honest or None,
            reuse=reuse,
            document=document,
            document_file=document_file or None,
        )
        return dict(_fit(started, what="start_run", keep=_OUTCOME))

    @server.tool(annotations=_READ_ONLY)
    def run_status(
        job: Annotated[
            str, Field(description="A job id; empty to list recent jobs.")
        ] = "",
    ) -> dict[str, Any]:
        """Report a job's state and progress (a run or a preparation), or list jobs.

        States: starting, running, done, refused, error, cancelled, lost.
        While it runs, compare estimate.expected_seconds with elapsed_s. A
        finished preparation job: prepare(job=...) returns its summary.

        With no job, list the most recent jobs.
        """
        from runs.facade import jobs

        if not job:
            return dict(_fit({"jobs": jobs.list_jobs()}, what="jobs"))
        status = _guard(lambda: jobs.job_status(job))
        return dict(_fit(status, what="run_status", keep=_OUTCOME))

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False, destructive_hint=True, open_world_hint=False
        )
    )
    def cancel_run(
        job: Annotated[str, Field(description="The job id to stop.")],
    ) -> dict[str, Any]:
        """Stop a running job; it ends 'cancelled' with no record.

        A finished job is left unchanged.
        """
        from runs.facade import jobs

        status = _guard(lambda: jobs.cancel_job(job))
        return dict(_fit(status, what="cancel_run", keep=_OUTCOME))

    @server.tool(annotations=_READ_ONLY)
    def get_report(
        job: Annotated[str, Field(description="A finished job id (done or refused).")],
        part: Annotated[
            str,
            Field(
                description="Optional stable path into the report: a section (result, "
                "protocol, assumptions, numerics, checks, provenance), "
                "'assumptions/A-ENS', 'inputs/rounds', 'checks/<id>', 'claims/<id>'. "
                "Or 'markdown' for the whole report as Markdown."
            ),
        ] = "",
    ) -> dict[str, Any]:
        """Return a finished run's key-rate report: the result and every assumption.

        By default a summary: result, inputs as read, honest model, and each
        assumption with its plain-language user_statement. The full report is
        in the files named under 'files' (report.html is the one for a human
        to review).
        """
        from runs.facade import core, jobs

        status = _guard(lambda: jobs.job_status(job))
        if status.get("kind") == jobs.PREPARE:
            raise ToolError(
                f"job {job!r} is a preparation; prepare(job=...) returns its summary"
            )
        directory = Path(status["directory"])
        if (
            status["state"] not in {"done", "refused"}
            or not (directory / "report.json").is_file()
        ):
            raise ToolError(
                f"job {job!r} has no report (state {status['state']!r}); "
                "a report exists once a run is done or refused by the engine"
            )
        files = {
            form: str(directory / name) for form, name in core.REPORT_FILES.items()
        }
        report = core.read_report(directory)
        if part == "markdown":
            text = (directory / core.REPORT_FILES["markdown"]).read_text(
                encoding="utf-8"
            )
            if len(text) > MAX_REPLY_CHARS:
                return {
                    "too_large_for_one_reply": True,
                    "size_chars": len(text),
                    "files": files,
                    "hint": "read report.md in pieces, or ask for parts by path",
                }
            return {"markdown": text, "files": files}
        if part:
            value = _guard(lambda: core.report_part(report, part))
            return {
                "part": part,
                "value": _fit(value, what=part),
                "files": files,
            }
        summary = {
            **core.report_summary(report),
            "files": files,
            "review": "Give the user report.html to review; each assumption to vouch "
            "for must hold for their device for the key rate to apply.",
        }
        return dict(
            _fit(summary, spill=directory / "report-summary.json", what="summary")
        )

    return server


def main() -> None:
    """Serve over stdio."""
    build_server().run("stdio")
