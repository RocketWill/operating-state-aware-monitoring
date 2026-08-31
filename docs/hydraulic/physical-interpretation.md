# Physical interpretation of hydraulic measurements

The family and incremental comparisons show how well each measurement group
supports the `pump_leakage` task. This analysis connects those results to the
measured signals themselves. It reports cycle-level summaries, raw-signal
envelopes, and ten-second phase summaries for motor power, pressure, flow, and
temperature.

The result is descriptive. It does not treat the three leakage labels as a
time-ordered degradation trajectory, and it does not make causal or
energy-saving claims.

## Reproducible command

Run the analysis from the repository root with the `windfusion` Conda
environment:

```text
conda run --no-capture-output -n windfusion python src/run_physical_interpretation.py
```

The verified run used:

| Setting | Value |
|---|---|
| Environment | `windfusion`; Python 3.11.16; NumPy 2.4.6; pandas 3.0.5; Matplotlib 3.11.2; scikit-learn 1.9.1 |
| Input | `data/hydraulic/raw/`; profile shape `2,205 × 5` |
| Eligibility | `stable_flag == 0`; 1,449 cycles |
| Target | `pump_leakage`, labels `0/1/2`, counts `489/480/480` |
| Groups | 144 contiguous condition blocks; 143 blocks of 10 cycles and one block of 19 cycles |
| Channels | 13 measured channels: `EPS1`, `PS1–PS6`, `FS1–FS2`, and `TS1–TS4` |
| Primary summary | Per-cycle mean for each channel |
| Additional summaries | Pointwise median and IQR of each raw signal; six ten-second phase means |

The channel definitions and source meanings are recorded in the
[hydraulic measurement audit](measurement-audit.md). The other component
conditions (`cooler_condition`, `valve_condition`, and
`accumulator_pressure`) are pooled in the signal plots and reported separately
below.

## Data observations

The table reports the median of the per-cycle channel mean. Values are grouped
by the observed `pump_leakage` label; they are not estimates of a time series.

| Family | Channel | Quantity | Unit | Label 0 | Label 1 | Label 2 |
|---|---|---|---|---:|---:|---:|
| Motor power | `EPS1` | Motor power | W | 2465.218 | 2547.456 | 2557.540 |
| Pressure | `PS1` | Pressure | bar | 159.036 | 160.588 | 160.306 |
| Pressure | `PS2` | Pressure | bar | 107.720 | 108.776 | 108.672 |
| Pressure | `PS3` | Pressure | bar | 1.799 | 1.757 | 1.731 |
| Pressure | `PS4` | Pressure | bar | 0.000 | 0.000 | 0.000 |
| Pressure | `PS5` | Pressure | bar | 9.140 | 9.151 | 9.147 |
| Pressure | `PS6` | Pressure | bar | 9.056 | 9.066 | 9.063 |
| Flow | `FS1` | Volume flow | l/min | 6.660 | 6.458 | 6.361 |
| Flow | `FS2` | Volume flow | l/min | 9.710 | 9.705 | 9.708 |
| Temperature | `TS1` | Temperature | °C | 44.580 | 44.346 | 44.534 |
| Temperature | `TS2` | Temperature | °C | 49.634 | 49.359 | 49.576 |
| Temperature | `TS3` | Temperature | °C | 46.827 | 46.592 | 46.821 |
| Temperature | `TS4` | Temperature | °C | 40.055 | 39.921 | 40.081 |

Several patterns are visible in these summaries:

- `EPS1` has a higher median in labels `1` and `2` than in label `0`.
- `FS1` shows a small downward shift across the observed label values, but its raw-trace shape is shared across labels and it is not a standout signal. `FS2` is nearly unchanged.
- Pressure changes are mixed: `PS1` and `PS2` are higher in labels `1` and `2`, `PS3` shows a small but directionally consistent downward shift across the later phases, and the `PS4` median is zero in all three groups despite a wider cycle-level distribution.
- The temperature medians largely overlap. No temperature channel shows a monotonic separation across all three labels in this summary.

The raw-signal plots retain the recorded time axis and channel-specific unit.
Their bands show the interquartile range across eligible cycles for each label.
The phase table uses the source sampling rate for each channel, so the phase
boundaries refer to the same six 10-second intervals even though the number of
samples per interval differs by channel.

