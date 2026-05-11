# Lane A Parameter Equivalence Report

## 1. Question
Are MuJoCo, bridge, MATLAB native, and SysID lanes using physically equivalent parameters?

## 2. Artifacts and source files inspected
- `example_two_link/two_link_arm.xml`
- `example_two_link/matlab_v2_params.py`
- `example_two_link/matlab_v2_dynamics.py`
- `Matlab_v2/default_params.m`
- `Matlab_v2/dynamics/two_link_dynamics.m`
- `Matlab_v2/dynamics/gravity_terms.m`
- `Matlab_v2/dynamics/coriolis_terms.m`
- `systematic_studies/swing_benchmark_mujoco_vs_bridge.py`
- `systematic_studies/outputs/sysid_bridge_params.json`
- `runs/diagnostics/evidence_packets/lane_a_integrator_ablation_qdot2_event.md`

## 3. Parameter sources
- **MuJoCo XML source**
  - `example_two_link/two_link_arm.xml` defines geometry (lengths via `geom fromto`), joint defaults (damping), gravity vector, timestep, integrator, and actuator torque limits.
  - It does **not** explicitly specify per-body `<inertial>` blocks; masses/inertias are therefore derived by MuJoCo from geoms/densities (inference is possible but not directly stated as scalar params).

- **Bridge from_xml source**
  - `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` defaults to `--param-source from_xml`, which calls `example_two_link/matlab_v2_params.py::params_from_mujoco_xml(args.xml)`.
  - That function computes an **approximate** two-link parameter set from XML geom lengths/radii/densities:
    - mass: capsule volume * density
    - inertia: slender rod proxy about base
    - COM: fixed at half-length (`lc = 0.5*l`)
    - gravity: magnitude taken from the XML option gravity vector (abs(z))

- **MATLAB default source**
  - `Matlab_v2/default_params.m` defines a canonical parameter struct (including dt, horizon, initial state, physics values, and damping vector).
  - `Matlab_v2/run_swing_sim.m` uses semi-implicit Euler integration by construction.
  - `Matlab_v2/dynamics/two_link_dynamics.m` optionally applies viscous damping via `tau = u - b.*qd` where `b = params.physics.damping_nm_s`.

- **SysID JSON source (optional)**
  - `systematic_studies/outputs/sysid_bridge_params.json` (schema `sysid_bridge_params.v1`) contains a fitted `{l1,l2,lc1,lc2,m1,m2,I1,I2,g}` parameter set.
  - It is used by the benchmark only if `--param-source from_json` is passed (the JSON is the default `--params-json` path).

## 4. Parameter comparison table
| Parameter | MuJoCo XML / inferred | Bridge from_xml | MATLAB default | SysID JSON | Notes |
|---|---|---|---|---|---|
| l1 | 0.32 (upperarm `fromto`) | 0.32 | 0.30 | 0.32 | MuJoCo length is explicit via geom. |
| l2 | 0.26 (forearm `fromto`) | 0.26 | 0.35 | 0.26 | MATLAB default differs from XML. |
| lc1 | not explicit in XML; implied by mass distribution | 0.16 (=0.5*l1) | 0.15 | 0.16 | Bridge uses fixed 0.5*l; MATLAB default differs. |
| lc2 | not explicit in XML; implied | 0.13 (=0.5*l2) | 0.20 | 0.13 | Same pattern. |
| m1 | not explicit scalar; derived from geom density+shape by MuJoCo | 1.0687698207512475 | 2.0 | 0.2137623825184281 | SysID masses differ strongly from bridge-from-XML approximation. |
| m2 | not explicit scalar; derived | 0.6047565858160353 | 1.5 | 0.21307882172639045 |  |
| I1 | not explicit scalar; derived | 0.03648067654830925 | 0.025 | 0.18239893602856921 | SysID inertia differs strongly from bridge-from-XML. |
| I2 | not explicit scalar; derived | 0.01362718173372133 | 0.045 | 0.0027255436838254997 |  |
| damping joint1 | 0.12 (default joint damping) | none in analytical bridge | 0 (via `damping_nm_s=[0;0]`) | n/a | MuJoCo has joint damping; analytical bridge has no damping term; MATLAB has damping term but defaults to 0. |
| damping joint2 | 0.12 | none | 0 | n/a | Same as above. |
| gravity | vector (0,0,-9.81) | g=9.81 (scalar) | g=9.81 (scalar) | g=9.81 (scalar) | Direction/convention is explicit only in MuJoCo; analytical lanes encode gravity as scalar in planar equations. |
| actuator/torque assumptions | 2 motors, ctrlrange ±60 Nm, gear=1 | direct torque input, no saturation | direct torque input; optional damping subtracts `b.*qd` | n/a | Saturation exists in MuJoCo; analytical lanes assume direct torque unless explicitly clipped elsewhere. |
| timestep/integrator | dt=0.001, integrator=implicitfast (XML) | bridge integrator method: semi-implicit Euler by default (separate from MuJoCo integrator) | dt=0.002 default, semi-implicit Euler | n/a | In parity benchmark scripts, MATLAB dt is set from CSV; bridge dt is set from MuJoCo model timestep. |

