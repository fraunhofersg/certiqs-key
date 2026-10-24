# Protocol instances

An instance is one QKD protocol with its devices and an honest model of the data
it should produce. You pick an instance, set its parameters, inspect the
prepared protocol and run a key rate. Each instance has its own page.

| Instance | Protocol | Source | Receiver |
| --- | --- | --- | --- |
| [bb84](bb84/README.md) | ideal qubit BB84 | trusted qubit states | exact qubit measurement; no loss |
| [optical_bb84](optical_bb84/README.md) | BB84 with a passive optical receiver | trusted single-photon polarization states | beamsplitter basis choice, four threshold detectors |
| [decoy_bb84](decoy_bb84/README.md) | decoy-state BB84 | trusted weak coherent pulses at three intensities | the same passive receiver |
| [bbm92](bbm92/README.md) | entanglement-based BBM92 | untrusted pair source, ideal pair or SPDC | two passive stations, one per party |

All four are written as protocol documents: each is the
`protocol.yaml` in its folder, which you can read, copy and edit into a
protocol of your own (the format is described in
[declared/README.md](declared/README.md); the MCP server serves the four as
templates).

## Common vocabulary

**Outcome labels.** A party's outcome is a short label. A threshold-detector
station reports `H`, `V`, `D` or `A` when exactly that detector clicks, `nc`
for no click and `mc` for two or more clicks. A qubit party reports basis and
bit, such as `(Z,0)`. An entry of the joint table is written Alice's letter,
`|`, Bob's outcome, as in `(Z,0)|V`. In BBM92 both parties measure at a
station: the two station outcomes are joined with `__`, as in `(H,gen)__V`, and
the source contributes the single placeholder letter `x0`, as in
`x0|(H,gen)__V`.

**Announcements and acceptance values.** After each round the parties announce
part of what they saw. The acceptance map groups those announcements into
acceptance values, such as `gen`, `ok`, `err` and `disc`. The protocol checks
the observed frequency of every value. Key rounds are always the value `gen`
(`Z|Z` under optical BB84's `pair-resolved` map), and no value reveals a key
bit.

**Who holds the key.** In every instance the key bit is Alice's. Bob's
result is his copy, and his errors are corrected by error correction, whose
leakage $\lambda_{\mathrm{EC}}$ you declare.

**Photon-number cutoffs and routes.** An optical receiver can be sent any
number of photons. Its photon cutoff $N$ keeps photon numbers up to $N$ exact,
and the route (`encoded`, `licensed`, `licensed+two-sector`) chooses how higher
photon numbers are handled. The optical BB84 page explains the choice.

**Exact numbers.** Parameters are exact rationals. You may type decimals or
fractions such as `1/3`. Where an input must be moved onto a grid to be
represented exactly, the run records the original value, the value used and the
difference.

## Reading a result

A preparation shows the protocol before any optimization: the labels, the
announcements, the acceptance values and the honest statistics. A run adds the
key rate:

| Field | Meaning |
| --- | --- |
| key length $\ell$ | final key bits for $n$ rounds. This is the headline. |
| tier | `estimate` (backs no key length), `first-order` (a bound proved in exact arithmetic, evaluated in floating point) or `certified` (every arithmetic step exact or rigorously enclosed) |
| `h_lb` | a lower bound on the entropy per round, valid when the solver's linear subproblems are solved exactly |
| `h_low` | the objective at the solver's last point: an upper estimate, shown as a diagnostic, never a bound |
| Frank-Wolfe gap | the solver's convergence measure at its last point: `h_low` minus the gap is the lower bound from that point, and `h_lb` is the best such bound over the run. A large gap means the solver has not converged: `h_lb` is still valid but may lie well below the true minimum, which costs key |

$$\ell=\max\Big\{0,\Big\lfloor n\max\{0,h_{\mathrm{lb}}\}-\lambda_{\mathrm{EC}}
-\big\lceil\log_2\tfrac{1}{\varepsilon_{\mathrm{EV}}}\big\rceil
-\tfrac{\alpha}{\alpha-1}\log_2\tfrac{1}{\varepsilon_{\mathrm{PA}}}+1\Big\rfloor\Big\}$$

A run can also end in a refusal. The record then names the stage that refused
and the reason. Every record lists the assumptions its result rests on.

Driving the instances from Python, or adding a protocol of your own, is
described in [NOTES.md](NOTES.md).
