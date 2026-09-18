'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/plot_paderborn_shift_drop_heatmap.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm


METADATA_PATH = Path("outputs/paderborn_four_condition_robustness/run_metadata.json")
OUTPUT_PATH = Path("outputs/paderborn_figures/shifted_minus_matched_macro_f1.png")
CONDITIONS = [
    "N15_M07_F10",
    "N09_M07_F10",
    "N15_M01_F10",
    "N15_M07_F04",
]
SENSOR_GROUPS = ["current", "vibration", "combined"]


def main():
    metadata = json.loads(METADATA_PATH.read_text())
    metrics = metadata["pooled_metrics"]
    values = np.asarray(
        [
            [
                metrics[condition]["shifted"][sensor_group]["logistic"]["macro_f1"]
                - metrics[condition]["matched"][sensor_group]["logistic"]["macro_f1"]
                for condition in CONDITIONS
            ]
            for sensor_group in SENSOR_GROUPS
        ]
    )
    limit = max(abs(values.min()), abs(values.max()))

    fig, ax = plt.subplots(figsize=(10, 3.8))
    image = ax.imshow(
        values,
        cmap="RdBu",
        norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit),
        aspect="auto",
    )
    for row_index in range(values.shape[0]):
        for column_index in range(values.shape[1]):
            value = values[row_index, column_index]
            ax.text(
                column_index,
                row_index,
                f"{value:+.4f}",
                ha="center",
                va="center",
                color="white" if abs(value) > limit * 0.55 else "black",
            )

    ax.set_title("Shifted − Matched Macro-F1 Across Operating Conditions")
    ax.set_xticks(range(len(CONDITIONS)))
    ax.set_xticklabels(CONDITIONS, rotation=15)
    ax.set_yticks(range(len(SENSOR_GROUPS)))
    ax.set_yticklabels([group.title() for group in SENSOR_GROUPS])
    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label("Shifted − Matched Macro-F1")
    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=180)
    print(f"saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
