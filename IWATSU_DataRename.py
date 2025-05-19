# %% [markdown]
# <!-- # %% [markdown]
# # ### 檔案命名
# # 功能：
# # 1. 依檔名或欄位把檔案分進 waveforms/ summary/ images/
# # 2. 只對 summary/ 下的 CSV 進行標準化重新命名
# # 命名規則：
# # <vendor>_<material>_<size>_<AC/DC>_<SIN/PULSE>_<freq>k_<ΔB/Bmax>_[Dxx]_[HdcAm]_[temp]_[sample]_N=<turn ratio>.csv -->
# 

# %% [markdown]
# 
# ### 檔案命名
# 功能：
# 1. 依檔名或欄位把檔案分進 waveforms/ summary/ images/
# 2. 只對 summary/ 下的 CSV 進行標準化重新命名
# ### 命名規則：
# <vendor>_<material>_<size>_<AC/DC>_<SIN/PULSE>_<freq>k_<ΔB 或 Bmax>_
# [Dxx]_[temp]_[sample]_N=<turn ratio>.csv
# 

# %%
# 清空所有變數
%reset -f  
# 強制 Python 回收記憶體
import gc
gc.collect()  

# %%
import os
import re
import shutil
import sys
import pandas as pd
from typing import Dict, Optional

# %%
"""
DATE: 
250207
250219
250306
250312
250314
250318
250326
250328-s2
250328-s1
250416
250423
250502-s1
250502-s2
250514
"""

# %% [markdown]
# ### 使用者直接 Key 的參數

# %%
# ─── 使用者直接 Key 的參數（改這裡就好）─────────────────────────────
USER_DATE = "250207"  # 資料夾日期
USER_VENDOR = "CSC"  # 廠商
USER_MAT = "HighFlux"  # 材料
USER_SIZE = "CH467160G"  # 尺寸
USER_SAMPLE = "A"  # A / B / C… 沒有就留空
USER_TEMP = "25"  # 溫度（°C）
COPY_INSTEAD_OF_MOVE = True  # True=複製，False=移動
# ────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(
    __file__) if "__file__" in globals() else os.getcwd()
RENAME_D = os.path.join(SCRIPT_DIR, "RENAME")
os.makedirs(RENAME_D, exist_ok=True)

# 設定分類資料夾
root = os.path.join(".", USER_DATE)
wave_d = os.path.normpath(f"{USER_DATE}/waveforms")
summ_d = os.path.normpath(f"{USER_DATE}/summary")
img_d = os.path.normpath(f"{USER_DATE}/images")
for d in (wave_d, summ_d, img_d):
    os.makedirs(d, exist_ok=True)

# ---------- 可調整：CSV 欄位對應表 ----------
COLUMN_MAP: Dict[str, list[str]] = {
    "mode": ["mode"],
    "function": ["function", "waveform"],
    "freq": ["freq(kHz)", "frequency(kHz)"],
    "deltaB": ["fix value"],
    "duty": ["Duty(%)"],
    "hdc": ["Hdc(A/m)"],
    "n1": ["N1"],
    "n2": ["N2"],
}

# 用於記錄生成的新檔名及其對應的原始檔案
generated_filenames = {}


# ---------- 小工具：安全提取欄位值 ----------
def safe_get(df: pd.DataFrame, key: str, default: str = "") -> str:
    col = find_col(df, key)
    if col is not None and not df[col].empty:
        return str(df[col].iloc[0])
    return default


# ---------- 小工具：找欄位名稱 ----------
def find_col(df: pd.DataFrame, key: str) -> Optional[str]:
    for col in df.columns:
        if col.strip().lower() in [c.lower() for c in COLUMN_MAP[key]]:
            return col
    return None


# ---------- Duty 標籤 ----------
def duty_tag(duty_val: str, func: str) -> str:
    # 僅在 pulse 模式下檢查 Duty
    if func != "pulse":
        return ""
    try:
        d = float(duty_val) / 100  # Duty(%) 轉為小數
        return "" if abs(d - 0.5) < 1e-2 else f"D{d:.1f}"  # 保留一位小數
    except Exception:
        return ""


