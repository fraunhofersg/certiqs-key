"""The run tier as JSON in, JSON out: one facade every outward adapter calls.

WHY THIS EXISTS. ``PRINCIPLES.md`` section 9 ("Clear piping") names the
external interfaces -- a CLI, HTTP, an MCP server -- as ADAPTERS over the artefact
schemas, never second interfaces with semantics of their own. Each adapter
(the MCP server ``runs/mcp``, the gateway of a separate application) needs the same
wiring an outside caller needs (discover the instances, read and key-check a
configuration, prepare, run with an oracle, record, report). This is the one
copy of it, in the engine, so that every adapter calls the same functions and
none decides anything of its own.

WHY HERE AND NOT UNDER ``src/certiqs_key/runs``. ``spec/architecture.md`` 3.5:
"no run imports an instance". The facade enumerates and drives instances, so
it sits above them, in this repository-level package where a user docks, like
``runs/report_examples``.

    core     instances, configurations, preparation, reports (seconds)
    jobs     a run as a background job: a directory of files, no database
    worker   ``python -m runs.facade.worker JOB_DIR``: the one process a job is

Every function returns JSON-native data. A request the engine refuses is
returned as data in ONE shape, ``{"refused": true, "stage", "reason",
"detail"}``; anything else the
engine raises is an error, never a refusal.
"""
