"""The frozen compiler registry was PARTITIONED THREE WAYS, and the cut is checked.

WHY THE FILE EXISTS. The oracle registries "are the executable memory of every
derivation ... and are NEVER REGENERATED FROM THE CODE THEY TEST"
(PRINCIPLES.md section 2.3), so splitting one is the kind of edit that has to
be checkable rather than trusted. The split was a textual CUT along the
original group boundaries:

* group PC-H -- source replacement and its certificate -- and the one group
  PC-M entry that pins the same labels, ``O-PC-CERTIFICATE-OPERATOR``, moved
  into ``registry_transmitter.py``. PC10 and PC11 are ``transmitter`` claims;
* groups PC-I and PC-J -- the worked BB84 declaration and the conjugation
  branch pair -- moved into ``registry_instances_bb84.py``. An instance is
  DATA and not a claim (PRINCIPLES.md section 5), and these two entries are its
  executable memory;
* everything else stayed in ``registry_protocol_compiler.py``.

WHAT IS CHECKED, AND WHY EACH HALF OF IT MATTERS.

* THE THREE MODULES ARE PAIRWISE DISJOINT. A value defined twice could drift,
  and the whole point of a frozen registry is that it cannot.
* THEIR UNION IS THE ORIGINAL ``__all__``, carried in the compiler's
  half as ``ORIGINAL_REGISTRY_NAMES`` -- a list of NAMES, not of oracle values
  -- plus exactly the accessors the split itself needed. So the cut can
  neither lose a value nor invent one. Two names were NARROWED rather than
  moved -- ``PC_ORACLES`` and ``pc_oracle`` answer for the compiler's half
  alone -- and ``PARTITION_NARROWED`` says so with the reason.
* THE DEPENDENCY RUNS ONE WAY. ``registry_protocol_compiler`` names nothing in
  either of the two halves that left it, which is what makes the compiler's
  half readable on its own and what stops a circular import.
* THE ORACLE ENTRIES ARE PARTITIONED TOO, and their ids are disjoint and
  complete against the original ``PC_ORACLES`` order.
* THE MOVED ENTRIES KEEP THEIR ORIGINAL CLAIM IDS. ``O-PC-CERTIFICATE``
  still says ``PC10``/``PC11`` and ``O-PC-BB84`` still says ``PC12``: those are
  the ids the derivations were written against, and re-labelling frozen
  evidence to agree with a later structure is the one thing a freeze forbids.

WHAT IS NOT CHECKED HERE, stated rather than left as a gap: a BYTE comparison
against the original single file. That file is not in this repository, so a
test reading it would be unrunnable. The name-level union
above is what survives, and the cut itself is recorded in the header of all
three halves. (``test_reductions_registry_partition.py`` takes the same
disposition for the same reason.)
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import registry_instances_bb84 as bb84
import registry_protocol_compiler as compiler
import registry_transmitter as transmitter

#: The names the SPLIT created: one entry tuple and one accessor per half that
#: left. They are not values of the original registry and are the only
#: additions the cut made.
SPLIT_ACCESSORS = frozenset(
    {
        "TRANSMITTER_PC_ORACLES",
        "transmitter_pc_oracle",
        "BB84_PC_ORACLES",
        "bb84_pc_oracle",
        "ORIGINAL_REGISTRY_NAMES",
    }
)

HALVES = (compiler, transmitter, bb84)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_three_registry_halves_are_pairwise_disjoint() -> None:
    """No value is defined twice; a duplicated frozen value could drift."""
    assert set(compiler.__all__).isdisjoint(transmitter.__all__)
    assert set(compiler.__all__).isdisjoint(bb84.__all__)
    assert set(transmitter.__all__).isdisjoint(bb84.__all__)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_union_of_the_halves_is_the_original_all() -> None:
    """The cut loses nothing and invents nothing but its own accessors."""
    union = set().union(*(set(half.__all__) for half in HALVES))
    original = set(compiler.ORIGINAL_REGISTRY_NAMES)
    assert union - original == SPLIT_ACCESSORS
    # NOTHING WAS LOST: every name of the original __all__ is in one
    # of the three halves.
    assert original - union == set()
    # TWO NAMES WERE NARROWED RATHER THAN MOVED, and each says why in prose of
    # substance rather than a marker word.
    narrowed = {name for name, _ in compiler.PARTITION_NARROWED}
    assert narrowed == {"PC_ORACLES", "pc_oracle"}
    assert narrowed <= set(compiler.__all__)
    for _name, reason in compiler.PARTITION_NARROWED:
        assert len(reason) > 80


@pytest.mark.contract
@pytest.mark.oracle
def test_every_declared_name_resolves_in_the_half_that_declares_it() -> None:
    """An ``__all__`` entry that resolves to nothing is a value that was lost."""
    for half in HALVES:
        for name in half.__all__:
            assert hasattr(half, name), (half.__name__, name)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_compiler_half_names_nothing_in_the_halves_that_left() -> None:
    """The dependency runs one way: the two halves read the compiler's, not back.

    Read off the SOURCE rather than off the imported module, so that a name
    used only inside a derivation string or a comment is not mistaken for a
    reference and, more importantly, so that a real reference cannot hide
    behind a runtime path that no test takes.
    """
    source = (Path(__file__).parent / "registry_protocol_compiler.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    moved = set(transmitter.__all__) | set(bb84.__all__)
    # ORIGINAL_REGISTRY_NAMES is a list of STRINGS and names nothing.
    assert used & moved == set()
    # And this half IMPORTS neither of the two, which is what makes it
    # readable on its own.
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported.isdisjoint({"registry_transmitter", "registry_instances_bb84"})


@pytest.mark.contract
@pytest.mark.oracle
def test_the_oracle_entries_are_partitioned_and_complete() -> None:
    """Twenty-four entries in three tuples, disjoint, in the frozen order."""
    compiler_ids = [entry.oracle_id for entry in compiler.PC_ORACLES]
    transmitter_ids = [entry.oracle_id for entry in transmitter.TRANSMITTER_PC_ORACLES]
    bb84_ids = [entry.oracle_id for entry in bb84.BB84_PC_ORACLES]

    assert transmitter_ids == [
        "O-PC-CERTIFICATE",
        "O-PC-SR-BOUNDARY",
        "O-PC-CERTIFICATE-OPERATOR",
    ]
    assert bb84_ids == ["O-PC-BB84", "O-PC-CONJUGATION"]
    assert set(compiler_ids).isdisjoint(transmitter_ids)
    assert set(compiler_ids).isdisjoint(bb84_ids)
    assert len(compiler_ids) + len(transmitter_ids) + len(bb84_ids) == 24
    # Each accessor answers for its own half and refuses the others'.
    for oracle_id in transmitter_ids:
        assert transmitter.transmitter_pc_oracle(oracle_id).oracle_id == oracle_id
        with pytest.raises(KeyError):
            compiler.pc_oracle(oracle_id)
    for oracle_id in bb84_ids:
        assert bb84.bb84_pc_oracle(oracle_id).oracle_id == oracle_id
        with pytest.raises(KeyError):
            compiler.pc_oracle(oracle_id)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_moved_entries_keep_their_frozen_claim_ids() -> None:
    """The ``claims`` tuples are HISTORY and are not re-labelled.

    PC10 and PC11 are ``transmitter`` claims now and PC12 is an instance, but
    the derivations were written against those ids and the mapping is in each
    half's header. Editing frozen evidence to agree with a later structure is
    exactly what a freeze forbids.
    """
    transmitter_claims = {
        claim
        for entry in transmitter.TRANSMITTER_PC_ORACLES
        for claim in entry.claims
    }
    assert {"PC10", "PC11"} <= transmitter_claims
    bb84_claims = {claim for entry in bb84.BB84_PC_ORACLES for claim in entry.claims}
    assert "PC12" in bb84_claims
    # AND A COMPILER ENTRY MAY STILL CITE PC12, which is not a slip: the
    # frozen ``claims`` tuples say which labels a derivation READS, and the
    # exact-summation entry reads the BB84 weight presentations. What the cut
    # moved is the ENTRIES whose SUBJECT those labels are, and no entry of this
    # half carries one of their ids.
    moved_ids = {entry.oracle_id for entry in transmitter.TRANSMITTER_PC_ORACLES}
    moved_ids |= {entry.oracle_id for entry in bb84.BB84_PC_ORACLES}
    assert {entry.oracle_id for entry in compiler.PC_ORACLES}.isdisjoint(moved_ids)


@pytest.mark.contract
@pytest.mark.oracle
def test_no_half_imports_the_module_it_pins() -> None:
    """An oracle that imported its subject would check the code against itself."""
    for name in (
        "registry_protocol_compiler.py",
        "registry_transmitter.py",
        "registry_instances_bb84.py",
    ):
        source = (Path(__file__).parent / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
        assert not any(
            module.startswith(("certiqs_key", "instances")) for module in imported
        ), name
