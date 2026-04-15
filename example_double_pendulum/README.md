# Double Pendulum (Hello World)

This folder is a minimal MuJoCo “hello world” for a **double pendulum**, following the recommended workflow:

- Stage 1: build the model from **primitive capsules**
- Stage 2: run it from **Python**
- Stage 3: add a **mesh-visual** variant (meshes for visuals, primitives for physics)

## Files

| File | Purpose |
|------|---------|
| `double_pendulum.xml` | Capsule-based MJCF model (stable physics baseline) |
| `run_example.py` | Runs `double_pendulum.xml` in the passive viewer |
| `double_pendulum_mesh.xml` | Same physics, plus **visual-only** mesh geoms |
| `view_mesh.py` | Runs `double_pendulum_mesh.xml` in the passive viewer |

## Run (macOS)

From the project root:

```bash
# Capsule model (viewer)
./run.sh example_double_pendulum/run_example.py

# Mesh-visual model (viewer)
./run.sh example_double_pendulum/view_mesh.py
```

By default, the viewer runs **until you close the window**. To run for a fixed duration:

```bash
./run.sh example_double_pendulum/run_example.py --seconds 30
```

Directly (if you activated `.venv` manually):

```bash
source .venv/bin/activate
mjpython example_double_pendulum/run_example.py
```

## Quick headless check (no viewer)

Useful when you just want to confirm the XML compiles and steps:

```bash
./run.sh example_double_pendulum/run_example.py --headless --seconds 1
./run.sh example_double_pendulum/view_mesh.py --headless --seconds 1
```

## First things to tweak

- `data.qpos` via `--q1`, `--q2`
- joint `axis` in the XML (e.g. `0 1 0` vs `1 0 0`)
- `damping`
- link length in `fromto`
- `timestep` / `integrator`

## Mesh notes

`double_pendulum_mesh.xml` currently references the repo root OBJ (`Two_link_model.obj`) as a **placeholder** mesh to demonstrate the pattern. For a real CAD import:

- export each moving part as a **separate** mesh (`base`, `link1`, `link2`)
- keep mesh frames aligned with joint frames if possible
- keep simple primitives for collision/inertia and use meshes for visuals (`contype="0" conaffinity="0"`)

