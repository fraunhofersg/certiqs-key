"""Route (iii): the declared element graph and its compilation.

Definitions ``def:graph`` and ``def:compile``, and Theorem
``thm:compilation-well-defined``.

THE QUESTION THIS ANSWERS is the one that makes route (iii) safe: does the
declared graph DETERMINE the instrument matrix? It does, but not for free, and
the condition it needs is stated rather than assumed.

* (E1) every element's parameter tuple lies in the declared domain of its entry
  type, so that ``Gamma_Sigma`` is defined and is a contraction;
* (E2) the graph is acyclic, so that reachability is a partial order;
* (E3) SUPPORT COMPARABILITY -- any two elements whose supports intersect are
  comparable under reachability.

(E3) is NOT implied by acyclicity and the failure is silent. Remark
``rem:e3``'s own instance: a rotator and a polarizer on the same two modes with
no edge between them. The graph is acyclic and both elements are admissible,
yet the two topological sorts compile to two DIFFERENT contractions -- and,
having the same declared port map, both would pass every other validation in
this contract. Without (E3), the declared receiver does not denote.

COMPOSITION ORDER IS LOAD-BEARING
=================================
The ``composition_order`` convention (``interface.yaml`` ``conventions``): LATER
ELEMENTS MULTIPLY FROM THE LEFT, so element ``e_1`` then ``e_2`` gives
``Gamma = Ghat_{e_2} Ghat_{e_1}`` (Eq. ``eq:compile``). Getting the direction
wrong produces a perfectly valid instrument for a DIFFERENT receiver, which is
why the direction is fixed once and realised in one function.

WHAT IS COMPILED, AND WHAT IS NOT
=================================
:func:`compile_element_graph` returns ``Gamma_G``, the product of the graph's
elements. The COMPILED INSTRUMENT MATRIX of Definition ``def:compile`` is
``Gamma = D_eta Gamma_G`` with the terminal detector layer applied after every
element; ``D_eta`` lives in :mod:`certiqs_key.receiver.efficiency`, because
Theorem ``thm:efficiency`` (iii)'s "one structural site" is what it is about.

REFUSAL IS A RECORD, AND NO ORDERING IS INVENTED TO REPAIR A GRAPH
==================================================================
Requirement ``req:graph-refusal``: a graph failing any of (E1)-(E3) is refused
with the failing condition named, together with THE OFFENDING ELEMENT OR EDGE
for (E1) and THE OFFENDING ELEMENT PAIR for (E3); no matrix is emitted, and no
ordering is invented to repair it. Remark ``rem:noloops`` adds that a receiver
that needs a cycle -- a cavity, a ring resonator, any feedback path -- "is a
new claim, not a bigger computation".
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np

from certiqs_key.receiver.catalogue import Component
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import Matrix, NumericalTolerances, identity
from certiqs_key.receiver.reasons import GRAPH_CONDITION_REASONS, Refusal

__all__ = [
    "Element",
    "ElementGraph",
    "check_element_graph",
    "compile_element_graph",
    "embed",
    "linear_extensions",
    "topological_order",
]


def embed(local: Matrix, support: Sequence[int], mode_count: int) -> Matrix:
    r"""Return the global embedding ``Ghat = Gamma_Sigma (+) id_{M \ Sigma}``.

    The ``embedding`` convention, Eq. ``eq:embed``: the identity on EVERY
    untouched mode. Proposition ``prop:mode-algebra`` (i) is why this preserves
    admissibility, and (iii) is why two embeddings on disjoint supports
    commute.
    """
    global_matrix = identity(mode_count)
    for column_position, column in enumerate(support):
        for row_position, row in enumerate(support):
            global_matrix[row, column] = local[row_position, column_position]
    return global_matrix


@dataclass(frozen=True)
class Element:
    """One vertex of a declared element graph.

    ``support`` lists the modes of ``M`` the element acts on, in the order the
    element's own matrix is written in. Definition ``def:graph``: a vertex
    carries a catalogue entry type, a parameter tuple, and a support.
    """

    name: str
    component: Component
    support: tuple[int, ...]

    def embedded(self, mode_count: int) -> Matrix:
        """Return the element's global embedding on ``C^M``."""
        return embed(self.component.matrix(), self.support, mode_count)


