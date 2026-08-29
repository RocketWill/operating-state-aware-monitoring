'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/run_stability_check.py
Description: Check split stability and condition stratification.

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import StratifiedGroupKFold

from run_first_baseline import (
    CONDITION_COLUMNS,
    DATA_DIR,
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
from run_family_comparison import build_split_records
from run_incremental_value import (
    MEASUREMENT_INCREMENTAL,
    build_measurement_metadata,
    create_result_table,
    make_result_delta,
    validate_family_definitions,
)


OUTPUT_DIR = Path("outputs/stability_check")
LOOP_N = 5
RANDOM_STATES = [RANDOM_STATE + n for n in range(LOOP_N)]
CONDITION_STRATA_COLUMNS = [
    "cooler_condition",
    "valve_condition",
    "accumulator_pressure",
]


def create_cross_validation_dataset(
    y,
    groups,
    random_state=RANDOM_STATE,
):
    cv = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=random_state,
    )

    return list(cv.split(np.zeros(len(y)), y, groups))


def calculate_pooled_records(y, oof_pred, seed):
    records = []

    for incremental in MEASUREMENT_INCREMENTAL:
        metrics = calculate_metrics(
            y,
            oof_pred[incremental],
        )

        print()
        print(
            "Seed({}) {} logistic_regression pooled OOF summary".format(
                seed,
                incremental,
            )
        )
        print_metrics(
            "Seed({})-{} pooled".format(seed, incremental),
            metrics,
        )

        record = make_metric_record(
            "logistic_regression",
            "pooled_oof",
            metrics,
            len(y),
        )
        record["seed"] = int(seed)
        record["incremental"] = incremental
        records.append(record)

    return records


