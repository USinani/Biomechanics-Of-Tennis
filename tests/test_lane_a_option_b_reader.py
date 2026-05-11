"""Tests for Lane A Option B derived contract report HTML (read/display only)."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FIXTURE_SRC = REPO_ROOT / "tests/fixtures/lane_a_contract_report_min.json"
EXPECTED_D_WARNING = (
    "Full-horizon XML-limited contract D is diagnostic-only and must not be "
    "interpreted as contract-C smooth-dynamics parity."
)
GUARDRAIL = (
    "This Lane A contract-C section is not the same contract as the legacy "
    "parity_strict full-horizon row."
)

CANONICAL_KPI_REL = [
    Path("systematic_studies/outputs/compare_signals_matlab_vs_mujoco_metrics.json"),
    Path("systematic_studies/outputs/compare_signals_bridge_relaxed_metrics.json"),
    Path("systematic_studies/outputs/swing_benchmark_summary.json"),
    Path("systematic_studies/outputs/racket_trajectory_summary.json"),
    Path("example_two_link/metrics/eval_sac_two_link_arm.json"),
]


class LaneAOptionBReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        from systematic_studies import lane_a_contract_report_html as mod

        self.mod = mod

    def test_fixture_renders_contract_labels_and_c_fields(self) -> None:
        root = Path(self.id()).resolve()
        dst = root / "runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURE_SRC, dst)
        html = self.mod.render_lane_a_contract_report_section(root)
        self.assertIn("contract-badge", html)
        self.assertIn('class="contract-badge">C</span>', html)
        self.assertIn('class="contract-badge">D</span>', html)
        self.assertIn("PRIMARY fixture rule A", html)
        self.assertIn("PRIMARY fixture rule B", html)
        self.assertIn("mujoco", html)
        self.assertIn("480", html)
        self.assertIn("477", html)

    def test_d_diagnostic_warning_verbatim(self) -> None:
        root = Path(self.id()).resolve()
        dst = root / "runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURE_SRC, dst)
        html = self.mod.render_lane_a_contract_report_section(root)
        import html as html_mod

        self.assertIn(html_mod.escape(EXPECTED_D_WARNING), html)

    def test_derived_banner_created_at_created_by(self) -> None:
        root = Path(self.id()).resolve()
        dst = root / "runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURE_SRC, dst)
        html = self.mod.render_lane_a_contract_report_section(root)
        self.assertIn("derived_or_canonical", html)
        self.assertIn(">derived<", html)
        self.assertIn("implementation_option", html)
        self.assertIn(">B<", html)
        self.assertIn("2099-01-01T00:00:00Z", html)
        self.assertIn("tests/fixtures/lane_a_contract_report_min.json", html)

    def test_guardrail_line_present(self) -> None:
        root = Path(self.id()).resolve()
        dst = root / "runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURE_SRC, dst)
        html = self.mod.render_lane_a_contract_report_section(root)
        import html as html_mod

        self.assertIn(html_mod.escape(GUARDRAIL), html)

    def test_missing_json_degrades_gracefully(self) -> None:
        root = Path(self.id()).resolve()
        html = self.mod.render_lane_a_contract_report_section(root)
        self.assertIn("lane-a-contract-report", html)
        self.assertIn("not found", html.lower())

    def test_no_canonical_kpi_json_write_on_render(self) -> None:
        root = Path(self.id()).resolve()
        dst = root / "runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURE_SRC, dst)
        markers: dict[Path, str] = {}
        for rel in CANONICAL_KPI_REL:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps({"marker": rel.as_posix(), "x": 1})
            p.write_text(text, encoding="utf-8")
            markers[p] = text
        self.mod.render_lane_a_contract_report_section(root)
        for p, before in markers.items():
            self.assertEqual(p.read_text(encoding="utf-8"), before, msg=str(p))

    def test_helper_does_not_reference_json_specs_flatten(self) -> None:
        src = (REPO_ROOT / "systematic_studies/lane_a_contract_report_html.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("_flatten_json", src)
        self.assertNotIn("render_json_table", src)
        self.assertNotIn("OUTPUTS_DIR", src)

    def test_weekly_dashboard_wires_lane_a_without_json_specs(self) -> None:
        wd = (REPO_ROOT / "systematic_studies/weekly_dashboard.py").read_text(encoding="utf-8")
        self.assertIn("render_lane_a_contract_report_section", wd)
        self.assertIn("lane_a_contract_report_html", wd)
        self.assertIn("lane_a_html = render_lane_a_contract_report_section", wd)
        self.assertIn("{lane_a_html}", wd)
        idx_weekly = wd.find("{weekly_html}")
        idx_lane = wd.find("{lane_a_html}")
        idx_fig = wd.find("<h2>Figures</h2>")
        self.assertNotEqual(idx_weekly, -1)
        self.assertNotEqual(idx_lane, -1)
        self.assertNotEqual(idx_fig, -1)
        self.assertLess(idx_weekly, idx_lane)
        self.assertLess(idx_lane, idx_fig)


if __name__ == "__main__":
    unittest.main()
