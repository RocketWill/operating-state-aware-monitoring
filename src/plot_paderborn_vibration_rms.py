'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/plot_paderborn_vibration_rms.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


FEATURE_PATH = Path("outputs/paderborn_signal_features/recording_features.csv")
OUTPUT_PATH = Path("outputs/paderborn_figures/vibration_rms_distribution.png")
CONDITIONS = [
    "N15_M07_F10",
    "N09_M07_F10",
    "N15_M01_F10",
    "N15_M07_F04",
]
LABELS = ["healthy", "damaged"]
COLORS = {"healthy": "#4C78A8", "damaged": "#E15759"}


def main():
    with FEATURE_PATH.open() as file:
        rows = list(csv.DictReader(file))

    recording_values = {
        (condition, label): [
            float(row["vibration_1_rms"])
            for row in rows
            if row["condition"] == condition and row["label"] == label
        ]
        for condition in CONDITIONS
        for label in LABELS
    }

    fig, ax = plt.subplots(figsize=(10, 5.2))
    positions = np.arange(len(CONDITIONS)) * 2.4
    for label_index, label in enumerate(LABELS):
        boxes = ax.boxplot(
            [recording_values[(condition, label)] for condition in CONDITIONS],
            positions=positions + (label_index - 0.5) * 0.55,
            widths=0.45,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": "black", "linewidth": 1.2},
        )
        for box in boxes["boxes"]:
            box.set_facecolor(COLORS[label])
            box.set_alpha(0.75)

    ax.set_title("Vibration RMS by Operating Condition and Bearing Health")
    ax.set_ylabel("Vibration RMS (dataset units)")
    ax.set_xticks(positions)
    ax.set_xticklabels(CONDITIONS, rotation=15)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(
        handles=[Patch(facecolor=COLORS[label], label=label.title()) for label in LABELS],
        frameon=False,
    )
    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=180)
    print(f"saved: {OUTPUT_PATH}")

    bearing_recordings = defaultdict(list)
    for row in rows:
        key = (row["condition"], row["bearing_id"], row["label"])
        bearing_recordings[key].append(float(row["vibration_1_rms"]))

    bearing_values = defaultdict(list)
    for (condition, _bearing_id, label), rms_values in bearing_recordings.items():
        bearing_values[(condition, label)].append(float(np.median(rms_values)))

    fig, ax = plt.subplots(figsize=(10, 5.2))
    positions = np.arange(len(CONDITIONS)) * 2.4
    for label_index, label in enumerate(LABELS):
        label_positions = positions + (label_index - 0.5) * 0.55
        boxes = ax.boxplot(
            [bearing_values[(condition, label)] for condition in CONDITIONS],
            positions=label_positions,
            widths=0.45,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": "black", "linewidth": 1.2},
        )
        for box in boxes["boxes"]:
            box.set_facecolor(COLORS[label])
            box.set_alpha(0.75)
        for position, condition in zip(label_positions, CONDITIONS):
            values = bearing_values[(condition, label)]
            point_offsets = np.linspace(-0.12, 0.12, len(values))
            ax.scatter(
                np.full(len(values), position) + point_offsets,
                values,
                color=COLORS[label],
                edgecolor="black",
                linewidth=0.5,
                s=28,
                zorder=3,
            )

    ax.set_title("Bearing-level Vibration RMS by Operating Condition and Health")
    ax.set_ylabel("Per-bearing median vibration RMS (dataset units)")
    ax.set_xticks(positions)
    ax.set_xticklabels(CONDITIONS, rotation=15)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(
        handles=[Patch(facecolor=COLORS[label], label=label.title()) for label in LABELS],
        frameon=False,
    )
    fig.tight_layout()

    bearing_output_path = OUTPUT_PATH.with_name("vibration_rms_bearing_level.png")
    fig.savefig(bearing_output_path, dpi=180)
    print(f"saved: {bearing_output_path}")


if __name__ == "__main__":
    main()
