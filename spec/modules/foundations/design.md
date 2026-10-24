# Foundations: design notes

Working design notes of the `foundations` module (`spec/modules/foundations`):
why its claims are shaped as they are. Non-normative and in places dense; the
claim files and `interface.yaml` are authoritative. The module's `interface.yaml` holds only the ledger row of its one
assumption, `ass:snapped-measurement` (A-SNAP), with the machine key run
records carry it under; the module has no inputs or outputs of its own, and
its code is described under "Where the code is".

## Module summary

Read the [generated module summary](graphs/README.md#module-summary), shared
with the contract PDF. The design rationale follows here.

## Why the module exists

The number model, the tolerance policy and the emission rules are rules that
claims of several modules rely on: a consumer's admission, a producer's
emission, the reason no module takes a tolerance, the claim that a computed sum
is the real sum. A rule a statement relies on is a claim (`spec/style.md` §2):
it has one owner, it is reviewed like the rest of the mathematics, a claim that
relies on it says so with a `uses` edge, and `check_claims --dependents`
computes who is affected when it changes. `foundations` is that owner. It sits
at the bottom of the claim graph, depends on nothing, and none of its
mathematics is specific to a protocol, so every module may use it.

## Structural decisions

1. **The common core, not a merged definition.** The admission definitions of
   `reductions` and `protocol-compiler` differ in scope. `foundations` states
   the five conditions they share (`def:exact-admissibility`): agreement of the
   sector maps, Hermiticity, positivity, completeness and a completeness sum
   that rounds nowhere. The completeness constant is a parameter, so the one
   definition covers a measurement (constant one) and a class of one
   (constant a class weight). What only one module states stays with it: the
   declared lattice as an admission condition, the scope clause for objects no
   finite list of matrices presents, the conditions on Alice's data and her
   marginal's trace, the ensemble form, the general format, and the definition
   of the declared order through the compiler's index map.

2. **Four parties, and a supplier is not a producer.** `def:declared-data`
   names the instance, the supplier, the producer and the consumer. The
   receiver evaluates its own conditions in floating point at slacks an
   instance declares to it, and its output reaches the other modules only as
   the instance's declaration. A supplier is defined by that contract and not
   by how a run wires it: the run tier may hand the receiver's rows on
   untouched when an instance sets no rows adapter, and those rows are then
   numbers the instance passes on unchanged, which the consumer decides
   exactly on entry, so the classification does not change with the wiring.
   Calling such a module a supplier keeps
   every requirement of this module true of the receiver as it stands: the
   exact rules bind the declared path, from the instance's declaration to the
   key rate, and the instance is the declarer of what a supplier computed.
   That includes the numbers the instance passes on unchanged beside the
   blocks it snaps (the receiver's high-photon weights, dark-count channel
   and bound evaluation): the consumer reads the whole artifact as the
   instance's declaration and decides it exactly on entry, and were the
   receiver their producer, the producer's obligations would bind a module
   whose own contract decides in floating point.

3. **Rules that need a lattice bind only a party that declares one.** The
   compiler and the transmitter declare no lattice exponent and never snap
   their emission; they decide exact admissibility of what they emit and
   refuse otherwise. `req:declared-lattice`, `req:rounding-direction` and
   `req:exact-emission` therefore state the rule in its general form and
   then say whom it binds: the lattice condition, the rounding onto a
   lattice and the snap route of the emission rule bind a party that declares
   a lattice exponent, and a producer that declares none establishes the other
   five conditions or refuses.

4. **The lattice condition is read per part for a complex entry.** The one
   module that states the lattice as an admission condition reads a complex
   entry through its real and imaginary parts; `req:declared-lattice` does the
   same, so that it imposes nothing that module does not.

5. **The snap route of the emission rule is open on the lattice condition as
   well.** The emission rule's text opens the route where the constructed
   family fails Hermiticity, positivity or completeness; the snapping rule
   re-establishes the lattice at every emission whose construction lies off
   it. `req:exact-emission` reads the two together, which is what the
   emission normaliser of `reductions` does.

6. **Three tiers, and only their vocabulary and reporting.** `def:tiers` and
   `req:tiers` fix the labels, the rule that each tier a run reaches is
   reported with the strongest named as the one that carries the claim, and
   the refusal of any other tier. What the first-order bound must not do
   (named hypotheses, no gradient perturbation, the composite point after the
   clip) and how the certified evaluation forms its number are the
   Frank–Wolfe solver's own mathematics and stay in `meat-core/frank-wolfe`;
   the reporting of a negative bound stays with `meat-core`'s key-length
   claims. The facts that number needs and that are not about a protocol stay
   here: the least-eigenvalue bound and its form over an enclosure, the rank
   rule over an entrywise enclosure, and the perturbation bounds for matrix
   functions (`lem:least-eigenvalue-bound`,
   `cor:least-eigenvalue-over-enclosure`, `lem:matrix-function-perturbation`),
   derived in full here rather than imported, so that no reference is
   registered for them. `req:exact-island` admits rigorously enclosed
   computation beside the island as neither the island nor an error budget.

7. **A counterexample instead of a pointer.** `rem:computed-completeness`
   exhibits a family whose computed completeness sum is exactly one while its
   true sum is not. Both module definitions give this as the reason the
   rounds-nowhere condition exists, and neither states it.

8. **Symbols of the module's own for a generic sector map.** The catalogue's
   sector index set is that of the receiver's measured system, and its
   fraktur sector map is the one a source link emits. A sector map here is any
   declared decomposition, of any system, so the module writes
   $\mathfrak{m}$ for a sector map and $\mathsf{S}$ for its identifiers; for
   the receiver's declared sector map the identifier set is the catalogue's
   $\mathbb{S}$. These two and the binary64 symbols $\mathbb{B}$,
   $\mathbb{B}_{\mathbb{C}}$ and $\mathrm{fl}$ are catalogued in
   `spec/notation.md` §3.12 as plain LaTeX without macros, so no part A entry
   moves; the module's `notation_version` pins a catalogue that contains them.

9. **The exact island is drawn at decisions and certificates.** It holds
   every decision that data satisfy the conditions their declaration states,
   whoever takes it (a consumer on what it reads, a declarer, and so a snap,
   on what it is about to declare), a producer's construction, and, on the
   acceptance side of the optimisation, the construction of the acceptance
   set, the exact establishment that the iterate lies in it, and the exact
   certification of the acceptance-side minimum or of a lower bound on it.
   How a candidate is found is not on the island: the Frank–Wolfe
   submodule's acceptance-side point may be chosen by a binary64 closed form
   and then formed exactly as a member, and a lower bound may be a downward
   rounding of an exact value, or a rounded dual certificate re-verified
   exactly. That is what the submodule's own claims require (membership and
   the bound established exactly), and a rule forbidding every rounding on
   the way to a candidate would be stronger than they are. The ceiling of the
   declared tolerance is decided on binary64 measurements, taken on the data
   before any step of the snap, and is not on the island: whether data lie
   within a tolerance is not a condition their declaration states, and it
   decides only whether an instance may repair, the repaired data then being
   decided exactly.

   One further scoping: the honest distribution and the completeness budget
   that instances and runs hand the statistics module are declared exact
   rational data, which the statistics module reads and decides exactly; how
   an instance arrives at its honest model (the coherent-pulse model, for
   instance, evaluates exponentials at high decimal precision before stating
   exact rationals) is the instance's modelling and is not on the island.

   **The acceptance set the optimiser reads is the set so declared.** The
   statistics module constructs its acceptance set from those data and emits
   it as exact rationals; it is the producer and the declarer of that set.
   Its consumer, `meat-core`, reads the set into its own binary64 type through
   its docking adapter (`src/certiqs_key/meat_core/docking_statistics.py`,
   whose owner and direction the statistics interface records under
   `artifact_bindings.docking`), rounding each lower bound of the box down and
   each upper bound up and building the half-space rows from the rounded
   pair. That is a consumer altering a producer's data, which the two
   no-alteration requirements would otherwise forbid, so both state it as
   their one exception: a consumer may replace an emitted scalar bound by that
   bound rounded to a binary64 number in a direction the producer's own
   claims license as weakening it (here `statistics/binomial-box/lem:widening`: a lower
   endpoint may move down and an upper one up, never the reverse), records
   the direction where its reading is specified, and alters nothing else.
   `req:consumer-decides-exactly` states the exception with its limits and
   `req:who-snaps` refers to it. The decision that a replacement lies on the
   weakening side of the emitted bound is on the island, in (i), and the
   adapter takes it exactly (a binary64 candidate, then an exact comparison
   with the rational). The set so read contains the set constructed, so an
   iterate established in it and a minimum certified over it cost rate and
   never soundness.

   The rejected alternative makes the run tier, acting for the instance, the
   declarer of the docked set, with the statistics module a supplier of it.
   The exception is preferred because it keeps the statistics module a
   producer, which is what its own contract says it is (every number it emits
   is an exact rational, decided exactly), and it states the one alteration
   the tree makes where the rule against alteration is stated, rather than
   stretching who counts as an instance.

