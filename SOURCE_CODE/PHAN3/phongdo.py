import pandas as pd
import numpy as np

# Định nghĩa tên file input
input_file = 'squad_stats.csv'

try:
    # Tải dataframe
    df = pd.read_csv(input_file)
    
    # In thông tin để kiểm tra kiểu dữ liệu
    print("--- DataFrame Info (Trước khi chuyển đổi) ---")
    df.info()
    
    # Lưu trữ cột 'Squad' (tên đội)
    squad_col = df['Squad']
    
    # Xác định tất cả các cột *ngoại trừ* 'Squad' để chuyển đổi sang dạng số
    cols_to_convert = df.columns.drop('Squad')
    
    # Chuyển đổi tất cả các cột khác sang dạng số
    # errors='coerce' sẽ biến các giá trị không phải số thành NaN
    df_numeric = df[cols_to_convert].apply(pd.to_numeric, errors='coerce')
    
    # Ghép cột 'Squad' trở lại với dữ liệu số đã xử lý
    df_processed = pd.concat([squad_col, df_numeric], axis=1)
    
    # Đặt 'Squad' làm chỉ mục (index) để tra cứu dễ dàng hơn
    df_processed.set_index('Squad', inplace=True)
    
    print("\n--- ĐỘI CÓ CHỈ SỐ CAO NHẤT CHO MỖI HẠNG MỤC ---")
    
    results = {}
    # Lặp qua tất cả các cột số
    for col in df_processed.columns:
        try:
            # Tìm chỉ mục (Tên đội) của giá trị lớn nhất
            max_team = df_processed[col].idxmax()
            # Lấy giá trị lớn nhất
            max_value = df_processed[col].max()
            
            results[col] = {'Team': max_team, 'Value': max_value}
            print(f"[{col}]: {max_team} (Giá trị: {max_value})")
            
        except Exception as e:
            # Xử lý các lỗi tiềm ẩn (ví dụ: cột toàn NaN)
            print(f"[{col}]: Lỗi khi xử lý - {e}")
            
    # --- Phần 2: Phân tích "Phong độ tốt nhất" ---
    print("\n--- PHÂN TÍCH PHONG ĐỘ (DỰA TRÊN DỮ LIỆU) ---")
    
    # Xác định các chỉ số chính cho "phong độ tốt"
    # Chúng tôi sử dụng tên cột đã xác định từ bản in ra
    key_metrics = [
        'Performance_Gls',        # Bàn thắng
        'Performance_Ast',        # Kiến tạo
        'Expected_xG',            # Bàn thắng kỳ vọng
        'Expected_xAG',           # Kiến tạo kỳ vọng
        'Unnamed: 3_level_0_Poss' # Tỷ lệ kiểm soát bóng
    ]
    
    best_form_summary = {}
    
    for metric in key_metrics:
        if metric in results:
            best_form_summary[metric] = results[metric]
            print(f"Cao nhất {metric}: {results[metric]['Team']} ({results[metric]['Value']})")
        else:
            print(f"Không tìm thấy chỉ số: {metric}")
            
    # Đồng thời kiểm tra kỷ luật phòng ngự (ít thẻ vàng hơn là tốt hơn)
    try:
        min_yellow_col = 'Performance_CrdY'
        min_yellow_team = df_processed[min_yellow_col].idxmin()
        min_yellow_val = df_processed[min_yellow_col].min()
        print(f"Ít thẻ vàng nhất (Performance_CrdY): {min_yellow_team} ({min_yellow_val})")
        best_form_summary['Min_CrdY'] = {'Team': min_yellow_team, 'Value': min_yellow_val}
    except Exception as e:
        print(f"Không thể tìm thấy chỉ số thẻ vàng: {e}")
        
except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file {input_file}")
except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")