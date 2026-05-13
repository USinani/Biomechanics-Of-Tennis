# Cursor command: Theory inspector

Use when symptoms look like "physics bugs" but may be contract or measurement issues.

## Prompt body

```text
Theory inspection:

Symptom: {{DESCRIPTION}}
1. List competing explanations (≥3), including "contract mismatch" and "wrong local invariant".
2. What is the smallest experiment or static check that discriminates top two?
3. Map symptom to downstream vs upstream cause using:
   "Trajectory disagreement is downstream — smallest local invariant first."
4. Recommend one move ID for the scorecard.
```
