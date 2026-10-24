"""The claim graph a key rate rests on, read from a GENERATED table shipped here.

WHY THIS EXISTS. PRINCIPLES.md section 2.1: a result is a number plus a
machine-generated manifest of "the assumption IDs, module versions and claim
graph it rests on"; spec/architecture.md 4.4 names "the claim ids of the
theorem and its transitive ``uses`` closure". The claim files live in
``spec/``, which is not part of the installed distribution, and the closure is
computed by ``harness/check_claims.py``. So the closure a run can name is
computed in the checkout and SHIPPED AS PACKAGE DATA (``claim_closure.json``
beside this file), a generated table.

THE TABLE IS WRITTEN BY ``python -m harness.generate_claim_closure`` AND NEVER
BY HAND; ``--check`` fails when it is stale against the claim files, and
``tests/harness/test_generate_claim_closure.py`` runs that check on the tree.
Its shape::

    {
      "assumptions": {
        "<A-...>": {"machine_key": "<ledger key>",
                    "owner": "<owning assumption claim id>",
                    "verification": "never | partly",
                    "verification_sentence": "<the contract's generated sentence>",
                    "title": "<plain title>", "summary": "<plain text>",
                    "user_statement": "<plain text> | null",
                    "category": "<category> | null",
                    "presupposes": ["trusted-source" | "sends" | "setting"
                                    | "letters", ...],
                    "affects": ["secrecy", ...] | null,
                    "refines": "<A-...> | null",
                    "status": "<header status>",
                    "effective_status": "<status over its closure>",
                    "contract": {"pdf": "spec/modules/<core>/contract.pdf",
                                 "anchor": "claim-<owner>"},
                    "emission": {"<module>": "<its interface's emission rule>"}},
        ...
      },
      "category_order": ["source", "receiver", ...],
      "claims": {
        "<claim id>": {"kind": "thm", "kind_word": "Theorem",
                       "title": "...", "summary": "...",
                       "user_statement": "<plain text> | null",
                       "status": "...", "effective_status": "...",
                       "contract": {"pdf": "...", "anchor": "claim-<claim id>"}},
        ...
      },
      "generated_by": "python -m harness.generate_claim_closure",
      "limitations": ["<claim id>", ...],
      "module_versions": {"<module-id>": "<version>", ...},
      "roots": {
        "<root claim id>": {
          "claims": ["<root>", <its transitive uses closure, sorted>],
          "assumptions": {"<A-...>": "<owning assumption claim id>", ...}
        }
      }
    }

``claims`` is the root and every claim its ``uses`` reach; ``assumptions`` is
every short id an ``assumes`` of one of those claims declares, resolved to the
assumption claim file that owns it -- exactly what ``check_claims
--assumptions <root>`` lists. ``module_versions`` is every module's and
submodule's ``version`` from its ``module.yaml``: the accepted claim set a
version names. The top-level ``assumptions`` block is every assumption with
the machine key its owner's interface gives it and its ``verification``
header field (spec/claim-format.md section 3.2), which :func:`never_verified`
reads.

THE TEXT A KEY-RATE REPORT QUOTES IS CARRIED HERE TOO (the report is built
from one source, the claim headers). Each assumption also carries its plain title,
``summary``, ``user_statement``, ``category``, ``affects``, ``refines``, its header and
effective status, the contract anchor a renderer links to, the generated
verification sentence and each interface's emission rule for it (display
only, never parsed). Its ``presupposes`` lists the roles a run must have for the
assumption's text to hold, from the vocabulary ``ASSUMPTION_PRESUPPOSITIONS`` of
``harness/check_claims.py`` (spec/claim-format.md section 3), empty where the header
declares none; a run-tier guard reads it. ``claims`` carries the plain title, summary
and ``user_statement`` (``null`` where the claim has none; a claim of any kind
but a definition may carry one) for every root,
every limitation (:data:`LIMITATION_CLAIMS`), every cited claim
(:data:`CITED_CLAIMS`), every assumption owner and every claim a carried text
links to; every ``[[...]]`` link in a carried text is written as a full
target (``[[A-...]]`` or ``[[<module>/<kind>:<label>]]``), so a renderer
resolves it without knowing the contract that holds it, and every such target
is itself in the table. A run-tier copy of that text would drift from the
headers; this one is regenerated with them.

WHETHER A RUN RESTS ON AN ASSUMPTION UNVERIFIED IS READ HERE AND NOWHERE ELSE
(the assumption's ``verification`` header field). A mark stated by hand in
several places can disagree with itself. Every
module's never-verified constants and emitted flags, and the run record's
mark on every manifest row, are :func:`never_verified` of the row's machine
key; ``tests/unit/test_never_verified_agree.py`` holds every remaining place
that states a mark to the header field.

WHICH ROOTS. :data:`CLAIM_ROOTS` below is the one list of claims a key-rate
result may name as the claim its number is an instance of; the Frank-Wolfe
result imports its names from here and the generator reads the list from here,
so a root a result could name and a root the table covers are one declaration.
The table covers :data:`ALL_ROOTS`: those, the three properties a key length
rests on, every device module's emission results (:data:`DEVICE_ROOTS`),
the completeness results (:data:`COMPLETENESS_ROOTS`) and the result behind
the emitted acceptance support (:data:`ACCEPTANCE_ROOTS`), so a run can name
the closure of every result it actually used (the route-exact assumption set).

A MISSING ENTRY IS AN ERROR, not a gap in the manifest (4.4: "a manifest that
cannot be generated ... is an error that refuses the result, not a warning").
It can only mean the package data is stale or absent, which is a packaging
defect: :class:`ClaimClosureError`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import cache
from importlib import resources
from types import MappingProxyType
from typing import Any, Final

from certiqs_key.foundations.errors import CertiqsError

__all__ = [
    "ACCEPTANCE_ROOTS",
    "ALL_ROOTS",
    "CERTIFIED_REFERENCE_ROOT",
    "CERTIFIED_ROOT",
    "CITED_CLAIMS",
    "CLAIM_ROOTS",
    "COMPANION_ROOTS",
    "COMPLETENESS_ROOTS",
    "COMPOSITION_ROOTS",
    "CORRECTNESS_ROOTS",
    "DEVICE_ROOTS",
    "DROPPED_ROOT",
    "ESTIMATE_ROOT",
    "FIRST_ORDER_ROOT",
    "KEY_LENGTH_ROOT",
    "LIMITATION_CLAIMS",
    "REFERENCE_ROOT",
    "SECRECY_ROOTS",
    "TABLE_NAME",
    "VERIFICATIONS",
    "ClaimClosureError",
    "assumption_info",
    "category_order",
    "claim_closure",
    "claim_info",
    "closure_table",
    "limitations",
    "module_version",
    "never_verified",
    "roots_of_module",
    "short_id_of",
]

#: The ``estimate`` tier's claim: ``h_low`` bounds the true value from above.
ESTIMATE_ROOT: Final[str] = "meat-core/lem:estimate"
#: The key length computed from an entropy lower bound.
KEY_LENGTH_ROOT: Final[str] = "meat-core/cor:keylength-bound"
#: The ``first-order`` tier's lower bound ``h_lb``.
FIRST_ORDER_ROOT: Final[str] = "meat-core/frank-wolfe/thm:firstorder"
#: The ``first-order`` bound over a dropped set of key-inert pairs.
DROPPED_ROOT: Final[str] = "meat-core/frank-wolfe/cor:fo-dropped"
#: The ``first-order`` bound formed on the reference companion at the points of
#: the search on the snapped declaration (the direct route,
#: ``frank-wolfe/req:bracket-on-reference``). Its closure holds the companion's
#: admission (``meat-core/prop:reference-companion``) and the reductions'
#: ``cor:reference-companion`` with its conditional A-SNAP.
REFERENCE_ROOT: Final[str] = "meat-core/frank-wolfe/cor:fo-reference"
#: The ``certified`` tier's key length, from the certified number formed at the
#: run's final points (``frank-wolfe/req:certified-evaluation``). Named on every
#: result reported at that tier: its closure is the first-order key length's
#: (``frank-wolfe/cor:fo-keylength``).
CERTIFIED_ROOT: Final[str] = "meat-core/frank-wolfe/cor:certified-keylength"
#: The ``certified`` tier's key length where the certified number is formed on
#: the reference companion: it carries the conclusion over to the protocol the
#: companion declares, as :data:`REFERENCE_ROOT` does for the first-order
#: bound, and its closure is that root's. Named beside :data:`CERTIFIED_ROOT`
#: on the reference route.
CERTIFIED_REFERENCE_ROOT: Final[str] = (
    "meat-core/frank-wolfe/cor:certified-keylength-reference"
)

#: Every claim a key-rate result may name in ``claim_roots``.
CLAIM_ROOTS: Final[tuple[str, ...]] = (
    ESTIMATE_ROOT,
    KEY_LENGTH_ROOT,
    FIRST_ORDER_ROOT,
    DROPPED_ROOT,
    REFERENCE_ROOT,
    CERTIFIED_ROOT,
    CERTIFIED_REFERENCE_ROOT,
)

#: THE THREE PROPERTIES A KEY LENGTH RESTS ON, each named by the claim that
#: states it: secrecy, correctness and their composition with the
#: authentication scheme. An assumption in the closure of a secrecy or a
#: correctness root lists that property in ``affects``, and one in the
#: composition root's closure lists at least one of the two; the converse is
#: not required, since a device premise reaches the key length through the
#: run's route rather than through claim edges. ``harness/check_claims``
#: reads these tuples and checks that direction. They are not result roots: a run
#: names ``KEY_LENGTH_ROOT``, whose closure reaches all three.
SECRECY_ROOTS: Final[tuple[str, ...]] = ("meat-core/thm:keylength",)
CORRECTNESS_ROOTS: Final[tuple[str, ...]] = ("meat-core/lem:ev-correctness",)
COMPOSITION_ROOTS: Final[tuple[str, ...]] = ("meat-core/cor:composed-security",)

#: THE EMISSION RESULTS OF THE DEVICE-SIDE MODULES, per module: the results
#: whose emitted artefact a key-rate run consumes, so that the run can name
#: the closure of the ones its route used (the route-exact set). WHICH OF THEM A GIVEN
#: RUN USED is chosen in the run tier, per route; this is only the set the table covers.
#: A REMOVABLE SUBMODULE'S ROOTS ARE NOT HERE: no shipped tier below the
#: module may name its claims (each such submodule has an isolation test,
#: such as tests/unit/test_receiver_probe_isolation.py), so the generator adds them,
#: and the table carries them, only while the submodule is in the tree
#: (``harness/generate_claim_closure.py``, ``REMOVABLE_ROOTS``).
DEVICE_ROOTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "protocol-compiler": (
        "protocol-compiler/thm:gates",
        "protocol-compiler/thm:chain-consumption",
        "protocol-compiler/thm:band-a",
        "protocol-compiler/thm:choice-encoding",
        "protocol-compiler/thm:validator-soundness",
        "protocol-compiler/thm:measurements-and-statistics",
        "protocol-compiler/thm:sifting-and-key",
        "protocol-compiler/thm:typing",
        "protocol-compiler/req:link-row-provenance",
    ),
    "receiver": (
        "receiver/thm:emitted-bound",
        "receiver/cor:emitted-unconditioned",
    ),
    "reductions": (
        "reductions/thm:emit",
        "reductions/thm:licence",
        "reductions/wpfss/cor:emitted-flat",
        "reductions/req:recv-row-provenance",
    ),
    "transmitter": (
        "transmitter/thm:certificate-sufficiency",
        "transmitter/fact:sr",
        "transmitter/decoy/cor:emitted-decoy",
    ),
})

#: THE REDUCTIONS' RESULTS A RUN USES WHERE ITS FIRST-ORDER NUMBER IS FORMED ON
#: THE REFERENCE COMPANION (the direct route): the companion of any reduction
#: instance (``reductions/cor:reference-companion``) and (H-REF) for the flat
#: instance (``reductions/wpfss/cor:flat-companion``, with A-RECV, A-PROBE and
#: A-TSM), which the run's manifest names beside ``meat-core/frank-wolfe/
#: cor:fo-reference`` (``reductions/lem:row-relaxation`` is in their closure). Kept
#: apart from :data:`DEVICE_ROOTS` so that a run that did not count the companion does
#: not name them: the run tier adds them only where it did.
COMPANION_ROOTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "reductions": (
        "reductions/cor:reference-companion",
        "reductions/wpfss/cor:flat-companion",
    ),
})

#: THE COMPLETENESS RESULTS. The completeness figure is a reported number, so
#: the assumptions it rests on are listed with it: the box's bound and its
#: honest containment, and the singleton's figure for a declared singleton.
COMPLETENESS_ROOTS: Final[tuple[str, ...]] = (
    "statistics/binomial-box/thm:completeness-bound",
    "statistics/binomial-box/thm:honest-containment",
    "statistics/singleton/thm:singleton-completeness",
)

#: THE RESULT BEHIND THE EMITTED ACCEPTANCE SUPPORT. statistics emits the
#: acceptance support beside the set and the figure, and its formula is
#: ``thm:box-oracle`` (i)'s (``req:acceptance-support``), a result in no
#: other root's closure; a run that consumes the support rests on it.
ACCEPTANCE_ROOTS: Final[tuple[str, ...]] = ("statistics/thm:box-oracle",)

#: Every root the table carries a closure for, but a removable submodule's.
ALL_ROOTS: Final[tuple[str, ...]] = tuple(sorted({
    *CLAIM_ROOTS,
    *SECRECY_ROOTS,
    *CORRECTNESS_ROOTS,
    *COMPOSITION_ROOTS,
    *(root for roots in DEVICE_ROOTS.values() for root in roots),
    *(root for roots in COMPANION_ROOTS.values() for root in roots),
    *COMPLETENESS_ROOTS,
    *ACCEPTANCE_ROOTS,
}))

#: THE CLAIMS A KEY-RATE REPORT QUOTES AS LIMITATIONS of what it states
#: (known open defects reach a report through such a claim and never through
#: an open item). One declaration, as :data:`CLAIM_ROOTS` is.
LIMITATION_CLAIMS: Final[tuple[str, ...]] = (
    "meat-core/rem:completeness-scope",
    "meat-core/rem:declared-measurement",
    "meat-core/rem:repeated-executions",
)

#: THE OTHER CLAIMS A REPORT LINKS: the requirements and definitions that
#: decide the checks the engine ran, the claim that fixes how the
#: completeness figure is reported, and the claims the report's own
#: sentences name (the certified tier, the check of the statistics, the
#: acceptance box, the snap's reference), so that each reads by its title
#: rather than its id. The generator carries their text so the report needs
#: no copy of its own.
CITED_CLAIMS: Final[tuple[str, ...]] = (
    "foundations/def:evaluated-off-snap",
    "foundations/req:snap-reference",
    "meat-core/def:declaration",
    "meat-core/frank-wolfe/rem:certified-scope",
    "meat-core/frank-wolfe/rem:fo-interface",
    "meat-core/frank-wolfe/req:bracket-on-reference",
    "meat-core/frank-wolfe/req:certified-evaluation",
    "meat-core/frank-wolfe/req:first-order-withdrawal",
    "meat-core/frank-wolfe/thm:firstorder",
    "meat-core/prop:minimal-divergence",
    "meat-core/prop:model-pass-bound",
    "meat-core/prop:value-range",
    "meat-core/rem:plus2",
    "meat-core/req:constrained-key-gate",
    "meat-core/req:exact-admission",
    "meat-core/req:hash-penalty",
    "meat-core/req:key-length-alpha-domain",
    "meat-core/req:marginal-licence-gate",
    "meat-core/req:reported-key-length",
    "meat-core/req:security-statement-not-vacuous",
    "meat-core/req:unreachable-acceptance-set",
    "meat-core/thm:constrained-accumulation",
    "protocol-compiler/def:well-formed-spec",
    "protocol-compiler/thm:gates",
    "protocol-compiler/thm:validator-soundness",
    "receiver/def:compile",
    "receiver/def:graph",
    "receiver/def:probe",
    "receiver/detector-imperfections/prop:efficiency-normalization",
    "receiver/req:graph-refusal",
    "receiver/req:probe-diagonal-admission",
    "reductions/def:protocol",
    "statistics/binomial-box/def:construction",
    "statistics/binomial-box/req:completeness-report",
    "statistics/binomial-box/req:input-refusal",
    "statistics/req:matched-alphabet",
)

#: The package-data file, beside this module.
TABLE_NAME: Final[str] = "claim_closure.json"

#: The vocabulary of the ``verification`` header field of an assumption
#: (spec/claim-format.md section 3.2); ``harness/check_claims.py`` refuses any
#: other value. ``decided`` and ``discharged`` are outside it: an
#: engine-decided condition is a definition plus a requirement and a discharged
#: one is a lemma, so a table carrying
#: either is stale and is refused like any other value outside this set.
VERIFICATIONS: Final[frozenset[str]] = frozenset({"never", "partly"})


class ClaimClosureError(CertiqsError):
    """The shipped closure table is absent or does not cover what was asked.

    Never a refusal: a run's inputs cannot cause it. It means the package data
    is stale against the code (regenerate with
    ``python -m harness.generate_claim_closure``) or was not installed.
    """


@cache
def closure_table() -> dict[str, Any]:
    """Return the shipped table, read once per process."""
    try:
        text = (
            resources.files("certiqs_key.domain")
            .joinpath(TABLE_NAME)
            .read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise ClaimClosureError(
            f"the package data {TABLE_NAME} is missing: {exc}"
        ) from exc
    table = json.loads(text)
    if not isinstance(table, dict):
        raise ClaimClosureError(f"{TABLE_NAME} is not a JSON object")
    return table


def module_version(module_id: str) -> str:
    """Return a module's accepted version as its ``module.yaml`` states it."""
    versions = closure_table().get("module_versions", {})
    if module_id not in versions:
        raise ClaimClosureError(
            f"{TABLE_NAME} names no version for module {module_id!r}"
        )
    return str(versions[module_id])


