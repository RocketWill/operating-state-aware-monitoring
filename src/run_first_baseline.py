"""
Author: Will Cheng <will.chengyong@gmail.com>
LastEditors: Will Cheng <will.chengyong@gmail.com>
FilePath: /operating-state-aware-monitoring/src/run_first_baseline.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com.
All Rights Reserved.
"""

import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


DATA_DIR = Path("data/hydraulic/raw")

PROFILE_COLUMNS = [
    "cooler_condition",
    "valve_condition",
    "pump_leakage",
    "accumulator_pressure",
    "stable_flag",
]

CONDITION_COLUMNS = [
    "cooler_condition",
    "valve_condition",
    "pump_leakage",
    "accumulator_pressure",
]

FEATURE_CHANNELS = [
    "PS1",
    "PS2",
    "PS3",
    "PS4",
    "PS5",
    "PS6",
    "FS1",
    "FS2",
]

TARGET_LABELS = [0, 1, 2]
FEATURE_STATISTICS = ["mean", "std", "min", "max"]
N_SPLITS = 5
RANDOM_STATE = 42
DUMMY_STRATEGY = "most_frequent"
LOGISTIC_C = 1.0
LOGISTIC_L1_RATIO = 0.0
LOGISTIC_SOLVER = "lbfgs"
LOGISTIC_MAX_ITER = 1000
OUTPUT_DIR = Path("outputs/first_baseline")

METHOD_OUTPUT_COLUMNS = {
    "dummy": "predicted_dummy",
    "logistic_regression": "predicted_logistic",
}
OOF_COLUMNS = list(METHOD_OUTPUT_COLUMNS.values())
OUTPUT_COLUMN_METHODS = {
    column: method
    for method, column in METHOD_OUTPUT_COLUMNS.items()
}
METHOD_LABELS = {
    "dummy": "Dummy",
    "logistic_regression": "Logistic regression",
}


def load_profile():
    profile = pd.read_csv(
        DATA_DIR / "profile.txt",
        sep="\t",
        header=None,
        names=PROFILE_COLUMNS,
    )

    if profile.isna().any().any():
        missing_columns = profile.columns[
            profile.isna().any()
        ].tolist()
        raise ValueError(
            "Profile contains missing values in: "
            f"{missing_columns}"
        )

    print("Profile shape:", profile.shape)

    return profile


def extract_cycle_features(data, prefix):
    return pd.DataFrame(
        {
            f"{prefix}_mean": data.mean(
                axis=1,
                skipna=False,
            ),
            f"{prefix}_std": data.std(
                axis=1,
                skipna=False,
            ),
            f"{prefix}_min": data.min(
                axis=1,
                skipna=False,
            ),
            f"{prefix}_max": data.max(
                axis=1,
                skipna=False,
            ),
        },
        index=data.index,
    )


def select_eligible_cycles(profile):
    """
    Keep stable cycles and assign a group ID to each contiguous block
    of cycles sharing the same operating-condition labels.
    """
    eligible = profile.loc[profile["stable_flag"] == 0].copy()

    condition_changed = (
        eligible[CONDITION_COLUMNS]
        .ne(eligible[CONDITION_COLUMNS].shift())
        .any(axis=1)
    )

    index_gap = (
        eligible.index
        .to_series()
        .diff()
        .ne(1)
    )

    new_block = condition_changed | index_gap
    eligible["group"] = new_block.cumsum()

    print()
    print("Eligible cycles:", len(eligible))

    print()
    print("Target counts:")
    print(
        eligible["pump_leakage"]
        .value_counts()
        .sort_index()
    )

    print()
    print("Groups:", eligible["group"].nunique())

    print()
    print("Cycles per group:")
    print(
        eligible
        .groupby("group")
        .size()
        .value_counts()
        .sort_index()
    )

    return eligible


def load_channel(channel, indices):
    data = pd.read_csv(
        DATA_DIR / f"{channel}.txt",
        sep="\t",
        header=None,
    )

    selected = data.loc[indices]

    if selected.isna().any().any():
        missing_rows = selected.index[
            selected.isna().any(axis=1)
        ].tolist()
        raise ValueError(
            f"{channel} contains missing values in cycles: "
            f"{missing_rows[:10]}"
        )

    return selected


def build_features(profile, channels):
    feature_tables = []

    for channel in channels:
        data = load_channel(
            channel,
            profile.index,
        )

        features = extract_cycle_features(
            data,
            channel,
        )

        feature_tables.append(features)

    return pd.concat(
        feature_tables,
        axis=1,
    )


def calculate_metrics(y_true, y_pred):
    recall = recall_score(
        y_true,
        y_pred,
        labels=TARGET_LABELS,
        average=None,
    )

    return {
        "macro_f1": f1_score(
            y_true,
            y_pred,
            average="macro",
        ),
        "balanced_accuracy": balanced_accuracy_score(
            y_true,
            y_pred,
        ),
        "recall": recall,
        "confusion_matrix": confusion_matrix(
            y_true,
            y_pred,
            labels=TARGET_LABELS,
        ),
    }


