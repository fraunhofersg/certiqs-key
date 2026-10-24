# Principles

This is the document every contributor, human or agent, reads first, and the
one every plan is aligned against. It says what the project wants and why; it
does not say how. The how is decided by whoever does the work, within these
principles. When a rule elsewhere in the repository conflicts with this file,
this file wins and the rule is the defect. This file changes in the open: a
change to it is a commit, accepted by the maintainer, whose message says why.

---

## 1. What we are building

A modular, extensible engine for **fixed-length key rates of practical
relevance**, computed with the marginal-constrained entropy accumulation
theorem (MEAT). It aims to be:

- **general** enough for complex protocols, imperfect and partially
  characterised devices, and high photon-number cutoffs;
- **practical**: its rates are competitive on realistic channels and round
  numbers, and a calculation finishes in a time a user will wait for;
- **trustworthy** enough that a result can be handed to a partner, an
  evaluator or a certification lab with its assumptions attached.

It serves researchers computing key rates for their own setups; vendors,
laboratories and evaluators who need a rate they can trace to its premises;
and the security-proof community, as an open reference implementation. Its
long-term trajectory is formal verification of the core theorem chain; today
the target is research-grade correctness under adversarial review.

## 2. Where trust comes from

1. **Every key rate carries its assumptions.** A result is a number plus a
   machine-generated record of the assumptions, module versions and claims it
   rests on, and a key-rate report that states each assumption in plain
   language and marks what the user declared rather than the engine derived.
   The engine proves the bound for the declared model; whether the model fits
   the device is the user's to vouch for, and the report says exactly what
   that takes. A result also names its tier. `certified` is the default
   headline: a key length that follows from the declared model and the claims
   alone, with every number between the prepared declaration and the key
   length exact or rigorously enclosed, so that no premise about
   floating-point rounding remains (the enclosing code and its interval
   library are reviewed, not proved). Where certification cannot cover a
   run, the result is the `first-order` number, reported with the reason;
   `estimate` is a diagnostic and never a key.
2. **Claims are reviewed adversarially by an independent party.** A claim,
   and the code that implements its mathematics, is verified by a reviewer
   that sees only the artefacts, never the drafter's reasoning, and that runs
   by default on a different model family from the drafter. Independent
   review is the process rule that has demonstrably caught errors that would
   have made an emitted key rate unsafe; it is not negotiable. A departure
   from the default reviewer is named for its batch and recorded with it.
3. **Numbers are checked against hand-derived oracles.** Reference values are
   derived independently from the statement, never regenerated from the code
   they test. The oracle registries and golden tests are the executable memory
   of every derivation and move with their module.
4. **Humans accept, agents propose.** Accepting a claim batch or an
   implementation batch, like every other project decision, is a human act,
   recorded by the commit that puts it into effect: the effect is written into
   the file it changes, and the commit message quotes the human and ends with
   a `Decided-by:` trailer. No agent writes that trailer for a decision the
   human did not make. Accepting a batch is a decision on the verifier's
   report and the batch's statements; it is not a human reading of every
   proof.
5. **Git plus human review is the ledger.** There is no second ledger: no
   receipt chains, no byte-pinned evidence, no forgery-resistance machinery.
   An accepted version is pinned by its commit; a run record pins what it
   used. A decision needs no log of its own: its effect is the text it
   changed and its reason is the commit (`git log --grep "^Decided-by:"`,
   `git blame`). Records of another kind, such as what a key-rate run used,
   are decided on their own merits.

## 3. How humans and agents work together

Most of the writing here, mathematics and code alike, is done by AI agents.
Agents are tireless at bookkeeping, review and tests, and weak at restraint
and at judging what serves the project. The process is built around both
facts.

- **Align first, then delegate.** Before a piece of work, the agent aligns
  with the human on the goal and the principle at stake; after that it makes
  the implementation decisions itself. Plans state intent, not procedures; a
  plan enforced after reality has moved is a defect.
- **Write down the intent agents cannot infer.** Practical relevance,
  runtime, and what a feature is for are stated where the work starts, not
  left to be guessed. An agent that cannot tell whether a thorough answer
  serves the project asks rather than pursues it.
