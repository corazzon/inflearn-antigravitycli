# -*- coding: utf-8 -*-
"""
__PROJECT_NAME__ 데이터 동적 수집 스크래퍼 스크립트 템플릿

이 스크립트는 Playwright를 사용해 실시간 보안 통과 키를 자동 획득한 후,
Requests 라이브러리를 사용해 백엔드 API에 다이렉트 쿼리를 날려 대용량 데이터를
범용 5대 속성 구조(name, category, value_1, value_2, detail_text)로 수집하여 안전하고 빠르게 로드합니다.
또한 429/503 등 일시적인 서버 통신 지연에 대응하기 위해 지수 백오프 기반의 재시도 메커니즘을 적용하였습니다.

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
        # 쿼리 파라미터 구성 (사이트 스펙에 맞춰 수정 가능)
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
        
        # 데이터 리스트 추출 (교보문고 및 기본 구조 대응)
        items_list = json_data.get("data", {}).get("bestSeller", [])
        if not items_list:
            # 예비 패턴 매칭 (일반 list 혹은 data 필드 바로 밑)
            items_list = json_data.get("list", json_data.get("data", []))
            
        if not items_list or not isinstance(items_list, list):
            print(f"[Info] {page}페이지에 추가 데이터가 없습니다. 수집을 안전하게 완료합니다.")
            break
            
        for item in items_list:
            # 범용 5대 속성 추출 (도서, 상품, 공고 등의 키 매핑 예외 처리 및 가드)
            rank = item.get("prstRnkn", item.get("rank", ""))
            
            # 1. name (명칭)
            name = item.get("cmdtName", item.get("title", item.get("name", ""))).strip()
            
            # 2. category (분류)
            category = item.get("pbcmName", item.get("chrcName", item.get("company", item.get("category", "")))).strip()
            
            # 3. value_1 (수치 1 - 정가 또는 주요 가격, 지표)
            value_1 = item.get("price", item.get("value_1", 0))
            
            # 4. value_2 (수치 2 - 판매가 또는 만족도, 평점)
            value_2 = item.get("buyRevwRvgr", item.get("sapr", item.get("value_2", 0)))
            
            # 5. detail_text (상세 텍스트)
            detail_text_raw = item.get("inbukCntt", item.get("description", item.get("detail_text", "")))
            detail_text = detail_text_raw.strip() if detail_text_raw else ""
            
            collected_data.append({
                "순위": rank,
                "name": name,
                "category": category,
                "value_1": value_1,
                "value_2": value_2,
                "detail_text": detail_text
            })
            
        page += 1
        time.sleep(random.uniform(0.3, 0.7))
        
        # 안전 장치: 테스트 중 10페이지 한도 제어
        if page > 10:
            break
        
    if not collected_data:
        print("[Error] 수집에 실패하여 적재할 데이터가 존재하지 않습니다.")
        return
        
    df = pd.DataFrame(collected_data)
    # 순위 기준 정렬 시도 (숫자 변환 가드)
    try:
        df["순위"] = pd.to_numeric(df["순위"], errors="coerce")
        df = df.sort_values(by="순위").reset_index(drop=True)
    except Exception:
        pass
    
    # 디렉토리 생성 및 utf-8-sig 명시적 저장 규칙 적용
    output_dir = os.path.dirname("__CSV_PATH__")
    os.makedirs(output_dir, exist_ok=True)
    output_path = "__CSV_PATH__"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[Success] 총 {len(df)}건 데이터가 {output_path} 에 성공적으로 적재 완료되었습니다.")

if __name__ == "__main__":
    main_scraper()
