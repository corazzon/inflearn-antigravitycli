# iHerb 비타민D 제품 목록 수집 계획

> **작성일**: 2026-06-27  
> **대상 URL**: https://kr.iherb.com/c/vitamin-d?p=1  
> **수집 도구**: Scrapling (StealthyFetcher / AsyncStealthyFetcher)  
> **저장 형식**: SQLite DB

---

## 1. 목표 (Goals)

| 항목 | 내용 |
|------|------|
| 수집 사이트 | iHerb 한국 (kr.iherb.com) |
| 수집 카테고리 | 비타민 D (Vitamin D) |
| 수집 범위 | 전체 페이지 (페이지네이션 자동 순회) |
| 저장 형식 | SQLite DB |
| DB 파일 경로 | `data/iherb_vitamind.sqlite` |
| 테이블명 | `products` |

### 수집 대상 필드

| 필드명 | 설명 | 예시 |
|--------|------|------|
| `product_id` | iHerb 제품 고유 ID | `LFS-04002` |
| `title` | 제품명 | `Now Foods, 비타민 D-3` |
| `brand` | 브랜드명 | `Now Foods` |
| `price` | 현재 판매 가격 (원) | `12500` |
| `original_price` | 정가 (할인 전) | `18000` |
| `discount_rate` | 할인율 (%) | `30` |
| `rating` | 평점 (0.0 ~ 5.0) | `4.7` |
| `review_count` | 리뷰 수 | `1234` |
| `product_url` | 제품 상세 페이지 URL | `https://kr.iherb.com/pr/...` |
| `image_url` | 제품 이미지 URL | `https://cloudfront.net/...` |
| `page_no` | 수집된 페이지 번호 | `1` |
| `collected_at` | 수집 일시 | `2026-06-27 18:10:00` |

---

## 2. HTTP 정보 (HTTP Info)

### 기본 요청 정보

```
URL     : https://kr.iherb.com/c/vitamin-d
Method  : GET
Query   : ?p={page_number}
```

### 페이지네이션 파라미터

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `p` | 페이지 번호 (1부터 시작) | `?p=1`, `?p=2`, ... |

> **주의**: iHerb는 Cloudflare와 봇 탐지 시스템을 사용하므로  
> 일반 `requests` 라이브러리로는 **403 Forbidden** 응답을 받습니다.  
> 반드시 **Scrapling의 StealthyFetcher**를 사용해야 합니다.

### 권장 요청 설정 (StealthyFetcher 자동 처리)

```python
# StealthyFetcher가 자동으로 다음을 관리합니다:
# - User-Agent (실제 브라우저 지문 사용)
# - Accept-Language: ko-KR,ko;q=0.9
# - Accept-Encoding: gzip, deflate, br
# - 쿠키 세션 관리
# - Cloudflare 우회 처리
```

---

## 3. 예상 HTML 구조 분석 (Response Analysis)

> **실제 수집 전 브라우저 개발자 도구로 반드시 셀렉터 확인 필요**  
> iHerb는 CSS 클래스명을 주기적으로 변경하므로, 아래 셀렉터는 참고용입니다.

### 예상 제품 카드 구조

```html
<!-- 제품 카드 컨테이너 (반복) -->
<div class="product-cell">

  <!-- 제품 이미지 -->
  <a href="/pr/제품ID" class="product-link">
    <img class="product-image" src="https://cloudfront.net/..." alt="제품명">
  </a>

  <!-- 브랜드명 -->
  <span class="product-brand">Now Foods</span>

  <!-- 제품명 -->
  <div class="product-title">
    <a href="/pr/제품ID">비타민 D-3, 2,000 IU, 240 소프트젤</a>
  </div>

  <!-- 평점 / 리뷰 수 -->
  <div class="product-rating">
    <span class="rating-value">4.7</span>
    <span class="rating-count">(1,234)</span>
  </div>

  <!-- 가격 정보 -->
  <div class="product-price">
    <span class="price">₩12,500</span>
    <span class="price-original">₩18,000</span>
    <span class="discount-badge">30% 할인</span>
  </div>

</div>
```

