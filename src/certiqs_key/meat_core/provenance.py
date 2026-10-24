"""Whether a declaration is the protocol compiler's emission: the in-memory token.

WHY THIS EXISTS. ``req:compiled-declaration-only``: "The engine reports a key
length ... only on a declaration that the protocol compiler emitted; on any
other declaration it reports none." On a compiled declaration the compiler has
decided condition (vii) of ``def:admissible-declaration``, the non-empty
feasible set
(``protocol-compiler/thm:feasibility``), and filled the declaration from a
specification whose agreement with the apparatus is the compiler's own
assumptions; on a hand-built one neither holds, and no code path of this
module decides (vii) exactly where constraints are declared.

HOW THE ENGINE KNOWS. The wire and
the bundle format are unchanged: nothing on disk says where a declaration came
from, and :class:`~certiqs_key.domain.bundle.OperatorBundleManifest`'s
``created_by`` is a free string. Instead the run tier, which holds the
compilation, passes a :class:`CompilerEmission` beside the bundle it solves.
The token lives in memory only, so it survives the pipeline's write and
re-read of the bundle by never touching the bundle. Without it the engine
WITHHOLDS the key length: the run is not refused and every other number is
reported, and ``key_length_reason`` starts with
:data:`~certiqs_key.meat_core.reasons.DECLARATION_NOT_COMPILED` and says why.

WHAT THE TOKEN IS NOT. It is no proof and no signature: git and human review
are the ledger, and a caller that constructs one by hand asserts what the
run tier asserts, that the declaration is the compiler's emission (the tests
that stand for compiled output do exactly this). It is minted on the real
path by :func:`certiqs_key.meat_core.docking.compiler_emission`, the one file
of this package that reads the compiler's type.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["CompilerEmission"]


@dataclass(frozen=True)
class CompilerEmission:
    """The run tier's word that the declaration it solves is the compiler's emission.

    ``emitted_by`` names what vouches: on the run tier's path the compiler's
    ``mathematical_spec_version`` (``protocol-compiler@<version>``); in a test,
    the fixture that stands for compiled output. It is read by nothing but
    ``__post_init__`` and decides no number.
    """

    emitted_by: str

    def __post_init__(self) -> None:
        """Refuse a token that names nothing."""
        if not str(self.emitted_by).strip():
            raise ValueError(
                "a CompilerEmission names what vouches for the declaration "
                "(req:compiled-declaration-only); got an empty emitted_by"
            )
