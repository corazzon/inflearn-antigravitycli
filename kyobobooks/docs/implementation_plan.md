# 교보문고 베스트셀러 웹앱 대시보드 구현 계획

수집된 교보문고 컴퓨터/IT 분야 일간 베스트셀러 데이터(총 449건)를 브라우저에서 직관적으로 탐색할 수 있는 반응형 웹 대시보드를 구축합니다.

## User Review Required

> [!NOTE]
> - **기술 스택**: 단일 파일 구조의 HTML, CSS, JavaScript (CDN을 통한 Chart.js 및 구글 폰트 로드)
> - **서버 CORS 우회 솔루션**: 사용자가 웹 서버 구동 없이도 로컬에서 HTML 파일을 더블 클릭해 즉시 열 수 있도록, 파이썬 스크립트(`dashboard_data_builder.py`)를 가동하여 수집된 CSV 데이터를 `dashboard_data.js` 파일 내의 전역 자바스크립트 객체(`window.DASHBOARD_DATA`)로 빌드하여 HTML에 주입합니다.
> - **테마 모드**: 라이트 모드(Nordic Light)와 다크 모드(Glassmorphism Sleek Dark)를 동시에 지원하는 토글 스위치 구현.
> - **레이아웃**: Modern Bento Grid 레이아웃 사용.

## Proposed Changes

### kyobobooks

---

#### [NEW] [dashboard_data_builder.py](../src/dashboard_data_builder.py)
`kyobobooks/data/kyobo_bestseller.csv` 데이터를 로드하고, 통계 요약 및 TF-IDF 키워드 정보를 사전에 추출하여 `kyobobooks/src/dashboard_data.js` 파일에 자바스크립트 전역 변수로 변환 및 내보내기하는 전처리 스크립트입니다.

#### [NEW] [dashboard.html](../src/dashboard.html)
웹앱 대시보드의 메인 인터페이스 파일입니다. CSS 스타일(라이트/다크 모드 변수, Bento Grid, 유리효과) 및 Chart.js 초기화 코드와 인터랙티브 검색/정렬 도서 테이블을 포함합니다.

#### [NEW] [dashboard_data.js](../src/dashboard_data.js)
`dashboard_data_builder.py`에 의해 자동 생성되는 로컬 데이터 파일로, 대시보드가 오프라인에서도 작동하도록 지원합니다.

---

## Verification Plan

### Automated Tests
1. **데이터 빌더 실행**:
   ```bash
   uv run python kyobobooks/src/dashboard_data_builder.py
   ```
   - `kyobobooks/src/dashboard_data.js` 파일이 오류 없이 정상 생성되었는지 확인합니다.
2. **대시보드 구동**:
   - `kyobobooks/src/dashboard.html` 파일을 브라우저로 직접 실행하거나 간이 서버(Streamlit/Live server)를 기동하여 시각적으로 검증합니다.
   - 5개의 인터랙티브 차트가 깨짐 없이 로드되고 테마 전환이 매끄러운지 확인합니다.

### Manual Verification
- 라이트/다크 모드 전환 시 차트 글씨 색상 및 그리드 색상이 동적으로 변경되는지 점검합니다.
- 데이터 테이블에서 검색어 입력 시 실시간으로 행이 필터링되는지 점검합니다.
