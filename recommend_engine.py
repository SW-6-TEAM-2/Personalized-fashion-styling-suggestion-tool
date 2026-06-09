import sqlite3
import math

# 두 HSV 색상 간의 원통형 좌표계 유클리드 거리 계산 함수
def calculate_hsv_distance(h1, s1, v1, h2, s2, v2):
    """
    3차원 HSV 원통형 좌표계 (Cylindrical Space)상에서 두 색상 사이의 수학적 (유클리드) 거리를 계산합니다.
    각 축의 입력값 범위는 0.0 ~ 1.0입니다.
    단일 축의 단순 차이가 아니라 원통형 공간 내 대각선 최단 거리를 구하므로,
    계산 결과는 최대 sqrt(2)[~1.414]까지 나타날 수 있습니다.
    (엔진에서 호출 시 아우터-상의, 상의-하의 거리가 합산되므로 종합 거리는 1.0을 초과할 수 있습니다.)
    
    Returns:
        float: 0에 가까울수록 두 색상이 시각적으로 유사함을 의미하는 거리 값
    """

    # [안전장치] DB 내에 HSV 값이 누락된 (NULL/None) 불량 데이터가 있을 경우,
    # 파이썬 TypeError 크래시를 방지하고 추천 순위 최하위로 밀어내기 위해 999.0 (페널티)을 반환
    if h1 is None or s1 is None or v1 is None or h2 is None or s2 is None or v2 is None:
        return 999.0
    
    # 색상 (Hue)은 0.0 (0도)과 1.0 (360도)이 맞물리는 원형 구조라는 특성을 반영하기 위해
    # 각도 (Radians)로 변환 후 채도 (Saturation)를 반지름으로 삼아
    # X, Y 평면 좌표로 사영 (Projection)하여 정밀한 원통형 공간 거리를 산출
    # 더 단순하게는 일반 유클리드로도 가능하지만, 원형 특성을 반영하면 훨씬 정밀해짐
    theta1 = h1 * 2 * math.pi
    theta2 = h2 * 2 * math.pi
    
    # 원통형 좌표계 (Cylindrical coordinates) X, Y 요소 변환
    x1, y1 = s1 * math.cos(theta1), s1 * math.sin(theta1)
    x2, y2 = s2 * math.cos(theta2), s2 * math.sin(theta2)

    # 명도 (Value)를 Z축으로 두고 최종 3차원 유클리드 거리 계산
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (v1 - v2)**2)


