"""Every emitted version pin against the interface row that states it.

Each module's ``interface.yaml`` states the pin a result carries for it under
``artifact_bindings.mathematical_spec_version``, and this test compares the
two. THE DRIFT THIS CATCHES: statistics emits no version string of its own,
the run record carries ``statistics@`` followed by its module.yaml version
(read from the claim-closure table), so a statistics row that names an older
version than the record carries is wrong. A pin and its row are edited by hand
together; this test fails when one of the two is forgotten.

It also checks two necessary conditions of what PRINCIPLES.md section 6 asks
of any pin: never a draft, and never a version above the one on the module's
``version:`` line. It does not ask the pin to EQUAL that
line, because a pin moves with the code that implements a version, which may
land after the version's claims.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from certiqs_key.domain.claim_closure import module_version
from certiqs_key.meat_core.declaration.validation import (
    MATHEMATICAL_SPEC_VERSION as MEAT_CORE_PIN,
)
from certiqs_key.protocol_compiler import (
    MATHEMATICAL_SPEC_VERSION as PROTOCOL_COMPILER_PIN,
)
from certiqs_key.receiver import MATHEMATICAL_SPEC_VERSION as RECEIVER_PIN
from certiqs_key.reductions import MATHEMATICAL_SPEC_VERSION as REDUCTIONS_PIN
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.transmitter import MATHEMATICAL_SPEC_VERSION as TRANSMITTER_PIN
from certiqs_key.transmitter.decoy import MATHEMATICAL_SPEC_VERSION as DECOY_PIN

MODULES = Path(__file__).resolve().parents[2] / "spec" / "modules"

#: The string the run record carries for statistics (runs/record.py).
STATISTICS_PIN = f"statistics@{module_version('statistics')}"

#: (module directory under spec/modules, the module whose version the pin
#: names, the pin emitted for it). A submodule emits no artefact of its own and
#: states its core's pin, so its row names the core.
PINS: tuple[tuple[str, str, str], ...] = (
    ("meat-core", "meat-core", MEAT_CORE_PIN),
    ("meat-core/frank-wolfe", "meat-core", MEAT_CORE_PIN),
    ("protocol-compiler", "protocol-compiler", PROTOCOL_COMPILER_PIN),
    ("receiver", "receiver", RECEIVER_PIN),
    ("reductions", "reductions", REDUCTIONS_PIN),
    ("reductions/wpfss", "reductions", REDUCTIONS_PIN),
    ("transmitter", "transmitter", TRANSMITTER_PIN),
    ("transmitter/decoy", "transmitter/decoy", DECOY_PIN),
    ("statistics", "statistics", STATISTICS_PIN),
    ("statistics/binomial-box", "statistics", STATISTICS_PIN),
)

#: The removable submodules with a row above (spec/modules.yaml): where a
#: directory is absent its row skips, and every other row is checked as before.
REMOVABLE: tuple[str, ...] = ()
PIN_PARAMS = [
    pytest.param(
        *row,
        marks=pytest.mark.skipif(
            row[0] in REMOVABLE and not (MODULES / row[0]).is_dir(),
            reason=f"{row[0]} is not in this tree",
        ),
    )
    for row in PINS
]


def _yaml(path: Path) -> dict[str, Any]:
    document: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return document


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


@pytest.mark.parametrize(("directory", "named", "pin"), PIN_PARAMS)
def test_the_interface_row_states_the_emitted_pin(
    directory: str, named: str, pin: str
) -> None:
    """``artifact_bindings.mathematical_spec_version`` is the string emitted."""
    bindings = _yaml(MODULES / directory / "interface.yaml")["artifact_bindings"]
    assert bindings["mathematical_spec_version"] == pin, directory


@pytest.mark.parametrize(("directory", "named", "pin"), PIN_PARAMS)
def test_the_pin_is_no_draft_and_no_later_than_module_yaml(
    directory: str, named: str, pin: str
) -> None:
    """The module id, then a non-draft version no later than module.yaml's."""
    module_id, _, version = pin.partition("@")
    assert module_id == named
    assert "draft" not in version
    current = str(_yaml(MODULES / named / "module.yaml")["version"])
    assert _version(version) <= _version(current), (pin, current)


def test_the_reductions_artifact_default_is_the_package_pin() -> None:
    """The artifact's default is a literal beside the package constant, and equal."""
    field = ProofReductionArtifact.__dataclass_fields__["mathematical_spec_version"]
    assert field.default == REDUCTIONS_PIN
