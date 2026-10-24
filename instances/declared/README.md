# Protocol documents: the format guide

A protocol document describes a QKD protocol as data: JSON, or YAML that parses
to one JSON object. The engine reads it into the same instance surface every
instance exports (`DESCRIPTOR`, `PARAMETERS`, `PRESETS`,
`default_config`, ...) and hands every value to the modules' own constructors.
The modules decide whether the protocol is admissible. The document layer
refuses only what has no meaning as a document: text that does not parse, an
unknown key, a reference that does not resolve, an expression that does not
parse.

- The shape is `protocol-document.schema.json` beside this file. It is
  generated from `model.py` (`python -m instances.declared.schema`; a test
  holds it current); never edit it by hand.
- Status: every block is lowered to a run: Band-A
  stations (`declared_povm`, which on the Band-A route the compiler admits
  only as one ideal qubit receiver, see below) and optical stations, one or
  several; the
  `trusted_ensemble`, `untrusted` and `wcp_decoy` sources (a `wcp_decoy`
  source with exactly one optical station: beside `declared_povm` stations
  it is refused at load, `wcp_decoy_needs_optical_stations`, and beside
  several optical stations, `wcp_decoy_needs_one_optical_station`); the accepted
  format or a transcript of any length; the default, factor-projection or
  explicit partition; choice weightings; docked, explicit and library
  constraints and witnesses; every honest form; every channel interface.
- Templates: each packaged instance's document is
  `instances/<id>/protocol.yaml`: bb84 (Band A, `conjugate_states`),
  optical_bb84 (an optical receiver as a catalogue element graph), decoy_bb84
  (a `wcp_decoy` source and a transcript) and bbm92 (two stations,
  `factor_projection`, a choice weighting). Each IS its instance: the
  package's `surface.py` loads it
  (`tests/integration/test_declared_equivalence.py` keeps the named
  differences from the reference constructions). Only a
  document loaded from there (`load_packaged`) may carry a packaged id, a
  `readme`, a `record_label` or an `instances.` label. Every other document
  is custom and is refused `reserved_identity` for any of them (the refusal
  lists every such place at once); start a custom one from a template by
  giving it a new `identity.id` and deleting `readme`, `record_label` and the
  other strings its header names (optical_bb84's and decoy_bb84's stations
  and source write `instances.` labels).
- Bounds (`limits.py`): an alphabet has at most 4,096 labels, a rule table
  at most 16,384 keys (and 10^6 key-rule tests), a Hilbert-space dimension
  is at most 64, and `identity.id` at most 64 characters. A custom
  document's optical stations are also bounded in the work they ask for: a
  photon cutoff of at most 7, at most 8 detector ports, and `3^ports` times
  the summed squared photon-number blocks up to the deepest window at most
  40,000. Past them a document is refused with `document_too_large` before
  the work starts. A packaged template is held to the size bounds only; its
  parameter domains bound its work.
- Through the MCP server (`runs/mcp/README.md`): `describe_instance`,
  `prepare` and `start_run` take a document (object) or `document_file`
  instead of an instance; `get_reference` serves the schema
  (`name="protocol-document"`), the templates (`"template"`) and this guide
  (`"document-guide"`). A refusal is
  `{refused, stage: "document", reason, path, detail}`. Every preparation's
  expected time is estimated first from the lowered receivers
  (`DocumentSurface.receiver_requests`, which constructs nothing), stated
  with its reason, and past a budget run in the background
  (`runs/facade/estimate.py`).

```python
from instances.declared import load

surface = load(Path("my_protocol.yaml"))  # or load(text), load(mapping)
config = surface.default_config(model={"qber": "1/50"})
outcome = surface.preparation(config)  # no oracle: compilation, tables
run = surface.runner(oracle, directory, created_by="me")  # run(config, index)
```

`preparation` and `runner` take the uniform instance signature.
`channel_interface` and `DEFAULT_HONEST_MODEL_NOTE` never raise on access: the
first is read off the document, the second is the note at `default_config()`,
or a note saying the model was not built there (`not_built` names why).

