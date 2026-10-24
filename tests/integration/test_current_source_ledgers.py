"""Current matrix-source artifacts carry no ``source_stage_empty`` ledger row.

That key (A-NOSRC's) is pinned absent on the public preparation paths of the
instance constructors; historical serialized records and frozen registry values
are not rewritten.
"""

from importlib import import_module

import pytest

from certiqs_key.runs.pipeline import Preparation


@pytest.mark.parametrize(
    ("instance", "device"),
    [
        ("bb84", {}),
        ("optical_bb84", {"route": "encoded"}),
        ("optical_bb84", {"route": "licensed"}),
        ("optical_bb84", {"route": "licensed+two-sector"}),
    ],
)
def test_public_matrix_sources_emit_current_conditional_ledger(
    instance: str, device: dict[str, str]
) -> None:
    surface = import_module(f"instances.{instance}.surface")
    config = surface.default_config(**({"device": device} if device else {}))
    prepared = surface.preparation(config)
    assert isinstance(prepared, Preparation), prepared
    artifact = prepared.specification.source.artifact
    assert artifact.assumption_ledger == (
        "source_ensemble",
        "sequential_round_model",
        "source_replacement_license",
    )
    assert "source_stage_empty" not in prepared.compilation.assumption_ledger
