# Artifact policy — {{PROJECT}}

## Canonical outputs (protected)

| Path / pattern | Purpose | Write policy |
|----------------|---------|--------------|
| {{path}} | | executor + approval only |

## Derived outputs (preferred for probes)

| Path / pattern | Purpose |
|----------------|---------|
| {{path}} | |

## Evidence packets

- Location: {{e.g. runs/diagnostics/evidence_packets/}}
- Naming: {{convention}}

## Forbidden without approval

- Deleting or overwriting canonical rows
- Changing threshold defaults in code
- Mixing contracts in a single KPI without labels
