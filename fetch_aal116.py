"""Fetch the SPM12 AAL116 atlas and export its ordered label table."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import nibabel as nib
from nilearn.datasets import fetch_atlas_aal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the SPM12 AAL116 atlas and save the ROI order used by "
            "116-by-116 connectivity matrices."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("aal116_data"),
        help="Directory receiving the atlas and label table.",
    )
    parser.add_argument(
        "--nilearn-data",
        type=Path,
        default=None,
        help="Optional Nilearn cache directory.",
    )
    return parser.parse_args()


def hemisphere_from_name(name: str) -> str:
    if name.endswith("_L"):
        return "Left"
    if name.endswith("_R"):
        return "Right"
    return "Midline"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    atlas = fetch_atlas_aal(
        version="SPM12",
        data_dir=None if args.nilearn_data is None else str(args.nilearn_data),
    )

    labels = [str(label) for label in atlas.labels]
    values = [int(value) for value in atlas.indices]
    if len(labels) != 116 or len(values) != 116:
        raise RuntimeError(
            "Expected 116 SPM12 AAL regions, got {} labels and {} values".format(
                len(labels), len(values)
            )
        )
    if len(set(values)) != 116:
        raise RuntimeError("AAL voxel-label values are not unique")

    atlas_output = args.output_dir / "AAL116_SPM12.nii.gz"
    nib.save(nib.load(str(atlas.maps)), str(atlas_output))

    table_output = args.output_dir / "AAL116_SPM12_labels.csv"
    with table_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("AAL_Index", "AAL_Index_0based", "AAL_Value", "AAL_ROI", "Hemisphere"),
        )
        writer.writeheader()
        for index, (value, label) in enumerate(zip(values, labels), start=1):
            writer.writerow(
                {
                    "AAL_Index": index,
                    "AAL_Index_0based": index - 1,
                    "AAL_Value": value,
                    "AAL_ROI": label,
                    "Hemisphere": hemisphere_from_name(label),
                }
            )

    print("AAL116 atlas: {}".format(atlas_output.resolve()))
    print("AAL116 labels: {}".format(table_output.resolve()))


if __name__ == "__main__":
    main()
