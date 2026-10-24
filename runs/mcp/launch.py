"""Start the CERTIQS-KEY MCP server from any directory, or print a client config.

WHY THIS EXISTS. An MCP client starts a server as ``command`` plus ``args``,
from a working directory of its own choosing (Claude Code's and Cursor's
configurations carry no ``cwd``), and the server needs this repository on its
import path, because ``instances/`` and ``runs/`` are not installed
(``instances/NOTES.md``). So clients are configured with the absolute path of
THIS file, which puts the repository on the path itself and serves. It uses
only the standard library until then, so that a client configured with a
Python that lacks the engine's dependencies is handed on to the repository's
virtual environment instead of failing.

    python runs/mcp/launch.py                       serve over stdio
    python runs/mcp/launch.py --print-config claude|cursor|codex|all
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER_NAME = "certiqs-key"


def _venv_python() -> Path | None:
    configured = os.environ.get("CERTIQS_KEY_PYTHON")
    candidates = [Path(configured)] if configured else []
    candidates += [
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
    ]
    return next((path for path in candidates if path.is_file()), None)


def _has_dependencies() -> bool:
    try:
        import mcp.server.mcpserver  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


def _config_snippets(python: Path) -> dict[str, str]:
    launch = Path(__file__).resolve()
    command, arg = python.as_posix(), launch.as_posix()
    entry = {"command": command, "args": [arg]}
    return {
        "claude": (
            "# Claude Code: run once (user scope: every project can use it)\n"
            f'claude mcp add {SERVER_NAME} --scope user -- "{command}" "{arg}"\n'
            "# or, in a project's .mcp.json:\n"
            + json.dumps(
                {"mcpServers": {SERVER_NAME: {"type": "stdio", **entry}}}, indent=2
            )
            + "\n# A run is a background job, so the default tool timeout suffices."
        ),
        "cursor": (
            "// Cursor: ~/.cursor/mcp.json (global) or <project>/.cursor/mcp.json\n"
            + json.dumps({"mcpServers": {SERVER_NAME: entry}}, indent=2)
        ),
        "codex": (
            "# Codex: ~/.codex/config.toml, or <project>/.codex/config.toml in a "
            "trusted project\n"
            f"[mcp_servers.{SERVER_NAME}]\n"
            f"command = '{command}'\n"
            f"args = ['{arg}']\n"
            "# the first call imports the engine (a few seconds); give it room\n"
            "startup_timeout_sec = 30\n"
            "tool_timeout_sec = 120"
        ),
    }


def main(argv: list[str]) -> int:
    """Serve, or print the configuration ``argv`` asks for; return the exit code."""
    if argv[:1] == ["--print-config"]:
        snippets = _config_snippets(_venv_python() or Path(sys.executable))
        wanted = argv[1] if len(argv) > 1 else "all"
        if wanted != "all" and wanted not in snippets:
            print(
                f"unknown client {wanted!r}; one of {sorted(snippets)} or all",
                file=sys.stderr,
            )
            return 2
        for name, text in snippets.items():
            if wanted in ("all", name):
                print(text, end="\n\n")
        return 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 2
    if not _has_dependencies():
        venv = _venv_python()
        if venv is None or Path(sys.executable).resolve() == venv.resolve():
            print(
                "certiqs-key MCP: this Python lacks the engine's dependencies; "
                "install them with pip install -e '.[oracle-qics,certify,mcp]' "
                "(README.md)",
                file=sys.stderr,
            )
            return 1
        # Hand over to the repository's environment; stdio is inherited.
        return subprocess.call([str(venv), str(Path(__file__).resolve())])
    for path in (ROOT, ROOT / "src"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from runs.mcp.server import main as serve

    serve()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
