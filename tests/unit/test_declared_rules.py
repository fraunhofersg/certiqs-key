"""The rule language: alphabets, first-match rules, and their expansion.

Two worked examples are expanded and compared, row for row, with the
tables the instances build: BB84's accepted-format public part
(``instances/bb84/specification.py``, ``_bb84_public``) and decoy BB84's two-message
transcript under all three acceptance maps (the decoy template's lowered public part).
Then the evaluation rules: a missing component never matches, unmatched keys are listed
and omitted, and the two refusals.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest
import yaml
from instances.declared import DocumentError, DocumentReason
from instances.declared.model import AlphabetNode, Public, Rules, Transcript
from instances.declared.rules import (
    Entry,
    Variable,
    build_alphabet,
    build_alphabets,
    check_table,
    expand,
)
from instances.declared.values import Environment
from pydantic import TypeAdapter

from certiqs_key.runs.surface import Kind

ALPHABETS = TypeAdapter(dict[str, AlphabetNode])
RULES = TypeAdapter(Rules)

BB84 = yaml.safe_load(
    """
alphabets:
  signal: {product: {dims: {basis: [Z, X], bit: ["0", "1"]}, label: "({basis},{bit})"}}
  ann: {union: [{enum: [{label: Z, basis: Z}]},
                {product: {dims: {bit: ["0","1"]}, label: "(X,{bit})"},
                 attrs: {basis: X}}]}
public:
  partition: default
  announcements:
    alice: {alphabet: ann,
            map: [{when: {x.basis: Z}, value: Z}, {value: "(X,{x.bit})"}]}
    bob: {alphabet: ann,
          map: [{when: {v.basis: Z}, value: Z}, {value: "(X,{v.bit})"}]}
  sifting: [{when: {A: Z, B: Z}, value: pass}, {value: fail}]
  key: {holder: A, alphabet: [0, 1], rule: [{value: {int: o.bit}}]}
  acceptance:
    alphabet: [gen, ok, err, disc]
    map:
      - {when: {A: Z, B: Z}, value: gen}
      - {when: {A.basis: X, B.basis: X, A.bit: {eq: B.bit}}, value: ok}
      - {when: {A.basis: X, B.basis: X}, value: err}
      - {value: disc}
"""
)


def _bb84_expanded() -> dict[str, Any]:
    alphabets = build_alphabets(ALPHABETS.validate_python(BB84["alphabets"]))
    public = Public.model_validate(BB84["public"])
    assert public.announcements is not None
    signal, ann = alphabets["signal"], alphabets["ann"]
    classes = [Variable("A", ann), Variable("B", ann)]
    key = public.key
    acceptance = public.acceptance
    assert not isinstance(key, list) and hasattr(key, "rule")
    assert hasattr(acceptance, "map")
    return {
        "ann": ann,
        "alice": expand(
            "announce_alice",
            public.announcements.alice.map,
            [Variable("x", signal)],
            path="/a",
        ),
        "bob": expand(
            "announce_bob",
            public.announcements.bob.map,
            [Variable("v", signal)],
            path="/b",
        ),
        "sifting": expand("sifting", public.sifting, classes, path="/s"),
        "key": expand("key", key.rule, [Variable("o", signal), *classes], path="/k"),
        "acceptance": expand("acceptance", acceptance.map, classes, path="/c"),
    }


def test_bb84_expands_to_the_instance_tables() -> None:
    from instances.bb84.specification import (
        BB84_ACCEPTANCE_ALPHABET,
        bb84_specification,
    )

    half = Fraction(1, 2)
    public = bb84_specification(half, half, half, half).public
    expanded = _bb84_expanded()
    assert tuple(entry.label for entry in expanded["ann"]) == (
        public.alice_announcement_alphabet
    )
    assert {k[0]: v for k, v in expanded["alice"].mapping().items()} == dict(
        public.announce_alice
    )
    assert {k[0]: v for k, v in expanded["bob"].mapping().items()} == dict(
        public.announce_bob
    )
    assert expanded["sifting"].mapping() == {
        key: str(value) for key, value in public.sifting.items()
    }
    assert {
        (o, (a, b)): value for (o, a, b), value in expanded["key"].mapping().items()
    } == dict(public.key_rule)
    assert expanded["acceptance"].mapping() == dict(public.accept_statistic)
    assert BB84_ACCEPTANCE_ALPHABET == ("gen", "ok", "err", "disc")
    sizes = [
        len(expanded[name].rows)
        for name in ("alice", "bob", "sifting", "key", "acceptance")
    ]
    assert sizes == [4, 4, 9, 36, 9]
    assert [row.rule_index for row in expanded["sifting"].rows].count(0) == 1


DECOY = yaml.safe_load(
    """
