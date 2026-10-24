# Using and adding protocol instances: developer notes

How to drive the instances from Python and how to add one. The overview for
someone choosing and running an instance is [README.md](README.md).

An instance supplies protocol data, a device declaration and an honest statistics
model. The compiler, reductions and key-rate engine decide their own conditions.
Imports point downwards: share apparatus code in `instances/common/`, and keep
protocol choices in each instance package.

Four instances are protocol documents: `bb84`, `optical_bb84`, `decoy_bb84`
and `bbm92` are each a `protocol.yaml` (the packaged template) and a
`surface.py` of a few lines that loads it with the packaged loader
(`instances.declared.load_packaged`) and exposes the surface below; the
document layer, `instances/declared/`, lowers it to the modules' constructors
(its format guide is [declared/README.md](declared/README.md)).
bb84 also keeps `specification.py` and `parameters.yaml`, the protocol
compiler's worked declaration, which its template is held equal to.

Some strings the templates write into records name modules that do not
exist: `instances.optical_bb84.declare` and `instances.decoy_bb84.declare`
(the stations' `declared_by`), `instances.decoy_bb84.source` (the decoy
source's record label) and `instances.bbm92.spdc.port_grams` (the SPDC model's
snap site). They are kept so that a record of the same declaration does not
change; they are labels, not import paths.

