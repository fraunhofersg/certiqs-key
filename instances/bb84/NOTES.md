# Ideal qubit BB84: developer notes

The page for someone inspecting or running the instance is
[README.md](README.md).

## Files

| File | What it is |
| --- | --- |
| [protocol.yaml](protocol.yaml) | the instance: a Band-A protocol document (descriptor, parameters, presets, source, Bob's declared qubit POVM, public rules, honest model) |
| [surface.py](surface.py) | loads `protocol.yaml` with the packaged loader and exposes the shared run surface |
| [specification.py](specification.py) | `bb84_specification` (the Band-A declaration) and `conjugation_example_specification` (the Y-basis example): the protocol compiler's worked declaration, not the run path |
| [parameters.yaml](parameters.yaml) | the three basis-weight fixtures (the template's presets are held equal to them) and the declared source, receiver and chain data |
| [declare.py](declare.py) | `declare_acceptance_frequencies`, a test helper for meat-core's `rem:optol-reach`; the run path does not use it |

`specification.py` and `parameters.yaml` are the compiler's worked
declaration (PC12, `ex:conj`), cited by the protocol compiler's contract and
imported by the golden tests; the document's lowered specification is held
equal to `bb84_specification(...)`
(`tests/unit/test_declared_lowering.py`).

The worked derivations (certificate, D(i)–D(viii), gates, key map, statistics
at the noiseless state, and both conjugation branches) are frozen, with their
arithmetic, in the `O-PC-BB84` and `O-PC-CONJUGATION` entries of
[tests/oracles/registry_instances_bb84.py](../../tests/oracles/registry_instances_bb84.py).
They are never regenerated from the code. The instance is data: no claim of
the compiler depends on it.

## Invariants that are easy to break

- **The conjugation is applied in the specification, only in
  `conjugate_projector`.** The compiler multiplies the weight in and does not
  conjugate. On the four BB84 states conjugation is the identity (all real
  amplitudes), so a reversed convention is invisible here. Only the Y-basis
  example can detect it: `ConjugationConvention.OMITTED` builds the wrong branch
  on purpose, and compiling it at $d_A=2$ must be refused by gate (G2) on
  (SR2). Do not "simplify" the second constructor away.
- **`_basis_weights` checks $p_{\mathsf Z}+p_{\mathsf X}=1$ on the computed
  binary64 total, not the exact rational sum.** The binary64 literals `0.9` and
  `0.1` therefore pass the constructor and are refused by the compiler, as the
  refusal record `choice_weights_not_normalized`
  (`protocol-compiler/req:weight-list`, which decides the weight list on the
  exact sum). This is the instance's one compile failure mode. Deciding the
  sum exactly in the constructor would turn that refusal into an exception.
  The surface prepares ordinary inputs onto weights that sum to exactly 1 and
  records the displacement, so a run from `default_config` does not meet this
  case.
- **The block kind is `proof_sector`** (`band_a_block_kind`): the one-sector
  map is justified by source replacement, not by a photon number.
- The declared statistics at $\omega=\lvert\Phi^+\rangle\langle\Phi^+\rvert$
  check the emitted declaration. They are not the honest model, which is
  the library model `depolarized_bell_pair`
  (`instances/common/honest/depolarized_bell_pair.py`, parameter `qber`). The
  receiver is the idealization A-IDEAL.

## Tests

- `tests/golden/test_protocol_compiler_against_registry.py`,
  `test_protocol_compiler_conjugation.py`,
  `test_protocol_compiler_marks_executed.py`: the declaration and both
  conjugation branches against the frozen registry, including the `0.9`/`0.1`
  refusal.
- `tests/unit/test_bb84_closed_forms.py`, `test_bb84_honest_provider.py`,
  `test_bb84_wire_bundle.py`; `tests/integration/test_bb84_slice.py`
  (end-to-end run and record).
- `tests/unit/test_declared_lowering.py`: the document's specification is
  `bb84_specification(...)` and its preparation record the reference
  preparation's, at the defaults, every preset and edits.
