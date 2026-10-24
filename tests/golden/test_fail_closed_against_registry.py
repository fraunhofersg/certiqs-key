"""Fail-closed behaviour, against the FROZEN fail-closed oracles.

``O-HLOW-INFINITE``, ``O-CONSTRAINT-GATE``, ``O-ASSURANCE-ESTIMATE`` and, since
contract 0.4.0, ``O-ASSURANCE-CERTIFIED-GATE``. These are the tests where a
*number* or a *label* would be the failure: an ``h_low`` clamped to a finite
ceiling, a key length emitted without the attack-set licence, or a result
labelled ``certified`` that no runtime check stands behind. Each overstates the
key.

AT contract 0.5.0 ``O-ASSURANCE-CERTIFIED-GATE`` IS MARKED ``superseded``
(``SUPERSEDED_BY_0_5_0``): the "EXACTLY WHEN" of its biconditional is false
once Theorem ``thm:optol`` (iii) forces the label off on a branch where all
four check groups may pass. This file therefore asserts of it only what stayed
true -- that it is the unique registry entry naming the label as a value, and
that its own tier is ``estimate``. The 0.5.0 statement it gave way to is
``O-OPTOL-ASSURANCE-FORCED-ESTIMATE``, replayed in
``tests/golden/test_operator_tolerance_against_registry.py``.

WHAT REPLACED THE AST BAN ON THE WORD ``certified``
===================================================
Through 0.3.0 the control here was NEGATIVE: :class:`Assurance` had one member
and a test walked the syntax tree of every engine module banning the token, so
the label could not be produced at all. Contract 0.4.0 CLOSES C13 and makes the
label reachable, so that control expired -- and it is replaced by a STRONGER,
POSITIVE one rather than deleted:

* the exact literal ``"certified"`` may still appear nowhere in the engine
  except the enum member's own definition (prose mentioning the word is not a
  label and is not banned; a string EQUAL to the label is);
* ``Assurance.FIRST_ORDER`` may be WRITTEN in exactly one module,
  ``meat/certificate/certify.py``, and in exactly one expression there -- the
  single success return of the check chain. Everywhere else it may only be
  READ, inside a comparison;
* every other exit of that module goes through one ``_downgrade`` helper, which
  can only produce ``Assurance.ESTIMATE`` with a machine-readable reason;
* a record REFUSES to carry the label without the witness payload and an
  ``h_cert``, so the tier cannot be claimed without its evidence.

Together these say what the old ban said -- ``certified`` is unreachable except
through the certificate -- while permitting the one path the contract now
authorizes.
"""

from __future__ import annotations

import ast
import math
from dataclasses import replace
from pathlib import Path

import pytest
from dummy_bundles import build_bundle
from licensed_form import as_declared_form
from registry import ALPHA_GRID, ASSURANCE, ORACLES, is_superseded, oracle
from toy_declarations import toy

from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import RhsTag
from certiqs_key.meat_core.errors import SecurityGateError
from certiqs_key.meat_core.finitekey.keylength import (
    check_key_length_permitted,
    homogeneous_scalars,
    key_length,
    key_length_permitted,
    licensed_class_check,
)
from certiqs_key.solvers.frank_wolfe.general_keyrate import GeneralKeyRateResult

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "certiqs_key"

#: The ONE module where the enum member's value may be written as a literal:
#: the definition of the member itself.
LABEL_LITERAL_HOME = "foundations/assurance.py"

#: The ONE module that may WRITE ``Assurance.FIRST_ORDER``.
#: THE 0.4.0 WRITE HOME IS GONE. ``meat/certificate/certify.py`` was the one
#: expression that could assign the label; the certificate chain is deleted
#: with C13 and C18-C20, and 1.0.0 shelves the rung, so there is no write home
#: left and the rule is that the label is WRITTEN NOWHERE.
LABEL_WRITE_HOME = None

#: THE ONE PLACE THAT STILL WRITES THE SHELVED LABEL, and it is not this
#: module's to fix. ``certiqs_key.reductions`` belongs to the ``proof-reductions``
#: band, whose 1.0.0 re-entry is in flight, and spec/architecture.md Section
#: 12.1 forbids one module's band to edit another's package. The offender is
#: NAMED rather than the scan narrowed, so that a SECOND one anywhere in the
#: tree still fails this test: what is exempted is this file and this line, not
#: a tier.
#:
#: The label is shelved platform-wide (spec/architecture.md
#: Section 3.8) and "IS NEVER EMITTED", so a module that writes it is emitting
#: a tier no contract can earn.
CROSS_BAND_LABEL_WRITES: frozenset[str] = frozenset({"reductions/emit.py"})


