import time
import os
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 크롬 드라이버 자동 설치 및 설정
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# 무신사 검색 페이지 이동 (예: 워크웨어/시티보이 의류/코디 검색 결과)
driver.get("https://www.musinsa.com/search/goods?keyword=%EC%9B%8C%ED%81%AC%EC%9B%A8%EC%96%B4&gf=A")

# 스크롤을 3번 반복해서 내림
for i in range(3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2) # 이미지가 로딩될 시간 대기

# 무신사 상품 이미지의 공통 클래스명을 사용해 모든 이미지 태그 수집
img_elements = driver.find_elements(By.CSS_SELECTOR, "img[data-mds='Image']")

if not os.path.exists('data'): os.makedirs('data')

# 데이터 가공 및 저장
for idx, img in enumerate(img_elements[:30]):
    # 1. 속성 추출
    url = img.get_attribute("src")

    # 2. 이미지 파일 저장
    file_path = f"data/cloth_{idx}.jpg"
    urllib.request.urlretrieve(url, file_path)

driver.quit() # 브라우저 종료
print("모든 작업이 완료되었습니다.")