@dataclass(frozen=True)
class ElementGraph:
    """A declared element graph ``G = (V, E)`` -- Definition ``def:graph``.

    An edge ``e -> f`` fixes the ORDER in which ``e`` and ``f`` act, ``e``
    first; moving light from one mode to another is done by the elements'
    matrices and not by the edge (Remark ``rem:edgemeaning``).

    ``edges = ()`` IS AN ABSENCE, NOT A SUBSTITUTED DATUM (the ``fail_closed``
    convention). Definition ``def:graph`` types the graph as a pair ``(V, E)``
    and ``E = {}`` is a value of that type. It cannot change an emitted
    quantity: with no edges every pair of elements is incomparable, so (E3)
    support comparability REFUSES any declaration whose elements share a mode,
    and on every graph that survives Theorem
    ``thm:compilation-well-defined`` (i) makes the compiled matrix independent
    of the order the edges would have imposed. An omitted edge set is therefore
    either refused or immaterial -- unlike a phase or a dark-count probability,
    which is why those carry no default and this may.
    """

    elements: tuple[Element, ...]
    edges: tuple[tuple[str, str], ...] = ()

    @property
    def names(self) -> tuple[str, ...]:
        """Return the element names, in the declared order."""
        return tuple(element.name for element in self.elements)

    def element(self, name: str) -> Element:
        """Return the element with the given name."""
        for candidate in self.elements:
            if candidate.name == name:
                return candidate
        raise HypothesisError(f"no element named {name!r} is declared")

    def successors(self) -> dict[str, set[str]]:
        """Return the direct-successor map of the declared edges."""
        out: dict[str, set[str]] = {name: set() for name in self.names}
        for tail, head in self.edges:
            out.setdefault(tail, set()).add(head)
            out.setdefault(head, set())
        return out

    def reachability(self) -> dict[str, set[str]]:
        """Return the reflexive-transitive closure of the edges.

        The relation ``preceq_G`` of Definition ``def:graph``.
        """
        successors = self.successors()
        closure = {name: {name} for name in successors}
        changed = True
        while changed:
            changed = False
            for name in successors:
                reachable = set(closure[name])
                for target in list(reachable):
                    reachable |= successors.get(target, set())
                if reachable != closure[name]:
                    closure[name] = reachable
                    changed = True
        return closure


def topological_order(graph: ElementGraph) -> tuple[str, ...] | None:
    """Return ONE linear extension, or ``None`` if the graph has a cycle.

    Theorem ``thm:compilation-well-defined`` (iv) decides (E2) BY A TOPOLOGICAL
    SORT, and this is that sort: Kahn's algorithm, linear in the declared
    elements and edges. It is what validation and the compiler both use, and it
    is the whole content of the (E2) test -- a graph admits a topological order
    exactly when it is acyclic.

    ONE SORT IS ENOUGH BECAUSE THE THEOREM SAYS SO. Theorem
    ``thm:compilation-well-defined`` (i) proves that on a well-formed graph EVERY linear
    extension compiles to the same matrix, so the compiler needs one and not all of
    them; :func:`linear_extensions` enumerates every one and exists for the test that
    checks that theorem, not for validating a receiver.

    Ties are broken by element name so that the order is deterministic and a
    refusal names the same element twice.
    """
    predecessors: dict[str, set[str]] = {name: set() for name in graph.names}
    successors: dict[str, list[str]] = {name: [] for name in graph.names}
    for tail, head in graph.edges:
        predecessors.setdefault(head, set()).add(tail)
        predecessors.setdefault(tail, set())
        successors.setdefault(tail, []).append(head)
        successors.setdefault(head, [])
    ready = sorted(name for name, waiting in predecessors.items() if not waiting)
    placed: list[str] = []
    while ready:
        name = ready.pop(0)
        placed.append(name)
        for head in sorted(successors.get(name, ())):
            predecessors[head].discard(name)
            if not predecessors[head]:
                ready.append(head)
                ready.sort()
    if len(placed) != len(graph.names):
        return None
    return tuple(placed)


def linear_extensions(graph: ElementGraph) -> tuple[tuple[str, ...], ...]:
    """Return EVERY linear extension of the graph, by element name.

    An enumeration ``e_1, ..., e_L`` with ``e_i preceq_G e_j`` implying
    ``i <= j`` (Definition ``def:graph``).

    EXHAUSTIVE, AND THEREFORE NOT FOR VALIDATION. The number of linear
    extensions is factorial in the number of pairwise-incomparable elements, so
    a receiver with a dozen parallel arms has more of them than can be
    enumerated. Nothing on the emission path calls this: (E2) and the compile
    order both use :func:`topological_order`, which is the single sort Theorem
    ``thm:compilation-well-defined`` (iv) names. What this function is for is the
    statement of Theorem ``thm:compilation-well-defined`` (i) -- that every one of them
    compiles to the SAME matrix -- which is a test about small declared graphs.
    """
    predecessors: dict[str, set[str]] = {name: set() for name in graph.names}
    for tail, head in graph.edges:
        predecessors.setdefault(head, set()).add(tail)
        predecessors.setdefault(tail, set())

    def walk(
        placed: tuple[str, ...], remaining: frozenset[str]
    ) -> Iterator[tuple[str, ...]]:
        if not remaining:
            yield placed
            return
        for name in sorted(remaining):
            if predecessors[name] - set(placed):
                continue
            yield from walk((*placed, name), remaining - {name})

    return tuple(walk((), frozenset(graph.names)))


