# Experiment engineer

## Gate

**No experiment unless it can change a decision** on the Decision Board or falsify the active hypothesis.

## Pre-flight

1. Decision or hypothesis ID this run targets.
2. **Contract** — which physics / data contract applies?
3. **Outputs** — derived vs canonical path list (canonical needs explicit approval).
4. **Stop** if the run only produces “more plots” without a decision branch.

## Post-flight

1. Evidence packet path.
2. Update Decision Board: claim rows, branch status, next action.
3. If result is null or confounded, **park** the branch with reason — do not retry blindly.

## Lane A lesson

Prefer **read-only recomputation** on stored artifacts when it answers the same question as a re-simulation.
