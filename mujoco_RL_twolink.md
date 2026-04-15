## MuJoCo Two-Link Arm RL Baseline

### 1. Overview and Motivation

This document describes a baseline reinforcement learning (RL) setup for controlling a simplified human arm modeled as a two-link planar manipulator in MuJoCo. The implementation is intended as a starting point for research on arm swing / racket-sport motions, motor control, and robust policy learning under physically plausible constraints.

The project combines:

- **Physics simulation**: A MuJoCo model (`mujoco_arm.xml`) of a two-link arm (upper arm + forearm) moving in the sagittal plane under gravity.
- **Custom RL environment**: A Gymnasium-compatible environment (`ArmSwingEnv` in `arm_env.py`) that wraps the MuJoCo model and exposes a continuous control task.
- **Learning algorithm**: Soft Actor–Critic (SAC) implemented via Stable-Baselines3, with training scripts in `train_sac.py` and `train_sac_quick.py`.

The primary task is to move the hand site of the arm towards a fixed spatial target while respecting realistic joint limits and torque bounds. The baseline objective is to achieve a final hand–target distance below **4 cm** after sufficient training.

---

### 2. MuJoCo Model: Two-Link Arm (`mujoco_arm.xml`)

#### 2.1 Coordinate System and Global Settings

The MuJoCo model is defined as:

- **Model name**: `two_link_arm`
- **Compiler settings**:
  - Angles specified in **degrees**.
  - `coordinate="local"` (local body frames for joint coordinates).
- **Global options**:
  - Timestep: **0.001 s** (1 kHz simulation step).
  - Gravity: \( (0, 0, -9.81)\,\mathrm{m/s^2} \).

These settings provide a high-fidelity simulation with a small integration step, suitable for stiff dynamics and high control rates if needed.

#### 2.2 Default Material and Joint Properties

Defaults applied to joints and geoms:

- **Joints**:
  - Damping: `0.05` (dimensionless MuJoCo damping coefficient).
  - `limited="true"` so that joint ranges are enforced.
- **Geometries**:
  - Type: `capsule` (cylindrical segments for links).
  - Color: light gray RGBA `0.7 0.7 0.7 1`.
  - Density: `1200` kg/m³ (overridden by per-geom density in links).
  - Friction: `0.8 0.1 0.1` (tangential/sliding, torsional, rolling).

#### 2.3 Kinematic Structure

The arm is attached to the world via a shoulder body:

- **Shoulder body**:
  - Position: `(0, 0, 1.4)` m (approximately shoulder height above ground).
  - Joint `shoulder_pitch`:
    - Type: `hinge`
    - Axis: `(0, 1, 0)` (pitch in the sagittal plane).
    - Range: **−120° to +120°**.
  - Upper arm geom `upperarm`:
    - From: `(0, 0, 0)` to `(0.32, 0, 0)` m.
    - Length: **0.32 m**.
    - Radius: `0.03` m.
    - Density: `1050` kg/m³ (approximate soft-tissue density).

- **Elbow body**:
  - Position relative to shoulder: `(0.32, 0, 0)` m (end of upper arm).
  - Joint `elbow_pitch`:
    - Type: `hinge`
    - Axis: `(0, 1, 0)` (pitch).
    - Range: **0° to 150°** (flexion/extension).
  - Forearm geom `forearm`:
    - From: `(0, 0, 0)` to `(0.26, 0, 0)` m.
    - Length: **0.26 m**.
    - Radius: `0.025` m.
    - Density: `1050` kg/m³.

- **Sites**:
  - `hand` site:
    - Position: `(0.26, 0, 0)` relative to elbow body (end of forearm).
    - Size: `0.02` m (visual marker).
    - Color: blue `0.2 0.2 1 1`.
  - `target` site:
    - World position: `(0.50, 0.10, 1.20)` m.
    - Size: `0.02` m.
    - Color: red `1 0 0 1`.

