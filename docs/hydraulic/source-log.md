# Hydraulic source log

## Verified source record

Checked on 2026-08-24.

| Item | Record |
|---|---|
| Official source | [UCI Machine Learning Repository: Condition monitoring of hydraulic systems](https://archive.ics.uci.edu/dataset/447/condition%2Bmonitoring%2Bof%2Bhydraulic%2Bsystems) |
| Dataset identifier | UCI dataset 447 |
| Dataset DOI | [10.24432/C5CW21](https://doi.org/10.24432/C5CW21) |
| Dataset citation | Helwig, N., Pignanelli, E., & Schütze, A. (2015). *Condition monitoring of hydraulic systems* [Dataset]. UCI Machine Learning Repository. |
| Dataset license | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Local metadata | [`description.txt`](../../data/hydraulic/raw/description.txt), [`documentation.txt`](../../data/hydraulic/raw/documentation.txt) |

## Source claims used by the audit

The official record and the retained local metadata support the following statements:

- The data come from a hydraulic test rig with primary working and secondary cooling-filtration circuits.
- The rig repeats constant-load cycles of 60 seconds.
- The dataset contains 2,205 cycles and raw tab-delimited process measurements.
- The primary recorded quantities are pressure, motor power, volume flow, temperature, and vibration. `CE` and `CP` are identified as virtual quantities in the metadata. `SE` is listed as an efficiency factor, but its measured or derived status is not resolved by the retained metadata.
- `profile.txt` contains cycle-level values for cooler condition, valve condition, internal pump leakage, hydraulic accumulator pressure, and the stable flag.

## Verification record

The local dimensions and `profile.txt` value counts were checked with the `windfusion` Conda environment:

```text
conda run -n windfusion python src/check_dataset.py
```

The command completed with exit code 0. It reported the expected 2,205 rows for all channel files and a `2205 × 5` `profile.txt` matrix. The detailed counts are recorded in [`measurement-audit.md`](measurement-audit.md).

This log records the dataset source and attribution. It does not assign a license to the project source code.
