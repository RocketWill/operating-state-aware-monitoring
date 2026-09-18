'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/analyze_paderborn_signal_features.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.io import loadmat


DATA_DIR = Path("data/paderborn/raw")
PROTOCOL_DIR = Path("outputs/paderborn_protocol")
OUTPUT_DIR = Path("outputs/paderborn_signal_features")
CHANNELS = ["phase_current_1", "phase_current_2", "vibration_1"]
FEATURE_NAMES = ["mean", "std", "rms", "peak_to_peak"]


def signal_features(values):
    return dict(
        zip(
            FEATURE_NAMES,
            [
                float(values.mean()),
                float(values.std()),
                float(np.sqrt(np.mean(values**2))),
                float(np.ptp(values)),
            ],
        )
    )


def load_rows():
    with (PROTOCOL_DIR / "recording_manifest.csv").open() as file:
        manifest = list(csv.DictReader(file))

    rows = []
    for item in manifest:
        if item["include_primary"] != "true" or item["include_recording"] != "true":
            continue
        path = DATA_DIR / item["bearing_id"] / item["filename"]
        mat = loadmat(path, simplify_cells=True)
        record = mat[path.stem]
        channels = {channel["Name"]: channel for channel in record["Y"]}
        rows.append(
            {
                "bearing_id": item["bearing_id"],
                "recording_id": item["recording_id"],
                "condition": item["condition"],
                "label": item["label"],
                "features": {
                    name: signal_features(
                        np.asarray(channels[name]["Data"], dtype=float)
                    )
                    for name in CHANNELS
                },
            }
        )
    return rows


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    grouped = defaultdict(list)
    for row in rows:
        for channel in CHANNELS:
            for feature in FEATURE_NAMES:
                key = (row["condition"], channel, feature, row["label"])
                grouped[key].append(row["features"][channel][feature])

    summary = []
    for (condition, channel, feature, label), values in sorted(grouped.items()):
        values = np.asarray(values)
        summary.append(
            {
                "condition": condition,
                "channel": channel,
                "feature": feature,
                "label": label,
                "count": len(values),
                "mean": float(values.mean()),
                "median": float(np.median(values)),
                "std": float(values.std()),
                "q25": float(np.quantile(values, 0.25)),
                "q75": float(np.quantile(values, 0.75)),
            }
        )

    with (OUTPUT_DIR / "feature_summary.csv").open("w", newline="") as file:
        fields = list(summary[0].keys())
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)

    recording_features = []
    for row in rows:
        recording_row = {
            "bearing_id": row["bearing_id"],
            "recording_id": row["recording_id"],
            "condition": row["condition"],
            "label": row["label"],
        }
        for channel in CHANNELS:
            for feature in FEATURE_NAMES:
                recording_row[f"{channel}_{feature}"] = row["features"][channel][feature]
        recording_features.append(recording_row)

    with (OUTPUT_DIR / "recording_features.csv").open("w", newline="") as file:
        fields = list(recording_features[0].keys())
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(recording_features)

    print(f"rows: {len(rows)}")
    for condition in sorted({row["condition"] for row in rows}):
        for channel in CHANNELS:
            healthy = next(
                row
                for row in summary
                if row["condition"] == condition
                and row["channel"] == channel
                and row["feature"] == "rms"
                and row["label"] == "healthy"
            )
            damaged = next(
                row
                for row in summary
                if row["condition"] == condition
                and row["channel"] == channel
                and row["feature"] == "rms"
                and row["label"] == "damaged"
            )
            print(
                f"{condition} {channel} rms: "
                f"healthy={healthy['mean']:.4f}, "
                f"damaged={damaged['mean']:.4f}, "
                f"diff={damaged['mean'] - healthy['mean']:.4f}"
            )
    print(f"saved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
