"""
iHerb 상세페이지 HTML 구조 분석용 스크립트

목적:
    - SQLite DB에서 첫 번째 제품의 URL을 읽어옵니다.
    - Scrapling StealthyFetcher를 사용해 해당 상세페이지 정보를 요청합니다.
    - 상세 설명, 사용법, 경고 사항 등의 구조 및 클래스/ID를 확인하여 셀렉터를 발굴합니다.
"""

import sqlite3
from scrapling.fetchers import StealthyFetcher

DB_PATH = "data/iherb_vitamind.sqlite"

def main():
    print("⏳ DB에서 첫 번째 상세페이지 URL 조회 중...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, product_url FROM products WHERE product_url IS NOT NULL LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("❌ DB에 수집된 제품 URL이 없습니다.")
        return

    pid, url = row
    print(f"✅ 대상 제품: {pid}")
    print(f"✅ URL: {url}")

    print("⏳ StealthyFetcher로 상세페이지 요청 중...")
    fetcher = StealthyFetcher()
    response = fetcher.fetch(url, headless=True, network_idle=True)
    print(f"✅ 응답 상태코드: {response.status}")

    # 주요 특징 태그들 검색 테스트
    print("\n🔍 상세정보 구역 셀렉터 후보 테스트:")
    
    # iHerb 상세페이지는 보통 아래와 같은 구조를 많이 사용합니다.
    test_selectors = {
        "description_section": ".product-description-item",
        "description_detail": "[itemprop='description']",
        "warnings": "#warnings",
        "suggested_use": "#suggested-use",
        "supplement_facts": ".supplement-facts-container",
        # 일반적인 div 구조 후보군
        "prod_overview": "#product-overview",
        "facts_table": "#supplement-facts",
    }

    for name, sel in test_selectors.items():
        found = response.css(sel)
        if found:
            print(f"  ✅ '{sel}' ({name}) -> {len(found)}개 발견 | 텍스트 샘플: {found[0].text.strip()[:60]}...")
        else:
            print(f"  ❌ '{sel}' ({name}) -> 없음")

    # 전체 HTML에서 특정 텍스트나 클래스 힌트 찾아보기
    body_str = response.body.decode("utf-8", errors="replace") if isinstance(response.body, bytes) else str(response.body)
    
    print("\n🔍 힌트 검색:")
    for word in ["description", "suggested-use", "warnings", "supplement-facts"]:
        count = body_str.lower().count(word)
        print(f"  - '{word}' 단어 등장 횟수: {count}회")

if __name__ == "__main__":
    main()
