# -*- coding: utf-8 -*-
"""
교보문고 일간 베스트셀러 도서 정보 스크래핑 모듈

이 모듈은 Playwright를 사용하여 교보문고 API 호출에 필요한 게이트웨이 보안 키(x-api-gw-key)를 
동적으로 획득하고, 획득한 키를 바탕으로 백엔드 API를 직접 호출하여 컴퓨터/IT 분야의
일간 베스트셀러 목록(1위 ~ 200위, 전체 10페이지)을 안전하고 신속하게 수집합니다.
수집된 도서 데이터는 정제 후 UTF-8-sig 인코딩의 CSV 파일로 저장됩니다.

주요 기능:
- Playwright를 통한 실시간 x-api-gw-key 헤더 값 자동 추출
- 획득한 키를 기반으로 하는 requests API 병렬/순차 고속 수집
- 순위, 도서명, 저자, 출판사, 출판일, 가격, 평점, 리뷰 수, 상품코드 등 파싱
- 수집된 데이터 정제 및 Pandas DataFrame을 활용한 CSV 파일 저장

작성자: Antigravity AI
생성일: 2026-06-08
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
    """오늘 날짜를 YYYYMMDD 포맷의 문자열로 반환합니다.
    
    Returns:
        str: YYYYMMDD 형태의 오늘 날짜
    """
    return datetime.today().strftime('%Y%m%d')

async def fetch_api_gateway_key():
    """Playwright를 이용해 교보문고 베스트셀러 페이지를 띄우고,
    네트워크 요청 헤더에서 x-api-gw-key 값을 추출합니다.
    
    Returns:
        str: 추출된 x-api-gw-key 값. 실패 시 None 반환.
    """
    target_url = "https://store.kyobobook.co.kr/bestseller/online/daily/domestic/33?page=1"
    captured_key = None
    
    print("[Playwright] 게이트웨이 보안 키(x-api-gw-key) 추출을 위해 브라우저를 시작합니다...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # 키 값을 캡처하기 위한 리스너 이벤트 정의
        def handle_request(request):
            nonlocal captured_key
            if "best-seller/online" in request.url:
                headers = request.headers
                if "x-api-gw-key" in headers:
                    captured_key = headers["x-api-gw-key"]
        
        page.on("request", handle_request)
        
        # 페이지 접속 및 대기
        try:
            await page.goto(target_url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"[Playwright] 페이지 로딩 중 대기 시간 초과 혹은 오류 발생(키가 감지되었을 수 있음): {e}")
            
        await browser.close()
        
    if captured_key:
        print(f"[Playwright] 보안 키 획득 성공: {captured_key[:20]}...{captured_key[-20:]}")
    else:
        print("[Playwright] 보안 키 획득에 실패했습니다.")
        
    return captured_key

def scrape_kyobo_bestseller():
    """교보문고 베스트셀러 데이터를 수집하여 CSV 파일로 저장하는 메인 실행 함수입니다."""
    # 1. API 키 동적 추출
    gw_key = asyncio.run(fetch_api_gateway_key())
    
    if not gw_key:
        # 획득 실패 시, 최근에 탐색된 백업 키를 수동 포백으로 대입해 시도해봅니다.
        print("[Warning] 동적 키 획득에 실패하여 최근 백업 키로 수정을 시도합니다.")
        gw_key = "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..fGckpIc2rocGlaNW.tAQwssCAjZPkubQdkN4mxNuV_XEza4qmGB-uNJwIs032Enxo9a9ElYpvfVw8rEpp3seGnIBo4N9cAjpD56WGPuIkK-xrJfVkp3RRgwreIZoM-As3hxzMqpc-Rs38cnx-GAu9gUNJ.Mwf9x7KZlcYv9TdHt0YSEg"
        
    # 2. API 호출 준비
    base_url = "https://store.kyobobook.co.kr/api/gw/best/best-seller/online"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://store.kyobobook.co.kr/bestseller/online/daily/domestic/33?page=1",
        "Content-Type": "application/json",
        "x-api-gw-key": gw_key
    }
    
    books_data = []
    page = 1
    
    print("[Scraper] 교보문고 일간 베스트셀러 전체 수집을 시작합니다. (동적 페이지 탐색)")
    
    while True:
        params = {
            "page": str(page),
            "per": "20",
            "period": "001",
            "dsplDvsnCode": "001",
            "dsplTrgtDvsnCode": "004",
            "saleCmdtClstCode": "33"  # 컴퓨터/IT
        }
        
        print(f"[Scraper] {page}페이지 요청 중...")
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 401:
                print(f"[Error] 401 Unauthorized 오류 발생. 보안 키가 만료되었거나 비정상적입니다.")
                break
                
            if response.status_code != 200:
                print(f"[Error] {page}페이지 호출 실패 (HTTP {response.status_code})")
                break
                
            json_data = response.json()
            bestseller_list = json_data.get("data", {}).get("bestSeller", [])
            
            if not bestseller_list:
                print(f"[Info] {page}페이지에 도서 데이터가 없습니다. 수집을 완료합니다.")
                break
                
            for item in bestseller_list:
                # 필드 값 추출 및 안전한 예외 처리(None 대치)
                rank = item.get("prstRnkn", "")
                title = item.get("cmdtName", "").strip()
                author = item.get("chrcName", "").strip()
                publisher = item.get("pbcmName", "").strip()
                release_date = item.get("rlseDate", "")
                
                # 날짜 포맷팅 (YYYYMMDD -> YYYY-MM-DD)
                if len(release_date) == 8:
                    release_date = f"{release_date[:4]}-{release_date[4:6]}-{release_date[6:]}"
                    
                price = item.get("price", 0)
                sale_price = item.get("sapr", 0)
                rating = item.get("buyRevwRvgr", 0.0)
                review_count = item.get("buyRevwNumc", 0)
                cmd_id = item.get("saleCmdtid", "")
                description_raw = item.get("inbukCntt")
                description = description_raw.strip() if description_raw else ""
                
                books_data.append({
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
                
        except Exception as e:
            print(f"[Error] {page}페이지 데이터 처리 중 예외 발생: {e}")
            
        # 서버 부하 방지 및 차단 우회를 위한 랜덤 딜레이 적용
        delay = random.uniform(0.3, 0.8)
        time.sleep(delay)
        page += 1
        
    if not books_data:
        print("[Error] 수집된 데이터가 없습니다. 프로세스를 종료합니다.")
        return
        
    # 3. 데이터 저장
    df = pd.DataFrame(books_data)
    
    # 순위 기준으로 정렬 (혹시 섞였을 경우 대비)
    df = df.sort_values(by="순위").reset_index(drop=True)
    
    # data 폴더 생성 확인
    os.makedirs("kyobobooks/data", exist_ok=True)
    
    today_str = get_today_str()
    output_path = f"kyobobooks/data/kyobo_bestseller_{today_str}.csv"
    
    # utf-8-sig 인코딩을 적용해 엑셀에서 바로 열어도 한글이 깨지지 않게 방지합니다.
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n[성공] 총 {len(df)}개의 도서 데이터를 성공적으로 수집하여 저장했습니다.")
    print(f"저장 경로: {output_path}")

if __name__ == "__main__":
    scrape_kyobo_bestseller()
