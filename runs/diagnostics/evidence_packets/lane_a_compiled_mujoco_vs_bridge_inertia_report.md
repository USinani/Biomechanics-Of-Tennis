# Lane A Compiled MuJoCo vs Bridge Inertia Report

## 1. Question
Are bridge scalar inertias semantically equivalent to compiled MuJoCo inertias?

## 2. Source files and model fields inspected
- `example_two_link/two_link_arm.xml`
- `example_two_link/matlab_v2_params.py`
- `example_two_link/matlab_v2_dynamics.py`
- `Matlab_v2/default_params.m`
- `Matlab_v2/dynamics/two_link_dynamics.m`
- `runs/diagnostics/evidence_packets/lane_a_parameter_equivalence_report.md`
- `runs/diagnostics/evidence_packets/lane_a_damping_sweep.md`

Compiled MuJoCo model fields (loaded from `example_two_link/two_link_arm.xml`):
- `model.body_mass`
- `model.body_ipos`
- `model.body_inertia`
- joint hinge axis assumption: XML uses `axis="0 1 0"` for both joints (rotation about Y)

## 3. MuJoCo compiled inertial data
Moving bodies:

- **shoulder**
  - mass: **1.0687698207512477**
  - body_ipos (inertial frame position / COM proxy in body frame): **[0.16, 0.0, 0.0]**
  - body_inertia diagonal: **[0.011830886075041958, 0.011830886075041958, 0.000470258721130549]**
  - candidate planar inertia axis (hinge about Y): use **Iy = 0.011830886075041958** as a candidate COM-frame planar inertia

- **elbow**
  - mass: **0.6047565858160354**
  - body_ipos: **[0.13, 0.0, 0.0]**
  - body_inertia diagonal: **[0.004449513760726305, 0.004449513760726305, 0.00018469128686143127]**
  - candidate planar inertia axis (hinge about Y): use **Iy = 0.004449513760726305** as a candidate COM-frame planar inertia

## 4. Bridge parameter extraction logic
From `example_two_link/matlab_v2_params.py::params_from_mujoco_xml()`:
- **mass**: `_capsule_mass(length, radius, density)` using cylinder + two hemispheres volume.
- **COM**: fixed at half-length (`lc = 0.5 * l`).
- **I1/I2**:
  - `_rod_inertia_about_base(mass, length) = (1/3) * mass * length^2`
  - This is the standard slender-rod inertia **about one end** (proximal joint), not about COM.
- **parallel-axis theorem**: not explicitly applied (the bridge directly returns the base/about-one-end proxy).

Bridge-from-XML scalar inertias (computed by `params_from_mujoco_xml(two_link_arm.xml)`):
- `I1 = 0.03648067654830925`
- `I2 = 0.01362718173372133`

## 5. Candidate inertia comparison
Assumption for mapping: both joints are hinges about Y (`axis="0 1 0"`), so the relevant planar inertia is about Y.

For each link we report:
- MuJoCo diagonal inertias (Ix, Iy, Iz) (about the body inertial frame / COM proxy)
- Candidate planar COM inertia: **Iy**
- Candidate proximal-joint planar inertia (parallel-axis): \(I_{joint,y} \approx I_{com,y} + m \cdot lc^2\), where `lc` is taken from `body_ipos.x`
- Bridge scalar inertia and its formula intent (“about base” rod proxy)

| Link | Quantity | Value | Interpretation |
|---|---:|---|
| shoulder | MuJoCo body_inertia diag | [0.011830886075041958, 0.011830886075041958, 0.000470258721130549] | Compiled 3D diagonal inertia; candidate planar axis is Y |
| shoulder | MuJoCo candidate planar inertia about COM (Iy) | 0.011830886075041958 | Candidate COM-frame planar inertia about hinge axis |
| shoulder | MuJoCo candidate planar inertia about proximal joint (Iy + m*lc^2) | 0.0391913934862739 | Using m=1.0687698207512477, lc=0.16 |
| shoulder | Bridge `I1` | 0.03648067654830925 | Computed as (1/3)*m*l^2 (about one end) |
| elbow | MuJoCo body_inertia diag | [0.004449513760726305, 0.004449513760726305, 0.00018469128686143127] | Compiled 3D diagonal inertia; candidate planar axis is Y |
| elbow | MuJoCo candidate planar inertia about COM (Iy) | 0.004449513760726305 | Candidate COM-frame planar inertia about hinge axis |
| elbow | MuJoCo candidate planar inertia about proximal joint (Iy + m*lc^2) | 0.014669900061017304 | Using m=0.6047565858160354, lc=0.13 |
| elbow | Bridge `I2` | 0.01362718173372133 | Computed as (1/3)*m*l^2 (about one end) |

## 6. Semantic match assessment
**bridge inertia matches MuJoCo proximal-joint inertia**

Evidence:
- Bridge inertias are computed as a rod **about one end**.
- The MuJoCo-derived “proximal joint” candidate \(I_{com,y} + m lc^2\) is numerically close to bridge scalars for both links:
  - shoulder: bridge 0.03648 vs MuJoCo candidate 0.03919
  - elbow: bridge 0.01363 vs MuJoCo candidate 0.01467
This suggests the bridge scalar inertia is intended to approximate a proximal-joint inertia, not COM inertia, and is not expected to match MuJoCo’s COM-frame Iy directly.

## 7. Research implication
- The analytical bridge inertia scalars (`I1`, `I2`) are **not** directly comparable to MuJoCo’s compiled diagonal inertias unless the intended reference point is matched (COM vs proximal joint) and the hinge axis is respected.
- If parity comparisons implicitly treat `I1/I2` as COM inertias (or otherwise mismatch the reference), passive dynamics can diverge even under identical torques.
- For the qdot2 event investigation: the damping experiments show local transients are sensitive to damping, but the remaining whole-run mismatch may still be dominated by **inertia semantics / mapping**, i.e., whether the analytical model’s mass matrix matches the compiled MuJoCo system in the same coordinate conventions.

## 8. Next smallest safe action
**plan bridge inertia correction from compiled MuJoCo inertials**

(Plan only: establish a consistent mapping from compiled MuJoCo inertial quantities to the analytical parameterization and then test it via derived-path probes, without editing canonical outputs.)

