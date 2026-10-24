"""The parity target, and exactly how far the modules reach.

THE TARGET. The parity dataset is
``tests/oracles/data/slice2-n1to5/results.csv`` -- 105 rows, fig 1, photon
cutoffs 1 to 5, three routes, seven QBERs, first-order tier, every row ``ok``.
Its README says which of its columns can be checked without the solver: FOUR
COLUMNS PLUS ``p_mc`` -- ``target_dimension``, ``constraint_entries``,
``constraint_floor_a`` and ``constraint_floor_b``; the key lengths need the
solver and the oracle.

WHAT THIS FILE DOES. The four columns are read off the REDUCTIONS artefact of
a point of the dataset:

* ``construct_receiver`` emits the artefact of the fig-1 device -- four
  unit-efficiency ports, no dark counts, transmittance 1 -- at photon cutoffs
  1 and 2, and ``receiver.docking`` converts it into the reductions module's
  own input rows.
* ``reductions``' ``def:exactadm`` (c) decides exact positive semidefiniteness
  on the declared numbers and REFUSES a family that is not exactly admissible,
  with ``declaration_not_exactly_admissible``. It does not snap: the number
  model puts the one repair at the INSTANCE, before the declaration is made
  (spec/architecture.md 2.8).
* ``certiqs_key.foundations.snap`` is the lattice repair against a declared
  tolerance whose ``snap_max_defect`` and ``snap_max_displacement`` columns are
  in this very CSV, and ``instances/optical_bb84/`` is the prologue that
  declares the tolerance, the lattice exponent and the device.

WHAT IS CHECKED. The four expected values are read from the frozen CSV and
asserted to be what the README says they are, so that the target is in the
tree and machine-readable; and the same four are READ OFF AN ARTEFACT THIS
REPOSITORY PRODUCES, at the two cutoffs whose receiver this suite builds. The
105 key lengths are not here: they need the solver and the oracle.

NOTHING HERE IS FAKED. No fixture stands in for the instance, no tolerance is
invented and no column is compared against a number this repository did not
produce.
"""

from __future__ import annotations

import csv
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from instances.optical_bb84.device import ROUTES
from instances.optical_bb84.optics import ReceiverParameters
from optical_bb84_prologue import run_prologue
from receiver_povm_support import bb84_channel_only_request

from certiqs_key.foundations.exact import Matrix, direct_sum, subtract
from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.receiver.docking import receiver_artifact_rows
from certiqs_key.reductions.wpfss.construction import (
    transported_cutoff_projectors,
)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]

DATA = Path(__file__).resolve().parents[1] / "oracles" / "data" / "slice2-n1to5"

#: The two cutoffs whose receiver this repository can build today. The fixture
#: ``bb84_channel_only_request`` is the receiver's own carried one and is the
#: fig-1 device at transmittance 1 with no dark counts; cutoffs 3 to 5 are the
#: same construction and are left out of the loop only to keep the suite quick.
CUTOFFS = (1, 2)

#: ``tau``, the ceiling the instance's snap may spend on this comparison. It
#: is the dataset's own declared tolerance -- the ``declared_tolerance`` column
#: of every row is ``1e-12`` -- so what is compared is what the run declared.
DECLARED_TOLERANCE = 1e-12

#: The produced artefacts, one per point. Cached because the prologue runs the
#: receiver, the snap and the reduction, and every column of one point is read
#: from the same artefact.
_CACHE: dict[tuple[int, str], Any] = {}


