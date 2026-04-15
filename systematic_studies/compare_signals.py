#!/usr/bin/env python3
"""Compare canonical MATLAB and MuJoCo signals with parity diagnostics."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class SignalSet:
    time_s: np.ndarray
    q1: np.ndarray
    q2: np.ndarray
    qdot1: np.ndarray
    qdot2: np.ndarray


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="") as f:
        return list(csv.DictReader(f))


def _require_fields(rows: list[dict[str, str]], fields: list[str], path: Path) -> None:
    if not rows:
        raise ValueError(f"No data rows in CSV: {path}")
    missing = [name for name in fields if name not in rows[0]]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")


def _load_parity_csv(path: Path) -> tuple[SignalSet, SignalSet]:
    rows = _read_rows(path)
    _require_fields(
        rows,
        [
            "time_s",
            "matlab_q1_rad",
            "matlab_q2_rad",
            "matlab_qdot1_rad_s",
            "matlab_qdot2_rad_s",
            "mujoco_q1_rad",
            "mujoco_q2_rad",
            "mujoco_qdot1_rad_s",
            "mujoco_qdot2_rad_s",
        ],
        path,
    )
    t = np.array([float(r["time_s"]) for r in rows], dtype=float)
    matlab = SignalSet(
        time_s=t,
        q1=np.array([float(r["matlab_q1_rad"]) for r in rows], dtype=float),
        q2=np.array([float(r["matlab_q2_rad"]) for r in rows], dtype=float),
        qdot1=np.array([float(r["matlab_qdot1_rad_s"]) for r in rows], dtype=float),
        qdot2=np.array([float(r["matlab_qdot2_rad_s"]) for r in rows], dtype=float),
    )
    mujoco = SignalSet(
        time_s=t,
        q1=np.array([float(r["mujoco_q1_rad"]) for r in rows], dtype=float),
        q2=np.array([float(r["mujoco_q2_rad"]) for r in rows], dtype=float),
        qdot1=np.array([float(r["mujoco_qdot1_rad_s"]) for r in rows], dtype=float),
        qdot2=np.array([float(r["mujoco_qdot2_rad_s"]) for r in rows], dtype=float),
    )
    return matlab, mujoco


def _load_canonical_csv(path: Path, prefix: str) -> SignalSet:
    rows = _read_rows(path)
    qdot1 = f"{prefix}_qdot1_rad_s"
    qdot2 = f"{prefix}_qdot2_rad_s"
    legacy_qd1 = f"{prefix}_qd1"
    legacy_qd2 = f"{prefix}_qd2"
    required = [
        "time_s",
        f"{prefix}_q1_rad",
        f"{prefix}_q2_rad",
    ]
    if qdot1 not in rows[0] and legacy_qd1 not in rows[0]:
        required.append(qdot1)
    if qdot2 not in rows[0] and legacy_qd2 not in rows[0]:
        required.append(qdot2)
    _require_fields(
        rows,
        required,
        path,
    )
    qdot1_key = qdot1 if qdot1 in rows[0] else legacy_qd1
    qdot2_key = qdot2 if qdot2 in rows[0] else legacy_qd2
    return SignalSet(
        time_s=np.array([float(r["time_s"]) for r in rows], dtype=float),
        q1=np.array([float(r[f"{prefix}_q1_rad"]) for r in rows], dtype=float),
        q2=np.array([float(r[f"{prefix}_q2_rad"]) for r in rows], dtype=float),
        qdot1=np.array([float(r[qdot1_key]) for r in rows], dtype=float),
        qdot2=np.array([float(r[qdot2_key]) for r in rows], dtype=float),
    )


def _resample_to_time(src: SignalSet, t_target: np.ndarray) -> SignalSet:
    if np.array_equal(src.time_s, t_target):
        return src
    if src.time_s.size < 2:
        raise ValueError("Need at least two samples for interpolation.")
    return SignalSet(
        time_s=t_target,
        q1=np.interp(t_target, src.time_s, src.q1),
        q2=np.interp(t_target, src.time_s, src.q2),
        qdot1=np.interp(t_target, src.time_s, src.qdot1),
        qdot2=np.interp(t_target, src.time_s, src.qdot2),
    )


def _count_spikes(vel: np.ndarray, dt: float, threshold: float) -> int:
    if vel.size < 2 or dt <= 0:
        return 0
    acc = np.diff(vel) / dt
    return int(np.count_nonzero(np.abs(acc) > threshold))


def _jerk_proxy(vel: np.ndarray, dt: float) -> np.ndarray:
    if vel.size < 3 or dt <= 0:
        return np.array([], dtype=float)
    acc = np.diff(vel) / dt
    return np.diff(acc) / dt


def _metrics(t: np.ndarray, matlab: SignalSet, mujoco: SignalSet, spike_threshold: float, jerk_threshold: float) -> dict:
    dt = float(np.median(np.diff(t))) if t.size > 2 else 0.0
    e_q1 = mujoco.q1 - matlab.q1
    e_q2 = mujoco.q2 - matlab.q2
    e_qd1 = mujoco.qdot1 - matlab.qdot1
    e_qd2 = mujoco.qdot2 - matlab.qdot2

    jerk_mj_1 = _jerk_proxy(mujoco.qdot1, dt)
    jerk_mj_2 = _jerk_proxy(mujoco.qdot2, dt)
    jerk_ml_1 = _jerk_proxy(matlab.qdot1, dt)
    jerk_ml_2 = _jerk_proxy(matlab.qdot2, dt)

    return {
        "dt_s": dt,
        "sample_count": int(t.size),
        "max_abs_dev_q1_rad": float(np.max(np.abs(e_q1))),
        "max_abs_dev_q2_rad": float(np.max(np.abs(e_q2))),
        "max_abs_dev_qdot1_rad_s": float(np.max(np.abs(e_qd1))),
        "max_abs_dev_qdot2_rad_s": float(np.max(np.abs(e_qd2))),
        "rmse_q_rad": float(np.sqrt(np.mean(e_q1**2 + e_q2**2))),
        "rmse_qdot_rad_s": float(np.sqrt(np.mean(e_qd1**2 + e_qd2**2))),
        "spike_count_mujoco": _count_spikes(mujoco.qdot1, dt, spike_threshold)
        + _count_spikes(mujoco.qdot2, dt, spike_threshold),
        "spike_count_matlab": _count_spikes(matlab.qdot1, dt, spike_threshold)
        + _count_spikes(matlab.qdot2, dt, spike_threshold),
        "jerk_outliers_mujoco": int(np.count_nonzero(np.abs(jerk_mj_1) > jerk_threshold))
        + int(np.count_nonzero(np.abs(jerk_mj_2) > jerk_threshold)),
        "jerk_outliers_matlab": int(np.count_nonzero(np.abs(jerk_ml_1) > jerk_threshold))
        + int(np.count_nonzero(np.abs(jerk_ml_2) > jerk_threshold)),
        "median_abs_jerk_mujoco": float(np.median(np.abs(np.concatenate([jerk_mj_1, jerk_mj_2]))))
        if jerk_mj_1.size + jerk_mj_2.size > 0
        else 0.0,
        "median_abs_jerk_matlab": float(np.median(np.abs(np.concatenate([jerk_ml_1, jerk_ml_2]))))
        if jerk_ml_1.size + jerk_ml_2.size > 0
        else 0.0,
    }


def _plot(t: np.ndarray, matlab: SignalSet, mujoco: SignalSet, out_png: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.5))
    axes = axes.ravel()

    axes[0].plot(t, matlab.q1, "--", label="MATLAB")
    axes[0].plot(t, mujoco.q1, "-", label="MuJoCo")
    axes[0].set_title("q1")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("rad")

    axes[1].plot(t, matlab.q2, "--", label="MATLAB")
    axes[1].plot(t, mujoco.q2, "-", label="MuJoCo")
    axes[1].set_title("q2")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("rad")

    axes[2].plot(t, matlab.qdot1, "--", label="MATLAB")
    axes[2].plot(t, mujoco.qdot1, "-", label="MuJoCo")
    axes[2].set_title("qdot1")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylabel("rad/s")

    axes[3].plot(t, matlab.qdot2, "--", label="MATLAB")
    axes[3].plot(t, mujoco.qdot2, "-", label="MuJoCo")
    axes[3].set_title("qdot2")
    axes[3].set_xlabel("Time (s)")
    axes[3].set_ylabel("rad/s")

    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")

    fig.suptitle("MATLAB vs MuJoCo Signal Comparison")
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare MATLAB and MuJoCo q/qdot signals.")
    parser.add_argument("--parity-csv", type=Path, default=None, help="Single CSV containing matlab_* and mujoco_* canonical fields.")
    parser.add_argument("--matlab-csv", type=Path, default=None, help="CSV with matlab_q* canonical fields.")
    parser.add_argument("--matlab-prefix", type=str, default="matlab", help="Prefix for reference signal columns (default: matlab).")
    parser.add_argument("--mujoco-csv", type=Path, default=None, help="CSV with mujoco_q* canonical fields.")
    parser.add_argument("--mujoco-prefix", type=str, default="mujoco", help="Prefix for MuJoCo signal columns (default: mujoco).")
    parser.add_argument(
        "--out-figure",
        type=Path,
        default=ROOT / "systematic_studies" / "outputs" / "figures" / "compare_signals.png",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "systematic_studies" / "outputs" / "compare_signals_metrics.json",
    )
    parser.add_argument("--spike-threshold-rad-s2", type=float, default=500.0)
    parser.add_argument("--jerk-threshold-rad-s3", type=float, default=5.0e4)
    parser.add_argument("--max-q-dev-rad", type=float, default=0.35)
    parser.add_argument("--max-qdot-dev-rad-s", type=float, default=4.0)
    parser.add_argument("--max-spike-count", type=int, default=0)
    parser.add_argument("--max-jerk-outliers", type=int, default=0)
    args = parser.parse_args()

    if args.parity_csv is not None:
        matlab, mujoco = _load_parity_csv(args.parity_csv)
        source_desc = str(args.parity_csv)
    else:
        if args.matlab_csv is None or args.mujoco_csv is None:
            raise ValueError("Provide either --parity-csv or both --matlab-csv and --mujoco-csv.")
        matlab = _load_canonical_csv(args.matlab_csv, args.matlab_prefix)
        mujoco = _load_canonical_csv(args.mujoco_csv, args.mujoco_prefix)
        source_desc = f"{args.matlab_csv} + {args.mujoco_csv}"

    t_ref = matlab.time_s
    mujoco_aligned = _resample_to_time(mujoco, t_ref)
    metrics = _metrics(
        t_ref,
        matlab,
        mujoco_aligned,
        spike_threshold=args.spike_threshold_rad_s2,
        jerk_threshold=args.jerk_threshold_rad_s3,
    )

    parity_ready = (
        max(metrics["max_abs_dev_q1_rad"], metrics["max_abs_dev_q2_rad"]) <= args.max_q_dev_rad
        and max(metrics["max_abs_dev_qdot1_rad_s"], metrics["max_abs_dev_qdot2_rad_s"]) <= args.max_qdot_dev_rad_s
        and metrics["spike_count_mujoco"] <= args.max_spike_count
        and metrics["spike_count_matlab"] <= args.max_spike_count
        and metrics["jerk_outliers_mujoco"] <= args.max_jerk_outliers
        and metrics["jerk_outliers_matlab"] <= args.max_jerk_outliers
    )
    metrics["parity_ready"] = bool(parity_ready)
    metrics["source"] = source_desc
    metrics["thresholds"] = {
        "max_q_dev_rad": args.max_q_dev_rad,
        "max_qdot_dev_rad_s": args.max_qdot_dev_rad_s,
        "max_spike_count": args.max_spike_count,
        "max_jerk_outliers": args.max_jerk_outliers,
        "spike_threshold_rad_s2": args.spike_threshold_rad_s2,
        "jerk_threshold_rad_s3": args.jerk_threshold_rad_s3,
    }

    _plot(t_ref, matlab, mujoco_aligned, args.out_figure)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))
    print(f"Wrote {args.out_figure} and {args.out_json}")
    if not parity_ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
