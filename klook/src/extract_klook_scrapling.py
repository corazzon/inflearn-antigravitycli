# -*- coding: utf-8 -*-
"""
scrapling 라이브러리를 사용하여 Klook의 데이터를 수집하는 독립 실행형 스크립트입니다.
scrapling의 StealthyFetcher를 사용하여 봇 탐지 방어막(Datadome)을 안전하게 우회하고,
서울 목적지 페이지의 SSR 데이터 및 메인 페이지의 비동기 API 데이터를 수집하여 CSV로 저장합니다.
"""

import os
import json
import time
import random
import re
import pandas as pd
from scrapling.fetchers import StealthyFetcher

# 저장 경로 설정
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SEOUL_CSV = os.path.join(DATA_DIR, "klook_seoul_activities_scrapling.csv")
MAIN_DESTINATIONS_CSV = os.path.join(DATA_DIR, "klook_popular_destinations_scrapling.csv")
MAIN_ACTIVITIES_CSV = os.path.join(DATA_DIR, "klook_popular_activities_scrapling.csv")

def extract_seoul_activities():
    """
    scrapling을 사용하여 서울 목적지 페이지의 SSR 데이터를 파싱하고 저장합니다.
    """
    url = "https://www.klook.com/ko/destination/c13-seoul/"
    print(f"서울 목적지 페이지 데이터 수집 시작: {url}")
    
    max_retries = 3
    backoff_factor = 2
    response = None
    
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(1.0, 2.0))
            response = StealthyFetcher.fetch(url, headless=True, network_idle=True)
            if response.status == 200:
                print("서울 페이지 HTML 획득 성공!")
                break
            else:
                print(f"접속 시도 실패 (Status: {response.status})")
        except Exception as e:
            print(f"에러 발생: {e}")
            
        if attempt < max_retries - 1:
            sleep_time = backoff_factor ** attempt + random.uniform(0.5, 1.5)
            print(f"{sleep_time:.2f}초 후 재시도합니다...")
            time.sleep(sleep_time)
            
    if not response or response.status != 200:
        print("서울 페이지의 데이터를 로드할 수 없습니다. (차단됨)")
        return

    html_content = response.text
    match = re.search(r"window\.__KLOOK__\s*=\s*(\{.*?\});", html_content)
    if not match:
        match = re.search(r"window\.__KLOOK__\s*=\s*(\{.*?\}\n)", html_content)

    if not match:
        print("HTML 소스에서 window.__KLOOK__ 상태 객체를 추출하지 못했습니다.")
        return

    try:
        klook_json = json.loads(match.group(1))
        page_data = klook_json.get("data", {}).get("0", {}).get("pageData", {})
        sections = page_data.get("page", {}).get("body", {}).get("sections", [])
        
        target_section = next(
            (sec for sec in sections if sec.get("meta", {}).get("name") == "DestinationExploreTtdActs"),
            None
        )
        
        if not target_section:
            print("서울 추천 액티비티 섹션(DestinationExploreTtdActs)을 찾지 못했습니다.")
            return

        cards = target_section.get("body", {}).get("content", {}).get("data", {}).get("cards", [])
        print(f"총 {len(cards)}개의 서울 액티비티 상품을 확인했습니다.")
        
        parsed_activities = []
        for card in cards:
            c_data = card.get("data", {})
            if not c_data:
                continue
            
            title = c_data.get("title", "")
            sub_title = c_data.get("sub_title", "")
            city_name = c_data.get("city_name", "")
            
            price_info = c_data.get("price", {})
            original_price = price_info.get("market_price", {}).get("value_with_symbol", "")
            selling_price = price_info.get("sell_price", {}).get("value_with_symbol", "")
            
            review_info = c_data.get("review_obj", {})
            rating = review_info.get("rating", "")
            review_count = review_info.get("review_num", "")
            
            deep_link = c_data.get("deep_link", "")
            full_link = f"https://www.klook.com{deep_link}" if deep_link.startswith("/") else deep_link
            cover_url = c_data.get("cover_url", "")
            
            parsed_activities.append({
                "상품명": title,
                "부제목": sub_title,
                "도시": city_name,
                "정가": original_price,
                "판매가": selling_price,
                "평점": rating,
                "리뷰수": review_count,
                "상세링크": full_link,
                "이미지URL": cover_url
            })
            
        if parsed_activities:
            df = pd.DataFrame(parsed_activities)
            df.to_csv(SEOUL_CSV, index=False, encoding="utf-8-sig")
            print(f"서울 액티비티 저장 완료: {SEOUL_CSV}")
        else:
            print("파싱된 서울 액티비티 목록이 비어있습니다.")
            
    except Exception as e:
        print(f"서울 데이터 파싱 중 에러 발생: {e}")


