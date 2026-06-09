"""
패션 추천 엔진

스코어링 구조 (CLIP 전용):
  style(CLIP) 0.4 + color_harmony(HSV) 0.3 + clip_compat(CLIP) 0.3

fashion.db 의존성 제거 — CLIP 텍스트 프롬프트가 6개 스타일을 직접 처리하므로 불필요.
"""

import math
import random

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from clip_utils import cosine_style_score
    HAS_CLIP = True
except Exception:
    HAS_CLIP = False
    def cosine_style_score(emb, style): return None


class FashionRecommendationEngine:

    # ══════════════════════════════════════════════════════════════════════
    # 색상 조화도 (HSV 기반 — 낮을수록 좋음)
    # ══════════════════════════════════════════════════════════════════════
    def _calculate_outfit_harmony(self, items):
        """
        포인트 컬러 법칙 기반 색상 조화도 (낮을수록 좋음, 음수 = 보너스)

        규칙 1: 유채색 1개 + 나머지 무채색 → 강한 보너스 (포인트 컬러)
        규칙 2: 유채색 2개
            - 색상이 비슷 (hue_diff < 0.1) → 톤온톤, 소패널티만
            - 색상이 많이 다름             → 강한 패널티
            - 보색 충돌 (0.4~0.6)          → 매우 강한 패널티
        규칙 3: 유채색 3개 이상 → 개수에 비례해 강한 패널티
        규칙 4: 밝기(V) 차이 너무 크면 → 패널티
        """
        if len(items) <= 1:
            return 0.0

        vivid   = [i for i in items if not i['is_neutral']]
        neutral = [i for i in items if i['is_neutral']]
        score   = 0.0

        if len(vivid) == 0:
            pass  # 전부 무채색 → 중립

        elif len(vivid) == 1:
            score -= 0.5  # 포인트 컬러 법칙 — 보너스

        elif len(vivid) == 2:
            h1 = vivid[0]['h']
            h2 = vivid[1]['h']
            hue_diff = min(abs(h1 - h2), 1.0 - abs(h1 - h2))
            if hue_diff < 0.1:
                score += 0.1   # 톤온톤 → 허용
            elif 0.40 < hue_diff < 0.60:
                score += 0.7   # 보색 충돌 → 강한 패널티
            else:
                score += 0.4   # 다른 색 → 중간 패널티

        else:
            score += 0.6 * (len(vivid) - 1)  # 유채색 3개+ → 강한 패널티

        # ── 패턴 복잡도 규칙 ──────────────────────────────────────────────
        patterned = [i for i in items if i.get('isPatterned') or i.get('is_patterned')]

        if len(patterned) == 1:
            score -= 0.15  # 패턴 아이템 1개 → 포인트 아이템, 소보너스

        elif len(patterned) >= 2:
            # 패턴 아이템 여러 개 → 복잡해 보임, 패널티
            score += 0.5 * (len(patterned) - 1)

        # ── 아우터 + 상의 레이어링 규칙 ──────────────────────────────────
        outer = next((i for i in items if i.get('category') == '아우터'), None)
        top   = next((i for i in items if i.get('category') == '상의'), None)
        if outer and top:
            outer_complex = (not outer['is_neutral']) or bool(outer.get('isPatterned') or outer.get('is_patterned'))
            top_complex   = (not top['is_neutral'])   or bool(top.get('isPatterned')   or top.get('is_patterned'))

            if outer_complex and top_complex:
                h1 = outer['h']
                h2 = top['h']
                hue_diff = min(abs(h1 - h2), 1.0 - abs(h1 - h2))
                if hue_diff < 0.1:
                    score += 0.2   # 비슷한 색이라도 둘 다 복잡 → 소패널티
                else:
                    score += 1.0   # 서로 다른 복잡한 아이템 → 매우 강한 패널티
            elif outer_complex and not top_complex:
                score -= 0.3       # 아우터만 튐 + 상의 무채색 → 이상적

        # ── 밝기 차이 ─────────────────────────────────────────────────────
        v_values = [i['v'] for i in items]
        if max(v_values) - min(v_values) > 0.7:
            score += 0.2

        # ── 신발 배색(포인트컬러) 규칙 ────────────────────────────────────
        # 신발의 도미넌트 색이 아닌 2등 클러스터(배색)가 유채색일 때,
        # 나머지 옷과의 색 어울림을 별도로 평가한다.
        #
        # 감지 기준: sub_s > 0.35 (유채색 배색)  AND  sub_ratio > 0.15 (15% 이상 차지)
        # 판단:
        #   - 나머지 옷에 유채색 있음:
        #       hue 차이 < 0.12  → 배색이 옷과 어울림 → 보너스 -0.3
        #       hue 차이 0.25~0.65 → 배색이 튐       → 강한 패널티 +0.7
        #       그 외              → 그냥 안 맞음     → 패널티 +0.4
        #   - 나머지 옷이 전부 무채색:
        #       신발 배색이 유일한 포인트 → 이미 위의 vivid 1개 보너스로 처리, 추가 없음
        shoe = next((i for i in items if i.get('category') == '신발'), None)
        if shoe:
            sub_s_val     = shoe.get('sub_s')     or 0.0
            sub_ratio_val = shoe.get('sub_ratio') or 0.0
            sub_h_val     = shoe.get('sub_h')     or 0.0

            if sub_s_val > 0.35 and sub_ratio_val > 0.15:
                outfit_vivid_hues = [
                    i['h'] for i in items
                    if i is not shoe and not i['is_neutral']
                ]
                if outfit_vivid_hues:
                    min_diff = min(
                        min(abs(sub_h_val - oh), 1.0 - abs(sub_h_val - oh))
                        for oh in outfit_vivid_hues
                    )
                    if min_diff < 0.12:
                        score -= 0.3   # 배색이 옷 색상과 유사 → 잘 어울림
                    elif min_diff > 0.25:
                        score += 0.7   # 배색이 옷 색상과 충돌 → 강한 패널티

        return score

    # ══════════════════════════════════════════════════════════════════════
    # CLIP 아이템 간 시각적 호환성 (낮을수록 좋음)
    # ══════════════════════════════════════════════════════════════════════
    def _calculate_clip_compatibility(self, items):
        """
        아이템 간 CLIP 임베딩 코사인 유사도로 시각적 어울림 계산

        유사도 범위별 판단:
          0.85+       : 너무 비슷한 옷끼리 → 단조로움 패널티
          0.50 ~ 0.75 : 서로 다르지만 어울림 → 보너스 (이게 최적)
          0.50 미만   : 완전 다른 스타일 → 소패널티
        """
        if not HAS_NUMPY:
            return 0.0

        valid = [
            np.array(item['embedding'], dtype=np.float32)
            for item in items if item.get('embedding')
        ]

        if len(valid) < 2:
            return 0.0

        score = 0.0
        for i in range(len(valid)):
            for j in range(i + 1, len(valid)):
                sim = float(np.dot(valid[i], valid[j]))
                if sim > 0.85:
                    score += 0.3    # 너무 비슷 → 단조로움
                elif 0.50 <= sim <= 0.75:
                    score -= 0.2    # 적당히 다름 → 시각적으로 어울림
                else:
                    score += 0.1    # 너무 다름 → 소패널티

        return score

    # ══════════════════════════════════════════════════════════════════════
    # 스타일 스코어 (CLIP 전용)
    # ══════════════════════════════════════════════════════════════════════
    # 스타일별 "반대" 스타일 정의
    # 이 스타일이 선택됐을 때, 반대 스타일과 유사한 아이템에 페널티를 부여
    _CONTRAST_STYLE = {
        "minimal": "street",
        "classic": "street",
    }
    # 반대 스타일 유사도 임계값: 코사인 유사도가 이보다 높으면 패널티
    _CONTRAST_THRESHOLD = 0.28
    _CONTRAST_WEIGHT    = 3.5   # 패널티 강도 (높을수록 반대 스타일 아이템 강하게 제거)

    def _compute_style_score(self, item, target_styles):
        """
        CLIP으로 아이템과 선택된 스타일(들) 간 유사도 계산.

        target_styles: str 또는 list[str]
        여러 스타일이 주어지면 각 스타일 점수의 평균 반환.
        임베딩 없는 아이템은 중립값 1.0 반환.

        반대 스타일 패널티:
          미니멀/클래식 선택 시, 스트릿 유사도가 높은 아이템에 페널티 부여.
          cosine(item, street) > THRESHOLD 이면 초과분 × WEIGHT 만큼 점수 가산.
        """
        if isinstance(target_styles, str):
            target_styles = [target_styles]

        embedding = item.get('embedding')
        if not embedding:
            return 1.0  # 임베딩 없으면 중립 (순위에 영향 최소화)

        scores = [
            s for style in target_styles
            if (s := cosine_style_score(embedding, style)) is not None
        ]
        base = sum(scores) / len(scores) if scores else 1.0

        # ── 반대 스타일 패널티 ─────────────────────────────────────────────
        contrast_penalty = 0.0
        for ts in target_styles:
            opp = self._CONTRAST_STYLE.get(ts)
            if opp:
                opp_score = cosine_style_score(embedding, opp)
                if opp_score is not None:
                    # opp_score = 1 - cosine(item, opp_style)
                    # → cosine 유사도 = 1 - opp_score (높을수록 반대 스타일에 가까움)
                    street_sim = 1.0 - opp_score
                    if street_sim > self._CONTRAST_THRESHOLD:
                        contrast_penalty += (street_sim - self._CONTRAST_THRESHOLD) * self._CONTRAST_WEIGHT

        return base + contrast_penalty

    # ══════════════════════════════════════════════════════════════════════
    # 메인 추천 메서드
    # ══════════════════════════════════════════════════════════════════════
    def recommend_outfit_from_closet(self, category_items, target_style=None,
                                     candidates_per_cat=5, top_n=5):
        """
        사용자 옷장에서 최적의 코디 조합을 추천합니다.

        category_items : { '아우터': [...], '상의': [...], '하의': [...], '신발': [...] }
        target_style   : str 또는 list[str] — 선택한 스타일 키워드들

        1단계: 카테고리별로 스타일 스코어 상위 candidates_per_cat개 선정
        2단계: 모든 조합 점수화 후 상위 top_n개 pool에서 랜덤 선택
               → 매번 좋은 조합 중 다양하게 추천

        가중치: style×0.4 + harmony×0.3 + clip_compat×0.3
        """
        target_styles = (
            target_style if isinstance(target_style, list)
            else [target_style or "casual"]
        )

        # ── 1단계: 카테고리별 스타일 후보 추출 ──────────────────────────────
        category_candidates = {}

        for category, items in category_items.items():
            if not items:
                continue

            scored = []
            for item in items:
                style_score = self._compute_style_score(item, target_styles)
                # 동점 구간에서 다양성 확보용 소폭 노이즈 (±0.05)
                noise = random.uniform(-0.05, 0.05)
                scored.append({
                    **item,
                    'h':          item.get('h') or 0.0,
                    's':          item.get('s') or 0.0,
                    'v':          item.get('v') or 0.0,
                    'is_neutral': bool(item.get('isNeutral') or item.get('is_neutral', False)),
                    'style_score': style_score + noise,
                })

            # 카테고리 내 min-max 정규화
            # CLIP 유사도가 0.20~0.35로 몰려 있어 절대값 차이가 작음
            # 정규화하면 "이 카테고리에서 상대적으로 얼마나 잘 맞는가"로 변환 → 차별화 강화
            if len(scored) > 1:
                lo = min(i['style_score'] for i in scored)
                hi = max(i['style_score'] for i in scored)
                rng = hi - lo
                if rng > 1e-6:
                    for item in scored:
                        item['style_score'] = (item['style_score'] - lo) / rng
            scored.sort(key=lambda x: x['style_score'])
            category_candidates[category] = scored[:candidates_per_cat]

        if not category_candidates:
            return []

        # ── 2단계: 후보 조합 중 상위 N개 수집 후 랜덤 선택 ──────────────────
        from itertools import product as cart_product

        cats            = list(category_candidates.keys())
        candidate_lists = [category_candidates[c] for c in cats]

        all_combos = []
        for combo in cart_product(*candidate_lists):
            combo_list  = list(combo)
            style_scores = [i['style_score'] for i in combo_list]
            style_sum    = sum(style_scores)

            # 스타일 일관성 패널티: 아이템들의 스타일 점수 편차가 크면 페널티
            # (어떤 아이템은 키워드에 잘 맞고 어떤 건 안 맞으면 = 어색한 조합)
            style_spread = max(style_scores) - min(style_scores)
            style_coherence_penalty = style_spread * 0.4

            harmony     = self._calculate_outfit_harmony(combo_list)
            clip_compat = self._calculate_clip_compatibility(combo_list)

            total = (style_sum * 0.3
                     + style_coherence_penalty
                     + harmony * 0.35
                     + clip_compat * 0.35)
            all_combos.append((total, combo_list))

        all_combos.sort(key=lambda x: x[0])
        _, chosen = random.choice(all_combos[:top_n])
        return chosen

    def close(self):
        pass  # fashion.db 제거로 닫을 커넥션 없음
