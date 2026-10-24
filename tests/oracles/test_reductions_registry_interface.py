"""The frozen registry, the interface files, the claim files and the code agree.

The frozen registry was once bound to one ``interface.yaml`` and one contract
document with thirty tests; those thirty are absent, and the header of
``test_reductions_registry.py`` records the reasons. The registry is bound here
to the claim files and the ``interface.yaml`` files.

EIGHT ARE RE-ESTABLISHED AND ARE HERE, one per absent test, under the name
the absent one had. What each catches: a reason string, a row order, an output
key, a link kind, a ledger row, a claim id or a rounding rule that exists on
one side of the boundary and not on the other.

THE OTHER TWENTY-TWO STAY ABSENT, with their reasons in the header of
``test_reductions_registry.py``: they read keys the three interface files
DELIBERATELY RETIRE -- the interface delta blocks, the change-request
candidates, the open implementation choices, the provenance recount, the
accepted-contract pin, the declared operator tolerance, the wire-form
comparison, the locator residues, the keyed deferral block and the two
file-name scans.

THE MODULE WITHOUT ITS REMOVABLE SUBMODULE is what is checked here: the core
plus ``wpfss`` and ``domination``, which is the module of every tree, the
public one included. The frozen record still names what the removable
submodule owned (the record is never edited): its refusal string, its row's
order, its ledger rows and its labels are named below where the counts set
them apart. Where the submodule is in the tree, its own test file adds its
half back and checks the whole (its ``removability`` block names that file).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import registry_reductions as core
import yaml

SPEC = Path(__file__).resolve().parents[2] / "spec" / "modules" / "reductions"
ROOT = Path(__file__).resolve().parents[2]

#: The interface files of the module without its removable submodule.
FILES: dict[str, Path] = {
    "reductions": SPEC / "interface.yaml",
    "wpfss": SPEC / "wpfss" / "interface.yaml",
    "domination": SPEC / "domination" / "interface.yaml",
}

#: THE ``domination`` SUBMODULE'S ROWS AND STRINGS, added after the freeze
#: (rows 29 and 30, ``domination_weights_ill_formed``
#: and ``domination_not_carried``) and RETIRED with the certified
#: snap: its interface declares no input, no output and no refusal row now, so
#: the live side equals the frozen one again. Kept as a name so that a row of
#: it coming back fails here.
DOMINATION_ROWS_RETIRED: tuple[str, ...] = ("domination_weights", "domination_strict")
DOMINATION_STRINGS_RETIRED = frozenset(
    {"domination_weights_ill_formed", "domination_not_carried"}
)

#: THE ROW AND THE STRING ADDED SINCE THE FREEZE, named here rather than edited
#: into the frozen record (an oracle is never regenerated from the code it
#: tests, PRINCIPLES.md section 2.3): ``wpfss``'s ``normalized_branch`` row at
#: the next free order, 29, and its one string
#: (``wpfss/req:normalized-branch-refusal``, reductions 0.18.0).
FAIL_CLOSED_ROWS_ADDED_SINCE_THE_FREEZE: dict[str, int] = {"normalized_branch": 29}
STRINGS_ADDED_SINCE_THE_FREEZE = frozenset({"normalized_receiver_in_branch"})

#: The ONE rename of the freeze, recorded in the core interface's
#: ``requested_assurance`` row: the shelved tier is dropped entirely
#: (PRINCIPLES.md section 10), so the row's subject is a tier that is not live.
RENAMED = {"requested_assurance_shelved": "requested_assurance_unknown"}

#: Labels the frozen registry names that resolve to no claim file of this
#: repository, each with the reason. NOTHING ELSE MAY BE ABSENT.
#:
#: * ``ass:decl`` is ``meat-core`` 1.0.0's, which is not a claim file here; the
#:   claim files cite it in text for the same reason (thm:emit (ii)).
#: * the nine ``tol``-era labels are the DECLARED OPERATOR TOLERANCE's,
#:   superseded at proof-reductions 1.0.0 when the tolerance was removed and
#:   the conditions it hypothesized became decisions. The registry records them
#:   as history, which is what a frozen record is for.
FOREIGN_OR_SUPERSEDED = frozenset(
    {
        "ass:decl",
        # Its setting half is def:system-setting; its adversary half is no
        # claim (meat-core/ass:eve-dim is superseded). The frozen record's
        # prose keeps the label, as it keeps the other superseded ones.
        "ass:dim",
        "ass:optol",
        "cor:tolentries",
        "def:tolerance",
        "lem:tolprop",
        "prop:tolrows",
        "rem:consumerdisposition",
        "rem:tolboundary",
        "rem:tolscope",
        "thm:tolerance",
    }
)

#: Labels of the removable submodule, which the frozen core record's prose
#: names: without the submodule they are the record's history, as the rest of
#: that prose is (that they resolve where it is present is its own file's
#: check).
REMOVED_LABELS_IN_THE_CORE_RECORD = frozenset(
    {"ass:blind", "def:blindmodel", "rem:paddednotemitted", "thm:blinding"}
)
#: The probe-conditioning claims the core record's prose names: the frozen
#: record names the receiver theorems the weight route imported for a probe,
#: which the removable probe-conditioning submodule states and takes with it.
PROBE_LABELS_IN_THE_CORE_RECORD = frozenset(
    {"thm:channel-block-diagonal", "thm:conditional-povm"}
)
PROBE_SPEC_PRESENT = (
    ROOT / "spec" / "modules" / "receiver" / "probe-conditioning"
).is_dir()

_LABEL = re.compile(r"\b(?:def|thm|lem|prop|cor|rem|ass|ex):[A-Za-z0-9-]+")


def _load(name: str) -> dict[str, Any]:
    return dict(yaml.safe_load(FILES[name].read_text(encoding="utf-8")))


def _registry_text() -> str:
    return Path(core.__file__).read_text(encoding="utf-8")


def _declared_reasons() -> list[str]:
    return [
        reason
        for name in FILES
        for reason in _load(name).get("fail_closed", {}).get("refusal_reasons", [])
    ]


def removable_rules() -> set[str]:
    """Return the fail-closed rows the present removable submodules declare."""
    return {
        row["rule"]
        for path in SPEC.glob("*/interface.yaml")
        for document in [yaml.safe_load(path.read_text(encoding="utf-8"))]
        if "removability" in document
        for row in document.get("fail_closed", {}).get("rows", [])
    }


def _declared_rows() -> dict[str, tuple[int, tuple[str, ...]]]:
    return {
        row["rule"]: (row["order"], tuple(row["reasons"]))
        for name in FILES
        for row in _load(name).get("fail_closed", {}).get("rows", [])
    }


# ---------------------------------------------------------------------------
#  1. test_every_oracle_claim_id_exists_in_the_interface
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_every_oracle_claim_id_exists_in_the_interface() -> None:
    """A frozen entry pinned to a claim that does not exist pins nothing.

    THE CHECK IS AT THE CLAIM FILES. Claim ids are not in a ``claims:`` block
    of ``interface.yaml``; claims are
    FILES here (spec/claim-format.md section 5) and the interface keeps only
    what is not a claim, so the resolution target is the file set.

    TWO LEVELS. The registry's own ``claims`` fields carry the
    PR numbering, which spec/modules.yaml still accounts for module by module;
    the registry's prose carries CLAIM LABELS, which resolve to claim files.
    """
    labels = {
        path.stem.replace("-", ":", 1)
        for path in (ROOT / "spec" / "modules").rglob("claims/*.tex")
    }
    assert len(labels) > 100
    named = set(_LABEL.findall(_registry_text()))
    assert named, "the registry names claim labels"
    removed = REMOVED_LABELS_IN_THE_CORE_RECORD | (
        frozenset() if PROBE_SPEC_PRESENT else PROBE_LABELS_IN_THE_CORE_RECORD
    )
    unresolved = sorted(named - labels - FOREIGN_OR_SUPERSEDED - removed)
    assert unresolved == [], unresolved

    # Every PR id a frozen entry pins is one of the thirteen codes.
    pinned = {claim for oracle in core.PR_ORACLES for claim in oracle.claims}
    pinned |= {claim for row in core.ASSUMPTION_LEDGER for claim in row.supports}
    assert pinned
    # THE PR NUMBERING IS THE FROZEN REGISTRY'S, and claim_codes.yaml, the
    # one table where the codes meet this repository's claim ids, declares
    # its range. So the check is that every pinned id is one of the thirteen
    # and that the range is still declared where a reader would look for it.
    assert pinned <= {f"PR{index}" for index in range(1, 14)}, sorted(pinned)
    codes = (ROOT / "tests" / "oracles" / "claim_codes.yaml").read_text(
        encoding="utf-8"
    )
    assert "PR1-PR13" in codes


# ---------------------------------------------------------------------------
#  2. test_refusal_reason_totality_registry_equals_interface
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_refusal_reason_totality_registry_equals_interface() -> None:
    """The freeze fixes the strings; the interface files partition them.

    THE FREEZE IS ``REFUSAL_REASONS_1_0_0``, thirty strings, and the one
    difference this repository makes is the rename recorded in the
    ``requested_assurance`` input row. THE CODE'S ENUMS ARE THE THIRD SIDE:
    a string declared and not spelled, or spelled and not declared, is what
    this catches.
    """
    from certiqs_key.reductions.reasons import CORE_REFUSAL_REASONS

    declared = _declared_reasons()
    assert len(declared) == len(set(declared)), "a string is declared twice"

    frozen = {RENAMED.get(name, name) for name in core.REFUSAL_REASONS_1_0_0}
    frozen |= STRINGS_ADDED_SINCE_THE_FREEZE
    in_code = set(CORE_REFUSAL_REASONS)
    assert not DOMINATION_STRINGS_RETIRED & (set(declared) | in_code)
    # The removed submodule's one string went away with it, and nothing else.
    assert frozen - set(declared) == {"blinding_model_ill_formed"}
    assert len(declared) == 29 + len(STRINGS_ADDED_SINCE_THE_FREEZE)
    assert set(declared) == in_code


# ---------------------------------------------------------------------------
#  3. test_every_fail_closed_row_has_at_least_one_registry_case
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_every_fail_closed_row_has_at_least_one_registry_case() -> None:
    """Row name, place in the table, reasons -- and a frozen case per reason.

    THE ORDERS ARE A PARTITION OF ``1..n`` WITH NO GAP AND NO DUPLICATE, which
    is what lets a submodule's row sit between two core rows without the core
    naming it, and what makes a deletion leave the rest in order. The code
    registers exactly the same rows at exactly the same orders.
    """
    import certiqs_key.reductions.wpfss.validation  # noqa: F401,RUF100
    from certiqs_key.reductions.reasons import registered_rows

    declared = _declared_rows()
    orders = sorted(order for order, _ in declared.values())
    assert len(set(orders)) == len(orders), "an order is declared twice"
    # THE FROZEN TWENTY-EIGHT: the domination submodule's two rows
    # (orders 29 and 30) are retired.
    assert not set(DOMINATION_ROWS_RETIRED) & set(declared)
    # The rows added since the freeze take the next free orders after it.
    assert all(
        declared[rule][0] == order
        for rule, order in FAIL_CLOSED_ROWS_ADDED_SINCE_THE_FREEZE.items()
    )
    total = core.FAIL_CLOSED_ROW_COUNT_1_0_0 + len(
        FAIL_CLOSED_ROWS_ADDED_SINCE_THE_FREEZE
    )
    missing = sorted(set(range(1, total + 1)) - set(orders))
    # DELETING A SUBMODULE LEAVES A GAP AND THE REST IN ORDER, which is
    # what the `order` field exists for: the core's own orders are not
    # contiguous, and no row moves when a submodule goes.
    assert len(declared) == total - 1
    assert len(missing) == 1, missing

    # A removable submodule's rows are registered wherever its package was
    # imported, which another test may have done: they are its own file's.
    in_code = {
        str(row.rule): (row.order, tuple(str(reason) for reason in row.reasons))
        for row in registered_rows()
        if str(row.rule) not in removable_rules()
    }
    assert in_code == declared

    # AND EVERY DECLARED REASON HAS A FROZEN CASE THAT PRODUCES IT.
    cases = {RENAMED.get(case.reason, case.reason) for case in core.REFUSAL_CASES}
    cases |= {
        RENAMED.get(case.refusal_reason, case.refusal_reason)
        for case in core.REFUSAL_CASES_PR_R
    }
    declared_reasons = set(_declared_reasons())
    # FIVE STRINGS THE FROZEN ``RefusalCase`` ENTRIES DO NOT REACH, each named
    # so that the absence is a decision and a SIXTH would fail this test:
    #
    # * the three rows added at 1.0.0 with the number model -- the lattice
    #   exponent, the requested assurance and the emitted family -- whose
    #   cases the adding band froze under its own names;
    # * ``dark_counts_not_column_stochastic``, added at 0.3.0 with the
    #   column-stochasticity row;
    # * ``high_photon_slot_ill_formed``, added at 0.2.0 with the slot row.
    #
    # Each of the five has a case in
    # ``tests/golden/test_reductions_fail_closed.py``, which is where the
    # row-to-refusal traceability lives; what this assertion fixes is that no
    # OTHER declared string is left without a frozen case.
    # The string added since the freeze has its case in
    # tests/unit/test_efficiency_normalization.py.
    without_a_frozen_case = declared_reasons - cases
    assert without_a_frozen_case == {
        "lattice_exponent_not_declared",
        "requested_assurance_unknown",
        "emitted_family_not_admissible",
        "dark_counts_not_column_stochastic",
        "high_photon_slot_ill_formed",
        *STRINGS_ADDED_SINCE_THE_FREEZE,
    }, sorted(without_a_frozen_case)


# ---------------------------------------------------------------------------
#  4. test_the_interface_key_vocabulary_is_the_frozen_one   (this is F-3's test)
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_interface_key_vocabulary_is_the_frozen_one() -> None:
    """Every output key of the interface files, and no other.

    A key with no content is a hand-maintained mirror of a deferral
    (PRINCIPLES.md section 7); ``douglas_data`` is a listed retirement
    and the emitted record may not carry it. THE FROZEN
    ``OUTPUT_KEYS_1_0_0`` IS THE ORIGINAL EIGHTEEN and is not regenerated:
    what is asserted is the RELATION between it and what this repository
    declares, so the freeze still decides every key but the retired one.

    The output row ``factor_emission`` is emitted by the code
    (:mod:`certiqs_key.reductions.factors`), and the third declared change
    since the freeze is named in the difference the way ``route`` and
    ``douglas_data`` are.
    """
    from certiqs_key.reductions.artifact import OUTPUT_KEYS

    declared = [row["name"] for row in _load("reductions")["outputs"]]
    # `wpfss`'s outputs block is a mapping with a `rows` list beside a note,
    # so the rows are read by key rather than by iterating the block.
    declared += [row["name"] for row in _load("wpfss")["outputs"]["rows"]]
    # The `domination` submodule's output rows (`domination_record`
    # and `domination_link`) are retired: it declares none.
    assert _load("domination")["outputs"] == []
    assert len(declared) == len(set(declared))
    assert set(OUTPUT_KEYS) == set(declared)
    assert "douglas_data" not in OUTPUT_KEYS
    # THE FREEZE IS THE ORIGINAL EIGHTEEN and is not regenerated. THREE
    # declared changes: ``douglas_data`` retired
    # (F-3); ``route`` -- an output row of ``wpfss/interface.yaml`` -- EMITTED
    # rather than only carried; and, at
    # reductions 0.2.0, ``factor_emission``, the ordered list of the
    # factors' artefacts with the combination rule. That row is "PRESENT
    # EXACTLY WHEN THE CALL DECLARES MORE THAN ONE INSTANCE" and is ABSENT from
    # a one-factor artefact, which is why it is a key of the module's
    # vocabulary and not a field of the artefact dataclass -- the distinction
    # ``ONE_ARTEFACT_ONLY_KEYS`` carries and ``tests/unit/
    # test_reductions_artifact.py`` pins.
    assert set(core.OUTPUT_KEYS_1_0_0) - set(OUTPUT_KEYS) == {"douglas_data"}
    # a FOURTH declared change, the
    # output row `reference_companion` the claim round added to
    # spec/modules/reductions/interface.yaml (req:reference-companion), which
    # the code emits now. The freeze is not regenerated.
    # A FIFTH, the output row `receiver_row_omitted_on_provenance`
    # (req:recv-row-provenance), which records why an artefact's A-RECV row
    # is absent where the run attested the receiver artefact it built.
    assert set(OUTPUT_KEYS) - set(core.OUTPUT_KEYS_1_0_0) == {
        "route",
        "factor_emission",
        "reference_companion",
        "receiver_row_omitted_on_provenance",
    }


# ---------------------------------------------------------------------------
#  5. test_the_link_vocabulary_matches_the_interface
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_link_vocabulary_matches_the_interface() -> None:
    """The kinds are per module, so that deleting a submodule deletes its kinds.

    The core declares six receiver-stage kinds, ``wpfss`` adds two, and
    ``source-map`` is the TRANSMITTER'S. The frozen nine are a
    single list, and the partition is what changed.
    """
    from certiqs_key.reductions.reasons import LinkKind

    core_row = next(
        row
        for row in _load("reductions")["inputs"]
        if row["name"] == "link_declarations"
    )
    declared = list(core_row["receiver_stage_kind_vocabulary_core"])
    for name in FILES:
        if name == "reductions":
            continue
        block = _load(name).get("link_kinds") or {}
        declared += list(block.get("added_by_this_submodule", []))
    assert len(declared) == len(set(declared))
    assert set(declared) | {"source-map"} == set(core.LINK_KINDS)
    # The code's enum carries the frozen nine, `source-map` included;
    # the core interface's kind_vocabulary_note records the disagreement, which
    # is about OWNERSHIP and not about the refusal a caller receives.
    assert {member.value for member in LinkKind} == set(core.LINK_KINDS)
    assert set(declared) <= {member.value for member in LinkKind}


# ---------------------------------------------------------------------------
#  6. test_the_interface_carries_the_nine_assumption_ledger_rows
# ---------------------------------------------------------------------------


#: THE AMENDMENT THE FROZEN LEDGER DOES NOT CARRY, mapped here rather than
#: edited there. ``registry_reductions.py`` is the record at
#: 1.0.0 and an oracle is never regenerated from the code it tests
#: (PRINCIPLES.md section 2.3), so its ``ASSUMPTION_COUNT_1_0_0 = 9`` and its
#: ``NEVER_VERIFIED_1_0_0 = ("A-RECV", "A-BLIND")`` stand untouched and this
#: constant is what says where the tenth row came from. It is the pattern
#: ``MERGED_IDS`` uses in
#: ``tests/golden/test_protocol_compiler_against_registry.py`` for the A-LIC /
#: A-ATK merge: the frozen side keeps its record, the live side is compared
#: against it THROUGH A NAMED MAP, and the map carries the reason.
#:
#: THE LEDGER HAD ONE MORE ROW: A-SOUND, machine key
#: ``constraints_sound``, NEVER-VERIFIABLE, at order 10, PRESENT IN AN EMITTED
#: LEDGER ONLY WHEN THE EMITTED CONSTRAINT LIST IS NON-EMPTY. It was
#: ``meat-core/ass:sound`` and moved here: the soundness of an emitted
#: constraint entry for the attack set is the obligation of the module that
#: BUILDS the entries, and no claim of the consuming module declared it.
#:
#: A-SOUND is RETIRED and left this map for
#: :data:`VACATED_ROWS`; its order 10 stays vacant
#: (:data:`VACANT_ORDERS`). A-DIM left; A-EVE-DIM, which took its order 1,
#: arrived and left again, and its order 1 stays vacant.
ROWS_ADDED_SINCE_THE_FREEZE: dict[str, str] = {
    # THE TWO ROWS reductions 0.2.0 ASSUMES FROM THE TRANSMITTER, added to the
    # map rather than absorbed, exactly as A-SOUND was.
    "A-SEQ": (
        "the "
        "transmitter's ass:seq, which def:protocol declares -- an assumption "
        "being a leaf whose assumes is empty, so no ass claim of this module "
        "can carry it -- at order 11, UNCONDITIONAL, because the number of "
        "measuring parties is not a datum def:protocol reads and with one "
        "measuring party the key is the assumption it always was"
    ),
    "A-SRC": (
        "the "
        "transmitter's source-replacement attestation, which "
        "lem:source-transfer reads through "
        "transmitter/thm:certificate-sufficiency (iii), at "
        "order 8 -- the order A-NOSRC vacated -- and PRESENT ONLY where the "
        "emitted chain's source segment is non-empty and only in "
        "trusted-source mode, which no artefact emitted today is"
    ),
    # foundations' A-SNAP arrives at the next free order after a removed
    # submodule's row at 12.
    "A-SNAP": (
        "foundations' ass:snapped-measurement, key "
        "snapped_measurement, which req:emission-record carries "
        "among the assumptions the artefact rests on; at order 13, the next "
        "free order, PRESENT ONLY where the emission record or the declaring "
        "party's snap record names a moved block, never-verifiable by its "
        "owner's field"
    ),
}

#: A ROW THAT ARRIVED AFTER THE FREEZE AND HAS LEFT AGAIN, kept so that the
#: order it took is accounted for.
VACATED_ROWS: dict[str, str] = {
    "A-SOUND": (
        "moved here from meat-core, order 10; retired: the soundness of the "
        "emitted list is a conclusion of thm:chain, cor:entries and thm:licence "
        "(rem:sound-and-atk)"
    ),
    "A-EVE-DIM": (
        "meat-core's ass:eve-dim, key adversary_registers_finite, assumed from "
        "that module at order 1, the order the split A-DIM held; retired: "
        "ass:eve-dim is superseded and no claim of this module assumes it, the "
        "round model keeping the adversary's registers finite-dimensional "
        "(foundations/def:round-model) and meat-core/lem:memory-lift carrying "
        "the security statement to registers of any dimension"
    ),
}

#: THE ORDERS NO ROW HOLDS, each with the row that left it. A row keeps the
#: place it was given, so a retirement leaves a gap rather than renumbering.
VACANT_ORDERS: dict[int, str] = {1: "A-EVE-DIM", 10: "A-SOUND"}

#: THE ROW THAT LEFT THIS LEDGER SINCE THE FREEZE, mapped here for the same
#: reason the arrivals are: the frozen side keeps its record and the live side
#: is compared against it THROUGH A NAMED MAP. A-NOSRC was the transmitter's
#: ``source_stage_empty`` at order 8. No claim of this module
#: rests on the source segment being empty -- ``def:chain`` defines the chain at
#: every length and its composite as the PAIR, ``thm:chain`` (i)-(iv) read the
#: receiver composite alone, and ``rem:ordering``'s inclusion is
#: ``lem:precomposition`` -- and this ledger is computed from that closure, so a
#: row for it would be a hand-maintained mirror of a generated view
#: (PRINCIPLES.md section 7). Whether the segment is empty is DATA a consumer
#: reads in the emitted ``reduction_chain``.
ROWS_REMOVED_SINCE_THE_FREEZE: dict[str, str] = {
    "A-NOSRC": (
        "no claim of "
        "this module rests on the source segment being empty any more, so the "
        "key is in the closure of none of them; interface.yaml's "
        "assumption_ledger.no_row_for_an_empty_source_segment states it"
    ),
    "A-DIM": (
        "split into "
        "def:system-setting, a definition and no row, and meat-core's "
        "A-EVE-DIM, which took its order 1 and has retired in turn "
        "(VACATED_ROWS)"
    ),
}


@pytest.mark.contract
@pytest.mark.oracle
def test_the_interface_carries_the_nine_assumption_ledger_rows() -> None:
    """Eight core rows, one assumed from the transmitter, one per submodule.

    THE FREEZE COUNTS NINE and names A-RECV and A-BLIND as the never-verifiable
    two. One of them is renamed -- A-ROUND to A-ROUND-SQ with the
    machine key ``round_homogeneity_squashing``, because short ids and machine
    keys are repository-wide and the receiver already owns the old one -- and
    that rename is what the ``a_round_sq_key_note`` of the core interface
    records. The orders are a partition with no gap.

    ROWS HAVE ARRIVED AND ONE HAS LEFT SINCE THE FREEZE, and each is MAPPED
    rather than absorbed: :data:`ROWS_ADDED_SINCE_THE_FREEZE` and
    :data:`ROWS_REMOVED_SINCE_THE_FREEZE`. The test name is 1.0.0's and is left
    alone, because what it names is the deleted test it re-establishes.

    The code carries both readings (A-SEQ in the interface's ledger, A-NOSRC
    out of it), and the arithmetic below pins the total, the orders as a
    contiguous partition, the never-verifiable set, and the row-for-row
    agreement between the interface and the code.
    """
    from certiqs_key.reductions.reasons import CORE_ASSUMPTIONS

    ledger = next(
        row
        for row in _load("reductions")["outputs"]
        if row["name"] == "assumption_ledger"
    )
    rows = {row["id"]: row for row in ledger["core_rows"]}
    rows.update({row["id"]: row for row in ledger["assumed_from_another_module"]})
    assert ledger["core_row_count"] == 6

    orders = sorted(row["order"] for row in rows.values())
    assert len(set(orders)) == len(orders), "a ledger order is declared twice"
    # THE FROZEN TOTAL PLUS THE ROWS THAT ARRIVED SINCE, and each arrival is
    # named in the map with its reason. An arriving row takes THE NEXT ORDER
    # rather than renumbering the frozen nine, which is what keeps the two
    # sides comparable at all: the frozen orders 1..9 are still the frozen
    # rows' orders.
    assert set(ROWS_ADDED_SINCE_THE_FREEZE) <= set(rows)
    assert set(ROWS_REMOVED_SINCE_THE_FREEZE) & set(rows) == set()
    assert set(VACATED_ROWS) & set(rows) == set()
    assert set(VACANT_ORDERS.values()) == set(VACATED_ROWS)
    assert set(VACANT_ORDERS) & set(orders) == set()
    total = (
        core.ASSUMPTION_COUNT_1_0_0
        + len(ROWS_ADDED_SINCE_THE_FREEZE)
        - len(ROWS_REMOVED_SINCE_THE_FREEZE)
    )
    # THE ORDERS ARE A PARTITION OF 1..(total + vacant) LESS THE VACANT ONES.
    span = set(range(1, total + len(VACANT_ORDERS) + 1)) - set(VACANT_ORDERS)
    # The same ratchet as the fail-closed table: a removed submodule's two rows
    # (A-BLIND at 5, and a row at 12 under which A-SNAP took 13) are gone and
    # the rest keep their places, 5 and 12 vacant.
    assert len(rows) == total - 1
    assert span - set(orders) == {5, 12} and set(orders) - span == {13}

    # THE RENAME, on both sides of the boundary.
    assert "A-ROUND" not in rows
    assert rows["A-ROUND-SQ"]["machine_key"] == "round_homogeneity_squashing"
    assert set(core.NEVER_VERIFIED_1_0_0) - set(rows) == {"A-BLIND"}
    never = {row["id"] for row in rows.values() if row.get("never_verifiable")}
    # THE FROZEN PAIR LESS THE REMOVED ROW.
    # A-MEAS AND A-ROUND-SQ are marked too (req:never-verified-assumptions):
    # statements about the devices and the run that no declared datum bears on;
    # the frozen pair is untouched. FROZEN UNION ADDED, the added rows listed:
    # A-PROBE, A-TSM and A-CONST carry `verification: never`, and the rows
    # assumed from the transmitter, A-SRC and A-SEQ, carry their owner's mark
    # (req:never-verified-assumptions). A-SOUND, A-DIM and A-EVE-DIM have
    # left with their rows.
    assert never == (
        (set(core.NEVER_VERIFIED_1_0_0) & set(rows))
        | {"A-MEAS", "A-ROUND-SQ"}
        | {"A-PROBE", "A-TSM", "A-CONST", "A-SRC", "A-SEQ"}
        | {"A-SNAP"}
    )

    # A-SNAP's row is not among the rows every emission carries; it is
    # appended where its presence rule holds, so the code's rows are
    # CORE_ASSUMPTIONS and that one row.
    from certiqs_key.reductions.reasons import SNAPPED_MEASUREMENT_ROW

    in_code = {row.identifier: row for row in CORE_ASSUMPTIONS}
    in_code[SNAPPED_MEASUREMENT_ROW.identifier] = SNAPPED_MEASUREMENT_ROW
    for identifier, row in in_code.items():
        assert rows[identifier]["machine_key"] == row.machine_key, identifier
        assert rows[identifier]["order"] == row.order, identifier
        assert rows[identifier].get("never_verifiable", False) == (
            row.never_verifiable
        ), identifier
    # AND THE CODE CARRIES EVERY ROW THE INTERFACE DECLARES AS THE CORE'S, not
    # merely a subset of them: the loop above would pass a code that dropped a
    # row, which is the direction that understates what an artifact rests on.
    # A-SEQ and A-SRC are the TRANSMITTER'S and are declared under
    # `assumed_from_another_module`, so they are in the code's emitted tuple
    # and not in the interface's core_rows -- which is the same reading this
    # line carried for the removed A-NOSRC row. The code
    # names which of its rows are the transmitter's rather than leaving the
    # difference to be inferred here. No row is assumed from meat-core.
    from certiqs_key.reductions.reasons import (
        ASSUMED_FROM_FOUNDATIONS,
        ASSUMED_FROM_THE_TRANSMITTER,
    )

    assumed_in_code = set(ASSUMED_FROM_THE_TRANSMITTER) | set(
        ASSUMED_FROM_FOUNDATIONS
    )
    declared_core = {row["id"] for row in ledger["core_rows"]}
    declared_assumed = {row["id"] for row in ledger["assumed_from_another_module"]}
    assert declared_core == set(in_code) - assumed_in_code
    assert declared_assumed == assumed_in_code
    owners = {row["id"]: row["owner"] for row in ledger["assumed_from_another_module"]}
    assert {i for i, o in owners.items() if o == "meat-core"} == set()
    assert {i for i, o in owners.items() if o == "transmitter"} == set(
        ASSUMED_FROM_THE_TRANSMITTER
    )
    assert {i for i, o in owners.items() if o == "foundations"} == set(
        ASSUMED_FROM_FOUNDATIONS
    )
    # NO CORE ROW IS CONDITIONAL BUT FOUR: the presence rules in this ledger
    # include A-SRC's, assumed from the transmitter, and A-SNAP's, assumed from
    # foundations. A-CONST is present only where the emitted constraint
    # list is non-empty (req:assumption-ledger), and the code reads that rule
    # at the emission (PRESENT_ONLY_WITH_A_NON_EMPTY_CONSTRAINT_LIST).
    # A-PROBE is present
    # only where the declared setting set has at least two values, and A-TSM
    # where it does or where a public choice is applied at the station
    # (req:assumption-ledger); the code reads both rules at the emission.
    # A-RECV is present save where req:recv-row-provenance omits it, which the
    # code reads at the emission too (OMITTED_ON_RECEIVER_PROVENANCE).
    from certiqs_key.reductions.reasons import (
        OMITTED_ON_RECEIVER_PROVENANCE,
        PRESENT_ONLY_WITH_A_NON_EMPTY_CONSTRAINT_LIST,
        PRESENT_ONLY_WITH_A_PRIVATE_SETTING,
        PRESENT_ONLY_WITH_A_SETTING_OR_A_CHOICE,
    )

    conditional = {
        row["id"] for row in ledger["core_rows"] if "presence" in row
    }
    assert conditional == {"A-CONST", "A-PROBE", "A-RECV", "A-TSM"} == (
        set(PRESENT_ONLY_WITH_A_NON_EMPTY_CONSTRAINT_LIST)
        | set(PRESENT_ONLY_WITH_A_PRIVATE_SETTING)
        | set(PRESENT_ONLY_WITH_A_SETTING_OR_A_CHOICE)
        | set(OMITTED_ON_RECEIVER_PROVENANCE)
    )
    assert "req:recv-row-provenance" in next(
        row["presence"] for row in ledger["core_rows"] if row["id"] == "A-RECV"
    )
    assert "AT LEAST TWO VALUES" in next(
        row["presence"] for row in ledger["core_rows"] if row["id"] == "A-PROBE"
    )
    assert "not told" in next(
        row["presence"] for row in ledger["core_rows"] if row["id"] == "A-TSM"
    )
    assert "NON-EMPTY" in next(
        row["presence"] for row in ledger["core_rows"] if row["id"] == "A-CONST"
    )


# ---------------------------------------------------------------------------
#  7. test_the_two_rounding_rules_are_recorded_and_are_two
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_rounding_rules_are_recorded_and_are_two() -> None:
    """Every rounded bound has a direction and a sentence saying why it is safe.

    THE STANDING TABLE HAS THREE ROWS -- the certified weight DOWN, its
    complement RECOMPUTED rather than rounded, and a caller's constant toward
    the enlarging side -- and the interface's ``emission_record`` row states
    the same three. The frozen ``ROUNDING_RULE`` is the conditional weight rule
    and fixes the first one's direction.
    """
    from certiqs_key.reductions.artifact import ROUNDING_DIRECTIONS

    declared = _load("reductions")["outputs"]
    record = next(row for row in declared if row["name"] == "emission_record")
    directions = record["rounding_directions"]
    assert len(directions) == len(ROUNDING_DIRECTIONS) == 3
    assert [item["direction"] for item in directions] == [
        direction for _, direction, _ in ROUNDING_DIRECTIONS
    ]
    assert all(item["why"].strip() for item in directions)
    assert core.ROUNDING_RULE["direction"] == "toward_zero"
    assert ROUNDING_DIRECTIONS[0][1] == "down"
    assert ROUNDING_DIRECTIONS[1][1] == "recomputed_not_rounded"


# ---------------------------------------------------------------------------
#  8. test_the_corpus_directory_is_never_named
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_corpus_directory_is_never_named() -> None:
    """PRINCIPLES.md section 8: ``context/`` is evidence and never authority.

    "An idea taken from one is derived in full in a claim file and tagged
    ``newly-derived``", so no shipped module file, no interface row and no
    frozen registry value may cite the working-notes directory as the reason
    for anything.
    """
    offenders: list[str] = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        if "context/" in path.read_text(encoding="utf-8"):
            offenders.append(str(path.relative_to(ROOT)))
    for name in FILES:
        if "context/" in FILES[name].read_text(encoding="utf-8"):
            offenders.append(str(FILES[name].relative_to(ROOT)))
    if "context/" in _registry_text():
        offenders.append("the frozen registry")
    assert offenders == [], offenders
