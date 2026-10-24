# Ideal qubit BB84

Prepare-and-measure BB84 on an ideal qubit. Alice prepares one of the four BB84
states, the qubit crosses a channel the adversary controls, and Bob measures it
in a basis of his choice. Bob's measurement is an exact projective qubit
measurement: there is no loss, no detector and no photon number. This makes the
instance the reference point for the optical BB84 instances.

## Setup

| Part | What it is | Trust |
| --- | --- | --- |
| Alice (source) | prepares $\lvert a^b\rangle$: basis $b\in\{\mathsf Z,\mathsf X\}$ with probability $p^A_b$, bit $a\in\{0,1\}$ uniform | trusted: her states are exactly as declared |
| Channel | carries the qubit from Alice to Bob | untrusted: any attack |
| Bob (receiver) | measures in basis $b'$ with probability $p^B_{b'}$, outcome $y\in\{0,1\}$ | trusted: an exact, noiseless projective measurement |

The bases are $\lvert 0^{\mathsf Z}\rangle=\lvert0\rangle$,
$\lvert 1^{\mathsf Z}\rangle=\lvert1\rangle$ and
$\lvert 0^{\mathsf X}\rangle=(\lvert0\rangle+\lvert1\rangle)/\sqrt2$,
$\lvert 1^{\mathsf X}\rangle=(\lvert0\rangle-\lvert1\rangle)/\sqrt2$.

## One round

1. Alice chooses a basis and a bit and sends the state.
2. Bob chooses a basis and measures.
3. Both announce. A party who used $\mathsf Z$ announces only `Z`; a party who
   used $\mathsf X$ announces basis and bit, `(X,0)` or `(X,1)`.
4. Sifting keeps the rounds where both announced `Z`. These are the
   generation rounds; their bits stay private.
5. The key bit is **Alice's** bit $a$. Bob's result $y$ is his copy of it; a
   $\mathsf Z$-basis disagreement is an error for error correction to fix,
   and it is not visible in the public statistics.

Rounds where both used $\mathsf X$ are test rounds: both bits are public, so
agreement and disagreement are counted. Mismatched bases are discarded.

| Announcements (Alice, Bob) | Acceptance value |
| --- | --- |
| `Z`, `Z` | `gen` (key round) |
| `(X,a)`, `(X,y)` with $a=y$ | `ok` |
| `(X,a)`, `(X,y)` with $a\ne y$ | `err` |
| any other pair (basis mismatch) | `disc` |

## Reading the labels

| Label | Meaning |
| --- | --- |
| `(Z,0)`, `(Z,1)`, `(X,0)`, `(X,1)` | Alice's letter: basis and bit, e.g. `(X,1)` is $\lvert 1^{\mathsf X}\rangle$. Bob's outcomes use the same spelling for his basis and result. |
| `(Z,0)\|(X,1)` | a joint outcome: Alice's letter, then Bob's |
| `Z`, `(X,0)`, `(X,1)` | the public announcements |
| `gen`, `ok`, `err`, `disc` | the acceptance values of the table above |

## Parameters

| Parameter | Section | Default | Range | Meaning |
| --- | --- | --- | --- | --- |
| `qber` | model | $0$ | $[0,\tfrac12)$ | error parameter $Q$ of the depolarizing channel; a model input, not an observed rate |
| `alice_z`, `alice_x` | device | $\tfrac12$, $\tfrac12$ | $(0,1)$ | Alice's basis probabilities $p^A_{\mathsf Z}$, $p^A_{\mathsf X}$ |
| `bob_z`, `bob_x` | device | $\tfrac12$, $\tfrac12$ | $(0,1)$ | Bob's basis probabilities $p^B_{\mathsf Z}$, $p^B_{\mathsf X}$ |

Each party's two weights must sum to one. Decimals such as `0.9` and `0.1` are
accepted; they are converted to exact rationals and the run records the
conversion.

**Presets** set the four basis weights and leave `qber` alone:

| Preset | $p^A_{\mathsf Z}, p^A_{\mathsf X}$ | $p^B_{\mathsf Z}, p^B_{\mathsf X}$ |
| --- | --- | --- |
| `BB84-w1` | $\tfrac12,\tfrac12$ | $\tfrac12,\tfrac12$ |
| `BB84-w2` | $\tfrac34,\tfrac14$ | $\tfrac12,\tfrac12$ |
| `BB84-w3` | $\tfrac23,\tfrac13$ | $\tfrac45,\tfrac15$ |

The default run uses $n=10\,000$ rounds, completeness budget $10^{-6}$,
$\alpha=1.5$, $\varepsilon_{\mathrm{PA}}=\varepsilon_{\mathrm{EV}}=2^{-30}$
and $\lambda_{\mathrm{EC}}=0$.

## The honest model

The simulated statistics come from a depolarizing channel. In the equivalent
entanglement picture Alice and Bob share the Werner state

$$\omega(Q)=v\,\lvert\Phi^+\rangle\langle\Phi^+\rvert+(1-v)\,\frac{\mathbb 1}{4},
\qquad v=1-2Q,$$

so a matched-basis round gives disagreeing bits with probability $Q$ in either
basis. The statistics are exact rationals per round, over every acceptance
value including discards:

| Value | Probability per round |
| --- | --- |
| `gen` | $p^A_{\mathsf Z}\,p^B_{\mathsf Z}$ |
| `ok` | $p^A_{\mathsf X}\,p^B_{\mathsf X}\,(1-Q)$ |
| `err` | $p^A_{\mathsf X}\,p^B_{\mathsf X}\,Q$ |
| `disc` | $p^A_{\mathsf Z}\,p^B_{\mathsf X}+p^A_{\mathsf X}\,p^B_{\mathsf Z}$ |

**Example.** At the defaults, the joint entry `(Z,0)|(Z,0)` is $\tfrac18$:
Alice sends $\lvert0\rangle$ with probability $\tfrac12\cdot\tfrac12$, Bob
picks $\mathsf Z$ with probability $\tfrac12$ and then reads $0$ with certainty.
With $Q>0$ the entry `(Z,0)|(Z,1)` becomes $Q/8$. That is a key-round error,
and it is counted in `gen` like any other key round.

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
- The run record lists every assumption the result rests on, including the
  trusted source and receiver.

## Written as a protocol document

This instance is the protocol document [protocol.yaml](protocol.yaml): its
parameters, presets, source, Bob's qubit measurement and public rules are data
there, and [surface.py](surface.py) only loads it. To start a protocol of your
own, copy it and customise it as its header says; the format is described in
[the protocol-document guide](../declared/README.md), and the MCP server serves
this document as a template.
