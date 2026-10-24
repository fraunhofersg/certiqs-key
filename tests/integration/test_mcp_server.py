"""The MCP server, as a client sees it: few tools, flat inputs, replies that fit.

The constraints come from the three clients it is built for
(``runs/mcp/server.py`` docstring): Cursor loads about 40 tools across all
servers, some clients drop ``$ref`` in tool input schemas, and Claude Code
caps one tool result at 25k tokens. One test drives the whole workflow over a
real stdio connection through the launcher, from a working directory outside
the repository, as a client configured by ``launch.py --print-config`` would;
it runs a packaged instance and then a CUSTOM protocol document -- the bb84
template with the Y basis in place of X -- to a report.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import anyio
import pytest

pytest.importorskip("mcp")

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from runs.mcp.server import MAX_REPLY_CHARS, build_server
from tests.support.declared_documents import bb84_tree, y_basis

ROOT = Path(__file__).resolve().parents[2]
TOOLS = {
    "list_instances",
    "describe_instance",
    "get_reference",
    "prepare",
    "start_run",
    "run_status",
    "cancel_run",
    "get_report",
}


def _body(result: Any) -> Any:
    assert not result.is_error, result.content[0].text
    if result.structured_content is not None:
        return result.structured_content
    return json.loads(result.content[0].text)


def _keys(schema: Any) -> set[str]:
    """Every key used anywhere in a JSON schema (not inside its strings)."""
    if isinstance(schema, dict):
        return set(schema).union(*(_keys(value) for value in schema.values()))
    if isinstance(schema, list):
        return set().union(*(_keys(value) for value in schema))
    return set()


def test_the_tools_are_few_with_flat_input_schemas() -> None:
    async def listed() -> list[Any]:
        async with Client(build_server()) as client:
            return list((await client.list_tools()).tools)

    tools = anyio.run(listed)
    assert {tool.name for tool in tools} == TOOLS
    for tool in tools:
        assert not _keys(tool.input_schema) & {"$ref", "$defs"}, tool.name
        assert tool.description, tool.name
        assert len(tool.name) <= 20
    # A custom protocol enters through the three tools that take an instance.
    by_name = {tool.name: tool for tool in tools}
    for name in ("describe_instance", "prepare", "start_run"):
        properties = by_name[name].input_schema["properties"]
        assert {"instance", "document", "document_file"} <= set(properties), name
        assert "instance" not in by_name[name].input_schema.get("required", [])


def test_a_retired_parameter_is_refused_over_mcp() -> None:
    """A retired parameter is refused through the MCP tool too."""

    async def session() -> dict[str, Any]:
        async with Client(build_server()) as client:
            described = _body(
                await client.call_tool("describe_instance", {"instance": "bb84"})
            )
            config = copy.deepcopy(described["default_config"])
            config["parameters"]["strict_certification"] = True
            refused: dict[str, Any] = _body(
                await client.call_tool(
                    "prepare", {"instance": "bb84", "config": config}
                )
            )
            return refused

    refused = anyio.run(session)
    assert refused["refused"] is True
    assert refused["reason"] == "retired_parameter"
    assert "strict_snaps" in refused["detail"]


def test_reference_and_refusals_need_no_engine_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A reference too large for one reply is written under the jobs directory.
    monkeypatch.setenv("CERTIQS_KEY_JOBS_DIR", str(tmp_path / "jobs"))

    async def session() -> dict[str, Any]:
        async with Client(build_server()) as client:
            workflow = _body(
                await client.call_tool("get_reference", {"topic": "workflow"})
            )
            schema = _body(
                await client.call_tool(
                    "get_reference", {"topic": "schema", "name": "run-input"}
                )
            )
            unknown = await client.call_tool("describe_instance", {"instance": "nope"})
            refused = _body(
                await client.call_tool(
                    "prepare", {"instance": "bb84", "config": {"rounds": 10}}
                )
            )
            template = _body(
                await client.call_tool(
                    "get_reference", {"topic": "template", "name": "bb84"}
                )
            )
            no_template = await client.call_tool(
                "get_reference", {"topic": "template", "name": "nope"}
            )
            guide = _body(
                await client.call_tool("get_reference", {"topic": "document-guide"})
            )
            document_schema = _body(
                await client.call_tool(
                    "get_reference", {"topic": "schema", "name": "protocol-document"}
                )
            )
            codes = _body(
                await client.call_tool("get_reference", {"topic": "refusal-codes"})
            )
            # The template passed back unedited is a packaged identity: refused
            # as data, with the path to change.
            reserved = _body(
                await client.call_tool(
                    "describe_instance", {"document": template["document"]}
                )
            )
            return {
                "workflow": workflow,
                "schema": schema,
                "unknown": unknown,
                "refused": refused,
                "template": template,
                "no_template": no_template,
                "guide": guide,
                "document_schema": document_schema,
                "codes": codes,
                "reserved": reserved,
            }

    out = anyio.run(session)
    assert "prepare" in out["workflow"]["workflow"]
    assert "document" in out["workflow"]["workflow"]
    assert "run_request" in out["schema"]["schema"]["$defs"]
    assert out["unknown"].is_error
    assert out["refused"]["refused"] is True
    assert out["template"]["document"]["identity"]["id"] == "bb84"
    assert out["template"]["yaml"].startswith("# The bb84 instance")
    assert out["no_template"].is_error
    assert out["guide"]["markdown"].startswith("# Protocol documents")
    # The schema is larger than one reply: it is always written to a file.
    spilled = out["document_schema"]["schema"]
    assert spilled["too_large_for_one_reply"] is True
    assert json.loads(Path(spilled["file"]).read_text(encoding="utf-8"))["$defs"]
    assert "reserved_identity" in out["codes"]["document_refusal_codes"]
    assert out["codes"]["input_refusal_codes"]
    assert out["reserved"]["stage"] == "document"
    assert out["reserved"]["reason"] == "reserved_identity"
    assert out["reserved"]["path"].startswith("/identity/")
    for key, value in out.items():
        if not hasattr(value, "is_error"):
            assert len(json.dumps(value)) <= MAX_REPLY_CHARS, key


def _large_document() -> dict[str, Any]:
    """Return the bb84 template with 300 unused parameter rows of float numbers.

    Each row's default and bounds are JSON floats, so the document carries 900
    conversion records: every reply about it is far past one tool result.
    """
    tree = bb84_tree()
    del tree["identity"]["readme"], tree["identity"]["record_label"]
    tree["identity"]["id"] = "my_large_bb84"
    template = tree["parameters"]["table"][0]
    for index in range(300):
        tree["parameters"]["table"].append(
            {
                **template,
                "name": f"unused_{index}",
                "default": 0.1,
                "domain": {"form": "interval", "lower": 0.05, "upper": 0.45},
            }
        )
    return tree


def test_every_reply_about_a_large_document_fits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CERTIQS_KEY_JOBS_DIR", str(tmp_path / "jobs"))
    document = _large_document()
    unknown_key = copy.deepcopy(document)
    unknown_key["stations"][0]["measurement"]["x" * 100_000] = 1

    async def session() -> dict[str, Any]:
        async with Client(build_server()) as client:
            described = _body(
                await client.call_tool("describe_instance", {"document": document})
            )
            config = json.loads(Path(described["file"]).read_text(encoding="utf-8"))[
                "default_config"
            ]
            prepared = _body(
                await client.call_tool(
                    "prepare", {"document": document, "config": config}
                )
            )
            refused = _body(
                await client.call_tool("describe_instance", {"document": unknown_key})
            )
            return {"described": described, "prepared": prepared, "refused": refused}

    out = anyio.run(session)
    for key, reply in out.items():
        assert len(json.dumps(reply)) <= MAX_REPLY_CHARS, key
    described, prepared = out["described"], out["prepared"]
    assert described["too_large_for_one_reply"] is True
    assert described["document"]["id"] == "my_large_bb84"
    full = json.loads(Path(described["file"]).read_text(encoding="utf-8"))
    assert len(full["conversions"]) == 900
    assert prepared["too_large_for_one_reply"] is True
    assert prepared["refused"] is False
    assert prepared["document"]["digest"] == described["document"]["digest"]
    assert Path(prepared["file"]).is_file()
    assert out["refused"]["reason"] == "document_schema_violation"


FINAL = {"done", "refused", "error", "cancelled", "lost"}


async def _finish(client: Client, started: dict[str, Any]) -> dict[str, Any]:
    """Poll a job's status until it is final."""
    status = started
    with anyio.fail_after(300):
        while status["state"] not in FINAL:
            await anyio.sleep(1)
            status = _body(
                await client.call_tool("run_status", {"job": started["job"]})
            )
    return status