On a `declared_povm` station the reduction is `{links: [{kind: identity}]}`;
any other reduction field is refused with its path rather than ignored. The
Band-A lowering docks no source segment, so a `wcp_decoy` source, whose links
need one, is refused beside `declared_povm` stations (one or several) at load
with `wcp_decoy_needs_optical_stations`: declare its receivers as optical
stations. Otherwise that identity link puts the document on the Band-A route
wherever the source carries no source segment and the emitted sector set is
one sector. The route
rests on A-IDEAL, an ideal projective qubit measurement, so there the compiler
refuses the document with `band_a_outside_ideal_receiver`
(`protocol-compiler/req:band-a-ideal-receiver`) unless it declares exactly
one measured station, a `declared_povm` station on a receiver system
of dimension two (and, with a trusted source, a transmitted system of
dimension two), whose family is projective as declared: every element of each
basis where a basis choice is declared, every element otherwise. Declare any
other receiver as an optical station. On a
Band-A document `constraints.docked` has nothing to dock and has no effect,
and `party_local_view` is refused. An honest block's `note` is recorded under
`note.document`; it never replaces the fields the engine writes. Each outcome
carries `protocol_document` -- the canonical document, its digest, every
expanded rule table with the keys no rule matched, and the premises the
document declared itself -- which the run record writes as
`payload.protocol_document`.

## The top level

| Key | Required | What it is |
| --- | --- | --- |
| `format` | yes | `certiqs-key/protocol-document` |
| `format_version` | yes | `"1"` |
| `identity` | yes | `id`, `title`, `summary`, optional `readme`, `record_label` |
| `parameters` | yes | the parameter table and the absent-key policy |
| `presets` | no | named parameter sets |
| `snap`, `preparations` | no | the engine's probability preparation of parameters |
| `run_defaults` | yes | the base of `default_config` |
| `alphabets` | no | named label sets, used by rules |
| `source` | yes | `trusted_ensemble`, `wcp_decoy` or `untrusted` |
| `stations` | yes | one or more receivers: `declared_povm` or `optical` |
| `public` | yes | partition, announcements or transcript, sifting, key, acceptance |
| `constraints` | no | docking, and explicit (flagged) entries, licence, witness |
| `honest` | yes | a library model, a table, or an envelope |
| `channel_interface` | no | `qubit_identity`, `single_photon`, `mode_intensity`, `bipartite`, `none` |
| `annotations` | no | anything, keyed by semantic id; recorded, never read |

Every block refuses a key it does not declare.

## Parameters

Parameters are the document's only free variables. Each row is a
`ParameterSpec` of `certiqs_key.runs.surface`:

```yaml
parameters:
  model_absent: refuse        # an absent model key is refused (or: default)
  device_absent: refuse
  check_order: [model, device]
  table:
    - name: test_fraction
      section: device         # model (the channel) or device (the apparatus)
      kind: fraction          # fraction | int | choice | per_port_fraction
      quantity: probability   # the run tier's closed Quantity vocabulary
      default: 1/8            # stored as an exact Fraction however written
      domain: {form: interval, lower: 0, upper: 1, lower_open: true, upper_open: true}
      snapped: true
      meaning: Probability that a round is a test round
    - name: dark_count
      section: device
      kind: per_port_fraction
      per_port_of: bob        # keyed by station bob's port labels, in order
      quantity: probability
      default: 0              # one number here means that number on every port
      domain: {form: interval, lower: 0, upper: 1}
      snapped: true
      meaning: Dark-click probability per round of each detector
    - name: route
      section: device
      kind: choice
      quantity: choice
      default: encoded
      domain:
        form: choices
        options:
          - {value: encoded, meaning: Weight-preserving flag reduction}
          - {value: licensed, meaning: Flag reduction with a multi-click constraint}
      snapped: false
      meaning: Photon-number reduction of the receiver
      applies_when: null      # or {other_parameter: [values]}
```

`station: <id>` says which station a parameter describes (several-station
documents). `applies_when` must resolve inside the table; the run tier's
`check_applicability` decides it at load.

