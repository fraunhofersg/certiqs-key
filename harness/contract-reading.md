# Reading contracts and graphs

Start at the [project site](https://fraunhofersg.github.io/certiqs-key/latest/),
which links each module's contract PDF, digest and graphs, or at
[spec/overview/overview.pdf](../spec/overview/overview.pdf), which collects
every contract's main results. The repository-wide
[core module map](../spec/module-graph.svg) shows the registry's declared
dependencies. Arrows point from a module to a declared dependency: these are
allowed imports, not execution order or a claim that every module uses every
allowance. A filled box means claim files exist, not that the module is
accepted.

For **how inputs become a key rate**, start with the
[conceptual data-flow diagram](../spec/architecture.md#6-protocol-compilation-and-meat-flow).
It shows both the receiver/reduction route and directly supplied finite POVMs
with an explicit identity link. It is authored in the architecture; it does
not duplicate the interfaces or infer execution from
import dependencies. Module-local branches remain in their design notes.

## In a contract PDF

The layout is the one `spec/style.md` sections 3 to 6 describe.

- **Grey text is non-normative.** The opening page says so once: the module
  overview, each section's introduction, each claim's summary (the grey
  italic line above its heading) and its lead-in (grey, before the heading)
  explain; the statements, proofs and declared assumptions are the contract.
- **The opening pages**: title and version, the overview, links to the
  design notes, the graph index and these instructions, the contents; then
  **Main results** (every claim marked `prominence: main`, listed by number,
  title and summary, each linked to its statement and with every assumption
  it rests on, directly or through what it uses; the digest has them in
  full), **Assumptions at a glance** (every assumption the
  contract states or its claims assume, with who assumes it),
  **Notation** (the rows of `spec/notation.md` whose symbols the contract
  uses) and **Terms** (every phrase the contract defines, and every term of
  another contract it uses, with a one-line gloss and a link to its
  definition). In the overview, the section introductions and the claims, a
  linked term opens its definition.
- **Parts**: Part I is the core's mathematics, its assumptions closing it;
  Part II the core's engine requirements (what an implementation must do or
  refuse), when it has any; then one part per submodule, its mathematics
  before its requirements. Sections are numbered through the whole PDF and
  every claim is numbered within its section on one counter, so
  "Proposition 7.3" names one claim, whatever its kind. The graphs and
  `graphs/README.md` use the same numbers.
- **A claim** reads: summary, lead-in, the numbered heading with its title
  (an assumption also shows its short id, such as [A-SEQ]), the statement,
  a small grey **meta line**, the proof. The meta line lists what the claim
  uses (for a requirement: what motivates it), the assumptions it declares,
  for an assumption who assumes it and the machine key the run ledger
  records it under, what uses the claim, its provenance (with the citation
  of a published result), its status (and its effective status when a claim
  it rests on is less settled), its code and the oracle registries that pin
  it. "Def. 2.1" and the like link inside the PDF; a full claim id links
  into another contract's PDF (purple links open another file).
- **Styles**: a main result has a thin coloured rule in the margin and a
  bold heading; a technical step a grey heading; a remark or example
  smaller type; a requirement a small-caps heading in an accent colour.
  Each distinction survives greyscale printing.
- **Section openings**: a grey introduction, then, in small type, the claims
  of other contracts the section's claims use (*Imports*).
- **The back**: the declared inputs and outputs of `interface.yaml` (key,
  symbol, presence and the claims that fix it), the claim index (number,
  title, identifier, page), the index of defined terms, the references.
- Open your PDF viewer's **Bookmarks** or **Document outline** pane: parts,
  sections, and each claim as "Theorem 2.5 Title", numbered as in the text.
- **The digest** (`digest.pdf` beside each contract) holds only the
  statements of definitions, facts, assumptions, results and requirements,
  with the contract's numbers; a heading opens the claim in the contract.
- **The overview** (`spec/overview/overview.pdf`) lists every contract's main
  results in module dependency order, linked into the contracts, and draws
  the module map.

A link into another PDF (the digest, another contract, a claim in it) is a
relative web link, `<file>#nameddest=<destination>`, which browser viewers
such as Edge and Chrome follow; Adobe Acrobat may ask before opening it or
open it in a browser. Keep the directory layout of the clone so the relative
paths resolve.
Claim titles in navigation come from their metadata. The claim index retains
mathematical TeX; graph labels and bookmarks strip formatting and retain math
macro names rather than copying raw TeX commands. The dependency matrix
between sections is not printed in the PDF; it is `graphs/overview.svg`,
linked from the opening page.

## Where the graphs live and how to open them

Each core has `spec/modules/<id>/graphs/README.md`, a **generated index**.
Open it in the repository website or a Markdown preview. It carries the same
module, submodule, group and claim summaries as the PDF, beside links to the
mathematical sources. It links:

- `overview.svg`: a matrix of the contract's sections and their dependencies.
  Open in a browser; zoom normally, and click a section to open its detailed
  dependency view.
- `group-NN-topic-title.svg`: one section's claims plus their immediate external
  prerequisites. Dashed boundary boxes explicitly omit those prerequisites' own
  dependencies. NN is the section's number in the PDF; the suffix comes from
  its title (prefixed by the submodule's title for a submodule's section).
- `claims.svg`: all local claims and immediate external prerequisites; useful
  for searching and zooming, usually too large for a printed page.
- `overview.pdf`: the same matrix as a standalone printable page.
- `groups.svg`: the complete arrow graph between groups, for zooming rather
  than fitting densely connected modules onto a printed page.
- `.dot` files: generated Graphviz sources, for alternate layouts or export.

No server, JavaScript, account or extension is needed to view an SVG. Download
it or use **Raw** if the repository website displays its source. Keep the
directory structure when downloading if you want relative links to work.
Every claim node offers **TeX source** and **Rendered PDF** links. The first
opens the original claim file; the second opens the claim in the owning core's
contract PDF, including for external boundary claims. The index
offers the same pair. This reuses the normal TeX build, including the project's
macros and citations, with no second renderer or extra dependency. Opening
source may download the file depending on browser settings. Open the two links
in separate tabs/windows to compare; there is no custom split-view application.

PDF links use stable named destinations, not page numbers. Viewer support
varies; if a browser opens the PDF at its beginning, use its bookmarks or
claim index, or a desktop PDF viewer that supports named destinations. Keep
the destination module's PDF built and the repository directory layout intact.

**Dependency arrows point from claim to prerequisite.** Solid edges are
`uses`; dashed amber edges are `assumes`. `mentions` are not proof edges and
are excluded. Status is written on each claim as well as indicated by colour.
Pending references are counted on nodes, not invented as resolved edges.
An overview edge means *at least one* dependency crosses the two groups.
Internal edges are hidden. Collapsing groups can introduce cycles even when
the claim-level `uses` graph is acyclic. None of these views verifies that
the declared dependencies are complete or mathematically justified.

## The explanatory flowcharts

The section **The module's main logic** of each module's `design.md` is the
one authored source of its Mermaid processing flowchart. It
explains data transformations, gates and branches; it is non-normative and
is not the generated proof-dependency graph.

Open `design.md` on the repository website to see the rendered Mermaid
diagram. Locally, use a Markdown preview with Mermaid support; if the preview
shows a fenced text block, that viewer does not render Mermaid. The graph
index links directly to this section. Generation cannot prove that
explanatory prose is correct: a change of meaning is reviewed in the diagram
alongside the claims.

The architecture's cross-module diagram uses the same Mermaid preview. A
run record also carries a **run-specific** `composition_flow`: the ordered
stages actually selected, their executed/refused/not-executed outcomes and a
Mermaid rendering of that same list. The
[run flow implementation](../src/certiqs_key/runs/flow.py) derives the diagram
from recorded stages.

## Rebuilding

The PDFs, digests, graphs and indexes are generated from the claim files and
`module.yaml`; [harness/README.md](README.md) lists the tools that rebuild and
check them. `python -m harness.check_claims --focus <claim-id> --graph
<file>.svg` draws one result's full prerequisite closure across module
boundaries.