# 데이터베이스 연결 및 100% 개인화된 옷장 기반 코디 세트 추천 엔진 클래스
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
    def get_stylized_recommendations(self, user_cloth_id, user_item_category, user_gender, current_temp, target_style, applicable_styles, limit=5):
        """
        사용자가 업로드한 아이템 ID를 고정하고, 사용자의 개인 옷장 (user_clothes) 서랍들을 스스로 조합 (Self-Join)하여 가중치 기반의 최적의 OOTD 세트 5개를 추천합니다.
        """

        # 1. 날씨 API 기반 계절 실시간 파싱
        season_filter = self._convert_temperature_to_season(current_temp)      

        # 2. 허용할 스타일 목록을 동적으로 구성
        # 사용자가 선택한 target_style과 CLIP이 분석한 applicable_styles를 합치고 중복을 제거
        # 예: target_style = "workwear" + applicable_styles = ["workwear", "casual"] -> ['workwear', 'casual']
        allowed_styles = list(set([target_style] + applicable_styles))
        
        # SQL의 IN 절에 동적으로 맵핑한 물음표 바인딩 구문 생성
        style_in_clause = ", ".join(["?"] * len(allowed_styles))

        # CLㅣP 스타일 일치 플래그 판정 및 매칭 상태 파악 (1: 일치 / 0: 미스매치)
        is_style_matched = 1 if target_style in applicable_styles else 0
        
        # 3. 100% 개인화된 옷장 자가 매칭 크로스 밸런싱 SQL 쿼리
        # 내 옷장 내부의 아우터, 상의, 하의, 신발을 전부 매칭시켜서 완벽한 코디 세트를 연산
        sql_query_formatted = """
            SELECT 
                u_out.id AS outer_id, u_out.product_name AS outer_name, u_out.style AS outer_style,
                u_top.id AS top_id, u_top.product_name AS top_name, u_top.style AS top_style,
                u_bot.id AS bottom_id, u_bot.product_name AS bottom_name, u_bot.style AS bottom_style,
                u_sho.id AS shoes_id, u_sho.product_name AS shoes_name, u_sho.style AS shoes_style,
                
                -- [색상 조화도 기준 점수] 아우터-상의 거리 + 상의-하의 거리를 합산
                (hsv_dist(u_out.h, u_out.s, u_out.v, u_top.h, u_top.s, u_top.v) +
                 hsv_dist(u_top.h, u_top.s, u_top.v, u_bot.h, u_bot.s, u_bot.v)) AS raw_color_dist,
                 
                -- [최종 가중치 밸런스 스코어 계산] (낮을수록 최적 조합)
                (
                    (hsv_dist(u_out.h, u_out.s, u_out.v, u_top.h, u_top.s, u_top.v) +
                     hsv_dist(u_top.h, u_top.s, u_top.v, u_bot.h, u_bot.s, u_bot.v))
                    
                    -- 가중치 1단계: 매칭된 상의/하의/신발이 사용자가 원하는 타겟 스타일 (예: 워크웨어)과 맞으면 점수 우대 (0.7배)
                    * CASE WHEN u_top.style = ? THEN 0.7 ELSE 1.0 END
                    * CASE WHEN u_bot.style = ? THEN 0.7 ELSE 1.0 END
                    * CASE WHEN u_sho.style = ? THEN 0.8 ELSE 1.0 END
                    
                    -- 가중치 2단계: 유채색과 무채색 단품 간의 조화도 밸런스 인센티브 (톤온톤 구원 가중치)
                    * CASE WHEN u_top.is_neutral = 1 AND u_bot.is_neutral = 0 THEN 0.85 ELSE 1.0 END
                    * CASE WHEN u_top.is_neutral = 0 AND u_bot.is_neutral = 1 THEN 0.85 ELSE 1.0 END

                    -- 가중치 3단계 (하의-신발): 전체 룩이 과해지지 않도록 하의와 신발의 유·무채색 크로스 매칭 보정
                    -- 하의가 튀는 유채색일 때 신발이 무채색이거나, 하의가 무채색일 때 신발에 색감 포인트
                    * CASE WHEN u_bot.is_neutral = 0 AND u_sho.is_neutral = 1 THEN 0.90 ELSE 1.0 END
                    * CASE WHEN u_bot.is_neutral = 1 AND u_sho.is_neutral = 0 THEN 0.95 ELSE 1.0 END  
                ) AS final_score

            FROM user_clothes u_out
            JOIN user_clothes u_top ON u_top.category = 'top'
            JOIN user_clothes u_bot ON u_bot.category = 'bottom'
            JOIN user_clothes u_sho ON u_sho.category = 'shoes'
            
            -- 사용자가 선택해서 진입한 '기준 단품 옷'의 ID로 대상을 타겟팅하여 고정
            WHERE u_out.id = ?
              AND u_top.style IN ({0})
              AND u_bot.style IN ({0})
              AND u_sho.style IN ({0})
            ORDER BY final_score ASC
            LIMIT ?
        """.format(style_in_clause)

        # SQL 파라미터 리스트 작성 (순서 엄격 주의)
        params = [
            # 가중치 1단계용 변수 맵핑
            target_style, target_style, target_style,
            # WHERE 기준 조건 소스 고정
            user_cloth_id
        ]
        
        # 동적 IN 절의 ? 개수만큼 스타일 리스트를 상의, 하의, 신발 자리에 각각 더해줌
        params.extend(allowed_styles)  # u_top.style IN
        params.extend(allowed_styles)  # u_bot.style IN
        params.extend(allowed_styles)  # u_sho.style IN
        
        # LIMIT 필터
        params.append(limit)
        
        # 최종적으로 튜플로 변환하여 execute에 주입
        refined_params = tuple(params)
        self.cur.execute(sql_query_formatted, refined_params)
        return self.cur.fetchall(), season_filter

    def close(self):
        self.conn.close()

