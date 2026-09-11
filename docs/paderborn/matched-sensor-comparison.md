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

The local outputs are:

- `outputs/paderborn_matched_sensor_comparison/predictions.csv`
- `outputs/paderborn_matched_sensor_comparison/run_metadata.json`

The public source is [`src/run_paderborn_matched_sensor_comparison.py`](../../src/run_paderborn_matched_sensor_comparison.py).
