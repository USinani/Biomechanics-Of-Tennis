# Lane A Decision Board

**Model contract (options, stop rules, next experiments):** [`docs/research/LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`](LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md)

**Pre-limit strict RMSE closure (scored moves, red team, permissions):** [`docs/research/LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md`](LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md)

**Reporting / dashboard contract (planning only, no code yet):** [`docs/research/LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`](LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md)

**Thesis/report-facing Lane A summary (markdown only):** [`docs/research/LANE_A_REPORTING_NOTE.md`](LANE_A_REPORTING_NOTE.md)

**Supervisor-facing Lane A brief (markdown only):** [`docs/research/LANE_A_SUPERVISOR_SUMMARY.md`](LANE_A_SUPERVISOR_SUMMARY.md)

**Phase 2 clean fork / folder plan (planning only):** [`docs/research/PHASE_2_CLEAN_FORK_PLAN.md`](PHASE_2_CLEAN_FORK_PLAN.md)

**Phase 2 provisional governance & branch (not created):** **A** — **contract C** primary smooth-dynamics metric: **YES (provisional)** · **B** — **contract D** diagnostic-only: **YES** · **C** — defer constrained **B**: **YES** · **D** — **`bridge_gravity_sign=mujoco`**: **opt-in** until replication + supervisor sign-off for default: **YES**. **Proposed branch:** `phase-2-contract-c` ← parent **`chore/agent-pack`** @ **`cebb4477`**. Detail: plan **§8a–§8c**.

## 1. Research objective
Close or explain strict parity between MuJoCo, Python bridge analytical dynamics, and MATLAB-native dynamics under a reproducible model contract.

## 2. Current state summary
- **relaxed bridge parity status**: **not closed** (benchmark gate `parity_ready_bridge_gate` remains false in all recent derived probes; relaxed `compare_signals_bridge_relaxed_metrics.json` exists as a contract artifact but is not used as strict closure evidence here).
- **strict native parity status**: **historical strict artifact exists and reports parity not ready**; strict native replay is currently **parked** due to MATLAB batch failure (see below).
- **qdot2 spike/jerk event status**: **explained** for the MuJoCo side as **constrained (XML joint limits) vs unconstrained bridge** mismatch; **removed** when joint limits are disabled in-memory on the same 500-step derived benchmark (`runs/diagnostics/evidence_packets/lane_a_joint_limit_ablation.md`). Baseline **reproduced** the event before ablation.
- **whole-run RMSE / bridge gate status**: **open** — `parity_ready_bridge_gate` remains **false** on both baseline and no-limit summaries (RMSE vs thresholds, not spike counts, dominates on no-limit run). Whole-run KPIs on the **mixed** XML-limited vs unconstrained bridge horizon remain **diagnostic** for strict ODE claims until a **pre-limit** or **no-limit** contract is adopted (see model-contract brief).
- **pre-limit contract (C) metrics**: **baseline (bridge default)** — `time_s < 0.480`, **480** rows; MuJoCo spike/jerk **0/0**; relaxed gate **passes**; **strict** swing-style RMSE gate **failed** (~**2.32** / ~**12.16** rad/s) (`lane_a_prelimit_metrics_probe.md`). **With `--bridge-gravity-sign mujoco` (M1 trajectory probe):** same window; pre-limit **strict gate passes** (RMSE q ~**0.62** rad, RMSE qd ~**3.39** rad/s); see `lane_a_prelimit_gravity_sign_trajectory_probe.md`, `parity_prelimit_gravity_sign/prelimit_compare.json`.
- **full-horizon (D) with gravity-sign**: RMSE improves but **`parity_ready_bridge_gate` still false** (MuJoCo limit-contact spike/jerk unchanged)—**diagnostic only**, not contract **C**.
- **reporting / scoring contract**: **explicit** in `LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md` section 5a — **primary C** (pre-limit unconstrained), **companion A** (no-limit full horizon), **defer B** (constrained parity).
- **provenance status**: **improved** — derived probes are written under `runs/diagnostics/...`; native replay runner now copies + hashes benchmark input and writes a manifest under a diagnostics dir.
- **native MATLAB replay status**: **parked** — MATLAB `-batch` returns code 1 with empty captured stdout/stderr; no new `Matlab_v2/outputs/mujoco_benchmark/parity_*` dir created; cause unknown.