def _engine_modules() -> list[Path]:
    """Return every source module under ``certiqs_key``, the floor included.

    The domain layer carries the label's DEFINITION (``LABEL_LITERAL_HOME``
    lives there with the tier vocabulary), as ``foundations`` does, so the scan
    covers both: the home is the one exception, not a whole tier.
    """
    return sorted(SOURCE_ROOT.rglob("*.py"))


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Return the ids of every docstring constant in ``tree``."""
    return {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        )
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }


def _certified_attribute_nodes(tree: ast.AST) -> list[ast.Attribute]:
    """Return every ``Assurance.FIRST_ORDER`` attribute access in ``tree``."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "CERTIFIED"
        and isinstance(node.value, ast.Name)
        and node.value.id == "Assurance"
    ]


def declaration_of(toy_id: str):
    """Return the validated declaration of a frozen toy."""
    return declaration_from_bundle(build_bundle(toy(toy_id)))


@pytest.mark.contract
@pytest.mark.oracle
def test_o_hlow_infinite_is_propagated_and_stops_the_key_length() -> None:
    """O-HLOW-INFINITE: +inf is a value, and it emits NO key-length claim."""
    entry = oracle("O-HLOW-INFINITE")
    assert entry.value == math.inf
    assert entry.kind == "fail-closed"
    with pytest.raises(SecurityGateError, match="rem:hlow-range"):
        key_length(
            rounds=1_000_000,
            h_low=math.inf,
            lambda_ec=0,
            eps_ev=2.0**-30,
            eps_pa=2.0**-30,
            alpha=1.5,
        )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_infinite_end_to_end(alpha: float) -> None:
    """O-HLOW-INFINITE on TOY-4c, through the solver: +inf, and no key length."""
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    result = solve(declaration_of("TOY-4c"), QicsSectorChoiOracle(), alpha=alpha)
    assert math.isinf(result.h_low)
    assert not math.isnan(result.h_low)
    assert result.key_length is None
    assert "rem:hlow-range" in result.key_length_reason
    # The same case under its closed code.
    assert result.key_length_reason_code == "objective_infinite"
    assert result.rate_per_round is None
    assert result.as_payload()["h_low"] == "inf"
    assert result.as_payload()["h_low_is_infinite"] is True