# ---------- Hdc 標籤 ----------
def hdc_tag(df: pd.DataFrame, acdc: str) -> str:
    # 僅在 DC 模式下顯示 Hdc
    if acdc != "DC":
        return ""
    try:
        # 提取 Hdc(A/m) 欄位
        col = find_col(df, "hdc")
        if col is None:
            return ""
        # 將欄位值轉為數值，無效值轉為 NaN
        hdc_vals = pd.to_numeric(df[col], errors='coerce').abs()
        # 移除 NaN 值
        hdc_vals = hdc_vals.dropna()
        # 檢查是否有有效數據
        if hdc_vals.empty:
            return ""
        # 生成範圍標籤
        hdc_tag = f"{int(hdc_vals.min())}-{int(hdc_vals.max())}Am"
        return hdc_tag
    except Exception:
        return ""


# ---------- 從 N1 和 N2 欄位提取圈數比例，轉成 N=x.y ----------
def get_turns_ratio(df: pd.DataFrame) -> str:
    try:
        # 提取 N1 和 N2
        n1 = safe_get(df, "n1", "1")  # 預設為 1
        n2 = safe_get(df, "n2", "1")  # 預設為 1
        # 轉為整數
        p = int(float(n1))  # primary turns
        s = int(float(n2))  # secondary turns
        # 生成 N=x.y 格式
        if p == s:
            return f"N={p}"
        return f"N={p}.{s}"
    except Exception:
        return "N=1"  # 如果提取或轉換失敗，預設為 N=1


# =================重新命名流程=================


def rename_summary(csv_path: str) -> None:
    print(f"正在處理檔案：{csv_path}")
    # 檢查檔案是否為空
    if os.path.getsize(csv_path) == 0:
        print(f"警告：{csv_path} 檔案為空，跳過處理")
        return False  # 返回 False 表示處理失敗

    # 嘗試讀取檔案
    try:
        df = pd.read_csv(csv_path, skiprows=3, encoding='big5')
    except UnicodeDecodeError as e:
        print(f"編碼錯誤：{csv_path} 無法使用 Big5 編碼讀取，錯誤訊息：{e}")
        print("建議：嘗試其他編碼（如 'gbk' 或 'latin1'），或將檔案轉換為 UTF-8")
        return False
    except pd.errors.EmptyDataError:
        print(f"錯誤：{csv_path} 檔案內容為空或無數據，無法處理")
        return False
    except Exception as e:
        print(f"讀取檔案失敗：{csv_path}，錯誤訊息：{e}")
        return False

    base, ext = os.path.splitext(os.path.basename(csv_path))

    # 提取 mode 並判斷 AC/DC
    mode_raw = safe_get(df, "mode").strip().upper()
    if not mode_raw:
        print("警告：mode 值為空，預設為 AC")
        acdc = "AC"
    else:
        # 更明確的判斷邏輯
        if mode_raw == "DC_BIAS" or "DC" in mode_raw:
            acdc = "DC"
        elif mode_raw == "STANDARD":
            acdc = "AC"
        else:
            print(f"警告：無法識別 mode 值 '{mode_raw}'，預設為 AC")
            acdc = "AC"
    print(f"提取 mode：{mode_raw}，判斷為 {acdc}")

    # 提取波形類型
    func_raw = safe_get(df, "function").upper()
    func = "sin" if func_raw.startswith("SIN") else "pulse"
    print(f"提取 function：{func_raw}，判斷為 {func}")

    # 提取頻率
    freq = int(round(float(safe_get(df, "freq", "0"))))
    print(f"提取 freq：{freq}kHz")

    # ΔB / Bmax 處理
    try:
        b_vals = df[find_col(df, "deltaB")].abs()  # 單位從 T 轉為 mT
        b_tag = f"Bm{int(b_vals.min())}-{int(b_vals.max())}mT" if acdc == "AC" else f"dB{int(b_vals.mean())}mT"
        print(f"提取 deltaB：{b_vals.min()} - {b_vals.max()}，生成標籤：{b_tag}")
    except Exception as e:
        print(f"處理 deltaB 失敗：{csv_path}，錯誤訊息：{e}")
        return False

    # Duty 標籤
    duty = duty_tag(safe_get(df, "duty"), func)
    print(f"提取 duty：{duty}")

    # Hdc 標籤（範圍形式）
    hdc = hdc_tag(df, acdc)
    print(f"提取 Hdc：{hdc}")

    # 圈數（從 N1 和 N2 提取）
    turns = get_turns_ratio(df)
    print(f"提取 turns：{turns}")

    # 溫度標籤
    temp_tag = f"{USER_TEMP}C" if USER_TEMP else ""
    print(f"溫度標籤：{temp_tag}")

    # 組合檔名
    parts = [
        USER_VENDOR, USER_MAT, USER_SIZE, acdc, func, f"{freq}k", b_tag, duty,
        hdc, temp_tag,
        USER_SAMPLE.upper(), turns
    ]
    new_name = "_".join([p for p in parts if p]) + ext
    new_path = os.path.join(RENAME_D, new_name)

    # 檢查新檔名是否已經存在
    if new_name in generated_filenames:
        print(f"⚠️警告：新檔名 {new_name} 已存在，將會覆蓋以下檔案：")
        print(f"  - 原始檔案：{generated_filenames[new_name]}")
        print(f"  - 當前檔案：{csv_path}")
    else:
        generated_filenames[new_name] = csv_path

    if COPY_INSTEAD_OF_MOVE:
        shutil.copy2(csv_path, new_path)
        action = "Copy"
    else:
        shutil.move(csv_path, new_path)
        action = "Move"
    print(f"✔ {action:4} {base+ext} → RENAME/{new_name}")
    return True  # 返回 True 表示處理成功


