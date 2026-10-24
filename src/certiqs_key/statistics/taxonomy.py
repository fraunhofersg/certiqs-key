"""thm:geometry-validation -- the geometry taxonomy, and thm:box-oracle (i), the emitted support.

Definition ``def:taxonomy`` admits EXACTLY TWO TAGS and no
third; "a consumer presented with any other tag refuses rather than guessing".

* ``singleton`` -- data ``q^*`` in ``Q^Chat``, denoting ``{q^*}``. Validation
  predicate: ``q^*(chat) >= 0`` for every ``chat`` and ``sum_chat q^*(chat) =
  1``, which Theorem ``thm:geometry-validation`` (ii) proves NECESSARY AND SUFFICIENT
  for the denotation to be a non-empty subset of the simplex.
* ``polytope`` -- data ``(m_row, B, b)``, denoting
  ``{q in Delta(Chat) : B q <= b}`` (Eq. ``eq:polytope``). Validation predicate:
  rational feasibility of ``{q >= 0, sum q = 1, B q <= b}``.

The CANONICAL BOX FORM is a sub-form of ``polytope`` and NOT a third tag
(Remark ``rem:two-tags``): it adds a recorded pair ``(q^-, q^+)`` with
``0 <= q^- <= q^+`` whose one-hot rows ``B`` already spells out (Eq.
``eq:boxrows``), and a consumer that ignores ``box_bounds`` still reads a
well-formed ``polytope``. That is why :class:`PolytopeGeometry` carries the box
as an optional field of the one tag rather than as a class of its own.

THE ORDER OF THE TWO CHECKS IS LOAD-BEARING
===========================================
The closed-form predicate of Theorem ``thm:geometry-validation`` (iii),
``sum q^- <= 1 <= sum q^+`` (Eq. ``eq:boxfeas``), is proved UNDER the hypothesis
``0 <= q^- <= q^+`` componentwise. Data violating that hypothesis is not a
canonical box at all, and running the sum test on it first returns a PASS on an
empty set -- the frozen ``ILLFORMED-box-inverted`` case. So well-formedness is
decided first and emptiness second, and the two verdicts are kept apart
(:class:`GeometryDefect`).
"""  # noqa: E501

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from certiqs_key.statistics.errors import UndecidedGeometryError

__all__ = [
    "GeometryDefect",
    "GeometryTag",
    "GeometryVerdict",
    "PolytopeGeometry",
    "SingletonGeometry",
    "acceptance_support",
    "box_witness_point",
    "canonical_box",
    "validate_geometry",
]

_ZERO = Fraction(0)
_ONE = Fraction(1)


class GeometryTag(StrEnum):
    """The two admissible tags of Definition ``def:taxonomy``. There is no third."""

    SINGLETON = "singleton"
    POLYTOPE = "polytope"


class GeometryDefect(StrEnum):
    """Why a declared geometry is not usable, if it is not.

    A vocabulary of DEFECTS IN A DECLARED GEOMETRY, and deliberately NOT the
    ``infeasibility_report`` vocabulary of Theorem ``thm:honest-containment`` (iii):
    those ten codes name violations of THIS MODULE'S INPUT DOMAIN, and Theorem
    ``thm:honest-containment`` (iii) proves that the construction map's own output
    satisfies the validation predicate unconditionally, so no geometry the construction
    emits can carry a defect from this enum. What can carry one is a geometry a
    profile DECLARES, which is what :func:`validate_geometry` is for. Nor is it
    ``certiqs_key.meat_core.acceptance.geometry.AcceptanceDefect``, which is the
    consuming module's own vocabulary for the same question asked at its own
    boundary; keeping the three apart is what stops them drifting into one
    implicit vocabulary.
    """

    #: The data is not well formed for the form it claims -- checked FIRST.
    ILL_FORMED = "ill-formed"
    #: Well-formed data whose denotation is empty.
    EMPTY = "empty"


@dataclass(frozen=True)
class GeometryVerdict:
    """What a declared geometry is, and what is wrong with it if anything."""

    defect: GeometryDefect | None
    detail: str = ""

    @property
    def admissible(self) -> bool:
        """Return whether the validation predicate of Definition def:taxonomy holds."""
        return self.defect is None