### 예상 CSS 셀렉터 (실제 확인 후 수정 필요)

| 데이터 | CSS 셀렉터 (예상) |
|--------|-----------------|
| 제품 카드 (반복 단위) | `div.product-cell` |
| 제품 링크 + URL | `a.product-link[href]` |
| 브랜드명 | `.product-brand` |
| 제품명 | `.product-title a` |
| 현재 가격 | `.product-price .price` |
| 원래 가격 | `.product-price .price-original` |
| 할인율 | `.discount-badge` |
| 평점 | `.rating-value` |
| 리뷰 수 | `.rating-count` |
| 이미지 URL | `.product-image[src]` |

### 페이지 종료 조건

```python
# 다음 중 하나에 해당하면 수집 종료:
# 1. 응답 HTML에서 제품 카드(.product-cell)가 0개 발견될 때
# 2. 현재 페이지 번호가 최대 페이지 수를 초과할 때
# 3. 연속 3회 요청 실패 시
```

---

## 4. 기술 스택 및 환경 (Technical Stack)

### 필수 패키지 설치

```bash
# Scrapling 설치 (fetchers 포함)
uv pip install "scrapling[fetchers]"

# Playwright 브라우저 바이너리 설치
playwright install chromium

# 기타 패키지
uv pip install pandas
```

### 패키지 역할

| 패키지 | 역할 |
|--------|------|
| `scrapling` | 봇 탐지 우회 + HTML 파싱 |
| `scrapling[fetchers]` | Playwright 기반 StealthyFetcher 활성화 |
| `sqlite3` | 수집 데이터 영구 저장 (Python 내장) |
| `pandas` | 데이터 검증 및 보고서 생성 |

### 사용 페처(Fetcher) 전략

```python
# iHerb는 강력한 봇 탐지를 사용하므로 StealthyFetcher 사용
from scrapling.fetchers import StealthyFetcher

fetcher = StealthyFetcher()
response = fetcher.fetch(
    url,
    headless=True,           # 헤드리스 모드 (화면 없이 실행)
    network_idle=True,       # 네트워크 안정화 후 파싱
    wait_selector=".product-cell"  # 제품 카드 로딩 완료 대기
)
```

---

## 5. 1페이지 검증 절차 (1-Page Verification Procedure)

`src/test_one_page.py` 실행 후 다음을 확인합니다:

### 체크리스트

- [ ] HTTP 상태코드 200 OK 응답 확인
- [ ] 응답 HTML 길이 > 10,000 bytes
- [ ] 제품 카드(`.product-cell`) 개수 > 0
- [ ] 각 카드에서 제품명, 가격, 평점 추출 가능 여부
- [ ] 제품 URL이 `https://kr.iherb.com/pr/` 형식인지 확인
- [ ] 가격 데이터가 숫자로 변환 가능한지 확인
- [ ] 이미지 URL이 유효한 형식인지 확인
- [ ] 수집된 첫 3개 제품 미리보기 출력

---

## 6. 전체 수집 계획 (Full Collection Instructions)

### 수집 흐름도

```
START
  │
  ├─ SQLite DB 초기화 (products 테이블 생성)
  │
  ├─ page = 1 부터 시작
  │
  ├─ [루프]
  │    │
  │    ├─ URL 생성: https://kr.iherb.com/c/vitamin-d?p={page}
  │    │
  │    ├─ StealthyFetcher로 페이지 요청
  │    │
  │    ├─ 제품 카드 파싱
  │    │
  │    ├─ 제품 수 == 0? → STOP (수집 완료)
  │    │
  │    ├─ 데이터 SQLite DB에 즉시 저장 (append)
  │    │
  │    ├─ 로그 출력: [INFO] page=N 수집 성공, M개 저장 (누적 K개)
  │    │
  │    ├─ 0.5 ~ 2.0초 랜덤 대기 (서버 부하 방지)
  │    │
  │    └─ page += 1 → 루프 반복
  │
  └─ END
```

