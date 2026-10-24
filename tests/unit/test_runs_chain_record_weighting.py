"""The one-factor chain record, read through Bob's route-C weighting for the wire.

``runs.pipeline._chain_record_through_weighting``. The compiler
keeps its one-factor ``reduction_chain_record`` unweighted and records the
weighting beside it (``rem:relabel``); the bundle's Bob alphabet is the
weighted support. The rule is the compiler's own multi-factor expansion
(``_factor_chain_record``): each pair ``(physical, v)`` becomes one pair
``(setting_joint_label(physical, f), (v, f))`` per support member of ``v``, in
the support's order, the pairs off the support omitted.

THE EXPANSION IS PINNED HERE ON A STAND-IN WEIGHTING, with no instance, so that
removing a removable submodule, with the instance that first needed the rule,
leaves the run tier's rule tested; that instance's own tests check its
compiled record end to end.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from certiqs_key.protocol_compiler.compile import FactorWeighting
from certiqs_key.protocol_compiler.weights import (
    SettingWeightedFamily,
    setting_joint_label,
)
from certiqs_key.runs.pipeline import _chain_record_through_weighting


@dataclass(frozen=True)
class _WeightingStandIn:
    """The three members of ``SettingWeightedFamily`` the expansion reads."""

    alphabet: tuple[str, ...]
    pairs: dict[str, tuple[str, str]]

    def members_of_outcome(self, outcome: str) -> tuple[str, ...]:
        """Return the support members of one chain outcome, in support order."""
        return tuple(
            label for label in self.alphabet if self.pairs[label][0] == outcome
        )


def test_no_weighting_and_several_factors_pass_through_untouched() -> None:
    record = {"outcome_correspondence": [["a", "a"]], "source_segment": []}
    assert _chain_record_through_weighting(record, ()) is record
    factored = {"source_segment": [], "receiver_factor_segments": []}
    assert _chain_record_through_weighting(factored, (object(),)) is factored  # type: ignore[arg-type]
    assert _chain_record_through_weighting(None, ()) is None


def test_each_pair_expands_to_one_pair_per_support_member() -> None:
    """``v0`` has both choices on the support, ``v1`` only ``f1``: three pairs."""
    weighting = _WeightingStandIn(
        alphabet=("v0@f0", "v0@f1", "v1@f1"),
        pairs={
            "v0@f0": ("v0", "f0"),
            "v0@f1": ("v0", "f1"),
            "v1@f1": ("v1", "f1"),
        },
    )
    record = {
        "outcome_correspondence": [["p0", "v0"], ["p1", "v1"]],
        "source_segment": ["kept"],
    }
    out = _chain_record_through_weighting(
        record,
        (FactorWeighting("f0", cast(SettingWeightedFamily, weighting)),),
    )
    assert out == {
        "outcome_correspondence": [
            [str(setting_joint_label("p0", "f0")), "v0@f0"],
            [str(setting_joint_label("p0", "f1")), "v0@f1"],
            [str(setting_joint_label("p1", "f1")), "v1@f1"],
        ],
        "source_segment": ["kept"],
    }
    # The record handed in is not mutated.
    assert record["outcome_correspondence"] == [["p0", "v0"], ["p1", "v1"]]
