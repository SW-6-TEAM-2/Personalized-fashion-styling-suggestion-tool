import sqlite3
import math

# 두 HSV 색상 간의 유클리드 거리 계산 함수
def calculate_hsv_distance(h1, s1, v1, h2, s2, v2):
    """
    3차원 HSV 원통형 좌표계에서 두 색상 사이의 수학적 (유클리드) 거리를 계산합니다.
    값은 모두 0.0 ~ 1.0 사이의 소수점이고, 이 값이 0에 가까울수록 두 색상이 서로 유사함을 의미합니다.
    """
    # 색상 (Hue)은 원형 (0~360도) 구조이므로, 0.0과 1.0이 만나는 특성을 고려해 각도로 변환 후 원통형 좌표계 거리 계산
    # 더 단순하게는 일반 유클리드로도 가능하지만, 원형 특성을 반영하면 훨씬 정밀해짐
    theta1 = h1 * 2 * math.pi
    theta2 = h2 * 2 * math.pi
    
    # 원통형 좌표계 (Cylindrical coordinates) 변환 후 거리 계산
    x1, y1 = s1 * math.cos(theta1), s1 * math.sin(theta1)
    x2, y2 = s2 * math.cos(theta2), s2 * math.sin(theta2)
    
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (v1 - v2)**2)


