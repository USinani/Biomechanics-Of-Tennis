#!/usr/bin/env python3
"""
Artifact contract checker (read-only by default).

Checks presence/readability/type of canonical dashboard/KPI artifacts defined in docs/REPO_LAYOUT.md.

Default: emit a Markdown report to stdout.
Optional: write a derived report under runs/diagnostics/ with --write (guarded; refuses overwrite).

Terminology: Missing artifacts indicate an *artifact contract failure*, not scientific invalidity.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal


Status = Literal["present", "missing", "unreadable", "wrong_type"]


EXPECTED_ARTIFACTS: tuple[str, ...] = (
    "systematic_studies/outputs/compare_signals_matlab_vs_mujoco_metrics.json",
    "systematic_studies/outputs/compare_signals_bridge_relaxed_metrics.json",
    "systematic_studies/outputs/swing_benchmark_summary.json",
    "systematic_studies/outputs/racket_trajectory_summary.json",
    "example_two_link/metrics/eval_sac_two_link_arm.json",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_run_log_inventory_module(repo_root: Path):
    """
    Load tools/diagnostics/run_log_inventory.py as a module so we can reuse the exact write-guard.
    """
    path = repo_root / "tools/diagnostics/run_log_inventory.py"
    spec = importlib.util.spec_from_file_location("run_log_inventory", path)
    if not spec or not spec.loader:
        raise RuntimeError("could not load run_log_inventory.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@dataclass(frozen=True)
class ArtifactResult:
    status: Status
    path: str
    evidence: str


def check_artifact(repo_root: Path, rel_path: str) -> ArtifactResult:
    p = repo_root / rel_path
    try:
        if not p.exists():
            return ArtifactResult(status="missing", path=rel_path, evidence="path does not exist")
        if p.is_dir():
            return ArtifactResult(status="wrong_type", path=rel_path, evidence="expected file, found directory")
        if not p.is_file():
            return ArtifactResult(status="wrong_type", path=rel_path, evidence="expected file, found non-file")

        # Readability probe: open a small amount.
        try:
            with p.open("rb") as f:
                f.read(1)
        except OSError as e:
            return ArtifactResult(status="unreadable", path=rel_path, evidence=f"open failed: {e}")

        return ArtifactResult(status="present", path=rel_path, evidence="exists and is readable file")
    except OSError as e:
        # Covers race or permissions on exists/is_file.
        return ArtifactResult(status="unreadable", path=rel_path, evidence=f"os error during stat: {e}")


def render_report(results: list[ArtifactResult]) -> str:
    total = len(results)
    counts = {s: 0 for s in ("present", "missing", "unreadable", "wrong_type")}
    for r in results:
        counts[r.status] += 1

    lines: list[str] = [
        "# Artifact Contract Check",
        "",
        "## Scope",
        "Dashboard / KPI contract artifacts",
        "",
        "## Summary",
        f"- total expected: {total}",
        f"- present: {counts['present']}",
        f"- missing: {counts['missing']}",
        f"- unreadable: {counts['unreadable']}",
        f"- wrong_type: {counts['wrong_type']}",
        "",
        "## Artifact results",
        "",
        "| Status | Path | Evidence |",
        "|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r.status} | `{r.path}` | {r.evidence} |")

    lines.extend(["", "## Conservative diagnosis"])
    if counts["missing"] == 0 and counts["unreadable"] == 0 and counts["wrong_type"] == 0:
        lines.append("- No artifact contract failure detected (all expected artifacts present).")
    else:
        lines.append(
            "- Artifact contract failure detected (missing/unreadable/wrong_type artifacts). Root cause: **UNKNOWN** without run/log evidence."
        )
        lines.append(
            "- Do not infer scientific invalidity from missing artifacts alone; treat this as an observability / pipeline contract issue."
        )

    lines.extend(
        [
            "",
            "## Permission boundary",
            "Read-only check. No canonical outputs modified.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--write",
        type=str,
        default=None,
        help="Optional report output path under runs/diagnostics/ (repo-relative). Default: stdout only.",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = _repo_root()

    results = [check_artifact(repo_root, rp) for rp in EXPECTED_ARTIFACTS]
    report = render_report(results)

    if args.write:
        rli = _load_run_log_inventory_module(repo_root)
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

