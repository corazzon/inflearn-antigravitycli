# -*- coding: utf-8 -*-
"""
__PROJECT_NAME__ 데이터 탐색적 데이터 분석(EDA) 및 시각화 스크립트 템플릿

이 스크립트는 수집된 CSV 데이터를 로드하여 데이터 무결성을 검증하고 결측치/기술통계를 분석하며,
11가지 시각화 차트 이미지(일변량, 이변량, 다변량)를 생성하여 저장합니다.
또한 scikit-learn TF-IDF Vectorizer를 통해 상세설명 텍스트 중요 키워드를 추출합니다.

치환 대상 변수:
- PROJECT_NAME: __PROJECT_NAME__
- CSV_PATH: __CSV_PATH__
- IMAGE_DIR: __IMAGE_DIR__
- TXT_REPORT_PATH: __TXT_REPORT_PATH__
- TFIDF_CSV_PATH: __TFIDF_CSV_PATH__

작성자: Antigravity AI Data Pipeline Framework
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
import koreanize_matplotlib

def run_eda():
    csv_path = "__CSV_PATH__"
    image_dir = "__IMAGE_DIR__"
    txt_report_path = "__TXT_REPORT_PATH__"
    tfidf_csv_path = "__TFIDF_CSV_PATH__"
    
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
    missing_info = df.isnull().sum()
    print(missing_info)
    
    # 수치형 변수 통계
    print("\n=== 수치형 기술통계 ===")
    desc_num = df.describe()
    print(desc_num)
    
    # 범주형 변수 통계
    print("\n=== 범주형 기술통계 ===")
    desc_cat = df.describe(include=['object']) if df.select_dtypes(include=['object']).shape[1] > 0 else pd.DataFrame()
    print(desc_cat)
    
    # 텍스트 파일로 기초 통계정보 저장
    with open(txt_report_path, "w", encoding="utf-8") as f:
        f.write("=== 기초 데이터 정보 ===\n")
        f.write(f"전체 데이터 행 수: {df.shape[0]}\n")
        f.write(f"전체 데이터 열 수: {df.shape[1]}\n")
        f.write(f"중복 행 수: {df.duplicated().sum()}\n\n")
        f.write("=== 결측치 수 ===\n")
        f.write(missing_info.to_string())
        f.write("\n\n=== 수치형 기술통계 ===\n")
        f.write(desc_num.to_string())
        if not desc_cat.empty:
            f.write("\n\n=== 범주형 기술통계 ===\n")
            f.write(desc_cat.to_string())
        
    print(f"[EDA] 기초 통계 로그가 저장되었습니다: {txt_report_path}")
    
    # ==================== 시각화 파트 ====================
    # 1. 정가 분포 (일변량 1)
    if '정가' in df.columns:
        plt.figure(figsize=(8, 5))
        plt.hist(df['정가'], bins=20, color='skyblue', edgecolor='black', alpha=0.7)
        plt.title('도서 정가 분포 히스토그램')
        plt.xlabel('정가 (원)')
        plt.ylabel('도서 수')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/01_price_histogram.png")
        plt.close()
        
    # 2. 판매가 분포 (일변량 2)
    if '판매가' in df.columns:
        plt.figure(figsize=(8, 5))
        plt.hist(df['판매가'], bins=20, color='salmon', edgecolor='black', alpha=0.7)
        plt.title('도서 판매가 분포 히스토그램')
        plt.xlabel('판매가 (원)')
        plt.ylabel('도서 수')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/02_sale_price_histogram.png")
        plt.close()
    
    # 3. 도서 평점 분포 (일변량 3)
    if '평점' in df.columns:
        plt.figure(figsize=(8, 5))
        plt.hist(df['평점'], bins=15, color='gold', edgecolor='black', alpha=0.7)
        plt.title('도서 평점 분포')
        plt.xlabel('평점 (점)')
        plt.ylabel('도서 수')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/03_rating_distribution.png")
        plt.close()
        
    # 4. 리뷰 수 분포 (일변량 4)
    if '리뷰수' in df.columns:
        plt.figure(figsize=(8, 5))
        plt.boxplot(df['리뷰수'], vert=False, patch_artist=True, 
                    boxprops=dict(facecolor='lightgreen', color='black'),
                    medianprops=dict(color='red'))
        plt.title('도서 리뷰 수 상자그림(Boxplot)')
        plt.xlabel('리뷰 수 (건)')
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/04_review_count_boxplot.png")
        plt.close()
        
    # 5. 상위 10개 출판사 빈도 (일변량 5)
    if '출판사' in df.columns:
        pub_counts = df['출판사'].value_counts().head(10)
        plt.figure(figsize=(10, 6))
        pub_counts.plot(kind='barh', color='orchid', edgecolor='black', alpha=0.8)
        plt.title('상위 10개 출판사 도서 빈도')
        plt.xlabel('도서 수')
        plt.ylabel('출판사명')
        plt.gca().invert_yaxis()
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/05_top_publishers.png")
        plt.close()
    
    # 6. 상위 10개 저자 빈도 (일변량 6)
    if '저자' in df.columns:
        author_counts = df['저자'].value_counts().head(10)
        plt.figure(figsize=(10, 6))
        author_counts.plot(kind='barh', color='teal', edgecolor='black', alpha=0.8)
        plt.title('상위 10개 저자 도서 빈도')
        plt.xlabel('도서 수')
        plt.ylabel('저자명')
        plt.gca().invert_yaxis()
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/06_top_authors.png")
        plt.close()
        
    # 7. 정가 vs 판매가 산점도 (이변량 1)
    if '정가' in df.columns and '판매가' in df.columns:
        plt.figure(figsize=(8, 6))
        plt.scatter(df['정가'], df['판매가'], color='blue', alpha=0.5, edgecolor='none')
        max_val = max(df['정가'].max(), df['판매가'].max())
        plt.plot([0, max_val], [0, max_val], color='red', linestyle='--', label='정가=판매가 (할인 없음)')
        plt.title('정가 대비 판매가 산점도')
        plt.xlabel('정가 (원)')
        plt.ylabel('판매가 (원)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/07_price_vs_sale_price.png")
        plt.close()
        
    # 8. 평점 vs 리뷰 수 관계 (이변량 2)
    if '평점' in df.columns and '리뷰수' in df.columns:
        plt.figure(figsize=(8, 6))
        plt.scatter(df['평점'], df['리뷰수'], color='darkorange', alpha=0.6, edgecolor='black')
        plt.title('평점과 리뷰 수 상관관계 산점도')
        plt.xlabel('평점 (점)')
        plt.ylabel('리뷰 수 (건)')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(f"{image_dir}/08_rating_vs_reviews.png")
        plt.close()
        
    # 9. 상위 10개 출판사별 평균 평점 분포 (이변량 3)
    if '출판사' in df.columns and '평점' in df.columns:
        top_pubs = df['출판사'].value_counts().head(10).index
        df_top_pubs = df[df['출판사'].isin(top_pubs)]
        if not df_top_pubs.empty:
            plt.figure(figsize=(12, 6))
            sns.boxplot(x='출판사', y='평점', data=df_top_pubs, hue='출판사', legend=False, palette='Set3')
            plt.title('상위 10개 출판사별 도서 평점 분포')
            plt.xticks(rotation=45)
            plt.xlabel('출판사')
            plt.ylabel('평점 (점)')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(f"{image_dir}/09_publisher_rating_boxplot.png")
            plt.close()
            
    # 10. 상관관계 히트맵 (다변량 1)
    numeric_cols = [col for col in ['순위', '정가', '판매가', '평점', '리뷰수'] if col in df.columns]
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".3f", linewidths=.5, cbar=True)
        plt.title('수치형 변수 간 상관계수 히트맵')
        plt.tight_layout()
        plt.savefig(f"{image_dir}/10_correlation_heatmap.png")
        plt.close()
        
    # 11. 상세설명 텍스트 중요 키워드 TF-IDF 분석
    if '상세설명' in df.columns:
        descriptions = df['상세설명'].dropna().tolist()
        if descriptions:
            stop_words_korean = ['이', '그', '저', '것', '수', '등', '및', '를', '을', '에', '의', '은', '는', '도', '으로', '로', '한다', '있다', '대한', '위한', '통해', '에서', '하여', '따라', '책은', '가장', '다양한', '제시하며', '제공하며']
            
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
                plt.title('상세설명 본문 핵심 키워드 중요도 (TF-IDF 상위 15개)')
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
