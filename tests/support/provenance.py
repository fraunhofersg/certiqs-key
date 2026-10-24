"""The provenance token a test passes where its declaration stands for compiled output.

``meat-core/req:compiled-declaration-only``: the engine reports a key length
only on a declaration the protocol compiler emitted, and knows it by an
in-memory token the run tier passes
(:class:`~certiqs_key.meat_core.provenance.CompilerEmission`). A test that
builds its declaration by hand and exercises the MATHEMATICS of a key length
passes :data:`COMPILED`, which says in its own words that it stands for the
compiler's emission; a test of the provenance gate itself passes nothing and
asserts the withheld length. No number depends on which: the token decides
whether a length is reported, never its value.
"""

from __future__ import annotations

from certiqs_key.meat_core.provenance import CompilerEmission

COMPILED = CompilerEmission(
    emitted_by=(
        "a test fixture standing for the protocol compiler's emission "
        "(tests/support/provenance.py)"
    )
)
