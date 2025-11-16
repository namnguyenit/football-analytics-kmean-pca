import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import warnings

# Tắt các cảnh báo (warnings) để output sạch hơn
warnings.filterwarnings('ignore')

# --- Bước 1: Định nghĩa các file và các chỉ số (features) ---
file_players = 'player_stats.csv'
output_file = 'player_clusters.csv'
elbow_plot_file = 'kmeans_elbow_plot.png'
silhouette_plot_file = 'kmeans_silhouette_plot.png'

# Các cột cần chuyển sang số (danh sách đầy đủ)
numeric_columns_to_convert = [
    'Age', 'Born', 'Playing Time_MP', 'Playing Time_Starts', 'Playing Time_Min', 'Playing Time_90s',
    'Performance_Gls', 'Performance_Ast', 'Performance_G+A', 'Performance_G-PK',
    'Performance_PK', 'Performance_PKatt', 'Performance_CrdY', 'Performance_CrdR',
    'Expected_xG', 'Expected_npxG', 'Expected_xAG', 'Expected_npxG+xAG',
    'Progression_PrgC', 'Progression_PrgP', 'Progression_PrgR',
    'Per 90 Minutes_Gls', 'Per 90 Minutes_Ast', 'Per 90 Minutes_G+A',
    'Per 90 Minutes_G-PK', 'Per 90 Minutes_G+A-PK', 'Per 90 Minutes_xG',
    'Per 90 Minutes_xAG', 'Per 90 Minutes_xG+xAG', 'Per 90 Minutes_npxG',
    'Per 90 Minutes_npxG+xAG'
]

# CHỌN LỌC CÁC CHỈ SỐ để phân cụm
feature_columns = [
    'Age',
    'Playing Time_90s', # Số "90 phút" đã chơi
    'Per 90 Minutes_Gls', # Bàn thắng trên 90p
    'Per 90 Minutes_Ast', # Kiến tạo trên 90p
    'Per 90 Minutes_xG',  # Bàn thắng kỳ vọng trên 90p
    'Per 90 Minutes_xAG', # Kiến tạo kỳ vọng trên 90p
    'Progression_PrgC', # Rê bóng tịnh tiến
    'Progression_PrgP', # Chuyền bóng tịnh tiến
    'Performance_CrdY'  # Thẻ vàng (để xem mức độ kỷ luật/vị trí)
]

try:
    # --- Bước 2: Tải và Tiền xử lý Dữ liệu ---
    df = pd.read_csv(file_players)
    
    # Lọc các cột số hợp lệ có trong file
    valid_numeric_cols = [col for col in numeric_columns_to_convert if col in df.columns]
    
    # Chuyển đổi các cột sang số
    for col in valid_numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Chỉ giữ lại các cột cần thiết cho phân tích
    df_analysis = df[['Player', 'Squad', 'Pos'] + feature_columns].copy()

    # QUAN TRỌNG: Loại bỏ bất kỳ cầu thủ nào có dữ liệu rỗng (NaN)
    df_analysis.dropna(subset=feature_columns, inplace=True)
    
    # Lọc ra các cầu thủ chơi ít (ví dụ: ít hơn 5 trận * 90 phút)
    # Điều này giúp mô hình ổn định hơn, tránh các chỉ số bị nhiễu
    df_analysis = df_analysis[df_analysis['Playing Time_90s'] > 5.0]

    print(f"Bắt đầu phân tích trên {len(df_analysis)} cầu thủ (sau khi lọc NaNs và thời gian chơi).")

    # Tách riêng phần dữ liệu để scale
    df_features = df_analysis[feature_columns].copy()

    # --- Bước 3: Co giãn Dữ liệu (Scaling) ---
    # Đây là bước bắt buộc với K-Means
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_features)
    
    print("Đã co giãn (scale) dữ liệu.")

    # --- Bước 4: Phương pháp Elbow & Silhouette để tìm K tối ưu ---
    inertia_list = []
    silhouette_list = []
    
    # K-range phải bắt đầu từ 2 vì Silhouette Score không được định nghĩa cho K=1
    k_range = range(2, 11) # Thử K từ 2 đến 10
    
    print("Đang tính toán K-Means cho K=2 đến 10...")
    for k in k_range:
        kmeans = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=42)
        kmeans.fit(X_scaled)
        
        # 1. Tính Inertia (cho Elbow)
        inertia_list.append(kmeans.inertia_)
        
        # 2. Tính Silhouette Score
        silhouette_list.append(silhouette_score(X_scaled, kmeans.labels_))
    
    print("Đã tính toán xong Inertia và Silhouette scores.")

    # --- Bước 5: Vẽ Biểu đồ Elbow ---
    plt.figure(figsize=(10, 6))
    plt.plot(k_range, inertia_list, marker='o', color='b')
    plt.title('Phương pháp "Khuỷu tay" (Elbow Method) tìm K tối ưu')
    plt.xlabel('Số lượng Cụm (K)')
    plt.ylabel('Inertia (Tổng bình phương khoảng cách trong cụm)')
    plt.grid(True)
    plt.xticks(k_range)
    plt.savefig(elbow_plot_file)
    print(f"Đã lưu biểu đồ Elbow vào file: {elbow_plot_file}")

    # --- Bước 6: Vẽ Biểu đồ Silhouette ---
    plt.figure(figsize=(10, 6))
    plt.plot(k_range, silhouette_list, marker='o', color='g')
    plt.title('Biểu đồ Silhouette tìm K tối ưu')
    plt.xlabel('Số lượng Cụm (K)')
    plt.ylabel('Silhouette Score (Điểm càng cao càng tốt)')
    plt.grid(True)
    plt.xticks(k_range)
    plt.savefig(silhouette_plot_file)
    print(f"Đã lưu biểu đồ Silhouette vào file: {silhouette_plot_file}")

    # --- Bước 7: Chạy K-Means cuối cùng với K tối ưu ---
    # Dựa trên phân tích 2 biểu đồ, chúng ta chọn K=5
    OPTIMAL_K = 5
    
    print(f"Chạy K-Means cuối cùng với K = {OPTIMAL_K}...")
    
    kmeans_final = KMeans(n_clusters=OPTIMAL_K, init='k-means++', n_init=10, random_state=42)
    clusters = kmeans_final.fit_predict(X_scaled)
    
    # --- Bước 8: Thêm kết quả vào DataFrame và Xuất file ---
    df_analysis['Cluster'] = clusters
    
    # Sắp xếp lại các cột để dễ đọc
    final_columns = ['Player', 'Squad', 'Pos', 'Cluster'] + feature_columns
    df_final_output = df_analysis[final_columns].sort_values(by=['Cluster', 'Player'])
    
    # Lưu file CSV
    df_final_output.to_csv(output_file, index=False)
    
    print(f"\nĐã hoàn thành! Kết quả phân cụm được lưu tại: {output_file}")
    
    # In ra "hồ sơ" (profile) của mỗi cụm để hiểu họ là ai
    cluster_profiles = df_analysis.groupby('Cluster')[feature_columns].mean()
    print("\n--- HỒ SƠ CỤM (GIÁ TRỊ TRUNG BÌNH CỦA CÁC CHỈ SỐ) ---")
    print(cluster_profiles)

except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file {file_players}. Vui lòng kiểm tra lại.")
except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")