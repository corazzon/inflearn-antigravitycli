# 스타벅스 데이터 수집기 구현 태스크 리스트

- [x] 가상환경 의존성 패키지 설치 (`requests`, `pandas` 등)
- [x] 스타벅스 매장 정보 수집기 소스코드 구현 (`../src/store_crawler.py`)
  - [x] 시도 코드 API 조회 (`getSidoList.do`)
  - [x] 매장 API 조회 (`getStore.do`) 및 데이터 파싱
  - [x] 랜덤 딜레이 및 지수 백오프 재시도 구현
  - [x] 서울 테스트 모드 및 전국 수집 모드 구현
- [x] 데이터 수집 검증
  - [x] 서울 매장 선 수집 테스트 실행 및 정합성 검증
  - [x] 전국 매장 전체 수집 실행 및 확인
- [x] README.md 및 수집 보고서 작성
  - [x] `./README.md` 작성
  - [x] `../reports/store_crawl_report.md` 작성