# 데이터베이스 연결 및 추천 엔진 클래스
class AdvancedFashionRecommendationEngine:
    def __init__(self, db_path='fashion.db'):
        self.conn = sqlite3.connect(db_path)
        # SQLite 내부 쿼리문 안에서 고속 연산이 가능하도록 파이썬의 거리 계산 함수 등록
        self.conn.create_function("hsv_dist", 6, calculate_hsv_distance)
        self.cur = self.conn.cursor()

    def _convert_temperature_to_season(self, temp):
        """Open-Meteo의 기온 데이터를 기반으로 학술적 기온별 계절을 판정합니다."""
        if temp >= 23.0:
            return "summer"
        elif temp >= 15.0:
            return "spring"
        elif temp >= 6.0:
            return "fall"
        else:
            return "winter"
        
    # 패션 가중치 로직이 적용된 정밀 스타일링 함수
    def get_stylized_recommendations(self, user_hsv, user_item_category, user_gender, current_temp, target_style, applicable_styles, limit=5):
        """
        성별, 기온 (계절), 타겟 스타일, 사용자가 올린 단품의 CLIP 분석 스타일 배열을 모두 고려하여
        최적의 매칭 코디 세트 (set) 및 단품을 정밀 추천합니다.
        """
        user_h, user_s, user_v = user_hsv
        
        # 1. 사용자의 옷이 무채색인지, 유채색인지 판단 (기준 채도 0.15 활용)
        # S (채도)가 0.15 미만이면 무채색 (True)
        user_is_neutral = 1 if user_s < 0.15 else 0

        # 2. 날씨 API 기반 계절 실시간 파싱
        season_filter = self._convert_temperature_to_season(current_temp)
        
        # 3. CLIP이 분석한 활용 가능 스타일 배열을 SQL IN 연산용 쿼리로 바인딩 준비
        # 입력 예시: ["워크웨어", "캐주얼"] -> 쿼리 내부 가중치 연산에 활용
        is_user_item_style_matched = 1 if target_style in applicable_styles else 0
        
        # 4. 고도화된 패션 규칙 기반 가중치 쿼리
        # 점수가 '낮을수록' 오히려 우선순위가 높아지게 구성 (0에 수렴할수록 최상위 추천 순위에 등극)
        # 따라서, 추천하고 싶은 조건의 데이터는 거리를 깎아줌 (discount 효과)
        sql_query = """
            SELECT id, product_name, style, category, gender, season, image_type, image_path, is_neutral,
                   hsv_dist(?, ?, ?, h, s, v) AS raw_color_dist,
                   
                   CASE 
                       -- 규칙 1: 사용자가 선택한 '타겟 스타일'과 코디 데이터의 스타일이 일치하면 강한 benefit (0.5배 디스카운트)
                       WHEN style = ? THEN hsv_dist(?, ?, ?, h, s, v) * 0.5
                       
                       -- 규칙 2: 스타일 매칭이 살짝 빗나가더라도, 사용자가 올린 옷의 CLIP 활용 계열 (applicable)에 속한다면 차선책 benefit (0.7배)
                       WHEN style IN ({0}) THEN hsv_dist(?, ?, ?, h, s, v) * 0.7
                       
                       -- 규칙 3: 톤온톤/톤인톤 밸런스 (유채색-무채색 교차 인센티브)
                       WHEN ? = 1 AND is_neutral = 0 THEN hsv_dist(?, ?, ?, h, s, v) * 0.75
                       WHEN ? = 0 AND is_neutral = 1 THEN hsv_dist(?, ?, ?, h, s, v) * 0.80
                       
                       ELSE hsv_dist(?, ?, ?, h, s, v)
                   END AS final_score
                   
            FROM clothes
            WHERE gender = ? 
              AND (season = ? OR season = 'all')  -- 신발 ('all') 및 해당 계절 의류 통합 필터링
              AND image_type = 'set'             -- 최종 추천 결과물은 완성형 코디 세트 룩북으로 구성
              AND category = 'set'
              AND product_name NOT LIKE 'proc_%'
              AND image_path NOT LIKE '%proc_proc_%'
            ORDER BY final_score ASC
            LIMIT ?
        """.format(', '.join(['?'] * len(applicable_styles)))  # 가변인자 스타일 배열 동적 바인딩

        # 5. 쿼리 파라미터 정밀 매핑 (순서 엄격 유지)
        params = [
            user_h, user_s, user_v,  # raw_color_dist용
            target_style, user_h, user_s, user_v,  # 규칙 1
        ]
        # 규칙 2: 동적 스타일 리스트 파라미터 주입
        for _ in applicable_styles:
            params.append(user_h)
            params.append(user_s)
            params.append(user_v)
        
        # 규칙 3 및 기본 필터 파라미터 추가
        params.extend([
            user_is_neutral, user_h, user_s, user_v,
            user_is_neutral, user_h, user_s, user_v,
            user_gender, season_filter, limit
        ])

        # 허용할 스타일 목록을 동적으로 구성
        # 사용자가 선택한 target_style과 CLIP이 분석한 applicable_styles를 합치고 중복을 제거
        # 예: target_style = "workwear" + applicable_styles = ["workwear", "casual"] -> ['workwear', 'casual']
        allowed_styles = list(set([target_style] + applicable_styles))
        
        # SQL의 IN (?, ?) 구문에 들어갈 물음표 개수를 스타일 개수만큼 동적으로 생성
        style_in_clause = ", ".join(["?"] * len(allowed_styles))
        
        # 실제 데이터베이스 조회 시 생성된 placeholder에 스타일 배열 리스트를 대입하기 위한 처리
        # ?, ?, ? 개수를 맞추기 위해 파라미터 리스트 구조 재조정
        sql_query_formatted = """
            SELECT id, product_name, style, category, gender, season, image_type, image_path, is_neutral,
                   hsv_dist(?, ?, ?, h, s, v) AS raw_color_dist,
                   
                   -- [최종 스코어 연산]
                   hsv_dist(?, ?, ?, h, s, v) 
                   * -- 1단계: 사용자가 선택한 타겟 스타일 순위 반영 (맞으면 0.5배로 대폭 우대, 틀리면 1.0배 유지)
                   CASE WHEN style = ? THEN 0.5 ELSE 1.0 END
                   *
                   -- 2단계: 이미지 CLIP 분석 결과와의 스타일 조화도 반영 (맞으면 0.8배 우대)
                   CASE WHEN ? = 1 AND style = ? THEN 0.8 ELSE 1.0 END
                   *
                   -- 3단계: 단품 무드 역주행 (미스매치) 시 색상/톤 밸런스 구원 가중치
                   -- 스타일이 안 맞더라도 톤 조합이 기가 막히면 점수를 보정 (0.7~0.8)
                   CASE 
                       WHEN ? = 0 AND ? = 1 AND is_neutral = 0 THEN 0.7  -- 스타일은 불일치인데 유채단품-무채코디 밸런스 (보정 효과)
                       WHEN ? = 0 AND ? = 0 AND is_neutral = 1 THEN 0.8  -- 스타일은 불일치인데 무채단품-유채코디 밸런스 (보정 효과)
                       WHEN ? = 1 AND ? = 1 AND is_neutral = 0 THEN 0.9            -- 스타일도 일치하고 유채단품-무채코디 밸런스 (시너지 효과)
                       WHEN ? = 1 AND ? = 0 AND is_neutral = 1 THEN 0.95           -- 스타일도 일치하고 무채단품-유채코디 밸런스 (시너지 효과)
                       ELSE 1.0
                   END AS final_score
            FROM clothes
            WHERE gender = ? 
              AND (season = ? OR season = 'all')
              AND style IN ({0})
              AND image_type IN ('set', 'coordinate')
              AND product_name NOT LIKE 'proc_%'
              AND image_path NOT LIKE '%proc_proc_%'
            ORDER BY final_score ASC
            LIMIT ?
        """.format(style_in_clause)
        
        # 스타일 일치 플래그 및 매칭 상태 파악 (1: 일치 / 0: 미스매치)
        is_style_matched = 1 if target_style in applicable_styles else 0

        params = [
            # raw_color_dist (3개)
            user_h, user_s, user_v,
            # final_score 계산용 hsv_dist (3개)
            user_h, user_s, user_v,
            # 1단계 (1개)
            target_style,
            # 2단계 (2개)
            is_style_matched, target_style,
            # 3단계 상황별 톤 밸런스 플래그 연동 (8개)
            is_style_matched, user_is_neutral,
            is_style_matched, user_is_neutral,
            is_style_matched, user_is_neutral,
            is_style_matched, user_is_neutral,
            # WHERE 절 기본 필터 (2개)
            user_gender, season_filter
        ]
        
        # WHERE 절의 style IN (?, ?) 자리에 allowed_styles 목록을 순서대로 추가
        params.extend(allowed_styles)
        
        # LIMIT 필터 (1개)
        params.append(limit)
        
        # 최종적으로 튜플로 변환하여 execute에 주입
        refined_params = tuple(params)
        
        self.cur.execute(sql_query_formatted, refined_params)
        return self.cur.fetchall(), season_filter

    def close(self):
        self.conn.close()

