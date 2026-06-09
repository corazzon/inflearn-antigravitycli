# Data Pipeline Framework Skill

이 스크킬은 신규 웹사이트를 대상으로 데이터 수집, 정제, EDA(탐색적 데이터 분석), 그리고 대형 대시보드 시각화 웹앱 빌드를 자동화하는 프레임워크 스킬입니다.

## 기능 구성
1. **API Inspect**: Playwright로 dynamic network request를 탐색하여 보안 인증 키(`x-api-gw-key` 등)를 식별 및 획득합니다.
2. **Robust Scraper**: 지수 백오프(Exponential Backoff) 재시도 로직을 적용하여 유실 없는 원천 데이터 고속 수집 및 CSV(UTF-8-sig 인코딩) 저장을 지원합니다.
3. **Automated EDA**: 11개의 주요 다차원 분석 차트 이미지 시각화 및 TF-IDF 기반 핵심 키워드 리포팅을 자동으로 수행합니다.
4. **JS Data Compiler**: 로컬 파일 시스템 제약 하에서도 호스팅 가능한 Bento Grid 대시보드 웹앱 맞춤 데이터 자바스크립트 컴파일러를 기동합니다.
5. **Hook System**: `post_scrape`, `post_eda`, `on_failure` 단계별 커스텀 스크립트 실행 트리거를 지원합니다.

## CLI 사용법

### 1. 설정 파일(`config.json`) 준비
프로젝트 설정 파일 예시:
```json
{
  "project_name": "example_project",
  "target_url": "https://example.com/bestseller",
  "api_url": "https://api.example.com/v1/list",
  "retry_config": {
    "max_retries": 5,
    "backoff_factor": 1.5
  },
  "hooks": {
    "post_scrape": "python example_project/src/validate.py",
    "post_eda": "python example_project/src/dashboard_data_builder.py"
  }
}
```

### 2. 프로젝트 초기화 (Init)
```bash
uv run python .agents/skills/data-pipeline-framework/engine.py init --config config.json
```
- 프로젝트 디렉토리 구조(`src`, `data`, `images`, `docs`, `reports`)가 생성되고 치환 코드가 자동 배포됩니다.

### 3. 파이프라인 전체 실행 (Run)
```bash
uv run python .agents/skills/data-pipeline-framework/engine.py run --config config.json --step all
```
- 단계를 개별 가동하려면 `--step inspect`, `--step scrape`, `--step eda`, `--step dashboard` 매개변수를 지정합니다.