## Numbers

| Written | Read as |
| --- | --- |
| `3` (a JSON integer) | that integer |
| `"1/3"`, `"0.02"`, `1e-3`, `"2^-30"`, unquoted `0.02` in YAML | exactly that rational: a constant expression |
| a float in a parsed object (an MCP argument) | its binary64 value, exactly, with a recorded conversion |
| `{param: test_fraction}` | the configuration's value |
| `{param: dark_count, port: H}` | one port's value |
| `{expr: "1 - test_fraction"}` | exact arithmetic |
| `{switch: route, cases: {encoded: ..., licensed: ...}, default: ...}` | the case the choice parameter selects |

Text keeps its decimals: `0.02` in YAML is the rational 1/50, never a binary64
number. In YAML only `true` and `false` are Booleans, so `off` and `on` are
labels. A float in a parsed object is recorded as a `numeric_input_conversion`
(`written` keeps its spelling), and every `default_config` puts these records
first in `input_preparation`.

There is one number grammar. Every number string is an expression that reads
no parameter; reading one takes `{expr: ...}`. Table defaults, presets and
`run_defaults` sections take numbers, `{expr}` of no name, choice names, or a
per-port mapping; a single number for a `per_port_fraction` means that number
on every port.

**Expressions** use `+ - * /`, parentheses, integer powers (`2^-30`), decimals
and fractions, and the names of `fraction` and `int` parameters (`dark_count[H]`
for one port). Arithmetic is exact. There are no functions and no irrational
numbers: a receiver angle is written in units of pi (`angle_pi`). In
`run_defaults`, `preparations.family` and `run_defaults.derived` a string *is*
an expression: `eps_pa: 2^-30`, `family: [1 - test_fraction, test_fraction]`.

**A switch** may stand only where the schema allows `Switch[...]`: every
scalar, matrix and rule list, and the blocks a protocol varies (a station's
reduction, the public tables, the key, the acceptance, the constraints, the
honest model); not the source, a station's measurement or the station list.
Each case must be a value of the choice parameter (a misspelt case is refused
at load), and every case's rules are checked at load, not only the one a
configuration selects. A selected value with no case and no default is refused
(`switch_case_missing`).

**Matrices** are `{matrix: rows}` (an entry is a number or `[re, im]`;
`serialize_matrix` output is accepted as it is), `{identity: n}`,
`{scale: {factor, of}}`, or `{outer: {vector, squared_norm}}`, the projector
`v v^dag / N` without a square root:

```yaml
psi: {outer: {vector: [1, 0, 0, 1], squared_norm: 2}}     # |Phi+><Phi+|
alice_marginal: {scale: {factor: 1/2, of: {identity: 2}}}
```

## Tables are rules

A table the compiler reads (announcements, sifting, key, acceptance, a
transcript message, a coarse-graining) is written as ordered rules and
expanded over its domain. The first rule that matches wins.

```yaml
alphabets:
  signal: {product: {dims: {basis: [Z, X], bit: [0, 1]}, label: "({basis},{bit})"}}
  ann:
    union:
      - {enum: [{label: Z, basis: Z}]}
      - {product: {dims: {bit: [0, 1]}, label: "(X,{bit})"}, attrs: {basis: X}}
public:
  partition: default
  announcements:
    alice: {alphabet: ann, map: [{when: {x.basis: Z}, value: Z}, {value: "(X,{x.bit})"}]}
    bob: {alphabet: ann, map: [{when: {v.basis: Z}, value: Z}, {value: "(X,{v.bit})"}]}
  sifting: [{when: {A: Z, B: Z}, value: pass}, {value: fail}]
  key: {holder: A, alphabet: [0, 1], rule: [{value: {int: o.bit}}]}
  acceptance:
    alphabet: [gen, ok, err, disc]
    map:
      - {when: {A: Z, B: Z}, value: gen}
      - {when: {A.basis: X, B.basis: X, A.bit: {eq: B.bit}}, value: ok}
      - {when: {A.basis: X, B.basis: X}, value: err}
      - {value: disc}
```

