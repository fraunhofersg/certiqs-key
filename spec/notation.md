# Notation Reference — Curated Symbol List

```yaml
status: current
version: 0.13.0
pinned_by: each module's notation_version field in spec/modules/<id>/module.yaml
macro_file: spec/macros.tex   # part A is this catalogue's executable form
sources:
  - "the number model: spec/modules/foundations/claims (def:tolerance,
    def:binary64, def:exact-admissibility)"
  - "section 3.10: spec/modules/transmitter/claims,
    spec/modules/transmitter/decoy/claims and spec/modules/reductions/claims"
  - "section 3.11: spec/modules/protocol-compiler/claims,
    spec/modules/meat-core/claims and spec/modules/meat-core/frank-wolfe/claims"
  - "section 3.12: spec/modules/foundations/claims (def:binary64,
    def:sector-map)"
  - "section 3.13: spec/modules/foundations/claims (def:round-model)"
  - "section 3.14: the claims each of its rows names"
  - "section 3.15: spec/modules/foundations/claims
    (cor:least-eigenvalue-over-enclosure, lem:matrix-function-perturbation),
    spec/modules/meat-core/frank-wolfe/claims (cor:certified-keylength) and
    spec/modules/receiver/claims (def:enclosed-weight, thm:enclosed-weight)"
```

This is the single curated notation reference of this repository: **the symbol
catalogue every claim file writes against**. A claim uses a symbol listed here
with exactly the meaning given here, and `spec/macros.tex` is the catalogue's
executable form — its **part A** is the macros listed here, copied verbatim
(§1 names the catalogued macros that part B holds instead).

**How its version moves.** Each module pins the version it is written against
as `notation_version` in its `module.yaml`. A change to a **part A** entry (a
macro's name, its expansion or its Meaning) or a new row of §3 bumps the
`version` above, and a module pinned to an older version is re-checked against
a changed part A entry before it is treated as current; an editorial change
that touches no part A entry does not bump it. A change here is proposed and
accepted like every other change under `spec/` (`PRINCIPLES.md` §2.4).

---

## 1. How to use this document

**Claims must use these symbols.** Every symbol a claim uses that is defined
here must be used with exactly the meaning given here. A claim may declare
*document-local deltas* — additional symbols it needs that are not in this
file — disclosing them where it uses them, but it must **never redefine a
symbol listed here**. If a module needs a different meaning for a listed
symbol, that is a signal to amend this document (with a version bump), not to
shadow it locally.

**Macro file.** In this repository the LaTeX view of this document is
`spec/macros.tex`. Its **part A** is the macros this document catalogues,
copied verbatim: changing one of them is a notation change and takes a version
bump here. The catalogued macros marked *(local)* in the tables below are the
exception: `spec/macros.tex` defines them in part B, in the `meat-core` group,
and the rule on part A entries binds them all the same. Its
**part B** holds the module-local macros, grouped by module. No claim file and
no generated contract defines a macro of its own: `harness/assemble_contract.py`
writes the preamble and inputs the one file.

**Module-local macros are not catalogued here, and are prefixed when two modules
disagree.** A module may need a symbol this document does not list; it lives in
part B, it never redefines a part A macro, and §5.1's rule stands — a symbol
absent from §3 is put to the maintainer, not invented. Where two modules spell the same
macro name with **different** expansions, both are kept under a module prefix
and neither module writes the bare name: `\redChain` ($\mathfrak{C}$, the
reduction chain) against `\pcChain` ($\mathfrak{R}$, the two-segment chain the
protocol compiler consumes, with $\mathfrak{R}_{\mathrm{src}}$ and
$\mathfrak{R}_{\mathrm{rec}}$ built on it), and `\redNmsm` ($\mathcal{N}$, a POVM
measurement channel) against `\pcNmsm` ($\mathcal{N}_{\mathsf A}$, Alice's
measurement channel, which the transmitter writes). Two further module-local
readings are disclosed rather than catalogued: the compiler writes its
setting-dependent public choice as $N_{v,f}=P(f\,|\,t(v))\,F_v$ over the support
of $P$, and it writes the **generic** setting and choice alphabets inline as
$\mathcal{T}$ and $\mathcal{F}$ — deliberately not `\Tset` and `\Fset`, which
are optical-profile symbols of §3.7 and are not used by a declaration-level
contract.

**LaTeX preamble requirement.** The importing document must load `amsmath`,
`amssymb`, `amsfonts`, `mathtools`, `dsfont`, `braket`, and `physics` — with
**`braket` before `physics`**, so that `physics` wins for `\ket`, `\bra`,
`\ketbra`, `\dyad`, `\tr`, `\Tr`. The assembler's preamble loads them in that
order and imports the macro set with `\input{../../macros}`, read from
`spec/modules/<id>/`.

**Reading the tables.** Macros that take arguments are shown expanded with a
representative argument (e.g. `\Hs{A}` rendering as $\mathcal{H}(A)$). A
backslash-pipe `\|` inside a table cell is a Markdown escape for a literal `|`.
A macro name marked *(local)* is in `meat-core`'s group of `spec/macros.tex`
part B; the others are in part A (see the macro-file paragraph above). Both are
in the one file every generated contract inputs, so the mark does not decide
where a compile finds the definition. A Meaning cell is printed in the
notation table of each contract that uses its symbol, so it is plain: no
bold, no pointer to a section of this document, and a claim named as
"module Kind. `label`" so that the table links it
(`harness/check_symbols.py` checks the three).

---

## 2. Conventions

These structural rules govern how symbols combine, and they are as binding on a
contract as the symbol tables.

### 2.1 System label → Hilbert space → operators → states

Physical and information-carrying degrees of freedom are labelled by capital
letters $A, B, C, \dots$, called **system labels**. A system label determines a
chain of objects:

$$A \;\longrightarrow\; \mathcal{H}(A) \;\longrightarrow\; \mathcal{L}(A) \;\supseteq\; \mathrm{Pos}(A) \;\supseteq\; S_{\leq}(A) \;\supseteq\; S_{=}(A)$$

- $\mathcal{H}(A)$ is the (possibly infinite-dimensional) Hilbert space of $A$;
- $\mathcal{L}(A)$ is the space of bounded linear operators on $\mathcal{H}(A)$,
  and $\mathcal{L}(A,B)$ the space of linear maps $\mathcal{H}(A)\to\mathcal{H}(B)$;
- $\mathrm{Pos}(A)\subseteq\mathcal{L}(A)$ are the positive semidefinite operators;
- $S_{\leq}(A)=\{\rho\in\mathrm{Pos}(A):\mathrm{tr}(\rho)\leq 1\}$ are the
  **subnormalized** states;
- $S_{=}(A)=\{\rho\in\mathrm{Pos}(A):\mathrm{tr}(\rho)=1\}$ are the
  **normalized** states, also written $\mathrm{D}(A)$.

The identity on $\mathcal{H}(A)$ is $\mathds{1}_{A}$.

### 2.2 Composite systems and the direct-sum convention

Juxtaposition $AB$ is the tensor product, $A\oplus B$ the direct sum, at the
level of Hilbert spaces. The direct sum needs care, because
$\mathcal{L}\big(\bigoplus_z\mathcal{H}(A)\big)\neq\bigoplus_z\mathcal{L}(A)$:
the left-hand side includes off-diagonal coherence blocks; the right-hand side
contains only the block-diagonal operators and is a proper subspace.

> **Convention (⊕ of labels means block-diagonal operators).** A direct sum of
> *system labels* always means the block-diagonal operators: the label
> $\bigoplus_z A$ is identified with the operator space
> $\bigoplus_z\mathcal{L}(A)$, and likewise for $S_{\leq}(\cdot)$,
> $\mathrm{Pos}(\cdot)$, etc. For $n$ identical copies:
> $\mathcal{L}(A)^{\oplus n}$.

**Classical systems.** A classical system $Z$ over a finite alphabet is the
special case where every summand is one-dimensional; a classical state is a
probability distribution $\sum_z p_z\dyad{z}_Z$, and attaching $Z$ to a quantum
system under block-diagonal restriction identifies
$\sum_{z} X_z\otimes\dyad{z}_Z \longleftrightarrow \bigoplus_{z} X_z$.

### 2.3 States carry systems as **subscripts**; ∧ vs. |

States are $\rho,\sigma,\tau,\omega,\nu$ and **always carry their system as a
subscript**. *States are the only object whose system label is a subscript* —
operators use a superscript (§2.5). For a cq state on $XA$:

$$\rho_{XA} = \sum_{x} \dyad{x}_X \otimes \rho_{A\wedge x} = \sum_{x} p_x\, \dyad{x}_X \otimes \rho_{A\vert x}$$

- **Event ("and") component** $\rho_{A\wedge x}\in S_{\leq}(A)$, with
  $\mathrm{tr}(\rho_{A\wedge x})=p_x$ — subnormalized, keeps the weight;
- **Conditional state** $\rho_{A\vert x}=\frac{1}{p_x}\rho_{A\wedge x}\in S_{=}(A)$ —
  normalized, weight removed.

For an event $\Omega$: $\rho_{A\wedge\Omega}=\sum_{x\in\Omega}\rho_{A\wedge x}$
with $\mathrm{tr}=\Pr[\Omega]$.

> **Mnemonic: $\wedge$ keeps the weight, $|$ removes it.**

### 2.4 Sector decompositions and block restrictions

The platform's receiver space carries a **declared sector decomposition**
$\mathcal{H}(Q)=\bigoplus_{s\in\mathbb{S}}\mathcal{H}(Q_s)$ with orthogonal
sector projectors $\Pi_s$ (meat-core, Def. `def:declaration`). The
photon-number decomposition of the optical profile —
$\mathcal{H}(C)=\bigoplus_{n}\mathcal{H}(C_n)$ with projectors $P_n^{C}$,
cutoff blocks $C_{\leq N}$, $C_{>N}$ — is the canonical *instance* of this
convention, not a separate one.

> **Convention (block restriction).** For a block-diagonal operator $M$:
> - the **operator block** is a parenthesized superscript,
>   $M^{(s)}\in\mathcal{L}(Q_s)$ (profile instance: $M^{(\leq N)}$, $M^{(>N)}$,
>   $M^{(=n)}$), so that $M=\bigoplus_s M^{(s)}$;
> - the **state block** generalizes the event notation:
>   $\rho_{\wedge s}$ (profile instance: $\rho_{C\wedge n}$) is the
>   subnormalized component in the block.

Three caveats a contract must respect:

1. $\rho_{C\wedge n}=P_n^{C}\rho\,P_n^{C}$ is **not literal**: the two sides
   live on different spaces ($S_{\leq}(C)$ vs $S_{\leq}(C_n)$) and agree only
   after the inclusion isometry.
2. **Blocks capture only the diagonal part.** $\rho=\bigoplus_{s}\rho_{\wedge s}$
   holds only for block-diagonal states; in general it recovers the dephased
   (sector-pinched) state.
3. **Compressed ≠ projected.** $P_{\leq N}M P_{\leq N}\in\mathcal{L}(C)$ versus
   $M^{(\leq N)}\in\mathcal{L}(C_{\leq N})$ act on different spaces.

### 2.5 Operators carry systems (and blocks) as **superscripts**

All operators carry their system label(s) as a superscript:
$M_y^{C}\in\mathcal{L}(C)$, $M_x^{A}\in\mathcal{L}(A)$. Block restrictions go
in the same slot: $F_v^{(s)}$, $M_y^{(\leq N)}$,
$(M_y^{CL})^{(>N)} = M_y^{C_{>N}L}$. The superscript is dropped when the
system is clear from context (meat-core writes $F_v$, $M_x$ with the systems
fixed by the declaration).

### 2.6 Comma vs. bar on POVM subscripts

- $M_{y,t}$ is the element for the **joint outcome** $(y,t)$:
  $\sum_{y,t}M_{y,t}=\mathds{1}$ over the joint alphabet.
- $M_{y\vert t}$ is an element of the **conditional POVM** given $t$: for each
  fixed $t$, $\sum_{y}M_{y\vert t}=\mathds{1}$.

When $t$ is recorded as an outcome with fixed, state-independent probability
$q_t$: $M_{y,t}=q_t M_{y\vert t}$. **Platform note:** the declared POVM
$\{F_v\}$ of a protocol declaration absorbs every per-round classical choice
of known bias into the *joint* outcome $v$ (weights $q_t F_{v|t}$) — this is
the `output_state` test-statistics model, and no contract may assume a
state-independent test fraction (Assumption A-TSM, `reductions/ass:tsm`).

### 2.7 Register-naming conventions

**General (declaration-generated) registers** — the platform vocabulary, fixed
by meat-core `def:declaration` and `def:maps`:

| Register | Role |
| --- | --- |
| $A$ | Alice's system in the source-replacement picture; the marginal $\tau_A$ is declared **only in trusted-source mode** (in untrusted-source mode the marginal slot is empty — `transmitter/rem:source-mode`; the transmitted system $A'$ and the virtual transmitted system $A''$ are deliberately module-local, the macros `\Asig`, `\Avirt` of `spec/macros.tex` part B, and are not catalogued here) |
| $Q$, $Q_s$ | The declared sector-carrying measured system and its sectors; which party holds which tensor factor of $\mathcal{H}(Q_s)$ is declaration metadata (the party partition $\mathfrak{P}$ of meat-core `def:declaration`, §3.3), not fixed by the symbol |
| $X$, $Y$ | The classical outcome registers of the measurement on $A$ and of the **measuring parties** — Alice's and Bob's under the default partition (alphabets $\mathcal{X}$, $\mathcal{V}$); in the general format $\mathcal{V}$ is a product over measured factors (§3.11) |
| $C_AC_B$ | The **announcement register**: one register holding the joint announcement $a(x,v)$, alphabet $\mathcal{K}$ (meat-core `def:maps`). It is named after the first and second message of the $L=2$ transcript, whose alphabets are $\mathcal{C}_A=\mathcal{C}_1$ and $\mathcal{C}_B=\mathcal{C}_2$ with $\mathcal{K}=\mathcal{C}_A\times\mathcal{C}_B$; in the general format it holds the whole tuple of messages (§3.11), and no claim writes $C_A$ or $C_B$ alone |
| $I$ | Eve's copy of the transcript (alphabet $\mathcal{K}=\prod_{m=1}^{L}\mathcal{C}_m$, which at $L=2$ is $\mathcal{C}_A\times\mathcal{C}_B$) |
| $\widehat{C}$ | Acceptance-statistic register (alphabet $\widehat{\mathcal{C}}$) |
| $R$, $Z$ | Raw-key register and its pinched copy; alphabet $\mathcal{Z}_\perp=\mathcal{Z}\sqcup\{\perp\}$ |
| $\widetilde{E}$, $\widehat{E}$ | Single-round purifying register; Eve's $n$-round register |

