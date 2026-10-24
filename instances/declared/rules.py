"""The rule language: alphabets, and ordered rules expanded into total tables.

WHY RULES AND NOT TABLES. The compiler reads its public structure as tables:
an announcement per readout letter, a sifting verdict per class, a key bit per
``(readout, class)``. BB84's key table alone has 36 rows and bbm92's about a
thousand, while each says one thing ("the key bit is the signal's bit"). A
document therefore writes a few ordered rules and this module expands them,
row for row, into exactly the mappings ``PublicPart``, ``Message``,
``CoarseGraining`` and ``ChoiceWeighting`` take.

WHAT THE EXPANDER DOES NOT DECIDE. A key no rule matches is OMITTED and listed
in :attr:`Expansion.unmatched`, never refused: whether a map is total is the
compiler's check (V1), and its refusal is data. Only what has no
meaning as a document is refused here: a path naming a variable the table does
not have or a component no entry carries (``rule_reference_unknown``), and a
value that cannot be rendered for the entry it matched (``rule_value_invalid``).

THE EVALUATION RULES. Rules are tried in order
and the first match wins. A ``when`` ANDs its conditions. A condition whose
path names a component the entry lacks does not match, and neither does an
``eq`` or ``ne`` either of whose sides is missing, also under ``not``: a
comparison with nothing is undecided, and an undecided condition never selects
a rule.
"""

from __future__ import annotations

import itertools
import math
import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from instances.declared.errors import DocumentError, DocumentReason
from instances.declared.limits import (
    MAX_ALPHABET_LABELS,
    MAX_TABLE_ROWS,
    MAX_TABLE_WORK,
    check_size,
)
from instances.declared.model import (
    AlphabetNode,
    EnumAlphabet,
    Eq,
    IntOf,
    MessageValue,
    Ne,
    Not,
    Pattern,
    ProductAlphabet,
    Rule,
    Switch,
)
from instances.declared.values import Environment, pointer_join, unwrap

__all__ = [
    "Entry",
    "ExpandedRow",
    "Expansion",
    "Variable",
    "build_alphabet",
    "build_alphabets",
    "check_table",
    "expand",
    "expand_bindings",
    "render",
]

#: The table value of a rule: a label, or an integer literal.
type TableValue = str | int


@dataclass(frozen=True)
class Entry:
    """One letter of an alphabet: its label and its components.

    ``components`` always holds ``label`` itself, then the product dimensions
    and attributes the entry was given.
    """

    label: str
    components: Mapping[str, str]

    @classmethod
    def of(cls, label: str, attributes: Mapping[str, str] | None = None) -> Entry:
        """Return an entry with ``label`` and ``attributes``."""
        return cls(label, {**(attributes or {}), "label": label})

    @classmethod
    def absent(cls) -> Entry:
        """Return the entry of a variable that has no value for this key.

        A coarse-graining's ``port`` exists only where exactly one port fired:
        on every other pattern the variable is bound to this entry, which has
        no component at all, so that every condition on it is undecided and
        does not match and a template reading it is refused.
        """
        return cls("", {})

    def component(self, name: str) -> str | None:
        """Return a component, or ``None`` where this entry lacks it."""
        return self.components.get(name)


@dataclass(frozen=True)
class Variable:
    """A table variable and the entries it ranges over, in declared order."""

    name: str
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class ExpandedRow:
    """One expanded key: its value and the index of the rule that fired."""

    key: tuple[str, ...]
    value: TableValue
    rule_index: int
    #: The message value's components where the rule wrote ``{label, attrs}``.
    entry: Entry | None = None


