import argparse
import threading
import time

import mujoco
import mujoco.viewer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Minimal Hill-type muscle control for a double pendulum.")
    p.add_argument(
        "--model",
        default="example_double_pendulum/muscle_pendulum.xml",
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
    p.add_argument("--step", type=float, default=0.05, help="Activation step per keypress.")
    p.add_argument("--q1", type=float, default=0.4, help="Initial hinge1 angle (rad).")
    p.add_argument("--q2", type=float, default=0.1, help="Initial hinge2 angle (rad).")
    return p.parse_args()


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def input_loop(stop: threading.Event, state: dict, step: float) -> None:
    print(
        "Muscle controls:\n"
        "  1 / ! : increase / decrease muscle1 activation\n"
        "  2 / @ : increase / decrease muscle2 activation\n"
        "  0     : zero both activations\n"
        "  q     : quit\n"
    )
    while not stop.is_set():
        try:
            s = input().strip()
        except EOFError:
            break
        if not s:
            continue
        c = s[0]
        if c == "q":
            stop.set()
            break
        if c == "0":
            state["a1"] = 0.0
            state["a2"] = 0.0
        elif c == "1":
            state["a1"] = clamp01(state["a1"] + step)
        elif c == "!":
            state["a1"] = clamp01(state["a1"] - step)
        elif c == "2":
            state["a2"] = clamp01(state["a2"] + step)
        elif c == "@":
            state["a2"] = clamp01(state["a2"] - step)
        print(f"activation: muscle1={state['a1']:.2f}, muscle2={state['a2']:.2f}")


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

    if args.headless:
        run_headless(model, data, seconds=args.seconds if args.seconds > 0 else 0.5)
        return

    state = {"a1": 0.0, "a2": 0.0}
    stop = threading.Event()
    t = threading.Thread(target=input_loop, args=(stop, state, args.step), daemon=True)
    t.start()

    with mujoco.viewer.launch_passive(model, data) as viewer:
        if args.seconds <= 0:
            while viewer.is_running() and not stop.is_set():
                if model.nu >= 2:
                    data.ctrl[0] = state["a1"]
                    data.ctrl[1] = state["a2"]
                mujoco.mj_step(model, data)
                viewer.sync()
                if args.realtime:
                    time.sleep(model.opt.timestep)
        else:
            start = time.time()
            while viewer.is_running() and not stop.is_set() and time.time() - start < args.seconds:
                if model.nu >= 2:
                    data.ctrl[0] = state["a1"]
                    data.ctrl[1] = state["a2"]
                mujoco.mj_step(model, data)
                viewer.sync()
                if args.realtime:
                    time.sleep(model.opt.timestep)

    stop.set()


if __name__ == "__main__":
    main()

