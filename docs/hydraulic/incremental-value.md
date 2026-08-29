# Incremental measurement value

The family comparison shows how each measurement behaves alone. This experiment keeps the hydraulic measurements as the reference and adds motor power, temperature, vibration, or all three families. Under the fixed protocol, adding motor power or all available measured families improves macro-F1, adding temperature gives a small negative change, and adding vibration gives a small positive change. These are paired out-of-fold differences for this dataset, feature representation, and model; they are not sensor ROI, causal effects, or claims about independent information.

## Reproducible command

Run the experiment from the repository root with the `windfusion` Conda environment:

```text
conda run --no-capture-output -n windfusion python src/run_incremental_value.py
```

The verified run used:

| Setting | Value |
|---|---|
| Environment | `windfusion`; Python 3.11.16; NumPy 2.4.6; pandas 3.0.5; scikit-learn 1.9.1 |
| Input | `data/hydraulic/raw/`; profile shape `2,205 × 5` |
| Eligible rows | `stable_flag == 0`; 1,449 cycles |
| Target | `pump_leakage`, classes `0/1/2` with counts `489/480/480` |
| Features | Per-channel mean, standard deviation, minimum, and maximum |
| Split | Five-fold `StratifiedGroupKFold`, shuffled with `random_state=42` |
| Preprocessing | `StandardScaler` fit inside each training fold |
| Model | Logistic regression with the fixed Task04 settings; no combination-specific tuning |
| Primary metric | Pooled out-of-fold macro-F1 |
| Delta reference | Hydraulic-only prediction on the same cycles and folds |

The eligible rows form 144 contiguous condition blocks: 143 blocks contain 10 cycles and one contains 19 cycles. The same group is not used in both the training and test portion of a fold. The hydraulic prediction in this run matches the Task05 hydraulic prediction for all 1,449 cycles.

## Combinations

| Combination | Added channels | Feature shape |
|---|---|---:|
| Hydraulic | `PS1–PS6`, `FS1–FS2` | `1,449 × 32` |
| Hydraulic + motor power | `EPS1` | `1,449 × 36` |
| Hydraulic + temperature | `TS1–TS4` | `1,449 × 48` |
| Hydraulic + vibration | `VS1` | `1,449 × 36` |
| All measurements | `EPS1`, `TS1–TS4`, `VS1` added to hydraulic | `1,449 × 56` |

The source channels are `PS1–PS6` pressure at 100 Hz, `FS1–FS2` volume flow at 10 Hz, `EPS1` motor power at 100 Hz, and `TS1–TS4` temperature plus `VS1` vibration at 1 Hz. `VS1` remains a one-hertz cycle summary rather than a high-frequency waveform. The virtual channels `CE` and `CP`, and the unresolved channel `SE`, are excluded.

## Results

The delta is calculated as combination metric minus hydraulic-only metric over pooled OOF predictions. Positive and negative values are both retained.

| Combination | Macro-F1 | Δ Macro-F1 | Balanced accuracy | Δ Balanced accuracy |
|---|---:|---:|---:|---:|
| Hydraulic | 0.9723 | 0.0000 | 0.9723 | 0.0000 |
| Hydraulic + motor power | 0.9855 | +0.0131 | 0.9855 | +0.0132 |
| Hydraulic + temperature | 0.9709 | -0.0014 | 0.9709 | -0.0014 |
| Hydraulic + vibration | 0.9765 | +0.0042 | 0.9765 | +0.0042 |
| All measurements | 0.9862 | +0.0138 | 0.9862 | +0.0139 |

The class-recall changes show where the differences occur:

| Combination | Δ recall class 0 | Δ recall class 1 | Δ recall class 2 |
|---|---:|---:|---:|
| Hydraulic | 0.0000 | 0.0000 | 0.0000 |
| Hydraulic + motor power | +0.0020 | +0.0125 | +0.0250 |
| Hydraulic + temperature | 0.0000 | -0.0021 | -0.0021 |
| Hydraulic + vibration | -0.0020 | +0.0062 | +0.0083 |
| All measurements | +0.0041 | +0.0104 | +0.0271 |

Motor power produces the clearest single-family addition in this run, while temperature does not improve the hydraulic reference. The all-measurements combination has the highest score, but its difference is still a result of this fixed model and these cycle-level summary features.

## Scope and limits

The comparison does not establish a universally optimal sensor set, sensor ROI, causal influence, or independent information content. It uses the same four summary statistics for every channel, does not tune a separate model for each combination, and does not test independent experimental runs. `stable_flag=1` rows are not included. The result should therefore be read as incremental predictive value under the stated evaluation protocol.

The local run artifacts contain the combination definitions, channel metadata, split records, fold metrics, pooled metrics, delta metrics, and paired OOF predictions:

- `outputs/incremental_value/run_metadata.json`
- `outputs/incremental_value/incremental_value_predictions.csv`

The single-family reference is documented in the [measurement-family comparison](family-comparison.md), and the public source for this experiment is [`src/run_incremental_value.py`](../../src/run_incremental_value.py).
