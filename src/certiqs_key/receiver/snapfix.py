"""The cause and fix recorded for a receiver block that rests on its snap.

Requirement ``req:snap-fix`` (detector-imperfections): when a moved
block of a snap of the receiver's emitted dark-composed blocks rests on
``foundations/ass:snapped-measurement`` under ``foundations/req:snap-reference``
(iii), its record names, beside the setting, the block with its cause and
group, the reference kind of the snap, the kind of the reference handed, and a
fix that says what to change IN THE RECEIVER DECLARATION. The snap and its
record are the declaring instance's (``foundations/req:who-snaps``); the
foundations record carries a generic fix per cause, and this module supplies
the receiver's, from what the receiver knows about its own declaration:

    item (i)     no reference           the reference cause of
                                        req:dark-composed-reference (iv), with
                                        the fix (a), (b) or (c)
    item (ii)    enclosure not used     the kind OFFERED per block with each
                                        enclosed block's largest radius, and the
                                        exact alternative
    last resort  support_not_preserved  the ports of declared efficiency 1 where
                                        lmax(A_Sigma) < 1 is not established; the
                                        click patterns S with R_{S|empty} = 0 (on
                                        the generated route: the ports whose
                                        dark-count probability is 0 or 1); a
                                        model with loss and dark counts; and the
                                        fix of (i) where no reference is offered

A reference failing the decisions of ``foundations/req:snap-reference`` (i)
cannot arise for the receiver (the requirement's last paragraph), so that
cause carries the foundations fix. The groups ``reference bracket withdrawn``
and ``reference bracket not evaluated`` are the run's, and carry the fixes
``foundations/req:snap-reference`` (iii) names.

Every decision this module reports -- whether ``lmax(A_Sigma) < 1`` is
established, which entries of ``R`` are zero -- is exact.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol

from certiqs_key.foundations.reference import ReferenceKind
from certiqs_key.foundations.resting import RestingCause
from certiqs_key.receiver.dark import DarkCountChannel, DarkCountRoute
from certiqs_key.receiver.reference import ReferenceCause, SettingReference
from certiqs_key.receiver.request import ValidatedRequest

__all__ = [
    "BlockRecord",
    "SnapFixContext",
    "SnapRecord",
    "receiver_fix",
    "receiver_fixes",
    "snap_fix_context",
]


class BlockRecord(Protocol):
    """What a fix reads of one block of a snap record.

    The block record of ``foundations/req:who-snaps`` as the declaring
    instance holds it, read STRUCTURALLY through this protocol.
    """

    @property
    def block(self) -> str:
        """The block label, ``m=n``."""
        ...

    @property
    def cause(self) -> RestingCause | None:
        """The cause of ``foundations/req:snap-reference`` (iii)(a), or ``None``."""
        ...

    @property
    def support_not_preserved(self) -> bool:
        """Whether the last resort snapped the block."""
        ...


class SnapRecord(Protocol):
    """What a fix reads of a snap record of one setting (structurally)."""

    @property
    def blocks(self) -> Sequence[BlockRecord]:
        """The record of every block."""
        ...


@dataclass(frozen=True)
class SnapFixContext:
    """What a fix reads about the receiver declaration at one setting.

    Everything is the declaration's or an exact decision on it.
    """

    setting: str
    reference: SettingReference
    port_labels: tuple[str, ...]
    efficiencies: tuple[Fraction, ...]
    dark_route: DarkCountRoute
    dark_probabilities: tuple[Fraction, ...]
    #: ``R_{S|empty}`` for every click pattern, keyed by sorted port labels.
    no_click_column: Mapping[tuple[str, ...], Fraction]
    photon_cutoff: int


def snap_fix_context(
    validated: ValidatedRequest,
    channel: DarkCountChannel,
    reference: SettingReference,
) -> SnapFixContext:
    """Return the context of the fixes at one setting, from the declaration."""
    request = validated.request
    labels = request.port_map.labels
    empty: frozenset[int] = frozenset()
    column = {
        tuple(labels[k] for k in sorted(pattern)): Fraction(
            channel.entry(pattern, empty)
        )
        for pattern in channel.patterns()
    }
    return SnapFixContext(
        setting=reference.setting,
        reference=reference,
        port_labels=labels,
        efficiencies=tuple(
            Fraction(port.efficiency) for port in request.detector_layer
        ),
        dark_route=channel.route,
        dark_probabilities=tuple(
            Fraction(port.dark_count_probability) for port in request.detector_layer
        ),
        no_click_column=column,
        photon_cutoff=request.photon_cutoff,
    )


def _radius_text(value: Fraction | None) -> str:
    return "none" if value is None else f"{float(value):.3e}"


def _no_reference_fix(context: SnapFixContext) -> str:
    """Item (i): the cause req:dark-composed-reference (iv) records, with its fix."""
    cause = context.reference.cause
    route = context.reference.exact_route
    if cause is ReferenceCause.NO_EXACT_MODEL:
        reason = route.cause.value if route.cause is not None else "no exact model"
        return (
            f"the receiver offers no reference: the declaration has no model "
            f"admissible exactly ({reason}: {route.detail}); declare data that are "
            "Hermitian and admissible exactly, in rational arithmetic and not "
            "only at the receiver tolerances (receiver/req:exact-route-decision "
            "(i), (ii))"
        )
    if cause is ReferenceCause.DARK_CHANNEL_NOT_EXACT:
        return (
            "the receiver offers no reference: the declared dark-count matrix "
            f"does not satisfy (D1) and (D2) exactly ({context.reference.detail}); "
            "declare one that is exactly column-stochastic and monotone, or use "
            "the generated dark-count route (per-port dark-count probabilities)"
        )
    if cause is ReferenceCause.RECIPROCAL_NOT_ENCLOSED:
        return (
            "the receiver offers no reference: a reciprocal that the enclosure "
            "of the conditioned setting family forms received no enclosure "
            "(receiver/detector-imperfections/req:dark-composed-reference (iv)); "
            "use square-root and angle enclosures with smaller radii "
            "(receiver/def:complex-enclosure)"
        )
    return (
        "the receiver offers a reference at this setting; pass it to the snap "
        "(receiver/detector-imperfections/req:dark-composed-reference (iii))"
    )


def _noise_fix(context: SnapFixContext) -> str:
    """Return the last-resort fix: lossless ports, zero entries of ``R``, noise."""
    parts: list[str] = []
    if context.reference.loss_established is not True:
        lossless = [
            label
            for label, efficiency in zip(
                context.port_labels, context.efficiencies, strict=True
            )
            if efficiency == 1
        ]
        if lossless:
            parts.append(
                "lmax(A_Sigma) < 1 is not established, and the ports "
                f"{lossless} declare efficiency 1: declare the loss each has"
            )
        else:
            parts.append(
                "lmax(A_Sigma) < 1 is not established: declare a loss that "
                "leaves lmax(A_Sigma) < 1"
            )
    if context.dark_route is DarkCountRoute.PER_PORT_PRODUCT_FORM:
        extreme = [
            label
            for label, value in zip(
                context.port_labels, context.dark_probabilities, strict=True
            )
            if value in (0, 1)
        ]
        if extreme:
            parts.append(
                f"the ports {extreme} declare a dark-count probability of 0 or 1; "
                "declare a dark-count probability in (0, 1) in every port "
                "(receiver/detector-imperfections/prop:noise-floor (ii))"
            )
    else:
        zero = [
            list(pattern)
            for pattern, value in context.no_click_column.items()
            if value == 0
        ]
        if zero:
            parts.append(
                f"the declared R has R_(S|empty) = 0 for the click patterns {zero}; "
                "declare an R with R_(S|empty) > 0 for every S "
                "(receiver/detector-imperfections/prop:noise-floor (i))"
            )
    parts.append(
        "model the loss and dark counts the device has, at the smallest rates "
        "you are sure of (receiver/detector-imperfections/prop:noise-floor)"
    )
    return "; ".join(parts)


def _enclosure_not_used_fix(context: SnapFixContext) -> str:
    """Item (ii): the kinds offered, and the exact alternative."""
    offered = ", ".join(
        f"{block.label}: {block.kind.value}"
        + (
            f" (largest radius {_radius_text(block.largest_radius)})"
            if block.kind is ReferenceKind.ENCLOSED
            else ""
        )
        for block in context.reference.offered
    )
    return (
        f"the run declares enclosed references not used, and the receiver "
        f"offers {offered}; the alternatives are an exact reference, which the "
        "receiver offers for a declaration on the exact route at a cutoff "
        "N <= 1 with its port Grams enclosed exactly (receiver/thm:exact-blocks "
        "(iii), receiver/detector-imperfections/cor:exact-dark-composed (ii)), "
        "or a run that uses enclosed references (run parameter "
        "reference_enclosure on)"
    )


def receiver_fix(context: SnapFixContext, record: BlockRecord) -> str | None:
    """Return the receiver's fix for one block of a snap record, or ``None``.

    Implements ``receiver/detector-imperfections/req:snap-fix``:
    the fix of items (i) and (ii) for the block's cause, and for a block the
    last resort snapped (``support_not_preserved``) the loss and dark counts
    the requirement names with, where the receiver offers no reference, the
    fix of item (i). A block with no cause and no flag has no fix (``None``).
    """
    cause = record.cause
    parts: list[str] = []
    if cause is RestingCause.NO_REFERENCE:
        parts.append(_no_reference_fix(context))
    elif cause is RestingCause.ENCLOSURE_NOT_USED:
        parts.append(_enclosure_not_used_fix(context))
    elif cause is not None:
        # A reference failing the decisions cannot arise for the receiver's
        # reference (req:snap-fix, last paragraph); the run's
        # causes carry the fixes foundations/req:snap-reference (iii) names.
        parts.append(cause.fix)
    if record.support_not_preserved:
        flag = (
            "the block was snapped by the last resort and is flagged "
            "support_not_preserved: " + _noise_fix(context)
        )
        if context.reference.cause is not None and (
            cause is not RestingCause.NO_REFERENCE
        ):
            flag += "; " + _no_reference_fix(context)
        parts.append(flag)
    if not parts:
        return None
    return "; ".join(parts)


def receiver_fixes(context: SnapFixContext, record: SnapRecord) -> dict[str, str]:
    """Return the receiver's fix for every block of a snap record that has one.

    Implements ``receiver/detector-imperfections/req:snap-fix``
    over the whole snap record of one setting (:class:`SnapRecord`, the
    measurement-family record of ``foundations/req:who-snaps``): keyed by
    block label, for the blocks with a cause or the ``support_not_preserved``
    flag. The declaring instance writes them into the snap's record beside
    the foundations fix.
    """
    fixes: dict[str, str] = {}
    for block in record.blocks:
        fix = receiver_fix(context, block)
        if fix is not None:
            fixes[block.block] = fix
    return fixes
