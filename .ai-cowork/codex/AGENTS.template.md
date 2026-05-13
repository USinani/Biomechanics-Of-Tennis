# Codex agent instructions (template)

Copy to repo root as `AGENTS.md` and customize.

## Scope
{{One paragraph: codebase, safety, research domain}}

## Prime directive
Start from the **research decision**, not the immediate edit.

## Operating rules
- One **mission** and one **active hypothesis** visible in each handoff (see `.ai-cowork/mission-control.md`).
- One **executor** per write scope; others read-only unless promoted.
- **Evidence packets** for non-trivial claims; cite paths and commands.
- **Canonical outputs** {{list}} — write only with approval.
- **Thresholds** — do not change without explicit sign-off.

## Handoff packet (required for cross-agent work)
```text
Agent:
Mission:
Hypothesis:
Files changed:
Commands run:
Artifacts:
Evidence:
Failures:
Assumptions:
Unknowns:
Next validation:
Permission:
```

## Stop rules
{{Bullets — link `.ai-cowork/stop-rules-template.md` when filled}}

## Non-goals
{{What agents must not do}}
