# Numerical inputs before the exact core

Every instance's surface accepts integers, finite floats, Decimals, Fractions
and numeric strings at fields its parameter table marks numeric. Use `default_config(...)`, then `preparation(config)` or the callable
returned by `runner(...)`. Numeric-looking choice names remain names. Generic
`RunConfig.from_inputs` parses device strings only when the caller supplies
`numeric_device_fields`; instances derive that list from their parameter table.

`certiqs_key.runs.inputs` owns this adapter. Core modules receive exact
declarations and no numerical tolerance. Exactly admissible binary64
probability families, including their exactly representable partial sums, pass
through unchanged even when finer than the nominal lattice. A configuration or
result payload carries no empty preparation field.

## Probability admission and preparation

Policy `binary64_nearest_even_cells_v1` is a front-end representation policy.
Each finite float probability denotes the nearest-even rounding cell bounded
by the exact midpoints to its predecessor and successor, clipped to [0, 1].
The bounds are Fractions, so half a subnormal ULP does not underflow. Cells at
powers of two are asymmetric. Midpoint endpoints belong to the float exactly
when its significand is even. A declared zero, including negative zero, is
fixed at zero rather than given a positive uncertainty interval. Exact numeric
strings, Decimals, Fractions and integers have singleton cells.

The exact input normalization defect must be within `declared_tolerance`, or
1 must belong to the sum of those cells. A sum of intervals contains 1 exactly
when some member of their Cartesian product is normalized; at an extreme
endpoint every contributing endpoint must be included. Thus ordinary floats
0.1 and 0.9 are accepted at tau = 0 without claiming their stored values sum
exactly to one. Exact Decimal/Fraction-only mismatches have no representation
allowance. Negative and above-one values are always refused.

After that exact admission decision, the `foundations.snap.snap_family_exact`
algorithm prepares scalar 1-by-1 blocks on the instance's lattice and absorbs
its completeness residue using the shared designated-element rule. This is
one implementation of normalization, not another probability snap algorithm.
The shared routine measures completeness using floating arithmetic; its local
execution guard is `max(declared_tolerance, measured_float_residue)`, recorded
as `shared_snap_guard`. This guard only executes an already admitted scalar
preparation. It changes no admission criterion, user tolerance or core check.
Nested snap records label that local guard `declared_tolerance` according to
the shared snap schema; the outer record carries the actual user declaration.

The resulting vector sums exactly to one. Structural zeros remain zero;
positive support must also survive, or the adapter refuses. In particular,
subnormal positive weights need not be representable on the selected lattice;
they are never silently dropped. A prepared vector need not remain in the
original rounding cells: lattice preparation is a separate recorded change.

## Records, replay and bounds

Configuration conversion records retain input type and exact value. This lets
probability preparation recover float provenance after conversion to Fraction
and after `RunConfig.to_payload` / `from_payload`. `with_` discards evidence
for any replaced section; a newly supplied exact Fraction cannot borrow the
replaced float's representation allowance. A numerical-looking device name uses
an optional `device_name_fields` discriminator in serialized configurations.

A probability record contains original and binary64-converted values, rounding
cells, the exact normalization defect and interval, the admission route, the
user tolerance, local snap guard, lattice exponent, shared snap records and
signed exact total/conversion displacements. Instance preparations and runner
outcomes carry these under `rows_adaptation.input_preparation`; configurations
and run records retain nonempty conversion evidence as `input_preparation`.
When calling `record_run`, pass the same user configuration supplied to the
runner: its source inputs are retained, while the outcome's preparation record
identifies the exact values used by the core. A prepared execution may have a
different execution digest from that source configuration.

`prepare_bound` treats all inputs by their exact stored numeric meaning and
rounds lower bounds downward and upper bounds upward on the chosen dyadic
lattice. Float rounding cells do not relax a bound. Every displacement is
recorded. A small displacement is not a continuity bound on the resulting key
rate; device-characterization uncertainty and proof-relevant perturbation
accounting remain separate obligations.
