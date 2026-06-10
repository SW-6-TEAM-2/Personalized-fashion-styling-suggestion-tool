"""
스타일 태깅 검증 스크립트

목적:
    CLIP zero-shot 스타일 태깅이 "추천 필터로 쓸 만한가"를 판단한다.
    핵심 지표는 1등 라벨이 아니라 margin(1등-2등 점수 차)의 분포다.

사용법:
    # 폴더 안의 모든 이미지를 한꺼번에 검증
    python test_style_classifier.py <이미지폴더>

    # 이미지 한 장만
    python test_style_classifier.py <이미지파일>

읽는 법:
    - margin이 큰 옷이 많다 (평균 0.15+)  -> 태깅이 뚜렷. 추천 필터로 써볼 만함.
    - margin이 작은 옷이 많다 (평균 0.05-) -> 옷마다 스타일이 안 갈림.
      => 단정 태그는 위험. "참고용 복수 태그"로만 쓰거나, 스타일은
         사용자가 UI에서 고르게 하는 편이 안전하다는 증거가 된다.

    같은 흰 셔츠를 여러 번 넣어보고 점수가 흔들리는지도 확인해보면 좋다.
"""

import os
import sys

from style_classifier import classify_style


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
        print("사용법: python test_style_classifier.py <이미지폴더 또는 파일>")
        sys.exit(1)

    images = collect_images(sys.argv[1])
    if not images:
        print("이미지를 찾지 못했습니다:", sys.argv[1])
        sys.exit(1)

    print(f"\n총 {len(images)}장 검증 시작 "
          f"(최초 1회 모델 다운로드로 시간이 걸릴 수 있습니다)\n")
    print(f"{'파일명':<28} {'1등 스타일':<10} {'1등%':>6} {'sm_margin':>10} {'raw_margin':>11}  판정")
    print("-" * 84)

    margins = []
    raw_margins = []
    confident_count = 0
    style_tally = {}

    for img_path in images:
        try:
            r = classify_style(img_path)
        except Exception as e:
            print(f"{os.path.basename(img_path):<28} 실패: {e}")
            continue

        margins.append(r["margin"])
        raw_margins.append(r["raw_margin"])
        if r["is_confident"]:
            confident_count += 1
        style_tally[r["top_style"]] = style_tally.get(r["top_style"], 0) + 1

        verdict = "뚜렷" if r["is_confident"] else "모호"
        name = os.path.basename(img_path)
        if len(name) > 27:
            name = name[:24] + "..."
        print(f"{name:<28} {r['top_style']:<10} "
              f"{r['top_score']:>5.0%} {r['margin']:>10.3f} "
              f"{r['raw_margin']:>11.4f}  {verdict}")

    # ── 요약 통계 (이게 의사결정의 핵심) ──
    if not margins:
        print("\n분석된 이미지가 없습니다.")
        return

    n = len(margins)
    avg_margin = sum(margins) / n
    sorted_m = sorted(margins)
    median_margin = sorted_m[n // 2]
    avg_raw_margin = sum(raw_margins) / n

    print("\n" + "=" * 84)
    print("요약")
    print("-" * 84)
    print(f"  검증 장수:            {n}")
    print(f"  평균 softmax margin:  {avg_margin:.3f}")
    print(f"  중앙값 softmax margin:{median_margin:.3f}")
    print(f"  평균 raw 유사도 margin:{avg_raw_margin:.4f}")
    print(f"  '뚜렷' 비율:          {confident_count}/{n} "
          f"({confident_count / n:.0%})  (softmax margin >= 0.15)")
    print(f"  1등 스타일 분포:      {style_tally}")

    # ── softmax 착시 진단 ──
    print("\n  softmax 착시 진단:")
    if avg_raw_margin < 0.03:
        print(f"    -> raw margin 평균이 {avg_raw_margin:.4f}로 매우 작은데도")
        print("       softmax %는 크게 벌어짐. 즉 1등의 '확신'은 대부분")
        print("       softmax 증폭에서 온 착시. margin을 신뢰 지표로 쓰면 안 됨.")
    elif avg_raw_margin < 0.06:
        print(f"    -> raw margin 평균 {avg_raw_margin:.4f}. 실제 격차가 작은 편.")
        print("       softmax %를 액면 그대로 신뢰하기 어려움.")
    else:
        print(f"    -> raw margin 평균 {avg_raw_margin:.4f}. 실제로도 어느 정도")
        print("       구분이 됨. softmax만의 착시는 아닌 것으로 보임.")

    print("\n  판단 가이드:")
    if avg_margin >= 0.15 and confident_count / n >= 0.6:
        print("    -> softmax margin은 크지만, 위 raw 진단을 함께 봐야 함.")
    elif avg_margin >= 0.08:
        print("    -> 애매한 수준. 추천 핵심 필터보다는 참고용 태그 권장.")
    else:
        print("    -> margin이 작음. 단품 스타일 단정은 위험.")
        print("       스타일은 사용자 선택 또는 스타일별 복수 추천으로 가는 게 안전.")

    # 1등 스타일이 한두 개로 쏠리면, 모델이 특정 스타일만
    # 남발하는 것일 수 있으니 별도 경고
    if style_tally and max(style_tally.values()) / n >= 0.5:
        print("\n  [경고] 1등 스타일이 소수 스타일로 쏠림 "
              f"({style_tally}).")
        print("       6개 스타일을 고르게 구분하지 못하고 있을 수 있음.")


if __name__ == "__main__":
    main()
