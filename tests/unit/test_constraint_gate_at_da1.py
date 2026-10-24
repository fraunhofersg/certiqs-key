"""Part (i) of the constraint gate at d_A = 1, in the general format.

Part (i) is a type check at every d_A. The expectations are read off the claims:

* ``protocol-compiler/def:homog``, which ``meat-core/def:homog`` cites: a list
  is licensed when every entry is declared homogeneous (trusted-source mode)
  or party-local; "a general entry ... is not licensed". No clause depends on
  d_A, so a ``general`` 1x1 entry is unlicensed at d_A = 1.
* ``meat-core/rem:cgate``: at d_A = 1 the check "rejects nothing a producer
  cannot trivially avoid", and in untrusted-source mode it is vacuously true.
* ``meat-core/req:degenerate-gate-report``: in those two cases a passing part
  (i) is evidence of nothing, "nor ... about a party-local entry".

The basic format's ``licensed_class_check`` is pinned against the frozen
oracle ``O-CGATE-DEGENERATE`` in tests/golden/test_source_modes_against_registry.py;
this file holds the general format's ``general_security_gates`` to the same
reading, which the run path uses.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from general_toys import two_factor_general

from certiqs_key.meat_core.declaration.general import (
    GeneralDeclaration,
    GeneralRhsTag,
)
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    gate_failures,
    general_security_gates,
)

LICENCE = {"certificate": "supplied for this test"}


def _trusted_da1(tag: GeneralRhsTag) -> GeneralDeclaration:
    """Return the two-factor toy at total d_A = 1 in trusted mode, one entry.

    tau_A = [1] is the one marginal d_A = 1 admits
    (prop:trivial-alice-system). The entry keeps its scope and operator; only
    its tag, and with a ``general`` tag its right-hand side [1/4], change.
    """
    untrusted = two_factor_general(party_local=False)
    trusted = replace(
        untrusted, alice_marginal={"t0": np.eye(1, dtype=np.complex128)}
    )
    entry = trusted.constraint_list[0]
    bound: float | dict[str, np.ndarray] = (
        {"t0": np.array([[0.25]], dtype=np.complex128)}
        if tag is GeneralRhsTag.GENERAL
        else 0.25
    )
    return replace(
        trusted, constraint_list=(replace(entry, rhs_tag=tag, bound=bound),)
    )


def test_a_general_entry_at_da1_fails_part_i_even_with_a_licence() -> None:
    declaration = replace(
        _trusted_da1(GeneralRhsTag.GENERAL), attack_set_license=LICENCE
    )
    assert declaration.alice_dim == 1 and declaration.is_trusted_source
    gates = general_security_gates(declaration)
    assert gates["licensed_class_passed"] is False
    assert gates["licensed_class_vacuous"] is False
    assert gates["attack_set_license_present"] is True
    assert gates["key_length_permitted"] is False
    assert "at any d_A" in gates["licensed_class_reason"]
    assert "rem:cgate" in gates["licensed_class_reason"]
    (failure,) = gate_failures(gates)
    assert failure.startswith("(i)")


def test_without_a_licence_both_parts_are_named() -> None:
    gates = general_security_gates(_trusted_da1(GeneralRhsTag.GENERAL))
    failures = gate_failures(gates)
    assert [failure[:4] for failure in failures] == ["(i) ", "(ii)"]
    # A FAILING part (i) is a verdict, so the (ii) line does not call it
    # degenerate.
    assert "DEGENERATE" not in failures[1]


def test_a_homogeneous_entry_at_da1_passes_degenerately() -> None:
    declaration = replace(
        _trusted_da1(GeneralRhsTag.HOMOGENEOUS), attack_set_license=LICENCE
    )
    gates = general_security_gates(declaration)
    assert gates["licensed_class_passed"] is True
    assert gates["licensed_class_vacuous"] is True
    assert gates["key_length_permitted"] is True
    assert gates["licensed_class_reason"].startswith("DEGENERATE")
    unlicensed = general_security_gates(_trusted_da1(GeneralRhsTag.HOMOGENEOUS))
    (failure,) = gate_failures(unlicensed)
    assert failure.startswith("(ii)")
    assert "part (i) is DEGENERATE here" in failure


def test_a_party_local_entry_passes_as_no_evidence_at_da1_and_untrusted() -> None:
    """req:degenerate-gate-report: no evidence "about a party-local entry either"."""
    trusted = general_security_gates(_trusted_da1(GeneralRhsTag.PARTY_LOCAL))
    assert trusted["licensed_class_passed"] is True
    assert trusted["licensed_class_vacuous"] is True
    assert trusted["party_local_entries"] == [0]
    assert "party-local" in trusted["licensed_class_reason"]
    untrusted = general_security_gates(two_factor_general(party_local=True))
    assert untrusted["licensed_class_passed"] is True
    assert untrusted["licensed_class_vacuous"] is True
    assert untrusted["licensed_class_reason"].startswith("VACUOUS")
