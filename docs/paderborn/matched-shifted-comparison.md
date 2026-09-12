<!--
 * @Author: Will Cheng will.chengyong@gmail.com
 * @LastEditors: Will Cheng will.chengyong@gmail.com
 * @FilePath: /operating-state-aware-monitoring/docs/paderborn/matched-shifted-comparison.md
 * @Description:
 *
 * Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
-->
# 06 Matched and shifted condition comparison

This experiment checks how the sensor comparison changes when the training condition is different from the test condition.

Run from the repository root:

```text
conda run --no-capture-output -n windfusion python src/run_paderborn_shifted_sensor_comparison.py
```

The test condition is fixed at `N15_M07_F10`. Each test bearing contributes the same 20 recordings in both scenarios.

| Scenario | Training recordings | Test recordings |
|---|---|---|
| Matched | `N15_M07_F10` | `N15_M07_F10` |
| Shifted | `N09_M07_F10`, `N15_M01_F10`, `N15_M07_F04` | `N15_M07_F10` |

The shifted training set uses 20 recordings per training bearing. Conditions are selected in the fixed order `N09_M07_F10 -> N15_M01_F10 -> N15_M07_F04`, cycling by recording ID. Excluded duplicate recordings are skipped and the next eligible condition is used.

The same three bearing-level folds, features, models, and sensor groups from 03–05 are used. The sensor groups are current, vibration, and combined.

## Results

Results are pooled over the test recordings from the three fixed folds.

| Sensor group | Matched accuracy | Shifted accuracy | Matched macro-F1 | Shifted macro-F1 | Shifted - matched macro-F1 |
|---|---:|---:|---:|---:|---:|
| Current | 0.7325 | 0.6575 | 0.6421 | 0.5787 | -0.0634 |
| Vibration | 0.9375 | 0.9100 | 0.9289 | 0.8902 | -0.0387 |
| Combined | 0.8250 | 0.8175 | 0.7740 | 0.7575 | -0.0165 |

The current group has the largest macro-F1 drop. Vibration keeps a higher absolute score, while the combined group has the smallest drop in this run. The result is an initial condition-shift observation, not yet a general robustness conclusion.

## 目前理解

06 主要是在看：training 時沒有看過 test 的 operating condition，模型表現會不會下降。

這次 test condition 固定使用 `N15_M07_F10`。Test bearings 和 test recordings 都不變，只改 training data 來自哪個 condition。

Matched 比較直接：

```text
Train: N15_M07_F10
Test:  N15_M07_F10
```

每顆 training bearing 使用這個 condition 下的 20 筆 recordings。

Shifted 則不能讓 training 看到 test condition，所以改用：

```text
N09_M07_F10
N15_M01_F10
N15_M07_F04
```

三個 condition 的資料不能全部放進去，否則會變成 matched 每顆 bearing 20 筆、shifted 每顆 bearing 60 筆，結果就很難判斷差異到底來自 operating condition，還是 training data 變多。

因此 shifted 每顆 training bearing 仍然只取 20 筆，按照固定順序輪流取：

```text
recording 1  -> condition A
recording 2  -> condition B
recording 3  -> condition C
recording 4  -> condition A
...
```

大致上會是 condition A 取 7 筆、condition B 取 7 筆、condition C 取 6 筆，總數仍然是 20 筆。這樣 matched 和 shifted 的主要差別就是：matched 的 training 看過 test condition，shifted 沒有看過。

三組 sensor 換到 shifted training 後都有下降。Current 從 `0.6421` 降到 `0.5787`，掉幅最大，表示在這次實驗裡 current 對 operating condition 的改變比較敏感。

Vibration 從 `0.9289` 降到 `0.8902`，雖然也有下降，但換 condition 後仍然是三組裡表現最好的。Combined 從 `0.7740` 降到 `0.7575`，絕對分數沒有 vibration 高，但前後差距最小。

目前可以先理解成：

> Vibration 的分類能力最好，而 combined 在這一次 condition shift 下變化最小。

The local outputs are:

- `outputs/paderborn_shifted_sensor_comparison/predictions.csv`
- `outputs/paderborn_shifted_sensor_comparison/run_metadata.json`

The public source is [`src/run_paderborn_shifted_sensor_comparison.py`](../../src/run_paderborn_shifted_sensor_comparison.py).
