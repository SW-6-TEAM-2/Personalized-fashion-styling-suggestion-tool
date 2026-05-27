"""
K-means 클러스터 개수(K) 선정 근거 검증 실험

목적:
  image_processor.py의 K 선정 근거를 데이터 기반으로 검증한다.
  Elbow method와 Silhouette score 두 가지 정량 지표를 통해
  여러 의류 이미지에서 K=2~8 범위 중 적절한 K가 무엇인지 분석한다.

배경:
  초기에는 K=3을 "메인색상/그림자/하이라이트 3요소"라는 직관적 근거로
  선택했으나, K-means가 의미적 분류를 하는 알고리즘이 아니라는 점
  (RGB 좌표상 거리 기반 클러스터링)을 인지하고 데이터 기반 재검증을 진행.

  본 실험 결과 K=4 지점에서 Inertia 감소율이 둔화되고 Silhouette score도
  양호하여 최종적으로 K=4를 채택. (image_processor.py에 반영 완료)

실행:
  python kmeans_validation.py

출력:
  - kmeans_validation_result.png : Elbow + Silhouette 그래프
  - kmeans_validation_result.csv : 이미지별 K별 inertia/silhouette 결과
"""

import os
import csv
import random
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import matplotlib

# 한글 폰트 설정 (Windows: 맑은 고딕)
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False


# ─────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────

DATA_DIR = os.path.join("data", "reference", "coordinate")
STYLES = ["workwear", "minimal", "casual", "classic", "street"]
SAMPLES_PER_STYLE = 5     # 스타일당 무작위로 N장 추출
K_RANGE = range(2, 9)     # K=2~8 실험
PIXEL_SAMPLE_SIZE = 5000  # 이미지당 최대 픽셀 수 (K-means 속도용)
RANDOM_SEED = 42

OUTPUT_GRAPH = "kmeans_validation_result.png"
OUTPUT_CSV = "kmeans_validation_result.csv"


# ─────────────────────────────────────────────────────────────────
# 이미지 로드 및 픽셀 추출
# ─────────────────────────────────────────────────────────────────

def load_pixels(image_path):
    """이미지에서 픽셀 RGB 배열 추출. 너무 많으면 샘플링."""
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img).reshape(-1, 3)

    if len(arr) > PIXEL_SAMPLE_SIZE:
        rng = np.random.default_rng(RANDOM_SEED)
        idx = rng.choice(len(arr), PIXEL_SAMPLE_SIZE, replace=False)
        arr = arr[idx]

    return arr


def sample_images(data_dir, styles, samples_per_style):
    """각 스타일 폴더에서 이미지를 무작위로 N장씩 샘플링."""
    random.seed(RANDOM_SEED)
    selected = []

    for style in styles:
        folder = os.path.join(data_dir, style)
        if not os.path.isdir(folder):
            print(f"[경고] 폴더 없음: {folder}")
            continue

        files = [f for f in os.listdir(folder)
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))]

        if len(files) < samples_per_style:
            print(f"[경고] {style} 이미지 부족: {len(files)}장 (요청 {samples_per_style})")
            samples = files
        else:
            samples = random.sample(files, samples_per_style)

        for f in samples:
            selected.append((style, os.path.join(folder, f)))

    return selected


# ─────────────────────────────────────────────────────────────────
# K-means 검증
# ─────────────────────────────────────────────────────────────────

def evaluate_k_for_image(pixels, k_range):
    """한 이미지에 대해 K별 inertia와 silhouette score 계산."""
    inertias = []
    silhouettes = []

    for k in k_range:
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_SEED)
        labels = kmeans.fit_predict(pixels)
        inertias.append(kmeans.inertia_)

        # silhouette은 K=1이면 정의 안 됨. 우리 범위는 K≥2이라 안전
        # 단, 픽셀이 너무 많으면 silhouette 계산이 느려서 샘플링
        if len(pixels) > 1000:
            rng = np.random.default_rng(RANDOM_SEED)
            idx = rng.choice(len(pixels), 1000, replace=False)
            score = silhouette_score(pixels[idx], labels[idx])
        else:
            score = silhouette_score(pixels, labels)

        silhouettes.append(score)

    return inertias, silhouettes


# ─────────────────────────────────────────────────────────────────
# 시각화
# ─────────────────────────────────────────────────────────────────

