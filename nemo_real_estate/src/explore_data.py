"""
네모부동산 데이터 심층 탐색 및 비판점 발굴 스크립트

이 스크립트는 기존 EDA 결과물의 문제점을 데이터 과학 관점에서 분석합니다:
1. 데이터 기본 구조 파악
2. 이상치(Outlier) 탐지
3. 샘플 불균형 확인
4. 결측값 처리 현황
5. 누락된 분석 지표 파악

작성자: 데이터 분석 비판 에이전트
작성일: 2026-06-12
"""

import pandas as pd
import numpy as np

CSV_PATH = '/Users/corazzon/work/inflearn-antigravitycli/nemo_real_estate/data/nemo_real_estate_bestseller.csv'

df = pd.read_csv(CSV_PATH)

print('=== 기본 정보 ===')
print('Shape:', df.shape)
print('\n컬럼 목록:', df.columns.tolist())

print('\n=== 데이터 타입 ===')
print(df.dtypes)

print('\n=== 결측값 ===')
missing = df.isnull().sum()
missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
missing_df = pd.DataFrame({'결측수': missing, '결측률(%)': missing_pct})
print(missing_df[missing_df['결측수'] > 0])

print('\n=== 수치형 통계 ===')
print(df.describe())

print('\n=== 범주형 통계 ===')
print(df.describe(include=['object']))

print('\n=== 중복값 ===')
print('중복 행 수:', df.duplicated().sum())

print('\n=== 상위 5행 ===')
print(df.head().to_string())

print('\n=== region 컬럼 확인 ===')
if 'region' in df.columns:
    print(df['region'].value_counts())
    print('\n비율:')
    print(df['region'].value_counts(normalize=True).round(4) * 100)
else:
    print('region 컬럼 없음')

print('\n=== deposit 이상치 분석 ===')
if 'deposit' in df.columns:
    dep = pd.to_numeric(df['deposit'], errors='coerce').dropna()
    q1, q3 = dep.quantile(0.25), dep.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
    outliers = dep[(dep < lower) | (dep > upper)]
    print(f'보증금 범위: {dep.min():.0f} ~ {dep.max():.0f} 만원')
    print(f'IQR 기준 이상치 범위: {lower:.0f} ~ {upper:.0f} 만원')
    print(f'이상치 개수: {len(outliers)} / {len(dep)} ({len(outliers)/len(dep)*100:.1f}%)')
    print(f'상위 5개 이상치:')
    print(dep.nlargest(5).to_string())

print('\n=== monthly_rent 이상치 분석 ===')
if 'monthly_rent' in df.columns:
    rent = pd.to_numeric(df['monthly_rent'], errors='coerce').dropna()
    q1, q3 = rent.quantile(0.25), rent.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
    outliers = rent[(rent < lower) | (rent > upper)]
    print(f'월세 범위: {rent.min():.0f} ~ {rent.max():.0f} 만원')
    print(f'IQR 기준 이상치 범위: {lower:.0f} ~ {upper:.0f} 만원')
    print(f'이상치 개수: {len(outliers)} / {len(rent)} ({len(outliers)/len(rent)*100:.1f}%)')
    print(f'상위 5개 이상치:')
    print(rent.nlargest(5).to_string())

print('\n=== area(면적) 컬럼 확인 ===')
area_cols = [c for c in df.columns if 'area' in c.lower() or '면적' in c or '평' in c]
print('면적 관련 컬럼:', area_cols)

print('\n=== 지역별 보증금/월세 비교 ===')
if 'region' in df.columns:
    df['deposit_n'] = pd.to_numeric(df['deposit'], errors='coerce')
    df['monthly_rent_n'] = pd.to_numeric(df['monthly_rent'], errors='coerce')
    print(df.groupby('region')[['deposit_n', 'monthly_rent_n']].agg(['mean','median','std','count']))

print('\n=== 전체 컬럼 상세 ===')
for col in df.columns:
    nunique = df[col].nunique()
    null_cnt = df[col].isnull().sum()
    dtype = df[col].dtype
    sample = df[col].dropna().head(3).tolist()
    print(f'  [{col}] dtype={dtype}, unique={nunique}, null={null_cnt}, sample={sample}')
