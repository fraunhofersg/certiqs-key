"""The value language: exact scalars, references, arithmetic, switches, matrices.

WHY A LANGUAGE AT ALL. A document must say "the weight is the parameter
``alice_z``", "the window is ``photon_cutoff + 1``" and "under
``acceptance_map = pair-resolved`` the map is this one", and say it as data
that a validator can read without running code. The language is
deliberately small:

- a JSON integer is that integer; a number string (``"1/3"``, ``"0.02"``,
  ``"2^-30"``) is a constant of the arithmetic below, read exactly;
- ``{param: name}`` is a configuration value, ``{param: name, port: label}``
  one entry of a per-port value;
- ``{expr: "..."}`` is a closed exact arithmetic over ``Fraction``: ``+ - * /``,
  integer powers and parentheses, with parameter names as its only free
  variables. There are no functions, no irrationals and no comparisons; an
  irrational quantity (a receiver angle) is carried as a ``_pi`` field;
- ``{switch: name, cases, default?}`` chooses a node by a ``choice``
  parameter's value;
- a matrix is its rows, or one of three generators that call the same-named
  ``foundations.exact`` function.

WHAT IT NEVER DOES. It never rounds. A value a module needs on a lattice or in
binary64 is either admissible already, and the module decides it, or it is
prepared by the engine's own input preparation (``snap`` and
``preparations``), which records what it did. Whether a matrix is Hermitian,
positive or complete is the modules' decision; only a matrix that cannot be
read at all is refused here (``matrix_malformed``).

THE READER IS A TRUST BOUNDARY. A document can arrive from an MCP client, so
every expression is bounded before it is evaluated: its length, its token
count, its nesting depth, a literal's decimal exponent, and the size of every
intermediate result. A document that exceeds a bound is refused
(``expression_invalid``) rather than allowed to exhaust the stack or memory.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from typing import Any, cast

from pydantic import BaseModel

from certiqs_key.foundations import exact
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.runs.inputs import NumericInput, exact_input
from certiqs_key.runs.surface import Kind
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.model import (
    Expr,
    IdentityMatrix,
    MatrixRows,
    Outer,
    ParamRef,
    Scale,
    Switch,
)

__all__ = [
    "Environment",
    "Expression",
    "ParameterAbsentError",
    "check_references",
    "choose",
    "constant",
    "evaluate_exact",
    "evaluate_int",
    "matrix",
    "number",
    "parse_expression",
    "unwrap",
    "walk",
]

#: The largest exponent ``^`` admits, and the largest decimal exponent a
#: literal may carry (``1e-4096``): enough for every binary64 power of two
#: (``2^-1074``) and far below what would exhaust memory.
MAX_EXPONENT = 4096
#: The longest expression text, and the most tokens one may hold.
MAX_EXPRESSION_LENGTH = 1024
MAX_TOKENS = 256
#: The deepest nesting of parentheses and unary minus signs.
MAX_NESTING = 32
#: The largest numerator or denominator, in bits, any intermediate result may
#: have (``2^65536``); a power is refused before it is computed.
MAX_BITS = 1 << 16


class ParameterAbsentError(DocumentError):
    """A declared parameter has no value in the configuration being read.

    Raised, never returned, so that the one caller that may proceed without the
    value -- ``default_config``'s derived defaults, which leave such a target
    absent for the run tier's key check to decide -- catches exactly this.
    """


@dataclass(frozen=True)
class Environment:
    """What names mean while a node is resolved: the table's kinds and the values.

    ``values`` holds the configuration's values of both sections by name
    (names are unique across the table). A value may be any number the run
    tier reads (``Fraction``, ``int``, ``float``, ``Decimal``, a number
    string); it is read with ``exact_input``.
    """

    kinds: Mapping[str, Kind]
    values: Mapping[str, object] = field(default_factory=dict)

    def kind(self, name: str, path: str) -> Kind:
        """Return a parameter's kind, refusing a name the table does not declare."""
        kind = self.kinds.get(name)
        if kind is None:
            raise DocumentError(
                f"{name!r} is not a parameter of this document's table "
                f"({sorted(self.kinds)})",
                reason=DocumentReason.UNKNOWN_PARAMETER_REFERENCE,
                path=path,
            )
        return kind

    def number(self, name: str, port: str | None, path: str) -> Fraction:
        """Return a numeric parameter's value (or one port's) as an exact rational."""
        _check_numeric(name, port, self.kind(name, path), path)
        value = self._value(name, path)
        if port is not None:
            if not isinstance(value, Mapping) or port not in value:
                raise DocumentError(
                    f"{name} has no entry for port {port!r}",
                    reason=DocumentReason.UNKNOWN_PARAMETER_REFERENCE,
                    path=path,
                )
            value = value[port]
        return exact_input(cast(NumericInput, value))

    def choice(self, name: str, path: str) -> str:
        """Return a ``choice`` parameter's value."""
        if self.kind(name, path) is not Kind.CHOICE:
            raise DocumentError(
                f"a switch chooses by a choice parameter; {name} is a "
                f"{self.kinds[name]} parameter",
                reason=DocumentReason.VALUE_KIND_MISMATCH,
                path=path,
            )
        return str(self._value(name, path))

    def _value(self, name: str, path: str) -> object:
        value = self.values.get(name)
        if value is None:
            raise ParameterAbsentError(
                f"{name} has no value in this configuration",
                reason=DocumentReason.UNKNOWN_PARAMETER_REFERENCE,
                path=path,
            )
        return value


