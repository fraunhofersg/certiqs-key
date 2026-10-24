# The parity target: fig 1, N = 1..5, first-order tier

FROZEN ORACLE DATA, never regenerated from code. `results.csv` is the capture
described in `PROVENANCE.md`. The per-point records and bundles it was produced with are not part of this
repository.

What it is: 105 rows, `fig1` only, 5 photon cutoffs x 3 routes (encoded,
licensed, licensed+eq27) x 7 QBERs, every row `status ok`, `reported_tier
first-order`, 2000 Frank-Wolfe iterations. `key_length` is the number the
pipeline must reproduce; the four compiler-visible columns
(`target_dimension`, `constraint_entries`, `constraint_floor_a`,
`constraint_floor_b`) and `p_mc` are what can be checked on the compiler
side alone.
