from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import uuid
import json
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps

# 백엔드 모듈 import (없으면 fallback 모드로 실행)
try:
    from image_processor import process_clothing_image
    HAS_PROCESSOR = True
except ImportError:
    HAS_PROCESSOR = False
    print("⚠️  image_processor.py 없음 — 배경 제거 비활성화")

try:
    from recommend_engine import FashionRecommendationEngine
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False
    print("⚠️  recommend_engine.py 없음 — 랜덤 추천으로 대체")

# ══════════════════════════════════════
# 앱 설정
# ══════════════════════════════════════
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

SECRET_KEY = "dailycloset-secret-2026"
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH    = os.path.join(BASE_DIR, "user_data.db")

os.makedirs(STATIC_DIR, exist_ok=True)

# ══════════════════════════════════════
# DB 초기화
# ══════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    UNIQUE NOT NULL,
            password   TEXT    NOT NULL,
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_closet (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            colors      TEXT,
            materials   TEXT,
            image_path  TEXT,
            color_type  TEXT,
            hex_color   TEXT,
            h           REAL,
            s           REAL,
            v           REAL,
            is_neutral  INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ══════════════════════════════════════
# 인증 헬퍼
# ══════════════════════════════════════
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def make_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "인증이 필요합니다"}), 401
        try:
            payload = jwt.decode(auth[7:], SECRET_KEY, algorithms=["HS256"])
            user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "토큰이 만료되었습니다"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "유효하지 않은 토큰입니다"}), 401
        return f(user_id, *args, **kwargs)
    return decorated

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ══════════════════════════════════════
# Static 파일 서빙
# ══════════════════════════════════════
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

# ══════════════════════════════════════
# AUTH
# ══════════════════════════════════════
@app.route("/auth/signup", methods=["POST"])
def signup():
    data     = request.get_json() or {}
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "모든 필드를 입력해주세요"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hash_pw(password)),
        )
        conn.commit()
        user  = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        token = make_token(user["id"])
        return jsonify({"token": token, "name": user["name"], "email": user["email"]}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "이미 사용 중인 이메일입니다"}), 409
    finally:
        conn.close()

@app.route("/auth/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, hash_pw(password)),
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "이메일 또는 비밀번호가 올바르지 않습니다"}), 401

    token = make_token(user["id"])
    return jsonify({"token": token, "name": user["name"], "email": user["email"]})

@app.route("/auth/me", methods=["GET"])
@token_required
def get_me(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"]})

# ══════════════════════════════════════
# CLOSET
# ══════════════════════════════════════
def row_to_item(row):
    image_url = None
    if row["image_path"]:
        image_url = "/static/" + os.path.basename(row["image_path"])
    return {
        "id":        row["id"],
        "name":      row["name"],
        "category":  row["category"],
        "colors":    json.loads(row["colors"])    if row["colors"]    else [],
        "materials": json.loads(row["materials"]) if row["materials"] else [],
        "imageUrl":  image_url,
        "colorType": row["color_type"],
        "hexColor":  row["hex_color"],
        "isNeutral": bool(row["is_neutral"]),
    }

@app.route("/closet", methods=["GET"])
@token_required
def get_closet(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM user_closet WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return jsonify([row_to_item(r) for r in rows])

# ※ /closet/remove-bg 는 /closet/<int:item_id> 보다 먼저 등록
@app.route("/closet/remove-bg", methods=["POST"])
def remove_background():
    if "image" not in request.files:
        return jsonify({"error": "이미지 파일이 없습니다"}), 400

    file        = request.files["image"]
    ext         = os.path.splitext(file.filename)[1] or ".jpg"
    uid         = uuid.uuid4().hex
    input_path  = os.path.join(STATIC_DIR, f"tmp_{uid}{ext}")
    output_path = os.path.join(STATIC_DIR, f"bg_{uid}.png")

    file.save(input_path)

    if HAS_PROCESSOR:
        try:
            result = process_clothing_image(input_path, output_path)
            os.remove(input_path)
            return jsonify({
                "imageUrl":  "/static/" + os.path.basename(output_path),
                "colorInfo": result,
            })
        except Exception as e:
            if os.path.exists(input_path):
                os.remove(input_path)
            return jsonify({"error": str(e)}), 500
    else:
        import shutil
        shutil.copy(input_path, output_path)
        os.remove(input_path)
        return jsonify({"imageUrl": "/static/" + os.path.basename(output_path)})

@app.route("/closet/<int:item_id>", methods=["GET"])
@token_required
def get_closet_item(user_id, item_id):
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM user_closet WHERE id = ? AND user_id = ?",
        (item_id, user_id),
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "아이템을 찾을 수 없습니다"}), 404
    return jsonify(row_to_item(row))

