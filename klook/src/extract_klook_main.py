# -*- coding: utf-8 -*-
"""
Klook 메인 페이지(첫 페이지)의 인기 목적지 및 인기 액티비티 목록을 수집하는 독립형 스크립트입니다.
Playwright의 네트워크 응답 가로채기(Response interception) 기능과 세션 재사용 방식을 활용하여,
Datadome 보안을 우회하고 비동기로 호출되는 API 데이터를 안전하게 수집 및 CSV로 저장합니다.
"""

import os
import json
import time
import random
import pandas as pd
from patchright.sync_api import sync_playwright

# 저장 경로 설정
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DESTINATIONS_CSV = os.path.join(DATA_DIR, "klook_popular_destinations.csv")
ACTIVITIES_CSV = os.path.join(DATA_DIR, "klook_popular_activities.csv")

# 가로챈 데이터를 임시 보관할 사전
captured_data = {
    "destinations": None,
    "activities": None
}

def response_handler(response):
    """
    Playwright 네트워크 응답을 가로채어 Klook 비동기 API 데이터를 수집합니다.
    """
    url = response.url
    try:
        # 인기 목적지 API 감지
        if "get_where_to_next" in url and response.status == 200:
            print(f"인기 목적지 API 감지됨: {url[:80]}...")
            captured_data["destinations"] = response.json()
        
        # 인기 액티비티 API 감지
        elif "get_pop_activity" in url and response.status == 200:
            print(f"인기 액티비티 API 감지됨: {url[:80]}...")
            captured_data["activities"] = response.json()
    except Exception as e:
        # JSON 파싱 실패 등 예외 방어
        pass

def scrape_klook_main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    print("Playwright 브라우저를 구동하는 중...")
    with sync_playwright() as p:
        # patchright 자체 내장 Chromium 브라우저를 사용하여 패치 기능이 완벽히 동작하도록 합니다.
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # User-Agent 수동 조작을 배제하여 핑거프린트 불일치를 방지합니다.
        context = browser.new_context(
            locale="ko-KR",
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()
        
        # navigator.webdriver 탐지를 우회하기 위한 초기화 스크립트 삽입
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 네트워크 응답 이벤트 리스너 등록
        page.on("response", response_handler)
        
        max_retries = 3
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                target_url = "https://www.klook.com/ko/"
                print(f"[{attempt + 1}/{max_retries}] Klook 메인 페이지 접속 시도: {target_url}")
                
                # 차단 방지를 위한 랜덤 지연
                time.sleep(random.uniform(1.0, 2.0))
                
                # 페이지 이동 및 네트워크 대기
                response = page.goto(target_url, wait_until="networkidle", timeout=45000)
                
                if response and response.status == 200:
                    print("메인 페이지 로드 완료!")
                    break
                else:
                    status_code = response.status if response else "No Response"
                    print(f"페이지 로드 오류 (Status: {status_code})")
                    if attempt == max_retries - 1:
                        raise Exception(f"HTTP 에러 상태 코드: {status_code}")
            except Exception as e:
                print(f"에러 발생: {e}")
                if attempt < max_retries - 1:
                    sleep_time = backoff_factor ** attempt + random.uniform(0.5, 1.5)
                    print(f"{sleep_time:.2f}초 후 재시도합니다...")
                    time.sleep(sleep_time)
                else:
                    print("최대 재시도 횟수를 초과했습니다.")
                    browser.close()
                    return

        # 비동기 요청이 완료되어 데이터가 캡처될 때까지 추가 딜레이 부여하며 스크롤 수행
        print("비동기 API 데이터 수집을 기다리는 중...")
        for _ in range(5):
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(random.uniform(0.5, 1.0))
            
            # 목적 데이터가 모두 수집되었는지 확인
            if captured_data["destinations"] and captured_data["activities"]:
                print("필요한 비동기 API 데이터를 모두 성공적으로 가로챘습니다.")
                break
                
        browser.close()

    # 데이터 후처리 및 CSV 파일 저장
    # 1. 인기 목적지 데이터 가공
    if captured_data["destinations"]:
        try:
            dest_list = []
            result_list = captured_data["destinations"].get("result", [])
            for item in result_list:
                for dest in item.get("dest_list", []):
                    dest_list.append({
                        "도시ID": dest.get("city_id", ""),
                        "도시명": dest.get("city_name", ""),
                        "국가명": dest.get("country_name", ""),
                        "상세링크": dest.get("target_url", ""),
                        "이미지URL": dest.get("image_url", "")
                    })
            
            if dest_list:
                df_dest = pd.DataFrame(dest_list)
                df_dest.to_csv(DESTINATIONS_CSV, index=False, encoding="utf-8-sig")
                print(f"인기 목적지 저장 완료: {DESTINATIONS_CSV}")
            else:
                print("인기 목적지 목록이 비어있습니다.")
        except Exception as e:
            print(f"인기 목적지 가공 중 에러 발생: {e}")
    else:
        print("인기 목적지 데이터를 수집하지 못했습니다.")

    # 2. 인기 액티비티 데이터 가공
    if captured_data["activities"]:
        try:
            act_list = []
            # API 반환값의 result 내의 cards 정보 파싱
            cards = captured_data["activities"].get("result", {}).get("cards", [])
            for card in cards:
                c_data = card.get("data", {})
                if not c_data:
                    continue
                
                title = c_data.get("title", "")
                sub_title = c_data.get("sub_title", "")
                city_name = c_data.get("city_name", "")
                
                # 가격 추출
                price_info = c_data.get("price", {})
                original_price = price_info.get("market_price", {}).get("value_with_symbol", "")
                selling_price = price_info.get("sell_price", {}).get("value_with_symbol", "")
                
                # 리뷰 추출
                review_info = c_data.get("review_obj", {})
                rating = review_info.get("rating", "")
                review_count = review_info.get("review_num", "")
                
                deep_link = c_data.get("deep_link", "")
                full_link = f"https://www.klook.com{deep_link}" if deep_link.startswith("/") else deep_link
                cover_url = c_data.get("cover_url", "")
                
                act_list.append({
                    "상품명": title,
                    "부제목": sub_title,
                    "도시명": city_name,
                    "정가": original_price,
                    "판매가": selling_price,
                    "평점": rating,
                    "리뷰수": review_count,
                    "상세링크": full_link,
                    "이미지URL": cover_url
                })
            
            if act_list:
                df_act = pd.DataFrame(act_list)
                df_act.to_csv(ACTIVITIES_CSV, index=False, encoding="utf-8-sig")
                print(f"인기 액티비티 저장 완료: {ACTIVITIES_CSV}")
            else:
                print("인기 액티비티 목록이 비어있습니다.")
        except Exception as e:
            print(f"인기 액티비티 가공 중 에러 발생: {e}")
    else:
        print("인기 액티비티 데이터를 수집하지 못했습니다.")

if __name__ == "__main__":
    scrape_klook_main()
