"""Weekly dashboard generator.

Regenerates the publication figures, refreshes the racket trajectory
time series, and assembles a single portable HTML report under
``systematic_studies/outputs/reports/`` that embeds every PNG as a
base64 data URI, renders the key JSON summaries as tidy tables, and
renders the current-week section of the rolling weekly log.

Usage::

    ./run.sh systematic_studies/weekly_dashboard.py
    ./run.sh systematic_studies/weekly_dashboard.py --no-open --date 2026-04-22
    ./run.sh systematic_studies/weekly_dashboard.py --skip-refresh-racket

The script is headless (no MuJoCo viewer) and relies on Python stdlib
only; ``markdown`` is used if importable, otherwise the weekly markdown
is shown inside a ``<pre>`` block.
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import html
import json
import sys
import webbrowser
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systematic_studies.lane_a_contract_report_html import render_lane_a_contract_report_section

OUTPUTS_DIR = ROOT / "systematic_studies" / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = OUTPUTS_DIR / "reports"
WEEKLY_MD = ROOT / "project_updates" / "weekly_updates.md"
CONSOLIDATED_MD = (
    ROOT / "project_updates" / "2026-04-22_project_consolidation_and_racket_viz.md"
)

FIGURE_SPECS: list[tuple[str, str, str]] = [
    (
        "timing_vs_velocity",
        "Timing vs. peak tip velocity",
        "figures/timing_vs_velocity.png",
    ),
    (
        "energy_vs_timing",
        "Energy vs. elbow timing",
        "figures/energy_vs_timing.png",
    ),
    (
        "benchmark_comparison",
        "MATLAB bridge vs. MuJoCo benchmark",
        "figures/benchmark_comparison.png",
    ),
    (
        "summary_figure",
        "Summary figure (multi-panel)",
        "figures/summary_figure.png",
    ),
    (
        "racket_trajectory_xz",
        "Racket (hand) figure-8 trace in the X-Z plane",
        "figures/racket_trajectory_xz.png",
    ),
    (
        "racket_trajectory_joint_vs_time",
        "Joint angles and hand speed vs. time",
        "figures/racket_trajectory_joint_vs_time.png",
    ),
]


# Presentation-ready captions for each figure. Each entry follows the same
# What / Why / How / Takeaway / Supervisor-Q schema so every figure in the
# report answers the same five questions at meeting tempo.
FIGURE_CAPTIONS: dict[str, dict[str, str]] = {
    "timing_vs_velocity": {
        "what": (
            "Peak end-effector (hand) speed in m/s as a function of the "
            "elbow-onset delay relative to the shoulder, expressed in "
            "simulation steps (dt = 1 ms). Green marker = argmax "
            "(empirical optimum)."
        ),
        "why": (
            "Directly probes the kinetic-chain hypothesis: does delaying "
            "the distal joint (elbow) amplify distal tip velocity, as "
            "biomechanics predicts for tennis / baseball strokes?"
        ),
        "how": (
            "Single-seed sweep in systematic_studies/double_pendulum_sweep.py; "
            "peak speed read per configuration. Rendered by "
            "plot_results.plot_timing_vs_velocity from "
            "outputs/double_pendulum_sweep.csv."
        ),
        "takeaway": (
            "A non-trivial optimum exists (delay > 0 beats simultaneous "
            "drive). Current curve is single-seed; 10-seed re-run + CIs "
            "are blocked on closing the strict parity gate."
        ),
        "supervisor_q": (
            "\"Confidence intervals?\" -> Pending multi-seed re-run once "
            "SysID closes the strict gate (docs/PHD_DIRECTIONS.md §2.1)."
        ),
    },
    "energy_vs_timing": {
        "what": (
            "Energy-transfer ratio (distal / proximal kinetic energy at "
            "release) versus the same elbow-onset delay. Same sweep as "
            "the timing plot above."
        ),
        "why": (
            "Tests whether the speed-maximising delay is also energy-"
            "efficient, i.e. whether the kinetic-chain optimum is a "
            "Pareto win rather than a brute-force exchange of effort "
            "for speed."
        ),
        "how": (
            "plot_results.plot_energy_vs_timing on "
            "outputs/double_pendulum_sweep.csv; KE computed per link "
            "from (I, qdot)."
        ),
        "takeaway": (
            "Energy ratio tracks peak-speed trend monotonically in the "
            "current regime: no obvious Pareto trade-off. Still single-"
            "seed."
        ),
        "supervisor_q": (
            "\"Is the energy metric canonical?\" -> We use "
            "KE_elbow / KE_shoulder; needs supervisor sign-off before "
            "Paper-1 submission."
        ),
    },
    "benchmark_comparison": {
        "what": (
            "Shoulder and elbow angle + angular velocity over a single "
            "0.5 s swing; MuJoCo (solid blue) vs the Python MATLAB_v2 "
            "bridge (dashed orange) given identical initial state and "
            "torque schedule."
        ),
        "why": (
            "Parity diagnostic. MATLAB_v2 is the ground-truth controller "
            "spec. If MuJoCo diverges, any timing/velocity claim that "
            "uses MuJoCo alone cannot be published against MATLAB."
        ),
        "how": (
            "systematic_studies/swing_benchmark_mujoco_vs_bridge.py "
            "writes outputs/swing_benchmark_timeseries.csv; "
            "plot_benchmark_comparison renders the 2x2 panel."
        ),
        "takeaway": (
            "Strict gate FAILS (see \"Strict parity\" table below): "
            "rmse_q ~ 2.49 rad, rmse_qdot ~ 13.76 rad/s, 7 MuJoCo "
            "velocity spikes vs 0 in MATLAB. Relaxed gate passes; that "
            "is NOT a publication claim."
        ),
        "supervisor_q": (
            "\"Integrator or parameters?\" -> Next-week task splits "
            "this: (i) RK4 on the bridge, (ii) SysID the MATLAB params "
            "to MuJoCo rollouts. Ablation table follows."
        ),
    },
    "summary_figure": {
        "what": (
            "Slide-ready multi-panel: timing-vs-velocity with the "
            "optimal-delay marker, and energy-transfer-vs-timing. "
            "Collapses the two sweep figures above into a single figure "
            "for talks."
        ),
        "why": (
            "Single deliverable that captures the headline result "
            "candidate for Paper 1 (\"Hybrid residual control + a "
            "validated timing study\")."
        ),
        "how": (
            "plot_results.plot_summary_figure combines sweep CSV + "
            "benchmark CSV."
        ),
        "takeaway": (
            "Do NOT quote as a Paper-1 figure yet. Strict parity is "
            "required first; this figure will be re-rendered with 10-"
            "seed CIs once the parity gate closes."
        ),
        "supervisor_q": (
            "\"Is this the figure we will submit?\" -> Not verbatim. "
            "Target is a 3-panel Paper-1 figure with CIs + a parity "
            "status box."
        ),
    },
    "racket_trajectory_xz": {
        "what": (
            "End-effector (hand site) trajectory in the arm's X-Z plane "
            "over 10 s of closed-loop simulation. The desired workspace "
            "Lissajous 2:1 reference is tracked via IK + joint-space "
            "PD control."
        ),
        "why": (
            "Qualitative demonstration that the two-link arm can execute "
            "a clean infinity-shaped warm-up motion. The figure-8 is the "
            "candidate structured-exploration prior for a residual "
            "policy (PhD direction §1.4 / §3.3)."
        ),
        "how": (
            "./run.sh systematic_studies/racket_trajectory.py "
            "--protocol workspace_figure8 --mode plot --steps 10000. "
            "See Racket-summary table below for the FFT-based "
            "figure8_detected flag."
        ),
        "takeaway": (
            "Clean infinity trace: figure8_detected = true, "
            "freq_ratio_z_over_x ~ 2.00 (exact Lissajous condition), "
            "~89 self-intersections (consistent with a tight figure-8)."
        ),
        "supervisor_q": (
            "\"How do you decide it IS a figure-8?\" -> Zero-padded "
            "rFFT of centred X and Z after a settle window; ratio in "
            "[1.6, 2.4] OR [0.42, 0.62]; stdev gate + self-intersection "
            "count. Implementation: racket_trajectory.detect_figure8."
        ),
    },
    "racket_trajectory_joint_vs_time": {
        "what": (
            "Per-joint angle (q1 shoulder, q2 elbow) and the "
            "end-effector speed magnitude in the X-Z plane, all plotted "
            "against time for the same 10 s rollout."
        ),
        "why": (
            "Sanity-check the PD tracking: joint signals should be "
            "smooth sinusoids at frequencies f and 2f respectively "
            "(Lissajous condition) with no chatter or saturation."
        ),
        "how": (
            "Same rollout as the X-Z trace above; "
            "plot_results.plot_racket_trajectory renders this panel from "
            "outputs/racket_trajectory_timeseries.csv."
        ),
        "takeaway": (
            "Joint angles are clean sinusoids at the expected ratio; no "
            "torque clipping; hand-speed envelope is periodic and bounded "
            "(~ 1 m/s peaks)."
        ),
        "supervisor_q": (
            "\"Is the PD gain tuned or arbitrary?\" -> Fixed at (kp=120, "
            "kd=8); deliberately under-aggressive to stay well inside "
            "the actuator limits. Gain sweep is deferred, low-priority."
        ),
    },
}


# One-line context for each JSON summary table so the reader knows what
# to scan for without opening the source file.
JSON_CONTEXTS: dict[str, str] = {
    "racket_trajectory_summary": (
        "All figure-8 detection metrics + the schedule that generated "
        "them. Key row: figure8_detected (must be true) and "
        "freq_ratio_z_over_x (expected ~ 2.00)."
    ),
    "parity_strict": (
        "Current strict MATLAB vs. MuJoCo parity residual on the swing "
        "benchmark. parity_ready = true is the gate for Paper-1 claims. "
        "Scan: rmse_q_rad, rmse_qdot_rad_s, spike_count_mujoco, "
        "jerk_outliers_mujoco, parity_ready."
    ),
    "parity_relaxed": (
        "Relaxed-bridge parity check used for iteration only. Passing "
        "this gate is NOT a publication claim; it is a debug signal."
    ),
    "swing_benchmark": (
        "Single-swing benchmark run: bridge vs. MuJoCo deltas, "
        "parity_ready_bridge_gate, hand-speed RMSE. Aggregates into the "
        "benchmark_comparison figure above."
    ),
    "eval_sac": (
        "Most recent SAC policy evaluation (two-link arm). Scan: "
        "mean_return, success_rate. Current run is the pre-SysID "
        "baseline and is expected to improve after re-training on the "
        "mechanically-consistent plant."
    ),
}

JSON_SPECS: list[tuple[str, str, Path, list[str] | None]] = [
    (
        "racket_trajectory_summary",
        "Racket trajectory summary",
        OUTPUTS_DIR / "racket_trajectory_summary.json",
        None,
    ),
    (
        "parity_strict",
        "Strict MATLAB vs. MuJoCo parity metrics",
        OUTPUTS_DIR / "compare_signals_matlab_vs_mujoco_metrics.json",
        None,
    ),
    (
        "parity_relaxed",
        "Relaxed bridge parity metrics",
        OUTPUTS_DIR / "compare_signals_bridge_relaxed_metrics.json",
        None,
    ),
    (
        "swing_benchmark",
        "Swing benchmark summary",
        OUTPUTS_DIR / "swing_benchmark_summary.json",
        None,
    ),
    (
        "eval_sac",
        "SAC eval summary (two-link arm)",
        ROOT / "example_two_link" / "metrics" / "eval_sac_two_link_arm.json",
        [
            "checkpoint",
            "n_episodes",
            "mean_return",
            "std_return",
            "mean_final_dist",
            "std_final_dist",
            "success_rate",
        ],
    ),
]


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value != value:  # NaN
            return "NaN"
        if abs(value) >= 1e4 or (abs(value) > 0 and abs(value) < 1e-3):
            return f"{value:.3e}"
        return f"{value:.6g}"
    if isinstance(value, (list, tuple)):
        if all(not isinstance(v, (dict, list, tuple)) for v in value):
            return ", ".join(_format_scalar(v) for v in value)
        return json.dumps(value)
    if isinstance(value, dict):
        return json.dumps(value)
    return html.escape(str(value))


def _flatten_json(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    """Flatten a nested JSON object to ``(dotted_key, scalar)`` pairs."""
    rows: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                rows.extend(_flatten_json(v, key))
            elif isinstance(v, (list, tuple)) and v and isinstance(v[0], dict):
                rows.append((key, f"<list of {len(v)} objects>"))
            else:
                rows.append((key, v))
    else:
        rows.append((prefix or "value", obj))
    return rows


def _filter_fields(
    flat: list[tuple[str, Any]], fields: Iterable[str] | None
) -> list[tuple[str, Any]]:
    if not fields:
        return flat
    allow = {f: i for i, f in enumerate(fields)}
    picked = [(k, v) for (k, v) in flat if k in allow]
    picked.sort(key=lambda kv: allow.get(kv[0], 0))
    return picked


def _render_caption(slug: str) -> str:
    """Render the What/Why/How/Takeaway/Supervisor-Q block for a figure."""
    cap = FIGURE_CAPTIONS.get(slug)
    if not cap:
        return ""
    rows: list[str] = ['<dl class="caption">']
    pairs = [
        ("What", cap.get("what", "")),
        ("Why", cap.get("why", "")),
        ("How", cap.get("how", "")),
        ("Takeaway", cap.get("takeaway", "")),
        ("Likely Q", cap.get("supervisor_q", "")),
    ]
    for label, text in pairs:
        if not text:
            continue
        rows.append(
            f"<dt>{html.escape(label)}</dt>"
            f"<dd>{html.escape(text)}</dd>"
        )
    rows.append("</dl>")
    return "".join(rows)


def render_image_card(spec: tuple[str, str, str]) -> str:
    slug, title, rel_path = spec
    abs_path = OUTPUTS_DIR / rel_path
    title_esc = html.escape(title)
    rel_esc = html.escape(rel_path)
    if not abs_path.exists():
        return (
            f'<section class="card warn" id="fig-{slug}">'
            f"<h3>{title_esc}</h3>"
            f'<p class="missing">Missing figure: <code>{rel_esc}</code>.</p>'
            "<p>Regenerate with <code>./run.sh systematic_studies/visualisation/plot_results.py</code>.</p>"
            "</section>"
        )
    try:
        data = abs_path.read_bytes()
    except OSError as exc:
        return (
            f'<section class="card warn" id="fig-{slug}">'
            f"<h3>{title_esc}</h3>"
            f'<p class="missing">Unable to read <code>{rel_esc}</code>: {html.escape(str(exc))}.</p>'
            "</section>"
        )
    b64 = base64.b64encode(data).decode("ascii")
    caption_html = _render_caption(slug)
    return (
        f'<section class="card" id="fig-{slug}">'
        f"<h3>{title_esc}</h3>"
        f'<img loading="lazy" alt="{title_esc}" src="data:image/png;base64,{b64}" />'
        f"{caption_html}"
        f'<p class="path">Source: <code>{rel_esc}</code></p>'
        "</section>"
    )


def render_json_table(
    slug: str, title: str, path: Path, fields: list[str] | None
) -> str:
    title_esc = html.escape(title)
    rel = html.escape(str(path.relative_to(ROOT)))
    if not path.exists():
        return (
            f'<section class="card warn" id="json-{slug}">'
            f"<h3>{title_esc}</h3>"
            f'<p class="missing">Missing JSON: <code>{rel}</code>.</p>'
            "</section>"
        )
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return (
            f'<section class="card warn" id="json-{slug}">'
            f"<h3>{title_esc}</h3>"
            f'<p class="missing">Failed to parse <code>{rel}</code>: {html.escape(str(exc))}.</p>'
            "</section>"
        )

    flat = _flatten_json(payload)
    flat = _filter_fields(flat, fields)
    if not flat:
        return (
            f'<section class="card warn" id="json-{slug}">'
            f"<h3>{title_esc}</h3>"
            f'<p class="missing">Empty or filtered out. Source: <code>{rel}</code>.</p>'
            "</section>"
        )

    rows_html = "".join(
        f"<tr><th scope='row'>{html.escape(k)}</th><td>{_format_scalar(v)}</td></tr>"
        for (k, v) in flat
    )
    context = JSON_CONTEXTS.get(slug, "")
    context_html = (
        f'<p class="context">{html.escape(context)}</p>' if context else ""
    )
    return (
        f'<section class="card" id="json-{slug}">'
        f"<h3>{title_esc}</h3>"
        f"{context_html}"
        f'<table class="kv"><thead><tr><th>Key</th><th>Value</th></tr></thead>'
        f"<tbody>{rows_html}</tbody></table>"
        f'<p class="path">Source: <code>{rel}</code></p>'
        "</section>"
    )


def _render_markdown(md_text: str) -> str:
    try:
        import markdown as _md  # type: ignore
    except Exception:
        return f'<pre class="markdown-fallback">{html.escape(md_text)}</pre>'
    try:
        return _md.markdown(md_text, extensions=["fenced_code", "tables"])
    except Exception:
        return f'<pre class="markdown-fallback">{html.escape(md_text)}</pre>'


def _extract_current_week_section(md_text: str, iso_week: str) -> str | None:
    """Return the `## Week <iso_week> ...` section, or None if not found."""
    marker = f"## Week {iso_week}"
    start = md_text.find(marker)
    if start == -1:
        return None
    after = md_text.find("\n## ", start + 1)
    if after == -1:
        after = md_text.find("\n---\n", start + 1)
    return md_text[start:after] if after != -1 else md_text[start:]


def _extract_archive_index(md_text: str) -> str | None:
    marker = "## Past weeks (archive)"
    start = md_text.find(marker)
    if start == -1:
        return None
    end = md_text.find("\n---\n", start + 1)
    if end == -1:
        end = md_text.find("\n## ", start + 1)
    return md_text[start:end] if end != -1 else md_text[start:]


def render_markdown_block(iso_week: str) -> str:
    if not WEEKLY_MD.exists():
        return (
            '<section class="card warn" id="weekly-md">'
            "<h3>Weekly updates</h3>"
            f'<p class="missing">Missing <code>{html.escape(str(WEEKLY_MD.relative_to(ROOT)))}</code>.</p>'
            "</section>"
        )
    md_text = WEEKLY_MD.read_text()

    current = _extract_current_week_section(md_text, iso_week)
    archive = _extract_archive_index(md_text)

    parts = [
        '<section class="card" id="weekly-md">',
        "<h3>Weekly updates</h3>",
    ]
    if current:
        parts.append('<div class="md-rendered">')
        parts.append(_render_markdown(current))
        parts.append("</div>")
    else:
        parts.append(
            f'<p class="missing">Could not find a <code>## Week {html.escape(iso_week)}</code> section in '
            f"<code>{html.escape(str(WEEKLY_MD.relative_to(ROOT)))}</code>.</p>"
        )

    if archive:
        parts.append(
            '<details class="archive-index"><summary>Past weeks (archive)</summary>'
            '<div class="md-rendered">'
        )
        parts.append(_render_markdown(archive))
        parts.append("</div></details>")

    rel = html.escape(str(WEEKLY_MD.relative_to(ROOT)))
    parts.append(f'<p class="path">Source: <code>{rel}</code></p>')

    if CONSOLIDATED_MD.exists():
        rel_cons = html.escape(str(CONSOLIDATED_MD.relative_to(ROOT)))
        parts.append(
            f'<p class="path">Consolidated update: <code>{rel_cons}</code></p>'
        )
    parts.append("</section>")
    return "".join(parts)


CSS = """
:root {
  --bg: #0f172a;
  --card: #1e293b;
  --card-warn: #3f2f14;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --border: #334155;
  --table-alt: #0f172a;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 2rem clamp(1rem, 4vw, 3rem);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}
header.report {
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1rem;
}
header.report h1 { margin: 0 0 .25rem; font-size: 1.75rem; }
header.report .meta { color: var(--muted); font-size: .9rem; }
header.report .meta code { background: var(--card); padding: .05rem .35rem; border-radius: 4px; }
nav.toc {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: .75rem 1rem;
  margin-bottom: 1.5rem;
}
nav.toc h2 { font-size: 1rem; margin: 0 0 .5rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
nav.toc ul { margin: 0; padding-left: 1.2rem; }
nav.toc a { color: var(--accent); text-decoration: none; }
nav.toc a:hover { text-decoration: underline; }
section.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}
section.card.warn {
  background: var(--card-warn);
  border-color: #eab308;
}
section.card.warn .missing { color: #facc15; font-weight: 600; }
section.card h3 { margin-top: 0; margin-bottom: .75rem; font-size: 1.1rem; color: var(--accent); }
section.card img { max-width: 100%; border-radius: 6px; border: 1px solid var(--border); background: white; }
section.card p.path { font-size: .8rem; color: var(--muted); margin: .5rem 0 0; }
section.card code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .85rem; }
table.kv { width: 100%; border-collapse: collapse; font-size: .9rem; }
table.kv th, table.kv td { text-align: left; padding: .35rem .6rem; border-bottom: 1px solid var(--border); vertical-align: top; }
table.kv tbody tr:nth-child(even) { background: var(--table-alt); }
table.kv th[scope='row'] { font-weight: 500; color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; width: 45%; }
table.kv td { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 520px), 1fr));
}
.md-rendered h1, .md-rendered h2 { font-size: 1.1rem; color: var(--accent); }
.md-rendered h3 { font-size: 1rem; }
.md-rendered ul { padding-left: 1.25rem; }
.md-rendered a { color: var(--accent); }
.md-rendered code { background: rgba(148, 163, 184, .15); padding: .05rem .3rem; border-radius: 3px; }
pre.markdown-fallback {
  white-space: pre-wrap;
  background: var(--table-alt);
  padding: 1rem;
  border-radius: 6px;
  max-height: 60vh;
  overflow: auto;
}
details.archive-index { margin-top: 1rem; }
details.archive-index summary { cursor: pointer; color: var(--muted); }
footer.report { color: var(--muted); font-size: .8rem; margin-top: 2rem; border-top: 1px solid var(--border); padding-top: 1rem; }

