# %% [markdown]
# <!-- # %% [markdown]
# # ### 檔案命名
# # 功能：
# # 1. 依檔名或欄位把檔案分進 waveforms/ summary/ images/
# # 2. 只對 summary/ 下的 CSV 進行標準化重新命名
# # 命名規則：
# # <vendor>_<material>_<size>_<AC/DC>_<SIN/PULSE>_<freq>k_<ΔB/Bmax>_[Dxx]_[HdcAm]_[temp]_[sample]_N=<turn ratio>.csv -->
#

# %%
import os
import pandas as pd


def count_csv_data(main_folder):
    # 用於儲存總計數據
    total_csv_count = 0
    total_csv_zero = 0
    total_data_rows_all = 0
    summary = []

    # 遍歷主資料夾下的所有子資料夾
    for subfolder in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder)

        # 檢查是否為資料夾
        if os.path.isdir(subfolder_path):
            csv_count = 0
            total_data_rows = 0
            zero_rows_files = []  # 儲存數據量為 0 行的檔案

            print(f"\n子資料夾 {subfolder}:")

            # 遍歷子資料夾內的所有檔案
            for file in os.listdir(subfolder_path):
                if file.endswith('.csv'):
                    csv_count += 1
                    file_path = os.path.join(subfolder_path, file)

                    try:
                        # 嘗試使用 UTF-8 編碼讀取
                        df = pd.read_csv(file_path,
                                         skiprows=4,
                                         encoding='utf-8')
                    except UnicodeDecodeError:
                        # 如果 UTF-8 失敗，嘗試使用 'big5' 編碼（常用於繁體中文）
                        try:
                            df = pd.read_csv(file_path,
                                             skiprows=4,
                                             encoding='big5')
                        except UnicodeDecodeError:
                            # 如果 big5 也失敗，嘗試 'gbk' 編碼（常用於簡體中文）
                            try:
                                df = pd.read_csv(file_path,
                                                 skiprows=4,
                                                 encoding='gbk')
                            except Exception as e:
                                print(f"無法讀取檔案 {file}: {e}")
                                continue

                    # 計算數據量（行數）
                    data_rows = len(df)
                    total_data_rows += data_rows

                    # 檢查數據量是否為 0 點
                    if data_rows == 0:
                        zero_rows_files.append(file)
                        total_csv_zero += 1
                    else:
                        print(f"檔案 {file}: 數據量 = {data_rows} 點")

            # 該子資料夾的統計結果
            print(f"CSV 檔案數量 = {csv_count}")
            print(f"總數據量 = {total_data_rows} 點")

            # 列出數據量為 0 行的檔案
            if zero_rows_files:
                print("數據量為 0 行的檔案：")
                for zero_file in zero_rows_files:
                    print(f"- {zero_file}")
            else:
                print("無數據量為 0 行的檔案")

            print()  # 換行

            # 更新總計
            total_csv_count += csv_count
            total_data_rows_all += total_data_rows
            summary.append((subfolder, csv_count, total_data_rows))

    # 輸出總結報告
    print("=" * 50)
    print("總結報告")
    print("=" * 50)
    print(f"{'子資料夾':<20} {'CSV 數量':<10} {'數據量 (點)':<10}")
    print("-" * 50)
    for subfolder, csv_count, data_rows in summary:
        print(f"{subfolder:<20} {csv_count:<10} {data_rows:<10}")
    print("-" * 50)
    print(f"總計 CSV 檔案數量 = {total_csv_count}")
    print(f"總計數據量為 0 行的檔案 = {total_csv_zero} 個")
    print(f"總計數據量 = {total_data_rows_all} 點")


# %%
if __name__ == "__main__":
    main_folder_path = "./"
    count_csv_data(main_folder_path)
