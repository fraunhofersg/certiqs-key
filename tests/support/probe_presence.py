"""Whether the removable probe-conditioning submodule is in this tree.

The receiver's probe-conditioning submodule is a removable leaf, and the
public tree is exported without it, the passive receiver's probe source
(``instances/common/led.py``) and the protocol document's ``probe`` field
going with it (``harness/export_manifest.yaml``, group
``probe-conditioning``). A test file that checks the core receiver and also a
receiver with source modes survives that cut: its probe cases carry
:data:`requires_probe` and import the probe source inside the test, so that they skip
where the submodule is absent and the rest of the file runs.
``tests/harness/test_removability.py`` cuts the group from a copy of the tree
and checks that every remaining test still collects.
"""

from __future__ import annotations

import importlib.util

import pytest

from certiqs_key.receiver.settings import conditioning_present

__all__ = ["PROBE_PRESENT", "requires_probe", "with_probe"]

#: The submodule's code and the passive receiver's probe source, both present.
PROBE_PRESENT: bool = (
    conditioning_present()
    and importlib.util.find_spec("instances.common.led") is not None
)

#: Skip a test of a receiver with source modes where the submodule is absent.
requires_probe = pytest.mark.skipif(
    not PROBE_PRESENT,
    reason="the probe-conditioning submodule is not in this tree",
)


def with_probe[T](*items: T) -> tuple[T, ...]:
    """Return ``items`` where the submodule is present, and nothing where not.

    For a test that loops over a probe-free and a probe receiver: the
    probe-free half runs in every tree.
    """
    return items if PROBE_PRESENT else ()