/* Presentation-ready caption underneath each figure card */
section.card p.context { color: var(--muted); font-size: .88rem; margin: .25rem 0 .75rem; }
h2 + p.section-sub { color: var(--muted); font-size: .88rem; margin: -.5rem 0 1rem; }
dl.caption {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: .3rem .85rem;
  margin: .85rem 0 .25rem;
  font-size: .88rem;
  border-top: 1px solid var(--border);
  padding-top: .75rem;
}
dl.caption dt {
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: .06em;
  font-size: .7rem;
  font-weight: 700;
  padding-top: .15rem;
}
dl.caption dd { margin: 0; color: var(--text); line-height: 1.45; }
dl.caption dt:nth-of-type(5) { color: #facc15; }

/* 'At a glance' KPI strip */
section.card.intro ul { padding-left: 1.2rem; margin: .5rem 0 0; font-size: .9rem; line-height: 1.55; }
section.card.intro li { margin-bottom: .25rem; }
.kpi-strip {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
  margin-top: .5rem;
}
.kpi {
  background: rgba(148, 163, 184, .08);
  border: 1px solid var(--border);
  border-left-width: 4px;
  border-radius: 8px;
  padding: .75rem .9rem;
}
.kpi-label { font-size: .7rem; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.kpi-value { font-size: 1.3rem; font-weight: 600; margin-top: .2rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.kpi-hint { font-size: .78rem; color: var(--muted); margin-top: .25rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.kpi.kpi-ok   { border-left-color: #22c55e; }
.kpi.kpi-ok   .kpi-value { color: #86efac; }
.kpi.kpi-warn { border-left-color: #eab308; }
.kpi.kpi-warn .kpi-value { color: #facc15; }
.kpi.kpi-bad  { border-left-color: #ef4444; }
.kpi.kpi-bad  .kpi-value { color: #fca5a5; }
.kpi.kpi-info { border-left-color: var(--accent); }
.kpi.kpi-info .kpi-value { color: var(--accent); }

/* Lane A Option B derived subsection (firewall from canonical JSON_SPECS tables) */
section.lane-a-contract {
  border: 2px solid var(--accent);
  margin: 2rem 0;
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.12), var(--card));
}
section.lane-a-contract h2 {
  margin-top: 0;
  color: var(--accent);
  font-size: 1.25rem;
}
section.lane-a-contract.lane-a-missing {
  border-color: var(--border);
  background: var(--card-warn);
}
p.lane-a-guardrail {
  font-weight: 600;
  color: #facc15;
  border-left: 4px solid #eab308;
  padding: 0.75rem 1rem;
  margin: 1rem 0;
  background: rgba(234, 179, 8, 0.12);
  line-height: 1.45;
}
div.lane-a-derived-banner {
  border: 1px dashed var(--accent);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
p.lane-a-meta code { font-size: 0.85rem; }
div.lane-a-governance ul { margin: 0.25rem 0 0; padding-left: 1.2rem; }
article.lane-a-record {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.1rem;
  margin-bottom: 1rem;
  background: rgba(15, 23, 42, 0.55);
}
span.contract-badge {
  display: inline-block;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  background: rgba(56, 189, 248, 0.25);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
dl.lane-a-kv {
  display: grid;
  grid-template-columns: minmax(9rem, 32%) 1fr;
  gap: 0.35rem 0.75rem;
  font-size: 0.88rem;
  margin: 0.5rem 0 0;
}
dl.lane-a-kv dt {
  color: var(--muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
dl.lane-a-kv dd {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
dd.lane-a-d-warning {
  white-space: pre-wrap;
  color: #fecaca;
}
hr.lane-a-sep {
  border: none;
  border-top: 2px solid var(--accent);
  margin: 2rem 0 1.5rem;
  opacity: 0.85;
}
""".strip()


def _safe_load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        if value != value:
            return "NaN"
        return f"{value:.{digits}g}"
    return html.escape(str(value))


def _kpi_tile(label: str, value: str, status: str, hint: str = "") -> str:
    status_class = {
        "ok": "kpi-ok",
        "warn": "kpi-warn",
        "bad": "kpi-bad",
        "info": "kpi-info",
    }.get(status, "kpi-info")
    hint_html = f'<div class="kpi-hint">{html.escape(hint)}</div>' if hint else ""
    return (
        f'<div class="kpi {status_class}">'
        f'<div class="kpi-label">{html.escape(label)}</div>'
        f'<div class="kpi-value">{value}</div>'
        f"{hint_html}"
        "</div>"
    )


def render_executive_summary() -> str:
    """Render the 'At a glance' KPI strip from the embedded JSON summaries.

    Reads the same JSONs that are rendered as tables below, so the KPIs
    and the detailed tables always agree.
    """
    parity_strict = _safe_load_json(
        OUTPUTS_DIR / "compare_signals_matlab_vs_mujoco_metrics.json"
    )
    parity_relaxed = _safe_load_json(
        OUTPUTS_DIR / "compare_signals_bridge_relaxed_metrics.json"
    )
    racket = _safe_load_json(OUTPUTS_DIR / "racket_trajectory_summary.json")
    eval_sac = _safe_load_json(
        ROOT / "example_two_link" / "metrics" / "eval_sac_two_link_arm.json"
    )

    tiles: list[str] = []

    if parity_strict:
        rmse_q = parity_strict.get("rmse_q_rad")
        rmse_qdot = parity_strict.get("rmse_qdot_rad_s")
        ready = bool(parity_strict.get("parity_ready", False))
        status = "ok" if ready else "bad"
        tiles.append(
            _kpi_tile(
                "Strict parity",
                f"{'READY' if ready else 'FAILING'}",
                status,
                hint=(
                    f"rmse_q = {_fmt(rmse_q)} rad | "
                    f"rmse_qdot = {_fmt(rmse_qdot)} rad/s"
                ),
            )
        )
    else:
        tiles.append(_kpi_tile("Strict parity", "n/a", "warn", "summary missing"))

    if parity_relaxed is not None:
        relaxed_ready = bool(parity_relaxed.get("parity_ready_bridge_gate", False))
        tiles.append(
            _kpi_tile(
                "Relaxed parity gate",
                "pass" if relaxed_ready else "fail",
                "info" if relaxed_ready else "warn",
                hint="debug-only; NOT a publication claim",
            )
        )

    if racket is not None:
        detected = bool(racket.get("figure8_detected", False))
        ratio = racket.get("freq_ratio_z_over_x")
        self_x = racket.get("self_intersections")
        tiles.append(
            _kpi_tile(
                "Racket figure-8",
                "detected" if detected else "not detected",
                "ok" if detected else "warn",
                hint=(
                    f"z/x freq ratio = {_fmt(ratio, 3)} | "
                    f"self-intersections = {_fmt(self_x, 0)}"
                ),
            )
        )

    if eval_sac is not None:
        mean_ret = eval_sac.get("mean_return")
        success = eval_sac.get("success_rate")
        n_ep = eval_sac.get("n_episodes")
        success_status = "ok" if isinstance(success, (int, float)) and success > 0.5 else "warn"
        tiles.append(
            _kpi_tile(
                "SAC eval (two-link)",
                f"return = {_fmt(mean_ret)}",
                success_status,
                hint=f"success_rate = {_fmt(success)} over {_fmt(n_ep, 0)} episodes",
            )
        )

    if not tiles:
        return ""

    return (
        '<section class="card" id="at-a-glance">'
        '<h3>At a glance</h3>'
        '<p class="context">Live KPIs read from the embedded JSON summaries below. '
        "Strict parity is the hard gate for Paper-1 claims.</p>"
        f'<div class="kpi-strip">{"".join(tiles)}</div>'
        "</section>"
    )


def render_intro_banner() -> str:
    return (
        '<section class="card intro" id="how-to-read">'
        '<h3>How to read this report</h3>'
        "<ul>"
        "<li><strong>At a glance</strong> (below): current status of the parity gate, "
        "figure-8 detector, and SAC eval, all read live from the JSONs embedded "
        "further down the page.</li>"
        "<li><strong>Each figure</strong> is followed by a fixed 5-field caption "
        "(<em>What / Why / How / Takeaway / Likely supervisor Q</em>) so every "
        "plot answers the same questions at meeting tempo.</li>"
        "<li><strong>Each JSON summary</strong> has a one-line context above the "
        "key/value table flagging the rows to scan first.</li>"
        "<li><strong>Source pointers</strong>: PhD roadmap "
        "<code>docs/PHD_DIRECTIONS.md</code>; weekly log "
        "<code>project_updates/weekly_updates.md</code>; this week's consolidated "
        "update <code>project_updates/2026-04-22_project_consolidation_and_racket_viz.md</code>."
        "</li>"
        "</ul>"
        "</section>"
    )


def _iso_week_and_year(d: _dt.date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def _build_toc() -> str:
    items: list[str] = []
    items.append('<li><a href="#how-to-read">How to read this report</a></li>')
    items.append('<li><a href="#at-a-glance">At a glance</a></li>')
    items.append('<li><a href="#weekly-md">Weekly updates</a></li>')
    items.append('<li><a href="#lane-a-contract-report">Lane A (derived contract report)</a></li>')
    items.append("<li>Figures")
    items.append("<ul>")
    for slug, title, _ in FIGURE_SPECS:
        items.append(f'<li><a href="#fig-{slug}">{html.escape(title)}</a></li>')
    items.append("</ul></li>")
    items.append("<li>Summaries")
    items.append("<ul>")
    for slug, title, _, _ in JSON_SPECS:
        items.append(f'<li><a href="#json-{slug}">{html.escape(title)}</a></li>')
    items.append("</ul></li>")
    return "".join(items)


def build_report_html(report_date: _dt.date, iso_week: str) -> str:
    generated_at = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    figures_html = "".join(render_image_card(spec) for spec in FIGURE_SPECS)
    json_html = "".join(
        render_json_table(slug, title, path, fields)
        for (slug, title, path, fields) in JSON_SPECS
    )
    toc_html = _build_toc()
    intro_html = render_intro_banner()
    kpi_html = render_executive_summary()
    weekly_html = render_markdown_block(iso_week)
    lane_a_html = render_lane_a_contract_report_section(ROOT)

    return f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\" />
<title>Weekly dashboard {html.escape(iso_week)} ({html.escape(report_date.isoformat())})</title>
<style>{CSS}</style>
</head><body>
<header class=\"report\">
  <h1>Two-link arm weekly dashboard</h1>
  <p class=\"meta\">ISO week <code>{html.escape(iso_week)}</code> | Report date <code>{html.escape(report_date.isoformat())}</code> | Generated {html.escape(generated_at)}</p>
</header>
<nav class=\"toc\">
  <h2>Contents</h2>
  <ul>{toc_html}</ul>
</nav>
{intro_html}
{kpi_html}
{weekly_html}
<hr class="lane-a-sep" />
{lane_a_html}
<h2>Figures</h2>
<p class=\"section-sub\">Each figure is followed by a fixed What / Why / How / Takeaway / Likely-supervisor-question caption.</p>
<div class=\"grid\">{figures_html}</div>
<h2>Summaries</h2>
<p class=\"section-sub\">Each table has a one-line context above it flagging the rows to scan first.</p>
<div class=\"grid\">{json_html}</div>
<footer class=\"report\">
  <p>Rebuild this report at any time with <code>./run.sh systematic_studies/weekly_dashboard.py</code>.</p>
  <p>Figures live under <code>systematic_studies/outputs/figures/</code>; reports under <code>systematic_studies/outputs/reports/</code>.</p>
</footer>
</body></html>
"""


def refresh_racket_trajectory() -> tuple[bool, str]:
    """Re-run the workspace figure-8 simulation to refresh CSV+JSON."""
    try:
        from systematic_studies import racket_trajectory as rt
    except Exception as exc:
        return False, f"Could not import racket_trajectory: {exc!r}"
    try:
        rows, summary = rt.simulate(
            xml_path=rt.DEFAULT_XML,
            protocol="workspace_figure8",
            steps=10000,
            a_shoulder=18.0,
            a_elbow=10.0,
            f_shoulder_hz=0.6,
            elbow_freq_ratio=2.0,
            elbow_phase_deg=90.0,
            q1_amp_deg=35.0,
            q2_amp_deg=45.0,
            q1_offset_deg=0.0,
            q2_offset_deg=70.0,
            pd_kp=120.0,
            pd_kd=8.0,
            q1_init_deg=10.0,
            q2_init_deg=70.0,
            qd1=0.0,
            qd2=0.0,
            ws_center_x=0.40,
            ws_center_z=1.20,
            ws_half_width_m=0.12,
            ws_half_height_m=0.08,
            ws_f_hz=0.5,
            viewer_mode=False,
            viewer_realtime=False,
        )
        rt.write_csv(rows, rt.DEFAULT_CSV)
        rt.write_summary(summary, rt.DEFAULT_JSON)
        return True, (
            f"figure8_detected={summary.get('figure8_detected')} "
            f"freq_ratio_z_over_x={summary.get('freq_ratio_z_over_x'):.2f}"
        )
    except Exception as exc:
        return False, f"racket_trajectory simulate failed: {exc!r}"


def regenerate_figures() -> tuple[bool, dict[str, Path] | str]:
    try:
        from systematic_studies.visualisation.plot_results import generate_all_plots
    except Exception as exc:
        return False, f"Could not import plot_results: {exc!r}"
    try:
        return True, generate_all_plots(OUTPUTS_DIR)
    except Exception as exc:
        return False, f"generate_all_plots failed: {exc!r}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate figures and render a weekly HTML dashboard.",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Override report date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the HTML report in the default browser.",
    )
    parser.add_argument(
        "--skip-refresh-racket",
        action="store_true",
        help="Skip re-running the racket trajectory simulation before rendering.",
    )
    parser.add_argument(
        "--skip-regenerate-figures",
        action="store_true",
        help="Skip re-running plot_results.generate_all_plots.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Override output HTML path. Defaults to reports/weekly_dashboard_<week>_<date>.html.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.date:
        report_date = _dt.date.fromisoformat(args.date)
    else:
        report_date = _dt.date.today()
    iso_week = _iso_week_and_year(report_date)

    print(f"[weekly_dashboard] report date: {report_date.isoformat()} ({iso_week})")

    if args.skip_refresh_racket:
        print("[weekly_dashboard] skipping racket trajectory refresh (per --skip-refresh-racket)")
    else:
        print("[weekly_dashboard] refreshing racket trajectory (workspace_figure8, 10000 steps)...")
        ok, info = refresh_racket_trajectory()
        tag = "ok" if ok else "warn"
        print(f"[weekly_dashboard]   racket refresh {tag}: {info}")

    if args.skip_regenerate_figures:
        print("[weekly_dashboard] skipping figure regeneration (per --skip-regenerate-figures)")
    else:
        print("[weekly_dashboard] regenerating publication figures...")
        ok, info = regenerate_figures()
        if ok and isinstance(info, dict):
            for name, path in info.items():
                print(f"[weekly_dashboard]   wrote {name}: {path.relative_to(ROOT)}")
        else:
            print(f"[weekly_dashboard]   figure regeneration warn: {info}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = args.out or (
        REPORTS_DIR / f"weekly_dashboard_{iso_week}_{report_date.isoformat()}.html"
    )

    html_text = build_report_html(report_date, iso_week)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_text)
    try:
        display_path: Path | str = out_path.relative_to(ROOT)
    except ValueError:
        display_path = out_path
    print(f"[weekly_dashboard] wrote report: {display_path}")

    embedded_figs = [s for s, _, rel in FIGURE_SPECS if (OUTPUTS_DIR / rel).exists()]
    missing_figs = [s for s, _, rel in FIGURE_SPECS if not (OUTPUTS_DIR / rel).exists()]
    embedded_json = [s for s, _, p, _ in JSON_SPECS if p.exists()]
    missing_json = [s for s, _, p, _ in JSON_SPECS if not p.exists()]
    print(
        f"[weekly_dashboard] embedded {len(embedded_figs)}/{len(FIGURE_SPECS)} figures, "
        f"{len(embedded_json)}/{len(JSON_SPECS)} JSON summaries"
    )
    if missing_figs:
        print(f"[weekly_dashboard] missing figures: {missing_figs}")
    if missing_json:
        print(f"[weekly_dashboard] missing JSON summaries: {missing_json}")

    if not args.no_open:
        url = out_path.resolve().as_uri()
        print(f"[weekly_dashboard] opening {url}")
        try:
            webbrowser.open(url)
        except Exception as exc:
            print(f"[weekly_dashboard] could not open browser: {exc!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
