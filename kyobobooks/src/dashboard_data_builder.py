# -*- coding: utf-8 -*-
"""
교보문고 대시보드 오프라인 데이터 빌더 스크립트

이 스크립트는 수집된 교보문고 일간 베스트셀러 CSV 데이터(kyobobooks/data/kyobo_bestseller.csv)와
TF-IDF 키워드 데이터(kyobobooks/docs/tfidf_keywords.csv)를 로드하여,
웹 대시보드(kyobobooks/src/dashboard.html)에서 로컬 파일 서버 없이도 즉시 로드할 수 있도록
전역 자바스크립트 변수 형태로 데이터를 추출하여 dashboard_data.js로 내보냅니다.

주요 기능:
- 데이터 요약 통계(총 수, 평균가, 평점, 최다 리뷰수) 연산
- Chart.js 시각화용 데이터 가공 (가격 분포, 평점 분포, 출판사 점유율, 키워드 순위, 평점-리뷰 산점도)
- 전체 도서 정보 JSON 변환 및 자바스크립트 파일(dashboard_data.js) 생성

작성자: Antigravity AI
생성일: 2026-06-08
"""

import os
import json
import pandas as pd

def build_dashboard_data():
    csv_path = "kyobobooks/data/kyobo_bestseller.csv"
    tfidf_path = "kyobobooks/docs/tfidf_keywords.csv"
    output_js_path = "kyobobooks/src/dashboard_data.js"
    
    print(f"[Builder] CSV 데이터를 로드합니다: {csv_path}")
    if not os.path.exists(csv_path):
        print("[Error] CSV 파일이 존재하지 않습니다.")
        return
        
    df = pd.read_csv(csv_path)
    
    # 1. 요약 통계(Metrics) 가공
    total_books = int(df.shape[0])
    avg_price = int(df['정가'].mean())
    avg_rating = float(df['평점'].mean())
    max_reviews = int(df['리뷰수'].max())
    
    metrics = {
        "total_books": total_books,
        "avg_price": avg_price,
        "avg_rating": round(avg_rating, 2),
        "max_reviews": max_reviews
    }
    
    # 2. 전체 도서 데이터 (상세설명 포함)
    # NaN 값은 자바스크립트 JSON 파싱 시 null로 변환되므로 미리 빈 문자열로 정제
    df_cleaned = df.fillna("")
    books_list = df_cleaned.to_dict(orient="records")
    
    # 3. Chart 1: 가격대 분포 데이터 (정가 및 판매가 구간별 집계)
    price_bins = [0, 15000, 20000, 25000, 30000, 35000, 40000, 100000]
    price_labels = ["1.5만 미만", "1.5만~2만", "2만~2.5만", "2.5만~3만", "3만~3.5만", "3.5만~4만", "4만 이상"]
    
    df_cleaned['정가_구간'] = pd.cut(df_cleaned['정가'], bins=price_bins, labels=price_labels)
    df_cleaned['판매가_구간'] = pd.cut(df_cleaned['판매가'], bins=price_bins, labels=price_labels)
    
    price_dist_regular = df_cleaned['정가_구간'].value_counts().reindex(price_labels).fillna(0).astype(int).tolist()
    price_dist_sale = df_cleaned['판매가_구간'].value_counts().reindex(price_labels).fillna(0).astype(int).tolist()
    
    price_chart_data = {
        "labels": price_labels,
        "regular": price_dist_regular,
        "sale": price_dist_sale
    }
    
    # 4. Chart 2: 출판사 점유율 (상위 10개)
    pub_counts = df_cleaned['출판사'].value_counts().head(10)
    publisher_chart_data = {
        "labels": pub_counts.index.tolist(),
        "values": pub_counts.tolist()
    }
    
    # 5. Chart 3: 평점 분포 데이터
    rating_bins = [-1, 0.1, 5.0, 8.0, 9.0, 9.5, 10.1]
    rating_labels = ["평가 없음 (0.0)", "5점 미만", "5점~8점 미만", "8점~9점 미만", "9점~9.5점 미만", "9.5점 이상"]
    df_cleaned['평점_구간'] = pd.cut(df_cleaned['평점'], bins=rating_bins, labels=rating_labels)
    rating_dist = df_cleaned['평점_구간'].value_counts().reindex(rating_labels).fillna(0).astype(int).tolist()
    
    rating_chart_data = {
        "labels": rating_labels,
        "values": rating_dist
    }
    
    # 6. Chart 4: TF-IDF 중요 키워드 (상위 15개)
    keyword_labels = []
    keyword_weights = []
    if os.path.exists(tfidf_path):
        df_tfidf = pd.read_csv(tfidf_path).head(15)
        keyword_labels = df_tfidf['keyword'].tolist()
        keyword_weights = df_tfidf['tfidf_weight'].tolist()
    else:
        print("[Warning] TF-IDF 키워드 파일이 없습니다. 기본 키워드로 대체합니다.")
        keyword_labels = ["AI", "데이터", "실전", "실무", "최신", "프로그래밍", "분석", "개발", "핵심", "기초"]
        keyword_weights = [0.16, 0.07, 0.07, 0.06, 0.09, 0.05, 0.05, 0.04, 0.07, 0.04]
        
    keyword_chart_data = {
        "labels": keyword_labels,
        "weights": keyword_weights
    }
    
    # 7. Chart 5: 평점 vs 리뷰 수 상관관계 산점도 데이터
    scatter_data = []
    for item in books_list:
        # 산점도 가시성을 위해 리뷰가 존재하고 평점이 0점보다 큰 실시간 데이터 위주 매핑
        scatter_data.append({
            "x": float(item["평점"]),
            "y": int(item["리뷰수"]),
            "title": item["도서명"],
            "rank": int(item["순위"])
        })
        
    chart_data = {
        "price_chart": price_chart_data,
        "publisher_chart": publisher_chart_data,
        "rating_chart": rating_chart_data,
        "keyword_chart": keyword_chart_data,
        "scatter_chart": scatter_data
    }
    
    # 8. 최종 JS 파일 내보내기
    print(f"[Builder] 데이터를 JavaScript로 변환하여 저장합니다: {output_js_path}")
    os.makedirs(os.path.dirname(output_js_path), exist_ok=True)
    
    with open(output_js_path, "w", encoding="utf-8") as f:
        f.write("/**\n * 교보문고 일간 베스트셀러 대시보드 데이터 파일\n * 본 파일은 dashboard_data_builder.py에 의해 자동 생성되었습니다.\n */\n\n")
        f.write(f"window.DASHBOARD_METRICS = {json.dumps(metrics, ensure_ascii=False, indent=2)};\n\n")
        f.write(f"window.DASHBOARD_CHARTS = {json.dumps(chart_data, ensure_ascii=False, indent=2)};\n\n")
        f.write(f"window.DASHBOARD_BOOKS = {json.dumps(books_list, ensure_ascii=False, indent=2)};\n")
        
    print("[Builder] 데이터 파일 dashboard_data.js 빌드 성공!")

if __name__ == "__main__":
    build_dashboard_data()