@dataclass(frozen=True)
class SingletonGeometry:
    """The ``singleton`` geometry: data ``q^*``, denotation ``{q^*}``."""

    outcomes: tuple[str, ...]
    #: ``q^*``, in the DECLARATION's own enumeration of Chat (the conventions
    #: of ``interface.yaml``, "Coordinate order").
    frequencies: tuple[Fraction, ...]

    @property
    def tag(self) -> GeometryTag:
        """Return the tag this geometry carries."""
        return GeometryTag.SINGLETON

    def as_machine_record(self) -> dict[str, object]:
        """Return the record under the machine key ``acceptance_set``.

        SERIALIZED SUB-KEYS ARE AN IMPLEMENTATION CHOICE, DECIDED HERE AND
        RECORDED. the outputs table fixes ``geometry_tag``, and
        Definition ``def:taxonomy`` fixes ``box_bounds``; it names the
        remaining data only by SYMBOL -- ``q^*`` here -- and fixes no
        serialized key for it and no on-disk encoding for a rational
        (``interface.yaml``, ``outputs.acceptance_set.representation_note``).
        The key chosen is ``frequencies``, which is the field the CONSUMER
        already reads ``q^*`` from
        (``certiqs_key.meat_core.declaration.declaration.AcceptanceSet.frequencies``).
        Naming it anything else would create a second vocabulary for one
        object, which is the only way this decision could acquire
        proof-relevant content.
        """
        return {
            "geometry_tag": str(self.tag),
            "frequencies": self.frequencies,
        }


@dataclass(frozen=True)
class PolytopeGeometry:
    """The ``polytope`` geometry: data ``(m_row, B, b)``, and its box sub-form.

    ``rows`` is ``B`` and ``rhs`` is ``b``, read positionally against each
    other in the declaration's own row order -- which for the canonical box is
    the order Eq. ``eq:boxrows`` fixes: the ``m`` cap rows first, row ``i``
    belonging to ``chat^(i)``, then the ``m`` floor rows in the same order.
    "Row indices are always integers in ``{1, ..., 2m}`` and never alphabet
    elements" (the conventions of ``interface.yaml``).
    """

    outcomes: tuple[str, ...]
    rows: tuple[tuple[Fraction, ...], ...]
    rhs: tuple[Fraction, ...]
    #: ``(q^-, q^+)`` when the geometry claims canonical box form; ``None`` for
    #: a general polytope. A sub-form, not a third tag (Remark rem:two-tags).
    box_bounds: tuple[tuple[Fraction, ...], tuple[Fraction, ...]] | None = None

    @property
    def tag(self) -> GeometryTag:
        """Return the tag this geometry carries."""
        return GeometryTag.POLYTOPE

    @property
    def m_row(self) -> int:
        """Return ``m_row``, the row count of Definition ``def:taxonomy``."""
        return len(self.rows)

    @property
    def is_canonical_box(self) -> bool:
        """Return whether a ``(q^-, q^+)`` pair is recorded."""
        return self.box_bounds is not None

    def as_machine_record(self) -> dict[str, object]:
        """Return the record under the machine key ``acceptance_set``.

        SERIALIZED SUB-KEYS ARE AN IMPLEMENTATION CHOICE, DECIDED HERE AND
        RECORDED, for the same reason and on the same ground as
        :meth:`SingletonGeometry.as_machine_record`: the claim files fix
        ``geometry_tag`` and ``box_bounds`` and names ``m_row``, ``B`` and
        ``b`` by symbol alone. The keys chosen are ``m_row`` -- the contract's
        own name, after the 0.1.2 rename away from ``r`` -- together with
        ``rows`` for ``B`` and ``rhs`` for ``b``, which are the field names the
        CONSUMER already reads that data under
        (``certiqs_key.meat_core.declaration.declaration.PolytopeData``). ``box_bounds``
        is omitted rather than written ``null`` when the geometry is not in
        canonical box form, because the key's presence is what claims the
        sub-form.
        """
        record: dict[str, object] = {
            "geometry_tag": str(self.tag),
            "m_row": self.m_row,
            "rows": self.rows,
            "rhs": self.rhs,
        }
        if self.box_bounds is not None:
            record["box_bounds"] = self.box_bounds
        return record