10. **Six simpler rules the claims reject.** Each would be shorter to state;
    each is either false of the tree or binds a party it should not.
    - *Calling the estimate an upper estimate* (`def:tiers`) is rejected
      because the objective at the point an optimiser returned is established
      only at a point of the relaxed set the solver works in, so it is not in
      general an upper bound on the minimum.
    - *Recording every snap in the run record with its measured pre-snap
      defect* (`req:who-snaps`) is rejected for a producer's snap. A
      producer's constructed family is exact data and the exact reference of
      its snap; nothing relates the emitted family to it, and a run that
      needs no such relation evaluates off the snap on the reference
      companion; the emission discloses the displacement and the rounding
      direction of every weight (`req:exact-emission`, decision 12).
    - *Moving an emitted bound by one unit in the last place*
      (`req:rounding-direction`) is rejected because the emission normaliser
      of `reductions` rounds a bound down or up onto its declared lattice,
      which is in general more than one unit in the last place; the direction,
      not the size of the step, is what keeps the bound a bound.
    - *Admitting a prepared probability vector only within the declared
      tolerance* (`req:declared-tolerance`, `req:who-snaps`) is rejected
      because the input preparation of `PRINCIPLES.md` §9 also admits a vector
      where the rounding cells of its inputs contain a normalised vector, and
      its snap runs at a recorded guard that may exceed the declared
      tolerance. That is a front-end reading of what an ordinary float input
      denotes, not a wider repair of declared data, and the claims state the
      rule the code follows.
    - *No result resting on a floating-point error budget, anywhere*
      (`req:exact-island`, `req:tolerance-scope` (iii)) is rejected because
      the receiver's exact window, where the receiver evaluates it in
      floating point, subtracts a declared slack from a computed eigenvalue
      under its assumption A-EIG, which it cannot verify, and a key length can
      rest on it (never a key length at the certified tier). The claims state the exception with its limits (a
      supplier, a named assumption carried in its output). Filing that slack
      as a physical bound is rejected for the same reason: it bounds a
      floating-point evaluation error, and it is never derived from the
      declared tolerance.
    - *A declared order binding every party* (`req:declared-order`) is
      rejected because a supplier decides its own conditions in floating point
      at declared slacks, and its contract carries no summation order; the
      order binds consumers and declarers.