### 실패 처리 전략

```python
MAX_RETRY = 3          # 최대 재시도 횟수
RETRY_DELAY = 5.0      # 재시도 대기 시간 (초)
CONSECUTIVE_FAIL = 3   # 연속 실패 시 중단

# 실패 로그 예시:
# [WARN] page=5 요청 실패 (1/3 재시도)
# [ERROR] page=5 3회 연속 실패 → 수집 중단
```

---

## 7. 검증 체크리스트 (Verification Checklist)

### 요청 검증
- [ ] User-Agent가 일반 브라우저로 인식되는지 확인
- [ ] 응답 상태코드 200 여부
- [ ] Cloudflare 차단 페이지 감지 로직 구현

### 페이지네이션 검증
- [ ] `p=1` ~ 마지막 페이지까지 순서대로 수집되는지 확인
- [ ] 중복 페이지 수집 방지 로직
- [ ] 마지막 페이지에서 정상 종료 확인

### 저장 검증
- [ ] SQLite DB 파일 생성 확인
- [ ] 각 페이지 수집 직후 DB 즉시 저장 확인
- [ ] 프로세스 중단 후 재시작 시 이어서 수집 가능 여부

### 데이터 품질 검증
- [ ] 전체 수집 건수 vs. DB 저장 건수 일치 여부
- [ ] 제품명 NULL 비율 < 1%
- [ ] 가격 NULL 비율 < 5%
- [ ] 중복 `product_id` 존재 여부 확인
- [ ] 가격 데이터 형식 일관성 (숫자형 변환 가능)

### 서버 부하 방지
- [ ] 페이지 간 최소 0.5초 이상 대기
- [ ] 연속 오류 시 자동 중단 로직

---

## 8. 최종 산출물 구조 (Deliverables)

```
iherb/
├── data/
│   └── iherb_vitamind.sqlite        # 수집된 제품 데이터 DB
├── docs/
│   └── SCRAPING_PROMPT.md           # 본 계획 문서
├── src/
│   ├── test_one_page.py             # 1페이지 테스트 스크립트
│   ├── collect_all_pages.py         # 전체 수집 스크립트
│   └── verify_scraped_data.py       # 데이터 품질 검증 스크립트
└── images/
    └── (시각화 결과 이미지 저장)
```

---

## 9. 주의사항 및 윤리 가이드라인

**법적 검토 필요**  
- iHerb의 `robots.txt` 및 이용약관(Terms of Service)을 반드시 사전 확인할 것  
- 상업적 목적의 대규모 수집은 법적 분쟁 소지가 있음  
- 수집 데이터는 개인 학습/연구 목적으로만 사용 권장  
- 서버에 과도한 부하를 주지 않도록 요청 간 충분한 지연 적용  

**셀렉터 유지보수 주의**  
- iHerb는 주기적으로 HTML 클래스명을 변경하므로, 실행 전 브라우저 개발자 도구로 셀렉터를 반드시 재확인할 것  
- Scrapling의 자동 적응형 파싱 기능을 최대한 활용하여 셀렉터 변경에 대응  

---

## 10. 다음 단계 (Next Steps)

1. **사전 확인**: 브라우저 개발자 도구(F12)로 실제 CSS 셀렉터 확인 후 이 문서 업데이트
2. **환경 구성**: `uv pip install "scrapling[fetchers]"` 및 `playwright install chromium`
3. **1페이지 테스트**: `src/test_one_page.py` 작성 및 실행
4. **검토 후 승인**: 1페이지 결과 확인 후 전체 수집 진행 여부 결정
5. **전체 수집 실행**: `src/collect_all_pages.py` 실행
6. **데이터 검증**: `src/verify_scraped_data.py` 실행 및 보고서 생성
