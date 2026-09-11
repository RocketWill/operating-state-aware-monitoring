<!--
 * @Author: Will Cheng will.chengyong@gmail.com
 * @LastEditors: Will Cheng will.chengyong@gmail.com
 * @FilePath: /operating-state-aware-monitoring/docs/paderborn/matched-vibration-baseline.md
 * @Description:
 *
 * Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
-->
# 04 Matched vibration baseline

## English

This is the first Paderborn classification run. It uses only `vibration_1` and keeps the test condition fixed at `N15_M07_F10`.

Run from the repository root:

```text
conda run --no-capture-output -n windfusion python src/run_paderborn_matched_vibration_baseline.py
```

Each recording is one sample. The four fixed features are:

```text
mean, std, rms, peak_to_peak
```

The models are a most-frequent dummy reference and `StandardScaler + LogisticRegression(C=1.0, max_iter=1000)`. The scaler is fit inside each bearing-level training fold.

### Data and split

The target is `healthy=0` and `damaged=1`. The test condition is `N15_M07_F10`. The fixed three folds from 03 keep every bearing on one side of the split. There are 400 recordings: 20 recordings for each of the 20 primary bearings.

### Results

The table uses pooled out-of-fold predictions over the 400 test-condition recordings.

| Model | Macro-F1 | Balanced accuracy | Recall healthy / damaged |
|---|---:|---:|---:|
| Most-frequent dummy | 0.4118 | 0.5000 | 0.0000 / 1.0000 |
| Logistic regression | 0.9289 | 0.9506 | 0.9833 / 0.9179 |

Logistic regression confusion matrix, rows are true labels and columns are predicted labels:

```text
[[118,   2],
 [ 23, 257]]
```

The result shows that the vibration summary features can separate the two labels under this matched condition and bearing-level split. It is a first feasibility result, not a final sensor comparison.

The saved predictions and run settings are local:

- `outputs/paderborn_matched_vibration/predictions.csv`
- `outputs/paderborn_matched_vibration/run_metadata.json`

The public source is [`src/run_paderborn_matched_vibration_baseline.py`](../../src/run_paderborn_matched_vibration_baseline.py).

## 中文筆記

04 先只跑 `vibration_1`，test condition 固定 `N15_M07_F10`。一筆 recording 當一個 sample，不切 window。

固定四個 features：

```text
mean / std / rms / peak_to_peak
```

模型先放兩個：

```text
dummy most-frequent
StandardScaler + LogisticRegression
```

400 筆 recording 都是同一個 condition，每顆 primary bearing 20 筆。split 仍然以 bearing 為單位，所以同一顆 bearing 不會同時出現在 train 和 test。

結果：

```text
dummy       macro-F1 = 0.4118
logistic    macro-F1 = 0.9289
```

logistic 的 confusion matrix：

```text
[[118,   2],
 [ 23, 257]]
```
