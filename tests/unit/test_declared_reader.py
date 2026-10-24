"""The reader: one canonical tree on every route, its digest, and what it refuses.

A document read from YAML text, JSON
text or a parsed object becomes one tree of integers, strings, booleans, nulls,
lists and objects; non-integer numbers in text keep their source text, floats
in an object become their exact rational with a recorded conversion, and the
YAML reader knows only ``true``/``false`` and decimal integers. The tree and its
conversions reload through ``load_canonical`` to the same surface (the
prepare-versus-worker test; the run facade tests repeat it end to end).
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
import yaml
from instances.declared import DocumentError, DocumentReason, load, load_canonical
from instances.declared.reader import (
    MAX_DEPTH,
    MAX_NODES,
    MAX_TEXT_LENGTH,
    canonicalize,
    digest,
    parse_text,
    read,
    read_canonical,
    read_packaged,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "declared"
CUSTOM = FIXTURES / "custom_qubit_bb84.yaml"


def _custom() -> dict[str, Any]:
    tree, _ = canonicalize(parse_text(CUSTOM.read_text(encoding="utf-8")))
    return tree


def _refused(reason: DocumentReason, source: object, **kwargs: Any) -> DocumentError:
    with pytest.raises(DocumentError) as caught:
        read(source, **kwargs)
    assert caught.value.reason is reason, caught.value
    return caught.value


# ---------------------------------------------------------------------------
#  YAML and JSON text
# ---------------------------------------------------------------------------


def test_yaml_keeps_words_decimals_and_spellings_as_text() -> None:
    parsed = parse_text(
        "a: off\nb: on\nc: yes\nd: true\ne: 0.02\nf: 1e-3\ng: 0x10\nh: 010\n"
        "i: 1:30\nj: 2026-10-06\nk: .inf\nl: ~\nm: -7\nn: !!float 1.50\n"
    )
    assert parsed == {
        "a": "off",
        "b": "on",
        "c": "yes",
        "d": True,
        "e": "0.02",
        "f": "1e-3",
        "g": "0x10",
        "h": 10,
        "i": "1:30",
        "j": "2026-10-06",
        "k": ".inf",
        "l": None,
        "m": -7,
        "n": "1.50",
    }


def test_yaml_keys_are_their_source_text() -> None:
    assert parse_text("1: a\noff: b\n0.5: c\n") == {"1": "a", "off": "b", "0.5": "c"}


@pytest.mark.parametrize(
    "text", ["a: 1\na: 2\n", '{"a": 1, "a": 2}', "x: {a: 1, a: 2}\n"]
)
def test_a_repeated_key_is_refused(text: str) -> None:
    with pytest.raises(DocumentError) as caught:
        parse_text(text)
    assert caught.value.reason is DocumentReason.DOCUMENT_UNREADABLE


def test_json_keeps_decimals_as_text_and_refuses_constants() -> None:
    assert parse_text('{"a": 0.10, "b": 3, "c": 1E-3}') == {
        "a": "0.10",
        "b": 3,
        "c": "1E-3",
    }
    with pytest.raises(DocumentError):
        parse_text('{"a": NaN}', syntax="json")


def test_a_yaml_flow_mapping_document_is_read_as_yaml() -> None:
    """Guessed, text beginning with ``{`` falls back to YAML when it is not JSON."""
    assert parse_text("{a: 0.5, b: off}") == {"a": "0.5", "b": "off"}


def test_unparseable_text_is_unreadable() -> None:
    _refused(DocumentReason.DOCUMENT_UNREADABLE, "a: [1, 2\n")
    _refused(DocumentReason.DOCUMENT_UNREADABLE, "- just\n- a list\n")
    _refused(DocumentReason.DOCUMENT_UNREADABLE, "a: 1\n---\nb: 2\n")


def test_a_file_is_read_by_its_suffix(tmp_path: Path) -> None:
    tree = _custom()
    json_file = tmp_path / "document.json"
    json_file.write_text(json.dumps(tree), encoding="utf-8")
    assert read(json_file).canonical == tree
    other = tmp_path / "document.txt"
    other.write_text("{}", encoding="utf-8")
    _refused(DocumentReason.DOCUMENT_UNREADABLE, other)


# ---------------------------------------------------------------------------
#  The canonical tree
# ---------------------------------------------------------------------------


def test_text_routes_give_one_tree_and_one_digest() -> None:
    """YAML text, JSON text of the same tree, and the tree itself agree."""
    from_yaml = read(CUSTOM)
    from_json = read(json.dumps(from_yaml.canonical))
    from_object = read(from_yaml.canonical)
    assert from_yaml.canonical == from_json.canonical == from_object.canonical
    assert from_yaml.digest == from_json.digest == from_object.digest
    assert from_yaml.conversions == ()
    assert from_yaml.canonical["parameters"]["table"][1]["default"] == "0.5"
    assert from_yaml.digest == digest(from_yaml.canonical)


def test_an_object_float_becomes_its_exact_value_with_a_record() -> None:
    tree = _custom()
    tree["parameters"]["table"][1]["default"] = 0.5
    tree["parameters"]["table"][2]["default"] = 0.1
    document = read(tree)
    table = document.canonical["parameters"]["table"]
    assert table[1]["default"] == "1/2"
    assert table[2]["default"] == str(Fraction(0.1))
    assert [record["path"] for record in document.conversions] == [
        "/parameters/table/1/default",
        "/parameters/table/2/default",
    ]
    tenth = document.conversions[1]
    # runs.inputs' meaning: the input IS the float's exact value, so nothing moved.
    assert tenth == {
        "site": "document:/parameters/table/2/default",
        "path": "/parameters/table/2/default",
        "rule": "numeric_input_conversion",
        "input_type": "float",
        "input_value": str(Fraction(0.1)),
        "prepared_value": str(Fraction(0.1)),
        "total_displacement": "0",
        "written": "0.1",
    }


def test_python_exact_numbers_are_kept_exactly() -> None:
    from decimal import Decimal

    tree, conversions = canonicalize(
        {"a": Fraction(1, 3), "b": Decimal("0.25"), "c": (1, 2)}
    )
    assert tree == {"a": "1/3", "b": "0.25", "c": [1, 2]}
    assert conversions == ()


@pytest.mark.parametrize(
    "value", [{1: "a"}, {"a": float("inf")}, {"a": {1, 2}}, {"a": b"bytes"}]
)
def test_what_is_not_json_is_unreadable(value: object) -> None:
    with pytest.raises(DocumentError) as caught:
        canonicalize(value)
    assert caught.value.reason is DocumentReason.DOCUMENT_UNREADABLE


def test_the_stored_tree_reloads_to_the_same_surface() -> None:
    """What ``prepare`` reads, the worker reads."""
    for source in (CUSTOM, _object_with_floats()):
        surface = load(source)
        stored = json.loads(
            json.dumps(
                {
                    "document": surface.canonical,
                    "conversions": list(surface.conversions),
                }
            )
        )
        again = load_canonical(stored["document"], stored["conversions"])
        assert again.canonical == surface.canonical
        assert again.digest == surface.digest
        assert again.conversions == surface.conversions
        payload = surface.default_config().to_payload()
        assert again.default_config().to_payload() == payload
        # the document's conversions reach input_preparation.
        recorded = payload.get("input_preparation", [])
        assert recorded[: len(surface.conversions)] == list(surface.conversions)
        assert len(surface.conversions) == (3 if isinstance(source, dict) else 0)
        twice = surface.default_config(input_preparation=surface.conversions)
        assert twice.to_payload() == payload
        assert [p.as_payload() for p in again.PARAMETERS] == [
            p.as_payload() for p in surface.PARAMETERS
        ]


def _object_with_floats() -> dict[str, Any]:
    tree = yaml.safe_load(CUSTOM.read_text(encoding="utf-8"))
    assert isinstance(tree["parameters"]["table"][1]["default"], float)
    return tree


def test_a_stored_tree_holding_a_float_is_refused() -> None:
    tree = _custom()
    tree["parameters"]["table"][1]["default"] = 0.5
    with pytest.raises(DocumentError) as caught:
        read_canonical(tree)
    assert caught.value.reason is DocumentReason.DOCUMENT_UNREADABLE
    assert caught.value.path == "/parameters/table/1/default"


# ---------------------------------------------------------------------------
#  Format, version and schema
# ---------------------------------------------------------------------------


def test_format_and_version() -> None:
    tree = _custom()
    tree["format_version"] = 1
    as_int = read(tree)
    assert as_int.canonical["format_version"] == "1"
    assert as_int.digest == read(_custom()).digest
    tree["format_version"] = "2"
    error = _refused(DocumentReason.FORMAT_VERSION_UNSUPPORTED, tree)
    assert error.path == "/format_version"
    tree = _custom()
    tree["format"] = "something-else"
    assert _refused(DocumentReason.DOCUMENT_SCHEMA_VIOLATION, tree).path == "/format"


def test_a_schema_violation_names_its_path() -> None:
    tree = _custom()
    tree["parameters"]["table"][0]["meening"] = "typo"
    error = _refused(DocumentReason.DOCUMENT_SCHEMA_VIOLATION, tree)
    assert error.path == "/parameters/table/0/meening"
    tree = _custom()
    tree["stations"][0]["measurement"]["dimension"] = "two"
    error = _refused(DocumentReason.DOCUMENT_SCHEMA_VIOLATION, tree)
    assert error.path == "/stations/0/measurement/dimension"
    tree = _custom()
    del tree["public"]
    assert _refused(DocumentReason.DOCUMENT_SCHEMA_VIOLATION, tree).path == ""


def test_a_static_read_ignores_the_unread_blocks_but_not_unknown_keys() -> None:
    tree = _custom()
    tree["source"] = {"anything": "goes"}
    assert read(tree, static=True).model.identity.id == "custom_qubit_bb84"
    tree["sauce"] = {}
    _refused(DocumentReason.DOCUMENT_SCHEMA_VIOLATION, tree, static=True)


# ---------------------------------------------------------------------------
#  Reserved identities
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("edit", "path"),
    [
        (lambda t: t["identity"].update(id="bb84"), "/identity/id"),
        (
            lambda t: t["identity"].update(record_label="declared.other"),
            "/identity/record_label",
        ),
        (
            lambda t: t["identity"].update(record_label="instances.bb84"),
            "/identity/record_label",
        ),
        (
            lambda t: t["stations"][0].update(declared_by="instances.bb84.bob"),
            "/stations/0/declared_by",
        ),
        (
            lambda t: t["source"].update(
                retention_attestation={"attested_by": "instances.x", "statement": "s"}
            ),
            "/source/retention_attestation/attested_by",
        ),
        (
            lambda t: t["honest"].update(note={"module": "instances.bb84.honest"}),
            "/honest/note/module",
        ),
    ],
)
def test_a_custom_document_may_not_claim_a_packaged_identity(
    edit: Any, path: str
) -> None:
    tree = _custom()
    edit(tree)
    assert _refused(DocumentReason.RESERVED_IDENTITY, tree).path == path


def test_a_custom_document_names_no_readme() -> None:
    """``readme`` is a repository path a server serves; only a template's is one."""
    tree = _custom()
    tree["identity"]["readme"] = "../../../../Windows/win.ini"
    error = _refused(DocumentReason.RESERVED_IDENTITY, tree)
    assert error.path == "/identity/readme"


def test_one_refusal_names_every_reserved_place() -> None:
    """A copied template's reserved strings are cleared in one round."""
    tree = _custom()
    tree["identity"]["readme"] = "instances/bb84/README.md"
    tree["stations"][0]["declared_by"] = "instances.bb84.bob"
    tree["source"]["retention_attestation"] = {
        "attested_by": "instances.x",
        "statement": "s",
    }
    error = _refused(DocumentReason.RESERVED_IDENTITY, tree)
    assert error.path == "/identity/readme"
    assert (
        "; also reserved: /stations/0/declared_by, "
        "/source/retention_attestation/attested_by. "
    ) in error.detail
    # A required field is renamed, never deleted.
    assert "who attests the retention" in error.detail


def test_the_default_record_label_and_a_label_of_its_own_are_admitted() -> None:
    tree = _custom()
    tree["identity"]["record_label"] = "declared.custom_qubit_bb84"
    tree["stations"][0]["declared_by"] = "lab.bob"
    assert load(tree).record_label == "declared.custom_qubit_bb84"
    assert load(_custom()).record_label == "declared.custom_qubit_bb84"


def test_only_instances_id_protocol_yaml_is_packaged(tmp_path: Path) -> None:
    elsewhere = tmp_path / "protocol.yaml"
    elsewhere.write_text(CUSTOM.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(DocumentError) as caught:
        read_packaged(elsewhere)
    assert caught.value.reason is DocumentReason.RESERVED_IDENTITY
    assert read(elsewhere).packaged is False


# ---------------------------------------------------------------------------
#  The trust boundary: nothing exhausts the stack or memory
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        '{"a": ' + "[" * 100_000 + "]" * 100_000 + "}",
        "a: " + "[" * 5_000 + "]" * 5_000 + "\n",
        "a:\n" + "".join("  " * depth + "- \n" for depth in range(1, 3_000)),
        "a: &x [*x]\n",
        "a: &a [1, 2]\nb: *a\n",
        "x" * (MAX_TEXT_LENGTH + 1),
    ],
    ids=[
        "deep-json",
        "deep-yaml-flow",
        "deep-yaml-block",
        "alias-cycle",
        "alias",
        "long",
    ],
)
def test_hostile_text_is_unreadable(text: str) -> None:
    with pytest.raises(DocumentError) as caught:
        canonicalize(parse_text(text))
    assert caught.value.reason is DocumentReason.DOCUMENT_UNREADABLE


