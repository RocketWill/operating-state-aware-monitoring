"""
Read a few Paderborn recordings and save simple signal plots.
"""

import json
from pathlib import Path

import matplotlib
import numpy as np
from scipy.io import loadmat


matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATA_DIR = Path("data/paderborn/raw")
OUTPUT_DIR = Path("outputs/paderborn_reading")

RECORDINGS = [
    DATA_DIR / "K001/N15_M07_F10_K001_20.mat",
    DATA_DIR / "KA04/N15_M07_F10_KA04_10.mat",
]

SIGNALS = [
    "phase_current_1",
    "phase_current_2",
    "vibration_1",
]

# Nominal rates come from the bearing measuring logs.
NOMINAL_RATES = {
    "phase_current_1": 64000.0,
    "phase_current_2": 64000.0,
    "vibration_1": 64000.0,
}


def get_text(value):
    """Return a small MAT metadata field without guessing empty values."""
    value = np.asarray(value)
    if value.size == 0:
        return "unknown"
    return str(value.reshape(-1)[0])


def recording_info(path):
    parts = path.stem.split("_")
    return {
        "condition": "_".join(parts[:3]),
        "bearing_id": parts[3],
        "recording_id": parts[4],
    }


def read_recording(path):
    """Read selected channels and keep the source time arrays."""
    mat = loadmat(path, simplify_cells=True)
    record = mat[path.stem]
    x_axes = record["X"]
    y_channels = {
        channel["Name"]: channel
        for channel in record["Y"]
    }

    result = []
    for name in SIGNALS:
        channel = y_channels[name]
        x_index = int(channel["XIndex"]) - 1
        time = np.asarray(x_axes[x_index]["Data"], dtype=float)
        values = np.asarray(channel["Data"], dtype=float)
        delta = np.diff(time)

        result.append(
            {
                "name": name,
                "time": time,
                "values": values,
                "x_index": x_index + 1,
                "raster": x_axes[x_index]["Raster"],
                "unit": get_text(channel["Unit"]),
                "samples": int(values.size),
                "time_start_s": float(time[0]),
                "time_end_s": float(time[-1]),
                "duration_s": float(time[-1] - time[0]),
                "nominal_rate_hz": NOMINAL_RATES[name],
                "mean_rate_hz": float(
                    (len(time) - 1) / (time[-1] - time[0])
                ),
                "median_dt_rate_hz": float(1.0 / np.median(delta)),
                "non_finite": int((~np.isfinite(values)).sum()),
            }
        )

    return result


def plot_recording(path, channels):
    info = recording_info(path)
    figure, axes = plt.subplots(
        len(channels),
        1,
        figsize=(10, 7),
        sharex=True,
    )

    for axis, channel in zip(axes, channels):
        axis.plot(
            channel["time"],
            channel["values"],
            linewidth=0.4,
        )
        axis.set_ylabel(channel["name"])
        axis.grid(alpha=0.25)

    axes[-1].set_xlabel("Time (s)")
    figure.suptitle(
        "{} | {} | {}".format(
            info["bearing_id"],
            info["condition"],
            path.stem,
        )
    )
    figure.tight_layout()
    figure.savefig(
        OUTPUT_DIR / "{}.png".format(path.stem),
        dpi=150,
    )
    plt.close(figure)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []

    for path in RECORDINGS:
        info = recording_info(path)
        channels = read_recording(path)
        plot_recording(path, channels)

        end_times = [channel["time_end_s"] for channel in channels]
        print()
        print("Recording:", path)
        print("  bearing:", info["bearing_id"])
        print("  condition:", info["condition"])
        print("  recording_id:", info["recording_id"])
        print("  sync end-time spread:", max(end_times) - min(end_times))

        for channel in channels:
            summary = {
                **info,
                "source_file": str(path),
                **{
                    key: value
                    for key, value in channel.items()
                    if key not in {"time", "values"}
                },
            }
            summaries.append(summary)
            print(
                "  {name}: samples={samples}, duration={duration_s:.6f}s, "
                "mean_rate={mean_rate_hz:.2f}Hz, unit={unit}, "
                "non_finite={non_finite}".format(**channel)
            )

    with (OUTPUT_DIR / "recording_summary.json").open("w") as file:
        json.dump(summaries, file, indent=2)

    print()
    print("Saved:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
