# -*- coding: utf-8 -*-
"""
이 스크립트는 iHerb 데이터베이스 통계 및 TF-IDF 테이블을 텍스트로 생성하여 리포트에 삽입할 수 있도록 요약 결과를 터미널에 출력하는 역할을 합니다.
"""
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def print_stats():
    conn = sqlite3.connect("iherb/data/iherb_vitamind.sqlite")
    df_prod = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    
    print("--- Products Describe (Numeric) ---")
    print(df_prod[['price', 'rating', 'review_count']].describe().to_markdown())
    
    print("\n--- Products Describe (Categorical) ---")
    print(df_prod[['brand', 'product_id']].describe(include=['object']).to_markdown())
    
    print("\n--- Top 10 Brands by Product Count ---")
    print(df_prod['brand'].value_counts().head(10).reset_index().to_markdown(index=False))
    
    print("\n--- Top 10 Brands by Average Price ---")
    print(df_prod.groupby('brand')['price'].mean().reset_index().sort_values(by='price', ascending=False).head(10).to_markdown(index=False))
    
    # TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english', max_features=30)
    tfidf_matrix = vectorizer.fit_transform(df_prod['title'].dropna())
    feature_names = vectorizer.get_feature_names_out()
    tfidf_sums = tfidf_matrix.sum(axis=0).A1
    df_tfidf = pd.DataFrame({'keyword': feature_names, 'weight': tfidf_sums})
    df_tfidf = df_tfidf.sort_values(by='weight', ascending=False)
    
    print("\n--- Top 30 TF-IDF Keywords ---")
    print(df_tfidf.to_markdown(index=False))

if __name__ == "__main__":
    print_stats()
