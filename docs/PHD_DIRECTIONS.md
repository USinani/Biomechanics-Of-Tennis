# PhD Directions for the Two-Link MuJoCo + MATLAB Parity Project

_Drafted 2026-04-22; extended 2026-04-22 with supervisor direction on
mutual motor learning and adaptive control. Living research-agenda
document, not a specification. Revise as the project matures._

## 0a. Supervisor direction: mutual motor learning and adaptive control (2026-04-22)

> "This investigation delineates the control boundaries of motor
> learning within paired interaction tasks, establishing a novel
> benchmark for the development of collaborative haptic systems and
> rehabilitative robotics. Rather than observing passive coordination,
> this project establishes a framework for optimizing skill acquisition
> through structured control handover." — supervisor, 2026-04-22.

The supervisor's reframing promotes a paired / shared-control paradigm
to the headline research question. The existing two-link arm + MATLAB
parity harness is then positioned as the _mechanical substrate_ on
which the following control-handover question is interrogated:

**Primary strategic objective.** Evaluate the efficacy of the
**Reinforced Turn-take (RT)** mode against the **Static (Equal-Control)**
mode in facilitating skill transfer and environmental adaptation when
two agents share control of the same mechanical plant under external
disturbance.

Concrete instantiation adopted for this repo:

- **Plant.** The existing `example_two_link/two_link_arm.xml` two-link
  planar arm (single source of truth; no MJCF fork needed).
- **Two agents.** Agent `A` and agent `B` each carry an internal
  reference trajectory `q_A^*(t)` and `q_B^*(t)`; differences between
  them model motor-command disagreement.
- **Coupling.** A virtual-spring PD controller per agent applies
  torque `tau_i(t) = K_i(t) * (q_i^*(t) - q(t)) - D_i(t) * qdot(t)`.
  Agents' torques are additive at the joint: `tau = tau_A + tau_B + w(t)`
  where `w(t)` is an exogenous disturbance.
- **Control-handover modes.**
  1. **Static:** `K_A = K_B = K_eq` constant; neither agent dominates.
  2. **Reinforced Turn-take (RT):** `K_A(t)` and `K_B(t)` oscillate in
     anti-phase at `f_rt` Hz, modulated by a sine-wave spring-length
     schedule:

     ```
     L_i(t) = L_0 + DeltaL * sin(2*pi*f_rt*t + phi_i)
     K_i(t) = K_ref * (L_0 / L_i(t))    # short spring => high stiffness
     ```

     with `phi_A = 0` and `phi_B = pi` so that dominance transfers
     back and forth each half-period. `dominance_A(t) = K_A(t) / (K_A(t) + K_B(t))`
     is the scalar metric of interest.

### Acceptance criteria for the RT-vs-Static benchmark

- A single command produces a comparable pair of runs:

  ```
  ./run.sh systematic_studies/mutual_motor_learning.py --mode static --perturb-mode impulse
  ./run.sh systematic_studies/mutual_motor_learning.py --mode rt     --perturb-mode impulse
  ```

- Both runs log joint state, per-agent reference, per-agent stiffness,
  dominance share, tracking errors, and the exogenous disturbance time
  series to `systematic_studies/outputs/`.
- A plot bundle shows stiffness-vs-time, dominance-vs-time, tracking
  error per agent, and joint trajectory vs. both references, for each
  mode. These populate Paper-4 figures below.

### Risks and supervisor asks

1. Confirm whether the two "agents" should eventually be instantiated
   as (i) two analytical PD controllers (current scope), (ii) one
   analytical + one SAC residual agent, or (iii) two SAC residual
   agents. The prototype supports (i) and trivially extends to (ii).
2. Confirm the disturbance protocol(s): impulse, sinusoid, or stochastic
   noise. A single default is chosen for the prototype; the supervisor
   should anchor the publishable protocol.
3. Agree on a skill-transfer metric. Default below is **normalised
   RMS tracking error on the second half of the episode**, but the
   learning-efficacy story may need a dedicated pre/post-perturbation
   delta.

### Linking to existing workstreams

- The parity gate (Section 2.1 below) **remains a hard prerequisite**:
  any claim comparing RT and Static hinges on a mechanically consistent
  plant. The SysID loop closes before any RT-vs-Static statistics are
  reported.
- The figure-8 / infinity trajectory is reused as a default reference
  for both agents so the same plant dynamics are exercised as in the
  2026-04-22 visualiser. Agent `B` uses a phase-shifted copy to
  engineer disagreement without changing task complexity.

