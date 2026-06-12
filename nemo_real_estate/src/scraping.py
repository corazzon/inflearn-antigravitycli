# -*- coding: utf-8 -*-
"""
네모앱(nemoapp.kr) 상업용 부동산 매물 수집 스크래퍼

이 스크립트는 광화문역과 강남역의 Bounding Box 영역을 설정하고,
네모앱의 'search-list' 백엔드 API를 직접 호출하여 매물 데이터를 수집합니다.
기존 5대 필수 속성을 실제 HTML/자바스크립트 비즈니스 도메인 명칭(title, region, deposit, monthly_rent, details)
으로 교정하고, 동시에 API가 제공하는 모든 원천 원데이터 컬럼을 누락 없이 통째로 CSV 파일에 적재합니다.

작성자: Antigravity AI Data Pipeline Framework
작성일: 2026-06-12
"""

import os
import time
import random
import pandas as pd
import requests

def request_with_retry(url, params, headers, max_retries=5, backoff_factor=1.5):
    """지수 백오프 재시도 메커니즘을 적용한 HTTP GET 요청 수행 함수"""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            # 정상 응답 시 바로 반환
            if response.status_code == 200:
                return response
            
            # 재시도할 상태 코드 감지 (429, 500, 502, 503, 504 등)
            if response.status_code in [429, 500, 502, 503, 504]:
                sleep_time = (backoff_factor ** attempt) + random.uniform(0.5, 1.5)
                print(f"[Warning] HTTP {response.status_code} 발생. {attempt}/{max_retries}회 재시도. {sleep_time:.2f}초 후 재개...")
                time.sleep(sleep_time)
            else:
                print(f"[Error] 치명적 HTTP {response.status_code} 에러 발생. 재시도를 생략합니다.")
                return response
                
        except requests.exceptions.RequestException as e:
            sleep_time = (backoff_factor ** attempt) + random.uniform(0.5, 1.5)
            print(f"[Warning] 네트워크 통신 오류 ({e}). {attempt}/{max_retries}회 재시도. {sleep_time:.2f}초 후 재개...")
            time.sleep(sleep_time)
            
    return None

def scrape_region(station_name, bbox, base_url, headers, max_pages=20):
    """특정 지하철역 근처의 매물을 수집하는 함수"""
    print(f"\n[Scraper] {station_name} 영역 매물 수집 시작...")
    
    params = {
        "CompletedOnly": "false",
        "NELat": str(bbox["NELat"]),
        "NELng": str(bbox["NELng"]),
        "SWLat": str(bbox["SWLat"]),
        "SWLng": str(bbox["SWLng"]),
        "Zoom": "16",
        "SortBy": "29",
        "PageIndex": "0"
    }
    
    region_data = []
    
    for page in range(0, max_pages):
        params["PageIndex"] = str(page)
        print(f"[Scraper] {station_name} | {page + 1}페이지 수집 시도 중...")
        
        response = request_with_retry(base_url, params, headers)
        
        if not response or response.status_code != 200:
            print(f"[Error] {station_name} {page + 1}페이지 수집 실패로 수집을 중단합니다.")
            break
            
        json_data = response.json()
        items = json_data.get("items", [])
        
        if not items:
            print(f"[Info] {station_name} {page + 1}페이지에 더 이상 매물이 없습니다.")
            break
            
        for item in items:
            # 원천 API 데이터를 통째로 복사
            item_copy = item.copy()
            
            # 대시보드 바인딩을 위한 핵심 도메인 필드 명시적 추가
            title = item.get("title")
            if not title:
                title = f"{station_name} 상업용 매물"
            else:
                title = title.strip()
                
            deposit = item.get("deposit", 0)
            monthly_rent = item.get("monthlyRent", 0)
            premium = item.get("premium", 0)
            maintenance_fee = item.get("maintenanceFee", 0)
            floor = item.get("floor", "-")
            ground_floor = item.get("groundFloor", "-")
            size = item.get("size", 0.0)
            large_cat = item.get("businessLargeCodeName", "기타")
            mid_cat = item.get("businessMiddleCodeName", "기타")
            near_station = item.get("nearSubwayStation", "")
            
            # 상세 속성 텍스트 구성
            detail_parts = []
            if size:
                detail_parts.append(f"면적: {size:.2f}㎡")
            if premium:
                detail_parts.append(f"권리금: {premium:,}만원")
            if maintenance_fee:
                detail_parts.append(f"관리비: {maintenance_fee:,}만원")
            if floor != "-" or ground_floor != "-":
                detail_parts.append(f"층수: {floor}층/{ground_floor}층")
            if large_cat or mid_cat:
                detail_parts.append(f"업종: {large_cat}>{mid_cat}")
            if near_station:
                detail_parts.append(f"교통: {near_station}")
                
            details = " | ".join(detail_parts)
            
            # 명시적 컬럼 주입
            item_copy["title"] = title
            item_copy["region"] = station_name
            item_copy["deposit"] = deposit
            item_copy["monthly_rent"] = monthly_rent
            item_copy["details"] = details
            
            region_data.append(item_copy)
            
        # 서버 부하 방지를 위한 딜레이 적용
        time.sleep(random.uniform(0.3, 0.8))
        
    print(f"[Success] {station_name}에서 총 {len(region_data)}개의 매물을 수집하였습니다.")
    return region_data

def main_scraper():
    base_url = "https://www.nemoapp.kr/api/store/search-list"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.nemoapp.kr/store"
    }
    
    regions = {
        "강남역": {
            "SWLat": 37.490000, "SWLng": 127.020000,
            "NELat": 37.505000, "NELng": 127.035000
        },
        "광화문역": {
            "SWLat": 37.564000, "SWLng": 126.966000,
            "NELat": 37.579000, "NELng": 126.987000
        }
    }
    
    all_data = []
    
    for station, bbox in regions.items():
        station_data = scrape_region(station, bbox, base_url, headers, max_pages=20)
        all_data.extend(station_data)
        time.sleep(1.0)
        
    if not all_data:
        print("[Error] 수집된 데이터가 없습니다.")
        return
        
    df = pd.DataFrame(all_data)
    
    # 순위 컬럼을 맨 앞으로 삽입
    df.insert(0, "순위", range(1, len(df) + 1))
    
    output_path = "nemo_real_estate/data/nemo_real_estate_bestseller.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n[Success] 총 {len(df)}건의 매물 데이터(API 원천 전체 필드 포함)가 {output_path}에 최종 적재되었습니다.")

if __name__ == "__main__":
    main_scraper()


