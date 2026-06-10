"""기존 옷장 아이템에 dominant_ratio / color_variance / is_patterned 배치 업데이트"""
import sqlite3, json, os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'user_data.db')

from image_processor import extract_dominant_color
from PIL import Image

conn = sqlite3.connect(DB_PATH)
rows = conn.execute(
    "SELECT id, name, image_path FROM user_closet WHERE is_patterned IS NULL OR dominant_ratio IS NULL"
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
            "UPDATE user_closet SET dominant_ratio=?, color_variance=?, is_patterned=? WHERE id=?",
            (result['dominant_ratio'], result['color_variance'],
             1 if result['is_patterned'] else 0, item_id)
        )
        conn.commit()
        print(f"  [{item_id}] {name} | ratio={result['dominant_ratio']:.2f} var={result['color_variance']:.1f} patterned={result['is_patterned']}")
        updated += 1
    except Exception as e:
        print(f"  [{item_id}] {name} - FAILED: {e}")
        failed += 1

conn.close()
print(f"\nDone: {updated} updated, {failed} failed/skipped")
