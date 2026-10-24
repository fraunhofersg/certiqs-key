# General protocol records

Field-level notes on the run record (`record.json`) that `certiqs_key.runs`
writes; the authoritative shape is `src/certiqs_key/runs/record.schema.json`.
The notes describe the current record shape (`RECORD_SCHEMA_VERSION` in
`src/certiqs_key/runs/record.py`). The key-rate report also reads the older
record schemas its code lists (`SUPPORTED_RECORD_SCHEMA_VERSIONS`,
`src/certiqs_key/runs/report/build.py`; see the last section) and refuses any
other: re-run that record's configuration (`/payload/config`).

## Stations and sources

**Optical source shapes.** A reader inspects
`channel_interface.source_shape` before assuming a finite transmitted basis
and encoding matrix. `mode_and_intensity` records the source intensities and
source cutoff separately from the receiver's photon evaluation cutoff.
`bipartite` records both arms in station order. Neither assigns a fictitious
finite dimension to the physical optical source.

**Each station names itself.** An instance declares on every
`DeviceRequests` of a `MultiDeviceRequests` a `Station`: `factor`, the
measured factor of the compiled declaration its receiver becomes, and
`party`, the party that factor is scoped to. The run tier checks that each
station names one measured factor with that factor's party and that every
measured factor is named by one station, and refuses the composition
(`SliceAssemblyError`) otherwise. The record's `stages.stations[i]` carries
`factor` and `party` beside `index`. Order is not the pairing: read the
factor. The factor, not the party, is the key, because the declaration admits
two measured factors of one party.

`MultiDeviceRequests` prepares each station through the same receiver,
declaration and reduction stages as the single-station path. Its provider sees
the ordered `DeviceEmission` records only after all stations have emitted.
Each record includes the final prepared reduction call, including requested
carried operators, so the reductions module can assemble its own factor
emission and licence. Instances do not invent that licence.

Completed run and preparation records carry every station's supplier artifacts
and preparation displacement. The assumption manifest identifies each station;
the contract pins identify the consumed versions. The operator bundle stores
factor families and the declared transcript, never a rounded product POVM.

**Per-station stages name their station.** Every `composition_flow` stage
carries `station`: the factor on the three device-prologue stages of a
multi-station route, `null` everywhere else and on every stage of a
single-device route. A preparation's planned list and a refusal's
`not_executed` tail list the prologue once per station. The receiver and
reduction artefacts of station `i` carry the `record_key`s
`payload.stages.stations[i].receiver` and `payload.stages.stations[i].reduction`,
which resolve. The Mermaid node of a
per-station stage reads `receiver_construction [bob_station] (receiver) -- ok`.
`ParameterSpec.station` names the same factor on an instance's per-station
parameters (BBM92's `alice_*` and `bob_*` rows, the two transmittances
included) and is `null` on the rest.

**Bundle digests cover the operators.** The `bundle` and `docked_declaration`
artefact digests hash the manifest and, per dataset, each array's layout,
shape, dtype and the sha256 of its little-endian C-order bytes, so two
declarations that differ only in operator entries do not share them.

**Probe-free labels.** A joint receiver outcome `(y, t)` is spelled by one
function, `certiqs_key.reductions.inputs.outcome_label`: `y,t` in general, and
`y` alone when the receiver declares exactly the probe-off setting
(`T = {off}`). The probe setting is an add-on, so a probe-free receiver's
target alphabet, readouts, key-map keys and flag sector names carry no `,off`:
BBM92's stations emit `H`, `V`, `nc`, ..., Alice's weighted readouts are
`(H,gen)`, and a joint label is `(H,gen)__V`. A probe-bearing receiver keeps
`y,t`.

## Receivers

**Receiver route.** `stages.receiver_construction.receiver_route` says how
the receiver was given: `port-grams`, `instrument-matrix`, `element-graph`,
`declared-finite-povm` (Band A) or `per-station`; each `stages.stations[i]`
names its own. The preparation record's `receiver_construction` carries it
too.

