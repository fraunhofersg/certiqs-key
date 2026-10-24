"""``foundations``: the code of the ``foundations`` module, and the floor.

Imports point downward only (PRINCIPLES.md section 4), and this package is the
floor: every other package of :mod:`certiqs_key` may import it, and it imports
the standard library, NumPy and itself, nothing else of this repository. The
claims it implements are those of ``spec/modules/foundations`` (the number
model, exact admissibility, the sector map, the snap, the tiers and the
divergence kernel); what each file carries is named by the ``implements``
field of the claim it serves.

``errors``
    the two hard errors -- a malformed argument, a violated hypothesis -- that
    every module raises and that no module may confuse with a refusal. They
    live beside ``exact``, which raises both.
``exact``
    the exact Gaussian-rational substrate: ``Cx``, ``Matrix``, the algebra, the
    exact predicates, the declared dyadic lattice, the binary64 membership test
    (``foundations/def:binary64``) and the one accumulation that decides the
    rounds-nowhere condition (``foundations/def:declared-order``), together with
    the two partial traces, the two projectors and the exact inverse the
    compiler and the transmitter read.
``dyadic``
    exact dyadic matrices on Python integers and the rigorous least-eigenvalue
    bound of ``foundations/lem:least-eigenvalue-bound``: a certification on the
    exact island of numbers a solver computed in binary64
    (``foundations/def:exact-island`` (iii)).
``exact_admission``
    the exact DECISION kernel -- Hermiticity, positivity, completeness and the
    declared-order sum, decided on declared binary64 arrays and never measured
    against a window (``foundations/def:exact-admissibility``).
``blocks``
    the sector-block operator form: the block kind, the sector map
    (``foundations/def:sector-map``), the factorised sector map, the block
    operator and the joint block list on ``A Q``.
``numeric``
    the measuring kernel: one implementation of each operator predicate's
    DEFECT, each returning a number, which the declared tolerance is compared
    against (``foundations/def:tolerance``). No function in it takes a
    tolerance, returns a bool, or mutates its input.
``snap``
    the snapping table (``foundations/def:snap``): the ONE licensed repair of
    declared data, called only by an instance on what it declares, never on
    data a module was handed. It produces exact admissibility or refuses, and
    records every step with its pre-snap defect and its displacement. A
    measurement family is snapped by ``snap_measurement_family``: kept where
    it is known exactly on the lattice, moved by one support-safe procedure
    elsewhere, and disclosed where it rests on A-SNAP
    (``foundations/req:snap-reference``).
``resting``
    why a moved block rests on A-SNAP: the four groups of
    ``foundations/req:snap-reference`` (iii), their causes and fixes, which
    the snap, the receiver's fixes and the run's decision all name.
``reference``
    a reference of a measurement family, exact or known through entrywise
    enclosures (``foundations/def:exact-reference``), the decisions a
    declarer takes on it, and the enclosure decision of
    ``lem:enclosure-psd``. ``snap`` imports it.
``recentring``
    the entrywise enclosure as NumPy-free data and its recentring at zero
    (``foundations/lem:recentred-enclosure``), which the reference companion
    of the direct route reads (``reductions/req:reference-companion``).
``rungs``
    the ONE copy of the lattice-exponent check, the weight ladder and the
    round-down candidate list, NumPy-free, which the ``reductions`` emission
    normaliser imports (spec/architecture.md 2.9).
``assurance``
    the platform's one tier vocabulary (``foundations/def:tiers``).
``kernel``
    the extended divergence kernel ``d(u, v)`` (``foundations/def:kl``,
    ``foundations/lem:kernel``) and its two partial derivatives.

WHAT STAYS ELSEWHERE. ``foundations/def:pinching``, ``def:renyi`` and
``lem:pinchmono`` are implemented in :mod:`certiqs_key.meat_core.objective`
(``linalg``, ``branch``): that code reads ``meat-core``'s declared thresholds and
declaration type, so moving it here would make this package import a module.
The general declaration format (``domain.families``) and the reduction-chain
records (``domain.chain``, ``domain.constraints``) stay in
:mod:`certiqs_key.domain`, which imports this package.

The names are deliberately NOT re-exported from this namespace: a caller names
the module it reaches into, so that the import line says what it is doing.
"""

from __future__ import annotations

__all__: list[str] = []
