"""Each packaged instance is its template, and the gate's named differences hold.

Each template ``instances/<id>/protocol.yaml`` stands for its instance
(bb84, optical_bb84, decoy_bb84 and bbm92): static surface, preparation
records and refusals on the gate's grid, and run records at
``max_iterations=5``, with named differences. A comparison with a Python
instance has no reference; what is held here is what has one:

1. each instance's ``surface`` IS its template, read as packaged: the module's
   six names are the packaged document surface's, and its digest is the
   template's (``tests/unit/test_declared_surface_static.py`` holds the static
   read equal to it on the whole grid);
2. the NAMED DIFFERENCES are the instances' behaviour, each
   checked for exactly its own shape at its grid point:

   - ``wcp_source_invalid``: decoy's cutoffs out of
     order are the document's coded refusal, not a builtin ``ValueError``;
   - ``factor_assembly_refused``: the document
     PREPARES bbm92's factor assembly on a licensed route with dark counts,
     each factor's entries on its trailing link's witness, so the point is a
     named difference with the preparation as its check (the grid point keeps
     its label, the snapshot's key);
   - ``empty_window``: a cutoff of 2 at the default window of 2 is the
     receiver's coded refusal returned as data, not an escaping
     ``OpticalReceiverError``;
   - ``null_means_absent``: a ``None`` in a section the caller
     passes is dropped, so the key is absent and its section's absence rule
     decides (optical_bb84: no window, recorded; decoy_bb84:
     ``missing_parameter``; bbm92 reads it as absent, as it did).

   The fifth, bbm92's honest note (``test_fraction`` and ``key_bases`` laid over the
   library model's note), is held where a bbm92 record is: the report examples
   (``runs/report_examples/``) and ``tests/unit/test_declared_lowering_optical.py``'s
   note test.

The bb84 template's permanent equivalence with ``instances/bb84/
specification.py`` is ``tests/unit/test_declared_lowering.py``.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from fractions import Fraction as F
from typing import Any

import pytest
from instances import surface_of
from instances.declared import DocumentError, DocumentReason, DocumentSurface
from tests.support.declared_equivalence import IDS, copied
from tests.support.declared_optical_documents import template_surface

from certiqs_key.runs.errors import RunInputKeyError, RunInputReason
from certiqs_key.runs.pipeline import Preparation, SliceRefusal


def _over(instance: str, **sections: dict[str, Any]) -> dict[str, Any]:
    """Lay ``sections`` over the instance's full defaults (optical, bbm92 replace)."""
    default = surface_of(instance).default_config()
    return {
        "model": {**dict(default.model), **sections.get("model", {})},
        "device": {**dict(default.device), **sections.get("device", {})},
    }


# ---------------------------------------------------------------------------
#  1. The instance is its template
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("instance", IDS)
def test_the_instance_surface_is_its_packaged_template(instance: str) -> None:
    """``surface.py`` exposes the packaged surface of ``protocol.yaml`` and no other."""
    module = surface_of(instance)
    document = module.preparation.__self__
    assert isinstance(document, DocumentSurface)
    assert document.packaged
    assert document.digest == template_surface(instance).digest
    for name in ("default_config", "preparation", "runner", "resolve"):
        assert getattr(module, name).__self__ is document, name
    assert module.DESCRIPTOR is document.DESCRIPTOR
    assert module.PARAMETERS is document.PARAMETERS
    assert module.PRESETS is document.PRESETS
    assert module.DEFAULT_HONEST_MODEL_NOTE == document.DEFAULT_HONEST_MODEL_NOTE
    assert module.channel_interface is document.channel_interface
    assert document.DESCRIPTOR.id == instance


# ---------------------------------------------------------------------------
#  2. The named differences, as the instances' behaviour
# ---------------------------------------------------------------------------


def _decide(instance: str, overrides: dict[str, Any]) -> object:
    """Return an instance's preparation of a grid point, or what it raised."""
    surface = surface_of(instance)
    try:
        config = surface.default_config(**copied(copy.deepcopy(overrides)))
        outcome: object = surface.preparation(config)
    except Exception as failure:
        return failure
    return outcome


