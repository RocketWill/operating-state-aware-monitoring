'''
Author: Will Cheng will.chengyong@gmail.com
LastEditors: Will Cheng will.chengyong@gmail.com
FilePath: /operating-state-aware-monitoring/src/build_paderborn_protocol.py
Description:

Copyright (c) 2026 by will.chengyong@gmail.com, All Rights Reserved.
'''
import csv
import json
from pathlib import Path


RAW_DIR = Path("data/paderborn/raw")
OUTPUT_DIR = Path("outputs/paderborn_protocol")
TEST_CONDITION = "N15_M07_F10"
CONDITIONS = [
    "N15_M07_F10",
    "N09_M07_F10",
    "N15_M01_F10",
    "N15_M07_F04",
]


BEARINGS = [
    ("K001", "healthy", "reference", True),
    ("K002", "healthy", "reference", True),
    ("K003", "healthy", "reference", True),
    ("K004", "healthy", "reference", True),
    ("K005", "healthy", "reference", True),
    ("K006", "healthy", "reference", True),
    ("KA01", "damaged", "artificial", False),
    ("KA03", "damaged", "artificial", False),
    ("KA05", "damaged", "artificial", False),
    ("KA06", "damaged", "artificial", False),
    ("KA07", "damaged", "artificial", False),
    ("KA08", "damaged", "artificial", False),
    ("KA09", "damaged", "artificial", False),
    ("KI01", "damaged", "artificial", False),
    ("KI03", "damaged", "artificial", False),
    ("KI05", "damaged", "artificial", False),
    ("KI07", "damaged", "artificial", False),
    ("KI08", "damaged", "artificial", False),
    ("KA04", "damaged", "accelerated_lifetime", True),
    ("KA16", "damaged", "accelerated_lifetime", True),
    ("KA22", "damaged", "accelerated_lifetime", True),
    ("KA15", "damaged", "accelerated_lifetime", True),
    ("KA30", "damaged", "accelerated_lifetime", True),
    ("KB23", "damaged", "accelerated_lifetime", True),
    ("KB24", "damaged", "accelerated_lifetime", True),
    ("KB27", "damaged", "accelerated_lifetime", True),
    ("KI04", "damaged", "accelerated_lifetime", True),
    ("KI14", "damaged", "accelerated_lifetime", True),
    ("KI16", "damaged", "accelerated_lifetime", True),
    ("KI17", "damaged", "accelerated_lifetime", True),
    ("KI18", "damaged", "accelerated_lifetime", True),
    ("KI21", "damaged", "accelerated_lifetime", True),
]


FOLDS = {
    "fold_1": ["K001", "K004", "KA04", "KA15", "KB23", "KI14"],
    "fold_2": ["K002", "K005", "KA16", "KA22", "KB24", "KI04", "KI16"],
    "fold_3": ["K003", "K006", "KA30", "KB27", "KI17", "KI18", "KI21"],
}


# Exact signal duplicates found in the first full audit.
DUPLICATE_KEEP = {
    "KA04/N09_M07_F10_KA04_18.mat",
    "KA04/N15_M07_F04_KA04_5.mat",
}
DUPLICATE_EXCLUDE = {
    "KA04/N09_M07_F10_KA04_17.mat",
    "KA04/N15_M07_F04_KA04_6.mat",
    "KA04/N15_M07_F04_KA04_15.mat",
    "KA04/N15_M07_F04_KA04_19.mat",
    "KA04/N15_M07_F04_KA04_20.mat",
}


def recording_name(condition, bearing_id, recording_id):
    # The dataset uses 1..20, not zero-padded 01..20.
    return f"{condition}_{bearing_id}_{recording_id}.mat"


def build_manifest():
    rows = []
    for bearing_id, label, damage_source, include_primary in BEARINGS:
        archive_exists = (RAW_DIR / f"{bearing_id}.rar").exists()
        for condition in CONDITIONS:
            for recording_id in range(1, 21):
                duplicate = (
                    bearing_id == "KA04"
                    and condition == "N09_M07_F10"
                    and recording_id == 17
                )
                filename = recording_name(condition, bearing_id, recording_id)
                extracted_path = RAW_DIR / bearing_id / filename
                relative_path = f"{bearing_id}/{filename}"
                duplicate_candidate = relative_path in (
                    DUPLICATE_KEEP | DUPLICATE_EXCLUDE
                )
                rows.append(
                    {
                        "bearing_id": bearing_id,
                        "label": label,
                        "damage_source": damage_source,
                        "include_primary": str(include_primary).lower(),
                        "condition": condition,
                        "recording_id": recording_id,
                        "filename": filename,
                        "archive_downloaded": str(archive_exists).lower(),
                        "extracted_here": str(extracted_path.exists()).lower(),
                        "local_available": str(archive_exists or extracted_path.exists()).lower(),
                        "duplicate_replacement": str(
                            duplicate or relative_path in DUPLICATE_EXCLUDE
                        ).lower(),
                        "duplicate_candidate": str(duplicate_candidate).lower(),
                        "include_recording": str(
                            not duplicate and relative_path not in DUPLICATE_EXCLUDE
                        ).lower(),
                    }
                )
    return rows


def build_protocol():
    primary_ids = [bearing_id for bearing_id, _, _, include in BEARINGS if include]
    shift_conditions = [condition for condition in CONDITIONS if condition != TEST_CONDITION]
    return {
        "target": {
            "name": "bearing_damage",
            "task": "binary_classification",
            "classes": {"healthy": 0, "damaged": 1},
            "primary_damage_sources": ["accelerated_lifetime"],
            "excluded_from_primary": ["artificial"],
        },
        "primary_bearings": primary_ids,
        "folds": FOLDS,
        "split_rule": "all recordings from one bearing stay on one side",
        "test_condition": TEST_CONDITION,
        "test_recordings": "recording_id 1..20 at the test condition, excluding listed duplicates",
        "matched_train": "same test condition, all non-test bearings",
        "shifted_train": {
            "conditions": shift_conditions,
            "recordings_per_bearing": 20,
            "sampling_rule": "use N09_M07_F10 -> N15_M01_F10 -> N15_M07_F04 repeatedly by recording_id; skip excluded duplicates and continue to the next eligible row",
        },
        "features": ["mean", "std", "rms", "peak_to_peak"],
        "sensor_groups": {
            "current": ["phase_current_1", "phase_current_2"],
            "vibration": ["vibration_1"],
            "combined": ["phase_current_1", "phase_current_2", "vibration_1"],
        },
        "model": "StandardScaler + logistic regression, fixed before test evaluation",
        "metrics": ["macro_f1", "balanced_accuracy", "per_class_recall", "confusion_matrix"],
        "duplicate_rule": "keep one file per exact signal duplicate group; keep KA04 N09_M07_F10 recording 18 per measuring log",
        "note": "Full archives and all duplicate checks are not downloaded yet.",
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_manifest()
    with (OUTPUT_DIR / "recording_manifest.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with (OUTPUT_DIR / "protocol.json").open("w") as handle:
        json.dump(build_protocol(), handle, indent=2)

    primary = [row for row in rows if row["include_primary"] == "true"]
    duplicate_count = sum(row["duplicate_replacement"] == "true" for row in rows)
    extracted_count = sum(row["extracted_here"] == "true" for row in rows)
    print(f"bearings: {len({row['bearing_id'] for row in rows})}")
    print(f"primary bearings: {len({row['bearing_id'] for row in primary})}")
    print(f"primary recordings: {len(primary) - duplicate_count}")
    print(f"duplicate rows marked: {duplicate_count}")
    print(f"extracted recordings present locally: {extracted_count}")
    print(f"saved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
