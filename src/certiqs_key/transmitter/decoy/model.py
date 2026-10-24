"""The phase-randomised weak-coherent-pulse source model, as a SOURCE MODEL.

spec/modules/transmitter/decoy/: Definition ``def:wcp-model`` (W1)-(W4) and
Assumption ``ass:wcp``.

IT FIXES THE STATES AS MATHEMATICAL OBJECTS AND NOT AS MATRICES, which is what
``def:source-spec`` (b) admits and what this file's types are shaped by: the
transmitted system is the Fock space over two modes, "separable and infinite
dimensional", so there is no matrix of ``rho_x`` to declare and none is declared.
What this record carries is the labels, the intensities, the weights and, per
polarisation label, which vector of ``D`` it stands for; ``eq:wcpstate`` is a
statement about those objects and is decided by nothing.

WHAT IS NOT HERE, AND THE ABSENCE IS THE POINT
==============================================
THE POLARISATION UNIT VECTORS. (W1) declares each polarisation as a LABEL
standing for a unit vector ``|a>`` in ``C^2``, a mathematical object of the
model whose coordinates are not declared: ``|+>`` has the amplitudes
``1/sqrt 2``, and no binary64 number squares to ``1/2``. NO CONDITION OF THIS
SUBMODULE READS AN AMPLITUDE. The entries of the signal dyads in the basis of a
quantum sector are FORMED by the emission, by the construction of
``cor:emitted-decoy`` (iv)(b) (``req:signal-dyads``), from
:attr:`WcpModel.polarisation_parts`, which says which of the four vectors of
``D`` each label stands for.

THE POISSON WEIGHTS. ``P_mu(n) = e^-mu mu^n / n!`` is transcendental and "is not
a declared datum". What is decided is the inequality of (T2) against the lower
end of the rational enclosure of ``lem:poisson-enclosure``, which the emission
forms from the declared intensity
(:mod:`certiqs_key.transmitter.decoy.enclosure`, ``req:sector-weight-bound``).

A RETAINED SYSTEM, A MEASUREMENT, A MARGINAL OR A CERTIFICATE. "It declares the
specified ensemble ``{p_x, rho_x}`` of a source specification and nothing else",
each of the others being supplied by the tagged declaration -- and there, by
being DEFINED from the declared blocks rather than declared.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction

from certiqs_key.foundations.blocks import Label
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import is_binary64
from certiqs_key.transmitter.decoy.bases import BB84_POLARISATION_ORDER
from certiqs_key.transmitter.decoy.reasons import RoundType

__all__ = ["WcpLetter", "WcpModel"]


@dataclass(frozen=True)
class WcpLetter:
    """One letter ``x = (a_x, mu_x, z_x)`` of ``def:wcp-model`` (W2).

    THE INTENSITY IS NAMED AND NOT VALUED HERE, and that is an implementation
    choice with a mechanical reason rather than a reading of the contract. (W2)
    declares ``Int`` as a finite set of non-negative reals; a sector identifier
    of the tagged declaration is a WIRE identifier -- an HDF5 link name drawn
    from ``domain.identifiers.IDENTIFIER_PATTERN`` -- and the tail flag
    ``f_{a,mu}`` is indexed by an intensity, so the intensity needs a name that
    a sector label can be built from. The VALUE travels in
    :attr:`WcpModel.intensities` under that name, and no condition of this
    submodule reads it as a label: the emission reads the value to form the
    enclosure of ``P_mu(n)`` that (T2) is decided against
    (``req:sector-weight-bound``).
    """

    label: Label
    polarisation: Label
    intensity: Label
    round_type: RoundType


@dataclass(frozen=True)
class WcpModel:
    """The declared data of ``def:wcp-model``: (W1) to (W4), and nothing formed.

    ``alphabet`` IS THE DECLARED ORDER and is the order every sum over ``X`` is
    accumulated in, here as in the core. "A LABEL OF WEIGHT ZERO IS NOT A
    LETTER: the alphabet carries the labels the source actually prepares", so
    every ``p_x`` is strictly positive -- which is what keeps every declared
    sector's rank at least one, and what ``prop:decoy-cert`` (ii), (iii) and
    ``cor:emitted-decoy`` (iv) need.
    """

    #: ``Pol``, finite, non-empty, ordered. Declared by LABEL; see the module
    #: docstring on why the unit vectors of (W1) are not here.
    polarisations: tuple[Label, ...]
    #: ``Int`` by name, each a declared non-negative binary64 number. AN
    #: INTENSITY OF ZERO IS ADMISSIBLE and is the vacuum-only letter.
    intensities: Mapping[Label, Fraction]
    #: ``X``, with its declared order.
    alphabet: tuple[WcpLetter, ...]
    #: ``p_x > 0`` with ``sum_x p_x = 1`` in the declared order, rounding
    #: nowhere -- decided by the core on the emitted specification, as every
    #: weight sum of this repository is.
    weights: Mapping[Label, Fraction]
    #: Per polarisation label, which of the four vectors of the set ``D`` of
    #: ``cor:emitted-decoy`` (iv)(b) it stands for. The emission forms the
    #: signal dyads from it (``req:signal-dyads``,
    #: :func:`certiqs_key.transmitter.decoy.bases.exhibited_signal_dyad`); the
    #: vector itself carries ``1/sqrt 2`` and is not a declared datum.
    #:
    #: A polarisation without a part is not refused as a polarisation -- the
    #: claims are generic in ``Pol`` -- but a declaration whose index set then
    #: carries a quantum sector above the vacuum is refused
    #: (``quantum_sector_outside_construction``), as is one with two labels
    #: for one vector of ``D`` or fewer than ``n + 1`` polarisations at ``n``
    #: photons; at the vacuum alone none of these is a condition. ``dim S_n``
    #: is no field: inside the construction it is ``n + 1``
    #: (``cor:emitted-decoy`` (iv)(b)).
    polarisation_parts: Mapping[Label, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Refuse a model no condition of ``def:wcp-model`` can be read against."""
        if not self.polarisations or len(set(self.polarisations)) != len(
            self.polarisations
        ):
            raise MalformedInputError(
                "Pol is finite, non-empty and its labels pairwise distinct "
                f"(def:wcp-model (W1)); the declared set is {list(self.polarisations)}"
            )
        if not self.intensities:
            raise MalformedInputError(
                "Int is finite and non-empty (def:wcp-model (W2))"
            )
        for name, value in self.intensities.items():
            if value < 0 or not is_binary64(value):
                raise MalformedInputError(
                    f"the intensity {name!r} is a declared NON-NEGATIVE binary64 "
                    f"number (def:wcp-model (W2)); it is {value}"
                )
        if not self.alphabet:
            raise MalformedInputError(
                "X is finite and non-empty (def:wcp-model (W2))"
            )
        seen: set[Label] = set()
        for letter in self.alphabet:
            if letter.label in seen:
                raise MalformedInputError(
                    f"the letter {letter.label!r} is declared twice; X is an "
                    "ordered set of pairwise distinct labels"
                )
            seen.add(letter.label)
            if letter.polarisation not in self.polarisations:
                raise MalformedInputError(
                    f"the letter {letter.label!r} carries the polarisation "
                    f"{letter.polarisation!r}, which Pol does not declare"
                )
            if letter.intensity not in self.intensities:
                raise MalformedInputError(
                    f"the letter {letter.label!r} carries the intensity "
                    f"{letter.intensity!r}, which Int does not declare"
                )
            weight = self.weights.get(letter.label)
            if weight is None or weight <= 0:
                raise MalformedInputError(
                    f"the letter {letter.label!r} carries the weight {weight}; "
                    "A LABEL OF WEIGHT ZERO IS NOT A LETTER of X, the alphabet "
                    "carrying the labels the source actually prepares "
                    "(def:wcp-model (W2))"
                )
        for label, part in self.polarisation_parts.items():
            if label not in self.polarisations:
                raise MalformedInputError(
                    f"the polarisation part map names {label!r}, which Pol does "
                    "not declare"
                )
            if part not in BB84_POLARISATION_ORDER:
                raise MalformedInputError(
                    f"the polarisation {label!r} is declared as the part "
                    f"{part!r}; cor:emitted-decoy (iv)(b) exhibits a declared "
                    f"basis for {list(BB84_POLARISATION_ORDER)} and asserts "
                    "nothing about any other polarisation"
                )

    @property
    def letter_of(self) -> Mapping[Label, WcpLetter]:
        """Return the letters by their labels, for a reader that has one."""
        return {letter.label: letter for letter in self.alphabet}

    @property
    def signal_alphabet(self) -> tuple[Label, ...]:
        """Return ``X`` as the core's ordered label list."""
        return tuple(letter.label for letter in self.alphabet)
