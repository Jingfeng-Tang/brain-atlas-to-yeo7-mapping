import tempfile
import unittest
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from mapping_aal116_to_yeo import (
    compute_mapping,
    load_aal_labels,
    module_payload,
)


class AAL116MappingTests(unittest.TestCase):
    def test_overlap_assignment_and_coverage_guard(self):
        aal = np.zeros((4, 4, 4), dtype=np.int32)
        aal[:2] = 2001
        aal[2:] = 2002
        yeo = np.zeros_like(aal)
        yeo[:2, :3] = 1
        yeo[:2, 3:] = 2
        yeo[2, :1] = 7

        rows = []
        for index in range(116):
            value = 2001 + index
            rows.append(
                {
                    "AAL_Index": index + 1,
                    "AAL_Index_0based": index,
                    "AAL_Value": value,
                    "AAL_ROI": "ROI_{}".format(index + 1),
                    "Hemisphere": "Midline",
                }
            )
        labels = pd.DataFrame(rows)
        # Give unused synthetic labels one voxel each in an expanded vector.
        extra_aal = np.arange(2003, 2117, dtype=np.int32).reshape(114, 1, 1)
        extra_yeo = np.zeros_like(extra_aal)
        aal = np.concatenate((aal.reshape(64, 1, 1), extra_aal), axis=0)
        yeo = np.concatenate((yeo.reshape(64, 1, 1), extra_yeo), axis=0)

        mapping, mapped = compute_mapping(aal, yeo, labels, min_coverage=0.5)
        self.assertEqual(int(mapping.iloc[0]["Yeo_Network"]), 1)
        self.assertEqual(int(mapping.iloc[1]["Yeo_Network"]), 0)
        self.assertTrue(np.all(mapped[aal == 2001] == 1))
        self.assertTrue(np.all(mapped[aal == 2002] == 0))
        payload = module_payload(mapping, 0.5)
        all_nodes = sorted(
            node
            for module in payload["modules"].values()
            for node in module["aal_indices_0based"]
        )
        self.assertEqual(all_nodes, list(range(116)))

    def test_label_table_requires_matrix_order(self):
        rows = []
        for index in range(116):
            rows.append(
                {
                    "AAL_Index": index + 1,
                    "AAL_Index_0based": index,
                    "AAL_Value": 3000 + index,
                    "AAL_ROI": "ROI_{}".format(index + 1),
                    "Hemisphere": "Midline",
                }
            )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labels.csv"
            pd.DataFrame(rows).to_csv(path, index=False)
            loaded = load_aal_labels(path)
        self.assertEqual(loaded.shape[0], 116)
        self.assertEqual(int(loaded.iloc[-1]["AAL_Index_0based"]), 115)


if __name__ == "__main__":
    unittest.main()
