# Key-rate report

## <a id="contents"></a>Contents

- [Summary](#summary): [Key rate considerations](#considerations) · [The result](#result) · [Your setup in brief](#setup-brief) · [What the guarantee means](#guarantee) · [What you vouch for](#vouch) · [Not counted](#not-counted) · [Choices that could lengthen the key](#levers)
- [Your QKD setup](#setup)
- [Your inputs](#inputs)
- [Assumptions you vouch for](#assumptions)
- [Appendix](#appendix): [How the number was computed](#how-computed) · [Security claims](#security-claims) · [Checks the engine ran](#checks) · [Route, instance and preparation](#route) · [Provenance](#provenance) · [Glossary](#glossary)

## <a id="summary"></a>Summary

> **At a glance**
>
> - **No key**: the run was refused at its solve stage, so nothing is certified ([The result](#result))

### <a id="considerations"></a>Key rate considerations

- Idealised honest model, bearing on completeness only. The run's honest model is at its ideal extreme (QBER 0): the acceptance test is built for statistics a real device may not show. For such a device the completeness figure ε\* no longer bounds how often it aborts, possibly on almost every run; security is unaffected. See [Your inputs](#inputs).

### <a id="result"></a>The result

The run was refused at its solve stage (security_statement_vacuous), so no key length was computed and nothing is certified. Why: the \`parameters\` table: eps_PA + eps_EV + 2 eps_auth = 9.313225746154785e-10 + 9.313225746154785e-10 + 2\*0.5 = 1.0000000018626451 (formed exactly) >= 1, so the (eps_PA + eps_EV + 2 eps_auth)-security statement of [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security) (iii) -- at eps_auth = 0 the (eps_PA + eps_EV)-statement of (ii) -- is EMPTY: a distinguishing advantage bounded by one or more is bounded for every protocol, including one that publishes the key -- and NO KEY LENGTH IS REPORTED UNDER IT. [Corollary "Key length from any lower bound on the value"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:keylength-bound) (b) excludes this corner rather than claiming it: its proof records that ell = 1 satisfies the expression at eps_PA = eps_EV = 1 under a security statement that is empty. THE ARITHMETIC IS NOT IN QUESTION and is unchanged; THE RUN IS REFUSED. Every budget keeps its domain and the refusal is on their SUM ([Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous)). A DISCLOSED SCOPE NARROWING.

### <a id="setup-brief"></a>Your setup in brief

- Protocol: Ideal qubit BB84.
- Run: n = 10,000 rounds.

The details: [Your QKD setup](#setup).

### <a id="guarantee"></a>What the guarantee means

This run output no key, so no security guarantee applies to it.

### <a id="vouch"></a>What you vouch for

> **Declared in the protocol document, not derived by the engine**
>
> - `receiver_povm` `bob`: The measurement of station 'bob', declared as a POVM. Declared in the run's protocol document (your own or a shipped template), not derived by the engine; you vouch for it. The premise is that these matrices describe the receiver you have, performed in every round on that round's system alone, whatever happens in the other rounds (A-SPEC). The Band-A route the engine takes for a declared POVM rests on A-IDEAL: an ideal qubit measurement, on a transmitted system that is exactly a qubit, with unit efficiency, no loss, no dark counts, no multi-photon events and no misalignment. If your receiver is not such a measurement, A-IDEAL fails and the key length does not apply to it; declare it as an optical station (kind: optical) instead (instances/declared/README.md). ([A-SPEC](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:spec), [A-IDEAL](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:ideal))

### <a id="not-counted"></a>Not counted

The record names nothing the key length leaves out.

### <a id="levers"></a>Choices that could lengthen the key

The record names no run setting that could lengthen the key.

## <a id="setup"></a>Your QKD setup

### <a id="setup-round"></a>What a round is

A round is one use of the protocol as declared, recording its own outcomes. How a time-tagged system cuts its detection record into rounds (time bins, coincidence windows, how the stations synchronise) is yours to choose, and your declaration must describe it.

### <a id="setup-protocol"></a>Protocol

1. Rounds: The protocol runs n = 10,000 rounds. See [What a round is](#setup-round) above. Record: [record](record.md#p-.payload.config.rounds).
2. Source: The record does not hold this step.
3. Measurement: The record does not hold this step.
4. Public choice: The record does not hold this step.
5. Announcements: The record does not hold this step.
6. Sifting and key map: The record does not hold this step.
7. Acceptance test: The record does not hold this step.
8. Error correction: One-way error correction; its transcript leaks λ_EC = 0 bits. Record: [record](record.md#p-.payload.config.parameters.lambda_ec).
9. Error verification: The parties compare a hash of the corrected keys (failure probability ε_EV = 9.31323e-10). Record: [record](record.md#p-.payload.config.parameters.eps_ev).
10. Privacy amplification: The record holds no key length, so no privacy amplification is stated.

### <a id="setup-source"></a>Source

The record holds no compiled source, so the source is not described.

### <a id="setup-stations"></a>Stations

The record holds no receiver stage, so no station is described.

### <a id="setup-expected"></a>Expected statistics of the honest model

The record holds no honest raw joint distribution, so no expected statistic is given.

## <a id="inputs"></a>Your inputs

Every value the run was computed for, in three tables: your devices and the channel, the budgets (the ε you choose), and the engine's settings. A value shows its default where it differs from it.

### <a id="inputs-device"></a>Device and channel

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-model.qber"></a>QBER ([`model.qber`](record.md#p-.payload.config.model.qber)) | 0 | — | Error rate Q of the honest depolarizing channel in either basis; a model input, not an observed rate | — |
| <a id="input-device.alice_x"></a>[`device.alice_x`](record.md#p-.payload.config.device.alice_x) | 0.5 | — | Probability that Alice prepares in the X basis; Alice's two basis weights sum to one | — |
| <a id="input-device.alice_z"></a>[`device.alice_z`](record.md#p-.payload.config.device.alice_z) | 0.5 | — | Probability that Alice prepares in the Z basis; Alice's two basis weights sum to one | — |
| <a id="input-device.bob_x"></a>[`device.bob_x`](record.md#p-.payload.config.device.bob_x) | 0.5 | — | Probability that Bob measures in the X basis; Bob's two basis weights sum to one | — |
| <a id="input-device.bob_z"></a>[`device.bob_z`](record.md#p-.payload.config.device.bob_z) | 0.5 | — | Probability that Bob measures in the Z basis; Bob's two basis weights sum to one | — |

### <a id="inputs-budget"></a>Budgets (the ε you choose)

A budget is an error probability (an ε) you choose before the run. ε_PA, ε_EV and ε_auth make up the security parameter ε = ε_PA + ε_EV + 2ε_auth. The completeness budget ε_comp is not part of ε: it bounds only how often an honest run fails the acceptance test. The table also holds the round count and the other inputs of the key length.

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-rounds"></a>Rounds n ([`rounds`](record.md#p-.payload.config.rounds)) | 10000 | — | the number of rounds (n), total channel uses; the same n reaches the acceptance construction and the declaration ([Requirement "Alphabet and round count taken from the consuming declaration"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/req:matched-alphabet)) | — |
| <a id="input-completeness_budget"></a>Completeness budget ([`completeness_budget`](record.md#p-.payload.config.completeness_budget)) | 1e-06 | — | the completeness budget (eps_comp) of the acceptance construction; it buys completeness and never soundness | — |
| <a id="input-parameters.alpha"></a>Rényi order α (declared) ([`parameters.alpha`](record.md#p-.payload.config.parameters.alpha)) | 1.5 | — | the Renyi order (alpha) of the declaration; every key-length statement requires alpha in (1, 2) ([Requirement "Rényi order of a reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:key-length-alpha-domain)) | — |
| <a id="input-parameters.eps_pa"></a>Secrecy error ε_PA ([`parameters.eps_pa`](record.md#p-.payload.config.parameters.eps_pa)) | 9.31e-10 (2^-30) | — | the privacy-amplification (secrecy) budget of the key-length expression; eps_pa + eps_ev + 2 eps_auth &lt; 1 ([Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous)) | — |
| <a id="input-parameters.eps_ev"></a>Error-verification error ε_EV ([`parameters.eps_ev`](record.md#p-.payload.config.parameters.eps_ev)) | 9.31e-10 (2^-30) | — | the error-verification (correctness) budget; eps_pa + eps_ev + 2 eps_auth &lt; 1 ([Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous)) | — |
| <a id="input-parameters.lambda_ec"></a>Error-correction leakage λ_EC ([`parameters.lambda_ec`](record.md#p-.payload.config.parameters.lambda_ec)) | 0 | bit | the error-correction transcript length in bits, total and not per round: a fixed-length register of that many bits ([Assumption "Dedicated key register and one-way reconciliation"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:keyreg)) How λ_EC was chosen: declared by you (no estimate sits beside the record). | — |
| <a id="input-parameters.eps_auth"></a>Authentication error ε_auth ([`parameters.eps_auth`](record.md#p-.payload.config.parameters.eps_auth)) | 0.5; default 0.0 | — | authentication error bound: the scheme's error on an ideal key plus the key's trace distance delta from an ideal key; delta = 0 for a fresh key, and for a key from an earlier run a distance you bound and declare ([Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth)). It enters the security parameter twice and never the key length | — |
| <a id="input-parameters.k_auth"></a>Authentication key bits k_auth ([`parameters.k_auth`](record.md#p-.payload.config.parameters.k_auth)) | 0 | bit | the pre-shared key bits the authentication scheme consumes in one run ([Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth) (ii)); the net key is the key length minus k_auth | — |
| <a id="input-alpha"></a>Rényi order α (configured) ([`alpha`](record.md#p-.payload.config.alpha)) | — | — | the Renyi order the run solves at; unset, the run solves at parameters.alpha, or lets alpha_search choose it where that is set (never both) | — |

### <a id="inputs-engine"></a>Engine settings

| Input | Value | Unit | Meaning | Premises |
| --- | --- | --- | --- | --- |
| <a id="input-declared_tolerance"></a>Declared tolerance τ ([`declared_tolerance`](record.md#p-.payload.config.declared_tolerance)) | 0.0 | — | the ceiling (tau) on the pre-snap defect the instance may repair ([spec/architecture.md](../../../spec/architecture.md) 2.8); required, with no default, and told to no module | — |
| <a id="input-parameters.reference_enclosure"></a>Reference enclosure ([`parameters.reference_enclosure`](record.md#p-.payload.config.parameters.reference_enclosure)) | true | — | whether the instance hands beside its snap of its receiver measurement the blocks of the reference known through rigorous rational enclosures ([Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference) (i)); off, only the blocks known exactly are handed, and the reference companion carries the snapped block on every other moved block, which then rests on A-SNAP in the group no_usable_reference (cause enclosure_not_used) | — |
| <a id="input-parameters.strict_snaps"></a>Strict option ([`parameters.strict_snaps`](record.md#p-.payload.config.parameters.strict_snaps)) | false | — | the strict option: whether the run refuses wherever a moved block of a measurement snap or a moved class of the emission would rest on A-SNAP, rather than disclosing it, and reports no key length that rests on it ([Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference) (iv)) | — |
| <a id="input-parameters.statistics_check"></a>Statistics check ([`parameters.statistics_check`](record.md#p-.payload.config.parameters.statistics_check)) | on (not run: the statistics are your honest model's predictions and you declared no constraint entry) | — | the check of the acceptance set against the statistics the declared model can produce ([Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set)): once per run it bounds the mismatch from below and caps the probability that devices behaving as declared pass the acceptance test | — |
| <a id="input-parameters.min_model_pass_probability"></a>Minimum model pass probability τ ([`parameters.min_model_pass_probability`](record.md#p-.payload.config.parameters.min_model_pass_probability)) | 0.5 | — | the smallest probability (tau) with which devices behaving as declared must be able to pass the acceptance test: a checked run whose proven cap on that probability is at most tau is refused as a whole, with no key length ([Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set) (iv)) | — |
| <a id="input-constrained"></a>Constrained solve ([`constrained`](record.md#p-.payload.config.constrained)) | — | — | which acceptance outcomes the acceptance set constrains; unset, every outcome is constrained, and an empty list is a selector in its own right | — |
| <a id="input-endpoint_rule"></a>Endpoint rule ([`endpoint_rule`](record.md#p-.payload.config.endpoint_rule)) | exact | — | statistics' endpoint rule for the acceptance box | — |
| <a id="input-tail_evaluation"></a>Tail evaluation ([`tail_evaluation`](record.md#p-.payload.config.tail_evaluation)) | sweep | — | how statistics decides a tail comparison; it never changes what is decided | — |
| <a id="input-solver.max_iterations"></a>Solver step limit ([`solver.max_iterations`](record.md#p-.payload.config.solver.max_iterations)) | 5 | — | a method-native work cap (under auto, of the Frank-Wolfe stages only); unset, the solver's own is taken | — |
| <a id="input-solver.method"></a>Solver method ([`solver.method`](record.md#p-.payload.config.solver.method)) | fw | — | the candidate search method; unset, auto is taken | — |

## <a id="assumptions"></a>Assumptions you vouch for

No assumption of the run is listed because the run was refused at stage solve (security_statement_vacuous) before any result named a claim. The premises your protocol document declared are listed below.

### Declared in the protocol document, vouched for by you

| Assumption | Kind | Label | Declared | Record |
| --- | --- | --- | --- | --- |
| [A-SPEC](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:spec), [A-IDEAL](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/ass:ideal) | `receiver_povm` | `bob` | The measurement of station 'bob', declared as a POVM. Declared in the run's protocol document (your own or a shipped template), not derived by the engine; you vouch for it. The premise is that these matrices describe the receiver you have, performed in every round on that round's system alone, whatever happens in the other rounds (A-SPEC). The Band-A route the engine takes for a declared POVM rests on A-IDEAL: an ideal qubit measurement, on a transmitted system that is exactly a qubit, with unit efficiency, no loss, no dark counts, no multi-photon events and no misalignment. If your receiver is not such a measurement, A-IDEAL fails and the key length does not apply to it; declare it as an optical station (kind: optical) instead (instances/declared/README.md). | [record](record.md#p-.payload.protocol_document.user_declared.0) |

## <a id="appendix"></a>Appendix

### <a id="how-computed"></a>How the number was computed

The run was refused at its solve stage, so no key length was reported. The record holds no bound. The table holds what the record states.

| Result | Value |
| --- | --- |
| outcome | refused |
| refused at stage | solve |
| reason | security_statement_vacuous |
| detail | the \`parameters\` table: eps_PA + eps_EV + 2 eps_auth = 9.313225746154785e-10 + 9.313225746154785e-10 + 2\*0.5 = 1.0000000018626451 (formed exactly) >= 1, so the (eps_PA + eps_EV + 2 eps_auth)-security statement of [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security) (iii) -- at eps_auth = 0 the (eps_PA + eps_EV)-statement of (ii) -- is EMPTY: a distinguishing advantage bounded by one or more is bounded for every protocol, including one that publishes the key -- and NO KEY LENGTH IS REPORTED UNDER IT. [Corollary "Key length from any lower bound on the value"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:keylength-bound) (b) excludes this corner rather than claiming it: its proof records that ell = 1 satisfies the expression at eps_PA = eps_EV = 1 under a security statement that is empty. THE ARITHMETIC IS NOT IN QUESTION and is unchanged; THE RUN IS REFUSED. Every budget keeps its domain and the refusal is on their SUM ([Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous)). A DISCLOSED SCOPE NARROWING |
| rule | — |
| key length | — |
| net key length | — |
| rate per round | — |
| rounds | 10000 |
| Rényi order alpha | 1.5 |
| alpha chosen by | the declaration (parameters.alpha) |
| reported tier | — |
| security parameter | — |
| term eps_pa | 9.313225746154785e-10 |
| term eps_ev | 9.313225746154785e-10 |
| term eps_auth | 0.5 |
| authentication factor | 2 |
| completeness ε\* | — |
| key length reason code | — |
| reason text | — |

### <a id="security-claims"></a>Security claims

#### Per execution

- [Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions): One execution's parameter covers one run, and separate executions that share no key add their parameters ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)). A reused authentication key enters through ε_auth, charged twice, and the earlier run's parameter does not bound its distance in general.
- [Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions): N executions that share no key and no device state and leave their keys unused until all have ended, run against one adversary, are together (ε_1 + ... + ε_N)-secure for the joint ideal map. A key reused from one execution in another is not covered.

#### Limitations

- [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope): The completeness parameter ε\* of the statistics module bounds an honest run's failure of the acceptance test only. Aborts in error verification and in authentication are bounded by no claim, so ε\* does not bound the honest abort probability of the whole protocol.
- [Remark "The declared measurement as a premise of the rate"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:declared-measurement): A tiny change of the declared measurement can move the key rate by many bits per round, so the model is a premise of the rate. Where a handed reference's companion counts and the key length is formed on it, the snap only steers the search; nothing bounds model to device.
- [Remark "One execution's security parameter and a reused key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:repeated-executions): One execution's parameter covers one run, and separate executions that share no key add their parameters ([Corollary "Security parameters of separate executions add"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:separate-executions)). A reused authentication key enters through ε_auth, charged twice, and the earlier run's parameter does not bound its distance in general.

### <a id="checks"></a>Checks the engine ran

| Check | Outcome | Value | Claims | Record |
| --- | --- | --- | --- | --- |
| `snaps-within-tolerance` Instance snaps within the declared tolerance | not-applicable | — |   |   |
| `receiver-route` Receiver route | passed | — | [Definition "Compilation of a declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:compile) |   |
| `element-graph-acyclic` Declared element graph well formed | not-applicable | — | [Definition "Declared element graph"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:graph), [Requirement "Refusal of a graph that is not well formed"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/req:graph-refusal) |   |
| `probe-states-diagonal` Probe declaration admitted | not-applicable | — | [Definition "Probe declaration"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:probe), [Requirement "Admission of Gaussian-tier probe states only"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/req:probe-diagonal-admission) |   |
| `specification-well-formed` Specification well formed | passed | — | [Definition "Well-formed specification"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/def:well-formed-spec), [Theorem "Soundness, completeness and decidability of the validator"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:validator-soundness) |   |
| `compiler-gates` Compiler emission gates | passed | — | [Theorem "The emission gates and their outcomes"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:gates) |   |
| `exact-statistics-inputs` Acceptance-set inputs admissible | passed | — | [Requirement "Refusal of an input that violates a decidable clause"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/req:input-refusal) |   |
| `matched-alphabet` Acceptance alphabet matches the declaration | passed | — | [Requirement "Alphabet and round count taken from the consuming declaration"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/req:matched-alphabet) |   |
| `declaration-admitted` Declaration exactly admissible | passed | — | [Requirement "Exact admission of declared data"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:exact-admission) |   |
| `alpha-range` Rényi order of the key length | passed | — | [Requirement "Rényi order of a reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:key-length-alpha-domain) |   |
| `security-statement-not-vacuous` Security statement not vacuous | refused | stage = solve; reason = security_statement_vacuous | [Requirement "Refusal of budgets with an empty security statement"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:security-statement-not-vacuous) | [record](record.md#p-.payload.stages.solve) |
| `key-length-gate` Key-length security gates | not-reached | — | [Requirement "Two-part gate on a key length with declared constraints"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:constrained-key-gate), [Requirement "Source licence for a declared marginal"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:marginal-licence-gate), [Theorem "Constrained accumulation under the attack-set licence"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:constrained-accumulation) |   |
| `first-order-hypotheses` First-order hypotheses at the contributing iterates | not-reached | — | [Requirement "Withdrawal of the first-order bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/req:first-order-withdrawal), [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder) |   |
| `reported-key-length` Reported key length | not-reached | — | [Requirement "Reported key length"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:reported-key-length) |   |

### <a id="route"></a>Route, instance and preparation

#### Instance

| Instance | Value |
| --- | --- |
| id | bb84 |
| title | Ideal qubit BB84 |
| summary | Trusted-source BB84 with configurable basis weights, a directly declared qubit measurement and an explicit identity reduction link. The honest channel is depolarizing and is parameterized by its quantum bit error rate. This instance provides a simple reference for optical BB84 runs. |
| readme | [instances/bb84/README.md](../../../instances/bb84/README.md) |

#### Protocol document

| Document | Value |
| --- | --- |
| id | bb84 |
| format_version | 1 |
| packaged | true |
| digest | 017c81159da61e927d12a8c7699087e6a9282392beb7279e9d8a90f8625671ec |

#### Honest model

| Honest model | Value |
| --- | --- |
| note | — |
| tag | — |

#### Preparation

| Preparation | Value |
| --- | --- |
| input_preparation_pointer | — |
| snaps_pointer | — |
| declared_tolerance | 0.0 |
| snap_max_defect | — |
| snap_max_displacement | — |

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
| report_id | cc3c5893770dfd1689d32386a03fc87279ccea4b0f658292f07a5aaac4201d49 |
| record_schema_version | 0.46.0 |
| report_schema_version | 0.36.0 |
| created_by | runs.report_examples.generate |
| config_digest | 7494363dc330a4a87548791152025100bbf2ac40e316f3aa6eb07caa463ee6b1 |
| engine | distribution_version = 0.1.0; git_commit = da9eda22e78a438c7bc0dfa7fb8909b0065a132f; git_dirty = false |
| platform | — |
| final_iterate | — |
| reproduce | config_pointer = [record](record.md#p-.payload.config) |

#### Module versions

| Versions | Value |
| --- | --- |
| contracts | none |
| assumption_manifest | none |

#### Claim status

No claim status is listed: the run was refused before any result named a claim.

#### Solver and tolerances

| Setting | Value |
| --- | --- |
| config | max_iterations = 5; method = fw |
| solver_options | — |
| pointers | none |
| declared_tolerance | 0.0 |
| optimizer | — |
| group_b_worst_pointer | — |

#### Artefacts

| Stage | Station | Kind | Digest |
| --- | --- | --- | --- |
| compilation | — | transmitter_artifact | `467cf56ca0b1a5dae80b8322e483d76871f454b23205a2b25acf62732c3973df` |
| compilation | — | declaration | `0bba6be1b6cecc1a8c65e623cbd0e3191775f95d25b6756a1572a7c0a351d1dc` |
| honest_model | — | honest_distribution | `91700c4b665fb3385686fca8118fadd2b2d91c7908649a8d872ae5c190df25a7` |
| acceptance_construction | — | acceptance_set | `640e25dbda0673544e691e90828457cc3a8f5e60e3d026cb47421030fc81f8af` |
| docking | — | docked_declaration | `72fbe0d811b76b11db7b9feec0b14ef60861d139c4341f5395f6d2b564985582` |
| bundle_write | — | bundle | `72fbe0d811b76b11db7b9feec0b14ef60861d139c4341f5395f6d2b564985582` |
| bundle_read | — | bundle | `72fbe0d811b76b11db7b9feec0b14ef60861d139c4341f5395f6d2b564985582` |

### <a id="glossary"></a>Glossary

- <a id="g-a-the-letter"></a>A (the letter): The report uses the letter A in four ways: party A of the declaration (Alice); system A, the declaration's per-round letter on that party's side; a detector port named A (as among BBM92's ports H, V, D and A); and the prefix of a premise's short id (A-LAB, A-SPEC). Which is meant follows from where it stands. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-acceptance-test"></a>acceptance test: The test every run applies to its statistics: each round records one acceptance value, and the run continues only if the frequency of every value lies in an interval (together, the box) around the honest model's prediction. See [Definition "The construction map"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/def:construction).
- <a id="g-alice"></a>Alice: The name the report gives party A of the declaration. A party may send, measure, or both: in a prepare-and-measure protocol Alice usually sends, in an entanglement-based one she measures at a station; the run's record says which. Where a premise speaks of Alice's letter or of system A, it means the party the declaration assigns A to: Alice, unless the party partition says otherwise. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-band-a-route"></a>Band-A route: The direct route: a finite measurement declared on one sector, with no optical characterisation and no photon-number reduction. It needs an ideal qubit receiver (A-IDEAL), which no real optical receiver is.
- <a id="g-bob"></a>Bob: The name the report gives party B, the other of the declaration's two parties. Like Alice, he may send, measure, or both; on most protocols he measures at one or more stations. Which he does on this run is read from its record, which also says which party holds system A. See [Definition "The protocol declaration as the MEAT core reads it"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/def:declaration).
- <a id="g-budget"></a>budget: An error probability (an ε) that you choose before the run. The secrecy, error-verification and authentication budgets ε_PA, ε_EV and ε_auth make up the security parameter ε. The completeness budget ε_comp is not part of ε: it is the largest ε\* you allow and bounds only how often an honest run fails the acceptance test. The configuration keys keep the word (completeness_budget). See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-certified-bound"></a>certified bound: The first-order bound formed again at the solver's final points from the declared data, every arithmetic step exact or rigorously enclosed: a lower bound on h_low that rests on the claims and the modelling premises and on no premise about floating-point arithmetic. Where a run reaches it, the key length is computed from it, exactly. See [Corollary "Key length from the certified bracket"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/cor:certified-keylength).
- <a id="g-completeness"></a>completeness: How often an honest run, with no attacker and devices behaving as modelled, aborts. It never affects the security parameter ε, which holds for every abort pattern. See [Remark "Completeness covers the acceptance test only"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/rem:completeness-scope).
- <a id="g-constraint-entry"></a>constraint entry: A constraint a declaration places on the states it admits, beyond the declared marginal. A run whose declaration carries an entry you declared is checked by the statistics check unless that check is switched off (the inputs table says whether it ran); entries the compiler or a reduction derives do not by themselves call for it. See [Requirement "The check of the acceptance set against the feasible statistics"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/req:unreachable-acceptance-set).
- <a id="g-declared-tolerance-tau"></a>declared tolerance τ: The ceiling on the defects of the run's own data that the snap may repair before solving.
- <a id="g-detection-efficiency"></a>detection efficiency: The probability that a detector clicks on a photon that reaches it.
- <a id="g-digest"></a>digest: A hash that identifies the content of a file, an artefact or the configuration: the same digest means the same content.
- <a id="g-effective-status"></a>effective status: The lowest review status over a claim and everything it rests on; a claim accepted on its own is only as reviewed as its weakest premise.
- <a id="g-endpoint-rule"></a>endpoint rule: How the acceptance test sets the ends of each outcome's interval: the exact binomial quantile rule (exact) or the closed-form Bernstein rule (bernstein).
- <a id="g-estimate"></a>estimate: The value of the objective at the point the solver returned. It claims no bound: that point is feasible only within a window, so the estimate need not lie above the true minimum h_low. No key length is computed from it.
- <a id="g-first-order-bound"></a>first-order bound: A lower bound on h_low from the tangent planes of the objective at the solver's steps. Its proof is exact, and the minima it uses are bounded from below in exact arithmetic, not taken from the solver; its objective and gradient are computed in floating point with no bound on their numerical error. Stopping early makes it looser, not invalid. The key length uses it where the run is not certified. See [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder).
- <a id="g-frank-wolfe"></a>Frank-Wolfe: The solver's iterative method: each step minimises a linear approximation of the objective over the feasible set and moves toward that point. See [Theorem "The estimate and the first-order lower bound"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/frank-wolfe/thm:firstorder).
- <a id="g-honest-model"></a>honest model: The model of what an honest run looks like. It sets the acceptance test and the expected statistics; it never affects the security parameter ε, which holds for every abort pattern.
- <a id="g-k-auth"></a>k_auth: The bits of pre-shared key the authentication uses per run; the net key gain is ℓ − k_auth. See [Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth).
- <a id="g-kept-snap-block"></a>kept (snap block): A snap block is kept where your model gives it exactly on the grid, so the snap changes nothing there; every other block is moved.
- <a id="g-key-length-ell"></a>key length ℓ: The number of secret key bits one run outputs, after deducting error correction, error verification and the finite-size cost of secrecy. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-key-map-and-sifting"></a>key map and sifting: Sifting decides from the public announcements which rounds give key; the key map sends each kept round's readout to a key bit. See [Theorem "Announcement locality, sifting and party computability"](../../../spec/modules/protocol-compiler/contract.pdf#nameddest=claim-protocol-compiler/thm:sifting-and-key).
- <a id="g-net-key-length"></a>net key length: The key length minus the k_auth bits of pre-shared key the authentication consumed: what the run gains. See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-povm"></a>POVM: A measurement written as one positive operator per outcome; the probability of an outcome is the trace of its operator times the state.
- <a id="g-qber"></a>QBER: The quantum bit error rate: the fraction of key rounds in which the two parties' raw key bits differ.
- <a id="g-reference-snap"></a>reference (snap): Your declared receiver model, computed exactly (exact) or known through rigorous rational intervals (enclosed). The snap starts from it where it is exact, and the run hands it beside the snap so that the key length can be computed from it.
- <a id="g-reference-companion"></a>reference companion: Your receiver model put through the same reductions as the rounded measurement, without that rounding, its rows relaxed outward by their floating-point rounding and the model's intervals. A block not handed is carried rounded; with none handed, it is the reduction's exact construction before its own rounding. The run takes its first-order bound there and never solves it. See [Corollary "The reference companion of a reduction instance"](../../../spec/modules/reductions/contract.pdf#nameddest=claim-reductions/cor:reference-companion).
- <a id="g-round"></a>round: One use of the protocol as declared, which records its own outcomes. How a time-tagged system cuts its detection record into rounds (time bins, coincidence windows, how the stations synchronise) is your choice, and your declaration must describe it; What a round is, before the protocol's steps, names premises of this run that the cut bears on.
- <a id="g-setting"></a>setting: A probe setting of a receiver; "off" is the setting with no probe light. A receiver without a probe has this one setting only, so on such a station "setting off" names its one measurement, not a switch. See [Definition "Probe declaration"](../../../spec/modules/receiver/contract.pdf#nameddest=claim-receiver/def:probe).
- <a id="g-snap"></a>snap: Before solving, the declarer (your instance, or a reduction for what it emits) moves each measurement onto a grid of exact numbers of the same shape. A block your model gives exactly on the grid is kept; every other block is moved, and rests on A-SNAP unless it is evaluated off its snap.
- <a id="g-strict-option"></a>strict option: The run setting strict_snaps: on, the run refuses wherever a moved block or emission sector would rest on A-SNAP, and reports no key length that rests on it, and the certified evaluation does not fall back to the rounded measurement where your receiver model certifies no point; off, the default, such a block is disclosed. See [Requirement "Snaps of a measurement family: kept, or moved and disclosed"](../../../spec/modules/foundations/contract.pdf#nameddest=claim-foundations/req:snap-reference).
- <a id="g-alpha-r-nyi-order"></a>α (Rényi order): A parameter of the proof, not of your device: any value in (1, 2) fixed before the run gives a valid key length, and the choice changes only how long the key is, never its secrecy. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-eps-security-parameter"></a>ε (security parameter): The bound on how far one run's output can be told from an ideal key exchange: ε = ε_PA + ε_EV + 2ε_auth. It covers one execution. See [Corollary "Security of the protocol and its net key"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/cor:composed-security).
- <a id="g-eps-star-completeness"></a>ε\* (completeness): A bound on the chance that an honest run fails the acceptance test; it covers that test only, not later aborts in error verification or authentication. The completeness budget is the largest ε\* you allow. See [Theorem "The completeness bound"](../../../spec/modules/statistics/contract.pdf#nameddest=claim-statistics/binomial-box/thm:completeness-bound).
- <a id="g-eps-auth"></a>ε_auth: The error of the authentication of the classical messages, which you declare, including, for a key from an earlier run, its distance from an ideal key; it is counted twice in ε. Zero asserts a channel that is itself authenticated. See [Assumption "Authentication of the classical channel by a keyed scheme"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:auth).
- <a id="g-eps-ev"></a>ε_EV: A bound on the chance that both parties accept the run with different keys; error verification compares a hash of ⌈log₂(1/ε_EV)⌉ bits. See [Lemma "Correctness from error verification"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/lem:ev-correctness).
- <a id="g-eps-pa"></a>ε_PA: The secrecy error of privacy amplification: how far the key may be from uniformly random and independent of everything the attacker holds. See [Theorem "Secrecy of the key from the accumulated entropy"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/thm:keylength).
- <a id="g-lambda-ec"></a>λ_EC: The number of bits the error-correction transcript reveals; the key length deducts it in full. You declare it; with an estimate file beside the record the report shows how it was chosen. See [Assumption "Dedicated key register and one-way reconciliation"](../../../spec/modules/meat-core/contract.pdf#nameddest=claim-meat-core/ass:keyreg).
