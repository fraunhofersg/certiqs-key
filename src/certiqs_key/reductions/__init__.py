"""``reductions``: theorem-backed reductions to a finite proof model.

A MINIMAL GENERIC CORE WITH SUBMODULES THAT EXTEND IT. A submodule declared
removable can in principle be removed without touching the core. What that
means in code:

* THIS PACKAGE states the relation and its calculus, the number model, the
  emission obligation and the chain over an ABSTRACT REDUCTION INSTANCE
  (:mod:`certiqs_key.reductions.instance`). It names no squasher, no branching
  model and no device.
* :mod:`certiqs_key.reductions.wpfss` is one squasher: the flag-state squasher
  with certified weights, with the FLAT instance and ``reduce_flat``.
* a branching model is a submodule of its own, with its own builder, and
  deleting its directory is a deletion.

THE ENTRY POINT IS THE CORE'S :func:`certiqs_key.reductions.emit.reduce`, which
takes a request and an INSTANCE BUILDER -- a Protocol with one method. A run
selects ``wpfss.reduce_flat`` or a branching submodule's entry.

WHAT THE PACKAGE SURFACE DELIBERATELY DOES NOT IMPORT
=====================================================
Importing this package imports NO consumer, NO array library and NO submodule.
Imports point downward only (PRINCIPLES.md section 4) -- an instance may import
runs, runs may import modules, and NO MODULE IMPORTS EITHER -- and this module
owns its input serialization. Concretely: ``numpy`` is absent from the import
graph of everything re-exported here, and so are the submodules, so that the
core can be read and tested without either.

There is one sanctioned exception, and it is a rule about where the exception
may live rather than a general licence: :mod:`certiqs_key.reductions.docking` is
the only file of this package that may name a consumer's declared records, it
converts in ONE direction, it modifies nothing on either side, and it is
deliberately NOT imported from this file -- a caller that wants it imports it by
name.

WHERE THE INTERFACE'S OPEN IMPLEMENTATION CHOICES ARE DECIDED
=============================================================
The interface records the places it is silent on something an implementation
must settle, and decides none of them, "because deciding one in that file would
hide proof-relevant behaviour in a YAML file instead of the source". Each is
decided at ONE site in code, with a docstring saying what was chosen and why:

1. the numeric substrate -- :mod:`certiqs_key.foundations.exact`, the exact
   Gaussian-rational island every module now shares;
2. the null source-mode spelling -- :mod:`certiqs_key.reductions.reasons`;
3. the source-descriptor serialization -- :mod:`certiqs_key.reductions.inputs`
   and the generic branch-register record of
   :mod:`certiqs_key.reductions.artifact`;
4. the squashing-channel constructor record --
   :mod:`certiqs_key.reductions.channels`;
5. the certified-weight record's presence on the licensed route -- the emission
   pass;
6. the link identifier -- :mod:`certiqs_key.reductions.links`;
7. the source of a branching model's flat branch -- that submodule's model,
   where it is DERIVED and not declared;
8. the verification-report encoding --
   :class:`certiqs_key.reductions.artifact.VerificationReport`;
9. the inherited receiver assumption NAMESPACING -- CLOSED AT THIS MOVE, and
   not by namespacing: the collision that made it open was this module's
   A-ROUND sharing the machine key ``round_homogeneity`` with the receiver's
   own, and the two now differ (``A-ROUND-SQ``,
   ``round_homogeneity_squashing``);
10. the ordered field of ``def:substrate`` -- :mod:`certiqs_key.foundations.exact`;
11. the PSD decision algorithm of ``lem:exactpsd`` --
    :mod:`certiqs_key.foundations.exact`;
12. the ``emission_record`` serialization --
    :class:`certiqs_key.reductions.artifact.EmissionRecord`;
13. the designation order of ``def:emitnorm`` -- largest exact trace, then
    the declared order, over the sector support (an element outside the
    sector support is never a host);
14. the rounding tie of every rounding to nearest in ``def:emitnorm`` (2) and
    (3) -- ties to even;
15. ``def:emitnorm`` has no lift probability vector, the uniform
    lift surviving only as the flagged last resort (3), whose mixing family
    ``(q_t / n) 1`` the claim fixes.

Items 13 and 14 are the contract's; 15 needs no deciding function.
"""

from __future__ import annotations

from certiqs_key.reductions.errors import (
    HypothesisError,
    MalformedInputError,
    ReductionsError,
)
from certiqs_key.reductions.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    CERTIFICATE_KINDS,
    CORE_ASSUMPTIONS,
    CORE_FAIL_CLOSED_ROWS,
    CORE_REFUSAL_REASONS,
    LINK_KINDS_DEFERRED,
    LINK_KINDS_IMPLEMENTED,
    LINK_STATUS_EMITTED,
    NEVER_VERIFIED,
    AssumptionId,
    AssumptionRow,
    CertificateKind,
    FailClosedRow,
    FailClosedRule,
    LinkKind,
    LinkStage,
    LinkStatus,
    Refusal,
    RefusalReason,
    Relation,
    Route,
    SourceMode,
)

#: The accepted contract version this package implements: a ``version`` of
#: spec/modules/reductions/module.yaml, this repository's single source of
#: truth for a module's version, moved here at accept-implementation. A
#: submodule (wpfss, or any other) pins no version of its own; the artifact names
#: this one. The frozen expectations that spell the emitted string are edited
#: BY HAND when it moves, never regenerated from the code.
CONTRACT_VERSION = "0.21.0"

#: The emitted ``mathematical_spec_version``. THE VALUE IS DERIVED FROM
#: :data:`CONTRACT_VERSION` and is not a second literal, so the two cannot
#: drift; the emitted default of
#: :class:`certiqs_key.reductions.artifact.ProofReductionArtifact` is the same
#: string and a golden test asserts the equality. The module id is this
#: repository's (`reductions`).
MATHEMATICAL_SPEC_VERSION = f"reductions@{CONTRACT_VERSION}"

#: The spec/notation.md version this module is written against:
#: spec/modules/reductions/module.yaml's ``notation_version``.
SYMBOLS_VERSION = "0.4.0"

__all__ = [
    "ASSUMPTION_MACHINE_KEYS",
    "CERTIFICATE_KINDS",
    "CONTRACT_VERSION",
    "CORE_ASSUMPTIONS",
    "CORE_FAIL_CLOSED_ROWS",
    "CORE_REFUSAL_REASONS",
    "LINK_KINDS_DEFERRED",
    "LINK_KINDS_IMPLEMENTED",
    "LINK_STATUS_EMITTED",
    "MATHEMATICAL_SPEC_VERSION",
    "NEVER_VERIFIED",
    "SYMBOLS_VERSION",
    "AssumptionId",
    "AssumptionRow",
    "CertificateKind",
    "FailClosedRow",
    "FailClosedRule",
    "HypothesisError",
    "LinkKind",
    "LinkStage",
    "LinkStatus",
    "MalformedInputError",
    "ReductionsError",
    "Refusal",
    "RefusalReason",
    "Relation",
    "Route",
    "SourceMode",
]
