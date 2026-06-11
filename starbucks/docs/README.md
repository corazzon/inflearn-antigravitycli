# 스타벅스 전국 매장 데이터 수집기 (Starbucks Store Crawler)

스타벅스 코리아 공식 웹사이트 지도 페이지의 비공식 내부 API(`getStore.do`)를 활용하여 전국 스타벅스 매장의 지리적/운영 정보를 정기적 혹은 수동으로 수집하는 데이터 파이프라인 컴포넌트입니다.

## 기능 특징
- **시도 목록 자동 연동**: `getSidoList.do` API를 통해 현재 운영 중인 전국 시도 코드를 자동으로 동적 조회합니다.
- **안전한 수집 정책**: 연속된 요청 사이에 0.5초 ~ 1.0초의 임의 대기(Random Sleep)를 주어 대상 서버의 부하를 최소화합니다.
- **견고한 예외 처리**: 일시적 네트워크 끊김, 503, 429 에러 등에 대처하기 위해 지수 백오프(Exponential Backoff)를 적용한 최대 5회 자동 재시도 메커니즘을 지원합니다.
- **인코딩 무결성**: MS 엑셀 더블클릭 및 한글 데이터 호환성 보장을 위해 출력 CSV 파일은 반드시 `utf-8-sig` 형식으로 기록됩니다.

## 디렉토리 구조
스타벅스 컴포넌트는 다음과 같은 상대 경로 구조를 따릅니다.
```text
starbucks/
├── data/
│   ├── raw_starbucks_stores.json         # 전국 원본 JSON 백업
│   ├── starbucks_stores.csv              # 전국 가공 CSV 데이터
│   ├── raw_starbucks_stores_seoul.json   # 서울 테스트 원본 JSON
│   └── starbucks_stores_seoul.csv        # 서울 테스트 가공 CSV
├── docs/
│   ├── implementation_plan.md            # 수집 구현 계획서
│   └── README.md                         # 본 문서
├── reports/
│   └── store_crawl_report.md             # 수집 실행 최종 결과 보고서
└── src/
    └── store_crawler.py                  # 수집기 파이썬 소스코드
```

## 실행 가이드

### 의존성 확인
본 수집기는 워크스페이스 공통 가상환경(`.venv`)을 활용하며, `requests` 및 `pandas` 라이브러리를 필요로 합니다.
실행은 가상환경 도구인 `uv`를 사용합니다.

### 1단계: 서울 지역 테스트 수집
수집기가 정상 작동하는지 확인하기 위해 서울 지역 데이터만 부분 수집합니다.
```bash
# 워크스페이스 루트에서 실행
uv run starbucks/src/store_crawler.py --test-seoul
```
- 결과 파일:
  - 원본 JSON: `starbucks/data/raw_starbucks_stores_seoul.json`
  - 가공 CSV: `starbucks/data/starbucks_stores_seoul.csv`

### 2단계: 전국 매장 전체 수집
전국 17개 시도의 모든 매장 정보를 순차적으로 수집합니다.
```bash
# 워크스페이스 루트에서 실행
uv run starbucks/src/store_crawler.py --all
```
- 결과 파일:
  - 원본 JSON: `starbucks/data/raw_starbucks_stores.json`
  - 가공 CSV: `starbucks/data/starbucks_stores.csv`

## 수집 데이터 스키마
가공된 CSV 파일(`starbucks_stores.csv`)에는 다음과 같은 주요 필드가 포함되어 제공됩니다.

| 컬럼명 | 원본 필드 | 설명 | 예시 |
| :--- | :--- | :--- | :--- |
| **매장명** | `s_name` | 스타벅스 매장의 지점명 | 역삼아레나빌딩 |
| **시도명** | `sido_name` | 매장이 속한 광역지자체명 | 서울 |
| **구군명** | `gugun_name` | 매장이 속한 기초지자체명 | 강남구 |
| **시도코드** | `sido_code` | 스타벅스 관리용 시도 코드 | 01 |
| **구군코드** | `gugun_code` | 스타벅스 관리용 구군 코드 | 0101 |
| **주소** | `addr` | 매장 상세 도로명/지번 주소 | 서울특별시 강남구 역삼동 721-13... |
| **전화번호** | `tel` | 매장 대표 연락처 | 1522-3232 |
| **위도** | `lat` | 매장 위치의 GPS 위도 좌표 | 37.501087 |
| **경도** | `lng` | 매장 위치의 GPS 경도 좌표 | 126.97865 |
| **매장코드** | `store_cd` | 고유 매장 식별자 | 0 |
| **관리코드** | `s_code` | 내부 매장 관리 코드 | 1509 |
| **오픈일자** | `open_dt` | 해당 지점의 최초 영업 개시일 | 20190613 |
| **테마매장여부** | `theme_state` | 리저브, 드라이브스루 등 부가 서비스 인덱스 | Z9999@T05... |