def _check_numeric(name: str, port: str | None, kind: Kind, path: str) -> None:
    """Refuse a name used in arithmetic that is not a number of the right shape."""
    if kind is Kind.CHOICE:
        raise DocumentError(
            f"{name} is a choice parameter, a name and not a number",
            reason=DocumentReason.VALUE_KIND_MISMATCH,
            path=path,
        )
    if kind is Kind.PER_PORT_FRACTION and port is None:
        raise DocumentError(
            f"{name} has one value per port; write {name}[port]",
            reason=DocumentReason.VALUE_KIND_MISMATCH,
            path=path,
        )
    if kind is not Kind.PER_PORT_FRACTION and port is not None:
        raise DocumentError(
            f"{name} is one number, not one per port",
            reason=DocumentReason.VALUE_KIND_MISMATCH,
            path=path,
        )


# ---------------------------------------------------------------------------
#  The closed exact arithmetic
# ---------------------------------------------------------------------------

_TOKEN = re.compile(
    r"[ \t\n\r]*(?:"
    r"(?P<number>(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?)"
    r"|(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    r"|(?P<label>\[[^\[\]]*\])"
    r"|(?P<op>[-+*/^()])"
    r")"
)


@dataclass(frozen=True)
class _Number:
    value: Fraction


@dataclass(frozen=True)
class _Name:
    name: str
    port: str | None


@dataclass(frozen=True)
class _Negate:
    operand: _Node


@dataclass(frozen=True)
class _Binary:
    operator: str
    left: _Node
    right: _Node


@dataclass(frozen=True)
class _Power:
    base: _Node
    exponent: int


type _Node = _Number | _Name | _Negate | _Binary | _Power


class _Syntax(Exception):
    """An expression that does not parse; the message says where."""


@dataclass(frozen=True)
class Expression:
    """A parsed expression: its text, its tree, and the names it reads."""

    text: str
    tree: _Node

    def names(self) -> tuple[tuple[str, str | None], ...]:
        """Return each ``(name, port)`` the expression reads, in reading order."""
        found: list[tuple[str, str | None]] = []

        def visit(node: _Node) -> None:
            if isinstance(node, _Name):
                found.append((node.name, node.port))
            elif isinstance(node, _Negate):
                visit(node.operand)
            elif isinstance(node, _Binary):
                visit(node.left)
                visit(node.right)
            elif isinstance(node, _Power):
                visit(node.base)

        visit(self.tree)
        return tuple(found)

    def check(self, kinds: Mapping[str, Kind], path: str) -> None:
        """Refuse a name the table lacks or one that is not a number of this shape."""
        environment = Environment(kinds)
        for name, port in self.names():
            _check_numeric(name, port, environment.kind(name, path), path)

    def evaluate(self, environment: Environment, path: str) -> Fraction:
        """Return the expression's exact value under ``environment``."""
        return _evaluate(self.tree, environment, path, self.text)


def parse_expression(text: str, path: str) -> Expression:
    """Parse ``text`` by the grammar above, refusing ``expression_invalid``."""
    try:
        return _parse_cached(text)
    except _Syntax as failure:
        raise DocumentError(
            f"the expression {text!r} does not parse: {failure}",
            reason=DocumentReason.EXPRESSION_INVALID,
            path=path,
        ) from None


