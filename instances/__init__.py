"""Protocol instances: one package per concrete protocol the platform can run.

spec/architecture.md 3.3 and PRINCIPLES.md section 4. An instance is DATA plus the one
model that goes with it -- a specification the compiler can consume, and the honest
channel model behind ``statistics``'s interface. It is ordinary, non-proof-critical
code: no contract, no gate.

WHY THIS IS A SEPARATE TIER FROM ``runs``
=========================================
Because they answer different questions. An instance answers *which protocol*;
:mod:`certiqs_key.runs` answers *how a run is driven*. Kept apart, the instance
package keeps its name clear of :mod:`certiqs_key.protocol_compiler` -- the
proof-critical, accepted compiler, of an entirely different gate status -- and a
second protocol calls the driver rather than copying it.

WHAT AN INSTANCE OWNS, AND THE ONE REQUIREMENT THAT TRAVELS WITH IT
===================================================================
The honest channel model is an instance's to own: spec/architecture.md 4.3 calls
the provider of ``p_honest`` "not proof-critical" and spec/architecture.md 3.4 says such
a simulator "needs no contract and no gate". One requirement is not optional -- a
provider emits TOTAL CHANNEL USES and JOINT PER-OUTCOME probabilities on the declared
acceptance alphabet, never a sifted QBER, because Assumption A-TSM binds the
``output_state`` test-statistics model.

Nothing else may be owned here. A number an instance invented -- an acceptance
set it widened, a QBER it read off, a default it substituted for a missing
argument -- would be proof-relevant behaviour living outside every gate, which is
precisely what the tier split exists to prevent.

Every package under here is a LEAF: nothing in ``src/certiqs_key/`` outside an
instance imports one.

DISCOVERY LIVES HERE AND NOT IN ``runs/``
==========================================
A consumer enumerates the instances without naming one, and the list is HERE
because ``runs/`` may not import ``instances/``: imports point downward only
(PRINCIPLES.md section 4), and a discovery function in the run tier that
imported these packages would be the one upward edge the layout exists to
prevent. The TYPES every instance exports are ``runs/``'s
(:mod:`certiqs_key.runs.surface`); the LIST of who exports them is this
package's.

``tests/unit/test_instance_surface.py`` asserts that every listed package
exports the full surface, so a package added to the list below without one is
a failure rather than a silent half-instance.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Final

__all__ = ["INSTANCE_PACKAGES", "discover", "surface_of"]

#: The instance packages this repository carries, in no significant order.
INSTANCE_PACKAGES: Final[tuple[str, ...]] = (
    "bb84", "optical_bb84", "decoy_bb84", "bbm92",
)


def surface_of(name: str) -> ModuleType:
    """Return one instance's ``surface`` module by package name."""
    return import_module(f"instances.{name}.surface")


def discover() -> tuple[ModuleType, ...]:
    """Return the ``surface`` module of every instance, in the listed order.

    A caller enumerates instances with this and drives each one through the
    names of the uniform surface -- ``DESCRIPTOR``, ``PARAMETERS``, ``PRESETS``,
    ``default_config``, ``preparation`` and ``runner`` -- without naming any of
    them. ``preparation`` is the sixth: it is the
    oracle-free preparation with THIS instance's wiring, which a consumer
    cannot assemble from the other five.
    """
    return tuple(surface_of(name) for name in INSTANCE_PACKAGES)
