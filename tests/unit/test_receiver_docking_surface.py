"""The docking adapter is OFF the package surface, and is the only importer.

PRINCIPLES.md section 4 and spec/architecture.md section 3.5: imports point
downward only, and a module does not carry another module's package on its own
surface. ``docking.py`` is the sanctioned exception, and the exception is only
worth anything if it is enforced -- so both halves are asserted here:

* importing :mod:`certiqs_key.receiver` does NOT put ``certiqs_key.reductions`` on the
  import path, checked in a FRESH INTERPRETER so that no other test in the
  session can make the check pass or fail by accident;
* the abstract syntax tree of every module of the package except ``docking.py``
  names no ``certiqs_key.reductions`` import at all.

The subprocess is deliberate. A ``sys.modules`` assertion inside the session is
a statement about everything pytest has collected, not about the package -- the
same reason the frozen registry's integrity test gives.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2] / "src" / "certiqs_key" / "receiver"
DOCKING = "docking.py"


def _modules() -> list[Path]:
    """Return every source module of the receiver package."""
    return sorted(PACKAGE.glob("*.py"))


@pytest.mark.contract
def test_importing_the_package_does_not_import_the_consumer() -> None:
    """A fresh interpreter: the package surface stays clean."""
    program = (
        "import sys; import certiqs_key.receiver; "
        "print('certiqs_key.reductions' in sys.modules, "
        "hasattr(certiqs_key.receiver, 'docking'), "
        "'docking' in certiqs_key.receiver.__all__)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.split() == ["False", "False", "False"], completed.stdout


@pytest.mark.contract
def test_importing_the_adapter_does_import_the_consumer() -> None:
    """The exception is real: the adapter names the consumer's types."""
    program = (
        "import sys; import certiqs_key.receiver.docking; "
        "print('certiqs_key.reductions' in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.split() == ["True"], completed.stdout


@pytest.mark.contract
def test_only_the_adapter_names_the_consumer_package() -> None:
    """Every other module of the package imports no ``certiqs_key.reductions``."""
    offenders: list[tuple[str, int, str]] = []
    adapter_imports = 0
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            named: list[str] = []
            if isinstance(node, ast.Import):
                named = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                named = [node.module or ""]
            for name in named:
                if not name.startswith("certiqs_key.reductions"):
                    continue
                if path.name == DOCKING:
                    adapter_imports += 1
                else:
                    offenders.append((path.name, node.lineno, name))
    assert offenders == []
    assert adapter_imports >= 1, "the adapter is expected to name the consumer"


@pytest.mark.contract
def test_the_adapter_is_not_reachable_from_the_package_surface() -> None:
    """``__init__`` neither imports nor re-exports it; a caller uses its name."""
    init = ast.parse((PACKAGE / "__init__.py").read_text(encoding="utf-8"))
    for node in ast.walk(init):
        if isinstance(node, ast.ImportFrom):
            assert node.module != "certiqs_key.receiver.docking"
            assert "docking" not in {alias.name for alias in node.names}
        if isinstance(node, ast.Import):
            assert all(
                alias.name != "certiqs_key.receiver.docking" for alias in node.names
            )
    import certiqs_key.receiver as package

    assert "docking" not in package.__all__
    # And nothing else in the package reaches it either.
    for path in _modules():
        if path.name in {DOCKING, "__init__.py"}:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module != "certiqs_key.receiver.docking", path.name


@pytest.mark.contract
def test_the_adapter_modifies_nothing_it_reads() -> None:
    """The conversion is one-directional: no consumer type is constructed here.

    A structural reading of the rule the module docstring states -- "Nothing in
    the consuming module is modified and nothing reads back the other way". What
    the adapter may do is CALL the consumer's constructors; what it may not do
    is import anything that would let it mutate the consumer's package, and
    there is nothing of that kind in its import list.
    """
    tree = ast.parse((PACKAGE / DOCKING).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert imported == {
        "__future__",
        "collections.abc",
        "dataclasses",
        "enum",
        "fractions",
        "numpy",
        "certiqs_key.receiver.artifact",
        "certiqs_key.receiver.numerics",
        "certiqs_key.receiver.reasons",
        "certiqs_key.foundations.exact",
        "certiqs_key.reductions.inputs",
    }
    # No consumer module that DECIDES anything is imported: the adapter converts
    # and the consumer judges.
    assert "certiqs_key.reductions.validation" not in imported
    assert "certiqs_key.reductions.emit" not in imported