## Other component conditions

The signal plots pool the other conditions to keep the primary comparison
readable. The separate condition summary records the support available for
that pooling:

| Condition | Values | Cycle counts | Group counts | Target counts `0/1/2` |
|---|---|---|---|---|
| `cooler_condition` | `3 / 20 / 100` | `480 / 480 / 489` | `48 / 48 / 48` | `160/160/160`; `160/160/160`; `169/160/160` |
| `valve_condition` | `73 / 80 / 90 / 100` | `360 / 360 / 360 / 369` | `36 / 36 / 36 / 36` | `120/120/120`; `120/120/120`; `120/120/120`; `129/120/120` |
| `accumulator_pressure` | `90 / 100 / 115 / 130` | `369 / 360 / 360 / 360` | `36 / 36 / 36 / 36` | `129/120/120`; `120/120/120`; `120/120/120`; `120/120/120` |

Within each row, the cycle counts, group counts, and target-count entries
follow the listed value order. Each target-count entry is ordered as
`pump_leakage 0/1/2`.

These counts show that all reported condition strata contain all three pump
leakage labels. They do not by themselves remove the effects of operating
condition, nor do they establish independent experimental runs.

## Physical interpretation

The higher `EPS1` cycle mean for labels `1` and `2` is consistent with a
hypothesis that internal leakage changes the motor's operating demand. The
observation is not sufficient to identify the mechanism: the analysis does not
verify the motor, pump, load, or pressure topology, and the other component
conditions are pooled in the main plots.

The small downward shift in `FS1` is compatible with lower effective output
flow, but its trace shape is similar across labels and its sensor location is
not verified. The different behaviour of `FS1` and `FS2` therefore suggests
that flow measurements should be interpreted by sensor location rather than
as one interchangeable flow quantity.

`PS3` shows a small downward shift in the full-cycle median and in several
later ten-second phases. This makes it a more specific pressure observation
than a single full-cycle average, but it still cannot be reduced to a verified
pressure drop. The mixed changes across `PS1`, `PS2`, `PS3`, `PS5`, and `PS6`
require a sensor-location mapping before they can be assigned to a hydraulic
mechanism.

The temperature summaries do not show a clear label-separated pattern in this
run. This is a statement about the recorded 1 Hz signals and the cycle-level
summary, not evidence that temperature is physically irrelevant to leakage.

## Hypotheses to verify

The current observations support the following bounded hypotheses:

1. Internal leakage may be associated with higher motor power and lower `FS1`
   under some operating conditions.
2. A lower `PS3` signal may be associated with internal leakage, depending on
   where `PS3` sits in the hydraulic circuit.
3. The pressure and flow response may depend on where each sensor sits in the
   hydraulic circuit.
4. A temperature effect, if present, may require condition-stratified or
   time-window analysis rather than one mean over the full cycle.

These hypotheses require a verified hydraulic schematic and sensor mapping
before a pressure-drop or hydraulic-power quantity can be calculated.

## 我的理解與目前猜測

`pump leakage` 就是原本應該被送出去做事的油，有一部分在泵裡面漏回去了。
所以泵雖然還在轉，但真正送到系統裡的有效流量可能變少。這會連帶影響幾種量測。

### FS1：有效輸出流量可能變少

FS1 下降是目前最容易用直覺理解的現象：

```text
原本泵出去 10 份油，幾乎 10 份都進系統。
有 leakage 後，可能有 1–2 份在泵內部回流，所以外面某條管路量到的 flow 變少。
```

資料中的 FS1 cycle-mean median 是：

```text
6.660 → 6.458 → 6.361 l/min
```

這和「有效輸出流量下降」的直覺相符。不過目前的變化幅度不大，raw trace 的形狀也大致相同，所以 FS1 比較適合當成弱的 supporting observation，不是單獨很有辨識力的訊號。

### FS2：不同位置可能有不同反應

FS2 幾乎不變：

```text
9.710 → 9.705 → 9.708 l/min
```

這不一定和 FS1 矛盾，因為 FS1 和 FS2 很可能不在同一個位置。一個可能在 pump output，另一個可能在被控制、旁通或回流的支路。沒有 hydraulic schematic，我們不能直接說哪一個是哪裡，所以目前只能說：

> leakage 對不同位置的 flow sensor 影響不一樣。

