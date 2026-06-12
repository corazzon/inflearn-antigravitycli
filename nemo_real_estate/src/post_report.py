# -*- coding: utf-8 -*-
"""
네모앱(nemoapp.kr) 파이프라인 후처리 및 자동 커밋 스크립트

이 스크립트는 데이터 분석 및 대시보드 데이터 빌드 단계가 완료된 후 실행됩니다:
1. 워드 보고서 생성 스크립트(generate_docx.py) 실행
2. PPTX 발표자료 생성 스크립트(generate_pptx.py) 실행
3. PPTX 발표자료를 PDF로 자동 변환 (LibreOffice soffice 도구 활용)
4. nemo_real_estate 폴더 하위의 변경사항들을 Git에 자동 스테이징 및 커밋 수행
"""

import subprocess
import sys
import os

def run_cmd(cmd, cwd=None):
    print(f"[Post-Report] 실행 중: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    if res.returncode != 0:
        print(f"[Post-Report] [Error] 실행 실패: {cmd}")
        return False
    return True

def main():
    # 현재 스크립트의 절대 경로 기준 프로젝트 루트
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    python_exe = os.path.join(base_dir, ".venv", "bin", "python")
    
    # 1. 워드 보고서 생성
    print("\n[Post-Report] [1/4] DOCX 워드 보고서 생성 시작...")
    docx_script = os.path.join("nemo_real_estate", "src", "generate_docx.py")
    if not run_cmd(f"{python_exe} {docx_script}", cwd=base_dir):
        print("[Post-Report] [Error] 워드 보고서 생성에 실패했습니다.")
        return False
        
    # 2. PPTX 발표자료 생성
    print("\n[Post-Report] [2/4] PPTX 발표자료 생성 시작...")
    pptx_script = os.path.join("nemo_real_estate", "src", "generate_pptx.py")
    if not run_cmd(f"{python_exe} {pptx_script}", cwd=base_dir):
        print("[Post-Report] [Error] PPTX 발표자료 생성에 실패했습니다.")
        return False
        
    # 3. PDF 변환 (soffice 실행)
    print("\n[Post-Report] [3/4] PPTX 발표자료를 PDF로 변환 시작...")
    pdf_cmd = "soffice --headless --convert-to pdf --outdir nemo_real_estate/reports nemo_real_estate/reports/real_estate_presentation.pptx"
    if not run_cmd(pdf_cmd, cwd=base_dir):
        print("[Post-Report] [Warning] PDF 변환 명령을 수행할 수 없습니다. LibreOffice 설치 여부를 확인하십시오.")
        # PDF 변환 실패는 소프트 페일로 처리하여 Git 커밋 단계는 계속 진행
        
    # 4. Git 자동 커밋
    print("\n[Post-Report] [4/4] Git 변경사항 자동 스테이징 및 커밋 시작...")
    # 작업 디렉토리에 변경 내용이 있는지 체크
    status_res = subprocess.run("git status --porcelain nemo_real_estate/", shell=True, capture_output=True, text=True, cwd=base_dir)
    if not status_res.stdout.strip():
        print("[Post-Report] 변경된 파일이 없어 Git 커밋을 건너뜁니다.")
        return True
        
    git_add = "git add nemo_real_estate/"
    git_commit = 'git commit -m "auto: update real estate reports, data and dashboard [skip ci]"'
    
    if run_cmd(git_add, cwd=base_dir):
        run_cmd(git_commit, cwd=base_dir)
        
    print("\n[Post-Report] [Success] 후처리 파이프라인 및 자동 커밋이 완료되었습니다.")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
