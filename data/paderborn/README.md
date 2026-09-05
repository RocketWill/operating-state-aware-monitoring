# Paderborn bearing dataset / Paderborn 軸承資料集

## English

This directory contains the local source files used for the Paderborn bearing study.

The data comes from the [Paderborn University Bearing DataCenter](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter). It contains measurements from 32 bearings: 6 healthy bearings, 12 bearings with artificial damage, and 14 bearings damaged through accelerated lifetime tests.

Each bearing was measured under four operating conditions. The conditions change rotational speed, load torque, or radial force. Each condition normally contains 20 recordings of about 4 seconds.

The main signals are:

| Signal | Description | Nominal sampling rate |
|---|---|---:|
| `phase_current_1`, `phase_current_2` | Two motor phase-current channels | 64 kHz |
| `vibration_1` | Acceleration measured at the bearing housing | 64 kHz |
| `force`, `speed`, `torque` | Mechanical operating measurements | 4 kHz |
| `temp_2_bearing_module` | Bearing-module temperature | 1 Hz |

The local `raw/` directory currently contains the `K001` healthy-bearing archive and the `KA04` damaged-bearing archive. They are used to check the MATLAB structure before downloading the full dataset. Raw archives and extracted recordings stay local and are not committed to Git.

The MATLAB files contain their own time arrays. Sample counts can vary slightly between recordings, so readers should use the recorded time axis instead of assuming a fixed number of samples. The `Unit` fields in the checked files are empty. Signal units and scaling should therefore remain marked as unverified until they can be traced to source metadata.

One known duplicate is also present: `N09_M07_F10_KA04_17.mat` is a replacement copy of recording 18. The two recordings should not both contribute weight to a later experiment.

## 中文

這個資料夾保存 Paderborn bearing study 使用的本地原始資料。

資料來自 [Paderborn University Bearing DataCenter](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter)，共有 32 個 bearings：6 個 healthy bearings、12 個 artificial damage bearings，以及 14 個透過 accelerated lifetime test 產生損傷的 bearings。

每個 bearing 都在四種 operating conditions 下量測。這四種設定分別改變轉速、負載扭矩或徑向力，每個 condition 原則上包含 20 筆、每筆約 4 秒的 recordings。

主要 signals 包含：

| Signal | 說明 | 標稱取樣率 |
|---|---|---:|
| `phase_current_1`, `phase_current_2` | 兩相 motor current | 64 kHz |
| `vibration_1` | Bearing housing 的加速度訊號 | 64 kHz |
| `force`, `speed`, `torque` | Operating condition 的機械量測 | 4 kHz |
| `temp_2_bearing_module` | Bearing module temperature | 1 Hz |

目前 `raw/` 只有 healthy bearing `K001` 和 damaged bearing `KA04`，先用來確認 MATLAB 檔案結構，再決定完整下載範圍。Raw archives 與解壓後的 recordings 都保留在本地，不提交到 Git。

MATLAB 檔案內有自己的時間軸，而且不同 recording 的點數可能略有差異。讀取時應使用檔案內的時間資料，不要直接假設每筆都是固定點數。目前抽查檔案的 `Unit` 欄位是空的，因此 signal unit 和 scaling 在找到明確來源前，仍標示為未確認。

另外，`N09_M07_F10_KA04_17.mat` 是第 18 筆 recording 的替代副本，兩者訊號完全相同。後續實驗不能讓這兩筆同時增加資料權重。

## Source, citation, and license / 來源、引用與授權

- Dataset: [KAt Bearing DataCenter](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter)
- Download index: [Bearing DataCenter files](https://groups.uni-paderborn.de/kat/BearingDataCenter/)
- License: [Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/)

Citation:

> Lessmeier, C., Kimotho, J. K., Zimmer, D., & Sextro, W. (2016). *Condition Monitoring of Bearing Damage in Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchmark Data Set for Data-Driven Classification*. European Conference of the Prognostics and Health Management Society, Bilbao, Spain.

The dataset license permits noncommercial academic use with attribution. Commercial use requires contacting the data provider.
