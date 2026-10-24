"""Compilation of a declared element graph (registry RC2), against the registry.

Golden replay of ``COMPILE_CASES`` (oracle entry ``O-RP-COMPILE``). What the
SET of six graphs pins, and what each test here checks:

* the three well-formedness conditions are INDEPENDENT -- each violation case
  fails exactly one of (E1), (E2), (E3);
* the refusal names the contract's own identifier for the failing condition,
  never an invented spelling, and names the offending element pair for (E3);
* independence of the linear extension is an EQUALITY BETWEEN TWO PRODUCTS,
  and G-PARALLEL freezes both orders with one compiled matrix;
* COMPOSITION ORDER IS LOAD-BEARING and G-ORDERED is where it bites: the two
  products differ, the graph's EDGE selects one, and BOTH are contractions --
  so a wrong direction would produce a valid instrument for another receiver;
* isometry iff lossless, in both directions.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, assert_matches, mat_value
from registry_receiver_povm import COMPILE_CASES, rp_oracle

from certiqs_key.receiver import (
    Element,
    ElementGraph,
    Loss,
    PhaseShifter,
    Polarizer,
    Retarder,
    Rotator,
    check_element_graph,
    compile_element_graph,
    linear_extensions,
)
from certiqs_key.receiver.numerics import PiMultiple
from certiqs_key.receiver.reasons import GRAPH_CONDITION_REASONS

_MODE_COUNT = 2
_ANGLE_3_4_5 = math.atan2(0.8, 0.6)


def _graph(case_id: str) -> ElementGraph:
    """Return the declared graph of a frozen compile case."""
    rotator = Rotator(_ANGLE_3_4_5)
    polarizer = Polarizer(0, 1, 0)
    phase = PhaseShifter((math.pi,))
    loss = Loss((F(1, 4),))
    graphs: dict[str, ElementGraph] = {
        "G-PARALLEL": ElementGraph(
            (
                Element("e_a", phase, (0,)),
                Element("e_b", loss, (1,)),
            )
        ),
        "G-LOSSLESS": ElementGraph((Element("e_a", phase, (0,)),)),
        "G-ORDERED": ElementGraph(
            (
                Element("e_1", rotator, (0, 1)),
                Element("e_2", polarizer, (0, 1)),
            ),
            (("e_1", "e_2"),),
        ),
        "G-E3-VIOLATION": ElementGraph(
            (
                Element("e", rotator, (0, 1)),
                Element("f", polarizer, (0, 1)),
            )
        ),
        "G-E2-VIOLATION": ElementGraph(
            (
                Element("e", phase, (0,)),
                Element("f", loss, (1,)),
            ),
            (("e", "f"), ("f", "e")),
        ),
        # The registry declares delta = 2 pi EXACTLY, the excluded endpoint: it
        # is written as the coefficient 2 of pi. The double math.tau is a
        # dyadic rational below 2 pi, inside the half-open domain, and would
        # not be this case's datum.
        "G-E1-VIOLATION": ElementGraph(
            (Element("e", Retarder(PiMultiple(F(2)), 0, 0), (0, 1)),)
        ),
    }
    return graphs[case_id]


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_graph_compiles_or_is_refused_as_frozen() -> None:
    """Definition def:compile and Theorem thm:compilation-well-defined (i), (ii), (iv)."""  # noqa: E501
    assert rp_oracle("O-RP-COMPILE").claims == ("RC2",)
    for case in COMPILE_CASES:
        graph = _graph(case.case_id)
        refusal = check_element_graph(graph, _MODE_COUNT, TOLERANCE)
        if case.refused_condition is None:
            assert refusal is None, (case.case_id, refusal)
            compiled = compile_element_graph(graph, _MODE_COUNT)
            assert case.compiled is not None
            assert_matches(
                compiled, mat_value(case.compiled), TOLERANCE.eps_1, case.case_id
            )
            # Theorem thm:compilation-well-defined (ii): a contraction BY CONSTRUCTION.
            defect = compiled.conj().T @ compiled - np.eye(_MODE_COUNT)
            assert float(np.max(np.linalg.eigvalsh(defect).real)) <= TOLERANCE.eps_1
        else:
            assert refusal is not None, case.case_id
            assert refusal.reason is GRAPH_CONDITION_REASONS[case.refused_condition], (
                case.case_id
            )
            assert case.compiled is None


@pytest.mark.contract
@pytest.mark.oracle
def test_the_linear_extensions_are_the_frozen_ones() -> None:
    """Definition def:graph; the empty tuple IS the (E2) refusal's content."""
    for case in COMPILE_CASES:
        graph = _graph(case.case_id)
        assert linear_extensions(graph) == case.linear_extensions, case.case_id


