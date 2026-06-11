# 스타벅스 데이터 파이프라인 프레임워크 구축 및 EDA 계획

데이터 파이프라인 프레임워크 스킬(`data-pipeline-framework`)을 기반으로 스타벅스 매장 정보의 수집, 정제, EDA 시각화 및 대시보드 데이터 컴파일 파이프라인을 자동화합니다.

## User Review Required

> [!IMPORTANT]
> - 기존에 작성된 `store_crawler.py` 수집 로직을 프레임워크 스킬의 `scraping.py` 템플릿에 맞추어 이식합니다.
> - `eda.py` 템플릿은 데이터의 시각화 및 핵심 키워드 리포팅을 자동으로 수행하며, 이를 스타벅스 데이터 스키마(예: 매장명, 주소, 시도명 등)에 부합하도록 커스텀 처리합니다.
> - 모든 산출물 경로는 워크스페이스 내 상대 경로 기준을 준수합니다.

## Proposed Changes

### Configuration Setup
- `starbucks_config.json`을 워크스페이스 루트에 설정 파일로 생성하여 프레임워크 엔진의 입력으로 사용합니다.

### Framework Engine Initialization (Init)
- 아래 명령을 실행하여 프로젝트를 초기화하고 템플릿 코드를 배포합니다.
  ```bash
  uv run python .agents/skills/data-pipeline-framework/engine.py init --config starbucks_config.json
  ```

### Customization of Deployed Source Codes
- **[MODIFY] [scraping.py](../src/scraping.py)**: 스타벅스 `getSidoList.do` 및 `getStore.do` API 호출 방식으로 구현된 재시도 및 수집 로직을 이식합니다.
- **[MODIFY] [eda.py](../src/eda.py)**: 스타벅스 매장 분포 및 주소 키워드 빈도를 다차원 분석하고 차트를 생성하도록 수정합니다.
- **[MODIFY] [dashboard_data_builder.py](../src/dashboard_data_builder.py)**: 수집된 스타벅스 매장 정보를 대시보드 컴파일러 포맷에 맞춥니다.

### Pipeline Execution (Run)
- 전체 파이프라인 단계를 통합 구동하여 데이터 수집 및 EDA 차트 작성을 완료합니다.
  ```bash
  uv run python .agents/skills/data-pipeline-framework/engine.py run --config starbucks_config.json --step all
  ```

## Verification Plan

### Automated Tests
- 전체 파이프라인 실행 명령어가 정상 반환 코드(`0`)로 종료되는지 확인합니다.
- 생성되는 차트 이미지 파일(`starbucks/images/*.png`) 및 보고서 파일(`starbucks/docs/*.csv`)의 무결성을 검사합니다.
