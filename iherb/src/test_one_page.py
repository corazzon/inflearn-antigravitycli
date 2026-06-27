"""
iHerb 비타민D 제품 목록 - 1페이지 테스트 수집 스크립트

목적:
    - Scrapling StealthyFetcher를 사용해 iHerb 봇 탐지를 우회하여 1페이지 수집
    - 실제 페이지 HTML에서 확인된 CSS 셀렉터로 필드 추출
    - 성공 시 첫 3개 제품 미리보기 출력 및 JSON 저장

실행:
    uv run src/test_one_page.py

확인된 iHerb HTML 구조 (2026-06-27 기준):
    - 제품명  : div[itemprop='name']          → content 속성
    - 가격    : meta[itemprop='price']         → content 속성 (숫자)
    - 평점    : a.stars                        → title 속성 "4.8/5 - 32,898 Reviews"
    - 리뷰수  : a.rating-count span            → 텍스트
    - 이미지  : img[itemprop='image']          → src 속성
    - 제품ID  : div[itemprop='sku']            → content 속성
    - 제품URL : a.product-link                 → href 속성
    - 브랜드  : 제품명에서 첫 쉼표 이전 파트 추출

참고 (Scrapling 0.4.9 실제 확인된 API):
    - response.body        : 페이지 전체 HTML 소스 (bytes 또는 str)
    - response.status      : HTTP 상태코드 (int)
    - response.css(sel)    : 매칭 요소 리스트 반환 (Selectors)
    - element.css(sel)     : 자식 요소 리스트 반환
    - element.attrib       : 속성 딕셔너리 (AttributesHandler)
    - element.text         : 직계 텍스트 내용
"""

import re
import json
import time
from datetime import datetime

from scrapling.fetchers import StealthyFetcher

# ──────────────────────────────────────────────────────────────
# 설정 상수
# ──────────────────────────────────────────────────────────────
TARGET_URL = "https://kr.iherb.com/c/vitamin-d?p=1"

# 실제 페이지 HTML에서 확인된 CSS 셀렉터
SELECTORS = {
    # 제품 카드 컨테이너 (각 상품 1개)
    "product_card":   "div.product-cell",
    # 제품 상세 URL
    "product_url":    "a.product-link",
    # 제품명 (content 속성에서 추출)
    "title":          "[itemprop='name']",
    # 현재 가격 (meta content 속성 - 숫자 그대로)
    "price_meta":     "meta[itemprop='price']",
    # 평점 + 리뷰수 (title="4.8/5 - 32,898 Reviews")
    "rating_link":    "a.stars",
    # 리뷰수 (span 텍스트)
    "review_count":   "a.rating-count span",
    # 이미지 URL (src 속성)
    "image":          "img[itemprop='image']",
    # 제품 고유 코드 (SKU)
    "sku":            "div[itemprop='sku']",
}


def css_first(element, selector):
    """Scrapling element에서 첫 번째 매칭 요소를 반환합니다. 없으면 None."""
    결과 = element.css(selector)
    return 결과[0] if 결과 else None


def 리뷰수_정수_변환(텍스트: str) -> int | None:
    """'32,898' → 32898 으로 변환"""
    if not 텍스트:
        return None
    숫자만 = re.sub(r"[^\d]", "", 텍스트)
    return int(숫자만) if 숫자만 else None


