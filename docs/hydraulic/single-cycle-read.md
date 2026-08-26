# Single-cycle read

## Reproducible command

Run the reader from the repository root with the `windfusion` Conda environment:

```text
conda run --no-capture-output -n windfusion python src/read_single_cycle.py
```

The verified run completed with exit code 0. The reader uses `cycle_index=211`, where the index is zero-based.

## Verified channel timing

The selected row is read separately from each raw channel file. The reader keeps the sampling rates as recorded and does not resample the signals.

| Channels | Physical quantity | Samples | Sampling rate | Time axis |
|---|---|---:|---:|---|
| PS1–PS6, EPS1 | Pressure; motor power | 6,000 | 100 Hz | 0.00–59.99 s |
| FS1–FS2 | Volume flow | 600 | 10 Hz | 0.00–59.90 s |
| TS1–TS4 | Temperature | 60 | 1 Hz | 0.00–59.00 s |
| VS1 | Vibration | 60 | 1 Hz | 0.00–59.00 s |
| CE, CP | Cooling efficiency; cooling power (virtual) | 60 | 1 Hz | 0.00–59.00 s |
| SE | Efficiency factor (classification unresolved) | 60 | 1 Hz | 0.00–59.00 s |

Each channel has 60 seconds of recorded duration. The final timestamp is determined by the sample index and the channel sampling rate; it is not set to 60 seconds for every last sample.

## Selected cycle labels

The `profile.txt` row with the same index is read with the channel data:

| Field | Value |
|---|---:|
| Cooler condition | 3 |
| Valve condition | 73 |
| Pump leakage | 2 |
| Accumulator pressure | 130 |
| Stable flag | 0 |

## Reader checks

[`src/read_single_cycle.py`](../../src/read_single_cycle.py) checks that:

- each requested file exists;
- each channel file contains 2,205 cycle rows;
- the selected row has the expected number of samples;
- the selected channel row and profile row contain no missing values;
- each selected channel has the expected 60-second duration;
- the profile row uses the same cycle index as the channel files.

The reader prints the result and does not create a derived data file. Raw data remain under `data/hydraulic/raw/` as local input.

This step verifies data access and time-axis alignment only. It does not perform feature extraction, resampling, normalization, or model fitting.
