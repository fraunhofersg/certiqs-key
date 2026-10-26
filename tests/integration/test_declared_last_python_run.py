"""The templates against the frozen snapshot of the Python instances' last run.

The Python instances bb84, optical_bb84, decoy_bb84 and bbm92, against which
the equivalence gate held their templates, are not in the tree. Their outcomes
on the gate's grid are frozen as a SNAPSHOT (``tests/data/b6-last-python-run/``,
its ``README.md``): per instance the static surface, and per grid point the
``default_config`` payload and the preparation record (wall clock, provenance
and ``protocol_document`` stripped), or the exception's type and code. This
test holds the templates against it, so that a change to a template, the
lowering or the library that moves any preparation of the four instances is
seen as a difference from the code they replaced.

It is a snapshot, not an oracle (PRINCIPLES.md 2.3 is not engaged): a
difference is a finding to read, and the snapshot is regenerated only by an
explicit, reviewed decision, never to make this test pass.

THE NAMED DIFFERENCES are the only points not compared: at the
grid points of :data:`INTENDED` the snapshot holds the Python side's decision,
which is checked to be the one the gate named, and the template's own outcome
there is ``tests/integration/test_declared_equivalence.py``'s. bbm92's
honest-note difference is in no preparation record.

ENGINE CHANGES AFTER THE SNAPSHOT. The snapshot froze the ENGINE at the time
as well as the Python instances, and the Python instances cannot be re-run on
a later engine. An engine change that moves a preparation on purpose is
therefore named here, as a projection both sides pass through
(:func:`_projected`) and, where it moves a number, as a named engine
difference (:data:`ENGINE_NAMED`), each checked to be the decided behaviour.
The projections:

* the record carries the group of every reduction-chain snap block (``group``,
  ``group_fix``), the instance-snap block's ``group`` and ``reference_kind``,
  each resting block's ``group`` and ``fix`` and the A-SNAP entry's
  ``groups``, and no ``added_sector_labels``; the digest of every
  reduction-chain artefact moves with that content. These are projected away;
* the instance's measurement-snap record has no ``weight_carried`` (the
  instance wrote ``true`` there to mean "handed to reductions", which the
  encoded route does not carry). Projected away;
* at the numeric edits ``edit 1`` (dark counts) and ``edit 2`` (efficiency
  0.9 at cutoff 2) the snapshot shows a carry by ADDED flag sectors, or an
  all-or-nothing composition that dropped a certified block's weight beside
  an uncertified one; the engine carries neither on the encoded route and
  discloses the weight as not carried. Those points are checked to be exactly
  that difference;
* at ``edit 0`` of optical_bb84 (basis split 1/3, an ideal device) an
  uncertified one-photon block is snapped by the one fidelity-first
  procedure (the support-safe rows on the centres), where the snapshot used
  round-down-and-place. The declared family and its displacement are the
  same; the steps, the residue placement and the absorbing outcome of an
  uncertified block are the procedure's own and are projected away at
  :data:`PROCEDURE_NAMED`, after checking that the snapshot used the other
  procedure and we do not;
* ``certify_snaps`` and ``underlying_cause`` (every snap block and emission
  class) and ``entries_not_in_force`` are keys of the record the snapshot
  lacks; they are projected away (:data:`_NEW_KEYS`). The default path,
  which certifies nothing, is held by its own tests
  (``tests/unit/test_snap_certification_opt_in.py``,
  ``tests/integration/test_snap_keep_or_move_runs.py``);
* ``compiled.public.choice_weighting`` in the snapshot, one object with the
  factor's party or ``null``, is ``choice_weightings`` in ours, a list of one
  entry per weighted factor naming the factor and no party; the snapshot's
  object is projected onto that shape;
* the transmitter emits A-ENS in trusted-source mode only, a station's
  reductions ledger carries A-PROBE only at two settings or more and A-TSM
  only where it does or a public choice is applied at its factor, and the
  station bindings of A-MEAS, A-ROUND-SQ and A-SEQ name the station's party
  (:func:`_r2_named`, which checks each rule before applying it to the
  snapshot); the transmitter artefact's digest moves with its ledger;
* the reductions artefact's A-ROUND-SQ binding is "the measuring party's
  physical POVM" with the value "one for every round, no memory across
  rounds" (reductions/ass:round is the physical measurement), where the
  snapshot says "one POVM, one declared model, one squashing channel" with
  the value "declared". The old wording is mapped to the new one on both
  sides (:data:`_RENAMED_BINDINGS`), the value by :data:`_REVALUED_BINDINGS`;
* the compiler's emitted record has no A-PRESENT row, omits A-LINK on an
  in-run single exact instance link and gains the decision on the physical
  receiver family in its transcript, so the digest of every declaration
  artefact differs; like a reduction chain's, it is projected away
  (``declaration:*``), the compiled declaration itself still being compared.
  The reductions artefact carries A-CONST only where its emitted constraint
  list is non-empty (``reductions/req:assumption-ledger``): on a ledger
  beside an empty list the snapshot's A-CONST row is projected away, after
  :func:`_check_a_const` has checked that ours carries the row exactly where
  the list is non-empty. The module pins differ from the snapshot's
  (:data:`_MOVED_PINS`). No number, entry, family or weight moves;
* there is no certified snap: no certification option, no weight ceiling, no
  domination link and no weight of a snap, and every snap block is kept or
  moved by the one fidelity-first procedure, the emission normaliser's too.
  ``certified_weight_ceiling`` is dropped from the snapshot's configurations
  (:data:`_RETIRED_KEYS`), and no point is prepared with ``certify_snaps``
  (:data:`CERTIFY` is empty). The snap records themselves -- the instance's
  measurement snaps and their settings, the instance-snap record the
  reduction reads, the emission record and the domination record -- are in a
  vocabulary the snapshot has and ours has not, and are projected away
  (:data:`_RETIRED_KEYS`), with the rows adapter's note that describes them
  (:data:`_SNAP_NOTE`), the input preparation of the ceiling and the
  domination submodule's two verification rows (:data:`_RETIRED_RULES`); what
  the snap produced is still compared wherever the record carries it (the
  declared rows, the raw joint distribution, the constraint entries, the
  reduction's target). At the numeric edits of :data:`ENGINE_NAMED` the
  snapshot carried a positive weight by a domination link, or dropped it all
  or nothing; ours forms no such link, and at ``edit 2`` the moved numbers
  are the fidelity-first procedure's (the raw joint distribution differs
  there by single lattice steps). Those points are checked to have that
  difference and are not compared further;
* the run option ``strict_certification`` of the snapshot is ``strict_snaps``
  (:data:`_RENAMED_KEYS`), A-SNAP's machine key
  ``snapped_measurement_uncertified`` is ``snapped_measurement``, and the
  emitted pins are those of the current modules (:data:`_MOVED_PINS`). The
  snapshot's spelling is mapped to ours. The receiver artefact pins its
  version, so its digest differs too and is projected away
  (``receiver_artifact:*``), as a reduction chain's and a declaration's are;
  the receiver's content is still compared; the transmitter artefact pins its
  version likewise;
* the snapshot's route ``licensed+eq27`` is ``licensed+two-sector``, in its
  case labels and every value (:data:`_RENAMED_ROUTES`, applied as the
  snapshot is read). No number moves;
* an exact-route receiver emits the enclosed weight rounded down where its
  port Grams are enclosed (``receiver/req:rigorous-weight``), so the weight
  differs (by at most ``eps_eig`` up, rounding down) and with it the declared
  POVM, the reductions' target and the A-EIG row. The snapshot froze the
  floating-point weight, which still runs: :func:`_floating_point_receiver`
  checks the named difference at every rigorous setting and hands the
  floating-point setting on, and the four per-setting fields of the rigorous
  weight are projected away after checking they say so
  (:func:`_without_evaluation_fields`);
* the receiver carries a factor enclosure beside the entrywise enclosure of
  every block of a component graph whose count admits one
  (``receiver/detector-imperfections/req:dark-composed-reference`` (vii)),
  and leaves the entrywise enclosure unaltered. Each offered block has
  ``factor_enclosures`` and, where one is carried, the reference's
  establishing claims include ``receiver/thm:factor-blocks (iii)`` and
  ``receiver/component-catalogue/lem:catalogue-dilations (ii)``. Both are
  projected away after checking they say so (:func:`_without_factor_form`).
  The digest of the enclosures covers the factors, so it is formed here
  without them (:func:`_enclosure_digest_without_factors`) and still compares
  the entrywise enclosures whole;
* the reductions artefact's licence names, per entry, the claim that
  discharges it (``discharge_per_entry``, ``reductions/req:licence-record``),
  a key the snapshot lacks and that is projected away (:data:`_NEW_KEYS`);
  and a receiver's efficiency-record row carries its declared loss parameter
  as ``value``, the snapshot's ``transmittance``, mapped back in
  :func:`_projected`. No number moves;
* no reductions ledger carries A-EVE-DIM (``adversary_registers_finite``):
  ``meat-core/ass:eve-dim`` is superseded and no claim assumes it. The
  snapshot's row is projected away (:func:`_projected`) after
  :func:`_check_no_eve_dim` has checked that ours carries it nowhere. It
  binds nothing, so no value moves:
  :func:`_check_snapshot_eve_dim_binds_nothing` asserts that of every
  snapshot row it drops (``constrains`` empty, ``inherited`` empty);
* a configuration's ``solver`` block writes ``gap_tolerance`` only where it
  is chosen, under ``solver.advanced`` (record schema 0.43.0), where the
  snapshot's always wrote it beside ``max_iterations``. The snapshot's
  unchosen ``gap_tolerance: null`` is projected away (:func:`_projected`),
  after checking that it is null; a chosen one would be a real difference.
  No number moves.
* every reductions artefact records why its A-RECV row is absent where it is
  (``receiver_row_omitted_on_provenance``, ``reductions/req:recv-row-provenance``),
  and the receiver stage carries the receiver artefact's own ledger
  (``assumption_ledger``, record 0.44.0). Both keys are projected away
  (:data:`_NEW_KEYS`, :data:`_ADDED_KEYS`) after :func:`_check_recv_row` has
  checked what they say here: the comparison runs the floating-point receiver
  (:func:`_floating_point_receiver`), whose weights keep the A-RECV row, so
  every omission list is empty and every station's ledger carries the row as
  the snapshot's does; and the receiver stage's ledger names the keys its
  ``assumptions`` map names, in its order. No row or number moves.

INSTANCE CHANGES AFTER THE SNAPSHOT. The optical receivers' polarizing
beamsplitter had one parameter, ``pbs_extinction``; it is two now,
``pbs_leak_transmitted`` (the PBS's ``transmittance_v``) and
``pbs_leak_reflected`` (``1 - transmittance_h``), and each detector port reads
both polarization modes of its path instead of one (``instances/common/
optics.py``, ``PORTS``), so that light a PBS leaks the wrong way clicks the
other detector of the pair. The snapshot is read through that change
(:func:`_split_pbs`): each ``pbs_extinction`` value becomes the same value in
both leaks, and each single-mode port its path's two modes. Every value the
snapshot holds is ``0`` (checked), where a perfect PBS sends nothing into the
added modes, so no number moves and the preparation is compared whole. On the
static surface the two leak rows stand where the extinction row stood and
carry its declaration but for name and meaning (:func:`_split_static`).

ROUNDING. The receiver's floating-point evaluations (each photon-number
block's elements, each port's Gram) carry the last bits of the BLAS kernel
the CPU picks at run time, so they are compared within four ulps of one
(:func:`_within_rounding`), as a residual is compared within its tolerance;
everything else, the exact values and the digests of the enclosures among
them, is compared whole.
"""