@lru_cache(maxsize=4096)
def _parse_cached(text: str) -> Expression:
    if len(text) > MAX_EXPRESSION_LENGTH:
        raise _Syntax(f"it is longer than {MAX_EXPRESSION_LENGTH} characters")
    tokens = _tokenize(text)
    if len(tokens) > MAX_TOKENS:
        raise _Syntax(f"it has more than {MAX_TOKENS} tokens")
    parser = _Parser(tokens)
    tree = parser.sum()
    if parser.position != len(tokens):
        raise _Syntax(f"unexpected {tokens[parser.position][1]!r}")
    return Expression(text, tree)


def _tokenize(text: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    position = 0
    stripped = text.rstrip()
    while position < len(stripped):
        match = _TOKEN.match(stripped, position)
        if match is None or match.end() == position:
            raise _Syntax(f"unreadable at character {position + 1}")
        kind = match.lastgroup
        assert kind is not None
        tokens.append((kind, match.group(kind)))
        position = match.end()
    if not tokens:
        raise _Syntax("it is empty")
    return tokens


class _Parser:
    """Recursive descent over the token list; one method per grammar rule."""

    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.position = 0
        self.depth = 0

    def _deeper(self) -> None:
        self.depth += 1
        if self.depth > MAX_NESTING:
            raise _Syntax(f"it nests deeper than {MAX_NESTING}")

    def _peek(self) -> tuple[str, str] | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def _take(self) -> tuple[str, str]:
        token = self._peek()
        if token is None:
            raise _Syntax("it ends early")
        self.position += 1
        return token

    def _at(self, operator: str) -> bool:
        token = self._peek()
        return token is not None and token == ("op", operator)

    def sum(self) -> _Node:
        node = self.term()
        while self._at("+") or self._at("-"):
            operator = self._take()[1]
            node = _Binary(operator, node, self.term())
        return node

    def term(self) -> _Node:
        node = self.unary()
        while self._at("*") or self._at("/"):
            operator = self._take()[1]
            node = _Binary(operator, node, self.unary())
        return node

    def unary(self) -> _Node:
        if self._at("-"):
            self._take()
            self._deeper()
            node = _Negate(self.unary())
            self.depth -= 1
            return node
        return self.power()

    def power(self) -> _Node:
        base = self.atom()
        if not self._at("^"):
            return base
        self._take()
        negative = self._at("-")
        if negative:
            self._take()
        kind, text = self._take()
        if kind != "number" or not re.fullmatch("[0-9]+", text):
            raise _Syntax(f"an exponent is an integer; got {text!r}")
        exponent = int(text)
        if exponent > MAX_EXPONENT:
            raise _Syntax(f"an exponent is at most {MAX_EXPONENT}")
        return _Power(base, -exponent if negative else exponent)

    def atom(self) -> _Node:
        kind, text = self._take()
        if kind == "number":
            _mantissa, _e, exponent = text.lower().partition("e")
            if exponent and abs(int(exponent)) > MAX_EXPONENT:
                raise _Syntax(f"a decimal exponent is at most {MAX_EXPONENT}")
            return _Number(Fraction(text))
        if kind == "name":
            token = self._peek()
            if token is not None and token[0] == "label":
                self._take()
                return _Name(text, token[1][1:-1].strip())
            return _Name(text, None)
        if (kind, text) == ("op", "("):
            self._deeper()
            node = self.sum()
            if not self._at(")"):
                raise _Syntax("a parenthesis is not closed")
            self._take()
            self.depth -= 1
            return node
        raise _Syntax(f"unexpected {text!r}")


def _evaluate(node: _Node, environment: Environment, path: str, text: str) -> Fraction:
    return _bounded(_compute(node, environment, path, text), text, path)


def _bits(value: Fraction) -> int:
    return max(abs(value.numerator).bit_length(), value.denominator.bit_length())


def _bounded(value: Fraction, text: str, path: str) -> Fraction:
    if _bits(value) > MAX_BITS:
        raise _too_large(text, path)
    return value


def _too_large(text: str, path: str) -> DocumentError:
    return DocumentError(
        f"the expression {text!r} has a value beyond {MAX_BITS} bits",
        reason=DocumentReason.EXPRESSION_INVALID,
        path=path,
    )


def _compute(node: _Node, environment: Environment, path: str, text: str) -> Fraction:
    if isinstance(node, _Number):
        return node.value
    if isinstance(node, _Name):
        return environment.number(node.name, node.port, path)
    if isinstance(node, _Negate):
        return -_evaluate(node.operand, environment, path, text)
    if isinstance(node, _Power):
        base = _evaluate(node.base, environment, path, text)
        if base == 0 and node.exponent < 0:
            raise _division_by_zero(text, path)
        if abs(node.exponent) * _bits(base) > MAX_BITS:
            raise _too_large(text, path)
        return base**node.exponent
    left = _evaluate(node.left, environment, path, text)
    right = _evaluate(node.right, environment, path, text)
    if node.operator == "+":
        return left + right
    if node.operator == "-":
        return left - right
    if node.operator == "*":
        return left * right
    if right == 0:
        raise _division_by_zero(text, path)
    return left / right


def _division_by_zero(text: str, path: str) -> DocumentError:
    return DocumentError(
        f"the expression {text!r} divides by zero",
        reason=DocumentReason.EXPRESSION_DIVISION_BY_ZERO,
        path=path,
    )


def constant(node: int | str, path: str) -> Fraction:
    """Return a number written as an integer or a string: an expression of no name.

    Every number string of a document is read here, so there is one number
    grammar: ``"1/3"``, ``"0.02"``, ``"1e-3"`` and ``"2^-30"`` alike. A string
    that reads a parameter is refused; that is written ``{expr: ...}``.
    """
    if isinstance(node, int):
        return Fraction(node)
    expression = parse_expression(node, path)
    names = sorted({name for name, _port in expression.names()})
    if names:
        raise DocumentError(
            f"{node!r} reads {names}; a number string is a constant, and an "
            "expression over parameters is written {expr: ...}",
            reason=DocumentReason.UNKNOWN_PARAMETER_REFERENCE,
            path=path,
        )
    return expression.evaluate(Environment({}), path)


def evaluate_exact(node: int | str, environment: Environment, path: str) -> Fraction:
    """Return an :data:`~instances.declared.model.Exact` field's value."""
    if isinstance(node, int):
        return Fraction(node)
    return parse_expression(node, path).evaluate(environment, path)


def evaluate_int(node: int | str, environment: Environment, path: str) -> int:
    """Return an :data:`~instances.declared.model.Exact` field that is an integer."""
    value = evaluate_exact(node, environment, path)
    if value.denominator != 1:
        raise DocumentError(
            f"an integer is required here; {node!r} is {value}",
            reason=DocumentReason.EXPRESSION_NOT_INTEGRAL,
            path=path,
        )
    return int(value)


# ---------------------------------------------------------------------------
#  Scalars, switches and matrices
# ---------------------------------------------------------------------------


def choose(node: Switch[Any], environment: Environment, path: str) -> tuple[Any, str]:
    """Return the case ``node`` chooses under ``environment``, and its path."""
    value = environment.choice(node.switch, pointer_join(path, "switch"))
    if value in node.cases:
        return node.cases[value], pointer_join(path, "cases", value)
    if node.default is not None:
        return node.default, pointer_join(path, "default")
    raise DocumentError(
        f"the switch over {node.switch} has no case {value!r} and no default "
        f"(cases: {sorted(node.cases)})",
        reason=DocumentReason.SWITCH_CASE_MISSING,
        path=path,
    )


def unwrap(node: Any, environment: Environment, path: str) -> tuple[Any, str]:
    """Resolve switches until a node that is not one; return it and its path."""
    while isinstance(node, Switch):
        node, path = choose(node, environment, path)
    return node, path


def number(node: object, environment: Environment, path: str) -> int | Fraction:
    """Return a value-language scalar: an ``int`` where written as one, else exact.

    A JSON integer stays a Python ``int``, because records serialise ``0`` and
    ``Fraction(0)`` differently and some fields are read as written (the
    catalogue scalars). Everything else is a ``Fraction``.
    """
    node, path = unwrap(node, environment, path)
    if isinstance(node, bool):
        raise DocumentError(
            "a Boolean is not a number",
            reason=DocumentReason.VALUE_KIND_MISMATCH,
            path=path,
        )
    if isinstance(node, int):
        return node
    if isinstance(node, str):
        return constant(node, path)
    if isinstance(node, ParamRef):
        return environment.number(node.param, node.port, path)
    if isinstance(node, Expr):
        return parse_expression(node.expr, path).evaluate(environment, path)
    raise DocumentError(
        f"a number is expected here, not {type(node).__name__}",
        reason=DocumentReason.VALUE_KIND_MISMATCH,
        path=path,
    )


def _entry(node: object, environment: Environment, path: str) -> exact.Cx:
    if isinstance(node, tuple):
        real = Fraction(number(node[0], environment, pointer_join(path, 0)))
        imaginary = Fraction(number(node[1], environment, pointer_join(path, 1)))
        return exact.Cx(real, imaginary)
    return exact.as_scalar(number(node, environment, path))


def matrix(node: object, environment: Environment, path: str) -> exact.Matrix:
    """Return a matrix node as an exact matrix; ``matrix_malformed`` if unreadable."""
    node, path = unwrap(node, environment, path)
    try:
        if isinstance(node, MatrixRows):
            return exact.matrix(
                [
                    [
                        _entry(entry, environment, pointer_join(path, "matrix", i, j))
                        for j, entry in enumerate(row)
                    ]
                    for i, row in enumerate(node.matrix)
                ]
            )
        if isinstance(node, Outer):
            vector = exact.vector(
                [
                    _entry(entry, environment, pointer_join(path, "outer", "vector", i))
                    for i, entry in enumerate(node.outer.vector)
                ]
            )
            norm = Fraction(
                number(
                    node.outer.squared_norm,
                    environment,
                    pointer_join(path, "outer", "squared_norm"),
                )
            )
            return exact.outer_projector(vector, norm)
        if isinstance(node, IdentityMatrix):
            if node.identity < 1:
                raise MalformedInputError("an identity has dimension at least one")
            return exact.identity(node.identity)
        if isinstance(node, Scale):
            factor = _entry(
                node.scale.factor, environment, pointer_join(path, "scale", "factor")
            )
            return exact.scale(
                factor,
                matrix(node.scale.of, environment, pointer_join(path, "scale", "of")),
            )
    except MalformedInputError as failure:
        raise DocumentError(
            str(failure), reason=DocumentReason.MATRIX_MALFORMED, path=path
        ) from failure
    raise DocumentError(
        f"a matrix is expected here, not {type(node).__name__}",
        reason=DocumentReason.MATRIX_MALFORMED,
        path=path,
    )


def pointer_join(path: str, *parts: str | int) -> str:
    """Return ``path`` extended by ``parts``, as a JSON pointer."""
    return path + pointer(*parts)


# ---------------------------------------------------------------------------
#  The static reference check, made at load
# ---------------------------------------------------------------------------


def walk(node: object, path: str) -> Iterator[tuple[object, str]]:
    """Yield every model, list item and mapping value under ``node``, with its path."""
    yield node, path
    if isinstance(node, BaseModel):
        for name, info in type(node).model_fields.items():
            value = getattr(node, name)
            if value is None:
                continue
            yield from walk(value, pointer_join(path, info.alias or name))
    elif isinstance(node, list | tuple):
        for index, item in enumerate(node):
            yield from walk(item, pointer_join(path, index))
    elif isinstance(node, dict):
        for key, item in node.items():
            yield from walk(item, pointer_join(path, key))


def check_references(
    node: object,
    kinds: Mapping[str, Kind],
    path: str = "",
    *,
    options: Mapping[str, Sequence[str]] | None = None,
) -> None:
    """Refuse each ``param``, ``expr`` and ``switch`` under ``node`` not resolving.

    Names must be parameters of the table and of the kind their position needs:
    a number in arithmetic and ``param``, a ``choice`` in a ``switch``. Given
    ``options`` (each choice parameter's values), a switch case must be one of
    them, so that a misspelt case is not silently never chosen. Run
    once at load, so that a document that names a parameter it does not
    declare fails before any configuration is read. The opaque slots
    (``annotations``, an honest note) hold plain JSON and no value node, so
    nothing in them is read.
    """
    environment = Environment(kinds)
    for item, where in walk(node, path):
        if isinstance(item, ParamRef):
            _check_numeric(
                item.param, item.port, environment.kind(item.param, where), where
            )
        elif isinstance(item, Expr):
            parse_expression(item.expr, where).check(kinds, where)
        elif isinstance(item, Switch):
            name_path = pointer_join(where, "switch")
            if environment.kind(item.switch, name_path) is not Kind.CHOICE:
                raise DocumentError(
                    f"a switch chooses by a choice parameter; {item.switch} is a "
                    f"{kinds[item.switch]} parameter",
                    reason=DocumentReason.VALUE_KIND_MISMATCH,
                    path=name_path,
                )
            admitted = (options or {}).get(item.switch)
            for case in item.cases:
                if admitted is not None and case not in admitted:
                    raise DocumentError(
                        f"the case {case!r} is not a value of {item.switch} "
                        f"({list(admitted)})",
                        reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                        path=pointer_join(where, "cases", case),
                    )
