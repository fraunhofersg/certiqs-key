# Optical BB84 with a characterized receiver

BB84 with a passive optical receiver and four threshold detectors. Alice sends
BB84 polarization states; Bob's basis is chosen by a beamsplitter, and he
announces which detector clicked. The receiver's measurement is computed from
the optical components you set, so loss, detector efficiency, dark counts and
multi-photon inputs all enter the result.

## Setup

| Part | What it is | Trust |
| --- | --- | --- |
| Alice (source) | picks basis $\mathsf Z$ or $\mathsf X$ with probability $\tfrac12$ each and a uniform bit | trusted: her states are exactly as declared |
| Channel | carries light from Alice to Bob | untrusted: the adversary may deliver any optical state, with any photon number |
| Bob (receiver) | the passive optics and detectors below | trusted: characterized exactly by the declared model |

```
channel ---->[ BS ]--+--> Z arm ------------->[ PBS ]--> H , V
                     |
                     +--> X arm --[ HWP ]---->[ PBS ]--> D , A
```

The beamsplitter chooses Bob's basis passively. In the $\mathsf X$ arm a
half-wave plate at $\pi/8$ rotates the diagonal basis onto the rectilinear one,
so a second polarizing beamsplitter (PBS) separates $D$ from $A$. Each of the
four outputs has one threshold detector, which registers a click or no click
and cannot count photons. The receiver has eight optical modes, four paths with
two polarizations each; the channel enters on the $\mathsf Z$ path, and the
other three inputs are vacuum.

## One round

1. Alice sends one of four states: `(Z,0)` = $H$, `(Z,1)` = $V$,
   `(X,0)` = $D$, `(X,1)` = $A$.
2. Bob's detectors produce one of six outcomes: exactly one click (`H`, `V`,
   `D` or `A`), no click (`nc`) or more than one click (`mc`).
3. Announcements. Alice announces `Z` for a $\mathsf Z$ state and her full
   letter `(X,0)` or `(X,1)` for an $\mathsf X$ state. Bob announces `Z` for a
   single click on `H` or `V`, `(X,0)` for `D`, `(X,1)` for `A`, and `nc` or
   `mc` otherwise.
4. Key rounds are those where both announce `Z`. The key bit is **Alice's**
   bit ($H\to0$, $V\to1$); Bob reads `H` as 0 and `V` as 1, and a
   disagreement is an error for error correction to fix.
5. When both announce an $\mathsf X$ letter, both bits are public, so the round
   is a test: equal bits are `ok`, different bits `err`. Every other round,
   including no-click and multi-click rounds, is discarded but still counted in
   $n$. That is how loss is accounted for.

## Reading the labels

| Label | Meaning |
| --- | --- |
| `(Z,0)`, `(Z,1)`, `(X,0)`, `(X,1)` | Alice's letter: basis and bit |
| `H`, `V`, `D`, `A` | Bob's outcome: exactly this detector clicked |
| `nc` | no click |
| `mc` | multi-click: two or more detectors clicked |
| `(Z,0)\|V` | a joint outcome: Alice's letter, then Bob's outcome |

## Parameters

| Parameter | Section | Default | Meaning |
| --- | --- | --- | --- |
| `qber` | model | $0$ | error parameter $Q\in[0,\tfrac12)$ of the depolarizing channel |
| `transmittance` | model | $1$ | probability $\eta$ that the photon reaches Bob; at $0$ Bob sees only dark counts |
| `basis_split` | device | $\tfrac12$ | beamsplitter transmittance, which is the probability of the $\mathsf Z$ arm |
| `half_wave_angle` | device | $\tfrac18$ | half-wave plate angle in units of $\pi$; $\tfrac18$ is $22.5^\circ$ |
| `pbs_leak_transmitted` | device | $0$ | fraction of the vertical polarization each PBS transmits instead of reflecting; this light clicks the transmitted-path detector (`H`, or `D` behind the plate), because each detector watches both polarizations of its path. $0$ is perfect, $\tfrac12$ is no separation |
| `pbs_leak_reflected` | device | $0$ | fraction of the horizontal polarization each PBS reflects instead of transmitting; this light clicks the reflected-path detector (`V`, or `A` behind the plate), because each detector watches both polarizations of its path. $0$ is perfect, $\tfrac12$ is no separation |
| `efficiency` | device | $1$ per detector | detection efficiency $\eta_k$ of detectors `H`, `V`, `D`, `A` |
| `dark_count` | device | $0$ per detector | dark-click probability per round, per detector |
| `photon_cutoff` | device | $1$ | $N$: photon numbers up to $N$ are modelled exactly; higher ones are bounded |
| `exact_window` | device | $N+1$ | $m^{\ast}$: photon numbers $N+1$ to $m^{\ast}$ are evaluated exactly when bounding the high-photon part; must exceed $N$ |
| `efficiency_normalization` | device | empty (the largest efficiency divided by $\tfrac{99}{100}$, or $1$ where it is at least $\tfrac{99}{100}$) | factored loss $t$: the efficiencies are divided by $t$ and the common loss $t$ is moved into the channel, which leaves the observed statistics unchanged; between the largest efficiency and $1$, where $1$ turns it off. The default stops short of the largest efficiency because at that full normalization, with dark counts at a photon cutoff of two or more, the engine can report no key where the model gives one (`receiver/detector-imperfections/rem:normalization-scope`); declaring the largest efficiency itself is allowed and sound |
| `route` | device | `encoded` | the photon-number reduction; see below |
| `acceptance_map` | device | `announcement-resolved` | how finely the public statistics are recorded; see below |

