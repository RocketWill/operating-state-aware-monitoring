# 03 Target, bearing split, and comparison protocol

## English

This step fixes the first Paderborn comparison before looking at test scores.

Run:

```text
conda run --no-capture-output -n windfusion python src/build_paderborn_protocol.py
```

The script writes a local expected recording manifest and protocol to `outputs/paderborn_protocol/`.

The primary task is binary bearing classification:

```text
healthy -> 0
damaged -> 1
```

The primary set contains 6 healthy bearings and 14 bearings damaged through accelerated lifetime tests. The 12 artificial-damage bearings are kept as a possible extension, but are not mixed into the first comparison.

The split unit is the bearing. All conditions and recordings from one bearing stay on the same side of a fold. Three folds are used because the primary set has six healthy bearings:

| Fold | Test bearings |
|---|---|
| `fold_1` | `K001`, `K004`, `KA04`, `KA15`, `KB23`, `KI14` |
| `fold_2` | `K002`, `K005`, `KA16`, `KA22`, `KB24`, `KI04`, `KI16` |
| `fold_3` | `K003`, `K006`, `KA30`, `KB27`, `KI17`, `KI18`, `KI21` |

The first test condition is `N15_M07_F10`. Both comparisons use the same test bearings and test recordings:

- `matched`: training bearings use their recordings from `N15_M07_F10`.
- `shifted`: training bearings use the other three conditions.

The shifted rule selects 20 recordings per training bearing using the fixed order `N09_M07_F10 -> N15_M01_F10 -> N15_M07_F04`, repeated by recording ID. Excluded duplicate recordings are skipped and the next eligible row is used. This keeps the training count comparable with matched and makes the selection reproducible.

The first comparison uses `mean`, `std`, `rms`, and `peak_to_peak`. The first model is `StandardScaler + logistic regression`. The primary metric is macro-F1; balanced accuracy, per-class recall, and a confusion matrix are secondary metrics.

The sensor groups are fixed before the test run:

| Group | Channels | Feature shape per recording |
|---|---|---:|
| Current | `phase_current_1`, `phase_current_2` | 8 |
| Vibration | `vibration_1` | 4 |
| Combined | both current channels and `vibration_1` | 12 |

The manifest describes 32 known bearings and 2,560 expected recording rows. The primary set has 1,600 expected rows, or 1,595 after excluding five files from two exact duplicate groups. The known replacement pair is `17 == 18`, so recording 18 is kept and 17 is excluded. The second group is `5 == 6 == 15 == 19 == 20`, so recording 5 is kept and 6, 15, 19, and 20 are excluded.

All 32 bearing directories are now extracted locally. Each contains 80 MATLAB recordings and 2 PDFs. K001 and KA04 have been read for the first signal inspection. The file-count check does not replace reading every measuring log or checking all recordings for additional duplicates before the baseline run.

## 中文筆記

這一步先把 target 和 split 固定，不先看 test 分數。

目前先做二分類：

```text
healthy -> 0
damaged -> 1
```

第一版只放 6 個 healthy 和 14 個 accelerated lifetime damage。12 個 artificial damage 先留著，不先混進來。這樣第一個比較不會同時混兩種 damage generation mechanism。

資料切分以 bearing 為單位。同一顆 bearing 的所有 conditions 和 recordings 都留在同一個 fold，不跨 train/test。

第一個 test condition 先用 `N15_M07_F10`：

```text
matched:
  train bearing 用同一個 condition

shifted:
  train bearing 用另外三個 conditions
```

兩種比較使用相同的 test bearings 和 test recordings。shifted 每顆 train bearing 固定取 20 筆，避免只是因為訓練資料變多，結果就不能直接比較。

第一輪固定使用 `mean`、`std`、`rms`、`peak_to_peak`，模型用 `StandardScaler + logistic regression`。主要看 macro-F1，另外保留 balanced accuracy、per-class recall 和 confusion matrix。

sensor groups 也先固定：

```text
current    = phase_current_1 + phase_current_2  -> 8 features
vibration  = vibration_1                         -> 4 features
combined   = current + vibration                -> 12 features
```

目前全部 32 個 bearing 都已解壓，每個目錄都有 80 個 `.mat` 和 2 個 PDF。第一輪 audit 找到 1 個讀取錯誤和 3 組 exact duplicate candidates。第一版 primary protocol 先保留 1,595 筆，排除 5 個 duplicate files；K001、KA04 已讀過 signal，其他 bearings 的 measuring logs 還要再核對。

## Full recording audit status

The first full pass checked 2,560 recording paths. 2,559 recordings were read successfully with the expected channels, matching channel/time-axis lengths, and no non-finite values.

One file needs separate handling:

```text
KA08/N15_M01_F10_KA08_2.mat
```

SciPy can identify it as a MATLAB v5 file, but fails while reading one nested matrix in the struct. It is kept locally and is not silently counted as a valid recording.

The signal-content check also found three exact duplicate candidates:

```text
KA04/N09_M07_F10_KA04_17.mat
KA04/N09_M07_F10_KA04_18.mat

KA04/N15_M07_F04_KA04_5.mat
KA04/N15_M07_F04_KA04_6.mat
KA04/N15_M07_F04_KA04_15.mat
KA04/N15_M07_F04_KA04_20.mat

KA04/N15_M07_F04_KA04_19.mat
KA04/N15_M07_F04_KA04_5.mat
```

The first pair is the known replacement. The other groups are connected into one exact duplicate group because recording 5 appears in both comparisons. The first protocol keeps recording 5 and excludes 6, 15, 19, and 20.

The local audit outputs are `outputs/paderborn_audit/recording_audit.csv`, `duplicate_candidates.json`, and `audit_errors.json`.

For the first protocol, one file is kept per exact signal duplicate group. Recording 18 is kept for the known `N09_M07_F10` replacement. The connected `N15_M07_F04` group keeps recording 5 and excludes 6, 15, 19, and 20.