- An alphabet is `enum`, `product` (the first dimension varies slowest) or
  `union`; an entry's components are its dimensions, its attributes and
  `label`. Labels must be distinct.
- A path is `var` (the label) or `var.component`. A pattern is a string,
  a list (membership), `{eq: path}`, `{ne: path}` or `{not: pattern}`.
- A value is a template (`"(X,{x.bit})"`), an integer, `{int: path}`,
  `{label, attrs}` (a message value later rules can read), `pass`, `fail`,
  `perp`, or a switch.
- A condition on a component the entry lacks does not match, and neither does
  a comparison with a missing side. A template that reads a missing component
  is refused (`rule_value_invalid`), so guard it with a `when`.
- A key no rule matches is left out and listed as unmatched; whether the table
  is total is the compiler's check.

The entries a variable ranges over: `x` is the source alphabet (or Alice's
readout alphabet under an explicit partition), `v` is the station's outcomes
(or Bob's readout alphabet). A `declared_povm` station's outcomes carry the
components `choice` and `outcome` where it declares a `choice_family`, and the
label alone where it declares a `povm`. An optical station's outcomes are the
reductions' `V = Y x T` (the letter alone when there is no probe, `letter,t`
with one) and carry `letter`, the letter's own attributes and `setting`; with
a `choice_weighting` they are the weighted labels `(v,choice)` and carry
`choice` too (`weighted_choice` on a Band-A station whose outcomes already
carry a `choice`). A `wcp_decoy` source's letters carry `round`, `intensity`,
`polarisation` and the polarisation's attributes. With several stations `v`
ranges over their joint labels (joined by the product separator), whose
components are each station's label under its id and each station's
components as `<id>.<component>`. An explicit partition's readout maps range
over `x` and `v` together; `factor_projection` (one station per party) gives
each party its own station's outcomes.

