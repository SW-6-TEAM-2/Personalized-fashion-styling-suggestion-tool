"""
의류 이미지 처리 모듈
- 사용자가 업로드한 옷 사진의 배경을 제거하고
- 정사각 캔버스에 정규화한 PNG로 저장
"""

from rembg import remove, new_session
from PIL import Image
import io


def process_clothing_image(input_path: str, output_path: str, target_size: int = 800) -> dict:
    """
    옷 사진 한 장을 받아 배경을 제거하고 정사각 PNG로 저장한다.
    """
    # 1) Rembg 의류 전용 세그멘테이션 모델 세션 준비
    session = new_session("u2net_cloth_seg")

    # 2) 입력 이미지 읽고 배경 제거
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes, session=session)

    # 3) RGBA로 열고 알파 채널 기반 자동 크롭
    img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # 4) 비율 유지 리사이즈 후 정사각 캔버스 중앙 배치
    img.thumbnail((target_size, target_size), Image.LANCZOS)
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    offset = ((target_size - img.width) // 2, (target_size - img.height) // 2)
    canvas.paste(img, offset, img)

    # 5) PNG 저장
    canvas.save(output_path, "PNG")

    return {
        "path": output_path,
        "size": (target_size, target_size),
        "original_bbox": bbox,
    }


# 단독 실행 테스트용
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("사용법: python image_processor.py <입력이미지경로>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = "output.png"
    result = process_clothing_image(input_path, output_path)
    print(f"✅ 처리 완료: {result}")