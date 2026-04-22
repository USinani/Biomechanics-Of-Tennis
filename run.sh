#!/bin/bash
# Run project scripts using the project's virtual environment.
# Usage: ./run.sh <script.py> [args...]
# Examples:
#   ./run.sh example_two_link/train_sac.py --steps 200000 --seed 0
#   ./run.sh example_two_link/eval.py --checkpoint example_two_link/checkpoints/sac_two_link_seed0 --export-trajectory
#   ./run.sh example_two_link/validate_matlab_v2_bridge.py --samples 50
#
# On macOS, viewer scripts (view_mujoco_arm.py, run_policy_in_mujoco_viewer.py)
# MUST use mjpython - the standard python command won't work for the MuJoCo GUI.

cd "$(dirname "$0")"
VENV="${VIRTUAL_ENV:-.venv}"
PYTHON="$VENV/bin/python"
MJPYTHON="$VENV/bin/mjpython"

if [[ ! -x "$PYTHON" ]]; then
  echo "Error: Virtual environment not found. Run:"
  echo "  python -m venv .venv && .venv/bin/pip install mujoco gymnasium stable-baselines3"
  exit 1
fi

# On macOS, use mjpython for scripts that launch the MuJoCo viewer
if [[ "$(uname)" == "Darwin" ]] && [[ -x "$MJPYTHON" ]]; then
  # Allow headless preflight checks for this viewer script.
  if [[ "$1" == "view_dummy_two_link_obj.py" ]] && [[ "$2" == "--check-only" ]]; then
    exec "$PYTHON" "$@"
  fi
  case "$1" in
    view_mujoco_arm.py|view_3d_two_link_model.py|view_dummy_two_link_obj.py|run_policy_in_mujoco_viewer.py|example_two_link/run_example.py|example_two_link/view.py|example_two_link/view_mesh.py|example_two_link/play_matlab_bridge.py|example_double_pendulum/run_example.py|example_double_pendulum/view_mesh.py|example_double_pendulum/free_swing.py|example_double_pendulum/forward_swing.py|example_double_pendulum/backward_swing.py|example_double_pendulum/muscle_control.py|systematic_studies/run_trunk_arm_demo.py|systematic_studies/visual_showcase.py|systematic_studies/view_swing_protocol.py|systematic_studies/sim_parameter_lab.py)
      exec "$MJPYTHON" "$@"
      ;;
  esac
fi

exec "$PYTHON" "$@"
