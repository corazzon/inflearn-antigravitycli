"""
iHerb 제품 상세페이지 수집 및 저장 스크립트 (미수집 우선 배치형)

목적:
    - products 테이블에는 존재하나 product_details에 수집되지 않은 (또는 상세 항목이 비어 있는) 
      상위 10개의 제품 상세 정보만을 우선적으로 수집합니다.
    - 실행할 때마다 새로운 10개의 미수집 정보를 처리하며, 중복 시 업데이트(UPSERT)합니다.
"""

import os
import re
import sqlite3
import time
import json
import random
import pathlib
from datetime import datetime
from scrapling.fetchers import StealthyFetcher

# 경로를 스크립트 파일 기준으로 설정하여 실행 위치 상관없이 작동하도록 절대경로 처리
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "iherb_vitamind.sqlite")
TABLE_NAME = "product_details"
LIMIT_COUNT = 10  # 1회 실행당 수집 개수

def db_초기화(conn: sqlite3.Connection):
    """상세 정보를 저장할 product_details 테이블을 초기화합니다."""
    # 상위 data 폴더가 없으면 생성
    pathlib.Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            product_id        TEXT PRIMARY KEY,
            description       TEXT,
            suggested_use     TEXT,
            other_ingredients TEXT,
            warnings          TEXT,
            supplement_facts  TEXT,  -- JSON string
            collected_at      TEXT,
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        )
    """)
    conn.commit()

def extract_section_text(selector, title_keyword: str) -> str | None:
    """
    #product-overview 내부에서 특정 타이틀(예: Suggested use, Other ingredients, Warnings)을 가진
    구역을 찾아 그 하위 상세 텍스트(prodOverviewDetail, prodOverviewIngred)를 반환합니다.
    """
    rows = selector.css(".item-row, .row")
    for row in rows:
        h3 = row.css("h3")
        if not h3:
            continue
        
        # h3 태그 내부 텍스트 전체(자식 태그 포함) 가져오기
        h3_text = h3[0].get_all_text()
        h3_text_clean = "".join(h3_text).strip().lower()
        
        if title_keyword.lower() in h3_text_clean:
            details = row.css(".prodOverviewDetail, .prodOverviewIngred")
            if details:
                # 내부 텍스트 전체를 줄바꿈을 유지하며 병합
                texts = details[0].get_all_text()
                return "\n".join([t.strip() for t in texts if t.strip()])
    return None

def supplement_facts_파싱(selector) -> str | None:
    """영양 성분 테이블의 데이터를 파싱하여 JSON 문자열로 반환합니다."""
    container = selector.css(".supplement-facts-container table")
    if not container:
        return None
    
    rows = container[0].css("tr")
    facts = {}
    
    for row in rows:
        tds = row.css("td")
        if not tds:
            continue
        
        td_texts = [td.text.strip() for td in tds if td.text]
        td_texts = [re.sub(r"\s+", " ", t) for t in td_texts]
        
        if len(td_texts) == 1:
            val = td_texts[0]
            if "serving size" in val.lower():
                facts["Serving Size"] = val.replace("Serving Size:", "").strip()
            elif "servings per container" in val.lower():
                facts["Servings Per Container"] = val.replace("Servings Per Container:", "").strip()
        elif len(td_texts) >= 2:
            name = td_texts[0]
            amount = td_texts[1]
            dv = td_texts[2] if len(td_texts) > 2 else ""
            facts[name] = {"Amount": amount, "Daily Value": dv}
            
    return json.dumps(facts, ensure_ascii=False)

def main():
    print("=" * 60)
    print("🚀 iHerb 미수집 상세페이지 우선 수집기")
    print(f"   시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    db_초기화(conn)

    # product_details 테이블에 아예 존재하지 않는 (product_id 기준) 제품 상위 10개만 타겟팅
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT p.product_id, p.title, p.product_url 
        FROM products p
        WHERE p.product_url IS NOT NULL 
          AND p.product_id NOT IN (SELECT product_id FROM {TABLE_NAME})
        LIMIT ?
    """, (LIMIT_COUNT,))
    targets = cursor.fetchall()
    
    if not targets:
        print("[INFO] 수집하지 않은 새로운 상세페이지가 더 이상 없습니다. 모든 상세 정보가 완료되었습니다!")
        conn.close()
        return

    print(f"[INFO] 이번 차례에 수집할 미수집 제품 {len(targets)}개를 조회했습니다.")

    fetcher = StealthyFetcher()
    success_count = 0

    for idx, (pid, title, url) in enumerate(targets, 1):
        print(f"\n[{idx}/{len(targets)}] 상세수집: {pid} - {title[:30]}...")
        
        try:
            response = fetcher.fetch(url, headless=True, network_idle=True)
            if response.status != 200:
                print(f"  ❌ HTTP {response.status} 응답 에러 (수집 스킵)")
                continue
            
            # 개선된 파싱 로직 적용
            suggested_use = extract_section_text(response, "Suggested use")
            other_ingredients = extract_section_text(response, "Other ingredients")
            warnings = extract_section_text(response, "Warnings")
            
            # 설명문 (Description)
            overview = response.css("#product-overview")
            description = None
            if overview:
                first_desc = overview[0].css(".col-xs-24 p")
                if first_desc:
                    description = "\n".join([p.text.strip() for p in first_desc[:3] if p.text.strip()])
            
            # 영양성분 정보
            supplement_facts = supplement_facts_파싱(response)

            # DB 저장 (INSERT OR REPLACE로 중복 발생 시 신규 정보로 덮어쓰며 업데이트)
            conn.execute(f"""
                INSERT OR REPLACE INTO {TABLE_NAME} 
                (product_id, description, suggested_use, other_ingredients, warnings, supplement_facts, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pid,
                description,
                suggested_use,
                other_ingredients,
                warnings,
                supplement_facts,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            
            print(f"  ✅ 수집 및 업데이트 완료!")
            print(f"    - Suggested Use   : {'Yes (' + str(len(suggested_use)) + '자)' if suggested_use else 'No'}")
            print(f"    - Ingredients     : {'Yes (' + str(len(other_ingredients)) + '자)' if other_ingredients else 'No'}")
            print(f"    - Warnings        : {'Yes (' + str(len(warnings)) + '자)' if warnings else 'No'}")
            print(f"    - Supplement Facts: {'Yes' if supplement_facts else 'No'}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 에러 발생: {e}")
            
        if idx < len(targets):
            time.sleep(random.uniform(1.5, 3.0))

    conn.close()
    print("\n" + "=" * 60)
    print("📊 상세 수집 완료 요약")
    print(f"  수집 및 덮어쓰기 성공: {success_count} / {len(targets)} 개")
    print("=" * 60)

if __name__ == "__main__":
    main()
