# Matlab_v2/three_d — 3D forward-swing module

Phase-0 kinematic forehand swing in 3D, with a tennis-ball impact and a
ready-to-stream Unity hand-off. The default DOF mode is the project's
canonical two-link planar arm; a full 5-DOF anthropomorphic forehand is
available behind a single flag.

The complete Unity-side specification (file format, axis flip, C# struct,
UDP packet) lives in [`docs/UNITY_INTEGRATION.md`](../../docs/UNITY_INTEGRATION.md).

---

## Quick start

```matlab
% From Matlab_v2/
addpath('three_d');                        % once per session

% Default: two-link planar, plot ON, no UDP stream
res = run_3d_forward_swing();

% Full 5-DOF anthropomorphic forehand
res = run_3d_forward_swing('dof_mode', 'five_dof_full');

% Two-link + push the swing over UDP at 100 Hz to 127.0.0.1:55001
res = run_3d_forward_swing('stream', true);

% Smoke-test the whole pipeline (run from Matlab_v2/)
test_three_d
```

After every run the driver prints the contact velocity and the output
folder, e.g.:

```
[run_3d_forward_swing] dof_mode=two_link_planar | 151 frames @ 100 Hz |
    racket_speed_at_contact=18.42 m/s | peak=22.11 m/s
[run_3d_forward_swing] outputs:
    Matlab_v2/outputs/three_d_forward_swing/three_d_forward_swing_20260429_091833_812347
```

---

## Conventions (single source of truth)

| Aspect | Value |
|---|---|
| Coordinate frame | RHS, **Z-up** (X = forward toward net, Y = lateral, Z = up) |
| Length / time / mass | metres / seconds / kilograms |
| Angles | radians (keyframe table is in degrees and is converted internally) |
| Quaternion order | `[w, x, y, z]`, unit-norm |
| Unity-side mapping | applied on the Unity importer side per `unity_coords.m` |

The MATLAB → Unity axis flip is documented once in
[`export/unity_coords.m`](export/unity_coords.m) (`schema_meta` op). Every
exporter, the UDP streamer, and the test harness consume the same schema.

---

## File map

```
three_d/
├── default_params_3d.m              # canonical params (anthropometry, swing
│                                     #   keyframes, ball, Unity FPS, UDP knobs)
├── run_3d_forward_swing.m           # top-level driver (this is the entry point)
├── plot_swing_3d.m                  # 4-panel summary figure
│
├── kinematics/
│   ├── fk_5dof_arm.m                # 5-DOF FK -> 8 named frames
│   ├── racket_pose_from_joints.m    # q -> racket head pose (pos, quat, normal)
│   ├── jacobian_5dof.m              # 3x5 finite-difference Jacobian
│   └── quat_utils.m                 # rotation / quaternion helpers
│
├── trajectories/
│   └── min_jerk_swing.m             # quintic min-jerk between keyframes
│
├── ball/
│   ├── ball_dynamics_3d.m           # gravity + drag + Magnus (ode45)
│   └── ball_racket_collision.m      # Cross-2014 impulse model (CoR + friction)
│
├── export/
│   ├── unity_coords.m               # 41-column CSV schema + axis-flip spec
│   ├── export_unity_swing_csv.m     # per-frame CSV writer
│   └── export_unity_swing_jsonl.m   # per-frame JSONL writer
│
└── streaming/
    └── stream_swing_udp.m           # JSONL replay over UDP at fixed FPS
```

The Python sanity-check listener for the UDP path lives at
[`tools/udp_swing_listener.py`](../../tools/udp_swing_listener.py).

---

## DOF modes

### `two_link_planar` (default)

- Active joints: `q1` shoulder pitch (about world Y), `q3` elbow flexion
  (about local Y of upper-arm).
- Locked: `q2` shoulder yaw, `q4` forearm pronation, `q5` wrist flexion
  (all set to 0 in every keyframe).
- Swing plane: world X-Z. Visually equivalent to the 2-DOF arm in
  `example_two_link/two_link_arm.xml` and the racket-figure-8 work in
  `systematic_studies/racket_trajectory.py`.
- Use this for parity-aligned demos.

### `five_dof_full`

- All five joints active. Keyframes in `default_params_3d.m` are tuned
  for a right-handed forehand (backswing → forward swing → contact at
  ~0.85 s → follow-through).