# =================分類+重命名流程=================


def classify_and_rename():
    # 清空已生成的檔名記錄
    generated_filenames.clear()

    # 分類檔案（僅針對不在 waveforms/、summary/、images/ 資料夾中的檔案）
    files_classified = 0
    for r, _, fs in os.walk(root):
        for f in fs:
            p = os.path.normpath(os.path.join(r, f))
            # 檢查檔案是否已經在目標資料夾中
            if p.startswith((wave_d, summ_d, img_d)):
                print(f"跳過檔案：{p}，因為已經在目標資料夾中")
                continue
            if f.endswith("_Norm..csv"):
                dest = os.path.join(wave_d, f)
            elif f.lower().endswith(".csv"):
                dest = os.path.join(summ_d, f)
            elif f.lower().endswith(".jpg"):
                dest = os.path.join(img_d, f)
            else:
                print(f"跳過檔案：{p}，因為不符合分類條件")
                continue
            shutil.move(p, dest)
            print(f"✔ Classified: {f} → {dest}")
            files_classified += 1
    if files_classified == 0:
        print("分類階段：未找到需要分類的檔案，所有檔案可能已經分類好")

    # 重新命名 summary/ 下的 CSV
    if not os.path.exists(summ_d):
        print(f"錯誤：{summ_d} 資料夾不存在，無法進行重新命名！")
        sys.exit(1)

    csv_files = [f for f in os.listdir(summ_d) if f.lower().endswith(".csv")]
    if not csv_files:
        print(f"警告：{summ_d} 資料夾中未找到任何 CSV 檔案，無法進行重新命名！")
    else:
        print(f"找到 {len(csv_files)} 個 CSV 檔案：{csv_files}")

    # 記錄成功處理的檔案數
    successful_files = 0
    for f in csv_files:
        if rename_summary(os.path.join(summ_d, f)):
            successful_files += 1

    # 檢查是否有檔案未成功處理
    if successful_files != len(csv_files):
        print(f"⚠️警告：找到 {len(csv_files)} 個檔案，但只有 {successful_files} 個檔案成功處理！")

    print("🎉 All done! 檔案已分類並複製到 ./RENAME")


# %% [markdown]
# ###　執行結果

# %%
# ---------- 程式進入點 ----------
if __name__ == "__main__":
    classify_and_rename()


