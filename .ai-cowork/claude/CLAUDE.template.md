# Claude project instructions (template)

Paste into Claude project memory or repo `CLAUDE.md` after customization.

## Mission control
- Single **mission** and **active hypothesis** at a time (`.ai-cowork/mission-control.md`).
- **Trajectory disagreement is downstream** — establish smallest local invariants before long-horizon conclusions.

## Evidence
- Every quantitative claim: artifact path + command + contract label (strict/relaxed/diagnostic).
- Do not conflate incompatible comparisons (e.g. constrained sim vs unconstrained model) without naming the contract.

## Permissions
- **Allowed without extra approval:** {{read, small docs, derived diagnostics}}
- **Requires approval:** {{canonical writes, thresholds, destructive ops}}

## Decision Board
- Link: {{path to decision board markdown}}
- Update branches when parking or closing work.

## Red team
Before publication-facing claims, run mental checklist from `.ai-cowork/red-team-critic.md`.
