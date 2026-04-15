#!/usr/bin/env python3
"""Export MuJoCo rollout data to Unity-friendly TXT/CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


EXPORT_COLUMNS = [
    "episode",
    "step",
    "time_s",
    "q1",
    "q2",
    "qd1",
    "qd2",
    "tau1",
    "tau2",
    "prior_tau1",
    "prior_tau2",
    "applied_tau1",
    "applied_tau2",
    "hand_x",
    "hand_y",
    "hand_z",
    "target_x",
    "target_y",
    "target_z",
    "reward",
    "dist",
]


def _normalize_records(records: Iterable[dict]) -> list[dict]:
    out = []
    for rec in records:
        row = {k: rec.get(k, "") for k in EXPORT_COLUMNS}
        out.append(row)
    return out


def write_rollout_csv(records: Iterable[dict], output_csv: str | Path) -> Path:
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = _normalize_records(records)
    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output_csv


def write_rollout_txt(records: Iterable[dict], output_txt: str | Path) -> Path:
    output_txt = Path(output_txt)
    output_txt.parent.mkdir(parents=True, exist_ok=True)
    rows = _normalize_records(records)
    with output_txt.open("w") as f:
        f.write(",".join(EXPORT_COLUMNS) + "\n")
        for row in rows:
            vals = [str(row[c]) for c in EXPORT_COLUMNS]
            f.write(",".join(vals) + "\n")
    return output_txt


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert rollout JSON list to TXT/CSV")
    parser.add_argument("--input-json", type=Path, required=True, help="JSON file containing list of rollout records")
    parser.add_argument("--out-prefix", type=Path, required=True, help="Output prefix (without extension)")
    args = parser.parse_args()

    with args.input_json.open("r") as f:
        records = json.load(f)
    if not isinstance(records, list):
        raise ValueError("Input JSON must be a list of per-step records.")

    csv_path = write_rollout_csv(records, args.out_prefix.with_suffix(".csv"))
    txt_path = write_rollout_txt(records, args.out_prefix.with_suffix(".txt"))
    print(f"Wrote {csv_path}")
    print(f"Wrote {txt_path}")


if __name__ == "__main__":
    main()
