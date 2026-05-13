# Agent roles

## Executor (one)

- May edit allowed files, run approved commands, create derived artifacts.
- Owns the **handoff packet**: commands, outputs, failures, assumptions.
- Must not expand scope without mission update.

## Read-only thinkers (many)

- Red-team, evidence audit, literature cross-check, alternative explanations.
- May **not** change repo state unless promoted to executor for a scoped task.

## Promotions

Temporary executor role requires:

- explicit scope (files, dirs, commands),
- permission line from project policy,
- time box or stop condition.

## Anti-patterns

- Multiple executors writing the same canonical paths.
- “Everyone implements a fix” without a scored move.
