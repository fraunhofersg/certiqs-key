# Key-rate sweep report

## <a id="contents"></a>Contents

- [Summary](#summary)
- [Your QKD setup](#setup)
- [Your inputs](#inputs)
- [Assumptions you vouch for](#assumptions)
- [Per-point differences](#points)
- [Appendix](#appendix): [Checks the engine ran](#checks) · [Not engaged on this route](#not-engaged) · [Provenance](#provenance) · [Glossary](#glossary)

## <a id="summary"></a>Summary

### <a id="points-summary"></a>The points

| Point | Authentication error ε_auth | QBER | Key length | Bits per round | ε | Outcome | Report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.0 | 0.02 | 1,170 | 0.117 | 1.86e-09 | key-length | [report](points/0000.md) |
| 1 | 0.0 | 0.04 | 935 | 0.0935 | 1.86e-09 | key-length | [report](points/0001.md) |
| 2 | 0.5 | 0.06 | — | — | — | refused | [report](points/0002.md) |

Bits per round is a point's key length divided by all its n rounds, the rounds that give no raw key bit included.

### <a id="guarantee"></a>What the guarantee means

A run either aborts or outputs a key of ℓ bits that is a perfect key up to the security parameter ε: identical for both parties, uniform and independent of all the attacker holds, public messages included. One party may abort while the other gets a key. No test, whatever the attacker knows, tells the run's output from an ideal protocol's with advantage above ε = ε_PA + ε_EV + 2ε_auth. It holds against every attack, of any memory, if every premise in the run record holds, [A-AUTH](#A-AUTH), [A-CONFORM](#A-CONFORM) and [A-FIXED](#A-FIXED) included. A first-order run also needs its bound to hold, computed h_lb ≤ h_low, which no premise covers ([Remark "Exact real arithmetic in the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/rem:fo-arithmetic)). ε averages over aborted runs too. The criterion is composable. Separate executions provably add ε ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)). Not every later use of the key is covered ([Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions)). A run where both get a key nets ℓ − k_auth bits; an abort uses up to k_auth. Abort rates: [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope). Statement: [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).

The composable statement takes its authenticated classical channel from [A-AUTH](#A-AUTH), whose own text says that no composable proof for this timing-aware channel is published yet; Wegman-Carter authentication with separate keys per direction approximates it.

It holds for each point that output a key, separately, with that point's own ε ([the points](#points-summary)).

Completeness. The completeness figure ε\* bounds one thing only: the chance that an honest run, with no attacker and devices behaving as the declared honest model says, fails the acceptance test on its statistics. An honest run can also abort later: in error verification, when error correction leaves the two raw keys different, and in authentication. No result bounds those aborts, so an honest run's overall abort chance can exceed ε\*. Whether your error-correction code reconstructs the key on honest runs is yours to check; it affects only how often you obtain a key. Completeness never affects the security parameter ε, which holds for every abort pattern ([Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security)) and so says nothing about how often runs abort. Statement: [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope).

One execution. The security parameter ε covers one execution: one run of n rounds and its post-processing. It is not a per-round or per-bit figure, and it does not shrink when you repeat the protocol. Several executions are together secure with the sum of their ε ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)) under [A-SEPARATE](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:separate-executions). The sum does not cover parameters chosen from an earlier run's data, such as the error-correction budget or the acceptance test. The conditions of [A-SEPARATE](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:separate-executions) include: (i) their number and parameters are all fixed before the first starts; (ii) they share no key material and no device state; (iii) their keys stay unused until the last has ended. Reusing key from an earlier run to authenticate the next is not covered either. Such a key enters only through the next run's declared authentication error ε_auth, counted twice, and the earlier run's ε does not by itself bound how far that key is from an ideal one. Statement: [Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions).

[Review status](#status-legend): the lowest status of the claims below, with everything they rest on in the claim graph, is: reviewed adversarially by an AI model and accepted by the project's human owner.

- [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security), the security statement: statement and code reviewed adversarially by an AI model and accepted by the project's human owner.
- [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength), the security statement: statement and code reviewed adversarially by an AI model and accepted by the project's human owner.

The premises [A-ALPHABET](#A-ALPHABET), [A-COIN](#A-COIN), [A-HON-ENV](#A-HON-ENV), [A-IDEAL](#A-IDEAL) and [A-REACH](#A-REACH) are not beneath the claims above in the claim graph: they enter through this sweep's own route, and each carries its own review status under Assumptions you vouch for.

### <a id="not-counted"></a>Not counted

> **Not counted**
>
> - `parameters.lambda_ec = 0`: No error-correction leakage counted (λ_EC = 0). A run that sends an error-correction transcript must declare its length; with λ_EC = 0 the key length is too long for it. ([A-KEYREG](#A-KEYREG), [A-CONFORM](#A-CONFORM)) \[all completed points\]
> - `parameters.eps_auth = 0.0`: No authentication error counted (ε_auth = 0). This holds only where the classical channel is itself authenticated, with no keyed scheme and no pre-shared key; a keyed scheme's error, a reused key's distance δ included, must be declared. ([A-AUTH](#A-AUTH)) \[all completed points\]
> - `parameters.k_auth = 0`: No authentication key consumption counted (k_auth = 0); the net key equals the key length. ([A-AUTH](#A-AUTH)) \[all completed points\]

- The completeness parameter ε\* of the statistics module bounds an honest run's failure of the acceptance test only. Aborts in error verification and in authentication are bounded by no claim, so ε\* does not bound the honest abort probability of the whole protocol. ([Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope))
- A tiny change of the declared measurement can move the key rate by many bits per round, so the model is a premise of the rate. Where a handed reference's companion counts and the key length is formed on it, the snap only steers the search; nothing bounds model to device. ([Remark "The declared measurement as a premise of the rate"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:declared-measurement))
- One execution's parameter covers one run, and separate executions that share no key add their parameters ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)). A reused authentication key enters through ε_auth, charged twice, and the earlier run's parameter does not bound its distance in general. ([Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions))

### <a id="vouch"></a>What you vouch for

The points rest on 17 premises about your devices, the setup and supplied artefacts, and 0 about the engine's numerics, listed once under [Assumptions you vouch for](#assumptions); a premise that only some points rest on names them.

> **Declared in the protocol document, not derived by the engine**
>
> - `receiver_povm` `bob`: The measurement of station 'bob', declared as a POVM. Declared in the run's protocol document (your own or a shipped template), not derived by the engine; you vouch for it. The premise is that these matrices describe the receiver you have, performed in every round on that round's system alone, whatever happens in the other rounds (A-SPEC). The Band-A route the engine takes for a declared POVM rests on A-IDEAL: an ideal qubit measurement, on a transmitted system that is exactly a qubit, with unit efficiency, no loss, no dark counts, no multi-photon events and no misalignment. If your receiver is not such a measurement, A-IDEAL fails and the key length does not apply to it; declare it as an optical station (kind: optical) instead (instances/declared/README.md). ([A-SPEC](#A-SPEC), [A-IDEAL](#A-IDEAL)) \[all completed points\]

## <a id="setup"></a>Your QKD setup

This is the setup of point 0 ([its report](points/0000.md)). Across the points these inputs vary: parameters.eps_auth, model.qber; each point's values are in the points table, and everything below that does not depend on them holds for every point.

### <a id="setup-round"></a>What a round is

A round is one use of the protocol as declared, recording its own outcomes. How a time-tagged system cuts its detection record into rounds (time bins, coincidence windows, how the stations synchronise) is yours to choose, and your declaration must describe it. Every one of the n rounds counts: where your measurement has a no-click outcome, a time bin in which nothing clicks is a round with that outcome, not one to drop.

How you cut the record into rounds bears on these premises, each in full under [Assumptions you vouch for](#assumptions):

- [A-SPEC](#A-SPEC): each round's recorded outcome is what the declared measurement gives, so a detection lost from its round or filed in another, or a no-click bin dropped, is a security matter.
- [A-IDEAL](#A-IDEAL): exactly one qubit reaches the receiver in each round.
- [A-RHOM](#A-RHOM): one declaration covers every round.
- [A-SEQ](#A-SEQ): the declared order of measurements and messages within a round, and each measuring party completing one round's measurement before the next round's.
- [A-LAB](#A-LAB): no timing or synchronisation signal reveals a party's records, and only the declared inputs influence a measurement.
- [A-FIXED](#A-FIXED): the number of rounds and the acceptance test are fixed before the run.
- [A-ALPHABET](#A-ALPHABET): all n rounds are in the record (the acceptance test is evaluated on all n rounds); a measured round missing from it, a lost time tag or no-click bin included, leaves the counts wrong and is a security matter under [A-SPEC](#A-SPEC) and [A-CONFORM](#A-CONFORM).

### <a id="setup-protocol"></a>Protocol

1. Rounds: The protocol runs n = 10,000 rounds. See [What a round is](#setup-round) above. Record: [record](points/0000.record.md#p-.payload.config.rounds).
2. Source: In every round the trusted source emits one signal of 4 ((Z,0), (Z,1), (X,0), (X,1)); see Source below. Record: [record](points/0000.record.md#p-.payload.compiled.source).
3. Measurement: Each round is measured at Bob's station (declared-finite-povm); see the stations below. Record: [record](points/0000.record.md#p-.payload.stages.receiver_construction).
4. Public choices: Alice draws a public choice: Z with probability 0.5, X with probability 0.5. At Bob's station, a public choice is drawn: Z with probability 0.5, X with probability 0.5. Record: [record](points/0000.record.md#p-.payload.compiled.source.public_choices).
5. Announcements: Alice announces one of Z, (X,0), (X,1); Bob announces one of Z, (X,0), (X,1). Each announcement is computed from the announcing party's own readout (the record's announcement tables), and [A-SEQ](#A-SEQ) states the order within a round: every party's measurement, then the round's public messages. So the analysis assumes that no announcement, a basis included, comes before a measurement of its round; you vouch for this under [A-SEQ](#A-SEQ). Record: [record](points/0000.record.md#p-.payload.compiled.public.announce_alice).
6. Sifting and key map: A round gives a raw key bit when its announcements pass sifting: 4 of the 16 combinations of signal and readouts map to a key bit, the rest are discarded. Alice holds the key over the alphabet 0, 1. Record: [record](points/0000.record.md#p-.payload.compiled.public.key_map).
7. Acceptance test: The parties estimate the acceptance statistics on the whole run and abort unless they pass; see Acceptance test below. Record: [record](points/0000.record.md#p-.payload.stages.acceptance_construction).
8. Error correction: One-way error correction; its transcript leaks λ_EC = 0 bits, which the key length deducts. Record: [record](points/0000.record.md#p-.payload.config.parameters.lambda_ec).
9. Error verification: The parties compare a hash of the corrected keys (failure probability ε_EV = 9.31323e-10); the key length deducts 30 bits for it. Record: [record](points/0000.record.md#p-.payload.stages.key_rate.deductions.error_verification).
10. Privacy amplification: A two-universal hash shortens the corrected key to ℓ = 1,170 bits, secret except with probability ε_PA = 9.31323e-10. Record: [record](points/0000.record.md#p-.payload.stages.key_rate.key_length).

### <a id="setup-source"></a>Source

The source is trusted: the analysis uses the declared ensemble of signals below, prepared with the weights shown.

| Field | Value |
| --- | --- |
| Source mode | trusted |
| Trusted | true |
| Honest model | depolarizing qubit channel, evaluated exactly on the emitted declaration |
| Honest model: qber | 0.02 |
| How the honest model is derived | — |
| Status | — |
| Signals | (Z,0) (weight 0.25), (Z,1) (weight 0.25), (X,0) (weight 0.25), (X,1) (weight 0.25) |
| Record | [record](points/0000.record.md#p-.payload.compiled.source) |

#### Alice's measurement in the source-replacement picture

The trusted source as the proof sees it: Alice holds one half of an entangled state and measures it; each outcome selects the signal sent. The record names no basis for Alice's system, so basis states are numbered.

Alice's system. Basis: 1. basis state 1; 2. basis state 2. Record: [record](points/0000.record.md#p-.payload.compiled.source.alice_povm).

*(Z,0)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 1/2 | 0 |
| **basis state 2** | 0 | 0 |

*(Z,1)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 0 | 0 |
| **basis state 2** | 0 | 1/2 |

*(X,0)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 1/4 | 1/4 |
| **basis state 2** | 1/4 | 1/4 |

*(X,1)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 1/4 | -1/4 |
| **basis state 2** | -1/4 | 1/4 |

Alice's reduced state. Basis: 1. basis state 1; 2. basis state 2. Record: [record](points/0000.record.md#p-.payload.compiled.source.alice_marginal).

*reduced state*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 1/2 | 0 |
| **basis state 2** | 0 | 1/2 |

#### Signal states as declared in the protocol document

The state the source prepares for each signal.

Transmitted system. Basis: 1. basis state 1; 2. basis state 2. Record: [record](points/0000.record.md#p-.payload.protocol_document.canonical.source.states).

*(Z,0)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 1 | 0 |
| **basis state 2** | 0 | 0 |

*(Z,1)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 0 | 0 |
| **basis state 2** | 0 | 1 |

*(X,0)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 1/2 | 1/2 |
| **basis state 2** | 1/2 | 1/2 |

*(X,1)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 1/2 | -1/2 |
| **basis state 2** | -1/2 | 1/2 |

### <a id="station-bob"></a>Bob's station

| Field | Value |
| --- | --- |
| Party | B |
| Station | bob |
| Input route | declared finite POVM: the measurement operators are declared directly, with no optical model |
| Record | [record](points/0000.record.md#p-.payload.stages.receiver_construction) |

#### Outcome alphabet

| Letter | Meaning | Click patterns |
| --- | --- | --- |
| `(Z,0)` | an outcome of the declared measurement | — |
| `(Z,1)` | an outcome of the declared measurement | — |
| `(X,0)` | an outcome of the declared measurement | — |
| `(X,1)` | an outcome of the declared measurement | — |

#### Declared POVM

The measurement operators as declared, one per outcome, per sector; the record names no basis for these systems, so basis states are numbered in the record's order. Statement: [Theorem "The Band-A route"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:band-a).

Sector s0. Basis: 1. basis state 1; 2. basis state 2. Record: [record](points/0000.record.md#p-.payload.stages.receiver_construction.declared_povm).

*Outcome (Z,0)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 0.5 | 0 |
| **basis state 2** | 0 | 0 |

*Outcome (Z,1)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 0 | 0 |
| **basis state 2** | 0 | 0.5 |

*Outcome (X,0)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 0.25 | 0.25 |
| **basis state 2** | 0.25 | 0.25 |

*Outcome (X,1)*

|   | basis state 1 | basis state 2 |
| --- | --- | --- |
| **basis state 1** | 0.25 | -0.25 |
| **basis state 2** | -0.25 | 0.25 |

### <a id="setup-acceptance"></a>Acceptance test

The run records one acceptance value per round, from 4 outcomes, and accepts only if the observed frequency of every outcome lies in the box of intervals built around the honest model's probabilities (endpoint rule exact). An honest run fails it with probability at most 8.77e-07 (ε\*, rounded up; its exact value is in the table below), within your completeness budget of 1e-06 (the completeness parameter ε_comp you allow). The table of acceptance categories below gives, for each outcome, the honest model's probability and the interval its observed frequency must lie in, ends included, and the counts that interval admits out of the rounds of the run: a run whose count of any outcome falls outside its range is not accepted ([Definition "The construction map"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/def:construction)). Statement: [Theorem "The completeness bound"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/thm:completeness-bound).

| Field | Value |
| --- | --- |
| Acceptance categories | 4 |
| Outcomes the honest model gives positive probability | 4 |
| Endpoint rule | exact |
| Geometry | PolytopeGeometry |
| Completeness budget | 1e-06 |
| Certified completeness ε\* | at most 8.77e-07 (rounded up; the exact fraction is below) |
| Record | [record](points/0000.record.md#p-.payload.stages.acceptance_construction) |

ε\* = 92333685184654264603261871452993461609589558379487522430129/105312291668557186697918027683670432318895095400549111254310977536

| Acceptance category | Honest probability | Allowed frequency | Allowed count |
| --- | --- | --- | --- |
| gen | 0.25 | 0.2279 to 0.2725 | 2,279 to 2,725 of 10,000 |
| ok | 0.245 | 0.223 to 0.2674 | 2,230 to 2,674 of 10,000 |
| err | 0.005 | 0.0018 to 0.009 | 18 to 90 of 10,000 |
| disc | 0.5 | 0.4742 to 0.5258 | 4,742 to 5,258 of 10,000 |

### <a id="setup-expected"></a>Expected statistics of the honest model

These statistics are expected from the honest model "depolarizing qubit channel, evaluated exactly on the emitted declaration", evaluated with QBER 0.02, as your declared stations record them (see the stations above).

| Statistic | Value | How it is computed | Record |
| --- | --- | --- | --- |
| Probability that a round gives a raw key bit | 0.25 | The sum of the honest raw joint distribution over every combination of signal and readouts the compiled key map sends to a key bit. | [record](points/0000.record.md#p-.payload.stages.acceptance_construction.raw_joint_distribution) |
| Expected QBER, key rounds Alice announces Z | 0.02 | Among these key rounds of the honest raw joint distribution, the probability that Alice's key bit differs from the bit the other party most likely holds given their own readout. | [record](points/0000.record.md#p-.payload.stages.acceptance_construction.raw_joint_distribution) |

## <a id="inputs"></a>Your inputs

The inputs equal at every point; those that vary are in the points table.

### <a id="inputs-device"></a>Device and channel

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-device.alice_x"></a>[`device.alice_x`](points/0000.record.md#p-.payload.config.device.alice_x) | 0.5 | — | Probability that Alice prepares in the X basis; Alice's two basis weights sum to one | — |
| <a id="input-device.alice_z"></a>[`device.alice_z`](points/0000.record.md#p-.payload.config.device.alice_z) | 0.5 | — | Probability that Alice prepares in the Z basis; Alice's two basis weights sum to one | — |
| <a id="input-device.bob_x"></a>[`device.bob_x`](points/0000.record.md#p-.payload.config.device.bob_x) | 0.5 | — | Probability that Bob measures in the X basis; Bob's two basis weights sum to one | — |
| <a id="input-device.bob_z"></a>[`device.bob_z`](points/0000.record.md#p-.payload.config.device.bob_z) | 0.5 | — | Probability that Bob measures in the Z basis; Bob's two basis weights sum to one | — |

### <a id="inputs-budget"></a>Budgets (the ε you choose)

A budget is an error probability (an ε) you choose before the run. ε_PA, ε_EV and ε_auth make up the security parameter ε = ε_PA + ε_EV + 2ε_auth. The completeness budget ε_comp is not part of ε: it bounds only how often an honest run fails the acceptance test. The table also holds the round count and the other inputs of the key length.

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-rounds"></a>Rounds n ([`rounds`](points/0000.record.md#p-.payload.config.rounds)) | 10000 | — | the number of rounds (n), total channel uses; the same n reaches the acceptance construction and the declaration ([Requirement "Alphabet and round count taken from the consuming declaration"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/req:matched-alphabet)) | [A-ALPHABET](#A-ALPHABET), [A-FIXED](#A-FIXED), [A-HON-ENV](#A-HON-ENV), [A-RHOM](#A-RHOM), [A-SEQ](#A-SEQ) |
| <a id="input-completeness_budget"></a>Completeness budget ([`completeness_budget`](points/0000.record.md#p-.payload.config.completeness_budget)) | 1e-06 | — | the completeness budget (eps_comp) of the acceptance construction; it buys completeness and never soundness | — |
| <a id="input-parameters.alpha"></a>Rényi order α (declared) ([`parameters.alpha`](points/0000.record.md#p-.payload.config.parameters.alpha)) | 1.5 | — | the Renyi order (alpha) of the declaration; every key-length statement requires alpha in (1, 2) ([Requirement "Rényi order of a reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:key-length-alpha-domain)) | — |
| <a id="input-parameters.eps_pa"></a>Secrecy error ε_PA ([`parameters.eps_pa`](points/0000.record.md#p-.payload.config.parameters.eps_pa)) | 9.31e-10 (2^-30) | — | the privacy-amplification (secrecy) budget of the key-length expression; eps_pa + eps_ev + 2 eps_auth &lt; 1 ([Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous)) | [A-FIXED](#A-FIXED) |
| <a id="input-parameters.eps_ev"></a>Error-verification error ε_EV ([`parameters.eps_ev`](points/0000.record.md#p-.payload.config.parameters.eps_ev)) | 9.31e-10 (2^-30) | — | the error-verification (correctness) budget; eps_pa + eps_ev + 2 eps_auth &lt; 1 ([Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous)) | [A-FIXED](#A-FIXED) |
| <a id="input-parameters.lambda_ec"></a>Error-correction leakage λ_EC ([`parameters.lambda_ec`](points/0000.record.md#p-.payload.config.parameters.lambda_ec)) | 0 | bit | the error-correction transcript length in bits, total and not per round: a fixed-length register of that many bits ([Assumption "Dedicated key register and one-way reconciliation"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:keyreg)) How λ_EC was chosen: declared by you (no estimate sits beside the record). | [A-CONFORM](#A-CONFORM), [A-FIXED](#A-FIXED), [A-KEYREG](#A-KEYREG) |
| <a id="input-parameters.k_auth"></a>Authentication key bits k_auth ([`parameters.k_auth`](points/0000.record.md#p-.payload.config.parameters.k_auth)) | 0 | bit | the pre-shared key bits the authentication scheme consumes in one run ([Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth) (ii)); the net key is the key length minus k_auth | [A-AUTH](#A-AUTH), [A-FIXED](#A-FIXED) |
| <a id="input-alpha"></a>Rényi order α (configured) ([`alpha`](points/0000.record.md#p-.payload.config.alpha)) | — | — | the Renyi order the run solves at; unset, the run solves at parameters.alpha, or lets alpha_search choose it where that is set (never both) | — |

### <a id="inputs-engine"></a>Engine settings

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-declared_tolerance"></a>Declared tolerance τ ([`declared_tolerance`](points/0000.record.md#p-.payload.config.declared_tolerance)) | 0.0 | — | the ceiling (tau) on the pre-snap defect the instance may repair ([spec/architecture.md](../../../spec/architecture.md) 2.8); required, with no default, and told to no module | — |
| <a id="input-parameters.reference_enclosure"></a>Reference enclosure ([`parameters.reference_enclosure`](points/0000.record.md#p-.payload.config.parameters.reference_enclosure)) | true | — | whether the instance hands beside its snap of its receiver measurement the blocks of the reference known through rigorous rational enclosures ([Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference) (i)); off, only the blocks known exactly are handed, and the reference companion carries the snapped block on every other moved block, which then rests on A-SNAP in the group no_usable_reference (cause enclosure_not_used) | — |
| <a id="input-parameters.strict_snaps"></a>Strict option ([`parameters.strict_snaps`](points/0000.record.md#p-.payload.config.parameters.strict_snaps)) | false | — | the strict option: whether the run refuses wherever a moved block of a measurement snap or a moved class of the emission would rest on A-SNAP, rather than disclosing it, and reports no key length that rests on it ([Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference) (iv)) | — |
| <a id="input-parameters.statistics_check"></a>Statistics check ([`parameters.statistics_check`](points/0000.record.md#p-.payload.config.parameters.statistics_check)) | on (not run: the statistics are your honest model's predictions and you declared no constraint entry) | — | the check of the acceptance set against the statistics the declared model can produce ([Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set)): once per run it bounds the mismatch from below and caps the probability that devices behaving as declared pass the acceptance test | — |
| <a id="input-parameters.min_model_pass_probability"></a>Minimum model pass probability τ ([`parameters.min_model_pass_probability`](points/0000.record.md#p-.payload.config.parameters.min_model_pass_probability)) | 0.5 | — | the smallest probability (tau) with which devices behaving as declared must be able to pass the acceptance test: a checked run whose proven cap on that probability is at most tau is refused as a whole, with no key length ([Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set) (iv)) | — |
| <a id="input-constrained"></a>Constrained solve ([`constrained`](points/0000.record.md#p-.payload.config.constrained)) | — | — | which acceptance outcomes the acceptance set constrains; unset, every outcome is constrained, and an empty list is a selector in its own right | — |
| <a id="input-endpoint_rule"></a>Endpoint rule ([`endpoint_rule`](points/0000.record.md#p-.payload.config.endpoint_rule)) | exact | — | statistics' endpoint rule for the acceptance box | — |
| <a id="input-tail_evaluation"></a>Tail evaluation ([`tail_evaluation`](points/0000.record.md#p-.payload.config.tail_evaluation)) | sweep | — | how statistics decides a tail comparison; it never changes what is decided | — |
| <a id="input-solver.max_iterations"></a>Solver step limit ([`solver.max_iterations`](points/0000.record.md#p-.payload.config.solver.max_iterations)) | 5 | — | a method-native work cap (under auto, of the Frank-Wolfe stages only); unset, the solver's own is taken | — |
| <a id="input-solver.method"></a>Solver method ([`solver.method`](points/0000.record.md#p-.payload.config.solver.method)) | fw | — | the candidate search method; unset, auto is taken | — |

## <a id="assumptions"></a>Assumptions you vouch for

### <a id="premises-devices"></a>Premises about your devices and setup

The engine does not verify these premises; a run that rests on one records it as unverified. Where a premise's own text says the engine checks a part of it (its inputs, say), that part is checked and the rest is yours; a premise whose verification differs says so under it.

#### <a id="category-laboratory"></a>Your laboratories

Premises about each party's laboratory as a whole, whatever the party does in the protocol (send, measure, or both): that nothing about its records leaks out and nothing reaches in except what the protocol declares. Evidence for them comes from side-channel testing of each laboratory: back-reflections into a source where the party sends, detector back-flash where it measures, electromagnetic and power emanations, and timing.

##### <a id="A-LAB"></a>A-LAB: Each party's laboratory is sealed

| Field | Value |
| --- | --- |
| About | Alice's laboratory and Bob's laboratory (the receiver) |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | Nothing about a party's records leaves its laboratory but its key, the public messages and, in trusted-source mode at the party of A, the emitted systems; the adversary acts on it only through what its declared measurements receive and the messages. It excludes side channels at both parties. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Each party's laboratory is sealed"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:lab) |
| Category | laboratory |
| Machine key | `laboratory_sealed` |
| Emitted by | `meat-core@partyA`, `meat-core@partyB` |

Whatever a party's role, nothing about its letters, settings, choices, detection results, keys or random numbers leaves its laboratory but the final key, the public messages and, where the party sends with a trusted source, the signals that source emits; timing and auxiliary signals reveal no more. An untrusted source counts as outside every laboratory, even one it is in. The attacker reaches a laboratory only via the systems its declared measurements receive and the public messages. Light sent in to read out a letter, a setting, a choice or a detector state (a Trojan-horse attack, at a receiver as at a modulator), emanations from any device, detector back-flash and anything but the declared input modes influencing a measurement violate this, a clock or trigger line from an untrusted source included; where it sends with a trusted source, so does light seeding or recalibrating its laser.

For this run:

- laboratory: Alice's (party A)
- source_mode: trusted
- party_partition: system A: party A (Alice); measured station: the receiver (Bob)

#### <a id="category-source"></a>Your source

Premises about a trusted source of the quantum signals, the only kind whose declared states the proof uses (with an untrusted source no premise of this group applies; what may reach a laboratory from it is part of A-LAB). Evidence for them comes from characterising the source as built: the states it prepares, their weights and photon statistics, its memory between rounds, and any side channel that could reveal a signal.

##### <a id="A-ENS"></a>A-ENS: Emission of the specified ensemble

| Field | Value |
| --- | --- |
| About | Your source |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | The physical source draws each round's letter independently with the declared weights and emits the product of the declared states, no round depending on another. It ties a source specification declared as matrices to the device it describes. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Emission of the specified ensemble"](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:ens) |
| Category | source |
| Machine key | `source_ensemble` |
| Emitted by | `transmitter` |

Your source prepares, in every round, one of the declared states with the declared probabilities. Each round's letter is drawn independently with weights p_x, and the states emitted over the n rounds form a product: no round's letter or state depends on another round, its detection results or its public messages. A source with memory or drift between rounds (for example pattern effects in a modulator) violates this. Where your source is a pair source inside your laboratory with one half measured there to herald or fix the letter, those local detectors belong to the declared ensemble: their efficiency mismatch must be carried by the declared weights and states, and their memory across rounds (for example afterpulsing or dead time) violates this like any other dependence between rounds.

For this run:

- source_ensemble: signal_alphabet = (Z,0), (Z,1), (X,0), (X,1), transmitted_dim = 2, weights = (X,0) = 0.25, (X,1) = 0.25, (Z,0) = 0.25, (Z,1) = 0.25

##### <a id="A-SRC"></a>A-SRC: Retention of the system A in trusted-source mode

| Field | Value |
| --- | --- |
| About | Your source |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | In trusted-source mode the retained system A stays in the laboratory of the party that holds it and is acted on only by that party's declared measurement, condition (SR3) of the certificate. It is what lets a declared marginal delete attacks. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Retention of the system A in trusted-source mode"](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:src) |
| Category | source |
| Machine key | `source_replacement_license` |
| Emitted by | `transmitter`, `meat-core` |

The source's retained half, system A, never leaves the laboratory of the party the declaration assigns it to, and nothing acts on it except that party's own declared measurement: no other step of the protocol and no action of the adversary. In a prepare-and-measure setup A exists only in the source-replacement description, and this is the premise that the adversary has no access to that party's laboratory. Only then may you declare the source's reduced state τ_A (trusted-source mode), which removes attacks from the analysis when A has dimension at least two. If you cannot vouch for this, use untrusted-source mode: the key rate can only drop, and the result stays valid.

For this run:

- source_mode: trusted
- alice_marginal: dimension = 2, sector_dims = 2
- alice_povm: alphabet = (Z,0), (Z,1), (X,0), (X,1), dimension = 2, form = povm
- party_partition: system A: party A (Alice); measured station: the receiver (Bob)

#### <a id="category-receiver"></a>Your receivers

Premises about the measuring stations, whichever party each belongs to. Evidence for them comes from characterising each receiver as built: detector efficiencies and dark counts, the optical elements and the modes they act on, and tests against detector-control attacks such as bright-light blinding.

##### <a id="A-IDEAL"></a>A-IDEAL: Ideal qubit receiver on the Band-A route

| Field | Value |
| --- | --- |
| About | Bob's station |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | On the Band-A route the declared receiver is an exactly projective qubit measurement with unit efficiency and no loss, dark counts, multi-photon events or misalignment, on a transmitted system that is exactly a qubit. The route is an explicit idealization, not a squashing argument. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Ideal qubit receiver on the Band-A route"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:ideal) |
| Category | receiver |
| Machine key | `ideal_qubit_receiver` |
| Emitted by | `protocol-compiler` |

Only for an idealised Band-A analysis: your receiver is a perfect qubit measurement, with unit detection efficiency, no loss, no dark counts, no multi-photon events and no misalignment, and what reaches it in each round is exactly one qubit. The engine refuses a Band-A declaration whose own numbers contradict this: more than one measuring station, a measured system (or, with a trusted source, a transmitted system) of dimension other than two, or a measurement not made of projectors (per basis, where a basis choice is declared). No real optical receiver meets this; use the route to reproduce textbook comparison values. Declare a real device through the receiver module and a squashing reduction.

For this run:

- declared_povm: choices = Z, X, party = B, physical_dim = 2, presentation = choice-weighted
- transmitted_dim: 2

#### <a id="category-channel-and-adversary"></a>The channel and the attacker

Premises about the attacker and what she can do. Evidence comes from the authentication scheme's specification and implementation review and, for detector-control premises, from testing the receiver under attack. No premise limits the size of the attacker's memory: the security statement holds against an attacker with memory of any size.

##### <a id="A-AUTH"></a>A-AUTH: Authentication of the classical channel by a keyed scheme

| Field | Value |
| --- | --- |
| About | The classical channel and the attacker |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Points | all completed points |
| Summary | Every classical message travels through an authentication scheme using at most k_auth bits of pre-shared key and realising the authenticated classical channel within ε_auth, a reused key's distance from an ideal one included. It is the premise by which authentication enters the key's security. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth) |
| Category | channel-and-adversary |
| Machine key | `classical_channel_authenticated` |
| Emitted by | `meat-core` |

Every classical message of your protocol, per-round announcements included, is protected by one authentication scheme: the attacker may read, delay or block any message, but one she alters or injects, or delivers before it was sent, is rejected except within an error ε_auth. It uses at most k_auth bits of pre-shared secret key per run. That error is its composable error on two identical copies of a uniform, independent key plus the distance of the parties' actual copies from such a pair (zero for a fresh key; for a key from an earlier run, a distance you must bound, which that run's security parameter alone does not bound); declare that sum as ε_auth and the bits used as k_auth. No composable proof for this timing-aware channel is published yet; Wegman–Carter authentication with separate keys per direction approximates it. Both declared zero assert a keyless authenticated channel.

For this run:

- ε_auth (eps_auth): 0.0
- k_auth (k_auth): 0

#### <a id="category-protocol-structure"></a>The protocol's structure

Premises that the run follows the protocol as declared. Evidence for them comes from reviewing the implementation and its recorded data against the protocol description.

##### <a id="A-ALPHABET"></a>A-ALPHABET: An acceptance value recorded in every round

| Field | Value |
| --- | --- |
| About | The protocol's structure |
| At stake | secrecy (the key may leak to the attacker); completeness (an honest run may abort more often) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | In every one of the n rounds of the run an acceptance value of the alphabet is recorded. The counts and the frequency vector then describe the whole run, normalised by its round count. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "An acceptance value recorded in every round"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:alphabet) |
| Category | protocol-structure |
| Machine key | `acceptance_recorded_every_round` |
| Emitted by | `statistics` |

Every one of the n rounds of your run records an acceptance value from the declared acceptance alphabet: no round counted in n is missing from the record. If rounds go missing (for example through lost time tags), the counts are normalised against the wrong number of rounds and the acceptance test does not describe the run. A round missing from the record also puts security at stake: the acceptance test must be evaluated on the acceptance values of all n rounds ([A-CONFORM](#A-CONFORM)), and a measured round the record drops is a sifting step the declaration does not describe ([A-SPEC](#A-SPEC)). Where the engine builds the acceptance set, it checks that the alphabet, its order and n are those of your protocol declaration; a set carried in the declaration is read in the declaration's order, so writing it in that order is yours to check.

For this run:

- acceptance_alphabet: [the 4 acceptance outcomes](#setup-acceptance)
- rounds: 10000

##### <a id="A-FIXED"></a>A-FIXED: Protocol parameters fixed before the run

| Field | Value |
| --- | --- |
| About | The protocol's structure |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Points | all completed points |
| Summary | The acceptance set, the round count, the key length, the transcript length, the error budgets, the authentication parameters and the Rényi order are fixed before the run and applied unchanged. The key length is that of a fixed-length protocol, not one chosen from the run's data. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Protocol parameters fixed before the run"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:fixed) |
| Category | protocol-structure |
| Machine key | `parameters_fixed_before_run` |
| Emitted by | `meat-core` |

Every parameter the key length rests on is fixed before the run starts: the acceptance test, the number of rounds, the key length, the error-correction budget λ_EC, the error budgets ε_PA and ε_EV, and the authentication parameters ε_auth and k_auth. The Rényi order α at which the key length is computed is fixed before the run too; choosing it by comparing the key lengths your declared model gives at several orders, as the run tier's outer search over α does, reads no data of the run and is such a choice. None of them may be chosen or adjusted after looking at the run's data, for example by relaxing the acceptance threshold or picking the key length from the observed error rate. That would be a variable-length protocol, which this analysis does not cover.

For this run:

- acceptance_set: alphabet = the 4 acceptance outcomes (see Acceptance test), geometry = polytope, inequalities = 8
- rounds: 10000
- key_length: varies between the points
- λ_EC (lambda_ec): 0
- ε_PA (eps_pa): 9.31e-10 (2^-30)
- ε_EV (eps_ev): 9.31e-10 (2^-30)
- ε_auth (eps_auth): 0.0
- k_auth (k_auth): 0

##### <a id="A-RHOM"></a>A-RHOM: Round homogeneity of the declaration

| Field | Value |
| --- | --- |
| About | The protocol's structure |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | The same specification, source mode and operators describe every round: the sameness clause of round homogeneity, not the absence of memory across rounds. One compiled declaration and one certificate decision then serve the whole run. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Round homogeneity of the declaration"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:rhom) |
| Category | protocol-structure |
| Machine key | `round_homogeneity_declaration` |
| Emitted by | `protocol-compiler`, `meat-core` |

One protocol description covers the whole run. Every round uses the same measurements, the same setting choices and their probabilities, and the same classical processing, and, where the source is trusted, the same source, so one declaration and one certificate decision apply to all n rounds. A run in which you change settings, or your devices drift so that later rounds need different operators, violates this. Only parts of a run fixed before it starts, each processed as its own execution and composed under [A-SEPARATE](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:separate-executions), which also asks that no device carry a state from one part into the next, can be analysed separately; a split chosen after seeing the data is not covered. That no device remembers earlier rounds is not part of this premise: for the measuring stations it is [A-SPEC](#A-SPEC), for Alice's letter [A-ALICE-MEAS](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:alice-meas), and where the source is trusted the source premise.

For this run:

- specification: 367 characters, written out in full below
- source_mode: trusted
- rounds: 10000

acceptance_alphabet = the 4 acceptance outcomes (see Acceptance test), alice_dim = 2, announcement_alphabets = A = Z, (X,0), (X,1), B = Z, (X,0), (X,1), key_alphabet = 0, 1, key_holder = A, physical_receiver_dims = 2, readout_alphabets = A = (Z,0), (Z,1), (X,0), (X,1), B = (Z,0), (Z,1), (X,0), (X,1), signal_alphabet = (Z,0), (Z,1), (X,0), (X,1), transmitted_dim = 2

##### <a id="A-SEQ"></a>A-SEQ: Sequential round structure

| Field | Value |
| --- | --- |
| About | The protocol's structure |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | Each round runs the delivery of its quantum systems, then every party's measurement, then the round's public messages, then sifting; each party measures in round order, post-processing follows all rounds and every message is public. It is the timing premise of the security analysis. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Sequential round structure"](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:seq) |
| Category | protocol-structure |
| Machine key | `sequential_round_model` |
| Emitted by | `transmitter`, `meat-core` |

In every round the quantum systems come first: where your source is trusted, it prepares and sends that round's signal, and otherwise the systems of the round are delivered to the measuring stations. Then every party that measures completes its measurement, and only then are that round's public messages sent, in the declared order. Sifting is then determined by the announcements, and no operation on a quantum system of a round depends on a public message of that round. All classical post-processing (for example error correction, verification and privacy amplification) runs after all n rounds, and every classical message is public. A message sent before a measurement of the same round has finished (for example an early basis announcement) violates this. Each party that measures completes its measurement of each round before it completes that of the next round.

For this run:

- rounds: 10000

##### <a id="A-SPEC"></a>A-SPEC: Specification faithful to the apparatus

| Field | Value |
| --- | --- |
| About | The protocol's structure |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | Declared dimensions, alphabets, tables and measurements describe the apparatus: the receiver's in every round whatever the others did and, where no source certificate is demanded, Alice's of two or more letters; every input yields a key. The compiler checks only the last, in part. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Specification faithful to the apparatus"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:spec) |
| Category | protocol-structure |
| Machine key | `specification_describes_apparatus` |
| Emitted by | `protocol-compiler` |

Your declared numbers describe your apparatus: each system has its declared dimension, every alphabet and table (announcements, sifting, the raw key bit) is what your devices and software do, and the key rule yields a key value, never "no key", on every input. Each measuring station, of either party, performs exactly its declared measurement in every round, on that round's input alone; afterpulsing or a dead time violates this. A declared receiver instrument's measurement is the model the engine emits from it; the emission step is recorded, not bounded. Where no source-replacement certificate is demanded (an untrusted source, or a one-dimensional A), Alice's declared measurement of her letter is the one she performs; [A-ALICE-MEAS](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:alice-meas) adds every round, alone. The engine checks that the declaration is well formed, not that it matches your hardware.

Not on this run: Alice's declared measurement of two or more letters, since a trusted source with A of dimension two or more demands a source-replacement certificate instead.

For this run:

- specification: 367 characters, written out in full below
- receiver_family: choices = Z, X, party = B, physical_dim = 2, presentation = choice-weighted

acceptance_alphabet = the 4 acceptance outcomes (see Acceptance test), alice_dim = 2, announcement_alphabets = A = Z, (X,0), (X,1), B = Z, (X,0), (X,1), key_alphabet = 0, 1, key_holder = A, physical_receiver_dims = 2, readout_alphabets = A = (Z,0), (Z,1), (X,0), (X,1), B = (Z,0), (Z,1), (X,0), (X,1), signal_alphabet = (Z,0), (Z,1), (X,0), (X,1), transmitted_dim = 2

#### <a id="category-local-randomness"></a>Your random number generators

Premises about the local randomness of the choices and hash seeds. Evidence for them comes from certifying the random number generators.

##### <a id="A-COIN"></a>A-COIN: Public choices as private coins of declared bias

| Field | Value |
| --- | --- |
| About | Your random number generators (the choices drawn by Alice and at Bob's station) |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | Every public choice is drawn with its declared bias; those of fixed bias are jointly independent of each other, the quantum systems and the adversary, and one weighted by a station's setting depends on the round through that setting only. It lets a weight inside the measurement describe the round. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Public choices as private coins of declared bias"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:coin) |
| Category | local-randomness |
| Machine key | `public_choice_weights` |
| Emitted by | `protocol-compiler` |

Every public choice of your protocol (for example an actively chosen basis, or whether a round is a test round; a basis set passively by a beam splitter is part of the measurement, not a choice), whichever party draws it and at whichever of its stations, comes from a local random number generator with exactly the declared probabilities, and each is announced or kept secret exactly as declared. The choices with fixed probabilities are independent of each other and, all together, of the quantum signals and of anything an attacker does. A choice whose probabilities depend on a station's private setting is drawn by a party whose recorded outcome includes that setting, and may depend on that setting only, never otherwise on Alice's letter, another choice or a detection result.

Not on this run: a choice whose probabilities depend on a station's private setting, since no choice on this run is weighted by a setting.

For this run:

- public_choices: Alice: Z 0.5, X 0.5; Bob: Z 0.5, X 0.5
- specification: 367 characters, written out in full below

acceptance_alphabet = the 4 acceptance outcomes (see Acceptance test), alice_dim = 2, announcement_alphabets = A = Z, (X,0), (X,1), B = Z, (X,0), (X,1), key_alphabet = 0, 1, key_holder = A, physical_receiver_dims = 2, readout_alphabets = A = (Z,0), (Z,1), (X,0), (X,1), B = (Z,0), (Z,1), (X,0), (X,1), signal_alphabet = (Z,0), (Z,1), (X,0), (X,1), transmitted_dim = 2

##### <a id="A-SEED"></a>A-SEED: Private, independent and fresh local randomness

| Field | Value |
| --- | --- |
| About | Your random number generators |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Points | all completed points |
| Summary | The post-processing seeds are drawn with their declared laws, privately, independently and afresh; in trusted-source mode the source's letters and prepared systems are independent of the adversary, who never gets a purification of them. Leftover hashing and source replacement rest on it. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Private, independent and fresh local randomness"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:seed) |
| Category | local-randomness |
| Machine key | `post_processing_seeds` |
| Emitted by | `meat-core` |

Your random choices come from a good private random number generator. The error-correction seed, the error-verification hash and the privacy-amplification hash are each drawn with their intended distribution, kept secret until the protocol announces them, independent of each other, of every other record of the protocol (the raw key included) and of everything the attacker knows, and drawn anew in every run. With a trusted source, the randomness with which it picks each round's letter and prepares its state is uncorrelated with the attacker at the start, and no purification of a prepared state is ever available to the attacker. A seed reused across runs, fixed in the device or disclosed early, or a predictable or pre-shared random source, violates this.

Which party draws each post-processing seed (the error-correction seed, the error-verification seed and the privacy-amplification hash) is not fixed by the analysed post-processing: each is drawn and then announced. As for the seeds, this premise is about the random number generator of whichever party draws each; [A-HASH](#A-HASH) is about the hash families the seeds select from.

For this run:

- source_mode: trusted

#### <a id="category-post-processing"></a>Your post-processing

Premises about error correction, error verification and privacy amplification. Evidence for them comes from reviewing and testing that software.

##### <a id="A-CONFORM"></a>A-CONFORM: The implementation runs the analysed post-processing

| Field | Value |
| --- | --- |
| About | Your post-processing |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Points | all completed points |
| Summary | The implementation applies the acceptance test and the verification abort, sends no message beyond the model's, outputs the model's key or nothing, uses no key before the execution ends and aborts on an authentication failure. It ties the analysed protocol to the one that runs. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "The implementation runs the analysed post-processing"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:conform) |
| Category | post-processing |
| Machine key | `post_processing_as_analysed` |
| Emitted by | `meat-core` |

Your implementation runs exactly the analysed post-processing. It aborts unless the acceptance statistics lie in the declared acceptance set; after the rounds it sends no public message other than the error-correction transcript of at most λ_EC bits and its seed, the verification seed, hash and result, the privacy-amplification hash choice and the closing accept or abort decisions; it aborts when verification fails or a message fails authentication (an auth-abort); it outputs the analysed ℓ-bit key, or nothing. No part of the key is used before the execution has ended: the key holder, having sent its final decision, waits until the partner has received it or an auth-abort in its place, and the partner until one of these has arrived. Interactive error correction, a resent syndrome or early key use violate this. Tightening 2ε_auth to ε_auth under this timing is an open question.

For this run:

- acceptance_set: alphabet = the 4 acceptance outcomes (see Acceptance test), geometry = polytope, inequalities = 8
- λ_EC (lambda_ec): 0
- ev_hash_bits: 30
- key_length: varies between the points

##### <a id="A-HASH"></a>A-HASH: Ideal two-universal privacy amplification

| Field | Value |
| --- | --- |
| About | Your post-processing |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Points | all completed points |
| Summary | Privacy amplification uses an ideal two-universal family, collision probability exactly 2^−ℓ for distinct inputs, and error verification a two-universal family. The first is what leftover hashing reads, the second what the verification collision bound reads. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Ideal two-universal privacy amplification"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:hash) |
| Category | post-processing |
| Machine key | `pa_hash_family` |
| Emitted by | `meat-core` |

Privacy amplification uses a hash family in which any two different inputs collide with probability exactly 2^−ℓ (an ideal two-universal family, such as Toeplitz hashing), and error verification uses a two-universal hash family. If your privacy-amplification family is only two-universal (collision probability at most 2^−ℓ), shorten the key by one further bit.

For this run:

- key_length: varies between the points
- ideal_hash: true
- ev_hash_bits: 30

##### <a id="A-KEYREG"></a>A-KEYREG: Dedicated key register and one-way reconciliation

| Field | Value |
| --- | --- |
| About | Your post-processing |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | The post-processing acts on the raw-key string the rounds write, the declared holder computes that string, and reconciliation runs one way from the holder through a padded fixed-length transcript. The leakage term counts the register's full length. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Dedicated key register and one-way reconciliation"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:keyreg) |
| Category | post-processing |
| Machine key | `key_register` |
| Emitted by | `meat-core` |

Error correction is one-way. The key holder computes its raw key from its own record (its letters, the detection results of its measuring stations, or both, whichever it holds) and the public announcements, and its messages depend only on that raw key and public random seeds. The transcript always has exactly λ_EC bits, shorter messages being padded. Interactive error correction (for example Cascade) or a variable-length transcript is not covered by this key length.

On this run Alice holds the key; her own record here is her letters.

For this run:

- λ_EC (lambda_ec): 0
- key_holder: A

#### <a id="category-honest-model"></a>The honest model

Premises about what an honest run looks like; each bears on completeness: how often an honest run aborts, or whether a key length is reported at all. One whose If it fails row says security, as A-REACH's does, bears on security as well. Evidence for them comes from comparing the model's expected statistics with measured data.

##### <a id="A-HON-ENV"></a>A-HON-ENV: Honest rounds inside a declared envelope

| Field | Value |
| --- | --- |
| About | The honest model (what an honest run is expected to show) |
| At stake | completeness (an honest run may abort more often) |
| If it fails | only how often an honest run aborts, never security |
| Points | all completed points |
| Summary | On an honest run each round's probability of each acceptance outcome, given everything before it, stays inside the declared honest envelope. The premise bears on the advertised honest abort probability and restricts no adversary. |
| Review status | implemented, also with everything it rests on |
| Statement | [Assumption "Honest rounds inside a declared envelope"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:hon-env) |
| Category | honest-model |
| Machine key | `honest_rounds_within_envelope` |
| Emitted by | `statistics` |

When no attacker is present, each round's probability of each acceptance outcome, given everything that happened before, stays inside the honest model: between the lower and upper bounds of the honest envelope where you declared one, and equal to the honest distribution where you gave a single one instead (an envelope of zero width). With an envelope the channel may drift within and between runs as long as it stays inside it; with a single distribution it may not drift at all. This premise only bears on the advertised probability that an honest run aborts; it never affects security. If drift can leave the honest model, declare a wider envelope.

For this run:

- honest_model: iid_honest_rounds
- honest_distribution: varies between the points
- rounds: 10000

##### <a id="A-REACH"></a>A-REACH: An honest law produced by a feasible state

| Field | Value |
| --- | --- |
| About | The honest model (what an honest run is expected to show) |
| At stake | secrecy (the key may leak to the attacker); completeness (an honest run may abort more often, and a checked run whose mismatch is proven may report no key length) |
| If it fails | security (the key may leak) |
| Points | all completed points |
| Summary | Some feasible state of the consuming declaration produces a law of the declared honest envelope, for a single declared law that law itself. It rules out an incompatibility of the honest model with the declaration. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "An honest law produced by a feasible state"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:reach) |
| Category | honest-model |
| Machine key | `honest_reachable` |
| Emitted by | `statistics` |

Your honest model fits your protocol declaration: a state the declaration admits as feasible produces acceptance statistics in your declared honest envelope, or equal to your single declared honest law. If it fails, the declared devices do not describe the statistics and a key length for them is not warranted. The engine's own honest models are built to match the declared Alice marginal; nothing proves this premise for them. Unless switched off, the engine checks every run whose honest statistics you supply or whose declaration carries a constraint you declared: from a proven mismatch it states a cap on the probability that devices behaving as the declaration says pass your acceptance test, and refuses the run where that cap is at most one half, a threshold you can set. On an unchecked run a mismatch goes undetected and this premise is yours to vouch for.

For this run:

- honest_distribution: varies between the points

### Declared in the protocol document, vouched for by you

| Assumption | Kind | Label | Declared | Record |
| --- | --- | --- | --- | --- |
| [A-SPEC](#A-SPEC), [A-IDEAL](#A-IDEAL) | `receiver_povm` | `bob` | The measurement of station 'bob', declared as a POVM. Declared in the run's protocol document (your own or a shipped template), not derived by the engine; you vouch for it. The premise is that these matrices describe the receiver you have, performed in every round on that round's system alone, whatever happens in the other rounds (A-SPEC). The Band-A route the engine takes for a declared POVM rests on A-IDEAL: an ideal qubit measurement, on a transmitted system that is exactly a qubit, with unit efficiency, no loss, no dark counts, no multi-photon events and no misalignment. If your receiver is not such a measurement, A-IDEAL fails and the key length does not apply to it; declare it as an optical station (kind: optical) instead (instances/declared/README.md). \[all completed points\] | [record](points/0000.record.md#p-.payload.protocol_document.user_declared.0) |

## <a id="points"></a>Per-point differences

What differs from point to point: the varying inputs, each point's own numbers, its route and whether its key length rests on a measurement snap. Each point's report has the rest.

| Point | Label | parameters.eps_auth | model.qber | Key length | Net key length | Rate per round | Tier | Security parameter | Outcome | Route | Measurement snaps | Report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | — | 0.0 | 0.02 | 1170 | 1170 | 0.117 | certified | 1.862645149230957e-09 | key-length | common | — | [report](points/0000.md) |
| 1 | — | 0.0 | 0.04 | 935 | 935 | 0.0935 | certified | 1.862645149230957e-09 | key-length | common | — | [report](points/0001.md) |
| 2 | — | 0.5 | 0.06 | — | — | — | — | — | refused `security_statement_vacuous` | — | — | [report](points/0002.md) |

## <a id="appendix"></a>Appendix

### <a id="checks"></a>Checks the engine ran

| Check | Outcome | Value | Claims | Record |
| --- | --- | --- | --- | --- |
| `snaps-within-tolerance` Instance snaps within the declared tolerance | varies: 0: passed; 1: passed; 2: not-applicable | varies |   |   |
| `receiver-route` Receiver route | passed | varies | [Definition "Compilation of a declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:compile) | [record](points/0000.record.md#p-.payload.stages.receiver_construction.receiver_route) |
| `element-graph-acyclic` Declared element graph well formed | not-applicable | varies | [Definition "Declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:graph), [Requirement "Refusal of a graph that is not well formed"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/req:graph-refusal) | [record](points/0000.record.md#p-.payload.stages.receiver_construction.receiver_route) |
| `probe-states-diagonal` Probe declaration admitted | not-applicable | — | [Definition "Probe declaration"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:probe), [Requirement "Admission of Gaussian-tier probe states only"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/req:probe-diagonal-admission) |   |
| `specification-well-formed` Specification well formed | passed | — | [Definition "Well-formed specification"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/def:well-formed-spec), [Theorem "Soundness, completeness and decidability of the validator"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:validator-soundness) | [record](points/0000.record.md#p-.payload.stages.compilation) |
| `compiler-gates` Compiler emission gates | passed | — | [Theorem "The emission gates and their outcomes"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:gates) | [record](points/0000.record.md#p-.payload.compiled) |
| `exact-statistics-inputs` Acceptance-set inputs admissible | passed | varies | [Requirement "Refusal of an input that violates a decidable clause"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/req:input-refusal) | [record](points/0000.record.md#p-.payload.stages.acceptance_construction.geometry) |
| `matched-alphabet` Acceptance alphabet matches the declaration | passed | varies | [Requirement "Alphabet and round count taken from the consuming declaration"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/req:matched-alphabet) | [record](points/0000.record.md#p-.payload.stages.acceptance_construction.outcomes) |
| `declaration-admitted` Declaration exactly admissible | passed | — | [Requirement "Exact admission of declared data"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:exact-admission) | [record](points/0000.record.md#p-.payload.stages.key_rate) |
| `alpha-range` Rényi order of the key length | passed | varies | [Requirement "Rényi order of a reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:key-length-alpha-domain) | [record](points/0000.record.md#p-.payload.stages.key_rate.alpha) |
| `security-statement-not-vacuous` Security statement not vacuous | varies: 0: passed; 1: passed; 2: refused | varies | [Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous) |   |
| `key-length-gate` Key-length security gates | varies: 0: passed; 1: passed; 2: not-reached | varies | [Requirement "Two-part gate on a key length with declared constraints"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:constrained-key-gate), [Requirement "Source licence for a declared marginal"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:marginal-licence-gate), [Theorem "Constrained accumulation under the attack-set licence"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:constrained-accumulation) |   |
| `first-order-hypotheses` First-order hypotheses at the contributing iterates | varies: 0: passed; 1: passed; 2: not-reached | varies | [Requirement "Withdrawal of the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:first-order-withdrawal), [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder) |   |
| `reported-key-length` Reported key length | varies: 0: passed; 1: passed; 2: not-reached | varies | [Requirement "Reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:reported-key-length) |   |

#### Discharged on the route

| Assumption | Module | Reason | Discharged by | Points |
| --- | --- | --- | --- | --- |
| [A-LINK](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:link) | `protocol-compiler` | discharged on this route by [Theorem "The Band-A route"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:band-a) | `protocol-compiler/thm:band-a` | all completed points |

### <a id="not-engaged"></a>Not engaged on this route

#### Not engaged on the route

| Assumption | Module | Reason | Points |
| --- | --- | --- | --- |
| [A-ALICE-MEAS](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:alice-meas) | `protocol-compiler` | emission rule: wherever no source-replacement certificate is demanded (untrusted-source mode, or d_A = 1) and the letter alphabet X has at least two letters; at one letter {M_x} is the identity on A and [Assumption "Alice's declared measurement where no source certificate is demanded"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:alice-meas) holds of every device; not met on this route | all completed points |
| [A-ATK](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:atk) | `protocol-compiler` | emission rule: whenever m >= 1 and a key-length-eligible declaration is wanted; not met on this route | all completed points |
| [A-ATK](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:atk) | `meat-core` | emission rule: whenever the constraint list is non-empty and a key length is wanted, on a run that reports a key length or a first-order bound; not met on this route | all completed points |

### <a id="provenance"></a>Provenance

#### <a id="status-legend"></a>What a claim's status means

- superseded: replaced by a newer claim; it no longer counts.
- draft: not yet through an independent review, or sent back by one, or substantively amended since.
- verified: passed an adversarial review by an AI model that saw only the written artefacts (the claim files and the references they cite), not the author's reasoning; not yet accepted by a person.
- accepted: passed that review and was then accepted by the project's human owner.
- implemented: accepted, and the code that implements it is accepted.
- effective status: the lowest status over the claim and everything it rests on.

| Sweep | Value |
| --- | --- |
| id | 53209367d74663dbaf4fa6a8df8a21c6b29d6eca078415b356e83efdb357a46b |
| points | 3 |
| record schema | 0.46.0 |
| report schema | 0.36.0 |

| Instance | Value |
| --- | --- |
| id | bb84 |
| title | Ideal qubit BB84 |
| summary | Trusted-source BB84 with configurable basis weights, a directly declared qubit measurement and an explicit identity reduction link. The honest channel is depolarizing and is parameterized by its quantum bit error rate. This instance provides a simple reference for optical BB84 runs. |
| readme | [instances/bb84/README.md](../../../instances/bb84/README.md) |

| Provenance | Value |
| --- | --- |
| engine | distribution_version = 0.1.0; git_commit = da9eda22e78a438c7bc0dfa7fb8909b0065a132f; git_dirty = false |
| created_by | runs.report_examples.generate |

### <a id="glossary"></a>Glossary

- <a id="g-a-the-letter"></a>A (the letter): The report uses the letter A in four ways: party A of the declaration (Alice); system A, the declaration's per-round letter on that party's side; a detector port named A (as among BBM92's ports H, V, D and A); and the prefix of a premise's short id (A-LAB, A-SPEC). Which is meant follows from where it stands. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-acceptance-test"></a>acceptance test: The test every run applies to its statistics: each round records one acceptance value, and the run continues only if the frequency of every value lies in an interval (together, the box) around the honest model's prediction. See [Definition "The construction map"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/def:construction).
- <a id="g-alice"></a>Alice: The name the report gives party A of the declaration. A party may send, measure, or both: in a prepare-and-measure protocol Alice usually sends, in an entanglement-based one she measures at a station; the run's record says which. Where a premise speaks of Alice's letter or of system A, it means the party the declaration assigns A to: Alice, unless the party partition says otherwise. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-band-a-route"></a>Band-A route: The direct route: a finite measurement declared on one sector, with no optical characterisation and no photon-number reduction. It needs an ideal qubit receiver (A-IDEAL), which no real optical receiver is.
- <a id="g-binding"></a>binding: A value of this run that an assumption is about, for example the ε_auth you declared for A-AUTH; shown under the assumption so that you know what exactly you vouch for.
- <a id="g-bob"></a>Bob: The name the report gives party B, the other of the declaration's two parties. Like Alice, he may send, measure, or both; on most protocols he measures at one or more stations. Which he does on this run is read from its record, which also says which party holds system A. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-budget"></a>budget: An error probability (an ε) that you choose before the run. The secrecy, error-verification and authentication budgets ε_PA, ε_EV and ε_auth make up the security parameter ε. The completeness budget ε_comp is not part of ε: it is the largest ε\* you allow and bounds only how often an honest run fails the acceptance test. The configuration keys keep the word (completeness_budget). See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-certified-bound"></a>certified bound: The first-order bound formed again at the solver's final points from the declared data, every arithmetic step exact or rigorously enclosed: a lower bound on h_low that rests on the claims and the modelling premises and on no premise about floating-point arithmetic. Where a run reaches it, the key length is computed from it, exactly. See [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength).
- <a id="g-completeness"></a>completeness: How often an honest run, with no attacker and devices behaving as modelled, aborts. It never affects the security parameter ε, which holds for every abort pattern. See [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope).
- <a id="g-composable"></a>composable: The kind of security statement the guarantee is: no test, whatever the attacker knows, tells the run's output from an ideal key exchange with advantage above ε. Later uses of the key build on such a statement, but this contract proves only that separate executions add their ε, not that every later use of the key is covered. See [Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions).
- <a id="g-constraint-entry"></a>constraint entry: A constraint a declaration places on the states it admits, beyond the declared marginal. A run whose declaration carries an entry you declared is checked by the statistics check unless that check is switched off (the inputs table says whether it ran); entries the compiler or a reduction derives do not by themselves call for it. See [Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set).
- <a id="g-declared-tolerance-tau"></a>declared tolerance τ: The ceiling on the defects of the run's own data that the snap may repair before solving.
- <a id="g-detection-efficiency"></a>detection efficiency: The probability that a detector clicks on a photon that reaches it.
- <a id="g-effective-status"></a>effective status: The lowest review status over a claim and everything it rests on; a claim accepted on its own is only as reviewed as its weakest premise.
- <a id="g-emitted-by"></a>emitted by: The module of the engine whose result rests on the assumption on this run, with the station it was emitted at (station0, station1, ...).
- <a id="g-endpoint-rule"></a>endpoint rule: How the acceptance test sets the ends of each outcome's interval: the exact binomial quantile rule (exact) or the closed-form Bernstein rule (bernstein).
- <a id="g-estimate"></a>estimate: The value of the objective at the point the solver returned. It claims no bound: that point is feasible only within a window, so the estimate need not lie above the true minimum h_low. No key length is computed from it.
- <a id="g-feasible-state"></a>feasible state: A state the declaration admits: block-diagonal and normalised, with the declared marginal and constraints. h_low is an infimum over the feasible states whose statistics pass the acceptance test.
- <a id="g-first-order-bound"></a>first-order bound: A lower bound on h_low from the tangent planes of the objective at the solver's steps. Its proof is exact, and the minima it uses are bounded from below in exact arithmetic, not taken from the solver; its objective and gradient are computed in floating point with no bound on their numerical error. Stopping early makes it looser, not invalid. The key length uses it where the run is not certified. See [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder).
- <a id="g-frank-wolfe"></a>Frank-Wolfe: The solver's iterative method: each step minimises a linear approximation of the objective over the feasible set and moves toward that point. See [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder).
- <a id="g-generation-and-test-rounds"></a>generation and test rounds: gen is the acceptance value of a round whose announcements pass sifting, so that it may give key. Where a public test coin exists (as in BBM92) it makes each round a generation round (gen), which may give key, or a test round (test), in which both parties announce their full outcome. Every round of either kind records one acceptance value.
- <a id="g-geometry-acceptance-set"></a>geometry (acceptance set): The engine's name for the shape of the acceptance set it built; a box of intervals is a polytope.
- <a id="g-h-lb"></a>h_lb: The first-order lower bound on h_low: the best bound over the steps that passed the first-order checks. It is proved in exact arithmetic, its linear minima bounded exactly, and computed in floating point, so a computed h_lb can exceed h_low. A first-order run computes its key length from max{0, h_lb}; a certified run computes it from the certified bound h_cert and records h_lb beside it. See [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder).
- <a id="g-h-low"></a>h_low: A lower bound on the attacker's per-round uncertainty about the raw key, at the chosen α, over every attack compatible with your devices and with statistics that pass the acceptance test.
- <a id="g-honest-envelope"></a>honest envelope: The set of per-round outcome probabilities an honest run is declared to stay within (A-HON-ENV). With a single honest model, as on most runs, it is that model's one law. See [Assumption "Honest rounds inside a declared envelope"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:hon-env).
- <a id="g-honest-model"></a>honest model: The model of what an honest run looks like. It sets the acceptance test and the expected statistics; it never affects the security parameter ε, which holds for every abort pattern.
- <a id="g-iid-honest-rounds"></a>iid_honest_rounds: The acceptance construction's tag for its honest model. In its simplest form the honest rounds are independent and identically distributed with one declared law (A-HON); A-HON-ENV, where a run lists it, lets each round's law vary inside the declared envelope. See [Assumption "Honest i.i.d. rounds"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:hon).
- <a id="g-k-auth"></a>k_auth: The bits of pre-shared key the authentication uses per run; the net key gain is ℓ − k_auth. See [Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth).
- <a id="g-kept-snap-block"></a>kept (snap block): A snap block is kept where your model gives it exactly on the grid, so the snap changes nothing there; every other block is moved.
- <a id="g-key-length-ell"></a>key length ℓ: The number of secret key bits one run outputs, after deducting error correction, error verification and the finite-size cost of secrecy. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-key-map-and-sifting"></a>key map and sifting: Sifting decides from the public announcements which rounds give key; the key map sends each kept round's readout to a key bit. See [Theorem "Announcement locality, sifting and party computability"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:sifting-and-key).
- <a id="g-letter"></a>letter: The per-round value on Alice's side of the declaration (system A): in a prepare-and-measure protocol, the signal she prepares. A declaration with one letter uses no clause a premise makes for two or more letters. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-machine-key"></a>machine key: The stable identifier under which the engine records an assumption.
- <a id="g-net-key-length"></a>net key length: The key length minus the k_auth bits of pre-shared key the authentication consumed: what the run gains. See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-povm"></a>POVM: A measurement written as one positive operator per outcome; the probability of an outcome is the trace of its operator times the state.
- <a id="g-qber"></a>QBER: The quantum bit error rate: the fraction of key rounds in which the two parties' raw key bits differ.
- <a id="g-reference-snap"></a>reference (snap): Your declared receiver model, computed exactly (exact) or known through rigorous rational intervals (enclosed). The snap starts from it where it is exact, and the run hands it beside the snap so that the key length can be computed from it.
- <a id="g-reference-companion"></a>reference companion: Your receiver model put through the same reductions as the rounded measurement, without that rounding, its rows relaxed outward by their floating-point rounding and the model's intervals. A block not handed is carried rounded; with none handed, it is the reduction's exact construction before its own rounding. The run takes its first-order bound there and never solves it. See [Corollary "The reference companion of a reduction instance"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/cor:reference-companion).
- <a id="g-review-status"></a>review status: A claim's review stage, lowest first: superseded (replaced); draft (not yet through an independent review, sent back by one, or substantively amended since); verified (passed an AI model's adversarial review of the written artefacts, not the author's reasoning; not yet accepted by a person); accepted (by the project's human owner); implemented (accepted, its code too). Not a hardware check.
- <a id="g-round"></a>round: One use of the protocol as declared, which records its own outcomes. How a time-tagged system cuts its detection record into rounds (time bins, coincidence windows, how the stations synchronise) is your choice, and your declaration must describe it; What a round is, before the protocol's steps, names premises of this run that the cut bears on.
- <a id="g-sector"></a>sector: One block of a block-diagonal operator, named by a sector map.
- <a id="g-setting"></a>setting: A probe setting of a receiver; "off" is the setting with no probe light. A receiver without a probe has this one setting only, so on such a station "setting off" names its one measurement, not a switch. See [Definition "Probe declaration"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:probe).
- <a id="g-snap"></a>snap: Before solving, the declarer (your instance, or a reduction for what it emits) moves each measurement onto a grid of exact numbers of the same shape. A block your model gives exactly on the grid is kept; every other block is moved, and rests on A-SNAP unless it is evaluated off its snap.
- <a id="g-source-mode"></a>source mode: Whether the security analysis trusts the source. A trusted source's declared states enter the proof; an untrusted source is the attacker's, and its honest model only predicts the statistics.
- <a id="g-squashed-target-povm"></a>squashed target POVM: The finite-dimensional measurement the security proof works with; the reduction proves that analysing it covers your receiver.
- <a id="g-sr3"></a>SR3: Condition (SR3) of the source-replacement certificate: the retention attestation, that the retained system A stays in the laboratory of the party that holds it and is acted on only by that party's declared measurement. It carries no number and nothing decides it; you vouch for it as A-SRC.
- <a id="g-strict-option"></a>strict option: The run setting strict_snaps: on, the run refuses wherever a moved block or emission sector would rest on A-SNAP, and reports no key length that rests on it, and the certified evaluation does not fall back to the rounded measurement where your receiver model certifies no point; off, the default, such a block is disclosed. See [Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference).
- <a id="g-transmitter"></a>transmitter: The engine module that models the source side of the protocol. With a trusted source it carries the source's declared states and their premises (A-ENS, A-SRC, or A-WCP for a decoy source); with an untrusted source it carries no source premise. On every run it carries its part of the sequential round order, A-SEQ.
- <a id="g-alpha-r-nyi-order"></a>α (Rényi order): A parameter of the proof, not of your device: any value in (1, 2) fixed before the run gives a valid key length, and the choice changes only how long the key is, never its secrecy. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-eps-security-parameter"></a>ε (security parameter): The bound on how far one run's output can be told from an ideal key exchange: ε = ε_PA + ε_EV + 2ε_auth. It covers one execution. See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-eps-star-completeness"></a>ε\* (completeness): A bound on the chance that an honest run fails the acceptance test; it covers that test only, not later aborts in error verification or authentication. The completeness budget is the largest ε\* you allow. See [Theorem "The completeness bound"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/thm:completeness-bound).
- <a id="g-eps-auth"></a>ε_auth: The error of the authentication of the classical messages, which you declare, including, for a key from an earlier run, its distance from an ideal key; it is counted twice in ε. Zero asserts a channel that is itself authenticated. See [Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth).
- <a id="g-eps-ev"></a>ε_EV: A bound on the chance that both parties accept the run with different keys; error verification compares a hash of ⌈log₂(1/ε_EV)⌉ bits. See [Lemma "Correctness from error verification"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/lem:ev-correctness).
- <a id="g-eps-pa"></a>ε_PA: The secrecy error of privacy amplification: how far the key may be from uniformly random and independent of everything the attacker holds. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-lambda-ec"></a>λ_EC: The number of bits the error-correction transcript reveals; the key length deducts it in full. You declare it; with an estimate file beside the record the report shows how it was chosen. See [Assumption "Dedicated key register and one-way reconciliation"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:keyreg).