**Assumption**: The anthropometric choices (link lengths, densities, shoulder height) approximate a mid-sized adult arm, but are not calibrated to a specific subject. For committee-level work, these can be justified via anthropometric tables or tuned to mocap-measured limb lengths.

#### 2.4 Actuators and Control Limits

The model uses simple torque motors at the two joints:

- `m_shoulder`:
  - Type: `motor`
  - Joint: `shoulder_pitch`
  - Control range: **−60 to +60** (interpreted as \( \pm 60 \,\mathrm{Nm} \)).
  - `ctrllimited="true"` and `gear="1"`.

- `m_elbow`:
  - Type: `motor`
  - Joint: `elbow_pitch`
  - Same control range: **−60 to +60**.

These limits are intended to be compatible with typical peak shoulder and elbow torques in athletic movements, while still leaving room for future safety constraints (e.g., enforcing <55 Nm at shoulder and <50 Nm at elbow as part of validation).

---

### 3. Custom RL Environment (`arm_env.py`)

#### 3.1 Environment Class and Simulation Rates

The environment `ArmSwingEnv` subclasses `gym.Env` (Gymnasium API) and directly embeds MuJoCo:

- **Model loading**:
  - Uses `mujoco.MjModel.from_xml_path("mujoco_arm.xml")`.
  - Data: `mujoco.MjData(self.model)`.
- **Rates**:
  - Simulation rate: `sim_rate = 500` Hz.
  - Control rate: `ctrl_rate = 50` Hz.
  - Each call to `step()` performs `substeps = sim_rate // ctrl_rate = 10` low-level MuJoCo steps.
- **Episode length**:
  - `max_steps = int(2.0 * ctrl_rate)` → **100 control steps** per episode.
  - At 50 Hz, this corresponds to **2 seconds** of simulated time.

This separation ensures numerically stable integration (500 Hz) while keeping the decision/control frequency at a more realistic 50 Hz, which is common in motor-control and robotics settings.

#### 3.2 Observation Space

The environment exposes a continuous observation vector constructed in `_obs()`:

- **Components**:
  - `sin(q1), sin(q2)` (2 values)
  - `cos(q1), cos(q2)` (2 values)
  - Joint velocities `q̇1, q̇2` (2 values)
  - Hand Cartesian position \( \mathbf{x}_\text{hand} \in \mathbb{R}^3 \)
  - Target Cartesian position \( \mathbf{x}_\text{target} \in \mathbb{R}^3 \)
  - Delta \( \mathbf{\Delta} = \mathbf{x}_\text{target} - \mathbf{x}_\text{hand} \in \mathbb{R}^3 \)

Total observation dimension:

\[
2 (\sin q) + 2 (\cos q) + 2 (q̇) + 3 (\text{hand}) + 3 (\text{target}) + 3 (\Delta) = 15.
\]

In code:

- Observation space: `Box(-inf, inf, shape=(15,), dtype=float32)`.

**Assumptions and rationale**:

- Using `sin` and `cos` encodings avoids discontinuities at \( \pm \pi \), which is beneficial for function approximators.
- Exposing both hand and target positions (and their difference) makes it easy for the policy to reason about absolute and relative geometry.

#### 3.3 Action Space

The action space is a 2D torque command:

- `Box(low=-60.0, high=60.0, shape=(2,), dtype=float32)`.
- `action[0]`: shoulder torque.
- `action[1]`: elbow torque.

Actions are clipped to this range before being applied, aligning with the actuator `ctrlrange` in the MuJoCo model.

#### 3.4 Reset Logic

On `reset()`:

- MuJoCo data is reset via `mujoco.mj_resetData`.
- Initial joint positions:
  - `q1 ∈ [-0.2, 0.2]` rad
  - `q2 ∈ [0.3, 1.0]` rad
- Initial velocities: `q̇1 = q̇2 = 0`.
- `mujoco.mj_forward` is called to update kinematics.
- Step counter is set to zero.

