# Two singleton-overshoot points: evidence, not oracles

**Evidence, not an oracle** (PRINCIPLES.md §2.3 is not engaged). These are the
two bound-contributing points of the singleton-overshoot diagnosis, at
which the printed first-order bracket lay ABOVE the proved finite-alpha
ceiling `U` because the oracle's return did not attain the feasible-side
minimum (A-LMO failing visibly). They are copied here, cut to what a test
reads, so that the test reads no run output.

## What each file holds

- `a7.npz`, `a8.npz`: per block `i`, in the order of `points.json`'s
  `pairs`, the gradient `gradient_i` and the consumed point `point_i`, as
  binary64 complex arrays (copied unchanged from the diagnosis' saved point,
  which also held the vertex, the witness and the repair arrays).
- `points.json`: per point the stored `alpha` (and its hex), the joint
  sectors `pairs` (one trusted Alice sector `A`, input dimension 2, no rows),
  the gate's `objective` and its printed bracket `printed_bracket` (from
  `capture.json`'s `gate`), and `ceiling`, the proved upper bound
  `U = 3809807790243/8796093022208` of the reviewed honest-witness
  calculation.

The acceptance side is the exact honest singleton, so a bracket at these
points is `objective - sum_i Re tr(G_i J_i) + b^F` with `b^F` the feasible
side. `tests/integration/test_singleton_overshoot_verified.py` forms `b^F`
from the dual of a fresh QICS solve of the saved cost, as
`meat-core/frank-wolfe/req:verified-feasible-side` does, and asserts the
verified bracket lies below `U` in exact rationals (P0 measured `U - 3.1e-5`
at a7 and `U - 3.8e-3` at a8).
