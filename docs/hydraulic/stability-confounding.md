# Stability and condition stratification

The Task06 comparison used one grouped split. That was enough to compare the measurement combinations on the same out-of-fold rows, but it did not show whether a small delta depended on that particular split. This run repeats the same comparison over five grouped split seeds and then inspects the seed-42 predictions by component-condition stratum.

The result is stable for the larger positive effects in this dataset. Motor power and the all-measurements combination improve macro-F1 in every seed. Vibration also stays positive, although the change is smaller. Temperature remains close to the hydraulic reference and changes sign across seeds. These are split-sensitivity results for the fixed protocol, not confidence intervals from independent experiments.

## Reproducible command

Run the experiment from the repository root with the `windfusion` Conda environment:

```text
conda run --no-capture-output -n windfusion python src/run_stability_check.py
```

The verified run used:

| Setting | Value |
|---|---|
| Environment | `windfusion`; Python 3.11.16; NumPy 2.4.6; pandas 3.0.5; scikit-learn 1.9.1 |
| Input | `data/hydraulic/raw/`; profile shape `2,205 × 5` |
| Eligible rows | `stable_flag == 0`; 1,449 cycles |
| Target | `pump_leakage`, classes `0/1/2` with counts `489/480/480` |
| Features | Per-channel mean, standard deviation, minimum, and maximum |
| Combinations | Hydraulic; hydraulic + motor power; hydraulic + temperature; hydraulic + vibration; all measured families |
| Split | Five-fold `StratifiedGroupKFold`, shuffled with seeds `42/43/44/45/46` |
| Groups | 144 contiguous condition blocks; 143 blocks contain 10 cycles and one contains 19 cycles |
| Preprocessing | `StandardScaler` fit inside each training fold |
| Model | Logistic regression with the fixed Task04 settings; no seed- or combination-specific tuning |
| Primary metric | Pooled out-of-fold macro-F1 for each seed |
| Delta reference | Hydraulic-only prediction on the same rows and folds within each seed |
| Condition analysis | Seed 42; cooler, valve, and accumulator condition strata |

The source channels are the same measured inputs used in Task06. `CE` and `CP` remain excluded as virtual quantities, and `SE` remains unresolved in the source audit.

## Split stability

The table reports the mean and standard deviation across the five seeds. The range is the minimum–maximum pooled OOF macro-F1. The delta is calculated separately within each seed before its mean and standard deviation are reported.

| Combination | Macro-F1 mean ± SD | Macro-F1 range | Δ Macro-F1 vs hydraulic | Balanced accuracy mean ± SD |
|---|---:|---:|---:|---:|
| Hydraulic | 0.9716 ± 0.0034 | 0.9675–0.9772 | 0.0000 ± 0.0000 | 0.9716 ± 0.0034 |
| Hydraulic + motor power | 0.9845 ± 0.0013 | 0.9827–0.9862 | +0.0129 ± 0.0023 | 0.9845 ± 0.0013 |
| Hydraulic + temperature | 0.9711 ± 0.0036 | 0.9682–0.9779 | -0.0006 ± 0.0023 | 0.9710 ± 0.0036 |
| Hydraulic + vibration | 0.9762 ± 0.0029 | 0.9723–0.9813 | +0.0045 ± 0.0013 | 0.9762 ± 0.0029 |
| All measurements | 0.9848 ± 0.0015 | 0.9820–0.9862 | +0.0131 ± 0.0023 | 0.9848 ± 0.0015 |

Motor power has a positive macro-F1 delta in all five seeds, from `+0.0090` to `+0.0159`. The all-measurements combination has a similar range, from `+0.0090` to `+0.0159`. Vibration remains positive in all five seeds, while temperature ranges from `-0.0042` to `+0.0027`. The seed-42 hydraulic predictions match the Task06 hydraulic predictions for all 1,449 eligible cycles.

The same split assignment is reused for all five combinations within a seed. The generated prediction file therefore keeps the comparison paired at the cycle and fold level. `build_split_records()` also checks that the group sets in the training and test parts of every fold are disjoint.

## Condition strata

The condition analysis uses the seed-42 out-of-fold predictions. Each row below gives the observed support and the macro-F1 delta against the hydraulic prediction in that same stratum. Hydraulic is the zero reference and is not repeated in the delta columns.

| Stratum | Cycles / groups | Δ Motor power | Δ Temperature | Δ Vibration | Δ All measurements |
|---|---:|---:|---:|---:|---:|
| `cooler_condition=3` | 480 / 48 | +0.0227 | -0.0062 | +0.0021 | +0.0268 |
| `cooler_condition=20` | 480 / 48 | +0.0104 | -0.0021 | +0.0084 | +0.0084 |
| `cooler_condition=100` | 489 / 48 | +0.0062 | +0.0042 | +0.0023 | +0.0062 |
| `valve_condition=73` | 360 / 36 | +0.0110 | -0.0082 | +0.0083 | +0.0166 |
| `valve_condition=80` | 360 / 36 | +0.0083 | +0.0028 | +0.0028 | +0.0111 |
| `valve_condition=90` | 360 / 36 | +0.0194 | 0.0000 | +0.0027 | +0.0194 |
| `valve_condition=100` | 369 / 36 | +0.0138 | 0.0000 | +0.0029 | +0.0083 |
| `accumulator_pressure=90` | 369 / 36 | +0.0221 | 0.0000 | +0.0085 | +0.0221 |
| `accumulator_pressure=100` | 360 / 36 | +0.0055 | -0.0055 | 0.0000 | +0.0083 |
| `accumulator_pressure=115` | 360 / 36 | +0.0220 | +0.0055 | +0.0082 | +0.0247 |
| `accumulator_pressure=130` | 360 / 36 | +0.0029 | -0.0056 | +0.0001 | +0.0001 |

All 11 strata contain all three pump-leakage classes. The target counts are balanced within each observed block except for the additional cycles in the longer blocks: the per-stratum counts are recorded in `stratum_metrics.csv`. Motor power is positive in every listed stratum, and the all-measurements result is also positive in every listed stratum. Temperature is mixed, while vibration is close to zero in some strata.

These are descriptive cycle-level strata. The group count is reported as support for the observed condition blocks; it is not treated as a count of independent experimental runs. The current files do not identify independent run IDs, so this analysis does not estimate confidence intervals or make an independent-run uncertainty claim.

## Scope and limits

The repeated split analysis checks sensitivity to the selected grouped fold assignment. It does not establish a universally optimal sensor set, causal influence, sensor ROI, or independent information content. The condition table is tied to the seed-42 split and the same fixed model used in the baseline and incremental comparison.

The local run artifacts contain the per-seed predictions, the condition-stratum table, the split records, and the full metric records:

- `outputs/stability_check/stability_predictions.csv`
- `outputs/stability_check/stratum_metrics.csv`
- `outputs/stability_check/run_metadata.json`

Raw data and generated experiment outputs remain local. The public source for this analysis is [`src/run_stability_check.py`](../../src/run_stability_check.py), and the preceding paired comparison is documented in the [incremental measurement value](incremental-value.md) record.
