"""
Yes24 IT/컴퓨터 베스트셀러 EDA PPTX 보고서용 플랫 아이콘 다운로드 및 색상 변환 스크립트

이 스크립트는 Icons8 API를 활용하여 PPTX 제작에 필요한 아이콘들을 다운로드하고,
노르딕 미니멀리즘 스타일의 포인트 컬러인 벽돌색(#b85042, RGB: 184, 80, 66)으로 색상을 변환하여 저장합니다.
"""

import os
import requests
from PIL import Image

# 사용할 아이콘 매핑
icons = {
    "trend": "positive-dynamic",
    "price": "us-dollar-circled",
    "star": "star",
    "book": "open-book",
    "award": "trophy",
    "users": "conference-call",
    "building": "company",
    "percent": "percentage",
    "calendar": "calendar",
    "tag": "price-tag",
    "review": "speech-bubble",
    "spring": "scissors",
    "lightbulb": "idea",
    "chart": "line-chart",
    "key": "key"
}

icon_dir = "yes24/images/icons"
os.makedirs(icon_dir, exist_ok=True)

# 포인트 컬러 벽돌색 (RGB)
TARGET_RGB = (184, 80, 66)

def recolor_image(img_path, target_rgb):
    """
    이미지의 투명(Alpha) 채널을 유지하며 검은색 픽셀을 지정한 RGB 색상으로 변경합니다.
    """
    try:
        img = Image.open(img_path).convert("RGBA")
        data = img.getdata()
        
        new_data = []
        for item in data:
            if item[3] > 0:
                # 불투명한 픽셀에 대해 색상 변경 (알파값은 그대로 유지)
                new_data.append((target_rgb[0], target_rgb[1], target_rgb[2], item[3]))
            else:
                new_data.append(item)
                
        img.putdata(new_data)
        img.save(img_path)
        return True
    except Exception as e:
        print(f"색상 변환 중 에러 발생: {e}")
        return False

print("아이콘 다운로드 및 색상 변환 시작...")
for name, icon_id in icons.items():
    url = f"https://img.icons8.com/ios-filled/100/000000/{icon_id}.png"
    dest_path = os.path.join(icon_dir, f"{name}.png")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(response.content)
            
            # 색상 변환 수행
            if recolor_image(dest_path, TARGET_RGB):
                print(f"다운로드 및 변환 완료: {name}.png ({icon_id})")
            else:
                print(f"다운로드 완료했으나 변환 실패: {name}.png")
        else:
            print(f"다운로드 실패 (상태 코드 {response.status_code}): {name}")
    except Exception as e:
        print(f"에러 발생 {name}: {e}")

print("아이콘 작업 완료.")
