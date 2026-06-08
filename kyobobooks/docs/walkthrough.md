# 교보문고 일간 베스트셀러 데이터 수집 및 대시보드 완료 보고서 (Walkthrough)

교보문고의 컴퓨터/IT 분야 일간 베스트셀러 데이터 수집 파이프라인 구축, EDA 분석 리포트 작성, 그리고 Chart.js를 이용한 무서버 반응형 대시보드 웹앱 제작까지 모든 개발을 성공적으로 완료하였습니다.

## 1. 구현 결과 요약

- **API 탐색 스크립트 개발**: [inspect_api.py](../src/inspect_api.py)
  - Playwright를 사용해 타겟 페이지를 기동하여 API 게이트웨이 보안 키(`x-api-gw-key`)를 실시간으로 자동 캡처하는 로직입니다.
- **수집 명세 기록**: [scaraping_prompt.md](scaraping_prompt.md)
  - 발견된 API 경로, 필수 쿼리 스트링, 헤더 구성 등을 체계적으로 도큐멘테이션하였습니다.
- **메인 스크래퍼 개발**: [scraping.py](../src/scraping.py)
  - 캡처된 동적 키와 함께 파이썬 `requests` 기반으로 고속 수집을 진행하며, 호출 간 랜덤 딜레이를 주어 차단을 방지하는 안정적 스크래퍼입니다.
  - 책 상세설명 필드(`inbukCntt`) 수집 기능 및 비어 있는 값(`None`)에 대한 방어 로직을 적용하였습니다.
- **최종 데이터셋 수집**: [kyobo_bestseller_20260608.csv](../data/kyobo_bestseller_20260608.csv)
  - 컴퓨터/IT 분야 1위부터 449위까지의 도서 정보와 책 상세 정보 449건 수집 완료.
- **대시보드 데이터 빌더**: [dashboard_data_builder.py](../src/dashboard_data_builder.py)
  - 로컬 CORS 차단을 방지하고 오프라인 구동이 가능하도록 수집된 CSV와 TF-IDF 키워드 데이터를 전처리하여 JS 파일 내 전역 객체로 빌드하는 스크립트입니다.
- **Bento Grid 웹앱 대시보드**: [dashboard.html](../src/dashboard.html)
  - 라이트 모드(Nordic Light) 및 다크 모드(Glassmorphism Sleek Dark) 실시간 테마 스위치를 제공하며, 요약 메트릭, 5개의 Chart.js 인터랙티브 차트 및 실시간 Instant Search/정렬/필터가 가능한 도서 목록 테이블을 Bento Grid 레이아웃에 탑재한 웹앱 페이지입니다.

## 2. 수집된 데이터 사양 및 검증

### 데이터셋 필드 (총 11개 열)
- `순위` (1 ~ 449)
- `도서명`
- `저자`
- `출판사`
- `출판일` (YYYY-MM-DD 포맷 정제 완료)
- `정가`
- `판매가`
- `평점`
- `리뷰수`
- `상품코드` (도서 고유 ID)
- `상세설명` (책 소개 및 상세 설명 텍스트, `inbukCntt` 수집 완료)

## 3. 대시보드 인터랙티브 차트 명세
1. **정가 및 판매가 분포**: 도서 가격 구간별 듀얼 Bar 차트
2. **출판사 시장 점유율**: 상위 10대 출판사 도서 빈도 Doughnut 차트
3. **도서 만족도 분포**: 평점 구간별 Polar Area 차트
4. **상세설명 핵심 키워드**: TF-IDF 가중치 상위 15 Horizontal Bar 차트
5. **평점 대비 리뷰 수 상관관계**: 도서 흥행 상관도 Scatter 차트
