"""
iHerb 제품 카드 실제 HTML 구조 확인 스크립트

목적:
    - 수집된 JSON에서 첫 번째 제품 카드의 URL을 가져와
      실제 HTML 구조(클래스명, 셀렉터)를 출력합니다.
    - test_one_page.py에서 저장한 JSON을 재활용하여
      StealthyFetcher를 다시 실행하지 않아도 됩니다.
"""
from scrapling.fetchers import StealthyFetcher
from lxml import html as lhtml

URL = "https://kr.iherb.com/c/vitamin-d?p=1"

print("⏳ 페이지 요청 중...")
fetcher = StealthyFetcher()
response = fetcher.fetch(URL, headless=True, network_idle=True)
print(f"✅ 응답 수신\n")

카드목록 = response.css("div.product-cell")
print(f"제품 카드 수: {len(카드목록)}\n")

if 카드목록:
    카드 = 카드목록[0]
    # html_content() 메서드로 실제 HTML 출력
    print("=" * 60)
    print("📦 첫 번째 제품 카드 HTML 구조:")
    print("=" * 60)
    print(카드.html_content)
    print()

    # 가능한 셀렉터들 직접 테스트
    print("=" * 60)
    print("🔍 다양한 셀렉터 테스트:")
    print("=" * 60)

    테스트_셀렉터 = [
        # 제품명 후보
        "a.product-title",
        ".product-title",
        "a[class*='title']",
        "[class*='title']",
        # 브랜드 후보
        "a.product-brand-name",
        ".product-brand-name",
        "[class*='brand']",
        # 가격 후보
        "[class*='price']",
        "span[class*='price']",
        "div[class*='price']",
        # 평점 후보
        "[class*='rating']",
        "[class*='star']",
        # 이미지 후보
        "img",
        ".product-image-area img",
    ]

    for 셀렉터 in 테스트_셀렉터:
        결과 = 카드.css(셀렉터)
        if 결과:
            첫번째 = 결과[0]
            텍스트 = str(첫번째.text or "").strip()[:50]
            print(f"  ✅ '{셀렉터}' → {len(결과)}개 | 텍스트: '{텍스트}'")
            # 속성도 출력
            try:
                attrs = dict(첫번째.attrib)
                if attrs:
                    print(f"     attrs: {attrs}")
            except Exception:
                pass
        else:
            print(f"  ❌ '{셀렉터}' → 없음")