def summarize_values(values):
    values = np.asarray(values, dtype=float)

    return {
        "mean": float(values.mean()),
        "std": float(values.std()),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def build_stability_summary(pooled_records, delta_records):
    summary = []

    for incremental in MEASUREMENT_INCREMENTAL:
        pooled = [
            record
            for record in pooled_records
            if record["incremental"] == incremental
        ]
        deltas = [
            record
            for record in delta_records
            if record["incremental"] == incremental
        ]

        summary.append(
            {
                "incremental": incremental,
                "seed_count": len(pooled),
                "macro_f1": summarize_values(
                    [record["macro_f1"] for record in pooled]
                ),
                "macro_f1_delta_vs_hydraulic": summarize_values(
                    [record["macro_f1"] for record in deltas]
                ),
                "balanced_accuracy": summarize_values(
                    [record["balanced_accuracy"] for record in pooled]
                ),
                "balanced_accuracy_delta_vs_hydraulic": summarize_values(
                    [record["balanced_accuracy"] for record in deltas]
                ),
            }
        )

    return summary


def build_prediction_frame(
    eligible_profile,
    y,
    groups,
    fold_ids,
    oof_pred,
    seed,
):
    predictions = eligible_profile[CONDITION_COLUMNS].copy()
    predictions.insert(0, "cycle_index", predictions.index)
    predictions.insert(1, "seed", int(seed))
    predictions.insert(2, "group", groups.values)
    predictions.insert(3, "fold", fold_ids.values)
    predictions.insert(4, "true_pump_leakage", y.values)

    for incremental in MEASUREMENT_INCREMENTAL:
        predictions[
            "predicted_{}".format(incremental)
        ] = oof_pred[incremental].astype(int).values

    return predictions.reset_index(drop=True)


def run_split_stability(eligible_profile, condition="pump_leakage"):
    validate_family_definitions()

    y = eligible_profile[condition].copy()
    groups = eligible_profile["group"].copy()
    seed_fold_metric_records = []
    seed_pooled_records = []
    seed_delta_records = []
    seed_split_records = []
    seed_incremental_shapes = {}
    seed_predictions = {}
    seed_oof_tables = {}

    for seed in RANDOM_STATES:
        cv_splits = create_cross_validation_dataset(
            y,
            groups,
            seed,
        )
        fold_ids, split_records = build_split_records(
            y,
            groups,
            cv_splits,
        )
        seed_split_records.append(
            {
                "seed": int(seed),
                "folds": split_records,
            }
        )

        oof_pred = create_result_table(y)
        incremental_shapes = {}

        for incremental, channels in MEASUREMENT_INCREMENTAL.items():
            X = build_features(eligible_profile, channels)
            incremental_shapes[incremental] = [
                int(X.shape[0]),
                int(X.shape[1]),
            ]

            print()
            print("Seed:", seed)
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
                    "Seed({})-{}-{} logistic".format(
                        seed,
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
                record["seed"] = int(seed)
                record["incremental"] = incremental
                seed_fold_metric_records.append(record)

                test_index = y_test.index
                oof_pred.loc[test_index, incremental] = pred

        assert not oof_pred.isna().any().any()

        pooled_records = calculate_pooled_records(
            y,
            oof_pred,
            seed,
        )
        delta_records = make_result_delta(pooled_records)
        for record in delta_records:
            record["seed"] = int(seed)

        seed_pooled_records.extend(pooled_records)
        seed_delta_records.extend(delta_records)
        seed_incremental_shapes[int(seed)] = incremental_shapes
        seed_oof_tables[int(seed)] = oof_pred
        seed_predictions[int(seed)] = build_prediction_frame(
            eligible_profile,
            y,
            groups,
            fold_ids,
            oof_pred,
            seed,
        )

    return {
        "fold_metric_records": seed_fold_metric_records,
        "pooled_records": seed_pooled_records,
        "delta_records": seed_delta_records,
        "split_records": seed_split_records,
        "incremental_shapes": seed_incremental_shapes,
        "predictions": seed_predictions,
        "oof_tables": seed_oof_tables,
        "stability_summary": build_stability_summary(
            seed_pooled_records,
            seed_delta_records,
        ),
    }


def build_condition_record(
    y,
    pred,
    groups,
    seed,
    condition,
    label,
    incremental,
):
    metrics = calculate_metrics(y, pred)
    record = make_metric_record(
        "logistic_regression",
        "condition_stratum",
        metrics,
        len(y),
    )
    all_target_classes_present = all(
        count > 0
        for count in target_counts(y).values()
    )
    record.update(
        {
            "seed": int(seed),
            "condition": condition,
            "condition_value": int(label),
            "incremental": incremental,
            "support": {
                "cycle_count": int(len(y)),
                "group_count": int(groups.nunique()),
                "target_counts": target_counts(y),
                "all_target_classes_present": (
                    all_target_classes_present
                ),
            },
            "interpretation": "descriptive_cycle_level",
        }
    )
    return record


def build_condition_delta_records(condition_records):
    grouped_records = {}

    for record in condition_records:
        key = (
            record["condition"],
            record["condition_value"],
        )
        grouped_records.setdefault(key, []).append(record)

    delta_records = []
    for (condition, label), records in grouped_records.items():
        deltas = make_result_delta(records)
        for delta in deltas:
            matching_record = next(
                record
                for record in records
                if record["incremental"] == delta["incremental"]
            )
            delta.update(
                {
                    "seed": int(matching_record["seed"]),
                    "condition": condition,
                    "condition_value": int(label),
                    "support": matching_record["support"],
                    "interpretation": "descriptive_cycle_level",
                }
            )
            delta_records.append(delta)

    return delta_records


def run_condition_stratification(
    eligible_profile,
    oof_pred,
    seed=RANDOM_STATE,
):
    y = eligible_profile["pump_leakage"].copy()
    condition_records = []

    for condition in CONDITION_STRATA_COLUMNS:
        labels = sorted(
            eligible_profile[condition].drop_duplicates().tolist()
        )

        for label in labels:
            stratum_index = eligible_profile.index[
                eligible_profile[condition] == label
            ]
            stratum_y = y.loc[stratum_index]
            stratum_groups = eligible_profile.loc[
                stratum_index,
                "group",
            ]

            print()
            print(
                "Condition: {} = {} ({} cycles, {} groups)".format(
                    condition,
                    label,
                    len(stratum_y),
                    stratum_groups.nunique(),
                )
            )

            for incremental in MEASUREMENT_INCREMENTAL:
                stratum_pred = oof_pred.loc[
                    stratum_index,
                    incremental,
                ]
                record = build_condition_record(
                    stratum_y,
                    stratum_pred,
                    stratum_groups,
                    seed,
                    condition,
                    label,
                    incremental,
                )
                condition_records.append(record)

                print_metrics(
                    "{}-{}".format(condition, incremental),
                    calculate_metrics(stratum_y, stratum_pred),
                )

    return {
        "records": condition_records,
        "delta_records": build_condition_delta_records(
            condition_records
        ),
        "seed": int(seed),
        "columns": CONDITION_STRATA_COLUMNS,
    }


def flatten_condition_records(condition_result):
    delta_lookup = {
        (
            record["condition"],
            record["condition_value"],
            record["incremental"],
        ): record
        for record in condition_result["delta_records"]
    }
    rows = []

    for record in condition_result["records"]:
        support = record["support"]
        delta = delta_lookup[
            (
                record["condition"],
                record["condition_value"],
                record["incremental"],
            )
        ]
        row = {
            "seed": record["seed"],
            "condition": record["condition"],
            "condition_value": record["condition_value"],
            "incremental": record["incremental"],
            "cycle_count": support["cycle_count"],
            "group_count": support["group_count"],
            "all_target_classes_present": (
                support["all_target_classes_present"]
            ),
            "macro_f1": record["macro_f1"],
            "balanced_accuracy": record["balanced_accuracy"],
            "delta_macro_f1_vs_hydraulic": delta["macro_f1"],
            "delta_balanced_accuracy_vs_hydraulic": (
                delta["balanced_accuracy"]
            ),
        }
        for label in TARGET_LABELS:
            row["target_count_{}".format(label)] = support[
                "target_counts"
            ][str(label)]
            row["recall_{}".format(label)] = record[
                "per_class_recall"
            ][str(label)]
            row["delta_recall_{}".format(label)] = delta[
                "per_class_recall"
            ][str(label)]
        rows.append(row)

    return pd.DataFrame(rows)


def build_run_metadata(
    profile,
    eligible_profile,
    y,
    groups,
    stability_result,
    condition_result,
    prediction_file,
    stratum_file,
):
    group_size_counts = (
        eligible_profile["group"]
        .value_counts()
        .value_counts()
        .sort_index()
    )
    first_seed = RANDOM_STATES[0]
    first_seed_shapes = stability_result["incremental_shapes"][
        first_seed
    ]

    combinations = {
        incremental: build_measurement_metadata(
            incremental,
            first_seed_shapes[incremental],
        )
        for incremental in MEASUREMENT_INCREMENTAL
    }

    return {
        "source_script": "src/run_stability_check.py",
        "command": (
            "conda run --no-capture-output -n windfusion "
            "python src/run_stability_check.py"
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
            "random_states": RANDOM_STATES,
            "group_disjoint_check": (
                "build_split_records asserts disjoint train/test groups."
            ),
            "preprocessing": (
                "StandardScaler is fit inside each training fold."
            ),
            "folds_by_seed": stability_result["split_records"],
        },
        "model": {
            "name": "logistic_regression",
            "tuning": (
                "No seed- or combination-specific tuning; fixed "
                "settings are shared."
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
            "aggregation": "pooled_oof_per_seed",
            "delta_reference": "hydraulic",
            "paired_structure": (
                "Each measurement combination uses the same rows and "
                "fold assignment within a seed."
            ),
        },
        "condition_stratification": {
            "seed": condition_result["seed"],
            "columns": condition_result["columns"],
            "support": (
                "Every stratum records cycle count, group count, and "
                "target counts."
            ),
            "interpretation": "descriptive_cycle_level",
        },
        "results": {
            "stability_summary": stability_result[
                "stability_summary"
            ],
            "pooled_oof_metrics_by_seed": stability_result[
                "pooled_records"
            ],
            "delta_metrics_by_seed": stability_result[
                "delta_records"
            ],
            "condition_metrics": condition_result["records"],
            "condition_delta_metrics": condition_result[
                "delta_records"
            ],
            "prediction_file": prediction_file,
            "stratum_file": stratum_file,
        },
        "limitations": [
            "The observed condition blocks are not verified independent runs.",
            "No confidence interval is estimated from cycle rows or condition blocks.",
            "Condition results are descriptive strata under the fixed seed-42 split.",
        ],
    }


def main():
    profile = load_profile()
    eligible_profile = select_eligible_cycles(profile)
    y = eligible_profile["pump_leakage"].copy()
    groups = eligible_profile["group"].copy()

    stability_result = run_split_stability(
        eligible_profile,
        condition="pump_leakage",
    )
    condition_result = run_condition_stratification(
        eligible_profile,
        stability_result["oof_tables"][RANDOM_STATE],
        seed=RANDOM_STATE,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    prediction_path = OUTPUT_DIR / "stability_predictions.csv"
    pd.concat(
        stability_result["predictions"].values(),
        ignore_index=True,
    ).to_csv(
        prediction_path,
        index=False,
    )

    stratum_path = OUTPUT_DIR / "stratum_metrics.csv"
    flatten_condition_records(condition_result).to_csv(
        stratum_path,
        index=False,
    )

    metadata = build_run_metadata(
        profile,
        eligible_profile,
        y,
        groups,
        stability_result,
        condition_result,
        str(prediction_path),
        str(stratum_path),
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
    print("Stability summary:")
    for record in stability_result["stability_summary"]:
        print(
            "  {} macro-F1: {:.4f} ± {:.4f}; "
            "delta: {:+.4f} ± {:.4f}".format(
                record["incremental"],
                record["macro_f1"]["mean"],
                record["macro_f1"]["std"],
                record["macro_f1_delta_vs_hydraulic"]["mean"],
                record["macro_f1_delta_vs_hydraulic"]["std"],
            )
        )

    print()
    print("Saved predictions to:", prediction_path)
    print("Saved stratum metrics to:", stratum_path)
    print("Saved run metadata to:", metadata_path)


if __name__ == "__main__":
    main()
