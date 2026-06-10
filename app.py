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
except Exception as e:
    HAS_PROCESSOR = False
    print(f"[WARN] image_processor load failed - bg removal disabled: {e}")

try:
    from recommend_engine import FashionRecommendationEngine
    HAS_ENGINE = True
except Exception as e:
    HAS_ENGINE = False
    print(f"[WARN] recommend_engine load failed - random fallback: {e}")

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
            embedding   TEXT,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # 기존 DB 마이그레이션: 신규 컬럼 없으면 추가
    for col_def in [
        "ALTER TABLE user_closet ADD COLUMN embedding TEXT",
        "ALTER TABLE user_closet ADD COLUMN style_tag TEXT",
        "ALTER TABLE user_closet ADD COLUMN sleeve_type TEXT",
        "ALTER TABLE user_closet ADD COLUMN bottom_length TEXT",
        "ALTER TABLE user_closet ADD COLUMN dominant_ratio REAL",
        "ALTER TABLE user_closet ADD COLUMN color_variance REAL",
        "ALTER TABLE user_closet ADD COLUMN is_patterned INTEGER DEFAULT 0",
        "ALTER TABLE user_closet ADD COLUMN sub_h REAL",
        "ALTER TABLE user_closet ADD COLUMN sub_s REAL",
        "ALTER TABLE user_closet ADD COLUMN sub_v REAL",
        "ALTER TABLE user_closet ADD COLUMN sub_ratio REAL",
    ]:
        try:
            c.execute(col_def)
        except sqlite3.OperationalError:
            pass  # 이미 존재하면 무시
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

    # embedding: JSON 문자열 → float list (없으면 None)
    try:
        embedding_raw = row["embedding"]
        embedding = json.loads(embedding_raw) if embedding_raw else None
    except (IndexError, KeyError):
        embedding = None

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
        "h":         row["h"],
        "s":         row["s"],
        "v":         row["v"],
        "embedding": embedding,
        "styleTag":      row["style_tag"]      if "style_tag"      in row.keys() else None,
        "sleeveType":    row["sleeve_type"]    if "sleeve_type"    in row.keys() else None,
        "bottomLength":  row["bottom_length"]  if "bottom_length"  in row.keys() else None,
        "dominantRatio": row["dominant_ratio"] if "dominant_ratio" in row.keys() else None,
        "colorVariance": row["color_variance"] if "color_variance" in row.keys() else None,
        "isPatterned":   bool(row["is_patterned"]) if "is_patterned" in row.keys() else False,
        "subH":          row["sub_h"]     if "sub_h"     in row.keys() else None,
        "subS":          row["sub_s"]     if "sub_s"     in row.keys() else None,
        "subV":          row["sub_v"]     if "sub_v"     in row.keys() else None,
        "subRatio":      row["sub_ratio"] if "sub_ratio" in row.keys() else None,
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
            # remove-bg 단계에서는 배경 제거만 수행 (빠른 미리보기용)
            # CLIP 임베딩/분류는 실제 저장(/closet POST) 시에만 수행
            from image_processor import remove_background_and_normalize
            remove_background_and_normalize(input_path, output_path)
            os.remove(input_path)
            return jsonify({
                "imageUrl": "/static/" + os.path.basename(output_path),
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
    embedding_json = None
    style_tag      = None
    dominant_ratio = None
    color_variance = None
    is_patterned   = 0
    sub_h          = None
    sub_s          = None
    sub_v          = None
    sub_ratio_val  = None
    sleeve_type    = request.form.get("sleeve_type")
    bottom_length  = request.form.get("bottom_length")

    # ── 경로 1: 이미 remove-bg를 거친 이미지 URL이 넘어온 경우 (주 흐름) ──
    processed_url = request.form.get("processed_url")  # 예: "/static/bg_xxx.png"

    if processed_url:
        src_filename = os.path.basename(processed_url)
        src_path     = os.path.join(STATIC_DIR, src_filename)
        unique       = f"closet_{uuid.uuid4().hex}.png"
        save_path    = os.path.join(STATIC_DIR, unique)

        if os.path.exists(src_path):
            import shutil
            shutil.copy(src_path, save_path)  # 이미 처리된 파일 복사

            if HAS_PROCESSOR:
                try:
                    from image_processor import analyze_existing_image
                    result     = analyze_existing_image(save_path)  # 배경제거 재실행 없음
                    color_type = result.get("color_type")
                    hex_color  = result.get("hex")
                    h, s, v    = result.get("h"), result.get("s"), result.get("v")
                    is_neutral = 1 if result.get("is_neutral") else 0
                    if result.get("embedding"):
                        embedding_json = json.dumps(result["embedding"])
                    style_tag      = result.get("style_tag")
                    dominant_ratio = result.get("dominant_ratio")
                    color_variance = result.get("color_variance")
                    is_patterned   = 1 if result.get("is_patterned") else 0
                    sub_h          = result.get("sub_h")
                    sub_s          = result.get("sub_s")
                    sub_v          = result.get("sub_v")
                    sub_ratio_val  = result.get("sub_ratio")
                except Exception as e:
                    print(f"[WARN] image analysis error (save continues): {e}")

        image_path = save_path

    # ── 경로 2: 원본 파일이 직접 올라온 경우 (fallback) ──
    elif "image" in request.files:
        file      = request.files["image"]
        ext       = os.path.splitext(file.filename)[1] or ".jpg"
        unique    = f"closet_{uuid.uuid4().hex}.png"
        save_path = os.path.join(STATIC_DIR, unique)

        if HAS_PROCESSOR:
            tmp = os.path.join(STATIC_DIR, f"tmp_{uuid.uuid4().hex}{ext}")
            file.save(tmp)
            try:
                result         = process_clothing_image(tmp, save_path)
                color_type     = result.get("color_type")
                hex_color      = result.get("hex")
                h, s, v        = result.get("h"), result.get("s"), result.get("v")
                is_neutral     = 1 if result.get("is_neutral") else 0
                dominant_ratio = result.get("dominant_ratio")
                color_variance = result.get("color_variance")
                is_patterned   = 1 if result.get("is_patterned") else 0
                sub_h          = result.get("sub_h")
                sub_s          = result.get("sub_s")
                sub_v          = result.get("sub_v")
                sub_ratio_val  = result.get("sub_ratio")
                if result.get("embedding"):
                    embedding_json = json.dumps(result["embedding"])
                style_tag = result.get("style_tag")
            except Exception as e:
                print(f"[WARN] image processing error (save continues): {e}")
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
            color_type, hex_color, h, s, v, is_neutral, embedding,
            style_tag, sleeve_type, bottom_length,
            dominant_ratio, color_variance, is_patterned,
            sub_h, sub_s, sub_v, sub_ratio)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, category, colors_raw, materials_raw, image_path,
         color_type, hex_color, h, s, v, is_neutral, embedding_json,
         style_tag, sleeve_type, bottom_length,
         dominant_ratio, color_variance, is_patterned,
         sub_h, sub_s, sub_v, sub_ratio_val),
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