def test_an_alias_bomb_is_refused_before_it_expands() -> None:
    lines = ["a0: &a0 [x, x, x, x, x, x, x, x, x, x]"]
    lines += [f"a{i}: &a{i} [{', '.join([f'*a{i - 1}'] * 10)}]" for i in range(1, 9)]
    with pytest.raises(DocumentError) as caught:
        parse_text("\n".join(lines) + "\n")
    assert caught.value.reason is DocumentReason.DOCUMENT_UNREADABLE


def test_a_deep_wide_or_cyclic_object_is_unreadable() -> None:
    deep: dict[str, Any] = {}
    node = deep
    for _ in range(MAX_DEPTH + 1):
        node["a"] = {}
        node = node["a"]
    cyclic: dict[str, Any] = {}
    cyclic["self"] = cyclic
    wide = {"a": list(range(MAX_NODES))}
    for value in (deep, cyclic, wide):
        with pytest.raises(DocumentError) as caught:
            canonicalize(value)
        assert caught.value.reason is DocumentReason.DOCUMENT_UNREADABLE


def test_many_keys_are_checked_for_repeats_in_linear_time() -> None:
    import time

    keys = ", ".join(f'"k{i}": {i}' for i in range(50_000))
    started = time.perf_counter()
    assert len(parse_text("{" + keys + "}")) == 50_000
    assert time.perf_counter() - started < 5