def canonical_box(
    outcomes: tuple[str, ...],
    lower: tuple[Fraction, ...],
    upper: tuple[Fraction, ...],
) -> PolytopeGeometry:
    """Return the canonical box form of Eq. ``eq:boxrows`` on the given bounds.

    ``m_row = 2m``; row ``i`` is ``+delta_{chat^(i)}`` with right-hand side
    ``q^+(chat^(i))``, and row ``m + i`` is ``-delta_{chat^(i)}`` with
    right-hand side ``-q^-(chat^(i))``. Every entry of ``B`` is in ``{0, +-1}``
    (Theorem ``thm:box-construction`` (i)).

    The rows are BUILT here rather than declared, so the data cannot contradict
    itself: a geometry whose recorded ``box_bounds`` disagree with its rows is
    the defect the consumer's well-formedness check exists to catch, and the
    construction map must not be able to produce one.
    """
    size = len(outcomes)
    if len(lower) != size or len(upper) != size:
        raise ValueError(
            "a canonical box carries one (q^-, q^+) pair per element of Chat; "
            f"got {len(lower)} and {len(upper)} against |Chat| = {size}"
        )
    caps = tuple(
        tuple(_ONE if column == index else _ZERO for column in range(size))
        for index in range(size)
    )
    floors = tuple(
        tuple(-_ONE if column == index else _ZERO for column in range(size))
        for index in range(size)
    )
    return PolytopeGeometry(
        outcomes=outcomes,
        rows=caps + floors,
        rhs=tuple(upper) + tuple(-value for value in lower),
        box_bounds=(tuple(lower), tuple(upper)),
    )


def validate_geometry(
    geometry: SingletonGeometry | PolytopeGeometry,
) -> GeometryVerdict:
    """Return the verdict of the validation predicate of Definition ``def:taxonomy``.

    Well-formedness FIRST, emptiness second (see the module docstring). For a
    ``polytope`` NOT in canonical box form the predicate is rational
    feasibility of ``{q >= 0, sum q = 1, B q <= b}``, which is not a closed form
    and is not decided here: this module emits only canonical boxes (Definition
    ``def:construction``), and deciding a declared general polytope is a linear
    program the consuming package already owns and runs at its own boundary
    (``certiqs_key.meat_core.acceptance.geometry.polytope_is_nonempty``). Writing a
    second exact simplex here would be a parallel implementation of one
    decision, which is how two answers to one question come to exist. Such a
    geometry raises :class:`~certiqs_key.statistics.errors.UndecidedGeometryError`
    AFTER its shape has been checked, so that ill-formed data is still named
    ill-formed rather than deferred.
    """
    if isinstance(geometry, SingletonGeometry):
        return _singleton_verdict(geometry)
    return _polytope_verdict(geometry)


def _singleton_verdict(geometry: SingletonGeometry) -> GeometryVerdict:
    """Return the verdict for a ``singleton``: a membership test, and both halves."""
    if len(geometry.frequencies) != len(geometry.outcomes):
        return GeometryVerdict(
            GeometryDefect.ILL_FORMED,
            f"q^* carries {len(geometry.frequencies)} coordinates against "
            f"|Chat| = {len(geometry.outcomes)}",
        )
    if any(value < _ZERO for value in geometry.frequencies):
        return GeometryVerdict(
            GeometryDefect.EMPTY,
            "the singleton validation predicate asks q^*(chat) >= 0 for EVERY "
            "chat, and a coordinate is negative, so {q^*} is not a subset of "
            "the simplex (Theorem thm:geometry-validation (ii): the predicate is "
            "necessary as well as sufficient)",
        )
    total = sum(geometry.frequencies, _ZERO)
    if total != _ONE:
        return GeometryVerdict(
            GeometryDefect.EMPTY,
            f"q^* sums to {total} rather than 1, so {{q^*}} is not a subset of "
            "the simplex (Theorem thm:geometry-validation (ii))",
        )
    return GeometryVerdict(None)


