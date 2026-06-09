"""
Batch update embeddings for existing closet items that have no embedding.
Runs analyze_existing_image on each item's stored image.
"""
import sqlite3
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'user_data.db')

print("Loading image_processor...")
try:
    from image_processor import analyze_existing_image
    print("  OK")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
rows = conn.execute(
    "SELECT id, name, image_path FROM user_closet WHERE embedding IS NULL"
).fetchall()

print(f"\nFound {len(rows)} items without embedding")

updated = 0
failed  = 0

for item_id, name, image_path in rows:
    if not image_path or not os.path.exists(image_path):
        print(f"  [{item_id}] {name} - skip (no file)")
        failed += 1
        continue

    try:
        result = analyze_existing_image(image_path)
        emb = result.get("embedding")
        style_tag = result.get("style_tag")
        color_type = result.get("color_type")
        hex_color  = result.get("hex")
        h, s, v    = result.get("h"), result.get("s"), result.get("v")
        is_neutral = 1 if result.get("is_neutral") else 0

        conn.execute(
            """UPDATE user_closet
               SET embedding=?, style_tag=?, color_type=?, hex_color=?,
                   h=?, s=?, v=?, is_neutral=?
               WHERE id=?""",
            (json.dumps(emb) if emb else None,
             style_tag, color_type, hex_color,
             h, s, v, is_neutral,
             item_id)
        )
        conn.commit()
        emb_ok = "OK" if emb else "None"
        print(f"  [{item_id}] {name} - embedding={emb_ok}, style={style_tag}")
        updated += 1
    except Exception as e:
        print(f"  [{item_id}] {name} - FAILED: {e}")
        failed += 1

conn.close()
print(f"\nDone: {updated} updated, {failed} failed/skipped")