def check_element_graph(
    graph: ElementGraph, mode_count: int, tolerances: NumericalTolerances
) -> Refusal | None:
    """Return a refusal naming the first of (E1)-(E3) that fails.

    Theorem ``thm:compilation-well-defined`` (iv): each condition is decidable by finite
    inspection -- (E1) by evaluating the declared domain predicate of each element, (E2)
    by a topological sort, (E3) by testing support intersection against the
    transitive closure for each of the ``|V| choose 2`` pairs. The order of the
    three checks is the order the definition states them in, and each of the
    frozen counterexamples fails exactly one.
    """
    seen: set[str] = set()
    for element in graph.elements:
        if element.name in seen:
            return Refusal(
                GRAPH_CONDITION_REASONS["E1"],
                f"(E1) two elements are declared with the name {element.name!r}",
            )
        seen.add(element.name)
        if any(index < 0 or index >= mode_count for index in element.support):
            return Refusal(
                GRAPH_CONDITION_REASONS["E1"],
                f"(E1) element {element.name!r} has a support outside the "
                f"declared mode space",
            )
        if len(set(element.support)) != len(element.support):
            return Refusal(
                GRAPH_CONDITION_REASONS["E1"],
                f"(E1) element {element.name!r} lists a mode twice in its support",
            )
        if len(element.support) != element.component.support_size():
            return Refusal(
                GRAPH_CONDITION_REASONS["E1"],
                f"(E1) element {element.name!r} declares a support of "
                f"{len(element.support)} modes, but entry "
                f"{element.component.entry_id} acts on "
                f"{element.component.support_size()}",
            )
        refusal = element.component.check_domain(tolerances)
        if refusal is not None:
            return Refusal(
                refusal.reason,
                f"element {element.name!r} (entry "
                f"{element.component.entry_id}): {refusal.detail}",
            )

    for tail, head in graph.edges:
        if tail not in seen or head not in seen:
            return Refusal(
                GRAPH_CONDITION_REASONS["E1"],
                f"(E1) the edge {tail!r} -> {head!r} names an undeclared element",
            )

    if topological_order(graph) is None:
        return Refusal(
            GRAPH_CONDITION_REASONS["E2"],
            "(E2) the declared graph contains a cycle: a topological sort of "
            "it does not terminate, so it admits no linear extension at all. "
            "Remark rem:noloops -- a feedback path is REFUSED, not approximated",
        )

    closure = graph.reachability()
    for i, first in enumerate(graph.elements):
        for second in graph.elements[i + 1 :]:
            if not set(first.support) & set(second.support):
                continue
            comparable = (
                second.name in closure[first.name] or first.name in closure[second.name]
            )
            if not comparable:
                return Refusal(
                    GRAPH_CONDITION_REASONS["E3"],
                    f"(E3) elements {first.name!r} and {second.name!r} have "
                    f"intersecting supports "
                    f"{sorted(set(first.support) & set(second.support))} and are "
                    f"incomparable; two linear extensions of this graph compile "
                    f"to two different instruments and both would pass every "
                    f"other validation (Remark rem:e3)",
                )
    return None


def compile_element_graph(
    graph: ElementGraph, mode_count: int, order: Sequence[str] | None = None
) -> Matrix:
    """Return ``Gamma_G`` of Eq. ``eq:compile`` -- later elements from the LEFT.

    ``order`` selects one linear extension; any of them gives the same matrix
    on a well-formed graph, which is Theorem ``thm:compilation-well-defined`` (i). The
    caller is responsible for having run :func:`check_element_graph` first: compiling an
    ill-formed graph is a hypothesis failure, not a refusal, because the
    quantity has no value rather than a wrong one.
    """
    if order is None:
        sorted_order = topological_order(graph)
        if sorted_order is None:
            raise HypothesisError(
                "the declared graph admits no linear extension; (E2) refuses it"
            )
        order = sorted_order
    matrix = identity(mode_count)
    for name in order:
        matrix = graph.element(name).embedded(mode_count) @ matrix
    return np.asarray(matrix, dtype=np.complex128)
