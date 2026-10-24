"""Three dead symbols stay absent.

WHY THIS FILE EXISTS. ``sequence_payload``, ``admissible_isometry`` and
``checks_nothing`` are dead code that must not return, and this test is the
record that keeps them out: a symbol that returns is a change someone has to
declare again.

None of the three was named by a claim, an interface row or a binding, so
nothing under ``spec/`` moves with them.
"""

from __future__ import annotations

from certiqs_key.meat_core.finitekey import keylength, result
from certiqs_key.meat_core.objective import choi


def test_the_dead_symbols_stay_absent() -> None:
    assert not hasattr(result, "sequence_payload")
    assert not hasattr(choi.ChoiParametrization, "admissible_isometry")
    assert not hasattr(keylength.LicensedClassCheck, "checks_nothing")