@dataclass(frozen=True)
class Expansion:
    """A rule list expanded over its domain."""

    table: str
    variables: tuple[str, ...]
    rows: tuple[ExpandedRow, ...]
    unmatched: tuple[tuple[str, ...], ...]
    #: Where the expanded rule list is written, as a JSON pointer.
    path: str = ""

    def mapping(self) -> dict[tuple[str, ...], TableValue]:
        """Return the table: each matched key to its value."""
        return {row.key: row.value for row in self.rows}

    def alphabet(self) -> tuple[Entry, ...]:
        """Return the values in first appearance, as entries (a ``derived`` alphabet).

        A value written as ``{label, attrs}`` carries its attributes; a value
        reached twice with different attributes is refused, because the
        alphabet would give one label two meanings.
        """
        seen: dict[str, Entry] = {}
        for row in self.rows:
            entry = row.entry or Entry.of(str(row.value))
            if entry.label in seen and seen[entry.label] != entry:
                raise DocumentError(
                    f"{self.table}: the value {entry.label!r} is written with two "
                    f"different attribute sets ({dict(seen[entry.label].components)} "
                    f"and {dict(entry.components)})",
                    reason=DocumentReason.RULE_VALUE_INVALID,
                    path=self.path,
                )
            seen.setdefault(entry.label, entry)
        return tuple(seen.values())

    def as_record(self) -> dict[str, Any]:
        """Return the expansion as recorded: rows ``[key..., value, rule_index]``."""
        return {
            "variables": list(self.variables),
            "rows": [[*row.key, row.value, row.rule_index] for row in self.rows],
            "unmatched": [list(key) for key in self.unmatched],
        }


# ---------------------------------------------------------------------------
#  Templates
# ---------------------------------------------------------------------------

_PLACEHOLDER = re.compile(r"\{\{|\}\}|\{([^{}]*)\}")


class _Missing(Exception):
    """A template named something the entry does not carry."""


def placeholders(template: str) -> tuple[str, ...]:
    """Return the names a template reads, in order."""
    return tuple(
        match.group(1).strip()
        for match in _PLACEHOLDER.finditer(template)
        if match.group(1) is not None
    )


def render(template: str, lookup: Callable[[str], str | None]) -> str:
    """Return ``template`` with each ``{name}`` filled; ``{{`` and ``}}`` are braces."""

    def substitute(match: re.Match[str]) -> str:
        if match.group(0) == "{{":
            return "{"
        if match.group(0) == "}}":
            return "}"
        name = match.group(1).strip()
        value = lookup(name)
        if value is None:
            raise _Missing(name)
        return value

    return _PLACEHOLDER.sub(substitute, template)


# ---------------------------------------------------------------------------
#  Alphabets
# ---------------------------------------------------------------------------


def build_alphabets(
    named: Mapping[str, AlphabetNode], path: str = "/alphabets"
) -> dict[str, tuple[Entry, ...]]:
    """Return every named alphabet, built, refusing repeated labels and cycles."""
    return {
        name: build_alphabet(node, named, pointer_join(path, name))
        for name, node in named.items()
    }


