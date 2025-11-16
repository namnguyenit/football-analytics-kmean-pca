import pandas as pd
import numpy as np

# Định nghĩa tên file input và output
input_file = 'player_stats.csv'
output_file = 'team_stats_summary.csv'

try:
    # Đọc file CSV vào DataFrame
    df = pd.read_csv(input_file)
    
    # Xác định các cột cần chuyển đổi sang dạng số (numeric)
    # Dựa trên lần chạy trước, chúng ta biết các cột này đang ở dạng 'object'
    numeric_columns_to_convert = [
        'Age', 'Born',
        'Playing Time_MP', 'Playing Time_Starts', 'Playing Time_Min', 'Playing Time_90s',
        'Performance_Gls', 'Performance_Ast', 'Performance_G+A', 'Performance_G-PK',
        'Performance_PK', 'Performance_PKatt', 'Performance_CrdY', 'Performance_CrdR',
        'Expected_xG', 'Expected_npxG', 'Expected_xAG', 'Expected_npxG+xAG',
        'Progression_PrgC', 'Progression_PrgP', 'Progression_PrgR',
        'Per 90 Minutes_Gls', 'Per 90 Minutes_Ast', 'Per 90 Minutes_G+A',
        'Per 90 Minutes_G-PK', 'Per 90 Minutes_G+A-PK', 'Per 90 Minutes_xG',
        'Per 90 Minutes_xAG', 'Per 90 Minutes_xG+xAG', 'Per 90 Minutes_npxG',
        'Per 90 Minutes_npxG+xAG'
    ]
    
    # Lọc ra các cột thực sự tồn tại trong DataFrame
    valid_numeric_cols = [col for col in numeric_columns_to_convert if col in df.columns]
    
    print(f"Tìm thấy {len(valid_numeric_cols)} cột để chuyển đổi sang dạng số.")
    
    # Chuyển đổi các cột đã xác định sang dạng số
    # errors='coerce' sẽ biến các giá trị không phải số thành NaN
    for col in valid_numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    print("\nThông tin DataFrame sau khi chuyển đổi:")
    df.info()

    # Kiểm tra xem cột 'Squad' (Đội) có tồn tại không
    if 'Squad' not in df.columns:
        print(f"Lỗi: Không tìm thấy cột 'Squad' trong {input_file}. Không thể nhóm theo đội.")
    else:
        # Chọn tất cả các cột dạng số để tính toán
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Loại bỏ các cột không phải là chỉ số thống kê (ví dụ: 'Born')
        cols_to_drop = ['Born']
        final_stat_cols = numeric_cols.drop(cols_to_drop, errors='ignore')
        
        if len(final_stat_cols) == 0:
            print("Không có cột số nào được chuyển đổi thành công.")
        else:
            print(f"\nĐang tính toán thống kê cho {len(final_stat_cols)} cột số...")
            
            # Nhóm dữ liệu theo 'Squad' và tính toán 'mean', 'median', 'std'
            team_stats = df.groupby('Squad')[final_stat_cols].agg(['mean', 'median', 'std'])
            
            # Lưu kết quả ra file CSV
            team_stats.to_csv(output_file)
            
            print(f"\nĐã tính toán thống kê và lưu vào {output_file} thành công.")
            print("\nMột phần kết quả (5 dòng đầu):")
            print(team_stats.head())

except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file {input_file}.")
except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")