# Hydraulic measurement audit

## Source, citation, and license

The source is the UCI Machine Learning Repository dataset [Condition monitoring of hydraulic systems](https://archive.ics.uci.edu/dataset/447/condition%2Bmonitoring%2Bof%2Bhydraulic%2Bsystems), dataset 447.

Citation: Helwig, N., Pignanelli, E., & Schütze, A. (2015). *Condition monitoring of hydraulic systems* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CW21

The UCI record states that the dataset is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The local source metadata is retained in [`data/hydraulic/raw/description.txt`](../../data/hydraulic/raw/description.txt) and [`data/hydraulic/raw/documentation.txt`](../../data/hydraulic/raw/documentation.txt).

## Dataset structure

The dataset contains 2,205 operating cycles. Each cycle has a duration
of 60 seconds.

Raw measurement files are stored separately by channel. Rows correspond
to operating cycles, while columns represent sequential samples within
a cycle.

Observed raw-file dimensions:

| Channels | Shape | Samples per cycle |
|---|---:|---:|
| PS1–PS6 | 2205 × 6000 | 6000 |
| EPS1 | 2205 × 6000 | 6000 |
| FS1–FS2 | 2205 × 600 | 600 |
| TS1–TS4 | 2205 × 60 | 60 |
| VS1 | 2205 × 60 | 60 |
| CE, CP, SE | 2205 × 60 | 60 |
| profile | 2205 × 5 | 5 target/status fields |

The observed sample counts are consistent with the documented
100 Hz, 10 Hz, and 1 Hz sampling rates over each 60-second cycle.

## Target profile

`profile.txt` has shape `2205 × 5`. Each row corresponds to the same
operating cycle index used by the measurement files.

| Column | Target | Observed values | Counts |
|---|---|---|---|
| 0 | Cooler condition | 3, 20, 100 | 732, 732, 741 |
| 1 | Valve condition | 73, 80, 90, 100 | 360, 360, 360, 1125 |
| 2 | Internal pump leakage | 0, 1, 2 | 1221, 492, 492 |
| 3 | Hydraulic accumulator | 90, 100, 115, 130 | 808, 399, 399, 599 |
| 4 | Stable flag | 0, 1 | 1449, 756 |

These counts were verified directly from the downloaded `profile.txt`.

The rows are not assumed to represent independent experimental runs.
Run/group structure remains to be established separately.

## Measurement channels

Source: dataset-provided `description.txt`.

| Channel | Physical quantity | Unit | Sampling rate | Classification |
|---|---|---|---:|---|
| PS1 | Pressure | bar | 100 Hz | Measured |
| PS2 | Pressure | bar | 100 Hz | Measured |
| PS3 | Pressure | bar | 100 Hz | Measured |
| PS4 | Pressure | bar | 100 Hz | Measured |
| PS5 | Pressure | bar | 100 Hz | Measured |
| PS6 | Pressure | bar | 100 Hz | Measured |
| EPS1 | Motor power | W | 100 Hz | Measured |
| FS1 | Volume flow | l/min | 10 Hz | Measured |
| FS2 | Volume flow | l/min | 10 Hz | Measured |
| TS1 | Temperature | °C | 1 Hz | Measured |
| TS2 | Temperature | °C | 1 Hz | Measured |
| TS3 | Temperature | °C | 1 Hz | Measured |
| TS4 | Temperature | °C | 1 Hz | Measured |
| VS1 | Vibration | mm/s | 1 Hz | Measured |
| CE | Cooling efficiency | % | 1 Hz | Virtual |
| CP | Cooling power | kW | 1 Hz | Virtual |
| SE | Efficiency factor | % | 1 Hz | Unresolved |

## Target definitions

The target values are quantitative condition values, except for the stable flag. The source metadata gives the following meanings:

| Target | Values and meaning |
|---|---|
| Cooler condition | `3`: close to total failure; `20`: reduced efficiency; `100`: full efficiency |
| Valve condition | `100`: optimal switching behavior; `90`: small lag; `80`: severe lag; `73`: close to total failure |
| Internal pump leakage | `0`: no leakage; `1`: weak leakage; `2`: severe leakage |
| Hydraulic accumulator | `130`: optimal pressure; `115`: slightly reduced pressure; `100`: severely reduced pressure; `90`: close to total failure |
| Stable flag | `0`: conditions were stable; `1`: static conditions might not have been reached yet |

The first four targets describe degradation or condition levels. They should not automatically be treated as nominal class labels without deciding the task definition first.

## Vibration channel

`VS1` is a measured vibration channel with units of `mm/s` and a sampling rate of `1 Hz`. The available data support cycle-level summaries or comparisons at this recorded rate. They do not, by themselves, support high-frequency vibration spectrum analysis, envelope analysis, or a verified bearing-fault diagnosis. The sensor location is not identified in the retained metadata.
