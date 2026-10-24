"""``meat-core``: the protocol-agnostic key-rate engine.

The mathematics between a protocol declaration and a key length: the
single-round objective that is optimised, the sector structure that makes it
optimisable, the numerical (Choi) formulation with its gradients, and the
assembly of the optimised value into a fixed-length key. Everything downstream
of the declaration is DERIVED from it (``def:declaration``, ``def:maps``,
``thm:protocol-channel``): no protocol, no squasher and no receiver model is hard-coded
anywhere, and a specific protocol enters as an INSTANCE of the declaration,
supplied by :mod:`certiqs_key.protocol_compiler`.

The contract is the claim files under ``spec/modules/meat-core/``, with
``interface.yaml`` beside them; the readable form is assembled from them.

THE PACKAGE SPLIT
=================

``declaration``
    the declaration as data, the input validation this module runs
    (spec/architecture.md 3.6), the exact admission of ``def:declaration``, the
    operator bundle read into a declaration, and the sector classification.
``objective``
    the pointwise quantities, the Choi form and the gradients.
``finitekey``
    the fixed-length assembly and the result record.
``acceptance``
    the declared acceptance set, its two geometries, and exact linear
    minimisation over them.
``thresholds``
    the interface's declared threshold rows, as data.
``reasons``
    the machine vocabulary: refusal strings, withdrawal reasons, and the
    assumption ledger this module emits.
``provenance``
    the run tier's in-memory token that a declaration is the protocol
    compiler's emission, without which no key length is reported
    (``req:compiled-declaration-only``).
``docking_statistics``
    the statistics module's acceptance construction read into this module's
    type. The consumer reads the supplier.
``docking``
    the compiler's emitted declaration read into this module's type. NOT ON THE
    PACKAGE SURFACE, and its own docstring says why.

THE SOLVER IS A SUBMODULE AND IS A DIFFERENT PACKAGE
====================================================
:mod:`certiqs_key.solvers` -- the Frank-Wolfe driver, the linear oracles and
the capability probe -- is the code of the ``frank-wolfe`` submodule (the core
is program plus formulation). IT IS REMOVABLE, as a submodule declared removable is:
deleting the package and the submodule's claim directory leaves the core green.
What would remain is a module that states the program, solves nothing and
reports the estimate at a point somebody else supplies; ``lem:estimate`` and
``cor:keylength-bound`` are the two claims that make that a coherent contract
rather than a gap, and a SECOND solver submodule docks at exactly those two
with its own bound and its own trust root.

THIS MODULE TAKES NO TOLERANCE
==============================
Declared data arrives EXACTLY ADMISSIBLE or the run is refused
(``def:declaration``, the exact-admissibility paragraph), which is the decision
the compiler has already taken on the numbers it emits
(``protocol-compiler/def:exact``, mentioned and not used) and which
spec/architecture.md 2.8 states as the platform rule. There is no declared
numerical tolerance, no admitted-with-defect branch and no
``tolerance_report``; what is kept is the REASON, ``prop:optol-nobound`` with
``rem:optol-direction``, which is why no tolerance could have licensed a
key-length claim.

THREE RUNGS, ACHIEVED AND NEVER REQUESTED
=========================================
Every run reports the objective at the point the optimiser returned -- a
diagnostic, never a bound -- and, where the hypotheses held, the first-order
lower bound; where the certified evaluation forms that bound again with every
arithmetic step exact or rigorously enclosed
(``frank-wolfe/req:certified-evaluation``), the certified number beside it.
``reported_tier`` names which carries the claim. THE TIER IS ACHIEVED AND NEVER
REQUESTED. The certified tier is a narrow a-posteriori verification of the
first-order bound at a run's final points (PRINCIPLES.md section 10): no
interval-arithmetic library is a premise, its correctness being the code's.
"""

from __future__ import annotations

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.errors import (
    DeclarationError,
    GradientHypothesisError,
    HypothesisError,
    MeatError,
    SectorOperationError,
    SecurityGateError,
    SecurityStatementVacuousError,
    SupportError,
    UnsupportedDeclarationError,
)
from certiqs_key.meat_core.provenance import CompilerEmission

__all__ = [
    "Assurance",
    "CompilerEmission",
    "DeclarationError",
    "GradientHypothesisError",
    "HypothesisError",
    "MeatError",
    "SectorOperationError",
    "SecurityGateError",
    "SecurityStatementVacuousError",
    "SupportError",
    "UnsupportedDeclarationError",
]
