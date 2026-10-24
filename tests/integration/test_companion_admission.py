"""The compiled reference companion and its evaluation-only admission.

``protocol-compiler/req:reference-companion-compiled`` and
``meat-core/req:companion-admission`` with ``meat-core/prop:reference-companion``
(i): the companion is compiled from the same specification, differs from the
declaration in the measured family and the replaced link's entries and in
nothing else, and is admitted beside the declaration, deciding its shape and
importing the rest. One licensed-route run of the optical instance at a small
budget supplies the declaration and its companion.
"""

from __future__ import annotations

import tempfile
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest

from certiqs_key.domain.constraints import ConstraintEntry
from certiqs_key.foundations.blocks import BlockOperator
from certiqs_key.foundations.exact import Cx
from certiqs_key.meat_core.declaration.companion import (
    AdmittedCompanion,
    CompanionNotAdmitted,
    NotAdmittedReason,
    admit_reference_companion,
)
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.protocol_compiler.companion import CompiledReferenceCompanion
from certiqs_key.runs.config import SolverSettings
from certiqs_key.runs.pipeline import SliceResult
from certiqs_key.solvers.frank_wolfe.keyrate import general_declaration_of

pytest.importorskip("qics")
pytestmark = pytest.mark.contract

PORTS = ("H", "V", "D", "A")


@pytest.fixture(scope="module")
def licensed() -> tuple[GeneralDeclaration, CompiledReferenceCompanion]:
    """Run the noisy device on the licensed route; return D and its companion."""
    from instances.optical_bb84.surface import default_config, runner

    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    base = default_config(solver=SolverSettings(method="fw", max_iterations=3))
    config = base.with_(
        device={
            **base.device,
            "route": "licensed",
            "efficiency": dict.fromkeys(PORTS, F(9, 10)),
            "dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
        }
    )
    with tempfile.TemporaryDirectory() as tmp:
        outcome = runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(config, 0)
    assert isinstance(outcome, SliceResult)
    companion = outcome.reference_companion
    assert isinstance(companion, CompiledReferenceCompanion)
    return general_declaration_of(outcome.reread), companion


def test_the_companion_shares_every_component_but_the_family_and_its_entries(
    licensed: tuple[GeneralDeclaration, CompiledReferenceCompanion],
) -> None:
    """prop:reference-companion (i); req:companion-admission (i), (iii)."""
    declaration, companion = licensed
    admitted = admit_reference_companion(declaration, companion)
    assert isinstance(admitted, AdmittedCompanion)
    evaluated = admitted.declaration
    for name in (
        "alice", "alice_marginal", "alice_alphabet", "alice_form", "transcript",
        "accept_statistic", "key_map", "key_holder", "acceptance_values",
        "key_value_count", "acceptance_set", "rounds", "parameters",
        "party_partition", "sector_block_kind", "attack_set_license",
        "source_replacement_license",
    ):
        assert getattr(evaluated, name) == getattr(declaration, name), name
    (factor,) = evaluated.factors
    (original,) = declaration.factors
    assert (factor.label, factor.alphabet, factor.sectors) == (
        original.label, original.alphabet, original.sectors,
    )
    assert any(
        not np.array_equal(factor.blocks[v][s], original.blocks[v][s])
        for v in factor.alphabet
        for s in factor.sectors.labels
    ), "the companion's family is the reference's, not the snap's"
    # The one replaced link entry, relaxed; the specification's own entry kept.
    (replacement,) = companion.replacements
    assert replacement.relaxed == (True,)
    assert len(evaluated.constraint_list) == len(declaration.constraint_list)
    assert evaluated.constraint_list[: replacement.start] == (
        declaration.constraint_list[: replacement.start]
    )
    relaxed = evaluated.constraint_list[replacement.start]
    assert relaxed.scalar_bound < 0
    # (iii): measured, recorded, deciding nothing.
    assert admitted.measurements and all(
        item.completeness_defect < 1e-12 for item in admitted.measurements
    )


def test_a_shape_the_declaration_does_not_have_is_not_admitted(
    licensed: tuple[GeneralDeclaration, CompiledReferenceCompanion],
) -> None:
    """req:companion-admission (i): the reason names the component."""
    declaration, companion = licensed
    (factor,) = companion.factors
    wrong = replace(
        companion,
        factors=(replace(factor, sector_dims=(*factor.sector_dims[:-1], 99)),),
    )
    refused = admit_reference_companion(declaration, wrong)
    assert isinstance(refused, CompanionNotAdmitted)
    assert refused.reason is NotAdmittedReason.MEASURED_FAMILY_SHAPE
    longer = replace(companion, base_entry_count=companion.base_entry_count + 1)
    refused = admit_reference_companion(declaration, longer)
    assert isinstance(refused, CompanionNotAdmitted)
    assert refused.reason is NotAdmittedReason.CONSTRAINT_LIST


def test_an_entry_off_the_binary64_grid_is_not_admitted(
    licensed: tuple[GeneralDeclaration, CompiledReferenceCompanion],
) -> None:
    """req:companion-admission (i): each replacing entry is Hermitian binary64."""
    declaration, companion = licensed
    (replacement,) = companion.replacements
    (entry,) = replacement.entries
    blocks = list(entry.operator.blocks)
    third = Cx(F(1, 3), F(0))
    blocks[0] = tuple(
        tuple(third if i == j == 0 else value for j, value in enumerate(row))
        for i, row in enumerate(blocks[0])
    )
    off_grid = ConstraintEntry(
        operator=BlockOperator.of(entry.operator.sector_map, blocks),
        relation=entry.relation,
        rhs=entry.rhs,
        arriving_tag=entry.arriving_tag,
        scope=entry.scope,
    )
    wrong = replace(
        companion, replacements=(replace(replacement, entries=(off_grid,)),)
    )
    refused = admit_reference_companion(declaration, wrong)
    assert isinstance(refused, CompanionNotAdmitted)
    assert refused.reason is NotAdmittedReason.ENTRY_NOT_HERMITIAN_BINARY64


def test_each_replacing_entry_carries_its_own_tag(
    licensed: tuple[GeneralDeclaration, CompiledReferenceCompanion],
) -> None:
    """prop:reference-companion (ii), condition (vi): tags read as def:compile does.

    A replacing entry is tagged off its own datum,
    the arriving tag deciding party_local, never by the first entry of the
    link it replaces. The licensed link's entry is homogeneous; the same entry
    arriving tagged party_local keeps that tag in D^ref.
    """
    from certiqs_key.domain.constraints import RhsTag
    from certiqs_key.meat_core.declaration.general import GeneralRhsTag

    declaration, companion = licensed
    (replacement,) = companion.replacements
    (entry,) = replacement.entries
    original = declaration.constraint_list[replacement.start]
    assert original.rhs_tag is GeneralRhsTag.HOMOGENEOUS
    admitted = admit_reference_companion(declaration, companion)
    assert isinstance(admitted, AdmittedCompanion)
    assert (
        admitted.declaration.constraint_list[replacement.start].rhs_tag
        is GeneralRhsTag.HOMOGENEOUS
    )
    tagged = replace(entry, arriving_tag=RhsTag.PARTY_LOCAL)
    other = replace(
        companion, replacements=(replace(replacement, entries=(tagged,)),)
    )
    admitted = admit_reference_companion(declaration, other)
    assert isinstance(admitted, AdmittedCompanion)
    assert (
        admitted.declaration.constraint_list[replacement.start].rhs_tag
        is GeneralRhsTag.PARTY_LOCAL
    )