This produces a modestly perturbed initial pose around a flexed elbow configuration, ensuring variability while staying in a physically reasonable region of the workspace.

#### 3.5 Step Function and Dynamics Integration

For each call to `step(action)`:

1. **Action clipping** to the action space bounds.
2. **Substepping**:
   - For each of 10 substeps:
     - `self.data.ctrl[:2] = action`
     - `mujoco.mj_step(self.model, self.data)`
3. **Observation reconstruction** via `_obs()`.
4. **Hand and target kinematics** extracted from the observation (positions) and from `MjData` (velocity).

This pattern ensures that the RL agent operates at 50 Hz, while the underlying physics are integrated at 500 Hz.

#### 3.6 Reward Function (PDF-aligned)

The scalar reward now follows the guidance from the MuJoCo/Unity crossover PDF and is built from:

1. **Task-space distance term**:
   - \( r_\text{dist} = -w_\text{dist} \cdot \|\mathbf{\Delta}\|_2 \), with `w_dist=2.0` by default.
   - Encourages the hand to approach the target in Cartesian space.

2. **Velocity-toward-target term**:
   - Hand linear velocity \( \mathbf{v}_\text{hand} \) is obtained (when available) from `data.site_xvelp[hand_site]`.
   - Unit direction from hand to target: \( \hat{\mathbf{d}} = -\mathbf{\Delta} / \|\mathbf{\Delta}\| \) (if the distance is non-zero).
   - Projection: \( \text{toward} = \mathbf{v}_\text{hand} \cdot \hat{\mathbf{d}} \).
   - Term: \( r_\text{toward} = w_\text{toward} \cdot \text{toward} \), with `w_toward=0.5`.

3. **Control effort penalty**:
   - Quadratic torque cost:
   - \( r_\text{effort} = -w_\tau \sum_i a_i^2 \), with `w_effort=1e-3`.
   - Regularizes control effort as suggested in the PDF.

4. **Action smoothness penalty**:
   - Penalizes rapid changes in torque:
   - \( r_\text{smooth} = -w_{\Delta\tau} \sum_i (a_i(t) - a_i(t-1))^2 \), with `w_smooth=1e-3`.

5. **Joint speed penalty (hinged)**:
   - Uses a soft threshold on angular velocities:
   - \( r_\text{speed} = -w_{\dot q} \sum_i \max(0, |\dot q_i| - \dot q_{i,\text{soft}})^2 \).
   - Disabled by default (`w_speed=0.0`) but wired for experimentation.

6. **Barrier-style joint limit penalty**:
   - Adds a margin inside each joint limit (`joint_margin ≈ 5°`) and penalizes approaching the hard range:
   - \( r_\text{limit} = -w_\text{limit} \sum_i \big[\max(0, q_i - (q_{i,\max} - m))^2 + \max(0, (q_{i,\min} + m) - q_i)^2\big] \),
   - with `w_limit=0.05`.

7. **Optional terminal success bonus**:
   - If the hand stays within `eps_success` (default 4 cm) of the target for `n_hold_success` consecutive steps, an optional lump-sum `terminal_bonus` can be added to the reward and (optionally) terminate the episode early.

All weights and thresholds are configurable via the `ArmSwingEnv` constructor so that shaping can be tuned without code changes.

#### 3.7 Episode Termination, Safety, and Info

- **Termination**:
  - Time horizon: `truncated = (steps >= max_steps)` as before.
  - Optional success termination: when the reach-and-hold condition is met and `end_on_success=True`.
  - Catastrophic safety termination:
    - `terminated = True` if joint speeds exceed a hard threshold or torques exceed `torque_hard_limit`.
    - Episodes also terminate if non-finite values (NaNs/Infs) appear in the observation.

