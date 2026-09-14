<!--
 * @Author: Will Cheng will.chengyong@gmail.com
 * @LastEditors: Will Cheng will.chengyong@gmail.com
 * @FilePath: /operating-state-aware-monitoring/docs/paderborn/signal-feature-interpretation.md
 * @Description:
 *
 * Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
-->
# 08 Signal feature interpretation

This step returns to the recording-level features instead of training another classifier. It compares healthy and accelerated-lifetime damaged bearings by condition, signal channel, and fixed feature.

Run from the repository root:

```text
conda run --no-capture-output -n windfusion python src/analyze_paderborn_signal_features.py
```

The analysis uses the same primary recordings from 03 and the same four features used in 04–07:

```text
mean, std, rms, peak_to_peak
```

The three channels are `phase_current_1`, `phase_current_2`, and `vibration_1`. The output reports count, mean, median, standard deviation, and the 25th/75th percentiles for each class.

## RMS check

The first quick check prints the RMS mean for healthy and damaged recordings. The full feature summary is kept in the local CSV.

| Test condition | Channel | Healthy RMS | Damaged RMS | Difference |
|---|---|---:|---:|---:|
| N15_M07_F10 | phase_current_1 | 1.7583 | 1.7577 | -0.0006 |
| N15_M07_F10 | phase_current_2 | 1.7664 | 1.7709 | +0.0045 |
| N15_M07_F10 | vibration_1 | 0.2910 | 0.4019 | +0.1109 |
| N09_M07_F10 | phase_current_1 | 1.6836 | 1.7003 | +0.0166 |
| N09_M07_F10 | phase_current_2 | 1.6956 | 1.7122 | +0.0166 |
| N09_M07_F10 | vibration_1 | 0.2420 | 0.1945 | -0.0475 |
| N15_M01_F10 | phase_current_1 | 0.9073 | 0.8920 | -0.0153 |
| N15_M01_F10 | phase_current_2 | 0.9202 | 0.9042 | -0.0161 |
| N15_M01_F10 | vibration_1 | 0.2937 | 0.4052 | +0.1115 |
| N15_M07_F04 | phase_current_1 | 1.7655 | 1.7468 | -0.0187 |
| N15_M07_F04 | phase_current_2 | 1.7739 | 1.7600 | -0.0139 |
| N15_M07_F04 | vibration_1 | 0.2809 | 0.3653 | +0.0844 |

Vibration has a larger RMS difference in three conditions, while current differences are smaller. The vibration direction changes under `N09_M07_F10`, where damaged recordings have a lower RMS mean than healthy recordings. This matches the condition-dependent behavior seen in 07 and is a reason to avoid one fixed physical explanation for all conditions.

The first interpretation should stay at the feature level. A larger damaged-versus-healthy difference in vibration can support the idea that vibration carries useful damage information, while a smaller current difference is consistent with a more indirect measurement. This is not a causal test.

## 目前理解

08 先不再訓練新的 classifier，而是回到 recording-level features，看 healthy 和 damaged 的 signal 分布有沒有支持前面模型結果。

四個 operating conditions 可以先簡化成：

```text
A、B、C、D
```

每個 condition 都分別看：

```text
phase_current_1
phase_current_2
vibration_1
```

再比較 healthy 和 damaged 的：

```text
mean / std / rms / peak_to_peak
```

目前先看 RMS。三個 conditions 裡，vibration 的 healthy / damaged 差異比 current 明顯，這和前面 vibration 分類能力比較強的結果大致一致。Current 的 RMS 差異比較小，暫時符合它比較 indirect 的理解。

但 `N09_M07_F10` 的 vibration 方向相反：damaged 的 RMS 反而比 healthy 低。這和 07 裡 vibration 在這個 condition 的 shifted 結果變好的現象放在一起看，代表不同 operating condition 下，signal pattern 可能不是同一個方向。

所以目前不能直接寫成：

> damaged bearing 一定會讓 vibration RMS 上升。

比較合理的說法是：

> vibration 在目前資料裡提供了比較明顯的 damage-related information，但這個差異的大小和方向會隨 operating condition 改變。

這一步只能支持 feature-level 的理解，還不能當成 causal explanation。下一步如果要再細看，可以把 RMS、STD 的 distribution 畫出來，確認差異是整體移動，還是只有少數 recordings 拉開平均值。

## N09_M07_F10 的特殊現象

在 07 的 four-condition robustness comparison 中，`N09_M07_F10` 的 vibration 結果比較特殊。

Matched scenario：

```text
Train = N09_M07_F10
Test  = N09_M07_F10
```

Macro-F1 是 `0.6106`。

Shifted scenario：

```text
Train = 其他三個 operating conditions
Test  = N09_M07_F10
```

Macro-F1 反而提升到 `0.8081`。也就是在這個 condition 下，使用相同 condition 的 training data 沒有得到較好的分類結果；使用其他三個 conditions 混合訓練後，對 `N09_M07_F10` 的泛化表現反而比較好。

一個可能的解釋是，`N09_M07_F10` 的 vibration pattern 和其他 conditions 有比較明顯的差異。只使用這個 condition 訓練時，模型可能比較容易學到 condition-specific pattern；使用其他三個 conditions 混合訓練，則可能提供更多 operating-state variation，使模型學到比較 general 的 healthy / damaged distinction。

08 的 feature analysis 也看到相關現象。其他三個 conditions 中，damaged bearing 的 vibration RMS 都高於 healthy bearing；但在 `N09_M07_F10` 中方向相反，damaged RMS 反而比較低。

因此目前比較合理的理解是：

> `N09_M07_F10` 可能具有比較特殊的 vibration distribution，healthy / damaged 的 signal pattern 和其他 operating conditions 不完全一致。

這也表示 bearing damage 的 measurement pattern 不能直接假設在所有 operating conditions 下都保持相同。Matched 和 shifted 的結果差異，可能同時受到 damage information 和 operating-condition-specific signal behavior 影響。這仍然是目前的 interpretation，不是已經證明的 causal explanation。

The local output is:

- `outputs/paderborn_signal_features/feature_summary.csv`

The public source is [`src/analyze_paderborn_signal_features.py`](../../src/analyze_paderborn_signal_features.py).
