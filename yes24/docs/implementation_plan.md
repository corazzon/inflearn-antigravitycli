# YES24 베스트셀러 데이터 탐색적 데이터 분석(EDA) 계획서

본 계획서는 `yes24/data/yes24_bestsellers.csv` 파일을 분석하여 YES24 베스트셀러의 특징, 가격 분포, 판매지수 상관관계, 주요 저자 및 출판사 정보, 그리고 도서명/태그 텍스트 분석(TF-IDF)을 진행하기 위한 상세 실행 계획입니다.

## User Review Required

> [!IMPORTANT]
> - **시각화 관련 제한**: `seaborn` 스타일을 배제하고 vanilla matplotlib 및 사용자 지정 고대비 팔레트만 사용합니다.
> - **한글 폰트 적용**: 그래프의 한글 깨짐을 방지하기 위해 `koreanize-matplotlib` 라이브러리를 필수적으로 사용합니다.
> - **텍스트 분석**: 형태소 분석기(KoNLPy 등) 대신 **TF-IDF** 분석을 사용하여 도서명 및 태그의 키워드 분석을 신속하고 정확하게 수행합니다.
> - **기술통계 분량**: 수치형 및 범주형 분석 리포트는 각각 한국어 기준 **1000자 이상**의 상세한 인사이트를 포함하여 작성합니다.

## Proposed Changes

EDA 작업을 실행하기 위해 다음과 같이 파일을 생성하고 분석을 진행할 예정입니다.

### [EDA Execution Component]

#### [NEW] [eda.py](../src/eda.py)
- pandas, matplotlib, koreanize-matplotlib, scikit-learn(TF-IDF)을 활용하여 데이터를 로드, 정제, 통계치 산출 및 시각화 이미지를 생성하는 파이썬 스크립트입니다.
- 정제 대상:
  - `sale_price`, `original_price`에서 쉼표(`,`)를 제거하고 수치형(int)으로 변환
  - `point` 열에서 숫자만 추출하여 포인트(int) 변환
  - `publish_date`에서 연도 및 월 정보를 추출
  - 결측치 처리 및 중복 데이터(goods_no 기준) 확인

#### [NEW] [eda_report.md](eda_report.md)
- 분석 결과 및 시각화 자료를 종합하여 작성하는 최종 한글 EDA 보고서입니다.
- 분석 결과는 20년 경력의 베테랑 데이터 분석가 관점에서 깊이 있는 비즈니스 인사이트로 작성됩니다.

## 시각화 계획 (13개 그래프 예정)

최소 10개 이상의 시각화 요구조건을 충족하기 위해 아래의 그래프들을 생성하고, 각 그래프마다 **데이터 테이블(Crosstab/Pivot/Descriptive stats)** 및 **최소 50자 이상의 설명**을 포함합니다.

1. **도서 가격(sale_price) 분포** (히스토그램 & KDE)
2. **판매지수(sale_index) 분포** (상자 그림 - Box plot)
3. **도서 평점(rating) 분포** (히스토그램)
4. **리뷰 수(review_count) 분포** (상자 그림 및 분포도)
5. **분철 서비스 제공 여부(spring_service) 비율** (원형 차트)
6. **베스트셀러 등록 도서 수가 가장 많은 출판사 Top 30** (가로 막대 그래프)
7. **베스트셀러 등록 도서 수가 가장 많은 저자 Top 30** (가로 막대 그래프)
8. **도서 정가(original_price)와 판매지수(sale_index)의 산점도**
9. **평점(rating)과 리뷰 수(review_count)의 산점도**
10. **분철 서비스 제공 여부(spring_service)에 따른 판매지수(sale_index) 비교** (Box plot)
11. **출판 연도 및 월별 베스트셀러 도서 출판 추이** (꺾은선 그래프)
12. **수치형 변수들 간의 상관계수 히트맵 (Correlation Heatmap)**
13. **TF-IDF 기반 도서명/태그 주요 키워드 Top 30** (막대 그래프)

## Verification Plan

### Automated Tests
- 가상환경 `.venv`에서 필요한 패키지들을 설치하고 `python yes24/src/eda.py` 스크립트가 오류 없이 완수되는지 검증합니다.
- 필요한 패키지: `pandas`, `matplotlib`, `koreanize-matplotlib`, `scikit-learn` 등

### Manual Verification
- 생성된 13개의 시각화 플롯 이미지 파일이 `yes24/images/` 디렉토리에 정상적으로 저장되었는지 확인합니다.
- 최종 `yes24/docs/eda_report.md` 파일이 작성 가이드라인(1000자 이상의 통계 보고서, 시각화 설명 50자 이상, 한글 폰트 적용 등)을 정확히 지켰는지 셀프 체크리스트를 기반으로 검토합니다.
