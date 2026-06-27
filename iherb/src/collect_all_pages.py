"""
iHerb 비타민D 제품 목록 - 전체 페이지 수집 스크립트

목적:
    - Scrapling StealthyFetcher로 iHerb 비타민D 카테고리 전체 페이지를 순회하며
      제품 정보를 수집하고 SQLite DB에 페이지별로 즉시 저장합니다.
    - 중간에 중단되더라도 이미 저장된 데이터는 보존됩니다.

실행:
    uv run src/collect_all_pages.py

저장 위치:
    data/iherb_vitamind.sqlite (테이블: products)

수집 필드 (test_one_page.py에서 확인된 셀렉터 기준):
    - product_id    : 제품 고유 코드 (SKU)
    - title         : 제품 전체 명칭
    - brand         : 브랜드명 (제품명에서 추출)
    - price         : 현재 판매 가격 (원, 정수)
    - rating        : 평점 (0.0~5.0)
    - review_count  : 리뷰 수
    - product_url   : 제품 상세 페이지 URL
    - image_url     : 제품 이미지 URL
    - page_no       : 수집된 페이지 번호
    - collected_at  : 수집 일시
"""

import re
import time
import sqlite3
import random
import pathlib
from datetime import datetime

from scrapling.fetchers import StealthyFetcher

# ──────────────────────────────────────────────────────────────
# 설정 상수
# ──────────────────────────────────────────────────────────────
BASE_URL      = "https://kr.iherb.com/c/vitamin-d"
DB_PATH       = "data/iherb_vitamind.sqlite"
TABLE_NAME    = "products"
MAX_RETRY     = 3          # 페이지당 최대 재시도 횟수
RETRY_DELAY   = 8.0        # 재시도 대기 시간 (초)
MIN_DELAY     = 1.0        # 페이지 간 최소 대기 (초)
MAX_DELAY     = 3.0        # 페이지 간 최대 대기 (초)
CONSEC_FAIL   = 3          # 연속 실패 시 중단

# 실제 페이지에서 확인된 CSS 셀렉터
SELECTORS = {
    "product_card": "div.product-cell",
    "product_url":  "a.product-link",
    "title":        "[itemprop='name']",
    "price_meta":   "meta[itemprop='price']",
    "rating_link":  "a.stars",
    "review_count": "a.rating-count span",
    "image":        "img[itemprop='image']",
    "sku":          "div[itemprop='sku']",
}


# ──────────────────────────────────────────────────────────────
# DB 초기화
# ──────────────────────────────────────────────────────────────
def db_초기화(db_path: str) -> sqlite3.Connection:
    """SQLite DB와 products 테이블을 생성합니다."""
    pathlib.Path("data").mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id    TEXT,
            title         TEXT,
            brand         TEXT,
            price         INTEGER,
            rating        REAL,
            review_count  INTEGER,
            product_url   TEXT,
            image_url     TEXT,
            page_no       INTEGER,
            collected_at  TEXT,
            UNIQUE(product_id)          -- 중복 방지
        )
    """)
    conn.commit()
    print(f"[INFO] DB 초기화 완료: {db_path}")
    return conn


def db_저장(conn: sqlite3.Connection, 제품_목록: list, page_no: int) -> int:
    """제품 목록을 SQLite에 즉시 저장합니다. 저장된 행 수를 반환합니다."""
    저장수 = 0
    for 제품 in 제품_목록:
        try:
            conn.execute(f"""
                INSERT OR IGNORE INTO {TABLE_NAME}
                    (product_id, title, brand, price, rating,
                     review_count, product_url, image_url, page_no, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                제품.get("product_id"),
                제품.get("title"),
                제품.get("brand"),
                제품.get("price"),
                제품.get("rating"),
                제품.get("review_count"),
                제품.get("product_url"),
                제품.get("image_url"),
                page_no,
                제품.get("collected_at"),
            ))
            저장수 += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  [WARN] DB 저장 오류 (product_id={제품.get('product_id')}): {e}")
    conn.commit()
    return 저장수


# ──────────────────────────────────────────────────────────────
# 파싱 함수
# ──────────────────────────────────────────────────────────────
def css_first(element, selector):
    """첫 번째 매칭 요소를 반환합니다. 없으면 None."""
    결과 = element.css(selector)
    return 결과[0] if 결과 else None


