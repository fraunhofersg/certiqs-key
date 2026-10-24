"""The settings axis: the probe declaration, its admission, and the seam.

Definition ``def:probe`` and Requirement ``req:probe-diagonal-admission``,
which are the core's, and the one place where the core hands a setting to the
submodule that constructs it.

THE SETTINGS AXIS IS THE CORE'S
===============================
Every receiver has a probe declaration ``(T, {rho^(t)})``. A receiver without
source modes (``Inp_S`` empty) declares exactly ``T = {off}``, and the core
constructs its one setting itself: Corollary ``cor:unconditioned-family``
makes it a setting family (Definition ``def:setting-family``) whose
prefactors are all exactly one and whose exact flag is set, read off the
single declared fact ``Inp_S = empty`` (Remark ``rem:flag-instances``). The
types below, the admission check and the probe-free construction are that
much and no more, and they are what every probe-free receiver needs.

A RECEIVER WITH SOURCE MODES IS A SUBMODULE'S
=============================================
Conditioning on a declared probe state is not the core's: a submodule that
constructs another setting family proves there that it is one
(Definition ``def:setting-family``, lead-in), states at which of its
settings the exact flag is set (Remark ``rem:flag-instances``), and states the
enclosure of its blocks (``detector-imperfections/req:dark-composed-reference``
(ii)-(iv)). The probe-conditioning submodule is that submodule; its code is
:mod:`certiqs_key.receiver.probe`, and it is REMOVABLE: its interface's
``removability`` block lists what deleting it deletes.

So the core reaches it through ONE function, :func:`setting_construction`,
and only for a receiver that declares source modes -- which, Definition
``def:probe`` fixing ``T = {off}`` when ``Inp_S`` is empty, is every receiver
whose declaration carries a setting other than ``off``. The function returns a
:class:`SettingConstruction`: the core's own :data:`UNCONDITIONED` for a
probe-free receiver, the submodule's otherwise, loaded by name, so that no
core module imports the submodule and deleting it leaves every core module
importable. Where the submodule is absent, a receiver with source modes is
REFUSED at validation, under the ``fail_closed`` convention, with the reason
``probe_conditioning_submodule_absent``
(:func:`check_setting_construction`): a refusal naming what is missing, and
never an ``ImportError``. ``tests/unit/test_receiver_probe_isolation.py``
holds the core to the seam.

OCCUPATION-DIAGONALITY IS VALIDATED BY CONSTRUCTION, NOT ASSUMED OF A MATRIX
=============================================================================
Requirement ``req:probe-diagonal-admission``: the engine admits a probe
declaration only in the Gaussian tier of Def. ``def:probe``, whose states are
occupation-diagonal by construction. A setting of the Gaussian tier is
presented as its diagonal of mean photon numbers, so no state outside the tier
can be declared at all: diagonality is a property of the TYPE, and the only
thing left to validate is ``nbar >= 0`` -- which is what
:func:`check_probe_declaration` does. Occupation-diagonality is the checkable
form of the condition under which the channel grading of the blocks is
recovered from the total one (Remark ``rem:blockmeaning``).
"""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import ClassVar, Final, Protocol, cast

from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.generic import (
    Arithmetic,
    Field,
    GenericMatrix,
    NoClickPairs,
    unconditioned_pairs,
)
from certiqs_key.receiver.grams import GramFamily
from certiqs_key.receiver.numerics import Scalar, to_float
from certiqs_key.receiver.povm import NoClickFamily, unconditioned_family
from certiqs_key.receiver.reasons import Refusal, RefusalReason

__all__ = [
    "CONDITIONING_MODULE",
    "OFF_SETTING",
    "UNCONDITIONED",
    "ProbeDeclaration",
    "ProbeSetting",
    "SettingConstruction",
    "check_probe_declaration",
    "check_setting_construction",
    "conditioning_present",
    "predicate_x_holds",
    "setting_construction",
]

#: The setting Definition ``def:probe`` requires every declaration to carry,
#: "whose state is vacuum". When ``Inp_S`` is empty the declaration is exactly
#: ``{off}`` and every statement about conditioning is vacuous.
OFF_SETTING = "off"

