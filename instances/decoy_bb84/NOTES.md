# Decoy-state BB84: developer notes

The page for someone inspecting or running the instance is
[README.md](README.md).

## Files

| File | What it is |
| --- | --- |
| `protocol.yaml` | the instance: a protocol document with a `wcp_decoy` source, one passive optical station, a two-message transcript and the three acceptance maps; its presets include a one-decoy configuration and a vacuum diagnostic |
| `surface.py` | loads `protocol.yaml` with the packaged loader and exposes the shared run surface |

The tagged
weak-coherent source's preparation -- category lattice, sector weights rounded
down from the transmitter's own Poisson enclosures, the
`TaggedSourceDeclaration` handed to `transmitter.decoy` -- is the library's
`instances/common/wcp.py`, which the document's `wcp_decoy` block calls; the
vacuum-output witness is `instances/common/witness.py`'s. The honest model,
coherent pulses through loss and misalignment, is the library model
`instances/common/honest/coherent_pulses.py`; the lowering's honest context is
the structure it is told.

Source and apparatus parameters live in the `device` section; the channel's
`transmittance` and `misalignment` live in `model`.

## Invariants that are easy to break

- **Three cutoffs, kept distinct.** The receiver's photon cutoff and exact
  window are independent of the source's entropy cutoff `N_ent` and truncation
  `N_src`. The source is declared through `ModeIntensityChannelInterface` with
  no finite encoding isometry.
- **Source masses are on a $2^{-24}$ lattice, split afterwards.** Category
  masses (generation, and one test category per intensity) are snapped
  together by the shared family routine and only then split equally over the
  polarizations, which keeps bit symmetry. Poisson weights are exact
  alternating-series lower bounds rounded down to the same lattice; the
  shortfall goes to the tail flags. Weighted dyads have denominators at most
  $2^{51}$, so every entry and partial sum is binary64-exact. A positive
  category too small for the lattice is refused, never dropped.
- **Source preparation builds the ensemble presentation only**: weighted
  blocks and their transposes. No Alice POVM, inverse square root, support
  compression or block certificate is constructed here.
- **The honest provider is a model prediction, not a proof-critical
  enclosure.** Exponentials use `Decimal` at precision 60, then exact rational
  arithmetic combines click patterns and normalizes the six outcomes. Click
  probabilities do not depend on either proof cutoff.
- **The receiver merges every pattern with two or more clicks into `mc`.**
  A comparison with a literature protocol that resolves click patterns must
  state that coarsening; no equality with published curves is claimed.
- On the licensed routes the compiler checks the supplied vacuum-output
  witness; feasibility is never inferred from the provider that built it.

## Frozen registry and tests

`tests/oracles/registry_instances_decoy_bb84.py` holds threshold-pair toy
instances, not this four-detector apparatus. Tests compare its component
limits, together with independent vacuum and coherent-port formulas; they do
not treat the toy numbers as this receiver's full output.

Tests: `tests/unit/test_decoy_bb84_{source,protocol,surface}.py`,
`tests/property/test_declared_poisson_enclosures.py`,
`tests/unit/test_transmitter_decoy.py`, `tests/integration/test_decoy_bb84_*.py`,
`tests/integration/test_decoy_literature_limits.py`.
