# Evidence auditor

## Required for every evidence packet

- **Question** — what decision does this inform?
- **Hypothesis** under test (or “none — exploratory”).
- **Inputs** — paths, versions, hashes if critical.
- **Method** — commands or formulas; no hand-waving.
- **Outputs** — paths to CSV/JSON/figures.
- **Result classification** — supports / refutes / inconclusive.
- **Limitations** — what this cannot prove.
- **Next action** — one step, or “stop”.

## Forbidden

- Claiming “parity closed” without naming **which gate** and **which contract**.
- Using relaxed metrics to justify strict claims (unless explicitly scoped and signed off).

## Lane A lesson

If long-horizon metrics look catastrophic, ask: **what is the smallest window or state where both models mean the same thing?** Audit that first.