**Optical-profile registers** — used by the receiver and reduction
documents only; a general contract does not touch them:

| Register | Role |
| --- | --- |
| $C$ | Quantum channel input from Eve; $\mathcal{H}(C)=\bigoplus_n\mathcal{H}(C_n)$ |
| $P$ | Probe-light input inserted by Bob |
| $D_H, D_V, D_+, D_-$ | The four detector systems |
| $\mathrm{Flg}$ | Flag system, introduced **only by the squashing map**; no physical meaning before squashing |
| $T_{\mathrm{set}}$ | Private-setting register |

> **"Flag" is post-squashing only.** $\mathrm{Flg}$ is created by the
> (weight-preserving) flag-state squasher, never a physical mode.

### 2.8 Convention summary table

| Object | System label goes | Marker | Example |
| --- | --- | --- | --- |
| State (subnormalized component) | subscript | `\wedge` — keeps weight | $\rho_{A\wedge x}\in S_{\leq}(A)$ |
| State (normalized conditional) | subscript | `\|` — removes weight | $\rho_{A\vert x}\in S_{=}(A)$ |
| State (sector/photon block) | subscript | `\wedge` | $\rho_{C\wedge n}\in S_{\leq}(C_n)$ |
| Operator / POVM element | superscript | parenthesized block | $F_v^{(s)}$, $M_y^{(\leq N)}$ |
| POVM joint outcome | subscript, comma | — | $M_{y,t}$, $\sum_{y,t}M_{y,t}=\mathds{1}$ |
| POVM conditional | subscript, bar | `\|` | $M_{y\vert t}$, $\sum_{y}M_{y\vert t}=\mathds{1}$ per $t$ |

---

## 3. Symbol tables

### 3.1 State spaces and operator sets

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\Hs{A}` | $\mathcal{H}(A)$ | Hilbert space of the system label $A$ | Possibly infinite-dimensional |
| `\Lin{A}` | $\mathcal{L}(A)$ | Bounded linear operators on $\mathcal{H}(A)$ | |
| `\Linn{A}{B}` | $\mathcal{L}(A,B)$ | Linear maps $\mathcal{H}(A)\to\mathcal{H}(B)$ | |
| `\Pos{A}` | $\mathrm{Pos}(A)$ | Positive semidefinite operators | |
| `\Density` | $\mathrm{D}$ | Density operators, $\mathrm{D}(A)$ | Synonym for $S_{=}(A)$; takes no argument |
| `\Seq{A}` | $S_{=}(A)$ | Normalized states | |
| `\Sleq{A}` | $S_{\leq}(A)$ | Subnormalized states | The natural home of every $\wedge$-component |
| `\id`, `\idon{C}` | $\mathds{1}$, $\mathds{1}_{C}$ | Identity operator (contextual / named) | |
| `\idmap` *(local)* | $\mathrm{id}$ | Identity channel | Distinct from the identity operator |
| `\Lop{H}{K}` | $\mathcal{L}(\mathcal{H},\mathcal{K})$ | Linear maps between Hilbert spaces named by letter | **Deprecated** — use `\Linn` |

### 3.2 Composites, sectors, and photon-number blocks

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\dsum` | $\oplus$ | Direct sum of system labels | ⊕ of labels means block-diagonal operators (§2.2) |
| `\Pnum{n}`, `\Pnumon{n}{C}` | $P_{n}$, $P_{n}^{C}$ | Photon-number projector | Also $P_{\geq k}^C$ etc.; profile instance of the sector projector $\Pi_s$ |
| `\blk{M}{\leqN}` | $M^{(\leq N)}$ | Operator block restriction | $\in\mathcal{L}(C_{\leq N})$, *not* $P_{\leq N}MP_{\leq N}$ (§2.4) |
| `\leqN`, `\gtN`, `\eqn` | $\leq N$, $>N$, $=n$ | Block indices for `\blk` | |

No macro for the tensor product: write `\otimes` or juxtapose labels.

### 3.3 The protocol declaration (platform vocabulary)