- **Deviations are written down where they happen**: in the file they
  concern (a claim's notes, an open item, the spec section) and named in the
  commit message; never silently and never only in a chat.
- **Human attention is the scarce resource.** Agents produce far more than a
  human can read, so the process is designed to fit a few hours of human
  review a week. Review is batched: it happens when a milestone converges or
  when a claim's statement or proof changes, and escalation between sittings
  is used sparingly. What reaches the human is judgement: whether the stated
  assumptions and top-level claims match the intended protocol and devices.
- **What a human reads is tested on outside readers.** The README, the
  rendered contracts and the key-rate report are read by reviewers who
  play their intended audience (a newcomer, a theorist, an experimentalist,
  an evaluator) without the project's context, and where they stumble is a
  defect.
- **One human entry point.** `state/DASHBOARD.md` shows, in this order:
  decisions waiting on the human, ranked, each with a brief and a recommended
  option; the module and claim status map; open findings by severity.
  Everything else is one link deeper. `PRINCIPLES.md` and `spec/` are the
  documentation entry point.
- **Agents own the mechanical, humans own the judgement.** Machine checks
  verify form: labels resolve, edges resolve, citations are registered,
  symbols are declared. Whether an argument is sound is decided by a reviewer
  and a human, never by a tool.

## 4. Separations that must stay visible on disk

| Concern | Lives in | Changes |
| --- | --- | --- |
| Normative spec: principles, architecture, notation, contracts as claim files | `PRINCIPLES.md`, `spec/` | slowly; by human-accepted batch |
| Module code, the executable mathematics | `src/` | slowly, the longer the slower |
| Instances: one protocol's parameters, data and device model | `instances/` | often; this is where a user docks |
| Runs: composition, order, result records | `runs/` | often |
| Harness: tools, role files, checks | `harness/` | ordinary code review; never governed by a lifecycle of its own |
| State: dashboard, open items | `state/` | continuously; generated where a generator exists |
| Reports, analyses, reviews | `reports/` | dated, non-normative, deletable |
| Pinned references and working notes | `refs/`, `context/` | read-only; `context/` is never cited |

Imports point downward only: instances may import runs, runs may import
modules, modules import nothing above them. Normative text is never mixed
with commentary, and a report is never authority.

**Files state what is; history lives in git.** Specification, code, tests,
tools and documentation describe the current design and the reasons it has
its shape, stated so that they stay true. How it came to be (who decided
what on which day, earlier versions, the order of the work) belongs in commit
messages, in dated reports and in the history of an open item, and is
recovered with `git log` and `git blame`. A count is likewise never written
into normative prose: the prose names the command that computes it.

## 5. The claim model

- **One file per claim.** A theorem, lemma, proposition, corollary,
  definition, assumption, remark, example, requirement on the implementation
  or imported fact is one LaTeX file with its id, kind, status, the claims it
  `uses`, the assumptions it `assumes`, its registered citations, and, when
  one exists, the code symbol that implements it. Every claim file has a
  Lean-name field, empty until formalisation reaches it. The format is
  `spec/claim-format.md`.
- **Assumptions are leaves** with stable short ids (`A-...`); a claim may not
  rest on an assumption it does not declare, directly or through what it
  uses.
- **A module is a set of claim files plus an interface** (inputs, outputs,
  parameters, thresholds). The readable contract is assembled from the claim
  files; nothing is authored twice.
- **A submodule** (a squasher, a source model, a receiver family, a
  statistical box) is a small claim bundle whose claims use the core module's
  claims, reviewed like a module at its own scale. Instances are data, not
  claims.
- **The graph is declared in the files, checked for form, rendered for the
  human, and used to compute the re-review scope of a change.** It never
  refuses anything. It grows toward formal verification by attaching Lean
  names, not hashes.
- **No super documents.** A file longer than a human reads in one sitting is
  a defect to be split.

## 6. Lifecycle, as small as it can be

- Claim status: `draft`, `verified`, `accepted`, `implemented`, `superseded`.
  A claim's header status is its local judgement; its effective status, which
  the checker computes, is the minimum over its `uses` and `assumes` closure.
- Module version: bumped once per human-accepted batch, naming the batch.
- Two human gates, both at a sitting: **accept** (a claim batch) and
  **accept-implementation** (a code batch, with the implementation
  reviewer's report and the tests green).
- Three amendment routes:
  - **editorial**: `harness/math_diff.py` shows that no claim statement or
    proof changed; no review.
  - **presentational**: statements and proofs are rephrased or restructured,
    or claims split, merged, relabelled or re-kinded, with the mathematics
    unchanged. An editor rewrites, and an equivalence reviewer on artefacts
    only certifies, reading `math_diff`'s report, that no mathematics
    changed. Claims keep their status; the module version is bumped once for
    the batch, which the human accepts.
  - **substantive**: dependents computed; one reviewer round on that closure;
    accepted at the next sitting. The amended claim drops to the status its
    new review gives it; its dependents keep their header status and their
    effective status follows, so there is no cascade of status edits.

  Non-normative summaries, lead-ins and abstracts follow the editorial route
  when only that prose changes. How they are kept apart from the mathematics
  is `spec/claim-format.md`; how contracts read is `spec/style.md`.
- Reviewer rounds are bounded (three by default); exhaustion queues the item
  for the next sitting instead of halting the module.
- Submodule review rides the next sitting; it has no gate of its own.

## 7. The harness

- **Process must earn its cost.** Agents do not tire of bookkeeping, which
  makes thorough review affordable and also removes the natural brake on
  process growth. The harness exists to serve the mathematics and the code;
  when it starts to outgrow them, it is cut back.
- **Every tool states its motivation in its own header**: the concrete
  question it answers or the error class it catches, ideally one that has
  already occurred. `harness/README.md` lists every tool with that
  motivation. A tool without a written motivation is removed.
- **The harness is ordinary code**: reviewed like code, tested like code,
  never subject to gates, locks or successors of its own.
- **Prefer generated views over maintained ones.** The dashboard, the claim
  graphs, the contracts, the bibliography and the queue are generated; a
  hand-maintained mirror of anything is a defect.
- **Open items are tracked** in `state/open-items/`, one file per item, with
  owner, severity, module, claims touched and what would close it; the human
  half is what needs a decision, the agent half is what does not.

## 8. Citation and evidence

- Cite only registered reference ids with locators (`<ref-id>, Thm./Eq. <n>`);
  the registry `refs/index.json` pins each source. A quoted import is checked
  against the pinned source itself, never against an extraction or a note.
- Working notes in `context/` are evidence, never authority; an idea taken
  from one is derived in full in a claim file and tagged `newly-derived`.
- Provenance on every claim: `published` (with locator) or `newly-derived`.

## 9. Design approaches

- **Practical results come first.** A computed key rate must be of practical
  relevance: positive and competitive where the physics allows it, for
  realistic devices, channels and round numbers, in a runtime a user accepts.
  Soundness is never traded for speed; the two are reconciled by where the
  rigour is applied. A new feature that affects what runs is benchmarked on a
  realistic protocol, before it is built where its cost is in question and
  again before it is accepted.
- **Search fast, certify after.** The optimisation runs in binary64, where
  it is fast; exactness enters only where it decides the result. Inputs are
  prepared once into exact declarations, and the bound is certified a
  posteriori at the few points that set the key length, by exact and
  rigorously enclosed arithmetic, at a small fraction of the run's cost.
  Exactness pursued where it does not reach the key (an effect many orders
  of magnitude below the uncertainty of the device characterisation it
  feeds) is cost, not rigour.
- **Complexity must earn its ongoing cost.** A change that adds maintenance
  work, runtime, or friction for later changes is justified only when its
  expected benefit clearly outweighs those costs over its useful life. Count
  human review effort, duplicated information and the risk of staleness,
  dependency upkeep, performance, and how hard the change is to remove, not
  only the effort to build it. Prefer the simplest approach that meets the
  correctness and usability needs, and state the concrete benefit and the
  recurring cost in the implementing commit; this creates no separate report,
  checklist or approval gate.
- **No compatibility tax before a stable release.** Until a stable release
  is declared, early research releases included, an interface, record shape,
  instance or code path may be changed or removed without a deprecation path
  or a parallel old route; a change that breaks a caller updates it in the
  same batch. Numbers stay governed by §2.3: a change that moves a pinned
  number names it, and its oracle is re-derived by hand.
- **User-facing inputs are ordinary numbers.** Supported entry points accept
  ordinary numeric inputs and prepare them for the core through shared,
  documented conversion and snapping rules; users never construct exact data
  themselves. Preparation records the prepared values and their
  displacement, preserves normalisation and bound directions, and accounts
  for every perturbation the proof needs. Core modules validate the prepared
  declarations exactly.
- **Clear piping.** A module boundary is a pure function over serialisable,
  versioned artefacts, so a command line, an API or an MCP endpoint is an
  adapter over the run tier, never on the proof path.
- **Build with formal verification in mind.** Claim files are the informal
  blueprint; Lean names attach to them; nothing in the structure has to
  change when formalisation begins.
- **Learn from prior art** (Lean blueprints, RFC and ADR governance,
  assurance cases) and from this project's own history; do not re-derive a
  process that exists.
- Operators are sector blocks, and each instance declares one tolerance
  (stated in the `foundations` contract).
- Squash first, then optimise: proof reductions are applied before the
  entropic step.

## 10. Scope: deliberately not built

Formal proofs are the long-term target the design is built for (§1, §9):
claim files are the blueprint that Lean names attach to, and none is built
yet. Digital-twin statistics and variable-length protocols are not built now;
`spec/future-scope.md` keeps such directions apart from the backbone. A
parallel exact engine is not built either: certification checks the
floating-point search, it does not replace it (§9). Moving anything out of
this list is a human decision, recorded as §2.4 says.
