import os
import sqlite3

# 이미지 처리 모듈에서 분석 함수를 가져옵니다.
from image_processor import process_clothing_image

# DB 연결 및 테이블 생성
conn = sqlite3.connect('fashion.db')
cur = conn.cursor()

# 테이블 생성 (season, gender 및 확장 데이터 반영)
cur.execute('DROP TABLE IF EXISTS clothes')
cur.execute('''
    CREATE TABLE clothes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        image_path TEXT,
        image_type TEXT,
        category TEXT,
        style TEXT,
        gender TEXT,  -- 성별 (man/woman)
        season TEXT,  -- 계절, 날씨 대응 (spring/summer/fall/winter)
        h REAL,          -- Hue (색상)
        s REAL,          -- Saturation (채도)
        v REAL,          -- Value (명도)
        is_neutral INTEGER  -- 무채색 여부 (0: 유채색, 1: 무채색)
    )
''')

# single과 coordinate가 모두 들어있는 최상위 폴더 경로를 지정
base_path = r"C:\Users\user\Personalized-fashion-styling-suggestion-tool\data\reference"

# 모든 하위 폴더 순회 (Recursive Scan)
print("확장된 메타 데이터 스펙 기반 데이터 등록 및 이미지 분석을 시작합니다...")

# os.walk로 모든 하위 폴더를 하나씩 탐색
for root, dirs, files in os.walk(base_path):
    for file_name in files:
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            # 중복 분석 방지: proc_ 파일은 원본 데이터 수집에서 제외
            if file_name.startswith("proc_") or "proc_proc_" in root:
                continue

            # 1. 파일의 전체 경로 표준화
            full_path = os.path.join(root, file_name).replace('\\', '/')
            
            # 2. 폴더 경로를 쪼개서 세부 메타 데이터 추출
            # 예: C:/Users/user/data/reference/single/shoes/workwear/woman/winter -> ['single', 'shoes', 'workwear', 'woman', 'winter']
            # base_path 이후의 하위 경로만 잘라내어 분석
            relative_path = os.path.relpath(root, base_path).replace('\\', '/')
            path_parts = [part.lower() for part in relative_path.split('/') if part]

            # 기본값 설정 (경로가 매칭되지 않을 경우를 대비한 예외 안전장치)
            image_type = "single"
            category = "top"
            style_label = "casual"
            gender = "man"
            season = "spring"
            
            # 3. 수집기 (image_collect.py) 폴더 설계 규칙에 맞춰 배열 인덱스로 자동 매핑
            # 구조: single (shoes 제외) - [image_type] / [category] / [style] / [gender] / [season] (5단계)
            # 구조: single (shoes만) - [image_type] / [category] / [style] / [gender] (4단계)
            # 구조: coordinate - [image_type] / [style] / [gender] / [season] (4단계)
            if len(path_parts) == 4:
                if path_parts[0] == "coordinate":
                    image_type  = path_parts[0]  # coordinate
                    style_label = path_parts[1]  # casual, cityboy, classic, minimal, street, workwear
                    gender      = path_parts[2]  # man or woman
                    season      = path_parts[3]  # spring, summer, fall, winter
                
                    # coordinate는 상/하의/아우터/신발이 모두 합쳐져 있으므로
                    # 카테고리를 특정할 수 없어서 'set'로 지정
                    category    = "set"

                elif path_parts[0] == "single" and path_parts[1] == "shoes":
                    img_type    = path_parts[0]  # single
                    category    = path_parts[1]  # shoes
                    style_label = path_parts[2]  # casual, cityboy, classic, minimal, street, workwear
                    gender      = path_parts[3]  # man or woman
                    # 신발은 계절 폴더가 없으므로, 기본값 'all'(사계절)로 지정
                    season      = "all"          

                else:
                    # 그 외에 4단계 구조일 경우의 방어 코드
                    image_type  = path_parts[0]
                    category    = path_parts[1]
                    style_label = path_parts[2]
                    gender      = path_parts[3]
                    season      = "spring"
                    
            elif len(path_parts) >= 5:
                image_type  = path_parts[0]  # single
                category    = path_parts[1]  # top, bottom, outer, shoes 
                style_label = path_parts[2]  # casual, cityboy, classic, minimal, street, workwear
                gender      = path_parts[3]  # man or woman
                season      = path_parts[4]  # spring, summer, fall, winter
                                    
            else:
                # 4. 폴더 깊이가 3개 이하로 일치하지 않는 데이터나 예외 경로일 경우 차선책 백업 로직
                image_type = "single" if "single" in root.lower() else "coordinate"
                style_label = os.path.basename(root)

                if "top" in root.lower(): category = "top"
                elif "bottom" in root.lower(): category = "bottom"
                elif "outer" in root.lower(): category = "outer"
                elif "shoes" in root.lower(): category = "shoes"
                
                gender = "woman" if "woman" in root.lower() else "man"

                if "spring" in root.lower(): season = "spring"
                elif "summer" in root.lower(): season = "summer"
                elif "fall" in root.lower(): season = "fall"
                elif "winter" in root.lower(): season = "winter"

            try:
                # 5. image_processor를 사용해 이미지의 HSV 색상 정보와 무채색 여부 추출
                # 배경 제거된 이미지를 저장할 출력 경로 설정 (예: 원본 파일명 앞에 'proc_'를 붙임)
                # 만약 원본을 덮어쓰거나 별도 폴더에 모으고 싶으면 이 경로를 조절
                output_path = os.path.join(root, "proc_" + file_name).replace('\\', '/')
                
                # 이미지 처리 통합 파이프라인 엔진 가동 (배경 제거, 정규화, 색상 분석을 한 번에 실행)
                analysis_result = process_clothing_image(full_path, output_path)
                
                # 반환된 딕셔너리에서 정밀 소수값 및 플래그 데이터 추출 (K-means 알고리즘 결과물 수신)
                h_val = analysis_result["h"] 
                s_val = analysis_result["s"]
                v_val = analysis_result["v"] 
                neutral_flag = 1 if analysis_result["is_neutral"] else 0

                # 6. 확장된 쿼리로 DB 등록 
                cur.execute('''
                    INSERT INTO clothes (product_name, image_path, image_type, category, style, gender, season, h, s, v, is_neutral)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (file_name, output_path, image_type, category, style_label, gender, season, h_val, s_val, v_val, neutral_flag))
                
                print(f"등록 및 분석 완료: {file_name} [{image_type} | {category} | {style_label} | {gender} | {season}]")
                
            except Exception as e:
                # 특정 이미지 분석 중 에러가 나더라도 전체 프로세스가 멈추지 않도록 예외 처리
                print(f"분석 실패시 건너뜀 [{file_name}]: {e}")
                continue     

# 데이터 반영 및 검증 통계 출력
conn.commit()
print("-" * 60)
print("모든 세부 폴더의 이미지 데이터 가공 및 DB 구축이 성공적으로 완료되었습니다.")

# 확장 데이터 검증용 다차원 교차 통계 쿼리
cur.execute("SELECT category, style, gender, season, COUNT(*) FROM clothes GROUP BY category, style, gender, season")
print("\n[카테고리 X 스타일 X 성별 X 계절] 구축 현황")
for row in cur.fetchall():
    print(f" - {row[0]}/{row[1]}/{row[2]}/{row[3]}: {row[4]}개")

conn.close()