### New mini-paper prospect (Paper 4)

> **Paper 4 (journal, strategic).**
> _Reinforced Turn-take vs equal-control handover: a simulated
> collaborative benchmark for two-agent skill transfer under
> disturbance._
>
> Depends on: closed strict parity gate; mutual-motor-learning
> prototype (`systematic_studies/mutual_motor_learning.py`); a
> formalised skill-transfer metric.

## 0. Positioning

The project so far has produced:

1. A validated SAC training pipeline for a planar two-link arm, with a
   hybrid residual controller on top of an analytical MATLAB prior.
2. A systematic-studies harness: reproducible sweeps, canonical unit
   contract, a timing-vs-velocity figure, and a swing-benchmark comparing
   MuJoCo against a Python port of MATLAB_v2 dynamics.
3. A racket / figure-8 end-effector visualiser (added 2026-04-22).

What the project has **not** yet delivered:

- A defensible "first result" (optimal elbow delay, peak racket speed)
  that passes strict MATLAB-vs-MuJoCo parity gates. Current parity
  passes only under relaxed thresholds
  (`rmse_q` ~ 2.5 rad, `rmse_qdot` ~ 13 rad/s).
- A sim-to-real or biomechanical validation story.

The directions below are structured to take the project from "mature
engineering artefact" to "PhD-thesis-grade scientific contribution".

## 1. Open scientific questions

1. **Is the "optimal elbow delay" a universal feature, or an artefact of
   a specific parameter set?**
   - Sweep across inertia ratios, damping, and torque amplitudes; check
     whether the timing-vs-velocity maximum shifts smoothly or jumps.
   - Frame this as: what is the Pareto frontier of
     `{timing, peak racket speed, energy, control effort}`?
2. **How much of SAC's policy is truly "learned" when the analytical
   prior is present?**
   - Measure information-theoretic divergence between the prior-only
     action and the prior+residual action during eval episodes.
   - Define a residual-ratio metric; study how it evolves over training.
3. **What is the MuJoCo-vs-MATLAB parity gap actually caused by?**
   - Integrator (implicitfast vs Euler vs RK4), parameter mismatch
     (damping, inertia), contact/friction model differences.
   - An ablation table (flip one axis at a time) would close this.
4. **Does the figure-8 / infinity warm-up motion correspond to an
   information-efficient exploration prior for a learned controller?**
   - Use the figure-8 trajectory as initial demonstrations for a
     residual policy; compare sample-efficiency against cold-start SAC.

## 2. Methodological improvements

1. **System identification loop (closes the strict parity gate).**
   - Fit `matlab_v2_params.py` (masses, lengths, damping, Coulomb friction)
     to MuJoCo rollouts via least-squares / gradient descent.
   - Expected outcome: `rmse_q` drops below the strict threshold, bridge
     and MuJoCo agree under the strict gate.
2. **Replace the Python bridge's first-order Euler integrator with RK4
   (or MuJoCo-native integration of the analytical model).**
   - Isolates integrator mismatch from parameter mismatch in the parity
     residual.
   - Deliverable: `matlab_v2_dynamics_rk4.py` with a flag-switchable
     integrator and a re-run of `compare_signals.py`.
3. **Sensitivity analysis on the physics parameters.**
   - Morris elementary-effects screening first, then Sobol indices on
     the survivors. Targets: shoulder/elbow damping, link masses and
     lengths, `ctrlrange`.
   - Deliverable: a ranked bar chart + a short methods note.
4. **Formal parity gate specification.**
   - Today we have both a strict and a relaxed gate; they disagree.
     Lock down the thresholds with a principled argument (e.g. sensor
     noise floor, discretisation error).
5. **Confidence intervals, not single-run metrics.**
   - Every number in the summaries should carry a (seed, CI) pair.

## 3. Novel directions

1. **Impedance-controlled residual.**
   - Replace the pure torque residual with a learned impedance
     parameterisation `(K_p, K_d)` around the analytical trajectory.
     Study robustness under perturbation (ball mass jitter, joint
     noise), which torque-only controllers cannot handle gracefully.
2. **Cross-subject / cross-morphology generalisation.**
   - Parameterise link mass and length per "virtual athlete";
     retrain or zero-shot evaluate SAC. Compare the shift in optimal
     elbow delay against biomechanics literature predictions.
