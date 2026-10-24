"""The value language: scalars, references, arithmetic, switches, matrices.

Each refusal is checked by its code, never by its message. The arithmetic is
``Fraction`` throughout, so ``0.1 + 0.2`` is exactly ``3/10``; a JSON integer
stays a Python ``int`` where a scalar is read, because records serialise ``0``
and ``Fraction(0)`` differently.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest
from instances.declared import DocumentError, DocumentReason
from instances.declared.model import Matrix, ParamRef, Scalar, Switch
from instances.declared.values import (
    Environment,
    ParameterAbsentError,
    check_references,
    evaluate_exact,
    evaluate_int,
    matrix,
    number,
    parse_expression,
)
from pydantic import TypeAdapter

from certiqs_key.foundations import exact
from certiqs_key.runs.surface import Kind

KINDS = {
    "photon_cutoff": Kind.INT,
    "test_fraction": Kind.FRACTION,
    "route": Kind.CHOICE,
    "dark_count": Kind.PER_PORT_FRACTION,
}
VALUES: dict[str, object] = {
    "photon_cutoff": Fraction(2),
    "test_fraction": "1/8",
    "route": "licensed",
    "dark_count": {"H": Fraction(1, 10**6), "V": 0.5},
}
ENV = Environment(KINDS, VALUES)


def _scalar(node: object) -> Any:
    return TypeAdapter(Scalar).validate_python(node)


def _matrix(node: object) -> Any:
    return TypeAdapter(Matrix).validate_python(node)


def _code(call: Any) -> DocumentReason:
    with pytest.raises(DocumentError) as caught:
        call()
    return caught.value.reason


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("1 + 2 * 3", Fraction(7)),
        ("(1 + 2) * 3", Fraction(9)),
        ("2^-30", Fraction(1, 2**30)),
        ("-2^2", Fraction(-4)),
        ("2^3^1", None),
        ("1/3 + 1/6", Fraction(1, 2)),
        ("1e-3", Fraction(1, 1000)),
        ("0.1 + 0.2", Fraction(3, 10)),
        ("--1", Fraction(1)),
        ("photon_cutoff + 1", Fraction(3)),
        ("1 - test_fraction", Fraction(7, 8)),
        ("dark_count[H] * 10^6", Fraction(1)),
        ("dark_count[ V ]", Fraction(1, 2)),
    ],
)
def test_the_arithmetic(text: str, value: Fraction | None) -> None:
    if value is None:
        assert (
            _code(lambda: parse_expression(text, ""))
            is DocumentReason.EXPRESSION_INVALID
        )
        return
    assert parse_expression(text, "").evaluate(ENV, "") == value


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("1 +", DocumentReason.EXPRESSION_INVALID),
        ("", DocumentReason.EXPRESSION_INVALID),
        ("2^x", DocumentReason.EXPRESSION_INVALID),
        ("2^1.5", DocumentReason.EXPRESSION_INVALID),
        ("2^5000", DocumentReason.EXPRESSION_INVALID),
        ("(1 + 2", DocumentReason.EXPRESSION_INVALID),
        ("sqrt(2)", DocumentReason.EXPRESSION_INVALID),
        ("1 $ 2", DocumentReason.EXPRESSION_INVALID),
        ("1 / (2 - 2)", DocumentReason.EXPRESSION_DIVISION_BY_ZERO),
        ("0^-1", DocumentReason.EXPRESSION_DIVISION_BY_ZERO),
        ("mu + 1", DocumentReason.UNKNOWN_PARAMETER_REFERENCE),
        ("route + 1", DocumentReason.VALUE_KIND_MISMATCH),
        ("dark_count + 1", DocumentReason.VALUE_KIND_MISMATCH),
        ("photon_cutoff[H]", DocumentReason.VALUE_KIND_MISMATCH),
        ("dark_count[D]", DocumentReason.UNKNOWN_PARAMETER_REFERENCE),
    ],
)
def test_what_the_arithmetic_refuses(text: str, reason: DocumentReason) -> None:
    assert _code(lambda: parse_expression(text, "/x").evaluate(ENV, "/x")) is reason


def test_names_are_checked_without_a_configuration() -> None:
    expression = parse_expression("dark_count[H] + photon_cutoff", "")
    assert expression.names() == (("dark_count", "H"), ("photon_cutoff", None))
    expression.check(KINDS, "")
    assert (
        _code(lambda: parse_expression("route * 2", "").check(KINDS, ""))
        is DocumentReason.VALUE_KIND_MISMATCH
    )


def test_an_absent_value_is_its_own_refusal() -> None:
    environment = Environment(KINDS, {"photon_cutoff": None})
    with pytest.raises(ParameterAbsentError):
        parse_expression("photon_cutoff + 1", "").evaluate(environment, "")


def test_integers_where_required() -> None:
    assert evaluate_int("2^3 - 1", ENV, "") == 7
    assert evaluate_int(5, ENV, "") == 5
    assert evaluate_exact(5, ENV, "") == Fraction(5)
    assert (
        _code(lambda: evaluate_int("7/2", ENV, ""))
        is DocumentReason.EXPRESSION_NOT_INTEGRAL
    )


def test_scalars() -> None:
    assert number(_scalar(0), ENV, "") == 0
    assert type(number(_scalar(0), ENV, "")) is int
    assert number(_scalar("0.02"), ENV, "") == Fraction(1, 50)
    assert number(_scalar("-1/2"), ENV, "") == Fraction(-1, 2)
    assert number(_scalar({"param": "test_fraction"}), ENV, "") == Fraction(1, 8)
    assert number(_scalar({"param": "dark_count", "port": "V"}), ENV, "") == Fraction(
        1, 2
    )
    assert number(_scalar({"expr": "photon_cutoff * 2"}), ENV, "") == Fraction(4)
    assert (
        _code(lambda: number(_scalar("1 - test_fraction"), ENV, ""))
        is DocumentReason.UNKNOWN_PARAMETER_REFERENCE
    )
    assert number(_scalar("2^-30"), ENV, "") == Fraction(1, 2**30)
    assert _code(lambda: number(_scalar("1/0"), ENV, "")) is (
        DocumentReason.EXPRESSION_DIVISION_BY_ZERO
    )
    assert _code(lambda: number(_scalar("1/2/"), ENV, "")) is (
        DocumentReason.EXPRESSION_INVALID
    )
    assert _code(lambda: number(True, ENV, "")) is DocumentReason.VALUE_KIND_MISMATCH
    assert (
        _code(lambda: number(_scalar({"param": "route"}), ENV, ""))
        is DocumentReason.VALUE_KIND_MISMATCH
    )


def test_a_switch_chooses_by_a_choice_parameter() -> None:
    node = _scalar(
        {"switch": "route", "cases": {"encoded": 1, "licensed": {"expr": "1/2"}}}
    )
    assert number(node, ENV, "") == Fraction(1, 2)
    defaulted = _scalar({"switch": "route", "cases": {"encoded": 1}, "default": 3})
    assert number(defaulted, ENV, "") == 3
    missing = _scalar({"switch": "route", "cases": {"encoded": 1}})
    error_reason = _code(lambda: number(missing, ENV, "/a"))
    assert error_reason is DocumentReason.SWITCH_CASE_MISSING
    nested = _scalar(
        {
            "switch": "route",
            "cases": {"licensed": {"switch": "route", "cases": {"licensed": 9}}},
        }
    )
    assert number(nested, ENV, "") == 9
    over_a_number = _scalar({"switch": "photon_cutoff", "cases": {"2": 1}})
    assert (
        _code(lambda: number(over_a_number, ENV, ""))
        is DocumentReason.VALUE_KIND_MISMATCH
    )


def test_matrices() -> None:
    rows = _matrix({"matrix": [[1, "1/2"], ["1/2", [0, "-1/4"]]]})
    built = matrix(rows, ENV, "")
    assert built[0][1] == exact.Cx(Fraction(1, 2), Fraction(0))
    assert built[1][1] == exact.Cx(Fraction(0), Fraction(-1, 4))
    serialized = exact.serialize_matrix(built)
    assert matrix(_matrix({"matrix": serialized}), ENV, "") == built
    phi = matrix(
        _matrix({"outer": {"vector": [1, 0, 0, 1], "squared_norm": 2}}), ENV, ""
    )
    assert phi[0][3] == exact.Cx(Fraction(1, 2), Fraction(0))
    assert matrix(_matrix({"identity": 2}), ENV, "") == exact.identity(2)
    half = matrix(_matrix({"scale": {"factor": "1/2", "of": {"identity": 2}}}), ENV, "")
    assert half == exact.scale(Fraction(1, 2), exact.identity(2))
    switched = _matrix({"switch": "route", "cases": {"licensed": {"identity": 1}}})
    assert matrix(switched, ENV, "") == exact.identity(1)
    weighted = _matrix({"matrix": [[{"param": "test_fraction"}]]})
    assert matrix(weighted, ENV, "")[0][0] == exact.Cx(Fraction(1, 8), Fraction(0))


@pytest.mark.parametrize(
    "node",
    [
        {"matrix": [[1, 0], [0]]},
        {"matrix": []},
        {"outer": {"vector": [1, 1], "squared_norm": 3}},
        {"identity": 0},
    ],
)
def test_an_unreadable_matrix_is_malformed(node: object) -> None:
    assert (
        _code(lambda: matrix(_matrix(node), ENV, "/m"))
        is DocumentReason.MATRIX_MALFORMED
    )


def test_a_matrix_is_not_judged() -> None:
    """Hermiticity and positivity are the modules' decision, not the reader's."""
    built = matrix(_matrix({"matrix": [[0, 1], [2, -5]]}), ENV, "")
    assert built[1][0] == exact.Cx(Fraction(2), Fraction(0))


def test_the_static_reference_check() -> None:
    check_references([ParamRef(param="test_fraction")], KINDS)
    for node, reason in (
        (ParamRef(param="nope"), DocumentReason.UNKNOWN_PARAMETER_REFERENCE),
        (ParamRef(param="route"), DocumentReason.VALUE_KIND_MISMATCH),
        (ParamRef(param="dark_count"), DocumentReason.VALUE_KIND_MISMATCH),
        (_scalar({"expr": "1 +"}), DocumentReason.EXPRESSION_INVALID),
        (
            Switch[Any](switch="test_fraction", cases={}),
            DocumentReason.VALUE_KIND_MISMATCH,
        ),
        (
            Switch[Any](switch="nope", cases={}),
            DocumentReason.UNKNOWN_PARAMETER_REFERENCE,
        ),
    ):
        with pytest.raises(DocumentError) as caught:
            check_references({"a": [node]}, KINDS, "/root")
        assert caught.value.reason is reason
        assert caught.value.path.startswith("/root/a/0")


# ---------------------------------------------------------------------------
#  The trust boundary: bounded parsing and evaluation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "(" * 5000 + "1" + ")" * 5000,
        "-" * 5000 + "1",
        "(" * 40 + "1" + ")" * 40,
        "-" * 40 + "1",
        "+".join(["1"] * 300),
        "1" * 2000,
        "1e10000000",
        "1e-5000",
        "((2^4096)^4096)^4096",
        "(2^4096)^17",
        "2^4096 * 2^4096 * 2^4096 * 2^4096 * 2^4096 * 2^4096 * 2^4096 * 2^4096"
        " * 2^4096 * 2^4096 * 2^4096 * 2^4096 * 2^4096 * 2^4096 * 2^4096 * 2^4096"
        " * 2^4096",
        "\u0661 + 1",
    ],
    ids=[
        "deep-parens",
        "deep-minus",
        "parens-41",
        "minus-41",
        "many-tokens",
        "long",
        "huge-exponent-literal",
        "tiny-exponent-literal",
        "power-tower",
        "power-of-big",
        "product-of-big",
        "unicode-digit",
    ],
)
def test_a_hostile_expression_is_refused_cheaply(text: str) -> None:
    """No input reaches a RecursionError or an unbounded computation."""
    import time

    started = time.perf_counter()
    reason = _code(lambda: parse_expression(text, "/x").evaluate(ENV, "/x"))
    assert reason is DocumentReason.EXPRESSION_INVALID
    assert time.perf_counter() - started < 1


def test_the_bounds_admit_what_a_document_needs() -> None:
    assert parse_expression("2^-1074", "").evaluate(ENV, "") == Fraction(1, 2**1074)
    assert parse_expression("1e-4096 * 1e4096", "").evaluate(ENV, "") == 1
    nested = "(" * 30 + "1" + ")" * 30
    assert parse_expression(nested, "").evaluate(ENV, "") == 1


def test_a_switch_case_must_be_a_value_of_its_choice() -> None:
    options = {"route": ("encoded", "licensed")}
    good = _scalar({"switch": "route", "cases": {"encoded": 1, "licensed": 2}})
    check_references([good], KINDS, options=options)
    typo = _scalar({"switch": "route", "cases": {"encoded": 1, "licenced": 2}})
    with pytest.raises(DocumentError) as caught:
        check_references([typo], KINDS, "/r", options=options)
    assert caught.value.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION
    assert caught.value.path == "/r/0/cases/licenced"
