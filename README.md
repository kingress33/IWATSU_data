# rename_IWATSU_data


# IWATSU Core Loss Utility Scripts – 使用說明

>我只是想練習打git的README，下面都一坨廢話✨

這份 README 介紹 **IWATSU\_Count.py** 與 **IWATSU\_DataRename.py** 兩支腳本的目的、安裝需求、目錄結構以及實際操作流程。依照步驟執行即可快速完成資料統計與檔案分類／重新命名。

---

## 0 環境需求

| 需求     | 建議版本   |
| ------ | ------ |
| Python | ≥ 3.8  |
| pandas | ≥ 1.5  |
| numpy  | ≥ 1.23 |

安裝相依套件：

```bash
pip install pandas numpy
```

---

## 1 專案目錄結構

```text
project_root/
│  README.md          ← 使用說明（本檔）
│  IWATSU_Count.py    ← 統計 CSV 數量與資料點
│  IWATSU_DataRename.py ← 檔案分類 + 標準化命名
└─ <DATE>/            ← 每一次量測的原始資料夾（如 250514/）
   ├─ raw files...    ← .csv / .jpg 任意散落
   └─ …
```

腳本會在 `<DATE>/` 內自動建立：

* **waveforms/** – \_Norm..csv 單點波形
* **summary/**   – 其他 .csv 整理報表
* **images/**    – .jpg 波形截圖
* **RENAME/**    – 重新命名後的最終檔案

---

## 2 IWATSU\_Count.py

### 2‑1 功能

* 掃描主資料夾下所有子資料夾的 `.csv`。
* 顯示每檔資料點數、空檔案清單。
* 匯出總計：子資料夾數、CSV 數量、總資料點。

### 2‑2 快速開始

```bash
# 預設統計當前資料夾
python IWATSU_Count.py

# or 指定路徑
python IWATSU_Count.py path/to/your/folder
```

> **注意**：原始程式在 `__main__` 內將 `main_folder_path = "./"` 寫死，若要 CLI 方式傳參，可自行加入 `argparse`，或直接修改該變數。

### 2‑3 輸出範例

```
子資料夾 250514:
檔案 sample1.csv: 數據量 = 1024 點
…
CSV 檔案數量 = 42
總數據量 = 43008 點
數據量為 0 行的檔案： - bad.csv
…
總計 CSV 檔案數量 = 84
總計數據量為 0 行的檔案 = 1 個
總計數據量 = 86016 點
```

---

## 3 IWATSU\_DataRename.py

### 3‑1 功能

1. **分類**：依副檔名 / filename pattern 將檔案移動至 `waveforms/ | summary/ | images/`。
2. **重新命名**：只針對 `summary/` 下的 `.csv` 依下列規則產生一致檔名並複製到 `RENAME/`：

```
<vendor>_<material>_<size>_<AC/DC>_<SIN/PULSE>_<freq>k_<ΔB或Bmax>_[Dxx]_[HdcAm]_[temp]_[sample]_N=<turn ratio>.csv
```

### 3‑2 執行前設定

打開檔案頂部 **「使用者直接 Key 的參數」** 區段，依實際量測條件填入：

```python
USER_DATE   = "250514"   # 資料夾日期 (必填)
USER_VENDOR = "CSC"      # 廠商代號
USER_MAT    = "HighFlux" # 材料名稱
USER_SIZE   = "CH467160" # 核心尺寸/型號
USER_SAMPLE = "A"        # A / B / C… 無則留空
USER_TEMP   = "25"       # 攝氏溫度，無則留空
COPY_INSTEAD_OF_MOVE = True  # True=複製，False=搬移
```

> 另外可依資料欄位名稱調整 `COLUMN_MAP`；若有自訂欄位請同步更新。

### 3‑3 執行流程

```bash
python IWATSU_DataRename.py
```

執行完畢後，可在 `RENAME/` 看到已標準化的新檔名；原始資料仍保留在 `summary/` 內（若 `COPY_INSTEAD_OF_MOVE = True`）。
若命名設定有誤

### 3‑4 常見標籤說明

| 標籤        | 來源           | 範例值     | 備註                             |
| ----------- | --------------- | ------- | ------------------------------    |
| AC / DC     | CSV `mode`      | AC      | `STANDARD`→AC；`DC_BIAS`/含DC→DC  |
| SIN / PULSE | CSV `function`  | sin     | 只看開頭字串                        |
| freq k      | CSV `freq(kHz)` | 100k    | 四捨五入為整數                      |
| ΔB          | CSV `fix value` | dB40mT  | AC 模式：範圍                      |
| Bmax        | CSV `fix value` | Bm40mT  | DC 模式：定值                      |
| Dxx         | CSV `Duty(%)`   | D40.0   | 只在 PULSE 模式且 duty≠50% 時出現   |
| HdcAm       | `Hdc(A/m)`      | 0-250Am | 只在 DC 模式輸出範圍                |
| N=p.s       | `N1`, `N2`      | N=10.5  | P\:S 比；若相等→`N=10`              |

---

## 4 Troubleshooting / FAQ

* **UnicodeDecodeError**：腳本已自動切換 `utf-8 → big5 → gbk`，仍失敗時請先手動轉碼。
* **檔名衝突**：若同名檔案重複，腳本會提出覆蓋警告，但會直接覆蓋；請自行確認是否要保留舊檔。
* **空檔案**：`IWATSU_Count.py` 會列出 0 行檔案

---

## 5 小建議

* 建議先用 `IWATSU_Count.py` 查看資料完整度，再進行分類／重新命名，避免垃圾檔流入。
* 若需要更動分類規則，只需修改 `classify_and_rename()` 內的 `elif` 分支或加入新的副檔名條件即可。

---

## 6 License

0，你想怎麼改就怎麼改，因為我也只會Vibe coding 哈！我就爛！

---

 __        __  __     ______     ______   ______        ______     __         __            ______     ______      ______   __  __     __     ______    
/\ \      /\ \_\ \   /\  __ \   /\__  _\ /\  ___\      /\  __ \   /\ \       /\ \          /\  __ \   /\  ___\    /\__  _\ /\ \_\ \   /\ \   /\  ___\   
\ \ \     \ \  __ \  \ \  __ \  \/_/\ \/ \ \  __\      \ \  __ \  \ \ \____  \ \ \____     \ \ \/\ \  \ \  __\    \/_/\ \/ \ \  __ \  \ \ \  \ \___  \  
 \ \_\     \ \_\ \_\  \ \_\ \_\    \ \_\  \ \_____\     \ \_\ \_\  \ \_____\  \ \_____\     \ \_____\  \ \_\         \ \_\  \ \_\ \_\  \ \_\  \/\_____\ 
  \/_/      \/_/\/_/   \/_/\/_/     \/_/   \/_____/      \/_/\/_/   \/_____/   \/_____/      \/_____/   \/_/          \/_/   \/_/\/_/   \/_/   \/_____/ 
                                                                                                                                                        

⚡好想畢業，好想找到工作，好想攀岩🤖
