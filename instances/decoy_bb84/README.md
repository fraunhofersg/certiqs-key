# Decoy-state BB84

BB84 with phase-randomized weak coherent pulses and decoy intensities. Alice's
laser pulses contain a Poisson-distributed number of photons; she varies the
pulse intensity between a signal, a weak decoy and a vacuum decoy, so the test
statistics reveal how the channel treats each photon number. Bob uses the same
passive four-detector receiver as [optical BB84](../optical_bb84/README.md).

## Setup

| Part | What it is | Trust |
| --- | --- | --- |
| Alice (source) | phase-randomized coherent pulses at intensities $\mu_{\mathrm s}$, $\mu_{\mathrm w}$, $\mu_{\mathrm v}$ (mean photon numbers), polarized $H$, $V$, $D$ or $A$ | trusted: phase randomization, intensities and polarizations as declared |
| Channel | carries the pulses to Bob | untrusted: any attack |
| Bob (receiver) | beamsplitter basis choice, polarizing beamsplitters and four threshold detectors | trusted: characterized exactly by the declared model |

## One round

1. Alice flips her test coin: a test round with probability $\gamma$,
   otherwise a generation round.
2. **Generation**: signal intensity, $\mathsf Z$ basis, $H$ or $V$ with
   probability $\tfrac12$ each.
   **Test**: intensity signal, weak or vacuum with the declared test
   probabilities, and polarization $H$, $V$, $D$ (`plus`) or $A$ (`minus`) with
   probability $\tfrac14$ each.
3. Bob's detectors give `H`, `V`, `D`, `A` (one click), `nc` (no click) or
   `mc` (two or more clicks).
4. Alice announces `gen-Z` in a generation round, and her full letter, such as
   `test-weak-plus`, in a test round.
5. Bob answers. After `gen-Z` he announces only his basis: `Z` for `H` or
   `V`, `X` for `D` or `A`, or `nc` or `mc`. In a test round he announces his
   outcome.
6. A generation round where Bob announces `Z` is a key round. The key bit is
   **Alice's** ($H\to0$, $V\to1$); Bob's `H` or `V` is his copy, and a
   disagreement is an error for error correction to fix.

Test rounds check both bases at every intensity: `H` should give `H`, `V`
gives `V`, `plus` gives `D`, `minus` gives `A`. Bob's multi-clicks are
reported as the single outcome `mc`, never as individual click patterns.

## Reading the labels

| Label | Meaning |
| --- | --- |
| `gen-signal-H`, `gen-signal-V` | Alice's generation letters |
| `test-<intensity>-<pol>`, e.g. `test-vacuum-minus` | Alice's test letters: intensity `signal`, `weak` or `vacuum`, polarization `H`, `V`, `plus` ($D$) or `minus` ($A$) |
| `H`, `V`, `D`, `A`, `nc`, `mc` | Bob's outcome |
| `gen-signal-H\|V` | a joint outcome: Alice's letter, then Bob's outcome |

**Acceptance values** depend on `acceptance_map`; the default is
`announcement-resolved`.

| `acceptance_map` | Values |
| --- | --- |
| `merged-discard` | `gen`; `test-<i>-Z-ok`, `test-<i>-Z-error`, `test-<i>-X-ok`, `test-<i>-X-error` per intensity $i$; one `disc` for everything else |
| `announcement-resolved` | `gen`, `gen-X`, `gen-nc`, `gen-mc`; per intensity the four ok/error values plus `test-<i>-mismatch`, `test-<i>-nc`, `test-<i>-mc` |
| `pair-resolved` | the generation values as above; every test announcement pair on its own, e.g. `test-weak-plus-D` |

`ok` and `error` are single clicks in the basis Alice tested, `mismatch` is a
single click in the other basis. Under the resolved maps the alphabet also
lists `gen-H`, `gen-V`, `gen-D` and `gen-A`. They exist because every
announcement table is complete, but no round produces them, and their
frequency is zero. No map records a generation bit.

