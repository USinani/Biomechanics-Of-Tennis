# Mesh Import Preflight (OBJ -> MuJoCo)

Use this checklist before loading OBJ meshes in MuJoCo:

1. **Do not drag `.obj` directly into MuJoCo GUI**
   - MuJoCo GUI expects MJCF/XML model files.
   - Always load an XML wrapper (`view_mesh.xml`, `view_matlab_model.xml`).

2. **Triangulate faces**
   - In Blender: Edit Mode -> A -> `Ctrl+T`.

3. **Apply transforms**
   - In Blender: Object Mode -> Apply Location/Rotation/Scale.

4. **Normals**
   - In Blender: Edit Mode -> A -> `Shift+N`.

5. **Material references**
   - Ensure `.mtl` exists if `mtllib ...` is present in OBJ, or remove invalid refs.

6. **Reasonable mesh size**
   - Keep triangle count moderate.
   - Use MuJoCo `<mesh ... scale="...">` to normalize world size.

7. **Relative paths**
   - Keep mesh `file="..."` paths relative to the XML wrapper location.

8. **Compile-check before viewer**
   - `./run.sh example_two_link/check_model_compile.py`

## Recommended flow

`OBJ -> MJCF XML wrapper -> compile-check -> viewer`

Example commands:

```bash
./run.sh example_two_link/check_model_compile.py
./run.sh example_two_link/play_matlab_bridge.py
```

