# -*- coding: utf-8 -*-
"""
Klook 서울 목적지 페이지의 액티비티 상품 목록을 수집하는 스크립트입니다.
Datadome 보안 차단을 방지하기 위해 Playwright 브라우저를 구동하고,
SSR(서버 사이드 렌더링)로 삽입된 window.__KLOOK__ 전역 변수에서 데이터를 직접 추출합니다.
"""

import os
import json
import time
import random
import pandas as pd
from patchright.sync_api import sync_playwright

# 저장 경로 설정
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "klook_seoul_activities.csv")

def extract_klook_data():
    # 데이터 저장 폴더가 없는 경우 자동 생성
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
        
        # 지수 백오프 기반 재시도 로직
        max_retries = 3
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                url = "https://www.klook.com/ko/destination/c13-seoul/"
                print(f"[{attempt + 1}/{max_retries}] Klook 서울 페이지 접속 시도: {url}")
                
                # 랜덤 대기 추가
                time.sleep(random.uniform(1.0, 2.0))
                
                # 페이지 이동 및 네트워크 대기
                response = page.goto(url, wait_until="networkidle", timeout=30000)
                
                if response and response.status == 200:
                    print("페이지 로드 성공!")
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

        # 페이지가 캡차에 걸렸는지 잠시 확인 및 대기
        time.sleep(random.uniform(1.5, 2.5))
        
        # window.__KLOOK__ 객체 추출
        print("SSR 상태 데이터(window.__KLOOK__)를 추출하는 중...")
        try:
            klook_data = page.evaluate("() => window.__KLOOK__ ? JSON.stringify(window.__KLOOK__) : null")
            if not klook_data:
                raise ValueError("window.__KLOOK__ 데이터를 찾을 수 없습니다. (보안 차단 또는 페이지 로드 미완료)")
            
            parsed_data = json.loads(klook_data)
        except Exception as e:
            print(f"데이터 추출 중 에러가 발생했습니다: {e}")
            browser.close()
            return
        
        browser.close()

    # 데이터 파싱 프로세스
    try:
        # window.__KLOOK__.data["0"].pageData.page.body.sections 구조 접근
        page_data = parsed_data.get("data", {}).get("0", {}).get("pageData", {})
        sections = page_data.get("page", {}).get("body", {}).get("sections", [])
        
        # 'DestinationExploreTtdActs' 섹션 탐색 (추천 액티비티 목록 포함)
        target_section = next(
            (sec for sec in sections if sec.get("meta", {}).get("name") == "DestinationExploreTtdActs"),
            None
        )
        
        if not target_section:
            print("목록을 담고 있는 'DestinationExploreTtdActs' 섹션을 찾지 못했습니다.")
            return

        cards = target_section.get("body", {}).get("content", {}).get("data", {}).get("cards", [])
        print(f"총 {len(cards)}개의 상품 카드를 확인했습니다.")
        
        parsed_activities = []
        for card in cards:
            c_data = card.get("data", {})
            if not c_data:
                continue
            
            # 정보 파싱
            title = c_data.get("title", "")
            sub_title = c_data.get("sub_title", "")
            city_name = c_data.get("city_name", "")
            
            # 가격 정보
            price_info = c_data.get("price", {})
            original_price = price_info.get("market_price", {}).get("value_with_symbol", "")
            selling_price = price_info.get("sell_price", {}).get("value_with_symbol", "")
            
            # 평점 및 리뷰 개수
            review_info = c_data.get("review_obj", {})
            rating = review_info.get("rating", "")
            review_count = review_info.get("review_num", "")
            
            # 상세 링크 및 이미지
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
            
        # DataFrame 변환 및 Excel 호환 인코딩(utf-8-sig)으로 CSV 저장
        df = pd.DataFrame(parsed_activities)
        df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
        print(f"데이터 수집 및 저장 완료: {OUTPUT_PATH}")
        
    except Exception as e:
        print(f"데이터 분석 및 가공 실패: {e}")

if __name__ == "__main__":
    extract_klook_data()
