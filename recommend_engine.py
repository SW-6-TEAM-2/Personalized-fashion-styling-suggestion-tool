import sqlite3
import math

# 두 RGB 색상 간의 유클리드 거리 계산 함수
def calculate_rgb_distance(r1, g1, b1, r2, g2, b2):
    """
    3차원 RGB 공간에서 두 색상 사이의 유클리드 거리를 계산합니다.
    값이 0에 가까울수록 두 색상이 서로 유사함을 의미합니다.
    """
    return math.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)


# 데이터베이스 연결 및 추천 엔진 클래스
class FashionRecommendationEngine:
    def __init__(self, db_path='fashion.db'):
        self.conn = sqlite3.connect(db_path)
        # SQLite 쿼리문 안에서 파이썬의 거리 계산 함수를 직접 쓸 수 있도록 등록
        self.conn.create_function("rgb_dist", 6, calculate_rgb_distance)
        self.cur = self.conn.cursor()

    def get_recommendations(self, user_rgb, target_style, target_type='coordinate', limit=5):
        """
        사용자의 옷 색상 (RGB)과 원하는 스타일에 맞는 최적의 아이템을 유사도 순으로 정렬하여 반환합니다.
        """
        user_r, user_g, user_b = user_rgb
        
        # 가중치 로직 적용 (is_neutral 플래그 활용 계획 반영)
        # 사용자의 옷이 무채색 (S < 0.15)이면 다양한 유채색 코디를 추천하고,
        # 사용자의 옷이 유채색이면 무채색 코디나 명도가 맞는 조화로운 옷을 우선 추천할 수 있는 쿼리 확장 기반
        
        sql_query = """
            SELECT id, product_name, style, image_type, image_path,
                   rgb_dist(?, ?, ?, h, s, v) AS distance,
                   is_neutral
            FROM clothes
            WHERE style = ? AND image_type = ?
            ORDER BY distance ASC
            LIMIT ?
        """
        
        self.cur.execute(sql_query, (user_r, user_g, user_b, target_style, target_type, limit))
        return self.cur.fetchall()

    def close(self):
        self.conn.close()


# 추천 로직 실행 테스트
if __name__ == "__main__":
    # 임시 테스트를 위해 가상의 데이터 세팅
    # 실제 구동 시에는 clothes 테이블에 h, s, v REAL 컬럼이 존재해야 함.
    print("정밀 추천 알고리즘을 가동합니다...")
    
    engine = FashionRecommendationEngine('fashion.db')
    
    # 사용자가 입력한 옷의 분석 결과
    # HSV 값이 각각 0~1 혹은 0~360, 0~100 등으로 정규화되어 저장되어 있어야 함.
    user_uploaded_rgb = (105, 95, 70)  # 카키/브라운 계열 RGB
    requested_style = "workwear"  # 사용자가 원하는 스타일 (예: 워크웨어)
    requested_type = "coordinate"  # 코디 컷 위주로 추천받기

    print(f"사용자 선택 색상 RGB{user_uploaded_rgb} 기반으로 '{requested_style}' 코디 추천 중...\n")
    
    try:
        results = engine.get_recommendations(
            user_rgb=user_uploaded_rgb,
            target_style=requested_style,
            target_type=requested_type,
            limit=5
        )
        
        print(f"===== 사용자의 {requested_style} 스타일 코디 추천 결과 (상위 5개) =====")
        if not results:
            print("조건에 맞는 코디 아이템이 DB에 없거나 테이블 구조를 확인해야 합니다.")
        else:
            for i, row in enumerate(results, 1):
                img_id, name, style, img_type, path, distance, is_neutral = row
                neutral_text = "무채색" if is_neutral == 1 else "유채색"
                print(f"{i}위. [색상 거리: {distance:.2f} ({neutral_text})] {name}")
                print(f"   - 추천 코디 이미지 경로: {path}")
                print(f"   - 분류: {style} / {img_type}")
                print("-" * 60)
                
    except sqlite3.OperationalError as e:
        print("\n데이터베이스 실행 에러 발생: {e}")
        print("만약 'no such column: h' 라고 뜬다면 image_store.py를 다시 돌려서 DB를 갱신해야 합니다.")
        
    finally:
        engine.close()
