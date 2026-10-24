"""The contracted objective: pointwise P, T, K, the Choi form and the gradients.

The modules, and the claims they carry:

    linalg      the support cutoff, the matrix powers and the key pinching
                (``foundations/def:pinching``, ``foundations/def:renyi``)
    branch      the generated maps and P, T, tr G, K, the deficits
                (``def:maps``, ``thm:protocol-channel``, ``def:branch``,
                ``lem:branch-maps``,
                ``thm:branch-formula``, ``foundations/lem:pinchmono``, ``cor:f-nonpos``,
                ``def:keyinert``, ``prop:exact-cancellation``, ``def:keyactive``)
    objective   the three-term objective and the feasible set
                (``def:feasible``, ``thm:reduction``, ``cor:reduction-constrained``,
                ``thm:convexity``)
    choi        the exact Choi reformulation (``lem:choi-marginal``,
                ``thm:choi``)
    gradient    the divided-difference gradients and the face rules
                (``lem:dk``, ``thm:gradient``, ``cor:full-gradient``)
    limit       the alpha -> 1+ validation oracle -- A VALIDATION STATEMENT
                AND NOT A BOUND OF ANY KIND (``lem:b-derivative``,
                ``thm:oracle``, ``rem:oracle``)
    support     the support dimensions (H-SUPP) is measured against

The lower-semicontinuous extension ``d(u, v)`` of ``foundations/lem:kernel``
and its two partial derivatives are :mod:`certiqs_key.foundations.kernel`, which
imports nothing of this package; ``linalg`` and ``branch`` stay here because
they read this module's declared thresholds and declaration type.
"""

from __future__ import annotations
