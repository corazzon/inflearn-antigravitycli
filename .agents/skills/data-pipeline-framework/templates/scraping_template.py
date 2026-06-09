# -*- coding: utf-8 -*-
"""
__PROJECT_NAME__ 데이터 동적 수집 스크래퍼 스크립트

이 스크립트는 Playwright를 사용해 실시간 보안 통과 키를 자동 획득한 후,
Requests 라이브러리를 사용해 백엔드 API에 다이렉트 쿼리를 날려 대용량 데이터를
안전하고 빠르게 수집합니다. 429/503 등 일시적인 서버 통신 지연에 대응하기 위해
지수 백오프(Exponential Backoff) 기반의 재시도 메커니즘을 적용하였습니다.

치환 대상 변수:
- PROJECT_NAME: __PROJECT_NAME__
- TARGET_URL: __TARGET_URL__
- API_URL: __API_URL__
- MAX_RETRIES: __MAX_RETRIES__
- BACKOFF_FACTOR: __BACKOFF_FACTOR__

작성자: Antigravity AI Data Pipeline Framework
"""

import os
import time
import random
import asyncio
from datetime import datetime
import pandas as pd
import requests
from playwright.async_api import async_playwright

def get_today_str():
    return datetime.today().strftime('%Y%m%d')

async def fetch_api_gateway_key():
    target_url = "__TARGET_URL__"
    captured_key = None
    
    print(f"[Scraper] 실시간 API 게이트웨이 키를 획득하기 위해 브라우저를 기동합니다: {target_url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        def handle_request(request):
            nonlocal captured_key
            # 헤더에 x-api-gw-key 혹은 특정 인증 키가 포함되는 패턴 감지
            if "x-api-gw-key" in request.headers:
                captured_key = request.headers["x-api-gw-key"]
        
        page.on("request", handle_request)
        try:
            await page.goto(target_url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            pass
        await browser.close()
        
    return captured_key

def request_with_retry(url, params, headers, max_retries=__MAX_RETRIES__, backoff_factor=__BACKOFF_FACTOR__):
    """지수 백오프 재시도 메커니즘을 적용한 HTTP GET 요청 수행 함수"""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            # 정상 응답 시 바로 반환
            if response.status_code == 200:
                return response
            
            # 재시도할 상태 코드 감지 (429, 500, 502, 503, 504 등)
            if response.status_code in [429, 500, 502, 503, 504]:
                sleep_time = backoff_factor ** attempt + random.uniform(0.5, 1.5)
                print(f"[Warning] HTTP {response.status_code} 발생. {attempt}/{max_retries}회 재시도. {sleep_time:.2f}초 후 재개...")
                time.sleep(sleep_time)
            else:
                # 401, 403, 404 등 재시도가 무의미한 에러는 즉시 중단
                print(f"[Error] 치명적 HTTP {response.status_code} 에러 발생. 재시도를 생략합니다.")
                return response
                
        except requests.exceptions.RequestException as e:
            sleep_time = backoff_factor ** attempt + random.uniform(0.5, 1.5)
            print(f"[Warning] 네트워크 통신 오류 ({e}). {attempt}/{max_retries}회 재시도. {sleep_time:.2f}초 후 재개...")
            time.sleep(sleep_time)
            
    return None

def main_scraper():
    gw_key = asyncio.run(fetch_api_gateway_key())
    
    # 2. API 요청 세팅
    base_url = "__API_URL__"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "__TARGET_URL__",
        "Content-Type": "application/json"
    }
    if gw_key:
        headers["x-api-gw-key"] = gw_key
        
    collected_data = []
    page = 1
    
    print("[Scraper] 동적 페이지 데이터 수집 루프를 기동합니다...")
    while True:
        # 쿼리 파라미터 구성 (사용자 정의 및 치환 가능)
        params = {
            "page": str(page),
            "per": "20",
            "period": "001",
            "dsplDvsnCode": "001",
            "dsplTrgtDvsnCode": "004",
            "saleCmdtClstCode": "33"
        }
        
        print(f"[Scraper] {page}페이지 수집 시도 중...")
        response = request_with_retry(base_url, params, headers)
        
        if not response or response.status_code != 200:
            print(f"[Error] {page}페이지 수집에 최종 실패했습니다. 루프를 종료합니다.")
            break
            
        json_data = response.json()
        
        # 데이터 리스트 추출 (교보문고 data.bestSeller 구조 예시 참조)
        items_list = json_data.get("data", {}).get("bestSeller", [])
        if not items_list:
            print(f"[Info] {page}페이지에 도서 데이터가 없습니다. 수집을 안전하게 완료합니다.")
            break
            
        for item in items_list:
            # 설정 기반 필드 맵 파싱 처리 (__FIELD_MAPPING__)
            rank = item.get("prstRnkn", "")
            title = item.get("cmdtName", "").strip()
            author = item.get("chrcName", "").strip()
            publisher = item.get("pbcmName", "").strip()
            release_date = item.get("rlseDate", "")
            if len(release_date) == 8:
                release_date = f"{release_date[:4]}-{release_date[4:6]}-{release_date[6:]}"
                
            price = item.get("price", 0)
            sale_price = item.get("sapr", 0)
            rating = item.get("buyRevwRvgr", 0.0)
            review_count = item.get("buyRevwNumc", 0)
            cmd_id = item.get("saleCmdtid", "")
            
            # 상세설명 None 방어 예외 처리
            description_raw = item.get("inbukCntt")
            description = description_raw.strip() if description_raw else ""
            
            collected_data.append({
                "순위": rank,
                "도서명": title,
                "저자": author,
                "출판사": publisher,
                "출판일": release_date,
                "정가": price,
                "판매가": sale_price,
                "평점": rating,
                "리뷰수": review_count,
                "상품코드": cmd_id,
                "상세설명": description
            })
            
        page += 1
        time.sleep(random.uniform(0.3, 0.7))
        
    if not collected_data:
        print("[Error] 수집에 실패하여 적재할 데이터가 존재하지 않습니다.")
        return
        
    df = pd.DataFrame(collected_data)
    df = df.sort_values(by="순위").reset_index(drop=True)
    
    # 디렉토리 생성 및 utf-8-sig 명시적 저장 규칙 적용
    output_dir = "__PROJECT_NAME__/data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/kyobo_bestseller.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[Success] 총 {len(df)}건 데이터가 {output_path} 에 성공적으로 적재 완료되었습니다.")

if __name__ == "__main__":
    main_scraper()