11. **The round model once; its instances and the round assumptions where
    they are.** `def:round-model` states what the round models of `meat-core`
    and `reductions` share, the rounds, the attack sequences and the attack
    sets, for a generic per-round system. `meat-core/def:roundmodel`
    instantiates it at the squashed system, and `reductions/def:roundmodel`
    and `reductions/def:attset` at the physical and the squashed system; each
    keeps its own displays, because other claims cite their equation labels.
    The definition holds nothing a module's own claims supply: no protocol
    channel, no announcement register, no squashing channel, no licence.
    `def:round-homogeneity` is the schema of the round assumptions
    (`receiver/ass:round`, `reductions/ass:round`,
    `protocol-compiler/ass:rhom`) and asserts nothing about any family: each
    assumption asserts it, or its sameness clause alone, of its own family,
    and the families differ, so none of them implies another. Its two clauses
    are kept apart because the second, no memory across rounds, is a
    condition on the rounds and is not implied by the first, a condition on
    the objects.

12. **A snap only steers the search; where a reference is held, the key
    length is formed on the model.** `meat-core/prop:optol-nobound` shows
    that two entrywise close measurements can have key-rate bounds far
    apart, by an amount the distance does not control, and a small move can
    change which outcomes are impossible. No claim therefore relates a
    snapped family to the model it replaced, and none is sought. What makes
    the snap harmless instead is that the first-order bound holds at any
    admissible points, wherever they came from
    (`meat-core/frank-wolfe/cor:fo-reference`): the run searches on the
    snapped declaration and evaluates the bound on the reference companion,
    the same chain run on a reference of the model, at the points the search
    found and at those of a short search continued on the companion from
    them (`meat-core/frank-wolfe/req:bracket-on-reference`). A block so
    evaluated is evaluated off its snap (`def:evaluated-off-snap`) and rests
    on no premise about the snap, where the key length is formed from a number on the companion (not in the fallback of `meat-core/frank-wolfe/req:certified-evaluation` (i)). A producer that snaps its own emission,
    the reductions' normaliser, carries its exact construction past its
    snap by the same companion, which the reductions form wherever a claim
    allows it, also where the instance hands no reference
    (`reductions/req:reference-companion`).

    *The reference.* A reference (`def:exact-reference`) is read through
    entrywise enclosures, a Gaussian-rational centre and rational radii,
    exact being radius zero, because photon-number blocks in the orthonormal
    occupation basis carry square roots even at rational parameters, and an
    analyser whose analysed polarisation `cos(alpha)|H> + sin(alpha)|V>` has
    an irrational `tan(alpha)` has irrational entries in the basis in which
    it is declared. The binary64 evaluation of a model is not a reference: it
    is indefinite at the `1e-16` scale on rank-deficient blocks, so its
    kernel is unknown. That an enclosed reference encloses the model and is a
    POVM is a claim of the module that constructs it, its enclosures computed
    in exact rational arithmetic; the declarer decides exactly only what can
    be read off centres and radii (`req:snap-reference` (i)). Enclosures are
    recentred so that an entry whose enclosure contains zero has centre zero
    (`lem:recentred-enclosure`), which keeps the evaluated family from
    gaining an entry where the model may have none. A reference given only
    in the scaled exact form `D^-1 S D^-1` (S Gaussian-rational, D the
    diagonal of square roots) was considered as a kind of its own and
    rejected: it is one way of producing an enclosure (`lem:enclosure-psd`
    (ii)). The evaluation at the centres is unbudgeted, a displacement of the
    measured family of the size of the radius, to which `prop:optol-nobound`
    applies as it does to a snap; the record carries the largest radius
    (`meat-core/frank-wolfe/rem:fo-arithmetic`). A run may declare that
    enclosed references are not used; it then hands only the exact blocks.

    *The snap itself.* A block known exactly on the lattice is kept and rests
    on nothing. Every other block is moved by one procedure that aims at
    fidelity to the model and is support-safe (`req:support-safe-snap`):
    nothing the data state to be zero is revived, a positivity lift acts per
    coordinate on each element's own structural support, and a residue goes
    only where the receiving element's structural support holds it. Fidelity
    is the aim because the snap matters only where a run has to rest on it,
    and there the premise should depart from the model as little as
    possible. The uniform lift, mixing with the trivial POVM, revives the
    structurally zero rows and columns of every element that has them, so it
    survives only as a last resort where the support-safe steps cannot
    restore the conditions of a snap on a block (`req:support-safe-snap`
    (iv)); the block is flagged `support_not_preserved`.

    *Disclose, or refuse on request.* A moved block that the run does not
    evaluate off its snap rests on the assumption `ass:snapped-measurement`
    (A-SNAP) that the device measures the snapped family there, recorded
    with its cause, one of four groups (no usable reference, reference
    bracket withdrawn, reference bracket not evaluated, last resort) and a
    fix (`req:snap-reference` (iii)); the strict option `strict_snaps`
    refuses instead (`req:snap-reference` (iv)). A-SNAP replaces, on those
    blocks, any premise of the run that a model describes the device, so the
    two are never asserted of the same block; for a producer's snap of its
    own emission, which is a reduction target and not a device's
    measurement, it is the premise that what the run concludes from the
    emission holds of the snapped family. Refusal by default is rejected: a
    run whose model reaches the engine without a usable reference, or whose
    bound on the companion is withdrawn, would be refused for a snapping
    reason alone, against `PRINCIPLES.md` §1 and §9; the default runs and
    makes the premise it rests on explicit and machine-readable.

    *Domination is not the route for snaps.* Relating a snap to its model by
    domination (`def:domination`, the hypothesis of the noise channel of
    `nahar2025imperfect`, Thm. 3) and carrying the weight into the key
    length through flags is the alternative, and it is rejected. It needs
    a weight ladder, a ceiling, an absorbing element and corrected entries
    route by route; it drives the key to zero on the default route; and an
    idealised model with an element whose support has no rational direction
    admits no useful weight against a lattice family at any lattice exponent
    (`lem:rational-obstruction`, `rem:noise-floor`). The domination results
    of this module stay as mathematics for a declared device range, a weight
    attested rather than computed (`spec/future-scope.md` §13).
    `rem:noise-floor` also records that the obstruction belongs to
    domination and not to rational targets: a reduction that applies a
    channel first (a common unitary for an ideal analyser with an irrational
    `tan(alpha)`; the isometry from the m-photon block into the m-fold tensor
    power of a qubit for an ideal device at N >= 2) can map such models
    exactly onto rational families, which is future scope too.