The single input object of the key-rate engine, fixed by meat-core
Def. `def:declaration` / Def. `def:admissible-declaration`. The macros marked *(local)* in this
and the next three subsections are in `meat-core`'s group of
`spec/macros.tex` part B (§1).

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\Decl` *(local)* | $\mathfrak{D}$ | Protocol declaration $\big(A,\tau_A;\,Q,\mathbb{S};\,\{M_x\};\,\{F_v\};\,\mathfrak{P};\,a_A,a_B;\,\phi;\,r,\mathsf{h};\,\mathfrak{L}\big)$ — the tuple of meat-core Def. `def:declaration`: the party partition $\mathfrak{P}$ is a slot, and the marginal slot $\tau_A$ takes a state or the no-marginal value (trusted- vs untrusted-source mode) | Everything downstream is *generated* from it. The same slots are read in the **general format** (§3.11), of which this tuple is the degenerate case entry for entry |
| `\SecSet` *(local)* | $\mathbb{S}$ | Sector index set of $Q$ | $\mathcal{H}(Q)=\bigoplus_{s\in\mathbb{S}}\mathcal{H}(Q_s)$, projectors $\Pi_s$. In the general format it is the product $\prod_{f\in\mathbb{F}}\mathbb{S}^f$ over measured factors and $s=(s_f)_f$ (§3.11) |
| `\Qsys` *(local)* | $Q$ | The declared sector-carrying measured system | Sectors $Q_s$; the party split of the tensor factors is declaration metadata $\mathfrak{P}$ (meat-core `def:declaration`) |
| `\Party` *(local)* | $\mathfrak{P}$ | The declared party partition: the readout maps $\pi_{\mathsf A}$, $\pi_{\mathsf B}$ onto the alphabets $\mathcal{O}_{\mathsf A}$, $\mathcal{O}_{\mathsf B}$, with a party label for $A$ and, for each sector $s$, a declared tensor factorisation of $\mathcal{H}(Q_s)$ with a party label per factor | `protocol-compiler/def:declaration`; meat-core `def:declaration` says what the engine reads of it, the readout maps alone, through `def:admissible-declaration` (viii). Deliberately not $\mathcal{P}$, which is the deprecated `\Pdeph` (§3.9) and one subscript away from $\mathcal{P}_{\mathbb{S}}$ (`\PinS`, §3.4) |
| `\Xset` | $\mathcal{X}$ | Outcome alphabet of the measurement on $A$ — Alice's under the default partition | POVM $\{M_x\}_{x\in\mathcal{X}}$ on $A$, or the ensemble form's $\{N_x\}$ in the same index set (§3.11) |
| `\Vset` *(local)* | $\mathcal{V}$ | The measuring parties' declared joint outcome alphabet — Bob's alone under the default partition | POVM $\{F_v\}_{v\in\mathcal{V}}$ on $Q$, every $F_v=\bigoplus_s F_v^{(s)}$ block-diagonal. In the general format it is the product $\prod_{f\in\mathbb{F}}\mathcal{V}^f$ over measured factors, last factor fastest (§3.11). Carries all per-round classical choices (§2.6). Deliberately **not** $\mathcal{Y}$ (§3.7): $\mathcal{Y}$ is the optical profile's six-outcome instance |
| `\CAset`, `\CBset` *(local)* | $\mathcal{C}_A$, $\mathcal{C}_B$ | The alphabets of the first and second message of the transcript, which is the $L=2$ case | Maps $a_A:\mathcal{X}\to\mathcal{C}_A$, $a_B:\mathcal{V}\to\mathcal{C}_B$; jointly $a(x,v)$. In the general format they are $\mathcal{C}_1$, $\mathcal{C}_2$ of §3.11, where a message may read the earlier messages of its round |
| `\Kann` *(local)* | $\mathcal{K}$ | Transcript alphabet $\prod_{m=1}^{L}\mathcal{C}_m$, which at $L=2$ is $\mathcal{C}_A\times\mathcal{C}_B$ | Classes $\kappa$; at $L=2$, $\kappa=(c_A,c_B)$. $\phi$, $\varsigma$ and $r$ are maps on this $\mathcal{K}$ whatever $L$ is |
| `\Chat`, `\Chatset` | $\widehat{C}$, $\widehat{\mathcal{C}}$ | The acceptance-statistic register $\widehat{C}$ and its alphabet $\widehat{\mathcal{C}}$ | $\phi:\mathcal{C}_A\times\mathcal{C}_B\to\widehat{\mathcal{C}}$. Hat is the only mark distinguishing $\widehat C$ from the channel system $C$ — collision hazard |
| `\Chkey` *(local)* | $\widehat{\mathcal{C}}_{\mathrm{key}}$ | Key-live acceptance values | $\{\hat c:\exists\kappa\in\phi^{-1}(\hat c),\ \varsigma(\kappa)=\mathrm{pass}\}$ |
| `\Zval`, `\Zset` *(local)* | $\mathcal{Z}$, $\mathcal{Z}_{\perp}$ | Key alphabet $\{0,\dots,d_Z{-}1\}$ and $\mathcal{Z}\sqcup\{\perp\}$ | Raw-key map $r:\mathcal{X}\times\mathcal{V}\to\mathcal{Z}_\perp$ |
| — | $\varsigma$ | Sifting predicate $\mathcal{C}_A\times\mathcal{C}_B\to\{\mathrm{pass},\mathrm{fail}\}$ | Sifting is announcement-determined: $r(x,v)=\perp\iff\varsigma(a(x,v))=\mathrm{fail}$. Supersedes `\pass` ($\top$; §3.9) |
| `\hold` *(local)* | $\mathsf{h}$ | Declared key holder, $\mathsf{h}\in\{\mathsf A,\mathsf B\}$ | $r$ must factor through the holder's own outcome and the announcements (holder computability, `def:admissible-declaration` (viii)) — without it no party can compute the raw key |
| `\CList` *(local)* | $\mathfrak{L}$ | Declared constraint list $\{(\hat O_k,\bowtie_k,\Theta_k)\}$ | $\hat O_k$ sector-block-diagonal. **Two-part constraint gate** (meat-core `def:hqkd-list`): a non-empty $\mathfrak{L}$ backs a key-length claim only through the mechanical homogeneity check **plus** the attested `attack_set_license` (A-ATK); `rem:cgate` discloses where the mechanical half degenerates to vacuous truth. Absent the gate, device knowledge enters encoded in $\{F_v\}$ |
| `\acSet` | $\mathcal{S}_{\mathrm{acc}}$ | Acceptance set | Closed **convex** subset of the probability simplex on $\widehat{\mathcal{C}}$ (meat-core `def:admissible-acceptance-set`) |

### 3.4 Generated registers, isometries, and maps

Fixed by meat-core `def:maps` and `def:branch`; §5.2 records which name each
map carries.

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\Vmsm` | $V_{\mathrm{msm}}$ | Measurement isometry ($\sqrt{M_x}\otimes\sqrt{F_v}$ form) | |
| `\Vann` | $V_{\mathrm{ann}}$ | Announcement isometry | |
| `\VI` | $V_{I}$ | Eve's copy of the announcements | |
| `\VChat` | $V_{\widehat C}$ | Acceptance-statistic isometry | |
| `\VR`, `\VZ` | $V_{R}$, $V_{Z}$ | Raw-key isometry; raw key → key register | |
| `\Wprot` | $W$ | Full protocol isometry | Composition order fixed by meat-core Eq. `eq:Mprot`: $W=V_R V_{\widehat C} V_I V_{\mathrm{ann}} V_{\mathrm{msm}}$ |
| `\Mprot` | $\mathcal{M}$ | Single-round protocol channel $AQ\to Z\widehat{C}I$ | Generated from $\mathfrak{D}$ |
| `\Phimap` | $\boldsymbol{\Phi}$ | The test-statistics map $\mathcal{L}(AQ)\to\mathbb{R}^{\widehat{\mathcal{C}}}$ | Affine. `\testE` is a deprecated alias (§3.9) |
| `\cZ` | $\mathcal{Z}$ | The key pinching, on the raw-key register $R$ | $\mathcal{Z}(\tau)=\sum_j \dyad{j}\tau\dyad{j}$ |
| `\PinS` *(local)* | $\mathcal{P}_{\mathbb{S}}$ | Sector pinching on $Q$ | $\mathcal{P}_{\mathbb{S}}(X)=\sum_s\Pi_s X\Pi_s$. `\Pdeph` is deprecated (§3.9) |
| `\cG` | $\mathcal{G}$ | Branch (generation) maps $\mathcal{G}_{\hat c}$, sector components $\mathcal{G}_{\hat c,s}$ | CP, trace-non-increasing key branches of $\mathcal{M}$ (meat-core `def:branch`, `lem:branch-maps`). $\mathcal{M}$ is the channel, $\mathcal{G}_{\hat c}$ its key branches (§5.2) |

### 3.5 Optimization and key-length objects

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\Feas` *(local)* | $\mathcal{W}$ | Feasible set of sector-block-diagonal marginals: $\operatorname{tr}\omega=1$ always; $\omega_A=\tau_A$ in trusted-source mode only; $\mathfrak{L}$ if declared (meat-core Def. `def:feasible`) | Convex, compact |
| — | $P_{\hat c}$, $f_{\hat c,s}$, $K_{\hat c}$ | Branch probability, sector trace-power deficit, branch denominator | $K_{\hat c}=P_{\hat c}+\sum_s f_{\hat c,s}$, $0\le K_{\hat c}\le P_{\hat c}$ |
| — | $O_{\alpha}(\mathbf q,\omega)$ | The three-term convex objective | meat-core Eq. `eq:objective` |
| `\hup` | $h^{\uparrow}_{\alpha}$ | Single-round MEAT rate (up variant) | **SECURITY-CRITICAL — §4** |
| `\hqkd` | $h^{\uparrow,\mathrm{QKD}}_{\alpha}$ | Single-round QKD rate — carries the $\uparrow$ arrow | **SECURITY-CRITICAL — §4** |
| `\hlow` | $\underline{h}_{\alpha}$ | Computable relaxation: lower bound on $h^{\uparrow,\mathrm{QKD}}_{\alpha}$; written `h_low` in plain text | **SECURITY-CRITICAL — §4.** Range $[0,+\infty]$ (meat-core `prop:value-range`); $+\infty$ is propagated and never clamped (meat-core `req:infinite-value`). It is the **quantity**, not either number a run computes — see §4.5 |
| `\hlb` | $\underline{h}^{\mathrm{FO}}_{\alpha}$ | First-order lower bound on $\underline{h}_{\alpha}$: the maximum over iterates of the linearization of the objective, with lower bounds on its two linear minima | **SECURITY-CRITICAL — §4.5.** The `first-order` tier of `foundations/def:tiers`, and the headline key rate of a run that does not reach the `certified` tier ($\underline{h}^{\mathrm{cert}}_{\alpha}$, §3.15). May be negative or $-\infty$ before reporting; what is reported is $\max\{0,\underline{h}^{\mathrm{FO}}_{\alpha}\}$, flagged |
| `\tnum` | $\tau_{\mathrm{num}}$ | The instance's one declared numerical tolerance: the ceiling on the pre-snap defect an instance may repair in what it declares — a declared block whose measured defect (Hermiticity, positivity, completeness, column-stochasticity, a probability sum) exceeds it is a modelling error and is refused (a probability vector prepared from numerical inputs is admitted by the input preparation's rule instead, foundations Req. `req:declared-tolerance`); one within it is snapped onto an exactly admissible family and the snap is recorded with the defect it corrected | Defined in `foundations/def:tolerance`, with its use in `foundations/req:declared-tolerance`. **It is not the number a predicate is decided at.** No module takes a tolerance input, and no predicate on declared data is decided at a window (`foundations/req:consumer-decides-exactly`): a consumer decides exactly on the declared dyadic numbers and refuses, and the reason no tolerance can be accepted where the entropic step reads a declaration is `meat-core/prop:optol-nobound`. **Disclosed near-collision:** $\tau$ with subscript $A$ is the declared marginal of §3.3 and has nothing to do with this; bare $\tau$ is reserved and used for neither. Prose and code call this "the declared tolerance $\tau$" only where no marginal is in scope. It has no default: a run that does not declare it is refused |
| — | $W_{\tau}$, $A_0$ | Fixed-marginal Choi factor $W_{\tau}=\tau_A^{1/2}\iota\in\mathcal{L}(A_0,A)$ and the Choi input register $A_0$, which the declared isometry $\iota$ maps into $A$ onto a support frame containing $\operatorname{supp}\tau_A$: $\operatorname{rank}\tau_A\le d_{A_0}\le d_A$, $\operatorname{ran}W_{\tau}=\operatorname{supp}\tau_A$, and $\iota$ identifies $A_0$ with $\operatorname{supp}\tau_A$ only on a tight frame. Trusted-source mode only | meat-core `def:support-frame`, `lem:choi-marginal`, `thm:choi` |
| — | $J$, $J_s$ | Choi variable and its sector blocks | $J_s\in\mathrm{Pos}(A_0 Q_s)$, $\sum_s\mathrm{tr}_{Q_s}J_s=\mathds{1}_{A_0}$; input factor $A_0$ **first** |
| `\epa`, `\eev` *(local)* | $\varepsilon_{\mathrm{PA}}$, $\varepsilon_{\mathrm{EV}}$ | Secrecy / correctness budgets | |
| `\lEC` *(local)* | $\lambda_{\mathrm{EC}}$ | Error-correction transcript length, total bits, fixed-length register (shorter transcripts padded) | Settles the per-round-vs-total ambiguity of `\ecLeak`, which it supersedes (§3.9) |
| — | $\alpha$, $n$, $\ell$ | Rényi order; round count; output key length | Working intersection $\alpha\in(1,2)$ for key-length statements. **Scoped $n$ rule:** wherever a round count or finite-key quantity is in scope, $n$ is the round count and photon numbers use another index. A contract that states **no** round count and no finite-key quantity (e.g. `receiver`) may use $n$ as the photon-number block index of §2.4/§3.2 ($P_n$, $M^{(\leq N)}$), disclosing that reading in its Notation section. Lemma-local deviations are permitted where disclosed in place. The two global readings never co-occur in one document |
| `\OmAT` *(local)* | $\Omega_{\mathrm{AT}}$ | Acceptance event $\operatorname{freq}_{\hat c_1^n}\in\mathcal{S}_{\mathrm{acc}}$ | |
| `\Etil`, `\Ehat` *(local)* | $\widetilde{E}$, $\widehat{E}$ | Purifying register; Eve's $n$-round register | $\dim\mathcal{H}(\widetilde E)\ge\dim\mathcal{H}(AQ)$ where the accumulation theorem is invoked |

### 3.6 Divergences and entropies

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\sfD` *(local)* | $D$ | Classical KL divergence, base 2; also the quantum relative entropy on operators | The MEAT penalty divergence — see §4.4 |
| — | $D_{\alpha}$ | Classical Rényi divergence, base 2 | Defined for completeness in `foundations/def:kl`; **no claim uses it** — see §4.4 |
| `\Dsand` *(local)* | $\widetilde{D}_{\alpha}$ | Sandwiched Rényi divergence | |
| `\Hsandup` | $\widetilde{H}^{\uparrow}_{\alpha}$ | Sandwiched Rényi conditional entropy, up | **SECURITY-CRITICAL — §4.1** |
| `\Hsanddown` | $\widetilde{H}^{\downarrow}_{\alpha}$ | Sandwiched Rényi conditional entropy, down | **SECURITY-CRITICAL — §4.1** |
| `\Hpetzup`, `\Hpetzdown` | $\overline{H}^{\uparrow}_{\alpha}$, $\overline{H}^{\downarrow}_{\alpha}$ | Petz family | Tilde = sandwiched, overline = Petz; never converted silently |

