"""
SSG.COM 해피바이 특가 수집 엔진

이 스크립트는 SSG.COM의 해피바이(happybuy) 특가 페이지에 매립된 JSON 데이터를 파싱하여,
오늘의 특가 상품 정보(상품명, 정상가, 판매가, 할인율, 상품 상세 URL, 이미지 URL, 수집 일시)를 수집합니다.
수집된 데이터는 'ssg_com/data/' 폴더 아래에 'happybuy_YYYYMMDD_HHMMSS.csv' 파일로 저장됩니다.
"""
# -*- coding: utf-8 -*-
import os
import re
import csv
import json
import time
import random
import datetime
import requests
from bs4 import BeautifulSoup
from git_hook import execute_git_commit

# 대상 URL
TARGET_URL = "https://www.ssg.com/page/pc/SpecialPrice/happybuy.ssg"

# HTTP 요청 헤더 설정
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

def fetch_html_with_retry(url, headers, max_retries=3, backoff_factor=2):
    """
    Exponential Backoff를 적용하여 지정된 URL의 HTML 소스를 가져옵니다.
    """
    delay = 1.0  # 초기 딜레이 초
    for attempt in range(1, max_retries + 1):
        try:
            # 네트워크 요청 전 서버 부하 방지를 위해 랜덤 딜레이를 부여
            time.sleep(random.uniform(0.3, 0.8))
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Rate limit(429) 이나 서버 오류(5xx)에 대해 재시도 유도
            if response.status_code == 429 or response.status_code >= 500:
                print(f"[경고] HTTP 상태 코드 {response.status_code} 수신. 재시도 중... ({attempt}/{max_retries})")
                time.sleep(delay)
                delay *= backoff_factor
                continue
                
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.RequestException as e:
            print(f"[오류] 네트워크 오류 발생: {e}. 재시도 중... ({attempt}/{max_retries})")
            if attempt == max_retries:
                raise e
            time.sleep(delay)
            delay *= backoff_factor

def parse_ssg_happybuy(html_content):
    """
    SSG 해피바이 HTML에서 Next.js 매립 JSON을 파싱하여 상품 목록을 추출합니다.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    target_json = None
    
    # JSON이 매립된 스크립트 태그 탐색
    for s in soup.find_all("script"):
        if s.string and "initialZustandApplicationState" in s.string:
            json_str = s.string[s.string.find('{'):s.string.rfind('}')+1]
            try:
                target_json = json.loads(json_str)
                break
            except json.JSONDecodeError:
                continue
                
    if not target_json:
        raise ValueError("HTML 내에서 상품 데이터를 포함한 JSON 스크립트를 찾지 못했습니다.")
        
    # JSON 트리에서 상품 목록 블록 탐색
    queries = target_json.get("props", {}).get("pageProps", {}).get("dehydratedState", {}).get("queries", [])
    if not queries:
        raise ValueError("JSON 데이터 내에 queries 노드가 없습니다.")
        
    page_data = queries[0].get("state", {}).get("data", {}).get("pages", [{}])[0]
    area_list = page_data.get("areaList", [[]])[0]
    
    items = []
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for block in area_list:
        item_list = block.get("itemList", [])
        for raw_item in item_list:
            # 1. 상품명
            item_name = raw_item.get("itemNm") or raw_item.get("itemName") or "상품명 없음"
            
            # 2. 가격 데이터 정제 (쉼표 및 원화 표시 제거 후 숫자만 추출)
            def clean_price(price_str):
                if not price_str:
                    return ""
                cleaned = re.sub(r"[^\d]", "", str(price_str))
                return int(cleaned) if cleaned else ""
                
            final_price = clean_price(raw_item.get("finalPrice"))
            strike_out_price = clean_price(raw_item.get("strikeOutPrice"))
            
            # 3. 할인율
            discount_rate = raw_item.get("discountRate") or ""
            if discount_rate:
                discount_rate = f"{discount_rate}%"
                
            # 정상가가 비어 있고 할인율이 존재한다면 정상가 역산 시도
            if not strike_out_price and final_price and discount_rate:
                try:
                    rate = int(re.sub(r"[^\d]", "", discount_rate))
                    if 0 < rate < 100:
                        strike_out_price = int(final_price / (1 - rate / 100))
                except:
                    pass
            
            # 만약 정상가 정보가 최종 가격보다 낮거나 비어 있다면 최종 가격으로 대치
            if not strike_out_price or (isinstance(strike_out_price, int) and isinstance(final_price, int) and strike_out_price < final_price):
                strike_out_price = final_price

            # 4. 상세 URL (itemUrl 제공 시 사용, 없으면 ID 기반 조립)
            item_id = raw_item.get("itemId") or ""
            item_url = raw_item.get("itemUrl") or raw_item.get("itemDetailLink") or ""
            if not item_url and item_id:
                item_url = f"https://www.ssg.com/item/itemView.ssg?itemId={item_id}"
                
            # 5. 이미지 URL
            image_url = raw_item.get("itemImgUrl") or ""
            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url
                
            items.append({
                "상품명": item_name,
                "정상가": strike_out_price,
                "판매가": final_price,
                "할인율": discount_rate,
                "상품상세링크": item_url,
                "이미지링크": image_url,
                "수집일시": current_time
            })
            
    return items

def save_to_csv(items, output_dir="ssg_com/data"):
    """
    수집된 상품 리스트를 CSV 파일로 저장합니다. 
    MS 엑셀 한글 깨짐 방지를 위해 'utf-8-sig' 인코딩을 적용합니다.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"happybuy_{timestamp}.csv"
    file_path = os.path.join(output_dir, file_name)
    
    fields = ["상품명", "정상가", "판매가", "할인율", "상품상세링크", "이미지링크", "수집일시"]
    
    with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow(item)
            
    print(f"[성공] 총 {len(items)}개의 특가 상품을 CSV로 저장 완료: {file_path}")
    return file_path

def main():
    print("SSG.COM 해피바이 특가 상품 수집을 시작합니다...")
    try:
        html = fetch_html_with_retry(TARGET_URL, HEADERS)
        items = parse_ssg_happybuy(html)
        if items:
            file_path = save_to_csv(items)
            # 수집 완료 후 자동 커밋 실행 (Git Hook)
            execute_git_commit([file_path], f"[데이터 수집] {os.path.basename(file_path)}")
        else:
            print("[경고] 수집된 상품이 없습니다.")
    except Exception as e:
        print(f"[실패] 수집 진행 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
