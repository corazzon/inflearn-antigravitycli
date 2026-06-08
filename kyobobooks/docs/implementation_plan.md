# 교보문고 베스트셀러 데이터 수집 구현 계획

교보문고의 컴퓨터/IT 분야 일간 베스트셀러 페이지의 도서 데이터(순위, 도서명, 저자, 출판사, 출판일, 가격, 평점 등)를 수집하는 파이프라인을 구축합니다. 교보문고는 동적 웹페이지 형식이므로, 먼저 브라우저 네트워크 로그를 캡처하는 탐색 스크립트를 사용하여 백엔드 API 엔드포인트 정보를 확보한 후, 안전하고 빠른 API 기반 스크래퍼를 구현합니다.

## User Review Required

> [!NOTE]
> - **수집 대상 URL**: `https://store.kyobobook.co.kr/bestseller/online/daily/domestic/33?page=1` (전체 페이지)
> - **1단계 (네트워크 탐색)**: Playwright를 사용해 타겟 페이지를 띄우고, 백엔드 API 호출 목록을 인터셉트하여 URL 및 필요한 Request 헤더(Headers) 정보를 추출해 `kyobobooks/docs/scaraping_prompt.md` 파일에 기록합니다.
> - **2단계 (API 기반 수집 및 저장)**: 수집한 API 명세를 바탕으로 파이썬 `requests` 모듈과 필요시 `BeautifulSoup`을 활용해 페이지별 데이터를 JSON/HTML로 수집한 후, Pandas를 이용해 `kyobobooks/data/kyobo_bestseller_YYYYMMDD.csv` 파일로 저장합니다.

## Proposed Changes

### kyobobooks

---

#### [NEW] [inspect_api.py](../src/inspect_api.py)
Playwright를 이용해 브라우저를 백그라운드에서 실행하고, 네트워크 호출 중 교보문고 도서 데이터(예: `/api/gw/pub/...` 등)로 보이는 요청의 URL, Headers, Payload를 캡처하여 출력 및 저장하는 탐색 코드입니다.

#### [MODIFY] [scaraping_prompt.md](scaraping_prompt.md)
탐색 스크립트를 통해 확인된 실제 API URL, Header, Payload 정보와 응답 예시를 기록합니다.

#### [NEW] [scraping.py](../src/scraping.py)
`scaraping_prompt.md` 정보를 활용해 실제 데이터를 페이지 단위로 순차 수집하고, 차단 방지를 위한 딜레이 설정 및 `kyobobooks/data/kyobo_bestseller_YYYYMMDD.csv` 저장을 수행하는 메인 스크래핑 코드입니다.

---

## Verification Plan

### Automated Tests
1. **탐색 스크립트 실행**:
   ```bash
   uv run python kyobobooks/src/inspect_api.py
   ```
   - 브라우저 네트워크 탭 감지를 통해 타겟 API 정보가 성공적으로 도출되는지 검증하고 `scaraping_prompt.md` 내용 업데이트를 확인합니다.
2. **스크래퍼 스크립트 실행**:
   ```bash
   uv run python kyobobooks/src/scraping.py
   ```
   - 전체 베스트셀러 페이지 데이터 수집이 에러 없이 수행되는지 확인합니다.
   - `kyobobooks/data/` 폴더 하위에 CSV 파일이 올바르게 생성되고, 순위/도서명/저자/출판사/평점 등의 열이 잘 작성되었는지 검증합니다.

### Manual Verification
- 생성된 CSV 파일을 검토하여 결측치 여부 및 인코딩 깨짐(`utf-8-sig` 적용 여부)을 점검합니다.