def claim_closure(root: str) -> dict[str, Any]:
    """Return one root's ``claims`` and ``assumptions``, as the table has them.

    A fresh copy, so that a caller writing it into a record cannot alter the
    cached table.
    """
    roots = closure_table().get("roots", {})
    if root not in roots:
        raise ClaimClosureError(
            f"{TABLE_NAME} carries no closure for the claim root {root!r}; "
            "regenerate it with python -m harness.generate_claim_closure"
        )
    entry = roots[root]
    return {
        "claims": list(entry["claims"]),
        "assumptions": dict(entry["assumptions"]),
    }


@cache
def _verification_by_machine_key() -> dict[str, str]:
    """Return ``{machine key: verification}`` over every assumption of the table.

    Refuses a table in which an assumption has no machine key, two
    assumptions share one, or a field is outside the vocabulary: one key must
    carry one mark, and a key the index cannot resolve uniquely carries none.
    """
    rows = closure_table().get("assumptions")
    if not isinstance(rows, dict) or not rows:
        raise ClaimClosureError(
            f"{TABLE_NAME} carries no assumptions; regenerate it with "
            "python -m harness.generate_claim_closure"
        )
    index: dict[str, str] = {}
    for short_id, row in sorted(rows.items()):
        key = row.get("machine_key") if isinstance(row, dict) else None
        verification = row.get("verification") if isinstance(row, dict) else None
        if not isinstance(key, str) or not key:
            raise ClaimClosureError(
                f"{TABLE_NAME} gives the assumption {short_id} no machine key"
            )
        if key in index:
            raise ClaimClosureError(
                f"the machine key {key!r} names two assumptions in {TABLE_NAME}"
            )
        if verification not in VERIFICATIONS:
            raise ClaimClosureError(
                f"{TABLE_NAME} gives the assumption {short_id} the verification "
                f"{verification!r}, which is not one of {sorted(VERIFICATIONS)}"
            )
        index[key] = str(verification)
    return index


