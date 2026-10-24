"""The refusals of the protocol-document format, as one closed vocabulary.

WHY A VOCABULARY OF ITS OWN. A protocol document can fail in ways no Python
instance can: its text does not parse, a key is misspelt, a reference names a
parameter that is not declared, an expression does not parse. Those failures
are about the DOCUMENT, and they are coded here, in the instance tier that owns
the format, rather than in :class:`~certiqs_key.runs.errors.RunInputReason`:
putting them there would make ``runs/`` own a vocabulary of a format it never
reads.

WHAT IS NOT HERE. A refusal of a PROTOCOL is never a document refusal. A
configuration value outside its domain is ``check_keys``' own
:class:`~certiqs_key.runs.errors.RunInputError`; a module that refuses what a
document declares returns its own refusal as data. The document layer refuses
only what has no meaning as a document.

:class:`DocumentError` is a :class:`~certiqs_key.runs.errors.RunError`, so the
facade reads its ``reason`` as it reads any run error's, and a
:class:`ValueError`, so ``except ValueError`` still catches it.
"""

from __future__ import annotations

from enum import StrEnum

from certiqs_key.runs.errors import RunError

__all__ = ["DocumentError", "DocumentReason", "pointer"]


class DocumentReason(StrEnum):
    """Why a protocol document was refused: the closed vocabulary."""

    # Reading the document.
    DOCUMENT_UNREADABLE = "document_unreadable"
    DOCUMENT_SCHEMA_VIOLATION = "document_schema_violation"
    FORMAT_VERSION_UNSUPPORTED = "format_version_unsupported"
    #: An alphabet, a rule table or a dimension past :mod:`.limits`' bounds:
    #: work a short document asks for that no tool call can wait for.
    DOCUMENT_TOO_LARGE = "document_too_large"
    # The value language.
    UNKNOWN_PARAMETER_REFERENCE = "unknown_parameter_reference"
    EXPRESSION_INVALID = "expression_invalid"
    EXPRESSION_DIVISION_BY_ZERO = "expression_division_by_zero"
    EXPRESSION_NOT_INTEGRAL = "expression_not_integral"
    VALUE_KIND_MISMATCH = "value_kind_mismatch"
    SWITCH_CASE_MISSING = "switch_case_missing"
    # The rule language.
    ALPHABET_LABELS_NOT_DISTINCT = "alphabet_labels_not_distinct"
    RULE_REFERENCE_UNKNOWN = "rule_reference_unknown"
    RULE_VALUE_INVALID = "rule_value_invalid"
    # Matrices.
    MATRIX_MALFORMED = "matrix_malformed"
    # Stations.
    STATION_REFERENCE_UNKNOWN = "station_reference_unknown"
    STATION_KINDS_MIXED = "station_kinds_mixed"
    #: A ``wcp_decoy`` source beside ``declared_povm`` stations: the Band-A
    #: lowering docks no source segment, so the source needs optical stations.
    WCP_DECOY_NEEDS_OPTICAL_STATIONS = "wcp_decoy_needs_optical_stations"
    #: A ``wcp_decoy`` source beside two or more optical stations: only the
    #: one-station optical lowering docks the source segment.
    WCP_DECOY_NEEDS_ONE_OPTICAL_STATION = "wcp_decoy_needs_one_optical_station"
    # The honest-model library.
    LIBRARY_MODEL_UNKNOWN = "library_model_unknown"
    LIBRARY_MODEL_BINDING_INVALID = "library_model_binding_invalid"
    HONEST_MODEL_FAILED = "honest_model_failed"
    #: A raw honest table with a negative entry.
    HONEST_TABLE_INVALID = "honest_table_invalid"
    # Constraints.
    USER_ENTRIES_WITHOUT_LICENCE = "user_entries_without_licence"
    # Identity and topology.
    RESERVED_IDENTITY = "reserved_identity"
    UNSUPPORTED_TOPOLOGY = "unsupported_topology"
    # Wrapped call sites of module code.
    WCP_SOURCE_INVALID = "wcp_source_invalid"
    FACTOR_ASSEMBLY_REFUSED = "factor_assembly_refused"
    CHOICE_WEIGHTING_REFUSED = "choice_weighting_refused"
    # The transmitter.
    SOURCE_REFUSED = "source_refused"
    #: The lowering found its own prediction contradicted by a module's
    #: emission (a station's outcome alphabet): a defect of the lowering,
    #: refused with a code rather than raised as a bare assertion.
    LOWERING_INCONSISTENT = "lowering_inconsistent"


class DocumentError(RunError, ValueError):
    """A protocol document was refused; :attr:`reason` says why, :attr:`path` where.

    ``path`` is a JSON pointer into the document's canonical tree (``""`` for
    the whole document). ``module_reason`` carries a module's own refusal code
    where one was wrapped (``source_refused`` and the wrapped call sites).
    ``str(error)`` is the human message, prefixed with the path.
    """

    def __init__(
        self,
        detail: str,
        *,
        reason: DocumentReason,
        path: str = "",
        module_reason: str | None = None,
    ) -> None:
        """Keep the machine-readable code and the location beside the message."""
        message = f"{path}: {detail}" if path else detail
        super().__init__(message)
        #: The machine-readable code, a member of the closed vocabulary.
        self.reason: DocumentReason = DocumentReason(reason)
        #: Where in the canonical tree, as a JSON pointer.
        self.path = path
        #: The human sentence, without the path.
        self.detail = detail
        #: A module's own reason, where its refusal was wrapped.
        self.module_reason = module_reason
        #: The full human message.
        self.message = message

    def __str__(self) -> str:
        """Return the human message."""
        return self.message

    def as_payload(self) -> dict[str, str | None]:
        """Return the refusal as JSON, the shape a consumer reports."""
        return {
            "reason": str(self.reason),
            "path": self.path,
            "detail": self.detail,
            "module_reason": self.module_reason,
        }


def pointer(*parts: str | int) -> str:
    """Return the JSON pointer (RFC 6901) of a sequence of keys and indices."""
    return "".join(
        "/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )
