'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/run_physical_interpretation.py
Description: Summarize measured signals for physical interpretation.

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import json
import math
import os
import platform
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import sklearn

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from read_single_cycle import CHANNELS
from run_first_baseline import (
    CONDITION_COLUMNS,
    DATA_DIR,
    TARGET_LABELS,
    load_channel,
    load_profile,
    select_eligible_cycles,
)


OUTPUT_DIR = Path("outputs/physical_interpretation")
TARGET_COLUMN = "pump_leakage"
OTHER_CONDITION_COLUMNS = [
    column
    for column in CONDITION_COLUMNS
    if column != TARGET_COLUMN
]
MEASUREMENT_CHANNELS = {
    "motor_power": ["EPS1"],
    "pressure": [
        "PS1",
        "PS2",
        "PS3",
        "PS4",
        "PS5",
        "PS6",
    ],
    "flow": ["FS1", "FS2"],
    "temperature": ["TS1", "TS2", "TS3", "TS4"],
}
PHASE_RANGES = [
    (0, 10),
    (10, 20),
    (20, 30),
    (30, 40),
    (40, 50),
    (50, 60),
]


def build_cycle_feature_records(
    channel,
    family,
    channel_data,
    eligible_profile,
):
    cycle_mean = channel_data.mean(
        axis=1,
        skipna=False,
    )
    metadata = CHANNELS[channel]
    cycle_records = pd.DataFrame(
        {
            "cycle_index": channel_data.index,
            "group": eligible_profile.loc[
                channel_data.index,
                "group",
            ].values,
            TARGET_COLUMN: eligible_profile.loc[
                channel_data.index,
                TARGET_COLUMN,
            ].values,
            "channel": channel,
            "family": family,
            "cycle_mean": cycle_mean.values,
            "unit": metadata["unit"],
            "sampling_rate_hz": metadata["rate"],
        }
    )

    summary_records = []
    for label in TARGET_LABELS:
        subset = cycle_records.loc[
            cycle_records[TARGET_COLUMN] == label
        ]
        values = subset["cycle_mean"]
        summary_records.append(
            {
                "channel": channel,
                "family": family,
                "quantity": metadata["quantity"],
                "unit": metadata["unit"],
                "sampling_rate_hz": metadata["rate"],
                TARGET_COLUMN: label,
                "cycle_count": int(len(subset)),
                "group_count": int(subset["group"].nunique()),
                "cycle_mean_mean": float(values.mean()),
                "cycle_mean_median": float(values.median()),
                "cycle_mean_std": float(values.std()),
                "cycle_mean_q1": float(values.quantile(0.25)),
                "cycle_mean_q3": float(values.quantile(0.75)),
                "cycle_mean_min": float(values.min()),
                "cycle_mean_max": float(values.max()),
            }
        )

    return cycle_records, pd.DataFrame(summary_records)


def build_trace_summary_records(
    channel,
    channel_data,
    eligible_profile,
):
    metadata = CHANNELS[channel]
    target = eligible_profile[TARGET_COLUMN]
    records = []

    for label in TARGET_LABELS:
        label_index = target[target == label].index
        label_data = channel_data.loc[label_index]
        median = label_data.median(axis=0)
        q1 = label_data.quantile(0.25, axis=0)
        q3 = label_data.quantile(0.75, axis=0)

        records.append(
            pd.DataFrame(
                {
                    "channel": channel,
                    "quantity": metadata["quantity"],
                    "unit": metadata["unit"],
                    "sampling_rate_hz": metadata["rate"],
                    TARGET_COLUMN: label,
                    "sample_index": np.arange(len(median)),
                    "time_s": np.arange(len(median)) / metadata["rate"],
                    "median": median.values,
                    "q1": q1.values,
                    "q3": q3.values,
                    "cycle_count": int(len(label_data)),
                    "group_count": int(
                        eligible_profile.loc[
                            label_index,
                            "group",
                        ].nunique()
                    ),
                }
            )
        )

    return pd.concat(records, ignore_index=True)


