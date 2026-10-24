# Contract style guide

This guide governs the prose of the contracts: claim files, module and section
metadata, `design.md`, `interface.yaml` comments and the other documents under
`spec/`. The file format is `spec/claim-format.md`; this guide says what goes
where and how it reads. The checker enforces the mechanical part of it (marked
**[checked]** below, specified in `spec/claim-format.md`, the separation
rules among them as its check 13). The rest is applied
by the editor role (`harness/roles/editor.md`) and judged by reviewers and the
maintainer.

The drafter writes mathematics first. Following this guide is the editor's
job, run on demand; a drafter who follows it saves that pass, but is not
required to.

## 1. The reader

Write for a QKD theorist who knows entropy accumulation, MEAT and finite-key
analysis but not this repository. That reader opens one section, reads its
introduction, the summary lines and the statements, and should come away
knowing what the section establishes and under which assumptions, without
reading a proof. Everything else in this guide serves that reader.

## 2. Where content goes

| Element | Belongs there | Does not belong there | Why |
| --- | --- | --- | --- |
| Module overview (`module.yaml: abstract`, plain text) | what the module establishes; its inputs and outputs; its main results by name; the scope limits a reader must know first | history, process, how the module was built | the first page a reader sees |
| Section introduction (`reading_groups[].abstract`, plain text) | the section's storyline, its key idea, its main result via `[[label]]` | anything a proof relies on | a reader who jumps to one section needs orientation |
| Claim summary (`summary`, plain text) | the result in words, then its consequence | TeX, chains of caveats, meta verbs ("Exhibits", "Explains") | it is reused in the index, the main-results page, the graphs and other plain-text views |
| Claim lead-in (TeX before `\begin{...}`) | motivation, the key idea, the link to the previous claim | `\label`, definitions, anything a proof cites | connecting prose without polluting statements |
| Definition | objects and notation; immediate properties with a one-line reason; `\term{...}` on each defined term | results that need a proof (these become lemmas); an `assumes` entry (the claims that rest on the premise declare it) **[checked]**; a `uses` edge to a remark or a requirement, and a pointer to a remark, requirement or example in its statement **[checked]** | a definition fixes meaning; it asserts nothing that could be false |
| Assumption | its conditions only, as clauses (i), (ii), …, each one checkable condition; in its header its `category`, `affects` and `user_statement` **[checked]** and, for a member of a family, `refines` | lists of claims it supports (generated backlinks replace them), and any reference to a claim other than a definition or the assumption it refines **[checked]**; what fails if it is violated (a fact about its consumers, carried by `affects` and the graph); when it is emitted (`interface.yaml`); interpretation (a remark); definitions; engine behaviour (a requirement); the sentence on whether the engine verifies it (it is generated) | the reader must be able to decide whether it holds |
| Statement (theorem, proposition, lemma, corollary) | hypotheses and conclusion | motivation, emphasis, repository paths, code identifiers, history; pointers to remarks, requirements and examples **[checked]** | a statement is read as mathematics and nothing else |
| Proof | the complete argument; for a long proof an "Idea." paragraph first and named steps | rationale, commentary about the proof, history | every step stays, so the contract remains a blueprint for formalisation |
| Remark | sharpness, counterexamples, special cases, relation to the literature, a brief guard against a plausible misreading | design rationale, engine rules, inventories, history; an `implements` binding **[checked]** | remarks are mathematics about mathematics |
| Requirement (`req`) | what the implementation must do or refuse, with a link to the result that motivates it | proofs, history | engine behaviour is normative for code and gets its own part |
| Example | a worked instance | counterexamples (these become remarks or propositions) | — |
| Fact | an imported published result in this repository's notation, with a descriptive title | a bare citation as the title | — |
| `notes` header | a current caveat a future drafter needs ("the statement is deliberately weaker than X because Y") | history, decision quotes, review logs | git and `reports/` hold history |
| `design.md` | rationale, rejected alternatives that are still relevant, the main-logic flowchart, limitations, the mapping to code | batch logs, defect lists (these are open items), reading lists for reviewers | non-normative explanation beside the contract |
| `interface.yaml` | the machine-readable interface; comments that explain fields | comparisons with an earlier version or repository, decision quotes, hand-kept copies of the claim graph | it is read by code and tests |
| architecture, notation, claim-format, future-scope, `modules.yaml` | the current state | revision history; a rule a claim relies on (that rule is a claim) | contracts are self-contained |

