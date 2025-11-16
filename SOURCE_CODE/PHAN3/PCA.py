import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
# Thư viện này cần thiết cho việc vẽ 3D
from mpl_toolkits.mplot3d import Axes3D 
import warnings

# Tắt các cảnh báo (warnings) để output sạch hơn
warnings.filterwarnings('ignore')

# --- Bước 1: Định nghĩa file và các chỉ số (features) ---
file_players = 'player_stats.csv'
# Các file output
output_file_2d = 'player_pca_2d_results.csv'
output_file_3d = 'player_pca_3d_results.csv'
plot_file_2d = 'pca_2d_scatter.png'
plot_file_3d = 'pca_3d_scatter.png'

# Các cột cần chuyển sang số
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

# Các chỉ số (features) đã chọn ở bước trước
feature_columns = [
    'Age',
    'Playing Time_90s',
    'Per 90 Minutes_Gls',
    'Per 90 Minutes_Ast',
    'Per 90 Minutes_xG',
    'Per 90 Minutes_xAG',
    'Progression_PrgC',
    'Progression_PrgP',
    'Performance_CrdY'
]

try:
    # --- Bước 2: Tải và Tiền xử lý Dữ liệu ---
    # (Lặp lại chính xác quy trình như K-Means để đảm bảo dữ liệu khớp)
    df = pd.read_csv(file_players)
    
    valid_numeric_cols = [col for col in numeric_columns_to_convert if col in df.columns]
    
    for col in valid_numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df_analysis = df[['Player', 'Squad', 'Pos'] + feature_columns].copy()
    df_analysis.dropna(subset=feature_columns, inplace=True)
    
    # Lọc các cầu thủ chơi ít (dưới 5 trận * 90 phút)
    df_analysis = df_analysis[df_analysis['Playing Time_90s'] > 5.0]
    
    # QUAN TRỌNG: Reset index để chuẩn bị cho việc ghép (concat) sau này
    df_analysis.reset_index(drop=True, inplace=True)

    print(f"Đã tải và xử lý {len(df_analysis)} cầu thủ.")

    # Tách dữ liệu player và dữ liệu features
    player_info = df_analysis[['Player', 'Squad', 'Pos']].copy()
    df_features = df_analysis[feature_columns].copy()

    # --- Bước 3: Co giãn Dữ liệu (Scaling) ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_features)
    
    print("Đã co giãn (scale) dữ liệu.")

    # --- Bước 4: Chạy K-Means (để lấy nhãn cụm) ---
    # Sử dụng K=5 (từ kết quả phân tích trước)
    OPTIMAL_K = 5
    kmeans = KMeans(n_clusters=OPTIMAL_K, init='k-means++', n_init=10, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)
    
    print(f"Đã chạy K-Means và gán nhãn {OPTIMAL_K} cụm.")

    # --- Bước 5: Chạy PCA 2 Chiều (2D) ---
    pca_2d = PCA(n_components=2, random_state=42)
    X_pca_2d = pca_2d.fit_transform(X_scaled)
    
    # Giải thích phương sai
    explained_variance_2d = pca_2d.explained_variance_ratio_
    print(f"\n--- PCA 2D ---")
    print(f"Phương sai được giải thích bởi PC1: {explained_variance_2d[0]*100:.2f}%")
    print(f"Phương sai được giải thích bởi PC2: {explained_variance_2d[1]*100:.2f}%")
    print(f"Tổng phương sai được giải thích (2D): {np.sum(explained_variance_2d)*100:.2f}%")

    # Tạo 2D DataFrame
    df_pca_2d = pd.DataFrame(X_pca_2d, columns=['PC1', 'PC2'])
    df_plot_2d = pd.concat([player_info, df_pca_2d], axis=1)
    df_plot_2d['Cluster'] = clusters
    
    # Lưu file 2D
    df_plot_2d.to_csv(output_file_2d, index=False)
    print(f"Đã lưu kết quả PCA 2D vào: {output_file_2d}")

    # --- Bước 6: Vẽ Biểu đồ 2D ---
    plt.figure(figsize=(12, 8))
    # 'c=clusters' sẽ tô màu các điểm theo nhãn cụm K-Means
    scatter = plt.scatter(df_plot_2d['PC1'], df_plot_2d['PC2'], c=df_plot_2d['Cluster'], cmap='viridis', alpha=0.7)
    
    # Thêm thanh màu (colorbar) để giải thích
    cbar = plt.colorbar(scatter, ticks=range(OPTIMAL_K))
    cbar.set_label('Cluster (Cụm)')
    
    plt.title('Phân cụm K-Means (K=5) trên 2 chiều PCA')
    plt.xlabel(f'Thành phần Chính 1 (PC1 - {explained_variance_2d[0]*100:.1f}%)')
    plt.ylabel(f'Thành phần Chính 2 (PC2 - {explained_variance_2d[1]*100:.1f}%)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig(plot_file_2d)
    print(f"Đã lưu biểu đồ PCA 2D vào: {plot_file_2d}")

    # --- Bước 7: Chạy PCA 3 Chiều (3D) ---
    pca_3d = PCA(n_components=3, random_state=42)
    X_pca_3d = pca_3d.fit_transform(X_scaled)
    
    # Giải thích phương sai
    explained_variance_3d = pca_3d.explained_variance_ratio_
    print(f"\n--- PCA 3D ---")
    print(f"Phương sai được giải thích bởi PC1: {explained_variance_3d[0]*100:.2f}%")
    print(f"Phương sai được giải thích bởi PC2: {explained_variance_3d[1]*100:.2f}%")
    print(f"Phương sai được giải thích bởi PC3: {explained_variance_3d[2]*100:.2f}%")
    print(f"Tổng phương sai được giải thích (3D): {np.sum(explained_variance_3d)*100:.2f}%")

    # Tạo 3D DataFrame
    df_pca_3d = pd.DataFrame(X_pca_3d, columns=['PC1', 'PC2', 'PC3'])
    df_plot_3d = pd.concat([player_info, df_pca_3d], axis=1)
    df_plot_3d['Cluster'] = clusters
    
    # Lưu file 3D
    df_plot_3d.to_csv(output_file_3d, index=False)
    print(f"Đã lưu kết quả PCA 3D vào: {output_file_3d}")

    # --- Bước 8: Vẽ Biểu đồ 3D ---
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    scatter = ax.scatter(df_plot_3d['PC1'], df_plot_3d['PC2'], df_plot_3d['PC3'], 
                         c=df_plot_3d['Cluster'], cmap='viridis', alpha=0.7, s=40) # s=40 để điểm to hơn
    
    # Thêm thanh màu
    cbar = fig.colorbar(scatter, ticks=range(OPTIMAL_K), shrink=0.7)
    cbar.set_label('Cluster (Cụm)')
    
    ax.set_title('Phân cụm K-Means (K=5) trên 3 chiều PCA')
    ax.set_xlabel(f'PC1 ({explained_variance_3d[0]*100:.1f}%)')
    ax.set_ylabel(f'PC2 ({explained_variance_3d[1]*100:.1f}%)')
    ax.set_zlabel(f'PC3 ({explained_variance_3d[2]*100:.1f}%)')
    plt.savefig(plot_file_3d)
    print(f"Đã lưu biểu đồ PCA 3D vào: {plot_file_3d}")

except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file {file_players}.")
except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")