"""The statistics request built from a frozen construction case.

Shared by ``tests/golden/test_statistics_acceptance_against_registry.py`` and
``tests/golden/test_statistics_acceptance_docking.py``. It lives here because a
test module importing a SIBLING TEST MODULE by bare name does not collect under
the configured ``--import-mode=importlib`` (``tests/golden`` is not on
``sys.path``; ``tests/support`` is, by ``tests/conftest.py``), and every
documented gate passes ``-o addopts=""`` and so never saw it.
"""

from __future__ import annotations

from registry_statistics_acceptance import ConstructionCase

from certiqs_key.statistics import AcceptanceRequest, BudgetAllocation


def request_of(case: ConstructionCase) -> AcceptanceRequest:
    """Return the frozen construction case as this module's input record.

    ``allocation_rule`` is honoured rather than bypassed: where the case
    declares ``uniform-default`` the request carries ``None`` and the module
    materializes the rule itself, so the frozen ``eps_lower`` / ``eps_upper``
    columns are checked against what the DEFAULT produces and not merely fed
    back in.
    """
    allocation = (
        None
        if case.allocation_rule == "uniform-default"
        else BudgetAllocation(case.eps_lower, case.eps_upper)
    )
    return AcceptanceRequest(
        alphabet=case.outcomes,
        honest=dict(zip(case.outcomes, case.honest, strict=True)),
        rounds=case.rounds,
        budget=case.ecomp,
        constrained=case.constrained,
        allocation=allocation,
    )
