"""
스타일 태깅 모듈 (CLIP zero-shot)

목적:
    사용자가 올린 단품 의류 사진 1장에 대해, 6개 스타일
    (workwear / casual / street / minimal / classic / cityboy)
    각각에 대한 유사도 점수를 매긴다.

중요 — 이 모듈은 "검증용"이다:
    단품 한 장으로 스타일을 단정하는 것은 본질적으로 한계가 있다
    (흰 셔츠는 minimal일 수도, classic일 수도, cityboy일 수도 있다).
    따라서 이 코드는 1등 라벨만 뱉지 않고 6개 전부의 점수와
    1·2등 격차(margin)를 함께 반환한다.

    판단 기준:
      - margin이 크다(예: 0.15+)  -> 스타일이 뚜렷함. 태그 신뢰 가능.
      - margin이 작다(예: 0.05-)  -> 스타일이 안 갈림. 추천 필터로 쓰면 위험.
    실제 옷 사진 여러 장을 test_style_classifier.py로 돌려보고,
    margin 분포를 본 뒤 "추천에 쓸지 / 참고 태그로만 둘지"를 결정한다.

의존성:
    pip install transformers torch pillow
    (모델 가중치는 최초 실행 시 자동 다운로드 — 약 600MB)
"""

import colorsys  # noqa: F401  (image_processor와의 일관성 위해 남겨둠. 미사용)
from functools import lru_cache

import numpy as np
from PIL import Image


# ── 스타일 정의 ───────────────────────────────────────────────
# 각 스타일을 여러 영어 프롬프트로 풀어쓴다 (prompt ensembling).
# CLIP은 단어 하나("workwear")보다 자연스러운 문장 여러 개의
# 평균 임베딩에 더 안정적으로 반응한다.
# 한글 라벨은 사용자에게 보여줄 표시용, 영어 프롬프트는 모델 입력용.
STYLE_PROMPTS = {
    "워크웨어": [
        "rugged workwear clothing",
        "a denim or canvas work jacket with utility pockets",
        "heavy-duty carpenter pants or coveralls",
        "functional utility workwear in earthy tones",
    ],
    "캐주얼": [
        "relaxed casual everyday clothing",
        "a plain t-shirt and jeans casual outfit",
        "comfortable laid-back daily wear",
        "simple ordinary casual clothes",
    ],
    "스트릿": [
        "streetwear clothing with bold graphics",
        "an oversized graphic hoodie or printed tee",
        "trendy urban street style with logos",
        "hip-hop inspired streetwear",
    ],
    "미니멀": [
        "minimalist clothing in plain solid color",
        "a clean simple garment with no pattern or logo",
        "understated monochrome minimal fashion",
        "sleek modern minimalist clothes",
    ],
    "클래식": [
        "classic formal tailored clothing",
        "a dress shirt, slacks or a blazer",
        "elegant business formalwear",
        "a refined tailored suit",
    ],
    "시티보이": [
        "clean japanese cityboy style clothing",
        "preppy neat clothes in light soft tones",
        "a tidy smart-casual coordinated outfit",
        "polished urban japanese casual wear",
    ],
}


# 사용 가능한 모델
#  - FashionCLIP: 패션 의류 이미지·캡션으로 특화 학습된 CLIP.
#    일반 CLIP보다 의류 스타일 구분에 유리할 것으로 기대.
#  - 일반 CLIP: 비교 기준(baseline). 결과 대조용.
FASHION_CLIP = "patrickjohncyh/fashion-clip"
GENERAL_CLIP = "openai/clip-vit-base-patch32"

DEFAULT_MODEL = FASHION_CLIP