def _apply_temperature_filter(category_items, temperature):
    """
    기온에 따라 카테고리별 아이템 필터링
    필터 조건을 만족하는 옷이 없으면 원본 그대로 반환 (옷 없다고 추천 막지 않음)
    """
    if temperature is None:
        return category_items

    temp = float(temperature)
    filtered = dict(category_items)

    # 아우터 포함 여부 (25도 이상이면 제외, 22~24도는 상의 소매에 따라 후처리)
    if temp >= 25 and "아우터" in filtered:
        del filtered["아우터"]

    # 상의 소매 길이 필터
    if "상의" in filtered:
        if temp >= 25:
            allowed = ["반팔", "민소매"]          # 더움 → 반팔·민소매만
        elif temp >= 22:
            allowed = ["반팔", "민소매", "긴팔"]   # 22~24도 환절기 → 모두 허용
        else:
            allowed = ["긴팔"]                    # 쌀쌀 → 긴팔만
        sleeve_filtered = [i for i in filtered["상의"] if i.get("sleeveType") in allowed]
        if sleeve_filtered:
            filtered["상의"] = sleeve_filtered

    # 하의 기장 필터 (20도 이상이면 반바지 허용)
    if "하의" in filtered:
        if temp >= 20:
            allowed = ["반바지", "긴바지"]
        else:
            allowed = ["긴바지"]
        bottom_filtered = [i for i in filtered["하의"] if i.get("bottomLength") in allowed]
        if bottom_filtered:
            filtered["하의"] = bottom_filtered

    return filtered