## Why exact, and the measurements behind the policy

- **Exact rather than budgeted.** Rounding at the `1e-16` level is far below
  any device characterisation a key rate is computed from, so a declared
  family that differs from the receiver's floating-point output by that much
  is as good a model of the device as the unsnapped one, provided it keeps
  the supports of the model; for a measurement family the run forms its key
  length on the model where a reference is held, and rests on a disclosed
  premise where it reads the snap (decision 12). What an exact
  substrate must never do is verify, in full space, zeros that a constructor
  wrote: that is, as measured, the dominant cost of the compile stage. Exact
  decisions on sector blocks of dimension in the single digits cost nothing
  measurable.
- **The entrywise reading of the defects.** It is chosen because it is
  independent of the dimension, because it is what the shared numerical
  kernel computes, and because it is what the tolerance is sized against.
  The two readings are not interchangeable, but they compose in the safe
  direction: a least eigenvalue of at least `-tau` puts a Hermitian matrix
  within entrywise distance `tau` of the positive cone
  (`lem:floor-stricter` (ii)), which is why one tolerance may govern both.
- **No default tolerance.** A defaulted ceiling on repair would decide a
  security-relevant act on nobody's authority.
- **Why the Frank–Wolfe feasibility number is not the tolerance**
  (`req:tolerance-scope` (ii)). It decides a coupling residual measured at
  `2.04e-10`, the drift accumulated over two hundred convex combinations of
  oracle returns, not a defect in anybody's declaration; applying the
  declared tolerance to it at any value the measurement supports would refuse
  every run at around iteration thirty.
