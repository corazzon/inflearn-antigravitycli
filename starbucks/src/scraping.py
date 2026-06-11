# -*- coding: utf-8 -*-
"""
스타벅스 매장 정보를 수집하는 스크래퍼 스크립트입니다.
데이터 파이프라인 프레임워크 규격에 맞추어 매장 데이터를 범용 5대 속성 구조로 정제하여 저장합니다.
"""

import os
import sys
import json
import time
import random
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


def fetch_with_backoff(url, data=None, max_retries=5, backoff_factor=1.5):
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

            response = requests.post(url, data=data, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return response.json()

        except (requests.exceptions.RequestException, ValueError) as e:
            retries += 1
            print(f"[경고] API 호출 실패 ({url}). 재시도 {retries}/{max_retries}. 오류: {e}")
            if retries >= max_retries:
                print(f"[에러] 최대 재시도 횟수를 초과했습니다. ({url})")
                raise

            # 지수 백오프 적용 (재시도할 때마다 대기 시간 증가)
            backoff_delay = (
                backoff_factor**retries + random.uniform(0.1, 0.5)
            )
            print(f"[알림] {backoff_delay:.2f}초 후 재시도합니다.")
            time.sleep(backoff_delay)


def get_sido_list():
    """시도 목록을 조회하여 반환합니다."""
    print("[Scraper] 시도 코드 목록 조회를 시작합니다...")
    sido_data = fetch_with_backoff(SIDO_API_URL)
    sido_list = sido_data.get("list", [])
    print(f"[Scraper] 총 {len(sido_list)}개의 시도 코드를 조회했습니다.")
    return sido_list


def get_stores_by_sido(sido_code, sido_name):
    """특정 시도 코드의 모든 매장 정보를 조회합니다."""
    print(
        f"[Scraper] '{sido_name}'({sido_code}) 지역 매장 정보 조회를 시작합니다..."
    )
    payload = {
        "ins_lat": "37.56682",
        "ins_lng": "126.97865",
        "p_sido_cd": sido_code,
        "p_gugun_cd": "",
        "in_biz_cd": "",
        "set_date": "",
        "iend": "2000",
    }

    store_data = fetch_with_backoff(STORE_API_URL, data=payload)
    stores = store_data.get("list", [])
    print(
        f"[Scraper] '{sido_name}'({sido_code})에서 {len(stores)}개의 매장을 조회했습니다."
    )
    return stores


def main_scraper():
    print("[Scraper] 스타벅스 매장 정보 수집 루프를 기동합니다...")
    setup_directories()

    try:
        sido_list = get_sido_list()
        all_raw_stores = []

        # 전국 매장 정보 수집
        for sido in sido_list:
            sido_code = sido.get("sido_cd")
            sido_name = sido.get("sido_nm")

            if sido_code and sido_name:
                try:
                    stores = get_stores_by_sido(sido_code, sido_name)
                    all_raw_stores.extend(stores)
                except Exception as e:
                    print(
                        f"[Error] {sido_name} 지역 수집 중 에러 발생: {e}. 다음 지역으로 진행합니다."
                    )

        if not all_raw_stores:
            print("[Error] 수집된 데이터가 없습니다.")
            sys.exit(1)

        # 수집 원본 JSON 백업 저장
        raw_json_path = os.path.join(DATA_DIR, "raw_starbucks_stores.json")
        with open(raw_json_path, "w", encoding="utf-8") as f:
            json.dump(all_raw_stores, f, ensure_ascii=False, indent=2)
        print(f"[Success] Raw JSON 백업 성공: {raw_json_path}")

        # 프레임워크 5대 범용 속성으로 변환 및 저장
        collected_data = []
        for index, item in enumerate(all_raw_stores, 1):
            name = item.get("s_name", "").strip()
            category = item.get("sido_name", "").strip()
            try:
                value_1 = float(item.get("lat", 0.0))
            except (ValueError, TypeError):
                value_1 = 0.0
            try:
                # 스타벅스 API는 경도(longitude)의 키로 'lot'을 사용함
                value_2 = float(item.get("lot", 0.0))
            except (ValueError, TypeError):
                value_2 = 0.0
            addr = item.get("addr", "").strip()
            tel = item.get("tel", "").strip()
            detail_text = f"주소: {addr} | 전화번호: {tel}"

            collected_data.append(
                {
                    "순위": index,
                    "name": name,
                    "category": category,
                    "value_1": value_1,
                    "value_2": value_2,
                    "detail_text": detail_text,
                }
            )

        df = pd.DataFrame(collected_data)

        # utf-8-sig 인코딩 적용하여 저장
        output_csv_path = os.path.join(DATA_DIR, "starbucks_bestseller.csv")
        df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")
        print(
            f"[Success] 총 {len(df)}건 데이터가 {output_csv_path}에 성공적으로 적재 완료되었습니다."
        )

    except Exception as e:
        print(f"[Error] 스크래퍼 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_scraper()