@pytest.mark.contract
def test_independence_of_the_sort_and_the_layered_form() -> None:
    """Theorem thm:compilation-well-defined (i) on G-PARALLEL: both orders, one matrix."""  # noqa: E501
    graph = _graph("G-PARALLEL")
    extensions = linear_extensions(graph)
    assert len(extensions) == 2
    first = compile_element_graph(graph, _MODE_COUNT, extensions[0])
    second = compile_element_graph(graph, _MODE_COUNT, extensions[1])
    assert_matches(first, second, TOLERANCE.eps_1, "sort independence")


@pytest.mark.contract
def test_composition_order_is_load_bearing() -> None:
    """The `composition_order` convention, on G-ORDERED: the products DIFFER."""
    graph = _graph("G-ORDERED")
    declared = compile_element_graph(graph, _MODE_COUNT, ("e_1", "e_2"))
    reversed_order = compile_element_graph(graph, _MODE_COUNT, ("e_2", "e_1"))
    assert np.max(np.abs(declared - reversed_order)) > 0.5
    # Both are contractions, which is why the error would be silent.
    for matrix in (declared, reversed_order):
        defect = matrix.conj().T @ matrix - np.eye(_MODE_COUNT)
        assert float(np.max(np.linalg.eigvalsh(defect).real)) <= TOLERANCE.eps_1
    # And the DECLARED one is the frozen matrix.
    case = next(c for c in COMPILE_CASES if c.case_id == "G-ORDERED")
    assert case.compiled is not None
    assert_matches(declared, mat_value(case.compiled), TOLERANCE.eps_1, "G-ORDERED")


@pytest.mark.contract
@pytest.mark.oracle
def test_isometry_iff_lossless_in_both_directions() -> None:
    """Theorem thm:compilation-well-defined (iii), on the frozen pair that exercises both sides."""  # noqa: E501
    for case_id in ("G-LOSSLESS", "G-PARALLEL", "G-ORDERED"):
        case = next(c for c in COMPILE_CASES if c.case_id == case_id)
        graph = _graph(case_id)
        compiled = compile_element_graph(graph, _MODE_COUNT)
        unitary = bool(
            np.max(np.abs(compiled.conj().T @ compiled - np.eye(_MODE_COUNT)))
            <= TOLERANCE.eps_1
        )
        every_element_lossless = all(
            element.component.is_lossless() for element in graph.elements
        )
        assert unitary is every_element_lossless, case_id
        assert unitary is case.lossless, case_id


@pytest.mark.contract
def test_the_three_conditions_are_independent() -> None:
    """No two of (E1), (E2), (E3) can be conflated by these six graphs."""
    # G-E1-VIOLATION fails only (E1): acyclic, and one element cannot violate
    # support comparability.
    graph = _graph("G-E1-VIOLATION")
    assert linear_extensions(graph) == (("e",),)
    assert graph.elements[0].component.check_domain(TOLERANCE) is not None

    # G-E2-VIOLATION fails only (E2): its elements are G-PARALLEL's, admissible
    # and disjointly supported.
    graph = _graph("G-E2-VIOLATION")
    assert linear_extensions(graph) == ()
    for element in graph.elements:
        assert element.component.check_domain(TOLERANCE) is None
    supports = [set(element.support) for element in graph.elements]
    assert not supports[0] & supports[1]

    # G-E3-VIOLATION fails only (E3): acyclic, both elements admissible, and
    # the two sorts compile to two DIFFERENT contractions.
    graph = _graph("G-E3-VIOLATION")
    assert len(linear_extensions(graph)) == 2
    for element in graph.elements:
        assert element.component.check_domain(TOLERANCE) is None
    first = compile_element_graph(graph, _MODE_COUNT, ("e", "f"))
    second = compile_element_graph(graph, _MODE_COUNT, ("f", "e"))
    assert np.max(np.abs(first - second)) > 0.5
    refusal = check_element_graph(graph, _MODE_COUNT, TOLERANCE)
    assert refusal is not None
    assert refusal.reason is GRAPH_CONDITION_REASONS["E3"]
    # Requirement req:graph-refusal requires the OFFENDING ELEMENT PAIR to be
    # named.
    assert "'e'" in refusal.detail and "'f'" in refusal.detail


@pytest.mark.contract
def test_a_cycle_is_refused_and_never_resolved() -> None:
    """Definition def:graph (E2), Requirement req:graph-refusal, Remark rem:noloops."""
    graph = _graph("G-E2-VIOLATION")
    refusal = check_element_graph(graph, _MODE_COUNT, TOLERANCE)
    assert refusal is not None
    assert refusal.reason is GRAPH_CONDITION_REASONS["E2"]
    # No matrix is emitted and no ordering is invented to repair it.
    with pytest.raises(Exception, match="no linear extension"):
        compile_element_graph(graph, _MODE_COUNT)
