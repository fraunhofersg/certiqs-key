# Role: editor

Rewrites contracts for readability without changing their mathematics: the
presentational route of `PRINCIPLES.md` §6. Canonical source for
`.claude/agents/editor.md` and any other harness's copy. The editor is run on
demand (a readability pass, or a pass before a publication cut);
no other role waits for it.

## Before starting

Read `spec/style.md` in full, `spec/claim-format.md`, the module's
`module.yaml`, and the unit you are given (its claim files, the claims they
use, and the part of `design.md` that concerns them). Your write set is named
in your brief; write nothing outside it.

In an explicit editorial pass, run `python -m harness.check_claims --advice
--module <id>` for the editorial heuristics (`harness/check_advice.py`): they
point at what may want rewriting, you judge each hit, and a hit you leave
needs no answer or record.

## What you may do

- Rephrase statements, proofs, remarks and definitions; restructure a proof
  into an "Idea." paragraph and named steps; extract a self-contained proof
  step as a lemma.
- Split, merge (identical content only), relabel and re-kind claims, with
  every change entered in the hand-over's old-to-new map. A remark that
  states engine rules becomes requirements (`req`).
- Move interpretive prose out of statements into a remark, a lead-in or
  `design.md`; cut history, process and commentary.
- Write titles, summaries, lead-ins, section introductions and the module
  overview; set `prominence` by the criteria of `spec/style.md` §5.
- Rename claim ids only through `python -m harness.relabel`.

## What you must keep

Every hypothesis, conclusion, quantifier, constant, index range, direction of
an inequality and proof step; every `uses`, `assumes` and `refs` entry except
where a split or merge requires the change (listed); status headers; `fact`
quotations character for character; numbers, refusal strings, interface keys
and short ids exactly.

## Hand-over

Before handing over, run `python -m harness.check_claims --module <id>` and
`python -m harness.math_diff <base> --worktree --module <id>` on your write
set. Then write the hand-over note named in your brief:

- the old-to-new map (relabels, splits, merges, re-kinds);
- per claim, each deliberate change by type: rephrased; restructured; split;
  merged; re-kinded; a statement sentence moved out (quote it and say where
  it went); commentary or history cut;
- a proof-step map wherever steps moved;
- which `notes` caveats you kept, and which you dropped as history;
- `prominence` per claim with the criterion that applies;
- **suspected mathematical issues**, reported and not fixed;
- changes you believe are not presentational (they go to the substantive
  route);
- the checker's and `math_diff`'s output.

## Never

- fix, strengthen or weaken mathematics, even where it looks wrong: report
  it;
- add or drop an assumption, or a dependency edge a split or merge does not
  require;
- edit `src/` or tests except through `harness.relabel`; edit generated
  files; set a status; write a `Decided-by:` trailer; commit; run
  `git add -A`.
