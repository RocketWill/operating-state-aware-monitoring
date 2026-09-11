'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/run_paderborn_matched_vibration_baseline.py
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
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    recall_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


DATA_DIR = Path("data/paderborn/raw")
PROTOCOL_DIR = Path("outputs/paderborn_protocol")
OUTPUT_DIR = Path("outputs/paderborn_matched_vibration")
TEST_CONDITION = "N15_M07_F10"


def vibration_features(path):
    mat = loadmat(path, simplify_cells=True)
    record = mat[path.stem]
    channel = next(item for item in record["Y"] if item["Name"] == "vibration_1")
    values = np.asarray(channel["Data"], dtype=float)
    return [
        float(values.mean()),
        float(values.std()),
        float(np.sqrt(np.mean(values**2))),
        float(np.ptp(values)),
    ]


def load_rows():
    with (PROTOCOL_DIR / "recording_manifest.csv").open() as file:
        manifest = list(csv.DictReader(file))

    rows = []
    for item in manifest:
        if item["condition"] != TEST_CONDITION:
            continue
        if item["include_primary"] != "true" or item["include_recording"] != "true":
            continue
        path = DATA_DIR / item["bearing_id"] / item["filename"]
        rows.append(
            {
                **item,
                "path": str(path),
                "label_id": 0 if item["label"] == "healthy" else 1,
                "features": vibration_features(path),
            }
        )
    return rows


def score(y_true, y_pred):
    return {
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "recall": recall_score(y_true, y_pred, labels=[0, 1], average=None).tolist(),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    folds = json.loads((PROTOCOL_DIR / "protocol.json").read_text())["folds"]
    fold_by_bearing = {
        bearing_id: fold_id
        for fold_id, bearing_ids in folds.items()
        for bearing_id in bearing_ids
    }

    predictions = []
    fold_metrics = []
    for fold_id, test_bearings in folds.items():
        train = [row for row in rows if row["bearing_id"] not in test_bearings]
        test = [row for row in rows if row["bearing_id"] in test_bearings]
        X_train = np.asarray([row["features"] for row in train])
        X_test = np.asarray([row["features"] for row in test])
        y_train = np.asarray([row["label_id"] for row in train])
        y_test = np.asarray([row["label_id"] for row in test])

        models = {
            "dummy": DummyClassifier(strategy="most_frequent"),
            "logistic": make_pipeline(
                StandardScaler(),
                LogisticRegression(C=1.0, max_iter=1000),
            ),
        }
        fold_result = {"fold": fold_id, "train_rows": len(train), "test_rows": len(test)}
        for model_name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            fold_result[model_name] = score(y_test, y_pred)
            for row, prediction in zip(test, y_pred):
                predictions.append(
                    {
                        "model": model_name,
                        "fold": fold_id,
                        "bearing_id": row["bearing_id"],
                        "condition": row["condition"],
                        "recording_id": row["recording_id"],
                        "true_label": row["label_id"],
                        "predicted_label": int(prediction),
                    }
                )
        fold_metrics.append(fold_result)

    pooled = {}
    for model_name in ("dummy", "logistic"):
        model_rows = [row for row in predictions if row["model"] == model_name]
        pooled[model_name] = score(
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
        "condition": TEST_CONDITION,
        "sensor_group": "vibration_1",
        "features": ["mean", "std", "rms", "peak_to_peak"],
        "model": "StandardScaler + LogisticRegression(C=1.0, max_iter=1000)",
        "dummy": "most_frequent",
        "split": "fixed bearing-level folds from outputs/paderborn_protocol/protocol.json",
        "rows": len(rows),
        "bearings": sorted({row["bearing_id"] for row in rows}),
        "fold_assignment": fold_by_bearing,
        "fold_metrics": fold_metrics,
        "pooled_metrics": pooled,
    }
    (OUTPUT_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    print(f"rows: {len(rows)}")
    print(f"bearings: {len({row['bearing_id'] for row in rows})}")
    for model_name, result in pooled.items():
        print(f"{model_name}: macro_f1={result['macro_f1']:.4f}")
    print(f"saved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