@cache
def _short_id_by_machine_key() -> dict[str, str]:
    """Return ``{machine key: short id}``, refusing what the mark index refuses."""
    _verification_by_machine_key()
    return {
        str(row["machine_key"]): short_id
        for short_id, row in closure_table()["assumptions"].items()
    }


def short_id_of(machine_key: str) -> str:
    """Return the short id of the assumption whose ledger key this is.

    Fail-closed as :func:`never_verified` is: a key that names no assumption
    raises :class:`ClaimClosureError`.
    """
    index = _short_id_by_machine_key()
    if machine_key not in index:
        raise ClaimClosureError(
            f"the machine key {machine_key!r} names no assumption in {TABLE_NAME}; "
            "regenerate the table with python -m harness.generate_claim_closure, "
            "or give the row its owner's key"
        )
    return index[machine_key]


def assumption_info(short_id: str) -> dict[str, Any]:
    """Return one assumption's entry: key, owner, mark, text and anchor.

    A fresh copy, so that a caller writing it into a record cannot alter the
    cached table. An unknown short id raises :class:`ClaimClosureError`.
    """
    rows = closure_table().get("assumptions", {})
    if short_id not in rows:
        raise ClaimClosureError(
            f"{TABLE_NAME} carries no assumption {short_id!r}; regenerate it "
            "with python -m harness.generate_claim_closure"
        )
    copied: dict[str, Any] = json.loads(json.dumps(rows[short_id]))
    return copied