def target_counts(series):
    counts = series.value_counts()

    return {
        str(label): int(counts.get(label, 0))
        for label in TARGET_LABELS
    }


def make_metric_record(
    method,
    aggregation,
    metrics,
    sample_count,
    split_context=None,
):
    record = {
        "method": method,
        "aggregation": aggregation,
        "sample_count": int(sample_count),
        "macro_f1": float(metrics["macro_f1"]),
        "balanced_accuracy": float(
            metrics["balanced_accuracy"]
        ),
        "per_class_recall": {
            str(label): float(score)
            for label, score in zip(
                TARGET_LABELS,
                metrics["recall"],
            )
        },
        "confusion_matrix": [
            [int(value) for value in row]
            for row in metrics["confusion_matrix"]
        ],
    }

    if split_context is not None:
        record["split"] = split_context

    return record


def print_metrics(name, metrics):
    recall = metrics["recall"]

    recall_text = ", ".join(
        f"class{label}={score:.4f}"
        for label, score in zip(TARGET_LABELS, recall)
    )

    print(f"  {name} macro-F1: {metrics['macro_f1']:.4f}")
    print(
        f"  {name} balanced accuracy: "
        f"{metrics['balanced_accuracy']:.4f}"
    )

    print(f"  {name} recall: {recall_text}")

    print(f"  {name} confusion matrix:")
    print(metrics["confusion_matrix"])


def print_fold_summary(method, fold_metric_records):
    method_records = [
        record
        for record in fold_metric_records
        if record["method"] == method
    ]

    macro_f1_scores = [
        record["macro_f1"]
        for record in method_records
    ]
    balanced_acc_scores = [
        record["balanced_accuracy"]
        for record in method_records
    ]

    recall_scores = np.array(
        [
            [
                record["per_class_recall"][str(label)]
                for label in TARGET_LABELS
            ]
            for record in method_records
        ]
    )

    print()
    print(f"{METHOD_LABELS[method]} fold-average summary")

    print(
        "  macro-F1: "
        f"{np.mean(macro_f1_scores):.4f} "
        f"± {np.std(macro_f1_scores):.4f}"
    )

    print(
        "  balanced accuracy: "
        f"{np.mean(balanced_acc_scores):.4f} "
        f"± {np.std(balanced_acc_scores):.4f}"
    )

    return {
        "method": method,
        "aggregation": "fold_average",
        "sample_count": int(
            sum(record["sample_count"] for record in method_records)
        ),
        "macro_f1": float(np.mean(macro_f1_scores)),
        "macro_f1_std": float(np.std(macro_f1_scores)),
        "balanced_accuracy": float(
            np.mean(balanced_acc_scores)
        ),
        "balanced_accuracy_std": float(
            np.std(balanced_acc_scores)
        ),
        "per_class_recall": {
            str(label): float(score)
            for label, score in zip(
                TARGET_LABELS,
                recall_scores.mean(axis=0),
            )
        },
        "per_class_recall_std": {
            str(label): float(score)
            for label, score in zip(
                TARGET_LABELS,
                recall_scores.std(axis=0),
            )
        },
    }


def create_logistic_model():
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=LOGISTIC_C,
            l1_ratio=LOGISTIC_L1_RATIO,
            solver=LOGISTIC_SOLVER,
            max_iter=LOGISTIC_MAX_ITER,
            random_state=RANDOM_STATE,
        ),
    )


def run_cross_validation(X, y, groups):
    cv = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    oof_pred = pd.DataFrame(
        index=y.index,
        columns=OOF_COLUMNS,
        dtype="Int64",
    )

    fold_ids = pd.Series(
        index=y.index,
        dtype="Int64",
        name="fold",
    )
    fold_metric_records = []

    for fold, (train_idx, test_idx) in enumerate(
        cv.split(X, y, groups),
        start=1,
    ):
        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test = y.iloc[test_idx]

        train_groups = groups.iloc[train_idx]
        test_groups = groups.iloc[test_idx]

        assert set(train_groups).isdisjoint(
            set(test_groups)
        )

        print()
        print(f"Fold {fold}")
        print(f"  train cycles: {len(X_train)}")
        print(f"  test cycles:  {len(X_test)}")
        print(f"  train groups: {train_groups.nunique()}")
        print(f"  test groups:  {test_groups.nunique()}")

        print("  train target counts:")
        print(
            y_train
            .value_counts()
            .sort_index()
            .to_dict()
        )

        print("  test target counts:")
        print(
            y_test
            .value_counts()
            .sort_index()
            .to_dict()
        )

        split_context = {
            "fold": int(fold),
            "train_sample_count": int(len(X_train)),
            "test_sample_count": int(len(X_test)),
            "train_group_count": int(train_groups.nunique()),
            "test_group_count": int(test_groups.nunique()),
            "train_target_counts": target_counts(y_train),
            "test_target_counts": target_counts(y_test),
        }

        dummy = DummyClassifier(
            strategy=DUMMY_STRATEGY,
        )

        dummy.fit(
            X_train,
            y_train,
        )

        dummy_pred = dummy.predict(X_test)

        dummy_metrics = calculate_metrics(
            y_test,
            dummy_pred,
        )

        print_metrics(
            "dummy",
            dummy_metrics,
        )

        fold_metric_records.append(
            make_metric_record(
                "dummy",
                "fold",
                dummy_metrics,
                len(y_test),
                split_context,
            )
        )

        model = create_logistic_model()

        model.fit(
            X_train,
            y_train,
        )

        logistic_pred = model.predict(X_test)

        logistic_metrics = calculate_metrics(
            y_test,
            logistic_pred,
        )

        print_metrics(
            "logistic",
            logistic_metrics,
        )

        fold_metric_records.append(
            make_metric_record(
                "logistic_regression",
                "fold",
                logistic_metrics,
                len(y_test),
                split_context,
            )
        )

        test_index = y_test.index

        oof_pred.loc[test_index, OOF_COLUMNS[0]] = dummy_pred
        oof_pred.loc[test_index, OOF_COLUMNS[1]] = logistic_pred
        fold_ids.loc[test_index] = fold

    fold_summaries = [
        print_fold_summary(
            method,
            fold_metric_records,
        )
        for method in METHOD_OUTPUT_COLUMNS
    ]

    return (
        oof_pred,
        fold_ids,
        fold_metric_records,
        fold_summaries,
    )


