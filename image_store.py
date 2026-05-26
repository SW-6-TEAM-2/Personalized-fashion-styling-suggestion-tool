import os
import sqlite3

# 이미지 처리 모듈에서 분석 함수를 가져옵니다.
from image_processor import process_clothing_image

# DB 연결 및 테이블 생성
conn = sqlite3.connect('fashion.db')
cur = conn.cursor()

# 테이블 생성 (h, s, v, is_neutral 컬럼 구조 반영)
cur.execute('DROP TABLE IF EXISTS clothes')
cur.execute('''
    CREATE TABLE clothes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        style TEXT,
        category TEXT,
        image_type TEXT,
        image_path TEXT,
        h REAL,          -- Hue (색상)
        s REAL,          -- Saturation (채도)
        v REAL,          -- Value (명도)
        is_neutral INTEGER  -- 무채색 여부 (0: 유채색, 1: 무채색)
    )
''')

# single과 coordinate가 모두 들어있는 상위 폴더 경로를 지정
base_path = r"C:\Users\user\data\reference"

# 모든 하위 폴더 순회 (Recursive Scan)
print("데이터 등록 및 이미지 분석을 시작합니다...")

# os.walk는 하위 폴더를 하나씩 방문
for root, dirs, files in os.walk(base_path):
    for file_name in files:
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            # 1. 파일의 전체 경로 생성
            full_path = os.path.join(root, file_name).replace('\\', '/')
            
            # 2. 폴더 이름을 '스타일'로 활용
            # 예: ...\coordinate\workwear\cloth_1.jpg -> style은 'workwear'가 됨
            style_label = os.path.basename(root)

            # 3. 이미지 타입 판별 (경로 분석)
            # 경로에 'single'이 있으면 'single', 아니면 'coordinate'로 분류
            if "single" in root.lower():
                img_type = "single"
            else:
                img_type = "coordinate"
                
            # 4. 카테고리 판별 (파일명에 키워드가 있을 경우)
            category = "Etc"
            if "pants" in file_name.lower() or "팬츠" in file_name:
                category = "Pants"
            elif "outer" in file_name.lower() or "자켓" in file_name:
                category = "Outer"

            try:
                # 5. image_processor를 사용해 이미지의 HSV 색상 정보와 무채색 여부 추출
                # 배경 제거된 이미지를 저장할 출력 경로 설정 (예: 원본 파일명 앞에 'proc_'를 붙임)
                # 만약 원본을 덮어쓰거나 별도 폴더에 모으고 싶으면 이 경로를 조절
                output_path = os.path.join(root, "proc_" + file_name).replace('\\', '/')
                
                # 통합 함수 호출 (배경 제거, 정규화, 색상 분석을 한 번에 실행)
                analysis_result = process_clothing_image(full_path, output_path)
                
                # 반환된 딕셔너리에서 데이터 추출 (K-means 알고리즘 결과물 수신)
                h_val = analysis_result["rgb"][0]  # colorsys.rgb_to_hsv 인자 파싱 방식에 맞춰 
                s_val = analysis_result["rgb"][1]  # h, s, v를 개별 리턴하지 않고 
                v_val = analysis_result["rgb"][2]  # 분석 구조를 가졌으므로 딕셔너리 키값을 활용
                
                # 정밀 추천을 위해 리턴값에 맞춰 가공하거나, 
                # 임시로 rgb 값 혹은 분석된 속성값 (is_neutral)을 매핑
                
                # 딕셔너리 데이터 매칭
                # 추출한 HSV 정밀 소수점이 필요하다면 
                # 우선 딕셔너리에 들어있는 'is_neutral' 플래그를 정수 (0 또는 1)로 변환
                neutral_flag = 1 if analysis_result["is_neutral"] else 0
                # 6. DB에 새롭게 정의한 컬럼값 (h, s, v, is_neutral)을 포함하여 함께 저장
                cur.execute('''
                    INSERT INTO clothes (product_name, style, category, image_type, image_path, h, s, v, is_neutral)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (file_name, style_label, category, img_type, output_path, float(h_val), float(s_val), float(v_val), neutral_flag))
                
                print(f"등록 및 분석 완료: [{img_type} | {style_label}] {file_name} -> Type: {analysis_result['color_type']}")
                
            except Exception as e:
                # 특정 이미지 분석 중 에러가 나더라도 전체 프로세스가 멈추지 않도록 예외 처리
                print(f"분석 실패시 건너뜀 [{file_name}]: {e}")
                continue     

# 작업 마무리
conn.commit()
print("-" * 45)
print("모든 폴더의 사진 분석 및 DB 저장이 성공적으로 완료되었습니다.")

# 타입별(단품/코디) 데이터 개수 확인
cur.execute("SELECT image_type, COUNT(*) FROM clothes GROUP BY image_type")
print("타입별 통계: ", cur.fetchall())

conn.close()
