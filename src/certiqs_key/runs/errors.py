"""The hard errors of a run -- and the rule that a REFUSAL is not one.

Two categories, kept apart for the same reason
:mod:`certiqs_key.protocol_compiler.errors` keeps them apart.

A **refusal** is a conforming answer that an owning module produced: the compiler
refusing a specification, ``statistics`` reporting an infeasible
input, ``meat-core`` emitting no key-length claim behind a security gate. None of
those is an exception here. They are carried out of
:func:`certiqs_key.runs.pipeline.run_slice` as a typed outcome, with the refusing
module's own machine-readable reason attached, because a caller is entitled to
see WHICH check refused and to act on it. One kind of refusal is the run
tier's own: a check of a module's RESULT against its own declaration, made
after the module answered (the plausibility check of
:mod:`certiqs_key.runs.plausibility`). Its code is a member of
:class:`RunRefusalReason`, and it is carried the same way.

An **error** is a call the orchestration cannot make sense of at all. Nothing in
any contract is about such an argument, so there is no module reason code to
name and no default to substitute.

INPUT ERRORS CARRY A CODE OF THE RUN TIER'S OWN
===============================================
One kind of error is common and a caller can fix it: the configuration a caller
handed in, before anything is composed -- an unknown parameter, a value outside
its domain, a probability family that does not normalise, a tolerance that was
never declared. Those raise :class:`RunInputError`, whose :attr:`~RunInputError.reason`
is a member of :class:`RunInputReason`, the ONE closed vocabulary of such codes.
A consumer words the code; it does not parse the
message or guess from the module that raised. Each concrete class also subclasses
the builtin the check raised before the codes existed (:class:`KeyError`,
:class:`ValueError`, :class:`TypeError`), which costs nothing and keeps a plain
``except ValueError`` working. The codes and their meanings for a caller are
listed in ``instances/NOTES.md``; a test holds that list to this enum.

WHY THE BASE CLASS LIVES HERE AND NOT WITH AN INSTANCE
======================================================
Before the tier split of PRINCIPLES.md section 4 these classes shared one module with
the BB84 honest-model errors, under a ``BB84SliceError`` base. That base named the wrong
thing: an acceptance alphabet disagreement is a defect in the orchestration's hand-off,
and it is not about BB84 in any way. :class:`RunError` is the base for what the run
itself raises; an instance or the honest-model library derives its own model errors
from it (``instances.common.honest.depolarized_bell_pair.HonestModelError``), so
``except RunError`` still catches everything a run can raise.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "RunError",
    "RunInputError",
    "RunInputKeyError",
    "RunInputReason",
    "RunInputTypeError",
    "RunInputValueError",
    "RunRefusalReason",
    "SliceAssemblyError",
]


class RunError(Exception):
    """Base class for every hard error raised while assembling or driving a run."""


class SliceAssemblyError(RunError):
    """Two stages of the pipeline disagree about something neither may decide.

    Raised where an owning module's output cannot be handed to the next one at
    all -- the acceptance construction and the compiled declaration disagreeing
    about the acceptance alphabet is the case this exists for. It is a defect in
    one of the two, not a refusal by either, so it is reported as an error rather
    than turned into an outcome code the contracts do not define.
    """


class RunInputReason(StrEnum):
    """Why a caller's input was refused before a run: the closed vocabulary.

    Defined once, here. A new input check adds its member here, in the open, and
    to the table in ``instances/NOTES.md``; no instance writes a code of its own.
    """

    # The instance's parameter table (runs.surface.check_keys).
    UNKNOWN_PARAMETER = "unknown_parameter"
    MISSING_PARAMETER = "missing_parameter"
    WRONG_KIND = "wrong_kind"
    NOT_AN_INTEGER = "not_an_integer"
    OUTSIDE_DOMAIN = "outside_domain"
    PORT_LABELS_MISMATCH = "port_labels_mismatch"
    # Reading one number (runs.inputs).
    NOT_A_NUMBER = "not_a_number"
    UNREADABLE_NUMBER = "unreadable_number"
    NOT_FINITE = "not_finite"
    OUTSIDE_BINARY64 = "outside_binary64"
    # Preparing a probability family or bound (runs.inputs).
    PROBABILITY_FAMILY_EMPTY = "probability_family_empty"
    PROBABILITY_OUTSIDE_UNIT_INTERVAL = "probability_outside_unit_interval"
    NORMALIZATION_EXCEEDS_TOLERANCE = "normalization_exceeds_tolerance"
    POSITIVE_SUPPORT_LOST = "positive_support_lost"
    PREPARATION_ARGUMENT_INVALID = "preparation_argument_invalid"
    # The configuration record (runs.config.RunConfig and SolverSettings).
    DECLARED_TOLERANCE_ABSENT = "declared_tolerance_absent"
    DECLARED_TOLERANCE_NOT_BINARY64 = "declared_tolerance_not_binary64"
    DECLARED_TOLERANCE_OUT_OF_DOMAIN = "declared_tolerance_out_of_domain"
    ENDPOINT_RULE_NOT_ADMITTED = "endpoint_rule_not_admitted"
    TAIL_EVALUATION_NOT_ADMITTED = "tail_evaluation_not_admitted"
    SOLVER_BUDGET_NOT_POSITIVE = "solver_budget_not_positive"
    SOLVER_GAP_TOLERANCE_NOT_POSITIVE = "solver_gap_tolerance_not_positive"
    SOLVER_ORACLE_NOT_ADMITTED = "solver_oracle_not_admitted"
    SOLVER_METHOD_NOT_ADMITTED = "solver_method_not_admitted"
    #: Both ``solver.method`` and ``solver.advanced.method`` chosen (record
    #: 0.43.0): the advanced one would override the other silently.
    SOLVER_METHOD_SET_TWICE = "solver_method_set_twice"
    #: A ``solver`` or ``solver.advanced`` key the settings do not read,
    #: among them the flat keys that moved under ``solver.advanced`` (record
    #: 0.43.0); refused rather than ignored, so a misplaced choice is not
    #: silently the default.
    SOLVER_KEY_NOT_ADMITTED = "solver_key_not_admitted"
    #: ``solver.advanced.certified_evaluation`` (record 0.43.0; flat
    #: ``solver.certified_evaluation`` from 0.33.0) not one of on, off, strict.
    SOLVER_CERTIFIED_EVALUATION_NOT_ADMITTED = (
        "solver_certified_evaluation_not_admitted"
    )
    #: An ``alpha_search`` whose interval is not inside ``(0, 1)`` in
    #: ``alpha - 1``, ordered, or whose budget is not a grid of two or more
    #: points and a non-negative refinement (record schema 0.24.0).
    ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN = "alpha_search_setting_out_of_domain"
    #: A configuration that fixes ``alpha`` and asks for an alpha search.
    ALPHA_AND_ALPHA_SEARCH_BOTH_SET = "alpha_and_alpha_search_both_set"
    #: ``eps_auth`` outside ``[0, 1)`` or ``k_auth`` not a non-negative
    #: integer (meat-core's parameters rows of A-AUTH; record schema 0.20.0).
    AUTHENTICATION_PARAMETER_OUT_OF_DOMAIN = "authentication_parameter_out_of_domain"
    #: ``reference_enclosure`` or ``strict_snaps`` not a boolean
    #: (``foundations/req:snap-reference`` (i), (iv); record schema 0.22.0).
    SNAP_SETTING_OUT_OF_DOMAIN = "snap_setting_out_of_domain"
    #: ``statistics_check`` not one of on, off, or ``min_model_pass_probability``
    #: not an exact rational in ``(0, 1]``
    #: (``meat-core/req:unreachable-acceptance-set``; record schema 0.46.0).
    STATISTICS_CHECK_SETTING_OUT_OF_DOMAIN = "statistics_check_setting_out_of_domain"
    #: A configuration payload that names a run parameter the engine no
    #: longer has: ``certify_snaps`` and ``certified_weight_ceiling``, removed
    #: with the certification of snaps (record schema 0.28.0), and
    #: ``strict_certification``, renamed ``strict_snaps`` (record schema
    #: 0.29.0), and ``contradiction_share``, whose share rule gave way to
    #: ``min_model_pass_probability`` (record schema 0.46.0). Refused rather
    #: than ignored, so that a caller who asks for a
    #: retired behaviour is told it is gone instead of getting the default
    #: silently.
    RETIRED_PARAMETER = "retired_parameter"
    # A warm-start seed (runs.config.WarmStartSeed, runs.iterate_file).
    WARM_START_HASH_MALFORMED = "warm_start_hash_malformed"
    WARM_START_FILE_MISSING = "warm_start_file_missing"
    WARM_START_HASH_MISMATCH = "warm_start_hash_mismatch"
    WARM_START_NOT_AN_ITERATE = "warm_start_not_an_iterate"


class RunRefusalReason(StrEnum):
    """Why the run tier itself refused: its own checks of what the stages hand on.

    Every other refusal of a run is a module's, under that module's code
    (:class:`~certiqs_key.runs.pipeline.SliceRefusal`). This vocabulary holds
    the codes of the run tier's own checks of what came back, each of which
    states its motivation where it is implemented, of the one evaluation
    the outer alpha search refuses itself because its solve raised
    (:attr:`ORACLE_FAILURE`), and of the one check made before the honest
    model runs (:attr:`FACTORED_LOSS_NOT_APPLIED`). Not an input code: nothing
    a caller handed in was malformed, so it is carried as a refusal outcome
    and never raised.
    """

    #: The bound the key length is computed from exceeds what any key could
    #: carry, ``log2(d_Z + 1)`` times the largest key-live probability over the
    #: acceptance set (``meat-core/prop:value-range`` (ii);
    #: :mod:`certiqs_key.runs.plausibility`; record schema 0.25.0): the
    #: accepted statistics contradict the declared model. Since 0.35.0 the
    #: comparison is exact on a certified number, and an outer alpha search
    #: that meets it stops and refuses the run as a whole
    #: (:mod:`certiqs_key.runs.alpha_search`).
    ENTROPY_BOUND_ABOVE_KEY_CEILING = "entropy_bound_above_key_ceiling"
    #: The run declares the strict option and, after its search, a moved block
    #: of a measurement snap or a moved class of the emission is not evaluated
    #: off its snap, so a key length would rest on A-SNAP
    #: (``foundations/req:snap-reference`` (iv); record schema 0.28.0). The
    #: same string the snap and the emission refuse under where the resting is
    #: decided earlier.
    STRICT_SNAPS = "strict_snaps"
    #: One evaluation of the outer alpha search raised because that alpha's
    #: solve stopped on an unsolved oracle status, neither optimal nor an
    #: infeasibility verdict (``OracleFailure.unsolved``), so that alpha gave
    #: no run to read. The search records it as refused, as
    #: ``solve: oracle_failure``, and goes on with its other alphas
    #: (:mod:`certiqs_key.runs.alpha_search`). An infeasibility verdict
    #: is no such failure: it says the declaration is not admissible at every
    #: alpha, and still stops the search.
    ORACLE_FAILURE = "oracle_failure"
    #: A station's receiver was compiled at its normalized station, factored
    #: loss t < 1, and the honest provider does not declare that it applies
    #: ``Lambda^loss_t`` to that station's input before it evaluates the
    #: emitted measurement (``receiver/detector-imperfections/
    #: req:loss-before-evaluation``; record schema 0.38.0), or, since 0.39.0,
    #: the raw ``X x V`` provider does not (``LossAppliedRawProvider``).
    #: Refused at ``honest_model`` before the provider is called: its law would
    #: be that of a receiver more efficient than the device, and the acceptance
    #: set, or lambda_EC and the raw table, would be built around statistics
    #: the device does not produce.
    FACTORED_LOSS_NOT_APPLIED = "factored_loss_not_applied"


class RunInputError(RunError):
    """A caller's input was refused before a run; :attr:`reason` says why.

    Never raised itself: each concrete class below also subclasses the builtin
    its check raises, so ``except RunInputError`` catches every coded input
    error and ``except KeyError`` (and so on) still catches its own.
    ``str(error)`` is the human message, also for the ``KeyError`` member, whose
    builtin would otherwise render it quoted.
    """

    def __init__(self, message: str, *, reason: RunInputReason) -> None:
        """Keep the machine-readable code beside the human message."""
        super().__init__(message)
        #: The machine-readable code, a member of the closed vocabulary.
        self.reason: RunInputReason = RunInputReason(reason)
        #: The human message, one sentence naming the input and what is wrong.
        self.message = message

    def __str__(self) -> str:
        """Return the human message."""
        return self.message


class RunInputKeyError(RunInputError, KeyError):
    """An input names a key the check does not know, or lacks one it needs."""


class RunInputValueError(RunInputError, ValueError):
    """An input carries a value its check does not admit."""


class RunInputTypeError(RunInputError, TypeError):
    """An input carries an object that is not a number where one is read."""
