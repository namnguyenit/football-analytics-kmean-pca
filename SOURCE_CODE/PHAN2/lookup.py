import argparse
import requests
import json
import pandas as pd
import platform
import os

BASE_URL = "http://localhost:5000"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tra cứu thông tin cầu thủ hoặc câu lạc bộ"
    )

    parser.add_argument("--name", type=str, help="Tên cầu thủ cần tra cứu")
    parser.add_argument("--club", type=str, help="Tên câu lạc bộ cần tra cứu")

    args = parser.parse_args()

    if not args.name and not args.club:
        print("Bạn cần nhập: --name <tên> hoặc --club <tên>")
        exit()

    return args


def build_request(args):
    if args.name:
        return "/player", {"name": args.name}, args.name.replace(" ", "_") + ".csv"

    if args.club:
        return "/club", {"club": args.club}, args.club.replace(" ", "_") + ".csv"


def send_request(endpoint, params):
    url = BASE_URL + endpoint
    print(f"Đang gửi request tới: {url} với tham số {params}\n")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi request: {e}")
        exit()


def save_csv(data, filename):
    df = pd.DataFrame(data)

    try:
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu kết quả vào file: {filename}")
    except PermissionError:
        print(f"\nKhông thể ghi file '{filename}'.")
        print("File này đang được mở trong Excel. Vui lòng đóng lại rồi chạy lại.")
        exit()

    if platform.system() == "Windows":
        print("Đang mở file CSV bằng Excel...")
        try:
            os.startfile(filename)
        except Exception as e:
            print(f"⚠ Không thể mở file CSV: {e}")
    else:
        print("(Không tự động mở file CSV trên hệ điều hành này.)")


def main():
    args = parse_arguments()
    endpoint, params, filename = build_request(args)

    data = send_request(endpoint, params)

    print("Kết quả dạng JSON:")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    if isinstance(data, list) and len(data) > 0:
        save_csv(data, filename)
    else:
        print("\nKhông có dữ liệu để lưu vào CSV.")


if __name__ == "__main__":
    main()
