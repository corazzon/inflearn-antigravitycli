# -*- coding: utf-8 -*-
"""
이 스크립트는 iHerb 비타민 D 데이터베이스의 데이터를 활용하여 상세한 EDA를 수행하고 시각화 이미지를 저장하는 파이썬 코드입니다.
"""
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
import os

# Seaborn 스타일 설정 사용 안 함 (지침 준수)

def run_eda():
    os.makedirs("iherb/images", exist_ok=True)
    os.makedirs("iherb/reports", exist_ok=True)
    
    conn = sqlite3.connect("iherb/data/iherb_vitamind.sqlite")
    
    # 데이터 로드
    df_prod = pd.read_sql_query("SELECT * FROM products", conn)
    df_detail = pd.read_sql_query("SELECT * FROM product_details", conn)
    
    conn.close()
    
    # ------------------ 데이터 파악 기본 정보 출력 ------------------
    print("--- Products Info ---")
    print(df_prod.info())
    print("\n--- Details Info ---")
    print(df_detail.info())
    
    print("\nProducts Shape:", df_prod.shape)
    print("Details Shape:", df_detail.shape)
    
    print("\nProducts Duplicates:", df_prod.duplicated().sum())
    print("Details Duplicates:", df_detail.duplicated().sum())
    
    # ------------------ 시각화 생성 (총 10개 이상) ------------------
    
    # 1. 일변량 - 가격 분포 (히스토그램 & KDE)
    plt.figure(figsize=(10, 6))
    plt.hist(df_prod['price'].dropna(), bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    plt.title('비타민 D 제품 가격 분포')
    plt.xlabel('가격 (원)')
    plt.ylabel('제품 수')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('iherb/images/01_price_distribution.png')
    plt.close()
    
    # 2. 일변량 - 평점 분포 (히스토그램)
    plt.figure(figsize=(10, 6))
    plt.hist(df_prod['rating'].dropna(), bins=15, color='orange', edgecolor='black', alpha=0.7)
    plt.title('비타민 D 제품 평점 분포')
    plt.xlabel('평점')
    plt.ylabel('제품 수')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('iherb/images/02_rating_distribution.png')
    plt.close()
    
    # 3. 일변량 - 리뷰 수 분포 (박스 플롯)
    plt.figure(figsize=(10, 4))
    plt.boxplot(df_prod['review_count'].dropna(), vert=False, patch_artist=True, 
                boxprops=dict(facecolor='lightgreen', color='green'))
    plt.title('비타민 D 제품 리뷰 수 분포 (Boxplot)')
    plt.xlabel('리뷰 수')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('iherb/images/03_review_count_boxplot.png')
    plt.close()

    # 4. 이변량 - 상위 20개 브랜드별 평균 가격 (Bar chart)
    top_brands = df_prod['brand'].value_counts().head(20).index
    df_top_brands = df_prod[df_prod['brand'].isin(top_brands)]
    brand_price = df_top_brands.groupby('brand')['price'].mean().sort_values(ascending=False)
    
    plt.figure(figsize=(12, 6))
    brand_price.plot(kind='bar', color='coral', edgecolor='black', alpha=0.8)
    plt.title('상위 20개 브랜드별 제품 평균 가격')
    plt.xlabel('브랜드')
    plt.ylabel('평균 가격 (원)')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('iherb/images/04_brand_avg_price.png')
    plt.close()
    
    # 5. 이변량 - 상위 20개 브랜드별 제품 수 (Bar chart)
    brand_counts = df_prod['brand'].value_counts().head(20)
    plt.figure(figsize=(12, 6))
    brand_counts.plot(kind='bar', color='plum', edgecolor='black', alpha=0.8)
    plt.title('상위 20개 브랜드별 등록 제품 수')
    plt.xlabel('브랜드')
    plt.ylabel('제품 수')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('iherb/images/05_brand_product_count.png')
    plt.close()
    
    # 6. 이변량 - 가격 vs 평점 상관관계 (산점도)
    plt.figure(figsize=(10, 6))
    plt.scatter(df_prod['price'], df_prod['rating'], alpha=0.5, color='teal')
    plt.title('제품 가격과 평점의 상관관계')
    plt.xlabel('가격 (원)')
    plt.ylabel('평점')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('iherb/images/06_price_vs_rating.png')
    plt.close()
    
    # 7. 이변량 - 가격 vs 리뷰 수 상관관계 (산점도)
    plt.figure(figsize=(10, 6))
    plt.scatter(df_prod['price'], df_prod['review_count'], alpha=0.5, color='darkred')
    plt.title('제품 가격과 리뷰 수의 상관관계')
    plt.xlabel('가격 (원)')
    plt.ylabel('리뷰 수')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('iherb/images/07_price_vs_reviews.png')
    plt.close()
    
    # 8. 이변량 - 평점 vs 리뷰 수 상관관계 (산점도)
    plt.figure(figsize=(10, 6))
    plt.scatter(df_prod['rating'], df_prod['review_count'], alpha=0.5, color='darkblue')
    plt.title('제품 평점과 리뷰 수의 상관관계')
    plt.xlabel('평점')
    plt.ylabel('리뷰 수')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('iherb/images/08_rating_vs_reviews.png')
    plt.close()
    
    # 9. 다변량 - 수치형 변수 간 상관관계 히트맵
    plt.figure(figsize=(8, 6))
    corr = df_prod[['price', 'rating', 'review_count', 'page_no']].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    plt.title('수치형 변수 간 상관계수 히트맵')
    plt.tight_layout()
    plt.savefig('iherb/images/09_correlation_heatmap.png')
    plt.close()

    # 10. 다변량 - 평점 구간별 가격과 리뷰 수 (버블 차트)
    # 평점을 0.5 간격으로 구간화
    df_prod['rating_group'] = pd.cut(df_prod['rating'], bins=[0, 3.5, 4.0, 4.5, 4.8, 5.0], 
                                     labels=['3.5 이하', '3.5-4.0', '4.0-4.5', '4.5-4.8', '4.8-5.0'])
    rating_group_stats = df_prod.groupby('rating_group', observed=False).agg({
        'price': 'mean',
        'review_count': 'mean',
        'id': 'count'
    }).rename(columns={'id': 'count'}).dropna()
    
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(rating_group_stats['price'], rating_group_stats['review_count'], 
                          s=rating_group_stats['count']*20, alpha=0.6, c=range(len(rating_group_stats)), cmap='viridis')
    plt.title('평점 그룹별 평균 가격 vs 평균 리뷰 수 (원 크기는 제품 수)')
    plt.xlabel('평균 가격 (원)')
    plt.ylabel('평균 리뷰 수')
    for i, txt in enumerate(rating_group_stats.index):
        plt.annotate(txt, (rating_group_stats['price'].iloc[i], rating_group_stats['review_count'].iloc[i]),
                     textcoords="offset points", xytext=(0,10), ha='center', fontsize=10, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('iherb/images/10_multivariate_bubble.png')
    plt.close()

    # 11. 텍스트 분석 - 제품 타이틀 TF-IDF 중요 키워드 상위 30개
    vectorizer = TfidfVectorizer(stop_words='english', max_features=30)
    tfidf_matrix = vectorizer.fit_transform(df_prod['title'].dropna())
    feature_names = vectorizer.get_feature_names_out()
    tfidf_sums = tfidf_matrix.sum(axis=0).A1
    
    df_tfidf = pd.DataFrame({'keyword': feature_names, 'weight': tfidf_sums})
    df_tfidf = df_tfidf.sort_values(by='weight', ascending=False)
    
    plt.figure(figsize=(12, 8))
    plt.barh(df_tfidf['keyword'].head(30)[::-1], df_tfidf['weight'].head(30)[::-1], color='mediumpurple', edgecolor='black', alpha=0.8)
    plt.title('제품 타이틀 핵심 키워드 상위 30개 (TF-IDF)')
    plt.xlabel('TF-IDF 가중치 합')
    plt.ylabel('키워드')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('iherb/images/11_title_tfidf_top30.png')
    plt.close()

    print("EDA Visualizations generated and saved to iherb/images/")
    return df_prod, df_detail, df_tfidf

if __name__ == "__main__":
    run_eda()