def _postprocess_outer(outfit, temperature):
    """
    22~24도 환절기: 엔진이 고른 상의가 긴팔이면 아우터 제거
    반팔·민소매면 아우터 유지
    """
    if temperature is None:
        return outfit

    temp = float(temperature)
    if not (22 <= temp < 25):
        return outfit

    top = next((i for i in outfit if i.get("category") == "상의"), None)
    if top and top.get("sleeveType") == "긴팔":
        outfit = [i for i in outfit if i.get("category") != "아우터"]

    return outfit


@app.route("/ootd/recommend", methods=["POST"])
@token_required
def ootd_recommend(user_id):
    import random
    data        = request.get_json() or {}
    keywords    = data.get("keywords", [])
    temperature = data.get("temperature")  # 프론트에서 넘어오는 기온 (°C)

    # 키워드 → CLIP 스타일 프롬프트 키 매핑 (clip_utils.STYLE_PROMPTS 키와 일치)
    # CLIP이 텍스트 프롬프트로 직접 임베딩하므로 fashion.db 보유 여부와 무관하게 6개 전부 지원
    KEYWORD_TO_STYLE = {
        "#캐주얼": "casual",
        "#미니멀": "minimal",
        "#클래식": "classic",
        "#스트릿": "street",
    }

    # 선택된 모든 키워드의 스타일을 수집 (중복 제거, 없으면 cityboy 기본값)
    target_styles = list(dict.fromkeys(
        KEYWORD_TO_STYLE[kw] for kw in keywords if kw in KEYWORD_TO_STYLE
    ))
    if not target_styles:
        target_styles = ["cityboy"]
    target_style = target_styles[0]  # fallback용 단일 스타일

    # ── 추천 엔진 사용 ──────────────────────────────────────────────────────
    if HAS_ENGINE:
        try:
            # user_data.db에서 옷장 아이템 조회 (app.py가 담당)
            conn = get_db()
            rows = conn.execute(
                "SELECT * FROM user_closet WHERE user_id = ?", (user_id,)
            ).fetchall()
            conn.close()

            all_items = [row_to_item(r) for r in rows]
            category_items = {}
            for cat in ["아우터", "상의", "하의", "신발"]:
                cat_list = [i for i in all_items if i["category"] == cat]
                if cat_list:
                    category_items[cat] = cat_list

            # 기온 기반 필터링 적용
            category_items = _apply_temperature_filter(category_items, temperature)

            # fashion.db에서 스타일 스코어 계산 (엔진이 담당)
            engine = FashionRecommendationEngine()
            outfit = engine.recommend_outfit_from_closet(
                category_items = category_items,
                target_style   = target_styles,  # 선택된 모든 스타일 전달
            )
            engine.close()

            if outfit:
                # 22~24도 환절기 후처리: 긴팔이면 아우터 제거
                outfit = _postprocess_outer(outfit, temperature)

                result = []
                for item in outfit:
                    result.append({
                        "id":        item.get("id"),
                        "name":      item.get("name"),
                        "category":  item.get("category"),
                        "imageUrl":  item.get("imageUrl"),
                        "colors":    item.get("colors", []),
                        "materials": item.get("materials", []),
                        "isNeutral": item.get("isNeutral", False),
                        "hexColor":  item.get("hexColor"),
                        "colorType": item.get("colorType"),
                    })
                return jsonify(result)
        except Exception as e:
            print(f"[WARN] recommendation engine error - random fallback: {e}")

    # ── 폴백: 랜덤 선택 (엔진 없거나 오류 시) ───────────────────────────────
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
        neutral_kw      = {"#미니멀", "#캐주얼", "#워크웨어"}
        prefers_neutral = bool(set(keywords) & neutral_kw)
        neutrals        = [i for i in cat_items if i.get("isNeutral")]
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
    print("[OK] DailyCloset API server - http://localhost:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
