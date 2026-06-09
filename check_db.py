import sqlite3
from db_manager import FashionDBManager

print("=== 1. 테이블 존재 여부 및 구조 초기화 ===")
with sqlite3.connect("fashion.db") as conn:
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS user_clothes;")
    conn.commit()
    print("구버전 user_clothes 테이블이 존재했다면 강제 리셋 완료.")
    
    # SQLite 내부의 모든 테이블 목록 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("현재 DB에 존재하는 테이블 목록:", [t[0] for t in tables])

# DB 매니저를 가동하여 테이블이 없다면 자동으로 최신 구조의 테이블을 생성
db_manager = FashionDBManager("fashion.db")

print("\n=== 2. 사용자 옷장 데이터 클리닝 및 테스트 데이터 세팅 ===")
with sqlite3.connect("fashion.db") as conn:
    cursor = conn.cursor()
    try:
        # 시뮬레이션을 정상적으로 돌리기 위해 기존 사용자 옷장 데이터를 깔끔하게 삭제
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='user_clothes';")
        conn.commit()
        print("기존 테스트용 사용자 옷장 데이터 (ID)를 초기화했습니다.")
        
        # 상의, 하의, 아우터, 신발이 서랍에 모두 존재해야 조합이 가능
        # 사용자가 업로드하는 시나리오를 가정한 가을/워크웨어 기반의 옷장 세팅
        test_items = [
            # 1번 옷: 사용자가 방금 업로드한 "타겟 아우터" (ID: 1번이 됨)
            {"name": "카키 브라운 워크 자켓", "cat": "outer", "style": "workwear", "h": 0.08, "s": 0.35, "v": 0.45},
            
            # 상의 서랍 (top)
            {"name": "아이보리 오버핏 맨투맨", "cat": "top", "style": "casual", "h": 0.12, "s": 0.10, "v": 0.90},
            {"name": "데님 워크 셔츠", "cat": "top", "style": "workwear", "h": 0.60, "s": 0.40, "v": 0.50},
            
            # 하의 서랍 (bottom)
            {"name": "셀비지 생지 데님 팬츠", "cat": "bottom", "style": "workwear", "h": 0.65, "s": 0.50, "v": 0.30},
            {"name": "와이드 차콜 치노 팬츠", "cat": "bottom", "style": "casual", "h": 0.00, "s": 0.05, "v": 0.25},
            
            # 신발 서랍 (shoes)
            {"name": "팀버랜드 레더 워커", "cat": "shoes", "style": "workwear", "h": 0.07, "s": 0.55, "v": 0.40},
            {"name": "원스타 화이트 스니커즈", "cat": "shoes", "style": "casual", "h": 0.00, "s": 0.02, "v": 0.95}
        ]
        
        print("\n개인화 옷장에 카테고리별 아이템 주입 시작...")
        for item in test_items:
            # db_manager 스펙에 맞춰 product_name, category, style, h, s, v 순서로 정확히 바인딩
            new_id = db_manager.add_user_cloth(
                product_name=item["name"],
                category=item["cat"],
                style=item["style"],
                h=item["h"],
                s=item["s"],
                v=item["v"]
            )
            print(f" └─ [{item['cat'].upper()}] '{item['name']}' 등록 성공! (발급된 옷 ID: {new_id})")
            
        # 최종 개수 검증
        cursor.execute("SELECT COUNT(*) FROM user_clothes;")
        final_count = cursor.fetchone()[0]
        print(f"\n사용자 옷장 세팅 최종 완료! 현재 저장된 사용자 옷 개수: {final_count}개")
        print("이제 1번 아우터 (카키 자켓)를 기준으로 내 옷장 조합 추천을 수행할 준비가 끝났습니다.")
            
    except sqlite3.OperationalError as e:
        print(f"오류 발생 (테이블이 없을 확률이 높음): {e}")