### EPS1：motor operating demand 可能上升

如果系統還是要求 pump 維持某個壓力或工作狀態，但泵內部一直漏，motor / pump 可能需要付出更多 input power：

```text
馬達做的功
   ↓
泵產生流量
   ↓
一部分有效輸出
一部分內部漏掉
```

資料中的 EPS1 是：

```text
2465 → 2547 → 2558 W
```

所以可以形成一個合理假設：

> leakage 較大的狀態，可能伴隨較高的 motor operating demand。

但這裡一定要保留「可能」，因為我們還不知道控制系統到底怎麼調 pump，也不知道 load 是否完全一致。這是 data pattern 與 hydraulic intuition 相符的解釋，不是已經證明的因果關係。

### PS3：另一個值得追蹤的反向訊號

PS3 的 cycle-mean median 是：

```text
1.799 → 1.757 → 1.731 bar
```

PS3 和 PS1 / PS2 的方向不一樣，而且在後面幾個 10-second phases 也大致維持下降。可以用很粗略的方式理解：如果 leakage 讓有效流量變少，那某些位置的 pressure 可能也會稍微掉下來。

```text
水泵裡面有一部分水漏回去
        ↓
下游某個位置得到的流量 / pressure 可能比較低
```

但這不能套到所有 pressure sensor。現在看到的是：

```text
PS1 / PS2：稍微上升或接近不變
PS3：下降
PS5 / PS6：幾乎不變
```

這不一定矛盾，因為 valve、regulator、accumulator 或其他支路會讓不同位置的 pressure 有不同反應。例如非常粗略地想：

```text
Pump → PS1 → valve → PS3 → actuator
```

所以 PS3 下降目前可以保留成一個值得追蹤的 pressure observation，但還不能直接叫做 pressure drop，也不能直接說這就是 leakage mechanism。

### 目前的整體理解

現在可以把三個主要現象先記成：

```text
Pump leakage
     ↓
一部分油在 pump 內部流失
     ↓
有效輸出可能下降
     ↓
FS1 ↓        某些位置 flow 下降

系統仍要維持工作
     ↓
motor / pump operating demand 改變
     ↓
EPS1 ↑       motor power 可能較高

不同管路位置受到不同影響
     ↓
PS3 ↓
PS1 / PS2 ↑ or similar
```

最重要的是，這不是已經證明的機制，而是目前 data pattern 與 hydraulic intuition 相符的解釋。我們現在做的是：

> 模型告訴我 sensor 有用 → 回頭看 sensor 本身怎麼變 → 檢查這個變化能不能用合理的物理機制解釋。

因此，`EPS1 ↑ + FS1 ↓ + PS3 ↓` 可以先作為一個合理的 internal leakage signature hypothesis，但還需要 hydraulic schematic、sensor mapping 和 condition-stratified analysis 才能繼續驗證。

## Scope and limits

- The analysis uses the 1,449 rows with `stable_flag == 0`; unstable rows are not mixed into the reported summaries.
- Labels `0/1/2` are compared as observed condition values. They are not interpreted as a measured temporal progression.
- No `Δp × Q` power proxy is calculated. The retained source information does not verify the upstream/downstream pressure pair and its corresponding flow channel, so a unit-correct proxy cannot be assigned safely.
- The repeated cycles within a condition block are reported with their group support. Different cycle indices are not assumed to be independent experimental runs.
- The results are descriptive and do not establish causation, energy savings, production readiness, remaining useful life, or a universally optimal sensor set.

The local run artifacts contain the complete channel metadata, cycle-level
values, raw-trace summaries, phase summaries, condition support, plots, and
environment information:

- `outputs/physical_interpretation/run_metadata.json`
- `outputs/physical_interpretation/cycle_feature_values.csv`
- `outputs/physical_interpretation/channel_summary.csv`
- `outputs/physical_interpretation/raw_trace_summary.csv`
- `outputs/physical_interpretation/phase_summary.csv`
- `outputs/physical_interpretation/condition_summary.csv`
- `outputs/physical_interpretation/cycle_mean_distributions.png`
- `outputs/physical_interpretation/raw_trace_summaries.png`

Raw data and generated outputs remain local. The public source for this
analysis is [`src/run_physical_interpretation.py`](../../src/run_physical_interpretation.py).
