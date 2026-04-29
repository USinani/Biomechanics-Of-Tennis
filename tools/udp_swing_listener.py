#!/usr/bin/env python3
"""Tiny UDP listener to verify Matlab_v2/three_d/streaming/stream_swing_udp.m.

Run BEFORE the MATLAB streamer (acts as a stand-in for the future Unity
client). Prints each received swing frame as compact JSON; dumps the full
session to a .jsonl file for offline diff against the source jsonl.

Usage:
    python tools/udp_swing_listener.py
    python tools/udp_swing_listener.py --port 55001 --out /tmp/recv.jsonl
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=55001)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional .jsonl file to record every received frame.",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="Stop after this many frames (0 = run forever).",
    )
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    sock.settimeout(5.0)
    print(f"[udp_swing_listener] listening on {args.host}:{args.port}", flush=True)

    fp = args.out.open("w") if args.out else None
    received = 0
    try:
        while True:
            try:
                data, addr = sock.recvfrom(2048)
            except socket.timeout:
                print("[udp_swing_listener] no data for 5s; exiting.", flush=True)
                break
            try:
                obj = json.loads(data.decode("utf-8").strip())
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                print(f"[udp_swing_listener] bad packet from {addr}: {exc}", file=sys.stderr)
                continue
            received += 1
            if fp is not None:
                fp.write(json.dumps(obj) + "\n")
            short = (
                f"frame={obj.get('frame'):>4}  t={obj.get('t_s'):.3f}s  "
                f"phase={obj.get('phase_label')}  speed={obj.get('racket_speed_mps', 0):.2f} m/s"
            )
            print(short, flush=True)
            if args.frames and received >= args.frames:
                break
    finally:
        sock.close()
        if fp is not None:
            fp.close()
            print(f"[udp_swing_listener] wrote {received} frames to {args.out}", flush=True)


if __name__ == "__main__":
    main()