#: The module of the submodule that constructs the setting family of a receiver
#: with source modes. Named here and nowhere else in the core: the seam loads it
#: by this name, so that its absence is a refusal and not an import error.
CONDITIONING_MODULE: Final[str] = "certiqs_key.receiver.probe"


@dataclass(frozen=True)
class ProbeSetting:
    """One declared probe setting of the Gaussian tier.

    ``mean_photon_numbers`` is the diagonal of ``Gamma^{(t)}``, one entry per
    declared source mode in the ``Inp_S`` order. A zero-mean Gaussian state
    with diagonal normally-ordered second-moment matrix is a product of
    single-mode thermal states, and ``Gamma^{(t)} = 0`` IS VACUUM.
    """

    label: str
    mean_photon_numbers: tuple[Scalar, ...] = ()
    #: The reserved optional ``tolerance`` field of every declared parameter
    #: (Requirement ``req:reserved-tolerance-field``; Assumption ``ass:exact``),
    #: keyed by parameter name, as :class:`~certiqs_key.receiver.catalogue.Component`
    #: carries it. Absent or exactly zero is admitted and anything else is
    #: refused by :func:`certiqs_key.receiver.validation.check_parameter_tolerances`.
    #: Excluded from the hash, so that the record stays hashable.
    tolerances: Mapping[str, Scalar] = field(
        default_factory=dict, kw_only=True, hash=False
    )

    #: How a refusal names this record (``check_parameter_tolerances``).
    record_kind: ClassVar[str] = "probe setting"

    @property
    def is_vacuum(self) -> bool:
        """Return whether ``Gamma^{(t)} = 0`` -- the probe-off condition."""
        return all(to_float(value) == 0.0 for value in self.mean_photon_numbers)

    def diagonal(self) -> tuple[float, ...]:
        """Return ``Gamma^{(t)}`` as its diagonal, in machine numbers."""
        return tuple(to_float(value) for value in self.mean_photon_numbers)


@dataclass(frozen=True)
class ProbeDeclaration:
    """The pair ``(T, {rho^{(t)}})`` of Definition ``def:probe``."""

    settings: tuple[ProbeSetting, ...]

    @property
    def labels(self) -> tuple[str, ...]:
        """Return the declared probe alphabet ``T``, in its declared order."""
        return tuple(setting.label for setting in self.settings)

    def setting(self, label: str) -> ProbeSetting:
        """Return the declared setting with the given label."""
        for candidate in self.settings:
            if candidate.label == label:
                return candidate
        raise HypothesisError(f"no probe setting {label!r} is declared")

    @classmethod
    def probe_free(cls) -> ProbeDeclaration:
        """Return the declaration of a receiver with no source modes.

        Definition ``def:probe``: "When ``Inp_S`` is empty the declaration is
        ``T = {off}`` and every statement about conditioning is vacuous."
        """
        return cls((ProbeSetting(OFF_SETTING, ()),))