- **Info dictionary** now includes:
  - `"dist"`: current hand–target distance.
  - `"hand_speed"`: norm of the estimated hand linear velocity.
  - Reward components: `"r_dist"`, `"r_toward"`, `"r_effort"`, `"r_smooth"`, `"r_speed"`, `"r_limit"`, `"r_terminal"`.
  - Kinematic/limit diagnostics: `"q"`, `"qd"`, `"action"`, `"upper_violation"`, `"lower_violation"`, `"max_speed"`, `"max_torque"`.
  - Safety flags: `"success_steps"`, `"safety_terminated"`, `"safety_reason"`.

These fields make it straightforward to reproduce the PDF’s recommended reward unit tests and debugging workflow.

---

### 4. RL Training Setup

#### 4.1 Training Scripts

Two training scripts are provided:

- `train_sac.py`: main training run for the SAC agent.
- `train_sac_quick.py`: shorter smoke-test run to verify integration and observe early learning trends.

Both scripts:

- Import `ArmSwingEnv` from `arm_env.py`.
- Create a single environment instance (no parallelism).
- Train an SAC agent implemented in Stable-Baselines3.
- Perform a short evaluation rollout with the learned policy.

#### 4.2 Algorithm Choice: Soft Actor–Critic (SAC)

SAC is chosen for this baseline because:

- It handles **continuous action spaces** natively.
- It is **off-policy**, making sample usage efficient.
- Maximum-entropy objective encourages **exploration** and robust control policies.

In code:

- `SAC("MlpPolicy", env=env, verbose=1, ...)` in `train_sac.py`.

#### 4.3 Hyperparameters (train_sac.py)

Key hyperparameters configured in `train_sac.py`:

- Policy: `"MlpPolicy"` (default multilayer perceptron).
- Learning rate: `3e-4`.
- Replay buffer size: `200_000` transitions.
- Batch size: `256`.
- Discount factor: `gamma = 0.99`.
- Training frequency: `train_freq = 1` (update after every environment step).
- Gradient steps per update: `gradient_steps = 1`.
- Polyak averaging coefficient: `tau = 0.02`.
- Target entropy: `-2` (suitable for 2D action, roughly \(-|\mathcal{A}|\)).
- Total timesteps: `300_000` (main experiment).

These values follow common SAC defaults in continuous control benchmarks while leaving room for later tuning (e.g., larger replay buffer or different target entropy).

#### 4.4 Quick Training Script (train_sac_quick.py)

`train_sac_quick.py` now provides:

- A default short run:
  - `SAC("MlpPolicy", env=ArmSwingEnv(), verbose=1)` trained for `10_000` timesteps.
  - A 100-step evaluation rollout that prints a compact summary including final distance, episode reward, peak speeds/torques, and reward components.

- An optional **ablation ladder** (`--ablation` flag):
  - Sequential runs with different reward configurations:
    - Task-only distance/velocity term.
    - Task + torque penalty.
    - Task + torque + smoothness.
    - Full reward (including limit penalties).
  - Each setting trains briefly (~5k steps) and prints the same summary, making it easy to see which additional term destabilizes or helps learning.

#### 4.5 Evaluation Protocol

Both scripts use a simple evaluation:

- Reset the environment.
- For a fixed number of steps (e.g., 100):
  - Use `model.predict(obs, deterministic=True)` to select actions.
  - Step the environment and ignore stochastic exploration.
- Record or print the final distance from the `info["dist"]` field.

For more rigorous evaluation, future extensions could:

- Average performance over many random initial seeds.
- Track full time series of distance, torques, and joint speeds.
- Use separate validation episodes with randomized target positions.

---

### 5. Dependencies and Execution

#### 5.1 Software Stack

The current implementation assumes:

- **Python**: ≥ 3.10 (tested with 3.11.9).
- **MuJoCo**: `mujoco==3.1.4`.
- **Gymnasium**: continuous control API (e.g., `gymnasium==1.2.3`).
- **Stable-Baselines3**: deep RL algorithms (e.g., `stable-baselines3==2.7.1`).
- **NumPy**: numerical operations.
- **GLFW**: optional, for on-screen rendering (`pip install glfw`).

Example installation commands (in a virtual environment):

