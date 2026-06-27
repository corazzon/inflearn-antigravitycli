"""
Scrapling 0.4.9 API 속성 디버그 스크립트

목적:
    - Response 및 Element 객체의 실제 속성과 메서드를 확인하여
      올바른 API 사용법을 파악합니다.
"""
from scrapling.fetchers import StealthyFetcher

URL = "https://kr.iherb.com/c/vitamin-d?p=1"

print("⏳ 페이지 요청 중...")
fetcher = StealthyFetcher()
response = fetcher.fetch(URL, headless=True, network_idle=True)
print(f"✅ 응답 수신\n")

# ── Response 객체 속성 확인 ──────────────────────────────────
print("=" * 50)
print("📦 Response 객체 타입:", type(response))
print("📦 Response 속성/메서드 목록:")
속성목록 = [a for a in dir(response) if not a.startswith("__")]
for 속성 in 속성목록:
    print(f"   .{속성}")

# 텍스트/HTML 속성 후보 직접 테스트
print("\n🔍 HTML/텍스트 속성 후보 테스트:")
후보 = ["text", "html", "body", "content", "source", "page_source", "get_content"]
for 후보명 in 후보:
    try:
        값 = getattr(response, 후보명)
        print(f"   ✅ response.{후보명} → 길이 {len(값)}")
    except AttributeError:
        print(f"   ❌ response.{후보명} → 없음")

# ── 제품 카드 Element 속성 확인 ─────────────────────────────
print("\n" + "=" * 50)
카드목록 = response.css("div.product-cell")
print(f"📦 제품 카드 수: {len(카드목록)}")

if 카드목록:
    카드 = 카드목록[0]
    print(f"\n📦 Element 객체 타입: {type(카드)}")
    print("📦 Element 속성/메서드 목록:")
    elem_속성 = [a for a in dir(카드) if not a.startswith("__")]
    for 속성 in elem_속성:
        print(f"   .{속성}")

    # 속성 딕셔너리 후보 테스트
    print("\n🔍 속성 딕셔너리 후보 테스트:")
    후보 = ["attrib", "attribs", "attrs", "attributes"]
    for 후보명 in 후보:
        try:
            값 = getattr(카드, 후보명)
            print(f"   ✅ element.{후보명} → {type(값)}")
        except AttributeError:
            print(f"   ❌ element.{후보명} → 없음")

    # 텍스트 속성 후보 테스트
    print("\n🔍 텍스트 속성 후보 테스트:")
    후보 = ["text", "inner_text", "text_content", "get_text", "clean_text"]
    for 후보명 in 후보:
        try:
            값 = getattr(카드, 후보명)
            if callable(값):
                결과 = 값()
                print(f"   ✅ element.{후보명}() → '{str(결과)[:50]}'")
            else:
                print(f"   ✅ element.{후보명} → '{str(값)[:50]}'")
        except Exception as e:
            print(f"   ❌ element.{후보명} → {e}")

    # a 태그에서 href 추출 테스트
    print("\n🔍 자식 a 요소 href 추출 테스트:")
    링크목록 = 카드.css("a")
    if 링크목록:
        링크 = 링크목록[0]
        print(f"   a 요소 타입: {type(링크)}")
        attr_후보 = ["attrib", "attribs", "attrs", "attributes"]
        for 후보명 in attr_후보:
            try:
                값 = getattr(링크, 후보명)
                print(f"   ✅ a.{후보명} → {type(값)} / href: {dict(값).get('href', 'N/A')}")
            except Exception as e:
                print(f"   ❌ a.{후보명} → {e}")