def claim_info(claim_id: str) -> dict[str, Any]:
    """Return one carried claim's kind, plain title, summary, reading, status, anchor.

    The table carries every root, limitation, cited claim, assumption owner
    and link target of a carried text; any other id raises
    :class:`ClaimClosureError`. A fresh copy, as :func:`assumption_info`.
    """
    claims = closure_table().get("claims", {})
    if claim_id not in claims:
        raise ClaimClosureError(
            f"{TABLE_NAME} carries no claim {claim_id!r}; a report cites only the "
            "claims the generator carries (ALL_ROOTS, LIMITATION_CLAIMS, "
            "CITED_CLAIMS, the assumption owners and what their texts link)"
        )
    copied: dict[str, Any] = json.loads(json.dumps(claims[claim_id]))
    return copied


def roots_of_module(module_id: str) -> tuple[str, ...]:
    """Return the roots the table carries whose claims are ``module_id``'s.

    A root belongs to a module when its claim id is ``<module_id>/<label>``,
    or lies in a submodule of it (``<module_id>/<sub>/<label>``). Sorted. This
    is how a run reads the roots of a removable submodule, which the
    generator adds only while the submodule is in the tree and which no tier
    below it may name (``harness/generate_claim_closure.py``,
    ``REMOVABLE_ROOTS``). An empty result is not an error: the module may
    have no root, or may be absent.
    """
    roots = closure_table().get("roots")
    if not isinstance(roots, dict):
        raise ClaimClosureError(
            f"{TABLE_NAME} carries no roots; regenerate it with "
            "python -m harness.generate_claim_closure"
        )
    prefix = module_id.rstrip("/") + "/"
    return tuple(sorted(root for root in roots if root.startswith(prefix)))


