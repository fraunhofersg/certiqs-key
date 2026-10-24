"""Assumption bindings: the declared values each ledger row's assumption is about.

WHY THIS EXISTS. Values are bound per assumption: every emitter records,
beside each row of its assumption ledger, the declared values that row's assumption's
clauses are about, so that a run report can say which of a user's inputs each premise
constrains. The receiver, reductions and statistics carry them on each row
(``constrains``); the emitters whose ledger is a tuple of bare machine keys (the
protocol compiler and the transmitter, with its decoy submodule) carry them BESIDE that
tuple, which frozen expectations pin and which therefore keeps its shape. This file
holds the one shape those emitters share and the one JSON form an artefact's machine
record writes them in, so that no emitter spells a second. It decides nothing
and names no assumption.

THE SHAPE. A binding is an immutable ``(name, value)`` pair. The name is the
declared input the value comes from. The value is a string, an ``int``, a
``bool``, ``None``, a binary64 ``float`` (a declared floating-point parameter,
bound as itself, as the receiver binds ``eps_eig``), or a tuple of such
values or of further ``(name, value)`` pairs; an exact rational is written
``"p/q"`` (:func:`exact`), as the run record writes every rational. AN
OPERATOR IS NEVER INLINED: an operator-valued input is bound by its shape --
the alphabet that indexes it and its dimension -- and its entries stay in the
artefact that carries them, where the run tier's pointer finds them. A
ledger's bindings are a tuple of ``(machine key, bindings)`` pairs in the
ledger's own order, one per row, a row that binds no declared value carrying
``()``.

Cost: one small module and one JSON rule shared by four emitters, against a copy of the
rule in each.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

__all__ = [
    "Binding",
    "Bindings",
    "LedgerBindings",
    "as_json",
    "exact",
    "is_immutable",
    "ledger_bindings_record",
]

#: One binding: the declared input's name and the value bound.
type Binding = tuple[str, object]
#: The bindings of one ledger row, in the emitter's order.
type Bindings = tuple[Binding, ...]
#: A ledger's bindings: ``(machine key, bindings)`` per row, in ledger order.
type LedgerBindings = tuple[tuple[str, Bindings], ...]


def exact(value: Fraction | int) -> str:
    """Return an exact rational as ``"p/q"`` (an integer as ``"n"``)."""
    return str(Fraction(value))


def _is_pairs(value: tuple[object, ...]) -> bool:
    """Whether ``value`` is a non-empty tuple of ``(name, value)`` pairs.

    The names must be distinct, so that the pairs read as one object.
    """
    if not value:
        return False
    names: list[str] = []
    for item in value:
        if not (isinstance(item, tuple) and len(item) == 2):
            return False
        name = item[0]
        if not isinstance(name, str):
            return False
        names.append(name)
    return len(set(names)) == len(names)


def as_json(value: object) -> Any:
    """Return a bound value in its JSON form.

    A tuple of ``(name, value)`` pairs with distinct names becomes an object,
    any other tuple a list; a :class:`~fractions.Fraction` becomes ``"p/q"``.
    The run tier's reading of a binding (``runs.assumptions``) is the same, so
    an artefact's record and a run record agree on every value.
    """
    if isinstance(value, Fraction):
        return exact(value)
    if isinstance(value, tuple):
        if _is_pairs(value):
            return {name: as_json(item) for name, item in value}
        return [as_json(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): as_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_json(item) for item in value]
    return value


def ledger_bindings_record(rows: LedgerBindings) -> dict[str, dict[str, Any]]:
    """Return a ledger's bindings as an artefact's machine record writes them.

    ``{machine key: {name: value}}`` in ledger order, a row that binds nothing
    carrying ``{}``.
    """
    return {
        key: {name: as_json(value) for name, value in bindings}
        for key, bindings in rows
    }


def is_immutable(value: object) -> bool:
    """Whether ``value`` is built only of the immutable values a binding may hold."""
    if value is None or isinstance(value, str | int | bool | float | Fraction):
        return True
    if isinstance(value, tuple):
        return all(is_immutable(item) for item in value)
    return False
