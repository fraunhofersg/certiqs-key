"""The base layer of the operator-bundle format: its model config and errors.

WHY THE BUNDLE ERRORS LIVE HERE. :mod:`certiqs_key.foundations.errors` has a
subject of its own -- the two hard errors every MODULE raises, where "almost
nothing is an error" and a failed rule is a refusal instead. The bundle
format's hierarchy is the opposite posture (spec/architecture.md 3.6: "a
bundle that does not validate produces no result at all"), so putting the two
in one file would put two rules about what an exception means under one
docstring. The format's errors therefore sit beside the format's base model,
which is the floor its other seven modules already import.

Pydantic sits at the wire boundary and nowhere else (spec/architecture.md 8).
Two settings of :class:`StrictModel` are load-bearing rather than stylistic:

``extra="forbid"``
    An unrecognised key is a hard error naming that key. This is how the
    deferred envelope fields of spec/architecture.md 4.1 -- ``artifact_id``,
    ``content_hash``, ``input_artifact_hashes``, ``provenance`` -- stay
    *omitted* rather than quietly accepted and ignored. 4.1 forbids giving a
    field a meaning incompatible with the one it will carry later; accepting
    one now and dropping it is precisely that.

``frozen=True``
    Artifacts crossing a module boundary are immutable
    (spec/architecture.md 2.1).

Every failure in the bundle format is one of the exceptions below. Nothing
there warns, repairs, or substitutes a default: spec/architecture.md 3.6
requires bundle failures to be hard errors, and 2.5 requires the input end to
fail closed exactly as the output end does. A bundle that does not load is no
bundle at all.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "BundleError",
    "BundleValidationError",
    "RetiredSchemaVersionError",
    "StrictModel",
    "UnsupportedArrayEncodingError",
]


class StrictModel(BaseModel):
    """An immutable model that rejects every key it does not declare."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class BundleError(Exception):
    """Base class for every operator-bundle failure."""


class BundleValidationError(BundleError):
    """A bundle is not well-formed or not self-consistent as data.

    The message always names the offending key by its path in the manifest,
    for example ``payload.declaration.bob_povm['v0']``.
    """


class UnsupportedArrayEncodingError(BundleValidationError):
    """An array uses an encoding this format forbids.

    Object arrays, pickled payloads, compound/opaque/variable-length HDF5
    dtypes, and NumPy complex dtypes written directly are all refused
    (spec/architecture.md 4.1).
    """


class RetiredSchemaVersionError(BundleValidationError):
    """The bundle is stamped a version this reader no longer reads.

    Read support for schema 0.1.0 and 0.2.0 is dropped
    (spec/architecture.md 2.9): those versions can express a full-space
    operator payload, and a reader that still accepts them keeps the removed
    form alive at the one boundary where it would matter.

    IT IS ITS OWN CLASS, AND CARRIES THE VERSION AS DATA, because the two
    failures a caller must tell apart look alike in prose: a bundle stamped a
    retired version was well-formed when it was written and its instance can
    regenerate it, whereas a bundle stamped an unknown version is a document
    nobody in this tree wrote. Nothing is converted in either case -- re-blocking
    a full-space operator would require inventing a sector map, which is a
    mathematical claim and not a format conversion.
    """

    def __init__(
        self,
        message: str,
        *,
        reason: str,
        declared_version: str,
        supported_versions: tuple[str, ...],
        retired_versions: tuple[str, ...],
    ) -> None:
        """Record the machine-readable half of the refusal beside its message."""
        super().__init__(message)
        #: The machine-readable reason code, ``"schema_version_retired"``.
        self.reason = reason
        #: The version the offending manifest stamped.
        self.declared_version = declared_version
        #: What this reader does accept.
        self.supported_versions = supported_versions
        #: The versions it names and refuses.
        self.retired_versions = retired_versions
