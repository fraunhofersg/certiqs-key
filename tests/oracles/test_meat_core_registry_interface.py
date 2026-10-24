"""The frozen registry, the claim files, interface.yaml and the code agree.

ONE TEST PER ABSENT GROUP. An earlier arrangement bound this
registry to a single interface transcription and to a
``contract.tex`` pinned by content hash; neither document exists here and
neither will (PRINCIPLES.md section 2.5: git plus human review is the ledger,
and there is no second one). EIGHTEEN such tests are absent and the
header of ``test_registry_integrity.py`` lists them with its reason for each.
What is re-establishable against THIS repository's artefacts -- the 74 claim
files under ``spec/modules/meat-core/claims/``, the eleven under
``frank-wolfe/claims/`` and the two ``interface.yaml`` beside them -- is here.

WHAT EACH CATCHES: a claim label, a ledger row, a machine key, a refusal
string, a threshold row or a recorded parameter that exists on one side of the
boundary and not on the other. The compiler's and reductions' registries make the
same call for the same reason and their files say so in the same words
(``test_protocol_compiler_registry_interface.py``,
``test_reductions_registry_interface.py``).

WHAT IS DIFFERENT HERE, AND IT IS THE POINT. The frozen registry
was authored against a contract whose claims are numbered ``C1``..``C22`` and
whose declared-tolerance apparatus is retired; this module's claims are
labelled and the apparatus is gone. THE REGISTRY IS NOT EDITED. Every test
below states the mapping explicitly -- which frozen number resolves to which
claim label (read from ``claim_codes.yaml``, the one table where the
oracle codes meet this repository's claim ids), which frozen string is
retired and where the retirement is recorded -- so that a reader can see where
each went rather than infer it from a silence.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import claim_codes
import pytest
import registry
import yaml

from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    INHERITED_KEYS,
    INHERITED_NEVER_VERIFIED_KEYS,
    NEVER_VERIFIED,
    RETIRED_ASSUMPTION_IDS,
    RETIRED_REFUSAL_REASONS,
    AssuranceReason,
    RefusalReason,
    assumption_ledger,
)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "spec" / "modules" / "meat-core"
CLAIMS = SPEC / "claims"
INTERFACE = SPEC / "interface.yaml"
SUBMODULE = SPEC / "frank-wolfe"
SUBMODULE_CLAIMS = SUBMODULE / "claims"
SUBMODULE_INTERFACE = SUBMODULE / "interface.yaml"

#: THE ORACLE'S NUMBERED CLAIMS, AND WHERE EACH ONE'S MATHEMATICS IS IN
#: THIS REPOSITORY. The numbering was a section numbering; this
#: repository labels a claim and the label is its identity
#: (spec/claim-format.md). A registry entry pinning ``C8`` is pinning the
#: reduction to the block-diagonal feasible set, which is ``thm:reduction``
#: here, and ``claim_codes.yaml`` is what says so: this table is its meat-core
#: rows, as labels of this module.
#:
#: FOUR OF THE ORACLE'S NUMBERS RESOLVE TO NOTHING, and each is disposed of
#: on a stated ground rather than left as a gap: ``C13`` and ``C18``-``C20``
#: were the numerical lower-bound certificate, which the contract's
#: 1.0.0 deleted and which this repository does not build in any form
#: (PRINCIPLES.md section 10). Every registry entry naming one is MARKED in the
#: frozen file, which ``test_registry_integrity.py`` checks.
#: The oracle's meat-core lies in two modules: its quantum-information
#: preliminaries are in foundations, so
#: this table maps each number onto full claim ids of either.
WHERE_EACH_NUMBER_WENT: dict[str, tuple[str, ...]] = claim_codes.labels(
    "C", ("meat-core", "foundations")
)

#: The submodule's, kept apart because the labels live in another directory and
#: the coupling is two core claims and no more (core = program + formulation;
#: submodule frank-wolfe).
WHERE_C22_WENT: tuple[str, ...] = claim_codes.labels("C", "meat-core/frank-wolfe")[
    "C22"
]

#: The numbers that resolve to no claim of this repository (``no_claim`` in
#: ``claim_codes.yaml``). See above.
DROPPED_WITH_THE_THIRD_RUNG: frozenset[str] = frozenset(claim_codes.no_claim("C"))

#: TWO DELTAS AGAINST THE FROZEN REGISTRY, READ AGAINST THE INTERFACE:
#: A-SOUND moved to ``reductions/ass:sound`` and the
#: vacuous corner is refused with a named reason. THE ASSERTIONS BELOW ARE
#: EXACT EQUALITIES and no tolerated difference is left standing. A-SOUND is
#: RETIRED: no ledger carries it, and the test below
#: asserts that the inherited rows do not name it.
A_SOUND_MOVED_TO_REDUCTIONS: frozenset[str] = frozenset({"A-SOUND"})
VACUOUS_CORNER_REFUSAL: frozenset[str] = frozenset({"security_statement_vacuous"})


def _document(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        document: dict[str, Any] = yaml.safe_load(handle)
    return document


def _claim_ids(directory: Path, module: str) -> set[str]:
    """Return every claim id declared under ``module``, from the files."""
    ids: set[str] = set()
    for path in sorted(directory.glob("*.tex")):
        match = re.search(
            rf"^% id: {re.escape(module)}/(?P<id>\S+)$",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        assert match is not None, path.name
        ids.add(match.group("id"))
    return ids


def submodule_withdrawals() -> tuple[str, ...]:
    """Return every withdrawal string the SUBMODULE interface declares.

    The frozen spellings it carries; the file coins none of its own. Read
    from the submodule file rather than from the core's summary, because that
    file is the authority and the summary is a snapshot of it.
    """
    table = _document(SUBMODULE_INTERFACE)["withdrawal_reasons"]
    # A list of the file's own spellings would be strings the registry does
    # not freeze; its absence is part of what this reads.
    assert "this_files_own_spelling" not in table, sorted(table)
    return tuple(table["frozen_spellings"])


def test_every_oracle_claim_number_resolves_to_a_claim_of_this_repository() -> None:
    """Traceability, re-established through the labels the numbers became.

    THE ABSENT TEST read a ``claims:`` block of an earlier interface and
    asserted that every number a registry entry names was in it. There is no
    such block here: the claims ARE the files, and the command that computes a
    fact about them is ``python -m harness.check_claims`` (spec/claim-format.md
    section 4). So the traceability is asserted through
    :data:`WHERE_EACH_NUMBER_WENT`, which maps each frozen number onto the claim
    labels that carry its mathematics, and every label on the right-hand side is
    read out of the claim files themselves.
    """
    core = {f"meat-core/{label}" for label in _claim_ids(CLAIMS, "meat-core")} | {
        f"foundations/{label}"
        for label in _claim_ids(ROOT / "spec" / "modules" / "foundations" / "claims",
                                "foundations")
    }
    submodule = _claim_ids(SUBMODULE_CLAIMS, "meat-core/frank-wolfe")
    for number, labels in WHERE_EACH_NUMBER_WENT.items():
        for label in labels:
            assert label in core, (number, label)
    for label in WHERE_C22_WENT:
        assert label in submodule, label

    named = {claim for entry in registry.ORACLES for claim in entry.claims}
    covered = set(WHERE_EACH_NUMBER_WENT) | {"C22"} | DROPPED_WITH_THE_THIRD_RUNG
    assert named <= covered, sorted(named - covered)
    # AND THE FOUR THAT RESOLVE TO NOTHING RESOLVE TO NOTHING ON BOTH SIDES:
    # neither module has a claim for the deleted certificate chain, which is
    # what makes the frozen marks on those entries the honest disposition.
    for number in DROPPED_WITH_THE_THIRD_RUNG:
        assert number not in WHERE_EACH_NUMBER_WENT


def test_the_interface_carries_the_ledger_the_code_emits() -> None:
    """The assumption ledger, row for row, key for key, on both sides.

    THE ABSENT TEST asserted that the assumption ids the toys use were the ones
    an earlier interface listed, against a ledger of fourteen ids of this
    module's own. Four are inherited by machine key ("Merge four, rename one,
    licence under A-ATK in the compiler"), and the
    submodule owns one. What
    this asserts is that the enum, the machine keys and the never-verified sets
    in the code are exactly the interface's.
    """
    ledger = _document(INTERFACE)["assumption_ledger"]
    own = {row["id"]: row for row in ledger["own_rows"]}
    assert set(own) == {str(member) for member in ASSUMPTION_MACHINE_KEYS}
    for identifier, row in own.items():
        key = next(
            value
            for member, value in ASSUMPTION_MACHINE_KEYS.items()
            if str(member) == identifier
        )
        assert row["machine_key"] == key, identifier
    # A-PUR and A-DIM are both retired (implied by def:hqkd-list); the
    # retirement is recorded where the frozen ids are.
    assert "A-PUR" not in own
    assert RETIRED_ASSUMPTION_IDS["A-DIM"].startswith("renamed A-PUR")
    # THE FIVE RETIRED: no own row, no member, each with its fate.
    for retired in ("A-DECL", "A-MARG", "A-PUR", "A-ACC", "A-BLOCK"):
        assert retired not in own
        assert retired in RETIRED_ASSUMPTION_IDS
    # A-EVE-DIM IS SUPERSEDED (ass:eve-dim): no own row, no member, its key
    # kept among the interface's unemitted rows for the claim-closure table,
    # and its fate recorded where the other retired ids are. A-SEPARATE is
    # unemitted too but live, so it is no retired id.
    unemitted = {
        row["id"]: row["machine_key"] for row in ledger["unemitted_rows"]["rows"]
    }
    assert unemitted["A-EVE-DIM"] == "adversary_registers_finite"
    assert "A-EVE-DIM" not in own
    assert "A-EVE-DIM" not in {str(member) for member in ASSUMPTION_MACHINE_KEYS}
    assert "adversary_registers_finite" not in ASSUMPTION_MACHINE_KEYS.values()
    assert "A-EVE-DIM" in RETIRED_ASSUMPTION_IDS
    assert "A-SEPARATE" in unemitted
    assert "A-SEPARATE" not in RETIRED_ASSUMPTION_IDS
    assert set(unemitted).isdisjoint(own)

    inherited = {row["id"]: row for row in ledger["inherited_rows"]["rows"]}
    assert set(inherited) == set(INHERITED_KEYS)
    for identifier, row in inherited.items():
        assert row["machine_key"] == INHERITED_KEYS[identifier], identifier
    # THE ROW MOVED TO REDUCTIONS IS RETIRED: neither the interface nor the
    # code inherits it, and the retirement is recorded where the frozen ids
    # are.
    assert set(A_SOUND_MOVED_TO_REDUCTIONS) & set(inherited) == set()
    assert "A-SOUND" not in INHERITED_KEYS
    assert "A-SOUND" in RETIRED_ASSUMPTION_IDS

    never = _document(INTERFACE)["never_verified"]
    assert [str(member) for member in NEVER_VERIFIED] == never["own"]
    # AND THE OBLIGATION IS STILL NEVER-VERIFIED, on the other side:
    # an inherited supplier obligation is no more decidable here than an own one
    # was, which is why the row left one list and went into
    # the other rather than out of both.
    assert set(INHERITED_NEVER_VERIFIED_KEYS) == {
        inherited[identifier]["machine_key"] for identifier in never["inherited"]
    }
    # RE-DERIVED BY HAND from the amended interfaces: meat-core's
    # assumption_ledger reads "submodule_rows: []" with the note "The submodule
    # emits no row. Its one assumption, A-LMO (frank-wolfe/ass:lmo), is
    # superseded", and
    # never_verified reads "submodule: []"; the frank-wolfe interface keeps the
    # row {id: A-LMO, machine_key: exact_linear_oracle} with the emission rule
    # "on no run". The code emits it on no run either. Old expectation: one
    # submodule row, A-LMO under exact_linear_oracle, never verified.
    assert ledger["submodule_rows"] == []
    assert never["submodule"] == []
    submodule_ledger = _document(SUBMODULE_INTERFACE)["assumption_ledger"]
    assert submodule_ledger["rows"] == [
        {"id": "A-LMO", "machine_key": "exact_linear_oracle"}
    ]
    assert submodule_ledger["emission_rule"]["A-LMO"].startswith("on no run")
    for first_order in (True, False):
        emitted = assumption_ledger(
            trusted_source=True,
            alice_dim=2,
            alice_party="A",
            constraint_entries=1,
            key_length_wanted=True,
            key_length_reported=first_order,
            first_order=first_order,
        )
        assert "exact_linear_oracle" not in emitted

    # NO ROW IS DISCHARGED ANY MORE: A-BLOCK became the compiler's remark
    # rem:block-restriction, which thm:reduction step 1 proves.
    assert "discharged_rows" not in ledger
    assert "discharged_rather_than_verified" not in never


def test_no_ledger_names_the_retired_a_sound_and_a_atk_keeps_its_rule() -> None:
    """A-SOUND is retired; the attack-set licence fires on its own rule.

    This test once pinned the inherited ``constraints_sound`` row to its
    owner's scope: non-empty list AND entries
    that came through a reductions chain. The row retired with A-SOUND: the
    soundness of every entry reductions emits is a conclusion of that module's
    theorems (``reductions/rem:sound-and-atk``), and inside the security chain
    A-ATK implies it (``lem:range`` (i)). What stays is A-ATK's rule, which
    never read the provenance: it fires on a non-empty list where a key length
    is wanted, and nowhere else.
    """

    def ledger(*, entries: int, wanted: bool) -> tuple[str, ...]:
        return assumption_ledger(
            trusted_source=True,
            alice_dim=2,
            alice_party="A",
            constraint_entries=entries,
            key_length_wanted=wanted,
            key_length_reported=wanted,
            first_order=True,
        )

    empty = ledger(entries=0, wanted=True)
    licensed = ledger(entries=1, wanted=True)
    numerical_only = ledger(entries=1, wanted=False)
    for keys in (empty, licensed, numerical_only, ledger(entries=3, wanted=True)):
        assert "constraints_sound" not in keys
    assert INHERITED_KEYS["A-ATK"] in licensed
    assert INHERITED_KEYS["A-ATK"] not in empty
    assert INHERITED_KEYS["A-ATK"] not in numerical_only
    # THE OWN ROWS COME FIRST, then the inherited: A-ATK sits after the last
    # own row rather than among them.
    # A-LAB's row is
    # emitted once per party, so the own rows are read once each.
    own = [ASSUMPTION_MACHINE_KEYS[member] for member in ASSUMPTION_MACHINE_KEYS]
    first = licensed.index(INHERITED_KEYS["A-ATK"])
    assert tuple(dict.fromkeys(licensed[:first])) == tuple(own)
    # AND THE LIST ENGAGES THAT ONE KEY ALONE.
    assert set(licensed) - set(empty) == {INHERITED_KEYS["A-ATK"]}


def test_the_refusal_vocabulary_is_the_frozen_one_minus_what_was_retired() -> None:
    """The strings, on both sides of the boundary and against the frozen list.

    THE ABSENT TESTS asserted that the seventeen frozen reason strings
    were the interface's and that one of them had been renamed with its datum.
    NINE SURVIVE and one spelling is the interface's own; EIGHT ARE RETIRED,
    seven with the declared-tolerance apparatus and one with the
    request row. NONE IS REUSED AND NONE IS RESPELLED, and that is what this
    asserts -- against the frozen vocabulary, which is not edited.
    """
    document = _document(INTERFACE)
    reasons = document["refusal_reasons"]
    carried = set(reasons["frozen_spellings"]["core"])
    carried |= set(reasons["frozen_spellings"]["submodule"])
    own_spellings = set(reasons["this_files_own_spelling"])
    retired = {row["reason"] for row in reasons["retired"]["rows"]}

    # THE PARTITION OF THE FROZEN SEVENTEEN IS EXACT: every one is either
    # carried or retired, and nothing is in both.
    frozen = set(registry.REASON_VOCABULARY_1_0_0)
    assert carried | retired == frozen
    assert not (carried & retired)
    assert not (own_spellings & frozen)
    assert "declaration_not_exactly_admissible" in own_spellings

    # THE CODE SPELLS THE CARRIED ONES AND THE INTERFACE'S OWN, AND NO OTHER --
    # BESIDE THE VACUOUS-CORNER STRING, WHICH IS SUBTRACTED FROM BOTH SIDES AND
    # ASSERTED ON ITS OWN below.
    live = {str(member) for member in RefusalReason}
    live |= {str(member) for member in AssuranceReason if str(member) in frozen}
    assert live == carried | own_spellings
    # THE VACUOUS-CORNER STRING IS SPELLED BY THE CODE, is in neither the frozen
    # vocabulary nor the retired list, and is not a respelling of either: it
    # names a state the frozen vocabulary had no name for because it reported a
    # key length there ("Gate: refuse the corner with a named reason").
    assert live >= VACUOUS_CORNER_REFUSAL
    assert own_spellings >= VACUOUS_CORNER_REFUSAL
    assert not (VACUOUS_CORNER_REFUSAL & frozen)
    assert not (VACUOUS_CORNER_REFUSAL & set(RETIRED_REFUSAL_REASONS))
    # AND EVERY OTHER STRING THE CODE CAN EMIT IS DISCLOSED IN ONE OF THE THREE
    # BLOCKS. A string a run record carries and no table lists is a reason a
    # consumer cannot look up; the implementation block is where the four that
    # are neither refusals nor withdrawals are named.
    implementation = {
        row["reason"]
        for row in reasons["implementation_reasons_beside_the_vocabulary"]["rows"]
    }
    every_emitted = {str(member) for member in AssuranceReason} | {
        str(member) for member in RefusalReason
    }
    documented = carried | own_spellings | implementation
    documented |= set(submodule_withdrawals())
    assert every_emitted <= documented, sorted(every_emitted - documented)
    # AND THE RETIRED ONES ARE NAMED IN THE CODE AS RETIRED, so that a reader of
    # the frozen record finds them disposed of rather than missing. The
    # code's list is the interface's PLUS one the interface never carried:
    # `acceptance_geometry_unsupported` was the frozen spelling of a
    # withdrawal for an unread geometry, which no run reaches because
    # frank-wolfe/req:acceptance-geometries refuses that geometry at admission.
    assert set(RETIRED_REFUSAL_REASONS) == retired | {"acceptance_geometry_unsupported"}
    assert not (set(RETIRED_REFUSAL_REASONS) & live)


def test_the_declared_thresholds_are_the_interface_rows_and_group_a_has_no_window() -> (
    None
):
    """Every threshold row, under its machine key, on both sides.

    THE ABSENT TEST asserted the frozen tolerance surface against an earlier
    interface: which row was at ``tau_num``, which were at exactly zero, and
    which were retired. THERE IS NO ROW AT A TOLERANCE, and the
    inventory is the interface's ``declared_thresholds``.
    """
    groups = _document(INTERFACE)["declared_thresholds"]
    group_a = {row["machine_key"] for row in groups["group_a_declared_data"]["rows"]}
    assert {row.key for row in thresholds.GROUP_A} == group_a
    # EVERY GROUP A ROW IS DECIDED EXACTLY AND CARRIES NO WINDOW, which the
    # interface states row by row and the code states once, in the values.
    for row in groups["group_a_declared_data"]["rows"]:
        assert "window" not in row, row["machine_key"]
        assert row["decided"].startswith("exactly")
    assert {row.value for row in thresholds.GROUP_A} == {0.0}

    group_b = {row["machine_key"] for row in groups["group_b_computed_objects"]["rows"]}
    submodule_b = set(
        groups["group_b_computed_objects"]["rows_the_submodule_declares"]["keys"]
    )
    # THE GROUP B ROWS ARE SPLIT ACROSS THE TWO INTERFACES and the code carries
    # them in one table, which is what the one-to-one carrying rule needs.
    carried = {row.key for row in thresholds.GROUP_B}
    assert group_b | submodule_b <= carried
    # The one row beyond them is `limit_membership`, which the interface retires
    # CONDITIONALLY and this implementation keeps because it runs the oracle.
    assert carried - (group_b | submodule_b) == {"limit_membership"}
    assert "limit_membership" in thresholds.RETIRED_UNLESS_CARRIED

    retired = {row["machine_key"] for row in groups["group_c_retired"]["rows"]}
    # ``limit_membership`` IS IN THE INTERFACE'S GROUP C AND IS LIVE HERE, and
    # the disposition is the interface's own conditional: an implementation that
    # does not run the alpha -> 1 oracle carries neither, and ONE THAT DOES
    # declares it as a Group B number. This one runs the oracle, so the row is
    # live and the ground is kept beside the live rows rather than dropped.
    assert set(thresholds.RETIRED) == retired - {"limit_membership"}
    assert set(thresholds.RETIRED_UNLESS_CARRIED) == {"limit_membership"}
    # And the one-to-one carrying rule is executed rather than described, over
    # EVERY live row of both groups.
    assert set(thresholds.carrying_table()) == {row.key for row in thresholds.LIVE}
    assert {row.key for row in thresholds.LIVE} == group_a | carried


def test_the_submodule_interface_owns_the_withdrawals() -> None:
    """The four withdrawal strings are the submodule's, on both sides.

    THE ABSENT TEST asserted the withdrawal vocabulary and the two-rung ladder
    against a single interface. They are two files here, and
    the point of the split is that deleting the submodule deletes its rows and
    nothing of the core's. So the assertion is on the SEAM: the core
    interface names the submodule's rows as the submodule's, and the submodule
    interface carries them.
    """
    core = _document(INTERFACE)
    entry = core["submodules_today"]["frank-wolfe"]
    assert entry["removable"] is True
    assert entry["docks_at"] == ["lem:estimate", "cor:keylength-bound"]
    # THE WHOLE OF THE COUPLING IS TWO CORE CLAIMS, and both are claim files.
    assert set(entry["docks_at"]) <= _claim_ids(CLAIMS, "meat-core")

    # FOUR, THE FROZEN VOCABULARY'S WITHDRAWALS AND NO OTHER. RE-DERIVED BY
    # HAND from the core interface's submodules_today.frank-wolfe row,
    # "withdrawal_reasons: [gradient_hypothesis_positivity,
    # gradient_hypothesis_support, gradient_perturbation_applied,
    # iterate_not_feasible]"; from req:first-order-withdrawal, which withdraws
    # for no status of the oracle; and from req:acceptance-geometries, which
    # refuses an unread geometry at admission, so no withdrawal names one.
    # Old expectations: six, with oracle_not_optimal fifth; then five, with
    # the submodule file's own spelling for an unread geometry fifth.
    withdrawals = tuple(entry["withdrawal_reasons"])
    assert withdrawals == registry.FO_WITHDRAWAL_REASONS
    assert set(withdrawals) == set(submodule_withdrawals())
    # EVERY STRING THE SUBMODULE INTERFACE SPELLS IS ONE THE CODE CAN EMIT: a
    # string a contract documents and no code path produces is a reason a
    # consumer greps a record for in vain.
    emitted = {str(member) for member in AssuranceReason}
    assert set(submodule_withdrawals()) <= emitted, sorted(
        set(submodule_withdrawals()) - emitted
    )
    # RE-DERIVED BY HAND: the same row now reads
    # "ledger_rows: []", A-LMO being superseded. Old expectation: one row,
    # never verified.
    assert entry["ledger_rows"] == []

    submodule = _document(SUBMODULE_INTERFACE)
    assert submodule["module_id"] == "meat-core/frank-wolfe"
    assert set(entry["threshold_rows"]) <= {
        row.key for row in thresholds.GROUP_B
    }


def test_the_two_live_rungs_are_the_frozen_ones_and_there_is_no_third() -> None:
    """The ladder, and the dropped rung named as dropped on both sides.

    THE REMOVED TEST asserted that the enum kept the shelved third name so that
    nothing re-used the string, and that a request for it was refused. The rung
    is carried in NO FORM here (PRINCIPLES.md section 10) and the request row is
    retired with it, so what is asserted instead is that neither the tier name
    nor its refusal string appears anywhere this module emits.
    """
    from certiqs_key.foundations.assurance import Assurance

    assert tuple(str(member) for member in Assurance) == registry.ASSURANCE_VALUES_1_0_0
    # def:tiers (iii) as amended: the name is the live third label.
    assert registry.SHELVED_TIER_NAME in {str(member) for member in Assurance}
    assert registry.SHELVED_TIER_REFUSAL in RETIRED_REFUSAL_REASONS
    document = _document(INTERFACE)
    retired = {row["name"] for row in document["retired_parameter_rows"]}
    assert "requested_assurance" in retired
    # AND THE INTERFACE SAYS THE SAME IN ITS OWN ROW: the tier is ACHIEVED.
    tier_row = next(
        row for row in document["outputs"] if row["name"] == "reported_tier"
    )
    assert "estimate" in tier_row["domain"]
    assert "first-order" in tier_row["domain"]


def test_the_parameters_are_the_seven_the_interface_records() -> None:
    """The free numerical parameters, and that a tolerance is not among them.

    THE ABSENT TEST checked the frozen ``alpha`` domain and its declared
    tolerance domain against an earlier interface. The tolerance row is retired; what
    remains is the parameters and the interface's statement, in terms, that
    there is no other free number. ``eps_auth`` and ``k_auth``, the parameters of
    ``ass:auth`` that ``cor:composed-security`` (iii) composes, joined the five.
    """
    document = _document(INTERFACE)
    parameters = {row["name"] for row in document["parameters"]["rows"]}
    assert parameters == {
        "alpha", "eps_pa", "eps_ev", "lambda_ec", "eps_auth", "k_auth",
        "purifier_dim",
    }
    assert document["parameters"]["tolerances"].startswith("NONE")
    retired = {row["name"] for row in document["retired_input_rows"]}
    assert retired == {"declared_tolerance"}
    # EVERY ALPHA THE REGISTRY PINS LIES IN THE STRUCTURAL DOMAIN, which is the
    # half of the removed test that still has a subject.
    for value in registry.ALPHA_GRID:
        assert 1.0 < value < 2.0
