"""기존 옷장 아이템에 sub_h / sub_s / sub_v / sub_ratio 배치 업데이트"""
import sqlite3, json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'user_data.db')

from image_processor import extract_dominant_color
from PIL import Image
import colorsys

conn = sqlite3.connect(DB_PATH)

# 컬럼 없으면 생성
for col in ["sub_h REAL", "sub_s REAL", "sub_v REAL", "sub_ratio REAL"]:
    try:
        conn.execute(f"ALTER TABLE user_closet ADD COLUMN {col}")
    except Exception:
        pass
conn.commit()

rows = conn.execute(
    "SELECT id, name, image_path FROM user_closet WHERE sub_h IS NULL"
).fetchall()
print(f"Updating {len(rows)} items...")

updated = failed = 0
for item_id, name, image_path in rows:
    if not image_path or not os.path.exists(image_path):
        print(f"  [{item_id}] {name} - skip (no file)")
        failed += 1
        continue
    try:
        img    = Image.open(image_path).convert("RGBA")
        result = extract_dominant_color(img)
        conn.execute(
            "UPDATE user_closet SET sub_h=?, sub_s=?, sub_v=?, sub_ratio=? WHERE id=?",
            (result['sub_h'], result['sub_s'], result['sub_v'], result['sub_ratio'], item_id)
        )
        conn.commit()
        print(f"  [{item_id}] {name} | sub_h={result['sub_h']:.3f} sub_s={result['sub_s']:.3f} sub_ratio={result['sub_ratio']:.2f}")
        updated += 1
    except Exception as e:
        print(f"  [{item_id}] {name} - FAILED: {e}")
        failed += 1

conn.close()
print(f"\nDone: {updated} updated, {failed} failed/skipped")
