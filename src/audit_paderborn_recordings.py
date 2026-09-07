'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/audit_paderborn_recordings.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
"""Small audit for the extracted Paderborn recordings."""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.io import loadmat


DATA_DIR = Path("data/paderborn/raw")
OUTPUT_DIR = Path("outputs/paderborn_audit")
REQUIRED_CHANNELS = {
    "phase_current_1",
    "phase_current_2",
    "vibration_1",
    "force",
    "speed",
    "torque",
    "temp_2_bearing_module",
}
CONDITIONS = {
    "N15_M07_F10",
    "N09_M07_F10",
    "N15_M01_F10",
    "N15_M07_F04",
}


def parse_name(path):
    parts = path.stem.split("_")
    return {
        "condition": "_".join(parts[:3]),
        "bearing_id": parts[3],
        "recording_id": int(parts[4]),
    }


def signal_digest(record):
    digest = hashlib.sha256()
    for channel in sorted(record["Y"], key=lambda item: item["Name"]):
        digest.update(channel["Name"].encode())
        digest.update(np.asarray(channel["Data"]).tobytes())
    for axis in record["X"]:
        digest.update(np.asarray(axis["Data"]).tobytes())
    return digest.hexdigest()


def inspect(path):
    info = parse_name(path)
    mat = loadmat(path, simplify_cells=True)
    record = mat[path.stem]
    channels = {channel["Name"]: channel for channel in record["Y"]}
    missing = sorted(REQUIRED_CHANNELS - set(channels))
    non_finite = 0
    channel_lengths = []
    axis_lengths = []
    end_times = []

    for channel in channels.values():
        values = np.asarray(channel["Data"], dtype=float)
        non_finite += int((~np.isfinite(values)).sum())
        channel_lengths.append(values.size)
        axis = record["X"][int(channel["XIndex"]) - 1]
        time = np.asarray(axis["Data"], dtype=float)
        axis_lengths.append(time.size)
        end_times.append(float(time[-1]))

    return {
        **info,
        "source_file": str(path),
        "channel_count": len(channels),
        "missing_channels": ",".join(missing),
        "all_channel_lengths_match_time": len(channel_lengths) == len(axis_lengths)
        and all(a == b for a, b in zip(channel_lengths, axis_lengths)),
        "sync_end_time_spread_s": max(end_times) - min(end_times),
        "non_finite": non_finite,
        "digest": signal_digest(record),
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(DATA_DIR.glob("*/N*_*.mat"))
    rows = []
    errors = []

    for index, path in enumerate(paths, start=1):
        try:
            row = inspect(path)
            rows.append(row)
        except Exception as error:  # keep the audit moving and report the file
            errors.append({"source_file": str(path), "error": repr(error)})
        if index % 100 == 0:
            print(f"checked {index}/{len(paths)}")

    with (OUTPUT_DIR / "recording_audit.csv").open("w", newline="") as file:
        fields = [
            "bearing_id",
            "condition",
            "recording_id",
            "source_file",
            "channel_count",
            "missing_channels",
            "all_channel_lengths_match_time",
            "sync_end_time_spread_s",
            "non_finite",
            "digest",
        ]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    by_digest = defaultdict(list)
    for row in rows:
        by_digest[row["digest"]].append(row["source_file"])
    duplicates = [files for files in by_digest.values() if len(files) > 1]
    (OUTPUT_DIR / "duplicate_candidates.json").write_text(
        json.dumps(duplicates, indent=2)
    )
    (OUTPUT_DIR / "audit_errors.json").write_text(json.dumps(errors, indent=2))

    print(f"recordings: {len(rows)}")
    print(f"errors: {len(errors)}")
    print(f"duplicate candidates: {len(duplicates)}")
    print(f"saved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
