# Anatomical Atlases to Yeo-7 Network Mapping
<div align="center">

**English** | [简体中文](./README_zh-CN.md)

</div>

This project maps the **HCP MMP 1.0 (Glasser 360)** and **AAL116 (SPM12)** atlases to the **Yeo 2011 (7 Networks)** functional parcellation. The atlases are aligned in a common MNI space, and each anatomical region is assigned according to its voxel-wise overlap with the Yeo networks.

<table>
  <tr>
    <td align="center" width="25%"><img src="asset/hcp360.png" width="100%" alt="HCP360 Original"></td>
    <td align="center" width="25%"><img src="asset/yeo7.png" width="100%" alt="Yeo 7 Networks"></td>
    <td align="center" width="25%"><img src="asset/hcp360_resample.png" width="100%" alt="HCP360 Resampled"></td>
    <td align="center" width="25%"><img src="asset/hcp360_to_yeo7.png" width="100%" alt="Mapping Result"></td>
  </tr>
  <tr>
   <td align="center"><b>HCP360 (Glasser)</b><br>Original Atlas</td>
    <td align="center"><b>Yeo-7</b><br>Functional Networks</td>
    <td align="center"><b>HCP360 Resampled</b><br>Aligned to Yeo space</td>
    <td align="center"><b>Mapping Result</b><br>HCP Regions Colored by Yeo Net</td>
  </tr>
</table>

## 📥 Quick Access

If you strictly require the final lookup table and do not need to run the processing pipeline, you can download the result directly:

* **Mapping File:** [HCP360_to_Yeo7_Mapping.csv](https://github.com/Jingfeng-Tang/HCP360-Glasser-atlas-mapping-Yeo-7-subnetwork/blob/main/HCP360_to_Yeo7_Mapping.csv)

This CSV contains the correspondence between Glasser ROI IDs ,Yeo network labels and confidence.

0: 'Unassigned (未分配)'

1: 'Visual (视觉)'

2: 'Somatomotor (体感运动)'

3: 'Dorsal Attention (背侧注意)'

4: 'Ventral Attention (腹侧注意)'

5: 'Limbic (边缘系统)'

6: 'Frontoparietal (额顶控制)'

7: 'Default Mode (默认模式)'



---

## 🚀 Usage

Follow these steps to reproduce the mapping process or generate the files from scratch.

### 0. Prerequisites
Install the dependencies with `pip install -r requirements.txt`.

### 1. Acquire Yeo Atlas
Obtain the Yeo 2011 7-Network atlas in MNI152 space.
* **Run:**
    ```bash
    python fetch_yeo.py
    ```
* **Direct Download:** [Yeo2011_7Networks_MNI152.nii.gz](https://github.com/Jingfeng-Tang/HCP360-Glasser-atlas-mapping-Yeo-7-subnetwork/blob/main/Yeo2011_7Networks_MNI152_FreeSurferConformed1mm_LiberalMask.nii.gz)

### 2. Acquire HCP360 Atlas
Obtain the Glasser HCP 360 atlas.
* **Source:** [Glasser360 Github](https://github.com/brainspaces/glasser360)
* **Backup File:** [glasser360MNI.nii.gz](https://github.com/Jingfeng-Tang/HCP360-Glasser-atlas-mapping-Yeo-7-subnetwork/blob/main/glasser360MNI.nii.gz)

### 3. Resample HCP360 to Yeo Space
Resample the HCP360 atlas to match the resolution, affine matrix, and dimensions of the Yeo template to ensure voxel-wise alignment.
* **Run:**
    ```bash
    python resample_hcp2yeo.py
    ```

### 4. Generate Mapping
Calculate the overlap between the resampled HCP ROIs and the Yeo networks to generate the final CSV mapping file.
* **Run:**
    ```bash
    python mapping_hcp2yeo.py
    ```

### 5. Generate the AAL116 Mapping

Fetch the SPM12 AAL116 atlas and its ordered labels:

```bash
python fetch_aal116.py
```

Map all 116 AAL regions to Yeo-7:

```bash
python mapping_aal116_to_yeo.py --aal-path aal116_data/AAL116_SPM12.nii.gz --aal-labels aal116_data/AAL116_SPM12_labels.csv
```

The script generates a CSV lookup table, an aligned AAL atlas, a mapped NIfTI image, and an H2GT-ready JSON module definition. AAL116 contains cortical, subcortical, and cerebellar regions, whereas Yeo-7 is a cortical parcellation. Regions with less than 25% Yeo coverage are therefore retained as network 0 (`NonCorticalOrUnassigned`) instead of being forced into a cortical network. The JSON uses zero-based AAL indices in the standard 116-by-116 connectivity-matrix order.

---

## 📚 References

If you use these atlases in your research, please cite the original publications:

1.  **HCP MMP 1.0 (Glasser 360):**
    > Glasser, M. F., Coalson, T. S., Robinson, E. C., Hacker, C. D., Harwell, J., Yacoub, E., ... & Van Essen, D. C. (2016). A multi-modal parcellation of human cerebral cortex. *Nature*, 536(7615), 171-178.

2.  **Yeo 7 Networks:**
    > Yeo, B. T., Krienen, F. M., Sepulcre, J., Sabuncu, M. R., Lashkari, D., Hollinshead, M., ... & Buckner, R. L. (2011). The organization of the human cerebral cortex estimated by intrinsic functional connectivity. *Journal of neurophysiology*, 106(3), 1125-1165.

3.  **AAL:**
    > Tzourio-Mazoyer, N., Landeau, B., Papathanassiou, D., Crivello, F., Etard, O., Delcroix, N., Mazoyer, B., & Joliot, M. (2002). Automated anatomical labeling of activations in SPM using a macroscopic anatomical parcellation of the MNI MRI single-subject brain. *NeuroImage*, 15(1), 273-289.
