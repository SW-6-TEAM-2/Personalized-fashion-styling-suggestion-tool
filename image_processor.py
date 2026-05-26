"""
의류 이미지 처리 모듈

기능:
  1. 배경 제거 (Rembg / 모델 선택 가능)
  2. 정사각 캔버스 정규화 (800x800 RGBA PNG)
  3. 대표 색상 추출 (K-means + HSV)
  4. OOTD 합성 (상/하/신발 -> 800x1200 코디)
"""

import io
import colorsys
from rembg import remove, new_session
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans


TARGET_SIZE = 800
DEFAULT_MODEL = "isnet-general-use"
KMEANS_CLUSTERS = 3
NEUTRAL_SAT_THRESHOLD = 0.15
NEUTRAL_TONED_THRESHOLD = 0.35

OOTD_CANVAS_WIDTH = 800
OOTD_CANVAS_HEIGHT = 1200
OOTD_GAP = 10  # 의류 사이 간격 (px). 음수면 살짝 겹침.


def remove_background_and_normalize(input_path, output_path,
                                    target_size=TARGET_SIZE,
                                    model=DEFAULT_MODEL):
    """배경 제거 + 정사각 캔버스 정규화."""
    session = new_session(model)

    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes, session=session)

    img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    img.thumbnail((target_size, target_size), Image.LANCZOS)
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    offset = ((target_size - img.width) // 2, (target_size - img.height) // 2)
    canvas.paste(img, offset, img)

    canvas.save(output_path, "PNG")
    return canvas


def extract_dominant_color(image, k=KMEANS_CLUSTERS):
    """K-means로 대표 색상 추출 + HSV 기반 분류.

    반환 dict 구조:
      - rgb, hex, color_type, is_neutral : 기존 필드 (호환성 유지)
      - h, s, v                          : HSV 정밀값 (모두 0.0 ~ 1.0)
      - dominant_ratio                   : 주색 클러스터 비중 (0.0 ~ 1.0)
      - sub_rgb, sub_ratio               : 2등 클러스터 색상/비중 (보조색, 확장용)
    """
    arr = np.array(image)
    mask = arr[:, :, 3] > 0
    pixels = arr[mask][:, :3]

    if len(pixels) == 0:
        raise ValueError("의류 영역 픽셀이 없습니다.")

    if len(pixels) > 10000:
        indices = np.random.choice(len(pixels), 10000, replace=False)
        pixels_sample = pixels[indices]
    else:
        pixels_sample = pixels

    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    kmeans.fit(pixels_sample)

    labels = kmeans.labels_
    counts = np.bincount(labels)
    total = counts.sum()

    # 비중 큰 순으로 정렬된 클러스터 인덱스
    sorted_clusters = np.argsort(counts)[::-1]

    # 주색 (1등 클러스터)
    dominant_cluster = sorted_clusters[0]
    dominant_rgb = kmeans.cluster_centers_[dominant_cluster].astype(int)
    r, g, b = int(dominant_rgb[0]), int(dominant_rgb[1]), int(dominant_rgb[2])
    dominant_ratio = counts[dominant_cluster] / total

    # HSV 변환 (모두 0.0 ~ 1.0 범위)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    # HSV 기반 5단계 분류
    if s < NEUTRAL_SAT_THRESHOLD:
        if v > 0.85:
            color_type = "white"
        elif v < 0.25:
            color_type = "black"
        else:
            color_type = "gray"
        is_neutral = True
    elif s < NEUTRAL_TONED_THRESHOLD:
        color_type = "neutral_toned"
        is_neutral = True
    else:
        color_type = "vivid"
        is_neutral = False

    # 보조색 (2등 클러스터, 패턴/배색 대응용)
    if len(sorted_clusters) >= 2:
        sub_cluster_idx = sorted_clusters[1]
        sub_rgb_arr = kmeans.cluster_centers_[sub_cluster_idx].astype(int)
        sub_r, sub_g, sub_b = int(sub_rgb_arr[0]), int(sub_rgb_arr[1]), int(sub_rgb_arr[2])
        sub_ratio = counts[sub_cluster_idx] / total
    else:
        sub_r, sub_g, sub_b = r, g, b
        sub_ratio = 0.0

    return {
        # ── 기존 필드 (호환성 유지: image_store.py 그대로 작동) ──
        "rgb": (r, g, b),
        "hex": "#{:02X}{:02X}{:02X}".format(r, g, b),
        "color_type": color_type,
        "is_neutral": is_neutral,

        # ── 신규: HSV 정밀값 (모두 0.0 ~ 1.0 범위) ──
        "h": float(h),
        "s": float(s),
        "v": float(v),

        # ── 신규: 주색 비중 (추천 신뢰도 가중치로 활용 가능) ──
        "dominant_ratio": float(dominant_ratio),

        # ── 신규: 보조색 (확장용, 현재 v1 추천 로직에서는 미사용해도 됨) ──
        "sub_rgb": (sub_r, sub_g, sub_b),
        "sub_ratio": float(sub_ratio),
    }


def process_clothing_image(input_path, output_path, model=DEFAULT_MODEL):
    """단품 이미지 처리: 배경 제거 + 정규화 + 색상 추출."""
    processed_img = remove_background_and_normalize(input_path, output_path,
                                                    model=model)
    color_info = extract_dominant_color(processed_img)

    return {
        "path": output_path,
        "size": (TARGET_SIZE, TARGET_SIZE),
        "model": model,
        **color_info,
    }


def compose_outfit(top_path, bottom_path, shoes_path, output_path):
    """
    상의 + 하의 + 신발 PNG를 800x1200 캔버스에 합성.

    각 의류의 최대 크기를 실제 사람 비례에 맞춰 다르게 적용:
      - 상의:  가로 75% (어깨 너비), 영역 높이 38%
      - 하의:  가로 50% (허리/다리 너비), 영역 높이 42%
      - 신발:  가로 35% (발 너비), 영역 높이 20%

    알파 bbox로 의류만 추출하고, 위에서 아래로 차곡차곡 쌓음.
    """
    canvas = Image.new("RGBA",
                       (OOTD_CANVAS_WIDTH, OOTD_CANVAS_HEIGHT),
                       (0, 0, 0, 0))

    # (이미지 경로, 최대 가로 비율, 영역 높이 비율)
    items_config = [
        (top_path,    0.75, 0.38),  # 상의
        (bottom_path, 0.50, 0.42),  # 하의
        (shoes_path,  0.35, 0.20),  # 신발
    ]

    cursor_y = 0

    for img_path, max_width_ratio, section_height_ratio in items_config:
        item = Image.open(img_path).convert("RGBA")

        # 1) 알파 채널 bbox로 의류 영역만 크롭
        bbox = item.getbbox()
        if bbox:
            item = item.crop(bbox)

        # 2) 의류별 최대 크기로 리사이즈 (비율 유지)
        max_w = int(OOTD_CANVAS_WIDTH * max_width_ratio)
        max_h = int(OOTD_CANVAS_HEIGHT * section_height_ratio)
        item.thumbnail((max_w, max_h), Image.LANCZOS)

        # 3) 가로 중앙 정렬, 세로는 cursor_y 위치에 배치
        x_pos = (OOTD_CANVAS_WIDTH - item.width) // 2
        y_pos = cursor_y

        canvas.paste(item, (x_pos, y_pos), item)

        # 다음 의류 위치로 커서 이동
        cursor_y += item.height + OOTD_GAP

    canvas.save(output_path, "PNG")

    return {
        "path": output_path,
        "size": (OOTD_CANVAS_WIDTH, OOTD_CANVAS_HEIGHT),
        "sections": ["top", "bottom", "shoes"],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법:")
        print("  단품 처리:        python image_processor.py <이미지>")
        print("  모델 지정:        python image_processor.py <이미지> --model <모델명>")
        print("  OOTD 합성:        python image_processor.py --ootd <상의> <하의> <신발>")
        print("")
        print("모델: isnet-general-use (기본) / u2net / u2net_cloth_seg")
        sys.exit(1)

    if sys.argv[1] == "--ootd":
        if len(sys.argv) < 5:
            print("OOTD 합성에는 3장의 이미지가 필요합니다.")
            sys.exit(1)

        top, bottom, shoes = sys.argv[2], sys.argv[3], sys.argv[4]
        print("\nOOTD 합성 시작")
        print("  상의:", top)
        print("  하의:", bottom)
        print("  신발:", shoes)

        result = compose_outfit(top, bottom, shoes, "ootd_result.png")

        print("\n[OK] 합성 완료")
        print("  파일:", result["path"])
        print("  크기:", result["size"])

    else:
        input_path = sys.argv[1]
        output_path = "output.png"

        model = DEFAULT_MODEL
        if "--model" in sys.argv:
            idx = sys.argv.index("--model")
            if idx + 1 < len(sys.argv):
                model = sys.argv[idx + 1]

        print("\n처리 시작:", input_path)
        print("  사용 모델:", model)

        result = process_clothing_image(input_path, output_path, model=model)

        print("\n[OK] 처리 완료\n")
        print("  파일:        ", result["path"])
        print("  크기:        ", result["size"])
        print("  사용 모델:    ", result["model"])
        print("  대표 색상:    ", "RGB", result["rgb"], "/", result["hex"])
        print("  HSV 정밀값:   ", f"H={result['h']:.3f}, S={result['s']:.3f}, V={result['v']:.3f}")
        print("  주색 비중:    ", f"{result['dominant_ratio']:.1%}")
        print("  보조색:      ", "RGB", result["sub_rgb"], f"(비중 {result['sub_ratio']:.1%})")
        print("  색상 분류:    ", result["color_type"])
        print("  무채색 여부:  ", result["is_neutral"])
