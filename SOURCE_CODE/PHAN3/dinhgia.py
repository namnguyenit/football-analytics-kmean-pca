import pandas as pd
import numpy as np

# --- Bước 1: Định nghĩa file và các KPIs ---
file_players = 'player_stats.csv'
file_team_stats = 'team_stats_summary.csv'
output_file = 'player_valuations.csv'

# Định nghĩa các chỉ số chính (KPIs) và trọng số (weights)
# Bạn có thể thay đổi các chỉ số và trọng số này
KPI_WEIGHTS = {
    'Performance_Gls': 0.30,
    'Performance_Ast': 0.25,
    'Expected_xG': 0.20,
    'Progression_PrgP': 0.15,
    'Playing Time_Min': 0.10  # Dùng số phút để lọc bớt cầu thủ dự bị
}

# Lấy danh sách các cột KPI
kpi_columns = list(KPI_WEIGHTS.keys())

# Các cột cần chuyển sang số từ file player_stats.csv
numeric_columns_to_convert = [
    'Age', 'Born',
    'Playing Time_MP', 'Playing Time_Starts', 'Playing Time_Min', 'Playing Time_90s',
    'Performance_Gls', 'Performance_Ast', 'Performance_G+A', 'Performance_G-PK',
    'Performance_PK', 'Performance_PKatt', 'Performance_CrdY', 'Performance_CrdR',
    'Expected_xG', 'Expected_npxG', 'Expected_xAG', 'Expected_npxG+xAG',
    'Progression_PrgC', 'Progression_PrgP', 'Progression_PrgR'
]

try:
    # --- Bước 2: Tải và làm sạch Dữ liệu Cầu thủ ---
    df_players = pd.read_csv(file_players)
    
    # Lọc các cột số hợp lệ
    valid_numeric_cols = [col for col in numeric_columns_to_convert if col in df_players.columns]
    
    # Chuyển đổi các cột sang số
    for col in valid_numeric_cols:
        df_players[col] = pd.to_numeric(df_players[col], errors='coerce')
    
    # Chỉ giữ lại các cột cần thiết
    df_players_clean = df_players[['Player', 'Squad', 'Pos'] + kpi_columns].copy()
    
    # Loại bỏ cầu thủ có dữ liệu NaN trong các cột KPI (ví dụ: cầu thủ mới)
    df_players_clean.dropna(subset=kpi_columns, inplace=True)

    print(f"Tải và làm sạch {len(df_players_clean)} cầu thủ.")

    # --- Bước 3: Tải và làm sạch Dữ liệu Đội (ĐÃ SỬA LỖI) ---
    
    # SỬA ĐỔI: Thêm `index_col=0` để tự động đọc 'Squad' (cột đầu tiên) làm chỉ mục
    df_team_stats = pd.read_csv(file_team_stats, header=[0, 1], index_col=0)

    # Làm phẳng MultiIndex (ví dụ: ('Performance_Gls', 'mean') -> 'Performance_Gls_mean')
    df_team_stats.columns = ['_'.join(col).strip() for col in df_team_stats.columns.values]
    
    # SỬA ĐỔI: Chuyển 'Squad' (đang là index) thành một cột để merge
    df_team_stats.reset_index(inplace=True)
    
    # SỬA ĐỔI: Xóa 2 dòng code tìm kiếm tên cột 'Squad' không còn cần thiết
    # squad_col_name = [col for col in df_team_stats.columns if 'Squad' in col][0] # <- Đã xóa
    # df_team_stats.rename(columns={squad_col_name: 'Squad'}, inplace=True) # <- Đã xóa

    # Giữ lại các cột mean và std cho các KPI của chúng ta
    # 'Squad' giờ là một tên cột đã biết sau khi reset_index()
    stats_to_keep = ['Squad']
    for kpi in kpi_columns:
        stats_to_keep.append(f"{kpi}_mean")
        stats_to_keep.append(f"{kpi}_std")
        
    df_team_stats_clean = df_team_stats[stats_to_keep].copy()
    print("Tải và làm sạch dữ liệu thống kê đội.")

    # --- Bước 4: Hợp nhất (Merge) hai DataFrame ---
    # Việc merge này sẽ hoạt động vì cả hai DataFrame đều có cột tên 'Squad'
    df_merged = pd.merge(df_players_clean, df_team_stats_clean, on='Squad', how='left')
    
    # Thêm kiểm tra lỗi merge
    if df_merged.isnull().any().any():
        print("\nCẢNH BÁO: Có giá trị NaN sau khi merge.")
        print("Điều này có thể xảy ra nếu tên đội trong player_stats.csv không khớp chính xác với team_stats_summary.csv.")
    
    print("Đã hợp nhất dữ liệu cầu thủ và đội.")

    # --- Bước 5 & 6: Tính Z-Scores và Điểm Tổng hợp ---
    df_merged['ValuationScore'] = 0.0
    
    for kpi, weight in KPI_WEIGHTS.items():
        # Tên cột tương ứng
        kpi_col = kpi
        mean_col = f"{kpi}_mean"
        std_col = f"{kpi}_std"
        zscore_col = f"ZScore_{kpi}"
        
        # Lấy giá trị mean và std
        player_stat = df_merged[kpi_col]
        team_mean = df_merged[mean_col]
        team_std = df_merged[std_col]
        
        # Tính Z-Score
        # np.where để tránh lỗi chia cho 0 (nếu std == 0, Z-Score = 0)
        df_merged[zscore_col] = np.where(team_std > 0, 
                                         (player_stat - team_mean) / team_std, 
                                         0.0)
        
        # Cộng vào điểm tổng hợp (với trọng số)
        df_merged['ValuationScore'] += df_merged[zscore_col] * weight

    print("Đã tính toán Z-Scores và Điểm Giá trị Tổng hợp.")

    # --- Bước 7: Sắp xếp và Lưu kết quả ---
    df_final_valuation = df_merged.sort_values(by='ValuationScore', ascending=False)
    
    # Lưu vào file CSV
    df_final_valuation.to_csv(output_file, index=False)
    
    print(f"\nĐã lưu kết quả định giá vào {output_file}")
    print("\n--- TOP 10 CẦU THỦ ĐƯỢC ĐỊNH GIÁ CAO NHẤT (THEO MÔ HÌNH NÀY) ---")
    print(df_final_valuation[['Player', 'Squad', 'Pos', 'ValuationScore']].head(10))

except FileNotFoundError as e:
    print(f"Lỗi: Không tìm thấy file. {e}")
except KeyError as e:
    print(f"Lỗi: Không tìm thấy cột. Hãy kiểm tra lại tên cột trong file CSV. {e}")
except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")