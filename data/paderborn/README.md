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

The dataset can be viewed as a nested structure:

```text
Paderborn dataset
└── K001  (healthy bearing)
    ├── Condition A
    │   ├── Recording 01
    │   │   ├── current 1   -> one 4-second signal
    │   │   ├── current 2   -> one 4-second signal
    │   │   └── vibration    -> one 4-second signal
    │   ├── Recording 02
    │   ├── Recording 03
    │   └── ... Recording 20
    ├── Condition B
    │   └── 20 recordings
    ├── Condition C
    │   └── 20 recordings
    └── Condition D
        └── 20 recordings

K002  (healthy)   -> same four conditions × 20 recordings
KA04  (damaged)   -> same four conditions × 20 recordings
...
```

One recording therefore contains several synchronized signal channels. It is the basic unit used by the first reading check and the later recording-level experiments.

The local `raw/` directory currently contains all 32 bearing directories, with 80 MATLAB recordings and 2 PDFs per bearing. The first primary protocol uses 6 healthy bearings and 14 accelerated-lifetime damaged bearings; the 12 artificial-damage bearings are also available locally for later comparison. Raw data and extracted recordings stay local and are not committed to Git.

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

資料結構可以先看成這樣：

```text
Paderborn Dataset
│
├── K001  ← healthy bearing
│   │
│   ├── Condition A
│   │   ├── Recording 01
│   │   │   ├── current 1 → 一條約 4 秒 signal
│   │   │   ├── current 2 → 一條約 4 秒 signal
│   │   │   └── vibration → 一條約 4 秒 signal
│   │   │
│   │   ├── Recording 02
│   │   ├── Recording 03
│   │   └── ... 到 20
│   │
│   ├── Condition B
│   │   └── 20 recordings
│   │
│   ├── Condition C
│   │   └── 20 recordings
│   │
│   └── Condition D
│       └── 20 recordings
│
├── K002  ← healthy
│   └── 一樣是 4 conditions × 20 recordings
│
├── KA04  ← damaged
│   └── 一樣是 4 conditions × 20 recordings
│
└── ...
```

所以一筆 recording 裡面不是只有一條 signal，而是同時有幾個同步量測的 channels。後面的實驗先把一筆 recording 當成一個樣本，不先切成很多 windows。

目前 `raw/` 已解壓全部 32 個 bearing 目錄，每個都有 80 個 `.mat` 和 2 個 PDF。第一版 primary protocol 使用 6 個 healthy bearings 和 14 個 accelerated-lifetime damaged bearings，另外 12 個 artificial-damage bearings 也保留，之後可以再做延伸比較。Raw data 與解壓後的 recordings 都保留在本地，不提交到 Git。

MATLAB 檔案內有自己的時間軸，而且不同 recording 的點數可能略有差異。讀取時應使用檔案內的時間資料，不要直接假設每筆都是固定點數。目前抽查檔案的 `Unit` 欄位是空的，因此 signal unit 和 scaling 在找到明確來源前，仍標示為未確認。

另外，`N09_M07_F10_KA04_17.mat` 是第 18 筆 recording 的替代副本，兩者訊號完全相同。後續實驗不能讓這兩筆同時增加資料權重。

## 如何理解這個資料集

Paderborn dataset 可以先簡單理解成：**軸承本身已經有已知的健康狀態，再把這些軸承放到不同 operating conditions 下運轉並記錄 signals。**

資料中的 bearings 可以先分成三類：

- **Healthy**：正常軸承。
- **Artificial damage**：人工製造損傷的軸承。
- **Accelerated-lifetime damage**：經過 accelerated lifetime test 後產生損傷的軸承。這是資料集中的一種 damage 類別，不直接等同於現場故障。

因此 bearing 的狀態不是從 signal 後來推測出來的，而是在量測之前就已經知道。模型要做的是看這些已知狀態，能不能從 current、vibration 或其他 measurements 中被區分出來。

每一顆 bearing 會放到相同的 test rig 上，在四種 operating conditions 下運轉。這些 conditions 主要改變 rotational speed、load torque 或 radial force。運轉過程中同步記錄 vibration、motor current，以及 speed、torque、force 和 temperature 等 measurements。

可以把資料結構理解成：

```text
bearing condition
    +
operating condition
    ↓
measured signals
```

例如，同一顆 damaged bearing 會在不同轉速、扭矩和徑向負載下被量測。這讓我們不只可以研究 signal 能不能區分 healthy 和 damaged bearing，也可以進一步觀察：

> 當 operating condition 改變後，原本有用的 measurement 是否仍然可靠？

這也是這個 study 使用 Paderborn dataset 的主要原因。後續會比較 current、vibration，以及 current + vibration，在 matched condition 和 condition shift 下的差異。

為了避免模型只是記住某一顆 bearing 的特徵，後續 train/test split 會以 **bearing 為單位**。同一顆 bearing 的不同 conditions 和 recordings 不會同時出現在 training 和 test data。

## 02 單一 recording 讀取與訊號檢查

先拿兩個 recording 試讀：

```text
K001  healthy   256088 samples
KA04  damaged   256001 samples
```

兩個檔案都可以讀到 `phase_current_1`、`phase_current_2` 和 `vibration_1`。每筆大約 4 秒，current 和 vibration 在同一筆 recording 裡 sample 數一致，end time 也對得上，沒有 non-finite value。

所以後面不直接假設每筆都是 `4 × 64000 = 256000` points。實際點數會有一點差異，讀取和後續 feature extraction 先以 `.mat` 裡的 time axis 為準。

目前算出的 observed sampling rate 大約在 64 kHz 附近：

```text
K001  64021.87 Hz
KA04  64000.01 Hz
```

這裡的 64 kHz 還是當作 nominal sampling rate。observed rate 主要用來確認資料讀取是否合理，不把小差異解釋成不同的 sensor setting。

`Unit` 欄位目前沒有有效內容，所以先寫成 `unknown`，不自行猜 current 或 vibration 的實際單位。

## Source, citation, and license / 來源、引用與授權

- Dataset: [KAt Bearing DataCenter](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter)
- Download index: [Bearing DataCenter files](https://groups.uni-paderborn.de/kat/BearingDataCenter/)
- License: [Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/)

Citation:

> Lessmeier, C., Kimotho, J. K., Zimmer, D., & Sextro, W. (2016). *Condition Monitoring of Bearing Damage in Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchmark Data Set for Data-Driven Classification*. European Conference of the Prognostics and Health Management Society, Bilbao, Spain.

The dataset license permits noncommercial academic use with attribution. Commercial use requires contacting the data provider.
