<!--
 * @Author: Will Cheng will.chengyong@gmail.com
 * @LastEditors: Will Cheng will.chengyong@gmail.com
 * @FilePath: /operating-state-aware-monitoring/docs/paderborn/reproducibility.md
 * @Description:
 *
 * Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
-->
# Paderborn reproducibility

The Paderborn experiments use the `windfusion` Conda environment and local raw recordings. Source code and public notes are tracked in Git; raw recordings and generated outputs stay local.

## Environment

Create the environment from the repository root:

```text
conda env create -f environment.yml
```

If the environment already exists:

```text
conda env update -f environment.yml --prune
```

The verified local run used Python `3.11.16`, NumPy `2.4.6`, SciPy `1.17.1`, pandas `3.0.5`, Matplotlib `3.11.2`, and scikit-learn `1.9.1`.

## Data

Download and extract the Paderborn bearing recordings into:

```text
data/paderborn/raw/
```

The expected local layout and source links are in [`data/paderborn/README.md`](../../data/paderborn/README.md). The primary protocol uses 20 bearings: 6 healthy and 14 accelerated-lifetime damaged bearings. Artificial-damage bearings remain local for later extensions.

The raw directory is ignored by Git. Generated files under `outputs/` are also local and are not part of the public checkout.

## Run order

Run from the repository root:

```text
conda run --no-capture-output -n windfusion python src/read_paderborn_recording.py
conda run --no-capture-output -n windfusion python src/audit_paderborn_recordings.py
conda run --no-capture-output -n windfusion python src/build_paderborn_protocol.py
conda run --no-capture-output -n windfusion python src/run_paderborn_matched_vibration_baseline.py
conda run --no-capture-output -n windfusion python src/run_paderborn_matched_sensor_comparison.py
conda run --no-capture-output -n windfusion python src/run_paderborn_shifted_sensor_comparison.py
conda run --no-capture-output -n windfusion python src/run_paderborn_four_condition_robustness.py
conda run --no-capture-output -n windfusion python src/analyze_paderborn_signal_features.py
conda run --no-capture-output -n windfusion python src/plot_paderborn_robustness_bars.py
conda run --no-capture-output -n windfusion python src/plot_paderborn_shift_drop_heatmap.py
conda run --no-capture-output -n windfusion python src/plot_paderborn_vibration_rms.py
```

The audit and protocol steps should be completed before the classification runs. The protocol script creates the local manifest and fixed bearing-level folds under `outputs/paderborn_protocol/`.

## Quick checks

Compile the Paderborn scripts without running the data experiments:

```text
conda run --no-capture-output -n windfusion python -m py_compile src/read_paderborn_recording.py src/audit_paderborn_recordings.py src/build_paderborn_protocol.py src/run_paderborn_matched_vibration_baseline.py src/run_paderborn_matched_sensor_comparison.py src/run_paderborn_shifted_sensor_comparison.py src/run_paderborn_four_condition_robustness.py src/analyze_paderborn_signal_features.py src/plot_paderborn_robustness_bars.py src/plot_paderborn_shift_drop_heatmap.py src/plot_paderborn_vibration_rms.py
```

The experiments use deterministic bearing-level folds, fixed feature names, fixed sensor groups, and fixed condition-selection rules. No random seed is needed for the current protocol.

## Current local verification

The current local environment passed the Python compilation check and each Paderborn experiment exited successfully after the raw recordings were extracted. The public repository does not contain the raw recordings or generated CSV/JSON results, so a new checkout must prepare the data directory before running the commands above.

The three main figures are committed under `docs/paderborn/figures/` and are embedded in the corresponding public notes.
