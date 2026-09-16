<!--
 * @Author: Will Cheng will.chengyong@gmail.com
 * @LastEditors: Will Cheng will.chengyong@gmail.com
 * @FilePath: /operating-state-aware-monitoring/docs/paderborn/four-condition-robustness.md
 * @Description:
 *
 * Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
-->
# 07 Four-condition robustness comparison

This experiment repeats the matched and shifted comparison with each of the four operating conditions used as the test condition.

Run from the repository root:

```text
conda run --no-capture-output -n windfusion python src/run_paderborn_four_condition_robustness.py
```

The test conditions are:

```text
N15_M07_F10
N09_M07_F10
N15_M01_F10
N15_M07_F04
```

For each test condition, the same eligible test recordings are used in both scenarios. The nominal target is 20 recordings per bearing; the protocol-excluded duplicate files make two condition totals slightly smaller.

| Scenario | Training data | Test data |
|---|---|---|
| Matched | the current test condition | the current test condition |
| Shifted | the other three conditions, 20 recordings per training bearing | the current test condition |

The shifted recordings cycle through the other three conditions by recording ID. Excluded duplicate recordings are skipped and the next eligible row is used. The bearing-level folds, features, sensor groups, and models are unchanged from 03–06.

## Results

Results are pooled over the eligible test recordings for each condition and scenario. The test-row totals are `400` for `N15_M07_F10`, `399` for `N09_M07_F10`, `400` for `N15_M01_F10`, and `396` for `N15_M07_F04`.

| Test condition | Sensor group | Matched macro-F1 | Shifted macro-F1 | Drop |
|---|---|---:|---:|---:|
| N15_M07_F10 | Current | 0.6421 | 0.5787 | -0.0634 |
| N15_M07_F10 | Vibration | 0.9289 | 0.8902 | -0.0388 |
| N15_M07_F10 | Combined | 0.7740 | 0.7575 | -0.0165 |
| N09_M07_F10 | Current | 0.6425 | 0.5683 | -0.0741 |
| N09_M07_F10 | Vibration | 0.6106 | 0.8081 | +0.1975 |
| N09_M07_F10 | Combined | 0.6576 | 0.8016 | +0.1441 |
| N15_M01_F10 | Current | 0.6454 | 0.4872 | -0.1582 |
| N15_M01_F10 | Vibration | 0.9209 | 0.8732 | -0.0477 |
| N15_M01_F10 | Combined | 0.8230 | 0.4981 | -0.3248 |
| N15_M07_F04 | Current | 0.6541 | 0.5936 | -0.0605 |
| N15_M07_F04 | Vibration | 0.9259 | 0.8851 | -0.0407 |
| N15_M07_F04 | Combined | 0.8390 | 0.8538 | +0.0147 |

The shift effect is not identical across test conditions. Current drops for all four conditions. Vibration and combined improve when `N09_M07_F10` is the test condition, while combined also improves slightly for `N15_M07_F04`. The largest drop in this run is the combined group under `N15_M01_F10`.

These results do not support one universal robustness ranking yet. The direction and size of the shift effect depend on the test condition, so the condition itself remains part of the result.

## 目前理解

四個 operating conditions 可以先簡化成：

```text
A、B、C、D
```

Bearings 固定分成三個 bearing-level folds：

```text
Fold 1、Fold 2、Fold 3
```

假設先把 Condition A 當作 test condition，會有兩種 training scenario。

Matched：

```text
Train condition = A
Test condition  = A
```

也就是 training 和 test 使用相同的 operating condition。

Shifted：

```text
Train conditions = B + C + D
Test condition   = A
```

也就是 training 不包含 A，改用另外三個 conditions，測試模型在 unseen operating condition 下的表現。

兩種 scenario 都使用相同的 bearing-level cross-validation：

```text
Fold 1 當 test，Fold 2 + Fold 3 當 train
Fold 2 當 test，Fold 1 + Fold 3 當 train
Fold 3 當 test，Fold 1 + Fold 2 當 train
```

所以 matched 和 shifted 的主要差別是 training condition 是否包含 test condition，test bearings 和 fold split 都保持一致。最後將三個 folds 的 test predictions 合併，再比較 matched 和 shifted 的差異。

Condition A 完成後，再讓 B、C、D 依序當作 test condition：

```text
Test B:
Matched = Train B
Shifted  = Train A + C + D

Test C:
Matched = Train C
Shifted  = Train A + B + D

Test D:
Matched = Train D
Shifted  = Train A + B + C
```

因此 07 的核心就是在四個 operating conditions 下重複同一個比較：

> 比較模型在 seen condition 和 unseen condition 下的分類表現，觀察不同 sensor 對 operating-condition shift 的敏感程度與穩定性。

The local outputs are:

- `outputs/paderborn_four_condition_robustness/predictions.csv`
- `outputs/paderborn_four_condition_robustness/run_metadata.json`

The first figure can be generated with:

```text
conda run --no-capture-output -n windfusion python src/plot_paderborn_robustness_bars.py
```

It is saved locally as `outputs/paderborn_figures/matched_shifted_macro_f1.png`.

The public source is [`src/run_paderborn_four_condition_robustness.py`](../../src/run_paderborn_four_condition_robustness.py).
