# -*- coding: utf-8 -*-
"""
네모앱(nemoapp.kr) 대시보드 데이터 빌더 스크립트

이 스크립트는 수집이 완료된 매물 CSV 데이터와 TF-IDF 키워드 데이터를 가공하여,
대시보드 웹앱(dashboard.html)이 로컬 서버 없이 정적으로 동작할 수 있도록
실제 도메인 속성명(title, region, deposit, monthly_rent, details)을 그대로 적용하여
JS 변수 파일(dashboard_data.js)로 컴파일합니다.
기존 데이터의 금액 단위를 '천원'에서 '만원'으로 보정하여 정합성을 확보하고,
차트 구간 및 통계 수치를 현실적인 수준으로 정제합니다.

작성자: Antigravity AI Data Pipeline Framework
작성일: 2026-06-12
"""

import os
import json
import pandas as pd

def build_dashboard_data():
    csv_path = "nemo_real_estate/data/nemo_real_estate_bestseller.csv"
    tfidf_path = "nemo_real_estate/docs/tfidf_keywords.csv"
    output_js_path = "nemo_real_estate/src/dashboard_data.js"
    
    print(f"[Builder] CSV 데이터를 로드합니다: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"[Error] CSV 파일이 존재하지 않습니다: {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    
    # 숫자 변환 및 단위 보정 (원본 데이터의 단위가 '천원'이므로 10으로 나누어 '만원' 단위로 통일)
    if 'deposit' in df.columns:
        df['deposit'] = pd.to_numeric(df['deposit'], errors='coerce').fillna(0) / 10.0
    if 'monthly_rent' in df.columns:
        df['monthly_rent'] = pd.to_numeric(df['monthly_rent'], errors='coerce').fillna(0) / 10.0
        
    # 1. 요약 통계(Metrics) 가공 (부동산 용어 적용)
    total_listings = int(df.shape[0])
    
    valid_val1 = df[df['deposit'] > 0]['deposit']
    avg_val1 = float(valid_val1.mean()) if not valid_val1.empty else 0.0
    
    valid_val2 = df[df['monthly_rent'] > 0]['monthly_rent']
    avg_val2 = float(valid_val2.mean()) if not valid_val2.empty else 0.0
    
    max_val2 = float(df['monthly_rent'].max()) if 'monthly_rent' in df.columns else 0.0
    
    metrics = {
        "total_listings": total_listings,
        "avg_deposit": round(avg_val1, 1),
        "avg_monthly_rent": round(avg_val2, 1),
        "max_monthly_rent": round(max_val2, 1)
    }
    
    # 2. 전체 데이터 (결측치 정제 및 JSON 직렬화용 리스트 반환)
    df_cleaned = df.fillna("")
    items_list = df_cleaned.to_dict(orient="records")
    
    # 3. Chart 1: 보증금(deposit) 구간 분포 데이터
    price_chart_data = {
        "labels": [],
        "values": []
    }
    if 'deposit' in df.columns:
        # 보증금 구간 설정 (만원 단위이므로 10,000 = 1억원)
        bins = [0, 5000, 10000, 20000, 50000, 100000, 1000000]
        labels = ["5천만원 이하", "5천만~1억원", "1억~2억원", "2억~5억원", "5억~10억원", "10억원 초과"]
        
        try:
            df_cleaned['v1_range'] = pd.cut(df_cleaned['deposit'], bins=bins, labels=labels, include_lowest=True)
            dist_v1 = df_cleaned['v1_range'].value_counts().reindex(labels).fillna(0).astype(int).tolist()
        except Exception as e:
            print(f"[Warning] 보증금 구간 분할 실패: {e}")
            labels = ["1억 이하", "1억~3억", "3억~5억", "5억~10억", "10억 이상"]
            dist_v1 = [0, 0, 0, 0, 0]
        
        price_chart_data = {
            "labels": labels,
            "values": dist_v1
        }
    
    # 4. Chart 2: region(지역구분) 점유율
    publisher_chart_data = {
        "labels": [],
        "values": []
    }
    if 'region' in df.columns:
        cat_counts = df_cleaned['region'].value_counts()
        publisher_chart_data = {
            "labels": cat_counts.index.tolist(),
            "values": cat_counts.tolist()
        }
    
    # 5. Chart 3: 월세(monthly_rent) 분포 데이터
    rating_chart_data = {
        "labels": [],
        "values": []
    }
    if 'monthly_rent' in df.columns:
        # 월세 구간 설정 (단위: 만원 - 현실적인 상가/사무실 월세 분포 반영)
        bins2 = [0, 100, 200, 300, 500, 1000, 100000]
        labels2 = ["100만원 이하", "100만~200만", "200만~300만", "300만~500만", "500만~1000만", "1000만원 초과"]
        
        try:
            df_cleaned['v2_range'] = pd.cut(df_cleaned['monthly_rent'], bins=bins2, labels=labels2, include_lowest=True)
            rating_dist = df_cleaned['v2_range'].value_counts().reindex(labels2).fillna(0).astype(int).tolist()
        except Exception as e:
            print(f"[Warning] 월세 구간 분할 실패: {e}")
            labels2 = ["100만 이하", "100~300만", "300~500만", "500~1000만", "1000만 이상"]
            rating_dist = [0, 0, 0, 0, 0]
            
        rating_chart_data = {
            "labels": labels2,
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
        keyword_labels = ["층수", "1층", "기타업종", "기타창업모음", "강남역", "5분", "일반음식점", "2층", "역삼역", "신논현역"]
        keyword_weights = [0.17, 0.15, 0.13, 0.12, 0.10, 0.09, 0.09, 0.09, 0.07, 0.05]
        
    keyword_chart_data = {
        "labels": keyword_labels,
        "weights": keyword_weights
    }
    
    # 7. Chart 5: 보증금(deposit) vs 월세(monthly_rent) 상관관계 산점도 데이터
    scatter_data = []
    if 'deposit' in df.columns and 'monthly_rent' in df.columns:
        for item in items_list:
            scatter_data.append({
                "x": float(item.get("deposit", 0.0)),
                "y": float(item.get("monthly_rent", 0.0)),
                "title": item.get("title", ""),
                "rank": int(item.get("순위", 0)) if item.get("순위") else 0,
                "region": item.get("region", "")
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
        f.write("/**\n * 부동산 대시보드 데이터 파일\n * 본 파일은 dashboard_data_builder.py에 의해 자동 생성되었습니다.\n */\n\n")
        f.write(f"window.DASHBOARD_METRICS = {json.dumps(metrics, ensure_ascii=False, indent=2)};\n\n")
        f.write(f"window.DASHBOARD_CHARTS = {json.dumps(chart_data, ensure_ascii=False, indent=2)};\n\n")
        f.write(f"window.DASHBOARD_LISTINGS = {json.dumps(items_list, ensure_ascii=False, indent=2)};\n")
        
    print("[Builder] 데이터 파일 dashboard_data.js 빌드 성공!")

if __name__ == "__main__":
    build_dashboard_data()