from __future__ import annotations

import copy
import functools
import gzip
import importlib.util
import json
import math
import re
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from instances import surface_of
from tests.support.declared_equivalence import IDS, config_grid

from certiqs_key.receiver import construct

SNAPSHOT = Path(__file__).resolve().parents[1] / "data" / "b6-last-python-run"


@functools.cache
def _maker() -> ModuleType:
    """Return the snapshot's own writer: its stripping rule, its outcome reader."""
    spec = importlib.util.spec_from_file_location(
        "b6_make_snapshot", SNAPSHOT / "make_snapshot.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Routes the snapshot names by an earlier name, and their names now.
_RENAMED_ROUTES: dict[str, str] = {"licensed+eq27": "licensed+two-sector"}


@functools.cache
def _snapshot(instance: str) -> dict[str, Any]:
    with gzip.open(SNAPSHOT / f"{instance}.json.gz", "rt", encoding="utf-8") as handle:
        text = handle.read()
    for before, after in _RENAMED_ROUTES.items():
        text = text.replace(f'"{before}"', f'"{after}"').replace(
            f"route={before}", f"route={after}"
        )
    data: dict[str, Any] = json.loads(text)
    return data


def _over(instance: str, **sections: dict[str, Any]) -> dict[str, Any]:
    """Lay ``sections`` over the instance's full defaults (optical, bbm92 replace)."""
    default = surface_of(instance).default_config()
    return {
        "model": {**dict(default.model), **sections.get("model", {})},
        "device": {**dict(default.device), **sections.get("device", {})},
    }


# The gate's refusals beyond the grid, verbatim from
# tests/integration/test_declared_equivalence.py at a development commit.
REFUSALS: list[tuple[str, str, dict[str, Any]]] = [
    (
        "bb84",
        "refused normalisation",
        _over("bb84", device={"alice_z": F(3, 5), "alice_x": F(3, 5)}),
    ),
    ("bb84", "refused domain", _over("bb84", model={"qber": F(1, 2)})),
    (
        "optical_bb84",
        "refused domain",
        _over("optical_bb84", device={"basis_split": F(3, 2)}),
    ),
    (
        "optical_bb84",
        "refused by the receiver",
        _over("optical_bb84", device={"half_wave_angle": F(1)}),
    ),
    (
        "optical_bb84",
        "refused port labels",
        _over("optical_bb84", device={"dark_count": {"H": F(1, 2)}}),
    ),
    (
        "decoy_bb84",
        "refused normalisation",
        {"device": {"test_signal": F(1, 2), "test_weak": F(1, 2)}},
    ),
    ("decoy_bb84", "refused domain", {"device": {"gamma": F(0)}}),
    ("decoy_bb84", "refused support", {"device": {"gamma": F(1, 3**20)}}),
    (
        "decoy_bb84",
        "refused cutoffs",
        {"device": {"entropy_cutoff": 2, "source_cutoff": 1}},
    ),
    ("bbm92", "refused domain", _over("bbm92", device={"test_fraction": F(1)})),
    ("bbm92", "refused choice", _over("bbm92", device={"key_bases": "XZ"})),
    (
        "bbm92",
        "refused by the receiver",
        _over("bbm92", device={"alice_half_wave_angle": F(1)}),
    ),
    # "efficiency 0.9 at cutoff 2", at the default window of 2.
    (
        "optical_bb84",
        "refused empty window",
        _over("optical_bb84", device={"photon_cutoff": 2}),
    ),
    (
        "decoy_bb84",
        "refused empty window",
        {"device": {"photon_cutoff": 2, "exact_window": 2}},
    ),
    (
        "bbm92",
        "refused empty window",
        _over("bbm92", device={"alice_photon_cutoff": 2}),
    ),
    # A licensed route with dark counts.
    (
        "bbm92",
        "refused factor assembly",
        _over(
            "bbm92",
            model={"mean_pairs": F(1, 16)},
            device={
                "source_model": "spdc",
                "route": "licensed",
                "alice_dark_count": dict.fromkeys(("H", "V", "D", "A"), F(1, 10**6)),
            },
        ),
    ),
    # A None in a section the caller passes.
    (
        "optical_bb84",
        "null window",
        _over("optical_bb84", device={"exact_window": None}),
    ),
    ("decoy_bb84", "null window", {"device": {"exact_window": None}}),
    (
        "bbm92",
        "null window",
        _over("bbm92", device={"alice_exact_window": None}),
    ),
]

#: The named differences' grid points, with the Python side's decision there
#: (the exception's type), as the gate named them.
INTENDED: dict[tuple[str, str], str] = {
    ("decoy_bb84", "refused cutoffs"): "ValueError",
    ("bbm92", "refused factor assembly"): "ValueError",
    ("optical_bb84", "refused empty window"): "OpticalReceiverError",
    ("decoy_bb84", "refused empty window"): "OpticalReceiverError",
    ("bbm92", "refused empty window"): "OpticalReceiverError",
    ("optical_bb84", "null window"): "RunInputTypeError",
    ("decoy_bb84", "null window"): "RunInputTypeError",
}


def _cases() -> list[tuple[str, str, dict[str, Any]]]:
    return [
        (instance, label, overrides)
        for instance in IDS
        for label, overrides in config_grid(surface_of(instance))
    ] + REFUSALS


CASES = _cases()

#: The run option every point is prepared with. The snapshot's path certified
#: wherever it could; there is no certification option, so none is passed.
CERTIFY: dict[str, Any] = {}

#: Keys of the certified snap's vocabulary, dropped on both sides wherever
#: they occur (module docstring).
_RETIRED_KEYS = frozenset({
    "certified_weight_ceiling",
    "certification",
    "snap_settings",
    "measurement_snaps",
    "instance_snap",
    "emission_record",
    "domination_record",
})

#: The rows adapter's note opens with this in both versions and then
#: describes the snap's vocabulary, which ours lacks (module docstring).
_SNAP_NOTE = "the emitted rows carry the dark-composed family this instance DECLARED"

#: Phrases reworded in the record's strings: the strict option is not an option
#: of certification, and an equation is named by the claim that states it.
_REWORDED: dict[str, str] = {
    "the strict certification option's (req:emission-refusal)":
        "the strict option's (req:emission-refusal)",
    # The squashing map's equation names the claim that states it.
    "eq:flatchannel: ": "prop:flat-instance (I3): ",
}

#: A name of A-SNAP's ``resting_blocks`` binding: origin, block, (detail).
_RESTING_NAME = re.compile(r"^(instance_snap|emission): (.*?) \(.*\)$")

#: The verification rows the domination submodule registered, which ours lacks.
_RETIRED_RULES = frozenset({"domination_weights", "domination_strict"})

#: Keys of a record the snapshot lacks, wherever they occur.
_NEW_KEYS = frozenset({
    "certify_snaps",
    "underlying_cause",
    "entries_not_in_force",
    # The reduction's
    # reference companion record, each snap's handed reference and each snap
    # block's handed kind. No snapped number, weight or declared family moves.
    "reference_companion",
    "handed_reference",
    "handed_reference_kind",
    # The efficiency normalization (record 0.38.0;
    # receiver/detector-imperfections/req:normalization-record): the receiver
    # stage's copy of it. The artefact's efficiency_record is projected to its
    # rows in :func:`_projected`. On the grid every station's efficiencies are
    # one or the station has a probe, except the ENGINE_NAMED edits, so the
    # factor is one and no number moves.
    "efficiency_normalization",
    # The factored loss beside the photon blocks on the channel interface and
    # each of its arms (record 0.39.0;
    # receiver/detector-imperfections/req:loss-before-evaluation), copied
    # from the artefact's normalization record: one on the grid, as above,
    # and null on the declared-finite-POVM interface.
    "factored_loss",
    # The licence's per-entry discharge (record 0.42.0;
    # reductions/req:licence-record): the claim that discharges each entry
    # and the supplier artefact it reads. The entries, their certificates and
    # the record-wide supplier fact and version are compared as before.
    "discharge_per_entry",
    # Why a reductions artefact's A-RECV row is absent (record 0.44.0;
    # reductions/req:recv-row-provenance); empty on every point here, which
    # _check_recv_row checks.
    "receiver_row_omitted_on_provenance",
})

#: Keys the snapshot lacks, by the record object that holds them (the last
#: path segment that names a container).
_ADDED_KEYS: dict[str, frozenset[str]] = {
    "measurement_snap": frozenset({"weight_carried"}),
    "measurement_snap_block": frozenset({"group", "group_fix"}),
    "instance_snap_block": frozenset({"group", "reference_kind"}),
    "instance_snap": frozenset({"pair_readings"}),
    "resting_block": frozenset({"group", "fix"}),
    "assumption": frozenset({"groups"}),
    "domination_record": frozenset({"added_sector_labels"}),
    # The receiver artefact's own ledger in the receiver stage (record
    # 0.44.0), checked by _check_recv_row against its `assumptions` map.
    "receiver_construction": frozenset({"assumption_ledger"}),
}

#: The numeric edits at which the engine's decisions move a preparation.
ENGINE_NAMED: frozenset[tuple[str, str]] = frozenset(
    (instance, label)
    for instance in ("optical_bb84", "decoy_bb84", "bbm92")
    for label in ("edit 1", "edit 2")
)


#: The grid points whose uncertified blocks the snapshot's procedure snapped.
PROCEDURE_NAMED: frozenset[tuple[str, str]] = frozenset({("optical_bb84", "edit 0")})


def _uncertified_blocks(value: Any) -> list[dict[str, Any]]:
    """Every uncertified block of a measurement snap, at any depth."""
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get("status") == "uncertified" and "steps" in value:
            found.append(value)
        for item in value.values():
            found += _uncertified_blocks(item)
    elif isinstance(value, list):
        for item in value:
            found += _uncertified_blocks(item)
    return found


#: Binding names reworded since the snapshot, old to new (module docstring).
_RENAMED_BINDINGS: dict[str, str] = {
    # (The snapshot's "Bob's device enters through one POVM" names the
    # station's party: :data:`_PARTY_NAMED_BINDINGS`, per station, in
    # :func:`_r2_named`.)
    "one POVM, one declared model, one squashing channel":
        "the measuring party's physical POVM",
}

#: Emitted version pins moved since the snapshot, old to new (module
#: docstring).
_MOVED_PINS: dict[str, str] = {
    "reductions@0.13.0": "reductions@0.21.0",
    "transmitter@0.8.0": "transmitter@0.13.0",
    "receiver@0.4.0": "receiver@0.9.0",
    "snapped_measurement_uncertified": "snapped_measurement",
    "strict_certification": "strict_snaps",
}

#: Keys renamed after the snapshot, old to new (module docstring).
_RENAMED_KEYS: dict[str, str] = {"strict_certification": "strict_snaps"}


def _check_no_eve_dim(value: Any) -> None:
    """No ledger of ours carries A-EVE-DIM (``meat-core/ass:eve-dim`` superseded)."""
    if isinstance(value, dict):
        if value.get("assumption_id") == "A-EVE-DIM":
            raise AssertionError(f"an A-EVE-DIM row: {value}")
        for item in value.values():
            _check_no_eve_dim(item)
    elif isinstance(value, list):
        for item in value:
            _check_no_eve_dim(item)


def _check_snapshot_eve_dim_binds_nothing(value: Any) -> None:
    """Every snapshot A-EVE-DIM row :func:`_projected` drops binds nothing."""
    if isinstance(value, dict):
        if value.get("assumption_id") == "A-EVE-DIM":
            assert value.get("constrains") == {}, value
            assert value.get("inherited") == [], value
        for item in value.values():
            _check_snapshot_eve_dim_binds_nothing(item)
    elif isinstance(value, list):
        for item in value:
            _check_snapshot_eve_dim_binds_nothing(item)


def _check_recv_row(value: Any) -> None:
    """Check that the two 0.44.0 keys say what the floating-point run implies.

    Every omission list is empty, and a ledger beside one carries A-RECV
    (the floating-point weight keeps the row, req:recv-row-provenance (iv));
    a receiver stage's ledger names its ``assumptions`` keys, in order.
    """
    if isinstance(value, dict):
        if "receiver_row_omitted_on_provenance" in value:
            assert value["receiver_row_omitted_on_provenance"] == [], value[
                "receiver_row_omitted_on_provenance"
            ]
            if "assumption_ledger" in value:
                ids = {row["assumption_id"] for row in value["assumption_ledger"]}
                assert "A-RECV" in ids, ids
        receiver = value.get("receiver_construction")
        if isinstance(receiver, dict) and "assumption_ledger" in receiver:
            ledger = receiver["assumption_ledger"]
            keys = receiver.get("assumptions")
            if ledger is None:
                assert keys is None
            else:
                assert [row["machine_key"] for row in ledger] == list(keys)
        for item in value.values():
            _check_recv_row(item)
    elif isinstance(value, list):
        for item in value:
            _check_recv_row(item)


def _check_a_const(value: Any) -> None:
    """Every reductions ledger carries A-CONST exactly beside a non-empty list."""
    if isinstance(value, dict):
        if "assumption_ledger" in value and "constraint_list" in value:
            ids = {row["assumption_id"] for row in value["assumption_ledger"]}
            assert ("A-CONST" in ids) == bool(value["constraint_list"]), ids
        for item in value.values():
            _check_a_const(item)
    elif isinstance(value, list):
        for item in value:
            _check_a_const(item)


#: Values of renamed bindings reworded with them, keyed by the new name: the
#: old value and the new one (module docstring).
_REVALUED_BINDINGS: dict[str, tuple[str, str]] = {
    "the measuring party's physical POVM":
        ("declared", "one for every round, no memory across rounds"),
}


def _retired_rows(key: str, item: Any) -> Any:
    """Drop the ceiling's input row and the domination verification rows."""
    if key == "input_preparation" and isinstance(item, list):
        return [
            row
            for row in item
            if not (isinstance(row, dict) and row.get("site") in _RETIRED_KEYS)
        ]
    if key == "rules" and isinstance(item, list):
        return [
            row
            for row in item
            if not (isinstance(row, dict) and row.get("rule") in _RETIRED_RULES)
        ]
    return item


#: The artefact kinds whose ids carry a digest of content this file names as
#: moved (each id is compared as its kind alone). ``transmitter_artifact``:
#: its untrusted-mode ledger has no A-ENS.
_DIGESTED: tuple[str, ...] = (
    "reduction_chain:",
    "declaration:",
    "receiver_artifact:",
    "transmitter_artifact:",
)

#: The station bindings that name the station's party, as the snapshot spells
#: them after :data:`_RENAMED_BINDINGS` and :data:`_REVALUED_BINDINGS`, each with
#: the template its party's name fills.
_PARTY_NAMED_BINDINGS: dict[str, str] = {
    "Bob's device enters through one POVM":
        "{party}'s device enters through one POVM",
    "the measuring party's physical POVM": "{party}'s physical POVM",
}
_PARTY_NAMED_VALUES: dict[str, str] = {
    "the instance's declared party's own": "the systems {party}'s station measures",
}
_PARTY_NAMES: dict[str, str] = {"A": "Alice", "B": "Bob"}


def _r2_named(ours: Any, expected: Any) -> Any:
    """Return the snapshot with the party-role engine changes applied.

    Three things differ in a preparation record, each checked here to be the
    rule before it is applied:

    * the transmitter emits A-ENS (``source_ensemble``) in trusted-source mode
      only: the snapshot's untrusted artefact loses that row and its binding;
    * a station's reductions ledger carries A-PROBE only where its setting set
      has two values or more (the snapshot's row binds one ``q_t`` per
      setting), and A-TSM only where it does or a public choice is applied at
      its factor (no ``choice_weightings`` entry names it in our record);
    * the A-MEAS, A-ROUND-SQ and A-SEQ bindings name the station's party.
    """
    if not (isinstance(ours, dict) and isinstance(expected, dict)):
        return expected
    mine, theirs = ours.get("record"), expected.get("record")
    if not (isinstance(mine, dict) and isinstance(theirs, dict)):
        return expected
    theirs = copy.deepcopy(theirs)
    transmitter = theirs.get("transmitter_artifact")
    ours_transmitter = mine.get("transmitter_artifact")
    if (
        isinstance(transmitter, dict)
        and isinstance(ours_transmitter, dict)
        and "source_ensemble" in transmitter.get("assumption_ledger", ())
        and "source_ensemble" not in ours_transmitter.get("assumption_ledger", ())
    ):
        assert transmitter.get("alice_marginal") is None, "A-ENS left a trusted run"
        transmitter["assumption_ledger"] = [
            key for key in transmitter["assumption_ledger"] if key != "source_ensemble"
        ]
        transmitter.get("assumption_bindings", {}).pop("source_ensemble", None)
    weighted = {
        str(entry.get("factor"))
        for entry in (mine.get("compiled", {}).get("public", {})
                      .get("choice_weightings") or ())
    }
    for station, ours_station in zip(
        theirs.get("stations") or (), mine.get("stations") or (), strict=True
    ):
        party = _PARTY_NAMES.get(str(station.get("party")), "Bob")
        reduction = station.get("reduction") or {}
        ours_reduction = ours_station.get("reduction") or {}
        present = {
            row["assumption_id"]
            for row in ours_reduction.get("assumption_ledger", ())
        }
        rows = []
        for row in reduction.get("assumption_ledger", ()):
            identifier = row["assumption_id"]
            if identifier == "A-PROBE" and identifier not in present:
                assert len(row["constrains"]) == 1, row
                continue
            if identifier == "A-TSM" and identifier not in present:
                assert "A-PROBE" not in present
                assert str(station.get("factor")) not in weighted
                continue
            row = {
                **row,
                "constrains": {
                    _PARTY_NAMED_BINDINGS.get(name, name).format(party=party): (
                        _PARTY_NAMED_VALUES.get(value, value).format(party=party)
                        if isinstance(value, str)
                        else value
                    )
                    for name, value in row["constrains"].items()
                },
            }
            rows.append(row)
        if "assumption_ledger" in reduction:
            reduction["assumption_ledger"] = rows
    return {**expected, "record": theirs}


def _projected(value: Any, role: str = "") -> Any:
    """Return ``value`` with the keys the snapshot lacks and chain digests dropped."""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            item = _retired_rows(key, item)
            if key == "input_preparation" and item == []:
                continue
            if key == "efficiency_record" and isinstance(item, dict):
                # Record 0.38.0: the rows beside the normalization; the
                # snapshot's record is the rows alone. Record 0.42.0: a row's
                # declared loss parameter is ``value``, the snapshot's
                # ``transmittance``; the number is the same.
                item = [
                    {
                        ("transmittance" if name == "value" else name): entry
                        for name, entry in row.items()
                    }
                    for row in item["rows"]
                ]
            if key == "choice_weighting" and role == "":
                # One entry per
                # weighted factor, naming the factor and no party.
                out["choice_weightings"] = [] if item is None else [{
                    name: entry for name, entry in _projected(item).items()
                    if name != "party"
                }]
                continue
            if key == "note" and str(item).startswith(_SNAP_NOTE):
                item = _SNAP_NOTE
            if (
                key == "solver"
                and role == ""
                and isinstance(item, dict)
                and "gap_tolerance" in item
            ):
                # Record 0.43.0: an unchosen gap target is not written; the
                # snapshot's flat block always wrote it, as null.
                assert item["gap_tolerance"] is None, item
                item = {k: v for k, v in item.items() if k != "gap_tolerance"}
            if (
                key in _ADDED_KEYS.get(role, frozenset())
                or key in _NEW_KEYS
                or key in _RETIRED_KEYS
            ):
                continue
            if role == "domination_record" and key == "instance_snap":
                child = "instance_snap"
            elif role == "domination_record" and key == "resting_blocks":
                child = "resting_block"
            elif role == "domination_record" and key == "assumption":
                child = "assumption"
            elif key == "instance_snap":
                child = "instance_snap"
            elif key == "domination_record":
                child = "domination_record"
            elif role == "instance_snap" and key == "blocks":
                child = "instance_snap_block"
            elif role == "measurement_snap" and key == "blocks":
                child = "measurement_snap_block"
            elif key == "measurement_snaps":
                child = "measurement_snap"
            elif key == "receiver_construction" and role == "":
                child = "receiver_construction"
            else:
                child = ""
            name = _RENAMED_BINDINGS.get(key, _RENAMED_KEYS.get(key, key))
            projected = _projected(item, child)
            if name in _REVALUED_BINDINGS:
                old_value, new_value = _REVALUED_BINDINGS[name]
                if projected == old_value:
                    projected = new_value
            if key == "rows_adaptation" and projected == {}:
                projected = None
            out[name] = projected
        if ("residual" in out or "residual_id" in out) and isinstance(
            out.get("value"), float
        ):
            # A residual's value is rounding noise (order 1e-16, set by the
            # BLAS kernel's last bit): whether it lies within its tolerance is
            # compared, not its digits.
            out["value"] = abs(out["value"]) <= out["tolerance"]
        for prefix in _DIGESTED:
            if str(out.get("id", "")).startswith(prefix):
                out["id"] = f"{prefix}*"
                out.pop("digest", None)
        if isinstance(out.get("assumption_ledger"), list):
            out["assumption_ledger"] = [
                row
                for row in out["assumption_ledger"]
                if not (
                    isinstance(row, dict) and row.get("assumption_id") == "A-EVE-DIM"
                )
            ]
        if "assumption_ledger" in out and out.get("constraint_list") == []:
            out["assumption_ledger"] = [
                row
                for row in out["assumption_ledger"]
                if not (isinstance(row, dict) and row.get("assumption_id") == "A-CONST")
            ]
        return out
    if isinstance(value, list):
        return [_projected(item, role) for item in value]
    for prefix in _DIGESTED:
        if isinstance(value, str) and value.startswith(prefix):
            return f"{prefix}*"
    if isinstance(value, str):
        for before, after in _REWORDED.items():
            value = value.replace(before, after)
        # A-SNAP's resting_blocks binding names each block with a detail in
        # the snapshot's vocabulary ("uncertified (above_ceiling)") or ours
        # ("reference handed"): the block is compared, the detail is not.
        value = _RESTING_NAME.sub(r"\1: \2", value)
        return _MOVED_PINS.get(value, _RENAMED_BINDINGS.get(value, value))
    return value


#: The receiver's floating-point evaluations: each photon-number block's
#: elements and each port's Gram matrix, entries of modulus at most one.
_FLOATING_POINT_KEYS = frozenset({"photon_blocks", "port_grams"})

#: How far a floating-point entry may lie from the snapshot's: four ulps of
#: one, the entries' largest modulus (the decoy registry's freeze allows four
#: ulps likewise). The BLAS kernel, picked by CPU at run time, sets the last
#: bits: on a Linux x86_64 runner an entry the snapshot holds as 0.0 comes out
#: of order 1e-50, another one ulp away (harness/PITFALLS.md).
_ROUNDING = 4 * math.ulp(1.0)


def _within_rounding(ours: Any, snapshot: Any, inside: bool = False) -> Any:
    """Return ``ours``, each floating-point entry within rounding set to the snapshot's.

    Only under :data:`_FLOATING_POINT_KEYS`; every other value, and an entry
    farther than :data:`_ROUNDING`, is left as it is, so the comparison
    still shows it.
    """
    if isinstance(ours, dict) and isinstance(snapshot, dict):
        return {
            key: (
                _within_rounding(
                    item, snapshot[key], inside or key in _FLOATING_POINT_KEYS
                )
                if key in snapshot
                else item
            )
            for key, item in ours.items()
        }
    if (
        isinstance(ours, list)
        and isinstance(snapshot, list)
        and len(ours) == len(snapshot)
    ):
        return [
            _within_rounding(item, theirs, inside)
            for item, theirs in zip(ours, snapshot, strict=True)
        ]
    if (
        inside
        and isinstance(ours, float)
        and isinstance(snapshot, float)
        and abs(ours - snapshot) <= _ROUNDING
    ):
        return snapshot
    return ours


def _domination_records(value: Any) -> list[dict[str, Any]]:
    """Every ``domination_record`` at any depth of a preparation record."""
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "domination_record" and isinstance(item, dict):
                found.append(item)
            else:
                found += _domination_records(item)
    elif isinstance(value, list):
        for item in value:
            found += _domination_records(item)
    return found


def _links(value: Any) -> list[str]:
    """Every link kind of every reduction chain, at any depth."""
    found: list[str] = []
    if isinstance(value, dict):
        if "link_id" in value and "kind" in value:
            found.append(str(value["kind"]))
        for item in value.values():
            found += _links(item)
    elif isinstance(value, list):
        for item in value:
            found += _links(item)
    return found


def _floating_point_receiver(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Make the receiver emit its floating-point weight, after checking the change.

    Under ``receiver/req:rigorous-weight`` an exact-route receiver emits the
    enclosed weight rounded down, invokes A-EIG at no rigorous setting and
    labels itself ``rigorous``, and the weight flows into the declared POVM,
    the reductions and the key. The snapshot froze the floating-point
    evaluation, which still runs. This wraps the one site that swaps the
    weight (``construct._rigorous``): it checks the named difference -- the
    enclosed weight lies at most rounding below the floating-point one and at
    most ``eps_eig`` (1e-3) above it -- and hands the floating-point setting
    on, so the rest of the preparation is compared whole. The returned list
    holds the weights checked, so a case can see the wrap was exercised.
    """
    checked: list[float] = []
    real = construct._rigorous

    def wrapped(bound: Any, evaluated: Any) -> Any:
        swapped = real(bound, evaluated)
        if swapped.evaluation == "rigorous":
            assert bound.weight - 1e-15 <= swapped.weight <= bound.weight + 1.0001e-3
            checked.append(swapped.weight)
        return bound

    monkeypatch.setattr(construct, "_rigorous", wrapped)
    return checked


def _without_evaluation_fields(value: Any) -> Any:
    """Return ``value`` without the rigorous weight's per-setting fields.

    Each is checked to say "floating point" first (the wrap above hands every
    setting on unswapped): ``evaluation`` is ``floating_point`` and the
    fallback reason, the enclosed record and the floating-point weight are
    absent.
    """
    if isinstance(value, list):
        return [_without_evaluation_fields(item) for item in value]
    if not isinstance(value, dict):
        return value
    out = {key: _without_evaluation_fields(item) for key, item in value.items()}
    if "assumption_eig_invoked" in out and "evaluation" in out:
        assert out.pop("evaluation") == "floating_point"
        for key in ("fallback_reason", "enclosed", "floating_point_weight"):
            assert out.pop(key) is None
    return out


#: The claims the receiver names where it carries a factor enclosure.
_FACTOR_CLAIMS: tuple[str, ...] = (
    "receiver/thm:factor-blocks (iii)",
    "receiver/component-catalogue/lem:catalogue-dilations (ii)",
)
_FACTOR_CAUSES = frozenset({
    "probe_conditioned",
    "no_port_dilation",
    "columns_exceed_dimension",
    "enclosed_references_not_used",
})


def _enclosure_digest_without_factors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Form ``enclosures_sha256`` from the entrywise enclosures alone.

    An element's record carries ``factor`` where a factor enclosure is
    carried, and the digest of the enclosures covers it. The wrap drops that
    key, so the snapshot's digest still pins the centres and radii.
    """
    from certiqs_key.foundations.reference import Enclosure

    real = Enclosure.as_record

    def wrapped(self: Enclosure) -> dict[str, object]:
        record = real(self)
        record.pop("factor", None)
        return record

    monkeypatch.setattr(Enclosure, "as_record", wrapped)


def _without_factor_form(value: Any) -> Any:
    """Return ``value`` without the receiver's factor-form fields.

    Each is checked first: every offered block records, per letter, a carried
    factor enclosure with its columns and largest radius, or one of the
    causes; and the reference's establishing claims end with the two factor
    claims exactly where some block carries one.
    """
    if isinstance(value, list):
        return [_without_factor_form(item) for item in value]
    if not isinstance(value, dict):
        return value
    out = {key: _without_factor_form(item) for key, item in value.items()}
    offered = out.get("offered")
    identity = out.get("identity")
    if isinstance(offered, list) and isinstance(identity, dict):
        carried = False
        for block in offered:
            for offer in block.pop("factor_enclosures", {}).values():
                if offer["carried"]:
                    carried = True
                    assert offer["columns"] >= 0 and F(offer["largest_radius"]) >= 0
                else:
                    assert offer["cause"] in _FACTOR_CAUSES, offer
        claims = list(identity["establishing_claims"])
        if carried:
            assert tuple(claims[-len(_FACTOR_CLAIMS):]) == _FACTOR_CLAIMS, claims
            claims = claims[: -len(_FACTOR_CLAIMS)]
        assert not set(_FACTOR_CLAIMS) & set(claims), claims
        identity["establishing_claims"] = claims
    return out


def _check_engine_named(ours: dict[str, Any], expected: dict[str, Any]) -> None:
    """Check the named difference: what the snapshot carried, we do not.

    The snapshot either carried a positive weight by added flag sectors or
    dropped a certified block's weight (all or nothing); ours forms no
    domination record and no domination link at all.
    """
    before = _domination_records(expected)
    assert before
    assert any(
        record.get("added_sector_labels")
        or any(
            "req:domination-certificate (iii)" in str(block.get("cause"))
            for block in record.get("resting_blocks") or []
        )
        for record in before
    ), before
    assert _domination_records(ours) == []
    assert "family-dominating" not in _links(ours)


@pytest.mark.parametrize("instance", IDS)
def test_the_snapshot_holds_exactly_the_grid(instance: str) -> None:
    """Every point of the grid is in the snapshot and nothing else is."""
    labels = {label for name, label, _ in CASES if name == instance}
    assert labels == set(_snapshot(instance)["cases"])


#: Parameters added to a template after the snapshot, by instance: the factored
#: loss of each optical station
#: (receiver/detector-imperfections/req:efficiency-normalization), with no
#: default, so that a configuration that does not set it prepares what it did.
PARAMETERS_ADDED: dict[str, frozenset[str]] = {
    "optical_bb84": frozenset({"efficiency_normalization"}),
    "decoy_bb84": frozenset({"efficiency_normalization"}),
    "bbm92": frozenset(
        {"alice_efficiency_normalization", "bob_efficiency_normalization"}
    ),
}


#: The snapshot's one PBS parameter, and the two that replaced it.
_PBS_EXTINCTION = "pbs_extinction"
_PBS_LEAKS: tuple[str, str] = ("pbs_leak_reflected", "pbs_leak_transmitted")


def _split_pbs(value: Any) -> Any:
    """Read the snapshot through the PBS split and the whole-path ports.

    Valid only at a perfect PBS, so every value it splits is checked to be 0.
    """
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and key.endswith(_PBS_EXTINCTION):
                assert str(item) == "0", (key, item)
                prefix = key[: -len(_PBS_EXTINCTION)]
                for leak in _PBS_LEAKS:
                    out[prefix + leak] = item
            elif key == "port_map" and isinstance(item, list):
                out[key] = [_whole_path(port) for port in item]
            else:
                out[key] = _split_pbs(item)
        return out
    if isinstance(value, list):
        return [_split_pbs(item) for item in value]
    return value


def _whole_path(port: Any) -> Any:
    """Return a single-mode port reading both polarization modes of its path."""
    modes = port.get("modes") if isinstance(port, dict) else None
    if not (isinstance(modes, list) and len(modes) == 1):
        return port
    path = str(modes[0]).rsplit("_", 1)[0]
    return {**port, "modes": [f"{path}_H", f"{path}_V"]}


def _split_static(ours: list[dict[str, Any]], theirs: list[dict[str, Any]]) -> None:
    """Check the leak rows against the extinction row, then drop all three."""
    for row in [r for r in theirs if r["name"].endswith(_PBS_EXTINCTION)]:
        prefix = row["name"][: -len(_PBS_EXTINCTION)]
        names = {prefix + leak for leak in _PBS_LEAKS}
        leaks = [r for r in ours if r["name"] in names]
        assert {r["name"] for r in leaks} == names
        at = theirs.index(row)
        assert {ours.index(r) for r in leaks} == {at, at + 1}
        for leak in leaks:
            assert {k: v for k, v in leak.items() if k not in ("name", "meaning")} == {
                k: v for k, v in row.items() if k not in ("name", "meaning")
            }
            ours.remove(leak)
        theirs.remove(row)


def _eve_dim_rows(value: Any) -> int:
    """Count the A-EVE-DIM rows in a snapshot value."""
    if isinstance(value, dict):
        own = 1 if value.get("assumption_id") == "A-EVE-DIM" else 0
        return own + sum(_eve_dim_rows(item) for item in value.values())
    if isinstance(value, list):
        return sum(_eve_dim_rows(item) for item in value)
    return 0


def test_the_snapshot_s_a_eve_dim_rows_bind_nothing() -> None:
    """The rows :func:`_projected` drops exist and bind nothing, so no value moves."""
    snapshots = [_snapshot(instance) for instance in IDS]
    assert sum(_eve_dim_rows(snapshot) for snapshot in snapshots) > 0
    for snapshot in snapshots:
        _check_snapshot_eve_dim_binds_nothing(snapshot)


@pytest.mark.parametrize("instance", IDS)
def test_the_static_surface_is_the_snapshot_s(instance: str) -> None:
    surface = surface_of(instance)
    static = copy.deepcopy(_snapshot(instance)["static"])
    added = PARAMETERS_ADDED.get(instance, frozenset())
    assert added <= {spec.name for spec in surface.PARAMETERS}
    payload = json.loads(
        json.dumps(
            {
                "descriptor": surface.DESCRIPTOR.as_payload(),
                "parameters": [
                    spec.as_payload()
                    for spec in surface.PARAMETERS
                    if spec.name not in added
                ],
                "presets": [preset.as_payload() for preset in surface.PRESETS],
            }
        )
    )
    _split_static(payload["parameters"], static["parameters"])
    assert payload == static


@pytest.mark.parametrize(
    ("instance", "label", "overrides"),
    CASES,
    ids=[f"{instance}-{label}" for instance, label, _ in CASES],
)
def test_the_preparation_is_the_snapshot_s(
    instance: str,
    label: str,
    overrides: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The configuration and the preparation (or refusal) of the replaced code."""
    expected = _split_pbs(_snapshot(instance)["cases"][label])
    named = INTENDED.get((instance, label))
    if named is not None:
        assert expected["raised"][0] == named, expected["raised"]
        return
    _floating_point_receiver(monkeypatch)
    _enclosure_digest_without_factors(monkeypatch)
    ours = _without_factor_form(
        _without_evaluation_fields(
            _maker().outcome_of(surface_of(instance), {**overrides, **CERTIFY})
        )
    )
    _check_a_const(ours)
    _check_recv_row(ours)
    _check_no_eve_dim(ours)
    _check_snapshot_eve_dim_binds_nothing(expected)
    if (instance, label) in ENGINE_NAMED:
        _check_engine_named(ours, expected)
        return
    if (instance, label) in PROCEDURE_NAMED:
        before = _uncertified_blocks(expected)
        assert any("round-down" in block["steps"] for block in before)
        assert not _uncertified_blocks(ours)
    projected = _projected(ours)
    snapshot = _r2_named(projected, _projected(expected))
    assert _within_rounding(projected, snapshot) == snapshot


def test_the_receiver_wrap_checks_an_enclosed_weight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The wrap is exercised: bbm92's default preparation has a rigorous setting."""
    checked = _floating_point_receiver(monkeypatch)
    overrides = next(o for i, label, o in CASES if (i, label) == ("bbm92", "defaults"))
    _maker().outcome_of(surface_of("bbm92"), {**overrides, **CERTIFY})
    assert checked
