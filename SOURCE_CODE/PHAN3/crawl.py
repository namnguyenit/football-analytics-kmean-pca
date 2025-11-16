import time
import pandas as pd
from bs4 import BeautifulSoup, Comment
import sys
from io import StringIO 

# Thư viện Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_fbref_table_selenium(url, table_id):
    """
    Hàm chung: Lấy 1 bảng bất kỳ từ FBref bằng Selenium,
    có xử lý cuộn (scroll) và chờ đợi thông minh.
    """
    
    # 1. THIẾT LẬP SELENIUM (Giữ nguyên)
    CHROME_DRIVER_PATH = "chromedriver.exe" 
    service = Service(executable_path=CHROME_DRIVER_PATH)
    
    options = Options()
    # options.add_argument("--headless") 
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/5.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")

    driver = None
    page_source = None
    
    try:
        # 2. KHỞI ĐỘNG TRÌNH DUYỆT
        driver = webdriver.Chrome(service=service, options=options)
        print(f"[{table_id}] Đang mở trình duyệt và tải trang...")
        driver.get(url)
        
        # === PHẦN SỬA LỖI QUAN TRỌNG ===
        
        # 3. CHỜ CHO CÁI "DIV" BỌC NGOÀI XUẤT HIỆN
        # Thay vì dùng driver.find_element (tìm ngay), 
        # chúng ta dùng WebDriverWait để chờ tối đa 10 giây
        
        placeholder_div = None
        wait = WebDriverWait(driver, 10) # Tạo đối tượng "chờ"
        
        try:
            # Ưu tiên chờ cái div 'div_...'
            print(f"[{table_id}] Đang chờ placeholder 'div_{table_id}' xuất hiện...")
            placeholder_div = wait.until(
                EC.presence_of_element_located((By.ID, f"div_{table_id}"))
            )
            print(f"[{table_id}] Đã tìm thấy 'div_{table_id}'.")
        except:
            # Nếu sau 10s không thấy, thử chờ cái div '..._sh'
            print(f"[{table_id}] Không tìm thấy 'div_{table_id}', đang thử chờ '{table_id}_sh'...")
            placeholder_div = wait.until(
                EC.presence_of_element_located((By.ID, f"{table_id}_sh"))
            )
            print(f"[{table_id}] Đã tìm thấy '{table_id}_sh'.")
        
        # === KẾT THÚC PHẦN SỬA LỖI ===

        # 4. CUỘN TRANG (Giữ nguyên)
        print(f"[{table_id}] Đang cuộn (scroll) đến bảng...")
        driver.execute_script("arguments[0].scrollIntoView(true);", placeholder_div)
        
        # 5. CHỜ JAVASCRIPT TẢI BẢNG (Giữ nguyên)
        print(f"[{table_id}] Đang chờ JavaScript giải nén/tải bảng...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, table_id))
        )
        
        print(f"[{table_id}] Bảng đã được tải! Đang lấy nội dung trang...")
        page_source = driver.page_source

    except Exception as e:
        print(f"[{table_id}] ĐÃ XẢY RA LỖI KHI DÙNG SELENIUM: {e}", file=sys.stderr)
        return None
    finally:
        # 6. LUÔN LUÔN ĐÓNG TRÌNH DUYỆT
        if driver:
            driver.quit()
            
    # === PHẦN 7: XỬ LÝ HTML (Giữ nguyên) ===
    
    if not page_source:
        print(f"[{table_id}] Không lấy được page_source (nội dung trang).", file=sys.stderr)
        return None
        
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', {'id': table_id}) 
        
        if table:
            print(f"[{table_id}] Tìm thấy bảng, đang chuyển sang DataFrame...")
            df = pd.read_html(StringIO(str(table)))[0]
            df.columns = ['_'.join(col).strip() for col in df.columns.values]
            return df
        else:
            print(f"[{table_id}] LỖI: Không tìm thấy bảng sau khi Selenium chạy.", file=sys.stderr)
            return None

    except Exception as e:
        print(f"[{table_id}] ĐÃ XẢY RA LỖI KHI PHÂN TÍCH HTML: {e}", file=sys.stderr)
        return None

# ==================================================================
# === PHẦN ĐIỀU KHIỂN (Giữ nguyên, không thay đổi) ===
# ==================================================================
if __name__ == "__main__":
    
    url = "https://fbref.com/en/comps/9/2024-2025/stats/2024-2025-Premier-League-Stats"

    # --- LẤY BẢNG 1: Squad Standard Stats ---
    
    table_id_1 = "stats_squads_standard_for" 
    output_file_1 = "squad_stats.csv"
    
    print(f"--- Bắt đầu lấy bảng: {table_id_1} ---")
    df_squad = get_fbref_table_selenium(url, table_id_1)
    
    if df_squad is not None:
        df_squad = df_squad.rename(columns={
            'Unnamed: 0_level_0_Squad': 'Squad',
            'Unnamed: 1_level_0_# Pl': '# Pl'
        })
        print(f"\n--- DỮ LIỆU BẢNG {table_id_1} (In 5 dòng đầu) ---")
        print(df_squad.head())
        df_squad.to_csv(output_file_1, index=False, encoding='utf-8-sig')
        print(f"\nĐã lưu dữ liệu thành công ra file: {output_file_1}")
    else:
        print(f"Không thể lấy được dữ liệu cho bảng: {table_id_1}")
    
    print("\n" + "=" * 50 + "\n")

    # --- LẤY BẢNG 2: Player Standard Stats ---
    
    table_id_2 = "stats_standard"
    output_file_2 = "player_stats.csv"
    
    print(f"--- Bắt đầu lấy bảng: {table_id_2} ---")
    df_player = get_fbref_table_selenium(url, table_id_2)
    
    if df_player is not None:
        df_player = df_player.rename(columns={
            'Unnamed: 0_level_0_Rk': 'Rk',
            'Unnamed: 1_level_0_Player': 'Player',
            'Unnamed: 2_level_0_Nation': 'Nation',
            'Unnamed: 3_level_0_Pos': 'Pos',
            'Unnamed: 4_level_0_Squad': 'Squad',
            'Unnamed: 5_level_0_Age': 'Age',
            'Unnamed: 6_level_0_Born': 'Born'
        })
        
        print(f"\n--- DỮ LIỆU BẢNG {table_id_2} (In 5 dòng đầu) ---")
        print(df_player.head())
        df_player.to_csv(output_file_2, index=False, encoding='utf-8-sig')
        print(f"\nĐã lưu dữ liệu thành công ra file: {output_file_2}")
    else:
        print(f"Không thể lấy được dữ liệu cho bảng: {table_id_2}")