def build_alphabet(
    node: AlphabetNode,
    named: Mapping[str, AlphabetNode],
    path: str,
    _stack: tuple[str, ...] = (),
) -> tuple[Entry, ...]:
    """Return an alphabet node's entries in declared order."""
    if isinstance(node, str):
        if node not in named:
            raise DocumentError(
                f"{node!r} names no alphabet ({sorted(named)})",
                reason=DocumentReason.RULE_REFERENCE_UNKNOWN,
                path=path,
            )
        if node in _stack:
            raise DocumentError(
                f"the alphabet {node!r} contains itself ({' -> '.join(_stack)})",
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path=path,
            )
        return build_alphabet(
            named[node], named, f"/alphabets{pointer_join('', node)}", (*_stack, node)
        )
    entries: list[Entry]
    if isinstance(node, EnumAlphabet):
        entries = []
        for item in node.enum:
            if isinstance(item, str):
                entries.append(Entry.of(item))
            else:
                attributes = {
                    key: value for key, value in item.items() if key != "label"
                }
                entries.append(Entry.of(item["label"], attributes))
    elif isinstance(node, ProductAlphabet):
        dims = node.product.dims
        check_size(
            math.prod(len(values) for values in dims.values()),
            MAX_ALPHABET_LABELS,
            "the product alphabet's size",
            pointer_join(path, "product", "dims"),
        )
        entries = []
        for values in itertools.product(*dims.values()):
            components = dict(zip(dims, values, strict=True))
            try:
                label = render(node.product.label, components.get)
            except _Missing as missing:
                raise DocumentError(
                    f"the label template {node.product.label!r} reads {missing}, "
                    f"which is not a dimension ({list(dims)})",
                    reason=DocumentReason.RULE_REFERENCE_UNKNOWN,
                    path=pointer_join(path, "product", "label"),
                ) from None
            entries.append(Entry.of(label, components))
    else:
        entries = []
        for index, part in enumerate(node.union):
            where = pointer_join(path, "union", index)
            entries += build_alphabet(part, named, where, _stack)
            check_size(len(entries), MAX_ALPHABET_LABELS, "the union's size", where)
    check_size(len(entries), MAX_ALPHABET_LABELS, "the alphabet's size", path)
    if node.attrs:
        entries = [_with_attributes(entry, node.attrs, path) for entry in entries]
    counts = Counter(entry.label for entry in entries)
    repeated = sorted(label for label, count in counts.items() if count > 1)
    if repeated:
        raise DocumentError(
            f"the alphabet repeats the labels {repeated}",
            reason=DocumentReason.ALPHABET_LABELS_NOT_DISTINCT,
            path=path,
        )
    return tuple(entries)


def _with_attributes(entry: Entry, attributes: Mapping[str, str], path: str) -> Entry:
    """Add a part's constant attributes, refusing one that contradicts the entry."""
    for name, value in attributes.items():
        if entry.components.get(name, value) != value:
            raise DocumentError(
                f"the entry {entry.label!r} already has {name} = "
                f"{entry.components[name]!r}; the part's attrs say {value!r}",
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path=pointer_join(path, "attrs", name),
            )
    return Entry(entry.label, {**entry.components, **attributes})


# ---------------------------------------------------------------------------
#  Expansion
# ---------------------------------------------------------------------------


def _read(path: str, binding: Mapping[str, Entry]) -> str | None:
    """Return the value a ``var`` or ``var.component`` path reads, or ``None``."""
    variable, _, component = path.partition(".")
    entry = binding[variable]
    return entry.component(component or "label")


def _pattern(pattern: Pattern, value: str, binding: Mapping[str, Entry]) -> bool | None:
    """Return whether ``value`` matches ``pattern``; ``None`` where undecided."""
    if isinstance(pattern, str):
        return value == pattern
    if isinstance(pattern, list):
        return value in pattern
    if isinstance(pattern, Eq | Ne):
        other = _read(pattern.eq if isinstance(pattern, Eq) else pattern.ne, binding)
        if other is None:
            return None
        return (value == other) if isinstance(pattern, Eq) else (value != other)
    inner = _pattern(pattern.not_, value, binding)
    return None if inner is None else not inner


def _matches(rule: Rule, binding: Mapping[str, Entry]) -> bool:
    for path, pattern in (rule.when or {}).items():
        value = _read(path, binding)
        if value is None or _pattern(pattern, value, binding) is not True:
            return False
    return True


def _pattern_paths(pattern: Pattern) -> list[str]:
    if isinstance(pattern, Eq):
        return [pattern.eq]
    if isinstance(pattern, Ne):
        return [pattern.ne]
    if isinstance(pattern, Not):
        return _pattern_paths(pattern.not_)
    return []


def _value_paths(value: object) -> list[str]:
    if isinstance(value, str):
        return list(placeholders(value))
    if isinstance(value, MessageValue):
        return [
            *placeholders(value.label),
            *(
                name
                for template in value.attrs.values()
                for name in placeholders(template)
            ),
        ]
    if isinstance(value, IntOf):
        return [value.int_]
    if isinstance(value, Switch):
        cases = [
            *value.cases.values(),
            *([] if value.default is None else [value.default]),
        ]
        return [path for case in cases for path in _value_paths(case)]
    return []


