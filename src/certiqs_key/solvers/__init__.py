"""``meat-core/frank-wolfe``: the solver submodule's code.

THE SUBMODULE'S CODE AND NOT THE CORE'S (core = program + formulation;
submodule frank-wolfe). The core states the
program and the formulation; this package states the Frank-Wolfe linearisation
bound, its feasible side verified from the oracle's dual
(``frank-wolfe/req:verified-feasible-side``), the relaxed iterate set and the
acceptance-side exact minimisation.

    capabilities  the probe and the fail-closed gate (spec/architecture.md 7.3)
    oracles       the physics-blind ``LinearOracle`` protocol and its backends
    frank_wolfe   the support-aware driver and the end-to-end assembly

IT IS REMOVABLE, as a submodule declared removable is: deleting this package
and the submodule's claim directory leaves the core green. The whole of the
coupling is two core claims -- ``lem:estimate``, the warrant of the estimate
every run reports, and ``cor:keylength-bound``, the key length from ANY lower
bound -- and a second solver submodule docks at exactly those two with a
different bound and a different trust root.

It imports :mod:`certiqs_key.meat_core` and the core imports nothing from here:
imports point downward only (PRINCIPLES.md section 4).

NOTHING HERE CAN RAISE THE REPORTED TIER: solver status and duality gap are
diagnostics, never evidence (spec/architecture.md 2.5).
"""

from __future__ import annotations