def _as_tensor(out):
    """get_text_features / get_image_features 반환값을 텐서로 보정.

    transformers 버전에 따라 이 메서드들이 순수 텐서 대신
    pooler_output을 가진 출력 객체를 돌려주는 경우가 있어,
    어느 쪽이 와도 [batch, dim] 임베딩 텐서를 꺼내도록 한다.
    """
    import torch

    if isinstance(out, torch.Tensor):
        return out
    # 출력 객체인 경우: pooler_output이 임베딩에 해당
    for attr in ("pooler_output", "text_embeds", "image_embeds",
                 "last_hidden_state"):
        val = getattr(out, attr, None)
        if isinstance(val, torch.Tensor):
            # last_hidden_state는 [batch, seq, dim] → 평균 풀링으로 [batch, dim]
            return val.mean(dim=1) if val.dim() == 3 else val
    # 튜플 형태 폴백
    if isinstance(out, (tuple, list)) and isinstance(out[0], torch.Tensor):
        return out[0]
    raise TypeError(f"임베딩 텐서를 추출하지 못했습니다: {type(out)}")


@lru_cache(maxsize=1)
def _load_model(model_name=DEFAULT_MODEL):
    """CLIP 모델·프로세서 로드 (최초 1회만, 이후 캐시).

    GPU가 있으면 자동으로 사용, 없으면 CPU로 폴백한다.
    """
    import torch
    from transformers import CLIPModel, CLIPProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained(model_name).to(device)
    model.eval()
    processor = CLIPProcessor.from_pretrained(model_name)
    return model, processor, device


@lru_cache(maxsize=1)
def _build_text_features(model_name=DEFAULT_MODEL):
    """각 스타일의 텍스트 임베딩을 미리 계산해 둔다.

    스타일당 여러 프롬프트의 임베딩을 평균내 하나의 대표 벡터로
    만든 뒤 정규화한다. 이미지가 바뀌어도 텍스트 쪽은 고정이므로
    한 번만 계산하면 된다.
    반환: (style_names: list[str], text_feats: Tensor[num_styles, dim])
    """
    import torch

    model, processor, device = _load_model(model_name)

    style_names = list(STYLE_PROMPTS.keys())
    style_vectors = []

    with torch.no_grad():
        for name in style_names:
            prompts = STYLE_PROMPTS[name]
            inputs = processor(text=prompts, return_tensors="pt",
                               padding=True).to(device)
            feats = _as_tensor(model.get_text_features(**inputs))
            feats = feats / feats.norm(dim=-1, keepdim=True)
            # 여러 프롬프트 평균 -> 다시 정규화
            mean_feat = feats.mean(dim=0)
            mean_feat = mean_feat / mean_feat.norm()
            style_vectors.append(mean_feat)

    text_feats = torch.stack(style_vectors)  # [num_styles, dim]
    return style_names, text_feats


def _prepare_image(image):
    """입력을 RGB PIL 이미지로 정규화.

    - 경로(str) / PIL.Image 모두 허용
    - RGBA(누끼 딴 PNG)는 흰 배경에 합성해 RGB로 변환.
      CLIP은 투명 배경을 검정으로 처리하는 경향이 있어,
      흰 배경 합성이 의류 색을 더 정확히 보게 한다.
    """
    if isinstance(image, str):
        image = Image.open(image)

    if image.mode == "RGBA":
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])  # 알파를 마스크로
        return bg
    return image.convert("RGB")


