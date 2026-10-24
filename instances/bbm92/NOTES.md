# BBM92: developer notes

The page for someone inspecting or running the instance is
[README.md](README.md); the honest models are derived in
[pair_models.md](../common/honest/pair_models.md), beside the library models.

## Files

| File | What it is |
| --- | --- |
| `protocol.yaml` | the instance: a protocol document with an untrusted pair source and two passive optical stations (`alice_station`, `bob_station`), each with its own cutoff, window and route, docked as two factors (`factor_projection`), Alice's test coin as a `choice_weighting`, and the BBM92 transcript; `key_bases`, `source_model`, `party_local_view`, `route` and `acceptance_map` switch the rest |
| `surface.py` | loads `protocol.yaml` with the packaged loader and exposes the shared run surface |

The two honest models
are library models in `instances/common/honest/`: `ideal_pair.py` (the ideal
pair and its honest provider) and `spdc_pair.py` (`prepare_station_grams`, the
reduced no-click determinant and inclusion–exclusion over click patterns).
Their derivation is [pair_models.md](../common/honest/pair_models.md).

The document lowering wires both stations through `MultiDeviceRequests`
(`instances/declared/lowering/providers.py`), with the factor witness of
`instances/common/witness.py`; their ledgers and numerical preparation are
carried by the shared production runner.

## Invariants that are easy to break

- **The source is untrusted.** The compiled protocol has $d_A=1$, untrusted
  source mode and no marginal condition. The honest models predict frequencies
  only and supply no certificate.
- **The test coin sits inside the compiled measurement family**, not applied
  afterwards. When preparation is needed it goes on a $2^{-12}$ lattice before
  the stations' $2^{-40}$ receiver entries are weighted, so an input such as
  `1/5` need not stay `1/5`. The input-preparation record shows the coin used.
- **Station Grams are floating outputs.** `prepare_station_grams` adds the
  unmonitored-loss effect and snaps the family with `snap_family_exact`. Its
  displacement declares a new honest optical model. It is not a continuity
  bound on the key rate. The resulting frequency table is prepared again by
  the run input adapter, which keeps a separate record.
- **Bob's Gram enters the SPDC determinant transposed, not adjointed.** The
  complex Grams in `tests/unit/test_bbm92_spdc.py` tell the two apart. The
  eight-dimensional determinant there checks the reduction; it is not a frozen
  oracle.
- **`party_local_view=licensed_scalar`** selects the reductions supplier's
  already-licensed scalar consequence and keeps its licence provenance. The
  instance never retags an entry itself, and the encoded route rejects the
  option. `tests/integration/test_bbm92_licensed_constraints.py` exhibits a
  scalar-feasible state that violates a party-local row (a feasible-set
  comparison, not a key-rate claim).
- A station's default exact window is its own cutoff plus one. An explicitly
  absent window selects the analytic high-photon bound.

## Frozen registry

`tests/oracles/registry_instances_bbm92.py` fixes a Z-only key protocol with
test bias `1/5`; `key_bases=("Z",)` expresses it here. A comparison must
normalize by the actual prepared sifted-generation mass and state the
protocol difference: in the ideal lossless symmetric device both-basis
generation has mass $(1-\gamma)/2$ and Z-only $(1-\gamma)/4$. The registry
also separates the objective at the depolarized honest state from the
optimizer's infimum at the same error statistics. No frozen value is changed.

## Tests

`tests/unit/test_bbm92_{instance,spdc,surface,acceptance_maps,entropy}.py`,
`tests/oracles/test_bbm92_registry_integrity.py`,
`tests/integration/test_bbm92_*.py`.