# 백엔드 서버 엔드포인트 연동 가상 시뮬레이션
if __name__ == "__main__":
    print("=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
    print(" 100% 개인화된 옷장 아이템 자체 조합 정밀 추천 엔진 가동 ")
    print("=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=\n")
    
    engine = AdvancedFashionRecommendationEngine('fashion.db')
    
    # [시뮬레이션 상황 가이드]
    # 프론트엔드 navigator.geolocation -> Open-Meteo를 거쳐 백엔드로 전달된 기온 데이터가 14.5도인 상황
    # 사용자는 남성 (man), 카키 브라운 자켓 (1번 옷, 아우터, 유채색 단품)을 업로드하고 '워크웨어' 스타일 추천을 요청함

    mock_user_cloth_id = 1 # 옷장에서 1번 카키 브라운 자켓 단품을 선택했다고 가정
    mock_front_weather_temp = 14.5  # 가을 날씨 판정 예상
    mock_user_gender = "man"
    mock_user_uploaded_category = "outer"
    mock_user_target_style = "workwear" 
    
    # 팀원의 CLIP 모듈 (style_classifier.py) 결과값 연동
    # 이미지 분석 결과 워크웨어와 캐주얼 성향을 동시에 지닌 자켓으로 판명됨
    clip_analysis_result = {
        "top_style": "워크웨어",
        "applicable_styles": ["workwear", "casual"],  # CLIP이 연동해준 스타일 무드
        "is_confident": True
    }
    
    print(f"[프론트엔드 전송 수신 데이터]")
    print(f" - 사용자가 선택한 옷 ID (Target Cloth ID): {mock_user_cloth_id}")
    print(f" - 현재 기온: {mock_front_weather_temp}°C | 선택 성별: {mock_user_gender}")
    print(f" - 유저 타겟 스타일 선호: {mock_user_target_style}")
    print(f" - CLIP 단품 매칭 분석 계열: {clip_analysis_result['applicable_styles']}\n")
    
    try:
        recommendations, calculated_season = engine.get_stylized_recommendations(
            user_cloth_id=mock_user_cloth_id,
            user_item_category=mock_user_uploaded_category,
            user_gender=mock_user_gender,
            current_temp=mock_front_weather_temp,
            target_style=mock_user_target_style,
            applicable_styles=clip_analysis_result["applicable_styles"],
            limit=5
        )
        
        print(f"[날씨 계절 변환 완료]: 현재 기온 {mock_front_weather_temp}°C는 패션 스펙상 '{calculated_season}' 계절에 대응됩니다.")
        print(f"[내 옷장 내부 아이템 최적 가중치 연산 기반 추천 Top 5 코디 결과 리스트]")
        print("-" * 85)
        
        if not recommendations:
            print("조건에 맞는 옷장 내 조합을 만들 수 없습니다. 옷장에 상의 (top), 하의 (bottom), 신발 (shoes)을 더 등록해 주세요!")
        else:
            for i, item in enumerate(recommendations, 1):
                # 쿼리 SELECT 구조 파싱
                out_id, out_name, out_style, top_id, top_name, top_style, bot_id, bot_name, bot_style, sho_id, sho_name, sho_style, raw_dist, final_score = item

                # 페널티 기반 스코어를 0~100점 만점의 '코디 매칭 적합도 (%)'로 변환
                # final_score가 0에 가까울수록 100점에 수렴하고, 이 값이 커질수록 점수가 깎임
                # 변환 공식: max(0, (2.0 - final_score) / 2.0 * 100) -> 2.0 이상으로 커지면 0점 처리
                match_percentage = max(0.0, (2.0 - final_score) / 2.0 * 100)
                
                print(f"    {i}순위 추천 OOTD 세트 (최종 코디 매칭 적합도: {match_percentage:.1f}%)")
                print(f"  ├─ 아우터 (기준): {out_name} [{out_style}]")
                print(f"  ├─ 매칭 상의: {top_name} [{top_style}]")
                print(f"  ├─ 매칭 하의: {bot_name} [{bot_style}]")
                print(f"  └─ 매칭 신발: {sho_name} [{sho_style}]")
                print(f"    종합 누적 HSV 색상 유클리드 거리: {raw_dist:.4f} | 내부 페널티 스코어: {final_score:.4f}")
                print("-" * 85)
                
    except sqlite3.OperationalError as e:
        print(f"\n[오류] 데이터베이스 조회 및 연산 실패. 테이블 데이터와 필드명을 확인하세요: {e}")
    finally:
        engine.close()
