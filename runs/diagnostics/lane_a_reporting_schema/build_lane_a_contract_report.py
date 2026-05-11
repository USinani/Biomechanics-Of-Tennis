#!/usr/bin/env python3
"""Build lane_a_contract_report.json from existing derived JSON only (Option B).

Reads:
  runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json
  runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_summary_500_gravsign.json
  runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json
  runs/diagnostics/phase2_contract_c_replication/ic_2/gravsign_mujoco/swing_benchmark_summary_500.json

Writes:
  runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json

Does not read or write systematic_studies/outputs/ or weekly_dashboard.py.

C rows include t_cut_source, t_cut_rule_source, t_cut_provenance_note (Record 1 explains
baseline-window t_cut vs missing t_cut_s in gravsign_prelimit). D row includes
diagnostic_warning for Option C display.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    repo = here.parents[2]
    out_path = here / "lane_a_contract_report.json"

    prelimit_orig = repo / "runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json"
    summary_orig_d = repo / "runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_summary_500_gravsign.json"
    prelimit_ic2 = repo / "runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json"
    summary_ic2_d = (
        repo / "runs/diagnostics/phase2_contract_c_replication/ic_2/gravsign_mujoco/swing_benchmark_summary_500.json"
    )

    with open(prelimit_orig, encoding="utf-8") as f:
        po = json.load(f)
    with open(summary_orig_d, encoding="utf-8") as f:
        so_d = json.load(f)
    with open(prelimit_ic2, encoding="utf-8") as f:
        p2 = json.load(f)
    with open(summary_ic2_d, encoding="utf-8") as f:
        s2_d = json.load(f)

    gp_o = po["gravsign_prelimit"]
    gp2 = p2["gravsign_prelimit"]
    ic = p2["ic"]

    t_cut_rule = (
        "PRIMARY: first row (min time_s) where mj_q1_deg >= 120.0 on baseline_default "
        "MuJoCo CSV; window time_s < t_cut"
    )

    diagnostic_warning_d = (
        "Full-horizon XML-limited contract D is diagnostic-only and must not be "
        "interpreted as contract-C smooth-dynamics parity."
    )

    t_cut_provenance_note_orig = (
        "t_cut=0.480 aligns with the established Lane A contract-C baseline window / "
        "evidence chain (480 pre-limit samples; window ends at time_s_max from "
        "gravsign_prelimit in prelimit_compare.json). It is not copied from a t_cut_s "
        "key inside the gravsign_prelimit object of that file; that object only "
        "carries window aggregates."
    )
    t_cut_provenance_note_ic2 = (
        "t_cut and t_cut_rule are read from runs/diagnostics/phase2_contract_c_replication/"
        "ic_2/prelimit_compare.json (parent-level t_cut_s / t_cut_rule, consistent with "
        "gravsign_prelimit window metadata in the same file)."
    )

    report = {
        "schema_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "created_by": "runs/diagnostics/lane_a_reporting_schema/build_lane_a_contract_report.py",
        "derived_or_canonical": "derived",
        "implementation_option": "B",
        "governance": {
            "contract_C_primary": True,
            "contract_C_primary_status": "provisional",
            "contract_D_diagnostic_only": True,
            "contract_B_deferred": True,
            "bridge_gravity_sign_policy": "opt_in",
        },
        "records": [
            {
                "contract_label": "C",
                "metric_scope": "window",
                "horizon_type": "pre_limit",
                "ic_label": "original_passive",
                "run_id": "parity_prelimit_gravity_sign_m1_gravsign_prelimit",
                "source_artifacts": {
                    "source_summary_json": "runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json",
                    "source_csv": "runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_timeseries_500_gravsign.csv",
                },
                "evidence_packet": "runs/diagnostics/evidence_packets/lane_a_prelimit_gravity_sign_trajectory_probe.md",
                "t_cut": 0.48,
                "t_cut_rule": t_cut_rule,
                "t_cut_source": (
                    "lane_a_original_passive_contract_c_baseline_window_evidence_chain"
                ),
                "t_cut_rule_source": (
                    "shared_primary_rule_text_matches_ic_2_prelimit_compare.json_t_cut_rule"
                ),
                "t_cut_provenance_note": t_cut_provenance_note_orig,
                "sample_count": gp_o["sample_count"],
                "time_start_s": gp_o["time_s_min"],
                "time_end_s": gp_o["time_s_max"],
                "q1_deg": 5.002088059159929,
                "q2_deg": 54.997385535776786,
                "qd1_rad_s": 0.03644350731719041,
                "qd2_rad_s": -0.045631008870626884,
                "tau_amp": 0.0,
                "bridge_gravity_sign": "mujoco",
                "mujoco_joint_limits": "xml",
                "limit_contact_present": False,
                "strict_swing_window_gate": gp_o["strict_swing_style_gate_on_window"],
                "relaxed_compare_signals_window_gate": gp_o["relaxed_compare_signals_parity_ready_on_window"],
                "parity_ready_bridge_gate_full_horizon": None,
                "rmse_q_rad": gp_o["rmse_q_rad"],
                "rmse_qd": gp_o["rmse_qd"],
                "velocity_spike_count_mujoco": gp_o["velocity_spike_count_mujoco"],
                "velocity_jerk_outlier_count_mujoco": gp_o["velocity_jerk_outlier_count_mujoco"],
                "interpretation_label": "c_smooth_strict_pass",
                "not_claimed": [
                    "Not full-horizon contract D closure",
                    "Not native MATLAB strict parity",
                    "Not contract B constrained parity",
                    "Not all ICs / tasks / torques — original passive IC only for this row",
                    "Default bridge_gravity_sign remains opt-in for harness defaults",
                ],
            },
            {
                "contract_label": "C",
                "metric_scope": "window",
                "horizon_type": "pre_limit",
                "ic_label": "IC-2",
                "run_id": "P2-M1_ic2_gravsign_prelimit",
                "source_artifacts": {
                    "source_summary_json": "runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json",
                    "source_csv": "runs/diagnostics/phase2_contract_c_replication/ic_2/gravsign_mujoco/swing_benchmark_timeseries_500.csv",
                },
                "evidence_packet": "runs/diagnostics/evidence_packets/lane_a_phase2_p2m1_ic2_contract_c_replication.md",
                "t_cut": p2["t_cut_s"],
                "t_cut_rule": p2["t_cut_rule"],
                "t_cut_source": (
                    "runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json"
                    "#t_cut_s"
                ),
                "t_cut_rule_source": (
                    "runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json"
                    "#t_cut_rule"
                ),
                "t_cut_provenance_note": t_cut_provenance_note_ic2,
                "sample_count": gp2["sample_count"],
                "time_start_s": gp2["time_s_min"],
                "time_end_s": gp2["time_s_max"],
                "q1_deg": ic["q1_deg"],
                "q2_deg": ic["q2_deg"],
                "qd1_rad_s": ic["qd1"],
                "qd2_rad_s": ic["qd2"],
                "tau_amp": float(ic["tau_amp"]),
                "bridge_gravity_sign": "mujoco",
                "mujoco_joint_limits": gp2.get("mujoco_joint_limits", "xml"),
                "limit_contact_present": False,
                "strict_swing_window_gate": gp2["strict_swing_style_gate_on_window"],
                "relaxed_compare_signals_window_gate": gp2["relaxed_compare_signals_parity_ready_on_window"],
                "parity_ready_bridge_gate_full_horizon": None,
                "rmse_q_rad": gp2["rmse_q_rad"],
                "rmse_qd": gp2["rmse_qd"],
                "velocity_spike_count_mujoco": gp2["velocity_spike_count_mujoco"],
                "velocity_jerk_outlier_count_mujoco": gp2["velocity_jerk_outlier_count_mujoco"],
                "interpretation_label": "c_smooth_strict_pass",
                "not_claimed": [
                    "Not full-horizon contract D closure",
                    "Not native MATLAB strict parity",
                    "Not contract B constrained parity",
                    "Not proof beyond two passive ICs with IC-specific t_cut",
                    "Default bridge_gravity_sign remains opt-in for harness defaults",
                ],
            },
            {
                "contract_label": "D",
                "metric_scope": "full_horizon",
                "horizon_type": "xml_limited_mixed",
                "ic_label": "IC-2",
                "run_id": "P2-M1_ic2_full_horizon_gravsign_summary",
                "source_artifacts": {
                    "source_summary_json": "runs/diagnostics/phase2_contract_c_replication/ic_2/gravsign_mujoco/swing_benchmark_summary_500.json",
                    "source_csv": "runs/diagnostics/phase2_contract_c_replication/ic_2/gravsign_mujoco/swing_benchmark_timeseries_500.csv",
                },
                "evidence_packet": "runs/diagnostics/evidence_packets/lane_a_joint_limit_ablation.md",
                "t_cut": None,
                "t_cut_rule": "N/A — full-horizon mixed contract D (XML-limited MuJoCo vs unconstrained bridge)",
                "sample_count": int(s2_d["steps"]),
                "time_start_s": 0.0,
                "time_end_s": float(s2_d["duration_s"]),
                "q1_deg": ic["q1_deg"],
                "q2_deg": ic["q2_deg"],
                "qd1_rad_s": ic["qd1"],
                "qd2_rad_s": ic["qd2"],
                "tau_amp": float(ic["tau_amp"]),
                "bridge_gravity_sign": s2_d.get("bridge_gravity_sign", "mujoco"),
                "mujoco_joint_limits": s2_d.get("mujoco_joint_limits", "xml"),
                "limit_contact_present": True,
                "strict_swing_window_gate": None,
                "relaxed_compare_signals_window_gate": None,
                "parity_ready_bridge_gate_full_horizon": s2_d["parity_ready_bridge_gate"],
                "rmse_q_rad": s2_d["rmse_q_rad"],
                "rmse_qd": s2_d["rmse_qd"],
                "velocity_spike_count_mujoco": s2_d["velocity_spike_count"],
                "velocity_jerk_outlier_count_mujoco": s2_d["velocity_jerk_outlier_count"],
                "interpretation_label": "d_diagnostic_gate_fail",
                "diagnostic_warning": diagnostic_warning_d,
                "not_claimed": [
                    "Not contract C smooth unconstrained strict closure",
                    "Not contract A no-limit ODE companion",
                    "Not contract B matched analytical limits",
                    "baseline_default full-horizon summary for same IC exists separately under ic_2/baseline_default/",
                    "Original passive full-horizon D exemplar: runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_summary_500_gravsign.json",
                ],
            },
        ],
        "notes": (
            "Record 3 uses IC-2 gravsign_mujoco full-horizon summary JSON. "
            "Original passive full-horizon D: see swing_benchmark_summary_500_gravsign.json in parity_prelimit_gravity_sign/."
        ),
    }

    out_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path.relative_to(repo)}")


if __name__ == "__main__":
    main()
