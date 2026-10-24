"""bbm92's licensed routes prepare with dark counts on either station.

Regression for licensed cases refusing at factor assembly with
``constraint_channel_mismatch`` for any dark count:
:mod:`certiqs_key.reductions.factors` checks every factor's entries against
that factor's SQUASHING witness, so the entries must sit on it.

The grid is {licensed, licensed+two-sector} x {Alice, Bob} x dark count
{1e-5, 1e-9}, with the encoded route as the control; and efficiency 4/5 on
every port of one station with no dark count. Preparation only: what is
asserted is that the stations' factor emission is assembled, and that every
factor's entries sit on its squashing witness. No chain carries a trailing
link after the squasher.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest

from certiqs_key.reductions.factors import entry_link_witness
from certiqs_key.reductions.reasons import LinkKind
from certiqs_key.runs.pipeline import Preparation

PORTS = ("H", "V", "D", "A")


def _prepare(route: str, station: str, dark: F, efficiency: F = F(1)) -> Preparation:
    from instances.bbm92.surface import default_config, preparation

    config = default_config()
    device = {
        **config.device,
        "route": route,
        f"{station}_dark_count": dict.fromkeys(PORTS, dark),
        f"{station}_efficiency": dict.fromkeys(PORTS, efficiency),
    }
    prepared = preparation(replace(config, device=device))
    assert isinstance(prepared, Preparation), prepared
    return prepared


@pytest.mark.parametrize("dark", [F(1, 10**5), F(1, 10**9)], ids=["1e-5", "1e-9"])
@pytest.mark.parametrize("station", ["alice", "bob"])
@pytest.mark.parametrize("route", ["licensed", "licensed+two-sector", "encoded"])
def test_every_station_route_prepares_with_dark_counts(
    route: str, station: str, dark: F
) -> None:
    _assert_assembled(_prepare(route, station, dark))


@pytest.mark.parametrize("station", ["alice", "bob"])
@pytest.mark.parametrize("route", ["licensed", "licensed+two-sector"])
def test_every_station_licensed_route_prepares_at_efficiency_four_fifths(
    route: str, station: str
) -> None:
    """Efficiency 4/5 on every port, no dark count: the probe's refused case.

    ``Preparation`` is returned (the station factor assembly is not refused
    with ``constraint_channel_mismatch``), and every factor's entries sit on
    the witness of its squashing link.
    """
    _assert_assembled(_prepare(route, station, F(0), efficiency=F(4, 5)))


def _assert_assembled(prepared: Preparation) -> None:
    emissions = prepared.device_artifacts
    assert len(emissions) == 2
    for emission in emissions:
        artefact = emission.reduction
        links = artefact.reduction_chain.links
        assert not any(link.kind is LinkKind.FAMILY_DOMINATING for link in links)
        witness = entry_link_witness(artefact)
        assert witness == artefact.squashing_channel.identity
        for entry in artefact.constraint_list:
            assert entry.certified_against == witness
