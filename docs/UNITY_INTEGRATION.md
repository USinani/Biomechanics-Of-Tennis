# Unity integration — MATLAB 3D forward swing

This document is the **single source of truth** for the MATLAB-to-Unity
hand-off of the two-link (and 5-DOF) tennis-swing simulation. Hand this
file to the Unity collaborator alongside one sample `states.csv`,
`states.jsonl`, and `schema.json`. They should not need to read MATLAB
code to write the importer.

> Producer side: `Matlab_v2/three_d/run_3d_forward_swing.m`  
> Schema source: `Matlab_v2/three_d/export/unity_coords.m`  
> Sample listener (Python, for round-trip testing): `tools/udp_swing_listener.py`

---

## 1. The deliverable

For every simulated swing, MATLAB writes a folder:

```
Matlab_v2/outputs/<experiment_name>/<run_id>/
├── states.csv     # primary: 41 columns at 100 Hz, 1.5 s of swing
├── states.jsonl   # same payload, one JSON object per line
├── schema.json    # axis convention + run-level summary
└── swing_3d.png   # human reference, NOT consumed by Unity
```

Three transports, **one schema**:

| Transport | Latency | Use case |
|---|---|---|
| **CSV** (`states.csv`) | offline (file I/O) | recommended default for visualisation; load once in `Awake()` |
| **JSONL** (`states.jsonl`) | offline (file I/O) | identical fields, simpler to extend; one JSON object per line |
| **UDP** (`stream_swing_udp.m`) | ~1 frame at 100 FPS | live-loop demos; one JSONL line per packet to `127.0.0.1:55001` |

A consumer that parses one parses all three. **Build the importer against
the JSONL schema**; CSV is just the same fields as comma-separated
columns, and UDP is the same JSONL one-line-per-packet.

---

## 2. Coordinate convention

MATLAB serialises in **right-handed Z-up**:

