# First baseline

The first baseline tests one concrete path from measured pressure and flow cycles to the `pump_leakage` target. The question is deliberately narrow: can the selected measurements produce a reproducible result under the target and group-split protocol? The score is therefore tied to this dataset, these eligible rows, and these folds. It is not a claim that the classifier or the sensor set is optimal.

## Reproducible command

Run the experiment from the repository root with the `windfusion` Conda environment:

```text
conda run --no-capture-output -n windfusion python src/run_first_baseline.py
```

The verified run used:

| Setting | Value |
|---|---|
| Environment | `windfusion`; Python 3.11.16; NumPy 2.4.6; pandas 3.0.5; scikit-learn 1.9.1 |
| Input | `data/hydraulic/raw/`; profile shape `2,205 × 5` |
| Eligible rows | `stable_flag == 0`; 1,449 cycles |
| Target | `pump_leakage`, classes `0/1/2` with counts `489/480/480` |
| Measurements | `PS1–PS6` and `FS1–FS2` |
| Cycle features | Per-channel mean, standard deviation, minimum, and maximum; 32 features |
| Split | Five-fold `StratifiedGroupKFold`, shuffled with `random_state=42` |
| Preprocessing | `StandardScaler` fit inside each training fold |
| Dummy | `most_frequent` |
| Classifier | Logistic regression, `C=1.0`, L2 regularization, `lbfgs`, `max_iter=1000` |

In scikit-learn 1.9.1, the code expresses L2 regularization as `l1_ratio=0.0`. The exact settings and results are written to the local `outputs/first_baseline/run_metadata.json` file. The two prediction files are `predicted_dummy_predictions.csv` and `predicted_logistic_predictions.csv`.

## Grouped evaluation

The eligible rows form 144 contiguous condition blocks: 143 blocks contain 10 cycles and one contains 19 cycles. A new block begins when the condition labels change or the original cycle index is no longer consecutive. The grouping columns are `cooler_condition`, `valve_condition`, `pump_leakage`, and `accumulator_pressure`.

The same group does not appear in both the training and test portion of a fold. The verified fold test sizes were 289 or 290 cycles, and all three target classes appeared in every test fold. These blocks are observed row-order groups, not verified independent experimental runs; the results are cycle-level predictions under group-disjoint folds.

## Results

The script reports both fold-average and pooled out-of-fold (OOF) metrics. Fold-average values show the mean and standard deviation across the five test folds. Pooled OOF values calculate each metric once over all held-out predictions. They are kept separate because the dummy classifier's most-frequent class changes between folds.

| Model | Aggregation | Macro-F1 | Balanced accuracy | Recall for classes 0 / 1 / 2 |
|---|---|---:|---:|---|
| Dummy | Fold average ± standard deviation | 0.1603 ± 0.0049 | 0.3333 ± 0.0000 | 0.4000 / 0.2000 / 0.4000 |
| Dummy | Pooled OOF | 0.3091 | 0.3163 | 0.3865 / 0.1875 / 0.3750 |
| Logistic regression | Fold average ± standard deviation | 0.9724 ± 0.0126 | 0.9726 ± 0.0124 | 0.9879 / 0.9671 / 0.9627 |
| Logistic regression | Pooled OOF | 0.9723 | 0.9723 | 0.9877 / 0.9667 / 0.9625 |

The pooled OOF confusion matrices use rows for true labels and columns for predicted labels, ordered as `0/1/2`:

```text
Dummy
[[189, 100, 200],
 [190,  90, 200],
 [200, 100, 180]]

Logistic regression
[[483,   6,   0],
 [  3, 464,  13],
 [  0,  18, 462]]
```

## Scope and limits

The primary run uses measured pressure and flow channels only. `CE` and `CP` are virtual quantities, while `SE` remains unresolved in the source audit, so none of them is included. `stable_flag=1` rows are not part of this run; an all-row sensitivity analysis remains separate.

The result establishes a runnable measurement-to-baseline path under the specified protocol. It does not establish independent-run uncertainty, production performance, an optimal model, or a universally sufficient sensor set. Dataset provenance and the measured/virtual classification are recorded in the [measurement audit](measurement-audit.md) and [target feasibility record](target-feasibility.md).

Raw data and generated experiment outputs remain local. The public project materials are the reader, the baseline source, and the records in this directory.
