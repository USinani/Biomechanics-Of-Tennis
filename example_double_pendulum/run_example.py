import argparse
import time

import mujoco
import mujoco.viewer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Double pendulum MuJoCo hello-world example.")
    p.add_argument(
        "--model",
        default="example_double_pendulum/double_pendulum.xml",
        help="Path to MJCF XML.",
    )
    p.add_argument(
        "--seconds",
        type=float,
        default=0.0,
        help="Max runtime in seconds. Use 0 to run until the viewer is closed.",
    )
    p.add_argument(
        "--realtime",
        action="store_true",
        help="Sleep to approximate real-time (based on model timestep).",
    )
    p.add_argument(
        "--headless",
        action="store_true",
        help="Compile and step without launching the viewer (useful for quick checks).",
    )
    p.add_argument("--q1", type=float, default=1.2, help="Initial hinge1 angle (rad).")
    p.add_argument("--q2", type=float, default=0.7, help="Initial hinge2 angle (rad).")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    model = mujoco.MjModel.from_xml_path(args.model)
    data = mujoco.MjData(model)

    if model.nq >= 2:
        data.qpos[0] = args.q1
        data.qpos[1] = args.q2

    if args.headless:
        start = time.time()
        seconds = args.seconds if args.seconds > 0 else 0.5
        while time.time() - start < seconds:
            mujoco.mj_step(model, data)
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

