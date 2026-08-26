# Measurement-family comparison

This comparison uses the same target, eligible cycles, grouped split, model, and metrics for four measurement families. Under this protocol, the hydraulic family gives the highest macro-F1, followed by motor power, temperature, and vibration. The result is tied to this dataset and this feature representation; it is not a universal ranking of sensor families.

## Reproducible command

Run the experiment from the repository root with the `windfusion` Conda environment:

```text
conda run --no-capture-output -n windfusion python src/run_family_comparison.py
```

The verified run used:

| Setting | Value |
|---|---|
| Environment | `windfusion`; Python 3.11.16; NumPy 2.4.6; pandas 3.0.5; scikit-learn 1.9.1 |
| Input | `data/hydraulic/raw/`; profile shape `2,205 × 5` |
| Eligible rows | `stable_flag == 0`; 1,449 cycles |
| Target | `pump_leakage`, classes `0/1/2` with counts `489/480/480` |
| Split | Five-fold `StratifiedGroupKFold`, shuffled with `random_state=42` |
| Preprocessing | `StandardScaler` fit inside each training fold |
| Model | Logistic regression with the fixed Task04 settings; no family-specific tuning |
| Primary metric | Pooled out-of-fold macro-F1 |
| Secondary metrics | Balanced accuracy, per-class recall, and confusion matrix |

The eligible rows form 144 contiguous condition blocks: 143 blocks contain 10 cycles and one contains 19 cycles. The grouping rule starts a new block when the condition labels change or the original cycle index is no longer consecutive. The same group is not used in both the training and test portion of a fold.

The hydraulic family uses the same rows, fold assignment, features, and logistic regression settings as the first baseline. Its saved predictions match the Task04 logistic predictions for all 1,449 cycles.

## Measurement families

Each channel contributes four cycle-level features: mean, standard deviation, minimum, and maximum. The sampling rate describes the source channel; it does not mean that the comparison reconstructs the original high-frequency waveform.

| Family | Channels and source measurements | Features |
|---|---|---:|
| Hydraulic | `PS1–PS6`: pressure, 100 Hz, bar; `FS1–FS2`: volume flow, 10 Hz, l/min | 32 |
| Motor power | `EPS1`: motor power, 100 Hz, W | 4 |
| Temperature | `TS1–TS4`: temperature, 1 Hz, °C | 16 |
| Vibration | `VS1`: vibration, 1 Hz, mm/s | 4 |

`VS1` is therefore compared as a one-hertz cycle summary. It is not treated as a high-frequency vibration waveform. The virtual channels `CE` and `CP`, and the unresolved channel `SE`, are excluded from all families.

## Results

All rows in the table are pooled out-of-fold results over the same 1,449 eligible cycles. The recall columns use the target labels `0/1/2`.

| Family | Feature shape | Macro-F1 | Balanced accuracy | Recall `0 / 1 / 2` |
|---|---:|---:|---:|---|
| Hydraulic | `1,449 × 32` | 0.9723 | 0.9723 | 0.9877 / 0.9667 / 0.9625 |
| Motor power | `1,449 × 4` | 0.6852 | 0.7008 | 0.8650 / 0.4125 / 0.8250 |
| Temperature | `1,449 × 16` | 0.5107 | 0.5146 | 0.6585 / 0.4062 / 0.4792 |
| Vibration | `1,449 × 4` | 0.4294 | 0.4320 | 0.5542 / 0.3250 / 0.4167 |

The largest error for motor power is class `1`: 137 class-1 cycles are predicted as class `0`, and 145 as class `2`. Temperature has a similar class-1 recall of 0.4062, with 144 class-1 cycles predicted as class `0` and 141 as class `2`. Vibration has the lowest class-1 recall, 0.3250; 211 class-1 cycles are predicted as class `2`.

The pooled out-of-fold confusion matrices use rows for true labels and columns for predicted labels, ordered as `0/1/2`:

```text
Hydraulic
[[483,   6,   0],
 [  3, 464,  13],
 [  0,  18, 462]]

Motor power
[[423,  55,  11],
 [137, 198, 145],
 [ 20,  64, 396]]

Temperature
[[322, 100,  67],
 [144, 195, 141],
 [109, 141, 230]]

Vibration
[[271, 116, 102],
 [113, 156, 211],
 [137, 143, 200]]
```

## Interpretation and limits

The hydraulic measurements provide the clearest separation of `pump_leakage` in this representation. Motor power retains a measurable signal, but it does not separate class `1` as reliably. The temperature and one-hertz vibration summaries are weaker under the same fixed model and grouped evaluation.

This comparison does not establish that hydraulic sensors are universally necessary, that the other families have no physical value, or that one family would remain best after feature redesign or model tuning. It is a single-family comparison using four summary statistics per channel. It also does not test sensor fusion, raw vibration waveforms, independent experimental-run uncertainty, or the excluded `stable_flag=1` rows.

The local run artifacts record the complete family definitions, source sampling rates, split records, fold metrics, pooled metrics, and OOF predictions:

- `outputs/family_comparison/run_metadata.json`
- `outputs/family_comparison/family_comparison_predictions.csv`

Raw data and generated outputs remain local. The public source for the comparison is [`src/run_family_comparison.py`](../../src/run_family_comparison.py); channel definitions and the measured/virtual classification are recorded in the [single-cycle read](single-cycle-read.md) and [measurement audit](measurement-audit.md).