All entropies and divergences are in **bits** (`log_base: 2`); natural
logarithms appear only inside derivative formulas with explicit conversion
factors.

The sandwiched divergence and its two conditional entropies are defined in
`foundations/def:renyi`, the classical divergences and the quantum relative
entropy in `foundations/def:kl`, and pinching in `foundations/def:pinching`.

### 3.7 Optical-profile symbols

Used by `receiver`, `reductions` and the optical protocol profiles. **A
general (declaration-level) contract does not use these.** In particular `\Tset` below is Bob's private setting set, the probe
settings in the optical instance, and `\Fset` the optical instance's round
types: the `protocol-compiler`'s **generic** setting and choice alphabets are
written inline as $\mathcal{T}$ and $\mathcal{F}$ (§1, module-local macros),
the setting alphabet being `\Tset`'s set where the reduction chain comes from
`reductions`. The probe symbols (`\Prb`, the probe settings of `\Tset`)
belong to the receiver core's probe declaration (`receiver/def:probe`); with
the setting `\off` alone they describe every probe-free receiver.

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\Chan`, `\Prb` | $C$, $P$ | Channel input; probe input | $\mathcal{H}(C)=\bigoplus_n\mathcal{H}(C_n)$ |
| `\Flag` | $\mathrm{Flg}$ | Flag system — post-squashing only | Never a physical mode (§2.7) |
| `\Yset` | $\mathcal{Y}$ | Bob's coarse-grained detection alphabet, $\vert\mathcal{Y}\vert=6$ | $\{\mathrm{nc},\mathrm{sc}_H,\mathrm{sc}_V,\mathrm{sc}_+,\mathrm{sc}_-,\mathrm{mc}\}$. Profile-specific — the general outcome alphabet is $\mathcal{V}$ (§3.3) |
| `\Yraw`, `\Yscset`, `\Ymcset` | $\mathcal{Y}_{\mathrm{raw}}$, $\mathcal{Y}_{\mathrm{sc}}$, $\mathcal{Y}_{\mathrm{mc}}$ | Raw click patterns $\{0,1\}^4$; single-click; multi-click | |
| `\Tset` | $\mathcal{T}_{\mathrm{set}}$ | Bob's private setting set, weights $q_t$ (`reductions` `def:joint-family`); in the optical instance the probe settings (register $T_{\mathrm{set}}$) | In the optical instance it includes "off". Where Bob's private setting has components other than the probe setting, $\mathcal{T}_{\mathrm{set}}$ records all of them |
| `\Dset` | $\{H,V,+,-\}$ | Polarization / detector labels | |
| `\Fset` | $\mathcal{T}$ | Round-type alphabet $\{\mathrm{test},\mathrm{gen}\}$ | Collision hazard with $\mathcal{T}_{\mathrm{set}}$ (`\Tset`, Bob's private setting set): visually close, semantically different |
| `\Amap`, `\Amapnb` | $\mathcal{A}_{\mathrm{ann}}$, $\mathcal{A}_{\mathrm{ann}\|\mathrm{nb}}$ | Announcement + measurement map (and its nb-conditional) | Profile shorthand; the general construction is $V_{\mathrm{ann}}$/$\mathcal{M}$ |
| `\bA`, `\bB`, `\kB` | $b_A$, $b_B$, $k_B$ | Basis / key extraction functions | Profile instances of $a_A$, $a_B$, $r$ |
| `\on`, `\off`, `\dc`, `\sq`, `\mc`, `\nc`, `\singlec`, `\vac` | $\mathrm{on}$, $\mathrm{off}$, $\mathrm{dc}$, $\mathrm{sq}$, $\mathrm{mc}$, $\mathrm{nc}$, $\mathrm{sc}$, $\mathrm{vac}$ | Mode / outcome abbreviations | |
| `\tst`, `\gen` | $\mathrm{test}$, $\mathrm{gen}$ | Round-type values | |
| `\askeyr`, `\ppass`, `\pgen` | $R_{\infty}$, $p_{\mathrm{pass}}$, $p_{\mathrm{gen}}$ | Asymptotic rate; sifting-pass and generation-round probabilities | Profile-analysis quantities only. A state-independent $p_{\mathrm{gen}}$ **does not exist** in the platform model (`output_state`, §2.6); these may appear in asymptotic profile analyses, never in a security chain |

### 3.8 Miscellaneous operators

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\Prob` | $\mathrm{Prob}$ | Probability | $\Pr[\Omega]$ is the other form; pick one per contract (meat-core uses $\Pr$) |
| `\lmin` | $\lambda_{\min}$ | Minimum eigenvalue | |
| `\transpose` | $\mathsf{T}$ | Transpose, $X^{\mathsf T}$ | Choi pairings take it in the **declared input basis of $A_0$** (meat-core `rem:ordering`) |
| `\innerp{a}{b}` | $\left\langle a \vert b \right\rangle$ | Inner product | Auto-sizing: the macro is `\left\langle ... \right\rangle` and this cell copies it verbatim, as part A requires |
| `\vec{v}` | $\boldsymbol{v}$ | Vector (bold) | **Overrides** LaTeX's arrow accent; do not rely on the standard meaning |
| `\simpl` | *(empty)* | Typographic hook for simplified block maps | No mathematical content; a contract must not attach meaning to it |

### 3.9 Reserved, superseded, and deprecated symbols

**Reserved (meaning never established by the sources — a contract must not use
them until this document assigns one, with a version bump):**
`\Nout` ($N_{\mathrm{out}}$), `\Nin` ($N_{\mathrm{in}}$), `\kout`
($k_{\mathrm{out}}$), `\kin` ($k_{\mathrm{in}}$), `\Loss` ($\mathrm{Lss}$),
`\Vc` ($\mathrm{Vcm}$), `\Wflag` ($W_{\mathrm{Flg}}$).

**Superseded (meaning carried by a listed symbol; do not use):**

| Old | Superseded by | Why |
| --- | --- | --- |
| `\pass` ($\top$) | the sifting predicate $\varsigma$ and its $\mathrm{pass}$ value (§3.3) | $\top$ leaves open whether it is an outcome, a register value or an event; the declaration fixes sifting as announcement-determined |
| `\ecLeak` ($\mathrm{leak}^{\mathrm{EC}}_{\mathrm{obs}}$) | $\lambda_{\mathrm{EC}}$ (§3.5) | Settles the per-round-vs-total ambiguity: total bits, fixed-length register |
| `\testE` ($\mathcal{E}_{\mathrm{test}}$) | $\boldsymbol{\Phi}$ (§3.4) | Duplicate of the test-statistics map (§5.2) |
| `\Pdeph` ($\mathcal{P}$) | $\mathcal{P}_{\mathbb{S}}$ (§3.4) | A dephasing that is a sector pinching, an instance of the general map |
| `\Lop` | `\Linn` (§3.1) | Takes Hilbert-space letters rather than system labels |

The macros of superseded symbols are deprecated aliases, kept defined in
`spec/macros.tex` so that older text compiles; do not use them.

### 3.10 Alice-side sectors, source links, decoy, factors

The symbols that `transmitter`, `transmitter/decoy` and `reductions` write for
Alice's sector structure, the source link, the decoy source and the factors of
the measured system. Two things about this section.

- **No row is a part A entry.** Each symbol is plain LaTeX or a module-local
  macro of part B, named in the Notes cell where one exists.
- **The declaration's general format is §3.11's.** The declaration's Alice
  form and factor list, the joint sectors \((t,s)\), the transcript, the
  dropped set and its bounds belong to `protocol-compiler` and `meat-core`
  and are catalogued in §3.11. The symbols below are catalogued although
  some of them have **no consumer** — that is a fact about the gates
  (`transmitter/def:srcert`), not about the notation.

**(a) Alice's sector structure and the three certificate forms**
(`transmitter/def:source-spec`, `def:srcert`, `lem:ensemble-presentation`,
`lem:matched-pinching`).

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $\mathbb{T}$ | Ordered index set of Alice's declared sector structure, $\mathcal{H}(A)=\bigoplus_{t\in\mathbb{T}}\mathcal{H}(A_t)$ | The **one-sector** structure is the default, and with it every condition reduces to its form without Alice-side sectors. **Collision hazard:** $t$ is an Alice sector here, while in `reductions` the same letter indexes a private setting class in $\mathcal{T}_{\mathrm{set}}$ (§3.7); the two never range together in one statement |
| — | $A_t$, $\Pi^{A}_t$, $d_{A_t}$ | Alice's sector, its projector, its dimension $\geq 1$ | Each $A_t$ is spanned by vectors of $A$'s declared basis |
| — | $S_t$, $\Pi^{\mathrm v}_t$ | The matched sector of the virtual transmitted system $A''$ and its projector | Matched means the same ordered $\mathbb{T}$ on both sides; $A''$ is `\Avirt` of part B (§2.7) |
| — | $\sigma_x$ | Weighted member of the specified ensemble, $\sigma_x=p_x\rho_x\in\mathrm{Pos}(A')$ with $p_x=\mathrm{tr}\,\sigma_x$ | *The declared datum:* every condition that reads an admitted ensemble reads it through its weighted members. A declared pair $(p_x,\rho_x)$ **is** the declaration of $\sigma_x$ with the product formed exactly, and still requires $\rho_x\in S_{=}(A')$ of every letter |
| — | $\sigma^{\mathrm v}_x$, $\sigma^{\mathrm v,(t)}_x$ | Weighted members of the virtual ensemble and their blocks along $(S_t)_t$ | In an **ensemble presentation** these blocks are the only declared certificate data, under (E1)–(E3); nothing else is declared |
| — | $\Psi$, $\Psi_t$ | Source-replacement certificate and its blocks $\Psi_t\in\mathcal{L}(A_tS_t)$ | Block form imposes **no** purity condition; in an ensemble presentation $\Psi_t$ is *defined* and never formed as numbers |
| — | $N_x$, $N^{(t)}_x$ | $N^{(t)}_x=\big(\sigma^{\mathrm v,(t)}_x\big)^{\mathsf T}$ — all of Alice's measurement a consumer can read in an ensemble presentation, with $\sum_xN^{(t)}_x=\tau^{(t)}_A$ | `lem:ensemble-presentation` (v); entrywise the declared numbers, so no square root or quotient is formed. **A consumer whose declaration carries $\{M_x\}$ refuses a presentation**; the form that carries $\{N_x\}$ instead is the **ensemble form** of §3.11, and `protocol-compiler` and `meat-core` write it with this same symbol |
| — | $\tau^{(t)}_A$ | Blocks of the declared marginal; in an ensemble presentation $\tau^{(t)}_A$ is the transpose of $\sum_x\sigma^{\mathrm v,(t)}_x$ and the one defined object ever formed as numbers | $\tau_A$ itself is §3.3's, and §3.5's disclosed near-collision with $\tau_{\mathrm{num}}$ applies to its blocks as well |
| — | `proof_sector` | The block kind an Alice-side sector map carries | A sector map's block kind in the sense of `spec/architecture.md` §2.9, not a symbol of the mathematics |