All values are exact rationals. The default run uses $n=10\,000$ rounds,
completeness budget $10^{-6}$, $\alpha=1.05$,
$\varepsilon_{\mathrm{PA}}=\varepsilon_{\mathrm{EV}}=2^{-30}$ and
$\lambda_{\mathrm{EC}}=0$.

**The exact window matters.** If `exact_window` is left empty, only the uniform
analytic high-photon bound applies. At $N=1$ that bound gives a minimum
multi-click probability $p_{\mathrm{mc}}=0$ for the high-photon part, and the
run returns no key. The default configuration therefore sets $m^{\ast}=N+1$, the
smallest window allowed.

## Reduction route

The adversary can send Bob any number of photons. The reduction maps that
unbounded input to a finite system: photon numbers up to $N$ stay as they are,
and higher ones are represented by flag states.

| `route` | What it declares |
| --- | --- |
| `encoded` | the weight-preserving flag-state reduction: the high-photon multi-click bound is built into the target, so no constraint is needed |
| `licensed` | the plain flag-state reduction plus a licensed constraint: the multi-click probability is at least $p_{\mathrm{mc}}$ times the above-cutoff (flag) weight |
| `licensed+two-sector` | as `licensed`, plus a stronger entry that also credits the smallest multi-click probability $a$ of states within the cutoff: multi-click $\ge a\,\cdot$ (within-cutoff weight) $+\,p_{\mathrm{mc}}\cdot$ (flag weight) |

The optics, channel and source are identical on all three routes, so a
difference between two routes' results comes from the reduction alone. The
extra `licensed+two-sector` entry only differs from `licensed` when a state within
the cutoff can itself produce a multi-click, for example with dark counts; for
an ideal device it adds nothing. A licensed route's key rate also rests on the
licence of its constraint, which the run record lists among its assumptions.

## Acceptance map

The acceptance map groups the public announcements into the values whose
frequencies the protocol checks. It is a declared protocol choice; the physics
is the same under all three.

| `acceptance_map` | Values | What is resolved |
| --- | --- | --- |
| `merged-discard` | `gen`, `ok`, `err`, `disc` | no click, multi-click and basis mismatch share `disc` |
| `announcement-resolved` | `gen`, `ok`, `err`, `mis`, `nc`, `mc` | basis mismatch (`mis`), no click and multi-click each separate |
| `pair-resolved` | 15 values `a\|b`, one per announcement pair | every pair of announcements; the key rounds are `Z\|Z` |

The multi-click rate is what bounds the adversary's use of many-photon
signals. `merged-discard` does not report it separately: it is summed into
`disc` together with the no-click rounds, which grow with loss. No map records
Alice's $\mathsf Z$ bit, because that bit is the key and is never announced.
The joint table of Alice's letters and Bob's outcomes, shown with the
preparation, describes the honest model; the protocol only checks the
acceptance values.

Under `merged-discard` this instance has the same source, acceptance values and
announcements for retained rounds as [ideal qubit BB84](../bb84/README.md).

## The honest model

With probability $\eta$ (`transmittance`) Bob receives Alice's single photon
after a depolarizing channel; otherwise he receives vacuum. In the
source-replacement picture, where Alice prepares by measuring half of a pair
$\lvert\Phi^+\rangle$ and sends the other half, the state shared by Alice's
retained qubit and the qubit that arrives is the Werner state of ideal BB84,

$$\omega(Q)=v\,\lvert\Phi^+\rangle\langle\Phi^+\rvert+(1-v)\,\frac{\mathbb 1}{4},
\qquad v=1-2Q.$$

Detector efficiencies and dark counts are part of Bob's measurement, not of the
channel. The statistics are exact rationals per round over every outcome,
including `nc` and `mc`.

Bob's measurement is evaluated from the optics in floating point and then
declared as an exactly valid measurement within the run's declared tolerance
($10^{-12}$ by default). The run records how far each entry moved. The result
is a statement about the declared measurement; a small displacement does not by
itself bound the change in key rate.

**Example.** With `transmittance` $=\tfrac1{10}$ and `qber` $=\tfrac1{20}$,
ideal detectors otherwise:

- `(Z,0)|nc` $=\tfrac{9}{40}$: Alice sends $H$ with probability $\tfrac14$,
  and the photon is lost with probability $\tfrac{9}{10}$.
- `(Z,0)|V` $=\tfrac1{1600}$: $\tfrac14\cdot\tfrac1{10}$ for the photon to
  arrive, $\tfrac12$ for the $\mathsf Z$ arm, and $Q=\tfrac1{20}$ for the wrong
  detector. This is a key-round error, counted in the key rounds.

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
- The run record lists every assumption, among them that the receiver is
  exactly the declared optics, that it has no undeclared optical paths, and
  that its detectors are threshold detectors without memory.

## Written as a protocol document

This instance is the protocol document [protocol.yaml](protocol.yaml): its
parameters, presets, source, receiver optics and public rules are data there,
and [surface.py](surface.py) only loads it. To start a protocol of your own,
copy it and customise it as its header says; the format is described in [the
protocol-document guide](../declared/README.md), and the MCP server serves this
document as a template.
