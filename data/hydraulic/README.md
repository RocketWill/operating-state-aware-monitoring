# Hydraulic dataset

This directory contains the local raw files used for the hydraulic measurement study.

## Source

The source dataset is [Condition monitoring of hydraulic systems](https://archive.ics.uci.edu/dataset/447/condition%2Bmonitoring%2Bof%2Bhydraulic%2Bsystems) from the UCI Machine Learning Repository, dataset 447.

The dataset contains 2,205 operating cycles. Each cycle lasts 60 seconds. The raw channel files are tab-delimited matrices: each row is one cycle and each column is one sequential sample within that cycle. `profile.txt` contains five cycle-level target or status fields.

The local copy is kept under `raw/`. Its metadata files are `description.txt` and `documentation.txt`.

## Citation

Helwig, N., Pignanelli, E., & Schütze, A. (2015). *Condition monitoring of hydraulic systems* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CW21

## License

The UCI dataset page states that the dataset is available under the [Creative Commons Attribution 4.0 International license (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Sharing and adaptation are allowed when appropriate credit is given.

Keep the source citation and license notice with any copied or adapted dataset files.
