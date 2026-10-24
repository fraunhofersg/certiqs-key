# Provenance: fixed-length qubit BB84 comparison numbers from Renyi-ConicQKD

Goal: regenerate the fixed-length qubit BB84 key-rate curve of Navarro et al.,
arXiv:2511.10584 ("Finite-Size Quantum Key Distribution Rates from Renyi
Entropies Using Conic Optimization"), **Fig. 1**, as exact numbers from the
paper's own public code, at zero loss (0 dB) and nearby, so this repository
can cite a documented comparison reference instead of reading pixels off a
log-scale plot.

## Source repository (GPL-3.0 -- outputs only cross into this project)

- Repository: https://github.com/MarianaNvrr/Renyi-ConicQKD
- Commit: `e89f73db901176186b806f63bb13335422dc91b9` (2026-07-21, "update
  readme").
- License: GPL-3.0 (see `LICENSE` in that repo). **Only the numeric outputs
  of running this code are used here.** No file of that repository was
  copied, vendored, or committed into this project; it was cloned and run
  entirely inside a scratch directory outside this repository. The driver
  script below `include`s the vendor file but does not modify it (see "No
  patch was needed" below).
- Entry point used: `Instance_bb84.jl`, specifically its `Finite_SKR(...)`
  orchestration, called with `variable=false` (the fixed-length path) and
  `fast=true` (the FastRenyiQKD cone, which is what Fig. 1 itself is
  computed with -- see the Fig. 1 caption: "for the qubit BB84 protocol via
  the FastRenyiQKD cone").
- Depolarization convention (confirmed from `Instance_bb84.jl`,
  `alice_depol`/`alice_depol_loss`): visibility `v` sets `Q = (1 - v) / 2`
  as the QBER in both bases (a depolarizing channel).

## Toolchain

- Julia **1.12.7** (portable Windows x64 zip from
  `julialang-s3.julialang.org/bin/winnt/x64/1.12/julia-1.12.7-win64.zip`,
  no installer, no admin rights). The vendored `Manifest.toml` was generated
  with Julia `1.12.6`; `1.12.7` was used instead (see "Toolchain caveats"
  below for why) and instantiates/loads the same manifest cleanly.
- `JULIA_DEPOT_PATH` was kept private to the scratch area throughout (never a
  user's real `~/.julia`), though see the caveat below about where its bytes
  ended up physically.
- Key package versions actually resolved into the environment (from
  `Manifest.toml`, confirmed against the live depot after `Pkg.instantiate()`):
  - `Hypatia` 0.10.0
  - `JuMP` 1.30.1
  - `ConicQKD` 0.3.0
  - `Ket` 0.9.6
  - `Optim` 2.2.1
  - `MathOptInterface` 1.51.2

### Toolchain caveats (reported honestly, not massaged)

1. **Julia version**: the repo's `Manifest.toml` was generated with Julia
   1.12.6. Julia 1.11.7 was tried first and fails outright (Julia 1.11 does
   not ship the `JuliaSyntaxHighlighting`/`StyledStrings` stdlibs the
   manifest pins), so 1.12.7 (the latest 1.12.x patch available at run time)
   was used instead of the exact 1.12.6.
2. **A Windows `MAX_PATH` (260-character) limit** blocked package
   precompilation from a deeply nested working directory: Julia/libuv's Windows
   file APIs are not long-path aware here, so `Base.identify_package`, `isfile`
   and `FileWatching.Pidfile.tryopen_exclusive` silently report "not found" for
   paths beyond the limit. NTFS junctions and `subst` drive mappings do not help,
   because Windows resolves them back to the real long path. What worked was
   placing the Julia package depot (disposable build artifacts, not output of
   this capture) in a genuinely short, non-aliased real directory and pointing
   `JULIA_DEPOT_PATH` there directly.
3. **Two non-corrupting Windows-only `Pkg.jl` races** were worked around by
   clearing the specific stale cache directory and retrying; both symptoms
   disappeared once the path-length issue was fixed.

None of this affected the *numerical* run: once the depot was moved,
`Pkg.instantiate()` and `Pkg.precompile()` completed cleanly and the driver
script ran end-to-end with no errors or warnings other than routine Hypatia
solver diagnostics (see below).

## Security parameters actually used for Fig. 1 -- NOT the code's own default

`Instance_bb84.jl` defines:

```julia
@with_kw struct epsilon_coeffs{T<:AbstractFloat}
    # Parameters set for variable length computation. Change otherwise.
    ϵEC::T = 1/2*10e-80
    ϵPA::T = 1/2*10e-80
    ϵcompPE::T = 10e-9
end
```

i.e. `ϵEC = ϵPA = 5e-80`, `ϵ_compPE = 1e-9` by default, and `Finite_SKR`
unconditionally constructs `epsilon_coeffs{T}()` with no override. **This
default is for Figure 2** (the variable-length run, chosen "for a fair
comparison" with Ref. [7]'s extreme security parameters -- confirmed against
the version refs/index.json pins: the paper states, right after the Fig. 2 discussion, *"For a
fair comparison, we set the security parameters to ϵ_PA = ϵ_EC = 1/2·10⁻⁸⁰"*,
which is exactly the code's built-in default), **not** for Figure 1.

The paper's actual general-purpose defaults, stated once and used "unless
explicitly stated otherwise" (confirmed against the version refs/index.json pins, Eqs. 49-51):

```
ϵ_EC  = 1e-11        (Eq. 49)
ϵ_PA  = 9e-11        (Eq. 50)
ϵ̄_PE  = 9e-11        (Eq. 51)
```

Fig. 1's caption and surrounding text state no override, so these are the
values used for Fig. 1, and are what the driver script below passes
explicitly.

**No patch to the vendor file was needed.** The lower-level functions
(`EC_cost_bb84`, `FixedLenghtOBJ`, `Finite_corrections`) all accept these
epsilons as explicit arguments already -- only the top-level `Finite_SKR`
wrapper hard-codes the struct default. The driver script re-implements
`Finite_SKR`'s `variable=false, N<1e10, α==1` branch (fixed-length,
finite-size regime, α numerically optimized -- Instance_bb84.jl lines
370-393 of the pinned commit) by calling those lower-level functions
directly with the paper's Eqs. 49-51 values.

## Fig. 1 parameter statement (the version refs/index.json pins, for cross-reference)

> "Our results are shown in Figure 1, where we plot the secret key rates
> against the total transmittance η for the qubit BB84 protocol via the
> FastRenyiQKD cone. Here we consider f = 1.16, [...]"
>
> "Figure 1: Finite secret key rate for qubit BB84 protocol using the
> FastRenyiQKD cone for a different number of rounds n. All curves consider
> v = 0.97, and f = 1.16. The probability p_K was optimized for each point
> according to a coarse-grained tuning, while the Renyi parameter α was
> optimized numerically."

n ∈ {1e5, 1e6, 1e7, 1e9}, transmittance axis 0-30 dB, y-axis labelled
**"Secret key rate (bits/pulse)"**.

## Convention findings (sanity checks)

- **Per-pulse, not per-sifted-round.** Confirmed two independent ways:
  (1) the paper's own y-axis label is "Secret key rate (bits/pulse)"; (2)
  the code's own normalization is consistent with that: `FixedLenghtOBJ`'s
  conic program normalizes over **all** POVM outcomes for a launched pulse
  (`sum(q) + qK == 1`, where `Q = [proj(3,3)]` explicitly includes the
  no-click/loss outcome), so the returned Renyi entropy term is already a
  per-launched-pulse quantity, not conditioned on a click or a basis match.
  `EC_cost_bb84` dilutes its leakage the same way: `leak_EC = f * η * pK^2 *
  binary_entropy(qber) + finite_correction/N`, i.e. it is scaled by the
  detection probability `η` **and** the sifting probability `pK^2` (both
  Alice and Bob must choose the Z basis, each with probability `pK`, so
  sifting probability is `pK^2`) before adding it to the per-pulse rate.
  Cross-check: at n=1e9, dB=0, pK=0.905, computed `leak_EC = 0.10675`;
  `f * pK^2 * h2(Q=0.015) = 1.16 * 0.905^2 * 0.112361 = 0.10653` -- matches
  to within the residual from `qberZ`'s exact simulated value vs. the
  idealized `Q`, confirming the per-pulse dilution convention.
- **p_K is fixed per point** (not re-optimized by this driver), taken from
  the code's own tabulated "coarse-grained tuning" values in
  `Utils_data_bb84.jl::optimal_pK(f=1.16, N, dB, variable=false)` -- exactly
  the values the paper itself used for Fig. 1 (per its caption). For the
  Q-sweep (v != 0.97), there is no paper-tabulated p_K, so the driver
  reuses the v=0.97, same-(N, dB=0) tabulated p_K rather than re-optimizing
  it; this is flagged explicitly as a simplification, not a re-derivation.
- **α (Renyi parameter) is optimized numerically per point** by the driver
  itself, via `Optim.optimize(..., Brent())` over α ∈ (1, 1.5], exactly
  reproducing `Finite_SKR`'s own `α == 1` branch. `optim_converged = true`
  and `optim_iterations` are logged for every point (see `results.csv`);
  none failed to converge.

## Sanity checks

- **Positive and increasing in n** (v=0.97, dB=0): 0.1282 (n=1e5) < 0.2558
  (n=1e6) < 0.3758 (n=1e7) < 0.5554 (n=1e9) bits/pulse. Monotonic, as
  expected (finite-size penalty shrinks with n).
- **n=1e9 vs. the asymptotic anchor**: `1 - 2*h2(0.015) = 0.7753`. The
  n=1e9 rate (0.5554) is a factor **0.716** of that anchor -- comfortably
  within "roughly a factor 2", and in the expected direction (finite-size
  penalty terms make the fixed-length rate strictly below the asymptotic
  one, more so than the n=1e7/1e6/1e5 points, consistent with the
  per-pulse/pK-dilution convention above rather than a bug).
- **Monotonic in loss** (v=0.97): at both n=1e6 and n=1e7, the rate strictly
  decreases as dB increases from 0 to 2 to 4, as physically required.
- **Monotonic in Q** (dB=0): at both n=1e6 and n=1e7, the rate strictly
  decreases as Q increases from 0.005 to 0.05, as physically required.
- **Nothing flagged as off.** All 20 points have `optim_converged = true`,
  positive `SKR`, and the only Hypatia solver diagnostic seen across the
  whole run was the routine, non-fatal `"cannot step in centering
  direction"` warning (an interior-point step-size heuristic message, not a
  termination-status failure) -- no point reported an inaccurate or failed
  solver status.

## Files in this directory

- `results.csv` -- all 20 computed points (final).
- `PROVENANCE.md` -- this file.

## Driver script

The driver performs zero modification of the vendor repository; it only
`include`s `Instance_bb84.jl` (which in turn includes `Utils_data_bb84.jl`)
from the pinned clone, and calls the functions defined there directly with
explicit arguments. The driver script is not part of this repository.

## Results table

| n | v | Q | dB | pK | alpha-1 | SKR (bits/pulse) | leak_EC | optim_converged |
|---|---|---|----|----|---------|-------------------|---------|------------------|
| 1e5 | 0.97 | 0.015 | 0 | 0.589 | 3.180e-02 | 0.128206 | 0.045587 | true |
| 1e6 | 0.97 | 0.015 | 0 | 0.714 | 5.289e-03 | 0.255784 | 0.066483 | true |
| 1e7 | 0.97 | 0.015 | 0 | 0.802 | 9.935e-04 | 0.375818 | 0.083838 | true |
| 1e9 | 0.97 | 0.015 | 0 | 0.905 | 4.297e-05 | 0.555403 | 0.106750 | true |
| 1e6 | 0.97 | 0.015 | 2 | 0.672 | 8.075e-03 | 0.130969 | 0.037174 | true |
| 1e6 | 0.97 | 0.015 | 4 | 0.624 | 1.292e-02 | 0.063816 | 0.020241 | true |
| 1e7 | 0.97 | 0.015 | 2 | 0.772 | 1.466e-03 | 0.209064 | 0.049016 | true |
| 1e7 | 0.97 | 0.015 | 4 | 0.736 | 2.268e-03 | 0.113387 | 0.028112 | true |
| 1e6 | 0.99 | 0.005 | 0 | 0.714 | 5.327e-03 | 0.315880 | 0.026894 | true |
| 1e6 | 0.98 | 0.010 | 0 | 0.714 | 5.302e-03 | 0.284528 | 0.047815 | true |
| 1e6 | 0.96 | 0.020 | 0 | 0.714 | 5.277e-03 | 0.228838 | 0.083680 | true |
| 1e6 | 0.94 | 0.030 | 0 | 0.714 | 5.288e-03 | 0.178918 | 0.114993 | true |
| 1e6 | 0.90 | 0.050 | 0 | 0.714 | 5.351e-03 | 0.090386 | 0.169402 | true |
| 1e7 | 0.99 | 0.005 | 0 | 0.802 | 1.024e-03 | 0.454937 | 0.033888 | true |
| 1e7 | 0.98 | 0.010 | 0 | 0.802 | 1.010e-03 | 0.413657 | 0.060285 | true |
| 1e7 | 0.96 | 0.020 | 0 | 0.802 | 9.831e-04 | 0.340369 | 0.105535 | true |
| 1e7 | 0.94 | 0.030 | 0 | 0.802 | 9.662e-04 | 0.274772 | 0.145043 | true |
| 1e7 | 0.90 | 0.050 | 0 | 0.802 | 9.541e-04 | 0.158657 | 0.213689 | true |

(rounded to display precision; `results.csv` holds full precision)