**Factored loss.** `factored_loss` stands beside every receiver's
`photon_blocks_basis`: on the finite interface, on `arm` and on each of
`arms`, the exact `p/q` the receiver artefact's
`efficiency_record.normalization` records (null on the declared-finite-POVM
interface). Where it is below one the blocks are the normalized station's, and
a consumer computing statistics from them first applies the pure-loss channel
of that transmittance to the channel modes
(`receiver/detector-imperfections/req:loss-before-evaluation`).

**Efficiency normalization.** A receiver's efficiency normalization is
recorded as applied exactly where its factored loss is below one. A factor of
one, declared or by default, is the not-applied reason `factor_one`;
`factor_declared` says which
(`receiver/detector-imperfections/req:normalization-record`). Each
`efficiency_record.rows` entry carries its declared loss parameter as `value`,
read as the parameter its `element` names
(`receiver/detector-imperfections/req:efficiency-record`).

**The receiver's own ledger.** The record carries each receiver artefact's own
assumption ledger, row for row with the values each row constrains: on the
single-receiver route under `stages.receiver_construction.assumption_ledger`;
on a multi-station run under each `stations[i].receiver.assumption_ledger`,
that station's artefact's own, while
`stages.receiver_construction.assumption_ledger` is null, as it is on the
declared-finite-POVM route.

## Assumptions

**The attack-set licence.** Every reduction artefact's attack-set licence
names what discharges each constraint entry (`discharge_per_entry`:
`reductions/req:licence-record`): the claim that establishes its certificate
and, where that claim reads the receiver's claims, the supplier fact (A-RECV)
and the receiver artefact's version. The record-wide
`discharging_receiver_fact` and `receiver_spec_version` are null where no
entry's discharge reads a supplier fact.

