"""Shared pytest plumbing.

Test-harness infrastructure only -- no fixtures that encode mathematics. Four
markers are declared in pyproject.toml:

    contract        exercises a claim of an accepted contract
    oracle          compares against the independent oracle registry
    requires_qics   needs the optional QICS LinearOracle
    slow            excluded from a tight edit loop
    pins            bit-for-bit regression pins, excluded by default

THE THREE TIERS
===============
A `smoke` marker and a default tier that deselects `slow`, with the smoke tier
running in under a minute. The three tiers are:

    smoke     `pytest -m smoke`  the wiring, in under a minute
    default   `pytest`           everything except `slow` and `pins`
    full      `pytest --full`    everything, `slow` and `pins` included

A `pins` test compares a solver run bit for bit with a value recorded on one
machine (tests/support/platform_pins.py). It holds only there: OpenBLAS picks
its kernel by CPU at run time, and near-tie choices in the pairwise rule carry
a last-bit difference far, while every bound stays sound
(harness/PITFALLS.md). The default tier leaves them out so that it is never
red for that reason; `pytest -m pins` runs them on the recording machine.

`--full` IS A FLAG AND NOT `-m ""`, and that is forced rather than chosen:
pytest's default for `markexpr` is the empty string, so `-m ""` is
INDISTINGUISHABLE at the option level from passing no `-m` at all, and a full
tier spelled that way would silently be the default tier. A flag says what it
means and can be read back.

`smoke` IS REGISTERED HERE AND NOT IN pyproject.toml, and the deselection is
implemented here too, because pyproject.toml declares the markers a tool
enforces and this one is owned by the tier logic beside it. `--strict-markers`
is satisfied by the `addinivalue_line` below, which is pytest's own supported
route for a marker a conftest owns.

WHY THE DEFAULT DESELECTS RATHER THAN THE INI FILE DOING IT. An `addopts` of
`-m "not slow"` would be silently overridden by any caller passing its own
`-m`, which is exactly what the full tier does; deselecting in
`pytest_collection_modifyitems` and STANDING DOWN when the caller supplied a
`-m` of their own keeps one rule with one exception instead of two rules that
can disagree. A deselected test is reported as deselected, never as passed.

`requires_qics` is auto-skipped rather than failed when its dependency is
absent. That is deliberate and is NOT fail-closed behaviour: the capability
probe raising when a required oracle is missing is itself a test, and it must
run precisely when the dependency is not installed.

Two helper trees are put on ``sys.path`` here, once, so that no test module has
to do it inline and the order never depends on which subset was collected.
pyproject.toml's ``pythonpath = ["."]`` puts the repository root there; these
two are directories INSIDE ``tests/``, which the tests import by bare name
(``from registry_receiver_povm import ...``), so they need their own entries:

``tests/oracles``
    the FROZEN, hand-derived registries (PRINCIPLES.md §2.3). Read-only: they
    may be imported and may not be modified, moved, reformatted, extended or
    regenerated from the code they test.

``tests/support``
    helpers the suites share, today ``receiver_povm_support``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

for _helper_tree in ("oracles", "support"):
    _path = str(Path(__file__).resolve().parent / _helper_tree)
    if _path not in sys.path:
        sys.path.insert(0, _path)

QICS_AVAILABLE = importlib.util.find_spec("qics") is not None


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip tests whose optional dependency is not installed."""
    if not QICS_AVAILABLE and item.get_closest_marker("requires_qics"):
        pytest.skip(
            "QICS is not installed; install with: "
            'pip install -e ".[oracle-qics]" '
            "(pyproject.toml's oracle-qics extra pins the version)"
        )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add ``--full``, the opt-in that stops the default tier deselecting."""
    parser.addoption(
        "--full",
        action="store_true",
        default=False,
        help=(
            "run the FULL tier: everything, `slow` included. The default tier "
            "deselects `slow`; this is the opt-in that "
            'stops it. It is a flag rather than `-m ""` because pytest\'s '
            'default markexpr IS the empty string, so `-m ""` cannot be '
            "told apart from passing no -m at all."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the one marker this file owns. See the module docstring."""
    config.addinivalue_line(
        "markers",
        "smoke: the wiring check -- one point of each path, under a minute in "
        "total. A smoke test asserts that the stages "
        "compose and that the record has its shape; it asserts NO NUMBER a "
        "contract owns, because a tier that can be skipped must not be the "
        "only place a claim is exercised.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Deselect ``slow`` and ``pins`` on the DEFAULT tier, and only there.

    Stands down entirely under ``--full``, and when the caller supplied a
    ``-m`` of their own -- the smoke tier is ``-m smoke`` -- so a caller's
    selection is never intersected with a second one behind their back.
    """
    if config.getoption("--full") or config.option.markexpr:
        return
    kept, deselected = [], []
    for item in items:
        excluded = item.get_closest_marker("slow") or item.get_closest_marker("pins")
        (deselected if excluded else kept).append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = kept