def 제품_파싱(카드) -> dict:
    """제품 카드 Element에서 데이터를 추출합니다."""
    제품 = {}

    # ── 제품 URL ──────────────────────────────────────────────
    url_요소 = css_first(카드, SELECTORS["product_url"])
    if url_요소:
        href = url_요소.attrib.get("href", "")
        제품["product_url"] = href if href.startswith("http") else f"https://kr.iherb.com{href}"
    else:
        제품["product_url"] = None

    # ── 제품 SKU / product_id ─────────────────────────────────
    sku_요소 = css_first(카드, SELECTORS["sku"])
    제품["product_id"] = sku_요소.attrib.get("content") if sku_요소 else None

    # ── 제품명 (content 속성) ──────────────────────────────────
    title_요소 = css_first(카드, SELECTORS["title"])
    제품명 = title_요소.attrib.get("content", "").strip() if title_요소 else None
    제품["title"] = 제품명 or None

    # ── 브랜드 (제품명에서 첫 쉼표 이전 파트 추출) ────────────
    if 제품명:
        제품["brand"] = 제품명.split(",")[0].strip()
    else:
        제품["brand"] = None

    # ── 가격 (meta itemprop='price' content 속성 - 이미 숫자) ─
    price_요소 = css_first(카드, SELECTORS["price_meta"])
    if price_요소:
        가격_str = price_요소.attrib.get("content", "")
        try:
            제품["price"] = int(float(가격_str)) if 가격_str else None
        except (ValueError, TypeError):
            제품["price"] = None
    else:
        제품["price"] = None

    # 정가/할인율: iHerb 현재 HTML 구조에 별도 요소 없음 → None
    제품["original_price"] = None
    제품["discount_rate"] = None

    # ── 평점 (a.stars title 속성 "4.8/5 - 32,898 Reviews" 파싱) ─
    rating_요소 = css_first(카드, SELECTORS["rating_link"])
    if rating_요소:
        title_attr = rating_요소.attrib.get("title", "")
        # 예: "4.8/5 - 32,898 Reviews"
        rating_매치 = re.search(r"([\d.]+)/5", title_attr)
        제품["rating"] = float(rating_매치.group(1)) if rating_매치 else None
    else:
        제품["rating"] = None

    # ── 리뷰수 ────────────────────────────────────────────────
    review_요소 = css_first(카드, SELECTORS["review_count"])
    리뷰_텍스트 = review_요소.text.strip() if review_요소 else ""
    제품["review_count"] = 리뷰수_정수_변환(리뷰_텍스트)

    # ── 이미지 URL ────────────────────────────────────────────
    img_요소 = css_first(카드, SELECTORS["image"])
    if img_요소:
        제품["image_url"] = img_요소.attrib.get("src") or img_요소.attrib.get("data-src")
    else:
        제품["image_url"] = None

    제품["page_no"] = 1
    제품["collected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return 제품


def 검증_체크리스트(response, 제품_목록: list) -> bool:
    """수집 결과를 검증합니다."""
    print("\n" + "=" * 60)
    print("📋 검증 체크리스트")
    print("=" * 60)

    통과 = True

    # 1. 상태코드
    상태OK = (response.status == 200)
    print(f"  {'✅' if 상태OK else '❌'} HTTP 상태코드: {response.status}")
    if not 상태OK:
        통과 = False

    # 2. HTML 크기
    body = response.body
    html_크기 = len(body) if body else 0
    크기OK = (html_크기 > 10_000)
    print(f"  {'✅' if 크기OK else '❌'} HTML 크기: {html_크기:,} bytes")
    if not 크기OK:
        통과 = False

    # 3. 제품 카드 수량
    카드수 = len(제품_목록)
    카드OK = (카드수 > 0)
    print(f"  {'✅' if 카드OK else '❌'} 제품 카드 수: {카드수}개")
    if not 카드OK:
        통과 = False
        return 통과

    # 4. 필드별 추출 성공률
    필드목록 = ["title", "brand", "price", "rating", "product_url", "product_id", "image_url"]
    for 필드 in 필드목록:
        성공수 = sum(1 for p in 제품_목록 if p.get(필드) is not None)
        성공률 = 성공수 / 카드수 * 100
        필드OK = (성공률 >= 80)
        print(f"  {'✅' if 필드OK else '⚠️ '} {필드:15s}: {성공수}/{카드수} ({성공률:.0f}%)")

    return 통과


def main():
    print("=" * 60)
    print("🧪 iHerb 비타민D 1페이지 테스트 수집")
    print(f"   대상 URL: {TARGET_URL}")
    print(f"   시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── 1. 페이지 요청 ────────────────────────────────────────
    print("\n⏳ StealthyFetcher로 페이지 요청 중... (최대 60초 소요)")
    시작 = time.time()
    try:
        fetcher = StealthyFetcher()
        response = fetcher.fetch(TARGET_URL, headless=True, network_idle=True)
    except Exception as e:
        print(f"\n❌ 요청 실패: {e}")
        return

    소요시간 = time.time() - 시작
    print(f"✅ 응답 수신 완료 ({소요시간:.1f}초)")

    # ── 2. 제품 카드 탐색 ─────────────────────────────────────
    print(f"\n🔍 제품 카드 탐색: '{SELECTORS['product_card']}'")
    카드목록 = response.css(SELECTORS["product_card"])
    print(f"   발견된 제품 카드: {len(카드목록)}개")

    if len(카드목록) == 0:
        print("\n⚠️  제품 카드를 찾지 못했습니다. HTML 일부를 출력합니다:")
        body = response.body
        body_str = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        print(body_str[:2000])
        return

    # ── 3. 데이터 추출 ────────────────────────────────────────
    print("\n⚙️  데이터 파싱 중...")
    제품_목록 = []
    오류수 = 0
    for 카드 in 카드목록:
        try:
            제품 = 제품_파싱(카드)
            제품_목록.append(제품)
        except Exception as e:
            오류수 += 1
            print(f"   [WARN] 카드 파싱 오류: {e}")

    print(f"   파싱 완료: {len(제품_목록)}개 (오류: {오류수}개)")

    # ── 4. 검증 ───────────────────────────────────────────────
    통과 = 검증_체크리스트(response, 제품_목록)

    # ── 5. 미리보기 ───────────────────────────────────────────
    if 제품_목록:
        print("\n" + "=" * 60)
        print("🔎 수집 데이터 미리보기 (상위 3개)")
        print("=" * 60)
        for i, 제품 in enumerate(제품_목록[:3], 1):
            print(f"\n  [{i}번 제품]")
            print(f"   제품 ID   : {제품.get('product_id', 'N/A')}")
            print(f"   브랜드    : {제품.get('brand', 'N/A')}")
            print(f"   제품명    : {str(제품.get('title', 'N/A'))[:60]}")
            print(f"   가격      : {제품.get('price', 'N/A'):,}원" if isinstance(제품.get('price'), int) else f"   가격      : {제품.get('price', 'N/A')}")
            print(f"   평점      : {제품.get('rating', 'N/A')}")
            print(f"   리뷰수    : {제품.get('review_count', 'N/A'):,}개" if isinstance(제품.get('review_count'), int) else f"   리뷰수    : {제품.get('review_count', 'N/A')}")
            print(f"   이미지 URL: {str(제품.get('image_url', 'N/A'))[:60]}")
            print(f"   상품 URL  : {str(제품.get('product_url', 'N/A'))[:60]}")

    # ── 6. JSON 저장 ──────────────────────────────────────────
    import pathlib
    pathlib.Path("data").mkdir(exist_ok=True)
    결과파일 = "data/test_one_page_result.json"
    with open(결과파일, "w", encoding="utf-8") as f:
        json.dump(제품_목록, f, ensure_ascii=False, indent=2)
    print(f"\n💾 결과 저장: {결과파일} ({len(제품_목록)}개 제품)")

    # ── 7. 최종 판정 ──────────────────────────────────────────
    print("\n" + "=" * 60)
    if 통과 and len(제품_목록) > 0:
        print("🎉 1페이지 테스트 성공! → 다음 단계: collect_all_pages.py 실행")
    else:
        print("⚠️  1페이지 테스트 일부 실패 → 셀렉터 또는 파싱 로직 점검 필요")
    print("=" * 60)


if __name__ == "__main__":
    main()
