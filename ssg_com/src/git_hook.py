"""
Git 자동 커밋 훅 헬퍼 모듈

이 모듈은 데이터 수집이나 분석 보고서 생성이 완료된 후
해당 파일들을 Git에 자동으로 스테이징(add)하고 커밋(commit)하는 후속 훅 기능을 제공합니다.
"""
# -*- coding: utf-8 -*-
import subprocess
import os

def execute_git_commit(file_paths, message):
    """
    지정된 파일 경로 리스트를 Git에 add하고 지정된 메시지로 commit을 실행합니다.
    """
    try:
        # Git 리포지토리 여부 확인
        status_res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                                    capture_output=True, text=True, check=True)
        if "true" not in status_res.stdout.strip():
            print("[Git 훅 경고] 현재 작업 경로가 Git 리포지토리 내부가 아닙니다.")
            return False
            
        # 1. git add 실행
        for path in file_paths:
            if not os.path.exists(path):
                print(f"[Git 훅 경고] 파일이 존재하지 않아 add할 수 없습니다: {path}")
                continue
            subprocess.run(["git", "add", path], check=True)
            print(f"[Git 훅] git add 완료: {path}")
            
        # 2. 변경 내용이 있는지 확인 (diff-index)
        diff_res = subprocess.run(["git", "diff-index", "--cached", "HEAD", "--"], 
                                  capture_output=True, text=True)
        
        # 첫 번째 커밋이거나 캐시된 변경이 있는 경우 커밋 수행
        if diff_res.returncode == 0 and not diff_res.stdout.strip():
            print("[Git 훅 정보] 커밋할 변경 사항(Staged)이 없습니다.")
            return True
            
        # 3. git commit 실행
        commit_res = subprocess.run(["git", "commit", "-m", message], 
                                    capture_output=True, text=True, check=True)
        print(f"[Git 훅 성공] 자동 커밋 완료! 메시지: '{message}'")
        print(commit_res.stdout.strip())
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[Git 훅 실패] Git 명령어 실행 중 오류가 발생했습니다: {e}")
        if e.stderr:
            print(e.stderr.strip())
        return False
    except Exception as e:
        print(f"[Git 훅 오류] 자동 커밋 진행 중 알 수 없는 예외 발생: {e}")
        return False