- **Why the oracle clip has a window of its own** (`req:tolerance-scope`
  (ii)). The adapter's positivity clip on a returned Choi operator fires
  eighty to five hundred times per run at depths to `-6.87e-11`, above every
  tolerance in the recommended band; a window of the tolerance's size would
  refuse every run.
- **The cost of the exact island.** Its acceptance side (the statistics
  module, the honest distribution and completeness budget it is handed, and
  the acceptance-block linear program of `meat-core`) costs about six per
  cent of a run at $n = 10^4$. On the admission boundary, exact decisions
  on sector blocks of dimension in the single digits take microseconds; what
  costs seconds is verifying full-space zeros a producer wrote itself, which
  the block-list operator form removes.
- **The oracle's return is not trusted.** On a toy instance whose true value
  is `0`, a bound formed at the oracle's returned vertex is `4.8121e-11`, on
  the wrong side, while the exact linear-minimisation vertex at the same
  iterates gives a bracket of `+4.9e-16` / `-1.6e-15`; the whole of the
  excess is the returned vertex, not the face, the objective or the clip.
  This is why the feasible side of every bracket is a lower bound by weak
  duality, verified in exact arithmetic
  (`meat-core/frank-wolfe/lem:feasible-side-dual`,
  `meat-core/frank-wolfe/req:verified-feasible-side`). What stays binary64
  is the objective and its gradient, so `h_lb <= h_low` is not a
  floating-point invariant and clamping at zero does not repair a bound that
  is too high (`meat-core/frank-wolfe/rem:fo-arithmetic`).

