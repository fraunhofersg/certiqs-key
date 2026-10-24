"""The protocol document: an instance written as data.

WHY. A custom protocol specification should be possible, or there is little
point in people using the engine. A user -- often
an agent through the MCP server -- writes a protocol as a declarative document
(JSON or YAML), and this package turns it into the uniform instance surface the
run tier already drives. The format guide an agent reads is ``README.md``
beside this file, and the schema
``protocol-document.schema.json`` is generated from :mod:`.model`.

THE ONE RULE. The document layer constructs the arguments of the modules'
existing public constructors and nothing else. Every decision about a protocol
is taken by the engine's existing validators; this package refuses only what
has no meaning as a document (:mod:`.errors`).

The modules, in reading order: :mod:`.errors` (the refusal vocabulary),
:mod:`.model` (the shape), :mod:`.reader` (the canonical tree and its digest),
:mod:`.values` (the value language), :mod:`.rules` (the rule language),
:mod:`.lowering` (one configuration's lowering to the modules' constructors),
:mod:`.surface` (the instance surface) and :mod:`.schema` (the generated
schema). The lowering covers Band-A documents, optical stations
(:mod:`.optical`), the ``wcp_decoy`` source (:mod:`.wcp`), transcripts, several
stations and the library witnesses (``instances/common/witness.py``);
:mod:`.lowering` is a package of one module per block.
"""

from __future__ import annotations

from instances.declared.errors import DocumentError, DocumentReason
from instances.declared.surface import (
    DocumentSurface,
    load,
    load_canonical,
    load_packaged,
)

__all__ = [
    "DocumentError",
    "DocumentReason",
    "DocumentSurface",
    "load",
    "load_canonical",
    "load_packaged",
]