@app.route("/closet", methods=["POST"])
@token_required
def add_closet_item(user_id):
    name          = request.form.get("name", "").strip()
    category      = request.form.get("category", "").strip()
    colors_raw    = request.form.get("colors", "[]")
    materials_raw = request.form.get("materials", "[]")

    if not name or not category:
        return jsonify({"error": "이름과 카테고리는 필수입니다"}), 400

    image_path = color_type = hex_color = None
    h = s = v = None
    is_neutral = 0

    if "image" in request.files:
        file      = request.files["image"]
        ext       = os.path.splitext(file.filename)[1] or ".jpg"
        unique    = f"closet_{uuid.uuid4().hex}.png"
        save_path = os.path.join(STATIC_DIR, unique)

        if HAS_PROCESSOR:
            tmp = os.path.join(STATIC_DIR, f"tmp_{uuid.uuid4().hex}{ext}")
            file.save(tmp)
            try:
                result     = process_clothing_image(tmp, save_path)
                color_type = result.get("color_type")
                hex_color  = result.get("hex")
                h, s, v    = result.get("h"), result.get("s"), result.get("v")
                is_neutral = 1 if result.get("is_neutral") else 0
            except Exception:
                pass
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
        else:
            file.save(save_path)

        image_path = save_path

    conn = get_db()
    cur  = conn.execute(
        """INSERT INTO user_closet
           (user_id, name, category, colors, materials, image_path,
            color_type, hex_color, h, s, v, is_neutral)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, category, colors_raw, materials_raw, image_path,
         color_type, hex_color, h, s, v, is_neutral),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM user_closet WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(row_to_item(row)), 201

@app.route("/closet/<int:item_id>", methods=["DELETE"])
@token_required
def delete_closet_item(user_id, item_id):
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM user_closet WHERE id = ? AND user_id = ?",
        (item_id, user_id),
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "아이템을 찾을 수 없습니다"}), 404

    if row["image_path"] and os.path.exists(row["image_path"]):
        try:
            os.remove(row["image_path"])
        except Exception:
            pass

    conn.execute("DELETE FROM user_closet WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "삭제되었습니다"})

# ══════════════════════════════════════
# OOTD
# ══════════════════════════════════════
CATEGORY_ORDER = ["아우터", "상의", "원피스", "하의", "신발"]

@app.route("/ootd/recommend", methods=["POST"])
@token_required
def ootd_recommend(user_id):
    import random
    data     = request.get_json() or {}
    keywords = data.get("keywords", [])

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM user_closet WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()

    items = [row_to_item(r) for r in rows]
    if not items:
        return jsonify([])

    result = []
    for cat in CATEGORY_ORDER:
        cat_items = [i for i in items if i["category"] == cat]
        if not cat_items:
            continue

        if HAS_ENGINE:
            try:
                engine = FashionRecommendationEngine()
                picked = engine.recommend(cat_items, keywords)
            except Exception:
                picked = random.choice(cat_items)
        else:
            neutral_kw     = {"#미니멀", "#캐주얼", "#워크웨어"}
            prefers_neutral = bool(set(keywords) & neutral_kw)
            neutrals       = [i for i in cat_items if i.get("isNeutral")]
            if prefers_neutral and neutrals:
                picked = random.choice(neutrals)
            else:
                picked = random.choice(cat_items)

        result.append(picked)

    return jsonify(result)

@app.route("/ootd/refresh", methods=["POST"])
@token_required
def ootd_refresh(user_id):
    import random
    data     = request.get_json() or {}
    category = data.get("category", "")

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM user_closet WHERE user_id = ? AND category = ?",
        (user_id, category),
    ).fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": f"{category} 아이템이 없습니다"}), 404

    return jsonify(row_to_item(random.choice(rows)))

# ══════════════════════════════════════
# 실행
# ══════════════════════════════════════
if __name__ == "__main__":
    print("✅ DailyCloset API 서버 — http://localhost:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
