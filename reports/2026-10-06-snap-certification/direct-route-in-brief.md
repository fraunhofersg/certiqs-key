# The direct route, in brief

*How the engine now keeps the key rate sound when it rounds your measurement
model, and why that is simpler than what came before. A working paper, not
authority (`reports/README.md`).*

## The problem

The engine's exact machinery (exact admission, the squashing reductions and
their certificates) needs the receiver's measurement written on an exact
dyadic number grid. A real device model is not on that grid: it has
efficiencies like 0.8, dark-count rates, and angles whose cosines are
irrational. So the engine **snaps** the model onto the grid before solving.

The snap moves the measurement by about 10⁻¹². The trouble is that the key
rate is not a continuous function of the measurement. A change too small to
see can move the rate by bits per round, for example when it makes an
outcome nearly impossible (meat-core `prop:optol-nobound`). So no direct
"error bar" on the rate follows from the size of the snap.

## What we tried first

1. **Disclose it.** Say plainly that the run assumes the device measures the
   snapped model (assumption A-SNAP). This is honest, but it is an assumption
   about every realistic device.
2. **Certify it.** Prove that the snapped model *dominates* the true one,
   G ⪰ (1−q)·F, and carry the weight q through the reductions as extra
   "flag" outcomes.
   - Mathematically this is sound.
   - In practice it needed a ladder of weights, a ceiling, a special absorbing
     outcome, noise floors, corrected constraint entries and per-route rules.
   - On the default route it sent the key to zero.
   - It failed outright for ideal devices off the π/8 grid.
   - It grew into a fragile policy matrix.

## The idea that replaced both

The number the engine reports is not the abstract optimum. It is the
**first-order lower bound** `h_lb`, a certificate built at one point the
solver found:

> the objective at that point, minus the largest decrease a linear step could
> still reach over the feasible set.

Convexity makes this a valid lower bound, and the theorem behind it
(`thm:firstorder`) holds at **any** admissible point, however that point was
found. That makes the following procedure sound:

1. **Search** on the snapped model, where everything is exact and fast.
2. **Evaluate the certificate on your actual model** at the best points the
   search found: one extra gradient and one oracle call per point.

The snap now only steers the search. It plays no part in the soundness
argument, because the bound is computed for your model itself.

**Why the discontinuity does not bite.** The discontinuity lives in the
*value*, the minimum over all adversary states, which can jump when supports
change. The certificate is evaluated at one fixed, strictly positive point.
There the dependence on the measurement is local and smooth, and the
measured difference is tiny.

## How it is built

- **The reference companion.** The receiver hands its reference model (exact
  where it can be, otherwise a tight enclosure) beside the snapped one. The
  same reduction chain runs on it, without rounding to the grid.
- **Constraint rows.** Rows that must be stored in floating point are relaxed
  outward by their rounding error. The feasible set can then only grow, and
  the bound can only stay valid.
- **Evaluation-only admission.** The companion is never solved, only
  evaluated. It is checked to have the same shape as the snapped declaration.
  That it is a genuine measurement is imported from the receiver's own exact
  or enclosure guarantees.
- **The fallback.** If no point gives a usable bound on the companion, the run
  falls back to the snapped bound and discloses A-SNAP, naming the reason. No
  measured configuration has needed it.

## What it bought

| | Before | Now |
|---|---|---|
| Realistic noisy device, default route | key 0, or disclosed A-SNAP | full key, no snap assumption |
| Ideal device off the π/8 grid | refused, or an overstated key | full key, no snap assumption |
| Licensed route | paid a corrected entry for the weight | pays nothing |
| Key lengths | — | unchanged on every measured configuration (difference ≤ 2·10⁻¹¹ per round) |
| Extra runtime | — | 0.1–2.5 s per run |
| Machinery | domination link, flags, ladder, ceiling, 8 causes | retired: 15 claims, one code package, about 4.4k lines |

A-SNAP now applies only where no reference exists, or in the fallback.

## What it does not change

- **You still vouch for the receiver model** (A-TRUST). The snap premise is
  gone; the model premise remains, as it always was.
- **Arithmetic.** The route's own evaluation runs in ordinary floating
  point; certifying its arithmetic is a separate step, the certified tier
  below.

## Where it led

The route has the classic shape of *a-posteriori verification*: solve
loosely, certify once at the end. The engine's `certified` tier does exactly
that: at the few points the reported number came from, it recomputes the
bound with every arithmetic step from the declaration's data exact or
rigorously enclosed, so no premise about floating-point accuracy remains
(`meat-core/frank-wolfe/cor:certified-keylength`). Where certification
fails, the run reports the first-order number and says why. The solver and
the reductions stayed as they were.

One lesson is also worth keeping: **certify the final certificate, not every
intermediate object.** Another is now a test tier of its own: realistic-device
key-rate canaries, after a regression hunt showed that every failure along the
way had passed tests that checked statuses but never a key.

## Where to read more

- Claims: `meat-core/frank-wolfe/cor:fo-reference`,
  `req:bracket-on-reference`, `reductions/cor:reference-companion`,
  `lem:row-relaxation` and `meat-core/req:companion-admission`; for the
  certified tier, `meat-core/frank-wolfe/req:certified-evaluation`,
  `cor:certified-keylength` and `rem:certified-scope`.