def 제품_파싱(카드, page_no: int) -> dict:
    """제품 카드 Element에서 데이터를 추출합니다."""
    제품 = {}

    # 제품 URL
    url_요소 = css_first(카드, SELECTORS["product_url"])
    if url_요소:
        href = url_요소.attrib.get("href", "")
        제품["product_url"] = href if href.startswith("http") else f"https://kr.iherb.com{href}"
    else:
        제품["product_url"] = None

    # 제품 SKU / product_id
    sku_요소 = css_first(카드, SELECTORS["sku"])
    제품["product_id"] = sku_요소.attrib.get("content") if sku_요소 else None

    # 제품명 (content 속성)
    title_요소 = css_first(카드, SELECTORS["title"])
    제품명 = title_요소.attrib.get("content", "").strip() if title_요소 else None
    제품["title"] = 제품명 or None

    # 브랜드 (제품명에서 첫 쉼표 이전)
    제품["brand"] = 제품명.split(",")[0].strip() if 제품명 else None

    # 가격 (meta content 속성 - 숫자)
    price_요소 = css_first(카드, SELECTORS["price_meta"])
    if price_요소:
        가격_str = price_요소.attrib.get("content", "")
        try:
            제품["price"] = int(float(가격_str)) if 가격_str else None
        except (ValueError, TypeError):
            제품["price"] = None
    else:
        제품["price"] = None

    # 평점 (a.stars title 속성 파싱)
    rating_요소 = css_first(카드, SELECTORS["rating_link"])
    if rating_요소:
        title_attr = rating_요소.attrib.get("title", "")
        m = re.search(r"([\d.]+)/5", title_attr)
        제품["rating"] = float(m.group(1)) if m else None
    else:
        제품["rating"] = None

    # 리뷰 수
    review_요소 = css_first(카드, SELECTORS["review_count"])
    리뷰_텍스트 = review_요소.text.strip() if review_요소 else ""
    숫자만 = re.sub(r"[^\d]", "", 리뷰_텍스트)
    제품["review_count"] = int(숫자만) if 숫자만 else None

    # 이미지 URL
    img_요소 = css_first(카드, SELECTORS["image"])
    제품["image_url"] = img_요소.attrib.get("src") if img_요소 else None

    제품["page_no"] = page_no
    제품["collected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return 제품


# ──────────────────────────────────────────────────────────────
# 페이지 수집
# ──────────────────────────────────────────────────────────────
def 페이지_수집(fetcher: StealthyFetcher, page_no: int) -> list | None:
    """단일 페이지를 수집하여 제품 목록을 반환합니다. 실패 시 None."""
    url = f"{BASE_URL}?p={page_no}"
    for 시도 in range(1, MAX_RETRY + 1):
        try:
            response = fetcher.fetch(url, headless=True, network_idle=True)
            if response.status == 404:
                # 404는 마지막 페이지 이후 → 재시도 없이 즉시 빈 목록 반환
                print(f"  [INFO] page={page_no} HTTP 404 → 마지막 페이지 도달")
                return []
            if response.status != 200:
                print(f"  [WARN] page={page_no} HTTP {response.status} (시도 {시도}/{MAX_RETRY})")
                time.sleep(RETRY_DELAY)
                continue

            카드목록 = response.css(SELECTORS["product_card"])
            if not 카드목록:
                # 제품 없음 = 마지막 페이지 이후
                return []

            제품_목록 = []
            for 카드 in 카드목록:
                try:
                    제품_목록.append(제품_파싱(카드, page_no))
                except Exception as e:
                    print(f"  [WARN] 카드 파싱 오류: {e}")

            return 제품_목록

        except Exception as e:
            print(f"  [WARN] page={page_no} 요청 오류 (시도 {시도}/{MAX_RETRY}): {e}")
            if 시도 < MAX_RETRY:
                time.sleep(RETRY_DELAY)

    return None  # 모든 재시도 실패


# ──────────────────────────────────────────────────────────────
# 메인 수집 루프
# ──────────────────────────────────────────────────────────────
def main():
    시작시각 = datetime.now()
    print("=" * 60)
    print("🚀 iHerb 비타민D 전체 페이지 수집 시작")
    print(f"   시작 시각: {시작시각.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   저장 경로: {DB_PATH}")
    print("=" * 60)

    conn = db_초기화(DB_PATH)
    fetcher = StealthyFetcher()

    누적_저장수 = 0
    연속_실패수 = 0
    page_no = 1

    try:
        while True:
            print(f"\n[INFO] page={page_no} 수집 시작")

            제품_목록 = 페이지_수집(fetcher, page_no)

            # 수집 실패
            if 제품_목록 is None:
                연속_실패수 += 1
                print(f"  [ERROR] page={page_no} {MAX_RETRY}회 연속 실패 ({연속_실패수}/{CONSEC_FAIL})")
                if 연속_실패수 >= CONSEC_FAIL:
                    print(f"\n[ERROR] 연속 {CONSEC_FAIL}회 실패 → 수집 중단")
                    break
                time.sleep(RETRY_DELAY * 2)
                page_no += 1
                continue

            # 제품 없음 = 수집 완료
            if len(제품_목록) == 0:
                print(f"  [INFO] page={page_no} 제품 없음 → 수집 완료")
                break

            연속_실패수 = 0  # 성공 시 연속 실패 카운터 초기화

            # DB 즉시 저장
            저장수 = db_저장(conn, 제품_목록, page_no)
            누적_저장수 += 저장수

            print(f"  [INFO] page={page_no} 수집 성공: {len(제품_목록)}개 파싱, "
                  f"{저장수}개 저장 (누적 {누적_저장수}개)")

            page_no += 1

            # 페이지 간 랜덤 대기 (서버 부하 방지)
            대기 = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"  [INFO] 다음 페이지까지 {대기:.1f}초 대기...")
            time.sleep(대기)

    except KeyboardInterrupt:
        print("\n\n[INFO] 사용자 중단 (Ctrl+C) → 지금까지 수집된 데이터는 DB에 보존됩니다.")

    finally:
        conn.close()

    # ── 최종 요약 ──────────────────────────────────────────────
    종료시각 = datetime.now()
    소요시간 = (종료시각 - 시작시각).total_seconds()
    print("\n" + "=" * 60)
    print("📊 수집 완료 요약")
    print("=" * 60)
    print(f"  수집 페이지 수  : {page_no - 1}페이지")
    print(f"  총 저장 건수    : {누적_저장수:,}개")
    print(f"  소요 시간       : {소요시간/60:.1f}분")
    print(f"  DB 파일         : {DB_PATH}")
    print(f"  종료 시각       : {종료시각.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("→ 다음 단계: uv run src/verify_scraped_data.py")


if __name__ == "__main__":
    main()
