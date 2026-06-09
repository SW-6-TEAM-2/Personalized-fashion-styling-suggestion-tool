"""
CLIP 유틸리티 모듈

이미지/텍스트 → 512차원 임베딩 변환 및 스타일 유사도 계산
서버 전체에서 모델을 1회만 로드하도록 전역 캐싱 사용
"""

import numpy as np

try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False

# ── 전역 모델 캐시 (lazy load) ──────────────────────────────────────────────
_model     = None
_processor = None
_text_cache = {}  # 텍스트 임베딩 캐시 (스타일 프롬프트는 고정이므로 재계산 불필요)

# ── 스타일별 텍스트 프롬프트 ────────────────────────────────────────────────
# fashion.db 스타일 키 → CLIP 텍스트 프롬프트
STYLE_PROMPTS = {
    "casual":  (
        "casual everyday fashion: plain hoodie, basic t-shirt, straight jeans, "
        "white sneakers, relaxed comfortable fit, simple colors, everyday wear"
    ),
    "minimal": (
        "minimalist fashion: tailored slim trousers, plain crewneck sweater, "
        "structured overcoat, tonal monochrome dressing, clean architectural silhouette, "
        "COS Lemaire Acne Studios luxury basics, no graphic no logo no pattern"
    ),
    "classic": (
        "classic preppy fashion: wool blazer, oxford button-down shirt, "
        "chino trousers, leather loafers, trench coat, polo shirt, "
        "Ralph Lauren Tommy Hilfiger aesthetic, smart elegant timeless tailored"
    ),
    "street":  (
        "streetwear fashion: oversized graphic hoodie, baggy cargo pants, "
        "chunky platform sneakers, Supreme BAPE Off-White Palace aesthetic, "
        "bold logo print, camouflage, graffiti, urban hype youth culture"
    ),
}


def _get_clip():
    """CLIP 모델 lazy load (최초 1회만 로드, 이후 캐싱)"""
    global _model, _processor
    if not HAS_CLIP:
        return None, None
    if _model is None:
        print("[CLIP] Loading model... (first run, may download ~600MB)")
        _model     = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _model.eval()
        print("[CLIP] Model loaded OK")
    return _model, _processor


def embed_image(pil_image):
    """
    PIL Image → 정규화된 512차원 float list 반환
    CLIP 사용 불가 시 None 반환
    """
    model, processor = _get_clip()
    if model is None:
        return None

    rgb    = pil_image.convert("RGB")
    inputs = processor(images=rgb, return_tensors="pt")

    with torch.no_grad():
        vision_out = model.vision_model(**inputs)
        pooled     = vision_out.pooler_output          # (1, hidden_size)
        feat       = model.visual_projection(pooled)   # (1, 512)
        feat       = feat / feat.norm(dim=-1, keepdim=True)

    return feat[0].cpu().numpy().tolist()


def embed_text(text):
    """
    텍스트 → 정규화된 512차원 numpy array 반환
    결과를 캐싱하여 동일 텍스트 반복 계산 방지
    CLIP 사용 불가 시 None 반환
    """
    if text in _text_cache:
        return _text_cache[text]

    model, processor = _get_clip()
    if model is None:
        return None

    inputs = processor(text=[text], return_tensors="pt", padding=True)

    with torch.no_grad():
        text_out = model.text_model(**inputs)
        pooled   = text_out.pooler_output              # (1, hidden_size)
        feat     = model.text_projection(pooled)       # (1, 512)
        feat     = feat / feat.norm(dim=-1, keepdim=True)

    result = feat[0].cpu().numpy()
    _text_cache[text] = result
    return result


def cosine_style_score(image_embedding, target_style):
    """
    이미지 임베딩과 스타일 텍스트 간 코사인 유사도로 스타일 스코어 계산

    반환값: 0.0 ~ 2.0 (낮을수록 해당 스타일과 유사 → 추천 우선순위 높음)
    1.0 - cosine_similarity 로 변환 (HSV distance 방식과 동일하게 '낮을수록 좋음')
    CLIP 사용 불가 또는 임베딩 없으면 None 반환
    """
    if not image_embedding:
        return None

    prompt   = STYLE_PROMPTS.get(target_style, "casual fashion outfit")
    text_emb = embed_text(prompt)

    if text_emb is None:
        return None

    img_emb = np.array(image_embedding, dtype=np.float32)
    cosine  = float(np.dot(img_emb, text_emb))

    return 1.0 - cosine  # 낮을수록 스타일에 가까움


# UI 키워드 4개 → CLIP 텍스트 프롬프트 (STYLE_PROMPTS와 동기화)
UI_STYLE_PROMPTS = {
    "#캐주얼": STYLE_PROMPTS["casual"],
    "#미니멀": STYLE_PROMPTS["minimal"],
    "#클래식": STYLE_PROMPTS["classic"],
    "#스트릿": STYLE_PROMPTS["street"],
}


def classify_style(image_embedding):
    """
    이미지 임베딩 → UI 6개 스타일 중 가장 유사한 스타일 태그 반환
    예: "#캐주얼", "#워크웨어" 등
    CLIP 사용 불가 또는 임베딩 없으면 None 반환
    """
    if not image_embedding:
        return None

    img_emb    = np.array(image_embedding, dtype=np.float32)
    best_label = None
    best_score = -999.0

    for label, prompt in UI_STYLE_PROMPTS.items():
        text_emb = embed_text(prompt)
        if text_emb is None:
            return None
        score = float(np.dot(img_emb, text_emb))
        if score > best_score:
            best_score = score
            best_label = label

    return best_label  # 예: "#캐주얼"
