"""
CLIP 임베딩이 실제로 작동하는지 테스트
가장 최근에 저장된 이미지 파일로 직접 테스트
"""
import sqlite3
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 가장 최근 아이템 이미지 경로 확인
conn = sqlite3.connect(os.path.join(BASE_DIR, 'user_data.db'))
row  = conn.execute(
    "SELECT id, name, image_path FROM user_closet ORDER BY id DESC LIMIT 1"
).fetchone()
conn.close()

if not row:
    print("옷장에 아이템이 없습니다.")
    exit()

item_id, name, image_path = row
print(f"테스트 아이템: [{item_id}] {name}")
print(f"이미지 경로: {image_path}")

if not image_path or not os.path.exists(image_path):
    print("[ERROR] 이미지 파일 없음")
    exit()

print("\n1. image_processor import 테스트...")
try:
    from image_processor import analyze_existing_image
    print("[OK] import 성공")
except Exception as e:
    print(f"[FAIL] import 실패: {e}")
    exit()

print("\n2. analyze_existing_image 실행 테스트...")
try:
    result = analyze_existing_image(image_path)
    print("[OK] 실행 성공")
    print(f"   color_type : {result.get('color_type')}")
    print(f"   style_tag  : {result.get('style_tag')}")
    emb = result.get('embedding')
    print(f"   embedding  : {len(emb)}차원" if emb else "   embedding  : None (CLIP 미작동)")
except Exception as e:
    print(f"[FAIL] 실행 실패: {e}")
    import traceback
    traceback.print_exc()
