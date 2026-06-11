# 스타벅스 전국 매장 정보 수집 및 EDA 완료 결과서 (Walkthrough)

데이터 파이프라인 프레임워크 스킬(`data-pipeline-framework`)을 적용하여 스타벅스 매장 정보의 수집, 정제, EDA 시각화 분석 단계를 성공적으로 구동 완료하였습니다.

## 주요 수행 및 결과 사항

1. **프레임워크 초기화**: `starbucks_config.json` 설정에 따라 디렉토리 구조 및 기본 코드가 배포되었습니다.
2. **스크래퍼 최적화 ([scraping.py](../src/scraping.py))**:
   - 지수 백오프 및 랜덤 딜레이 요청 구조에 스타벅스 API(시도 코드 루프 및 POST 호출) 수집 로직을 안전하게 이식하였습니다.
   - 스타벅스 고유 지리 데이터 스펙 중 경도 정보의 키(`lot`) 매핑 오류를 진단하고 패치 완료하였습니다.
   - 수집된 정보를 프레임워크 공통 5대 속성(`name`, `category`, `value_1`[위도], `value_2`[경도], `detail_text`[주소/연락처]) 데이터셋으로 규격화하여 [starbucks_bestseller.csv](../data/starbucks_bestseller.csv) 파일에 저장했습니다.
3. **탐색적 데이터 분석 ([eda.py](../src/eda.py))**:
   - 수집된 전국 2,157개 매장 정보를 분석하여 기초 통계 문서([basic_statistics.txt](./basic_statistics.txt))를 작성했습니다.
   - 지리적 좌표 분석을 위한 위경도 분포 산점도를 지도 형상으로 구현하는 등 총 11가지 분석 차트 이미지([images/](../images))를 자동 렌더링하였습니다.
   - 매장 주소 상세 텍스트를 분석하여 중요 키워드 가중치를 정량 추출([tfidf_keywords.csv](./tfidf_keywords.csv))하였습니다.
4. **JS 대시보드 컴파일 ([dashboard_data_builder.py](../src/dashboard_data_builder.py))**:
   - 로컬 호스팅 제약 없이 구동 가능한 Bento Grid 형상의 자바스크립트 변수 데이터 파일([dashboard_data.js](../src/dashboard_data.js))을 완성했습니다.

## 주요 생성 산출물 (상대 경로 기준)

- **설정 파일**: [starbucks_config.json](../../starbucks_config.json)
- **통계 리포트**: [basic_statistics.txt](./basic_statistics.txt)
- **주소 키워드 가중치**: [tfidf_keywords.csv](./tfidf_keywords.csv)
- **데이터 분석 차트 (총 11개)**: [starbucks/images/](../images)
  - 전국 매장 위경도 산점도 지도: [07_price_vs_sale_price.png](../images/07_price_vs_sale_price.png)
  - 시도별 매장 점유수 분포: [05_top_publishers.png](../images/05_top_publishers.png)
  - 주소 텍스트 핵심 키워드 중요도: [11_tfidf_keywords_bar.png](../images/11_tfidf_keywords_bar.png)
- **최종 데이터셋**:
  - CSV 데이터셋: [starbucks_bestseller.csv](../data/starbucks_bestseller.csv)
  - Raw 백업 JSON: [raw_starbucks_stores.json](../data/raw_starbucks_stores.json)

---

## 데이터 분석 요약 (Summary of EDA)

```text
=== 수치형 기술통계 ===
                순위      value_1(위도)   value_2(경도)
count  2157.000000  2157.000000      2157.000000
mean   1079.000000    36.798229       127.399891
std     622.816586     1.026755         0.796809
min       1.000000    33.206777       126.240490  (제주도 서부 지역)
max    2157.000000    38.213347       129.454821  (울릉도 등 동부 지역)
```
- **지리적 경계**: 전국 스타벅스 매장은 대한민국 영토(위도 33°~38°, 경도 126°~129°) 내에 정확히 맵핑되어 지리지도 형상 차트([07_price_vs_sale_price.png](../images/07_price_vs_sale_price.png))로 성공적으로 시각화되었습니다.
- **주소 텍스트**: TF-IDF 분석 결과 구/동 명칭(예: '역삼역', '서초동' 등 핵심 상권 단어)이 고주파 가중치 항목으로 검출되었습니다.
