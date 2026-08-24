# Hydraulic audit open questions

## Sensor locations and schematic

The available UCI metadata identifies each channel's physical quantity, unit, and sampling rate, but it does not provide a verified sensor-to-component location map or a schematic in the retained local files. Do not assign `PS1`–`PS6`, `FS1`–`FS2`, `TS1`–`TS4`, or `VS1` to a specific physical position until a source for that mapping is found.

## `SE` classification

`description.txt` calls `SE` an “Efficiency factor” and lists it with a 1 Hz sampling rate. It does not label `SE` as virtual, while it explicitly labels `CE` and `CP` as virtual. `SE` therefore remains unresolved and should not be silently placed in either the measured or virtual primary-input group.

## Cycle independence and run structure

The dataset contains 2,205 cycles, but the retained metadata does not define run IDs, batch IDs, or an independent-experiment grouping. Different cycle rows must not be treated as independent experimental runs without further evidence.