@pytest.mark.contract
@pytest.mark.oracle
def test_o_constraint_gate_frozen_verdicts() -> None:
    """O-CONSTRAINT-GATE: the four frozen verdicts, and both parts load-bearing.

    Part (i) is A TYPE CHECK ON THE DECLARED TAG of Definition ``def:homog``
    and compares no numbers; it does not project onto ``tau_A`` and compare a
    residual against a declared window.

    TOY-5 AND TOY-6 ARE LICENSED IN THE FORM THEIR RECORDS DECLARE, AND NOT IN
    THE FORM THE WIRE FORCES. Both records name the scalar ``c_1 = 1/2``, so the
    frozen verdict "L homogeneous, no license -> HARD-FAILS on part (ii)" is a
    verdict on the homogeneous declaration, which :func:`as_declared_form`
    rebuilds. The frozen 0.1.0 manifest carries the same entry in the
    ``general`` form (its builder types "every bound as an array"), and part
    (i) is a type check at EVERY ``d_A`` (``O-CGATE-DEGENERATE`` pins it): that
    carriage FAILS part (i) at ``d_A = 1`` too, and fails part (ii) as well.
    Both carriages lack the licence, so no key length is formed.

    TOY-7 IS THE ONE WHERE THE TAG DECIDES, and it is the case the amendment is
    for: ``d_A = 2``, a declared operator ``Theta = diag(1, 1/2)``, and a
    frozen record naming no scalar. At 0.5.0 it failed part (i) because no
    ``c`` exists; at 1.0.0 it fails because it declares ``general``. Same
    verdict, and the new mechanism cannot be passed by an entry merely NEAR
    ``c tau_A``.
    """
    entry = oracle("O-CONSTRAINT-GATE")
    assert entry.claims == ("C14", "C17")

    assert key_length_permitted(declaration_of("TOY-1")) is True  # L empty

    # Part (ii): licensed (degenerately, at d_A = 1) in the declared form, but
    # no supplier attestation.
    for toy_id in ("TOY-5", "TOY-6"):
        declaration = declaration_of(toy_id)
        assert declaration.alice_dim == 1
        assert toy(toy_id).constraint_list[0].homogeneous_scalar == 0.5
        licensed = as_declared_form(declaration, toy(toy_id))
        assert homogeneous_scalars(licensed) == (0.5,)
        check = licensed_class_check(licensed)
        assert check.licensed is True and check.vacuous is True
        assert licensed.attack_set_license is None
        assert key_length_permitted(licensed) is False
        with pytest.raises(SecurityGateError, match="attack_set_license") as raised:
            check_key_length_permitted(licensed)
        # PART (ii) ALONE FAILS, AND THE RECORD SAYS PART (i) WAS DEGENERATE.
        failing = str(raised.value).split("Failing:")[1]
        assert failing.lstrip().startswith("(ii)")
        assert "(i) entries" not in failing
        assert "part (i) is DEGENERATE here" in failing
        # THE TAG THE WIRE FORCED, recorded rather than assumed: the frozen
        # 0.1.0 builder types every bound as an array, so the entry crosses in
        # the `general` form and the DECLARATION-level scalar the frozen record
        # names (homogeneous_scalar = 0.5) has no field to travel in. Part (i)
        # is a type check at every d_A, so that carriage fails it -- and part
        # (ii) as well, both named.
        assert all(row.rhs_tag is RhsTag.GENERAL for row in declaration.constraint_list)
        assert homogeneous_scalars(declaration) is None
        general = licensed_class_check(declaration)
        assert general.licensed is False and general.vacuous is False
        assert key_length_permitted(declaration) is False
        with pytest.raises(SecurityGateError) as raised:
            check_key_length_permitted(declaration)
        failing = str(raised.value).split("Failing:")[1]
        assert "(i) entries [0] declare the `general` form" in failing
        assert "(ii) the declaration carries no attack_set_license" in failing

    # Part (i): TOY-7 declares `general` at d_A = 2, where the tag decides.
    declaration = declaration_of("TOY-7")
    assert declaration.alice_dim == 2
    assert toy("TOY-7").constraint_list[0].homogeneous_scalar is None
    assert homogeneous_scalars(declaration) is None
    assert key_length_permitted(declaration) is False
    with pytest.raises(SecurityGateError, match="`general` form"):
        check_key_length_permitted(declaration)


@pytest.mark.contract
@pytest.mark.oracle
def test_both_gate_parts_are_independently_load_bearing() -> None:
    """Neither the licensed form alone nor a licence alone opens the gate."""
    from dataclasses import replace

    # TOY-5 IN THE FORM ITS RECORD DECLARES (c_1 = 1/2): the frozen wire's
    # `general` carriage is never licensed, at d_A = 1 included.
    homogeneous_and_licensed = replace(
        as_declared_form(declaration_of("TOY-5"), toy("TOY-5")),
        attack_set_license={"certificate": "supplied by proof-reductions"},
    )
    assert key_length_permitted(homogeneous_and_licensed) is True
    check_key_length_permitted(homogeneous_and_licensed)
    # AND THE SAME LICENCE DOES NOT OPEN THE GATE FOR THE GENERAL CARRIAGE AT
    # d_A = 1: part (i) is a type check at every d_A (the owner's reading).
    general_and_licensed = replace(
        declaration_of("TOY-5"),
        attack_set_license={"certificate": "supplied by proof-reductions"},
    )
    assert general_and_licensed.alice_dim == 1
    assert key_length_permitted(general_and_licensed) is False
    with pytest.raises(SecurityGateError, match="`general` form"):
        check_key_length_permitted(general_and_licensed)

    licensed_but_general = replace(
        declaration_of("TOY-7"),
        attack_set_license={"certificate": "supplied by proof-reductions"},
    )
    assert key_length_permitted(licensed_but_general) is False
    with pytest.raises(SecurityGateError, match="`general` form"):
        check_key_length_permitted(licensed_but_general)


