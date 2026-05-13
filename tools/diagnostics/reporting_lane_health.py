#!/usr/bin/env python3
"""
Reporting lane health wrapper (stdlib only; read-only by default).

Orchestrates existing safe diagnostics to provide a concise Lane C (Reporting) health signal:
- Artifact contract check (dashboard/KPI contract)
- Output inventory snapshot

Default: print Markdown to stdout.
Optional: write report under runs/diagnostics/ with --write (guarded; refuses overwrite).

Optional (explicit): --include-dashboard-smoke runs:
  ./run.sh systematic_studies/weekly_dashboard.py --no-open --skip-refresh-racket --skip-regenerate-figures
and records exit code plus a bounded excerpt of stdout+stderr.

Safety:
- No canonical outputs are modified by default.
- --write is guarded using tools/diagnostics/run_log_inventory.py::_safe_write_target
  (rejects absolute paths, traversal, symlink escape, and refuses overwrite).
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal


OverallStatus = Literal["ok", "warning", "failed", "unknown"]
SubStatus = Literal["ok", "warning", "failed", "skipped"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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


@dataclass(frozen=True)
class ArtifactContractSummary:
    status: SubStatus
    total_expected: int
    present: int
    missing: int
    unreadable: int
    wrong_type: int
    missing_like_paths: list[str]


def run_artifact_contract(repo_root: Path) -> ArtifactContractSummary:
    acc = _load_module(repo_root, "tools/diagnostics/artifact_contract_check.py", "artifact_contract_check")
    results = [acc.check_artifact(repo_root, rp) for rp in acc.EXPECTED_ARTIFACTS]

    counts = {"present": 0, "missing": 0, "unreadable": 0, "wrong_type": 0}
    missing_like: list[str] = []
    for r in results:
        counts[r.status] += 1
        if r.status != "present":
            missing_like.append(r.path)

    status: SubStatus = "ok" if (counts["missing"] + counts["unreadable"] + counts["wrong_type"]) == 0 else "warning"
    return ArtifactContractSummary(
        status=status,
        total_expected=len(results),
        present=counts["present"],
        missing=counts["missing"],
        unreadable=counts["unreadable"],
        wrong_type=counts["wrong_type"],
        missing_like_paths=missing_like,
    )


@dataclass(frozen=True)
class OutputInventorySummary:
    status: SubStatus
    note: str
    markdown: str | None


def run_output_inventory(repo_root: Path) -> OutputInventorySummary:
    oi = _load_module(repo_root, "tools/diagnostics/output_inventory.py", "output_inventory")
    try:
        md = oi.build_markdown(repo_root)
    except Exception as e:  # noqa: BLE001
        return OutputInventorySummary(status="failed", note=f"exception: {e}", markdown=None)
    return OutputInventorySummary(status="ok", note="generated inventory markdown", markdown=md)


@dataclass(frozen=True)
class DashboardSmokeResult:
    status: SubStatus
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


def run_dashboard_smoke(repo_root: Path) -> DashboardSmokeResult:
    cmd = [
        "./run.sh",
        "systematic_studies/weekly_dashboard.py",
        "--no-open",
        "--skip-refresh-racket",
        "--skip-regenerate-figures",
    ]
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
    status: SubStatus = "ok" if proc.returncode == 0 else "failed"
    return DashboardSmokeResult(
        status=status,
        command=" ".join(cmd),
        exit_code=proc.returncode,
        excerpt=excerpt,
    )


def compute_overall(
    artifact_contract: ArtifactContractSummary,
    output_inventory: OutputInventorySummary,
    dashboard_smoke: DashboardSmokeResult | None,
    wrapper_error: bool,
) -> OverallStatus:
    # User-specified rules:
    # - overall = failed if wrapper errors, output inventory fails, or dashboard smoke was enabled and failed
    # - overall = warning if artifact contract has missing/unreadable/wrong_type artifacts
    # - overall = ok if artifact contract ok, output inventory ok, and dashboard smoke skipped or passed
    if wrapper_error:
        return "failed"
    if output_inventory.status == "failed":
        return "failed"
    if dashboard_smoke is not None and dashboard_smoke.status == "failed":
        return "failed"
    if artifact_contract.status == "warning":
        return "warning"
    return "ok"


def render_report(
    artifact_contract: ArtifactContractSummary,
    output_inventory: OutputInventorySummary,
    dashboard_smoke: DashboardSmokeResult | None,
    overall: OverallStatus,
) -> str:
    dash_status: SubStatus = "skipped" if dashboard_smoke is None else dashboard_smoke.status

    lines: list[str] = [
        "# Reporting Lane Health",
        "",
        "## Summary",
        f"- status: {overall}",
        f"- artifact contract: {artifact_contract.status}",
        f"- output inventory: {output_inventory.status}",
        f"- dashboard smoke: {dash_status}",
        "",
        "## Artifact contract",
        f"- expected: {artifact_contract.total_expected}",
        f"- present: {artifact_contract.present}",
        f"- missing: {artifact_contract.missing}",
        f"- unreadable: {artifact_contract.unreadable}",
        f"- wrong_type: {artifact_contract.wrong_type}",
        "",
    ]

    if artifact_contract.missing_like_paths:
        lines.append("Missing/unreadable/wrong_type artifacts (evidence):")
        for p in artifact_contract.missing_like_paths:
            lines.append(f"- `{p}`")
        lines.append("")

    lines.extend(
        [
            "## Output inventory",
            f"- status: {output_inventory.status}",
            f"- note: {output_inventory.note}",
            "",
        ]
    )

    if dashboard_smoke is None:
        lines.extend(["## Dashboard smoke", "skipped (enable with --include-dashboard-smoke)", ""])
    else:
        lines.extend(
            [
                "## Dashboard smoke",
                f"- command: `{dashboard_smoke.command}`",
                f"- exit_code: {dashboard_smoke.exit_code}",
                "",
                "Excerpt (bounded):",
                "",
                "```",
                dashboard_smoke.excerpt or "",
                "```",
                "",
            ]
        )

    lines.extend(["## Evidence"])
    # Evidence is intentionally minimal and path/command anchored.
    for p in artifact_contract.missing_like_paths:
        lines.append(f"- artifact_missing_like: `{p}`")
    lines.append("- artifact_contract_source: `docs/REPO_LAYOUT.md` (Dashboard JSON contract section)")
    lines.append("- tools_used: `tools/diagnostics/artifact_contract_check.py`, `tools/diagnostics/output_inventory.py`")
    if dashboard_smoke is not None:
        lines.append(f"- dashboard_smoke_command: `{dashboard_smoke.command}` (exit {dashboard_smoke.exit_code})")
    lines.append("")

    lines.extend(
        [
            "## Permission boundary",
            "Read-only health check. No canonical outputs modified.",
            "",
            "## Recommended next safe action",
        ]
    )

    if overall == "ok":
        lines.append("- No action needed for reporting lane health; proceed with next PhD lane task.")
    elif overall == "warning":
        lines.append("- Investigate the missing/unreadable artifacts (read-only). If needed, regenerate via the documented pipeline (human-approved).")
    else:
        lines.append("- Inspect wrapper output/errors and rerun the smallest safe check to isolate the failure (read-only).")

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
        "--include-dashboard-smoke",
        action="store_true",
        help="If set, run weekly_dashboard smoke (no-open, no racket refresh, no figure regen). Skipped by default.",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = _repo_root()

    wrapper_error = False
    dashboard_smoke: DashboardSmokeResult | None = None
    try:
        artifact_contract = run_artifact_contract(repo_root)
        output_inventory = run_output_inventory(repo_root)
        if args.include_dashboard_smoke:
            dashboard_smoke = run_dashboard_smoke(repo_root)
    except Exception as e:  # noqa: BLE001
        wrapper_error = True
        # Keep output bounded and evidence-led.
        artifact_contract = ArtifactContractSummary(
            status="failed",
            total_expected=0,
            present=0,
            missing=0,
            unreadable=0,
            wrong_type=0,
            missing_like_paths=[],
        )
        output_inventory = OutputInventorySummary(status="failed", note=f"wrapper exception: {e}", markdown=None)

    overall = compute_overall(artifact_contract, output_inventory, dashboard_smoke, wrapper_error)
    report = render_report(artifact_contract, output_inventory, dashboard_smoke, overall)

    if args.write:
        rli = _load_write_guard(repo_root)
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

