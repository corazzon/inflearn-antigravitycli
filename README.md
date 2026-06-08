# 📚 국내 도서 베스트셀러 분석 & 시각화 통합 리포지토리

본 프로젝트는 국내 양대 온라인 서점인 **YES24**와 **교보문고**의 도서 데이터를 수집하고, 탐색적 데이터 분석(EDA)을 거쳐 엑셀/PPT 자동 생성 및 모던 웹앱 대시보드로 시각화하는 통합 데이터 공학 프로젝트입니다.

---

## 🌐 교보문고 실시간 웹 대시보드 서비스

교보문고 컴퓨터/IT 일간 베스트셀러(1위~449위) 전체 데이터와 도서 소개글을 시각적으로 탐색할 수 있는 인터랙티브 웹 대시보드가 배포되어 있습니다.

- **교보문고 대시보드 접속 주소**: [https://corazzon.github.io/inflearn-antigravitycli/src/index.html](https://corazzon.github.io/inflearn-antigravitycli/src/index.html)

### 💻 대시보드 주요 기능
* **실시간 테마 스위치**: 라이트(Nordic Light) / 다크(Glassmorphism Sleek Dark) 모드 실시간 토글 지원
* **5가지 Chart.js 인터랙티브 그래프**: 가격 분포, 출판사 점유율, 평점 분포, TF-IDF 핵심 키워드, 평점-리뷰 산점도 시각화
* **실시간 검색 및 다중 정렬**: 검색어 입력 시 즉각 필터링되는 테이블 및 순위/가격/평점 정렬 지원
* **상세 설명 팝업**: 도서 선택 시 상세 소개글을 읽을 수 있는 부드러운 모달 창 연동

---

## 🛠️ 서점별 주요 모듈 및 기능 요약

### 1. 교보문고 (KyoboBooks)
- **API 탐색 및 스펙화**: Playwright 브라우저 네트워크 감지를 통해 게이트웨이 보안 키(`x-api-gw-key`)를 캡처하여 명세로 수립하였습니다.
- **동적 스크래핑**: 수집 한계점(449위)까지 페이지를 루프로 돌며 정가, 판매가, 평점, 리뷰수, 책 소개글(`inbukCntt`)을 순차적으로 안전하게 크롤링합니다.
- **EDA & 텍스트 분석**: 11개의 분석 그래프를 생성하고, 상세설명 본문에서 KoNLPy 없이 Scikit-learn의 `TfidfVectorizer`를 활용해 핵심 키워드 30개를 도출하였습니다.

### 2. YES24
- **베스트셀러 크롤러**: YES24의 비동기 베스트셀러 목록 API를 활용한 소설/시 분야 도서 데이터 적재 파이프라인.
- **EDA & PPT 보고서 생성**: 데이터 분석 결과를 기반으로 python-pptx를 활용하여 트렌디한 **Neo-Brutalism 디자인 스타일**의 파워포인트 슬라이드 쇼를 자동 조립 및 빌드합니다.
- **엑셀 대시보드 연동**: 수집된 통계를 요약하여 보기 좋은 형태의 엑셀 대시보드 포맷으로 내보냅니다.

---

## 📂 프로젝트 폴더 구조

```bash
workspace/
  ├── .github/workflows/          # GitHub Pages 자동 배포 CI/CD 워크플로우
  ├── kyobobooks/                 # [교보문고 모듈]
  │     ├── data/                 # 수집 완료된 CSV 원시 데이터셋 (449건)
  │     ├── docs/                 # 작업 계획서, 태스크 대장, EDA 종합 보고서
  │     ├── images/               # 11개의 EDA 분석 그래프 이미지 (.png)
  │     └── src/                  # API 수집기, 분석기, 대시보드 HTML/JS/Builder 소스코드
  ├── yes24/                      # [YES24 모듈]
  │     ├── data/                 # YES24 스크래핑 데이터 적재 폴더
  │     ├── docs/                 # YES24 작업 내역 및 관련 문서
  │     ├── images/               # YES24 시각화 결과물 이미지 폴더
  │     └── src/                  # PPT 자동 조립기, Excel 대시보드 빌더, 크롤러 소스코드
  └── README.md                   # 통합 리포지토리 메인 설명문
```

---

## ⚙️ 실행 및 로컬 개발 가이드

본 리포지토리는 패키지 및 가상환경 관리 도구인 `uv`를 사용하며, 루트 폴더의 공통 `.venv` 가상환경을 공유하여 동작합니다.

### 1. 라이브러리 환경 설정
```bash
uv pip install playwright nest-asyncio pandas openpyxl scikit-learn seaborn matplotlib python-pptx koreanize-matplotlib
uv run playwright install chromium
```

### 2. 교보문고 모듈 구동 순서
```bash
# 1. API 보안 토큰 자동 캡처
uv run python kyobobooks/src/inspect_api.py

# 2. 전체 페이지 베스트셀러 데이터 크롤링
uv run python kyobobooks/src/scraping.py

# 3. EDA 리포트 및 시각화 이미지 11개 추출
uv run python kyobobooks/src/eda.py

# 4. 웹앱 대시보드용 데이터 전처리 및 JS 빌드
uv run python kyobobooks/src/dashboard_data_builder.py
```

### 3. YES24 모듈 구동 순서
```bash
# 1. YES24 베스트셀러 데이터 수집
uv run python yes24/src/scraping.py

# 2. 데이터 분석 및 기술통계 산출
uv run python yes24/src/eda.py

# 3. 엑셀 대시보드 및 PPT 슬라이드 보고서 자동 생성
uv run python yes24/src/create_excel_dashboard.py
uv run python yes24/src/generate_ppt_neobrutalism_v2.py
```