@pytest.mark.contract
def test_both_entry_points_decide_every_group_a_row_before_anything_is_computed() -> (
    None
):
    """`fail_closed` row 2: "refusal ... NO RESULT OF ANY KIND", on both doors.

    THE ROW IS THE WHOLE OF THE DECLARED DATA AND NOT ITS BOB HALF.
    ``admit_declaration`` decides ``bob_povm_admission`` and
    ``bob_povm_summation_exact``; ``alice_povm_exact``,
    ``alice_marginal_exact`` and ``constraint_operator_exact`` -- are decided in
    ``validate_declaration``. Both solve entry points call both, so a
    declaration that did not come through a bundle cannot reach the program
    with three Group A rows UNDECIDED and be solved to a full record
    (``reported_tier`` first-order, an emitted ``key_length``, and an
    ``assumption_ledger`` whose first key is ``declaration_valid``, asserting
    A-DECL on a declaration the module's own validator refuses under its own
    clauses).

    THE WITNESS IS THE REPORT'S: one licensed homogeneous entry whose operator
    blocks are the identity with an imaginary part of 0.25 on one diagonal
    entry, which ``def:admissible-declaration`` (iii) and (vi) make inadmissible and
    which no other rule of this module looks at.
    """
    import numpy as np

    from certiqs_key.meat_core.declaration.admission import AdmissionError
    from certiqs_key.meat_core.declaration.declaration import ConstraintEntry
    from certiqs_key.meat_core.declaration.validation import validate_declaration
    from certiqs_key.meat_core.reasons import GroupAPredicate, RefusalReason
    from certiqs_key.solvers.frank_wolfe.keyrate import solve, solve_declaration

    declaration = declaration_of("TOY-5")
    blocks = {
        sector: np.eye(dim, dtype=np.complex128)
        for sector, dim in declaration.sector_dims.items()
    }
    first = declaration.sector_index_set[0]
    blocks[first] = blocks[first].copy()
    blocks[first][0, 0] += 0.25j
    broken = replace(
        declaration,
        constraint_list=(
            ConstraintEntry(
                operator_blocks=blocks,
                relation=ConstraintRelation.PRECEQ,
                bound=0.5,
                rhs_tag=RhsTag.HOMOGENEOUS,
            ),
        ),
        attack_set_license={"certificate": "supplied for this fixture"},
    )

    # THE VALIDATOR REFUSES IT, NAMING THE ROW.
    with pytest.raises(AdmissionError) as refusal:
        validate_declaration(broken)
    assert refusal.value.reason is RefusalReason.DECLARATION_NOT_EXACTLY_ADMISSIBLE
    assert refusal.value.predicate is GroupAPredicate.CONSTRAINT_OPERATOR_EXACT

    # AND SO DO BOTH SOLVE PATHS, WITH THE SAME REASON AND THE SAME ROW, before
    # any oracle is consulted: the stand-in raises if it is asked anything at
    # all, so a refusal that let the run start would fail here instead.
    class Untouchable:
        """An oracle that must never be consulted, and says so if it is."""

        def capabilities(self) -> object:
            raise AssertionError("the declaration should have been refused")

        def minimize(self, problem: object) -> object:
            raise AssertionError("the declaration should have been refused")

    for entry_point in (solve, solve_declaration):
        with pytest.raises(AdmissionError) as raised:
            entry_point(broken, Untouchable())  # type: ignore[arg-type]
        assert raised.value.reason is RefusalReason.DECLARATION_NOT_EXACTLY_ADMISSIBLE
        assert raised.value.predicate is GroupAPredicate.CONSTRAINT_OPERATOR_EXACT

    # AND THE DECLARATION THE FIXTURE WAS BUILT FROM IS STILL ADMITTED, so what
    # the two refusals show is the row and not a broken fixture.
    assert validate_declaration(declaration) is not None


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
@pytest.mark.parametrize("toy_id", ("TOY-5", "TOY-6", "TOY-7"))
def test_a_blocked_gate_still_reports_the_numerical_value(toy_id: str) -> None:
    """Numerical use outside the security chain is unrestricted (Section 2.1)."""
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    result = solve(declaration_of(toy_id), QicsSectorChoiOracle(), alpha=1.5)
    assert result.key_length is None
    assert math.isfinite(result.h_low)
    assert result.h_low >= 0.0
    # THE ACHIEVED ASSURANCE AND THE REPORTED TIER ARE DIFFERENT QUESTIONS at
    # 1.0.0, and a blocked gate separates them: the bracket may be EARNED --
    # every hypothesis of Theorem thm:firstorder held -- while the run claims
    # only the estimate, because reported_tier is `first-order` "EXACTLY WHEN
    # h_lb is present AND a key_length is emitted from it" (the reported_tier
    # output row) and the gate withheld the length. A withheld length is no
    # claim.
    assert result.reported_tier is Assurance.ESTIMATE
    # AND THE LEDGER NAMES NO SOLVER TRUST ROOT FOR THE RECORD'S h_lb. The gate
    # withheld the key length; it did not withdraw the bracket.
    # Derived by hand from the frank-wolfe interface: A-LMO's emission rule
    # reads "on no run: superseded, and in the closure of no live claim", and
    # thm:firstorder does not assume it -- the feasible side of every bracket
    # is the bound req:verified-feasible-side verifies from the oracle's dual,
    # so exact_linear_oracle is in the ledger of no run.
    if result.h_lb is not None:
        assert result.certificate["assurance_reason"] == "first_order_reported"
        assert "exact_linear_oracle" not in result.assumption_ledger


