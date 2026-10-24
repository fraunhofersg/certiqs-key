"""Lowering a ``wcp_decoy`` source: the tagged weak-coherent-pulse declaration.

WHAT THIS MODULE DOES AND WHAT THE LIBRARY DOES. The document's ``wcp_decoy``
block declares the source as data -- the polarisations with their
parts and attributes, the intensity set, what a generation round and a test
round send, the test coin. This module reads that block at one
configuration's values (each scalar through the value language, each size
against :mod:`.limits`) and hands the values to the library's preparation,
:func:`instances.common.wcp.prepare_source`, which runs the sequence the
decoy instance ran, step for step:

1. the coin, the test intensities and the categories, with
   ``prepare_probabilities`` (sites ``<record_site>.test_coin``,
   ``.test_intensities``, ``.source_category_lattice``);
2. each ``mu`` read as ``Fraction(float(exact_input(mu)))``, the binary64
   value its declaration denotes;
3. the Poisson enclosures, with ``prepare_bound`` (sites
   ``<record_site>.poisson.<intensity>.<n>``);
4. ``WcpModel`` and ``TaggedSourceDeclaration``.

It then builds each letter's alphabet entry from its polarisation's attributes
and its fields. The caller emits the declaration through
``transmitter.decoy.emit_decoy_declaration`` and reads its refusal as
``source_refused``. For the decoy template every step is the decoy instance's
own, so its record is the instance's record (the equivalence gate).

``poisson_enclosures`` is the transmitter's
(``certiqs_key.transmitter.decoy.enclosure``, ``lem:poisson-enclosure``): the
emission forms the enclosure that the weight inequality (T2) is decided
against itself, and the preparation declares each weight at or below its lower
end. A property test holds it against an 80-digit evaluation over the widened
domain a document reaches (``tests/property/test_declared_poisson_enclosures.py``).

THE WRAPPED CALL SITE. The library's
:class:`~instances.common.wcp.WcpSourceError` -- one test probability per
intensity, the entropy cutoff's range, a lost positive support, a negative
intensity, the domain of ``poisson_enclosures`` -- is re-raised as
``DocumentError(wcp_source_invalid)`` with the original message, at the
field it names, here and nowhere else.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from certiqs_key.transmitter.certificate import RetentionAttestation
from certiqs_key.transmitter.decoy import FlagFamily, TaggedSourceDeclaration
from instances.common.wcp import (
    PreparedSource,
    WcpSourceError,
    check_cutoffs,
    prepare_source,
)
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.limits import (
    MAX_INTENSITY,
    MAX_SOURCE_CUTOFF,
    MAX_SOURCE_LABELS,
    check_size,
)
from instances.declared.model import WcpDecoy
from instances.declared.rules import Entry, placeholders, render
from instances.declared.values import Environment, number

__all__ = ["LoweredWcp", "lower_wcp"]

#: The names a ``letter_label`` template may read.
LETTER_FIELDS: tuple[str, ...] = ("round", "intensity", "polarisation")


@dataclass(frozen=True)
class LoweredWcp:
    """The library's prepared source and the letters' alphabet entries."""

    prepared: PreparedSource
    entries: tuple[Entry, ...]

    @property
    def tagged(self) -> TaggedSourceDeclaration:
        """The tagged declaration, before emission."""
        return self.prepared.tagged

    @property
    def record(self) -> Mapping[str, Any]:
        """The source's preparation record."""
        return self.prepared.record


def _invalid(detail: str, path: str) -> DocumentError:
    return DocumentError(detail, reason=DocumentReason.WCP_SOURCE_INVALID, path=path)


def _integer(node: object, environment: Environment, path: str) -> int:
    value = Fraction(number(node, environment, path))
    if value.denominator != 1:
        raise DocumentError(
            f"an integer is required here; the value is {value}",
            reason=DocumentReason.EXPRESSION_NOT_INTEGRAL,
            path=path,
        )
    return int(value)