```bash
pip install mujoco==3.1.4 gymnasium stable-baselines3 numpy
pip install glfw  # optional, for rendering
```

For headless servers, MuJoCo can be configured with:

```bash
export MUJOCO_GL=egl
```

#### 5.2 Running Training

From the project root:

- **Quick test** (single configuration):

```bash
python train_sac_quick.py
```

- **Reward ablation ladder** (optional):

```bash
python train_sac_quick.py --ablation
```

- **Main training run with diagnostics**:

```bash
python train_sac.py
```

The main script now prints a summary of final performance and writes `eval_summary.csv` with reward components, distances, and safety metrics for downstream plotting.

---

### 6. Validation Strategy and Metrics

Although the baseline code focuses on training and simple evaluation, it is designed to support a richer validation pipeline suitable for a research project.

#### 6.1 Hand–Target Distance

Primary metric:

- **Final hand–target distance** at the end of an episode.
- Target specification:
  - Aim for **< 4 cm (0.04 m)** as a threshold for satisfactory control performance.

Implementation hooks:

- `info["dist"]` is already provided in the environment’s `step` method.
- Scripts such as `train_sac_quick.py` print this distance after evaluation.

#### 6.2 Torque Limits and Safety

Desired checks:

- Ensure **peak shoulder torque < 55 Nm**.
- Ensure **peak elbow torque < 50 Nm**.

Current code:

- Action space is clipped to ±60 Nm, and MuJoCo actuators share this range.
- The environment tracks `max_torque` and `max_speed` in `info`, and can terminate episodes when hard thresholds are exceeded.

These can be monitored via the printed summaries and `eval_summary.csv` to confirm that the learned policy stays within biomechanically reasonable envelopes.

#### 6.3 Joint Speeds

To compare against biomechanical literature (e.g., peak elbow extension speed in forehand strokes):

- Track joint angular velocities (`data.qvel[:2]`) during rollouts.
- Compute metrics such as:
  - Peak elbow extension speed.
  - RMS joint velocities over the episode.

These are not yet logged in the baseline code, but `qvel` is already part of the observation, making it straightforward to add logging.

#### 6.4 Gravity Drop Test

A standard physics sanity check:

- Set control inputs to **zero torques**.
- Release the arm from different initial configurations.
- Observe whether the resulting motion obeys expected energy behavior (e.g., no artificial energy injection).

This test can be implemented by:

- Running an evaluation loop with `action = [0.0, 0.0]`.
- Monitoring joint angles, velocities, and potential/kinetic energy over time.

#### 6.5 Domain Randomization and Generalization

To probe robustness:

- **Randomize target positions** within a bounded region around the nominal target.
- **Randomize inertial and friction parameters** slightly:
  - Link masses/densities.
  - Joint or geom friction coefficients.

Such randomization can be applied at reset time and will help assess whether the learned controller generalizes beyond a single nominal configuration.

---

### 7. Assumptions and Design Choices

This baseline embodies several pragmatic design decisions:

- **Two-link planar model**:
  - Focuses on sagittal-plane dynamics to reduce complexity while retaining key features of arm swing.
  - Assumes negligible out-of-plane motion and no wrist degrees of freedom.

- **Anthropometry**:
  - Link lengths (0.32 m, 0.26 m) and densities (≈1050 kg/m³) are chosen to be broadly human-like but are not subject-specific.
  - These parameters can be tuned later to match motion-capture data.

- **Control representation**:
  - Direct joint torques are used rather than muscle models or high-level kinematic targets.
  - This is appropriate for RL algorithm prototyping but abstracts away muscle-level constraints.

- **Reward shaping**:
  - Distance-based term dominates, with velocity-toward-target encouraging dynamic movement.
  - Torque and joint-limit penalties promote physically reasonable motions without fully enforcing strict safety limits.

- **Episode design**:
  - Fixed 2-second horizon; no early termination for success.
  - This simplifies learning at the cost of not explicitly rewarding “reach-fast-then-hold” behavior.