async def _custom_protocol(client: Client, replies: dict[str, Any]) -> None:
    """Run a custom protocol as an agent writes one: the bb84 template, edited.

    The Y basis replaces X (``tests/support/declared_documents.py``), so the
    document is no instance's; it is validated, prepared and run through the
    tools alone.
    """
    template = _body(
        await client.call_tool("get_reference", {"topic": "template", "name": "bb84"})
    )
    document = template["document"]
    document["identity"] = {
        "id": "my_y_bb84",
        "title": "Qubit BB84 in the Z and Y bases",
        "summary": "The bb84 template with the Y basis in place of X.",
    }
    y_basis(document)
    described = _body(
        await client.call_tool("describe_instance", {"document": document})
    )
    replies["document_described"] = described
    config = described["default_config"]
    config["solver"] = {"max_iterations": 5}
    replies["document_prepare"] = _body(
        await client.call_tool(
            "prepare", {"instance": "", "document": document, "config": config}
        )
    )
    started = _body(
        await client.call_tool("start_run", {"document": document, "config": config})
    )
    replies["document_started"] = started
    replies["document_status"] = await _finish(client, started)
    replies["document_report"] = _body(
        await client.call_tool("get_report", {"job": started["job"]})
    )


@pytest.mark.requires_qics
def test_the_workflow_over_stdio_from_outside_the_repository(tmp_path: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "runs" / "mcp" / "launch.py")],
        env={"CERTIQS_KEY_JOBS_DIR": str(tmp_path / "jobs")},
        cwd=str(tmp_path),
    )

    async def session() -> dict[str, Any]:
        async with Client(params, read_timeout_seconds=120) as client:
            replies: dict[str, Any] = {}
            listed = await client.call_tool("list_instances", {})
            replies["list"] = _body(listed)
            described = _body(
                await client.call_tool(
                    "describe_instance", {"instance": "optical_bb84"}
                )
            )
            config = described["default_config"]
            config["solver"] = {"max_iterations": 5}
            replies["prepare"] = _body(
                await client.call_tool(
                    "prepare", {"instance": "optical_bb84", "config": config}
                )
            )
            started = _body(
                await client.call_tool(
                    "start_run", {"instance": "optical_bb84", "config": config}
                )
            )
            replies["status"] = await _finish(client, started)
            replies["report"] = _body(
                await client.call_tool("get_report", {"job": started["job"]})
            )
            replies["part"] = _body(
                await client.call_tool(
                    "get_report", {"job": started["job"], "part": "inputs/rounds"}
                )
            )
            await _custom_protocol(client, replies)
            replies["sizes"] = [
                len(json.dumps(value))
                for key, value in replies.items()
                if key != "sizes"
            ]
            return replies

    out = anyio.run(session)
    assert "optical_bb84" in [entry["id"] for entry in out["list"]["instances"]]
    assert out["prepare"]["refused"] is False
    assert Path(out["prepare"]["file"]).is_file()
    assert out["status"]["state"] == "done", out["status"]
    assert out["report"]["result"]["key_length"] == out["status"]["key_length"]
    assert Path(out["report"]["files"]["html"]).is_file()
    assert out["part"]["value"]["value"] == 10000
    assert max(out["sizes"]) <= MAX_REPLY_CHARS
    # The custom document: validated, prepared, run, and reported as itself.
    listed = {entry["id"]: entry for entry in out["list"]["instances"]}
    assert listed["bb84"]["template"] == "instances/bb84/protocol.yaml"
    document = out["document_described"]["document"]
    assert document["id"] == "my_y_bb84" and document["packaged"] is False
    prepared = out["document_prepare"]
    assert prepared["refused"] is False, prepared
    assert prepared["document"]["digest"] == document["digest"]
    assert [item["kind"] for item in prepared["user_declared"]] == ["receiver_povm"]
    assert "protocol_document" in prepared["parts"]
    started = out["document_started"]
    assert started["job"].startswith("declared_my_y_bb84-")
    assert started["document"]["digest"] == document["digest"]
    status = out["document_status"]
    assert status["state"] == "done", status
    report = out["document_report"]
    assert report["document"]["digest"] == document["digest"]
    assert report["document"]["packaged"] is False
    declared = report["result"]["user_declared"]
    assert "receiver_povm" in [item["kind"] for item in declared]
    vouched = [
        entry
        for entry in report["assumptions_to_vouch_for"]
        if entry.get("user_declared")
    ]
    assert "receiver_povm" in [entry["kind"] for entry in vouched]
