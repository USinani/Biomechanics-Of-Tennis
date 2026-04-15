import argparse
import time

import mujoco
import mujoco.viewer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Double pendulum backward swing (toward -X) example.")
    p.add_argument(
        "--model",
        default="example_double_pendulum/free_swing.xml",
        help="Path to MJCF XML.",
    )
    p.add_argument(
        "--seconds",
        type=float,
        default=0.0,
        help="Max runtime in seconds. Use 0 to run until the viewer is closed.",
    )
    p.add_argument("--realtime", action="store_true", help="Sleep to approximate real-time.")
    p.add_argument("--headless", action="store_true", help="Run without opening viewer.")
    p.add_argument("--q1", type=float, default=0.2, help="Initial hinge1 angle (rad).")
    p.add_argument("--q2", type=float, default=-0.1, help="Initial hinge2 angle (rad).")
    p.add_argument(
        "--qd1",
        type=float,
        default=-2.0,
        help="Initial hinge1 velocity (rad/s). Negative tends to start motion toward -X.",
    )
    p.add_argument("--qd2", type=float, default=0.0, help="Initial hinge2 velocity (rad/s).")
    return p.parse_args()


def run_headless(model: mujoco.MjModel, data: mujoco.MjData, seconds: float) -> None:
    start = time.time()
    while time.time() - start < seconds:
        mujoco.mj_step(model, data)


def main() -> None:
    args = parse_args()
    model = mujoco.MjModel.from_xml_path(args.model)
    data = mujoco.MjData(model)

    if model.nq >= 2:
        data.qpos[0] = args.q1
        data.qpos[1] = args.q2
    if model.nv >= 2:
        data.qvel[0] = args.qd1
        data.qvel[1] = args.qd2

    if args.headless:
        run_headless(model, data, seconds=args.seconds if args.seconds > 0 else 0.5)
        return

    with mujoco.viewer.launch_passive(model, data) as viewer:
        if args.seconds <= 0:
            while viewer.is_running():
                mujoco.mj_step(model, data)
                viewer.sync()
                if args.realtime:
                    time.sleep(model.opt.timestep)
        else:
            start = time.time()
            while viewer.is_running() and time.time() - start < args.seconds:
                mujoco.mj_step(model, data)
                viewer.sync()
                if args.realtime:
                    time.sleep(model.opt.timestep)


if __name__ == "__main__":
    main()