## What stays out

- **Code rules**, which stay in `spec/architecture.md`: this module's code
  package is the floor and imports nothing else of the repository, and the
  shared format package imports no module package but it; the numerical kernel
  measures and never decides; the names of the exact decision functions; the steps and
  constraints of the snapping table; the run configuration's tolerance field;
  where the tier vocabulary lives; the bundle schema; and that no full-space
  matrix is formed on a live path.
- **The factorised sector map and the factorised family.** They are the
  general format of the declaration, (DX1) to (DX3) of
  `protocol-compiler/def:declaration`, which `meat-core/def:declaration`
  reads.
- **The round assumptions themselves**, which stay with the modules whose
  families they describe (decision 11).
- **Explicit norm conversion inside a derivation.** The architecture asks a
  module whose assumption bounds an entrywise defect and whose conclusion is an
  operator inequality to carry the dimension factor through its own proof.
  That is an obligation on a proof, which the review of that proof enforces,
  and not on the engine; `req:norm-conversion` binds only a declared number
  derived from a bound in another norm.

## Where the code is

The module's code is the package `src/certiqs_key/foundations`. Every other
package may import it, and it imports nothing else of the repository. The
pinching and trace-power functions stay in `meat-core`'s objective package:
they read that module's declared thresholds and its declaration type, so
moving them would make this package import a module. A claim's `implements`
field names the symbol it binds where one does; paths below are under
`src/certiqs_key/`:

| Claims | Code |
| --- | --- |
| `def:pinching`, `def:renyi` | `meat_core/objective/linalg.py` (`pinch`, `psd_trace_power`) |
| `def:kl`, `lem:kernel` | `foundations/kernel.py` (`divergence_kernel`) |
| `lem:pinchmono` | `meat_core/objective/branch.py` (`trace_power_pinched`) |
| `def:binary64`, `lem:binary64-lattice` | `foundations/exact.py` (`scalar_is_binary64`, `is_binary64` and the lattice helpers) |
| `def:declared-order`, `lem:exact-accumulation` | `foundations/exact.py` (`sum_in_declared_order`, `trace_in_row_order`, `sum_rounds_nowhere`) and `foundations/exact_admission.py` (its own `sum_rounds_nowhere`) |
| `def:exact-admissibility`, `req:boundary-admission` | `foundations/exact_admission.py` (the admission decisions) |
| `def:sector-map` | `foundations/blocks.py` (`SectorStructure`) |
| `def:tolerance`, `lem:floor-stricter` | `foundations/numeric.py` (the measurements) |
| `def:snap`, `req:snap-reference`, `req:who-snaps`, `req:support-safe-snap` | `foundations/snap.py` (`snap_measurement_family`, `MeasurementSnapRecord`, `support_safe_snap_block`) |
| `def:exact-reference`, `lem:enclosure-psd` | `foundations/reference.py` (`Reference`, `enclosure_psd`) |
| `lem:recentred-enclosure` | `foundations/recentring.py` (`recentred_enclosure`) |
| `def:factor-enclosure`, `cor:rank-over-factor-enclosure` | `foundations/reference.py` (`FactorEnclosure`, `gram_radius`, `fixes_rank`), carried beside a block's entrywise enclosure by `foundations/recentring.py` (`EntrywiseEnclosure.factor`) |
| the groups of `req:snap-reference` (iii) | `foundations/resting.py` |
| `def:evaluated-off-snap` | `runs/direct_route.py` (`direct_route`) |
| `req:declared-lattice` | `foundations/snap.py` (`is_on_lattice`) |
| `req:declared-tolerance` | `runs/config.py` |
| `def:tiers`, `req:tiers` | `foundations/assurance.py` |
| `lem:least-eigenvalue-bound` | `foundations/dyadic.py` (`least_eigenvalue_bound`, the exact dyadic matrices it runs on) |
| `cor:least-eigenvalue-over-enclosure` | `foundations/dyadic.py` (`enclosure_eigenvalue_bounds`) and `foundations/balls.py` (`least_eigenvalue`) |
| `lem:matrix-function-perturbation` | `foundations/balls.py` (`spectral`, `power`, `trace_power`, `deriv_power`; the only module that imports the ball-arithmetic library) |
