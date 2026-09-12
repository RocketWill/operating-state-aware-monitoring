<!--
 * @Author: Will Cheng will.chengyong@gmail.com
 * @LastEditors: Will Cheng will.chengyong@gmail.com
 * @FilePath: /operating-state-aware-monitoring/docs/paderborn/matched-sensor-comparison.md
 * @Description:
 *
 * Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
-->
# 05 Matched sensor comparison

This experiment compares current, vibration, and combined sensor groups under the same matched condition.

Run from the repository root:

```text
conda run --no-capture-output -n windfusion python src/run_paderborn_matched_sensor_comparison.py
```

The test condition is fixed at `N15_M07_F10`. Each recording is one sample, with the same four features used in 04:

```text
mean, std, rms, peak_to_peak
```

The sensor groups are:

| Sensor group | Signals | Number of features |
|---|---|---:|
| Current | `phase_current_1`, `phase_current_2` | 8 |
| Vibration | `vibration_1` | 4 |
| Combined | current + vibration | 12 |

The target is `healthy=0` and `damaged=1`. The same fixed bearing-level folds from 03 are used for all groups. The dummy model and the logistic regression model are also unchanged from 04.

## Results

Results are pooled over the 400 recordings in the test condition.

| Sensor group | Logistic accuracy | Dummy macro-F1 | Logistic macro-F1 | Logistic balanced accuracy |
|---|---:|---:|---:|---:|
| Current | 0.7325 | 0.4118 | 0.6421 | 0.6327 |
| Vibration | 0.9375 | 0.4118 | 0.9289 | 0.9506 |
| Combined | 0.8250 | 0.4118 | 0.7740 | 0.7560 |

Vibration gives the strongest result in this first comparison. Current is weaker on its own, and adding current to vibration does not improve the result here. This is only the matched-condition comparison; the effect under a shifted condition is a separate experiment.

## Current interpretation

This round compares current, vibration, and current + vibration under the same operating condition.

Vibration alone is the strongest group, with a macro-F1 of `0.9289`. Current alone is `0.6421`, and the combined group is `0.7740`. Under this matched condition, the useful information is more visible in vibration. Adding current does not give an extra gain with the current feature set and model.

The simple physical interpretation is that bearing damage is a mechanical change. When a rolling element passes a damaged part of the bearing, it can create extra impacts or vibration, which the vibration sensor may measure more directly.

Current is more indirect. The damage may first change friction, load, or torque, and only then appear in the motor current. This may explain why the current features are weaker in this comparison.

The lower score of the combined group is only a hypothesis for now. Vibration uses 4 features, while the combined group uses 12. If current does not provide enough new information in these simple statistical features, it may add variation without adding useful separation for this logistic regression run.

The safer conclusion is:

> Under this matched condition, with these features and logistic regression, vibration separates healthy and damaged bearings more easily than current. Current does not provide an additional gain in this run.

The next useful check is to compare the feature distributions for healthy and damaged bearings, especially RMS and standard deviation, to see whether the signal-level changes support this interpretation.

## 目前理解

這一輪是在同一個 operating condition 下，比較 current、vibration 和 current + vibration 對 healthy / damaged bearing 的分類效果。

結果是 vibration alone 最好，macro-F1 為 `0.9289`；current alone 是 `0.6421`；combined 是 `0.7740`。目前看起來，vibration 的資訊比較明顯，current 加進去也沒有帶來額外提升。

比較直覺的物理理解是，bearing damage 本身是機械損傷。滾動體經過受損位置時，可能產生額外撞擊或震動，vibration sensor 可以比較直接地量到這些變化。

Current 則比較間接。損傷可能先影響摩擦、負載或 torque，再反映到 motor current，所以目前這組 current features 的辨識能力比較弱。

Combined 變差暫時只能當成 hypothesis。vibration 只有 4 個 features，combined 增加到 12 個。如果 current 在這組簡單 statistical features 下沒有提供足夠新的資訊，反而可能增加 variation，讓 logistic regression 的結果變差。

比較保守的說法是：

> 在這個 matched condition、目前這組 features 和 logistic regression 下，vibration 比 current 更容易區分 healthy 和 damaged bearing；current 暫時沒有提供額外增益。

下一步可以直接看 healthy / damaged 在 vibration 和 current 的 RMS、STD 等 feature distribution，確認這個理解是否真的有資料支持。

The local outputs are:

- `outputs/paderborn_matched_sensor_comparison/predictions.csv`
- `outputs/paderborn_matched_sensor_comparison/run_metadata.json`

The public source is [`src/run_paderborn_matched_sensor_comparison.py`](../../src/run_paderborn_matched_sensor_comparison.py).
