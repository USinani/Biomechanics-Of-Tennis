# Move generator

## Purpose

Produce **candidate moves** (actions) that might resolve the active hypothesis or unblock the mission. Do not execute until scored and approved.

## Move template

```text
Move ID:
One-line description:
Information gain (H/M/L):
Cost (H/M/L):
Risk (H/M/L):
Reversibility (easy | hard | irreversible):
Decision impact (H/M/L):
Touches canonical outputs? (Y/N)
Touches thresholds? (Y/N)
Executor-only? (Y/N)
```

## Rules

- Prefer **smallest** move that could **change a decision** (see `experiment-engineer.md`).
- If two moves have similar gain, choose **higher reversibility** and **lower canonical touch**.

## Scoring shortcut

Reject moves that:

- cannot change the Decision Board or hypothesis status, or
- violate active **stop rules**, or
- conflate incompatible contracts (e.g. mixed physics vs clean ODE lane) without labeling.
