# 脑图谱到 Yeo-7 网络映射

<div align="center">

[English](./README.md) | **简体中文**

</div>

本项目将 **HCP MMP 1.0 (Glasser 360)** 和 **AAL116 (SPM12)** 图谱映射到 **Yeo 2011 (7 Networks)** 功能分区。项目将图谱对齐到相同的 MNI 空间，并根据体素重叠情况为每个解剖区域分配 Yeo 网络。

<table>
  <tr>
    <td align="center" width="25%"><img src="asset/hcp360.png" width="100%" alt="HCP360 原始图谱"></td>
    <td align="center" width="25%"><img src="asset/yeo7.png" width="100%" alt="Yeo 7 网络"></td>
    <td align="center" width="25%"><img src="asset/hcp360_resample.png" width="100%" alt="HCP360 重采样后"></td>
    <td align="center" width="25%"><img src="asset/hcp360_to_yeo7.png" width="100%" alt="映射结果"></td>
  </tr>
  <tr>
   <td align="center"><b>HCP360 (Glasser)</b><br>原始图谱</td>
    <td align="center"><b>Yeo-7</b><br>功能网络</td>
    <td align="center"><b>HCP360 Resampled</b><br>对齐至 Yeo 空间</td>
    <td align="center"><b>Mapping Result</b><br>按 Yeo 网络着色的 HCP 区域</td>
  </tr>
</table>

## 📥 快速获取结果

如果您仅需要最终的对照表，而无需运行处理流程，可以直接下载结果文件：

* **映射文件:** [HCP360_to_Yeo7_Mapping.csv](https://github.com/Jingfeng-Tang/HCP360-Glasser-atlas-mapping-Yeo-7-subnetwork/blob/main/HCP360_to_Yeo7_Mapping.csv)

该 CSV 文件包含了 Glasser ROI ID，Yeo 网络标签和置信度之间的对应关系。


0: 'Unassigned (未分配)'

1: 'Visual (视觉)'

2: 'Somatomotor (体感运动)'

3: 'Dorsal Attention (背侧注意)'

4: 'Ventral Attention (腹侧注意)'

5: 'Limbic (边缘系统)'

6: 'Frontoparietal (额顶控制)'

7: 'Default Mode (默认模式)'

---

## 🚀 使用说明

请按照以下步骤复现映射过程或从头生成文件。

### 0. 环境准备
运行 `pip install -r requirements.txt` 安装依赖。

### 1. 获取 Yeo 图谱
获取 MNI152 空间下的 Yeo 2011 7网络图谱。
* **运行脚本:** `python fetch_yeo.py`
* **直接下载:** [Yeo2011_7Networks_MNI152.nii.gz](https://github.com/Jingfeng-Tang/HCP360-Glasser-atlas-mapping-Yeo-7-subnetwork/blob/main/Yeo2011_7Networks_MNI152_FreeSurferConformed1mm_LiberalMask.nii.gz)

### 2. 获取 HCP360 图谱
获取 Glasser HCP 360 图谱。
* **原始来源:** [Glasser360 Github](https://github.com/brainspaces/glasser360)
* **本项目备份:** [glasser360MNI.nii.gz](https://github.com/Jingfeng-Tang/HCP360-Glasser-atlas-mapping-Yeo-7-subnetwork/blob/main/glasser360MNI.nii.gz)

### 3. 将 HCP360 重采样至 Yeo 空间
对 HCP360 图谱进行重采样，使其分辨率、仿射矩阵和维度与 Yeo 模板完全匹配，以确保体素级对齐。
* **运行:**
    ```bash
    python resample_hcp2yeo.py
    ```

### 4. 生成映射关系
计算重采样后的 HCP ROI 与 Yeo 网络的重叠情况，生成最终的 CSV 映射文件。
* **运行:**
    ```bash
    python mapping_hcp2yeo.py
    ```

### 5. 生成 AAL116 映射

获取 SPM12 版本的 AAL116 图谱及其有序标签：

```bash
python fetch_aal116.py
```

将全部 116 个 AAL 区域映射到 Yeo-7：

```bash
python mapping_aal116_to_yeo.py --aal-path aal116_data/AAL116_SPM12.nii.gz --aal-labels aal116_data/AAL116_SPM12_labels.csv
```

脚本会生成 CSV 对照表、对齐后的 AAL 图谱、映射后的 NIfTI 图像，以及可直接用于 H2GT 的模块 JSON。AAL116 包含皮层、皮层下和小脑区域，而 Yeo-7 是皮层功能分区。因此，Yeo 覆盖率低于 25% 的区域保留为网络 0（`NonCorticalOrUnassigned`），不会被强制分配到某个皮层网络。JSON 中的节点编号采用从 0 开始的标准 AAL116 功能连接矩阵顺序。

---

## 📚 参考文献

如果您在研究中使用了这些图谱，请引用原始文献：

1.  **HCP MMP 1.0 (Glasser 360):**
    > Glasser, M. F., Coalson, T. S., Robinson, E. C., Hacker, C. D., Harwell, J., Yacoub, E., ... & Van Essen, D. C. (2016). A multi-modal parcellation of human cerebral cortex. *Nature*, 536(7615), 171-178.

2.  **Yeo 7 Networks:**
    > Yeo, B. T., Krienen, F. M., Sepulcre, J., Sabuncu, M. R., Lashkari, D., Hollinshead, M., ... & Buckner, R. L. (2011). The organization of the human cerebral cortex estimated by intrinsic functional connectivity. *Journal of neurophysiology*, 106(3), 1125-1165.

3.  **AAL:**
    > Tzourio-Mazoyer, N., Landeau, B., Papathanassiou, D., Crivello, F., Etard, O., Delcroix, N., Mazoyer, B., & Joliot, M. (2002). Automated anatomical labeling of activations in SPM using a macroscopic anatomical parcellation of the MNI MRI single-subject brain. *NeuroImage*, 15(1), 273-289.