def check_probe_declaration(
    declaration: ProbeDeclaration, source_dimension: int
) -> Refusal | None:
    """Return a refusal if the declared probe is not well formed.

    Requirement ``req:probe-diagonal-admission``: the declaration's type admits
    only the Gaussian tier, and this check refuses what the type cannot rule
    out. Definition ``def:probe``: ``T`` is a finite NON-EMPTY alphabet -- a set, so
    no label is declared twice -- INCLUDING the setting ``off`` whose state is
    vacuum; each ``Gamma^{(t)}`` is diagonal
    and positive semidefinite, i.e. every declared mean photon number is
    non-negative; and when ``Inp_S`` is empty the declaration is exactly
    ``{off}``.
    """
    if not declaration.settings:
        return Refusal(
            RefusalReason.PROBE_ALPHABET_EMPTY,
            "the probe alphabet T is empty; Definition def:probe requires a "
            "finite NON-EMPTY alphabet",
        )
    repeated = sorted(
        {label for label in declaration.labels if declaration.labels.count(label) > 1}
    )
    if repeated:
        return Refusal(
            RefusalReason.PROBE_ALPHABET_LABEL_REPEATED,
            f"the probe alphabet {list(declaration.labels)} declares the "
            f"label(s) {repeated} more than once; Definition def:probe's T is "
            f"an alphabet, a set of settings",
        )
    if OFF_SETTING not in declaration.labels:
        return Refusal(
            RefusalReason.PROBE_SETTING_OFF_MISSING,
            f"the probe alphabet {list(declaration.labels)} does not include "
            f"the setting {OFF_SETTING!r}, which Definition def:probe requires "
            f"and whose state is vacuum",
        )
    for setting in declaration.settings:
        if len(setting.mean_photon_numbers) != source_dimension:
            return Refusal(
                RefusalReason.PROBE_DECLARED_WITHOUT_SOURCE_MODES,
                f"setting {setting.label!r} declares "
                f"{len(setting.mean_photon_numbers)} mean photon number(s) for "
                f"{source_dimension} declared source mode(s)",
            )
        for index, value in enumerate(setting.diagonal()):
            if value < 0.0:
                return Refusal(
                    RefusalReason.PROBE_MEAN_PHOTON_NUMBER_NEGATIVE,
                    f"setting {setting.label!r} declares nbar = {value} on "
                    f"source mode {index}; Definition def:probe requires "
                    f"Gamma^(t) >= 0",
                )
    if source_dimension == 0 and declaration.labels != (OFF_SETTING,):
        return Refusal(
            RefusalReason.PROBE_DECLARED_WITHOUT_SOURCE_MODES,
            f"Inp_S is empty but the declared alphabet is "
            f"{list(declaration.labels)}; Definition def:probe fixes it to "
            f"{{{OFF_SETTING}}} in that case",
        )
    off = declaration.setting(OFF_SETTING)
    if not off.is_vacuum:
        return Refusal(
            RefusalReason.PROBE_SETTING_OFF_MISSING,
            f"the setting {OFF_SETTING!r} declares a non-vacuum state; "
            f"Definition def:probe fixes its state to vacuum",
        )
    return None


class SettingConstruction(Protocol):
    """How the declared settings of a receiver become a setting family.

    Definition ``def:setting-family``: per setting, a POVM whose joint
    no-click elements have the prefactor form, and an exact flag set by the
    construction. The core's construction is :data:`UNCONDITIONED`
    (Corollary ``cor:unconditioned-family``); a submodule supplies another
    for a receiver with source modes, through :func:`setting_construction`.
    """

    @property
    def enclosure_claims(self) -> tuple[str, ...]:
        """Return the claims establishing the enclosure of this family's blocks.

        Those that establish the enclosure, positive semidefiniteness and
        completeness of the blocks this construction yields, beside the
        dark-count composition's
        (``detector-imperfections/req:dark-composed-reference`` (iii)).
        """
        ...

    def exact_flag(self, setting: ProbeSetting) -> bool:
        """Return the setting's exact flag, read off the declaration alone."""
        ...

    def no_click_family(
        self, family: GramFamily, setting: ProbeSetting, channel_dimension: int
    ) -> NoClickFamily:
        """Return the setting's joint no-click pairs ``(c_J, B_J)``, in binary64."""
        ...

    def no_click_pairs[N: Arithmetic](
        self,
        field: Field[N],
        grams: Sequence[GenericMatrix[N]],
        channel_dimension: int,
        setting: ProbeSetting,
    ) -> NoClickPairs[N]:
        """Return the setting's joint no-click pairs in the arithmetic ``field``."""
        ...


