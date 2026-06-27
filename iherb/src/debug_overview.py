"""
iHerb 상세페이지 #product-overview 영역 상세 분석 스크립트

목적:
    - #product-overview 영역의 원본 HTML을 추출하여 상세설명, 사용법, 경고 사항 등의 구조 및 태그를 파악합니다.
"""

import sqlite3
from scrapling.fetchers import StealthyFetcher

DB_PATH = "data/iherb_vitamind.sqlite"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_url FROM products WHERE product_url IS NOT NULL LIMIT 1")
    url = cursor.fetchone()[0]
    conn.close()

    fetcher = StealthyFetcher()
    response = fetcher.fetch(url, headless=True, network_idle=True)
    
    overview = response.css("#product-overview")
    if overview:
        print("=== #product-overview HTML 내용 ===")
        print(overview[0].html_content)
    else:
        print("❌ #product-overview 영역을 찾을 수 없습니다.")

    facts = response.css(".supplement-facts-container")
    if facts:
        print("\n=== .supplement-facts-container HTML 내용 ===")
        print(facts[0].html_content[:1500])  # 너무 길 수 있으므로 1500자 제한

if __name__ == "__main__":
    main()
