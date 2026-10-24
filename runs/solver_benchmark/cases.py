"""Public development cases selected by numerical failure mechanism.

Motivation: comparisons must include licensed rows, near-one orders and photon
cutoffs, instead of repeatedly optimizing one convenient qubit problem.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _case(
    name: str,
    instance: str,
    reason: str,
    *,
    alpha: float = 1.005,
    rounds: int = 100_000_000,
    model: dict[str, Any] | None = None,
    device: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": name,
        "instance": instance,
        "reason": reason,
        "alpha": alpha,
        "rounds": rounds,
        "model": model or {},
        "device": device or {},
        "f_ec": 1.16,
    }


def bbm_device(
    cutoff: int = 1,
    *,
    route: str = "encoded",
    dark: str = "1e-7",
    efficiency: str = "0.8",
) -> dict[str, Any]:
    """Realistic two-station data; scalar per-port values expand by the surface."""
    result: dict[str, Any] = {"route": route}
    for party in ("alice", "bob"):
        result.update(
            {
                f"{party}_photon_cutoff": cutoff,
                f"{party}_exact_window": cutoff + 1,
                f"{party}_efficiency": efficiency,
                f"{party}_dark_count": dark,
            }
        )
    return result


def cases(profile: str) -> list[dict[str, Any]]:
    """Return independent dictionaries; profiles contain no solver settings."""
    realistic = {
        "alice_transmittance": "0.31622776601683794",
        "bob_transmittance": "0.31622776601683794",
        "visibility": "0.98",
    }
    result = [
        _case(
            "qubit-control",
            "bb84",
            "small well-conditioned control",
            alpha=1.05,
            model={"qber": "0.01"},
        ),
        _case(
            "qubit-near-one",
            "bb84",
            "near-one curvature",
            alpha=1.00001,
            rounds=10**10,
            model={"qber": "0.02"},
        ),
        _case(
            "optical-loss",
            "optical_bb84",
            "optical loss and sectors",
            model={"transmittance": "0.1"},
        ),
        _case(
            "optical-rows",
            "optical_bb84",
            "licensed operator rows",
            model={"transmittance": "0.1"},
            device={"route": "licensed"},
        ),
        _case(
            "optical-dark",
            "optical_bb84",
            "known negative-objective regime",
            model={"transmittance": "0.1"},
            device={"dark_count": "1e-6", "efficiency": "0.8"},
        ),
        _case(
            "bbm-realistic",
            "bbm92",
            "realistic two-sided optical problem",
            alpha=1.00702,
            model=realistic,
            device=bbm_device(),
        ),
        _case(
            "bbm-cutoff3",
            "bbm92",
            "historical early portfolio termination",
            alpha=1.00702,
            model=realistic,
            device=bbm_device(3),
        ),
        _case(
            "bbm-licensed2",
            "bbm92",
            "row-constrained two-sided problem",
            alpha=1.00702,
            model=realistic,
            device=bbm_device(2, route="licensed"),
        ),
        _case(
            "bbm-scalar",
            "bbm92",
            "licensed party-local scalar rows",
            alpha=1.00702,
            model=realistic,
            device={
                **bbm_device(route="licensed"),
                "party_local_view": "licensed_scalar",
            },
        ),
        _case(
            "bbm-tiny-mass",
            "bbm92",
            "reference polish at dark-count products",
            alpha=1.05,
            rounds=2 * 10**11,
            model={
                "alice_transmittance": "0.1",
                "bob_transmittance": "0.006",
                "mean_pairs": "0.05",
            },
            device={
                **bbm_device(dark="1e-6", efficiency="0.6"),
                "bob_efficiency": "0.2",
                "source_model": "spdc",
            },
        ),
        _case(
            "decoy-loss",
            "decoy_bb84",
            "widely differing source weights",
            rounds=10**10,
            model={"transmittance": "0.1"},
        ),
        _case(
            "decoy-cutoff2",
            "decoy_bb84",
            "source and receiver cutoffs",
            rounds=10**10,
            model={"transmittance": "0.1"},
            device={"entropy_cutoff": 2, "photon_cutoff": 2, "exact_window": 3},
        ),
        _case(
            "bbm-singular",
            "bbm92",
            "open support-lift limitation; diagnostic",
            model=realistic,
            device={
                **bbm_device(2, efficiency="1"),
                "alice_efficiency_normalization": "1",
                "bob_efficiency_normalization": "1",
            },
        ),
    ]
    if profile == "fast":
        return deepcopy(result)
    if profile != "slow":
        raise ValueError(f"unknown profile {profile!r}")
    for route in ("encoded", "licensed"):
        for cutoff in (1, 3, 4, 5, 8, 12):
            result.append(
                _case(
                    f"bbm-{route}-N{cutoff}",
                    "bbm92",
                    "cutoff scaling at identical per-case declarations",
                    alpha=1.00702,
                    model=realistic,
                    device=bbm_device(cutoff, route=route),
                )
            )
    for epsilon in (1e-3, 1e-5, 1e-7, 1e-8):
        result.append(
            _case(
                f"bbm-order-{epsilon:g}",
                "bbm92",
                "near-one conditioning at fixed physical data",
                alpha=1 + epsilon,
                rounds=10**12,
                model=realistic,
                device=bbm_device(),
            )
        )
    result.append(
        _case(
            "bbm-spdc-cutoff3",
            "bbm92",
            "populated multiphoton sectors, rather than ideal-pair dimension alone",
            alpha=1.00702,
            model={**realistic, "mean_pairs": "0.05"},
            device={**bbm_device(3), "source_model": "spdc"},
        )
    )
    for cutoff in (8, 12, 20):
        result.append(
            _case(
                f"decoy-source-N{cutoff}",
                "decoy_bb84",
                "higher source preparation cutoff; supported entropy cutoff two",
                rounds=10**10,
                model={"transmittance": "0.1"},
                device={"entropy_cutoff": 2, "source_cutoff": cutoff},
            )
        )
    result.append(
        _case(
            "bbm-asymmetric-cutoff",
            "bbm92",
            "asymmetric sectors",
            model=realistic,
            device={**bbm_device(2), "bob_photon_cutoff": 5, "bob_exact_window": 6},
        )
    )
    return deepcopy(result)
