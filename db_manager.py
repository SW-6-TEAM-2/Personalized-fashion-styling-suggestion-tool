import sqlite3

class FashionDBManager:
    def __init__(self, db_path="fashion.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 무신사 크롤링 데이터용 테이블 (참조용 코디 룩북 가이드라인)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clothes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT, style TEXT, category TEXT, gender TEXT, 
                    season TEXT, image_type TEXT, image_path TEXT, is_neutral INTEGER,
                    h REAL, s REAL, v REAL
                )
            """)
            # 사용자 옷장 테이블 (연동)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_clothes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT DEFAULT 'current_user',
                    product_name TEXT,
                    category TEXT,
                    style TEXT,
                    h REAL, s REAL, v REAL,
                    is_neutral INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_user_cloth(self, product_name, category, style, h, s, v):
        """test_style_classifier.py"""

        # 사용자의 옷이 무채색인지, 유채색인지 판단 (기준 채도 0.15 활용)
        # S (채도)가 0.15 미만이면 무채색 (1), 이상이면 유채색 (0)으로 자동 분류
        is_neutral = 1 if s < 0.15 else 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_clothes (product_name, category, style, h, s, v, is_neutral)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product_name, category, style, h, s, v, is_neutral))
            conn.commit()
            # 프론트엔드나 추천 엔진으로 즉시 넘겨줄 수 있도록 방금 저장된 옷의 고유 ID (PK)를 반환
            return cursor.lastrowid

    def get_user_cloth_by_id(self, cloth_id):
        """저장된 사용자 옷 정보를 검증하거나 디버깅할 때 사용할 수 있는 단건 조회 함수"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_clothes WHERE id = ?", (cloth_id,))
            return cursor.fetchone()