## 5. Equivalence assessment
- **MuJoCo vs bridge-from-XML**: **approximately equivalent** for geometric lengths and gravity magnitude; **mismatched/unknown** for inertias/masses because MuJoCo’s effective inertias are derived internally while bridge uses a simplified approximation, and MuJoCo includes joint damping that bridge omits.
- **MuJoCo vs MATLAB default**: **mismatched** (lengths, masses, inertias, damping defaults, dt).
- **Bridge-from-XML vs MATLAB default**: **mismatched** (same reasons as above).
- **SysID vs bridge-from-XML**: **mismatched** (masses/inertias differ substantially; lengths/COM match).
- **SysID vs MuJoCo**: **unknown/mismatched** (MuJoCo scalars not explicit; but sysID differs strongly from bridge-from-XML approximation which itself is meant to approximate the MuJoCo XML geometry).

## 6. Highest-risk mismatches
1. **Damping mismatch (MuJoCo has joint damping; bridge omits it; MATLAB defaults to 0 damping)** — likely to affect passive trajectories and especially velocity transients.
2. **Mass/inertia mismatch across lanes (bridge-from-XML approximation vs MATLAB defaults vs SysID fit)** — likely to dominate passive divergence even with identical torque schedules.
3. **Gravity/coordinate convention mismatch risk (MuJoCo uses explicit 3D gravity vector; analytical lanes encode planar gravity as scalar with implicit sign/axis conventions)** — potential sign/axis mismatch unless explicitly mapped.

## 7. What this proves
- The current parity-related lanes are **not guaranteed** to be comparing physically equivalent systems, because:
  - MuJoCo includes joint damping and implicit geometric inertia derivation, while the analytical bridge dynamics omits damping and uses a simplified inertia approximation.
  - MATLAB native defaults are a different parameter set unless explicitly overridden.
  - SysID parameters (when used) can materially change masses/inertias relative to the bridge-from-XML approximation.

## 8. What this does not prove
- It does **not** prove which mismatch is the primary bottleneck for strict parity closure.
- It does **not** prove that sysID parameters are “more correct” than XML-derived approximations (only that they differ).
- It does **not** prove a specific gravity-axis sign error; it only flags that conventions are implicit in analytical equations.

## 9. Next smallest safe experiment
**SysID parameter replay plan**

Rationale (safest/lowest surface-area test of physical equivalence without touching canonical outputs):
- Run the existing benchmark with `--param-source from_json` (uses `systematic_studies/outputs/sysid_bridge_params.json`) while keeping MuJoCo XML unchanged, writing outputs to a derived diagnostics path. This tests whether the fitted analytical parameters improve alignment without any code/XML edits or canonical output overwrites.

