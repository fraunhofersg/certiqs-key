"""The named deductions of the key-length expression, for the result record.

WHERE THE RECORD LIVES. With one Frank-Wolfe driver every run writes the
general record,
:class:`~certiqs_key.solvers.frank_wolfe.general_keyrate.GeneralKeyRateResult`,
which carries the same refusals in its shape: ``reported_tier`` is
``first-order`` exactly when a lower bound is present and a ``key_length`` was
emitted from it, ``key_length`` is absent (never zero, never clamped) with a
reason when no claim may be emitted, and ``h_low`` is an estimate. What stays
here is the part of the record that is the core's arithmetic.
"""

from __future__ import annotations

import math


def deductions_of(
    *,
    lambda_ec: int,
    eps_ev: float,
    eps_pa: float,
    alpha: float,
    ideal_hash: bool,
) -> dict[str, float]:
    """Return the named deductions of Eq. ``eq:keylength``, term by term.

    spec/architecture.md 4.4 asks for the error-correction, verification and
    privacy-amplification deductions separately rather than as one number, so
    that a reader can see which budget cost what.
    """
    return {
        "error_correction_lambda_ec": float(lambda_ec),
        "error_verification": float(math.ceil(-math.log2(eps_ev))),
        "privacy_amplification": (alpha / (alpha - 1.0)) * (-math.log2(eps_pa)),
        "accepted_state_flag_bonus": 1.0,
        "two_universal_hash_penalty": 0.0 if ideal_hash else 1.0,
    }