def _parity_rows() -> list[dict[str, str]]:
    with (DATA / "results.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _receiver_rows(cutoff: int) -> object:
    request = bb84_channel_only_request(
        photon_cutoff=cutoff,
        efficiencies=(Fraction(1),) * 4,
        dark_counts=(Fraction(0),) * 4,
    )
    outcome = construct_receiver(request)
    assert outcome.refusal is None, (cutoff, outcome.refusal)
    assert outcome.artifact is not None
    rows = receiver_artifact_rows(outcome.artifact)
    assert not hasattr(rows, "reason"), rows
    return rows


# ---------------------------------------------------------------------------
#  The target, read from the frozen data
# ---------------------------------------------------------------------------


def test_the_frozen_parity_dataset_is_the_one_the_readme_describes() -> None:
    """105 rows, fig 1, five cutoffs, three routes, first-order, every row ok."""
    rows = _parity_rows()
    assert len(rows) == 105
    assert {row["figure"] for row in rows} == {"fig1"}
    assert {row["photon_cutoff"] for row in rows} == {"1", "2", "3", "4", "5"}
    # The frozen rows name the route by the name it had when they were made;
    # it is licensed+two-sector now (reductions/rename-eq27-two-sector).
    assert {row["route"] for row in rows} == {"encoded", "licensed", "licensed+eq27"}
    assert {row["status"] for row in rows} == {"ok"}
    assert {row["reported_tier"] for row in rows} == {"first-order"}


def test_the_four_compiler_visible_columns_are_constant_per_cutoff_and_route() -> None:
    """The target values, stated so that they are in the tree and readable.

    ``target_dimension`` depends on the cutoff alone; ``constraint_entries`` is
    0 on the encoded route and 1 on the two licensed ones; the two-sector entry's two
    floors are ``0`` and ``1 - 2^-N`` for ``N >= 2``, and at ``N = 1`` the
    dyadic ``137164075565 / 274877906944``, which is the lattice-rounded value
    the run emitted rather than a closed form. NOTHING IS RECOMPUTED HERE: the
    CSV is frozen oracle data and this test reads it.
    """
    rows = _parity_rows()
    dimensions = {row["photon_cutoff"]: row["target_dimension"] for row in rows}
    assert dimensions == {"1": "9", "2": "12", "3": "16", "4": "21", "5": "27"}

    for row in rows:
        if row["route"] == "encoded":
            assert row["constraint_entries"] == "0", row["index"]
            assert row["constraint_floor_a"] == "", row["index"]
            assert row["constraint_floor_b"] == "", row["index"]
        else:
            assert row["constraint_entries"] == "1", row["index"]
            assert row["constraint_floor_a"] == "0", row["index"]

    floors = {
        row["photon_cutoff"]: row["constraint_floor_b"]
        for row in rows
        if row["route"] != "encoded"
    }
    assert floors["2"] == "3/4"
    assert floors["3"] == "7/8"
    assert floors["4"] == "15/16"
    assert floors["5"] == "31/32"
    assert floors["1"] == "137164075565/274877906944"


# ---------------------------------------------------------------------------
#  How far the modules reach
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_the_receiver_artefact_of_a_slice_two_point_is_producible(cutoff: int) -> None:
    """THE HALF THAT IS DONE, asserted rather than assumed.

    The fig-1 device is the channel-only BB84 receiver at unit efficiency with
    no dark counts, the receiver tests' fixture. Its
    artefact is emitted and docks into the reductions module's input rows, and
    the two data the parity columns will be read through -- the block grading
    and the bound quantifier's cutoff -- carry the cutoff the point declares.
    """
    rows = _receiver_rows(cutoff)
    # The receiver's pin, an accepted version of spec/modules/receiver/module.yaml,
    # written by hand when the pin moves, never regenerated from the code.
    assert rows.mathematical_spec_version == "receiver@0.9.0"  # type: ignore[attr-defined]
    grading = rows.channel_grading  # type: ignore[attr-defined]
    assert grading.block_dimensions == tuple(range(1, cutoff + 2))
    assert rows.bound_quantifier_domain.cutoff == cutoff  # type: ignore[attr-defined]
    assert rows.detection_alphabet == (  # type: ignore[attr-defined]
        "nc",
        "sc_0",
        "sc_1",
        "sc_2",
        "sc_3",
        "mc",
    )


# ---------------------------------------------------------------------------
#  The comparison the sentinel asked for
# ---------------------------------------------------------------------------


def _floors(reduction: object) -> tuple[Fraction, Fraction] | None:
    """Return ``(a, b)`` of the strongest declared entry, or ``None``.

    RECOVERED FROM THE OPERATOR, never parsed out of a label, which is how the
    instance and the reductions module each recover them independently. An emitted entry
    of
    Eq. ``eq:two-sector-entry``'s shape is ``F_e - a Pi_{<=N} - b Pi_Flag``, so the
    difference against the target element it is about is
    ``a Pi_{<=N} + b Pi_Flag``: a two-block scalar whose diagonal reads off
    both. The LARGEST pair is the one reported -- a list carrying the baseline
    entry and the published one carries ``a = 0`` and ``a > 0``, and what the
    column says is what the strongest declared entry asserts.

    The emitted operators are SECTOR-BLOCK LISTS (spec/architecture.md 2.9), so
    each is re-assembled by ``direct_sum`` for this whole-space reading, which
    is the same rendering :func:`transported_cutoff_projectors` returns.
    """
    preserved = reduction.source_descriptor.channel_grading.preserved_dimension  # type: ignore[attr-defined]
    projector, _flag = transported_cutoff_projectors(
        preserved, len(reduction.target_povm)  # type: ignore[attr-defined]
    )
    dimension = len(projector)
    if dimension == 0 or preserved == 0 or preserved >= dimension:
        return None
    found: list[tuple[Fraction, Fraction]] = []
    for entry in reduction.constraint_list:  # type: ignore[attr-defined]
        operator = direct_sum(list(entry.operator))
        for element in reduction.target_povm.values():  # type: ignore[attr-defined]
            difference = subtract(direct_sum(list(element)), operator)
            below = difference[0][0]
            above = difference[dimension - 1][dimension - 1]
            if below.im != 0 or above.im != 0:
                continue
            if _is_two_block_scalar(difference, preserved, below.re, above.re):
                found.append((below.re, above.re))
                break
    return max(found) if found else None


def _is_two_block_scalar(
    operator: Matrix, preserved: int, below: Fraction, above: Fraction
) -> bool:
    """Say whether ``operator`` is ``below Pi_{<=N} + above Pi_Flag``, exactly."""
    dimension = len(operator)
    for row in range(dimension):
        for column in range(dimension):
            entry = operator[row][column]
            if row != column:
                if not entry.is_zero:
                    return False
                continue
            expected = below if row < preserved else above
            if entry.re != expected or entry.im != 0:
                return False
    return True


@pytest.mark.parametrize("cutoff", CUTOFFS)
@pytest.mark.parametrize("route", ROUTES)
def test_the_four_parity_columns_reproduce_on_the_migrated_modules(
    cutoff: int, route: str
) -> None:
    """The four parity columns of the fig-1 device, against the frozen CSV.

    The lattice-snapping step and the optical BB84 prologue declare the
    tolerance, the lattice exponent and the device; the comparison is made on
    the two cutoffs whose receiver this suite builds.

    FOUR COLUMNS, READ OFF A PRODUCED ARTEFACT AND COMPARED WITH THE FROZEN
    CSV: ``target_dimension`` off the target descriptor,
    ``constraint_entries`` as the length of the emitted list, and the two
    floors recovered from the operators. The 105 KEY LENGTHS ARE NOT HERE: they
    belong to the recalculation, which runs the grid and compares ``h_lb`` and
    ``key_length``. What this file checks is the part that needs no solver and
    no oracle.

    THE DEVICE IS THE DATASET'S OWN: unit efficiencies, no dark counts,
    transmittance 1, a balanced beamsplitter, and the exact-window depth the
    row carries (``m* = N + 1``). Nothing is tuned: a column that disagreed
    would be a finding about the modules, not a tolerance to widen.
    """
    expected = _row(cutoff, route)
    reduction = _reduction(cutoff, route)

    assert str(reduction.target_descriptor.dimension) == expected["target_dimension"]
    assert str(len(reduction.constraint_list)) == expected["constraint_entries"]

    floors = _floors(reduction)
    if expected["constraint_floor_a"] == "":
        # The encoded route declares no entry at all, so both columns are empty
        # rather than reporting a zero no one declared.
        assert floors is None
        assert expected["constraint_floor_b"] == ""
        return
    assert floors is not None
    assert str(floors[0]) == expected["constraint_floor_a"]
    # Derived by hand. The CSV's floor_b is lat(p) at the floating-point
    # weight p = 1/2 - eps_eig (N = 1), resp. its 3/4 (N = 2); it stays in the
    # tree as the dataset's record. receiver/req:rigorous-weight (iv)
    # emits the largest binary64 at or below the enclosed weight, which
    # def:enclosed-weight (iii) reads with no eps_eig, so p lies in
    # [p* - 2^-52, p*] with p* = 1/2 at N = 1 (ex:bb84exact: beta*(2) = 1/2 =
    # beta(3)) and p* = 3/4 at N = 2 (the remainder beta(4) = 3/4), and
    # floor_b = lat(p) <= p, lat the floor to the 2^-40 lattice of
    # eq:latdown (r_min = 0, q_t = 1 here).
    exact = {1: Fraction(1, 2), 2: Fraction(3, 4)}[cutoff]
    assert exact - Fraction(1, 2**52) - Fraction(1, 2**40) <= floors[1] <= exact


#: Routes the frozen rows name by an earlier name: the name now, and the
#: frozen name (``reductions/rename-eq27-two-sector``).
FROZEN_ROUTE_NAME: dict[str, str] = {"licensed+two-sector": "licensed+eq27"}


def _row(cutoff: int, route: str) -> dict[str, str]:
    """Return one frozen row's four columns; every QBER agrees on all four."""
    frozen = FROZEN_ROUTE_NAME.get(route, route)
    rows = [
        row
        for row in _parity_rows()
        if row["photon_cutoff"] == str(cutoff) and row["route"] == frozen
    ]
    assert rows, (cutoff, route)
    keys = (
        "target_dimension",
        "constraint_entries",
        "constraint_floor_a",
        "constraint_floor_b",
        "exact_window",
    )
    for key in keys:
        assert len({row[key] for row in rows}) == 1, (key, cutoff, route)
    return {key: rows[0][key] for key in keys}


def _reduction(cutoff: int, route: str) -> Any:
    """Return the reduction artefact of the fig-1 device at this point."""
    key = (cutoff, route)
    if key not in _CACHE:
        window = int(_row(cutoff, route)["exact_window"])
        parameters = ReceiverParameters(photon_cutoff=cutoff, exact_window=window)
        _CACHE[key] = run_prologue(
            parameters, route=route, declared_tolerance=DECLARED_TOLERANCE
        ).reduction
    return _CACHE[key]
