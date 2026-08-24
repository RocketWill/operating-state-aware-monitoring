from pathlib import Path

import pandas as pd


data_dir = Path("data/hydraulic/raw")

for path in sorted(data_dir.glob("*.txt")):
    try:
        if path.name in ('description.txt', 'documentation.txt'):
            continue
        df = pd.read_csv(path, sep="\t", header=None)
        print(f"{path.name:<15} {df.shape}")
        if path.name == "profile.txt":
            df.columns = [
                "cooler_condition",
                "valve_condition",
                "pump_leakage",
                "accumulator_pressure",
                "stable_flag",
            ]

            print(df.head(10))
            print()

            for col in df.columns:
                print(f"\n{col}")
                print(df[col].value_counts().sort_index())
    except Exception as e:
        print(f"{path.name:<15} ERROR: {e}")