def check_table(
    table: str,
    rules: object,
    variables: Mapping[str, Sequence[Entry] | None],
    path: str,
) -> None:
    """Check the references of EVERY case of a (possibly switched) rule list.

    ``variables`` maps each variable of the table to its entries, or to
    ``None`` where the alphabet is the engine's and known only after emission;
    then only the variable's name is checked here, and its components when the
    table is expanded.
    """
    for rule_list, where in _rule_lists(rules, path):
        _check_paths(table, rule_list, variables, where)


def _rule_lists(node: object, path: str) -> list[tuple[Sequence[Rule], str]]:
    if isinstance(node, Switch):
        found: list[tuple[Sequence[Rule], str]] = []
        for case, branch in node.cases.items():
            found += _rule_lists(branch, pointer_join(path, "cases", case))
        if node.default is not None:
            found += _rule_lists(node.default, pointer_join(path, "default"))
        return found
    assert isinstance(node, list)
    return [(node, path)]


def check_rule_references(
    table: str, rules: Sequence[Rule], variables: Sequence[Variable], path: str
) -> None:
    """Refuse a path whose variable the table lacks or whose component no entry has."""
    _check_paths(
        table, rules, {variable.name: variable.entries for variable in variables}, path
    )


def _check_paths(
    table: str,
    rules: Sequence[Rule],
    variables: Mapping[str, Sequence[Entry] | None],
    path: str,
) -> None:
    components = {
        name: None
        if entries is None
        else {component for entry in entries for component in entry.components}
        for name, entries in variables.items()
    }
    for index, rule in enumerate(rules):
        paths = [
            (where, pointer_join(path, index, "when", where))
            for where in (rule.when or {})
        ]
        paths += [
            (other, pointer_join(path, index, "when", where))
            for where, pattern in (rule.when or {}).items()
            for other in _pattern_paths(pattern)
        ]
        paths += [
            (read, pointer_join(path, index, "value"))
            for read in _value_paths(rule.value)
        ]
        for read, where in paths:
            variable, _, component = read.partition(".")
            if variable not in components:
                raise DocumentError(
                    f"{table}: {read!r} names no variable of this table "
                    f"({list(components)})",
                    reason=DocumentReason.RULE_REFERENCE_UNKNOWN,
                    path=where,
                )
            known = components[variable]
            if component and known is not None and component not in known:
                raise DocumentError(
                    f"{table}: no entry of {variable} has the component "
                    f"{component!r} ({sorted(known)})",
                    reason=DocumentReason.RULE_REFERENCE_UNKNOWN,
                    path=where,
                )


def expand(
    table: str,
    rules: object,
    variables: Sequence[Variable],
    *,
    path: str,
    environment: Environment | None = None,
) -> Expansion:
    """Expand ``rules`` over the product of ``variables`` (the first varies slowest).

    ``rules`` is a rule list or a switch over rule lists; ``environment``
    resolves switches and is needed only where one is written. ``table`` names
    the table in every refusal.
    """
    check_table(table, rules, {v.name: v.entries for v in variables}, path)
    rule_list, rules_path = _unwrap(rules, environment, path)
    keys = math.prod(len(variable.entries) for variable in variables)
    check_size(keys, MAX_TABLE_ROWS, f"{table}: the number of keys", rules_path)
    check_size(
        keys * max(1, len(rule_list)),
        MAX_TABLE_WORK,
        f"{table}: the keys times the rules",
        rules_path,
    )
    names = tuple(variable.name for variable in variables)
    rows: list[ExpandedRow] = []
    unmatched: list[tuple[str, ...]] = []
    for combination in itertools.product(*(v.entries for v in variables)):
        binding = dict(zip(names, combination, strict=True))
        key = tuple(entry.label for entry in combination)
        for index, rule in enumerate(rule_list):
            if _matches(rule, binding):
                value, entry = _value(
                    rule.value,
                    binding,
                    environment,
                    pointer_join(rules_path, index, "value"),
                    f"{table} at {key} by rule {index}",
                )
                rows.append(ExpandedRow(key, value, index, entry))
                break
        else:
            unmatched.append(key)
    return Expansion(table, names, tuple(rows), tuple(unmatched), rules_path)