def limitations() -> tuple[str, ...]:
    """Return the limitation claims the table carries, in their declared order."""
    found = closure_table().get("limitations")
    if not isinstance(found, list):
        raise ClaimClosureError(
            f"{TABLE_NAME} carries no limitations; regenerate it with "
            "python -m harness.generate_claim_closure"
        )
    return tuple(str(claim_id) for claim_id in found)


def category_order() -> tuple[str, ...]:
    """Return the assumption categories in the order a report groups by."""
    found = closure_table().get("category_order")
    if not isinstance(found, list) or not found:
        raise ClaimClosureError(
            f"{TABLE_NAME} carries no category order; regenerate it with "
            "python -m harness.generate_claim_closure"
        )
    return tuple(str(category) for category in found)


def never_verified(machine_key: str) -> bool:
    """Return whether the assumption with this ledger key is never verified.

    True exactly when the assumption whose machine key this is carries
    ``verification: never`` (spec/claim-format.md section 3.2). The key is
    matched AS WRITTEN, and one key carries one mark whichever module emits
    its row.

    FAIL-CLOSED. A key that names no assumption raises
    :class:`ClaimClosureError`. It can only mean that the table is stale
    against the code or that a module emits a key no assumption owns; either
    way a row whose mark cannot be read is not written with a guessed one, and
    a run record stops on it exactly as it stops on a claim root the table
    lacks.
    """
    index = _verification_by_machine_key()
    if machine_key not in index:
        raise ClaimClosureError(
            f"the machine key {machine_key!r} names no assumption in {TABLE_NAME}; "
            "a ledger row whose owner cannot be read carries no mark (regenerate "
            "the table with python -m harness.generate_claim_closure, or give the "
            "row its owner's key)"
        )
    return index[machine_key] == "never"
