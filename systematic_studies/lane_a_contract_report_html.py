"""Read-only HTML fragment for Lane A Option B contract report (weekly dashboard).

Loads ``runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json`` only.
Does not write JSON, does not touch canonical KPI paths, and does not reuse the
weekly dashboard's canonical summary flattening helpers.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

LANE_A_CONTRACT_REPORT_REL = Path("runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json")

GUARDRAIL_LINE = (
    "This Lane A contract-C section is not the same contract as the legacy "
    "parity_strict full-horizon row."
)


def lane_a_contract_report_path(root: Path) -> Path:
    return (root / LANE_A_CONTRACT_REPORT_REL).resolve()


def _esc(s: Any) -> str:
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def render_lane_a_contract_report_section(root: Path) -> str:
    """Return standalone HTML for the Lane A subsection, or a soft missing notice."""
    path = lane_a_contract_report_path(root)
    if not path.is_file():
        return (
            '<section class="card lane-a-contract lane-a-missing" id="lane-a-contract-report">'
            "<h2>Lane A — contract-labeled reporting (derived)</h2>"
            "<p class=\"missing\">Option B derived contract report not found: "
            f"<code>{_esc(LANE_A_CONTRACT_REPORT_REL)}</code>. "
            "Regenerate with "
            "<code>python3 runs/diagnostics/lane_a_reporting_schema/build_lane_a_contract_report.py</code> "
            "if appropriate.</p>"
            "</section>"
        )
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return (
            '<section class="card lane-a-contract warn lane-a-missing" id="lane-a-contract-report">'
            "<h2>Lane A — contract-labeled reporting (derived)</h2>"
            "<p class=\"missing\">Option B derived contract report exists but could not be parsed: "
            f"<code>{_esc(path.relative_to(root))}</code>.</p>"
            "</section>"
        )

    if not isinstance(data, dict):
        return (
            '<section class="card lane-a-contract warn lane-a-missing" id="lane-a-contract-report">'
            "<h2>Lane A — contract-labeled reporting (derived)</h2>"
            "<p class=\"missing\">Invalid contract report structure (expected object).</p>"
            "</section>"
        )

    created_at = data.get("created_at")
    created_by = data.get("created_by")
    derived = data.get("derived_or_canonical")
    impl_opt = data.get("implementation_option")
    gov = data.get("governance") if isinstance(data.get("governance"), dict) else {}
    records = data.get("records")
    if not isinstance(records, list):
        records = []

    parts: list[str] = [
        '<section class="card lane-a-contract" id="lane-a-contract-report">',
        '<h2>Lane A — contract-labeled reporting (derived)</h2>',
        '<p class="lane-a-guardrail">',
        _esc(GUARDRAIL_LINE),
        "</p>",
        '<div class="lane-a-derived-banner">',
        "<p><strong>Derived — not a canonical KPI path.</strong> "
        f"<code>derived_or_canonical</code> = <code>{_esc(derived)}</code> · "
        f"<code>implementation_option</code> = <code>{_esc(impl_opt)}</code></p>",
        "<p class=\"lane-a-meta\">",
        f"<code>created_at</code>: <code>{_esc(created_at)}</code><br />",
        f"<code>created_by</code>: <code>{_esc(created_by)}</code>",
        "</p>",
        "</div>",
    ]

    if gov:
        parts.append('<div class="lane-a-governance"><h3>Governance (from JSON)</h3><ul>')
        for k, v in sorted(gov.items()):
            parts.append(f"<li><code>{_esc(k)}</code>: {_esc(v)}</li>")
        parts.append("</ul></div>")

    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            continue
        label = rec.get("contract_label", "?")
        rid = f"lane-a-record-{i}"
        parts.append(f'<article class="lane-a-record" id="{rid}">')
        parts.append(f'<h3>Record: contract <span class="contract-badge">{_esc(label)}</span></h3>')
        parts.append("<dl class=\"lane-a-kv\">")
        for key in ("ic_label", "metric_scope", "horizon_type", "run_id", "interpretation_label"):
            if key in rec and rec[key] is not None:
                parts.append(f"<dt>{_esc(key)}</dt><dd>{_esc(rec[key])}</dd>")
        if label == "C":
            for key in ("t_cut", "t_cut_rule", "bridge_gravity_sign", "sample_count"):
                if key in rec:
                    parts.append(f"<dt>{_esc(key)}</dt><dd>{_esc(rec[key])}</dd>")
            for key in ("rmse_q_rad", "rmse_qd", "strict_swing_window_gate"):
                if key in rec and rec[key] is not None:
                    parts.append(f"<dt>{_esc(key)}</dt><dd>{_esc(rec[key])}</dd>")
        if label == "D":
            warn = rec.get("diagnostic_warning")
            parts.append("<dt>diagnostic_warning</dt>")
            parts.append(f'<dd class="lane-a-d-warning">{_esc(warn)}</dd>')
            ph = rec.get("parity_ready_bridge_gate_full_horizon")
            parts.append("<dt>parity_ready_bridge_gate_full_horizon</dt>")
            parts.append(f"<dd>{_esc(ph)}</dd>")
            for key in ("velocity_spike_count_mujoco", "velocity_jerk_outlier_count_mujoco"):
                if key in rec:
                    parts.append(f"<dt>{_esc(key)}</dt><dd>{_esc(rec[key])}</dd>")
        parts.append("</dl>")
        nc = rec.get("not_claimed")
        if isinstance(nc, list) and nc:
            parts.append("<h4>Not claimed</h4><ul>")
            for item in nc:
                parts.append(f"<li>{_esc(item)}</li>")
            parts.append("</ul>")
        parts.append("</article>")

    rel = _esc(path.relative_to(root))
    parts.append(f'<p class="path">Source (read-only): <code>{rel}</code></p>')
    parts.append("</section>")
    return "".join(parts)
