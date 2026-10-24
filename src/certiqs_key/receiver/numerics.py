"""THE NUMERIC SUBSTRATE OF THIS MODULE, decided here and nowhere else.

The representation of an exactly declared parameter is decided in this file,
at the one site it is observable at, and nothing else in
:mod:`certiqs_key.receiver` performs arithmetic on any other representation.
The residual norm is the contract's, and is transcribed below rather than
decided.

THE NUMERIC REPRESENTATION OF AN EXACTLY DECLARED PARAMETER
===========================================================
``interface.yaml`` ``parameters.representation_note`` records what is fixed and
what is not. Fixed: the declared parameter is EXACT (Assumption ``ass:exact``;
Theorem ``thm:exact-and-evaluated`` (i): every asserted identity and inequality
is between exactly specified quantities), and the EVALUATION of the contract's
statements is IEEE-754 double precision, binary64 (Definition ``def:evaluation-model``;
the ``numerics`` convention; Theorem ``thm:exact-and-evaluated`` (ii)). Not
fixed: how a declared parameter such as ``x = 1/3`` is represented between
declaration and evaluation.

**THE DECISION.** A declared parameter is accepted EXACTLY -- as an ``int``, a
:class:`~fractions.Fraction`, or a ``float`` -- and is converted to IEEE-754
double precision at exactly one function, :func:`to_float`, which is the
boundary at which a declared datum becomes a machine number. Every matrix this
package builds, compares or emits is :data:`Matrix`, a NumPy ``complex128``
array. Three reasons, in order of weight:

1. **The contract declares the evaluation, so the evaluation is not a choice.**
   Definition ``def:evaluation-model``: the contract evaluates its claims in binary64
   floating-point arithmetic, reports those of the six residuals of Definition
   ``def:residuals`` that exist on the input route taken and for the evaluation
   requested, and asserts no rigorous enclosure of any computed quantity. This
   module is that evaluation. Choosing an exact substrate instead would produce
   a module that could not compute ``lmax(A_Sigma)`` at all -- the eigenvalue
   extremes of Eq. ``eq:cd`` are not rational functions of the entries -- and
   would therefore have to introduce an algebraic-number layer the contract
   neither asks for nor scopes. The remark names the ONE exception in its own
   statement, and says why it is stated elsewhere: the one relation
   between a computed number and an exact one that the contract does assert is
   Assumption ``ass:eig``, stated there because it is invoked only on the opt-in
   route of Definition ``def:pmcex``. So the no-enclosure rule is unconditional
   at this file's boundary, and the single computed-to-exact assertion the
   contract makes is A-EIG's, declared with its own ``eps_eig`` and invoked on
   the exact-window route alone.
2. **Exactness is a property of the DATUM and floating point of the
   EVALUATION, and the two must stay separable.** Accepting a
   :class:`~fractions.Fraction` and converting once means the declared
   ``x = 9/25`` is carried exactly through validation -- where
   ``parameters.domains``' "A parameter outside its domain is refused; it is
   never clipped to the boundary" is decided, and where a domain endpoint such
   as ``delta = 2 pi`` must be distinguished from ``delta`` just below it --
   and becomes a machine number once, at a site that can be named in a report.
3. **There is exactly one conversion site, so there is exactly one place to
   look.** The choice is observable at exactly one place, the boundary at
   which a declared parameter becomes a float. This is that place; no other
   function in the package calls ``float()`` on a declared parameter.

THE ENCLOSURES ARE COMPUTED BESIDE THIS SUBSTRATE, NOT IN IT
============================================================
Definition ``def:evaluation-model`` adds that, for a declaration whose model is
an admissible receiver exactly, the module MOREOVER computes complex enclosures
of the photon-number blocks in exact rational arithmetic (Theorem
``thm:enclosed-blocks``; ``thm:exact-and-evaluated`` (vi)). Those live in
:mod:`certiqs_key.receiver.enclosure`, :mod:`certiqs_key.receiver.radicals`,
:mod:`certiqs_key.receiver.generic` and :mod:`certiqs_key.receiver.reference`,
take the DECLARED values (``int``, :class:`~fractions.Fraction`, a ``float``
read as the dyadic rational it is, or a :class:`PiMultiple`) and never a value
:func:`to_float` produced. So nothing above changes: every matrix this file
types is binary64, no binary64 number is enclosed, and the enclosures are not
evaluations (``thm:exact-and-evaluated`` (ii)).

THE RESIDUAL NORM IS THE CONTRACT'S, NOT THIS MODULE'S
======================================================
Definition ``def:residuals`` fixes ``||.||`` as THE SPECTRAL NORM throughout
Eq. ``eq:res1`` to Eq. ``eq:rhodef``. :func:`residual_norm` is that norm and
:data:`RESIDUAL_NORM` names it in the artifact; the value is a transcription
and not a decision.

EVERY THRESHOLD THIS MODULE APPLIES IS ONE OF THE DECLARED TOLERANCES
=====================================================================
Definition ``def:tolmap`` fixes, for each exact admissibility condition the
contract evaluates under Definition ``def:evaluation-model``, WHICH DECLARED TOLERANCE
DECIDES IT "and by no other threshold", and the
``numerical_tolerance_assignment`` convention (``interface.yaml``
``conventions``) carries the same list. The five items are

    (i)    route-(i) Gram admissibility            eps_2
    (ii)   the route-(i) rank consistency check    eps_2, by Eq. eq:eps2rank
    (iii)  dark-channel (D1) / (D2)                eps_4 / eps_2
    (iv)   bound-data admissibility, c >= -eps_2   eps_2, UNCLAMPED
    (v)    route-(ii) contractivity, C10's (E1)    eps_1

and the closing enumeration classes every other validation as a
declared-domain comparison, a combinatorial predicate, or a residual test
against its own declared ``eps``.

**THE RANK CUTOFF IS DECLARED.** It is never a library's relative
``lmax * max(D_1, D_2) * eps_mach``: :func:`epsilon_rank` is Eq.
``eq:eps2rank``,

    rk_{eps_2}(X) = #{ i : lambda_i((X + X^dagger)/2) > eps_2 } ,

**the comparison STRICT and the threshold ABSOLUTE**, and Requirement
``req:tolerance-tests`` adds that every rank statement this module decides on
floating-point data is decided by Eq. ``eq:eps2rank``, and no other rule is
licensed, there or at Theorem ``thm:representation-independence`` (iv) --
which is why :func:`certiqs_key.receiver.grams.one_mode_per_port` takes the
declared tolerance too. Remark ``rem:ranktwosided`` is why the rule had to be
fixed rather than inherited: the count can differ from the exact rank in BOTH
directions, so the choice of ``tau`` is a choice about which declarations are
accepted, not a numerical detail, and the usual library default is RELATIVE,
UNDECLARED, AND INVISIBLE IN THE ARTIFACT. Under Eq. ``eq:eps2rank`` both
directions remain -- "no threshold can remove them" -- but "the rank the check
used is a function of ``{A_k}`` and ``eps_2`` alone".

THE DECLARED TOLERANCES HAVE A DECLARED DOMAIN
==============================================
Each of the receiver tolerances ``eps_1, ..., eps_6``, ``eps_gap`` and
``eps_eig`` is declared in ``[0, 1)``, validated at input, and a value outside
it is refused with the contract-verbatim ``tolerance_outside_declared_domain``
(``interface.yaml`` ``refusals``; Requirement ``req:tolerance-domain``; Remark
``rem:tolerancedomain``). The interval is HALF-OPEN and this module writes it
so: ``0`` is admissible -- a declarer who wants an exactly decided condition
declares it -- and ``1`` is not, because at ``eps >= 1`` the test a tolerance
governs is "vacuous or degenerate, and namably so". The domain is checked
BEFORE any tolerance is used to decide anything, since the tolerances decide
the other validations.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

import numpy as np
import numpy.typing as npt

from certiqs_key.receiver.errors import MalformedInputError
from certiqs_key.receiver.reasons import Refusal, RefusalReason

__all__ = [
    "RESIDUAL_NORM",
    "TOLERANCE_DOMAIN",
    "TOLERANCE_KEYS",
    "TOLERANCE_KEYS_ALL",
    "TOLERANCE_KEYS_CONDITIONAL",
    "Angle",
    "Matrix",
    "NumericalTolerances",
    "PiMultiple",
    "RealVector",
    "Scalar",
    "as_matrix",
    "eigenvalues",
    "epsilon_rank",
    "hermitian_part",
    "hermiticity_positivity_defect",
    "identity",
    "is_hermitian",
    "lambda_max",
    "lambda_min",
    "positive_part",
    "residual_norm",
    "to_float",
    "tolerance_field_is_admissible",
    "tolerance_is_in_declared_domain",
    "tolerances_from_declaration",
]

#: Every operator of this contract is Hermitian or a complex field-transfer
#: matrix, so the substrate is complex throughout: Eq. eq:retarder carries
#: `exp(-i delta / 2)`, Eq. eq:bs carries `exp(i varphi)`, and the interface
#: conventions (`waveplate_convention`, `beamsplitter_convention`) forbid
#: dropping either.
Matrix = npt.NDArray[np.complex128]

#: Spectra and other real vectors.
RealVector = npt.NDArray[np.float64]

#: What a DECLARED parameter may be: exact by Assumption ass:exact, and
#: accepted in whichever exact form the declaration writes it.
Scalar = int | float | Fraction


@dataclass(frozen=True)
class PiMultiple:
    """An angle or phase declared as ``c * pi``, ``c`` a rational read exactly.

    ``interface.yaml`` ``parameters.units.angle_presentation`` and its
    ``presentation_rule`` (b): the coefficient ``c`` is the declared datum and
    what the artifact carries, and the parameter is ``c * pi`` EXACTLY. This is
    how an angle reaches the exact route of Requirement
    ``req:exact-route-decision`` (ii): an angle given in radians is a declared
    value, the dyadic rational it denotes, and a non-zero one is no rational
    multiple of ``pi``.

    The coefficient is read as the rational number it denotes: an ``int`` or
    a :class:`~fractions.Fraction` as itself, a finite binary64 ``float`` as
    the dyadic rational it is (``foundations/def:binary64`` (iii)), and it is
    held as a :class:`~fractions.Fraction` from then on. A non-finite float
    denotes no rational and is refused.

    The binary64 evaluation uses ``float(c) * math.pi`` (:func:`to_float`), the
    binary64 product of ``c`` and ``pi`` each rounded to binary64, an
    evaluation of the datum under Definition ``def:evaluation-model``. It is
    written that way, and not as the correctly rounded ``c * pi``, so that a
    declaration that passes ``float(c) * math.pi`` in radians evaluates
    to the same machine number in this presentation.
    """

    coefficient: Fraction

    def __post_init__(self) -> None:
        """Read the coefficient as the exact rational it denotes, or refuse it."""
        value: object = self.coefficient
        if isinstance(value, bool) or not isinstance(value, Fraction | int | float):
            raise MalformedInputError(
                "the coefficient of an angle given in units of pi is a rational "
                f"(int, Fraction or finite float), not {type(value).__name__}"
            )
        if isinstance(value, float) and not math.isfinite(value):
            raise MalformedInputError(
                f"the coefficient {value} of an angle given in units of pi is "
                "not finite and denotes no rational number"
            )
        if not isinstance(value, Fraction):
            object.__setattr__(self, "coefficient", Fraction(value))

    def __str__(self) -> str:
        """Return ``c pi`` with the coefficient as an exact rational."""
        return f"{self.coefficient} pi"


#: What a declared ANGLE or PHASE may be: a declared value in radians, or a
#: rational coefficient of pi (`interface.yaml` `parameters.units`).
Angle = Scalar | PiMultiple

#: The norm of Eqs. eq:res1, eq:res3, eq:res4 and eq:rhodef. NAMED BY THE
#: CONTRACT -- Def. def:residuals fixes ||.|| as the spectral norm throughout
#: eq:res1 to eq:rhodef -- and still emitted beside the tolerance so that a
#: pass/fail verdict is reproducible from the artifact.
RESIDUAL_NORM: Final[str] = "spectral"

#: The six tolerances of the inputs table's `numerical_tolerances` row that are
#: declared on EVERY declaration (its `always_required`), in the row's own
#: order. They are declared, never defaulted (`never_defaulted: true`): no
#: member of this tuple has a default anywhere in this package.
TOLERANCE_KEYS: Final[tuple[str, ...]] = (
    "eps_1",
    "eps_2",
    "eps_3",
    "eps_4",
    "eps_5",
    "eps_gap",
)

#: The two tolerances of the inputs table that are CONDITIONALLY required.
#: interface.yaml `inputs.numerical_tolerances`: "eps_6 and eps_eig are
#: conditionally required, on the same rule and for the same reason as m_t:
#: required exactly where an `exact_window` depth is declared, refused when
#: missing there, and neither required nor an error when no depth is declared
#: anywhere".
#:
#: THIS IS WHERE THEY DIFFER FROM eps_1 AND eps_3, which are declared on every
#: route and merely unused on one, while eps_6 is not required where no depth
#: is, being conditionally required on the same condition as r_6
#: (Req. req:residual-emission; `outputs.validation_results`,
#: `r6_is_request_dependent_note`).
TOLERANCE_KEYS_CONDITIONAL: Final[tuple[str, ...]] = ("eps_6", "eps_eig")

#: The declared tolerance tuple of the inputs table (`numerical_tolerances`,
#: its `members`): EIGHT members, {eps_1, ..., eps_6} together with eps_gap and
#: eps_eig, of which six are required on every declaration and two, eps_6 and
#: eps_eig, only on the opt-in route; each member has the declared domain
#: [0, 1).
TOLERANCE_KEYS_ALL: Final[tuple[str, ...]] = (
    "eps_1",
    "eps_2",
    "eps_3",
    "eps_4",
    "eps_5",
    "eps_6",
    "eps_gap",
    "eps_eig",
)

#: The declared domain of every member, as the HALF-OPEN interval Remark
#: rem:tolerancedomain writes it: [0, 1). 0 is admissible and 1 is not.
TOLERANCE_DOMAIN: Final[tuple[float, float]] = (0.0, 1.0)


def to_float(value: Scalar | PiMultiple) -> float:
    """Return a declared parameter as an IEEE-754 double.

    An angle given as a coefficient of pi (:class:`PiMultiple`) is evaluated
    as ``float(c) * math.pi``; see that class for why.

    THE ONE CONVERSION SITE of this package (the module docstring). ``bool`` is
    rejected although it is an ``int`` subclass: the only boolean the interface
    carries is the mirror handedness flag of the ``mirror_handedness``
    convention, which selects a matrix and is never a numerical parameter, so a
    ``bool`` reaching here is a mis-presentation rather than a value.
    """
    if isinstance(value, bool):
        raise MalformedInputError(
            "a boolean is not a declared numerical parameter; the only boolean "
            "the interface carries is the mirror handedness flag"
        )
    if isinstance(value, PiMultiple):
        return float(value.coefficient) * math.pi
    if isinstance(value, int | Fraction):
        return float(value)
    if isinstance(value, float):
        return value
    raise MalformedInputError(  # pragma: no cover - unreachable under mypy
        f"a declared parameter must be an int, a Fraction or a float, not "
        f"{type(value).__name__}"
    )


def as_matrix(rows: Sequence[Sequence[Scalar | complex]]) -> Matrix:
    """Return a rectangular table of declared entries as a complex matrix.

    Raises :class:`MalformedInputError` for a ragged table: rows of differing
    length enumerate no operator, so no validity condition of the inputs table
    can be read against them.
    """
    widths = {len(row) for row in rows}
    if len(widths) > 1:
        raise MalformedInputError(f"ragged matrix: row lengths {sorted(widths)}")
    if not rows:
        raise MalformedInputError("an empty matrix presents no operator")
    entries = [[complex(entry) for entry in row] for row in rows]
    return np.asarray(entries, dtype=np.complex128)


def identity(dimension: int) -> Matrix:
    """Return the identity matrix of the given dimension."""
    return np.eye(dimension, dtype=np.complex128)


def hermitian_part(matrix: Matrix) -> Matrix:
    """Return ``(X + X^dagger) / 2``.

    Applied where the operator is Hermitian by construction -- a Gram
    (Eq. ``eq:gramdef``), a deficiency (Eq. ``eq:deficiency``), a POVM block --
    so that a symmetric-eigenvalue routine reads a symmetric matrix. It removes
    representation noise, never a genuine anti-Hermitian part, and every caller
    that could receive a non-Hermitian argument tests :func:`is_hermitian`
    first.
    """
    return np.asarray(0.5 * (matrix + matrix.conj().T), dtype=np.complex128)


def is_hermitian(matrix: Matrix, tolerance: float) -> bool:
    """Return whether ``matrix`` is Hermitian within a DECLARED tolerance.

    ``tolerance`` has no default: this module never invents one, and every
    caller passes a member of the declared :class:`NumericalTolerances`.
    """
    if matrix.shape[0] != matrix.shape[1]:
        return False
    defect = matrix - matrix.conj().T
    return bool(residual_norm(defect) <= tolerance)


def eigenvalues(hermitian: Matrix) -> RealVector:
    """Return the eigenvalues of a Hermitian operator, ascending."""
    if hermitian.size == 0:
        return np.zeros(0, dtype=np.float64)
    values = np.linalg.eigvalsh(hermitian_part(hermitian))
    return np.asarray(values, dtype=np.float64)


def lambda_min(hermitian: Matrix) -> float:
    """Return the smallest eigenvalue of a Hermitian operator."""
    spectrum = eigenvalues(hermitian)
    if spectrum.size == 0:
        raise MalformedInputError("an empty operator has no smallest eigenvalue")
    return float(spectrum[0])


def lambda_max(hermitian: Matrix) -> float:
    """Return the largest eigenvalue of a Hermitian operator."""
    spectrum = eigenvalues(hermitian)
    if spectrum.size == 0:
        raise MalformedInputError("an empty operator has no largest eigenvalue")
    return float(spectrum[-1])


def positive_part(hermitian: Matrix) -> Matrix:
    """Return ``(X)_+``, the positive part of a Hermitian operator.

    Eq. ``eq:res1``'s ``(Gamma^dagger Gamma - 1)_+``: the spectral positive
    part, obtained by replacing every negative eigenvalue with zero. It is the
    part that must vanish, and a contraction is exactly an operator whose
    positive part vanishes.
    """
    if hermitian.size == 0:
        return np.zeros((0, 0), dtype=np.complex128)
    spectrum, vectors = np.linalg.eigh(hermitian_part(hermitian))
    clipped = np.maximum(spectrum, 0.0)
    return np.asarray(
        vectors @ np.diag(clipped.astype(np.complex128)) @ vectors.conj().T,
        dtype=np.complex128,
    )


def residual_norm(matrix: Matrix) -> float:
    """Return the SPECTRAL norm of a matrix -- the norm of Def. def:residuals.

    NAMED BY THE CONTRACT, not chosen here: Definition ``def:residuals`` fixes
    ``||.||`` as the spectral norm throughout Eq. ``eq:res1`` to
    Eq. ``eq:rhodef``. The value is the largest singular value, which for a
    Hermitian argument is the largest eigenvalue modulus.
    """
    if matrix.size == 0:
        return 0.0
    return float(np.linalg.norm(matrix, ord=2))


def hermiticity_positivity_defect(matrix: Matrix) -> float:
    """Return ``rho(X)`` of Eq. ``eq:rhodef`` -- the defect ``r_5`` measures.

        rho(X) = max{ ||X - X^dagger||, (-lmin((X + X^dagger)/2))_+ }

    in the SPECTRAL norm (Definition ``def:residuals``). Proposition
    ``prop:res5`` (i): ``rho(X) = 0`` if and only if ``X = X^dagger`` AND
    ``X >= 0`` -- BOTH conditions, which is exactly what a consumer validating
    an operator row checks. (ii): on a Hermitian argument it reduces to
    ``(-lmin(X))_+``, "which is the form Eq. ``eq:res2`` takes on a Gram".

    NOTHING HERE REPAIRS ANYTHING. The Hermitian part is computed to MEASURE
    the defect and is never substituted for the argument: "no block is
    Hermitized, symmetrized, projected onto the positive cone, clamped or
    repaired in any way; the artifact carries the computed block itself"
    (Requirement ``req:residual-refusal``).
    """
    if matrix.size == 0:
        return 0.0
    skew = np.asarray(matrix - matrix.conj().T, dtype=np.complex128)
    hermiticity = residual_norm(skew)
    negativity = max(0.0, -lambda_min(matrix))
    return max(hermiticity, negativity)


def epsilon_rank(matrix: Matrix, epsilon: float) -> int:
    """Return ``rk_{eps_2}(X)`` of Eq. ``eq:eps2rank``.

        rk_{eps_2}(X) = #{ i : lambda_i((X + X^dagger)/2) > eps_2 }

    counting eigenvalues WITH MULTIPLICITY, THE COMPARISON STRICT and THE
    THRESHOLD ABSOLUTE. Definition ``def:tolmap`` (ii) fixes all three, and each
    is load-bearing:

    * *strict.* An eigenvalue at exactly ``eps_2`` is NOT counted. Remark
      ``rem:ranktwosided``'s argument for the threshold turns on it -- a Gram
      admitted by item (i) "has its numerically-zero eigenvalues in
      ``[-eps_2, eps_2]`` and the two thresholds cannot disagree about which
      they are", which is true for ``>`` and false for ``>=``;
    * *absolute.* By the same remark a port Gram is already normalized by
      construction, so there is no scale to normalize against, and a threshold
      taken relative to ``lmax(A_k)`` would make the decision at a nearly dark
      port A MILLION TIMES TIGHTER than at a lossless one;
    * *declared.* The threshold is the declarer's ``eps_2`` and nothing else:
      Requirement ``req:tolerance-tests`` licenses no other rule, there or at
      Theorem ``thm:representation-independence`` (iv).

    Remark ``rem:ranktwosided`` records that the count can differ from the exact
    rank in BOTH directions and that no threshold removes that; what the rule
    buys is that "the rank the check used is a function of ``{A_k}`` and
    ``eps_2`` alone".
    """
    if matrix.size == 0:
        return 0
    return int(sum(1 for value in eigenvalues(matrix) if value > epsilon))


@dataclass(frozen=True)
class NumericalTolerances:
    """The declared ``numerical_tolerances`` input (``interface.yaml`` ``inputs``).

    NO FIELD HAS A DEFAULT, and that is the whole point of the type. The input
    row: "Without them the ``fail_closed`` convention has no threshold to test,
    so they are declared, never defaulted."

    ``eps_1``..``eps_5`` bound the five residuals of Definition
    ``def:residuals`` on the routes where each exists, and ``eps_gap`` bounds
    the residual gap Eq. ``eq:resgap`` where a window is declared. ``eps_1``,
    ``eps_2`` and ``eps_4`` ADDITIONALLY decide the exact admissibility
    conditions of Definition ``def:tolmap``, "the only place any of the three
    is consumed other than as a residual bound".

    ALL SIX ARE DECLARED ON EVERY ROUTE. ``eps_1`` and ``eps_3`` are UNUSED on
    route (i), where ``r_1`` and ``r_3`` do not exist and no contractivity check
    is made, "and an unused tolerance is unused, not an error" -- so they are
    still required there and are simply not consumed.

    THERE IS NO MARGIN TOLERANCE. Branch 1 of Definition ``def:pmc`` is
    selected by predicate (X) alone, and Remark ``rem:pmc-branch-choice``
    closes: "There is no such predicate here, and there is no declared margin
    among the inputs."

    ``eps_6`` AND ``eps_eig`` ARE ``None`` WHEN THEY WERE NOT DECLARED, AND
    ``None`` MEANS ABSENT AND NOT ZERO. They are conditionally required --
    exactly where an ``exact_window`` depth is declared -- and where no depth is
    declared anywhere they are neither required nor an error
    (``inputs.numerical_tolerances``). A ``0.0`` in either field would be a
    declared exact tolerance, which is a legal and quite different declaration:
    ``eps_eig = 0`` is inside the declared domain, and Assumption ``ass:eig``
    then asserts that the eigenvalue routine never overshoots at all
    (``numerical_tolerances.eps_eig_zero_note``); the domain is a floor, not
    sizing advice (Remark ``rem:tolerancedomain``). The two states must stay
    distinguishable, so neither field has a default and every construction
    site says which it means.

    ``eps_eig`` DECIDES NOTHING, AND THE CONTRACT SAYS SO. Definition
    ``def:tolmap``'s preamble: it decides NOTHING AT ALL; it is subtracted from
    a computed eigenvalue in Eq. ``eq:elldef``, so it is the one declared number
    the contract spends on a HYPOTHESIS (Assumption ``ass:eig``) rather than on
    a test. It is therefore absent from :meth:`residual_bound` and from every
    threshold in this package.
    """

    eps_1: float
    eps_2: float
    eps_3: float
    eps_4: float
    eps_5: float
    eps_gap: float
    #: CONDITIONALLY DECLARED: the bound on r_6 (Eq. eq:res6), present exactly
    #: where an `exact_window` depth is declared.
    eps_6: float | None
    #: CONDITIONALLY DECLARED: the slack SUBTRACTED from a
    #: computed eigenvalue in Eq. eq:elldef. It decides nothing.
    eps_eig: float | None

    def residual_bound(self, residual_id: str) -> float:
        """Return the declared bound on one of ``r_1``..``r_6``.

        ``r_6``'s bound is ``eps_6``, which exists exactly where an exact-window
        depth was declared. Asking for it on a declaration that carries none is
        a programming error and not a refusal: Requirement
        ``req:residual-emission`` makes the KEY of ``r_6`` absent there, so no caller
        has a residual to compare.
        """
        bounds: dict[str, float | None] = {
            "r_1": self.eps_1,
            "r_2": self.eps_2,
            "r_3": self.eps_3,
            "r_4": self.eps_4,
            "r_5": self.eps_5,
            "r_6": self.eps_6,
        }
        if residual_id not in bounds:
            raise MalformedInputError(f"no residual {residual_id!r} is declared")
        bound = bounds[residual_id]
        if bound is None:
            raise MalformedInputError(
                f"{residual_id} has no declared tolerance on this declaration: "
                f"eps_6 is declared exactly where an `exact_window` depth is, "
                f"and where none is declared the key of r_6 is ABSENT"
            )
        return bound


def tolerance_is_in_declared_domain(value: float) -> bool:
    """Return whether a declared tolerance lies in ``[0, 1)``.

    Remark ``rem:tolerancedomain``, transcribed with its half-open end: ``0``
    is admissible and ``1`` is not (``interface.yaml``
    ``inputs.numerical_tolerances.domain_note``). BOTH SIDES ARE TESTED -- a
    negative tolerance would make Definition ``def:tolmap`` (iii)'s entrywise
    test STRICTER than the exact condition, which is not a tolerance at all --
    and the upper end is EXCLUSIVE, because at ``eps >= 1`` the test a
    tolerance governs is "vacuous or degenerate, and namably so".
    """
    low, high = TOLERANCE_DOMAIN
    return low <= value < high


def tolerances_from_declaration(
    declared: Mapping[str, Scalar],
    exact_window_declared: bool,
) -> NumericalTolerances | Refusal:
    """Return the declared tolerances, or the first refusal, and never raise.

    THREE CHECKS, IN THIS ORDER, AND THE ORDER IS NOT ARBITRARY. First that
    every ALWAYS-required tolerance is PRESENT -- the inputs table, declared,
    never defaulted; a missing declared tolerance is one of the refusals
    ``interface.yaml`` ``refusals.named_without_a_spelling`` lists, so the key
    is this module's. Then that the two CONDITIONALLY required ones are present
    exactly where they are required, which is a different condition with a
    different, contract-verbatim reason. Then that every tolerance that IS
    present lies in its DECLARED DOMAIN ``[0, 1)``, refused with the
    contract-verbatim ``tolerance_outside_declared_domain`` (the refusal rules,
    row 5). The domain is "validated at input", and it must be
    validated before anything else, because these numbers decide the other
    validations (Definition ``def:tolmap``): a tolerance outside its own domain
    has to refuse BEFORE it decides anything.

    ``exact_window_declared`` IS A COMBINATORIAL PREDICATE ON THE DECLARATION
    AND NOT A COMPUTATION. Definition ``def:tolmap``'s closing enumeration puts
    the conditional presence of ``eps_eig`` and ``eps_6`` at a declaration
    carrying an exact-window depth under kind (b), "a combinatorial predicate
    on the declaration decided by finite inspection". It has NO
    DEFAULT here, because the permissive value is the one that skips a required
    check: a caller that forgot to pass it would silently stop requiring the
    two tolerances a depth needs.

    THE REQUIREMENT IS SCOPED TO THE DECLARATION, NOT TO THE SETTING.
    Requirement ``req:exact-window-declaration``: declaring an exact-window
    depth AT ANY SETTING requires ``eps_eig`` and ``eps_6``. So one depth
    anywhere requires both everywhere, which is the same rule the mixed-setting
    case ``MIX-DEPTH-AT-OFF-ONLY`` exercises.

    SUPPLIED WHERE NOT REQUIRED IS UNUSED, NOT AN ERROR. The inputs table says
    the two are "neither required nor an error when no depth is declared
    anywhere", and states no refusal for a supplied one -- exactly as ``eps_1``
    and ``eps_3`` are declared on every route and merely UNUSED on one, and as
    Requirement ``req:window-declaration`` says of a ``tail_window`` supplied
    where (X) holds. So a supplied-and-unneeded value is carried, domain-checked like
    every other, and consumed by nothing.

    THE DOMAIN IS A FLOOR AND NOT SIZING ADVICE. A declared
    ``eps_gap = 999/1000`` lies inside ``[0, 1)`` and is ADMITTED although it
    makes its test very nearly no constraint: Remark ``rem:tolerancedomain``
    says nothing here makes a tolerance near 1 sensible, and this module adds
    no rule the contract does not state. The same holds at the other end for
    ``eps_eig = 0``, which is admissible and with which Assumption ``ass:eig``
    asserts that the eigenvalue routine never overshoots at all -- a
    declaration this module does not second-guess and cannot verify.
    """
    for key in TOLERANCE_KEYS:
        if key not in declared:
            return Refusal(
                RefusalReason.NUMERICAL_TOLERANCE_MISSING,
                f"the declaration supplies no {key}; the inputs table's "
                f"`numerical_tolerances` declares it, never defaults it",
            )
    if exact_window_declared:
        for key in TOLERANCE_KEYS_CONDITIONAL:
            if key not in declared:
                return Refusal(
                    RefusalReason.EXACT_WINDOW_DECLARED_WITHOUT_REQUIRED_TOLERANCE,
                    f"the declaration carries an `exact_window` depth and "
                    f"supplies no {key}; Requirement req:exact-window-declaration "
                    f"requires eps_eig and eps_6 wherever a depth is declared, "
                    f"and a missing one is refused rather than defaulted",
                )
    present = tuple(TOLERANCE_KEYS) + tuple(
        key for key in TOLERANCE_KEYS_CONDITIONAL if key in declared
    )
    values = {key: to_float(declared[key]) for key in present}
    low, high = TOLERANCE_DOMAIN
    for key, value in values.items():
        if not tolerance_is_in_declared_domain(value):
            return Refusal(
                RefusalReason.TOLERANCE_OUTSIDE_DECLARED_DOMAIN,
                f"{key} = {value} lies outside the declared domain "
                f"[{low}, {high}); the inputs table and Remark rem:tolerancedomain "
                f"declare each of eps_1..eps_6, eps_gap and eps_eig in that "
                f"half-open interval, and at eps >= 1 the test it governs is "
                f"vacuous or degenerate",
            )
    return NumericalTolerances(
        eps_1=values["eps_1"],
        eps_2=values["eps_2"],
        eps_3=values["eps_3"],
        eps_4=values["eps_4"],
        eps_5=values["eps_5"],
        eps_gap=values["eps_gap"],
        eps_6=values.get("eps_6"),
        eps_eig=values.get("eps_eig"),
    )


def tolerance_field_is_admissible(value: Scalar | None) -> bool:
    """Return whether a reserved ``tolerance`` field is admissible.

    ``interface.yaml`` ``parameters.exactness``: the field is validated as
    ABSENT OR EXACTLY ZERO and refused otherwise. Exactly zero, not nearly zero
    -- an ignored tolerance "is a silent claim that the device is exact"
    (Assumption ``ass:exact``; Requirement ``req:reserved-tolerance-field``).
    """
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, Fraction | int):
        return value == 0
    return value == 0.0