def classify_style(image, model_name=DEFAULT_MODEL, temperature=8.0):
    """단품 이미지 1장의 스타일 점수를 계산.

    Args:
        image: 이미지 경로(str) 또는 PIL.Image.
               누끼 딴 RGBA PNG를 그대로 넣어도 된다.
        temperature: softmax 온도. CLIP 기본 logit_scale(약 100)을
               그대로 쓰면 미세한 유사도 차이도 극단적 확률로 부풀려져
               (예: 77% vs 8%) 모호한 옷도 자신만만하게 찍힌다.
               온도로 logit을 나눠 분포를 부드럽게 만들면, 모호한 옷은
               여러 스타일에 고르게 퍼져 '모호함'이 수치에 드러난다.
               값이 클수록 더 부드러워짐(=모호함이 더 잘 보임).
               1.0이면 CLIP 원본 동작. 6~10 권장.

    Returns:
        dict {
          "top_style":  str,    # 1등 스타일 (한글 라벨)
          "top_score":  float,  # 1등 점수 (softmax 확률, 0~1)
          "margin":     float,  # 1등 - 2등 점수 차 (작을수록 모호)
          "scores":     dict,   # {스타일: 확률} 전체, 내림차순
          "is_confident": bool, # margin >= CONFIDENCE_MARGIN 여부
          "raw_scores": dict,   # softmax 전 코사인 유사도
          "raw_margin": float,  # raw 1등-2등 격차
        }
    """
    import torch

    model, processor, device = _load_model(model_name)
    style_names, text_feats = _build_text_features(model_name)

    pil_img = _prepare_image(image)

    with torch.no_grad():
        img_inputs = processor(images=pil_img, return_tensors="pt").to(device)
        img_feat = _as_tensor(model.get_image_features(**img_inputs))
        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)  # [1, dim]

        # raw 코사인 유사도 (logit_scale·softmax 적용 전)
        # text_feats, img_feat 모두 정규화돼 있으므로 내적 = 코사인 유사도
        cos_sim = (img_feat @ text_feats.T).squeeze(0).cpu().numpy()

        # 코사인 유사도 -> logit_scale/temperature 로 스케일 -> softmax
        # CLIP 원본 logit_scale은 약 100배라 분포가 과도하게 뾰족해진다.
        # temperature로 나눠 완화하면 모호한 옷의 모호함이 보존된다.
        # 일부 모델은 logit_scale 속성이 없을 수 있어 기본값 100 사용.
        if hasattr(model, "logit_scale"):
            base_scale = model.logit_scale.exp().item()
        else:
            base_scale = 100.0
        logit_scale = base_scale / temperature
        logits = (img_feat @ text_feats.T) * logit_scale  # [1, num_styles]
        probs = logits.softmax(dim=-1).squeeze(0).cpu().numpy()

    # 점수 내림차순 정렬 (softmax 확률 기준)
    order = np.argsort(probs)[::-1]
    scores = {style_names[i]: float(probs[i]) for i in order}

    # raw 코사인 유사도도 같은 순서로 정리
    raw_scores = {style_names[i]: float(cos_sim[i]) for i in order}
    sorted_cos = cos_sim[order]
    raw_margin = float(sorted_cos[0] - sorted_cos[1])

    sorted_probs = probs[order]
    top_style = style_names[order[0]]
    top_score = float(sorted_probs[0])
    margin = float(sorted_probs[0] - sorted_probs[1])

    # 신뢰 판정은 온도에 영향받지 않는 raw 유사도 격차로 한다.
    # (softmax margin은 temperature에 따라 절대값이 변해 기준이 흔들림)
    # 0.03은 검증으로 조정할 임계값: raw 1-2등 격차가 이보다 작으면
    # "실제로 잘 안 갈리는 모호한 옷"으로 본다.
    RAW_CONFIDENCE_MARGIN = 0.03

    return {
        "top_style": top_style,
        "top_score": top_score,
        "margin": margin,
        "scores": scores,
        "is_confident": raw_margin >= RAW_CONFIDENCE_MARGIN,
        # raw 코사인 유사도 (softmax 착시 진단용)
        "raw_scores": raw_scores,
        "raw_margin": raw_margin,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python style_classifier.py <이미지경로>")
        sys.exit(1)

    result = classify_style(sys.argv[1])

    print("\n===== 스타일 태깅 결과 =====")
    print(f"  1등 스타일: {result['top_style']} "
          f"({result['top_score']:.1%})")
    print(f"  softmax margin: {result['margin']:.3f}  /  "
          f"raw 유사도 margin: {result['raw_margin']:.4f}")
    print(f"  판정: {'신뢰 가능' if result['is_confident'] else '모호함 (주의)'}")

    print("\n  전체 점수 (softmax % | raw 코사인유사도):")
    for style in result["scores"]:
        p = result["scores"][style]
        raw = result["raw_scores"][style]
        bar = "█" * int(p * 40)
        print(f"    {style:<6} {p:>6.1%} | {raw:.4f}  {bar}")

    print("\n  ※ raw margin이 0.02~0.03처럼 작은데 softmax %가 크게"
          " 벌어졌다면,\n     그 격차는 softmax 증폭(착시)이라는 신호입니다.")
