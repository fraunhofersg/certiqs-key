"""The error-correction leak lambda_EC, estimated from the honest model before the run.

``lambda_EC`` is a declared input of the key length: one additive term in bits,
TOTAL over the n rounds, in ``meat-core/thm:keylength`` (Eq. ``eq:keylength``)
and ``cor:keylength-bound`` (Eq. ``eq:keylength-h``). Reconciliation is one-way
from the declared key holder. A-FIXED (``meat-core/ass:fixed``) requires it to
be fixed before the first round. This module fixes it from the HONEST model's
distribution, which is known before the run, and from nothing observed.

THE ESTIMATE
============
::

    lambda_EC = ceil( f_EC * n * H(R | O_nonholder, K) )

over the honest per-round distribution of the raw outcome pairs ``(x, v)``:

- ``R = r(x, v)``, the declaration's raw key map (``protocol-compiler``
  ``eq:rdef``): the holder's key symbol, ``perp`` on a failing class. ``perp`` is
  kept as a symbol; it is determined by ``K`` and contributes nothing;
- ``O_nonholder``, the non-holder's readout in the declaration's party
  partition;
- ``K``, the announcement class ``a(x, v)``
  (:meth:`~certiqs_key.protocol_compiler.declaration.CandidateDeclaration.announcement`,
  which reads the pair spelling and the transcript alike).

``H(R | O_nonholder, K)`` is the Slepian-Wolf rate of one-way reconciliation
from the holder, and ``f_EC >= 1`` is the reconciliation inefficiency of a
practical code.

THE DEFAULT f_EC = 1.1 is the value of Kamin, Burniston and Tan
(``kamin2025renyi``, Sec. VII, Eq. (123): "with fEC = 1.1"), the paper this
project's Renyi framework follows; it cites Elkouss, Martinez-Mateo and Martin
(arXiv:1007.1616) for it. It is a
parameter: a caller with a measured code efficiency passes that instead.

This module computes the estimate from the typed declaration, so that a run
needs no frontend.

WHAT THIS IS NOT. It is not a security claim. The key length is sound for the
declared ``lambda_EC`` provided the reconciliation transcript is no longer than
it (A-FIXED fixes that length; ``ass:keyreg``). A value below what the real
code needs is a code that fails more often, which error verification turns into
aborts: a robustness cost, not a secrecy one. Nor is it wired into a
configuration by default: the bbm92 document keeps ``lambda_ec = 0`` (the
estimator is opt-in only).
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any

from certiqs_key.foundations.errors import CertiqsError
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.protocol_compiler.spec import Party
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.pipeline import Preparation

__all__ = [
    "DEFAULT_F_EC",
    "FORMULA",
    "F_EC_SOURCE",
    "LambdaEcEstimate",
    "LambdaEcEstimateError",
    "estimate_lambda_ec",
    "with_estimated_lambda_ec",
]

#: The default reconciliation inefficiency; see the module docstring.
DEFAULT_F_EC = 1.1
#: Where the default comes from, with its locator.
F_EC_SOURCE = "kamin2025renyi, Sec. VII, Eq. (123)"
#: The formula, as recorded beside every estimate.
FORMULA = "lambda_EC = ceil(f_EC * n * H(R | O_nonholder, K)) over the honest raw joint"

PERP = "perp"


class LambdaEcEstimateError(ValueError):
    """The estimate cannot be formed from what was supplied; never a guess."""


@dataclass(frozen=True)
class LambdaEcEstimate:
    """One estimate, with everything it was computed from."""

    lambda_ec: int
    f_ec: float
    rounds: int
    #: ``H(R | O_nonholder, K)`` in bits per round.
    conditional_entropy: float
    #: The honest probability that a round passes sifting.
    p_pass: float
    key_holder: str

    def as_payload(self) -> dict[str, Any]:
        """Return the estimate as JSON, for a configuration's provenance."""
        return {
            "lambda_ec": self.lambda_ec,
            "f_ec": self.f_ec,
            "f_ec_source": F_EC_SOURCE if self.f_ec == DEFAULT_F_EC else "caller",
            "rounds": self.rounds,
            "conditional_entropy_bits_per_round": self.conditional_entropy,
            "p_pass": self.p_pass,
            "key_holder": self.key_holder,
            "formula": FORMULA,
        }