# 백엔드 서버 엔드포인트 연동 가상 시뮬레이션
if __name__ == "__main__":
    print("=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
    print(" 기온·성별·CLIP 멀티태깅 연동형 정밀 추천 엔진 가동 ")
    print("=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=\n")
    
    engine = AdvancedFashionRecommendationEngine('fashion.db')
    
    # [상황 가이드]
    # 프론트엔드 navigator.geolocation -> Open-Meteo를 거쳐 백엔드로 전달된 기온 데이터가 14.5도인 상황
    # 사용자는 남성 (man), 카키 브라운 자켓 (유채색 단품)을 업로드하고 '워크웨어' 스타일 추천을 클릭함
    
    mock_front_weather_temp = 14.5  # 가을 날씨 판정 예상
    mock_user_gender = "man"
    mock_user_uploaded_category = "top"
    mock_user_target_style = "workwear"
    
    # 사용자가 올린 자켓 이미지 색상 정밀 추출 값 (HSV)
    user_item_hsv = (0.08, 0.35, 0.45) 
    
    # 팀원의 CLIP 모듈 (style_classifier.py) 결과값 연동
    # 이미지 분석 결과 워크웨어와 캐주얼 성향을 동시에 지닌 자켓으로 판명됨
    clip_analysis_result = {
        "top_style": "워크웨어",
        "applicable_styles": ["workwear", "casual"],  # 내부 매핑용 영어 키워드 변환
        "is_confident": True
    }
    
    print(f"[프론트엔드 전송 수신 데이터]")
    print(f" - 현재 기온: {mock_front_weather_temp}°C | 선택 성별: {mock_user_gender}")
    print(f" - 유저 타겟 스타일 선호: {mock_user_target_style}")
    print(f" - CLIP 단품 매칭 분석 계열: {clip_analysis_result['applicable_styles']}\n")
    
    try:
        recommendations, calculated_season = engine.get_stylized_recommendations(
            user_hsv=user_item_hsv,
            user_item_category=mock_user_uploaded_category,
            user_gender=mock_user_gender,
            current_temp=mock_front_weather_temp,
            target_style=mock_user_target_style,
            applicable_styles=clip_analysis_result["applicable_styles"],
            limit=5
        )
        
        print(f"[날씨 계절 변환 완료]: 현재 기온 {mock_front_weather_temp}°C는 패션 스펙상 '{calculated_season}' 계절에 대응됩니다.")
        print(f"[종합 알고리즘 가중치 연산 기반 추천 Top 5 코디 세트 결과]")
        print("-" * 75)
        
        if not recommendations:
            print("현재 필터 조건 (성별/계절/스타일)에 맞는 코디 세트가 DB에 존재하지 않습니다.")
        else:
            for i, item in enumerate(recommendations, 1):
                img_id, name, style, cat, gender, season, img_type, path, is_neutral, raw_dist, final_score = item
                color_type = "무채색 기반" if is_neutral == 1 else "유채색 중심"
                
                print(f"  {i}순위 매칭 추천 코디")
                print(f"   - 상품명: {name}")
                print(f"   - 스타일 레이블: {style} ({color_type})")
                print(f"   - 타겟 매칭 스펙: 성별 [{gender}] | 계절 [{season}]")
                print(f"   - 이미지 룩북 경로: {path}")
                print(f"   - [알고리즘 스코어] 색상 순수 거리: {raw_dist:.4f} -> 가중치 반영 최종 매칭 점수: {final_score:.4f}")
                print("-" * 75)
                
    except sqlite3.OperationalError as e:
        print(f"\n[오류] 데이터베이스 조회 실패. 테이블 구조나 필드명을 확인하세요: {e}")
    finally:
        engine.close()