alphabets:
  bob_m2:
    enum: [nc, {label: H, basis: Z, bit: "0"}, {label: V, basis: Z, bit: "1"},
           {label: D, basis: X, bit: "0"}, {label: A, basis: X, bit: "1"}, mc, Z, X]
transcript:
  messages:
    - id: m1
      sender: A
      alphabet: derived
      table:
        - {when: {r.round: gen}, value: {label: gen-Z, attrs: {round: gen}}}
        - value: {label: "test-{r.intensity}-{r.polarisation}",
                  attrs: {round: test, intensity: "{r.intensity}", basis: "{r.basis}",
                          bit: "{r.bit}"}}
    - id: m2
      sender: B
      alphabet: bob_m2
      table:
        - {when: {m1.round: gen, r.letter: [H, V, D, A]}, value: "{r.basis}"}
        - {value: "{r.letter}"}
sifting: [{when: {m1: gen-Z, m2: Z}, value: pass}, {value: fail}]
key: [{when: {o.polarisation: V}, value: 1}, {value: 0}]
acceptance:
  switch: acceptance_map
  cases:
    merged-discard:
      - {when: {m1: gen-Z, m2: Z}, value: gen}
      - {when: {m1.round: test, m2: [H, V, D, A], m2.basis: {eq: m1.basis},
                m2.bit: {eq: m1.bit}}, value: "test-{m1.intensity}-{m1.basis}-ok"}
      - {when: {m1.round: test, m2: [H, V, D, A], m2.basis: {eq: m1.basis}},
         value: "test-{m1.intensity}-{m1.basis}-error"}
      - {value: disc}
    announcement-resolved:
      - {when: {m1: gen-Z, m2: Z}, value: gen}
      - {when: {m1: gen-Z}, value: "gen-{m2}"}
      - {when: {m1.round: test, m2: [nc, mc]}, value: "test-{m1.intensity}-{m2}"}
      - {when: {m1.round: test, m2: [H, V, D, A], m2.basis: {eq: m1.basis},
                m2.bit: {eq: m1.bit}}, value: "test-{m1.intensity}-{m1.basis}-ok"}
      - {when: {m1.round: test, m2: [H, V, D, A], m2.basis: {eq: m1.basis}},
         value: "test-{m1.intensity}-{m1.basis}-error"}
      - {when: {m1.round: test}, value: "test-{m1.intensity}-mismatch"}
    pair-resolved:
      - {when: {m1: gen-Z, m2: Z}, value: gen}
      - {when: {m1: gen-Z}, value: "gen-{m2}"}
      - {value: "{m1}-{m2}"}
