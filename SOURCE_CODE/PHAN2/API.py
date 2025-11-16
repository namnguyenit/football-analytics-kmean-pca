from flask import Flask, request, jsonify, render_template_string
from flask_restful import Api, Resource
import sqlite3
import pandas as pd

#   KHỞI TẠO ỨNG DỤNG
app = Flask(__name__)
api = Api(app)

#   CẤU HÌNH KẾT NỐI DATABASE
DB_FILE = "football.sqlite"
MAIN_TABLE = "pl_stats_clean"

#   HÀM THỰC HIỆN TRUY VẤN SQL
def fetch_data(sql, params=()):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            result = pd.read_sql_query(sql, conn, params=params)
        return result, None
    except Exception as err:
        return None, str(err)

#   API: TÌM KIẾM THEO TÊN CẦU THỦ
class SearchPlayer(Resource):
    def get(self):
        keyword = request.args.get("name")

        if not keyword:
            return {"error": "Bạn cần truyền tham số ?name=<ten_cau_thu>"}, 400

        sql = f"SELECT * FROM {MAIN_TABLE} WHERE player LIKE ?"
        df, error_msg = fetch_data(sql, (f"%{keyword}%",))

        if df is None:
            return {"error": f"Lỗi SQL: {error_msg}"}, 500
        if df.empty:
            return {"message": f"Không tồn tại cầu thủ '{keyword}'"}, 404

        return df.to_dict(orient="records"), 200

#   API: TÌM KIẾM THEO TÊN CÂU LẠC BỘ
class SearchClub(Resource):
    def get(self):
        club_kw = request.args.get("club")

        if not club_kw:
            return {"error": "Bạn cần truyền tham số ?club=<ten_club>"}, 400

        sql = f"SELECT * FROM {MAIN_TABLE} WHERE club LIKE ?"
        df, error_msg = fetch_data(sql, (f"%{club_kw}%",))

        if df is None:
            return {"error": f"Lỗi SQL: {error_msg}"}, 500
        if df.empty:
            return {"message": f"Không tìm thấy CLB '{club_kw}'"}, 404

        return df.to_dict(orient="records"), 200

#   ĐĂNG KÝ API ROUTES
api.add_resource(SearchPlayer, "/player")
api.add_resource(SearchClub, "/club")


#   GIAO DIỆN HTML
@app.route("/ui")
def home_ui():
    page_html = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Tra cứu dữ liệu Premier League</title>
        <link rel="stylesheet" 
              href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

        <style>
            body { background: #0f172a; color: #fff; }
            .card-box { background: #1e293b; padding: 20px; border-radius: 14px; }
            .result-area { background: #1e293b; padding: 20px; border-radius: 12px; margin-top: 30px; }
            .scroll-zone {
                max-height: 440px; overflow-y: auto; overflow-x: auto;
                background: #243447; padding: 10px; border-radius: 12px;
            }
            thead th { background: #0f172a !important; position: sticky; top: 0; }
        </style>
    </head>

    <body>
        <div class="container mt-5">
            <h1 class="text-center fw-bold mb-4">⚽ Tra cứu dữ liệu bóng đá ⚽</h1>

            <div class="card-box">
                <h5>Tìm kiếm cầu thủ</h5>
                <div class="input-group mb-4">
                    <input id="inpPlayer" class="form-control" placeholder="Nhập tên cầu thủ...">
                    <button class="btn btn-primary" onclick="searchPlayer()">Tìm</button>
                </div>

                <h5>Tìm kiếm câu lạc bộ</h5>
                <div class="input-group">
                    <input id="inpClub" class="form-control" placeholder="Nhập tên CLB...">
                    <button class="btn btn-warning" onclick="searchClub()">Tìm</button>
                </div>
            </div>

            <div id="display"></div>
        </div>

        <script>
            function searchPlayer() {
                let name = document.getElementById("inpPlayer").value;
                fetch(`/player?name=${name}`)
                    .then(r => r.json())
                    .then(d => render(d));
            }

            function searchClub() {
                let name = document.getElementById("inpClub").value;
                fetch(`/club?club=${name}`)
                    .then(r => r.json())
                    .then(d => render(d));
            }

            function render(data) {
                const block = document.getElementById("display");

                if (data.error || data.message) {
                    block.innerHTML = `
                        <div class="alert alert-danger mt-4">
                            ${data.error || data.message}
                        </div>
                    `;
                    return;
                }

                let header = Object.keys(data[0]);
                let rows = data.map(r =>
                    `<tr>${Object.values(r).map(v => `<td>${v}</td>`).join("")}</tr>`
                ).join("");

                block.innerHTML = `
                    <div class="result-area">
                        <h3>Kết quả:</h3>
                        <div class="scroll-zone">
                            <table class="table table-dark table-striped table-bordered">
                                <thead>
                                    <tr>${header.map(h => `<th>${h}</th>`).join("")}</tr>
                                </thead>
                                <tbody>${rows}</tbody>
                            </table>
                        </div>
                    </div>
                `;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(page_html)

#   KHỞI CHẠY SERVER
if __name__ == "__main__":
    print(" Server chạy tại: http://localhost:5000")
    print("UI tại: http://localhost:5000/ui")
    app.run(debug=True)
