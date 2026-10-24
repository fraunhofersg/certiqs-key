"""Frank-Wolfe search and key assembly, loaded without import-order cycles.

Generic preparation, assessment and request modules import the small FW
components. Importing this package must not eagerly import the high-level
assembly that itself depends on those generic modules. The existing public
exports are therefore resolved when requested.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from certiqs_key.solvers.frank_wolfe.driver import (
        ACCUMULATION_RULE,
        FrankWolfeOptions,
    )
    from certiqs_key.solvers.frank_wolfe.general_keyrate import (
        GeneralKeyRateResult,
        key_length_from_first_order,
    )
    from certiqs_key.solvers.frank_wolfe.joint_driver import (
        IterateObserver,
        JointFrankWolfeResult,
        run_joint_frank_wolfe,
    )
    from certiqs_key.solvers.frank_wolfe.keyrate import (
        NegativeObjectiveError,
        solve,
        solve_bundle,
        solve_declaration,
    )


__all__ = [
    "ACCUMULATION_RULE",
    "FrankWolfeOptions",
    "GeneralKeyRateResult",
    "IterateObserver",
    "JointFrankWolfeResult",
    "NegativeObjectiveError",
    "key_length_from_first_order",
    "run_joint_frank_wolfe",
    "solve",
    "solve_bundle",
    "solve_declaration",
]


_EXPORT_MODULES = {
    "ACCUMULATION_RULE": "driver",
    "FrankWolfeOptions": "driver",
    "GeneralKeyRateResult": "general_keyrate",
    "key_length_from_first_order": "general_keyrate",
    "IterateObserver": "joint_driver",
    "JointFrankWolfeResult": "joint_driver",
    "run_joint_frank_wolfe": "joint_driver",
    "NegativeObjectiveError": "keyrate",
    "solve": "keyrate",
    "solve_bundle": "keyrate",
    "solve_declaration": "keyrate",
}


def __getattr__(name: str) -> Any:
    """Resolve existing exports lazily so low-level imports stay acyclic."""
    if name not in _EXPORT_MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"{__name__}.{_EXPORT_MODULES[name]}"), name)
    globals()[name] = value
    return value
