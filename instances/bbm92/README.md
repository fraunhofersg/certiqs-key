# BBM92 with two passive stations

Entanglement-based QKD. A source between Alice and Bob emits
polarization-entangled photon pairs, and each party measures one photon with a
passive optical station: a beamsplitter chooses the basis, and four threshold
detectors read $H$, $V$, $D$ or $A$. The source is untrusted, so the key rate
holds whatever the source emits.

## Setup

| Part | What it is | Trust |
| --- | --- | --- |
| Source | emits photon pairs toward Alice and Bob | untrusted: it may be the adversary's |
| Arms | carry one photon of each pair to each station, with transmittances $\eta_A$, $\eta_B$ | untrusted |
| Alice's station | beamsplitter, polarizing beamsplitters and four threshold detectors, with its own parameters | trusted: characterized exactly by the declared model |
| Bob's station | the same design, with its own parameters | trusted: characterized exactly by the declared model |
| Alice's test coin | a public coin, independent of everything else: test with probability $\gamma$ | trusted |

Each station works like the receiver of [optical BB84](../optical_bb84/README.md)
and has its own photon cutoff, exact window and photon-number reduction. The two
stations' settings and readouts are declared separately; no joint measurement
is assumed.

## One round

1. Alice flips her test coin: a test round with probability $\gamma$
   (`test_fraction`), otherwise a generation round. The coin is announced.
2. Each station gives one outcome: `H`, `V`, `D`, `A` (exactly one click),
   `nc` (no click) or `mc` (two or more clicks).
3. **Generation round.** Alice announces only her basis or failure: `gen:Z`
   for `H` or `V`, `gen:X` for `D` or `A`, `gen:nc` or `gen:mc`. Bob answers
   the same way: `Z`, `X`, `nc` or `mc`.
4. **Sifting.** The round is a key round when both announced the same basis and
   that basis is a key basis: both $\mathsf Z$ and $\mathsf X$ by default, or
   $\mathsf Z$ only with `key_bases` = `Z`.
5. **Key bit.** The key is **Alice's**: `H` or `D` gives 0, `V` or `A` gives 1.
   Bob reads his letter the same way; if it differs from Alice's, that is an
   error for error correction to fix. Key-round errors are not visible in the
   public statistics.
6. **Test round.** Both announce their full outcome, `test:<letter>` from Alice
   and the letter from Bob, so agreement and disagreement are public.

## Reading the labels

| Label | Meaning |
| --- | --- |
| `H`, `V`, `D`, `A`, `nc`, `mc` | a station's outcome |
| `(H,gen)`, `(V,test)`, `(nc,gen)`, … | Alice's outcome: her station's letter, then her coin, `gen` or `test` |
| `(H,gen)__V` | a joint outcome: Alice's outcome, `__`, Bob's letter |
| `x0\|(H,gen)__V` | the same joint outcome in the joint table; `x0` is the source's only letter, since an untrusted source gives Alice no prepared signal |
| `gen:Z`, `gen:X`, `gen:nc`, `gen:mc`, `test:H`, … | Alice's announcements |
| `Z`, `X`, `nc`, `mc`, `H`, `V`, `D`, `A` | Bob's announcements |

So `(H,gen)__V` is a generation round in which Alice's `H` and Bob's `V` both
announce basis $\mathsf Z$: a key round with key bit 0 for Alice and a bit error
at Bob.

## Acceptance map

The acceptance map groups the public transcript (Alice's announcement, Bob's
announcement) into the values whose frequencies the protocol checks. A key
round is always the single value `gen`, and no map publishes a key bit.

| `acceptance_map` | Values | Count at defaults |
| --- | --- | --- |
| `pair-resolved` (default) | `gen`, and every other transcript as its own value `first\|second`, e.g. `gen:Z\|X`, `test:H\|V` | 79 |
| `announcement-resolved` | generation failures as in `pair-resolved`; test rounds grouped by the two parties' classes (`Z`, `X`, `nc`, `mc`): `test-Z-ok`, `test-Z-error`, `test-X-ok`, `test-X-error` for a matched basis, and `test-<a>-<b>` otherwise, e.g. `test-Z-X`, `test-nc-mc` | 61 |
| `merged-discard` | `gen`, the four matched-basis test values above, and one `disc` for everything else | 6 |

`ok` means equal letters, hence equal bits. Because every announcement table is
complete, the alphabets also contain transcripts no round produces, such as a
basis letter in a test round or a detector letter in a generation round.
`pair-resolved` and `announcement-resolved` list them as their own values;
`merged-discard` puts them in `disc`. Their frequency is zero.

**What the choice changes.** The set of states the adversary may hold does not
depend on the map; the map changes what the observed data pin down. Grouping
values can only lower the divergence terms of the objective, by data processing,
and `gen` is unchanged under every map. So a coarser map gives a key rate no
larger than `pair-resolved`, provided its acceptance box contains the image of
the finer box. In exchange it has fewer values, so the solve is cheaper. At
finite $n$ that proviso can fail: the completeness budget is shared among the
values, so each value of a coarser map gets a larger share and a tighter
interval. The comparison can then go either way and has to be measured.

## Parameters

