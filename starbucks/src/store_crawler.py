# -*- coding: utf-8 -*-
"""
스타벅스 매장 정보를 수집하는 크롤러 스크립트입니다.
공식 웹사이트의 내부 API를 사용하여 매장 상세 정보(명칭, 주소, 위도, 경도 등)를 안전하게 수집합니다.
"""

import os
import sys
import json
import time
import random
import argparse
import requests
import pandas as pd

# 스타벅스 내부 API 엔드포인트 설정
SIDO_API_URL = "https://www.starbucks.co.kr/store/getSidoList.do"
STORE_API_URL = "https://www.starbucks.co.kr/store/getStore.do"

# 브라우저 요청 모방 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
}

# 상대 경로를 파이썬 파일 기준으로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def setup_directories():
    """데이터 저장용 폴더가 없으면 생성합니다."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def fetch_with_backoff(url, data=None, max_retries=5):
    """
    네트워크 요청을 처리하며, 지수 백오프(Exponential Backoff)를 적용한 재시도 로직을 탑재합니다.
    """
    retries = 0
    delay = 1.0  # 초기 딜레이(초)

    while retries < max_retries:
        try:
            # 서버 부하 방지를 위해 호출 전 랜덤 딜레이 추가 (0.5 ~ 1.0초)
            sleep_time = random.uniform(0.5, 1.0)
            time.sleep(sleep_time)

            response = requests.post(url, data=data, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()

        except (requests.exceptions.RequestException, ValueError) as e:
            retries += 1
            print(f"[경고] API 호출 실패 ({url}). 재시도 {retries}/{max_retries}. 오류: {e}")
            if retries >= max_retries:
                print(f"[에러] 최대 재시도 횟수를 초과했습니다. ({url})")
                raise

            # 지수 백오프 적용 (재시도할 때마다 대기 시간 증가 + 미세 노이즈 추가)
            backoff_delay = delay * (2 ** (retries - 1)) + random.uniform(0.1, 0.5)
            print(f"[알림] {backoff_delay:.2f}초 후 재시도합니다.")
            time.sleep(backoff_delay)


def get_sido_list():
    """시도 목록을 조회하여 반환합니다."""
    print("[정보] 시도 코드 목록 조회를 시작합니다...")
    sido_data = fetch_with_backoff(SIDO_API_URL)
    sido_list = sido_data.get("list", [])
    print(f"[정보] 총 {len(sido_list)}개의 시도 코드를 조회했습니다.")
    return sido_list


def get_stores_by_sido(sido_code, sido_name):
    """특정 시도 코드의 모든 매장 정보를 조회합니다."""
    print(f"[정보] '{sido_name}'({sido_code}) 지역 매장 정보 조회를 시작합니다...")
    payload = {
        "ins_lat": "37.56682",  # 서울 시청 기준 위도
        "ins_lng": "126.97865",  # 서울 시청 기준 경도
        "p_sido_cd": sido_code,
        "p_gugun_cd": "",
        "in_biz_cd": "",
        "set_date": "",
        "iend": "2000",  # 한 지역당 최대 2000개 매장 조회 (서울 전체도 충분히 포함 가능)
    }

    store_data = fetch_with_backoff(STORE_API_URL, data=payload)
    stores = store_data.get("list", [])
    print(f"[정보] '{sido_name}'({sido_code})에서 {len(stores)}개의 매장을 조회했습니다.")
    return stores


def process_and_save_data(raw_stores, output_suffix=""):
    """
    수집한 원천 데이터를 JSON으로 백업하고,
    유용한 데이터 필드만 가공하여 utf-8-sig 인코딩의 CSV 파일로 저장합니다.
    """
    setup_directories()

    # 파일 이름 설정 (상대경로 활용)
    json_filename = f"raw_starbucks_stores{output_suffix}.json"
    csv_filename = f"starbucks_stores{output_suffix}.csv"

    json_path = os.path.join(DATA_DIR, json_filename)
    csv_path = os.path.join(DATA_DIR, csv_filename)

    # 1. Raw JSON 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(raw_stores, f, ensure_ascii=False, indent=2)
    print(f"[성공] Raw JSON 데이터 저장 완료 -> {os.path.relpath(json_path, os.getcwd())}")

    # 2. CSV 데이터 변환 및 저장 (필요한 컬럼 추출)
    if not raw_stores:
        print("[경고] 수집된 매장 데이터가 없어 CSV 파일을 작성하지 않습니다.")
        return

    df = pd.DataFrame(raw_stores)

    # 관심 컬럼 필터링 및 이름 변경 정의
    columns_mapping = {
        "s_name": "매장명",
        "sido_name": "시도명",
        "gugun_name": "구군명",
        "sido_code": "시도코드",
        "gugun_code": "구군코드",
        "addr": "주소",
        "tel": "전화번호",
        "lat": "위도",
        "lng": "경도",
        "store_cd": "매장코드",
        "s_code": "관리코드",
        "open_dt": "오픈일자",
        "theme_state": "테마매장여부",
    }

    # 존재하는 컬럼만 선택하여 변경
    existing_cols = [col for col in columns_mapping.keys() if col in df.columns]
    df_filtered = df[existing_cols].rename(columns=columns_mapping)

    # 한국어 깨짐 방지를 위해 utf-8-sig 인코딩 사용
    df_filtered.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[성공] 가공된 CSV 데이터 저장 완료 -> {os.path.relpath(csv_path, os.getcwd())}")
    print(f"[정보] 총 {len(df_filtered)}개 매장의 정제 데이터가 저장되었습니다.")


def main():
    parser = argparse.ArgumentParser(description="스타벅스 매장 정보 수집기")
    parser.add_argument(
        "--test-seoul",
        action="store_true",
        help="서울 지역 매장 데이터만 테스트 수집합니다.",
    )
    parser.add_argument(
        "--all", action="store_true", help="전국 모든 매장 데이터를 수집합니다."
    )

    args = parser.parse_args()

    if not args.test_seoul and not args.all:
        print("[오류] --test-seoul 또는 --all 옵션 중 하나를 반드시 선택해야 합니다.")
        sys.exit(1)

    try:
        if args.test_seoul:
            print("==========================================")
            print("[시작] 1단계: 서울 지역 스타벅스 매장 정보 수집 테스트")
            print("==========================================")
            # 서울시 시도 코드는 '01'
            stores = get_stores_by_sido("01", "서울")
            process_and_save_data(stores, output_suffix="_seoul")
            print("[완료] 서울 지역 수집 테스트가 완료되었습니다.")

        elif args.all:
            print("==========================================")
            print("[시작] 2단계: 전국 스타벅스 매장 정보 전체 수집")
            print("==========================================")
            sido_list = get_sido_list()
            all_stores = []

            for sido in sido_list:
                sido_code = sido.get("sido_cd")
                sido_name = sido.get("sido_nm")

                if sido_code and sido_name:
                    try:
                        stores = get_stores_by_sido(sido_code, sido_name)
                        all_stores.extend(stores)
                    except Exception as e:
                        print(
                            f"[에러] {sido_name} 지역 수집 중 에러 발생: {e}. 다음 지역으로 계속 진행합니다."
                        )

            process_and_save_data(all_stores)
            print(f"[완료] 전국 스타벅스 매장 정보 수집이 전체 완료되었습니다. (총 {len(all_stores)}개)")

    except Exception as e:
        print(f"[실패] 프로그램 실행 중 치명적 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
