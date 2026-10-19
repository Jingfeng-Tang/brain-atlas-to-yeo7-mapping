"""Map SPM12 AAL116 regions to Yeo-7 networks by spatial overlap.

The AAL atlas uses non-consecutive voxel labels.  The accompanying label file
therefore provides the authoritative ROI order for a 116-by-116 connectivity
matrix.  Each AAL region is assigned to the Yeo network occupying the largest
number of its Yeo-covered voxels.  Regions with insufficient Yeo coverage are
kept as network 0 instead of being forced into a cortical network.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, Tuple

import nibabel as nib
import numpy as np
import pandas as pd
from nibabel.processing import resample_from_to


YEO_NAMES = {
    0: "NonCorticalOrUnassigned",
    1: "Visual",
    2: "Somatomotor",
    3: "DorsalAttention",
    4: "VentralAttention",
    5: "Limbic",
    6: "Frontoparietal",
    7: "DefaultMode",
}

REQUIRED_LABEL_COLUMNS = (
    "AAL_Index",
    "AAL_Index_0based",
    "AAL_Value",
    "AAL_ROI",
    "Hemisphere",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Map AAL116 ROIs to Yeo-7 networks in MNI space."
    )
    parser.add_argument("--aal-path", type=Path, required=True)
    parser.add_argument("--aal-labels", type=Path, required=True)
    parser.add_argument(
        "--yeo-path",
        type=Path,
        default=Path(
            "Yeo2011_7Networks_MNI152_FreeSurferConformed1mm_LiberalMask.nii.gz"
        ),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("AAL116_to_Yeo7_Mapping.csv"),
    )
    parser.add_argument(
        "--output-modules",
        type=Path,
        default=Path("AAL116_to_Yeo7_ModuleNodes.json"),
    )
    parser.add_argument(
        "--output-resampled",
        type=Path,
        default=Path("AAL116_resampled_to_Yeo7.nii.gz"),
    )
    parser.add_argument(
        "--output-mapped",
        type=Path,
        default=Path("AAL116_to_Yeo7_Mapped.nii.gz"),
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0.25,
        help=(
            "Minimum fraction of an AAL ROI covered by nonzero Yeo voxels. "
            "Lower-coverage regions remain network 0."
        ),
    )
    return parser.parse_args()


def load_label_image(path: Path, description: str) -> nib.Nifti1Image:
    if not path.is_file():
        raise FileNotFoundError("Missing {}: {}".format(description, path))
    image = nib.squeeze_image(nib.load(str(path)))
    if len(image.shape) != 3:
        raise ValueError(
            "{} must be a 3D label image, got {}".format(
                description, image.shape
            )
        )
    data = np.asanyarray(image.dataobj)
    if not np.isfinite(data).all():
        raise ValueError("{} contains NaN or Inf".format(description))
    rounded = np.rint(data)
    if not np.allclose(data, rounded, rtol=0.0, atol=1e-6):
        raise ValueError("{} contains non-integer labels".format(description))
    return nib.Nifti1Image(
        rounded.astype(np.int32), image.affine, image.header
    )


def load_aal_labels(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError("Missing AAL label table: {}".format(path))
    table = pd.read_csv(path)
    missing = [name for name in REQUIRED_LABEL_COLUMNS if name not in table]
    if missing:
        raise ValueError("AAL label table is missing columns: {}".format(missing))
    table = table.loc[:, REQUIRED_LABEL_COLUMNS].copy()
    table["AAL_Index"] = table["AAL_Index"].astype(int)
    table["AAL_Index_0based"] = table["AAL_Index_0based"].astype(int)
    table["AAL_Value"] = table["AAL_Value"].astype(int)
    table = table.sort_values("AAL_Index").reset_index(drop=True)
    if table.shape[0] != 116:
        raise ValueError("Expected 116 AAL rows, got {}".format(table.shape[0]))
    if table["AAL_Index"].tolist() != list(range(1, 117)):
        raise ValueError("AAL_Index must be exactly 1..116")
    if table["AAL_Index_0based"].tolist() != list(range(116)):
        raise ValueError("AAL_Index_0based must be exactly 0..115")
    if table["AAL_Value"].duplicated().any():
        raise ValueError("AAL_Value contains duplicates")
    return table


def resample_aal_to_yeo(
    aal_image: nib.Nifti1Image, yeo_image: nib.Nifti1Image
) -> nib.Nifti1Image:
    resampled = resample_from_to(
        aal_image,
        (yeo_image.shape, yeo_image.affine),
        order=0,
        mode="constant",
        cval=0,
    )
    data = np.rint(np.asanyarray(resampled.dataobj)).astype(np.int32)
    return nib.Nifti1Image(data, yeo_image.affine, yeo_image.header)


def overlap_text(counts: np.ndarray, covered_voxels: int) -> str:
    if covered_voxels == 0:
        return ""
    entries = []
    for network in range(1, 8):
        count = int(counts[network])
        if count:
            entries.append(
                "{}:{:.6f}".format(network, count / covered_voxels)
            )
    return ";".join(entries)


def compute_mapping(
    aal_data: np.ndarray,
    yeo_data: np.ndarray,
    labels: pd.DataFrame,
    min_coverage: float,
) -> Tuple[pd.DataFrame, np.ndarray]:
    if aal_data.shape != yeo_data.shape:
        raise ValueError(
            "Aligned AAL and Yeo shapes differ: {} vs {}".format(
                aal_data.shape, yeo_data.shape
            )
        )
    if not 0.0 <= min_coverage <= 1.0:
        raise ValueError("min_coverage must lie in [0, 1]")
    unexpected_yeo = sorted(
        int(value)
        for value in np.unique(yeo_data)
        if int(value) not in range(8)
    )
    if unexpected_yeo:
        raise ValueError(
            "Yeo atlas contains labels outside 0..7: {}".format(
                unexpected_yeo
            )
        )

    atlas_values = set(int(value) for value in np.unique(aal_data) if value)
    expected_values = set(labels["AAL_Value"].astype(int))
    missing_values = sorted(expected_values.difference(atlas_values))
    unexpected_values = sorted(atlas_values.difference(expected_values))
    if missing_values or unexpected_values:
        raise ValueError(
            "Resampled AAL labels do not match the table; missing={}, "
            "unexpected={}".format(missing_values, unexpected_values)
        )

    mapped_volume = np.zeros_like(aal_data, dtype=np.uint8)
    records = []
    for row in labels.itertuples(index=False):
        roi_mask = aal_data == int(row.AAL_Value)
        total_voxels = int(np.count_nonzero(roi_mask))
        values = yeo_data[roi_mask].astype(np.int64, copy=False)
        covered = values[values != 0]
        covered_voxels = int(covered.size)
        coverage = covered_voxels / total_voxels
        counts = np.bincount(covered, minlength=8)
        winner = int(np.argmax(counts[1:8]) + 1) if covered_voxels else 0
        winner_voxels = int(counts[winner]) if winner else 0
        confidence_covered = (
            winner_voxels / covered_voxels if covered_voxels else 0.0
        )
        confidence_roi = winner_voxels / total_voxels
        assigned = winner if coverage >= min_coverage else 0
        mapped_volume[roi_mask] = assigned
        records.append(
            {
                "AAL_Index": int(row.AAL_Index),
                "AAL_Index_0based": int(row.AAL_Index_0based),
                "AAL_Value": int(row.AAL_Value),
                "AAL_ROI": str(row.AAL_ROI),
                "Hemisphere": str(row.Hemisphere),
                "Yeo_Network": assigned,
                "Yeo_Network_Name": YEO_NAMES[assigned],
                "ROI_Voxels": total_voxels,
                "Yeo_Covered_Voxels": covered_voxels,
                "Yeo_Coverage": round(coverage, 6),
                "Winner_Voxels": winner_voxels,
                "Confidence_Among_Covered": round(confidence_covered, 6),
                "Confidence_Whole_ROI": round(confidence_roi, 6),
                "Yeo_Overlap_Fractions": overlap_text(
                    counts, covered_voxels
                ),
            }
        )
    return pd.DataFrame.from_records(records), mapped_volume


def module_payload(mapping: pd.DataFrame, min_coverage: float) -> Dict[str, object]:
    modules = {}
    for network in range(8):
        rows = mapping.loc[mapping["Yeo_Network"] == network]
        modules[str(network)] = {
            "name": YEO_NAMES[network],
            "aal_indices_0based": rows["AAL_Index_0based"].astype(int).tolist(),
            "aal_indices_1based": rows["AAL_Index"].astype(int).tolist(),
            "aal_values": rows["AAL_Value"].astype(int).tolist(),
            "roi_names": rows["AAL_ROI"].astype(str).tolist(),
        }
    return {
        "atlas": "AAL116_SPM12",
        "target": "Yeo2011_7Networks",
        "assignment": "winner_take_all_spatial_overlap",
        "minimum_yeo_coverage": min_coverage,
        "matrix_node_order": "AAL_Index_0based",
        "modules": modules,
    }


def ensure_parents(paths: Iterable[Path]) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()
    ensure_parents(
        (
            args.output_csv,
            args.output_modules,
            args.output_resampled,
            args.output_mapped,
        )
    )
    aal_image = load_label_image(args.aal_path, "AAL116 atlas")
    yeo_image = load_label_image(args.yeo_path, "Yeo-7 atlas")
    labels = load_aal_labels(args.aal_labels)

    resampled = resample_aal_to_yeo(aal_image, yeo_image)
    aal_data = np.asanyarray(resampled.dataobj).astype(np.int32)
    yeo_data = np.asanyarray(yeo_image.dataobj).astype(np.int32)
    mapping, mapped_volume = compute_mapping(
        aal_data, yeo_data, labels, args.min_coverage
    )

    nib.save(resampled, str(args.output_resampled))
    nib.save(
        nib.Nifti1Image(mapped_volume, yeo_image.affine, yeo_image.header),
        str(args.output_mapped),
    )
    mapping.to_csv(args.output_csv, index=False)
    args.output_modules.write_text(
        json.dumps(
            module_payload(mapping, args.min_coverage),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("Mapped all {} AAL116 regions.".format(mapping.shape[0]))
    for network in range(8):
        count = int((mapping["Yeo_Network"] == network).sum())
        print("  {} {:<25} {}".format(network, YEO_NAMES[network], count))
    print("Mapping CSV: {}".format(args.output_csv.resolve()))
    print("H2GT modules: {}".format(args.output_modules.resolve()))
    print("Resampled atlas: {}".format(args.output_resampled.resolve()))
    print("Mapped atlas: {}".format(args.output_mapped.resolve()))


if __name__ == "__main__":
    main()