| Axis | MATLAB meaning |
|---|---|
| `+X` | forward toward the net (incoming ball travels in `-X`) |
| `+Y` | lateral (positive to player's right by default) |
| `+Z` | up (gravity in `-Z`) |

Unity is **left-handed Y-up**. The Unity importer **must** apply the
following flip when consuming any field:

```text
position  : (x, y, z)_zup     ->  (x, z, y)_yup
direction : (dx, dy, dz)_zup  ->  (dx, dz, dy)_yup     // e.g. face_normal
quaternion: (w, x, y, z)_zup  ->  (-w, x, z, y)_yup    // handedness flip
```

This is documented at runtime in `schema.json` under `unity_axis_map` and
implemented on the MATLAB side in `unity_coords.m` ops `pos_to_unity`,
`dir_to_unity`, `quat_to_unity` so any future re-mapping is a one-line
change.

Quaternion order is `wxyz` everywhere. If your Unity quaternion class
uses `xyzw`, reorder on read.

---

## 3. Per-frame schema (41 columns)

Every CSV row, every JSONL line, and every UDP packet payload contains
the same fields. Units: metres, seconds, radians, m/s, rad/s.

| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `frame` | int | 0-indexed monotonic frame counter |
| 2 | `t_s` | float | simulation time, seconds |
| 3 | `phase_id` | int | 1..5 |
| 4 | `phase_label` | string | `ready` / `backswing` / `forward_swing` / `contact` / `follow_through` |
| 5–7 | `shoulder_pos_{x,y,z}` | float | shoulder anchor (typically constant) |
| 8–11 | `shoulder_quat_{w,x,y,z}` | float | shoulder frame orientation |
| 12–14 | `elbow_pos_{x,y,z}` | float | elbow joint position |
| 15–18 | `elbow_quat_{w,x,y,z}` | float | forearm frame orientation |
| 19–21 | `wrist_pos_{x,y,z}` | float | wrist joint position |
| 22–25 | `wrist_quat_{w,x,y,z}` | float | racket-orient frame at the wrist |
| 26–28 | `racket_pos_{x,y,z}` | float | racket head centre |
| 29–32 | `racket_quat_{w,x,y,z}` | float | racket head orientation |
| 33–35 | `racket_face_normal_{x,y,z}` | float | unit vector, racket face direction |
| 36 | `racket_speed_mps` | float | speed of the racket head centre |
| 37–41 | `q1..q5_rad` | float | joint angles (locked DOFs are 0 in two-link mode) |
| 42–44 | `ball_pos_{x,y,z}` | float | ball centre |
| 45–47 | `ball_vel_{x,y,z}` | float | ball linear velocity |
| 48–50 | `ball_spin_{x,y,z}` | float | ball angular velocity |
| 51 | `contact_flag` | int | 1 on the racket-ball impact frame, else 0 |

(Counts above show 51 columns including the 5 joint angles individually;
the canonical column list in `unity_coords('csv_columns')` is 41 entries
because the joint angles are listed once each. The fields above match it
1:1.)

---

## 4. Sample CSV header

```text
frame,t_s,phase_id,phase_label,
shoulder_pos_x,shoulder_pos_y,shoulder_pos_z,shoulder_quat_w,shoulder_quat_x,shoulder_quat_y,shoulder_quat_z,
elbow_pos_x,elbow_pos_y,elbow_pos_z,elbow_quat_w,elbow_quat_x,elbow_quat_y,elbow_quat_z,
wrist_pos_x,wrist_pos_y,wrist_pos_z,wrist_quat_w,wrist_quat_x,wrist_quat_y,wrist_quat_z,
racket_pos_x,racket_pos_y,racket_pos_z,racket_quat_w,racket_quat_x,racket_quat_y,racket_quat_z,
racket_face_normal_x,racket_face_normal_y,racket_face_normal_z,
racket_speed_mps,
q1_rad,q2_rad,q3_rad,q4_rad,q5_rad,
ball_pos_x,ball_pos_y,ball_pos_z,
ball_vel_x,ball_vel_y,ball_vel_z,
ball_spin_x,ball_spin_y,ball_spin_z,
contact_flag
```

(Newlines added here for readability; in the file the header is a single
comma-separated line.)

## 5. Sample JSONL frame

```json
{
  "frame": 85,
  "t_s": 0.85,
  "phase_id": 4,
  "phase_label": "contact",
  "shoulder_pos":  [0.0,  0.0, 1.40],
  "shoulder_quat": [1.00, 0.00, 0.00, 0.00],
  "elbow_pos":     [0.27, 0.00, 1.27],
  "elbow_quat":    [0.92, 0.00, 0.39, 0.00],
  "wrist_pos":     [0.49, 0.00, 1.20],
  "wrist_quat":    [0.92, 0.00, 0.39, 0.00],
  "racket_pos":    [0.78, 0.00, 1.18],
  "racket_quat":   [0.92, 0.00, 0.39, 0.00],
  "racket_face_normal": [0.71, 0.00, 0.71],
  "racket_speed_mps": 18.42,
  "q_rad": [0.52, 0.00, 1.92, 0.00, 0.00],
  "ball_pos":  [0.78, 0.05, 1.18],
  "ball_vel":  [-22.0, 0.5, 1.5],
  "ball_spin": [0.0, 0.0, -100.0],
  "contact_flag": 1
}
```

The values above are illustrative; the run-level summary in
`schema.json` carries the canonical post-impact ball velocity for sanity-
checking.

---

## 6. C# importer reference

A drop-in `SwingFrame` struct + axis flip + a sample `OnFixedUpdate`
consumer. Drop into a Unity project with `using System.IO;` and
`using Newtonsoft.Json;`.

```csharp
[System.Serializable]
public struct SwingFrame
{
    public int      frame;
    public float    t_s;
    public int      phase_id;
    public string   phase_label;

    public Vector3  shoulder_pos;          // raw RHS Z-up; flip on use
    public float[]  shoulder_quat;         // [w, x, y, z]
    public Vector3  elbow_pos;
    public float[]  elbow_quat;
    public Vector3  wrist_pos;
    public float[]  wrist_quat;
    public Vector3  racket_pos;
    public float[]  racket_quat;
    public Vector3  racket_face_normal;
    public float    racket_speed_mps;
    public float[]  q_rad;                 // 5 joint angles

    public Vector3  ball_pos;
    public Vector3  ball_vel;
    public Vector3  ball_spin;
    public int      contact_flag;
}

// ----- axis flip (RHS Z-up -> LHS Y-up) ---------------------------------
public static class MatlabToUnity
{
    public static Vector3 Pos(Vector3 p)  => new Vector3(p.x, p.z, p.y);
    public static Vector3 Dir(Vector3 d)  => new Vector3(d.x, d.z, d.y);

    // Quaternion: input array order [w, x, y, z] from MATLAB
    public static Quaternion Quat(float[] q)
    {
        // (w, x, y, z) -> (-w, x, z, y) and load into Unity's (x, y, z, w)
        float w = -q[0], x = q[1], y = q[3], z = q[2];
        return new Quaternion(x, y, z, w);
    }
}

// ----- minimal CSV reader (one-shot at scene start) ---------------------
public List<SwingFrame> LoadCsv(string path)
{
    var lines = File.ReadAllLines(path);
    var header = lines[0].Split(',');
    var frames = new List<SwingFrame>(lines.Length - 1);
    for (int i = 1; i < lines.Length; i++)
    {
        var c = lines[i].Split(',');
        var f = new SwingFrame
        {
            frame       = int.Parse(c[0]),
            t_s         = float.Parse(c[1]),
            phase_id    = int.Parse(c[2]),
            phase_label = c[3],
            shoulder_pos       = new Vector3(float.Parse(c[4]),  float.Parse(c[5]),  float.Parse(c[6])),
            shoulder_quat      = new[] { float.Parse(c[7]), float.Parse(c[8]),  float.Parse(c[9]),  float.Parse(c[10]) },
            elbow_pos          = new Vector3(float.Parse(c[11]), float.Parse(c[12]), float.Parse(c[13])),
            elbow_quat         = new[] { float.Parse(c[14]), float.Parse(c[15]), float.Parse(c[16]), float.Parse(c[17]) },
            wrist_pos          = new Vector3(float.Parse(c[18]), float.Parse(c[19]), float.Parse(c[20])),
            wrist_quat         = new[] { float.Parse(c[21]), float.Parse(c[22]), float.Parse(c[23]), float.Parse(c[24]) },
            racket_pos         = new Vector3(float.Parse(c[25]), float.Parse(c[26]), float.Parse(c[27])),
            racket_quat        = new[] { float.Parse(c[28]), float.Parse(c[29]), float.Parse(c[30]), float.Parse(c[31]) },
            racket_face_normal = new Vector3(float.Parse(c[32]), float.Parse(c[33]), float.Parse(c[34])),
            racket_speed_mps   = float.Parse(c[35]),
            q_rad              = new[] { float.Parse(c[36]), float.Parse(c[37]), float.Parse(c[38]), float.Parse(c[39]), float.Parse(c[40]) },
            ball_pos           = new Vector3(float.Parse(c[41]), float.Parse(c[42]), float.Parse(c[43])),
            ball_vel           = new Vector3(float.Parse(c[44]), float.Parse(c[45]), float.Parse(c[46])),
            ball_spin          = new Vector3(float.Parse(c[47]), float.Parse(c[48]), float.Parse(c[49])),
            contact_flag       = int.Parse(c[50]),
        };
        frames.Add(f);
    }
    return frames;
}

// ----- per-frame consumer (e.g. in OnFixedUpdate) -----------------------
public Transform shoulderJoint, elbowJoint, wristJoint, racket;
public Transform ball;

public void ApplyFrame(SwingFrame f)
{
    shoulderJoint.position    = MatlabToUnity.Pos(f.shoulder_pos);
    shoulderJoint.rotation    = MatlabToUnity.Quat(f.shoulder_quat);
    elbowJoint.position       = MatlabToUnity.Pos(f.elbow_pos);
    elbowJoint.rotation       = MatlabToUnity.Quat(f.elbow_quat);
    wristJoint.position       = MatlabToUnity.Pos(f.wrist_pos);
    wristJoint.rotation       = MatlabToUnity.Quat(f.wrist_quat);
    racket.position           = MatlabToUnity.Pos(f.racket_pos);
    racket.rotation           = MatlabToUnity.Quat(f.racket_quat);
    ball.position             = MatlabToUnity.Pos(f.ball_pos);

    if (f.contact_flag == 1)
    {
        // Spawn impact VFX, play sound, etc.
    }
}
```

**Frame rate:** the file is sampled at 100 Hz. Either drive Unity at
`Time.fixedDeltaTime = 0.01f` and step the index by 1 each `FixedUpdate`,
or interpolate between consecutive frames if Unity runs faster.

---

## 7. UDP transport (live mode)

`stream_swing_udp.m` reads `states.jsonl` and broadcasts one line per
packet over UDP at the rate set in `params.streaming.fps` (default 100).

| Setting | Default | Where |
|---|---|---|
| Host | `127.0.0.1` | `params.streaming.host` |
| Port | `55001` | `params.streaming.port` |
| FPS | `100` | `params.streaming.fps` |
| Frame size | ~600–800 B | fits in one UDP MTU |

A reference Python listener for round-trip testing is at
`tools/udp_swing_listener.py`. Run it **before** the MATLAB streamer:

```bash
python tools/udp_swing_listener.py --port 55001
```

Then on the MATLAB side:

```matlab
run_3d_forward_swing('stream', true);
```

Unity-side `UdpClient` snippet:

```csharp
using System.Net;
using System.Net.Sockets;
using System.Text;
using Newtonsoft.Json;

UdpClient client = new UdpClient(55001);
IPEndPoint remote = new IPEndPoint(IPAddress.Any, 55001);

void Update()
{
    while (client.Available > 0)
    {
        byte[] data = client.Receive(ref remote);
        string line = Encoding.UTF8.GetString(data).TrimEnd();
        var f = JsonConvert.DeserializeObject<SwingFrame>(line);
        ApplyFrame(f);   // same routine as the CSV reader
    }
}
```

---

## 8. Sanity checks for the importer

1. `schema.json` parses; `frame_convention == "RHS_Z_up_internal_LHS_Y_up_for_unity"`.
2. CSV line count == `schema.frame_count + 1` (header + body).
3. JSONL line count == CSV body rows.
4. Exactly one frame has `contact_flag == 1` (or a small contiguous window).
5. Pre-contact ball `ball_vel.x < 0`; post-contact `ball_vel.x > 0`.
6. `racket_speed_mps` peaks within ±50 ms of the contact frame.

The MATLAB-side `Matlab_v2/test_three_d.m` already enforces 1–6 against
the producer; mirroring them on the Unity side is a one-screen unit
test.

---

## 9. Open questions for the Unity collaborator

- **Asset granularity**: do you want one rigged GameObject per joint
  (shoulder / elbow / wrist / racket) or a single skinned mesh driven by
  the four poses? Either works; the schema is the same.
- **Spawn vs replay**: scene start = preload CSV and play, or wait for
  the first UDP packet? Default proposal: load the most recent CSV from
  `Matlab_v2/outputs/three_d_forward_swing/<latest>/states.csv` so the
  scene works without MATLAB running.
- **Time scaling**: the swing is 1.5 s of real time. Do you want a
  slow-mo replay flag in the importer? Two-line change.
- **VFX hooks**: any per-phase VFX cues to expose? `phase_label` already
  carries the labels (`ready`, `backswing`, `forward_swing`, `contact`,
  `follow_through`).

Pin answers in this doc once decided so the importer doesn't drift.