These packages are available from a checkout, not installed: installing the
clone (`pip install -e .`) packages `src/` alone. Run the
examples from the repository root, or add the checkout to `sys.path`. This
keeps the generic top-level name `instances` out of `site-packages`; the engine
can still consume any independently supplied instance. Each package has a
`NOTES.md` with its files, invariants and tests; shared apparatus code (the
passive receiver, its three routes and Bob's optional probe source) is in
`common/`, and so are the honest models (`common/honest/`, a library by name
with one interface, which a protocol document names as well), the
channel-interface builders (`common/channel.py`), the BB84 qubit source
part (`common/sources.py`), the tagged weak-coherent-pulse source's
preparation and Poisson enclosures (`common/wcp.py`) and the feasibility
witnesses a document's topology picks (`common/witness.py`).

Discover the supported interfaces without importing a particular protocol:

```python
from instances import discover, surface_of
from certiqs_key.runs import preparation_record

surfaces = discover()
surface = surface_of("bb84")
config = surface.default_config()
prepared = surface.preparation(config)
record = preparation_record(prepared)
```

Preparation runs the device and compiler stages without an optimization oracle.
Its outcome can be a refusal, with the responsible module's reason. A successful
preparation records the declared data, conversion and snapping displacement,
assumptions and planned remaining stages. Ordinary numeric inputs, including
decimal and fractional values, are prepared through shared helpers before exact
core validation. The record describes the prepared declaration; a small input
displacement alone is not a bound on key-rate displacement.

Every instance also exports `receiver_requests(config)`, optional and outside
the uniform surface: the receiver requests `preparation` would construct, built without
constructing them (none for Band A). The facade reads it to estimate a
preparation's time before running it (`runs/facade/estimate.py`); an instance
without it is estimated `unknown`.

`default_config` accepts `Decimal`, `Fraction` and numeric strings such as
`"1/3"`; custom configuration callers can use `RunConfig.from_inputs`.
Probability families are prepared together to preserve exact normalization,
and already admissible values are retained. Configuration conversions appear
in `input_preparation`; declaration conversions appear under
`rows_adaptation.input_preparation`, with original/prepared values and exact
displacements. The declared tolerance controls normalization repair.

## Input errors

An input the run tier refuses before anything runs raises a
`certiqs_key.runs.errors.RunInputError`. Its `reason` is a stable code from
one closed vocabulary, `RunInputReason`; `str(error)` is a message for a
person. Word the code; do not parse the message. Each error is also the
builtin named below, so `except KeyError` and `except ValueError` still work,
and `RunConfigError` and `WarmStartFileError` belong to the same family. A
refusal by a module during a run is different: it is returned as an outcome
with that module's own reason, not raised. One such outcome is the run tier's
own checks of a result, at `solve` (`RunRefusalReason`):
`entropy_bound_above_key_ceiling` (`certiqs_key.runs.plausibility`), where the
bound a key length would be computed from exceeds what any key could carry,
so that the accepted statistics contradict the declared model (an outer alpha
search that meets it at any alpha stops and refuses the run as a whole),
and `strict_snaps`, where a run that declares the strict option
would rest on A-SNAP after its search (`certiqs_key.runs.direct_route`).
The same vocabulary names the one evaluation the outer alpha search refuses
itself: `oracle_failure`, recorded as `solve: oracle_failure` in the search's
evaluations, where that alpha's solve stopped on a linear-oracle status that is
neither optimal nor an infeasibility verdict; the search goes on with its
other alphas (`certiqs_key.runs.alpha_search`).

| Code | Builtin | The input refused |
| --- | --- | --- |
| `unknown_parameter` | KeyError | a key the instance's parameter table does not have |
| `missing_parameter` | KeyError | a parameter the instance reads is not declared |
| `wrong_kind` | ValueError | a value of the wrong kind: a name where a number is declared, one number where one per port is |
| `not_an_integer` | ValueError | a non-integral value of an integer parameter |
| `outside_domain` | ValueError | a value outside the parameter's declared domain, or a name not among its choices |
| `port_labels_mismatch` | KeyError | a per-port mapping not keyed by exactly the receiver's port labels |
| `not_a_number` | TypeError | an object that is not a number (a Boolean, a list) where a number is read |
| `unreadable_number` | ValueError | a string that is not a decimal or a fraction, or a zero denominator |
| `not_finite` | ValueError | an infinity or a NaN |
| `outside_binary64` | ValueError | a binary64 field (the tolerance) beyond the binary64 range |
| `probability_family_empty` | ValueError | a probability family with no member |
| `probability_outside_unit_interval` | ValueError | a probability or probability bound outside [0, 1] |
| `normalization_exceeds_tolerance` | ValueError | a probability family whose sum misses one by more than the declared tolerance allows |
| `positive_support_lost` | ValueError | a positive probability too small for the instance's lattice |
| `preparation_argument_invalid` | ValueError | a preparation argument an instance passed (lattice exponent, bound direction, tolerance) |
| `declared_tolerance_absent` | ValueError | no `declared_tolerance` |
| `declared_tolerance_not_binary64` | ValueError | a `declared_tolerance` that is not a float |
| `declared_tolerance_out_of_domain` | ValueError | a `declared_tolerance` outside [0, 1) |
| `endpoint_rule_not_admitted` | ValueError | an `endpoint_rule` statistics does not admit |
| `tail_evaluation_not_admitted` | ValueError | a `tail_evaluation` statistics does not admit |
| `solver_budget_not_positive` | ValueError | `max_iterations` below one |
| `solver_gap_tolerance_not_positive` | ValueError | a `solver.advanced.gap_tolerance` that is not finite and positive |
| `solver_oracle_not_admitted` | ValueError | a `solver.advanced.oracle` choice the solver does not offer |
| `solver_certified_evaluation_not_admitted` | ValueError | a `solver.advanced.certified_evaluation` other than `on`, `off` or `strict` |
| `solver_method_not_admitted` | ValueError | a `solver.method` other than `auto` or `fw`, or a `solver.advanced.method` other than `pairwise`, `factor`, `entropy` or `corrective` |
| `solver_method_set_twice` | ValueError | both `solver.method` and `solver.advanced.method` chosen |
| `solver_key_not_admitted` | ValueError | a `solver` or `solver.advanced` key the settings do not read, among them an expert key (`oracle`, `gap_tolerance`, `warm_start`, `certified_evaluation`) written beside `method` instead of under `solver.advanced` |
| `alpha_search_setting_out_of_domain` | ValueError | an `alpha_search` whose `alpha - 1` interval is not `0 < lower < upper < 1`, whose `coarse_points` is below two or `refine_steps` negative, or that carries a key it does not read |
| `alpha_and_alpha_search_both_set` | ValueError | a configuration that fixes `alpha` and asks for an `alpha_search` |
| `authentication_parameter_out_of_domain` | ValueError | an `eps_auth` outside `[0, 1)` or a `k_auth` that is not a non-negative integer (A-AUTH's run inputs) |
| `snap_setting_out_of_domain` | ValueError | a `reference_enclosure` or `strict_snaps` that is not a Boolean (the snap run parameters) |
| `statistics_check_setting_out_of_domain` | ValueError | a `statistics_check` other than `on` or `off`, or a `min_model_pass_probability` that is not a number in (0, 1] (the check of meat-core/req:unreachable-acceptance-set) |
| `retired_parameter` | ValueError | a configuration payload naming a run parameter the engine does not have: `certify_snaps` or `certified_weight_ceiling` (snap certification is not a run option), or `strict_certification` (spelled `strict_snaps`), or `contradiction_share` (the check reads `min_model_pass_probability`) |
| `warm_start_hash_malformed` | ValueError | a warm-start sha256 that is not 64 lowercase hex characters |
| `warm_start_file_missing` | ValueError | no readable warm-start file at the given path |
| `warm_start_hash_mismatch` | ValueError | a warm-start file whose bytes do not hash to the named seed |
| `warm_start_not_an_iterate` | ValueError | a warm-start file that is not a final iterate of a known format |

## Solving and saving

To solve and save a record, use a fresh bundle directory:

```python
from pathlib import Path
from certiqs_key.runs import record_run, write_record
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

run = surface.runner(QicsSectorChoiOracle(), Path("build/example-bundles"),
                     created_by="example")
outcome = run(config, 0)
write_record(Path("build/example-result.json"),
             record_run(outcome, config, created_by="example"))
```

Read the returned tier, refusal or key-length reason, assumptions and
Frank-Wolfe gap alongside the number. A returned estimate is not a first-order
key-rate bound. Dropped-program objectives and bounds have separate names and
carry their dropped set. See [general records](../runs/general-records.md).

A run solves at `config.alpha`, or at `parameters.alpha` where that is null.
To let the run choose the order, opt into the outer alpha search instead:
`default_config(alpha_search=AlphaSearchSettings(...))` (from
`certiqs_key.runs.config`). The runner then runs the configuration once per
searched alpha, from the honest model and before any data, each run in
`run-NNNN/alpha-KK/`, and returns the best run; its record's solve stage has an
`alpha` child with `searched: true` and every evaluation, and the report says
the order was chosen by the search. Setting both `alpha` and `alpha_search` is
refused. See `certiqs_key.runs.alpha_search`.

A new protocol is best written as a protocol document: a user's own runs
through `instances.declared.load` or the MCP server (a custom document, whose
runs are labelled `declared_<id>`), and a packaged one as
`instances/<id>/protocol.yaml` with a `surface.py` like bb84's. Either way the
surface is the one below and no code of the protocol's own is needed. Write
Python only for what the document format does not cover.

A new instance exports `DESCRIPTOR`, `PARAMETERS`, `PRESETS`, `default_config`,
`preparation` and `runner` in its `surface.py`, and registers its package in
`instances/__init__.py`. The surface tests check this shared interface. Declare
parameters once using the run tier's parameter types; unknown keys must not
silently disappear. A preset is configuration data, not a separate code path.
Its `runner` wraps its one-alpha run in
`certiqs_key.runs.alpha_search.searching_runner`, so the instance gets the
outer alpha search with no code of its own.

Supply a specification directly, or use `DeviceRequests` and a provider that
receives the receiver and reduction artifacts. For two stations use
`MultiDeviceRequests`: its provider receives the ordered `DeviceEmission`
records after both stations emit. Each contains the final prepared reduction
call, so `reductions.factors.assemble_factor_emissions` can assemble the tensor
artifact using supplier-owned operations. Preserve both station ledgers.

Declare channel-interface data that matches the physical source:

- `ChannelInterface` for an explicitly encoded finite system;
- `ModeIntensityChannelInterface` for a mode/intensity source, keeping source
  and receiver cutoffs distinct;
- `BipartiteChannelInterface` for two arms in station order.

Honest providers return joint probabilities per channel use over the declared
acceptance alphabet, including discarded outcomes. They must not return only a
sifted error rate. Record their physical model, parameters and preparation rules
under the test-statistics-model assumption. Validate physical limiting cases
against independently derived targets; keep solver measurements separate from
frozen numerical oracles.
