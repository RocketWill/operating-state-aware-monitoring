<!--
 * @Author: Will Cheng will.chengyong@gmail.com
 * @LastEditors: Will Cheng will.chengyong@gmail.com
 * @FilePath: /operating-state-aware-monitoring/docs/hydraulic/target-feasibility.md
 * @Description:
 *
 * Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
-->
## Cycle / run structure

Observed:
- The `stable_flag=0` subset contains 144 condition combinations.
- 143 combinations contain 10 consecutive 60-second cycles; one combination contains 19 cycles.
- The cycles are contiguous in dataset row order.

Not established:
- Whether one contiguous condition block corresponds to one independent experimental run.
- Whether cycles within a block are statistically independent.
- No explicit run ID has been identified from the currently inspected files.

## Target and eligibility

Use `pump_leakage` as a three-class classification target:

| Value | Meaning | All rows |
|---:|---|---:|
| 0 | No leakage | 1,221 |
| 1 | Weak leakage | 492 |
| 2 | Severe leakage | 492 |

The primary analysis uses rows with `stable_flag=0`. This gives 1,449 cycles with class counts of 489, 480, and 480. The source defines `stable_flag=1` as a condition where static conditions might not have been reached yet. In the observed data, those 756 rows contain 732 pump class 0 rows, 12 class 1 rows, and 12 class 2 rows. This makes the flag a substantive eligibility condition, not an ordinary feature.

The all-row result remains a sensitivity analysis. `stable_flag` is not used as a predictor in either analysis.

The other component conditions remain represented in the eligible data rather than being filtered to one nominal combination. They are used for condition-block grouping and stratified reporting, not as predictor columns in the first baseline.

## Split protocol

Use the 144 contiguous `stable_flag=0` condition blocks as groups. Do not randomly split individual cycles from the same block across folds. The first evaluation uses five-fold stratified group cross-validation, with every learned preprocessing step fitted inside the training portion of each fold.

The condition blocks are an observed row-order grouping, not verified independent experimental runs. Results are therefore reported as cycle-level predictions under group-disjoint folds; they are not presented as uncertainty from 144 independent experiments.

## Metrics

Use macro-F1 as the primary metric. Report balanced accuracy, per-class recall, and the confusion matrix as secondary results. Overall accuracy is not sufficient as the main result because the all-row class distribution is uneven and the evaluation is multiclass.

## First baseline

The first measurement baseline uses measured pressure and flow channels (`PS1`–`PS6` and `FS1`–`FS2`). Per-cycle summary features are calculated separately for each channel, starting with mean, standard deviation, minimum, and maximum. `CE` and `CP` are virtual quantities, and `SE` remains unresolved, so none of them is included in the primary baseline.

Use a most-frequent dummy classifier as the lower reference and a regularized logistic regression as the first simple classifier. The baseline is a feasibility check for the target and split protocol, not a claim that this model is optimal.

## Data quality check

The `windfusion` environment was used to inspect all 18 tab-delimited measurement and profile files. Each file contains 2,205 rows, and the chunked missing-value scan reported zero missing values.
