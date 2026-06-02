"""
무신사 스냅 코디컷 이미지 수집 모듈

목적:
  추천 시스템의 비교 대상 풀(pool)을 DB에 채우기 위한 코디컷 데이터 수집.
  무신사 스냅(/snap/main/recommend) 페이지에서 사용자 OOTD 사진을 수집한다.

스냅 페이지를 선택한 이유:
  일반 상품 검색(/search/goods)은 단품 상품컷 위주라 추천 결과로 적합하지 않음.
  스냅 페이지는 모델/사용자의 전신 코디 사진만 모여 있어 추천 결과로 보여주기에 적합.

폴더 구조 (신승민의 image_store.py가 자동 인식):
  data/
  └── reference/
      └── coordinate/
          ├── workwear/      (styles=6)
          ├── minimal/       (styles=5)
          ├── casual/        (styles=8)
          ├── classic/       (styles=9)
          ├── street/        (styles=10)
          └── citiboy/       (styles=7, 선택)

기술 스택:
  - Selenium + ChromeDriverManager (지연 로딩 대응)
  - data-mds='Image' 셀렉터 (광고/아이콘 제외)
  - 학술 목적 소량 수집, 외부 배포하지 않음

실행:
  python image_collect.py
"""

import os
import time
import urllib.request

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("[ERROR] 필요한 패키지가 설치되어 있지 않습니다.")
    print("        터미널에서 다음 명령을 실행하세요:")
    print("          pip install selenium webdriver-manager")
    raise


# ─────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────

BASE_DIR = os.path.join("data", "reference", "coordinate")

# 무신사 스냅 페이지의 스타일 코드 매핑 (?styles=숫자)
# 직접 확인한 값. 변경 시 무신사 사이트에서 재확인 필요.
SNAP_STYLES = [
    # (스타일 라벨, 무신사 스냅 styles 파라미터 값)
    ("workwear", 6),
    ("minimal",  5),
    ("casual",   8),
    ("classic",  9),
    ("street",   10),
    # ("citiboy",  7),   # 시티보이도 받으려면 주석 해제
]

# 스타일당 수집 목표 개수
IMAGES_PER_STYLE = 30

# 스크롤 설정 (스냅 페이지는 무한 스크롤이라 일반 검색보다 많이 굴림)
SCROLL_COUNT = 6
SCROLL_WAIT_SEC = 2

# 깨진 이미지/썸네일 필터 (이 크기 미만은 폐기)
MIN_FILE_SIZE_KB = 5


# ─────────────────────────────────────────────────────────────────
# 드라이버 설정
# ─────────────────────────────────────────────────────────────────

def setup_driver(headless=False):
    """Selenium Chrome 드라이버 초기화."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,900")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


# ─────────────────────────────────────────────────────────────────
# 수집 로직
# ─────────────────────────────────────────────────────────────────

def build_snap_url(style_code):
    """무신사 스냅 페이지 URL 생성.

    Args:
        style_code: 스타일 ID 정수 (예: 6은 워크웨어)
    """
    return f"https://www.musinsa.com/snap/main/recommend?styles={style_code}&gf=A"


def scroll_to_load(driver, count=SCROLL_COUNT, wait=SCROLL_WAIT_SEC):
    """무한 스크롤 페이지에서 충분한 이미지가 로드되도록 여러 번 스크롤."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(count):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait)
        new_height = driver.execute_script("return document.body.scrollHeight")
        # 더 이상 페이지가 늘어나지 않으면 중단
        if new_height == last_height:
            break
        last_height = new_height


def collect_one_style(driver, style_label, style_code, count):
    """
    단일 스타일에 대해 스냅 이미지 수집 후 지정 폴더에 저장.

    Args:
        driver: Selenium WebDriver 인스턴스
        style_label: 저장 폴더/파일명용 영문 라벨 (예: "workwear")
        style_code: 무신사 스냅 styles 파라미터 값 (예: 6)
        count: 수집 목표 개수

    Returns:
        (downloaded_count, skipped_count, failed_count)
    """
    save_dir = os.path.join(BASE_DIR, style_label)
    os.makedirs(save_dir, exist_ok=True)

    url = build_snap_url(style_code)
    print(f"\n── [{style_label}] styles={style_code} ──")
    print(f"   URL: {url}")

    try:
        driver.get(url)
        time.sleep(3)  # 스냅 페이지는 초기 로딩 약간 더 걸림
        scroll_to_load(driver)
    except WebDriverException as e:
        print(f"   페이지 로드 실패: {e}")
        return 0, 0, 0

    # 무신사 이미지 태그 (광고/아이콘 제외)
    img_elements = driver.find_elements(By.CSS_SELECTOR, "img[data-mds='Image']")
    print(f"   감지된 이미지 후보: {len(img_elements)}개")

    downloaded = 0
    skipped = 0
    failed = 0

    for idx, img in enumerate(img_elements):
        if downloaded >= count:
            break

        try:
            img_url = img.get_attribute("src")
            if not img_url or not img_url.startswith("http"):
                continue

            file_path = os.path.join(save_dir, f"{style_label}_{idx:03d}.jpg")

            # 중복 다운로드 방지
            if os.path.exists(file_path):
                skipped += 1
                downloaded += 1
                continue

            urllib.request.urlretrieve(img_url, file_path)

            # 너무 작은 파일은 썸네일/깨진 이미지로 보고 폐기
            if os.path.getsize(file_path) < MIN_FILE_SIZE_KB * 1024:
                os.remove(file_path)
                failed += 1
                continue

            downloaded += 1

        except Exception as e:
            failed += 1
            print(f"   건너뜀 [idx={idx}]: {type(e).__name__}")
            continue

    new_count = downloaded - skipped
    print(f"   [OK] 신규 {new_count}개, 기존 {skipped}개, 실패 {failed}개")
    return downloaded, skipped, failed


def collect_all(styles=None, count=IMAGES_PER_STYLE, headless=False):
    """
    모든 스타일에 대해 일괄 수집.

    Args:
        styles: 수집할 (라벨, 코드) 리스트. None이면 전역 SNAP_STYLES 사용
        count: 스타일당 수집 개수
        headless: True면 브라우저 창 숨김
    """
    targets = styles if styles is not None else SNAP_STYLES

    print("=" * 60)
    print("무신사 스냅 코디컷 이미지 수집 시작")
    print(f"  스타일: {[s[0] for s in targets]}")
    print(f"  스타일당 목표: {count}개")
    print(f"  저장 루트: {os.path.abspath(BASE_DIR)}")
    print("=" * 60)

    driver = setup_driver(headless=headless)
    total_downloaded = 0

    try:
        for style_label, style_code in targets:
            d, _, _ = collect_one_style(driver, style_label, style_code, count)
            total_downloaded += d

    finally:
        driver.quit()

    print("\n" + "=" * 60)
    print(f"수집 완료: 총 {total_downloaded}개")
    print("수동 검토 권장: 의도와 다른 이미지는 폴더에서 직접 삭제")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    collect_all()
