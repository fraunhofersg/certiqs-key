"""The frozen registry, the two interface files, the claim files and the code agree.

The frozen ``registry_statistics_acceptance`` was once bound to ONE
interface transcription with nine
tests; that document has no successor at the same shape here -- the claims are
claim files under ``spec/modules/statistics/`` and the interface is two
files, the core's and ``binomial-box``'s -- so the nine could not be carried
verbatim and could not simply be dropped either, or the registry would be bound
to nothing. Each is re-established below UNDER THE NAME THE ABSENT ONE HAD,
against the documents this repository does have. The reductions and receiver
registries do the same.

WHAT EACH OF THE NINE CATCHES, which is why they are worth the re-write: a
claim id that resolves on one side of the boundary and not the other, a reason
code whose spelling drifted, a convention the registry's derivations assume and
the interface no longer declares, a ledger row that lost its machine key, and
the two branches of the ``acceptance_support`` formula being collapsed into
one.

THE ONE MAPPING THIS FILE READS. The registry's entries name the oracle's
section ids ``SA1``-``SA9``; this repository has claim LABELS. Eight map one to
one; the ninth, ``SA3``, is SPLIT -- what is the exact rule's is
``binomial-box/prop:rule-exact`` and what is every rule's is
``binomial-box/lem:guard`` -- and the file ``thm-sa3.tex`` is gone. The map is
the SA rows of ``claim_codes.yaml``, read here as :data:`CLAIM_LABELS`, and
that file is the only place the two vocabularies meet.

NOTHING HERE READS A FROZEN VALUE AS A SOURCE OF TRUTH ABOUT THE MATHEMATICS,
and nothing here runs the module: the assertions are between documents and a
frozen tuple of strings.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import claim_codes
import pytest
import yaml
from registry_statistics_acceptance import (
    INPUT_DOMAIN_VIOLATION_CASES,
    REASON_CODES,
    SA_ORACLES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE = REPO_ROOT / "spec" / "modules" / "statistics"
CORE_INTERFACE = MODULE / "interface.yaml"
BOX_INTERFACE = MODULE / "binomial-box" / "interface.yaml"

#: The contract version the freeze bound, and the accepted version the
#: interface records (statistics/module.yaml's `version:` line), written by
#: hand when it moves.
FROZEN_CONTRACT_VERSION = "0.1.2"
ACCEPTED_VERSION = "statistics@0.10.0"

#: The oracle's nine section ids against this repository's claim labels,
#: each relative to ``spec/modules/statistics/``, read from
#: ``claim_codes.yaml``. ``SA3`` maps to TWO labels: the old theorem is split
#: into the exact rule's proposition and the rule-independent lemma, and the
#: registry's SA3 entries pin values of both.
CLAIM_LABELS: dict[str, tuple[str, ...]] = claim_codes.labels(
    "SA", "statistics", submodules=True
)


def _document(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        document: dict[str, Any] = yaml.safe_load(handle)
    return document


def _claim_file(label: str) -> Path:
    """Return the claim file a label of :data:`CLAIM_LABELS` names."""
    parts = label.split("/")
    stem = parts[-1].replace(":", "-").replace("_", "-")
    directory = MODULE.joinpath(*parts[:-1]) / "claims"
    return directory / f"{stem}.tex"


def _declared_on(short_id: str) -> set[str]:
    """Return the claims whose own ``assumes`` header holds ``short_id``.

    Each label is relative to ``spec/modules/statistics/``, as in
    :data:`CLAIM_LABELS`. The claim files are the authority
    (``check_claims --dependents``); the interface keeps no copy of the list.
    """
    declared: set[str] = set()
    for path in MODULE.rglob("claims/*.tex"):
        text = path.read_text(encoding="utf-8")
        claim = re.search(r"^% id: statistics/(\S+)$", text, re.MULTILINE)
        assumes = re.search(r"^% assumes: \[(.*)\]$", text, re.MULTILINE)
        assert claim and assumes, path
        if short_id in (item.strip() for item in assumes.group(1).split(",")):
            declared.add(claim.group(1))
    return declared


def _labels_in(document: dict[str, Any], prefix: str = "") -> set[str]:
    return {f"{prefix}{entry['claim']}" for entry in document["claims"]["order"]}


def _all_labels() -> set[str]:
    core = _labels_in(_document(CORE_INTERFACE))
    box = _labels_in(_document(BOX_INTERFACE), "binomial-box/")
    singleton = {
        f"singleton/{entry['claim']}"
        for entry in _document(CORE_INTERFACE)["submodules_today"]["singleton"][
            "claims_snapshot"
        ]["order"]
    }
    return core | box | singleton


# ---------------------------------------------------------------------------
#  1. Traceability against the interface files and the claim files
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_interface_yaml_exists_and_names_the_accepted_contract() -> None:
    """Both interface files exist, name this module, and pin one version.

    THE VERSION IS THE ONLY THING THAT MOVED. The earlier file carried a
    ``contract_version`` and a ``symbols_md_version`` of its own; here the pin
    is ``artifact_bindings.mathematical_spec_version`` and it is the core's,
    the submodule carrying the same string because a submodule's claims are
    inside its core's contract and it emits no artefact of its own.
    """
    core = _document(CORE_INTERFACE)
    box = _document(BOX_INTERFACE)
    assert core["module_id"] == "statistics"
    assert box["module_id"] == "statistics/binomial-box"
    assert box["parent_module"] == "statistics"
    assert core["artifact_bindings"]["mathematical_spec_version"] == ACCEPTED_VERSION
    assert box["artifact_bindings"]["mathematical_spec_version"] == ACCEPTED_VERSION
    assert core["max_attainable_tier"] == "first-order"
    # THE FREEZE'S OWN VERSION IS NAMED, not silently dropped: the registry was
    # bound to it, and the interface records it as the version the registry's
    # cases were derived from.
    assert FROZEN_CONTRACT_VERSION in core["artifact_bindings"]["version_note"]
    assert core["artifact_bindings"]["package"] == "src/certiqs_key/statistics/"


@pytest.mark.contract
def test_every_oracle_claim_id_exists_in_the_interface() -> None:
    """Every ``SAk`` a frozen entry names resolves to a claim OF THIS REPOSITORY.

    Through :data:`CLAIM_LABELS`, read from ``claim_codes.yaml``, the only place
    the oracle's section ids and this repository's labels meet. Each label
    must appear in the interface file that assembles it AND have a claim file
    on disk: a label that resolved in one and not the other is exactly the
    drift this test catches.
    """
    known = _all_labels()
    for section, labels in CLAIM_LABELS.items():
        for label in labels:
            assert label in known, (section, label)
            assert _claim_file(label).is_file(), (section, label)
    for entry in SA_ORACLES:
        assert entry.claims, entry.oracle_id
        for claim in entry.claims:
            assert claim in CLAIM_LABELS, (entry.oracle_id, claim)


@pytest.mark.contract
def test_the_registry_covers_every_claim_of_the_contract() -> None:
    """The nine frozen section ids are all pinned by at least one entry."""
    covered = {claim for entry in SA_ORACLES for claim in entry.claims}
    assert set(CLAIM_LABELS) <= covered


@pytest.mark.contract
def test_every_claim_is_newly_derived_and_cites_nothing() -> None:
    """Provenance and citations, across BOTH interface files and the submodule.

    The earlier version counted nine ``newly-derived`` claims and no
    citation. The count is not restated here, because a count in a test is a
    second place to keep it
    (spec/claim-format.md section 4); what is asserted is the PROPERTY, on
    every row of both files: every claim is ``newly-derived`` and every ``refs``
    list is empty. The core's own ``no_citation_is_load_bearing`` says the same
    and is asserted with it, because that sentence is what makes the empty
    lists a fact about the contract rather than an omission.
    """
    rows = (
        _document(CORE_INTERFACE)["claims"]["order"]
        + _document(BOX_INTERFACE)["claims"]["order"]
        + _document(CORE_INTERFACE)["submodules_today"]["singleton"][
            "claims_snapshot"
        ]["order"]
    )
    assert rows
    for row in rows:
        assert row["provenance"] == "newly-derived", row["claim"]
        assert row["refs"] == [], row["claim"]
    assert "EVERY `refs` LIST BELOW IS EMPTY" in _document(CORE_INTERFACE)["claims"][
        "no_citation_is_load_bearing"
    ]


@pytest.mark.contract
def test_the_interface_carries_the_own_ledger_rows() -> None:
    """The own rows, with their machine keys, and no inherited one.

    ``A-TSM`` was inherited from ``reductions/ass:tsm`` rather than being a
    row of this module's own ledger; it is no row at all, no result
    this module reports resting on it. The honest-model keys are identifiers.
    The frozen ``A-EXACT``, renamed ``A-RATIONAL`` because
    ``receiver/ass:exact`` owns ``A-EXACT``, is no assumption: its condition is
    ``statistics/def:conservative-evaluation``, decided by requirements, and
    it carries no ledger row. A-ALPHABET's row keeps only the clause no code
    decides, under the key ``acceptance_recorded_every_round``.
    """
    ledger = _document(CORE_INTERFACE)["assumption_ledger"]
    own = {row["id"]: row for row in ledger["own_rows"]}
    # A-HON-ENV is the honest envelope's assumption.
    assert set(own) == {"A-HON", "A-HON-ENV", "A-ALPHABET", "A-REACH"}
    assert own["A-HON"]["machine_key"] == "honest_rounds_iid"
    assert own["A-HON-ENV"]["machine_key"] == "honest_rounds_within_envelope"
    assert own["A-ALPHABET"]["machine_key"] == "acceptance_recorded_every_round"
    assert own["A-REACH"]["machine_key"] == "honest_reachable"
    for row in own.values():
        assert _declared_on(row["id"]), row["id"]
        assert _claim_file(row["claim"]).is_file(), row["id"]

    assert "inherited_rows" not in ledger
    assert set(ledger["emission_rule"]) == set(own)
    # A-ALPHABET supports every one of the nine but SA2 (thm:binomial-tails, a
    # statement about a binomial count alone, which declares no assumption)
    # and SA3; A-REACH supports SA6 alone.
    alphabet_labels = _declared_on("A-ALPHABET")
    for section in ("SA1", "SA4", "SA5", "SA6", "SA7", "SA8", "SA9"):
        assert alphabet_labels & set(CLAIM_LABELS[section]), section
    assert _declared_on("A-REACH") & set(CLAIM_LABELS["SA6"])
    # AND THE SUBMODULES ADD NONE, which is what makes these rows the whole
    # ledger.
    assert _document(BOX_INTERFACE)["assumption_ledger"]["rows"] == []
    assert _document(CORE_INTERFACE)["assumption_ledger"]["submodule_rows"] == []


@pytest.mark.contract
def test_the_interface_conventions_match_what_the_registry_assumes() -> None:
    """The conventions every frozen case was written against, unchanged."""
    conventions = _document(CORE_INTERFACE)["conventions"]
    assert conventions["log_base"] == 2
    assert conventions["entropy_units"] == "bits"
    # No Renyi object occurs anywhere in this contract: both are `not used`.
    assert conventions["entropy_variant"] is None
    assert conventions["arrow"] is None
    assert conventions["alpha_domain"] == "(1, 2)"
    assert conventions["test_statistics_model"] == "output_state"
    assert conventions["round_homogeneity"] == "honest side only"
    # No quantum system occurs, so there is no subsystem order to declare.
    assert conventions["subsystem_order"] is None
    # THE ONE CONVENTION CHANGE: the model is INHERITED.
    assert conventions["test_statistics_model_inherited"] is True
    # The submodule inherits the core's list whole and adds two of its own,
    # both of which bind the two new routes.
    box = _document(BOX_INTERFACE)["conventions"]
    assert "spec/modules/statistics/interface.yaml" in box["inherits"]
    assert "DYADIC" in box["the_substrate_rule"]
    assert "NO LOGARITHM, EXPONENTIAL OR SPECIAL FUNCTION" in (
        box["no_transcendental_dependency"]
    )


@pytest.mark.contract
def test_alpha_is_not_a_parameter_of_this_module() -> None:
    """The one parameter row exists to say alpha is not one."""
    parameters = _document(CORE_INTERFACE)["parameters"]
    rows = {row["name"]: row for row in parameters["rows"]}
    assert set(rows) == {"alpha"}
    assert rows["alpha"]["is_a_parameter_of_this_module"] is False
    assert rows["alpha"]["consumer_domain"] == "(1, 2)"
    assert "NONE AT THE CORE" in parameters["free_numerical_parameters"]
    # AND THE SUBMODULE'S EVALUATION PARAMETERS ARE NOT PARAMETERS IN THAT
    # SENSE and not thresholds, which is the row a reader is likeliest to
    # misread now that there are numbers to fix.
    assert _document(CORE_INTERFACE)["declared_thresholds"] == {}
    assert "NOT PARAMETERS IN THAT SENSE" in (
        _document(BOX_INTERFACE)["parameters"]["note"]
    )


@pytest.mark.contract
def test_the_nine_reason_codes_are_the_interface_ones() -> None:
    """Theorem thm:honest-containment (iii) fixes the vocabulary; nothing here invents one.

    NINE BECAME TEN. The registry's nine are the interface's first nine, in its
    order and with their spellings unchanged, and the tenth is
    ``endpoint_rule_unknown``. The frozen violating requests cover the nine and
    no more, the tenth having no frozen case.
    """  # noqa: E501
    outputs = {row["name"]: row for row in _document(CORE_INTERFACE)["outputs"]}
    listed = outputs["infeasibility_report"]["reason_code_list"]
    # TEN BECAME ELEVEN with the honest envelope: the
    # envelope's own code sits beside the point form's, as in thm:honest-containment
    # (iii).
    assert len(listed) == 11
    # Each interface line is "<code> -- <clause>"; the code is its first token.
    codes = tuple(line.split()[0] for line in listed)
    envelope = "honest_envelope_not_admissible"
    assert codes[codes.index("honest_not_a_distribution") + 1] == envelope
    without = tuple(code for code in codes if code != envelope)
    assert without[:9] == REASON_CODES
    assert without[9] == "endpoint_rule_unknown"
    frozen = tuple(case.reason_code for case in INPUT_DOMAIN_VIOLATION_CASES)
    assert frozen == REASON_CODES
    # AND THE VALIDATION ORDER IS DECLARED, which the earlier interface
    # did not do and which the code follows step by step.
    order = outputs["infeasibility_report"]["validation_order"]
    assert len(order) == 9
    assert order[-1].endswith("endpoint_rule_unknown")


@pytest.mark.contract
def test_the_acceptance_support_row_carries_both_branches() -> None:
    """The judgement call recorded in interface.yaml, asserted as text.

    The two branches are not the same kind of statement: for the box form the
    emitted ``Chat^+`` need not be minimal and must not be tightened, and for
    ``singleton`` the claim does assert minimality. Collapsing them is the one
    way this output can be silently wrong.
    """
    outputs = {row["name"]: row for row in _document(CORE_INTERFACE)["outputs"]}
    domain = outputs["acceptance_support"]["domain"]
    assert "q^+(chat) > 0" in domain
    assert "supp q^*" in domain
    judgement = outputs["acceptance_support"]["formula_judgement"]
    assert "NEED NOT BE MINIMAL" in judgement
    assert "MUST NOT" in judgement
    # The consumer-side notion: def:perturbed is retired, and the acceptance
    # support is eq:chacc-def of frank-wolfe/def:first-order-setting.
    assert "def:first-order-setting" in outputs["acceptance_support"]["locator"]
    assert "def:perturbed" not in domain


# ---------------------------------------------------------------------------
#  2. What was added, which had no earlier test to re-establish
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_two_request_fields_and_their_defaults_are_the_codes() -> None:
    """The inputs table's two new rows against the enumerations in the code.

    ``interface.yaml`` fixes the domains as CLOSED enumerations and the
    defaults, on its own authority (``fixed_by_this_file``), and the closure is
    what makes the tenth reason code decidable. This is the one place the
    document and the enum are compared.
    """
    from certiqs_key.statistics import EndpointRuleName, TailEvaluation

    inputs = {row["name"]: row for row in _document(CORE_INTERFACE)["inputs"]}
    # honest_envelope, the ninth, joined with the honest-envelope batch.
    assert len(inputs) == 9
    assert "honest_envelope" in inputs
    assert "DEFAULT `exact`" in inputs["endpoint_rule"]["presence"]
    assert "DEFAULT `sweep`" in inputs["tail_evaluation"]["presence"]
    assert {str(name) for name in EndpointRuleName} == {"exact", "bernstein"}
    assert {str(name) for name in TailEvaluation} == {"sweep", "enclosure"}
    for value in EndpointRuleName:
        assert f"`{value}`" in inputs["endpoint_rule"]["domain"]
    for value in TailEvaluation:
        assert f"`{value}`" in inputs["tail_evaluation"]["domain"]


@pytest.mark.contract
def test_every_rule_table_row_is_a_route_the_code_carries() -> None:
    """The submodule's ``rule_table`` against the code's route table.

    ``binomial-box/interface.yaml``: "adding a rule adds a claim, its entry in
    the clauses that enumerate the rules (def:endpoint-rule (viii),
    req:rule-in-force), a row of ``rule_table`` and a value of the core's
    ``endpoint_rule`` input, and no theorem about the construction changes".
    This asserts the other direction too -- the
    code carries no route the table does not -- and that the monotonicity
    column, which is exactly the hypothesis ``thm:monotonicity-limits`` (i) and (ii)
    read, says of each route what the rule class says of itself.
    """
    from certiqs_key.statistics import ENDPOINT_RULES, EndpointRuleName, TailEvaluation

    rows = _document(BOX_INTERFACE)["rule_table"]["rows"]
    declared: dict[tuple[str, str], bool] = {}
    for row in rows:
        rule = row["endpoint_rule"]
        if row["tail_evaluation"].startswith("either"):
            evaluations = [str(value) for value in TailEvaluation]
        else:
            evaluations = [row["tail_evaluation"]]
        for evaluation in evaluations:
            declared[(rule, evaluation)] = row["monotone_in_the_allocation"]
            assert row["sa7_i_and_ii_apply"] is row["monotone_in_the_allocation"]
            assert _claim_file(
                "binomial-box/" + row["instance_proved_by"].split(" ")[0]
            ).is_file(), row["instance_proved_by"]
    live = {(str(rule), str(evaluation)) for rule, evaluation in ENDPOINT_RULES}
    assert live == set(declared)
    for key, monotone in declared.items():
        instance = ENDPOINT_RULES[
            (EndpointRuleName(key[0]), TailEvaluation(key[1]))
        ]()
        assert instance.monotone_in_the_allocation is monotone, key


@pytest.mark.contract
def test_every_completeness_report_row_has_a_route_and_a_direction() -> None:
    """The four rows of ``completeness_report``, and the one thing none may do.

    ``req:completeness-report`` fixes the report on ``exact`` + ``sweep`` and
    requires on every other route the report that route's row names; what is
    asserted here is that the rows cover every route exactly once and that the
    file still says a downward-rounded figure is inadmissible on every one of
    them.
    """
    from certiqs_key.statistics import ENDPOINT_RULES

    report = _document(BOX_INTERFACE)["completeness_report"]
    routes = {(row["endpoint_rule"], row["tail_evaluation"]) for row in report["rows"]}
    live = {(str(rule), str(evaluation)) for rule, evaluation in ENDPOINT_RULES}
    assert routes == live
    assert len(report["rows"]) == len(routes)
    assert "REPORT A DOWNWARD-ROUNDED FIGURE" in report["one_thing_no_row_may_do"]


@pytest.mark.contract
def test_the_settled_evaluation_parameters_are_recorded_against_the_proposals() -> None:
    """Every proposal of the submodule is marked as one, and the code fixes it.

    ``binomial-box/interface.yaml`` marks every evaluation-parameter default
    ``proposal: true`` and gives the value in force in the row's ``settled``
    field, with the reason where it differs from the proposal. What is asserted
    here is that a proposal row exists for every parameter the code records, so
    that a reader of the ``honest_model`` can find the row that sized it.
    """
    from certiqs_key.statistics import (
        BernsteinRule,
        EnclosureExactRule,
        TailEvaluation,
    )

    parameters = _document(BOX_INTERFACE)["evaluation_parameters"]
    enclosure_rows = {
        row["name"] for row in parameters["the_enclosure_route"]["rows"]
    }
    bernstein_rows = {row["name"] for row in parameters["the_bernstein_rule"]["rows"]}
    for block in (parameters["the_enclosure_route"], parameters["the_bernstein_rule"]):
        for row in block["rows"]:
            if row["name"] == "the_rounding_directions":
                continue
            assert row["proposal"] is True, row["name"]
    # EVERY RECORDED NAME IS A PATH INTO THIS FILE: the block it is declared
    # in, a dot, and the row's own name. The block is what keeps the record
    # unambiguous on bernstein + enclosure, where both blocks apply and each
    # declares a root_exponent_j. The
    # window row's single name covers an ADAPTIVE policy, so the three numbers
    # that define it are all recorded under names beginning ``window_``.
    blocks = {
        "the_enclosure_route": enclosure_rows,
        "the_bernstein_rule": bernstein_rows,
    }
    recorded = (
        EnclosureExactRule(TailEvaluation.ENCLOSURE).recorded_parameters()
        + BernsteinRule(TailEvaluation.ENCLOSURE).recorded_parameters()
    )
    assert recorded
    for name, _ in recorded:
        block, _, row = name.partition(".")
        assert block in blocks, name
        assert row in blocks[block] or row.startswith("window_"), name


@pytest.mark.contract
def test_the_search_procedure_is_fixed_total_and_deterministic() -> None:
    """The hypothesis of ``prop:bracketed-endpoints``, discharged by the file.

    That proposition defines the enclosure evaluation as the rule whose
    endpoint "a fixed search procedure that ``interface.yaml`` records"
    returns: until the procedure is fixed there is no function of the inputs
    and the proposition has no subject. This asserts that the file still
    records one and still states the three properties the claim needs of it.
    """
    procedure = _document(BOX_INTERFACE)["search_procedure"]
    assert "BISECTION" in procedure["proposed"]
    assert "hi = n" in procedure["proposed"]
    assert "lo = -1" in procedure["proposed"]
    assert "UNDECIDED" in procedure["proposed"].upper()
    assert "FIXED, TOTAL and DETERMINISTIC" in procedure["proposal_note"]
    why = procedure["why_it_terminates_and_what_it_returns"]
    assert "THE SEARCH CANNOT FAIL" in why