def _wcp_source_invalid(ours: object) -> None:
    """Check that the library's refusal is the document's code."""
    assert isinstance(ours, DocumentError), ours
    assert ours.reason is DocumentReason.WCP_SOURCE_INVALID
    assert "entropy_cutoff" in ours.detail


def _empty_window(ours: object) -> None:
    """Refuse the empty window as the receiver does: coded, as data."""
    assert isinstance(ours, SliceRefusal), ours
    assert (ours.stage, ours.reason) == (
        "receiver_construction",
        "exact_window_depth_outside_declared_range",
    )


def _factor_assembly_refused(ours: object) -> None:
    """Check that the factor assembly's refusal is the document's code.

    Under ``reductions/thm:licence`` (v) the assembly checks each factor's
    entries against the witness of that factor's TRAILING link, so the point
    prepares, and every station's entries sit on that witness.
    """
    from certiqs_key.reductions.factors import entry_link_witness

    assert isinstance(ours, Preparation), ours
    assert len(ours.device_artifacts) == 2
    for emission in ours.device_artifacts:
        witness = entry_link_witness(emission.reduction)
        for entry in emission.reduction.constraint_list:
            assert entry.certified_against == witness


def _null_means_absent(ours: object) -> None:
    """Check that a ``None`` is dropped and the section's absence rule decides."""
    if isinstance(ours, Preparation):
        # optical_bb84 and bbm92: an absent window is no window, and optical's
        # template records it.
        assert ours.protocol_document is not None
        return
    # decoy_bb84 reads every device parameter: the absent window is missing.
    assert isinstance(ours, RunInputKeyError), ours
    assert ours.reason is RunInputReason.MISSING_PARAMETER


def _null_window_recorded(ours: object) -> None:
    _null_means_absent(ours)
    assert isinstance(ours, Preparation)
    assert ours.protocol_document is not None
    assert [entry["parameter"] for entry in ours.protocol_document["absent"]] == [
        "exact_window"
    ]


#: The named differences, by grid point: the instance, the label, the
#: configuration and the check of the document's outcome.
NAMED: list[tuple[str, str, Callable[[], dict[str, Any]], Callable[[object], None]]] = [
    (
        "decoy_bb84",
        "refused cutoffs",
        lambda: {"device": {"entropy_cutoff": 2, "source_cutoff": 1}},
        _wcp_source_invalid,
    ),
    (
        "bbm92",
        "refused factor assembly",
        lambda: _over(
            "bbm92",
            model={"mean_pairs": F(1, 16)},
            device={
                "source_model": "spdc",
                "route": "licensed",
                "alice_dark_count": dict.fromkeys(("H", "V", "D", "A"), F(1, 10**6)),
            },
        ),
        _factor_assembly_refused,
    ),
    (
        "optical_bb84",
        "refused empty window",
        lambda: _over("optical_bb84", device={"photon_cutoff": 2}),
        _empty_window,
    ),
    (
        "decoy_bb84",
        "refused empty window",
        lambda: {"device": {"photon_cutoff": 2, "exact_window": 2}},
        _empty_window,
    ),
    (
        "bbm92",
        "refused empty window",
        lambda: _over("bbm92", device={"alice_photon_cutoff": 2}),
        _empty_window,
    ),
    (
        "optical_bb84",
        "null window",
        lambda: _over("optical_bb84", device={"exact_window": None}),
        _null_window_recorded,
    ),
    (
        "decoy_bb84",
        "null window",
        lambda: {"device": {"exact_window": None}},
        _null_means_absent,
    ),
    (
        "bbm92",
        "null window",
        lambda: _over("bbm92", device={"alice_exact_window": None}),
        _null_means_absent,
    ),
]


@pytest.mark.parametrize(
    ("instance", "label", "overrides", "check"),
    NAMED,
    ids=[f"{instance}-{label}" for instance, label, _, _ in NAMED],
)
def test_a_named_difference_is_the_instance_s_behaviour(
    instance: str,
    label: str,
    overrides: Callable[[], dict[str, Any]],
    check: Callable[[object], None],
) -> None:
    """Each named difference, for exactly its own shape."""
    check(_decide(instance, overrides()))
