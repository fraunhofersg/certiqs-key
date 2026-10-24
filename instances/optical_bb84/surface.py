"""Optical BB84: the instance surface its protocol document defines.

THE INSTANCE IS ``protocol.yaml`` BESIDE THIS FILE, one optical station, its
receiver the C1-C3 element graph of catalogue components. This module loads it
with the packaged loader
(:func:`instances.declared.load_packaged`, which grants the repository's own
identity strings and bounds the template by its parameter domains rather than
the custom-document work bounds) and exposes the surface every instance exports
(:mod:`certiqs_key.runs.surface`), so ``discover()``, ``readme_path`` and
every ``from instances.optical_bb84.surface import ...`` work unchanged.
``resolve`` returns the parameter values a run of a configuration reads.
``README.md`` describes the protocol and its scope; ``NOTES.md`` lists
the files, the invariants and the tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from instances.declared import load_packaged

__all__ = [
    "DEFAULT_HONEST_MODEL_NOTE",
    "DESCRIPTOR",
    "PARAMETERS",
    "PRESETS",
    "channel_interface",
    "default_config",
    "preparation",
    "receiver_parameters",
    "receiver_requests",
    "resolve",
    "runner",
]

_SURFACE = load_packaged(Path(__file__).with_name("protocol.yaml"))

DESCRIPTOR = _SURFACE.DESCRIPTOR
PARAMETERS = _SURFACE.PARAMETERS
PRESETS = _SURFACE.PRESETS
default_config = _SURFACE.default_config
preparation = _SURFACE.preparation
runner = _SURFACE.runner
resolve = _SURFACE.resolve
#: Optional (not in the uniform surface): the receiver requests a preparation
#: would construct, for the facade's cost estimate
#: (``runs/facade/estimate.py``).
receiver_requests = _SURFACE.receiver_requests
#: The parameters those receivers' photon numbers read (cutoffs, windows).
receiver_parameters: tuple[str, ...] = _SURFACE.receiver_parameters
channel_interface = _SURFACE.channel_interface
#: What the record says about the honest model when the document's own is used.
DEFAULT_HONEST_MODEL_NOTE: dict[str, Any] = _SURFACE.DEFAULT_HONEST_MODEL_NOTE
