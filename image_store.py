import os
import sqlite3

# DB 연결 및 테이블 생성
conn = sqlite3.connect('fashion.db')
cur = conn.cursor()

# 테이블 생성 (기존 테이블이 있다면 유지)
cur.execute('DROP TABLE IF EXISTS clothes')
cur.execute('''
    CREATE TABLE clothes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        style TEXT,
        category TEXT,
        image_type TEXT,
        image_path TEXT
    )
''')

# single과 coordinate가 모두 들어있는 상위 폴더 경로를 지정
base_path = r"C:\Users\user\data\reference"

# 모든 하위 폴더 순회 (Recursive Scan)
print("데이터 등록을 시작합니다...")

# os.walk는 하위 폴더를 하나씩 방문
for root, dirs, files in os.walk(base_path):
    for file_name in files:
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            # 1. 파일의 전체 경로 생성
            full_path = os.path.join(root, file_name)
            
            # 2. 폴더 이름을 '스타일'로 활용
            # 예: ...\coordinate\workwear\cloth_1.jpg -> style은 'workwear'가 됨
            style_label = os.path.basename(root)

            # 2. 이미지 타입 판별 (경로 분석)
            # 경로에 'single'이 있으면 'single', 아니면 'coordinate'로 분류
            if "single" in root.lower():
                img_type = "single"
            else:
                img_type = "coordinate"
                
            # 3. 카테고리 판별 (파일명에 키워드가 있을 경우)
            category = "Etc"
            if "pants" in file_name.lower() or "팬츠" in file_name:
                category = "Pants"
            elif "outer" in file_name.lower() or "자켓" in file_name:
                category = "Outer"
                
            # 4. DB에 저장
            cur.execute('''
                INSERT INTO clothes (product_name, style, category, image_type, image_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_name, style_label, category, img_type, full_path))
        
            print(f"등록 완료: [{img_type} | {style_label}] {file_name}")

# 작업 마무리
conn.commit()
print("-" * 45)
print("모든 폴더의 사진이 DB에 성공적으로 저장되었습니다.")

# 타입별(단품/코디) 데이터 개수 확인
cur.execute("SELECT image_type, COUNT(*) FROM clothes GROUP BY image_type")
print("타입별 통계: ", cur.fetchall())

# 사용 예시: 워크웨어 스타일 중 '단품'만 랜덤으로 5개 뽑기
cur.execute("""
    SELECT image_path FROM clothes 
    WHERE style = 'workwear' 
      AND image_type = 'single' 
    ORDER BY RANDOM() 
    LIMIT 5
""")

# 2. 결과 가져오기 (리스트 형태로 반환됨)
rows = cur.fetchall()

# 3. 화면에 출력하기
print("\n--- [랜덤] 워크웨어 단품 (single) 사진 5개 리스트 ---")

if not rows:
    print("조건에 맞는 데이터가 DB에 없습니다. 스타일명이나 타입을 확인해 주세요.")
else:
    for i, row in enumerate(rows, 1):
        # row는 튜플 형태이므로 row[0]으로 실제 경로에 접근합니다.
        print(f"{i}. {row[0]}")

conn.close()