def print_oof_summary(y, oof_pred):
    records = []

    for predicted_method in OOF_COLUMNS:
        metrics = calculate_metrics(
            y,
            oof_pred[predicted_method],
        )

        method = OUTPUT_COLUMN_METHODS[predicted_method]

        print()
        print(
            f"{METHOD_LABELS[method]} pooled OOF summary"
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

        records.append(
            make_metric_record(
                method,
                "pooled_oof",
                metrics,
                len(y),
            )
        )

    return records


def build_run_metadata(
    profile,
    eligible_profile,
    X,
    y,
    groups,
    fold_metric_records,
    fold_summaries,
    oof_metric_records,
    prediction_files,
):
    group_size_counts = (
        eligible_profile["group"]
        .value_counts()
        .value_counts()
        .sort_index()
    )

    return {
        "source_script": "src/run_first_baseline.py",
        "command": (
            "conda run --no-capture-output -n windfusion "
            "python src/run_first_baseline.py"
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
        "features": {
            "channels": FEATURE_CHANNELS,
            "statistics": FEATURE_STATISTICS,
            "shape": [int(X.shape[0]), int(X.shape[1])],
        },
        "groups": {
            "columns": CONDITION_COLUMNS,
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
        },
        "models": {
            "dummy": {
                "strategy": DUMMY_STRATEGY,
            },
            "logistic_regression": {
                "C": LOGISTIC_C,
                "l1_ratio": LOGISTIC_L1_RATIO,
                "effective_regularization": "l2",
                "solver": LOGISTIC_SOLVER,
                "max_iter": LOGISTIC_MAX_ITER,
                "random_state": RANDOM_STATE,
            },
        },
        "metric_reporting": {
            "primary": "macro_f1",
            "secondary": [
                "balanced_accuracy",
                "per_class_recall",
                "confusion_matrix",
            ],
            "aggregations": ["fold_average", "pooled_oof"],
        },
        "results": {
            "fold_metrics": fold_metric_records,
            "fold_summaries": fold_summaries,
            "pooled_oof_metrics": oof_metric_records,
            "prediction_files": prediction_files,
        },
    }


def main():
    profile = load_profile()

    eligible_profile = select_eligible_cycles(
        profile
    )

    X = build_features(
        eligible_profile,
        FEATURE_CHANNELS,
    )

    y = eligible_profile[
        "pump_leakage"
    ].copy()

    groups = eligible_profile[
        "group"
    ].copy()

    print()
    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print("groups shape:", groups.shape)

    print()
    print(X.head())

    assert X.index.equals(y.index)
    assert X.index.equals(groups.index)
    assert not X.isna().any().any()

    (
        oof_pred,
        fold_ids,
        fold_metric_records,
        fold_summaries,
    ) = run_cross_validation(
        X,
        y,
        groups,
    )

    assert not oof_pred.isna().any().any()
    assert not fold_ids.isna().any()

    oof_metric_records = print_oof_summary(
        y,
        oof_pred,
    )

    output_dir = OUTPUT_DIR
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    prediction_files = {}

    for predicted_method in OOF_COLUMNS:
        predictions = pd.DataFrame(
            {
                "cycle_index": y.index,
                "group": groups.values,
                "fold": fold_ids.values,
                "true_pump_leakage": y.values,
                "predicted_pump_leakage": oof_pred[predicted_method].values,
            }
        )

        output_path = output_dir / f"{predicted_method}_predictions.csv"

        prediction_files[
            OUTPUT_COLUMN_METHODS[predicted_method]
        ] = str(output_path)

        predictions.to_csv(
            output_path,
            index=False,
        )

        print()
        print(f"Saved predictions to: {output_path}")

    metadata = build_run_metadata(
        profile,
        eligible_profile,
        X,
        y,
        groups,
        fold_metric_records,
        fold_summaries,
        oof_metric_records,
        prediction_files,
    )

    metadata_path = output_dir / "run_metadata.json"
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
