"""Bit-for-bit regression pins, kept per platform.

WHY THIS EXISTS. A pin of ``float.hex()`` holds only on the platform that
recorded it. Another BLAS (Accelerate on macOS arm64 against the OpenBLAS of
the Windows wheels) rounds a matrix product differently in its last bit, and a
Frank-Wolfe run of 12 to 30 iterations carries that to about 1e-8 relative
(harness/PITFALLS.md).
Re-recording on one machine only moves the red to the other. Pins are
keyed by platform: EXACT WHEREVER A VALUE WAS RECORDED ON THAT PLATFORM, AND A
NEW PLATFORM RECORDS ITS OWN PINS; a platform, case or field with none
recorded SKIPS rather than fails, so a default suite on an unrecorded platform
is green and says what it did not compare. The tests that use
these pins carry the ``pins`` marker and the default tier deselects them
(tests/conftest.py): a pin is the maintainer's check on the machine that
recorded it, run with ``pytest -m pins``.

THE KEY is ``<system>-<machine>-<blas>``: :func:`platform.system`,
:func:`platform.machine` and the BLAS numpy was built against, as
``numpy.show_config(mode="dicts")`` names it. Two machines with the same key
can still differ where a BLAS dispatches on the CPU at run time (OpenBLAS's
DYNAMIC_ARCH builds do); a pin that fails on a machine whose key IS recorded
is then a finding to report, not a value to overwrite.

WHAT A TABLE HOLDS. ``{platform key: {case: {field: pinned string}}}``. A
recorded field is compared EXACTLY, and a mismatch fails. A field, a case or a
platform with no recorded value SKIPS, with a message that names the key, the
file to edit and the values this run produced, ready to paste once the run has
been checked to be the one the pin describes (each float within a stated
relative distance of a recorded platform's value). Nothing is ever recorded
automatically: a test that wrote its own expectation would pin whatever the
code did, which is what PRINCIPLES.md section 2.3 forbids of an oracle and what
a regression pin would then no longer catch.
"""

from __future__ import annotations

import platform
from collections.abc import Mapping
from functools import cache

import numpy as np
import pytest

__all__ = ["PinTable", "assert_pinned", "platform_key"]

#: ``{platform key: {case: {field: pinned string}}}``.
type PinTable = Mapping[str, Mapping[str, Mapping[str, str]]]

#: The platform the pins of this repository were first recorded on: the
#: Windows development machine, whose numpy wheel links OpenBLAS.
WINDOWS_AMD64_OPENBLAS = "Windows-AMD64-scipy-openblas"

#: macOS on Apple Silicon with numpy on Accelerate, where the cross-platform
#: report ran the suite and recorded one value per case for five cases.
DARWIN_ARM64_ACCELERATE = "Darwin-arm64-accelerate"


@cache
def platform_key() -> str:
    """Return ``<system>-<machine>-<blas>`` for the running interpreter."""
    try:
        config = np.show_config(mode="dicts")
        blas = str(config["Build Dependencies"]["blas"]["name"])
    except (KeyError, TypeError):  # pragma: no cover - an unusual numpy build
        blas = "unknown-blas"
    return f"{platform.system()}-{platform.machine()}-{blas}"


def assert_pinned(
    table: PinTable, case: str, observed: Mapping[str, str], *, where: str
) -> None:
    """Compare ``observed`` with the pins recorded for ``case`` on this platform.

    ``where`` names the table for the message: the file and the constant a
    reader edits to record a value.
    """
    key = platform_key()
    recorded = table.get(key, {}).get(case)
    if recorded is None:
        pytest.skip(
            f"no bit-for-bit pins are recorded for case {case!r} on platform "
            f"{key!r}, so this run was not compared. Such pins hold only on the "
            "platform that recorded them (tests/support/platform_pins.py). To "
            "record this platform's, check that this run is the one the pin "
            f"describes and add under {key!r} in {where}:\n    {case!r}: "
            f"{dict(observed)!r},"
        )
    missing = {name: value for name, value in observed.items() if name not in recorded}
    for name, value in recorded.items():
        assert observed.get(name) == value, (
            f"{case!r}, field {name!r}, platform {key!r}: pinned {value!r}, "
            f"obtained {observed.get(name)!r}. A bit-for-bit pin can differ "
            "between machines that share this key: OpenBLAS picks its kernel by "
            "CPU at run time, and near-tie choices in the solver can amplify a "
            "last-bit difference. Such a difference is expected and harmless "
            "(harness/PITFALLS.md, 'Running checks')"
        )
    if missing:
        pytest.skip(
            f"case {case!r} on platform {key!r} has no pin recorded for "
            f"{sorted(missing)}; the recorded fields matched and these were not "
            f"compared. To record the rest, add to the {case!r} entry under "
            f"{key!r} in {where}: {missing!r}"
        )