@dataclass(frozen=True)
class _Unconditioned:
    """The core's construction: the receiver without source modes.

    Corollary ``cor:unconditioned-family``: one setting ``off`` with
    ``M_{S|off} = M_S``, every prefactor exactly one and every effective Gram
    the subset sum ``A_J`` (Theorem ``thm:click-povm`` (ii)), and the exact
    flag set, read off the declared fact ``Inp_S = empty`` with no arithmetic
    performed.
    """

    enclosure_claims: tuple[str, ...] = (
        "receiver/thm:enclosed-blocks (ii)",
        "receiver/detector-imperfections/cor:exact-dark-composed (iii)",
    )

    def exact_flag(self, setting: ProbeSetting) -> bool:
        """Return ``True``: exact by Cor. ``cor:unconditioned-family`` (c)."""
        return True

    def no_click_family(
        self, family: GramFamily, setting: ProbeSetting, channel_dimension: int
    ) -> NoClickFamily:
        """Return ``(1, A_J)`` for every ``J`` -- Thm. ``thm:click-povm`` (ii)."""
        if channel_dimension != family.dimension:
            raise HypothesisError(
                "a receiver without source modes has Inp = Inp_C "
                "(Cor. cor:unconditioned-family)"
            )
        return unconditioned_family(family)

    def no_click_pairs[N: Arithmetic](
        self,
        field: Field[N],
        grams: Sequence[GenericMatrix[N]],
        channel_dimension: int,
        setting: ProbeSetting,
    ) -> NoClickPairs[N]:
        """Return ``(1, A_J)`` for every ``J`` -- Thm. ``thm:click-povm`` (ii)."""
        return unconditioned_pairs(field, grams)


#: The core's construction, the one setting of a probe-free receiver.
UNCONDITIONED: Final[SettingConstruction] = _Unconditioned()


def conditioning_present() -> bool:
    """Return whether the submodule of :data:`CONDITIONING_MODULE` is installed."""
    return importlib.util.find_spec(CONDITIONING_MODULE) is not None


def check_setting_construction(source_dimension: int) -> Refusal | None:
    """Refuse a receiver with source modes where no submodule constructs it.

    The receiver's ``fail_closed`` convention: a declaration the engine cannot
    construct is refused with a reason that names what is missing. A receiver
    without source modes is the core's (Cor. ``cor:unconditioned-family``) and
    is never refused here.
    """
    if source_dimension == 0 or conditioning_present():
        return None
    return Refusal(
        RefusalReason.PROBE_CONDITIONING_SUBMODULE_ABSENT,
        f"the receiver declares {source_dimension} source mode(s), so its "
        "setting family is conditioned on the declared probe states, and the "
        "probe-conditioning submodule that constructs it is not part of this "
        "installation; only a receiver without source modes (Inp_S empty, "
        f"T = {{{OFF_SETTING}}}) is admitted",
    )


def setting_construction(source_dimension: int) -> SettingConstruction:
    """Return the construction of a receiver's setting family -- THE SEAM.

    :data:`UNCONDITIONED` where ``Inp_S`` is empty; the probe-conditioning
    submodule's construction otherwise, loaded by name. Validation refuses a
    receiver with source modes where the submodule is absent
    (:func:`check_setting_construction`), so a caller holding a validated
    request never reaches the error below.

    Raises:
        HypothesisError: if the receiver has source modes and the submodule is
            not installed.
    """
    if source_dimension == 0:
        return UNCONDITIONED
    if not conditioning_present():
        raise HypothesisError(
            "a receiver with source modes needs the probe-conditioning "
            f"submodule ({CONDITIONING_MODULE}), which is not installed; "
            "validation refuses it as probe_conditioning_submodule_absent"
        )
    module = importlib.import_module(CONDITIONING_MODULE)
    return cast(SettingConstruction, module.CONSTRUCTION)


def predicate_x_holds(
    declaration: ProbeDeclaration, label: str, source_dimension: int
) -> bool:
    """Return predicate (X) of Definition ``def:pmc`` at one setting.

    Remark ``rem:flag-instances``: (X) is the setting's exact flag
    (Definition ``def:setting-family`` (c)), set by the construction that
    produced the setting and read off the declaration alone, WITHOUT
    COMPUTING A GRAM, A DETERMINANT OR AN EIGENVALUE, which is what makes the
    window requirement decidable at input validation
    (Requirement ``req:window-declaration``). At the one setting of a
    probe-free receiver it is set (Cor. ``cor:unconditioned-family``); at a
    setting a submodule constructs, that submodule states where.

    (X) is SUFFICIENT, NOT NECESSARY. A setting whose prefactors are one in
    fact but not by construction fails (X) and is served by branch 2; Remark
    ``rem:pmc-branch-choice``: "That is conservative, and Lemma lem:windowtail
    (i) makes it sound." Nothing here widens the predicate to catch it.
    """
    construction = setting_construction(source_dimension)
    return construction.exact_flag(declaration.setting(label))