## Parameters

| Parameter | Section | Default | Meaning |
| --- | --- | --- | --- |
| `gamma` | device | $\tfrac14$ | test-round probability $\gamma$ |
| `mu_signal`, `mu_weak`, `mu_vacuum` | device | $\tfrac45$, $\tfrac15$, $0$ | mean photon number of each intensity; the weak and vacuum decoys are sent in test rounds only |
| `test_signal`, `test_weak`, `test_vacuum` | device | $\tfrac12$, $\tfrac14$, $\tfrac14$ | intensity probabilities within a test round; they sum to one |
| `transmittance` | model | $1$ | channel power transmittance |
| `misalignment` | model | $0$ | $\sin^2$ of the channel's polarization rotation, in $[0,\tfrac12]$ |
| `entropy_cutoff` | device | $1$ | $N_{\mathrm{ent}}$: photon numbers up to here stay quantum in the analysis (at most 2) |
| `source_cutoff` | device | $6$ | $N_{\mathrm{src}}$: photon numbers up to here keep a sector of their own |
| `photon_cutoff` | device | $1$ | receiver cutoff $N$: photon numbers up to $N$ at Bob are modelled exactly |
| `exact_window` | device | $2$ | receiver exact window $m^{\ast}$, above $N$; see [optical BB84](../optical_bb84/README.md) |
| `basis_split`, `half_wave_angle`, `pbs_leak_transmitted`, `pbs_leak_reflected` | device | $\tfrac12$, $\tfrac18$, $0$, $0$ | receiver optics, as in optical BB84; the angle is in units of $\pi$; light a PBS leaks the wrong way clicks the other detector of the pair, because each detector watches both polarizations of its path |
| `efficiency`, `dark_count` | device | $1$, $0$ per detector | detection efficiency and dark-click probability of `H`, `V`, `D`, `A` |
| `efficiency_normalization` | device | empty (the largest efficiency divided by $\tfrac{99}{100}$, or $1$ where it is at least $\tfrac{99}{100}$) | receiver factored loss $t$, as in optical BB84 |
| `route` | device | `encoded` | receiver photon-number reduction: `encoded`, `licensed` or `licensed+two-sector`, as in optical BB84 |
| `acceptance_map` | device | `announcement-resolved` | see above |

The three cutoffs are separate choices: two for the source, one for the
receiver.

**Presets**

| Preset | Change from the defaults |
| --- | --- |
| `two-decoy` | none: signal plus weak and vacuum decoys |
| `one-decoy` | tests use signal and weak only, $\tfrac12$ each |
| `vacuum` | all three intensities zero, a check of the vacuum sector |

The default run uses $n=10^8$ rounds, completeness budget $10^{-6}$,
$\alpha=1.05$, $\varepsilon_{\mathrm{PA}}=\varepsilon_{\mathrm{EV}}=2^{-30}$,
$\lambda_{\mathrm{EC}}=0$, at most 2000 solver iterations, and the `bernstein`
rule for the acceptance intervals. That rule keeps the same completeness
guarantee as exact binomial endpoints with a possibly wider acceptance set;
`exact` is available.

## How the source enters the analysis

A phase-randomized pulse of intensity $\mu$ is a mixture of photon numbers with
Poisson weights $P_\mu(n)=e^{-\mu}\mu^n/n!$. The analysis splits it by photon
number:

- $n\le N_{\mathrm{ent}}$: a quantum sector, where the polarization state
  enters the entropy bound;
- $N_{\mathrm{ent}}<n\le N_{\mathrm{src}}$: a classical flag for each pair of
  photon number $n$ and polarization, shared by all intensities;
- $n>N_{\mathrm{src}}$: one tail flag per polarization and intensity.

The sector weights are certified lower bounds on $P_\mu(n)$, rounded down to a
$2^{-24}$ grid; everything they leave out goes to the tail. The round-type and
intensity probabilities are put on the same grid. The run records every such
change. A category too small for the grid is refused rather than dropped.