## 3. Evidence-backed claims
| ID | Claim | Status | Evidence | Confidence | Next implication |
|---|---|---|---|---|---|
| A1 | relaxed bridge parity can pass | **unknown/pending** | Not established from the Lane A derived benchmark summaries alone; contract artifact path exists but not re-evaluated here | low | Do not use relaxed status for strict closure claims |
| A2 | strict native historical artifact fails | **supported** | Historical native parity CSV path in `Matlab_v2/outputs/mujoco_benchmark/parity_20260506_095912_814723/parity_timeseries.csv`; strict artifacts previously observed parity not ready | medium | Strict closure remains open; focus on bottlenecks |
| A3 | qdot2 event reproduces in current 500-step derived benchmark | **supported** | `runs/diagnostics/evidence_packets/lane_a_integrator_ablation_qdot2_event.md` (baseline values match historical window) | high | Event is real/reproducible; not a packaging artifact |
| A4 | MATLAB packaging is not source of qdot2 event | **supported** | qdot2 event reproduced via Python benchmark generator (derived path), independent of MATLAB run | medium | Focus on model/physics/contract, not MATLAB IO |
| A5 | RK4 reduces magnitude but does not eliminate spike/jerk failures | **supported** | `runs/diagnostics/evidence_packets/lane_a_integrator_ablation_qdot2_event.md` | high | Integrator alone insufficient |
| A6 | SysID improves RMSE but not qdot2 event | **supported** | `runs/diagnostics/evidence_packets/lane_a_sysid_parameter_replay.md` | high | Parameter fit helps global error but not MuJoCo-side transient |
| A7 | damping is causal/sensitive but no tested damping scale beats baseline overall | **supported** | `runs/diagnostics/evidence_packets/lane_a_damping_sweep.md` and `lane_a_damping_off_probe.md` | high | Damping affects local transient; simple scaling does not solve whole-run mismatch |
| A8 | COM-frame inertia substitution does not improve alignment | **supported** | Derived COM-inertia probe (`runs/diagnostics/parity_com_inertia_probe/*`) worsened RMSE; local qdot2 unchanged | high | Inertia fix via naive COM Iy swap is not sufficient |
| A9 | native MATLAB replay is parked due MATLAB batch failure with empty stdout/stderr | **supported** | `runs/diagnostics/native_strict_replay_provenance/native_matlab_parity_manifest.json` + empty `matlab_stdout.txt`/`matlab_stderr.txt` | high | Do not spend cycles debugging unless explicitly resumed |
| A10 | joint-limit hypothesis: MuJoCo shoulder limits drive qdot2 spike/jerk event | **supported** | `runs/diagnostics/evidence_packets/lane_a_joint_limit_ablation.md` + `lane_a_mujoco_force_decomposition_event_states.md` + ablation CSV/summary under `runs/diagnostics/parity_joint_limit_ablation/` | high | Split Lane A into unconstrained vs limit-contact parity; do not treat spike as unexplained physics |
| A11 | pre-limit window separates spike/jerk from ODE RMSE; relaxed max-dev gate passes; strict RMSE **fails** under **default** `bridge_gravity_sign` on window | **supported** | `runs/diagnostics/evidence_packets/lane_a_prelimit_metrics_probe.md` + `runs/diagnostics/parity_prelimit_metrics/prelimit_metrics.json` | high | Adopt **C** for reporting; label gravity-sign mode; **strict** pre-limit closure with **`mujoco`** sign is **A12**, not A11 |
| A12 | under contract C, `bridge_gravity_sign=mujoco` closes pre-limit strict swing-style gate on derived passive 500-step run | **supported** | `runs/diagnostics/evidence_packets/lane_a_prelimit_gravity_sign_trajectory_probe.md` + `runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json` | high | Label all **C** KPIs with gravity-sign mode; do not imply full-horizon D closure |

## 4. Branch status
| Branch | Status | Why | Resume condition |
|---|---|---|---|
| native MATLAB replay | **parked** | MATLAB batch returns code 1; stdout/stderr empty; no parity output dir created | User explicitly resumes debugging MATLAB runner/environment |
| integrator | **parked (insufficient)** | RK4 reduces magnitude only; spike/jerk failures persist | Resume only if combined with other changes (contract/physics) |
| SysID parameters | **parked (partial win)** | RMSE improves but qdot2 event unchanged; gate still false | Resume when strict/native replay is working or as part of contract rewrite |
| damping | **parked (tradeoff found)** | Strong local transient effect but no sweep scale improves whole-run vs baseline | Resume only if paired with analytical damping model or other contract changes |
| COM inertia | **parked (negative result)** | COM Iy substitution worsened RMSE; no local change | Resume only with better inertia mapping evidence |
| gravity / coordinate convention | **supported for contract C trajectory** | Static `qacc` + M2 local states + **M1** pre-limit trajectory: `--bridge-gravity-sign mujoco` materially improves pre-limit RMSE and **closes pre-limit strict gate** on derived passive benchmark | Default bridge sign remains until governance approves flip; full-horizon D still fails on spikes |
| actuator/control convention | **parked** | Inspection suggests joint order, torque order, torque sign, gear/scaling, and control timing are aligned; saturation caveat is not implicated in passive tau=0 baseline | Reopen only if future nonzero-torque probes show saturation or applied-vs-commanded torque divergence |
| broader model contract | **superseded (narrowed)** | Prior “broad model-contract mismatch” framing replaced by joint-limit hypothesis; **C** trajectory RMSE aligns with **`bridge_gravity_sign=mujoco`** (M1); **default** harness sign unchanged | Revisit only if joint-limit hypothesis is weakened by new evidence |
| joint-limit qdot2 spike/jerk (diagnostic) | **explained / closed for cause** | In-memory `--mujoco-joint-limits disabled` removes local and whole-run spike/jerk counters; baseline retained for XML-true physics | Further work is **contract choice**, not blind spike hunting |
| pre-limit metrics probe | **closed (initial scope)** | Derived CSV recompute `t<0.480`; artifacts in `parity_prelimit_metrics/` + evidence packet | Extend only if contract window or IC set changes |

