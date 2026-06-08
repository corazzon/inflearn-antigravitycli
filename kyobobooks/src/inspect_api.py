# -*- coding: utf-8 -*-
"""
교보문고 베스트셀러 페이지 API 네트워크 요청 탐색 스크립트

이 스크립트는 Playwright를 사용하여 교보문고의 일간 베스트셀러 페이지를 렌더링하고,
백그라운드에서 발생하는 API 네트워크 요청(URL, Method, Headers, Payload)을 감지하고 기록합니다.
감지된 정보는 kyobobooks/docs/scaraping_prompt.md 파일 작성을 돕기 위한 레퍼런스로 활용됩니다.

주요 기능:
- Headless 브라우저를 통한 동적 페이지 렌더링 및 로딩
- 네트워크 요청(request) 모니터링 및 API 키워드가 포함된 요청 필터링
- API 요청의 세부 정보(URL, Method, Headers, Payload) 추출 및 출력

작성자: Antigravity AI
생성일: 2026-06-08
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_network():
    url = "https://store.kyobobook.co.kr/bestseller/online/daily/domestic/33?page=1"
    
    print("[1/3] Playwright 브라우저를 시작합니다...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 실제 사용자처럼 보이도록 User-Agent 설정
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        api_requests = []
        
        # 네트워크 요청 이벤트 리스너 등록
        async def handle_request(request):
            req_url = request.url
            # 교보문고 API 게이트웨이나 베스트셀러 관련 API 패턴 필터링
            if "api" in req_url or "bestseller" in req_url or "product" in req_url:
                # 불필요한 정적 파일이나 이미지, 폰트 요청 등은 제외
                if any(ext in req_url for ext in [".png", ".jpg", ".jpeg", ".gif", ".css", ".js", ".woff", ".svg"]):
                    return
                
                try:
                    payload = request.post_data if request.method == "POST" else None
                except Exception:
                    payload = None
                    
                api_requests.append({
                    "url": req_url,
                    "method": request.method,
                    "headers": request.headers,
                    "payload": payload
                })
        
        page.on("request", handle_request)
        
        # 네트워크 응답 이벤트 리스너 등록
        async def handle_response(response):
            res_url = response.url
            if "best-seller/online" in res_url:
                try:
                    status = response.status
                    text = await response.text()
                    req_headers = response.request.headers
                    
                    # 파일에 전체 로그 저장
                    with open("kyobobooks/docs/api_debug.txt", "w", encoding="utf-8") as f:
                        f.write(f"URL: {res_url}\n")
                        f.write(f"Status: {status}\n\n")
                        f.write("=== Request Headers ===\n")
                        f.write(json.dumps(req_headers, indent=2, ensure_ascii=False))
                        f.write("\n\n=== Response Body ===\n")
                        f.write(text)
                    print(f"\n[성공] API 응답을 파일에 저장했습니다: kyobobooks/docs/api_debug.txt")
                except Exception as e:
                    print(f"응답 저장 중 에러 발생: {e}")
                    
        page.on("response", handle_response)
        
        print(f"[2/3] 페이지에 접속합니다: {url}")
        # 네트워크가 어느 정도 안정될 때까지 대기
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"페이지 로딩 중 타임아웃 발생 (일부 데이터는 감지되었을 수 있습니다): {e}")
            
        print("[3/3] 페이지 로드가 완료되었습니다. 5초간 추가 대기하며 API 요청을 감지합니다...")
        await asyncio.sleep(5)
        
        await browser.close()
        
        print(f"\n=== 감지된 API 요청 목록 (총 {len(api_requests)}개) ===")
        found_target = False
        for i, req in enumerate(api_requests):
            # 베스트셀러 목록 데이터 조회와 직접 연관된 것으로 보이는 API 필터링 출력
            # 보통 bestseller, product, list, gw/pub 등의 키워드가 포함됨
            is_potential = any(k in req["url"] for k in ["bestseller", "product", "gw", "pub", "list", "search"])
            
            if is_potential:
                found_target = True
                print(f"\n[{i+1}] [POTENTIAL TARGET] {req['method']} - {req['url']}")
                print("--- Headers ---")
                print(json.dumps(req["headers"], indent=2, ensure_ascii=False))
                if req["payload"]:
                    print("--- Payload ---")
                    print(req["payload"])
        
        if not found_target:
            print("특별한 베스트셀러 대상 API를 특정하지 못했습니다. 전체 감지된 API를 출력합니다:")
            for i, req in enumerate(api_requests[:10]):  # 상위 10개만 출력
                print(f"[{i+1}] {req['method']} - {req['url']}")

if __name__ == "__main__":
    asyncio.run(inspect_network())
