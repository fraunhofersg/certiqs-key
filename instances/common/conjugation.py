"""The conjugation of a declared state: the one place the bar is applied.

A protocol document's ``conjugate_states``
applies the ``conjugation_basis`` convention through this function, as the
qubit instance's specification and the shared BB84 source part do; the
instance tier keeps one copy of it, and ``instances.bb84.specification``
re-exports it, so the compiler's worked declaration and the golden tests can
import it from there.

The convention and its reasons are the qubit instance's
(``instances/bb84/specification.py``, "WHERE THE CONJUGATION HAPPENS").
"""

from __future__ import annotations

from certiqs_key.foundations.exact import Matrix

__all__ = ["conjugate_projector"]


def conjugate_projector(projector: Matrix) -> Matrix:
    """Return ``|conj(psi)><conj(psi)|`` for ``projector = |psi><psi|``.

    THE ENTRYWISE COMPLEX CONJUGATE, taken in the DECLARED COMPUTATIONAL BASIS
    OF ``A`` -- the ``conjugation_basis`` convention: "This is the ONE PLACE
    where a transposed index would be SILENT, so the basis is NAMED RATHER THAN
    ASSUMED."

    For a rank-one projector the entrywise conjugate coincides with the
    transpose, the form transmitter Lemma ``lem:ensemble-presentation`` states
    (``N_x = (sigma_x)^T``): transposition in the declared basis conjugates the
    entries of a rank-one projector, and conjugating twice returns the
    original. The entrywise form
    is written here because it is the one that says what it means for the
    VECTOR, and because ``P^T`` and ``conj(P)`` agree only for a Hermitian ``P``
    and would silently diverge if this were ever applied to something else.
    """
    return tuple(tuple(entry.conjugate() for entry in row) for row in projector)
