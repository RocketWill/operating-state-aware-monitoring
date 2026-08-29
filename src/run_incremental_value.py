'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/run_incremental_value.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from read_single_cycle import CHANNELS
from run_first_baseline import (
    DATA_DIR,
    FEATURE_STATISTICS,
    LOGISTIC_C,
    LOGISTIC_L1_RATIO,
    LOGISTIC_MAX_ITER,
    LOGISTIC_SOLVER,
    N_SPLITS,
    RANDOM_STATE,
    TARGET_LABELS,
    build_features,
    calculate_metrics,
    create_logistic_model,
    load_profile,
    make_metric_record,
    print_metrics,
    select_eligible_cycles,
    target_counts,
)
from run_family_comparison import (
    MEASUREMENT_FAMILIES,
    build_split_records,
    create_cross_validation_dataset,
)


OUTPUT_DIR = Path("outputs/incremental_value")

EXPECTED_FEATURE_COUNTS = {
    "hydraulic": 32,
    "hydraulic_plus_motor_power": 32 + 4,
    "hydraulic_plus_temperature": 32 + 16,
    "hydraulic_plus_vibration": 32 + 4,
    "all_measurements": 32 + 4 + 16 + 4,
}

MEASUREMENT_INCREMENTAL = {
    "hydraulic": MEASUREMENT_FAMILIES["hydraulic"],
    "hydraulic_plus_motor_power": (
        MEASUREMENT_FAMILIES["hydraulic"]
        + MEASUREMENT_FAMILIES["motor_power"]
    ),
    "hydraulic_plus_temperature": (
        MEASUREMENT_FAMILIES["hydraulic"]
        + MEASUREMENT_FAMILIES["temperature"]
    ),
    "hydraulic_plus_vibration": (
        MEASUREMENT_FAMILIES["hydraulic"]
        + MEASUREMENT_FAMILIES["vibration"]
    ),
    "all_measurements": (
        MEASUREMENT_FAMILIES["hydraulic"]
        + MEASUREMENT_FAMILIES["motor_power"]
        + MEASUREMENT_FAMILIES["temperature"]
        + MEASUREMENT_FAMILIES["vibration"]
    ),
}


def validate_family_definitions():
    # CE and CP are virtual quantities; SE is unresolved in the source audit.
    excluded_channels = {"CE", "CP", "SE"}

    for incremental, channels in MEASUREMENT_INCREMENTAL.items():
        assert len(channels) == len(set(channels))
        assert set(channels).issubset(CHANNELS)
        assert excluded_channels.isdisjoint(channels)

        feature_count = len(channels) * len(FEATURE_STATISTICS)

        assert feature_count == EXPECTED_FEATURE_COUNTS[incremental]


def create_result_table(y):
    return pd.DataFrame(
        index=y.index,
        columns=list(MEASUREMENT_INCREMENTAL.keys()),
        dtype="Int64",
    )


def make_result_delta(records):
    baseline_record = next(
        record
        for record in records
        if record["incremental"] == "hydraulic"
    )
    record_deltas = []

    for record in records:
        per_class_recall_delta = {}

        for label, score in record["per_class_recall"].items():
            assert label in baseline_record["per_class_recall"]
            per_class_recall_delta[label] = (
                score - baseline_record["per_class_recall"][label]
            )

        record_deltas.append(
            {
                "reference": "hydraulic",
                "incremental": record["incremental"],
                "method": record["method"],
                "aggregation": record["aggregation"],
                "sample_count": record["sample_count"],
                "macro_f1": (
                    record["macro_f1"]
                    - baseline_record["macro_f1"]
                ),
                "balanced_accuracy": (
                    record["balanced_accuracy"]
                    - baseline_record["balanced_accuracy"]
                ),
                "per_class_recall": per_class_recall_delta,
            }
        )

    return record_deltas


def build_measurement_metadata(incremental, shape):
    channels = MEASUREMENT_INCREMENTAL[incremental]

    return {
        "channels": channels,
        "measurements": {
            channel: {
                "quantity": CHANNELS[channel]["quantity"],
                "sampling_rate_hz": CHANNELS[channel]["rate"],
                "unit": CHANNELS[channel]["unit"],
            }
            for channel in channels
        },
        "statistics": FEATURE_STATISTICS,
        "shape": [int(shape[0]), int(shape[1])],
    }


