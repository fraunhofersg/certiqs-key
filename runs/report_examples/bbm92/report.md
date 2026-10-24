# Key-rate report

## <a id="contents"></a>Contents

- [Summary](#summary): [Key rate considerations](#considerations) · [The result](#result) · [Your setup in brief](#setup-brief) · [What the guarantee means](#guarantee) · [Roles on this run](#roles) · [What you vouch for](#vouch) · [Not counted](#not-counted) · [Choices that could lengthen the key](#levers)
- [Your QKD setup](#setup)
- [Your inputs](#inputs)
- [Assumptions you vouch for](#assumptions)
- [Appendix](#appendix): [How the number was computed](#how-computed) · [Measurement snaps](#measurement-snaps) · [Measurement snaps in detail](#snaps-detail) · [Security claims](#security-claims) · [Checks the engine ran](#checks) · [Not engaged on this route](#not-engaged) · [Route, instance and preparation](#route) · [Provenance](#provenance) · [Glossary](#glossary)

## <a id="summary"></a>Summary

> **At a glance**
>
> - **Idealised example**, not a characterised device ([Your inputs](#inputs))
> - **BBM92 with two passive stations**, no loss, detector efficiency 1, expected QBER 0 ([Your QKD setup](#setup))
> - **Key length ℓ = 40,192,819 bits** from n = 100,000,000 rounds ([The result](#result))
> - **Key rate ℓ/n = 0.402 bits per round**, every round counted ([The result](#result))
> - **Security parameter ε = 1.86e-09 (2^-29)**, the target you set (ε_PA = 9.31e-10, ε_EV = 9.31e-10) ([What the guarantee means](#guarantee))
> - **Free authentication**: the run assumes an authenticated classical channel at no cost (ε_auth = 0, k_auth = 0), an idealisation like the device values ([Not counted](#not-counted))
> - **No error-correction cost counted**: λ_EC = 0 as declared, so for a run that sends an error-correction transcript this key length is too long ([Not counted](#not-counted))
> - **26 premises** for you to vouch for: the key length and ε are guaranteed when all of them hold ([What you vouch for](#vouch))
> - **Model-based**: no measured data analysed; the acceptance test is built around your honest model's predictions ([Acceptance test](#setup-acceptance))

### <a id="considerations"></a>Key rate considerations

- The accepted statistics were not checked against your declared model, so that a state your declared devices admit can produce them ([A-REACH](#A-REACH)) is yours to vouch for. See [The result](#result).
- The key length is certified: its bound was formed again with every arithmetic step exact or rigorously enclosed, so the certified evaluation adds no premise about numerics; the premises the run lists remain. See [How the number was computed](#how-computed).
- What is idealised: the run's device values are at their ideal extreme (dark-click probability 0, detection efficiency 1, polarising beam splitter reflected leak 0, polarising beam splitter transmitted leak 0): the key length covers only a device with exactly these values ([A-EXACT](#A-EXACT)). The run's honest model is at its ideal extreme (transmittance 1, visibility 1): the acceptance test is built for statistics a real device may not show. The acceptance test built from it admits a count of exactly 0 in 64 outcomes, so a single round with one of them makes the run abort ([A-CONFORM](#A-CONFORM); see Acceptance test). For such a device the completeness figure ε\* no longer bounds how often it aborts; security is unaffected. See [Your inputs](#inputs).

### <a id="result"></a>The result

From n = 100,000,000 rounds the protocol, unless it aborts, outputs a key of ℓ = 40,192,819 bits: a key rate of 0.402 bits per round, ℓ divided by all n rounds, the rounds that give no raw key bit included. Its security parameter is ε = 1.86e-09. The accepted statistics were not checked against your declared model (its statistics are your honest model's predictions for your declared devices and you declared no constraint entry; [Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set)): that a state your declared devices admit can produce them, [A-REACH](#A-REACH), is yours to vouch for. The key length rests on a certified lower bound, h_cert, on the attacker's worst-case uncertainty per round about the raw key. h_cert is the solver's first-order bound formed again at its final points, from the data of the declaration it is formed on, with every arithmetic step exact or rigorously enclosed. It lies below that declaration's value by the claims alone, and the key length is computed from it exactly ([Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength), [Remark "What a certified number rests on"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/rem:certified-scope)). It is formed on the reference companion: the declaration built from your receiver model, through the model's rigorous intervals, on every block the run handed those intervals for.

From the accumulated entropy to the key you gain ([Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength)):

- The accumulated entropy, bounded below by n·h_cert ≈ 40,193,478.4 bits (n = 100,000,000 rounds, h_cert = 0.401935 bits per round).
- Less 0 bits that error correction reveals (λ_EC, as declared).
- Less a 30-bit hash for error verification (⌈log₂(1/ε_EV)⌉).
- Less 630 bits that privacy amplification costs for a finite key (α/(α−1)·log₂(1/ε_PA)).
- Plus one bit, a constant of the bound: its source's derivation adds two, and one of them pays for announcing whether error verification passed ([Remark "The constant in the key length and the source's convention"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:plus2)).
- Rounded down to a whole bit, the key length is ℓ = 40,192,819 bits.
- Authentication consumes k_auth = 0 bits of pre-shared key per run (declared); an aborted run may consume as many.
- You gain ℓ − k_auth = 40,192,819 bits.

Record: [record](record.md#p-.payload.stages.key_rate.deductions).

### <a id="setup-brief"></a>Your setup in brief

- Protocol: BBM92 with two passive stations, with an untrusted source (the proof uses no model of the source: whatever it delivers into the stations' declared input modes is treated as prepared by the attacker; that nothing else from it reaches a station, such as a clock or trigger line, pump light or light in an undeclared mode, is part of [A-LAB](#A-LAB) and [A-MODES](#A-MODES) under What you vouch for).
- Source: untrusted; honest model ideal_pair.
- Channel: Alice's arm transmittance 1 (no loss), Bob's 1 (no loss).
- Alice's station: an optical element graph, 4 optical elements, 4 detectors (detection efficiency 1, dark-click probability per round 0), photon cutoff N = 1.
- Bob's station: an optical element graph, 4 optical elements, 4 detectors (detection efficiency 1, dark-click probability per round 0), photon cutoff N = 1.
- Run: n = 100,000,000 rounds, test fraction 0.125, key bases ZX.

The details: [Your QKD setup](#setup).

### <a id="guarantee"></a>What the guarantee means

A run either aborts or outputs a key of ℓ bits that is a perfect key up to the security parameter ε: identical for both parties, uniform and independent of all the attacker holds, public messages included. One party may abort while the other gets a key. No test, whatever the attacker knows, tells the run's output from an ideal protocol's with advantage above ε = ε_PA + ε_EV + 2ε_auth. It holds against every attack, of any memory, if every premise in the run record holds, [A-AUTH](#A-AUTH), [A-CONFORM](#A-CONFORM) and [A-FIXED](#A-FIXED) included. A first-order run also needs its bound to hold, computed h_lb ≤ h_low, which no premise covers ([Remark "Exact real arithmetic in the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/rem:fo-arithmetic)). ε averages over aborted runs too. The criterion is composable. Separate executions provably add ε ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)). Not every later use of the key is covered ([Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions)). A run where both get a key nets ℓ − k_auth bits; an abort uses up to k_auth. Abort rates: [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope). Statement: [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).

This run's key length is certified (h_cert, every arithmetic step exact or rigorously enclosed), so the clause on a first-order run's computed h_lb does not apply to it.

The composable statement takes its authenticated classical channel from [A-AUTH](#A-AUTH), whose own text says that no composable proof for this timing-aware channel is published yet; Wegman-Carter authentication with separate keys per direction approximates it.

| Parameter | Value on this run | What it bounds |
| --- | --- | --- |
| ε | 1.86e-09 (2^-29) | the run's security parameter, ε_PA + ε_EV + 2ε_auth |
| ε_PA | 9.31e-10 (2^-30) | secrecy error: how far the key may be from uniformly random and independent of the attacker |
| ε_EV | 9.31e-10 (2^-30) | a bound on the chance that both parties accept with different keys |
| ε_auth | 0 | authentication error, counted twice in ε, including, for a key from an earlier run, its distance from an ideal key |

Completeness. On this run an honest run fails the acceptance test with probability at most 1e-06 (ε\*; [its exact value](#setup-acceptance)). The completeness figure ε\* bounds one thing only: the chance that an honest run, with no attacker and devices behaving as the declared honest model says, fails the acceptance test on its statistics. An honest run can also abort later: in error verification, when error correction leaves the two raw keys different, and in authentication. No result bounds those aborts, so an honest run's overall abort chance can exceed ε\*. Whether your error-correction code reconstructs the key on honest runs is yours to check; it affects only how often you obtain a key. Completeness never affects the security parameter ε, which holds for every abort pattern ([Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security)) and so says nothing about how often runs abort. Statement: [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope).

One execution. The security parameter ε covers one execution: one run of n rounds and its post-processing. It is not a per-round or per-bit figure, and it does not shrink when you repeat the protocol. Several executions are together secure with the sum of their ε ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)) under [A-SEPARATE](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:separate-executions). The sum does not cover parameters chosen from an earlier run's data, such as the error-correction budget or the acceptance test. The conditions of [A-SEPARATE](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:separate-executions) include: (i) their number and parameters are all fixed before the first starts; (ii) they share no key material and no device state; (iii) their keys stay unused until the last has ended. Reusing key from an earlier run to authenticate the next is not covered either. Such a key enters only through the next run's declared authentication error ε_auth, counted twice, and the earlier run's ε does not by itself bound how far that key is from an ideal one. Statement: [Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions).

[Review status](#status-legend): the lowest status of the claims below, with everything they rest on in the claim graph, is: reviewed adversarially by an AI model and accepted by the project's human owner.

- [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security), the security statement: statement and code reviewed adversarially by an AI model and accepted by the project's human owner.
- [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength), the security statement: statement and code reviewed adversarially by an AI model and accepted by the project's human owner.
- [Corollary "The first-order bound on the reference companion"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:fo-reference), on this run: statement reviewed adversarially by an AI model and accepted by the project's human owner.
- [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength), on this run: statement and code reviewed adversarially by an AI model and accepted by the project's human owner.
- [Corollary "Key length on a reference companion from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength-reference), on this run: statement reviewed adversarially by an AI model and accepted by the project's human owner.
- [Corollary "Key length from any lower bound on the value"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:keylength-bound), on this run: statement and code reviewed adversarially by an AI model and accepted by the project's human owner.
- [Lemma "Correctness from error verification"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/lem:ev-correctness), on this run: statement reviewed adversarially by an AI model and accepted by the project's human owner.

The premises [A-ALPHABET](#A-ALPHABET), [A-COIN](#A-COIN), [A-EXACT](#A-EXACT), [A-HON-ENV](#A-HON-ENV), [A-MODES](#A-MODES), [A-NOSEL](#A-NOSEL), [A-PASSIVE](#A-PASSIVE), [A-PORT](#A-PORT), [A-REACH](#A-REACH), [A-ROUND](#A-ROUND), [A-THRESH](#A-THRESH), [A-TRUST](#A-TRUST), [A-TSM](#A-TSM) and [A-VAC](#A-VAC) are not beneath the claims above in the claim graph: they enter through this run's own route, and each carries its own review status under Assumptions you vouch for. Every route theorem they reach it through (the roots of this run's assumption manifest) is accepted with everything it rests on.

### <a id="roles"></a>Roles on this run

- Neither party sends: the untrusted source delivers one system to each station. The source, its pump, timing and trigger electronics included, counts as outside every laboratory wherever it stands ([A-LAB](#A-LAB)).
- Measuring stations: Alice's station (alice_station), Bob's station (bob_station).
- Key: Alice holds it, computed from the detection results of Alice's station (alice_station).
- Public choices: gen or test, drawn at Alice's station.

Not on this run, so the parts of the premises that apply only with them do not apply here (each premise says which):

- A trusted source: the source is untrusted.
- A private setting: no station has one.
- A second letter: the declaration has one letter (x0), the per-round value a sender would prepare on Alice's side.

### <a id="vouch"></a>What you vouch for

The key length rests on the premises below, and the engine cannot check them. Each links to its statement and to what it means for this run.

| Premises of this run | Count |
| --- | --- |
| Can break security if they fail | 25 |
| Affect only completeness: how often an honest run aborts, or whether it yields a key | 1 |
| All premises of this run | 26 |

Your devices and setup (15):

- [A-MEAS](#A-MEAS): In every round each measuring party's device acts as one POVM: it emits a classical outcome, retains no quantum system, and everything after it acts on classical data. — security
- [A-TRUST](#A-TRUST): The declared instrument describes the physical receiver exactly, and the receiver is under the legitimate party's control. — security; 7 refinements: [A-EXACT](#A-EXACT) (security), [A-MODES](#A-MODES) (security), [A-NOSEL](#A-NOSEL) (security), [A-PASSIVE](#A-PASSIVE) (security), [A-PORT](#A-PORT) (security), [A-THRESH](#A-THRESH) (security), [A-VAC](#A-VAC) (security)
- [A-LAB](#A-LAB): Nothing about a party's records leaves its laboratory but its key, the public messages and, in trusted-source mode at the party of A, the emitted systems; the adversary acts on it only through what its declared measurements receive and the messages. — security
- [A-AUTH](#A-AUTH): Every classical message travels through an authentication scheme using at most k_auth bits of pre-shared key and realising the authenticated classical channel within ε_auth, a reused key's distance from an ideal one included. — security
- [A-COIN](#A-COIN): Every public choice is drawn with its declared bias; those of fixed bias are jointly independent of each other, the quantum systems and the adversary, and one weighted by a station's setting depends on the round through that setting only. — security
- [A-SEED](#A-SEED): The post-processing seeds are drawn with their declared laws, privately, independently and afresh; in trusted-source mode the source's letters and prepared systems are independent of the adversary, who never gets a purification of them. — security
- [A-HON-ENV](#A-HON-ENV): On an honest run each round's probability of each acceptance outcome, given everything before it, stays inside the declared honest envelope. — completeness only
- [A-REACH](#A-REACH): Some feasible state of the consuming declaration produces a law of the declared honest envelope, for a single declared law that law itself. — security

How the run is carried out (11):

- [A-ALPHABET](#A-ALPHABET): In every one of the n rounds of the run an acceptance value of the alphabet is recorded. — security
- [A-FIXED](#A-FIXED): The acceptance set, the round count, the key length, the transcript length, the error budgets, the authentication parameters and the Rényi order are fixed before the run and applied unchanged. — security
- [A-RHOM](#A-RHOM): The same specification, source mode and operators describe every round: the sameness clause of round homogeneity, not the absence of memory across rounds. — security; 2 refinements: [A-ROUND](#A-ROUND) (security), [A-ROUND-SQ](#A-ROUND-SQ) (security)
- [A-SEQ](#A-SEQ): Each round runs the delivery of its quantum systems, then every party's measurement, then the round's public messages, then sifting; each party measures in round order, post-processing follows all rounds and every message is public. — security
- [A-SPEC](#A-SPEC): Declared dimensions, alphabets, tables and measurements describe the apparatus: the receiver's in every round whatever the others did and, where no source certificate is demanded, Alice's of two or more letters; every input yields a key. — security
- [A-TSM](#A-TSM): Every per-round public choice of known bias at the measurement the emitted family describes, its private setting included where it has one, is a component of the emitted outcome and enters only through its statistics. — security
- [A-CONFORM](#A-CONFORM): The implementation applies the acceptance test and the verification abort, sends no message beyond the model's, outputs the model's key or nothing, uses no key before the execution ends and aborts on an authentication failure. — security
- [A-HASH](#A-HASH): Privacy amplification uses an ideal two-universal family, collision probability exactly 2^−ℓ for distinct inputs, and error verification a two-universal family. — security
- [A-KEYREG](#A-KEYREG): The post-processing acts on the raw-key string the rounds write, the declared holder computes that string, and reconciliation runs one way from the holder through a padded fixed-length transcript. — security

Where each premise applies (every premise of this run, by the laboratory or station it applies at):

| Where | Premises |
| --- | --- |
| Alice's laboratory | [A-KEYREG](#A-KEYREG), [A-LAB](#A-LAB) |
| Bob's laboratory | [A-LAB](#A-LAB) |
| Alice's station (alice_station) | [A-COIN](#A-COIN), [A-EXACT](#A-EXACT), [A-MEAS](#A-MEAS), [A-MODES](#A-MODES), [A-NOSEL](#A-NOSEL), [A-PASSIVE](#A-PASSIVE), [A-PORT](#A-PORT), [A-ROUND](#A-ROUND), [A-ROUND-SQ](#A-ROUND-SQ), [A-THRESH](#A-THRESH), [A-TRUST](#A-TRUST), [A-TSM](#A-TSM), [A-VAC](#A-VAC) |
| Bob's station (bob_station) | [A-EXACT](#A-EXACT), [A-MEAS](#A-MEAS), [A-MODES](#A-MODES), [A-NOSEL](#A-NOSEL), [A-PASSIVE](#A-PASSIVE), [A-PORT](#A-PORT), [A-ROUND](#A-ROUND), [A-ROUND-SQ](#A-ROUND-SQ), [A-THRESH](#A-THRESH), [A-TRUST](#A-TRUST), [A-VAC](#A-VAC) |
| About the protocol as a whole (both parties' equipment and software) | [A-ALPHABET](#A-ALPHABET), [A-AUTH](#A-AUTH), [A-CONFORM](#A-CONFORM), [A-FIXED](#A-FIXED), [A-HASH](#A-HASH), [A-HON-ENV](#A-HON-ENV), [A-REACH](#A-REACH), [A-RHOM](#A-RHOM), [A-SEED](#A-SEED), [A-SEQ](#A-SEQ), [A-SPEC](#A-SPEC) |

### <a id="not-counted"></a>Not counted

- A measured value with an error bar is not covered: the result applies to the exact declared values ([A-EXACT](#A-EXACT)).
- No error-correction leakage counted (λ_EC = 0). A run that sends an error-correction transcript must declare its length; with λ_EC = 0 the key length is too long for it. ([A-KEYREG](#A-KEYREG), [A-CONFORM](#A-CONFORM))
- No authentication error counted (ε_auth = 0). This holds only where the classical channel is itself authenticated, with no keyed scheme and no pre-shared key; a keyed scheme's error, a reused key's distance δ included, must be declared. ([A-AUTH](#A-AUTH))
- No authentication key consumption counted (k_auth = 0); the net key equals the key length. ([A-AUTH](#A-AUTH))
- A tiny change of the declared measurement can move the key rate by many bits per round, so the model is a premise of the rate. Where a handed reference's companion counts and the key length is formed on it, the snap only steers the search; nothing bounds model to device. ([Remark "The declared measurement as a premise of the rate"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:declared-measurement))
- What ε covers per execution, and what the completeness figure does and does not bound, are not repeated here. See [What the guarantee means](#guarantee).

### <a id="levers"></a>Choices that could lengthen the key

These are run settings that change ℓ without changing your devices or the security statement. Your device values change it too; a sweep over them shows how.

- Rényi order: the key length was computed at α = 1.05; any α in (1, 2) fixed before the run is valid and changes only the key's length, so the opt-in α search may find a longer key ([Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength)).

## <a id="setup"></a>Your QKD setup

### <a id="setup-round"></a>What a round is

A round is one use of the protocol as declared, recording its own outcomes. How a time-tagged system cuts its detection record into rounds (time bins, coincidence windows, how the stations synchronise) is yours to choose, and your declaration must describe it. Every one of the n rounds counts: where your measurement has a no-click outcome, a time bin in which nothing clicks is a round with that outcome, not one to drop.

How you cut the record into rounds bears on these premises, each in full under [Assumptions you vouch for](#assumptions):

- [A-SPEC](#A-SPEC): each round's recorded outcome is what the declared measurement gives, so a detection lost from its round or filed in another, or a no-click bin dropped, is a security matter.
- [A-EXACT](#A-EXACT): the declared efficiencies and dark-count probabilities are the true values for the rounds as you cut them.
- [A-MODES](#A-MODES): no light outside the declared temporal modes (outside a window, say) reaches a detector.
- [A-PORT](#A-PORT): a click probability that depends on the temporal mode (efficiency mismatch) is declared as mode-dependent loss.
- [A-THRESH](#A-THRESH): threshold detectors read once per gate, with no dead time, afterpulsing or timing jitter.
- [A-RHOM](#A-RHOM): one declaration covers every round.
- [A-ROUND](#A-ROUND): the same receiver behaviour in every round and no memory across rounds, such as dead time or afterpulsing across a boundary.
- [A-SEQ](#A-SEQ): the declared order of measurements and messages within a round, and each measuring party completing one round's measurement before the next round's.
- [A-LAB](#A-LAB): no timing or synchronisation signal reveals a party's records, and only the declared inputs influence a measurement, not a clock or trigger line from the untrusted source.
- [A-FIXED](#A-FIXED): the number of rounds and the acceptance test are fixed before the run.
- [A-ALPHABET](#A-ALPHABET): all n rounds are in the record (the acceptance test is evaluated on all n rounds); a measured round missing from it, a lost time tag or no-click bin included, leaves the counts wrong and is a security matter under [A-SPEC](#A-SPEC) and [A-CONFORM](#A-CONFORM).

### <a id="setup-protocol"></a>Protocol

1. Rounds: The protocol runs n = 100,000,000 rounds. See [What a round is](#setup-round) above. Record: [record](record.md#p-.payload.config.rounds).
2. Source: In every round the untrusted source delivers one system to each station; see Source below. Record: [record](record.md#p-.payload.compiled.source).
3. Measurement: Each round is measured at Alice's station (element-graph) and Bob's station (element-graph); see the stations below. Record: [record](record.md#p-.payload.stages.stations).
4. Public choice (test coin): At Alice's station, a public choice is drawn: gen with probability 0.875, test with probability 0.125. The test fraction is 0.125. Record: [record](record.md#p-.payload.compiled.public.choice_weightings.0).
5. Announcements: First Alice announces one of gen:Z, gen:X, gen:nc, gen:mc, test:nc, test:H, test:V, test:D, test:A, test:mc; then Bob announces one of Z, X, nc, mc, H, V, D, A. Record: [record](record.md#p-.payload.compiled.public.transcript).
6. Sifting and key map: A round gives a raw key bit when its announcements pass sifting: 8 of the 72 combinations of readouts map to a key bit, the rest are discarded. Alice holds the key over the alphabet 0, 1. Key bases: ZX. Record: [record](record.md#p-.payload.compiled.public.key_map).
7. Acceptance test: The parties estimate the acceptance statistics on the whole run and abort unless they pass; see Acceptance test below. Record: [record](record.md#p-.payload.stages.acceptance_construction).
8. Error correction: One-way error correction; its transcript leaks λ_EC = 0 bits, which the key length deducts. Record: [record](record.md#p-.payload.config.parameters.lambda_ec).
9. Error verification: The parties compare a hash of the corrected keys (failure probability ε_EV = 9.31323e-10); the key length deducts 30 bits for it. Record: [record](record.md#p-.payload.stages.key_rate.deductions.error_verification).
10. Privacy amplification: A two-universal hash shortens the corrected key to ℓ = 40,192,819 bits, secret except with probability ε_PA = 9.31323e-10. Record: [record](record.md#p-.payload.stages.key_rate.key_length).

### <a id="setup-source"></a>Source

The security analysis does not trust the source. Its model (ideal_pair) only predicts the statistics an honest run is expected to show; those set the acceptance test, and nothing in the key length's security rests on the model being right. The declaration's letter is the one placeholder x0: Alice draws no letter, and the data of a round are the stations' readouts.

| Field | Value |
| --- | --- |
| Source mode | untrusted |
| Trusted | false |
| Honest model | ideal_pair |
| Honest model: [alice_transmittance](#g-param-model-alice-transmittance) | 1 |
| Honest model: [bob_transmittance](#g-param-model-bob-transmittance) | 1 |
| Honest model: [mean_pairs](#g-param-model-mean-pairs) | 0.03125; has no effect under the declared values: it applies only where source_model is spdc |
| Honest model: [visibility](#g-param-model-visibility) | 1 |
| How the honest model is derived | [instances/common/honest/pair_models.md](../../../instances/common/honest/pair_models.md) |
| Status | honest-data model; no source security attestation |
| Record | [record](record.md#p-.payload.compiled.source) |

### <a id="station-alice_station"></a>Alice's station

| Field | Value |
| --- | --- |
| Party | A |
| Station | alice_station |
| Input route | element graph: the engine compiled the measurement from the declared optical elements and detectors |
| Channel modes | Z_H, Z_V |
| Photon cutoff N | 1 |
| Exact window | 2 |
| Record | [record](record.md#p-.payload.stages.stations.0) |
| Statement | [Definition "Compilation of a declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:compile) |

#### Outcome alphabet

| Letter | Meaning | Click patterns |
| --- | --- | --- |
| `nc` | no detector clicked | {} |
| `H` | only detector H clicked; basis Z, bit 0 | {H} |
| `V` | only detector V clicked; basis Z, bit 1 | {V} |
| `D` | only detector D clicked; basis X, bit 0 | {D} |
| `A` | only detector A clicked; basis X, bit 1 | {A} |
| `mc` | more than one detector clicked (any of 11 click patterns) | {H, V}; {H, D}; {H, A}; {V, D}; {V, A}; {D, A}; {H, V, D}; {H, V, A}; {H, D, A}; {V, D, A}; {H, V, D, A} |

#### Optical elements

| Element | What it is |
| --- | --- |
| `bs` | beamsplitter, transmittance 0.5 (50:50) (a photon from path Z stays in path Z with probability 0.5 and otherwise moves to path X), on modes Z_H, Z_V, X_H, X_V |
| `hwp` | half-wave plate at angle π/8 = 22.5°, in the X arm (modes X_H, X_V) |
| `pbs_z` | polarising beamsplitter, transmits H and reflects V (H stays in path Z, V is reflected into path Zr), on modes Z_H, Z_V, Zr_H, Zr_V |
| `pbs_x` | polarising beamsplitter, transmits H and reflects V (H stays in path X, V is reflected into path Xr), on modes X_H, X_V, Xr_H, Xr_V |

Order of the elements (light passes the first before the second): bs → hwp, bs → pbs_z, hwp → pbs_x.

#### Detectors

| Port | Collects modes | dark-click probability per round | efficiency |
| --- | --- | --- | --- |
| `H` | Z_H, Z_V | 0 | 1 |
| `V` | Zr_H, Zr_V | 0 | 1 |
| `D` | X_H, X_V | 0 | 1 |
| `A` | Xr_H, Xr_V | 0 | 1 |

This station has no probe: its one setting is off, the probe setting with no probe light ([Definition "Probe declaration"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:probe)), so the measurement below is the station's only one.

Mode names are the instance's labels, a path and a polarisation: Xr_V is V-polarised light in path Xr. The instance's own description is in [instances/bbm92/README.md](../../../instances/bbm92/README.md).

Why these tables are shown: they are the measurement the key length is computed for, which [A-EXACT](#A-EXACT) and [A-SPEC](#A-SPEC) ask you to vouch for as your receiver's. What to check: that the 1-photon operators agree with your detectors' efficiencies and the splitting ratios above, and that the table with dark counts agrees with your dark-count probability.

The measurement appears below in 3 forms: per photon number, the receiver's measurement as declared, before dark counts; the same with the declared dark counts composed in; and the squashed target POVM, the finite model the proof analyses in place of the device ([Corollary "Exact emission of the flat instance"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/wpfss/cor:emitted-flat)).

#### POVM per photon number

One operator per outcome on each photon-number block of the channel modes, before dark counts: the measurement the receiver applies to a pulse of that many photons. Statement: [Definition "Compilation of a declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:compile).

| Outcome | 0 photons (vacuum) |
| --- | --- |
| nc | 1 |
| H | 0 |
| V | 0 |
| D | 0 |
| A | 0 |
| mc | 0 |

1 photon. Basis in the record's order, occupation numbers over the channel modes (Z_H, Z_V): 1. one photon in mode Z_V (0, 1); 2. one photon in mode Z_H (1, 0). Record: [record](record.md#p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.blocks.1).

*Outcome nc*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

*Outcome H*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 0.5 |

*Outcome V*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0.5 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

*Outcome D*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0.25 | 0.25 |
| **one photon in mode Z_H** | 0.25 | 0.25 |

*Outcome A*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0.25 | -0.25 |
| **one photon in mode Z_H** | -0.25 | 0.25 |

*Outcome mc*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

Entries below 1e-12 of the block's largest are floating-point residue and shown as 0; the unrounded values are in the record excerpt.

#### POVM with dark counts

The same blocks with the detectors' dark counts composed in: what a pulse of that many photons produces including dark clicks.

| Outcome | 0 photons (vacuum) |
| --- | --- |
| nc | 1 |
| H | 0 |
| V | 0 |
| D | 0 |
| A | 0 |
| mc | 0 |

1 photon. Basis in the record's order, occupation numbers over the channel modes (Z_H, Z_V): 1. one photon in mode Z_V (0, 1); 2. one photon in mode Z_H (1, 0). Record: [record](record.md#p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.dark_composed.1).

*Outcome nc*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

*Outcome H*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 0.5 |

*Outcome V*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0.5 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

*Outcome D*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0.25 | 0.25 |
| **one photon in mode Z_H** | 0.25 | 0.25 |

*Outcome A*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0.25 | -0.25 |
| **one photon in mode Z_H** | -0.25 | 0.25 |

*Outcome mc*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

Entries below 1e-12 of the block's largest are floating-point residue and shown as 0; the unrounded values are in the record excerpt.

#### Squashed target POVM

The finite-dimensional model the security proof works with: the reduction maps the receiver's measurement onto it, and proves that analysing it is enough. One block per photon number up to the cutoff, then one flag per outcome. Statement: [Corollary "Exact emission of the flat instance"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/wpfss/cor:emitted-flat).

| Outcome | 0 photons (vacuum) | flag nc | flag H | flag V | flag D | flag A | flag mc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nc | 1 | ≈ 0.5 (549755813889/1099511627776) | 0 | 0 | 0 | 0 | 0 |
| H | 0 | 0 | ≈ 0.5 (549755813889/1099511627776) | 0 | 0 | 0 | 0 |
| V | 0 | 0 | 0 | ≈ 0.5 (549755813889/1099511627776) | 0 | 0 | 0 |
| D | 0 | 0 | 0 | 0 | ≈ 0.5 (549755813889/1099511627776) | 0 | 0 |
| A | 0 | 0 | 0 | 0 | 0 | ≈ 0.5 (549755813889/1099511627776) | 0 |
| mc | 0 | ≈ 0.5 (549755813887/1099511627776) | ≈ 0.5 (549755813887/1099511627776) | ≈ 0.5 (549755813887/1099511627776) | ≈ 0.5 (549755813887/1099511627776) | ≈ 0.5 (549755813887/1099511627776) | 1 |

1 photon. Basis in the record's order, occupation numbers over the channel modes (Z_H, Z_V): 1. one photon in mode Z_V (0, 1); 2. one photon in mode Z_H (1, 0). Record: [record](record.md#p-.payload.stages.stations.0.reduction.target_povm).

*Outcome nc*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

*Outcome H*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 1/2 |

*Outcome V*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 1/2 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

*Outcome D*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 1/4 | 1/4 |
| **one photon in mode Z_H** | 1/4 | 1/4 |

*Outcome A*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 1/4 | -1/4 |
| **one photon in mode Z_H** | -1/4 | 1/4 |

*Outcome mc*

|   | one photon in mode Z_V | one photon in mode Z_H |
| --- | --- | --- |
| **one photon in mode Z_V** | 0 | 0 |
| **one photon in mode Z_H** | 0 | 0 |

### <a id="station-bob_station"></a>Bob's station

| Field | Value |
| --- | --- |
| Party | B |
| Station | bob_station |
| Record | [record](record.md#p-.payload.stages.stations.1) |

Identical to [Alice's station](#station-alice_station): the same input route, outcome alphabet, optical elements, detectors and measurement, read from this station's own record.

### <a id="setup-acceptance"></a>Acceptance test

The run records one acceptance value per round, from 79 outcomes, and accepts only if the observed frequency of every outcome lies in the box of intervals built around the honest model's probabilities (endpoint rule bernstein). An honest run fails it with probability at most 1e-06 (ε\*), within your completeness budget of 1e-06 (the completeness parameter ε_comp you allow). The table of acceptance categories below gives, for each outcome, the honest model's probability and the interval its observed frequency must lie in, ends included, and the counts that interval admits out of the rounds of the run: a run whose count of any outcome falls outside its range is not accepted ([Definition "The construction map"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/def:construction)). 64 of the 79 outcomes admit a count of exactly 0: a single round with any of them fails the acceptance test, and your implementation must abort the run ([A-CONFORM](#A-CONFORM)). In an acceptance value written with a bar, Alice's announcement stands before the bar and Bob's after it. Statement: [Theorem "The completeness bound"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/thm:completeness-bound).

| Field | Value |
| --- | --- |
| Acceptance categories | 79 |
| Outcomes the honest model gives positive probability | 15 |
| Endpoint rule | bernstein |
| Geometry | PolytopeGeometry |
| Completeness budget | 1e-06 |
| Certified completeness ε\* | 1e-06 |
| Record | [record](record.md#p-.payload.stages.acceptance_construction) |

| Acceptance category | Honest probability | Allowed frequency | Allowed count |
| --- | --- | --- | --- |
| gen | 0.4375 | 0.437195 to 0.437805 | 43,719,511 to 43,780,489 of 100,000,000 |
| gen:Z\|X | 0.21875 | 0.218496 to 0.219004 | 21,849,591 to 21,900,409 of 100,000,000 |
| gen:Z\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:Z\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:Z\|H | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:Z\|V | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:Z\|D | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:Z\|A | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:X\|Z | 0.21875 | 0.218496 to 0.219004 | 21,849,591 to 21,900,409 of 100,000,000 |
| gen:X\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:X\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:X\|H | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:X\|V | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:X\|D | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:X\|A | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:nc\|Z | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:nc\|X | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:nc\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:nc\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:nc\|H | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:nc\|V | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:nc\|D | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:nc\|A | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:mc\|Z | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:mc\|X | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:mc\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:mc\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:mc\|H | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:mc\|V | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:mc\|D | 0 | exactly 0 | exactly 0 of 100,000,000 |
| gen:mc\|A | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:nc\|Z | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:nc\|X | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:nc\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:nc\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:nc\|H | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:nc\|V | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:nc\|D | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:nc\|A | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:H\|Z | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:H\|X | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:H\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:H\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:H\|H | 0.015625 | 0.0155487 to 0.0157013 | 1,554,873 to 1,570,127 of 100,000,000 |
| test:H\|V | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:H\|D | 0.0078125 | 0.00775833 to 0.00786667 | 775,833 to 786,667 of 100,000,000 |
| test:H\|A | 0.0078125 | 0.00775833 to 0.00786667 | 775,833 to 786,667 of 100,000,000 |
| test:V\|Z | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:V\|X | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:V\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:V\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:V\|H | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:V\|V | 0.015625 | 0.0155487 to 0.0157013 | 1,554,873 to 1,570,127 of 100,000,000 |
| test:V\|D | 0.0078125 | 0.00775833 to 0.00786667 | 775,833 to 786,667 of 100,000,000 |
| test:V\|A | 0.0078125 | 0.00775833 to 0.00786667 | 775,833 to 786,667 of 100,000,000 |
| test:D\|Z | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:D\|X | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:D\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:D\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:D\|H | 0.0078125 | 0.00775833 to 0.00786667 | 775,833 to 786,667 of 100,000,000 |
| test:D\|V | 0.0078125 | 0.00775833 to 0.00786667 | 775,833 to 786,667 of 100,000,000 |
| test:D\|D | 0.015625 | 0.0155487 to 0.0157013 | 1,554,873 to 1,570,127 of 100,000,000 |
| test:D\|A | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:A\|Z | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:A\|X | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:A\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:A\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:A\|H | 0.0078125 | 0.00775833 to 0.00786667 | 775,833 to 786,667 of 100,000,000 |
| test:A\|V | 0.0078125 | 0.00775833 to 0.00786667 | 775,833 to 786,667 of 100,000,000 |
| test:A\|D | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:A\|A | 0.015625 | 0.0155487 to 0.0157013 | 1,554,873 to 1,570,127 of 100,000,000 |
| test:mc\|Z | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:mc\|X | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:mc\|nc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:mc\|mc | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:mc\|H | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:mc\|V | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:mc\|D | 0 | exactly 0 | exactly 0 of 100,000,000 |
| test:mc\|A | 0 | exactly 0 | exactly 0 of 100,000,000 |

### <a id="setup-expected"></a>Expected statistics of the honest model

These statistics are expected from the honest model ideal_pair, evaluated with its parameters at their ideal values (transmittance 1, visibility 1), as your declared stations record them (with their detector efficiencies, dark counts and settings; see the stations above).

| Statistic | Value | How it is computed | Record |
| --- | --- | --- | --- |
| Probability that a round gives a raw key bit | 0.4375 | The sum of the honest raw joint distribution over every combination of readouts the compiled key map sends to a key bit. | [record](record.md#p-.payload.stages.acceptance_construction.raw_joint_distribution) |
| Expected QBER, key rounds Alice announces gen:Z | 0 | Among these key rounds of the honest raw joint distribution, the probability that Alice's key bit differs from the bit the other party most likely holds given their own readout. | [record](record.md#p-.payload.stages.acceptance_construction.raw_joint_distribution) |
| Expected QBER, key rounds Alice announces gen:X | 0 | Among these key rounds of the honest raw joint distribution, the probability that Alice's key bit differs from the bit the other party most likely holds given their own readout. | [record](record.md#p-.payload.stages.acceptance_construction.raw_joint_distribution) |
| Detection probability at Alice's station | 1 | The honest probability that at least one detector of the station clicks: the sum of the raw joint distribution over every readout whose letter is not nc. | [record](record.md#p-.payload.stages.acceptance_construction.raw_joint_distribution) |
| Detection probability at Bob's station | 1 | The honest probability that at least one detector of the station clicks: the sum of the raw joint distribution over every readout whose letter is not nc. | [record](record.md#p-.payload.stages.acceptance_construction.raw_joint_distribution) |

## <a id="inputs"></a>Your inputs

Every value the run was computed for, in three tables: your devices and the channel, the budgets (the ε you choose), and the engine's settings. A value shows its default where it differs from it.

### <a id="inputs-device"></a>Device and channel

[A-EXACT](#A-EXACT) asks you to vouch that every number you declared for a receiver component (each efficiency, dark-count probability, probe mean photon number and other component parameter) is the device's true value, not an estimate with an error bar. It applies to every such value, whether or not the Premises column names it there: the column names it only beside the values the report could tie to a receiver.

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-model.alice_transmittance"></a>Alice's transmittance ([`model.alice_transmittance`](record.md#p-.payload.config.model.alice_transmittance)) | 1 | — | Probability that Alice's photon of a pair reaches her station | — |
| <a id="input-model.bob_transmittance"></a>Bob's transmittance ([`model.bob_transmittance`](record.md#p-.payload.config.model.bob_transmittance)) | 1 | — | Probability that Bob's photon of a pair reaches his station | — |
| <a id="input-model.mean_pairs"></a>Mean pairs ([`model.mean_pairs`](record.md#p-.payload.config.model.mean_pairs)) | 0.03125; has no effect under the declared values: it applies only where source_model is spdc | — | Mean number of photon pairs the SPDC source emits per round, summed over both polarizations | — |
| <a id="input-model.visibility"></a>Visibility ([`model.visibility`](record.md#p-.payload.config.model.visibility)) | 1 | — | Visibility v of the entangled pair: matched-basis bits disagree with probability (1 - v)/2 | — |
| <a id="input-device.acceptance_map"></a>Acceptance map ([`device.acceptance_map`](record.md#p-.payload.config.device.acceptance_map)) | pair-resolved | — | How finely the public announcements are grouped into the statistics the protocol checks; a key round is always one value | — |
| <a id="input-device.alice_basis_split"></a>Alice's basis split ([`device.alice_basis_split`](record.md#p-.payload.config.device.alice_basis_split)) | 0.5 | — | Transmittance of Alice's basis beamsplitter, which is the probability that a photon is measured in the Z basis | [A-EXACT](#A-EXACT) |
| <a id="input-device.alice_dark_count"></a>Alice's dark count ([`device.alice_dark_count`](record.md#p-.payload.config.device.alice_dark_count)) | 0 (each of A, D, H, V) | — | Dark-click probability per round of each of Alice's four detectors | [A-EXACT](#A-EXACT) |
| <a id="input-device.alice_efficiency"></a>Alice's efficiency ([`device.alice_efficiency`](record.md#p-.payload.config.device.alice_efficiency)) | 1 (each of A, D, H, V) | — | Detection efficiency of each of Alice's four detectors | [A-EXACT](#A-EXACT) |
| <a id="input-device.alice_exact_window"></a>Alice's exact window ([`device.alice_exact_window`](record.md#p-.payload.config.device.alice_exact_window)) | 2 | — | Exact-window depth m\* of Alice's station: photon numbers N+1 to m\* are evaluated exactly when bounding the high-photon part; must exceed N, and empty leaves only the analytic bound | — |
| <a id="input-device.alice_half_wave_angle"></a>Alice's half wave angle ([`device.alice_half_wave_angle`](record.md#p-.payload.config.device.alice_half_wave_angle)) | 0.125 | pi | Angle of the half-wave plate in Alice's X arm, in units of pi; 1/8 (22.5 degrees) measures the diagonal basis | [A-EXACT](#A-EXACT) |
| <a id="input-device.alice_pbs_leak_reflected"></a>Alice's PBS leak reflected ([`device.alice_pbs_leak_reflected`](record.md#p-.payload.config.device.alice_pbs_leak_reflected)) | 0 | — | Fraction of the horizontal polarization each of Alice's polarizing beamsplitters reflects instead of transmitting; it clicks the reflected-path detector (V, or A behind the plate), which watches both polarizations of its path; 0 is perfect separation, 1/2 is none | [A-EXACT](#A-EXACT) |
| <a id="input-device.alice_pbs_leak_transmitted"></a>Alice's PBS leak transmitted ([`device.alice_pbs_leak_transmitted`](record.md#p-.payload.config.device.alice_pbs_leak_transmitted)) | 0 | — | Fraction of the vertical polarization each of Alice's polarizing beamsplitters transmits instead of reflecting; it clicks the transmitted-path detector (H, or D behind the plate), which watches both polarizations of its path; 0 is perfect separation, 1/2 is none | [A-EXACT](#A-EXACT) |
| <a id="input-device.alice_photon_cutoff"></a>Alice's photon cutoff ([`device.alice_photon_cutoff`](record.md#p-.payload.config.device.alice_photon_cutoff)) | 1 | — | Photon cutoff N of Alice's station: photon numbers up to N are modelled exactly and higher ones are bounded | — |
| <a id="input-device.bob_basis_split"></a>Bob's basis split ([`device.bob_basis_split`](record.md#p-.payload.config.device.bob_basis_split)) | 0.5 | — | Transmittance of Bob's basis beamsplitter, which is the probability that a photon is measured in the Z basis | [A-EXACT](#A-EXACT) |
| <a id="input-device.bob_dark_count"></a>Bob's dark count ([`device.bob_dark_count`](record.md#p-.payload.config.device.bob_dark_count)) | 0 (each of A, D, H, V) | — | Dark-click probability per round of each of Bob's four detectors | [A-EXACT](#A-EXACT) |
| <a id="input-device.bob_efficiency"></a>Bob's efficiency ([`device.bob_efficiency`](record.md#p-.payload.config.device.bob_efficiency)) | 1 (each of A, D, H, V) | — | Detection efficiency of each of Bob's four detectors | [A-EXACT](#A-EXACT) |
| <a id="input-device.bob_exact_window"></a>Bob's exact window ([`device.bob_exact_window`](record.md#p-.payload.config.device.bob_exact_window)) | 2 | — | Exact-window depth m\* of Bob's station: photon numbers N+1 to m\* are evaluated exactly when bounding the high-photon part; must exceed N, and empty leaves only the analytic bound | — |
| <a id="input-device.bob_half_wave_angle"></a>Bob's half wave angle ([`device.bob_half_wave_angle`](record.md#p-.payload.config.device.bob_half_wave_angle)) | 0.125 | pi | Angle of the half-wave plate in Bob's X arm, in units of pi; 1/8 (22.5 degrees) measures the diagonal basis | [A-EXACT](#A-EXACT) |
| <a id="input-device.bob_pbs_leak_reflected"></a>Bob's PBS leak reflected ([`device.bob_pbs_leak_reflected`](record.md#p-.payload.config.device.bob_pbs_leak_reflected)) | 0 | — | Fraction of the horizontal polarization each of Bob's polarizing beamsplitters reflects instead of transmitting; it clicks the reflected-path detector (V, or A behind the plate), which watches both polarizations of its path; 0 is perfect separation, 1/2 is none | [A-EXACT](#A-EXACT) |
| <a id="input-device.bob_pbs_leak_transmitted"></a>Bob's PBS leak transmitted ([`device.bob_pbs_leak_transmitted`](record.md#p-.payload.config.device.bob_pbs_leak_transmitted)) | 0 | — | Fraction of the vertical polarization each of Bob's polarizing beamsplitters transmits instead of reflecting; it clicks the transmitted-path detector (H, or D behind the plate), which watches both polarizations of its path; 0 is perfect separation, 1/2 is none | [A-EXACT](#A-EXACT) |
| <a id="input-device.bob_photon_cutoff"></a>Bob's photon cutoff ([`device.bob_photon_cutoff`](record.md#p-.payload.config.device.bob_photon_cutoff)) | 1 | — | Photon cutoff N of Bob's station: photon numbers up to N are modelled exactly and higher ones are bounded | — |
| <a id="input-device.key_bases"></a>Key bases ([`device.key_bases`](record.md#p-.payload.config.device.key_bases)) | ZX | — | Which matched bases of a generation round give key; with Z, matched-X generation rounds are discarded. Independent of the test coin | — |
| <a id="input-device.party_local_view"></a>Party local view ([`device.party_local_view`](record.md#p-.payload.config.device.party_local_view)) | operator; has no effect under the declared values: it applies only where route is licensed or licensed+two-sector | — | How each station's multi-click constraints enter the analysis on a licensed route | — |
| <a id="input-device.route"></a>Route ([`device.route`](record.md#p-.payload.config.device.route)) | encoded | — | Photon-number reduction applied to each station, mapping any number of incoming photons to a finite system | — |
| <a id="input-device.source_model"></a>Source model ([`device.source_model`](record.md#p-.payload.config.device.source_model)) | ideal_pair | — | Model of the source that predicts the expected data; the security analysis never trusts the source | — |
| <a id="input-device.test_fraction"></a>Test fraction ([`device.test_fraction`](record.md#p-.payload.config.device.test_fraction)) | 0.125 | — | Probability that Alice's public coin makes a round a test round, in which both parties announce their full outcome | — |
| <a id="input-device.alice_efficiency_normalization"></a>Alice's efficiency normalization ([`device.alice_efficiency_normalization`](record.md#p-.payload.instance.parameters.18.default)) | — | — | Factored loss t of Alice's station: her detector efficiencies are divided by t and the common loss t is moved into the channel, which leaves the observed statistics unchanged; between her largest efficiency and 1, where 1 turns it off, and empty uses her largest efficiency divided by 99/100, or 1 where that efficiency is at least 99/100 | — |
| <a id="input-device.bob_efficiency_normalization"></a>Bob's efficiency normalization ([`device.bob_efficiency_normalization`](record.md#p-.payload.instance.parameters.27.default)) | — | — | Factored loss t of Bob's station: his detector efficiencies are divided by t and the common loss t is moved into the channel, which leaves the observed statistics unchanged; between his largest efficiency and 1, where 1 turns it off, and empty uses his largest efficiency divided by 99/100, or 1 where that efficiency is at least 99/100 | — |

### <a id="inputs-budget"></a>Budgets (the ε you choose)

A budget is an error probability (an ε) you choose before the run. ε_PA, ε_EV and ε_auth make up the security parameter ε = ε_PA + ε_EV + 2ε_auth. The completeness budget ε_comp is not part of ε: it bounds only how often an honest run fails the acceptance test. The table also holds the round count and the other inputs of the key length.

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-rounds"></a>Rounds n ([`rounds`](record.md#p-.payload.config.rounds)) | 100000000 | — | the number of rounds (n), total channel uses; the same n reaches the acceptance construction and the declaration ([Requirement "Alphabet and round count taken from the consuming declaration"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/req:matched-alphabet)) | [A-ALPHABET](#A-ALPHABET), [A-FIXED](#A-FIXED), [A-HON-ENV](#A-HON-ENV), [A-RHOM](#A-RHOM), [A-SEQ](#A-SEQ) |
| <a id="input-completeness_budget"></a>Completeness budget ([`completeness_budget`](record.md#p-.payload.config.completeness_budget)) | 1e-06 | — | the completeness budget (eps_comp) of the acceptance construction; it buys completeness and never soundness | — |
| <a id="input-parameters.alpha"></a>Rényi order α (declared) ([`parameters.alpha`](record.md#p-.payload.config.parameters.alpha)) | 1.05 | — | the Renyi order (alpha) of the declaration; every key-length statement requires alpha in (1, 2) ([Requirement "Rényi order of a reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:key-length-alpha-domain)) | — |
| <a id="input-parameters.eps_pa"></a>Secrecy error ε_PA ([`parameters.eps_pa`](record.md#p-.payload.config.parameters.eps_pa)) | 9.31e-10 (2^-30) | — | the privacy-amplification (secrecy) budget of the key-length expression; eps_pa + eps_ev + 2 eps_auth &lt; 1 ([Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous)) | [A-FIXED](#A-FIXED) |
| <a id="input-parameters.eps_ev"></a>Error-verification error ε_EV ([`parameters.eps_ev`](record.md#p-.payload.config.parameters.eps_ev)) | 9.31e-10 (2^-30) | — | the error-verification (correctness) budget; eps_pa + eps_ev + 2 eps_auth &lt; 1 ([Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous)) | [A-FIXED](#A-FIXED) |
| <a id="input-parameters.lambda_ec"></a>Error-correction leakage λ_EC ([`parameters.lambda_ec`](record.md#p-.payload.config.parameters.lambda_ec)) | 0 | bit | the error-correction transcript length in bits, total and not per round: a fixed-length register of that many bits ([Assumption "Dedicated key register and one-way reconciliation"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:keyreg)) How λ_EC was chosen: declared by you (no estimate sits beside the record). | [A-CONFORM](#A-CONFORM), [A-FIXED](#A-FIXED), [A-KEYREG](#A-KEYREG) |
| <a id="input-parameters.eps_auth"></a>Authentication error ε_auth ([`parameters.eps_auth`](record.md#p-.payload.config.parameters.eps_auth)) | 0.0 | — | authentication error bound: the scheme's error on an ideal key plus the key's trace distance delta from an ideal key; delta = 0 for a fresh key, and for a key from an earlier run a distance you bound and declare ([Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth)). It enters the security parameter twice and never the key length | [A-AUTH](#A-AUTH), [A-FIXED](#A-FIXED) |
| <a id="input-parameters.k_auth"></a>Authentication key bits k_auth ([`parameters.k_auth`](record.md#p-.payload.config.parameters.k_auth)) | 0 | bit | the pre-shared key bits the authentication scheme consumes in one run ([Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth) (ii)); the net key is the key length minus k_auth | [A-AUTH](#A-AUTH), [A-FIXED](#A-FIXED) |
| <a id="input-alpha"></a>Rényi order α (configured) ([`alpha`](record.md#p-.payload.config.alpha)) | — | — | the Renyi order the run solves at; unset, the run solves at parameters.alpha, or lets alpha_search choose it where that is set (never both) | — |

### <a id="inputs-engine"></a>Engine settings

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-declared_tolerance"></a>Declared tolerance τ ([`declared_tolerance`](record.md#p-.payload.config.declared_tolerance)) | 1e-12 | — | the ceiling (tau) on the pre-snap defect the instance may repair ([spec/architecture.md](../../../spec/architecture.md) 2.8); required, with no default, and told to no module | — |
| <a id="input-parameters.reference_enclosure"></a>Reference enclosure ([`parameters.reference_enclosure`](record.md#p-.payload.config.parameters.reference_enclosure)) | true | — | whether the instance hands beside its snap of its receiver measurement the blocks of the reference known through rigorous rational enclosures ([Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference) (i)); off, only the blocks known exactly are handed, and the reference companion carries the snapped block on every other moved block, which then rests on A-SNAP in the group no_usable_reference (cause enclosure_not_used) | — |
| <a id="input-parameters.strict_snaps"></a>Strict option ([`parameters.strict_snaps`](record.md#p-.payload.config.parameters.strict_snaps)) | false | — | the strict option: whether the run refuses wherever a moved block of a measurement snap or a moved class of the emission would rest on A-SNAP, rather than disclosing it, and reports no key length that rests on it ([Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference) (iv)) | — |
| <a id="input-parameters.statistics_check"></a>Statistics check ([`parameters.statistics_check`](record.md#p-.payload.config.parameters.statistics_check)) | on (not run: the statistics are your honest model's predictions and you declared no constraint entry) | — | the check of the acceptance set against the statistics the declared model can produce ([Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set)): once per run it bounds the mismatch from below and caps the probability that devices behaving as declared pass the acceptance test | — |
| <a id="input-parameters.min_model_pass_probability"></a>Minimum model pass probability τ ([`parameters.min_model_pass_probability`](record.md#p-.payload.config.parameters.min_model_pass_probability)) | 0.5 | — | the smallest probability (tau) with which devices behaving as declared must be able to pass the acceptance test: a checked run whose proven cap on that probability is at most tau is refused as a whole, with no key length ([Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set) (iv)) | — |
| <a id="input-constrained"></a>Constrained solve ([`constrained`](record.md#p-.payload.config.constrained)) | — | — | which acceptance outcomes the acceptance set constrains; unset, every outcome is constrained, and an empty list is a selector in its own right | — |
| <a id="input-endpoint_rule"></a>Endpoint rule ([`endpoint_rule`](record.md#p-.payload.config.endpoint_rule)) | bernstein; default exact | — | statistics' endpoint rule for the acceptance box | — |
| <a id="input-tail_evaluation"></a>Tail evaluation ([`tail_evaluation`](record.md#p-.payload.config.tail_evaluation)) | sweep | — | how statistics decides a tail comparison; it never changes what is decided | — |
| <a id="input-solver.max_iterations"></a>Solver step limit ([`solver.max_iterations`](record.md#p-.payload.config.solver.max_iterations)) | 10 | — | a method-native work cap (under auto, of the Frank-Wolfe stages only); unset, the solver's own is taken | — |
| <a id="input-solver.method"></a>Solver method ([`solver.method`](record.md#p-.payload.config.solver.method)) | fw | — | the candidate search method; unset, auto is taken | — |

## <a id="assumptions"></a>Assumptions you vouch for

### <a id="premises-devices"></a>Premises about your devices and setup

The engine does not verify these premises; a run that rests on one records it as unverified. Where a premise's own text says the engine checks a part of it (its inputs, say), that part is checked and the rest is yours; a premise whose verification differs says so under it.

#### <a id="category-laboratory"></a>Your laboratories

Premises about each party's laboratory as a whole, whatever the party does in the protocol (send, measure, or both): that nothing about its records leaks out and nothing reaches in except what the protocol declares. Evidence for them comes from side-channel testing of each laboratory: back-reflections into a source where the party sends, detector back-flash where it measures, electromagnetic and power emanations, and timing.

##### <a id="A-LAB"></a>A-LAB: Each party's laboratory is sealed

| Field | Value |
| --- | --- |
| About | Alice's laboratory (station alice_station) and Bob's laboratory (station bob_station) |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Nothing about a party's records leaves its laboratory but its key, the public messages and, in trusted-source mode at the party of A, the emitted systems; the adversary acts on it only through what its declared measurements receive and the messages. It excludes side channels at both parties. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Each party's laboratory is sealed"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:lab) |
| Category | laboratory |
| Machine key | `laboratory_sealed` |
| Emitted by | `meat-core@partyA`, `meat-core@partyB` |

Whatever a party's role, nothing about its letters, settings, choices, detection results, keys or random numbers leaves its laboratory but the final key, the public messages and, where the party sends with a trusted source, the signals that source emits; timing and auxiliary signals reveal no more. An untrusted source counts as outside every laboratory, even one it is in. The attacker reaches a laboratory only via the systems its declared measurements receive and the public messages. Light sent in to read out a letter, a setting, a choice or a detector state (a Trojan-horse attack, at a receiver as at a modulator), emanations from any device, detector back-flash and anything but the declared input modes influencing a measurement violate this, a clock or trigger line from an untrusted source included; where it sends with a trusted source, so does light seeding or recalibrating its laser.

Not on this run: the clauses about a trusted source in the party's laboratory (the signals it emits, light seeding or recalibrating its laser), since the source is untrusted and counts as outside every laboratory.

Light sent into a laboratory to read out a letter, a setting, a choice or a detector state (a Trojan-horse attack, at a receiver as at a modulator) still violates this premise on this run.

For this run:

- laboratory: Alice's (party A)
- laboratory: Bob's (party B)
- source_mode: untrusted
- party_partition: system A: party A (Alice); measured stations: alice_station (Alice), bob_station (Bob)

#### <a id="category-receiver"></a>Your receivers

Premises about the measuring stations, whichever party each belongs to. Evidence for them comes from characterising each receiver as built: detector efficiencies and dark counts, the optical elements and the modes they act on, and tests against detector-control attacks such as bright-light blinding.

##### <a id="A-MEAS"></a>A-MEAS: Each measuring party's device as one POVM per round

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | In every round each measuring party's device acts as one POVM: it emits a classical outcome, retains no quantum system, and everything after it acts on classical data. It is the hypothesis about the devices behind the output-state equality of the physical and the squashed protocol. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Each measuring party's device as one POVM per round"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/ass:meas) |
| Category | receiver |
| Machine key | `measurement_only_receiver` |
| Emitted by | `reductions@station0`, `reductions@station1` |

Each measuring device, at every measuring station of either party, turns the incoming quantum signal into a classical result in every round and keeps nothing quantum afterwards: no post-measurement system is stored, re-used or passed on. Everything after detection (announcements, sifting, acceptance, the key map, error correction, privacy amplification) uses classical data only. Where several measuring stations are declared, of different parties or of one, or where several parties measure inside one declared station, each device measures independently of the others, so that the round's measurement is the product of theirs: no shared randomness or shared ancilla couples them. A receiver with a quantum memory that keeps the measured light, or passes it on, violates this.

For this run:

- Alice's device enters through one POVM: declared
- Bob's device enters through one POVM: declared

##### <a id="A-TRUST"></a>A-TRUST: Trusted and exactly characterised receiver

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | The declared instrument describes the physical receiver exactly, and the receiver is under the legitimate party's control. It is the parent of most of the receiver's device assumptions, which spell out its parts. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Trusted and exactly characterised receiver"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:trust) |
| Category | receiver |
| Machine key | `receiver_trusted_exact` |
| Emitted by | `receiver@station0`, `receiver@station1` |

The receiver you declared is the receiver you run. Its mode space, its optical layout (or the instrument or Gram matrices you supplied), the assignment of outputs to detectors, the efficiencies, the dark-count probabilities and the probe states are those of the physical device, with no uncertainty to account for. The device is under your control, and nobody else can select, tune or influence it. A characterisation uncertainty is not modelled: the result applies to the device exactly as declared.

Not on this run: the probe states, since no station it is about has a private setting.

###### <a id="A-EXACT"></a>A-EXACT: Exact declared parameters

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Declared component parameters, efficiencies, dark-count probabilities and probe mean photon numbers are exact. A non-zero parameter tolerance would be an uncertainty set, which is out of scope and is refused rather than ignored. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Exact declared parameters"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:exact) |
| Category | receiver |
| Refines | [A-TRUST](#A-TRUST) |
| Machine key | `exact_parameters` |
| Emitted by | `receiver@station0`, `receiver@station1` |

Every number you declared for a receiver component (each efficiency, dark-count probability, probe mean photon number and other component parameter) is the device's true value, not an estimate with an error bar. The engine refuses a non-zero tolerance field, and an uncertainty set is not modelled. A result computed from a measured value therefore applies to a device with exactly that value.

Not on this run: the probe mean photon numbers, since no station it is about has a private setting.

For this run:

- declared_tolerance_fields: none

###### <a id="A-MODES"></a>A-MODES: Completeness of the declared modes

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Every optical path from outside the receiver to a detector is a declared mode. A bright-illumination or wavelength-shifted attack targets exactly this premise. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Completeness of the declared modes"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:modes) |
| Category | receiver |
| Refines | [A-TRUST](#A-TRUST) |
| Machine key | `no_undeclared_paths` |
| Emitted by | `receiver@station0`, `receiver@station1` |

Every way light from outside can reach one of your detectors (every spatial, spectral, temporal and polarisation mode it can arrive in) is represented by one of the declared modes. Light the model does not carry, for example at another wavelength or along a path straight to the detectors as in bright-illumination attacks, violates this. Declare the mode, or declare a model of the attack. This premise is about the completeness of the receiver's optical description; that nothing reaches the station except through its declared inputs, and that nothing leaks out of it, is the laboratory premise of this station's party, [A-LAB](#A-LAB).

###### <a id="A-NOSEL"></a>A-NOSEL: Device fixed independently of the adversary

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | The receiver configuration and the probe declaration are fixed before the run and cannot be chosen or influenced by the adversary. With [A-TRUST](#A-TRUST) this makes one declared POVM, rather than a family, the right object. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Device fixed independently of the adversary"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:nosel) |
| Category | receiver |
| Refines | [A-TRUST](#A-TRUST) |
| Machine key | `device_not_adversarial` |
| Emitted by | `receiver@station0`, `receiver@station1` |

Your receiver's configuration (its components and their settings, which output goes to which detector, and the probe settings) is fixed before the run. An attacker cannot choose or change it, including through properties the model does not describe, such as the wavelength of injected light shifting a beam splitter's ratio. If an attacker can steer the receiver this way, the declared measurement is the wrong one and the result does not apply. This premise is about the configuration of the receiver itself; what may leave or enter the station by other routes is the laboratory premise of this station's party, [A-LAB](#A-LAB).

Not on this run: the probe settings, since no station it is about has a private setting.

###### <a id="A-PASSIVE"></a>A-PASSIVE: Passive linear optics

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Every optical element is passive linear optics, with no gain and no mixing of creation and annihilation operators. Total photon number is then a conserved grading, on which every block statement of the module rests. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Passive linear optics"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:passive) |
| Category | receiver |
| Refines | [A-TRUST](#A-TRUST) |
| Machine key | `passive_optics` |
| Emitted by | `receiver@station0`, `receiver@station1` |

Every optical component of your receiver is passive and linear: beam splitters, wave plates, polarisers, attenuators and the like. No component amplifies light, and none is nonlinear (no frequency conversion, no squeezing). The total photon number is then never increased inside the receiver. If a component can add photons, the photon-number blocks the analysis rests on do not exist.

For this run:

- catalogue entries (catalogue_entries): C1, C2, C3

###### <a id="A-PORT"></a>A-PORT: Mode-insensitive port response

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | A port clicks exactly when the modes it collects carry at least one photon, whatever their distribution over those modes. It is the multimode form of [A-THRESH](#A-THRESH), and it gives a detector that collects several modes a meaning. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Mode-insensitive port response"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:port) |
| Category | receiver |
| Refines | [A-THRESH](#A-THRESH) |
| Machine key | `mode_insensitive_ports` |
| Emitted by | `receiver@station0`, `receiver@station1` |

Each detector port clicks exactly when at least one photon arrives in any of the modes it collects, whatever their distribution over those modes. A detector whose click probability depends on the spatial, spectral or temporal mode of the arriving photon (efficiency mismatch) violates this. Such a mismatch has to be declared as mode-dependent loss in front of the port.

For this run:

- ports: H, V, D, A

###### <a id="A-THRESH"></a>A-THRESH: Threshold detectors without memory

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Each detector reports one bit per gate, with no photon-number resolution, no memory or timing effects, and no correlations beyond the declared dark-count channel. It fixes the click-or-no-click outcome alphabet the receiver's measurement is built on. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Threshold detectors without memory"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:thresh) |
| Category | receiver |
| Refines | [A-TRUST](#A-TRUST) |
| Machine key | `threshold_memoryless_detectors` |
| Emitted by | `receiver@station0`, `receiver@station1` |

Your detectors are threshold (click or no-click) detectors read once per gate. They have no photon-number resolution, no dead time, no afterpulsing and no timing jitter. Gates and detectors are correlated only through the dark-count model you declared. Dark counts are independent from round to round, and between detectors unless you declared a correlated dark-count channel. Detectors with dead time or afterpulsing at your gate rate violate this.

For this run:

- temporal mode index (tau): 0, the temporal or spectral index of every mode label (reserved: a single value, with no temporal meaning; not the declared tolerance)

###### <a id="A-VAC"></a>A-VAC: Vacuum on undeclared input modes

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Undeclared input modes and dilation modes start in vacuum. A mode that can carry light to a detector is declared, as a channel mode if the adversary can populate it and as a source mode if the legitimate party does. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Vacuum on undeclared input modes"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:vac) |
| Category | receiver |
| Refines | [A-TRUST](#A-TRUST) |
| Machine key | `undeclared_inputs_vacuum` |
| Emitted by | `receiver@station0`, `receiver@station1` |

Every optical input of your receiver that you did not declare as an input, and every internal loss or ancilla mode, receives no light. A mode that can carry light to a detector is declared: as a channel mode if an attacker could put light into it, and as a source mode if your own equipment, for example a probe laser, does.

For this run:

- undeclared_input_modes: X_H, X_V, Xr_H, Xr_V, Zr_H, Zr_V

#### <a id="category-channel-and-adversary"></a>The channel and the attacker

Premises about the attacker and what she can do. Evidence comes from the authentication scheme's specification and implementation review and, for detector-control premises, from testing the receiver under attack. No premise limits the size of the attacker's memory: the security statement holds against an attacker with memory of any size.

##### <a id="A-AUTH"></a>A-AUTH: Authentication of the classical channel by a keyed scheme

| Field | Value |
| --- | --- |
| About | The classical channel and the attacker |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
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
| Summary | In every one of the n rounds of the run an acceptance value of the alphabet is recorded. The counts and the frequency vector then describe the whole run, normalised by its round count. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "An acceptance value recorded in every round"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:alphabet) |
| Category | protocol-structure |
| Machine key | `acceptance_recorded_every_round` |
| Emitted by | `statistics` |

Every one of the n rounds of your run records an acceptance value from the declared acceptance alphabet: no round counted in n is missing from the record. If rounds go missing (for example through lost time tags), the counts are normalised against the wrong number of rounds and the acceptance test does not describe the run. A round missing from the record also puts security at stake: the acceptance test must be evaluated on the acceptance values of all n rounds ([A-CONFORM](#A-CONFORM)), and a measured round the record drops is a sifting step the declaration does not describe ([A-SPEC](#A-SPEC)). Where the engine builds the acceptance set, it checks that the alphabet, its order and n are those of your protocol declaration; a set carried in the declaration is read in the declaration's order, so writing it in that order is yours to check.

For this run:

- acceptance_alphabet: [the 79 acceptance outcomes](#setup-acceptance)
- rounds: 100000000

##### <a id="A-FIXED"></a>A-FIXED: Protocol parameters fixed before the run

| Field | Value |
| --- | --- |
| About | The protocol's structure |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Summary | The acceptance set, the round count, the key length, the transcript length, the error budgets, the authentication parameters and the Rényi order are fixed before the run and applied unchanged. The key length is that of a fixed-length protocol, not one chosen from the run's data. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Protocol parameters fixed before the run"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:fixed) |
| Category | protocol-structure |
| Machine key | `parameters_fixed_before_run` |
| Emitted by | `meat-core` |

Every parameter the key length rests on is fixed before the run starts: the acceptance test, the number of rounds, the key length, the error-correction budget λ_EC, the error budgets ε_PA and ε_EV, and the authentication parameters ε_auth and k_auth. The Rényi order α at which the key length is computed is fixed before the run too; choosing it by comparing the key lengths your declared model gives at several orders, as the run tier's outer search over α does, reads no data of the run and is such a choice. None of them may be chosen or adjusted after looking at the run's data, for example by relaxing the acceptance threshold or picking the key length from the observed error rate. That would be a variable-length protocol, which this analysis does not cover.

For this run:

- acceptance_set: alphabet = the 79 acceptance outcomes (see Acceptance test), geometry = polytope, inequalities = 158
- rounds: 100000000
- key_length: 40192819
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
| Summary | The same specification, source mode and operators describe every round: the sameness clause of round homogeneity, not the absence of memory across rounds. One compiled declaration and one certificate decision then serve the whole run. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Round homogeneity of the declaration"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:rhom) |
| Category | protocol-structure |
| Machine key | `round_homogeneity_declaration` |
| Emitted by | `protocol-compiler`, `meat-core` |

One protocol description covers the whole run. Every round uses the same measurements, the same setting choices and their probabilities, and the same classical processing, and, where the source is trusted, the same source, so one declaration and one certificate decision apply to all n rounds. A run in which you change settings, or your devices drift so that later rounds need different operators, violates this. Only parts of a run fixed before it starts, each processed as its own execution and composed under [A-SEPARATE](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:separate-executions), which also asks that no device carry a state from one part into the next, can be analysed separately; a split chosen after seeing the data is not covered. That no device remembers earlier rounds is not part of this premise: for the measuring stations it is [A-SPEC](#A-SPEC), for Alice's letter [A-ALICE-MEAS](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:alice-meas), and where the source is trusted the source premise.

Not on this run: the same source in every round, and the source's memory, since the source is untrusted.

For this run:

- specification: 501 characters, written out in full below
- source_mode: untrusted
- rounds: 100000000

acceptance_alphabet = the 79 acceptance outcomes (see Acceptance test), alice_dim = 1, announcement_alphabets = A = gen:Z, gen:X, gen:nc, gen:mc, test:nc, test:H, test:V, test:D, test:A, test:mc, B = Z, X, nc, mc, H, V, D, A, key_alphabet = 0, 1, key_holder = A, physical_receiver_dims = 3, 3, readout_alphabets = A = (nc,gen), (nc,test), (H,gen), (H,test), (V,gen), (V,test), (D,gen), (D,test), (A,gen), (A,test), (mc,gen), (mc,test), B = nc, H, V, D, A, mc, signal_alphabet = x0, transmitted_dim = 1

###### <a id="A-ROUND"></a>A-ROUND: Round homogeneity of the instrument, probe and dark counts

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | The same instrument, probe declaration and dark-count channel describe every round, and the receiver has no memory across rounds. One receiver artifact then describes the whole run. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Round homogeneity of the instrument, probe and dark counts"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:round) |
| Category | receiver |
| Refines | [A-RHOM](#A-RHOM) |
| Machine key | `round_homogeneity` |
| Emitted by | `receiver@station0`, `receiver@station1` |

Your receiver behaves the same way in every round: the same optics, the same probe settings and the same dark-count behaviour. Nothing it does in one round depends on the inputs or outputs of other rounds: no detector memory, and no drift that the declaration averages over. A receiver whose efficiency drifts during the run violates this. Only parts of a run fixed before it starts, each processed as its own execution and composed under [A-SEPARATE](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:separate-executions), can be analysed separately; a split chosen after seeing the data is not covered. A receiver whose detectors remember earlier clicks, through afterpulsing, a dead time or any other dependence on earlier rounds, violates it too, and nothing in this engine repairs that: no input describes more than one round.

Not on this run: the probe settings, since no station it is about has a private setting.

###### <a id="A-ROUND-SQ"></a>A-ROUND-SQ: Round homogeneity of the physical measurement

| Field | Value |
| --- | --- |
| About | Alice's and Bob's stations |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | One physical POVM describes the measurement of every round, and each round's measurement acts as it describes whatever happened in other rounds: no detector memory and no drift. Nothing is assumed about the attacks being independent across rounds. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Round homogeneity of the physical measurement"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/ass:round) |
| Category | receiver |
| Refines | [A-RHOM](#A-RHOM) |
| Machine key | `round_homogeneity_squashing` |
| Emitted by | `reductions@station0`, `reductions@station1` |

Each measuring device, at every measuring station of either party, performs the same measurement in every round: the same optics, detectors and dark-count behaviour, settings drawn with the same probabilities, and, where you declared detector-response modes, the same response in each mode. What a device does in one round does not depend on the inputs or outputs of other rounds. Drift of efficiency, alignment or dark counts violates this. Only parts of a run fixed before it starts, each processed as its own execution and composed under [A-SEPARATE](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:separate-executions), can be analysed separately; a split chosen after seeing the data is not covered. Detector memory (afterpulsing, a dead time, any dependence on earlier rounds) violates it too, and nothing here repairs that. Attacks may still correlate the rounds. The engine's finite model and squashing map are its own construction, not part of this premise.

Not on this run: the same response in each declared detector-response mode, since no detector-response mode is declared.

For this run:

- Alice's physical POVM: one for every round, no memory across rounds
- Bob's physical POVM: one for every round, no memory across rounds

##### <a id="A-SEQ"></a>A-SEQ: Sequential round structure

| Field | Value |
| --- | --- |
| About | The protocol's structure |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Each round runs the delivery of its quantum systems, then every party's measurement, then the round's public messages, then sifting; each party measures in round order, post-processing follows all rounds and every message is public. It is the timing premise of the security analysis. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Sequential round structure"](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:seq) |
| Category | protocol-structure |
| Machine key | `sequential_round_model` |
| Emitted by | `transmitter`, `reductions@station0`, `reductions@station1`, `meat-core` |

In every round the quantum systems come first: where your source is trusted, it prepares and sends that round's signal, and otherwise the systems of the round are delivered to the measuring stations. Then every party that measures completes its measurement, and only then are that round's public messages sent, in the declared order. Sifting is then determined by the announcements, and no operation on a quantum system of a round depends on a public message of that round. All classical post-processing (for example error correction, verification and privacy amplification) runs after all n rounds, and every classical message is public. A message sent before a measurement of the same round has finished (for example an early basis announcement) violates this. Each party that measures completes its measurement of each round before it completes that of the next round.

Not on this run: the trusted source preparing and sending each round's signal, since the source is untrusted.

For this run:

- round order: every measurement of the round precedes the round's public messages ([Assumption "Sequential round structure"](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:seq), [Definition "Measurement-factorizing n-round protocol"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/def:protocol))
- measured system: the systems Alice's station measures
- measured system: the systems Bob's station measures
- rounds: 100000000

##### <a id="A-SPEC"></a>A-SPEC: Specification faithful to the apparatus

| Field | Value |
| --- | --- |
| About | The protocol's structure |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Declared dimensions, alphabets, tables and measurements describe the apparatus: the receiver's in every round whatever the others did and, where no source certificate is demanded, Alice's of two or more letters; every input yields a key. The compiler checks only the last, in part. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Specification faithful to the apparatus"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:spec) |
| Category | protocol-structure |
| Machine key | `specification_describes_apparatus` |
| Emitted by | `protocol-compiler` |

Your declared numbers describe your apparatus: each system has its declared dimension, every alphabet and table (announcements, sifting, the raw key bit) is what your devices and software do, and the key rule yields a key value, never "no key", on every input. Each measuring station, of either party, performs exactly its declared measurement in every round, on that round's input alone; afterpulsing or a dead time violates this. A declared receiver instrument's measurement is the model the engine emits from it; the emission step is recorded, not bounded. Where no source-replacement certificate is demanded (an untrusted source, or a one-dimensional A), Alice's declared measurement of her letter is the one she performs; [A-ALICE-MEAS](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:alice-meas) adds every round, alone. The engine checks that the declaration is well formed, not that it matches your hardware.

Not on this run: Alice's declared measurement of two or more letters, since the declaration has one letter.

For this run:

- specification: 501 characters, written out in full below
- receiver_family: alphabet = nc, H, V, D, A, mc, party = A, physical_dim = 3, presentation = direct, alphabet = nc, H, V, D, A, mc, party = B, physical_dim = 3, presentation = direct

acceptance_alphabet = the 79 acceptance outcomes (see Acceptance test), alice_dim = 1, announcement_alphabets = A = gen:Z, gen:X, gen:nc, gen:mc, test:nc, test:H, test:V, test:D, test:A, test:mc, B = Z, X, nc, mc, H, V, D, A, key_alphabet = 0, 1, key_holder = A, physical_receiver_dims = 3, 3, readout_alphabets = A = (nc,gen), (nc,test), (H,gen), (H,test), (V,gen), (V,test), (D,gen), (D,test), (A,gen), (A,test), (mc,gen), (mc,test), B = nc, H, V, D, A, mc, signal_alphabet = x0, transmitted_dim = 1

##### <a id="A-TSM"></a>A-TSM: Output-state test statistics

| Field | Value |
| --- | --- |
| About | Alice's station |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Every per-round public choice of known bias at the measurement the emitted family describes, its private setting included where it has one, is a component of the emitted outcome and enters only through its statistics. No derivation then assumes a state-independent test fraction. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Output-state test statistics"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/ass:tsm) |
| Category | protocol-structure |
| Machine key | `test_statistics_model` |
| Emitted by | `reductions@station0` |

Every per-round random choice with a known bias made at this station (for example its probe setting, where it has one, or whether a round is a test round, where that is added by relabelling its outcomes) is recorded as part of that round's outcome, and it enters the analysis only through the observed statistics. No derivation of this contract then assumes a state-independent test fraction.

Not on this run: its probe setting, since no station it is about has a private setting.

For this run:

- test_statistics_model: output_state

#### <a id="category-local-randomness"></a>Your random number generators

Premises about the local randomness of the choices and hash seeds. Evidence for them comes from certifying the random number generators.

##### <a id="A-COIN"></a>A-COIN: Public choices as private coins of declared bias

| Field | Value |
| --- | --- |
| About | Your random number generators (the choice drawn at Alice's station) |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | Every public choice is drawn with its declared bias; those of fixed bias are jointly independent of each other, the quantum systems and the adversary, and one weighted by a station's setting depends on the round through that setting only. It lets a weight inside the measurement describe the round. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Public choices as private coins of declared bias"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:coin) |
| Category | local-randomness |
| Machine key | `public_choice_weights` |
| Emitted by | `protocol-compiler` |

Every public choice of your protocol (for example an actively chosen basis, or whether a round is a test round; a basis set passively by a beam splitter is part of the measurement, not a choice), whichever party draws it and at whichever of its stations, comes from a local random number generator with exactly the declared probabilities, and each is announced or kept secret exactly as declared. The choices with fixed probabilities are independent of each other and, all together, of the quantum signals and of anything an attacker does. A choice whose probabilities depend on a station's private setting is drawn by a party whose recorded outcome includes that setting, and may depend on that setting only, never otherwise on Alice's letter, another choice or a detection result.

Not on this run: a choice whose probabilities depend on a station's private setting, since no choice on this run is weighted by a setting; its mention of Alice's letter, since the declaration has one letter, a placeholder.

For this run:

- choice_weighting: choice_alphabet = gen, test, factor = alice_station, matrix = off\|gen = 0.875, off\|test = 0.125, setting_alphabet = off
- specification: 501 characters, written out in full below

acceptance_alphabet = the 79 acceptance outcomes (see Acceptance test), alice_dim = 1, announcement_alphabets = A = gen:Z, gen:X, gen:nc, gen:mc, test:nc, test:H, test:V, test:D, test:A, test:mc, B = Z, X, nc, mc, H, V, D, A, key_alphabet = 0, 1, key_holder = A, physical_receiver_dims = 3, 3, readout_alphabets = A = (nc,gen), (nc,test), (H,gen), (H,test), (V,gen), (V,test), (D,gen), (D,test), (A,gen), (A,test), (mc,gen), (mc,test), B = nc, H, V, D, A, mc, signal_alphabet = x0, transmitted_dim = 1

##### <a id="A-SEED"></a>A-SEED: Private, independent and fresh local randomness

| Field | Value |
| --- | --- |
| About | Your random number generators |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Summary | The post-processing seeds are drawn with their declared laws, privately, independently and afresh; in trusted-source mode the source's letters and prepared systems are independent of the adversary, who never gets a purification of them. Leftover hashing and source replacement rest on it. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Private, independent and fresh local randomness"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:seed) |
| Category | local-randomness |
| Machine key | `post_processing_seeds` |
| Emitted by | `meat-core` |

Your random choices come from a good private random number generator. The error-correction seed, the error-verification hash and the privacy-amplification hash are each drawn with their intended distribution, kept secret until the protocol announces them, independent of each other, of every other record of the protocol (the raw key included) and of everything the attacker knows, and drawn anew in every run. With a trusted source, the randomness with which it picks each round's letter and prepares its state is uncorrelated with the attacker at the start, and no purification of a prepared state is ever available to the attacker. A seed reused across runs, fixed in the device or disclosed early, or a predictable or pre-shared random source, violates this.

Not on this run: the randomness of a trusted source and its prepared states, since the source is untrusted.

Which party draws each post-processing seed (the error-correction seed, the error-verification seed and the privacy-amplification hash) is not fixed by the analysed post-processing: each is drawn and then announced. As for the seeds, this premise is about the random number generator of whichever party draws each; [A-HASH](#A-HASH) is about the hash families the seeds select from.

For this run:

- source_mode: untrusted

#### <a id="category-post-processing"></a>Your post-processing

Premises about error correction, error verification and privacy amplification. Evidence for them comes from reviewing and testing that software.

##### <a id="A-CONFORM"></a>A-CONFORM: The implementation runs the analysed post-processing

| Field | Value |
| --- | --- |
| About | Your post-processing |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Summary | The implementation applies the acceptance test and the verification abort, sends no message beyond the model's, outputs the model's key or nothing, uses no key before the execution ends and aborts on an authentication failure. It ties the analysed protocol to the one that runs. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "The implementation runs the analysed post-processing"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:conform) |
| Category | post-processing |
| Machine key | `post_processing_as_analysed` |
| Emitted by | `meat-core` |

Your implementation runs exactly the analysed post-processing. It aborts unless the acceptance statistics lie in the declared acceptance set; after the rounds it sends no public message other than the error-correction transcript of at most λ_EC bits and its seed, the verification seed, hash and result, the privacy-amplification hash choice and the closing accept or abort decisions; it aborts when verification fails or a message fails authentication (an auth-abort); it outputs the analysed ℓ-bit key, or nothing. No part of the key is used before the execution has ended: the key holder, having sent its final decision, waits until the partner has received it or an auth-abort in its place, and the partner until one of these has arrived. Interactive error correction, a resent syndrome or early key use violate this. Tightening 2ε_auth to ε_auth under this timing is an open question.

For this run:

- acceptance_set: alphabet = the 79 acceptance outcomes (see Acceptance test), geometry = polytope, inequalities = 158
- λ_EC (lambda_ec): 0
- ev_hash_bits: 30
- key_length: 40192819

##### <a id="A-HASH"></a>A-HASH: Ideal two-universal privacy amplification

| Field | Value |
| --- | --- |
| About | Your post-processing |
| At stake | secrecy (the key may leak to the attacker); correctness (the two keys may differ) |
| If it fails | security (the key may leak, or the two keys may differ) |
| Summary | Privacy amplification uses an ideal two-universal family, collision probability exactly 2^−ℓ for distinct inputs, and error verification a two-universal family. The first is what leftover hashing reads, the second what the verification collision bound reads. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Ideal two-universal privacy amplification"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:hash) |
| Category | post-processing |
| Machine key | `pa_hash_family` |
| Emitted by | `meat-core` |

Privacy amplification uses a hash family in which any two different inputs collide with probability exactly 2^−ℓ (an ideal two-universal family, such as Toeplitz hashing), and error verification uses a two-universal hash family. If your privacy-amplification family is only two-universal (collision probability at most 2^−ℓ), shorten the key by one further bit.

For this run:

- key_length: 40192819
- ideal_hash: true
- ev_hash_bits: 30

##### <a id="A-KEYREG"></a>A-KEYREG: Dedicated key register and one-way reconciliation

| Field | Value |
| --- | --- |
| About | Your post-processing |
| At stake | secrecy (the key may leak to the attacker) |
| If it fails | security (the key may leak) |
| Summary | The post-processing acts on the raw-key string the rounds write, the declared holder computes that string, and reconciliation runs one way from the holder through a padded fixed-length transcript. The leakage term counts the register's full length. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "Dedicated key register and one-way reconciliation"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:keyreg) |
| Category | post-processing |
| Machine key | `key_register` |
| Emitted by | `meat-core` |

Error correction is one-way. The key holder computes its raw key from its own record (its letters, the detection results of its measuring stations, or both, whichever it holds) and the public announcements, and its messages depend only on that raw key and public random seeds. The transcript always has exactly λ_EC bits, shorter messages being padded. Interactive error correction (for example Cascade) or a variable-length transcript is not covered by this key length.

On this run Alice holds the key; her own record here is the detection results of Alice's station (alice_station).

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
| Summary | On an honest run each round's probability of each acceptance outcome, given everything before it, stays inside the declared honest envelope. The premise bears on the advertised honest abort probability and restricts no adversary. |
| Review status | implemented, also with everything it rests on |
| Statement | [Assumption "Honest rounds inside a declared envelope"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:hon-env) |
| Category | honest-model |
| Machine key | `honest_rounds_within_envelope` |
| Emitted by | `statistics` |

When no attacker is present, each round's probability of each acceptance outcome, given everything that happened before, stays inside the honest model: between the lower and upper bounds of the honest envelope where you declared one, and equal to the honest distribution where you gave a single one instead (an envelope of zero width). With an envelope the channel may drift within and between runs as long as it stays inside it; with a single distribution it may not drift at all. This premise only bears on the advertised probability that an honest run aborts; it never affects security. If drift can leave the honest model, declare a wider envelope.

For this run:

- honest_model: iid_honest_rounds
- honest_distribution: the honest probability of each acceptance outcome, as in [the table under Acceptance test](#setup-acceptance) (exact fractions: [record](record.md#p-.payload.stages.acceptance_construction.honest_distribution))
- rounds: 100000000

##### <a id="A-REACH"></a>A-REACH: An honest law produced by a feasible state

| Field | Value |
| --- | --- |
| About | The honest model (what an honest run is expected to show) |
| At stake | secrecy (the key may leak to the attacker); completeness (an honest run may abort more often, and a checked run whose mismatch is proven may report no key length) |
| If it fails | security (the key may leak) |
| Summary | Some feasible state of the consuming declaration produces a law of the declared honest envelope, for a single declared law that law itself. It rules out an incompatibility of the honest model with the declaration. |
| Review status | accepted, also with everything it rests on |
| Statement | [Assumption "An honest law produced by a feasible state"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:reach) |
| Category | honest-model |
| Machine key | `honest_reachable` |
| Emitted by | `statistics` |

Your honest model fits your protocol declaration: a state the declaration admits as feasible produces acceptance statistics in your declared honest envelope, or equal to your single declared honest law. If it fails, the declared devices do not describe the statistics and a key length for them is not warranted. The engine's own honest models are built to match the declared Alice marginal; nothing proves this premise for them. Unless switched off, the engine checks every run whose honest statistics you supply or whose declaration carries a constraint you declared: from a proven mismatch it states a cap on the probability that devices behaving as the declaration says pass your acceptance test, and refuses the run where that cap is at most one half, a threshold you can set. On an unchecked run a mismatch goes undetected and this premise is yours to vouch for.

For this run:

- honest_distribution: the honest probability of each acceptance outcome, as in [the table under Acceptance test](#setup-acceptance) (exact fractions: [record](record.md#p-.payload.stages.acceptance_construction.honest_distribution))

## <a id="appendix"></a>Appendix

### <a id="how-computed"></a>How the number was computed

Over n rounds the attacker's uncertainty about the raw key accumulates to n times the per-round bound h_low, less a term for how unlikely the acceptance test is to pass, which cancels over all runs; the bound h_low holds over every attack compatible with your declared devices and with passing statistics. Subtracted are the error-correction transcript of λ_EC bits, the verification hash of ⌈log₂(1/ε_EV)⌉ bits and a finite-size penalty of α/(α−1)·log₂(1/ε_PA) bits; one bit is added back. The remaining key of ℓ bits is secret, counted over all runs: it is within the secrecy parameter ε_PA of a uniform key independent of the attacker's memory and every public message. It is proved for a finite-memory attacker receiving every signal at once; [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security) covers every attacker. The Rényi order α in (1, 2) is fixed before the run ([A-FIXED](#A-FIXED)) and changes the key's length, never its secrecy. Statement: [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).

The certified key rate is the best of a few brackets, each formed from enclosures of the gradient at a point the search found, with every arithmetic step from the declaration's data exact or rigorously enclosed. It is a lower bound on the minimum h_low of the declaration it is formed on, and the key length built from it is secret and correct under the same premises as the first-order key length: the declaration's modelling premises remain, but no premise about how a number was computed is added, the key length itself being computed exactly, its one logarithm enclosed until the integer part is decided. It is not a bound on any other declaration, so a run formed on the snapped declaration still rests where its record says on the premise that the device measures the snapped family. Statement: [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength).

The key length is certified: the first-order bound was formed again at the solver's final points from the data of the declaration it is formed on, every arithmetic step exact or rigorously enclosed, so no premise about how a number was computed is added; the premises of the run remain ([Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength), [Remark "What a certified number rests on"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/rem:certified-scope)). It is formed on the reference companion: the declaration built from your receiver model, through the model's rigorous intervals, on every block the run handed those intervals for.

| Result | Value |
| --- | --- |
| outcome | key-length |
| key length | 40192819 |
| net key length | 40192819 |
| rate per round | 0.40192819 |
| rounds | 100000000 |
| Rényi order alpha | 1.05 |
| alpha chosen by | the declaration (parameters.alpha) |
| reported tier | certified |
| security parameter | 1.862645149230957e-09 |
| term eps_pa | 9.313225746154785e-10 |
| term eps_ev | 9.313225746154785e-10 |
| term eps_auth | 0.0 |
| authentication factor | 2 |
| completeness ε\* | 1/1000000 |
| key length reason code | certified_reported |
| reason text | the bracket was formed again at the run's final points from the declaration's data with every arithmetic step exact or rigorously enclosed ([Requirement "The certified evaluation of the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:certified-evaluation)), and the key length is computed exactly from max{0, h_cert} by [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength); the first-order number and its key length are recorded beside it |

The engine also records why the key length is what it is in one line of its own, kept verbatim below; its capitals are the engine's emphasis, not the report's.

certified_reported: the bracket was formed again at the run's final points from the declaration's data with every arithmetic step exact or rigorously enclosed ([Requirement "The certified evaluation of the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:certified-evaluation)), and the key length is computed exactly from max{0, h_cert} by [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength); the first-order number and its key length are recorded beside it

#### <a id="diagnostics"></a>Diagnostics

| Diagnostic | Value | What it means |
| --- | --- | --- |
| Estimate of h_low (`h_low`) | 0.40193773949173434 | The objective at the point the solver returned: an estimate of the worst-case entropy per round. It claims no bound and is not used for the key length; the point is feasible only within a window, so the estimate need not lie above h_low ([Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder)). |
| Certified lower bound h_cert (`h_cert`) | 0.4019347843859667 | The certified lower bound, from which the key length is computed, exactly, through max{0, h_cert}: the first-order bound formed again at the solver's final points from the data of the declaration it is formed on, every arithmetic step exact or rigorously enclosed, so it lies below that declaration's value by the claims alone ([Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength), [Remark "What a certified number rests on"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/rem:certified-scope)). |
| First-order lower bound h_lb (`h_lb`) | 0.4019347843858996 | The first-order lower bound on h_low, recorded beside the certified bound h_cert, from which this run's key length is computed: the best bound over the steps that passed the first-order checks. It is proved in exact arithmetic, its linear minimisations bounded exactly, and computed in floating point, so a computed h_lb can exceed h_low ([Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder), [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength)). |
| Bound minus estimate (`first_order_minus_estimate`) | -2.955105834756555e-06 | h_lb minus the estimate of h_low, recorded with its sign as a diagnostic that asserts nothing. A negative value is how far the bound lies below the estimate, a rough indication of what a longer solve might gain. A positive value is evidence about the arithmetic or the relaxation, not by itself of an unsound bound. |
| Bound clamped at zero (`first_order_clamped`) | false | Whether h_cert was negative, so that the key length used 0 in its place. |
| Estimate's point checked (`estimate_point_relaxed_member`) | true | Whether the Choi factor of the estimate's point passed the three feasibility checks (the acceptance-side factor is not part of this check); it changes no bound, tier or length. |
| Frank-Wolfe gap (`frank_wolfe_gap`) | 0.00012359884073602327 | The Frank-Wolfe gap of one step: the objective there minus that step's tangent-plane bound. On an fw run it is the last step whose gradient was formed; on a candidate search, the best contributing step. It is a convergence diagnostic, and no key length uses it. It reads the point the solver returned, which nothing verifies, so it is no proven bound. |
| How the solver's search stopped (`solver_status`) | iteration-limit | How the search for a good point stopped (on an fw run the loop's own stop; on a candidate search the search's termination), not whether the bound holds. How the search stopped does not enter h_lb, and any lower bound on h_low may stand in the key length ([Corollary "Key length from any lower bound on the value"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:keylength-bound)); so it can cost key length. Whether h_lb is a lower bound rests on the first-order checks, which run in floating point, and on exact arithmetic the engine does not have ([Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder)). |
| Steps (`iterations`) | 10 | The number of steps the solve counted: Frank-Wolfe iterations on an fw run, candidate assessments on a candidate search. |
| Withdrawn steps (`withdrawals`) | none | Steps whose first-order bound was withdrawn because a hypothesis failed or was not established, by reason; a withdrawn step contributes no bound ([Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder)). |

How the search stopped, as a whole: The search did not meet its gap target (1e-10). Its bracket closed to a relative gap of 7.35e-06 ((h_low - h_lb) / \|h_low\|). Its 1 attempt ended 1 budget_exhausted; the last (fw) ended budget_exhausted. The record's termination field reads budget_exhausted.

| Attempt | Method | Steps | Seconds | How it stopped | Why it stopped | Resumed | Bound after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | fw | 10 | — | budget_exhausted | — | — | — |

### <a id="measurement-snaps"></a>Measurement snaps

Before solving, the engine rounds each station's measurement operators onto a fine numerical grid (a snap), so that its exact checks can run.

4 of the 4 blocks of your stations are kept: your model gives them exactly on the grid, so the rounding moved nothing there.

The rounding adds no premise: the key length does not rest on A-SNAP, so nothing in this section asks anything of you.

| Station | Photon number | Status | Rests on A-SNAP? | Fix |
| --- | --- | --- | --- | --- |
| Alice's station | 0 photons (vacuum) | kept exactly: the rounding moved nothing | no | — |
| Alice's station | 1 photon | kept exactly: the rounding moved nothing | no | — |
| Bob's station | 0 photons (vacuum) | kept exactly: the rounding moved nothing | no | — |
| Bob's station | 1 photon | kept exactly: the rounding moved nothing | no | — |

Every block's reference, radii, flags and record pointers, the reduction's own rounding and the run settings: [Measurement snaps in detail](#snaps-detail).

### <a id="snaps-detail"></a>Measurement snaps in detail

- The engine moved your receiver's measurement onto its numerical lattice (a snap) block by block, 4 blocks in all: a block your model gives exactly on the lattice is kept as it is, and every other block is moved as little as the rules that keep its zeros allow.
- 4 blocks were snapped from an exact reference (your receiver model, computed exactly).
- On 4 blocks the run handed an exact reference (your receiver model, computed exactly) beside the snap.
- 4 blocks are kept: your model gives them exactly on the lattice, so the snap moved nothing there.
- Run settings: enclosed references are used, so the blocks of your model handed beside the snap for the key length to be computed from are those known exactly and those known through rigorous intervals (reference_enclosure = true); the strict option is off, so a block that rests on A-SNAP is disclosed, not refused (strict_snaps = false).

| Block | Setting | Station | Status | Snapped from | Reference handed | Largest radius | Input radius | Group | What to change | Cause (detail) | Fix (detail) | Flags | Record |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `m=0` | off | alice_station | kept | exact | exact | 0 | — | — | — | — | — |   | [record](record.md#p-.payload.stages.stations.0.rows_adaptation.measurement_snaps.0.blocks.0) |
| `m=1` | off | alice_station | kept | exact | exact | 0 | — | — | — | — | — |   | [record](record.md#p-.payload.stages.stations.0.rows_adaptation.measurement_snaps.0.blocks.1) |
| `m=0` | off | bob_station | kept | exact | exact | 0 | — | — | — | — | — |   | [record](record.md#p-.payload.stages.stations.1.rows_adaptation.measurement_snaps.0.blocks.0) |
| `m=1` | off | bob_station | kept | exact | exact | 0 | — | — | — | — | — |   | [record](record.md#p-.payload.stages.stations.1.rows_adaptation.measurement_snaps.0.blocks.1) |

| Run setting | Value |
| --- | --- |
| reference_enclosure | true |
| strict_snaps | false |

### <a id="security-claims"></a>Security claims

#### Security statement

- [Corollary "The first-order bound on the reference companion"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:fo-reference): At any points, such as those of a search on the snapped declaration or of one continued on the companion, the bracket formed with the reference companion's objective, gradient, entries and linear minima bounds the companion's value from below; its key length is the reference model's.
- [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength): The largest bracket formed by [Lemma "The certified bracket from enclosures of the gradient"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/lem:certified-bracket) over finitely many points is a first-order bound of [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder), so it is at most the value of the declaration it is formed on and gives that declaration's fixed-length key length exactly as h_lb does.
- [Corollary "Key length on a reference companion from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength-reference): On a reference companion, the best certified bracket, formed over its enclosed measured family as [Lemma "The certified bracket over a measured family known through enclosures"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/lem:certified-bracket-enclosed) allows, gives the key length of the protocol whose declaration is the companion, as the first-order bound on the companion does.
- [Corollary "Key length from any lower bound on the value"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:keylength-bound): Any h ≤ h_low may replace h_low in the key-length bound through max{0, h}, with the same security statement. This is where every solver obtains its key length; a bound h ≤ 0 yields no positive key when ε_EV &lt; 1.
- [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security): Secrecy and correctness compose to (ε_PA + ε_EV)-security with honest authentication; over an authentication scheme within ε_auth that consumes k_auth bits of pre-shared key, the protocol is (ε_PA + ε_EV + 2ε_auth)-secure; when both parties output a key, its net key gain is ℓ − k_auth bits.
- [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength): For a Rényi order α in (1, 2), a key of length ℓ ≤ n·h_low − λ_EC − ⌈log₂(1/ε_EV)⌉ − α/(α−1)·log₂(1/ε_PA) + 1 is ε_PA-secret on the accepted state at every all-at-once finite-register attack the reduction chain carries onto the round model ([A-LINK](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:link)). [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security) extends it to every attack.
- [Lemma "Correctness from error verification"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/lem:ev-correctness): In the fixed-length post-processing model the two parties accept with different keys with probability at most ε_EV, for every attack and every output length. It is the correctness half of the protocol's security.

#### Per execution

- [Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions): One execution's parameter covers one run, and separate executions that share no key add their parameters ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)). A reused authentication key enters through ε_auth, charged twice, and the earlier run's parameter does not bound its distance in general.
- [Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions): N executions that share no key and no device state and leave their keys unused until all have ended, run against one adversary, are together (ε_1 + ... + ε_N)-secure for the joint ideal map. A key reused from one execution in another is not covered.

#### Completeness

- [Requirement "The reported completeness figure"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/req:completeness-report): The engine reports ε\* itself on the exact rule evaluated by its closed forms, and otherwise the figure its route's row names: the allocation sum or an upward-rounded evaluation of the tails clamped at the budget. It never reports a downward-rounded figure.

#### Limitations

- [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope): The completeness parameter ε\* of the statistics module bounds an honest run's failure of the acceptance test only. Aborts in error verification and in authentication are bounded by no claim, so ε\* does not bound the honest abort probability of the whole protocol.
- [Remark "The declared measurement as a premise of the rate"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:declared-measurement): A tiny change of the declared measurement can move the key rate by many bits per round, so the model is a premise of the rate. Where a handed reference's companion counts and the key length is formed on it, the snap only steers the search; nothing bounds model to device.
- [Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions): One execution's parameter covers one run, and separate executions that share no key add their parameters ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)). A reused authentication key enters through ε_auth, charged twice, and the earlier run's parameter does not bound its distance in general.

### <a id="checks"></a>Checks the engine ran

| Check | Outcome | Value | Claims | Record |
| --- | --- | --- | --- | --- |
| `snaps-within-tolerance` Instance snaps within the declared tolerance | passed | snap_max_defect = none; declared_tolerance = 1e-12 |   | [record](record.md#p-.payload.snaps) |
| `receiver-route` Receiver route | passed | element-graph | [Definition "Compilation of a declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:compile) | [record](record.md#p-.payload.stages.receiver_construction.receiver_route) |
| `element-graph-acyclic` Declared element graph well formed | passed | element-graph | [Definition "Declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:graph), [Requirement "Refusal of a graph that is not well formed"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/req:graph-refusal) | [record](record.md#p-.payload.stages.receiver_construction.receiver_route) |
| `probe-states-diagonal` Probe declaration admitted | not-applicable | — | [Definition "Probe declaration"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:probe), [Requirement "Admission of Gaussian-tier probe states only"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/req:probe-diagonal-admission) |   |
| `specification-well-formed` Specification well formed | passed | — | [Definition "Well-formed specification"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/def:well-formed-spec), [Theorem "Soundness, completeness and decidability of the validator"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:validator-soundness) | [record](record.md#p-.payload.stages.compilation) |
| `compiler-gates` Compiler emission gates | passed | — | [Theorem "The emission gates and their outcomes"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:gates) | [record](record.md#p-.payload.compiled) |
| `exact-statistics-inputs` Acceptance-set inputs admissible | passed | PolytopeGeometry | [Requirement "Refusal of an input that violates a decidable clause"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/req:input-refusal) | [record](record.md#p-.payload.stages.acceptance_construction.geometry) |
| `matched-alphabet` Acceptance alphabet matches the declaration | passed | gen, gen:Z\|X, gen:Z\|nc, gen:Z\|mc, gen:Z\|H, gen:Z\|V, gen:Z\|D, gen:Z\|A, gen:X\|Z, gen:X\|nc, gen:X\|mc, gen:X\|H, gen:X\|V, gen:X\|D, gen:X\|A, gen:nc\|Z, gen:nc\|X, gen:nc\|nc, gen:nc\|mc, gen:nc\|H, gen:nc\|V, gen:nc\|D, gen:nc\|A, gen:mc\|Z, gen:mc\|X, gen:mc\|nc, gen:mc\|mc, gen:mc\|H, gen:mc\|V, gen:mc\|D, gen:mc\|A, test:nc\|Z, test:nc\|X, test:nc\|nc, test:nc\|mc, test:nc\|H, test:nc\|V, test:nc\|D, test:nc\|A, test:H\|Z, test:H\|X, test:H\|nc, test:H\|mc, test:H\|H, test:H\|V, test:H\|D, test:H\|A, test:V\|Z, test:V\|X, test:V\|nc, test:V\|mc, test:V\|H, test:V\|V, test:V\|D, test:V\|A, test:D\|Z, test:D\|X, test:D\|nc, test:D\|mc, test:D\|H, test:D\|V, test:D\|D, test:D\|A, test:A\|Z, test:A\|X, test:A\|nc, test:A\|mc, test:A\|H, test:A\|V, test:A\|D, test:A\|A, test:mc\|Z, test:mc\|X, test:mc\|nc, test:mc\|mc, test:mc\|H, test:mc\|V, test:mc\|D, test:mc\|A | [Requirement "Alphabet and round count taken from the consuming declaration"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/req:matched-alphabet) | [record](record.md#p-.payload.stages.acceptance_construction.outcomes) |
| `declaration-admitted` Declaration exactly admissible | passed | — | [Requirement "Exact admission of declared data"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:exact-admission) | [record](record.md#p-.payload.stages.key_rate) |
| `alpha-range` Rényi order of the key length | passed | 1.05 | [Requirement "Rényi order of a reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:key-length-alpha-domain) | [record](record.md#p-.payload.stages.key_rate.alpha) |
| `security-statement-not-vacuous` Security statement not vacuous | passed | eps_pa = 9.313225746154785e-10; eps_ev = 9.313225746154785e-10; eps_auth = 0.0 | [Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous) | [record](record.md#p-.payload.config.parameters) |
| `key-length-gate` Key-length security gates | passed | true | [Requirement "Two-part gate on a key length with declared constraints"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:constrained-key-gate), [Requirement "Source licence for a declared marginal"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:marginal-licence-gate), [Theorem "Constrained accumulation under the attack-set licence"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:constrained-accumulation) | [record](record.md#p-.payload.stages.key_rate.security_gates.key_length_permitted) |
| `first-order-hypotheses` First-order hypotheses at the contributing iterates | passed | contributing = 10; withdrawn = 0 | [Requirement "Withdrawal of the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:first-order-withdrawal), [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder) | [record](record.md#p-.payload.stages.key_rate.per_iterate) |
| `reported-key-length` Reported key length | passed | 40192819 | [Requirement "Reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:reported-key-length) | [record](record.md#p-.payload.stages.key_rate.key_length) |

#### Discharged on this route

| Assumption | Module | Reason | Discharged by |
| --- | --- | --- | --- |
| [A-LINK](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:link) | `protocol-compiler` | discharged on this route by [Requirement "Omission of the link-soundness row only on a proved chain"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/req:link-row-provenance) | `protocol-compiler/req:link-row-provenance` |
| [A-RECV](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/ass:recv) | `reductions` | discharged on this route by [Requirement "Omission of the supplier row for a receiver artefact the run built"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/req:recv-row-provenance) | `reductions/req:recv-row-provenance` |

### <a id="not-engaged"></a>Not engaged on this route

#### Closure members excluded on this route

| Assumption | Module | Reason |
| --- | --- | --- |
| [A-ALICE-MEAS](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:alice-meas) | `protocol-compiler` | emission rule: wherever no source-replacement certificate is demanded (untrusted-source mode, or d_A = 1) and the letter alphabet X has at least two letters; at one letter {M_x} is the identity on A and [Assumption "Alice's declared measurement where no source certificate is demanded"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:alice-meas) holds of every device; not met on this route |
| [A-ATK](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:atk) | `protocol-compiler` | emission rule: whenever m >= 1 and a key-length-eligible declaration is wanted; not met on this route |
| [A-ATK](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:atk) | `meat-core` | emission rule: whenever the constraint list is non-empty and a key length is wanted, on a run that reports a key length or a first-order bound; not met on this route |
| [A-CONST](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/ass:constdecl) | `reductions` | emission rule: only where the emitted constraint list is non-empty, a condition on the constants of emitted entries holding vacuously of an empty list ([Assumption "Declared constants of the constraint list"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/ass:constdecl); [req:assumption-ledger](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/req:assumption-ledger)); not met on this route |
| [A-EIG](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:eig) | `receiver` | invoked exactly at the settings whose declaration carries an \`exact_window\` depth and whose weight is evaluated in floating point (Ass. [Assumption "Declared slack on the computed block eigenvalues"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/ass:eig); Def. [def:pmcex](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:pmcex); Req. [req:eig-ledger-row](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/req:eig-ledger-row)) |
| [A-ENS](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:ens) | `protocol-compiler` | not on the transmitter artefact's ledger on this route |
| [A-ENS](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:ens) | `transmitter` | not emitted on this route |
| [A-PROBE](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/ass:probe) | `reductions` | emission rule: at a station only where its declared setting set T has at least two values: at T = {\*}, q\_\* = 1, every clause of [Assumption "The station's private setting drawn from its own declared randomness"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/ass:probe) holds of the one setting drawn with weight one ([req:assumption-ledger](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/req:assumption-ledger)); not met on this route |
| [A-SNAP](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/ass:snapped-measurement) | `reductions` | emission rule: whenever the run's record names a moved class of the normalizer or a moved block of the declaring party's snap as resting on it ([Theorem "Exact emission of a reduction instance"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/thm:emit) (vi); [Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference) (iii)), and never for a kept one or one evaluated off its snap ([Definition "A reference handed beside a snap; a block evaluated off its snap"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/def:evaluated-off-snap)): in a run whose key length is formed from a number on the reference companion ([req:reference-companion](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/req:reference-companion); [Requirement "The first-order bound evaluated on the reference companion"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:bracket-on-reference)), no class of the normalizer and no handed block of the instance snap rests on it, and only the moved blocks on which the companion carries the snapped block can ([Corollary "The reference companion of a reduction instance"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/cor:reference-companion) (v)); where it is formed instead on the searched declaration, after a withdrawn bracket (its causes, factor_enclosure_inconsistent among them, [Requirement "The first-order bound evaluated on the reference companion"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:bracket-on-reference) (iv)) or in the certified evaluation's fallback (cause companion_not_certified, [Requirement "The certified evaluation of the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:certified-evaluation) (i)), they rest on it. A block whose data the declaring party computes from a model not exact on it is moved even where the snap leaves that evaluation unchanged ([foundations/def:snap](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/def:snap)). Each resting block or class carries its group: no usable reference, reference bracket withdrawn, reference bracket not evaluated, or last resort. A run whose every block and class is kept, as at a shipped default whose blocks are all exact on the lattice, does not engage it; not met on this route |
| [A-SRC](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:src) | `protocol-compiler` | not on the transmitter artefact's ledger on this route |
| [A-SRC](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:src) | `transmitter` | not emitted on this route |
| [A-SRC](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:src) | `reductions` | not emitted on this route |
| [A-SRC](../../../spec/modules/transmitter/contract.pdf#nameddest=claim-transmitter/ass:src) | `meat-core` | emission rule: trusted-source mode at d_A >= 2, on a run that reports a key length or a first-order bound; vacuous at d_A = 1 and never demanded there; not met on this route |

### <a id="route"></a>Route, instance and preparation

#### Instance

| Instance | Value |
| --- | --- |
| id | bbm92 |
| title | BBM92 with two passive stations |
| summary | An untrusted entangled source, independent optical stations, and an Alice-held test coin. |
| readme | [instances/bbm92/README.md](../../../instances/bbm92/README.md) |

#### Protocol document

| Document | Value |
| --- | --- |
| id | bbm92 |
| format_version | 1 |
| packaged | true |
| digest | 10c787ac241e9dfebbe76a1397c7731b6908c7a01f3e9f0c81d355a71876e9f1 |

#### Route

| Fact | Value | Record |
| --- | --- | --- |
| `source_mode` | untrusted | [record](record.md#p-.payload.stages.key_rate.security_gates.source_mode) |
| `receiver_route` | element-graph | [record](record.md#p-.payload.stages.receiver_construction.receiver_route) |
| `receiver_construction_route` | declared_finite_povm | [record](record.md#p-.payload.stages.receiver_construction.route) |
| `source_shape` | bipartite | [record](record.md#p-.payload.channel_interface.source_shape) |
| `source_model` | ideal_pair | [record](record.md#p-.payload.channel_interface.source_model) |
| `acceptance_geometry` | PolytopeGeometry | [record](record.md#p-.payload.stages.acceptance_construction.geometry) |
| `accumulation_branch` | [thm:accumulated-entropy](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:accumulated-entropy) | [record](record.md#p-.payload.stages.key_rate.security_gates.accumulation_branch) |
| `stations` | 2 | [record](record.md#p-.payload.stages.stations) |

#### Honest model

| Honest model | Value |
| --- | --- |
| note | model = ideal_pair; model_derivation = [instances/common/honest/pair_models.md](../../../instances/common/honest/pair_models.md); overridden = false; source_trusted = false; status = honest-data model; no source security attestation |
| tag | iid_honest_rounds |

#### Preparation

| Preparation | Value |
| --- | --- |
| input_preparation_pointer | [record](record.md#p-.payload.snaps.instance.input_preparation) |
| snaps_pointer | [record](record.md#p-.payload.snaps) |
| declared_tolerance | 1e-12 |
| snap_max_defect | — |
| snap_max_displacement | 0.0 |

### <a id="provenance"></a>Provenance

#### <a id="status-legend"></a>What a claim's status means

- superseded: replaced by a newer claim; it no longer counts.
- draft: not yet through an independent review, or sent back by one, or substantively amended since.
- verified: passed an adversarial review by an AI model that saw only the written artefacts (the claim files and the references they cite), not the author's reasoning; not yet accepted by a person.
- accepted: passed that review and was then accepted by the project's human owner.
- implemented: accepted, and the code that implements it is accepted.
- effective status: the lowest status over the claim and everything it rests on.

| Provenance | Value |
| --- | --- |
| report_id | 67617caf590f419c244d053493a49e092f3b878357348cb1e154f15258211e52 |
| record_schema_version | 0.46.0 |
| report_schema_version | 0.36.0 |
| created_by | runs.report_examples.generate |
| config_digest | 36f7e24cdc75605a8a0d476dc8d581e249b4c59141d33168983608a6033d2348 |
| engine | distribution_version = 0.1.0; git_commit = da9eda22e78a438c7bc0dfa7fb8909b0065a132f; git_dirty = false |
| platform | numpy = 2.5.4; oracle = (capabilities = (choi_form, complex_hermitian_psd, direct_sum_sectors, equality_rows, inequality_rows); max_sector_dim = none; name = qics-sector-choi; version = 1.1.3); python = 3.14.6; qics = 1.1.3; scipy = 1.18.1 |
| final_iterate | — |
| reproduce | config_pointer = [record](record.md#p-.payload.config) |

#### Module versions

| Versions | Value |
| --- | --- |
| contracts | meat-core = meat-core@1.28.0; protocol-compiler = protocol-compiler@0.23.0; receiver.station0 = receiver@0.9.0; receiver.station1 = receiver@0.9.0; reductions.station0 = reductions@0.21.0; reductions.station1 = reductions@0.21.0; statistics = statistics@0.10.0; transmitter = transmitter@0.13.0 |
| assumption_manifest | meat-core = meat-core@1.28.0; protocol-compiler = protocol-compiler@0.23.0; receiver.station0 = receiver@0.9.0; receiver.station1 = receiver@0.9.0; reductions.station0 = reductions@0.21.0; reductions.station1 = reductions@0.21.0; statistics = statistics@0.10.0; transmitter = transmitter@0.13.0 |

#### Claim status

| Claim | Review status of the claim | Review status with its dependencies |
| --- | --- | --- |
| `meat-core/frank-wolfe/cor:fo-reference` | accepted | accepted |
| `meat-core/frank-wolfe/cor:certified-keylength` | implemented | accepted |
| `meat-core/frank-wolfe/cor:certified-keylength-reference` | accepted | accepted |
| `meat-core/cor:keylength-bound` | implemented | accepted |
| `meat-core/cor:composed-security` | implemented | accepted |
| `meat-core/thm:keylength` | implemented | accepted |
| `meat-core/lem:ev-correctness` | accepted | accepted |

#### Solver and tolerances

| Setting | Value |
| --- | --- |
| config | max_iterations = 10; method = fw |
| solver_options | — |
| pointers | solver_request = [record](record.md#p-.payload.stages.key_rate.solver_request); search_report = [record](record.md#p-.payload.stages.key_rate.search_report); joint_solver = [record](record.md#p-.payload.stages.key_rate.joint_solver) |
| declared_tolerance | 1e-12 |
| optimizer | constraint_rows = 1e-07; iterate_coupling = 1e-07; iterate_repair_window = 1e-07; optimizer_gap = 1e-10 |
| group_b_worst_pointer | [record](record.md#p-.payload.stages.key_rate.group_b_worst) |

#### Artefacts

| Stage | Station | Kind | Digest |
| --- | --- | --- | --- |
| receiver_construction | alice_station | receiver_artifact | `35613abdfd65d62a418fc802fe6d1a8bb69c1c1c797dbc95d75171546eff5b70` |
| receiver_docking | alice_station | receiver_artifact | `35613abdfd65d62a418fc802fe6d1a8bb69c1c1c797dbc95d75171546eff5b70` |
| reduction | alice_station | reduction_chain | `64231a028be9ac65aaa8086dc5357a42bb676986535adc303471bd76bb66bc7c` |
| receiver_construction | bob_station | receiver_artifact | `35613abdfd65d62a418fc802fe6d1a8bb69c1c1c797dbc95d75171546eff5b70` |
| receiver_docking | bob_station | receiver_artifact | `35613abdfd65d62a418fc802fe6d1a8bb69c1c1c797dbc95d75171546eff5b70` |
| reduction | bob_station | reduction_chain | `d20c0403c58b74b51ef7d85380f2dfccf7abe8bd28d5d875e70a719f558054ea` |
| compilation | — | transmitter_artifact | `00c52e86149764235e110e2acf5143e8bc8e5f34b50466071b0d2a800ee75722` |
| compilation | — | declaration | `0f8111e75df9ec6d7a100d348aac38bd9034af383f13a6f5ab8e95df2a183f98` |
| honest_model | — | honest_distribution | `fbe36a0e16bcc6798f349004bf9f8fe9fc86bb1ddd9f84688f0908cbf353c721` |
| acceptance_construction | — | acceptance_set | `d9befcfc8abee805504c23345bdf5e0a4c4f2d3ca5416678f637a562e022d4a0` |
| docking | — | docked_declaration | `ccaee12c1a599e4c52a28f498a15ef44b99b3695670e47fa39a64ba1dae88643` |
| bundle_write | — | bundle | `ccaee12c1a599e4c52a28f498a15ef44b99b3695670e47fa39a64ba1dae88643` |
| bundle_read | — | bundle | `ccaee12c1a599e4c52a28f498a15ef44b99b3695670e47fa39a64ba1dae88643` |
| solve | — | key_rate_result | `899ae59ef14da40acdf68dfc75ef0af94fbdb8ab09637ce187600c21e4db92d0` |

### <a id="glossary"></a>Glossary

- <a id="g-a-the-letter"></a>A (the letter): The report uses the letter A in four ways: party A of the declaration (Alice); system A, the declaration's per-round letter on that party's side; a detector port named A (as among BBM92's ports H, V, D and A); and the prefix of a premise's short id (A-LAB, A-SPEC). Which is meant follows from where it stands. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-acceptance-map"></a>acceptance map: An input of some templates (BBM92's among them): how finely the public announcements are grouped into the acceptance values the test checks. Every announcement pair its own value (pair-resolved), test rounds grouped by announced bases (announcement-resolved), or key rounds, matched-basis test rounds as ok or error, and one discard value for everything else (merged-discard).
- <a id="g-acceptance-test"></a>acceptance test: The test every run applies to its statistics: each round records one acceptance value, and the run continues only if the frequency of every value lies in an interval (together, the box) around the honest model's prediction. See [Definition "The construction map"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/def:construction).
- <a id="g-acceptance-value-label"></a>acceptance value label: An acceptance value as the protocol document names it. A document may name its values freely (key, ok, err); some, BBM92's among them, write the round's kind and then the two parties' announcements joined by a bar, in the order the document writes them. There gen:Z\|X is a generation round in which the party written first announced Z and the other X, so no key; the key rounds record gen. See [Assumption "An acceptance value recorded in every round"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:alphabet).
- <a id="g-alice"></a>Alice: The name the report gives party A of the declaration. A party may send, measure, or both: in a prepare-and-measure protocol Alice usually sends, in an entanglement-based one she measures at a station; the run's record says which. Where a premise speaks of Alice's letter or of system A, it means the party the declaration assigns A to: Alice, unless the party partition says otherwise. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-param-model-alice-transmittance"></a>alice_transmittance: Probability that Alice's photon of a pair reaches her station. The instance's parameter `model.alice_transmittance` (Alice's transmittance); its value on this run is under [Your inputs](#input-model.alice_transmittance).
- <a id="g-binding"></a>binding: A value of this run that an assumption is about, for example the ε_auth you declared for A-AUTH; shown under the assumption so that you know what exactly you vouch for.
- <a id="g-bob"></a>Bob: The name the report gives party B, the other of the declaration's two parties. Like Alice, he may send, measure, or both; on most protocols he measures at one or more stations. Which he does on this run is read from its record, which also says which party holds system A. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-param-model-bob-transmittance"></a>bob_transmittance: Probability that Bob's photon of a pair reaches his station. The instance's parameter `model.bob_transmittance` (Bob's transmittance); its value on this run is under [Your inputs](#input-model.bob_transmittance).
- <a id="g-budget"></a>budget: An error probability (an ε) that you choose before the run. The secrecy, error-verification and authentication budgets ε_PA, ε_EV and ε_auth make up the security parameter ε. The completeness budget ε_comp is not part of ε: it is the largest ε\* you allow and bounds only how often an honest run fails the acceptance test. The configuration keys keep the word (completeness_budget). See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-catalogue-entries"></a>catalogue entries: The kinds of optical component of the receiver module's catalogue that the declared receiver uses, by entry number, for example C1 beamsplitter, C2 polarising beamsplitter, C3 retarder (a wave plate); the catalogue lists C1 to C10.
- <a id="g-certified-bound"></a>certified bound: The first-order bound formed again at the solver's final points from the declared data, every arithmetic step exact or rigorously enclosed: a lower bound on h_low that rests on the claims and the modelling premises and on no premise about floating-point arithmetic. Where a run reaches it, the key length is computed from it, exactly. See [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength).
- <a id="g-channel-modes"></a>channel modes: The input modes of a receiver that the channel, and so the attacker, can populate; the photon-number blocks are over these modes.
- <a id="g-choi"></a>Choi: A way of writing a quantum channel as one operator; the solver states its optimisation over operators in that form.
- <a id="g-completeness"></a>completeness: How often an honest run, with no attacker and devices behaving as modelled, aborts. It never affects the security parameter ε, which holds for every abort pattern. See [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope).
- <a id="g-composable"></a>composable: The kind of security statement the guarantee is: no test, whatever the attacker knows, tells the run's output from an ideal key exchange with advantage above ε. Later uses of the key build on such a statement, but this contract proves only that separate executions add their ε, not that every later use of the key is covered. See [Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions).
- <a id="g-constraint-entry"></a>constraint entry: A constraint a declaration places on the states it admits, beyond the declared marginal. A run whose declaration carries an entry you declared is checked by the statistics check unless that check is switched off (the inputs table says whether it ran); entries the compiler or a reduction derives do not by themselves call for it. See [Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set).
- <a id="g-dark-count"></a>dark count: A detector click with no photon arriving. Its declared probability per detector and round enters the measurement model.
- <a id="g-declared-tolerance-tau"></a>declared tolerance τ: The ceiling on the defects of the run's own data that the snap may repair before solving.
- <a id="g-detection-efficiency"></a>detection efficiency: The probability that a detector clicks on a photon that reaches it.
- <a id="g-digest"></a>digest: A hash that identifies the content of a file, an artefact or the configuration: the same digest means the same content.
- <a id="g-effective-status"></a>effective status: The lowest review status over a claim and everything it rests on; a claim accepted on its own is only as reviewed as its weakest premise.
- <a id="g-element-graph"></a>element graph: A receiver declared by its optical elements (beamsplitters, wave plates, polarising beamsplitters) and detectors; the engine computes the measurement from them. See [Definition "Compilation of a declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:compile).
- <a id="g-emitted-by"></a>emitted by: The module of the engine whose result rests on the assumption on this run, with the station it was emitted at (station0, station1, ...).
- <a id="g-endpoint-rule"></a>endpoint rule: How the acceptance test sets the ends of each outcome's interval: the exact binomial quantile rule (exact) or the closed-form Bernstein rule (bernstein).
- <a id="g-estimate"></a>estimate: The value of the objective at the point the solver returned. It claims no bound: that point is feasible only within a window, so the estimate need not lie above the true minimum h_low. No key length is computed from it.
- <a id="g-evaluated-off-its-snap"></a>evaluated off its snap: Said of a moved snap block when no number the key length is computed from reads the rounded block: the bound is formed on your receiver model at the points the solver found on the rounded measurement. Such a block rests on your receiver model, not on A-SNAP. See [Definition "A reference handed beside a snap; a block evaluated off its snap"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/def:evaluated-off-snap).
- <a id="g-exact-window"></a>exact window: Above the photon cutoff N, up to a declared depth m\*: the photon numbers at which the multi-click bound takes the larger of the analytic bound and the block's smallest eigenvalue, computed by a floating-point eigensolver less a declared slack ε_eig. The computed value is trusted under A-EIG.
- <a id="g-feasible-state"></a>feasible state: A state the declaration admits: block-diagonal and normalised, with the declared marginal and constraints. h_low is an infimum over the feasible states whose statistics pass the acceptance test.
- <a id="g-first-order-bound"></a>first-order bound: A lower bound on h_low from the tangent planes of the objective at the solver's steps. Its proof is exact, and the minima it uses are bounded from below in exact arithmetic, not taken from the solver; its objective and gradient are computed in floating point with no bound on their numerical error. Stopping early makes it looser, not invalid. The key length uses it where the run is not certified. See [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder).
- <a id="g-flag"></a>flag: A one-dimensional sector of the squashed model that stands for one outcome of the receiver above the photon cutoff.
- <a id="g-frank-wolfe"></a>Frank-Wolfe: The solver's iterative method: each step minimises a linear approximation of the objective over the feasible set and moves toward that point. See [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder).
- <a id="g-frank-wolfe-gap"></a>Frank-Wolfe gap: The objective at one solver step minus that step's tangent-plane bound (fw run: the last step; candidate search: the best contributing one). A convergence diagnostic: it reads the point the solver returned, which nothing verifies, so it is no proven bound. See [Remark "Two reported numbers and one first-order claim"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/rem:fo-interface).
- <a id="g-generation-and-test-rounds"></a>generation and test rounds: gen is the acceptance value of a round whose announcements pass sifting, so that it may give key. Where a public test coin exists (as in BBM92) it makes each round a generation round (gen), which may give key, or a test round (test), in which both parties announce their full outcome. Every round of either kind records one acceptance value.
- <a id="g-geometry-acceptance-set"></a>geometry (acceptance set): The engine's name for the shape of the acceptance set it built; a box of intervals is a polytope.
- <a id="g-h-lb"></a>h_lb: The first-order lower bound on h_low: the best bound over the steps that passed the first-order checks. It is proved in exact arithmetic, its linear minima bounded exactly, and computed in floating point, so a computed h_lb can exceed h_low. A first-order run computes its key length from max{0, h_lb}; a certified run computes it from the certified bound h_cert and records h_lb beside it. See [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder).
- <a id="g-h-low"></a>h_low: A lower bound on the attacker's per-round uncertainty about the raw key, at the chosen α, over every attack compatible with your devices and with statistics that pass the acceptance test.
- <a id="g-honest-envelope"></a>honest envelope: The set of per-round outcome probabilities an honest run is declared to stay within (A-HON-ENV). With a single honest model, as on most runs, it is that model's one law. See [Assumption "Honest rounds inside a declared envelope"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:hon-env).
- <a id="g-honest-model"></a>honest model: The model of what an honest run looks like. It sets the acceptance test and the expected statistics; it never affects the security parameter ε, which holds for every abort pattern.
- <a id="g-iid-honest-rounds"></a>iid_honest_rounds: The acceptance construction's tag for its honest model. In its simplest form the honest rounds are independent and identically distributed with one declared law (A-HON); A-HON-ENV, where a run lists it, lets each round's law vary inside the declared envelope. See [Assumption "Honest i.i.d. rounds"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/ass:hon).
- <a id="g-input-radius"></a>input radius: For an enclosed reference, the largest radius of the enclosures of the irrational inputs (square roots, trigonometric values) from which its centres were computed exactly.
- <a id="g-k-auth"></a>k_auth: The bits of pre-shared key the authentication uses per run; the net key gain is ℓ − k_auth. See [Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth).
- <a id="g-kept-snap-block"></a>kept (snap block): A snap block is kept where your model gives it exactly on the grid, so the snap changes nothing there; every other block is moved.
- <a id="g-key-bases"></a>key bases: The matched bases of a generation round that give key.
- <a id="g-key-length-ell"></a>key length ℓ: The number of secret key bits one run outputs, after deducting error correction, error verification and the finite-size cost of secrecy. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-key-map-and-sifting"></a>key map and sifting: Sifting decides from the public announcements which rounds give key; the key map sends each kept round's readout to a key bit. See [Theorem "Announcement locality, sifting and party computability"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:sifting-and-key).
- <a id="g-largest-radius"></a>largest radius: For the reference handed beside a snap, the largest radius of the rational intervals that enclose its matrix entries: zero where the reference is exact.
- <a id="g-letter"></a>letter: The per-round value on Alice's side of the declaration (system A): in a prepare-and-measure protocol, the signal she prepares. A declaration with one letter uses no clause a premise makes for two or more letters. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-machine-key"></a>machine key: The stable identifier under which the engine records an assumption.
- <a id="g-mc"></a>mc: The outcome "more than one detector clicked" in the same round.
- <a id="g-param-model-mean-pairs"></a>mean_pairs: Mean number of photon pairs the SPDC source emits per round, summed over both polarizations. The instance's parameter `model.mean_pairs` (Mean pairs); its value on this run is under [Your inputs](#input-model.mean_pairs).
- <a id="g-nc"></a>nc: The outcome "no detector clicked".
- <a id="g-net-key-length"></a>net key length: The key length minus the k_auth bits of pre-shared key the authentication consumed: what the run gains. See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-oracle"></a>oracle: The solver library the engine calls for each linear minimisation (QICS, through its sector Choi adapter). Its answers steer the search only; see LMO.
- <a id="g-party-local-view"></a>party local view: How each station's multi-click constraints enter the analysis on a licensed route: as operator inequalities (operator) or only their scalar consequences (licensed_scalar). It has no effect on the encoded route.
- <a id="g-photon-cutoff-n"></a>photon cutoff N: The largest photon number the receiver model treats exactly; higher photon numbers are bounded rather than modelled, so a pulse of more photons is still covered, through that bound (see squashed target POVM).
- <a id="g-photon-number-block"></a>photon-number block: The part of a measurement acting on pulses of exactly m photons; m=0 is the vacuum, m=1 one photon.
- <a id="g-povm"></a>POVM: A measurement written as one positive operator per outcome; the probability of an outcome is the trace of its operator times the state.
- <a id="g-qber"></a>QBER: The quantum bit error rate: the fraction of key rounds in which the two parties' raw key bits differ.
- <a id="g-reference-snap"></a>reference (snap): Your declared receiver model, computed exactly (exact) or known through rigorous rational intervals (enclosed). The snap starts from it where it is exact, and the run hands it beside the snap so that the key length can be computed from it.
- <a id="g-reference-companion"></a>reference companion: Your receiver model put through the same reductions as the rounded measurement, without that rounding, its rows relaxed outward by their floating-point rounding and the model's intervals. A block not handed is carried rounded; with none handed, it is the reduction's exact construction before its own rounding. The run takes its first-order bound there and never solves it. See [Corollary "The reference companion of a reduction instance"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/cor:reference-companion).
- <a id="g-review-status"></a>review status: A claim's review stage, lowest first: superseded (replaced); draft (not yet through an independent review, sent back by one, or substantively amended since); verified (passed an AI model's adversarial review of the written artefacts, not the author's reasoning; not yet accepted by a person); accepted (by the project's human owner); implemented (accepted, its code too). Not a hardware check.
- <a id="g-round"></a>round: One use of the protocol as declared, which records its own outcomes. How a time-tagged system cuts its detection record into rounds (time bins, coincidence windows, how the stations synchronise) is your choice, and your declaration must describe it; What a round is, before the protocol's steps, names premises of this run that the cut bears on.
- <a id="g-route-encoded-licensed"></a>route (encoded, licensed): How the reduction squashes the receiver: the encoded route keeps each outcome's lower bound above the cutoff (its weight p_v) in the target and adds no constraint; the licensed route uses one flag per outcome and adds a licensed constraint.
- <a id="g-sector"></a>sector: One block of a block-diagonal operator, named by a sector map.
- <a id="g-setting"></a>setting: A probe setting of a receiver; "off" is the setting with no probe light. A receiver without a probe has this one setting only, so on such a station "setting off" names its one measurement, not a switch. See [Definition "Probe declaration"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:probe).
- <a id="g-snap"></a>snap: Before solving, the declarer (your instance, or a reduction for what it emits) moves each measurement onto a grid of exact numbers of the same shape. A block your model gives exactly on the grid is kept; every other block is moved, and rests on A-SNAP unless it is evaluated off its snap.
- <a id="g-solver-status"></a>solver status: How the solver's search for a good point stopped, not whether the bound holds; the key length uses only steps that passed the first-order checks. See [Requirement "Withdrawal of the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:first-order-withdrawal).
- <a id="g-source-mode"></a>source mode: Whether the security analysis trusts the source. A trusted source's declared states enter the proof; an untrusted source is the attacker's, and its honest model only predicts the statistics.
- <a id="g-spdc"></a>SPDC: Spontaneous parametric down-conversion: a source of entangled photon pairs whose emission includes multi-pair events; one of this instance's honest models.
- <a id="g-squashed-target-povm"></a>squashed target POVM: The finite-dimensional measurement the security proof works with; the reduction proves that analysing it covers your receiver.
- <a id="g-strict-option"></a>strict option: The run setting strict_snaps: on, the run refuses wherever a moved block or emission sector would rest on A-SNAP, and reports no key length that rests on it, and the certified evaluation does not fall back to the rounded measurement where your receiver model certifies no point; off, the default, such a block is disclosed. See [Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference).
- <a id="g-temporal-mode-index"></a>temporal mode index: The reserved temporal or spectral index of every optical mode label; it takes a single value in a run and is not the declared tolerance τ.
- <a id="g-test-fraction"></a>test fraction: The probability that a round is a test round, in which both parties announce their full outcome.
- <a id="g-transmitter"></a>transmitter: The engine module that models the source side of the protocol. With a trusted source it carries the source's declared states and their premises (A-ENS, A-SRC, or A-WCP for a decoy source); with an untrusted source it carries no source premise. On every run it carries its part of the sequential round order, A-SEQ.
- <a id="g-param-model-visibility"></a>visibility: Visibility v of the entangled pair: matched-basis bits disagree with probability (1 - v)/2. The instance's parameter `model.visibility` (Visibility); its value on this run is under [Your inputs](#input-model.visibility).
- <a id="g-withdrawn-step"></a>withdrawn step: A solver step whose first-order bound was withdrawn because a hypothesis failed or was not established; it contributes no bound. See [Requirement "Withdrawal of the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:first-order-withdrawal).
- <a id="g-x0"></a>x0: The one letter of this declaration's system A, which is one-dimensional here: with the untrusted source, every measurement of this protocol is made at a station, so A carries a single letter, of weight 1, that the proof does not use.
- <a id="g-alpha-r-nyi-order"></a>α (Rényi order): A parameter of the proof, not of your device: any value in (1, 2) fixed before the run gives a valid key length, and the choice changes only how long the key is, never its secrecy. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-eps-security-parameter"></a>ε (security parameter): The bound on how far one run's output can be told from an ideal key exchange: ε = ε_PA + ε_EV + 2ε_auth. It covers one execution. See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-eps-star-completeness"></a>ε\* (completeness): A bound on the chance that an honest run fails the acceptance test; it covers that test only, not later aborts in error verification or authentication. The completeness budget is the largest ε\* you allow. See [Theorem "The completeness bound"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/thm:completeness-bound).
- <a id="g-eps-auth"></a>ε_auth: The error of the authentication of the classical messages, which you declare, including, for a key from an earlier run, its distance from an ideal key; it is counted twice in ε. Zero asserts a channel that is itself authenticated. See [Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth).
- <a id="g-eps-ev"></a>ε_EV: A bound on the chance that both parties accept the run with different keys; error verification compares a hash of ⌈log₂(1/ε_EV)⌉ bits. See [Lemma "Correctness from error verification"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/lem:ev-correctness).
- <a id="g-eps-pa"></a>ε_PA: The secrecy error of privacy amplification: how far the key may be from uniformly random and independent of everything the attacker holds. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-lambda-ec"></a>λ_EC: The number of bits the error-correction transcript reveals; the key length deducts it in full. You declare it; with an estimate file beside the record the report shows how it was chosen. See [Assumption "Dedicated key register and one-way reconciliation"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:keyreg).
