# 02 Single Recording Read and Signal Check

This step checks the actual structure of the Paderborn raw MATLAB data, and whether current and vibration can be read and aligned.

Two recordings are checked:

- `K001`: healthy bearing
- `KA04`: damaged bearing

Both files contain:

```text
phase_current_1
phase_current_2
vibration_1
```

There are no non-finite values in the checked channels.

```text
K001  -> about 4 seconds, 256088 samples
KA04  -> about 4 seconds, 256001 samples
```

Within each recording, current and vibration have the same sample count, and their end times match.

## Notes

Each Paderborn recording is roughly 4 seconds long. Current and vibration are measured together, but the sample count is not always exactly the same.

The later processing should not assume:

```text
4 × 64000 = 256000 points
```

It is more reasonable to use the actual time axis stored in each `.mat` file for signal processing and feature extraction. Recordings should not be forced to have the same length at this stage.

The observed sampling rates calculated from the time axes are:

```text
K001  -> 64021.87 Hz
KA04  -> 64000.01 Hz
```

Both are close to the dataset nominal rate of 64 kHz. The observed rate is used as a readout check, not interpreted as a different sensor sampling setting.

The `Unit` field in the MATLAB files does not contain usable information. The current and vibration units therefore remain `unknown` instead of being guessed.

This check confirms that the reader can handle both healthy and damaged bearings, and that current and vibration can be read from the same recording. The next step is to define the bearing split, target, and matched / shifted experiments.

## Run

```text
conda run --no-capture-output -n windfusion python src/read_paderborn_recording.py
```

The plots and summary are written to `outputs/paderborn_reading/` and kept local.

---

# 02 單一 Recording 讀取與訊號檢查

這一步主要確認 Paderborn raw MATLAB data 的實際結構，以及 current 和 vibration 能不能正常讀取、對齊。

目前先測兩個 recording：

- `K001`：healthy bearing
- `KA04`：damaged bearing

兩個檔案都可以讀到：

```text
phase_current_1
phase_current_2
vibration_1
```

而且沒有 non-finite value。

```text
K001  -> 約 4 秒，256088 samples
KA04  -> 約 4 秒，256001 samples
```

同一筆 recording 裡，current 和 vibration 的 sample 數一致，end time 也對得上。

## 我的理解

Paderborn 每筆 recording 大概都是 4 秒，current 和 vibration 也是同步量測，但 sample 數不一定完全一樣。

所以後續不直接假設每筆都是：

```text
4 × 64000 = 256000 points
```

比較合理的是使用每個 `.mat` 裡實際的 time axis，再做後續 signal processing 和 feature extraction。不要先把所有 recording 強制切成相同長度。

目前從 time axis 算出的 observed sampling rate：

```text
K001  -> 64021.87 Hz
KA04  -> 64000.01 Hz
```

兩個都接近 dataset 的 nominal sampling rate 64 kHz。這裡 observed rate 主要拿來檢查資料有沒有讀歪，不把小差異解釋成不同的 sensor sampling setting。

另外，MATLAB 裡的 `Unit` 欄位目前沒有有效資訊，所以先保留成 `unknown`，不自行猜 current 或 vibration 的實際 unit。

目前這一步可以確認 reader 能同時處理 healthy 和 damaged bearing，也能從同一筆 recording 取得 current 和 vibration。下一步再處理 bearing split、target，以及 matched / shifted experiment 的定義。

## 執行

```text
conda run --no-capture-output -n windfusion python src/read_paderborn_recording.py
```

圖和摘要會放在 `outputs/paderborn_reading/`，只保留在本地。