@pytest.mark.contract
@pytest.mark.oracle
def test_o_assurance_estimate_is_the_default_and_the_fallback() -> None:
    """O-ASSURANCE-ESTIMATE: estimate is what a run starts at.

    The frozen entry pins the word ``estimate``, and a record with no lower
    bound can carry nothing else: the general record has no default and
    REFUSES any other tier without a bound.

    THE MEMBERSHIP LINE IS AN EXACT SET EQUALITY over three names, the third
    being ``first-order``, the live middle rung of spec/architecture.md
    section 3.8's ladder (added by spec/architecture.md 2.9 section 5).
    ``certified`` is in the enum as the top rung and is controlled by every
    check on the ``certified`` literal below.
    """
    entry = oracle("O-ASSURANCE-ESTIMATE")
    assert entry.claims == ("C13",)
    assert entry.value == ASSURANCE == "estimate"
    # THREE MEMBERS, ALL LIVE. Derived by hand from foundations/def:tiers
    # ("one of the following three labels"): the enum IS the ladder and the
    # equality stays exact.
    assert {member.value for member in Assurance} == {
        "estimate", "first-order", "certified"
    }
    assert str(Assurance.ESTIMATE) == "estimate"
    unbounded = _result(h_lb=None, tier=Assurance.ESTIMATE, key_length=None)
    assert unbounded.reported_tier is Assurance.ESTIMATE
    with pytest.raises(ValueError, match="first-order requires a lower bound"):
        _result(h_lb=None, tier=Assurance.FIRST_ORDER, key_length=None)


@pytest.mark.contract
def test_the_certified_label_is_written_only_where_the_key_length_is_formed() -> None:
    """The label controls, under the strongest rule available.

    A scan of the engine's syntax tree for an occurrence of the label outside
    a comparison would ban ASSIGNING the name, not naming it.

    THERE IS NO CERTIFICATE CHAIN AND NO ENUM MEMBER FOR THE DROPPED RUNG. The
    rung is carried in no form -- not the tier name, not the enum member, not
    the witness apparatus (PRINCIPLES.md section 10) -- so there is no member to
    assign. The enum has no such member, so an assignment is an ERROR AT IMPORT
    rather than a defect a scan must find, and the residue of the scan is kept
    below because it is cheap.
    """
    # Derived by hand from frank-wolfe/req:certified-evaluation
    # (vi) ("the run reports it at the certified tier") and foundations/req:tiers:
    # the label is live, and the one place that may write it is the record that
    # forms the key length from the certified number.
    assert str(Assurance.CERTIFIED) == "certified"
    offenders = [
        path.relative_to(SOURCE_ROOT).as_posix()
        for path in _engine_modules()
        if _certified_attribute_nodes(ast.parse(path.read_text(encoding="utf-8")))
    ]
    assert offenders == ["solvers/frank_wolfe/general_keyrate.py"], offenders



