"""``domain``: the shared format every module may import.

Imports point downward only (PRINCIPLES.md section 4). A module may import this
package, and it imports no module package except :mod:`certiqs_key.foundations`,
the floor below it: the sector-block operator form, the exact substrate and the
two hard errors it reads are that package's (``foundations.blocks``,
``foundations.exact``, ``foundations.errors``).

WHAT LIVES ELSEWHERE
====================
``assurance``, ``errors``, ``exact``, ``exact_admission``, ``blocks``,
``numeric`` and ``snap`` are the ``foundations`` module's and live in
:mod:`certiqs_key.foundations`. What this package holds is the format those
types are carried in:

``constraints``, ``chain``
    the frozen wire records a reduction chain is carried in -- the constraint
    entry and its licence, the link and the two segments -- over the
    sector-block operator form of ``foundations.blocks``. They live here so that
    no module imports the protocol compiler, and
    :mod:`certiqs_key.protocol_compiler` reads them from here rather than
    declaring any of them a second time.
``families``
    ``{F_v}`` of several measuring parties as ONE FAMILY PER MEASURED FACTOR
    plus the product rule, never a product datum. Every exact predicate runs per factor
    with ``foundations.blocks``'s own functions; the Kronecker block is formed only
    for a numerical consumer. One factor is today's family, entry for entry.

THE SHARED FORMAT
=================
The operator bundle of spec/architecture.md 4.1 (the measuring kernel of 2.9
is ``foundations.numeric``):

``_base``
    the format's floor: :class:`_base.StrictModel`, the frozen
    ``extra="forbid"`` model every manifest model is built on, and the bundle
    error hierarchy (``BundleError`` and its three refinements), beside the
    format's base model rather than with the module tier's two hard errors and
    their opposite posture (``foundations.errors``). See ``_base``'s own
    docstring.
``identifiers``, ``arrays``
    the stable identifiers every alphabet and HDF5 link name is drawn from,
    and the array descriptors, block-diagonal operator payload and in-memory
    dense/CSC arrays of 4.1.
``manifest``, ``validation``
    the ``manifest.json`` models -- envelope, alphabets, declaration,
    parameters, the carried reduction chain -- and the structural validation
    that decides a bundle well-formed AS DATA and stops exactly there: what
    the numbers mean is ``meat-core``'s.
``hdf5``, ``bundle``
    ``arrays.h5`` read and written in the layout a descriptor declares, and
    the directory of ``manifest.json`` + ``arrays.h5`` that is the whole of
    the file format. Nothing warns, repairs or defaults.
``announcements``, ``claim_closure``
    the transcript protocol of a declaration (an ordered list of public
    messages, (DX5)), and the claim-closure table (``claim_closure.json``,
    package data written by ``harness/generate_claim_closure.py``) a run record
    names its claim graph from.
``bindings``
    the declared values each ledger row's assumption is about, in the one
    immutable shape the bare-key emitters (the protocol compiler and the
    transmitter) carry beside their ledgers, and its one JSON form.

ONE BLOCKKIND
=============
The wire spelling of spec/architecture.md 4.1 and the in-memory spelling of
2.9 are ONE enum: ``foundations.blocks.BlockKind`` is the type and ``arrays``
imports it. ``runs/wire.py`` writes a compiled declaration's sector block kind
into the manifest and ``meat_core`` reads it back, so the two meet on every
run; one enum is the smaller design than a named conversion every meeting
point calls, and it makes a comparison by ``.value`` unnecessary.

``manifest.ReductionChain`` and ``chain.ReductionChain`` are NOT the same case
and stay two types. They never meet as two spellings of one in-memory value:
the compiler re-emits its chain record as JSON-ready data, ``runs/wire.py``
re-keys that mapping, and ``manifest.ReductionChain`` is the pydantic model
that parses it back off the disk. One is a wire schema and one is the
in-memory record of the same facts, related by a serialisation rather than by
a rename, so collapsing them would put a pydantic model inside the reduction
chain's own vocabulary. The overlap is named here and left.

The names are deliberately NOT re-exported from this namespace: a caller names
the module it reaches into, so that the import line says what it is doing.
"""

from __future__ import annotations

__all__: list[str] = []
