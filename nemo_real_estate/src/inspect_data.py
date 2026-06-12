# -*- coding: utf-8 -*-
"""
부동산 매물 데이터 기초 통계 및 층수/교통 입지별 집계 스크립트

이 스크립트는 nemo_real_estate/data/nemo_real_estate_bestseller.csv 데이터를 로드하여
층수별, 교통 입지(지하철역 도보 거리)별 통계적 분포를 분석하고 출력합니다.
분석 결과는 보고서 작성 시 정량적인 해석 텍스트와 표를 구성하는 기초 자료로 활용됩니다.

작성자: Docx Reporter
작성일: 2026-06-12
"""

import os
import pandas as pd
import re

def inspect_real_estate_data():
    csv_path = "nemo_real_estate/data/nemo_real_estate_bestseller.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} 파일이 존재하지 않습니다.")
        return
        
    df = pd.read_csv(csv_path)
    df['deposit'] = pd.to_numeric(df['deposit'], errors='coerce').fillna(0)
    df['monthly_rent'] = pd.to_numeric(df['monthly_rent'], errors='coerce').fillna(0)
    
    print("=== [1] 전체 요약 ===")
    print(f"전체 매물 수: {len(df)}")
    print(f"평균 보증금: {df['deposit'].mean():.2f}만원, 중간 보증금: {df['deposit'].median():.2f}만원")
    print(f"평균 월세: {df['monthly_rent'].mean():.2f}만원, 중간 월세: {df['monthly_rent'].median():.2f}만원")
    
    print("\n=== [2] 지역별 요약 ===")
    for region, group in df.groupby('region'):
        print(f"지역: {region} ({len(group)}건)")
        print(f"  평균 보증금: {group['deposit'].mean():.2f}만원, 중간 보증금: {group['deposit'].median():.2f}만원")
        print(f"  평균 월세: {group['monthly_rent'].mean():.2f}만원, 중간 월세: {group['monthly_rent'].median():.2f}만원")
        
    # 층수(floor) 변환 및 그룹화
    # floor 컬럼: 1, 2, 3, -1 등
    # 지하는 음수이거나 지하로 매핑
    def categorize_floor(f):
        try:
            val = float(f)
            if val < 0:
                return "지하층"
            elif val == 1:
                return "1층"
            elif val == 2:
                return "2층"
            elif 3 <= val <= 5:
                return "3~5층"
            else:
                return "6층 이상"
        except:
            return "기타/미분류"
            
    df['floor_cat'] = df['floor'].apply(categorize_floor)
    
    print("\n=== [3] 층수별 요약 ===")
    floor_stats = df.groupby('floor_cat')[['deposit', 'monthly_rent']].agg(['mean', 'median', 'count'])
    print(floor_stats)
    
    # 교통 입지(nearSubwayStation) 분석
    # 도보 분수 추출
    # 예: "강남역, 도보 4분" -> 4
    def extract_walk_minutes(station_str):
        if pd.isna(station_str):
            return None
        match = re.search(r'도보\s*(\d+)분', str(station_str))
        if match:
            return int(match.group(1))
        return None
        
    df['walk_min'] = df['nearSubwayStation'].apply(extract_walk_minutes)
    
    def categorize_transit(row):
        walk = row['walk_min']
        if pd.isna(walk):
            return "정보 없음"
        elif walk <= 5:
            return "초역세권 (도보 5분 이내)"
        else:
            return "일반역세권 (도보 5분 초과)"
            
    df['transit_cat'] = df.apply(categorize_transit, axis=1)
    
    print("\n=== [4] 교통 입지별 요약 ===")
    transit_stats = df.groupby('transit_cat')[['deposit', 'monthly_rent']].agg(['mean', 'median', 'count'])
    print(transit_stats)

if __name__ == "__main__":
    inspect_real_estate_data()