3. **Perception-in-the-loop tennis warm-up.**
   - Extend the environment with a ball / target tracker (e.g. a
     synthetic 2D image observation). Train a policy that uses the
     figure-8 trajectory as a warm-up, then transitions to a hitting
     controller at ball arrival.
4. **Sim-to-real bridge.**
   - Specify the transfer gap concretely: servo bandwidth, sensor
     latency, static friction, gearhead backlash. Define the minimum
     changes to training setup (domain randomisation ranges, reward
     shaping) that would make the residual policy robust. Build a
     small physical 2-link testbed or partner with an existing lab.
5. **Neuromechanical interpretation.**
   - Connect the optimal timing to the kinetic-chain literature in
     sports biomechanics (baseball pitching, tennis strokes). Is the
     learned delay consistent with human data?

## 4. PhD-output framing

- **Paper 1 (conference, near-term, ~6 months).**
  _Hybrid analytical-residual control for a planar arm: validated
  MATLAB-vs-MuJoCo parity and a timing study._ Requires closing the
  strict parity gate and publishing the timing-vs-velocity result with
  confidence intervals.
- **Paper 2 (workshop or journal, mid-term).**
  _Sensitivity analysis and sim-identification for mechanically
  consistent RL environments._
- **Paper 3 (journal, long-term).**
  _Figure-8 warm-up as a structured exploration prior for residual
  policies_, ideally with a sim-to-real component.
- **Thesis chapters, tentative mapping.**
  1. Background + biomechanics of the figure-8 motion.
  2. Simulation pipeline (MuJoCo + MATLAB bridge + parity harness).
  3. Hybrid residual controller (SAC + analytical prior).
  4. Timing study on the two-link arm.
  5. Impedance and perception extensions.
  6. Sim-to-real.
  7. Discussion, limits, future work.

## 5. Reproducibility ethos

- All figures and metrics live in `systematic_studies/outputs/` and are
  regenerated by a single command.
- Every result reported has a `seed`, a `run_id`, and a pinned set of
  parameters. No per-run manual tuning.
- Artifact bundles (CSV + JSON + PNG + a one-line hash of the repo) are
  published alongside each report.
- The consolidated project update (`project_updates/2026-04-22_*.md`)
  is the single entry point for a fresh reader.

## 6. Methodological risks the supervisor should sign off on

1. **"MATLAB" currently means the Python port `matlab_v2_dynamics.py`**
   for most comparisons. The native MATLAB runner exists but is slower
   and harder to automate. Decide up-front which runs demand the native
   MATLAB output for publication and which can stay on the Python
   bridge.
2. **Strict vs relaxed parity gates** — relaxed gates are useful for
   iteration but cannot be the basis for a claim. Agree with the
   supervisor on the thresholds that will appear in the final paper.
3. **Reward shaping vs analytical prior trade-off.** The residual
   controller can in principle absorb missing physics into the learned
   residual rather than the reward. This conflates sim-fidelity with
   policy behaviour. Keep a clean ablation: prior-only, reward-only,
   hybrid.
4. **Morphology choice.** The planar 2-link arm is a pedagogical
   vehicle; any biomechanical claim will require a 3D arm + wrist
   model. Plan the transition early so the pipeline generalises.

## 7. Concrete next experiments (2-4 week horizon)

- Close the strict parity gate via SysID (Task 2.1).
- Run the timing-vs-velocity sweep under the closed gate with 10 seeds
  and CIs; only then declare a "first result".
- Extend `racket_trajectory.py` with a `--sweep` mode that runs a
  parameter sweep (e.g. over `f_hz`) and writes a tidy CSV suitable for
  a peak-speed-vs-frequency plot.
- Add sensitivity analysis (Task 2.3) as a dedicated study.
- **Mutual motor learning prototype (supervisor direction, Section 0a).**
  Ship `systematic_studies/mutual_motor_learning.py` with `--mode static`
  and `--mode rt`, plus a disturbance injector; generate a
  stiffness/dominance/tracking-error panel for each mode. First RT-vs-Static
  comparison does NOT yet support a publishable claim (parity gate blocking),
  but establishes the pipeline end-to-end.

## 8. Supervisor "asks"

- Sign-off on the strict parity thresholds that will anchor the
  timing-vs-velocity claim in Paper 1.
- Input on whether the sim-to-real transition should happen at the
  planar 2-link stage or after migrating to a 3D arm.
- Pointers to existing biomechanics datasets that could ground-truth
  the optimal-timing claim.
