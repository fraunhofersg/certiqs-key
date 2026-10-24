# The Python instances' last run: a frozen snapshot

**A snapshot, not an oracle.** These files record what the Python instances
bb84, optical_bb84, decoy_bb84 and bbm92 computed on the equivalence gate's
grid at a development commit, the last at which they existed (the instances
are protocol documents now, `instances/<id>/protocol.yaml`). That commit is
not in the public history, so the snapshot cannot be reproduced from this
repository. They pin the code that was replaced, not a correct value:
PRINCIPLES.md §2.3 is not engaged, and no number here is an oracle.

`tests/integration/test_declared_last_python_run.py` holds the templates
against them, preparations only (about 15 seconds).

## What each file holds

One gzip-compressed JSON file per instance, `<instance>.json.gz` (written
with no file name and a zero time, so the same content compresses to the same
bytes):

- `static`: the instance's `DESCRIPTOR`, `PARAMETERS` and `PRESETS` payloads;
- `cases`: per grid point, by the gate's label,
  - `config`: the `default_config(...)` payload, or `null` where
    `default_config` raised;
  - `kind` and `record`: the outcome's type (`Preparation` or
    `SliceRefusal`) and its `preparation_record`; or
  - `raised`: the exception's type name and its `reason` code (empty for a
    builtin).

The grid is the gate's (`tests/support/declared_equivalence.py`,
`config_grid`: the defaults, every preset, every value of every choice
parameter, three numeric edits, the run fields, the snap-certification run
parameters and the partial-section calls) and its refusals beyond it, copied
verbatim into the test.

## The stripping rule

As the gate's: every `wall_time_s`, `elapsed_seconds`,
`preparation_seconds`, `solver_seconds`, `seconds` and `timings` field at any
depth; the `id` and `digest` of a container whose `id` starts with
`key_rate_result:`; every `provenance` block; and `protocol_document` (which
the Python instances recorded as `null` and a template records as its
document).

## How it was made

`make_snapshot.py` beside this file, run from an export of that commit, with
the Python instances present; it is runnable only there. It was run twice
and wrote the same bytes both times. The same run of the gate at that
commit passed in full (101 tests).

## The named differences

At the gate's seven named-difference points (decoy's cutoffs out of order,
bbm92's refused factor assembly, the empty exact window in three instances,
a `null` window in optical_bb84 and decoy_bb84) the snapshot holds the Python
side's exception; the test checks it is the one the gate named and does not
compare the template there (its outcome is
`tests/integration/test_declared_equivalence.py`'s). bbm92's honest-note
difference is in no preparation record.
