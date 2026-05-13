# Lane A Gravity Convention Check

## 1. Question
Are analytical gravity torques consistent with the MuJoCo q=0 horizontal-link convention?

## 2. Sources inspected
- `docs/research/LANE_A_DECISION_BOARD.md`
- `example_two_link/two_link_arm.xml`
- `example_two_link/matlab_v2_params.py`
- `example_two_link/matlab_v2_dynamics.py`
- `Matlab_v2/dynamics/gravity_terms.m`
- `runs/diagnostics/evidence_packets/lane_a_parameter_equivalence_report.md`

## 3. Parameter set used
Using bridge from_xml parameters derived from `example_two_link/two_link_arm.xml` via `params_from_mujoco_xml()`:
- l1=0.32, l2=0.26
- m1=1.0687698207512475, m2=0.6047565858160353
- lc1=0.16, lc2=0.13
- g=9.81

## 4. Gravity torque table
Analytical gravity vector uses the form (Python + MATLAB match):
- \(G_1 = (m_1 lc_1 + m_2 l_1) g \cos(q_1) + m_2 lc_2 g \cos(q_1 + q_2)\)
- \(G_2 = m_2 lc_2 g \cos(q_1 + q_2)\)

Numerical values (N·m):

| q1 | q2 | G1 | G2 | Expected qualitative behavior |
|---|---|---:|---:|---|
| 0 | 0 | 4.347239 | 0.771246 | q=0 is horizontal (+X); gravity torque magnitude should be maximal (nonzero) |
| pi/2 | 0 | ~0 | ~0 | link vertical; gravity torque about hinge should be near zero |
| -pi/2 | 0 | ~0 | ~0 | link vertical; gravity torque about hinge should be near zero |
| 0 | pi/2 | 3.575993 | ~0 | second link folded; elbow gravity torque near zero when forearm vertical relative to gravity |
| 0 | -pi/2 | 3.575993 | ~0 | same magnitude as +pi/2 due to cosine symmetry |

## 5. Interpretation
**gravity convention appears consistent**

## 6. Implication for active hypothesis
Gravity convention mismatch is **less likely** to be the primary remaining driver of parity gap, based on this static check; it can be **parked as “not-evidently-wrong”**, though not fully proven for all conventions/frames.

## 7. Next smallest safe action
**inspect model formulation / mass matrix equivalence**

