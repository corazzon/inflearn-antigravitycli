# -*- coding: utf-8 -*-
"""
네모앱(nemoapp.kr) 수집 데이터 탐색적 데이터 분석(EDA) 및 시각화 스크립트

이 스크립트는 수집 완료된 매물 CSV 데이터를 로드하여 다음 항목들을 수행합니다:
1. 기초 기술통계 분석 (두 지역(강남역 vs 광화문역)의 평균 보증금, 평균 월세 비교 분석 포함)
2. 11가지 분석 시각화 차트 이미지 생성 및 저장 (보증금 분포, 월세 분포, 지역별 점유율, 보증금 vs 월세 산점도 등)
3. 매물 상세 정보(details) 텍스트로부터 TF-IDF 기반 중요 키워드 추출

작성자: Antigravity AI Data Pipeline Framework
작성일: 2026-06-12
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
import koreanize_matplotlib

def run_eda():
    csv_path = "nemo_real_estate/data/nemo_real_estate_bestseller.csv"
    image_dir = "nemo_real_estate/images"
    txt_report_path = "nemo_real_estate/docs/basic_statistics.txt"
    tfidf_csv_path = "nemo_real_estate/docs/tfidf_keywords.csv"
    
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(os.path.dirname(txt_report_path), exist_ok=True)
    os.makedirs(os.path.dirname(tfidf_csv_path), exist_ok=True)
    
    print(f"[EDA] 데이터를 로드합니다: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"[Error] CSV 파일이 존재하지 않습니다: {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    
    # 2. 기초 정보 출력 및 임시 로그 저장
    print("\n=== 데이터 기본 구조 ===")
    print(f"행 수: {df.shape[0]}, 열 수: {df.shape[1]}")
    print(f"중복 행 수: {df.duplicated().sum()}")
    
    # 결측치 확인
    print("\n=== 결측치 정보 ===")
    missing_info = df[["title", "region", "deposit", "monthly_rent", "details"]].isnull().sum()
    print(missing_info)
    
    # 수치형 변수 통계 (보증금 및 월세)
    print("\n=== 수치형 기술통계 ===")
    desc_num = df[["deposit", "monthly_rent"]].describe()
    print(desc_num)
    
    # 두 지역(강남역 vs 광화문역) 그룹별 분석
    print("\n=== 지역별 평균 보증금 및 월세 ===")
    grouped = df.groupby("region")[["deposit", "monthly_rent"]].agg(["mean", "median", "count"])
    print(grouped)
    
    # 텍스트 파일로 기초 통계정보 저장
    with open(txt_report_path, "w", encoding="utf-8") as f:
        f.write("=== 기초 데이터 정보 ===\n")
        f.write(f"전체 수집 매물 수: {df.shape[0]}\n")
        f.write(f"중복 행 수: {df.duplicated().sum()}\n\n")
        f.write("=== 결측치 수 ===\n")
        f.write(missing_info.to_string())
        f.write("\n\n=== 수치형 기술통계 (단위: 만원) ===\n")
        f.write(desc_num.to_string())
        f.write("\n\n=== 지역별 기술통계 (단위: 만원) ===\n")
        f.write(grouped.to_string())
        
    print(f"[EDA] 기초 통계 로그가 저장되었습니다: {txt_report_path}")
    
    # ==================== 시각화 파트 ====================
    # 1. 보증금(deposit) 분포 (일변량 1)
    if 'deposit' in df.columns:
        plt.figure(figsize=(8, 5))
        val1_numeric = pd.to_numeric(df['deposit'], errors='coerce').dropna()
        if not val1_numeric.empty:
            plt.hist(val1_numeric, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
            plt.title('보증금 분포 히스토그램 (단위: 만원)')
            plt.xlabel('보증금 (만원)')
            plt.ylabel('매물 수')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(f"{image_dir}/01_price_histogram.png")
            plt.close()
        
    # 2. 월세(monthly_rent) 분포 (일변량 2)
    if 'monthly_rent' in df.columns:
        plt.figure(figsize=(8, 5))
        val2_numeric = pd.to_numeric(df['monthly_rent'], errors='coerce').dropna()
        if not val2_numeric.empty:
            plt.hist(val2_numeric, bins=20, color='salmon', edgecolor='black', alpha=0.7)
            plt.title('월세 분포 히스토그램 (단위: 만원)')
            plt.xlabel('월세 (만원)')
            plt.ylabel('매물 수')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(f"{image_dir}/02_sale_price_histogram.png")
            plt.close()
    
    # 3. 월세 상세 분포 (일변량 3)
    if 'monthly_rent' in df.columns:
        plt.figure(figsize=(8, 5))
        val2_numeric = pd.to_numeric(df['monthly_rent'], errors='coerce').dropna()
        if not val2_numeric.empty:
            plt.hist(val2_numeric, bins=15, color='gold', edgecolor='black', alpha=0.7)
            plt.title('월세 상세 분포 (단위: 만원)')
            plt.xlabel('월세 (만원)')
            plt.ylabel('매물 수')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(f"{image_dir}/03_rating_distribution.png")
            plt.close()
        
    # 4. 월세 상자그림 (일변량 4)
    if 'monthly_rent' in df.columns:
        val2_numeric = pd.to_numeric(df['monthly_rent'], errors='coerce').dropna()
        if not val2_numeric.empty:
            plt.figure(figsize=(8, 5))
            plt.boxplot(val2_numeric, vert=False, patch_artist=True, 
                        boxprops=dict(facecolor='lightgreen', color='black'),
                        medianprops=dict(color='red'))
            plt.title('월세 상자그림(Boxplot)')
            plt.xlabel('월세 (만원)')
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(f"{image_dir}/04_review_count_boxplot.png")
            plt.close()
        
    # 5. 수집 지역별 매물 수 (일변량 5)
    if 'region' in df.columns:
        cat_counts = df['region'].value_counts()
        plt.figure(figsize=(8, 5))
        cat_counts.plot(kind='bar', color=['orchid', 'teal'], edgecolor='black', alpha=0.8)
        plt.title('지역별 수집 매물 수')
        plt.xlabel('지역구분')
        plt.ylabel('매물 수')
        plt.xticks(rotation=0)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/05_top_publishers.png")
        plt.close()
    
    # 6. 매물 제목 고유 이름 빈도 (일변량 6)
    if 'title' in df.columns:
        name_counts = df['title'].value_counts().head(10)
        plt.figure(figsize=(10, 6))
        name_counts.plot(kind='barh', color='teal', edgecolor='black', alpha=0.8)
        plt.title('상위 10개 매물 명칭 빈도')
        plt.xlabel('출현 수')
        plt.ylabel('매물 명칭')
        plt.gca().invert_yaxis()
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/06_top_authors.png")
        plt.close()
        
    # 7. 보증금 vs 월세 산점도 (이변량 1)
    if 'deposit' in df.columns and 'monthly_rent' in df.columns:
        v1 = pd.to_numeric(df['deposit'], errors='coerce')
        v2 = pd.to_numeric(df['monthly_rent'], errors='coerce')
        valid_idx = v1.notnull() & v2.notnull()
        if valid_idx.any():
            plt.figure(figsize=(8, 6))
            sns.scatterplot(x=v1[valid_idx], y=v2[valid_idx], hue=df.loc[valid_idx, 'region'], palette='Set1', alpha=0.7)
            plt.title('보증금 대비 월세 상관 산점도')
            plt.xlabel('보증금 (만원)')
            plt.ylabel('월세 (만원)')
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            plt.savefig(f"{image_dir}/07_price_vs_sale_price.png")
            plt.close()
        
    # 8. 인덱스 대비 월세 산포도 (이변량 2)
    if 'monthly_rent' in df.columns:
        v2 = pd.to_numeric(df['monthly_rent'], errors='coerce').dropna()
        if not v2.empty:
            plt.figure(figsize=(8, 6))
            plt.scatter(df.index, df['monthly_rent'], color='darkorange', alpha=0.6, edgecolor='black')
            plt.title('매물 수집 순서 대비 월세 산포도')
            plt.xlabel('수집 인덱스')
            plt.ylabel('월세 (만원)')
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            plt.savefig(f"{image_dir}/08_rating_vs_reviews.png")
            plt.close()
        
    # 9. 지역별 월세 분포 boxplot (이변량 3)
    if 'region' in df.columns and 'monthly_rent' in df.columns:
        df_clean = df.copy()
        df_clean['monthly_rent'] = pd.to_numeric(df_clean['monthly_rent'], errors='coerce')
        df_clean = df_clean.dropna(subset=['monthly_rent'])
        if not df_clean.empty:
            plt.figure(figsize=(10, 6))
            sns.boxplot(x='region', y='monthly_rent', data=df_clean, hue='region', legend=False, palette='Set2')
            plt.title('지역별 월세 수치 분포 비교')
            plt.xlabel('지역구분')
            plt.ylabel('월세 (만원)')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(f"{image_dir}/09_publisher_rating_boxplot.png")
            plt.close()
            
    # 10. 상관관계 히트맵 (다변량 1)
    numeric_cols = []
    for col in ['순위', 'deposit', 'monthly_rent']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            numeric_cols.append(col)
    
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".3f", linewidths=.5, cbar=True)
        plt.title('수치형 변수 간 상관계수 히트맵')
        plt.tight_layout()
        plt.savefig(f"{image_dir}/10_correlation_heatmap.png")
        plt.close()
        
    # 11. details 텍스트 중요 키워드 TF-IDF 분석
    if 'details' in df.columns:
        descriptions = df['details'].dropna().tolist()
        if descriptions:
            stop_words_korean = [
                '이', '그', '저', '것', '수', '등', '및', '를', '을', '에', '의', '은', '는', '도', '으로', '로',
                '한다', '있다', '대한', '위한', '통해', '에서', '하여', '따라', '만원', '도보', '층', '면적', '권리금',
                '관리비', '업종', '교통', '있습니다', '상가', '사무실', '매물', '추천', '강추', '가능', '인근', '보증금',
                '월세', '구분', '완료', '위치', '인테리어', '최상', '최고', '안내', '문의', '연락', '상담', '환영', '시설'
            ]
            
            try:
                vectorizer = TfidfVectorizer(max_features=30, stop_words=stop_words_korean, min_df=1)
                tfidf_matrix = vectorizer.fit_transform(descriptions)
                mean_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).ravel()
                features = vectorizer.get_feature_names_out()
                
                tfidf_df = pd.DataFrame({'keyword': features, 'tfidf_weight': mean_tfidf})
                tfidf_df = tfidf_df.sort_values(by='tfidf_weight', ascending=False)
                tfidf_df.to_csv(tfidf_csv_path, index=False, encoding="utf-8-sig")
                
                plt.figure(figsize=(10, 8))
                plt.barh(tfidf_df['keyword'].head(15), tfidf_df['tfidf_weight'].head(15), color='darkgrey', edgecolor='black', alpha=0.8)
                plt.title('매물 상세 설명 핵심 키워드 중요도 (TF-IDF 상위 15개)')
                plt.xlabel('평균 TF-IDF 가중치')
                plt.ylabel('핵심 키워드')
                plt.gca().invert_yaxis()
                plt.grid(axis='x', linestyle='--', alpha=0.7)
                plt.tight_layout()
                plt.savefig(f"{image_dir}/11_tfidf_keywords_bar.png")
                plt.close()
            except Exception as e:
                print(f"[Warning] TF-IDF 키워드 분석 중 오류 발생: {e}")
                
    print("[EDA] 모든 시각화 분석 및 시각화 이미지 생성이 완료되었습니다.")

if __name__ == "__main__":
    run_eda()


