"""The passive receiver's default call is the probe-free one, key for key.

The DEFAULT call of the shared builder must declare exactly what the
probe-free receiver declares (optical_bb84, decoy_bb84 and bbm92 build on
it), so it is held against a literal copy of the probe-free construction.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from instances.common.optics import (
    DECLARED_EXACT_WINDOW_TOLERANCES,
    PORTS,
    RAW_LETTERS,
    ReceiverParameters,
    coarse_graining,
    element_graph,
    mode_space,
    receiver_request,
)
from instances.common.passive_device import (
    ACCEPTED_RECEIVER_VERSIONS,
    ENCODED,
    LATTICE_EXPONENT,
    LICENSED,
    passive_device_requests,
)

from certiqs_key.receiver import (
    OFF_SETTING,
    Assurance,
    DetectorPort,
    InputModes,
    PortMap,
    ProbeDeclaration,
    ReceiverRequest,
)
from certiqs_key.reductions.inputs import (
    LinkDeclaration,
    ReductionRequest,
)
from certiqs_key.reductions.inputs import (
    ProbeDeclaration as ReductionProbeDeclaration,
)
from certiqs_key.reductions.inputs import (
    ProtocolDeclaration as ReductionDeclaration,
)
from certiqs_key.reductions.reasons import LinkKind, LinkStage, SourceMode
from certiqs_key.reductions.wpfss import reduce_flat

TOLERANCE = 1e-10


def _old_receiver_request(parameters: ReceiverParameters) -> ReceiverRequest:
    """Return the probe-free request as it was built before the probe hook, frozen."""
    at = {mode.label: position for position, mode in enumerate(mode_space().modes)}
    tolerances = dict(parameters.tolerances)
    exact_window: dict[str, int] = {}
    if parameters.exact_window is not None:
        exact_window = {OFF_SETTING: parameters.exact_window}
        for key, value in DECLARED_EXACT_WINDOW_TOLERANCES.items():
            tolerances.setdefault(key, value)
    return ReceiverRequest(
        mode_space=mode_space(),
        input_modes=InputModes(channel=(at["Z_H"], at["Z_V"]), source=()),
        port_map=PortMap(
            tuple((label, tuple(at[m] for m in modes)) for label, modes in PORTS)
        ),
        detector_layer=tuple(
            DetectorPort(label, efficiency, dark)
            for (label, _modes), efficiency, dark in zip(
                PORTS, parameters.efficiency, parameters.dark_count, strict=True
            )
        ),
        probe_declaration=ProbeDeclaration.probe_free(),
        photon_cutoff=parameters.photon_cutoff,
        exact_window=exact_window,
        numerical_tolerances=tolerances,
        outcome_coarse_graining=coarse_graining(),
        requested_assurance=Assurance.ESTIMATE,
        element_graph=element_graph(parameters),
    )


PARAMETER_CASES = (
    ReceiverParameters(),
    ReceiverParameters(photon_cutoff=1, exact_window=2),
    ReceiverParameters(
        photon_cutoff=2,
        exact_window=3,
        dark_count=(F(1, 1000),) * 4,
        efficiency=(F(9, 10), F(4, 5), F(1), F(1, 2)),
        basis_split=F(1, 3),
    ),
)


@pytest.mark.parametrize("parameters", PARAMETER_CASES)
def test_the_default_receiver_request_is_the_probe_free_one(
    parameters: ReceiverParameters,
) -> None:
    assert receiver_request(parameters) == _old_receiver_request(parameters)


@pytest.mark.parametrize("parameters", PARAMETER_CASES)
@pytest.mark.parametrize("route", [ENCODED, LICENSED])
@pytest.mark.parametrize("mode", [SourceMode.TRUSTED, SourceMode.UNTRUSTED])
def test_the_default_device_requests_are_the_old_ones(
    parameters: ReceiverParameters, route: str, mode: SourceMode
) -> None:
    requests = passive_device_requests(
        parameters, declared_tolerance=TOLERANCE, route=route, source_mode=mode
    )
    assert requests.receiver_request == _old_receiver_request(parameters)
    assert requests.reduction_declaration == ReductionDeclaration(
        probe_declaration=ReductionProbeDeclaration(
            settings=(OFF_SETTING,), weights={OFF_SETTING: F(1)}
        ),
        detection_alphabet=RAW_LETTERS,
        photon_cutoff=parameters.photon_cutoff,
        source_mode=mode,
        joint_alphabet=tuple((letter, OFF_SETTING) for letter in RAW_LETTERS),
    )
    assert requests.reduction_request == ReductionRequest(
        link_declarations=(
            LinkDeclaration(
                stage=LinkStage.RECEIVER,
                kind=LinkKind.WPFSS if route == ENCODED else LinkKind.FSS,
            ),
        ),
        route=route,
        accepted_receiver_versions=ACCEPTED_RECEIVER_VERSIONS,
        requested_assurance="estimate",
        lattice_exponent=LATTICE_EXPONENT,
    )
    assert requests.reduction_entry is reduce_flat
    assert requests.carried_operator_provider is None
