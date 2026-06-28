# Klook 데이터 수집용 Playwright & Scrapling 분석 및 프롬프트 가이드

이 문서는 Klook 서울 목적지 페이지(`https://www.klook.com/ko/destination/c13-seoul/`) 및 Klook 메인 페이지(`https://www.klook.com/ko/`)에서 각각 상품 목록 및 인기 여행 목적지를 효율적으로 수집하기 위한 분석 내용과 실제 Playwright 및 Scrapling 사용 시 적용할 프롬프트를 정리한 가이드라인입니다.

---

## 1. Klook 웹사이트 네트워크 분석 및 우회 원리

### 1.1 Datadome 보안 차단 우회
* Klook은 보안 솔루션인 **Datadome**을 사용하므로 API 주소로 직접 일반 HTTP 요청(예: standard requests 등)을 보내면 **403 Forbidden** 차단을 당합니다.
* 이를 해결하기 위해 Playwright를 사용하거나, **Scrapling** 라이브러리의 `StealthyFetcher`를 사용해 헤더, TLS 지문 등을 자동으로 우화하여 진입해야 합니다.

### 1.2 두 가지 데이터 적재 유형
Klook 웹사이트는 페이지 성격에 따라 데이터를 두 가지 방식으로 로드합니다.

#### 유형 A: 서버 사이드 렌더링 (SSR) (예: 서울 목적지 페이지)
* 페이지 진입 시점에 필요한 주요 액티비티 목록을 서버 사이드에서 미리 렌더링(SSR)하여 HTML 내부 자바스크립트 전역 변수인 `window.__KLOOK__`에 JSON 구조로 담아둡니다.
* **데이터 추출 경로:**
  * `window.__KLOOK__.data["0"].pageData.page.body.sections` 배열 중 `meta.name`이 `"DestinationExploreTtdActs"`인 섹션
  * 상품 목록: `body.content.data.cards`

#### 유형 B: 비동기 지연 로딩 (Async Lazy-Load) (예: Klook 첫 페이지/메인 페이지)
* 초기 페이지 로딩 속도를 최적화하기 위해, 주요 핵심 섹션들의 데이터를 페이지 로드 완료 후 API 통신을 통해 비동기적으로 가져옵니다.
* **추출 정보 및 API 엔드포인트 주소:**
  1. **인기 여행 목적지 목록 (Where to Next):**
     * `https://www.klook.com/v1/platformbffsrv/homepage/service/get_where_to_next?brand=&carrier=&city_id=0&country_id=10&roaming=&sim_region_code=&source=human&system_platform=desktop`
  2. **인기 액티비티 목록 (Popular Activities):**
     * `https://www.klook.com/v1/platformbffsrv/homepage/service/get_pop_activity?city_id=0&country_id=0&limit=12&source=human&system_platform=desktop`

---

## 2. Playwright 적용 프롬프트 (SSR 기반 수집)

```text
Klook 서울 여행 페이지(https://www.klook.com/ko/destination/c13-seoul/)의 액티비티 상품 데이터를 수집해 주세요.

[요구사항]
1. Datadome 보안 차단을 우회하기 위해 Playwright 브라우저를 띄워 페이지에 진입합니다.
2. 페이지 로드가 완료되면 추가적인 네트워크 API 요청을 모방하는 대신, 이미 HTML에 SSR 형태로 박혀 있는 전역 변수 'window.__KLOOK__'를 추출해 주세요.
3. 추출 경로:
   - window.__KLOOK__.data["0"].pageData.page.body.sections 배열을 찾습니다.
   - 이 중 meta.name이 'DestinationExploreTtdActs'인 섹션을 선택합니다.
   - 해당 섹션의 body.content.data.cards 배열에서 상품 정보를 파싱합니다.
4. 각 카드 데이터에서 다음 정보를 추출하여 정리해 주세요.
   - 상품명 (title)
   - 부제목 (sub_title)
   - 정가 (price.market_price.value_with_symbol)
   - 판매가 (price.sell_price.value_with_symbol)
   - 평점 (review_obj.rating)
   - 리뷰 수 (review_obj.review_num)
   - 상세 링크 (https://www.klook.com + deep_link)
   - 대표 이미지 URL (cover_url)
```

---

## 3. Scrapling 적용 프롬프트 (API 직접 우회 수집)

```text
scrapling 라이브러리를 사용하여 Klook 첫 페이지의 인기 목적지 및 인기 액티비티 API를 직접 호출해 데이터를 수집해 주세요.

[요구사항]
1. anti-bot 탐지 기능(Datadome)을 우회하기 위해 scrapling 라이브러리의 'StealthyFetcher'를 활용합니다.
2. 메인 페이지의 데이터를 로드하기 위해 브라우저를 띄우고 스크롤하는 대신, 실제 브라우저가 호출하는 아래 두 API 주소를 StealthyFetcher.fetch()로 직접 호출해 주세요.
   - 인기 목적지 API:
     https://www.klook.com/v1/platformbffsrv/homepage/service/get_where_to_next?brand=&carrier=&city_id=0&country_id=10&roaming=&sim_region_code=&source=human&system_platform=desktop
   - 인기 액티비티 API:
     https://www.klook.com/v1/platformbffsrv/homepage/service/get_pop_activity?city_id=0&country_id=0&limit=12&source=human&system_platform=desktop
3. 호출 성공 시 반환되는 Response 객체에서 .json() 메서드를 호출하여 JSON 데이터를 파싱합니다.
4. 각 JSON 데이터 구조에서 아래의 항목들을 추출하여 구조화해 주세요.
   - 인기 목적지 (result.items 배열 내):
     * 도시명 (data.title)
     * 활동 수 (data.sub_title)
     * 상세 링크 (data.deep_link)
     * 이미지 URL (data.img_url)
   - 인기 액티비티 (result.items 배열 내):
     * 상품명 (data.title)
     * 부제목 (data.sub_title)
     * 도시명 (data.city_name)
     * 정가 (data.price.market_price)
     * 판매가 (data.price.selling_price)
     * 평점 (data.review.star)
     * 리뷰 수 (data.review.number)
     * 상세 링크 (https://www.klook.com + data.deep_link)
     * 이미지 URL (data.cover_url)
```