def extract_main_destinations():
    """
    scrapling을 사용하여 Klook 메인 페이지의 인기 목적지(Where to Next) 데이터를 수집합니다.
    """
    api_url = "https://www.klook.com/v1/platformbffsrv/homepage/service/get_where_to_next?brand=&carrier=&city_id=0&country_id=10&roaming=&sim_region_code=&source=human&system_platform=desktop"
    print(f"Klook 메인 인기 목적지 API 수집 시작: {api_url}")
    
    max_retries = 3
    backoff_factor = 2
    response = None
    
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(1.0, 2.0))
            response = StealthyFetcher.fetch(api_url, headless=True)
            if response.status == 200:
                print("인기 목적지 API 호출 성공!")
                break
            else:
                print(f"접속 시도 실패 (Status: {response.status})")
        except Exception as e:
            print(f"에러 발생: {e}")
            
        if attempt < max_retries - 1:
            sleep_time = backoff_factor ** attempt + random.uniform(0.5, 1.5)
            print(f"{sleep_time:.2f}초 후 재시도합니다...")
            time.sleep(sleep_time)

    if not response or response.status != 200:
        print("인기 목적지 API 데이터를 불러올 수 없습니다. (차단됨)")
        return

    try:
        data = response.json()
        items = data.get("result", {}).get("items", [])
        print(f"총 {len(items)}개의 메인 인기 목적지 카드를 획득했습니다.")
        
        dest_list = []
        for item in items:
            c_data = item.get("data", {})
            if not c_data:
                continue
            
            title = c_data.get("title", "")
            sub_title = c_data.get("sub_title", "")
            img_url = c_data.get("img_url", "")
            deep_link = c_data.get("deep_link", "")
            
            dest_list.append({
                "도시명": title,
                "활동수": sub_title,
                "상세링크": deep_link,
                "이미지URL": img_url
            })
            
        if dest_list:
            df = pd.DataFrame(dest_list)
            df.to_csv(MAIN_DESTINATIONS_CSV, index=False, encoding="utf-8-sig")
            print(f"메인 인기 목적지 저장 완료: {MAIN_DESTINATIONS_CSV}")
        else:
            print("파싱된 메인 인기 목적지 목록이 비어있습니다.")
            
    except Exception as e:
        print(f"메인 인기 목적지 데이터 파싱 중 에러 발생: {e}")


def extract_main_popular_activities():
    """
    scrapling을 사용하여 Klook 메인 페이지의 인기 액티비티 호출 데이터를 수집합니다.
    """
    api_url = "https://www.klook.com/v1/platformbffsrv/homepage/service/get_pop_activity?city_id=0&country_id=0&limit=12&source=human&system_platform=desktop"
    print(f"Klook 메인 인기 액티비티 API 수집 시작: {api_url}")
    
    max_retries = 3
    backoff_factor = 2
    response = None
    
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(1.0, 2.0))
            response = StealthyFetcher.fetch(api_url, headless=True)
            if response.status == 200:
                print("인기 액티비티 API 호출 성공!")
                break
            else:
                print(f"접속 시도 실패 (Status: {response.status})")
        except Exception as e:
            print(f"에러 발생: {e}")
            
        if attempt < max_retries - 1:
            sleep_time = backoff_factor ** attempt + random.uniform(0.5, 1.5)
            print(f"{sleep_time:.2f}초 후 재시도합니다...")
            time.sleep(sleep_time)

    if not response or response.status != 200:
        print("인기 액티비티 API 데이터를 불러올 수 없습니다. (차단됨)")
        return

    try:
        data = response.json()
        items = data.get("result", {}).get("items", [])
        print(f"총 {len(items)}개의 메인 인기 상품 카드를 획득했습니다.")
        
        act_list = []
        for item in items:
            c_data = item.get("data", {})
            if not c_data:
                continue
            
            title = c_data.get("title", "")
            sub_title = c_data.get("sub_title", "")
            city_name = c_data.get("city_name", "")
            
            price_info = c_data.get("price", {})
            # API JSON 필드에 맞춰 파싱 수행
            original_price = price_info.get("market_price", "")
            selling_price = price_info.get("selling_price", "")
            
            review_info = c_data.get("review", {})
            rating = review_info.get("star", "")
            review_count = review_info.get("number", "")
            
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
            df = pd.DataFrame(act_list)
            df.to_csv(MAIN_ACTIVITIES_CSV, index=False, encoding="utf-8-sig")
            print(f"메인 인기 액티비티 저장 완료: {MAIN_ACTIVITIES_CSV}")
        else:
            print("파싱된 메인 인기 액티비티 목록이 비어있습니다.")
            
    except Exception as e:
        print(f"메인 데이터 파싱 중 에러 발생: {e}")

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    extract_seoul_activities()
    print("-" * 50)
    extract_main_destinations()
    print("-" * 50)
    extract_main_popular_activities()
