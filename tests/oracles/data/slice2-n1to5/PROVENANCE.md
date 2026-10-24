# Provenance: the fig 1 capture at five photon cutoffs

**FROZEN ORACLE DATA, never regenerated from code.** `results.csv` was produced
by the project's earlier research code, which is not published. It carries
`fig1` rows and nothing else.

## The grid

105 points: 5 photon cutoffs (`N = 1..5`, exact window `N + 1`) x 3 routes
(`encoded`, `licensed`, `licensed+eq27`) x 7 QBERs (`1/128, 1/64, 1/32, 3/64,
1/16, 5/64, 3/32`). Every point: transmittance 1 (`loss_db` 0), dark count 0,
basis split 1/2, `rounds` 10000, `alpha_declared` 1.05, 2000 Frank-Wolfe
iterations, declared tolerance `1e-12`, `p_mc` per `def:pmcex`.

**All 105 completed.** No refusals, no errors, no `first_order_clamped`,
`reported_tier` `first-order` throughout, solver status `iteration-limit`
throughout at the declared 2000 iterations.

## The columns

Each row gives the point's parameters (`figure`, `index`, `route`,
`photon_cutoff`, `exact_window`, `qber`, `transmittance`, `loss_db`,
`dark_count`, `basis_split`, `rounds`, `alpha_declared`), its outcome
(`status`, `stage`, `reason`), what the compiler declared (`p_gen`, `p_mc`,
`p_mc_definition`, `assumption_eig_invoked`, `target_dimension`,
`constraint_entries`, `constraint_floor_a`, `constraint_floor_b`), the bound
(`h_low`, `h_lb`, `first_order_minus_estimate`, `first_order_clamped`,
`reported_tier`, `snap_max_defect`, `snap_max_displacement`), the key length
(`key_length`, `key_length_reason`, `assurance`, `alpha_used`), and the
solver's report (`solver_status`, `iterations`, `frank_wolfe_gap`,
`declared_tolerance`, `wall_time_s`). `record` names the per-point record,
which is not part of this repository.

## Measured over the 105 points

| | |
| --- | --- |
| bracket `h_low - h_lb` | median `8.66e-4`, min `3.93e-4`, max `1.73e-3` |
| Frank-Wolfe gap | median `1.53e-3`, max `1.11e-2` |
| max snap displacement | `4.52e-13` |
| refusals | 0 |

Median wall per point: 111.5 s, 191.9 s, 243.4 s, 275.0 s, 545.2 s at
`N = 1..5`; the slowest `N = 5` completer took 983 s.

### ONE `wall_time_s` IS NOT A COST MEASUREMENT

`fig1#92` (`licensed`, `N = 5`, `Q = 1/32`) records **33947.7 s**, 37x the
`N = 5` median, while the two points after it took 239.8 s and 275.5 s; the
wall clock ran while the process did not. The RESULT is unaffected and is
corroborated by its own twin: it returns `l = 628`, exactly what
`licensed+eq27` returns at the same point, as `a = 0` requires. Exclude that
row from any timing statistic.

## What the five cutoffs say

*The encoded route is flat from `N = 2`.* At `Q = 1/64`, `h_lb` reads
`0.1688726, 0.1740701, 0.1740812, 0.1740787, 0.1740875`: the `N = 1 -> 2` step
is `5.2e-3`, six times the bracket, and the whole `N = 2..5` spread is
`1.75e-5`, **fifty times smaller than it**.

*The licensed route's penalty peaks at `N = 2` and decays, above zero.* The
deficit against the encoded arm at the same point:

| Q | N=1 | N=2 | N=3 | N=4 | N=5 |
| --- | --- | --- | --- | --- | --- |
| 1/128 | `9.3e-6` | `2.02e-2` | `1.71e-2` | `1.59e-2` | `1.53e-2` |
| 1/64 | `1.2e-5` | `1.96e-2` | `1.66e-2` | `1.54e-2` | `1.49e-2` |
| 1/16 | `-9.8e-7` | `1.67e-2` | `1.42e-2` | `1.32e-2` | `1.27e-2` |
| 3/32 | `1.8e-6` | `1.50e-2` | `1.28e-2` | `1.19e-2` | `1.15e-2` |

**The shape is the same on all seven QBERs**: `N = 1` at or inside the
bracket, a jump at `N = 2`, then a monotone decay whose increments shrink
faster than they close. It does not reach zero, and it does not return to
`N = 1`'s value anywhere on this grid: at `Q = 1/64` the licensed arm yields
958 bits at `N = 1` and 861 at `N = 5`.

*Why*, measured from the returned points' `sector_weight_report`: at `N = 1`
the preserved blocks are vacuum and one photon and `M[mc]` on them is
**exactly zero**, so the only multi-clicks that can pay the licence
`p(mc) >= b W` are flag weight burnt in the `mc` sector, which is exactly the
price the encoded route charges pointwise through its flag pass-through
`1 - p_mc`, and the two routes agree. From `N = 2` the preserved `nb_2` block
multi-clicks (`lambda_min(M[mc]) = 0.5`), the licence accepts those as
payment, and the adversary buys clean flag weight with them: at `N = 2` the
returned point holds `W = 0.0900` of flag weight against the `W <= 0.00015`
that burnt flag weight alone would license, **604x**. Rising `b` then claws it
back as `N` grows.

*The two licensed arms are bit-identical.* `max |h_lb(licensed) -
h_lb(licensed+eq27)| = 0.0` over all 35 pairs, `a = 0` at `p_dc = 0`.
