'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/audit_target_feasibility.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
from pathlib import Path

import pandas as pd


PROFILE_PATH = Path("data/hydraulic/raw/profile.txt")

COLUMNS = [
    "cooler_condition",
    "valve_condition",
    "pump_leakage",
    "accumulator_pressure",
    "stable_flag",
]

profile = pd.read_csv(
    PROFILE_PATH,
    sep="\t",
    header=None,
    names=COLUMNS,
)

print(profile.shape)
print(profile.head())

print("\n=== Pump leakage class counts ===")
print(
    profile["pump_leakage"]
    .value_counts()
    .sort_index()
)

print("\n=== Pump leakage class proportions ===")
print(
    profile["pump_leakage"]
    .value_counts(normalize=True)
    .sort_index()
    .round(4)
)

other_conditions = [
    "cooler_condition",
    "valve_condition",
    "accumulator_pressure",
    "stable_flag",
]

for col in other_conditions:
    print(f"\n=== pump_leakage × {col} ===")
    print(
        pd.crosstab(
            profile["pump_leakage"],
            profile[col],
        )
    )

condition_cols = [
    "cooler_condition",
    "valve_condition",
    "pump_leakage",
    "accumulator_pressure",
    "stable_flag",
]

combinations = (
    profile
    .groupby(condition_cols)
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

print("\n=== Full condition combinations ===")
print(combinations.to_string(index=False))

print(f"\nNumber of unique combinations: {len(combinations)}")

stable = profile[profile["stable_flag"] == 0]

print("Stable subset shape:", stable.shape)

for col in [
    "cooler_condition",
    "valve_condition",
    "accumulator_pressure",
]:
    print(f"\n=== pump_leakage × {col} (stable=0) ===")
    print(
        pd.crosstab(
            stable["pump_leakage"],
            stable[col],
        )
    )

condition_counts = (
    stable
    .groupby([
        "cooler_condition",
        "valve_condition",
        "pump_leakage",
        "accumulator_pressure",
    ])
    .size()
)

print(condition_counts.value_counts().sort_index())
print("Number of combinations:", len(condition_counts))


condition_cols = [
    "cooler_condition",
    "valve_condition",
    "pump_leakage",
    "accumulator_pressure",
]

stable = profile[profile["stable_flag"] == 0].copy()

# Condition changed compared with previous remaining row
condition_changed = (
    stable[condition_cols]
    .ne(stable[condition_cols].shift())
    .any(axis=1)
)

# Original row index is no longer consecutive
index_gap = stable.index.to_series().diff().ne(1)

# A new block starts if either happens
new_block = condition_changed | index_gap

stable["block_id"] = new_block.cumsum()

blocks = (
    stable
    .groupby("block_id")
    .agg(
        start_row=("pump_leakage", lambda x: x.index.min()),
        end_row=("pump_leakage", lambda x: x.index.max()),
        cycles=("pump_leakage", "size"),
        cooler=("cooler_condition", "first"),
        valve=("valve_condition", "first"),
        pump=("pump_leakage", "first"),
        accumulator=("accumulator_pressure", "first"),
    )
)

print("Number of blocks:", len(blocks))
print()
print(blocks["cycles"].value_counts().sort_index())
print()
print(blocks.head(30))
