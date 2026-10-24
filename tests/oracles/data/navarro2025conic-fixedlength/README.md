# The published-curve reference: Navarro et al., Fig. 1, regenerated

FROZEN COMPARISON DATA, never regenerated from this repository's code. Twenty
fixed-length qubit BB84 key rates computed by the public code of
`navarro2025conic` (arXiv:2511.10584) at the paper's own Fig. 1 parameters.
`PROVENANCE.md` says how the numbers
were produced, with which toolchain, and that only numeric outputs of that
GPL-3.0 code crossed over.

What it is for: `tests/integration/test_navarro_head_to_head.py` runs the
qubit instance at the one point the two formulations share (n = 1e5,
Q = 0.015, p_K = 0.589 on both sides, the paper's security parameters) and
checks that this engine's rate lies above theirs and below the diluted
ceiling. It is a LOOSE reference and the test says why: their acceptance set
is a uniform ball and their accumulation carries no marginal constraint, so
the two numbers are different mathematical objects and equality is not
expected.
