#!/usr/bin/env python3
"""
Lane A parity health snapshot (stdlib only; read-only by default).

This is a *health snapshot*, not a fixer. It summarizes:
- strict vs relaxed parity artifact presence/readability/type
- parsed metrics only when keys exist (otherwise UNKNOWN)
- conservative interpretation of whether artifacts constitute relaxed/strict parity evidence

Default: print Markdown to stdout.
Optional: write under runs/diagnostics/ with --write (guarded; refuses overwrite).

Optional (explicit): --include-parity-smoke runs ./scripts/parity_smoke.sh
and records exit code plus a bounded excerpt of stdout+stderr.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal


OverallStatus = Literal["ok", "warning", "failed", "unknown"]
ArtifactStatus = Literal["present", "missing", "unreadable", "wrong_type"]
EvidenceFlag = Literal["yes", "no", "unknown"]
SmokeStatus = Literal["skipped", "ok", "failed"]


STRICT_PATH = "systematic_studies/outputs/compare_signals_matlab_vs_mujoco_metrics.json"
RELAXED_PATH = "systematic_studies/outputs/compare_signals_bridge_relaxed_metrics.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

CODE_ROOT = _repo_root()


def _load_module(repo_root: Path, rel_path: str, module_name: str):
    path = repo_root / rel_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"could not load module {module_name} from {rel_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_write_guard(repo_root: Path):
    return _load_module(repo_root, "tools/diagnostics/run_log_inventory.py", "run_log_inventory")


def _load_artifact_checker(repo_root: Path):
    return _load_module(repo_root, "tools/diagnostics/artifact_contract_check.py", "artifact_contract_check")


@dataclass(frozen=True)
class ArtifactEvidence:
    name: str
    path: str
    status: ArtifactStatus
    evidence: str
    parsed_fields: dict[str, Any]
    parity_evidence: EvidenceFlag
    parity_evidence_basis: str


def _safe_read_json(repo_root: Path, rel_path: str) -> dict[str, Any] | None:
    p = repo_root / rel_path
    try:
        txt = p.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(txt)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return data
    return None


def _extract_fields(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k in keys:
        if k in data:
            out[k] = data[k]
    return out


def _evidence_from_keys(data: dict[str, Any], evidence_keys: list[str]) -> tuple[EvidenceFlag, str]:
    """
    Return yes/no only if an explicit boolean-like key exists. Otherwise unknown.
    """
    for k in evidence_keys:
        if k in data:
            v = data[k]
            if isinstance(v, bool):
                return ("yes" if v else "no"), f"explicit key `{k}` = {v}"
    return "unknown", "no explicit parity-ready boolean key found"


def check_parity_artifact(repo_root: Path, name: str, rel_path: str, evidence_keys: list[str]) -> ArtifactEvidence:
    """
    repo_root: where the artifacts live (may be a fixture root in tests).
    Code modules are always loaded from CODE_ROOT (the actual repo checkout).
    """
    acc = _load_artifact_checker(CODE_ROOT)
    r = acc.check_artifact(repo_root, rel_path)
    parsed_fields: dict[str, Any] = {}
    parity_flag: EvidenceFlag = "unknown"
    parity_basis = "UNKNOWN"

    if r.status == "present":
        data = _safe_read_json(repo_root, rel_path)
        if data is None:
            parsed_fields = {"schema": "UNKNOWN (not a JSON object or parse failed)"}
            parity_flag, parity_basis = ("unknown", "could not parse JSON object")
        else:
            # Only include fields that actually exist.
            parsed_fields = _extract_fields(
                data,
                [
                    "rmse_q",
                    "rmse_qdot",
                    "parity_ready",
                    "parity_ready_strict",
                    "parity_ready_bridge_gate",
                    "gate",
                    "strict_gate",
                    "relaxed_gate",
                ],
            )
            parity_flag, parity_basis = _evidence_from_keys(data, evidence_keys)
            if not parsed_fields:
                parsed_fields = {"schema": "UNKNOWN (no known keys found)"}

    return ArtifactEvidence(
        name=name,
        path=rel_path,
        status=r.status,
        evidence=r.evidence,
        parsed_fields=parsed_fields,
        parity_evidence=parity_flag,
        parity_evidence_basis=parity_basis,
    )


@dataclass(frozen=True)
class SmokeResult:
    status: SmokeStatus
    command: str
    exit_code: int | None
    excerpt: str


def _bounded_excerpt(text: str, max_chars: int = 4000, last_lines: int = 40) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    tail = "\n".join(lines[-last_lines:])
    if len(tail) > max_chars:
        return tail[-max_chars:]
    return tail


def run_parity_smoke(repo_root: Path) -> SmokeResult:
    cmd = ["./scripts/parity_smoke.sh"]
    proc = subprocess.run(  # noqa: S603,S607
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    combined = ""
    if proc.stdout:
        combined += proc.stdout
    if proc.stderr:
        if combined and not combined.endswith("\n"):
            combined += "\n"
        combined += proc.stderr
    excerpt = _bounded_excerpt(combined)
    status: SmokeStatus = "ok" if proc.returncode == 0 else "failed"
    return SmokeResult(status=status, command=" ".join(cmd), exit_code=proc.returncode, excerpt=excerpt)


def compute_overall(strict: ArtifactEvidence, relaxed: ArtifactEvidence, smoke: SmokeResult | None, wrapper_error: bool) -> OverallStatus:
    # Status logic (user-specified):
    # - failed if wrapper errors or parity smoke was enabled and failed
    # - warning if strict or relaxed artifacts are missing/unreadable/wrong_type
    # - unknown if artifacts exist but schema cannot be interpreted
    # - ok only if expected artifacts are present/readable and no enabled smoke failed
    # - skipped smoke is neutral
    if wrapper_error:
        return "failed"
    if smoke is not None and smoke.status == "failed":
        return "failed"
    if strict.status != "present" or relaxed.status != "present":
        return "warning"

    strict_schema_unknown = "schema" in strict.parsed_fields and isinstance(strict.parsed_fields.get("schema"), str) and "UNKNOWN" in str(strict.parsed_fields.get("schema"))
    relaxed_schema_unknown = "schema" in relaxed.parsed_fields and isinstance(relaxed.parsed_fields.get("schema"), str) and "UNKNOWN" in str(relaxed.parsed_fields.get("schema"))
    if strict_schema_unknown or relaxed_schema_unknown:
        return "unknown"
    return "ok"


def render_report(overall: OverallStatus, strict: ArtifactEvidence, relaxed: ArtifactEvidence, smoke: SmokeResult | None) -> str:
    smoke_status: SmokeStatus = "skipped" if smoke is None else smoke.status

    lines: list[str] = [
        "# Lane A Parity Health Snapshot",
        "",
        "## Summary",
        f"- status: {overall}",
        f"- strict artifact: {strict.status}",
        f"- relaxed artifact: {relaxed.status}",
        f"- strict parity evidence: {strict.parity_evidence}",
        f"- relaxed parity evidence: {relaxed.parity_evidence}",
        f"- parity smoke: {smoke_status}",
        "",
        "## Artifact evidence",
        "| Artifact | Status | Path | Evidence |",
        "|---|---|---|---|",
        f"| strict | {strict.status} | `{strict.path}` | {strict.evidence} |",
        f"| relaxed | {relaxed.status} | `{relaxed.path}` | {relaxed.evidence} |",
        "",
        "## Parsed metrics, if available",
        "",
        "Strict artifact fields:",
    ]
    for k, v in strict.parsed_fields.items():
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("Relaxed artifact fields:")
    for k, v in relaxed.parsed_fields.items():
        lines.append(f"- `{k}`: {v}")
    lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "- Artifact present does not prove scientific validity.",
            "- Missing artifact is a parity lane health warning.",
            "- Strict parity closure must not be claimed unless explicitly supported by the metrics.",
            f"- Strict evidence basis: {strict.parity_evidence_basis}",
            f"- Relaxed evidence basis: {relaxed.parity_evidence_basis}",
            "",
            "## Parity smoke",
        ]
    )

    if smoke is None:
        lines.append("Skipped by default (enable with --include-parity-smoke).")
        lines.append("")
    else:
        lines.extend(
            [
                f"- command: `{smoke.command}`",
                f"- exit_code: {smoke.exit_code}",
                "",
                "Excerpt (bounded):",
                "",
                "```",
                smoke.excerpt or "",
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Permission boundary",
            "Read-only health snapshot. No parity thresholds, scripts, outputs, or experiment logic modified.",
            "",
            "## Recommended next safe action",
        ]
    )

    if overall == "ok":
        lines.append("- Proceed with the next parity lane task (e.g. sysID/RK4 work) under explicit approval for code edits.")
    elif overall == "warning":
        lines.append("- Investigate missing/unreadable artifacts (read-only). Regenerate via documented pipelines only with human approval.")
    elif overall == "unknown":
        lines.append("- Inspect the JSON schema (read-only) to determine which explicit parity-ready fields (if any) the metrics expose.")
    else:
        lines.append("- Inspect wrapper errors; re-run without smoke first to isolate read-only issues.")

    lines.append("")
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--write",
        type=str,
        default=None,
        help="Optional output path under runs/diagnostics/ (repo-relative). Default: stdout only.",
    )
    p.add_argument(
        "--include-parity-smoke",
        action="store_true",
        help="If set, run ./scripts/parity_smoke.sh and record bounded output. Skipped by default.",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = CODE_ROOT
    smoke: SmokeResult | None = None
    wrapper_error = False

    try:
        strict = check_parity_artifact(repo_root, "strict", STRICT_PATH, evidence_keys=["parity_ready", "parity_ready_strict"])
        relaxed = check_parity_artifact(repo_root, "relaxed", RELAXED_PATH, evidence_keys=["parity_ready"])
        if args.include_parity_smoke:
            smoke = run_parity_smoke(repo_root)
    except Exception as e:  # noqa: BLE001
        wrapper_error = True
        strict = ArtifactEvidence(
            name="strict",
            path=STRICT_PATH,
            status="unreadable",
            evidence=f"wrapper exception: {e}",
            parsed_fields={"schema": "UNKNOWN"},
            parity_evidence="unknown",
            parity_evidence_basis="UNKNOWN",
        )
        relaxed = ArtifactEvidence(
            name="relaxed",
            path=RELAXED_PATH,
            status="unreadable",
            evidence=f"wrapper exception: {e}",
            parsed_fields={"schema": "UNKNOWN"},
            parity_evidence="unknown",
            parity_evidence_basis="UNKNOWN",
        )

    overall = compute_overall(strict, relaxed, smoke, wrapper_error)
    report = render_report(overall, strict, relaxed, smoke)

    if args.write:
        rli = _load_write_guard(CODE_ROOT)
        try:
            target = rli._safe_write_target(repo_root, args.write)
        except (ValueError, FileExistsError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        target.write_text(report, encoding="utf-8")
        print(f"Wrote {target}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