| Parameter | Section | Default | Meaning |
| --- | --- | --- | --- |
| `alice_transmittance`, `bob_transmittance` | model | $1$, $1$ | probability $\eta_A$, $\eta_B$ that each photon of a pair reaches its station |
| `visibility` | model | $1$ | visibility $v$ of the pair: matched-basis bits disagree with probability $(1-v)/2$. Has an effect only when `source_model` is `ideal_pair` |
| `mean_pairs` | model | $\tfrac1{32}$ | mean number of pairs $\mu$ emitted per round, summed over both polarizations. Has an effect only when `source_model` is `spdc` |
| `test_fraction` | device | $\tfrac18$ | probability $\gamma$ that Alice's public coin makes a round a test round |
| `source_model` | device | `ideal_pair` | the model that predicts the expected data: `ideal_pair` or `spdc`; the security analysis never trusts the source |
| `key_bases` | device | `ZX` | which matched bases of a generation round give key: `ZX` (both) or `Z`, which discards matched-$\mathsf X$ generation rounds. Independent of the test coin |
| `route` | device | `encoded` | photon-number reduction, applied to each station: `encoded`, `licensed` or `licensed+two-sector`, as in optical BB84 |
| `party_local_view` | device | `operator` | how each station's constraints enter on a licensed route: see below. Has an effect only when `route` is `licensed` or `licensed+two-sector` |
| `acceptance_map` | device | `pair-resolved` | how finely the public announcements are grouped: see above |
| `alice_…`, `bob_…` | device | per station | `basis_split` ($\tfrac12$), `half_wave_angle` ($\tfrac18$, in units of $\pi$), `pbs_leak_transmitted` ($0$), `pbs_leak_reflected` ($0$), `efficiency` ($1$ per detector), `dark_count` ($0$ per detector), `photon_cutoff` ($1$), `exact_window` (cutoff $+1$), `efficiency_normalization` (empty: the station's largest efficiency divided by $\tfrac{99}{100}$, or $1$ where it is at least $\tfrac{99}{100}$; see optical BB84) |

The station parameters mean what they mean in optical BB84, one set per
station: the basis beamsplitter's transmittance (the $\mathsf Z$-basis
probability), the X-arm half-wave plate angle, the polarizing beamsplitters'
two leaks (the share of vertical light transmitted and of horizontal light
reflected, which clicks the other detector of the pair because each detector
watches both polarizations of its path), each detector's efficiency and dark-click probability, the photon
cutoff $N$ and the exact-window depth $m^{\ast}>N$. With `exact_window` left
empty, a station falls back on the analytic high-photon bound.

**The test coin is put on a $2^{-12}$ grid** when needed, and the run records
the coin actually used. An input such as $\tfrac15$ need not stay exactly
$\tfrac15$; the record gives the value the protocol ran with.

**`party_local_view`** matters only on the licensed routes. `operator` imposes
each station's constraints as operator inequalities on that station's own
system. `licensed_scalar` imposes only their licensed scalar consequences, a
weaker set of constraints. The `encoded` route has no constraints and does not
accept `licensed_scalar`. A licensed route's key rate also rests on the licence
of its constraints, which the run record lists among its assumptions.

**Presets** set `source_model` only: `ideal_pair` (one ideal entangled pair per
round) and `spdc` (low-brightness polarization-entangled SPDC).

The default run uses $n=10^8$ rounds, completeness budget $10^{-6}$,
$\alpha=1.05$, $\varepsilon_{\mathrm{PA}}=\varepsilon_{\mathrm{EV}}=2^{-30}$,
$\lambda_{\mathrm{EC}}=0$ and the `bernstein` rule for the acceptance
intervals, which keeps the completeness guarantee of exact binomial endpoints
with a possibly wider acceptance set.

## The honest models

- `ideal_pair`: one pair per round in the state
  $v\,\lvert\Phi^+\rangle\langle\Phi^+\rvert+(1-v)\,\mathbb 1/4$, then
  independent loss on each arm. Matched-basis bits disagree with probability
  $(1-v)/2$.
- `spdc`: two squeezed polarization pairs in one spectral mode, all pair
  numbers included, with the stations' efficiencies and dark counts; the click
  statistics are exact rationals.

[The pair models' derivation](../common/honest/pair_models.md) derives both. The statistics are per round over every
outcome, including no-click and multi-click rounds. They describe the expected
data only; the security analysis assumes nothing about the source.

**Example.** With `visibility` $=\tfrac{9}{10}$ and otherwise default
parameters, the joint entry `(H,gen)__V` is $\tfrac{7}{1280}$: the coin shows
generation ($\tfrac78$), Alice's photon goes to her $\mathsf Z$ arm and reads
`H` ($\tfrac14$), Bob's goes to his $\mathsf Z$ arm ($\tfrac12$), and reads the
wrong letter with probability $(1-v)/2=\tfrac1{20}$. The same event in a test
round, `(H,test)__V` $=\tfrac1{1280}$, is public and counted as a test error.

## The key-rate result

A run builds an acceptance set from the honest statistics, the round count $n$
and the completeness budget: with independent honest rounds, the honest
implementation aborts with probability at most that budget. It then bounds the
key the protocol can extract against any source and arm attack, given the
trusted stations above.

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
- The run record lists every assumption the result rests on, station by
  station.

## Written as a protocol document

This instance is the protocol document [protocol.yaml](protocol.yaml): its
parameters, presets, source, two stations and transcript are data there, and
[surface.py](surface.py) only loads it. To start a protocol of your own, copy
it and customise it as its header says; the format is described in [the
protocol-document guide](../declared/README.md), and the MCP server serves this
document as a template.
