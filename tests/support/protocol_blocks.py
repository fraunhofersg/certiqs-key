"""Fixture helpers: dense literals to the block lists the module now carries.

`protocol-compiler` 0.3.0 types every ``Q``-operator as its list of sector
blocks (contract Definition ``def:declaration``), so that
sector-block-diagonality "HOLDS BY CONSTRUCTION; nothing verifies that the
off-sector entries are zero, BECAUSE NOTHING CAN WRITE THEM" (Section 2.5,
``operator_form``).

THE FROZEN ORACLE REGISTRY PREDATES THAT TYPE and carries its ``Q``-operators
as ``d_Q x d_Q`` arrays, which is correct evidence written against the 0.1.3
text and is under the two-instance freeze -- not one value of it may be edited.
So the adaptation happens HERE, in the fixture layer, and it is deliberately
NOT a function of the module: :func:`split` REFUSES an array with a non-zero
off-sector entry rather than truncating it, so no test can accidentally feed
the module an operator whose block list is not the operator it wrote down.

A registry case whose whole content IS a non-block-diagonal operator has no
image under this function, and that is the right answer: its subject is
superseded by scope at 0.3.0 (``SUPERSEDED_BY_SCOPE_0_3_0``,
``VALIDATOR_CASES/V3-block-diagonality``), because "an emitted Q-operator is a
block list, so there is NO ``Pi_s F_v Pi_{s'}`` ... TO EVALUATE and NOTHING
THAT COULD BE NON-ZERO".
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from certiqs_key.foundations.blocks import (
    BlockOperator,
    JointBlockOperator,
    Label,
    SectorStructure,
)
from certiqs_key.foundations.exact import Matrix
from certiqs_key.protocol_compiler.spec import (
    DirectPovm,
    PovmPresentation,
    SourcePart,
)
from certiqs_key.protocol_compiler.weights import weighted_family
from certiqs_key.transmitter.artifact import TransmitterArtifact
from certiqs_key.transmitter.certificate import (
    SourceReplacementCertificate,
    SourceReplacementLicense,
    verify_certificate,
)
from certiqs_key.transmitter.reasons import SourceMode

__all__ = [
    "as_blocks",
    "family_as_blocks",
    "joint_as_blocks",
    "source_part",
    "split",
]


class NotBlockDiagonalError(AssertionError):
    """A dense fixture that no block list against the given map denotes."""


def split(operator: Matrix, dims: tuple[int, ...]) -> tuple[Matrix, ...]:
    """Return the diagonal blocks of ``operator``, refusing any off-block mass.

    The refusal is the point: a truncation here would let a test assert
    something of an operator the module never saw.
    """
    total = sum(dims)
    if len(operator) != total:
        raise NotBlockDiagonalError(
            f"an operator of dimension {len(operator)} against a map of total "
            f"dimension {total}"
        )
    starts: list[int] = []
    running = 0
    for dim in dims:
        starts.append(running)
        running += dim
    for row in range(total):
        for column in range(total):
            same = _sector_of(row, dims) == _sector_of(column, dims)
            if not same and not operator[row][column].is_zero:
                raise NotBlockDiagonalError(
                    f"the dense fixture has a non-zero entry at "
                    f"({row}, {column}), which lies off every sector block; no "
                    "block list against this map denotes it"
                )
    return tuple(
        tuple(
            tuple(operator[start + i][start + j] for j in range(dim))
            for i in range(dim)
        )
        for start, dim in zip(starts, dims, strict=True)
    )


def _sector_of(index: int, dims: tuple[int, ...]) -> int:
    start = 0
    for sector, dim in enumerate(dims):
        if start <= index < start + dim:
            return sector
        start += dim
    raise NotBlockDiagonalError("index outside the declared decomposition")


def as_blocks(sector_map: SectorStructure, operator: Matrix) -> BlockOperator:
    """Return the block list a dense fixture on ``Q`` denotes."""
    return BlockOperator.of(sector_map, split(operator, sector_map.dims))


def family_as_blocks(
    sector_map: SectorStructure, family: Mapping[Label, Matrix]
) -> dict[Label, BlockOperator]:
    """Return one block list per member of a dense fixture family."""
    return {
        label: as_blocks(sector_map, operator) for label, operator in family.items()
    }


def joint_as_blocks(
    sector_map: SectorStructure, alice_dim: int, operator: Matrix
) -> JointBlockOperator:
    """Return the block list on ``A Q`` a dense fixture denotes.

    The ``A``-first factor order of Section 2.5 (``subsystem_order``): the
    ``s``-block occupies the rows and columns ``A`` indexes within the ``s``-th
    sector, and every entry outside those blocks must be zero.
    """
    dims = sector_map.dims
    q_total = sector_map.total_dim
    starts: list[int] = []
    running = 0
    for dim in dims:
        starts.append(running)
        running += dim

    def sector_of(index: int) -> int:
        return _sector_of(index % q_total, dims)

    total = alice_dim * q_total
    if len(operator) != total:
        raise NotBlockDiagonalError(
            f"a joint operator of dimension {len(operator)} against d_A d_Q = {total}"
        )
    for row in range(total):
        for column in range(total):
            if sector_of(row) == sector_of(column):
                continue
            if not operator[row][column].is_zero:
                raise NotBlockDiagonalError(
                    f"the dense joint fixture has a non-zero entry at "
                    f"({row}, {column}), which lies off every A Q_s block"
                )
    blocks: list[Matrix] = []
    for position, dim in enumerate(dims):
        start = starts[position]
        rows = [
            tuple(
                operator[a1 * q_total + start + s1][a2 * q_total + start + s2]
                for a2 in range(alice_dim)
                for s2 in range(dim)
            )
            for a1 in range(alice_dim)
            for s1 in range(dim)
        ]
        blocks.append(tuple(rows))
    return JointBlockOperator.of(sector_map, alice_dim, blocks)


def source_part(
    *,
    alphabet: tuple[Label, ...],
    alice_dim: int,
    alice_povm: PovmPresentation,
    transmitted_dim: int,
    signal_weights: Mapping[Label, Fraction],
    signal_states: Mapping[Label, Matrix],
    certificate: SourceReplacementCertificate | None = None,
    source_mode: SourceMode = SourceMode.UNTRUSTED,
    marginal_slot_filled: bool = False,
) -> SourcePart:
    """Return a ``SourcePart`` from SIX FIELDS.

    WHY A FIXTURE HELPER EXISTS FOR THIS AT ALL. The compiler's
    ``SourcePart`` is A THIN READER of
    :class:`~certiqs_key.transmitter.artifact.TransmitterArtifact`
    (``def:spec`` (a)), so a fixture that writes six fields has to build an
    artefact. The conversion is mechanical, so it is written ONCE here instead
    of at every call site.

    IT BUILDS THE ARTEFACT AS A FROZEN RECORD AND DOES NOT CALL
    ``emit_artifact``. The transmitter's decision path is exercised by the
    transmitter's own tests; several fixtures here declare data a transmitter
    would refuse (a failing certificate, in particular) precisely so that the
    COMPILER's gate (G2) can refuse it, which is the behaviour row 3 of the
    gate outcome table fixes. Routing them through the transmitter would move
    the refusal one module upstream and delete the case.

    ALICE'S FAMILY IS CONSTRUCTED HERE AND DECIDED IN THE COMPILER, which is
    the seam ``SourcePart.alice_choices`` exists for: the artefact carries the
    weighted ``{M_x}`` and the choice record travels beside it, so that
    ``def:weighted``'s emission decision is taken on the compilation path where
    its refusal is DATA. :func:`weighted_family` constructs and decides
    nothing; ``resolve_povm`` would decide, and deciding here would turn a
    frozen refusal case into an exception.
    """
    presented = alice_povm
    emitted = (
        presented
        if isinstance(presented, DirectPovm)
        else weighted_family(presented)
    )
    licence: SourceReplacementLicense | None = None
    marginal: Matrix | None = None
    if certificate is not None:
        marginal = certificate.alice_marginal
        licence = SourceReplacementLicense.pass_through(
            verify_certificate(certificate, emitted.alphabet, dict(emitted.elements)),
            certificate.retention_attestation,
            certificate,
        )
    elif source_mode is SourceMode.TRUSTED:
        raise AssertionError(
            "a trusted artefact carries a marginal, and at d_A >= 2 a licence "
            "record: the transmitter refuses the alternative with "
            "`trusted_mode_without_certificate`"
        )
    virtual_dim = transmitted_dim if certificate is None else certificate.virtual_dim
    virtual_weights = dict(
        signal_weights if certificate is None else certificate.virtual_weights
    )
    virtual_states = dict(
        signal_states if certificate is None else certificate.virtual_states
    )
    ledger = ["source_ensemble", "sequential_round_model"]
    if licence is not None and alice_dim >= 2:
        ledger.append("source_replacement_license")
    return SourcePart(
        alice_choices=None if isinstance(presented, DirectPovm) else presented,
        artifact=TransmitterArtifact(
            signal_alphabet=tuple(alphabet),
            alice_dim=alice_dim,
            alice_marginal=marginal,
            alice_povm=dict(emitted.elements),
            virtual_transmitted_system=virtual_dim,
            virtual_ensemble_weights=virtual_weights,
            virtual_ensemble_states=virtual_states,
            source_segment=(),
            source_replacement_license=(licence if alice_dim >= 2 else None),
            marginal_slot_filled=marginal_slot_filled,
            assumption_ledger=tuple(ledger),
        )
    )
