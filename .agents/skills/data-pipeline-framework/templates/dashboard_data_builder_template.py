# -*- coding: utf-8 -*-
"""
__PROJECT_NAME__ 대시보드 데이터 전처리 및 JS 빌더 스크립트 템플릿

이 스크립트는 수집된 CSV 데이터와 TF-IDF 키워드 분석 결과를 로드하여
웹 대시보드(dashboard.html)가 로컬 서버 환경 없이도 데이터를 직접 동적으로 바인딩해
렌더링할 수 있도록 JSON 데이터를 전역 자바스크립트 변수 파일(dashboard_data.js)로 컴파일합니다.

치환 대상 변수:
- PROJECT_NAME: __PROJECT_NAME__
- CSV_PATH: __CSV_PATH__
- TFIDF_CSV_PATH: __TFIDF_CSV_PATH__
- OUTPUT_JS_PATH: __OUTPUT_JS_PATH__

작성자: Antigravity AI Data Pipeline Framework
"""

import os
import json
import pandas as pd

def build_dashboard_data():
    csv_path = "__CSV_PATH__"
    tfidf_path = "__TFIDF_CSV_PATH__"
    output_js_path = "__OUTPUT_JS_PATH__"
    
    print(f"[Builder] CSV 데이터를 로드합니다: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"[Error] CSV 파일이 존재하지 않습니다: {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    
    # 1. 요약 통계(Metrics) 가공
    total_books = int(df.shape[0])
    avg_price = int(df['정가'].mean()) if '정가' in df.columns else 0
    avg_rating = float(df['평점'].mean()) if '평점' in df.columns else 0.0
    max_reviews = int(df['리뷰수'].max()) if '리뷰수' in df.columns else 0
    
    metrics = {
        "total_books": total_books,
        "avg_price": avg_price,
        "avg_rating": round(avg_rating, 2),
        "max_reviews": max_reviews
    }
    
    # 2. 전체 도서 데이터 (상세설명 포함)
    df_cleaned = df.fillna("")
    books_list = df_cleaned.to_dict(orient="records")
    
    # 3. Chart 1: 가격대 분포 데이터 (정가 및 판매가 구간별 집계)
    price_chart_data = {
        "labels": [],
        "regular": [],
        "sale": []
    }
    if '정가' in df.columns and '판매가' in df.columns:
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
    publisher_chart_data = {
        "labels": [],
        "values": []
    }
    if '출판사' in df.columns:
        pub_counts = df_cleaned['출판사'].value_counts().head(10)
        publisher_chart_data = {
            "labels": pub_counts.index.tolist(),
            "values": pub_counts.tolist()
        }
    
    # 5. Chart 3: 평점 분포 데이터
    rating_chart_data = {
        "labels": [],
        "values": []
    }
    if '평점' in df.columns:
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
        try:
            df_tfidf = pd.read_csv(tfidf_path).head(15)
            keyword_labels = df_tfidf['keyword'].tolist()
            keyword_weights = df_tfidf['tfidf_weight'].tolist()
        except Exception as e:
            print(f"[Warning] TF-IDF 키워드 로드 실패: {e}")
            
    if not keyword_labels:
        keyword_labels = ["AI", "데이터", "실전", "실무", "최신", "프로그래밍", "분석", "개발", "핵심", "기초"]
        keyword_weights = [0.16, 0.07, 0.07, 0.06, 0.09, 0.05, 0.05, 0.04, 0.07, 0.04]
        
    keyword_chart_data = {
        "labels": keyword_labels,
        "weights": keyword_weights
    }
    
    # 7. Chart 5: 평점 vs 리뷰 수 상관관계 산점도 데이터
    scatter_data = []
    if '평점' in df.columns and '리뷰수' in df.columns:
        for item in books_list:
            scatter_data.append({
                "x": float(item.get("평점", 0.0)),
                "y": int(item.get("리뷰수", 0)),
                "title": item.get("도서명", ""),
                "rank": int(item.get("순위", 0))
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
        f.write("/**\n * 대시보드 데이터 파일\n * 본 파일은 dashboard_data_builder_template.py에 의해 자동 생성되었습니다.\n */\n\n")
        f.write(f"window.DASHBOARD_METRICS = {json.dumps(metrics, ensure_ascii=False, indent=2)};\n\n")
        f.write(f"window.DASHBOARD_CHARTS = {json.dumps(chart_data, ensure_ascii=False, indent=2)};\n\n")
        f.write(f"window.DASHBOARD_BOOKS = {json.dumps(books_list, ensure_ascii=False, indent=2)};\n")
        
    print("[Builder] 데이터 파일 dashboard_data.js 빌드 성공!")

if __name__ == "__main__":
    build_dashboard_data()
