"""
폴더 안 이미지들의 1등 스타일만 출력하는 스크립트.

사용법:
    python test_first_style_classifier.py <이미지폴더 또는 파일>
    예) python test_first_style_classifier.py test_images
"""

import os
import sys

from first_style_classifier import classify_style


IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def collect_images(path):
    if os.path.isfile(path):
        return [path]
    images = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith(IMG_EXTS):
                images.append(os.path.join(root, f))
    return sorted(images)


def main():
    if len(sys.argv) < 2:
        print("사용법: python test_first_style_classifier.py <이미지폴더 또는 파일>")
        sys.exit(1)

    images = collect_images(sys.argv[1])
    if not images:
        print("이미지를 찾지 못했습니다:", sys.argv[1])
        sys.exit(1)

    print(f"\n총 {len(images)}장 (최초 1회 모델 다운로드로 시간이 걸릴 수 있습니다)\n")
    print(f"{'파일명':<22} 스타일")
    print("-" * 36)

    for img_path in images:
        stem = os.path.splitext(os.path.basename(img_path))[0]
        try:
            style = classify_style(img_path)
        except Exception as e:
            print(f"{stem:<22} 실패: {e}")
            continue
        print(f"{stem:<22} {style}")


if __name__ == "__main__":
    main()
