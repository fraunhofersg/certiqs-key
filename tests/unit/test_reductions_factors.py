"""The factor emission of ``thm:emitted-product``: the rule, and no product.

WHAT THESE TESTS ARE FOR, ROW BY ROW. The factor emission is the
one place this module emits more than one artefact, and its design (a
factorised family, no snap) is a decision about what is NOT formed. So the
tests here are of two kinds:

* the POSITIVE ones -- a two-factor emission on a toy pair of instances, the
  product sector map and the product alphabet, the ``party_local`` tag with its
  factor scope, the licence's party-local row, and the party label of an
  instance;
* the NEGATIVE ones, which are the point -- that a one-factor emission is
  today's artefact BYTE FOR BYTE, that NO KRONECKER PRODUCT IS FORMED ON THE
  EMISSION PATH, and that each refusal the factor rows decide is
  reached with an EXISTING reason string and no new one.

THE TOY PAIR IS TWO STATIONS OF ONE DEVICE MODEL, built by
``tests/support/reductions_support.flat_call`` with two declared party labels.
That is the degenerate BBM92 shape and is deliberately the SAME device twice:
what the tests are about is the factorisation and the labels, and two different
devices would make a failure ambiguous between the two.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from reductions_support import flat_call

from certiqs_key.domain.chain import Side, SystemDescriptor
from certiqs_key.domain.constraints import RhsTag
from certiqs_key.domain.families import FactorisedFamily
from certiqs_key.foundations.blocks import PRODUCT_LABEL_SEPARATOR, SystemTag
from certiqs_key.reductions import docking
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.constraints import ConstraintEntry, EntryTag
from certiqs_key.reductions.emit import emitted_assumption_rows, reduce
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.factors import (
    FactorCall,
    assemble_factor_emissions,
    reduce_factors,
)
from certiqs_key.reductions.links import Chain
from certiqs_key.reductions.reasons import Refusal, RefusalReason
from certiqs_key.reductions.sectors import party_partition_statement
from certiqs_key.reductions.wpfss import FlatInstanceBuilder

#: The block kind the flat instance's sector map is licensed by. It is the
#: INSTANCE'S declared kind and is never defaulted by the format, so a test
#: declares it exactly as a caller must.
KIND = "proof_sector"


#: THE SECOND FACTOR'S OWN DETECTION LETTERS. The toy pair is two stations, and
#: they are NOT the same declaration twice: a pair that agreed in every datum
#: could not tell a per-factor reading from a joint one, because either would
#: give the same answer. The letters are
#: what the second station's alphabet, its sector identifiers and therefore its
#: emitted blocks are named by, so differing here differs everywhere a factor's
#: identity is read.
SECOND_LETTERS = ("z_empty", "z_1", "z_2", "z_mc")


def _factor(
    party: str | None, label: str | None = None, **overrides: object
) -> FactorCall:
    """Return one factor of the toy pair: a flat instance scoped to ``party``."""
    return FactorCall(
        call=flat_call(party=party, **overrides),
        builder=FlatInstanceBuilder(),
        sector_block_kind=KIND,
        factor_label=label,
    )


def _pair(**overrides: object) -> tuple[FactorCall, FactorCall]:
    """Return the toy pair: Alice's station first, Bob's second, and DIFFERENT.

    The second factor declares its own detection letters, so the two factors
    differ in their alphabets, their sector identifiers and their emitted
    blocks -- which is what makes an assertion about WHICH factor an entry is
    scoped to say something.
    """
    return (
        _factor("Alice", **overrides),
        _factor("Bob", letters=SECOND_LETTERS, **overrides),
    )


# ---------------------------------------------------------------------------
#  One factor is today's artefact, byte for byte
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_one_factor_emission_is_todays_artefact_byte_for_byte() -> None:
    """``thm:emitted-product`` (vi), as an identity of the emitted records.

    "At one factor the combination rule is the identity, the product sector map
    is that factor's, the product channel is that factor's channel, and every
    statement above is ``thm:emit``'s ... SO THIS ROW ADDS NOTHING TO A
    ONE-FACTOR ARTEFACT AND IS ABSENT FROM IT."

    The comparison is against :func:`certiqs_key.reductions.emit.reduce` on the
    SAME call, so what it pins is that the factor path reaches the core's own
    emission and changes nothing on the way: the artefact is the object that
    call emitted, not a copy of it.
    """
    factor = _factor(None)
    direct = reduce(factor.call, FlatInstanceBuilder())
    assert direct.artifact is not None
    outcome = reduce_factors([factor])
    assert outcome.refusal is None
    assert outcome.emission is not None
    assert outcome.emission.count == 1
    artefact = outcome.artefact
    assert isinstance(artefact, ProofReductionArtifact)
    assert artefact.as_machine_record() == direct.artifact.as_machine_record()
    # AND THE RECORD IS THE EIGHTEEN KEYS IT ALWAYS WAS: `factor_emission` is
    # absent from a one-factor artefact.
    assert "factor_emission" not in artefact.as_machine_record()
    # The one-factor map and family ARE that factor's, which is what the
    # shared format's single-factor default means.
    assert outcome.emission.product_sector_map().labels == tuple(
        f"{group}:{name}" for group, name in artefact.target_descriptor.sectors.labels
    )
    assert outcome.emission.product_alphabet() == tuple(
        f"{letter},{setting}"
        for letter, setting in factor.call.declaration.joint_alphabet
    )


@pytest.mark.contract
def test_every_entry_of_a_one_factor_emission_is_untagged() -> None:
    """``cor:entries``: "EVERY ENTRY OF A ONE-FACTOR EMISSION IS UNTAGGED".

    And the request for the party-local form there is answered with THE
    UNTAGGED ENTRY AND NOT A REFUSAL, at the same operator, relation and
    constant -- the decision ``cor:entries`` writes down, for which no reason
    string exists and none is invented.
    """
    factor = _factor(None, route="licensed")
    outcome = reduce_factors([factor])
    assert outcome.refusal is None
    assert outcome.emission is not None
    assert outcome.emission.entries
    artefact = outcome.artefact
    assert artefact is not None
    assert all(entry.tag is None for entry in outcome.emission.entries)
    assert all(entry.scope is None for entry in outcome.emission.entries)
    # THE SAME OBJECTS the artefact emitted: nothing is re-derived and no
    # constant is rounded a second time.
    assert outcome.emission.entries == artefact.constraint_list
    # THE LICENCE IS THE ARTEFACT'S OWN, the object and not a copy: at one
    # factor "what is emitted is that instance's artefact" (thm:emitted-product
    # (vi)), so a second record would be a second wording of one licence.
    assert outcome.emission.licence is artefact.attack_set_license
    assert outcome.emission.licence is not None
    assert outcome.emission.licence.party_local_entries == ()
    assert "party_local_entries" not in (
        outcome.emission.licence.as_machine_record()
    )


# ---------------------------------------------------------------------------
#  The two-factor emission
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_two_factor_emission_is_one_artefact_per_party_and_a_rule() -> None:
    """``thm:emitted-product`` (i), (ii): the ordered list and the combination rule.

    ONE ARTEFACT PER MEASURING PARTY, each complete and each carrying its own
    party partition; the product sector map with the last factor varying
    fastest, its identifiers the factors' identifiers joined in that order and
    its dimensions the products; and the product alphabet the same way.
    """
    alice, bob = _pair()
    outcome = reduce_factors([alice, bob])
    assert outcome.refusal is None
    emission = outcome.emission
    assert emission is not None
    assert emission.count == 2
    assert emission.parties == ("Alice", "Bob")
    # THE FACTOR LABELS ARE WHAT A SCOPE NAMES, and the default is the position
    # in the declared order; the parties travel beside them.
    assert emission.factors == ("f0", "f1")
    assert outcome.artefact is None, "a two-factor emission is not one artefact"
    # EACH FACTOR CARRIES ITS OWN LABEL IN ITS OWN COPY OF THE PARTITION ROW.
    assert [
        artefact.target_descriptor.party_partition for artefact in emission.artefacts
    ] == [party_partition_statement("Alice"), party_partition_statement("Bob")]
    # THE PRODUCT SECTOR MAP: dimensions multiply, identifiers join, and the
    # LAST FACTOR VARIES FASTEST.
    factors = [
        artefact.target_descriptor.sectors for artefact in emission.artefacts
    ]
    product_map = emission.product_sector_map()
    assert product_map.count == len(factors[0].labels) * len(factors[1].labels)
    assert product_map.dims[0] == factors[0].dimensions[0] * factors[1].dimensions[0]
    assert PRODUCT_LABEL_SEPARATOR in product_map.labels[0]
    first, second = product_map.labels[0], product_map.labels[1]
    assert first.split(PRODUCT_LABEL_SEPARATOR)[0] == (
        second.split(PRODUCT_LABEL_SEPARATOR)[0]
    ), "the last factor varies fastest, so the first factor's part repeats"
    # THE PRODUCT ALPHABET, in the same order and by the same rule.
    assert len(emission.product_alphabet()) == len(
        alice.call.declaration.joint_alphabet
    ) * len(bob.call.declaration.joint_alphabet)
    # BOTH FACTORS ARE MEASURED SYSTEMS: {F_v} is a measurement on the measured
    # systems, and no factor of this emission decomposes the retained A.
    assert emission.sector_map.systems == (SystemTag.Q, SystemTag.Q)
    assert emission.sector_map.factors_of(SystemTag.A) == ()
    # THE RULE IS EMITTED AS A RULE, and the record says what is not emitted.
    record = emission.as_machine_record()
    assert "F_v = (x)_f F^f_{v_f}" in str(record["combination_rule"])
    assert "NOT EMITTED AS A NUMBER" in str(record["product_class_weights"])
    factor_records = record["factors"]
    assert isinstance(factor_records, list)
    assert len(factor_records) == 2
    # THE FACTOR LIST A CONSUMER COMPARES A SCOPE AGAINST is emitted, with each
    # factor's party beside its label.
    assert [item["factor"] for item in factor_records] == ["f0", "f1"]
    assert [item["party"] for item in factor_records] == ["Alice", "Bob"]
    product = record["product_sector_map"]
    assert isinstance(product, dict)
    assert product["factor_list"] == ["f0", "f1"]


@pytest.mark.contract
def test_already_emitted_factors_use_the_same_assembly_path() -> None:
    """Prepared station artefacts can be combined without reducing them again."""
    factors = _pair()
    original = reduce_factors(factors)
    assert original.emission is not None
    assembled = assemble_factor_emissions(
        factors,
        original.emission.artefacts,
        declared_factor_order=("f0", "f1"),
    )
    assert assembled == original.emission

    with pytest.raises(MalformedInputError, match="one already-emitted artefact"):
        assemble_factor_emissions(factors, original.emission.artefacts[:1])


@pytest.mark.contract
def test_a_one_factor_emission_has_no_factor_emission_value() -> None:
    """The row is ABSENT at one factor, so there is no value to serialize.

    "PRESENT EXACTLY WHEN THE CALL DECLARES MORE THAN ONE INSTANCE ... ABSENT
    FOR A ONE-FACTOR EMISSION, which is every emission of version 1." What a
    caller reads there is the artefact, and a record for the key would be a
    value for a key the accepted row says is not there.
    """
    outcome = reduce_factors([_factor(None)])
    assert outcome.emission is not None
    assert outcome.artefact is not None
    with pytest.raises(MalformedInputError):
        outcome.emission.as_machine_record()


@pytest.mark.contract
def test_two_stations_of_one_party_are_emitted_with_distinct_factor_scopes() -> None:
    """"NOTHING REQUIRES TWO FACTORS TO CARRY DIFFERENT LABELS" (the row).

    Two stations of ONE party are two factors, and the emission carries them:
    the party label repeats, the FACTOR labels do not, and each tagged entry is
    scoped to the factor whose artefact emitted it. That is what the factor
    label is for -- a scope that named the party would name two factors here,
    and the channel row could then not tell one factor's witness from the
    other's (``lem:party-local`` (iv)).
    """
    stations = [
        _factor("Bob", route="licensed"),
        _factor("Bob", route="licensed", letters=SECOND_LETTERS),
    ]
    outcome = reduce_factors(stations)
    assert outcome.refusal is None
    emission = outcome.emission
    assert emission is not None
    assert emission.parties == ("Bob", "Bob")
    assert emission.factors == ("f0", "f1")
    assert emission.sector_map.parties == ("Bob", "Bob")
    # EVERY ENTRY IS SCOPED TO THE FACTOR WHOSE ARTEFACT CARRIES ITS LABEL, and
    # the two stations' entries are distinguishable because their alphabets are.
    for label, artefact in zip(
        emission.factors, emission.artefacts, strict=True
    ):
        labels = {entry.label for entry in artefact.constraint_list}
        assert labels
        for entry in emission.entries:
            if entry.label in labels:
                assert entry.scope == label
    assert {entry.scope for entry in emission.entries} == {"f0", "f1"}
    # AND A CALLER MAY NAME ITS OWN FACTORS, which is what the scope then is.
    named = reduce_factors(
        [
            _factor("Bob", label="north", route="licensed"),
            _factor("Bob", label="south", route="licensed", letters=SECOND_LETTERS),
        ]
    )
    assert named.emission is not None
    assert named.emission.factors == ("north", "south")
    assert {entry.scope for entry in named.emission.entries} == {"north", "south"}


@pytest.mark.contract
def test_no_kronecker_product_is_formed_on_the_emission_path() -> None:
    """THE BINDING HALF OF THE DESIGN, as a test that fails if a product is formed.

    "NO ENTRY OF ANY F_v, OF ANY M^dec_v OR OF ANY PRODUCT CONSTRAINT OPERATOR
    IS EMITTED, DECLARED, ROUNDED OR SNAPPED", and the reason is arithmetic as
    well as structural: "a Kronecker product of two families on the 2^-kappa
    lattice lies on the 2^-2kappa lattice, so a declared product would have to
    be re-normalized against kappa, and a snapped joint target would declare a
    NON-PRODUCT measurement for separated stations".

    The two ways a product could be formed are both poisoned here: the exact
    substrate's ``kron``, which is the only multiplication of two operators the
    shared format offers, and ``FactorisedFamily.product_block``, which is the
    one function that calls it FOR a consumer. Poisoning both and emitting
    anyway is the whole assertion; the one-factor path is poisoned too, because
    the Kronecker product of one operand is that operand and an implementation
    could form it there without noticing.
    """
    import certiqs_key.domain.families as families
    import certiqs_key.foundations.exact as exact

    formed: list[str] = []

    def _poisoned_kron(*args: object, **kwargs: object) -> object:
        formed.append("kron")
        raise AssertionError(
            "a Kronecker product was formed on the emission path; "
            "thm:emitted-product (v) and the factor_emission row bind that no "
            "entry of any product operator is emitted, declared, rounded or "
            "snapped"
        )

    def _poisoned_block(*args: object, **kwargs: object) -> object:
        formed.append("product_block")
        raise AssertionError(
            "FactorisedFamily.product_block was called on the emission path; "
            "it exists for a NUMERICAL CONSUMER and is called by nothing that "
            "decides anything"
        )

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(exact, "kron", _poisoned_kron)
        patch.setattr(families, "kron", _poisoned_kron)
        patch.setattr(FactorisedFamily, "product_block", _poisoned_block)
        alice, bob = _pair()
        pair_outcome = reduce_factors([alice, bob])
        one = reduce_factors([_factor(None)])
        # And the records, which is where an entry of a product operator would
        # have to appear if one existed. At one factor there is no
        # `factor_emission` value, so what is serialized there is the artefact.
        assert pair_outcome.emission is not None
        pair_outcome.emission.as_machine_record()
        assert one.artefact is not None
        one.artefact.as_machine_record()
    assert formed == []


#: THE PACKAGE'S ONLY KRONECKER PRODUCT, a WITHIN-ONE-INSTANCE register
#: ampliation and not a product of two factors: ``channels.py``'s
#: ``instrument_adjoint``, which IS ``thm:mixture``'s ``I_b+(X) = X (x) N_b``
#: -- the adjoint of one instrument branch of ONE instance, over that
#: instance's own declared register POVM.
#:
#: It is an operator of ONE reduction instance on ``B = B_0 D``, which
#: ``def:reduction-instance`` (I1) admits and which no factor of a factor
#: emission is: a product of two factors' TARGETS is what ``thm:emitted-product``
#: forbids, and this forms none. It is listed by file and function rather than
#: allowed by a blanket exemption, so that a second call has to be added here
#: with its reason.
DECLARED_KRON_SITES: dict[str, str] = {
    "channels.py": "instrument_adjoint",
}


@pytest.mark.contract
def test_only_the_declared_register_ampliations_call_kron_in_the_package() -> None:
    """THE SAME BINDING, DECIDED STATICALLY OVER THE PACKAGE.

    The dynamic test above poisons the two functions on ONE path -- the paths
    its two calls take -- and a product formed on a path no test exercises would
    pass it. This one reads the package instead: every call node under
    ``src/certiqs_key/reductions`` that names ``kron`` or ``product_block`` is
    one of :data:`DECLARED_KRON_SITES`, and ``factors.py`` -- the emission of
    several measuring parties, which is where a PRODUCT OF FACTORS could be
    formed -- contains none.

    WHAT IT WOULD ALLOW AND DELIBERATELY DOES NOT: a helper in ``domain/`` that
    formed a product internally would pass this test, which is why the dynamic
    one stays -- the two catch different mistakes, and neither is the other's
    weaker form.
    """
    import ast

    root = Path(__file__).resolve().parents[2] / "src" / "certiqs_key" / "reductions"
    found: list[tuple[str, str, str]] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # THE ENCLOSING FUNCTION OF EVERY CALL, so that the declared sites are
        # checked as SITES and not merely as file names: a `kron` moved into
        # another function of the same file is a call nobody declared, and the
        # map's values are asserted by this walk.
        # THE INNERMOST ENCLOSING FUNCTION NAMES THE SITE: ``ast.walk`` is
        # breadth-first, so an outer function is visited before the nested one
        # it holds and the later assignment -- the inner -- wins. A nested
        # helper is where the call actually is, and naming its holder would let
        # the call move between the holder's helpers unnoticed.
        enclosing: dict[ast.AST, str] = {}
        for holder in ast.walk(tree):
            if isinstance(holder, ast.FunctionDef | ast.AsyncFunctionDef):
                for inner in ast.walk(holder):
                    enclosing[inner] = holder.name
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = node.func
            name = (
                called.id
                if isinstance(called, ast.Name)
                else called.attr
                if isinstance(called, ast.Attribute)
                else ""
            )
            if name in {"kron", "product_block"}:
                found.append((path.name, enclosing.get(node, "<module>"), name))
    assert sorted(item[0] for item in found) == sorted(DECLARED_KRON_SITES), found
    assert all(name == "kron" for _, _, name in found), found
    # THE VALUES ARE ASSERTED TOO: each call sits in the function the map names.
    assert {file: function for file, function, _ in found} == DECLARED_KRON_SITES
    # AND THE FACTOR EMISSION CONTAINS NONE, which is the file the binding is
    # about: no product of two factors' operators is formed there.
    assert "factors.py" not in {item[0] for item in found}


# ---------------------------------------------------------------------------
#  The party_local tag, its scope and its licence row
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_tag_and_its_scope_are_emitted_only_through_the_factor_emission() -> None:
    """``cor:entries``: the tag is emitted in ONE place, and per factor.

    ``thm:emitted-product`` (iii): the joint list is the disjoint union of the
    factors' lists, "each entry scoped to its factor and carrying the same
    operator, the same relation and the same constant". So every tagged entry
    is scoped to a declared party, its operator is the factor's own block list
    against that factor's sector map, and its constant is the one that factor
    emitted -- NO CONSTANT IS RE-DERIVED AND NONE IS ROUNDED.
    """
    alice, bob = _pair(route="licensed")
    outcome = reduce_factors([alice, bob])
    assert outcome.refusal is None
    emission = outcome.emission
    assert emission is not None
    assert emission.entries
    # THE SCOPE IS THE FACTOR'S LABEL, not its party's.
    assert {entry.scope for entry in emission.entries} == set(emission.factors)
    assert all(entry.tag is EntryTag.PARTY_LOCAL for entry in emission.entries)
    for artefact, label in zip(emission.artefacts, emission.factors, strict=True):
        scoped = [e for e in emission.entries if e.scope == label]
        assert len(scoped) == len(artefact.constraint_list)
        for tagged, emitted in zip(scoped, artefact.constraint_list, strict=True):
            assert tagged.operator == emitted.operator
            assert tagged.relation is emitted.relation
            assert tagged.constant == emitted.constant
            assert tagged.certified_against == emitted.certified_against
            # The operator is an operator on THAT FACTOR'S Q_f: one square
            # block per sector of that factor and nothing wider.
            sectors = artefact.target_descriptor.sectors.sectors
            assert len(tagged.operator) == len(sectors)
    # And the factors' own artefacts are untouched: their entries are untagged,
    # which is what makes each of them today's artefact.
    assert all(
        entry.tag is None
        for artefact in emission.artefacts
        for entry in artefact.constraint_list
    )
    # THE INVARIANT THE PER-FACTOR GUARD ESTABLISHES, ASSERTED OVER THE WHOLE
    # EMISSION: every tagged entry's scope
    # is a factor of the declared list and its certificate is THAT FACTOR'S own
    # channel witness -- the hypothesis of thm:licence (v).
    witnesses = dict(zip(emission.factors, emission.channel_witnesses, strict=True))
    for entry in emission.entries:
        assert entry.scope in witnesses
        assert entry.certified_against == witnesses[entry.scope]


@pytest.mark.contract
def test_the_licence_names_the_party_local_row_per_entry() -> None:
    """``thm:licence`` (v) and ``interface.yaml``'s ``party_local_entries``.

    PER ENTRY AND NEVER PER ARTEFACT: the part that licenses it, the factor and
    that factor's channel witness, the certificate discharged on that factor's
    channel with the supplier fact and version that discharge it, the
    party-local set ``eq:attsetpl``, and THE SCALAR SET THE SAME ENTRY IS ALSO
    ADMISSIBLE IN. What is NOT named is a joint channel: there is none.

    AND THE LICENCE'S OWN FIELDS ARE THE JOINT LIST'S, not a copy of the first
    factor's: one hypothesis line per joint
    entry, an admissible set naming every entry's condition, and the supplier
    artefact version OF EVERY FACTOR, because A-RECV names the artefact by
    version and there is one per factor.
    """
    alice, bob = _pair(route="licensed")
    emission = reduce_factors([alice, bob]).emission
    assert emission is not None
    licence = emission.licence
    assert licence is not None
    assert len(licence.party_local_entries) == len(emission.entries)
    witnesses = dict(
        zip(emission.factors, emission.channel_witnesses, strict=True)
    )
    party_of = dict(zip(emission.factors, emission.parties, strict=True))
    for row in licence.party_local_entries:
        assert row.part == "Theorem thm:licence (v)"
        assert row.factor in witnesses
        assert row.party == party_of[row.factor]
        assert row.factor_channel_witness == witnesses[row.factor]
        assert "eq:attsetpl" in row.admissible_set
        assert "lifted operator" in row.also_admissible_as_a_scalar
        assert "A-RECV" in row.discharging_receiver_fact
        assert row.factor_spec_version
    # THE SHARED FIELDS ARE OVER THE JOINT LIST.
    assert len(licence.hypothesis_per_entry) == len(emission.entries)
    for entry, line in zip(
        emission.entries, licence.hypothesis_per_entry, strict=True
    ):
        assert entry.label in line
        assert entry.scope is not None and entry.scope in line
    for entry in emission.entries:
        assert entry.label in licence.admissible_set
    for label, artefact in zip(
        emission.factors, emission.artefacts, strict=True
    ):
        assert label in licence.receiver_spec_version
        assert (
            artefact.verification_report.receiver_spec_version
            in licence.receiver_spec_version
        )
    assert licence.source_mode is alice.call.declaration.source_mode
    record = licence.as_machine_record()
    assert "party_local_entries" in record
    # NO JOINT CHANNEL IS NAMED ANYWHERE IN THE RECORD.
    assert "joint channel" not in str(record)


@pytest.mark.contract
def test_the_explicit_scalar_view_uses_the_licensed_consequence() -> None:
    """The same scoped O, relation and c cross under thm:licence (v)."""
    alice, bob = _pair(route="licensed")
    emission = reduce_factors([alice, bob]).emission
    assert emission is not None
    operator_view = docking.factor_constraint_entries(emission)
    scalar_view = docking.factor_constraint_entries(
        emission, party_local_view=docking.PartyLocalView.LICENSED_SCALAR
    )
    assert operator_view
    for operator_entry, scalar_entry in zip(
        operator_view, scalar_view, strict=True
    ):
        assert operator_entry.arriving_tag is RhsTag.PARTY_LOCAL
        assert scalar_entry.arriving_tag is None
        assert scalar_entry.tag is RhsTag.HOMOGENEOUS
        assert scalar_entry.operator == operator_entry.operator
        assert scalar_entry.relation is operator_entry.relation
        assert scalar_entry.rhs == operator_entry.rhs
        assert scalar_entry.scope == operator_entry.scope

    default_licence = docking.factor_attack_set_license(emission)
    scalar_licence = docking.factor_attack_set_license(
        emission, party_local_view=docking.PartyLocalView.LICENSED_SCALAR
    )
    assert default_licence is not None and scalar_licence is not None
    assert "Scalar view selected" not in default_licence.statement
    assert "also_admissible_as_a_scalar" in scalar_licence.statement
    for row in emission.licence.party_local_entries:
        assert row.also_admissible_as_a_scalar in scalar_licence.statement


@pytest.mark.contract
def test_a_factor_list_in_two_source_modes_is_refused() -> None:
    """One emission, ONE declared source mode (``def:licensed``).

    ``thm:emitted-product`` (iii) licenses the joint list in ONE licensed class
    and ``def:licensed`` types a licensed right-hand side BY THE MODE, so a
    mixed list has no admissible set of ``def:attset`` to name. NO REFUSAL
    STRING OF THIS MODULE HAS A ROW TRUE OF IT -- the nearest are
    ``alphabet_or_order_mismatch``, ``route_not_single_valued`` and
    ``licence_missing``, and none is about a factor list's modes -- so the list
    is MALFORMED INPUT, as an empty one is, and is refused before any factor is
    reduced.
    """
    from certiqs_key.reductions.reasons import SourceMode

    trusted = _factor("Alice")
    untrusted = _factor("Bob", letters=SECOND_LETTERS)
    assert untrusted.call.declaration.source_mode is SourceMode.UNTRUSTED
    mixed = FactorCall(
        call=flat_call(party="Alice", source_mode=SourceMode.TRUSTED),
        builder=FlatInstanceBuilder(),
        sector_block_kind=KIND,
    )
    with pytest.raises(MalformedInputError) as raised:
        reduce_factors([mixed, untrusted])
    assert "THE SAME source mode" in str(raised.value)
    # The unmixed list is emitted, which is what makes the refusal about the
    # modes and not about the pair.
    assert reduce_factors([trusted, untrusted]).emission is not None


@pytest.mark.contract
def test_a_tagged_entry_certified_against_another_factors_channel_is_refused() -> None:
    """Row 25 widened: ``constraint_channel_mismatch``, and no new string.

    "A certificate on the joint channel does not license it, and does not
    almost license it", ``lem:party-local`` (iv) exhibiting a channel that
    satisfies the scalar bound of the same entry and VIOLATES the operator one.
    So a tag emitted on a certificate against anything but that factor's own
    channel would assert an operator inequality nothing proves.
    """
    from certiqs_key.reductions.validation import rule_constraint_channel

    alice, bob = _pair(route="licensed")
    emission = reduce_factors([alice, bob]).emission
    assert emission is not None
    # THE TWO STATIONS OF THE TOY PAIR RUN ONE DEVICE MODEL, so their witness
    # IDENTITIES coincide -- which is why the emission decides this row PER
    # FACTOR, against the artefact the entry came from, and asserts the
    # invariant over the joint list afterwards (see `factors._assemble`). The
    # row itself is a function of a declared mapping, and that is what is
    # exercised here: the second factor is given a witness of its own so that
    # "another factor's channel" is a distinguishable thing at all.
    witnesses = {
        emission.factors[0]: emission.channel_witnesses[0],
        emission.factors[1]: "L-f1:fss",
    }
    # Each entry passes against ITS OWN factor's witness.
    for entry in emission.entries:
        assert entry.scope is not None
        own = {entry.scope: entry.certified_against}
        assert rule_constraint_channel(
            (entry,), entry.certified_against, factor_witnesses=own
        ) is None
    # Re-scope one entry to the OTHER factor: same operator, same constant, a
    # certificate against a channel that is not that factor's.
    entry = next(e for e in emission.entries if e.scope == emission.factors[0])
    crossed = ConstraintEntry(
        label=entry.label,
        operator=entry.operator,
        relation=entry.relation,
        constant=entry.constant,
        certificate_kind=entry.certificate_kind,
        certified_against=entry.certified_against,
        theta_typing=entry.theta_typing,
        tag=EntryTag.PARTY_LOCAL,
        scope=emission.factors[1],
    )
    refusal = rule_constraint_channel(
        (crossed,), emission.channel_witnesses[0], factor_witnesses=witnesses
    )
    assert refusal is not None
    assert refusal.reason is RefusalReason.CONSTRAINT_CHANNEL_MISMATCH
    assert "lem:party-local (iv)" in refusal.detail
    # AND A SCOPE THAT NAMES NO DECLARED FACTOR IS REFUSED UNDER THE SAME
    # STRING: a tag names a reading on ONE declared factor's Q_f.
    unknown = ConstraintEntry(
        label=entry.label,
        operator=entry.operator,
        relation=entry.relation,
        constant=entry.constant,
        certificate_kind=entry.certificate_kind,
        certified_against=entry.certified_against,
        theta_typing=entry.theta_typing,
        tag=EntryTag.PARTY_LOCAL,
        scope="Charlie",
    )
    stranger = rule_constraint_channel(
        (unknown,), emission.channel_witnesses[0], factor_witnesses=witnesses
    )
    assert stranger is not None
    assert stranger.reason is RefusalReason.CONSTRAINT_CHANNEL_MISMATCH


@pytest.mark.contract
def test_a_tag_without_its_scope_cannot_be_constructed() -> None:
    """The record refuses the tag and the scope apart (``cor:entries``).

    A MALFORMED RECORD AND NOT A FAIL-CLOSED ROW: no declaration reaches it,
    because the tag is emitted in one place and never declared by a caller.
    What it catches is a producer that tagged an entry without saying which
    factor the operator lives on, which names a reading with no subject.
    """
    alice, bob = _pair(route="licensed")
    emission = reduce_factors([alice, bob]).emission
    assert emission is not None
    entry = emission.entries[0]
    for tag, scope in ((EntryTag.PARTY_LOCAL, None), (None, "f0")):
        with pytest.raises(MalformedInputError):
            ConstraintEntry(
                label=entry.label,
                operator=entry.operator,
                relation=entry.relation,
                constant=entry.constant,
                certificate_kind=entry.certificate_kind,
                certified_against=entry.certified_against,
                theta_typing=entry.theta_typing,
                tag=tag,
                scope=scope,
            )


# ---------------------------------------------------------------------------
#  The factor order, and the party labels that name the factors
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_declared_factor_order_that_disagrees_is_refused() -> None:
    """Row 26 widened: ``alphabet_or_order_mismatch``, validated and not built.

    "THE ORDER OF THE FACTORS agrees with the order the product alphabet and
    the product sector map are read in ... VALIDATED against the declared
    product set and grouping and NEVER CONSTRUCTED IN PLACE OF A MISSING
    DECLARATION."
    """
    alice, bob = _pair()
    agreeing = reduce_factors([alice, bob], declared_factor_order=("f0", "f1"))
    assert agreeing.refusal is None
    swapped = reduce_factors([alice, bob], declared_factor_order=("f1", "f0"))
    assert swapped.emission is None
    assert swapped.refusal is not None
    assert swapped.refusal.reason is RefusalReason.ALPHABET_OR_ORDER_MISMATCH
    assert "declared" in swapped.refusal.detail


@pytest.mark.contract
def test_the_docking_refuses_a_tagged_entry_and_a_non_empty_segment() -> None:
    """A producer cannot silently weaken a tagged row or drop a source link.

    Converting a tagged reduction row through this one-factor adapter would
    hand the consumer an entry it reads as the scalar form -- "the producer's
    to emit and not the consumer's to infer" -- which is strictly weaker in
    untrusted-source mode at ``d_A > 1``. The separate factor adapter carries
    that tag. The chain record carries no slot for a source link's descriptor family,
    obligation record or witness, so docking a non-empty segment would drop what
    ``def:chain``'s admission rule is decided on. BOTH ARE REFUSED AT THE WIRE,
    by raising, as this adapter already refuses a sector-label collision: it
    decides no fail-closed row and adds no refusal string.
    """
    import dataclasses

    from certiqs_key.reductions import docking

    alice, bob = _pair(route="licensed")
    emission = reduce_factors([alice, bob]).emission
    assert emission is not None
    artefact = emission.artefacts[0]
    scoped = [e for e in emission.entries if e.scope == emission.factors[0]]
    tagged = dataclasses.replace(artefact, constraint_list=tuple(scoped))
    with pytest.raises(MalformedInputError) as raised:
        docking.constraint_entries(tagged, sector_block_kind=KIND)
    assert "party_local" in str(raised.value)
    # The untagged artefact converts, which is what makes the refusal about the
    # tag and not about the entry.
    assert docking.constraint_entries(artefact, sector_block_kind=KIND)
    with_source = dataclasses.replace(
        artefact,
        reduction_chain=Chain(
            links=artefact.reduction_chain.links, source_segment=("source-map",)
        ),
    )
    physical = SystemDescriptor(name="B", dim=2, side=Side.RECEIVER)
    with pytest.raises(MalformedInputError) as segment:
        docking.reduction_chain(with_source, physical, sector_block_kind=KIND)
    assert "source segment" in str(segment.value)
    # The empty-segment artefact docks, which is every artefact emitted today.
    assert docking.reduction_chain(
        artefact, physical, sector_block_kind=KIND
    ).source_segment == ()


@pytest.mark.contract
def test_a_factor_scope_is_copied_to_one_factor_chain_entries() -> None:
    """The declared factor label crosses on each transported scalar row."""
    alice, _bob = _pair(route="licensed")
    artefact = reduce_factors([alice]).artefact
    assert isinstance(artefact, ProofReductionArtifact)
    physical = SystemDescriptor(name="station", dim=2, side=Side.RECEIVER)
    chain = docking.reduction_chain(
        artefact,
        physical,
        sector_block_kind=KIND,
        factor_scope="alice_station",
    )
    carried = tuple(
        entry
        for link in chain.receiver_segment
        for entry in link.transported_constraints
    )
    assert carried
    assert {entry.scope for entry in carried} == {"alice_station"}


@pytest.mark.contract
def test_a_repeated_factor_label_cannot_be_emitted() -> None:
    """The factor labels ENUMERATE A SET, because a scope names ONE factor.

    A consumer decides a scope by "A COMPARISON OF A LABEL AGAINST THE FACTOR
    LIST" (``protocol-compiler``'s ``entry_scope_and_tag`` row), so a repeated
    factor label would leave that comparison naming two factors. It is a defect
    of a PRODUCER -- the labels are written by the emission, and the default is
    the position -- so it is refused where the record is built and not by a
    fail-closed row. PARTY labels may repeat, which is the point of the factor
    label, and the test above emits a pair that does.
    """
    alice, bob = _pair(route="licensed")
    emission = reduce_factors([alice, bob]).emission
    assert emission is not None
    with pytest.raises(MalformedInputError):
        type(emission)(
            artefacts=emission.artefacts,
            factors=("f0", "f0"),
            parties=emission.parties,
            sector_map=emission.sector_map,
            family=emission.family,
            entries=emission.entries,
            licence=emission.licence,
            channel_witnesses=emission.channel_witnesses,
        )


@pytest.mark.contract
def test_a_refusing_factor_refuses_the_emission_and_keeps_its_report() -> None:
    """A failure produces a refusal and NO artefact, and the report survives.

    The refusal a caller receives is THE FIRST FACTOR'S IN THE DECLARED ORDER,
    and every factor's verification report is carried whatever happened,
    because a caller diagnosing a refusal reads the report of the factor that
    refused.
    """
    broken = FactorCall(
        call=flat_call(party="Alice", requested_assurance="no-such-tier"),
        builder=FlatInstanceBuilder(),
        sector_block_kind=KIND,
    )
    outcome = reduce_factors([broken, _factor("Bob")])
    assert outcome.emission is None
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.REQUESTED_ASSURANCE_UNKNOWN
    assert len(outcome.outcomes) == 2
    assert outcome.outcomes[0].verification_report is not None
    with pytest.raises(MalformedInputError):
        # The outcome type refuses to hold both, as the core's does.
        type(outcome)(emission=None, outcomes=outcome.outcomes, refusal=None)


# ---------------------------------------------------------------------------
#  The party label of one instance
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_declared_party_label_is_emitted_with_the_sector_map() -> None:
    """``def:reduction-instance`` (I2) and ``thm:emit`` (ii), as one emission.

    "The default stays the default, and it stays Bob's; an instance may in
    addition be declared with ANOTHER PARTY'S LABEL ... every factor of every
    ``H(Q_s)`` is that party's." It is a DECLARED IDENTIFIER, COMPARED AND
    NEVER COMPUTED: the default sentence is the accepted one word for word, and
    a declared label changes that sentence AND NOTHING ELSE IN THE ARTEFACT.
    """
    default = reduce(flat_call(), FlatInstanceBuilder()).artifact
    labelled = reduce(flat_call(party="Alice"), FlatInstanceBuilder()).artifact
    assert default is not None and labelled is not None
    assert default.target_descriptor.party_partition == (
        "default: Bob holds every factor of every H(Q_s)"
    )
    assert "Alice" in labelled.target_descriptor.party_partition
    # DECLARING BOB EXPLICITLY IS THE DEFAULT, not a second spelling of it.
    explicit = reduce(flat_call(party="Bob"), FlatInstanceBuilder()).artifact
    assert explicit is not None
    assert (
        explicit.target_descriptor.party_partition
        == default.target_descriptor.party_partition
    )
    # NOTHING ELSE MOVES: the two records differ in that one field and in the
    # station bindings that name the
    # party (A-MEAS, A-ROUND-SQ, A-SEQ), which a label decides no rule of.
    left = default.as_machine_record()
    right = labelled.as_machine_record()
    differing = [
        key
        for key in left
        if key != "target_descriptor" and left[key] != right[key]
    ]
    assert differing == ["assumption_ledger"]
    named = {"A-MEAS", "A-ROUND-SQ", "A-SEQ"}
    left_rows = {row["assumption_id"]: row for row in left["assumption_ledger"]}  # type: ignore[union-attr,index]
    right_rows = {row["assumption_id"]: row for row in right["assumption_ledger"]}  # type: ignore[union-attr,index]
    assert set(left_rows) == set(right_rows)
    assert {key for key in left_rows if left_rows[key] != right_rows[key]} == named
    assert "Bob's device enters through one POVM" in left_rows["A-MEAS"]["constrains"]
    assert "Alice's device enters through one POVM" in right_rows["A-MEAS"][
        "constrains"
    ]
    assert {
        key
        for key in left["target_descriptor"]  # type: ignore[union-attr,index]
        if left["target_descriptor"][key] != right["target_descriptor"][key]  # type: ignore[index]
    } == {"party_partition"}


# ---------------------------------------------------------------------------
#  The two conditional ledger rows
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_src_is_named_exactly_where_the_source_segment_is_non_empty() -> None:
    """``assumption_ledger.assumed_from_another_module``, the A-SRC presence rule.

    The row is present "whenever the emitted chain's source segment is
    NON-EMPTY", which is the emitted chain and not a datum any rule re-derives;
    every artefact emitted today has an empty segment, so the row is absent
    from every one of them. A-SEQ is unconditional and is there either way.
    """
    artefact = reduce(flat_call(), FlatInstanceBuilder()).artifact
    assert artefact is not None
    empty = artefact.reduction_chain
    assert empty.source_segment == ()
    rows = {row.identifier for row in emitted_assumption_rows(empty)}
    assert "A-SEQ" in rows
    assert "A-SRC" not in rows
    assert "A-NOSRC" not in rows
    # THE SAME CHAIN WITH A DECLARED SOURCE SEGMENT, which is what the
    # transmitter's type carries today: a tuple of declared source-link kinds.
    with_source = Chain(links=empty.links, source_segment=("source-map",))
    named = {row.identifier for row in emitted_assumption_rows(with_source)}
    assert named - rows == {"A-SRC"}
    # AND THE COMPOSITE IS THE PAIR EITHER WAY (def:chain, eq:chaincomposite):
    # the source composite is the IDENTITY where the segment is empty, and the
    # second member is the receiver composite thm:chain (i)-(iv) read.
    source, receiver = empty.composite()
    assert receiver.identity == empty.composite_witness().identity
    assert source.identity == empty.source_composite_witness().identity
    assert "source-map" in str(with_source.composite()[0].as_machine_record())


@pytest.mark.contract
def test_the_emitted_chain_record_carries_the_pair_and_an_empty_segment() -> None:
    """The segment is EMITTED EMPTY RATHER THAN OMITTED (``link_record``).

    "presence: always emitted; EMPTY in every artefact emitted today", and
    "the segment is emitted EMPTY rather than omitted, SO THAT A CONSUMER READS
    A SEGMENT AND NOT A SILENCE". So every emitted chain record carries both
    members of the pair ``eq:chaincomposite``: the source composite is the
    IDENTITY at ``L_s = 0`` and says so in its own equation, and the receiver
    composite is what ``thm:chain`` (i)-(iv) read and what version 1 carried
    slot for slot and number for number.
    """
    artefact = reduce(flat_call(), FlatInstanceBuilder()).artifact
    assert artefact is not None
    chain_record = artefact.as_machine_record()["reduction_chain"]
    assert isinstance(chain_record, dict)
    assert set(chain_record) == {
        "order",
        "composite_witness",
        "links",
        "source_segment",
        "source_composite_witness",
    }
    assert chain_record["source_segment"] == []
    source = chain_record["source_composite_witness"]
    assert isinstance(source, dict)
    assert "Xi_Chain = id" in str(source["equation"])
    # AND THE RECEIVER HALF IS UNTOUCHED: the keys, the order and the links are
    # the ones version 1 emitted.
    assert chain_record["order"] == list(artefact.reduction_chain.composite_order())
    assert chain_record["composite_witness"] == (
        artefact.reduction_chain.composite_witness().as_machine_record()
    )


@pytest.mark.contract
def test_the_joint_licence_names_a_supplier_fact_only_where_one_is_read() -> None:
    """req:licence-record over the joint list: derived from the per-entry discharges.

    The record-wide ``discharging_receiver_fact`` and ``receiver_spec_version``
    and each party-local row's fact and version are read off the discharges
    the factors' own licences name: with the first factor's discharges made
    supplier-free, the record-wide version names the second factor alone and
    the first factor's rows name no fact; with both supplier-free, none is
    named anywhere. A factor whose licence names no discharge for an entry
    refuses the joint list ``licence_missing``.
    """
    from dataclasses import replace

    factors = _pair(route="licensed")
    original = reduce_factors(factors)
    assert original.emission is not None
    artefacts = original.emission.artefacts

    def supplier_free(artefact: ProofReductionArtifact) -> ProofReductionArtifact:
        licence = artefact.attack_set_license
        assert licence is not None
        return replace(
            artefact,
            attack_set_license=replace(
                licence,
                discharge_per_entry=tuple(
                    replace(item, supplier_fact=None, supplier_version=None)
                    for item in licence.discharge_per_entry
                ),
                discharging_receiver_fact=None,
                receiver_spec_version=None,
            ),
        )

    first, second = original.emission.factors
    half = assemble_factor_emissions(
        factors, (supplier_free(artefacts[0]), artefacts[1])
    )
    assert not isinstance(half, Refusal)
    licence = half.licence
    assert licence is not None
    assert licence.discharging_receiver_fact is not None
    assert licence.receiver_spec_version is not None
    assert second in licence.receiver_spec_version
    assert first not in licence.receiver_spec_version
    for row in licence.party_local_entries:
        if row.factor == first:
            assert row.discharging_receiver_fact is None
            assert row.factor_spec_version is None
        else:
            assert row.discharging_receiver_fact is not None
            assert row.factor_spec_version is not None

    none = assemble_factor_emissions(
        factors, tuple(supplier_free(artefact) for artefact in artefacts)
    )
    assert not isinstance(none, Refusal)
    assert none.licence is not None
    assert none.licence.discharging_receiver_fact is None
    assert none.licence.receiver_spec_version is None
    assert all(
        item.supplier_fact is None for item in none.licence.discharge_per_entry
    )

    licence_0 = artefacts[0].attack_set_license
    assert licence_0 is not None
    misnamed = replace(
        artefacts[0],
        attack_set_license=replace(
            licence_0,
            discharge_per_entry=tuple(
                replace(item, entry=item.entry + " (another)")
                for item in licence_0.discharge_per_entry
            ),
        ),
    )
    refused = assemble_factor_emissions(factors, (misnamed, artefacts[1]))
    assert isinstance(refused, Refusal)
    assert str(refused.reason) == "licence_missing"