def lower_wcp(
    source: WcpDecoy,
    environment: Environment,
    *,
    tolerance: float,
    site: str,
    instance: str,
    attestation: RetentionAttestation | None,
) -> LoweredWcp:
    """Prepare the tagged WCP declaration a ``wcp_decoy`` block declares.

    ``site`` prefixes every preparation record's site and ``instance`` is the
    record's ``instance`` string.
    """
    path = "/source"
    names = tuple(intensity.name for intensity in source.intensities)
    labels = tuple(polarisation.label for polarisation in source.polarisations)
    check_size(len(names), MAX_SOURCE_LABELS, "the number of intensities", path)
    check_size(len(labels), MAX_SOURCE_LABELS, "the number of polarisations", path)
    unknown = sorted(set(placeholders(source.letter_label)) - set(LETTER_FIELDS))
    if unknown:
        raise DocumentError(
            f"the letter label {source.letter_label!r} reads {unknown}; it may read "
            f"{list(LETTER_FIELDS)}",
            reason=DocumentReason.RULE_REFERENCE_UNKNOWN,
            path=path + "/letter_label",
        )
    probabilities = source.test.intensity_probabilities
    if not names or set(probabilities) != set(names) or len(set(names)) != len(names):
        # prepare_source: "one test probability is required per intensity".
        raise _invalid(
            "one test probability is required per intensity: the intensities are "
            f"{list(names)}, the test probabilities name {sorted(probabilities)}",
            path + "/test/intensity_probabilities",
        )
    entropy_cutoff = _integer(
        source.entropy_cutoff, environment, path + "/entropy_cutoff"
    )
    source_cutoff = _integer(source.source_cutoff, environment, path + "/source_cutoff")
    check_size(
        source_cutoff, MAX_SOURCE_CUTOFF, "the source cutoff", path + "/source_cutoff"
    )
    try:
        check_cutoffs(entropy_cutoff, source_cutoff)
    except WcpSourceError as failure:
        raise _invalid(str(failure), path + failure.field) from failure
    gamma = number(source.test.coin, environment, path + "/test/coin")
    tests_written = [
        number(
            probabilities[name],
            environment,
            path + pointer("test", "intensity_probabilities", name),
        )
        for name in names
    ]
    written_mu = {
        intensity.name: number(
            intensity.mu, environment, path + pointer("intensities", i, "mu")
        )
        for i, intensity in enumerate(source.intensities)
    }
    for i, (name, mu) in enumerate(written_mu.items()):
        check_size(
            max(0, math.ceil(Fraction(mu))),
            MAX_INTENSITY,
            f"the intensity {name!r}",
            path + pointer("intensities", i, "mu"),
        )
    parts = {
        polarisation.label: polarisation.part for polarisation in source.polarisations
    }
    attributes = {
        polarisation.label: dict(polarisation.attrs)
        for polarisation in source.polarisations
    }
    try:
        prepared = prepare_source(
            polarisations=parts,
            intensities=written_mu,
            test_probabilities=tests_written,
            coin=gamma,
            generation_intensity=source.generation.intensity,
            generation_polarisations=tuple(source.generation.polarisations),
            test_polarisations=tuple(source.test.polarisations),
            entropy_cutoff=entropy_cutoff,
            source_cutoff=source_cutoff,
            lattice_exponent=source.lattice_exponent,
            flag_family=FlagFamily(source.flag_family),
            attestation=attestation,
            letter_label=lambda fields: render(source.letter_label, fields.get),
            tolerance=tolerance,
            site=site,
            instance=instance,
        )
    except WcpSourceError as failure:
        raise _invalid(str(failure), path + failure.field) from failure
    entries = tuple(
        Entry.of(
            letter.label,
            {**attributes.get(letter.fields["polarisation"], {}), **letter.fields},
        )
        for letter in prepared.letters
    )
    return LoweredWcp(prepared=prepared, entries=entries)
