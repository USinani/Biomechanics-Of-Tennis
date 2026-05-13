# AI co-development operating system (blueprint)

Portable **markdown-only** blueprint for research and engineering projects where agents must not confuse fluency with correctness.

## What this is

- **Doctrine + templates + Cursor command stubs** — not automation, not orchestration scripts.
- Copy `.ai-cowork/` into a repo (or symlink) and adapt names/paths.
- Pair with your project’s permission rules (canonical outputs, thresholds, lanes).

## Core doctrine (summary)

1. **One mission state** — single current objective; everything else is backlog.
2. **One active hypothesis** — falsifiable; superseded hypotheses stay on the Decision Board, not in active work.
3. **One executor** — one agent/run owns mutations and experiments; many **read-only** reviewers allowed.
4. **Moves are scored** — information gain, cost, risk, reversibility, decision impact (see `move-scorecard-template.md`).
5. **Evidence packets preserve learning** — every non-trivial conclusion has a dated packet with inputs, method, outputs, limits.
6. **Decision Board preserves judgment** — branches parked/superseded; next action is explicit.
7. **Canonical outputs protected** — derived artifacts preferred; no experiment unless it can **change a decision**.

## Transferable lesson (Lane A)

> **Trajectory disagreement is downstream. Find the smallest local invariant first.**

Examples:

| Domain | Local invariant before full trajectory / curve |
|--------|-----------------------------------------------|
| Robotics | One-step `qacc` at a reference state before trajectory parity |
| ML | One-batch loss / gradient sanity before full training curve |
| Data pipelines | One-row transform before full report |
| Backend | One request lifecycle before load test |
| Trading | One signal slice before long backtest |

## Files

| File | Role |
|------|------|
| `mission-control.md` | How to hold one mission and rotate state |
| `move-generator.md` | How to propose candidate moves |
| `red-team-critic.md` | Adversarial review checklist |
| `evidence-auditor.md` | Evidence discipline |
| `experiment-engineer.md` | When an experiment is allowed |
| `agent-roles.md` | Executor vs read-only thinkers |
| `*-template.md` | Blank structures to copy per cycle |
| `cursor/commands/*.md` | Short prompts for Cursor |
| `codex/AGENTS.template.md` | Seed for Codex `AGENTS.md` |
| `claude/CLAUDE.template.md` | Seed for Claude project memory |

## Non-goals

- No shell runners, schedulers, or CI wiring in this folder.
- No replacement for human sign-off on publication, safety, or irreversible actions.
