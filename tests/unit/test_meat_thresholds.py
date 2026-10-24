"""The declared-threshold table of contract Section 2.6, against the contract.

Section 2.6 states an inventory and a carrying rule, and both are checkable, so
both are checked here rather than described in a docstring: exactly one row at
``tau_num``, every numbered row positive, and "EVERY ROW ... CARRIED BY EXACTLY
ONE, AND NO ROW ... BY TWO".

TWO INVENTORIES, AND THE DIFFERENCE BETWEEN THEM IS THE CONTRACT'S OWN.
Section 2.6 lists SEVENTEEN live rows in two groups plus Group C rows, and
:data:`~certiqs_key.meat_core.thresholds.CONTRACT_LIVE` is that list. But one Group C
row is retired CONDITIONALLY -- ``limit_membership`` "goes with the code it
guards: an implementation that does not run the oracle carries neither, and ONE
THAT DOES DECLARES IT AS A GROUP B NUMBER" -- and this implementation runs the
alpha -> 1+ oracle in ``certiqs_key.meat_core.objective.limit``. So
:data:`~certiqs_key.meat_core.thresholds.LIVE` is EIGHTEEN, ``RETIRED`` is three, and
the eighteenth row is that one. Both inventories are asserted below, because a
table that matched the contract's counts while running the oracle at an
undeclared constant would be the defect this file exists to catch.

WHY A TEST AND NOT A COMMENT. The failure this guards against is
``iterate_positivity`` deciding TWO predicates -- a
spectral floor and an entrywise residual -- at ONE declared value, and "the two
need opposite windows and cannot share one". That is invisible to every
arithmetic test and visible to a carrying table.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.thresholds import ThresholdGroup, ThresholdKind


@pytest.mark.contract
def test_the_inventory_is_the_contract_s() -> None:
    """SEVENTEEN live rows in two groups, and SIX retired ones.

    THE ARITHMETIC, stated rather than left to a reader: seventeen live rows,
    seven in Group A and ten in Group B. ``constraint_operator_exact`` is the
    interface's own and not a claim's: Hermiticity of a constraint operator is
    a predicate on the declared numbers. A WINDOW IS NOT A ROW:
    ``bob_povm_admission`` is decided at exactly zero. ``branch_support_dim``
    is not carried: its predicate is decided on every run at a window DERIVED
    from ``support_cutoff`` (``frank-wolfe/rem:fo-one-ruler``). Group C is
    six.
    """
    assert len(thresholds.CONTRACT_LIVE) == 17
    assert len(thresholds.GROUP_A) == 7
    # The interface's Group B is ten; the eleventh is ``limit_membership``,
    # asserted separately below so the two inventories cannot be confused.
    assert len(thresholds.GROUP_B) - 1 == 10
    group_c = dict(thresholds.RETIRED) | dict(thresholds.RETIRED_UNLESS_CARRIED)
    assert set(group_c) == {
        "limit_membership",
        "the tolerance window on bob_povm_admission",
        "certificate_series",
        "homogeneity",
        "marginal_support_floor",
        "branch_support_dim",
    }
    # Every retired row is disposed of on a STATED GROUND, because the interface
    # disposes of each on one rather than on evidence, there being none.
    for key, ground in group_c.items():
        assert len(ground) > 150, key
    # The machine keys are BINDING and are all distinct.
    keys = [row.key for row in thresholds.LIVE]
    assert len(set(keys)) == len(keys)
    # No live row is also an UNCONDITIONALLY retired one.
    assert set(keys) & set(thresholds.RETIRED) == set()


@pytest.mark.contract
def test_this_implementation_carries_the_conditionally_retired_row() -> None:
    """``limit_membership`` is live HERE, because this implementation runs it.

    Section 2.6's Group C disposition is conditional in terms: the row "goes
    with the code it guards -- an implementation that does not run the oracle
    carries neither, and ONE THAT DOES DECLARES IT AS A GROUP B NUMBER, the
    object it decides being one the module computed".
    ``certiqs_key.meat_core.objective.limit`` is the alpha -> 1+ validation oracle of
    Remark ``rem:oracle``, it is in ``src/``, and it decides (H2) on
    ``Phi[omega]`` -- an object this module computed, which is the Group B
    criterion. So the row is declared, carried and reported here.

    THE FAILURE THIS CATCHES: the row named in
    ``RETIRED`` while the oracle runs at a bare ``1e-9`` in ``limit.py``, so
    ``carrying_table()`` did not cover it -- an undeclared window deciding a
    predicate Section 2.6 names.
    """
    from certiqs_key.meat_core.objective import limit

    assert "limit_membership" not in thresholds.RETIRED
    assert set(thresholds.RETIRED_UNLESS_CARRIED) == {"limit_membership"}
    assert len(thresholds.LIVE) == len(thresholds.CONTRACT_LIVE) + 1
    added = {row.key for row in thresholds.LIVE} - {
        row.key for row in thresholds.CONTRACT_LIVE
    }
    assert added == {"limit_membership"}

    row = thresholds.LIMIT_MEMBERSHIP
    assert row.group is ThresholdGroup.B
    assert row.carried_by == (
        "certiqs_key.meat_core.objective.limit.ACCEPTANCE_TOLERANCE"
    )
    # The constant IS the declared number, read from here and not written there.
    assert thresholds.declared(row) == limit.ACCEPTANCE_TOLERANCE
    assert thresholds.carrying_table()["limit_membership"] == row.carried_by


@pytest.mark.contract
def test_no_row_is_at_a_declared_tolerance_and_every_group_a_row_is_exact() -> None:
    """NO ROW IS AT ``tau_num``, ``bob_povm_admission`` INCLUDED.

    A row decided at the run's declared tolerance would have a ``value`` of
    ``None``, because the number would be the run's and not the module's.
    ``bob_povm_admission`` is decided at exactly zero like every other Group A
    row.

    WHAT THIS ASSERTS: no row anywhere in the table
    defers its number to a run, EVERY Group A row reads exactly zero, and the
    retired window is named in the disposition list rather than merely absent.
    """
    assert [row.key for row in thresholds.LIVE if row.value is None] == []
    assert {row.value for row in thresholds.GROUP_A} == {0.0}
    assert all(row.kind is ThresholdKind.EXACT for row in thresholds.GROUP_A)
    assert thresholds.BOB_POVM_ADMISSION.group is ThresholdGroup.A
    assert thresholds.declared(thresholds.BOB_POVM_ADMISSION) == 0.0
    assert "the tolerance window on bob_povm_admission" in thresholds.RETIRED


@pytest.mark.contract
def test_the_group_b_rows_carry_a_number_and_two_are_exactly_zero() -> None:
    """Section 2.6: the two at exactly 0 are named, and they are not windows."""
    exact = [row for row in thresholds.GROUP_B if row.value == 0.0]
    assert {row.key for row in exact} == {"choi_isometry", "iterate_positivity"}
    numbered = [row for row in thresholds.GROUP_B if row.value not in (None, 0.0)]
    # EIGHT in the contract's own Group B, and NINE here: ``limit_membership``
    # is the ninth, and it is a positive window like the other eight.
    # (``branch_support_dim`` is not one of them: its window is derived from
    # support_cutoff.)
    assert len(numbered) == 9
    contract_numbered = [
        row for row in thresholds.CONTRACT_LIVE if row.value not in (None, 0.0)
    ]
    assert len(contract_numbered) == 8
    for row in numbered:
        assert row.value is not None and row.value > 0.0, row.key

    # THE FOUR RELATIVE ROWS EACH NAME WHAT THEY ARE RELATIVE TO, because "its
    # reference is fixed by this contract rather than chosen by an
    # implementation" is half of what the rows buy.
    for row in thresholds.LIVE:
        if row.kind is ThresholdKind.RELATIVE:
            assert row.relative_to, row.key


@pytest.mark.contract
def test_every_row_is_carried_by_exactly_one_and_none_by_two() -> None:
    """The carrying rule, executed. Section 2.6 states it in those words."""
    table = thresholds.carrying_table()
    assert set(table) == {row.key for row in thresholds.LIVE}
    assert len(set(table.values())) == len(table)
    for key, carrier in table.items():
        assert carrier, key


@pytest.mark.contract
def test_the_positivity_split_kept_the_two_windows_apart() -> None:
    """The split of ``iterate_positivity``, and the one thing it must keep.

    Deciding per-block positivity AND the coupling residual at one declared
    value would be wrong. "The two need opposite windows and cannot share one":
    positivity is EXACTLY 0, the coupling residual keeps a positive window
    under its own name, and the drift that would otherwise pass silently is
    REPAIRED AND RECORDED under ``iterate_repair_window`` at the same number.
    """
    positivity = thresholds.ITERATE_POSITIVITY
    coupling = thresholds.ITERATE_COUPLING
    repair = thresholds.ITERATE_REPAIR_WINDOW

    assert positivity.value == 0.0
    assert positivity.kind is ThresholdKind.SPECTRAL_FLOOR
    assert coupling.kind is ThresholdKind.ENTRYWISE
    assert repair.kind is ThresholdKind.SPECTRAL_FLOOR
    # THE REPAIR WINDOW IS A POSITIVITY WINDOW'S SIZE, which is what makes the
    # split cost no run its positivity check.
    assert thresholds.declared(repair) == 1e-7
    assert thresholds.declared(coupling) == 1e-7
    # And no two of the three share a carrier.
    carriers = {
        thresholds.carrying_table()[row.key] for row in (positivity, coupling, repair)
    }
    assert len(carriers) == 3


@pytest.mark.contract
def test_every_live_row_has_a_carrier_a_call_reaches() -> None:
    """THE DUAL OF THE ONE-TO-ONE RULE.

    ``carrying_table`` refuses a carrier that decides TWO rows. This refuses a
    row whose carrier decides NONE: were the two callers of
    ``objective.linalg.is_hermitian`` decided exactly -- correctly, a declared
    predicate is not decided at a window -- the ``internal_hermiticity`` row
    would name a symbol nothing called, stating a fail-closed rule ("ABOVE THE
    WINDOW THE OPERATOR IS REFUSED") that no code path decided, while every
    formed operator went through ``hermitian_part`` and had its anti-Hermitian
    half discarded in silence.

    The same walk refuses carrier strings that name NOTHING ON EITHER SIDE
    (``numerical_rank`` for ``support_rank``, ``divided_differences`` for
    ``divided_difference``).

    WHAT IS ASSERTED, by what the carrier is:

    * a function -- the final component is a lowercase identifier that the
      named module defines -- must be CALLED somewhere in ``src/certiqs_key``;
    * a class attribute -- the component before it is CapWords -- must be a
      field of that class and must be READ somewhere;
    * a module constant -- the final component is upper case -- must resolve,
      and must be read somewhere;
    * a module -- the whole dotted path imports -- must be imported somewhere.

    A row whose carrier cannot be resolved at all fails the first step, which is
    the case the two stale names were in.
    """
    import ast
    import importlib

    source_root = Path(__file__).resolve().parents[2] / "src" / "certiqs_key"
    called: set[str] = set()
    read: set[str] = set()
    imported: set[str] = set()
    for path in sorted(source_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                function = node.func
                if isinstance(function, ast.Name):
                    called.add(function.id)
                elif isinstance(function, ast.Attribute):
                    called.add(function.attr)
            elif isinstance(node, ast.Attribute):
                read.add(node.attr)
            elif isinstance(node, ast.Name):
                read.add(node.id)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.rsplit(".", 1)[-1])
                for alias in node.names:
                    imported.add(alias.name)

    for row in thresholds.LIVE:
        # The one row whose carrier carries prose after it, because at exactly
        # zero no constant may carry it and the row says so.
        carrier = row.carried_by.split(" -- ")[0].strip()
        parts = carrier.split(".")
        leaf, parent = parts[-1], parts[-2]

        module = None
        for cut in range(len(parts), 0, -1):
            try:
                module = importlib.import_module(".".join(parts[:cut]))
            except ModuleNotFoundError:
                continue
            break
        assert module is not None, (row.key, carrier)

        if module.__name__ == carrier:
            assert leaf in imported, (row.key, carrier)
            continue
        if leaf.isupper():
            assert hasattr(module, leaf), (row.key, carrier)
            assert leaf in read, (row.key, carrier)
            continue
        if parent[:1].isupper():
            owner = getattr(module, parent, None)
            assert owner is not None, (row.key, carrier)
            assert leaf in getattr(owner, "__dataclass_fields__", {}), (
                row.key,
                carrier,
            )
            assert leaf in read, (row.key, carrier)
            continue
        assert hasattr(module, leaf), (row.key, carrier)
        if row.key in CARRIER_DEFINED_BUT_NOT_CALLED:
            continue
        assert leaf in called, (row.key, carrier)


#: THE ROWS WHOSE CARRIER IS DEFINED AND CALLED NOWHERE, AND THERE ARE NONE.
#: A RATCHET THAT ONLY SHRINKS: a NEW entry here is a regression and is the
#: thing this list makes visible.
#:
#: A carrier computing ``dim W_{chat,s}`` as the numerical rank of the Kraus
#: stack of Eq. ``eq:Kstack`` is the RIGHT-HAND SIDE of Eq. ``eq:hsupp-check``,
#: and ``frank-wolfe/rem:fo-one-ruler`` says in so many words that BOTH SIDES of
#: ``eq:hsupp-check`` are computed, each at its own declared number, so such a
#: carrier is called (the window is derived from ``support_cutoff``).
CARRIER_DEFINED_BUT_NOT_CALLED: frozenset[str] = frozenset()