**(b) The source link, the source segment and the soundness registry**
(`transmitter/def:source-link`, `def:source-segment`).

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $\Xi$ | A source link: the typed tuple (kind, source and target descriptors, channel witness, descriptor family, sector map, transported entries, licence, status) | The receiver-stage link type and the chain stay `reductions`' |
| — | $\mathfrak{R}_{\mathrm{src}}=(\Xi_1,\dots,\Xi_{L_{\mathrm s}})$ | The source segment of a chain, $L_{\mathrm s}\geq0$ | Written `\Chsrc` of part B on `\pcChain` (§1); it is a slot of the chain record and not a type of its own |
| — | $\Gamma_{\Xi}$ | The link's channel witness, supplied either as data or as a *theorem constructor* | The constructor case is what a submodule's soundness claim discharges |
| — | $\mathcal{D}_{\Xi}$ | The link's declared descriptor family — the slot that makes a link sound rather than merely well typed | Membership is asserted by the emitting module and re-proved by no one; for a constructor link it is not a decidable condition. **Disclosed collision:** the subscripted $\mathcal{D}_{\Xi}$ is this family, the bare $\mathcal{D}$ of §3.11 is a run's dropped set, and nothing relates them |
| — | $\mathfrak{s}_{\Xi}$ | The optional retained-register sector map a link emits | Written `\Smap` of part B; for the one link that exists it is the matched pair of (a) |
| — | $\mathfrak{L}_{\Xi}$ | The link's list of transported constraint entries | Written `\CList` of part B, a subscripted instance of §3.3's $\mathfrak{L}$; a link with a non-empty list is refused, no claim of this repository transporting an Alice-side entry |
| — | $\mathcal{A}(\texttt{kind})$ | The assumptions the obligation carries, the third component of a soundness-registry entry $(\texttt{kind},\ \text{soundness claim id},\ \mathcal{A}(\texttt{kind}))$ | Two sources, both listed: the soundness claim's assumption closure, which the `check_claims --assumptions` command computes and which may be empty, **together with** the physical-source assumption the submodule declares for the model that claim is stated over, which is not a premise of the claim and must not be made one |

**(c) The decoy source** (`transmitter/decoy/def:wcp-model`,
`def:tagged-source`; the submodule uses no macro of its own).

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $\mathsf{n}$ | Photon number, sans-serif | Forced by the scoped-$n$ rule of §3.5: this submodule states finite-key quantities, so $n$ is the round count and the photon number takes another symbol |
| — | $\mathrm{Pol}$, $\mathrm{Int}$ | The declared polarisations $a$ (each a label standing for a unit vector of $\mathbb{C}^2$, an object of the model) and intensities $\mu$ | |
| — | $x=(a_x,\mu_x,z_x)$ | A signal label: polarisation, intensity, round type $z\in\{\mathrm{test},\mathrm{gen}\}$ | $\mathcal{X}$ is §3.3's alphabet; a label of weight zero is not a letter |
| — | $P_{\mu}(\mathsf{n})=e^{-\mu}\mu^{\mathsf{n}}/\mathsf{n}!$ | The Poisson weight | Transcendental, so it is never a declared datum and no condition compares a declared number with it for equality |
| — | $\tilde p(\mathsf{n}\mid\mu)$ | The declared sector weights, $0\leq\tilde p(\mathsf{n}\mid\mu)\leq P_{\mu}(\mathsf{n})$ | A *certified inequality* and never an equality: the declared dyadic is decided against the rational lower end of an enclosure of $P_{\mu}(\mathsf{n})$ that the emission forms from the declared $\mu$ (`decoy/lem:poisson-enclosure`) |
| — | $\tilde w_{\mu}$ | The tail weight $1-\sum_{\mathsf{n}\leq N_{\mathrm{src}}}\tilde p(\mathsf{n}\mid\mu)\geq0$ | Summed in increasing $\mathsf{n}$, rounding nowhere |
| — | $N_{\mathrm{ent}}$, $N_{\mathrm{src}}$ | The entropy cutoff (largest photon number whose sector stays quantum) and the source cutoff (largest photon number with a sector of its own), $0\leq N_{\mathrm{ent}}\leq N_{\mathrm{src}}$ | **Three cutoffs, one gloss:** neither is the receiver's $N$ of §3.2/§3.4, the photon cutoff of the optical profile. `rem:cutoffs` is the claim that says so; confusing them is the error this row exists to prevent |
| — | $S_{\mathsf{n}}$, $\ket{\mathsf{n},a}$ | The span of the number states of the declared polarisations, and the number state itself | $\dim S_{\mathsf{n}}\leq\min(\mathsf{n}+1,\lvert\mathrm{Pol}\rvert)$; $S_0$ is one dimensional |
| — | $f_{\mathsf{n},a}$, $f_{a,\mu}$ | The polarisation flag (per photon number above $N_{\mathrm{ent}}$ and polarisation, shared across intensities and round types) and the tail flag (per polarisation and intensity, shared across round types) | That sharing is the decoy content; a finer flag is `rem:no-intensity-split`'s subject |
| — | $\Xi_{\mathrm{tag}}$ | The source link of kind `tagging`, whose witness is a theorem constructor | Admitted by `transmitter/decoy`, whose `prop:tagging` is its soundness claim |

**(d) Measuring factors, and the exact operational reduction**
(`reductions/def:protocol`, `def:roundmodel`, `thm:emitted-product`,
`def:opreduction`).

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $\mathbb{F}$, $f$ | The finite ordered set of factors of the measured system, one per measuring party, and a factor index | With one factor every statement of those claims reduces to its form for an undivided measured system |
| — | $B_f$, $Q_f$, $\Lambda_f$ | A factor's physical system, its squashed system and its squashing channel | $B=\bigotimes_fB_f$, $Q=\bigotimes_fQ_f$, $\Lambda=\bigotimes_f\Lambda_f$ in the order of $\mathbb{F}$, last factor fastest (`spec/architecture.md` §2.9). $B$ is `\Bsys` of part B; $Q$ is §3.3's `\Qsys` |
| — | $F^{f}_{v_f}$, $v=(v_f)_f$ | A factor's emitted target family and the product letter | $F_v=\bigotimes_fF^{f}_{v_f}$ is a **theorem** about the factors' exact numbers and never a declared datum: no entry of a product is emitted, declared, rounded or snapped |
| — | `party_local` | The tag an emitted constraint entry may carry, with a factor scope | The untagged entry is the form of its source mode; a tagged entry is emitted only against a certificate on that factor's own channel. This tag is the one widening of gate (G3)(a) of `protocol-compiler/def:eligible` beyond the untagged form |
| — | $\mathsf{P}=(\mathbb{A},W,\mathsf{out})$ | A protocol presentation: attack strategies, output registers, and the full output state each strategy produces | The full output is every register a security criterion may read, and no marginal of them |
| — | $r$ | An exact operational reduction $r:\mathbb{A}\to\mathbb{A}'$ between presentations over the same $W$, with $\mathsf{out}(a)=\mathsf{out}'(r(a))$ | Equality on the nose — not of a marginal, not up to a distance (`rem:why-exact`). $\mathbb{A}$ is the *physical*, $\mathbb{A}'$ the *analysed* set, and $r(\mathbb{A})$ the image, which is strictly smaller than $\mathbb{A}'$ here |

### 3.11 The general declaration format

The symbols of the general declaration format, which `protocol-compiler`,
`meat-core` and `frank-wolfe` write. The general format is the one
`protocol-compiler/def:declaration` states in (DX1)–(DX6), which
`meat-core/def:declaration` cites — **the basic format is its case
$\lvert\mathbb{T}\rvert=1$, $\lvert\mathbb{F}\rvert=1$, POVM form, $L=2$, no
party-scoped entry, entry for entry**, which is why §3.3's rows read as they
do for the basic format and carry a pointer here. As in §3.10, no row is a
part A entry. The Meanings of the §3.3 rows `\Xset`, `\Vset`,
`\CAset`/`\CBset` and `\Kann` cover both formats.

**(a) The factor list, Alice's form, and party-scoped entries**
(`def:declaration` (DX1)–(DX4), (DX6); `meat-core/lem:ensemble-form`).

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $\mathbb{F}$, $f$ | The ordered set of measured factors of the declaration's factor list, and a factor index | The same $\mathbb{F}$ `reductions` emits over (§3.10 d). A factor carries a **system tag** $A$ or $Q$, a party label and its own sector map; at most one factor is tagged $A$ and it comes first, at least one is tagged $Q$ |
| — | $\mathbb{T}$, $A_t$, $\Pi^{A}_t$, $d_{A_t}$ | Alice's sector index set and sectors, fixed by the factor tagged $A$ | The same objects as §3.10 (a); where no factor is tagged $A$, $\mathbb{T}=\{t_0\}$ and $A_{t_0}=A$ |
| — | $\mathbb{S}^{f}$, $Q_f$, $\Pi^{f}_{s_f}$, $d_{f,s_f}$ | A measured factor's sector index set, system, projectors and dimensions | $\mathbb{S}=\prod_f\mathbb{S}^f$, $Q=\bigotimes_fQ_f$, $\Pi_s=\bigotimes_f\Pi^{f}_{s_f}$, $d_s=\prod_fd_{f,s_f}$, all in the order of $\mathbb{F}$ with the last factor fastest |
| — | $(t,s)$ | A joint sector, $(t,s)\in\mathbb{T}\times\mathbb{S}$, ordered with $t$ slowest, the $A$ index first inside the block $\mathcal{H}(A_t)\otimes\mathcal{H}(Q_s)$ | The variable is the block list $\omega=\bigoplus_{(t,s)}\omega^{(t,s)}$. **This declares structure and licenses nothing**: that restricting $\omega$ to such lists is sound is `meat-core/thm:reduction` with `prop:a-neutral`, under exactly this typing against a *declared* factor |
| — | $\mathcal{V}^{f}$, $F^{f}_{v_f}$ | A measured factor's declared alphabet and family of block lists, $F_v=\bigotimes_fF^{f}_{v_f}$ | The **factorised family** of §2.9 and §3.10 (d); no entry of a product is declared, formed, rounded or decided on, and every exact predicate is decided per factor |
| — | $N_x$, $N^{(t)}_x$ | Alice's measurement slot in ensemble form, trusted-source mode only: block lists along $\mathbb{T}$ with $\sum_xN^{(t)}_x=\tau^{(t)}_A$ and $\tau^{(t)}_A\ne0$ | The same operators §3.10 (a) catalogues on the transmitter's side. An ensemble-form declaration **denotes** the POVM-form one whose $M^{(t)}_x$ is the conjugation of $N^{(t)}_x$ by $(\tau^{(t)}_A)^{-1/2}$ plus a kernel term split in proportion to $\operatorname{tr}N^{(t)}_x$; those $M^{(t)}_x$ are in general irrational and **formed by no one**, every statement being made of the declaration it denotes |
| — | $P_t$ | The projector onto the support of $\tau^{(t)}_A$, in the denoted POVM's kernel term | The inverse square root is taken on that support and is zero off it |
| — | $f_k$ | The scope of a constraint entry: the label of the one measured factor its operator $\hat O_k$ lives on | Unless the entry is tagged `party_local` (§3.10 d) it denotes the *lifted* operator on $Q$, never formed as a datum; with one measured factor the scope is that factor and the lifted operator is $\hat O_k$ itself. **Collision hazard:** $f$ is a factor index, $f_k$ an entry's scope, and $f_{\hat c,s}$ of §3.5 a sector trace-power deficit |