@pytest.mark.contract
def test_a_record_refuses_the_label_without_its_evidence() -> None:
    """The structural refusals of contract Section 2.2, one per way to fake a tier.

    THERE ARE FOUR. The evidence a label is a statement about is the
    PER-ITERATE BRACKET RECORD, and the certified rung adds two refusals of its
    own. Held against the one record every run writes (the general record).
    """
    # (1) The label without its evidence. `first-order` is the statement that
    # every hypothesis held AT EACH CONTRIBUTING ITERATE, so a record claiming
    # it with no iterate to point at claims something about an empty set --
    # and the index set of Eq. eq:hlb is FINITE AND NON-EMPTY.
    with pytest.raises(ValueError, match="PER-ITERATE record"):
        _result(h_lb=0.5, tier=Assurance.FIRST_ORDER, key_length=5, per_iterate=[])

    # (2) THE CERTIFIED LABEL WITHOUT ITS EVIDENCE. Derived by hand from
    # frank-wolfe/req:certified-evaluation (vi) and
    # meat-core's `reported_tier` row: `certified` exactly where a key length
    # is formed from the certified number, so the label with the first-order
    # reason code is refused.
    with pytest.raises(ValueError, match="certified tier is reported"):
        _result(h_lb=0.5, tier=Assurance.CERTIFIED, key_length=5)

    # (3) A tier with no bound. reported_tier is `first-order` EXACTLY WHEN
    # h_lb is present and a key_length is emitted from it.
    with pytest.raises(ValueError, match="first-order requires a lower bound"):
        _result(h_lb=None, tier=Assurance.FIRST_ORDER, key_length=0)

    # (4) A length on an estimate run. The warrant of a key length is
    # cor:keylength-bound, which consumes max{0, h} for an h ESTABLISHED to
    # satisfy h <= h_low; h_low is the objective at the returned point and is
    # NOT established to lie on either side of h_low (lem:estimate), so a
    # length here would rest on no claim of this contract.
    with pytest.raises(ValueError, match="an estimate cannot emit a key length"):
        _result(h_lb=None, tier=Assurance.ESTIMATE, key_length=5)
    # And the control: with its evidence the label stands.
    assert _result(h_lb=0.5, tier=Assurance.FIRST_ORDER, key_length=5).key_length == 5


def _result(
    *,
    h_lb: float | None,
    tier: Assurance,
    key_length: int | None,
    per_iterate: list[dict[str, object]] | None = None,
) -> GeneralKeyRateResult:
    """Return a minimal result record with ``h_lb`` and the tier asked for."""
    return GeneralKeyRateResult(
        alpha=1.5,
        rounds=1,
        h_low=1.0,
        h_lb=h_lb,
        h_lb_dropped=None,
        dropped_set=(),
        key_length=key_length,
        # cor:composed-security (iii): present exactly when the length is.
        security_parameter=None if key_length is None else 0.5,
        net_key_length=key_length,
        key_length_reason="reason",
        # The closed reason code beside the prose.
        key_length_reason_code=(
            "iterate_not_feasible" if key_length is None else "first_order_reported"
        ),
        reported_tier=tier,
        first_order_clamped=False,
        optimized_q={},
        predicted_statistics={},
        block_contributions={},
        sector_weight_report={},
        # ONE CONTRIBUTING ITERATE by default, so that the refusals below are
        # each about the field they name and not about missing evidence.
        certificate={
            "per_iterate": (
                [{"iteration": 1, "withdrawal": None}]
                if per_iterate is None
                else per_iterate
            )
        },
        sector_report={},
        # The interface's own rows, emitted on every run, and REQUIRED fields.
        map_validation_report={"declaration_admitted_exactly": True},
        assumption_ledger=("key_register",),
        assumption_ids=("A-KEYREG",),
        # One entry per ledger row; the values are not under test.
        assumption_bindings=(("key_register", ()),),
        deductions={},
        constraint_entries_through_a_reductions_chain=0,
        estimate_point_relaxed_member=True,
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_every_registry_entry_is_estimate_tier() -> None:
    """Nothing in the frozen registry claims anything else either.

    Exactly ONE entry NAMES ``certified`` as the value it pins --
    ``O-ASSURANCE-CERTIFIED-GATE``, whose whole subject is when the label may be
    emitted -- and naming it is not claiming it. The exception is enumerated by
    ID so that a second one is a defect this test catches.

    THE UNIQUENESS HOLDS FOR GROUP 9, which has thirteen entries
    including ``O-OPTOL-ASSURANCE-FORCED-ESTIMATE``, whose subject is a route
    to ``estimate`` and whose pinned value is a REASON STRING and not a tier --
    "naming ``certified`` is not claiming it, and this entry does not name it as
    a value at all". So the exception set is unchanged, while the marked entry's
    biconditional is asserted nowhere in this file.
    """
    for entry in ORACLES:
        assert entry.assurance == "estimate", entry.oracle_id
    naming = {record.oracle_id for record in ORACLES if record.value == "certified"}
    assert naming == {"O-ASSURANCE-CERTIFIED-GATE"}
    assert is_superseded("O-ASSURANCE-CERTIFIED-GATE")
    forced = oracle("O-OPTOL-ASSURANCE-FORCED-ESTIMATE")
    assert forced.value == "declared_operator_tolerance_open"
    assert forced.assurance == "estimate"