def build_run_metadata(
    profile,
    eligible_profile,
    y,
    groups,
    incremental_shapes,
    split_records,
    fold_metric_records,
    pooled_oof_metrics,
    result_deltas,
    prediction_file,
):
    group_size_counts = (
        eligible_profile["group"]
        .value_counts()
        .value_counts()
        .sort_index()
    )

    combinations = {
        incremental: build_measurement_metadata(
            incremental,
            incremental_shapes[incremental],
        )
        for incremental in MEASUREMENT_INCREMENTAL
    }

    return {
        "source_script": "src/run_incremental_value.py",
        "command": (
            "conda run --no-capture-output -n windfusion "
            "python src/run_incremental_value.py"
        ),
        "environment": {
            "conda_environment": os.environ.get(
                "CONDA_DEFAULT_ENV"
            ),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
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
        },
        "target": {
            "column": "pump_leakage",
            "labels": TARGET_LABELS,
            "counts": target_counts(y),
        },
        "combinations": combinations,
        "groups": {
            "columns": [
                "cooler_condition",
                "valve_condition",
                "pump_leakage",
                "accumulator_pressure",
            ],
            "rule": (
                "A new group starts when condition labels change "
                "or the original cycle index is not consecutive."
            ),
            "count": int(groups.nunique()),
            "size_counts": {
                str(size): int(count)
                for size, count in group_size_counts.items()
            },
        },
        "split": {
            "method": "StratifiedGroupKFold",
            "n_splits": N_SPLITS,
            "shuffle": True,
            "random_state": RANDOM_STATE,
            "preprocessing": (
                "StandardScaler is fit inside each training fold."
            ),
            "folds": split_records,
        },
        "model": {
            "name": "logistic_regression",
            "tuning": (
                "No combination-specific tuning; "
                "fixed settings are shared."
            ),
            "C": LOGISTIC_C,
            "l1_ratio": LOGISTIC_L1_RATIO,
            "effective_regularization": "l2",
            "solver": LOGISTIC_SOLVER,
            "max_iter": LOGISTIC_MAX_ITER,
            "random_state": RANDOM_STATE,
        },
        "metric_reporting": {
            "primary": "macro_f1",
            "secondary": [
                "balanced_accuracy",
                "per_class_recall",
                "confusion_matrix",
            ],
            "aggregation": "pooled_oof",
            "delta_reference": "hydraulic",
        },
        "results": {
            "fold_metrics": fold_metric_records,
            "pooled_oof_metrics": pooled_oof_metrics,
            "delta_metrics": result_deltas,
            "prediction_file": prediction_file,
        },
    }


def print_oof_summary(y, oof_pred):
    records = []

    for incremental in MEASUREMENT_INCREMENTAL:
        metrics = calculate_metrics(
            y,
            oof_pred[incremental],
        )

        print()
        print(
            f"{incremental.capitalize()} logistic_regression "
            "pooled OOF summary"
        )
        print(f"  macro-F1: {metrics['macro_f1']:.4f}")
        print(
            "  balanced accuracy: "
            f"{metrics['balanced_accuracy']:.4f}"
        )

        recall_text = ", ".join(
            f"class{label}={score:.4f}"
            for label, score in zip(
                TARGET_LABELS,
                metrics["recall"],
            )
        )

        print(f"  recall: {recall_text}")

        print("  confusion matrix:")
        print(metrics["confusion_matrix"])

        record = make_metric_record(
            "logistic_regression",
            "pooled_oof",
            metrics,
            len(y),
        )
        record["incremental"] = incremental
        records.append(record)

    return records


def main():
    validate_family_definitions()
    profile = load_profile()
    eligible_profile = select_eligible_cycles(
        profile
    )
    y = eligible_profile["pump_leakage"].copy()
    groups = eligible_profile["group"].copy()

    oof_pred = create_result_table(y)
    cv_splits = create_cross_validation_dataset(y, groups)
    fold_ids, split_records = build_split_records(
        y,
        groups,
        cv_splits,
    )

    incremental_shapes = {}
    fold_metric_records = []

    for incremental, channels in MEASUREMENT_INCREMENTAL.items():
        X = build_features(eligible_profile, channels)
        incremental_shapes[incremental] = X.shape

        print()
        print("Incremental:", incremental)
        print("X shape:", X.shape)
        print("y shape:", y.shape)
        print("groups shape:", groups.shape)

        assert X.index.equals(y.index)
        assert not X.isna().any().any()

        for fold, (train_idx, test_idx) in enumerate(
            cv_splits,
            start=1,
        ):
            X_train = X.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_train = y.iloc[train_idx]
            y_test = y.iloc[test_idx]

            model = create_logistic_model()
            model.fit(X_train, y_train)

            pred = model.predict(X_test)
            metrics = calculate_metrics(y_test, pred)
            print_metrics(
                "{}-{} logistic".format(
                    incremental,
                    str(fold).zfill(2),
                ),
                metrics,
            )

            record = make_metric_record(
                "logistic_regression",
                "fold",
                metrics,
                len(y_test),
                split_records[fold - 1],
            )
            record["incremental"] = incremental
            fold_metric_records.append(record)

            test_index = y_test.index
            oof_pred.loc[test_index, incremental] = pred

    assert not oof_pred.isna().any().any()

    pooled_oof_metrics = print_oof_summary(
        y,
        oof_pred,
    )
    result_deltas = make_result_delta(pooled_oof_metrics)

    print()
    print("Delta vs hydraulic:")
    for delta in result_deltas:
        print(
            f"  {delta['incremental']} macro-F1: "
            f"{delta['macro_f1']:+.4f}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions = pd.DataFrame(
        {
            "cycle_index": y.index,
            "group": groups.values,
            "fold": fold_ids.values,
            "true_pump_leakage": y.values,
        }
    )

    for incremental in MEASUREMENT_INCREMENTAL:
        predictions[
            f"predicted_{incremental}"
        ] = oof_pred[incremental].values

    prediction_path = OUTPUT_DIR / "incremental_value_predictions.csv"
    predictions.to_csv(
        prediction_path,
        index=False,
    )

    print()
    print(f"Saved predictions to: {prediction_path}")

    metadata = build_run_metadata(
        profile,
        eligible_profile,
        y,
        groups,
        incremental_shapes,
        split_records,
        fold_metric_records,
        pooled_oof_metrics,
        result_deltas,
        str(prediction_path),
    )

    metadata_path = OUTPUT_DIR / "run_metadata.json"
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
    print(f"Saved run metadata to: {metadata_path}")


if __name__ == "__main__":
    main()
