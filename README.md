# 📚 도서 베스트셀러 데이터 수집 및 분석 대시보드 프로젝트

본 리포지토리는 교보문고 컴퓨터/IT 카테고리의 일간 베스트셀러 도서 데이터를 동적으로 수집하여 탐색적 데이터 분석(EDA)을 수행하고, 이를 한눈에 볼 수 있는 인터랙티브 웹 대시보드를 구축해 배포하는 프로젝트입니다.

---

## 🚀 실시간 웹 대시보드 서비스

인터넷이 연결된 환경이라면 어디서든 아래 링크를 통해 실시간으로 분석된 교보문고 베스트셀러 통계와 상세 도서 목록을 인터랙티브하게 탐색할 수 있습니다.

- **교보문고 대시보드 링크**: [https://corazzon.github.io/inflearn-antigravitycli/src/index.html](https://corazzon.github.io/inflearn-antigravitycli/src/index.html)

### 💻 대시보드 주요 기능
* **Bento Grid 레이아웃**: 핵심 지표 요약(KPI) 카드와 차트 영역이 바둑판 배열로 정돈되어 있어 가독성이 뛰어납니다.
* **5가지 인터랙티브 차트 (Chart.js)**:
  1. *정가 및 판매가 분포* (Bar 차트)
  2. *출판사 시장 점유율 Top 10* (Doughnut 차트)
  3. *도서 만족도 분포* (Polar Area 차트)
  4. *상세설명 핵심 키워드 중요도* (TF-IDF Horizontal Bar 차트)
  5. *평점 대비 리뷰 수 상관관계* (Scatter 차트)
* **실시간 반응형 테이블**: 도서명, 저자, 출판사를 타이핑하는 즉시 필터링되며, 정렬 기능을 통해 순위나 가격, 평점 등으로 도서 목록을 재배치할 수 있습니다.
* **라이트 & 다크 모드**: 우측 상단 토글 버튼을 통해 다크 모드(유리효과 적용)와 라이트 모드 간 실시간 테마 전환이 가능합니다.
* **상세정보 팝업 모달**: 테이블의 도서를 클릭하면 책의 상세 설명 본문(`inbukCntt`)을 깔끔한 모달창으로 읽을 수 있습니다.

---

## 📂 프로젝트 폴더 구조

```bash
workspace/
  ├── .github/workflows/
  │     └── static.yml                # GitHub Pages 자동 배포 CI/CD 워크플로우
  ├── kyobobooks/
  │     ├── data/
  │     │     └── kyobo_bestseller.csv # 수집된 일간 베스트셀러 데이터 (총 449건)
  │     ├── docs/
  │     │     ├── scaraping_prompt.md  # 스크래핑 설계 명세서
  │     │     ├── task.md              # 프로젝트 관리 태스크 대장
  │     │     ├── walkthrough.md       # 수집 완료 보고서
  │     │     └── EDA_Report.md        # 데이터 EDA 종합 리포트 (3,000자 이상)
  │     ├── images/
  │     │     └── *.png                # 11개의 EDA 시각화 그래프 이미지 파일
  │     └── src/
  │           ├── inspect_api.py       # Playwright 기반 API 게이트웨이 키 탐색기
  │           ├── scraping.py          # 일간 베스트셀러 동적 크롤링 스크래퍼
  │           ├── eda.py               # 시각화 및 TF-IDF 키워드 도출 분석기
  │           ├── dashboard_data_builder.py # 대시보드 주입용 데이터 프리프로세서
  │           ├── dashboard_data.js    # 변환된 대시보드 바인딩 데이터셋
  │           ├── dashboard.html       # 대시보드 뷰 HTML 소스코드
  │           └── index.html           # 대시보드 기본 진입점
  └── yes24/
        └── ...                        # YES24 관련 기존 작업 폴더
```

---

## ⚙️ 실행 및 로컬 개발 가이드

프로젝트는 패키지 관리 및 가상환경 관리 도구인 `uv`를 사용합니다.

### 1. 의존성 패키지 설치
```bash
uv pip install playwright nest-asyncio pandas openpyxl scikit-learn seaborn matplotlib koreanize-matplotlib
uv run playwright install chromium
```

### 2. 스크래핑 및 분석 파이프라인 가동
```bash
# 1단계: API 게이트웨이 보안 키(x-api-gw-key) 구조 파악
uv run python kyobobooks/src/inspect_api.py

# 2단계: 끝페이지(449위)까지 안전하게 도서 상세 정보 수집
uv run python kyobobooks/src/scraping.py

# 3단계: 탐색적 데이터 분석(EDA) 및 11개 차트 이미지 생성
uv run python kyobobooks/src/eda.py

# 4단계: 수집된 데이터를 대시보드용 전역 자바스크립트로 빌드
uv run python kyobobooks/src/dashboard_data_builder.py
```

빌드가 정상 완료되면 `kyobobooks/src/dashboard.html` 또는 `kyobobooks/src/index.html` 파일을 크롬 브라우저 등에서 더블 클릭하여 즉시 실행하고 분석 보고서를 모니터링할 수 있습니다.