## The honest model

Each pulse is a coherent state of intensity $\mu$. The channel rotates its
polarization by an angle $\theta$ with $\sin^2\theta$ = `misalignment` and
attenuates it by `transmittance` $T$. After Bob's optics, detector $k$ sees a
share $P_k$ of the pulse's power and fails to click with probability

$$(1-d_k)\,e^{-\eta_k\,\mu\,T\,P_k},$$

independently of the other detectors, where $\eta_k$ is its efficiency and
$d_k$ its dark-click probability. A single click on $k$ is a click on $k$ and
none elsewhere; `mc` is every other outcome with a click. The statistics are
per round over all outcomes. They do not depend on any cutoff.

**Example.** At the defaults, `test-vacuum-H|nc` $=\tfrac1{64}$: a test round
($\tfrac14$) at vacuum intensity ($\tfrac14$) with polarization $H$
($\tfrac14$), and an empty pulse never clicks without dark counts. And
`gen-signal-H|H` $\approx0.0829$: a generation round with $H$
($\tfrac{3}{8}$) times the probability that only detector `H` clicks,
$(1-e^{-0.4})\,e^{-0.4}$, since the $\mathsf Z$ arm's `H` port receives
power $0.4$ and each $\mathsf X$ port $0.2$.

## The key-rate result

A run builds an acceptance set from the honest statistics, the round count $n$
and the completeness budget: with independent honest rounds, the honest
implementation aborts with probability at most that budget. It then bounds the
key the protocol can extract against any channel attack, given the trusted
source and receiver above.

| Field | Meaning |
| --- | --- |
| key length $\ell$ | final key bits for $n$ rounds. This is the headline. |
| `h_lb`, tier `first-order` | a lower bound on the entropy per round, the number $\ell$ is computed from |
| `h_low` | the objective at the solver's last point: an estimate of the minimum entropy per round, shown as a diagnostic, never a bound. The point is feasible only within a window, so the estimate need not lie above the true minimum (`meat-core/frank-wolfe/thm:firstorder` (iiia)) |
| Frank-Wolfe gap | the solver's convergence measure at its last point: `h_low` minus the gap is the lower bound from that point, and `h_lb` is the best such bound over the run. A large gap means the solver has not converged: `h_lb` is still valid but may lie well below the true minimum, which costs key |

$$\ell=\max\Big\{0,\Big\lfloor n\max\{0,h_{\mathrm{lb}}\}-\lambda_{\mathrm{EC}}
-\big\lceil\log_2\tfrac{1}{\varepsilon_{\mathrm{EV}}}\big\rceil
-\tfrac{\alpha}{\alpha-1}\log_2\tfrac{1}{\varepsilon_{\mathrm{PA}}}+1\Big\rfloor\Big\}$$

- `h_lb` is valid when the solver's linear subproblems are solved exactly. That
  assumption is named in the record and not budgeted.
- $\lambda_{\mathrm{EC}}$ is the error-correction leakage in bits. At its
  default of zero, $\ell$ charges nothing for correcting Bob's errors; set it to
  your reconciliation's leakage for a practical key length.
- A negative `h_lb` is reported as zero key and flagged. A run can also end
  in a refusal instead of a number; the record names the stage that refused and
  why.
- Because Bob reports multi-clicks as one outcome and tests use all four
  polarizations, results are not directly comparable with protocols that
  resolve click patterns or test only one basis.
- The run record lists every assumption the result rests on, including the
  weak-coherent source model and the characterized receiver.

## Written as a protocol document

This instance is the protocol document [protocol.yaml](protocol.yaml): its
parameters, presets, weak-coherent source, receiver optics and transcript are
data there, and [surface.py](surface.py) only loads it. To start a protocol of
your own, copy it and customise it as its header says; the format is described
in [the protocol-document guide](../declared/README.md), and the MCP server
serves this document as a template.