def plot_results(all_inertias, all_silhouettes, k_range, output_path):
    """모든 이미지의 K별 결과를 평균 + 분산 곡선으로 시각화."""
    inertias_arr = np.array(all_inertias)
    silhouettes_arr = np.array(all_silhouettes)

    mean_inertia = inertias_arr.mean(axis=0)
    std_inertia = inertias_arr.std(axis=0)

    mean_silhouette = silhouettes_arr.mean(axis=0)
    std_silhouette = silhouettes_arr.std(axis=0)

    k_list = list(k_range)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # ─── 왼쪽: Elbow method (inertia) ───
    ax1 = axes[0]
    ax1.plot(k_list, mean_inertia, marker="o", color="#2E86AB", linewidth=2)
    ax1.fill_between(k_list,
                     mean_inertia - std_inertia,
                     mean_inertia + std_inertia,
                     alpha=0.2, color="#2E86AB")
    ax1.axvline(x=4, color="red", linestyle="--", alpha=0.7,
                linewidth=2, label="선택 (K=4)")
    ax1.set_xlabel("클러스터 개수 (K)", fontsize=12)
    ax1.set_ylabel("Inertia (작을수록 클러스터 밀집)", fontsize=12)
    ax1.set_title("Elbow Method", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3)
    ax1.set_xticks(k_list)

    # ─── 오른쪽: Silhouette score ───
    ax2 = axes[1]
    ax2.plot(k_list, mean_silhouette, marker="s", color="#A23B72", linewidth=2)
    ax2.fill_between(k_list,
                     mean_silhouette - std_silhouette,
                     mean_silhouette + std_silhouette,
                     alpha=0.2, color="#A23B72")
    ax2.axvline(x=4, color="red", linestyle="--", alpha=0.7,
                linewidth=2, label="선택 (K=4)")
    ax2.set_xlabel("클러스터 개수 (K)", fontsize=12)
    ax2.set_ylabel("Silhouette Score (1에 가까울수록 좋음)", fontsize=12)
    ax2.set_title("Silhouette Analysis", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.3)
    ax2.set_xticks(k_list)

    fig.suptitle(
        f"K-means K 선정 검증 (의류 이미지 {len(inertias_arr)}장 평균)",
        fontsize=14, fontweight="bold"
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n[OK] 그래프 저장: {output_path}")


def save_csv(results, k_range, output_path):
    """이미지별 K별 결과를 CSV로 저장."""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        header = ["style", "image"] \
                 + [f"inertia_K{k}" for k in k_range] \
                 + [f"silhouette_K{k}" for k in k_range]
        writer.writerow(header)

        for row in results:
            writer.writerow(row)

    print(f"[OK] CSV 저장: {output_path}")


# ─────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("K-means K 선정 검증 실험")
    print(f"  데이터: {DATA_DIR}")
    print(f"  스타일: {STYLES}")
    print(f"  스타일당 샘플: {SAMPLES_PER_STYLE}장")
    print(f"  K 범위: {list(K_RANGE)}")
    print("=" * 60)

    # 1. 이미지 샘플링
    sampled = sample_images(DATA_DIR, STYLES, SAMPLES_PER_STYLE)
    print(f"\n총 {len(sampled)}장 분석 시작\n")

    # 2. 각 이미지에 대해 K별 메트릭 계산
    all_inertias = []
    all_silhouettes = []
    csv_rows = []

    for i, (style, img_path) in enumerate(sampled, 1):
        try:
            pixels = load_pixels(img_path)
            inertias, silhouettes = evaluate_k_for_image(pixels, K_RANGE)

            all_inertias.append(inertias)
            all_silhouettes.append(silhouettes)

            row = [style, os.path.basename(img_path)] + inertias + silhouettes
            csv_rows.append(row)

            print(f"  [{i:2d}/{len(sampled)}] {style}/{os.path.basename(img_path)} 완료")

        except Exception as e:
            print(f"  [{i:2d}/{len(sampled)}] 실패 [{img_path}]: {e}")
            continue

    if not all_inertias:
        print("\n[ERROR] 분석된 이미지가 없습니다. 데이터 폴더 확인 필요.")
        return

    # 3. 시각화 및 결과 저장
    plot_results(all_inertias, all_silhouettes, K_RANGE, OUTPUT_GRAPH)
    save_csv(csv_rows, K_RANGE, OUTPUT_CSV)

    # 4. 요약 통계
    mean_inertia = np.mean(all_inertias, axis=0)
    mean_silhouette = np.mean(all_silhouettes, axis=0)
    k_list = list(K_RANGE)

    print("\n" + "=" * 60)
    print("결과 요약 (모든 이미지 평균)")
    print("=" * 60)
    print(f"{'K':>3} | {'Inertia':>12} | {'Silhouette':>12}")
    print("-" * 35)
    for i, k in enumerate(k_list):
        marker = "  ← K=4 (선택)" if k == 4 else ""
        print(f"{k:>3} | {mean_inertia[i]:>12.1f} | {mean_silhouette[i]:>12.4f}{marker}")

    # 5. 해석 도움말
    print("\n" + "=" * 60)
    print("해석 가이드")
    print("=" * 60)
    print("  - Elbow method: inertia 감소율이 급격히 둔화되는 'K' 지점이 최적")
    print("  - Silhouette score: 1에 가까울수록 클러스터링 품질 좋음")
    print("  - 두 지표 모두 고려해서 K 선정 근거 정당화 가능")


if __name__ == "__main__":
    main()
