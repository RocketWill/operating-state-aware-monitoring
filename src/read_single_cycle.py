'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/read_single_cycle.py
Description: 

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved. 
'''
from pathlib import Path

import pandas as pd
import numpy as np


DATA_DIR = Path("data/hydraulic/raw")
CYCLE_INDEX = 211
EXPECTED_CYCLES = 2205
EXPECTED_DURATION_S = 60.0

CHANNELS = {
    "PS1": {"quantity": "Pressure", "rate": 100, "samples": 6000, "unit": "bar"},
    "PS2": {"quantity": "Pressure", "rate": 100, "samples": 6000, "unit": "bar"},
    "PS3": {"quantity": "Pressure", "rate": 100, "samples": 6000, "unit": "bar"},
    "PS4": {"quantity": "Pressure", "rate": 100, "samples": 6000, "unit": "bar"},
    "PS5": {"quantity": "Pressure", "rate": 100, "samples": 6000, "unit": "bar"},
    "PS6": {"quantity": "Pressure", "rate": 100, "samples": 6000, "unit": "bar"},

    "EPS1": {"quantity": "Motor power", "rate": 100, "samples": 6000, "unit": "W"},

    "FS1": {"quantity": "Volume flow", "rate": 10, "samples": 600, "unit": "l/min"},
    "FS2": {"quantity": "Volume flow", "rate": 10, "samples": 600, "unit": "l/min"},

    "TS1": {"quantity": "Temperature", "rate": 1, "samples": 60, "unit": "°C"},
    "TS2": {"quantity": "Temperature", "rate": 1, "samples": 60, "unit": "°C"},
    "TS3": {"quantity": "Temperature", "rate": 1, "samples": 60, "unit": "°C"},
    "TS4": {"quantity": "Temperature", "rate": 1, "samples": 60, "unit": "°C"},

    "VS1": {"quantity": "Vibration", "rate": 1, "samples": 60, "unit": "mm/s"},

    "CE": {"quantity": "Cooling efficiency", "rate": 1, "samples": 60, "unit": "%"},
    "CP": {"quantity": "Cooling power", "rate": 1, "samples": 60, "unit": "kW"},
    "SE": {"quantity": "Efficiency factor", "rate": 1, "samples": 60, "unit": "%"},
}

PROFILE_COLUMNS = [
    "cooler_condition",
    "valve_condition",
    "pump_leakage",
    "accumulator_pressure",
    "stable_flag",
]

# Channels printed again with detailed time/value dumps,
# and the time format used for each one.
DETAIL_CHANNELS = {
    "PS1": "{:.2f}",
    "FS1": "{:.1f}",
    "TS1": "{:.0f}",
}


def read_cycle(path: Path, cycle_index: int, expected_samples: int) -> pd.Series:
    """Read and validate a single cycle row from a channel file."""
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path, sep="\t", header=None)

    if len(df) != EXPECTED_CYCLES:
        raise ValueError(
            f"{path.name}: expected {EXPECTED_CYCLES} cycles, "
            f"got {len(df)}"
        )

    if cycle_index < 0 or cycle_index >= len(df):
        raise IndexError(
            f"cycle_index={cycle_index} is out of range "
            f"for {path.name} with {len(df)} cycles"
        )

    cycle = df.iloc[cycle_index]

    if len(cycle) != expected_samples:
        raise ValueError(
            f"{path.name}: expected {expected_samples} samples, "
            f"got {len(cycle)}"
        )

    if cycle.isna().any():
        raise ValueError(
            f"{path.name}: missing value found "
            f"in cycle {cycle_index}"
        )

    return cycle


def read_profile(path: Path, cycle_index: int) -> pd.Series:
    """Read and validate the label profile, returning one cycle's labels."""
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    profile = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=PROFILE_COLUMNS,
    )

    if len(profile) != EXPECTED_CYCLES:
        raise ValueError(
            f"profile.txt: expected {EXPECTED_CYCLES} cycles, "
            f"got {len(profile)}"
        )

    if cycle_index < 0 or cycle_index >= len(profile):
        raise IndexError(
            f"cycle_index={cycle_index} is out of range "
            f"for {len(profile)} cycles"
        )
    
    profile_cycle = profile.iloc[cycle_index]
    if profile_cycle.isna().any():
        missing_fields = profile_cycle[profile_cycle.isna()].index.tolist()
        raise ValueError(
            f"profile.txt: missing value found in cycle {cycle_index}: "
            f"{missing_fields}"
        )

    return profile.iloc[cycle_index]


def load_channel(name: str, meta: dict) -> pd.Series:
    """Load one channel cycle and validate its duration."""
    cycle = read_cycle(
        DATA_DIR / f"{name}.txt",
        CYCLE_INDEX,
        expected_samples=meta["samples"],
    )

    duration = len(cycle) / meta["rate"]
    if duration != EXPECTED_DURATION_S:
        raise ValueError(
            f"{name}: expected duration {EXPECTED_DURATION_S}s, "
            f"got {duration}s"
        )

    return cycle


def summarize_channels() -> None:
    """Print the overview line for every channel."""
    print()
    print("All channels:")

    for name, meta in CHANNELS.items():
        cycle = load_channel(name, meta)
        rate = meta["rate"]
        time = np.arange(len(cycle)) / rate

        print(
            f"  {name:<4} "
            f"{meta['quantity']:<20} "
            f"samples={len(cycle):<4} "
            f"rate={rate:<3} Hz "
            f"duration={len(cycle) / rate:.1f} s "
            f"time={time[0]:.2f}..{time[-1]:.2f} s "
            f"value={cycle.iloc[0]}..{cycle.iloc[-1]} "
            f"unit={meta['unit']}"
        )


def print_labels(cycle_label: pd.Series) -> None:
    """Print the label values for the selected cycle."""
    print(f"Cycle index: {CYCLE_INDEX}")
    print()
    print("Labels:")

    for name, value in cycle_label.items():
        print(f"  {name}: {value}")


def print_channel_detail(name: str, time_fmt: str) -> None:
    """Print samples, timing and first values for one channel."""
    meta = CHANNELS[name]
    rate = meta["rate"]

    cycle = read_cycle(
        DATA_DIR / f"{name}.txt",
        CYCLE_INDEX,
        expected_samples=meta["samples"],
    )
    time = np.arange(len(cycle)) / rate

    print()
    print(f"{name}:")
    print(f"  samples: {len(cycle)}")
    print(f"  first 5 values: {cycle.iloc[:5].tolist()}")
    print(f"  rate: {rate} Hz")
    print(f"  time start: {time_fmt.format(time[0])} s")
    print(f"  time end: {time_fmt.format(time[-1])} s")
    print(f"  duration: {len(cycle) / rate:.1f} s")

    print("  first 5 time/value pairs:")
    for t, value in zip(time[:5], cycle.iloc[:5]):
        print(f"    {time_fmt.format(t)} s -> {value}")


def main() -> None:
    summarize_channels()

    cycle_label = read_profile(DATA_DIR / "profile.txt", CYCLE_INDEX)
    print_labels(cycle_label)

    for name, time_fmt in DETAIL_CHANNELS.items():
        print_channel_detail(name, time_fmt)


if __name__ == "__main__":
    main()