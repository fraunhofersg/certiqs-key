"""One worked tagged decoy declaration, shared by the tests that need one.

WHY A HELPER. A tagged declaration of ``decoy/def:tagged-source`` carries a model,
two cutoffs and a weight table; three test files need the same one, and writing
it three times would make a drift between them a silent difference in what is
being tested rather than a failure. The enclosure of each Poisson weight and the
signal dyads are no part of it: the emission forms both
(``req:sector-weight-bound``, ``req:signal-dyads``).

THE NUMBERS ARE CHOSEN SO THAT EVERY FORMED PRODUCT IS EXACT, which is exactly
the remedy the lead-in of ``req:exact-decoy-blocks`` names for
``formed_entry_not_declarable``: "choosing the ``p_x`` and the
``ptilde(n|mu)`` with few enough significant bits makes every product exact, and
LOWERING a ``ptilde`` is permitted by ``eq:weightineq``". The weights below are
dyadic with few bits and lie safely below the lower end of the enclosure the
emission forms at each ``(n, mu)``.

NOTHING HERE IS AN ORACLE. The frozen, hand-derived expectations of this batch
are in ``tests/oracles/registry_transmitter_c1.py``; this module builds INPUTS.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction as F

from certiqs_key.foundations.exact import Matrix
from certiqs_key.transmitter.decoy import (
    DecoySourceDeclaration,
    RoundType,
    TaggedSourceDeclaration,
    WcpLetter,
    WcpModel,
    emit_decoy_declaration,
    exhibited_signal_dyad,
)

__all__ = [
    "BB84_POLARISATIONS",
    "declaration_input",
    "signal_dyads",
    "tagged_declaration",
    "wcp_model",
]

#: The four polarisations of ``cor:emitted-decoy`` (iv)(b)'s set ``D``, in the
#: order the construction of its proof is written in.
BB84_POLARISATIONS: tuple[str, ...] = ("H", "V", "+", "-")

#: Two intensities, so that the SHARING of one polarisation flag across
#: intensities is exercised rather than assumed: that sharing "IS the decoy
#: content of the declaration" (``rem:no-intensity-split``).
_INTENSITIES: Mapping[str, F] = {"signal": F(1, 2), "decoy": F(1, 8)}


def wcp_model() -> WcpModel:
    """Return the model of ``def:wcp-model``: four polarisations, two intensities."""
    letters = tuple(
        WcpLetter(
            label=f"{polarisation}-{intensity}",
            polarisation=polarisation,
            intensity=intensity,
            round_type=RoundType.GEN,
        )
        for intensity in _INTENSITIES
        for polarisation in BB84_POLARISATIONS
    )
    weight = F(1, len(letters))
    return WcpModel(
        polarisations=BB84_POLARISATIONS,
        intensities=dict(_INTENSITIES),
        alphabet=letters,
        weights={letter.label: weight for letter in letters},
        # THE LABELS OF THIS FIXTURE ARE THE PARTS, which is the simplest map
        # and not the only admissible one: a declaration may call its
        # polarisations anything and say which member of D each one IS.
        polarisation_parts=dict(
            zip(BB84_POLARISATIONS, BB84_POLARISATIONS, strict=True)
        ),
    )


def signal_dyads(entropy_cutoff: int) -> dict[tuple[int, str], Matrix]:
    """Return the dyads the corollary's proof exhibits, up to ``entropy_cutoff``.

    What the emission must form (``req:signal-dyads``); a test compares the
    emitted blocks with them.
    """
    return {
        (photon_number, polarisation): exhibited_signal_dyad(
            photon_number, polarisation
        )
        for photon_number in range(entropy_cutoff + 1)
        for polarisation in BB84_POLARISATIONS
    }


def declaration_input(
    *,
    entropy_cutoff: int = 1,
    source_cutoff: int = 2,
    **overrides: object,
) -> TaggedSourceDeclaration:
    """Return a tagged declaration of ``def:tagged-source``, with the exact weights.

    ``N_ent = 1`` is the instance default (the claims are generic and
    N_ent <= 2 is usable), and ``N_src = 2`` puts ONE photon
    number between the cutoffs, which is the polarisation-flag summand (T3)'s
    middle case -- the summand the published lemma does not carry and this
    submodule derives.
    """
    weights: dict[tuple[int, str], F] = {}
    for intensity in _INTENSITIES:
        for photon_number in range(source_cutoff + 1):
            # DYADIC AND DELIBERATELY BELOW THE POISSON WEIGHT. At mu = 1/2 the
            # exact weights are 0.6065, 0.3033, 0.0758; at mu = 1/8 they are
            # 0.8825, 0.1103, 0.0069. The declared numbers below are lower
            # dyadic rationals, which eq:weightineq permits and
            # cor:emitted-decoy (v) makes another tagged declaration.
            declared = {
                ("signal", 0): F(1, 2),
                ("signal", 1): F(1, 4),
                ("signal", 2): F(1, 16),
                ("decoy", 0): F(7, 8),
                ("decoy", 1): F(1, 16),
                ("decoy", 2): F(1, 256),
            }.get((intensity, photon_number), F(0))
            weights[(photon_number, intensity)] = declared
    fields: dict[str, object] = {
        "model": wcp_model(),
        "entropy_cutoff": entropy_cutoff,
        "source_cutoff": source_cutoff,
        "sector_weights": weights,
    }
    fields.update(overrides)
    return TaggedSourceDeclaration(**fields)  # type: ignore[arg-type]


def tagged_declaration(**overrides: object) -> DecoySourceDeclaration:
    """Return the emitted declaration, refusing to hide a refusal from a caller."""
    result = emit_decoy_declaration(declaration_input(**overrides))
    assert result.refusal is None, result.refusal
    return result.require()
