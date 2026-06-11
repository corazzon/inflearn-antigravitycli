# -*- coding: utf-8 -*-
"""
범용 데이터 파이프라인 프레임워크 CLI 엔진 스크립트
설정 파일(config.json)의 column_mapping 정보를 적용하여 대시보드 템플릿의 컬럼명을 동적으로 치환 배포합니다.
"""

import os
import sys
import json
import argparse
import subprocess

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def load_config(config_path):
    if not os.path.exists(config_path):
        print(f"[Engine] [Error] 설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_cmd(command, cwd=None):
    print(f"[Engine] 실행 중: {command}")
    res = subprocess.run(command, shell=True, cwd=cwd)
    if res.returncode != 0:
        print(
            f"[Engine] [Error] 명령어 실행 실패 (반환 코드: {res.returncode}): {command}"
        )
        return False
    return True


def cmd_init(args):
    config = load_config(args.config)
    project_name = config.get("project_name")
    target_url = config.get("target_url")

    if not project_name:
        print("[Engine] [Error] project_name 설정이 누락되었습니다.")
        sys.exit(1)

    print(f"[Engine] 신규 프로젝트 '{project_name}' 초기화를 시작합니다...")

    # 1. 디렉토리 구조 생성
    dirs = [
        f"{project_name}/src",
        f"{project_name}/data",
        f"{project_name}/images",
        f"{project_name}/docs",
        f"{project_name}/reports",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"디렉토리 생성: {d}")

    # 2. 템플릿 치환 배포 (컬럼 매핑 기본값 적용)
    column_map = config.get("column_mapping", {})
    replacements = {
        "__PROJECT_NAME__": project_name,
        "__TARGET_URL__": target_url if target_url else "",
        "__API_URL__": config.get("api_url", ""),
        "__MAX_RETRIES__": str(
            config.get("retry_config", {}).get("max_retries", 5)
        ),
        "__BACKOFF_FACTOR__": str(
            config.get("retry_config", {}).get("backoff_factor", 1.5)
        ),
        "__CSV_PATH__": f"{project_name}/data/{project_name}_bestseller.csv",
        "__IMAGE_DIR__": f"{project_name}/images",
        "__TXT_REPORT_PATH__": f"{project_name}/docs/basic_statistics.txt",
        "__TFIDF_CSV_PATH__": f"{project_name}/docs/tfidf_keywords.csv",
        "__OUTPUT_JS_PATH__": f"{project_name}/src/dashboard_data.js",
        # 컬럼 레이블 매핑 변수들
        "__NAME_LABEL__": column_map.get("name", "명칭 (name)"),
        "__CATEGORY_LABEL__": column_map.get("category", "분류 (category)"),
        "__VALUE_1_LABEL__": column_map.get("value_1", "수치 1 (value_1)"),
        "__VALUE_2_LABEL__": column_map.get("value_2", "수치 2 (value_2)"),
        "__DETAIL_TEXT_LABEL__": column_map.get(
            "detail_text", "상세 정보 (detail_text)"
        ),
    }

    # 배포할 파일 목록
    templates = {
        "inspect_api_template.py": f"{project_name}/src/inspect_api.py",
        "scraping_template.py": f"{project_name}/src/scraping.py",
        "eda_template.py": f"{project_name}/src/eda.py",
        "dashboard_data_builder_template.py": f"{project_name}/src/dashboard_data_builder.py",
        "dashboard_template.html": f"{project_name}/src/dashboard.html",
    }

    for t_name, dest_path in templates.items():
        src_path = os.path.join(TEMPLATES_DIR, t_name)
        if not os.path.exists(src_path):
            print(f"[Warning] 템플릿 소스 파일을 찾을 수 없습니다: {src_path}")
            continue

        with open(src_path, "r", encoding="utf-8") as sf:
            content = sf.read()

        # 변수 치환
        for key, val in replacements.items():
            content = content.replace(key, val)

        with open(dest_path, "w", encoding="utf-8") as df:
            df.write(content)
        print(f"템플릿 배포 및 치환 완료: {dest_path}")

    print(f"[Engine] 프로젝트 '{project_name}' 초기화 완료!")


def cmd_run(args):
    config = load_config(args.config)
    project_name = config.get("project_name")

    if not project_name:
        print("[Engine] [Error] project_name 설정이 누락되었습니다.")
        sys.exit(1)

    step = args.step
    print(
        f"[Engine] 파이프라인 단계 구동 시작: {step} (프로젝트: {project_name})"
    )

    # venv 파이썬 경로 획득
    python_exe = sys.executable

    if step == "all" or step == "inspect":
        print("[Engine] [Step 1] API 탐색 (inspect_api.py) 실행...")
        if not run_cmd(f"{python_exe} {project_name}/src/inspect_api.py"):
            sys.exit(1)

    if step == "all" or step == "scrape":
        print("[Engine] [Step 2] 데이터 수집 (scraping.py) 실행...")
        if not run_cmd(f"{python_exe} {project_name}/src/scraping.py"):
            sys.exit(1)

        # post_scrape 훅 실행
        hook = config.get("hooks", {}).get("post_scrape")
        if hook:
            print("[Engine] [Hook] post_scrape 훅 실행...")
            if not run_cmd(hook):
                print(
                    "[Engine] [Warning] post_scrape 훅 실행 실패. 후속 단계를 계속 진행합니다."
                )

    if step == "all" or step == "eda":
        print("[Engine] [Step 3] 데이터 분석 (eda.py) 실행...")
        if not run_cmd(f"{python_exe} {project_name}/src/eda.py"):
            sys.exit(1)

    if step == "all" or step == "dashboard":
        print(
            "[Engine] [Step 4] 대시보드 데이터 빌드 (dashboard_data_builder.py) 실행..."
        )
        if not run_cmd(
            f"{python_exe} {project_name}/src/dashboard_data_builder.py"
        ):
            sys.exit(1)

        # post_eda 훅 실행
        hook = config.get("hooks", {}).get("post_eda")
        if hook:
            print("[Engine] [Hook] post_eda 훅 실행...")
            run_cmd(hook)

    print("[Engine] 지정된 단계가 성공적으로 완수되었습니다!")


def main():
    parser = argparse.ArgumentParser(
        description="Antigravity 데이터 파이프라인 프레임워크 CLI 엔진"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    parser_init = subparsers.add_parser(
        "init", help="신규 프로젝트 디렉토리 생성 및 소스코드 복사/치환"
    )
    parser_init.add_argument(
        "--config", required=True, help="설정 파일(config.json) 경로"
    )
    parser_init.set_defaults(func=cmd_init)

    # run command
    parser_run = subparsers.add_parser(
        "run", help="데이터 파이프라인 단계별 구동"
    )
    parser_run.add_argument(
        "--config", required=True, help="설정 파일(config.json) 경로"
    )
    parser_run.add_argument(
        "--step",
        choices=["all", "inspect", "scrape", "eda", "dashboard"],
        default="all",
        help="구동할 단계 (기본값: all)",
    )
    parser_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
