# `reports/`

In the public tree this folder holds one design brief,
[`2026-10-06-snap-certification/direct-route-in-brief.md`](2026-10-06-snap-certification/direct-route-in-brief.md):
how the key rate stays sound when the engine rounds a measurement model. A
report is never authority: it is read as of its date, and nothing under
`spec/` cites one.

## How the claims are reviewed

Every claim, and the code that implements its mathematics, is checked by an
independent verifier that sees only the artefacts, never the drafter's
reasoning. A change that only rephrases or restructures the mathematics
gets an equivalence review instead, which certifies that no mathematics
changed. Only a maintainer accepts a claim, on the verifier's report; an
accepted claim is not one a human has checked line by line. The principles
are [PRINCIPLES.md](../PRINCIPLES.md) (sections 2 and 6) and the reviewers'
roles are in [harness/roles/](../harness/roles/).

The full review trail (the round-by-round review reports and the audits
behind each accepted claim) and the history before the release are kept in
the internal repository and are not published.
