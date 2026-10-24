"""The tier a run that earns its bracket reaches on this machine.

WHY. The certified evaluation (``meat-core/frank-wolfe/req:certified-
evaluation``) runs by default and needs the optional ball arithmetic (the
``certify`` extra); without it a run reports its first-order number with the
reason ``certifier_unavailable`` and is never an error. A test of a run whose
bracket is earned and whose final points certify therefore expects
``certified`` where the library is installed and ``first-order`` where it is
not, so it asserts the stronger statement wherever it can be made.
"""

from __future__ import annotations

from certiqs_key.foundations import balls
from certiqs_key.foundations.assurance import Assurance

#: The tier of a run whose bracket is earned and whose final points certify.
BRACKET_TIER: Assurance = (
    Assurance.CERTIFIED if balls.AVAILABLE else Assurance.FIRST_ORDER
)

__all__ = ["BRACKET_TIER"]
