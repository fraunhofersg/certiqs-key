"""The residual r_5's blocks, the efficiency record's rows, and the basis fallback.

Three statements of the receiver claims that describe what the code does,
each checked here so that the code cannot drift from them:

* ``receiver/req:residual-emission``: the blocks ``eq:res5`` maximises over are
  the floating-point blocks of the coarse-grained elements BEFORE any
  dark-count channel, which ``photon_blocks`` carries beside its dark-composed
  blocks; ``r_5`` does not run over the dark-composed ones;
* ``receiver/detector-imperfections/thm:efficiency`` (iv) and
  ``req:efficiency-record``: the record lists every declared loss parameter by
  catalogue entry and parameter, ``t_H``, ``t_V``, ``y_1``, ``y_2`` of C2 and
  ``y`` of C3 among them, each value read as the parameter its row names;
* ``receiver/req:rigorous-weight`` (iii): a proposed basis for which no
  rational ``theta < 1`` satisfies ``foundations/lem:least-eigenvalue-bound``'s
  hypothesis is replaced by the identity, which admits ``theta = 0``.
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import Any

import numpy as np
import pytest

from certiqs_key.foundations import dyadic
from certiqs_key.foundations.dyadic import DyadicMatrix, least_eigenvalue_bound
from certiqs_key.receiver import construct as construct_module
from certiqs_key.receiver.catalogue import PolarizingBeamsplitter, Retarder
from certiqs_key.receiver.efficiency import efficiency_record
from certiqs_key.receiver.numerics import PiMultiple

pytestmark = pytest.mark.contract


def test_r5_runs_on_the_bare_blocks_and_not_on_the_dark_composed_ones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:residual-emission: the blocks r_5 reads are photon_blocks' bare ones.

    A receiver with dark counts emits, per setting, the bare blocks and the
    dark-composed blocks, which differ; the blocks handed to ``r_5`` are
    exactly the bare ones, every letter at every photon number and setting.
    """
    from instances.common.optics import ReceiverParameters
    from tests.support.lowered_templates import optical_lowered

    from certiqs_key.runs.pipeline import DeviceRequests

    seen: list[list[dict[str, Any]]] = []
    original = construct_module.block_positivity_residual

    def capture(blocks: Any, tolerances: Any) -> Any:
        seen.append([dict(item) for item in blocks])
        return original(blocks, tolerances)

    monkeypatch.setattr(construct_module, "block_positivity_residual", capture)
    parameters = ReceiverParameters(
        efficiency=(F(9, 10),) * 4,
        dark_count=(F(1, 10**3),) * 4,
        photon_cutoff=2,
        exact_window=3,
    )
    device = optical_lowered(parameters).device
    assert isinstance(device, DeviceRequests)
    emission = construct_module.construct_receiver(device.receiver_request)
    artifact = emission.artifact
    assert artifact is not None, emission
    (handed,) = seen
    bare = [
        dict(letters)
        for emitted in artifact.photon_blocks
        for _, letters in emitted.blocks
    ]
    composed = [
        dict(letters)
        for emitted in artifact.photon_blocks
        for _, letters in emitted.dark_composed
    ]
    assert handed == bare
    assert handed != composed, "no dark count was composed; the case shows nothing"


def test_the_efficiency_record_lists_c2_and_c3_by_parameter() -> None:
    """thm:efficiency (iv): t_H, t_V, y_1, y_2 of C2 and y of C3, each by name.

    Every row carries its parameter in its element string and its value under
    ``value``, read as that parameter (req:efficiency-record): ``t_H`` and
    ``t_V`` transmittances, ``y_1``, ``y_2`` and ``y`` losses whose
    transmittance is one minus the value.
    """
    pbs = PolarizingBeamsplitter(
        transmittance_h=F(9, 10),
        transmittance_v=F(1, 20),
        phase_h=PiMultiple(F(0)),
        phase_v=PiMultiple(F(0)),
        loss_1=F(1, 100),
        loss_2=F(1, 50),
    )
    retarder = Retarder.half_wave(PiMultiple(F(1, 8)), F(3, 100))
    rows = efficiency_record(
        (
            ("pbs", pbs.entry_id, pbs.loss_parameters()),
            ("hwp", retarder.entry_id, retarder.loss_parameters()),
        ),
        (("H", 0.8),),
    )
    by_element = {row.element: row for row in rows}
    expected = {
        "C2 pbs, parameter t_H": (0.9, "chain position 1"),
        "C2 pbs, parameter t_V": (0.05, "chain position 1"),
        "C2 pbs, parameter y_1": (0.01, "chain position 1"),
        "C2 pbs, parameter y_2": (0.02, "chain position 1"),
        "C3 hwp, parameter y": (0.03, "chain position 2"),
        "L1 detector layer, parameter eta_H": (0.8, "terminal factor D_eta"),
    }
    assert set(by_element) == set(expected)
    for element, (value, site) in expected.items():
        assert by_element[element].value == pytest.approx(value, abs=1e-15)
        assert by_element[element].site == site


def test_an_unusable_proposed_basis_falls_back_to_the_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:rigorous-weight (iii): no rational theta < 1, so the identity is used.

    The refined basis is replaced by ``V = 2 1``, whose Gram defect
    ``||V^T V - 1||_F`` is at least one, so the lemma's hypothesis admits no
    ``theta < 1`` there; the bound returned is the one at the identity,
    ``theta = 0``.
    """
    values = np.array([[0.5, 0.25], [0.25, 0.75]])
    matrix = DyadicMatrix.from_array(values)
    at_identity = least_eigenvalue_bound(matrix, basis="identity")
    # The refined basis is tighter, so the fallback is visible.
    assert least_eigenvalue_bound(matrix) > at_identity

    def doubled(matrix: Any, embedded: Any) -> tuple[Any, int]:
        del matrix
        bits = 4
        return dyadic._eye(embedded.shape[0], 2 << bits), bits

    monkeypatch.setattr(dyadic, "_refined_basis", doubled)
    assert least_eigenvalue_bound(matrix) == at_identity
    assert at_identity <= F(1, 4)