def build_phase_summary_records(
    channel,
    channel_data,
    eligible_profile,
):
    metadata = CHANNELS[channel]
    target = eligible_profile[TARGET_COLUMN]
    records = []

    for label in TARGET_LABELS:
        label_index = target[target == label].index
        label_data = channel_data.loc[label_index]

        for start_sec, end_sec in PHASE_RANGES:
            start_index = int(start_sec * metadata["rate"])
            end_index = min(
                int(end_sec * metadata["rate"]),
                label_data.shape[1],
            )
            phase_data = label_data.iloc[:, start_index:end_index]
            cycle_phase_mean = phase_data.mean(axis=1)

            records.append(
                {
                    "channel": channel,
                    "quantity": metadata["quantity"],
                    "unit": metadata["unit"],
                    "sampling_rate_hz": metadata["rate"],
                    TARGET_COLUMN: label,
                    "phase_start_s": start_sec,
                    "phase_end_s": end_sec,
                    "cycle_count": int(len(cycle_phase_mean)),
                    "group_count": int(
                        eligible_profile.loc[
                            label_index,
                            "group",
                        ].nunique()
                    ),
                    "mean": float(cycle_phase_mean.mean()),
                    "median": float(cycle_phase_mean.median()),
                    "std": float(cycle_phase_mean.std()),
                }
            )

    return pd.DataFrame(records)


def build_condition_summary(eligible_profile):
    records = []

    for condition in OTHER_CONDITION_COLUMNS:
        for value in sorted(
            eligible_profile[condition].drop_duplicates().tolist()
        ):
            subset = eligible_profile.loc[
                eligible_profile[condition] == value
            ]
            counts = subset[TARGET_COLUMN].value_counts()
            record = {
                "condition": condition,
                "condition_value": value,
                "cycle_count": int(len(subset)),
                "group_count": int(subset["group"].nunique()),
            }
            for label in TARGET_LABELS:
                record["target_count_{}".format(label)] = int(
                    counts.get(label, 0)
                )
            records.append(record)

    return pd.DataFrame(records)