The variables per table: announcements `x` / `v`; sifting and acceptance `A`,
`B` (or the transcript's message ids); key `o` plus those; transcript message
k `r` (the sender's readout) plus the earlier message ids, its alphabet
declared or `derived` (the values in first appearance, with the attributes a
`{label, attrs}` value wrote); coarse-graining `count`, `port`, `fired`;
`setting_of` `v`. A coarse-graining's map ranges over the `2^K` click
patterns: `count` is the number of ports fired, `port` the port's label where
exactly one fired (and no value otherwise), `fired` the pattern `{H,V}` with a
component `1` or `0` per port label. A transcript's announcement alphabets
default, per party, to the alphabets of the messages it sends;
`announcement_alphabets` states them. The accepted format's `announcements`
may switch as a whole, where a choice changes an announcement alphabet.

## Optical stations

```yaml
stations:
  - id: bob
    party: B
    measurement:
      kind: optical
      modes: [{path: Z, polarization: H}, {path: Z, polarization: V}, ...]
      channel_modes: [Z_H, Z_V]            # a mode is named <path>_<polarization>
      route: element_graph                 # or port_grams, instrument_matrix
      elements:
        - {name: bs, component: beamsplitter, support: [Z_H, Z_V, X_H, X_V],
           params: {transmittance: {param: basis_split}, phase_pi: 0,
                    loss_1: 0, loss_2: 0}}
        - {name: hwp, component: half_wave, support: [X_H, X_V],
           params: {angle_pi: {param: half_wave_angle}, loss: 0}}
      edges: [[bs, hwp]]
      ports: [{label: H, modes: [Z_H]}]
      detectors: [{port: H, efficiency: {param: efficiency, port: H},
                   dark_count: {param: dark_count, port: H}}]
      coarse_graining:
        letters: [{label: nc}, {label: H, basis: Z, bit: 0}, {label: mc}]
        map: [{when: {count: "0"}, value: nc},
              {when: {count: "1"}, value: "{port}"}, {value: mc}]
      photon_cutoff: {param: photon_cutoff}
      exact_window: {param: exact_window}  # a parameter the configuration lacks: none
    reduction:
      switch: route
      cases:
        encoded: {links: [{kind: wpfss}], route: encoded}
        licensed: {links: [{kind: fss}], route: licensed,
                   carried_operators: [{library: two_sector_floor}]}
```

- Every catalogue entry (C1-C10) declares all its fields; an angle is written
  in units of pi as `<field>_pi` and passed as a pi multiple, an integer `0`
  as `0`. A JSON integer is passed as an integer, every other number exactly.
  Port Grams, an instrument matrix (`|M| x |M|`) and a C10 block are float
  data of the receiver: their entries are converted to binary64 and each
  inexact one is recorded in `input_preparation`.
- `dark_count_channel` declares `R` on the click patterns (by the number of
  ports fired, then by port position) and needs every detector's dark count
  to be 0. `tolerances` default to the receiver's 1e-3.
- The reduction's protocol declaration is derived from the measurement. An
  explicit carried operator is certified against the first pass's own
  channel. `declared_by` defaults to `<record_label>.<station id>`.
- Several stations each emit a factor; with `constraints.docked` (default)
  the reductions assemble them and their scoped entries are docked as
  `constraints.party_local_view` reads them. Three or more stations need an
  explicit partition, a `none` or explicit witness and no channel interface.
- `feasibility_witness: auto` is the topology's: below-cutoff for one station,
  vacuum output behind a `wcp_decoy` source, uniform below the cutoffs for two
  stations.
- `exact_window` written as a bare `{param: name}` that the configuration
  does not carry is no window, and the record lists it under `absent`; any
  other expression over an absent parameter is refused.
- `efficiency_normalization` (optional) is the station's factored loss `t`:
  the receiver divides every detector efficiency by `t` and hands the common
  loss to the channel, which leaves the observed statistics unchanged
  (`receiver/detector-imperfections/req:efficiency-normalization`). Left out,
  a station without source modes is analysed at `t` = its largest
  efficiency divided by 99/100, or `t` = 1 where that efficiency is at least
  99/100 (the default stops short of the largest efficiency, where the engine
  can lose the key with dark counts at a photon cutoff of two or more:
  `receiver/detector-imperfections/rem:normalization-scope`); declared, `t`
  lies between the largest efficiency and 1, and 1 turns the normalization
  off. Like `exact_window`, a bare `{param: name}` the configuration does
  not carry is read as left out (not listed under
  `absent`: the receiver's efficiency record says what was done). A station
  whose receiver is read as a branch of a larger receiver model must
  declare 1.
- `accepted_receiver_versions` keeps its default (Assumption A-RECV); every
  `lattice_exponent` lies in 1..53.
- The snap parameters (`reference_enclosure`, `strict_snaps`) are
  run parameters, set in the configuration as for any instance; every
  optical station's receiver construction, snap and reduction request carry
  them. A document does not set them. A block known exactly on the lattice
  is kept and every other block is moved by one fidelity-first procedure.
  The receiver's reference is handed beside the snap and the first-order
  bound is evaluated on it at the search's points
  (`meat-core/frank-wolfe/req:bracket-on-reference`), so a moved block
  carrying it is evaluated off its snap and rests on the receiver model; a
  moved block with no handed reference, or one of a run whose bound on the
  reference withdrew, is disclosed resting on A-SNAP. `reference_enclosure`
  decides which blocks are handed (the enclosed ones too, the default, or the
  exact ones alone); `strict_snaps` refuses wherever a moved block
  would rest on A-SNAP.
- The check of the acceptance set against the statistics the declared
  model can produce (`meat-core/req:unreachable-acceptance-set`; run
  parameters `statistics_check`, default `on`, and
  `min_model_pass_probability`, default 1/2) runs where the document supplies its honest statistics as
  data (an acceptance or raw table, or an envelope), where a caller replaces
  the document's model, or where the document declares explicit constraint
  entries. A library model with no explicit entries is not checked, and the
  record names A-REACH as the caller's to vouch for.
- Bounds, measured (`limits.py`): a photon cutoff of at most 7; a station of
  at most 32 modes and 8 ports; a photon-number block on the input modes at
  most 64-dimensional; and the receiver's work `3^ports * sum_n dim(n)^2` up
  to the deepest window at most 40,000 (four ports: windows up to 9; six: 3;
  eight: 1). The packaged instances' defaults and presets lie well inside.

## The `wcp_decoy` source

Polarisations (`part` H, V, + or -, with attributes), intensities, what a
generation and a test round send, the test coin and test intensity
probabilities, the entropy and source cutoffs. The lowering prepares the coin,
the categories and the Poisson enclosures on the declared lattice (default
2^-24), records them in `input_preparation`, and emits the tagged declaration
through the transmitter. A source cutoff is at most 100, an intensity at most
10, and at most 16 intensities and polarisations. `letter_label` reads
`round` and `polarisation` (and may read `intensity`). The source's links are
docked on the chain of its one optical station; the Band-A and several-station
lowerings dock no source segment, so the source is refused at load beside
`declared_povm` stations (`wcp_decoy_needs_optical_stations`) and beside two
or more optical stations (`wcp_decoy_needs_one_optical_station`).

## run_defaults and `default_config`

```yaml
run_defaults:
  rounds: 100000000
  endpoint_rule: bernstein
  completeness_budget: 1/1000000
  declared_tolerance: 1e-10                # binary64 fields: the value the literal denotes
  parameters: {alpha: 1.05, eps_pa: 2^-30, eps_ev: 2^-30, lambda_ec: 0}
  solver: {max_iterations: 2000}
  device: {acceptance_map: announcement-resolved}   # overrides a table default
  sections: merge                          # replace | merge
  derived: {exact_window: photon_cutoff + 1}
  derived_timing: unless_supplied          # base_only | unless_supplied
```

`solver` takes the ordinary choices `method` (`auto` or `fw`),
`budget_seconds` and `max_iterations`; the expert ones go under
`solver.advanced` (`method`: `pairwise`, `factor`, `entropy` or `corrective`;
`oracle`, `gap_tolerance`, `certified_evaluation`), as in `SolverSettings`. A
warm start is a run's choice and not a document field.

`default_config(**overrides)` builds the base from the table defaults and
`run_defaults.model`/`device`; with `base_only` it evaluates `derived` on the
base; a caller's `model=`/`device=` then replaces (`replace`) or is laid over
(`merge`) its section; with `unless_supplied` each derived key the caller did
not supply is evaluated on the combined values; `None` values are dropped
(a supplied `None` means absent); `RunConfig.from_inputs` runs last.

## Identity

`record_label` (default `declared.<id>`) prefixes every identity string a run
records. A custom document may not take a packaged instance's id (`bb84`,
`optical_bb84`, ...), may not set `record_label` to anything but its default,
and may not write a string beginning `instances.` (a `declared_by`, an
attestation, an honest note). Only `instances/<id>/protocol.yaml`, read with
`load_packaged`, is packaged. A custom document names no `readme`: the field
is a repository path a server serves as a file.

## Limits

The reader is a trust boundary for documents from an MCP client, so it is
bounded, and a document past a bound is refused rather than allowed to exhaust
the stack or memory: at most 1 MiB of text, nesting 64 deep and 200,000 values;
no YAML aliases or anchors in use; an expression of at most 1,024 characters,
256 tokens and 32 levels of nesting, decimal exponents within ±4096, and no
intermediate value beyond 65,536 bits.

## Refusals

A refused document raises `DocumentError`, a `RunError` and a `ValueError`,
with `reason` (a `DocumentReason`), `path` (a JSON pointer into the canonical
document) and `detail`. A configuration value is refused by the run tier's own
`RunInputError`; a module's refusal of the protocol is returned as data.

| Code | Refused |
| --- | --- |
| `document_unreadable` | text that does not parse; not one JSON object; a repeated key; a YAML alias; past a limit |
| `document_schema_violation` | a key, type or required field the schema does not admit; a switch case that is not a value of its choice |
| `format_version_unsupported` | a `format_version` other than `"1"` |
| `unknown_parameter_reference` | a name that is not a parameter (or not of that section) |
| `expression_invalid` | an expression or number string that does not parse, or one past a limit |
| `expression_division_by_zero` | a division by zero |
| `expression_not_integral` | a non-integer where an integer is required |
| `value_kind_mismatch` | a choice in arithmetic, a switch over a number, a per-port name without a port |
| `switch_case_missing` | a selected value with no case and no default |
| `alphabet_labels_not_distinct` | an alphabet repeating a label |
| `rule_reference_unknown` | a rule path naming no variable, or a component no entry has |
| `rule_value_invalid` | a matched rule whose value cannot be rendered |
| `matrix_malformed` | a ragged or unreadable matrix |
| `station_reference_unknown` | a station id that names no station |
| `station_kinds_mixed` | `declared_povm` and `optical` stations in one document |
| `wcp_decoy_needs_optical_stations` | a `wcp_decoy` source beside `declared_povm` stations, one or several: the Band-A lowering docks no source segment |
| `wcp_decoy_needs_one_optical_station` | a `wcp_decoy` source beside two or more optical stations: only the one-station optical lowering docks the source segment |
| `reserved_identity` | an identity a custom document may not claim, or a custom `readme` |
| `unsupported_topology` | three or more stations without a rule-written partition, an explicit or `none` witness and channel interface `none`; `factor_projection` without one station per party |
| `library_model_unknown`, `library_model_binding_invalid` | an honest model the library lacks, a binding that is not its parameters, a protocol its preconditions do not model |
| `honest_model_failed` | an honest model's arithmetic failure |
| `honest_table_invalid` | a raw honest table with a negative entry (an acceptance table or envelope is checked by the engine itself) |
| `user_entries_without_licence` | explicit constraint entries without an explicit `attack_set_license` |
| `source_refused` | the transmitter refused the source; `module_reason` is its own reason code |
| `wcp_source_invalid` | a `wcp_decoy` source the preparation cannot read: a missing test probability, an entropy cutoff outside `0..min(2, source cutoff)`, a lost category support, a negative intensity |
| `factor_assembly_refused` | the reductions refused to assemble the stations' factor emission; `module_reason` is their reason |
| `choice_weighting_refused` | the compiler refused a station's choice weighting; `module_reason` is its reason |
| `lowering_inconsistent` | a module emitted a station alphabet other than the one the tables were expanded over: a defect of the lowering, never of the document |

`unsupported_topology` also refuses, at `preparation`, a channel interface
that does not describe the stations (`qubit_identity` needs one declared
qubit, `single_photon` and `mode_intensity` one optical station, the latter a
`wcp_decoy` source, `bipartite` two optical stations).

## What you declare yourself

Some blocks are premises the engine cannot derive. Each one the document
supplies is listed in the run record (`protocol_document.user_declared`) and in
the key-rate report, in the result section and under the assumption it stands
under, and among the assumptions to vouch for:

| Kind | Where | Assumption |
| --- | --- | --- |
| `receiver_povm` | every `declared_povm` station | A-SPEC, A-IDEAL (the Band-A route's ideal-qubit-receiver premise) |
| `receiver_characterisation` | an optical station declared by port Grams, an instrument matrix, a C10 block or a dark-count channel | A-TRUST (the engine takes the numbers as exactly your device) |
| `retention_attestation` | `source.retention_attestation` | A-SRC |
| `constraint_entry` | each of `constraints.entries` | A-ATK |
| `attack_set_license` | `constraints.attack_set_license` (`supplier: user-declared:<id>`) | A-ATK |
| `feasibility_witness` | an explicit `constraints.feasibility_witness` | none: the compiler verifies it |

A packaged template (`instances/<id>/protocol.yaml`) records its items as a
custom document does: bb84's declared qubit POVM (`receiver_povm`) and
decoy_bb84's retention attestation (`retention_attestation`) are listed and
shown like your own, because whoever uses the key rates of a shipped template
takes responsibility for them too. The report words them
as declared in the run's protocol document, yours or a shipped template.