Nothing under `spec/` cites `reports/`, `state/`, `tmp/` or `context/`
**[checked]**, and nothing names a person: a human decision is attributed to
"the maintainer" where attribution matters, and otherwise not at all.

"Why the engine does X" is one sentence in the contract (a lead-in, a remark,
or a requirement's motivation) and the full reasoning in `design.md`.

## 3. The page, claim by claim

A claim appears in this order: its summary (one grey italic line); its
lead-in, if any (grey); the environment, opening with its number and title;
for an assumption, the generated sentence on its verification, where §3.8
says (grey); for any claim with a `user_statement`, its reading (grey); a
generated meta line (uses, used by, assumptions, source, status, code); the
proof. Grey text is non-normative; the front matter says so once, and
nothing repeats it.

A result, remark or requirement may carry a `user_statement`: a reading of
it for a user who is not a proof expert, such as an experimentalist or a
certification lab reading a key-rate report, saying in plain words what it
guarantees or warns about. It is exact about what is and is not promised,
never stronger than the statement, and says why a quantity matters rather
than how it is computed; a definition carries none **[checked]**. Statements of every kind are set upright, because italic
belongs to the non-normative summary.

### 3.1 Titles

A descriptive noun phrase in sentence case, positive, at most 70 characters
**[checked]**: "Instability of the rate under measurement perturbations",
"Concavity on the positive cone", "Key length from a lower bound on the
rate". No claim codes of the internal test registries under `tests/oracles/`
(C5, PC9, RC8, SA5) **[checked]**; no TeX outside `$...$`, so "Rényi" is
written with its accented letter, and inside it only symbols the plain title of the bookmarks
and graphs renders ($\varepsilon$, $\ge$, $\min$; not a project macro)
**[checked]**; no questions,
no "Why…", no negations where a positive phrase exists. The header `title` is
the only title; the environment carries none **[checked]**. Section titles
follow the same rule. A label carries no such code either.

### 3.2 Summaries

At most two sentences and 300 characters **[checked]**: the result in words,
then its consequence or role. Plain text; Unicode symbols from the mapped set
are allowed (α, ε, ≤, ⊆, ρ) **[checked]**; no TeX. Start with the content,
not with a verb about the claim.

- Avoid: "Exhibits nearby exactly admissible measurements with a large gap in
  the computed rate within the stated binary64 representability limits."
- Prefer: "Two exactly admissible measurements within ε of each other can
  have rate bounds α/(α−1)·N bits per round apart, for every positive
  integer N ≤ 53 + log₂ε (up to 52). Closeness of declared data therefore
  never carries a key-rate claim over to a nearby declaration."

A summary may name another claim with `[[label]]` or `[[module/label]]`
**[checked]**; it renders as a linked "Proposition 7.3".

### 3.3 Lead-ins

Optional, and short: one paragraph that motivates the claim, gives its key
idea or links it to the claim before. Mathematics is welcome. A lead-in
contains no `\label`, no numbered display and no `\term` **[checked]**, and it
asserts nothing a proof cites: if a proof would need it, it belongs in a
statement, a proof or a definition. Nothing follows the proof or the
environment **[checked]**.

### 3.4 Statements

Hypotheses, then conclusions. Nothing that a reader could mistake for a
further condition, and nothing that is not one: interpretation goes to a
remark, motivation to the lead-in, design consequences to `design.md`. A
statement points at no remark, requirement or example, and a result or
definition does not rest on a remark or a requirement in `uses`
**[checked]**: a pointer goes to the lead-in or the proof, or is dropped where
the target's "Used by" line already links back, and an argument a result
needs is stated as a lemma. No
`\textbf`, `\texttt`, repository paths, file names or code identifiers
**[checked]**; refusal strings and interface keys appear only in requirements.
Enumerate clauses with (i), (ii), … and keep one assertion per clause.

### 3.5 Proofs

Keep every step. Rephrase and restructure freely: open a long proof with an
"Idea." paragraph, split it into named steps ("Step 1 (reduction to one
sector)."), extract a self-contained step as a lemma. Cut commentary about the
proof ("two steps deserve naming because…") and never replace a justification
by "clearly" or "standard".

### 3.6 Remarks

A remark says something mathematical about the claims around it:
sharpness, a counterexample, a special case, the relation to a published
result, or a brief guard against a misreading that a competent reader might
actually make. One topic per remark. A misreading guard is one or two
sentences, not a catalogue. Rationale goes to `design.md`; engine behaviour
becomes a requirement; an inventory of claims is a generated view, not a
remark. A remark carries no `implements` and is never `implemented`
**[checked]**: the code binding belongs to the requirement, definition or
result whose object the symbol computes.

### 3.7 Requirements

A requirement states, as an obligation on the implementation, what the engine
must do, record or refuse ("The engine refuses a declaration that is not
exactly admissible."). It cites the result that motivates it and may name the
refusal string or interface key it binds (`\iface{...}`). One rule per
requirement: a remark that lists five rules becomes five requirements.
Requirements are Part II of a contract and carry `implements` once code
exists.

### 3.8 Definitions, assumptions, examples, facts

A definition marks each term it defines with `\term{...}`, which feeds the
index of defined terms; a term is defined once per contract. An assumption states
its conditions and nothing else: clauses (i), (ii), …, each one checkable
condition, referencing only definitions and the assumption it refines.
What its failure puts at stake is a fact about the claims that use it, so it
is not written into the assumption; `affects` records it and the graph
names the consumers. An optional lead-in explains the mechanism without
naming a claim. Its header carries the component it is about
(`category`), what its failure puts at stake (`affects`), the assumption of
its family it narrows (`refines`, where there is one), the roles a run must
have for its text to hold (`presupposes`, where it has any) and a longer
plain-text reading a user checks against their setup (`user_statement`,
non-normative; the statement wins); all but `refines` and `presupposes` are
required, and a role word in the plain texts is presupposed or conditioned
**[checked]**. The contract prints a generated sentence on
whether the engine verifies it, from `verification`, after the statement,
and its body does not repeat that sentence; a `user_statement` follows as a
grey "Reading:" paragraph; the meta line names the category, `affects` and
`refines` that are present. An example
is a worked instance; a fact quotes a published result character for
character in this repository's notation, with the hypothesis check in the
body.

## 4. Sections and modules

A section is a reading group. It opens with its introduction (two to six
sentences, plain text): what the section does, the idea that carries it, and
which result is its main one. Order claims so that each section reads
forward: definitions, then the main result and what supports it, then
remarks. Assumptions close Part I; requirements form Part II
**[checked]**. A section of more than about twenty claims is probably two.

The module overview (five to eight sentences) says what the module
establishes, from what inputs, with which main results, and the scope limits
without which a result would be misread.

## 5. Prominence

Every claim has `prominence` **[checked]**:

- `main`: the one to five most important results of a core module, the
  results its overview names as what the module establishes; a submodule
  may add up to two of its own. Choose them in this order: a root of
  `CLAIM_ROOTS` or a claim a run record names (not everything in a root's
  closure); a result that states a rate, key or entropy bound a reader would
  quote; a result another module or a run consumes as this module's output;
  the theorem the module exists to prove. Every core module has at least one.
  Main results are framed, listed up front by number, title and summary with
  their assumption closures, and named in their section's introduction.
  Never a remark or an example **[checked]**.
- `technical`: a computational step that only its neighbours use. It gets a
  lighter heading and is left out of the statements-only digest.
- `standard`: everything else.

## 6. References

- Within a contract: `Proposition~\ref{prop:x}`, with the kind written out.
  Tell the reader why the reference matters ("by the concavity of the branch
  functional, Lemma~\ref{lem:x}") rather than stacking bare numbers; no bare
  "above" or "below".
- Across contracts: `\xref{module/label}` only **[checked]**; it renders the
  target's kind and title with a link into the other contract.
- In plain-text fields: `[[label]]` **[checked]**.
- A repository document, where one must be named at all:
  `\repodoc{path#anchor}` **[checked]**, never a `\texttt` path.
- Defined terms: a definition marks each phrase it defines as
  `\term[<gloss>]{<phrase>}`, the gloss one plain line saying what the thing
  is (it fills the contract's Terms table). In each section the first use of
  a multi-word defined term, this contract's or a dependency's, is
  `\tref{<phrase>}` (or `\tref[<phrase>]{<inflected text>}`), which links it
  to its definition **[presentation]**; link a single-word term where a
  reader would otherwise not know it is defined. Repository jargon is a
  defined term or plain English, never an undefined phrase.
- No counts of tool output in normative prose (`spec/claim-format.md` §4.5).

## 7. Language

- British English; "we" for choices of the text ("we write N for …"); present
  tense. The engine is a grammatical subject only in requirements.
- One term per concept. House terms (source mode, key-live, key-inert,
  licensed constraint, exactly admissible) are defined once with `\term` and
  used unchanged. Avoid jargon that has a plain equivalent: "fail-closed"
  becomes "refuses", "docking point" becomes "interface", "load-bearing"
  becomes "used by". "Snap" is not jargon but a defined term
  (`foundations/def:snap`), linked to its definition as §6 says.
- No history and no process: no "formerly", "retired", "at the move",
  "version 1", review rounds, finding codes, dates, batch names or sittings.
  State the current mathematics; git holds the rest.
- Emphasis: `\emph` for the occasional word that carries the contrast,
  `\term` for definitions, never `\textbf` in a statement. Em-dashes
  sparingly; a sentence that needs two is usually two sentences.
- Condition tags used across claims get descriptive names, such as
  (H-SUPP); tags local to one claim stay (i), (ii).

## 8. A worked example

Before: the proposition "No uniform robustness" carries in its statement a
bold paragraph on the number model, a pointer to a paragraph elsewhere, the
design consequence ("that is why this module takes no tolerance"), a
defensive paragraph ("stated so that the proposition is not read for more
than it proves") and the α ≥ 2 caveat. Its companion remark begins with a
derivation outside any environment and ends with a rejected design
alternative.

After:

- **Title:** "Instability of the rate under measurement perturbations"
  (`prominence: standard`).
- **Summary:** as in §3.2.
- **Lead-in:** "One might admit a declaration whose operators are only close
  to exact ones, with an error allowance depending on the distance. The
  following proposition shows that no allowance of that kind can be useful."
- **Statement:** the hypotheses ($\alpha>1$, $B>0$, $N=\lceil B\rceil$,
  $\epsilon\in(0,\tfrac12]$ with $2^N\le\epsilon\,2^{53}$; the proof builds
  its families at the largest power of two at most $\epsilon$),
  then (i) the existence of the two exactly admissible families at distance at most
  $\epsilon$ with gap at least $B$, on data whose dimensions do not depend on
  $B$ or $\epsilon$; (ii) the non-existence of an allowance below
  $\frac{\alpha}{\alpha-1}N$; (iii) for $\alpha\in(1,2)$, the key lengths
  differ by at least $nB-1$ bits when the smaller is positive. Nothing else.
- **Remark "The representability ceiling":** why $2^N\le\epsilon\,2^{53}$
  forces $N\le52$ and that $N=52$ is attained, moved from the loose paragraph
  into the remark; the ceiling belongs to the number model, not to the map
  $\{F_v\}\mapsto\hlow$.
- **Remark "Scope of the perturbation gap":** what the instance does and does
  not show (no defect is involved; the gap lives in the statistics penalty; the
  direction of the gap is not controlled; an allowance of at least
  $\frac{\alpha}{\alpha-1}\cdot53$ is neither exhibited nor ruled out; at
  the instance's $d_Z=1$ it exceeds the entropy-part ceiling
  $\log_2|\Zset|=1$ bit per round, and it would be useless against a key
  rate below one bit; the comparison at $\alpha\ge2$ has no key-length
  reading).
- **Requirement "Exact admission of declared data":** the engine admits a
  declaration only if it is exactly admissible, motivated by the proposition.
- **design.md:** why the proposition is stated over binary64 families rather
  than real-valued ones.
