"""The oracle claim codes, read from ``claim_codes.yaml`` beside this file.

The frozen registries pin claims by oracle codes (C5, PC9, RC8, PR13,
SA3); ``claim_codes.yaml`` is the one table that maps them to this repository's
claim ids, and its header says why and on what evidence. The interface tests
state their mappings as labels relative to one module, so :func:`labels` returns
that shape, keys in natural order.

Nothing here computes a mapping: every function reads the file and reshapes what
it says.
"""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path
from typing import Any

import yaml

PATH = Path(__file__).with_name("claim_codes.yaml")

#: An oracle code: a family of capitals, a number, an optional sub-letter.
CODE = re.compile(r"^(?P<family>[A-Z]+)(?P<number>[0-9]+)(?P<suffix>[a-z]?)$")


def natural_key(code: str) -> tuple[str, int, str]:
    """Order codes by family, then number, then suffix: C9b before C10."""
    match = CODE.match(code)
    if match is None:
        raise ValueError(f"not an oracle claim code: {code!r}")
    return match["family"], int(match["number"]), match["suffix"]


def family(code: str) -> str:
    """Return the family of a code: ``PC`` for ``PC10``, ``C`` for ``C9b``."""
    return natural_key(code)[0]


@cache
def document() -> dict[str, Any]:
    """Return ``claim_codes.yaml``, parsed once."""
    with PATH.open(encoding="utf-8") as handle:
        loaded: dict[str, Any] = yaml.safe_load(handle)
    return loaded


def codes() -> dict[str, tuple[str, ...]]:
    """Return every resolved code with the full ids of the claims that carry it."""
    table = document()["codes"]
    return {code: tuple(table[code]) for code in sorted(table, key=natural_key)}


def labels(
    code_family: str, module: str | tuple[str, ...], *, submodules: bool = False
) -> dict[str, tuple[str, ...]]:
    """Return the codes of a family whose claims lie in ``module``, as labels in it.

    ``labels("PC", "protocol-compiler")`` maps ``PC9`` to ``("def:eligible",
    "thm:gates")``. With ``submodules`` a claim of a submodule of ``module`` lies in
    it too and keeps the submodule in its label (``binomial-box/thm:box-construction``
    under ``statistics``); without, it does not (``C22``, frank-wolfe's, is not among
    ``labels("C", "meat-core")``). A code whose claims lie partly in ``module``
    and partly outside it is an error, because it would drop out of the caller's
    table without a word.

    ``module`` may name several modules, for an oracle module whose claims
    now lie in more than one (the oracle's meat-core: ``("meat-core",
    "foundations")``, its quantum-information preliminaries being in
    foundations); each label then keeps its module, as a full id.
    """
    modules = (module,) if isinstance(module, str) else module
    found: dict[str, tuple[str, ...]] = {}

    def inside_label(claim: str) -> str | None:
        for name in modules:
            rest = claim.removeprefix(f"{name}/")
            if rest != claim and (submodules or "/" not in rest):
                return rest if len(modules) == 1 else claim
        return None

    for code, ids in codes().items():
        if family(code) != code_family:
            continue
        labelled = (inside_label(claim) for claim in ids)
        inside = tuple(label for label in labelled if label is not None)
        if not inside:
            continue
        if len(inside) != len(ids):
            raise ValueError(f"{code} lies partly in {module} and partly not: {ids}")
        found[code] = inside
    return found


def no_claim(code_family: str) -> tuple[str, ...]:
    """Return the codes of a family that resolve to no claim of any module."""
    return tuple(
        code
        for code in sorted(document()["no_claim"], key=natural_key)
        if family(code) == code_family
    )
