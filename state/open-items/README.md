# Open items

The published tree carries no open items: the queue is the maintainers'
working state and is not published, so this folder holds only the
description of its format, and `state/DASHBOARD.md` is generated from an
empty queue.

One YAML file per item. This is the single queue: findings, tasks, decisions
waiting on a human, defects. `state/DASHBOARD.md` is generated from it by
`python -m harness.dashboard` (run it after every change here; its `--check`
is a harness test) and from the claim files.

The one question that sorts the queue: **can an agent close this without a
human choosing anything?** No: `needs_human: true`, and it appears on the
dashboard's first list. Yes: `needs_human: false`, and agents consume it.

## Schema

```yaml
id: <area>/<slug>              # area: principles, spec, harness, <module-id>, migration, refs, quality
title: one line
kind: decision | task | finding | defect
status: open | in-progress | closed
severity: blocking | major | minor | info     # for findings and defects; tasks use priority
priority: 1 | 2 | 3                            # 1 = next
needs_human: true | false
owner: <maintainer> | agent | <role>
module: <module-id> | null
claims: [<claim ids touched>]                  # may be empty
opened: YYYY-MM-DD
closes_when: one sentence stating the observable condition
decision: |                   # kind: decision only, set on closing: the answer, quoting the human
brief: |
  What, why, and (for a decision) the options with a recommended one.
links: [paths or ids]
history:
  - YYYY-MM-DD: what happened
```

Closing an item: set `status: closed`, add the closing history line, leave the
file in place. Closing a decision item also fills `decision:` with the human's
answer (verbatim where there is one), and the commit that closes it carries
the trailer `Decided-by: <maintainer's name>` (PRINCIPLES.md §2.4). No separate decision
log is kept by default. Files are never deleted; an item that was wrong says so in its
history.
