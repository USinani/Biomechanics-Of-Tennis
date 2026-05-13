# Mission control

## Invariant

At any moment there is exactly:

- **One mission** — one sentence outcome the team is trying to decide or prove.
- **One active hypothesis** — the leading falsifiable claim under test.
- **One executor** — one agent/session that may edit files, run commands, or schedule work (per project permissions).

Many **read-only** thinkers (review, red-team, audit) may run in parallel; they do not branch the mission without a handoff.

## Mission state block (copy into chat or doc)

```text
Mission:
Active hypothesis:
Executor:
Lane / scope:
Last evidence packet:
Stop rules in effect:
Next action (single):
Permission: Allowed | Allowed with conditions | Needs review
```

## Rotation rules

1. **Close or park** the previous hypothesis on the Decision Board before promoting a new one.
2. **Never** merge “diagnostic contract” numbers with “publication contract” claims without labeling both.
3. If new data **invalidates** the mission, **stop** and rewrite the mission before more experiments.

## Lane A lesson

**Trajectory disagreement is downstream.** Stabilize **local invariants** (one-step dynamics, sign conventions, contract boundaries) before interpreting long-horizon RMSE or spikes.