def plot_cycle_mean_distributions(
    cycle_records,
    eligible_profile,
    output_path,
):
    channel_names = [
        channel
        for channels in MEASUREMENT_CHANNELS.values()
        for channel in channels
    ]
    columns = 3
    rows = math.ceil(len(channel_names) / columns)
    figure, axes = plt.subplots(
        rows,
        columns,
        figsize=(15, 4 * rows),
        squeeze=False,
    )

    for position, channel in enumerate(channel_names):
        axis = axes[position // columns][position % columns]
        channel_records = cycle_records.loc[
            cycle_records["channel"] == channel
        ]
        values = [
            channel_records.loc[
                channel_records[TARGET_COLUMN] == label,
                "cycle_mean",
            ]
            for label in TARGET_LABELS
        ]
        metadata = CHANNELS[channel]

        axis.boxplot(
            values,
            tick_labels=[str(label) for label in TARGET_LABELS],
        )
        axis.set_title(
            "{} ({})\n{}; n={}".format(
                channel,
                metadata["quantity"],
                metadata["unit"],
                len(channel_records),
            )
        )
        axis.set_xlabel(TARGET_COLUMN)
        axis.set_ylabel("Cycle mean ({})".format(metadata["unit"]))

    for position in range(len(channel_names), rows * columns):
        axes[position // columns][position % columns].axis("off")

    figure.suptitle(
        "Cycle-level measurement summaries by pump leakage label",
        y=0.995,
    )
    figure.text(
        0.5,
        0.01,
        "stable_flag=0; cooler_condition, valve_condition, and "
        "accumulator_pressure pooled; "
        "cycle index range {}–{}".format(
            eligible_profile.index.min(),
            eligible_profile.index.max(),
        ),
        ha="center",
    )
    figure.tight_layout(rect=[0, 0.03, 1, 0.97])
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_raw_trace_summaries(
    trace_records,
    eligible_profile,
    output_path,
):
    channel_names = [
        channel
        for channels in MEASUREMENT_CHANNELS.values()
        for channel in channels
    ]
    columns = 3
    rows = math.ceil(len(channel_names) / columns)
    figure, axes = plt.subplots(
        rows,
        columns,
        figsize=(15, 4 * rows),
        squeeze=False,
    )

    for position, channel in enumerate(channel_names):
        axis = axes[position // columns][position % columns]
        channel_records = trace_records.loc[
            trace_records["channel"] == channel
        ]
        metadata = CHANNELS[channel]

        for label in TARGET_LABELS:
            label_records = channel_records.loc[
                channel_records[TARGET_COLUMN] == label
            ]
            axis.plot(
                label_records["time_s"],
                label_records["median"],
                label="{} (n={})".format(label, label_records.iloc[0]["cycle_count"]),
            )
            axis.fill_between(
                label_records["time_s"],
                label_records["q1"],
                label_records["q3"],
                alpha=0.15,
            )

        axis.set_title(
            "{} ({})".format(channel, metadata["quantity"])
        )
        axis.set_xlabel("Time (s)")
        axis.set_ylabel(metadata["unit"])

    for position in range(len(channel_names), rows * columns):
        axes[position // columns][position % columns].axis("off")

    handles, labels = axes[0][0].get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        loc="upper center",
        ncol=len(TARGET_LABELS),
        bbox_to_anchor=(0.5, 0.995),
    )
    figure.suptitle(
        "Raw-signal median and IQR by pump leakage label",
        y=0.965,
    )
    figure.text(
        0.5,
        0.01,
        "stable_flag=0; cooler_condition, valve_condition, and "
        "accumulator_pressure pooled; "
        "cycle index range {}–{}".format(
            eligible_profile.index.min(),
            eligible_profile.index.max(),
        ),
        ha="center",
    )
    figure.tight_layout(rect=[0, 0.03, 1, 0.94])
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def build_run_metadata(
    profile,
    eligible_profile,
    output_paths,
):
    group_size_counts = (
        eligible_profile["group"]
        .value_counts()
        .value_counts()
        .sort_index()
    )
    channel_metadata = {}

    for family, channels in MEASUREMENT_CHANNELS.items():
        for channel in channels:
            metadata = CHANNELS[channel]
            channel_metadata[channel] = {
                "family": family,
                "quantity": metadata["quantity"],
                "sampling_rate_hz": metadata["rate"],
                "samples_per_cycle": metadata["samples"],
                "unit": metadata["unit"],
            }

    return {
        "source_script": "src/run_physical_interpretation.py",
        "command": (
            "conda run --no-capture-output -n windfusion "
            "python src/run_physical_interpretation.py"
        ),
        "environment": {
            "conda_environment": os.environ.get(
                "CONDA_DEFAULT_ENV"
            ),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "matplotlib": matplotlib.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "data": {
            "directory": str(DATA_DIR),
            "profile_shape": [
                int(profile.shape[0]),
                int(profile.shape[1]),
            ],
            "profile_columns": list(profile.columns),
        },
        "eligibility": {
            "rule": "stable_flag == 0",
            "selected_cycles": int(len(eligible_profile)),
            "cycle_index_range": [
                int(eligible_profile.index.min()),
                int(eligible_profile.index.max()),
            ],
        },
        "target": {
            "column": TARGET_COLUMN,
            "labels": TARGET_LABELS,
            "counts": {
                str(label): int(
                    (eligible_profile[TARGET_COLUMN] == label).sum()
                )
                for label in TARGET_LABELS
            },
        },
        "groups": {
            "columns": CONDITION_COLUMNS,
            "count": int(eligible_profile["group"].nunique()),
            "size_counts": {
                str(size): int(count)
                for size, count in group_size_counts.items()
            },
        },
        "channels": channel_metadata,
        "interpretation": {
            "summary": (
                "Cycle-level features and raw-signal median/IQR are "
                "reported by pump leakage label."
            ),
            "other_conditions": OTHER_CONDITION_COLUMNS,
            "other_condition_scope": (
                "Other component conditions are pooled in signal plots "
                "and reported separately with cycle and group support."
            ),
            "power_proxy": "not_calculated",
            "power_proxy_reason": (
                "No verified topology supports an upstream/downstream "
                "pressure-drop and flow pairing."
            ),
            "claim_boundary": [
                "Pump leakage labels are not treated as a temporal degradation trajectory.",
                "Descriptive differences are not causal effects or energy-saving claims.",
            ],
        },
        "outputs": output_paths,
    }


def main():
    profile = load_profile()
    eligible_profile = select_eligible_cycles(profile)
    cycle_records = []
    channel_summaries = []
    trace_summaries = []
    phase_summaries = []

    for family, channels in MEASUREMENT_CHANNELS.items():
        for channel in channels:
            metadata = CHANNELS[channel]
            channel_data = load_channel(
                channel,
                eligible_profile.index,
            )
            assert channel_data.shape[1] == metadata["samples"]
            assert not channel_data.isna().any().any()

            cycle_summary, channel_summary = build_cycle_feature_records(
                channel,
                family,
                channel_data,
                eligible_profile,
            )
            cycle_records.append(cycle_summary)
            channel_summaries.append(channel_summary)
            trace_summaries.append(
                build_trace_summary_records(
                    channel,
                    channel_data,
                    eligible_profile,
                )
            )
            phase_summaries.append(
                build_phase_summary_records(
                    channel,
                    channel_data,
                    eligible_profile,
                )
            )

    cycle_records = pd.concat(cycle_records, ignore_index=True)
    channel_summary = pd.concat(
        channel_summaries,
        ignore_index=True,
    )
    trace_summary = pd.concat(
        trace_summaries,
        ignore_index=True,
    )
    phase_summary = pd.concat(
        phase_summaries,
        ignore_index=True,
    )
    condition_summary = build_condition_summary(eligible_profile)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_paths = {
        "cycle_feature_values": str(
            OUTPUT_DIR / "cycle_feature_values.csv"
        ),
        "channel_summary": str(
            OUTPUT_DIR / "channel_summary.csv"
        ),
        "raw_trace_summary": str(
            OUTPUT_DIR / "raw_trace_summary.csv"
        ),
        "phase_summary": str(
            OUTPUT_DIR / "phase_summary.csv"
        ),
        "condition_summary": str(
            OUTPUT_DIR / "condition_summary.csv"
        ),
        "cycle_mean_plot": str(
            OUTPUT_DIR / "cycle_mean_distributions.png"
        ),
        "raw_trace_plot": str(
            OUTPUT_DIR / "raw_trace_summaries.png"
        ),
    }

    cycle_records.to_csv(
        output_paths["cycle_feature_values"],
        index=False,
    )
    channel_summary.to_csv(
        output_paths["channel_summary"],
        index=False,
    )
    trace_summary.to_csv(
        output_paths["raw_trace_summary"],
        index=False,
    )
    phase_summary.to_csv(
        output_paths["phase_summary"],
        index=False,
    )
    condition_summary.to_csv(
        output_paths["condition_summary"],
        index=False,
    )

    plot_cycle_mean_distributions(
        cycle_records,
        eligible_profile,
        output_paths["cycle_mean_plot"],
    )
    plot_raw_trace_summaries(
        trace_summary,
        eligible_profile,
        output_paths["raw_trace_plot"],
    )

    metadata_path = OUTPUT_DIR / "run_metadata.json"
    metadata = build_run_metadata(
        profile,
        eligible_profile,
        output_paths,
    )
    metadata_path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("Saved physical interpretation outputs to:", OUTPUT_DIR)
    print("Saved metadata to:", metadata_path)


if __name__ == "__main__":
    main()
