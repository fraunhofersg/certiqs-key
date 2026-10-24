"""The claim-closure table's accessors read what the key-rate report needs, fail-closed.

MOTIVATION. The key-rate report quotes assumption text and links claims from
one source, the claim headers, carried into the package by the generated
table. These accessors are the
only way the run tier reads that text, so a gap in the table has to surface
as an error, never as a silently missing line in a report: every declared
root, limitation and cited claim is carried, every link a carried text makes
resolves inside the table, and an unknown id or key raises
:class:`ClaimClosureError`. That the table is current against the claim
files is ``tests/harness/test_generate_claim_closure.py``.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from certiqs_key.domain import claim_closure as module
from certiqs_key.domain.claim_closure import (
    ACCEPTANCE_ROOTS,
    ALL_ROOTS,
    CITED_CLAIMS,
    CLAIM_ROOTS,
    COMPANION_ROOTS,
    COMPLETENESS_ROOTS,
    COMPOSITION_ROOTS,
    CORRECTNESS_ROOTS,
    DEVICE_ROOTS,
    LIMITATION_CLAIMS,
    SECRECY_ROOTS,
    ClaimClosureError,
    assumption_info,
    category_order,
    claim_closure,
    claim_info,
    closure_table,
    limitations,
    roots_of_module,
    short_id_of,
)

LINK = re.compile(r"\[\[([^\[\]]*)\]\]")
SHORT_ID = re.compile(r"^A-[A-Z0-9][A-Z0-9-]*$")


def _assumptions() -> dict[str, Any]:
    rows = closure_table()["assumptions"]
    assert isinstance(rows, dict)
    return rows


def test_all_roots_is_the_union_of_the_declared_roots_and_each_is_carried() -> None:
    declared = {*CLAIM_ROOTS, *SECRECY_ROOTS, *CORRECTNESS_ROOTS, *COMPOSITION_ROOTS,
                *COMPLETENESS_ROOTS, *ACCEPTANCE_ROOTS,
                *(root for roots in DEVICE_ROOTS.values() for root in roots),
                *(root for roots in COMPANION_ROOTS.values() for root in roots)}
    assert set(ALL_ROOTS) == declared
    assert list(ALL_ROOTS) == sorted(ALL_ROOTS)
    carried = set(closure_table()["roots"])
    assert declared <= carried
    # Beyond them only a removable submodule's roots, which the generator adds
    # while the submodule is in the tree (and which domain/ may not name).
    for root in carried - declared:
        module_id = root.rsplit("/", 1)[0]
        assert module_id.count("/") == 1, root
        assert module_id in closure_table()["module_versions"], root
    for root in sorted(carried):
        entry = claim_closure(root)
        assert entry["claims"][0] == root
        assert claim_info(root)["contract"]["anchor"] == f"claim-{root}"


def test_every_assumption_carries_its_text_mark_and_anchor() -> None:
    sentences = {row["verification"]: row["verification_sentence"]
                 for row in _assumptions().values()}
    for short_id, row in _assumptions().items():
        info = assumption_info(short_id)
        assert info == row
        assert info["title"] and info["summary"], short_id
        assert info["contract"] == {
            "pdf": f"spec/modules/{info['owner'].split('/')[0]}/contract.pdf",
            "anchor": f"claim-{info['owner']}",
        }
        # One sentence per verification value: the contract's, copied.
        assert info["verification_sentence"] == sentences[info["verification"]]
        assert claim_info(info["owner"])["kind"] == "ass"
        if info["category"] is not None:
            assert info["category"] in category_order(), short_id
        if info["refines"] is not None:
            assert info["refines"] in _assumptions(), short_id
        assert isinstance(info["emission"], dict)


def test_a_returned_entry_is_a_copy() -> None:
    first = sorted(_assumptions())[0]
    info = assumption_info(first)
    info["title"] = "altered"
    info["contract"]["anchor"] = "altered"
    assert assumption_info(first)["title"] != "altered"
    assert assumption_info(first)["contract"]["anchor"] != "altered"
    claim = claim_info(ALL_ROOTS[0])
    claim["summary"] = "altered"
    assert claim_info(ALL_ROOTS[0])["summary"] != "altered"


def test_short_id_of_inverts_the_machine_key() -> None:
    for short_id, row in _assumptions().items():
        assert short_id_of(row["machine_key"]) == short_id
    with pytest.raises(ClaimClosureError, match="names no assumption"):
        short_id_of("honest_model = iid_honest_rounds")


def test_roots_of_module_filters_the_carried_roots_by_module_prefix() -> None:
    carried = set(closure_table()["roots"])
    for module_id, roots in DEVICE_ROOTS.items():
        found = roots_of_module(module_id)
        assert list(found) == sorted(found)
        assert set(roots) <= set(found), module_id
        assert set(found) <= carried
        assert all(root.startswith(module_id + "/") for root in found)
    # A submodule's roots are found under its own id too, and the roots of
    # the device modules partition the device part of the table.
    assert roots_of_module("statistics/singleton") == (
        "statistics/singleton/thm:singleton-completeness",
    )
    assert roots_of_module("meat-core/") == roots_of_module("meat-core")
    assert roots_of_module("no-such-module") == ()
    # The prefix is a whole path segment: "receiver" is not "receiver-x".
    assert not any(root.startswith("reductions/")
                   for root in roots_of_module("reduction"))


def test_limitations_and_cited_claims_are_carried() -> None:
    assert limitations() == LIMITATION_CLAIMS
    for claim_id in (*LIMITATION_CLAIMS, *CITED_CLAIMS):
        info = claim_info(claim_id)
        assert info["title"] and info["kind_word"], claim_id
        assert info["contract"]["anchor"] == f"claim-{claim_id}"


def test_every_link_of_a_carried_text_is_a_full_target_inside_the_table() -> None:
    table = closure_table()
    texts = [
        row[field]
        for block in ("assumptions", "claims")
        for row in table[block].values()
        for field in ("summary", "user_statement")
        if row.get(field)
    ]
    targets = {target for text in texts for target in LINK.findall(text)}
    assert targets, "no carried text links anything; the check would be vacuous"
    for target in targets:
        if SHORT_ID.match(target):
            assert target in table["assumptions"], target
        else:
            assert "/" in target and target in table["claims"], target


def test_unknown_ids_are_refused() -> None:
    with pytest.raises(ClaimClosureError, match="no assumption"):
        assumption_info("A-NOWHERE")
    with pytest.raises(ClaimClosureError, match="no claim"):
        claim_info("meat-core/thm:nowhere")


def test_a_table_without_the_report_blocks_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module, "closure_table", lambda: {"roots": {}})
    with pytest.raises(ClaimClosureError, match="no limitations"):
        limitations()
    with pytest.raises(ClaimClosureError, match="no category order"):
        category_order()
    with pytest.raises(ClaimClosureError, match="no assumption"):
        assumption_info("A-AUTH")
    with pytest.raises(ClaimClosureError, match="no claim"):
        claim_info(ALL_ROOTS[0])
    monkeypatch.setattr(module, "closure_table", lambda: {})
    with pytest.raises(ClaimClosureError, match="no roots"):
        roots_of_module("meat-core")
