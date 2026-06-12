# -*- coding: utf-8 -*-
"""
네모앱(nemoapp.kr) 수집 데이터 유효성 검증 스크립트

이 스크립트는 수집이 완료된 매물 CSV 데이터를 읽어와 다음 항목들을 검증합니다:
1. 파일의 정상 생성 여부 및 파일 크기
2. 데이터의 행 수 (비어있지 않은지)
3. 보증금(deposit) 및 월세(monthly_rent) 컬럼의 결측치 여부
4. 실제 도메인 컬럼명(title, region, deposit, monthly_rent, details)의 존재 여부

작성자: Antigravity AI Data Pipeline Framework
작성일: 2026-06-12
"""

import os
import pandas as pd

def main():
    csv_path = "nemo_real_estate/data/nemo_real_estate_bestseller.csv"
    print(f"[Validator] 수집 완료 데이터 검증 시작: {csv_path}")
    
    # 1. 파일 존재 여부 확인
    if not os.path.exists(csv_path):
        print(f"[Validator] [Error] 파일이 존재하지 않습니다: {csv_path}")
        return False
        
    # 2. 데이터 파일 크기 확인
    file_size = os.path.getsize(csv_path)
    print(f"[Validator] 파일 크기: {file_size / 1024:.2f} KB")
    if file_size == 0:
        print("[Validator] [Error] 파일 크기가 0바이트입니다.")
        return False
        
    # 3. 데이터 로딩 및 구조 확인
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[Validator] [Error] CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
        return False
        
    print(f"[Validator] 수집된 데이터 행 수: {len(df)}개")
    if len(df) == 0:
        print("[Validator] [Error] 수집된 데이터가 비어 있습니다.")
        return False
        
    # 4. 필수 컬럼 확인 (수정된 실제 도메인 명칭 적용)
    required_cols = ["순위", "title", "region", "deposit", "monthly_rent", "details"]
    for col in required_cols:
        if col not in df.columns:
            print(f"[Validator] [Error] 필수 컬럼이 누락되었습니다: {col}")
            return False
            
    # 5. 결측치 및 비정상 데이터 검증
    null_counts = df[required_cols].isnull().sum()
    print("[Validator] 필수 컬럼별 결측치 통계:")
    for col, cnt in null_counts.items():
        print(f"  - {col}: {cnt}개 결측")
        
    # 보증금(deposit)이나 월세(monthly_rent)가 모두 0 이하인 비정상 데이터 비율 탐색
    zero_price_df = df[(df["deposit"] <= 0) & (df["monthly_rent"] <= 0)]
    if len(zero_price_df) > 0:
        print(f"[Validator] [Warning] 보증금과 월세가 모두 0 이하인 매물이 {len(zero_price_df)}개 존재합니다.")
        
    print("[Validator] [Success] 데이터 검증이 완료되었습니다. 다음 단계(EDA)로 진행이 가능합니다.")
    return True

if __name__ == "__main__":
    import sys
    success = main()
    if not success:
        sys.exit(1)