**(b) The transcript** (`def:declaration` (DX5); the party partition's readout
maps, which this row set catalogues because (DX5) reuses their letter).

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $L$, $m$ | The number of messages of the transcript, $L\geq1$, and a message index | $L=2$ is the two-announcement case of the basic format |
| — | $\pi_m$ | The sender of message $m$, $\pi_m\in\{\mathsf A,\mathsf B\}$ | **Disclosed collision, and it is deliberate in the source:** the *readout map* of a party is also written $\pi$, so `\rd` of part B renders $\pi_{\mathsf A}$, $\pi_{\mathsf B}$, and (DX5) writes the sender's readout as $\pi_{\pi_m}$. A contract that writes $\pi$ with a message index means the sender, with a party label the readout map |
| — | $\pi_{\mathsf A}$, $\pi_{\mathsf B}$; $\mathcal{O}_{\mathsf A}$, $\mathcal{O}_{\mathsf B}$ | The party partition's total readout maps $\mathcal{X}\times\mathcal{V}\to\mathcal{O}_{\mathsf{p}}$ and their declared alphabets — what each party physically observes in a round | `\rd`, `\Oset` of part B, catalogued here for the collision above. The **default partition** is $\pi_{\mathsf A}(x,v)=x$, $\pi_{\mathsf B}(x,v)=v$. Only this half of the partition is consumed by a derivation |
| — | $\mathcal{C}_m$, $a_m$ | Message $m$'s alphabet and its total table $\mathcal{O}_{\pi_m}\times\mathcal{C}_1\times\dots\times\mathcal{C}_{m-1}\to\mathcal{C}_m$ | A message is a function of its sender's readout and of the **earlier messages of the same round**, and of nothing else; no measurement of a round depends on a message of that round |
| — | $\kappa_m$, $a$ | The joint announcement functions derived from the tables by composition, $a(x,v)=(\kappa_m(x,v))_{m=1}^{L}\in\mathcal{K}$ | Derived, not declared; $\phi$, $\varsigma$ and $r$ read this $\mathcal{K}$ (§3.3) |
| — | $F^{\mathrm{ph},f}_{w_f}$, $\mathcal{V}^{\mathrm{ph},f}$, $\gamma_f$ | A measured factor's physical POVM and alphabet, and the coarse-graining onto that factor's declared alphabet, $F^{f}_{v_f}=\sum_{w_f\in\gamma_f^{-1}(v_f)}F^{\mathrm{ph},f}_{w_f}$ | One entry of the receiver specification per measured factor, in the order of $\mathbb{F}$; no entry carries an operator on another factor's system and no product of physical families is presented |

**(c) Joint sectors, the dropped program, and the dropped first-order bound**
(`meat-core/def:joint-sectors`, `def:dropped`, `cor:drop-program`,
`prop:drop-bound`; `meat-core/frank-wolfe/cor:fo-dropped`).

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $\mathcal{G}_{\hat c,(t,s)}$, $P_{\hat c,(t,s)}$, $f_{\hat c,(t,s)}$ | The branch map, branch probability and sector deficit restricted to the cone of one joint sector | The Kraus operators act there through $\sqrt{M^{(t)}_x}\otimes\sqrt{F^{(s)}_v}$ |
| — | $E^{(t,s)}_{\kappa}$, $\mathbb{J}_K(\hat c)$ | The effective outcome set of a pass class on a joint sector, and the joint key-active index set — the pairs $(t,s)$ at which $(\hat c,(t,s))$ is not key-inert | Decided on declared data: $M^{(t)}_x\ne0$ in POVM form, $N^{(t)}_x\ne0$ in ensemble form, and a product block non-zero exactly when every factor block is, so no product is formed. At $\lvert\mathbb{T}\rvert=1$ it is $\{t_0\}\times\mathbb{S}_K(\hat c)$ |
| — | $\mathcal{D}$ | A run's dropped set $\subseteq\widehat{\mathcal{C}}_{\mathrm{key}}\times(\mathbb{T}\times\mathbb{S})$; a joint sector is *fully dropped* when every key-live value pairs with it | **A formulation choice of a run and not a declared datum**, recorded with the run. The feasible set is unchanged: a dropped block stays a variable, keeps its full weight inside $P_{\hat c}$, and enters $\boldsymbol{\Phi}$, the marginal condition and every constraint row. **Disclosed collision:** $\mathcal{D}_{\Xi}$ of §3.10 (b) is a descriptor family |
| — | $K^{\mathcal{D}}_{\hat c}$, $O^{\mathcal{D}}_{\alpha}$, $\underline{h}^{\mathcal{D}}_{\alpha}$ | The branch denominator, objective and value of the dropped program, the kept deficits only | **SECURITY-CRITICAL — §4.3 applies to it.** At $\mathcal{D}=\varnothing$ they are $K_{\hat c}$, $O_{\alpha}$ and $\underline{h}_{\alpha}$. A number a run reports from it is reported *as* $\underline{h}^{\mathcal{D}}_{\alpha}$ **together with $\mathcal{D}$**: dropping is safe, so it is a lower bound, and reporting it as $\underline{h}_{\alpha}$ would overstate which quantity was computed |
| — | $\underline{h}^{\mathrm{FO},\mathcal{D}}_{\alpha}$ | The first-order lower bound of the dropped program | **SECURITY-CRITICAL — §4.5 applies to it**, `\hlb`'s row word for word with the dropped objective in place of the objective |
| — | $W_{\hat c,(\mathsf t,s)}$ | The maximal support of a joint pair, refining `frank-wolfe`'s $W_{\hat c,s}$, with $W_{\hat c,s}=\bigoplus_{\mathsf t}W_{\hat c,(\mathsf t,s)}$ | **Document-local delta, disclosed in the claim:** `cor:fo-dropped` writes an Alice sector as $\mathsf t$ throughout, because $t$ indexes Frank–Wolfe **iterates** there (`thm:firstorder`). Elsewhere an Alice sector is $t$ |

### 3.12 Binary64 numbers and generic sector maps (`foundations`)

The symbols the `foundations` module writes for the number model
(`foundations/def:binary64`) and for a sector map of any system
(`foundations/def:sector-map`), which its definitions of exact admissibility,
the declared tolerance and the snap read. As in §3.10 and §3.11, no row is a
part A entry and none has a macro.

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $\mathbb{B}$ | The binary64 numbers: the reals $m\,2^{q}$ with $m,q\in\mathbb{Z}$, $\lvert m\rvert<2^{53}$ and $-1074\le q\le971$, the finite values of the IEEE 754 binary64 format | `def:binary64` (i). Every element is a dyadic rational. A **declared value** is an element of $\mathbb{B}$ stated as a datum, and it denotes that rational and nothing else (`def:binary64` (iii)) |
| — | $\mathbb{B}_{\mathbb{C}}$ | The complex numbers $x+iy$ with $x,y\in\mathbb{B}$ | A declared complex value is an element of it, and a declared matrix is a matrix over it |
| — | $\mathrm{fl}$ | Rounding to nearest binary64: $\mathrm{fl}(x)$ is the element of $\mathbb{B}$ nearest the real number $x$, a tie going to the even significand, and $\pm\infty$ where $\lvert x\rvert$ is too large to round into $\mathbb{B}$; on complex numbers and matrices it acts on the real and the imaginary part of every entry | `def:binary64` (ii). The binary64 sum of $a$ and $b$ is $\mathrm{fl}(a+b)$, **exact** when it equals $a+b$. `transmitter/rem:certificate-forms` writes $\mathrm{fl}(1/\sqrt2)$ in this sense. **Disclosed collision:** roman $\mathrm{fl}$ is also a *label*, the flag sector and letter of `protocol-compiler/ex:two-party-shape` and the handedness-flip parameter of the mirror in `receiver/component-catalogue/def:catalogue-entries`; applied to a number it is always this rounding |
| — | $\mathfrak{m}$ | A sector map: a block kind, a label naming what its blocks are, and a finite set $\mathsf{S}$ of block identifiers in a fixed order, each $s\in\mathsf{S}$ with a dimension $d_s\geq1$ | `def:sector-map`. Any declared decomposition of any system; a system without one carries the one-block map of its dimension. Deliberately not `\Smap` ($\mathfrak{s}$), which is the retained-register map a source link emits (§3.10 b), itself a sector map in this sense |
| — | $\mathsf{S}$ | The ordered identifier set of a sector map $\mathfrak{m}$ | For the receiver's declared sector map it is $\mathbb{S}$ (§3.3), and for Alice's $\mathbb{T}$ (§3.10 a); deliberately not `\SecSet`, which is the set of $Q$. Sans-serif like $\mathsf{n}$ (§3.10 c) and $\mathsf{h}$ (§3.3), with which it has nothing to do |

### 3.13 The round model (`foundations`)