**A-RECV** (`reductions/ass:recv`) comes from the reductions artefacts alone.
The compiler's `assumption_ledger` carries no A-RECV row on any route (the
protocol-compiler interface's `assumption_ledger.a_recv_not_emitted_note`).
Every reduction artefact carries `receiver_row_omitted_on_provenance` (in a
station's machine record and in `stages.reduction`): empty where its ledger
carries the A-RECV row, and the receiver artefact's version where
`reductions/req:recv-row-provenance` omitted it. That is where the run built
the receiver artefact itself and handed it on as emitted (the run tier's
`receiver_provenance` attestation,
`src/certiqs_key/runs/receiver_provenance.py`), its declaration has a model
admissible exactly and every weight was evaluated rigorously; a
floating-point weight, a declaration admitted only within the receiver
tolerances, or an artefact from outside the run keeps the row. Where every
reduction artefact of the run omitted it, the manifest names that
requirement among the reductions roots and lists A-RECV under `not_engaged`
with `discharged_by` it; the receiver's own rows stay listed.

**A-EVE-DIM** (`adversary_registers_finite`) is emitted by no module: the
round model keeps the adversary's registers finite-dimensional by definition,
and `meat-core/cor:composed-security`, through `meat-core/lem:memory-lift`,
carries the security statement to an attacker with memory of any size, so
`meat-core/ass:eve-dim` is superseded and in no ledger or manifest.

**The key-length roots.** `meat-core/thm:keylength` assumes the compiler's
A-LINK, A-SPEC and A-ALICE-MEAS, so the key-length roots' closures hold them
beside the compiler's own roots; each is listed once, as the compiler's ledger
has it: A-SPEC engaged on every run, A-ALICE-MEAS engaged where its presence
rule emits it and otherwise under `not_engaged`, and A-LINK engaged where the
compiler emits it and otherwise under `not_engaged` with `discharged_by`
(`thm:band-a` on Band A, `req:link-row-provenance` where that requirement
omits the row).

**One laboratory premise per party.** A-LAB (`meat-core/ass:lab`, machine key
`laboratory_sealed`, category `laboratory`) is one assumption whose row is
emitted once per party: at both parties on a run that reports a key length,
and without a length only in trusted-source mode at the party of `A`. Every
`emitted_by` object of the assumption manifest (an assumption's, a binding's,
a discrepancy's) carries `party` beside `station`: `"A"` or `"B"` on such a
row, `null` on every other.

**Which rows are listed.** A-ENS is listed in trusted-source mode only;
A-ALICE-MEAS at two letters or more only; a station's A-PROBE only at two
settings or more, and its A-TSM only there or where a public choice is applied
at its factor; A-LINK is omitted on a multi-station run whose every
station is an in-run flat instance link; the station bindings of A-MEAS,
A-ROUND-SQ and A-SEQ name the station's party. No receiver emits a row for
its probe states: `receiver/req:probe-diagonal-admission` decides them on the
declared data and refuses a declaration that fails it.
`stages.key_rate.assumption_ids` lists each id once, while
`assumption_ledger` lists A-LAB's key once per party.

## The claim graph a number rests on

`assumption_manifest.claim_closure` is on every completed run (PRINCIPLES.md 2.1,
spec/architecture.md 4.4). It is keyed by every root of the run (the union
over the modules' `roots`, in that order), the key-rate result's
`stages.key_rate.claim_roots` among them, and each entry
carries `claims` (the root, then its transitive `uses` closure) and
`assumptions` (every assumption short id those claims declare, mapped to the
assumption claim that owns it): what `python -m harness.check_claims
--assumptions <root>` lists. The record reads it from the package data
`certiqs_key/domain/claim_closure.json`, which `python -m
harness.generate_claim_closure` writes from the claim files and whose
`--check` keeps it current, so a record written from an installed package
names its claim graph although `spec/` is not installed. A root the table
does not cover stops the record with `ClaimClosureError`; it is never
omitted.

`assumption_manifest.module_versions.statistics` (the `version` of
`spec/modules/statistics/module.yaml`) and `stages.key_rate.module_versions`
(`meat-core`, `meat-core/frank-wolfe`) are read from the same table.

## The route-exact assumption set and the key-rate report

**`assumption_manifest` is the route-exact set** (`src/certiqs_key/runs/assumptions.py`).
It holds:

- `roots`: per module that ran, the top-level results this run used;
- `claim_closure`: keyed by every one of those roots;
- `assumptions`: one entry per engaged assumption, sorted by short id, with
  the claim-closure table's snapshot of its title, summary, `user_statement`,
  category, `affects`, `refines`, `verification` (and its sentence), status,
  effective status and contract anchor; `section` (`assumptions` or
  `numerics`); `emitted_by`, every emitter with its station, machine key and,
  for reductions' A-RECV, the receiver version it accepted; and `bindings`,
  the declared values the rows bind, each with its emitters. A-SEQ (the
  transmitter, reductions and meat-core) and A-RECV (each station's
  reductions artefact that emits it) are one entry each;
- `not_engaged`: closure members a module that ran did not emit on the route,
  with its emission rule or condition, and `discharged_by` where a root of
  the run discharges one (A-LINK on Band A or by
  `protocol-compiler/req:link-row-provenance`; A-RECV where
  `reductions/req:recv-row-provenance` omitted every reductions artefact's
  row);
- `discrepancies`: where rows and closures disagree; recorded, never refused.

The manifest also carries `module_versions` and `reported_tier`.
`verification` is `never` or `partly`.

**`config.parameters`** carries A-AUTH's two run inputs, `eps_auth` (binary64
in `[0, 1)`) and `k_auth` (bits), always, default 0; the configuration's own
payload (and so its digest) carries them only where they are not 0. They are `RunConfig`
fields, passed by every instance's runner to `run_slice` and on to
`solve_bundle`. A budget with `eps_pa + eps_ev + 2 eps_auth >= 1` is a
`solve`-stage refusal with reason `security_statement_vacuous`.

**`stages.key_rate`** carries `security_parameter` and `net_key_length`
(`cor:composed-security` (iii), null without a key length),
`key_length_reason_code` (a closed list:
`general_keyrate.KEY_LENGTH_REASON_CODES`) and `reason_text` (its sentence, or
null). `constraint_entries_through_a_reductions_chain` is provenance: it
decides nothing.

**Two payload blocks** identify what ran: `instance` (the instance's
descriptor and parameter table, `runs/surface.py` `InstanceIdentity`, or null)
and `provenance.engine` (distribution version, git commit, dirty flag;
`runs/provenance.py`). `record_run`, `sweep` and `runs/two_sided/point.py`
take the instance; `runs/surface.py` `RUN_PARAMETERS` describes the
configuration's own fields as the instance tables describe theirs.

## The statistics check

`statistics_consistency` holds the check of
`meat-core/req:unreachable-acceptance-set`. The pass cap of devices as
declared (`meat-core/prop:model-pass-bound`, the requirement's (v)) is
`model_pass_exponent_bits`, `x = n (alpha_0-1)/alpha_0 b` rounded toward
`-inf`, with `model_pass_exponent_tier`, the tier of `b`, both null where
`b <= 0` or no bound was formed. Devices the declaration admits, each round's
acceptance value following the statistics of a feasible state, pass the
acceptance test with probability at most `2^(-x)`.

A checked run is refused on that cap (the requirement's (iv)): the run option
`min_model_pass_probability` (`tau`, an exact rational in (0, 1], default
1/2; a payload naming the retired `contradiction_share` is refused with
`retired_parameter`) sets the threshold. `statistics_consistency` carries
`min_model_pass_probability`, `model_pass_decision` (`exact` where tau is a
power of two, `enclosure` against a rigorous enclosure of log2(1/tau),
`undecided`, which refuses), `no_cap_reason` (`bound_not_positive`,
`no_bound_formed`) and `refused`, decided on the exact x; a refused run is
evaluated at no order. Each entry of `orders` holds `alpha` and
`proven_part_bits` (n f, a diagnostic).

## Solver settings

`config.solver` has two tiers. The ordinary choices are `method` (`auto` or
`fw`), `budget_seconds` and `max_iterations`; the expert ones (`method` among
`pairwise`, `factor`, `entropy` and `corrective`, `oracle`, `gap_tolerance`,
`warm_start`, `certified_evaluation`) sit under `config.solver.advanced`,
which is written only where one is chosen.

`config.solver.method` chooses `auto` or `fw`; absent, the run tier takes its
default (`DEFAULT_METHOD`, which `solver_request` in
`src/certiqs_key/runs/surface.py` resolves).
`config.solver.advanced.method` chooses an expert method instead --
`pairwise`, `factor`, `entropy` or `corrective` -- and setting both is refused
(`solver_method_set_twice`). `budget_seconds` is the solver-wide wall budget,
`max_iterations` a method-native work cap (under `auto`, of its Frank-Wolfe
stages only: factor, entropy and corrective run to their own convergence or
their budget share) and `advanced.gap_tolerance` a diagnostic target. The
`advanced.oracle` and `advanced.warm_start` choices are independent. A solver
key the block does not read, among them an expert key written beside `method`,
is refused (`solver_key_not_admitted`). There is no step-rule setting.

| Key | Absent means |
| --- | --- |
| `method` | `DEFAULT_METHOD` |
| `budget_seconds` | no wall budget for `fw` and `pairwise`; the coordinator's `DEFAULT_PORTFOLIO_SECONDS` per evaluation for every other method (`solvers/solve.py`) |
| `max_iterations` | the driver's own (200) |
| `advanced.method` | the ordinary `method` |
| `advanced.oracle` | `qics`; `spectral` sends every spectraplex subproblem to the closed-form backend |
| `advanced.gap_tolerance` | `meat_core.thresholds.OPTIMIZER_GAP`, a diagnostic stopping target, never a proof threshold |
| `advanced.warm_start` | a cold start; set, a prior final iterate named by file and sha256 |
| `advanced.certified_evaluation` | `on`; `off` skips the certified evaluation, `strict` refuses a run whose bound cannot be certified |

## What the solve stage records

`stages.key_rate.solver_request` records the resolved common request.
`search_report` records the policy, attempts, skips, switch reasons, budgets
and termination separately from qualification of the reported bound. Its best
contributing candidate carries its own q, objective, bracket and gap; it need
not be the final/search-best candidate. Optimizer success alone emits no key.
The negative-estimate refusal and the security gates apply.
`joint_solver` retains algorithm-specific FW diagnostics when FW ran.

`stages.key_rate.joint_solver` records how the loop ran: `oracle`,
`step_rule`, `q_rule` (below), `oracle_assignment` (the backend of every subproblem group, an
Alice sector or `*`, decided before the loop from the declaration's
structure), `oracle_calls` per backend, `spectral_evidence` (the largest
eigen-residual `||C v - lambda v||` and the largest
`|<C, v v^dagger> - lambda|` over the spectral calls; evidence, discharging
nothing), `pairwise` (the shrink `1e-8`, the fold threshold `1e-12`, the
fallback count -- iterations whose TAKEN step, after the direct
re-evaluation accepted it, was the plain Frank-Wolfe step because it searched
lower than the pairwise step -- the final number of active atoms and
`anchor_min_eigenvalue`, below; `null` under the vanilla rule) and
`warm_start` (`blocks_sha256`, the seed's identity derived from its blocks'
canonical bytes; `file_sha256` and `source`, the file it was read from; source
mode, joint sector count, `constraint_count`, `rows_sha256` and the mix
`1e-6`; `null` for a cold start). Each entry of `oracle_diagnostics` names
the `group` it served and its `iteration`. These numbers are the solver's own
and no configuration sets them.

The general solver reports a dropped-program objective as `h_low_dropped` and
its lower bound as `h_lb_dropped`, together with the dropped set. These names
must not be relabeled as the original program's objective or bound.

**The outer alpha search without a key.** Where some evaluation formed a
bound and none reported a positive key length, the solve stage's `alpha`
child has status `no_positive_key`, `chosen_alpha` is null, and
`no_positive_key` names the evaluation the record is (`reported_alpha`, the
largest `h_low`), the largest `h_lb` and, where the reported bound is the
reference companion's, the largest bound on the searched declaration, with why
the key is 0 (`no_positive_key_rule` states the rule).

## One Frank-Wolfe driver: one record for every run

Every declaration runs on the joint driver. An accepted-format declaration --
`bb84`, `optical_bb84`, anything docked as a `ProtocolDeclaration` -- is
solved as the degenerate general declaration it is, and its record is the
general record: `optimized_q`, `predicted_statistics`, `block_contributions`
(key-active joint pairs only), the general `sector_report` (the general report
searches no removal witness, so `removable` is false), `assumption_ids`,
`deductions`, `oracle_diagnostics`, `tolerances`, `timings`, `joint_solver`,
`module_versions`, `claim_roots`, per-Alice-sector `choi_input_basis` and
`constraint_row_form`, every gate in `per_iterate`, and a `final_iterate`
file beside the record. `config.solver`'s `oracle`, `method` and
`warm_start` apply to these instances too. The tier is `reported_tier`, read
together with whether `h_lb` is present.

**On every record:** `first_order_minus_estimate`, `h_lb - h_low` with its
sign (`null` without a bound or at `h_low = inf`; `frank-wolfe/rem:fo-arithmetic`
(b)); each `per_iterate` entry carries
`oracle_status` (the status that decided `oracle_optimal`, `not-called` where
the gradient failed first), `min_block_eigenvalue_at` (the joint label of the
block), `coupling_residual_at` (the Alice sector),
`oracle_return_row_residual` and `oracle_return_coupling_residual` with its
`oracle_return_coupling_residual_at`;
`optimizer_certificate.group_b_worst` gives each per-run Group B
row (`iterate_positivity`, `iterate_repair_window`, `iterate_coupling`,
`constraint_rows` on the consumed point and on the oracle return,
`oracle_repair_window`, `optimizer_gap`) its declared window, the worst
quantity met, the iterate and where it sat, and the returned point's own
measurement under `returned_point`;
`optimizer_certificate.backend` carries the probe's backend identity;
`security_gates.licensed_class_reason` says in words why part (i) passed or
failed and whether it is vacuous; `key_length_reason` names every failing
gate part, or the corollary a length was computed by.

**A residual withdraws a bracket.** A declared-row residual above
`constraint_rows`, or a coupling residual above `iterate_coupling`, on a point
the loop consumes or on an oracle return withdraws that iterate's bracket
with `iterate_not_feasible`, and the run goes on with its estimate
(`frank-wolfe/rem:fo-interface` (1), (3)). A start or a warm-start seed
outside the window stops the run.
`optimizer_certificate.group_b_worst.iterate_coupling` is split like
`constraint_rows` into `consumed_point` and `oracle_return`, each with
`worst`, `iteration` and `at` (the Alice sector).

**The returned point.** The point the estimate is taken at is measured once
at loop exit, never fatally: a run ending by the iteration limit returns a
line-searched point no gate consumed. Its smallest block eigenvalue, coupling
residual and row residual are recorded as `returned_point` (with `iteration`
null) in `group_b_worst`'s `iterate_positivity`, `iterate_coupling` and
`constraint_rows`, and `stages.key_rate.estimate_point_relaxed_member`, beside
`h_low`, is `true` exactly when that point passes all three checks of
`rem:fo-interface` (3): positivity at exactly 0, coupling and rows each inside
its window. It is a record and not a gate: no bracket, tier or key length
reads it. A sweep that chains warm starts can read it before seeding the next
point from `final_iterate`; a seed outside the windows is in any case
refused at load with `warm_start_not_feasible`.

**The pairwise anchor** is checked positive definite before the loop and its
smallest block eigenvalue recorded as `joint_solver.pairwise.anchor_min_eigenvalue`;
a run whose anchor is not positive definite stops. With constraint rows the
anchor is the oracle's zero-cost start, so the pairwise rule runs with rows.

**The q rule.** On a canonical-box acceptance set the loop re-minimises `q`
in closed form at every point it evaluates and makes it an exact member of the
box; every other geometry keeps the Frank-Wolfe step toward the exact LP
vertex (`src/certiqs_key/solvers/frank_wolfe/q_rule.py`).
`stages.key_rate.joint_solver` says which ran: `q_rule` is
`box-partial-minimum` or `vertex-step` (on a singleton `q` never moves). It
is evidence and no number reads it.

**The (H-SUPP) reference.** The reference `dim W` of the (H-SUPP) rank
comparison is read with the `support_cutoff` row alone: the rank of each
pair's Kraus stack at the square root of that window on its singular values,
which is the window on the eigenvalues of `K K^dagger`
(meat-core/frank-wolfe/rem:fo-interface (2)). There is no
`branch_support_dim` threshold row. `map_validation_report.hsupp_reference_band`
is on every completed run -- under `stages.key_rate` in a general-format
record, and in the `map_generation_and_cross_validation` child of the solve
stage of `composition_flow` in every record: `support_cutoff` and
`factor_support_cutoff` (its square root), and `pairs[<chat>][<pair>]`, for
every key-active pair, the number of directions of the pair's Kraus stack
whose singular value lies in `(support_cutoff, sqrt(support_cutoff)]`
relative to the largest. Those are the directions the reference does not
count, and which a rank of the branch operator counts only at an iterate
whose input is ill-conditioned (`cond(J) > support_cutoff / sigma_rel^2`); a
positive count says where the remark's second exposure could sit, its window
being wider than the reference's by exactly this band. It is computed once
per run with the maps and decides nothing.

**Live progress.** A caller's stage observer is told an `iterate` event
(`iteration`, `gap`) at every Frank-Wolfe iterate of the `solve` stage; it is
not written into the record and cannot change the outcome.

## The final iterate and warm starts

**The final iterate.** A completed general run writes `final-iterate.json`
beside `record.json` and references it from the record as
`final_iterate: {file, sha256}`; the one writer of both is
`attach_final_iterate` in `src/certiqs_key/runs/iterate_file.py`, which
`runs/two_sided/point.py` and any other caller use. The file
is canonical JSON (sorted keys, no whitespace), so its sha256 is the same on
every machine: the joint sectors' blocks as `real`/`imag` lists keyed by the
joint label, the producing declaration's `source_mode` and `constraint_count`,
its `layout` (each block's split into Alice factor and sector factor, since
equal block sizes do not fix it), `rows_sha256` and the producing
configuration's digest. The file is format `3`; the loader reads every format
in `READABLE_FORMAT_VERSIONS`. Floats round-trip binary64 exactly.
`src/certiqs_key/runs/iterate_file.py` is the reader and writer.

**A warm start** names the file by path and file hash in
`config.solver.advanced`.
The path is a locator, not part of the request: `config_digest` hashes the
seed's `sha256` and drops its `file`, so the same seed bytes at two paths give
one digest, and `runs/two_sided/chain.py` writes the path relative to the
working directory. `runs/two_sided/point.py` reads and verifies the file
before it creates the output directory, refusing a missing, altered or
foreign file (`warm_start_file_missing`, `warm_start_hash_mismatch`,
`warm_start_not_an_iterate`) with no directory left behind. A seed that reads
but does not live in the new point's feasible set is refused by the solver and
recorded as a `solve`-stage refusal (a record with `refused: true`) with one of
`warm_start_source_mode_mismatch`, `warm_start_constraint_rows_mismatch`,
`warm_start_layout_mismatch`, `warm_start_block_dims_mismatch` (sizes or
split) and `warm_start_not_feasible` (a non-finite or non-Hermitian block, or
a seed outside the PSD or coupling window).

**Warm starts across constraint rows.** `rows_sha256` is the producing
declaration's `constraint_rows_digest` (its entries' scope, relation, tag,
operator blocks and bound, and in trusted-source mode the declared marginal).
A seed is admitted on a point with rows exactly when the digests match, and is
then mixed toward the point's cold start, the zero-cost vertex, which
satisfies the rows. The refusal reason is
`warm_start_constraint_rows_mismatch`: the rows differ, or a seed that
declared rows carries no digest (a format 1 or 2 file).

## Public choices

`compiled.public.choice_weightings` lists the choice weightings the measured
factors declared (`ReceiverPart.choice_weighting`), transcribed from the
compiler's `choice_weighting_record`: one entry per weighted factor, in the
factors' order, empty where none was declared. Each entry names its
`factor` and carries `setting_alphabet`, `choice_alphabet`, `matrix` keyed
`"<setting>|<choice>"` with exact `"p/q"` values, `setting_map`
(`t: V -> T`), `source_alphabet` and `support`, the rows `[label, v, f]` that
explain a weighted label's choice component; it records no party (a
station's party is `stages.stations[i].party`). For BBM92's test coin: factor
`alice_station`, settings `["off"]`, choices `["gen", "test"]`, matrix
`{"off|gen": "7/8", "off|test": "1/8"}`, support rows such as
`["(H,gen)", "H", "gen"]`. The coin's snap to its lattice is recorded
in `input_preparation` (site `bbm92.test_coin`).

## Older records the report still reads

- Before 0.40 a declared factor of one carries the not-applied reason
  `declared_one`, which the report reads as `factor_one`
  (`report/setup.py`, `_normalization_note`).
- Before 0.42 an `efficiency_record.rows` entry names its declared loss
  parameter `transmittance`, not `value` (`report/setup.py`).
- A 0.42 record has the expert solver keys beside `method`, which admits all
  six methods, and always writes `gap_tolerance`; the report lists each as a
  `solver.<key>` row (`report/inputs.py`).
- Before 0.44 `stages.receiver_construction.assumption_ledger` is absent, and
  A-RECV lists the compiler among its emitters on every route but Band A.
- Up to 0.40 A-EVE-DIM is one manifest entry emitted by reductions and
  meat-core; the report keeps the attacker intro written for it
  (`report/_render.py`, `report/glossary.py`).
- Before 0.30 the laboratory premises are A-LAB-ALICE and A-LAB-BOB (machine
  keys `alice_laboratory_sealed`, `bob_laboratory_sealed`), read as Alice's
  and Bob's laboratory (`report/explain.py`, `RETIRED_LABORATORY_KEYS`).
- From 0.20 to 0.29 the public choice is `compiled.public.choice_weighting`,
  one object with the factor's `party`, or null; the report reads it as a list
  of at most one (`report/setup.py`, `_choice_weightings`).
- Before 0.46 the report does not read the statistics check
  (`report/build.py`, `_statistics_check`): such a record refused on a share
  of the key length, and a 0.44 record carries no cap.
