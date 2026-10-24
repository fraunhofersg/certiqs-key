"""harness/same_code.py: what to read before reusing records of an earlier tree."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_tool() -> ModuleType:
    """Return ``harness/same_code.py``, loaded by path (see test_check_history.py)."""
    name = "_harness_same_code"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, REPO_ROOT / "harness" / "same_code.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


tool = _load_tool()


def _tree(root: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


OLD_DOC = '"""Old."""\n\ndef f():\n    """Old."""\n    return 1  # old\n'
NEW_DOC = '"""New."""\n\ndef f():\n    """New."""\n    return 1  # new\n'


def test_comments_and_docstrings_are_counted_not_listed(tmp_path: Path) -> None:
    old = _tree(tmp_path / "a", {"src/m.py": OLD_DOC})
    new = _tree(tmp_path / "b", {"src/m.py": NEW_DOC})
    found, comment_only = tool.compare(old, new)
    assert comment_only == 1
    assert not any(found.values())
    assert tool.main([str(old), str(new)]) == 0


def test_code_data_and_one_sided_files_are_listed(tmp_path: Path) -> None:
    old = _tree(tmp_path / "a", {
        "src/m.py": "X = 1\n", "instances/p.yaml": "rounds: 10\n",
        "runs/gone.py": "", "runs/data/r.json": "{}"})
    new = _tree(tmp_path / "b", {
        "src/m.py": "X = 2\n", "instances/p.yaml": "rounds: 20\n",
        "runs/added.py": "", "runs/data/r.json": "[]"})
    found, _ = tool.compare(old, new, exclude=["runs/data"])
    assert found == {"code": ["src/m.py"], "other": ["instances/p.yaml"],
                     "old only": ["runs/gone.py"], "new only": ["runs/added.py"]}
    assert tool.main([str(old), str(new)]) == 1


def test_a_changed_message_string_is_code(tmp_path: Path) -> None:
    old = _tree(tmp_path / "a", {"src/m.py": 'def f():\n    raise ValueError("a")\n'})
    new = _tree(tmp_path / "b", {"src/m.py": 'def f():\n    raise ValueError("b")\n'})
    assert tool.compare(old, new)[0]["code"] == ["src/m.py"]