def expand_bindings(
    table: str,
    rules: object,
    variables: Sequence[Variable],
    keys: Sequence[tuple[tuple[str, ...], Mapping[str, Entry]]],
    *,
    path: str,
    environment: Environment | None = None,
    key_names: Sequence[str] = ("key",),
) -> Expansion:
    """Expand ``rules`` over an explicit domain: each key with its own binding.

    For a table whose domain is not the product of its variables: a
    coarse-graining ranges over the ``2^K`` click patterns, and each pattern
    binds ``count``, ``port`` and ``fired`` at once. ``variables``
    carries every entry a variable takes anywhere in the domain, for the
    reference check; ``keys`` is the domain in its declared order, and
    ``key_names`` names a key's parts in the record.
    """
    check_table(table, rules, {v.name: v.entries for v in variables}, path)
    rule_list, rules_path = _unwrap(rules, environment, path)
    check_size(len(keys), MAX_TABLE_ROWS, f"{table}: the number of keys", rules_path)
    check_size(
        len(keys) * max(1, len(rule_list)),
        MAX_TABLE_WORK,
        f"{table}: the keys times the rules",
        rules_path,
    )
    rows: list[ExpandedRow] = []
    unmatched: list[tuple[str, ...]] = []
    for key, binding in keys:
        for index, rule in enumerate(rule_list):
            if _matches(rule, binding):
                value, entry = _value(
                    rule.value,
                    binding,
                    environment,
                    pointer_join(rules_path, index, "value"),
                    f"{table} at {key} by rule {index}",
                )
                rows.append(ExpandedRow(key, value, index, entry))
                break
        else:
            unmatched.append(key)
    return Expansion(table, tuple(key_names), tuple(rows), tuple(unmatched), rules_path)


def _unwrap(
    node: object, environment: Environment | None, path: str
) -> tuple[Any, str]:
    if isinstance(node, Switch):
        if environment is None:
            raise DocumentError(
                f"a switch over {node.switch} needs a configuration to choose by",
                reason=DocumentReason.SWITCH_CASE_MISSING,
                path=path,
            )
        return unwrap(node, environment, path)
    return node, path


def _value(
    node: object,
    binding: Mapping[str, Entry],
    environment: Environment | None,
    path: str,
    where: str,
) -> tuple[TableValue, Entry | None]:
    """Render a matched rule's value for ``binding``."""
    node, path = _unwrap(node, environment, path)

    def lookup(name: str) -> str | None:
        return _read(name, binding)

    try:
        if isinstance(node, bool):
            raise _Missing("a Boolean is not a table value")
        if isinstance(node, int):
            return node, None
        if isinstance(node, str):
            return render(node, lookup), None
        if isinstance(node, MessageValue):
            label = render(node.label, lookup)
            attributes = {
                name: render(template, lookup) for name, template in node.attrs.items()
            }
            return label, Entry.of(label, attributes)
        if isinstance(node, IntOf):
            text = lookup(node.int_)
            if text is None:
                raise _Missing(node.int_)
            if not re.fullmatch(r"[-+]?[0-9]+", text):
                raise _Missing(f"{node.int_} = {text!r}, which is not an integer")
            return int(text), None
    except _Missing as missing:
        raise DocumentError(
            f"{where}: the value cannot be rendered, it reads {missing}",
            reason=DocumentReason.RULE_VALUE_INVALID,
            path=path,
        ) from None
    raise DocumentError(
        f"{where}: {type(node).__name__} is not a table value",
        reason=DocumentReason.RULE_VALUE_INVALID,
        path=path,
    )
