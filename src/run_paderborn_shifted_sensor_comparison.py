'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/run_paderborn_shifted_sensor_comparison.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import csv
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


DATA_DIR = Path("data/paderborn/raw")
PROTOCOL_DIR = Path("outputs/paderborn_protocol")
OUTPUT_DIR = Path("outputs/paderborn_shifted_sensor_comparison")
TEST_CONDITION = "N15_M07_F10"
SHIFT_CONDITIONS = ["N09_M07_F10", "N15_M01_F10", "N15_M07_F04"]
SENSOR_GROUPS = {
    "current": ["phase_current_1", "phase_current_2"],
    "vibration": ["vibration_1"],
    "combined": ["phase_current_1", "phase_current_2", "vibration_1"],
}


def signal_features(values):
    return [
        float(values.mean()),
        float(values.std()),
        float(np.sqrt(np.mean(values**2))),
        float(np.ptp(values)),
    ]


def load_features(path):
    mat = loadmat(path, simplify_cells=True)
    record = mat[path.stem]
    channels = {item["Name"]: item for item in record["Y"]}
    names = sorted({name for group in SENSOR_GROUPS.values() for name in group})
    return {
        name: signal_features(np.asarray(channels[name]["Data"], dtype=float))
        for name in names
    }


def load_rows():
    with (PROTOCOL_DIR / "recording_manifest.csv").open() as file:
        manifest = list(csv.DictReader(file))

    rows = []
    for item in manifest:
        if item["include_primary"] != "true" or item["include_recording"] != "true":
            continue
        path = DATA_DIR / item["bearing_id"] / item["filename"]
        rows.append(
            {
                **item,
                "recording_id": int(item["recording_id"]),
                "label_id": 0 if item["label"] == "healthy" else 1,
                "features": load_features(path),
            }
        )
    return rows


def shifted_train(rows, bearing_id):
    by_key = {
        (row["condition"], row["recording_id"]): row
        for row in rows
        if row["bearing_id"] == bearing_id
    }
    selected = []
    for recording_id in range(1, 21):
        start = (recording_id - 1) % len(SHIFT_CONDITIONS)
        for offset in range(len(SHIFT_CONDITIONS)):
            condition = SHIFT_CONDITIONS[(start + offset) % len(SHIFT_CONDITIONS)]
            row = by_key.get((condition, recording_id))
            if row is not None:
                selected.append(row)
                break
    return selected


def score(y_true, y_pred):
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    folds = json.loads((PROTOCOL_DIR / "protocol.json").read_text())["folds"]
    predictions = []

    for fold_id, test_bearings in folds.items():
        train_bearings = [
            bearing_id
            for bearing_id in sorted({row["bearing_id"] for row in rows})
            if bearing_id not in test_bearings
        ]
        test = [
            row
            for row in rows
            if row["bearing_id"] in test_bearings
            and row["condition"] == TEST_CONDITION
        ]
        train_sets = {
            "matched": [
                row
                for row in rows
                if row["bearing_id"] in train_bearings
                and row["condition"] == TEST_CONDITION
            ],
            "shifted": [
                row
                for bearing_id in train_bearings
                for row in shifted_train(rows, bearing_id)
            ],
        }

        for scenario, train in train_sets.items():
            for group_name, channel_names in SENSOR_GROUPS.items():
                X_train = np.asarray(
                    [sum((row["features"][name] for name in channel_names), []) for row in train]
                )
                X_test = np.asarray(
                    [sum((row["features"][name] for name in channel_names), []) for row in test]
                )
                y_train = np.asarray([row["label_id"] for row in train])

                models = {
                    "dummy": DummyClassifier(strategy="most_frequent"),
                    "logistic": make_pipeline(
                        StandardScaler(),
                        LogisticRegression(C=1.0, max_iter=1000),
                    ),
                }
                for model_name, model in models.items():
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    for row, prediction in zip(test, y_pred):
                        predictions.append(
                            {
                                "scenario": scenario,
                                "sensor_group": group_name,
                                "model": model_name,
                                "fold": fold_id,
                                "bearing_id": row["bearing_id"],
                                "recording_id": row["recording_id"],
                                "true_label": row["label_id"],
                                "predicted_label": int(prediction),
                            }
                        )

    pooled = {}
    for scenario in ("matched", "shifted"):
        pooled[scenario] = {}
        for group_name in SENSOR_GROUPS:
            pooled[scenario][group_name] = {}
            for model_name in ("dummy", "logistic"):
                model_rows = [
                    row
                    for row in predictions
                    if row["scenario"] == scenario
                    and row["sensor_group"] == group_name
                    and row["model"] == model_name
                ]
                pooled[scenario][group_name][model_name] = score(
                    [row["true_label"] for row in model_rows],
                    [row["predicted_label"] for row in model_rows],
                )

    with (OUTPUT_DIR / "predictions.csv").open("w", newline="") as file:
        fields = list(predictions[0].keys())
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(predictions)

    metadata = {
        "environment": "windfusion",
        "target": "healthy=0, damaged=1",
        "test_condition": TEST_CONDITION,
        "shift_conditions": SHIFT_CONDITIONS,
        "sensor_groups": SENSOR_GROUPS,
        "features": ["mean", "std", "rms", "peak_to_peak"],
        "model": "StandardScaler + LogisticRegression(C=1.0, max_iter=1000)",
        "dummy": "most_frequent",
        "split": "fixed bearing-level folds from outputs/paderborn_protocol/protocol.json",
        "shifted_sampling": "cycle shift conditions by recording_id, skip excluded rows",
        "test_rows_per_scenario": len(predictions) // 12,
        "pooled_metrics": pooled,
    }
    (OUTPUT_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    print(f"loaded rows: {len(rows)}")
    for scenario in ("matched", "shifted"):
        for group_name in SENSOR_GROUPS:
            result = pooled[scenario][group_name]["logistic"]
            print(
                f"{scenario} {group_name}: accuracy={result['accuracy']:.4f}, "
                f"macro_f1={result['macro_f1']:.4f}"
            )
    print(f"saved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