def estimate_lambda_ec(
    declaration: CandidateDeclaration,
    raw_joint: Mapping[tuple[str, str], Fraction],
    *,
    rounds: int,
    f_ec: float = DEFAULT_F_EC,
) -> LambdaEcEstimate:
    """Return ``ceil(f_EC n H(R | O_nonholder, K))`` over ``raw_joint``.

    Args:
        declaration: the compiled declaration whose raw key map, partition and
            announcements define ``R``, ``O_nonholder`` and ``K``.
        raw_joint: the honest per-round distribution over ``X x V``, exactly
            (:attr:`~certiqs_key.runs.pipeline.Preparation.raw_joint_distribution`).
        rounds: ``n``, total channel uses.
        f_ec: the reconciliation inefficiency, at least 1.

    Raises:
        LambdaEcEstimateError: on an inefficiency below 1, a distribution that is
            not one, or a pair the declaration does not tabulate.
    """
    if not (math.isfinite(f_ec) and f_ec >= 1.0):
        raise LambdaEcEstimateError(f"f_EC is {f_ec!r}; an inefficiency is at least 1")
    if rounds < 1:
        raise LambdaEcEstimateError(f"rounds is {rounds}")
    total = sum(raw_joint.values(), Fraction(0))
    if any(p < 0 for p in raw_joint.values()) or total != 1:
        raise LambdaEcEstimateError(
            f"the raw joint distribution sums to {total} or has a negative entry"
        )
    holder = declaration.key_holder
    nonholder = Party.BOB if holder is Party.ALICE else Party.ALICE
    joint_rok: dict[tuple[object, object, object], Fraction] = defaultdict(Fraction)
    joint_ok: dict[tuple[object, object], Fraction] = defaultdict(Fraction)
    p_pass = Fraction(0)
    for pair, p in raw_joint.items():
        if p == 0:
            continue
        x, v = pair
        try:
            r = declaration.key_map[(x, v)]
            kappa = declaration.announcement(x, v)
            o = declaration.partition.readout(nonholder, x, v)
        except (KeyError, ValueError, CertiqsError) as error:
            raise LambdaEcEstimateError(
                f"the declaration does not determine (R, O, K) at {pair!r}: {error}"
            ) from error
        joint_rok[(r, o, kappa)] += p
        joint_ok[(o, kappa)] += p
        if r != PERP:
            p_pass += p
    entropy = 0.0
    for (_symbol, readout, cls), mass in joint_rok.items():
        ratio = mass / joint_ok[(readout, cls)]
        if ratio != 1:
            entropy -= float(mass) * math.log2(float(ratio))
    entropy = max(0.0, entropy)
    bits = f_ec * rounds * entropy
    return LambdaEcEstimate(
        lambda_ec=math.ceil(bits) if bits > 0 else 0,
        f_ec=f_ec,
        rounds=rounds,
        conditional_entropy=entropy,
        p_pass=float(p_pass),
        key_holder=str(holder),
    )


def with_estimated_lambda_ec(
    config: RunConfig, preparation: Preparation, *, f_ec: float = DEFAULT_F_EC
) -> tuple[RunConfig, LambdaEcEstimate]:
    """Return ``config`` with ``lambda_ec`` set to the estimate, and the estimate.

    ``preparation`` is the instance's ``surface.preparation(config)``. It must
    carry the honest raw joint distribution; an instance that computes none
    gives no estimate, rather than one approximated from the acceptance alphabet.
    """
    if preparation.raw_joint_distribution is None:
        raise LambdaEcEstimateError(
            "the preparation carries no honest raw joint distribution over X x V"
        )
    estimate = estimate_lambda_ec(
        preparation.declaration,
        preparation.raw_joint_distribution,
        rounds=config.rounds,
        f_ec=f_ec,
    )
    parameters = replace(config.parameters, lambda_ec=estimate.lambda_ec)
    return config.with_(parameters=parameters), estimate
