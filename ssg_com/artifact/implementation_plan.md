# SSG.COM 해피바이 특가 정보 수집 및 자동 커밋 훅 적용 계획

SSG.COM 해피바이 특가 수집 및 분석 보고서 생성이 완료되면 자동으로 파일들을 Git에 커밋해주는 훅(Hook) 기능을 설계하여 파이프라인의 버전 관리를 자동화합니다.

## User Review Required

> [!IMPORTANT]
> - **자동 커밋 동작**: 스크립트(`scraper.py`, `eda_analysis.py`) 완료부에서 자동으로 `git add` 및 `git commit`을 쉘 명령어로 수행합니다.
> - **커밋 메시지 규칙**: 수집 데이터는 `[데이터 수집] happybuy_YYYYMMDD_HHMMSS.csv` 형태로, 분석 리포트는 `[분석 리포트] EDA_Report.md 및 시각화 이미지 갱신` 형태로 일목요연하게 기록되도록 커밋 메시지를 규격화합니다.

## Proposed Changes

### ssg_com (소스 및 아티팩트 관리)

#### [NEW] [git_hook.py](file:///Users/corazzon/work/inflearn-antigravitycli/ssg_com/src/git_hook.py)
- `# -*- coding: utf-8 -*-` 선언 및 한국어 docstring 필수 적용.
- 파일 경로와 커밋 메시지를 받아 `git add`와 `git commit` 명령어를 실행하는 `execute_git_commit(file_paths, message)` 헬퍼 함수 구현.
- 로컬 Git 리포지토리 상태 확인 및 에러 핸들링 탑재.

#### [MODIFY] [scraper.py](file:///Users/corazzon/work/inflearn-antigravitycli/ssg_com/src/scraper.py)
- 데이터 수집 및 CSV 저장이 완료된 직후, `git_hook.py`의 `execute_git_commit`을 호출하여 수집된 CSV 파일을 자동으로 Git 커밋합니다.

#### [MODIFY] [eda_analysis.py](file:///Users/corazzon/work/inflearn-antigravitycli/ssg_com/src/eda_analysis.py)
- EDA 분석 및 이미지 저장, 리포트 생성이 최종 완료되면 자동으로 이미지 폴더(`ssg_com/images/`)와 리포트(`ssg_com/reports/EDA_Report.md`)를 커밋합니다.

---

## Verification Plan

### Automated Tests
- `uv run python ssg_com/src/scraper.py` 실행 후, `git log -n 1` 명령을 통해 데이터 수집에 대한 자동 커밋이 수행되었는지 확인합니다.
- `uv run python ssg_com/src/eda_analysis.py` 실행 후, 분석 보고서에 대한 자동 커밋 로그가 잘 남았는지 확인합니다.