def _polytope_verdict(geometry: PolytopeGeometry) -> GeometryVerdict:
    """Return the verdict for a ``polytope``, box sub-form included."""
    size = len(geometry.outcomes)
    if size < 1:
        return GeometryVerdict(
            GeometryDefect.ILL_FORMED,
            "the acceptance alphabet is empty, so no polytope is declared on it",
        )
    for index, row in enumerate(geometry.rows):
        if len(row) != size:
            return GeometryVerdict(
                GeometryDefect.ILL_FORMED,
                f"row {index} of B has {len(row)} columns against |Chat| = {size}",
            )
    if len(geometry.rhs) != geometry.m_row:
        return GeometryVerdict(
            GeometryDefect.ILL_FORMED,
            f"b has {len(geometry.rhs)} entries but B has {geometry.m_row} rows; "
            "they are read positionally against each other",
        )
    if geometry.box_bounds is None:
        raise UndecidedGeometryError(
            "this polytope is not in canonical box form, so its validation "
            "predicate is rational feasibility of {q >= 0, sum q = 1, "
            "B q <= b} rather than the closed form Eq. eq:boxfeas. Refusing to "
            "answer is not a verdict that the data is defective, which is why "
            "this raises rather than returning one"
        )
    lower, upper = geometry.box_bounds
    if len(lower) != size or len(upper) != size:
        return GeometryVerdict(
            GeometryDefect.ILL_FORMED,
            "box_bounds must carry one (q^-, q^+) pair per element of Chat, "
            f"which has {size}",
        )
    for index in range(size):
        if not _ZERO <= lower[index] <= upper[index]:
            return GeometryVerdict(
                GeometryDefect.ILL_FORMED,
                "a canonical box requires 0 <= q^- <= q^+ componentwise "
                f"(Definition def:taxonomy); at column {index} the pair is "
                f"({lower[index]}, {upper[index]}), so this data is not a "
                "canonical box and the closed form Eq. eq:boxfeas -- which is "
                "proved under that hypothesis -- does not apply to it",
            )
    rows_defect = _canonical_rows_defect(geometry, lower, upper)
    if rows_defect is not None:
        return GeometryVerdict(GeometryDefect.ILL_FORMED, rows_defect)
    if not sum(lower, _ZERO) <= _ONE <= sum(upper, _ZERO):
        return GeometryVerdict(
            GeometryDefect.EMPTY,
            f"Eq. eq:boxfeas fails: sum q^- = {sum(lower, _ZERO)} and "
            f"sum q^+ = {sum(upper, _ZERO)} do not bracket 1, so the "
            "denotation is empty (Theorem thm:geometry-validation (iii))",
        )
    return GeometryVerdict(None)


def _canonical_rows_defect(
    geometry: PolytopeGeometry,
    lower: tuple[Fraction, ...],
    upper: tuple[Fraction, ...],
) -> str | None:
    """Return why the rows are not the canonical box rows of the pair, or ``None``."""
    size = len(geometry.outcomes)
    if geometry.m_row != 2 * size:
        return (
            f"a canonical box on {size} outcomes has m_row = {2 * size} rows "
            f"(Eq. eq:boxrows), but {geometry.m_row} are declared"
        )
    for index in range(size):
        cap = tuple(_ONE if column == index else _ZERO for column in range(size))
        floor = tuple(-_ONE if column == index else _ZERO for column in range(size))
        if geometry.rows[index] != cap or geometry.rhs[index] != upper[index]:
            return (
                f"row {index} is not the canonical cap row of column {index} "
                "(Eq. eq:boxrows: +delta_i^T q <= q^+(chat^(i)))"
            )
        if (
            geometry.rows[size + index] != floor
            or geometry.rhs[size + index] != -lower[index]
        ):
            return (
                f"row {size + index} is not the canonical floor row of column "
                f"{index} (Eq. eq:boxrows: -delta_i^T q <= -q^-(chat^(i)))"
            )
    return None