- **Algorithm choice**:
  - SAC is selected as a well-established off-policy RL algorithm for continuous control, enabling good sample efficiency and robust performance.

Each of these choices can be revisited as the project matures (e.g., adding 3D degrees of freedom, modeling a wrist and racket, or switching to more structured action spaces).

---

### 8. Extensions and Future Work

The current implementation provides a robust baseline upon which more sophisticated research can be built. Key directions include:

#### 8.1 Reference-Motion Imitation

If motion-capture (mocap) or high-fidelity reference trajectories are available:

- Add an imitation term to the reward:

  \[
  r_\text{imit} = -w \, \| q - q_\text{ref}(t) \|_2,
  \]

  where \( q_\text{ref}(t) \) is the reference joint configuration at time \( t \), and \( w \) is a weighting factor.

- Combine with the existing distance-based reward to balance target accuracy and biomechanical realism.

#### 8.2 Racket and Ball Modeling

To move towards realistic racket-sport simulations:

- Add a lightweight racket geom rigidly attached at the `hand` site.
- Configure soft contact parameters initially to avoid numerical instability.
- Once the arm controller is stable, introduce a ball model with:
  - Appropriate mass and size.
  - Elastic collision properties.
  - Environmental constraints (e.g., ground and net).

This progression reduces confounding factors by stabilizing the arm controller before adding complex contact interactions.

#### 8.3 Unity-Based Visualization and Tooling

The crossover PDF recommends using a **JSON → MJCF** pipeline as the source of truth for arm parameters, which also aligns well with Unity-based workflows.

- The current project provides:
  - `model_params.json`: a JSON file capturing link lengths, densities, joint limits, actuator ranges, and site positions for the two-link arm.
  - `generate_mjcf_from_json.py`: a Python utility that reads `model_params.json` and writes a MuJoCo MJCF file (default `mujoco_arm_from_json.xml`).
  - `make_arm_env_from_json(...)` in `arm_env.py`: a helper that generates MJCF from JSON (if needed) and constructs `ArmSwingEnv` with the generated file.

- Intended Unity workflow:
  - Unity (or another tool) exports a compatible `model_params.json` describing the arm.
  - Python uses `generate_mjcf_from_json.py` / `make_arm_env_from_json` to build an MJCF model and run RL training.
  - Resulting trajectories (states, actions, hand poses) can be logged and replayed in Unity for visualization.

Two integration patterns remain as before:

- **Online streaming**:
  - Run RL in Python with MuJoCo.
  - Stream joint states or hand poses to Unity via a simple TCP bridge.
  - Use Unity for real-time visualization or interactive experiments.

- **Offline replay**:
  - Log trajectories (states, actions) during training.
  - Export them to a file and replay them in Unity for analysis and presentation.

#### 8.4 Logging, Plotting, and Experiment Management

For research-grade evaluation:

- Log time series of:
  - Hand–target distance.
  - Joint torques and velocities.
  - Reward components.
- Plot:
  - Learning curves (episode reward vs. timesteps).
  - Final distance distributions over evaluation episodes.
  - Torque/speed envelopes relative to biomechanical limits.
- Integrate an experiment manager (e.g., Sacred, Weights & Biases) to track hyperparameters and results.

---

### 9. Summary

This project implements a clean, minimal RL baseline for a two-link human arm modeled in MuJoCo. The environment combines:

- A physically meaningful planar arm model with realistic joint limits and torque bounds.
- A carefully shaped reward that encourages both proximity to a target and motion in the correct direction, while penalizing excessive torque and joint-limit violations.
- A modern deep RL algorithm (SAC) with standard hyperparameters, providing a strong starting point for further research.

The current setup is sufficient to train policies that substantially reduce hand–target distance, and it is architected to support more advanced studies, including imitation of measured motions, contact-rich interactions with rackets and balls, and high-quality visualization in Unity. As such, it provides an appropriate foundation for a research project committee to evaluate, extend, and build upon.