## 5. Hypothesis status (joint limits)
**Status: supported**

MuJoCo **shoulder joint-limit constraint forces**, absent from the bridge/MATLAB analytical model, **dominate the qdot2 spike/jerk event** on the derived 500-step passive benchmark (step480/486 window).

**Evidence chain:**  
- Force decomposition: `runs/diagnostics/evidence_packets/lane_a_mujoco_force_decomposition_event_states.md`  
- Contract inspection: `runs/diagnostics/evidence_packets/lane_a_joint_limit_contract_inspection.md`  
- Ablation: `runs/diagnostics/evidence_packets/lane_a_joint_limit_ablation.md`  
- Pre-limit metrics: `runs/diagnostics/evidence_packets/lane_a_prelimit_metrics_probe.md`
- Pre-limit RMSE closure tranche (M4/M3/M2): `runs/diagnostics/evidence_packets/lane_a_prelimit_rmse_closure_tranche_m4_m3_m2.md`
- Pre-limit gravity-sign trajectory (M1): `runs/diagnostics/evidence_packets/lane_a_prelimit_gravity_sign_trajectory_probe.md`

**Gravity sign:** for **contract C** passive swing, **`bridge_gravity_sign=mujoco`** is now **evidence-backed** for trajectory RMSE and **pre-limit strict** closure; **limit-contact** spike/jerk remains a **joint-limit / D** issue, not fixed by bridge sign alone.

**Lane A split (decision impact):** treat **unconstrained dynamics parity** (smooth ODE / RMSE / conventions) separately from **constrained / limit-contact parity** (limits mirrored, no-limit diagnostic lane, or explicit exclusion from strict agreement).

**Prior branches:** remain **parked** for spike **cause**; integrator, SysID, damping sweep, COM inertia, actuator/control, native replay unchanged unless contract brief reopens them.

## 5b. qdot2 spike/jerk event (operational meaning)
The historical **qdot2 spike/jerk gate failure** on the XML-limited MuJoCo trajectory is **explained** as **constrained MuJoCo vs unconstrained analytical bridge** in the same harness. It is **not** evidence of an unconstrained dynamics bug by itself. **Whole-run RMSE mismatch remains open.**

## 5c. Remaining open scientific question (post M1 trajectory probe)
Under **contract C** with **`bridge_gravity_sign=mujoco`**, **pre-limit strict swing-style gate passes** on the derived passive 500-step run—**gravity-sign trajectory mismatch is not the remaining blocker for C**. **Still open:** (1) **full-horizon D** strict parity under XML limits (joint contact + spikes); (2) **local qacc** parity under **M** / **damping** differences (M3); (3) **default** harness gravity sign vs thesis narrative; (4) **native MATLAB** replay when un-parked.

## 6. Current stop rules
- no threshold changes
- no canonical output writes
- no full parity runs
- no new wrappers/tools
- no broad SysID loop
- no more inertia probes unless new evidence appears
- no native MATLAB replay debugging unless explicitly resumed

## 7. Recommended next action
**Markdown-first reporting (no dashboard code yet):** execute **`docs/research/LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md` §6** — add a short **Lane A reporting note** under `docs/research/` linking contracts **C/A/D/B**, provenance fields, and derived artifacts (`prelimit_compare.json`, gravity-sign trajectory packet). **Dashboard / canonical JSON changes** only after explicit approval per plan §7.

## 8. Permission packet for next action
Allowed:
- read/write research markdown under `docs/research/` and evidence under `runs/diagnostics/evidence_packets/`
- read derived diagnostics CSV/JSON; approved small probes written **only** under `runs/diagnostics/...`
Forbidden:
- simulation/XML/code/threshold edits unless a separate approval covers that scope; canonical `systematic_studies/outputs/` writes; parity_smoke/full; native MATLAB parity; skill edits
Approval required:
- any change to swing benchmark code, dashboard JSON contract paths (`docs/REPO_LAYOUT.md` section 7), threshold defaults, or new canonical outputs