- Use this for visually richer demos and as a stepping stone to a
  closed-loop forehand later.

In both modes the per-frame schema is identical: locked DOFs simply
serialise as 0 in `q2_rad`, `q4_rad`, `q5_rad`. The Unity importer never
needs to know which mode produced the file.

---

## What the driver actually computes

```text
default_params_3d
        │
        ▼
min_jerk_swing(t)  ─────►  q(t), q̇(t), q̈(t), phase_id(t)
        │
        ▼
fk_5dof_arm(q)     ─────►  shoulder / elbow / wrist / racket frames
                            +  jacobian_5dof(q)·q̇ → racket head velocity
        │
        ▼
ball_dynamics_3d(0..t_contact)        ◄── incoming ball flight
        │
        ▼
ball_racket_collision(@t_contact)     ◄── single-frame impulse
        │
        ▼
ball_dynamics_3d(t_contact..t_end)    ◄── outgoing ball flight
        │
        ▼
resample to params.unity_fps  +  build per-frame struct
        │
        ▼
   states.csv  +  states.jsonl  +  schema.json  (+ swing_3d.png)
        │
        └─ (optional) stream_swing_udp →  udp://127.0.0.1:55001
```

---

## Output layout

Every run writes to:

```
Matlab_v2/outputs/<experiment_name>/<run_id>/
├── states.csv      # 41 columns, 1 header + N rows at unity_fps
├── states.jsonl    # 1 JSON object per frame, same payload
├── schema.json     # schema metadata + run-level summary
└── swing_3d.png    # 4-panel summary figure (if 'plot', true)
```

Defaults: `experiment_name = 'three_d_forward_swing'`,
`run_id = '<experiment>_YYYYMMDD_HHMMSS_<6-digit-rand>'` via
`utils/build_run_id.m`. `outputs/` is gitignored at the repo root, which
keeps regenerated CSVs out of version control.

`schema.json` carries the run-level summary so any consumer can sanity-
check the run without parsing every frame:

```json
{
  "frame_convention": "RHS_Z_up_internal_LHS_Y_up_for_unity",
  "angle_units": "radians",
  "length_units": "meters",
  "time_units": "seconds",
  "quat_order": "wxyz",
  "unity_axis_map": "pos: (x,y,z)_zup -> (x,z,y)_yup; quat (w,x,y,z)_zup -> (-w,x,z,y)_yup",
  "dof_mode": "two_link_planar",
  "run_id": "three_d_forward_swing_20260429_091833_812347",
  "dt_sim_s": 0.002,
  "unity_fps": 100,
  "t_end_s": 1.5,
  "contact_t_s": 0.85,
  "racket_speed_at_contact_mps": 18.42,
  "peak_racket_speed_mps": 22.11,
  "ball_v0":              [-22.0, 0.5, 1.5],
  "ball_v_post_impact":   [ 26.5,-1.1, 4.7],
  "ball_spin_post":       [...],
  "frame_count": 151,
  "columns": [ ... 41 entries ... ]
}
```

---

## Testing

```matlab
test_three_d        % runs both modes, asserts schema, contact, ball flip
```

The smoke test verifies:
1. CSV opens with the expected 41-column header.
2. CSV body rows == JSONL line count == reported frame count.
3. At least one frame has `contact_flag == 1`.
4. Racket speed at contact ≥ 50% of the peak.
5. Ball `vx` flips sign across the impact.
6. `schema.json` reports the requested `dof_mode`.
7. `five_dof_full` mode also runs and produces the three artefacts.

---

## Phase roadmap

| Phase | Status | What changes |
|---|---|---|
| **0 — Kinematic playback** | this module | min-jerk q(t); open-loop; CSV/JSONL/UDP for Unity |
| **1 — Closed-loop dynamics** | next (W19) | replace `min_jerk_swing` with PD-tracked torques on `Matlab_v2/dynamics/two_link_dynamics.m`; add RK4. Folds back into the parity gate. |
| **2 — MuJoCo behavioural parity** | following | port the same arm + ball + impact into `example_two_link/two_link_arm.xml`; same Unity export. First behavioural MATLAB-vs-MuJoCo comparison. |
| **3 — RL on the swing** | later | retarget `train_sac.py` at the 3D arm; reward = ball exit speed × accuracy. |

The Unity export contract (CSV/JSONL/UDP schema) is **stable across all
phases**. The Unity dev only writes the importer once.
