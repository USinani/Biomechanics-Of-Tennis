#!/usr/bin/env python3
"""Derived pre-limit metrics from stored swing benchmark CSVs (read-only inputs)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

# Relaxed compare_signals thresholds (scripts/parity_smoke.sh, parity_full.sh).
RELAX_MAX_Q_DEV_RAD = 5.0
RELAX_MAX_QDOT_DEV_RAD_S = 25.0
SPIKE_TH = 500.0
JERK_TH = 5.0e4
PRELIMIT_TIME_S = 0.480


def count_spikes(vel: list[float], dt: float, threshold: float) -> int:
    if len(vel) < 2:
        return 0
    acc = [abs(vel[i] - vel[i - 1]) / dt for i in range(1, len(vel))]
    return sum(1 for a in acc if a > threshold)


def count_jerk_outliers(vel: list[float], dt: float, threshold: float) -> int:
    if len(vel) < 3:
        return 0
    acc = [(vel[i] - vel[i - 1]) / dt for i in range(1, len(vel))]
    jerk = [(acc[j] - acc[j - 1]) / dt for j in range(1, len(acc))]
    return sum(1 for j in jerk if abs(j) > threshold)


def max_qdot2_jump(vel: list[float], dt: float) -> float:
    if len(vel) < 2:
        return 0.0
    return max(abs(vel[i] - vel[i - 1]) / dt for i in range(1, len(vel)))


def analyze_rows(rows: list[dict], label: str) -> dict:
    dt = float(rows[1]["dt_s"]) if len(rows) > 1 else 0.001
    mj1 = [float(r["mujoco_q1_rad"]) for r in rows]
    mj2 = [float(r["mujoco_q2_rad"]) for r in rows]
    b1 = [float(r["bridge_q1_rad"]) for r in rows]
    b2 = [float(r["bridge_q2_rad"]) for r in rows]
    mjd1 = [float(r["mujoco_qdot1_rad_s"]) for r in rows]
    mjd2 = [float(r["mujoco_qdot2_rad_s"]) for r in rows]
    bd1 = [float(r["bridge_qdot1_rad_s"]) for r in rows]
    bd2 = [float(r["bridge_qdot2_rad_s"]) for r in rows]
    t0 = float(rows[0]["time_s"])
    t1 = float(rows[-1]["time_s"])

    err_q = [((mj1[i] - b1[i]) ** 2 + (mj2[i] - b2[i]) ** 2) ** 0.5 for i in range(len(rows))]
    err_qd = [((mjd1[i] - bd1[i]) ** 2 + (mjd2[i] - bd2[i]) ** 2) ** 0.5 for i in range(len(rows))]

    rmse_q = (sum(e**2 for e in err_q) / len(err_q)) ** 0.5 if err_q else 0.0
    rmse_qd = (sum(e**2 for e in err_qd) / len(err_qd)) ** 0.5 if err_qd else 0.0

    max_d1 = max(abs(mj1[i] - b1[i]) for i in range(len(rows)))
    max_d2 = max(abs(mj2[i] - b2[i]) for i in range(len(rows)))
    max_dd1 = max(abs(mjd1[i] - bd1[i]) for i in range(len(rows)))
    max_dd2 = max(abs(mjd2[i] - bd2[i]) for i in range(len(rows)))

    sp_mj = count_spikes(mjd1, dt, SPIKE_TH) + count_spikes(mjd2, dt, SPIKE_TH)
    sp_br = count_spikes(bd1, dt, SPIKE_TH) + count_spikes(bd2, dt, SPIKE_TH)
    jk_mj = count_jerk_outliers(mjd1, dt, JERK_TH) + count_jerk_outliers(mjd2, dt, JERK_TH)
    jk_br = count_jerk_outliers(bd1, dt, JERK_TH) + count_jerk_outliers(bd2, dt, JERK_TH)

    max_jump_qdot2 = max_qdot2_jump(mjd2, dt)

    relaxed_pass = (
        max(max_d1, max_d2) <= RELAX_MAX_Q_DEV_RAD
        and max(max_dd1, max_dd2) <= RELAX_MAX_QDOT_DEV_RAD_S
        and sp_mj == 0
        and sp_br == 0
        and jk_mj == 0
        and jk_br == 0
    )

    # PHD narrative RMSE bounds (documentation only; not compare_signals).
    phd_rmse_ok = rmse_q <= 2.5 and rmse_qd <= 13.76

    return {
        "label": label,
        "sample_count": len(rows),
        "time_s_min": t0,
        "time_s_max": t1,
        "rmse_q_rad": rmse_q,
        "rmse_qd": rmse_qd,
        "max_abs_dev_q1_rad": max_d1,
        "max_abs_dev_q2_rad": max_d2,
        "max_abs_dev_qdot1_rad_s": max_dd1,
        "max_abs_dev_qdot2_rad_s": max_dd2,
        "velocity_spike_count_mujoco": sp_mj,
        "velocity_spike_count_bridge": sp_br,
        "velocity_jerk_outlier_count_mujoco": jk_mj,
        "velocity_jerk_outlier_count_bridge": jk_br,
        "max_abs_delta_qdot2_rad_s2": max_jump_qdot2,
        "relaxed_compare_signals_parity_ready_on_window": relaxed_pass,
        "relaxed_thresholds_note": (
            f"compare_signals relaxed (parity_smoke/parity_full): max_q_dev<={RELAX_MAX_Q_DEV_RAD}, "
            f"max_qdot_dev<={RELAX_MAX_QDOT_DEV_RAD_S}, spikes==0, jerk_outliers==0; "
            "evaluated on window rows only."
        ),
        "phd_narrative_rmse_under_2p5_and_13p76": phd_rmse_ok,
    }


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    base_csv = root / "runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv"
    nolim_csv = root / "runs/diagnostics/parity_joint_limit_ablation/swing_benchmark_timeseries_500_nolimits.csv"
    base_summary = root / "runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json"

    all_base = load_csv(base_csv)
    all_nolim = load_csv(nolim_csv)
    pre_b = [r for r in all_base if float(r["time_s"]) < PRELIMIT_TIME_S]
    pre_n = [r for r in all_nolim if float(r["time_s"]) < PRELIMIT_TIME_S]

    full_base_metrics = analyze_rows(all_base, "full_baseline_xml_limits")
    pre_base = analyze_rows(pre_b, "prelimit_baseline_xml_limits")
    pre_nolim = analyze_rows(pre_n, "prelimit_nolimit_mujoco")

    with (root / base_summary).open() as f:
        summary_500 = json.load(f)

    out = {
        "cutoff_time_s_strict_lt": PRELIMIT_TIME_S,
        "inputs": {
            "baseline_csv": str(base_csv.relative_to(root)),
            "nolimit_csv": str(nolim_csv.relative_to(root)),
            "baseline_summary_json": str(base_summary.relative_to(root)),
        },
        "summary_500_full_baseline": {
            "rmse_q_rad": summary_500.get("rmse_q_rad"),
            "rmse_qd": summary_500.get("rmse_qd"),
            "velocity_spike_count": summary_500.get("velocity_spike_count"),
            "velocity_jerk_outlier_count": summary_500.get("velocity_jerk_outlier_count"),
            "parity_ready_bridge_gate": summary_500.get("parity_ready_bridge_gate"),
        },
        "computed_full_baseline_from_csv": full_base_metrics,
        "prelimit_baseline": pre_base,
        "prelimit_nolimit": pre_nolim,
    }

    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "prelimit_metrics.json"
    out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