def box_witness_point(
    lower: tuple[Fraction, ...], upper: tuple[Fraction, ...]
) -> tuple[Fraction, ...] | None:
    """Return an explicit point of a non-empty canonical box, or ``None``.

    The ``(<=)`` direction of Theorem ``thm:geometry-validation`` (iii) made
    constructive. That proof interpolates ``q(theta) = q^- + theta (q^+ - q^-)`` and
    appeals to the intermediate value theorem; the map
    ``theta -> sum_chat q(theta)(chat)`` is AFFINE, so the witness is available in
    closed form and is RATIONAL whenever the data is:

        theta^* = (1 - sum q^-) / (sum q^+ - sum q^-)   if sum q^+ > sum q^- ,
        theta^* = 0                                     otherwise ,

    the second branch being correct because ``sum q^- <= 1 <= sum q^+`` with the
    two sums equal forces both to be ``1``. The theorem's witness is real-valued
    where the predicate it certifies is rational; this is the one-line rational
    witness, and it divides by zero if the second branch is not taken -- which
    is not an exotic input, being exactly what the construction map emits from a
    degenerate honest distribution (Proposition ``prop:rule-exact`` (v)).

    ``None`` when Eq. ``eq:boxfeas`` fails, i.e. when there is no point to
    exhibit.
    """
    total_lower = sum(lower, _ZERO)
    total_upper = sum(upper, _ZERO)
    if not total_lower <= _ONE <= total_upper:
        return None
    theta = (
        _ZERO
        if total_upper == total_lower
        else (_ONE - total_lower) / (total_upper - total_lower)
    )
    return tuple(
        low + theta * (high - low) for low, high in zip(lower, upper, strict=True)
    )


def acceptance_support(
    geometry: SingletonGeometry | PolytopeGeometry,
) -> tuple[str, ...]:
    """Return ``Chat^+``, the key ``acceptance_support`` of thm:box-oracle (i).

    THE FORMULA IS THE OUTPUTS TABLE'S, LITERALLY (``interface.yaml``):

        Chat^+ = {chat : q^+(chat) > 0}     for the box form,
        Chat^+ = supp q^*                   for `singleton`.

    WHAT IS EMITTED FOR THE BOX FORM IS THE CAP-POSITIVITY SET ``Chat^+``,
    WHICH IS A SUPERSET OF ``meat-core``'S ACCEPTANCE SUPPORT AND IS NEVER TO
    BE SUBSTITUTED FOR IT. The consuming notion --
    ``meat-core/frank-wolfe/lem:fo-khyp``'s ``eq:chacc-def`` -- is the UNION OF
    THE SUPPORTS of the members of ``AcceptSet``, and the MINIMAL set with the
    property that ``supp q`` lies inside it for every ``q`` in ``AcceptSet``.
    Theorem ``thm:box-oracle`` (i) proves that ``Chat^+`` HAS that property, and that
    is all it proves: it does NOT claim ``Chat^+`` is the union, and in general
    it is not. The frozen ``ACC-support-superset`` case emits a box with
    ``q^+(c1) = 1 > 0`` at an outcome every feasible point gives mass zero,
    because the floors already exhaust the normalization.

    EMITTING ``Chat^+`` IS CONFORMING and is what the outputs table asks for;
    substituting the minimal set computes a different quantity, and computing
    it means solving one linear program per outcome on an output whose
    specification is a one-line test on ``q^+``. A consumer that wants the
    minimal set computes it itself, and
    ``certiqs_key.meat_core.acceptance.geometry.polytope_support`` is where it
    does.

    FOR ``singleton`` THE CONTRACT DOES CLAIM MINIMALITY -- Theorem ``thm:box-oracle``
    (i), last sentence -- and the formula is correspondingly exact. The two
    branches are not the same kind of statement, and the difference is the
    contract's rather than this module's.

    A ``polytope`` that is not in canonical box form has no cap vector to read,
    so the Outputs-table formula has no instance; the whole alphabet is
    returned, which is an acceptance support for any subset of the simplex --
    trivially, and without pretending to more.
    """
    if isinstance(geometry, SingletonGeometry):
        return tuple(
            outcome
            for outcome, value in zip(
                geometry.outcomes, geometry.frequencies, strict=True
            )
            if value > _ZERO
        )
    if geometry.box_bounds is None:
        return geometry.outcomes
    _, upper = geometry.box_bounds
    return tuple(
        outcome
        for outcome, cap in zip(geometry.outcomes, upper, strict=True)
        if cap > _ZERO
    )
