#!/usr/bin/env python3
"""Generate publication-quality systematic study figures."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUTS_DIR = ROOT / "systematic_studies" / "outputs"
DEFAULT_FIGURES_DIR = DEFAULT_OUTPUTS_DIR / "figures"


def configure_plot_style(light_grid: bool = True) -> None:
    """Apply a clean, slide-friendly matplotlib style."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.size": 13,
            "axes.labelsize": 14,
            "axes.titlesize": 15,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 11,
            "lines.linewidth": 2.0,
            "lines.markersize": 6.0,
        }
    )
    if light_grid:
        plt.rcParams["axes.grid"] = True
        plt.rcParams["grid.alpha"] = 0.18
        plt.rcParams["grid.linewidth"] = 0.7
    else:
        plt.rcParams["axes.grid"] = False


def load_csv_rows(csv_file: Path, required_columns: list[str]) -> list[dict[str, float]]:
    """Load numeric CSV rows and validate required columns."""
    if not csv_file.exists():
        raise FileNotFoundError(f"Required CSV not found: {csv_file}")

    with csv_file.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {csv_file}")
        missing = [col for col in required_columns if col not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV {csv_file} is missing required columns: {missing}")

        rows: list[dict[str, float]] = []
        for raw in reader:
            parsed: dict[str, float] = {}
            for k, v in raw.items():
                if v is None or v == "":
                    continue
                parsed[k] = float(v)
            rows.append(parsed)

    if not rows:
        raise ValueError(f"CSV has no data rows: {csv_file}")
    return rows


def _group_delay_metric(
    rows: list[dict[str, float]],
    delay_key: str,
    metric_key: str,
    dt_seconds: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Aggregate metric by delay using mean value per delay bin."""
    grouped: dict[float, list[float]] = {}
    for row in rows:
        delay_steps = row[delay_key]
        delay = delay_steps * dt_seconds if dt_seconds is not None else delay_steps
        grouped.setdefault(delay, []).append(row[metric_key])

    x = np.array(sorted(grouped.keys()), dtype=float)
    y = np.array([float(np.mean(grouped[d])) for d in x], dtype=float)
    return x, y


def _smooth_curve(x: np.ndarray, y: np.ndarray, points: int = 250) -> tuple[np.ndarray, np.ndarray]:
    """Create a smooth curve if possible, fallback to straight segments."""
    if x.size < 3:
        return x, y

    x_dense = np.linspace(float(x.min()), float(x.max()), points)
    y_dense = np.interp(x_dense, x, y)

    # Optional moving-average smoothing on dense interpolation.
    win = min(11, max(3, (x_dense.size // 25) | 1))
    if win <= 3:
        return x_dense, y_dense
    kernel = np.ones(win, dtype=float) / float(win)
    y_smooth = np.convolve(y_dense, kernel, mode="same")
    return x_dense, y_smooth


def _timing_axis_label(dt_seconds: float | None) -> str:
    return "Timing Delay (s)" if dt_seconds is not None else "Timing Delay (steps)"


def _col_from_rows(rows: list[dict[str, float]], candidates: list[str]) -> np.ndarray:
    for key in candidates:
        if key in rows[0]:
            return np.array([r[key] for r in rows], dtype=float)
    raise KeyError(f"None of candidate columns found: {candidates}")


def plot_timing_vs_velocity(
    rows: list[dict[str, float]],
    figures_dir: Path,
    dt_seconds: float | None = None,
) -> Path:
    """Plot timing delay vs end-effector velocity with optimum marker."""
    x, y = _group_delay_metric(
        rows=rows,
        delay_key="elbow_delay_steps",
        metric_key="max_tip_speed_m_s",
        dt_seconds=dt_seconds,
    )
    xs, ys = _smooth_curve(x, y)
    peak_idx = int(np.argmax(y))
    peak_x = x[peak_idx]
    peak_y = y[peak_idx]

    fig, ax = plt.subplots(figsize=(8.2, 5.3))
    ax.plot(xs, ys, label="Trend")
    ax.plot(x, y, "o", label="Sweep points")
    ax.plot([peak_x], [peak_y], "o")
    ax.annotate(
        "Optimal Timing Delay",
        xy=(peak_x, peak_y),
        xytext=(10, 12),
        textcoords="offset points",
        fontsize=12,
        arrowprops={"arrowstyle": "->", "lw": 1.0},
    )
    ax.set_title("Timing Delay vs End-Effector Velocity")
    ax.set_xlabel(_timing_axis_label(dt_seconds))
    ax.set_ylabel("End-Effector Velocity (m/s)")
    ax.legend(loc="best")
    fig.tight_layout()

    out_path = figures_dir / "timing_vs_velocity.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def plot_energy_vs_timing(
    rows: list[dict[str, float]],
    figures_dir: Path,
    dt_seconds: float | None = None,
) -> Path:
    """Plot normalized efficiency proxy (energy transfer ratio) vs delay."""
    x, speed = _group_delay_metric(
        rows=rows,
        delay_key="elbow_delay_steps",
        metric_key="max_tip_speed_m_s",
        dt_seconds=dt_seconds,
    )
    max_speed = float(np.max(speed))
    ratio = speed / max_speed if max_speed > 0.0 else np.zeros_like(speed)

    xs, ys = _smooth_curve(x, ratio)
    fig, ax = plt.subplots(figsize=(8.2, 5.3))
    ax.plot(xs, ys, label="Efficiency trend")
    ax.plot(x, ratio, "o", label="Computed ratios")
    ax.set_title("Energy Transfer Ratio vs Timing Delay")
    ax.set_xlabel(_timing_axis_label(dt_seconds))
    ax.set_ylabel("Energy Transfer Ratio (-)")
    ax.set_ylim(0.0, 1.05)
    ax.legend(loc="best")
    fig.tight_layout()

    out_path = figures_dir / "energy_vs_timing.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def plot_benchmark_comparison(
    rows: list[dict[str, float]],
    figures_dir: Path,
) -> Path:
    """Create a 2x2 MATLAB-vs-MuJoCo overlay for angles and velocities."""
    t = np.array([r["time_s"] for r in rows], dtype=float)
    mj_q1_rad = _col_from_rows(rows, ["mujoco_q1_rad", "mj_q1_rad", "mj_q1_deg"])
    mj_q2_rad = _col_from_rows(rows, ["mujoco_q2_rad", "mj_q2_rad", "mj_q2_deg"])
    if "mj_q1_deg" in rows[0]:
        mj_q1 = _col_from_rows(rows, ["mj_q1_deg"])
        mj_q2 = _col_from_rows(rows, ["mj_q2_deg"])
    else:
        mj_q1 = np.rad2deg(mj_q1_rad)
        mj_q2 = np.rad2deg(mj_q2_rad)

    br_q1_deg = np.rad2deg(_col_from_rows(rows, ["bridge_q1_rad"]))
    br_q2_deg = np.rad2deg(_col_from_rows(rows, ["bridge_q2_rad"]))

    mj_qd1 = _col_from_rows(rows, ["mujoco_qdot1_rad_s", "mj_qd1_rad_s"])
    mj_qd2 = _col_from_rows(rows, ["mujoco_qdot2_rad_s", "mj_qd2_rad_s"])
    br_qd1 = _col_from_rows(rows, ["bridge_qdot1_rad_s", "bridge_qd1"])
    br_qd2 = _col_from_rows(rows, ["bridge_qdot2_rad_s", "bridge_qd2"])

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.4))
    axes = axes.ravel()

    axes[0].plot(t, mj_q1, "-", label="MuJoCo")
    axes[0].plot(t, br_q1_deg, "--", label="MATLAB")
    axes[0].set_title("Shoulder Angle")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Angle (deg)")

    axes[1].plot(t, mj_q2, "-", label="MuJoCo")
    axes[1].plot(t, br_q2_deg, "--", label="MATLAB")
    axes[1].set_title("Elbow Angle")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Angle (deg)")

    axes[2].plot(t, mj_qd1, "-", label="MuJoCo")
    axes[2].plot(t, br_qd1, "--", label="MATLAB")
    axes[2].set_title("Shoulder Velocity")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylabel("Velocity (rad/s)")

    axes[3].plot(t, mj_qd2, "-", label="MuJoCo")
    axes[3].plot(t, br_qd2, "--", label="MATLAB")
    axes[3].set_title("Elbow Velocity")
    axes[3].set_xlabel("Time (s)")
    axes[3].set_ylabel("Velocity (rad/s)")

    for ax in axes:
        ax.legend(loc="best")

    fig.suptitle("MATLAB vs MuJoCo Benchmark Comparison", y=1.02)
    fig.tight_layout()

    out_path = figures_dir / "benchmark_comparison.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def plot_summary_figure(
    double_rows: list[dict[str, float]],
    benchmark_rows: list[dict[str, float]],
    figures_dir: Path,
    dt_seconds: float | None = None,
) -> Path:
    """Create one summary figure with key timing/energy/benchmark insights."""
    x, vel = _group_delay_metric(
        rows=double_rows,
        delay_key="elbow_delay_steps",
        metric_key="max_tip_speed_m_s",
        dt_seconds=dt_seconds,
    )
    xs, vel_s = _smooth_curve(x, vel)
    peak_idx = int(np.argmax(vel))
    peak_x = x[peak_idx]
    peak_y = vel[peak_idx]

    max_speed = float(np.max(vel))
    ratio = vel / max_speed if max_speed > 0.0 else np.zeros_like(vel)
    xe, ratio_s = _smooth_curve(x, ratio)

    t = np.array([r["time_s"] for r in benchmark_rows], dtype=float)
    if "mj_q1_deg" in benchmark_rows[0]:
        mj_q1 = _col_from_rows(benchmark_rows, ["mj_q1_deg"])
    else:
        mj_q1 = np.rad2deg(_col_from_rows(benchmark_rows, ["mujoco_q1_rad", "mj_q1_rad"]))
    br_q1_deg = np.rad2deg(_col_from_rows(benchmark_rows, ["bridge_q1_rad"]))

    fig = plt.figure(figsize=(12.2, 6.5))
    gs = fig.add_gridspec(2, 3, width_ratios=(1.1, 1.1, 0.95))

    ax1 = fig.add_subplot(gs[:, 0])
    ax1.plot(xs, vel_s)
    ax1.plot(x, vel, "o")
    ax1.plot([peak_x], [peak_y], "o")
    ax1.annotate(
        "Optimal Timing Delay",
        xy=(peak_x, peak_y),
        xytext=(8, 10),
        textcoords="offset points",
        fontsize=11,
        arrowprops={"arrowstyle": "->", "lw": 0.9},
    )
    ax1.set_title("Timing vs Velocity")
    ax1.set_xlabel(_timing_axis_label(dt_seconds))
    ax1.set_ylabel("End-Effector Velocity (m/s)")

    ax2 = fig.add_subplot(gs[:, 1])
    ax2.plot(xe, ratio_s)
    ax2.plot(x, ratio, "o")
    ax2.set_title("Energy Ratio vs Timing")
    ax2.set_xlabel(_timing_axis_label(dt_seconds))
    ax2.set_ylabel("Energy Transfer Ratio (-)")
    ax2.set_ylim(0.0, 1.05)

    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(t, mj_q1, "-", label="MuJoCo")
    ax3.plot(t, br_q1_deg, "--", label="MATLAB")
    ax3.set_title("Benchmark Overlay (Angle)")
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Shoulder Angle (deg)")
    ax3.legend(loc="best")

    ax4 = fig.add_subplot(gs[1, 2])
    mj_qd1 = _col_from_rows(benchmark_rows, ["mujoco_qdot1_rad_s", "mj_qd1_rad_s"])
    br_qd1 = _col_from_rows(benchmark_rows, ["bridge_qdot1_rad_s", "bridge_qd1"])
    ax4.plot(t, mj_qd1, "-", label="MuJoCo")
    ax4.plot(t, br_qd1, "--", label="MATLAB")
    ax4.set_title("Benchmark Overlay (Velocity)")
    ax4.set_xlabel("Time (s)")
    ax4.set_ylabel("Shoulder Velocity (rad/s)")
    ax4.legend(loc="best")

    fig.suptitle("Systematic Study Summary", y=1.01)
    fig.tight_layout()

    out_path = figures_dir / "summary_figure.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def generate_all_plots(csv_path: str | Path) -> dict[str, Path]:
    """Generate all publication figures from systematic-study CSV outputs."""
    outputs_dir = Path(csv_path).expanduser().resolve()
    figures_dir = outputs_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    configure_plot_style(light_grid=True)

    double_csv = outputs_dir / "double_pendulum_sweep.csv"
    benchmark_csv = outputs_dir / "swing_benchmark_timeseries.csv"

    double_rows = load_csv_rows(
        double_csv,
        required_columns=["elbow_delay_steps", "max_tip_speed_m_s"],
    )
    benchmark_rows = load_csv_rows(
        benchmark_csv,
        required_columns=[
            "time_s",
            "bridge_q1_rad",
            "bridge_q2_rad",
        ],
    )

    dt_seconds = _infer_time_step_from_series(benchmark_rows)
    if dt_seconds is None:
        dt_seconds = _infer_delay_dt(double_rows)

    outputs = {
        "timing_vs_velocity": plot_timing_vs_velocity(double_rows, figures_dir, dt_seconds=dt_seconds),
        "energy_vs_timing": plot_energy_vs_timing(double_rows, figures_dir, dt_seconds=dt_seconds),
        "benchmark_comparison": plot_benchmark_comparison(benchmark_rows, figures_dir),
        "summary_figure": plot_summary_figure(
            double_rows, benchmark_rows, figures_dir, dt_seconds=dt_seconds
        ),
    }
    return outputs


def _infer_delay_dt(rows: list[dict[str, float]]) -> float | None:
    """Infer per-step dt from t_peak_speed_s / elbow_delay_steps if possible."""
    dt_candidates: list[float] = []
    for row in rows:
        delay = row.get("elbow_delay_steps", 0.0)
        t_peak = row.get("t_peak_speed_s")
        if t_peak is None:
            continue
        if delay > 0.0 and t_peak > 0.0:
            est = t_peak / delay
            if math.isfinite(est) and 1e-6 < est < 0.1:
                dt_candidates.append(est)
    if not dt_candidates:
        return None
    return float(np.median(np.array(dt_candidates, dtype=float)))


def _infer_time_step_from_series(rows: list[dict[str, float]]) -> float | None:
    """Infer dt from benchmark time column using median adjacent difference."""
    if len(rows) < 3:
        return None

    t = np.array([r.get("time_s", float("nan")) for r in rows], dtype=float)
    t = t[np.isfinite(t)]
    if t.size < 3:
        return None

    diffs = np.diff(t)
    diffs = diffs[diffs > 0.0]
    if diffs.size == 0:
        return None
    dt = float(np.median(diffs))
    if 1e-6 < dt < 0.1:
        return dt
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate publication-quality systematic study figures.")
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=DEFAULT_OUTPUTS_DIR,
        help="Directory containing systematic study output CSV files.",
    )
    args = parser.parse_args()

    output_paths = generate_all_plots(args.csv_path)
    print("Generated figures:")
    for name, path in output_paths.items():
        print(f"  - {name}: {path}")


if __name__ == "__main__":
    main()