"""
)

#: The WCP polarisations' attributes, as a document's ``polarisations`` gives them.
_POLARISATION = {
    "H": ("Z", "0"),
    "V": ("Z", "1"),
    "plus": ("X", "0"),
    "minus": ("X", "1"),
}
_RAW = ("nc", "H", "V", "D", "A", "mc")
#: Bob's emitted labels: the receiver's raw letters (a probe-free receiver's
#: labels carry no setting), as the template's lowering reads them.
_EMITTED = _RAW


def _decoy_model() -> Any:
    from tests.support.lowered_templates import wcp_source

    return wcp_source(
        intensities={"signal": Fraction(4, 5), "weak": Fraction(1, 5), "vacuum": 0},
        test_intensity_probabilities=[Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)],
        gamma=Fraction(1, 4),
    ).tagged.model


def _decoy_expanded(mode: str) -> dict[str, Any]:
    model = _decoy_model()
    source = tuple(
        Entry.of(
            letter.label,
            {
                "round": str(letter.round_type),
                "intensity": letter.intensity,
                "polarisation": letter.polarisation,
                "basis": _POLARISATION[letter.polarisation][0],
                "bit": _POLARISATION[letter.polarisation][1],
            },
        )
        for letter in model.alphabet
    )
    letters = dict(
        zip(
            _RAW,
            [{}, {"basis": "Z"}, {"basis": "Z"}, {"basis": "X"}, {"basis": "X"}, {}],
            strict=True,
        )
    )
    bob = tuple(
        Entry.of(label, {"letter": raw, **letters[raw]})
        for label, raw in zip(_EMITTED, _RAW, strict=True)
    )
    named = ALPHABETS.validate_python(DECOY["alphabets"])
    transcript = Transcript.model_validate(DECOY["transcript"])
    first = expand(
        "m1", transcript.messages[0].table, [Variable("r", source)], path="/m1"
    )
    m1 = first.alphabet()
    m2 = build_alphabet("bob_m2", named, "/m2")
    second = expand(
        "m2",
        transcript.messages[1].table,
        [Variable("r", bob), Variable("m1", m1)],
        path="/m2",
    )
    classes = [Variable("m1", m1), Variable("m2", m2)]
    environment = Environment({"acceptance_map": Kind.CHOICE}, {"acceptance_map": mode})
    acceptance = expand(
        "acceptance",
        RULES.validate_python(DECOY["acceptance"]),
        classes,
        path="/acc",
        environment=environment,
    )
    return {
        "source": model,
        "m1": first,
        "m1_alphabet": tuple(entry.label for entry in m1),
        "m2": second,
        "m2_alphabet": tuple(entry.label for entry in m2),
        "sifting": expand(
            "sifting", RULES.validate_python(DECOY["sifting"]), classes, path="/s"
        ),
        "key": expand(
            "key",
            RULES.validate_python(DECOY["key"]),
            [Variable("o", source), *classes],
            path="/k",
        ),
        "acceptance": acceptance,
    }


@pytest.mark.parametrize(
    "mode", ["merged-discard", "announcement-resolved", "pair-resolved"]
)
def test_decoy_transcript_expands_to_the_instance_tables(mode: str) -> None:
    from instances.decoy_bb84.surface import default_config
    from tests.support.lowered_templates import lowered

    expanded = _decoy_expanded(mode)
    # The template's defaults are the source above: intensities 4/5, 1/5, 0,
    # test probabilities 1/2, 1/4, 1/4, coin 1/4.
    _configured, lowering = lowered(
        "decoy_bb84", default_config(device={"acceptance_map": mode})
    )
    assert lowering.wcp_source is not None
    assert lowering.wcp_source.tagged.model == expanded["source"]
    public = lowering.public
    assert public is not None
    transcript = public.transcript
    assert transcript is not None
    first, second = transcript.messages
    assert (
        expanded["m1_alphabet"] == first.alphabet == public.alice_announcement_alphabet
    )
    assert (
        expanded["m2_alphabet"] == second.alphabet == public.bob_announcement_alphabet
    )
    assert {(k[0], ()): v for k, v in expanded["m1"].mapping().items()} == dict(
        first.table
    )
    assert {(k[0], (k[1],)): v for k, v in expanded["m2"].mapping().items()} == dict(
        second.table
    )
    assert expanded["sifting"].mapping() == {
        key: str(value) for key, value in public.sifting.items()
    }
    assert {
        (o, (a, b)): value for (o, a, b), value in expanded["key"].mapping().items()
    } == dict(public.key_rule)
    assert public.accept_statistic_general is not None
    assert expanded["acceptance"].mapping() == dict(public.accept_statistic_general)
    assert (
        tuple(entry.label for entry in expanded["acceptance"].alphabet())
        == public.acceptance_alphabet
    )
    for name in ("m1", "m2", "sifting", "key", "acceptance"):
        assert expanded[name].unmatched == ()


# ---------------------------------------------------------------------------
#  Alphabets
# ---------------------------------------------------------------------------


def _alphabets(text: str) -> dict[str, tuple[Entry, ...]]:
    return build_alphabets(ALPHABETS.validate_python(yaml.safe_load(text)))


def test_product_order_and_components() -> None:
    built = _alphabets("p: {product: {dims: {a: [x, y], b: [0, 1]}, label: '{a}{b}'}}")[
        "p"
    ]
    assert [entry.label for entry in built] == ["x0", "x1", "y0", "y1"]
    assert built[1].components == {"a": "x", "b": "1", "label": "x1"}


def test_union_and_reference_and_attributes() -> None:
    built = _alphabets(
        "base: {enum: [a, {label: b, kind: k}]}\n"
        "all: {union: [base, {enum: [c], attrs: {kind: other}}]}\n"
    )
    assert [entry.label for entry in built["all"]] == ["a", "b", "c"]
    assert built["all"][2].component("kind") == "other"
    assert built["all"][0].component("kind") is None


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("p: {enum: [a, b, a]}", DocumentReason.ALPHABET_LABELS_NOT_DISTINCT),
        (
            "p: {union: [{enum: [a]}, {enum: [a]}]}",
            DocumentReason.ALPHABET_LABELS_NOT_DISTINCT,
        ),
        (
            "p: {product: {dims: {a: [x, y]}, label: z}}",
            DocumentReason.ALPHABET_LABELS_NOT_DISTINCT,
        ),
        ("p: {union: [q]}", DocumentReason.RULE_REFERENCE_UNKNOWN),
        ("p: {union: [p]}", DocumentReason.DOCUMENT_SCHEMA_VIOLATION),
        (
            "p: {product: {dims: {a: [x]}, label: '{b}'}}",
            DocumentReason.RULE_REFERENCE_UNKNOWN,
        ),
        (
            "p: {enum: [{label: a, kind: k}], attrs: {kind: j}}",
            DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
        ),
    ],
)
def test_what_an_alphabet_refuses(text: str, reason: DocumentReason) -> None:
    with pytest.raises(DocumentError) as caught:
        _alphabets(text)
    assert caught.value.reason is reason


# ---------------------------------------------------------------------------
#  Evaluation
# ---------------------------------------------------------------------------

M1 = (
    Entry.of("gen-Z", {"round": "gen"}),
    Entry.of("test-weak-H", {"round": "test", "basis": "Z", "bit": "0"}),
)
M2 = (Entry.of("Z"), Entry.of("H", {"basis": "Z", "bit": "0"}))


def _expand(rules: object, **kwargs: Any) -> Any:
    return expand(
        "t",
        RULES.validate_python(rules),
        [Variable("m1", M1), Variable("m2", M2)],
        path="/t",
        **kwargs,
    )


def test_a_missing_component_never_matches() -> None:
    table = _expand(
        [
            {"when": {"m1.basis": "Z"}, "value": "basis-Z"},
            {"when": {"m2.bit": {"eq": "m1.bit"}}, "value": "same-bit"},
            {"when": {"m2.bit": {"not": {"eq": "m1.bit"}}}, "value": "other-bit"},
            {"value": "rest"},
        ]
    ).mapping()
    assert table[("gen-Z", "Z")] == "rest"
    assert table[("gen-Z", "H")] == "rest"
    assert table[("test-weak-H", "Z")] == "basis-Z"


def test_first_match_and_unmatched_keys_are_listed_not_refused() -> None:
    expansion = _expand(
        [
            {"when": {"m1": "gen-Z", "m2": "Z"}, "value": "gen"},
            {"when": {"m1": "gen-Z"}, "value": "never-first"},
            {"when": {"m2": ["Z", "H"], "m1": {"ne": "m2"}}, "value": 7},
        ]
    )
    assert expansion.mapping()[("gen-Z", "Z")] == "gen"
    assert expansion.mapping()[("test-weak-H", "H")] == 7
    assert expansion.unmatched == ()
    guarded = _expand(
        [{"when": {"m1": "gen-Z", "m2.bit": "0"}, "value": {"int": "m2.bit"}}]
    )
    assert guarded.mapping() == {("gen-Z", "H"): 0}
    assert _code(
        lambda: _expand([{"when": {"m2": "H"}, "value": {"int": "m1.basis"}}])
    ) is (DocumentReason.RULE_VALUE_INVALID)
    some = _expand([{"when": {"m2": "H"}, "value": "x"}])
    assert some.unmatched == (("gen-Z", "Z"), ("test-weak-H", "Z"))
    assert some.as_record() == {
        "variables": ["m1", "m2"],
        "rows": [["gen-Z", "H", "x", 0], ["test-weak-H", "H", "x", 0]],
        "unmatched": [["gen-Z", "Z"], ["test-weak-H", "Z"]],
    }


def _code(call: Any) -> DocumentReason:
    with pytest.raises(DocumentError) as caught:
        call()
    return caught.value.reason


@pytest.mark.parametrize(
    ("rules", "reason"),
    [
        ([{"when": {"m3": "x"}, "value": "y"}], DocumentReason.RULE_REFERENCE_UNKNOWN),
        (
            [{"when": {"m1.colour": "x"}, "value": "y"}],
            DocumentReason.RULE_REFERENCE_UNKNOWN,
        ),
        (
            [{"when": {"m1": {"eq": "m2.colour"}}, "value": "y"}],
            DocumentReason.RULE_REFERENCE_UNKNOWN,
        ),
        ([{"value": "{m9}"}], DocumentReason.RULE_REFERENCE_UNKNOWN),
        ([{"value": "{m1.basis}"}], DocumentReason.RULE_VALUE_INVALID),
        ([{"value": {"label": "{m2.bit}"}}], DocumentReason.RULE_VALUE_INVALID),
    ],
)
def test_the_two_refusals(rules: object, reason: DocumentReason) -> None:
    assert _code(lambda: _expand(rules)) is reason


def test_a_guarded_template_renders() -> None:
    table = _expand([{"when": {"m1.round": "test"}, "value": "{m1.basis}"}]).mapping()
    assert table == {("test-weak-H", "Z"): "Z", ("test-weak-H", "H"): "Z"}


def test_a_derived_alphabet_refuses_one_label_with_two_meanings() -> None:
    expansion = _expand(
        [
            {"when": {"m2": "Z"}, "value": {"label": "v", "attrs": {"a": "1"}}},
            {"value": {"label": "v", "attrs": {"a": "2"}}},
        ]
    )
    assert _code(expansion.alphabet) is DocumentReason.RULE_VALUE_INVALID


def test_a_switch_over_rules_needs_a_configuration() -> None:
    rules = {"switch": "mode", "cases": {"a": [{"value": "x"}]}}
    assert _code(lambda: _expand(rules)) is DocumentReason.SWITCH_CASE_MISSING
    environment = Environment({"mode": Kind.CHOICE}, {"mode": "a"})
    assert set(_expand(rules, environment=environment).mapping().values()) == {"x"}


def test_every_case_is_checked_not_only_the_chosen_one() -> None:
    """A typo in a case the configuration does not select still fails."""
    rules = {
        "switch": "mode",
        "cases": {
            "a": [{"value": "x"}],
            "b": [{"when": {"m1.colour": "y"}, "value": "z"}],
        },
    }
    environment = Environment({"mode": Kind.CHOICE}, {"mode": "a"})
    assert _code(lambda: _expand(rules, environment=environment)) is (
        DocumentReason.RULE_REFERENCE_UNKNOWN
    )
    with pytest.raises(DocumentError) as caught:
        check_table("t", RULES.validate_python(rules), {"m1": M1, "m2": M2}, "/t")
    assert caught.value.path == "/t/cases/b/0/when/m1.colour"


def test_an_unknown_variable_is_refused_even_where_components_are_unknown() -> None:
    rules = RULES.validate_python([{"when": {"q.x": "y"}, "value": "z"}])
    with pytest.raises(DocumentError) as caught:
        check_table("t", rules, {"m1": None}, "/t")
    assert caught.value.reason is DocumentReason.RULE_REFERENCE_UNKNOWN
    check_table(
        "t",
        RULES.validate_python([{"when": {"m1.any": "y"}, "value": "z"}]),
        {"m1": None},
        "/t",
    )


def test_a_derived_alphabet_refusal_names_its_table_path() -> None:
    expansion = _expand(
        [
            {"when": {"m2": "Z"}, "value": {"label": "v", "attrs": {"a": "1"}}},
            {"value": {"label": "v", "attrs": {"a": "2"}}},
        ]
    )
    with pytest.raises(DocumentError) as caught:
        expansion.alphabet()
    assert caught.value.path == "/t"