The symbols `foundations/def:round-model` writes for the round model over a
generic per-round system, which `meat-core/def:roundmodel` takes at $Q$ and
`reductions/def:roundmodel` and `reductions/def:attset` take at $B$ and $Q$.
As in §3.10 to §3.12, no row is a part A entry: the attack channel, the attack
set and the constraint list are written with `\Aev`, `\AttSet` and `\CList`
of part B's `meat-core` group, and the identity channel with `\idmap`, with
the meanings the rows below give them at a generic system.

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $S$, $S_j$ | The per-round system of a round model, and its copy in round $j$ | A parameter: $S=Q$ in `meat-core`, $S=B$ in `reductions`' attack sequence and $S=Q$ in its attack sets; the round index is dropped where one round is in view. **Collision hazard:** $S_t$ (§3.10 a) is a matched sector, $S_{\mathsf n}$ (§3.10 c) a span of number states, and `reductions/rem:variants` writes $S$ for the private per-round **setting register** ($\mathrm{id}_S\otimes\Lambda$); none of them ranges with the round model's $S$ in one statement |
| — | $S_f$, $S_{f^c}$, $S_{f,j}$ | A factor of a product per-round system $S=\bigotimes_{f\in\mathbb{F}}S_f$, the product of the factors other than $f$, and factor $f$ in round $j$ | $Q_f$, $Q_{f^c}$ at $S=Q$ (§3.10 d, §3.11 a); $B_{f,j}$ as `reductions/def:roundmodel` writes it. **Two subscripts, told apart by their index sets:** a factor index $f$ ranges over $\mathbb{F}$ and a round index $j$ over $\{1,\dots,n\}$; with both, the factor comes first ($S_{f,j}$), and $S_j$ with a round index is never a factor |
| — | $\mathcal{A}_j$ | The attack channel of round $j$, $E_{j-1}\to S_jE'_j$, or $E_{j-1}\to A_jS_jE'_j$ where the adversary supplies Alice's system | `foundations/def:round-model` (i), Eq. `eq:round-attack`. Written `\Aev` of part B |
| — | $E_0$, $E'_j$, $E_j$ | Eve's initial register, her outgoing memory of round $j$, and her register after round $j$, which holds $E'_j$ and what the instantiating model hands her in round $j$ | `meat-core` sets $E_j=E'_jI_j$ |
| — | $\mathfrak{A}_{\mathfrak{L}}(E',SE'')$ | The attack set of a constraint list $\mathfrak{L}=\{(\hat O_k,\bowtie_k,c_k)\}$ on $S$: the channels $E'\to SE''$ (or $E'\to ASE''$) whose adjoint satisfies every listed condition | `foundations/def:round-model` (ii)–(iii); $\mathfrak{A}_{\varnothing}=\mathrm{CPTP}$. `meat-core` calls it the licensed attack set, for a licensed list. Written `\AttSet` of part B, the list `\CList` |
| — | $R'$, $R$ | The reference system of the condition of an entry tagged with a factor ($R'$ any finite-dimensional system), and $R$, which is $A$ in untrusted-source mode and trivial in trusted-source mode | Eq. `eq:round-attset-pl` |

### 3.14 Letters with more than one meaning

The letters below carry more than one meaning across the claims. Each
meaning is fixed where the row says, by a row of this catalogue or by the
claim that introduces it; this section assigns none and moves none, it lists
the meanings side by side so that a reader can tell them apart. As in §3.10
to §3.13, no row is a part A entry.

| Letter | Meanings, and where each holds |
| --- | --- |
| $\varsigma$ | The **sifting predicate** $\mathcal{K}\to\{\mathrm{pass},\mathrm{fail}\}$ of the declaration (§3.3), applied to an announcement class or compared with $\mathrm{pass}$, $\mathrm{fail}$. Elsewhere a symbol local to one claim: a **state** in meat-core `lem:range` (the state after the round's attack channel) and `rem:homog`, in `reductions/lem:party-local` (iv) (a prepared state) and in `transmitter/thm:certificate-sufficiency` (a state on $A''$); a **scalar** in `meat-core/frank-wolfe/prop:relaxed-set-properties` and `rem:feas-tol`, the normalisation offset $\operatorname{tr}[\chi_{Q}(J)]-1$ |
| $R$ | The **raw-key register** (§2.7; meat-core `def:maps`), written as a register subscript, $\ket{j}_R$, $\dyad{j}_R$. The second **reference system** of the condition of a factor-tagged constraint entry, $A$ in untrusted-source mode and trivial in trusted-source mode, always beside $R'$ (§3.13; `foundations/def:round-model`, meat-core `def:roundmodel`, `reductions/def:attset`); meat-core uses both readings, the second only in Eq. `eq:attset-pl` and the claims that read it. An arbitrary **reference system** in `reductions/cor:pullback` and `cor:transported`. Not $\mathcal{R}$, the reversal channel of meat-core `lem:purifier-indep`, nor $r$, the raw-key map (§3.3) or an exact operational reduction (§3.10 d) |
| $\Theta$ | With an acceptance value, $\Theta_{\hat c}$ and $\Theta_{\hat c,s}$: the **fail map** of the branch maps (meat-core `def:branch`, Eq. `eq:GTheta`). With an entry index, $\Theta_k$ and $\Theta^{(t)}_k$: the **right-hand side** of constraint entry $k$ (§3.3 `\CList`; meat-core `def:feasible`). The subscript tells them apart |
| $L$ | The **number of messages** of the transcript, an integer $L\geq1$ (§3.11 b; `protocol-compiler/def:declaration` (DX5)). The classical **post-processing transcript** $L=(L_{\mathrm{EC}},T_{\mathrm{EV}},F_{\mathrm{acc}})$ of meat-core `def:postprocessing-model`. The length $L_{\mathrm s}$ of a source segment (§3.10 b), and the number of vertices of a declared element graph (`receiver/def:graph`). Not the Fraktur $\mathfrak{L}$, the constraint list (`\CList`, §3.3), nor $\mathcal{L}(\cdot)$, the operators (§3.1) |
| $P$ | The **probe input** of the optical profile, a register label (`\Prb`, §3.7; `receiver`). The photon-number projector $P_n$ (`\Pnum`, `\Pnumon`, §3.2), with a block index and, where the system is not clear, the superscript $C$. With other subscripts, the branch probability $P_{\hat c}$ (§3.5), the Poisson weight $P_{\mu}(\mathsf{n})$ (§3.10) and the support projector $P_t$ (§3.11). Not $\mathbb{P}_k$, the mode set of a detector port (`\Port`), nor $\mathcal{P}_{\mathbb{S}}$, the sector pinching (§3.4) |
| $S$ | Plain $S$, $S_j$: the **per-round system** of a round model (§3.13). In meat-core `fact:meat`, the source's symbols: $S_j$ the per-round register whose entropy is bounded and $S_{\Omega}$ a convex set of distributions containing every frequency vector of the accepted state, which `thm:accumulated-entropy` instantiates as $Z_j$ and $\mathcal{S}_{\mathrm{acc}}$. $S_t$ is a matched virtual sector (§3.10 a), $S_{\mathsf n}$ a span of number states (§3.10 c), and $S_t$ in `meat-core/frank-wolfe` (`thm:firstorder`, `cor:fo-dropped`) a block list satisfying the feasible-side inequality at iterate $t$, for which a run uses the verified lower bound $b^{\mathrm F}_t$ instead; `reductions/rem:variants` writes $S$ for a setting register (§3.13). Not $\mathbb{S}$, the sector index set of $Q$ (`\SecSet`, §3.3), nor $\mathsf{S}$, the identifier set of a sector map (§3.12) |
| $\widehat{C}$ | $\widehat{C}$ is the acceptance-statistic **register** and $\widehat{\mathcal{C}}$, calligraphic under the hat, its **alphabet** (`\Chat`, `\Chatset`, §3.3); $\hat c\in\widehat{\mathcal{C}}$ is an acceptance value. Not the channel input $C$ of the optical profile (`\Chan`, §3.7), nor the message alphabets $\mathcal{C}_A$, $\mathcal{C}_B$, $\mathcal{C}_m$ (§3.3, §3.11 b), nor the announcement register $C_AC_B$ (§2.7) |
| $\Phi$, $\phi$ | Bold $\boldsymbol{\Phi}$: the **statistics map** $\mathcal{L}(AQ)\to\mathbb{R}^{\widehat{\mathcal{C}}}$ (`\Phimap`, §3.4; meat-core `def:maps`, `protocol-compiler/def:phi`). Lower-case $\phi$: the **acceptance-statistic map** $\mathcal{K}\to\widehat{\mathcal{C}}$, a slot of the declaration (§3.3). Upright $\Phi$, local to one claim: the statistics vector $\boldsymbol{\Phi}[\omega_{AQ}]$ of one state in the proof of meat-core `thm:reduction`, and a channel in `reductions/lem:precomposition`; $\Phi^{+}$ (`\Phip`) labels a maximally entangled vector in `transmitter/cor:noncanonical` |
| $W$, $\mathcal{W}$ | Italic $W$: the **full protocol isometry** (`\Wprot`, §3.4; meat-core `def:maps`). Calligraphic $\mathcal{W}$: the **feasible set** (`\Feas`, §3.5), with $\mathcal{W}^{J}$ its Choi form (meat-core `thm:choi`) and $\mathcal{W}^{J}(\varepsilon)$ the relaxation of that form (`meat-core/frank-wolfe/def:relaxed-feasible-set`). Subscripted $W$: the fixed-marginal Choi factor $W_{\tau}$ (§3.5) and the maximal supports $W_{\hat c,s}$, $W_{\hat c,(\mathsf t,s)}$ (meat-core `def:branch-support`, §3.11 c). The $W$ of a protocol presentation $\mathsf{P}=(\mathbb{A},W,\mathsf{out})$ is its tuple of output registers (§3.10 d; `reductions/def:opreduction`) |
| $Y$ | The **classical outcome register** of the measuring parties, alphabet $\mathcal{V}$ (§2.7; meat-core `def:maps`); `reductions/def:msm` writes $Y$ for the outcome register of a measurement channel, alphabet $\mathcal{V}$, in the same role. Not $\mathcal{Y}$, the optical profile's six-outcome alphabet (`\Yset`, §3.7), which is no alphabet of $Y$. Inside proofs $Y$ is also a generic operator (meat-core `lem:range`, `reductions/lem:party-local`, `transmitter/thm:certificate-sufficiency`) |
| $\Sigma$ (`receiver`) | A **mode subset** $\Sigma\subseteq\mathbb{M}$, the support of a local element and the index of $E_{\Sigma}$, $G_{\Sigma}$ (`receiver/def:embed`; $\Sigma_e$ in `receiver/def:graph`). In $A_{\Sigma}\coloneqq A_{[K]}$ (`receiver/def:gram`) the subscript is a fixed label for the sum of all port Grams, not a mode subset |
| $V$ (`receiver`) | The **vertical polarisation**, $\pi\in\{H,V\}$ (`receiver/def:modes`; `\Dset`, §3.7). The **measurement isometry** of a receiver (`receiver/def:physmodel`, Eq. `eq:measisometry`). The **vertex set** of a declared element graph $(V,E)$ (`receiver/def:graph`). The subscripted isometries of §3.4 ($V_{\mathrm{msm}}$, $V_{\mathrm{ann}}$, …) are meat-core's and always carry their subscript |

### 3.15 Enclosures and the certified tier

The symbols of the certified tier (`foundations/def:tiers` (iii)): the
enclosure bounds of `foundations`, the certified number of
`meat-core/frank-wolfe`, and the receiver's rigorously evaluated weight. As in
§3.10 to §3.14, no row is a part A entry.

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| — | $\lVert X\rVert_{\mathrm F}$ | The Frobenius norm $(\sum_{i,l}\lvert X_{il}\rvert^{2})^{1/2}$ | `foundations/cor:least-eigenvalue-over-enclosure`. It bounds the operator norm $\lVert X\rVert$ (`\opn`) from above, and the matrices an entrywise enclosure with radii $r$ contains lie in the Frobenius ball of radius $(\sum r_{il}^2)^{1/2}$ around its centre |
| — | $(L_c,t,W)$ | A factor enclosure of a $d\times d$ matrix $X$: a matrix box $(L_c,t)$ of $d\times k$ columns (centre in $\mathbb{Q}(i)$, rational radii) and a diagonal core $W$ with positive rational entries, with $X=LWL^{\dagger}$ for some $L$ in the box | `foundations/def:factor-enclosure`; the rank it fixes, `foundations/cor:rank-over-factor-enclosure`. Carried beside a block's entrywise enclosure, never in its place. The core $W$ is unsubscripted; the frames $W_{\tau}$, $W_t$ of `meat-core` always carry a subscript |
| — | $(\mathbb{O};\mathbb{O}_1,\dots,\mathbb{O}_K;\Omega)$ | A port dilation: an isometry $\Omega$ from the input modes into a mode set $\mathbb{O}$ with port subsets $\mathbb{O}_k$, $\Omega^{\dagger}\Omega=\mathbb{1}$, whose compressions are the port Grams | `receiver/def:port-dilation`; the columns $c_m$ of a block through it, `receiver/thm:factor-blocks`; per catalogue entry, `receiver/component-catalogue/lem:catalogue-dilations` |
| — | $f^{[1]}(x,y)$ | The first divided difference of $f$, $(f(x)-f(y))/(x-y)$, and $f'(x)$ at $x=y$ | `meat-core/lem:dk`, `foundations/lem:matrix-function-perturbation` |
| — | $\mathrm{D}_P[H]$ | The divided-difference map of $x\mapsto x^{p}$, $0<p<1$, at a positive definite $P$: $\sum_{a,b}f^{[1]}(\mu_a,\mu_b)\Pi_aH\Pi_b$ | `foundations/lem:matrix-function-perturbation` (iii). It is the sum of `meat-core/lem:dk` Eq. `eq:dk` for $f=x^p$; $J_p$ and $c_p=1/J_p$ are local to that lemma |
| — | $\underline{h}^{\mathrm{cert}}_{\alpha}$ | The certified number: the largest of finitely many certified brackets $b^{\mathrm A}_t+b^{\mathrm F}_t$ | **SECURITY-CRITICAL — §4.5 applies to it.** `meat-core/frank-wolfe/cor:certified-keylength` (Eq. `eq:hcert`). A lower bound on $\underline{h}_{\alpha}$ **of the declaration it is formed on**; the `certified` tier of `foundations/def:tiers` and the headline key rate where `req:certified-evaluation` reports it at that tier |
| — | $\check\gamma$, $\check\beta_k$, $\check c$, $\check d_k$ | Enclosed bound data of a setting: reals bounding its bound data on the conservative side, $\check\gamma\le\gamma$, $\check\beta_k\ge\beta_k$, $\check c\le c$, $\check d_k\ge d_k$, within $[0,1]$ | `receiver/def:enclosed-weight` (i). The check accent always marks the conservative enclosure, never an estimate |
| — | $\check\beta$, $\check T_m$, $\underline{\check\beta}_{N,m}$ | The bound function, tail and window-and-tail value formed from enclosed bound data | `receiver/def:enclosed-weight` (i); each is at most its exact counterpart (`receiver/thm:enclosed-weight` (ii)) |
| — | $w(n)$, $\check\ell(n)$ | Rigorous window bounds, $w(n)\le\beta^{\ast(t)}(n)$, and $\check\ell(n)=\max\{\check\beta(n),w(n)\}$ | `receiver/def:enclosed-weight` (ii), Eq. `eq:enclosed-ell` |
| — | $\check p^{(t)}_{\mathrm{mc}}$ | The enclosed weight of a setting | `receiver/def:enclosed-weight` (iii). **SECURITY-CRITICAL:** a lower bound on the multiclick element by theorem (`receiver/thm:enclosed-weight` (iii)), with no computed eigenvalue and no eigenvalue slack; the emitted weight is it rounded down |
| — | $\operatorname{clip}(x)$ | $\min\{1,\max\{0,x\}\}$ | `receiver/thm:enclosed-weight` (i) |

---

## 4. Security-critical symbols

> **The rows in this section are the ones where a transcription slip becomes a
> silent security bug rather than a typo.** A reviewer must confirm each of
> them independently against the source, not merely spot-check the table.

### 4.1 The arrow: `\Hsandup` vs. `\Hsanddown`

$$\widetilde{H}^{\downarrow}_{\alpha} \;\leq\; \widetilde{H}^{\uparrow}_{\alpha}$$

The $\uparrow$ variant optimizes over the conditioning-system state; the
$\downarrow$ variant fixes it to the marginal. Substituting $\downarrow$ where
a proof establishes $\uparrow$ **inside a lower bound** is conservative (rate
loss, not a break); the reverse substitution inflates the certified entropy and
produces a key the adversary may partially know — **silently**, because the
arithmetic still type-checks. Rules:

1. Never change an arrow to make an inequality "work out". If an arrow appears
   wrong, the derivation is wrong; escalate rather than patch.
2. Never silently convert between the sandwiched ($\widetilde H$) and Petz
   ($\overline H$) families.
3. State the direction of every bound explicitly ("lower bound on
   $\widetilde H^{\uparrow}_{\alpha}$", not "bound on the entropy").

Meat-core's only exchange is $\widetilde H^{\uparrow}\to\widetilde
H^{\downarrow}$ inside a lower bound (`thm:reduction`, conservative).

### 4.2 `\hqkd` carries the arrow

`\hqkd` renders as $h^{\uparrow,\mathrm{QKD}}_{\alpha}$ — the arrow is **part
of the symbol**. Writing $h^{\mathrm{QKD}}_{\alpha}$ is not an abbreviation;
it is a different, undefined object. Reproduce the superscript in full,
including the comma. Compare `\hup` ($h^{\uparrow}_{\alpha}$), one superscript
away.

### 4.3 `\hlow` is the computable relaxation

$$\underline{h}_{\alpha} \;\leq\; h^{\uparrow,\mathrm{QKD}}_{\alpha}$$

The underline means "relaxed downward" and carries no arrow. The safe chain is
final key rate $\leftarrow \underline{h}_{\alpha} \leq
h^{\uparrow,\mathrm{QKD}}_{\alpha}$; never upper-bound a key rate by
$\underline{h}_{\alpha}$ and treat that as a guarantee. Two range facts fixed
by meat-core (Proposition `prop:value-range`):
$\underline{h}_{\alpha}\in[0,+\infty]$ with **no finite a-priori ceiling**
(the KL penalty is unbounded), and $\underline{h}_{\alpha}=+\infty$ signals an
infeasible acceptance set, on which no key-length claim may be emitted
(Requirement `req:infinite-value`); clamping it to a finite range is a defect.

### 4.4 The MEAT penalty divergence is KL, not Rényi

The penalty term of the imported single-round rate (`arqand2025meat`
Cor. 4.2/Eq. (137)) is $\frac{\alpha}{\alpha-1}D(\mathbf q\|\cdot)$ with $D$
the **base-2 KL divergence** — the source's Eq. (118) says so in words
("where the first term is the KL divergence"). Writing $D_{\alpha}$ there
makes the imported theorem **false**. Rules:

1. $D$ in a MEAT rate is KL. $D_{\alpha}$ appears in **no** current claim; any
   new use of it must be independently justified against a pinned source.
2. A quoted import is verified only by re-opening the source, in the version
   `refs/index.json` pins, at the locator — an extraction, a transcription,
   or a recorded conclusion
   (including in a review report) is evidence, never authority.

### 4.5 `\hlb` is the first-order lower bound — and is not `\hlow`

The three tiers of the assurance ladder are `foundations/def:tiers`:
estimate, first-order and certified.

$$\underline{h}^{\mathrm{FO}}_{\alpha} \;\leq\; \underline{h}_{\alpha}
  \;\leq\; h^{\uparrow,\mathrm{QKD}}_{\alpha}$$

**Four numbers, and confusing them is the failure this row exists to prevent.**

1. $\underline{h}_{\alpha}$ (`\hlow`) is a **quantity**: the value of the
   relaxed optimization problem. §4.3's range fact
   $\underline{h}_{\alpha}\in[0,+\infty]$ is a fact about *it*.
2. The **estimate** a run reports is the objective evaluated at the point the
   optimizer returned. At an exactly feasible point that number is an
   *upper* estimate of $\underline{h}_{\alpha}$ (`meat-core/lem:estimate`).
   A run establishes its returned point only in the relaxed feasible set,
   where the estimate bounds the relaxed value
   $\underline{h}_{\alpha}[\mathcal{W}^{J}(\varepsilon)]\le\underline{h}_{\alpha}$
   from above and need not lie above $\underline{h}_{\alpha}$
   (`meat-core/frank-wolfe/thm:firstorder` (iiia)). It is never a bound on
   the key rate. It has no symbol here, deliberately: it is a diagnostic of a
   computation, not an object of the mathematics.
3. $\underline{h}^{\mathrm{FO}}_{\alpha}$ (`\hlb`) is the **first-order
   bound**: the maximum over iterates of the linearization of the objective at
   the iterate, which lower-bounds the true minimum by convexity. It is a lower
   bound on $\underline{h}_{\alpha}$ in exact arithmetic **given lower bounds
   on its two linear minima**, which the owning contract forms without trusting
   the oracle (`meat-core/frank-wolfe/lem:feasible-side-dual`); it is not a
   certificate, its objective and gradient being evaluated in binary64.
4. $\underline{h}^{\mathrm{cert}}_{\alpha}$ is the **certified number**: the
   same bound formed again at a run's final points from enclosures of the
   gradient, every step from the declaration's data exact or rigorously
   enclosed (`meat-core/frank-wolfe/cor:certified-keylength`,
   `req:certified-evaluation`). It bounds $\underline{h}_{\alpha}$ of **the
   declaration it is formed on**, and the clamp below applies to it as to
   $\underline{h}^{\mathrm{FO}}_{\alpha}$.

**The clamp is sound, and §4.3 is why.** A computed
$\underline{h}^{\mathrm{FO}}_{\alpha}$ may come out negative — the
linearization is weak, or rounding crosses zero — and what a run reports is
$\max\{0,\underline{h}^{\mathrm{FO}}_{\alpha}\}$, flagged. Zero is a valid
lower bound on $\underline{h}_{\alpha}$ *precisely because* §4.3 fixes the
range at $[0,+\infty]$, so raising a lower bound to zero cannot overstate
anything. This is not the clamping §4.3 forbids: that rule concerns
$\underline{h}_{\alpha}=+\infty$, the signal of an infeasible acceptance
set, which is never brought down into a finite range.

**A negative estimate is a different matter and is never clamped.** At an
exactly feasible point the objective is non-negative (§4.3), and at a point of
the relaxed set it is bounded below by
$-\frac{\alpha}{\alpha-1}\log_2(1+d_{A_0}\varepsilon)$ where
$d_{A_0}\varepsilon<1$, in the state form with $d_A\varepsilon$ in
trusted-source mode and $\varepsilon$ in untrusted-source mode in place of
$d_{A_0}\varepsilon$ (`meat-core/frank-wolfe/prop:relaxed-set-properties`
(c''), `meat-core/frank-wolfe/req:negative-estimate-refused`), so a negative
estimate is evidence that a hypothesis does not hold of the point it was
computed at. It is a typed refusal.
Clamping it to zero would replace a detected inconsistency with a plausible
number, which is the shape of error this document exists to prevent.

---

## 5. Settled conventions

### 5.1 A symbol absent from the catalogue is not invented

If a contract needs a symbol that is not in §3, it does not invent a
definition: the symbol is put to the maintainer.

### 5.2 One name per map

This catalogue gives each map one name: $\boldsymbol{\Phi}$
**is** the test-statistics map and `\testE` is a deprecated alias;
$\mathcal{Z}$ **is** the key pinching on $R$ and `\Pdeph` is deprecated (its
dephasing role is an instance of the general
sector pinching $\mathcal{P}_{\mathbb{S}}$); $\mathcal{M}$ is the single-round
protocol channel and $\mathcal{G}_{\hat c}$ are its key branches (so `\cG`
and `\Mprot` name different, precisely related objects). See §3.4 and §3.9.

