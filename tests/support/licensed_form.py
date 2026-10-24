"""Rewrite a frozen declaration's constraint list into the LICENSED form.

WHY THIS EXISTS. Contract 1.0.0's Definition ``def:homog`` declares a
constraint entry's right-hand side in one of two TAGGED forms, and part (i) of
the two-part security gate is a type check on that tag. The frozen 0.1.0
operator-bundle builder in ``tests/oracles/dummy_bundles.py`` "types every bound
as an array" -- it refuses a non-array bound outright -- so every trusted-mode
entry that crosses it declares the ``general`` form, which is ADMISSIBLE INPUT
and IS NEVER LICENSED.

That is a fact about the WIRE and not about the mathematics: ``TOY-5`` and
``TOY-6`` carry ``homogeneous_scalar = 0.5`` in their frozen records, so the
declarations those records describe ARE in the licensed class; the 0.1.0
manifest simply has no field to carry the scalar. This helper rewrites the
in-memory declaration into the form the record declares, so that the licensed
PATH is exercised on the frozen numbers without editing anything frozen and
without inventing a tag at the artifact boundary.

NOTHING HERE DECIDES A GATE. The rewrite is a test fixture: it takes the scalar
the frozen record already names and re-declares the entry with it. A producer
does the same thing on its own side of the interface, which is what Remark
``rem:optol-reach`` (b) means by "shifting the constant ... is its own step,
taken on its own side".
"""

from __future__ import annotations

from dataclasses import replace

from toy_declarations import ToyDeclaration

from certiqs_key.meat_core.declaration.declaration import (
    ConstraintEntry,
    ProtocolDeclaration,
    RhsTag,
)


def as_declared_form(
    declaration: ProtocolDeclaration, frozen: ToyDeclaration
) -> ProtocolDeclaration:
    """Return the declaration with each entry re-declared as the record says.

    An entry whose frozen record names a ``homogeneous_scalar`` is re-declared
    with the ``homogeneous`` tag carrying that scalar; one whose record names
    ``None`` keeps the ``general`` tag and its operator. Every other component
    is untouched.
    """
    entries = tuple(
        entry
        if record.homogeneous_scalar is None
        else ConstraintEntry(
            operator_blocks=entry.operator_blocks,
            relation=entry.relation,
            rhs_tag=RhsTag.HOMOGENEOUS,
            bound=record.homogeneous_scalar,
        )
        for entry, record in zip(
            declaration.constraint_list, frozen.constraint_list, strict=True
        )
    )
    return replace(declaration, constraint_list=entries)
