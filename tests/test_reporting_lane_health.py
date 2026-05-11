"""Stdlib unittests for tools/diagnostics/reporting_lane_health.py (no pytest required)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_reporting_lane_health():
    path = REPO_ROOT / "tools/diagnostics/reporting_lane_health.py"
    spec = importlib.util.spec_from_file_location("reporting_lane_health", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_artifact_contract_check(repo_root: Path):
    path = repo_root / "tools/diagnostics/artifact_contract_check.py"
    spec = importlib.util.spec_from_file_location("artifact_contract_check", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_output_inventory(repo_root: Path):
    path = repo_root / "tools/diagnostics/output_inventory.py"
    spec = importlib.util.spec_from_file_location("output_inventory", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_rlh = _load_reporting_lane_health()


class TestReportingLaneHealth(unittest.TestCase):
    def test_overall_status_rules(self) -> None:
        # dashboard smoke skipped must not downgrade status.
        artifact_ok = _rlh.ArtifactContractSummary(
            status="ok",
            total_expected=5,
            present=5,
            missing=0,
            unreadable=0,
            wrong_type=0,
            missing_like_paths=[],
        )
        out_ok = _rlh.OutputInventorySummary(status="ok", note="ok", markdown="x")
        overall = _rlh.compute_overall(artifact_ok, out_ok, dashboard_smoke=None, wrapper_error=False)
        self.assertEqual(overall, "ok")

        artifact_warn = _rlh.ArtifactContractSummary(
            status="warning",
            total_expected=5,
            present=4,
            missing=1,
            unreadable=0,
            wrong_type=0,
            missing_like_paths=["a"],
        )
        overall2 = _rlh.compute_overall(artifact_warn, out_ok, dashboard_smoke=None, wrapper_error=False)
        self.assertEqual(overall2, "warning")

        out_failed = _rlh.OutputInventorySummary(status="failed", note="fail", markdown=None)
        overall3 = _rlh.compute_overall(artifact_ok, out_failed, dashboard_smoke=None, wrapper_error=False)
        self.assertEqual(overall3, "failed")

    def test_artifact_contract_against_fixture_root(self) -> None:
        # Avoid depending on real repo outputs: run artifact check directly on a fixture tree.
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/reporting_lane_health/root_ok"
        acc = _load_artifact_contract_check(REPO_ROOT)
        results = [acc.check_artifact(fixture_root, rp) for rp in acc.EXPECTED_ARTIFACTS]
        self.assertTrue(all(r.status == "present" for r in results))

    def test_output_inventory_builds_on_fixture_root(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/reporting_lane_health/root_ok"
        oi = _load_output_inventory(REPO_ROOT)
        md = oi.build_markdown(fixture_root)
        self.assertIn("Experiment output inventory", md)

    def test_write_guard_rejects_unsafe_paths(self) -> None:
        rli = _rlh._load_write_guard(REPO_ROOT)
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "/tmp/x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/diagnostics/../x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/not_diagnostics/x.md")


if __name__ == "__main__":
    unittest.main()

