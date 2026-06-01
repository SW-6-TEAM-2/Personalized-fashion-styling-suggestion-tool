"""
1등 스타일만 반환하는 간편 버전.

실제 분류 로직(CLIP 모델·프롬프트·이미지 처리)은 전부
style_classifier.py 를 그대로 재사용한다.
=> 프롬프트나 스타일을 바꿀 일이 생기면 style_classifier.py
   한 곳만 고치면 양쪽에 똑같이 반영된다.

쓰는 법:
    from first_style_classifier import classify_style
    style = classify_style("어떤옷.png")   # -> "캐주얼" 같은 문자열 1개

    # 점수 전부(6개 + margin)가 필요하면 이 파일이 아니라
    # style_classifier.py 의 classify_style 을 쓰면 된다.
"""

from style_classifier import classify_style as _classify_full


def classify_style(image, model_name=None):
    """단품 이미지 1장의 1등 스타일(한글 라벨)만 반환.

    Args:
        image: 이미지 경로(str) 또는 PIL.Image.

    Returns:
        str: 1등 스타일 (예: "캐주얼")
    """
    if model_name is None:
        result = _classify_full(image)
    else:
        result = _classify_full(image, model_name)
    return result["top_style"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python first_style_classifier.py <이미지경로>")
        sys.exit(1)

    print(f"1등 스타일: {classify_style(sys.argv[1])}")
