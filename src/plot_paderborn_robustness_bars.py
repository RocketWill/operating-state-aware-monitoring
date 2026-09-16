'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/plot_paderborn_robustness_bars.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


METADATA_PATH = Path("outputs/paderborn_four_condition_robustness/run_metadata.json")
OUTPUT_PATH = Path("outputs/paderborn_figures/matched_shifted_macro_f1.png")
CONDITIONS = [
    "N15_M07_F10",
    "N09_M07_F10",
    "N15_M01_F10",
    "N15_M07_F04",
]
SENSOR_GROUPS = ["current", "vibration", "combined"]
COLORS = {
    "current": "#4C78A8",
    "vibration": "#59A14F",
    "combined": "#B279A2",
}


def main():
    metadata = json.loads(METADATA_PATH.read_text())
    metrics = metadata["pooled_metrics"]
    x = np.arange(len(CONDITIONS))
    width = 0.12

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for sensor_index, sensor_group in enumerate(SENSOR_GROUPS):
        for scenario_index, scenario in enumerate(("matched", "shifted")):
            values = [
                metrics[condition][scenario][sensor_group]["logistic"]["macro_f1"]
                for condition in CONDITIONS
            ]
            offset = (sensor_index * 2 + scenario_index - 2.5) * width
            bars = ax.bar(
                x + offset,
                values,
                width,
                color=COLORS[sensor_group],
                hatch="//" if scenario == "shifted" else None,
                edgecolor="white",
            )
            ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=7)

    ax.set_title("Matched vs. Shifted Macro-F1 Across Operating Conditions")
    ax.set_ylabel("Macro-F1")
    ax.set_xticks(x)
    ax.set_xticklabels(CONDITIONS, rotation=15)
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.25)
    sensor_legend = [
        Patch(facecolor=COLORS[group], label=group.title())
        for group in SENSOR_GROUPS
    ]
    scenario_legend = [
        Patch(facecolor="white", edgecolor="black", label="Matched"),
        Patch(facecolor="white", edgecolor="black", hatch="//", label="Shifted"),
    ]
    ax.legend(
        handles=sensor_legend + scenario_legend,
        ncol=5,
        fontsize=8,
        frameon=False,
    )
    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=180)
    print(f"saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
