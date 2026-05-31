import sqlite3
import math

# 두 HSV 색상 간의 유클리드 거리 계산 함수
def calculate_hsv_distance(h1, s1, v1, h2, s2, v2):
    """
    3차원 HSV 색상 공간에서 두 색상 사이의 수학적 (유클리드) 거리를 계산합니다.
    값은 모두 0.0 ~ 1.0 사이의 소수점이고, 이 값이 0에 가까울수록 두 색상이 서로 유사함을 의미합니다.
    """
    # 색상 (Hue)은 원형 (0~360도) 구조이므로, 0.0과 1.0이 만나는 특성을 고려해 각도로 변환 후 원통형 좌표계 거리 계산
    # 더 단순하게는 일반 유클리드로도 가능하지만, 원형 특성을 반영하면 훨씬 정밀해짐.
    theta1 = h1 * 2 * math.pi
    theta2 = h2 * 2 * math.pi
    
    # 원통형 좌표계 (Cylindrical coordinates) 변환 후 거리 계산
    x1, y1 = s1 * math.cos(theta1), s1 * math.sin(theta1)
    x2, y2 = s2 * math.cos(theta2), s2 * math.sin(theta2)
    
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (v1 - v2)**2)


# 데이터베이스 연결 및 추천 엔진 클래스
class FashionRecommendationEngine:
    def __init__(self, db_path='fashion.db'):
        self.conn = sqlite3.connect(db_path)
        # SQLite 쿼리문 안에서 파이썬의 거리 계산 함수를 직접 쓸 수 있도록 등록
        self.conn.create_function("hsv_dist", 6, calculate_hsv_distance)
        self.cur = self.conn.cursor()

    # 패션 가중치 로직이 적용된 정밀 스타일링 함수
    def get_recommendations(self, user_hsv, target_style, target_type='coordinate', limit=5):
        """
        사용자의 옷 색상 (HSV)과 원하는 스타일에 맞는 최적의 코디 아이템을 유사도 순으로 정렬하여 추천합니다.
        """
        user_h, user_s, user_v = user_hsv
        
        # 1. 사용자의 옷이 무채색인지, 유채색인지 판단 (기준 채도 0.15 활용)
        # S (채도)가 0.15 미만이면 무채색(True)
        user_is_neutral = 1 if user_s < 0.15 else 0
        
        # 2. 패션 규칙 기반 가중치 쿼리 작성
        # 거리가 '낮을수록' 우선순위가 높습니다. (0에 가까울수록 베스트)
        # 그러므로 추천하고 싶은 조건의 데이터는 거리를 깎아줍니다. (디스카운트 효과)        
        sql_query = """
            SELECT id, product_name, style, image_type, image_path, is_neutral,
                   hsv_dist(?, ?, ?, h, s, v) AS distance,

                   CASE 
                       -- 조건 A: 사용자의 옷이 무채색(1)인데, 추천 코디가 유채색(0)인 경우
                       -- 다양한 색감 제안을 위해 거리에 0.6을 곱해 순위를 높임 (인센티브)
                       WHEN ? = 1 AND is_neutral = 0 THEN hsv_dist(?, ?, ?, h, s, v) * 0.6
                       
                       -- 조건 B: 사용자의 옷이 유채색(0)인데, 추천 코디가 무채색(1)인 경우
                       -- 안정적인 톤 밸런스를 위해 거리에 0.7을 곱해 순위를 높임 (인센티브)
                       WHEN ? = 0 AND is_neutral = 1 THEN hsv_dist(?, ?, ?, h, s, v) * 0.7
                       
                       -- 그 외의 경우 (기본 색상 유사도 거리 유지)
                       ELSE hsv_dist(?, ?, ?, h, s, v)
                   END AS final_score
                   
            FROM clothes
            WHERE style = ?
            AND image_type = ?
            AND product_name NOT LIKE 'proc_%'
            AND image_path NOT LIKE '%proc_proc_%'
            ORDER BY final_score ASC
            LIMIT ?
        """

        # 쿼리에 들어갈 파라미터 매핑
        params = (
            user_h, user_s, user_v,  # raw_distance 계산용
            user_is_neutral,  # 조건 A 판단용
            user_h, user_s, user_v,  # 조건 A 거리 보정용
            user_is_neutral,  # 조건 B 판단용
            user_h, user_s, user_v,  # 조건 B 거리 보정용
            user_h, user_s, user_v,  # ELSE 기본 거리용
            target_style, target_type, limit
        )
        
        self.cur.execute(sql_query, params)
        return self.cur.fetchall()

    def close(self):
        self.conn.close()


# 추천 로직 실행 테스트
if __name__ == "__main__":
    print("가중치 로직이 탑재된 정밀 패션 추천 알고리즘을 가동합니다...")
    
    engine = FashionRecommendationEngine('fashion.db')
    
    # 사용자가 입력한 옷의 분석 결과
    # 테스트용 사용자의 옷 HSV 설정 (예: 카키/올리브 브라운 계열의 소수점 HSV 값)
    # 실제 구동 시에는 사용자가 올린 사진을 process_clothing_image에 넣고 나온 ["h"], ["s"], ["v"]를 그대로 투입
    user_uploaded_hsv = (0.08, 0.33, 0.41)
    requested_style = "workwear"  # 사용자가 원하는 스타일 (예: 워크웨어)
    requested_type = "coordinate"  # 코디 컷 위주로 추천받기

    print(f"사용자 선택 색상 HSV{user_uploaded_hsv} 기반으로 '{requested_style}' 코디 추천 중...\n")
    
    try:
        results = engine.get_recommendations(
            user_hsv=user_uploaded_hsv,
            target_style=requested_style,
            target_type=requested_type,
            limit=5
        )
        
        print(f"===== 사용자의 {requested_style} 스타일 코디 추천 결과 (상위 5개) =====")
        if not results:
            print("조건에 맞는 코디 아이템이 DB에 없거나 테이블 구조를 확인해야 합니다.")
        else:
            for i, row in enumerate(results, 1):
                img_id, name, style, img_type, path, is_neutral, raw_dist, final_score = row
                neutral_text = "무채색 코디" if is_neutral == 1 else "유채색 코디"
                print(f"{i}위. {name} ({neutral_text})")
                print(f"   - 기본색상거리: {raw_dist:.4f} ➔ 가중치최종점수: {final_score:.4f}")
                print(f"   - 추천 코디 이미지 경로: {path}")
                print(f"   - 분류: {style} / {img_type}")
                print("-" * 60)
                
    except sqlite3.OperationalError as e:
        print("\n데이터베이스 실행 에러 발생: {e}")
        
    finally:
        engine.close()
